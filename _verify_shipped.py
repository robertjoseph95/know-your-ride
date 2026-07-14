#!/usr/bin/env python
"""KYR shipped-surfaces verifier (2026-07-12). Executes every invariant in
docs/shipped-surfaces-ledger.md over the BUILT, TRACKED artifacts.

Venues: [CI] checks need only tracked files (run everywhere, incl. GitHub Actions);
[DB] checks additionally need the local-only canonical wrench_vehicles.db and are
skipped with a notice when it is absent or --ci is passed.
Tiers: FAIL -> printed as `x <id>` and exit 1. WARN -> printed as `! <id>`, exit 0.

Usage: python _verify_shipped.py [--ci] [--root PATH]
Design: docs/ci-verifier-design.md. Stdlib only, guard-style output.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

# ---------------------------------------------------------------- artifact load

class Artifacts(object):
    def __init__(self, root):
        self.root = root
        self.index_path = os.path.join(root, "wrench_deploy", "index.html")
        self.demo_path = os.path.join(root, "wrench_demo.html")
        self.index = self._read(self.index_path)
        self.demo = self._read(self.demo_path)
        # demo markup = demo minus the inline __D__ data line (checks on framing/markers
        # must not match complaint/recall PROSE inside the data).
        self.demo_markup = re.sub(r"const __D__=\{.*?\};\n", "DATA;\n", self.demo, flags=re.S)
        blobs = sorted(glob.glob(os.path.join(root, "wrench_deploy", "data.*.js")))
        self.blob_paths = blobs
        self.blob_path = blobs[0] if len(blobs) == 1 else None
        self.blob_raw = self._read(self.blob_path) if self.blob_path else ""
        self.D = None
        if self.blob_raw:
            m = re.search(r"__D__\s*=\s*(\{.*\})\s*;?\s*$", self.blob_raw, re.S)
            if m:
                try:
                    self.D = json.loads(m.group(1))
                except Exception:
                    self.D = None
        sp = os.path.join(root, "wrench_deploy", "api", "specs.json")
        self.specs_path = sp
        try:
            self.specs = json.load(open(sp, encoding="utf-8"))
        except Exception:
            self.specs = None
        self.sitemap = self._read(os.path.join(root, "wrench_deploy", "sitemap.xml"))
        self.robots = self._read(os.path.join(root, "wrench_deploy", "robots.txt"))
        self.veh_pages = sorted(glob.glob(os.path.join(root, "wrench_deploy", "vehicles", "*", "index.html")))
        self.dtc_pages = sorted(glob.glob(os.path.join(root, "wrench_deploy", "dtc", "*", "index.html")))

    @staticmethod
    def _read(p):
        try:
            return open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            return ""


def walk(o, fn, path=""):
    fn(o, path)
    if isinstance(o, dict):
        for k, x in o.items():
            walk(x, fn, path + "." + str(k))
    elif isinstance(o, list):
        for x in o:
            walk(x, fn, path + "[]")

# ---------------------------------------------------------------- checks (return list of problems)

def s1_1_ver0_shell(a):
    bad = []
    def fn(o, path):
        if isinstance(o, dict) and "ver" in o and not o.get("ver") and len(o) > 1:
            bad.append(path)
    for v in a.D["v"]:
        walk(v, fn, "v")
    return ["%d ver:0 object(s) carry value keys, e.g. %s" % (len(bad), bad[0])] if bad else []

def s1_2_forbidden_strings(a):
    out = []
    for needle in ('"source":', "last_verified_at", "ai-haiku", "oilchangediy"):
        n = a.blob_raw.count(needle)
        if n:
            out.append("blob contains %d x %r" % (n, needle))
    return out

def s1_3_notes_gate(a):
    n = sum(1 for v in a.D["v"] if v.get("notes"))
    return ["%d vehicle(s) ship notes[] (vehicle_notes gate breached)" % n] if n else []

def s1_4_narratives_gone(a):
    out = []
    nc = sum(1 for v in a.D["v"] if v.get("comps"))
    nf = sum(1 for v in a.D["v"] if v.get("fuse_tsbs"))
    if nc: out.append("%d vehicle(s) ship comps[] narrative arrays" % nc)
    if nf: out.append("%d vehicle(s) ship fuse_tsbs[]" % nf)
    if a.D.get("fuseTsbsByCode") != {}: out.append("fuseTsbsByCode is not {}")
    return out

def s1_9_paid_feature_gate(a):
    # Block-1 paid-feature integrity (2026-07-13): three unverified surfaces must be ABSENT
    # from the shipped blob -- the same default-deny whitelist pattern as the notes/narrative
    # gates. `costs` = CarMD-derived, national-only, sold as "Regional service costs".
    # `rel`   = unsourced computed reliability score rendered as an authoritative rating.
    # `fixes` = CarMD DTC fix-rate probabilities/costs (the `dtc` definitions map is separate
    #           and legitimate, so only `fixes` is asserted empty, not `dtc`).
    out = []
    nc = sum(1 for v in a.D["v"] if "costs" in v)
    nr = sum(1 for v in a.D["v"] if "rel" in v)
    if nc: out.append("%d vehicle(s) ship costs{} (CarMD service_costs gate breached)" % nc)
    if nr: out.append("%d vehicle(s) ship rel{} (unsourced reliability score gate breached)" % nr)
    if a.D.get("fixes") != {}:
        out.append("fixes is not {} (%d code(s) -- CarMD DTC fix-rates gate breached)"
                   % len(a.D.get("fixes") or {}))
    return out

def s1_5_hash_and_reference(a):
    out = []
    if len(a.blob_paths) != 1:
        return ["expected exactly one wrench_deploy/data.*.js, found %d" % len(a.blob_paths)]
    name = os.path.basename(a.blob_path)
    h = hashlib.md5(open(a.blob_path, "rb").read()).hexdigest()[:8]
    if name != "data.%s.js" % h:
        out.append("blob filename %s != content hash data.%s.js" % (name, h))
    refs = set(re.findall(r"data\.[0-9a-f]{8}\.js", a.index))
    if refs != {name}:
        out.append("index.html references %s but blob on disk is %s" % (sorted(refs), name))
    return out

def s1_6_size_budget(a):
    sz = len(a.blob_raw)
    return ["blob is %.1f MB (budget 16 MB)" % (sz / 1e6)] if sz > 16 * 1024 * 1024 else []

def s2_1_noindex(a):
    bad = [p for p in a.veh_pages if 'name="robots" content="noindex' not in Artifacts._read(p)]
    return ["%d/%d vehicle page(s) missing noindex, e.g. %s" % (len(bad), len(a.veh_pages), bad[0])] if bad else []

def s2_2_false_attribution(a):
    bad = [p for p in a.veh_pages if "sourced from EPA, NHTSA and manufacturer" in Artifacts._read(p)]
    return ["%d vehicle page(s) carry the false EPA/NHTSA attribution, e.g. %s" % (len(bad), bad[0])] if bad else []

def s2_3_sitemap_delisted(a):
    n = a.sitemap.count("/vehicles/")
    return ["sitemap.xml lists %d /vehicles/ URL(s) (must be 0 during containment)" % n] if n else []

def s2_4_dtc_indexable(a):
    out = []
    bad = [p for p in a.dtc_pages if 'content="noindex' in Artifacts._read(p)]
    if bad: out.append("%d DTC page(s) are noindexed (must stay indexable), e.g. %s" % (len(bad), bad[0]))
    if a.dtc_pages and a.sitemap.count("/dtc/") == 0:
        out.append("sitemap.xml lost its /dtc/ URLs")
    return out

def s2_5_robots_crawlable(a):
    ok = "User-agent: *" in a.robots and "Allow: /" in a.robots and "Disallow: /" not in a.robots
    return [] if ok else ["robots.txt no longer allows crawl (noindex needs crawlability)"]

CARD_ID = re.compile(r'id="kyr-sample".*?openModal\((\d+)\)', re.S)
PLACARD_ID = re.compile(r"kyrHsDefaultPlacard\(\)\{[^}]*?VEH\[(\d+)\]")

def s3_1_sample_verified(a):
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        mc, mp = CARD_ID.search(txt), PLACARD_ID.search(txt)
        if not (mc and mp):
            out.append("%s: sample card or placard not found" % name); continue
        if mc.group(1) != mp.group(1):
            out.append("%s: card id %s != placard id %s" % (name, mc.group(1), mp.group(1))); continue
        vid = int(mc.group(1))
        rec = next((v for v in a.D["v"] if v.get("id") == vid), None)
        if not rec:
            out.append("%s: sample vehicle %d not in blob" % (name, vid)); continue
        if (rec.get("oil") or {}).get("ver") != 1 or (rec.get("parts") or {}).get("ver") != 1:
            out.append("%s: sample vehicle %d is not fully verified (oil/parts ver!=1)" % (name, vid))
    return out

def s3_2_sample_values_match(a):
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        mc = CARD_ID.search(txt)
        if not mc: continue
        vid = int(mc.group(1))
        rec = next((v for v in a.D["v"] if v.get("id") == vid), None)
        if not rec: continue
        card = re.search(r'id="kyr-sample".*?</button>', txt, re.S).group(0)
        oil = rec.get("oil") or {}
        mv = re.search(r"&#128738;\s*([0-9]+W-[0-9]+)", card)
        if mv and mv.group(1) not in (oil.get("visc") or ""):
            out.append("%s: card viscosity %s not in blob oil.visc %r" % (name, mv.group(1), oil.get("visc")))
        for cap in re.findall(r"([\d.]+)\s*/\s*[\d.]+\s*qt|(?<=&#128167;)\s*([\d.]+)", card)[:2]:
            capv = next(x for x in cap if x)
            if capv not in (oil.get("cap_w") or ""):
                out.append("%s: card capacity %s not in blob oil.cap_w %r" % (name, capv, oil.get("cap_w")))
        mr = re.search(r"(\d+) Open Recalls", card)
        if mr and int(mr.group(1)) != len(rec.get("recalls") or []):
            out.append("%s: card says %s recalls, blob has %d" % (name, mr.group(1), len(rec.get("recalls") or [])))
    return out

def s3_3_fabricated_absent(a):
    out = []
    for needle in ("0W-20 Full Synthetic", "14mm &middot; M12x1.25", "openModal(12802)"):
        for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
            if needle in txt:
                out.append("%s still contains fabricated-sample string %r" % (name, needle))
    return out

def s4_1_specs_marker(a):
    if not isinstance(a.specs, dict):
        return ["specs.json missing or unparseable"]
    meta = a.specs.get("_meta") or {}
    out = []
    if meta.get("generated_by") != "_gen_guide_specs.py":
        out.append("specs.json lacks _meta.generated_by=_gen_guide_specs.py")
    recs = {k: v for k, v in a.specs.items() if k != "_meta"}
    if meta.get("record_count") != len(recs):
        out.append("specs.json _meta.record_count=%r != %d records" % (meta.get("record_count"), len(recs)))
    return out

SPEC_REC_KEYS = {"label", "oil", "parts", "torque"}
SPEC_OIL_KEYS = {"viscosity", "oil_type", "capacity", "oem_spec"}
SPEC_PARTS_KEYS = {"spark_plug", "plug_gap", "plug_qty", "battery_group", "battery_cca", "tire", "psi_f", "psi_r"}
SPEC_TQ_KEYS = {"lug_nut", "drain_bolt", "spark_plug"}

def s4_2_specs_whitelist(a):
    out = []
    for k, v in a.specs.items():
        if k == "_meta": continue
        for label, got, allowed in (("record", set(v), SPEC_REC_KEYS),
                                    ("oil", set(v.get("oil") or {}), SPEC_OIL_KEYS),
                                    ("parts", set(v.get("parts") or {}), SPEC_PARTS_KEYS),
                                    ("torque", set(v.get("torque") or {}), SPEC_TQ_KEYS)):
            extra = got - allowed
            if extra:
                out.append("specs.json id %s: %s carries non-whitelisted key(s) %s" % (k, label, sorted(extra)))
        if len(out) >= 5: break
    return out

def s4_3_specs_size(a):
    sz = os.path.getsize(a.specs_path) if os.path.exists(a.specs_path) else 0
    return ["specs.json is %d KB (budget 500 KB; the fabricated legacy file was ~1 MB)" % (sz // 1024)] if sz > 500 * 1024 else []

AGG_KEYS = {"by_comp", "crash", "fire", "inj", "deaths", "first", "last"}

def s5_1_agg_whitelist(a):
    out = []
    for v in a.D["v"]:
        agg = v.get("comps_agg")
        if not agg: continue
        extra = set(agg) - AGG_KEYS
        if extra:
            out.append("vehicle %s comps_agg carries non-whitelisted key(s) %s" % (v.get("id"), sorted(extra)))
        if len(out) >= 5: break
    return out

def s5_2_reports_labels(a):
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if "Unverified consumer-submitted reports to NHTSA" not in txt:
            out.append("%s: consumer-reports disclaimer missing" % name)
        if "'Consumer Reports','Service Log'" not in txt:
            out.append("%s: comps tab label is not 'Consumer Reports'" % name)
    return out

def s5_3_hero_badge(a):
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if "WITH CONSUMER REPORTS" not in txt:
            out.append("%s: hero badge lost 'WITH CONSUMER REPORTS'" % name)
        if "WITH COMPLAINTS" in txt:
            out.append("%s: hero badge regressed to 'WITH COMPLAINTS'" % name)
    return out

PII_RES = (re.compile(r"\b[\w.+-]+@[\w-]+\.\w{2,}\b"),
           re.compile(r"\b(?:\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4})\b"),
           re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b"))

def s5_4_agg_pii(a):
    hits = []
    def fn(o, path):
        if isinstance(o, str):
            for rx in PII_RES:
                for m in rx.findall(o):
                    if any(ch.isdigit() for ch in m):
                        hits.append(path)
    for v in a.D["v"]:
        if v.get("comps_agg"):
            walk(v["comps_agg"], fn, "comps_agg")
    return ["%d PII-like string(s) inside comps_agg" % len(hits)] if hits else []

FRAMING = re.compile(r"known issues? documented|Documented model-specific|issues documented", re.I)

def s6_2_no_documented_framing(a):
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        n = len(FRAMING.findall(txt))
        if n:
            out.append("%s: %d 'documented' framing match(es)" % (name, n))
    return out

def s6_3_empty_state(a):
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        n = txt.count("No verified model-specific issues on file")
        if n != 1:
            out.append("%s: empty-state string appears %d time(s) (want exactly 1)" % (name, n))
    return out

def s7_1_footer_required(a):
    out = []
    for needle in ("U.S. DOE/ORNL", "not confirmed defects", "not affiliated with NHTSA"):
        for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
            if needle not in txt:
                out.append("%s: footer missing required string %r" % (name, needle))
    return out

def s7_2_footer_forbidden(a):
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if "(U.S. Government, public domain)" in txt:
            out.append("%s: blanket public-domain claim returned" % name)
    return out

def s7_3_paywall_copy(a):
    # P1-6 CLOSED (Block-2, 2026-07-13): the "No subscriptions, no paywalls" claim contradicted
    # the paid Pro tier. Copy fixed; this check is now FAIL-tier asserting ABSENCE (the ledger's
    # definition-of-done: the WARN may only be silenced by shipping the fix + this flip together).
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if "No subscriptions, no paywalls" in txt:
            out.append("%s: 'No subscriptions, no paywalls' copy present while Pro is sold (P1-6)" % name)
    return out

def s7_4_obd_absent(a):
    # OBD removal (Block-2, 2026-07-13): the OBD-II "Live Diagnostics" panel was a dead feature
    # (stub API always returned unavailable; no companion app ever shipped). Fully quarantined:
    # markup/JS/CSS gone from both HTML files, api/obd.py deleted, the vercel.json rewrite removed,
    # and the generator's fossil injectors deleted. This asserts none of it can silently return.
    out = []
    OBD_TOKENS = ("obd-panel", "OBD-II Live Diagnostics", "obdConnect", "/*WRENCH_OBD*/", "/api/obd")
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        for tok in OBD_TOKENS:
            if tok in txt:
                out.append("%s: OBD residue %r (dead feature must stay removed)" % (name, tok))
    if os.path.exists(os.path.join(a.root, "wrench_deploy", "api", "obd.py")):
        out.append("wrench_deploy/api/obd.py exists (OBD stub must stay deleted)")
    vj = Artifacts._read(os.path.join(a.root, "wrench_deploy", "vercel.json"))
    if "/api/obd" in vj:
        out.append("vercel.json still routes /api/obd")
    # the separate DTC Code Lookup feature MUST survive
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if 'id="pane-codes"' not in txt:
            out.append("%s: DTC Code Lookup pane missing (must survive OBD removal)" % name)
    return out

def s8_1_version_stamp(a):
    m = re.search(r'kyr-version" content="([^"]+)"', a.index)
    if not m:
        return ["index.html has no kyr-version meta"]
    if not re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$", m.group(1)):
        return ["kyr-version %r does not match ^YYYY-MM-DD-slug$" % m.group(1)]
    return []

DRIFT_MARKERS = ('id="kyr-sample"', "No verified model-specific issues on file",
                 "U.S. DOE/ORNL", "not confirmed defects",
                 "Unverified consumer-submitted reports to NHTSA", "WITH CONSUMER REPORTS")

def s8_2_two_file_drift(a):
    out = []
    for mk in DRIFT_MARKERS:
        ni, nd = a.index.count(mk), a.demo_markup.count(mk)
        if ni != nd:
            out.append("marker %r: index=%d demo=%d (two-file drift)" % (mk, ni, nd))
    return out

# ---------------------------------------------------------------- DB-tier checks
# These need the local-only canonical wrench_vehicles.db (315 MB, gitignored).
# They are auto-skipped -- with a printed SKIP line -- when the DB is absent (CI).

def _ver(src):
    # Verbatim mirror of files/04_rebuild_demo.py::_ver -- the single gate definition.
    s = (src or "").strip().lower()
    if not s or "ai-" in s or "haiku" in s or s == "scraped" or "classifier" in s or s == "unknown":
        return 0
    if "owner" in s or "manual" in s or "vpic" in s or "epa" in s or "nhtsa" in s:
        return 1
    return 0

GATE_TABLES = ("oil_change", "parts", "fluids", "torque_specs", "engine_specs", "maintenance")

def _db(a):
    import sqlite3
    con = sqlite3.connect("file:%s?mode=ro" % a.db_path.replace("\\", "/"), uri=True)
    con.row_factory = sqlite3.Row
    return con

def s1_7_gate_equivalence(a):
    """Gate-dimension DB<->blob equivalence: for each gated category, the set of vehicles
    the DB says are verified must equal the set the shipped blob marks ver:1. (Full
    byte-level rebuild equivalence stays deferred pending a --check mode on the rebuild.)"""
    con = _db(a)
    cur = con.cursor()
    vids = {r[0] for r in cur.execute("SELECT id FROM vehicles")}
    def db_set(table):
        return {r["vehicle_id"] for r in cur.execute("SELECT vehicle_id, source FROM %s" % table)
                if r["vehicle_id"] in vids and _ver(r["source"]) == 1}
    out = []
    flat = (("oil_change", "oil"), ("parts", "parts"), ("fluids", "fluids"))
    for table, key in flat:
        db = db_set(table)
        blob = {v["id"] for v in a.D["v"] if (v.get(key) or {}).get("ver") == 1}
        if db != blob:
            out.append("%s: DB verified %d vehicles, blob ver:1 %d (diff e.g. %s)"
                       % (key, len(db), len(blob), sorted(db ^ blob)[:3]))
    rows = (("torque_specs", "torque"), ("maintenance", "maint"), ("engine_specs", "engines"))
    for table, key in rows:
        db = db_set(table)
        blob = {v["id"] for v in a.D["v"]
                if any(x.get("ver") == 1 for x in (v.get(key) or []))}
        if db != blob:
            out.append("%s: DB verified %d vehicles, blob ver:1 %d (diff e.g. %s)"
                       % (key, len(db), len(blob), sorted(db ^ blob)[:3]))
    con.close()
    return out

def s1_8_gate_sources(a):
    """Mirror of the build-time _assert_gate_sources: no blacklisted-pattern source may
    compute ver=1 in any gated table."""
    con = _db(a)
    cur = con.cursor()
    out = []
    for t in GATE_TABLES:
        for (s,) in cur.execute("SELECT DISTINCT source FROM %s" % t):
            sl = (s or "").strip().lower()
            if ("ai-" in sl or "haiku" in sl or sl == "scraped" or "classifier" in sl) and _ver(s) == 1:
                out.append("blacklisted source computes ver=1 in %s: %r" % (t, s))
    con.close()
    return out

def s4_4_specs_regen(a):
    """Determinism-backed equivalence: regenerating specs.json from the DB must reproduce
    the committed file byte-for-byte. Runs the real generator against a temp output path
    (never touches the committed file)."""
    import importlib.util, io, tempfile
    from contextlib import redirect_stdout
    gen = os.path.join(a.root, "_gen_guide_specs.py")
    if not os.path.exists(gen):
        return ["_gen_guide_specs.py not found"]
    spec = importlib.util.spec_from_file_location("_gen_guide_specs_check", gen)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fd, tmp = tempfile.mkstemp(suffix=".specs.json")
    os.close(fd)
    try:
        mod.DB = a.db_path
        mod.OUT = tmp
        with redirect_stdout(io.StringIO()):
            mod.main()
        fresh = open(tmp, "rb").read()
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    committed = open(a.specs_path, "rb").read()
    if fresh != committed:
        return ["regenerated specs.json differs from the committed file "
                "(%d vs %d bytes) -- DB and artifact are out of sync; rerun _gen_guide_specs.py"
                % (len(fresh), len(committed))]
    return []

def s8_3_count_reconciliation(a):
    con = _db(a)
    cur = con.cursor()
    vids = {r[0] for r in cur.execute("SELECT id FROM vehicles")}
    union = set()
    for t in ("oil_change", "parts", "torque_specs"):
        union |= {r["vehicle_id"] for r in cur.execute("SELECT vehicle_id, source FROM %s" % t)
                  if r["vehicle_id"] in vids and _ver(r["source"]) == 1}
    con.close()
    out = []
    rc = (a.specs.get("_meta") or {}).get("record_count")
    if rc != len(union):
        out.append("specs.json record_count=%r != DB verified union %d" % (rc, len(union)))
    blob_oil = sum(1 for v in a.D["v"] if (v.get("oil") or {}).get("ver") == 1)
    if abs(blob_oil - len(union)) > len(union):  # sanity bound only; S1.7 does the exact match
        out.append("blob oil ver:1 count %d wildly off DB union %d" % (blob_oil, len(union)))
    return out

# ---------------------------------------------------------------- registry / main

CHECKS = [
    ("S1.1-ver0-shell",          "FAIL", "CI", s1_1_ver0_shell),
    ("S1.2-forbidden-strings",   "FAIL", "CI", s1_2_forbidden_strings),
    ("S1.3/S6.1-notes-gate",     "FAIL", "CI", s1_3_notes_gate),
    ("S1.4-narratives-gone",     "FAIL", "CI", s1_4_narratives_gone),
    ("S1.9-paid-feature-gate",   "FAIL", "CI", s1_9_paid_feature_gate),
    ("S1.5-hash-and-reference",  "FAIL", "CI", s1_5_hash_and_reference),
    ("S1.6-size-budget",         "WARN", "CI", s1_6_size_budget),
    ("S2.1-noindex",             "FAIL", "CI", s2_1_noindex),
    ("S2.2-false-attribution",   "FAIL", "CI", s2_2_false_attribution),
    ("S2.3-sitemap-delisted",    "FAIL", "CI", s2_3_sitemap_delisted),
    ("S2.4-dtc-indexable",       "FAIL", "CI", s2_4_dtc_indexable),
    ("S2.5-robots-crawlable",    "WARN", "CI", s2_5_robots_crawlable),
    ("S3.1-sample-verified",     "FAIL", "CI", s3_1_sample_verified),
    ("S3.2-sample-values-match", "FAIL", "CI", s3_2_sample_values_match),
    ("S3.3-fabricated-absent",   "FAIL", "CI", s3_3_fabricated_absent),
    ("S4.1-specs-marker",        "FAIL", "CI", s4_1_specs_marker),
    ("S4.2-specs-whitelist",     "FAIL", "CI", s4_2_specs_whitelist),
    ("S4.3-specs-size",          "WARN", "CI", s4_3_specs_size),
    ("S5.1-agg-whitelist",       "FAIL", "CI", s5_1_agg_whitelist),
    ("S5.2-reports-labels",      "FAIL", "CI", s5_2_reports_labels),
    ("S5.3-hero-badge",          "FAIL", "CI", s5_3_hero_badge),
    ("S5.4-agg-pii",             "WARN", "CI", s5_4_agg_pii),
    ("S6.2-no-documented-framing","FAIL", "CI", s6_2_no_documented_framing),
    ("S6.3-empty-state",         "FAIL", "CI", s6_3_empty_state),
    ("S7.1-footer-required",     "FAIL", "CI", s7_1_footer_required),
    ("S7.2-footer-forbidden",    "FAIL", "CI", s7_2_footer_forbidden),
    ("S7.3-paywall-copy",        "FAIL", "CI", s7_3_paywall_copy),
    ("S7.4-obd-absent",          "FAIL", "CI", s7_4_obd_absent),
    ("S8.1-version-stamp",       "FAIL", "CI", s8_1_version_stamp),
    ("S8.2-two-file-drift",      "FAIL", "CI", s8_2_two_file_drift),
    ("S1.7-gate-equivalence",    "FAIL", "DB", s1_7_gate_equivalence),
    ("S1.8-gate-sources",        "FAIL", "DB", s1_8_gate_sources),
    ("S4.4-specs-regen",         "FAIL", "DB", s4_4_specs_regen),
    ("S8.3-count-reconciliation","WARN", "DB", s8_3_count_reconciliation),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ci", action="store_true", help="run only tracked-artifact checks")
    ap.add_argument("--root", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()

    a = Artifacts(args.root)
    if a.D is None:
        print("SHIPPED-SURFACES VERIFY: FAIL")
        print("  x bootstrap: could not locate/parse the single wrench_deploy/data.<hash>.js payload")
        return 1
    a.db_path = os.path.join(args.root, "wrench_vehicles.db")
    run_db = (not args.ci) and os.path.exists(a.db_path)
    if not run_db:
        skipped = [cid for cid, _, v, _ in CHECKS if v == "DB"]
        print("  SKIP %s (%s)" % (", ".join(skipped),
                                  "--ci: DB-tier runs in the local deploy ritual" if args.ci
                                  else "wrench_vehicles.db not present"))

    fails, warns = [], []
    for cid, tier, venue, fn in CHECKS:
        if venue == "DB" and not run_db:
            continue
        try:
            problems = fn(a)
        except Exception as e:
            problems = ["check crashed: %r" % e]
        for p in problems:
            (fails if tier == "FAIL" else warns).append((cid, p))

    for cid, p in warns:
        print("  ! %s: %s" % (cid, p))
    for cid, p in fails:
        print("  x %s: %s" % (cid, p))
    n_run = sum(1 for _, _, v, _ in CHECKS if v != "DB" or run_db)
    if fails:
        print("SHIPPED-SURFACES VERIFY: FAIL (%d check(s) failing, %d warn(s), %d run)" % (len(set(c for c, _ in fails)), len(warns), n_run))
        return 1
    print("SHIPPED-SURFACES VERIFY: PASS (%d checks, %d warn(s))" % (n_run, len(warns)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
