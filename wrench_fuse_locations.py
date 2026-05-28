"""
wrench_fuse_locations.py
========================
Backfill fuse panel locations for every vehicle in wrench_vehicles.db using the
Claude API. Stores results in the `fuse_locations` table so files/04_rebuild_demo.py
can bake them into the embedded data blob.

Usage:
    python wrench_fuse_locations.py             # process up to 50 vehicles
    python wrench_fuse_locations.py --limit 20  # cap differently
    python wrench_fuse_locations.py --dry-run   # show the prompts without calling the API
    python wrench_fuse_locations.py --refresh   # also re-process already-stored rows

Behavior:
- Caps API calls per run to control spend (default 50).
- Skips vehicles that already have a row (unless --refresh is set).
- Reads the Claude API key from wrench_config.json (anthropic_api_key) the same way
  wrench_serve.py does.
- Prompts Claude for FACTUAL location text only — no diagrams, no copyrighted manual
  excerpts, no part numbers. Output is normalized to JSON: {"primary": "...", "secondary": "..."}.
- Uses NHTSA TSB and complaints context (rows mentioning fuse/relay) when available
  to ground the answer for vehicles where the model has weak generic knowledge.
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "wrench_vehicles.db")
CONFIG_PATH = os.path.join(ROOT, "wrench_config.json")
LOG_PATH = os.path.join(ROOT, "wrench_fuse_locations.log")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"
DEFAULT_LIMIT = 50

# Per-call pacing — keeps us well under default per-org rate limits even on long runs.
SLEEP_BETWEEN = 0.6

SYSTEM_PROMPT = (
    "You are an automotive reference assistant. Given a vehicle (year, make, model), "
    "describe ONLY the physical location of the fuse boxes in plain text. Rules:\n"
    "- Output a single JSON object with exactly two keys: \"primary\" and \"secondary\".\n"
    "- \"primary\" is the interior / cabin fuse box (or main fuse panel if there is only one).\n"
    "- \"secondary\" is the engine-bay / underhood fuse-and-relay box, OR the trunk/cargo "
    "fuse box if the model uses one. Use null if a second box is not present on this model.\n"
    "- Each value is a SHORT factual location description (one sentence, no diagrams, no "
    "part numbers, no copyrighted manual text). Example: \"Driver-side lower dashboard, "
    "behind a removable plastic cover near the hood release.\"\n"
    "- If you are not confident this exact vehicle has a documented fuse layout, return "
    "{\"primary\": null, \"secondary\": null}. Do NOT guess.\n"
    "- Do NOT include any other keys, prose, code fences, or markdown — JSON only."
)


def load_api_key():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        key = cfg.get("anthropic_api_key", "")
        if not key:
            sys.exit(f"ERROR: anthropic_api_key missing from {CONFIG_PATH}")
        return key
    except FileNotFoundError:
        sys.exit(f"ERROR: {CONFIG_PATH} not found")
    except Exception as e:
        sys.exit(f"ERROR: could not read {CONFIG_PATH}: {e}")


def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fuse_locations (
            vehicle_id INTEGER PRIMARY KEY,
            primary_location TEXT,
            secondary_location TEXT,
            source TEXT,
            generated_at TEXT,
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
        )
    """)
    conn.commit()


def gather_context(cur, vehicle_id):
    """Pull short fuse/relay-mentioning snippets from TSB + complaints to ground the prompt."""
    snippets = []

    cur.execute(
        "SELECT tsb_number, title, summary FROM tsb WHERE vehicle_id=? "
        "AND (title LIKE '%fuse%' OR summary LIKE '%fuse%' OR title LIKE '%relay%' "
        "OR summary LIKE '%relay%' OR component LIKE '%fuse%' OR component LIKE '%junction box%') "
        "LIMIT 3", (vehicle_id,))
    for r in cur.fetchall():
        title = (r[1] or "").strip()
        summary = (r[2] or "").strip()
        if title or summary:
            snippets.append(f"TSB {r[0] or ''}: {title} {summary[:200]}".strip())

    cur.execute(
        "SELECT component, summary FROM complaints WHERE vehicle_id=? "
        "AND (summary LIKE '%fuse%' OR summary LIKE '%relay%' OR summary LIKE '%fuse box%' "
        "OR summary LIKE '%junction box%' OR summary LIKE '%fuse panel%') "
        "LIMIT 3", (vehicle_id,))
    for r in cur.fetchall():
        comp = (r[0] or "").strip()
        summary = (r[1] or "").strip()
        if summary:
            snippets.append(f"Complaint ({comp}): {summary[:220]}")

    return snippets


def call_claude(api_key, year, make, model, snippets, dry_run=False):
    user = f"Vehicle: {year} {make} {model}\n"
    if snippets:
        user += "\nNHTSA context (may mention fuses/relays for this exact vehicle):\n"
        for s in snippets:
            user += f"- {s}\n"
    user += "\nReturn JSON only."

    if dry_run:
        return {"primary": None, "secondary": None}, user

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 280,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_URL, data=body, method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        })
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text").strip()

    parsed = parse_json(text)
    return parsed, user


def parse_json(text):
    """Extract {primary, secondary} robustly — Claude usually returns clean JSON but trim
    common wrappers if it slips up."""
    if not text:
        return {"primary": None, "secondary": None}
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].strip()
    try:
        obj = json.loads(t)
    except json.JSONDecodeError:
        start, end = t.find("{"), t.rfind("}")
        if start == -1 or end == -1 or end < start:
            return {"primary": None, "secondary": None}
        try:
            obj = json.loads(t[start:end + 1])
        except json.JSONDecodeError:
            return {"primary": None, "secondary": None}
    if not isinstance(obj, dict):
        return {"primary": None, "secondary": None}
    return {
        "primary": (obj.get("primary") or None) or None,
        "secondary": (obj.get("secondary") or None) or None,
    }


def log_line(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description="Backfill fuse panel locations via Claude.")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                    help=f"Max Claude API calls this run (default {DEFAULT_LIMIT}).")
    ap.add_argument("--refresh", action="store_true",
                    help="Re-process vehicles that already have a row.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the prompts but make no API calls.")
    args = ap.parse_args()

    if args.limit <= 0:
        sys.exit("ERROR: --limit must be positive")

    api_key = load_api_key() if not args.dry_run else ""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_table(conn)
    cur = conn.cursor()

    # Pick which vehicles we still need (positive ids only — negatives are partial pre-2003 stubs).
    if args.refresh:
        cur.execute(
            "SELECT v.id, v.year, v.make, v.model FROM vehicles v "
            "WHERE v.id > 0 ORDER BY v.year DESC, v.make, v.model")
    else:
        cur.execute(
            "SELECT v.id, v.year, v.make, v.model FROM vehicles v "
            "LEFT JOIN fuse_locations f ON f.vehicle_id = v.id "
            "WHERE v.id > 0 AND f.vehicle_id IS NULL "
            "ORDER BY v.year DESC, v.make, v.model")
    pending = cur.fetchall()

    if not pending:
        log_line("All vehicles already have fuse_locations rows. Use --refresh to re-run.")
        return

    log_line(f"Pending: {len(pending)} vehicle(s). Cap this run: {args.limit}.")
    if args.dry_run:
        log_line("DRY RUN -- no API calls will be made.")

    processed = 0
    saved = 0
    skipped_empty = 0
    errors = 0

    for row in pending:
        if processed >= args.limit:
            break
        vid, year, make, model = row["id"], row["year"], row["make"], row["model"]
        try:
            snippets = gather_context(cur, vid)
            parsed, prompt = call_claude(api_key, year, make, model, snippets,
                                         dry_run=args.dry_run)
            processed += 1

            if args.dry_run:
                log_line(f"[dry] {vid} {year} {make} {model}  ctx={len(snippets)} snippet(s)")
                continue

            primary = parsed.get("primary")
            secondary = parsed.get("secondary")
            if not primary and not secondary:
                skipped_empty += 1
                log_line(f"[skip] {vid} {year} {make} {model}  no confident answer")
            else:
                conn.execute(
                    "INSERT OR REPLACE INTO fuse_locations "
                    "(vehicle_id, primary_location, secondary_location, source, generated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (vid, primary, secondary, MODEL, time.strftime("%Y-%m-%dT%H:%M:%S")))
                conn.commit()
                saved += 1
                log_line(f"[ok]   {vid} {year} {make} {model}")

            time.sleep(SLEEP_BETWEEN)
        except urllib.error.HTTPError as e:
            errors += 1
            log_line(f"[err]  {vid} {year} {make} {model}  HTTP {e.code} {e.reason}")
            if e.code in (401, 403):
                log_line("Auth error from Anthropic API — aborting run.")
                break
            time.sleep(2.0)
        except Exception as e:
            errors += 1
            log_line(f"[err]  {vid} {year} {make} {model}  {type(e).__name__}: {e}")

    log_line(
        f"Done. calls={processed} saved={saved} empty={skipped_empty} "
        f"errors={errors} remaining={max(0, len(pending) - processed)}"
    )
    conn.close()


if __name__ == "__main__":
    main()
