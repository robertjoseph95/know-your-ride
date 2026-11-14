# Hyundai Veloster (JS) and Santa Cruz (NX4OB) - TENTH Hyundai slice. 3 model years written, 1 deferred.
# Written:  Veloster 2019 (id 38641), Veloster 2021 (id 38683), Santa Cruz 2026 (id 9981).
# Deferred: Veloster 2020 (id 38682) - no manufacturer owner's manual is available: the US portal answers HTTP 404 for
#           81 filename forms across seven folder spellings and the second manufacturer host carries no Veloster book.
#           The row is NOT touched by this script.
# The three written ids held only blacklisted-source rows (unsourced placeholders / scraped), which never shipped.
# Source: Hyundai owner's manuals (manufacturer, free, citable), saved under _hyundai_manuals/{veloster,santa_cruz}/
#   (gitignored); reads 2026-11-14.
#     Veloster   US portal owners.hyundaiusa.com .../glovebox-manual/<YEAR>/veloster/<file> - one print per year.
#     Santa Cruz second host ownersmanual.hyundai.com full_pdf NX4OB 2026 en_US - served by the host but absent from
#                its US menu (the menu lists NX4OB labels 2021-2024); the portal has nothing for 2025 / 2026.
# ** MODEL YEAR OF THE SANTA CRUZ BOOK: NHTSA vPIC lists a Santa Cruz for both 2026 and 2027, so the label was tested.
#    The host files 2027-model-year books under their own 2027 label (SX2, LX3, MX5a, DN8) and none exists for NX4OB;
#    it keeps updating 2026 labels in place after a 2027 book appears; and this book says AWD where the 2025-label
#    book says 4WD, the change the Tucson books show between 2025 and 2026. Read as a later print of model year 2026.
#    (The EARLY NX4OB labels are shifted: label 2021 is the model-year-2022 book. No row depends on them.)
# ** Each row comes from ONE print, so there is no second print to compare. All 17 printed unit pairs convert.
# ** Rulings 2026-11-14 ("Accept, go read" / "Go, write"): the unlisted NX4OB/2026 book is the Santa Cruz source;
#    both Veloster engines are written as printed, each labelled (the DB engine label '1.6L Turbo' is left as it is);
#    Veloster 2020 is deferred; the 36 psi figure the Veloster books print for driving over 100 mph is not carried.
# ** Gates (null): spark-plug part number / gap (not published); 12V battery (Veloster: not published; Santa Cruz:
#    capacity-label illustration only); EPS / MDPS has no fluid; Veloster N has its own manual.
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows (checked BEFORE
#    commit). S1.12 / S1.11: no bookkeeping words in shipped columns; battery_notes NULL; diff JSON = [{location,
#    fluid_type}].
#
# Usage:  python _write_hyundai_veloster_santa_cruz.py            -> DRY RUN: print every row, write nothing
#         python _write_hyundai_veloster_santa_cruz.py --write    -> backup DB, DELETE the 6 curated tables per id,
#                                                                    INSERT, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
TABLES = ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]
DEFERRED = 38682                                                               # Veloster 2020 - never written here

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute(
    "SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model IN ('Veloster','Santa Cruz')")}
_c.close()
assert sorted(VEHICLES) == [9981, 38641, 38682, 38683], ("unexpected Veloster / Santa Cruz rows", sorted(VEHICLES))

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_PHOS = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
COOL_EG = "Mixture of antifreeze and water; ethylene glycol base coolant for aluminum radiator"
BRAKE_LV = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
LUG = dict(ftlb=79.0, nm=107.0,
           note="79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)")
SYN = "Full synthetic (required)"
NO_PLUG = "spark-plug part number and gap (not published, interval only), battery notes"

def diff(*pairs):
    return json.dumps([{"location": loc, "fluid_type": fl} for loc, fl in pairs], ensure_ascii=False)

# ---- Veloster JS (2019 / 2021): the two books agree on every spec page read except the brake-fluid specification ----
T16, N20 = "Gamma 1.6 T-GDI", "Nu 2.0 MPI"
VEL_OIL = dict(visc="5W-30 (" + T16 + ") / 5W-20 (" + N20 + ")", type=None,
               cap="4.76 qt / 4.5 L (" + T16 + ") / 4.23 qt / 4.0 L (" + N20 + ")", cap_wo=None,
               spec=T16 + ": ACEA A5/B5; SAE 5W-30 recommended, chart also allows 5W-40 / 10W-30 / 15W-40 / 20W-50 by "
                    "temperature. " + N20 + ": API SM and ILSAC GF-4 (or above), ACEA A5/B5; SAE 5W-20 recommended, chart "
                    "also allows 5W-30 / 10W-30 by temperature.")
VEL_TRANS = ("Manual transmission: API GL-4 SAE 70W TGO-9 manual transmission fluid (HK SYN MTF 70W, SPIRAX S6 GHME 70W MTF "
             "or GS MTF HD 70W), 1.8-1.9 qt / 1.7-1.8 L. Automatic transmission (" + N20 + "): ATF SP-IV (MICHANG, SK, NOCA, "
             "Hyundai genuine or other approved brands meeting the spec), 7.08 qt / 6.7 L. Dual clutch transmission ("
             + T16 + "): API GL-4 SAE 70W dual clutch transmission fluid (HK SYN DCTF 70W, SPIRAX S6 GHME 70W DCTF or GS "
             "DCTF HD 70W), 2.01-2.11 qt / 1.9-2.0 L.")
def vel_fluids(brake):
    return dict(trans=VEL_TRANS, brake=brake + "; 0.74-0.85 qt / 0.7-0.8 L", cool_type=COOL_PHOS,
                cool_cap="7.5 qt / 7.1 L (" + T16 + ") / 6.8 qt / 6.5 L (" + N20 + ")", ps=EPS, diff=None)
VEL_PARTS = dict(tire="215/45R17, 225/40R18 or 225/40ZR18",
                 note="17-in wheels: 215/45R17; 18-in wheels: 225/40R18 or 225/40ZR18; 33 psi front and rear at normal and "
                      "maximum load. Compact spare (if equipped) T125/80D16 at 60 psi. Fuel tank 13.2 gal / 50 L.")
VEL_MAINT = [
    (7500, 12, "Engine oil & filter change (" + N20 + ")", "7-8"),
    (6000, 12, "Engine oil & filter change (" + T16 + ")", "7-13"),
    (97500, None, "Spark plug replacement (" + N20 + ")", "7-8"),
    (42000, None, "Spark plug replacement (" + T16 + ")", "7-13"),
    (30000, 48, "Engine air cleaner filter replacement (" + N20 + ")", "7-8"),
    (24000, 48, "Engine air cleaner filter replacement (" + T16 + ")", "7-13"),
    (15000, 12, "Climate control (cabin) air filter replacement (" + N20 + ")", "7-8"),
    (12000, 12, "Climate control (cabin) air filter replacement (" + T16 + ")", "7-13"),
    (6200, None, "Tire rotation", "7-8, 7-13"),
    (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-8, 7-13"),
]
VEL_ID = ("JS, self-ID p.8-2 Gamma 1.6 T-GDI 1,591cc + Nu 2.0 MPI 1,999cc, wheelbase 104.33 in, overall length 166.93 in, "
          "Veloster body on the exterior overview p.1-2 (image code OJS018001N); capacities p.8-7 / 8-8, viscosity chart "
          "p.8-9 read from a page render, tires + wheel lug nut torque p.8-4; the text is glyph-coded and was decoded; "
          "schedule printed per engine (Nu 2.0 MPI p.7-8 to 7-10, Gamma 1.6 T-GDI p.7-13 to 7-15) and tire rotation is "
          "printed as 6,200 miles in both; the book also prints 36 psi for driving over 100 mph, which is not carried; "
          "single available print (the second manufacturer host carries no Veloster book); Veloster N has its own manual")
VEL_GATES = "gated to null: 12V battery group and CCA (not published), " + NO_PLUG

# ---- Santa Cruz NX4OB (2026) --------------------------------------------------------------------------------------
G25, G25T = "Smartstream G2.5 GDI", "Smartstream G2.5 T-GDI"

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=38641, model="Veloster", label="2019 JS  " + T16 + " + " + N20, psi_f=33, psi_r=33, lug=LUG,
  oil=VEL_OIL, fluids=vel_fluids("FMVSS 116 DOT-3 or DOT-4"), parts=VEL_PARTS,
  src="owner-manual-verified (per 2019 Hyundai Veloster OM, portal file '2019 Veloster OM.pdf' = "
      "veloster_2019_portal_OM.pdf, owners.hyundaiusa.com glovebox-manual folder 2019/veloster, Copyright 2018 HYUNDAI "
      "Motor America, PDF created 2018-08-01 (no title metadata; the JS generation began with model year 2019); "
      + VEL_ID + "; brake fluid is inspect-only in this year's schedule; " + VEL_GATES + ")",
  msrc="Hyundai Owner's Manual (Veloster 2019 JS, p.%s)",
  maint=VEL_MAINT),

 dict(vid=38683, model="Veloster", label="2021 JS  " + T16 + " + " + N20, psi_f=33, psi_r=33, lug=LUG,
  oil=VEL_OIL, fluids=vel_fluids("DOT-4 (" + BRAKE_LV + ")"), parts=VEL_PARTS,
  src="owner-manual-verified (per 2021 Hyundai Veloster OM, portal file 2021-Veloster-Owners-Manual.pdf = "
      "veloster_2021_portal_OM.pdf, owners.hyundaiusa.com glovebox-manual folder 2021/veloster, PDF title '2021 Veloster "
      "Owners Manual', cover reads '2021 Owner's Manual VELOSTER' (part no. LJ3O-EU05B), Copyright 2020 HYUNDAI Motor "
      "America; " + VEL_ID + "; brake-fluid replacement rows read from grid marks on page renders (p.7-10 and 7-15); "
      + VEL_GATES + ")",
  msrc="Hyundai Owner's Manual (Veloster 2021 JS, p.%s)",
  maint=VEL_MAINT + [
      (30000, 48, "Brake fluid replacement (" + N20 + ")", "7-10"),
      (30000, 60, "Brake / clutch fluid replacement (" + T16 + ")", "7-15"),
  ]),

 dict(vid=9981, model="Santa Cruz", label="2026 NX4OB  " + G25 + " + " + G25T, psi_f=35, psi_r=35, lug=LUG,
  oil=dict(visc="0W-20 (" + G25 + ") / 0W-30 (" + G25T + ")", type=SYN,
           cap="6.13 qt / 5.8 L (" + G25 + ") / 6.13 qt / 5.8 L (" + G25T + ")", cap_wo=None,
           spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API SN PLUS or above); SAE 0W-20 (" + G25
                + ") / SAE 0W-30 (" + G25T + ")"),
  fluids=dict(trans="Automatic transmission: ATF SP4M-1 (SK, MICHANG, S-OIL, Hyundai genuine), 6.87 qt / 6.5 L.",
              brake=BRAKE_LV + "; 0.87 qt / 0.82 L", cool_type=COOL_EG,
              cool_cap="10 qt / 9.5 L (" + G25 + ") / 9.09 qt / 8.6 L (" + G25T + ")", ps=EPS,
              diff=diff(("Rear differential (AWD)", GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L"),
                        ("Transfer case (AWD)", GL5_85 + ", 0.65-0.71 qt / 0.62-0.68 L"))),
  parts=dict(tire="245/60R18 or 245/50R20",
             note="18-in wheels: 245/60R18; 20-in wheels: 245/50R20; 35 psi front and rear at normal and maximum load. "
                  "Compact spare (if equipped) T135/80D18 at 60 psi. Fuel tank 17.69 gal / 67 L."),
  src="owner-manual-verified (per 2026 Hyundai Santa Cruz OM, ownersmanual.hyundai.com full_pdf NX4OB 2026 en_US = "
      "santa_cruz_2026_NX4OB_global_OM.pdf, book header '_NX4aOB_en_US', Copyright 2026 HYUNDAI Motor America, PDF created "
      "2026-04-30, single available print (no US-portal copy exists for 2025 or 2026; this book is served by the "
      "manufacturer's host but is absent from its US menu, which lists NX4OB labels 2021-2024; accepted by ruling "
      "2026-11-14); model year read from the label and tested: the host files 2027-model-year books of other nameplates "
      "under their own 2027 label and none exists for NX4OB, it keeps updating 2026 labels in place, and this book says "
      "AWD where the 2025-label book says 4WD, as the Tucson books do between 2025 and 2026; NX4OB, self-ID p.10-2 "
      "Smartstream G2.5 GDI + G2.5 T-GDI 2,497cc, wheelbase 118.30 in, overall length 195.67 in, pickup body on the "
      "exterior overview p.2-3; capacities p.10-7 / 10-8 (one oil quantity cell spans both engines; the G2.5 GDI coolant "
      "figure is printed without decimals), viscosity chart p.10-9 and tires + wheel nut torque p.10-4 read from page "
      "renders; schedule p.9-11 to 9-15, the turbo spark-plug row and the cabin-filter row read from grid marks on page "
      "renders; gated to null: 12V battery group and CCA (the battery capacity label page shows only a label "
      "illustration, MF68R-DIN), " + NO_PLUG + ")",
  msrc="Hyundai Owner's Manual (Santa Cruz 2026 NX4OB, p.%s)",
  maint=[
      (8000, 12, "Engine oil & filter change", "9-11"),
      (96000, None, "Spark plug replacement (" + G25 + ")", "9-12"),
      (48000, 72, "Spark plug replacement (" + G25T + ")", "9-12"),
      (24000, 36, "Engine air cleaner filter replacement", "9-11"),
      (16000, 24, "Cabin air filter replacement", "9-15"),
      (8000, 12, "Tire rotation", "9-15"),
      (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-13"),
      (48000, 48, "Brake fluid replacement", "9-13"),
  ]),
]
assert DEFERRED not in [r["vid"] for r in ROWS]

# ---------------------------------------------------------------------------------------------------------------
def unit_pairs(vid, s):
    """Every printed US / metric pair must convert, within print rounding. Returns the number of pairs checked."""
    n = 0
    for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
        qs, ls = q.split("-"), l.split("-")
        assert len(qs) == len(ls), (vid, "qt/L range shape", q, l)
        for a, b in zip(qs, ls):          # a range is compared end to end; 1 L = 1.0567 US qt
            assert abs(float(a) - float(b) * 1.0567) <= 0.09, (vid, "qt/L mismatch", q, l, s)
            n += 1
    for g, l in re.findall(r"([0-9.]+) gal / ([0-9.]+) L", s or ""):
        dec = len(g.split(".")[1]) if "." in g else 0        # tolerance follows the printed precision; 1 US gal = 3.7854 L
        assert abs(float(g) - float(l) / 3.7854) <= max(0.03, 0.5 * 10 ** -dec + 0.005), (vid, "gal/L mismatch", g, l, s)
        n += 1
    assert not re.search(r"[0-9] (?:qt|gal)(?! /)", s or ""), (vid, "unpaired US unit", s)
    return n

def check(row):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid, model = row["vid"], row["model"]
    want = (int(row["label"][:4]), "Hyundai", model)
    assert VEHICLES.get(vid) == want, (vid, "target row is not the labelled vehicle", VEHICLES.get(vid), want)
    assert ("per %d Hyundai %s OM" % (want[0], model)) in row["src"] and ("%s %d " % (model, want[0])) in row["msrc"], (vid, "source year")
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    for mi, mo, desc, page in row["maint"]:
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert mi is None or (isinstance(mi, int) and mi > 0), (vid, desc)
        assert mo is None or (isinstance(mo, int) and mo > 0), (vid, desc)
        assert mi is not None or mo is not None, (vid, desc, "a row needs an interval")
    o, f, p = row["oil"], row["fluids"], row["parts"]
    shipped = [o["visc"], o["type"], o["cap"], o["cap_wo"], o["spec"], f["trans"], f["brake"], f["cool_type"], f["cool_cap"],
               f["ps"], p["tire"], p["note"], row["lug"]["note"]] + [d for _, _, d, _ in row["maint"]]
    for e in (json.loads(f["diff"]) if f["diff"] else []):
        assert set(e) == {"location", "fluid_type"}, (vid, e)
        shipped += [e["location"], e["fluid_type"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
            assert "36 psi" not in s and "100 mph" not in s, (vid, "the high-speed pressure must not ship", s)
    assert row["src"] != BARE and row["src"].startswith(BARE + " (") and row["src"].endswith(")")
    for k in ("psi_f", "psi_r"):
        assert row[k] is None or isinstance(row[k], int), (vid, k)
    return sum(unit_pairs(vid, s) for s in shipped)

def bare_count(c):
    return c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                     "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source=?", (BARE,)).fetchone()[0]

def holds(c, vid):
    """What an id holds now: {table: sorted source tokens}. A frozen bare row must never be deleted."""
    out = {}
    for t in TABLES:
        toks = sorted(set((r[0] or "NULL").split(" (")[0] for r in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % t, (vid,))))
        if toks:
            out[t] = toks
    return out

def fingerprint(c, vid):
    """Row counts per curated table for an id - used to prove the deferred row is untouched."""
    return tuple(c.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id=?" % t, (vid,)).fetchone()[0] for t in TABLES)

def write(c, nid, row):
    vid, o, f, p, lug = row["vid"], row["oil"], row["fluids"], row["parts"], row["lug"]
    for t in TABLES:
        c.execute("DELETE FROM %s WHERE vehicle_id=?" % t, (vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,"
              "filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, o["visc"], o["type"], o["cap"], o["cap_wo"], o["spec"], None, None, None, None, None, row["src"]))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,"
              "coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
              (vid, f["trans"], None, f["brake"], f["cool_type"], f["cool_cap"], f["ps"], f["diff"], row["src"]))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,"
              "tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,"
              "wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,"
              "real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, None, None, None, None, None, p["tire"], row["psi_f"], row["psi_r"], None, None, None, None, None,
               p["note"], None, None, None, None, None, row["src"]))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
              (vid, "lug_nut", lug["ftlb"], lug["nm"], lug["note"], row["src"]))
    for mi, mo, desc, page in row["maint"]:
        c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,"
                  "difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (nid, vid, mi, mo, desc, row["msrc"] % page, "standard", None, None, None))
        nid += 1
    return nid

def show(row):
    o, f, p = row["oil"], row["fluids"], row["parts"]
    print("\n=== %d  %s %s" % (row["vid"], row["model"], row["label"]))
    print("  oil   : %s | w/o filter: %s | %s | %s" % (o["cap"], o["cap_wo"], o["visc"], o["type"]))
    print("  spec  : %s" % o["spec"])
    print("  trans : %s" % f["trans"])
    print("  cool  : %s | %s" % (f["cool_cap"], f["cool_type"]))
    print("  brake : %s" % f["brake"])
    print("  steer : %s" % f["ps"])
    for e in (json.loads(f["diff"]) if f["diff"] else []):
        print("  diff  : %s -> %s" % (e["location"], e["fluid_type"]))
    print("  tires : %s @ %s front / %s rear psi | %s" % (p["tire"], row["psi_f"], row["psi_r"], p["note"]))
    print("  plugs : None | gap None | battery None")
    print("  lug   : %s lb-ft / %s N-m | %s" % (row["lug"]["ftlb"], row["lug"]["nm"], row["lug"]["note"]))
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7s mi / %s mo  %s  [p.%s]" % (mi if mi else "--", mo if mo else "--", desc, page))
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
DEFER_BEFORE = fingerprint(_c, DEFERRED)
print("  id %d (Veloster 2020, deferred) holds %s rows per table and is left as it is" % (DEFERRED, DEFER_BEFORE))
_c.close()
for row in ROWS:
    show(row)

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_veloster_santa_cruz_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
try:
    nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
    for row in ROWS:
        nid = write(c, nid, row)
        print("  wrote %d  %s %s" % (row["vid"], row["model"], row["label"]))
    assert bare_count(c) == 424, ("freeze would break", bare_count(c))            # checked BEFORE commit
    assert fingerprint(c, DEFERRED) == DEFER_BEFORE, "the deferred row changed"    # checked BEFORE commit
    db.commit()
except Exception:
    db.rollback()
    raise

print("\nVerify:")
for row in ROWS:
    vid = row["vid"]
    o = c.execute("SELECT capacity_with_filter, source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchall()
    f = c.execute("SELECT coolant_capacity, transmission_capacity, differential_fluids_json FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, tire_pressure_rear, battery_group, battery_notes, spark_plug_type, battery_cca FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT component, torque_ft_lbs, source FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), MIN(source) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and e == 0, vid
    assert f[0][1] is None and f[0][2] == row["fluids"]["diff"], vid
    assert p[0][3] is None and p[0][4] is None and p[0][5] is None and p[0][6] is None, vid
    assert t[0][2].startswith(BARE + " (") and classify(t[0][2], "torque_specs", vid) == 1
    for tb in ("oil_change", "fluids", "parts", "maintenance", "torque_specs"):
        for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)):
            assert classify(s, tb, vid) == 1, (vid, tb, s[:60])
    print("  %d: oil=%s | cool=%s | tire=%s @%s/%s | diff=%s | lug=%s | maint=%d"
          % (vid, o[0][0][:40], f[0][0][:40], p[0][0], p[0][1], p[0][2], "yes" if f[0][2] else "none", t[0][1], m[0]))
print("  deferred id %d unchanged: %s" % (DEFERRED, fingerprint(c, DEFERRED) == DEFER_BEFORE))
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare_count(c))
db.close()
print("DONE - %d rows written, 1 deferred row left untouched." % len(ROWS))
