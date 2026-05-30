#!/usr/bin/env python3
"""
Wrench - Ingestion bug fix
==========================
Re-pulls recalls + TSBs from the Vehicle Finder API with CORRECTED field
mapping (the original batch scripts wrote the wrong API field names, leaving
campaign_number/summary and tsb.title 100% NULL), and nulls out the bogus
generic tire_size fallback on exotic makes.

Read-only against the API; writes only to wrench_vehicles.db.

Actual API field names (verified live, 2026-05-29):
  recalls item: id, nhtsa_campaign, description, consequence, remedy,
                date_issued, source        (NO "component", NO "park_it")
  tsb item    : id, tsb_number, description, category, date_issued, source
                (NO "component"; "category" is the closest; date is date_issued)

Mapping applied:
  RECALLS  nhtsa_campaign -> campaign_number
           description    -> summary
           remedy         -> remedy
           component      -> (no source field) left NULL
           park_it        = 1 if item.get("park_it") else 0   (existing logic)
  TSB      tsb_number     -> tsb_number
           description    -> title
           category       -> component   (best available; API has no component)
           date_issued    -> date        (API has no plain "date")
"""
import os, json, sqlite3, time, logging, threading
from concurrent.futures import ThreadPoolExecutor
import urllib.request, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(ROOT, "wrench_vehicles.db")
CFG = json.load(open(os.path.join(ROOT, "wrench_config.json")))
API_KEY = CFG["vehicle_finder_api_key"]
BASE = "https://api.vehicle-finder.com/v1"
EXOTIC_MAKES = ["Rolls-Royce", "McLaren", "Ferrari", "Lamborghini",
                "Bentley", "Aston Martin", "Maserati", "Porsche"]
WORKERS = 5

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(os.path.join(ROOT, "wrench_fix_ingestion.log"),
                                  encoding="utf-8"),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
_rl = threading.Lock()


def api_get(path, _tries=0):
    req = urllib.request.Request(f"{BASE}/{path}", headers={"X-API-Key": API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode()).get("data")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code == 429 and _tries < 5:
            with _rl:
                time.sleep(8)
            return api_get(path, _tries + 1)
        log.warning(f"HTTP {e.code} for {path}")
        return None
    except Exception as e:
        if _tries < 3:
            time.sleep(1)
            return api_get(path, _tries + 1)
        log.error(f"error {path}: {e}")
        return None


def fetch_all(vids, endpoint):
    """Return dict vid -> list-of-items (only vehicles with data)."""
    out = {}
    done = [0]
    t0 = time.time()
    def work(vid):
        d = api_get(f"vehicles/{vid}/{endpoint}")
        items = d if isinstance(d, list) else (d.get(endpoint) if isinstance(d, dict) else None)
        with _rl:
            done[0] += 1
            if done[0] % 200 == 0:
                rate = done[0] / (time.time() - t0) * 60
                log.info(f"  [{endpoint}] {done[0]}/{len(vids)} fetched | {rate:.0f}/min")
        return vid, (items or [])
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for vid, items in ex.map(work, vids):
            if items:
                out[vid] = items
    return out


def main():
    conn = sqlite3.connect(DB_FILE)
    vids = [r[0] for r in conn.execute("SELECT id FROM vehicles ORDER BY id")]
    log.info("=" * 64)
    log.info(f"INGESTION FIX START - {len(vids)} vehicles")

    # ---------- 1. RECALLS ----------
    log.info("Re-pulling RECALLS ...")
    rec = fetch_all(vids, "recalls")
    conn.execute("DELETE FROM recalls")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='recalls'")
    n_rec = 0
    for vid, items in rec.items():
        for it in items:
            conn.execute(
                "INSERT INTO recalls (vehicle_id,campaign_number,component,summary,remedy,park_it) "
                "VALUES (?,?,?,?,?,?)",
                (vid, it.get("nhtsa_campaign"), it.get("component"),
                 it.get("description"), it.get("remedy"),
                 1 if it.get("park_it") else 0))
            n_rec += 1
    conn.commit()
    log.info(f"RECALLS done: {len(rec)} vehicles, {n_rec} rows inserted")

    # ---------- 2. TSB ----------
    log.info("Re-pulling TSBs ...")
    tsb = fetch_all(vids, "tsb")
    conn.execute("DELETE FROM tsb")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='tsb'")
    n_tsb = 0
    for vid, items in tsb.items():
        for it in items:
            conn.execute(
                "INSERT INTO tsb (vehicle_id,tsb_number,title,component,summary,date) "
                "VALUES (?,?,?,?,?,?)",
                (vid, it.get("tsb_number"), it.get("description"),
                 it.get("category"), None, it.get("date_issued")))
            n_tsb += 1
    conn.commit()
    log.info(f"TSB done: {len(tsb)} vehicles, {n_tsb} rows inserted")

    # ---------- 3. tire_size NULL for exotics ----------
    ph = ",".join("?" * len(EXOTIC_MAKES))
    cur = conn.execute(
        f"UPDATE parts SET tire_size=NULL WHERE vehicle_id IN "
        f"(SELECT id FROM vehicles WHERE make IN ({ph}))", EXOTIC_MAKES)
    conn.commit()
    log.info(f"tire_size nulled for exotic makes: {cur.rowcount} parts rows updated")

    # ---------- verification ----------
    rc = conn.execute("SELECT COUNT(*),SUM(campaign_number IS NULL),SUM(summary IS NULL) FROM recalls").fetchone()
    tc = conn.execute("SELECT COUNT(*),SUM(title IS NULL) FROM tsb").fetchone()
    log.info(f"VERIFY recalls: rows={rc[0]} campaign_NULL={rc[1]} summary_NULL={rc[2]}")
    log.info(f"VERIFY tsb:     rows={tc[0]} title_NULL={tc[1]}")
    log.info("INGESTION FIX COMPLETE")
    log.info("=" * 64)
    conn.close()


if __name__ == "__main__":
    main()
