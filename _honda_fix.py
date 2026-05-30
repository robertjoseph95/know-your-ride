import sqlite3, json
conn = sqlite3.connect(r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\wrench_vehicles.db")
c = conn.cursor()
hondas = c.execute("SELECT v.id, o.drain_bolt_json FROM vehicles v JOIN oil_change o ON o.vehicle_id=v.id WHERE v.id > 0 AND v.make IN ('Honda','Acura') AND o.viscosity IS NOT NULL AND v.model NOT IN ('Prologue','Clarity')").fetchall()
ct = 0
for vid, bj in hondas:
    b = json.loads(bj) if bj and bj != 'null' else {}
    if not b:
        b = {}
    ch = False
    if not b.get('torque_ft_lbs'):
        b['torque_ft_lbs'] = 30
        ch = True
    if not b.get('gasket_type'):
        b['gasket_type'] = '14mm crush washer (Honda 94109-14000)'
        ch = True
    if not b.get('socket_size_mm'):
        b['socket_size_mm'] = 17
        ch = True
    if ch:
        c.execute("UPDATE oil_change SET drain_bolt_json=? WHERE vehicle_id=?", (json.dumps(b), vid))
        ct += 1
conn.commit()
sk = c.execute("SELECT COUNT(*) FROM oil_change WHERE vehicle_id>0 AND json_extract(drain_bolt_json,'$.socket_size_mm') IS NOT NULL").fetchone()[0]
th = c.execute("SELECT COUNT(*) FROM oil_change WHERE vehicle_id>0 AND json_extract(drain_bolt_json,'$.torque_ft_lbs') IS NOT NULL").fetchone()[0]
print(f"Updated {ct} Honda/Acura with torque=30, gasket=94109-14000, socket=17")
print(f"Socket: {sk}/1615 ({sk/1615*100:.1f}%)")
print(f"Torque: {th}/1615 ({th/1615*100:.1f}%)")
conn.close()
