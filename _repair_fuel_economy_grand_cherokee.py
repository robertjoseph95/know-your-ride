"""Fuel-economy repair, part 6: Jeep Grand Cherokee rows that lack their own EPA lines.

Found 2026-11-15 while removing the Grand Cherokee L lines (part 5). The pull of May 2026 stored only part of what EPA
lists for the two-row Grand Cherokee:
  2021 and 2022   one 5.7L line each; the 3.6L lines were never stored
  2023            the two 3.6L lines; the 5.7L line was never stored
  2024            ONE line, and it is the Grand Cherokee L's 5.7L line - EPA lists no 5.7L two-row Grand Cherokee for 2024
A removal cannot fix a row that is missing lines, so these rows are REPLACED from EPA's own records.

Ruling (Robert, 2026-11-15, "Yes, start dry run" to "Start a dry run to re-pull the three Grand Cherokee rows?"):
re-pull 2021, 2022 and 2024 from the plain names only. The 2023 row was found with the same defect while preparing this
and was shown to him in the dry run as a fourth row. He then said "Go, write" for all four rows.

Names TAKEN for every year:    Grand Cherokee 2WD, Grand Cherokee 4WD
Names LEFT OUT, by ruling or because their kind is not ruled:
    Grand Cherokee L ...          the longer body, a vehicle of its own (ruled out, part 5)
    Grand Cherokee WK ...         the previous generation sold beside the new one in 2022 (the 1500 Classic ruling)
    Grand Cherokee SRT / Trackhawk    performance versions (not ruled); none is stored on these rows today
    Grand Cherokee 4xe            the plug-in hybrid (not ruled); none is stored on these rows today
The 2025 and 2026 rows are not touched: 2025 already holds exactly its plain records, and 2026 holds a 4xe line and two
lines that match no current EPA record, which a replace would drop without a ruling.

Each row is rebuilt as one line per distinct EPA record under the taken names (the rule of part 1). Every line stored
today must either come back (same six fields: city, highway, combined, engine size, transmission, drive) or be proved
a Grand Cherokee L record; anything else stops the run. A line that comes back takes EPA's current yearly fuel cost.

Source: EPA fueleconomy.gov only (government). Status-aware: an answer that is not HTTP 200 with a usable body stops the run.

    python _repair_fuel_economy_grand_cherokee.py
        DRY RUN. Pulls, prints every line out and in, rehearses the real build on in-memory copies of the database
        (before and after), saves the plan and prints its sha256. Writes nothing to wrench_vehicles.db.

    python _repair_fuel_economy_grand_cherokee.py --write --sha <sha256 printed by the dry run>
        Backs up the database, then applies EXACTLY the saved plan (no new pull). Each vehicle is changed only if
        its stored lines still equal what the dry run showed.
"""
import sqlite3, shutil, datetime, sys, os, io, re, json, time, socket, hashlib, importlib.util, contextlib
import urllib.request, urllib.error, urllib.parse
import defusedxml.ElementTree as ET        # hardened parser; fetch_xml() also refuses any document type declaration

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_repair_fuel_economy_grand_cherokee_plan_cache.json")      # gitignored (*_cache.json)
WRITE = "--write" in sys.argv
BARE_FROZEN = 424
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
EPA = "https://www.fueleconomy.gov/ws/rest/vehicle"
PACE = 0.5
Q = urllib.parse.quote
REQUESTS = []
_last = [0.0]
ELECTRIFIED = ("EV", "FCV", "Plug-in Hybrid")
COLS = ("city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, transmission, drive, range_miles, mpge, "
        "fuel_type, range_ev, city_ev, hwy_ev, comb_ev")
CITY, HWY, COMB, COST, ENG, TRANS, DRIVE, RANGE, MPGE, FTYPE = range(10)
MAKE, MODEL = "Jeep", "Grand Cherokee"
KEEP = ["Grand Cherokee 2WD", "Grand Cherokee 4WD"]
LONGER = ["Grand Cherokee L"]                                          # the only names a stored line may be lost to
IGNORE = LONGER + ["Grand Cherokee WK", "Grand Cherokee SRT", "Grand Cherokee Trackhawk", "Grand Cherokee 4xe"]


def rp(vid, year, out, inn, back, lost, asked):
    """out / inn = lines expected to go / to be written; back = stored lines that return; lost = stored lines of the longer body."""
    return dict(id=vid, year=year, out=out, inn=inn, back=back, lost=lost, asked=asked)


OPS = [
    rp(12857, 2021, 1, 3, 1, 0, True),
    rp(12922, 2022, 1, 3, 1, 0, True),
    rp(13053, 2024, 1, 2, 0, 1, True),
    rp(12987, 2023, 2, 3, 2, 0, False),          # not one of the three rows asked for: same defect, found while preparing
]
assert len({o["id"] for o in OPS}) == len(OPS) == 4


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


_MENU, _RECS = {}, {}


def menu(year, make):
    if (year, make) not in _MENU:
        root = fetch_xml("%s/menu/model?year=%d&make=%s" % (EPA, year, Q(make)), "EPA models %d %s" % (year, make))
        names = [(mi.findtext("text") or "").strip() for mi in root.iter("menuItem")]
        if not names:
            raise PullError("EPA models %d %s: HTTP 200 but no model list" % (year, make))
        _MENU[(year, make)] = names
    return _MENU[(year, make)]


def num(x):
    try:
        return int(float(x)) if x != "" else None
    except ValueError:
        return None


def records(year, make, name):
    k = (year, make, name)
    if k not in _RECS:
        root = fetch_xml("%s/menu/options?year=%d&make=%s&model=%s" % (EPA, year, Q(make), Q(name)), "EPA options %d %s %s" % (year, make, name))
        ids = [(mi.findtext("value") or "").strip() for mi in root.iter("menuItem")]
        if not ids or not all(i.isdigit() for i in ids):
            raise PullError("EPA options %d %s %s: HTTP 200 but no usable option list" % (year, make, name))
        out = []
        for eid in ids:
            v = fetch_xml("%s/%s" % (EPA, eid), "EPA vehicle %s" % eid)
            g = lambda f: (v.findtext(f) or "").strip()
            if (g("year"), g("make"), g("model")) != (str(year), make, name):
                raise PullError("EPA vehicle %s is %s %s %s, not %d %s %s" % (eid, g("year"), g("make"), g("model"), year, make, name))
            city, hwy, comb = num(g("city08")), num(g("highway08")), num(g("comb08"))
            if city is None or hwy is None or comb is None:
                raise PullError("EPA vehicle %s: no city / highway / combined figure" % eid)
            out.append({"epa_id": eid, "name": name, "atv": g("atvType"), "city": city, "hwy": hwy, "comb": comb, "cost": num(g("fuelCost08")),
                        "displ": g("displ") or None, "trans": g("trany") or None, "drive": g("drive") or None, "fuel": g("fuelType") or None})
        _RECS[k] = out
    return _RECS[k]


def pref(name, prefixes):
    return any(name == p or name.startswith(p + " ") for p in prefixes)


def fnum(text):
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(text)) if text not in (None, "") else None
    return float(m.group(1)) if m else None


def stored(cur, vid):
    return [list(r) for r in cur.execute("SELECT id, %s FROM fuel_economy WHERE vehicle_id=? ORDER BY id" % COLS, (vid,))]


def gas_row(rec):
    return [rec["city"], rec["hwy"], rec["comb"], rec["cost"], rec["displ"], rec["trans"], rec["drive"], None, None,
            rec["fuel"], None, None, None, None]


def key_line(d):
    return (d[CITY], d[HWY], d[COMB], fnum(d[ENG]), d[TRANS], d[DRIVE])


def key_rec(r):
    return (r["city"], r["hwy"], r["comb"], fnum(r["displ"]), r["trans"], r["drive"])


def fmt(d):
    return "%2s/%2s/%2s  %-4s %-16s %-17s cost %-5s fuel %s" % (d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE], d[COST], d[FTYPE])


def plan_op(cur, op, pulled_at):
    vid, year = op["id"], op["year"]
    row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
    if not row or tuple(row) != (year, MAKE, MODEL):
        sys.exit("target %d is %r, not %d %s %s" % (vid, row and tuple(row), year, MAKE, MODEL))
    cur_rows = stored(cur, vid)
    if not cur_rows:
        sys.exit("target %d holds no fuel-economy line" % vid)
    near = sorted(n for n in menu(year, MAKE) if pref(n, [MODEL]))
    missing = [n for n in KEEP if n not in near]
    if missing:
        raise PullError("%d: EPA does not list %r -- needs a ruling" % (year, missing))
    stray = [n for n in near if n not in KEEP and not pref(n, IGNORE)]
    if stray:
        raise PullError("%d: EPA lists %r, which this repair neither takes nor leaves out -- needs a ruling" % (year, stray))
    say("")
    say("[REPLACE%s] id %d  %d %s %s   (%d stored line%s)" % ("" if op["asked"] else " - NOT ONE OF THE THREE ROWS ASKED FOR", vid, year, MAKE, MODEL,
                                                             len(cur_rows), "" if len(cur_rows) == 1 else "s"))
    say("  taken   : %s" % "; ".join(KEEP))
    say("  left out: %s" % ("; ".join(n for n in near if n not in KEEP) or "nothing"))
    new, seen = [], set()
    for name in KEEP:
        for rec in records(year, MAKE, name):
            if rec["atv"] in ELECTRIFIED:
                raise PullError("EPA vehicle %s under %r is typed %s -- a taken name must not be electrified" % (rec["epa_id"], name, rec["atv"]))
            if rec["displ"] is None or rec["trans"] is None or rec["drive"] is None:
                raise PullError("EPA vehicle %s under %r lacks an engine size, a transmission or a drive" % (rec["epa_id"], name))
            if key_rec(rec) in seen:
                continue
            seen.add(key_rec(rec))
            new.append((gas_row(rec), rec))
    longer = [r for n in near if pref(n, LONGER) for r in records(year, MAKE, n)]
    back, lost, notes = [], [], {}
    for r in cur_rows:
        d = r[1:]
        mine = [x for x, _ in new if key_line(x) == key_line(d)]
        if mine:
            back.append(r[0])
            notes[r[0]] = "comes back" + ("" if mine[0][COST] == d[COST] else " (yearly cost %s -> %s)" % (d[COST], mine[0][COST]))
            continue
        theirs = [x for x in longer if key_rec(x) == key_line(d)]
        if not theirs:
            raise PullError("id %d: stored line fe#%d (%s) is neither a record of the taken names nor a Grand Cherokee L record -- needs a look" % (vid, r[0], fmt(d)))
        lost.append(r[0])
        notes[r[0]] = "does not come back: it is a record of %s (EPA %s)" % (theirs[0]["name"], theirs[0]["epa_id"])
    say("  OUT (%d):" % len(cur_rows))
    for r in cur_rows:
        say("    fe#%-5d %s   %s" % (r[0], fmt(r[1:]), notes[r[0]]))
    say("  IN (%d):" % len(new))
    stored_keys = {key_line(r[1:]) for r in cur_rows}
    for x, rec in new:
        say("            %s   <- %s (EPA %s)%s" % (fmt(x), rec["name"], rec["epa_id"], "" if key_line(x) in stored_keys else "   NEW"))
    got = (len(cur_rows), len(new), len(back), len(lost))
    if got != (op["out"], op["inn"], op["back"], op["lost"]):
        raise PullError("id %d: out / in / back / lost = %r, expected %r" % (vid, got, (op["out"], op["inn"], op["back"], op["lost"])))
    return {"id": vid, "year": year, "make": MAKE, "model": MODEL, "asked": op["asked"], "current": cur_rows, "delete_ids": [r[0] for r in cur_rows],
            "insert": [x for x, _ in new], "sources": [[rec["name"], rec["epa_id"]] for _, rec in new], "back_ids": back, "lost_ids": lost,
            "taken": KEEP, "left_out": [n for n in near if n not in KEEP], "pulled_at": pulled_at}


def plan_sha(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def after_rows(p):
    return [list(x) for x in p["insert"]]


def apply(cur, plan):
    for p in plan:
        vid = p["id"]
        row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        if not row or tuple(row) != (p["year"], p["make"], p["model"]):
            raise RuntimeError("target %d is %r" % (vid, row and tuple(row)))
        if stored(cur, vid) != p["current"]:
            raise RuntimeError("target %d: the stored fuel-economy lines changed since the dry run" % vid)
        for fid in p["delete_ids"]:
            cur.execute("DELETE FROM fuel_economy WHERE id=? AND vehicle_id=?", (fid, vid))
            if cur.rowcount != 1:
                raise RuntimeError("target %d: line fe#%d was not deleted" % (vid, fid))
        cur.executemany("INSERT INTO fuel_economy (vehicle_id, " + COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [[vid] + list(x) for x in p["insert"]])
        cur.execute("INSERT OR REPLACE INTO pull_log (vehicle_id, endpoint, status, pulled_at) VALUES (?,?,?,?)", (vid, "fuel-economy", "ok", p["pulled_at"]))
        if [r[1:] for r in stored(cur, vid)] != after_rows(p):
            raise RuntimeError("target %d does not hold the planned lines" % vid)


def bare_count(cur):
    return cur.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                       "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) "
                       "WHERE source='owner-manual-verified'").fetchone()[0]


def totals(plan):
    return sum(len(p["delete_ids"]) for p in plan), sum(len(p["insert"]) for p in plan)


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
        n0 = c1.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        apply(c1, plan)
        m1.commit()
        out, inn = totals(plan)
        n1 = c1.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        if n1 != n0 - out + inn or bare_count(c1) != BARE_FROZEN:
            say("  REHEARSAL FAILED: row count or bare rows are off")
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
            if diff != ["mpg"]:
                say("  UNEXPECTED: id %d differs in %s, expected fuel economy only" % (vid, diff))
                bad += 1
        elif a != b:
            say("  UNEXPECTED: id %d changed although the plan does not touch it" % vid)
            bad += 1
    for vid, p in want.items():
        mpg = after[vid].get("mpg") or []
        if len(mpg) != len(p["insert"]):
            say("  UNEXPECTED: id %d ships %d lines, planned %d" % (vid, len(mpg), len(p["insert"])))
            bad += 1
        for m, x in zip(mpg, p["insert"]):
            ok = (m.get("city"), m.get("hwy"), m.get("comb"), m.get("trans"), m.get("drive")) == (x[CITY], x[HWY], x[COMB], x[TRANS], x[DRIVE])
            if not ok or fnum(m.get("eng")) != fnum(x[ENG]) or m.get("mpge") or m.get("range"):
                say("  UNEXPECTED shipped line on id %d: %r" % (vid, m))
                bad += 1
    if bad:
        return False
    n_ver = sum(1 for v in after.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    ver = sorted(v for v in want if isinstance(before[v].get("oil"), dict) and before[v]["oil"].get("ver") == 1)
    say("  build gates passed on both copies; vehicles %d -> %d; owner's-manual-verified %d (unchanged)" % (len(before), len(after), n_ver))
    say("  %d vehicles differ, each in fuel economy only; all other %d vehicles identical" % (len(want), len(after) - len(want)))
    say("  fuel-economy rows %d -> %d (%d out, %d in); bare owner-manual rows %d" % (n0, n1, out, inn, BARE_FROZEN))
    say("  every shipped line on the changed vehicles equals a planned line; verified vehicles among them: %s" % ver)
    return True


def dry_run():
    say("FUEL-ECONOMY GRAND CHEROKEE RE-PULL -- DRY RUN (nothing is written)  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
    for p in plan:
        say("  %d %s %s (id %d)%s: %d line%s out, %d in; %d come back, %d new, %d not coming back" % (
            p["year"], p["make"], p["model"], p["id"], "" if p["asked"] else " [fourth row, not asked for]", len(p["delete_ids"]),
            "" if len(p["delete_ids"]) == 1 else "s", len(p["insert"]), len(p["back_ids"]), len(p["insert"]) - len(p["back_ids"]), len(p["lost_ids"])))
    out, inn = totals(plan)
    say("  total: %d vehicles, %d lines out, %d lines in" % (len(plan), out, inn))
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
    if [(p["id"], p["year"]) for p in plan] != [(o["id"], o["year"]) for o in OPS]:
        sys.exit("the saved plan does not match this script's operations")
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        bare, fleet, n0 = bare_count(cur), cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0], cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    bak = "%s.bak_fe_grand_cherokee_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    out, inn = totals(plan)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        apply(cur, plan)
        n1 = cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        if n1 != n0 - out + inn or cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] != fleet:
            raise RuntimeError("row count or fleet count is off")
        if bare_count(cur) != BARE_FROZEN:
            raise RuntimeError("bare owner-manual count moved")
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise
    con.close()
    say("WRITTEN: %d vehicles replaced (%d lines out, %d in); fuel-economy rows %d -> %d; fleet %d; bare rows %d" % (len(plan), out, inn, n0, n1, fleet, BARE_FROZEN))


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
