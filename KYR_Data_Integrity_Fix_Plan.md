# KYR — Data Integrity Fix — Implementation Plan
### Know Your Ride Technologies LLC · 20 June 2026

**Goal:** stop presenting unverified (AI-generated / scraped / unknown) curated specs as fact. Add provenance to the spec tables, define "verified" as manufacturer/government source only, and gate the 5 curated-spec areas behind the existing `specSoon()` "pending verification" state — **without touching the authoritative vPIC / EPA / NHTSA data.**

---

## Architecture decision

- **Carry a boolean `ver` (1/0) per spec object in the data blob**, computed at build time (`04_rebuild_demo.py`) from each row's `source`. The render functions gate on `ver`.
- **Why a boolean, not the source string:** smaller payload, and — critically — it **removes the raw `ai-haiku-4.5` string from the public `data.<hash>.js` payload entirely** (today it ships 22,730×). The "verified" definition lives in exactly one place (the Python `_ver()` helper).
- **Gate at the render layer**, not by deleting data — the DB keeps the values, so re-verification later just flips `source` and the spec reappears.

---

## Step 1 — Schema migration + backfill (`_migrate_spec_source.py`, new, idempotent, DB backup first)

Add a `source TEXT` column to the four tables that lack one (maintenance already has it):
```sql
ALTER TABLE oil_change   ADD COLUMN source TEXT;
ALTER TABLE parts        ADD COLUMN source TEXT;
ALTER TABLE fluids       ADD COLUMN source TEXT;
ALTER TABLE torque_specs ADD COLUMN source TEXT;
```
**Backfill** each row's `source`:
- **13 Mazda 3 vehicles (ids 38705–38717): `source = 'owner-manual-verified'`.**
- **All other vehicles: their inferred current source** = the vehicle's `maintenance.source` (`ai-haiku-4.5` / `scraped` / `engine_classifier_v1`). Vehicles with **no** maintenance row → `source = 'unknown'`.

(Idempotent: re-running re-applies the same values; `ALTER` guarded by a column-exists check.)

## Step 2 — Define VERIFIED (one place, `04_rebuild_demo.py`)

```python
def _ver(src):
    s = (src or '').strip().lower()
    if not s or 'ai-' in s or 'haiku' in s or s == 'scraped' or 'classifier' in s or s == 'unknown':
        return 0
    if 'owner' in s or 'manual' in s or 'vpic' in s or 'epa' in s or 'nhtsa' in s:
        return 1
    return 0
```
- **Verified = `'owner-manual-verified'`** (the 4 new columns) **or** `"<Mfr> Owner's Manual (…)"** (maintenance) → both match `owner`/`manual`.
- Everything else (`ai-haiku-4.5`, `scraped`, `engine_classifier_v1`, `unknown`, null) → unverified.

## Step 3 — Carry `ver` into the blob (`04_rebuild_demo.py`)

- `oil_change` loader → add `"ver": _ver(r["source"])` to the `oil` object.
- `parts` loader → add `"ver": _ver(r["source"])`.
- `fluids` loader → add `"ver": _ver(r["source"])`.
- `torque_specs` loader → add `"ver": _ver(r["source"])` per torque item.
- `maintenance` loader → **replace** the current `"src": r["source"]` with `"ver": _ver(r["source"])` (stops shipping the raw source string; the per-row gate uses `ver`).

## Step 4 — UI gate (`wrench_demo.html`, the 4 curated renderers)

| Renderer (tab) | Change |
|---|---|
| `renderOil` (Oil) | EV path unchanged. Then: `if(!o||!o.visc) return specSoon();` **add** `if(!o.ver) return specSoon();` |
| `renderParts` (Parts) | At the spec section: **add** `if(p && !p.ver) return specSoon();` (gates the vehicle spark-plug/battery/tire specs). Generic affiliate part-tiers / how-to remain — see Risks. |
| `renderFluids` (Fluids + Torque) | Render the **fluids** section only if `f && f.ver`; render the **torque** section only from torque items where `x.ver`; if neither → `specSoon()`. |
| `renderMaint` (Maintenance) | Filter to verified rows: `var m=(v.maint||[]).filter(function(s){return s.ver;});` → if none, `specSoon()`. **Remove the Source column** (Step 5). |

## Step 5 — Remove the exposed "Ai-Haiku-4.5" Source column (`renderMaint`)

- Header `…<th>Or Every</th><th>Source</th>` → drop `<th>Source</th>` (now 3 columns).
- Row: delete the trailing `…<td …>'+(s.src||'')+'</td>` source cell.
- Parts sub-row `colspan="4"` → `colspan="3"`.
- (The raw source string also no longer ships in the payload — Step 3.)

## Step 6 — SCOPE GUARANTEE (what is **NOT** gated)

The gate touches **only** these 4 renderers / 5 spec areas: `renderOil`, `renderParts`, `renderFluids` (fluids + torque), `renderMaint`. **Untouched and still displayed for every vehicle:**
- **Engine** string + **engine_specs** (vPIC) → render in the **Perf & MPG tab** (`renderPerf`, line 1374) — *not* gated.
- **MPG / fuel economy** (EPA) → Perf tab — not gated.
- **Recalls** (NHTSA) → Warranty & Recalls tab — not gated.
- **Complaints** (NHTSA) → Complaints tab — not gated.
- **Safety ratings** (NHTSA), **reliability** (NHTSA-derived), **warranty** → their tabs — not gated.
- EV specs (`renderEV`), known-issues, owner notes → not gated.

## Step 7 — Build pipeline (after code changes)
1. `python _migrate_spec_source.py` (schema + backfill; DB backup).
2. `python files/04_rebuild_demo.py` (regenerate blob with `ver`; confirm hand edits + JS parse).
3. Preview verification (Step 8) **before any deploy.**
4. `KYR_NEW_VER=2026-06-20-integrity-gate python _deploy_sync_specs.py` → commit → push → verify prod.

## Step 8 — Preview verification checklist (must pass before deploy)
- **2015 Camry (id 12161):** Oil / Parts / Fluids / Maintenance tabs → **"coming soon"**; the fabricated **"ATF Dexron III" power-steering value is GONE**; the **"Ai-Haiku-4.5" Source column is GONE**; **Perf (engine 3.5L V6 + MPG), Safety, Warranty/Recalls, Complaints still display.**
- **2008 Mazda 3 (id 38708):** curated specs (5W-20, 4.5 qt, FL22, lug torque, maintenance) **display normally** (verified).
- **2–3 other AI vehicles** (e.g. 2018 Civic, 2015 F-150, 2016 Silverado): curated → "coming soon"; authoritative tabs intact.
- **1–2 authoritative-only / verified vehicles:** a no-curated vehicle (already "coming soon", confirm no regression) + a Mazda 3 (verified shows).
- **Regression:** existing numeric/dual-value specs on Mazda 3 still render via `valU()`; JS parses (all script blocks); no emoji/console errors.

---

## SCOPE DECISIONS (confirmed) — engine_specs now gated; tiers stay
1. **`engine_specs` hp/torque IS now gated.** Data check: **all 711 engine_specs rows carry hp/torque, and vPIC never provides hp/torque** → every engine_specs row is AI/scraped-derived (none vPIC-only). So `engine_specs` gets a `source` column too (5 tables total), and the **"Engine Specs" hp/torque table in `renderPerf` is gated** by `ver`. **The vPIC engine string (`v.engine`, shown in the modal header / vehicle card — outside every curated renderer) stays visible**, as does **MPG (EPA)**. When the engine table is gated, the Perf tab still shows MPG + a short "engine performance specs pending verification" note.
2. **General affiliate tiers stay visible; only specific fabricated spec values + definitive fitment claims are gated.** `renderParts` (spark-plug type/gap, battery group/CCA, tire size/pressure, and the specific part-number fitment JSON) is gated; the generic OEM/Premium/Value `renderPartTiers` recommendations + how-to videos remain.
3. **Coverage drop (expected):** ~1,668 mostly-popular vehicles will show "coming soon" on the 4 curated tabs until re-verified. This is the intended honest state.
4. **The 1,807 no-curated vehicles** already show "coming soon" — unaffected.
5. **Reversible:** re-verifying a vehicle later = set its 5 tables' `source` to the manufacturer value → `ver` flips to 1 → specs reappear. No code change needed per vehicle.

---
*Plan only — nothing built or changed yet. Awaiting confirmation to proceed.*
