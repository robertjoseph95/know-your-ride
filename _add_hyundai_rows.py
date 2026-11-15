#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_add_hyundai_rows.py -- add missing Hyundai model-year rows with GOVERNMENT data only (step A of the two-step method)

Reusable successor of _add_hyundai_rows_venue.py (the Venue 2022-2025 pilot, rulings R1-R6 of 2026-11-14). One batch
per run, defined in BATCHES below. A new vehicle row carries:

    EPA fueleconomy.gov      -> fuel_economy
    NHTSA recalls            -> recalls
    NHTSA safety ratings     -> safety_ratings
    NHTSA complaints         -> complaints          (all of them; no cap)
    one pull_log line per endpoint, 'ok' or 'empty'

It writes NO curated specification (oil / fluids / parts / torque / maintenance): those come from the owner's manual
in the separate curated-spec slice. It writes NO reliability, warranty or service-cost rows.

A ROW NEEDS BOTH: a manufacturer book that identifies itself as the model year (BATCHES[..]["books"]) AND an NHTSA
vPIC listing of the model for that year (checked live on every dry run).

STATUS-AWARE PULLS: an answer is judged by its HTTP status AND its body. 'ok' needs an HTTP 200 whose body parses and
whose own count matches its rows. 'empty' needs either that with count 0, or the one shape NHTSA uses for "nothing
matched": HTTP 400 with a well-formed JSON body saying count 0. Because NHTSA gives an unknown model that same
answer, an 'empty' also needs a positive control (rows on that endpoint for the same make / model spelling in the
same run); a batch without one is flagged. Anything else stops the run. An error is never 'empty'.

ENGINE LABEL: '<displ>L <layout letter><cyl>' (several engines joined by ' / ') only when every part is sourced.
Displacement and cylinder count come from the EPA record and must agree with the book's engine table. The layout comes
from the book when it prints one, else from a vPIC decode of an NHTSA-complaint VIN prefix for that model year; with
neither, the label stays empty.

EPA MODEL NAMES: EPA may list a nameplate under several names. Each batch states the names that belong to the row
(epa_models) and the names of DIFFERENT vehicles that merely share the word (epa_ignore, e.g. an electric sibling with
its own manual). Any other name stops the run for a ruling.

REPAIR DRAFT (optional, per batch): repair_fuel_economy lists EXISTING rows of the same nameplate whose fuel-economy
rows are to be replaced from EPA under the same rules. The dry run shows current rows beside proposed rows. The write
replaces them only when the stored rows still equal what the dry run showed; --skip-repairs writes the new rows only.

    python _add_hyundai_rows.py <batch>
        DRY RUN. Pulls, prints every row it would insert, rehearses the real build against an in-memory copy of the
        database, saves the plan next to this script and prints its sha256. Touches nothing in wrench_vehicles.db.

    python _add_hyundai_rows.py <batch> --write --sha <sha256 printed by the dry run> [--skip-repairs]
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
BARE_FROZEN = 424                                                             # IC-02: untouched here, checked anyway

# ----------------------------------------------------------------------------------------------------------------
# One entry per batch. targets: (vehicle id, model year). books: the manufacturer book that identifies itself as the
# model year. book_engine: the engine table that book prints (layout None when the table states none).
# epa_models: every model name EPA lists for this nameplate and year; any other name stops the run for a ruling.
# ----------------------------------------------------------------------------------------------------------------
BATCHES = {
    "palisade-2023": dict(
        make="Hyundai", model="Palisade",
        targets=[(38722, 2023)],
        books={2023: ("_hyundai_manuals/palisade/palisade_2023_portal_OM.pdf",
                      "US portal, folder 2023, file 2023-Palisade-Owners-Manual.pdf; PDF title \"2023 Palisade Owner's "
                      "Manual\"; Copyright 2022; created 2022-05-24; 661 pp; overall length 196.65 in (the facelift body)")},
        # p.2-8: ENGINE | 3.8 GDI | 230.55 cu. in (3,778 cc) | 3.78 x 3.43 in | firing order 1-2-3-4-5-6 | No. of cylinders 6
        book_engine={2023: dict(page="2-8", cc=3778, cylinders=6, layout=None)},
        epa_models={2023: ["Palisade AWD", "Palisade FWD"]},
    ),
    "kona-missing-years": dict(
        make="Hyundai", model="Kona",
        targets=[(38723, 2018), (38724, 2019), (38725, 2023), (38726, 2025)],
        books={
            2018: ("_hyundai_manuals/kona/kona_2018_OS_portal_OM.pdf",
                   "US portal, folder 2018, file '2018 Kona Owners Manual.pdf'; Copyright 2017; PDF created 2017-12-01; "
                   "463 pp; 2018 is the Kona's first US model year"),
            2019: ("_hyundai_manuals/kona/kona_2019_OS_portal_OM.pdf",
                   "US portal, folder 2019, file '2019 Kona OM.pdf'; Copyright 2018; PDF created 2018-09-26; 485 pp; its "
                   "own edition between the 2018 book and the titled 2020 book"),
            2023: ("_hyundai_manuals/kona/kona_2023_portal_OM.pdf",
                   "US portal, folder 2023, file 2023-Kona-OM.pdf; PDF title \"2023 Kona Owner's Manual\"; Copyright 2022; "
                   "PDF created 2022-07-14; 602 pp"),
            2025: ("_hyundai_manuals/kona/kona_2025_SX2_global_OM.pdf",
                   "second host SX2/2025 (the portal serves no book for 2024 or later); PDF keywords "
                   "'en_US,hyundai,SX2,2025,engine,1.3' name the year; Copyright 2024; 713 pp; first posted 2024-10-14"),
        },
        # 2018 / 2019 p.8-2: 1.6 T-GDI 97.09 cu.in (1,591 cc) and Nu 2.0 MPI 121.98 (1,999); "In-line 4 cylinder" for both.
        # 2023 p.2-9: Smartstream G1.6 T-GDi 97.5 (1,598) and Smartstream G2.0 Atkinson 121.9 (1,999); "In-line 4 cylinder".
        # 2025 p.25: Smartstream G1.6 T-GDi 97.51 (1,598) and Smartstream G2.0 Atkinson 121.98 (1,999); "No. of cylinders 4",
        #            no layout printed.
        book_engine={
            2018: dict(page="8-2", engines=[dict(cc=1591, cylinders=4, layout="in-line"), dict(cc=1999, cylinders=4, layout="in-line")]),
            2019: dict(page="8-2", engines=[dict(cc=1591, cylinders=4, layout="in-line"), dict(cc=1999, cylinders=4, layout="in-line")]),
            2023: dict(page="2-9", engines=[dict(cc=1598, cylinders=4, layout="in-line"), dict(cc=1999, cylinders=4, layout="in-line")]),
            2025: dict(page="25", engines=[dict(cc=1598, cylinders=4, layout=None), dict(cc=1999, cylinders=4, layout=None)]),
        },
        epa_models={y: ["Kona AWD", "Kona FWD"] for y in (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)},
        # Different vehicles with their own manuals; electrified systems are gated (ruling 2026-11-14).
        epa_ignore=["Kona Electric", "Kona N"],
        # Existing rows whose fuel economy the May pull filled from the electric sibling (ruling 2026-11-14: draft a repair).
        repair_fuel_economy=[(673, 2020), (2166, 2021), (3694, 2022), (6787, 2024)],
    ),
    "santa-cruz-missing-years": dict(
        make="Hyundai", model="Santa Cruz",
        targets=[(38727, 2022), (38728, 2023), (38729, 2024), (38730, 2025)],
        books={
            2022: ("_hyundai_manuals/santa_cruz/santa_cruz_2022_portal_OM.pdf",
                   "US portal, folder 2022, file 2022-Santa-Cruz-Owners-Manual.pdf; PDF title '2022 Santa Cruz Owners "
                   "Manual'; Copyright 2021; PDF created 2021-06-08; 598 pp; 2022 is the Santa Cruz's first model year "
                   "(vPIC and EPA list none for 2021)"),
            2023: ("_hyundai_manuals/santa_cruz/santa_cruz_2023_portal_OM.pdf",
                   "US portal, folder 2023, file '2023-Santa Cruz-OM.pdf'; Copyright 2022; PDF created 2022-11-17; 620 pp; "
                   "the same production file as second host NX4OB/2022 (same proof marks, dated 2022-11-01)"),
            2024: ("_hyundai_manuals/santa_cruz/santa_cruz_2024_NX4OB_global_OM.pdf",
                   "second host NX4OB/2024 (the portal serves no 2024 book: 168 file-name forms, all HTTP 404); Copyright "
                   "2023; 620 pp; pre-facelift body; differs from the 2023 book on 324 pages and carries the sections first "
                   "seen in the 2024 books of Venue, Palisade and Kona; accepted as the 2024 source by ruling 2026-11-14 "
                   "(supported, not provable against a titled book)"),
            2025: ("_hyundai_manuals/santa_cruz/santa_cruz_2025_NX4OB_global_OM.pdf",
                   "second host NX4OB/2025 (served, not on the US menu; the portal serves no 2025 book); book header "
                   "_NX4aOB_en_US; Copyright 2024; PDF created 2024-10-17; 575 pp; the facelift body; NX4OB/2026 holds a "
                   "separate Copyright-2026 book"),
        },
        # 2022 / 2023 / 2024 p.2-8 and 2025 p.10-2: ENGINE | Smartstream G 2.5 GDI and Smartstream G 2.5 T-GDI share ONE cell:
        # 152.4 cu. in (2,497 cc) | 3.5 x 4 in. (88.5 x 101.5 mm) | firing order 1-3-4-2 | No. of cylinders "4, in-line".
        book_engine={
            2022: dict(page="2-8", cc=2497, cylinders=4, layout="in-line"),
            2023: dict(page="2-8", cc=2497, cylinders=4, layout="in-line"),
            2024: dict(page="2-8", cc=2497, cylinders=4, layout="in-line"),
            2025: dict(page="10-2", cc=2497, cylinders=4, layout="in-line"),
        },
        # 2025: "Santa Cruz XRT AWD" is a trim of the same vehicle, covered by the same book (ruling 2026-11-14: take it).
        epa_models={
            2022: ["Santa Cruz AWD", "Santa Cruz FWD"],
            2023: ["Santa Cruz AWD", "Santa Cruz FWD"],
            2024: ["Santa Cruz AWD", "Santa Cruz FWD"],
            2025: ["Santa Cruz AWD", "Santa Cruz FWD", "Santa Cruz XRT AWD"],
        },
    ),
    "accent-missing-years": dict(
        make="Hyundai", model="Accent",
        # Eleven model years with a US-portal book (single prints; the second host serves no Accent). The fleet held
        # only the 1995-2002 rows (deferred, no manual). No book exists for 2003, 2004, 2007, 2009-2013 or 2015
        # (21 file-name forms each under portal folder 'accent', every answer HTTP 404), so those years get no row.
        targets=[(38731, 2005), (38732, 2006), (38733, 2008), (38734, 2014), (38735, 2016), (38736, 2017),
                 (38737, 2018), (38738, 2019), (38739, 2020), (38740, 2021), (38741, 2022)],
        books={
            2005: ("_hyundai_manuals/accent/accent_2005_portal_OM.pdf",
                   "US portal, folder 2005, file 2005_Hyundai_Accent_OM.pdf; the cover prints '2005 Owner's Manual' and "
                   "the Accent name; Copyright 2005; 219 pp; wheelbase 96.1 in, 4 door and 3 door"),
            2006: ("_hyundai_manuals/accent/accent_2006_portal_OM.pdf",
                   "US portal, folder 2006, file 2006_Hyundai_Accent_OM.pdf; the cover prints '2006 Owner's Manual' and "
                   "ACCENT; Copyright 2006; PDF created 2006-01-24; 278 pp; wheelbase 98.4 in, 4 door and 3 door"),
            2008: ("_hyundai_manuals/accent/accent_2008_portal_OM.pdf",
                   "US portal, folder 2008, file 2008_Hyundai_Accent_OM.pdf; the cover prints '2008 Owner's Manual' and "
                   "ACCENT; Copyright 2008; 273 pp; wheelbase 98.4 in, 4 door and 3 door"),
            2014: ("_hyundai_manuals/accent/accent_2014_portal_OM.pdf",
                   "US portal, folder 2014, file 2014-Accent-Owners-Manual.pdf; PDF title '2014 Accent Owners Manual'; "
                   "Copyright 2013; PDF created 2013-11-13; 406 pp; wheelbase 101.2 in, 4 door and 5 door"),
            2016: ("_hyundai_manuals/accent/accent_2016_portal_OM.pdf",
                   "US portal, folder 2016, file 2016_Hyundai_Accent_OM.pdf; PDF title '2016 Hyundai Accent Owner's "
                   "Manual'; Copyright 2015; PDF created 2015-08-07; 456 pp; wheelbase 101.2 in, 4 door and 5 door"),
            2017: ("_hyundai_manuals/accent/accent_2017_portal_OM.pdf",
                   "US portal, folder 2017, file 2017_Hyundai_Accent_OM.pdf; PDF title '2017 Hyundai Accent Owner's "
                   "Manual'; Copyright 2017; PDF created 2017-02-16; 380 pp; wheelbase 101.2 in, 4 door and 5 door"),
            2018: ("_hyundai_manuals/accent/accent_2018_portal_OM.pdf",
                   "US portal, folder 2018, file '2018 Accent Owners Manual.pdf'; no PDF title names the year (accepted "
                   "by ruling 2026-11-14 on folder, file name, copyright and creation date); Copyright 2018; PDF created "
                   "2018-02-20; 442 pp; sedan on the exterior overview; wheelbase 101.5 in"),
            2019: ("_hyundai_manuals/accent/accent_2019_portal_OM.pdf",
                   "US portal, folder 2019, file '2019 Accent OM.pdf'; no PDF title names the year (ruling 2026-11-14); "
                   "Copyright 2018; PDF created 2018-08-01; 442 pp; its own edition (21 pages revised from the 2018 "
                   "file, LED headlamp content added); wheelbase 101.5 in"),
            2020: ("_hyundai_manuals/accent/accent_2020_portal_OM.pdf",
                   "US portal, folder 2020, file '2020 Accent Owner's Manual.pdf'; PDF title '2020 Accent Owner's "
                   "Manual' and the cover prints '2020 Owner's Manual' and Accent; Copyright 2019; 445 pp; wheelbase "
                   "101.5 in"),
            2021: ("_hyundai_manuals/accent/accent_2021_portal_OM.pdf",
                   "US portal, folder 2021, file '2021 Accent OM.pdf'; no PDF title names the year (ruling 2026-11-14); "
                   "Copyright 2020; proof marks 'HCa HMA' dated 5/25/2020; PDF created 2020-09-01; 443 pp; wheelbase "
                   "101.5 in"),
            2022: ("_hyundai_manuals/accent/accent_2022_portal_OM.pdf",
                   "US portal, folder 2022, file 2022-Accent-OM.pdf; no PDF title names the year (ruling 2026-11-14); "
                   "Copyright 2021; PDF created 2021-07-06; 445 pp; wheelbase 101.5 in"),
        },
        # 2005 / 2006 / 2008 p.9-3: ENGINE | 1.6 MPI | Engine Type '4-Cylinder in-line DOHC' | Displacement (cc) 1,599.
        # 2014 / 2016 / 2017 p.8-2: ENGINE | Gasoline 1.6 | 97.09 cu.in (1591 cc) | No. of cylinders '4, In-line'.
        # 2018 / 2019 p.8-2: Gamma 1.6 GDI | 97.09 (1,591) | 'In-line 4 cylinder'.
        # 2020 / 2021 / 2022 p.8-2: Smartstream G1.6 | 97.52 (1,598) | 'In-line 4 cylinder'.
        book_engine={
            2005: dict(page="9-3", cc=1599, cylinders=4, layout="in-line"),
            2006: dict(page="9-3", cc=1599, cylinders=4, layout="in-line"),
            2008: dict(page="9-3", cc=1599, cylinders=4, layout="in-line"),
            2014: dict(page="8-2", cc=1591, cylinders=4, layout="in-line"),
            2016: dict(page="8-2", cc=1591, cylinders=4, layout="in-line"),
            2017: dict(page="8-2", cc=1591, cylinders=4, layout="in-line"),
            2018: dict(page="8-2", cc=1591, cylinders=4, layout="in-line"),
            2019: dict(page="8-2", cc=1591, cylinders=4, layout="in-line"),
            2020: dict(page="8-2", cc=1598, cylinders=4, layout="in-line"),
            2021: dict(page="8-2", cc=1598, cylinders=4, layout="in-line"),
            2022: dict(page="8-2", cc=1598, cylinders=4, layout="in-line"),
        },
        # EPA lists the 2005 car as "Accent/Brio" - its only Accent entry that year (ruling 2026-11-14: take it).
        epa_models={2005: ["Accent/Brio"], 2006: ["Accent"], 2008: ["Accent"], 2014: ["Accent"], 2016: ["Accent"],
                    2017: ["Accent"], 2018: ["Accent"], 2019: ["Accent"], 2020: ["Accent"], 2021: ["Accent"],
                    2022: ["Accent"]},
    ),
}

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
if "--sha" in sys.argv:
    ARGS = [a for a in ARGS if a != sys.argv[sys.argv.index("--sha") + 1]]
if len(ARGS) != 1 or ARGS[0] not in BATCHES:
    sys.exit("usage: python _add_hyundai_rows.py <batch> [--write --sha <hash>]   batches: %s" % ", ".join(sorted(BATCHES)))
BATCH = ARGS[0]
B_ = BATCHES[BATCH]
MAKE, MODEL = B_["make"], B_["model"]
TARGETS, BOOKS, BOOK_ENGINE, EPA_MODELS = B_["targets"], B_["books"], B_["book_engine"], B_["epa_models"]
EPA_IGNORE = B_.get("epa_ignore", [])
REPAIRS = B_.get("repair_fuel_economy", [])
SKIP_REPAIRS = "--skip-repairs" in sys.argv
PLAN_FILE = os.path.join(ROOT, "_add_hyundai_rows_%s_plan_cache.json" % BATCH.replace("-", "_"))   # gitignored (*_cache.json)
WRITE = "--write" in sys.argv

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
EPA = "https://www.fueleconomy.gov/ws/rest/vehicle"
NHTSA = "https://api.nhtsa.gov"
VPIC = "https://vpic.nhtsa.dot.gov/api/vehicles"
PACE = 0.7                                   # seconds between requests
Q = urllib.parse.quote
REQUESTS = []                                # (what, status, bytes) for every request made
_last = [0.0]
BOOK_LAYOUT = {"in-line": "I", "v-type": "V"}
VPIC_LAYOUT = {"In-Line": "I", "V-Shaped": "V"}


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


# ---------------------------------------------------------------------------- vPIC listing
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
    """('ok'|'empty', rows, info). Row mapping follows _pull_epa_mpg.py (engine = EPA 'displ' as printed).
    EPA may list one nameplate under several model names (drive variants); every name must be expected."""
    root = fetch_xml("%s/menu/model?year=%d&make=%s" % (EPA, year, Q(MAKE)), "EPA models %d" % year)
    models = [(mi.findtext("text") or "").strip() for mi in root.iter("menuItem")]
    if not models:
        raise PullError("EPA models %d: HTTP 200 but no model list for %s" % (year, MAKE))
    listed = sorted(m for m in models if MODEL.lower() in m.lower())
    ignored = [m for m in listed if any(m == p or m.startswith(p + " ") for p in EPA_IGNORE)]
    near = [m for m in listed if m not in ignored]
    if not near:
        return "empty", [], {"models_listed": len(models), "near": near, "ignored": ignored}
    if near != sorted(EPA_MODELS[year]):
        raise PullError("EPA models %d: EPA lists %r (ignoring %r), this batch expects %r -- needs a ruling"
                        % (year, near, ignored, sorted(EPA_MODELS[year])))
    rows, recs, seen = [], [], set()
    for name in near:
        root = fetch_xml("%s/menu/options?year=%d&make=%s&model=%s" % (EPA, year, Q(MAKE), Q(name)),
                         "EPA options %d %s" % (year, name))
        opts = [((mi.findtext("value") or "").strip(), (mi.findtext("text") or "").strip()) for mi in root.iter("menuItem")]
        if not opts or not all(v.isdigit() for v, _ in opts):
            raise PullError("EPA options %d %s: HTTP 200 but no usable option list %r" % (year, name, opts))
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

            def na(n):                     # EPA prints 0 where a figure does not apply (range, EV figures)
                return n if n else None

            if (g("year"), g("make"), g("model")) != (str(year), MAKE, name):
                raise PullError("EPA vehicle %s is %s %s %s, not %d %s %s" % (eid, g("year"), g("make"), g("model"), year, MAKE, name))
            city, hwy, comb = num("city08"), num("highway08"), num("comb08")
            if city is None or hwy is None or comb is None:
                raise PullError("EPA vehicle %s: no city / highway / combined figure" % eid)
            row = [city, hwy, comb, num("fuelCost08"), g("displ") or None, g("trany") or None, g("drive") or None,
                   g("fuelType") or None, na(num("range")), na(num("phevComb") or num("combE")),
                   na(num("cityE")), na(num("highwayE")), na(num("combE"))]
            recs.append({"epa_id": eid, "epa_model": name, "option": text, "displ": g("displ"), "cylinders": g("cylinders"),
                         "trany": g("trany"), "drive": g("drive"), "fuelType": g("fuelType"), "VClass": g("VClass"),
                         "atvType": g("atvType"), "tCharger": g("tCharger"), "sCharger": g("sCharger")})
            key = (row[0], row[1], row[2], row[4], row[6])                 # city, hwy, comb, displ, drive
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return "ok", rows, {"models_listed": len(models), "near": near, "ignored": ignored, "records": recs}


# ---------------------------------------------------------------------------- NHTSA
def B(x):
    return 1 if (x is True or str(x).lower() == "true") else 0


SAFETY_FIELDS = ["overall", "front driver", "front passenger", "side driver", "side passenger", "rollover",
                 "rollover risk", "side pole"]


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
    """('ok'|'empty', row, variants, how, withheld). NHTSA may rate drive variants separately and the table holds one
    row per vehicle. Every variant is fetched. A rating that is the same for all variants is stored; a rating that
    DIFFERS between variants is stored as NULL (the app could not say which variant a single figure belongs to).
    The older pulls stored whichever variant NHTSA listed first."""
    res, how = nhtsa_list("%s/SafetyRatings/modelyear/%d/make/%s/model/%s" % (NHTSA, year, Q(MAKE), Q(MODEL)),
                          "NHTSA safety list %d" % year, "Count", "Results")
    variants = []
    for x in res:
        vid, desc = x.get("VehicleId"), x.get("VehicleDescription")
        d = fetch_json("%s/SafetyRatings/VehicleId/%s" % (NHTSA, vid), "NHTSA safety %s" % vid)
        rr = d.get("Results")
        if not isinstance(rr, list) or len(rr) != 1:
            raise PullError("NHTSA safety %s: expected one result" % vid)
        r0 = rr[0]
        if str(r0.get("ModelYear")) != str(year) or (r0.get("Model") or "").upper() != MODEL.upper():
            raise PullError("NHTSA safety %s is %s %s" % (vid, r0.get("ModelYear"), r0.get("Model")))

        def g(k):
            v = r0.get(k)
            if v in ("", "Not Rated", None):
                return None
            return int(v) if str(v).isdigit() else v

        risk = r0.get("RolloverPossibility")
        row = [g("OverallRating"), g("FrontCrashDriversideRating"), g("FrontCrashPassengersideRating"),
               g("SideCrashDriversideRating"), g("SideCrashPassengersideRating"), g("RolloverRating"),
               risk if risk else None,                 # NHTSA prints 0 when the rollover test was not run
               g("SidePoleCrashRating") or g("combinedSideBarrierAndPoleRating-Front")]
        variants.append([vid, desc, row])
    if not variants:
        return "empty", None, variants, how, []
    if all(x is None for v in variants for x in v[2]):
        # listed by NHTSA but not rated: there is nothing to store, and an all-empty row must not be written
        return "empty", None, variants, how + "; %d variant(s) listed, none rated" % len(variants), []
    row, withheld = list(variants[0][2]), []
    for i, name in enumerate(SAFETY_FIELDS):
        if any(v[2][i] != row[i] for v in variants):
            withheld.append("%s (%s)" % (name, "; ".join("%s: %r" % (v[1], v[2][i]) for v in variants)))
            row[i] = None
    if all(x is None for x in row):
        # some variants are rated, but no figure is shared by all of them (e.g. one body style rated, the other
        # not): nothing to store, and an all-empty row must not be written
        return "empty", None, variants, how + "; %d variant(s) listed, no rating shared by all of them" % len(variants), withheld
    return "ok", row, variants, how, withheld


def complaints(year):
    res, how = nhtsa_list("%s/complaints/complaintsByVehicle?make=%s&model=%s&modelYear=%d" % (NHTSA, Q(MAKE), Q(MODEL), year),
                          "NHTSA complaints %d" % year, "count", "results")
    rows, vins, all_models = [], [], []
    for x in sorted(res, key=lambda x: x.get("odiNumber") or 0, reverse=True):
        if not x.get("odiNumber"):
            raise PullError("NHTSA complaints %d: a row without an ODI number" % year)
        prods = [p for p in (x.get("products") or []) if (p.get("type") or "").lower() == "vehicle"]
        named = any(str(p.get("productYear")) == str(year) and (p.get("productModel") or "").upper() == MODEL.upper()
                    for p in prods)
        # NHTSA files some complaints against 'ALL MODELS' of a make and year and returns them for every model of
        # that make and year. They are kept, as NHTSA returns them (count == rows; the fleet already holds 360 such
        # complaint numbers on every vehicle of one make and year), and listed in the report. Their VIN is not used
        # for the engine decode, since it may belong to another model.
        whole_make = any(str(p.get("productYear")) == str(year) and (p.get("productMake") or "").upper() == MAKE.upper()
                         and (p.get("productModel") or "").upper() == "ALL MODELS" for p in prods)
        if prods and not named:
            if not whole_make:
                raise PullError("NHTSA complaints %d: ODI %s is not filed against this vehicle" % (year, x.get("odiNumber")))
            all_models.append(str(x["odiNumber"]))
        rows.append([str(x["odiNumber"]), x.get("components"), (x.get("summary") or "")[:2000], x.get("dateOfIncident"),
                     B(x.get("crash")), B(x.get("fire")), x.get("numberOfInjuries") or 0, x.get("numberOfDeaths") or 0])
        if x.get("vin") and (named or not prods):
            vins.append(str(x["vin"]).strip().upper())
    if len({r[0] for r in rows}) != len(rows):
        raise PullError("NHTSA complaints %d: an ODI number is listed twice" % year)
    if all_models:
        how += "; %d of them filed by NHTSA against 'ALL MODELS' of %d %s, kept as returned: ODI %s" % (
            len(all_models), year, MAKE, ", ".join(all_models))
    return ("ok" if rows else "empty"), rows, vins, how


def vpic_decode(year, vins):
    """Decode up to four distinct NHTSA-complaint VIN prefixes with vPIC (the matrix's authority for engine identity).
    A prefix decode names make, model and model year; whether it states cylinders or layout depends on the maker's filing."""
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
        if len(tried) == 4:
            break
    return out


def engine_string(epa_recs, decodes, year):
    """'<displ>L <letter><cyl>' per engine, joined by ' / ', ONLY when every part is sourced (see the module note)."""
    pairs = sorted({(r["displ"], r["cylinders"]) for r in epa_recs})
    if not pairs or any(not d or not c for d, c in pairs):
        return None, "EPA does not give a displacement / cylinder count (%r)" % pairs
    be = BOOK_ENGINE.get(year)
    if not be:
        return None, "no engine table recorded for the %d book" % year
    engines = be.get("engines") or [be]
    good = [d for d in decodes if ((d.get("Make") or "").upper(), (d.get("Model") or "").upper(), str(d.get("ModelYear")))
            == (MAKE.upper(), MODEL.upper(), str(year))]
    parts, notes = [], []
    for displ, cyl in pairs:
        match = [e for e in engines if "%.1f" % (e["cc"] / 1000.0) == "%.1f" % float(displ) and str(e["cylinders"]) == cyl]
        if len(match) != 1:
            return None, ("EPA %s L / %s cyl has %d matches in the book's engine table p.%s (%s)"
                          % (displ, cyl, len(match), be["page"], ", ".join("%d cc" % e["cc"] for e in engines)))
        e = match[0]
        base = "EPA %s L, %s cyl = book p.%s %s cc, %d cylinders" % (displ, cyl, be["page"], format(e["cc"], ","), e["cylinders"])
        if e.get("layout"):
            letter = BOOK_LAYOUT.get(e["layout"].lower())
            if not letter:
                return None, "the book states a layout this script does not map: %r" % e["layout"]
            notes.append(base + ", " + e["layout"])
        else:
            mine = [d for d in good if (d.get("DisplacementL") or "").strip() and "%.1f" % float(d["DisplacementL"]) == "%.1f" % float(displ)]
            layouts = sorted({(d.get("EngineConfiguration") or "").strip() for d in mine} - {""})
            if len(layouts) != 1 or layouts[0] not in VPIC_LAYOUT:
                return None, base + "; the book's engine table states no layout and the vPIC decodes state %r" % (layouts or "none")
            if any((d.get("EngineCylinders") or "").strip() not in ("", cyl) for d in mine):
                return None, base + "; a vPIC cylinder count disagrees"
            letter = VPIC_LAYOUT[layouts[0]]
            notes.append(base + " (no layout printed); vPIC decode: %s" % layouts[0])
        parts.append("%sL %s%s" % (displ, letter, cyl))
    return " / ".join(parts), "; ".join(notes)


# ---------------------------------------------------------------------------- plan
def canon(targets, repairs=None):
    payload = targets if not repairs else {"targets": targets, "repairs": repairs}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def plan_sha(targets, repairs=None):
    return hashlib.sha256(canon(targets, repairs).encode("ascii")).hexdigest()


FE_COLS = ("city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, transmission, drive, fuel_type, range_miles, "
           "mpge, city_ev, hwy_ev, comb_ev")


def stored_fuel_economy(cur, vid):
    return [list(r) for r in cur.execute("SELECT %s FROM fuel_economy WHERE vehicle_id=? ORDER BY id" % FE_COLS, (vid,))]


def apply_repairs(cur, repairs):
    """Replace the fuel-economy rows of an EXISTING vehicle, only if they still equal what the dry run showed."""
    for r in repairs:
        vid = r["id"]
        row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        if not row or tuple(row) != (r["year"], MAKE, MODEL):
            raise RuntimeError("repair target %d is %r, not %d %s %s" % (vid, row and tuple(row), r["year"], MAKE, MODEL))
        if stored_fuel_economy(cur, vid) != r["current"]:
            raise RuntimeError("repair target %d: the stored fuel-economy rows changed since the dry run" % vid)
        if not r["fuel_economy"]:
            raise RuntimeError("repair target %d: no replacement rows" % vid)
        cur.execute("DELETE FROM fuel_economy WHERE vehicle_id=?", (vid,))
        cur.executemany("INSERT INTO fuel_economy (vehicle_id, " + FE_COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        [[vid] + x for x in r["fuel_economy"]])
        cur.execute("INSERT OR REPLACE INTO pull_log (vehicle_id, endpoint, status, pulled_at) VALUES (?,?,?,?)",
                    (vid, "fuel-economy", "ok", r["pulled_at"]))


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
    if mx != TARGETS[0][0] - 1 or [v for v, _ in TARGETS] != list(range(TARGETS[0][0], TARGETS[0][0] + len(TARGETS))):
        sys.exit("highest vehicle id is %s; this batch expects to start at %d with consecutive ids" % (mx, TARGETS[0][0]))
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
def rehearse(targets, repairs=()):
    """Apply the plan to an in-memory copy and run the REAL build's gates and data assembly on it."""
    src = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    mem.row_factory = sqlite3.Row
    cur = mem.cursor()
    before = cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    apply(cur, targets)
    apply_repairs(cur, repairs)
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
    say("  build gates passed on the in-memory copy; vehicles %d -> %d; owner's-manual-verified %d (unchanged by this step)"
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
    for r in repairs:
        v = by[r["id"]]
        say("  ships after repair for id %d (%d): %d fuel-economy entr%s"
            % (r["id"], r["year"], len(v.get("mpg") or []), "y" if len(v.get("mpg") or []) == 1 else "ies"))
        for m in v.get("mpg") or []:
            say("      %sL | %s | %s | city %s hwy %s comb %s | MPGe %r" % (m.get("eng"), m.get("trans"), m.get("drive"),
                                                                        m.get("city"), m.get("hwy"), m.get("comb"), m.get("mpge")))
            if m.get("mpge") or m.get("comb") is None:
                say("      UNEXPECTED electric figure or missing combined figure after repair")
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
    say("DRY RUN, batch %s -- nothing is written to wrench_vehicles.db" % BATCH)
    say("fleet today: %d vehicles; ids %d-%d are free; no %s %s row exists for %s"
        % (fleet, TARGETS[0][0], TARGETS[-1][0], MAKE, MODEL, ", ".join(str(y) for _, y in TARGETS)))
    targets, flags = [], []
    for vid, year in TARGETS:
        say("")
        say("=" * 100)
        say("%d %s %s  ->  vehicle id %d" % (year, MAKE, MODEL, vid))
        book, why = BOOKS[year]
        on_disk = os.path.exists(os.path.join(ROOT, book))
        say("  book      : %s  [%s]" % (book, "on disk" if on_disk else "NOT ON DISK"))
        say("              %s" % why)
        if not on_disk:
            flags.append("%d: the book file is not on disk" % year)
        listed, n_models = vpic_listing(year)
        say("  vPIC      : %s listed for model year %d (%d %s models listed)" % ("IS" if listed else "IS NOT", year, n_models, MAKE))
        if not listed:
            sys.exit("no row for %d: vPIC does not list %s" % (year, MODEL))
        pulled_at = datetime.datetime.now().isoformat()
        e_st, e_rows, e_info = epa(year)
        r_st, r_rows, r_how = recalls(year)
        s_st, s_row, s_var, s_how, s_held = safety(year)
        c_st, c_rows, vins, c_how = complaints(year)
        decodes = vpic_decode(year, vins)
        eng, eng_why = engine_string(e_info.get("records", []), decodes, year)
        for d in decodes:
            if ((d.get("Make") or "").upper(), (d.get("Model") or "").upper(), str(d.get("ModelYear"))) != (MAKE.upper(), MODEL.upper(), str(year)):
                flags.append("%d: vPIC decodes complaint VIN prefix %s as %s %s %s" % (year, d["vin_prefix"], d.get("ModelYear"), d.get("Make"), d.get("Model")))

        say("  EPA fuel economy [%s]: models %r; ignored as different vehicles %r; %d record(s) -> %d row(s) after the "
            "duplicate-trim rule" % (e_st, e_info.get("near"), e_info.get("ignored"), len(e_info.get("records", [])), len(e_rows)))
        for rec in e_info.get("records", []):
            say("      EPA id %s (%s): %s | displ %s | cyl %s | %s | %s | turbo %r | class %s"
                % (rec["epa_id"], rec["epa_model"], rec["option"], rec["displ"], rec["cylinders"], rec["drive"],
                   rec["fuelType"], rec["tCharger"], rec["VClass"]))
        for r in e_rows:
            say("      ROW city %s / hwy %s / comb %s | $%s per year | engine %r | %s | %s | %s | range %r mpge %r"
                % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]))
        say("  vPIC decode of NHTSA complaint VIN prefixes: %d" % len(decodes))
        for d in decodes:
            say("      %s -> %s %s %s | layout %r | cyl %r | %s L | %s | %s"
                % (d["vin_prefix"], d["ModelYear"], d["Make"], d["Model"], d["EngineConfiguration"], d["EngineCylinders"],
                   d["DisplacementL"], d["FuelTypePrimary"], d["DriveType"]))
        say("  engine label: %r  (%s)" % (eng, eng_why))
        if eng is None:
            flags.append("%d: engine label left empty -- %s" % (year, eng_why))
        say("  NHTSA recalls [%s]: %d   (%s)" % (r_st, len(r_rows), r_how))
        for r in r_rows:
            say("      %s | %s | park-it %d | %s" % (r[0], r[1], r[4], r[2][:110].replace("\n", " ")))
        say("  NHTSA safety ratings [%s]: %d listed variant(s)   (%s)" % (s_st, len(s_var), s_how))
        for sv in s_var:
            say("      variant %s %r: overall %r | front driver %r | front passenger %r | side driver %r | side passenger %r | "
                "rollover %r | rollover risk %r | side pole %r" % tuple([sv[0], sv[1]] + sv[2]))
        if s_row is not None:
            say("      ROW stored: overall %r | front driver %r | front passenger %r | side driver %r | side passenger %r | "
                "rollover %r | rollover risk %r | side pole %r" % tuple(s_row))
        if s_held:
            flags.append("%d: NHTSA rates %d variants and they differ on: %s -- stored as empty; every other rating is the "
                         "same for all variants" % (year, len(s_var), ", ".join(s_held)))
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
        say("  NOT written: reliability, warranty, service_costs. NOT written here: any curated spec.")
        targets.append({"id": vid, "year": year, "make": MAKE, "model": MODEL, "engine": eng, "pulled_at": pulled_at,
                        "book": book, "book_basis": why, "fuel_economy": e_rows, "recalls": r_rows, "safety": s_row,
                        "complaints": c_rows, "log": log,
                        "evidence": {"epa": e_info, "safety_variants": s_var, "safety_withheld": s_held, "vpic_decodes": decodes, "engine_basis": eng_why,
                                     "answers": {"recalls": r_how, "safety-ratings": s_how, "complaints": c_how}}})
    # an 'empty' needs a positive control: the same make / model spelling returning rows on that endpoint for another year
    for ep in ("fuel-economy", "recalls", "safety-ratings", "complaints"):
        st = [dict(t["log"])[ep] for t in targets]
        if "empty" in st and "ok" not in st:
            flags.append("%s is empty for every year in this batch: no positive control for the spelling %r / %r on that endpoint"
                         % (ep, MAKE, MODEL))
    # ---- repair draft for existing rows of this nameplate
    repairs = []
    if REPAIRS:
        say("")
        say("=" * 100)
        say("REPAIR DRAFT -- fuel economy of EXISTING %s %s rows (nothing is written; shown for a ruling)" % (MAKE, MODEL))
        con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
        cur = con.cursor()
        for vid, year in REPAIRS:
            row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
            if not row or tuple(row) != (year, MAKE, MODEL):
                sys.exit("repair target %d is %r, not %d %s %s" % (vid, row and tuple(row), year, MAKE, MODEL))
            current = stored_fuel_economy(cur, vid)
            pulled_at = datetime.datetime.now().isoformat()
            e_st, e_rows, e_info = epa(year)
            say("")
            say("  id %d = %d %s %s   EPA [%s]: models %r; ignored as different vehicles %r"
                % (vid, year, MAKE, MODEL, e_st, e_info.get("near"), e_info.get("ignored")))
            say("    STORED NOW (%d row(s)):" % len(current))
            for r in current:
                say("      city %r / hwy %r / comb %r | $%r | engine %r | %s | %s | type %r | MPGe %r" % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[9]))
            say("    PROPOSED (%d row(s)):" % len(e_rows))
            for rec in e_info.get("records", []):
                say("      EPA id %s (%s): %s | displ %s | cyl %s | %s | %s" % (rec["epa_id"], rec["epa_model"], rec["option"], rec["displ"], rec["cylinders"], rec["drive"], rec["fuelType"]))
            for r in e_rows:
                say("      ROW city %s / hwy %s / comb %s | $%s per year | engine %r | %s | %s | %s" % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
            if e_st != "ok" or not e_rows:
                flags.append("repair %d (%d): EPA returned no rows for the expected model names -- left out of the plan" % (vid, year))
                continue
            repairs.append({"id": vid, "year": year, "pulled_at": pulled_at, "current": current, "fuel_economy": e_rows,
                            "evidence": {"epa": e_info}})
        con.close()
    say("")
    say("=" * 100)
    say("REHEARSAL (in-memory copy of the database + the real build code)")
    ok = rehearse(targets, repairs)
    exp = expected_counts(targets)
    say("")
    say("TOTAL rows the write would insert: " + ", ".join("%s %d" % kv for kv in exp.items()))
    if repairs:
        say("REPAIR would replace fuel-economy rows on %d existing vehicle(s): %d row(s) out, %d row(s) in  (optional: --skip-repairs)"
            % (len(repairs), sum(len(r["current"]) for r in repairs), sum(len(r["fuel_economy"]) for r in repairs)))
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
    sha = plan_sha(targets, repairs)
    with io.open(PLAN_FILE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"script": os.path.basename(__file__), "batch": BATCH, "sha256": sha, "targets": targets, "repairs": repairs},
                  fh, sort_keys=True, indent=1)
    say("plan saved: %s" % PLAN_FILE)
    say("plan sha256: %s" % sha)
    say("to write exactly this plan (only on Robert's go):  python %s %s --write --sha %s" % (os.path.basename(__file__), BATCH, sha))


# ---------------------------------------------------------------------------- write
def write():
    if "--sha" not in sys.argv:
        sys.exit("--write needs --sha <the sha256 a dry run printed>")
    want = sys.argv[sys.argv.index("--sha") + 1]
    with io.open(PLAN_FILE, encoding="utf-8") as fh:
        plan = json.load(fh)
    targets, repairs = plan["targets"], plan.get("repairs") or []
    got = plan_sha(targets, repairs)
    if got != want or plan.get("sha256") != want or plan.get("batch") != BATCH:
        sys.exit("plan file hash %s does not match --sha %s: run the dry run again and get a fresh go" % (got, want))
    if [(t["id"], t["year"]) for t in targets] != TARGETS or any((t["make"], t["model"]) != (MAKE, MODEL) for t in targets):
        sys.exit("plan targets do not match this batch")
    for t in targets:
        if not os.path.exists(os.path.join(ROOT, t["book"])):
            sys.exit("the %d book is not on disk (%s)" % (t["year"], t["book"]))
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:                                       # read-only checks first; the handle closes on every path
        cur = con.cursor()
        fleet = preflight(cur)
        bare = bare_count(cur)
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    bak = "%s.bak_rows_%s_%s" % (DB, BATCH.replace("-", "_"), datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
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
        if repairs and not SKIP_REPAIRS:
            apply_repairs(cur, repairs)
            for r in repairs:
                if stored_fuel_economy(cur, r["id"]) != r["fuel_economy"]:
                    raise RuntimeError("repair %d did not store the planned rows" % r["id"])
        if bare_count(cur) != BARE_FROZEN:
            raise RuntimeError("bare owner-manual count moved")
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise
    con.close()
    say("WRITTEN: " + ", ".join("%s %d" % kv for kv in exp.items()))
    if repairs:
        say("REPAIRS: %s" % ("skipped (--skip-repairs)" if SKIP_REPAIRS else "fuel economy replaced on ids %s" % [r["id"] for r in repairs]))
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
