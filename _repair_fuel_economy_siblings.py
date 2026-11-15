"""Fuel-economy repair: rows that carry ANOTHER vehicle's EPA figures, or figures in the wrong unit.

Found 2026-11-15 by the shape of the stored data (whole fleet), confirmed against EPA row by row:
  A. entries typed 'Electric' on a nameplate that is not an electric car. An earlier pull typed EVERY entry of a
     vehicle 'Electric' when one EPA match was electric, so gasoline entries lost city / highway / combined and their
     combined figure sits in the MPGe column; the electric sibling's own entries sit beside them.
  B. an electric sibling's MPGe stored in the plain MPG columns (no fuel type, no displacement).
  C. a fuel-cell sibling stored the same way.
  D. Mercedes-Benz GLC 300: a GLC350e plug-in entry and a C300 sedan entry (EPA writes 'GLC300'; the pull matched '300').
  E. Jaguar I-Pace: the right car, but its MPGe is stored as MPG.

Rulings (Robert, 2026-11-15, "Accept, start dry run"):
  REPLACE  the fuel-economy entries from STATED EPA model names where the gasoline entries are malformed or missing
           (group A, and the 2002 Explorer whose only entry is the postal electric truck).
  REMOVE   only the foreign entries where the vehicle's own entries are already right (groups B, C, D, including the
           two C300 entries). The other stored entries are not touched, not even re-numbered.
  ELECTRIC re-pull the I-Pace as electric entries (MPGe and range), in the shape the fleet's electric cars use.
  VERIFY   2024 Dodge Charger: EPA lists only the electric Charger that year, so its entries are the right car. No change.
  Name choices: Fiat 500 = 500 + 500 Abarth (500 L / 500 X are other cars); Countryman 2026 = S + JCW; Explorer 2002 =
  the four plain Explorer names (Sport and Sport Trac left out); Mustang keeps Dark Horse and GTD.
  NOT in scope: the '5.7L Hemi' engine label on the 2024 / 2026 Charger rows; the range figures of electric nameplates.

Source: EPA fueleconomy.gov only (government). Status-aware: an answer that is not HTTP 200 with a usable body stops
the run; an error is never 'nothing listed'. EPA lists a nameplate under several model names, so every op states the
names it takes and the names it leaves out; any other name that contains the nameplate stops the run for a ruling.
A record is electrified when EPA's own atvType says EV, FCV or Plug-in Hybrid (a name alone is not enough: the 2000
Ranger's electric truck is filed under the same name as the gasoline one).

    python _repair_fuel_economy_siblings.py
        DRY RUN. Pulls, prints every entry out and every entry in, rehearses the real build on in-memory copies of
        the database (before and after) and proves that only the fuel-economy key of the planned vehicles differs.
        Saves the plan next to this script and prints its sha256. Touches nothing in wrench_vehicles.db.

    python _repair_fuel_economy_siblings.py --write --sha <sha256 printed by the dry run>
        Backs up the database, then applies EXACTLY the saved plan (no new pull). Each vehicle is changed only if its
        stored entries still equal what the dry run showed.
"""
import sqlite3, shutil, datetime, sys, os, io, json, time, socket, hashlib, importlib.util, contextlib
import urllib.request, urllib.error, urllib.parse
import defusedxml.ElementTree as ET        # hardened parser; fetch_xml() also refuses any document type declaration

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_repair_fuel_economy_siblings_plan_cache.json")      # gitignored (*_cache.json)
WRITE = "--write" in sys.argv
BARE_FROZEN = 424
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
EPA = "https://www.fueleconomy.gov/ws/rest/vehicle"
PACE = 0.7                                   # seconds between requests
Q = urllib.parse.quote
REQUESTS = []
_last = [0.0]
ELECTRIFIED = ("EV", "FCV", "Plug-in Hybrid")
# fuel_economy data columns, in table order (id and vehicle_id excluded)
COLS = ("city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, transmission, drive, range_miles, mpge, "
        "fuel_type, range_ev, city_ev, hwy_ev, comb_ev")
CITY, HWY, COMB, COST, ENG, TRANS, DRIVE, RANGE, MPGE, FTYPE = range(10)


def replace(vid, year, make, model, keep, ignore):
    return dict(id=vid, year=year, make=make, model=model, kind="replace", keep=keep, ignore=ignore)


def remove(vid, year, make, model, foreign, out, extra=()):
    """foreign = [(EPA name or name prefix, allowed atvType list or None for any)]; out = entries expected to go."""
    return dict(id=vid, year=year, make=make, model=model, kind="remove", foreign=foreign, out=out, extra=list(extra))


EV, FCV, PHEV = ["EV"], ["FCV"], ["Plug-in Hybrid"]
OPS = [
    # ---- REPLACE from stated EPA names (gasoline entries malformed or missing)
    replace(6406, 2024, "Chevrolet", "Blazer", ["Blazer AWD", "Blazer FWD"], ["Blazer EV", "Trailblazer"]),
    replace(9626, 2026, "Chevrolet", "Blazer", ["Blazer AWD", "Blazer FWD"], ["Blazer EV", "Trailblazer"]),
    replace(13156, 2026, "Dodge", "Charger", ["Charger R/T AWD", "Charger Scat Pack AWD"], ["Charger Daytona"]),
    replace(33001, 2018, "Fiat", "500", ["500", "500 Abarth"], ["500 L", "500 X", "500X", "500e"]),
    replace(34344, 2019, "Fiat", "500", ["500", "500 Abarth"], ["500 L", "500 X", "500X", "500e"]),
    replace(13101, 2025, "Ford", "Mustang", ["Mustang", "Mustang Dark Horse", "Mustang GTD"], ["Mustang Mach-E"]),
    replace(5831, 2023, "Genesis", "G80", ["G80 AWD", "G80 RWD"], ["Electrified G80"]),
    replace(7409, 2024, "Genesis", "G80", ["G80 AWD"], ["Electrified G80"]),
    replace(9021, 2025, "Genesis", "G80", ["G80 AWD"], ["Electrified G80"]),
    replace(10633, 2026, "Genesis", "G80", ["G80 AWD"], ["Electrified G80"]),
    replace(7413, 2024, "Genesis", "GV70", ["GV70 AWD"], ["Electrified GV70"]),
    replace(9025, 2025, "Genesis", "GV70", ["GV70 AWD"], ["Electrified GV70"]),
    replace(10637, 2026, "Genesis", "GV70", ["GV70 AWD", "GV70 AWD (4 Mode)", "GV70 AWD (5 Mode)"], ["Electrified GV70"]),
    replace(682, 2020, "Kia", "Soul", ["Soul", "Soul Eco dynamics"], ["Soul Electric"]),
    replace(9515, 2026, "MINI", "Countryman", ["Countryman S All4", "JCW Countryman ALL4"], ["Countryman SE ALL4"]),
    replace(7106, 2024, "Porsche", "Macan", ["Macan", "Macan GTS", "Macan S", "Macan T"],
            ["Macan 4 Electric", "Macan 4S Electric", "Macan Electric", "Macan Turbo Electric"]),
    replace(8691, 2025, "Porsche", "Macan", ["Macan", "Macan GTS", "Macan S", "Macan T"],
            ["Macan 4 Electric", "Macan 4S Electric", "Macan Electric", "Macan Turbo Electric"]),
    replace(6696, 2024, "Volvo", "XC40", ["XC40 B5 AWD"], ["XC40 Recharge"]),
    replace(11006, 2002, "Ford", "Explorer", ["Explorer 2WD", "Explorer 2WD FFV", "Explorer 4WD", "Explorer 4WD FFV"],
            ["Explorer Sport", "Explorer USPS Electric"]),
    # ---- REMOVE only the foreign entries (the vehicle's own entries are already right and stay untouched)
    remove(7086, 2024, "Audi", "Q8", [("Q8 e-tron", EV), ("Q8 Sportback e-tron", EV)], 3),
    remove(14132, 2001, "Ford", "Explorer", [("Explorer USPS Electric", EV)], 1),
    remove(10966, 2000, "Ford", "Ranger", [("Ranger Pickup 2WD", EV)], 2),
    remove(10983, 2001, "Ford", "Ranger", [("Ranger Pickup 2WD", EV)], 1),
    remove(13216, 2000, "Toyota", "RAV4", [("RAV4 EV", EV)], 1),
    remove(10997, 2001, "Toyota", "RAV4", [("RAV4 EV", EV)], 1),
    remove(11030, 2002, "Toyota", "RAV4", [("RAV4 EV", EV)], 1),
    remove(11072, 2003, "Toyota", "RAV4", [("RAV4 EV", EV)], 1),
    remove(3602, 2022, "Volvo", "XC40", [("XC40 Recharge", EV)], 1),
    remove(5123, 2023, "Volvo", "XC40", [("XC40 Recharge", EV)], 1),
    remove(12382, 2017, "Hyundai", "Tucson", [("Tucson Fuel Cell", FCV)], 1),
    remove(371, 2020, "Honda", "Clarity", [("Clarity FCV", FCV)], 1),
    remove(1867, 2021, "Honda", "Clarity", [("Clarity FCV", FCV)], 1),
    remove(38650, 2019, "Mercedes-Benz", "GLC 300", [("GLC350e 4matic", PHEV), ("C300", None)], 2, extra=["GLC350e 4matic", "C300"]),
    remove(38651, 2020, "Mercedes-Benz", "GLC 300", [("GLC350e 4matic", PHEV), ("C300", None)], 2, extra=["GLC350e 4matic", "C300"]),
    # ---- ELECTRIC: the right car, stored in the wrong unit
    dict(id=13, year=2020, make="Jaguar", model="I-Pace", kind="electric", own=["I-Pace"]),
    dict(id=1512, year=2021, make="Jaguar", model="I-Pace", kind="electric", own=["I-Pace EV400"]),
    # ---- VERIFY only: EPA lists no gasoline Charger for 2024
    dict(id=13024, year=2024, make="Dodge", model="Charger", kind="verify", own_prefix="Charger 2-Dr Daytona"),
]
assert len({o["id"] for o in OPS}) == len(OPS) == 37


class PullError(Exception):
    pass


def say(*a):
    print(" ".join(str(x) for x in a).encode("ascii", "replace").decode("ascii"), flush=True)


def norm(s):
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def pref(name, prefixes):
    return any(name == p or name.startswith(p + " ") for p in prefixes)


# ---------------------------------------------------------------------------- EPA (status-aware)
def fetch(url, what):
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


_MENU, _RECS = {}, {}
FIELDS = ["year", "make", "model", "displ", "cylinders", "trany", "drive", "fuelType", "atvType", "city08", "highway08",
          "comb08", "range", "fuelCost08"]


def menu(year, make):
    k = (year, make)
    if k not in _MENU:
        root = fetch_xml("%s/menu/model?year=%d&make=%s" % (EPA, year, Q(make)), "EPA models %d %s" % (year, make))
        names = [(mi.findtext("text") or "").strip() for mi in root.iter("menuItem")]
        if not names:
            raise PullError("EPA models %d %s: HTTP 200 but no model list" % (year, make))
        _MENU[k] = names
    return _MENU[k]


def num(x):
    try:
        return int(float(x)) if x != "" else None
    except ValueError:
        return None


def records(year, make, name):
    k = (year, make, name)
    if k not in _RECS:
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
                        "cost": num(g["fuelCost08"]), "displ": g["displ"] or None, "trans": g["trany"] or None,
                        "drive": g["drive"] or None, "fuel": g["fuelType"] or None, "range": num(g["range"]) or None})
        _RECS[k] = out
    return _RECS[k]


def near_names(op):
    names = menu(op["year"], op["make"])
    token = norm(op["model"])
    return sorted(n for n in names if token in norm(n)), names


# ---------------------------------------------------------------------------- stored rows
def stored(cur, vid):
    return [list(r) for r in cur.execute("SELECT id, %s FROM fuel_economy WHERE vehicle_id=? ORDER BY id" % COLS, (vid,))]


def fmt_stored(r):
    d = r[1:]
    return "fe#%-5d %4s/%4s/%4s  MPGe %-4s %-4s %-34s %-27s type %-22s range %-4s cost %s" % (
        r[0], d[CITY], d[HWY], d[COMB], d[MPGE], (d[ENG] + "L") if d[ENG] else "-", d[TRANS], d[DRIVE], d[FTYPE], d[RANGE], d[COST])


def gas_row(rec):
    return [rec["city"], rec["hwy"], rec["comb"], rec["cost"], rec["displ"], rec["trans"], rec["drive"], None, None,
            rec["fuel"], None, None, None, None]


def electric_row(rec):          # the shape the fleet's electric cars use: MPGe + range, no MPG, typed 'Electric'
    return [None, None, None, rec["cost"], None, rec["trans"], rec["drive"], rec["range"], rec["comb"], "Electric",
            None, None, None, None]


def fmt_new(row, rec):
    return "           %4s/%4s/%4s  MPGe %-4s %-4s %-34s %-27s type %-22s range %-4s cost %-5s <- %s (EPA %s)" % (
        row[CITY], row[HWY], row[COMB], row[MPGE], (row[ENG] + "L") if row[ENG] else "-", row[TRANS], row[DRIVE],
        row[FTYPE], row[RANGE], row[COST], rec["name"], rec["epa_id"])


def same_car(d, rec):
    """A stored entry and an EPA record: all three figures, displacement, transmission and drive."""
    return (d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE]) == (rec["city"], rec["hwy"], rec["comb"], rec["displ"], rec["trans"], rec["drive"])


# ---------------------------------------------------------------------------- planning one op
def plan_op(cur, op):
    vid = op["id"]
    row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
    if not row or tuple(row) != (op["year"], op["make"], op["model"]):
        sys.exit("target %d is %r, not %d %s %s" % (vid, row and tuple(row), op["year"], op["make"], op["model"]))
    cur_rows = stored(cur, vid)
    if not cur_rows:
        sys.exit("target %d holds no fuel-economy entries" % vid)
    near, all_names = near_names(op)
    p = {"id": vid, "year": op["year"], "make": op["make"], "model": op["model"], "kind": op["kind"], "current": cur_rows,
         "near_names": near, "delete_ids": [], "insert": [], "sources": [],
         "pulled_at": datetime.datetime.now().isoformat()}
    say("")
    say("[%s] id %d  %d %s %s   (%d stored entr%s)" % (op["kind"].upper(), vid, op["year"], op["make"], op["model"],
                                                      len(cur_rows), "y" if len(cur_rows) == 1 else "ies"))
    say("  EPA names containing the nameplate: " + "; ".join(near))

    if op["kind"] == "replace":
        missing = [n for n in op["keep"] if n not in near]
        if missing:
            raise PullError("%d %s %s: EPA does not list %r -- needs a ruling" % (op["year"], op["make"], op["model"], missing))
        stray = [n for n in near if n not in op["keep"] and not pref(n, op["ignore"])]
        if stray:
            raise PullError("%d %s %s: EPA lists %r, which this op neither takes nor leaves out -- needs a ruling"
                            % (op["year"], op["make"], op["model"], stray))
        say("  taken: %s | left out: %s" % ("; ".join(op["keep"]), "; ".join(n for n in near if n not in op["keep"])))
        new, seen = [], set()
        for name in op["keep"]:
            for rec in records(op["year"], op["make"], name):
                if rec["atv"] in ELECTRIFIED:
                    raise PullError("EPA vehicle %s under %r is typed %s -- a taken name must not be electrified" % (rec["epa_id"], name, rec["atv"]))
                key = (rec["city"], rec["hwy"], rec["comb"], rec["displ"], rec["drive"], rec["trans"])
                if key in seen:
                    continue
                seen.add(key)
                new.append((gas_row(rec), rec))
        if not new:
            raise PullError("%d %s %s: no replacement entries" % (op["year"], op["make"], op["model"]))
        # no gasoline variant that is stored today may disappear
        for r in cur_rows:
            d = r[1:]
            if d[ENG] is None:
                continue
            fig = d[COMB] if d[COMB] is not None else d[MPGE]
            if not any((x[ENG], x[TRANS], x[DRIVE], x[COMB]) == (d[ENG], d[TRANS], d[DRIVE], fig) for x, _ in new):
                raise PullError("id %d: stored gasoline entry %s %s %s (%s) has no counterpart in the replacement -- needs a look"
                                % (vid, d[ENG], d[TRANS], d[DRIVE], fig))
        p["delete_ids"] = [r[0] for r in cur_rows]
        p["insert"] = [x for x, _ in new]
        p["sources"] = [[rec["name"], rec["epa_id"], rec["atv"]] for _, rec in new]
        say("  OUT (%d):" % len(cur_rows))
        for r in cur_rows:
            say("    " + fmt_stored(r))
        say("  IN (%d):" % len(new))
        for x, rec in new:
            say("    " + fmt_new(x, rec))

    elif op["kind"] == "remove":
        names = sorted(set(near) | set(op["extra"]))
        missing = [n for n in op["extra"] if n not in all_names]
        if missing:
            raise PullError("%d %s: EPA does not list %r" % (op["year"], op["make"], missing))
        recs = [rec for n in names for rec in records(op["year"], op["make"], n)]

        def is_foreign(rec):
            return any((rec["name"] == f or rec["name"].startswith(f + " ")) and (atv is None or rec["atv"] in atv)
                       for f, atv in op["foreign"])

        say("  foreign (to go): " + "; ".join("%s%s" % (f, "" if atv is None else " [%s]" % "/".join(atv)) for f, atv in op["foreign"]))
        out_ids, lines = [], []
        for r in cur_rows:
            d = r[1:]
            hit = [rec for rec in recs if same_car(d, rec)]
            f = [rec for rec in hit if is_foreign(rec)]
            o = [rec for rec in hit if not is_foreign(rec)]
            if f and not o:
                out_ids.append(r[0])
                p["sources"].append([r[0], f[0]["name"], f[0]["epa_id"], f[0]["atv"]])
                lines.append("    OUT  " + fmt_stored(r) + "   <= %s [%s]" % (f[0]["name"], f[0]["atv"] or "conventional"))
            elif o and not f:
                if any(rec["atv"] in ("EV", "FCV") for rec in o):
                    raise PullError("id %d: stored entry fe#%d matches an electric or fuel-cell record that is not listed as foreign (%s)"
                                    % (vid, r[0], o[0]["name"]))
                lines.append("    stay " + fmt_stored(r) + "   <= %s" % "; ".join(sorted({rec["name"] for rec in o}))[:90])
            elif f and o:
                raise PullError("id %d: stored entry fe#%d matches both a foreign and an own EPA record -- needs a ruling" % (vid, r[0]))
            else:
                raise PullError("id %d: stored entry fe#%d (%s/%s/%s %s %s %s) matches no EPA record -- needs a look"
                                % (vid, r[0], d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE]))
        for ln in lines:
            say(ln)
        if len(out_ids) != op["out"]:
            raise PullError("id %d: %d foreign entries found, %d expected" % (vid, len(out_ids), op["out"]))
        if len(out_ids) == len(cur_rows):
            raise PullError("id %d: every entry is foreign -- this needs a replace op, not a remove op" % vid)
        p["delete_ids"] = out_ids

    elif op["kind"] == "electric":
        if near != sorted(op["own"]):
            raise PullError("%d %s %s: EPA lists %r, expected %r" % (op["year"], op["make"], op["model"], near, op["own"]))
        new, seen = [], set()
        recs = [rec for n in near for rec in records(op["year"], op["make"], n)]
        for rec in recs:
            if rec["atv"] != "EV":
                raise PullError("EPA vehicle %s is typed %r, not EV" % (rec["epa_id"], rec["atv"]))
            key = (rec["comb"], rec["drive"], rec["trans"], rec["range"])
            if key not in seen:
                seen.add(key)
                new.append((electric_row(rec), rec))
        for r in cur_rows:                      # the stored entry must be this very car
            d = r[1:]
            if not any((d[CITY], d[HWY], d[COMB], d[TRANS], d[DRIVE]) == (rec["city"], rec["hwy"], rec["comb"], rec["trans"], rec["drive"]) for rec in recs):
                raise PullError("id %d: stored entry fe#%d does not match the EPA record of this car" % (vid, r[0]))
        p["delete_ids"] = [r[0] for r in cur_rows]
        p["insert"] = [x for x, _ in new]
        p["sources"] = [[rec["name"], rec["epa_id"], rec["atv"]] for _, rec in new]
        say("  OUT (%d):" % len(cur_rows))
        for r in cur_rows:
            say("    " + fmt_stored(r))
        say("  IN (%d):" % len(new))
        for x, rec in new:
            say("    " + fmt_new(x, rec))

    elif op["kind"] == "verify":
        stray = [n for n in near if not pref(n, [op["own_prefix"]])]
        if stray:
            raise PullError("%d %s %s: EPA lists %r beside the electric car -- needs a ruling" % (op["year"], op["make"], op["model"], stray))
        recs = [rec for n in near for rec in records(op["year"], op["make"], n)]
        if any(rec["atv"] != "EV" for rec in recs):
            raise PullError("%d %s %s: a record is not typed EV" % (op["year"], op["make"], op["model"]))
        for r in cur_rows:
            d = r[1:]
            hit = [rec for rec in recs if (d[MPGE], d[TRANS], d[DRIVE]) == (rec["comb"], rec["trans"], rec["drive"])]
            if not hit or d[FTYPE] != "Electric" or d[COMB] is not None:
                raise PullError("id %d: stored entry fe#%d is not an electric entry of this car" % (vid, r[0]))
            say("    stay " + fmt_stored(r) + "   <= %s [EV]" % hit[0]["name"])
        say("  EPA lists only the electric car for this year (%d names, %d records, all typed EV): NO CHANGE" % (len(near), len(recs)))
    return p


# ---------------------------------------------------------------------------- plan hash, apply
def plan_sha(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def after_rows(p):
    """Data columns the vehicle must hold after the op, in id order: untouched entries first, then the new ones."""
    gone = set(p["delete_ids"])
    return [r[1:] for r in p["current"] if r[0] not in gone] + [list(x) for x in p["insert"]]


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
        if p["insert"]:
            cur.executemany("INSERT INTO fuel_economy (vehicle_id, " + COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            [[vid] + list(x) for x in p["insert"]])
            cur.execute("INSERT OR REPLACE INTO pull_log (vehicle_id, endpoint, status, pulled_at) VALUES (?,?,?,?)",
                        (vid, "fuel-economy", "ok", p["pulled_at"]))
        if [r[1:] for r in stored(cur, vid)] != after_rows(p):
            raise RuntimeError("target %d does not hold the planned entries" % vid)


def bare_count(cur):
    return cur.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                       "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) "
                       "WHERE source='owner-manual-verified'").fetchone()[0]


def totals(plan):
    return sum(len(p["delete_ids"]) for p in plan), sum(len(p["insert"]) for p in plan)


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
        out, inn = totals(plan)
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
    changing = {p["id"]: p for p in plan if p["delete_ids"] or p["insert"]}
    still = {p["id"]: p for p in plan if not (p["delete_ids"] or p["insert"])}
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
            say("  UNEXPECTED: id %d changed although it is not in the plan (or is verify-only)" % vid)
            bad += 1
    for vid, p in changing.items():
        for m in after[vid].get("mpg") or []:
            if p["kind"] == "electric":
                ok = bool(m.get("mpge")) and m.get("comb") is None and not m.get("eng")
            else:
                ok = all(isinstance(m.get(k), int) for k in ("city", "hwy", "comb")) and bool(m.get("eng")) and not m.get("mpge")
            if not ok:
                say("  UNEXPECTED entry shape after repair on id %d: %r" % (vid, m))
                bad += 1
        if not after[vid].get("mpg"):
            say("  UNEXPECTED: id %d would ship no fuel-economy entry" % vid)
            bad += 1
    if bad:
        return False
    ver = sorted(v for v in changing if isinstance(before[v].get("oil"), dict) and before[v]["oil"].get("ver") == 1)
    n_ver = sum(1 for v in after.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    say("  build gates passed on both copies; vehicles %d -> %d; owner's-manual-verified %d (unchanged)" % (len(before), len(after), n_ver))
    say("  %d vehicles differ, each in the fuel-economy key only; %d verify-only vehicle(s) unchanged; all other %d vehicles identical"
        % (len(changing), len(still), len(after) - len(changing) - len(still)))
    say("  verified vehicles among the changed ones: %s (their curated specs are identical before and after)" % ver)
    say("  fuel-economy rows %d -> %d (%d out, %d in); bare owner-manual rows %d" % (n0, n1, out, inn, BARE_FROZEN))
    say("  every shipped entry on the 34 gasoline-side vehicles has city / highway / combined, an engine size and no MPGe; "
        "the I-Pace entries carry MPGe and no MPG")
    return True


# ---------------------------------------------------------------------------- dry run / write
def dry_run():
    say("FUEL-ECONOMY SIBLING REPAIR -- DRY RUN (nothing is written)  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        if bare_count(cur) != BARE_FROZEN:
            sys.exit("bare owner-manual rows are not %d" % BARE_FROZEN)
        plan = [plan_op(cur, op) for op in OPS]
    finally:
        con.close()
    say("")
    say("SUMMARY")
    for kind in ("replace", "remove", "electric", "verify"):
        ps = [p for p in plan if p["kind"] == kind]
        say("  %-8s %2d vehicles: %3d entries out, %3d entries in" % (kind, len(ps), sum(len(p["delete_ids"]) for p in ps),
                                                                   sum(len(p["insert"]) for p in ps)))
    out, inn = totals(plan)
    say("  total    %2d vehicles: %3d entries out, %3d entries in" % (len(plan), out, inn))
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
        bare = bare_count(cur)
        fleet = cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        n0 = cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    bak = "%s.bak_fe_siblings_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    out, inn = totals(plan)
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
    changed = [p["id"] for p in plan if p["delete_ids"] or p["insert"]]
    say("WRITTEN: fuel economy changed on %d vehicles (%d entries out, %d in); fuel-economy rows %d -> %d; fleet %d; bare rows %d"
        % (len(changed), out, inn, n0, n1, fleet, BARE_FROZEN))


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
