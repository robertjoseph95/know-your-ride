import sqlite3, json
conn = sqlite3.connect(r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\wrench_vehicles.db")
c = conn.cursor()
rows = c.execute("""
    SELECT v.id, v.model, o.drain_bolt_json FROM vehicles v
    JOIN oil_change o ON o.vehicle_id=v.id
    WHERE v.id > 0 AND v.make = 'Maserati' AND o.viscosity IS NOT NULL
""").fetchall()
ct = 0
for vid, model, bj in rows:
    b = json.loads(bj) if bj and bj != 'null' else {}
    if not b:
        b = {}
    b['socket_size_mm'] = 10
    b['thread_size'] = 'M22x1.5'
    b['notes'] = '10mm hex (Allen) key - not a standard socket'
    c.execute("UPDATE oil_change SET drain_bolt_json=? WHERE vehicle_id=?", (json.dumps(b), vid))
    ct += 1
conn.commit()
sk = c.execute("SELECT COUNT(*) FROM oil_change WHERE vehicle_id>0 AND json_extract(drain_bolt_json,'$.socket_size_mm') IS NOT NULL").fetchone()[0]
print(f"Updated {ct} Maserati vehicles (M22x1.5, 10mm Allen)")
print(f"Socket: {sk}/1615 ({sk/1615*100:.1f}%)")
conn.close()
