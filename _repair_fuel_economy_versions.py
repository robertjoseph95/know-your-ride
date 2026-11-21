"""Fuel-economy repair, part 9: the versions of a vehicle (ruling (c)).

Ruling (Robert, 2026-11-20, "Accept the rule" to the recon `_fe_kinds_recon_2026-11-20.md`, then "Approve approach"):
a row keeps, labelled, every version EPA lists under its nameplate that a buyer could get on that row (other
powertrains, performance versions, trims, body styles). What is not a finished vehicle (chassis cab) stays out, as do
the kinds already ruled out (another vehicle, longer bodies, special-purpose).

What this repair does, from EPA's complete file only:
  ADD     the own-name records the every-own-record fill (part 8) held back: hybrids and plug-in hybrids EPA files
          under the plain name, performance-leaning trims (BMW M35i / M40i / M50i / M60i, Mustang Bullitt / HO /
          Performance Package / Dark Horse SC, Camry / Tacoma TRD, RAM 1500 HO, 911 Turbo S), the SRT-8 records in
          EPA's shared `300/SRT-8` name, and the four-door Wrangler (`Wrangler 4dr`, `Wrangler Unlimited`); plus the
          F-150 trim `F150 Pickup 4WD XL/XLT`, which the naming rules had read as a longer body (fixed in
          files/epa_name_rules.py the same day). One line per distinct record (city, highway, combined, engine size,
          transmission, drive), the first in EPA's file where two share all six.
  REMOVE  the stored lines whose only EPA records are chassis-cab records (`... Cab Chassis ...`).
  COST    on every row this repair touches (it gains or loses a line, or it shows two fuel-price years), every line
          with an EPA record takes EPA's current yearly cost, so the row shows one price year. Other rows keep their
          cost: their own lines are just as old, and the fleet-wide refresh is item (d).
  LABELS  in the same transaction, _label_fuel_economy.py's own code labels the new lines and stores, for every line,
          fuel_economy.epa_plain; the build then ships a row's plain lines first, so the search card shows the plain car.
NOT done (each reported):
  - records that EPA lists with figures a stored line holds in their pre-revision form (2026 rows): item (e);
  - versions under their own EPA name that were never stored (e.g. Camry Hybrid LE on a Camry row without it): a
    later fill, not this ruling.

Source: EPA fueleconomy.gov complete file vehicles.csv.zip (U.S. government), last modified by EPA 2026-11-04,
SHA-256 pinned in _label_fuel_economy.py (the same file as the labels). The file is untrusted data: its path is an
argument, it is read into memory, it must hold exactly one member, and that member is only parsed as CSV.

    python -I _repair_fuel_economy_versions.py <path to vehicles.csv.zip>
        DRY RUN. Checks the file's hash, derives the operations from the rule and requires them to equal OPS below,
        plans every row, labels the result on an in-memory copy, rehearses the real build before and after, writes
        a report, saves the plan and prints its sha256. Writes nothing to wrench_vehicles.db.

    python -I _repair_fuel_economy_versions.py --write --sha <sha256 printed by the dry run>
        Backs up the database, then applies EXACTLY the saved plan in ONE transaction (lines, costs, label columns,
        triggers, labels and plain flags commit together or not at all).
"""
import collections
import contextlib
import csv
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(ROOT, "files")
for _p in (ROOT, FILES_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import epa_name_rules                     # noqa: E402  (files/)
import fe_labels                          # noqa: E402  (files/)
import _label_fuel_economy as LF          # noqa: E402  (the label script: matching, label plan, build rehearsal)

DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_repair_fuel_economy_versions_plan_cache.json")      # gitignored (*_cache.json)
BARE_FROZEN = 424
COLS = ("city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, transmission, drive, range_miles, mpge, "
        "fuel_type, range_ev, city_ev, hwy_ev, comb_ev")
CITY, HWY, COMB, COST, ENG, TRANS, DRIVE, RANGE, MPGE, FTYPE = range(10)
HYB = ("Hybrid", "Plug-in Hybrid")
NOT_GAS = ("EV", "FCV")
CHASSIS = re.compile(r".*Cab Chassis.*")
ADD_KINDS = ("hybrid under the plain name", "performance-leaning trim", "SRT-8 under the shared 300 / SRT-8 name",
             "four-door Wrangler", "F-150 XL / XLT trim")


class PlanError(Exception):
    pass


def say(*a):
    print(*a)
    sys.stdout.flush()


def R(vid, year, make, model, add, remove, cost):
    """add = EPA record ids to add; remove = stored line ids that come out; cost = stored lines whose yearly cost changes."""
    return dict(id=vid, year=year, make=make, model=model, add=add, remove=remove, cost=cost)


OPS = [   # from the dry run's discovery (--print-ops) on 2026-11-20, read before pinning; the dry run requires equality
    R(24, 2020, 'Toyota', 'Prius', [41916], [], 2),
    R(88, 2020, 'BMW', 'X3', [41758], [], 5),
    R(164, 2020, 'MINI', 'Countryman', [42371], [], 0),
    R(1523, 2021, 'Toyota', 'Prius', [42809], [], 2),
    R(1583, 2021, 'BMW', 'X5', [42863], [], 5),
    R(1584, 2021, 'BMW', 'X3', [42900], [], 5),
    R(1626, 2021, 'BMW', 'X7', [42871], [], 1),
    R(1663, 2021, 'MINI', 'Countryman', [43143], [], 0),
    R(3032, 2022, 'Toyota', 'Prius', [44080], [], 2),
    R(3167, 2022, 'MINI', 'Countryman', [43965], [], 0),
    R(3221, 2022, 'Ford', 'Bronco', [], [], 1),
    R(4639, 2023, 'BMW', 'X5', [45573], [], 5),
    R(4640, 2023, 'BMW', 'X3', [45545], [], 4),
    R(4762, 2023, 'Ford', 'Bronco', [], [], 1),
    R(6219, 2024, 'BMW', 'X5', [46546], [], 3),
    R(6220, 2024, 'BMW', 'X3', [46872], [], 4),
    R(6230, 2024, 'BMW', 'X1', [46871], [], 1),
    R(6231, 2024, 'BMW', '530i', [47067], [], 1),
    R(6434, 2024, 'Cadillac', 'Escalade', [], [], 1),
    R(7807, 2025, 'BMW', 'X5', [47744], [], 4),
    R(7808, 2025, 'BMW', 'X3', [48078], [], 1),
    R(7818, 2025, 'BMW', 'X1', [48262], [], 1),
    R(7819, 2025, 'BMW', '530i', [48176], [], 1),
    R(7820, 2025, 'BMW', '330i', [48164], [], 1),
    R(7934, 2025, 'Ford', 'Bronco', [], [], 1),
    R(8019, 2025, 'Cadillac', 'Escalade', [], [], 1),
    R(9367, 2026, 'Maserati', 'Grecale', [51097], [], 2),
    R(9373, 2026, 'Toyota', 'Corolla', [], [], 2),
    R(9374, 2026, 'Toyota', 'Prius', [49298], [], 3),
    R(9447, 2026, 'BMW', 'X5', [49565], [], 4),
    R(9448, 2026, 'BMW', 'X3', [49477], [], 1),
    R(9457, 2026, 'BMW', 'X1', [49473], [], 1),
    R(9458, 2026, 'BMW', '530i', [49273], [], 1),
    R(9459, 2026, 'BMW', '330i', [49234], [], 1),
    R(9467, 2026, 'BMW', '430i', [49202, 49204, 49241], [], 3),
    R(9470, 2026, 'BMW', 'X7', [49571], [], 1),
    R(9568, 2026, 'Ford', 'Bronco', [], [], 1),
    R(9781, 2026, 'Chrysler', 'Pacifica', [], [], 1),
    R(9974, 2026, 'Hyundai', 'Elantra', [], [], 1),
    R(10303, 2026, 'Porsche', '911', [50277], [], 14),
    R(11087, 2004, 'Ford', 'F-150', [], [], 4),
    R(11138, 2005, 'Chrysler', '300', [21601], [], 0),
    R(11198, 2006, 'Chevrolet', 'Colorado', [], [2466, 2477], 14),
    R(11205, 2006, 'Chrysler', '300', [22047], [], 0),
    R(11280, 2007, 'Chrysler', '300', [23607], [], 0),
    R(11362, 2008, 'Chrysler', '300', [25110], [], 0),
    R(11452, 2009, 'Chrysler', '300', [25992], [], 0),
    R(11546, 2010, 'Chrysler', '300', [31321], [], 0),
    R(11742, 2012, 'Chevrolet', 'Silverado 1500', [], [], 1),
    R(11812, 2012, 'Toyota', 'Camry', [], [], 2),
    R(12202, 2016, 'Chevrolet', 'Silverado 1500', [], [], 1),
    R(12291, 2016, 'Toyota', 'Camry', [], [], 2),
    R(12332, 2017, 'Chevrolet', 'Silverado 1500', [], [], 1),
    R(12370, 2017, 'GMC', 'Sierra 1500', [], [], 1),
    R(12452, 2018, 'BMW', 'X3', [39683], [], 1),
    R(12467, 2018, 'Chevrolet', 'Silverado 1500', [], [], 2),
    R(12496, 2018, 'Ford', 'F-150', [40223], [], 0),
    R(12506, 2018, 'GMC', 'Sierra 1500', [], [], 1),
    R(12513, 2018, 'Honda', 'Civic', [], [], 2),
    R(12531, 2018, 'Jeep', 'Wrangler', [40092, 40093], [], 8),
    R(12598, 2019, 'BMW', 'X3', [40513], [], 2),
    R(12641, 2019, 'Ford', 'F-150', [41112], [], 0),
    R(12723, 2019, 'Toyota', 'Camry', [], [], 2),
    R(12766, 2020, 'Ford', 'F-150', [42519], [], 0),
    R(12769, 2020, 'Ford', 'Mustang', [41995], [], 0),
    R(12790, 2020, 'Jeep', 'Wrangler', [41678, 41679, 41767, 42405], [], 0),
    R(12797, 2020, 'RAM', '1500', [41651, 41654, 41655], [], 0),
    R(12802, 2020, 'Toyota', 'Camry', [42018], [], 2),
    R(12839, 2021, 'Ford', 'Mustang', [43668, 43670, 43671, 43674], [], 0),
    R(12860, 2021, 'Jeep', 'Wrangler', [42906, 42908, 42911, 42965, 42966, 43682, 44092], [], 1),
    R(12865, 2021, 'RAM', '1500', [43006, 43014, 43415], [], 0),
    R(12876, 2021, 'Toyota', 'Tacoma', [43086], [], 0),
    R(12904, 2022, 'Ford', 'Mustang', [45046, 45048, 45053, 45057], [], 0),
    R(12910, 2022, 'Honda', 'Accord', [], [], 2),
    R(12925, 2022, 'Jeep', 'Wrangler', [44905, 44906, 44908, 44912, 44914, 44915], [], 1),
    R(12931, 2022, 'RAM', '1500', [44395, 44401], [], 0),
    R(12990, 2023, 'Jeep', 'Wrangler', [45689, 45690, 45692, 45695, 45696, 45697], [], 1),
    R(12997, 2023, 'RAM', '1500', [46224, 46227, 46369], [], 0),
    R(13001, 2023, 'Toyota', 'Camry', [45720], [], 2),
    R(13043, 2024, 'Honda', 'CR-V', [46694, 46716], [], 2),
    R(13057, 2024, 'Jeep', 'Wrangler', [46727, 46885, 46887, 47378], [], 1),
    R(13063, 2024, 'RAM', '1500', [46821, 46853, 47369], [], 2),
    R(13067, 2024, 'Toyota', 'Camry', [47086], [], 2),
    R(13098, 2025, 'Ford', 'F-150', [], [], 2),
    R(13107, 2025, 'Honda', 'Accord', [], [], 2),
    R(13109, 2025, 'Honda', 'CR-V', [47950, 47957], [], 2),
    R(13123, 2025, 'Jeep', 'Wrangler', [48532, 48919], [], 0),
    R(13128, 2025, 'RAM', '1500', [47727], [], 0),
    R(13135, 2025, 'Toyota', 'Highlander', [], [], 2),
    R(13167, 2026, 'Ford', 'Mustang', [51093, 51094], [], 0),
    R(13175, 2026, 'Honda', 'CR-V', [49353, 49488, 49489], [], 2),
    R(13187, 2026, 'Jeep', 'Wrangler', [49854, 50127], [], 0),
    R(13190, 2026, 'RAM', '1500', [49418, 49421, 50096, 50448], [], 0),
    R(13197, 2026, 'Toyota', 'Highlander', [], [], 2),
    R(13199, 2026, 'Toyota', 'RAV4', [50285], [], 0),
    R(17646, 2004, 'Porsche', '911', [], [], 2),
    R(18624, 2005, 'Porsche', '911', [], [], 2),
    R(20655, 2007, 'Porsche', '911', [], [], 2),
    R(21742, 2008, 'Porsche', '911', [], [], 3),
    R(32584, 2018, 'MINI', 'Countryman', [38863], [], 0),
    R(33916, 2019, 'MINI', 'Countryman', [40157], [], 0),
    R(38591, 2019, 'Chevrolet', 'Silverado 1500', [], [7524, 7525, 7536, 7537], 0),
    R(38608, 2020, 'RAM', '1500', [], [], 2),
    R(38609, 2021, 'RAM', '1500', [], [], 4),
    R(38610, 2022, 'RAM', '1500', [], [], 4),
    R(38612, 2017, 'Chevrolet', 'Camaro', [], [], 1),
    R(38613, 2018, 'Chevrolet', 'Camaro', [], [], 1),
    R(38614, 2019, 'Chevrolet', 'Camaro', [], [], 2),
    R(38615, 2020, 'Chevrolet', 'Camaro', [], [], 2),
    R(38616, 2021, 'Chevrolet', 'Camaro', [], [], 2),
    R(38643, 2019, 'Mazda', 'MX-5 Miata', [], [], 1),
    R(38694, 2023, 'Mercedes-Benz', 'GLE 350', [], [], 1),
    R(38699, 2022, 'Cadillac', 'XT4', [], [], 1),
    R(38700, 2023, 'Cadillac', 'XT4', [], [], 1),
    R(38703, 2022, 'Acura', 'TLX', [], [], 2),
    R(38704, 2023, 'Acura', 'TLX', [], [], 2),
    R(38707, 2007, 'Mazda', 'Mazda3', [], [], 1),
]
EXPECT = (117, 121, 6, 197)          # (rows, records added, lines removed, yearly costs changed)
assert len(OPS) == EXPECT[0] and sum(len(o["add"]) for o in OPS) == EXPECT[1]
assert sum(len(o["remove"]) for o in OPS) == EXPECT[2] and sum(o["cost"] for o in OPS) == EXPECT[3]


# ---------------------------------------------------------------- EPA's file
def load_epa(path):
    """(year, make.lower()) -> EPA records, as _label_fuel_economy.load_epa returns them (which checks the pinned hash),
    plus each record's current yearly cost, fuel type and engine size as EPA writes it."""
    by_ym = LF.load_epa(path)
    with open(path, "rb") as fh:
        z = zipfile.ZipFile(io.BytesIO(fh.read(LF.ZIP_MAX + 1)))
    extra = {}
    for r in csv.DictReader(io.StringIO(z.read("vehicles.csv").decode("utf-8", "replace"))):
        extra[int(r["id"])] = (LF._num(r["fuelCost08"]), r["fuelType"].strip() or None, r["displ"].strip() or None)
    for recs in by_ym.values():
        for rec in recs:
            rec["cost"], rec["fuel"], rec["displ_text"] = extra[rec["id"]]
    return by_ym


# ---------------------------------------------------------------- the rule
def key_rec(r):
    return (r["city"], r["hwy"], r["comb"], r["displ"], r["trans"], r["drive"])


def key_line(ln):
    return (ln["city_mpg"], ln["highway_mpg"], ln["combined_mpg"], LF._fnum(ln["engine"]), ln["transmission"], ln["drive"])


def add_kind(make, model, r):
    """Which held kind an own-name record is (None for any other record, which this repair never adds)."""
    if (make, model) == ("Jeep", "Wrangler") and re.search(r"4dr|Unlimited", r["name"]):
        return "four-door Wrangler"
    if (make, model) == ("Chrysler", "300") and re.fullmatch(r"300C?/SRT-8", r["name"]):
        return "SRT-8 under the shared 300 / SRT-8 name"
    if fe_labels.version_name(make, model, r) and not CHASSIS.fullmatch(r["name"]):
        return "performance-leaning trim"
    if (make, model) == ("Ford", "F-150") and re.search(r"(?<![A-Za-z])XL(?![A-Za-z])", r["name"]):
        return "F-150 XL / XLT trim"
    if r["atv"] in HYB:
        return "hybrid under the plain name"
    return None


def _candidate(make, model, r, cls):
    """A record the rule would put on the row if no stored line holds it."""
    if r["atv"] in NOT_GAS or None in key_rec(r) or CHASSIS.fullmatch(r["name"]):
        return False
    if cls == "own":
        return True
    return cls == "longer or different body" and (make, model) == ("Jeep", "Wrangler") and "Unlimited" in r["name"]


def stored_lines(cur):
    cols = ["id", "vehicle_id", "annual_fuel_cost"] + list(LF.LINE_COLS)
    out = collections.defaultdict(list)
    for row in cur.execute("SELECT %s FROM fuel_economy ORDER BY id" % ", ".join(cols)):
        out[row[1]].append(dict(zip(cols, row)))
    return out


def assess_row(year, make, model, lines, recs, plates):
    """The rule applied to one row: (adds, removes, cost updates, cost left, revised twins, touched)."""
    cls = epa_name_rules.name_classes(year, make, model, recs, plates)[0] if recs else {}
    assessed = []
    for ln in lines:
        hit = LF.match_line(ln, recs)
        assessed.append((ln, fe_labels.kept_records(hit, cls) if hit else []))
    remove = [ln["id"] for ln, kept in assessed if kept and all(CHASSIS.fullmatch(r["name"]) for r in kept)]
    unmatched = {(LF._fnum(ln["engine"]), ln["transmission"], ln["drive"]) for ln, kept in assessed
                 if not kept and ln["fuel_type"] != "Electric"}
    stored_keys = {key_line(ln) for ln, _k in assessed}
    adds, seen, revised = [], set(), []
    for r in recs:
        if not _candidate(make, model, r, cls.get(r["name"], "unrelated")):
            continue
        k = key_rec(r)
        if k in stored_keys or k in seen:
            continue
        seen.add(k)
        if k[3:] in unmatched:                  # a stored line holds this record's figures before EPA revised them
            revised.append(r)
            continue
        adds.append(r)
    kept_lines = [(ln, kept) for ln, kept in assessed if kept and ln["id"] not in remove]
    costs = [(ln, sorted({r["cost"] for r in kept if r["cost"] is not None})) for ln, kept in kept_lines]
    era = {ln["annual_fuel_cost"] in cs for ln, cs in costs if cs}
    touched = bool(adds or remove) or era == {True, False}
    updates = [[ln["id"], ln["annual_fuel_cost"], cs[0]] for ln, cs in costs if len(cs) == 1 and ln["annual_fuel_cost"] != cs[0]]
    left = [[ln["id"], ln["annual_fuel_cost"], cs] for ln, cs in costs if len(cs) > 1 and ln["annual_fuel_cost"] not in cs]
    if not touched:
        updates, left = [], []
    return adds, remove, updates, left, revised, touched


def discover(cur, by_ym, plates):
    """The operations the rule gives for the whole fleet, and the records left as revised twins (item e)."""
    lines = stored_lines(cur)
    ops, revised = [], []
    for vid, year, make, model in cur.execute("SELECT id, year, make, model FROM vehicles ORDER BY id").fetchall():
        if vid not in lines:
            continue
        adds, remove, updates, _left, rev, touched = assess_row(year, make, model, lines[vid],
                                                               by_ym.get((year, make.lower()), []), plates)
        revised += [(vid, r["id"]) for r in rev]
        if touched and (adds or remove or updates):
            ops.append(R(vid, year, make, model, sorted(r["id"] for r in adds), remove, len(updates)))
    return ops, revised


# ---------------------------------------------------------------- plan and apply
def stored(cur, vid):
    return [list(r) for r in cur.execute("SELECT id, %s FROM fuel_economy WHERE vehicle_id=? ORDER BY id" % COLS, (vid,))]


def line_row(rec):
    return [rec["city"], rec["hwy"], rec["comb"], rec["cost"], rec["displ_text"], rec["trans"], rec["drive"], None, None,
            rec["fuel"], None, None, None, None]


def after_rows(p):
    new_cost = {fid: new for fid, _old, new in p["cost_updates"]}
    gone = {r[0] for r in p["remove"]}
    rows = []
    for r in p["current"]:
        if r[0] in gone:
            continue
        d = list(r[1:])
        if r[0] in new_cost:
            d[COST] = new_cost[r[0]]
        rows.append(d)
    return rows + [list(x) for x in p["insert"]]


def plan_ops(cur, by_ym, plates, ops):
    """Detail for each operation; refuses operations that are not exactly what the rule gives today."""
    want, _rev = discover(cur, by_ym, plates)
    if ops != want:
        a, b = {o["id"]: o for o in ops}, {o["id"]: o for o in want}
        diff = sorted(i for i in set(a) | set(b) if a.get(i) != b.get(i))
        raise PlanError("the operations differ from the rule on %d row(s), e.g. ids %s" % (len(diff), diff[:8]))
    lines = stored_lines(cur)
    plan = []
    for op in ops:
        vid, year, make, model = op["id"], op["year"], op["make"], op["model"]
        row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        if not row or tuple(row) != (year, make, model):
            raise PlanError("target %d is %r, not %d %s %s" % (vid, row and tuple(row), year, make, model))
        recs = by_ym.get((year, make.lower()), [])
        adds, remove, updates, left, rev, _t = assess_row(year, make, model, lines[vid], recs, plates)
        kinds = [add_kind(make, model, r) for r in adds]
        if None in kinds:
            r = adds[kinds.index(None)]
            raise PlanError("id %d: own EPA record %d (%s) is of no held kind -- needs a look" % (vid, r["id"], r["name"]))
        current = stored(cur, vid)
        plan.append({"id": vid, "year": year, "make": make, "model": model, "current": current,
                     "insert": [line_row(r) for r in sorted(adds, key=lambda x: x["id"])],
                     "sources": [[r["name"], r["id"], r["atv"]] for r in sorted(adds, key=lambda x: x["id"])],
                     "kinds": [add_kind(make, model, r) for r in sorted(adds, key=lambda x: x["id"])],
                     "remove": [r for r in current if r[0] in remove], "cost_updates": updates, "cost_left": left,
                     "revised_left": [[r["name"], r["id"]] for r in rev]})
    return plan


def apply_ops(cur, plan):
    """Write exactly the planned rows; refuse any row that no longer holds what the dry run saw. Returns new line ids."""
    new_ids = []
    for p in plan:
        vid = p["id"]
        row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        if not row or tuple(row) != (p["year"], p["make"], p["model"]):
            raise RuntimeError("target %d is %r" % (vid, row and tuple(row)))
        if stored(cur, vid) != p["current"]:
            raise RuntimeError("target %d: the stored fuel-economy lines changed since the dry run" % vid)
        for r in p["remove"]:
            cur.execute("DELETE FROM fuel_economy WHERE id=? AND vehicle_id=?", (r[0], vid))
            if cur.rowcount != 1:
                raise RuntimeError("target %d: line fe#%d was not removed" % (vid, r[0]))
        for fid, old, new in p["cost_updates"]:
            cur.execute("UPDATE fuel_economy SET annual_fuel_cost=? WHERE id=? AND vehicle_id=? AND annual_fuel_cost IS ?",
                        (new, fid, vid, old))
            if cur.rowcount != 1:
                raise RuntimeError("target %d: the yearly cost of line fe#%d was not changed" % (vid, fid))
        for x in p["insert"]:
            cur.execute("INSERT INTO fuel_economy (vehicle_id, " + COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [vid] + list(x))
            new_ids.append(cur.lastrowid)
        if [r[1:] for r in stored(cur, vid)] != after_rows(p):
            raise RuntimeError("target %d does not hold the planned lines" % vid)
    return new_ids


def totals(plan):
    return (len(plan), sum(len(p["insert"]) for p in plan), sum(len(p["remove"]) for p in plan),
            sum(len(p["cost_updates"]) for p in plan))


def next_line_id(cur):
    row = cur.execute("SELECT seq FROM sqlite_sequence WHERE name='fuel_economy'").fetchone()
    return max(row[0] if row else 0, cur.execute("SELECT COALESCE(MAX(id), 0) FROM fuel_economy").fetchone()[0]) + 1


def bare_count(cur):
    return LF.bare_count(cur)


# ---------------------------------------------------------------- dry run
def _mem_copy():
    src = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def label_after(mem, plan, by_ym, plates):
    """Apply the operations to an in-memory copy, then the label script's plan; returns (new ids, label plan)."""
    cur = mem.cursor()
    first_id = next_line_id(cur)
    new_ids = apply_ops(cur, plan)
    if new_ids != list(range(first_id, first_id + len(new_ids))):
        raise PlanError("new line ids are not consecutive from %d" % first_id)
    LF.ensure_columns(cur)
    labels = LF.plan_labels(cur, by_ym, plates)
    LF.apply(cur, labels)
    mem.commit()
    if LF.plan_labels(cur, by_ym, plates):
        raise PlanError("a second label run would still change lines")
    changed = [x for x in labels if x["fe_id"] not in set(new_ids) and x["old"][:2] != x["new"][:2]]
    if changed:
        raise PlanError("%d existing lines would change their label, e.g. fe#%d %r -> %r" % (
            len(changed), changed[0]["fe_id"], changed[0]["old"][1], changed[0]["new"][1]))
    unlabelled = [i for i in new_ids if not next(x for x in labels if x["fe_id"] == i)["new"][1]]
    if unlabelled:
        raise PlanError("%d new lines get no label, e.g. fe#%d" % (len(unlabelled), unlabelled[0]))
    return first_id, new_ids, labels


def rehearse(plan, labels, new_ids, by_ym, plates):
    say("")
    say("REHEARSAL -- the real build on two in-memory copies of the database (untouched, and with the plan applied)")
    try:
        m0 = _mem_copy()
        order0 = LF.ship_order(m0.cursor())
        before, dtc0, fix0 = LF._build(m0)
        m0.close()
        m1 = _mem_copy()
        label_after(m1, plan, by_ym, plates)
        order1 = LF.ship_order(m1.cursor())
        n1 = m1.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        after, dtc1, fix1 = LF._build(m1)
        m1.close()
    except (SystemExit, AssertionError, RuntimeError, PlanError) as e:
        say("  REHEARSAL FAILED:", e)
        return None
    if sorted(before) != sorted(after) or dtc0 != dtc1 or fix0 != fix1:
        say("  REHEARSAL FAILED: the vehicle list, the code list or the fix list changed")
        return None
    by_vid = {p["id"]: p for p in plan}
    label_of = {x["fe_id"]: x["new"][1] for x in labels}
    ins = iter(new_ids)
    planned_new = {}
    for p in plan:
        for x in p["insert"]:
            planned_new[next(ins)] = (p["id"], x)
    bad, changed, reordered, cards = 0, [], 0, []
    ent = lambda x: {"city": x[CITY], "hwy": x[HWY], "comb": x[COMB], "cost": x[COST], "trans": x[TRANS], "drive": x[DRIVE],
                     "range": x[RANGE], "mpge": x[MPGE]}
    for vid, a in before.items():
        b = after[vid]
        if a == b:
            continue
        changed.append(vid)
        if sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k)) != ["mpg"]:
            say("  UNEXPECTED: id %d differs outside fuel economy" % vid)
            bad += 1
            continue
        o0, o1 = order0.get(vid, []), order1.get(vid, [])
        ma, mb = dict(zip(o0, a.get("mpg") or [])), dict(zip(o1, b.get("mpg") or []))
        p = by_vid.get(vid)
        gone = {r[0] for r in p["remove"]} if p else set()
        costs = {fid: new for fid, _o, new in p["cost_updates"]} if p else {}
        if set(ma) - set(mb) != gone or any(planned_new.get(f, (None,))[0] != vid for f in set(mb) - set(ma)):
            say("  UNEXPECTED: id %d gains or loses lines the plan does not" % vid)
            bad += 1
            continue
        for f, m in mb.items():
            if f in ma:
                want = dict(ma[f], cost=costs.get(f, ma[f].get("cost")))
                if {k: v for k, v in m.items() if k != "lbl"} != {k: v for k, v in want.items() if k != "lbl"} or \
                        m.get("lbl") != (label_of.get(f) or ma[f].get("lbl")):
                    say("  UNEXPECTED: id %d line fe#%d ships %r" % (vid, f, m))
                    bad += 1
            else:
                x = planned_new[f][1]
                got = {k: m.get(k) for k in ent(x)}
                if got != ent(x) or LF._fnum(m.get("eng")) != LF._fnum(x[ENG]) or m.get("lbl") != label_of.get(f) or not m.get("lbl"):
                    say("  UNEXPECTED: id %d new line fe#%d ships %r" % (vid, f, m))
                    bad += 1
        reordered += [f for f in o0 if f not in gone] != [f for f in o1 if f in ma]
        f0 = (a.get("mpg") or [{}])[0]
        f1 = (b.get("mpg") or [{}])[0]
        if (f0.get("comb"), f0.get("mpge"), f0.get("lbl")) != (f1.get("comb"), f1.get("mpge"), f1.get("lbl")):
            cards.append((vid, f0, f1))
    if bad:
        return None
    n_ver0 = sum(1 for v in before.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    n_ver1 = sum(1 for v in after.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    if n_ver0 != n_ver1:
        say("  REHEARSAL FAILED: owner's-manual-verified count moved %d -> %d" % (n_ver0, n_ver1))
        return None
    say("  build gates passed on both copies; vehicles %d -> %d; owner's-manual-verified %d (unchanged)" % (
        len(before), len(after), n_ver1))
    say("  %d vehicles differ, each in fuel economy only (lines, costs, labels or order); all other %d identical" % (
        len(changed), len(after) - len(changed)))
    say("  fuel-economy lines -> %d; vehicles shipping a new line order %d; search cards whose line changes %d" % (
        n1, reordered, len(cards)))
    return {"changed": len(changed), "reordered": reordered, "cards": cards, "lines_after": n1,
            "verified_ids": {v for v, x in before.items() if isinstance(x.get("oil"), dict) and x["oil"].get("ver") == 1}}


def plan_sha(saved):
    return hashlib.sha256(json.dumps(saved, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def write_report(path, plan, labels, new_ids, revised, rh, verified, sha, names):
    out = []
    w = out.append
    rows, inn, rm, nc = totals(plan)
    w("# Fuel-economy versions repair (ruling c): dry run, %s" % datetime.date.today().isoformat())
    w("")
    w("Dry run: nothing was written to the database. Local only; not staged. Plan sha256 `%s`." % sha)
    w("")
    w("| Rows | Records added | Lines removed | Yearly costs changed | Lines after | Ship order changes | Search cards that change |")
    w("|---|---|---|---|---|---|---|")
    w("| %d (%d verified) | %d | %d | %d | %d | %d | %d (%d verified) |" % (
        rows, sum(p["id"] in verified for p in plan), inn, rm, nc, rh["lines_after"], rh["reordered"], len(rh["cards"]),
        sum(v in verified for v, _a, _b in rh["cards"])))
    w("")
    kinds = collections.Counter(k for p in plan for k in p["kinds"])
    w("Added by kind: " + "; ".join("%s %d" % (k, kinds.get(k, 0)) for k in ADD_KINDS) + ".")
    w("")
    w("## Search cards that change (first line before -> after)")
    w("")
    w("| Vehicle | Verified | Before | After |")
    w("|---|---|---|---|")
    for vid, f0, f1 in sorted(rh["cards"], key=lambda c: (c[0] not in verified, c[0])):
        nm = names.get(vid) or "id %d" % vid
        fmt = lambda f: "%s mpg, %s" % (f.get("comb") if f.get("comb") is not None else f.get("mpge"), f.get("lbl") or "(no label)")
        w("| %s (id %d) | %s | %s | %s |" % (nm, vid, "yes" if vid in verified else "", fmt(f0).replace("|", "/"), fmt(f1).replace("|", "/")))
    w("")
    w("## Rows")
    w("")
    w("| Vehicle | Verified | Added (EPA name, id, kind) | Removed | Costs changed |")
    w("|---|---|---|---|---|")
    for p in plan:
        add = "; ".join("%s (%d, %s)" % (s[0], s[1], k) for s, k in zip(p["sources"], p["kinds"]))
        rem = "; ".join("fe#%d %s/%s/%s" % (r[0], r[1 + CITY], r[1 + HWY], r[1 + COMB]) for r in p["remove"])
        cst = "; ".join("fe#%d %s->%s" % (f, o, n) for f, o, n in p["cost_updates"])
        w("| %d %s %s (id %d) | %s | %s | %s | %s |" % (p["year"], p["make"], p["model"], p["id"],
                                                     "yes" if p["id"] in verified else "", add.replace("|", "/"), rem, cst))
    w("")
    w("## Left as they are")
    w("")
    w("Records whose figures a stored line holds in their pre-revision form (item e), not added: " +
      ("; ".join("id %d: EPA %d" % (v, i) for v, i in revised) or "none") + ".")
    left = [(p["id"], c) for p in plan for c in p["cost_left"]]
    w("")
    w("Lines whose EPA records carry two different costs, cost left as stored: " +
      ("; ".join("id %d fe#%d %s (EPA %s)" % (v, c[0], c[1], c[2]) for v, c in left) or "none") + ".")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")


def dry_run(zip_path, print_ops=False):
    say("FUEL-ECONOMY VERSIONS (RULING C) -- DRY RUN (nothing is written)  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    by_ym = load_epa(zip_path)
    say("EPA file: %d records, sha256 %s (pinned)" % (sum(len(v) for v in by_ym.values()), LF.ZIP_SHA256))
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        if bare_count(cur) != BARE_FROZEN:
            raise PlanError("bare owner-manual rows are not %d" % BARE_FROZEN)
        plates = epa_name_rules.fleet_plates(cur)
        ops, revised = discover(cur, by_ym, plates)
        if print_ops:
            for o in ops:
                say("    R(%d, %d, %r, %r, %r, %r, %d)," % (o["id"], o["year"], o["make"], o["model"], o["add"], o["remove"], o["cost"]))
            return
        plan = plan_ops(cur, by_ym, plates, OPS)
        verified = {r[0] for r in cur.execute("SELECT vehicle_id FROM oil_change WHERE source LIKE 'owner-manual-verified%' "
                                              "OR source LIKE 'service-manual-verified%'")}
        fleet = cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        n0 = cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        first_id = next_line_id(cur)
        plates_sha = LF.plates_sha(plates)
        names = {vid: "%d %s %s" % (y, mk, md) for vid, y, mk, md in cur.execute("SELECT id, year, make, model FROM vehicles")}
    finally:
        con.close()
    if EXPECT is None or totals(plan) != EXPECT:
        raise PlanError("totals %r, pinned %r" % (totals(plan), EXPECT))
    mem = _mem_copy()
    try:
        first, new_ids, labels = label_after(mem, plan, by_ym, plates)
    finally:
        mem.close()
    if first != first_id:
        raise PlanError("the in-memory copy numbers new lines from %d, the database from %d" % (first, first_id))
    rows, inn, rm, nc = totals(plan)
    say("")
    say("SUMMARY")
    say("  rows %d (verified %d); records added %d; lines removed %d; yearly costs changed %d" % (
        rows, sum(p["id"] in verified for p in plan), inn, rm, nc))
    kinds = collections.Counter(k for p in plan for k in p["kinds"])
    say("  added by kind: " + "; ".join("%s %d" % (k, kinds.get(k, 0)) for k in ADD_KINDS))
    say("  left for item (e), revised figures: %d records %s" % (len(revised), revised))
    say("  label plan: %d lines (plain flag on every line; labels on %d new lines)" % (len(labels), len(new_ids)))
    rh = rehearse(plan, labels, new_ids, by_ym, plates)
    if rh is None:
        raise PlanError("rehearsal failed")
    if rh["lines_after"] != n0 + inn - rm:
        raise PlanError("lines after %d, expected %d" % (rh["lines_after"], n0 + inn - rm))
    saved = {"script": os.path.basename(__file__), "epa_file_sha256": LF.ZIP_SHA256, "plates_sha256": plates_sha,
             "fleet": fleet, "lines_before": n0, "first_new_id": first_id, "new_ids": new_ids, "ops": plan, "labels": labels}
    sha = plan_sha(saved)
    report = os.path.join(ROOT, "_fe_versions_dry_run_%s.md" % datetime.date.today().isoformat())
    write_report(report, plan, labels, new_ids, revised, rh, verified, sha, names)
    with io.open(PLAN_FILE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dict(saved, sha256=sha), fh, sort_keys=True, indent=1)
    say("  report: %s" % report)
    say("")
    say("plan saved: %s" % PLAN_FILE)
    say("plan sha256: %s" % sha)
    say("to write exactly this plan (only on Robert's go):  python -I %s --write --sha %s" % (os.path.basename(__file__), sha))


# ---------------------------------------------------------------- write
def write(want):
    with io.open(PLAN_FILE, encoding="utf-8") as fh:
        saved = json.load(fh)
    body = {k: v for k, v in saved.items() if k != "sha256"}
    if plan_sha(body) != want or saved.get("sha256") != want or saved.get("epa_file_sha256") != LF.ZIP_SHA256:
        sys.exit("plan file hash does not match --sha %s: run the dry run again and get a fresh go" % want)
    plan, labels, new_ids = saved["ops"], saved["labels"], saved["new_ids"]
    if [(p["id"], p["year"]) for p in plan] != [(o["id"], o["year"]) for o in OPS]:
        sys.exit("the saved plan does not match this script's operations")
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        bare, fleet, n0 = bare_count(cur), cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0], \
            cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        plates_now = LF.plates_sha(epa_name_rules.fleet_plates(cur))
        first_now = next_line_id(cur)
    finally:
        con.close()
    if bare != BARE_FROZEN or fleet != saved["fleet"] or n0 != saved["lines_before"]:
        sys.exit("bare rows %d / fleet %d / lines %d differ from the dry run" % (bare, fleet, n0))
    if plates_now != saved["plates_sha256"] or first_now != saved["first_new_id"]:
        sys.exit("the fleet's nameplates or the next line id changed since the dry run: run it again and get a fresh go")
    bak = "%s.bak_fe_versions_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    rows, inn, rm, nc = totals(plan)
    con = sqlite3.connect(DB, isolation_level=None)          # explicit transaction: DDL rolls back too
    cur = con.cursor()
    cur.execute("BEGIN IMMEDIATE")
    try:
        got_ids = apply_ops(cur, plan)
        if got_ids != new_ids:
            raise RuntimeError("new lines got ids %s..., the dry run planned %s..." % (got_ids[:3], new_ids[:3]))
        added = LF.ensure_columns(cur)
        LF.apply(cur, labels)
        if cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0] != n0 + inn - rm or \
                cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] != fleet or bare_count(cur) != BARE_FROZEN:
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
    say("WRITTEN: %d rows (%d lines added, %d removed, %d yearly costs changed); label columns added %s; %d lines "
        "labelled or flagged; fuel-economy lines %d -> %d; fleet %d; bare rows %d" % (
            rows, inn, rm, nc, added or "none", len(labels), n0, n0 + inn - rm, fleet, BARE_FROZEN))


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
