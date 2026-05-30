#!/usr/bin/env python3
"""
Wrench - Open-source dataset import (read external sources, INSERT OR IGNORE only).
No deletions, no overwrites of existing rows.

TASK 1  Wal33D/dtc-database  -> dtc_codes        (expand code coverage)
TASK 2  chargeprice/open-ev-data -> ev_specs     (EV battery/charge enrichment)
TASK 3  Wal33D WMI            -> vpic_specs       (NOT FEASIBLE - reported, not run)
"""
import os, sys, io, json, sqlite3, logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))
DB   = os.path.join(ROOT, "wrench_vehicles.db")
OSS  = os.path.join(ROOT, "oss_import")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(os.path.join(ROOT, "wrench_opensource_import.log"),
                                  encoding="utf-8"),
              logging.StreamHandler()])
log = logging.getLogger(__name__)

conn = sqlite3.connect(DB)
log.info("=" * 70)
log.info("OPEN-SOURCE IMPORT START")

# ============================ TASK 1: DTC ============================
log.info("-" * 70)
log.info("TASK 1: Wal33D/dtc-database -> dtc_codes (INSERT OR IGNORE)")
ext = sqlite3.connect(f"file:{os.path.join(OSS,'dtc-database','data','dtc_codes.db')}?mode=ro", uri=True)

# external has one row per (code, manufacturer, locale); collapse to one description
# per code, PREFERRING the generic SAE definition so shared codes keep canonical meaning.
best = {}   # code -> (is_generic, description)
for code, desc, gen in ext.execute(
        "SELECT code, description, is_generic FROM dtc_definitions WHERE locale='en'"):
    cur = best.get(code)
    if cur is None or (gen and not cur[0]):
        best[code] = (gen, desc)
ext.close()

existing = {r[0] for r in conn.execute("SELECT code FROM dtc_codes")}
before = len(existing)
new_codes = [c for c in best if c not in existing]
already   = [c for c in best if c in existing]

ins = 0
for code in new_codes:
    cur = conn.execute("INSERT OR IGNORE INTO dtc_codes (code, description) VALUES (?,?)",
                       (code, best[code][1]))
    ins += cur.rowcount
conn.commit()
after = conn.execute("SELECT COUNT(*) FROM dtc_codes").fetchone()[0]
log.info(f"  external unique codes (en): {len(best)}")
log.info(f"  already in our DB (skipped, not overwritten): {len(already)}")
log.info(f"  NEW codes inserted: {ins}")
log.info(f"  dtc_codes total: {before} -> {after}")

# ============================ TASK 2: EV ============================
log.info("-" * 70)
log.info("TASK 2: chargeprice/open-ev-data -> ev_specs")
ev = json.load(open(os.path.join(OSS, "ev-data.json"), encoding="utf-8"))
log.info(f"  open-ev-data records available: {len(ev)} (dataset reduced to a sample "
         f"since Chargeprice moved to a paid API)")
conn.execute("""CREATE TABLE IF NOT EXISTS ev_specs (
    vehicle_id INTEGER PRIMARY KEY,
    battery_kwh REAL, usable_kwh REAL, max_charge_kw REAL, range_miles REAL,
    source TEXT)""")
conn.commit()

def norm(s): return (s or "").lower().replace("-", " ").strip()
veh = conn.execute("SELECT id, year, make, model FROM vehicles").fetchall()
matched = 0
for r in ev:
    brand = norm(r.get("brand")); model = norm(r.get("model"))
    yr = r.get("release_year")
    usable = r.get("usable_battery_size")
    dc = (r.get("dc_charger") or {}).get("max_power")
    mtoken = model.split()[0] if model else ""   # e-tron 50 -> e-tron ; i3s -> i3s
    for vid, vyr, vmk, vmd in veh:
        if norm(vmk) != brand:
            continue
        vm = norm(vmd)
        if not (mtoken and (mtoken in vm or vm in model or model in vm)):
            continue
        if yr and vyr and abs(vyr - yr) > 2:   # allow +/-2yr; Tesla has no year -> match all
            continue
        cur = conn.execute(
            "INSERT OR IGNORE INTO ev_specs (vehicle_id,battery_kwh,usable_kwh,max_charge_kw,range_miles,source) "
            "VALUES (?,?,?,?,?,?)",
            (vid, None, usable, dc, None, "open-ev-data"))
        if cur.rowcount:
            matched += 1
            log.info(f"    matched vid={vid} {vyr} {vmk} {vmd}  <- {r.get('brand')} {r.get('model')} "
                     f"(usable={usable}kWh dc={dc}kW)")
conn.commit()
log.info(f"  EV vehicles enriched: {matched}")
log.info(f"  NOTE: source lacks total battery_kWh and range -> those columns left NULL")

# ============================ TASK 3: WMI ============================
log.info("-" * 70)
log.info("TASK 3: Wal33D WMI -> vpic_specs  ==> SKIPPED (not feasible)")
log.info("  Reason 1: no VIN column exists anywhere in wrench_vehicles.db, so there is")
log.info("            no WMI prefix to match against.")
log.info("  Reason 2: WMI data maps a 3-char prefix -> MANUFACTURER only; it does NOT")
log.info("            contain body_class or plant_city (the NULL fields to backfill).")
log.info("  Reason 3: the bundled wmi.csv manufacturer names are in Chinese.")
log.info("  No rows written. License preserved as nhtsa_vin_decoder_wal33d_LICENSE.txt.")

log.info("-" * 70)
log.info("IMPORT COMPLETE")
log.info("=" * 70)
conn.close()
