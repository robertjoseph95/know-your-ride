"""
Task 1: add Maserati Ghibli oil specs.
Task 2: scrub stale 0W-20 / 4.5qt oil text from exotic maintenance descriptions.

UPSERTs the Ghibli oil_change rows (notes in drain_bolt_json.notes), then
rewrites every oil-change maintenance row for the 7 exotic makes whose
description still embeds the old generic 0W-20/4.5qt fallback so it points to
the owner's manual instead. Honda/Mazda/Toyota are never touched.

Run:  python _ghibli_and_maint_fix.py
"""

import sqlite3
import json
import os
import shutil
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "wrench_vehicles.db")

EXOTIC_MAKES = ("Rolls-Royce", "Aston Martin", "Bentley", "Ferrari",
                "Lamborghini", "Maserati", "McLaren")
FORBIDDEN = {"Honda", "Mazda", "Toyota", "Acura", "Lexus"}

# Task 1 spec (ASCII note; downstream output is ASCII)
GHIBLI = ("10W-60", 8.7, "ACEA A3/B4 / API SN",
          "3.0L twin-turbo V6 - 10W-60 required for high heat/performance demands. "
          "Shell Helix Ultra or Pennzoil Ultra Platinum recommended. Use OEM filter.")

# Task 2 replacement for the oil-change maintenance line
MAINT_FIXED = ("Engine oil and filter change. Consult your owner's manual or authorized "
               "dealer for correct oil specification and capacity.")


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = f"{DB}.bak-ghibli-maint-{ts}"
    shutil.copy2(DB, bak)
    print(f"Backup: {os.path.basename(bak)}\n")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # ---------- TASK 1: Maserati Ghibli oil ----------
    visc, cap, oem, note = GHIBLI
    drain = json.dumps({"notes": note})
    ghibli = cur.execute(
        "SELECT id, year FROM vehicles WHERE make='Maserati' AND model='Ghibli' ORDER BY year"
    ).fetchall()
    print("TASK 1 - Maserati Ghibli oil:")
    for v in ghibli:
        exists = cur.execute("SELECT 1 FROM oil_change WHERE vehicle_id=?", (v["id"],)).fetchone()
        if exists:
            cur.execute(
                "UPDATE oil_change SET viscosity=?, oil_type=?, capacity_with_filter=?, "
                "capacity_without_filter=NULL, oem_spec=?, filters_json=NULL, drain_bolt_json=?, "
                "socket=NULL, thread=NULL, gasket=NULL WHERE vehicle_id=?",
                (visc, "Full Synthetic", cap, oem, drain, v["id"]))
            act = "UPDATE"
        else:
            cur.execute(
                "INSERT INTO oil_change (vehicle_id, viscosity, oil_type, capacity_with_filter, "
                "capacity_without_filter, oem_spec, filters_json, drain_bolt_json, socket, thread, gasket) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (v["id"], visc, "Full Synthetic", cap, None, oem, None, drain, None, None, None))
            act = "INSERT"
        print(f"  {act} {v['year']} Maserati Ghibli -> {visc} / {cap}qt / {oem}")

    # ---------- TASK 2: scrub stale maintenance oil text ----------
    rows = cur.execute(
        f"SELECT m.id, v.make FROM maintenance m JOIN vehicles v ON v.id=m.vehicle_id "
        f"WHERE v.make IN ({','.join('?' * len(EXOTIC_MAKES))}) "
        "AND (m.description LIKE '%0W-20%' OR m.description LIKE '%4.5%')",
        EXOTIC_MAKES).fetchall()
    assert all(r["make"] not in FORBIDDEN for r in rows)
    ids = [r["id"] for r in rows]
    from collections import Counter
    by_make = Counter(r["make"] for r in rows)
    if ids:
        cur.executemany("UPDATE maintenance SET description=? WHERE id=?",
                        [(MAINT_FIXED, i) for i in ids])
    print(f"\nTASK 2 - maintenance descriptions scrubbed: {len(ids)} rows")
    for mk, n in sorted(by_make.items()):
        print(f"  {mk}: {n}")

    con.commit()

    # ---------- verify ----------
    print("\nVERIFY Ghibli oil:")
    for r in cur.execute("SELECT v.year, o.viscosity, o.capacity_with_filter cap, o.oem_spec, o.drain_bolt_json "
                         "FROM vehicles v JOIN oil_change o ON o.vehicle_id=v.id "
                         "WHERE v.make='Maserati' AND v.model='Ghibli' ORDER BY v.year"):
        print(f"  {r['year']} Ghibli: {r['viscosity']} / {r['cap']}qt / {r['oem_spec']}")

    print("\nVERIFY no stale 0W-20/4.5 left in these makes' maintenance:")
    left = cur.execute(
        f"SELECT COUNT(*) c FROM maintenance m JOIN vehicles v ON v.id=m.vehicle_id "
        f"WHERE v.make IN ({','.join('?' * len(EXOTIC_MAKES))}) "
        "AND (m.description LIKE '%0W-20%' OR m.description LIKE '%4.5%')", EXOTIC_MAKES).fetchone()["c"]
    print(f"  remaining stale rows: {left}")
    con.close()


if __name__ == "__main__":
    main()
