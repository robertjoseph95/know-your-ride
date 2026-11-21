"""Fuel-economy repair, part 10: the versions a row never stored (ruling (c), second step).

Ruling (c) (Robert, 2026-11-20, "Accept the rule"): a row keeps, labelled, every version EPA lists under its
nameplate that a buyer could get on that row -- other powertrains, performance versions, trims, body styles.
Part 9 (`_repair_fuel_economy_versions.py`, deployed as 845fdf16) added the own-name records the fill had held back.
This part adds the versions EPA lists under their own name that a row never stored (Robert, "Yes, dry run it"):
  ADD   hybrid and plug-in hybrid versions (`Camry Hybrid LE`, `F150 Pickup 4WD HEV`, `Escape FWD PHEV`), other
        alternative-fuel versions, performance versions (`X3 M`, `F150 RAPTOR 4WD`, `Durango SRT AWD`) and body
        styles (`A4 allroad quattro`). One line per distinct record (city, highway, combined, engine size,
        transmission, drive), the first in EPA's file where two share all six. Plug-in hybrids store their
        gasoline-mode figures, as every stored plug-in line does.
  COST  on every row that gains a line, every line with an EPA record takes EPA's current yearly cost (one price
        year per row, as in part 9).
  LABELS in the same transaction, _label_fuel_economy.py labels the new lines and flags them (versions are not the
        plain car, so they ship after the row's plain lines and the search card does not change).
Out, as already ruled: electric and fuel-cell records on a gasoline row (the Kona Electric ruling), records that run
on hydrogen, longer bodies, special-purpose versions (police, USPS, hearse, incomplete), the Hyundai N models and
another vehicle's records. Records whose figures a stored line holds in pre-revision form are left for item (e).

Source: EPA fueleconomy.gov complete file vehicles.csv.zip (U.S. government), last modified by EPA 2026-11-04,
SHA-256 pinned in _label_fuel_economy.py. The file is untrusted data: its path is an argument, it is read into
memory, it must hold exactly one member, and that member is only parsed as CSV.

    python -I _repair_fuel_economy_versions_fill.py <path to vehicles.csv.zip>              DRY RUN (writes nothing)
    python -I _repair_fuel_economy_versions_fill.py --write --sha <sha256 printed by the dry run>
"""
import collections
import datetime
import io
import json
import os
import shutil
import sqlite3
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "files")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _repair_fuel_economy_versions as V9      # noqa: E402  (part 9: EPA loading, apply, labels, rehearsal)

LF, epa_name_rules = V9.LF, V9.epa_name_rules
DB = V9.DB
PLAN_FILE = os.path.join(ROOT, "_repair_fuel_economy_versions_fill_plan_cache.json")      # gitignored (*_cache.json)
BARE_FROZEN = V9.BARE_FROZEN
VERSION_CLASSES = ("hybrid or alternative fuel", "performance version", "longer or different body")
LONGER_WORDS = {"l", "xl", "max", "ext", "ewb", "extended"}        # a longer body (ruled out 2026-11-15), not a body style
KINDS = ("hybrid version", "plug-in hybrid version", "alternative-fuel version", "performance version", "body style")
PlanError = V9.PlanError
say = V9.say
R = V9.R


OPS = [   # from the dry run's discovery (--print-ops) on 2026-11-20, read before pinning; the dry run requires equality
    R(24, 2020, 'Toyota', 'Prius', [41489], [], 0),
    R(942, 2020, 'Audi', 'A4', [42364], [], 0),
    R(949, 2020, 'Audi', 'Q7', [42558], [], 2),
    R(1523, 2021, 'Toyota', 'Prius', [42814], [], 0),
    R(2046, 2021, 'Volkswagen', 'Jetta', [43246, 43247], [], 2),
    R(2440, 2021, 'Audi', 'Q7', [43028], [], 2),
    R(3031, 2022, 'Toyota', 'Corolla', [44073], [], 0),
    R(3032, 2022, 'Toyota', 'Prius', [44362], [], 0),
    R(3691, 2022, 'Hyundai', 'Elantra', [44057], [], 5),
    R(4572, 2023, 'Toyota', 'Corolla', [45929, 45930, 46131, 46132], [], 3),
    R(4593, 2023, 'Toyota', 'Corolla Cross', [47519], [], 0),
    R(6785, 2024, 'Hyundai', 'Elantra', [47349], [], 4),
    R(7067, 2024, 'Audi', 'A4', [47105], [], 2),
    R(7073, 2024, 'Audi', 'Q7', [47175], [], 2),
    R(7734, 2025, 'Toyota', 'Corolla', [48490, 48492, 49139, 49140], [], 0),
    R(8360, 2025, 'Hyundai', 'Elantra', [48022], [], 4),
    R(8649, 2025, 'Audi', 'A4', [48048], [], 2),
    R(8655, 2025, 'Audi', 'Q7', [47806], [], 2),
    R(9373, 2026, 'Toyota', 'Corolla', [49804, 49806], [], 0),
    R(9395, 2026, 'Toyota', 'Corolla Cross', [49870], [], 0),
    R(9599, 2026, 'Chevrolet', 'Corvette', [50271], [], 5),
    R(9808, 2026, 'Mitsubishi', 'Outlander', [50310], [], 1),
    R(9972, 2026, 'Hyundai', 'Tucson', [51096], [], 5),
    R(9974, 2026, 'Hyundai', 'Elantra', [49816], [], 0),
    R(10274, 2026, 'Audi', 'Q7', [49561], [], 2),
    R(10303, 2026, 'Porsche', '911', [50440, 50441, 50442], [], 0),
    R(11081, 2004, 'Chevrolet', 'Silverado 1500', [19956, 20034], [], 14),
    R(11090, 2004, 'GMC', 'Sierra 1500', [19992, 20065], [], 14),
    R(11135, 2005, 'Chevrolet', 'Silverado 1500', [21082, 21150], [], 14),
    R(11202, 2006, 'Chevrolet', 'Silverado 1500', [22161, 22246], [], 14),
    R(11447, 2009, 'Chevrolet', 'Silverado 1500', [25578, 25586], [], 0),
    R(11510, 2009, 'Toyota', 'Highlander', [26289], [], 0),
    R(11742, 2012, 'Chevrolet', 'Silverado 1500', [31862], [], 0),
    R(12161, 2015, 'Toyota', 'Camry', [35736, 35737], [], 2),
    R(12202, 2016, 'Chevrolet', 'Silverado 1500', [37372], [], 0),
    R(12332, 2017, 'Chevrolet', 'Silverado 1500', [37649], [], 0),
    R(12360, 2017, 'Ford', 'F-150', [38275], [], 0),
    R(12370, 2017, 'GMC', 'Sierra 1500', [37655], [], 0),
    R(12386, 2017, 'Jeep', 'Grand Cherokee', [37862], [], 0),
    R(12424, 2017, 'Toyota', 'Camry', [37828, 37829], [], 2),
    R(12481, 2018, 'Dodge', 'Challenger', [39045, 39047], [], 0),
    R(12484, 2018, 'Dodge', 'Charger', [39059], [], 6),
    R(12487, 2018, 'Dodge', 'Durango', [39187], [], 0),
    R(12496, 2018, 'Ford', 'F-150', [39251], [], 0),
    R(12506, 2018, 'GMC', 'Sierra 1500', [38948], [], 0),
    R(12508, 2018, 'Honda', 'Accord', [39918], [], 0),
    R(12513, 2018, 'Honda', 'Civic', [39576], [], 0),
    R(12529, 2018, 'Jeep', 'Grand Cherokee', [39188, 39523], [], 0),
    R(12569, 2018, 'Toyota', 'Camry', [38936, 38937], [], 0),
    R(12595, 2019, 'Audi', 'A4', [41432], [], 0),
    R(12626, 2019, 'Dodge', 'Challenger', [40602, 40603], [], 6),
    R(12629, 2019, 'Dodge', 'Charger', [40619], [], 0),
    R(12632, 2019, 'Dodge', 'Durango', [40827], [], 0),
    R(12641, 2019, 'Ford', 'F-150', [41039], [], 0),
    R(12760, 2020, 'Dodge', 'Durango', [41971], [], 0),
    R(12762, 2020, 'Ford', 'Escape', [42253, 42258, 42743], [], 0),
    R(12764, 2020, 'Ford', 'Explorer', [41937, 41939], [], 0),
    R(12766, 2020, 'Ford', 'F-150', [42178], [], 0),
    R(12777, 2020, 'Honda', 'CR-V', [42502], [], 2),
    R(12787, 2020, 'Jeep', 'Grand Cherokee', [41972, 41973], [], 0),
    R(12805, 2020, 'Toyota', 'Highlander', [42477, 42478, 42479], [], 0),
    R(12824, 2021, 'Dodge', 'Challenger', [43439, 43440, 43444], [], 0),
    R(12826, 2021, 'Dodge', 'Charger', [43454], [], 0),
    R(12828, 2021, 'Dodge', 'Durango', [43399, 43660], [], 0),
    R(12830, 2021, 'Ford', 'Escape', [43644, 43649, 43912], [], 0),
    R(12832, 2021, 'Ford', 'Explorer', [43291, 43480], [], 0),
    R(12834, 2021, 'Ford', 'F-150', [43465, 43614, 44367, 44368, 44371, 44373], [], 0),
    R(12845, 2021, 'Honda', 'Accord', [43364, 43365], [], 0),
    R(12847, 2021, 'Honda', 'CR-V', [43476], [], 2),
    R(12857, 2021, 'Jeep', 'Grand Cherokee', [43400, 43661], [], 3),
    R(12865, 2021, 'RAM', '1500', [43416], [], 0),
    R(12870, 2021, 'Toyota', 'Camry', [43307, 43308], [], 0),
    R(12872, 2021, 'Toyota', 'Highlander', [43130, 43141, 43142], [], 0),
    R(12895, 2022, 'Dodge', 'Durango', [45098], [], 0),
    R(12897, 2022, 'Ford', 'Escape', [44811, 44813, 44931], [], 0),
    R(12899, 2022, 'Ford', 'Explorer', [44824, 44832, 44833, 44976], [], 0),
    R(12901, 2022, 'Ford', 'F-150', [44875, 44879, 44880, 44881, 44940, 44987], [], 0),
    R(12912, 2022, 'Honda', 'CR-V', [44435], [], 2),
    R(12922, 2022, 'Jeep', 'Grand Cherokee', [45148], [], 3),
    R(12931, 2022, 'RAM', '1500', [44403], [], 0),
    R(12935, 2022, 'Toyota', 'Camry', [44350, 44351], [], 0),
    R(12937, 2022, 'Toyota', 'Highlander', [44651, 44684, 44685], [], 0),
    R(12962, 2023, 'Ford', 'Escape', [46325, 46389, 47220], [], 0),
    R(12964, 2023, 'Ford', 'Explorer', [46403, 46404, 46418, 46419], [], 0),
    R(12966, 2023, 'Ford', 'F-150', [46166, 46176, 46181, 46182, 46183, 46184, 46185], [], 0),
    R(12977, 2023, 'Honda', 'CR-V', [46064, 46071], [], 2),
    R(12987, 2023, 'Jeep', 'Grand Cherokee', [46253], [], 3),
    R(12997, 2023, 'RAM', '1500', [46229], [], 0),
    R(13026, 2024, 'Dodge', 'Durango', [47426, 47427], [], 0),
    R(13032, 2024, 'Ford', 'F-150', [47612, 47615, 47617], [], 0),
    R(13049, 2024, 'Hyundai', 'Sonata', [47583], [], 3),
    R(13053, 2024, 'Jeep', 'Grand Cherokee', [47277], [], 2),
    R(13063, 2024, 'RAM', '1500', [46855], [], 0),
    R(13092, 2025, 'Dodge', 'Durango', [48289], [], 0),
    R(13094, 2025, 'Ford', 'Escape', [48601, 48609, 48663], [], 0),
    R(13098, 2025, 'Ford', 'F-150', [49144], [], 0),
    R(13115, 2025, 'Hyundai', 'Sonata', [48047], [], 4),
    R(13119, 2025, 'Jeep', 'Grand Cherokee', [48665], [], 2),
    R(13123, 2025, 'Jeep', 'Wrangler', [48664], [], 0),
    R(13128, 2025, 'RAM', '1500', [47946], [], 0),
    R(13160, 2026, 'Ford', 'Escape', [49763, 49851], [], 0),
    R(13164, 2026, 'Ford', 'F-150', [50097, 50101, 50104, 50447], [], 0),
    R(13181, 2026, 'Hyundai', 'Sonata', [49321, 49322], [], 4),
    R(13187, 2026, 'Jeep', 'Wrangler', [50264], [], 0),
    R(13190, 2026, 'RAM', '1500', [49419], [], 0),
    R(13197, 2026, 'Toyota', 'Highlander', [50180], [], 0),
    R(13201, 2026, 'Toyota', 'Tacoma', [50109], [], 10),
]
EXPECT = (107, 185, 0, 157)          # (rows, records added, lines removed, yearly costs changed)
assert len(OPS) == EXPECT[0] and sum(len(o["add"]) for o in OPS) == EXPECT[1] and sum(o["cost"] for o in OPS) == EXPECT[3]


# ---------------------------------------------------------------- the rule
def kind_of(r, cls):
    if cls == "performance version":
        return "performance version"
    if cls == "longer or different body":
        return "body style"
    return {"Hybrid": "hybrid version", "Plug-in Hybrid": "plug-in hybrid version"}.get(r["atv"], "alternative-fuel version")


def excluded(r, cls):
    """Why a version-class record stays out ('' when it is a candidate)."""
    if cls == "longer or different body":
        if {w.lower().strip("()") for w in epa_name_rules.words(r["name"])} & LONGER_WORDS:
            return "longer body"
    if r["atv"] in V9.NOT_GAS:
        return "electric or fuel cell"
    if "Hydrogen" in (r.get("fuel") or ""):
        return "hydrogen fuel"
    if None in V9.key_rec(r) or V9.CHASSIS.fullmatch(r["name"]):
        return "incomplete record"
    return ""


def assess_row(year, make, model, lines, recs, plates):
    """(adds, cost updates, cost left, revised twins, left out [(record, why)]) for one row."""
    cls = epa_name_rules.name_classes(year, make, model, recs, plates)[0] if recs else {}
    hits = [(ln, LF.match_line(ln, recs)) for ln in lines]
    unmatched = {(LF._fnum(ln["engine"]), ln["transmission"], ln["drive"]) for ln, hit in hits
                 if not hit and ln["fuel_type"] != "Electric"}
    stored_keys = {V9.key_line(ln) for ln in lines}
    adds, seen, revised, left_out = [], set(), [], []
    for r in recs:
        c = cls.get(r["name"], "unrelated")
        if c not in VERSION_CLASSES:
            continue
        why = excluded(r, c)
        k = V9.key_rec(r)
        if why:
            if why in ("electric or fuel cell", "hydrogen fuel") and k not in stored_keys:
                left_out.append((r, why))
            continue
        if k in stored_keys or k in seen:
            continue
        seen.add(k)
        if k[3:] in unmatched:
            revised.append(r)
            continue
        adds.append(r)
    updates, left = [], []
    if adds:
        for ln, hit in hits:
            kept = V9.fe_labels.kept_records(hit, cls) if hit else []
            cs = sorted({x["cost"] for x in kept if x["cost"] is not None})
            if len(cs) == 1 and ln["annual_fuel_cost"] != cs[0]:
                updates.append([ln["id"], ln["annual_fuel_cost"], cs[0]])
            elif len(cs) > 1 and ln["annual_fuel_cost"] not in cs:
                left.append([ln["id"], ln["annual_fuel_cost"], cs])
    return adds, updates, left, revised, left_out


def discover(cur, by_ym, plates):
    """The operations the rule gives for the whole fleet, the revised twins (item e) and the records left out by
    fuel (electric, fuel cell, hydrogen)."""
    lines = V9.stored_lines(cur)
    ops, revised, left_out = [], [], []
    for vid, year, make, model in cur.execute("SELECT id, year, make, model FROM vehicles ORDER BY id").fetchall():
        if vid not in lines:
            continue
        adds, updates, _left, rev, out = assess_row(year, make, model, lines[vid], by_ym.get((year, make.lower()), []), plates)
        revised += [(vid, r["id"]) for r in rev]
        left_out += [(vid, r["id"], why) for r, why in out]
        if adds:
            ops.append(R(vid, year, make, model, sorted(r["id"] for r in adds), [], len(updates)))
    return ops, revised, left_out


def plan_ops(cur, by_ym, plates, ops):
    """Detail for each operation, in part 9's plan shape; refuses operations that are not exactly the rule today."""
    want, _rev, _out = discover(cur, by_ym, plates)
    if ops != want:
        a, b = {o["id"]: o for o in ops}, {o["id"]: o for o in want}
        diff = sorted(i for i in set(a) | set(b) if a.get(i) != b.get(i))
        raise PlanError("the operations differ from the rule on %d row(s), e.g. ids %s" % (len(diff), diff[:8]))
    lines = V9.stored_lines(cur)
    plan = []
    for op in ops:
        vid, year, make, model = op["id"], op["year"], op["make"], op["model"]
        row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        if not row or tuple(row) != (year, make, model):
            raise PlanError("target %d is %r, not %d %s %s" % (vid, row and tuple(row), year, make, model))
        recs = by_ym.get((year, make.lower()), [])
        cls = epa_name_rules.name_classes(year, make, model, recs, plates)[0]
        adds, updates, left, rev, _out = assess_row(year, make, model, lines[vid], recs, plates)
        adds = sorted(adds, key=lambda x: x["id"])
        plan.append({"id": vid, "year": year, "make": make, "model": model, "current": V9.stored(cur, vid),
                     "insert": [V9.line_row(r) for r in adds], "sources": [[r["name"], r["id"], r["atv"]] for r in adds],
                     "kinds": [kind_of(r, cls[r["name"]]) for r in adds], "remove": [], "cost_updates": updates,
                     "cost_left": left, "revised_left": [[r["name"], r["id"]] for r in rev]})
    return plan


# ---------------------------------------------------------------- report
def write_report(path, plan, revised, left_out, rh, verified, sha, names, recname):
    out = []
    w = out.append
    rows, inn, _rm, nc = V9.totals(plan)
    w("# Fuel-economy versions never stored (ruling c, part 10): dry run, %s" % datetime.date.today().isoformat())
    w("")
    w("Dry run: nothing was written to the database. Local only; not staged. Plan sha256 `%s`." % sha)
    w("")
    w("| Rows | Records added | Yearly costs changed | Lines after | Vehicles that ship a change | Search cards that change |")
    w("|---|---|---|---|---|---|")
    w("| %d (%d verified) | %d | %d | %d | %d | %d |" % (rows, sum(p["id"] in verified for p in plan), inn, nc,
                                                       rh["lines_after"], rh["changed"], len(rh["cards"])))
    w("")
    kinds = collections.Counter(k for p in plan for k in p["kinds"])
    w("Added by kind: " + "; ".join("%s %d" % (k, kinds.get(k, 0)) for k in KINDS) + ".")
    w("")
    w("## Rows")
    w("")
    w("| Vehicle | Verified | Added (EPA name, id, kind) | Costs changed |")
    w("|---|---|---|---|")
    for p in plan:
        add = "; ".join("%s (%d, %s)" % (s[0], s[1], k) for s, k in zip(p["sources"], p["kinds"]))
        cst = "; ".join("fe#%d %s->%s" % (f, o, n) for f, o, n in p["cost_updates"])
        w("| %d %s %s (id %d) | %s | %s | %s |" % (p["year"], p["make"], p["model"], p["id"],
                                                "yes" if p["id"] in verified else "", add.replace("|", "/"), cst))
    w("")
    w("## Search cards that change")
    w("")
    w("; ".join("%s (id %d)" % (names.get(v, "?"), v) for v, _a, _b in rh["cards"]) or "None: every new line is a version and ships "
      "after the row's plain lines.")
    w("")
    w("## Left out")
    w("")
    by = collections.defaultdict(list)
    for vid, rid, why in left_out:
        by[why].append("%s: %s" % (names.get(vid, "?"), recname.get(rid, rid)))
    for why in sorted(by):
        w("- %s (%d records, the Kona Electric ruling / not a gasoline line): %s." % (why, len(by[why]), "; ".join(sorted(set(by[why])))))
    w("- Revised figures, item (e) (%d records): %s." % (len(revised), "; ".join("%s: %s" % (names.get(v, "?"), recname.get(i, i))
                                                                                 for v, i in revised) or "none"))
    w("- Longer bodies, special-purpose versions, the Hyundai N models and other vehicles' records stay out as already ruled.")
    left = [(p["id"], c) for p in plan for c in p["cost_left"]]
    w("- Lines whose EPA records carry two different costs, cost left as stored: " +
      ("; ".join("id %d fe#%d %s (EPA %s)" % (v, c[0], c[1], c[2]) for v, c in left) or "none") + ".")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")


# ---------------------------------------------------------------- dry run and write
def dry_run(zip_path, print_ops=False):
    say("FUEL-ECONOMY VERSIONS NEVER STORED (RULING C, PART 10) -- DRY RUN (nothing is written)  %s" %
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    by_ym = V9.load_epa(zip_path)
    say("EPA file: %d records, sha256 %s (pinned)" % (sum(len(v) for v in by_ym.values()), LF.ZIP_SHA256))
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        if V9.bare_count(cur) != BARE_FROZEN:
            raise PlanError("bare owner-manual rows are not %d" % BARE_FROZEN)
        plates = epa_name_rules.fleet_plates(cur)
        ops, revised, left_out = discover(cur, by_ym, plates)
        if print_ops:
            for o in ops:
                say("    R(%d, %d, %r, %r, %r, [], %d)," % (o["id"], o["year"], o["make"], o["model"], o["add"], o["cost"]))
            return
        plan = plan_ops(cur, by_ym, plates, OPS)
        verified = {r[0] for r in cur.execute("SELECT vehicle_id FROM oil_change WHERE source LIKE 'owner-manual-verified%' "
                                              "OR source LIKE 'service-manual-verified%'")}
        fleet = cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        n0 = cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        first_id = V9.next_line_id(cur)
        plates_sha = LF.plates_sha(plates)
        names = {vid: "%d %s %s" % (y, mk, md) for vid, y, mk, md in cur.execute("SELECT id, year, make, model FROM vehicles")}
    finally:
        con.close()
    if EXPECT is None or V9.totals(plan) != EXPECT:
        raise PlanError("totals %r, pinned %r" % (V9.totals(plan), EXPECT))
    mem = V9._mem_copy()
    try:
        first, new_ids, labels = V9.label_after(mem, plan, by_ym, plates)
        if discover(mem.cursor(), by_ym, plates)[0]:
            raise PlanError("a second run of the rule would still add lines")
    finally:
        mem.close()
    if first != first_id:
        raise PlanError("the in-memory copy numbers new lines from %d, the database from %d" % (first, first_id))
    rows, inn, _rm, nc = V9.totals(plan)
    kinds = collections.Counter(k for p in plan for k in p["kinds"])
    say("")
    say("SUMMARY")
    say("  rows %d (verified %d); records added %d; yearly costs changed %d" % (rows, sum(p["id"] in verified for p in plan), inn, nc))
    say("  added by kind: " + "; ".join("%s %d" % (k, kinds.get(k, 0)) for k in KINDS))
    say("  left out by fuel: %s; revised twins left for item (e): %d" % (
        dict(collections.Counter(w for _v, _i, w in left_out)), len(revised)))
    say("  label plan: %d lines (labels and plain flags on %d new lines)" % (len(labels), len(new_ids)))
    rh = V9.rehearse(plan, labels, new_ids, by_ym, plates)
    if rh is None:
        raise PlanError("rehearsal failed")
    if rh["lines_after"] != n0 + inn:
        raise PlanError("lines after %d, expected %d" % (rh["lines_after"], n0 + inn))
    saved = {"script": os.path.basename(__file__), "epa_file_sha256": LF.ZIP_SHA256, "plates_sha256": plates_sha,
             "fleet": fleet, "lines_before": n0, "first_new_id": first_id, "new_ids": new_ids, "ops": plan, "labels": labels}
    sha = V9.plan_sha(saved)
    recname = {r["id"]: r["name"] for recs in by_ym.values() for r in recs}
    report = os.path.join(ROOT, "_fe_versions_fill_dry_run_%s.md" % datetime.date.today().isoformat())
    write_report(report, plan, revised, left_out, rh, verified, sha, names, recname)
    with io.open(PLAN_FILE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dict(saved, sha256=sha), fh, sort_keys=True, indent=1)
    say("  report: %s" % report)
    say("")
    say("plan saved: %s" % PLAN_FILE)
    say("plan sha256: %s" % sha)
    say("to write exactly this plan (only on Robert's go):  python -I %s --write --sha %s" % (os.path.basename(__file__), sha))


def write(want):
    with io.open(PLAN_FILE, encoding="utf-8") as fh:
        saved = json.load(fh)
    body = {k: v for k, v in saved.items() if k != "sha256"}
    if V9.plan_sha(body) != want or saved.get("sha256") != want or saved.get("epa_file_sha256") != LF.ZIP_SHA256:
        sys.exit("plan file hash does not match --sha %s: run the dry run again and get a fresh go" % want)
    plan, labels, new_ids = saved["ops"], saved["labels"], saved["new_ids"]
    if [(p["id"], p["year"]) for p in plan] != [(o["id"], o["year"]) for o in OPS]:
        sys.exit("the saved plan does not match this script's operations")
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        bare, fleet, n0 = V9.bare_count(cur), cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0], \
            cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        plates_now = LF.plates_sha(epa_name_rules.fleet_plates(cur))
        first_now = V9.next_line_id(cur)
    finally:
        con.close()
    if bare != BARE_FROZEN or fleet != saved["fleet"] or n0 != saved["lines_before"]:
        sys.exit("bare rows %d / fleet %d / lines %d differ from the dry run" % (bare, fleet, n0))
    if plates_now != saved["plates_sha256"] or first_now != saved["first_new_id"]:
        sys.exit("the fleet's nameplates or the next line id changed since the dry run: run it again and get a fresh go")
    bak = "%s.bak_fe_versions_fill_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    rows, inn, _rm, nc = V9.totals(plan)
    con = sqlite3.connect(DB, isolation_level=None)          # explicit transaction
    cur = con.cursor()
    cur.execute("BEGIN IMMEDIATE")
    try:
        got_ids = V9.apply_ops(cur, plan)
        if got_ids != new_ids:
            raise RuntimeError("new lines got ids %s..., the dry run planned %s..." % (got_ids[:3], new_ids[:3]))
        LF.ensure_columns(cur)
        LF.apply(cur, labels)
        if cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0] != n0 + inn or \
                cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] != fleet or V9.bare_count(cur) != BARE_FROZEN:
            raise RuntimeError("line count, fleet count or bare rows are off")
        open_lines = cur.execute("SELECT COUNT(*) FROM fuel_economy WHERE epa_ids IS NULL OR epa_plain IS NULL").fetchone()[0]
        if open_lines:
            raise RuntimeError("%d lines are unassessed after the write" % open_lines)
        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        con.close()
        raise
    con.close()
    say("WRITTEN: %d rows (%d lines added, %d yearly costs changed); %d lines labelled or flagged; fuel-economy lines "
        "%d -> %d; fleet %d; bare rows %d" % (rows, inn, nc, len(labels), n0, n0 + inn, fleet, BARE_FROZEN))


if __name__ == "__main__":
    if "--write" in sys.argv:
        i = sys.argv.index("--sha") if "--sha" in sys.argv else -1
        if i < 0 or i + 1 >= len(sys.argv):
            sys.exit("--write needs --sha <the sha256 a dry run printed>")
        write(sys.argv[i + 1])
    else:
        args = [a for a in sys.argv[1:] if a != "--print-ops"]
        if len(args) != 1:
            sys.exit("usage: python -I %s <path to vehicles.csv.zip> [--print-ops]" % os.path.basename(__file__))
        try:
            dry_run(args[0], print_ops="--print-ops" in sys.argv)
        except (PlanError, LF.PlanError) as e:
            say("")
            say("STOPPED -- a check did not come back clean, so no plan was saved:")
            say("   ", e)
            sys.exit(2)
