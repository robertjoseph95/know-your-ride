#!/usr/bin/env python3
"""
Wrench — Maintenance Backfill
=============================
Repopulates the `maintenance` table (which came back empty due to a
response-shape bug) and the new `maintenance_parts` table, by re-pulling
ONLY the /vehicles/{id}/maintenance endpoint for every vehicle already
in the database.

The API returns:
    data = { "schedules": [ { id, mileage_interval, months_interval,
                              description, source, parts:[...] }, ... ] }

Safe to re-run: each vehicle's rows are deleted and re-inserted.
"""
import os
import requests, sqlite3, sys, io, time, logging

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

API_KEY  = os.environ.get("VEHICLE_FINDER_KEY", "")
BASE_URL = "https://api.vehicle-finder.com/v1"
DB_FILE  = r"C:\Users\Robert\Downloads\wrench_vehicles.db"
DELAY    = 0.25

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(r"C:\Users\Robert\Downloads\wrench_backfill_maintenance.log",
                                  encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({"X-API-Key": API_KEY})


def api_get(path):
    try:
        r = session.get(f"{BASE_URL}/{path}", timeout=20)
        time.sleep(DELAY)
        if r.status_code == 200:
            return r.json().get("data"), "ok"
        if r.status_code == 429:
            log.warning("Rate limited - sleeping 15s")
            time.sleep(15)
            return api_get(path)
        if r.status_code == 404:
            return None, "empty"
        log.error(f"HTTP {r.status_code} for {path}: {r.text[:80]}")
        return None, f"http_{r.status_code}"
    except Exception as e:
        log.error(f"Request error for {path}: {e}")
        return None, "error"


def migrate_schema(conn):
    """Rebuild maintenance + maintenance_parts to batch5's canonical schema,
    then repopulate from scratch. Destructive by design: the prior contents are
    backed up externally (wrench_vehicles.db.bak2) and re-pulled below."""
    conn.executescript("""
        DROP TABLE IF EXISTS maintenance;
        DROP TABLE IF EXISTS maintenance_parts;
        CREATE TABLE maintenance (
            id INTEGER PRIMARY KEY, vehicle_id INTEGER,
            mileage_interval INTEGER, months_interval INTEGER,
            description TEXT, source TEXT, notes TEXT
        );
        CREATE TABLE maintenance_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maintenance_id INTEGER, vehicle_id INTEGER,
            part_type TEXT, brand TEXT, part_number TEXT,
            description TEXT, qty INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_maint_vehicle ON maintenance(vehicle_id);
        CREATE INDEX IF NOT EXISTS idx_mp_maint ON maintenance_parts(maintenance_id);
        CREATE INDEX IF NOT EXISTS idx_mp_vehicle ON maintenance_parts(vehicle_id);
    """)
    conn.commit()
    log.info("Schema rebuilt to batch5 canonical schema (maintenance + maintenance_parts).")


def save_maintenance(conn, vid, data):
    schedules = data.get("schedules", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    # clean slate for this vehicle so re-runs don't leave stale rows
    conn.execute("DELETE FROM maintenance_parts WHERE vehicle_id=?", (vid,))
    conn.execute("DELETE FROM maintenance WHERE vehicle_id=?", (vid,))
    n_sched, n_parts = 0, 0
    for item in schedules:
        sid = item.get("id")
        conn.execute(
            "INSERT OR REPLACE INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes) VALUES (?,?,?,?,?,?,?)",
            (sid, vid, item.get("mileage_interval"), item.get("months_interval"),
             item.get("description"), item.get("source"), item.get("notes")))
        n_sched += 1
        for p in (item.get("parts") or []):
            conn.execute(
                "INSERT INTO maintenance_parts (maintenance_id,vehicle_id,part_type,brand,part_number,description,qty) VALUES (?,?,?,?,?,?,?)",
                (sid, vid, p.get("part_type"), p.get("brand"), p.get("part_number"),
                 p.get("description"), p.get("qty")))
            n_parts += 1
    return n_sched, n_parts


def main():
    conn = sqlite3.connect(DB_FILE)
    migrate_schema(conn)

    vids = [r[0] for r in conn.execute("SELECT id FROM vehicles ORDER BY id").fetchall()]
    log.info(f"Backfilling maintenance for {len(vids)} vehicles...")

    ok = empty = failed = 0
    total_sched = total_parts = 0
    t0 = time.time()

    for i, vid in enumerate(vids, 1):
        data, status = api_get(f"vehicles/{vid}/maintenance")
        if data is not None:
            s, p = save_maintenance(conn, vid, data)
            conn.execute("INSERT OR REPLACE INTO pull_log VALUES (?,?,?,datetime('now'))",
                         (vid, "maintenance", "ok"))
            conn.commit()
            total_sched += s; total_parts += p; ok += 1
        else:
            conn.execute("INSERT OR REPLACE INTO pull_log VALUES (?,?,?,datetime('now'))",
                         (vid, "maintenance", status))
            conn.commit()
            if status == "empty": empty += 1
            else: failed += 1

        if i % 50 == 0:
            rate = i / (time.time() - t0) * 60
            log.info(f"  [{i}/{len(vids)}] ok={ok} empty={empty} fail={failed} | "
                     f"{total_sched} schedules, {total_parts} parts | {rate:.0f}/min")

    elapsed = (time.time() - t0) / 60
    log.info("=" * 60)
    log.info("BACKFILL COMPLETE")
    log.info(f"  Vehicles:  {len(vids)}  (ok={ok}, empty={empty}, failed={failed})")
    log.info(f"  Schedules inserted: {total_sched:,}")
    log.info(f"  Parts inserted:     {total_parts:,}")
    log.info(f"  Time: {elapsed:.1f} min")
    log.info("=" * 60)
    conn.close()


if __name__ == "__main__":
    main()
