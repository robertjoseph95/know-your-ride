# KYR — Hyundai Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified · FIRST Hyundai Motor Group make

Parallel to the GM-group / Ford / Honda / Nissan / Mazda / Subaru logs. Make characterization + reusable
source pattern in `KYR_OEM_Manual_Source_Map.md` (Hyundai section). **Host:** `owners.hyundaiusa.com` MyHyundai
glovebox-manual (free, no auth, citable manufacturer source). **This is the HMG foundation — it pre-characterizes
Kia (~80 rows / 12 nameplates), and specifically Optima/K5 as a near-twin of the Sonata (shared platform + Theta II/Smartstream engines).**

> **Hyundai status (2026-11-14): 15 rows.** **Sonata ✅ 5/14** (NF + LF + DN8 clusters; 9 deferred) · **Elantra ✅ 4/13** (2017/2020 AD + 2021/2022 CN7; 9 deferred) · **Tucson ✅ 6/10** (2018/2020/2021 TL + 2022/2023/2024 NX4; 4 deferred) — the FIRST Hyundai SUV, sets the SUV-body baseline and is the first slice with OM service intervals recorded (39 rows). Make source characterized + engine families on record. DB also has Santa Fe 13, Accent, Tiburon, Palisade 6, Kona 5, Venue, Veloster, Ioniq (EV) — pending. **Kia does NOT cheaply unlock** (source boundary — full OMs behind a JS viewer; queued viewer-spike). **Next Hyundai:** Kona → Santa Fe → Palisade (recon done 2026-11-10; Tucson baseline inherited), then Elantra-N/turbo-trim targeted pulls.

## ✅ TUCSON — 6/10 (2018/2020/2021 TL + 2022/2023/2024 NX4) — `2026-11-13-hyundai-tucson`, commit 03fa8111 — THIRD HYUNDAI, FIRST SUV (sets the SUV-body baseline)
Read 2026-11-10; every value re-read page-by-page from its own book 2026-11-13; written 2026-11-13 (backup `wrench_vehicles.db.bak_tucson_20261113_212022`), deployed 2026-11-14 (live blob `data.058aeade.js` md5 `058aeade…` byte-identical to the commit; `_verify_shipped.py` PASS 58; README count copy 285→291). Multi-engine per row (TL: Nu 2.0 GDI + Theta II 2.4 GDI + Gamma 1.6T; NX4: Smartstream G2.5 GDI). 2022+ 1.6T Hybrid / Plug-in Hybrid = own 81.7 MB OM → gated, gas only written. **Ruling 2026-11-13 ("Go, write Tucson"): record the OM normal-schedule intervals** (the Mazda 3 convention) — 39 maintenance rows written, not the interval-free single row the Sonata/Elantra slices used. Write script `_write_hyundai_tucson.py` (committed; dry-run default, `--write` to apply).

| Row | Engines | Oil (drain+filter) | Visc | Coolant | Trans |
|---|---|---|---|---|---|
| **2018 TL** (id 12524) | 2.0 Nu GDI + 2.4 Theta II GDI + 1.6T Gamma | **4.23** / **5.07** / **4.76** | 5W-20 / 5W-20 / **5W-30** (1.6T) | 7.93 / 8.14 / 7.5 | AT SP-IV 7.71 (2.0) / 7.08 (2.4); 1.6T Ecoshift DCT GL-4 70W 2.01–2.11 |
| **2020 TL** (id 666) | 2.0 Nu GDI + 2.4 Theta II GDI | 4.23 / 5.07 | 5W-20 (API Latest / ILSAC Latest) | 7.93 / 8.14 | AT SP-IV 7.71 (2WD) / 7.50 (AWD) (2.0); 7.08 (2.4, 2WD and AWD) |
| **2021 TL** (id 2160) | "2.0 GDI / 2.4 GDI" (the OM's own labels) | 4.23 / 5.07 | 5W-20 | 7.93 / 8.14 | as 2020 (capacities pages 8-8/8-9 byte-identical to 2020 — read anyway) |
| **2022 NX4** (id 3689) | Smartstream G2.5 GDI | **6.13** | **0W-20** full synthetic (API SN PLUS/SP, ILSAC GF-6) | **10.11** | AT SP-IV 6.87 |
| **2023 NX4** (id 5210) | Smartstream G2.5 GDI | 6.13 | 0W-20 full synthetic | 10.11 | AT SP-IV 6.87 |
| **2024 NX4** (id 6783) | Smartstream G2.5 GDI | 6.13 | 0W-20 full synthetic | **10.04** (the one NX4 change) | AT SP-IV 6.87 |

Common: **EPS/MDPS** (no PS fluid) · brake **DOT 3/4** (TL; 0.74–0.85 qt) → **DOT 4 LV** (NX4; SAE J1704 / FMVSS 116 / ISO 4925 Class 6) · AWD **rear diff GL-5 75W/90 0.56–0.67 qt (2018) → 75W/85 (2020+)**; transfer case 0.36–0.38 (TL 2.0/2.4) · 0.51–0.55 (TL 1.6T) · 0.45–0.50 (2020/21) · 0.65–0.71 (NX4) · **lug 79–94 lb-ft** both gens (written WITH a citation suffix — never the frozen bare token) · fuel **16.38 gal (TL) / 14.27 gal (NX4)** · tires **225/60R17 · 225/55R18 · 245/45R19 (TL) / 235/65R17 · 235/55R19 (NX4)** @ 35/35 · spare T155/90D16 @ 60 psi (2018), T155/90D16 or T135/90D17 (2020/21), T135/90D17 (NX4).

**Gates (null; reasons live in the `source` suffix and here, never in shipped columns):** plug PN/gap — no Tucson book publishes one (interval only, all six) · **12V battery** — the TL books carry no 12V spec at all (only the CR2032 fob cell); the NX4 books show only a "how to read the capacity label" teaching example (MF68L-DIN under image code OTM090064L, a Santa Fe TM illustration reused) — NOT a Tucson spec, gated · `battery_notes` NULL · HEV/PHEV (own OM) · 2018 brake fluid is inspect-only (I I I …) → no replacement row; 2021 TL and all NX4 show R → written.

**★ Carry outcomes (engine predicts, the OM decides):** 2.0 Nu **GDI 4.23 = Elantra Nu MPI 4.23** (the pre-read prediction of a GDI-vs-MPI difference was WRONG — read, don't infer) · 1.6T Gamma **4.76 = Elantra 2020 4.76**, and **5W-30 again** (vs Sonata LF 5W-20) · 2.4 Theta II **5.07 = Sonata LF 5.07** · Smartstream 2.5 **6.13 = Sonata 2024 facelift 6.13** (not the 2021 Sonata's 5.49). **SUV-body baseline (body-decided; all diverge from the sedans):** coolant 7.5–8.14 (TL) / 10.04–10.11 (NX4); fuel 16.38 / 14.27 gal (vs Sonata 15.9/18.5, Elantra 14.0/12.4); 17–19 in SUV tire sizes. **Coolant-basis gate:** all six books sit on one consistent total-system scale (TL 7.5–8.14, NX4 10.04–10.11, NX4 ≈ Sonata 2024's 9.2–9.3 scale) → cleared, written. **Kona / Santa Fe / Palisade inherit this baseline — read their body-decided fields fresh.**

**★ Source/format catches (banked to source map):** TL books (2018/20/21) text-extract cleanly. **NX4 books encode table text as glyph ids** — pdfplumber returns `(cid:N)`; `chr(N+29)` decodes the capacities table — and the **NX4 maintenance-schedule tables have NO extractable text at all** (drawn, cid-decode returns nothing) → rendered at 130 dpi with `page.to_image(resolution=130).save()` and read visually. Self-ID held per book by the engine-displacement table + wheelbase (TL 105.12 in / NX4 108.5 in: 2018 p.8-2, 2020/21 p.8-2, 2022 p.2-12, 2023/24 p.10-2). The 2017 and 2019 portal folders hold only QRG / Getting-Started / Display-Audio guides — the Elantra "filename ≠ full OM" lesson again, caught by content-check.

**OM normal-schedule intervals written (mi / mo, OM page):** TL — oil & filter 7,500/12 (Gamma 6,000/12; p.7-9 / 7-14), plugs 97,500 (Gamma 42,000), engine air cleaner 22,500/36 (Gamma 18,000/36), climate-control filter 7,500/12 (Gamma 6,000/12), tire rotation 7,500 (Gamma 6,000), coolant first 120,000/120 then 30,000/24 (p.7-10 / 7-15); 2021 adds brake fluid 30,000/48 (p.7-11). NX4 — oil & filter 8,000/12, plugs 96,000, engine air cleaner 24,000/36, coolant first 120,000/120 then 24,000/24, brake fluid 48,000/48 (2022 p.9-8..9-10, 2023 p.9-9..9-11, 2024 p.9-10..9-12). Row counts 2018 = 11 (two oil + two plug rows for the Gamma schedule), 2020 = 6, 2021 = 7, NX4 = 5 each → **39**. Scope note: beyond the oil/plug rows named in the approved log, the air-cleaner / cabin / rotation / coolant / brake-fluid rows were read from the same schedule pages and written; NX4 climate-filter and rotation rows were NOT extracted from the rendered images (recheck if wanted).

### DEFERRED (4, each with reason)
- **2017 (id 12382)** — no full OM on the portal (folder holds only 2016/2018 quick-reference guides).
- **2019 (id 12677)** — portal folder holds only Getting Started + Display Audio guides (variant-only).
- **2025 (id 8358), 2026 (id 9972)** — full OM not posted. **2026 remains the blacklisted `scraped` value — gated, never shipped.**
- **⚠ Separate-OM engines (known gap):** 2022+ 1.6T Hybrid / Plug-in Hybrid (own OM) → gated, not guessed. (The 2018 1.6T Gamma IS in the base book and was written.)

---

## ✅ ELANTRA — 4/13 (2017/2020 AD + 2021/2022 CN7) — `2026-07-01-hyundai-elantra`, commit 8a754d96 — SECOND HYUNDAI (cashes the foundation)
Compact sibling; the source foundation transferred cheaply (host + self-ID + gates). Multi-engine (base OM only). HEV + separate-OM trims gated.

| Row | Engines | Oil | Visc | Coolant | Trans |
|---|---|---|---|---|---|
| **2017 AD** | 2.0 Nu MPI | **4.23** | 5W-20 | 6.34(MT)/6.97(AT) | 6AT SP-IV 7.08 |
| **2020 AD** | 2.0 Nu MPI + 1.6T (Gamma) | 4.23 / **4.76** | 5W-20 / **5W-30** | 6.34/6.97 · 1.6T 6.45 | IVT SP-CVT1 6.86; 1.6T 7-DCT |
| **2021 CN7** | 2.0 Smartstream | **4.54** | 0W-20 | **7.82** | IVT SP-CVT1 6.87 |
| **2022 CN7** | 2.0 Smartstream + 1.6T (Smartstream N-Line) | 4.54 / **5.07** | 0W-20 | 7.82 · 1.6T 7.19 | IVT SP-CVT1; 1.6T 7-DCT 1.7-1.8 |

Common: **EPS** (no PS fluid) · brake DOT 3/4 (AD) → DOT 4 (CN7) · **lug 79–94 ft-lb** · fuel **14.0 gal (AD) / 12.4 gal (CN7)** (compact) · tire **205/55R16** (215/40R18 Sport/N-Line) · battery AD **gated** (OM→label) / CN7 **AGM70L**. Plug PN **gated** (modern OM interval-only — gate transferred from Sonata).

**★ The twin thesis confirmed across compact-vs-sedan (controlled experiment over a body-class boundary):**
- **Engine-decided MATCH:** 1.6T Smartstream oil **5.07 = Sonata DN8 5.07**; 1.6T Gamma oil **4.76 ≈ Sonata LF 4.75** (⚠ visc diverges: 5W-30 Elantra vs 5W-20 Sonata — as-stated).
- **Body-decided DIVERGE:** fuel 14.0/12.4 (vs Sonata 15.9/18.5); tire 205/55R16 (vs 205/65R16); coolant Elantra-specific. Same engine, different body → oil/plug match, cooling/fuel/tire move.

**★ Per-year catches:** base 2.0 **Nu 4.23/5W-20 (AD) → Smartstream 4.54/0W-20 (CN7)**, coolant 6.34/6.97→7.82 (engine change across the AD→CN7 boundary — read across); 1.6T **Gamma→Smartstream** badge-but-different (4.76/5W-30→5.07/0W-20); trans **6AT SP-IV → IVT SP-CVT1 + 7-DCT**.
**★ Coolant-basis gate DISCRIMINATED** — cleared Elantra's consistent total-system values (6.34–7.82, written) as readily as it gated Sonata 2021's anomaly. New families on record: **Nu 2.0 MPI, Smartstream 2.0 MPI.**

### DEFERRED (9, each with reason)
- **2000–2004 (5)** — pre-2005 archive floor (XD/RD gen), aggregators-only.
- **2018** — full sedan OM not on portal (only Multimedia manual + the `elantra-gt` variant, a different body). **2024** — only an Abridged Manual on portal (no Capacities section).
- **2025, 2026** — full OM not yet published. **2026 remains the blacklisted `scraped` value — gated, never shipped.**
- **⚠ Separate-OM engines (known gap):** 1.4T Kappa Eco, 1.6T Sport (2017), 2.0T Elantra N (2022) — own OMs not on the base portal path → engine-specifics gated, not guessed. Future targeted pull (esp. the N 2.0T).

---

## ✅ SONATA — pilot 5/14 (2005/06 NF + 2018 LF + 2021 DN8 + 2024 DN8-FL) — `2026-07-01-hyundai-sonata`, commit 1da532c0 — FIRST HYUNDAI
Fresh make, recon-first. Multi-engine per row (turbos/N-Line = trims within the year's row). HEV = gated variant (own OM slug `sonata-hybrid`).

| Row | Engines | Oil (drain+filter) | Visc | Coolant | Trans |
|---|---|---|---|---|---|
| **2005/06 NF** | 2.4 Theta I4 + 3.3 Lambda V6 | **4.54** / **6.02** | 5W-20 | 6.66(AT) / 8.66 | ATF SP-III 8.24 / 11.52; MT MTF 75W/85 2.0 |
| **2018 LF** | 2.4 GDI + 2.0T (Theta II) + 1.6T (Gamma) | 5.07 / 5.07 / **4.75** | 5W-20 | 7.60 / 7.92 / 7.50 | 6AT SP-IV 7.5; 1.6T=7-DCT (GL-4 70W 2.0) |
| **2021 DN8** | 2.5 GDI + 1.6T (Smartstream) | **5.49** / 5.07 | 0W-20 | **GATED** (suspect basis) | 8AT SP-IV 6.89 |
| **2024 DN8-FL** | 2.5 GDI + 2.5T N-Line (Smartstream) | **6.13** / 6.13 | 0W-20 / **0W-30** (T-GDI) | 9.2 / 9.3 | 8AT SP4-M1 6.8; 2.5T=8-wet-DCT (gear 3.5+ctrl 2.6) |

Common: **PS hydraulic (NF, PSF-3 0.95qt) → EPS (LF/DN8, no PS fluid)** · brake DOT 3/4 (NF/LF) → DOT 4 (DN8) · **lug 79–94 ft-lb** (modern; NF gated) · fuel NF 17.7 / LF 18.5 / DN8 15.85–15.9 gal.
Plugs: **NF publishes** — 2.4 Theta **SK16PR-A11**, 3.3 Lambda **IFR5G-11**, gap **0.039–0.043** (written). **Modern gated** (OM interval-only). Battery: NF **MF68AH**, 2024 **AGM70L** (2018/2021 → OM refers to label, gated).

**★ Engine-family characterization (the Optima/K5 carry — read fresh, on record now):**
- **Theta II 2.4 GDI** 5.07 qt / 5W-20 · **2.0 T-GDI** 5.07 / 5W-20 · **Gamma 1.6 T-GDI** (LF) 4.75 / 5W-20 · **Smartstream 2.5** 0W-20 (oil 5.49→6.13 across facelift) · **Smartstream 1.6T** 5.07 / 0W-20 · **Lambda 3.3 V6** 6.02 / 5W-20 / IFR5G-11.

**★ Four make-level catches (banked to source map):**
1. **2005 = NF gen, not EF** — the portal's "2005" file (cover-confirmed 2005) carries the NF roster (2.4 Theta 2359cc + 3.3 Lambda 3342cc); the NF launched US mid-2005. **Hyundai filename year = badged MY; confirm gen by displacement/gen-code, never assume the calendar boundary.** (Caught by displacement + gen-code + cover + gov cross-check before any value rode onto the row.)
2. **Coolant-basis inconsistent across OM eras** — 2018 (2.4=7.60) & 2024 (2.5=9.2) are total-system; 2021 (2.5=5.49) is anomalously low (same Smartstream 2.5 as 2024, no cooling redesign) → refill/partial basis. **Gated 2021 coolant capacity** (type written). Sanity-check coolant vs the same engine in adjacent OMs; gate anomalously-low.
3. **Plug PN: NF-era publishes PN+gap; modern OMs publish replacement-interval only → gate modern PN.** Same old-publishes/modern-gates pattern as Subaru's spark gap. **The Optima/K5 modern rows hit the same gate — no re-derivation needed.**
4. **Facelift moved a capacity** — 2.5 GDI oil 5.49 (2021) → 6.13 (2024): read each refresh year, don't carry. Also: **1.6T is badge-but-different-engine** (Gamma LF 4.75 → Smartstream DN8 5.07), and the 1.6T dropped at the 2024 facelift.

### DEFERRED (9, each with reason)
- **2000–2004 EF gen (5 rows: 2.4 + 2.7 V6)** — not on the official portal (Sonata archive floor ≈ 2005); only non-citable aggregators (dealereprocess/carmanuals2/manualslib). Revisit if an official EF OM surfaces.
- **2019, 2020 (2 rows)** — portal has 2018 + 2021 full gas OMs but only QRG/Hybrid for 2019/2020; full gas OM only on aggregators (bounded form + web-search hunt exhausted). Not read off 2018/2021.
- **2025, 2026 (2 rows)** — full OM not yet published on the portal (as of mid-2026). **2026 remains the blacklisted `scraped` value — gated, never shipped.** Revisit when the OM posts.

---
*Page citations are OM printed-page numbers. Old OMs (NF 2005/06) are text-extractable; the capacities live in a Lubrication Chart (spec chapter). Modern OMs (LF/DN8) have a "Recommended Lubricants and Capacities" table (some fields image-rendered). Source = MyHyundai glovebox-manual, free + citable; provenance = filename + gen-code confirmation.*
