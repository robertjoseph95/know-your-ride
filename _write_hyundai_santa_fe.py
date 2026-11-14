# Hyundai Santa Fe - FIFTH Hyundai slice. 9 model years written, 4 deferred (untouched).
# Written: 2005 / 2006 SM (ids 11155 / 11225), 2018 NC three-row (id 12522), 2019 / 2020 TM (ids 12673 / 12781),
#          2021 / 2023 TM facelift (ids 12851 / 12981), 2025 / 2026 MX5 (ids 13113 / 13179).
# Deferred: 2001-2004 (ids 10988, 11014, 11049, 11097) - no manufacturer manual on either host.
# Sources (both manufacturer, free, citable), saved under _hyundai_manuals/santa_fe/ (gitignored); reads 2026-11-14:
#   * US portal owners.hyundaiusa.com glovebox-manual (first print): 2005, 2006, 2018, 2020, 2021, 2023.
#   * ownersmanual.hyundai.com full_pdf/<PLATFORM>/<label>/en_US (later print): 2019, 2025, 2026, and the cross-check
#     copies for 2020 / 2021 / 2023. For platform TMa the label in the URL is NOT the model year (it tracks the copyright
#     year): label 2018 = MY2019, 2019 = MY2020, 2020 = MY2021, 2022 / 2023 = MY2023. Every book was identified by
#     wheelbase + engine table + copyright, and matched page-for-page against the portal books, whose PDF Title names
#     the model year.
# ** Identity rulings 2026-11-14 ("Accept, go read"): (1) the 2019 row is written from the second-host book labelled
#    2018 (earliest TM book, Copyright 2018; the portal's 2019 file is the three-row Santa Fe XL); (2) the 2018 row is the
#    three-row 3.3 V6 vehicle (the manual titled 2018 Santa Fe; the two-row Sport has its own manual and no DB row);
#    (3) 2005 / 2006 are written V6-only - neither book carries the 2.4 I4.
# ** Null rules (ruling 2026-11-14), reasons live HERE and in the source suffix only:
#    EDITION CONFLICT - a value two prints of the same manual contradict is not written, the agreed part ships:
#      2020 brake fluid (first print DOT-3 or DOT-4, later print ISO 4925 DOT-4) -> "DOT-4";
#      2023 automatic transmission fluid (first print ATF SP-IV, later prints ATF SP4M-1) -> capacity only.
#    INTERNAL CONFLICT - 2021 T-GDI oil viscosity (capacities table 0W-20, viscosity chart 0W-30) -> not written;
#      2005 first oil grade (printed "SAE 50W-20") -> not written.
#    UNIT CONFLICT - figures that do not convert to each other are not written: 2019 / 2020 2.0 T-GDI transmission
#      capacity (7.09 qt beside 7.0 L), 2019 / 2020 transfer case capacity (0.44-0.49 qt beside 0.47-0.52 L),
#      2018 fuel tank (18.95 gal beside 71 L).
# ** Gates (null): spark-plug part number / gap for 2018+ (interval only; the 2005 / 2006 books publish both and they
#    are written); 12V battery for 2018+ (2018-2020 no spec; 2021+ only an example capacity label); Hybrid and Plug-in
#    Hybrid (own manuals); EPS / MDPS - no power-steering fluid (2005 / 2006 are hydraulic and are written).
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows.
# ** S1.12 / S1.11: no bookkeeping words in shipped columns; battery_notes NULL; diff JSON = [{location, fluid_type}].
#
# Usage:  python _write_hyundai_santa_fe.py            -> DRY RUN: print every row, classify every source, write nothing
#         python _write_hyundai_santa_fe.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Santa Fe'")}
_c.close()

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_PHOS = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
COOL_EG = "Mixture of antifreeze and water; ethylene glycol base coolant for aluminum radiator"
BRAKE_LV = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
ATF_SP3 = "ATF SP-III (Hyundai genuine, Diamond or SK ATF SP-III, or other brands approved by Hyundai)"
ATF_SP4 = "ATF SP-IV (MICHANG, SK, NOCA, Hyundai genuine or other approved brands meeting the spec)"
GL5_8090 = "API GL-5 SAE 80W/90 gear oil (Shell Spirax AX or equivalent)"
GL5_7590X = "Hypoid gear oil API GL-5 SAE 75W/90 (Shell Spirax X or equivalent)"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
LUG_HMG = dict(ftlb=79.0, nm=107.0,
               note="79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)")
LUG_SM = dict(ftlb=65.0, nm=None,
              note="65 to 80 lb-ft (900 to 1,100 kg-cm), wheel nut tightening torque per owner manual (range), steel and aluminium alloy wheels")
V27, V35 = "2.7 V6", "3.5 V6"
G24, T20 = "2.4 GDI", "2.0 T-GDI"
G25, G25T = "Smartstream G2.5 GDI", "Smartstream G2.5 T-GDI"
MXT = "Smartstream G2.5 T-GDi"
PORTAL = "owners.hyundaiusa.com glovebox-manual"
GLOBAL = "ownersmanual.hyundai.com full_pdf %s %s en_US"
NO_PLUG_BATT = "spark-plug part number and gap (not published, interval only), battery notes"

def diff(rear_name, rear, transfer_name, transfer):
    return json.dumps([{"location": rear_name, "fluid_type": rear},
                       {"location": transfer_name, "fluid_type": transfer}], ensure_ascii=False)

# ---- SM first generation (2005 / 2006) -------------------------------------------------------------------------
SM_FLUIDS = dict(
    trans="Automatic transaxle: " + ATF_SP3 + ", 8.98 qt / 8.5 L.",
    brake="DOT 3, DOT 4 or equivalent", cool_type="Ethylene glycol base coolant for aluminum radiator",
    cool_cap="7.4 qt / 7.0 L (" + V27 + ") / 8.66 qt / 8.2 L (" + V35 + ")",
    ps="Hydraulic power steering - PSF-3 type fluid; 0.95 qt / 0.9 L (" + V27 + "), 1.06 qt / 1.0 L (" + V35 + ")",
    diff=diff("Rear axle (4WD)", GL5_8090 + ", 1.16 qt / 1.1 L", "Transfer case (4WD)", GL5_8090 + ", 0.85 qt / 0.8 L"))
SM_PARTS = dict(tire="225/70R16", note="Standard tire 225/70R16 at 30 psi; full-size spare. Fuel tank 19 gal / 72 L.",
                plug_type="Champion RC10PYPB4 or NGK PFR5N-11 (" + V27 + " and " + V35 + ")",
                plug_gap="0.039 to 0.043 in (1.0 to 1.1 mm)", batt_group="MF 68 AH (12 V)")
SM_MAINT = [
    (7500, 6, "Engine oil & filter change", "5-4"),
    (60000, 48, "Spark plug replacement (platinum coated)", "5-4"),
    (30000, 24, "Engine air cleaner filter replacement", "5-4"),
    (10000, 12, "Air conditioner (cabin) filter replacement", "5-5"),
    (30000, 24, "Engine coolant replacement", "5-5"),
    (60000, 48, "Timing belt replacement", "5-5"),
]
def sm_oil(visc):
    return dict(visc=visc, type=None,
                cap="4.76 qt / 4.5 L (" + V27 + ") / 4.54 qt / 4.3 L (" + V35 + ")",
                cap_wo="4.44 qt / 4.2 L (" + V27 + ") / 4.23 qt / 4.0 L (" + V35 + ")",
                spec="API SJ, SL or above; ILSAC GF-3 or above")

# ---- TM pre-facelift (2019 / 2020) -----------------------------------------------------------------------------
TM_OIL = dict(visc="5W-20 (" + G24 + ") / 5W-30 (" + T20 + ")", type=None,
              cap="5.07 qt / 4.8 L (" + G24 + ") / 5.07 qt / 4.8 L (" + T20 + ")", cap_wo=None,
              spec=G24 + ": API Latest (ILSAC Latest); SAE 5W-20 recommended, chart also allows 0W-30 / 5W-30 / 10W-30 by "
                   "temperature. " + T20 + ": API Latest (ILSAC Latest) or ACEA A5/B5; SAE 5W-30 recommended, chart also "
                   "allows 0W-30 / 5W-40 / 10W-30 / 15W-40 / 20W-50 by temperature.")
def tm_fluids(brake):
    return dict(trans="Automatic transmission: " + ATF_SP4 + "; 6.86 qt / 6.5 L (" + G24 + ").",
                brake=brake, cool_type=COOL_PHOS,
                cool_cap="8.3 qt / 7.9 L (" + G24 + ") / 8.6 qt / 8.2 L (" + G24 + " with trailer package) / 7.9 qt / 7.5 L (" + T20 + ")",
                ps=EPS, diff=diff("Rear differential (AWD)", GL5_85 + ", 0.61 qt / 0.58 L", "Transfer case (AWD)", GL5_85))
TM_PARTS = dict(tire="235/65R17, 235/60R18 or 235/55R19",
                note="17-in wheels: 235/65R17; 18-in wheels: 235/60R18; 19-in wheels: 235/55R19; 35 psi front and rear. "
                     "Compact spare T165/90R17 at 60 psi. Fuel tank 18.75 gal / 71 L.")
TM_MAINT = [
    (7500, 12, "Engine oil & filter change (" + G24 + ")", "7-8"),
    (6000, 12, "Engine oil & filter change (" + T20 + ")", "7-13"),
    (97500, None, "Spark plug replacement (" + G24 + ")", "7-8"),
    (42000, None, "Spark plug replacement (" + T20 + ")", "7-13"),
    (30000, 48, "Engine air cleaner filter replacement (" + G24 + ")", "7-8"),
    (24000, 48, "Engine air cleaner filter replacement (" + T20 + ")", "7-13"),
    (15000, 12, "Climate control (cabin) air filter replacement (" + G24 + ")", "7-8"),
    (12000, 12, "Climate control (cabin) air filter replacement (" + T20 + ")", "7-13"),
    (7500, None, "Tire rotation (" + G24 + ")", "7-8"),
    (6000, None, "Tire rotation (" + T20 + ")", "7-13"),
    (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-8, 7-13"),
]
TM_GATES = ("2.0 T-GDI transmission fluid capacity (p.8-7 prints 7.09 qt beside 7.0 L, which do not convert), transfer case "
            "capacity (p.8-8 prints 0.44-0.49 qt beside 0.47-0.52 L), 12V battery group and CCA (not published), " + NO_PLUG_BATT)

# ---- TM facelift (2021 / 2023) ---------------------------------------------------------------------------------
FL_CAP = "6.13 qt / 5.8 L (" + G25 + ") / 6.13 qt / 5.8 L (" + G25T + ")"
FL_COOL = "7.5 qt / 7.1 L (" + G25 + ") / 8.17 qt / 7.73 L (" + G25T + ")"
FL_DIFF = diff("Rear differential (AWD)", GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L",
               "Transfer case (AWD)", GL5_85 + "; 0.66-0.72 qt / 0.62-0.68 L (automatic transmission), "
                                               "0.51-0.55 qt / 0.48-0.52 L (dual clutch transmission)")
FL_TIRE = "235/60R18, 235/55R19 or 255/45R20"
FL_NOTE = ("18-in wheels: 235/60R18; 19-in wheels: 235/55R19; 20-in wheels: 255/45R20; 35 psi front and rear at normal and "
           "maximum load. %s T135/90D17 at 60 psi. Fuel tank %s.")

# ---- MX5 (2025 / 2026) -----------------------------------------------------------------------------------------
MX_OIL = dict(visc="0W-30", type="Full synthetic (required)", cap="6.13 qt / 5.8 L (" + MXT + ")", cap_wo=None,
              spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required; SAE 0W-30")
def mx_fluids(trans):
    return dict(trans=trans, brake="DOT-4", cool_type=COOL_EG, cool_cap="9.65 qt / 9.133 L (" + MXT + ")", ps=EPS,
                diff=diff("Rear differential (AWD)", GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L",
                          "Transfer case (AWD)", GL5_85 + ", 0.5-0.55 qt / 0.47-0.52 L"))
MX_PARTS = dict(tire="235/60R18, 245/60R18, 255/45R20 or 245/45R21",
                note="18-in wheels: 235/60R18 or 245/60R18 at 35 psi; 20-in wheels: 255/45R20 and 21-in wheels: 245/45R21 at "
                     "36 psi; front and rear, normal and maximum load. Compact spare T135/90D17 at 60 psi. "
                     "Fuel tank 17.7 gal / 67 L.")
def mx_maint(p_oil, p_plug, p_cool, p_rot, p_cabin):
    return [
        (8000, 12, "Engine oil & filter change", p_oil),
        (48000, None, "Spark plug replacement", p_plug),
        (24000, 36, "Engine air cleaner filter replacement", p_oil),
        (16000, 24, "Cabin air filter replacement", p_cabin),
        (8000, 12, "Tire rotation", p_rot),
        (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", p_cool),
        (48000, 48, "Brake fluid replacement", p_cool),
    ]

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=11155, label="2005 SM  2.7 V6 + 3.5 V6", psi=30, lug=LUG_SM,
  oil=sm_oil("5W-30; 10W-30 above 0 F (-18 C)"), fluids=SM_FLUIDS, parts=SM_PARTS,
  src="owner-manual-verified (per 2005 Hyundai Santa Fe OM, portal file 2005_Hyundai_SantaFe_OM.pdf = santafe_2005_portal_OM.pdf, "
      + PORTAL + ", Copyright 2005 Hyundai Motor Company, Publication No. A26O-EU51C; SM first generation, self-ID engine "
      "table p.9-3 2.7 V6 2,656cc + 3.5 V6 3,497cc, wheel base 103.1 in p.9-2; specification pages 9-2 to 9-5 are scanned "
      "images read from page renders; lubrication chart p.9-4, quantities p.9-5, plugs p.9-3, battery + tire p.9-2, wheel "
      "nut torque p.3-11; single print; gated to null: first oil viscosity grade (p.9-4 prints 'SAE 50W-20', a misprint), "
      "2.4 I4 (not carried by this book), battery notes)",
  msrc="Hyundai Owner's Manual (Santa Fe 2005 SM, p.%s)", maint=SM_MAINT),

 dict(vid=11225, label="2006 SM  2.7 V6 + 3.5 V6", psi=30, lug=LUG_SM,
  oil=sm_oil("5W-20 or 5W-30 (all temperatures); 10W-30 above 0 F (-18 C)"), fluids=SM_FLUIDS, parts=SM_PARTS,
  src="owner-manual-verified (per 2006 Hyundai Santa Fe OM, portal file 2006_Hyundai_SantaFe_OM.pdf = santafe_2006_portal_OM.pdf, "
      + PORTAL + ", Copyright 2005 Hyundai Motor Company; SM first generation, self-ID engine table p.9-3 2.7 V6 2,656cc + "
      "3.5 V6 3,497cc, wheel base 103.1 in p.9-2; lubrication chart p.9-4, quantities p.9-5, plugs p.9-3, battery + tire "
      "p.9-2, wheel nut torque p.3-11; single print; gated to null: 2.4 I4 (not carried by this book), battery notes)",
  msrc="Hyundai Owner's Manual (Santa Fe 2006 SM, p.%s)", maint=SM_MAINT),

 dict(vid=12522, label="2018 NC three-row  Lambda 3.3 V6", psi=33, lug=LUG_HMG,
  oil=dict(visc="5W-30 (API SM / ILSAC GF-4 recommended; chart also allows 5W-40 / 10W-30 by temperature)", type=None,
           cap="6.02 qt / 5.7 L (Lambda 3.3 V6)", cap_wo=None,
           spec="API SM, ILSAC GF-4 (or above), ACEA A5 (or above); SAE 5W-30"),
  fluids=dict(trans="Automatic transaxle: " + ATF_SP4 + ", 8.24 qt / 7.8 L.",
              brake="FMVSS 116 DOT-3 or DOT-4; 0.74-0.85 qt / 0.7-0.8 L",
              cool_type="Mixture of antifreeze and distilled water; ethylene glycol base coolant for aluminum radiator",
              cool_cap="9.6 qt / 9.1 L (Lambda 3.3 V6)", ps=EPS,
              diff=diff("Rear differential (AWD)", GL5_7590X + ", 0.56 qt / 0.53 L",
                        "Transfer case (AWD)", GL5_7590X + ", 0.72 qt / 0.68 L")),
  parts=dict(tire="235/60R18 or 235/55R19",
             note="18-in wheels: 235/60R18; 19-in wheels: 235/55R19 or P235/55R19; 33 psi front and rear at normal and "
                  "maximum load. Compact spare T165/90R17 at 60 psi."),
  src="owner-manual-verified (per 2018 Hyundai Santa Fe OM, portal file 2018_Hyundai_SantaFe_OM.pdf = santafe_2018_portal_OM.pdf, "
      + PORTAL + ", PDF title '2018 Hyundai Santa Fe Owner's Manual', Copyright 2017 HYUNDAI Motor America; three-row body "
      "(the vehicle EPA lists as the 2018 Santa Fe; ruling 2026-11-14), self-ID p.8-2 Lambda 3.3 V6 3,342cc, wheelbase "
      "110.24 in; capacities p.8-7, viscosity p.8-8, tires + lug torque p.8-5; single print (this platform is not on the "
      "second host); gated to null: fuel tank (p.8-7 prints 18.95 gal beside 71 L, which do not convert), 12V battery "
      "group and CCA (not published), " + NO_PLUG_BATT + "; the two-row Santa Fe Sport has its own manual and is not "
      "covered)",
  msrc="Hyundai Owner's Manual (Santa Fe 2018 three-row, p.%s)",
  maint=[
   (7500, 12, "Engine oil & filter change", "7-10"),
   (100000, 120, "Spark plug replacement", "7-18"),
   (30000, 24, "Engine air cleaner filter replacement", "7-12"),
   (15000, 12, "Climate control (cabin) air filter replacement", "7-10"),
   (7500, 6, "Tire rotation", "7-10"),
   (120000, 60, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-16"),
  ]),

 dict(vid=12673, label="2019 TM  2.4 GDI + 2.0 T-GDI", psi=35, lug=LUG_HMG,
  oil=TM_OIL, fluids=tm_fluids("FMVSS 116 DOT-3 or DOT-4; 0.46-0.5 qt / 0.44-0.48 L"), parts=TM_PARTS,
  src="owner-manual-verified (per 2019 Hyundai Santa Fe OM, " + (GLOBAL % ("TMa", "2018")) + " = santafe_2018_TMa_global_OM.pdf "
      "(the host labels this file 2018; Copyright 2018 HYUNDAI Motor America, the earliest TM-generation book, accepted as "
      "the 2019 model-year manual by ruling 2026-11-14; the portal's 2019 file is the three-row Santa Fe XL); TM, self-ID "
      "p.8-2 2.4 GDI 2,359cc + 2.0 T-GDI 1,998cc, wheelbase 108.86 in; capacities p.8-7/8-8, viscosity p.8-9, tires + lug "
      "torque p.8-5; single print for this model year; gated to null: " + TM_GATES + ")",
  msrc="Hyundai Owner's Manual (Santa Fe 2019 TM, p.%s)", maint=TM_MAINT),

 dict(vid=12781, label="2020 TM  2.4 GDI + 2.0 T-GDI", psi=35, lug=LUG_HMG,
  oil=TM_OIL, fluids=tm_fluids("DOT-4; 0.46-0.5 qt / 0.44-0.48 L"), parts=TM_PARTS,
  src="owner-manual-verified (per 2020 Hyundai Santa Fe OM, portal file '2020 Santa Fe Owner's Manual.pdf' = santafe_2020_portal_OM.pdf, "
      + PORTAL + ", PDF title '2020 Santa Fe Owner's Manual', Copyright 2019 HYUNDAI Motor America; TM, self-ID p.8-2 2.4 GDI "
      "2,359cc + 2.0 T-GDI 1,998cc, wheelbase 108.86 in; capacities p.8-7/8-8, viscosity p.8-9, tires + lug torque p.8-5; "
      "cross-checked against the later print " + (GLOBAL % ("TMa", "2019")) + " (Copyright 2019): identical except the "
      "brake-fluid specification; gated to null: brake-fluid DOT-3 allowance (first print 'DOT-3 or DOT-4', later print "
      "'ISO 4925 DOT-4' - only DOT-4, accepted by both prints, is written), " + TM_GATES + ")",
  msrc="Hyundai Owner's Manual (Santa Fe 2020 TM, p.%s)", maint=TM_MAINT),

 dict(vid=12851, label="2021 TM facelift  Smartstream G2.5 GDI + Smartstream G2.5 T-GDI", psi=35, lug=LUG_HMG,
  oil=dict(visc="0W-20 (" + G25 + ")", type="Full synthetic (required)", cap=FL_CAP, cap_wo=None,
           spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API SN PLUS or above, or ACEA A5/B5)"),
  fluids=dict(
   trans="Automatic transmission (" + G25 + "): " + ATF_SP4 + ", 6.87 qt / 6.5 L. Dual clutch transmission (" + G25T
         + "): gear oil SAE 70W API GL-4 (GS WDCTF HD G 70W), 3.49-3.59 qt / 3.3-3.4 L; control oil SAE 70W API GL-4 "
           "(GS WDCTF HD H 70W), 2.59-2.64 qt / 2.45-2.50 L.",
   brake=BRAKE_LV, cool_type=COOL_PHOS, cool_cap=FL_COOL, ps=EPS, diff=FL_DIFF),
  parts=dict(tire=FL_TIRE, note=FL_NOTE % ("Compact spare", "67 L (70.8 US qt)")),
  src="owner-manual-verified (per 2021 Hyundai Santa Fe OM, portal file 2021-SantaFe-Owners-Manual.pdf = santafe_2021_portal_OM.pdf, "
      + PORTAL + ", PDF title '2021 Santa Fe Owners Manual', Copyright 2020 HYUNDAI Motor America; TM facelift, self-ID p.2-8 "
      "Smartstream G2.5 GDI + G2.5 T-GDI 2,497cc, wheelbase 108.9 in; capacities p.2-12/2-13, viscosity p.2-14, tires + "
      "wheel bolt torque p.2-10; cross-checked against the later print " + (GLOBAL % ("TMa", "2020")) + " (Copyright 2020, "
      "dated 2020-12-14): every written value identical; gated to null: G2.5 T-GDI oil viscosity (capacities table p.2-12 "
      "gives 0W-20 for both engines, viscosity chart p.2-14 gives the T-GDI 0W-30), 12V battery group and CCA (p.9-30 "
      "shows only an example capacity label), " + NO_PLUG_BATT + "; Hybrid has its own manual)",
  msrc="Hyundai Owner's Manual (Santa Fe 2021 TM facelift, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-8"),
   (96000, None, "Spark plug replacement (" + G25 + ")", "9-9"),
   (48000, None, "Spark plug replacement (" + G25T + ")", "9-9"),
   (24000, 36, "Engine air cleaner filter replacement", "9-9"),
   (16000, 24, "Climate control (cabin) air filter replacement", "9-11"),
   (120000, 120, "Engine coolant first replacement (" + G25 + "); thereafter every 30,000 mi / 24 months", "9-10"),
   (80000, 120, "Engine coolant first replacement (" + G25T + "); thereafter every 24,000 mi / 24 months", "9-10"),
   (60000, 48, "Brake fluid replacement (" + G25 + ")", "9-10"),
   (48000, 48, "Brake fluid replacement (" + G25T + ")", "9-10"),
  ]),

 dict(vid=12981, label="2023 TM facelift  Smartstream G2.5 GDI + Smartstream G2.5 T-GDI", psi=35, lug=LUG_HMG,
  oil=dict(visc="0W-20 (" + G25 + ") / 0W-30 (" + G25T + ")", type=None, cap=FL_CAP, cap_wo=None,
           spec="API SN PLUS/SP or ILSAC GF-6 (API SN PLUS or above required)"),
  fluids=dict(
   trans="Automatic transmission (" + G25 + "): 6.87 qt / 6.5 L. Dual clutch transmission (" + G25T
         + "): gear oil GS WDCTF HD G, 3.4-3.6 qt / 3.3-3.4 L; control oil GS WDCTF HD H, 2.58-2.64 qt / 2.45-2.5 L.",
   brake=BRAKE_LV, cool_type=COOL_PHOS, cool_cap=FL_COOL, ps=EPS, diff=FL_DIFF),
  parts=dict(tire=FL_TIRE, note=FL_NOTE % ("Compact spare (if equipped)", "17.7 gal / 67 L")),
  src="owner-manual-verified (per 2023 Hyundai Santa Fe OM, portal file 2023-Santa-Fe-Owners-Manual.pdf = santafe_2023_portal_OM.pdf, "
      + PORTAL + ", PDF title '2023 Santa Fe Owner's Manual', Copyright 2022 HYUNDAI Motor America; TM facelift, self-ID p.2-8 "
      "Smartstream G2.5 GDI + G2.5 T-GDI 2,497cc, wheelbase 108.9 in; capacities p.2-12/2-13, viscosity p.2-14, tires + "
      "wheel bolt torque p.2-10; cross-checked against the later prints " + (GLOBAL % ("TMa", "2022")) + " and TMa 2023 "
      "(both Copyright 2023): every written value identical; gated to null: automatic transmission fluid specification "
      "(first print ATF SP-IV, later prints ATF SP4M-1 - the prints disagree, only the capacity all prints share is "
      "written), 12V battery group and CCA (p.9-31 shows only an example capacity label), " + NO_PLUG_BATT
      + "; Hybrid and Plug-in Hybrid have their own manuals)",
  msrc="Hyundai Owner's Manual (Santa Fe 2023 TM facelift, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-8"),
   (96000, None, "Spark plug replacement (" + G25 + ")", "9-9"),
   (48000, None, "Spark plug replacement (" + G25T + ")", "9-9"),
   (24000, 36, "Engine air cleaner filter replacement", "9-9"),
   (16000, 24, "Cabin air filter replacement", "9-11"),
   (8000, 12, "Tire rotation", "9-11"),
   (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-10"),
   (48000, 48, "Brake fluid replacement", "9-10"),
  ]),

 dict(vid=13113, label="2025 MX5  Smartstream G2.5 T-GDi", psi=None, lug=LUG_HMG,
  oil=MX_OIL,
  fluids=mx_fluids("Dual clutch transmission: cooling oil GS WDCTF HD G (wet DCT fluid), 3.49-3.6 qt / 3.3-3.4 L; control "
                   "oil GS WDCTF HD H (wet DCT hydraulic control oil), 2.59-2.64 qt / 2.45-2.5 L."),
  parts=MX_PARTS,
  src="owner-manual-verified (per 2025 Hyundai Santa Fe OM, " + (GLOBAL % ("MX5a", "2025")) + " = santafe_2025_MX5a_global_OM.pdf, "
      "book header 'MX5a-2025-en_US', Copyright 2024 HYUNDAI Motor America, single print (no US-portal copy exists); MX5, "
      "self-ID p.10-2/10-3 Smartstream G2.5 T-GDi 2,497cc, wheelbase 110.8 in; capacities p.10-8, viscosity p.10-9, tires "
      "+ wheel nut torque p.10-5; gated to null: 12V battery group and CCA (p.9-33 shows only an example capacity label "
      "AGM70L-DIN), " + NO_PLUG_BATT + "; Hybrid has its own manual)",
  msrc="Hyundai Owner's Manual (Santa Fe 2025 MX5, p.%s)", maint=mx_maint("9-12", "9-13", "9-14", "9-16", "9-16")),

 dict(vid=13179, label="2026 MX5  Smartstream G2.5 T-GDi", psi=None, lug=LUG_HMG,
  oil=MX_OIL,
  fluids=mx_fluids("Automatic transmission: ATF SP4M-1 (SK, MICHANG, S-OIL or other approved brands meeting the spec), "
                   "7.5 qt / 7.1 L."),
  parts=MX_PARTS,
  src="owner-manual-verified (per 2026 Hyundai Santa Fe OM, " + (GLOBAL % ("MX5a", "2026")) + " = santafe_2026_MX5a_global_OM.pdf, "
      "PDF keywords 'MX5a,2026', Copyright 2026 HYUNDAI Motor America, single print (no US-portal copy exists); MX5, "
      "self-ID p.789/790 Smartstream G2.5 T-GDi 2,497cc, wheelbase 110.8 in; capacities p.796, viscosity p.797, tires + "
      "wheel nut torque p.792; this year's book specifies a conventional automatic transmission where the 2025 book "
      "specifies a dual clutch; gated to null: 12V battery group and CCA (p.736 shows only an example capacity label "
      "AGM70L-DIN), " + NO_PLUG_BATT + "; Hybrid has its own manual)",
  msrc="Hyundai Owner's Manual (Santa Fe 2026 MX5, p.%s)", maint=mx_maint("708", "708", "710", "711", "712")),
]
DEFERRED = [(10988, 2001), (11014, 2002), (11049, 2003), (11097, 2004)]

# ---------------------------------------------------------------------------------------------------------------
def check(row):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid = row["vid"]
    want = (int(row["label"][:4]), "Hyundai", "Santa Fe")
    assert VEHICLES.get(vid) == want, (vid, "target row is not the labelled vehicle", VEHICLES.get(vid), want)
    assert ("per %d Hyundai Santa Fe OM" % want[0]) in row["src"] and ("Santa Fe %d " % want[0]) in row["msrc"], (vid, "source year")
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    for mi, mo, desc, page in row["maint"]:
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert isinstance(mi, int) and mi > 0, (vid, desc)
        assert mo is None or (isinstance(mo, int) and mo > 0), (vid, desc)
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
    # unit sanity on every "<a> qt / <b> L" pair that ships: 1 L = 1.057 US qt, within print rounding
    for s in shipped:
        for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
            qs, ls = q.split("-"), l.split("-")
            assert len(qs) == len(ls), (vid, "qt/L range shape", q, l)
            for a, b in zip(qs, ls):          # a range is compared end to end
                assert abs(float(a) - float(b) * 1.0567) <= 0.09, (vid, "qt/L mismatch", q, l, s)

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
        print("  maint : %7d mi / %s mo  %s  [p.%s]" % (mi, mo if mo else "--", desc, page))
    print("  src   : %s" % row["src"])

# ---------------------------------------------------------------------------------------------------------------
for row in ROWS:
    check(row)
print("contract checks PASS: %d vehicles, %d maintenance rows; every source classified verified with a suffix; every "
      "target id is the labelled vehicle" % (len(ROWS), sum(len(r["maint"]) for r in ROWS)))
for row in ROWS:
    show(row)

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_santafe_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
for vid, y in DEFERRED:
    s = c.execute("SELECT source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchone()
    print("  %d %s DEFERRED (no manufacturer manual on either host) -> untouched: %s" % (vid, y, s[0] if s else "none"))
bare = c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                 "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source='owner-manual-verified'").fetchone()[0]
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare)
assert bare == 424, bare
db.close()
print("DONE - %d Santa Fe rows written, %d deferred untouched." % (len(ROWS), len(DEFERRED)))
