"""Fuel-economy repair, part 3: lines that belong to another vehicle on the rows filled by the pull of 2026-06-21,
and an engine size stored as text on fifteen Mazda rows.

Found 2026-11-15. The GMC Sierra 2500 rows carried Sierra 1500 figures. They came from one pull, so every line of
that pull (114 vehicles) was traced to the EPA record it came from. Gasoline lines on a gasoline vehicle look normal,
so no test on the shape of the data could find them; only the trace by origin did.

Rulings (Robert, 2026-11-15, "Accept, start dry run"):
  REMOVE   lines that belong to another vehicle (156 on 19 vehicles):
             GMC Sierra 2500 2019-2022     every line is a Sierra 1500 record; EPA lists no Sierra 2500, so these
                                           rows end with no fuel economy
             Ford Bronco Sport 2021-2023   lines of the full-size Bronco
             Volkswagen Golf GTI 2019-2022 lines of the Golf, Golf R, Alltrack and SportWagen
             Mercedes-Benz GLE 350 2020-23 lines of the E350, GLE450 and GLE580
             Lexus NX 300 2019-2021        the NX 300h line
             Mercedes-Benz GLC 300 2021    the C300 line
  REMOVE   the Veloster N lines from the Hyundai Veloster rows 2019-2021 (4 lines; the Kona N and Ioniq 5 N ruling).
  ENGINE   store the engine size as a plain number where it is stored as text ('2.0L', '2.0L I4'): 77 lines on the
           Mazda3 2005-2017 rows and the MX-5 Miata 2020 / 2021 rows. The page appends 'L' itself, so it printed
           '2.0LL'. No figure changes.
  NOT in scope: hybrid versions under the same nameplate (Avalon Hybrid, MKZ Hybrid); the pulls of May 2026.

Source: EPA fueleconomy.gov only (government). Status-aware: an answer that is not HTTP 200 with a usable body stops
the run. Every line is re-proved in the dry run: a line goes only if it matches a record under a name stated as
another vehicle and matches none of the vehicle's own records; a line that matches neither, or both, stops the run.
When one EPA name fits both a foreign and an own prefix, the longer prefix decides ('Bronco Sport 4WD' is the Bronco
Sport's, 'Veloster N' is not the Veloster's).

    python _repair_fuel_economy_june_batch.py
        DRY RUN. Pulls, prints every line with its verdict, rehearses the real build on in-memory copies of the
        database (before and after), saves the plan and prints its sha256. Writes nothing to wrench_vehicles.db.

    python _repair_fuel_economy_june_batch.py --write --sha <sha256 printed by the dry run>
        Backs up the database, then applies EXACTLY the saved plan (no new pull). Each vehicle is changed only if
        its stored lines still equal what the dry run showed.
"""
import sqlite3, shutil, datetime, sys, os, io, re, json, time, socket, hashlib, importlib.util, contextlib
import urllib.request, urllib.error, urllib.parse
import defusedxml.ElementTree as ET        # hardened parser; fetch_xml() also refuses any document type declaration

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_repair_fuel_economy_june_batch_plan_cache.json")      # gitignored (*_cache.json)
WRITE = "--write" in sys.argv
BARE_FROZEN = 424
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
EPA = "https://www.fueleconomy.gov/ws/rest/vehicle"
PACE = 0.5
Q = urllib.parse.quote
REQUESTS = []
_last = [0.0]
COLS = ("city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, transmission, drive, range_miles, mpge, "
        "fuel_type, range_ev, city_ev, hwy_ev, comb_ev")
CITY, HWY, COMB, COST, ENG, TRANS, DRIVE = range(7)


def rm(vid, year, make, model, own, foreign, out, stay):
    """own / foreign = EPA names or name prefixes; out / stay = lines expected to go / to remain."""
    return dict(id=vid, year=year, make=make, model=model, kind="remove", own=own, foreign=foreign, out=out, stay=stay)


def eng(vid, year, make, model, own, n):
    return dict(id=vid, year=year, make=make, model=model, kind="engine", own=own, foreign=[], out=0, stay=n)


SIERRA = (["Sierra 2500", "Sierra 2500HD", "Sierra 2500 HD"], ["Sierra"])
BRONCO = (["Bronco Sport"], ["Bronco"])
GTI = (["GTI", "Golf GTI"], ["Golf", "Golf-R"])
GLE = (["GLE350"], ["E350", "GLE450", "GLE580"])
NX = (["NX 300"], ["NX 300h"])
VELO = (["Veloster"], ["Veloster N"])
M3 = ["3", "3 4-Door", "3 5-Door", "3 DI 4-Door", "3 DI 5-Door"]
OPS = [
    rm(38664, 2019, "GMC", "Sierra 2500", *SIERRA, 20, 0), rm(38665, 2020, "GMC", "Sierra 2500", *SIERRA, 23, 0),
    rm(38666, 2021, "GMC", "Sierra 2500", *SIERRA, 29, 0), rm(38667, 2022, "GMC", "Sierra 2500", *SIERRA, 25, 0),
    rm(38653, 2021, "Ford", "Bronco Sport", *BRONCO, 8, 2), rm(38654, 2022, "Ford", "Bronco Sport", *BRONCO, 10, 2),
    rm(38655, 2023, "Ford", "Bronco Sport", *BRONCO, 10, 2),
    rm(38630, 2019, "Volkswagen", "Golf GTI", *GTI, 8, 2), rm(38684, 2020, "Volkswagen", "Golf GTI", *GTI, 2, 1),
    rm(38685, 2021, "Volkswagen", "Golf GTI", *GTI, 2, 2), rm(38686, 2022, "Volkswagen", "Golf GTI", *GTI, 2, 2),
    rm(38628, 2020, "Mercedes-Benz", "GLE 350", *GLE, 3, 2), rm(38692, 2021, "Mercedes-Benz", "GLE 350", *GLE, 3, 2),
    rm(38693, 2022, "Mercedes-Benz", "GLE 350", *GLE, 4, 2), rm(38694, 2023, "Mercedes-Benz", "GLE 350", *GLE, 3, 2),
    rm(38629, 2019, "Lexus", "NX 300", *NX, 1, 3), rm(38680, 2020, "Lexus", "NX 300", *NX, 1, 3),
    rm(38681, 2021, "Lexus", "NX 300", *NX, 1, 3),
    rm(38652, 2021, "Mercedes-Benz", "GLC 300", ["GLC300"], ["C300"], 1, 3),
    rm(38641, 2019, "Hyundai", "Veloster", *VELO, 1, 4), rm(38682, 2020, "Hyundai", "Veloster", *VELO, 1, 4),
    rm(38683, 2021, "Hyundai", "Veloster", *VELO, 2, 4),
    eng(12794, 2020, "Mazda", "MX-5 Miata", ["MX-5"], 1), eng(12863, 2021, "Mazda", "MX-5 Miata", ["MX-5"], 1),
    eng(38705, 2005, "Mazda", "Mazda3", M3, 4), eng(38706, 2006, "Mazda", "Mazda3", M3, 4), eng(38707, 2007, "Mazda", "Mazda3", M3, 5),
    eng(38708, 2008, "Mazda", "Mazda3", M3, 4), eng(38709, 2009, "Mazda", "Mazda3", M3, 4), eng(38710, 2010, "Mazda", "Mazda3", M3, 4),
    eng(38711, 2011, "Mazda", "Mazda3", M3, 4), eng(38712, 2012, "Mazda", "Mazda3", M3, 4), eng(38713, 2013, "Mazda", "Mazda3", M3, 4),
    eng(38714, 2014, "Mazda", "Mazda3", M3, 8), eng(38715, 2015, "Mazda", "Mazda3", M3, 10), eng(38716, 2016, "Mazda", "Mazda3", M3, 10),
    eng(38717, 2017, "Mazda", "Mazda3", M3, 10),
]
assert len({o["id"] for o in OPS}) == len(OPS) == 37


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
            out.append({"epa_id": eid, "name": name, "city": num(g("city08")), "hwy": num(g("highway08")), "comb": num(g("comb08")),
                        "displ": g("displ") or None, "trans": g("trany") or None, "drive": g("drive") or None})
        _RECS[k] = out
    return _RECS[k]


def best(name, prefixes):
    """Length of the longest stated name or name prefix that fits this EPA name, or 0."""
    return max([len(p) for p in prefixes if name == p or name.startswith(p + " ")] or [0])


def size(text):
    """The engine size as EPA prints it: the leading number of the stored text ('2.0L I4' -> '2.0')."""
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(text)) if text not in (None, "") else None
    return m.group(1) if m else None


def stored(cur, vid):
    return [list(r) for r in cur.execute("SELECT id, %s FROM fuel_economy WHERE vehicle_id=? ORDER BY id" % COLS, (vid,))]


def fmt(r):
    d = r[1:]
    return "fe#%-5d %2s/%2s/%2s  %-8s %-22s %-27s" % (r[0], d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE])


def plan_op(cur, op, pulled_at):
    vid, year, make, model = op["id"], op["year"], op["make"], op["model"]
    row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
    if not row or tuple(row) != (year, make, model):
        sys.exit("target %d is %r, not %d %s %s" % (vid, row and tuple(row), year, make, model))
    cur_rows = stored(cur, vid)
    names = menu(year, make)
    own_n = sorted(n for n in names if best(n, op["own"]) > best(n, op["foreign"]))
    for_n = sorted(n for n in names if best(n, op["foreign"]) > best(n, op["own"]))
    own_r = [r for n in own_n for r in records(year, make, n)]
    for_r = [r for n in for_n for r in records(year, make, n)]
    p = {"id": vid, "year": year, "make": make, "model": model, "kind": op["kind"], "current": cur_rows, "delete_ids": [], "engine_fix": [],
         "own_names": own_n, "foreign_names": for_n, "sources": [], "empties": False, "pulled_at": pulled_at}
    say("")
    say("[%s] id %d  %d %s %s   (%d stored lines)" % (op["kind"].upper(), vid, year, make, model, len(cur_rows)))
    say("  EPA names of this vehicle : %s" % ("; ".join(own_n) or "NONE (EPA lists %d %s names for %d, none for this vehicle)" % (len(names), make, year)))
    if op["foreign"]:
        say("  EPA names of other vehicles: %s" % "; ".join(for_n)[:200])

    def hit(d, recs):
        return [r for r in recs if (d[CITY], d[HWY], d[COMB], size(d[ENG]), d[TRANS], d[DRIVE]) == (r["city"], r["hwy"], r["comb"], r["displ"], r["trans"], r["drive"])]

    for r in cur_rows:
        d = r[1:]
        o, f = hit(d, own_r), hit(d, for_r)
        if f and not o:
            p["delete_ids"].append(r[0])
            p["sources"].append([r[0], f[0]["name"], f[0]["epa_id"]])
            say("    OUT  " + fmt(r) + " <= %s (EPA %s)" % (f[0]["name"], f[0]["epa_id"]))
        elif o and not f:
            new = size(d[ENG])
            if d[ENG] is not None and str(d[ENG]) != new:
                p["engine_fix"].append([r[0], d[ENG], new])
                say("    FIX  " + fmt(r) + " engine %r -> %r   <= %s" % (d[ENG], new, o[0]["name"]))
            else:
                say("    stay " + fmt(r) + " <= %s" % "; ".join(sorted({x["name"] for x in o}))[:80])
        elif o and f:
            raise PullError("id %d: line fe#%d matches both an own record (%s) and a foreign one (%s) -- needs a ruling" % (vid, r[0], o[0]["name"], f[0]["name"]))
        else:
            raise PullError("id %d: line fe#%d (%s/%s/%s %s %s %s) matches no EPA record -- needs a look" % (vid, r[0], d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE]))
    out, stay = len(p["delete_ids"]), len(cur_rows) - len(p["delete_ids"])
    if (out, stay) != (op["out"], op["stay"]):
        raise PullError("id %d: %d lines to go and %d to stay, expected %d and %d" % (vid, out, stay, op["out"], op["stay"]))
    texty = sum(1 for r in cur_rows if r[1:][ENG] is not None and str(r[1:][ENG]) != size(r[1:][ENG]))
    if op["kind"] == "engine" and (not p["engine_fix"] or len(p["engine_fix"]) != texty):
        raise PullError("id %d: %d engine texts planned, %d lines carry text" % (vid, len(p["engine_fix"]), texty))
    if op["kind"] == "remove" and p["engine_fix"]:
        raise PullError("id %d: unexpected engine text on a removal target" % vid)
    if stay == 0:
        if own_n:
            raise PullError("id %d: every line goes although EPA lists %r for this vehicle -- needs a ruling" % (vid, own_n))
        p["empties"] = True
        say("  after: no fuel-economy line (EPA does not list this vehicle for %d)" % year)
    return p


def plan_sha(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def after_rows(p):
    gone, fix = set(p["delete_ids"]), {f[0]: f[2] for f in p["engine_fix"]}
    out = []
    for r in p["current"]:
        if r[0] in gone:
            continue
        d = list(r[1:])
        if r[0] in fix:
            d[ENG] = fix[r[0]]
        out.append(d)
    return out


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
        for fid, old, new in p["engine_fix"]:
            cur.execute("UPDATE fuel_economy SET engine=? WHERE id=? AND vehicle_id=? AND engine=?", (new, fid, vid, old))
            if cur.rowcount != 1:
                raise RuntimeError("target %d: line fe#%d was not updated" % (vid, fid))
        if p["empties"]:
            cur.execute("INSERT OR REPLACE INTO pull_log (vehicle_id, endpoint, status, pulled_at) VALUES (?,?,?,?)", (vid, "fuel-economy", "empty", p["pulled_at"]))
        if [r[1:] for r in stored(cur, vid)] != after_rows(p):
            raise RuntimeError("target %d does not hold the planned lines" % vid)


def bare_count(cur):
    return cur.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                       "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) "
                       "WHERE source='owner-manual-verified'").fetchone()[0]


def totals(plan):
    return sum(len(p["delete_ids"]) for p in plan), sum(len(p["engine_fix"]) for p in plan)


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
        out, fixed = totals(plan)
        n1 = c1.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        if n1 != n0 - out or bare_count(c1) != BARE_FROZEN:
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
        if p["empties"] != (not mpg):
            say("  UNEXPECTED: id %d ships %d lines" % (vid, len(mpg)))
            bad += 1
        if len(mpg) != len(p["current"]) - len(p["delete_ids"]):
            say("  UNEXPECTED: id %d ships %d lines, planned %d" % (vid, len(mpg), len(p["current"]) - len(p["delete_ids"])))
            bad += 1
    odd = sum(1 for v in after.values() for m in v.get("mpg") or [] if m.get("eng") and not re.fullmatch(r"\d+(\.\d+)?", str(m["eng"])))
    if odd:
        say("  UNEXPECTED: %d shipped lines still carry an engine that is not a plain number" % odd)
        bad += 1
    if bad:
        return False
    ver = sorted(v for v in want if isinstance(before[v].get("oil"), dict) and before[v]["oil"].get("ver") == 1)
    n_ver = sum(1 for v in after.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    say("  build gates passed on both copies; vehicles %d -> %d; owner's-manual-verified %d (unchanged)" % (len(before), len(after), n_ver))
    say("  %d vehicles differ, each in fuel economy only; all other %d vehicles identical" % (len(want), len(after) - len(want)))
    say("  fuel-economy rows %d -> %d (%d out, %d engine texts fixed); bare owner-manual rows %d" % (n0, n1, out, fixed, BARE_FROZEN))
    say("  shipped lines whose engine is not a plain number: 0; vehicles left without fuel economy: %s" % sorted(v for v, p in want.items() if p["empties"]))
    say("  verified vehicles among the changed ones (%d): %s" % (len(ver), ver))
    return True


def dry_run():
    say("FUEL-ECONOMY JUNE-BATCH REPAIR -- DRY RUN (nothing is written)  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
    for kind, label in (("remove", "lines of another vehicle removed"), ("engine", "engine text made a plain number")):
        ps = [p for p in plan if p["kind"] == kind]
        say("  %-34s %2d vehicles: %3d lines out, %3d engine texts fixed, %3d lines untouched" % (
            label, len(ps), sum(len(p["delete_ids"]) for p in ps), sum(len(p["engine_fix"]) for p in ps),
            sum(len(p["current"]) - len(p["delete_ids"]) - len(p["engine_fix"]) for p in ps)))
    out, fixed = totals(plan)
    say("  %-34s %2d vehicles: %3d lines out, %3d engine texts fixed" % ("total", len(plan), out, fixed))
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
    if [(p["id"], p["year"], p["make"], p["model"], p["kind"]) for p in plan] != [(o["id"], o["year"], o["make"], o["model"], o["kind"]) for o in OPS]:
        sys.exit("the saved plan does not match this script's operations")
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        bare, fleet, n0 = bare_count(cur), cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0], cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    bak = "%s.bak_fe_june_batch_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    out, fixed = totals(plan)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        apply(cur, plan)
        n1 = cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        if n1 != n0 - out or cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] != fleet:
            raise RuntimeError("row count or fleet count is off")
        if bare_count(cur) != BARE_FROZEN:
            raise RuntimeError("bare owner-manual count moved")
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise
    con.close()
    say("WRITTEN: %d vehicles changed (%d lines out, %d engine texts fixed); fuel-economy rows %d -> %d; fleet %d; bare rows %d"
        % (len(plan), out, fixed, n0, n1, fleet, BARE_FROZEN))


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
