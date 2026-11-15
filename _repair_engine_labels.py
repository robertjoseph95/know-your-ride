"""Engine-label repair: thirteen `vehicles.engine` labels that EPA contradicts.

Found 2026-11-15 by testing every engine label against the engines EPA lists for the nameplate and year. The label
field has no source column and ships as plain text, so a wrong label is shown as fact. Thirteen labels name an engine
size that EPA does not list for that vehicle at all.

Rulings (Robert, 2026-11-15, "Accept, start dry run"):
  ELECTRIC  2024 Dodge Charger: EPA lists only the electric Charger for 2024 and types every record EV. The label
            becomes 'Electric', the label 62 other electric cars carry.
  CLEAR     the other twelve labels are cleared. Standing rule: a label stays empty unless it is sourced, and none of
            these has a sourced replacement yet.
  NOT in scope: the Sierra 2500 fuel-economy lines, the fifty unlabelled electric cars, the static vehicle pages,
            labels that are only partly wrong or doubtful, and layout errors EPA cannot test.

Source: EPA fueleconomy.gov only (government). Status-aware: an answer that is not HTTP 200 with a usable body stops
the run. The proof for each row is negative, so it is made as wide as possible: the label's engine size must be
absent from EVERY EPA model name that contains the nameplate for that year. If any such name lists that size, the run
stops and the label is left alone.

    python _repair_engine_labels.py
        DRY RUN. Pulls, prints each label before and after with the EPA evidence, rehearses the real build on
        in-memory copies of the database (before and after), saves the plan and prints its sha256. Writes nothing.

    python _repair_engine_labels.py --write --sha <sha256 printed by the dry run>
        Backs up the database, then applies EXACTLY the saved plan. A row is changed only if its label still equals
        what the dry run saw.

After a write: `python files/04_rebuild_demo.py`, then `python _gen_guide_specs.py` (the guide input embeds the label
of verified vehicles, so two entries change).
"""
import sqlite3, shutil, datetime, sys, os, io, re, json, time, socket, hashlib, importlib.util, contextlib
import urllib.request, urllib.error, urllib.parse
import defusedxml.ElementTree as ET        # hardened parser; fetch_xml() also refuses any document type declaration

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_repair_engine_labels_plan_cache.json")      # gitignored (*_cache.json)
WRITE = "--write" in sys.argv
BARE_FROZEN = 424
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
EPA = "https://www.fueleconomy.gov/ws/rest/vehicle"
PACE = 0.5
Q = urllib.parse.quote
REQUESTS = []
_last = [0.0]

# (id, year, make, model, label as stored, new label)
OPS = [
    (13024, 2024, "Dodge", "Charger", "5.7L Hemi", "Electric"),
    (13156, 2026, "Dodge", "Charger", "5.7L Hemi", None),
    (12673, 2019, "Hyundai", "Santa Fe", "2.5L I4", None),
    (12781, 2020, "Hyundai", "Santa Fe", "2.5L Turbo", None),
    (13184, 2026, "Jeep", "Grand Cherokee", "5.7L Hemi", None),
    (13133, 2025, "Toyota", "Camry", "3.5L V6", None),
    (13195, 2026, "Toyota", "Camry", "3.5L V6", None),
    (11419, 2008, "Toyota", "Highlander", "2.7L I4", None),
    (13069, 2024, "Toyota", "Highlander", "3.5L V6", None),
    (13073, 2024, "Toyota", "Tacoma", "2.7L I4", None),
    (13139, 2025, "Toyota", "Tacoma", "3.5L V6", None),
    (13201, 2026, "Toyota", "Tacoma", "2.7L I4", None),
    (12811, 2020, "Toyota", "Tundra", "4.6L V8", None),
]
assert len({o[0] for o in OPS}) == len(OPS) == 13


class PullError(Exception):
    pass


def say(*a):
    print(" ".join(str(x) for x in a).encode("ascii", "replace").decode("ascii"), flush=True)


def fetch_xml(url, what):
    for attempt in (1, 2, 3):
        wait = PACE - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            try:
                with urllib.request.urlopen(req, timeout=45) as r:
                    status, body, ra = r.status, r.read(), ""
            except urllib.error.HTTPError as e:
                status, body = e.code, b""
                ra = (e.headers.get("Retry-After") or "").strip() if e.headers else ""
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            REQUESTS.append((what, "ERR"))
            if attempt < 3:
                time.sleep(5 * attempt)
                continue
            raise PullError("%s: %r" % (what, e))
        REQUESTS.append((what, status))
        if status == 200:
            if b"<!DOCTYPE" in body or b"<!ENTITY" in body or len(body) > 2000000:
                raise PullError("%s: HTTP 200 but the XML carries a document type declaration or is oversized" % what)
            try:
                return ET.fromstring(body)
            except Exception as e:
                raise PullError("%s: HTTP 200 but the body is not XML (%r)" % (what, e))
        if status in (429, 500, 502, 503, 504) and attempt < 3:
            time.sleep(int(ra) if ra.isdigit() and int(ra) <= 120 else 10 * attempt)
            continue
        raise PullError("%s: HTTP %s" % (what, status))
    raise PullError("%s: no answer" % what)


_MENU = {}


def menu(year, make):
    if (year, make) not in _MENU:
        root = fetch_xml("%s/menu/model?year=%d&make=%s" % (EPA, year, Q(make)), "EPA models %d %s" % (year, make))
        names = [(mi.findtext("text") or "").strip() for mi in root.iter("menuItem")]
        if not names:
            raise PullError("EPA models %d %s: HTTP 200 but no model list" % (year, make))
        _MENU[(year, make)] = names
    return _MENU[(year, make)]


def options(year, make, name):
    root = fetch_xml("%s/menu/options?year=%d&make=%s&model=%s" % (EPA, year, Q(make), Q(name)), "EPA options %d %s %s" % (year, make, name))
    opts = [((mi.findtext("value") or "").strip(), (mi.findtext("text") or "").strip()) for mi in root.iter("menuItem")]
    if not opts or not all(v.isdigit() for v, _ in opts):
        raise PullError("EPA options %d %s %s: HTTP 200 but no usable option list" % (year, make, name))
    return opts


def record_type(eid, year, make, name):
    v = fetch_xml("%s/%s" % (EPA, eid), "EPA vehicle %s" % eid)
    g = lambda f: (v.findtext(f) or "").strip()
    if (g("year"), g("make"), g("model")) != (str(year), make, name):
        raise PullError("EPA vehicle %s is %s %s %s, not %d %s %s" % (eid, g("year"), g("make"), g("model"), year, make, name))
    return g("atvType"), g("displ")


def sizes(label):
    return sorted({"%.1f" % float(x) for x in re.findall(r"(\d\.\d)\s*[LlTt]", label or "")})


def plan_op(cur, op, pulled_at):
    vid, year, make, model, old, new = op
    row = cur.execute("SELECT year, make, model, engine FROM vehicles WHERE id=?", (vid,)).fetchone()
    if not row or tuple(row) != (year, make, model, old):
        sys.exit("target %d is %r, not %d %s %s with label %r" % (vid, row and tuple(row), year, make, model, old))
    want = sizes(old)
    if not want:
        sys.exit("target %d: the stored label %r names no engine size" % (vid, old))
    names = menu(year, make)
    near = sorted(n for n in names if model.lower() in n.lower())
    if not near:
        raise PullError("%d %s %s: EPA lists no model name containing the nameplate -- nothing to judge the label by" % (year, make, model))
    ev = {}
    for n in near:
        opts = options(year, make, n)
        ev[n] = {"sizes": sorted({m for _, t in opts for m in re.findall(r"(\d\.\d) L", t)}), "options": [t for _, t in opts]}
        if new == "Electric":
            types = [record_type(eid, year, make, n) for eid, _ in opts]
            ev[n]["types"] = sorted({t for t, _ in types})
            if ev[n]["sizes"] or any(t != "EV" or d for t, d in types):
                raise PullError("%d %s %s: EPA name %r is not electric-only -- 'Electric' is not justified, needs a ruling" % (year, make, model, n))
    listed = sorted({s for e in ev.values() for s in e["sizes"]})
    clash = [s for s in want if s in listed]
    if clash:
        raise PullError("%d %s %s: EPA DOES list a %s L engine under a name containing the nameplate -- the label %r is not contradicted, left alone"
                        % (year, make, model, "/".join(clash), old))
    say("")
    say("id %-6d %d %s %s" % (vid, year, make, model))
    say("  label now : %r   (engine size %s)" % (old, " / ".join(want)))
    say("  EPA lists : %s" % ("; ".join("%s [%s]" % (n, ", ".join(e["sizes"]) + " L" if e["sizes"] else ("no engine size, typed %s" % "/".join(e["types"]) if e.get("types") else "no engine size in the option list")) for n, e in ev.items())))
    say("  engine sizes EPA lists for the nameplate: %s -> the label's %s is not among them" % (", ".join(listed) if listed else "none (electric only)", " / ".join(want)))
    say("  label after: %s" % ("'Electric'" if new else "(empty)"))
    return {"id": vid, "year": year, "make": make, "model": model, "old": old, "new": new, "label_sizes": want, "epa_sizes": listed,
            "evidence": ev, "pulled_at": pulled_at}


def plan_sha(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def apply(cur, plan):
    for p in plan:
        row = cur.execute("SELECT year, make, model, engine FROM vehicles WHERE id=?", (p["id"],)).fetchone()
        if not row or tuple(row) != (p["year"], p["make"], p["model"], p["old"]):
            raise RuntimeError("target %d is %r: the row changed since the dry run" % (p["id"], row and tuple(row)))
        cur.execute("UPDATE vehicles SET engine=? WHERE id=? AND engine=?", (p["new"], p["id"], p["old"]))
        if cur.rowcount != 1:
            raise RuntimeError("target %d was not updated" % p["id"])
        got = cur.execute("SELECT engine FROM vehicles WHERE id=?", (p["id"],)).fetchone()[0]
        if got != p["new"]:
            raise RuntimeError("target %d holds %r, not %r" % (p["id"], got, p["new"]))


def bare_count(cur):
    return cur.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                       "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) "
                       "WHERE source='owner-manual-verified'").fetchone()[0]


def labelled(cur):
    return cur.execute("SELECT COUNT(*) FROM vehicles WHERE engine IS NOT NULL AND engine <> ''").fetchone()[0]


def build(con):
    sys.path.insert(0, os.path.join(ROOT, "files"))
    spec = importlib.util.spec_from_file_location("kyr_build_04", os.path.join(ROOT, "files", "04_rebuild_demo.py"))
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


def mem_copy():
    src = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def rehearse(plan):
    say("")
    say("REHEARSAL -- the real build on two in-memory copies of the database (untouched, and with the plan applied)")
    try:
        m0 = mem_copy()
        before, dtc0, fix0 = build(m0)
        m0.close()
        m1 = mem_copy()
        c1 = m1.cursor()
        n0 = labelled(c1)
        apply(c1, plan)
        m1.commit()
        n1 = labelled(c1)
        if bare_count(c1) != BARE_FROZEN:
            say("  REHEARSAL FAILED: bare owner-manual rows moved")
            return False
        after, dtc1, fix1 = build(m1)
        m1.close()
    except SystemExit as e:
        say("  REHEARSAL FAILED: the build stopped:", e)
        return False
    if sorted(before) != sorted(after) or dtc0 != dtc1 or fix0 != fix1:
        say("  REHEARSAL FAILED: the vehicle list, the code list or the fix list changed")
        return False
    want = {p["id"]: p for p in plan}
    bad = 0
    for vid, a in before.items():
        b = after[vid]
        if vid in want:
            diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            if diff != ["engine"]:
                say("  UNEXPECTED: id %d differs in %s, expected the engine label only" % (vid, diff))
                bad += 1
            elif (a.get("engine"), b.get("engine")) != (want[vid]["old"], want[vid]["new"]):
                say("  UNEXPECTED: id %d ships %r -> %r" % (vid, a.get("engine"), b.get("engine")))
                bad += 1
        elif a != b:
            say("  UNEXPECTED: id %d changed although the plan does not touch it" % vid)
            bad += 1
    if bad:
        return False
    ver = sorted(v for v in want if isinstance(before[v].get("oil"), dict) and before[v]["oil"].get("ver") == 1)
    n_ver = sum(1 for v in after.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    say("  build gates passed on both copies; vehicles %d -> %d; owner's-manual-verified %d (unchanged)" % (len(before), len(after), n_ver))
    say("  %d vehicles differ, each in the engine label only; all other %d vehicles identical" % (len(want), len(after) - len(want)))
    say("  vehicles with a label: %d -> %d; bare owner-manual rows %d" % (n0, n1, BARE_FROZEN))
    say("  verified vehicles among the changed ones: %s" % ver)
    for v in ver:
        p = want[v]
        base = "%d %s %s" % (p["year"], p["make"], p["model"])
        say("    guide input label for id %d: %r -> %r (after `python _gen_guide_specs.py`)" % (v, "%s (%s)" % (base, p["old"]), base + (" (%s)" % p["new"] if p["new"] else "")))
    return True


def dry_run():
    say("ENGINE-LABEL REPAIR -- DRY RUN (nothing is written)  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    pulled_at = datetime.datetime.now().isoformat()
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        if bare_count(cur) != BARE_FROZEN:
            sys.exit("bare owner-manual rows are not %d" % BARE_FROZEN)
        plan = [plan_op(cur, op, pulled_at) for op in OPS]
    finally:
        con.close()
    say("")
    say("SUMMARY")
    say("  labels changed: %d (cleared %d, set to 'Electric' %d)" % (len(plan), sum(1 for p in plan if p["new"] is None), sum(1 for p in plan if p["new"])))
    bad = [r for r in REQUESTS if r[1] != 200]
    say("  EPA requests: %d, answers other than HTTP 200: %d %s" % (len(REQUESTS), len(bad), bad[:5]))
    if not rehearse(plan):
        sys.exit("rehearsal failed -- no plan saved")
    sha = plan_sha(plan)
    with io.open(PLAN_FILE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"script": os.path.basename(__file__), "sha256": sha, "plan": plan}, fh, sort_keys=True, indent=1)
    say("")
    say("plan saved: %s" % PLAN_FILE)
    say("plan sha256: %s" % sha)
    say("to write exactly this plan (only on Robert's go):  python %s --write --sha %s" % (os.path.basename(__file__), sha))


def write():
    if "--sha" not in sys.argv:
        sys.exit("--write needs --sha <the sha256 a dry run printed>")
    want = sys.argv[sys.argv.index("--sha") + 1]
    with io.open(PLAN_FILE, encoding="utf-8") as fh:
        saved = json.load(fh)
    plan = saved["plan"]
    got = plan_sha(plan)
    if got != want or saved.get("sha256") != want:
        sys.exit("plan file hash %s does not match --sha %s: run the dry run again and get a fresh go" % (got, want))
    if [(p["id"], p["year"], p["make"], p["model"], p["old"], p["new"]) for p in plan] != OPS:
        sys.exit("the saved plan does not match this script's operations")
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        bare, fleet, n0 = bare_count(cur), cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0], labelled(cur)
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    bak = "%s.bak_engine_labels_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        apply(cur, plan)
        cleared = sum(1 for p in plan if p["new"] is None)
        if labelled(cur) != n0 - cleared or cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] != fleet:
            raise RuntimeError("label count or fleet count is off")
        if bare_count(cur) != BARE_FROZEN:
            raise RuntimeError("bare owner-manual count moved")
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise
    con.close()
    say("WRITTEN: %d engine labels changed (%d cleared, %d set to 'Electric'); vehicles with a label %d -> %d; fleet %d; bare rows %d"
        % (len(plan), cleared, len(plan) - cleared, n0, n0 - cleared, fleet, BARE_FROZEN))


if __name__ == "__main__":
    if WRITE:
        write()
    else:
        try:
            dry_run()
        except PullError as e:
            say("")
            say("STOPPED -- a pull or a check did not come back clean, so no plan was saved:")
            say("   ", e)
            say("requests so far: %d, non-200: %s" % (len(REQUESTS), [r for r in REQUESTS if r[1] != 200][:8]))
            sys.exit(2)
