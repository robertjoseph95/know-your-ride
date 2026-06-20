# KYR — Mazda 3 Curated Spec Verification Log
### Know Your Ride Technologies LLC · June 2026

> **Discipline:** every value below was read from an **official Mazda owner's manual PDF** (primary authoritative source). Nothing is from training data, blogs, parts-seller tools, or forums. Fields not present in the owner's manual are marked **UNVERIFIED → left NULL** (the `specSoon()` "coming soon" state stays).

> **UNIT CONVENTION (set 20 Jun 2026, applies to Gen 1/2/3 and all future entries):** store every value in **the unit the UI label displays**. The Oil/Fluids tabs label capacities **" qts"**, so capacities are stored in **US quarts** (e.g. 4.3 L with filter → store **4.5**). The pre-existing 2018 anchor stores liters-as-quarts (a mislabel) — logged in `KYR_Data_Inconsistencies_To_Fix.md` for a separate dedicated pass, **not** matched here.

---

## GENERATION 1 (BK) — 2005–2009 · engines 2.0L & 2.3L MZR (non-turbocharged) · ids 38705–38709 — ✅ WRITTEN TO DB (20 Jun 2026, in US quarts)

**Primary sources (official Mazda, mazdausa.com):**
- **2008 Mazda3 5-Door Owner's Manual** (Form 8Y64-EA-08A) — https://www.mazdausa.com/siteassets/pdf/owners-optimized/2008/mazda3-5door/2008-mazda3-owners-manual-built-after-jan-1-2008.pdf
- **2006 Mazda3 4-Door Owner's Manual** (cross-check) — https://www.mazdausa.com/siteassets/pdf/owners-optimized/2006/mazda3-4door/2006-mazda3-owners-manual.pdf

Both manuals agree on every key spec → Gen 1 BK is internally consistent (2.0L and 2.3L share these values; they are grouped as "Without turbocharger" in the spec table). 2005/2007/2009 are the same generation + engines, bracketed by the directly-verified 2006 and 2008 manuals.

| # | Field | Verified value | Source (page) | Status |
|---|---|---|---|---|
| 1 | **Oil viscosity** | **SAE 5W-20** (US/Canada). 5W-30 only as a substitute *where 5W-20 is unavailable* (non-US), or for the turbo Mazdaspeed3 — **not** the base car. | 2008 p304 · 2006 p266 | ✅ VERIFIED |
| 2 | **Oil capacity — with filter** | **4.3 L (4.5 US qt)** — both 2.0 & 2.3 | 2008 p401 · 2006 p268 | ✅ VERIFIED |
| 2b | Oil capacity — without filter | 3.9 L (4.1 US qt) | 2008 p401 · 2006 p268 | ✅ VERIFIED |
| 3 | **Spark plug** | **Iridium**, Mazda OE `LFG1 18 110` / `L3Y2 18 110`; **gap 1.25–1.35 mm (0.050–0.053 in)** | 2008 p400 · 2006 p362 | ✅ VERIFIED |
| 4 | **Battery** | Manual gives **Ah rating only** (40/52/55 Ah), **no BCI group size, no CCA** | 2008 p400 | ⚠️ NULL (group size/CCA not in manual) |
| 5 | **Tire (base) + pressure** | **P195/65R15 89H @ 230 kPa (33–34 psi)** F/R. Other trims: P205/55R16 @ 220 kPa (32 psi), P205/50R17 @ 220 kPa, 215/45R18 (2008) | 2008 p404 · 2006 p365 | ✅ VERIFIED |
| 6 | **Coolant type + capacity** | **Mazda FL22** (ethylene-glycol; use if "FL22" on cap) · **7.5 L (7.9 US qt)** | 2008 p291/p308 (type), p401 (cap) | ✅ VERIFIED |
| 7 | **Transmission fluid (auto)** | **Mazda ATF M-V** · capacity 4-spd 7.2 L / 5-spd 8.14 L | 2008 p400/p401 | ✅ VERIFIED |
| 7b | **Transmission fluid (manual)** | **API GL-4/GL-5 SAE 75W-90** · capacity 2.87 L | 2008 p400/p401 | ✅ VERIFIED |
| — | Power steering fluid | ATF M-III or equiv (Dexron II) | 2008 p400 | ✅ VERIFIED |
| 8 | **Brake fluid** | **DOT-3** (SAE J1703 / FMVSS116) | 2008 p400 | ✅ VERIFIED |
| 9 | **Maintenance intervals** (Schedule 1, normal) | **Oil + filter: 7,500 mi / 12 mo** · **Tire rotation: 7,500 mi** · **Spark plugs: 75,000 mi** · **Cabin air filter: 25,000 mi / 2 yr** · **Coolant (FL22): first 120,000 mi/10 yr, then 60,000 mi/5 yr** | 2008 p290–291 | ✅ VERIFIED |
| 10a | **Lug-nut torque** | **89–117 N·m (66–86 ft·lbf)** | 2008 p274 | ✅ VERIFIED |
| 10b | Oil drain-plug torque | Not in owner's manual (service-manual data) | — | ⚠️ NULL |
| 10c | Spark-plug torque | Not in owner's manual (service-manual data) | — | ⚠️ NULL |

### Gen 1 — what writes vs stays "coming soon"
- **WRITES (verified):** oil viscosity, oil capacity (w/ & w/o filter), spark plug type + gap, coolant type + capacity, auto + manual trans fluid + capacities, power-steering fluid, brake fluid, tire size + pressure, oil/rotation/plug/cabin-filter/coolant intervals, lug-nut torque.
- **STAYS NULL ("coming soon"):** battery group size + CCA (manual lists Ah only), oil drain-plug torque, spark-plug torque (service-manual-only data — not in any owner's-manual primary source).

---

## ⚠️ Two items for Robert's decision before any DB write

1. **The "already established 5W-30" was WRONG.** The official manual specifies **SAE 5W-20** for the 2.0/2.3 non-turbo (5W-30 is the turbo / no-5W-20-available case). The discipline caught a fabricated assumption — confirming the process is working. Gen 1 will be written as **5W-20**.

2. **Oil-capacity unit convention.** The demo's Oil tab renders the capacity value with a literal **" qts"** suffix. The existing **2018 anchor stores `4.2`** — which is the **liter** figure (2.5 SkyActiv = 4.2 L / 4.5 US qt), so it currently displays "4.2 qts" (a mislabel). For Gen 1 I recommend storing **US quarts (4.5)** so the "qts" label is correct, and separately flagging the 2018 anchor as a pre-existing unit inconsistency to fix. Need your call: **(a)** store US quarts (display-correct), or **(b)** match the 2018 anchor's liter convention. *(Same question will apply to Gen 2/3.)*

---

## GENERATION 2 (BL) — 2010–2013 · ids 38710–38713 — ✅ WRITTEN TO DB (20 Jun 2026; dual-value strings, per-year viscosity; renders via `valU()` helper)

**Primary sources (official Mazda):**
- **2010 Mazda3 4-Door Owner's Manual** — https://www.mazdausa.com/siteassets/pdf/owners-optimized/2010/mazda3-4door/2010-mazda-3-owners-manual.pdf
- **2013 Mazda3 4-Door Owner's Manual** — https://www.mazdausa.com/siteassets/pdf/owners-optimized/2013/mazda3-4door/2013-mazda3-owners-manual.pdf

**Gen 2 is NOT one spec block.** It splits by sub-period and by engine:

| Field | **2010–2011** (MZR 2.0 + MZR 2.5) | **2012–2013** (SkyActiv-G 2.0 + MZR 2.5) | Source |
|---|---|---|---|
| **Oil viscosity** | **5W-20** (both engines) | **0W-20** (all non-turbo: SkyActiv 2.0, MZR 2.0, MZR 2.5) | 2010 p390 · 2013 p485 |
| **Oil capacity w/filter** | 2.0 = **4.5 qt** · 2.5 = **5.3 qt** | SkyActiv 2.0 = **4.4 qt** · MZR 2.5 = **5.3 qt** | 2010 p489 · 2013 p590 |
| **Spark plug** | Iridium `LFG1 18 110`, gap **0.049–0.053″** (both MZR) | MZR 2.5 same; **SkyActiv 2.0 plug = PENDING** | 2010 p488 |
| **Coolant** | **FL22**, 7.5 L (**7.9 qt**) | **FL22**, 7.5 L (**7.9 qt**) | 2010 p376 · 2013 p469 |
| **Brake fluid** | **DOT-3** | **DOT-3** | both |
| **Auto trans fluid** | **ATF M-V** (5-spd) | SkyActiv **ATF FZ** (6-spd) / MZR 2.5 ATF M-V — *confirm* | capacities p489/590 |
| **Tire (base) + psi** | **P205/55R16 @ 240 kPa (35 psi)** | SkyActiv **P205/55R16 @ 250 kPa (36 psi)** | 2010 p493 · 2013 p596 |
| **Lug-nut torque** | **88–118 N·m (65–87 ft·lbf)** | same | 2010 / 2013 |
| **Oil change / rotation** | **7,500 mi / 12 mo** · rotation **7,500 mi** | same | 2010 p376 · 2013 p469 |
| **Spark plug interval** | **75,000 mi** | **75,000 mi** | both |
| **Coolant interval (FL22)** | first **120k mi/10 yr**, then **60k mi/5 yr** | same | both |

**Left NULL (not in owner's manual):** battery group size/CCA (Ah only), oil drain-plug & spark-plug torque, filter part numbers.

### ⚠️ Modeling decision needed before writing Gen 2
Each DB row is **one year with `engine = "2.0L I4 / 2.5L I4"`**, but `oil_change`/`parts`/`fluids` hold **one value per field**. Within a row the engines **diverge**: oil capacity (4.4/4.5 vs 5.3 qt), and in 2012–13 the plug, trans fluid, and tire pressure differ by engine. Viscosity is uniform *within each sub-period* (5W-20 for 2010–11, 0W-20 for 2012–13) so it stores cleanly. Options in the response.

## GENERATION 3 (BM) — 2014–2017 · SkyActiv-G 2.0 & 2.5 · ids 38714–38717 — ✅ WRITTEN TO DB (20 Jun 2026). Plug confirmed `PE5R-18-110`/`PE5S-18-110`; FL22 confirmed (2017 p441).

**Primary sources (official Mazda):**
- **2015 Mazda3 4-Door Owner's Manual** — https://www.mazdausa.com/siteassets/pdf/owners-optimized/2015/mazda3-4door/2015-mazda3-4-door-owners-manual.pdf
- **2017 Mazda3 4-Door Owner's Manual** — https://www.mazdausa.com/siteassets/pdf/owners-optimized/2017/mazda3-4door/2017-mazda3-owners-manual.pdf

Both SkyActiv-G engines, both years → **0W-20**. Capacities differ by engine (2.0 vs 2.5), so dual-value strings apply.

| Field | Verified value | Source (page) | Status |
|---|---|---|---|
| **Oil viscosity** | **0W-20** (full synthetic; SkyActiv-G 2.0 & 2.5) | 2015 p427 · 2017 p437 | ✅ |
| **Oil capacity w/filter** | **4.4 qt (SkyActiv 2.0) / 4.8 qt (SkyActiv 2.5)** | 2017 p589 | ✅ |
| Oil capacity w/o filter | 4.2 qt (2.0) / 4.5 qt (2.5) | 2017 p589 | ✅ |
| **Coolant** | **FL22**, ~6.7–6.9 qt (≈6.2–6.5 L; varies by engine/trans) | 2017 p589 | ✅ (type to re-confirm FL22 mark) |
| **Brake fluid** | **DOT-3** (J1703/FMVSS116) | 2017 p589 | ✅ |
| **Auto trans fluid** | **Mazda ATF FZ** (6-speed SkyActiv-Drive) | 2017 p589 | ✅ |
| Manual trans oil | API GL-4 (75W-80) | 2017 p589 | ✅ |
| **Power steering** | **Electric power steering — NO fluid** (not listed in lubricant table) | 2017 p589 (absent) | ✅ (verified by absence + EPS) |
| **Tire (base) + psi** | **P205/60R16 @ 250 kPa (36 psi)**; 215/45R18 @ 250 kPa | 2015 p576 · 2017 p595 | ✅ |
| **Lug-nut torque** | **108–147 N·m (80–108 ft·lbf)** — higher than Gen 1/2 | 2017 p498 | ✅ |
| **Spark plug** | Iridium, gap not published (SkyActiv pre-set); **OE number to confirm from 2017 spec table** | — | ⚠️ PENDING exact OE# |
| **Maintenance** | **Oil + filter: FLEXIBLE interval (oil-life monitor / wrench light), MAX 12 months** — *not* a fixed mileage · Spark plugs **75,000 mi** · Coolant (FL22) first **120,000 mi/10 yr** · Tire rotation: 2015 = **5,000 mi**, 2017 = flexible | 2015 p405 · 2017 p417 | ✅ |
| Battery group/CCA, drain/plug torque | Not in owner's manual | — | ⚠️ NULL |

### ⚠️ Gen 3 differs from Gen 1/2 in three ways worth your eyes before I write:
1. **Oil change is a flexible oil-life-monitor interval (max 12 months)** — I'll store `mileage_interval = NULL`, `months_interval = 12`, description "flexible (oil-life monitor), max 12 months." No fabricated fixed mileage.
2. **Electric power steering** → power-steering fluid stored as **"Electric power steering (no fluid)"**, not a fluid type.
3. **Lug torque is higher (108–147 N·m)** than Gen 1/2 (88–118 N·m).

Also note: the verified **2.5 capacity is 4.8 qt**, but the existing **2018 anchor stores `4.2`** — further evidence the 2018 row is wrong (already logged in `KYR_Data_Inconsistencies_To_Fix.md`).

**Two small items I'll finalize at write-time (after your OK):** the exact SkyActiv OE spark-plug number from the 2017 spec table, and re-confirming the "FL22" mark for Gen 3.
