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

---

## 3. AUDIT — AI-generated curated specs (full breakdown + UI assessment + recommendation)

*Read-only assessment, 20 June 2026. No code/data changed. For Robert's decision.*

### 3a. Provenance breakdown (by `maintenance.source`, the only spec table with a source column)

| Source | Maintenance rows | Vehicles | Meaning |
|---|---:|---:|---|
| **`ai-haiku-4.5`** | **22,730** | **1,668** | AI-generated, never verified against a manual |
| `scraped` | 3,411 | 179 | scraped from unknown web sources, unverified |
| `engine_classifier_v1` | 37 | 26 | classifier output |
| **`<Manufacturer> Owner's Manual`** | **57** | **13** | manual-verified (the Mazda 3 2005–2017 work only) |

Of the **1,860 vehicles that have any curated maintenance, ~90% (1,668) are AI-generated.** The other **1,807 of 3,667 vehicles have no curated maintenance at all** (they already show the `specSoon()` "coming soon" state — those are honest).

### 3b. Spec tables affected — and a critical gap

**Only `maintenance` has a `source` column.** `oil_change`, `parts`, `fluids`, and `torque_specs` have **no provenance field at all** — so there is currently *no way to tell* which oil/parts/fluids/torque rows are AI-generated except by joining to `maintenance.source` as a proxy. Inferred AI-attributed row counts (vehicles whose maintenance is `ai-*`):

| Table | AI-attributed rows | Has `source` col? |
|---|---:|:--:|
| oil_change | 1,566 | ❌ |
| parts | 1,668 | ❌ |
| fluids | 1,668 | ❌ |
| maintenance | 22,730 | ✅ |
| torque_specs | 5,237 | ❌ |
| **Total** | **≈ 32,869 rows** | |

**First remediation step regardless of approach:** add a `source` column to the other four tables so provenance is trackable.

### 3c. Which vehicles — and are they popular?

- **Year range:** 1999–2025. Heaviest buckets: 2020–2024 (676 vehicles), 2000–2004 (431), 2005–2009 (278), 2015–2019 (135).
- **Top makes affected (all mainstream):** Toyota 165, Honda 115, Chevrolet 106, Ford 104, Nissan 98, BMW 80, Subaru 70, VW 65, Hyundai 64, Kia 54.
- **60% (1,009 of 1,668) are mainstream high-volume makes** (Toyota/Honda/Ford/Chevy/Nissan/Hyundai/Kia/Subaru/Jeep/Ram/GMC/Mazda/VW/Dodge).
- Confirmed popular models with AI specs include the **Chevrolet Silverado 1500 across nearly every model year 2000–2024** — i.e. exactly the cars users are most likely to look up.
- **No traffic/popularity data exists in the DB** (`api_usage` table is empty; no per-vehicle view counts). Prioritization must use make/model volume as a proxy, or add real analytics first.

### 3d. ⚠️ UI ASSESSMENT — does the user see fabricated data presented as fact? **YES.** (verified empirically — corrects an earlier note)

**Demonstrated on a live render of the 2015 Toyota Camry (id 12161), whose specs are entirely `ai-haiku-4.5`:**

- **Oil / Parts / Fluids / Torque tabs: NO source indication at all.** These four tables have no `source` column, so the UI shows the values as plain authoritative fact:
  - Oil tab → "VISCOSITY 0W-20 · OIL TYPE Full Synthetic · **CAPACITY W/ FILTER 6.1 qts**" (the 6.1 is the liter figure mislabeled as quarts — real ≈ 6.4 US qt; the §1 unit bug, AI-sourced)
  - Fluids tab → "**POWER STEERING ATF Dexron III**" — **fabricated: the 2012–2017 Camry (XV50) has *electric* power steering and uses no PS fluid.** Concrete proof the AI invented a spec.
- **Maintenance tab: WORSE than no indicator — it prints the raw model name.** The schedule has a **"Source" column that literally displays `Ai-Haiku-4.5`** next to every row. This (a) exposes an internal AI model name to end users, and (b) is *not* understood by anyone as "unverified" — a layperson reads it as just another data-source label, lending it false authority.
- The AI specs otherwise render **identically** to the owner's-manual-verified Mazda 3 specs — same layout, same authority.
- **Net:** a user on a 2015 Camry sees AI-generated (and in at least one case demonstrably **fabricated**) values presented as fact, with no honest "unverified" signal — only an opaque `Ai-Haiku-4.5` tag on the maintenance tab. This directly contradicts KYR's "never a fabricated specification" positioning.

> **Correction to the prior assessment:** an earlier note here said "the render functions do not reference `source` at all." That is wrong for `renderMaint` — the maintenance table *does* render a Source column showing `Ai-Haiku-4.5`. The other four tabs show no source. Corrected after a live render.

### 3e. Recommendation — fastest integrity fix: apply `specSoon()` to all unverified specs

**Revised from the earlier "badge over hiding" lean.** That earlier position prioritized perceived coverage. Two facts change it: (1) KYR's positioning is *absolute* — "never a fabricated specification"; (2) we now have **proof of an actual fabrication** (the 2015 Camry's "ATF Dexron III" power-steering fluid on an electric-power-steering car). When you can demonstrate even one fabricated value, showing the rest with a "caveat badge" is no longer defensible — a user can still act on a wrong torque or capacity. **Better to show less than to show wrong.** So:

**Step 1 — Fastest fix (ship first, ~hours, no re-verification needed): hide unverified specs behind the honest `specSoon()` state.**
- Add a `source` column to `oil_change`, `parts`, `fluids`, `torque_specs` (currently only `maintenance` has one).
- Define **verified = `source LIKE '%Owner''s Manual%'`** (or other explicitly authoritative source). Everything else — `ai-*`, `scraped`, `engine_classifier_v1`, `NULL` — is **unverified**.
- In the render path, when a spec is unverified, show the existing **`specSoon()` "Spec data coming soon — we verify every value against the factory service manual before publishing"** instead of the value. This is the same honest state already shipping for vehicles with no data.
- **Immediately remove the maintenance "Source: Ai-Haiku-4.5" column** (it exposes an internal AI model name to users and reads as false authority). At minimum, stop printing raw `ai-*`/`scraped` source strings to end users.
- Trade-off (state it plainly): coverage on ~1,668 mostly-popular vehicles drops to "coming soon" across oil/parts/fluids/maintenance until re-verified. That is the honest cost of the brand promise, and it is reversible model-by-model.

**Step 2 — Re-verify in priority order** using the Mazda 3 owner's-manual method as the template (download official manual → cite pages → write verified values + `source`). Work highest-volume models first: Camry, Civic, Corolla, F-150, Silverado, Accord, RAV4, CR-V, Altima, Equinox… Each verified vehicle flips from "coming soon" back to real, cited specs.

**Step 3 — Decide volume vs. cost.** ~1,668 vehicles is large for one-at-a-time manual verification:
- (i) Manually verify the top ~100–200 highest-volume vehicles in-house; leave the long tail on `specSoon()`.
- (ii) Route the tail to the contracted researcher (Jazerie, $1.25/verified row) using the same method + verification log.
- (iii) Stand up real per-vehicle analytics (the DB has none today) so prioritization follows actual demand, not guessed popularity.

**Bottom line:** the problem isn't only that AI specs exist — it's that the **UI presents them (and at least one provably fabricated value) as fact.** The fastest, most brand-consistent fix is to **hide all unverified specs behind `specSoon()` now**, then re-verify popular models back into visibility behind that honest signal. This ships without re-verifying a single spec and makes the "never a fabricated specification" claim true again immediately.
