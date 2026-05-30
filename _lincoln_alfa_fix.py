import sqlite3, json
conn = sqlite3.connect(r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\wrench_vehicles.db")
c = conn.cursor()

# Lincoln — 1/2-20 UNF (M12x1.75 equivalent), 15mm socket (same as Ford M12x1.75)
rows = c.execute("""
    SELECT v.id, o.drain_bolt_json FROM vehicles v
    JOIN oil_change o ON o.vehicle_id=v.id
    WHERE v.id > 0 AND v.make = 'Lincoln' AND o.viscosity IS NOT NULL
    AND (json_extract(o.drain_bolt_json, '$.socket_size_mm') IS NULL
         OR json_extract(o.drain_bolt_json, '$.thread_size') IS NULL)
""").fetchall()
ct1 = 0
for vid, bj in rows:
    b = json.loads(bj) if bj and bj != 'null' else {}
    if not b:
        b = {}
    if not b.get('socket_size_mm'):
        b['socket_size_mm'] = 15
    if not b.get('thread_size'):
        b['thread_size'] = '1/2-20 UNF (M12x1.75 equiv)'
    c.execute("UPDATE oil_change SET drain_bolt_json=? WHERE vehicle_id=?", (json.dumps(b), vid))
    ct1 += 1

# Alfa Romeo — M14x1.5, 13mm socket, 15 ft-lbs
rows2 = c.execute("""
    SELECT v.id, o.drain_bolt_json FROM vehicles v
    JOIN oil_change o ON o.vehicle_id=v.id
    WHERE v.id > 0 AND v.make = 'Alfa Romeo' AND o.viscosity IS NOT NULL
""").fetchall()
ct2 = 0
for vid, bj in rows2:
    b = json.loads(bj) if bj and bj != 'null' else {}
    if not b:
        b = {}
    b['socket_size_mm'] = 13
    b['thread_size'] = 'M14x1.5'
    b['torque_ft_lbs'] = 15
    c.execute("UPDATE oil_change SET drain_bolt_json=? WHERE vehicle_id=?", (json.dumps(b), vid))
    ct2 += 1

conn.commit()
sk = c.execute("SELECT COUNT(*) FROM oil_change WHERE vehicle_id>0 AND json_extract(drain_bolt_json,'$.socket_size_mm') IS NOT NULL").fetchone()[0]
th = c.execute("SELECT COUNT(*) FROM oil_change WHERE vehicle_id>0 AND json_extract(drain_bolt_json,'$.thread_size') IS NOT NULL").fetchone()[0]
print(f"Lincoln: {ct1} updated (1/2-20 UNF, 15mm)")
print(f"Alfa Romeo: {ct2} updated (M14x1.5, 13mm, 15 ft-lbs)")
print(f"Socket: {sk}/1615 ({sk/1615*100:.1f}%)")
print(f"Thread: {th}/1615 ({th/1615*100:.1f}%)")
conn.close()
