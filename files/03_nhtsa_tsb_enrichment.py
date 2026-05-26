"""
WRENCH — Script 03: NHTSA TSB Title + Summary Enrichment
=========================================================
You already have 186,032 TSB numbers in the tsb table but they have
NULL titles, components, summaries, and dates. This script fills them in
using the NHTSA complaints/TSB API.

API: https://api.nhtsa.gov/tsbs/searchTsbsByVehicle (free, no key)
Also queries: https://api.nhtsa.gov/complaints/complaintsByVehicle
              (for complaints enrichment — bonus pass at end)

Strategy:
  - Group TSB rows by vehicle_id → look up each vehicle's make/model/year
  - Hit NHTSA TSB search → match tsb_number → fill title/component/summary/date
  - Deduplicate: many vehicles share TSBs; cache API results by make/model/year
  - Bonus pass: pull complaint text into a new `complaints` table

Run: python3 03_nhtsa_tsb_enrichment.py
Estimated time: ~4-6 hours (834 vehicles, throttled to avoid rate limits)
Resume-safe: already-filled rows are skipped.
"""

import sqlite3
import requests
import time
import json
from collections import defaultdict

DB_PATH    = "wrench_vehicles.db"
RATE_LIMIT = 0.3          # NHTSA allows ~3-4 req/sec
LOG_FILE   = "tsb_enrichment.log"
CACHE_FILE = "tsb_api_cache.json"  # persist API responses to disk

NHTSA_BASE = "https://api.nhtsa.gov"


# ── API helpers ──────────────────────────────────────────────────────────────

def nhtsa_get(path, params=None):
    try:
        r = requests.get(f"{NHTSA_BASE}/{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def fetch_tsbs_for_vehicle(make, model, year):
    """
    Returns list of TSB dicts from NHTSA for a given vehicle.
    Each dict has: nhtsa_id, subject, summary, component, date, tsb_number
    """
    data = nhtsa_get("tsbs/searchTsbsByVehicle", params={
        "make": make, "model": model, "modelYear": year
    })
    if not data:
        return []
    results = data.get("results", [])
    if isinstance(results, dict):
        results = [results]
    return results


def fetch_complaints_for_vehicle(make, model, year):
    """
    Returns list of complaint dicts for a given vehicle.
    Each dict: complaintNumber, component, summary, dateOfIncident, crash, fire
    """
    data = nhtsa_get("complaints/complaintsByVehicle", params={
        "make": make, "model": model, "modelYear": year
    })
    if not data:
        return []
    results = data.get("results", [])
    if isinstance(results, dict):
        results = [results]
    return results


# ── DB helpers ───────────────────────────────────────────────────────────────

def ensure_complaints_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id      INTEGER NOT NULL,
            complaint_number TEXT,
            component       TEXT,
            summary         TEXT,
            incident_date   TEXT,
            crash           INTEGER DEFAULT 0,
            fire            INTEGER DEFAULT 0,
            injury          INTEGER DEFAULT 0,
            deaths          INTEGER DEFAULT 0
        )
    """)
    # Index for fast lookup
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_complaints_vehicle
        ON complaints(vehicle_id)
    """)


def already_enriched(cur, vehicle_id):
    """Return True if this vehicle's TSBs already have titles filled in."""
    cur.execute("""
        SELECT COUNT(*) FROM tsb
        WHERE vehicle_id = ? AND title IS NOT NULL
    """, (vehicle_id,))
    return cur.fetchone()[0] > 0


def get_tsb_numbers_for_vehicle(cur, vehicle_id):
    """Return list of (tsb_row_id, tsb_number) for a vehicle."""
    cur.execute("""
        SELECT id, tsb_number FROM tsb
        WHERE vehicle_id = ? AND tsb_number IS NOT NULL
          AND (title IS NULL OR title = '')
    """, (vehicle_id,))
    return cur.fetchall()


def update_tsb_row(cur, row_id, title, component, summary, date):
    cur.execute("""
        UPDATE tsb SET
            title     = COALESCE(?, title),
            component = COALESCE(?, component),
            summary   = COALESCE(?, summary),
            date      = COALESCE(?, date)
        WHERE id = ?
    """, (title, component, summary, date, row_id))


def insert_complaint(cur, vehicle_id, c):
    # Avoid duplicates
    cur.execute("""
        SELECT id FROM complaints
        WHERE vehicle_id=? AND complaint_number=?
    """, (vehicle_id, c.get("complaintNumber")))
    if cur.fetchone():
        return False
    cur.execute("""
        INSERT INTO complaints
          (vehicle_id, complaint_number, component, summary,
           incident_date, crash, fire, injury, deaths)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        vehicle_id,
        c.get("complaintNumber"),
        c.get("components"),
        c.get("summary"),
        c.get("dateOfIncident"),
        1 if c.get("crash") else 0,
        1 if c.get("fire")  else 0,
        int(c.get("numberOfInjuries", 0) or 0),
        int(c.get("numberOfDeaths",   0) or 0),
    ))
    return True


# ── Cache ────────────────────────────────────────────────────────────────────

def load_cache():
    import os
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def cache_key(make, model, year):
    return f"{year}|{make}|{model}".upper()


# ── TSB matcher ──────────────────────────────────────────────────────────────

def match_tsb(api_tsbs, tsb_number):
    """
    Given NHTSA API TSB results, find the one matching our tsb_number.
    NHTSA sometimes formats numbers differently (dashes, spaces, case).
    """
    def normalize(s):
        return s.upper().replace("-","").replace(" ","").replace("_","")

    target = normalize(tsb_number)
    for t in api_tsbs:
        nhtsa_num = t.get("serviceIdentifier") or t.get("tsbNumber") or ""
        if normalize(nhtsa_num) == target:
            return t
    # Fuzzy: partial match
    for t in api_tsbs:
        nhtsa_num = t.get("serviceIdentifier") or t.get("tsbNumber") or ""
        if normalize(nhtsa_num) in target or target in normalize(nhtsa_num):
            return t
    return None


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    log  = open(LOG_FILE, "w")

    ensure_complaints_table(cur)
    conn.commit()

    cache = load_cache()

    # Get all vehicles that have TSB rows
    cur.execute("""
        SELECT DISTINCT v.id, v.year, v.make, v.model
        FROM vehicles v
        JOIN tsb t ON t.vehicle_id = v.id
        ORDER BY v.make, v.year, v.model
    """)
    vehicles = cur.fetchall()
    total = len(vehicles)
    print(f"Vehicles with TSBs: {total}\n")

    tsb_filled       = 0
    tsb_no_match     = 0
    complaints_added = 0
    api_calls        = 0

    for i, v in enumerate(vehicles):
        vid, year, make, model = v["id"], v["year"], v["make"], v["model"]
        label = f"{year} {make} {model}"

        # ── TSB enrichment ──
        tsb_rows = get_tsb_numbers_for_vehicle(cur, vid)
        if not tsb_rows:
            print(f"[{i+1}/{total}] {label} — already enriched, skipping TSBs")
        else:
            print(f"[{i+1}/{total}] {label} — {len(tsb_rows)} TSBs to fill...", end=" ", flush=True)
            ck = cache_key(make, model, year)
            if ck in cache:
                api_tsbs = cache[ck]
            else:
                api_tsbs = fetch_tsbs_for_vehicle(make, model, year)
                cache[ck] = api_tsbs
                api_calls += 1
                time.sleep(RATE_LIMIT)

            matched = 0
            for row_id, tsb_num in tsb_rows:
                hit = match_tsb(api_tsbs, tsb_num)
                if hit:
                    update_tsb_row(
                        cur, row_id,
                        title     = hit.get("subject") or hit.get("tsbTitle"),
                        component = hit.get("affectedProducts") or hit.get("component"),
                        summary   = hit.get("description") or hit.get("summary"),
                        date      = hit.get("dateIssued") or hit.get("issueDate"),
                    )
                    matched += 1
                    tsb_filled += 1
                else:
                    tsb_no_match += 1

            conn.commit()
            print(f"matched {matched}/{len(tsb_rows)}")
            log.write(f"TSB {label}: {matched}/{len(tsb_rows)} matched\n")

        # ── Complaints enrichment (bonus pass) ──
        comp_key = f"COMP|{cache_key(make, model, year)}"
        if comp_key not in cache:
            complaints = fetch_complaints_for_vehicle(make, model, year)
            cache[comp_key] = complaints
            api_calls += 1
            time.sleep(RATE_LIMIT)
        else:
            complaints = cache[comp_key]

        for c in complaints:
            if insert_complaint(cur, vid, c):
                complaints_added += 1
        conn.commit()

        # Save cache every 50 vehicles
        if i % 50 == 0:
            save_cache(cache)

    save_cache(cache)
    conn.close()
    log.close()

    print(f"\n── Done ────────────────────────────────────────")
    print(f"TSBs filled        : {tsb_filled}")
    print(f"TSBs no match      : {tsb_no_match}")
    print(f"Complaints added   : {complaints_added}")
    print(f"API calls made     : {api_calls} (rest from cache)")
    print(f"Log                : {LOG_FILE}")
    print(f"Cache              : {CACHE_FILE}")


if __name__ == "__main__":
    main()
