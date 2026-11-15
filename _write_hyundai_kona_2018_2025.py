# Hyundai Kona 2018 / 2019 / 2023 / 2025 - curated specs for the four model-year rows added by _add_hyundai_rows.py
# (missing-year step B). Ids 38723 (2018), 38724 (2019), 38725 (2023), 38726 (2025). They held no curated rows.
# Sources (manufacturer, free, citable), saved under _hyundai_manuals/kona/ (gitignored); reads 2026-11-14:
#   2018  US portal '2018 Kona Owners Manual.pdf' (Copyright 2017, created 2017-12-01; the Kona's first US model year)
#         + later print  ownersmanual.hyundai.com full_pdf OS 2018 en_US (Copyright 2018): every specification and
#           schedule page identical.
#   2019  US portal '2019 Kona OM.pdf' (Copyright 2018, created 2018-09-26)
#         + later print  full_pdf OS 2019 en_US (Copyright 2019): identical except the brake-fluid grade (see below).
#   2023  US portal 2023-Kona-OM.pdf, PDF title "2023 Kona Owner's Manual" (Copyright 2022, created 2022-07-14)
#         + full_pdf OS 2023 en_US and full_pdf OS 2022 en_US (both hold the 2023 book; neither is on the US menu):
#           every written value agrees.
#   2025  full_pdf SX2 2025 en_US, PDF keywords 'en_US,hyundai,SX2,2025,engine,1.3' (Copyright 2024), single print.
#   Second-host files were placed by vocabulary (layout-proof) and creation date, never by page identity across hosts.
#   Each book was identified by the Kona body on its exterior overview (page renders), the engine table and the
#   wheelbase (OS 102.36 in, SX2 104.7 in). Kona N and Kona Electric have their own books and are not here.
# ** Rulings 2026-11-14 ("Go, as recommended"), reasons live HERE and in the source suffix only:
#    EDITION CONFLICT 2019 brake fluid: first print 'FMVSS116 DOT-3 or DOT-4', later print 'SAE J1704 DOT-4 LV, FMVSS
#       116 DOT-4, ISO 4925 CLASS-6'. Written: the grade BOTH prints name, FMVSS 116 DOT-4, with the agreed quantity.
#    UNITS AS PRINTED (standing): all three 2023 prints give capacities in US gallons -> written in gallons; the 2023
#       transfer-case line is printed in quarts -> written in quarts.
#    UNIT CONFLICT (standing): a quantity whose US figure does not convert to its litre figure is not written -
#       2018 / 2019 transfer case and rear differential (the quart figures are the litre figures DIVIDED by 1.057),
#       2023 brake fluid (0.5-0.6 qt beside 0.7-0.8 L), 2025 IVT fluid, rear differential and transfer case.
#    DRIVETRAIN WORDING AS PRINTED (standing): the 2023 book prints 'Rear differential oil (AWD)' and 'Transfer case
#       oil (4WD)'; each line is written the way it is printed.
# ** 2018 / 2019 have no brake-fluid replacement line: both prints of each year show inspection marks only.
# ** Gates (null): spark-plug part number / gap (not published; interval only); 12V battery (2018 / 2019 publish no
#    spec; 2023 p.9-31 and 2025 p.655 show only an example capacity label); EPS / MDPS - no power-steering fluid.
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows (checked BEFORE
#    commit). S1.12 / S1.11: no bookkeeping words in shipped columns; battery_notes NULL; diff JSON = [{location, fluid_type}].
#
# Usage:  python _write_hyundai_kona_2018_2025.py            -> DRY RUN: print every row, classify every source
#         python _write_hyundai_kona_2018_2025.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
# printed US figures that do not convert to their litre figure: never in a shipped column
NO_CONVERT = re.compile(r"0\.44-0\.49|0\.36-0\.4 qt|0\.5-0\.6 qt|6\.9 qt|7\.1 qt|0\.6-0\.7 qt|0\.8-0\.9 qt")
TABLES = ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]
TARGETS = {38723: 2018, 38724: 2019, 38725: 2023, 38726: 2025}

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Kona'")}
_c.close()
assert sorted(VEHICLES) == [673, 2166, 3694, 6787, 9976, 38723, 38724, 38725, 38726], ("the Kona rows are not the nine expected", sorted(VEHICLES))
for _vid, _year in TARGETS.items():
    assert VEHICLES[_vid] == (_year, "Hyundai", "Kona"), (_vid, VEHICLES[_vid])

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_OS = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
COOL_OSPE = "Mixture of antifreeze and distilled water; ethylene glycol with phosphate-based coolant for aluminum radiator"
COOL_SX2 = "Mixture of antifreeze and distilled water; ethylene glycol base coolant for aluminum radiator"
BRAKE_LV = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
BRAKE_QTY = "0.74-0.85 qt / 0.7-0.8 L"
ATF_SP4 = "ATF SP-IV (MICHANG, SK, NOCA, Hyundai genuine or other approved brands meeting the spec)"
ATF_SP4M1 = "ATF SP4M-1 (SK, MICHANG, S-OIL, Hyundai genuine or other approved brands meeting the spec)"
GL5_90 = "Hypoid gear oil API GL-5 SAE 75W/90 (Shell HD Axle Oil 75W90 or equivalent)"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
LUG_NOTE = "79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)"
NU, GAMMA = "Nu 2.0 MPI", "Gamma 1.6 T-GDI"
S20, S16 = "Smartstream G2.0 Atkinson", "Smartstream G1.6 T-GDi"
PORTAL = "owners.hyundaiusa.com glovebox-manual"
GLOBAL = "ownersmanual.hyundai.com full_pdf %s %s en_US"

def diff(*pairs):
    return json.dumps([{"location": loc, "fluid_type": fl} for loc, fl in pairs], ensure_ascii=False)

CHART_NU = "SAE 5W-20 recommended, chart also allows 5W-30 / 10W-30 by temperature"
CHART_GAMMA = "SAE 5W-30 recommended, chart also allows 5W-40 / 10W-30 / 15W-40 / 20W-50 by temperature"
OS_VISC = "5W-20 (" + NU + ") / 5W-30 (" + GAMMA + ")"
OS_CAP = "4.23 qt / 4.0 L (" + NU + ") / 4.76 qt / 4.5 L (" + GAMMA + ")"
OS_COOL = "6.8 qt / 6.5 L (" + NU + ") / 7.5 qt / 7.1 L (" + GAMMA + ")"
OS_DIFF = diff(("Rear differential (AWD)", GL5_90), ("Transfer case (AWD)", GL5_90))
OS_TIRES = "205/60R16, 215/55R17 or 235/45R18"
OS_NOTE = ("16-in wheels: 205/60R16; 17-in wheels: 215/55R17; 18-in wheels: 235/45R18; 33 psi front and rear. "
           "Compact spare %sT125/80D16 at 60 psi. Fuel tank %s.")
def os_trans(hk):
    return ("Automatic transmission (" + NU + "): " + ATF_SP4 + ", 7.08 qt / 6.7 L. Dual clutch transmission (" + GAMMA
            + "): API GL-4 SAE 70W (" + hk + ", Spirax S6 GHME 70W DCTF or GS DCTF HD 70W), 2.01-2.11 qt / 1.9-2.0 L.")
OS_MAINT = [   # 2018 and 2019: each read from that year's own p.7-8 (Nu) and p.7-13 (Gamma); no brake-fluid replacement line
    (7500, 12, "Engine oil & filter change (" + NU + ")", "7-8"),
    (6000, 12, "Engine oil & filter change (" + GAMMA + ")", "7-13"),
    (97500, None, "Spark plug replacement (" + NU + ")", "7-8"),
    (42000, None, "Spark plug replacement (" + GAMMA + ")", "7-13"),
    (30000, 48, "Engine air cleaner filter replacement (" + NU + ")", "7-8"),
    (24000, 48, "Engine air cleaner filter replacement (" + GAMMA + ")", "7-13"),
    (15000, 12, "Climate control (cabin) air filter replacement (" + NU + ")", "7-8"),
    (12000, 12, "Climate control (cabin) air filter replacement (" + GAMMA + ")", "7-13"),
    (7500, None, "Tire rotation (" + NU + ")", "7-8"),
    (6000, None, "Tire rotation (" + GAMMA + ")", "7-13"),
    (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-8, 7-13"),
]
OS_ID = ("OS, self-ID engine table p.8-2 Gamma 1.6 T-GDI 1,591cc + Nu 2.0 MPI 1,999cc, wheelbase 102.36 in, Kona body on the "
         "exterior overview p.1-2; capacities p.8-7/8-8, viscosity chart p.8-9 read from a page render, tires + lug torque "
         "p.8-5; schedules p.7-8 (" + NU + ") and p.7-13 (" + GAMMA + ") read from page renders")
OS_GATES = ("gated to null: transfer case and rear differential capacities (the quart figures on p.8-8 do not convert to "
            "the litre figures), brake-fluid replacement interval (the schedule prints inspection only, p.7-10 and p.7-15, "
            "in both prints), 12V battery group and CCA (not published), spark-plug part number and gap (not published, "
            "interval only), battery notes")
SS_OIL_SPEC = "API SN PLUS/SP or ILSAC GF-6, full synthetic required; SAE 0W-20 only"
PLUG_GATE = "spark-plug part number and gap (not published, interval only), battery notes"

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=38723, label="2018 OS  Nu 2.0 MPI + Gamma 1.6 T-GDI", psi=33,
  oil=dict(visc=OS_VISC, type=None, cap=OS_CAP,
           spec=NU + ": API SM and ILSAC GF-4 (or above), ACEA A5/B5; " + CHART_NU + ". " + GAMMA + ": ACEA A5/B5; "
                + CHART_GAMMA + "."),
  fluids=dict(trans=os_trans("HK SYN DCTF 70W"), brake="FMVSS 116 DOT-3 or DOT-4; " + BRAKE_QTY, cool_type=COOL_OS,
              cool_cap=OS_COOL, diff=OS_DIFF),
  parts=dict(tire=OS_TIRES, note=OS_NOTE % ("", "13.2 gal / 50 L")),
  src="owner-manual-verified (per 2018 Hyundai Kona OM, portal file '2018 Kona Owners Manual.pdf' = "
      "kona_2018_OS_portal_OM.pdf, " + PORTAL + ", Copyright 2017 HYUNDAI Motor America, PDF created 2017-12-01 (first "
      "print; 2018 is the Kona's first US model year), cross-checked against the later print " + (GLOBAL % ("OS", "2018"))
      + " = kona_2018_OS_global_OM.pdf (Copyright 2018): every specification and schedule page is identical; " + OS_ID
      + "; " + OS_GATES + ")",
  msrc="Hyundai Owner's Manual (Kona 2018 OS, p.%s)",
  maint=list(OS_MAINT)),

 dict(vid=38724, label="2019 OS  Nu 2.0 MPI + Gamma 1.6 T-GDI", psi=33,
  oil=dict(visc=OS_VISC, type=None, cap=OS_CAP,
           spec=NU + ": API Latest (ILSAC Latest); " + CHART_NU + ". " + GAMMA + ": API Latest (ILSAC Latest) or ACEA "
                "A5/B5; " + CHART_GAMMA + "."),
  fluids=dict(trans=os_trans("HK DCTF 70W"), brake="FMVSS 116 DOT-4; " + BRAKE_QTY, cool_type=COOL_OS,
              cool_cap=OS_COOL, diff=OS_DIFF),
  parts=dict(tire=OS_TIRES, note=OS_NOTE % ("", "13.2 gal / 50 L")),
  src="owner-manual-verified (per 2019 Hyundai Kona OM, portal file '2019 Kona OM.pdf' = kona_2019_OS_portal_OM.pdf, "
      + PORTAL + ", Copyright 2018 HYUNDAI Motor America, PDF created 2018-09-26 (first print), cross-checked against "
      "the later print " + (GLOBAL % ("OS", "2019")) + " = kona_2019_OS_global_OM.pdf (Copyright 2019; a later print "
      "of the 2019 book: it keeps this book's wording where the 2020 book changes it): every specification and "
      "schedule page is identical except the brake-fluid line; " + OS_ID + "; the two prints name the brake fluid "
      "differently (first print p.8-8 'FMVSS116 DOT-3 or DOT-4', later print 'SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, "
      "ISO 4925 CLASS-6') - written: the grade both prints name, FMVSS 116 DOT-4, with the quantity both state "
      "(ruling 2026-11-14); " + OS_GATES + ")",
  msrc="Hyundai Owner's Manual (Kona 2019 OS, p.%s)",
  maint=list(OS_MAINT)),

 dict(vid=38725, label="2023 OS facelift  Smartstream G2.0 Atkinson + Smartstream G1.6 T-GDi", psi=33,
  oil=dict(visc="0W-20", type="Full synthetic (required)",
           cap="1.14 gal / 4.3 L (" + S20 + ") / 1.27 gal / 4.8 L (" + S16 + ")", spec=SS_OIL_SPEC),
  fluids=dict(
   trans="Intelligent variable transmission (" + S20 + "): SP-CVT1, 1.77 gal / 6.7 L. Dual clutch transmission (" + S16
         + "): API GL-4 SAE 70W (HK D DCTF TGO-10, Spirax S6 GHDE 70W DCTF or 7 DCTF HKM), 0.42-0.45 gal / 1.6-1.7 L.",
   brake=BRAKE_LV, cool_type=COOL_OSPE,
   cool_cap="1.59 gal / 6.0 L (" + S20 + ") / 1.82 gal / 6.9 L (" + S16 + ")",
   diff=diff(("Rear differential (AWD)", GL5_90 + ", 0.12-0.14 gal / 0.47-0.52 L"),
             ("Transfer case (4WD)", GL5_85 + "; 0.49-0.55 qt / 0.47-0.52 L (" + S16 + "), 0.4-0.44 qt / 0.38-0.42 L ("
              + S20 + ")"))),
  parts=dict(tire=OS_TIRES, note=OS_NOTE % ("(if equipped) ", "13.21 gal / 50 L")),
  src="owner-manual-verified (per 2023 Hyundai Kona OM, portal file 2023-Kona-OM.pdf = kona_2023_portal_OM.pdf, "
      + PORTAL + ", PDF title '2023 Kona Owner's Manual', Copyright 2022 HYUNDAI Motor America, PDF created 2022-07-14 "
      "(first print), cross-checked against two files on the second host, neither on its US menu: "
      + (GLOBAL % ("OS", "2023")) + " = kona_2023_OS_global_OM.pdf (Copyright 2022, PDF created 2023-07-06; identical on "
      "the specification and schedule pages apart from an added engine-oil-additive notice) and "
      + (GLOBAL % ("OS", "2022")) + " = kona_2022_OS_global_OM.pdf (the label audit 2026-11-14 showed this label holds "
      "the 2023 book; same values, schedule page numbers one lower): every written value agrees; OS facelift, self-ID "
      "engine table p.2-9 Smartstream G1.6 T-GDi 1,598cc + Smartstream G2.0 Atkinson 1,999cc, wheelbase 102.36 in, "
      "Kona body on the exterior overview p.2-2; capacities p.2-13/2-14 are printed in US gallons and litres and are "
      "written as printed (the transfer-case line is printed in quarts), viscosity chart p.2-14 read from a page "
      "render, tires + lug torque p.2-11; schedule p.9-9 to 9-11, grids read from upright page renders; the book "
      "prints 'Rear differential oil (AWD)' and 'Transfer case oil (4WD)', written as printed; gated to null: "
      "brake-fluid capacity (0.5-0.6 qt beside 0.7-0.8 L on p.2-14 do not convert to each other), 12V battery group "
      "and CCA (p.9-31 shows only an example capacity label CMF60L-BCI), " + PLUG_GATE + ")",
  msrc="Hyundai Owner's Manual (Kona 2023 OS facelift, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-9"),
   (96000, None, "Spark plug replacement (" + S20 + ")", "9-9"),
   (48000, None, "Spark plug replacement (" + S16 + ")", "9-9"),
   (24000, 36, "Engine air cleaner filter replacement", "9-9"),
   (16000, 24, "Cabin air filter replacement", "9-9"),
   (8000, 12, "Tire rotation", "9-9"),
   (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-10"),
   (48000, 48, "Brake fluid replacement", "9-11"),
  ]),

 dict(vid=38726, label="2025 SX2  Smartstream G2.0 Atkinson + Smartstream G1.6 T-GDi", psi=None,
  oil=dict(visc="0W-20", type="Full synthetic (required)",
           cap="4.5 qt / 4.3 L (" + S20 + ") / 5.1 qt / 4.8 L (" + S16 + ")", spec=SS_OIL_SPEC),
  fluids=dict(
   trans="Automatic transmission (" + S16 + "): " + ATF_SP4M1 + ", 6.8 qt / 6.5 L. Intelligent variable transmission ("
         + S20 + "): CVTF SP-CVT1 (MICHANG or Hyundai genuine).",
   brake="DOT-4", cool_type=COOL_SX2,
   cool_cap="7.3 qt / 6.9 L (" + S20 + ") / 9.0 qt / 8.5 L (" + S16 + ")",
   diff=diff(("Rear differential (AWD)", GL5_85), ("Transfer case (AWD)", GL5_85))),
  parts=dict(tire="215/60R17, 215/55R18 or 235/45R19",
             note="17-in wheels: 215/60R17 at 36 psi; 18-in wheels: 215/55R18 at 33 psi; 19-in wheels: 235/45R19 at 33 "
                  "psi; front and rear, normal and maximum load. Compact spare (if equipped) T145/90D16 at 60 psi. "
                  "Fuel tank 12.4 gal / 47 L (" + S20 + ") / 13.2 gal / 50 L (" + S16 + ")."),
  src="owner-manual-verified (per 2025 Hyundai Kona OM, " + (GLOBAL % ("SX2", "2025")) + " = kona_2025_SX2_global_OM.pdf, "
      "PDF keywords 'en_US,hyundai,SX2,2025,engine,1.3', Copyright 2024 HYUNDAI Motor America, first posted 2024-10-14, "
      "single print (no US-portal copy exists); SX2, self-ID p.25 Smartstream G1.6 T-GDi 1,598cc + Smartstream G2.0 "
      "Atkinson 1,999cc, wheelbase 104.7 in p.24, Kona body on the exterior overview p.15; capacities p.31, viscosity "
      "chart p.32 read from a page render, tires + wheel nut torque p.28; schedule p.625 to 629 read from page "
      "renders; gated to null: IVT, rear differential and transfer case capacities (quart and litre figures on p.31 "
      "do not convert to each other), 12V battery group and CCA (p.655 shows only an example capacity label "
      "AGM70L-DIN), " + PLUG_GATE + ")",
  msrc="Hyundai Owner's Manual (Kona 2025 SX2, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "625-626"),
   (48000, None, "Spark plug replacement (" + S16 + ")", "626"),
   (96000, None, "Spark plug replacement (" + S20 + ")", "626"),
   (24000, 36, "Engine air cleaner filter replacement", "626"),
   (16000, 24, "Cabin air filter replacement", "629"),
   (8000, 12, "Tire rotation", "628"),
   (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "628"),
   (48000, 48, "Brake fluid replacement", "628"),
  ]),
]
assert sorted(r["vid"] for r in ROWS) == sorted(TARGETS), "this script writes the four new Kona rows and nothing else"
EXPECT = {2018: (11, "7-"), 2019: (11, "7-"), 2023: (8, "9-"), 2025: (8, "62")}     # schedule lines, page prefix

# ---------------------------------------------------------------------------------------------------------------
def unit_pairs(vid, s):
    """Every printed US / metric pair must convert, within print rounding (ranges end to end). Returns pairs checked."""
    n = 0
    for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
        qs, ls = q.split("-"), l.split("-")
        assert len(qs) == len(ls), (vid, "qt/L range shape", q, l)
        for a, b in zip(qs, ls):                                  # 1 L = 1.0567 US qt
            assert abs(float(a) - float(b) * 1.0567) <= 0.09, (vid, "qt/L mismatch", q, l, s)
            n += 1
    for g, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) gal / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
        gs, ls = g.split("-"), l.split("-")
        assert len(gs) == len(ls), (vid, "gal/L range shape", g, l)
        for a, b in zip(gs, ls):                                  # 1 US gal = 3.7854 L; tolerance follows the printed precision
            dec = len(a.split(".")[1]) if "." in a else 0
            tol = 0.0075 if dec >= 2 else max(0.03, 0.5 * 10 ** -dec + 0.005)
            assert abs(float(a) - float(b) / 3.7854) <= tol, (vid, "gal/L mismatch", g, l, s)
            n += 1
    assert not re.search(r"[0-9] (?:qt|gal)(?! /)", s or ""), (vid, "unpaired US unit", s)
    return n

def check(row):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid = row["vid"]
    year = int(row["label"][:4])
    assert VEHICLES.get(vid) == (year, "Hyundai", "Kona") and TARGETS.get(vid) == year, (vid, "target row is not the labelled vehicle")
    assert ("per %d Hyundai Kona OM" % year) in row["src"] and ("Kona %d " % year) in row["msrc"], (vid, "source year")
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    n_lines, prefix = EXPECT[year]
    assert len(row["maint"]) == n_lines, (vid, "schedule lines", len(row["maint"]))
    for mi, mo, desc, page in row["maint"]:
        assert page.startswith(prefix), (vid, desc, page, "schedule pages for this year")
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert isinstance(mi, int) and mi > 0, (vid, desc)
        assert mo is None or (isinstance(mo, int) and mo > 0), (vid, desc)
    has_brake_row = any("Brake fluid" in d for _, _, d, _ in row["maint"])
    assert has_brake_row == (year in (2023, 2025)), (vid, "brake-fluid replacement line")
    o, f, p = row["oil"], row["fluids"], row["parts"]
    locs = [e["location"] for e in json.loads(f["diff"])]
    assert locs == (["Rear differential (AWD)", "Transfer case (4WD)"] if year == 2023 else
                    ["Rear differential (AWD)", "Transfer case (AWD)"]), (vid, locs)
    if year == 2018:
        assert f["brake"].startswith("FMVSS 116 DOT-3 or DOT-4; ") and "HK SYN DCTF 70W" in f["trans"] and "API SM" in o["spec"]
    if year == 2019:                    # edition ruling: only the grade both prints name
        assert f["brake"] == "FMVSS 116 DOT-4; " + BRAKE_QTY and "DOT-3" not in f["brake"] and "LV" not in f["brake"]
        assert "HK DCTF 70W" in f["trans"] and "API Latest" in o["spec"] and "API SM" not in o["spec"]
    shipped = [o["visc"], o["type"], o["cap"], o["spec"], f["trans"], f["brake"], f["cool_type"], f["cool_cap"],
               p["tire"], p["note"], LUG_NOTE, EPS] + [d for _, _, d, _ in row["maint"]]
    for e in json.loads(f["diff"]):
        assert set(e) == {"location", "fluid_type"}, (vid, e)
        shipped += [e["location"], e["fluid_type"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
            assert not NO_CONVERT.search(s), (vid, "a quantity that does not convert is in a shipped column", s)
    gal_capacity = any(re.search(r"gal / [0-9.-]+ L", s or "") for s in (o["cap"], f["trans"], f["cool_cap"]))
    assert gal_capacity == (year == 2023), (vid, "gallon capacities belong to the 2023 book only")
    assert row["src"] != BARE and row["src"].startswith(BARE + " (") and row["src"].endswith(")")
    assert row["psi"] is None or isinstance(row["psi"], int)
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
              (vid, o["visc"], o["type"], o["cap"], None, o["spec"], None, None, None, None, None, row["src"]))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,"
              "coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
              (vid, f["trans"], None, f["brake"], f["cool_type"], f["cool_cap"], EPS, f["diff"], row["src"]))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,"
              "tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,"
              "wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,"
              "real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, None, None, None, None, None, p["tire"], row["psi"], row["psi"], None, None, None, None, None,
               p["note"], None, None, None, None, None, row["src"]))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
              (vid, "lug_nut", 79.0, 107.0, LUG_NOTE, row["src"]))
    for mi, mo, desc, page in row["maint"]:
        c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,"
                  "difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (nid, vid, mi, mo, desc, row["msrc"] % page, "standard", None, None, None))
        nid += 1
    return nid

def show(row):
    o, f, p = row["oil"], row["fluids"], row["parts"]
    print("\n=== %d  Kona %s" % (row["vid"], row["label"]))
    print("  oil   : %s | %s | %s" % (o["cap"], o["visc"], o["type"]))
    print("  spec  : %s" % o["spec"])
    print("  trans : %s" % f["trans"])
    print("  cool  : %s | %s" % (f["cool_cap"], f["cool_type"]))
    print("  brake : %s" % f["brake"])
    for e in json.loads(f["diff"]):
        print("  diff  : %s -> %s" % (e["location"], e["fluid_type"]))
    print("  tires : %s @ %s psi | %s" % (p["tire"], row["psi"] if row["psi"] else "per size (see note)", p["note"]))
    print("  lug   : 79.0 lb-ft / 107.0 N-m | %s" % LUG_NOTE)
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7d mi / %s mo  %s  [p.%s]" % (mi, mo if mo else "--", desc, page))
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

bak = DB + ".bak_kona_2018_2025_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
try:
    nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
    for row in ROWS:
        nid = write(c, nid, row)
        print("  wrote %d  Kona %s" % (row["vid"], row["label"]))
    assert bare_count(c) == 424, ("freeze would break", bare_count(c))      # checked BEFORE commit
    db.commit()
except Exception:
    db.rollback()
    raise

print("\nVerify:")
for row in ROWS:
    vid = row["vid"]
    o = c.execute("SELECT capacity_with_filter, source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchall()
    f = c.execute("SELECT coolant_capacity, transmission_capacity, differential_fluids_json, brake_fluid FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, tire_pressure_rear, battery_group, battery_notes, spark_plug_type FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT component, torque_ft_lbs, source FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), MIN(source) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and e == 0, vid
    assert f[0][1] is None and len(json.loads(f[0][2])) == 2 and p[0][3] is None and p[0][4] is None and p[0][5] is None, vid
    assert t[0][2].startswith(BARE + " (") and classify(t[0][2], "torque_specs", vid) == 1
    for tb in ("oil_change", "fluids", "parts", "maintenance", "torque_specs"):
        for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)):
            assert classify(s, tb, vid) == 1, (vid, tb, s[:60])
    g = [c.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id=?" % tb, (vid,)).fetchone()[0]
         for tb in ("fuel_economy", "recalls", "safety_ratings", "complaints")]
    print("  %d: oil=%s | cool=%s | brake=%s | tire=%s @%s | lug=%s | maint=%d | government rows %s"
          % (vid, o[0][0][:30], f[0][0][:26], f[0][3][:26], p[0][0], p[0][1], t[0][1], m[0], g))
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare_count(c))
db.close()
print("DONE - %d rows written." % len(ROWS))
