# Hyundai second-host LABEL AUDIT corrections (2026-11-14). Surgical edits to six live rows; no new vehicle.
#
# Finding: a year label on ownersmanual.hyundai.com is not a model year until tested. A first print carries the
# previous year's copyright, and a back-catalogue label Y usually carries copyright Y, so label Y is often the FIRST
# PRINT OF MODEL YEAR Y+1. Each label cited by a live row was tested against the titled US-portal books for that year
# and the next, on values that differ between the two (see KYR_Hyundai_Verification_Log.md, LABEL AUDIT section).
#
#   CONTRADICTED (holds the next model year's book):  OS/2022 (Kona), CN7/2022 (Elantra), QX/2022 (Venue)
#   UNPROVED (matches next year's titled book on every differing marker): DN8/2021, CN7/2021, OS/2020, NX4a/2024
#
# Ruling 2026-11-14 ("Yes, as recommended"): fix the source notes; REMOVE every value that rests on an unproved book
# alone. No shipped value was proved wrong - these are removed because they are not proved for the row's model year.
#
#   Sonata 2021  (id 12853)  remove the G2.5 T-GDI set (oil, 0W-30, dual clutch fluids, coolant, 48,000-mile plug row)
#   Elantra 2021 (id 2163)   remove the G1.6 T-GDi set (oil, dual clutch + manual transmission fluid, coolant,
#                            235/40R18 tire line, T125/80D16 spare, 47,000-mile plug row)
#   Tucson 2024  (id 6783)   coolant back to the single figure printed in its titled book (10.04 qt / 9.5 L)
#   Kona 2020 (673), Kona 2022 (3694), Elantra 2022 (3691)   source wording only - no value changes
#
# Every value that stays on Sonata 2021 and Elantra 2021 was re-checked against the TITLED 2021 portal book
# (tires p.2-9, capacities p.2-11, full-synthetic note p.2-12).
# The frozen bare wheel-nut rows on 12853, 2163 and 3691 are not touched; the bare count is checked BEFORE commit.
# Older write scripts for these ids refuse --write unless told they are superseded; run THIS script after any re-run.
#
# Usage:  python _fix_hyundai_label_audit_2026_11_14.py            -> DRY RUN: show every change, write nothing
#         python _fix_hyundai_label_audit_2026_11_14.py --write    -> backup DB, apply, verify   (idempotent)
import sqlite3, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
SRC_TABLES = ("oil_change", "fluids", "parts", "torque_specs")
GLOBAL = "ownersmanual.hyundai.com full_pdf %s en_US"
# _fix_hyundai_restore_2022_intervals.py later rewords the Kona 2022 / Elantra 2022 notes; its mark means "already applied"
RESTORED_MARK = "restored 2026-11-14"

SONATA_SRC = (
    "owner-manual-verified (per 2021 Hyundai Sonata OM, portal file 2021-Sonata-Owners-Manual.pdf = "
    "sonata_2021_DN8_portal_OM.pdf, owners.hyundaiusa.com glovebox-manual, PDF title '2021 Sonata Owners Manual', "
    "Copyright 2020 HYUNDAI Motor America (G1.6 T-GDi + G2.5 GDi; dims p.2-7, tires p.2-9, capacities p.2-11, viscosity "
    "p.2-12); DN8, wheelbase 111.8 in; every written value is printed in this titled book; schedule tables are rotated "
    "and were read from decoded text and page renders; re-read 2026-11-14 to the current standard; label audit "
    "2026-11-14: the second-host book " + (GLOBAL % "DN8 2021") + " = sonata_2021_DN8_global_OM.pdf (Copyright 2021), "
    "earlier treated as a later print of this model year, matches the 2022 portal book wherever that book differs from "
    "this one, so its model year is not proved; the G2.5 T-GDI values taken from it alone (oil, 0W-30, dual clutch "
    "fluids, coolant, 48,000-mile plugs) were removed; gated to null: G2.5 GDi oil capacity (this book prints 5.49 qt / "
    "5.2 L, the 2022 portal book and the second-host book print 6.13 qt / 5.8 L), coolant capacity (this book prints "
    "4.76 qt / 4.5 L and 5.49 qt / 5.2 L, repeating its own oil cells; the other books print 8.03 qt / 7.6 L and 9.07 qt "
    "/ 8.59 L), 12V battery group and CCA (not published), spark-plug part number and gap (not published, interval "
    "only), battery notes; Hybrid has its own manual)")

ELANTRA_SRC = (
    "owner-manual-verified (per 2021 Hyundai Elantra OM, portal file 2021-Elantra-Owners-Manual.pdf = "
    "elantra_2021_portal_OM.pdf, owners.hyundaiusa.com glovebox-manual, PDF title '2021 Elantra Owners Manual', "
    "Copyright 2020 HYUNDAI Motor America (Smartstream G2.0 only; dims p.2-7, tires p.2-9, capacities p.2-11, viscosity "
    "p.2-12); CN7, wheelbase 107 in; every written value is printed in this titled book except the gallon rendering of "
    "the 47 L fuel tank (this book prints 47 L beside 49.66 US qt; the second-host CN7a books print the same 47 L beside "
    "12.42 US gal); schedule tables are rotated and were read from decoded text and page renders; re-read 2026-11-14 to "
    "the current standard; label audit 2026-11-14: the second-host books " + (GLOBAL % "CN7 2021") + " = "
    "elantra_2021_CN7_global_OM.pdf (Copyright 2021, G2.0 + G1.6 T-GDi) and " + (GLOBAL % "CN7a 2021") + " (Copyright "
    "2021, G2.0 only), earlier treated as later prints of this model year, could not be proved to be this model year "
    "(the CN7 book is closest to the 2022 portal book); the G1.6 T-GDi values taken from the CN7 book alone (oil, dual "
    "clutch and manual transmission fluid, coolant, 235/40R18 tire and its pressure, T125/80D16 spare, 47,000-mile "
    "plugs) were removed; the CN7a book agrees with every G2.0 value written; gated to null: 12V battery group and CCA "
    "(the battery page shows only a capacity-label illustration, AGM70L-DIN, captioned 'the actual battery label in the "
    "vehicle may differ'), spark-plug part number and gap (not published, interval only), battery notes; Hybrid and N "
    "have their own manuals)")

TUCSON_NOTE_OLD_MARK = "; 2026-11-14 second-book check: "
TUCSON_NOTE_NEW = (
    "; label audit 2026-11-14: a second coolant figure (10.11 qt / 9.57 L, from " + (GLOBAL % "NX4a 2024") + ") was "
    "added on 2026-11-14 and removed the same day - that book carries Copyright 2023 and its figure matches the 2022 and "
    "2023 books, so its model year is not proved; this titled book and " + (GLOBAL % "NX4 2024") + " both print 10.04 qt "
    "/ 9.5 L)")

# Each fix: (vehicle id, expected (year, make, model), list of operations)
#   ("set",  table, column, old, new)        column value old -> new (new may be None)
#   ("src",  tables, new_source, old_must_contain)   whole-source rewrite on the listed tables
#   ("sub",  old_substring, new_substring)   substring rewrite in every suffixed source of the row
#   ("del",  description, mileage)           delete one maintenance row
FIXES = [
 (12853, (2021, "Hyundai", "Sonata"), [
    ("set", "oil_change", "viscosity",
     "0W-20 (Smartstream G1.6 T-GDi and Smartstream G2.5 GDi) / 0W-30 (Smartstream G2.5 T-GDI)", "0W-20"),
    ("set", "oil_change", "capacity_with_filter",
     "5.07 qt / 4.8 L (Smartstream G1.6 T-GDi) / 6.13 qt / 5.8 L (Smartstream G2.5 T-GDI)",
     "5.07 qt / 4.8 L (Smartstream G1.6 T-GDi)"),
    ("set", "fluids", "transmission_fluid",
     "Automatic transmission: ATF SP-IV (MICHANG, SK, NOCA, S-OIL, Hyundai genuine or other approved brands meeting the "
     "spec), 6.89 qt / 6.5 L. Dual clutch transmission (Smartstream G2.5 T-GDI): gear oil GS WDCTF HD G, 3.49-3.59 qt / "
     "3.3-3.4 L; control oil GS WDCTF HD H, 2.59-2.64 qt / 2.45-2.5 L.",
     "Automatic transmission: ATF SP-IV (MICHANG, SK, NOCA, S-OIL, Hyundai genuine or other approved brands meeting the "
     "spec), 6.89 qt / 6.5 L."),
    ("set", "fluids", "coolant_capacity", "8.59 qt / 8.13 L (Smartstream G2.5 T-GDI)", None),
    ("del", "Spark plug replacement (Smartstream G2.5 T-GDI)", 48000),
    ("src", ("oil_change", "fluids", "parts"), SONATA_SRC, "per 2021 Hyundai Sonata OM"),
 ]),
 (2163, (2021, "Hyundai", "Elantra"), [
    ("set", "oil_change", "capacity_with_filter",
     "4.54 qt / 4.3 L (Smartstream G2.0) / 5.07 qt / 4.8 L (Smartstream G1.6 T-GDi)", "4.54 qt / 4.3 L (Smartstream G2.0)"),
    ("set", "fluids", "transmission_fluid",
     "Intelligent variable transmission: Hyundai genuine SP-CVT1, 6.87 qt / 6.5 L. Dual clutch transmission: SAE 70W API "
     "GL-4 dual clutch transmission fluid, 1.7-1.8 qt / 1.6-1.7 L. Manual transmission: SAE 70W API GL-4 manual "
     "transmission fluid, 1.6-1.7 qt / 1.5-1.6 L.",
     "Intelligent variable transmission: Hyundai genuine SP-CVT1, 6.87 qt / 6.5 L."),
    ("set", "fluids", "coolant_capacity",
     "7.82 qt / 7.4 L (Smartstream G2.0) / 7.19 qt / 6.8 L (Smartstream G1.6 T-GDi)", "7.82 qt / 7.4 L (Smartstream G2.0)"),
    ("set", "parts", "tire_size", "195/65R15, 205/55R16, 225/45R17 or 235/40R18", "195/65R15, 205/55R16 or 225/45R17"),
    ("set", "parts", "tire_size_note",
     "15-in wheels: 195/65R15; 16-in wheels: 205/55R16; 17-in wheels: 225/45R17; 34 psi front and 31 psi rear. 18-in "
     "wheels: 235/40R18 at 33 psi front and rear. Compact spare T125/80D15 or T125/80D16 at 60 psi. Fuel tank 12.42 gal "
     "/ 47 L.",
     "15-in wheels: 195/65R15; 16-in wheels: 205/55R16; 17-in wheels: 225/45R17; 34 psi front and 31 psi rear. Compact "
     "spare T125/80D15 at 60 psi. Fuel tank 12.42 gal / 47 L."),
    ("del", "Spark plug replacement (Smartstream G1.6 T-GDi)", 47000),
    ("src", ("oil_change", "fluids", "parts"), ELANTRA_SRC, "per 2021 Hyundai Elantra OM"),
 ]),
 (6783, (2024, "Hyundai", "Tucson"), [
    ("set", "fluids", "coolant_capacity",
     "10.04 qt / 9.5 L or 10.11 qt / 9.57 L (Smartstream G2.5 GDI)", "10.04 qt / 9.5 L (Smartstream G2.5 GDI)"),
    ("tucson_note",),
 ]),
 (673, (2020, "Hyundai", "Kona"), [
    ("sub", "cross-checked against the later print " + (GLOBAL % "OS 2020") + ": every written value identical",
            "compared with the second-host book " + (GLOBAL % "OS 2020") + ": every written value identical (label audit "
            "2026-11-14: that book's model year is not proved - its one differing value matches the titled 2021 book - so "
            "it is not counted as a second print of this year)"),
    ("sub", "brake-fluid replacement interval (first print inspect-only, later print 60,000 / 48,000 mi)",
            "brake-fluid replacement interval (this book is inspect-only; the second-host book prints replacement at "
            "60,000 / 48,000 mi)"),
 ]),
 (3694, (2022, "Hyundai", "Kona"), [
    ("sub", "cross-checked against the later print " + (GLOBAL % "OS 2022") + ": every written value agrees (litre "
            "figures identical, later print shows US gal)",
            "compared with the second-host book " + (GLOBAL % "OS 2022") + ": every written value agrees (litre figures "
            "identical, that book shows US gal); label audit 2026-11-14: that label holds the 2023 model year's book (it "
            "matches the titled 2023 portal book, not this one, on every value that differs between them), so it is not a "
            "second print of this year and its differences from this book are model-year changes"),
 ]),
 (3691, (2022, "Hyundai", "Elantra"), [
    ("sub", "(first print, G2.0 + G1.6 T-GDi; dims p.2-9, tires p.2-11, capacities p.2-13, viscosity p.2-14) and two later "
            "prints: ",
            "(G2.0 + G1.6 T-GDi; dims p.2-9, tires p.2-11, capacities p.2-13, viscosity p.2-14), compared with two "
            "second-host books: "),
    ("sub", "the prints dispute three schedule items, so only what they state identically is written;",
            "three schedule items differ between this book and the CN7 2022 book and were left out; label audit "
            "2026-11-14: the CN7 2022 label holds the 2023 model year's book (it matches the titled 2023 portal book, not "
            "this one, where they differ), so those differences are model-year changes, not print conflicts;"),
    ("sub", "G1.6 T-GDi spark-plug interval (first print 47,000 mi, later print 48,000 mi), coolant interval after the "
            "first replacement (30,000 mi in the first print and CN7a, 24,000 mi in CN7), tire-rotation months (none in "
            "the first print, 12 in the later prints), full-synthetic requirement (later print only)",
            "G1.6 T-GDi spark-plug interval (this book 47,000 mi, the CN7 2022 book 48,000 mi), coolant interval after "
            "the first replacement (30,000 mi in this book and CN7a, 24,000 mi in CN7), tire-rotation months (none in "
            "this book, 12 in the second-host books), full-synthetic requirement (second-host book only)"),
 ]),
]

# ---------------------------------------------------------------------------------------------------------------
def unit_pairs(s):
    for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
        qs, ls = q.split("-"), l.split("-")
        assert len(qs) == len(ls), ("qt/L range shape", q, l)
        for a, b in zip(qs, ls):
            assert abs(float(a) - float(b) * 1.0567) <= 0.09, ("qt/L mismatch", q, l, s)
    for g, l in re.findall(r"([0-9.]+) gal / ([0-9.]+) L", s or ""):
        dec = len(g.split(".")[1]) if "." in g else 0
        assert abs(float(g) - float(l) / 3.7854) <= max(0.03, 0.5 * 10 ** -dec + 0.005), ("gal/L mismatch", g, l, s)
    assert not re.search(r"[0-9] (?:qt|gal)(?! /)", s or ""), ("unpaired US unit", s)

def bare_count(c):
    return c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                     "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source=?", (BARE,)).fetchone()[0]

def good_source(s, table, vid):
    assert s != BARE and s.startswith(BARE + " (") and s.endswith(")"), (vid, table, s[:60])
    assert classify(s, table, vid) == 1, (vid, table, "source is not classified verified")

def plan(c):
    """Validate every operation against the current DB and return [(description, sql, params)] still to apply."""
    todo = []
    for vid, want, ops in FIXES:
        have = c.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        assert have == want, (vid, "target row is not the expected vehicle", have, want)
        for op in ops:
            kind = op[0]
            if kind == "set":
                _, table, col, old, new = op
                rows = c.execute("SELECT %s FROM %s WHERE vehicle_id=?" % (col, table), (vid,)).fetchall()
                assert len(rows) == 1, (vid, table, len(rows))
                cur = rows[0][0]
                if cur == new:
                    continue                                    # already applied
                assert cur == old, (vid, table, col, "unexpected current value", cur)
                if new is not None:
                    assert not JARGON.search(new), (vid, new)
                    unit_pairs(new)
                todo.append(("%d %s.%s: %s  ->  %s" % (vid, table, col, old, new),
                             "UPDATE %s SET %s=? WHERE vehicle_id=?" % (table, col), (new, vid)))
            elif kind == "del":
                _, desc, miles = op
                rows = c.execute("SELECT id FROM maintenance WHERE vehicle_id=? AND description=? AND mileage_interval=?",
                                 (vid, desc, miles)).fetchall()
                assert len(rows) <= 1, (vid, desc, len(rows))
                if rows:
                    todo.append(("%d maintenance: delete '%s' (%d mi)" % (vid, desc, miles),
                                 "DELETE FROM maintenance WHERE id=? AND vehicle_id=?", (rows[0][0], vid)))
            elif kind == "src":
                _, tables, new_src, must = op
                for t in tables:
                    good_source(new_src, t, vid)
                    cur = c.execute("SELECT source FROM %s WHERE vehicle_id=?" % t, (vid,)).fetchone()[0]
                    if cur == new_src:
                        continue
                    assert must in cur and cur != BARE, (vid, t, "unexpected current source", cur[:80])
                    todo.append(("%d %s.source: rewritten (%d -> %d chars)" % (vid, t, len(cur), len(new_src)),
                                 "UPDATE %s SET source=? WHERE vehicle_id=?" % t, (new_src, vid)))
            elif kind == "sub":
                _, old, new = op
                touched = 0
                for t in SRC_TABLES:
                    for (cur,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % t, (vid,)).fetchall():
                        if cur == BARE:
                            continue                            # frozen bare row: never touched
                        if new in cur or RESTORED_MARK in cur:
                            touched += 1
                            continue                            # already applied (or reworded later by the restoration script)
                        assert cur.count(old) == 1, (vid, t, "source text to replace not found exactly once", old[:60])
                        ns = cur.replace(old, new)
                        good_source(ns, t, vid)
                        touched += 1
                        todo.append(("%d %s.source: '%s...' reworded" % (vid, t, old[:46]),
                                     "UPDATE %s SET source=replace(source, ?, ?) WHERE vehicle_id=? AND source<>?" % t,
                                     (old, new, vid, BARE)))
                assert touched >= 3, (vid, "expected the wording in at least three suffixed sources", touched)
            elif kind == "tucson_note":
                cur = c.execute("SELECT source FROM fluids WHERE vehicle_id=?", (vid,)).fetchone()[0]
                if TUCSON_NOTE_NEW in cur:
                    continue
                assert cur.count(TUCSON_NOTE_OLD_MARK) == 1 and cur.endswith(")"), (vid, "unexpected fluids source")
                ns = cur[:cur.index(TUCSON_NOTE_OLD_MARK)] + TUCSON_NOTE_NEW
                good_source(ns, "fluids", vid)
                base = c.execute("SELECT source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchone()[0]
                assert ns.startswith(base[:-1]), (vid, "fluids source no longer matches the row's base citation")
                todo.append(("%d fluids.source: second-book note replaced by the label-audit note" % vid,
                             "UPDATE fluids SET source=? WHERE vehicle_id=?", (ns, vid)))
    return todo

def verify(c):
    for vid, want, ops in FIXES:
        for t in SRC_TABLES:
            for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % t, (vid,)):
                assert classify(s, t, vid) == 1, (vid, t)
        for (s,) in c.execute("SELECT source FROM maintenance WHERE vehicle_id=?", (vid,)):
            assert classify(s, "maintenance", vid) == 1 and "later print" not in s, (vid, s)
    row = lambda q, v: c.execute(q, (v,)).fetchone()
    assert row("SELECT viscosity, capacity_with_filter FROM oil_change WHERE vehicle_id=?", 12853) == ("0W-20", "5.07 qt / 4.8 L (Smartstream G1.6 T-GDi)")
    assert row("SELECT coolant_capacity FROM fluids WHERE vehicle_id=?", 12853) == (None,)
    assert row("SELECT COUNT(*) FROM maintenance WHERE vehicle_id=?", 12853) == (8,)
    assert row("SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?", 2163) == ("4.54 qt / 4.3 L (Smartstream G2.0)",)
    assert row("SELECT COUNT(*) FROM maintenance WHERE vehicle_id=?", 2163) == (7,)
    assert row("SELECT coolant_capacity FROM fluids WHERE vehicle_id=?", 6783) == ("10.04 qt / 9.5 L (Smartstream G2.5 GDI)",)
    for vid in (12853, 2163):                                   # nothing about the removed engines is left in a shipped column
        for t, cols in (("oil_change", "viscosity, capacity_with_filter, oem_spec"), ("fluids", "transmission_fluid, coolant_capacity"),
                        ("parts", "tire_size, tire_size_note")):
            vals = c.execute("SELECT %s FROM %s WHERE vehicle_id=?" % (cols, t), (vid,)).fetchone()
            for x in vals:
                bad = "G2.5 T-GDI" if vid == 12853 else "G1.6 T-GDi"
                assert x is None or (bad not in x and "0W-30" not in x and "235/40R18" not in x and "Dual clutch" not in x), (vid, t, x)
        descs = [r[0] for r in c.execute("SELECT description FROM maintenance WHERE vehicle_id=?", (vid,))]
        assert not any(("G2.5 T-GDI" in d) or ("G1.6 T-GDi" in d and vid == 2163) for d in descs), (vid, descs)
    for vid in (12853, 2163, 3691):                             # frozen wheel-nut rows untouched
        assert c.execute("SELECT torque_ft_lbs, torque_nm, source FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall() == [(79.0, 107.0, BARE)], vid

# ---------------------------------------------------------------------------------------------------------------
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
todo = plan(_c)
print("label-audit corrections: %d statement(s) to apply; bare rows now %d (freeze expects 424)" % (len(todo), bare_count(_c)))
_c.close()
for d, _, _ in todo:
    print("  - " + d[:300])
if not todo:
    print("  nothing to do - already applied")
if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_label_audit_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
try:
    for d, sql, params in plan(c):
        c.execute(sql, params)
        assert c.rowcount == 1, (d, c.rowcount)
    verify(c)
    assert bare_count(c) == 424, ("freeze would break", bare_count(c))      # checked BEFORE commit
    db.commit()
except Exception:
    db.rollback()
    raise
print("applied. bare rows after: %d" % bare_count(c))
assert plan(c) == [], "a second pass still finds work - not idempotent"
db.close()
print("DONE - six rows corrected (three with value removals, three with source wording only).")
