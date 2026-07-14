#!/usr/bin/env python
"""KYR TSB pairing tool (Block D-1, 2026-07-13) -- the mechanical gate for manufacturer-
communication guidance. A pairing links ONE NHTSA manufacturer communication to ONE
customer-complaint topic for ONE exact-applicable vehicle, and it can only exist as a
COMPLETE human-verification record. The generator emits guidance ONLY from complete rows;
the shipped-surfaces verifier (S5.7) rejects any guidance object lacking a valid record.

The human's approval IS the record: there is no "approve" flag to flip. Absent any required
field, the row is incomplete and the generator physically will not emit it.

Modes (never touches the 6 curated spec tables; only its own tsb_pairings table):
  init                            create the tsb_pairings table (idempotent) + flag truncated vehicles
  add   --spec pairing.json       capture one verified pairing (fetches + hashes the source URL)
  list                            list pairings with status
  recheck                         refetch every source_url; flag hash mismatches (supersession/rot)
  candidates --vehicle <id>       show substantive candidate bulletins for a vehicle (D-2 targeting)

Rights (D-1 ruling): ship a KYR-written one-line symptom + one-line service action, the confirmed
applicability, bulletin number/date/component, and the NHTSA document link. NEVER ship NHTSA's
abstract prose or a bulletin PDF.
"""
import argparse, hashlib, json, os, re, sqlite3, sys, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KYR-tsb-pairing"
OFFICIAL_HOSTS = ("static.nhtsa.gov", "www.nhtsa.gov", "nhtsa.gov")
CAP = 200            # the per-vehicle import cap (394 vehicles are truncated at exactly this)
SYM_MAX = 140        # KYR symptom/action length bound (short descriptor, never abstract prose)
ACT_MAX = 160

SCHEMA = """
CREATE TABLE IF NOT EXISTS tsb_pairings (
  id INTEGER PRIMARY KEY,
  vehicle_id INTEGER NOT NULL,
  complaint_topic TEXT NOT NULL,      -- normalized topic the verifier chose (must ship in comps_agg.topics)
  tsb_number TEXT NOT NULL,
  bulletin_date TEXT,
  component TEXT,                      -- NHTSA component from the tsb row (context only)
  applies_note TEXT NOT NULL,         -- applicability the verifier confirmed against the document
  symptom TEXT NOT NULL,              -- KYR-written, one line, <= SYM_MAX
  service_action TEXT NOT NULL,       -- KYR-written, one line, <= ACT_MAX
  source_url TEXT NOT NULL,           -- the NHTSA document reviewed
  source_hash TEXT NOT NULL,          -- md5 of the fetched document at verification time
  verified_by TEXT NOT NULL,
  verified_at TEXT NOT NULL,          -- ISO date
  superseded INTEGER NOT NULL DEFAULT 0,
  last_checked_at TEXT,
  UNIQUE(vehicle_id, tsb_number, complaint_topic)
);
-- internal truncation flag for D-2 targeting / future re-pull; never surfaced in the UI.
CREATE TABLE IF NOT EXISTS tsb_truncated (vehicle_id INTEGER PRIMARY KEY, tsb_count INTEGER);
"""

SPLIT = re.compile(r",(?! )")
def topics_for(cur, vehicle_id):
    """Recompute the SHIPPING complaint topics for a vehicle exactly as the generator does
    (year/make/model distinct-ODI union, normalized, >=3 and >=10% of n). The gate uses this
    to enforce that a chosen pairing topic actually reaches the user for this vehicle."""
    row = cur.execute("SELECT year,make,model FROM vehicles WHERE id=?", (vehicle_id,)).fetchone()
    if not row:
        return set(), 0
    ids = [r[0] for r in cur.execute("SELECT id FROM vehicles WHERE year IS ? AND make IS ? AND model IS ?", row)]
    odi = {}
    q = "SELECT complaint_number,component FROM complaints WHERE vehicle_id IN (%s)" % ",".join("?" * len(ids))
    for cn, comp in cur.execute(q, ids):
        odi[cn] = comp
    n = len(odi)
    tc = {}
    for comp in odi.values():
        seen = set()
        for part in SPLIT.split(comp or ""):
            t = part.split(", ")[0].strip()
            if t and t != "UNKNOWN OR OTHER":
                seen.add(t)
        for t in seen:
            tc[t] = tc.get(t, 0) + 1
    ship = {t for t, c in tc.items() if c >= 3 and n and c / n >= 0.10}
    return ship, n

def fetch_hash(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        body = r.read()
    return hashlib.md5(body).hexdigest(), len(body)

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def cmd_init(cur, con, args):
    cur.executescript(SCHEMA)
    # flag vehicles truncated at the import cap (internal only)
    cur.execute("DELETE FROM tsb_truncated")
    cur.execute("INSERT INTO tsb_truncated(vehicle_id,tsb_count) "
                "SELECT vehicle_id, COUNT(*) c FROM tsb GROUP BY vehicle_id HAVING c >= ?", (CAP,))
    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM tsb_truncated").fetchone()[0]
    print("tsb_pairings + tsb_truncated ready. flagged %d vehicles at/over the %d cap (internal)." % (n, CAP))

def cmd_add(cur, con, args):
    spec = json.load(open(args.spec, encoding="utf-8"))
    req = ["vehicle_id", "complaint_topic", "tsb_number", "applies_note", "symptom",
           "service_action", "source_url", "verified_by"]
    miss = [k for k in req if not spec.get(k)]
    if miss:
        sys.exit("INCOMPLETE pairing -- missing required field(s): %s (nothing written)" % miss)
    vid = int(spec["vehicle_id"])
    # 1) topic must actually ship for this vehicle
    ship, n = topics_for(cur, vid)
    if spec["complaint_topic"] not in ship:
        sys.exit("GATE: topic %r does not ship in this vehicle's complaint topics %s (n=%d). Refused."
                 % (spec["complaint_topic"], sorted(ship), n))
    # 2) source must be an official NHTSA host
    host = re.sub(r"^https?://", "", spec["source_url"]).split("/")[0].lower()
    if host not in OFFICIAL_HOSTS:
        sys.exit("GATE: source_url host %r is not an official NHTSA host. Refused." % host)
    # 3) KYR descriptors must be short (never abstract prose)
    if len(spec["symptom"]) > SYM_MAX or len(spec["service_action"]) > ACT_MAX:
        sys.exit("GATE: symptom/action exceed the length bound (%d/%d). Keep them one line." % (SYM_MAX, ACT_MAX))
    # 4) the bulletin must exist in the DB for this vehicle (context sanity)
    trow = cur.execute("SELECT tsb_number,date,component FROM tsb WHERE vehicle_id=? AND tsb_number=?",
                       (vid, spec["tsb_number"])).fetchone()
    if not trow:
        sys.exit("GATE: bulletin %s is not on file for vehicle %d. Refused." % (spec["tsb_number"], vid))
    # 5) fetch + hash the actual document the verifier reviewed
    print("fetching %s ..." % spec["source_url"])
    h, sz = fetch_hash(spec["source_url"])
    print("  fetched %d bytes, md5 %s" % (sz, h))
    cur.execute("""INSERT OR REPLACE INTO tsb_pairings
        (vehicle_id,complaint_topic,tsb_number,bulletin_date,component,applies_note,symptom,
         service_action,source_url,source_hash,verified_by,verified_at,superseded,last_checked_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0,?)""",
        (vid, spec["complaint_topic"], spec["tsb_number"], trow[1], trow[2], spec["applies_note"],
         spec["symptom"], spec["service_action"], spec["source_url"], h, spec["verified_by"],
         spec.get("verified_at") or now_iso(), now_iso()))
    con.commit()
    print("PAIRING STORED: vehicle %d | %s -> topic %r | verified_by %s"
          % (vid, spec["tsb_number"], spec["complaint_topic"], spec["verified_by"]))

def cmd_list(cur, con, args):
    rows = cur.execute("""SELECT id,vehicle_id,tsb_number,complaint_topic,verified_by,verified_at,
                          superseded,source_hash FROM tsb_pairings ORDER BY id""").fetchall()
    print("%d pairing(s):" % len(rows))
    for r in rows:
        print("  #%d veh=%d %s -> %s  by=%s @%s  %s  %s"
              % (r[0], r[1], r[2], r[3], r[4], r[5], "SUPERSEDED" if r[6] else "ok", r[7][:12]))

def cmd_recheck(cur, con, args):
    """Refetch every source_url and compare its hash. A mismatch means NHTSA replaced the
    document (supersession / revision) -- flag it so a human re-verifies before it keeps shipping."""
    rows = cur.execute("SELECT id,tsb_number,source_url,source_hash FROM tsb_pairings").fetchall()
    changed = 0
    for pid, tsb, url, old in rows:
        try:
            h, _ = fetch_hash(url)
        except Exception as e:
            print("  #%d %s FETCH-FAILED %s" % (pid, tsb, e)); continue
        ok = (h == old)
        if not ok:
            changed += 1
            cur.execute("UPDATE tsb_pairings SET superseded=1, last_checked_at=? WHERE id=?", (now_iso(), pid))
        else:
            cur.execute("UPDATE tsb_pairings SET last_checked_at=? WHERE id=?", (now_iso(), pid))
        print("  #%d %s -> %s" % (pid, tsb, "OK" if ok else "HASH CHANGED (superseded/rot -> re-verify)"))
    con.commit()
    print("recheck done. %d pairing(s) flagged superseded." % changed)

def cmd_candidates(cur, con, args):
    vid = args.vehicle
    ship, n = topics_for(cur, vid)
    print("vehicle %d ships topics %s (n=%d complaints)" % (vid, sorted(ship), n))
    trunc = cur.execute("SELECT 1 FROM tsb_truncated WHERE vehicle_id=?", (vid,)).fetchone()
    print("truncated at import cap (internal):", "YES" if trunc else "no")
    ADMIN = ("newsletter", "handover", "warranty administration", "courtesy transportation",
             "floor mat", "elsa newsletter", "goodwill", "policy information", "special notice")
    rows = cur.execute("SELECT tsb_number,date,component,title FROM tsb WHERE vehicle_id=? ORDER BY date DESC", (vid,)).fetchall()
    subst = [r for r in rows if not any(k in (r[3] or "").lower() for k in ADMIN)]
    print("bulletins: %d total, ~%d substantive (admin/junk filtered):" % (len(rows), len(subst)))
    for r in subst[:12]:
        print("  %s  %s  [%s]  %s" % (r[0], r[1], (r[2] or "")[:22], (r[3] or "")[:70]))

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    sub.add_parser("init")
    a = sub.add_parser("add"); a.add_argument("--spec", required=True)
    sub.add_parser("list")
    sub.add_parser("recheck")
    cand = sub.add_parser("candidates"); cand.add_argument("--vehicle", type=int, required=True)
    args = ap.parse_args()
    con = sqlite3.connect(DB); cur = con.cursor()
    {"init": cmd_init, "add": cmd_add, "list": cmd_list, "recheck": cmd_recheck,
     "candidates": cmd_candidates}[args.mode](cur, con, args)
    con.close()

if __name__ == "__main__":
    main()
