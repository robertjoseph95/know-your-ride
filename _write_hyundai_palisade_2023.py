# Hyundai Palisade 2023 (LX2 facelift) - curated specs for the model-year row added by _add_hyundai_rows.py
# (missing-year step B). Id 38722. It held no curated rows.
# Source: Hyundai owner's manuals (manufacturer, free, citable), saved under _hyundai_manuals/palisade/ (gitignored);
#   reads 2026-11-14. Two prints of the 2023 book:
#     first print  US portal owners.hyundaiusa.com glovebox-manual/2023/.../2023-Palisade-Owners-Manual.pdf
#                  PDF title "2023 Palisade Owner's Manual", Copyright 2022, PDF created 2022-05-24, 661 pp
#     later print  ownersmanual.hyundai.com full_pdf LX2 2023 en_US
#                  Copyright 2023, PDF created 2023-04-04, 660 pp
#   The later print is a 2023 book, not the 2024 one: it predates the 2024 book (PDF created 2023-10-23, 630 pp) and
#   lacks wording only the 2024 book has ("two-wheeler" 25 times, "methods" 104 times; neither 2023 print uses them).
#   The two hosts typeset differently, so prints are compared on values and on word counts, never on page identity.
#   Identified by the Palisade facelift body on the exterior overview p.2-2 (page render), 3.8 GDI 3,778cc as the only
#   engine (p.2-8), wheelbase 114.17 in, overall length 196.65 in, and the HYUNDAI Motor America copyright.
# ** EDITION CONFLICT, ruling 2026-11-14 ("Go, as recommended"), reasons live HERE and in the source suffix only:
#    the two prints state the automatic transmission fluid differently - first print p.2-12 "ATF SP-IV", later print
#    p.2-13 "ATF SP4M-1". Under the standing ruling a value two prints contradict is not written and the agreed part
#    ships: the fluid TYPE is NULL, the QUANTITY both prints state (7.39 US qt / 7.0 L) goes in the capacity column.
#    Every other written value is the same in both prints.
# ** Not carried: inspect-only schedule rows (the later print changes several of them).
# ** Gates (null): spark-plug part number / gap (not published; interval only); 12V battery (p.9-29 is only a
#    capacity-label illustration); MDPS - no power-steering fluid.
# ** IC-02: every row carries a " (...)" citation suffix; the bare token stays frozen at 424 rows (checked BEFORE
#    commit). S1.12 / S1.11: no bookkeeping words in shipped columns; battery_notes NULL; diff JSON = [{location, fluid_type}].
#
# Usage:  python _write_hyundai_palisade_2023.py            -> DRY RUN: print the row, classify every source
#         python _write_hyundai_palisade_2023.py --write    -> backup DB, DELETE the 6 curated tables for the id, INSERT, verify
import sqlite3, json, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
DISPUTED = re.compile(r"SP-IV|SP4M|SP-4M", re.I)                              # edition conflict: never in a shipped column
TABLES = ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]
TARGET = (38722, 2023)

# Target-row guard: the id must be the vehicle the label says it is (see the 2026-11-14 audit).
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
VEHICLES = {r[0]: r[1:] for r in _c.execute("SELECT id, year, make, model FROM vehicles WHERE make='Hyundai' AND model='Palisade'")}
_c.close()
assert sorted(VEHICLES) == [676, 2169, 3697, 6790, 8365, 9979, 38722], ("the Palisade rows are not the seven expected", sorted(VEHICLES))
assert VEHICLES[TARGET[0]] == (TARGET[1], "Hyundai", "Palisade"), VEHICLES[TARGET[0]]

EPS = "Electric power steering (EPS / MDPS) - no serviceable power-steering fluid"
COOL_PHOS = "Mixture of antifreeze and water; phosphate-based ethylene glycol coolant for aluminum radiator"
BRAKE_LV = "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6"
GL5_85 = "Hypoid gear oil API GL-5 SAE 75W/85 (SK HCT-5 gear oil 75W/85 or equivalent)"
V38 = "3.8 GDI"
PORTAL = "owners.hyundaiusa.com glovebox-manual"
GLOBAL = "ownersmanual.hyundai.com full_pdf %s %s en_US"

def diff(*pairs):
    return json.dumps([{"location": loc, "fluid_type": fl} for loc, fl in pairs], ensure_ascii=False)

# ---------------------------------------------------------------------------------------------------------------
# Every value below was read from the cited page of the 2023 book (first print), and checked in the later print.
# ---------------------------------------------------------------------------------------------------------------
ROWS = [
 dict(vid=38722, label="2023 LX2 facelift  3.8 GDI", psi=35,
  lug=dict(ftlb=79.0, nm=107.0,
           note="79 to 94 lb-ft (107 to 127 N-m, 11 to 13 kgf-m), wheel lug nut tightening torque per owner manual (range)"),
  oil=dict(visc="5W-30", type="Full synthetic (required)", cap="6.86 qt / 6.5 L (" + V38 + ")", cap_wo=None,
           spec="ACEA A5 or above; API latest (or ILSAC latest) or ACEA A5/B5 full synthetic required; SAE 5W-30"),
  fluids=dict(trans=None, trans_cap="7.39 qt / 7.0 L", brake=BRAKE_LV, cool_type=COOL_PHOS,
              cool_cap="12.44 qt / 11.79 L (without trailer) / 12.65 qt / 11.98 L (with trailer)", ps=EPS,
              diff=diff(("Rear differential", GL5_85 + ", 0.73 qt / 0.7 L"),
                        ("Transfer case (AWD)", GL5_85 + ", 0.73 qt / 0.7 L"))),
  parts=dict(tire="245/60R18 or 245/50R20",
             note="18-in wheels: 245/60R18; 20-in wheels: 245/50R20; 35 psi front and rear at normal and maximum "
                  "load. Compact spare T155/90R18 at 60 psi. Fuel tank 18.75 gal / 71 L."),
  src="owner-manual-verified (per 2023 Hyundai Palisade OM, portal file 2023-Palisade-Owners-Manual.pdf = "
      "palisade_2023_portal_OM.pdf, " + PORTAL + ", PDF title '2023 Palisade Owner's Manual', Copyright 2022 HYUNDAI "
      "Motor America (first print, PDF created 2022-05-24), cross-checked against the later print "
      + (GLOBAL % ("LX2", "2023")) + " = palisade_2023_LX2_global_OM.pdf (Copyright 2023, PDF created 2023-04-04; a "
      "later print of the 2023 book: it predates the 2024 book of 2023-10-23 and lacks that book's new wording); LX2 "
      "facelift, self-ID p.2-8 3.8 GDI 3,778cc, wheelbase 114.17 in, overall length 196.65 in, Palisade body on the "
      "exterior overview p.2-2; capacities p.2-12, viscosity chart p.2-13 read from a page render, tires + wheel nut "
      "torque p.2-10; schedule p.9-8 to 9-10, grids read from upright page renders; the two prints agree on every "
      "written value; not written: the automatic transmission fluid specification, which the two prints state "
      "differently (first print p.2-12 ATF SP-IV, later print p.2-13 ATF SP4M-1; edition ruling 2026-11-14) - the "
      "quantity both prints state is written in the capacity column; the gear-oil line is printed 'HYPIO GEAR OIL' "
      "and is written as hypoid; the first print misprints the brake-fluid grade as 'DOT0-4LV', the later print reads "
      "'DOT-4LV'; gated to null: 12V battery group and CCA (p.9-29 shows only a capacity-label illustration, "
      "AGM80L-DIN, captioned 'the actual battery label in the vehicle may differ from the illustration'), spark-plug "
      "part number and gap (not published, interval only), battery notes)",
  msrc="Hyundai Owner's Manual (Palisade 2023 LX2 facelift, p.%s)",
  maint=[
      (8000, 12, "Engine oil & filter change", "9-8"),
      (96000, None, "Spark plug replacement", "9-8"),
      (24000, 36, "Engine air cleaner filter replacement", "9-8"),
      (16000, 24, "Cabin air filter replacement", "9-9"),
      (8000, 12, "Tire rotation", "9-8"),
      (120000, 120, "Engine coolant first replacement; thereafter every 24,000 mi / 24 months", "9-9"),
      (48000, 48, "Brake fluid replacement", "9-10"),
  ]),
]
assert [r["vid"] for r in ROWS] == [TARGET[0]], "this script writes the one 2023 Palisade row and nothing else"

# ---------------------------------------------------------------------------------------------------------------
def check(row):
    """Contract checks that mirror the build and the shipped-surfaces verifier. Raise on the first violation."""
    vid = row["vid"]
    want = (int(row["label"][:4]), "Hyundai", "Palisade")
    assert VEHICLES.get(vid) == want and want[0] == TARGET[1], (vid, "target row is not the labelled vehicle", VEHICLES.get(vid), want)
    assert ("per %d Hyundai Palisade OM" % want[0]) in row["src"] and ("Palisade %d " % want[0]) in row["msrc"], (vid, "source year")
    for table in ("oil_change", "fluids", "parts", "torque_specs"):
        assert classify(row["src"], table, vid) == 1, (vid, table)
    assert len(row["maint"]) == 7, (vid, "seven schedule lines")
    for mi, mo, desc, page in row["maint"]:
        assert page in ("9-8", "9-9", "9-10"), (vid, desc, page)
        assert classify(row["msrc"] % page, "maintenance", vid) == 1, (vid, desc)
        assert mi is None or (isinstance(mi, int) and mi > 0), (vid, desc)
        assert mo is None or (isinstance(mo, int) and mo > 0), (vid, desc)
        assert mi is not None or mo is not None, (vid, desc, "a row needs an interval")
    o, f, p = row["oil"], row["fluids"], row["parts"]
    assert f["trans"] is None and f["trans_cap"] == "7.39 qt / 7.0 L", (vid, "edition ruling: fluid type empty, agreed quantity written")
    shipped = [o["visc"], o["type"], o["cap"], o["cap_wo"], o["spec"], f["trans"], f["trans_cap"], f["brake"], f["cool_type"],
               f["cool_cap"], f["ps"], p["tire"], p["note"], row["lug"]["note"]] + [d for _, _, d, _ in row["maint"]]
    for e in json.loads(f["diff"]):
        assert set(e) == {"location", "fluid_type"}, (vid, e)
        shipped += [e["location"], e["fluid_type"]]
    for s in shipped:
        if s is not None:
            m = JARGON.search(s)
            assert not m, (vid, m.group(0), s)
            assert not DISPUTED.search(s), (vid, "the disputed transmission fluid type is in a shipped column", s)
    assert row["src"] != BARE and row["src"].startswith(BARE + " (") and row["src"].endswith(")")
    assert row["psi"] is None or isinstance(row["psi"], int)
    # unit sanity on every printed pair that ships, within print rounding: 1 L = 1.0567 US qt; 1 US gal = 3.7854 L
    pairs = 0
    for s in shipped:
        for q, l in re.findall(r"((?:[0-9.]+-)?[0-9.]+) qt / ((?:[0-9.]+-)?[0-9.]+) L", s or ""):
            qs, ls = q.split("-"), l.split("-")
            assert len(qs) == len(ls), (vid, "qt/L range shape", q, l)
            for a, b in zip(qs, ls):
                assert abs(float(a) - float(b) * 1.0567) <= 0.09, (vid, "qt/L mismatch", q, l, s)
                pairs += 1
        for g, l in re.findall(r"([0-9.]+) gal / ([0-9.]+) L", s or ""):
            assert abs(float(g) - float(l) / 3.7854) <= 0.03, (vid, "gal/L mismatch", g, l, s)
            pairs += 1
        assert not re.search(r"[0-9] (?:qt|gal)(?! /)", s or ""), (vid, "unpaired US unit", s)
    return pairs

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
              (vid, f["trans"], f["trans_cap"], f["brake"], f["cool_type"], f["cool_cap"], f["ps"], f["diff"], row["src"]))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,"
              "tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,"
              "wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,"
              "real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (vid, None, None, None, None, None, p["tire"], row["psi"], row["psi"], None, None, None, None, None,
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
    print("\n=== %d  Palisade %s" % (row["vid"], row["label"]))
    print("  oil   : %s | w/o filter: %s | %s | %s" % (o["cap"], o["cap_wo"], o["visc"], o["type"]))
    print("  spec  : %s" % o["spec"])
    print("  trans : type %s | capacity %s" % (f["trans"], f["trans_cap"]))
    print("  cool  : %s | %s" % (f["cool_cap"], f["cool_type"]))
    print("  brake : %s" % f["brake"])
    print("  steer : %s" % f["ps"])
    for e in json.loads(f["diff"]):
        print("  diff  : %s -> %s" % (e["location"], e["fluid_type"]))
    print("  tires : %s @ %s psi | %s" % (p["tire"], row["psi"], p["note"]))
    print("  plugs : None | gap None | battery None")
    print("  lug   : %s lb-ft / %s N-m | %s" % (row["lug"]["ftlb"], row["lug"]["nm"], row["lug"]["note"]))
    for mi, mo, desc, page in row["maint"]:
        print("  maint : %7s mi / %s mo  %s  [p.%s]" % (mi if mi else "--", mo if mo else "--", desc, page))
    print("  src   : %s" % row["src"])

# ---------------------------------------------------------------------------------------------------------------
npairs = sum(check(row) for row in ROWS)
print("contract checks PASS: %d vehicle, %d maintenance rows, %d printed unit pairs converted; every source classified "
      "verified with a suffix; the target id is the labelled vehicle"
      % (len(ROWS), sum(len(r["maint"]) for r in ROWS), npairs))
_c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
print("bare rows now: %d (freeze expects 424)" % bare_count(_c))
for row in ROWS:
    h = holds(_c, row["vid"])
    print("  id %d holds now: %s" % (row["vid"], h))
    for t, toks in h.items():
        assert BARE not in toks, (row["vid"], t, "a frozen bare row sits on the target id - stop")
_c.close()
for row in ROWS:
    show(row)

if not WRITE:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_palisade_2023_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("\nbackup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
try:
    nid = c.execute("SELECT COALESCE(MAX(id),0) FROM maintenance").fetchone()[0] + 1
    for row in ROWS:
        nid = write(c, nid, row)
        print("  wrote %d  Palisade %s" % (row["vid"], row["label"]))
    assert bare_count(c) == 424, ("freeze would break", bare_count(c))      # checked BEFORE commit
    db.commit()
except Exception:
    db.rollback()
    raise

print("\nVerify:")
for row in ROWS:
    vid = row["vid"]
    o = c.execute("SELECT capacity_with_filter, source FROM oil_change WHERE vehicle_id=?", (vid,)).fetchall()
    f = c.execute("SELECT coolant_capacity, transmission_fluid, transmission_capacity, differential_fluids_json FROM fluids WHERE vehicle_id=?", (vid,)).fetchall()
    p = c.execute("SELECT tire_size, tire_pressure_front, tire_pressure_rear, battery_group, battery_notes, spark_plug_type FROM parts WHERE vehicle_id=?", (vid,)).fetchall()
    t = c.execute("SELECT component, torque_ft_lbs, source FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchall()
    m = c.execute("SELECT COUNT(*), MIN(source) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()
    e = c.execute("SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
    assert len(o) == 1 and len(f) == 1 and len(p) == 1 and len(t) == 1 and m[0] == len(row["maint"]) and e == 0, vid
    assert f[0][1] is None and f[0][2] == "7.39 qt / 7.0 L" and len(json.loads(f[0][3])) == 2, vid
    assert p[0][3] is None and p[0][4] is None and p[0][5] is None, vid
    assert t[0][2].startswith(BARE + " (") and classify(t[0][2], "torque_specs", vid) == 1
    for tb in ("oil_change", "fluids", "parts", "maintenance", "torque_specs"):
        for (s,) in c.execute("SELECT source FROM %s WHERE vehicle_id=?" % tb, (vid,)):
            assert classify(s, tb, vid) == 1, (vid, tb, s[:60])
    print("  %d: oil=%s | cool=%s | trans type=%s cap=%s | tire=%s @%s/%s | lug=%s | maint=%d (%s)"
          % (vid, o[0][0], f[0][0][:24], f[0][1], f[0][2], p[0][0], p[0][1], p[0][2], t[0][1], m[0], m[1][:50]))
    g = [c.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id=?" % tb, (vid,)).fetchone()[0]
         for tb in ("fuel_economy", "recalls", "safety_ratings", "complaints")]
    print("  %d government rows (fuel economy, recalls, safety, complaints): %s" % (vid, g))
print("  bare 'owner-manual-verified' rows after write: %d (freeze expects 424)" % bare_count(c))
db.close()
print("DONE - %d row written." % len(ROWS))
