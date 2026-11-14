# Hyundai Palisade - SIXTH Hyundai slice. 6 model years written, none deferred.
# Written: 2020 / 2021 / 2022 LX2 (ids 676 / 2169 / 3697), 2024 / 2025 LX2 facelift (ids 6790 / 8365),
#          2026 LX3 (id 9979). There is no 2023 row in the vehicles table.
# Sources (both manufacturer, free, citable), saved under _hyundai_manuals/palisade/ (gitignored); reads 2026-11-14:
#   * US portal owners.hyundaiusa.com glovebox-manual (first print, PDF Title names the model year): 2020, 2021, 2022.
#   * ownersmanual.hyundai.com full_pdf/<PLATFORM>/<label>/en_US: 2024, 2025 (LX2), 2026 (LX3), and the later-print
#     cross-check copies for 2021 / 2022. For Palisade the label in the URL IS the model year: labels 2021, 2022 and 2023
#     each match the portal book whose Title names that year (checked page by page). Labels 2024 / 2025 have no titled
#     portal book; accepted as those model years by ruling 2026-11-14 ("Accept, go read").
# ** Rulings 2026-11-14 ("Go, write Palisade"), reasons live HERE and in the source suffix only:
#    R1 WHOLE ROWS ONLY - a maintenance row whose interval the first print and the later print dispute is not written:
#       2021 brake fluid (first print grid 30,000 mi / 48 months, later print '60,000 miles or 48 months');
#       2022 oil, air cleaner, tire rotation, cabin filter and the coolant 'thereafter' interval (first print grid in
#       7,500-mile steps, later print in 8,000-mile steps). 2022 keeps what both prints state identically: spark plugs,
#       brake fluid, first coolant replacement.
#    R2 UNITS AS PRINTED - both 2022 prints give capacities in US gallons and litres; they are written that way and
#       checked with a gallon twin of the quart check (1 US gal = 3.7854 L). No quart figure is computed here.
#    R3 2021 quarts (first print) and gallons (later print) beside the same litres are one quantity -> quarts written.
#    R4 2026 battery page is a capacity-label illustration like 2024 / 2025 -> not written.
# ** Gates (null): spark-plug part number / gap (no book publishes them; interval only); 12V battery (2020-2022 no
#    spec; 2024-2026 only a capacity-label illustration); EPS / MDPS - no power-steering fluid; 2026 Hybrid (own manual).
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows.
# ** S1.12 / S1.11: no bookkeeping words in shipped columns; battery_notes NULL; diff JSON = [{location, fluid_type}].
#
# Usage:  python _write_hyundai_palisade.py            -> DRY RUN: print every row, classify every source, write nothing
#         python _write_hyundai_palisade.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Palisade'")}
_c.close()

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_PHOS = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
COOL_EG = "Mixture of antifreeze and water; ethylene glycol base coolant for aluminum radiator"
BRAKE_LV = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
ATF_SP4 = "ATF SP-IV (MICHANG, SK, NOCA, Hyundai genuine or other approved brands meeting the spec)"
ATF_SP4M = "ATF SP4M-1 (SK, MICHANG, S-OIL, Hyundai genuine or other approved brands meeting the spec)"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
LUG_HMG = dict(ftlb=79.0, nm=107.0,
               note="79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)")
V38, G35 = "3.8 GDI", "Smartstream G3.5 GDi"
PORTAL = "owners.hyundaiusa.com glovebox-manual"
GLOBAL = "ownersmanual.hyundai.com full_pdf %s %s en_US"
NO_PLUG_BATT = "spark-plug part number and gap (not published, interval only), battery notes"
NO_BATT_SPEC = "12V battery group and CCA (not published)"
LABEL_RULING = ("the host's year label is accepted as the model year by ruling 2026-11-14, after its labels 2021, 2022 "
                "and 2023 each matched the US-portal book whose PDF title names that year")

def diff(*pairs):
    return json.dumps([{"location": loc, "fluid_type": fl} for loc, fl in pairs], ensure_ascii=False)

# ---- LX2 pre-facelift (2020 / 2021 / 2022) ---------------------------------------------------------------------
LX2_SPEC = "ACEA A5 or above; where ACEA A5 oil is not available, API SM and ILSAC GF-4 (or above) or ACEA A3; SAE 5W-30"
LX2_TIRE = "245/60R18 or 245/50R20"
LX2_NOTE = ("18-in wheels: 245/60R18; 20-in wheels: 245/50R20; 35 psi front and rear. Compact spare T155/90R18 at "
            "60 psi. Fuel tank 18.75 gal / 71 L.")
def lx2_oil(visc, cap):
    return dict(visc=visc, type=None, cap=cap + " (" + V38 + ")", cap_wo=None, spec=LX2_SPEC)
def lx2_fluids(atf_cap, cool_cap, gear_cap):
    return dict(trans="Automatic transmission: " + ATF_SP4 + ", " + atf_cap + ".",
                brake="FMVSS 116 DOT-4", cool_type=COOL_PHOS, cool_cap=cool_cap + " (" + V38 + ")", ps=EPS,
                diff=diff(("Rear differential (AWD)", GL5_85 + ", " + gear_cap),
                          ("Transfer case (AWD)", GL5_85 + ", " + gear_cap)))
LX2_PARTS = dict(tire=LX2_TIRE, note=LX2_NOTE)
# 2020 and 2021: each book read on its own pages; the printed intervals are the same in both.
LX2_MAINT_75 = [
    (7500, 12, "Engine oil & filter change", "7-8"),
    (97500, None, "Spark plug replacement", "7-8"),
    (22500, 36, "Engine air cleaner filter replacement", "7-8"),
    (7500, 12, "Climate control (cabin) air filter replacement", "7-9"),
    (7500, None, "Tire rotation", "7-8"),
    (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-9"),
]

# ---- LX2 facelift (2024 / 2025) --------------------------------------------------------------------------------
PE_OIL = dict(visc="5W-30", type="Full synthetic (required)", cap="6.86 qt / 6.5 L (" + V38 + ")", cap_wo=None,
              spec="ACEA A5 or above; API latest (or ILSAC latest) or ACEA A5/B5 full synthetic required; SAE 5W-30")
PE_FLUIDS = dict(trans="Automatic transmission: " + ATF_SP4M + ", 7.39 qt / 7.0 L.",
                 brake=BRAKE_LV, cool_type=COOL_PHOS,
                 cool_cap="12.44 qt / 11.79 L (without trailer) / 12.65 qt / 11.98 L (with trailer)", ps=EPS,
                 diff=diff(("Rear differential", GL5_85 + ", 0.73 qt / 0.7 L"),
                           ("Transfer case (AWD)", GL5_85 + ", 0.73 qt / 0.7 L")))
PE_PARTS = dict(tire=LX2_TIRE,
                note="18-in wheels: 245/60R18; 20-in wheels: 245/50R20; 35 psi front and rear at normal and maximum "
                     "load. Compact spare T155/90R18 at 60 psi. Fuel tank 18.75 gal / 71 L.")
def maint_8k(cabin, p1, p2, p3):
    return [
        (8000, 12, "Engine oil & filter change", p1),
        (96000, None, "Spark plug replacement", p1),
        (24000, 36, "Engine air cleaner filter replacement", p1),
        cabin + ("Cabin air filter replacement", p2),
        (8000, 12, "Tire rotation", p1),
        (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", p2),
        (48000, 48, "Brake fluid replacement", p3),
    ]
PE_GATES = ("12V battery group and CCA (p.9-29 shows only a capacity-label illustration, AGM80L-DIN, captioned 'the "
            "actual battery label in the vehicle may differ from the illustration'), " + NO_PLUG_BATT)

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=676, label="2020 LX2  3.8 GDI", psi=35, lug=LUG_HMG,
  oil=lx2_oil("5W-30 (recommended); 10W-30 above 0 F", "6.87 qt / 6.5 L"),
  fluids=lx2_fluids("7.4 qt / 7.0 L", "9.4 qt / 8.9 L", "0.74 qt / 0.7 L"), parts=LX2_PARTS,
  src="owner-manual-verified (per 2020 Hyundai Palisade OM, portal file '2020 Palisade Owner's Manual.pdf' = "
      "palisade_2020_portal_OM.pdf, " + PORTAL + ", PDF title '2020 Palisade Owner's Manual', Copyright 2019 HYUNDAI "
      "Motor America; LX2, self-ID p.8-2 3.8 GDI 3,778cc, wheelbase 114.17 in; capacities p.8-7/8-8, viscosity chart "
      "p.8-9 read from a page render, tires + lug torque p.8-5; single print (the second host has no 2020 book); gated "
      "to null: " + NO_BATT_SPEC + ", " + NO_PLUG_BATT + ")",
  msrc="Hyundai Owner's Manual (Palisade 2020 LX2, p.%s)", maint=LX2_MAINT_75),

 dict(vid=2169, label="2021 LX2  3.8 GDI", psi=35, lug=LUG_HMG,
  oil=lx2_oil("5W-30 (recommended); 10W-30 above 0 F", "6.87 qt / 6.5 L"),
  fluids=lx2_fluids("7.4 qt / 7.0 L", "9.4 qt / 8.9 L", "0.74 qt / 0.7 L"), parts=LX2_PARTS,
  src="owner-manual-verified (per 2021 Hyundai Palisade OM, portal file 2021-Palisade-Owners-Manual.pdf = "
      "palisade_2021_portal_OM.pdf, " + PORTAL + ", PDF title '2021 Palisade Owners Manual', Copyright 2020 HYUNDAI "
      "Motor America; LX2, self-ID p.8-2 3.8 GDI 3,778cc, wheelbase 114.17 in; capacities p.8-7/8-8, viscosity chart "
      "p.8-9 read from a page render, tires + lug torque p.8-5; cross-checked against the later print "
      + (GLOBAL % ("LX2", "2021")) + " (Copyright 2021): every written value identical; the later print states the "
      "same litre quantities in US gallons where the first print states US quarts (one quantity, ruling 2026-11-14); "
      "gated to null: brake-fluid replacement interval (first print grid 30,000 mi / 48 months, later print 60,000 mi "
      "/ 48 months), " + NO_BATT_SPEC + ", " + NO_PLUG_BATT + ")",
  msrc="Hyundai Owner's Manual (Palisade 2021 LX2, p.%s)", maint=LX2_MAINT_75),

 dict(vid=3697, label="2022 LX2  3.8 GDI", psi=35, lug=LUG_HMG,
  oil=lx2_oil("5W-30", "1.71 gal / 6.5 L"),
  fluids=lx2_fluids("1.85 gal / 7.0 L", "2.35 gal / 8.9 L", "0.19 gal / 0.7 L"), parts=LX2_PARTS,
  src="owner-manual-verified (per 2022 Hyundai Palisade OM, portal file 2022-Palisade-Owners-Manual.pdf = "
      "palisade_2022_portal_OM.pdf, " + PORTAL + ", PDF title '2022 Palisade Owner's Manual', Copyright 2021 HYUNDAI "
      "Motor America; LX2, self-ID p.8-2 3.8 GDI 3,778cc, wheelbase 114.17 in; capacities p.8-7/8-8 are printed in US "
      "gallons and litres and are written as printed (ruling 2026-11-14), viscosity chart p.8-9 read from a page "
      "render, tires + lug torque p.8-5; cross-checked against the later print " + (GLOBAL % ("LX2", "2022"))
      + " (Copyright 2021): specification pages agree; the two prints dispute the maintenance grid (first print in "
      "7,500-mile steps, later print in 8,000-mile steps), so only the intervals both prints state identically are "
      "written - spark plugs, brake fluid, first coolant replacement (ruling 2026-11-14); gated to null: oil-change, "
      "air-cleaner, tire-rotation and cabin-filter intervals and the coolant interval after the first replacement, "
      + NO_BATT_SPEC + ", " + NO_PLUG_BATT + ")",
  msrc="Hyundai Owner's Manual (Palisade 2022 LX2, p.%s)",
  maint=[
   (96000, None, "Spark plug replacement", "7-8"),
   (120000, 120, "Engine coolant first replacement", "7-9"),
   (48000, 48, "Brake fluid replacement", "7-10"),
  ]),

 dict(vid=6790, label="2024 LX2 facelift  3.8 GDI", psi=35, lug=LUG_HMG,
  oil=PE_OIL, fluids=PE_FLUIDS, parts=PE_PARTS,
  src="owner-manual-verified (per 2024 Hyundai Palisade OM, " + (GLOBAL % ("LX2", "2024")) + " = "
      "palisade_2024_LX2_global_OM.pdf, book header 'LX2_PE_en_US', Copyright 2023 HYUNDAI Motor America, PDF created "
      "2023-10-23, single available print (no US-portal copy exists; " + LABEL_RULING + "); LX2 facelift, self-ID p.2-9 "
      "3.8 GDI 3,778cc, wheelbase 114.17 in, overall length 196.65 in; capacities p.2-13, viscosity chart p.2-14 read "
      "from a page render, tires + wheel nut torque p.2-11; the gear-oil line is printed 'HYPIO GEAR OIL' and is "
      "written as hypoid; gated to null: " + PE_GATES + ")",
  msrc="Hyundai Owner's Manual (Palisade 2024 LX2 facelift, p.%s)",
  maint=maint_8k((16000, 24), "9-9", "9-10", "9-11")),

 dict(vid=8365, label="2025 LX2 facelift  3.8 GDI", psi=35, lug=LUG_HMG,
  oil=PE_OIL, fluids=PE_FLUIDS, parts=PE_PARTS,
  src="owner-manual-verified (per 2025 Hyundai Palisade OM, " + (GLOBAL % ("LX2", "2025")) + " = "
      "palisade_2025_LX2_global_OM.pdf, book header 'LX2_PE_en_US', Copyright 2025 HYUNDAI Motor America, PDF created "
      "2025-04-24, single available print (no US-portal copy exists; " + LABEL_RULING + "); LX2 facelift, self-ID p.2-9 "
      "3.8 GDI 3,778cc, wheelbase 114.17 in, overall length 196.65 in; capacities p.2-13, viscosity chart p.2-14 read "
      "from a page render, tires + wheel nut torque p.2-11; the gear-oil line is printed 'HYPIO GEAR OIL' and is "
      "written as hypoid; the cabin-air-filter interval is printed in months only (p.9-10); gated to null: "
      + PE_GATES + ")",
  msrc="Hyundai Owner's Manual (Palisade 2025 LX2 facelift, p.%s)",
  maint=maint_8k((None, 24), "9-9", "9-10", "9-11")),

 dict(vid=9979, label="2026 LX3  Smartstream G3.5 GDi", psi=None, lug=LUG_HMG,
  oil=dict(visc="0W-20", type="Full synthetic (required)", cap="6.13 qt / 5.8 L (" + G35 + ")", cap_wo=None,
           spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API SN PLUS or above); SAE 0W-20"),
  fluids=dict(trans="Automatic transmission: " + ATF_SP4M + ", 7.39 qt / 7.0 L.",
              brake="DOT-4 (" + BRAKE_LV + ")", cool_type=COOL_EG, cool_cap="12.44 qt / 11.77 L (" + G35 + ")", ps=EPS,
              diff=diff(("Rear differential (AWD)", GL5_85 + ", 0.67 qt / 0.65 L"),
                        ("Transfer case (AWD)", GL5_85 + ", 0.74 qt / 0.7 L"),
                        ("Electronic limited slip differential (e-LSD, XRT Pro)",
                         "Shell TF0870C or equivalent, 0.507 qt / 480 mL"))),
  parts=dict(tire="235/65R18, 255/50R20, 265/45R21 or 255/60R18",
             note="18-in wheels: 235/65R18; 20-in wheels: 255/50R20; 21-in wheels: 265/45R21; 36 psi front and rear at "
                  "normal and maximum load. XRT Pro: 255/60R18 at 35 psi. Spare T155/90R18 at 60 psi. "
                  "Fuel tank 19 gal / 72 L."),
  src="owner-manual-verified (per 2026 Hyundai Palisade OM, " + (GLOBAL % ("LX3", "2026")) + " = "
      "palisade_2026_LX3_global_OM.pdf, PDF keywords '2026,engine,map,HYUNDAI,LX3,en_US', Copyright 2025 HYUNDAI Motor "
      "America, PDF created 2026-06-11, single available print (no US-portal copy exists); LX3, self-ID p.635 "
      "Smartstream G3.5 GDi 3,470cc, wheelbase 116.93 in; capacities p.638, viscosity chart p.639 and tire table p.636 "
      "read from page renders, wheel nut torque p.636; gated to null: 12V battery group and CCA (p.587 shows only a "
      "capacity-label illustration, AGM80L-DIN; ruling 2026-11-14), " + NO_PLUG_BATT + "; Hybrid has its own manual)",
  msrc="Hyundai Owner's Manual (Palisade 2026 LX3, p.%s)",
  maint=maint_8k((16000, 24), "567", "568", "569")),
]
DEFERRED = []

# ---------------------------------------------------------------------------------------------------------------
def check(row):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid = row["vid"]
    want = (int(row["label"][:4]), "Hyundai", "Palisade")
    assert VEHICLES.get(vid) == want, (vid, "target row is not the labelled vehicle", VEHICLES.get(vid), want)
    assert ("per %d Hyundai Palisade OM" % want[0]) in row["src"] and ("Palisade %d " % want[0]) in row["msrc"], (vid, "source year")
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    for mi, mo, desc, page in row["maint"]:
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert mi is None or (isinstance(mi, int) and mi > 0), (vid, desc)
        assert mo is None or (isinstance(mo, int) and mo > 0), (vid, desc)
        assert mi is not None or mo is not None, (vid, desc, "a row needs an interval")
    o, f, p = row["oil"], row["fluids"], row["parts"]
    shipped = [o["visc"], o["type"], o["cap"], o["cap_wo"], o["spec"], f["trans"], f["brake"], f["cool_type"], f["cool_cap"],
               f["ps"], p["tire"], p["note"], p.get("plug_type"), p.get("plug_gap"), p.get("batt_group"),
               row["lug"]["note"]] + [d for _, _, d, _ in row["maint"]]
    for e in json.loads(f["diff"]):
        assert set(e) == {"location", "fluid_type"}, (vid, e)
        shipped += [e["location"], e["fluid_type"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
    assert row["src"] != "owner-manual-verified" and row["src"].startswith("owner-manual-verified (")
    assert row["psi"] is None or isinstance(row["psi"], int)
    # unit sanity on every printed pair that ships, within print rounding:
    #   "<a> qt / <b> L"   1 L = 1.0567 US qt       "<a> gal / <b> L"   1 US gal = 3.7854 L       "<a> qt / <b> mL"
    pairs = 0
    for s in shipped:
        for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
            qs, ls = q.split("-"), l.split("-")
            assert len(qs) == len(ls), (vid, "qt/L range shape", q, l)
            for a, b in zip(qs, ls):          # a range is compared end to end
                assert abs(float(a) - float(b) * 1.0567) <= 0.09, (vid, "qt/L mismatch", q, l, s)
                pairs += 1
        for g, l in re.findall(r"([0-9.]+) gal / ([0-9.]+) L", s or ""):
            assert abs(float(g) - float(l) / 3.7854) <= 0.03, (vid, "gal/L mismatch", g, l, s)
            pairs += 1
        for q, ml in re.findall(r"([0-9.]+) qt / ([0-9.]+) mL", s or ""):
            assert abs(float(q) - float(ml) / 1000.0 * 1.0567) <= 0.09, (vid, "qt/mL mismatch", q, ml, s)
            pairs += 1
        # a capacity must never ship with a unit the checks above do not cover
        assert not re.search(r"[0-9] (?:qt|gal)(?! /)", s or ""), (vid, "unpaired US unit", s)
    return pairs

def write(c, nid, row):
    vid, o, f, p, lug = row["vid"], row["oil"], row["fluids"], row["parts"], row["lug"]
    for t in ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]:
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
              (vid, p.get("plug_type"), p.get("plug_gap"), None, p.get("batt_group"), None, p["tire"], row["psi"], row["psi"],
               None, None, None, None, None, p["note"], None, None, None, None, None, row["src"]))
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
    print("\n=== %d  %s" % (row["vid"], row["label"]))
    print("  oil   : %s | w/o filter: %s | %s | %s" % (o["cap"], o["cap_wo"], o["visc"], o["type"]))
    print("  spec  : %s" % o["spec"])
    print("  trans : %s" % f["trans"])
    print("  cool  : %s | %s" % (f["cool_cap"], f["cool_type"]))
    print("  brake : %s" % f["brake"])
    print("  steer : %s" % f["ps"])
    for e in json.loads(f["diff"]):
        print("  diff  : %s -> %s" % (e["location"], e["fluid_type"]))
    print("  tires : %s @ %s psi | %s" % (p["tire"], row["psi"] if row["psi"] else "per size (see note)", p["note"]))
    print("  plugs : %s | gap %s | battery %s" % (p.get("plug_type"), p.get("plug_gap"), p.get("batt_group")))
    print("  lug   : %s lb-ft / %s N-m | %s" % (row["lug"]["ftlb"], row["lug"]["nm"], row["lug"]["note"]))
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7s mi / %s mo  %s  [p.%s]" % (mi if mi else "--", mo if mo else "--", desc, page))
    print("  src   : %s" % row["src"])

# ---------------------------------------------------------------------------------------------------------------
assert sorted(VEHICLES) == sorted(r["vid"] for r in ROWS), ("Palisade rows in the vehicles table", sorted(VEHICLES))
npairs = sum(check(row) for row in ROWS)
print("contract checks PASS: %d vehicles, %d maintenance rows, %d printed unit pairs converted; every source classified "
      "verified with a suffix; every target id is the labelled vehicle"
      % (len(ROWS), sum(len(r["maint"]) for r in ROWS), npairs))
for row in ROWS:
    show(row)

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_palisade_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
for row in ROWS:
    nid = write(c, nid, row)
    print("  wrote %d  %s" % (row["vid"], row["label"]))
db.commit()

print("\nVerify:")
for row in ROWS:
    vid = row["vid"]
    o = c.execute("SELECT capacity_with_filter, source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchall()
    f = c.execute("SELECT coolant_capacity, differential_fluids_json FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, battery_group, battery_notes FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT component, torque_ft_lbs, source FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), MIN(source) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and e == 0, vid
    assert t[0][2].startswith("owner-manual-verified (") and classify(t[0][2], "torque_specs", vid) == 1
    print("  %d: oil=%s | cool=%s | tire=%s @%s | batt=%s/%s | lug=%s | maint=%d (%s)"
          % (vid, o[0][0][:36], f[0][0][:30], p[0][0], p[0][1], p[0][2], p[0][3], t[0][1], m[0], m[1][:44]))
bare = c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                 "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source='owner-manual-verified'").fetchone()[0]
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare)
assert bare == 424, bare
db.close()
print("DONE - %d Palisade rows written, %d deferred." % (len(ROWS), len(DEFERRED)))
