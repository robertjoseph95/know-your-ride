# Hyundai Accent 2005 / 2006 / 2008 - curated specs for three of the model-year rows added by _add_hyundai_rows.py
# (missing-year step B, slice 1 of 3). Ids 38731 (2005, LC), 38732 (2006, MC), 38733 (2008, MC). No curated rows before.
# Sources (manufacturer, free, citable), saved under _hyundai_manuals/accent/ (gitignored); reads 2026-11-14:
#   2005  US portal 2005_Hyundai_Accent_OM.pdf - cover '2005 Owner's Manual' + Accent, Copyright 2005, 219 pp
#   2006  US portal 2006_Hyundai_Accent_OM.pdf - cover '2006 Owner's Manual' + ACCENT, Copyright 2006, 278 pp
#   2008  US portal 2008_Hyundai_Accent_OM.pdf - cover '2008 Owner's Manual' + ACCENT, Copyright 2008, 273 pp
#   Single prints: the second host serves no Accent, so there is no second print to compare.
#   Each book was identified by its cover (page render), the engine table p.9-3 (1.6 MPI, 1,599 cc, '4-Cylinder
#   in-line DOHC') and the measurements p.9-2 (wheel base 96.1 in for 2005, 98.4 in for 2006 / 2008; 4 door + 3 door).
# ** Rulings 2026-11-14 ("Go, as recommended"), reasons live HERE and in the source suffix only:
#    VISCOSITY, a book against itself (2005, 2006): the drawn chart p.6-4 prints '5W-20, 5W-30' and the lubrication
#       chart p.9-4 prints 'SAE 5W-20, 20W-30'; both print 10W-30 above 0 F. Written: only the grades BOTH places
#       name - 5W-20, and 10W-30 above 0 F. The 2008 book prints 5W-30 in both places, so 2008 carries all three.
#    CLASSIFICATION (2005): the engine table p.9-3 prints 'Oil grade (API) SH, SG or SG/CD and ABOVE'; p.9-4 and
#       p.6-4 print 'API SJ, SL or ABOVE, ILSAC GF-3 or ABOVE'. Written: the second, which also satisfies the first.
#    NEW SCHEDULE ROW TYPES: fuel filter and fuel tank air filter are printed replacement rows in the normal
#       schedule -> written. Automatic transaxle fluid (one 'R' mark, at 105,000 miles / 84 months) is written under
#       the Santa Cruz ruling of the same day (a printed normal-schedule replacement interval is a row).
#    2005 ENGINE LABEL: the 2005 book covers the 1.6 MPI only while EPA also lists a 1.5 L for the model year, so the
#       2005 engine values are marked '(1.6 MPI)'.
# ** Not written: tire rotation ('every 7,500 miles' is printed in chapter 8, outside the schedule - as on the Santa Fe
#    2005 / 2006 and Sonata 2006 rows); brake fluid and manual transaxle oil have inspection marks only.
# ** Gates (null): spark-plug type and gap for 2006 / 2008 (not published; the 2005 book publishes both p.9-3);
#    12V battery for 2008 (not published); power-steering and brake-fluid quantities printed 'As required';
#    wheel nut torque in N-m (the books print lb-ft and kg-cm only -> torque_nm NULL, as on Santa Fe 2005 / 2006).
# ** Front-wheel drive: no differential entry (differential_fluids_json NULL, as on Sonata 2006).
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows (checked BEFORE
#    commit). S1.12: no bookkeeping words in shipped columns; battery_notes NULL.
#
# Usage:  python _write_hyundai_accent_2005_2008.py            -> DRY RUN: print every row, classify every source
#         python _write_hyundai_accent_2005_2008.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
import sqlite3, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
# the misprinted grade and the older classification line (rulings): never in a shipped column
NOT_WRITTEN = re.compile(r"20W-30|\bSH\b|SG/CD")
TABLES = ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]
TARGETS = {38731: 2005, 38732: 2006, 38733: 2008}

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Accent'")}
_c.close()
assert sorted(v for v in VEHICLES if v > 0) == list(range(38731, 38742)), ("the Accent rows are not the eleven expected", sorted(VEHICLES))
for _vid, _year in TARGETS.items():
    assert VEHICLES[_vid] == (_year, "Hyundai", "Accent"), (_vid, VEHICLES[_vid])

E16 = "1.6 MPI"
COOL = "Ethylene glycol base coolant for aluminum radiator"
BRAKE = "DOT 3, DOT 4 or equivalent"
ATF = "ATF SP-III (Hyundai genuine, Diamond or SK ATF SP-III, or other brands approved by Hyundai)"
MTF = "Hyundai genuine MTF 75W/85 (API GL-4)"
OIL_CLASS = "API SJ, SL or above; ILSAC GF-3 or above"
LUG_NOTE = ("65 to 80 lb-ft (900 to 1,100 kg-cm), wheel nut tightening torque per owner manual (range), steel and "
            "aluminium alloy wheels")
PORTAL = "owners.hyundaiusa.com glovebox-manual"
COOLANT_ROW = "Engine coolant first replacement; thereafter every 30,000 mi / 24 months"
ATF_ROW = "Automatic transaxle fluid replacement"
MC_TIRES = "P175/70R14, P185/65R14, P195/55R15 or P205/45R16"

def trans(mt_qty, at_qty):
    return ("Manual transaxle: " + MTF + ", " + mt_qty + ". Automatic transaxle: " + ATF + ", " + at_qty + ".")

def mc_maint():
    return [
        (7500, 6, "Engine oil & filter change", "5-4"),
        (30000, 24, "Spark plug replacement", "5-4"),
        (30000, 24, "Engine air cleaner filter replacement", "5-4"),
        (52500, 42, "Fuel filter replacement", "5-4"),
        (30000, 24, "Fuel tank air filter replacement", "5-4"),
        (10000, 12, "Climate control (cabin) air filter replacement", "5-5"),
        (60000, 60, COOLANT_ROW, "5-5"),
        (60000, 48, "Timing belt replacement", "5-5"),
        (105000, 84, ATF_ROW, "5-5"),
    ]

MC_ID = ("MC, self-ID engine table p.9-3 1.6 MPI 1,599cc '4-Cylinder in-line DOHC', wheel base 98.4 in and 4 door / 3 "
         "door bodies p.9-2; tires and fuel tank p.9-2; lubrication chart p.9-4; recommended-oil chart p.6-4 read from "
         "a page render; schedule p.5-4 / 5-5, grids read from page renders (the automatic-transaxle-fluid row has one "
         "replace mark, at 105,000 miles / 84 months)")
COMMON_GATES = ("wheel nut torque in N-m (not printed; lb-ft and kg-cm only), tire rotation (printed in chapter 8, "
                "outside the schedule), battery notes")

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=38731, label="2005 LC  " + E16, psi=30,
  oil=dict(visc="5W-20 (all temperatures); 10W-30 above 0 F (-18 C) (" + E16 + ")", type=None,
           cap="3.49 qt / 3.3 L (" + E16 + ")", cap_wo="3.16 qt / 3.0 L (" + E16 + ")", spec=OIL_CLASS + " (" + E16 + ")"),
  fluids=dict(trans=trans("2.27 qt / 2.15 L", "6.45 qt / 6.1 L"), brake=BRAKE, cool_type=COOL,
              cool_cap="6.2 qt / 5.88 L (" + E16 + ", manual transaxle) / 5.8 qt / 5.48 L (" + E16 + ", automatic transaxle)",
              ps="Hydraulic power steering - PSF-3 type fluid, 0.95 qt / 0.9 L"),
  parts=dict(plug="NGK BKR5ES-11 or Champion RC10YC4 (" + E16 + ")", gap="0.039 to 0.043 in (1.0 to 1.1 mm)",
             batt="MF12V, 55AH", tire="P175/70R13 or P185/60R14",
             note="Standard tire P175/70R13; optional P185/60R14; 30 psi. Spare tire T105/70D(R)14 at 60 psi. "
                  "Fuel tank 11.9 gal / 45 L."),
  src="owner-manual-verified (per 2005 Hyundai Accent OM, portal file 2005_Hyundai_Accent_OM.pdf = "
      "accent_2005_portal_OM.pdf, " + PORTAL + ", cover '2005 Owner's Manual' with the Accent name (page render), "
      "Copyright 2005 Hyundai Motor Company, single print (the second manufacturer host serves no Accent); LC, self-ID "
      "engine table p.9-3 1.6 MPI 1,599cc '4-Cylinder in-line DOHC', wheel base 96.1 in and 4 door / 3 door bodies "
      "p.9-2; tires, battery and fuel tank p.9-2; spark plug and gap p.9-3; lubrication chart p.9-4; recommended-oil "
      "chart p.6-4 read from a page render; wheel nut torque p.3-12; schedule p.5-4 / 5-5, grids read from page "
      "renders (the automatic-transaxle-fluid row has one replace mark, at 105,000 miles / 84 months); the book "
      "covers the 1.6 MPI only while EPA also lists a 1.5 L for this model year, so engine values are marked 1.6 MPI "
      "(ruling 2026-11-14); viscosity: the chart p.6-4 prints '5W-20, 5W-30' and the lubrication chart p.9-4 prints "
      "'5W-20' with a different second grade, both print 10W-30 above 0 F - written: the grades both places name "
      "(ruling 2026-11-14); classification: the engine table p.9-3 prints an older API line, p.9-4 and p.6-4 print 'API "
      "SJ, SL or ABOVE, ILSAC GF-3 or ABOVE' - written: the latter, which satisfies both (ruling 2026-11-14); gated to "
      "null: brake-fluid quantity (printed 'As required'), " + COMMON_GATES + ")",
  msrc="Hyundai Owner's Manual (Accent 2005 LC, p.%s)",
  maint=[
   (7500, 6, "Engine oil & filter change (" + E16 + ")", "5-4"),
   (30000, 24, "Spark plug replacement (" + E16 + ")", "5-4"),
   (30000, 24, "Engine air cleaner filter replacement (" + E16 + ")", "5-4"),
   (52500, 42, "Fuel filter replacement (" + E16 + ")", "5-4"),
   (30000, 24, "Fuel tank air filter replacement (" + E16 + ")", "5-4"),
   (12000, 12, "Air conditioner (cabin) filter replacement", "5-5"),
   (60000, 60, COOLANT_ROW + " (" + E16 + ")", "5-5"),
   (60000, 48, "Timing belt replacement (" + E16 + ")", "5-5"),
   (105000, 84, ATF_ROW, "5-5"),
  ]),

 dict(vid=38732, label="2006 MC  " + E16, psi=30,
  oil=dict(visc="5W-20 (all temperatures); 10W-30 above 0 F (-18 C)", type=None,
           cap="3.48 qt / 3.3 L", cap_wo="3.17 qt / 3.0 L", spec=OIL_CLASS),
  fluids=dict(trans=trans("2 qt / 1.9 L", "6.44 qt / 6.1 L"), brake=BRAKE, cool_type=COOL,
              cool_cap="5.49 qt / 5.2 L (manual transaxle) / 5.60 qt / 5.3 L (automatic transaxle)",
              ps="Hydraulic power steering - PSF-3 type fluid"),
  parts=dict(plug=None, gap=None, batt="MF 55AH", tire=MC_TIRES,
             note="4-door: P175/70R14, P185/65R14 or P195/55R15; 3-door: P175/70R14, P185/65R14 or P205/45R16; 30 psi. "
                  "Spare tire T115/70D15 at 60 psi. Fuel tank 11.9 gal / 45 L."),
  src="owner-manual-verified (per 2006 Hyundai Accent OM, portal file 2006_Hyundai_Accent_OM.pdf = "
      "accent_2006_portal_OM.pdf, " + PORTAL + ", cover '2006 Owner's Manual' with the ACCENT name (page render), "
      "Copyright 2006 Hyundai Motor Company, PDF created 2006-01-24, single print (the second manufacturer host serves "
      "no Accent); " + MC_ID + "; battery p.9-2; wheel nut torque p.3-12; viscosity: the chart p.6-4 prints '5W-20, "
      "5W-30' and the lubrication chart p.9-4 prints '5W-20' with a different second grade, both print 10W-30 above 0 "
      "F - written: the grades both places name (ruling 2026-11-14); gated to null: spark-plug part number and gap "
      "(not published), power-steering fluid and brake-fluid quantities (printed 'As required'), " + COMMON_GATES + ")",
  msrc="Hyundai Owner's Manual (Accent 2006 MC, p.%s)",
  maint=mc_maint()),

 dict(vid=38733, label="2008 MC  " + E16, psi=None,
  oil=dict(visc="5W-20 or 5W-30 (all temperatures); 10W-30 above 0 F (-18 C)", type=None,
           cap="3.48 qt / 3.3 L", cap_wo="3.17 qt / 3.0 L", spec=OIL_CLASS),
  fluids=dict(trans=trans("2 qt / 1.9 L", "6.44 qt / 6.1 L"), brake=BRAKE, cool_type=COOL,
              cool_cap="5.49 qt / 5.2 L (manual transaxle) / 5.60 qt / 5.3 L (automatic transaxle)",
              ps="Hydraulic power steering - PSF-3 type fluid"),
  parts=dict(plug=None, gap=None, batt=None, tire=MC_TIRES,
             note="4-door: P175/70R14, P185/65R14 or P195/55R15 at 30 psi; 3-door: P175/70R14 or P185/65R14 at 30 psi, "
                  "P205/45R16 at 32 psi. Spare tire T115/70D15 at 60 psi. Fuel tank 11.9 gal / 45 L."),
  src="owner-manual-verified (per 2008 Hyundai Accent OM, portal file 2008_Hyundai_Accent_OM.pdf = "
      "accent_2008_portal_OM.pdf, " + PORTAL + ", cover '2008 Owner's Manual' with the ACCENT name (page render), "
      "Copyright 2008 Hyundai Motor Company, single print (the second manufacturer host serves no Accent); " + MC_ID
      + "; wheel nut torque p.3-16; the chart p.6-4 and the lubrication chart p.9-4 agree on the oil grades; tire "
      "pressure differs by size (p.9-2), so it is given in the note; gated to null: spark-plug part number and gap "
      "(not published), 12V battery (not published), power-steering fluid and brake-fluid quantities (printed 'As "
      "required'), " + COMMON_GATES + ")",
  msrc="Hyundai Owner's Manual (Accent 2008 MC, p.%s)",
  maint=mc_maint()),
]
assert sorted(r["vid"] for r in ROWS) == sorted(TARGETS), "this script writes the three Accent rows of slice 1 and nothing else"

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
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    assert len(row["maint"]) == 9, (vid, "schedule lines", len(row["maint"]))
    for mi, mo, desc, page in row["maint"]:
        assert page in ("5-4", "5-5"), (vid, desc, page)
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert isinstance(mi, int) and mi > 0 and isinstance(mo, int) and mo > 0, (vid, desc)
    by = {re.sub(r" \(1\.6 MPI\)$", "", d): (mi, mo) for mi, mo, d, _ in row["maint"]}
    assert len(by) == 9, (vid, "duplicate schedule description")
    assert by["Engine oil & filter change"] == (7500, 6) and by["Spark plug replacement"] == (30000, 24), vid
    assert by["Fuel filter replacement"] == (52500, 42) and by["Fuel tank air filter replacement"] == (30000, 24), vid
    assert by["Timing belt replacement"] == (60000, 48) and by[ATF_ROW] == (105000, 84) and by[COOLANT_ROW] == (60000, 60), vid
    cabin = [(d, v) for d, v in by.items() if "cabin" in d]
    assert cabin == [(("Air conditioner (cabin) filter replacement", (12000, 12)) if year == 2005 else
                      ("Climate control (cabin) air filter replacement", (10000, 12)))], (vid, cabin)
    o, f, p = row["oil"], row["fluids"], row["parts"]
    # rulings: 5W-30 only where chart and table agree (2008); the 2005 values carry the engine name
    assert ("5W-30" in o["visc"]) == (year == 2008) and "5W-20" in o["visc"] and "10W-30 above 0 F (-18 C)" in o["visc"], (vid, o["visc"])
    labelled = [o["visc"], o["cap"], o["cap_wo"], o["spec"], f["cool_cap"]]
    assert all(("(" + E16 in s) == (year == 2005) for s in labelled), (vid, "1.6 MPI label belongs to 2005 only")
    assert o["spec"].startswith(OIL_CLASS), vid
    assert (p["plug"] is not None and p["gap"] is not None) == (year == 2005), (vid, "spark plug is published by the 2005 book only")
    assert p["batt"] == {2005: "MF12V, 55AH", 2006: "MF 55AH", 2008: None}[year], (vid, p["batt"])
    assert ("0.95 qt / 0.9 L" in f["ps"]) == (year == 2005), (vid, "power-steering quantity is printed in 2005 only")
    assert (row["psi"] is None and "32 psi" in p["note"]) if year == 2008 else (row["psi"] == 30 and "32 psi" not in p["note"]), vid
    shipped = [o["visc"], o["cap"], o["cap_wo"], o["spec"], f["trans"], f["brake"], f["cool_type"], f["cool_cap"], f["ps"],
               p["plug"], p["gap"], p["batt"], p["tire"], p["note"], LUG_NOTE] + [d for _, _, d, _ in row["maint"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
            assert not NOT_WRITTEN.search(s), (vid, "a value left out by ruling is in a shipped column", s)
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
    vid, o, f, p = row["vid"], row["oil"], row["fluids"], row["parts"]
    for t in TABLES:
        c.execute("DELETE FROM %s WHERE vehicle_id=?" % t, (vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,"
              "filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, o["visc"], o["type"], o["cap"], o["cap_wo"], o["spec"], None, None, None, None, None, row["src"]))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,"
              "coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
              (vid, f["trans"], None, f["brake"], f["cool_type"], f["cool_cap"], f["ps"], None, row["src"]))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,"
              "tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,"
              "wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,"
              "real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, p["plug"], p["gap"], None, p["batt"], None, p["tire"], row["psi"], row["psi"], None, None, None, None,
               None, p["note"], None, None, None, None, None, row["src"]))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
              (vid, "lug_nut", 65.0, None, LUG_NOTE, row["src"]))
    for mi, mo, desc, page in row["maint"]:
        c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,"
                  "difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (nid, vid, mi, mo, desc, row["msrc"] % page, "standard", None, None, None))
        nid += 1
    return nid

def show(row):
    o, f, p = row["oil"], row["fluids"], row["parts"]
    print("\n=== %d  Accent %s" % (row["vid"], row["label"]))
    print("  oil   : with filter %s | without %s | %s" % (o["cap"], o["cap_wo"], o["visc"]))
    print("  spec  : %s" % o["spec"])
    print("  trans : %s" % f["trans"])
    print("  cool  : %s | %s" % (f["cool_cap"], f["cool_type"]))
    print("  brake : %s | steering: %s" % (f["brake"], f["ps"]))
    print("  plug  : %s | gap %s | battery %s" % (p["plug"], p["gap"], p["batt"]))
    print("  tires : %s @ %s psi | %s" % (p["tire"], row["psi"] if row["psi"] else "per size (see note)", p["note"]))
    print("  lug   : 65.0 lb-ft / None N-m | %s" % LUG_NOTE)
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7d mi / %3d mo  %s  [p.%s]" % (mi, mo, desc, page))
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

bak = DB + ".bak_accent_2005_2008_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
    f = c.execute("SELECT coolant_capacity, transmission_capacity, differential_fluids_json, brake_fluid FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, tire_pressure_rear, battery_group, battery_notes, spark_plug_type FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT component, torque_ft_lbs, source, torque_nm FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), MIN(source) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and e == 0, vid
    assert f[0][1] is None and f[0][2] is None and p[0][4] is None and p[0][3] == row["parts"]["batt"] and p[0][5] == row["parts"]["plug"], vid
    assert t[0][2].startswith(BARE + " (") and classify(t[0][2], "torque_specs", vid) == 1 and t[0][3] is None
    for tb in ("oil_change", "fluids", "parts", "maintenance", "torque_specs"):
        for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)):
            assert classify(s, tb, vid) == 1, (vid, tb, s[:60])
    g = [c.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id=?" % tb, (vid,)).fetchone()[0]
         for tb in ("fuel_economy", "recalls", "safety_ratings", "complaints")]
    print("  %d: oil=%s / %s | cool=%s | tire=%s @%s | lug=%s | battery=%s | maint=%d | government rows %s"
          % (vid, o[0][0], o[0][1], f[0][0][:34], p[0][0][:26], p[0][1], t[0][1], p[0][3], m[0], g))
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare_count(c))
db.close()
print("DONE - %d rows written." % len(ROWS))
