"""
Patch: backfill EV range into fuel_economy.range_miles from epa_data.range_ev
=============================================================================
The EPA bulk import populated epa_data correctly (range_ev holds the EV range,
e.g. Tesla Model 3 = 310-363 mi), but the step that copied it into
fuel_economy left range_miles at 0/NULL for most EVs ("range_ev field didn't
match").

epa_data is keyed by EPA's granular model names ("Model 3 Long Range") while
our vehicles use the base name ("Model 3"), so we match on
year + make + model-prefix and take the longest (MAX) range_ev per vehicle.

Default action: backfill only rows where range_miles is NULL/0 (true backfill).
Pass --overwrite to also refresh existing values that disagree with epa_data
(10 such rows from the earlier script-02 pass, e.g. Model S 330 -> 402).

Run:  python patch_ev_range.py            (backfill gaps only)
      python patch_ev_range.py --overwrite (also correct stale values)
"""

import sqlite3
import shutil
import datetime
import sys
import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wrench_vehicles.db")
OVERWRITE = "--overwrite" in sys.argv


def main():
    backup = f"{DB}.pre_evrange_{datetime.datetime.now():%Y%m%d_%H%M%S}.bak"
    shutil.copy2(DB, backup)
    print(f"Backup: {os.path.basename(backup)}")

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=30000")
    cur = con.cursor()

    # Longest EPA EV range per vehicle. Restrict to true BEVs (engine='Electric',
    # set by the engine backfill) and to electric epa_data rows -- otherwise a gas
    # model whose name prefixes an EV variant (gas "Mustang" -> "Mustang Mach-E")
    # would wrongly inherit that EV's range.
    cur.execute("""
        SELECT v.id,
               (SELECT MAX(e.range_ev) FROM epa_data e
                 WHERE e.year = v.year
                   AND lower(e.make)  = lower(v.make)
                   AND lower(e.model) LIKE lower(v.model) || '%'
                   AND lower(e.fuel_type) = 'electricity'
                   AND e.range_ev > 0) AS rng
        FROM vehicles v
        WHERE v.engine = 'Electric'
    """)
    ranges = {vid: rng for vid, rng in cur.fetchall() if rng}
    print(f"EV vehicles with an epa_data range: {len(ranges)}")

    filled = corrected = veh = 0
    for vid, rng in ranges.items():
        # backfill the empties
        cur.execute("""UPDATE fuel_economy SET range_miles=?
                       WHERE vehicle_id=? AND (range_miles IS NULL OR range_miles=0)""", (rng, vid))
        f = cur.rowcount
        c = 0
        if OVERWRITE:
            cur.execute("""UPDATE fuel_economy SET range_miles=?
                           WHERE vehicle_id=? AND range_miles IS NOT NULL
                             AND range_miles<>0 AND range_miles<>?""", (rng, vid, rng))
            c = cur.rowcount
        if f or c:
            veh += 1
        filled += f
        corrected += c

    con.commit()

    # verify no matched-EV rows remain at 0/NULL
    ids = tuple(ranges) or (0,)
    ph = ",".join("?" * len(ids))
    remaining = cur.execute(
        f"SELECT count(*) FROM fuel_economy WHERE vehicle_id IN ({ph}) "
        f"AND (range_miles IS NULL OR range_miles=0)", ids).fetchone()[0]
    con.close()

    print(f"Backfilled (were 0/NULL): {filled} rows")
    if OVERWRITE:
        print(f"Corrected (stale values): {corrected} rows")
    print(f"Vehicles touched        : {veh}")
    print(f"Matched-EV rows still 0  : {remaining}")
    if not OVERWRITE:
        print("(Run with --overwrite to also refresh the stale script-02 values.)")


if __name__ == "__main__":
    main()
