"""Fuel-economy repair, part 5: lines of a longer-body version stored on the standard vehicle's row.

Found by the name sweep of 2026-11-15. The pulls of May 2026 (and part of the 2026-06-21 batch) took every EPA model
name that starts with the nameplate. So the Yukon row collected the Yukon XL's lines, the Grand Cherokee row the
Grand Cherokee L's and the RX 350 row the RX 350 L's. The fleet keeps long-body versions as vehicles of their own
(Escalade ESV, Navigator L), so these lines belong to another vehicle. Where the long body has the same figures as the
standard one, the row stored each line twice and the page repeated rows.

Ruling (Robert, 2026-11-15, "Yes, start dry run" to "Start a dry run to remove the longer-body lines next?"): the lines
of a longer-body version come out. He then said "Go, write" for the plan as shown (26 vehicles, 87 lines).

Scope (26 vehicles, 87 lines):
      GMC Yukon 2002, 2020-2022, 2024-2026     Yukon XL lines (most are identical copies)
      Jeep Grand Cherokee 2021-2023, 2025-26   Grand Cherokee L lines
      Lexus RX 350 2018-2022                   RX 350 L lines
      Chevrolet TrailBlazer 2002-2004          TrailBlazer EXT lines
      GMC Envoy 2003 / 2004                    Envoy XL lines
      Ford Expedition 2020 / 2021              Expedition MAX lines
      Bentley Bentayga 2026, Rolls-Royce Ghost 2021   extended-wheelbase (EWB) copies
NOT in scope:
      a different body STYLE under a suffixed name (A4 / A6 allroad, Malibu Maxx, Jetta SportWagen, V70 XC, Wrangler
      Unlimited, Transit Connect Wagon LWB): 13 vehicles, 19 lines. A wagon or a four-door is not a longer body; these
      wait for a ruling of their own.
      Jeep Grand Cherokee 2024 (id 13053): its only stored line is a Grand Cherokee L line. Removing it would leave the
      row empty although EPA lists the Grand Cherokee, so it needs a re-pull, not a removal.
      Performance versions and hybrid versions.

A line goes in one of two ways, and each is re-proved here against a fresh EPA pull:
  only   its six fields (city, highway, combined, engine size, transmission, drive) equal a record under a name stated
         as the longer body and no record under the vehicle's own names;
  copy   its six fields equal BOTH an own record and a record of the longer body, and the vehicle stores more identical
         lines than it has own records with those figures. The surplus copies go; as many lines stay as the vehicle
         has own records. Copies must be identical in every stored column.
When one EPA name fits both prefixes, the longer prefix decides ('Yukon XL 2WD' is not the Yukon's). A line that
matches neither side is left alone and counted. The expected number of lines out and left is pinned per vehicle; any
difference stops the run.

Source: EPA fueleconomy.gov only (government). Status-aware: an answer that is not HTTP 200 with a usable body stops the run.

    python _repair_fuel_economy_longer_bodies.py
        DRY RUN. Pulls, prints every line with its verdict, rehearses the real build on in-memory copies of the
        database (before and after), saves the plan and prints its sha256. Writes nothing to wrench_vehicles.db.

    python _repair_fuel_economy_longer_bodies.py --write --sha <sha256 printed by the dry run>
        Backs up the database, then applies EXACTLY the saved plan (no new pull). Each vehicle is changed only if
        its stored lines still equal what the dry run showed.
"""
import sqlite3, shutil, datetime, sys, os, io, re, json, time, socket, hashlib, importlib.util, contextlib, collections
import urllib.request, urllib.error, urllib.parse
import defusedxml.ElementTree as ET        # hardened parser; fetch_xml() also refuses any document type declaration

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_repair_fuel_economy_longer_bodies_plan_cache.json")      # gitignored (*_cache.json)
WRITE = "--write" in sys.argv
BARE_FROZEN = 424
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
EPA = "https://www.fueleconomy.gov/ws/rest/vehicle"
EPA_MAKE = {"RAM": "Ram"}                  # EPA's own spelling of a make, where it differs from the fleet's
PACE = 0.5
Q = urllib.parse.quote
REQUESTS = []
_last = [0.0]
COLS = ("city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, transmission, drive, range_miles, mpge, "
        "fuel_type, range_ev, city_ev, hwy_ev, comb_ev")
CITY, HWY, COMB, COST, ENG, TRANS, DRIVE = range(7)
GROUPS = (("longer", "lines of a longer-body version"),)


def rm(group, vid, year, make, model, own, foreign, out, stay):
    """own / foreign = EPA names or name prefixes; out / stay = lines expected to go / to remain."""
    return dict(id=vid, year=year, make=make, model=model, group=group, own=own, foreign=foreign, out=out, stay=stay)


YUKON = (["Yukon"], ["Yukon XL", "Yukon Denali XL", "Yukon C1500 XL", "Yukon K1500 XL"])
GC = (["Grand Cherokee"], ["Grand Cherokee L"])
RX = (["RX 350"], ["RX 350 L"])
TB = (["TrailBlazer"], ["TrailBlazer Ext"])
ENVOY = (["Envoy"], ["Envoy XL"])
EXPED = (["Expedition"], ["Expedition MAX"])
L = "longer"
OPS = [
    rm(L, 15182, 2002, "GMC", "Yukon", *YUKON, 1, 7), rm(L, 313, 2020, "GMC", "Yukon", *YUKON, 6, 6),
    rm(L, 1811, 2021, "GMC", "Yukon", *YUKON, 10, 10), rm(L, 3322, 2022, "GMC", "Yukon", *YUKON, 10, 10),
    rm(L, 6459, 2024, "GMC", "Yukon", *YUKON, 6, 6), rm(L, 8047, 2025, "GMC", "Yukon", *YUKON, 6, 6),
    rm(L, 9683, 2026, "GMC", "Yukon", *YUKON, 6, 6),
    rm(L, 12857, 2021, "Jeep", "Grand Cherokee", *GC, 1, 1), rm(L, 12922, 2022, "Jeep", "Grand Cherokee", *GC, 1, 1),
    rm(L, 12987, 2023, "Jeep", "Grand Cherokee", *GC, 2, 2), rm(L, 13119, 2025, "Jeep", "Grand Cherokee", *GC, 2, 2),
    rm(L, 13184, 2026, "Jeep", "Grand Cherokee", *GC, 2, 7),
    rm(L, 38595, 2018, "Lexus", "RX 350", *RX, 2, 2), rm(L, 38596, 2019, "Lexus", "RX 350", *RX, 2, 2),
    rm(L, 38597, 2020, "Lexus", "RX 350", *RX, 2, 2), rm(L, 38598, 2021, "Lexus", "RX 350", *RX, 2, 2),
    rm(L, 38599, 2022, "Lexus", "RX 350", *RX, 2, 2),
    rm(L, 15142, 2002, "Chevrolet", "TrailBlazer", *TB, 2, 2), rm(L, 16087, 2003, "Chevrolet", "TrailBlazer", *TB, 4, 2),
    rm(L, 17055, 2004, "Chevrolet", "TrailBlazer", *TB, 4, 2),
    rm(L, 16131, 2003, "GMC", "Envoy", *ENVOY, 4, 2), rm(L, 17103, 2004, "GMC", "Envoy", *ENVOY, 4, 2),
    rm(L, 191, 2020, "Ford", "Expedition", *EXPED, 2, 2), rm(L, 1689, 2021, "Ford", "Expedition", *EXPED, 2, 2),
    rm(L, 10299, 2026, "Bentley", "Bentayga", ["Bentayga"], ["Bentayga EWB"], 1, 2),
    rm(L, 1518, 2021, "Rolls-Royce", "Ghost", ["Ghost"], ["Ghost EWB", "Ghost Extended"], 1, 1),
]
assert len({o["id"] for o in OPS}) == len(OPS) == 26 and sum(o["out"] for o in OPS) == 87


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


def fnum(text):
    """The engine size as a number: the leading number of the stored text or of EPA's displacement."""
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(text)) if text not in (None, "") else None
    return float(m.group(1)) if m else None


def stored(cur, vid):
    return [list(r) for r in cur.execute("SELECT id, %s FROM fuel_economy WHERE vehicle_id=? ORDER BY id" % COLS, (vid,))]


def fmt(r):
    d = r[1:]
    return "fe#%-5d %2s/%2s/%2s  %-5s %-32s %-27s" % (r[0], d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE])


def key_line(d):
    return (d[CITY], d[HWY], d[COMB], fnum(d[ENG]), d[TRANS], d[DRIVE])


def key_rec(r):
    return (r["city"], r["hwy"], r["comb"], fnum(r["displ"]), r["trans"], r["drive"])


def plan_op(cur, op, pulled_at):
    vid, year, make, model = op["id"], op["year"], op["make"], op["model"]
    row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
    if not row or tuple(row) != (year, make, model):
        sys.exit("target %d is %r, not %d %s %s" % (vid, row and tuple(row), year, make, model))
    cur_rows = stored(cur, vid)
    emake = EPA_MAKE.get(make, make)
    names = menu(year, emake)
    own_n = sorted(n for n in names if best(n, op["own"]) > best(n, op["foreign"]))
    for_n = sorted(n for n in names if best(n, op["foreign"]) > best(n, op["own"]))
    if not for_n:
        raise PullError("id %d: EPA lists none of the other names %r for %d %s" % (vid, op["foreign"], year, emake))
    own_r = [r for n in own_n for r in records(year, emake, n)]
    for_r = [r for n in for_n for r in records(year, emake, n)]
    p = {"id": vid, "year": year, "make": make, "model": model, "group": op["group"], "current": cur_rows, "delete_ids": [],
         "own_names": own_n, "foreign_names": for_n, "sources": [], "empties": False, "pulled_at": pulled_at}
    say("")
    say("[%s] id %d  %d %s %s   (%d stored lines)" % (op["group"].upper(), vid, year, make, model, len(cur_rows)))
    say("  EPA names of this vehicle  : %s" % ("; ".join(own_n)[:220] or "NONE (EPA lists %d %s names for %d, none for this vehicle)" % (len(names), emake, year)))
    say("  EPA names of the longer body: %s" % "; ".join(for_n)[:220])
    groups = collections.OrderedDict()
    for r in cur_rows:
        groups.setdefault(key_line(r[1:]), []).append(r)
    verdict, nomatch = {}, 0
    for k, g in groups.items():
        o = [r for r in own_r if key_rec(r) == k]
        f = [r for r in for_r if key_rec(r) == k]
        src = "; ".join(sorted({x["name"] for x in f}))[:70]
        if f and not o:
            for r in g:
                verdict[r[0]] = ("OUT ", "<= %s (EPA %s)" % (src, f[0]["epa_id"]), "only", f[0])
        elif f and o:
            extra = min(max(0, len(g) - len(o)), len(f))
            if extra and len({tuple(r[1:]) for r in g}) != 1:
                raise PullError("id %d: the identical-figure lines %s differ in another column -- needs a look" % (vid, [r[0] for r in g]))
            keep = len(g) - extra
            for i, r in enumerate(g):
                if i < keep:
                    verdict[r[0]] = ("stay", "<= %s (same figures also under %s)" % ("; ".join(sorted({x["name"] for x in o}))[:50], src), None, None)
                else:
                    verdict[r[0]] = ("OUT ", "copy: %d identical lines stored, %d own record%s <= %s (EPA %s)" %
                                     (len(g), len(o), "" if len(o) == 1 else "s", src, f[0]["epa_id"]), "copy", f[0])
        elif o:
            for r in g:
                verdict[r[0]] = ("stay", "<= %s" % "; ".join(sorted({x["name"] for x in o}))[:80], None, None)
        else:
            nomatch += len(g)
            for r in g:
                verdict[r[0]] = ("stay", "?? matches no EPA record under these names (not judged here)", None, None)
    for r in cur_rows:
        tag, why, how, rec = verdict[r[0]]
        say("    %s " % tag + fmt(r) + " " + why)
        if how:
            p["delete_ids"].append(r[0])
            p["sources"].append([r[0], rec["name"], rec["epa_id"], how])
    p["nomatch"] = nomatch
    out, stay = len(p["delete_ids"]), len(cur_rows) - len(p["delete_ids"])
    if (out, stay) != (op["out"], op["stay"]):
        raise PullError("id %d: %d lines to go and %d to stay, expected %d and %d" % (vid, out, stay, op["out"], op["stay"]))
    if stay == 0:
        if own_n:
            raise PullError("id %d: every line goes although EPA lists %r for this vehicle -- needs a ruling" % (vid, own_n))
        p["empties"] = True
        say("  after: no fuel-economy line (EPA does not list this vehicle for %d)" % year)
    return p


def plan_sha(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def after_rows(p):
    gone = set(p["delete_ids"])
    return [list(r[1:]) for r in p["current"] if r[0] not in gone]


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
        if p["empties"]:
            cur.execute("INSERT OR REPLACE INTO pull_log (vehicle_id, endpoint, status, pulled_at) VALUES (?,?,?,?)", (vid, "fuel-economy", "empty", p["pulled_at"]))
        if [r[1:] for r in stored(cur, vid)] != after_rows(p):
            raise RuntimeError("target %d does not hold the planned lines" % vid)


def bare_count(cur):
    return cur.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                       "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) "
                       "WHERE source='owner-manual-verified'").fetchone()[0]


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
        out = sum(len(p["delete_ids"]) for p in plan)
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
    if bad:
        return False
    ver = sorted(v for v in want if isinstance(before[v].get("oil"), dict) and before[v]["oil"].get("ver") == 1)
    n_ver = sum(1 for v in after.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    say("  build gates passed on both copies; vehicles %d -> %d; owner's-manual-verified %d (unchanged)" % (len(before), len(after), n_ver))
    say("  %d vehicles differ, each in fuel economy only; all other %d vehicles identical" % (len(want), len(after) - len(want)))
    say("  fuel-economy rows %d -> %d (%d out); bare owner-manual rows %d" % (n0, n1, out, BARE_FROZEN))
    say("  vehicles left without fuel economy: %s" % sorted(v for v, p in want.items() if p["empties"]))
    say("  verified vehicles among the changed ones (%d): %s" % (len(ver), ver))
    return True


def dry_run():
    say("FUEL-ECONOMY LONGER-BODY REPAIR -- DRY RUN (nothing is written)  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
    for g, label in GROUPS:
        ps = [p for p in plan if p["group"] == g]
        say("  %-36s %2d vehicles: %3d lines out (%d match only the other name, %d surplus copies), %3d lines left" % (
            label, len(ps), sum(len(p["delete_ids"]) for p in ps), sum(1 for p in ps for s in p["sources"] if s[3] == "only"),
            sum(1 for p in ps for s in p["sources"] if s[3] == "copy"), sum(len(p["current"]) - len(p["delete_ids"]) for p in ps)))
    say("  %-36s %2d vehicles: %3d lines out, %3d lines left" % ("total", len(plan), sum(len(p["delete_ids"]) for p in plan),
                                                                 sum(len(p["current"]) - len(p["delete_ids"]) for p in plan)))
    say("  lines left that match no EPA record under these names (not judged here): %d on vehicles %s" % (
        sum(p["nomatch"] for p in plan), sorted(p["id"] for p in plan if p["nomatch"])))
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
    if [(p["id"], p["year"], p["make"], p["model"], p["group"]) for p in plan] != [(o["id"], o["year"], o["make"], o["model"], o["group"]) for o in OPS]:
        sys.exit("the saved plan does not match this script's operations")
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        bare, fleet, n0 = bare_count(cur), cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0], cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    bak = "%s.bak_fe_longer_bodies_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    out = sum(len(p["delete_ids"]) for p in plan)
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
    say("WRITTEN: %d vehicles changed (%d lines out); fuel-economy rows %d -> %d; fleet %d; bare rows %d" % (len(plan), out, n0, n1, fleet, BARE_FROZEN))


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
