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
    handlers=[logging.FileHandler("wrench_dtc_expanded.log", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

# Full OBD-II DTC range + manufacturer codes
def generate_codes():
    codes = []
    # P codes — Powertrain (most common)
    # P0000-P0999: Generic OBD-II
    for i in range(0, 1000):
        codes.append(f"P{i:04d}")
    # P1000-P1999: Manufacturer specific
    for i in range(1000, 2000):
        codes.append(f"P{i:04d}")
    # P2000-P2999: Generic (2nd generation)
    for i in range(2000, 3000):
        codes.append(f"P{i:04d}")
    # P3000-P3999: Generic/Manufacturer
    for i in range(3000, 4000):
        codes.append(f"P{i:04d}")
    # B codes — Body
    for i in range(0, 1000):
        codes.append(f"B{i:04d}")
    for i in range(1000, 2000):
        codes.append(f"B{i:04d}")
    # C codes — Chassis
    for i in range(0, 1000):
        codes.append(f"C{i:04d}")
    for i in range(1000, 2000):
        codes.append(f"C{i:04d}")
    # U codes — Network/Communication
    for i in range(0, 1000):
        codes.append(f"U{i:04d}")
    for i in range(1000, 2000):
        codes.append(f"U{i:04d}")
    return codes

session = requests.Session()
session.headers.update({"X-API-Key": API_KEY})
req_count = 0

def api_get(path):
    global req_count
    try:
        r = session.get(f"{BASE_URL}/{path}", timeout=15)
        req_count += 1
        time.sleep(DELAY)
        if r.status_code == 200: return r.json().get("data")
        if r.status_code == 429:
            log.warning("Rate limited - sleeping 15s")
            time.sleep(15)
            return api_get(path)
        return None
    except Exception as e:
        log.error(f"Request error: {e}")
        return None

def main():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dtc_codes (
            code TEXT PRIMARY KEY,
            description TEXT, urgency TEXT,
            cost_low INTEGER, cost_high INTEGER,
            possible_causes TEXT, systems TEXT
        )
    """)
    conn.commit()

    # Get already-pulled codes
    existing = set(r[0] for r in conn.execute("SELECT code FROM dtc_codes").fetchall())
    log.info(f"Already have: {len(existing)} codes")

    all_codes = generate_codes()
    to_pull = [c for c in all_codes if c not in existing]
    log.info(f"Codes to pull: {len(to_pull)}")

    saved = 0
    empty = 0
    for i, code in enumerate(to_pull, 1):
        data = api_get(f"diagnostics/{code}")
        if data and data.get("description"):
            conn.execute("INSERT OR REPLACE INTO dtc_codes VALUES (?,?,?,?,?,?,?)", (
                code,
                data.get("description"),
                data.get("urgency"),
                data.get("cost_low"),
                data.get("cost_high"),
                json.dumps(data.get("possible_causes") or []),
                json.dumps(data.get("systems") or [])
            ))
            conn.commit()
            saved += 1
            if saved % 50 == 0:
                log.info(f"  [{i}/{len(to_pull)}] Saved {saved} codes so far (last: {code})")
        else:
            empty += 1

    total = conn.execute("SELECT COUNT(*) FROM dtc_codes").fetchone()[0]
    log.info(f"DONE! Saved {saved} new codes. Total in DB: {total}. Empty: {empty}. Requests: {req_count}")
    conn.close()

if __name__ == "__main__":
    main()
