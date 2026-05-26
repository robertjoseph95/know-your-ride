"""
WRENCH — Script 02: EPA FuelEconomy.gov MPG + EV Range Backfill
================================================================
Fills 41 vehicles missing MPG data. Also adds EV range (MPGe) for
electric vehicles and plugs in annual fuel cost where missing.

API: https://www.fueleconomy.gov/ws/rest/ (free, no key required)
Docs: https://www.fueleconomy.gov/feg/ws/index.shtml

Strategy:
  1. Search EPA by year+make+model → get vehicle ID(s)
  2. Fetch full spec per ID (city/hwy/combined, MPGe, range, fuel cost)
  3. Insert into fuel_economy table
  4. For EVs: store range_miles and mpge in a new column (added if missing)

Run: python3 02_epa_mpg_backfill.py
Estimated time: ~10 min for 41 vehicles + full EV enrichment pass
"""

import sqlite3
import requests
import time
import json
from pathlib import Path

DB_PATH    = "wrench_vehicles.db"
RATE_LIMIT = 0.25   # EPA allows ~4 req/sec comfortably
LOG_FILE   = "epa_backfill.log"
EPA_BASE   = "https://www.fueleconomy.gov/ws/rest"

HEADERS = {"Accept": "application/json"}


# ── EPA helpers ──────────────────────────────────────────────────────────────

def epa_get(path, params=None):
    try:
        r = requests.get(f"{EPA_BASE}/{path}", params=params,
                         headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


def epa_search(year, make, model):
    """Return list of EPA vehicle IDs for this year/make/model."""
    data = epa_get("vehicle/menu/options", params={
        "year": year, "make": make, "model": model
    })
    if not data:
        return []
    items = data.get("menuItem", [])
    if isinstance(items, dict):        # single result comes back as dict
        items = [items]
    return [item["value"] for item in items if "value" in item]


def epa_vehicle(epa_id):
    """Fetch full vehicle record from EPA by their internal ID."""
    return epa_get(f"vehicle/{epa_id}")


def epa_make_list(year):
    """Get all makes EPA knows about for a given year (for fuzzy matching)."""
    data = epa_get("vehicle/menu/make", params={"year": year})
    if not data:
        return []
    items = data.get("menuItem", [])
    if isinstance(items, dict):
        items = [items]
    return [i.get("value","") for i in items]


def epa_model_list(year, make):
    data = epa_get("vehicle/menu/model", params={"year": year, "make": make})
    if not data:
        return []
    items = data.get("menuItem", [])
    if isinstance(items, dict):
        items = [items]
    return [i.get("value","") for i in items]


def normalize_make(make, epa_makes):
    """Case-insensitive match of our make name to EPA's make list."""
    lower = {m.lower(): m for m in epa_makes}
    return lower.get(make.lower())


def normalize_model(model, epa_models):
    """Fuzzy match model name against EPA list."""
    lower = {m.lower(): m for m in epa_models}
    if model.lower() in lower:
        return lower[model.lower()]
    # Try prefix
    for k, v in lower.items():
        if k.startswith(model.lower()[:6]):
            return v
    return None


def parse_epa_record(rec):
    """
    Extract the fields we care about from an EPA vehicle record.
    Returns a dict ready to insert into fuel_economy.
    """
    if not rec:
        return None

    def safe_int(v):
        try: return int(v)
        except: return None

    def safe_float(v):
        try: return float(v)
        except: return None

    # City/Hwy/Comb — EPA has "city08", "highway08", "comb08" for regular
    # and "cityA08", "highwayA08", "combA08" for second fuel (PHEVs)
    city  = safe_int(rec.get("city08"))
    hwy   = safe_int(rec.get("highway08"))
    comb  = safe_int(rec.get("comb08"))

    # EV / electric range
    range_miles = safe_int(rec.get("range")) or safe_int(rec.get("rangeA"))
    mpge        = safe_int(rec.get("combA08")) or safe_int(rec.get("city08A"))

    # Annual fuel cost (EPA estimate at national avg price)
    annual_cost = safe_int(rec.get("fuelCost08"))

    # Engine / transmission / drive
    engine   = rec.get("displ")          # e.g. "2.5"
    trans    = rec.get("trany")          # e.g. "Automatic 6-spd"
    drive    = rec.get("drive")          # e.g. "Front-Wheel Drive"
    fuel_type = rec.get("fuelType1","")

    return {
        "city_mpg":        city,
        "highway_mpg":     hwy,
        "combined_mpg":    comb,
        "annual_fuel_cost": annual_cost,
        "engine":          str(engine) if engine else None,
        "transmission":    trans,
        "drive":           drive,
        "range_miles":     range_miles,
        "mpge":            mpge,
        "fuel_type":       fuel_type,
    }


# ── DB helpers ───────────────────────────────────────────────────────────────

def ensure_ev_columns(cur):
    """Add range_miles and mpge columns to fuel_economy if they don't exist."""
    cur.execute("PRAGMA table_info(fuel_economy)")
    cols = [r[1] for r in cur.fetchall()]
    if "range_miles" not in cols:
        cur.execute("ALTER TABLE fuel_economy ADD COLUMN range_miles INTEGER")
        print("  Added column: range_miles")
    if "mpge" not in cols:
        cur.execute("ALTER TABLE fuel_economy ADD COLUMN mpge INTEGER")
        print("  Added column: mpge")
    if "fuel_type" not in cols:
        cur.execute("ALTER TABLE fuel_economy ADD COLUMN fuel_type TEXT")
        print("  Added column: fuel_type")


def insert_mpg(cur, vehicle_id, rec):
    cur.execute("""
        INSERT INTO fuel_economy
          (vehicle_id, city_mpg, highway_mpg, combined_mpg, annual_fuel_cost,
           engine, transmission, drive, range_miles, mpge, fuel_type)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        vehicle_id,
        rec["city_mpg"], rec["highway_mpg"], rec["combined_mpg"],
        rec["annual_fuel_cost"], rec["engine"], rec["transmission"],
        rec["drive"], rec["range_miles"], rec["mpge"], rec["fuel_type"]
    ))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    log  = open(LOG_FILE, "w")

    ensure_ev_columns(cur)
    conn.commit()

    # ── Pass 1: Fill vehicles with no MPG at all ──────────────────────────
    cur.execute("""
        SELECT v.id, v.year, v.make, v.model FROM vehicles v
        LEFT JOIN fuel_economy fe ON fe.vehicle_id = v.id
        WHERE fe.vehicle_id IS NULL
        ORDER BY v.make, v.year, v.model
    """)
    missing = cur.fetchall()
    print(f"Pass 1: {len(missing)} vehicles missing MPG data\n")

    updated = 0
    for i, v in enumerate(missing):
        vid, year, make, model = v["id"], v["year"], v["make"], v["model"]
        label = f"{year} {make} {model}"
        print(f"[{i+1}/{len(missing)}] {label}...", end=" ", flush=True)

        # Normalize make against EPA list
        epa_makes = epa_make_list(year)
        time.sleep(RATE_LIMIT)
        epa_make = normalize_make(make, epa_makes)
        if not epa_make:
            print("✗  make not in EPA")
            log.write(f"MISS_MAKE {label}\n")
            continue

        # Normalize model
        epa_models = epa_model_list(year, epa_make)
        time.sleep(RATE_LIMIT)
        epa_model = normalize_model(model, epa_models)
        if not epa_model:
            print("✗  model not in EPA")
            log.write(f"MISS_MODEL {label}\n")
            continue

        # Search for vehicle IDs
        epa_ids = epa_search(year, epa_make, epa_model)
        time.sleep(RATE_LIMIT)
        if not epa_ids:
            print("✗  no results")
            log.write(f"MISS_IDS {label}\n")
            continue

        # Fetch each variant and insert
        inserted = 0
        for eid in epa_ids[:6]:   # cap at 6 variants per model
            rec = epa_vehicle(eid)
            time.sleep(RATE_LIMIT)
            parsed = parse_epa_record(rec)
            if parsed and parsed["combined_mpg"]:
                insert_mpg(cur, vid, parsed)
                inserted += 1

        if inserted:
            conn.commit()
            updated += 1
            print(f"✓  {inserted} variants inserted")
            log.write(f"OK  {label}: {inserted} variants\n")
        else:
            print("✗  no usable records")
            log.write(f"MISS_PARSE {label}\n")

    # ── Pass 2: Enrich existing EVs with range_miles + MPGe ──────────────
    print(f"\nPass 2: Enriching EVs with range + MPGe data...")
    cur.execute("""
        SELECT DISTINCT v.id, v.year, v.make, v.model
        FROM vehicles v
        JOIN fuel_economy fe ON fe.vehicle_id = v.id
        WHERE (v.make IN ('Tesla','Lucid','Rivian','Polestar') OR fe.combined_mpg IS NULL)
          AND fe.range_miles IS NULL
        ORDER BY v.make, v.year, v.model
    """)
    ev_targets = cur.fetchall()
    print(f"Found {len(ev_targets)} EVs to enrich\n")

    ev_updated = 0
    for v in ev_targets:
        vid, year, make, model = v["id"], v["year"], v["make"], v["model"]
        label = f"{year} {make} {model}"
        print(f"  {label}...", end=" ", flush=True)

        epa_makes  = epa_make_list(year); time.sleep(RATE_LIMIT)
        epa_make   = normalize_make(make, epa_makes)
        if not epa_make: print("skip"); continue

        epa_models = epa_model_list(year, epa_make); time.sleep(RATE_LIMIT)
        epa_model  = normalize_model(model, epa_models)
        if not epa_model: print("skip"); continue

        epa_ids = epa_search(year, epa_make, epa_model); time.sleep(RATE_LIMIT)
        for eid in epa_ids[:4]:
            rec = epa_vehicle(eid); time.sleep(RATE_LIMIT)
            if not rec: continue
            range_m = None
            try: range_m = int(rec.get("range") or rec.get("rangeA") or 0) or None
            except: pass
            mpge = None
            try: mpge = int(rec.get("combA08") or rec.get("comb08") or 0) or None
            except: pass
            if range_m or mpge:
                cur.execute("""
                    UPDATE fuel_economy SET range_miles=?, mpge=?
                    WHERE vehicle_id=? AND (range_miles IS NULL OR mpge IS NULL)
                """, (range_m, mpge, vid))
                ev_updated += 1
        conn.commit()
        print(f"range={range_m} mpge={mpge}")

    conn.close()
    log.close()
    print(f"\n── Done ──────────────────────────────────")
    print(f"MPG backfill  : {updated}/{len(missing)} vehicles")
    print(f"EV enriched   : {ev_updated} records")
    print(f"Log           : {LOG_FILE}")


if __name__ == "__main__":
    main()
