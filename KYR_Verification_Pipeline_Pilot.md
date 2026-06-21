# KYR — Verification-Method Pilot (cross-manufacturer) + Pipeline Findings
### Know Your Ride Technologies LLC · 20 June 2026

**Goal:** confirm the Mazda owner's-manual verification method generalizes to other makers, and learn what an automated pipeline must handle. **Result: method generalizes (Honda verified end-to-end); full automation does NOT — discovery + confirmation + judgment need a human.**

---

## What was done
Picked the top gated nameplates (Camry, Civic, F-150 — all AI-sourced across every model year). Attempted **Toyota Camry** first (flagship example); **could not verify under discipline** (see below), so pivoted to **Honda Civic**. Fully verified the **2012 Honda Civic (id 11768, 9th gen)** from the official **2013 Honda Civic Sedan Owner's Manual** and let the integrity gate auto-flip it from "pending" to visible.

Source: `techinfo.honda.com/rjanisis/pubs/om/r31313/r31313om.pdf` (368 pp, text-extractable, self-identifying "2013 Civic Sedan"). 2012 ≈ 2013 (same 9th gen 2012–2015); exact-year 2012 OM not separately pulled (documented limitation).

### Verified values (page-cited)
| Field | Value | Page |
|---|---|---|
| Oil viscosity | **0W-20** (Genuine Honda / API Premium-grade) | p349/351 |
| Oil capacity w/filter | **3.9 qt (1.8L) / 4.4 qt (2.4L Si)** | p349/351 |
| Coolant | **Honda Type 2 (Long-Life 50/50)** · 5.9 qt / 5.8 qt | p349/351 |
| Brake fluid | **Honda DOT 3** | p349/351 |
| Trans fluid | **ATF DW-1** (auto) / **Honda MTF** (manual) | p349 |
| Tire + psi | **P195/65R15 @ 30 psi** (LX); P205/55R16 @ 32 (EX); P215/45R17 @ 32 (Si) | p349/351 |
| Spark plug | **NGK DILZKR7B11GS** (1.8L) / **NGK ILZKR7B-11S** (2.4L Si), iridium | p348/350 |
| Lug-nut torque | **80 lbf·ft (108 N·m)** | p322 |
| Oil interval | **Flexible — Maintenance Minder (oil-life), ≥ every 12 months** | p259–261 |
| Brake-fluid interval | **Every 3 years** | p261 |
| **NULL (not in OM)** | spark-plug gap (pre-set), plug/coolant/trans intervals (Minder-driven), battery group/CCA, drain-plug torque, 1.5L Hybrid (separate manual) | — |

---

## Pipeline findings (the real deliverable)

### 1. Manual accessibility — ranked
- **Mazda (best):** direct, near-predictable PDF URLs (`mazdausa.com/siteassets/pdf/owners-optimized/<YEAR>/mazda3-4door/...`), text-extractable, self-identifying.
- **Honda (good):** full OM PDFs **directly downloadable** from `techinfo.honda.com` (no login), text-extractable, **self-identifying** ("2013 Civic Sedan" on p1). BUT the consumer portal `owners.honda.com` redirects to a **JS app** (`mygarage.honda.com`), and the techinfo URL codes (`r31313`, `ATBA2121OM`, `AT202222OM`) are **opaque** — not derivable from year/model.
- **Toyota (worst for automation):** full OM behind **opaque codes** (`OM33840U`) on `assets.sia.toyota.com`; the owners portal is JS; and **the manual does NOT self-identify the model inside** — `OM33840U` never says "Camry," so you cannot confirm you fetched the right manual. Only the abbreviated Quick Reference Guide is cleanly addressable. **Verification discipline could not be met → could not verify the Camry.**
- **All three: TEXT-extractable, not image-based** — good once you have the PDF.

### 2. Which fields were findable
- **Findable (owner's manual):** oil viscosity + capacity (per engine), coolant type + capacity, brake fluid, auto + manual trans fluid, tire size + pressure (per trim), spark-plug part numbers, lug-nut torque, oil-change cadence, brake-fluid interval.
- **NOT in the owner's manual (same gaps as Mazda — OM ≠ service manual):** spark-plug **gap**, drain-plug & spark-plug **torque**, fixed plug/coolant/transmission **intervals** (Maintenance-Minder-driven), BCI battery **group size/CCA**.

### 3. Time
One generation ≈ **20–30 min of focused work** (search → confirm right manual → download → locate spec pages → extract → write → rebuild → verify). The bottleneck was **finding and confirming the right manual**, not the extraction.

### 4. What will NOT automate well
- **Manual discovery:** opaque per-make URL codes, not derivable from year/model → needs a maintained per-make code map or a crawl, not a URL template.
- **Manual confirmation (Toyota):** manuals that don't self-identify make "did I get the right one?" un-automatable.
- **Flexible-interval systems** (Honda Maintenance Minder, Mazda oil-life): can't be reduced to a fixed mileage → need a "flexible/oil-life" representation (already supported from Mazda gen 3).
- **Multi-engine / Hybrid vehicles:** one DB row spans engines documented across **multiple manuals** (the Civic's 1.5L Hybrid is a separate OM) → multi-source orchestration.
- **Trim-divergent specs** (tire size/pressure by trim) → dual/multi-value strings.
- **Judgment:** L→qt unit conversion, which engine is "base," what to leave NULL. Needs a human or a careful rules engine.

### 5. Is the URL pattern scriptable? — Partially.
- **Automatable:** PDF download (once code known) + text extraction + candidate-field parsing.
- **Not automatable:** discovering the right manual URL/code per vehicle, confirming it matches, and the per-vehicle judgment.
- **Implication:** the pipeline should be **human-in-the-loop** — a human supplies/confirms the manual; the tool auto-fetches, extracts, and surfaces candidate values with page cites for a human to approve; then auto-writes + rebuilds (the gate auto-flips). **Fully autonomous year/model → verified specs is not reliable.**

---

## Pilot status
- **2012 Civic written + verified locally; gate auto-flipped on preview.** NOT deployed (paused per instruction). DB backed up (`wrench_vehicles.db.bak-civicpilot-*`).
- The method + gate are proven cross-manufacturer. Ready to deploy the Civic and/or scale the human-in-the-loop pipeline on your word.
