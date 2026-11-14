# Hyundai Kona 2022 (id 3694) and Elantra 2022 (id 3691) - restore intervals that were left out as "print conflicts".
#
# Background: these two rows were written from their TITLED US-portal books and compared with the second-host books
# labelled OS/2022 and CN7/2022. Where the two disagreed the item was left out as an edition conflict. The 2026-11-14
# label audit showed that both labels hold the 2023 model year's book, so the disagreements were model-year changes and
# the titled 2022 books' own figures are the 2022 figures. This script restores them. Run it AFTER
# _fix_hyundai_label_audit_2026_11_14.py (it expects that script's source wording).
#
# Re-read 2026-11-14 from upright page renders (ruling "Go, write"):
#   Kona 2022    kona_2022_OSPE_portal_OM.pdf, PDF title '2022 Kona Owner's Manual', Copyright 2021
#       p.9-8  spark plugs, Smartstream G1.6 T-GDi: every 47,000 mi            (row was missing)
#       p.9-8  cabin air filter: every 16,000 mi or 12 months                  (months were missing)
#       p.9-9  coolant: first at 120,000 mi / 120 months, thereafter every 30,000 mi / 24 months
#       p.2-13 / 2-14  the book prints "Rear differential oil (4WD)" and "Transfer case oil (4WD)"; the row said AWD,
#              which is the 2023 book's wording (standing ruling: drivetrain wording as printed per year)
#   Elantra 2022 elantra_2022_portal_OM.pdf (portal folder 2022; untitled, Copyright 2020, page stamps 2020-12-03)
#       p.9-8  spark plugs, Smartstream G1.6 T-GDi: every 47,000 mi            (row was missing)
#       p.9-9  coolant: thereafter every 30,000 mi / 24 months
#   Unchanged on Elantra 2022: tire rotation 8,000 mi with no months (the book prints none); the oil requirement
#   (the book asks for API SN PLUS or above, not full synthetic).
#
# The maintenance set of each row is rewritten in schedule order (7 -> 8 rows). Nothing else changes except the two
# Kona location labels and the source notes. The frozen bare wheel-nut row on 3691 is not touched; the bare count is
# checked BEFORE commit. Idempotent.
#
# Usage:  python _fix_hyundai_restore_2022_intervals.py            -> DRY RUN
#         python _fix_hyundai_restore_2022_intervals.py --write    -> backup DB, apply, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
SRC_TABLES = ("oil_change", "fluids", "parts", "torque_specs")
COOLANT = "Engine coolant first replacement; thereafter every 30,000 mi / 24 months"

TARGETS = [
 dict(vid=3694, want=(2022, "Hyundai", "Kona"), msrc="Hyundai Owner's Manual (Kona 2022 OS facelift, p.%s)",
      before=[(8000, 12, "Engine oil & filter change"), (96000, None, "Spark plug replacement (Smartstream G2.0 Atkinson)"),
              (24000, 36, "Engine air cleaner filter replacement"), (16000, None, "Cabin air filter replacement"),
              (8000, None, "Tire rotation"), (120000, 120, "Engine coolant first replacement"), (48000, 48, "Brake fluid replacement")],
      maint=[(8000, 12, "Engine oil & filter change", "9-8"),
             (96000, None, "Spark plug replacement (Smartstream G2.0 Atkinson)", "9-8"),
             (47000, None, "Spark plug replacement (Smartstream G1.6 T-GDi)", "9-8"),
             (24000, 36, "Engine air cleaner filter replacement", "9-8"),
             (16000, 12, "Cabin air filter replacement", "9-8"),
             (8000, None, "Tire rotation", "9-8"),
             (120000, 120, COOLANT, "9-9"),
             (48000, 48, "Brake fluid replacement", "9-10")],
      relabel=("(AWD)", "(4WD)"),
      subs=[("its differences from this book are model-year changes; gated to null:",
             "its differences from this book are model-year changes; restored 2026-11-14 from this titled book: G1.6 T-GDi "
             "spark plugs every 47,000 mi, cabin air filter 12 months, coolant every 30,000 mi / 24 months after the first "
             "replacement (p.9-8 / 9-9, read from page renders), and the 4WD wording this book prints for the rear "
             "differential and transfer case (p.2-13 / 2-14); gated to null:")]),
 dict(vid=3691, want=(2022, "Hyundai", "Elantra"), msrc="Hyundai Owner's Manual (Elantra 2022 CN7, p.%s)",
      before=[(8000, 12, "Engine oil & filter change"), (96000, None, "Spark plug replacement (Smartstream G2.0)"),
              (24000, 36, "Engine air cleaner filter replacement"), (16000, 24, "Cabin air filter replacement"),
              (8000, None, "Tire rotation"), (120000, 120, "Engine coolant first replacement"), (48000, 48, "Brake fluid replacement")],
      maint=[(8000, 12, "Engine oil & filter change", "9-8"),
             (96000, None, "Spark plug replacement (Smartstream G2.0)", "9-8"),
             (47000, None, "Spark plug replacement (Smartstream G1.6 T-GDi)", "9-8"),
             (24000, 36, "Engine air cleaner filter replacement", "9-8"),
             (16000, 24, "Cabin air filter replacement", "9-8"),
             (8000, None, "Tire rotation", "9-8"),
             (120000, 120, COOLANT, "9-9"),
             (48000, 48, "Brake fluid replacement", "9-10")],
      relabel=None,
      subs=[("three schedule items differ between this book and the CN7 2022 book and were left out; label audit",
             "three schedule items differ between this book and the CN7 2022 book; label audit"),
            ("so those differences are model-year changes, not print conflicts;",
             "so those differences are model-year changes, not print conflicts; this book's own figures were restored "
             "2026-11-14 (G1.6 T-GDi spark plugs every 47,000 mi, coolant every 30,000 mi / 24 months after the first "
             "replacement; p.9-8 / 9-9, read from page renders);"),
            ("gated to null: G1.6 T-GDi spark-plug interval (this book 47,000 mi, the CN7 2022 book 48,000 mi), coolant "
             "interval after the first replacement (30,000 mi in this book and CN7a, 24,000 mi in CN7), tire-rotation months "
             "(none in this book, 12 in the second-host books), full-synthetic requirement (second-host book only), ",
             "gated to null: tire-rotation months (this book prints none), full-synthetic requirement (this book asks for "
             "API SN PLUS or above only), ")]),
]

def bare_count(c):
    return c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                     "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source=?", (BARE,)).fetchone()[0]

def maint_now(c, vid):
    return c.execute("SELECT mileage_interval, months_interval, description, source, notes, difficulty_level, tool_required, "
                     "time_minutes FROM maintenance WHERE vehicle_id=? ORDER BY id", (vid,)).fetchall()

def run(c, apply):
    """Validate against the current DB; print each change; execute when apply is True. Returns the change count."""
    n = 0
    for t in TARGETS:
        vid = t["vid"]
        have = c.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        assert have == t["want"], (vid, "target row is not the expected vehicle", have)
        # --- maintenance set
        target = [(mi, mo, d, t["msrc"] % pg, "standard", None, None, None) for mi, mo, d, pg in t["maint"]]
        for mi, mo, d, src, *_ in target:
            assert classify(src, "maintenance", vid) == 1 and not JARGON.search(d), (vid, d)
        cur = maint_now(c, vid)
        if cur != target:
            assert sorted((r[0], r[1] or 0, r[2]) for r in cur) == sorted((a, b or 0, d) for a, b, d in t["before"]), \
                (vid, "maintenance rows are not in the expected pre-restoration state", [r[:3] for r in cur])
            print("  %d maintenance: %d rows -> %d rows" % (vid, len(cur), len(target)))
            have_set = {(r[0], r[1], r[2]) for r in cur}
            for mi, mo, d, *_ in target:
                if (mi, mo, d) not in have_set:
                    print("      + %s mi / %s mo  %s" % (mi, mo if mo else "--", d))
            n += 1
            if apply:
                c.execute("DELETE FROM maintenance WHERE vehicle_id=?", (vid,))
                nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
                for row in target:
                    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,"
                              "difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)", (nid, vid) + row)
                    nid += 1
        # --- drivetrain wording
        if t["relabel"]:
            old, new = t["relabel"]
            raw = c.execute("SELECT differential_fluids_json FROM fluids WHERE vehicle_id=?", (vid,)).fetchone()[0]
            entries = json.loads(raw)
            assert all(set(e) == {"location", "fluid_type"} for e in entries), (vid, "S1.11 shape")
            if any(old in e["location"] for e in entries):
                assert all(old in e["location"] for e in entries), (vid, [e["location"] for e in entries])
                fixed = [{"location": e["location"].replace(old, new), "fluid_type": e["fluid_type"]} for e in entries]
                print("  %d fluids.differential_fluids_json: %s -> %s" % (vid, [e["location"] for e in entries], [e["location"] for e in fixed]))
                n += 1
                if apply:
                    c.execute("UPDATE fluids SET differential_fluids_json=? WHERE vehicle_id=?", (json.dumps(fixed, ensure_ascii=False), vid))
            else:
                assert all(new in e["location"] for e in entries), (vid, [e["location"] for e in entries])
        # --- source notes (suffixed sources only; a frozen bare row is never touched)
        for old, new in t["subs"]:
            for tb in SRC_TABLES:
                for (cur_src,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)).fetchall():
                    if cur_src == BARE or new in cur_src:
                        continue
                    assert cur_src.count(old) == 1, (vid, tb, "source wording not found exactly once", old[:60])
                    ns = cur_src.replace(old, new)
                    assert ns != BARE and ns.startswith(BARE + " (") and ns.endswith(")") and classify(ns, tb, vid) == 1, (vid, tb)
                    print("  %d %s.source: '%s...' updated" % (vid, tb, old[:50]))
                    n += 1
                    if apply:
                        c.execute("UPDATE %s SET source=? WHERE vehicle_id=? AND source=?" % tb, (ns, vid, cur_src))
                        assert c.rowcount == 1, (vid, tb, c.rowcount)
    return n

def verify(c):
    for t in TARGETS:
        vid = t["vid"]
        rows = maint_now(c, vid)
        assert [(r[0], r[1], r[2]) for r in rows] == [(mi, mo, d) for mi, mo, d, _ in t["maint"]], vid
        for tb in SRC_TABLES:
            for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)):
                assert classify(s, tb, vid) == 1, (vid, tb)
        for (s,) in c.execute("SELECT source FROM maintenance WHERE vehicle_id=?", (vid,)):
            assert classify(s, "maintenance", vid) == 1, (vid, s)
    locs = [e["location"] for e in json.loads(c.execute("SELECT differential_fluids_json FROM fluids WHERE vehicle_id=3694").fetchone()[0])]
    assert locs == ["Rear differential (4WD)", "Transfer case (4WD)"], locs
    assert c.execute("SELECT torque_ft_lbs, torque_nm, source FROM torque_specs WHERE vehicle_id=3691").fetchall() == [(79.0, 107.0, BARE)]

# ---------------------------------------------------------------------------------------------------------------
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
print("restore the 2022 Kona / Elantra intervals; bare rows now %d (freeze expects 424)" % bare_count(_c))
n = run(_c, False)
_c.close()
print("%d change group(s) to apply" % n if n else "  nothing to do - already applied")
if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_restore_2022_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
try:
    run(c, True)
    verify(c)
    assert bare_count(c) == 424, ("freeze would break", bare_count(c))      # checked BEFORE commit
    db.commit()
except Exception:
    db.rollback()
    raise
assert run(c, False) == 0, "a second pass still finds work - not idempotent"
print("applied. bare rows after: %d" % bare_count(c))
db.close()
print("DONE - Kona 2022 and Elantra 2022 restored (8 interval rows each).")
