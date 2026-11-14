# Hyundai Venue (QX) - NINTH Hyundai slice. 3 model years written: 2020 (id 677), 2021 (id 2170), 2026 (id 9980).
# The three ids held only blacklisted-source rows (ai-generated / scraped), which never shipped; this replaces them.
# Source: Hyundai owner's manuals (manufacturer, free, citable), saved under _hyundai_manuals/venue/ (gitignored); reads
#   2026-11-14. Two hosts:
#     US portal  owners.hyundaiusa.com/content/dam/hyundai/us/myhyundai/manuals/glovebox-manual/<YEAR>/venue/<file>
#                (first print; PDF title names the model year; has 2020-2024, nothing for 2025 / 2026)
#     second     ownersmanual.hyundai.com full_pdf QX <label> en_US  (later print; labels 2020-2026)
#   Every book was identified by the Venue body on the exterior overview, wheelbase 99.2 in, Smartstream G1.6 1,598cc
#   and the HYUNDAI Motor America copyright. The QX label IS the model year: QX/2020 has the same copyright year and
#   page count as the titled 2021 portal book, but its schedule steps by 7,500 miles like the titled 2020 book, while
#   the titled 2021 book steps by 8,000.
# ** PRINTS AGREE: portal 2020 vs QX/2020 and portal 2021 vs QX/2021 are identical (direct page diffs) on dimensions,
#    tires, weights, capacities and all three normal-schedule pages. 2026 has one available print.
# ** Rulings 2026-11-14 ("Go, as recommended"), reasons live HERE and in the source suffix only:
#    R1 UNIT RULING applied: the intelligent variable transmission fluid quantity (printed 6.34 US qt beside 6.7 L;
#       6.7 L = 7.08 qt) and the coolant quantity for that transmission (printed 6.32 US qt beside 5.78 L; 5.78 L =
#       6.11 qt) do not convert, in every book -> neither quantity is written. The 2020 / 2021 coolant column carries
#       the manual-transmission figure only; the 2026 coolant quantity is NULL.
#    R2 the 2021 books still list a manual transmission -> written as printed, marked "if equipped" (2020 and 2021).
#    R3 the 2020 severe-usage table is headed "Nu 2.0 MPI", an engine this vehicle does not have (both prints, gone
#       from 2021 on). Severe rows are never written; the 2020 NORMAL schedule carries no engine label, is identical
#       in both prints, and is written.
# ** Tire pressure differs by wheel size (15-in 36 psi, 17-in 33 psi) -> numeric columns NULL, pressures in the note.
# ** Gates (null): spark-plug part number / gap and 12V battery (neither is published); EPS / MDPS has no fluid.
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows (checked BEFORE
#    commit). S1.12 / S1.11: no bookkeeping words in shipped columns; battery_notes NULL.
#
# Usage:  python _write_hyundai_venue.py            -> DRY RUN: print every row, classify every source, write nothing
#         python _write_hyundai_venue.py --write    -> backup DB, DELETE the 6 curated tables per id, INSERT, verify
import sqlite3, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
NO_CONVERT = re.compile(r"6\.34|6\.7 L|6\.32|5\.78")                          # R1: must never reach a shipped column
TABLES = ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]

# Target-row guard: every id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Venue'")}
_c.close()
assert sorted(VEHICLES) == [677, 2170, 9980], ("the Venue rows are not the three expected", sorted(VEHICLES))

G16 = "Smartstream G1.6"
EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_PHOS = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
BRAKE = "DOT-4 (SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6); 0.74-0.85 qt / 0.7-0.8 L"
LUG = dict(ftlb=79.0, nm=107.0,
           note="79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)")
IVT_GEN = "Intelligent variable transmission: CVTF SP-CVT1 (use only the specified genuine fluid)."
MTF = ("Manual transmission (if equipped): API GL-4 SAE 70W TGO-9 manual transmission fluid (HK SYN MTF 70W, SPIRAX S6 "
       "GHME 70W MTF or GS MTF HD 70W), 1.59-1.69 qt / 1.5-1.6 L.")
PARTS = dict(tire="185/65R15 or 205/55R17",
             note="15-in wheels: 185/65R15 at 36 psi; 17-in wheels: 205/55R17 at 33 psi; front and rear at normal and "
                  "maximum load. Compact spare (if equipped) T125/80D15 or T125/80D16 at 60 psi. "
                  "Fuel tank 11.89 gal / 45 L.")
SYN = "Full synthetic (required)"
OIL_SYN = dict(visc="0W-20", type=SYN, cap="4.02 qt / 3.8 L", cap_wo=None,
               spec="API SN PLUS/SP or ILSAC GF-6, full synthetic required (API SN PLUS or above); SAE 0W-20")
PORTAL = "owners.hyundaiusa.com glovebox-manual"
GLOBAL = "ownersmanual.hyundai.com full_pdf QX %d en_US"
SELF_ID = ("QX, self-ID p.2-7 Smartstream G1.6 1,598cc, wheelbase 99.2 in, overall length 159.0 in, Venue body on the "
           "exterior overview p.2-2; capacities p.2-11, viscosity chart p.2-12 read from a page render, tires + wheel lug "
           "nut torque p.2-9; the book prints tire pressure per wheel size, carried in the tire note")
UNIT_IVT = ("the intelligent variable transmission fluid quantity (printed 6.34 US qt beside 6.7 L, which do not convert; "
            "unit ruling 2026-11-14)")
GATES = ("gated to null: 12V battery group and CCA (not published), spark-plug part number and gap (not published, "
         "interval only), battery notes")

# ---------------------------------------------------------------------------------------------------------------
# One entry per model year. Every value below was read from the cited page of that year's own book.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=677, model="Venue", label="2020 QX  " + G16, psi_f=None, psi_r=None, lug=LUG,
  oil=dict(visc="0W-20 (recommended); chart also allows 5W-20, 0W-30 and 5W-30 (all temperatures) and 10W-30 above "
                "0 F (-18 C)",
           type=None, cap="4.02 qt / 3.8 L", cap_wo=None,
           spec="API latest (SN PLUS); where that oil is not available, API SL / ILSAC GF-3 or ACEA A3; SAE 0W-20 "
                "recommended, chart also allows 5W-20 / 0W-30 / 5W-30 / 10W-30 by temperature"),
  fluids=dict(trans=IVT_GEN + " " + MTF, brake=BRAKE, cool_type=COOL_PHOS,
              cool_cap="5.94 qt / 5.62 L (manual transmission)", ps=EPS, diff=None),
  parts=PARTS,
  src="owner-manual-verified (per 2020 Hyundai Venue OM, portal file '2020 Venue Owner's Manual.pdf' = "
      "venue_2020_portal_OM.pdf, " + PORTAL + ", PDF title '2020 Venue Owner's Manual', Copyright 2019 HYUNDAI Motor "
      "America (first print), cross-checked against the later print " + (GLOBAL % 2020) + " = "
      "venue_2020_QX_global_OM.pdf (Copyright 2020): dimensions, tires, weights, capacities and all three normal-schedule "
      "pages are identical in the two prints; " + SELF_ID + "; the QX label is the model year (this later print steps "
      "its schedule by 7,500 miles like the titled portal book, the 2021 books step by 8,000); not written: " + UNIT_IVT
      + " and the coolant quantity for that transmission (printed 6.32 US qt beside 5.78 L, which do not convert), so "
      "the coolant column carries the manual-transmission figure only; the severe-usage table p.8-11 is headed 'Nu 2.0 "
      "MPI', an engine this vehicle does not have, in both prints - the normal schedule p.8-8 to 8-10 carries no engine "
      "label and is written (ruling 2026-11-14); the capacities table prints 'API Lastest'; brake fluid is "
      "inspect-only in this year's schedule; " + GATES + ")",
  msrc="Hyundai Owner's Manual (Venue 2020 QX, p.%s)",
  maint=[
      (7500, 12, "Engine oil & filter change", "8-8"),
      (97500, None, "Spark plug replacement", "8-8"),
      (30000, 48, "Engine air cleaner filter replacement", "8-8"),
      (15000, 12, "Climate control (cabin) air filter replacement", "8-8"),
      (7500, None, "Tire rotation", "8-8"),
      (120000, 120, "Engine coolant first replacement; thereafter every 30,000 mi / 24 months", "8-8"),
  ]),

 dict(vid=2170, model="Venue", label="2021 QX  " + G16, psi_f=None, psi_r=None, lug=LUG,
  oil=OIL_SYN,
  fluids=dict(trans=IVT_GEN + " " + MTF, brake=BRAKE, cool_type=COOL_PHOS,
              cool_cap="5.94 qt / 5.62 L (manual transmission)", ps=EPS, diff=None),
  parts=PARTS,
  src="owner-manual-verified (per 2021 Hyundai Venue OM, portal file 2021-Venue-Owners-Manual.pdf = "
      "venue_2021_portal_OM.pdf, " + PORTAL + ", PDF title '2021 Venue Owners Manual', Copyright 2020 HYUNDAI Motor "
      "America (first print; its text is glyph-coded and was decoded), cross-checked against the later print "
      + (GLOBAL % 2021) + " = venue_2021_QX_global_OM.pdf (Copyright 2021): dimensions, tires, weights, capacities and "
      "all three normal-schedule pages are identical in the two prints (the later print only adds a notice on p.8-7); "
      + SELF_ID + "; both prints still list a manual transmission, written as printed, if equipped (ruling 2026-11-14); "
      "not written: " + UNIT_IVT + " and the coolant quantity for that transmission (printed 6.32 US qt beside 5.78 L, "
      "which do not convert), so the coolant column carries the manual-transmission figure only; " + GATES + ")",
  msrc="Hyundai Owner's Manual (Venue 2021 QX, p.%s)",
  maint=[
      (8000, 12, "Engine oil & filter change", "8-8"),
      (96000, 144, "Spark plug replacement", "8-8"),
      (32000, 48, "Engine air cleaner filter replacement", "8-8"),
      (8000, 12, "Climate control (cabin) air filter replacement", "8-8"),
      (8000, None, "Tire rotation", "8-8"),
      (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 36 months", "8-8"),
      (60000, 48, "Brake fluid replacement", "8-10"),
  ]),

 dict(vid=9980, model="Venue", label="2026 QX  " + G16, psi_f=None, psi_r=None, lug=LUG,
  oil=OIL_SYN,
  fluids=dict(trans="Intelligent variable transmission: MICHANG CVTF SP-CVT1 or Hyundai genuine CVTF SP-CVT1 (use only "
                    "the specified genuine fluid).",
              brake=BRAKE, cool_type=COOL_PHOS, cool_cap=None, ps=EPS, diff=None),
  parts=PARTS,
  src="owner-manual-verified (per 2026 Hyundai Venue OM, " + (GLOBAL % 2026) + " = venue_2026_QX_global_OM.pdf, PDF "
      "title 'QX_ENG-HMA.indb', Copyright 2026 HYUNDAI Motor America, PDF created 2026-07-21, single available print (no "
      "US-portal copy exists for 2025 or 2026; this host's QX labels match the titled US-portal books for 2020 and "
      "2021); " + SELF_ID + "; this year's book lists the intelligent variable transmission only; schedule p.9-8 to "
      "9-10, grids read from upright page renders; not written: " + UNIT_IVT + " and the coolant quantity (the only "
      "figure printed, 6.32 US qt beside 5.78 L, does not convert); " + GATES + ")",
  msrc="Hyundai Owner's Manual (Venue 2026 QX, p.%s)",
  maint=[
      (8000, 12, "Engine oil & filter change", "9-8"),
      (96000, None, "Spark plug replacement", "9-8"),
      (32000, 48, "Engine air cleaner filter replacement", "9-8"),
      (16000, 24, "Cabin air filter replacement", "9-8"),
      (8000, 12, "Tire rotation", "9-8"),
      (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-8"),
      (60000, 48, "Brake fluid replacement", "9-10"),
  ]),
]

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
    assert f["diff"] is None, (vid, "front-wheel drive only: no differential entries")
    shipped = [o["visc"], o["type"], o["cap"], o["cap_wo"], o["spec"], f["trans"], f["brake"], f["cool_type"], f["cool_cap"],
               f["ps"], p["tire"], p["note"], row["lug"]["note"]] + [d for _, _, d, _ in row["maint"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
            assert not NO_CONVERT.search(s), (vid, "a quantity that does not convert is in a shipped column", s)
    assert row["src"] != BARE and row["src"].startswith(BARE + " (") and row["src"].endswith(")")
    for k in ("psi_f", "psi_r"):
        assert row[k] is None or isinstance(row[k], int), (vid, k)
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
_c.close()
for row in ROWS:
    show(row)

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_venue_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
try:
    nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
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
    f = c.execute("SELECT coolant_capacity, transmission_capacity, differential_fluids_json FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, tire_pressure_rear, battery_group, battery_notes, spark_plug_type FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT component, torque_ft_lbs, source FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), MIN(source) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and e == 0, vid
    assert f[0][1] is None and f[0][2] is None and p[0][3] is None and p[0][4] is None and p[0][5] is None, vid
    assert t[0][2].startswith(BARE + " (") and classify(t[0][2], "torque_specs", vid) == 1
    for tb in ("oil_change", "fluids", "parts", "maintenance", "torque_specs"):
        for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)):
            assert classify(s, tb, vid) == 1, (vid, tb, s[:60])
    print("  %d: oil=%s | cool=%s | tire=%s @%s/%s | lug=%s | maint=%d (%s)"
          % (vid, o[0][0], f[0][0], p[0][0], p[0][1], p[0][2], t[0][1], m[0], m[1][:44]))
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare_count(c))
db.close()
print("DONE - %d rows written." % len(ROWS))
