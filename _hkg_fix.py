import sqlite3, json
conn = sqlite3.connect(r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\wrench_vehicles.db")
c = conn.cursor()
# Update all Hyundai/Kia/Genesis missing socket — skip EVs
ev_models = ('EV9','EV6','Ioniq 5','Ioniq 6','GV60','Electrified G80','Electrified GV70')
rows = c.execute("""
    SELECT v.id, v.model, o.drain_bolt_json FROM vehicles v
    JOIN oil_change o ON o.vehicle_id=v.id
    WHERE v.id > 0 AND v.make IN ('Hyundai','Kia','Genesis')
    AND o.viscosity IS NOT NULL
""").fetchall()
ct = 0
for vid, model, bj in rows:
    if model in ev_models:
        continue
    b = json.loads(bj) if bj and bj != 'null' else {}
    if not b:
        b = {}
    ch = False
    if not b.get('socket_size_mm'):
        b['socket_size_mm'] = 17
        ch = True
    if not b.get('thread_size'):
        b['thread_size'] = 'M14x1.5'
        ch = True
    if not b.get('torque_ft_lbs'):
        b['torque_ft_lbs'] = 25
        ch = True
    if ch:
        c.execute("UPDATE oil_change SET drain_bolt_json=? WHERE vehicle_id=?", (json.dumps(b), vid))
        ct += 1
conn.commit()
sk = c.execute("SELECT COUNT(*) FROM oil_change WHERE vehicle_id>0 AND json_extract(drain_bolt_json,'$.socket_size_mm') IS NOT NULL").fetchone()[0]
th = c.execute("SELECT COUNT(*) FROM oil_change WHERE vehicle_id>0 AND json_extract(drain_bolt_json,'$.thread_size') IS NOT NULL").fetchone()[0]
print(f"Updated {ct} Hyundai/Kia/Genesis vehicles")
print(f"Socket: {sk}/1615 ({sk/1615*100:.1f}%)")
print(f"Thread: {th}/1615 ({th/1615*100:.1f}%)")
conn.close()
