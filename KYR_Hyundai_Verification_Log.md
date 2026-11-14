# KYR — Hyundai Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified · FIRST Hyundai Motor Group make

Parallel to the GM-group / Ford / Honda / Nissan / Mazda / Subaru logs. Make characterization + reusable
source pattern in `KYR_OEM_Manual_Source_Map.md` (Hyundai section). **Host:** `owners.hyundaiusa.com` MyHyundai
glovebox-manual (free, no auth, citable manufacturer source). **This is the HMG foundation — it pre-characterizes
Kia (~80 rows / 12 nameplates), and specifically Optima/K5 as a near-twin of the Sonata (shared platform + Theta II/Smartstream engines).**

> **Hyundai status (2026-11-14, after the Santa Fe deploy): 28 rows.** **Sonata 4/14** · **Elantra ✅ 4/13** · **Tucson ✅ 6/10** · **Kona ✅ 5/5** · **Santa Fe ✅ 9/13** (2005/2006 SM + 2018 three-row NC + 2019/2020 TM + 2021/2023 TM facelift + 2025/2026 MX5; 2001–2004 deferred). Two manufacturer hosts are in use (US portal = first print, `ownersmanual.hyundai.com` = later print); values the prints contradict, values a book contradicts internally, and capacities whose units do not convert are not written. DB also has Palisade 6, Accent, Tiburon, Venue, Veloster, Ioniq (EV) — pending. **Kia does NOT cheaply unlock** (source boundary — full OMs behind a JS viewer; queued viewer-spike). **Next Hyundai:** Palisade (LX2 2021–2025 and LX3 2026+ on the second host; Lambda 3.8 V6 read fresh), then the newest deferred years the second host serves (Tucson 2025/2026, Elantra 2024–2026, Sonata 2025/2026).

## ✅ SANTA FE — 9/13 (2005/2006 SM + 2018 NC + 2019/2020 TM + 2021/2023 TM facelift + 2025/2026 MX5) — `2026-11-14-hyundai-santa-fe`, commit b864f51f — FIFTH HYUNDAI
Recon, reads, write and deploy all 2026-11-14 (live blob data.e6b921b0.js md5 e6b921b0… byte-identical to the commit; _verify_shipped.py PASS 58; CI green; README count copy 295→304). Write script `_write_hyundai_santa_fe.py` (dry-run default; asserts each target id's year/make/model; quart/litre check on every shipped pair). Backup `wrench_vehicles.db.bak_santafe_20261114_114254`. Four generations, each read from its own books; Hybrid and Plug-in Hybrid have their own manuals and are not written.

**Identity rulings (2026-11-14):** (1) **2019** is written from the second host's file labelled 2018 — the earliest TM-generation book, Copyright 2018, engines matching EPA's 2019 Santa Fe; the portal's 2019 file is the three-row body (sold that year as the Santa Fe XL). (2) **2018** is the three-row 3.3 V6 vehicle (the manual titled "2018 Hyundai Santa Fe", and what EPA calls Santa Fe that year); the two-row Sport has a separate manual and no DB row. (3) **2005/2006** are V6-only: EPA lists a 2.4 I4 that neither book carries.

| Row | Engines | Oil (drain+filter) | Visc | Coolant | Trans |
|---|---|---|---|---|---|
| **2005 SM** (id 11155) | 2.7 V6 + 3.5 V6 | **4.76** / **4.54** | 5W-30; 10W-30 above 0 °F (first grade misprinted, not written) | 7.4 / 8.66 | ATF SP-III 8.98 |
| **2006 SM** (id 11225) | same | 4.76 / 4.54 | 5W-20 or 5W-30; 10W-30 above 0 °F | 7.4 / 8.66 | ATF SP-III 8.98 |
| **2018 NC three-row** (id 12522) | Lambda 3.3 V6 | **6.02** | 5W-30 | 9.6 | ATF SP-IV 8.24 |
| **2019 TM** (id 12673) | 2.4 GDI + 2.0 T-GDI | **5.07** / 5.07 | 5W-20 / 5W-30 | 8.3 (8.6 trailer pkg) / 7.9 | ATF SP-IV 6.86 (2.4); 2.0T capacity not written |
| **2020 TM** (id 12781) | same | 5.07 / 5.07 | 5W-20 / 5W-30 | same | same |
| **2021 TM facelift** (id 12851) | Smartstream G2.5 GDI + G2.5 T-GDI | **6.13** both | 0W-20 (GDI); T-GDI not written | 7.5 / 8.17 | ATF SP-IV 6.87; T-GDI dual clutch 3.49–3.59 + 2.59–2.64 |
| **2023 TM facelift** (id 12981) | same | 6.13 both | 0W-20 / 0W-30 | 7.5 / 8.17 | 6.87, fluid type not written; dual clutch 3.4–3.6 + 2.58–2.64 |
| **2025 MX5** (id 13113) | Smartstream G2.5 T-GDi | 6.13 | 0W-30 full synthetic | **9.65** | wet dual clutch 3.49–3.6 + 2.59–2.64 |
| **2026 MX5** (id 13179) | same | 6.13 | 0W-30 full synthetic | 9.65 | **automatic, ATF SP4M-1 7.5** |

Common by generation: **SM** — hydraulic PS (PSF-3 0.95 / 1.06 qt), brake DOT 3 / DOT 4, transfer case + rear axle GL-5 80W/90 (0.85 / 1.16 qt), tire 225/70R16 @ 30, wheel nut **65–80 lb-ft**, fuel 19 gal; **plugs published: Champion RC10PYPB4 or NGK PFR5N-11, gap 0.039–0.043 in; battery MF 68 AH** (Electrical spec table) — all written. **NC** — EPS, DOT 3/4, GL-5 75W/90 rear 0.56 / transfer 0.72 qt, 235/60R18 · 235/55R19 @ 33, lug 79–94. **TM** — EPS, GL-5 75W/85 rear 0.61 qt (pre-facelift) / 0.56–0.67 (facelift), 235/65R17 · 235/60R18 · 235/55R19 @ 35 (pre) / 235/60R18 · 235/55R19 · 255/45R20 @ 35 (facelift), lug 79–94, fuel 18.75 gal (pre) / 17.7 gal (facelift; the 2021 first print gives it as 70.8 US qt / 67 L). **MX5** — MDPS, DOT-4, GL-5 75W/85 rear 0.56–0.67 / transfer 0.5–0.55 qt, 18-in @ 35 and 20/21-in @ 36 psi (PSI cells empty, note carries them), lug 79–94, fuel 17.7 gal.

**Not written, and why (reasons live in the `source` suffix):**

| Row | Value | What the books say | Rule |
|---|---|---|---|
| 2023 | Automatic transmission fluid type | first print ATF SP-IV; both later prints ATF SP4M-1 | edition conflict — capacity only |
| 2020 | Brake fluid DOT-3 allowance | first print "DOT-3 or DOT-4"; later print "ISO 4925 DOT-4" | edition conflict — "DOT-4" written |
| 2021 | T-GDI oil viscosity | capacities table 0W-20 (cell spans both engines); viscosity chart 0W-30 | internal conflict |
| 2005 | First oil viscosity grade | printed "SAE 50W-20" | misprint |
| 2019, 2020 | 2.0 T-GDI transmission capacity | 7.09 qt beside 7.0 L | units do not convert |
| 2019, 2020 | Transfer case capacity | 0.44–0.49 qt beside 0.47–0.52 L | units do not convert |
| 2018 | Fuel tank | 18.95 gal beside 71 L | units do not convert |

Edition cross-checks: 2019 and 2020 books are text-identical on every page read; 2020 first print vs later print differ only in the brake-fluid line; 2021 first print vs later print (dated 2020-12-14) agree on every written value (they differ in a dual-clutch inspection interval); 2023 first print vs later prints agree on everything except the ATF type. 2005, 2006, 2018, 2019, 2025, 2026 have a single print.

**Gates (null):** plug PN/gap 2018+ (interval only) · 12V battery 2018–2020 (no spec) and 2021+ (label illustration, "may differ") · EPS/MDPS · Hybrid / Plug-in Hybrid.

**★ Carry outcomes (engine predicts, the OM decides):** Lambda 3.3 V6 **6.02 qt = Sonata NF's 3.3 Lambda 6.02** (thirteen model years apart) · Theta 2.4 GDI and 2.0 T-GDI both **5.07 = Sonata LF 5.07** · Smartstream 2.5 **6.13 = Tucson NX4 and Sonata facelift 6.13** · the same 2.5T keeps 6.13 qt and 0W-30 across TM and MX5 while coolant moves 8.17 → 9.65 qt with the body. **Transmission is not carried by the engine:** the 2.5T has a wet dual clutch in 2021–2025 and a conventional automatic in 2026.

**OM normal-schedule intervals written (71 rows; mi / mo):** 2005, 2006 (6 each; p.5-4/5-5) — oil 7,500 / 6, plugs 60,000 / 48, air cleaner 30,000 / 24, A/C filter 10,000 / 12, coolant 30,000 / 24, **timing belt 60,000 / 48** (fuel filter 52,500 / 42 and the single ATF change at 105,000 / 84 are in the book but not written). 2018 (6; list-style schedule p.7-9..7-23) — oil 7,500 / 12, plugs 100,000 / 10 years, air cleaner 30,000 / 24, climate filter 15,000 / 12, rotation 7,500 / 6, coolant first 120,000 mi or 60 months (as printed) then 30,000 / 24. 2019, 2020 (11 each; p.7-8, 7-13) — oil 7,500 / 12 (2.0T 6,000 / 12), plugs 97,500 (42,000), air cleaner 30,000 / 48 (24,000 / 48), climate filter 15,000 / 12 (12,000 / 12), rotation 7,500 (6,000), coolant 120,000 / 120 then 30,000 / 24. 2021 (9; p.9-8..9-11) — oil 8,000 / 12, plugs GDI 96,000 / T-GDI 48,000, air cleaner 24,000 / 36, climate filter 16,000 / 24, coolant GDI 120,000 / 120 then 30,000 / 24 and T-GDI 80,000 / 10 years then 24,000 / 24, brake fluid GDI 60,000 / 48 and T-GDI 48,000 / 48. 2023 (8) — oil 8,000 / 12, plugs 96,000 / 48,000, air cleaner 24,000 / 36, cabin filter 16,000 / 24, rotation 8,000 / 12, coolant 120,000 / 120 then 24,000 / 24, brake fluid 48,000 / 48. 2025, 2026 (7 each) — oil 8,000 / 12, plugs 48,000, air cleaner 24,000 / 36, cabin filter 16,000 / 24, rotation 8,000 / 12, coolant 120,000 / 120 then 24,000 / 24, brake fluid 48,000 / 48.

### DEFERRED (4, each with reason)
- **2001–2004 (ids 10988, 11014, 11049, 11097)** — no manufacturer manual on either host (portal sweep 2001–2007 found only 2005 and 2006; the second host starts at 2018).
- **⚠ Separate-manual variants (known gap):** Santa Fe Hybrid (TMaHEV / MX5aHEV), Plug-in Hybrid (TMPHEV), and the 2018 two-row Santa Fe Sport — not written, not guessed.

---

## ⚠ AUDIT 2026-11-14 — live-row corrections (commit e8b42251, `2026-11-14-hyundai-kona`)
The 15 Hyundai rows live before the Kona slice were checked against the later manual prints and against their own cited books (read-only audit, then corrections approved the same day; script `_fix_hyundai_audit_2026_11_14.py`, backup `wrench_vehicles.db.bak_hyundai_audit_20261114_104836`).

| Finding | Row | Correction |
|---|---|---|
| **Wrong vehicle** — the 2005 NF manual's values were written to id 35202, which is the model-year-2000 Sonata (EF generation). `_write_hyundai_sonata.py` addressed it as "2005". Live with a verified flag from 2026-07-01. | Sonata id 35202 | All curated rows removed; the 2000 Sonata is unverified again. The real 2005 row (id 11156) stays deferred: government data gives 2005 the EF roster (2.4 / 2.7 V6), which the NF "2005" manual (2.4 Theta / 3.3 Lambda) does not match. |
| **Edition conflict** — 2.5 GDi oil capacity 5.49 qt / 5.2 L in the first print (p.2-11, Copyright 2020), 6.13 qt / 5.8 L in the later print. | Sonata 2021 id 12853 | 2.5 figure removed; 1.6T 5.07 qt / 4.8 L (identical in both prints) stays. The old "facelift moved 5.49 → 6.13" note below was really a print revision. |
| **Not in the book** — tire size 205/65R16 is the 2021 book's base size; the 2024 book (both prints) lists 215/55R17, 235/45R18, 245/40R19 at 35 psi (p.2-13). | Sonata 2024 id 13049 | Tire sizes and 35 / 35 psi written from p.2-13. |
| **Example label** — battery group AGM70L came from the "Battery Capacity Label" page, an illustration marked Example / "may differ from the illustration". | Elantra 2021 id 2163, Elantra 2022 id 3691, Sonata 2024 id 13049 | Set to null (same gate as Tucson and Kona). |

Checked with no disagreement: Elantra 2021 / 2022 and Tucson 2022 / 2024 on every stored value (Tucson including the schedule intervals); all 109 stored quart/litre pairs convert correctly. No later print exists for Sonata 2006 / 2018, Elantra 2017 / 2020, Tucson 2018 / 2020 / 2021 (platform codes NF, LF, AD, TL are not served) and Tucson 2023 (only an abridged manual there). A fleet-wide scan found no other cross-generation address. The Sonata and Elantra write scripts now refuse to re-run. Noted, not changed: Sonata 2024 wet-DCT quantities are stored as 3.5 / 2.6 qt where the book prints ranges 3.49–3.59 / 2.59–2.64 qt.

---

## ✅ KONA — 5/5 (2020/2021 OS + 2022 OS facelift + 2024/2026 SX2) — `2026-11-14-hyundai-kona`, commit e8b42251 — FOURTH HYUNDAI, second SUV
Recon, reads, write and deploy all 2026-11-14 (live blob data.eb3fc46c.js md5 eb3fc46c… byte-identical to the commit; _verify_shipped.py PASS 58; CI green; README count copy 291→295). Write script `_write_hyundai_kona.py` (dry-run default; asserts each target id's year/make/model and runs a quart/litre conversion check on every shipped pair). Backups `wrench_vehicles.db.bak_kona_20261114_100859` and `_104836`. Self-ID per book by engine table + wheelbase. Kona N and Kona Electric have their own books and are not in these rows. The DB has no Kona rows for 2018, 2019, 2023 or 2025 (the books exist).

**Sources.** 2020, 2021, 2022: US portal first prints (`2020 Kona Owner's Manual.pdf`, `2021_Kona_Owners_Manual.pdf`, `2022-Kona-Owners-Manual.pdf`), each cross-checked page by page against the later print. 2024, 2026: `ownersmanual.hyundai.com/full_pdf/SX2/<MY>/en_US` (Copyright 2023 / 2026 HYUNDAI Motor America; no portal copy exists). **Ruling 2026-11-14:** that host is an accepted verified manufacturer source; the 2026 row was written under D1 (blacklisted by source, not by year) and is the first verified 2026 row read from a 2026 book.

| Row | Engines | Oil (drain+filter) | Visc | Coolant | Trans |
|---|---|---|---|---|---|
| **2020 OS** (id 673) | Nu 2.0 MPI + Gamma 1.6 T-GDI | **4.23** / **4.76** | 5W-20 / 5W-30 | 6.8 / 7.5 | AT SP-IV 7.08; 1.6T DCT GL-4 70W 2.01–2.11 |
| **2021 OS** (id 2166) | same pair | 4.23 / *not written* | 5W-20 / 5W-30 | 6.8 / 7.5 | as 2020 |
| **2022 OS facelift** (id 3694) | Smartstream G2.0 Atkinson + G1.6 T-GDi | **4.5** / **5.1** | 0W-20 full synthetic | 6.3 / 7.3 | IVT SP-CVT1 7.1; 1.6T DCT GL-4 70W 1.7–1.8 |
| **2024 SX2** (id 6787) | same Smartstream pair | 4.5 / 5.1 | 0W-20 full synthetic | 7.3 / **9.0** | 1.6T AT SP4M-1 6.8; IVT SP-CVT1 *capacity not written* |
| **2026 SX2** (id 9976) | same Smartstream pair | 4.5 / 5.1 | 0W-20 full synthetic | 7.3 / 9.0 | as 2024 |

Common: **EPS** (OS) / **MDPS** (SX2), no PS fluid · brake **DOT-4 LV** (OS; 0.74–0.85 qt on 2020/21) → **DOT-4** (SX2) · AWD gear oil GL-5 75W/90 (2020/21; 2022 rear) and 75W/85 (2022 transfer, SX2) · **lug 79–94 lb-ft** every book · fuel **13.2 gal** (SX2 2.0: 12.4 gal) · tires **205/60R16 · 215/55R17 · 235/45R18 @ 33/33** (OS) / **215/60R17 @ 36, 215/55R18 and 235/45R19 @ 33** (SX2; pressures vary by size, so the PSI cells are empty and the note carries them) · spare T125/80D16 (OS) / T145/90D16 (SX2) @ 60.

**★ Two null rules (ruling 2026-11-14) — reasons live in the `source` suffix, never in shipped columns:**
1. **Edition conflict → not written.** First print vs later print of the same model-year manual:

| MY | Value | First print (portal) | Later print | Written |
|---|---|---|---|---|
| 2020 | Brake-fluid replacement | inspect only | 60,000 mi / 48 mo (1.6T 48,000) | no row |
| 2021 | 1.6T oil capacity | 4.76 qt / 4.5 L | 4.23 qt / 4.0 L | 2.0 figure only |
| 2022 | 1.6T spark plugs | 47,000 mi | 48,000 mi | 2.0 row only (96,000) |
| 2022 | Cabin filter | 16,000 mi or 12 mo | 16,000 mi / 24 mo | 16,000 mi, no months |
| 2022 | Coolant repeat | 30,000 mi / 24 mo | 24,000 mi / 24 mo | first replacement only |
| 2022 | Tire rotation | 8,000 mi | 8,000 mi or 12 mo | 8,000 mi, no months |

2. **Quart/litre conflict → capacity not written, fluid specification only.** 2020/2021 transfer case and rear differential (0.44–0.49 qt printed beside 0.47–0.52 L; 0.36–0.4 qt beside 0.38–0.42 L); 2022 brake-fluid capacity (0.5–0.6 qt beside 0.7–0.8 L); 2024/2026 IVT (6.9 qt beside 6.7 L; 7.1 qt beside 6.9 L), rear differential (0.6–0.7 qt beside 0.4–0.5 L), transfer case (0.8–0.9 qt beside 0.62–0.68 L). The 2022 book prints the same transfer/differential litres as 2020/21 with quarts that do convert, which is why those 2022 capacities are written.

**Gates (null):** plug PN/gap (interval only, every book) · 12V battery (2020/21 carry no 12V spec; 2022 p.9-30 and SX2 p.655 / p.685 show only an example capacity label) · `battery_notes` NULL.

**★ Carry outcomes (engine predicts, the OM decides):** Nu 2.0 MPI **4.23 / 5W-20** = Elantra AD · Gamma 1.6T **4.76 / 5W-30** = Elantra 2020 and Tucson 2018 · Smartstream 2.0 **4.5** and 1.6T **5.1** = Elantra CN7's 4.54 / 5.07 at one-decimal print · body-decided fields moved as expected: coolant 6.8 / 7.5 (OS Nu / Gamma; the Gamma figure equals the Tucson TL's 7.5), 6.3 / 7.3 (facelift), 7.3 / 9.0 (SX2); fuel 13.2 gal against Tucson's 16.38 / 14.27. The SX2 1.6T swapped the 7-speed DCT for an 8-speed automatic (ATF SP4M-1).

**OM normal-schedule intervals written (47 rows):** 2020 (11) — oil & filter 7,500 / 12 (Gamma 6,000 / 12), plugs 97,500 (Gamma 42,000), air cleaner 30,000 / 48 (Gamma 24,000 / 48), climate filter 15,000 / 12 (Gamma 12,000 / 12), rotation 7,500 (Gamma 6,000), coolant 120,000 / 120 then 30,000 / 24 (p.7-8, 7-13). 2021 (13) — the same plus brake fluid 60,000 / 48 (Gamma 48,000 / 48; p.7-10, 7-15). 2022 (7) — oil 8,000 / 12, plugs 2.0 96,000, air cleaner 24,000 / 36, cabin filter 16,000, rotation 8,000, coolant first 120,000 / 120, brake fluid 48,000 / 48 (p.9-8 to 9-10). 2024 and 2026 (8 each) — oil 8,000 / 12, plugs 48,000 (1.6T) and 96,000 (2.0), air cleaner 24,000 / 36, cabin filter 16,000 / 24, rotation 8,000 / 12, coolant 120,000 / 120 then 24,000 / 24, brake fluid 48,000 / 48 (2024 p.625–629; 2026 p.654–657).

**★ Source/format notes (banked to source map):** OS first prints extract as text (bullets come out as `(cid:129)`); the 2022 facelift book's schedule tables are rotated, so the text comes out reversed and the pages were rendered and read as images; SX2 books are flat text. Later prints carry extra pages, so page indexes shift (506 vs 505 pp for 2020; 596 vs 579 for 2022) while printed page numbers stay usable.

---

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
> **⚠ Corrected 2026-11-14 (audit, commit e8b42251):** battery group AGM70L on the 2021 and 2022 rows came from an example label illustration and is now null. Every other 2021 / 2022 value matches the later print (`ownersmanual.hyundai.com` CN7). The table below is the original read.

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
> **⚠ Corrected 2026-11-14 (audit, commit e8b42251) — Sonata is 4/14, not 5/14:** (1) the "2005 NF" values had been written to id 35202, the model-year-2000 car, and were removed; only 2006 (id 11226) carries the NF read. (2) 2021: the 2.5 oil figure 5.49 below is the first print's; the later print says 6.13, so it is no longer shipped. (3) 2024: tire size is 215/55R17, 235/45R18 or 245/40R19 at 35 psi, not 205/65R16. (4) 2024: battery AGM70L came from an example label and is now null. The text below is the original read, kept for the record.

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
