# Hyundai Accent 2014 / 2016 / 2017 - curated specs for three of the model-year rows added by _add_hyundai_rows.py
# (missing-year step B, slice 2 of 3). Ids 38734 (2014), 38735 (2016), 38736 (2017), all RB. No curated rows before.
# Sources (manufacturer, free, citable), saved under _hyundai_manuals/accent/ (gitignored); reads 2026-11-14:
#   2014  US portal 2014-Accent-Owners-Manual.pdf - PDF title '2014 Accent Owners Manual', Copyright 2013, 406 pp
#   2016  US portal 2016_Hyundai_Accent_OM.pdf - PDF title '2016 Hyundai Accent Owner's Manual', Copyright 2015, 456 pp
#   2017  US portal 2017_Hyundai_Accent_OM.pdf - PDF title '2017 Hyundai Accent Owner's Manual', Copyright 2017, 380 pp
#   Single prints: the second host serves no Accent, so there is no second print to compare.
#   Each book was identified by its PDF title, the engine table p.8-2 (Gasoline 1.6, 97.09 cu.in / 1591 cc,
#   '4, In-line') and the dimensions p.8-2 (wheelbase 101.2 in; 4 Door + 5 Door).
#   Between years: the 2016 schedule pages are token-identical to 2014; 2017 differs only in page-number style. The
#   one value that changes is the manual-transaxle fluid grade (SAE 75W/85 in 2014, SAE 70W in 2016 and 2017).
# ** Standing rules applied (no new ruling on this slice; Robert's go: "Go, write"):
#    UNIT CONFLICT: 'Coolant 4.7 US qt.(5.3 l)' - the two figures do not convert (5.3 L is 5.6 US qt) -> capacity not
#       written. 'Brake/clutch fluid 0.7~0.8 US qt.(0.7~0.8 l)' - the same figures for both units -> quantity not
#       written; the fluid type is.
#    SCHEDULE: only printed replacement rows of the NORMAL schedule. Automatic transaxle fluid reads 'No check, No
#       service required' (p.7-17) -> no row. Fuel filter and fuel tank air filter are inspect-only here.
# ** Wording: the oil chart draws '5W-20, 5W-30' across the whole range and '10W-30' from about 0 F, and recommends
#    5W-20; no breakpoint is printed, so none is written (same wording as the 2017 Elantra row). The books print the
#    automatic transaxle fluid as 'ATF SP-4'; written as printed.
# ** Gates (null): spark-plug part number / gap (not published; interval only); 12V battery (not published);
#    coolant capacity and brake-fluid quantity (above). Electric power steering - no fluid. Front-wheel drive - no
#    differential entry.
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows (checked BEFORE
#    commit). S1.12: no bookkeeping words in shipped columns; battery_notes NULL.
#
# Usage:  python _write_hyundai_accent_2014_2017.py            -> DRY RUN: print every row, classify every source
#         python _write_hyundai_accent_2014_2017.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
import sqlite3, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
# the two printed quantities that do not convert: never in a shipped column
NOT_WRITTEN = re.compile(r"4\.7 (?:US )?qt|5\.3 L|0\.7-0\.8")
TABLES = ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]
TARGETS = {38734: 2014, 38735: 2016, 38736: 2017}

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Accent'")}
_c.close()
assert sorted(v for v in VEHICLES if v > 0) == list(range(38731, 38742)), ("the Accent rows are not the eleven expected", sorted(VEHICLES))
for _vid, _year in TARGETS.items():
    assert VEHICLES[_vid] == (_year, "Hyundai", "Accent"), (_vid, VEHICLES[_vid])

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL = "Mixture of antifreeze and water; ethylene glycol base coolant for aluminum radiator"
BRAKE = "FMVSS 116 DOT-3 or DOT-4"
ATF = "Automatic transaxle: ATF SP-4 (MICHANG, SK, NOCA, Hyundai genuine or other approved brands meeting the spec), 7.71 qt / 7.3 L."
MT_QTY = "1.9-2.01 qt / 1.8-1.9 L"
MT_7585 = "Manual transaxle: API GL-4 SAE 75W/85 manual transaxle fluid (HA SYN MTF, HD SYN MTF or GS PAO MTF), " + MT_QTY + "."
MT_70 = "Manual transaxle: API GL-4 SAE 70W manual transaxle fluid (HK MTF 70W, SPIRAX S6 GHME 70W or GS MTF HD 70W), " + MT_QTY + "."
OIL = dict(visc="5W-20 (recommended; chart also allows 5W-30 and 10W-30 by temperature)", type=None, cap="3.8 qt / 3.6 L",
           spec="API SM and ILSAC GF-4 (or above); SAE 5W-20")
TIRES = "P175/70R14 or P195/50R16"
NOTE = ("14-in wheels: P175/70R14; 16-in wheels: P195/50R16; 33 psi front and rear at normal and maximum load. Compact "
        "spare (if equipped) T125/80D15 at 60 psi. Fuel tank 11.4 gal / 43 L.")
LUG_NOTE = "65 to 79 lb-ft (88 to 107 N-m, 9 to 11 kg-m), wheel lug nut tightening torque per owner manual (range)"
PORTAL = "owners.hyundaiusa.com glovebox-manual"
MAINT = [
    (7500, 12, "Engine oil & filter change", "7-7"),
    (97500, 78, "Spark plug replacement (iridium plated)", "7-13"),
    (30000, 24, "Engine air cleaner filter replacement", "7-8"),
    (15000, 12, "Climate control (cabin) air filter replacement", "7-7"),
    (7500, 6, "Tire rotation", "7-7"),
    (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-14"),
]
GATES = ("gated to null: coolant capacity (the capacities page prints 4.7 US qt beside 5.3 l, which do not convert), "
         "brake / clutch-fluid quantity (the same figures are printed for US qt and litres), 12V battery group and CCA "
         "(not published), spark-plug part number and gap (not published, interval only), battery notes")

def src(year, fname, title, copyright_, created, pp, caps_page, chart_page, eps_page, extra):
    return ("owner-manual-verified (per %d Hyundai Accent OM, portal file %s = accent_%d_portal_OM.pdf, %s, PDF title "
            "'%s', Copyright %s, PDF created %s, %d pp, single print (the second manufacturer host serves no Accent); "
            "RB, self-ID engine table p.8-2 Gasoline 1.6 97.09 cu.in (1591cc) '4, In-line', wheelbase 101.2 in and 4 Door "
            "/ 5 Door bodies p.8-2; tires + wheel lug nut torque p.8-3 read from a page render; capacities p.%s; "
            "viscosity chart p.%s read from a page render; electric power steering p.%s; schedule p.7-7 to 7-17 (list "
            "format), the coolant line read from a page render; the automatic-transaxle-fluid schedule line p.7-17 reads "
            "'No check, No service required', so there is no such row; %s%s)"
            % (year, fname, year, PORTAL, title, copyright_, created, pp, caps_page, chart_page, eps_page, extra, GATES))

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=38734, label="2014 RB  Gasoline 1.6", trans=ATF + " " + MT_7585,
      src=src(2014, "2014-Accent-Owners-Manual.pdf", "2014 Accent Owners Manual", "2013 Hyundai Motor America",
              "2013-11-13", 406, "8-4", "8-5", "4-30", ""),
      msrc="Hyundai Owner's Manual (Accent 2014 RB, p.%s)"),
 dict(vid=38735, label="2016 RB  Gasoline 1.6", trans=ATF + " " + MT_70,
      src=src(2016, "2016_Hyundai_Accent_OM.pdf", "2016 Hyundai Accent Owner's Manual", "2015 Hyundai Motor America",
              "2015-08-07", 456, "8-4", "8-5", "4-30",
              "the schedule pages are token-identical to the 2014 book's and the manual-transaxle fluid grade differs "
              "from it (SAE 70W here); "),
      msrc="Hyundai Owner's Manual (Accent 2016 RB, p.%s)"),
 dict(vid=38736, label="2017 RB  Gasoline 1.6", trans=ATF + " " + MT_70,
      src=src(2017, "2017_Hyundai_Accent_OM.pdf", "2017 Hyundai Accent Owner's Manual", "2017 HYUNDAI Motor America",
              "2017-02-16", 380, "8-5", "8-6", "4-24",
              "the schedule pages match the 2016 book's apart from the page-number style; "),
      msrc="Hyundai Owner's Manual (Accent 2017 RB, p.%s)"),
]
assert sorted(r["vid"] for r in ROWS) == sorted(TARGETS), "this script writes the three Accent rows of slice 2 and nothing else"

# ---------------------------------------------------------------------------------------------------------------
def unit_pairs(vid, s):
    """Every printed US / metric pair must convert, within print rounding (ranges end to end). Returns pairs checked."""
    n = 0
    for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
        qs, ls = q.split("-"), l.split("-")
        assert len(qs) == len(ls), (vid, "qt/L range shape", q, l)
        for a, b in zip(qs, ls):                                  # 1 L = 1.0567 US qt
            assert abs(float(a) - float(b) * 1.0567) <= 0.09, (vid, "qt/L mismatch", q, l, s)
            if float(a) < 1.0:                                    # small quantities: test the direction as well
                assert 1.03 <= float(a) / float(b) <= 1.09, (vid, "qt/L ratio", q, l)
            n += 1
    for g, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) gal / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
        gs, ls = g.split("-"), l.split("-")
        assert len(gs) == len(ls), (vid, "gal/L range shape", g, l)
        for a, b in zip(gs, ls):                                  # 1 US gal = 3.7854 L; tolerance follows both printed precisions
            gdec = len(a.split(".")[1]) if "." in a else 0
            ldec = len(b.split(".")[1]) if "." in b else 0
            tol = 0.5 * 10 ** -gdec + (0.5 * 10 ** -ldec) / 3.7854 + 0.005
            assert abs(float(a) - float(b) / 3.7854) <= tol, (vid, "gal/L mismatch", g, l, s)
            n += 1
    assert not re.search(r"[0-9] (?:qt|gal)(?! /)", s or ""), (vid, "unpaired US unit", s)
    return n

def check(row):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid = row["vid"]
    year = int(row["label"][:4])
    assert VEHICLES.get(vid) == (year, "Hyundai", "Accent") and TARGETS.get(vid) == year, (vid, "target row is not the labelled vehicle")
    assert ("per %d Hyundai Accent OM" % year) in row["src"] and ("Accent %d " % year) in row["msrc"], (vid, "source year")
    assert ("capacities p.8-5; viscosity chart p.8-6" in row["src"]) == (year == 2017), (vid, "capacity page per year")
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    for mi, mo, desc, page in MAINT:
        assert re.fullmatch(r"7-\d{1,2}", page), (vid, desc, page)
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert isinstance(mi, int) and mi > 0 and isinstance(mo, int) and mo > 0, (vid, desc)
    assert len(MAINT) == 6 and not any("transaxle" in d.lower() or "fuel" in d.lower() for _, _, d, _ in MAINT), vid
    # the one value that changes between the years
    assert ("SAE 75W/85" in row["trans"]) == (year == 2014) and ("SAE 70W" in row["trans"]) == (year != 2014), (vid, row["trans"])
    assert "ATF SP-4" in row["trans"] and "7.71 qt / 7.3 L" in row["trans"] and MT_QTY in row["trans"], vid
    shipped = [OIL["visc"], OIL["cap"], OIL["spec"], row["trans"], BRAKE, COOL, EPS, TIRES, NOTE, LUG_NOTE] + [d for _, _, d, _ in MAINT]
    for s in shipped:
        m = JARGON.search(s)
        assert not m, (vid, m.group(0), s)
        assert not NOT_WRITTEN.search(s), (vid, "a quantity that does not convert is in a shipped column", s)
    assert row["src"] != BARE and row["src"].startswith(BARE + " (") and row["src"].endswith(")")
    return sum(unit_pairs(vid, s) for s in shipped)

def bare_count(c):
    return c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                     "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source=?", (BARE,)).fetchone()[0]

def holds(c, vid):
    """What the target id holds now: {table: sorted source tokens}. A frozen bare row must never be deleted."""
    out = {}
    for t in TABLES:
        toks = sorted(set((r[0] or "NULL").split(" (")[0] for r in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % t, (vid,))))
        if toks:
            out[t] = toks
    return out

def write(c, nid, row):
    vid = row["vid"]
    for t in TABLES:
        c.execute("DELETE FROM %s WHERE vehicle_id=?" % t, (vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,"
              "filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, OIL["visc"], OIL["type"], OIL["cap"], None, OIL["spec"], None, None, None, None, None, row["src"]))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,"
              "coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
              (vid, row["trans"], None, BRAKE, COOL, None, EPS, None, row["src"]))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,"
              "tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,"
              "wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,"
              "real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, None, None, None, None, None, TIRES, 33, 33, None, None, None, None, None, NOTE, None, None, None, None,
               None, row["src"]))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
              (vid, "lug_nut", 65.0, 88.0, LUG_NOTE, row["src"]))
    for mi, mo, desc, page in MAINT:
        c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,"
                  "difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (nid, vid, mi, mo, desc, row["msrc"] % page, "standard", None, None, None))
        nid += 1
    return nid

def show(row):
    print("\n=== %d  Accent %s" % (row["vid"], row["label"]))
    print("  oil   : %s | %s | %s" % (OIL["cap"], OIL["visc"], OIL["spec"]))
    print("  trans : %s" % row["trans"])
    print("  cool  : (capacity not written) | %s" % COOL)
    print("  brake : %s | steering: %s" % (BRAKE, EPS))
    print("  tires : %s @ 33 psi | %s" % (TIRES, NOTE))
    print("  lug   : 65.0 lb-ft / 88.0 N-m | %s" % LUG_NOTE)
    for mi, mo, desc, page in MAINT:
        print("  maint : %7d mi / %3d mo  %s  [p.%s]" % (mi, mo, desc, page))
    print("  src   : %s" % row["src"])

# ---------------------------------------------------------------------------------------------------------------
npairs = sum(check(row) for row in ROWS)
print("contract checks PASS: %d vehicles, %d maintenance rows, %d printed unit pairs converted; every source classified "
      "verified with a suffix; every target id is the labelled vehicle" % (len(ROWS), len(ROWS) * len(MAINT), npairs))
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
print("bare rows now: %d (freeze expects 424)" % bare_count(_c))
for row in ROWS:
    h = holds(_c, row["vid"])
    print("  id %d holds now: %s" % (row["vid"], h))
    for t, toks in h.items():
        assert BARE not in toks, (row["vid"], t, "a frozen bare row sits on a target id - stop")
_c.close()
for row in ROWS:
    show(row)

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_accent_2014_2017_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
try:
    nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
    for row in ROWS:
        nid = write(c, nid, row)
        print("  wrote %d  Accent %s" % (row["vid"], row["label"]))
    assert bare_count(c) == 424, ("freeze would break", bare_count(c))      # checked BEFORE commit
    db.commit()
except Exception:
    db.rollback()
    raise

print("\nVerify:")
for row in ROWS:
    vid = row["vid"]
    o = c.execute("SELECT capacity_with_filter, capacity_without_filter, source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchall()
    f = c.execute("SELECT coolant_capacity, transmission_capacity, differential_fluids_json, brake_fluid, transmission_fluid FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, tire_pressure_rear, battery_group, battery_notes, spark_plug_type FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT component, torque_ft_lbs, source, torque_nm FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), MIN(source) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(MAINT) and e == 0, vid
    assert f[0][0] is None and f[0][1] is None and f[0][2] is None and p[0][3] is None and p[0][4] is None and p[0][5] is None, vid
    assert t[0][2].startswith(BARE + " (") and classify(t[0][2], "torque_specs", vid) == 1 and t[0][3] == 88.0
    for tb in ("oil_change", "fluids", "parts", "maintenance", "torque_specs"):
        for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)):
            assert classify(s, tb, vid) == 1, (vid, tb, s[:60])
    g = [c.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id=?" % tb, (vid,)).fetchone()[0]
         for tb in ("fuel_economy", "recalls", "safety_ratings", "complaints")]
    print("  %d: oil=%s | cool cap=%s | manual=%s | tire=%s @%s | lug=%s / %s | maint=%d | government rows %s"
          % (vid, o[0][0], f[0][0], "75W/85" if "75W/85" in f[0][4] else "70W", p[0][0], p[0][1], t[0][1], t[0][3], m[0], g))
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare_count(c))
db.close()
print("DONE - %d rows written." % len(ROWS))
