# KYR — GM-Group (Chevrolet / GMC) Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified

Parallel to the Ford/Honda/Nissan/Mazda logs. **GM-group make** (Chevrolet pilot + GMC twin). Source-map findings in `KYR_OEM_Manual_Source_Map.md`. Page citations are OM **printed-page** numbers (PDF page − 1).

> **GM-group status:** **Silverado 1500 ✅ 21/21** (all 4 gens) · **GMC Sierra 1500 ✅ 15/15** (twin) = **36 GM trucks verified.** Next GM-group: Cadillac/Buick siblings, Suburban/Tahoe/Yukon, Colorado/Canyon, etc.

## ✅ GMC SIERRA 1500 — COMPLETE (15/15, twin of Silverado) — `2026-06-23-sierra`, commit 247eab62
Each row cited to its **own GMC Sierra OM** (9 reps pulled, all self-ID PASSED in-text incl. "Sierra/Sierra **Denali** 1500"). **Twin cross-check confirmed every platform-shared field matches Silverado per generation** (read from Sierra's OMs, not assumed): GMT800 (2000–2004) = 5W-30 / hydraulic PS / DOT 3 / DEXRON-III 4-spd / starburst→GM6094M; K2XX (2017–2018) = 0W-20 V8 / EPS / DOT 3 / dexos1 / VI-HP 6/8-spd; T1XX (2019–2026) = 0W-20 / EPS / **DOT 4** / dexos1 (+dexos D diesel) / HP-ULV 8/10-spd, diesel **LM2** (2020–2022) / **LZ0** (2023–2026), 4.3 V6 dropped 2022. Roster: 2000 = no 6.0. **No fluid/spec divergence found** — Denali-trim differences (wheels/tires/battery) fall in already-gated fields. Diesel via the shared "Chevrolet/GMC" Duramax supplement. **2003 V8 spark gap + part numbers GATED** (scanned OM, same as Silverado 2003). Engines byte-identical → per-engine values (oil cap, coolant cap, gap, filters) match Silverado.

---

---

## ★ GM/CHEVY PILOT — 2024 Silverado 1500 (id 13016, T1XX) — ✅ WRITTEN + preview-verified + DEPLOYED
**Source:** 2024 Silverado 1500 Owner's Manual, part# **85516379C** (self-ID p1 "2024 / Silverado / 1500 / Owner's Manual", 472 pp). Direct PDF from GM's own CDN: `contentdelivery.ext.gm.com/bypass/gma-content-api/resources/sites/GMA/content/.../MANUALS/8000/MA8860/en_US/4.0/24_CHEV_Silverado_1500_OM_en_US_U_85516379C_2024MAR04_3P.pdf`.
**Gas engines only: 2.7L turbo-4 (L3B), 5.3L V8 (L84), 6.2L V8 (L87).** 3.0L Duramax diesel GATED (separate supplement).

| Field | Value | Page |
|---|---|---|
| Oil viscosity | **5W-30 (2.7L turbo) / 0W-20 (5.3L & 6.2L V8)**; 0W-30 below −29 °C/−20 °F | p347 |
| Oil spec | **dexos1** full synthetic (ACDelco dexos1) — *OM states "dexos1", NO Gen qualifier → recorded as-is* | p347/429 |
| Oil cap w/filter | **6.0 qt / 5.7 L (2.7L) · 8.0 qt / 7.6 L (5.3L & 6.2L)** | p434 |
| **★ Spark-plug gap** | **0.026–0.030 in (2.7L) / 0.037–0.043 in (5.3L & 6.2L)** — *GM-ONLY bonus: gap IS in the OM* | p436 |
| Spark plug part# | ACDelco 41-106-IP / GM 12688094 (2.7L) · ACDelco 41-114 / GM 12622441 (5.3L & 6.2L) | p431 |
| Oil filter part# | ACDelco PF66 / GM 12727115 (2.7L) · ACDelco PF63 / GM 12707246 (5.3L & 6.2L) | p431 |
| Coolant | **DEX-COOL** (GM spec **GMW3420**), 50/50; 5 yr / 150,000 mi · cap 12.4 qt (2.7L) / 13.8 (5.3L) / 13.3 (6.2L) — *color NOT stated in OM → omitted* | p351/434 |
| Brake fluid | **GM-approved DOT 4** (per reservoir cap) | p358 |
| Transmission | **8-spd auto = DEXRON-HP / 10-spd auto = DEXRON ULV** (both OM-verified). **Engine→speed binding NOT in OM → gated** | p429 |
| Transfer case (4WD) | **DEXRON-VI** ATF, 1.6 qt / 1.5 L | p430/436 |
| Power steering | **Electric (EPS)** — *"does not have power steering fluid, regular maintenance is not required"* | p199 |
| **★ Lug torque** | **140 lb-ft (190 N·m)**, Wheel Nut Torque | p436 |
| Air / cabin filter | air ACDelco A3244C (high-cap)/A3246C; cabin ACDelco CF185 / GM 13508023 | p430/431 |
| Fuel tank | 24.0 gal (std/short box) · 28.3 gal (long box) | p434 |
| NULL → gated | **3.0L Duramax diesel (all fields)**, **battery group/CCA** (OM punts to label; AGM/Stop-Start), **drain-plug & oil-filter torque** (not in OM — lug only), **tire size/pressure** (door placard), **per-engine transmission speed** | — |

## GM pilot findings (format characterization)
1. **Self-ID ✅ (Grade A).** Page 1 names year + model + part#.
2. **Spec-density ✅✅✅ — RICHEST OM in the campaign.** Per-engine oil/coolant capacities **+ oil-filter & spark-plug part numbers + spark-plug GAP** (a field Honda/Mazda/Nissan **and** Ford OMs all OMIT). Plus engine VIN codes (K/D/L) and belt-routing diagrams.
3. **Torque profile = LUG-ONLY** (Ford-style): only Wheel Nut Torque (140 lb-ft). **No drain-plug / oil-filter torque** anywhere → unlike Nissan (which had the drain/filter bonus).
4. **Access — NO 403 with a spoofed browser UA** (GM 403s *bare* UAs; a Chrome UA returned HTTP 200). GM's CDN **ignores Range requests** and serves the whole 16.3 MB file in one GET → **simpler than Ford, no chunked download / no throttle.**
5. **URL pattern:** `contentdelivery.ext.gm.com/.../MANUALS/<MA####>/.../<YY>_CHEV_<Model>_OM_en_US_U_<part#>_<YYYYMMMDD>_3P.pdf`. The **part# + `MA####` path segment are model-year-specific** → bulk needs per-year URL discovery via the chevrolet.com/support portal (entry point) before download.
6. **Diesel lives in a SEPARATE Duramax Supplement** — the gas OM explicitly punts diesel oil/coolant/ATF/capacities/parts to it. NEVER fabricate diesel from the gas OM. → **queued as a discrete batched pull** (covers Silverado/Sierra/HD diesels across years).
7. **CONFIRM-DON'T-ASSUME catches:** (a) the **2.7L turbo uses 5W-30 while the V8s use 0W-20** — the thinner oil is the *V8*, counterintuitive; (b) **EPS confirmed by reading the steering section** (the Maxima lesson — full-size trucks are exactly where hydraulic-vs-electric varies); (c) coolant color **never stated** → DEX-COOL/GMW3420 recorded, "orange" omitted.
8. **GM-group siblings** (GMC Sierra, Cadillac Escalade, Buick, etc.) should inherit this exact ecosystem (`contentdelivery.ext.gm.com`, browser-UA, lug-only + spark-gap, DEX-COOL, dexos1) — characterize one sibling before its bulk.

**Pilot write:** single vehicle (2024 Silverado 1500, id 13016, gas). Multi-value strings for engine-divergent fields; fabricated ai-haiku purged; gated fields left pending. Preview-verified (`ver===1` on oil/fluids/parts/torque): per-engine oil 5W-30 vs 0W-20, spark gap renders, EPS, DEX-COOL GMW3420, DOT 4, lug 140; diesel/battery/trans-speed gated. Deployed **`2026-06-22-silverado-pilot`** (commit `4a1c06f9`).

---

## ★ T1XX BULK (2019–2026) — ✅ WRITTEN + preview-verified + DEPLOYED (`2026-06-22-silverado-t1xx`, commit 97600e97)
All 8 current-gen rows done (2024 pilot + 7 bulk: 2019, 2020, 2021, 2022, 2023, 2025, 2026).
**Sources:** 2021 Silverado 1500 OM (84550389C, early-T1XX rep incl. 4.3 V6) + 2024 OM (85516379C) — gas values cross-confirmed identical for shared engines. + 2021 LM2 Duramax sup (84557033C) + 2024 LZ0 Duramax sup (85137419 B).

| Field | 2.7T (L3B) | 4.3 V6 (LV3, ’19–’21) | 5.3 V8 (L82/L84) | 6.2 V8 (L87) | 3.0 Duramax diesel |
|---|---|---|---|---|---|
| Oil | 5W-30 dexos1 | 5W-30 dexos1 | 0W-20 dexos1 | 0W-20 dexos1 | 0W-20 **dexos D** |
| Cap w/filter | 6.0 qt | 6.0 qt | 8.0 qt | 8.0 qt | 7.0 qt |
| Coolant cap | 12.4 qt | 12.2 qt | 13.5 (L82)/13.8 (L84) qt | 13.3 qt | **LM2 20.5 / LZ0 19.4 qt** + charge-air |
| Spark gap | .026–.030 | .037–.043 | .037–.043 | .037–.043 | n/a (compression) |

**Diesel version split (CONFIRM-DON'T-ASSUME paid off — LM2 ≠ LZ0):** 2020–2022 = **LM2** (coolant 20.5 qt, DEF 5.3 gal, fuel filter GM 23304096/TP1015, VIN T); 2023/2025/2026 = **LZ0** (coolant 19.4 qt, DEF 5.4 gal, fuel filter GM 13539108, VIN 8); oil cap 7.0 qt & 0W-20 dexos D & DEXRON ULV 10-spd common to both. **2019 = no diesel** (launched 2020); **2019 row confirmed new-body T1XX** (old-body "Silverado 1500 LD" is a separately-named nameplate, absent from DB).
**Per-era gas part #s:** 2019–21 oil filter 2.7L PF66/GM 55495105, V-engines PF63E/12690385; 2022–26 2.7L PF66/12727115, V8s PF63/12707246. Spark 2.7L 41-106-IP, others 41-114. Cabin CF185.
Common gen-stable: DEX-COOL GMW3420 (no color), DOT 4, EPS, lug 140, 8-spd DEXRON-HP/10-spd DEXRON ULV, transfer DEXRON-VI 1.6 qt. Gated: battery group, drain/oil-filter torque, tire (placard), gas trans-speed binding.

---

## ★ K2XX BULK (2016–2018) — ✅ WRITTEN + preview-verified + DEPLOYED (`2026-06-22-silverado-k2xx`, commit 9c098e12)
3 rows from the **2017 Silverado 1500 OM** (23476161A, K2XX gen-rep, self-ID p1), applied across 2016–2018 (engines EPA-confirmed byte-identical: 4.3 V6 LV3/LV1, 5.3 V8 L83, 6.2 V8 L86; no 2.7T, no diesel). No GM-hosted 2016 full OM reachable → representative-OM application (same method as F-150 13th gen / T1XX); honest provenance in source string. **NOTE: combined 1500+2500/3500 OM** — the 6.0L V8 / hydraulic PS belong to the HD; the 1500 fields below were isolated.

| Field | 4.3 V6 | 5.3 V8 (L83) | 6.2 V8 (L86) |
|---|---|---|---|
| Oil | 5W-30 dexos1 | 0W-20 dexos1 | 0W-20 dexos1 |
| Cap w/filter | 6.0 qt | 8.0 qt | 8.0 qt |
| Coolant cap | 15.9 qt | 16.6 qt | 16.6 qt |
| Spark gap | .037–.043 | .037–.043 | .037–.043 |
| Oil filter | PF63E / GM 19330000 | (same) | (same) |
| Spark plug | 41-114 / GM 12622441 | (same) | (same) |

**★ K2XX divergences from T1XX (READ fresh, NOT carried back):** **brake = DOT 3** (T1XX DOT 4); **ATF 6-spd DEXRON-VI / 8-spd DEXRON-HP** (no 10-speed; T1XX = 8/10 HP/ULV); **coolant ~16 qt** (T1XX ~12–14); **fuel tank 26/34 gal** (T1XX 24/28.3); **rear axle 75W-85 / front 75W-90 given** (T1XX OM punted to dealer); **DEX-COOL with NO GMW3420 number stated** (no color); cabin **CF188** (T1XX CF185); oil filter PF63E/**19330000** (T1XX PF63/12707246). **Oil viscosity SAME as T1XX** (0W-20 V8 / 5W-30 4.3) — the "K2XX maybe 5W-30 across the board" hypothesis was disproven by reading; 2017 already shows 0W-20 on the V8s. EPS (1500), lug 140, transfer DEXRON-VI common. Gated: battery group, drain/oil-filter torque, tire, trans speed-binding.

---

## ★ GMT900 BULK (2008, 2009, 2012) — ✅ WRITTEN + preview-verified + DEPLOYED (`2026-06-23-silverado-gmt900`, commit 2c9f2dc9)
3 rows, **each from its own GM-hosted OM** (self-ID gate PASSED in-text: "20xx Chevrolet Silverado Owner Manual"). Per-year EPA roster: **2008** = 4.3/4.8/5.3/6.0; **2009** = +6.2 (5 engines); **2012** = 4.3/4.8/5.3/6.2 (6.0 dropped).

| Engine | Oil visc | Oil cap | Coolant | Spark gap | Oil filter |
|---|---|---|---|---|---|
| 4.3 V6 | 5W-30 | 4.5 qt | 16.5 qt | **0.060 in** | PF47 / 25010792 |
| 4.8 / 5.3 / 6.0 / 6.2 V8 | 5W-30 | 6.0 qt | 16.8–17.6 qt | 0.040 in | PF48 / 89017524 |

**★ Mid-gen oil-SPEC catch: GM6094M (2008/2009, pre-dexos) vs dexos1 (2012)** — read per year, not assumed. Spark-plug PNs also revise per year (2008 4.3=41-932/V8=41-985; 2009 4.3=41-993/V8=41-985; 2012 4.3=41-101/V8=41-110).
**★ Era divergences vs K2XX/T1XX (all READ fresh):** **5W-30** (not 0W-20); **HYDRAULIC power steering** (GM PS fluid 89021184) — NOT EPS (this era predates electric steering); **DEXRON-VI ATF** 4-spd (4L60-E) / 6-spd (6L80-E/6L90-E); **DOT 3** brake; oil cap V8 **6.0 qt** / V6 **4.5 qt** (vs K2XX 8.0/6.0); coolant ~16–17 qt; front axle **80W-90** / rear **75W-90**. DEX-COOL (no GMW3420 #, no color). Lug 140; transfer DEXRON-VI 1.6 qt. Gated: battery group, drain/oil-filter torque, tire, trans speed-binding.

---

## ★ GMT800 BULK (2000–2006) — ✅ WRITTEN + preview-verified + DEPLOYED (`2026-06-23-silverado-gmt800`, commit 9be6aa2b) — SILVERADO 1500 COMPLETE 21/21
7 rows, **each from its own GM-hosted OM** (self-ID gate PASSED in-text). Per-year EPA roster: **2000** = 4.3/4.8/5.3 (no 6.0); **2001–2006** = +6.0 V8. Engines: VORTEC 4.3 V6, 4.8/5.3/6.0 V8 (8.1 V8 = HD, excluded). Oil cap 4.5 qt (V6) / 6.0 qt (V8s); 5W-30; lug 140; **hydraulic PS** (GM PS fluid 89021184); **DOT 3** (Delco Supreme 11); **4-speed only** (4L60-E/4L65-E); axles 80W-90 front / 75W-90 rear; transfer case ~2.0 qt; fuel tank 26/34 gal; DEX-COOL (no spec#/color).

**★ Per-year / sub-era catches (read from each year's own OM, not interpolated):**
- **Oil spec:** API-starburst only (**2000–2003**, GM6094M not cited) → **GM6094M** (2004–2006)
- **ATF:** DEXRON-III (2000–2005) → **DEXRON-VI** (2006)
- **V8 spark gap:** 0.060 in (2000–2002) → 0.040 in (2004–2006); V6 always 0.060
- **Cooling cap** per year (~12.6 early → ~16.8 late, config-dependent)
- **★ 2003 BOUNDARY:** the 2003 OM is a scanned/OCR copy whose technical-data table is illegible → **V8 spark gap & part numbers GATED for 2003** (not inferred from neighboring years), per the gate-if-ambiguous rule. Caps/oil/ATF/PS read cleanly from its legible sections.

---

## ✅ SILVERADO 1500 — COMPLETE (21/21 rows, all 4 generations)
| Gen | Years | Brake | PS | ATF | Oil visc (V8) | Oil spec |
|---|---|---|---|---|---|---|
| GMT800 | 2000–2006 | DOT 3 | Hydraulic | DEXRON-III (VI ’06), 4-spd | 5W-30 | API-starburst (’00–’03) / GM6094M (’04–’06) |
| GMT900 | 2008/09/12 | DOT 3 | Hydraulic | DEXRON-VI, 4/6-spd | 5W-30 | GM6094M (’08/09) / dexos1 (’12) |
| K2XX | 2016–2018 | DOT 3 | **EPS** | DEXRON-VI/HP, 6/8-spd | **0W-20** | dexos1 |
| T1XX | 2019–2026 | **DOT 4** | EPS | DEXRON-HP/ULV, 8/10-spd | 0W-20 | dexos1 (+ dexos D diesel) |

The full sweep is a clean CONFIRM-DON'T-ASSUME case study: brake DOT 3→DOT 4, PS hydraulic→EPS, oil 5W-30→0W-20, oil-spec GM6094M→dexos1, ATF 4-spd DEXRON-III→10-spd DEXRON-ULV — every axis shifted across the generations and was read fresh per era.

---

## Silverado 1500 — DB inventory & per-year EPA engine roster (for bulk)
**21 rows, all gated** (20× `ai-haiku-4.5`, 2019 never-pulled `None`, 2026 `scraped`). **No EV trap** — Silverado EV is a separate nameplate, absent from the DB; all 21 rows are the gas truck.

| Gen | Year rows (ids) | EPA gas engines (per-year confirmed) |
|---|---|---|
| **GMT800** (’99–’06) | 2000(10962) 2001(10978) 2002(11002) 2003(11035) 2004(11081) 2005(11135) 2006(11202) | 4.3 V6, 4.8 V8, 5.3 V8; **6.0 V8 adds 2003** |
| **GMT900** (’07–’13) | 2008(11359) 2009(11447) 2012(11742) | 4.3 V6, 4.8 V8, 5.3 V8, 6.0 V8; **6.2 V8 adds 2009**; 6.0 drops from 1500 by 2012 |
| **K2XX** (’14–’18) | 2016(12202) 2017(12332) 2018(12467) | 4.3 V6, 5.3 V8, 6.2 V8 (EcoTec3; 4.8/6.0 gone) |
| **T1XX** (’19–present) | 2019(38591) 2020(12750) 2021(12819) 2022(12885) 2023(12950) **2024(13016 ✅)** 2025(13082) 2026(13148) | **2.7 turbo-4 adds 2019**; **3.0 Duramax diesel adds 2020**; **4.3 V6 drops after 2021**; 5.3 V8 + 6.2 V8 throughout |

**Bulk flags:** (1) **2019 is a split model-year** — redesigned T1XX sold alongside a carryover "Silverado 1500 LD" (old K2XX body, 4.3/5.3 only) with a *separate OM*; decide which OM covers the single 2019 row. (2) Pre-2008 GMT800/early GMT900 OMs — confirm self-ID before writing (source-confirmation gate). (3) Each year/gen needs its own OM for spec values (coolant spec, oil viscosity changed eras), engine roster per the table above.

## Progress & queued tasks
- [x] **2024 Silverado 1500 pilot** (gas) — `2026-06-22-silverado-pilot`
- [x] **2024 diesel column** (LZ0) — `2026-06-22-silverado-diesel`
- [x] **Duramax 3.0L supplements** — 2024 LZ0 (85137419 B) + 2021 LM2 (84557033C) pulled & extracted. *Confirmed "Chevrolet/GMC" shared doc → also covers Sierra.* (Still pending: HD 6.6L supplement for the Sierra 2500 rows; 2020/2022 LM2 + 2023/2025/2026 LZ0 per-exact-year part #s if needed — values stable within each version.)
- [x] **T1XX bulk (2019–2026, 8 rows)** — `2026-06-22-silverado-t1xx`; 2019 LD split resolved (new-body T1XX).
- [x] **K2XX (2016–2018, 3 rows)** — DONE (`2026-06-22-silverado-k2xx`); 2017 OM gen-rep; DOT 3 / 6-8 spd / ~16qt coolant / axle fluids.
- [x] **GMT900 (2008, 2009, 2012, 3 rows)** — DONE (`2026-06-23-silverado-gmt900`); per-year OMs (self-ID PASSED); 5W-30, hydraulic PS, DOT 3, GM6094M vs dexos1 per year.
- [x] **GMT800 (2000–2006, 7 rows)** — DONE (`2026-06-23-silverado-gmt800`); all 7 self-ID PASSED; per-year API-starburst/GM6094M, DEXRON-III/VI, 0.060/0.040 gap; 2003 V8 gap GATED (scanned OM). **→ SILVERADO 1500 COMPLETE 21/21.**
- [ ] **Engine→transmission-speed binding** — confirm from an authoritative GM source or leave gated (ATF type already verified; diesel→10-spd confirmed in supplement).
- [x] **GMC Sierra 1500** (15 rows) — DONE (`2026-06-23-sierra`, commit 247eab62); twin confirmed vs Silverado per gen; diesel-complete via shared supplement; 2003 V8 gap gated.
- [ ] **GM-group next:** Sierra 2500 HD (4 rows, 6.6L Duramax — separate supplement); Cadillac/Buick siblings (inherit GM ecosystem); Suburban/Tahoe/Yukon/Escalade (note LM2 SUV diesel); Colorado/Canyon.
