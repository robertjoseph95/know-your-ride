# WRENCH — Data Enrichment Scripts

Run these in order. Each one is resume-safe (skips already-filled rows).
Put all scripts in the same folder as `wrench_vehicles.db`.

---

## Prerequisites

```bash
pip install requests
```

---

## Run Order

### 01 — NHTSA vPIC Engine/Trim Backfill
```bash
python3 01_nhtsa_vpic_backfill.py
```
- **What:** Fills `engine` and `trim` columns for ~700 vehicles currently showing NULL
- **API:** https://vpic.nhtsa.dot.gov/api/ (free, no key)
- **Time:** ~25 min
- **Output:** Updates `vehicles` table in-place, writes `vpic_backfill.log`

---

### 02 — EPA FuelEconomy.gov MPG + EV Range
```bash
python3 02_epa_mpg_backfill.py
```
- **What:** Fills 41 vehicles missing MPG. Adds `range_miles` and `mpge` columns
  to `fuel_economy` for EVs (Tesla, Lucid, etc.)
- **API:** https://www.fueleconomy.gov/ws/rest/ (free, no key)
- **Time:** ~10 min
- **Output:** Updates `fuel_economy` table, writes `epa_backfill.log`

---

### 03 — NHTSA TSB Enrichment + Complaints
```bash
python3 03_nhtsa_tsb_enrichment.py
```
- **What:**
  - Fills `title`, `component`, `summary`, `date` for 186,032 TSB rows
    (currently only tsb_number is populated)
  - Creates a new `complaints` table with full NHTSA complaint text,
    crash/fire/injury flags
- **API:** https://api.nhtsa.gov/ (free, no key)
- **Time:** 4–6 hours (caches API responses to `tsb_api_cache.json` so it's
  resumable — kill it and restart anytime)
- **Output:** Updates `tsb` table, creates `complaints` table,
  writes `tsb_enrichment.log`, `tsb_api_cache.json`

---

### 04 — Rebuild wrench_demo.html
```bash
python3 04_rebuild_html.py
```
- **What:** Re-exports all DB data into a fresh `wrench_demo.html` with the
  newly enriched engine/trim, MPG/range, TSB titles, and complaints surfaced
  in the UI
- **Time:** ~30 seconds
- **Output:** Overwrites `wrench_demo.html`

---

## What Each Script Adds to the App

| Script | New data in UI |
|--------|---------------|
| 01 vPIC | Engine size/cylinders shown on vehicle cards and detail header |
| 02 EPA  | MPG gaps filled; EV cards show "320 mi range / 120 MPGe" |
| 03 TSBs | New "TSBs" tab in vehicle modal with searchable bulletins |
| 03 Complaints | New "Complaints" tab with NHTSA complaint text + crash/fire flags |
| 04 Rebuild | All of the above live in the HTML |

---

## Additional Sources (Future Batches)

These aren't scripted yet but are the next logical step:

| Source | Data | Notes |
|--------|------|-------|
| RepairPal API | Repair frequency by mileage, labor rates by ZIP | Requires account |
| CarMD | DTC fix rates ("replaced cat 68% of the time") | Paid API |
| RockAuto | Part numbers + prices | Scraping only |
| OEM PDF manuals | Factory maintenance schedules, exact torque tables | Parsing project |
| CPSC | Non-powertrain recalls (electronics, child safety) | Free, same pattern as NHTSA |
| iSeeCars | Depreciation curves | Scraping or paid data feed |

---

## Notes

- All scripts write to the same `wrench_vehicles.db` — keep a backup before running:
  ```bash
  cp wrench_vehicles.db wrench_vehicles_backup.db
  ```
- Scripts use `COALESCE` updates so existing good data is never overwritten
- Rate limits are conservative; you can lower `RATE_LIMIT` slightly if the APIs
  aren't complaining
