"""
Data Integrity Fix — Step 1: add a `source` provenance column to the curated-spec
tables that lack one, and backfill it.

Tables: oil_change, parts, fluids, torque_specs, engine_specs
(maintenance already has `source`).

Backfill rule:
- The 13 Mazda 3 vehicles (ids 38705-38717): source = 'owner-manual-verified'.
- All other vehicles: their INFERRED current source = the vehicle's dominant
  `maintenance.source` (ai-haiku-4.5 / scraped / engine_classifier_v1). Vehicles
  with no maintenance row -> 'unknown'.

Idempotent: ADD COLUMN guarded by a column-exists check; backfill re-applies the
same deterministic values. DB backed up first.
"""
import sqlite3, os, shutil, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
TABLES = ["oil_change", "parts", "fluids", "torque_specs", "engine_specs"]
MAZDA3 = set(range(38705, 38718))


def has_col(c, table, col):
    return any(r[1] == col for r in c.execute(f"PRAGMA table_info({table})"))


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = DB + ".bak-srcmigrate-" + ts
    shutil.copy2(DB, bak)
    print("Backup:", os.path.basename(bak))
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; c = con.cursor()

    # 1) add columns
    for t in TABLES:
        if not has_col(c, t, "source"):
            c.execute(f"ALTER TABLE {t} ADD COLUMN source TEXT")
            print(f"  + added {t}.source")
        else:
            print(f"  = {t}.source already exists")

    # 2) vehicle -> dominant maintenance source
    vmap = {}
    for r in c.execute("""SELECT vehicle_id, source, COUNT(*) n FROM maintenance
                          GROUP BY vehicle_id, source"""):
        cur = vmap.get(r["vehicle_id"])
        if cur is None or r["n"] > cur[1]:
            vmap[r["vehicle_id"]] = (r["source"], r["n"])
    vsrc = {vid: s for vid, (s, n) in vmap.items()}

    def src_for(vid):
        if vid in MAZDA3:
            return "owner-manual-verified"
        return vsrc.get(vid) or "unknown"

    # 3) backfill each table
    for t in TABLES:
        vids = [r[0] for r in c.execute(f"SELECT DISTINCT vehicle_id FROM {t}")]
        for vid in vids:
            c.execute(f"UPDATE {t} SET source=? WHERE vehicle_id=?", (src_for(vid), vid))
        con.commit()
        # report distribution
        dist = {}
        for r in c.execute(f"SELECT COALESCE(source,'(null)') s, COUNT(*) n FROM {t} GROUP BY s"):
            dist[r["s"]] = r["n"]
        print(f"  {t}: " + ", ".join(f"{k}={v}" for k, v in sorted(dist.items(), key=lambda x: -x[1])))

    con.close()
    print("\nDONE — source columns added + backfilled.")


if __name__ == "__main__":
    main()
