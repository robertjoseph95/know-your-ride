# Hyundai Sonata + Elantra RE-READ - EIGHTH Hyundai slice. 8 rows that were written in July in a thin format are
# re-read from the same manuals and written to the current standard. No new vehicle; the fleet tally does not change.
# Rows: Sonata 2006 NF (id 11226), 2018 LF (12523), 2021 DN8 (12853), 2024 DN8 facelift (13049);
#       Elantra 2017 AD (12379), 2020 AD facelift (669), 2021 CN7 (2163), 2022 CN7 (3691).
# This script SUPERSEDES _write_hyundai_sonata.py and _write_hyundai_elantra.py for these ids.
# Sources (both manufacturer, free, citable), saved under _hyundai_manuals/{sonata,elantra,_editions}/ (gitignored):
#   * US portal owners.hyundaiusa.com glovebox-manual - the first print of all eight (PDF Title names the year on six).
#   * ownersmanual.hyundai.com full_pdf/<CODE>/<label>/en_US - later prints for Sonata 2021 / 2024 (DN8) and Elantra
#     2021 / 2022 (CN7 = both engines, CN7a = the America-built 2.0-only book).
# ** What the July rows got wrong (found 2026-11-14, corrected here):
#      Sonata 2006 - spark-plug part numbers and gap that the cited book does not contain anywhere (removed);
#                    power-steering fluid stored as PSF-3, the book prints PSF-4.
#      Sonata 2018 - one oil grade (5W-20) for three engines; the book recommends 5W-30 for the two turbo engines.
#      Sonata 2024 - dual clutch quantities stored rounded; printed ranges restored.
# ** Rulings 2026-11-14 ("All eight, go read" / "Go, as recommended"); reasons live HERE and in the source suffix only:
#    - An engine that appears only in a later print of that year's manual is written from that print (Sonata 2021
#      G2.5 T-GDI, Elantra 2021 G1.6 T-GDi), and the source says so.
#    - EDITION CONFLICT (standing): Sonata 2021 G2.5 GDi oil capacity and the G1.6 T-GDi / G2.5 GDi coolant capacities
#      differ between the two prints -> not written. Elantra 2022 G1.6 T-GDi spark-plug interval (47,000 vs 48,000) ->
#      row not written; coolant interval after the first replacement (30,000 vs 24,000) -> first replacement only.
#    - R1 Elantra 2022 tire rotation: 8,000 mi with no months (all prints agree on the mileage; only later prints add months).
#    - R2 Elantra 2021 / 2022 fuel tank: gallon form (prints give quarts or gallons beside the same 47 L).
#    - R3 Sonata 2018 brake-fluid quantity not written (the book prints the same numbers for quarts and litres).
# ** FROZEN ROWS: seven of the eight ids already hold a wheel-nut row whose source is the bare token (part of the 424
#    frozen grandfathered rows). Their values match the manuals, so they are LEFT UNTOUCHED - this script never deletes
#    from torque_specs for them. Only Sonata 2006, which had no torque row, gains one (with a citation suffix).
# ** Gates (null): spark-plug part number / gap (no book publishes them); 12V battery except Sonata 2006 (MF68AH in a
#    specification table); EPS / MDPS (Sonata 2006 is hydraulic and is written); Sonata 2006 cold tire pressure.
# ** IC-02: every written row carries a " (...)" citation suffix. S1.12 / S1.11 as usual.
#
# Usage:  python _write_hyundai_sonata_elantra_reread.py            -> DRY RUN
#         python _write_hyundai_sonata_elantra_reread.py --write    -> backup DB, rewrite, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12

_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute(
    "SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model IN ('Sonata','Elantra')")}
_c.close()

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_PHOS = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
COOL_EG = "Mixture of antifreeze and water; ethylene glycol base coolant for aluminum radiator"
COOL_EG_DW = "Mixture of antifreeze and distilled water; ethylene glycol base coolant for aluminum radiator"
BRAKE_LV = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
ATF_SP4 = "ATF SP-IV (MICHANG, SK, NOCA, Hyundai genuine or other approved brands meeting the spec)"
ATF_SP4M = "ATF SP4M-1 (SK, MICHANG, S-OIL, Hyundai genuine)"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
MTF70 = "SAE 70W API GL-4 manual transmission fluid"
DCTF70 = "SAE 70W API GL-4 dual clutch transmission fluid"
LUG_NF = dict(ftlb=65.0, nm=None,
              note="65 to 80 lb-ft (900 to 1,100 kg-cm), wheel nut tightening torque per owner manual (range), steel and aluminium alloy wheels")
FROZEN_LUG = (79.0, 107.0)       # what the untouched frozen rows must hold
SYN = "Full synthetic (required)"
PORTAL = "owners.hyundaiusa.com glovebox-manual"
GLOBAL = "ownersmanual.hyundai.com full_pdf %s %s en_US"
NO_PLUG = "spark-plug part number and gap (not published, interval only)"
REREAD = "re-read 2026-11-14 to the current standard"
G16T, G25, G25T = "Smartstream G1.6 T-GDi", "Smartstream G2.5 GDi", "Smartstream G2.5 T-GDI"
G20 = "Smartstream G2.0"

def diff(*pairs):
    return json.dumps([{"location": loc, "fluid_type": fl} for loc, fl in pairs], ensure_ascii=False)

# ---- Elantra CN7 (2021 / 2022): capacities agree in every book of both years ----------------------------------
CN7_CAP = "4.54 qt / 4.3 L (" + G20 + ") / 5.07 qt / 4.8 L (" + G16T + ")"
CN7_SPEC = "API SN PLUS/SP or ILSAC GF-6 (API SN PLUS or above required); SAE 0W-20"
CN7_FLUIDS = dict(
    trans="Intelligent variable transmission: Hyundai genuine SP-CVT1, 6.87 qt / 6.5 L. Dual clutch transmission: "
          + DCTF70 + ", 1.7-1.8 qt / 1.6-1.7 L. Manual transmission: " + MTF70 + ", 1.6-1.7 qt / 1.5-1.6 L.",
    brake="DOT-4 (" + BRAKE_LV + "); 0.74-0.85 qt / 0.7-0.8 L", cool_type=COOL_PHOS,
    cool_cap="7.82 qt / 7.4 L (" + G20 + ") / 7.19 qt / 6.8 L (" + G16T + ")", ps=EPS, diff=None)
CN7_PARTS = dict(tire="195/65R15, 205/55R16, 225/45R17 or 235/40R18",
                 note="15-in wheels: 195/65R15; 16-in wheels: 205/55R16; 17-in wheels: 225/45R17; 34 psi front and 31 psi "
                      "rear. 18-in wheels: 235/40R18 at 33 psi front and rear. Compact spare T125/80D15 or T125/80D16 at "
                      "60 psi. Fuel tank 12.42 gal / 47 L.")
CN7_LABEL = ("12V battery group and CCA (the battery page shows only a capacity-label illustration, AGM70L-DIN, captioned "
             "'the actual battery label in the vehicle may differ')")

# ---- Sonata DN8 facelift (2024): text-identical to the 2025 book already written ------------------------------
DN8FL_NOTE = ("17-in wheels: 215/55R17; 18-in wheels: 235/45R18; 19-in wheels: 245/40R19; 35 psi front and rear at normal "
              "and maximum load. Compact spare (if equipped) T125/80D16 at 60 psi. Fuel tank 15.9 gal / 60 L.")

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book(s).
# lug=None means: keep the existing frozen wheel-nut row exactly as it is.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=11226, model="Sonata", label="2006 NF  2.4L + 3.3L", psi_f=None, psi_r=None, lug=LUG_NF,
  oil=dict(visc="5W-20 or 5W-30 (all temperatures); 10W-30 above 0 F (-18 C)", type=None,
           cap="4.54 qt / 4.3 L (2.4L) / 6.02 qt / 5.7 L (3.3L)", cap_wo=None,
           spec="API SJ, SL or above; ILSAC GF-3 or above"),
  fluids=dict(
   trans="Automatic transaxle: ATF SP-III (Hyundai genuine, Diamond or SK ATF SP-III, or other brands approved by "
         "Hyundai), 8.24 qt / 7.8 L (2.4L), 11.52 qt / 10.9 L (3.3L). Manual transaxle: Hyundai genuine MTF 75W/85 "
         "(API GL-4), 2.0 qt / 1.9 L.",
   brake="DOT 3 or DOT 4 equivalent", cool_type="Ethylene glycol base coolant for aluminum radiator",
   cool_cap="6.87 qt / 6.5 L (2.4L manual) / 6.66 qt / 6.3 L (2.4L automatic) / 8.66 qt / 8.2 L (3.3L)",
   ps="Hydraulic power steering - PSF-4 type fluid, 0.95 qt / 0.9 L", diff=None),
  parts=dict(tire="P215/60R16 or P225/50R17",
             note="Standard tire P215/60R16; optional P225/50R17. Temporary spare T125/80D16 at 60 psi. "
                  "Fuel tank 17.7 gal / 67 L.",
             batt_group="MF68AH"),
  src="owner-manual-verified (per 2006 Hyundai Sonata OM, portal file 2006_Hyundai_Sonata_OM.pdf = "
      "sonata_2006_portal_OM.pdf, " + PORTAL + ", Copyright 2005 Hyundai Motor Company; NF, self-ID engine table p.9-3 "
      "2.4L 2,359cc + 3.3L 3,342cc, wheel base 107.4 in p.9-2; lubrication chart p.9-4 (power steering PSF-4 type "
      "fluid), tire + battery + fuel p.9-2, wheel nut torque p.3-11; single print; " + REREAD + "; gated to null: "
      "spark-plug part number and gap (this book publishes neither - the numbers the earlier row carried are not in "
      "it), cold tire pressure (the book refers to the vehicle placard), battery notes)",
  msrc="Hyundai Owner's Manual (Sonata 2006 NF, p.%s)",
  maint=[
   (7500, 6, "Engine oil & filter change", "5-4"),
   (97500, 78, "Spark plug replacement (iridium coated)", "5-4"),
   (30000, 24, "Engine air cleaner filter replacement", "5-4"),
   (10000, 12, "Air conditioner (cabin) filter replacement", "5-5"),
   (60000, 60, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "5-5"),
  ]),

 dict(vid=12523, model="Sonata", label="2018 LF  1.6 T-GDI + 2.0 T-GDI + 2.4 GDI", psi_f=34, psi_r=34, lug=None,
  oil=dict(visc="5W-30 (1.6 T-GDI and 2.0 T-GDI) / 5W-20 (2.4 GDI)", type=None,
           cap="4.75 qt / 4.5 L (1.6 T-GDI) / 5.07 qt / 4.8 L (2.0 T-GDI) / 5.07 qt / 4.8 L (2.4 GDI)", cap_wo=None,
           spec="API SM, ILSAC GF-4, ACEA A5 (or above). 1.6 T-GDI and 2.0 T-GDI: SAE 5W-30 recommended, chart also "
                "allows 5W-40 / 10W-30 / 15W-40 / 20W-50 by temperature. 2.4 GDI: SAE 5W-20 recommended, chart also "
                "allows 5W-30 / 10W-30 by temperature."),
  fluids=dict(trans="Automatic transmission: " + ATF_SP4 + ", 7.50 qt / 7.1 L. Dual clutch transmission: " + DCTF70
                    + ", 2.00 qt / 1.9 L.",
              brake="FMVSS 116 DOT-3 or DOT-4", cool_type=COOL_EG,
              cool_cap="7.50 qt / 7.1 L (1.6 T-GDI) / 7.92 qt / 7.5 L (2.0 T-GDI) / 7.60 qt / 7.2 L (2.4 GDI)",
              ps=EPS, diff=None),
  parts=dict(tire="205/65R16, 215/55R17 or 235/45R18",
             note="16-in wheels: 205/65R16; 17-in wheels: 215/55R17; 18-in wheels: 235/45R18; 34 psi front and rear at "
                  "normal and maximum load. Compact spare (if equipped) T125/80D16 or T135/80D17 at 60 psi. "
                  "Fuel tank 18.5 gal / 70 L."),
  src="owner-manual-verified (per 2018 Hyundai Sonata OM, portal file 2018_Hyundai_Sonata_OM.pdf = "
      "sonata_2018_portal_OM.pdf, " + PORTAL + ", PDF title '2018 Hyundai Sonata Owner's Manual', Copyright 2017 "
      "HYUNDAI Motor America; LF, self-ID p.8-2 1.6 T-GDI 1,591cc + 2.0 T-GDI 1,998cc + 2.4 GDI 2,359cc, wheelbase "
      "110.4 in; capacities p.8-7/8-8, viscosity p.8-9 (5W-30 for the turbo engines, 5W-20 for the 2.4), tires p.8-5; "
      "single print; " + REREAD + "; gated to null: brake-fluid quantity (p.8-8 prints the same numbers for quarts and "
      "litres), 12V battery group and CCA (not published), " + NO_PLUG + ", battery notes)",
  msrc="Hyundai Owner's Manual (Sonata 2018 LF, p.%s)",
  maint=[
   (6000, 12, "Engine oil & filter change (1.6 T-GDI and 2.0 T-GDI)", "7-10"),
   (7500, 12, "Engine oil & filter change (2.4 GDI)", "7-15"),
   (42000, None, "Spark plug replacement (1.6 T-GDI and 2.0 T-GDI)", "7-10"),
   (97500, None, "Spark plug replacement (2.4 GDI)", "7-15"),
   (18000, 36, "Engine air cleaner filter replacement (1.6 T-GDI and 2.0 T-GDI)", "7-10"),
   (22500, 36, "Engine air cleaner filter replacement (2.4 GDI)", "7-15"),
   (6000, 12, "Climate control (cabin) air filter replacement (1.6 T-GDI and 2.0 T-GDI)", "7-10"),
   (7500, 12, "Climate control (cabin) air filter replacement (2.4 GDI)", "7-15"),
   (6000, None, "Tire rotation (1.6 T-GDI and 2.0 T-GDI)", "7-10"),
   (7500, None, "Tire rotation (2.4 GDI)", "7-15"),
   (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-10, 7-15"),
  ]),

 dict(vid=12853, model="Sonata", label="2021 DN8  " + G16T + " + " + G25 + " + " + G25T, psi_f=35, psi_r=35, lug=None,
  oil=dict(visc="0W-20 (" + G16T + " and " + G25 + ") / 0W-30 (" + G25T + ")", type=SYN,
           cap="5.07 qt / 4.8 L (" + G16T + ") / 6.13 qt / 5.8 L (" + G25T + ")", cap_wo=None,
           spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API SN PLUS or above)"),
  fluids=dict(
   trans="Automatic transmission: ATF SP-IV (MICHANG, SK, NOCA, S-OIL, Hyundai genuine or other approved brands meeting "
         "the spec), 6.89 qt / 6.5 L. Dual clutch transmission (" + G25T + "): gear oil GS WDCTF HD G, 3.49-3.59 qt / "
         "3.3-3.4 L; control oil GS WDCTF HD H, 2.59-2.64 qt / 2.45-2.5 L.",
   brake="DOT-4 (" + BRAKE_LV + "); 0.74-0.85 qt / 0.7-0.8 L", cool_type=COOL_EG_DW,
   cool_cap="8.59 qt / 8.13 L (" + G25T + ")", ps=EPS, diff=None),
  parts=dict(tire="205/65R16, 215/55R17, 235/45R18 or 245/40R19",
             note="16-in wheels: 205/65R16; 17-in wheels: 215/55R17; 18-in wheels: 235/45R18; 19-in wheels: 245/40R19; "
                  "35 psi front and rear at normal and maximum load. Compact spare (if equipped) T125/80D16, T135/80D17 "
                  "or T135/80D18 at 60 psi. Fuel tank 15.85 gal / 60 L (ECO package 14.79 gal / 56 L)."),
  src="owner-manual-verified (per 2021 Hyundai Sonata OM, portal file 2021-Sonata-Owners-Manual.pdf = "
      "sonata_2021_DN8_portal_OM.pdf, " + PORTAL + ", PDF title '2021 Sonata Owners Manual', Copyright 2020 HYUNDAI "
      "Motor America (first print: G1.6 T-GDi + G2.5 GDi; dims p.2-7, tires p.2-9, capacities p.2-11, viscosity p.2-12) "
      "and its later print " + (GLOBAL % ("DN8", 2021)) + " = sonata_2021_DN8_global_OM.pdf, Copyright 2021 (adds "
      "the G2.5 T-GDI; p.2-10, 2-12, 2-14, 2-15); DN8, wheelbase 111.8 in; the G2.5 T-GDI values (oil, 0W-30, dual "
      "clutch fluids, coolant, 48,000-mile plugs) appear ONLY in the later print and are written from it; every other "
      "written value is identical in both prints; schedule tables are rotated and were read from decoded text and "
      "page renders; " + REREAD + "; gated to null: G2.5 GDi oil capacity (first print 5.49 qt / 5.2 L, later print "
      "6.13 qt / 5.8 L), coolant capacity for G1.6 T-GDi and G2.5 GDi (first print 4.76 qt / 4.5 L and 5.49 qt / "
      "5.2 L, later print 8.03 qt / 7.6 L and 9.07 qt / 8.59 L), 12V battery group and CCA (not published), "
      + NO_PLUG + ", battery notes; Hybrid has its own manual)",
  msrc="Hyundai Owner's Manual (Sonata 2021 DN8, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "8-8, 8-12"),
   (40000, 60, "Spark plug replacement (" + G16T + ")", "8-8"),
   (96000, None, "Spark plug replacement (" + G25 + ")", "8-12"),
   (48000, None, "Spark plug replacement (" + G25T + ")", "8-19 of the later print"),
   (24000, 36, "Engine air cleaner filter replacement", "8-8, 8-12"),
   (16000, 24, "Climate control (cabin) air filter replacement", "8-8, 8-12"),
   (8000, None, "Tire rotation", "8-8, 8-12"),
   (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "8-8, 8-12"),
   (48000, 48, "Brake fluid replacement", "8-10, 8-14"),
  ]),

 dict(vid=13049, model="Sonata", label="2024 DN8 facelift  " + G25 + " + " + G25T, psi_f=35, psi_r=35, lug=None,
  oil=dict(visc="0W-20 (" + G25 + ") / 0W-30 (" + G25T + ")", type=SYN,
           cap="6.13 qt / 5.8 L (" + G25 + ") / 6.13 qt / 5.8 L (" + G25T + ")", cap_wo=None,
           spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API SN PLUS or above); SAE 0W-20 (" + G25
                + ") / SAE 0W-30 (" + G25T + ")"),
  fluids=dict(
   trans="Automatic transmission (" + G25 + "): " + ATF_SP4M + ", 6.8 qt / 6.5 L. Dual clutch transmission (" + G25T
         + "): gear oil GS WDCTF HD G (wet DCT fluid), 3.49-3.59 qt / 3.3-3.4 L; control oil GS WDCTF HD H (wet DCT "
           "hydraulic control oil), 2.59-2.64 qt / 2.45-2.5 L.",
   brake="DOT-4", cool_type=COOL_EG_DW,
   cool_cap="9.2 qt / 8.7 L (" + G25 + ") / 9.3 qt / 8.8 L (" + G25T + ")", ps=EPS,
   diff=diff(("Rear differential (AWD)", GL5_85 + ", 0.62 qt / 0.58 L"),
             ("Transfer case (AWD)", GL5_85 + ", 0.69 qt / 0.65 L"))),
  parts=dict(tire="215/55R17, 235/45R18 or 245/40R19", note=DN8FL_NOTE),
  src="owner-manual-verified (per 2024 Hyundai Sonata OM, portal file '24 Sonata OM.pdf' = "
      "sonata_2024_DN8_portal_OM.pdf, " + PORTAL + ", book header 'DN8_FL_en_US', Copyright 2023 HYUNDAI Motor America; "
      "DN8 facelift, self-ID p.2-11 Smartstream G2.5 GDI + G2.5 T-GDI 2,497cc, wheelbase 111.81 in; capacities p.2-15, "
      "viscosity table p.2-15 and chart p.2-16 agree (chart read from a page render), tires p.2-13; cross-checked "
      "against the later print " + (GLOBAL % ("DN8", 2024)) + ": specification and schedule pages are text-identical; "
      + REREAD + " (dual clutch quantities now carry the printed ranges; all-wheel-drive entries added); gated to "
      "null: 12V battery group and CCA (p.9-33 shows only a capacity-label illustration, AGM70L-DIN), " + NO_PLUG
      + ", battery notes; Hybrid has its own manual)",
  msrc="Hyundai Owner's Manual (Sonata 2024 DN8 facelift, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-11"),
   (96000, None, "Spark plug replacement (" + G25 + ")", "9-12"),
   (48000, None, "Spark plug replacement (" + G25T + ")", "9-12"),
   (24000, 36, "Engine air cleaner filter replacement", "9-11"),
   (16000, 24, "Cabin air filter replacement", "9-14"),
   (8000, 12, "Tire rotation", "9-13"),
   (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-13"),
   (48000, 48, "Brake fluid replacement", "9-13"),
  ]),

 dict(vid=12379, model="Elantra", label="2017 AD  Nu 2.0 MPI", psi_f=None, psi_r=None, lug=None,
  oil=dict(visc="5W-20 (recommended; chart also allows 5W-30 and 10W-30 by temperature)", type=None,
           cap="4.23 qt / 4.0 L (Nu 2.0 MPI)", cap_wo=None,
           spec="API SM and ILSAC GF-4 (or above), ACEA A5 (or above); SAE 5W-20"),
  fluids=dict(trans="Automatic transmission: " + ATF_SP4 + ", 7.08 qt / 6.7 L. Manual transmission: " + MTF70
                    + ", 1.8-1.9 qt / 1.7-1.8 L.",
              brake="FMVSS 116 DOT-3 or DOT-4; 0.74-0.85 qt / 0.7-0.8 L", cool_type=COOL_PHOS,
              cool_cap="6.34 qt / 6.0 L (manual transmission) / 6.97 qt / 6.6 L (automatic transmission)",
              ps=EPS, diff=None),
  parts=dict(tire="195/65R15, 205/55R16 or 225/45R17",
             note="15-in wheels: 195/65R15 and 16-in wheels: 205/55R16 at 36 psi; 17-in wheels: 225/45R17 at 33 psi; "
                  "front and rear at normal and maximum load. Compact spare (if equipped) T125/80D15 at 60 psi. "
                  "Fuel tank 14.0 gal / 53 L."),
  src="owner-manual-verified (per 2017 Hyundai Elantra OM, portal file 2017_Hyundai_Elantra_OM.pdf = "
      "elantra_2017_portal_OM.pdf, " + PORTAL + ", PDF title '2017 Hyundai Elantra Owner's Manual', Copyright 2016 "
      "HYUNDAI Motor America; AD, self-ID p.8-2 Nu 2.0 MPI 1,999cc, wheelbase 106.3 in (this book carries the 2.0 "
      "only); capacities p.8-7/8-8, viscosity p.8-9, tires p.8-5; single print; " + REREAD + "; gated to null: 12V "
      "battery group and CCA (not published), " + NO_PLUG + ", battery notes)",
  msrc="Hyundai Owner's Manual (Elantra 2017 AD, p.%s)",
  maint=[
   (7500, 12, "Engine oil & filter change", "7-8"),
   (97500, 78, "Spark plug replacement (iridium coated)", "7-16"),
   (30000, 24, "Engine air cleaner filter replacement", "7-9"),
   (15000, 12, "Climate control (cabin) air filter replacement", "7-8"),
   (7500, 6, "Tire rotation", "7-8"),
   (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-18"),
  ]),

 dict(vid=669, model="Elantra", label="2020 AD facelift  2.0 MPI + 1.6 T-GDI", psi_f=None, psi_r=None, lug=None,
  oil=dict(visc="5W-20 (2.0 MPI) / 5W-30 (1.6 T-GDI)", type=None,
           cap="4.23 qt / 4.0 L (2.0 MPI) / 4.76 qt / 4.5 L (1.6 T-GDI)", cap_wo=None,
           spec="2.0 MPI: API latest (ILSAC latest); SAE 5W-20 recommended, chart also allows 5W-30 / 10W-30 by "
                "temperature. 1.6 T-GDI: API latest (ILSAC latest) or ACEA A5/B5; SAE 5W-30 recommended, chart also "
                "allows 5W-40 / 10W-30 / 15W-40 by temperature."),
  fluids=dict(trans="Intelligent variable transmission (2.0 MPI): IVT fluid SP-CVT1, 6.86 qt / 6.5 L. Dual clutch "
                    "transmission (1.6 T-GDI): " + DCTF70 + ", 2.01-2.11 qt / 1.9-2.0 L. Manual transmission: " + MTF70
                    + ", 1.6-1.7 qt / 1.5-1.6 L.",
              brake="FMVSS 116 DOT-3 or DOT-4; 0.74-0.85 qt / 0.7-0.8 L", cool_type=COOL_PHOS,
              cool_cap="6.45 qt / 6.1 L (1.6 T-GDI) / 6.34 qt / 6.0 L (2.0 MPI manual) / 6.97 qt / 6.6 L (2.0 MPI IVT)",
              ps=EPS, diff=None),
  parts=dict(tire="195/65R15, 205/55R16, 225/45R17 or 225/40R18",
             note="15-in wheels: 195/65R15 at 36 psi; 16-in wheels: 205/55R16, 17-in wheels: 225/45R17 and 18-in wheels: "
                  "225/40R18 at 33 psi; front and rear at normal and maximum load. Compact spare (if equipped) "
                  "T125/80D15 or T125/80D16 at 60 psi. Fuel tank 14.0 gal / 53 L."),
  src="owner-manual-verified (per 2020 Hyundai Elantra OM, portal file '2020 Elantra Owner's Manual.pdf' under the "
      "portal's misspelled folder /2020/elentra/ = elantra_2020_portal_OM.pdf, " + PORTAL + ", PDF title '2020 Elantra "
      "Owner's Manual', Copyright 2019 HYUNDAI Motor America; AD facelift, self-ID p.8-2 1.6 T-GDI 1,591cc + 2.0 MPI "
      "1,999cc, wheelbase 106.3 in; capacities p.8-7/8-8, viscosity p.8-9, tires p.8-5; single print; " + REREAD
      + "; gated to null: 12V battery group and CCA (not published), " + NO_PLUG + ", battery notes)",
  msrc="Hyundai Owner's Manual (Elantra 2020 AD facelift, p.%s)",
  maint=[
   (7500, 12, "Engine oil & filter change (2.0 MPI)", "7-8"),
   (6000, 12, "Engine oil & filter change (1.6 T-GDI)", "7-13"),
   (97500, None, "Spark plug replacement (2.0 MPI)", "7-8"),
   (42000, None, "Spark plug replacement (1.6 T-GDI)", "7-13"),
   (30000, 48, "Engine air cleaner filter replacement (2.0 MPI)", "7-8"),
   (24000, 48, "Engine air cleaner filter replacement (1.6 T-GDI)", "7-13"),
   (None, 12, "Climate control (cabin) air filter replacement", "7-8, 7-13"),
   (7500, None, "Tire rotation (2.0 MPI)", "7-8"),
   (6000, None, "Tire rotation (1.6 T-GDI)", "7-13"),
   (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-8, 7-13"),
  ]),

 dict(vid=2163, model="Elantra", label="2021 CN7  " + G20 + " + " + G16T, psi_f=34, psi_r=31, lug=None,
  oil=dict(visc="0W-20", type=None, cap=CN7_CAP, cap_wo=None, spec=CN7_SPEC),
  fluids=CN7_FLUIDS, parts=CN7_PARTS,
  src="owner-manual-verified (per 2021 Hyundai Elantra OM, portal file 2021-Elantra-Owners-Manual.pdf = "
      "elantra_2021_portal_OM.pdf, " + PORTAL + ", PDF title '2021 Elantra Owners Manual', Copyright 2020 HYUNDAI "
      "Motor America (first print, Smartstream G2.0 only; dims p.2-7, tires p.2-9, capacities p.2-11, viscosity "
      "p.2-12) and two later prints of the same model year: " + (GLOBAL % ("CN7a", 2021)) + " (Copyright 2021, G2.0 "
      "only) and " + (GLOBAL % ("CN7", 2021)) + " = elantra_2021_CN7_global_OM.pdf (Copyright 2021, G2.0 + G1.6 "
      "T-GDi; p.2-9, 2-11, 2-13, 2-14); CN7, wheelbase 107 in; all three books agree on every G2.0 value; the G1.6 "
      "T-GDi values (oil, dual clutch and manual transmission fluid, coolant, 235/40R18 tire, 47,000-mile plugs) appear "
      "ONLY in the CN7 print and are written from it; fuel tank is 47 L in every book (printed beside 49.66 US qt or "
      "12.42 US gal); schedule tables are rotated and were read from decoded text and page renders; " + REREAD
      + "; gated to null: " + CN7_LABEL + ", " + NO_PLUG + ", battery notes; Hybrid and N have their own manuals)",
  msrc="Hyundai Owner's Manual (Elantra 2021 CN7, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-8"),
   (96000, None, "Spark plug replacement (" + G20 + ")", "9-8"),
   (47000, None, "Spark plug replacement (" + G16T + ")", "9-8 of the later print"),
   (24000, 36, "Engine air cleaner filter replacement", "9-8"),
   (16000, 24, "Cabin air filter replacement", "9-8"),
   (8000, None, "Tire rotation", "9-8"),
   (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "9-8"),
   (48000, 48, "Brake fluid replacement", "9-10"),
  ]),

 dict(vid=3691, model="Elantra", label="2022 CN7  " + G20 + " + " + G16T, psi_f=34, psi_r=31, lug=None,
  oil=dict(visc="0W-20", type=None, cap=CN7_CAP, cap_wo=None, spec=CN7_SPEC),
  fluids=CN7_FLUIDS, parts=CN7_PARTS,
  src="owner-manual-verified (per 2022 Hyundai Elantra OM, portal file 2022-Elantra-Owners-Manual.pdf = "
      "elantra_2022_portal_OM.pdf, " + PORTAL + ", Copyright 2020 HYUNDAI Motor America, PDF created 2021-11-03 "
      "(first print, G2.0 + G1.6 T-GDi; dims p.2-9, tires p.2-11, capacities p.2-13, viscosity p.2-14) and two later "
      "prints: " + (GLOBAL % ("CN7", 2022)) + " = elantra_2022_CN7_global_OM.pdf (Copyright 2022, both engines) and "
      + (GLOBAL % ("CN7a", 2022)) + " (G2.0 only); CN7, wheelbase 107 in; capacities and tires agree in all three "
      "books; fuel tank is 47 L in every book (printed beside 49.66 US qt or 12.42 US gal); schedule tables are "
      "rotated and were read from decoded text and page renders; the prints dispute three schedule items, so only "
      "what they state identically is written; " + REREAD + "; gated to null: G1.6 T-GDi spark-plug interval (first "
      "print 47,000 mi, later print 48,000 mi), coolant interval after the first replacement (30,000 mi in the first "
      "print and CN7a, 24,000 mi in CN7), tire-rotation months (none in the first print, 12 in the later prints), "
      "full-synthetic requirement (later print only), " + CN7_LABEL + ", " + NO_PLUG + ", battery notes; Hybrid and N "
      "have their own manuals)",
  msrc="Hyundai Owner's Manual (Elantra 2022 CN7, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-8"),
   (96000, None, "Spark plug replacement (" + G20 + ")", "9-8"),
   (24000, 36, "Engine air cleaner filter replacement", "9-8"),
   (16000, 24, "Cabin air filter replacement", "9-8"),
   (8000, None, "Tire rotation", "9-8"),
   (120000, 120, "Engine coolant first replacement", "9-9"),
   (48000, 48, "Brake fluid replacement", "9-10"),
  ]),
]

# ---------------------------------------------------------------------------------------------------------------
def unit_pairs(vid, s):
    """Every printed US / metric pair must convert, within print rounding. Returns the number of pairs checked."""
    n = 0
    for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
        qs, ls = q.split("-"), l.split("-")
        assert len(qs) == len(ls), (vid, "qt/L range shape", q, l)
        for a, b in zip(qs, ls):          # 1 L = 1.0567 US qt
            assert abs(float(a) - float(b) * 1.0567) <= 0.09, (vid, "qt/L mismatch", q, l, s)
            n += 1
    for g, l in re.findall(r"([0-9.]+) gal / ([0-9.]+) L", s or ""):
        dec = len(g.split(".")[1]) if "." in g else 0        # 1 US gal = 3.7854 L; tolerance follows the printed precision
        assert abs(float(g) - float(l) / 3.7854) <= max(0.03, 0.5 * 10 ** -dec + 0.005), (vid, "gal/L mismatch", g, l, s)
        n += 1
    assert not re.search(r"[0-9] (?:qt|gal)(?! /)", s or ""), (vid, "unpaired US unit", s)
    return n

def check(row, c):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid, model = row["vid"], row["model"]
    want = (int(row["label"][:4]), "Hyundai", model)
    assert VEHICLES.get(vid) == want, (vid, "target row is not the labelled vehicle", VEHICLES.get(vid), want)
    assert ("per %d Hyundai %s OM" % (want[0], model)) in row["src"] and ("%s %d " % (model, want[0])) in row["msrc"], (vid, "source year")
    for table in ("oil_change", "fluids", "parts") + (("torque_specs",) if row["lug"] else ()):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    for mi, mo, desc, page in row["maint"]:
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert mi is None or (isinstance(mi, int) and mi > 0), (vid, desc)
        assert mo is None or (isinstance(mo, int) and mo > 0), (vid, desc)
        assert mi is not None or mo is not None, (vid, desc, "a row needs an interval")
    o, f, p = row["oil"], row["fluids"], row["parts"]
    shipped = [o["visc"], o["type"], o["cap"], o["cap_wo"], o["spec"], f["trans"], f["brake"], f["cool_type"], f["cool_cap"],
               f["ps"], p["tire"], p["note"], p.get("plug_type"), p.get("plug_gap"), p.get("batt_group")] \
              + [d for _, _, d, _ in row["maint"]] + ([row["lug"]["note"]] if row["lug"] else [])
    for e in (json.loads(f["diff"]) if f["diff"] else []):
        assert set(e) == {"location", "fluid_type"}, (vid, e)
        shipped += [e["location"], e["fluid_type"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
    assert row["src"] != BARE and row["src"].startswith(BARE + " (") and row["src"].endswith(")")
    for k in ("psi_f", "psi_r"):
        assert row[k] is None or isinstance(row[k], int), (vid, k)
    # this is a RE-READ: the row must already exist, verified, in the three rewritten tables
    for t in ("oil_change", "fluids", "parts"):
        cur = c.execute("SELECT source FROM %s WHERE vehicle_id=?" % t, (vid,)).fetchall()
        assert len(cur) == 1 and cur[0][0].startswith(BARE + " ("), (vid, t, "expected one verified, suffixed row")
    tq = c.execute("SELECT torque_ft_lbs, torque_nm, source FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    if row["lug"] is None:
        assert len(tq) == 1 and tq[0][:2] == FROZEN_LUG and tq[0][2] == BARE, (vid, "frozen wheel-nut row is not as expected", tq)
    else:
        assert tq == [] or (len(tq) == 1 and tq[0][2] != BARE), (vid, "would replace a frozen row", tq)
    return sum(unit_pairs(vid, s) for s in shipped)

def write(c, nid, row):
    vid, o, f, p, lug = row["vid"], row["oil"], row["fluids"], row["parts"], row["lug"]
    for t in ["oil_change", "fluids", "parts", "maintenance", "engine_specs"] + (["torque_specs"] if lug else []):
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
              (vid, p.get("plug_type"), p.get("plug_gap"), None, p.get("batt_group"), None, p["tire"], row["psi_f"],
               row["psi_r"], None, None, None, None, None, p["note"], None, None, None, None, None, row["src"]))
    if lug:
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
    print("  oil   : %s | %s | %s" % (o["cap"], o["visc"], o["type"]))
    print("  spec  : %s" % o["spec"])
    print("  trans : %s" % f["trans"])
    print("  cool  : %s | %s" % (f["cool_cap"], f["cool_type"]))
    print("  brake : %s" % f["brake"])
    print("  steer : %s" % f["ps"])
    for e in (json.loads(f["diff"]) if f["diff"] else []):
        print("  diff  : %s -> %s" % (e["location"], e["fluid_type"]))
    print("  tires : %s @ %s front / %s rear psi | %s" % (p["tire"], row["psi_f"], row["psi_r"], p["note"]))
    print("  plugs : %s | gap %s | battery %s" % (p.get("plug_type"), p.get("plug_gap"), p.get("batt_group")))
    print("  lug   : %s" % (row["lug"]["note"] if row["lug"] else "existing frozen wheel-nut row kept as it is (79 lb-ft / 107 N-m)"))
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7s mi / %s mo  %s  [p.%s]" % (mi if mi else "--", mo if mo else "--", desc, page))
    print("  src   : %s" % row["src"])

def bare_count(c):
    return c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                     "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source=?", (BARE,)).fetchone()[0]

# ---------------------------------------------------------------------------------------------------------------
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
npairs = sum(check(row, _c) for row in ROWS)
before = bare_count(_c)
old_maint = _c.execute("SELECT COUNT(*) FROM maintenance WHERE vehicle_id IN (%s)" % ",".join(str(r["vid"]) for r in ROWS)).fetchone()[0]
_c.close()
assert before == 424, before
print("contract checks PASS: %d vehicles, %d maintenance rows (replacing %d), %d printed unit pairs converted; every source "
      "classified verified with a suffix; every target id is the labelled vehicle; 7 frozen wheel-nut rows untouched"
      % (len(ROWS), sum(len(r["maint"]) for r in ROWS), old_maint, npairs))
for row in ROWS:
    show(row)

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_reread_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
try:
    for row in ROWS:
        nid = write(c, nid, row)
        print("  wrote %d  %s %s" % (row["vid"], row["model"], row["label"]))
    assert bare_count(c) == 424, ("freeze would break", bare_count(c))      # checked BEFORE commit
    db.commit()
except Exception:
    db.rollback()
    raise

print("\nVerify:")
for row in ROWS:
    vid = row["vid"]
    o = c.execute("SELECT capacity_with_filter, source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchall()
    f = c.execute("SELECT coolant_capacity, power_steering_fluid FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, tire_pressure_rear, spark_plug_type, spark_plugs_json, battery_group, battery_notes FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT torque_ft_lbs, source FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), SUM(mileage_interval IS NULL AND months_interval IS NULL) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and m[1] == 0 and e == 0, vid
    assert p[0][3] is None and p[0][4] is None and p[0][6] is None, (vid, "plug data or battery notes present")
    assert (t[0][1] == BARE) == (row["lug"] is None), (vid, "wheel-nut row state")
    print("  %d: oil=%s | cool=%s | tire=%s @%s/%s | batt=%s | lug=%s (%s) | maint=%d"
          % (vid, o[0][0][:30], str(f[0][0])[:26], p[0][0][:34], p[0][1], p[0][2], p[0][5], t[0][0],
             "frozen row kept" if t[0][1] == BARE else "new, cited", m[0]))
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare_count(c))
db.close()
print("DONE - %d rows re-read and rewritten." % len(ROWS))
