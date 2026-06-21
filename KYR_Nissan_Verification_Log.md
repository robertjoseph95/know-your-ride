# KYR — Nissan Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified

Parallel to `KYR_Honda_Verification_Log.md` / `KYR_Mazda3_Spec_Verification_Log.md`. Nissan pilot. Source-map findings in `KYR_OEM_Manual_Source_Map.md`.

---

## 2019–2025 Nissan Altima Sedan (ids 12702/461/1959/3485/5023/6604/8173) — L34 gen — ✅ WRITTEN + preview-verified + DEPLOYED
**Source:** 2019 Altima Sedan Owner's Manual (generation-representative; self-ID p1 "ALTIMA SEDAN 2019", 592 pp, **full spec-dense OM**). Direct PDF: `owners.nissanusa.com/content/techpub/ManualsAndGuides/Altima/2019/2019-Altima-owner-manual.pdf` (no VIN/login). **Engine config + 2.5L value-stability confirmed against each year's own manual** (2022 + 2025 capacities tables cross-checked). Engines: **PR25DD** (2.5L, all years) + **KR20DDET** (2.0L VC-Turbo, **2019–2024 only — dropped for 2025**). CVT. Electric PS.

| Field | Value | Page (section-prefixed) |
|---|---|---|
| Oil viscosity | **0W-20 (2.5L) / 5W-30 Ester (2.0T)** | 10-2, 10-6 |
| Oil capacity w/filter | **5.4 qt (2.5L) / 5.0 qt (2.0T)** (5.1 L / 4.7 L; mfr "5-3/8 qt / 5 qt") | 10-2 |
| Oil capacity w/o filter | 5.1 qt (2.5L) / 4.9 qt (2.0T) | 10-2 |
| Coolant | Nissan Long Life Antifreeze/Coolant (**blue**, pre-diluted) | 10-2, 8-6 |
| Coolant capacity | **8.8 qt (2.5L) / 8.7 qt (2.0T)** (8.3 L / 8.2 L w/ reservoir) | 10-2 |
| Brake fluid | **DOT 3** (Nissan Super Heavy Duty) | 10-3, 8-13 |
| Transmission | **Nissan CVT Fluid NS-3** (capacity NOT in OM → gated) | 8-13, 10-3 |
| Rear diff (AWD) | Nissan Diff Oil Hypoid Super GL-5 80W-90 | 10-3 |
| Power steering | **Electric (no fluid)** — capacities table lists no PSF | 10-2/10-3 |
| Tire size + psi | S 215/60R16 @ 32 · SV/SL 215/55R17 @ 33 · SR/Platinum 235/40R19 @ 33 | 10-9, 8-33 |
| **★ Lug torque** | **83 ft-lb (113 N·m)** — in OM | 6-8 |
| **★ Drain-plug torque** | **22–28 ft-lb (29–39 N·m)** — in OM | 8-12 |
| **★ Oil-filter torque** | **11–15 ft-lb (14.7–20.6 N·m)** — in OM | 8-12 |
| Fuel | 87 octane · tank 16¼ gal FWD / 16 gal AWD | 10-2, 10-4 |
| Oil interval | Oil control system (oil-life based) | 9-7 |
| Tire rotation | 5,000 mi (2.5L) / 7,500 mi (2.0T) | 9-7 |
| NULL → service manual | spark-plug type/gap, battery group/CCA, CVT-fluid capacity | — |

**★ Key finding — Nissan OM torque bonus:** unlike Honda/Mazda OMs, **Nissan's OM publishes drain-plug, oil-filter, and lug torque** → written as `owner-manual-verified` (no service-manual stage needed). Nissan vehicles therefore verify *more* claim-critical fields from the free stream. The prior ai-haiku data had **lug=80 (wrong; OM says 83)** and a **fabricated spark-plug torque** (OM gives none) — both corrected/purged.

**Generation write:** 2019 cited to this exact manual; 2020–2024 `owner-manual-verified` (per 2019 OM, L34, engine config confirmed vs each year OM); **2025 written 2.5L-only** (cited to 2025 OM — 2.0T dropped). Dual-value strings for oil/coolant on 2019–2024; single 0W-20 on 2025. Fabricated rows purged; gap/battery/CVT-cap left pending. Gate verified on preview (oil/fluids/tire + **all 3 torque rows show ver=1/verified**; gap/battery pending). Deployed `2026-06-21-nissan-altima-l34`.

**Pilot took ~30 min** (multi-section layout: fluids §10, torque §8/§6, tire psi §8-33, maintenance §9). URL filename scheme varies by year (techpub for 2019, content/dam for 2020+).

---

## Nissan Sentra (ids 12146/12553/12706 B17 · 467/1965/9788 B18) — ✅ WRITTEN + preview-verified + DEPLOYED
**Sources:** 2019 Sentra OM (B17 rep) + 2020 Sentra OM (B18 rep); **per-year engine config verified vs each year's own manual** (the standing rule — see `KYR_Verification_Pipeline_Design.md` §1). All self-ID p1. Electric PS (no PSF in capacities). CVT = **NS-3** both gens (pinned, not NS-2).

**Per-year engine roster (verified, not assumed):**
- **B17:** 2015 = **1.8L (MRA8DE) only** (SR Turbo launched 2017); 2018 & 2019 = **1.8L + 1.6T (MR16DDT)**.
- **B18:** 2020 / 2021 / 2026 = **2.0L (MR20DD) only**. 2026 confirmed B18 vs its own 2026 OM (MR20DD, 0W-20, 4-3/8 qt — same as 2020).

| Field | B17 (2015/2018/2019) | B18 (2020/2021/2026) |
|---|---|---|
| Oil viscosity | 0W-20 (both engines) — p10-2 | 0W-20 — p10-2 |
| Oil cap w/filter | 4.3 qt (1.8L) / 4.6 qt (1.6T); **2015: 4.3 qt only** | 4.4 qt (4-3/8) — p10-2 |
| Coolant | Nissan LLC blue · CVT 9.0 qt (1.8L) / 9.2 qt (1.6T) | blue · CVT 7.5 qt (7.1 L) |
| Brake | Nissan DOT 3 — p10-3 | DOT 3 (2026: DOT 3 or 4) — p10-3 |
| Transmission | **NS-3** (cap not in OM); 6MT: Nissan MTF TL/JR 75W-80 | **NS-3** (cap not in OM) |
| Power steering | Electric (no fluid) | Electric (no fluid) |
| Tire + psi | 205/55R16 (S) / 205/50R17 (SV/SR/SL) / 215/45R18 (NISMO) @ 33; **2015: no 18" NISMO** — p8-37 | 205/60R16 (S) / 215/50R17 (SV) / 215/45R18 (SR) @ 33 — p8-31 |
| ★ Lug torque | 83 ft-lb (113 N·m) — p6-8 | 83 ft-lb — p6-8 |
| ★ Drain-plug torque | 25 ft-lb (34 N·m) — p8-9 | 22–29 ft-lb (29–39 N·m) — p8-10 |
| ★ Oil-filter torque | 13 ft-lb (18 N·m) — p8-11 | 11–15 ft-lb (14.7–20.6) — p8-10 |
| NULL → service manual | spark-plug type/gap, battery group/CCA, CVT capacity | same |

**Notes:** dual-value strings only on 2018/2019 (both engines offered); 2015 + all B18 single-value. Fabricated ai-haiku purged (incl. **wrong lug=80** + **fabricated spark-plug torque** — OM gives none). Gate verified on preview (2019 B17 dual + 2020 B18: oil/fluids/tire + **all 3 torque rows ver=1/verified**; gap/battery/CVT-cap pending). **B15 (2000–2006, 7 rows) stays gated — pre-2008 manuals not hosted on the Nissan portal (unreachable).** Deployed `2026-06-21-nissan-sentra`.
