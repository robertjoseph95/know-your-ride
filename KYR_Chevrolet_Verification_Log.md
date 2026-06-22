# KYR — Chevrolet (GM) Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified

Parallel to the Ford/Honda/Nissan/Mazda logs. **First GM-group pilot.** Source-map findings in `KYR_OEM_Manual_Source_Map.md`. Page citations are OM **printed-page** numbers (PDF page − 1).

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

## Silverado 1500 — DB inventory & per-year EPA engine roster (for bulk)
**21 rows, all gated** (20× `ai-haiku-4.5`, 2019 never-pulled `None`, 2026 `scraped`). **No EV trap** — Silverado EV is a separate nameplate, absent from the DB; all 21 rows are the gas truck.

| Gen | Year rows (ids) | EPA gas engines (per-year confirmed) |
|---|---|---|
| **GMT800** (’99–’06) | 2000(10962) 2001(10978) 2002(11002) 2003(11035) 2004(11081) 2005(11135) 2006(11202) | 4.3 V6, 4.8 V8, 5.3 V8; **6.0 V8 adds 2003** |
| **GMT900** (’07–’13) | 2008(11359) 2009(11447) 2012(11742) | 4.3 V6, 4.8 V8, 5.3 V8, 6.0 V8; **6.2 V8 adds 2009**; 6.0 drops from 1500 by 2012 |
| **K2XX** (’14–’18) | 2016(12202) 2017(12332) 2018(12467) | 4.3 V6, 5.3 V8, 6.2 V8 (EcoTec3; 4.8/6.0 gone) |
| **T1XX** (’19–present) | 2019(38591) 2020(12750) 2021(12819) 2022(12885) 2023(12950) **2024(13016 ✅)** 2025(13082) 2026(13148) | **2.7 turbo-4 adds 2019**; **3.0 Duramax diesel adds 2020**; **4.3 V6 drops after 2021**; 5.3 V8 + 6.2 V8 throughout |

**Bulk flags:** (1) **2019 is a split model-year** — redesigned T1XX sold alongside a carryover "Silverado 1500 LD" (old K2XX body, 4.3/5.3 only) with a *separate OM*; decide which OM covers the single 2019 row. (2) Pre-2008 GMT800/early GMT900 OMs — confirm self-ID before writing (source-confirmation gate). (3) Each year/gen needs its own OM for spec values (coolant spec, oil viscosity changed eras), engine roster per the table above.

## Queued discrete tasks
- [ ] **Duramax 3.0L diesel supplement pull** — separate batched pass; covers Silverado 1500 diesel (2020+) + GMC Sierra + HD trucks. Un-gate diesel columns after.
- [ ] **Silverado bulk** — by generation, OM per gen, engine roster per table above; resolve 2019 LD split.
- [ ] **Engine→transmission-speed binding** — confirm from an authoritative GM source (build/EPA) or leave the speed gated (ATF type already verified).
