"""
WRENCH — Script 03 (rewrite): NHTSA Complaints Enrichment
=========================================================
The original 03 tried to fill 207,065 TSB titles via
api.nhtsa.gov/tsbs/searchTsbsByVehicle.  That endpoint does NOT exist:
every TSB path returns 403 "Missing Authentication Token" (the AWS API
Gateway response for an unknown route).  NHTSA exposes recalls, complaints,
and safetyRatings — but no per-vehicle TSB JSON API.  TSB titles are
therefore left untouched by this script.

This salvages the half that works: NHTSA's complaints API
(api.nhtsa.gov/complaints/complaintsByVehicle) returns real complaint
records per vehicle.  We populate a `complaints` table from it.

Fixes vs the original draft:
  * field is `odiNumber`, not `complaintNumber`  (the original stored NULL)
  * idempotent: UNIQUE(vehicle_id, complaint_number) + INSERT OR IGNORE,
    so re-runs never duplicate
  * crash/fire normalized (bool or "Yes"/"No") to 0/1
  * responses cached to disk -> resume-safe, no repeat API calls

Run: python 03_complaints_enrichment.py
"""

import sqlite3
import requests
import time
import json
import os

DB_PATH    = r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\wrench_vehicles.db"
LOG_FILE   = r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\complaints_enrichment.log"
CACHE_FILE = r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\complaints_api_cache.json"
NHTSA_BASE = "https://api.nhtsa.gov"
RATE_LIMIT = 0.5
COMMIT_EVERY = 25

session = requests.Session()


# ── API ────────────────────────────────────────────────────────────────────

def fetch_complaints(make, model, year):
    """All complaint records for a vehicle, or [] on failure."""
    for attempt in range(4):
        try:
            r = session.get(f"{NHTSA_BASE}/complaints/complaintsByVehicle",
                            params={"make": make, "model": model, "modelYear": year},
                            timeout=60)
            # NHTSA returns HTTP 400 with a valid {"count":0,"results":[]} body for
            # make/model/year combos not in its catalog -> that's "no complaints",
            # not a transient error. Accept any well-formed JSON body.
            try:
                data = r.json()
            except Exception:
                data = None
            if isinstance(data, dict) and ("results" in data or "count" in data):
                res = data.get("results") or []
                return [res] if isinstance(res, dict) else res
            r.raise_for_status()            # 5xx / unparseable -> retry
        except Exception:
            time.sleep(0.6 * (attempt + 1))
    return None        # None = real API failure (don't cache); [] = genuinely no complaints


def truthy(v):
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        return 1 if v else 0
    if isinstance(v, str):
        return 1 if v.strip().lower() in ("yes", "y", "true", "1") else 0
    return 0


def safe_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


# ── DB ───────────────────────────────────────────────────────────────────────

def ensure_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id       INTEGER NOT NULL,
            complaint_number TEXT,
            component        TEXT,
            summary          TEXT,
            incident_date    TEXT,
            crash            INTEGER DEFAULT 0,
            fire             INTEGER DEFAULT 0,
            injury           INTEGER DEFAULT 0,
            deaths           INTEGER DEFAULT 0,
            UNIQUE(vehicle_id, complaint_number)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_vehicle ON complaints(vehicle_id)")


def insert_complaints(cur, vehicle_id, complaints):
    """INSERT OR IGNORE each complaint; returns number of new rows."""
    rows = [(
        vehicle_id,
        str(c["odiNumber"]) if c.get("odiNumber") is not None else None,
        c.get("components"),
        c.get("summary"),
        c.get("dateOfIncident"),
        truthy(c.get("crash")),
        truthy(c.get("fire")),
        safe_int(c.get("numberOfInjuries")),
        safe_int(c.get("numberOfDeaths")),
    ) for c in complaints]
    cur.executemany("""
        INSERT OR IGNORE INTO complaints
          (vehicle_id, complaint_number, component, summary, incident_date,
           crash, fire, injury, deaths)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, rows)
    return cur.rowcount


# ── Cache ──────────────────────────────────────────────────────────────────

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache):
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    os.replace(tmp, CACHE_FILE)


def key(make, model, year):
    return f"{year}|{make}|{model}".upper()


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    log = open(LOG_FILE, "w", encoding="utf-8")

    ensure_table(cur)
    conn.commit()
    cache = load_cache()

    cur.execute("SELECT id, year, make, model FROM vehicles ORDER BY make, year, model")
    vehicles = cur.fetchall()
    total = len(vehicles)
    print(f"Vehicles to enrich with complaints: {total}\n")

    added = api_calls = failures = 0
    for i, v in enumerate(vehicles, 1):
        vid, year, make, model = v["id"], v["year"], v["make"], v["model"]
        label = f"{year} {make} {model}"
        ck = key(make, model, year)

        if ck in cache:
            complaints = cache[ck]
        else:
            complaints = fetch_complaints(make, model, year)
            if complaints is None:                 # API failed -> don't cache, count, move on
                failures += 1
                print(f"[{i}/{total}] {label}  ->  API error")
                log.write(f"ERR  {label}\n")
                continue
            cache[ck] = complaints
            api_calls += 1
            time.sleep(RATE_LIMIT)

        new = insert_complaints(cur, vid, complaints) if complaints else 0
        added += new
        print(f"[{i}/{total}] {label}  ->  {len(complaints)} complaints, {new} new")
        log.write(f"OK   {label}: {len(complaints)} fetched, {new} new\n")

        if i % COMMIT_EVERY == 0:
            conn.commit()
            save_cache(cache)

    conn.commit()
    save_cache(cache)

    cur.execute("SELECT count(*) FROM complaints")
    grand = cur.fetchone()[0]
    conn.close()
    log.close()

    print("\n--- Done ---------------------------")
    print(f"New complaint rows : {added}")
    print(f"Total in table     : {grand}")
    print(f"API calls (live)   : {api_calls}")
    print(f"API failures       : {failures}")
    print(f"Log                : {LOG_FILE}")


if __name__ == "__main__":
    main()
