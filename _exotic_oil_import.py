"""
Import manually-researched exotic oil specs into wrench_vehicles.db.
====================================================================
Replaces the generic 0W-20/4.5qt/API-SP Vehicle Finder fallback (nulled in a
prior fix) with confirmed per-model specs for 7 exotic makes.

Matching: by make + model, and by engine for models that ship multiple engines.
NOTE: the DB stores ONE vehicle row per model-year that aggregates every engine
variant (e.g. a single "Aston Martin DB11" row covers both the 5.2 V12 and the
4.0 V8), while oil_change holds ONE row per vehicle. So for multi-engine models
we store the spec for the LARGEST-displacement engine actually present in that
vehicle's fuel-economy data (the flagship) and record the exact engine in the
notes. The only case where this changes viscosity is the Maserati Grecale
(2.0 hybrid = 0W-30 vs 3.0 V6 = 5W-40); see the run report.

Each oil_change row gets: viscosity, oil_type='Full Synthetic',
capacity_with_filter (qt), oem_spec, and the note in drain_bolt_json {"notes":...}.
UPDATE if a row exists, else INSERT. Honda/Mazda/Toyota are never touched.

Run:  python _exotic_oil_import.py
"""

import sqlite3
import json
import os
import shutil
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "wrench_vehicles.db")

# (viscosity, capacity_qt, oem_spec, note)  -- ASCII notes (downstream output is ASCII)
SINGLE = {
    ("Rolls-Royce", "Ghost"):    ("0W-40", 14.8, "BMW LL-01",
                                   "6.75L V12 - BMW LL-01 or LL-12 FE approved"),
    ("Rolls-Royce", "Cullinan"): ("5W-30", 14.8, "BMW LL-04/ACEA C3",
                                   "6.75L V12 - Castrol EDGE Euro 5W-30 or Mobil 1 ESP 5W-30"),
    ("Aston Martin", "Vantage"): ("0W-40", 9.5, "ACEA A3/B4 / API SN+",
                                   "4.0L AMG-derived V8 - Mobil 1 European 0W-40 recommended"),
    ("Aston Martin", "DBX"):     ("0W-40", 9.5, "ACEA A3/B4", "4.0L twin-turbo V8"),
    ("Ferrari", "Roma"):         ("5W-40", 13.7, "ACEA A3/B4 / API SN/CF",
                                   "3.9L V8 dry-sump - warm up before checking oil level"),
    ("Lamborghini", "Urus"):     ("5W-40", 10.5, "VW 511 00",
                                   "4.0L V8 - must meet VW 511 00 spec, 0W-40 also accepted"),
    ("McLaren", "720S"):         ("5W-40", 8.9, "ACEA C3 / API SN",
                                   "4.0L dry-sump - add 5-6L first, warm up, top off via dashboard. "
                                   "Check at 194-202F. DO NOT OVERFILL."),
    ("McLaren", "GT"):           ("0W-40", 8.0, "Gulf Formula Elite / ACEA C3",
                                   "4.0L dry-sump - extremely sensitive to overfill. "
                                   "Use dashboard monitor only."),
}

# model -> list of (engine_displacement_L, spec) ; pick the largest present
VARIANT = {
    ("Aston Martin", "DB11"): [
        (5.2, ("0W-20", 11.4, "Aston Martin approved", "5.2L twin-turbo V12")),
        (4.0, ("0W-20", 9.0, "Aston Martin approved", "4.0L V8 - 0W-20 or 5W-40 accepted")),
    ],
    ("Bentley", "Bentayga"): [
        (6.0, ("0W-40", 11.6, "VW 502 00 / VW 505 00",
               "6.0L W12 - 11.6qt service fill, 13.7qt dry fill")),
        (4.0, ("0W-40", 10.0, "VW 511 00 / ACEA C3",
               "4.0L V8 - engine consumes oil normally, carry spare quart")),
    ],
    ("Maserati", "Levante"): [
        (3.8, ("5W-40", 9.0, "Shell Helix Ultra", "3.8L V8 - 5W-40 or 10W-60 accepted")),
        (3.0, ("5W-40", 8.75, "Shell Helix Ultra", "3.0L V6")),
    ],
    ("Maserati", "Grecale"): [
        (3.0, ("5W-40", 8.5, "Shell Helix Ultra", "3.0L V6 Nettuno")),
        (2.0, ("0W-30", 8.0, "ACEA C2 / Fiat 9.55535-GS1",
               "2.0L mild hybrid - Shell Helix Ultra 0W-30 Hybrid")),
    ],
}

# guard: makes we must never touch
FORBIDDEN = {"Honda", "Mazda", "Toyota", "Acura", "Lexus"}


def present_displacements(cur, vid):
    out = set()
    for r in cur.execute("SELECT DISTINCT engine FROM fuel_economy WHERE vehicle_id=?", (vid,)):
        try:
            out.add(round(float(r[0]), 1))
        except (TypeError, ValueError):
            pass
    return out


def upsert_oil(cur, vid, spec):
    visc, cap, oem, note = spec
    drain = json.dumps({"notes": note})
    exists = cur.execute("SELECT 1 FROM oil_change WHERE vehicle_id=?", (vid,)).fetchone()
    if exists:
        cur.execute(
            "UPDATE oil_change SET viscosity=?, oil_type=?, capacity_with_filter=?, "
            "capacity_without_filter=NULL, oem_spec=?, filters_json=NULL, drain_bolt_json=?, "
            "socket=NULL, thread=NULL, gasket=NULL WHERE vehicle_id=?",
            (visc, "Full Synthetic", cap, oem, drain, vid))
        return "UPDATE"
    cur.execute(
        "INSERT INTO oil_change (vehicle_id, viscosity, oil_type, capacity_with_filter, "
        "capacity_without_filter, oem_spec, filters_json, drain_bolt_json, socket, thread, gasket) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (vid, visc, "Full Synthetic", cap, None, oem, None, drain, None, None, None))
    return "INSERT"


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = f"{DB}.bak-exoticoil-{ts}"
    shutil.copy2(DB, bak)
    print(f"Backup: {os.path.basename(bak)}\n")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    makes = tuple(set(m for m, _ in list(SINGLE) + list(VARIANT)))
    rows = cur.execute(
        f"SELECT id, year, make, model FROM vehicles WHERE make IN ({','.join('?' * len(makes))}) "
        "ORDER BY make, model, year", makes).fetchall()

    results = []
    for v in rows:
        vid, key = v["id"], (v["make"], v["model"])
        assert v["make"] not in FORBIDDEN, f"refusing to touch {v['make']}"
        if key in SINGLE:
            spec = SINGLE[key]
            chosen = "model"
        elif key in VARIANT:
            present = present_displacements(cur, vid)
            variants = VARIANT[key]  # already largest-first
            spec = None
            for disp, sp in variants:
                if any(abs(disp - p) <= 0.1 for p in present):
                    spec, chosen = sp, f"{disp}L (present: {sorted(present)})"
                    break
            if spec is None:  # fallback: flagship (first/largest)
                spec, chosen = variants[0][1], f"fallback {variants[0][0]}L (present: {sorted(present)})"
        else:
            results.append((v, None, "SKIP (no spec - e.g. Ghibli)"))
            continue
        action = upsert_oil(cur, vid, spec)
        results.append((v, spec, f"{action} via {chosen}"))

    con.commit()

    # report
    print(f"{'VEHICLE':38} {'VISC':6} {'QT':>5}  {'OEM':24} HOW")
    print("-" * 110)
    updated = 0
    for v, spec, how in results:
        name = f"{v['year']} {v['make']} {v['model']}"
        if spec is None:
            print(f"{name:38} {'-':6} {'-':>5}  {'-':24} {how}")
        else:
            visc, cap, oem, note = spec
            print(f"{name:38} {visc:6} {cap:>5}  {oem[:24]:24} {how}")
            updated += 1
    print("-" * 110)
    print(f"Rows written: {updated}   Skipped: {len(results) - updated}")

    # verify Ghost
    print("\nVERIFY Rolls-Royce Ghost:")
    for r in cur.execute(
            "SELECT v.year, o.viscosity, o.capacity_with_filter cap, o.oem_spec, o.drain_bolt_json "
            "FROM vehicles v JOIN oil_change o ON o.vehicle_id=v.id "
            "WHERE v.make='Rolls-Royce' AND v.model='Ghost' ORDER BY v.year"):
        print(f"  {r['year']} Ghost: {r['viscosity']} / {r['cap']}qt / {r['oem_spec']} / {r['drain_bolt_json']}")
    con.close()


if __name__ == "__main__":
    main()
