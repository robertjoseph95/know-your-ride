"""Fuel-economy repair, part 2: the range of electric cars, and an E85 figure shown as MPGe on two trucks.

Found 2026-11-15 by comparing every stored electric entry with EPA (114 vehicles, 527 entries):
  - An old enrichment step looked up ONE range per vehicle and wrote it to every entry of that vehicle. It was always
    the highest range EPA lists for the nameplate, so lower-range versions were overstated (55 vehicles, 200 entries,
    up to 151 miles). 49 more vehicles carried no range at all. The MPGe figures themselves were right.
  - 2023 Hyundai Ioniq 5: its only entry is the Ioniq 6 Long range AWD record, and EPA lists no Ioniq 5 for 2023.
  - Chevrolet Silverado 1500 2008 and GMC Sierra 1500 2019: the E85 combined figure of the flex-fuel 5.3L truck sits
    in the MPGe column of one entry each.

Rulings (Robert, 2026-11-15, "Accept, start dry run"):
  ELECTRIC  re-pull the entries of every electric car from EPA: one entry per distinct EPA record, each with its own
            range and MPGe, in the shape the fleet's electric cars use. A vehicle whose stored entries already equal
            EPA's is left alone.
  NAMES     every version EPA files under the nameplate comes in, except a different vehicle that shares the name:
            the Ioniq 5 N stays out (the Kona N ruling). PROPOSED in the dry run for confirmation: the 'Ioniq 5 Robo
            taxi' record also stays out (it is not a retail car).
  EMPTY     2023 Ioniq 5: remove the Ioniq 6 entry. EPA is silent on that car for that year, so it shows nothing.
  FLEX      clear the MPGe value on the two flex-fuel truck entries. Nothing else on those vehicles changes.

Source: EPA fueleconomy.gov only (government). Status-aware: an answer that is not HTTP 200 with a usable body stops
the run; an error is never 'nothing listed'. Every EPA name that contains the nameplate must either start with the
nameplate, be on the ALLOW list, or be on the LEFT_OUT list; anything else stops the run. Every record taken must be
typed EV by EPA itself. Every stored entry must be explained by an EPA record, or the run stops.

    python _repair_fuel_economy_electric.py
        DRY RUN. Pulls, prints every entry out and every entry in, rehearses the real build on in-memory copies of
        the database (before and after), saves the plan next to this script and prints its sha256. Writes nothing to
        wrench_vehicles.db. The EPA answers of the run are kept in a cache file beside the plan.

    python _repair_fuel_economy_electric.py --from-cache
        The same dry run, planned again from the cached EPA answers of the last pull (no new requests). For a changed
        name ruling.

    python _repair_fuel_economy_electric.py --resume
        Continues a dry run whose pull stopped part-way: keeps the cached answers and fetches only the rest.

    python _repair_fuel_economy_electric.py --write --sha <sha256 printed by the dry run>
        Backs up the database, then applies EXACTLY the saved plan (no new pull). Each vehicle is changed only if its
        stored entries still equal what the dry run showed.
"""
import sqlite3, shutil, datetime, sys, os, io, json, time, socket, hashlib, importlib.util, contextlib
import urllib.request, urllib.error, urllib.parse
import defusedxml.ElementTree as ET        # hardened parser; fetch_xml() also refuses any document type declaration

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_repair_fuel_economy_electric_plan_cache.json")      # gitignored (*_cache.json)
EPA_CACHE = os.path.join(ROOT, "_repair_fuel_economy_electric_epa_cache.json")       # gitignored (*_cache.json)
WRITE = "--write" in sys.argv
FROM_CACHE = "--from-cache" in sys.argv
RESUME = "--resume" in sys.argv              # continue a pull that stopped: keep the cached answers, fetch the rest
BARE_FROZEN = 424
EXPECT_ELECTRIC = 114                        # vehicles holding at least one entry typed 'Electric' (counted 2026-11-15)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
EPA = "https://www.fueleconomy.gov/ws/rest/vehicle"
PACE = 0.5                                   # seconds between requests
Q = urllib.parse.quote
REQUESTS = []
_last = [0.0]
COLS = ("city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, transmission, drive, range_miles, mpge, "
        "fuel_type, range_ev, city_ev, hwy_ev, comb_ev")
CITY, HWY, COMB, COST, ENG, TRANS, DRIVE, RANGE, MPGE, FTYPE = range(10)

# EPA names that belong to a nameplate although they do not start with it
ALLOW = {("Audi", "e-tron GT"): ["RS e-tron GT", "S e-tron GT"]}
# EPA names of a DIFFERENT vehicle that shares the nameplate's words (name, or name prefix)
LEFT_OUT = {("Hyundai", "Ioniq 5"): ["Ioniq 5 N", "Ioniq 5 Robo taxi"]}
# The row whose only entry belongs to another car, for a year in which EPA lists no such nameplate
EMPTY = {5220: dict(year=2023, make="Hyundai", model="Ioniq 5", foreign_token="ioniq 6")}
# Flex-fuel entries that carry EPA's E85 combined figure in the MPGe column
FLEX = {11359: dict(year=2008, make="Chevrolet", model="Silverado 1500", names=["Silverado C15 2WD"]),
        12653: dict(year=2019, make="GMC", model="Sierra 1500", names=["Sierra C10 2WD"])}


class PullError(Exception):
    pass


def say(*a):
    print(" ".join(str(x) for x in a).encode("ascii", "replace").decode("ascii"), flush=True)


def pref(name, prefixes):
    return any(name == p or name.startswith(p + " ") for p in prefixes)


# ---------------------------------------------------------------------------- EPA (status-aware, cached per run)
def fetch(url, what):
    if FROM_CACHE:
        sys.exit("--from-cache: %s is not in the cached pull; run a fresh dry run" % what)
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
            REQUESTS.append((what, "ERR", 0))
            if attempt < 3:
                time.sleep(5 * attempt)
                continue
            raise PullError("%s: %r" % (what, e))
        REQUESTS.append((what, status, len(body)))
        if status == 200:
            return body
        if status == 429 and ra.isdigit() and int(ra) > 120:
            raise PullError("%s: HTTP 429 with Retry-After %ss -- stop and come back later" % (what, ra))
        if status in (429, 500, 502, 503, 504) and attempt < 3:
            time.sleep(int(ra) if ra.isdigit() else 10 * attempt)
            continue
        raise PullError("%s: HTTP %s" % (what, status))
    raise PullError("%s: no answer" % what)


def fetch_xml(url, what):
    body = fetch(url, what)
    if b"<!DOCTYPE" in body or b"<!ENTITY" in body or len(body) > 2000000:
        raise PullError("%s: HTTP 200 but the XML carries a document type declaration or is oversized" % what)
    try:
        return ET.fromstring(body)
    except Exception as e:
        raise PullError("%s: HTTP 200 but the body is not XML (%r; %d bytes)" % (what, e, len(body)))


CACHE = {"pulled_at": None, "menu": {}, "recs": {}}
FIELDS = ["year", "make", "model", "displ", "trany", "drive", "fuelType", "atvType", "city08", "highway08", "comb08",
          "combA08", "range", "fuelCost08"]


def num(x):
    try:
        return int(float(x)) if x != "" else None
    except ValueError:
        return None


def menu(year, make):
    k = "%d|%s" % (year, make)
    if k not in CACHE["menu"]:
        root = fetch_xml("%s/menu/model?year=%d&make=%s" % (EPA, year, Q(make)), "EPA models %d %s" % (year, make))
        names = [(mi.findtext("text") or "").strip() for mi in root.iter("menuItem")]
        if not names:
            raise PullError("EPA models %d %s: HTTP 200 but no model list" % (year, make))
        CACHE["menu"][k] = names
    return CACHE["menu"][k]


def records(year, make, name):
    k = "%d|%s|%s" % (year, make, name)
    if k not in CACHE["recs"]:
        root = fetch_xml("%s/menu/options?year=%d&make=%s&model=%s" % (EPA, year, Q(make), Q(name)),
                         "EPA options %d %s %s" % (year, make, name))
        opts = [((mi.findtext("value") or "").strip(), (mi.findtext("text") or "").strip()) for mi in root.iter("menuItem")]
        if not opts or not all(v.isdigit() for v, _ in opts):
            raise PullError("EPA options %d %s %s: HTTP 200 but no usable option list %r" % (year, make, name, opts))
        out = []
        for eid, _text in opts:
            v = fetch_xml("%s/%s" % (EPA, eid), "EPA vehicle %s" % eid)
            g = {f: (v.findtext(f) or "").strip() for f in FIELDS}
            if (g["year"], g["make"], g["model"]) != (str(year), make, name):
                raise PullError("EPA vehicle %s is %s %s %s, not %d %s %s" % (eid, g["year"], g["make"], g["model"], year, make, name))
            city, hwy, comb = num(g["city08"]), num(g["highway08"]), num(g["comb08"])
            if city is None or hwy is None or comb is None:
                raise PullError("EPA vehicle %s: no city / highway / combined figure" % eid)
            out.append({"epa_id": eid, "name": name, "atv": g["atvType"], "city": city, "hwy": hwy, "comb": comb,
                        "combA": num(g["combA08"]) or None, "cost": num(g["fuelCost08"]), "displ": g["displ"] or None,
                        "trans": g["trany"] or None, "drive": g["drive"] or None, "fuel": g["fuelType"] or None,
                        "range": num(g["range"]) or None})
        CACHE["recs"][k] = out
    return CACHE["recs"][k]


# ---------------------------------------------------------------------------- stored rows
def stored(cur, vid):
    return [list(r) for r in cur.execute("SELECT id, %s FROM fuel_economy WHERE vehicle_id=? ORDER BY id" % COLS, (vid,))]


def electric_row(rec):          # the shape the fleet's electric cars use: MPGe + range, no MPG, typed 'Electric'
    return [None, None, None, rec["cost"], None, rec["trans"], rec["drive"], rec["range"], rec["comb"], "Electric",
            None, None, None, None]


def fmt(d, tag):
    return "%-9s MPGe %-4s range %-5s %-18s %-17s cost %-5s" % (tag, d[MPGE], d[RANGE], d[TRANS], d[DRIVE], d[COST])


def new_plan(vid, year, make, model, kind, cur_rows):
    return {"id": vid, "year": year, "make": make, "model": model, "kind": kind, "current": cur_rows, "delete_ids": [],
            "insert": [], "null_mpge_ids": [], "taken": [], "left_out": [], "sources": [], "log_status": None,
            "pulled_at": CACHE["pulled_at"]}


# ---------------------------------------------------------------------------- planning
def plan_electric(cur, vid, year, make, model, stats):
    cur_rows = stored(cur, vid)
    names = menu(year, make)
    token = model.lower()        # plain lower-case text: squeezing out spaces would make 'iX' match '530i xDrive'
    near = sorted(n for n in names if token in n.lower())
    left = [n for n in near if pref(n, LEFT_OUT.get((make, model), []))]
    taken = [n for n in near if n not in left and (n.lower().startswith(token) or pref(n, ALLOW.get((make, model), [])))]
    stray = [n for n in near if n not in left and n not in taken]
    if stray:
        raise PullError("%d %s %s: EPA lists %r, which neither starts with the nameplate nor is on a list -- needs a ruling" % (year, make, model, stray))
    if not taken:
        raise PullError("%d %s %s: EPA lists no name for this nameplate (names near it: %r) -- needs a ruling" % (year, make, model, near))
    p = new_plan(vid, year, make, model, "electric", cur_rows)
    p["taken"], p["left_out"] = taken, left
    recs = [rec for n in taken for rec in records(year, make, n)]
    out_recs = [rec for n in left for rec in records(year, make, n)]
    for rec in recs:
        if rec["atv"] != "EV":
            raise PullError("EPA vehicle %s under %r is typed %r, not EV -- needs a ruling" % (rec["epa_id"], rec["name"], rec["atv"]))
    new, seen = [], set()
    for rec in recs:
        row = electric_row(rec)
        key = (row[MPGE], row[RANGE], row[DRIVE], row[TRANS], row[COST])
        if key not in seen:
            seen.add(key)
            new.append((row, rec))
    lines = []
    for r in cur_rows:
        d = r[1:]
        if d[FTYPE] != "Electric" or d[COMB] is not None or d[ENG] is not None:
            raise PullError("id %d: stored entry fe#%d is not in the electric shape -- needs a look" % (vid, r[0]))
        hit = [rec for rec in recs if (d[MPGE], d[TRANS], d[DRIVE]) == (rec["comb"], rec["trans"], rec["drive"])]
        out = [rec for rec in out_recs if (d[MPGE], d[TRANS], d[DRIVE]) == (rec["comb"], rec["trans"], rec["drive"])]
        if not hit and not out:
            raise PullError("id %d: stored entry fe#%d (MPGe %s, %s, %s) matches no EPA record of this nameplate -- needs a look"
                            % (vid, r[0], d[MPGE], d[TRANS], d[DRIVE]))
        ranges = sorted({rec["range"] for rec in hit if rec["range"]})
        if not hit:
            note = "a left-out vehicle: %s" % out[0]["name"]
            stats["entries of a left-out vehicle"] += 1
        elif not ranges:
            note = "EPA prints no range for the matching record"
        elif d[RANGE] is None:
            note = "no range stored; EPA %s" % "/".join(map(str, ranges))
            stats["entries gaining a range"] += 1
        elif ranges == [d[RANGE]]:
            note = "range right"
            stats["entries already right"] += 1
        elif d[RANGE] in ranges:
            note = "range matches one of several EPA records (%s)" % "/".join(map(str, ranges))
            stats["entries matching one of several"] += 1
        else:
            note = "RANGE OVERSTATED by %d (EPA %s)" % (d[RANGE] - max(ranges), "/".join(map(str, ranges))) if d[RANGE] > max(ranges) \
                else "range differs (EPA %s)" % "/".join(map(str, ranges))
            stats["entries with a wrong range"] += 1
            stats["_over"].append(d[RANGE] - max(ranges))
        lines.append("    " + fmt(d, "fe#%d" % r[0]) + "   " + note)
    if sorted(map(json.dumps, [r[1:] for r in cur_rows])) == sorted(map(json.dumps, [x for x, _ in new])):
        p["kind"] = "unchanged"
        say("")
        say("[UNCHANGED] id %d  %d %s %s   %d entr%s already equal EPA (names: %s)" % (vid, year, make, model, len(cur_rows),
                                                                                  "y" if len(cur_rows) == 1 else "ies", "; ".join(taken)))
        return p
    if any(x[RANGE] is None for x, _ in new):
        stats["new entries without a range"] += sum(1 for x, _ in new if x[RANGE] is None)
    p["delete_ids"] = [r[0] for r in cur_rows]
    p["insert"] = [x for x, _ in new]
    p["sources"] = [[rec["name"], rec["epa_id"]] for _, rec in new]
    p["log_status"] = "ok"
    say("")
    say("[ELECTRIC] id %d  %d %s %s   %d out, %d in" % (vid, year, make, model, len(cur_rows), len(new)))
    say("  taken: %s%s" % ("; ".join(taken), (" | LEFT OUT: " + "; ".join(left)) if left else ""))
    say("  OUT:")
    for ln in lines:
        say(ln)
    say("  IN:")
    for x, rec in new:
        say("    " + fmt(x, "") + "   <- %s (EPA %s)" % (rec["name"], rec["epa_id"]))
    return p


def plan_empty(cur, vid, spec):
    cur_rows = stored(cur, vid)
    names = menu(spec["year"], spec["make"])
    near = [n for n in names if spec["model"].lower() in n.lower()]
    if near:
        raise PullError("%d %s %s: EPA now lists %r -- this needs a normal electric op" % (spec["year"], spec["make"], spec["model"], near))
    other = sorted(n for n in names if spec["foreign_token"] in n.lower())
    recs = [rec for n in other for rec in records(spec["year"], spec["make"], n)]
    p = new_plan(vid, spec["year"], spec["make"], spec["model"], "empty", cur_rows)
    say("")
    say("[EMPTY] id %d  %d %s %s   EPA lists %d %s names for %d and none contains the nameplate" % (
        vid, spec["year"], spec["make"], spec["model"], len(names), spec["make"], spec["year"]))
    for r in cur_rows:
        d = r[1:]
        hit = [rec for rec in recs if (d[MPGE], d[RANGE], d[TRANS], d[DRIVE]) == (rec["comb"], rec["range"], rec["trans"], rec["drive"])]
        if not hit:
            raise PullError("id %d: stored entry fe#%d matches no record of the other car -- needs a look" % (vid, r[0]))
        say("    OUT  " + fmt(d, "fe#%d" % r[0]) + "   <= %s (EPA %s)" % (hit[0]["name"], hit[0]["epa_id"]))
        p["sources"].append([r[0], hit[0]["name"], hit[0]["epa_id"]])
    p["delete_ids"] = [r[0] for r in cur_rows]
    p["log_status"] = "empty"
    say("  after: no fuel-economy entry (EPA is silent on this car for this year)")
    return p


def plan_flex(cur, vid, spec):
    cur_rows = stored(cur, vid)
    names = menu(spec["year"], spec["make"])
    missing = [n for n in spec["names"] if n not in names]
    if missing:
        raise PullError("%d %s: EPA does not list %r" % (spec["year"], spec["make"], missing))
    recs = [rec for n in spec["names"] for rec in records(spec["year"], spec["make"], n)]
    p = new_plan(vid, spec["year"], spec["make"], spec["model"], "flex", cur_rows)
    say("")
    say("[FLEX] id %d  %d %s %s   (%d stored entries; only the MPGe value of one changes)" % (vid, spec["year"], spec["make"], spec["model"], len(cur_rows)))
    for r in cur_rows:
        d = r[1:]
        if d[MPGE] is None:
            say("    stay " + "fe#%-6d %s/%s/%s %sL %s %s" % (r[0], d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE]))
            continue
        hit = [rec for rec in recs if rec["atv"] == "FFV" and rec["combA"] == d[MPGE] and
               (d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE]) == (rec["city"], rec["hwy"], rec["comb"], rec["displ"], rec["trans"], rec["drive"])]
        if not hit:
            raise PullError("id %d: stored entry fe#%d carries MPGe %s but no flex-fuel EPA record explains it -- needs a look" % (vid, r[0], d[MPGE]))
        p["null_mpge_ids"].append(r[0])
        p["sources"].append([r[0], hit[0]["name"], hit[0]["epa_id"], hit[0]["fuel"], hit[0]["combA"]])
        say("    FIX  " + "fe#%-6d %s/%s/%s %sL %s %s  MPGe %s -> empty   <= %s (EPA %s: %s, typed FFV, E85 combined %s)" % (
            r[0], d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE], d[MPGE], hit[0]["name"], hit[0]["epa_id"], hit[0]["fuel"], hit[0]["combA"]))
    if len(p["null_mpge_ids"]) != 1:
        raise PullError("id %d: %d entries carry an MPGe value, 1 expected" % (vid, len(p["null_mpge_ids"])))
    return p


# ---------------------------------------------------------------------------- plan hash, apply
def plan_sha(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def after_rows(p):
    gone, fix = set(p["delete_ids"]), set(p["null_mpge_ids"])
    out = []
    for r in p["current"]:
        if r[0] in gone:
            continue
        d = list(r[1:])
        if r[0] in fix:
            d[MPGE] = None
        out.append(d)
    return out + [list(x) for x in p["insert"]]


def touches(p):
    return bool(p["delete_ids"] or p["insert"] or p["null_mpge_ids"])


def apply(cur, plan):
    for p in plan:
        vid = p["id"]
        row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        if not row or tuple(row) != (p["year"], p["make"], p["model"]):
            raise RuntimeError("target %d is %r, not %d %s %s" % (vid, row and tuple(row), p["year"], p["make"], p["model"]))
        if stored(cur, vid) != p["current"]:
            raise RuntimeError("target %d: the stored fuel-economy entries changed since the dry run" % vid)
        for fid in p["delete_ids"]:
            cur.execute("DELETE FROM fuel_economy WHERE id=? AND vehicle_id=?", (fid, vid))
            if cur.rowcount != 1:
                raise RuntimeError("target %d: entry fe#%d was not deleted" % (vid, fid))
        for fid in p["null_mpge_ids"]:
            cur.execute("UPDATE fuel_economy SET mpge=NULL WHERE id=? AND vehicle_id=? AND mpge IS NOT NULL", (fid, vid))
            if cur.rowcount != 1:
                raise RuntimeError("target %d: entry fe#%d was not updated" % (vid, fid))
        if p["insert"]:
            cur.executemany("INSERT INTO fuel_economy (vehicle_id, " + COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            [[vid] + list(x) for x in p["insert"]])
        if p["log_status"]:
            cur.execute("INSERT OR REPLACE INTO pull_log (vehicle_id, endpoint, status, pulled_at) VALUES (?,?,?,?)",
                        (vid, "fuel-economy", p["log_status"], p["pulled_at"]))
        if [r[1:] for r in stored(cur, vid)] != after_rows(p):
            raise RuntimeError("target %d does not hold the planned entries" % vid)


def bare_count(cur):
    return cur.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                       "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) "
                       "WHERE source='owner-manual-verified'").fetchone()[0]


def electric_ids(cur):
    return [r[0] for r in cur.execute("SELECT DISTINCT vehicle_id FROM fuel_economy WHERE fuel_type='Electric' ORDER BY vehicle_id")]


def totals(plan):
    return sum(len(p["delete_ids"]) for p in plan), sum(len(p["insert"]) for p in plan), sum(len(p["null_mpge_ids"]) for p in plan)


# ---------------------------------------------------------------------------- rehearsal: real build, before and after
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
        out, inn, fixed = totals(plan)
        n1 = c1.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        if n1 != n0 - out + inn:
            say("  REHEARSAL FAILED: fuel-economy rows %d -> %d, expected %d" % (n0, n1, n0 - out + inn))
            return False
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
    changing = {p["id"]: p for p in plan if touches(p)}
    bad = 0
    for vid, a in before.items():
        b = after[vid]
        if vid in changing:
            if {k: v for k, v in a.items() if k != "mpg"} != {k: v for k, v in b.items() if k != "mpg"}:
                say("  UNEXPECTED: id %d differs outside the fuel-economy key" % vid)
                bad += 1
            if a.get("mpg") == b.get("mpg"):
                say("  UNEXPECTED: id %d shows no fuel-economy change" % vid)
                bad += 1
        elif a != b:
            say("  UNEXPECTED: id %d changed although the plan does not touch it" % vid)
            bad += 1
    no_range = 0
    for vid, p in changing.items():
        mpg = after[vid].get("mpg") or []
        if p["kind"] == "empty":
            if mpg:
                say("  UNEXPECTED: id %d still ships fuel economy" % vid)
                bad += 1
            continue
        if not mpg:
            say("  UNEXPECTED: id %d would ship no fuel-economy entry" % vid)
            bad += 1
        for m in mpg:
            if p["kind"] == "electric":
                ok = bool(m.get("mpge")) and m.get("comb") is None and not m.get("eng")
                no_range += not m.get("range")
            else:
                ok = all(isinstance(m.get(k), int) for k in ("city", "hwy", "comb")) and bool(m.get("eng")) and not m.get("mpge")
            if not ok:
                say("  UNEXPECTED entry shape after repair on id %d: %r" % (vid, m))
                bad += 1
    odd = 0
    for v in after.values():
        for m in v.get("mpg") or []:
            gas = all(isinstance(m.get(k), int) for k in ("city", "hwy", "comb")) and bool(m.get("eng")) and not m.get("mpge")
            ev = bool(m.get("mpge")) and m.get("comb") is None and not m.get("eng")
            odd += not (gas or ev)
    if bad:
        return False
    ver = sorted(v for v in changing if isinstance(before[v].get("oil"), dict) and before[v]["oil"].get("ver") == 1)
    n_ver = sum(1 for v in after.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    say("  build gates passed on both copies; vehicles %d -> %d; owner's-manual-verified %d (unchanged)" % (len(before), len(after), n_ver))
    say("  %d vehicles differ, each in the fuel-economy key only; all other %d vehicles identical" % (len(changing), len(after) - len(changing)))
    say("  verified vehicles among the changed ones: %s" % ver)
    say("  fuel-economy rows %d -> %d (%d out, %d in, %d MPGe values cleared); bare owner-manual rows %d" % (n0, n1, out, inn, fixed, BARE_FROZEN))
    say("  electric entries without a range after the repair: %d; entries fleet-wide that are neither gasoline-shaped nor electric-shaped: %d" % (no_range, odd))
    return True


# ---------------------------------------------------------------------------- dry run / write
def dry_run():
    global CACHE
    if FROM_CACHE or (RESUME and os.path.exists(EPA_CACHE)):
        with io.open(EPA_CACHE, encoding="utf-8") as fh:
            CACHE = json.load(fh)
    else:
        CACHE["pulled_at"] = datetime.datetime.now().isoformat()
    say("FUEL-ECONOMY ELECTRIC-RANGE AND FLEX-FUEL REPAIR -- DRY RUN (nothing is written)  %s%s" % (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ("   [planned from the cached EPA pull of %s]" % CACHE["pulled_at"]) if FROM_CACHE else ""))
    stats = {k: 0 for k in ("entries with a wrong range", "entries gaining a range", "entries already right", "entries matching one of several",
                            "entries of a left-out vehicle", "new entries without a range")}
    stats["_over"] = []
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        if bare_count(cur) != BARE_FROZEN:
            sys.exit("bare owner-manual rows are not %d" % BARE_FROZEN)
        ids = electric_ids(cur)
        if len(ids) != EXPECT_ELECTRIC:
            sys.exit("%d vehicles hold electric entries, %d expected -- the fleet changed, review before running" % (len(ids), EXPECT_ELECTRIC))
        veh = {r[0]: r[1:] for r in cur.execute("SELECT id, year, make, model FROM vehicles")}
        plan = []
        try:
            for vid in sorted(ids, key=lambda i: (veh[i][1], veh[i][2], veh[i][0])):
                year, make, model = veh[vid]
                if vid in EMPTY:
                    if (year, make, model) != (EMPTY[vid]["year"], EMPTY[vid]["make"], EMPTY[vid]["model"]):
                        sys.exit("target %d is %r" % (vid, veh[vid]))
                    plan.append(plan_empty(cur, vid, EMPTY[vid]))
                else:
                    plan.append(plan_electric(cur, vid, year, make, model, stats))
            for vid, spec in FLEX.items():
                if veh[vid] != (spec["year"], spec["make"], spec["model"]):
                    sys.exit("target %d is %r" % (vid, veh[vid]))
                plan.append(plan_flex(cur, vid, spec))
        finally:
            if not FROM_CACHE:
                with io.open(EPA_CACHE, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(CACHE, fh, sort_keys=True)
    finally:
        con.close()
    say("")
    say("SUMMARY")
    for kind, label in (("electric", "electric, re-pulled"), ("unchanged", "electric, already right"), ("empty", "wrong car, emptied"), ("flex", "flex-fuel, MPGe cleared")):
        ps = [p for p in plan if p["kind"] == kind]
        say("  %-26s %3d vehicles: %3d entries out, %3d in, %d cleared" % (label, len(ps), sum(len(p["delete_ids"]) for p in ps),
                                                                       sum(len(p["insert"]) for p in ps), sum(len(p["null_mpge_ids"]) for p in ps)))
    out, inn, fixed = totals(plan)
    say("  %-26s %3d vehicles: %3d entries out, %3d in, %d cleared" % ("total touched", sum(1 for p in plan if touches(p)), out, inn, fixed))
    over = sorted(stats.pop("_over"))
    for k, v in stats.items():
        say("  %-36s %d" % (k, v))
    if over:
        say("  wrong ranges: stored minus EPA's highest for that entry: min %+d, median %+d, max %+d" % (over[0], over[len(over) // 2], over[-1]))
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
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        bare = bare_count(cur)
        fleet = cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        n0 = cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        ids = electric_ids(cur)
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    if sorted(ids) != sorted(p["id"] for p in plan if p["kind"] != "flex") or sorted(p["id"] for p in plan if p["kind"] == "flex") != sorted(FLEX):
        sys.exit("the saved plan does not cover exactly the electric vehicles in the database and the two flex-fuel trucks")
    bak = "%s.bak_fe_electric_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    out, inn, fixed = totals(plan)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        apply(cur, plan)
        n1 = cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        if n1 != n0 - out + inn:
            raise RuntimeError("fuel-economy rows %d -> %d, expected %d" % (n0, n1, n0 - out + inn))
        if cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] != fleet:
            raise RuntimeError("fleet count moved")
        if bare_count(cur) != BARE_FROZEN:
            raise RuntimeError("bare owner-manual count moved")
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise
    con.close()
    say("WRITTEN: fuel economy changed on %d vehicles (%d entries out, %d in, %d MPGe values cleared); fuel-economy rows %d -> %d; fleet %d; bare rows %d"
        % (sum(1 for p in plan if touches(p)), out, inn, fixed, n0, n1, fleet, BARE_FROZEN))


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
            bad = [r for r in REQUESTS if r[1] != 200]
            say("requests so far: %d, non-200: %s" % (len(REQUESTS), bad[:8]))
            sys.exit(2)
