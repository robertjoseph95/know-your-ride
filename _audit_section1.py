import sqlite3
c = sqlite3.connect("wrench_vehicles.db"); c.row_factory = sqlite3.Row
def q1(sql, *a):
    r = c.execute(sql, a).fetchone(); return r[0] if r else None
TOTAL = q1("SELECT COUNT(*) FROM vehicles")

# ---- EV detection ----
ev = set()
for vid, comb in c.execute("SELECT vehicle_id, MAX(combined_mpg) FROM fuel_economy GROUP BY vehicle_id"):
    if comb and comb >= 90: ev.add(vid)
ev |= {r[0] for r in c.execute("SELECT vehicle_id FROM fuel_economy WHERE LOWER(COALESCE(fuel_type,'')) LIKE '%electric%'")}
ev |= {r[0] for r in c.execute("SELECT vehicle_id FROM ev_specs")}
EVN = ['Model 3','Model Y','Model S','Model X','Cybertruck','Ioniq 5','Ioniq 6','Ioniq 9','EV6','EV9',
       'Mustang Mach-E','F-150 Lightning','ID.4','ID. Buzz','Ariya','bZ4X','Solterra','Prologue','ZDX',
       'LYRIQ','Lyriq','Optiq','Vistiq','Hummer EV','Sierra EV','Silverado EV','Blazer EV','Equinox EV',
       'i4','i5','iX','EQS','EQE','Air','Gravity','R1T','R1S','Taycan','e-tron GT','EX30','EX90','Leaf',
       'Bolt','Bolt EUV','Kona Electric','Niro EV','Soul EV','GV60']
ph = ",".join("?" * len(EVN))
ev |= {r[0] for r in c.execute(f"SELECT id FROM vehicles WHERE model IN ({ph})", EVN)}
def isev(vid): return vid in ev
print(f"TOTAL VEHICLES: {TOTAL} | detected EVs: {len(ev)}")

print("\n===== 1. OIL CHANGE =====")
print("with oil_change row:", q1("SELECT COUNT(*) FROM oil_change"))
print("with non-null viscosity:", q1("SELECT COUNT(*) FROM oil_change WHERE viscosity IS NOT NULL AND viscosity<>''"))
print("vehicles MISSING oil_change row:", q1("SELECT COUNT(*) FROM vehicles v WHERE NOT EXISTS(SELECT 1 FROM oil_change o WHERE o.vehicle_id=v.id)"))
print("distinct viscosity values:")
for r in c.execute("SELECT viscosity, COUNT(*) c FROM oil_change WHERE viscosity IS NOT NULL AND viscosity<>'' GROUP BY viscosity ORDER BY c DESC"):
    print(f"   {r['viscosity']!r}: {r['c']}")
print("capacity <3qt (>0):", q1("SELECT COUNT(*) FROM oil_change WHERE capacity_with_filter>0 AND capacity_with_filter<3"))
print("capacity >12qt:", q1("SELECT COUNT(*) FROM oil_change WHERE capacity_with_filter>12"))
for r in c.execute("SELECT o.vehicle_id,v.year,v.make,v.model,o.capacity_with_filter cap FROM oil_change o JOIN vehicles v ON v.id=o.vehicle_id WHERE o.capacity_with_filter>12 OR (o.capacity_with_filter>0 AND o.capacity_with_filter<3) ORDER BY cap DESC LIMIT 20"):
    print(f"   cap={r['cap']}: {r['year']} {r['make']} {r['model']} (vid {r['vehicle_id']})")
evoil = [r for r in c.execute("SELECT o.vehicle_id,v.year,v.make,v.model,o.viscosity FROM oil_change o JOIN vehicles v ON v.id=o.vehicle_id WHERE o.viscosity IS NOT NULL AND o.viscosity<>''") if isev(r['vehicle_id'])]
print(f"EVs WITH real oil viscosity (WRONG): {len(evoil)}")
for r in evoil[:25]: print(f"   {r['year']} {r['make']} {r['model']} visc={r['viscosity']} (vid {r['vehicle_id']})")

print("\n===== 2. DRAIN PLUG (oil_change.socket/thread/gasket) =====")
print("with socket:", q1("SELECT COUNT(*) FROM oil_change WHERE socket IS NOT NULL AND socket<>''"))
print("with thread:", q1("SELECT COUNT(*) FROM oil_change WHERE thread IS NOT NULL AND thread<>''"))
print("with gasket:", q1("SELECT COUNT(*) FROM oil_change WHERE gasket IS NOT NULL AND gasket<>''"))
print("with drain_bolt_json non-empty:", q1("SELECT COUNT(*) FROM oil_change WHERE drain_bolt_json IS NOT NULL AND drain_bolt_json NOT IN ('','{}','null','[]')"))
print("torque_specs drain-plug rows:", q1("SELECT COUNT(*) FROM torque_specs WHERE LOWER(component) LIKE '%drain%'"))
print("distinct socket values:")
for r in c.execute("SELECT socket,COUNT(*) c FROM oil_change WHERE socket IS NOT NULL AND socket<>'' GROUP BY socket ORDER BY c DESC"):
    print(f"   {r['socket']!r}: {r['c']}")
GOOD = {'8','10','12','13','14','15','16','17','18','19','21','22','24'}
def norm(s): return str(s).lower().replace('mm','').strip()
odd = sorted({r['socket'] for r in c.execute("SELECT DISTINCT socket FROM oil_change WHERE socket IS NOT NULL AND socket<>''") if norm(r['socket']) not in GOOD})
print("non-standard socket values:", odd)
eb = [vid for vid in (r[0] for r in c.execute("SELECT vehicle_id FROM oil_change WHERE (socket IS NOT NULL AND socket<>'') OR (thread IS NOT NULL AND thread<>'')")) if isev(vid)]
print(f"EVs WITH drain plug data (WRONG): {len(eb)}")
for vid in eb[:15]:
    r = c.execute("SELECT year,make,model FROM vehicles WHERE id=?", (vid,)).fetchone(); print(f"   {r['year']} {r['make']} {r['model']} (vid {vid})")

print("\n===== 3. MAINTENANCE =====")
print("vehicles with >=1 maintenance item:", q1("SELECT COUNT(DISTINCT vehicle_id) FROM maintenance"))
print("vehicles with 0 maintenance items:", q1("SELECT COUNT(*) FROM vehicles v WHERE NOT EXISTS(SELECT 1 FROM maintenance m WHERE m.vehicle_id=v.id)"))
print("maintenance 'source' values:", [tuple(r) for r in c.execute("SELECT source,COUNT(*) FROM maintenance GROUP BY source ORDER BY 2 DESC")])
print("top duplicated maintenance descriptions (distinct-vehicle count):")
for r in c.execute("SELECT description, COUNT(DISTINCT vehicle_id) v FROM maintenance GROUP BY description ORDER BY v DESC LIMIT 12"):
    print(f"   x{r['v']} veh: {str(r['description'])[:75]!r}")
evoilm = [vid for vid in (r[0] for r in c.execute("SELECT DISTINCT vehicle_id FROM maintenance WHERE LOWER(description) LIKE '%oil change%' OR LOWER(description) LIKE '%engine oil%' OR LOWER(description) LIKE '%oil and filter%'")) if isev(vid)]
print(f"EVs WITH oil-change maintenance item (WRONG): {len(evoilm)}")
for vid in evoilm[:15]:
    r = c.execute("SELECT year,make,model FROM vehicles WHERE id=?", (vid,)).fetchone(); print(f"   {r['year']} {r['make']} {r['model']} (vid {vid})")

print("\n===== 4. FLUIDS =====")
print("fluids rows:", q1("SELECT COUNT(*) FROM fluids"))
evf = [r for r in c.execute("SELECT f.vehicle_id,v.year,v.make,v.model,f.power_steering_fluid ps,f.transmission_fluid tf FROM fluids f JOIN vehicles v ON v.id=f.vehicle_id") if isev(r['vehicle_id'])]
evps = [r for r in evf if r['ps']]
print(f"EVs with a fluids row: {len(evf)} | EVs with power_steering_fluid set (likely wrong, EPS): {len(evps)}")
for r in evps[:12]: print(f"   {r['year']} {r['make']} {r['model']} ps={r['ps']!r} trans={r['tf']!r}")
print("null/blank coolant_type:", q1("SELECT COUNT(*) FROM fluids WHERE coolant_type IS NULL OR coolant_type=''"))
print("null/blank brake_fluid:", q1("SELECT COUNT(*) FROM fluids WHERE brake_fluid IS NULL OR brake_fluid=''"))
print("vehicles with duplicate fluid rows:", q1("SELECT COUNT(*) FROM (SELECT vehicle_id,COUNT(*) c FROM fluids GROUP BY vehicle_id HAVING c>1)"))

print("\n===== 5. TIRE SIZE =====")
print("parts rows:", q1("SELECT COUNT(*) FROM parts"))
print("with real tire_size:", q1("SELECT COUNT(*) FROM parts WHERE tire_size IS NOT NULL AND tire_size<>''"))
print("null tire_size:", q1("SELECT COUNT(*) FROM parts WHERE tire_size IS NULL OR tire_size=''"))
print("count tire_size='215/55R17':", q1("SELECT COUNT(*) FROM parts WHERE tire_size='215/55R17'"))
EX = ['Ferrari','Lamborghini','Rolls-Royce','Bentley','Aston Martin','McLaren','Maserati','Porsche','Bugatti','Lotus']
ph2 = ",".join("?" * len(EX))
print("exotics with tire 215/55R17 (generic fallback):")
for r in c.execute(f"SELECT v.year,v.make,v.model,p.tire_size FROM parts p JOIN vehicles v ON v.id=p.vehicle_id WHERE v.make IN ({ph2}) AND p.tire_size='215/55R17'", EX):
    print(f"   {r['year']} {r['make']} {r['model']}: {r['tire_size']}")
print("trucks/large-SUV with 215/55R17 (suspicious):")
for r in c.execute("SELECT v.year,v.make,v.model FROM parts p JOIN vehicles v ON v.id=p.vehicle_id WHERE p.tire_size='215/55R17' AND (v.model LIKE '%F-150%' OR v.model LIKE '%Silverado%' OR v.model LIKE '%Sierra%' OR v.model LIKE '%Tundra%' OR v.model LIKE '%1500%' OR v.model LIKE '%2500%' OR v.model LIKE '%Tahoe%' OR v.model LIKE '%Suburban%' OR v.model LIKE '%Expedition%' OR v.make='RAM') LIMIT 25"):
    print(f"   {r['year']} {r['make']} {r['model']}")

print("\n===== 6. SAFETY RATINGS =====")
print("rows:", q1("SELECT COUNT(*) FROM safety_ratings"), "| with overall_rating:", q1("SELECT COUNT(*) FROM safety_ratings WHERE overall_rating IS NOT NULL"))
print("overall_rating outside 1-5:", q1("SELECT COUNT(*) FROM safety_ratings WHERE overall_rating IS NOT NULL AND (overall_rating<1 OR overall_rating>5)"))
print("vehicles MISSING safety row:", q1("SELECT COUNT(*) FROM vehicles v WHERE NOT EXISTS(SELECT 1 FROM safety_ratings s WHERE s.vehicle_id=v.id)"))
evnos = [vid for vid in ev if not c.execute("SELECT 1 FROM safety_ratings WHERE vehicle_id=?", (vid,)).fetchone()]
print(f"EVs missing safety data: {len(evnos)} of {len(ev)}")

print("\n===== 7. FUEL ECONOMY =====")
print("rows combined_mpg>=90 (MPGe mislabeled in MPG cols):", q1("SELECT COUNT(*) FROM fuel_economy WHERE combined_mpg>=90"))
print("rows using mpge column:", q1("SELECT COUNT(*) FROM fuel_economy WHERE mpge IS NOT NULL"))
print("rows using range_ev/comb_ev cols:", q1("SELECT COUNT(*) FROM fuel_economy WHERE comb_ev IS NOT NULL OR range_ev IS NOT NULL"))
print("distinct EV vehicles with combined_mpg>=90:", q1("SELECT COUNT(DISTINCT vehicle_id) FROM fuel_economy WHERE combined_mpg>=90"))
print("combined_mpg 60-90 (non-EV high - hybrids/suspicious), sample:")
for r in c.execute("SELECT v.year,v.make,v.model,MAX(f.combined_mpg) m FROM fuel_economy f JOIN vehicles v ON v.id=f.vehicle_id WHERE f.combined_mpg>60 AND f.combined_mpg<90 GROUP BY f.vehicle_id ORDER BY m DESC LIMIT 15"):
    print(f"   {r['m']}mpg {r['year']} {r['make']} {r['model']}")
print("combined_mpg<10 (>0) suspicious:", q1("SELECT COUNT(*) FROM fuel_economy WHERE combined_mpg<10 AND combined_mpg>0"))
for r in c.execute("SELECT v.year,v.make,v.model,f.combined_mpg m FROM fuel_economy f JOIN vehicles v ON v.id=f.vehicle_id WHERE f.combined_mpg<10 AND f.combined_mpg>0 LIMIT 10"):
    print(f"   {r['m']}mpg {r['year']} {r['make']} {r['model']}")

print("\n===== 8. TSB & RECALLS =====")
print("tsb rows:", q1("SELECT COUNT(*) FROM tsb"), "| null/blank title:", q1("SELECT COUNT(*) FROM tsb WHERE title IS NULL OR title=''"))
print("recalls rows:", q1("SELECT COUNT(*) FROM recalls"), "| null/blank summary:", q1("SELECT COUNT(*) FROM recalls WHERE summary IS NULL OR summary=''"))
print("recalls null campaign_number:", q1("SELECT COUNT(*) FROM recalls WHERE campaign_number IS NULL OR campaign_number=''"))
print("vehicles with 50+ TSBs:")
for r in c.execute("SELECT v.year,v.make,v.model,COUNT(*) n FROM tsb t JOIN vehicles v ON v.id=t.vehicle_id GROUP BY t.vehicle_id HAVING n>=50 ORDER BY n DESC LIMIT 15"):
    print(f"   {r['n']} TSBs: {r['year']} {r['make']} {r['model']}")

print("\n===== 9. PARTS =====")
print("vehicles missing ALL parts (no row):", q1("SELECT COUNT(*) FROM vehicles v WHERE NOT EXISTS(SELECT 1 FROM parts p WHERE p.vehicle_id=v.id)"))
evsp = [r for r in c.execute("SELECT p.vehicle_id,v.year,v.make,v.model,p.spark_plug_type t,p.spark_plug_qty qy FROM parts p JOIN vehicles v ON v.id=p.vehicle_id WHERE (p.spark_plug_type IS NOT NULL AND p.spark_plug_type<>'') OR p.spark_plug_qty>0") if isev(r['vehicle_id'])]
print(f"EVs WITH spark plug data (WRONG): {len(evsp)}")
for r in evsp[:15]: print(f"   {r['year']} {r['make']} {r['model']} plug={r['t']!r} qty={r['qy']}")
print("placeholder part numbers in maintenance_parts:")
for r in c.execute("SELECT COUNT(*) n, part_number p FROM maintenance_parts WHERE UPPER(COALESCE(part_number,'')) IN ('TBD','N/A','NA','UNKNOWN','NONE','?','-') GROUP BY part_number"):
    print(f"   {r['p']!r}: {r['n']}")
print("placeholder brands:", [tuple(r) for r in c.execute("SELECT brand,COUNT(*) FROM maintenance_parts WHERE UPPER(COALESCE(brand,'')) IN ('TBD','N/A','UNKNOWN','NONE') GROUP BY brand")])

print("\n===== 10. WARRANTY =====")
print("warranty rows:", q1("SELECT COUNT(*) FROM warranty"))
print("warranty months=0:", q1("SELECT COUNT(*) FROM warranty WHERE months=0"), "| months null:", q1("SELECT COUNT(*) FROM warranty WHERE months IS NULL"))
print("distinct warranty_type:", [tuple(r) for r in c.execute("SELECT warranty_type,COUNT(*) FROM warranty GROUP BY warranty_type ORDER BY 2 DESC")])
evbatt = [vid for vid in ev if c.execute("SELECT 1 FROM warranty WHERE vehicle_id=? AND (LOWER(warranty_type) LIKE '%batter%' OR LOWER(warranty_type) LIKE '%ev%' OR LOWER(warranty_type) LIKE '%electric%' OR LOWER(warranty_type) LIKE '%hybrid%')", (vid,)).fetchone()]
print(f"EVs WITH battery/EV warranty row: {len(evbatt)} of {len(ev)} (missing: {len(ev)-len(evbatt)})")
print("vehicles with duplicate (vehicle_id,warranty_type) rows:", q1("SELECT COUNT(*) FROM (SELECT vehicle_id,warranty_type,COUNT(*) c FROM warranty GROUP BY vehicle_id,warranty_type HAVING c>1)"))
c.close()
print("\n[section1 complete]")
