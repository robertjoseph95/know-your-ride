"""Fuel-economy version labels: match every stored fuel-economy line to EPA's complete file and store the
EPA record ids behind it (fuel_economy.epa_ids, never shipped) and its version label
(fuel_economy.epa_label, shipped as mpg[].lbl by files/04_rebuild_demo.py).

Design (approved by Robert 2026-11-20): docs/superpowers/specs/2026-11-20-fuel-economy-version-labels-design.md
Plan:  docs/superpowers/plans/2026-11-20-fuel-economy-version-labels.md

The label is EPA's model name plus tags, built only from EPA's own record fields (files/fe_labels.py):
`<names> · <tags>`. Names are those of the matching records that the full comparison's naming rules
(files/epa_name_rules.py) class as the vehicle's own or one of its versions; another vehicle's names are
dropped unless nothing else matches. A line that matches no EPA record is marked assessed (epa_ids = '')
and gets no label. Re-runnable: a later run labels lines written since and changes nothing else.

Matching (the rule every fuel-economy repair since 2026-11-15 uses):
    gasoline-type line  EPA records of the same make and model year with equal city, highway, combined,
                        engine size, transmission and drive
    electric line       EPA records typed EV or FCV with combined = the line's MPGe, range = its range,
                        equal transmission and drive

Source: EPA fueleconomy.gov complete file vehicles.csv.zip (U.S. government), last modified by EPA on
2026-11-04, SHA-256 pinned below. The file is untrusted data: its path is an argument, it is read into
memory, it must hold exactly one member, and that member is only parsed as CSV.

    python -I _label_fuel_economy.py <path to vehicles.csv.zip>
        DRY RUN. Checks the file's hash, plans every line, writes the review report
        _fe_labels_dry_run_<date>.md (local only), rehearses the real build on in-memory copies of the
        database (untouched, and with the plan applied), saves the plan and prints its sha256.
        Writes nothing to wrench_vehicles.db.

    python -I _label_fuel_economy.py --write --sha <sha256 printed by the dry run>
        Backs up the database, adds the two columns if absent, then applies EXACTLY the saved plan.
        Each line changes only if it still holds what the dry run saw.
"""
import collections
import contextlib
import csv
import datetime
import hashlib
import importlib.util
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

DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_label_fuel_economy_plan_cache.json")      # gitignored (*_cache.json)
ZIP_SHA256 = "1d553896a77898f6cf47128281337af268df053c90dc1365891c7c8abff82c82"
ZIP_MAX = 50 * 1024 * 1024
CSV_MAX = 200 * 1024 * 1024
BARE_FROZEN = 424
ELECTRIC_ATV = ("EV", "FCV")
LINE_COLS = ("city_mpg", "highway_mpg", "combined_mpg", "engine", "transmission", "drive", "fuel_type", "mpge", "range_miles")
REASON_FIELDS = (("eng_dscr", "EPA engine notes"), ("vclass", "EPA vehicle class"), ("startstop", "EPA stop-start flag"),
                 ("trans_dscr", "EPA transmission notes"), ("engid", "EPA internal engine code"))
SPEC_GROUPS, SPEC_TOLD_APART = 1154, 924


class PlanError(Exception):
    pass


def say(*a):
    print(" ".join(str(x) for x in a).encode("ascii", "replace").decode("ascii"), flush=True)


def _num(x):
    try:
        return int(float(x)) if x not in ("", None) else None
    except ValueError:
        return None


def _fnum(text):
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(text)) if text not in (None, "") else None
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------- EPA's file
def load_epa(path):
    """(year, make.lower()) -> EPA record dicts. Refuses any file that is not the pinned one."""
    with open(path, "rb") as fh:
        data = fh.read(ZIP_MAX + 1)
    if len(data) > ZIP_MAX:
        raise PlanError("%s is larger than %d bytes: not the pinned EPA file" % (path, ZIP_MAX))
    got = hashlib.sha256(data).hexdigest()
    if got != ZIP_SHA256:
        raise PlanError("%s has sha256 %s, not the pinned EPA file %s" % (path, got, ZIP_SHA256))
    z = zipfile.ZipFile(io.BytesIO(data))
    info = z.infolist()
    if [i.filename for i in info] != ["vehicles.csv"] or info[0].file_size > CSV_MAX:
        raise PlanError("the EPA file must hold exactly one member, vehicles.csv, of at most %d bytes" % CSV_MAX)
    by_ym, seen = collections.defaultdict(list), set()
    for r in csv.DictReader(io.StringIO(z.read("vehicles.csv").decode("utf-8", "replace"))):
        rec = {"id": int(r["id"]), "year": int(r["year"]), "make": r["make"].strip(), "name": r["model"].strip(),
               "atv": r["atvType"].strip(), "city": _num(r["city08"]), "hwy": _num(r["highway08"]), "comb": _num(r["comb08"]),
               "displ": _fnum(r["displ"]), "trans": r["trany"].strip() or None, "drive": r["drive"].strip() or None,
               "range": _num(r["range"]) or None, "tcharger": r["tCharger"].strip(), "scharger": r["sCharger"].strip(),
               "eng_dscr": r["eng_dscr"].strip(), "vclass": r["VClass"].strip(), "startstop": r["startStop"].strip(),
               "trans_dscr": r["trans_dscr"].strip(), "engid": r["engId"].strip()}
        if rec["id"] in seen:
            raise PlanError("EPA record id %d appears twice in the file" % rec["id"])
        seen.add(rec["id"])
        by_ym[(rec["year"], rec["make"].lower())].append(rec)
    return dict(by_ym)


def match_line(line, recs):
    """The EPA records behind one stored line (see the module docstring for the rule)."""
    if line["fuel_type"] == "Electric":
        if line["mpge"] is None or line["range_miles"] is None:
            return []
        return [r for r in recs if r["atv"] in ELECTRIC_ATV and r["comb"] == line["mpge"] and r["range"] == line["range_miles"]
                and r["trans"] == line["transmission"] and r["drive"] == line["drive"]]
    key = (line["city_mpg"], line["highway_mpg"], line["combined_mpg"], _fnum(line["engine"]), line["transmission"], line["drive"])
    return [r for r in recs if (r["city"], r["hwy"], r["comb"], r["displ"], r["trans"], r["drive"]) == key]


# ---------------------------------------------------------------- the database
def _has_label_columns(cur):
    cols = {r[1] for r in cur.execute("PRAGMA table_info(fuel_economy)").fetchall()}
    return {"epa_ids", "epa_label"} <= cols


# A label describes the line it was built for. When a script later edits what the line was matched on
# (its figures, engine, transmission, drive, fuel type, MPGe or range) or the vehicle's year, make or
# model, the label no longer holds: these triggers clear it, the card then shows no label and the
# verifier's S1.15 warns until this script runs again (the spec's rule for lines written later).
_TRIGGERS = (
    "CREATE TRIGGER IF NOT EXISTS fe_label_reset_on_line_change AFTER UPDATE OF %s ON fuel_economy WHEN %s "
    "BEGIN UPDATE fuel_economy SET epa_ids = NULL, epa_label = NULL WHERE id = NEW.id; END"
    % (", ".join(LINE_COLS), " OR ".join("OLD.%s IS NOT NEW.%s" % (c, c) for c in LINE_COLS)),
    "CREATE TRIGGER IF NOT EXISTS fe_label_reset_on_vehicle_change AFTER UPDATE OF year, make, model ON vehicles "
    "WHEN OLD.year IS NOT NEW.year OR OLD.make IS NOT NEW.make OR OLD.model IS NOT NEW.model "
    "BEGIN UPDATE fuel_economy SET epa_ids = NULL, epa_label = NULL WHERE vehicle_id = NEW.id; END",
)


def ensure_columns(cur):
    """Add the two label columns when absent (returns the names added) and the two reset triggers."""
    cols = {r[1] for r in cur.execute("PRAGMA table_info(fuel_economy)").fetchall()}
    added = []
    for name in ("epa_ids", "epa_label"):
        if name not in cols:
            cur.execute("ALTER TABLE fuel_economy ADD COLUMN %s TEXT" % name)
            added.append(name)
    for sql in _TRIGGERS:
        cur.execute(sql)
    return added


def assess_lines(cur, epa, plates):
    """Every stored line with the records behind it and the label they give (in vehicle, then row order)."""
    labelled = _has_label_columns(cur)
    extra = ", epa_ids, epa_label" if labelled else ", NULL, NULL"
    lines = collections.defaultdict(list)
    for row in cur.execute("SELECT id, vehicle_id, %s%s FROM fuel_economy ORDER BY id" % (", ".join(LINE_COLS), extra)):
        lines[row[1]].append(row)
    out = []
    for vid, year, make, model in cur.execute("SELECT id, year, make, model FROM vehicles ORDER BY id").fetchall():
        if vid not in lines:
            continue
        recs = epa.get((year, make.lower()), [])
        classes = epa_name_rules.name_classes(year, make, model, recs, plates)[0] if recs else {}
        for row in lines[vid]:
            line = dict(zip(LINE_COLS, row[2:2 + len(LINE_COLS)]))
            hit = match_line(line, recs)
            kept = fe_labels.kept_records(hit, classes) if hit else []
            new = [fe_labels.ids_text(kept), fe_labels.label_text(kept)] if kept else ["", None]
            out.append({"fe_id": row[0], "vehicle_id": vid, "year": year, "make": make, "model": model, "line": line,
                        "hit": hit, "kept": kept, "old": [row[-2], row[-1]], "new": new})
    return out


def _plan_item(a):
    """A plan line carries what the label was computed from, so the write can refuse a line that moved."""
    return {"fe_id": a["fe_id"], "vehicle_id": a["vehicle_id"], "old": a["old"], "new": a["new"],
            "line": [a["line"][c] for c in LINE_COLS], "vehicle": [a["year"], a["make"], a["model"]]}


def plan_labels(cur, epa, plates):
    """One item per line whose computed (epa_ids, epa_label) differs from what is stored."""
    return [_plan_item(a) for a in assess_lines(cur, epa, plates) if a["new"] != a["old"]]


def apply(cur, plan):
    """Write each planned label; refuse any line or vehicle that no longer holds what the dry run saw."""
    seen = {}
    for p in plan:
        vid = p["vehicle_id"]
        if vid not in seen:
            row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
            seen[vid] = list(row) if row else None
        if seen[vid] != p["vehicle"]:
            raise RuntimeError("vehicle %d is %r, the dry run saw %r" % (vid, seen[vid], p["vehicle"]))
        cur.execute("UPDATE fuel_economy SET epa_ids=?, epa_label=? WHERE id=? AND vehicle_id=? AND epa_ids IS ? "
                    "AND epa_label IS ? AND " + " AND ".join("%s IS ?" % c for c in LINE_COLS),
                    [p["new"][0], p["new"][1], p["fe_id"], vid, p["old"][0], p["old"][1]] + list(p["line"]))
        if cur.rowcount != 1:
            raise RuntimeError("line fe#%d of vehicle %d no longer holds what the dry run saw" % (p["fe_id"], vid))


def label_words_ok(label, ids, kept):
    """Independent check that a stored label says only what EPA's records say: the ids are those of the
    records behind it, the names part is their EPA names, and every tag is one every record carries."""
    if not kept:
        return label is None and ids == ""
    if ids != ",".join(str(i) for i in sorted({int(r["id"]) for r in kept})) or not label:
        return False
    head, sep, tail = label.partition(fe_labels.SEP)
    if head != ", ".join(sorted({r["name"] for r in kept})):
        return False
    tests = dict(fe_labels.TAGS)
    return all(t in tests and all(tests[t](r) for r in kept) for t in tail.split(", ")) if sep else True


def bare_count(cur):
    return cur.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                       "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) "
                       "WHERE source='owner-manual-verified'").fetchone()[0]


# ---------------------------------------------------------------- the review report
def lookalike_groups(assessed):
    """Groups of gasoline-type lines on one vehicle with identical card text and two or more figure sets."""
    g = collections.defaultdict(list)
    for a in assessed:
        ln = a["line"]
        if ln["fuel_type"] == "Electric":
            continue
        g[(a["vehicle_id"], ln["engine"], ln["transmission"], ln["drive"])].append(a)
    out = []
    for key, items in g.items():
        figs = collections.OrderedDict()
        for a in items:
            figs.setdefault((a["line"]["city_mpg"], a["line"]["highway_mpg"], a["line"]["combined_mpg"]), []).append(a)
        if len(figs) > 1:
            out.append((key, figs))
    return out


def group_verdict(figs):
    """'told apart', or the reason a group's labels do not tell its figure sets apart."""
    sets = list(figs.values())
    if any(not a["kept"] for items in sets for a in items):
        return "a line matches no EPA record"
    distinct = lambda vals: len(set(vals)) == len(vals)
    labels = [frozenset(a["new"][1] for a in items) for items in sets]
    if distinct(labels) and all(len(x) == 1 for x in labels):
        return "told apart"
    if distinct([frozenset(fe_labels.label_text(a["hit"]) for a in items) for items in sets]):
        return "only another vehicle's name differs (dropped by the keep rule)"
    if distinct([frozenset((r["atv"], r["tcharger"], r["scharger"]) for a in items for r in a["kept"]) for items in sets]):
        return "a fuel type or charger only some records carry (hidden by the every-record rule)"
    for field, name in REASON_FIELDS:
        if distinct([frozenset(r[field] for a in items for r in a["kept"]) for items in sets]):
            return "only %s differ" % name
    if len(set(labels)) > 1:
        return "partly told apart"
    return "no EPA field"


def write_report(path, assessed, plan, sha, jargon_hits):
    gas = [a for a in assessed if a["line"]["fuel_type"] != "Electric"]
    ele = [a for a in assessed if a["line"]["fuel_type"] == "Electric"]
    groups = lookalike_groups(assessed)
    verdicts = [(key, figs, group_verdict(figs)) for key, figs in groups]
    told = sum(1 for _k, _f, v in verdicts if v == "told apart")
    longest = max((a["new"][1] for a in assessed if a["new"][1]), key=len, default="")
    L = ["# Fuel-economy version labels: dry run, %s" % datetime.date.today().isoformat(), "",
         "Read-only. Nothing in the database, the site or git was changed. Local only, never staged.", "",
         "Plan sha256 `%s`; EPA file sha256 `%s`." % (sha, ZIP_SHA256), "", "## Result", "",
         "| | Count |", "|---|---|",
         "| Lines | %d |" % len(assessed),
         "| Gasoline-type lines labelled | %d |" % sum(1 for a in gas if a["kept"]),
         "| Electric lines labelled | %d |" % sum(1 for a in ele if a["kept"]),
         "| Lines matched against EPA with no record | %d |" % sum(1 for a in assessed if not a["kept"]),
         "| Lines whose stored label changes | %d |" % len(plan),
         "| Look-alike groups | %d (spec %d) |" % (len(groups), SPEC_GROUPS),
         "| ... told apart by the label | %d (spec at least %d) |" % (told, SPEC_TOLD_APART),
         "| Labels the S1.12 jargon pattern flags | %d |" % jargon_hits,
         "| Longest label | %d characters |" % len(longest), "",
         "Longest label: `%s`" % longest, "", "## Look-alike groups the label does not tell apart", "",
         "| Vehicle | Card text | Reason | Labels |", "|---|---|---|---|"]
    names = {a["vehicle_id"]: "%d %s %s" % (a["year"], a["make"], a["model"]) for a in assessed}
    reasons = collections.Counter(v for _k, _f, v in verdicts if v != "told apart")
    for key, figs, v in sorted(verdicts, key=lambda x: (names[x[0][0]], x[0][1:])):
        if v == "told apart":
            continue
        labels = " / ".join("%s/%s/%s: %s" % (f + ("; ".join(sorted({a["new"][1] or "(none)" for a in items})),))
                            for f, items in figs.items())
        L.append("| %s | %sL %s, %s | %s | %s |" % (names[key[0]], key[1], key[2], key[3], v, labels))
    L += ["", "Reasons: " + ", ".join("%s %d" % kv for kv in reasons.most_common()), "",
          "## Sample labels", "", "| Vehicle | Card text | Figures | Label |", "|---|---|---|---|"]
    for want in ((2020, "Volvo", "XC90"), (2016, "Chevrolet", "Silverado 1500"), (2016, "Toyota", "Camry"),
                 (2021, "Ford", "Mustang"), (2009, "Chevrolet", "Silverado 1500"), (2024, "Cadillac", "Escalade")):
        for a in assessed:
            if (a["year"], a["make"], a["model"]) == want:
                ln = a["line"]
                L.append("| %d %s %s | %s %s, %s | %s/%s/%s | %s |" % (want + (ln["engine"], ln["transmission"], ln["drive"],
                         ln["city_mpg"], ln["highway_mpg"], ln["combined_mpg"], a["new"][1] or "(no EPA record)")))
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    return told, len(groups)


# ---------------------------------------------------------------- rehearsal on in-memory copies
def _build(con):
    spec = importlib.util.spec_from_file_location("kyr_build_04", os.path.join(FILES_DIR, "04_rebuild_demo.py"))
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    with contextlib.redirect_stdout(io.StringIO()):
        b._assert_registry_admission(cur)
        b.assert_frozen_landscape(cur)
        vlist, dtc, fixes, _with_comps = b.build_data(cur)
        b._strip_unverified(vlist)
        b._assert_ic01_projection(vlist)
    return {v["id"]: v for v in vlist}, dtc, fixes


def _mem_copy():
    src = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def label_change_ok(before, after, fid, planned):
    """One shipped line before vs after the plan: nothing but `lbl` may differ, and `lbl` must be the
    planned label for a planned line, or unchanged for a line the plan leaves alone (a re-run)."""
    strip = lambda m: {k: v for k, v in m.items() if k != "lbl"}
    if strip(before) != strip(after):
        return False
    want = planned[fid] if fid in planned else before.get("lbl")
    return after.get("lbl") == want


def rehearse(plan):
    say("")
    say("REHEARSAL -- the real build on two in-memory copies of the database (untouched, and with the plan applied)")
    try:
        m0 = _mem_copy()
        before, dtc0, fix0 = _build(m0)
        m0.close()
        m1 = _mem_copy()
        c1 = m1.cursor()
        n0 = c1.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        order = collections.defaultdict(list)
        for fid, vid in c1.execute("SELECT id, vehicle_id FROM fuel_economy ORDER BY id"):
            order[vid].append(fid)
        ensure_columns(c1)
        apply(c1, plan)
        m1.commit()
        if c1.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0] != n0 or bare_count(c1) != BARE_FROZEN:
            say("  REHEARSAL FAILED: the line count or the bare rows moved")
            return False
        after, dtc1, fix1 = _build(m1)
        m1.close()
    except (SystemExit, AssertionError, RuntimeError) as e:
        say("  REHEARSAL FAILED: the build stopped:", e)
        return False
    if sorted(before) != sorted(after) or dtc0 != dtc1 or fix0 != fix1:
        say("  REHEARSAL FAILED: the vehicle list, the code list or the fix list changed")
        return False
    label = {p["fe_id"]: p["new"][1] for p in plan}
    bad, changed = 0, 0
    for vid, a in before.items():
        b = after[vid]
        if a == b:
            continue
        changed += 1
        if sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k)) != ["mpg"]:
            say("  UNEXPECTED: id %d differs outside fuel economy" % vid)
            bad += 1
            continue
        ma, mb = a.get("mpg") or [], b.get("mpg") or []
        if len(ma) != len(mb) or len(mb) != len(order[vid]):
            say("  UNEXPECTED: id %d ships a different number of lines" % vid)
            bad += 1
            continue
        for fid, ea, eb in zip(order[vid], ma, mb):
            if not label_change_ok(ea, eb, fid, label):
                say("  UNEXPECTED: id %d line fe#%d ships %r, planned label %r" % (vid, fid, eb, label.get(fid)))
                bad += 1
    if bad:
        return False
    n_ver0 = sum(1 for v in before.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    n_ver1 = sum(1 for v in after.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    if n_ver0 != n_ver1:
        say("  REHEARSAL FAILED: owner's-manual-verified count moved %d -> %d" % (n_ver0, n_ver1))
        return False
    shipped = sum(1 for v in after.values() for m in (v.get("mpg") or []) if "lbl" in m)
    say("  build gates passed on both copies; vehicles %d -> %d; owner's-manual-verified %d (unchanged)" % (len(before), len(after), n_ver1))
    say("  %d vehicles differ, each only by fuel-economy labels; all other %d vehicles identical" % (changed, len(after) - changed))
    say("  lines %d (unchanged); labels shipped %d; bare owner-manual rows %d" % (n0, shipped, BARE_FROZEN))
    return True


# ---------------------------------------------------------------- dry run and write
def plan_sha(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def plates_sha(plates):
    """The fleet's nameplates decide the name classes, so the write refuses a fleet that changed since the dry run."""
    body = json.dumps(sorted([mk, sorted(models)] for mk, models in plates.items()), ensure_ascii=True)
    return hashlib.sha256(body.encode("ascii")).hexdigest()


def save_plan(plan, fleet_plates_sha):
    sha = plan_sha(plan)
    with io.open(PLAN_FILE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"script": os.path.basename(__file__), "sha256": sha, "epa_file_sha256": ZIP_SHA256,
                   "plates_sha256": fleet_plates_sha, "plan": plan}, fh, sort_keys=True, indent=1)
    return sha


def dry_run(zip_path):
    say("FUEL-ECONOMY VERSION LABELS -- DRY RUN (nothing is written)  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    epa = load_epa(zip_path)
    say("EPA file: %d records, sha256 %s (pinned)" % (sum(len(v) for v in epa.values()), ZIP_SHA256))
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        if bare_count(cur) != BARE_FROZEN:
            raise PlanError("bare owner-manual rows are not %d" % BARE_FROZEN)
        plates = epa_name_rules.fleet_plates(cur)
        assessed = assess_lines(cur, epa, plates)
        plan = [_plan_item(a) for a in assessed if a["new"] != a["old"]]
    finally:
        con.close()
    import _verify_shipped
    jargon = [a["new"][1] for a in assessed if a["new"][1] and _verify_shipped._JARGON_RE.search(a["new"][1])]
    too_long = [a["new"][1] for a in assessed if a["new"][1] and len(a["new"][1]) > _verify_shipped.MPG_LABEL_MAX]
    not_epa = [a for a in assessed if not label_words_ok(a["new"][1], a["new"][0], a["kept"])]
    sha = plan_sha(plan)
    report = os.path.join(ROOT, "_fe_labels_dry_run_%s.md" % datetime.date.today().isoformat())
    told, groups = write_report(report, assessed, plan, sha, len(jargon))
    say("")
    say("SUMMARY")
    say("  lines %d; labelled %d; matched with no EPA record %d; lines whose label changes %d" % (
        len(assessed), sum(1 for a in assessed if a["kept"]), sum(1 for a in assessed if not a["kept"]), len(plan)))
    say("  look-alike groups %d (spec %d); told apart %d (spec at least %d)" % (groups, SPEC_GROUPS, told, SPEC_TOLD_APART))
    say("  report: %s" % report)
    if jargon:
        raise PlanError("%d labels carry process-jargon words, e.g. %r" % (len(jargon), jargon[0]))
    if too_long:
        raise PlanError("%d labels exceed %d characters, e.g. %r" % (len(too_long), _verify_shipped.MPG_LABEL_MAX, too_long[0][:80]))
    if not_epa:
        raise PlanError("%d labels say something EPA's records do not, e.g. line fe#%d: %r" % (
            len(not_epa), not_epa[0]["fe_id"], not_epa[0]["new"][1]))
    if not rehearse(plan):
        raise PlanError("rehearsal failed")
    if save_plan(plan, plates_sha(plates)) != sha:
        raise PlanError("the saved plan does not hash to the plan reported")
    say("")
    say("plan saved: %s" % PLAN_FILE)
    say("plan sha256: %s" % sha)
    say("to write exactly this plan (only on Robert's go):  python -I %s --write --sha %s" % (os.path.basename(__file__), sha))


def write(want):
    """Apply exactly the saved plan whose sha256 is `want`, in ONE transaction (the columns, the triggers and
    every label commit together or not at all), after a backup of the database."""
    with io.open(PLAN_FILE, encoding="utf-8") as fh:
        saved = json.load(fh)
    plan = saved["plan"]
    if plan_sha(plan) != want or saved.get("sha256") != want or saved.get("epa_file_sha256") != ZIP_SHA256:
        sys.exit("plan file hash does not match --sha %s: run the dry run again and get a fresh go" % want)
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        bare, fleet, n0 = bare_count(cur), cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0], \
            cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        plates_now = plates_sha(epa_name_rules.fleet_plates(cur))
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    if plates_now != saved.get("plates_sha256"):
        sys.exit("the fleet's nameplates changed since the dry run: run the dry run again and get a fresh go")
    bak = "%s.bak_fe_labels_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    con = sqlite3.connect(DB, isolation_level=None)          # explicit transaction: DDL rolls back too
    cur = con.cursor()
    cur.execute("BEGIN IMMEDIATE")
    try:
        added = ensure_columns(cur)
        apply(cur, plan)
        if cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0] != n0 or \
                cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] != fleet or bare_count(cur) != BARE_FROZEN:
            raise RuntimeError("line count, fleet count or bare rows moved")
        unassessed = cur.execute("SELECT COUNT(*) FROM fuel_economy WHERE epa_ids IS NULL").fetchone()[0]
        if unassessed:
            raise RuntimeError("%d lines are still unassessed after the write" % unassessed)
        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        con.close()
        raise
    con.close()
    say("WRITTEN: columns added %s; %d lines labelled or marked; fuel-economy rows %d; fleet %d; bare rows %d" % (
        added or "none", len(plan), n0, fleet, BARE_FROZEN))


if __name__ == "__main__":
    if "--write" in sys.argv:
        i = sys.argv.index("--sha") if "--sha" in sys.argv else -1
        if i < 0 or i + 1 >= len(sys.argv):
            sys.exit("--write needs --sha <the sha256 a dry run printed>")
        write(sys.argv[i + 1])
    else:
        if len(sys.argv) != 2:
            sys.exit("usage: python -I %s <path to vehicles.csv.zip>" % os.path.basename(__file__))
        try:
            dry_run(sys.argv[1])
        except PlanError as e:
            say("")
            say("STOPPED -- a check did not come back clean, so no plan was saved:")
            say("   ", e)
            sys.exit(2)
