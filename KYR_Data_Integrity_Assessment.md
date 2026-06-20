# KYR — Data-Integrity Assessment: Curated Vehicle Specs
### Know Your Ride Technologies LLC · 20 June 2026

> **Read-only assessment. Nothing in the database, app, or UI was changed.** Findings only — no recommendations, per request.

> **Methodology note (important):** Of the six curated-spec tables, **only `maintenance` has a `source` column.** `oil_change`, `parts`, `fluids`, `torque_specs`, and `engine_specs` have **no provenance field at all.** For those five tables, provenance is **inferred** from the vehicle's `maintenance.source` (the same generation pipeline populated all spec tables per-vehicle together). Inferred figures are labeled as such. "Verified" = `source` contains "Owner's Manual" (the Mazda 3 2005–2017 work — the only manufacturer-source-verified data in the DB).

---

## 1. SOURCE BREAKDOWN — by table × source

**Direct (the only table that records source):**

| Table | ai-haiku-4.5 | scraped | manufacturer-verified | classifier | total rows |
|---|---:|---:|---:|---:|---:|
| **maintenance** | **22,730** | 3,411 | **57** | 37 | 26,235 |

**Inferred (no `source` column — attributed via the vehicle's maintenance source):**

| Table | ai (inferred) | scraped | verified | unknown (no maint signal) | total rows |
|---|---:|---:|---:|---:|---:|
| oil_change | 1,566 | 146 | 13 | 59 | 1,784 |
| parts / battery | 1,668 | 179 | 13 | 103 | 1,963 |
| fluids | 1,668 | 179 | 13 | 2 | 1,862 |
| torque_specs | 5,237 | 546 | 13 | 8 | 5,804 |
| engine_specs | 562 | 66 | 0 | 83 | 711 |

**Takeaway:** across every curated table, the dominant source is `ai-haiku-4.5`. Manufacturer-verified data is **13 vehicles' worth in every table** (the Mazda 3 backfill), e.g. 13 of 1,784 oil rows (0.7%).

---

## 2. VEHICLE-LEVEL BREAKDOWN (3,667 total vehicles)

| Category | Vehicles | % of fleet |
|---|---:|---:|
| Have **ANY** `ai-haiku-4.5` curated data | **1,668** | **45.5%** |
| **Fully** AI-generated (100% of their maintenance is `ai-*`) | **1,668** | 45.5% |
| **Partially** AI (mixed `ai` + other source) | **0** | 0% |
| Zero AI — scraped only | 153 (+26 classifier+scraped) | 4.9% |
| Zero AI — **manufacturer-verified** | **13** | 0.35% |
| Zero AI — **no curated maintenance at all** (already honest) | **1,807** | 49.3% |

**Notes:**
- Every AI vehicle is **fully** AI — there are **no mixed-source vehicles.** A vehicle is either entirely AI-generated, entirely scraped, entirely verified, or has no curated data.
- The **13 manufacturer-verified** vehicles are exclusively the Mazda 3 2005–2017 rows.
- The **1,807** vehicles with no curated maintenance already display the honest "coming soon" state — they are not a problem; they are correctly absent.
- So of the ~1,860 vehicles that show curated specs, **~90% (1,668) are AI-generated.**

---

## 3. WHAT THE USER ACTUALLY SEES

**Test vehicle — 2015 Toyota Camry (3.5L V6, id 12161), 100% `ai-haiku-4.5`.** Rendered live in the demo. Exact on-screen values:

**Oil tab** (shown as plain fact, no source label):
- Viscosity: **0W-20** · Oil Type: Full Synthetic · Capacity w/ Filter: **6.1 qts** · Capacity w/o Filter: 5.7 qts · OEM Spec: ILSAC GF-5
- Drain plug → Socket 14mm · Thread M12x1.25 · **Torque: 30 ft-lb · 40.7 Nm** · Gasket: 14mm aluminum crush washer

**Fluids tab:**
- Transmission ATF WS · Trans Capacity 3.7 qts · Brake Fluid DOT 3 · Coolant Super Long Life · Coolant Capacity 7.4 qts · **Power Steering: ATF Dexron III**

**Maintenance tab:**
- A **"Source" column that prints `Ai-Haiku-4.5`** next to every row, e.g. *"Engine oil and filter change (0W-20 Full Synthetic, 6.1 qt capacity) … 7,500 mi — Ai-Haiku-4.5"*

**Is there any indication to the user that a spec is unverified? — NO.**
- The oil / parts / fluids / torque tabs carry **no source, "verified", "unverified", or "pending" indicator of any kind.** The values render identically to the manufacturer-verified Mazda 3 specs (same layout, same authority).
- The **only** source signal anywhere is the maintenance tab's "Source" column showing the raw string `Ai-Haiku-4.5`. This is **not** a meaningful "unverified" warning — it exposes an internal AI model name that a user cannot interpret, and it reads like a legitimate data-source label, lending false authority.

**Two of the displayed values on this single popular vehicle are demonstrably wrong:**
- **Power Steering "ATF Dexron III"** — the 2012–2017 Camry (XV50) uses **electric power steering** and has **no power-steering fluid.** This is a **fabricated specification** presented as fact.
- **Oil capacity "6.1 qts"** — appears to be the metric figure (6.1 L) mislabeled as quarts; the 2GR-FE 3.5 V6 holds ≈ **6.4 US qt** with filter. (Same liter-stored-as-quarts pattern noted in the prior inconsistencies log.)

---

## 4. POPULARITY / RISK PRIORITIZATION

The AI-generated data is concentrated on **exactly the highest-traffic vehicles** — every mainstream nameplate, across its full model-year span:

| Nameplate | AI model-years | of which 2015+ |
|---|---:|---:|
| Ford F-150 | 24 (2000–2025) | 11 |
| Toyota Camry | 23 (2000–2025) | 11 |
| Honda Accord | 22 | 10 |
| Honda Civic | 22 | 10 |
| Nissan Altima | 21 | 11 |
| Toyota Corolla | 20 | 8 |
| Toyota RAV4 | 20 | 10 |
| Chevrolet Silverado 1500 | 19 | 9 |
| Honda CR-V | 19 | 9 |
| Jeep Grand Cherokee | 16 | 8 |
| Toyota Tacoma / Highlander, Ford Escape / Explorer, Nissan Rogue, Jeep Wrangler, Chevy Equinox, Honda Pilot, Tesla Model 3 … | (all AI) | … |

- **Top-20 nameplates: 314 AI vehicle-years, 158 of them 2015+.**
- **923 of the 1,668 AI vehicles (55%) are model-year 2015 or newer** — i.e. cars currently on the road and most likely to be looked up and fact-checked by an owner.
- No per-vehicle traffic data exists in the DB (`api_usage` is empty), so "popularity" here is proxied by nameplate volume and recency.

---

## 5. CLAIM-CRITICAL FIELDS (cited as "verified" in investor / NSF docs)

The investor/NSF materials specifically cite **oil viscosity, drain-plug torque, and battery fitment** as verified. Actual provenance across all vehicles:

| Field | Total values | AI-generated | scraped | unknown | **manufacturer-verified** |
|---|---:|---:|---:|---:|---:|
| **Oil viscosity** | 1,784 | 1,566 (**87.8%**) | 146 (8.2%) | 59 (3.3%) | **13 (0.7%)** |
| **Drain-plug torque** | 1,709 | 1,561 (**91.3%**) | 146 (8.5%) | 2 (0.1%) | **0 (0.0%)** |
| **Battery fitment** (group/CCA) | 1,421 | 1,169 (**82.3%**) | 169 (11.9%) | 83 (5.8%) | **0 (0.0%)** |

**Finding:** of the three fields the public-facing docs describe as "verified":
- **Oil viscosity is 0.7% verified** (13 of 1,784) — the rest is AI-generated or scraped.
- **Drain-plug torque is 0% verified** (the Mazda 3 work recorded lug-nut torque, not drain-plug torque, and nothing else is manual-sourced).
- **Battery fitment is 0% verified** (the Mazda 3 work left battery group/CCA NULL because the owner's manual doesn't publish it).

In other words, for the three specific specifications named as "verified," **essentially none of the live data is manufacturer-source-verified today** (≤0.7%); the overwhelming majority is AI-generated.

---

## Summary of the integrity gap (facts only)

- **45.5% of all vehicles (1,668 / 3,667)** carry AI-generated curated specs; ~90% of vehicles that *show* specs are AI-generated.
- **5 of 6 curated tables have no provenance column**, so most AI data is not even labeled as such in the schema.
- **The UI presents AI-generated specs as verified fact** with no honest unverified indicator; the only source signal is an opaque `Ai-Haiku-4.5` tag on the maintenance tab.
- At least one displayed value on a single popular vehicle (2015 Camry power-steering fluid) is a **demonstrable fabrication**.
- The three fields named "verified" in investor/NSF docs are **≤0.7% verified** in the live data.

*Assessment prepared read-only. No changes made. Companion context: `KYR_Data_Inconsistencies_To_Fix.md` (prior audit + UI render detail), `KYR_Mazda3_Spec_Verification_Log.md` (the verified-data template).*
