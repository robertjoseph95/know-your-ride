# Hyundai live-row containment - corrections from the 2026-11-14 audit of the 15 live Hyundai rows against the later
# manual prints (ownersmanual.hyundai.com full_pdf) and against their own cited books. Approved 2026-11-14
# ("Go, all of it"). Four corrections, nothing else:
#
#   A. WRONG VEHICLE  id 35202 is the model-year-2000 Sonata (EF generation). _write_hyundai_sonata.py addressed it as
#      "2005" and wrote the 2005 NF manual's values onto it. All curated rows for id 35202 are REMOVED; the vehicle
#      returns to unverified. The real 2005 row (id 11156) stays deferred: government data gives 2005 the EF engine
#      roster (2.4 / 2.7 V6), which the NF "2005" manual (2.4 Theta / 3.3 Lambda) does not match.
#   B. EDITION CONFLICT  Sonata 2021 (id 12853): the first print (p.2-11, Copyright 2020) gives the Smartstream G2.5 GDi
#      oil capacity as 5.49 qt / 5.2 L, the later print gives 6.13 qt / 5.8 L. Per the 2026-11-14 ruling a value the two
#      prints contradict is not written: the 2.5 figure is removed, the 1.6T figure (identical in both) stays.
#   C. NOT IN THE BOOK  Sonata 2024 (id 13049): tire size 205/65R16 is not in the 2024 manual (either print). Replaced
#      with the book's Tires And Wheels table p.2-13: 215/55R17, 235/45R18, 245/40R19, all 35 psi front and rear.
#   D. EXAMPLE LABEL  battery_group AGM70L on Elantra 2021 (id 2163), Elantra 2022 (id 3691) and Sonata 2024 (id 13049)
#      came from the "Battery Capacity Label" page, an illustration marked Example / "the actual battery label in the
#      vehicle may differ". Per the Tucson ruling (2026-11-13) that page is not a vehicle specification: set to NULL.
#
# Every changed row keeps its verified source token and gains an audit note in the citation suffix (never in a shipped
# column). No row carrying the frozen bare token is touched (the lug-torque rows of these vehicles are left alone).
#
# Usage:  python _fix_hyundai_audit_2026_11_14.py            -> DRY RUN: show every change, classify every new source
#         python _fix_hyundai_audit_2026_11_14.py --write    -> backup DB, apply, verify
import sqlite3, shutil, datetime, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "files"))
from source_registry import classify  # noqa: E402

DB = os.path.join(ROOT, "wrench_vehicles.db")
WRITE = "--write" in sys.argv
BARE = "owner-manual-verified"
JARGON = re.compile(r"\bgated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)   # mirrors _verify_shipped S1.12
CURATED = ["oil_change", "fluids", "parts", "maintenance", "torque_specs", "engine_specs"]
LABEL = "shows only an example capacity label AGM70L-DIN, the actual label in the vehicle may differ"

REMOVE = dict(vid=35202, vehicle=(2000, "Hyundai", "Sonata"), cites="per 2005 Hyundai Sonata OM",
              counts={"oil_change": 1, "fluids": 1, "parts": 1, "maintenance": 1, "torque_specs": 0, "engine_specs": 0})

UPDATES = [
 dict(vid=12853, vehicle=(2021, "Hyundai", "Sonata"), table="oil_change",
      cells=[("capacity_with_filter",
              "5.49 qt / 5.2 L (2.5L GDI Smartstream) / 5.07 qt / 4.8 L (1.6L T-GDI Smartstream)",
              "5.07 qt / 4.8 L (1.6L T-GDI Smartstream)")],
      note="Smartstream G2.5 GDi oil capacity gated to null - the first print p.2-11 gives 5.49 qt / 5.2 L, the later "
           "print (ownersmanual.hyundai.com full_pdf DN8 2021 en_US) gives 6.13 qt / 5.8 L, the two prints disagree; "
           "G1.6 T-GDi 5.07 qt / 4.8 L is identical in both"),
 dict(vid=13049, vehicle=(2024, "Hyundai", "Sonata"), table="parts",
      cells=[("tire_size", "205/65R16", "215/55R17, 235/45R18 or 245/40R19"),
             ("tire_pressure_front", None, 35), ("tire_pressure_rear", None, 35),
             ("battery_group", "AGM70L", None)],
      note="tire sizes and 35 psi corrected to the Tires And Wheels table p.2-13 (the earlier 205/65R16 is not in the "
           "2024 book, either print); battery group gated to null (p.9-33 " + LABEL + ")"),
 dict(vid=2163, vehicle=(2021, "Hyundai", "Elantra"), table="parts",
      cells=[("battery_group", "AGM70L", None)],
      note="battery group gated to null (the Battery Capacity Label page, later print p.9-29, " + LABEL + ")"),
 dict(vid=3691, vehicle=(2022, "Hyundai", "Elantra"), table="parts",
      cells=[("battery_group", "AGM70L", None)],
      note="battery group gated to null (the Battery Capacity Label page, later print p.9-30, " + LABEL + ")"),
]

def audited(src, note):
    assert src.startswith(BARE + " (") and src.endswith(")") and "2026-11-14 audit" not in src, src
    return src[:-1] + "; 2026-11-14 audit: " + note + ")"

def vehicle(c, vid):
    return c.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()

def plan(c):
    """Validate every precondition and return the list of statements to run. Nothing is written here."""
    stmts = []
    # A. removal
    assert vehicle(c, REMOVE["vid"]) == REMOVE["vehicle"], ("unexpected vehicle", vehicle(c, REMOVE["vid"]))
    src = c.execute("SELECT source FROM oil_change WHERE vehicle_id=?", (REMOVE["vid"],)).fetchone()[0]
    assert REMOVE["cites"] in src, "id 35202 no longer cites the 2005 manual - already corrected?"
    print("A. REMOVE all curated rows from id %d = %s %s %s (source cites: %s)" % ((REMOVE["vid"],) + REMOVE["vehicle"] + (REMOVE["cites"],)))
    for t in CURATED:
        rows = c.execute("SELECT source FROM %s WHERE vehicle_id=?" % t, (REMOVE["vid"],)).fetchall()
        assert len(rows) == REMOVE["counts"][t], (t, len(rows))
        assert all(r[0] != BARE for r in rows), ("frozen bare row would be deleted", t)
        print("     %-13s %d row(s)" % (t, len(rows)))
        if rows:
            stmts.append(("DELETE FROM %s WHERE vehicle_id=?" % t, (REMOVE["vid"],), len(rows)))
    # B-D. cell updates
    for u in UPDATES:
        assert vehicle(c, u["vid"]) == u["vehicle"], ("unexpected vehicle", u["vid"], vehicle(c, u["vid"]))
        cols = [col for col, _, _ in u["cells"]]
        row = c.execute("SELECT source, %s FROM %s WHERE vehicle_id=?" % (", ".join(cols), u["table"]), (u["vid"],)).fetchall()
        assert len(row) == 1, (u["vid"], u["table"], len(row))
        src, cur = row[0][0], row[0][1:]
        assert src != BARE, ("frozen bare row would be edited", u["vid"], u["table"])
        new_src = audited(src, u["note"])
        assert classify(new_src, u["table"], u["vid"]) == 1, ("new source not verified", u["vid"])
        print("\n%d  %s %s %s  [%s]" % ((u["vid"],) + u["vehicle"] + (u["table"],)))
        for (col, old, new), have in zip(u["cells"], cur):
            assert have == old, ("unexpected current value", u["vid"], col, have, old)
            assert not (isinstance(new, str) and JARGON.search(new)), (u["vid"], col, new)
            print("     %-22s %r  ->  %r" % (col, old, new))
        print("     source               ...%s" % new_src[len(src) - 1:])
        sets = ", ".join("%s=?" % col for col in cols) + ", source=?"
        stmts.append(("UPDATE %s SET %s WHERE vehicle_id=?" % (u["table"], sets),
                      tuple(new for _, _, new in u["cells"]) + (new_src, u["vid"]), 1))
    return stmts

def bare_count(c):
    return c.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                     "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) WHERE source=?", (BARE,)).fetchone()[0]

ro = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
stmts = plan(ro.cursor())
before = bare_count(ro.cursor())
ro.close()
print("\npreconditions PASS: %d statements planned; frozen bare rows now: %d" % (len(stmts), before))

if not WRITE:
    print("DRY RUN - nothing written. Re-run with --write to apply.")
    sys.exit(0)

bak = DB + ".bak_hyundai_audit_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, bak)
print("backup:", bak)
db = sqlite3.connect(DB)
c = db.cursor()
for sql, args, expect in stmts:
    c.execute(sql, args)
    assert c.rowcount == expect, (sql, c.rowcount, expect)
db.commit()

print("\nVerify:")
for t in CURATED:
    assert c.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id=?" % t, (REMOVE["vid"],)).fetchone()[0] == 0, t
print("  35202: no curated rows remain (2000 Sonata is unverified)")
for u in UPDATES:
    cols = [col for col, _, _ in u["cells"]]
    row = c.execute("SELECT source, %s FROM %s WHERE vehicle_id=?" % (", ".join(cols), u["table"]), (u["vid"],)).fetchone()
    assert list(row[1:]) == [new for _, _, new in u["cells"]], (u["vid"], row)
    assert classify(row[0], u["table"], u["vid"]) == 1 and "2026-11-14 audit" in row[0]
    print("  %d %s: %s" % (u["vid"], u["table"], dict(zip(cols, row[1:]))))
after = bare_count(c)
print("  frozen bare rows after: %d (before %d)" % (after, before))
assert after == before == 424, (before, after)
db.close()
print("DONE - 1 vehicle returned to unverified, 4 rows corrected.")
