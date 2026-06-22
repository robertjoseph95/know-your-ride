# KYR — Ford Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified

Parallel to the Honda/Nissan/Mazda logs. Ford pilot. Source-map findings in `KYR_OEM_Manual_Source_Map.md`.

---

## ★ FORD PILOT — 2022 F-150 (id 12901, 14th gen) — ✅ WRITTEN + preview-verified + DEPLOYED
**Source:** 2022 Ford F-150 Owner's Manual (self-ID p1 "2022 FORD F-150 Owner's Manual", 750 pp). Direct PDF `fordservicecontent.com/Ford_Content/Catalog/owner_information/2022-Ford-F-150-Owners-Manual-version-1_om_EN-US_10_2021.pdf`. **Capacities & Specifications chapter pp.563–592 (printed).** 6 engines: 3.3L V6, 2.7L EcoBoost, 5.0L V8, 3.5L EcoBoost, 3.5L PowerBoost HEV, Raptor 3.5 HO.

| Field | Value | Page |
|---|---|---|
| Oil viscosity | **5W-20 (3.3L) / 5W-30 (2.7L EB, 3.5L EB, 5.0L V8, PowerBoost, Raptor)** | p569–577 |
| Oil cap w/filter | **6.0 qt (all V6 + PowerBoost) / 7.75 qt (5.0L V8)** | p569, p577 |
| Coolant | Motorcraft **Yellow** prediluted (WSS-M97B57-A2) · 12.7 qt (3.3L) / 15.1 (2.7EB) / 14.3 (3.5EB) / 13.2 (5.0L) / 13.7 (Raptor); PowerBoost dual-circuit 7.2+15.3 qt | p578–581 |
| Brake fluid | **Motorcraft DOT 4 LV** (WSS-M6C65-A2) — *Ford uses DOT 4, not DOT 3* | p590 |
| Transmission | **Motorcraft MERCON LV ATF** — 10-speed **conventional automatic** (not CVT) | p591 |
| Transfer case / front axle (4WD) | MERCON LV 1.5–1.9 qt; front axle 1.8 qt | p591–592 |
| Power steering | **Electric (EPAS, no fluid)** | p14/729 |
| **★ Lug torque** | **150 ft-lb (204 N·m) cold** — *truck-sized, NOT 83* | p650 |
| **★ Battery group** | **48 (std) / 94R (opt)** — derivable from Motorcraft BAGM part # | p563–568 |
| Spark plug | part # per engine (SP-520/578/588/596); **gap NOT in OM** | p563–568 |
| Oil filter | Motorcraft FL-500-S (most) / FL-2062-A (2.7EB) | p563–568 |
| Fuel tank | 23/26/36 gal (gas) · 30.6 (HEV) · 36 (Raptor) | p582–584 |
| NULL → gated | **drain-plug torque, oil-filter torque, spark-plug gap** (not in OM); **tire size + pressure** (door placard, not in OM body); trans-fluid capacity | — |

## Ford pilot findings (format characterization)
1. **Self-ID ✅. Spec-density ✅✅ — RICHEST OM source yet:** 30-page per-engine Capacities & Specifications chapter **+ Motorcraft part numbers** (oil filter, spark plug, battery, air/cabin filter, wiper). **Battery GROUP derivable** (48/94R) — a field Honda/Mazda/Nissan OMs didn't give.
2. **Torque:** lug only (**150 ft-lb**); **drain-plug & oil-filter torque NOT in OM** → Ford is like Honda/Mazda (lug only), **not** Nissan (which had the drain/filter bonus).
3. **Tire size + pressure NOT in OM** — explicitly punts to the **driver door placard** (truck has many cab/bed/wheel configs) → gated.
4. **URL pattern:** `fordservicecontent.com/Ford_Content/Catalog/owner_information/<YEAR>-Ford-<MODEL>-Owners-Manual-version-1_om_EN-US_<MM_YYYY>.pdf` — predictable but with a **date-stamp suffix that varies per manual**, and **large files (13.6 MB) that the server THROTTLES** → required a **chunked range-request download** (plain curl / urllib / WebFetch all timed out).
5. **★ Engine-matrix is the bulk challenge:** F-150 offers ~6 engines; the OM lists all generation-wide, and **vPIC is unreliable for the F-150** (it returns only ONE engine per year while the truck offers ~6). So for F-150 bulk, per-year engine roster can't be pinned from vPIC — options: write the generation's full multi-value strings to all year-rows (engine lineup is largely stable across 14th gen 2021–2026), or use EPA per-year. **To resolve before F-150 bulk.**
6. **Lincoln** = corporate sibling (same Motorcraft / fordservicecontent ecosystem — expect identical format).

**Pilot write:** single vehicle (2022 F-150, id 12901). Multi-value strings for engine-divergent fields; single-value common fields; fabricated ai-haiku purged; gated fields left pending. Preview-verified: multi-engine oil (6.0/7.75 qt) renders, **lug 150 (not 83)**, EPAS, MERCON LV, DOT 4, battery group 48/94R; gap/tire pending. Deployed `2026-06-21-ford-f150-pilot`.

**Next Ford step:** decide the F-150 bulk engine-roster approach, then bulk-verify F-150 (13th + 14th gen) and roll out to Escape/Explorer/Mustang/Ranger + Lincoln sibling.

---

## Ford Escape 4th gen (2020–2026, ids 12762/12830/12897/12962/13094/13160) — ✅ WRITTEN + preview-verified + DEPLOYED
**Source:** 2024 Escape OM (4th-gen rep; self-ID p1, Capacities & Specs p415–430). **EPA-confirmed roster STABLE** 2020–2026: 1.5L EcoBoost / 2.0L EcoBoost / 2.5L Duratec hybrid (FHEV/PHEV) every year → generation-wide multi-value.

| Field | Value | Page |
|---|---|---|
| Oil viscosity | **0W-20 (1.5L EB, 2.5 hybrid) / 5W-30 (2.0L EB)** | p417–419 |
| Oil cap w/filter | **5.0 qt (1.5L EB) / 6.1 qt (2.0L EB) / 5.7 qt (2.5 hybrid)** | p417–419 |
| Coolant | Motorcraft Yellow (WSS-M97B57-A2) · 8.0 qt (1.5L) / 9.0 qt (2.0L) / hybrid dual-circuit (FHEV 5.0+9.6; PHEV 6.6+10.1 qt) | p420–422 |
| Brake | Motorcraft **DOT 4 LV** | p430 |
| **★ Transmission** | **Motorcraft MERCON ULV** — **8-speed auto (8F35, gas) / eCVT (2.5 hybrid)** — *NOT F-150's 10-speed MERCON LV* | p429–430 |
| Power steering | **Electric (EPAS)** | — |
| **★ Lug torque** | **100 ft-lb (135 N·m), M12×1.5** — *NOT F-150's 150* | p411 |
| **★ Tire pressure** | **35 psi (P-metric)** — *crossover lists it in-OM* (truck didn't) | p389 |
| Battery group | **48 (1.5/2.0) / 99R (2.5 hybrid 12V)** | p415–416 |
| NULL → gated | drain-plug torque, oil-filter torque, spark-plug gap, **tire size** (trim placard) | — |

**Cross-platform differences confirmed by reading (not assumed):** Escape trans = **8-speed MERCON ULV** (vs F-150 10-speed MERCON LV); lug **100** (vs 150); tire pressure **in-OM** (vs placard-only on the truck). Format generalizes; per-platform specifics verified. Fabricated ai-haiku purged. Preview-verified all 6 render the 3-way oil + MERCON ULV + lug 100 + tire 35 + EPAS; gated fields pending. Deployed `2026-06-21-ford-escape`.

---

## Ford Explorer 6th gen (2020–2026, ids 12764/12832/12899/12964/13030/13096/13162) — ✅ WRITTEN + preview-verified + DEPLOYED
**Source:** 2022 Explorer OM (self-ID p1 "2022 EXPLORER Owner's Manual", 567 pp; Capacities & Specs pp.385–409; lug p380; PS p336; trans-ID p23 "10R60 10-speed"). **EPA-confirmed roster — hybrid DROPPED 2024** (standing rule, NOT generation-stable): 2020–2023 = 2.3T/3.0T/3.3 hybrid (3-way); 2024–2026 = 2.3T/3.0T (2-way, hybrid stripped). *(EPA's "3.3" in 2024 = the OM's separate "3.3L GASOLINE" Police-Interceptor fleet engine, not the consumer hybrid.)*

| Field | 2.3L EcoBoost | 3.0L EcoBoost | 3.3L Hybrid (HEV) | Page |
|---|---|---|---|---|
| Oil viscosity | 5W-30 | 5W-30 | **5W-20** | p388/398/409 |
| Oil cap w/filter | 5.2 qt | 6.0 qt | 6.0 qt | p387/394/408 |
| Oil filter | FL-910-S | FL-2062-A | FL-500-S | p383–384 |
| Spark / air | SP-594 / FA-1884 | SP-594 / FA-1884 | SP-520 / FA-1947 | p383–384 |
| Coolant cap | 14.1/15.2 qt | 15.5/18.0 qt | **13.9/16.4 qt + 4.6 qt HEV loop (dual-circuit)** | p387/394/408 |
| Trans cap | 12.6 qt | 12.6 qt | 13.7 qt | p386/400/407 |

| Common field | Value | Page |
|---|---|---|
| Coolant type | Motorcraft Yellow Prediluted (WSS-M97B57-A2) | p387 |
| **★ Transmission** | **Motorcraft MERCON ULV — 10-speed auto (10R60)**; hybrid = **10-speed modular-hybrid (NOT the Escape's eCVT)** | p23, p386 |
| Brake | Motorcraft **DOT 4 LV** | p389 |
| Power steering | **Electric (EPAS)** — OM: "no fluid reservoir to check or fill" | p336 |
| **★ Lug torque** | **150 lb-ft (204 N·m), M14×1.5** — *like F-150, NOT Escape's 100* | p380 |
| Battery group | **48** (BAGM-48H6-760, incl. hybrid 12V aux) | p383–384 |
| Transfer/axle (AWD) | MERCON LV transfer 1.1 qt; front axle 0.6 qt; rear 1.9 (gas)/1.7 (hybrid) qt | p390/397 |
| NULL → gated | **tire pressure + size (door placard — like F-150)**, drain-plug torque, oil-filter torque, spark-plug gap | — |

**Three-platform Ford spec map now confirmed by reading (not assumed):** Explorer = MERCON ULV / 10-spd 10R60 / lug 150 / tire placard; F-150 = MERCON LV / 10-spd / lug 150 / placard; Escape = MERCON ULV / 8-spd or eCVT / lug 100 / tire in-OM 35. **Hybrid drivetrains differ: Explorer hybrid = 10-speed modular (shares the 10R60), Escape hybrid = eCVT.** Preview-verified the per-year split: 2022 renders 3-way (5W-20 hybrid present), 2025 renders 2-way (hybrid stripped); MERCON ULV, lug 150, EPAS, gated fields pending. Deployed `2026-06-21-ford-explorer`.

---

## ★ F-150 BULK — 13th gen (2015–2020) + 14th gen (2021–2026) — ✅ WRITTEN + preview-verified + DEPLOYED
**11 rows** (2022 pilot already live → F-150 now ×12). The most complex single nameplate: 5–6 engines × 2 generations + diesel + per-year EPA roster. **Sources:** [2016 OM](https://www.fordservicecontent.com/Ford_Content/Catalog/owner_information/2016-F150-Owner-Manual-version-3_om_EN-US_02_2017.pdf) (13th early), [2017 OM](https://www.fordservicecontent.com/Ford_Content/Catalog/owner_information/2017-Ford-F-150-Owners-Manual-version-2_om_EN-US-EN-CA_12_2016.pdf) (trans-transition confirm), [2018 OM](https://www.fordservicecontent.com/Ford_Content/Catalog/owner_information/2018-Ford-F-150-Owners-Manual-version-5_om_EN-US_09_2018.pdf) (13th late + diesel), 2022 OM (14th, pilot). All self-ID gated.

**★ Confirm-don't-assume catches (would've been WRONG if assumed):**
- **Coolant: 13th gen ORANGE (WSS-M97B44-D2) vs 14th gen YELLOW (WSS-M97B57-A2)** — generational change, read both.
- **Transmission: 2015–16 = 6-speed (6R80); 2017 = 6-spd + 10-spd on 3.5EB (2017 OM confirmed the transition); 2018–20 = 6-spd (3.3 base) + 10-spd (others); 14th gen = 10-spd (10R80). All MERCON LV.**
- **5.0L V8: 13th gen 5W-20 (7.7 qt 2016 → 8.8 qt 2018) vs 14th gen 5W-30 7.75 qt** — viscosity AND capacity both flipped.
- **3.0L Power Stroke diesel (2018–2021): own oil 6.5 qt 5W-30 Diesel (WSS-M2C214-B1) + DEF 22.5 qt.** 2021 = 14th-gen Yellow coolant + diesel engine spec (engine field travels with engine, coolant with generation).

Per-year rosters: 2015–17 (2.7T/3.5NA/3.5T/5.0) · 2018–20 (+3.0d/3.3, −3.5NA) · 2021 (+PowerBoost, last diesel) · 2023 (−diesel) · 2024–26 (−3.3). Common all gens: DOT 4 LV, EPAS, lug **150** M14×1.5, battery 48/94R. **GATED (not fabricated): 5.2L Raptor R (2023+, no OM read — omitted from engine strings); drain/oil-filter torque, plug gap, tire (placard).** **No Lightning EV rows exist in DB** (confirmed — no EV-to-gas-spec risk). Preview-verified: Orange/6-spd (2016) vs Yellow/10-spd (2025) render distinctly; diesel on 2018–2021; Raptor R absent; per-year rosters correct; ver gate passes. Deployed `2026-06-21-ford-f150-bulk`.

**Ford coverage now: F-150 ×12 (13th+14th gen) + Escape ×6 + Explorer ×7 = 25 vehicles.**

---

## Lincoln Aviator 2nd gen (2020–2026, ids 233/1733/3238/4780/6369/7954/9588) — ✅ WRITTEN + preview-verified + DEPLOYED
**7 rows** (first Lincoln). **Sources:** [2023 Aviator OM](https://www.fordservicecontent.com/Ford_Content/Catalog/owner_information/2023_Lincoln_Aviator_Owners_Manual_version_2_om_EN-US.pdf) (self-ID p1, Capacities pp.467–487; lug p467; PS p414; tire p270) + [2020 Aviator Technical Specifications](https://media.lincoln.com/content/dam/lincolnmedia/lna/us/product/2020/Aviator/2020-aviator-tech-specs.pdf) (media.lincoln.com) for the **10-speed SelectShift** designation (not literally in the OM text — pulled an authoritative Lincoln source rather than infer). **EPA roster: 2020–2023 = gas 3.0TT V6 + PHEV (Grand Touring plug-in); 2024–2026 = gas only (PHEV dropped 2024).**

**Explorer-twin (CD6) was the HYPOTHESIS — every field read from the Aviator's own OM.** Confirmed SHARED: **MERCON ULV** (CD6, NOT F-150's LV) · **Yellow** coolant · EPAS · **lug 150** M14×1.5 · transfer-case MERCON LV 1.1 qt · oil 6.0 qt 5W-30 (WSS-M2C961-A1) · DOT 4 LV. **DIVERGED (luxury — read, not assumed):**
| Field | Aviator | Explorer |
|---|---|---|
| **Battery group** | **94R** (BAGM-94RH7-800) | 48 |
| **Electrified variant** | **PHEV (plug-in)** — dual-circuit coolant 19.3 qt engine + 5.1 qt battery/motor loop; trans 13.7 qt + rear aux battery | FHEV |
| Gas coolant cap | 18.0 qt | 15.5/18.0 (3.0EB) |

**PHEV fully covered by OM → written, not gated** (own coolant/trans/aux-battery captured; gas V6 spec NOT written to the PHEV config). NULL/gated: drain/oil-filter torque, plug gap, tire size/pressure (driver-door Tire Label). Preview-verified: 2022 renders gas+PHEV dual-circuit + 94R; 2025 gas-only; MERCON ULV 10-speed, lug 150, EPAS, ver gate passes. Deployed `2026-06-21-lincoln-aviator`.

**Ford/Lincoln coverage now: F-150 ×12 + Escape ×6 + Explorer ×7 + Lincoln Aviator ×7 = 32 vehicles.**

---

## Ford Mustang (gas coupe, S550+S650, ids 12769/12839/12904/13101/13167) — ✅ WRITTEN + preview-verified + DEPLOYED
**5 rows** (gas coupe only). **Mach-E (battery-electric SUV, 5 rows: 1723/3227/4768/7940/9574) deliberately UNTOUCHED — queued as a separate EV-verification pass** (no oil/conventional trans; no gas specs written to EVs). **Sources:** [2022 Mustang OM](https://www.fordservicecontent.com/Ford_Content/Catalog/owner_information/2022-Ford-Mustang-Owners-Manual-version-1_om_EN-US_11_2021.pdf) (S550) + [2025 Mustang S650 OM](https://www.fordservicecontent.com/Ford_Content/Catalog/owner_information/2025_MustangS650_OM_ENG_version1.pdf). EPA roster: all in-scope years = 2.3L EcoBoost + 5.0L V8 (V6 dropped 2018, none in scope).

| Field | S550 (2020–2022) | S650 (2025–2026) |
|---|---|---|
| Oil 2.3L / 5.0L | **6.0 / 10.0 qt** | **5.7 / 9.5 qt** (shrank) |
| Oil visc | 5W-30 (5W-50 track) | 5W-30 |
| Coolant | Yellow, 9.5/15.2 qt | Yellow |
| 2.3L filter/plug | FL-910-S / SP-550 | FL-2127 / SP-597-X |
| **Battery** | **96R** (BXT-96R-590) | **GATED** (S650 OM punts to dealer) |

**★ Transmission — the Mustang's signature divergence (manual option; fluid varies by gearbox, read in full):** Auto (10-spd 10R80) = **MERCON LV** (not the CD6 ULV); Manual **MT82** (2.3L + base 5.0 GT) = **Motorcraft Dual Clutch Transmission Fluid XT-11-QDC** (NOT MERCON — a real Ford quirk); Manual **Tremec TR-3160** (5.0 PP/Mach 1) = **MERCON LV**. Common: DOT 4 LV, EPAS, **lug 150 M14×1.5** (same as trucks despite sports car), rear axle 75W-85 + limited-slip friction modifier (XL-3). GATED: S650 battery group, **5.2L GTD/Shelby halo** (no clean OM, like Raptor R), drain/oil-filter torque, plug gap, tire (B-pillar placard). Preview-verified: S550 vs S650 oil distinct; manual-fluid split + auto MERCON LV render; 96R (S550) / gated (S650); lug 150; EPAS; ver passes. Deployed `2026-06-21-ford-mustang`.

**Ford/Lincoln coverage now: F-150 ×12 + Escape ×6 + Explorer ×7 + Aviator ×7 + Mustang ×5 = 37 vehicles.** EV queue: Mustang Mach-E ×5 (+ F-150 Lightning if added) — separate EV-spec method (battery coolant, reduction gear, HV/aux battery, no oil). Next gas: Ranger/Bronco, Lincoln Navigator/Nautilus/Corsair; or pivot to non-Ford makes.
