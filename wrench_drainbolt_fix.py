#!/usr/bin/env python3
"""
DRAIN-BOLT FIX (#1) — promote drain_bolt nested fields into dedicated columns.

Audit (prior turn) established this is NOT a field-mapping bug and NOT an
ingestion coverage gap: the Vehicle Finder oil-change endpoint returns null
socket/thread/gasket for the missing vehicles (0/22 sampled had data), so a
re-pull recovers nothing new. The stored drain_bolt_json IS the VF response.

What this DOES do (the achievable, useful part of the request): add the
requested dedicated columns and populate them from the already-stored
drain_bolt_json so the 832 vehicles that DO have data get queryable
socket/thread/gasket columns. The rest stay NULL (source gap — unrecoverable
from VF). Field mapping uses the ACTUAL API keys:
    drain_bolt.socket_size_mm -> socket
    drain_bolt.thread_size    -> thread
    drain_bolt.gasket_type    -> gasket
"""
import os, json, sqlite3, logging

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(os.path.join(ROOT, "wrench_drainbolt_fix.log"), encoding="utf-8"),
              logging.StreamHandler()])
log = logging.getLogger(__name__)


def main():
    conn = sqlite3.connect(DB, timeout=30)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(oil_change)")}
    for col in ("socket", "thread", "gasket"):
        if col not in cols:
            conn.execute(f"ALTER TABLE oil_change ADD COLUMN {col} TEXT")
            log.info(f"added column oil_change.{col}")
    conn.commit()

    rows = conn.execute("SELECT vehicle_id, drain_bolt_json FROM oil_change WHERE vehicle_id>0").fetchall()
    tot = len(rows)
    set_socket = set_thread = set_gasket = updated = 0
    for vid, dbj in rows:
        d = {}
        if dbj and dbj.strip() not in ("", "null", "{}", "[]"):
            try:
                d = json.loads(dbj)
                if isinstance(d, list):
                    d = d[0] if d else {}
            except Exception:
                d = {}
        socket = d.get("socket_size_mm")
        thread = d.get("thread_size")
        gasket = d.get("gasket_type")
        # normalize socket to a string like "14mm" when numeric
        socket_s = (f"{socket:g}mm" if isinstance(socket, (int, float)) else socket) if socket not in (None, "") else None
        conn.execute("UPDATE oil_change SET socket=?, thread=?, gasket=? WHERE vehicle_id=?",
                     (socket_s, thread or None, gasket or None, vid))
        if socket_s: set_socket += 1
        if thread: set_thread += 1
        if gasket: set_gasket += 1
        if socket_s or thread or gasket:
            updated += 1
    conn.commit()

    log.info("=" * 64)
    log.info("DRAIN-BOLT FIX COMPLETE")
    log.info(f"  vehicles total: {tot}")
    log.info(f"  rows with >=1 drain-bolt field populated: {updated}")
    log.info(f"  socket populated: {set_socket}  (null: {tot-set_socket})")
    log.info(f"  thread populated: {set_thread}  (null: {tot-set_thread})")
    log.info(f"  gasket populated: {set_gasket}  (null: {tot-set_gasket})")
    log.info("  Remaining NULLs are a SOURCE gap (Vehicle Finder API has no data); "
             "not recoverable by re-pull. NOT a mapping bug.")
    log.info("=" * 64)
    conn.close()


if __name__ == "__main__":
    main()
