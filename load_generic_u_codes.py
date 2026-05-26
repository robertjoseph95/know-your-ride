"""
Add the generic SAE J2012 network (U) codes to dtc_codes
========================================================
The two MIT datasets (mytrile/fabiovila) omit the generic network codes
(U0100 "Lost Communication With ECM/PCM A", etc.). Those definitions are public
SAE J2012 / ISO 15031-6 standard facts -- a code->description mapping isn't
copyrightable (Feist). We read them from python-obd's compiled table, using it
purely as a transcription of the public standard.

Additive: INSERT OR IGNORE, so existing codes (and the MIT-sourced U codes
already present) are untouched; only new generic U codes are added.

Run:  python load_generic_u_codes.py
"""

import sqlite3
import shutil
import datetime
import os
import obd.codes as oc

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wrench_vehicles.db")


def main():
    u_codes = {k: v.strip() for k, v in oc.DTC.items()
               if k.startswith("U") and v and v.strip()}
    print(f"Generic U codes in SAE/python-obd table: {len(u_codes)}")

    backup = f"{DB}.pre_ucodes_{datetime.datetime.now():%Y%m%d_%H%M%S}.bak"
    shutil.copy2(DB, backup)
    print(f"Backup: {os.path.basename(backup)}")

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=15000")
    cur = con.cursor()
    before = cur.execute("SELECT COUNT(*) FROM dtc_codes WHERE code LIKE 'U%'").fetchone()[0]

    added = 0
    for code, desc in u_codes.items():
        cur.execute("""INSERT OR IGNORE INTO dtc_codes
            (code, description, urgency, cost_low, cost_high, possible_causes, systems)
            VALUES (?,?,?,?,?,?,?)""",
            (code, desc, None, None, None, "[]", "Network"))
        added += cur.rowcount
    con.commit()

    total = cur.execute("SELECT COUNT(*) FROM dtc_codes").fetchone()[0]
    u_total = cur.execute("SELECT COUNT(*) FROM dtc_codes WHERE code LIKE 'U%'").fetchone()[0]
    u0100 = cur.execute("SELECT description FROM dtc_codes WHERE code='U0100'").fetchone()
    con.close()

    print("\n--- Done ---------------------------")
    print(f"U codes before : {before}")
    print(f"New U added    : {added}")
    print(f"U codes now    : {u_total}")
    print(f"dtc_codes total: {total}")
    print(f"U0100 check    : {u0100[0] if u0100 else 'MISSING'}")


if __name__ == "__main__":
    main()
