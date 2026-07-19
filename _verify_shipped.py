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

from files.ic01_quarantine import (
    EXPECTED_DB_ROWS,
    EXPECTED_HOMEPAGE_SAMPLE,
    HOMEPAGE_SAMPLE_ID,
    QUARANTINED_VEHICLE_IDS,
    QUARANTINE_SOURCE,
    projection_problems,
)

# ---------------------------------------------------------------- artifact load

class Artifacts(object):
    def __init__(self, root):
        self.root = root
        self.index_path = os.path.join(root, "wrench_deploy", "index.html")
        self.demo_path = os.path.join(root, "wrench_demo.html")
        self.index = self._read(self.index_path)
        self.demo = self._read(self.demo_path)
        self.demo_json_raw = ""
        self.demo_D = None
        data_start = self.demo.find("const __D__=")
        data_end = self.demo.find(";\n</script>", data_start)
        if data_start >= 0 and data_end > data_start:
            self.demo_json_raw = self.demo[data_start + len("const __D__="):data_end]
            try:
                self.demo_D = json.loads(self.demo_json_raw)
            except Exception:
                self.demo_D = None
        # demo markup = demo minus the inline __D__ data line (checks on framing/markers
        # must not match complaint/recall PROSE inside the data).
        self.demo_markup = re.sub(r"const __D__=\{.*?\};\n", "DATA;\n", self.demo, flags=re.S)
        blobs = sorted(glob.glob(os.path.join(root, "wrench_deploy", "data.*.js")))
        self.blob_paths = blobs
        self.blob_path = blobs[0] if len(blobs) == 1 else None
        self.blob_raw = self._read(self.blob_path) if self.blob_path else ""
        self.blob_json_raw = ""
        self.D = None
        if self.blob_raw:
            m = re.search(r"__D__\s*=\s*(\{.*\})\s*;?\s*$", self.blob_raw, re.S)
            if m:
                self.blob_json_raw = m.group(1)
                try:
                    self.D = json.loads(self.blob_json_raw)
                except Exception:
                    self.D = None
        sp = os.path.join(root, "wrench_deploy", "api", "specs.json")
        self.specs_path = sp
        try:
            with open(sp, encoding="utf-8") as f:
                self.specs = json.load(f)
        except Exception:
            self.specs = None
        self.sitemap = self._read(os.path.join(root, "wrench_deploy", "sitemap.xml"))
        self.robots = self._read(os.path.join(root, "wrench_deploy", "robots.txt"))
        self.readme = self._read(os.path.join(root, "README.md"))
        self.veh_pages = sorted(glob.glob(os.path.join(root, "wrench_deploy", "vehicles", "*", "index.html")))
        self.dtc_pages = sorted(glob.glob(os.path.join(root, "wrench_deploy", "dtc", "*", "index.html")))

    @staticmethod
    def _read(p):
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                return f.read()
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
    # Block-3: the dead fuseTsbsByCode root key is fully REMOVED (was {}); it must be ABSENT,
    # not empty -- a TSB-derived root key shipping at all contradicts "Phase 1 = no TSB coverage."
    if "fuseTsbsByCode" in a.D: out.append("fuseTsbsByCode root key is present (must be absent)")
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

# Payload field allowlist (2026-07-14 integrity gate). DEFAULT-DENY on the top-level vehicle
# shape: every key the generator may legitimately emit is enumerated here; any other key fails.
# This is the structural close of the warranty/fuse_loc class: both shipped unverified because
# they were never in GATE_TABLES and the generator attached them with no _ver() call -- no
# existing check could see a field it had never been told about. A gate that trusts the
# generator to remember is not a gate. New surface => new allowlist entry, deliberately.
#   identity:   id, year, make, model, trim, engine        (vehicles table)
#   gated spec: oil, parts, fluids, torque, maint, maint_parts, engines  (ver-carrying, S1.1/S1.7)
#   government: mpg (EPA), safety + recalls (NHTSA), comps_agg (NHTSA aggregates, S5.1)
#   ev:         ev_specs summary {batt,use,charge,range}
#   guidance:   D-2 human-verified TSB pairings (contents governed by S5.7/S5.9)
# warranty (vehicle-finder.com aggregator pull) and fuse_loc (AI-generated) are DELIBERATELY
# absent -- quarantined in the DB, stripped 2026-07-14, and rejected here if they reappear.
VEHICLE_FIELDS = {"id", "year", "make", "model", "trim", "engine",
                  "oil", "parts", "fluids", "torque", "maint", "maint_parts", "engines",
                  "mpg", "safety", "recalls", "comps_agg", "ev", "guidance"}

def s1_10_vehicle_field_allowlist(a):
    out = []
    for v in a.D["v"]:
        extra = set(v.keys()) - VEHICLE_FIELDS
        if extra:
            out.append("vehicle %s ships non-allowlisted top-level field(s) %s" % (v.get("id"), sorted(extra)))
            if len(out) >= 5:
                break
    return out

def s1_5_hash_and_reference(a):
    out = []
    if len(a.blob_paths) != 1:
        return ["expected exactly one wrench_deploy/data.*.js, found %d" % len(a.blob_paths)]
    name = os.path.basename(a.blob_path)
    with open(a.blob_path, "rb") as f:
        h = hashlib.md5(f.read()).hexdigest()[:8]
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

# Common Customer Complaints projection (Block-3, 2026-07-13). Default-deny whitelist: only
# these keys may appear on comps_agg. Any new key (esp. a TSB/manufacturer-guidance field) fails.
AGG_KEYS = {"n", "topics", "crash", "fire", "inj", "deaths", "through"}
# Manufacturer-guidance / TSB key names that must NEVER appear anywhere in the blob (Phase 1).
TSB_KEYS = {"tsb", "tsbs", "bulletin", "bulletins", "manufacturer_documented", "mfr_guidance",
            "service_action", "fuseTsbsByCode", "fuse_tsbs"}

def s5_1_agg_whitelist(a):
    out = []
    for v in a.D["v"]:
        agg = v.get("comps_agg")
        if not agg: continue
        extra = set(agg) - AGG_KEYS
        if extra:
            out.append("vehicle %s comps_agg carries non-whitelisted key(s) %s" % (v.get("id"), sorted(extra)))
        # topics must be [str, int] pairs -- no narrative text, no nested guidance objects
        for t in (agg.get("topics") or []):
            if not (isinstance(t, list) and len(t) == 2 and isinstance(t[0], str) and isinstance(t[1], int)):
                out.append("vehicle %s comps_agg topic is not a [label,int] pair: %r" % (v.get("id"), t)); break
        if len(out) >= 5: break
    return out

def s5_2_complaints_surface(a):
    # Common Customer Complaints heading + the permanent NHTSA disclaimer must ship; the old
    # standalone "Consumer Reports" tab label must NOT (it folded into Safety).
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if "Common Customer Complaints" not in txt:
            out.append("%s: 'Common Customer Complaints' heading missing" % name)
        if "Complaints are reports submitted to NHTSA, not verified defects" not in txt:
            out.append("%s: permanent complaint disclaimer missing" % name)
        if "'Consumer Reports','Service Log'" in txt:
            out.append("%s: obsolete standalone 'Consumer Reports' tab label still present" % name)
    return out

def s5_3_hero_badge(a):
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if "WITH CONSUMER REPORTS" not in txt:
            out.append("%s: hero badge lost 'WITH CONSUMER REPORTS'" % name)
        if "WITH COMPLAINTS" in txt:
            out.append("%s: hero badge regressed to 'WITH COMPLAINTS' (P0-4: keep the neutral term)" % name)
    return out

# Forbidden complaint framing (design "Disallowed labels"). Matched only as AFFIRMATIVE claims:
# the negations "not confirmed defects" (footer) / "not verified defects" (disclaimer) are the
# honest phrasing this feature relies on, so a preceding "not " must not trip the check.
FORBIDDEN_LABELS = tuple(re.compile(r"(?<!not )" + p) for p in
    ("confirmed defect", "common failure", "known defect", "usually fixes",
     "guaranteed fix", "nhtsa-recommended repair", "free repair"))
# Date phrasing that implies an ingest guarantee we cannot make (only 127/1040 have pull_log).
BANNED_DATE = ("data through", "retrieved", "updated as of", "reported through")

def s5_5_labeled_count(a):
    # The complaint count must always carry its label + denominator ("X of Y NHTSA complaint
    # records mention TOPIC"); a bare ratio may never ship. Assert the labeled render template
    # is present and no forbidden framing label appears in either shipped HTML.
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if "NHTSA complaint records mention " not in txt:
            out.append("%s: labeled complaint-count template missing (bare ratio risk)" % name)
        low = txt.lower()
        for rx in FORBIDDEN_LABELS:
            if rx.search(low):
                out.append("%s: forbidden complaint framing %r present" % (name, rx.pattern))
    return out

def s5_6_incident_date_phrasing(a):
    # Approved phrasing only. "Incident dates through {Month Year}" is generated; the banned
    # strings imply an ingest guarantee (the field is dateOfIncident, and pull_log is sparse).
    out = []
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if "Incident dates through " not in txt:
            out.append("%s: approved 'Incident dates through' phrasing missing" % name)
        low = txt.lower()
        for bad in BANNED_DATE:
            if bad in low:
                out.append("%s: banned date phrasing %r present" % (name, bad))
    return out

GUIDE_KEYS = {"topic", "tsb", "date", "comp", "sym", "act", "applies", "url",
              "tcount", "n", "vby", "vat", "vhash"}
GUIDE_STUB = ("tsb", "url", "vhash", "vby", "vat")   # the verification stub; missing any -> not a pairing
GUIDE_HOSTS = ("static.nhtsa.gov", "www.nhtsa.gov", "nhtsa.gov")
GUIDE_TEXT_MAX = 220                                  # sym/act bound; longer / multi-sentence -> prose reject
# A verified pairing may surface a topic BELOW the customer-reported threshold (2026-07-14 ruling),
# but only as a distinct card state that leads with the manufacturer evidence -- it may NOT carry
# frequency framing (that belongs to the >=3/>=10% customer lane alone).
FREQ_FRAMING = ("frequently reported", "frequently", "most reported", "most-reported",
                "commonly reported", "frequent")

def s5_7_tsb_gate(a):
    # Block D-1 (+ 2026-07-14 threshold ruling): "no UNVERIFIED TSB content." Default-deny holds --
    # top-level keys whitelisted, raw TSB-family keys forbidden -- but a per-vehicle `guidance`
    # object may ship IFF every entry is a COMPLETE human-verification record: full stub, official
    # NHTSA source, whitelisted keys only, short non-prose KYR descriptors, and NO frequency framing
    # (a pairing may surface a below-threshold topic, but never as "frequently reported"). The topic
    # need NOT be a threshold-clearing customer topic; its honest count is enforced DB-side (S5.9).
    out = []
    top_extra = set(a.D.keys()) - {"v", "dtc", "fixes"}
    if top_extra:
        out.append("blob has non-whitelisted top-level key(s) %s" % sorted(top_extra))
    hits = 0
    for v in a.D["v"]:
        bad = TSB_KEYS & set(v.keys())            # raw TSB-family keys remain forbidden
        if bad:
            out.append("vehicle %s carries raw TSB-family key(s) %s" % (v.get("id"), sorted(bad))); hits += 1
        for g in (v.get("guidance") or []):
            miss = [k for k in GUIDE_STUB if not g.get(k)]
            if miss:
                out.append("vehicle %s guidance missing verification stub %s" % (v.get("id"), miss)); hits += 1
            extra = set(g) - GUIDE_KEYS
            if extra:
                out.append("vehicle %s guidance has non-whitelisted key(s) %s" % (v.get("id"), sorted(extra))); hits += 1
            host = re.sub(r"^https?://", "", str(g.get("url", ""))).split("/")[0].lower()
            if host not in GUIDE_HOSTS:
                out.append("vehicle %s guidance url host %r not an official NHTSA host" % (v.get("id"), host)); hits += 1
            if not isinstance(g.get("tcount"), int) or not isinstance(g.get("n"), int):
                out.append("vehicle %s guidance tcount/n must be integers (honest labeled count)" % v.get("id")); hits += 1
            for f in ("sym", "act", "topic"):
                s = str(g.get(f, ""))
                low = s.lower()
                if len(s) > GUIDE_TEXT_MAX or s.count(".") > 2 or "\n" in s:
                    out.append("vehicle %s guidance %s is prose-shaped (bound %d, <=2 sentences, one line)" % (v.get("id"), f, GUIDE_TEXT_MAX)); hits += 1
                if any(fr in low for fr in FREQ_FRAMING):
                    out.append("vehicle %s guidance %s carries frequency framing (pairing card must not)" % (v.get("id"), f)); hits += 1
        if hits >= 8:
            break
    for name, txt in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        if "No matching manufacturer guidance found" not in txt:
            out.append("%s: manufacturer-guidance teal empty-state missing" % name)
    return out

def s5_10_collapse_canary(a):
    # Collapse canary (2026-07-14, post-Deploy-B guard commit): no shipped complaint-topic
    # label may contain ", ". Parent-collapsed labels never do (the collapse keeps everything
    # before the first ", "); every NHTSA subcategory label does ("SERVICE BRAKES, HYDRAULIC",
    # "FUEL SYSTEM, GASOLINE"). A parser edit that reintroduces split-before-threshold ships
    # comma-space labels immediately, so this fires on the blob alone -- in CI, on every push,
    # no DB needed. The split it guards against hid 68 cleared-threshold safety topics on
    # 2026-07-14 data (e.g. 2007 Prius SERVICE BRAKES 329/2,003 = 16.4% pooled). S5.11 is the
    # complete DB-tier equivalence; this is the cheap always-on tripwire. Not redundant.
    out = []
    for v in a.D["v"]:
        for t in ((v.get("comps_agg") or {}).get("topics") or []):
            label = str(t[0]) if isinstance(t, list) and t else ""
            if ", " in label:
                out.append("vehicle %s ships subcategory topic label %r (split-before-threshold reintroduced?)"
                           % (v.get("id"), label))
        for g in (v.get("guidance") or []):
            if ", " in str(g.get("topic", "")):
                out.append("vehicle %s guidance topic %r carries a subcategory label"
                           % (v.get("id"), g.get("topic")))
        if len(out) >= 5:
            break
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
                 "Common Customer Complaints", "No matching manufacturer guidance found",
                 "WITH CONSUMER REPORTS")

def s8_2_two_file_drift(a):
    out = []
    for mk in DRIFT_MARKERS:
        ni, nd = a.index.count(mk), a.demo_markup.count(mk)
        if ni != nd:
            out.append("marker %r: index=%d demo=%d (two-file drift)" % (mk, ni, nd))
    return out


# IC-01 (2026-07-18): source verification and exact-configuration applicability are
# independent gates.  These checks quarantine five cross-configuration CR-V rows on
# every shipped surface while preserving identity and government data.

def s9_1_ic01_projection(a):
    return projection_problems(a.D["v"])


def s9_2_ic01_guide_absent(a):
    if not isinstance(a.specs, dict):
        return ["specs.json missing or unparseable"]
    present = sorted(
        vehicle_id for vehicle_id in QUARANTINED_VEHICLE_IDS
        if str(vehicle_id) in a.specs
    )
    return ["quarantined CR-V id(s) still present in specs.json: %s" % present] if present else []


def s9_3_ic01_sample_pin(a):
    out = []
    sample = next((v for v in a.D["v"] if v.get("id") == HOMEPAGE_SAMPLE_ID), None)
    if not sample:
        return ["replacement homepage sample %s is absent from the blob" % HOMEPAGE_SAMPLE_ID]
    expected = EXPECTED_HOMEPAGE_SAMPLE
    identity = tuple(sample.get(key) for key in ("year", "make", "model", "trim", "engine"))
    if identity != expected["identity"]:
        out.append("replacement sample identity %r != pinned identity %r"
                   % (identity, expected["identity"]))
    oil = sample.get("oil") or {}
    if oil.get("visc") != expected["oil_visc"]:
        out.append("replacement sample oil viscosity %r != pinned %r"
                   % (oil.get("visc"), expected["oil_visc"]))
    if oil.get("cap_w") != expected["oil_cap_w"]:
        out.append("replacement sample oil capacity %r != pinned %r"
                   % (oil.get("cap_w"), expected["oil_cap_w"]))
    if len(sample.get("recalls") or []) != expected["recall_count"]:
        out.append("replacement sample recall count %d != pinned %d"
                   % (len(sample.get("recalls") or []), expected["recall_count"]))
    label = "%s %s %s" % expected["identity"][:3]
    function_re = re.compile(
        r"function kyrHsDefaultPlacard\(\)\{(.*?)\}\s*function kyrHsShowTrims\(",
        re.S,
    )
    for name, text in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        card_match = CARD_ID.search(text)
        body_match = function_re.search(text)
        if not card_match or not body_match:
            out.append("%s: sample card or default placard function not found" % name)
            continue
        card_id = int(card_match.group(1))
        body = body_match.group(1)
        placard_ids = [int(x) for x in re.findall(r"VEH\[(\d+)\]", body)]
        if card_id != HOMEPAGE_SAMPLE_ID:
            out.append("%s: sample card id %s != pinned id %s" % (name, card_id, HOMEPAGE_SAMPLE_ID))
        if placard_ids != [HOMEPAGE_SAMPLE_ID]:
            out.append("%s: default placard vehicle references %s != [%s]"
                       % (name, placard_ids, HOMEPAGE_SAMPLE_ID))
        if "||" in body or "DB.v" in body:
            out.append("%s: default placard contains a hidden fallback" % name)
        card = re.search(r'id="kyr-sample".*?</button>', text, re.S)
        if not card or label not in card.group(0):
            out.append("%s: sample card label does not match blob identity %r" % (name, label))
            continue
        card_html = card.group(0)
        expected_values = (
            ("viscosity", expected["oil_visc"]),
            ("capacity", expected["oil_cap_w"]),
            ("recall count", "%d Open Recalls" % expected["recall_count"]),
        )
        for field, value in expected_values:
            if not value or str(value) not in card_html:
                out.append("%s: sample card is missing blob-derived %s %r"
                           % (name, field, value))
    return out


COUNT_COPY_PATTERNS = (
    ("description/OG/H1", r"vehicles searchable[;,]\s*(\d+)\s+with owner's-manual-verified specifications", 3),
    ("database badge", r'class="db-badge">[^<]*?\b(\d+) OWNER\'S-MANUAL-VERIFIED', 1),
    ("hero badge", r">(\d+) Owner's-Manual-Verified<", 1),
    ("About statistic", r'<div class="astat-n">(\d+)</div><div class="astat-l">Verified Specs</div>', 1),
    ("Pro coverage", r"Owner's-manual-verified maintenance schedules &mdash; (\d+) vehicles and growing", 1),
)


def s9_4_ic01_count_copy(a):
    verified = sum(
        1 for v in a.D["v"]
        if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1
    )
    out = []
    for name, text in (("index.html", a.index), ("wrench_demo.html", a.demo_markup)):
        for label, pattern, expected_matches in COUNT_COPY_PATTERNS:
            values = [int(x) for x in re.findall(pattern, text)]
            if values != [verified] * expected_matches:
                out.append("%s: %s count(s) %s != %s"
                           % (name, label, values, [verified] * expected_matches))
    readme_patterns = (
        ("summary", r"vehicles searchable;\s*(\d+)\s+with owner's-manual-verified specifications"),
        ("coverage", r"Coverage:\s*\*\*(\d+) vehicles with owner's-manual-verified specifications"),
    )
    for label, pattern in readme_patterns:
        values = [int(x) for x in re.findall(pattern, a.readme)]
        if values != [verified]:
            out.append("README.md: %s count %s != [%s]" % (label, values, verified))
    return out


def s9_5_demo_blob_equivalence(a):
    if not a.demo_json_raw:
        return ["wrench_demo.html inline dataset missing or unparseable"]
    if not a.blob_json_raw:
        return ["deploy blob dataset missing or unparseable"]
    if a.demo_json_raw != a.blob_json_raw:
        return ["wrench_demo.html inline dataset differs byte-for-byte from the deploy blob"]
    return []


def s9_7_mobile_nav_containment(a):
    """The 390px proof must keep the primary navigation inside its own scroll rail."""
    out = []
    containment = re.compile(
        r"(?<![-\w])\.tabs\s*\{[^{}]*overflow-x\s*:\s*auto\s*;"
        r"[^{}]*-webkit-overflow-scrolling\s*:\s*touch\s*;?[^{}]*\}",
        flags=re.S,
    )
    for surface, markup in (("wrench_demo.html", a.demo_markup),
                            ("wrench_deploy/index.html", a.index)):
        if not containment.search(markup):
            out.append("%s does not contain the mobile primary-navigation rail" % surface)
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


def s9_6_ic01_source_scope(a):
    out = []
    if _ver(QUARANTINE_SOURCE) != 0:
        out.append("quarantine source token computes ver=1")

    con = _db(a)
    cur = con.cursor()
    ids = tuple(sorted(QUARANTINED_VEHICLE_IDS))
    placeholders = ",".join("?" for _ in ids)
    for table, expected in EXPECTED_DB_ROWS.items():
        rows = list(cur.execute(
            "SELECT vehicle_id, source FROM %s WHERE vehicle_id IN (%s)"
            % (table, placeholders),
            ids,
        ))
        if len(rows) != expected:
            out.append("%s has %d IC-01 row(s), expected %d" % (table, len(rows), expected))
        per_id = {}
        for row in rows:
            per_id[row["vehicle_id"]] = per_id.get(row["vehicle_id"], 0) + 1
            if row["source"] != QUARANTINE_SOURCE:
                out.append("%s vehicle %s source %r is not the exact quarantine token"
                           % (table, row["vehicle_id"], row["source"]))
        expected_per_id = 3 if table == "maintenance" else 1
        if per_id != {vehicle_id: expected_per_id for vehicle_id in ids}:
            out.append("%s per-vehicle IC-01 row counts %s are not %d each"
                       % (table, per_id, expected_per_id))

    # Exact token and every string containing it are reserved for this cohort and these
    # five tables. This rejects both outsider use and accepted-source concatenation.
    source_tables = []
    table_names = [row["name"] for row in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )]
    for table in table_names:
        quoted = '"%s"' % table.replace('"', '""')
        columns = {column["name"] for column in cur.execute("PRAGMA table_info(%s)" % quoted)}
        if {"vehicle_id", "source"}.issubset(columns):
            source_tables.append(table)
    for table in source_tables:
        quoted = '"%s"' % table.replace('"', '""')
        rows = cur.execute(
            "SELECT vehicle_id, source FROM %s WHERE source LIKE ?" % quoted,
            ("%" + QUARANTINE_SOURCE + "%",),
        )
        for row in rows:
            allowed = (
                table in EXPECTED_DB_ROWS
                and row["vehicle_id"] in QUARANTINED_VEHICLE_IDS
                and row["source"] == QUARANTINE_SOURCE
            )
            if not allowed:
                out.append("%s vehicle %s uses reserved quarantine token in source %r"
                           % (table, row["vehicle_id"], row["source"]))
    con.close()
    return out

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
        with open(tmp, "rb") as f:
            fresh = f.read()
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    with open(a.specs_path, "rb") as f:
        committed = f.read()
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

def s5_8_incident_date_matches_db(a):
    """The shipped comps_agg.through must equal the DB-derived clamped max incident month for
    that year/make/model identity -- and must NOT be a hardcoded literal (values must vary and
    match the DB). Recompute independently from the complaints table."""
    con = _db(a)
    cur = con.cursor()
    ymm = {}
    for vid, y, mk, md in cur.execute("SELECT id,year,make,model FROM vehicles"):
        ymm[vid] = (y, mk, md)
    dbmax = {}   # (y,mk,md) -> (year, month) of clamped max incident date
    for vid, dt in cur.execute("SELECT vehicle_id, incident_date FROM complaints"):
        key = ymm.get(vid)
        if not key or not dt:
            continue
        try:
            m, d, yr = dt.split("/"); yr = int(yr); m = int(m)
        except Exception:
            continue
        floor = max(1990, (key[0] or 0) - 2)
        if yr < floor:
            continue
        cur_best = dbmax.get(key)
        if cur_best is None or (yr, m) > cur_best:
            dbmax[key] = (yr, m)
    con.close()
    out = []
    seen_through = set()
    checked = 0
    for v in a.D["v"]:
        agg = v.get("comps_agg")
        if not agg or "through" not in agg:
            continue
        seen_through.add(agg["through"])
        key = (v.get("year"), v.get("make"), v.get("model"))
        want = dbmax.get(key)
        want_s = ("%04d-%02d" % want) if want else None
        if want_s and agg["through"] != want_s:
            out.append("vehicle %s comps_agg.through=%s but DB-derived=%s" % (v.get("id"), agg["through"], want_s))
        checked += 1
        if len(out) >= 5:
            break
    if checked and len(seen_through) < 2:
        out.append("comps_agg.through is invariant across %d vehicles (looks hardcoded, not DB-derived)" % checked)
    return out

def s5_9_guidance_count(a):
    """DB-tier (2026-07-14 threshold ruling): a verified pairing may surface a BELOW-threshold topic,
    but its count must be honest. Every shipped guidance object's `topic` must be a real normalized
    complaint component for the vehicle's year/make/model, and `tcount`/`n` must equal the DB-derived
    distinct-ODI counts. Recomputed independently. Vacuous when zero guidance ships (pipeline-only)."""
    have = [v for v in a.D["v"] if v.get("guidance")]
    if not have:
        return []
    con = _db(a); cur = con.cursor()
    ymm = {vid: (y, mk, md) for vid, y, mk, md in cur.execute("SELECT id,year,make,model FROM vehicles")}
    rows_by_key = {}
    for vid, cn, comp in cur.execute("SELECT vehicle_id,complaint_number,component FROM complaints"):
        key = ymm.get(vid)
        if key:
            rows_by_key.setdefault(key, {})[cn] = comp
    con.close()
    csplit = re.compile(r",(?! )")
    def counts(key):
        odi = rows_by_key.get(key, {})
        tc = {}
        for comp in odi.values():
            seen = set()
            for part in csplit.split(comp or ""):
                t = part.split(", ")[0].strip()
                if t and t != "UNKNOWN OR OTHER":
                    seen.add(t)
            for t in seen:
                tc[t] = tc.get(t, 0) + 1
        return tc, len(odi)
    out = []
    for v in have:
        tc, n = counts((v.get("year"), v.get("make"), v.get("model")))
        for g in v["guidance"]:
            t = g.get("topic")
            if t not in tc:
                out.append("vehicle %s guidance topic %r is not a real complaint component for this vehicle" % (v.get("id"), t))
            elif g.get("tcount") != tc[t]:
                out.append("vehicle %s guidance tcount=%s but DB=%s for %r" % (v.get("id"), g.get("tcount"), tc[t], t))
            if g.get("n") != n:
                out.append("vehicle %s guidance n=%s but DB=%s" % (v.get("id"), g.get("n"), n))
            if len(out) >= 5:
                return out
    return out

def s5_11_comps_agg_db(a):
    """[DB] Full projection equivalence (2026-07-14, post-Deploy-B guard commit): independently
    recompute every identity's complaint aggregate from the complaints table -- distinct-ODI
    dedup, PARENT-COLLAPSED topics (collapse BEFORE any threshold), top-6 by (-count, label),
    crash/fire/injury/death sums -- and assert the shipped comps_agg matches per vehicle, plus
    coverage equivalence (exactly the vehicles whose identity has complaint rows ship an agg).
    Mirror uses the simple comma-heuristic (split on ",(?! )", keep text before ", ") which
    provably agrees with the generator's vocabulary parser on the entire corpus (byte-identical
    blob, 2026-07-14) -- two DIFFERENT algorithms that must agree, so drift in either fires
    here. Catches ANY projection drift, not just the split (S5.10 is the CI tripwire).
    `through` equivalence stays in S5.8; topic-vs-guidance count honesty stays in S5.9."""
    con = _db(a)
    cur = con.cursor()
    ymm = {vid: (y, mk, md) for vid, y, mk, md in cur.execute("SELECT id,year,make,model FROM vehicles")}
    rows_by_key = {}
    for vid, cn, comp, crash, fire, inj, deaths in cur.execute(
            "SELECT vehicle_id,complaint_number,component,crash,fire,injury,deaths FROM complaints"):
        key = ymm.get(vid)
        if key:
            rows_by_key.setdefault(key, {})[cn] = (comp, 1 if crash else 0, 1 if fire else 0,
                                                   int(inj or 0), int(deaths or 0))
    con.close()
    csplit = re.compile(r",(?! )")
    memo = {}
    def agg_for(key):
        if key in memo:
            return memo[key]
        odi = rows_by_key.get(key)
        if not odi:
            memo[key] = None
            return None
        tc = {}
        crash = fire = inj = deaths = 0
        for comp, c, f, i, d in odi.values():
            seen = set()
            for part in csplit.split(comp or ""):
                t = part.split(", ")[0].strip()
                if t and t != "UNKNOWN OR OTHER":
                    seen.add(t)
            for t in seen:
                tc[t] = tc.get(t, 0) + 1
            crash += c; fire += f; inj += i; deaths += d
        topics = sorted(tc.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
        memo[key] = {"n": len(odi), "topics": [[t, c] for t, c in topics],
                     "crash": crash, "fire": fire, "inj": inj, "deaths": deaths}
        return memo[key]
    out = []
    for v in a.D["v"]:
        want = agg_for((v.get("year"), v.get("make"), v.get("model")))
        got = v.get("comps_agg")
        if want is None:
            if got:
                out.append("vehicle %s ships comps_agg but the DB has no complaint rows for its identity" % v.get("id"))
        elif not got:
            out.append("vehicle %s missing comps_agg (DB has %d complaint rows for its identity)"
                       % (v.get("id"), want["n"]))
        else:
            for f in ("n", "crash", "fire", "inj", "deaths"):
                if got.get(f) != want[f]:
                    out.append("vehicle %s comps_agg.%s=%r but DB-derived=%r" % (v.get("id"), f, got.get(f), want[f]))
            if got.get("topics") != want["topics"]:
                out.append("vehicle %s comps_agg.topics diverges from the DB-derived projection "
                           "(shipped %r... vs derived %r...)"
                           % (v.get("id"), (got.get("topics") or [])[:2], want["topics"][:2]))
        if len(out) >= 5:
            break
    return out

# ---------------------------------------------------------------- registry / main

# ---------------------------------------------------------------- S10: IC-02 exact-token source registry
# files/source_registry.py is the single PRODUCTION classifier for the gate.
# This section never lets the registry verify itself: every expectation below is
# pinned INDEPENDENTLY -- an independent parser, independently pinned token/table
# scopes, literal adversarial fixtures, and literal hashes. The mapping hash
# (S10.2) is a drift TRIPWIRE, not the correctness proof; correctness comes from
# the fixture contract (S10.1) and the DB-census agreement sweep (S10.4).

_S10_DELIMITER = " ("
# Pinned LITERAL spelling (never the ic01_quarantine/registry import): a
# coordinated token rename must fail the fixture contract and the census, not
# just the S10.2 mapping hash.
_S10_QUARANTINE = "quarantine-applicability-ic01"
_S10_VERIFIED = {
    "owner-manual-verified": ("oil_change", "parts", "fluids", "torque_specs"),
    "Buick Owner's Manual": ("maintenance",),
    "Cadillac Owner's Manual": ("maintenance",),
    "Chevrolet Owner's Manual": ("maintenance",),
    "Ford Owner's Manual": ("maintenance",),
    "GMC Owner's Manual": ("maintenance",),
    "Honda Owner's Manual": ("maintenance",),
    "Hyundai Owner's Manual": ("maintenance",),
    "Lincoln Owner's Manual": ("maintenance",),
    "Mazda Owner's Manual": ("maintenance",),
    "Nissan Owner's Manual": ("maintenance",),
    "Owner's Manual": ("maintenance",),
    "Subaru Owner's Manual": ("maintenance",),
}
_S10_UNVERIFIED = {
    "ai-haiku-4.5": ("oil_change", "parts", "fluids", "torque_specs",
                     "engine_specs", "maintenance"),
    "scraped": ("oil_change", "parts", "fluids", "torque_specs",
                "engine_specs", "maintenance"),
    "unknown": ("oil_change", "parts", "fluids", "torque_specs", "engine_specs"),
    "engine_classifier_v1": ("maintenance",),
    _S10_QUARANTINE: ("oil_change", "parts", "fluids", "torque_specs",
                      "maintenance"),
}
_S10_MARKERS = ("ai-", "haiku", "scraped", "classifier", "quarantine-applicability",
                "unknown", "epa-manufacturer-specs")
_S10_SOURCE_TABLES = frozenset({
    "oil_change", "parts", "fluids", "torque_specs", "engine_specs",
    "maintenance", "ev_specs", "fuse_locations", "vehicle_notes",
})
_S10_BARE_COUNT = 424
_S10_BARE_SHA256 = "ca156c69ed4cc8df34ff1244a612d497494a725ec3efcdd7d502f2aa179c8980"
_S10_MAPPING_SHA256 = "4e8447602ec0f67464d4decddcecbeb09f190e4a5b1796e281e4b12764065674"
_S10_EV_ROWS = 75
_S10_EV_SOURCE = "epa-manufacturer-specs"


def _s10_verdict(src, table):
    """Independent small parser: 1 / 0 / "fail" from THIS module's pinned scopes
    only (no source_registry import). Byte-exact token, split once on " (",
    opaque suffix except blacklist markers under a verified token."""
    if not isinstance(src, str) or not src or src != src.strip():
        return "fail"
    token, sep, suffix = src.partition(_S10_DELIMITER)
    if sep and not suffix:
        return "fail"
    if token in _S10_VERIFIED:
        if table not in _S10_VERIFIED[token]:
            return "fail"
        if sep and any(m in suffix.lower() for m in _S10_MARKERS):
            return "fail"
        return 1
    if token in _S10_UNVERIFIED:
        if table not in _S10_UNVERIFIED[token]:
            return "fail"
        if token == _S10_QUARANTINE and sep:
            return "fail"
        return 0
    return "fail"


# (source, table, vehicle_id, expected 1/0/"raise") -- expectations are literal.
_S10_FIXTURES = (
    ("owner-manual-verified", "oil_change", None, 1),
    ("owner-manual-verified", "parts", None, 1),
    ("owner-manual-verified", "fluids", None, 1),
    ("owner-manual-verified", "torque_specs", None, 1),
    ("Honda Owner's Manual", "maintenance", None, 1),
    ("owner-manual-verified (2019 Silverado 1500 OM p.337)", "oil_change", None, 1),
    ("GMC Owner's Manual (Sierra 2500HD) + 6.6L Duramax Supplement",
     "maintenance", None, 1),                      # real irregular legacy suffix
    ("ai-haiku-4.5", "maintenance", None, 0),
    ("scraped", "oil_change", None, 0),
    ("unknown", "engine_specs", None, 0),
    ("engine_classifier_v1", "maintenance", None, 0),
    (_S10_QUARANTINE, "oil_change", 12372, 0),
    ("scraped (owner-manual-verified)", "oil_change", None, 0),  # citation != source
    (None, "oil_change", None, "raise"),
    ("", "oil_change", None, "raise"),
    (" owner-manual-verified", "oil_change", None, "raise"),
    ("owner-manual-verified ", "oil_change", None, "raise"),
    ("Owner-Manual-Verified", "oil_change", None, "raise"),
    ("HONDA OWNER'S MANUAL", "maintenance", None, "raise"),
    ("Toyota Owner's Manual", "maintenance", None, "raise"),   # unobserved make
    ("scraped-owner-manual", "oil_change", None, "raise"),
    ("owner-manual-verified+scraped", "oil_change", None, "raise"),
    ("owner-manual-verified (", "oil_change", None, "raise"),
    ("owner-manual-verified (backfilled from scraped table)", "oil_change", None, "raise"),
    ("owner-manual-verified (unknown)", "oil_change", None, "raise"),
    ("owner-manual-verified (epa-manufacturer-specs)", "parts", None, "raise"),
    ("owner-manual-verified (SCRAPED copy)", "oil_change", None, "raise"),
    ("owner-manual-verified (Unknown provenance)", "fluids", None, "raise"),
    ("owner-manual-verified (EPA-Manufacturer-Specs)", "torque_specs", None, "raise"),
    ("owner-manual-verified (AI-Haiku assisted)", "parts", None, "raise"),
    ("owner-manual-verified (Engine_Classifier_V1)", "fluids", None, "raise"),
    ("Honda Owner's Manual (QUARANTINE-APPLICABILITY-IC01)", "maintenance", None, "raise"),
    ("owner-manual-verified", "maintenance", None, "raise"),   # wrong table
    ("owner-manual-verified", "engine_specs", None, "raise"),  # wrong table
    ("Honda Owner's Manual", "oil_change", None, "raise"),     # wrong table
    (_S10_QUARANTINE + " (x)", "oil_change", 12372, "raise"),
    (_S10_QUARANTINE, "oil_change", 467, "raise"),             # outside cohort
    ("epa-manufacturer-specs", "oil_change", None, "raise"),
    ("epa-manufacturer-specs", "ev_specs", None, "raise"),     # blocked table
    ("owner-manual-verified", "ev_specs", None, "raise"),
    ("owner-manual-verified", "fuse_locations", None, "raise"),
    ("owner-manual-verified", "zz_brand_new_table", None, "raise"),  # no disposition
)


def s10_1_registry_contract(a):
    from files.source_registry import SourceRegistryError, classify
    out = []
    for src, table, vid, expected in _S10_FIXTURES:
        try:
            got = classify(src, table, vehicle_id=vid)
        except SourceRegistryError:
            got = "raise"
        if got != expected:
            out.append("classify(%r, %r, vehicle_id=%r) -> %r, pinned %r"
                       % (src, table, vid, got, expected))
    return out


def s10_2_registry_mapping_pin(a):
    import files.source_registry as sr
    payload = {
        "delimiter": sr.TOKEN_DELIMITER,
        "verified": {t: sorted(v) for t, v in sr.VERIFIED_TOKEN_TABLES.items()},
        "unverified": {t: sorted(v) for t, v in sr.UNVERIFIED_TOKEN_TABLES.items()},
        "markers": sorted(sr.BLACKLIST_SUFFIX_MARKERS),
        "dispositions": sr.TABLE_DISPOSITIONS,
        "bare": [sr.BARE_VERIFIED_TOKEN, list(sr.BARE_ROW_TABLES),
                 sr.BARE_ROW_COUNT, sr.BARE_ROW_SHA256],
        "ev": [sr.EV_TABLE, sr.EV_FROZEN_ROW_COUNT, sr.EV_FROZEN_SOURCE],
    }
    canon = json.dumps(payload, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":"))
    got = hashlib.sha256(canon.encode()).hexdigest()
    if got != _S10_MAPPING_SHA256:
        return ["registry mapping drifted: canonical sha256 %s != pinned %s "
                "(a mapping change needs a ruling + a deliberate pin update)"
                % (got, _S10_MAPPING_SHA256)]
    return []


def s10_3_generator_wiring(a):
    """Structural (AST) wiring proof at call-graph strength (IC-02 final
    correction 1): a call that merely EXISTS somewhere is not wiring. For each
    generator this proves the gates are direct statements of main() ordered
    BEFORE any projection/template/backup/write access, that the admission scan
    invokes the imported classifier, that every gated projection classifies, and
    that the imported registry symbols are never rebound or shadowed. Calls
    hidden in uncalled helpers or `if False:` blocks do not count (only Try
    bodies are linearized into main's statement order). Expectations are pinned
    here, never derived from the registry."""
    import ast

    REGISTRY_MODULES = ("source_registry", "files.source_registry")

    def linearize(body):
        flat = []
        for stmt in body:
            if isinstance(stmt, ast.Try):
                flat.extend(linearize(stmt.body))
                flat.extend(linearize(stmt.finalbody))
            else:
                flat.append(stmt)
        return flat

    def direct_call_name(stmt):
        if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)):
            return stmt.value.func.id
        return None

    def calls_to(node, name):
        return [sub for sub in ast.walk(node)
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                and sub.func.id == name]

    def stmt_is_dangerous(stmt, extra_names):
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Call):
                f = sub.func
                if isinstance(f, ast.Name) and (f.id == "open" or f.id in extra_names):
                    return True
                if isinstance(f, ast.Attribute) and f.attr in ("copy2", "copy", "write"):
                    return True
        return False

    def is_r_vehicle_id(node):
        return (isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name) and node.value.id == "r"
                and isinstance(node.slice, ast.Constant)
                and node.slice.value == "vehicle_id")

    def is_proper_classify(call, classify_name, table):
        """A LIVE projection classifier call: the imported classifier, the same
        literal table, and the row's vehicle_id."""
        return (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                and call.func.id == classify_name and len(call.args) >= 3
                and isinstance(call.args[1], ast.Constant)
                and call.args[1].value == table
                and is_r_vehicle_id(call.args[2]))

    def direct_gate_expr(stmt, fn_name):
        return (direct_call_name(stmt) == fn_name
                and len(stmt.value.args) == 1
                and isinstance(stmt.value.args[0], ast.Name)
                and stmt.value.args[0].id == "cur")

    def protected_names(rel, tree, names, out):
        """Pinned function names: defined exactly once, never rebound -- not by
        assignment, import, class, or a second definition anywhere."""
        for name in names:
            defs = [n for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.ClassDef)) and n.name == name]
            if len(defs) != 1:
                out.append("%s: pinned function %r must be defined exactly once "
                           "(found %d)" % (rel, name, len(defs)))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
                    and node.id in names):
                out.append("%s rebinds pinned function %r (line %d)"
                           % (rel, node.id, node.lineno))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if (alias.asname or alias.name.split(".")[0]) in names:
                        out.append("%s rebinds pinned function %r via import "
                                   "(line %d)"
                                   % (rel, alias.asname or alias.name, node.lineno))

    def try_gate_discipline(rel, main_fn, gates, out):
        """Inside main's connection try block: the `cur` assignment, then the
        direct gate calls IMMEDIATELY -- no control flow, raise, or any other
        statement may precede them, so the gates are unconditionally reachable."""
        try_node = next((s for s in main_fn.body if isinstance(s, ast.Try)), None)
        if try_node is None:
            out.append("%s: main() has no connection try block" % rel)
            return
        pending = list(gates)
        seen_cur = False
        for stmt in try_node.body:
            if not pending:
                break
            if (not seen_cur and isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and stmt.targets[0].id == "cur"):
                seen_cur = True
                continue
            if direct_gate_expr(stmt, pending[0]):
                pending.pop(0)
                continue
            out.append("%s: inside the connection try block %r must directly "
                       "follow the cur assignment (found %s first)"
                       % (rel, pending[0], type(stmt).__name__))
            return
        if pending:
            out.append("%s: connection try block never reaches %s(cur)"
                       % (rel, pending[0]))

    def each_projection_coverage(rel, build_fn, classify_name, out):
        """Every gated projection is a DIRECT `each("<table>", lambda...)`
        statement of build_data whose emitted `ver` value is a live classifier
        call with the same literal table and the row vehicle_id. Dead or dummy
        calls anywhere else never satisfy coverage."""
        covered = set()
        for stmt in linearize(build_fn.body):
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Name)
                    and stmt.value.func.id == "each"):
                continue
            call = stmt.value
            if (len(call.args) < 2 or not isinstance(call.args[0], ast.Constant)
                    or call.args[0].value not in GATE_TABLES):
                continue
            table = call.args[0].value
            lam = call.args[1]
            if not isinstance(lam, ast.Lambda):
                out.append("%s: each(%r, ...) projection is not a lambda"
                           % (rel, table))
                continue
            ver_values = []
            for node in ast.walk(lam):
                if isinstance(node, ast.Dict):
                    for key, value in zip(node.keys, node.values):
                        if isinstance(key, ast.Constant) and key.value == "ver":
                            ver_values.append(value)
            if not ver_values:
                out.append("%s: each(%r, ...) emits no ver key" % (rel, table))
            elif all(is_proper_classify(v, classify_name, table)
                     for v in ver_values):
                covered.add(table)
            else:
                out.append("%s: each(%r, ...) emits a ver value that is not the "
                           "imported classifier with the literal table and row "
                           "vehicle_id" % (rel, table))
        missing = [t for t in GATE_TABLES if t not in covered]
        if missing:
            out.append("%s: build_data lacks live classified projection(s) for %s"
                       % (rel, missing))

    def guide_loop_coverage(rel, main_fn, classify_name, out):
        """Each real guide table loop's ACTIVE guard (first statement of the
        loop body) must directly invoke the imported classifier with the
        matching literal table and row vehicle_id."""
        required = ("oil_change", "parts", "torque_specs")
        covered = set()
        for stmt in linearize(main_fn.body):
            if not isinstance(stmt, ast.For):
                continue
            it = stmt.iter
            if not (isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute)
                    and it.func.attr == "execute" and it.args
                    and isinstance(it.args[0], ast.Constant)
                    and isinstance(it.args[0].value, str)):
                continue
            sql = it.args[0].value
            for table in required:
                if ("FROM %s" % table) not in sql:
                    continue
                guard = stmt.body[0] if stmt.body else None
                if (isinstance(guard, ast.If)
                        and any(is_proper_classify(n, classify_name, table)
                                for n in ast.walk(guard.test))):
                    covered.add(table)
                else:
                    out.append("%s: the %s loop guard does not directly invoke "
                               "the imported classifier with the literal table "
                               "and row vehicle_id" % (rel, table))
        missing = [t for t in required if t not in covered]
        if missing:
            out.append("%s: main() lacks live classified guide loop(s) for %s"
                       % (rel, missing))

    def analyze(rel, txt, out):
        try:
            tree = ast.parse(txt)
        except SyntaxError as e:
            out.append("%s does not parse: %r" % (rel, e))
            return None, None, None
        aliases = {}   # local binding name -> registry symbol name
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in REGISTRY_MODULES:
                for alias in node.names:
                    aliases[alias.asname or alias.name] = alias.name
        for node in ast.walk(tree):
            if (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
                    and node.id in aliases):
                out.append("%s rebinds imported registry symbol %r (line %d)"
                           % (rel, node.id, node.lineno))
            elif (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    and node.name in aliases):
                out.append("%s shadows imported registry symbol %r with a local "
                           "definition (line %d)" % (rel, node.name, node.lineno))
            elif isinstance(node, ast.arg) and node.arg in aliases:
                out.append("%s shadows imported registry symbol %r with a "
                           "parameter" % (rel, node.arg))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if (alias.asname or alias.name.split(".")[0]) in aliases:
                        out.append("%s rebinds imported registry symbol %r via "
                                   "import (line %d)"
                                   % (rel, alias.asname or alias.name, node.lineno))
            elif (isinstance(node, ast.ImportFrom)
                    and node.module not in REGISTRY_MODULES):
                for alias in node.names:
                    if (alias.asname or alias.name) in aliases:
                        out.append("%s rebinds imported registry symbol %r from "
                                   "module %r (line %d)"
                                   % (rel, alias.asname or alias.name, node.module,
                                      node.lineno))
        funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        return tree, aliases, funcs

    out = []

    # ---------------- files/04_rebuild_demo.py
    rel = os.path.join("files", "04_rebuild_demo.py")
    txt = a._read(os.path.join(a.root, rel))
    if not txt:
        out.append("%s missing or unreadable" % rel)
    else:
        tree, aliases, funcs = analyze(rel, txt, out)
        if tree is not None:
            local = {sym: name for name, sym in aliases.items()}
            classify_name = local.get("classify")
            afl_name = local.get("assert_frozen_landscape")
            main_fn = funcs.get("main")
            adm_fn = funcs.get("_assert_registry_admission")
            build_fn = funcs.get("build_data")
            if not classify_name or not afl_name:
                out.append("%s does not import classify + assert_frozen_landscape "
                           "from the shared source registry" % rel)
            elif main_fn is None or adm_fn is None or build_fn is None:
                out.append("%s is missing main / _assert_registry_admission / "
                           "build_data" % rel)
            else:
                protected_names(
                    rel, tree,
                    ("main", "build_data", "_assert_registry_admission"), out)
                try_gate_discipline(
                    rel, main_fn, ["_assert_registry_admission", afl_name], out)
                flat = linearize(main_fn.body)
                gate_i = {}
                for i, stmt in enumerate(flat):
                    name = direct_call_name(stmt)
                    if name == "_assert_registry_admission":
                        gate_i.setdefault("_assert_registry_admission", i)
                    elif name == afl_name:
                        gate_i.setdefault(afl_name, i)
                danger_i = len(flat)
                for i, stmt in enumerate(flat):
                    if stmt_is_dangerous(stmt, {"build_data"}):
                        danger_i = i
                        break
                for gate in ("_assert_registry_admission", afl_name):
                    if gate not in gate_i:
                        out.append("%s: main() does not call %s(cur) as a direct "
                                   "statement" % (rel, gate))
                    elif gate_i[gate] >= danger_i:
                        out.append("%s: main() calls %s only after build/template/"
                                   "backup/write access" % (rel, gate))
                if not calls_to(adm_fn, classify_name):
                    out.append("%s: _assert_registry_admission never invokes the "
                               "imported classifier" % rel)
                each_projection_coverage(rel, build_fn, classify_name, out)
        if '"owner" in s' in txt:
            out.append("%s still contains the copied substring whitelist gate" % rel)
        if re.search(r"^def _ver\(", txt, flags=re.M):
            out.append("%s still defines a local _ver classifier" % rel)

    # ---------------- _gen_guide_specs.py
    rel = "_gen_guide_specs.py"
    txt = a._read(os.path.join(a.root, rel))
    if not txt:
        out.append("%s missing or unreadable" % rel)
    else:
        tree, aliases, funcs = analyze(rel, txt, out)
        if tree is not None:
            local = {sym: name for name, sym in aliases.items()}
            classify_name = local.get("classify")
            afl_name = local.get("assert_frozen_landscape")
            main_fn = funcs.get("main")
            if not classify_name or not afl_name:
                out.append("%s does not import classify + assert_frozen_landscape "
                           "from the shared source registry" % rel)
            elif main_fn is None:
                out.append("%s is missing main()" % rel)
            else:
                protected_names(rel, tree, ("main",), out)
                try_gate_discipline(rel, main_fn, [afl_name], out)
                flat = linearize(main_fn.body)
                gate_at = None
                danger_i = len(flat)
                for i, stmt in enumerate(flat):
                    if gate_at is None and direct_call_name(stmt) == afl_name:
                        gate_at = i
                    if (stmt_is_dangerous(stmt, set())
                            or calls_to(stmt, classify_name)):
                        danger_i = i
                        break
                if gate_at is None:
                    out.append("%s: main() does not call %s(cur) as a direct "
                               "statement" % (rel, afl_name))
                elif gate_at >= danger_i:
                    out.append("%s: main() calls %s only after projection/output "
                               "access" % (rel, afl_name))
                guide_loop_coverage(rel, main_fn, classify_name, out)
        if '"owner" in s' in txt:
            out.append("%s still contains the copied substring whitelist gate" % rel)
        if re.search(r"^def _ver\(", txt, flags=re.M):
            out.append("%s still defines a local _ver classifier" % rel)
    return out


def s10_4_token_census(a):
    from files.source_registry import SourceRegistryError, classify
    con = _db(a)
    cur = con.cursor()
    pairs = []
    for t in GATE_TABLES:
        for (s,) in cur.execute("SELECT DISTINCT source FROM %s" % t).fetchall():
            pairs.append((s, t))
    con.close()
    out = []
    observed = {}
    for s, t in pairs:
        token = s.partition(_S10_DELIMITER)[0] if isinstance(s, str) else s
        observed.setdefault(token, set()).add(t)
    pinned = {}
    for token, tables in list(_S10_VERIFIED.items()) + list(_S10_UNVERIFIED.items()):
        pinned[token] = set(tables)
    if observed != pinned:
        unexpected = sorted("%r in %s" % (k, sorted(v - pinned.get(k, set())))
                            for k, v in observed.items() if v - pinned.get(k, set()))
        unobserved = sorted("%r in %s" % (k, sorted(set(pinned[k]) - observed.get(k, set())))
                            for k in pinned if set(pinned[k]) - observed.get(k, set()))
        out.append("token census drifted from pins: unexpected=%s unobserved=%s "
                   "(update pins only by ruling)" % (unexpected, unobserved))
    folded = {}
    for token in observed:
        if isinstance(token, str):
            folded.setdefault(token.lower(), []).append(token)
    collisions = {k: sorted(v) for k, v in folded.items() if len(v) > 1}
    if collisions:
        out.append("case-fold token collision(s): %s" % collisions)
    for s, t in pairs:
        independent = _s10_verdict(s, t)
        try:
            production = classify(s, t)
        except SourceRegistryError as e:
            production = "fail"
        if independent == "fail" or production == "fail":
            out.append("stored source rejected: %r in %s (independent=%r, registry=%r)"
                       % (s, t, independent, production))
        elif independent != production:
            out.append("classifier disagreement on %r in %s: independent=%r registry=%r"
                       % (s, t, independent, production))
    return out


def s10_5_bare_row_freeze(a):
    con = _db(a)
    cur = con.cursor()
    lines = []
    for table in ("oil_change", "parts", "fluids", "torque_specs"):
        cols = [r[1] for r in cur.execute('PRAGMA table_info("%s")' % table).fetchall()]
        keep = [i for i, c in enumerate(cols) if c != "source"]
        for row in cur.execute('SELECT * FROM "%s" WHERE source = ?' % table,
                               ("owner-manual-verified",)).fetchall():
            lines.append(json.dumps([table] + [[cols[i], row[i]] for i in keep],
                                    ensure_ascii=True, separators=(",", ":")))
    con.close()
    digest = hashlib.sha256()
    for line in sorted(lines):
        digest.update(line.encode())
        digest.update(b"\n")
    out = []
    if len(lines) != _S10_BARE_COUNT:
        out.append("bare owner-manual-verified rows: %d != frozen %d (citation-debt "
                   "freeze: new/changed verified rows need a provenance suffix)"
                   % (len(lines), _S10_BARE_COUNT))
    if digest.hexdigest() != _S10_BARE_SHA256:
        out.append("bare-row content digest %s != frozen %s"
                   % (digest.hexdigest(), _S10_BARE_SHA256))
    return out


def s10_6_table_disposition(a):
    import files.source_registry as sr
    con = _db(a)
    cur = con.cursor()
    names = [n for (n,) in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'").fetchall()]
    source_tables = set()
    for name in names:
        cols = {r[1] for r in cur.execute(
            'PRAGMA table_info("%s")' % name.replace('"', '""')).fetchall()}
        if "source" in cols:
            source_tables.add(name)
    con.close()
    out = []
    if source_tables != _S10_SOURCE_TABLES:
        out.append("source-bearing tables %s != pinned census %s (every new "
                   "source-bearing table needs an explicit disposition ruling)"
                   % (sorted(source_tables), sorted(_S10_SOURCE_TABLES)))
    if set(sr.TABLE_DISPOSITIONS) != _S10_SOURCE_TABLES:
        out.append("registry dispositions %s != pinned census %s"
                   % (sorted(sr.TABLE_DISPOSITIONS), sorted(_S10_SOURCE_TABLES)))
    return out


def s10_7_ev_freeze(a):
    con = _db(a)
    cur = con.cursor()
    out = []
    n = cur.execute("SELECT COUNT(*) FROM ev_specs").fetchone()[0]
    if n != _S10_EV_ROWS:
        out.append("ev_specs has %d row(s); frozen at %d pending IC-02E" % (n, _S10_EV_ROWS))
    sources = {s for (s,) in cur.execute("SELECT DISTINCT source FROM ev_specs").fetchall()}
    if sources != {_S10_EV_SOURCE}:
        out.append("ev_specs sources %s; frozen at exactly %r pending IC-02E"
                   % (sorted(map(repr, sources)), _S10_EV_SOURCE))
    for t in GATE_TABLES:
        leak = cur.execute("SELECT COUNT(*) FROM %s WHERE source = ?" % t,
                           (_S10_EV_SOURCE,)).fetchone()[0]
        if leak:
            out.append("%d %r row(s) in gated table %s (never a verified token)"
                       % (leak, _S10_EV_SOURCE, t))
    con.close()
    if _s10_verdict(_S10_EV_SOURCE, "ev_specs") != "fail":
        out.append("independent parser accepted %r in ev_specs" % _S10_EV_SOURCE)
    return out


CHECKS = [
    ("S1.1-ver0-shell",          "FAIL", "CI", s1_1_ver0_shell),
    ("S1.2-forbidden-strings",   "FAIL", "CI", s1_2_forbidden_strings),
    ("S1.3/S6.1-notes-gate",     "FAIL", "CI", s1_3_notes_gate),
    ("S1.4-narratives-gone",     "FAIL", "CI", s1_4_narratives_gone),
    ("S1.9-paid-feature-gate",   "FAIL", "CI", s1_9_paid_feature_gate),
    ("S1.10-field-allowlist",    "FAIL", "CI", s1_10_vehicle_field_allowlist),
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
    ("S5.2-complaints-surface",  "FAIL", "CI", s5_2_complaints_surface),
    ("S5.3-hero-badge",          "FAIL", "CI", s5_3_hero_badge),
    ("S5.4-agg-pii",             "WARN", "CI", s5_4_agg_pii),
    ("S5.5-labeled-count",       "FAIL", "CI", s5_5_labeled_count),
    ("S5.6-incident-date-copy",  "FAIL", "CI", s5_6_incident_date_phrasing),
    ("S5.7-tsb-gate",            "FAIL", "CI", s5_7_tsb_gate),
    ("S5.10-collapse-canary",    "FAIL", "CI", s5_10_collapse_canary),
    ("S6.2-no-documented-framing","FAIL", "CI", s6_2_no_documented_framing),
    ("S6.3-empty-state",         "FAIL", "CI", s6_3_empty_state),
    ("S7.1-footer-required",     "FAIL", "CI", s7_1_footer_required),
    ("S7.2-footer-forbidden",    "FAIL", "CI", s7_2_footer_forbidden),
    ("S7.3-paywall-copy",        "FAIL", "CI", s7_3_paywall_copy),
    ("S7.4-obd-absent",          "FAIL", "CI", s7_4_obd_absent),
    ("S8.1-version-stamp",       "FAIL", "CI", s8_1_version_stamp),
    ("S8.2-two-file-drift",      "FAIL", "CI", s8_2_two_file_drift),
    ("S9.1-ic01-projection",     "FAIL", "CI", s9_1_ic01_projection),
    ("S9.2-ic01-guide-absent",   "FAIL", "CI", s9_2_ic01_guide_absent),
    ("S9.3-ic01-sample-pin",     "FAIL", "CI", s9_3_ic01_sample_pin),
    ("S9.4-ic01-count-copy",     "FAIL", "CI", s9_4_ic01_count_copy),
    ("S9.5-demo-blob-equivalence","FAIL", "CI", s9_5_demo_blob_equivalence),
    ("S9.7-mobile-nav-containment","FAIL", "CI", s9_7_mobile_nav_containment),
    ("S1.7-gate-equivalence",    "FAIL", "DB", s1_7_gate_equivalence),
    ("S1.8-gate-sources",        "FAIL", "DB", s1_8_gate_sources),
    ("S9.6-ic01-source-scope",   "FAIL", "DB", s9_6_ic01_source_scope),
    ("S4.4-specs-regen",         "FAIL", "DB", s4_4_specs_regen),
    ("S5.8-incident-date-db",    "FAIL", "DB", s5_8_incident_date_matches_db),
    ("S5.9-guidance-count-db",   "FAIL", "DB", s5_9_guidance_count),
    ("S5.11-comps-agg-db",       "FAIL", "DB", s5_11_comps_agg_db),
    ("S8.3-count-reconciliation","WARN", "DB", s8_3_count_reconciliation),
    ("S10.1-registry-contract",  "FAIL", "CI", s10_1_registry_contract),
    ("S10.2-registry-mapping-pin","FAIL", "CI", s10_2_registry_mapping_pin),
    ("S10.3-generator-wiring",   "FAIL", "CI", s10_3_generator_wiring),
    ("S10.4-token-census",       "FAIL", "DB", s10_4_token_census),
    ("S10.5-bare-row-freeze",    "FAIL", "DB", s10_5_bare_row_freeze),
    ("S10.6-table-disposition",  "FAIL", "DB", s10_6_table_disposition),
    ("S10.7-ev-freeze",          "FAIL", "DB", s10_7_ev_freeze),
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
