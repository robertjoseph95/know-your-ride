#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_add_hyundai_rows_venue.py -- missing-model-year pilot, step A (rulings R1-R6, 2026-11-14)

Adds the Hyundai Venue model years the fleet lacks (2022, 2023, 2024, 2025) as vehicle rows that
carry GOVERNMENT data only:

    EPA fueleconomy.gov      -> fuel_economy
    NHTSA recalls            -> recalls
    NHTSA safety ratings     -> safety_ratings
    NHTSA complaints         -> complaints          (all of them; no cap)
    one pull_log line per endpoint, 'ok' or 'empty'

It writes NO curated specification (oil / fluids / parts / torque / maintenance): those come from
the owner's manual in the separate curated-spec slice. It writes NO reliability, warranty or
service-cost rows (R2).

R1 (a row needs BOTH): a self-identified manufacturer book for the model year (BOOKS below) AND a
NHTSA vPIC listing of the model for that year (checked live on every dry run).

STATUS-AWARE PULLS: an answer is judged by its HTTP status AND its body. 'ok' needs an HTTP 200
whose body parses and whose own count matches its rows. 'empty' needs either that with count 0, or
the one shape NHTSA uses for "nothing matched": HTTP 400 with a well-formed JSON body saying count 0
(seen 2026-11-14 on recallsByVehicle). Because NHTSA gives an unknown model that same answer, an
'empty' also needs a positive control: another year of the same make / model spelling that returned
rows on that endpoint in the same run. Anything else stops the run. An error is never 'empty'.

    python _add_hyundai_rows_venue.py
        DRY RUN. Pulls, prints every row it would insert, rehearses the real build against an
        in-memory copy of the database, saves the plan to PLAN_FILE and prints its sha256.
        Touches nothing in wrench_vehicles.db.

    python _add_hyundai_rows_venue.py --write --sha <sha256 printed by the dry run>
        Backs up the database, then inserts EXACTLY the saved plan (no new pull).
"""
import contextlib
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import socket
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_add_hyundai_rows_venue_plan_cache.json")     # gitignored (*_cache.json)
WRITE = "--write" in sys.argv

MAKE, MODEL = "Hyundai", "Venue"
TARGETS = [(38718, 2022), (38719, 2023), (38720, 2024), (38721, 2025)]        # (vehicle id, model year)
BARE_FROZEN = 424                                                             # IC-02: untouched here, checked anyway

# R1, part one: the manufacturer book that identifies itself as this model year.
BOOKS = {
    2022: ("_hyundai_manuals/venue/venue_2022_portal_OM.pdf",
           "US portal, folder 2022, file 2022-Venue-Owners-Manual.pdf; PDF title '2022 Venue Owners Manual'; Copyright 2021; 390 pp"),
    2023: ("_hyundai_manuals/venue/venue_2023_portal_OM.pdf",
           "US portal, folder 2023, file 2023-Venue-OM.pdf; PDF title \"2023 Venue Owner's Manual\"; Copyright 2022; 403 pp"),
    2024: ("_hyundai_manuals/venue/venue_2024_portal_OM.pdf",
           "US portal, folder 2024, file '2024 Venue OM.pdf'; cover page reads '2024 Owner's Manual VENUE'; Copyright 2023; 410 pp"),
    2025: ("_hyundai_manuals/venue/venue_2025_QX_global_OM.pdf",
           "second host QX/2025 only (the portal serves no 2025 book); no cover naming the year; "
           "Copyright 2025; 413 pp; first posted 2024-10-16; the host carries a separate QX/2026 label"),
}

# The engine table each of these four books prints on its page 2-7 (read 2026-11-14):
#   ENGINE | Smartstream G1.6 | Displacement 97.5 cu.in (1,598 cc) | No. of cylinders 4, in-line
BOOK_ENGINE = {y: {"page": "2-7", "cc": 1598, "cylinders": 4, "layout": "in-line"} for y in (2022, 2023, 2024, 2025)}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
EPA = "https://www.fueleconomy.gov/ws/rest/vehicle"
NHTSA = "https://api.nhtsa.gov"
VPIC = "https://vpic.nhtsa.dot.gov/api/vehicles"
PACE = 0.7                                   # seconds between requests
Q = urllib.parse.quote
REQUESTS = []                                # (what, status, bytes) for every request made
_last = [0.0]


class PullError(Exception):
    pass


def say(*a):
    print(" ".join(str(x) for x in a).encode("ascii", "replace").decode("ascii"))


def fetch(url, what, also=()):
    """(status, body). Status is 200, or one of `also` when the caller judges that answer by its body.
    Any other outcome raises PullError: an error is never 'empty'."""
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
                status = e.code
                body = e.read() if status in also else b""
                ra = (e.headers.get("Retry-After") or "").strip() if e.headers else ""
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            REQUESTS.append((what, "ERR", 0))
            if attempt < 3:
                time.sleep(5 * attempt)
                continue
            raise PullError("%s: %r" % (what, e))
        REQUESTS.append((what, status, len(body)))
        if status == 200 or status in also:
            return status, body
        if status == 429 and ra.isdigit() and int(ra) > 120:
            raise PullError("%s: HTTP 429 with Retry-After %ss -- stop and come back later" % (what, ra))
        if status in (429, 500, 502, 503, 504) and attempt < 3:
            time.sleep(int(ra) if ra.isdigit() else 10 * attempt)
            continue
        raise PullError("%s: HTTP %s" % (what, status))
    raise PullError("%s: no answer" % what)


def fetch_json(url, what):
    _, body = fetch(url, what)
    try:
        return json.loads(body.decode("utf-8"))
    except Exception as e:
        raise PullError("%s: HTTP 200 but the body is not JSON (%r)" % (what, e))


def fetch_xml(url, what):
    _, body = fetch(url, what)
    # The stdlib parser is only safe on XML that declares no entities: refuse any document type
    # declaration (no DOCTYPE means no external entities and no entity-expansion bombs) and any oversized body.
    if b"<!DOCTYPE" in body or b"<!ENTITY" in body or len(body) > 2000000:
        raise PullError("%s: HTTP 200 but the XML carries a document type declaration or is oversized" % what)
    try:
        return ET.fromstring(body)
    except Exception as e:
        raise PullError("%s: HTTP 200 but the body is not XML (%r; %d bytes)" % (what, e, len(body)))


NOTHING_MATCHED = ("Results returned successfully", "No results found for this request")


def nhtsa_list(url, what, count_key, results_key):
    """Rows of an NHTSA list endpoint, plus how the answer was judged.
    HTTP 200: the body's own count must equal its rows. HTTP 400: accepted ONLY as 'nothing matched', i.e. a
    well-formed JSON body with count 0, no rows and one of NHTSA's two stock messages. Anything else stops."""
    status, body = fetch(url, what, also=(400,))
    try:
        j = json.loads(body.decode("utf-8"))
    except Exception:
        raise PullError("%s: HTTP %s and the body is not JSON: %r" % (what, status, body[:160]))
    res, cnt, msg = j.get(results_key), j.get(count_key), j.get("Message") or j.get("message")
    if status == 200:
        if not isinstance(res, list) or cnt != len(res):
            raise PullError("%s: count %r does not match %s rows" % (what, cnt, res if res is None else len(res)))
        return res, "HTTP 200, count %d" % cnt
    if res == [] and cnt == 0 and msg in NOTHING_MATCHED:
        return [], "HTTP 400 with a well-formed body (count 0, message %r)" % msg
    raise PullError("%s: HTTP 400 that is not NHTSA's nothing-matched answer: %r" % (what, body[:200]))


# ---------------------------------------------------------------------------- R1 part two: vPIC listing
def vpic_listing(year):
    j = fetch_json("%s/GetModelsForMakeYear/make/%s/modelyear/%d?format=json" % (VPIC, Q(MAKE.lower()), year),
                   "vPIC models %d" % year)
    res = j.get("Results")
    if not isinstance(res, list) or j.get("Count") != len(res) or not res:
        raise PullError("vPIC models %d: Count %r does not match %s rows" % (year, j.get("Count"), len(res or [])))
    names = sorted({(x.get("Model_Name") or "").strip() for x in res})
    return MODEL in names, len(names)


# ---------------------------------------------------------------------------- EPA fuel economy
def epa(year):
    """('ok'|'empty', rows, records). Row mapping follows _pull_epa_mpg.py (engine = EPA 'displ' as printed)."""
    root = fetch_xml("%s/menu/model?year=%d&make=%s" % (EPA, year, Q(MAKE)), "EPA models %d" % year)
    models = [(mi.findtext("text") or "").strip() for mi in root.iter("menuItem")]
    if not models:
        raise PullError("EPA models %d: HTTP 200 but no model list for %s" % (year, MAKE))
    near = [m for m in models if MODEL.lower() in m.lower()]
    if MODEL not in models:
        return "empty", [], {"models_listed": len(models), "near": near}
    if near != [MODEL]:
        raise PullError("EPA models %d: more than one %s entry %r -- needs a ruling" % (year, MODEL, near))
    root = fetch_xml("%s/menu/options?year=%d&make=%s&model=%s" % (EPA, year, Q(MAKE), Q(MODEL)),
                     "EPA options %d" % year)
    opts = [((mi.findtext("value") or "").strip(), (mi.findtext("text") or "").strip()) for mi in root.iter("menuItem")]
    if not opts or not all(v.isdigit() for v, _ in opts):
        raise PullError("EPA options %d: HTTP 200 but no usable option list %r" % (year, opts))
    rows, recs, seen = [], [], set()
    for eid, text in opts:
        v = fetch_xml("%s/%s" % (EPA, eid), "EPA vehicle %s" % eid)

        def g(t):
            return (v.findtext(t) or "").strip()

        def num(t):
            x = g(t)
            try:
                return int(float(x)) if x != "" else None
            except ValueError:
                return None

        def na(n):                         # EPA prints 0 where a figure does not apply (range, EV figures)
            return n if n else None

        if (g("year"), g("make"), g("model")) != (str(year), MAKE, MODEL):
            raise PullError("EPA vehicle %s is %s %s %s, not %d %s %s" % (eid, g("year"), g("make"), g("model"), year, MAKE, MODEL))
        city, hwy, comb = num("city08"), num("highway08"), num("comb08")
        if city is None or hwy is None or comb is None:
            raise PullError("EPA vehicle %s: no city / highway / combined figure" % eid)
        row = [city, hwy, comb, num("fuelCost08"), g("displ") or None, g("trany") or None, g("drive") or None,
               g("fuelType") or None, na(num("range")), na(num("phevComb") or num("combE")),
               na(num("cityE")), na(num("highwayE")), na(num("combE"))]
        recs.append({"epa_id": eid, "option": text, "displ": g("displ"), "cylinders": g("cylinders"),
                     "trany": g("trany"), "drive": g("drive"), "fuelType": g("fuelType"), "VClass": g("VClass"),
                     "atvType": g("atvType"), "tCharger": g("tCharger"), "sCharger": g("sCharger")})
        key = (row[0], row[1], row[2], row[4], row[6])                     # city, hwy, comb, displ, drive
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    return "ok", rows, {"models_listed": len(models), "near": near, "records": recs}


# ---------------------------------------------------------------------------- NHTSA
def B(x):
    return 1 if (x is True or str(x).lower() == "true") else 0


def recalls(year):
    res, how = nhtsa_list("%s/recalls/recallsByVehicle?make=%s&model=%s&modelYear=%d" % (NHTSA, Q(MAKE), Q(MODEL), year),
                          "NHTSA recalls %d" % year, "Count", "results")
    rows = []
    for x in res:
        if not x.get("NHTSACampaignNumber"):
            raise PullError("NHTSA recalls %d: a row without a campaign number" % year)
        if str(x.get("ModelYear")) != str(year) or (x.get("Model") or "").upper() != MODEL.upper():
            raise PullError("NHTSA recalls %d: row is for %s %s" % (year, x.get("ModelYear"), x.get("Model")))
        rows.append([x["NHTSACampaignNumber"], x.get("Component"), (x.get("Summary") or "")[:2000],
                     (x.get("Remedy") or "")[:2000], B(x.get("parkIt"))])
    if len({r[0] for r in rows}) != len(rows):
        raise PullError("NHTSA recalls %d: a campaign number is listed twice" % year)
    return ("ok" if rows else "empty"), rows, how


def safety(year):
    res, how = nhtsa_list("%s/SafetyRatings/modelyear/%d/make/%s/model/%s" % (NHTSA, year, Q(MAKE), Q(MODEL)),
                          "NHTSA safety list %d" % year, "Count", "Results")
    variants = [[x.get("VehicleId"), x.get("VehicleDescription")] for x in res]
    if not variants:
        return "empty", None, variants, how
    d = fetch_json("%s/SafetyRatings/VehicleId/%s" % (NHTSA, variants[0][0]), "NHTSA safety %s" % variants[0][0])
    rr = d.get("Results")
    if not isinstance(rr, list) or len(rr) != 1:
        raise PullError("NHTSA safety %s: expected one result" % variants[0][0])
    r0 = rr[0]
    if str(r0.get("ModelYear")) != str(year) or (r0.get("Model") or "").upper() != MODEL.upper():
        raise PullError("NHTSA safety %s is %s %s" % (variants[0][0], r0.get("ModelYear"), r0.get("Model")))

    def g(k):
        v = r0.get(k)
        if v in ("", "Not Rated", None):
            return None
        return int(v) if str(v).isdigit() else v

    row = [g("OverallRating"), g("FrontCrashDriversideRating"), g("FrontCrashPassengersideRating"),
           g("SideCrashDriversideRating"), g("SideCrashPassengersideRating"), g("RolloverRating"),
           r0.get("RolloverPossibility"), g("SidePoleCrashRating") or g("combinedSideBarrierAndPoleRating-Front")]
    return "ok", row, variants, how


def complaints(year):
    res, how = nhtsa_list("%s/complaints/complaintsByVehicle?make=%s&model=%s&modelYear=%d" % (NHTSA, Q(MAKE), Q(MODEL), year),
                          "NHTSA complaints %d" % year, "count", "results")
    rows, vins = [], []
    for x in sorted(res, key=lambda x: x.get("odiNumber") or 0, reverse=True):
        if not x.get("odiNumber"):
            raise PullError("NHTSA complaints %d: a row without an ODI number" % year)
        prods = [p for p in (x.get("products") or []) if (p.get("type") or "").lower() == "vehicle"]
        if prods and not any(str(p.get("productYear")) == str(year) and (p.get("productModel") or "").upper() == MODEL.upper()
                             for p in prods):
            raise PullError("NHTSA complaints %d: ODI %s is not filed against this vehicle" % (year, x.get("odiNumber")))
        rows.append([str(x["odiNumber"]), x.get("components"), (x.get("summary") or "")[:2000], x.get("dateOfIncident"),
                     B(x.get("crash")), B(x.get("fire")), x.get("numberOfInjuries") or 0, x.get("numberOfDeaths") or 0])
        if x.get("vin"):
            vins.append(str(x["vin"]).strip().upper())
    if len({r[0] for r in rows}) != len(rows):
        raise PullError("NHTSA complaints %d: an ODI number is listed twice" % year)
    return ("ok" if rows else "empty"), rows, vins, how


def vpic_decode(year, vins):
    """Identity cross-check only: decode up to three distinct NHTSA-complaint VIN prefixes with vPIC. A prefix
    decode names make, model, model year and displacement; it does not give cylinder count or layout."""
    out, tried = [], []
    for vin in vins:
        key = vin[:8] + vin[9:11] if len(vin) >= 11 else vin
        if len(vin) < 11 or key in tried:
            continue
        tried.append(key)
        j = fetch_json("%s/DecodeVinValues/%s?format=json" % (VPIC, Q(vin)), "vPIC decode %d" % year)
        r0 = (j.get("Results") or [{}])[0]
        out.append({"vin_prefix": vin, "Make": r0.get("Make"), "Model": r0.get("Model"), "ModelYear": r0.get("ModelYear"),
                    "EngineConfiguration": r0.get("EngineConfiguration"), "EngineCylinders": r0.get("EngineCylinders"),
                    "DisplacementL": r0.get("DisplacementL"), "FuelTypePrimary": r0.get("FuelTypePrimary"),
                    "DriveType": r0.get("DriveType"), "ErrorCode": r0.get("ErrorCode")})
        if len(tried) == 3:
            break
    return out


def engine_string(epa_recs, year):
    """'<displ>L I<cyl>' in the fleet's style, ONLY when every part is sourced: displacement and cylinder count
    from the EPA record (R3), agreeing with the book's engine table, which also states the in-line layout."""
    pairs = sorted({(r["displ"], r["cylinders"]) for r in epa_recs})
    if len(pairs) != 1 or not pairs[0][0] or not pairs[0][1]:
        return None, "EPA does not give one displacement / cylinder count (%r)" % pairs
    displ, cyl = pairs[0]
    be = BOOK_ENGINE.get(year)
    if not be:
        return None, "no engine table recorded for the %d book" % year
    if "%.1f" % (be["cc"] / 1000.0) != "%.1f" % float(displ) or str(be["cylinders"]) != cyl:
        return None, "EPA %s L / %s cyl disagrees with the book (%d cc, %d cylinders)" % (displ, cyl, be["cc"], be["cylinders"])
    if be["layout"] != "in-line":
        return None, "the book states layout %r" % be["layout"]
    return "%sL I%s" % (displ, cyl), ("EPA: %s L, %s cyl; book p.%s: %s cc, %d cylinders, %s"
                                       % (displ, cyl, be["page"], format(be["cc"], ","), be["cylinders"], be["layout"]))


# ---------------------------------------------------------------------------- plan
def canon(targets):
    return json.dumps(targets, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def plan_sha(targets):
    return hashlib.sha256(canon(targets).encode("ascii")).hexdigest()


def bare_count(cur):
    """Rows whose source is the bare token, across the four gated tables (IC-02 freeze; same query as the write scripts)."""
    return cur.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                       "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) "
                       "WHERE source='owner-manual-verified'").fetchone()[0]


def preflight(cur):
    n, mx = cur.execute("SELECT COUNT(*), MAX(id) FROM vehicles").fetchone()
    for vid, year in TARGETS:
        hit = cur.execute("SELECT id, year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        if hit:
            sys.exit("id %d is taken: %r" % (vid, tuple(hit)))
        dup = cur.execute("SELECT id FROM vehicles WHERE year=? AND upper(make)=? AND upper(model)=?",
                          (year, MAKE.upper(), MODEL.upper())).fetchall()
        if dup:
            sys.exit("%d %s %s already exists as id %r" % (year, MAKE, MODEL, [d[0] for d in dup]))
        for t in ("fuel_economy", "recalls", "safety_ratings", "complaints", "pull_log", "oil_change", "fluids",
                  "parts", "torque_specs", "maintenance", "reliability", "warranty", "service_costs"):
            if cur.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id=?" % t, (vid,)).fetchone()[0]:
                sys.exit("table %s already holds rows for the unused id %d" % (t, vid))
    if mx != TARGETS[0][0] - 1:
        sys.exit("highest vehicle id is %s, expected %d" % (mx, TARGETS[0][0] - 1))
    return n


def apply(cur, targets):
    for t in targets:
        vid = t["id"]
        cur.execute("INSERT INTO vehicles (id, year, make, model, engine, trim, pulled_at) VALUES (?,?,?,?,?,?,?)",
                    (vid, t["year"], t["make"], t["model"], t["engine"], None, t["pulled_at"]))
        cur.executemany("""INSERT INTO fuel_economy (vehicle_id, city_mpg, highway_mpg, combined_mpg, annual_fuel_cost,
                           engine, transmission, drive, fuel_type, range_miles, mpge, city_ev, hwy_ev, comb_ev)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [[vid] + r for r in t["fuel_economy"]])
        cur.executemany("INSERT INTO recalls (vehicle_id, campaign_number, component, summary, remedy, park_it) "
                        "VALUES (?,?,?,?,?,?)", [[vid] + r for r in t["recalls"]])
        if t["safety"] is not None:
            cur.execute("""INSERT INTO safety_ratings (vehicle_id, overall_rating, frontal_crash_driver,
                           frontal_crash_passenger, side_crash_driver, side_crash_passenger, rollover_rating,
                           rollover_risk_pct, side_pole_rating) VALUES (?,?,?,?,?,?,?,?,?)""", [vid] + t["safety"])
        cur.executemany("""INSERT INTO complaints (vehicle_id, complaint_number, component, summary, incident_date,
                           crash, fire, injury, deaths) VALUES (?,?,?,?,?,?,?,?,?)""", [[vid] + r for r in t["complaints"]])
        cur.executemany("INSERT INTO pull_log (vehicle_id, endpoint, status, pulled_at) VALUES (?,?,?,?)",
                        [(vid, ep, st, t["pulled_at"]) for ep, st in t["log"]])


def expected_counts(targets):
    return {"vehicles": len(targets), "fuel_economy": sum(len(t["fuel_economy"]) for t in targets),
            "recalls": sum(len(t["recalls"]) for t in targets),
            "safety_ratings": sum(1 for t in targets if t["safety"] is not None),
            "complaints": sum(len(t["complaints"]) for t in targets), "pull_log": sum(len(t["log"]) for t in targets)}


def stored_counts(cur, targets):
    ids = [t["id"] for t in targets]
    ph = ",".join("?" * len(ids))
    out = {"vehicles": cur.execute("SELECT COUNT(*) FROM vehicles WHERE id IN (%s)" % ph, ids).fetchone()[0]}
    for tb in ("fuel_economy", "recalls", "safety_ratings", "complaints", "pull_log"):
        out[tb] = cur.execute("SELECT COUNT(*) FROM %s WHERE vehicle_id IN (%s)" % (tb, ph), ids).fetchone()[0]
    return out


# ---------------------------------------------------------------------------- rehearsal on an in-memory copy
def rehearse(targets):
    """Apply the plan to an in-memory copy and run the REAL build's gates and data assembly on it."""
    src = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    mem.row_factory = sqlite3.Row
    cur = mem.cursor()
    before = cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    apply(cur, targets)
    mem.commit()
    sys.path.insert(0, os.path.join(ROOT, "files"))
    spec = importlib.util.spec_from_file_location("kyr_build_04", os.path.join(ROOT, "files", "04_rebuild_demo.py"))
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    bad = []
    for t in targets:
        for comp in sorted({r[1] if r[1] is not None else "" for r in t["complaints"]}):
            try:
                b._component_topics(comp)
            except SystemExit as e:
                bad.append((t["year"], comp, str(e)))
    if bad:
        say("  REHEARSAL FAILED: NHTSA component labels the build's frozen vocabulary does not know:")
        for y, c, e in bad:
            say("    %d  %r" % (y, c))
        return False
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            b._assert_registry_admission(cur)
            b.assert_frozen_landscape(cur)
            vlist, dtc, fixes, with_comps = b.build_data(cur)
            b._strip_unverified(vlist)
            b._assert_ic01_projection(vlist)
    except SystemExit as e:
        say("  REHEARSAL FAILED: the build stopped:", e)
        return False
    verified = sum(1 for v in vlist if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    say("  build gates passed on the in-memory copy; vehicles %d -> %d; owner's-manual-verified %d (unchanged)"
        % (before, len(vlist), verified))
    by = {v["id"]: v for v in vlist}
    for t in targets:
        v = by[t["id"]]
        ca = v.get("comps_agg") or {}
        say("  ships for id %d (%d): keys %s" % (t["id"], t["year"], sorted(k for k in v if v[k] not in (None, [], {}))))
        say("      engine %r | mpg rows %d | recalls %d | safety overall %r | complaints n=%s through %s; topics %s"
            % (v.get("engine"), len(v.get("mpg") or []), len(v.get("recalls") or []),
               (v.get("safety") or {}).get("overall"), ca.get("n"), ca.get("through"), ca.get("topics")))
        for k in ("oil", "fluids", "parts", "torque", "maint"):
            if v.get(k):
                say("      UNEXPECTED curated key %s" % k)
                return False
    mem.close()
    return True


# ---------------------------------------------------------------------------- dry run
def dry_run():
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    cur = con.cursor()
    fleet = preflight(cur)
    bare = bare_count(cur)
    con.close()
    say("DRY RUN -- nothing is written to wrench_vehicles.db")
    say("fleet today: %d vehicles; ids %d-%d are free; no %s %s row exists for %s"
        % (fleet, TARGETS[0][0], TARGETS[-1][0], MAKE, MODEL, ", ".join(str(y) for _, y in TARGETS)))
    targets, flags = [], []
    for vid, year in TARGETS:
        say("")
        say("=" * 100)
        say("%d %s %s  ->  vehicle id %d" % (year, MAKE, MODEL, vid))
        book, why = BOOKS[year]
        on_disk = os.path.exists(os.path.join(ROOT, book))
        say("  R1 book   : %s  [%s]" % (book, "on disk" if on_disk else "NOT ON DISK"))
        say("              %s" % why)
        if not on_disk:
            flags.append("%d: the book file is not on disk" % year)
        listed, n_models = vpic_listing(year)
        say("  R1 vPIC   : %s listed for model year %d (%d %s models listed)" % ("IS" if listed else "IS NOT", year, n_models, MAKE))
        if not listed:
            sys.exit("R1 fails for %d: vPIC does not list %s" % (year, MODEL))
        pulled_at = datetime.datetime.now().isoformat()
        e_st, e_rows, e_info = epa(year)
        r_st, r_rows, r_how = recalls(year)
        s_st, s_row, s_var, s_how = safety(year)
        c_st, c_rows, vins, c_how = complaints(year)
        decodes = vpic_decode(year, vins)
        eng, eng_why = engine_string(e_info.get("records", []), year)
        for d in decodes:
            if ((d.get("Make") or "").upper(), (d.get("Model") or "").upper(), str(d.get("ModelYear"))) != (MAKE.upper(), MODEL.upper(), str(year)):
                flags.append("%d: vPIC decodes complaint VIN prefix %s as %s %s %s" % (year, d["vin_prefix"], d.get("ModelYear"), d.get("Make"), d.get("Model")))

        say("  EPA fuel economy [%s]: %d record(s) -> %d row(s) after the duplicate-trim rule" % (e_st, len(e_info.get("records", [])), len(e_rows)))
        for rec in e_info.get("records", []):
            say("      EPA id %s: %s | displ %s | cyl %s | %s | %s | turbo %r | class %s"
                % (rec["epa_id"], rec["option"], rec["displ"], rec["cylinders"], rec["drive"], rec["fuelType"],
                   rec["tCharger"], rec["VClass"]))
        for r in e_rows:
            say("      ROW city %s / hwy %s / comb %s | $%s per year | engine %r | %s | %s | %s | range %r mpge %r"
                % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]))
        say("  identity cross-check, vPIC decode of NHTSA complaint VIN prefixes: %d" % len(decodes))
        for d in decodes:
            say("      %s -> %s %s %s | %s L | %s" % (d["vin_prefix"], d["ModelYear"], d["Make"], d["Model"],
                                                   d["DisplacementL"], d["FuelTypePrimary"]))
        say("  engine string: %r  (%s)" % (eng, eng_why))
        if eng is None:
            flags.append("%d: engine string left empty -- %s" % (year, eng_why))
        say("  NHTSA recalls [%s]: %d   (%s)" % (r_st, len(r_rows), r_how))
        for r in r_rows:
            say("      %s | %s | park-it %d | %s" % (r[0], r[1], r[4], r[2][:110].replace("\n", " ")))
        say("  NHTSA safety ratings [%s]: variants %r   (%s)" % (s_st, s_var, s_how))
        if len(s_var) > 1:
            flags.append("%d: NHTSA lists %d rated variants; the first is used, as the older pull does" % (year, len(s_var)))
        if s_row is not None:
            say("      ROW overall %r | front driver %r | front passenger %r | side driver %r | side passenger %r | "
                "rollover %r | rollover risk %r | side pole %r" % tuple(s_row))
        say("  NHTSA complaints [%s]: %d, all stored, no cap   (%s)" % (c_st, len(c_rows), c_how))
        if c_rows:
            say("      crash %d | fire %d | injuries %d | deaths %d | blank component %d | with VIN prefix %d"
                % (sum(r[4] for r in c_rows), sum(r[5] for r in c_rows), sum(r[6] for r in c_rows),
                   sum(r[7] for r in c_rows), sum(1 for r in c_rows if not (r[1] or "").strip()), len(vins)))
            badd = [r[3] for r in c_rows if r[3] and not re.match(r"^\d{2}/\d{2}/\d{4}$", r[3])]
            if badd:
                flags.append("%d: %d complaint dates are not MM/DD/YYYY, e.g. %r" % (year, len(badd), badd[0]))
            for r in c_rows[:3]:
                say("      e.g. ODI %s | %s | incident %s | crash %d fire %d inj %d deaths %d"
                    % (r[0], r[1], r[3], r[4], r[5], r[6], r[7]))
        log = [["fuel-economy", e_st], ["recalls", r_st], ["safety-ratings", s_st], ["complaints", c_st]]
        say("  pull_log: %s" % ", ".join("%s=%s" % (a, c) for a, c in log))
        say("  NOT written (R2): reliability, warranty, service_costs. NOT written here: any curated spec.")
        targets.append({"id": vid, "year": year, "make": MAKE, "model": MODEL, "engine": eng, "pulled_at": pulled_at,
                        "book": book, "book_basis": why, "fuel_economy": e_rows, "recalls": r_rows, "safety": s_row,
                        "complaints": c_rows, "log": log,
                        "evidence": {"epa": e_info, "safety_variants": s_var, "vpic_decodes": decodes, "engine_basis": eng_why,
                                     "answers": {"recalls": r_how, "safety-ratings": s_how, "complaints": c_how}}})
    # an 'empty' needs a positive control: the same make / model spelling returning rows on that endpoint for another year
    for ep in ("fuel-economy", "recalls", "safety-ratings", "complaints"):
        st = [dict(t["log"])[ep] for t in targets]
        if "empty" in st and "ok" not in st:
            flags.append("%s is empty for every year: no positive control for the spelling %r / %r on that endpoint" % (ep, MAKE, MODEL))
    say("")
    say("=" * 100)
    say("REHEARSAL (in-memory copy of the database + the real build code)")
    ok = rehearse(targets)
    exp = expected_counts(targets)
    say("")
    say("TOTAL rows the write would insert: " + ", ".join("%s %d" % kv for kv in exp.items()))
    say("fleet total would become %d (verified count unchanged; bare owner-manual rows %d, frozen at %d)"
        % (fleet + len(targets), bare, BARE_FROZEN))
    bad = [r for r in REQUESTS if r[1] != 200]
    say("requests made: %d; answers other than HTTP 200: %d %s" % (len(REQUESTS), len(bad), bad if bad else ""))
    if flags:
        say("FLAGS:")
        for f in flags:
            say("  - " + f)
    if not ok:
        sys.exit("rehearsal failed -- no plan saved")
    sha = plan_sha(targets)
    with io.open(PLAN_FILE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"script": os.path.basename(__file__), "sha256": sha, "targets": targets}, fh, sort_keys=True, indent=1)
    say("plan saved: %s" % PLAN_FILE)
    say("plan sha256: %s" % sha)
    say("to write exactly this plan (only on Robert's go):  python %s --write --sha %s" % (os.path.basename(__file__), sha))


# ---------------------------------------------------------------------------- write
def write():
    if "--sha" not in sys.argv:
        sys.exit("--write needs --sha <the sha256 a dry run printed>")
    want = sys.argv[sys.argv.index("--sha") + 1]
    with io.open(PLAN_FILE, encoding="utf-8") as fh:
        plan = json.load(fh)
    targets = plan["targets"]
    got = plan_sha(targets)
    if got != want or plan.get("sha256") != want:
        sys.exit("plan file hash %s does not match --sha %s: run the dry run again and get a fresh go" % (got, want))
    if [(t["id"], t["year"]) for t in targets] != TARGETS or any((t["make"], t["model"]) != (MAKE, MODEL) for t in targets):
        sys.exit("plan targets do not match this script")
    for t in targets:
        if not os.path.exists(os.path.join(ROOT, t["book"])):
            sys.exit("R1: the %d book is not on disk (%s)" % (t["year"], t["book"]))
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:                                       # read-only checks first; the handle closes on every path
        cur = con.cursor()
        fleet = preflight(cur)
        bare = bare_count(cur)
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    bak = "%s.bak_venue_rows_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        apply(cur, targets)
        exp, got_n = expected_counts(targets), stored_counts(cur, targets)
        if exp != got_n:
            raise RuntimeError("stored %r, expected %r" % (got_n, exp))
        for t in targets:
            row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (t["id"],)).fetchone()
            if tuple(row) != (t["year"], MAKE, MODEL):
                raise RuntimeError("id %d holds %r" % (t["id"], tuple(row)))
        if cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] != fleet + len(targets):
            raise RuntimeError("fleet count is off")
        if bare_count(cur) != BARE_FROZEN:
            raise RuntimeError("bare owner-manual count moved")
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise
    con.close()
    say("WRITTEN: " + ", ".join("%s %d" % kv for kv in exp.items()))
    say("fleet total is now %d" % (fleet + len(targets)))


if __name__ == "__main__":
    if WRITE:
        write()
    else:
        try:
            dry_run()
        except PullError as e:
            say("")
            say("STOPPED -- a pull did not return a clean answer, so nothing was recorded for it:")
            say("   ", e)
            say("requests so far:", REQUESTS)
            sys.exit(2)
