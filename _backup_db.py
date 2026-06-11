"""
_backup_db.py — Timestamped, consistent snapshot of the live vehicle database.

SAFE IMPORT RULES require a DB backup before every live write. Use this so that rule is
automated rather than relied on per-script.

CLI:    python _backup_db.py ["reason"]      # snapshot now, prune to KEEP most recent
Import: from _backup_db import backup_db; backup_db("v22 spec import")

Snapshots use SQLite's online-backup API (consistent even if the DB is mid-write), land in
db_backups/ (gitignored via *.db.* / *.bak), and are pruned to the KEEP most recent.
"""
import os, glob, datetime, sqlite3

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
BACKUP_DIR = os.path.join(ROOT, "db_backups")
KEEP = 7


def backup_db(reason=""):
    if not os.path.exists(DB):
        raise SystemExit("DB not found: " + DB)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, "wrench_vehicles.%s.db.bak" % ts)
    src = sqlite3.connect(DB)
    try:
        dst = sqlite3.connect(dest)
        try:
            with dst:
                src.backup(dst)          # consistent online snapshot
        finally:
            dst.close()
    finally:
        src.close()
    # prune to the KEEP most recent (timestamp names sort lexically = chronologically)
    for old in sorted(glob.glob(os.path.join(BACKUP_DIR, "wrench_vehicles.*.db.bak")))[:-KEEP]:
        os.remove(old)
    size = os.path.getsize(dest) / 1024 / 1024
    print("DB backup -> %s (%.1f MB)%s" % (os.path.relpath(dest, ROOT), size, ("  [" + reason + "]") if reason else ""))
    return dest


if __name__ == "__main__":
    import sys
    backup_db(" ".join(sys.argv[1:]))
