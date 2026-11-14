# Hyundai Tucson - THIRD Hyundai slice, FIRST Hyundai SUV (sets the SUV body baseline that Kona / Santa Fe /
# Palisade inherit). 6 writable; 4 deferred (untouched).
# Writable: 2018 / 2020 / 2021 TL facelift (ids 12524 / 666 / 2160), 2022 / 2023 / 2024 NX4 (ids 3689 / 5210 / 6783).
# Deferred: 2017 id 12382 (no full OM on the portal, only 2016/2018 quick-reference guides), 2019 id 12677 (portal
#   folder holds only Getting Started + Display Audio guides), 2025 id 8358 and 2026 id 9972 (not posted; 2026 row is
#   the blacklisted scrape).
# Source = owners.hyundaiusa.com glovebox-manual full owner's manuals (free, citable), saved locally as
#   _hyundai_manuals/tucson/tucson_<year>_<gen>_OM.pdf (gitignored). Reads 2026-11-10, re-read page by page 2026-11-13.
# Self-ID: every book carries the engine table (displacement) + wheelbase on its specifications page, matching the EPA
#   roster - TL 105.12 in wheelbase, NX4 108.5 in.
# ** Carry outcomes (engine predicts, the OM decides): 2.0 Nu GDI 4.23 qt = Elantra Nu MPI 4.23 (prediction of a GDI
#    difference was WRONG); 1.6T Gamma 4.76 / 2.4 Theta II 5.07 match Elantra 2020 / Sonata LF; 2.5 Smartstream 6.13
#    matches the 2024 Sonata facelift. BODY-decided SUV baseline: coolant 7.5-8.14 (TL) / 10.04-10.11 (NX4), fuel 16.38
#    gal (TL) / 14.27 gal (NX4), tires 225/60R17-245/45R19 (TL) / 235/65R17-235/55R19 (NX4), lug 79-94 lb-ft both gens.
# ** Gates (null, reasons live HERE and in the source suffix, never in shipped columns): spark-plug part number / gap
#    (no book publishes one; interval only); 12V battery group / CCA (TL books hold no 12V battery spec at all, only the
#    CR2032 fob cell; the NX4 books show only a "how to read the capacity label" teaching example - MF68L-DIN under image
#    code OTM090064L, a Santa Fe TM illustration reused - which is NOT a Tucson spec); 2022+ Hybrid / Plug-in Hybrid
#    (1.6T electrified, own 81.7 MB owner's manual - gated, gas 2.5 only written); EPS / MDPS - no power-steering fluid.
# ** Ruling 2026-11-13 (Robert, "Go, write Tucson"): record the OM normal-schedule intervals (Mazda 3 convention),
#    not the interval-free single row the Elantra / Sonata slices used. 2018 therefore carries two oil rows (Nu/Theta
#    7,500 mi / 12 mo and Gamma 1.6T 6,000 mi / 12 mo) and two plug rows (97,500 / 42,000 mi).
# ** IC-02 registry contract: EVERY row - including the lug-torque row - carries a " (...)" citation suffix. The bare
#    "owner-manual-verified" token is frozen at 424 grandfathered rows; a new bare row hard-fails the build. No suffix
#    may contain a blacklist marker ("ai-", "haiku", "scraped", "classifier", "unknown", ...) - the dry run classifies
#    every source string through files/source_registry.classify() before anything is written.
# ** Shipped-text rule (S1.12): no "GATED" / "pending" / "in OM" bookkeeping in any value column. battery_notes stays
#    NULL. differential_fluids_json is written in the renderer's own shape [{location, fluid_type}] (S1.11).
#
# Usage:  python _write_hyundai_tucson.py            -> DRY RUN: print every row, classify every source, write nothing
#         python _write_hyundai_tucson.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify, SourceRegistryError  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_TL = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
COOL_NX4 = "Mixture of antifreeze and water; ethylene glycol base coolant for aluminum radiator"
BRAKE_TL = "FMVSS 116 DOT-3 or DOT-4; 0.74-0.85 qt / 0.7-0.8 L"
BRAKE_NX4 = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
ATF_TL = "ATF SP-IV (MICHANG, SK, NOCA or Hyundai genuine)"
ATF_TL2 = "ATF SP-IV (MICHANG, SK, NOCA, Hyundai genuine or other approved brands meeting the spec)"
GL5_90 = "Hypoid gear oil API GL-5 SAE 75W/90 (Shell HD Axle Oil 75W90 or equivalent)"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
LUG_NOTE = "79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)"

def diff(rear, transfer):
    return json.dumps([{"location": "Rear differential (AWD)", "fluid_type": rear},
                       {"location": "Transfer case (AWD)", "fluid_type": transfer}], ensure_ascii=False)

# ---------------------------------------------------------------------------------------------------------------
# One entry per writable model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=12524, label="2018 TL  Gamma 1.6 Turbo-GDI + Nu 2.0 GDI + Theta 2.4 GDI",
  oil=dict(
   visc="5W-20 (Nu 2.0 GDI, Theta 2.4 GDI; API SM / ILSAC GF-4 / ACEA A5 or above) / 5W-30 (Gamma 1.6 Turbo-GDI; ACEA A5 or above)",
   type=None,
   cap="4.23 qt / 4.0 L (Nu 2.0 GDI) / 5.07 qt / 4.8 L (Theta 2.4 GDI) / 4.76 qt / 4.5 L (Gamma 1.6 Turbo-GDI)",
   spec="2.0 / 2.4 GDI: API SM and ILSAC GF-4 (or above), ACEA A5 (or above); SAE 5W-20 recommended, chart also allows 5W-30 / 10W-30 by temperature. 1.6 Turbo-GDI: ACEA A5 (or above); SAE 5W-30 recommended, chart also allows 5W-40 / 10W-30 / 15W-40 / 20W-50 by temperature."),
  fluids=dict(
   trans="Automatic transmission (Nu 2.0 GDI / Theta 2.4 GDI): " + ATF_TL + ", 7.71 qt / 7.3 L (2.0 GDI), 7.08 qt / 6.7 L (2.4 GDI). Ecoshift dual-clutch transmission (Gamma 1.6 Turbo-GDI): API GL-4 SAE 70W (HK MTF 70W, Shell Spirax S6 GHME 70W or GS MTF HD 70W), 2.01-2.11 qt / 1.9-2.0 L.",
   brake=BRAKE_TL, cool_type=COOL_TL,
   cool_cap="7.93 qt / 7.5 L (Nu 2.0 GDI) / 8.14 qt / 7.7 L (Theta 2.4 GDI) / 7.5 qt / 7.1 L (Gamma 1.6 Turbo-GDI)",
   diff=diff(GL5_90 + ", 0.56-0.67 qt / 0.53-0.63 L",
             GL5_90 + "; 0.36-0.38 qt / 0.34-0.36 L (Nu 2.0 GDI, Theta 2.4 GDI), 0.51-0.55 qt / 0.48-0.52 L (Gamma 1.6 Turbo-GDI)")),
  parts=dict(tire="225/60R17 or 245/45R19",
   note="17-in wheels: 225/60R17; 19-in wheels: 245/45R19; 35 psi front and rear at normal and maximum load. Compact spare T155/90D16 at 60 psi. Fuel tank 16.38 gal / 62 L."),
  src="owner-manual-verified (per 2018 Hyundai Tucson OM, portal file '2018 Tucson OM.pdf' = tucson_2018_TL_OM.pdf, owners.hyundaiusa.com glovebox-manual; TL facelift, self-ID engine table p.8-2 Gamma 1.6 Turbo-GDI 1,591cc + Nu 2.0 GDI 1,999cc + Theta 2.4 GDI 2,359cc, wheelbase 105.12 in; capacities p.8-8/8-9, viscosity p.8-10, tires + lug torque p.8-6, brake fluid DOT 3/4 also p.7-20; gated to null: spark-plug part number and gap (not published, interval only), 12V battery group and CCA (not published, only the CR2032 fob cell), battery notes)",
  msrc="Hyundai Owner's Manual (Tucson 2018 TL, p.%s)",
  maint=[
   (7500, 12, "Engine oil & filter change (Nu 2.0 GDI, Theta 2.4 GDI)", "7-9"),
   (6000, 12, "Engine oil & filter change (Gamma 1.6 Turbo-GDI)", "7-14"),
   (97500, None, "Spark plug replacement (Nu 2.0 GDI, Theta 2.4 GDI)", "7-9"),
   (42000, None, "Spark plug replacement (Gamma 1.6 Turbo-GDI)", "7-14"),
   (22500, 36, "Engine air cleaner filter replacement (Nu 2.0 GDI, Theta 2.4 GDI)", "7-9"),
   (18000, 36, "Engine air cleaner filter replacement (Gamma 1.6 Turbo-GDI)", "7-14"),
   (7500, 12, "Climate control (cabin) air filter replacement (Nu 2.0 GDI, Theta 2.4 GDI)", "7-9"),
   (6000, 12, "Climate control (cabin) air filter replacement (Gamma 1.6 Turbo-GDI)", "7-14"),
   (7500, None, "Tire rotation (Nu 2.0 GDI, Theta 2.4 GDI)", "7-9"),
   (6000, None, "Tire rotation (Gamma 1.6 Turbo-GDI)", "7-14"),
   (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-10, 7-15"),
  ]),

 dict(vid=666, label="2020 TL  Nu 2.0 GDI + Theta 2.4 GDI",
  oil=dict(
   visc="5W-20 (API Latest / ILSAC Latest recommended; chart also allows 5W-30 / 10W-30 by temperature)",
   type=None,
   cap="4.23 qt / 4.0 L (Nu 2.0 GDI) / 5.07 qt / 4.8 L (Theta 2.4 GDI)",
   spec="API Latest (ILSAC Latest); SAE 5W-20"),
  fluids=dict(
   trans="Automatic transmission: " + ATF_TL2 + ". Nu 2.0 GDI: 7.71 qt / 7.3 L (2WD), 7.50 qt / 7.1 L (AWD). Theta 2.4 GDI: 7.08 qt / 6.7 L (2WD and AWD).",
   brake=BRAKE_TL, cool_type=COOL_TL,
   cool_cap="7.93 qt / 7.5 L (Nu 2.0 GDI) / 8.14 qt / 7.7 L (Theta 2.4 GDI)",
   diff=diff(GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L", GL5_85 + ", 0.45-0.5 qt / 0.43-0.47 L")),
  parts=dict(tire="225/60R17, 225/55R18 or 245/45R19",
   note="17-in wheels: 225/60R17; 18-in wheels: 225/55R18; 19-in wheels: 245/45R19; 35 psi front and rear at normal and maximum load. Compact spare T155/90D16 or T135/90D17 at 60 psi. Fuel tank 16.38 gal / 62 L."),
  src="owner-manual-verified (per 2020 Hyundai Tucson OM, portal file 2020-Tucson-Owners-Manual.pdf = tucson_2020_TL_OM.pdf, owners.hyundaiusa.com glovebox-manual; TL facelift, self-ID engine table p.8-2 Nu 2.0 GDI 1,999cc + Theta 2.4 GDI 2,359cc, wheelbase 105.12 in; capacities p.8-8/8-9, viscosity p.8-10, tires + lug torque p.8-6, brake fluid DOT 3/4 also p.7-15; gated to null: spark-plug part number and gap (not published, interval only), 12V battery group and CCA (not published, only the CR2032 fob cell), battery notes)",
  msrc="Hyundai Owner's Manual (Tucson 2020 TL, p.%s)",
  maint=[
   (7500, 12, "Engine oil & filter change", "7-9"),
   (97500, None, "Spark plug replacement", "7-9"),
   (22500, 36, "Engine air cleaner filter replacement", "7-9"),
   (7500, 12, "Climate control (cabin) air filter replacement", "7-9"),
   (7500, None, "Tire rotation", "7-9"),
   (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-10"),
  ]),

 dict(vid=2160, label="2021 TL  2.0 GDI + 2.4 GDI",
  oil=dict(
   visc="5W-20 (API Latest / ILSAC Latest recommended; chart also allows 5W-30 / 10W-30 by temperature)",
   type=None,
   cap="4.23 qt / 4.0 L (2.0 GDI) / 5.07 qt / 4.8 L (2.4 GDI)",
   spec="API Latest (ILSAC Latest), API Certification Mark; SAE 5W-20"),
  fluids=dict(
   trans="Automatic transmission: " + ATF_TL2 + ". 2.0 GDI: 7.71 qt / 7.3 L (2WD), 7.50 qt / 7.1 L (AWD). 2.4 GDI: 7.08 qt / 6.7 L (2WD and AWD).",
   brake=BRAKE_TL, cool_type=COOL_TL,
   cool_cap="7.93 qt / 7.5 L (2.0 GDI) / 8.14 qt / 7.7 L (2.4 GDI)",
   diff=diff(GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L", GL5_85 + ", 0.45-0.5 qt / 0.43-0.47 L")),
  parts=dict(tire="225/60R17, 225/55R18 or 245/45R19",
   note="17-in wheels: 225/60R17; 18-in wheels: 225/55R18; 19-in wheels: 245/45R19; 35 psi front and rear at normal and maximum load. Compact spare T155/90D16 or T135/90D17 at 60 psi. Fuel tank 16.38 gal / 62 L."),
  src="owner-manual-verified (per 2021 Hyundai Tucson OM, portal file 2021-Tucson-Owners-Manual.pdf = tucson_2021_TL_OM.pdf, owners.hyundaiusa.com glovebox-manual; TL facelift, self-ID engine table p.8-2 2.0 GDI 1,999cc + 2.4 GDI 2,359cc, wheelbase 105.12 in; capacities p.8-8/8-9 byte-identical to the 2020 book, viscosity p.8-10, tires + lug torque p.8-6, brake fluid DOT 3/4 also p.7-15; gated to null: spark-plug part number and gap (not published, interval only), 12V battery group and CCA (not published, only the CR2032 fob cell), battery notes)",
  msrc="Hyundai Owner's Manual (Tucson 2021 TL, p.%s)",
  maint=[
   (7500, 12, "Engine oil & filter change", "7-9"),
   (97500, None, "Spark plug replacement", "7-9"),
   (22500, 36, "Engine air cleaner filter replacement", "7-9"),
   (7500, 12, "Climate control (cabin) air filter replacement", "7-9"),
   (7500, None, "Tire rotation", "7-9"),
   (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "7-10"),
   (30000, 48, "Brake fluid replacement", "7-11"),
  ]),

 dict(vid=3689, label="2022 NX4  Smartstream G2.5 GDI (1.6T Hybrid / Plug-in Hybrid gated: own manual)",
  oil=dict(
   visc="0W-20",
   type="Full synthetic (required)",
   cap="6.13 qt / 5.8 L (Smartstream G2.5 GDI)",
   spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API Latest / ILSAC Latest); SAE 0W-20"),
  fluids=dict(
   trans="Automatic transmission: " + ATF_TL2 + ", 6.87 qt / 6.5 L.",
   brake=BRAKE_NX4, cool_type=COOL_NX4,
   cool_cap="10.11 qt / 9.57 L (Smartstream G2.5 GDI)",
   diff=diff(GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L", GL5_85 + ", 0.65-0.71 qt / 0.62-0.68 L")),
  parts=dict(tire="235/65R17 or 235/55R19",
   note="17-in wheels: 235/65R17; 19-in wheels: 235/55R19; 35 psi front and rear at normal and maximum load. Compact spare T135/90D17 at 60 psi. Fuel tank 14.27 gal / 54 L."),
  src="owner-manual-verified (per 2022 Hyundai Tucson OM, portal file 2022-Tucson-Owners-Manual1.pdf = tucson_2022_NX4_OM.pdf, owners.hyundaiusa.com glovebox-manual; NX4, self-ID engine table p.2-12 Smartstream G 2.5 GDI 2,497cc, wheelbase 108.5 in; capacities p.2-16, viscosity p.2-17, tires + lug torque p.2-14; gated to null: spark-plug part number and gap (not published, interval only), 12V battery group and CCA (p.9-33 shows only a label-reading example MF68L-DIN under Santa Fe image code OTM090064L, not a Tucson spec), battery notes; 1.6T Hybrid / Plug-in Hybrid has its own 81.7 MB manual and is gated)",
  msrc="Hyundai Owner's Manual (Tucson 2022 NX4, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-8"),
   (96000, None, "Spark plug replacement", "9-9"),
   (24000, 36, "Engine air cleaner filter replacement", "9-9"),
   (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-10"),
   (48000, 48, "Brake fluid replacement", "9-10"),
  ]),

 dict(vid=5210, label="2023 NX4  Smartstream G2.5 GDI (1.6T Hybrid / Plug-in Hybrid gated: own manual)",
  oil=dict(
   visc="0W-20",
   type="Full synthetic (required)",
   cap="6.13 qt / 5.8 L (Smartstream G2.5 GDI)",
   spec="Full synthetic, API SN PLUS/SP or ILSAC GF-6; SAE 0W-20"),
  fluids=dict(
   trans="Automatic transmission: " + ATF_TL2 + ", 6.87 qt / 6.5 L.",
   brake=BRAKE_NX4, cool_type=COOL_NX4,
   cool_cap="10.11 qt / 9.57 L (Smartstream G2.5 GDI)",
   diff=diff(GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L", GL5_85 + ", 0.65-0.71 qt / 0.62-0.68 L")),
  parts=dict(tire="235/65R17 or 235/55R19",
   note="17-in wheels: 235/65R17; 19-in wheels: 235/55R19; 35 psi front and rear at normal and maximum load. Compact spare T135/90D17 at 60 psi. Fuel tank 14.27 gal / 54 L."),
  src="owner-manual-verified (per 2023 Hyundai Tucson OM, portal file 2023-Tucson-Owners-Manual-Full.pdf = tucson_2023_NX4_OM.pdf, owners.hyundaiusa.com glovebox-manual; NX4, self-ID engine table p.10-2 Smartstream G 2.5 GDI 2,497cc, wheelbase 108.5 in; capacities p.10-6, viscosity p.10-7, tires + lug torque p.10-4, brake fluid DOT 4 also p.9-16; gated to null: spark-plug part number and gap (not published, interval only), 12V battery group and CCA (p.9-30 shows only a label-reading example MF68L-DIN under Santa Fe image code OTM090064L, not a Tucson spec), battery notes; 1.6T Hybrid / Plug-in Hybrid has its own manual and is gated)",
  msrc="Hyundai Owner's Manual (Tucson 2023 NX4, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-9"),
   (96000, None, "Spark plug replacement", "9-10"),
   (24000, 36, "Engine air cleaner filter replacement", "9-10"),
   (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-11"),
   (48000, 48, "Brake fluid replacement", "9-11"),
  ]),

 dict(vid=6783, label="2024 NX4  Smartstream G2.5 GDI (1.6T Hybrid / Plug-in Hybrid gated: own manual)",
  oil=dict(
   visc="0W-20",
   type="Full synthetic (required)",
   cap="6.13 qt / 5.8 L (Smartstream G2.5 GDI)",
   spec="Full synthetic, API SN PLUS/SP or ILSAC GF-6; SAE 0W-20"),
  fluids=dict(
   trans="Automatic transmission: " + ATF_TL2 + ", 6.87 qt / 6.5 L.",
   brake=BRAKE_NX4, cool_type=COOL_NX4,
   cool_cap="10.04 qt / 9.5 L (Smartstream G2.5 GDI)",
   diff=diff(GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L", GL5_85 + ", 0.65-0.71 qt / 0.62-0.68 L")),
  parts=dict(tire="235/65R17 or 235/55R19",
   note="17-in wheels: 235/65R17; 19-in wheels: 235/55R19; 35 psi front and rear at normal and maximum load. Compact spare T135/90D17 at 60 psi. Fuel tank 14.27 gal / 54 L."),
  src="owner-manual-verified (per 2024 Hyundai Tucson OM, portal file 2024_Tucson_Owners_Manual.pdf = tucson_2024_NX4_OM.pdf, owners.hyundaiusa.com glovebox-manual; NX4, self-ID engine table p.10-2 Smartstream G 2.5 GDI 2,497cc, wheelbase 108.5 in; capacities p.10-6 (coolant 10.04 qt, the one change from 2023), viscosity p.10-7, tires + lug torque p.10-4, brake fluid DOT 4 also p.9-17; gated to null: spark-plug part number and gap (not published, interval only), 12V battery group and CCA (p.9-31 shows only a label-reading example MF68L-DIN under Santa Fe image code OTM090064L, not a Tucson spec), battery notes; 1.6T Hybrid / Plug-in Hybrid has its own manual and is gated)",
  msrc="Hyundai Owner's Manual (Tucson 2024 NX4, p.%s)",
  maint=[
   (8000, 12, "Engine oil & filter change", "9-10"),
   (96000, None, "Spark plug replacement", "9-11"),
   (24000, 36, "Engine air cleaner filter replacement", "9-11"),
   (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-12"),
   (48000, 48, "Brake fluid replacement", "9-12"),
  ]),
]

DEFERRED = [(12382, 2017, "no full OM on the portal"), (12677, 2019, "variant-only guides on the portal"),
            (8358, 2025, "not posted"), (9972, 2026, "not posted; blacklisted scrape row")]

# ---------------------------------------------------------------------------------------------------------------
def check(row):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid = row["vid"]
    srcs = {"oil_change": row["src"], "fluids": row["src"], "parts": row["src"], "torque_specs": row["src"]}
    for table, s in srcs.items():
        assert classify(s, table, vid) == 1, (vid, table)
    for mi, mo, desc, page in row["maint"]:
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert isinstance(mi, int) and mi > 0, (vid, desc)
        assert mo is None or (isinstance(mo, int) and mo > 0), (vid, desc)
    shipped = [row["oil"]["visc"], row["oil"]["type"], row["oil"]["cap"], row["oil"]["spec"],
               row["fluids"]["trans"], row["fluids"]["brake"], row["fluids"]["cool_type"], row["fluids"]["cool_cap"],
               row["parts"]["tire"], row["parts"]["note"], LUG_NOTE] + [d for _, _, d, _ in row["maint"]]
    for e in json.loads(row["fluids"]["diff"]):
        assert set(e) == {"location", "fluid_type"}, (vid, e)
        shipped += [e["location"], e["fluid_type"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
    # the bare frozen token must never appear: every source string carries a suffix
    assert row["src"] != "owner-manual-verified" and row["src"].startswith("owner-manual-verified (")

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
              (vid, None, None, None, None, None, p["tire"], 35, 35, None, None, None, None, None, p["note"], None,
               None, None, None, None, row["src"]))
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
    print("  tires : %s @ 35/35 psi | %s" % (row["parts"]["tire"], row["parts"]["note"]))
    print("  lug   : 79.0 lb-ft / 107.0 N-m | %s" % LUG_NOTE)
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7d mi / %s mo  %s  [p.%s]" % (mi, mo if mo else "--", desc, page))
    print("  src   : %s" % row["src"])

# ---------------------------------------------------------------------------------------------------------------
for row in ROWS:
    check(row)
print("contract checks PASS: %d vehicles, %d maintenance rows, every source classified verified with a suffix"
      % (len(ROWS), sum(len(r["maint"]) for r in ROWS)))
for row in ROWS:
    show(row)

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_tucson_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
          % (vid, o[0][0][:40], f[0][0][:34], p[0][0], p[0][1], p[0][2], p[0][3], t[0][1], m[0], m[1][:40]))
for vid, y, why in DEFERRED:
    s = c.execute("SELECT source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchone()
    print("  %d %s DEFER (%s) -> untouched: %s" % (vid, y, why, s[0] if s else "none"))
bare = c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                 "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source='owner-manual-verified'").fetchone()[0]
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare)
assert bare == 424, bare
db.close()
print("DONE - 6 Tucson rows written, 4 deferred untouched.")
