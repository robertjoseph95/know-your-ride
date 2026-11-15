# Hyundai Accent 2018 / 2019 / 2020 / 2021 / 2022 - curated specs for the last five model-year rows added by
# _add_hyundai_rows.py (missing-year step B, slice 3 of 3). Ids 38737-38741, all HC. No curated rows before.
# Sources (manufacturer, free, citable), saved under _hyundai_manuals/accent/ (gitignored); reads 2026-11-14:
#   2018  US portal '2018 Accent Owners Manual.pdf' - Copyright 2018, created 2018-02-20, 442 pp
#   2019  US portal '2019 Accent OM.pdf' - Copyright 2018, created 2018-08-01, 442 pp (21 pages revised from 2018)
#   2020  US portal '2020 Accent Owner's Manual.pdf' - PDF title and cover name the year, Copyright 2019, 445 pp
#   2021  US portal '2021 Accent OM.pdf' - Copyright 2020, proof marks 'HCa HMA' 5/25/2020, 443 pp
#   2022  US portal 2022-Accent-OM.pdf - Copyright 2021, created 2021-07-06, 445 pp
#   Single prints: the second host serves no Accent, so there is no second print to compare. The 2018, 2019, 2021
#   and 2022 files carry no title naming the year; they were accepted on portal folder, file name, copyright and
#   creation date (ruling 2026-11-14).
#   Each book was identified by the sedan on its exterior overview p.1-2 (page renders), the engine table p.8-2
#   (2018 / 2019 Gamma 1.6 GDI 1,591 cc; 2020-2022 Smartstream G1.6 1,598 cc; 'In-line 4 cylinder') and the wheel
#   base 101.5 in.
#   Between years: 2018 and 2019 are token-identical on every specification and schedule page. 2020 has the new
#   engine and variable transmission but keeps the wider oil chart. 2021 / 2022 narrow the chart to 0W-20, name the
#   brake fluid DOT 4, add a brake-fluid replacement line and move the schedule step from 7,500 to 8,000 miles.
# ** Standing rules applied (no new ruling on this slice; Robert's go: "Go, write"):
#    UNIT CONFLICT: 'Brake/Clutch fluid 0.7~0.8 US qt.(0.7~0.8 l)' - the same figures for both units -> quantity not
#       written in any of the five years; the fluid type is. Coolant is printed correctly here (5.3 l / 5.60 US qt).
#    SCHEDULE: only printed replacement rows of the NORMAL schedule. Automatic / variable transmission fluid reads 'No
#       check, No service required' (p.7-10) in every book -> no row. Brake / clutch fluid is inspect-only through
#       2020 and has a replacement line from 2021.
# ** Months-only row: from 2020 the climate control air filter is printed 'Replace every 12 Months' with no mileage ->
#    mileage NULL (the fleet already holds manual-cited rows of that shape).
# ** Oil type is left empty for 2021 / 2022: the books require API SN PLUS or above for the normal interval and call
#    mineral or semi-synthetic oil a severe condition, but never print 'full synthetic'.
# ** The 2022 book still lists a manual transmission fluid (EPA lists the variable transmission only that year);
#    written as the book prints it.
# ** Gates (null): spark-plug part number / gap (not published; interval only); 12V battery (not published);
#    brake-fluid quantity (above). Electric power steering - no fluid. Front-wheel drive - no differential entry.
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows (checked BEFORE
#    commit). S1.12: no bookkeeping words in shipped columns; battery_notes NULL.
#
# Usage:  python _write_hyundai_accent_2018_2022.py            -> DRY RUN: print every row, classify every source
#         python _write_hyundai_accent_2018_2022.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
import sqlite3, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
NOT_WRITTEN = re.compile(r"0\.7-0\.8")                                          # the brake-fluid quantity that does not convert
TABLES = ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]
TARGETS = {38737: 2018, 38738: 2019, 38739: 2020, 38740: 2021, 38741: 2022}

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Accent'")}
_c.close()
assert sorted(v for v in VEHICLES if v > 0) == list(range(38731, 38742)), ("the Accent rows are not the eleven expected", sorted(VEHICLES))
for _vid, _year in TARGETS.items():
    assert VEHICLES[_vid] == (_year, "Hyundai", "Accent"), (_vid, VEHICLES[_vid])

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
COOL_CAP = "5.60 qt / 5.3 L"
BRAKE_34 = "FMVSS 116 DOT-3 or DOT-4"
BRAKE_4 = "DOT 4 (SAE J1704 DOT-4 LV, ISO 4925 Class 6, FMVSS 116 DOT-4)"
MT = ("Manual transmission: API GL-4 SAE 70W TGO-9 manual transmission fluid (HK SYN MTF 70W, SPIRAX S6 GHME 70W MTF or "
      "GS MTF HD 70W), 1.7-1.8 qt / 1.6-1.7 L.")
AT = ("Automatic transmission: ATF SP-IV (MICHANG, SK, NOCA, Hyundai genuine or other approved brands meeting the spec), "
      "7.1 qt / 6.7 L. " + MT)
IVT = "Intelligent variable transmission: SP-CVT1 (use only the specified genuine fluid), 6.87 qt / 6.5 L. " + MT
TIRES = "185/65R15 or 205/45R17"
NOTE = ("15-in wheels: 185/65R15; 17-in wheels: 205/45R17; 33 psi front and rear at normal and maximum load. Compact "
        "spare T125/80D15 at 60 psi. Fuel tank 11.9 gal / 45 L.")
LUG_NOTE = "79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)"
PORTAL = "owners.hyundaiusa.com glovebox-manual"
COOLANT_ROW = "Engine coolant first replacement; thereafter every 30,000 mi / 24 months"
CABIN_ROW = "Climate control (cabin) air filter replacement"
OIL_GAMMA = dict(visc="5W-20 (recommended; chart also allows 5W-30 and 10W-30 by temperature)", type=None, cap="3.49 qt / 3.3 L",
                 spec="API SM and ILSAC GF-4 (or above), ACEA A5/B5; SAE 5W-20")
OIL_2020 = dict(visc="0W-20 (recommended; chart also allows 0W-30, 5W-20, 5W-30 and 10W-30 by temperature)", type=None,
                cap="4.02 qt / 3.8 L", spec="API Latest (ILSAC Latest) or ACEA C5; SAE 0W-20")
OIL_GF6 = dict(visc="0W-20", type=None, cap="4.02 qt / 3.8 L", spec="API SN PLUS/SP or ILSAC GF-6; SAE 0W-20")

def maint(step, cabin, rotation_months, brake):
    """step = schedule step in miles (7,500 or 8,000); cabin = (miles, months); brake = replacement line present."""
    rows = [
        (step, 12, "Engine oil & filter change", "7-8"),
        (step * 13 if step == 7500 else step * 12, None, "Spark plug replacement", "7-8"),
        (step * 3, 36, "Engine air cleaner filter replacement", "7-8"),
        (cabin[0], cabin[1], CABIN_ROW, "7-9"),
        (step, rotation_months, "Tire rotation", "7-8"),
        (120000, 120, COOLANT_ROW, "7-9"),
    ]
    if brake:
        rows.append((48000, 48, "Brake fluid replacement", "7-9"))
    return rows

GATE_TAIL = ("gated to null: brake / clutch-fluid quantity (the same figures are printed for US qt and litres), 12V "
             "battery group and CCA (not published), spark-plug part number and gap (not published, interval only), "
             "battery notes")

def src(year, fname, ident, engine, eps_page, extra):
    return ("owner-manual-verified (per %d Hyundai Accent OM, portal file %s = accent_%d_portal_OM.pdf, %s, %s, single "
            "print (the second manufacturer host serves no Accent); HC, self-ID engine table p.8-2 %s 'In-line 4 "
            "cylinder', wheel base 101.5 in p.8-2, sedan on the exterior overview p.1-2 (page render); tires + wheel lug "
            "nut torque p.8-4 read from a page render; capacities p.8-6 / 8-7; viscosity chart p.8-8 read from a page "
            "render; electric power steering p.%s; schedule p.7-8 to 7-10; %s%s)"
            % (year, fname, year, PORTAL, ident, engine, eps_page, extra, GATE_TAIL))

NO_TITLE = "no PDF title names the year (accepted by ruling 2026-11-14 on portal folder, file name, copyright and creation date)"
GAMMA = "Gamma 1.6 GDI 97.09 cu.in (1,591cc)"
SMART = "Smartstream G1.6 97.52 cu.in (1,598cc)"
AT_LINE = "the automatic-transmission-fluid schedule line p.7-10 reads 'No check, No service required'; "
IVT_LINE = "the variable-transmission-fluid schedule line p.7-10 reads 'No check, No service required'; "
INSPECT = "brake / clutch fluid carries inspection marks only; "
CABIN12 = "the climate control air filter is printed 'Replace every 12 Months' with no mileage; "

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=38737, label="2018 HC  Gamma 1.6 GDI", oil=OIL_GAMMA, trans=AT, brake=BRAKE_34,
      maint=maint(7500, (7500, 12), None, False),
      src=src(2018, "'2018 Accent Owners Manual.pdf'", NO_TITLE + ", Copyright 2018 HYUNDAI Motor America, PDF created "
              "2018-02-20, 442 pp", GAMMA, "3-17", AT_LINE + INSPECT),
      msrc="Hyundai Owner's Manual (Accent 2018 HC, p.%s)"),
 dict(vid=38738, label="2019 HC  Gamma 1.6 GDI", oil=OIL_GAMMA, trans=AT, brake=BRAKE_34,
      maint=maint(7500, (7500, 12), None, False),
      src=src(2019, "'2019 Accent OM.pdf'", NO_TITLE + ", Copyright 2018 HYUNDAI Motor America, PDF created 2018-08-01, "
              "442 pp, its own edition (21 pages revised from the 2018 file)", GAMMA, "3-17",
              "the specification and schedule pages are token-identical to the 2018 book's; " + AT_LINE + INSPECT),
      msrc="Hyundai Owner's Manual (Accent 2019 HC, p.%s)"),
 dict(vid=38739, label="2020 HC  Smartstream G1.6", oil=OIL_2020, trans=IVT, brake=BRAKE_34,
      maint=maint(7500, (None, 12), None, False),
      src=src(2020, "'2020 Accent Owner's Manual.pdf'", "PDF title '2020 Accent Owner's Manual' and the cover names the "
              "year and the Accent, Copyright 2019 HYUNDAI Motor America, PDF created 2019-06-07, 445 pp", SMART, "3-17",
              IVT_LINE + INSPECT + CABIN12),
      msrc="Hyundai Owner's Manual (Accent 2020 HC, p.%s)"),
 dict(vid=38740, label="2021 HC  Smartstream G1.6", oil=OIL_GF6, trans=IVT, brake=BRAKE_4,
      maint=maint(8000, (None, 12), None, True),
      src=src(2021, "'2021 Accent OM.pdf'", NO_TITLE + ", Copyright 2020 HYUNDAI Motor America, proof marks 'HCa HMA' "
              "dated 5/25/2020, PDF created 2020-09-01, 443 pp", SMART, "3-18",
              IVT_LINE + CABIN12 + "the books require API SN PLUS or above for the normal oil interval and print no "
              "'full synthetic' wording, so the oil type is left empty; "),
      msrc="Hyundai Owner's Manual (Accent 2021 HC, p.%s)"),
 dict(vid=38741, label="2022 HC  Smartstream G1.6", oil=OIL_GF6, trans=IVT, brake=BRAKE_4,
      maint=maint(8000, (None, 12), 12, True),
      src=src(2022, "2022-Accent-OM.pdf", NO_TITLE + ", Copyright 2021 HYUNDAI Motor America, PDF created 2021-07-06, 445 "
              "pp", SMART, "3-18",
              IVT_LINE + CABIN12 + "tire rotation is printed as a mark in every 8,000-mile / 12-month column; the book "
              "still lists a manual transmission fluid, written as printed; the book requires API SN PLUS or above for "
              "the normal oil interval and prints no 'full synthetic' wording, so the oil type is left empty; "),
      msrc="Hyundai Owner's Manual (Accent 2022 HC, p.%s)"),
]
assert sorted(r["vid"] for r in ROWS) == sorted(TARGETS), "this script writes the five Accent rows of slice 3 and nothing else"

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
    o = row["oil"]
    assert VEHICLES.get(vid) == (year, "Hyundai", "Accent") and TARGETS.get(vid) == year, (vid, "target row is not the labelled vehicle")
    assert ("per %d Hyundai Accent OM" % year) in row["src"] and ("Accent %d " % year) in row["msrc"], (vid, "source year")
    assert ("Gamma 1.6 GDI" in row["src"]) == (year <= 2019) and ("Smartstream G1.6" in row["src"]) == (year >= 2020), (vid, "engine per year")
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    assert len(row["maint"]) == (7 if year >= 2021 else 6), (vid, "schedule lines", len(row["maint"]))
    for mi, mo, desc, page in row["maint"]:
        assert re.fullmatch(r"7-\d{1,2}", page), (vid, desc, page)
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert (mi is None or (isinstance(mi, int) and mi > 0)) and (mo is None or (isinstance(mo, int) and mo > 0)), (vid, desc)
        assert mi is not None or mo is not None, (vid, desc, "a row needs at least one interval")
    by = {d: (mi, mo) for mi, mo, d, _ in row["maint"]}
    assert len(by) == len(row["maint"]), (vid, "duplicate schedule description")
    step = 8000 if year >= 2021 else 7500                       # the schedule step changes with the 2021 book
    assert by["Engine oil & filter change"] == (step, 12), vid
    assert by["Spark plug replacement"] == ((96000 if year >= 2021 else 97500), None), (vid, by["Spark plug replacement"])
    assert by["Engine air cleaner filter replacement"] == ((24000 if year >= 2021 else 22500), 36), vid
    assert by["Tire rotation"] == (step, 12 if year == 2022 else None), (vid, by["Tire rotation"])
    assert by[CABIN_ROW] == ((7500, 12) if year <= 2019 else (None, 12)), (vid, by[CABIN_ROW])
    assert by[COOLANT_ROW] == (120000, 120), vid
    assert ("Brake fluid replacement" in by) == (year >= 2021), (vid, "brake-fluid replacement line belongs to 2021 / 2022")
    assert not any("transmission" in d.lower() for d in by), (vid, "no transmission-fluid row in any year")
    # values that change between the years
    assert (o["cap"] == "3.49 qt / 3.3 L") == (year <= 2019) and (o["cap"] == "4.02 qt / 3.8 L") == (year >= 2020), (vid, o["cap"])
    assert ("ATF SP-IV" in row["trans"]) == (year <= 2019) and ("SP-CVT1" in row["trans"]) == (year >= 2020), (vid, row["trans"])
    assert (o["visc"] == "0W-20") == (year >= 2021) and ("5W-20 (recommended" in o["visc"]) == (year <= 2019), (vid, o["visc"])
    assert (row["brake"] == BRAKE_4) == (year >= 2021) and (row["brake"] == BRAKE_34) == (year <= 2020), (vid, row["brake"])
    assert o["type"] is None and MT in row["trans"], vid
    shipped = [o["visc"], o["cap"], o["spec"], row["trans"], row["brake"], COOL, COOL_CAP, EPS, TIRES, NOTE, LUG_NOTE] + list(by)
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
    vid, o = row["vid"], row["oil"]
    for t in TABLES:
        c.execute("DELETE FROM %s WHERE vehicle_id=?" % t, (vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,"
              "filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, o["visc"], o["type"], o["cap"], None, o["spec"], None, None, None, None, None, row["src"]))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,"
              "coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
              (vid, row["trans"], None, row["brake"], COOL, COOL_CAP, EPS, None, row["src"]))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,"
              "tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,"
              "wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,"
              "real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, None, None, None, None, None, TIRES, 33, 33, None, None, None, None, None, NOTE, None, None, None, None,
               None, row["src"]))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
              (vid, "lug_nut", 79.0, 107.0, LUG_NOTE, row["src"]))
    for mi, mo, desc, page in row["maint"]:
        c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,"
                  "difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (nid, vid, mi, mo, desc, row["msrc"] % page, "standard", None, None, None))
        nid += 1
    return nid

def show(row):
    o = row["oil"]
    print("\n=== %d  Accent %s" % (row["vid"], row["label"]))
    print("  oil   : %s | %s | %s" % (o["cap"], o["visc"], o["spec"]))
    print("  trans : %s" % row["trans"])
    print("  cool  : %s | %s" % (COOL_CAP, COOL))
    print("  brake : %s | steering: %s" % (row["brake"], EPS))
    print("  tires : %s @ 33 psi | %s" % (TIRES, NOTE))
    print("  lug   : 79.0 lb-ft / 107.0 N-m | %s" % LUG_NOTE)
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7s mi / %4s mo  %s  [p.%s]" % (mi if mi else "--", mo if mo else "--", desc, page))
    print("  src   : %s" % row["src"])

# ---------------------------------------------------------------------------------------------------------------
npairs = sum(check(row) for row in ROWS)
print("contract checks PASS: %d vehicles, %d maintenance rows, %d printed unit pairs converted; every source classified "
      "verified with a suffix; every target id is the labelled vehicle"
      % (len(ROWS), sum(len(r["maint"]) for r in ROWS), npairs))
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

bak = DB + ".bak_accent_2018_2022_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
    o = c.execute("SELECT capacity_with_filter, oil_type, source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchall()
    f = c.execute("SELECT coolant_capacity, transmission_capacity, differential_fluids_json, brake_fluid, transmission_fluid FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, tire_pressure_rear, battery_group, battery_notes, spark_plug_type FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT component, torque_ft_lbs, source, torque_nm FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), SUM(mileage_interval IS NULL) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and e == 0, vid
    assert o[0][1] is None and f[0][0] == COOL_CAP and f[0][1] is None and f[0][2] is None and p[0][3] is None and p[0][4] is None and p[0][5] is None, vid
    assert t[0][2].startswith(BARE + " (") and classify(t[0][2], "torque_specs", vid) == 1 and t[0][3] == 107.0
    for tb in ("oil_change", "fluids", "parts", "maintenance", "torque_specs"):
        for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)):
            assert classify(s, tb, vid) == 1, (vid, tb, s[:60])
    g = [c.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id=?" % tb, (vid,)).fetchone()[0]
         for tb in ("fuel_economy", "recalls", "safety_ratings", "complaints")]
    print("  %d: oil=%s | trans=%s | brake=%s | tire=%s @%s | lug=%s / %s | maint=%d (months-only %d) | government rows %s"
          % (vid, o[0][0], "SP-IV" if "SP-IV" in f[0][4] else "SP-CVT1", f[0][3][:12], p[0][0], p[0][1], t[0][1], t[0][3], m[0], m[1], g))
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare_count(c))
db.close()
print("DONE - %d rows written." % len(ROWS))
