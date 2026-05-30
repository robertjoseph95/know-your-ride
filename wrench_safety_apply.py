#!/usr/bin/env python3
"""
SAFETY RATINGS FIX (#2) — apply phase.

Finding: the Vehicle Finder safety-ratings endpoint is NOT a mapping bug. Its
field names match our columns exactly, but it returns null for frontal_crash_driver,
frontal_crash_passenger, and side_pole_rating (0/1379 populated in our DB) — a
source gap. Those ratings ARE available from the authoritative NHTSA SafetyRatings
API, reached via the nhtsa_vehicle_id the VF response carries (which our table
never stored). wrench_nhtsa_safety_prefetch.py fetched them into
nhtsa_safety_cache.json; this script applies them (fill-only, never overwrites
an existing non-null value).
"""
import os, json, sqlite3, logging

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
CACHE = os.path.join(ROOT, "nhtsa_safety_cache.json")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(os.path.join(ROOT, "wrench_safety_ratings_fix.log"), encoding="utf-8"),
              logging.StreamHandler()])
log = logging.getLogger(__name__)

FIELDS = ("frontal_crash_driver", "frontal_crash_passenger", "side_pole_rating")


def main():
    cache = json.load(open(CACHE))
    conn = sqlite3.connect(DB, timeout=30)
    log.info("=" * 64)
    log.info(f"SAFETY APPLY START: {len(cache)} vehicles in NHTSA cache")
    fixed = {f: 0 for f in FIELDS}
    veh_touched = 0
    for vid_s, vals in cache.items():
        vid = int(vid_s)
        sets, params = [], []
        for f in FIELDS:
            v = vals.get(f)
            if v is not None:
                # fill-only: don't overwrite an existing non-null value
                sets.append(f"{f}=COALESCE({f}, ?)")
                params.append(v)
        if not sets:
            continue
        params.append(vid)
        cur = conn.execute(f"UPDATE safety_ratings SET {', '.join(sets)} WHERE vehicle_id=?", params)
        if cur.rowcount:
            veh_touched += 1
    conn.commit()
    # recount populated after apply
    for f in FIELDS:
        fixed[f] = conn.execute(f"SELECT COUNT(*) FROM safety_ratings WHERE {f} IS NOT NULL").fetchone()[0]
    tot = conn.execute("SELECT COUNT(*) FROM safety_ratings").fetchone()[0]
    log.info("SAFETY APPLY COMPLETE")
    log.info(f"  vehicles updated: {veh_touched}")
    for f in FIELDS:
        log.info(f"  {f}: now {fixed[f]}/{tot} non-null (was 0/{tot})")
    log.info("  Source: NHTSA SafetyRatings (authoritative). VF endpoint lacked these fields.")
    log.info("=" * 64)
    conn.close()


if __name__ == "__main__":
    main()
