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
