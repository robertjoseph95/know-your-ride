# KYR — Honda Verification Log (Phase 1 ground truth)
### Know Your Ride Technologies LLC · June 2026

> Page-cited, owner's-manual-verified Honda specs. Same discipline as the Mazda 3 log: manufacturer source only, NULL anything not in the manual, dual-value strings for engine-divergent specs. These are **regression-set ground truth** for the future extraction tool (Phase 2).

---

## 2012 Honda Civic (id 11768) — 9th gen (2012–2015) — ✅ WRITTEN + LIVE (deploy 635d6087)
**Source:** 2013 Honda Civic Sedan Owner's Manual — `techinfo.honda.com/rjanisis/pubs/om/r31313/r31313om.pdf` (self-ID "2013 Civic Sedan" p1). Same generation as 2012.

| Field | Value | Page |
|---|---|---|
| Oil viscosity | 0W-20 | p349/351 |
| Oil capacity w/filter | **3.9 qt (1.8L) / 4.4 qt (2.4L Si)** | p349/351 |
| Coolant | Honda Type 2 (50/50) · 5.9 qt / 5.8 qt | p349/351 |
| Brake fluid | Honda DOT 3 | p349 |
| Trans fluid | ATF DW-1 (auto) / Honda MTF (manual) | p349 |
| Tire + psi | P195/65R15 @ 30 psi (LX) · P205/55R16 @ 32 (EX) · P215/45R17 @ 32 (Si) | p349/351 |
| Spark plug | NGK DILZKR7B11GS (1.8L) / ILZKR7B-11S (2.4L), iridium | p348/350 |
| Lug torque | 80 lbf·ft (108 N·m) | p322 |
| Oil interval | Flexible (Maintenance Minder), ≥ every 12 mo | p259–261 |
| Brake-fluid interval | every 3 years | p261 |
| NULL → service manual | plug gap, plug/coolant/trans intervals, battery group/CCA, drain torque; 1.5L Hybrid (separate OM) | — |

---

## 2008–2012 Honda Accord (ids 11378/11467/11561/11766) — 8th gen — ✅ WRITTEN (preview-verified; deploy pending spot-check)
**Source:** 2008 Honda Accord Sedan Owner's Manual — `techinfo.honda.com/rjanisis/pubs/om/acc080/acc0808om.pdf` (self-ID "2008 Accord Sedan" p1, 422 pp, text-extractable). Engines 2.4L I4 / 3.5L V6.

| Field | Value | Page (printed) |
|---|---|---|
| Oil viscosity | **5W-20** (API-certified) | p317/323 |
| Coolant type | Honda Type 2 (Long-Life) | p326 |
| Brake fluid | Honda DOT 3 | p319/326 |
| Trans fluid | **Honda ATF-Z1** (auto) / Honda MTF (manual) | p330/331 |
| Power steering | **Honda PSF — HYDRAULIC** (red-cap; differs from Civic's electric PS) | p334 |
| Tire + psi | P215/60R16 @ 30 psi · P225/50R17 @ 32 psi | p350 |
| Lug torque | 80 lbf·ft (108 N·m) | p366 |
| Oil interval | Flexible (Maintenance Minder), ≥ every 12 mo | p319 |
| Brake-fluid interval | every 3 years | p319 |
| **NULL → Jazerie service manual** | **oil capacity, coolant capacity, spark-plug type/number/gap** (not published in this older OM), trans capacity, fixed plug/coolant/timing-belt intervals, battery group/CCA, drain torque | — |

### Pipeline findings from the Accord (new vs the Civic):
1. **Older OMs are spec-THIN.** The 2013 Civic OM has a consolidated specifications table (capacities, plug numbers). The **2008 Accord OM does NOT** — it gives fluid *types* + tire + lug torque + the Minder, but **omits oil/coolant capacities and spark-plug part numbers** → those route to Jazerie. **Implication: older vehicles yield fewer OM-verified fields and lean harder on the service-manual queue.**
2. **Hydraulic vs electric power steering varies by model/era** — the Civic (9th gen) is electric (no fluid); the Accord (8th gen) is hydraulic (Honda PSF). The tool must read the actual fluid-locations diagram, not assume.
3. **Printed page ≠ PDF page index** — Honda OM front-matter offsets the printed page numbers from the PDF page indices; citations should use the *printed* page (the tool needs a printed↔PDF page map).
4. **Two-stage verification proven in the UI:** OM-verified fields render; NULL fields show "—" cleanly; the vehicle is *partially verified* (gate flipped) while capacity/plug fields await Jazerie. The per-field-table gate already supports this.

---

## 2017–2022 Honda CR-V (ids 12372/12511/12777/12847/12912) — 5th gen — ✅ WRITTEN (preview-verified; deploy with Accord)
**Source:** 2018 Honda CR-V Owner's Manual — `techinfo.honda.com/rjanisis/pubs/OM/AH/ATLA1818OM/enu/ATLA1818OM.PDF` (self-ID p1 "2018 … CR-V", 679 pp, **spec-dense consolidated table**). Engines: 1.5L Turbo (volume) + 2.4L (2017 LX). CVT + electric PS.

| Field | Value | Page (printed) |
|---|---|---|
| Oil viscosity | 0W-20 (Genuine Honda / API Premium-grade) | p653 |
| Oil capacity w/filter | **3.7 qt (1.5T) / 4.7 qt (2.4L)** | p653 |
| Coolant | Honda Type 2 (50/50) · **6.6 qt** | p653 |
| Brake fluid | Honda DOT 3 | p653 |
| Transmission | **Honda HCF-2 (CVT)** · capacity **3.9 qt (2WD) / 4.5 qt (AWD)** | p653 |
| Rear diff (AWD) | Honda DPSF-II · 1.32 qt | p653 |
| Power steering | **Electric (no fluid)** — confirmed: spec table lists no PSF; 5th-gen CR-V is EPS | p652–653 |
| Tire + psi | 235/65R17 @ 32 F / 30 R · 235/60R18 @ 33 F / 30 R | p653 |
| Spark plug | NGK **ILZKAR8J8SY** (1.5T) / **DILKAR7H11GS** (2.4L), iridium | p652 |
| Lug torque | 80 lbf·ft (108 N·m) | p623 |
| Oil interval | Flexible (Maintenance Minder), ≥ every 12 mo | Minder |
| Brake-fluid interval | every 3 years | Minder |
| NULL → service manual | plug gap, fixed plug/coolant intervals, battery group/CCA, drain torque | — |

**Finding confirmed:** newer gen + **spec-dense OM = far more complete** than the 2008 Accord — capacities, CVT fluid + capacity, rear-diff fluid, and plug part numbers all present. Only the gap/intervals/battery/drain-torque route to Jazerie. This is the kind of vehicle the OM pipeline handles best.

---

## 2016–2021 Honda Civic Sedan (ids 12240/12374/12513/38592/12778/12848) — 10th gen — ✅ WRITTEN + preview-verified + DEPLOYED
**Source:** 2017 Honda Civic Sedan **Owner's Guide** `OG-05950` (`00X31-TBA-G110`, 83 pp; self-ID p1 + p3 "2017 Honda Civic Sedan"). Robert-supplied PDF. Engines: 2.0L I4 (LX/EX) + 1.5L Turbo (EX-T/Touring). CVT (6MT Sport). Electric PS. Covers the **Sedan** only (not Si/Type R/Hatch/Coupe). NOTE: this is the abbreviated *Owner's Guide*, not the full Owner's Manual — **lug torque is absent here** (the 9th-gen full manual had 80 ft-lb; not carried over — service-manual field).

| Field | Value | Page (printed) |
|---|---|---|
| Oil viscosity | 0W-20 (Genuine Honda / API Premium-grade) | p134 + spec pp.148/150 |
| Oil capacity w/filter | **3.7 qt (1.5T) / 4.4 qt (2.0L)** | p148 / p150 |
| Coolant | Honda Type 2 (50/50) · **5.4 qt (1.5T) / 5.6 qt (2.0L)** (mfr lists 1.34/1.4 US gal ×4→qt) | p149 / p150 |
| Brake fluid | Honda DOT 3 (Heavy Duty; DOT 5 not compatible) | p138 + pp.148/150 |
| Transmission | **Honda HCF-2 (CVT)** · cap 3.9 qt (1.5T) / 3.7 qt (2.0L); 6MT Sport: Honda MTF 2.0 qt | pp.148/150 |
| Power steering | **Electric (no fluid)** — confirmed by under-hood fluid diagram (no PSF reservoir) + EPS index/fuse | p132–133 + index p25 |
| Tire + psi | 215/55R16 (2.0L) / 215/50R17 (1.5T) @ 32/32 psi · Sport 235/40R18 @ 33 F | p149/150 |
| Spark plug | NGK **ILZKAR8H8S** (1.5T) / **DILKAR7H11GS**, DENSO DXE22HQR-D11S (2.0L), iridium | pp.148/150 |
| Oil interval | Flexible (Maintenance Minder), ≥ every 12 mo | pp.129–131 |
| Brake-fluid interval | every 3 years | pp.129–131 |
| NULL → service manual | **lug torque** (not in Guide), plug gap, fixed plug/coolant/trans intervals, battery group/CCA, **drain-plug & trans-drain torque/size** | — |

**Generation-stable write:** 2017 (id 12374) cited to this exact Guide; 2016/2018–2021 written `owner-manual-verified (per 2017 OG-05950, 10th-gen shared drivetrain)` — same 1.5T/2.0L drivetrain, fluids, capacities, tire sizes across the generation (same method as Mazda Gen 1/2/3, CR-V). Fabricated `ai-haiku-4.5` rows purged from all spec tables; service-manual fields left empty → "pending verification" (gate confirmed: oil/fluids/tire visible `ver=1`, gap/battery/torque pending; negative control 2022 11th-gen still gated). Deployed `2026-06-21-civic-10thgen`.
