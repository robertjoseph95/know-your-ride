# Hyundai Santa Cruz 2022 / 2023 / 2024 / 2025 - curated specs for the four model-year rows added by
# _add_hyundai_rows.py (missing-year step B). Ids 38727 (2022), 38728 (2023), 38729 (2024), 38730 (2025).
# They held no curated rows.
# Sources (manufacturer, free, citable), saved under _hyundai_manuals/santa_cruz/ (gitignored); reads 2026-11-14:
#   2022  US portal 2022-Santa-Cruz-Owners-Manual.pdf, PDF title '2022 Santa Cruz Owners Manual' (Copyright 2021,
#         created 2021-06-08) + the December 2021 print  ownersmanual.hyundai.com full_pdf NX4OB 2021 en_US
#         (Copyright 2021, proof marks 2021-12-23): specification pages identical, one schedule line differs.
#   2023  US portal '2023-Santa Cruz-OM.pdf' (Copyright 2022, created 2022-11-17) + full_pdf NX4OB 2022 en_US (the
#         same production file: identical proof marks dated 2022-11-01) + full_pdf NX4OB 2023 en_US (Copyright 2023,
#         not assigned to a model year; cross-check only): specification and schedule pages identical.
#   2024  full_pdf NX4OB 2024 en_US (Copyright 2023; the portal serves no 2024 book) - accepted as the 2024 book by
#         ruling on support, not proof - cross-checked against full_pdf NX4OB 2023 en_US: no value contradicted.
#   2025  full_pdf NX4OB 2025 en_US, book header '_NX4aOB_en_US' (Copyright 2024, created 2024-10-17), single print.
#   Each book was identified by the pickup body on its rear exterior overview (page renders), the engine table
#   (Smartstream G2.5 GDI + G2.5 T-GDI, 2,497 cc, '4, in-line') and the wheelbase (118.30 in).
# ** Rulings 2026-11-14, reasons live HERE and in the source suffix only:
#    LABELS ("Accept, start dry run"): NX4OB/2024 is the 2024 source; NX4OB/2023 is a cross-check for 2023 AND 2024 -
#       a value is written for either year only where that file does not contradict it.
#    EDITION CONFLICT 2022 (standing whole-row rule): the automatic-transmission-fluid schedule line is 'No check, No
#       service required' in the June 2021 print and 'Replace every 60,000 miles' in the December 2021 print -> no row.
#    NEW ROW TYPE ("Go, as recommended"): the 2023 and 2024 normal schedules print 'Automatic transmission fluid:
#       Replace every 60,000 miles' in every print -> written, mileage only. The 2025 book prints 'No check, No
#       service required' -> no row.
#    2025 DUAL-CLUTCH BLOCK ("Go, as recommended"): p.10-7 prints gear oil 2.53-2.64 US qt (2.45-2.50 L) and control
#       oil 3.5-3.6 US qt (3.3-3.4 L) with ONE fluid name; the 2022-2024 books assign the two quantities the other way
#       round and name two fluids; no second 2025 print exists -> the 2025 dual-clutch fluid name and quantities are
#       not written.
#    UNITS / WORDING AS PRINTED (standing): 2025 prints 'Rear differential oil (4WD)' and 'Transfer case oil (4WD)',
#       the earlier books '(AWD)'; the 2022 cabin-filter line is printed '16,000 miles or 12 months', the later grids
#       mark 24-month steps.
# ** Wheel nut torque: the 2022 and 2023 books print lbf-ft and kgf-m only -> torque_nm stays NULL for those years
#    (precedent: Santa Fe 2005 / 2006, Sonata 2006); the 2024 and 2025 books also print 107-127 N-m.
# ** The 2025 book spells the Hyundai genuine ATF brand 'SP4-M1'; the three other brands are printed 'SP4M-1'. Only
#    the three are named for 2025.
# ** Gates (null): spark-plug part number / gap (not published; interval only); 12V battery (each book shows only an
#    example capacity label); brake-fluid quantity 2022-2024 (printed 'As required'); EPS / MDPS - no fluid.
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows (checked BEFORE
#    commit). S1.12 / S1.11: no bookkeeping words in shipped columns; battery_notes NULL; diff JSON = [{location, fluid_type}].
#
# Usage:  python _write_hyundai_santa_cruz_2022_2025.py            -> DRY RUN: print every row, classify every source
#         python _write_hyundai_santa_cruz_2022_2025.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
# the 2025 dual-clutch block (ruling) and the misspelt brand: never in a shipped column
NOT_WRITTEN = re.compile(r"2\.53|3\.5-3\.6|SP4-M1")
TABLES = ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]
TARGETS = {38727: 2022, 38728: 2023, 38729: 2024, 38730: 2025}

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Santa Cruz'")}
_c.close()
assert sorted(VEHICLES) == [9981, 38727, 38728, 38729, 38730], ("the Santa Cruz rows are not the five expected", sorted(VEHICLES))
for _vid, _year in TARGETS.items():
    assert VEHICLES[_vid] == (_year, "Hyundai", "Santa Cruz"), (_vid, VEHICLES[_vid])

G25, G25T = "Smartstream G2.5 GDI", "Smartstream G2.5 T-GDI"
EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL = "Mixture of antifreeze and water; ethylene glycol base coolant for aluminum radiator"
BRAKE_LV = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
LUG_NOTE_FULL = "79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)"
LUG_NOTE_KGF = "79 to 94 lb-ft (11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)"
PORTAL = "owners.hyundaiusa.com glovebox-manual"
GLOBAL = "ownersmanual.hyundai.com full_pdf NX4OB %s en_US"

def diff(*pairs):
    return json.dumps([{"location": loc, "fluid_type": fl} for loc, fl in pairs], ensure_ascii=False)

OIL = dict(visc="0W-20 (" + G25 + ") / 0W-30 (" + G25T + ")", type="Full synthetic (required)",
           cap="6.13 qt / 5.8 L (" + G25 + ") / 6.13 qt / 5.8 L (" + G25T + ")",
           spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API SN PLUS or above); SAE 0W-20 (" + G25
                + ") / SAE 0W-30 (" + G25T + ")")
TIRES = "245/60R18 or 245/50R20"
NOTE = ("18-in wheels: 245/60R18; 20-in wheels: 245/50R20; 35 psi front and rear at normal and maximum load. "
        "Compact spare %sT135/80D18 at 60 psi. Fuel tank 17.69 gal / 67 L.")
COOL_CAP = "10.00 qt / 9.46 L (" + G25 + ") / 9.12 qt / 8.63 L (" + G25T + ")"
DIFF_AWD = diff(("Rear differential (AWD)", GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L"),
                ("Transfer case (AWD)", GL5_85 + "; 0.66-0.72 qt / 0.62-0.68 L (" + G25 + "), 0.51-0.55 qt / 0.48-0.52 L ("
                 + G25T + ")"))
ATF_ROW = "Automatic transmission fluid replacement"
SELF_ID = ("NX4OB, self-ID engine table p.2-8 Smartstream G 2.5 GDI + Smartstream G 2.5 T-GDI 2,497cc '4, in-line', "
           "wheelbase 118.30 in, pickup body with its bed on the exterior overview p.2-3")
PLUG_GATE = "spark-plug part number and gap (not published, interval only), battery notes"

def maint_2023_2024():
    return [
        (8000, 12, "Engine oil & filter change", "9-9"),
        (96000, None, "Spark plug replacement (" + G25 + ")", "9-10"),
        (48000, 72, "Spark plug replacement (" + G25T + ")", "9-10"),
        (24000, 36, "Engine air cleaner filter replacement", "9-10"),
        (16000, 24, "Cabin air filter replacement", "9-12"),
        (8000, 12, "Tire rotation", "9-12"),
        (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-11"),
        (48000, 48, "Brake fluid replacement", "9-11"),
        (60000, None, ATF_ROW, "9-12"),
    ]

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=38727, label="2022 NX4OB  " + G25 + " + " + G25T, psi=35, lug_nm=None, lug_note=LUG_NOTE_KGF,
  oil=dict(OIL),
  fluids=dict(
   trans="Automatic transmission: ATF SP-IV (MICHANG, SK, NOCA, Hyundai genuine or other approved brands meeting the "
         "spec), 6.87 qt / 6.5 L. Dual clutch transmission (" + G25T + "): gear oil GS WDCTF HD G (WDGO-1), "
         "3.49-3.59 qt / 3.3-3.4 L; control oil GS WDCTF HD H (WDHO-1), 2.59-2.64 qt / 2.45-2.50 L.",
   brake=BRAKE_LV, cool_type=COOL, cool_cap=COOL_CAP, diff=DIFF_AWD),
  parts=dict(tire=TIRES, note=NOTE % ""),
  src="owner-manual-verified (per 2022 Hyundai Santa Cruz OM, portal file 2022-Santa-Cruz-Owners-Manual.pdf = "
      "santa_cruz_2022_portal_OM.pdf, " + PORTAL + ", PDF title '2022 Santa Cruz Owners Manual', Copyright 2021 HYUNDAI "
      "Motor America, PDF created 2021-06-08 (first print; 2022 is the Santa Cruz's first model year), cross-checked "
      "against the December 2021 print " + (GLOBAL % "2021") + " = santa_cruz_2021_NX4OB_global_OM.pdf (Copyright 2021, "
      "proof marks dated 2021-12-23; no 2021 Santa Cruz exists): the specification pages are identical and the "
      "schedule differs on one line; " + SELF_ID + "; tires + wheel nut torque p.2-10 (printed in lbf-ft and kgf-m "
      "only), capacities p.2-12, viscosity chart p.2-13 read from a page render; schedule p.9-8 to 9-11, grids read "
      "from upright page renders of both prints; the automatic-transmission-fluid schedule line is not written because "
      "the two prints disagree (June print p.9-11 'No check, No service required', December print 'Replace every "
      "60,000 miles'; standing ruling: a disputed interval is left out as a whole row); gated to null: brake-fluid "
      "quantity (printed 'As required'), 12V battery group and CCA (p.9-32 shows only an example capacity label "
      "MF68L-DIN), " + PLUG_GATE + ")",
  msrc="Hyundai Owner's Manual (Santa Cruz 2022 NX4OB, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-8"),
   (96000, None, "Spark plug replacement (" + G25 + ")", "9-9"),
   (48000, 72, "Spark plug replacement (" + G25T + ")", "9-9"),
   (24000, 36, "Engine air cleaner filter replacement", "9-9"),
   (16000, 12, "Cabin air filter replacement", "9-11"),
   (8000, 12, "Tire rotation", "9-11"),
   (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-10"),
   (48000, 48, "Brake fluid replacement", "9-10"),
  ]),

 dict(vid=38728, label="2023 NX4OB  " + G25 + " + " + G25T, psi=35, lug_nm=None, lug_note=LUG_NOTE_KGF,
  oil=dict(OIL),
  fluids=dict(
   trans="Automatic transmission: ATF SP4M-1 (SK, MICHANG, S-OIL, Hyundai genuine), 6.87 qt / 6.5 L. Dual clutch "
         "transmission (" + G25T + "): gear oil GS WDCTF HD G (GS Caltex), 3.4-3.6 qt / 3.3-3.4 L; control oil GS WDCTF "
         "HD H (GS Caltex), 2.58-2.64 qt / 2.45-2.50 L.",
   brake=BRAKE_LV, cool_type=COOL, cool_cap=COOL_CAP, diff=DIFF_AWD),
  parts=dict(tire=TIRES, note=NOTE % ""),
  src="owner-manual-verified (per 2023 Hyundai Santa Cruz OM, portal file '2023-Santa Cruz-OM.pdf' = "
      "santa_cruz_2023_portal_OM.pdf, " + PORTAL + ", Copyright 2022 HYUNDAI Motor America, PDF created 2022-11-17 "
      "(first print), cross-checked against " + (GLOBAL % "2022") + " = santa_cruz_2022_NX4OB_global_OM.pdf (the same "
      "production file: identical proof marks dated 2022-11-01) and " + (GLOBAL % "2023") + " = "
      "santa_cruz_2023_NX4OB_global_OM.pdf (Copyright 2023; a file not assigned to a model year, used as a cross-check "
      "by ruling 2026-11-14): every specification and schedule page is identical; " + SELF_ID + "; tires + wheel nut "
      "torque p.2-10 (printed in lbf-ft and kgf-m only), capacities p.2-12, viscosity chart p.2-13 read from a page "
      "render; schedule p.9-9 to 9-12, grids read from upright page renders; the normal schedule prints 'Automatic "
      "transmission fluid: Replace every 60,000 miles' on p.9-12 in all three files, written by ruling 2026-11-14; "
      "gated to null: brake-fluid quantity (printed 'As required'), 12V battery group and CCA (p.9-33 shows only an "
      "example capacity label MF68L-DIN), " + PLUG_GATE + ")",
  msrc="Hyundai Owner's Manual (Santa Cruz 2023 NX4OB, p.%s)",
  maint=maint_2023_2024()),

 dict(vid=38729, label="2024 NX4OB  " + G25 + " + " + G25T, psi=35, lug_nm=107.0, lug_note=LUG_NOTE_FULL,
  oil=dict(OIL),
  fluids=dict(
   trans="Automatic transmission: ATF SP4M-1 (SK, MICHANG, S-OIL, Hyundai genuine), 6.87 qt / 6.5 L. Dual clutch "
         "transmission (" + G25T + "): gear oil GS WDCTF HD G (GS Caltex), 3.4-3.6 qt / 3.3-3.4 L; control oil GS WDCTF "
         "HD H (GS Caltex), 2.58-2.64 qt / 2.45-2.50 L.",
   brake=BRAKE_LV, cool_type=COOL, cool_cap=COOL_CAP, diff=DIFF_AWD),
  parts=dict(tire=TIRES, note=NOTE % ""),
  src="owner-manual-verified (per 2024 Hyundai Santa Cruz OM, " + (GLOBAL % "2024") + " = "
      "santa_cruz_2024_NX4OB_global_OM.pdf, Copyright 2023 HYUNDAI Motor America; the US portal serves no 2024 book (168 "
      "file-name forms, every answer HTTP 404); accepted as the 2024 book by ruling 2026-11-14 on support, not proof "
      "(filed as 2024, first-print copyright, pre-facelift body, sections that only the 2024 books of other nameplates "
      "carry); cross-checked against " + (GLOBAL % "2023") + " = santa_cruz_2023_NX4OB_global_OM.pdf (Copyright 2023; a "
      "file not assigned to a model year): no written value is contradicted; " + SELF_ID + "; tires + wheel nut torque "
      "p.2-10, capacities p.2-12, viscosity chart p.2-13 read from a page render; schedule p.9-9 to 9-12, grids read "
      "from upright page renders; the normal schedule prints 'Automatic transmission fluid: Replace every 60,000 miles' "
      "on p.9-12 in both files, written by ruling 2026-11-14; gated to null: brake-fluid quantity (printed 'As "
      "required'), 12V battery group and CCA (p.9-33 shows only an example capacity label MF68L-DIN), " + PLUG_GATE + ")",
  msrc="Hyundai Owner's Manual (Santa Cruz 2024 NX4OB, p.%s)",
  maint=maint_2023_2024()),

 dict(vid=38730, label="2025 NX4OB facelift  " + G25 + " + " + G25T, psi=35, lug_nm=107.0, lug_note=LUG_NOTE_FULL,
  oil=dict(OIL),
  fluids=dict(
   trans="Automatic transmission: ATF SP4M-1 (SK, MICHANG, S-OIL), 6.87 qt / 6.5 L.",
   brake=BRAKE_LV + "; 0.87 qt / 0.82 L", cool_type=COOL,
   cool_cap="10 qt / 9.5 L (" + G25 + ") / 9.09 qt / 8.6 L (" + G25T + ")",
   diff=diff(("Rear differential (4WD)", GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L"),
             ("Transfer case (4WD)", GL5_85 + "; 0.65-0.71 qt / 0.62-0.68 L (automatic transmission), 0.49-0.55 qt / "
              "0.47-0.52 L (dual clutch transmission)"))),
  parts=dict(tire=TIRES, note=NOTE % "(if equipped) "),
  src="owner-manual-verified (per 2025 Hyundai Santa Cruz OM, " + (GLOBAL % "2025") + " = "
      "santa_cruz_2025_NX4OB_global_OM.pdf, book header '_NX4aOB_en_US', Copyright 2024 HYUNDAI Motor America, PDF "
      "created 2024-10-17, single available print (served by the host but not on its US menu; the US portal serves no "
      "2025 book); NX4OB facelift, self-ID engine table p.10-2 Smartstream G2.5 GDI + Smartstream G2.5 T-GDI 2,497cc "
      "'4, in-line', wheelbase 118.30 in, pickup body with its bed on the exterior overview p.2-3; tires + wheel nut "
      "torque p.10-4, capacities p.10-7/10-8 read from the text and a page render, viscosity chart p.10-9 read from a "
      "page render; schedule p.9-11 to 9-15, sparse grid rows read from page renders; the book prints 'Rear "
      "differential oil (4WD)' and 'Transfer case oil (4WD)', written as printed; the automatic and dual-clutch "
      "transmission fluid schedule lines p.9-14 read 'No check, No service required'; gated to null: dual-clutch "
      "transmission fluid name and quantities (p.10-7 assigns the gear-oil and control-oil quantities the other way "
      "round from the 2022-2024 books and names one fluid for both; left out by ruling 2026-11-14), the Hyundai genuine "
      "ATF brand (printed with a different spelling), 12V battery group and CCA (p.9-33 shows only an example capacity "
      "label MF68R-DIN), " + PLUG_GATE + ")",
  msrc="Hyundai Owner's Manual (Santa Cruz 2025 NX4OB, p.%s)",
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
assert sorted(r["vid"] for r in ROWS) == sorted(TARGETS), "this script writes the four new Santa Cruz rows and nothing else"
EXPECT = {2022: 8, 2023: 9, 2024: 9, 2025: 8}                                  # schedule lines per year

# ---------------------------------------------------------------------------------------------------------------
def unit_pairs(vid, s):
    """Every printed US / metric pair must convert, within print rounding (ranges end to end). Returns pairs checked."""
    n = 0
    for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
        qs, ls = q.split("-"), l.split("-")
        assert len(qs) == len(ls), (vid, "qt/L range shape", q, l)
        for a, b in zip(qs, ls):                                  # 1 L = 1.0567 US qt
            assert abs(float(a) - float(b) * 1.0567) <= 0.09, (vid, "qt/L mismatch", q, l, s)
            if float(a) < 1.0:                                    # small quantities: the absolute test is too loose,
                ratio = float(a) / float(b)                       # so the direction of the conversion is tested too
                assert 1.03 <= ratio <= 1.09, (vid, "qt/L ratio", q, l, ratio)
            n += 1
    for g, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) gal / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
        gs, ls = g.split("-"), l.split("-")
        assert len(gs) == len(ls), (vid, "gal/L range shape", g, l)
        for a, b in zip(gs, ls):                                  # 1 US gal = 3.7854 L
            gdec = len(a.split(".")[1]) if "." in a else 0
            ldec = len(b.split(".")[1]) if "." in b else 0
            # tolerance = half a unit in the last printed place of EACH figure (the litre one converted), plus a
            # truncation allowance; a whole-litre figure such as 67 L therefore allows +-0.13 gal
            tol = 0.5 * 10 ** -gdec + (0.5 * 10 ** -ldec) / 3.7854 + 0.005
            assert abs(float(a) - float(b) / 3.7854) <= tol, (vid, "gal/L mismatch", g, l, s)
            n += 1
    assert not re.search(r"[0-9] (?:qt|gal)(?! /)", s or ""), (vid, "unpaired US unit", s)
    return n

def check(row):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid = row["vid"]
    year = int(row["label"][:4])
    assert VEHICLES.get(vid) == (year, "Hyundai", "Santa Cruz") and TARGETS.get(vid) == year, (vid, "target row is not the labelled vehicle")
    assert ("per %d Hyundai Santa Cruz OM" % year) in row["src"] and ("Santa Cruz %d " % year) in row["msrc"], (vid, "source year")
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    assert len(row["maint"]) == EXPECT[year], (vid, "schedule lines", len(row["maint"]))
    for mi, mo, desc, page in row["maint"]:
        assert re.fullmatch(r"9-\d{1,2}", page), (vid, desc, page, "schedule pages are in chapter 9")
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert isinstance(mi, int) and mi > 0, (vid, desc)
        assert mo is None or (isinstance(mo, int) and mo > 0), (vid, desc)
    by = {d: (mi, mo) for mi, mo, d, _ in row["maint"]}
    assert len(by) == len(row["maint"]), (vid, "duplicate schedule description")
    assert (ATF_ROW in by) == (year in (2023, 2024)), (vid, "the transmission-fluid row belongs to 2023 and 2024 only")
    if ATF_ROW in by:
        assert by[ATF_ROW] == (60000, None), (vid, by[ATF_ROW])
    assert by["Cabin air filter replacement"] == (16000, 12 if year == 2022 else 24), (vid, "cabin filter months as printed")
    assert by["Brake fluid replacement"] == (48000, 48) and by["Engine oil & filter change"] == (8000, 12), vid
    o, f, p = row["oil"], row["fluids"], row["parts"]
    locs = [e["location"] for e in json.loads(f["diff"])]
    assert locs == (["Rear differential (4WD)", "Transfer case (4WD)"] if year == 2025 else
                    ["Rear differential (AWD)", "Transfer case (AWD)"]), (vid, locs)
    if year == 2022:
        assert "ATF SP-IV" in f["trans"] and "SP4M" not in f["trans"] and "WDGO-1" in f["trans"], vid
    else:
        assert "ATF SP4M-1" in f["trans"] and "SP-IV" not in f["trans"], vid
    if year == 2025:                    # ruling: the dual-clutch fluid name and quantities are not written
        assert "clutch" not in f["trans"].lower() and "WDCTF" not in f["trans"] and "Hyundai genuine" not in f["trans"], vid
        assert f["brake"] == BRAKE_LV + "; 0.87 qt / 0.82 L" and f["cool_cap"].startswith("10 qt / 9.5 L"), vid
        assert "(if equipped)" in p["note"], vid
    else:
        assert "Dual clutch transmission (" + G25T + "): gear oil GS WDCTF HD G" in f["trans"] and "control oil GS WDCTF HD H" in f["trans"], vid
        assert f["brake"] == BRAKE_LV and f["cool_cap"] == COOL_CAP and "(if equipped)" not in p["note"], vid
    # wheel nut: N-m only where that year's book prints it
    assert (row["lug_nm"] is None and "N-m" not in row["lug_note"]) if year in (2022, 2023) else \
           (row["lug_nm"] == 107.0 and "107 to 127 N-m" in row["lug_note"]), (vid, "wheel nut units as printed")
    shipped = [o["visc"], o["type"], o["cap"], o["spec"], f["trans"], f["brake"], f["cool_type"], f["cool_cap"],
               p["tire"], p["note"], row["lug_note"], EPS] + [d for _, _, d, _ in row["maint"]]
    for e in json.loads(f["diff"]):
        assert set(e) == {"location", "fluid_type"}, (vid, e)
        shipped += [e["location"], e["fluid_type"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
            assert not NOT_WRITTEN.search(s), (vid, "a value left out by ruling is in a shipped column", s)
    assert row["src"] != BARE and row["src"].startswith(BARE + " (") and row["src"].endswith(")")
    assert isinstance(row["psi"], int)
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
              (vid, "lug_nut", 79.0, row["lug_nm"], row["lug_note"], row["src"]))
    for mi, mo, desc, page in row["maint"]:
        c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,"
                  "difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (nid, vid, mi, mo, desc, row["msrc"] % page, "standard", None, None, None))
        nid += 1
    return nid

def show(row):
    o, f, p = row["oil"], row["fluids"], row["parts"]
    print("\n=== %d  Santa Cruz %s" % (row["vid"], row["label"]))
    print("  oil   : %s | %s | %s" % (o["cap"], o["visc"], o["type"]))
    print("  spec  : %s" % o["spec"])
    print("  trans : %s" % f["trans"])
    print("  cool  : %s | %s" % (f["cool_cap"], f["cool_type"]))
    print("  brake : %s" % f["brake"])
    for e in json.loads(f["diff"]):
        print("  diff  : %s -> %s" % (e["location"], e["fluid_type"]))
    print("  tires : %s @ %s psi | %s" % (p["tire"], row["psi"], p["note"]))
    print("  lug   : 79.0 lb-ft / %s N-m | %s" % (row["lug_nm"], row["lug_note"]))
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

bak = DB + ".bak_santa_cruz_2022_2025_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
try:
    nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
    for row in ROWS:
        nid = write(c, nid, row)
        print("  wrote %d  Santa Cruz %s" % (row["vid"], row["label"]))
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
    t = c.execute("SELECT component, torque_ft_lbs, source, torque_nm FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), MIN(source) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and e == 0, vid
    assert f[0][1] is None and len(json.loads(f[0][2])) == 2 and p[0][3] is None and p[0][4] is None and p[0][5] is None, vid
    assert t[0][2].startswith(BARE + " (") and classify(t[0][2], "torque_specs", vid) == 1 and t[0][3] == row["lug_nm"]
    for tb in ("oil_change", "fluids", "parts", "maintenance", "torque_specs"):
        for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)):
            assert classify(s, tb, vid) == 1, (vid, tb, s[:60])
    g = [c.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id=?" % tb, (vid,)).fetchone()[0]
         for tb in ("fuel_economy", "recalls", "safety_ratings", "complaints")]
    print("  %d: oil=%s | cool=%s | brake=%s | tire=%s @%s | lug=%s / %s | maint=%d | government rows %s"
          % (vid, o[0][0][:30], f[0][0][:26], f[0][3][:26], p[0][0], p[0][1], t[0][1], t[0][3], m[0], g))
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare_count(c))
db.close()
print("DONE - %d rows written." % len(ROWS))
