import os
import requests, sqlite3, json, time, sys, io, logging
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_KEY  = os.environ.get("VEHICLE_FINDER_KEY", "")
BASE_URL = "https://api.vehicle-finder.com/v1"
DB_FILE  = "wrench_vehicles.db"
DELAY    = 0.25

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler("wrench_regional.log", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

# Regions available in Vehicle Finder API
REGIONS = ["northeast","southeast","midwest","southwest","west","national"]

session = requests.Session()
session.headers.update({"X-API-Key": API_KEY})
req_count = 0

def api_get(path, params=None):
    global req_count
    try:
        r = session.get(f"{BASE_URL}/{path}", params=params, timeout=15)
        req_count += 1
        time.sleep(DELAY)
        if r.status_code == 200: return r.json().get("data")
        if r.status_code == 429:
            log.warning("Rate limited - sleeping 15s")
            time.sleep(15)
            return api_get(path, params)
        return None
    except Exception as e:
        log.error(f"Request error: {e}")
        return None

def main():
    conn = sqlite3.connect(DB_FILE)

    # Only pull regional costs for vehicles that only have national
    vehicles = conn.execute("""
        SELECT DISTINCT v.id, v.year, v.make, v.model
        FROM vehicles v
        WHERE v.id IN (SELECT vehicle_id FROM service_costs WHERE region='national')
        AND v.id NOT IN (SELECT vehicle_id FROM service_costs WHERE region='northeast')
        ORDER BY v.year DESC, v.make, v.model
    """).fetchall()

    log.info(f"Pulling regional costs for {len(vehicles)} vehicles x {len(REGIONS)-1} regions")
    saved = 0

    for i, (vid, year, make, model) in enumerate(vehicles, 1):
        log.info(f"[{i}/{len(vehicles)}] {year} {make} {model}")
        for region in REGIONS:
            if region == "national": continue  # already have this
            data = api_get(f"vehicles/{vid}/service-costs", {"region": region})
            if data:
                for s in (data if isinstance(data, list) else []):
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO service_costs
                            (vehicle_id,service_type,region,cost_low,cost_high,
                             cost_average,labor_hours_low,labor_hours_high)
                            VALUES (?,?,?,?,?,?,?,?)
                        """, (vid, s.get("service_type"), region,
                              s.get("cost_low"), s.get("cost_high"),
                              s.get("cost_average"), s.get("labor_hours_low"),
                              s.get("labor_hours_high")))
                        saved += 1
                    except: pass
            conn.commit()

        if i % 20 == 0:
            total = conn.execute("SELECT COUNT(*) FROM service_costs").fetchone()[0]
            log.info(f"--- {i}/{len(vehicles)} done | {req_count} reqs | {total:,} cost records ---")

    total = conn.execute("SELECT COUNT(*) FROM service_costs").fetchone()[0]
    log.info(f"DONE! Saved {saved} regional records. Total service_costs: {total:,}. Requests: {req_count}")
    conn.close()

if __name__ == "__main__":
    main()
