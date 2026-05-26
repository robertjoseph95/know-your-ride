"""
WRENCH — Script 01 (rewrite): EPA Engine Backfill
=================================================
Fills `vehicles.engine` for the rows missing it, using the EPA
fueleconomy.gov web service (free, no key, no VIN required).

Why not NHTSA vPIC?  vPIC only returns engine/trim by *decoding a VIN*.
Its make/model/year endpoints return model NAMES only (Make_ID, Make_Name,
Model_ID, Model_Name) — no displacement, cylinders, or trim.  The vehicles
table has no VIN column, so vPIC cannot do this job.  fueleconomy.gov, by
contrast, exposes engine displacement + cylinder count per year/make/model.

Engine string format matches the existing rows:  "2.0L I4", "3.5L V6",
"5.7L V8".  Cylinder *configuration* (inline vs V) is inferred from the
cylinder count (see CONFIG) because no free source distinguishes I6 from V6
without a VIN — so straight-six engines (e.g. Supra/BMW) are labelled V6.
EVs (Teslas, Lucid, …) have no displacement and are labelled "Electric".

Trim is intentionally NOT written: no VIN-free source provides real trim.
(EPA's granular model names — "Corolla XLE", "Camry TRD" — could yield an
approximate trim later; left as a follow-up.)

Safe to re-run: only targets rows where engine IS NULL/''; never overwrites.

Run:  python 01_epa_engine_backfill.py
"""

import sqlite3
import requests
import time
import re
import shutil
import datetime
import sys

DB_PATH   = r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\wrench_vehicles.db"
LOG_FILE  = r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data\epa_engine_backfill.log"
BASE      = "https://www.fueleconomy.gov/ws/rest/vehicle"
RATE      = 0.15            # seconds between API calls (polite)
COMMIT_EVERY = 25

# cylinder count -> configuration label, matching existing engine strings.
CONFIG = {2: "I2", 3: "I3", 4: "I4", 5: "I5", 6: "V6",
          8: "V8", 10: "V10", 12: "V12", 16: "W16"}

session = requests.Session()
session.headers.update({"Accept": "application/json"})

# ── EPA API helpers ──────────────────────────────────────────────────────────

def api(path, **params):
    """GET an EPA endpoint as JSON, with light retry. Returns dict or None."""
    for attempt in range(3):
        try:
            r = session.get(f"{BASE}{path}", params=params, timeout=20)
            r.raise_for_status()
            time.sleep(RATE)
            return r.json()
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None


def items(data):
    """EPA returns menuItem as a dict (1 result) or list (many). Normalize."""
    if not data:
        return []
    mi = data.get("menuItem")
    if mi is None:
        return []
    return [mi] if isinstance(mi, dict) else mi


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# caches keyed to avoid refetching within a run
_make_cache = {}    # year -> {norm(make): canonical_make}
_model_cache = {}   # (make, year) -> [model_text, ...]
_opt_cache = {}     # (year, make, model) -> [option_text, ...]


def resolve_make(make, year):
    """Map a DB make to EPA's canonical spelling (e.g. RAM -> Ram). Falls back to raw."""
    if year not in _make_cache:
        _make_cache[year] = {norm(i["text"]): i["text"] for i in items(api("/menu/make", year=year))}
    return _make_cache[year].get(norm(make), make)


def model_list(make, year):
    key = (make, year)
    if key not in _model_cache:
        _model_cache[key] = [i["text"] for i in items(api("/menu/model", year=year, make=make))]
    return _model_cache[key]


def option_texts(year, make, model):
    key = (year, make, model)
    if key not in _opt_cache:
        _opt_cache[key] = [i["text"] for i in items(api("/menu/options", year=year, make=make, model=model))]
    return _opt_cache[key]


def match_models(db_model, epa_models, make=""):
    """
    EPA model names are granular ('Corolla XLE', '4Runner 4WD', 'Model 3 Long Range').
    Match every EPA model that begins with the DB model as a prefix, then union.
    Prefer word-boundary prefix; fall back to normalized prefix for punctuation
    differences (e.g. DB 'C-HR' vs EPA 'C-HR', 'CX-5' vs 'CX 5').

    Some makes attach the brand to the model ('Mazda3') while EPA strips it
    ('3 4-Door 2WD'), so a make-stripped candidate is added too.
    """
    d  = db_model.lower().strip()
    word = [m for m in epa_models if m.lower().strip() == d or m.lower().strip().startswith(d + " ")]
    if word:
        return word

    cands = {norm(db_model)}
    nm, nd = norm(make), norm(db_model)
    if nm and nd.startswith(nm) and len(nd) > len(nm):
        cands.add(nd[len(nm):])                       # 'mazda3' -> '3'
    cands = {c for c in cands if c}
    return [m for m in epa_models if any(norm(m) == c or norm(m).startswith(c) for c in cands)]


def engine_for(year, make, model):
    """Return (engine_string, status). status in {ok, ev, no_model_match, no_options}."""
    epa_make = resolve_make(make, year)
    models = model_list(epa_make, year)
    if not models and epa_make != make:          # retry with raw make spelling
        epa_make = make
        models = model_list(epa_make, year)
    if not models:
        return None, "no_model_match"

    matched = match_models(model, models, epa_make)
    if not matched:
        return None, "no_model_match"

    pieces = {}            # "2.0L I4" -> displacement float (for ordering)
    saw_option = False
    for m in matched:
        for text in option_texts(year, epa_make, m):
            saw_option = True
            dm = re.search(r"([\d.]+)\s*L\b", text)
            if not dm:
                continue
            displ = float(dm.group(1))
            cm = re.search(r"(\d+)\s*cyl", text)
            cyl = int(cm.group(1)) if cm else None
            cfg = CONFIG.get(cyl, f"{cyl}-cyl" if cyl else "")
            piece = f"{displ:.1f}L" + (f" {cfg}" if cfg else "")
            pieces[piece] = displ

    if pieces:
        ordered = sorted(pieces.items(), key=lambda kv: kv[1])
        return " / ".join(p for p, _ in ordered), "ok"
    if saw_option:
        return "Electric", "ev"          # found the model but no displacement -> EV
    return None, "no_options"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # 1) Back up the DB before any writes.
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{DB_PATH}.{stamp}.bak"
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    log = open(LOG_FILE, "w", encoding="utf-8")

    cur.execute("""
        SELECT id, year, make, model FROM vehicles
        WHERE engine IS NULL OR engine = ''
        ORDER BY make, year, model
    """)
    targets = cur.fetchall()
    total = len(targets)
    print(f"Found {total} vehicles missing engine\n")

    updated = ev = missed = 0
    for i, v in enumerate(targets, 1):
        vid, year, make, model = v["id"], v["year"], v["make"], v["model"]
        label = f"{year} {make} {model}"
        try:
            engine, status = engine_for(year, make, model)
        except Exception as e:
            engine, status = None, f"error:{e}"

        if engine:
            # COALESCE + WHERE guard: never overwrite an existing value.
            cur.execute(
                "UPDATE vehicles SET engine = COALESCE(engine, ?) "
                "WHERE id = ? AND (engine IS NULL OR engine = '')",
                (engine, vid),
            )
            if status == "ev":
                ev += 1
            else:
                updated += 1
            print(f"[{i}/{total}] {label}  ->  {engine}")
            log.write(f"OK   {label}: {engine}\n")
        else:
            missed += 1
            print(f"[{i}/{total}] {label}  ->  (miss: {status})")
            log.write(f"MISS {label}: {status}\n")

        if i % COMMIT_EVERY == 0:
            conn.commit()

    conn.commit()

    # Final state
    cur.execute("SELECT count(*) FROM vehicles WHERE engine IS NULL OR engine=''")
    still_null = cur.fetchone()[0]
    conn.close()
    log.close()

    print("\n--- Done ---------------------------")
    print(f"Engine filled (ICE) : {updated}")
    print(f"Engine filled (EV)  : {ev}")
    print(f"No match            : {missed}")
    print(f"Still NULL after run: {still_null}")
    print(f"Log                 : {LOG_FILE}")


if __name__ == "__main__":
    main()
