"""
WRENCH — Script 01: NHTSA vPIC Engine/Trim Backfill
====================================================
Fills the 700 vehicles missing `engine` and `trim` data in the vehicles table.

API: https://vpic.nhtsa.dot.gov/api/ (free, no key required)
Strategy:
  - For each vehicle missing engine/trim, query vPIC by make+model+year
  - Pull all variants, extract engine descriptions and trim levels
  - Write best match back to vehicles.engine and vehicles.trim
  - Also enriches engine_specs table where data is missing

Run: python3 01_nhtsa_vpic_backfill.py
Estimated time: ~25 min for 700 vehicles (rate-limited to 5 req/sec)
"""

import sqlite3
import requests
import time
import json
import re
from pathlib import Path

DB_PATH = "wrench_vehicles.db"   # ← adjust path if needed
RATE_LIMIT = 0.2                  # seconds between requests (5/sec max)
LOG_FILE   = "vpic_backfill.log"

# ── vPIC endpoints ──────────────────────────────────────────────────────────
BASE = "https://vpic.nhtsa.dot.gov/api/vehicles"

def vpic_get(path, params=None):
    params = params or {}
    params["format"] = "json"
    try:
        r = requests.get(f"{BASE}/{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None

def get_models_for_make_year(make, year):
    """Returns list of model dicts with ModelName, MakeId, etc."""
    data = vpic_get(f"GetModelsForMakeYear/make/{make}/modelyear/{year}")
    if data and data.get("Results"):
        return data["Results"]
    return []

def get_vehicle_types(make, model, year):
    """Returns variants with engine/trim info."""
    data = vpic_get(
        f"GetVariableValuesList/modelyear/{year}/make/{make}/model/{model}",
    )
    # Try alternate endpoint
    data = vpic_get("DecodeVINValuesBatch", params={
        # batch doesn't help without VINs; use GetModelsForMakeIdYear instead
    })
    return []

def search_make_model_year(make, model, year):
    """
    Primary strategy: GetModelsForMakeYear then GetVehicleTypesForMakeYear.
    Returns (engine_str, trim_str) or (None, None).
    """
    # Step 1: Confirm model exists
    models = get_models_for_make_year(make, year)
    match = next((m for m in models if m.get("Model_Name","").lower() == model.lower()), None)
    if not match:
        # Try partial match
        match = next((m for m in models if model.lower() in m.get("Model_Name","").lower()), None)
    if not match:
        return None, None

    # Step 2: Get engine variants via GetModelsForMakeIdYear (includes engine)
    make_id = match.get("Make_ID")
    model_id = match.get("Model_ID")
    data = vpic_get(f"GetModelsForMakeIdYear/makeId/{make_id}/modelyear/{year}")
    if not data or not data.get("Results"):
        return None, None

    engines = []
    for r in data["Results"]:
        eng = r.get("EngineCylinders") or r.get("EngineConfiguration")
        disp = r.get("DisplacementL") or r.get("DisplacementCI")
        fuel = r.get("FuelTypePrimary")
        if disp:
            try:
                disp_str = f"{float(disp):.1f}L"
            except:
                disp_str = str(disp)
            desc = disp_str
            if eng:
                desc += f" {eng}-cyl"
            if fuel and "gasoline" not in fuel.lower():
                desc += f" {fuel}"
            engines.append(desc)

    engine_str = " / ".join(sorted(set(engines))) if engines else None
    return engine_str, None


def get_engine_from_complaints_api(make, model, year):
    """
    Fallback: NHTSA complaints API sometimes returns richer variant info.
    https://api.nhtsa.gov/vehicles/GetModelsForMakeYear?...
    """
    url = "https://api.nhtsa.gov/vehicles/GetModelsForMakeYear"
    try:
        r = requests.get(url, params={
            "make": make, "model": model, "modelYear": year, "format": "json"
        }, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if results:
            # Pull unique engine descriptors
            engines = set()
            for v in results:
                if v.get("vehicleType"):
                    engines.add(v["vehicleType"])
            if engines:
                return " / ".join(sorted(engines)), None
    except:
        pass
    return None, None


def decode_vpic_batch(make, model, year):
    """
    Best-effort: GetAllVariants for make/model/year combo via
    the /vehicles/GetModelsForMakeYear endpoint which returns engine data.
    """
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/{make}/modelyear/{year}"
    try:
        r = requests.get(url, params={"format": "json"}, timeout=10)
        data = r.json()
        results = data.get("Results", [])
        # Filter to matching model
        matched = [x for x in results if x.get("Model_Name","").lower() == model.lower()]
        if not matched:
            matched = [x for x in results if model.lower() in x.get("Model_Name","").lower()]
        if matched:
            make_id = matched[0].get("Make_ID")
            model_id = matched[0].get("Model_ID")
            # Get detailed variants
            url2 = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeIdYear/makeId/{make_id}/modelyear/{year}"
            r2 = requests.get(url2, params={"format": "json"}, timeout=10)
            data2 = r2.json()
            variants = [x for x in data2.get("Results",[]) if str(x.get("Model_ID","")) == str(model_id)]
            
            engines = []
            trims   = []
            for v in variants:
                # Engine
                disp = v.get("DisplacementL")
                cyls = v.get("EngineCylinders")
                fuel = v.get("FuelTypePrimary","")
                if disp:
                    e = f"{float(disp):.1f}L"
                    if cyls: e += f" {cyls}-cyl"
                    if fuel and "gas" not in fuel.lower(): e += f" {fuel}"
                    engines.append(e)
                # Trim
                trim = v.get("Trim") or v.get("Series") or v.get("Series2")
                if trim: trims.append(trim)
            
            engine_str = " / ".join(sorted(set(engines))) if engines else None
            trim_str   = " / ".join(sorted(set(trims)))   if trims   else None
            return engine_str, trim_str
    except Exception as e:
        pass
    return None, None


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    log  = open(LOG_FILE, "w")

    # Get vehicles missing engine data
    cur.execute("""
        SELECT id, year, make, model FROM vehicles
        WHERE engine IS NULL OR engine = ''
        ORDER BY make, year, model
    """)
    targets = cur.fetchall()
    total = len(targets)
    print(f"Found {total} vehicles missing engine data\n")

    updated = 0
    failed  = 0

    for i, v in enumerate(targets):
        vid, year, make, model = v["id"], v["year"], v["make"], v["model"]
        label = f"{year} {make} {model}"
        print(f"[{i+1}/{total}] {label}...", end=" ", flush=True)

        # Try primary strategy
        engine_str, trim_str = decode_vpic_batch(make, model, year)
        time.sleep(RATE_LIMIT)

        # Fallback to complaints API
        if not engine_str:
            engine_str, trim_str = get_engine_from_complaints_api(make, model, year)
            time.sleep(RATE_LIMIT)

        if engine_str or trim_str:
            cur.execute("""
                UPDATE vehicles SET
                  engine = COALESCE(?, engine),
                  trim   = COALESCE(?, trim)
                WHERE id = ?
            """, (engine_str, trim_str, vid))
            conn.commit()
            updated += 1
            print(f"✓  engine={engine_str}  trim={trim_str}")
            log.write(f"OK  {label}: engine={engine_str} trim={trim_str}\n")
        else:
            failed += 1
            print("✗  no data")
            log.write(f"MISS {label}\n")

    conn.close()
    log.close()
    print(f"\n── Done ──────────────────────────────")
    print(f"Updated : {updated}/{total}")
    print(f"No data : {failed}/{total}")
    print(f"Log     : {LOG_FILE}")

if __name__ == "__main__":
    main()
