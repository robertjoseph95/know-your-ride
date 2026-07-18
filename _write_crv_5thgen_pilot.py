"""Replay-safe IC-01 quarantine for five fifth-generation Honda CR-V rows.

This file originally wrote one 2018 owner's-manual table across 2017, 2018,
2020, 2021, and 2022 vehicle identities.  The table combines 1.5T/2.4L,
trim-specific tire, and 2WD/AWD values, so source verification alone did not
establish exact-configuration applicability.

The historical values remain in the local research database for a future
exact-year recovery campaign.  Rerunning this script can only relabel their
sources with the IC-01 quarantine token; it contains no executable path that
can restore an accepted source or republish the mixed values.

Historical lead retained for research only (not publication authority for
all five rows): official 2018 Honda CR-V Owner's Manual,
techinfo.honda.com/rjanisis/pubs/OM/AH/ATLA1818OM/enu/ATLA1818OM.PDF.
"""

import datetime
import os
import shutil
import sqlite3

from files.ic01_quarantine import (
    EXPECTED_DB_ROWS,
    QUARANTINED_VEHICLE_IDS,
    QUARANTINE_SOURCE,
)


ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
VIDS = tuple(sorted(QUARANTINED_VEHICLE_IDS))


def apply_quarantine(con):
    """Apply the exact source token and fail if the expected cohort drifts."""
    placeholders = ",".join("?" for _ in VIDS)
    expected_by_table = {}
    for table, expected in EXPECTED_DB_ROWS.items():
        expected_per_id = 3 if table == "maintenance" else 1
        expected_by_id = {vehicle_id: expected_per_id for vehicle_id in VIDS}
        observed_by_id = dict(con.execute(
            "SELECT vehicle_id, COUNT(*) FROM %s WHERE vehicle_id IN (%s) GROUP BY vehicle_id"
            % (table, placeholders),
            VIDS,
        ).fetchall())
        if observed_by_id != expected_by_id:
            raise RuntimeError(
                "%s IC-01 rows by vehicle %r; expected %r"
                % (table, observed_by_id, expected_by_id)
            )
        if sum(observed_by_id.values()) != expected:
            raise RuntimeError("%s IC-01 total does not match %d" % (table, expected))
        expected_by_table[table] = expected_by_id

    counts = {}
    try:
        for table, expected in EXPECTED_DB_ROWS.items():
            con.execute(
                "UPDATE %s SET source=? WHERE vehicle_id IN (%s)" % (table, placeholders),
                (QUARANTINE_SOURCE,) + VIDS,
            )
            quarantined_by_id = dict(con.execute(
                "SELECT vehicle_id, COUNT(*) FROM %s "
                "WHERE vehicle_id IN (%s) AND source=? GROUP BY vehicle_id"
                % (table, placeholders),
                VIDS + (QUARANTINE_SOURCE,),
            ).fetchall())
            if quarantined_by_id != expected_by_table[table]:
                raise RuntimeError(
                    "%s quarantined rows by vehicle %r; expected %r"
                    % (table, quarantined_by_id, expected_by_table[table])
                )
            counts[table] = expected
        con.commit()
    except Exception:
        con.rollback()
        raise
    return counts


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB + ".bak-ic01-crv-" + ts
    shutil.copy2(DB, backup)
    print("Backup:", os.path.basename(backup))

    con = sqlite3.connect(DB)
    try:
        counts = apply_quarantine(con)
    finally:
        con.close()

    for table, count in counts.items():
        print("  %s: %d row(s) -> %s" % (table, count, QUARANTINE_SOURCE))
    print("DONE - five CR-V identities retained; curated values quarantined.")


if __name__ == "__main__":
    main()
