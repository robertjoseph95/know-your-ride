# Hyundai newest-year backfill - SEVENTH Hyundai slice. 7 model years written, none deferred, 1 live value corrected.
# Written: Sonata 2025 / 2026 DN8 facelift (ids 13115 / 13181), Tucson 2025 / 2026 NX4 facelift (ids 8358 / 9972),
#          Elantra 2024 / 2025 / 2026 CN7 facelift (ids 6785 / 8360 / 9974).
# Corrected: Tucson 2024 (id 6783) coolant capacity - see PLANT BOOKS below.
# Source: ownersmanual.hyundai.com full_pdf/<CODE>/<label>/en_US (manufacturer, free, citable), saved under
#   _hyundai_manuals/{sonata,tucson,elantra}/ (gitignored); reads 2026-11-14. The US portal has no book for 2025-2027 on
#   any of the three nameplates (1,320 probes) and only an abridged 2024 Elantra, so each row has one available print.
#   Every book was identified by wheelbase + engine table + copyright year; the label is the model year for all seven.
# ** PLANT BOOKS (found 2026-11-14): the host carries two books per year for some nameplates - a bare code and the same
#    code + "a" (NX4 / NX4a, CN7 / CN7a). The manufacturer's US menu lists both Tucson codes. They can differ:
#      Tucson 2025 - NX4 and NX4a agree on every page read; both are cited.
#      Tucson 2026 - only NX4 is a complete book (the NX4a file has no capacities chapter and no schedule tables).
#      Tucson 2024 (live row) - coolant is 10.04 qt / 9.5 L in the portal book and NX4, 10.11 qt / 9.57 L in NX4a.
#      Elantra 2024-2026 - only CN7 exists (CN7a stops at label 2023); the CN7 books are served by the host but are
#      absent from its US menu.
# ** Rulings 2026-11-14 ("Accept, go read" / "Go, as recommended"), reasons live HERE and in the source suffix only:
#    R0 the unlisted CN7 2024-2026 books are the Elantra source; Tucson 2026 is written from the one complete book.
#    R1 Tucson 2024 coolant: both manufacturer figures ship, unattributed (the books do not print which vehicle is which).
#    R2 Elantra tire pressure is written per axle (34 front / 31 rear); the 18-in size at 33 / 33 goes in the note.
#    R3 drivetrain wording as printed per year (Tucson 2025 says 4WD, 2026 says AWD).
# ** Gates (null): spark-plug part number / gap (not published; interval only); 12V battery (capacity-label illustration
#    only); EPS / MDPS; Hybrid, Plug-in Hybrid and N (own manuals).
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows.
# ** S1.12 / S1.11: no bookkeeping words in shipped columns; battery_notes NULL; diff JSON = [{location, fluid_type}].
#
# Usage:  python _write_hyundai_newest_years.py            -> DRY RUN: print every row, classify every source, write nothing
#         python _write_hyundai_newest_years.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT,
#                                                             apply the one correction, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute(
    "SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model IN ('Sonata','Tucson','Elantra')")}
_c.close()

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_PHOS = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
COOL_EG = "Mixture of antifreeze and water; ethylene glycol base coolant for aluminum radiator"
COOL_EG_DW = "Mixture of antifreeze and distilled water; ethylene glycol base coolant for aluminum radiator"
BRAKE_LV = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
ATF_SP4M = "ATF SP4M-1 (SK, MICHANG, S-OIL, Hyundai genuine)"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
LUG_HMG = dict(ftlb=79.0, nm=107.0,
               note="79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)")
G25, G25T = "Smartstream G2.5 GDI", "Smartstream G2.5 T-GDI"
G20, G16T = "Smartstream G2.0", "Smartstream G1.6 T-GDi"
GLOBAL = "ownersmanual.hyundai.com full_pdf %s %s en_US"
NO_PLUG_BATT = "spark-plug part number and gap (not published, interval only), battery notes"
SYN = "Full synthetic (required)"

def diff(*pairs):
    return json.dumps([{"location": loc, "fluid_type": fl} for loc, fl in pairs], ensure_ascii=False)

# ---- Sonata DN8 facelift (2025 / 2026): the two books are text-identical on every page read except one tire size ----
SON_OIL = dict(visc="0W-20 (" + G25 + ") / 0W-30 (" + G25T + ")", type=SYN,
               cap="6.13 qt / 5.8 L (" + G25 + ") / 6.13 qt / 5.8 L (" + G25T + ")", cap_wo=None,
               spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API SN PLUS or above); SAE 0W-20 (" + G25
                    + ") / SAE 0W-30 (" + G25T + ")")
SON_FLUIDS = dict(
    trans="Automatic transmission (" + G25 + "): " + ATF_SP4M + ", 6.8 qt / 6.5 L. Dual clutch transmission (" + G25T
          + "): gear oil GS WDCTF HD G (wet DCT fluid), 3.49-3.59 qt / 3.3-3.4 L; control oil GS WDCTF HD H (wet DCT "
            "hydraulic control oil), 2.59-2.64 qt / 2.45-2.5 L.",
    brake="DOT-4", cool_type=COOL_EG_DW,
    cool_cap="9.2 qt / 8.7 L (" + G25 + ") / 9.3 qt / 8.8 L (" + G25T + ")", ps=EPS,
    diff=diff(("Rear differential (AWD)", GL5_85 + ", 0.62 qt / 0.58 L"),
              ("Transfer case (AWD)", GL5_85 + ", 0.69 qt / 0.65 L")))
SON_NOTE = ("%s35 psi front and rear at normal and maximum load. Compact spare (if equipped) T125/80D16 at 60 psi. "
            "Fuel tank 15.9 gal / 60 L.")
SON_MAINT = [
    (8000, 12, "Engine oil & filter change", "9-11"),
    (96000, None, "Spark plug replacement (" + G25 + ")", "9-12"),
    (48000, None, "Spark plug replacement (" + G25T + ")", "9-12"),
    (24000, 36, "Engine air cleaner filter replacement", "9-11"),
    (16000, 24, "Cabin air filter replacement", "9-14"),
    (8000, 12, "Tire rotation", "9-13"),
    (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-13"),
    (48000, 48, "Brake fluid replacement", "9-13"),
]
SON_GATES = ("12V battery group and CCA (the battery capacity label page shows only a label illustration, AGM70L-DIN, "
             "captioned 'the actual battery label in the vehicle may differ'), " + NO_PLUG_BATT)
def son_src(year, cpy, created, extra):
    return ("owner-manual-verified (per %d Hyundai Sonata OM, " % year + (GLOBAL % ("DN8", year))
            + " = sonata_%d_DN8_global_OM.pdf, book header 'DN8_FL_en_US', Copyright %d HYUNDAI Motor America, PDF created "
              "%s, single available print (no US-portal copy exists; this host's DN8 labels match the titled US-portal "
              "books for 2021 and 2024); DN8 facelift, self-ID p.2-11 Smartstream G2.5 GDI + G2.5 T-GDI 2,497cc, "
              "wheelbase 111.81 in; capacities p.2-15 (one oil quantity cell spans both engines), viscosity table p.2-15 "
              "and chart p.2-16 agree (chart read from a page render), tires + wheel nut torque p.2-13%s; gated to null: "
              % (year, cpy, created, extra) + SON_GATES + "; Hybrid has its own manual)")

# ---- Tucson NX4 facelift (2025 / 2026) ------------------------------------------------------------------------
TUC_OIL = dict(visc="0W-20", type=SYN, cap="6.13 qt / 5.8 L (" + G25 + ")", cap_wo=None,
               spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API SN PLUS or above); SAE 0W-20")
def tuc_fluids(drive):
    return dict(trans="Automatic transmission: " + ATF_SP4M + ", 6.87 qt / 6.5 L.",
                brake=BRAKE_LV + "; 0.87 qt / 0.82 L", cool_type=COOL_EG, cool_cap="8.99 qt / 8.51 L (" + G25 + ")",
                ps=EPS,
                diff=diff(("Rear differential (%s)" % drive, GL5_85 + ", 0.56-0.67 qt / 0.53-0.63 L"),
                          ("Transfer case (%s)" % drive, GL5_85 + ", 0.65-0.71 qt / 0.62-0.68 L")))
TUC_PARTS = dict(tire="235/65R17, 235/60R18 or 235/55R19",
                 note="17-in wheels: 235/65R17; 18-in wheels: 235/60R18; 19-in wheels: 235/55R19; 35 psi front and rear "
                      "at normal and maximum load. Compact spare (if equipped) T135/90D17 at 60 psi. "
                      "Fuel tank 14.26 gal / 54 L.")
def tuc_maint(p_oil, p_plug, p_cool, p_rot, p_cabin):
    return [
        (8000, 12, "Engine oil & filter change", p_oil),
        (96000, None, "Spark plug replacement", p_plug),
        (24000, 36, "Engine air cleaner filter replacement", p_oil),
        (16000, 24, "Cabin air filter replacement", p_cabin),
        (8000, 12, "Tire rotation", p_rot),
        (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", p_cool),
        (48000, 48, "Brake fluid replacement", p_cool),
    ]
TUC_GATES = ("12V battery group and CCA (the battery page shows only a capacity-label illustration, AGM70L-DIN, "
             "captioned 'the actual battery label in the vehicle may differ from the illustration'), " + NO_PLUG_BATT)

# ---- Elantra CN7 facelift (2024 / 2025 / 2026) ----------------------------------------------------------------
ELA_OIL = dict(visc="0W-20", type=SYN,
               cap="4.54 qt / 4.3 L (" + G20 + ") / 5.07 qt / 4.8 L (" + G16T + ")", cap_wo=None,
               spec="Full synthetic, API SN PLUS/SP or ILSAC GF-6 (API SN PLUS or above required); SAE 0W-20")
DCTF = ("Dual clutch transmission: SAE 70W API GL-4 dual clutch transmission fluid (HK D DCTF TGO-10 PLUS or SPIRAX S6 "
        "GHDE 70W DCTF PLUS), 1.7-1.8 qt / 1.6-1.7 L.")
def ela_fluids(ivt):
    return dict(trans="Intelligent variable transmission: " + ivt + ", 6.87 qt / 6.5 L. " + DCTF,
                brake="DOT-4 (" + BRAKE_LV + "); 0.74-0.85 qt / 0.7-0.8 L", cool_type=COOL_PHOS,
                cool_cap="7.82 qt / 7.4 L (" + G20 + ") / 7.19 qt / 6.8 L (" + G16T + ")", ps=EPS, diff=None)
def ela_parts(spare):
    return dict(tire="195/65R15, 205/55R16, 225/45R17 or 235/40R18",
                note="15-in wheels: 195/65R15; 16-in wheels: 205/55R16; 17-in wheels: 225/45R17; 34 psi front and 31 psi "
                     "rear. 18-in wheels: 235/40R18 at 33 psi front and rear. " + spare + " T125/80D15 or T125/80D16 at "
                     "60 psi. Fuel tank 12.4 gal / 47 L.")
def ela_maint(p_oil, p_tbl, p_cool, p_brake):
    return [
        (8000, 12, "Engine oil & filter change", p_oil),
        (96000, None, "Spark plug replacement (" + G20 + ")", p_tbl),
        (48000, None, "Spark plug replacement (" + G16T + ")", p_tbl),
        (24000, 36, "Engine air cleaner filter replacement", p_tbl),
        (16000, 24, "Cabin air filter replacement", p_tbl),
        (8000, 12, "Tire rotation", p_tbl),
        (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", p_cool),
        (48000, 48, "Brake fluid replacement", p_brake),
    ]
ELA_GATES = ("12V battery group and CCA (the battery capacity label page shows only a label illustration, CMF60L-DIN / "
             "AGM70L-DIN), " + NO_PLUG_BATT)
ELA_UNLISTED = ("this book is served by the manufacturer's host but is absent from its US menu, which stops at label "
                "2023; accepted by ruling 2026-11-14")
def ela_src(year, ident, pages):
    return ("owner-manual-verified (per %d Hyundai Elantra OM, " % year + (GLOBAL % ("CN7", year))
            + " = elantra_%d_CN7_global_OM.pdf, %s, single available print (%s); CN7 facelift, self-ID p.%s "
              "Smartstream G2.0 1,999cc + Smartstream G1.6 T-GDi 1,598cc, wheelbase 107 in, overall length 185.4 in; "
              "capacities p.%s, viscosity chart p.%s read from a page render, tires + wheel lug nut torque p.%s; gated to "
              "null: " % ((year, ident, ELA_UNLISTED) + pages) + ELA_GATES + "; Hybrid and N have their own manuals)")

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=13115, model="Sonata", label="2025 DN8 facelift  " + G25 + " + " + G25T, psi_f=35, psi_r=35, lug=LUG_HMG,
  oil=SON_OIL, fluids=SON_FLUIDS,
  parts=dict(tire="215/55R17, 235/45R18 or 245/40R19",
             note=SON_NOTE % "17-in wheels: 215/55R17; 18-in wheels: 235/45R18; 19-in wheels: 245/40R19; "),
  src=son_src(2025, 2025, "2025-04-04", ""),
  msrc="Hyundai Owner's Manual (Sonata 2025 DN8 facelift, p.%s)", maint=SON_MAINT),

 dict(vid=13181, model="Sonata", label="2026 DN8 facelift  " + G25 + " + " + G25T, psi_f=35, psi_r=35, lug=LUG_HMG,
  oil=SON_OIL, fluids=SON_FLUIDS,
  parts=dict(tire="205/65R16, 215/55R17, 235/45R18 or 245/40R19",
             note=SON_NOTE % "16-in wheels: 205/65R16; 17-in wheels: 215/55R17; 18-in wheels: 235/45R18; 19-in wheels: "
                             "245/40R19; "),
  src=son_src(2026, 2026, "2026-06-25", " (this year's table adds the 205/65R16 size)"),
  msrc="Hyundai Owner's Manual (Sonata 2026 DN8 facelift, p.%s)", maint=SON_MAINT),

 dict(vid=8358, model="Tucson", label="2025 NX4 facelift  " + G25, psi_f=35, psi_r=35, lug=LUG_HMG,
  oil=TUC_OIL, fluids=tuc_fluids("4WD"), parts=TUC_PARTS,
  src="owner-manual-verified (per 2025 Hyundai Tucson OM, " + (GLOBAL % ("NX4", 2025)) + " = "
      "tucson_2025_NX4_global_OM.pdf (Copyright 2025 HYUNDAI Motor America, PDF created 2025-08-21) and "
      + (GLOBAL % ("NX4a", 2025)) + " = tucson_2025_NX4a_global_OM.pdf (Copyright 2025, PDF created 2025-05-29): the "
      "manufacturer lists both books for this model year and they agree on every page read; no US-portal copy exists; "
      "NX4 facelift, self-ID p.10-2 Smartstream G2.5 GDI 2,497cc, wheelbase 108.4 in, overall length 182.6 in; "
      "capacities p.10-7, viscosity chart p.10-8 read from a page render, tires + wheel nut torque p.10-4; gated to "
      "null: " + TUC_GATES + "; Hybrid and Plug-in Hybrid have their own manuals)",
  msrc="Hyundai Owner's Manual (Tucson 2025 NX4 facelift, p.%s)",
  maint=tuc_maint("9-11", "9-12", "9-13", "9-15", "9-15")),

 dict(vid=9972, model="Tucson", label="2026 NX4 facelift  " + G25, psi_f=35, psi_r=35, lug=LUG_HMG,
  oil=TUC_OIL, fluids=tuc_fluids("AWD"), parts=TUC_PARTS,
  src="owner-manual-verified (per 2026 Hyundai Tucson OM, " + (GLOBAL % ("NX4", 2026)) + " = "
      "tucson_2026_NX4_global_OM.pdf, PDF keywords 'en_US,hyundaiold,NX4,2026', Copyright 2026 HYUNDAI Motor America, "
      "PDF created 2026-10-02, single usable print (no US-portal copy exists; the second book the manufacturer lists "
      "for this year, " + (GLOBAL % ("NX4a", 2026)) + ", is a 447-page file without the capacities chapter or the "
      "schedule tables, so no second book could be compared; ruling 2026-11-14); NX4 facelift, self-ID p.741/742 "
      "Smartstream G2.5 GDI 2,497cc, wheelbase 108.4 in, overall length 182.6 in; capacities p.748, viscosity chart "
      "p.749 read from a page render, tires + wheel nut torque p.744; gated to null: " + TUC_GATES + "; Hybrid and "
      "Plug-in Hybrid have their own manuals)",
  msrc="Hyundai Owner's Manual (Tucson 2026 NX4 facelift, p.%s)",
  maint=tuc_maint("654", "654", "656", "657", "658")),

 dict(vid=6785, model="Elantra", label="2024 CN7 facelift  " + G20 + " + " + G16T, psi_f=34, psi_r=31, lug=LUG_HMG,
  oil=ELA_OIL, fluids=ela_fluids("Hyundai genuine SP-CVT1"), parts=ela_parts("Compact spare"),
  src=ela_src(2024, "book header 'CN7_PE_en_US', Copyright 2023 HYUNDAI Motor America, PDF created 2024-03-15; the US "
                    "portal carries only an abridged 2024 book without capacities", ("10-2/10-3", "10-8", "10-9", "10-6")),
  msrc="Hyundai Owner's Manual (Elantra 2024 CN7 facelift, p.%s)",
  maint=ela_maint("9-11", "9-11", "9-13", "9-14")),

 dict(vid=8360, model="Elantra", label="2025 CN7 facelift  " + G20 + " + " + G16T, psi_f=34, psi_r=31, lug=LUG_HMG,
  oil=ELA_OIL, fluids=ela_fluids("Hyundai genuine SP-CVT1"), parts=ela_parts("Compact spare (if equipped)"),
  src=ela_src(2025, "PDF keywords 'en_US,hyundai,CN7,2025', Copyright 2024 HYUNDAI Motor America, PDF created "
                    "2025-07-10; no US-portal copy exists", ("677/678", "684", "685", "681")),
  msrc="Hyundai Owner's Manual (Elantra 2025 CN7 facelift, p.%s)",
  maint=ela_maint("594", "595", "596", "597")),

 dict(vid=9974, model="Elantra", label="2026 CN7 facelift  " + G20 + " + " + G16T, psi_f=34, psi_r=31, lug=LUG_HMG,
  oil=ELA_OIL, fluids=ela_fluids("MICHANG CVTF SP-CVT1 or Hyundai genuine CVTF SP-CVT1"),
  parts=ela_parts("Compact spare (if equipped)"),
  src=ela_src(2026, "PDF keywords 'en_US,hyundai,CN7,2026', Copyright 2026 HYUNDAI Motor America, PDF created "
                    "2026-10-19; no US-portal copy exists", ("681/682", "688", "689", "685")),
  msrc="Hyundai Owner's Manual (Elantra 2026 CN7 facelift, p.%s)",
  maint=ela_maint("596", "597", "598", "599")),
]

# ---- The one correction to a row that is already live (ruling R1) ----------------------------------------------
FIX = dict(vid=6783, vehicle=(2024, "Hyundai", "Tucson"), table="fluids", col="coolant_capacity",
           old="10.04 qt / 9.5 L (Smartstream G2.5 GDI)",
           new="10.04 qt / 9.5 L or 10.11 qt / 9.57 L (Smartstream G2.5 GDI)",
           mark="2026-11-14 second-book check",
           note="the manufacturer lists two 2024 Tucson manuals for the U.S.A, " + (GLOBAL % ("NX4", 2024)) + " and "
                + (GLOBAL % ("NX4a", 2024)) + "; this row's portal book and NX4 print coolant 10.04 qt / 9.5 L, NX4a "
                "prints 10.11 qt / 9.57 L (p.10-6 in each); both manufacturer figures are written, unattributed, because "
                "the books do not say which vehicle is which (ruling 2026-11-14); oil, transmission fluid, viscosity, "
                "tires, wheel nut torque and the maintenance schedule are identical in the two books")

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
               f["ps"], p["tire"], p["note"], p.get("plug_type"), p.get("plug_gap"), p.get("batt_group"),
               row["lug"]["note"]] + [d for _, _, d, _ in row["maint"]]
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
    return sum(unit_pairs(vid, s) for s in shipped)

def fix_plan(c):
    """Validate the correction against the current row and return (new_source, statement)."""
    v = c.execute("SELECT year, make, model FROM vehicles WHERE id=?", (FIX["vid"],)).fetchone()
    assert v == FIX["vehicle"], ("unexpected vehicle", FIX["vid"], v)
    rows = c.execute("SELECT %s, source FROM %s WHERE vehicle_id=?" % (FIX["col"], FIX["table"]), (FIX["vid"],)).fetchall()
    assert len(rows) == 1, (FIX["vid"], len(rows))
    have, src = rows[0]
    if have == FIX["new"] and FIX["mark"] in src:
        return None, None                                   # already applied
    assert have == FIX["old"], ("unexpected current value", have)
    assert src != BARE and src.startswith(BARE + " (") and src.endswith(")") and FIX["mark"] not in src, src[:80]
    new_src = src[:-1] + "; " + FIX["mark"] + ": " + FIX["note"] + ")"
    assert classify(new_src, FIX["table"], FIX["vid"]) == 1, "corrected source is not classified verified"
    assert not JARGON.search(FIX["new"]) and unit_pairs(FIX["vid"], FIX["new"]) == 2
    return new_src, ("UPDATE %s SET %s=?, source=? WHERE vehicle_id=?" % (FIX["table"], FIX["col"]),
                     (FIX["new"], new_src, FIX["vid"]))

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
              (vid, p.get("plug_type"), p.get("plug_gap"), None, p.get("batt_group"), None, p["tire"], row["psi_f"],
               row["psi_r"], None, None, None, None, None, p["note"], None, None, None, None, None, row["src"]))
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
    print("  plugs : %s | gap %s | battery %s" % (p.get("plug_type"), p.get("plug_gap"), p.get("batt_group")))
    print("  lug   : %s lb-ft / %s N-m | %s" % (row["lug"]["ftlb"], row["lug"]["nm"], row["lug"]["note"]))
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7s mi / %s mo  %s  [p.%s]" % (mi if mi else "--", mo if mo else "--", desc, page))
    print("  src   : %s" % row["src"])

# ---------------------------------------------------------------------------------------------------------------
npairs = sum(check(row) for row in ROWS)
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
new_src, stmt = fix_plan(_c)
_c.close()
print("contract checks PASS: %d vehicles, %d maintenance rows, %d printed unit pairs converted; every source classified "
      "verified with a suffix; every target id is the labelled vehicle"
      % (len(ROWS), sum(len(r["maint"]) for r in ROWS), npairs))
for row in ROWS:
    show(row)
print("\n=== correction to a live row: %d %s" % (FIX["vid"], FIX["vehicle"]))
if stmt is None:
    print("  already applied - nothing to do")
else:
    print("  %s.%s: %s  ->  %s" % (FIX["table"], FIX["col"], FIX["old"], FIX["new"]))
    print("  source gains: ; %s: %s" % (FIX["mark"], FIX["note"]))

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_newest_years_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
for row in ROWS:
    nid = write(c, nid, row)
    print("  wrote %d  %s %s" % (row["vid"], row["model"], row["label"]))
if stmt is not None:
    c.execute(*stmt)
    assert c.rowcount == 1, c.rowcount
    print("  corrected %d %s.%s" % (FIX["vid"], FIX["table"], FIX["col"]))
db.commit()

print("\nVerify:")
for row in ROWS:
    vid = row["vid"]
    o = c.execute("SELECT capacity_with_filter, source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchall()
    f = c.execute("SELECT coolant_capacity, differential_fluids_json FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, tire_pressure_rear, battery_group, battery_notes FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT component, torque_ft_lbs, source FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), MIN(source) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and e == 0, vid
    assert t[0][2].startswith(BARE + " (") and classify(t[0][2], "torque_specs", vid) == 1
    print("  %d: oil=%s | cool=%s | tire=%s @%s/%s | batt=%s/%s | lug=%s | maint=%d (%s)"
          % (vid, o[0][0][:34], f[0][0][:28], p[0][0], p[0][1], p[0][2], p[0][3], p[0][4], t[0][1], m[0], m[1][:42]))
r = c.execute("SELECT coolant_capacity, source FROM fluids WHERE vehicle_id=?", (FIX["vid"],)).fetchone()
assert r[0] == FIX["new"] and FIX["mark"] in r[1] and classify(r[1], "fluids", FIX["vid"]) == 1
others = [c.execute("SELECT source FROM %s WHERE vehicle_id=?" % t, (FIX["vid"],)).fetchone()[0] for t in ("oil_change", "parts", "torque_specs")]
assert all(FIX["mark"] not in s for s in others)
print("  %d: coolant=%s | fluids source carries the check note; oil / parts / torque sources unchanged" % (FIX["vid"], r[0]))
bare = c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                 "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source=?", (BARE,)).fetchone()[0]
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare)
assert bare == 424, bare
db.close()
print("DONE - %d rows written, 1 live value corrected." % len(ROWS))
