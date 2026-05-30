import sqlite3
c = sqlite3.connect("wrench_vehicles.db"); c.row_factory = sqlite3.Row

# ---- EV detection (same as audit: 135 vehicles) ----
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
ev = sorted(ev)
evph = ",".join("?" * len(ev))
print(f"EV set: {len(ev)} vehicles")

def cnt(sql, *a): return c.execute(sql, a).fetchone()[0]
print("\n--- BEFORE ---")
print("EV oil_change rows:", cnt(f"SELECT COUNT(*) FROM oil_change WHERE vehicle_id IN ({evph})", *ev))
print("EV parts w/ spark plug:", cnt(f"SELECT COUNT(*) FROM parts WHERE vehicle_id IN ({evph}) AND (spark_plug_type IS NOT NULL OR spark_plug_qty>0)", *ev))
print("EV oil/plug maintenance items:", cnt(f"SELECT COUNT(*) FROM maintenance WHERE vehicle_id IN ({evph}) AND (LOWER(description) LIKE '%oil change%' OR LOWER(description) LIKE '%engine oil%' OR LOWER(description) LIKE '%oil and filter%' OR LOWER(description) LIKE '%spark plug%')", *ev))
print("EV drain torque_specs:", cnt(f"SELECT COUNT(*) FROM torque_specs WHERE vehicle_id IN ({evph}) AND (LOWER(component) LIKE '%drain%' OR LOWER(component) LIKE '%spark plug%')", *ev))
print("EV fuel rows w/ combined_mpg set:", cnt(f"SELECT COUNT(*) FROM fuel_economy WHERE vehicle_id IN ({evph}) AND combined_mpg IS NOT NULL", *ev))

# ===== FIX 1: EV CLEANUP =====
# 1a. oil + drain plug live entirely in oil_change -> delete the row
c.execute(f"DELETE FROM oil_change WHERE vehicle_id IN ({evph})", ev)
# 1b. spark plugs in parts -> null (keep tire/battery/cabin/air/wiper)
c.execute(f"UPDATE parts SET spark_plug_type=NULL, spark_plug_gap=NULL, spark_plug_qty=NULL, spark_plugs_json=NULL WHERE vehicle_id IN ({evph})", ev)
# 1c. oil/spark-plug maintenance items (+ their parts)
oilplug = "(LOWER(description) LIKE '%oil change%' OR LOWER(description) LIKE '%engine oil%' OR LOWER(description) LIKE '%oil and filter%' OR LOWER(description) LIKE '%spark plug%')"
mids = [r[0] for r in c.execute(f"SELECT id FROM maintenance WHERE vehicle_id IN ({evph}) AND {oilplug}", ev)]
if mids:
    mph = ",".join("?" * len(mids))
    c.execute(f"DELETE FROM maintenance_parts WHERE maintenance_id IN ({mph})", mids)
c.execute(f"DELETE FROM maintenance WHERE vehicle_id IN ({evph}) AND {oilplug}", ev)
# also any EV maintenance_parts referencing oil/plug part_types
c.execute(f"DELETE FROM maintenance_parts WHERE vehicle_id IN ({evph}) AND (LOWER(COALESCE(part_type,'')) LIKE '%spark plug%' OR LOWER(COALESCE(part_type,'')) LIKE '%oil%' OR LOWER(COALESCE(description,'')) LIKE '%spark plug%' OR LOWER(COALESCE(description,'')) LIKE '%engine oil%')", ev)
# 1d. drain-plug / spark-plug torque specs
c.execute(f"DELETE FROM torque_specs WHERE vehicle_id IN ({evph}) AND (LOWER(component) LIKE '%drain%' OR LOWER(component) LIKE '%spark plug%')", ev)

# ===== FIX 1 (MPGe labeling) =====
# move combined MPGe into mpge col, tag electric, fill range, then null misleading MPG cols
c.execute(f"UPDATE fuel_economy SET mpge = combined_mpg WHERE vehicle_id IN ({evph}) AND mpge IS NULL AND combined_mpg IS NOT NULL", ev)
c.execute(f"UPDATE fuel_economy SET fuel_type='Electric' WHERE vehicle_id IN ({evph})", ev)
c.execute(f"UPDATE fuel_economy SET range_miles = COALESCE(range_miles, comb_ev, (SELECT e.range_miles FROM ev_specs e WHERE e.vehicle_id=fuel_economy.vehicle_id)) WHERE vehicle_id IN ({evph})", ev)
c.execute(f"UPDATE fuel_economy SET city_mpg=NULL, highway_mpg=NULL, combined_mpg=NULL WHERE vehicle_id IN ({evph})", ev)

# ===== FIX 2: EXOTIC / RAM tire fallback =====
EX = ['Ferrari','Lamborghini','Rolls-Royce','Bentley','Aston Martin','McLaren','Maserati','Bugatti','Lotus']
exph = ",".join("?" * len(EX))
tire_before = cnt(f"SELECT COUNT(*) FROM parts p JOIN vehicles v ON v.id=p.vehicle_id WHERE p.tire_size='215/55R17' AND (v.make IN ({exph}) OR v.make='RAM')", *EX)
c.execute(f"UPDATE parts SET tire_size=NULL WHERE tire_size='215/55R17' AND vehicle_id IN (SELECT id FROM vehicles WHERE make IN ({exph}) OR make='RAM')", EX)
print(f"\nFIX 2: nulled 215/55R17 on {tire_before} exotic/RAM vehicles")

c.commit()

print("\n--- AFTER ---")
print("EV oil_change rows:", cnt(f"SELECT COUNT(*) FROM oil_change WHERE vehicle_id IN ({evph})", *ev))
print("EV parts w/ spark plug:", cnt(f"SELECT COUNT(*) FROM parts WHERE vehicle_id IN ({evph}) AND (spark_plug_type IS NOT NULL OR spark_plug_qty>0)", *ev))
print("EV oil/plug maintenance items:", cnt(f"SELECT COUNT(*) FROM maintenance WHERE vehicle_id IN ({evph}) AND (LOWER(description) LIKE '%oil change%' OR LOWER(description) LIKE '%engine oil%' OR LOWER(description) LIKE '%oil and filter%' OR LOWER(description) LIKE '%spark plug%')", *ev))
print("EV drain torque_specs:", cnt(f"SELECT COUNT(*) FROM torque_specs WHERE vehicle_id IN ({evph}) AND (LOWER(component) LIKE '%drain%' OR LOWER(component) LIKE '%spark plug%')", *ev))
print("EV fuel rows w/ combined_mpg (should be 0):", cnt(f"SELECT COUNT(*) FROM fuel_economy WHERE vehicle_id IN ({evph}) AND combined_mpg IS NOT NULL", *ev))
print("EV fuel rows w/ mpge set:", cnt(f"SELECT COUNT(*) FROM fuel_economy WHERE vehicle_id IN ({evph}) AND mpge IS NOT NULL", *ev))
print("exotic/RAM still 215/55R17:", cnt(f"SELECT COUNT(*) FROM parts p JOIN vehicles v ON v.id=p.vehicle_id WHERE p.tire_size='215/55R17' AND (v.make IN ({exph}) OR v.make='RAM')", *EX))
# integrity: non-EV oil rows untouched?
print("\nsanity - total oil_change rows now:", cnt("SELECT COUNT(*) FROM oil_change"))
print("sanity - total parts w/ spark plug now:", cnt("SELECT COUNT(*) FROM parts WHERE spark_plug_type IS NOT NULL"))
print("sanity - Camry(gas) still has oil:", cnt("SELECT COUNT(*) FROM oil_change WHERE vehicle_id=13195"))
c.close()
print("[db fixes complete]")
