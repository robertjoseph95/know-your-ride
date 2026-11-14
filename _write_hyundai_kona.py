# Hyundai Kona - FOURTH Hyundai slice, second SUV (subcompact body; inherits the Tucson SUV baseline).
# Written: 2020 / 2021 OS (ids 673 / 2166), 2022 OS facelift (id 3694), 2024 SX2 (id 6787), 2026 SX2 (id 9976).
# The 2026 row replaces a blacklisted row under D1 (blacklisted by source, not by year); it was read from its own
# book on 2026-11-14, reviewed, and approved the same day ("Go, all of it"). First verified 2026 row from a 2026 book.
# Sources (both manufacturer, free, citable):
#   * US portal owners.hyundaiusa.com glovebox-manual (FIRST print): 2020, 2021, 2022 books.
#   * ownersmanual.hyundai.com full_pdf/<PLATFORM>/<MY>/en_US (LATER print; accepted as a verified source by ruling
#     2026-11-14): the only source for SX2 2024 / 2026, and the cross-check copy for OS 2020 / 2021 / 2022.
#   Saved locally under _hyundai_manuals/kona/ (gitignored). Reads + page renders 2026-11-14.
# Self-ID: every book carries the engine table (displacement) + wheelbase on its specifications page - OS 102.36 in
#   (Gamma 1.6 T-GDI 1,591cc + Nu 2.0 MPI 1,999cc; facelift Smartstream G1.6 T-GDi 1,598cc + Smartstream G2.0 Atkinson
#   1,999cc), SX2 104.7 in (same Smartstream pair). Kona N and Kona Electric have their own books and are not here.
# ** Ruling 2026-11-14 ("Go, as recommended") - TWO null rules, reasons live HERE and in the source suffix only:
#    (1) EDITION CONFLICT: where the first print and the later print of the same model-year manual disagree, the
#        value is not written. 2021: Gamma 1.6 T-GDI oil capacity (first print 4.76 qt / 4.5 L, later print 4.23 qt /
#        4.0 L) - only the Nu figure ships. 2022: 1.6T plug interval (47,000 vs 48,000 mi) - row omitted; cabin-filter
#        months (12 vs 24), rotation months (none vs 12), coolant repeat interval (30,000 vs 24,000 mi) - the agreed
#        mileage / first replacement ships, the contested part is left out. 2020: brake-fluid replacement (first print
#        inspect-only, later print 60,000 / 48,000 mi) - no row.
#    (2) UNIT CONFLICT: where the quart and litre figures printed for one capacity do not convert to each other
#        (1 L = 1.057 US qt), the capacity is not written and only the fluid specification ships. 2020 / 2021 transfer
#        case + rear differential; 2022 brake fluid; 2024 / 2026 IVT, rear differential, transfer case.
# ** Gates (null): spark-plug part number / gap (no book publishes one; interval only); 12V battery (2020 / 2021 carry
#    no 12V spec; 2022 p.9-30 and SX2 p.655 / p.685 show only an EXAMPLE capacity label, "the actual battery label in
#    the vehicle may differ from the illustration" - not a vehicle spec); EPS / MDPS - no power-steering fluid.
# ** Standing ruling 2026-11-13: record the OM normal-schedule intervals.
# ** IC-02 registry contract: every row, including lug torque, carries a " (...)" citation suffix; the bare token is
#    frozen at 424 rows. No suffix may contain a blacklist marker - the dry run classifies every source string.
# ** Shipped-text rule (S1.12): no bookkeeping words in any value column; battery_notes stays NULL; diff JSON is
#    written in the renderer's own shape [{location, fluid_type}] (S1.11).
#
# Usage:  python _write_hyundai_kona.py            -> DRY RUN: print every row, classify every source, write nothing
#         python _write_hyundai_kona.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
#   (a row can be parked with hold=True; --with-2026 is the historical flag that also writes parked rows)
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify, SourceRegistryError  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
if WRITE and "--i-know-this-is-superseded" not in sys.argv:      # label audit 2026-11-14
    sys.exit("_write_hyundai_kona.py: rows this script writes were corrected by _fix_hyundai_label_audit_2026_11_14.py; a re-run "
             "would undo that. Pass --i-know-this-is-superseded to proceed, then run the fix script again.")
WITH_2026 = "--with-2026" in sys.argv
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12

# Target-row guard: every id must be the vehicle the label says it is. (The 2026-11-14 audit found the Sonata slice
# had written 2005-manual values to id 35202, which is the model-year-2000 Sonata.)
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Kona'")}
_c.close()

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_OS = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
COOL_OSPE = "Mixture of antifreeze and distilled water; ethylene glycol with phosphate-based coolant for aluminum radiator"
COOL_SX2 = "Mixture of antifreeze and distilled water; ethylene glycol base coolant for aluminum radiator"
BRAKE_LV = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
ATF_SP4 = "ATF SP-IV (MICHANG, SK, NOCA, Hyundai genuine or other approved brands meeting the spec)"
ATF_SP4M1 = "ATF SP4M-1 (SK, MICHANG, S-OIL, Hyundai genuine or other approved brands meeting the spec)"
GL5_90 = "Hypoid gear oil API GL-5 SAE 75W/90 (Shell HD Axle Oil 75W90 or equivalent)"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
LUG_NOTE = "79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)"
NU, GAMMA = "Nu 2.0 MPI", "Gamma 1.6 T-GDI"
S20, S16 = "Smartstream G2.0 Atkinson", "Smartstream G1.6 T-GDi"
PORTAL = "owners.hyundaiusa.com glovebox-manual"
GLOBAL = "ownersmanual.hyundai.com full_pdf %s %s en_US"

def diff(rear, transfer):
    return json.dumps([{"location": "Rear differential (AWD)", "fluid_type": rear},
                       {"location": "Transfer case (AWD)", "fluid_type": transfer}], ensure_ascii=False)

OS_OIL_SPEC = (NU + ": API Latest (ILSAC Latest); SAE 5W-20 recommended, chart also allows 5W-30 / 10W-30 by temperature. "
               + GAMMA + ": API Latest (ILSAC Latest) or ACEA A5/B5; SAE 5W-30 recommended, chart also allows "
               "5W-40 / 10W-30 / 15W-40 / 20W-50 by temperature.")
OS_TRANS = ("Automatic transmission (" + NU + "): " + ATF_SP4 + ", 7.08 qt / 6.7 L. Dual clutch transmission (" + GAMMA
            + "): API GL-4 SAE 70W (HK DCTF 70W, Spirax S6 GHME 70W DCTF or GS DCTF HD 70W), 2.01-2.11 qt / 1.9-2.0 L.")
OS_TIRE_NOTE = ("16-in wheels: 205/60R16; 17-in wheels: 215/55R17; 18-in wheels: 235/45R18; 33 psi front and rear. "
                "Compact spare T125/80D16 at 60 psi. Fuel tank %s.")
SX2_TIRE_NOTE = ("17-in wheels: 215/60R17 at 36 psi; 18-in wheels: 215/55R18 at 33 psi; 19-in wheels: 235/45R19 at 33 psi; "
                 "front and rear, normal and maximum load. Compact spare (if equipped) T145/90D16 at 60 psi. "
                 "Fuel tank 12.4 gal / 47 L (" + S20 + ") / 13.2 gal / 50 L (" + S16 + ").")
SS_OIL = dict(visc="0W-20", type="Full synthetic (required)",
              cap="4.5 qt / 4.3 L (" + S20 + ") / 5.1 qt / 4.8 L (" + S16 + ")",
              spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required; SAE 0W-20 only")
SX2_FLUIDS = dict(
    trans="Automatic transmission (" + S16 + "): " + ATF_SP4M1 + ", 6.8 qt / 6.5 L. Intelligent variable transmission ("
          + S20 + "): CVTF SP-CVT1 (MICHANG or Hyundai genuine).",
    brake="DOT-4", cool_type=COOL_SX2,
    cool_cap="7.3 qt / 6.9 L (" + S20 + ") / 9.0 qt / 8.5 L (" + S16 + ")",
    diff=diff(GL5_85, GL5_85))

def os_maint(brake):
    rows = [
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
    if brake:
        rows += [(60000, 48, "Brake fluid replacement (" + NU + ")", "7-10"),
                 (48000, 48, "Brake fluid replacement (" + GAMMA + ")", "7-15")]
    return rows

def sx2_maint(p_oil, p_plug, p_air, p_cabin, p_misc):
    return [
        (8000, 12, "Engine oil & filter change", p_oil),
        (48000, None, "Spark plug replacement (" + S16 + ")", p_plug),
        (96000, None, "Spark plug replacement (" + S20 + ")", p_plug),
        (24000, 36, "Engine air cleaner filter replacement", p_air),
        (16000, 24, "Cabin air filter replacement", p_cabin),
        (8000, 12, "Tire rotation", p_misc),
        (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", p_misc),
        (48000, 48, "Brake fluid replacement", p_misc),
    ]

COMMON_GATES = "spark-plug part number and gap (not published, interval only), battery notes"

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=673, label="2020 OS  Nu 2.0 MPI + Gamma 1.6 T-GDI", psi=33, hold=False,
  oil=dict(visc="5W-20 (" + NU + ") / 5W-30 (" + GAMMA + ")", type=None,
           cap="4.23 qt / 4.0 L (" + NU + ") / 4.76 qt / 4.5 L (" + GAMMA + ")", spec=OS_OIL_SPEC),
  fluids=dict(trans=OS_TRANS, brake=BRAKE_LV + "; 0.74-0.85 qt / 0.7-0.8 L", cool_type=COOL_OS,
              cool_cap="6.8 qt / 6.5 L (" + NU + ") / 7.5 qt / 7.1 L (" + GAMMA + ")", diff=diff(GL5_90, GL5_90)),
  parts=dict(tire="205/60R16, 215/55R17 or 235/45R18", note=OS_TIRE_NOTE % "13.2 gal / 50 L"),
  src="owner-manual-verified (per 2020 Hyundai Kona OM, portal file '2020 Kona Owner's Manual.pdf' = kona_2020_OS_portal_OM.pdf, "
      + PORTAL + "; OS, self-ID engine table p.8-2 Gamma 1.6 T-GDI 1,591cc + Nu 2.0 MPI 1,999cc, wheelbase 102.36 in; "
      "capacities p.8-7/8-8, viscosity p.8-9, tires + lug torque p.8-5; cross-checked against the later print "
      + (GLOBAL % ("OS", "2020")) + ": every written value identical; gated to null: transfer case and rear differential "
      "capacities (quart and litre figures on p.8-8 do not convert to each other), brake-fluid replacement interval "
      "(first print inspect-only, later print 60,000 / 48,000 mi), 12V battery group and CCA (not published), "
      + COMMON_GATES + ")",
  msrc="Hyundai Owner's Manual (Kona 2020 OS, p.%s)",
  maint=os_maint(brake=False)),

 dict(vid=2166, label="2021 OS  Nu 2.0 MPI + Gamma 1.6 T-GDI", psi=33, hold=False,
  oil=dict(visc="5W-20 (" + NU + ") / 5W-30 (" + GAMMA + ")", type=None,
           cap="4.23 qt / 4.0 L (" + NU + ")", spec=OS_OIL_SPEC + " API Certification Mark recommended."),
  fluids=dict(trans=OS_TRANS, brake=BRAKE_LV + "; 0.74-0.85 qt / 0.7-0.8 L", cool_type=COOL_OS,
              cool_cap="6.8 qt / 6.5 L (" + NU + ") / 7.5 qt / 7.1 L (" + GAMMA + ")", diff=diff(GL5_90, GL5_90)),
  parts=dict(tire="205/60R16, 215/55R17 or 235/45R18", note=OS_TIRE_NOTE % "13.2 gal / 50 L"),
  src="owner-manual-verified (per 2021 Hyundai Kona OM, portal file 2021_Kona_Owners_Manual.pdf = kona_2021_OS_portal_OM.pdf, "
      + PORTAL + "; OS, self-ID engine table p.8-2 Gamma 1.6 T-GDI 1,591cc + Nu 2.0 MPI 1,999cc, wheelbase 102.36 in; "
      "capacities p.8-7/8-8, viscosity p.8-9, tires + lug torque p.8-5; cross-checked against the later print "
      + (GLOBAL % ("OS", "2021")) + ": every written value identical; gated to null: Gamma 1.6 T-GDI oil capacity "
      "(first print p.8-7 4.76 qt / 4.5 L, later print 4.23 qt / 4.0 L - the two prints disagree), transfer case and "
      "rear differential capacities (quart and litre figures on p.8-8 do not convert to each other), 12V battery "
      "group and CCA (not published), " + COMMON_GATES + ")",
  msrc="Hyundai Owner's Manual (Kona 2021 OS, p.%s)",
  maint=os_maint(brake=True)),

 dict(vid=3694, label="2022 OS facelift  Smartstream G2.0 Atkinson + Smartstream G1.6 T-GDi", psi=33, hold=False,
  oil=SS_OIL,
  fluids=dict(
   trans="Intelligent variable transmission (" + S20 + "): SP-CVT1, 7.1 qt / 6.7 L. Dual clutch transmission (" + S16
         + "): API GL-4 SAE 70W (HK D DCTF TGO-10, Spirax S6 GHDE 70W DCTF or 7 DCTF HKM), 1.7-1.8 qt / 1.6-1.7 L.",
   brake=BRAKE_LV, cool_type=COOL_OSPE,
   cool_cap="6.3 qt / 6.0 L (" + S20 + ") / 7.3 qt / 6.9 L (" + S16 + ")",
   diff=diff(GL5_90 + ", 0.5-0.55 qt / 0.47-0.52 L",
             GL5_85 + "; 0.49-0.55 qt / 0.47-0.52 L (" + S16 + "), 0.4-0.44 qt / 0.38-0.42 L (" + S20 + ")")),
  parts=dict(tire="205/60R16, 215/55R17 or 235/45R18", note=OS_TIRE_NOTE % "13.21 gal / 50 L"),
  src="owner-manual-verified (per 2022 Hyundai Kona OM, portal file 2022-Kona-Owners-Manual.pdf = kona_2022_OSPE_portal_OM.pdf, "
      + PORTAL + "; OS facelift, self-ID engine table p.2-9 Smartstream G1.6 T-GDi 1,598cc + Smartstream G2.0 Atkinson "
      "1,999cc, wheelbase 102.36 in; capacities p.2-13/2-14, viscosity p.2-14, tires + lug torque p.2-11, lug also "
      "p.8-20; cross-checked against the later print " + (GLOBAL % ("OS", "2022")) + ": every written value agrees "
      "(litre figures identical, later print shows US gal); gated to null: brake-fluid capacity (0.5-0.6 qt vs "
      "0.7-0.8 L on p.2-14 do not convert to each other), 12V battery group and CCA (p.9-30 shows only an example "
      "capacity label CMF60L-BCI), " + COMMON_GATES + ")",
  msrc="Hyundai Owner's Manual (Kona 2022 OS facelift, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-8"),
   (96000, None, "Spark plug replacement (" + S20 + ")", "9-8"),
   (24000, 36, "Engine air cleaner filter replacement", "9-8"),
   (16000, None, "Cabin air filter replacement", "9-8"),
   (8000, None, "Tire rotation", "9-8"),
   (120000, 120, "Engine coolant first replacement", "9-9"),
   (48000, 48, "Brake fluid replacement", "9-10"),
  ]),

 dict(vid=6787, label="2024 SX2  Smartstream G2.0 Atkinson + Smartstream G1.6 T-GDi", psi=None, hold=False,
  oil=SS_OIL, fluids=SX2_FLUIDS,
  parts=dict(tire="215/60R17, 215/55R18 or 235/45R19", note=SX2_TIRE_NOTE),
  src="owner-manual-verified (per 2024 Hyundai Kona OM, " + (GLOBAL % ("SX2", "2024")) + " = kona_2024_SX2_global_OM.pdf, "
      "Copyright 2023 HYUNDAI Motor America, single print (no US-portal copy exists); SX2, self-ID p.24-25 Smartstream "
      "G1.6 T-GDi 1,598cc + Smartstream G2.0 Atkinson 1,999cc, wheelbase 104.7 in; capacities p.31, viscosity p.32, "
      "tires + wheel nut torque p.28; gated to null: IVT, rear differential and transfer case capacities (quart and "
      "litre figures on p.31 do not convert to each other), 12V battery group and CCA (p.655 shows only an example "
      "capacity label AGM70L-DIN), " + COMMON_GATES + ")",
  msrc="Hyundai Owner's Manual (Kona 2024 SX2, p.%s)",
  maint=sx2_maint("625-626", "626", "626", "629", "628")),

 dict(vid=9976, label="2026 SX2  Smartstream G2.0 Atkinson + Smartstream G1.6 T-GDi", psi=None, hold=False,
  oil=SS_OIL, fluids=SX2_FLUIDS,
  parts=dict(tire="215/60R17, 215/55R18 or 235/45R19", note=SX2_TIRE_NOTE),
  src="owner-manual-verified (per 2026 Hyundai Kona OM, " + (GLOBAL % ("SX2", "2026")) + " = kona_2026_SX2_global_OM.pdf, "
      "Copyright 2026 HYUNDAI Motor America, single print (no US-portal copy exists); SX2, self-ID p.26-27 Smartstream "
      "G1.6 T-GDi 1,598cc + Smartstream G2.0 Atkinson 1,999cc, wheelbase 104.7 in; capacities p.32-33, viscosity p.33, "
      "tires + wheel nut torque p.29; gated to null: IVT, rear differential and transfer case capacities (quart and "
      "litre figures on p.32 do not convert to each other), 12V battery group and CCA (p.685 shows only an example "
      "capacity label AGM70L-DIN), " + COMMON_GATES + ")",
  msrc="Hyundai Owner's Manual (Kona 2026 SX2, p.%s)",
  maint=sx2_maint("654", "654", "654", "657", "656")),
]

# ---------------------------------------------------------------------------------------------------------------
def check(row):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid = row["vid"]
    want = (int(row["label"][:4]), "Hyundai", "Kona")
    assert VEHICLES.get(vid) == want, (vid, "target row is not the labelled vehicle", VEHICLES.get(vid), want)
    assert ("per %d Hyundai Kona OM" % want[0]) in row["src"] and ("Kona %d " % want[0]) in row["msrc"], (vid, "source year")
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    for mi, mo, desc, page in row["maint"]:
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert isinstance(mi, int) and mi > 0, (vid, desc)
        assert mo is None or (isinstance(mo, int) and mo > 0), (vid, desc)
    shipped = [row["oil"]["visc"], row["oil"]["type"], row["oil"]["cap"], row["oil"]["spec"],
               row["fluids"]["trans"], row["fluids"]["brake"], row["fluids"]["cool_type"], row["fluids"]["cool_cap"],
               row["parts"]["tire"], row["parts"]["note"], LUG_NOTE, EPS] + [d for _, _, d, _ in row["maint"]]
    for e in json.loads(row["fluids"]["diff"]):
        assert set(e) == {"location", "fluid_type"}, (vid, e)
        shipped += [e["location"], e["fluid_type"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
    assert row["src"] != "owner-manual-verified" and row["src"].startswith("owner-manual-verified (")
    assert row["psi"] is None or isinstance(row["psi"], int)
    # unit sanity on every "<a> qt / <b> L" pair that ships: 1 L = 1.057 US qt, within print rounding
    for s in shipped:
        for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
            qs, ls = q.split("-"), l.split("-")
            assert len(qs) == len(ls), (vid, "qt/L range shape", q, l)
            for a, b in zip(qs, ls):          # a range is compared end to end
                assert abs(float(a) - float(b) * 1.0567) <= 0.09, (vid, "qt/L mismatch", q, l, s)

def write(c, nid, row):
    vid, o, f, p = row["vid"], row["oil"], row["fluids"], row["parts"]
    for t in ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]:
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
    print("\n=== %d  %s" % (row["vid"], row["label"]))
    print("  oil   : %s | %s | %s" % (row["oil"]["cap"], row["oil"]["visc"], row["oil"]["type"]))
    print("  spec  : %s" % row["oil"]["spec"])
    print("  trans : %s" % row["fluids"]["trans"])
    print("  cool  : %s | %s" % (row["fluids"]["cool_cap"], row["fluids"]["cool_type"]))
    print("  brake : %s" % row["fluids"]["brake"])
    for e in json.loads(row["fluids"]["diff"]):
        print("  diff  : %s -> %s" % (e["location"], e["fluid_type"]))
    print("  tires : %s @ %s psi | %s" % (row["parts"]["tire"], row["psi"] if row["psi"] else "per size (see note)", row["parts"]["note"]))
    print("  lug   : 79.0 lb-ft / 107.0 N-m | %s" % LUG_NOTE)
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7d mi / %s mo  %s  [p.%s]" % (mi, mo if mo else "--", desc, page))
    print("  src   : %s" % row["src"])

# ---------------------------------------------------------------------------------------------------------------
for row in ROWS:
    check(row)
todo = [r for r in ROWS if (not r["hold"]) or WITH_2026]
held = [r for r in ROWS if r["hold"] and not WITH_2026]
print("contract checks PASS: %d vehicles read, %d to write (%d maintenance rows), %d held; every source classified "
      "verified with a suffix" % (len(ROWS), len(todo), sum(len(r["maint"]) for r in todo), len(held)))
for row in ROWS:
    show(row)

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_kona_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
for row in todo:
    nid = write(c, nid, row)
    print("  wrote %d  %s" % (row["vid"], row["label"]))
db.commit()

print("\nVerify:")
for row in todo:
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
          % (vid, o[0][0][:40], f[0][0][:34], p[0][0], p[0][1], p[0][2], p[0][3], t[0][1], m[0], m[1][:40]))
for row in held:
    s = c.execute("SELECT source FROM oil_change WHERE vehicle_id=?", (row["vid"],)).fetchone()
    print("  %d HELD -> untouched: %s" % (row["vid"], s[0] if s else "none"))
bare = c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                 "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source='owner-manual-verified'").fetchone()[0]
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare)
assert bare == 424, bare
db.close()
print("DONE - %d Kona rows written, %d held." % (len(todo), len(held)))
