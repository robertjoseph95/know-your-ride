"""
Populate dtc_codes from openly-licensed SAE J2012 DTC datasets
==============================================================
Sources (both MIT-licensed, unioned for best coverage):
  1. mytrile/obd-trouble-codes  (MIT, (c) 2014 Dimitar Kostov)
     3,071 codes -> P 1138, B 1147, C 487, U 299  (the only B/Chassis + C/Body source)
  2. fabiovila/OBDIICodes        (MIT, (c) 2023 Fabio)
     P-code table that adds ~1,650 more P codes (incl. hex P000A-style) not in #1

Why these: obd-codes.com forbids scraping (robots.txt Disallow: / + Cloudflare); and
python-obd's table is GPL. These two are MIT. The code->description mappings are the
public SAE J2012 / ISO 15031-6 standard definitions.

Known gap: the generic network codes (U0100-style) aren't in either MIT dataset.

Behaviour: ADDITIVE. Existing codes (e.g. the 467 from the vehicle-finder API, which
carry a system field) are kept as-is; only codes not already present are inserted.
New rows get description + a category in `systems`; urgency/cost stay NULL.

Run:  python load_dtc_dataset.py
"""

import sqlite3
import csv
import io
import os
import json
import shutil
import datetime
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "wrench_vehicles.db")
CATEGORY = {"P": "Powertrain", "B": "Body", "C": "Chassis", "U": "Network"}

MYTRILE_URL = "https://raw.githubusercontent.com/mytrile/obd-trouble-codes/master/obd-trouble-codes.csv"
FABIO_URL = "https://raw.githubusercontent.com/fabiovila/OBDIICodes/master/codes.json"


def _cached(url, fname):
    path = os.path.join(HERE, fname)
    if os.path.exists(path):
        print(f"Using cached {fname}")
        return open(path, encoding="utf-8").read()
    print(f"Downloading {fname} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "wrench-dtc-loader"})
    text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    open(path, "w", encoding="utf-8").write(text)
    return text


def build_dataset():
    """Union of the two MIT datasets; mytrile's (cleaner) description wins on conflict."""
    dataset = {}
    # fabiovila first (P-only), then mytrile overrides for shared codes
    fab = json.loads(_cached(FABIO_URL, "dtc_dataset_fabiovila.json"))
    for o in fab:
        code = str(o.get("Code", "")).split("/")[0].strip().upper()
        desc = (o.get("Description") or "").strip()
        if len(code) == 5 and code[0] in CATEGORY and desc:
            dataset[code] = desc
    myt = _cached(MYTRILE_URL, "dtc_dataset_mytrile.csv")
    for r in csv.reader(io.StringIO(myt)):
        if len(r) >= 2 and r[0].strip():
            code, desc = r[0].strip().upper(), r[1].strip()
            if code[0] in CATEGORY and desc:
                dataset[code] = desc
    return dataset


def main():
    dataset = build_dataset()
    print(f"Dataset codes parsed (union): {len(dataset)}")

    backup = f"{DB}.pre_dtcload_{datetime.datetime.now():%Y%m%d_%H%M%S}.bak"
    shutil.copy2(DB, backup)
    print(f"Backup: {os.path.basename(backup)}")

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=15000")
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS dtc_codes (
        code TEXT PRIMARY KEY, description TEXT, urgency TEXT,
        cost_low INTEGER, cost_high INTEGER, possible_causes TEXT, systems TEXT)""")

    before = cur.execute("SELECT COUNT(*) FROM dtc_codes").fetchone()[0]
    added = 0
    for code, desc in dataset.items():
        # additive: don't clobber an existing code's richer data
        cur.execute("""INSERT OR IGNORE INTO dtc_codes
            (code, description, urgency, cost_low, cost_high, possible_causes, systems)
            VALUES (?,?,?,?,?,?,?)""",
            (code, desc, None, None, None, "[]", CATEGORY[code[0]]))
        added += cur.rowcount
    con.commit()

    total = cur.execute("SELECT COUNT(*) FROM dtc_codes").fetchone()[0]
    by = cur.execute("""SELECT substr(code,1,1) p, COUNT(*) FROM dtc_codes
                        GROUP BY p ORDER BY p""").fetchall()
    con.close()

    print("\n--- Done ---------------------------")
    print(f"dtc_codes before : {before}")
    print(f"New codes added  : {added}")
    print(f"dtc_codes total  : {total}")
    print(f"By prefix        : {dict(by)}")


if __name__ == "__main__":
    main()
