# KYR — Data Inconsistencies To Fix (dedicated pass, not inline)
### Know Your Ride Technologies LLC

Issues found during other work that should be corrected in a **separate, dedicated pass** — do NOT fix inline during unrelated feature work.

---

## 1. Oil-capacity unit mislabel on existing curated rows (liters stored, "qts" displayed)

**Found:** 20 June 2026, during the Mazda 3 2005–2017 curated-spec backfill.

**Problem:** The Oil tab (`renderOil` in `wrench_demo.html`) renders `capacity_with_filter` / `capacity_without_filter` with a literal **" qts"** suffix, but at least the **2018 Mazda 3 anchor (vehicle_id 12545)** stores the **liter** figure:
- DB: `capacity_with_filter = 4.2`, `capacity_without_filter = 3.8`
- Reality: 2018 Mazda 3 2.5 SkyActiv-G = **4.2 L = 4.5 US qt** with filter
- Result: the UI shows "4.2 qts" — wrong by the L→qt factor (~0.95×). Should display "4.5 qts".

**Convention going forward (set 20 Jun 2026):** store every spec value in **the unit the UI label displays**. The Oil/Fluids tabs label capacities "qts" → store **US quarts**. The Mazda 3 2005–2017 backfill follows this (quarts).

**Scope of the fix (TBD pass):** audit **all** `oil_change.capacity_*` and `fluids.*_capacity` rows across the 3,667-vehicle DB for liter-vs-quart mislabels (the AI-generated `source='ai-haiku-*'` rows are the likely population). Convert liters→US quarts where stored as liters, or relabel the UI — decide one canonical approach for the whole table, then apply once.

**Do NOT fix inline** during the Mazda work — it needs a DB-wide audit so we don't create a mixed-unit table.

---

## 2. ⚠️ SYSTEMIC: ~45% of curated specs are AI-generated, not manual-verified

**Found:** 20 June 2026. **This is a fleet-wide credibility issue, not a single row.**

Quantified (`maintenance.source`):
- **`ai-haiku-4.5`: 22,730 rows across 1,668 of 3,667 vehicles (~45%)** — AI-generated, never verified against a factory manual.
- `scraped`: 3,411 rows — provenance unclear, also unverified.
- `engine_classifier_v1`: 37 rows.
- **`Mazda Owner's Manual (2008, Schedule 1)`: 25 rows** — the only manual-verified curated data in the DB (the Mazda 3 2005–2009 work just done).

The same AI source populated `oil_change`, `parts`, `fluids`, and `torque_specs` on those vehicles. Some entries are internally inconsistent (e.g. the 2018 Mazda 3 `maintenance` says "air filter every 15,000 mi" while its `air_filters_json` says 30,000 mi). Any of these could be a **fabricated specification** — the exact thing KYR's positioning says it never publishes.

**Recommendation — investigate as a systemic issue:**
1. Treat **all `source LIKE 'ai-%'` and `source = 'scraped'` curated rows as UNVERIFIED**.
2. Decide a remediation policy: (a) show the `specSoon()` "coming soon" state for AI-sourced fields until human-verified, or (b) prioritize a verification pass by vehicle popularity.
3. The Mazda 3 method is the template: download the official Mazda PDF → cite page numbers → write only verified values, `source = "<manufacturer> Owner's Manual (<year>)"`.
4. This likely extends beyond Mazda to most makes in the DB — scope a full audit of curated-spec provenance.
