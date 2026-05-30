import sqlite3
c = sqlite3.connect("wrench_vehicles.db"); c.row_factory = sqlite3.Row
def q1(s, *a): return c.execute(s, *a).fetchone()[0]

# EV set (same detection as audit)
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
ev |= {r[0] for r in c.execute("SELECT id FROM vehicles WHERE model IN (%s)" % ",".join("?"*len(EVN)), EVN)}

# ============ D1: cap TSBs at 200 most-recent per vehicle ============
over = [r[0] for r in c.execute("SELECT vehicle_id FROM tsb GROUP BY vehicle_id HAVING COUNT(*)>200")]
removed = 0
for vid in over:
    ids = [r[0] for r in c.execute("SELECT id FROM tsb WHERE vehicle_id=? ORDER BY date DESC, id DESC", (vid,))]
    excess = ids[200:]
    if excess:
        c.executemany("DELETE FROM tsb WHERE id=?", [(i,) for i in excess]); removed += len(excess)
c.commit()
print(f"D1: capped {len(over)} vehicles to 200 TSBs; deleted {removed} excess rows")
print("    vehicles still >200 TSBs:", q1("SELECT COUNT(*) FROM (SELECT vehicle_id FROM tsb GROUP BY vehicle_id HAVING COUNT(*)>200)"))
print("    new max per vehicle:", q1("SELECT MAX(n) FROM (SELECT COUNT(*) n FROM tsb GROUP BY vehicle_id)"))
print("    total tsb rows now:", q1("SELECT COUNT(*) FROM tsb"))

# ============ D2: manufacturer coolant/brake defaults (non-EV, year>=2000) ============
COOL = {  # make -> (coolant, brake)
    'Toyota':('Super Long Life Coolant (SLLC)','DOT 3'),'Lexus':('Super Long Life Coolant (SLLC)','DOT 3'),'Scion':('Super Long Life Coolant (SLLC)','DOT 3'),
    'Honda':('Type 2 Coolant (Blue)','DOT 3'),'Acura':('Type 2 Coolant (Blue)','DOT 3'),
    'Ford':('Motorcraft Orange','DOT 3'),'Lincoln':('Motorcraft Orange','DOT 3'),'Mercury':('Motorcraft Orange','DOT 3'),
    'Chevrolet':('Dex-Cool','DOT 3'),'GMC':('Dex-Cool','DOT 3'),'Cadillac':('Dex-Cool','DOT 3'),'Buick':('Dex-Cool','DOT 3'),'Pontiac':('Dex-Cool','DOT 3'),'Saturn':('Dex-Cool','DOT 3'),'Oldsmobile':('Dex-Cool','DOT 3'),
    'Chrysler':('MOPAR OAT','DOT 3'),'Dodge':('MOPAR OAT','DOT 3'),'Jeep':('MOPAR OAT','DOT 3'),'RAM':('MOPAR OAT','DOT 3'),'Ram':('MOPAR OAT','DOT 3'),
    'BMW':('G13/G12++','DOT 4'),'Mercedes-Benz':('G13/G12++','DOT 4'),'Audi':('G13/G12++','DOT 4'),'Volkswagen':('G13/G12++','DOT 4'),'Porsche':('G13/G12++','DOT 4'),
}
DEF = ('OAT Coolant','DOT 3')
rows = c.execute("""SELECT f.vehicle_id, v.make, f.coolant_type, f.brake_fluid
                    FROM fluids f JOIN vehicles v ON v.id=f.vehicle_id WHERE v.year>=2000""").fetchall()
cool_set = brake_set = 0
for r in rows:
    if r['vehicle_id'] in ev:  # D2 scope = non-EV
        continue
    coolant, brake = COOL.get(r['make'], DEF)
    if not (r['coolant_type'] and r['coolant_type'].strip()):
        c.execute("UPDATE fluids SET coolant_type=? WHERE vehicle_id=?", (coolant, r['vehicle_id'])); cool_set += 1
    if not (r['brake_fluid'] and r['brake_fluid'].strip()):
        c.execute("UPDATE fluids SET brake_fluid=? WHERE vehicle_id=?", (brake, r['vehicle_id'])); brake_set += 1
c.commit()
print(f"\nD2: set coolant on {cool_set} vehicles, brake fluid on {brake_set} (non-EV, year>=2000, no overwrite)")
print("    fluids still missing coolant (non-EV >=2000):", q1("SELECT COUNT(*) FROM fluids f JOIN vehicles v ON v.id=f.vehicle_id WHERE v.year>=2000 AND (f.coolant_type IS NULL OR f.coolant_type='') AND f.vehicle_id NOT IN (%s)" % ",".join("?"*len(ev)), tuple(ev)) if ev else "n/a")

# ============ D3: EV battery warranty for EVs missing one ============
def batt_terms(make):
    m = (make or '').lower()
    if any(k in m for k in ('hyundai','kia','genesis')): return 120, 100000  # 10yr
    return 96, 100000  # 8yr (Tesla, GM, Ford, BMW/MB/Audi, Honda, others)
missing = [vid for vid in ev if not c.execute(
    "SELECT 1 FROM warranty WHERE vehicle_id=? AND (LOWER(warranty_type) LIKE '%batter%' OR LOWER(warranty_type) LIKE '%ev%' OR LOWER(warranty_type) LIKE '%electric%' OR LOWER(warranty_type) LIKE '%hybrid%')", (vid,)).fetchone()]
added = 0
for vid in missing:
    mk = c.execute("SELECT make FROM vehicles WHERE id=?", (vid,)).fetchone()[0]
    mo, mi = batt_terms(mk)
    c.execute("INSERT INTO warranty (vehicle_id,warranty_type,months,miles,notes) VALUES (?,?,?,?,?)",
              (vid, 'ev_battery', mo, mi, f"{mo//12}-year / {mi:,}-mile EV battery warranty"))
    added += 1
c.commit()
print(f"\nD3: added ev_battery warranty to {added} EVs (were missing)")
print("    EVs still missing battery warranty:", len([vid for vid in ev if not c.execute("SELECT 1 FROM warranty WHERE vehicle_id=? AND LOWER(warranty_type) LIKE '%batter%' OR vehicle_id=? AND LOWER(warranty_type) LIKE '%ev%'", (vid,vid)).fetchone()]))

# ============ D4: de-templatize top-10 most-duplicated maintenance descriptions ============
top10 = [r[0] for r in c.execute("SELECT description FROM maintenance GROUP BY description ORDER BY COUNT(DISTINCT vehicle_id) DESC LIMIT 10")]
print("\nD4: rewriting top-10 templated descriptions:")
for d in top10: print("   -", repr(d))
def verb_for(desc):
    d = desc.lower()
    if 'oil' in d: return 'an engine oil & filter change'
    if 'cabin' in d: return 'cabin air filter replacement'
    if 'air filter' in d or 'engine air' in d: return 'engine air filter replacement'
    if 'rotat' in d or 'tire' in d: return 'tire rotation'
    if 'brake' in d: return 'a brake inspection'
    if 'wiper' in d: return 'wiper blade replacement'
    return 'this service'
ph10 = ",".join("?"*len(top10))
rows = c.execute(f"""SELECT m.id, m.description, m.mileage_interval mi, m.months_interval mo, v.make
                     FROM maintenance m JOIN vehicles v ON v.id=m.vehicle_id
                     WHERE m.description IN ({ph10})""", top10).fetchall()
rew = 0
for r in rows:
    base = r['description']; make = r['make'] or 'the manufacturer'; mi = r['mi']; mo = r['mo']
    sv = verb_for(base)
    if mi and mi > 0 and mo and mo > 0:
        cad = f"every {mi:,} miles or {mo} months"
    elif mi and mi > 0:
        cad = f"every {mi:,} miles"
    elif mo and mo > 0:
        cad = f"every {mo} months"
    else:
        cad = None
    if cad:
        new = f"{base} — {make} recommends {sv} {cad}"
    else:
        new = f"{base} — follow the {make} factory maintenance schedule"
    c.execute("UPDATE maintenance SET description=? WHERE id=?", (new, r['id'])); rew += 1
c.commit()
print(f"D4: rewrote {rew} maintenance rows with make+interval wording")
print("    descriptions still on 50+ vehicles:", q1("SELECT COUNT(*) FROM (SELECT description FROM maintenance GROUP BY description HAVING COUNT(DISTINCT vehicle_id)>=50)"))
# sanity sample
ex = c.execute("SELECT m.description FROM maintenance m JOIN vehicles v ON v.id=m.vehicle_id WHERE v.make='Toyota' AND m.description LIKE '%air filter%' LIMIT 1").fetchone()
print("    sample:", ex[0] if ex else "(none)")
c.close()
print("\n[D1-D4 complete]")
