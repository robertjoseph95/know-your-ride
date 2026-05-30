import sqlite3, json
conn = sqlite3.connect(r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\wrench_vehicles.db")
c = conn.cursor()
turbos = c.execute("SELECT v.id, o.drain_bolt_json FROM vehicles v JOIN oil_change o ON o.vehicle_id=v.id WHERE v.id>0 AND v.make IN ('Honda','Acura') AND v.engine LIKE '%1.5%Turbo%'").fetchall()
ct = 0
for vid, bj in turbos:
    b = json.loads(bj) if bj and bj != 'null' else {}
    if not b:
        b = {}
    b['notes'] = 'Aluminum oil pan - use correct factory-length plug. Shorter plugs can strip threads.'
    c.execute("UPDATE oil_change SET drain_bolt_json=? WHERE vehicle_id=?", (json.dumps(b), vid))
    ct += 1
conn.commit()
print(f"Added aluminum pan warning to {ct} Honda/Acura 1.5T vehicles")
conn.close()
