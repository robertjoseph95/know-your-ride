# KYR — Hyundai Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified · FIRST Hyundai Motor Group make

Parallel to the GM-group / Ford / Honda / Nissan / Mazda / Subaru logs. Make characterization + reusable
source pattern in `KYR_OEM_Manual_Source_Map.md` (Hyundai section). **Host:** `owners.hyundaiusa.com` MyHyundai
glovebox-manual (free, no auth, citable manufacturer source). **This is the HMG foundation — it pre-characterizes
Kia (~80 rows / 12 nameplates), and specifically Optima/K5 as a near-twin of the Sonata (shared platform + Theta II/Smartstream engines).**

> **Hyundai status (2026-11-14, after the Santa Cruz 2022 / 2023 / 2024 / 2025 slice): 60 rows, all at the current standard.** **Sonata 6/14** · **Elantra ✅ 7/13** · **Tucson ✅ 8/10** · **Kona ✅ 9/9** · **Santa Fe ✅ 9/13** · **Palisade ✅ 7/7** · **Venue ✅ 7/7** · **Veloster ✅ 2/3 (2020 deferred)** · **Santa Cruz ✅ 5/5** · **Accent 0/19 verified (1995–2002: 8 rows deferred, no manufacturer manual before 2005; 2005, 2006, 2008, 2014 and 2016–2022: 11 rows added 2026-11-14 with government data only, curated specs still to read)**. Two manufacturer hosts are in use (US portal = first print, `ownersmanual.hyundai.com` = later print); the second host also carries plant-specific books (a bare code and the same code + `a`). Values two prints contradict, values a book contradicts internally, and capacities whose units do not convert are not written; a maintenance row whose interval two prints dispute is left out whole; a value two plant books give differently ships with both figures, unattributed; an engine only a later print carries is written from that print. **⚠ Label audit 2026-11-14: a second-host year label is NOT automatically the model year — three labels hold the next year's book and four are unproved; see the LABEL AUDIT section. Row corrections deployed as `2026-11-14-hyundai-label-audit`; the Kona 2022 / Elantra 2022 intervals lost to false print conflicts were restored as `2026-11-14-hyundai-restore-2022`.** DB also has Tiburon (1997–2002, not probed; the portal floor has been 2005 for every nameplate checked) and Ioniq (EV) — pending. **Kia does NOT cheaply unlock** (source boundary — full OMs behind a JS viewer; queued viewer-spike). **Next Hyundai:** the curated specs for the eleven Accent rows added 2026-11-14, in three slices by generation. The missing-year rows for Venue, Palisade, Kona and Santa Cruz are added and verified.

## ➕ ACCENT 2005–2022 — ELEVEN MISSING MODEL-YEAR ROWS ADDED (government data only) — `2026-11-14-hyundai-accent-rows`, commit dcc288f3 — MISSING-YEAR STEP A
**What this is:** eleven Accent model-year rows the fleet lacked (ids 38731–38741), with EPA fuel economy and NHTSA recalls, safety ratings and complaints, and **no curated specification yet**. Fleet 3,680 → 3,691; tally stays 336 / 42 / 11 (Hyundai 60 verified rows). Script `_add_hyundai_rows.py accent-missing-years` (dry run, then the approved plan by hash); backup `wrench_vehicles.db.bak_rows_accent_missing_years_20261114_212035`. **LIVE CONFIRMED 2026-11-14 21:26:05** (version string served; the live data file `data.97fd0a58.js` has the same md5 as the local one; CI green).

**Book basis per year (rulings, Robert 2026-11-14, "Accept, start dry run").** All eleven are US-portal files in folder `accent`, single prints; the second host serves no Accent (no US listing; codes HC, HCa, RB, RBa, MC, LC all answer HTTP 500 while a known file answers 200).

| Year | id | File | How it names its year | Copyright / pages | Engine table |
|---|---|---|---|---|---|
| 2005 | 38731 | `2005_Hyundai_Accent_OM.pdf` | cover "2005 Owner's Manual" + Accent | 2005 / 219 | 1.6 MPI, 1,599 cc, "4-Cylinder in-line DOHC" (p.9-3) |
| 2006 | 38732 | `2006_Hyundai_Accent_OM.pdf` | cover "2006 Owner's Manual" + ACCENT | 2006 / 278 | the same (p.9-3) |
| 2008 | 38733 | `2008_Hyundai_Accent_OM.pdf` | cover "2008 Owner's Manual" + ACCENT | 2008 / 273 | the same (p.9-3) |
| 2014 | 38734 | `2014-Accent-Owners-Manual.pdf` | PDF title "2014 Accent Owners Manual" | 2013 / 406 | Gasoline 1.6, 97.09 cu.in (1591 cc), "4, In-line" (p.8-2) |
| 2016 | 38735 | `2016_Hyundai_Accent_OM.pdf` | PDF title "2016 Hyundai Accent Owner's Manual" | 2015 / 456 | the same (p.8-2) |
| 2017 | 38736 | `2017_Hyundai_Accent_OM.pdf` | PDF title "2017 Hyundai Accent Owner's Manual" | 2017 / 380 | the same (p.8-2) |
| 2018 | 38737 | `2018 Accent Owners Manual.pdf` | folder + file name only | 2018 / 442, created 2018-02-20 | Gamma 1.6 GDI, 1,591 cc, "In-line 4 cylinder" (p.8-2) |
| 2019 | 38738 | `2019 Accent OM.pdf` | folder + file name only | 2018 / 442, created 2018-08-01 | the same (p.8-2) |
| 2020 | 38739 | `2020 Accent Owner's Manual.pdf` | cover + PDF title "2020 Accent Owner's Manual" | 2019 / 445 | Smartstream G1.6, 97.52 cu.in (1,598 cc), "In-line 4 cylinder" (p.8-2) |
| 2021 | 38740 | `2021 Accent OM.pdf` | folder + file name only; proof marks "HCa HMA" 5/25/2020 | 2020 / 443 | the same (p.8-2) |
| 2022 | 38741 | `2022-Accent-OM.pdf` | folder + file name only | 2021 / 445, created 2021-07-06 | the same (p.8-2) |

The four files with no title naming the year were accepted on folder, file name, copyright and creation date (as for Kona 2018 / 2019). The 2018 and 2019 files share a copyright year but are separate editions: 21 pages differ and the 2019 file adds LED headlamp content. Wheelbase steps through the four generations (96.1 / 98.4 / 101.2 / 101.5 in); the 2018–2022 books show the sedan on the exterior overview p.1-2; the 2014–2017 books show an interior overview only.

**Years with a government listing and NO book — no row:** 2003, 2004, 2007, 2009, 2010, 2011, 2012, 2013, 2015. For each, 21 file-name forms under portal folder `accent` answered HTTP 404 (2007, 2009–2013 and 2015 re-asked 2026-11-14 in full mode; an older tool had tried them without reading the status). vPIC lists the Accent for 2003–2022 and not 2023.

**Government data written:**

| Year | EPA entries (city / hwy / comb) | Recalls | Safety | Complaints | Engine label |
|---|---|---|---|---|---|
| 2005 | 1.5 auto 23 / 32 / 26; 1.6 auto 23 / 32 / 26; 1.5 manual 24 / 33 / 28; 1.6 manual 25 / 30 / 27 | 1 | front passenger 4, side passenger 4; the rest empty | 49 | empty |
| 2006 | auto 25 / 33 / 28; manual 27 / 32 / 29 | 3 | no row | 43 | 1.6L I4 |
| 2008 | auto 24 / 33 / 28; manual 27 / 32 / 29 | 1 | no row | 101 | 1.6L I4 |
| 2014 | auto 26 / 36 / 30; manual 27 / 37 / 31 | 1 | overall 4, rollover 4, risk 12.4% | 80 | 1.6L I4 |
| 2016 | auto 26 / 36 / 30; manual 27 / 37 / 31 | none | overall 4, rollover 4, risk 12.4% | 103 | 1.6L I4 |
| 2017 | auto 26 / 36 / 30; manual 27 / 37 / 31 | none | overall 4, rollover 4, risk 12.4% | 68 | 1.6L I4 |
| 2018 | auto 28 / 38 / 32; manual 28 / 37 / 31 | 1 | listed, not rated — no row | 19 | 1.6L I4 |
| 2019 | auto 28 / 38 / 32; manual 28 / 37 / 31 | 1 | listed, not rated — no row | 31 | 1.6L I4 |
| 2020 | variable 33 / 41 / 36; manual 29 / 39 / 33 | 4 | overall 4, rollover 4, risk 11.3% | 12 | 1.6L I4 |
| 2021 | variable 33 / 41 / 36; manual 29 / 39 / 33 | 4 | overall 4, rollover 4, risk 11.3% | 16 | 1.6L I4 |
| 2022 | variable 33 / 41 / 36 | 2 | overall 4, rollover 4, risk 11.3% | 17 | 1.6L I4 |

**Rulings (Robert 2026-11-14, "Go, write"):**
- **EPA name and engines, 2005:** EPA lists the 2005 car as "Accent/Brio" — taken, it is EPA's only Accent entry that year. EPA lists a 1.5 L beside the 1.6 L; the 2005 book's engine table lists the 1.6 only. All four EPA entries are kept as listed and the engine label stays empty (standing label rule: every EPA engine must match the book's table).
- **A complaint filed against "ALL MODELS":** one 2014 complaint (ODI 11697541) is filed by NHTSA against every 2014 Hyundai and is returned for each model. Kept as returned, so the stored count equals NHTSA's count (80). The fleet already holds 360 complaint numbers on every fleet vehicle of one make and year. The script now accepts this shape and reports it; any other product mismatch still stops the run.
- **Safety ratings for one body style:** for 2006 and 2008 NHTSA rates the four-door and lists the two-door unrated. No figure is shared by both, so no rating is stored and the app says none is on file. For 2005 both bodies are rated and differ on the two driver figures; only the two shared figures are stored.
- NHTSA answers "no recalls" for 2016 and 2017 with its HTTP 400 count-0 body; the other years supply the positive control.

**Checks:** 132 requests; the build rehearsal passed on an in-memory copy before the write; the rebuilt data differs from the previous deployed data by the eleven new objects only; bare rows 424; verifier PASS 58. Totals: vehicles 11, fuel economy 23, recalls 18, safety ratings 7, complaints 539, pull-log lines 44.

**Open after this step:** step B, the curated specs for the eleven years, in three slices by generation — 2005 / 2006 / 2008, then 2014 / 2016 / 2017, then 2018–2022. Each is a single print, so there is no second print to compare. The 2005 book publishes a spark-plug type and gap and a battery rating (p.9-2 / 9-3), which the later books do not.

---

## ✅ SANTA CRUZ 2022 / 2023 / 2024 / 2025 — 4/4, Santa Cruz now 5/5 — `2026-11-14-hyundai-santa-cruz-2022-2025`, commit 6d3fddeb — FOURTEENTH HYUNDAI SLICE (missing-year step B)
**What this is:** the curated specs for the four rows added in step A (section below), each read from that year's own book. Tally **336 verified / 42 nameplates / 11 makes; Hyundai 60 rows.** Script `_write_hyundai_santa_cruz_2022_2025.py`; backup `wrench_vehicles.db.bak_santa_cruz_2022_2025_20261114_204742`. **LIVE CONFIRMED 2026-11-14 20:53:09** (version string served; the live data file `data.e83fc00a.js` has the same md5 as the local one; CI green).

**Books and prints** (identification and label findings are in the rows section below):

| Year | id | Primary book | Other files of the same year | Result |
|---|---|---|---|---|
| 2022 | 38727 | portal `2022-Santa-Cruz-Owners-Manual.pdf`, June 2021 | `NX4OB/2021`, December 2021 print | identical on every specification page; ONE schedule line differs |
| 2023 | 38728 | portal `2023-Santa Cruz-OM.pdf` | `NX4OB/2022` (same production file); `NX4OB/2023` (cross-check) | identical on every specification and schedule page |
| 2024 | 38729 | `NX4OB/2024` | `NX4OB/2023` (cross-check) | no written value contradicted (wording differs only) |
| 2025 | 38730 | `NX4OB/2025` | none | single print |

**⚠ EDITION CONFLICT — 2022 automatic-transmission-fluid schedule line (p.9-11):** the June 2021 print says "No check, No service required"; the December 2021 print says "Replace every 60,000 miles". Standing whole-row rule: **no row is written for 2022.**

**★ NEW ROW TYPE — transmission-fluid interval (ruling, Robert 2026-11-14, "Go, as recommended"):** the 2023 and 2024 normal schedules print "Automatic transmission fluid: Replace every 60,000 miles" (p.9-12) in every file. Written for those two years as `Automatic transmission fluid replacement`, 60,000 mi, no month figure. It is the first manual-cited transmission-fluid row in the fleet; earlier Hyundai books print "No check, No service required" there, and so does the 2025 Santa Cruz book (p.9-14) — no row for 2025.

**⚠ 2025 DUAL-CLUTCH BLOCK NOT WRITTEN (same ruling):** p.10-7 prints gear oil 2.53–2.64 US qt (2.45–2.50 L) and control oil 3.5–3.6 US qt (3.3–3.4 L) with one fluid name (GS WDCTF HD G) for both. The 2022–2024 books assign the two quantities the other way round (gear oil 3.3–3.4 L, control oil 2.45–2.50 L) and name two fluids (HD G, HD H). There is no second 2025 print. The 2025 dual-clutch fluid name and quantities are left empty; the automatic-transmission line and the transfer-case line (which names both transmissions) are written.

**Read log — the same in all four years:**

| Item | Value | Page (2022 / 2023, 2024 / 2025) |
|---|---|---|
| Engines | Smartstream G2.5 GDI and G2.5 T-GDI, 152.4 cu. in (2,497 cc), "4, in-line" | 2-8 / 2-8 / 10-2 |
| Oil quantity | 6.13 qt / 5.8 L, one cell for both engines | 2-12 / 2-12 / 10-7 |
| Oil grade (chart, page render) | 0W-20 (G2.5 GDI), 0W-30 (G2.5 T-GDI), one bar each | 2-13 / 2-13 / 10-9 |
| Oil specification | API SN PLUS/SP or ILSAC GF-6; full synthetic required (API SN PLUS or above) | 2-12, 2-13 / same / 10-7, 10-8 |
| Automatic transmission quantity | 6.87 qt / 6.5 L | 2-12 / 2-12 / 10-7 |
| Coolant type | mixture of antifreeze and water, ethylene glycol base, aluminum radiator | 2-12 / 2-12 / 10-7 |
| Brake fluid type | SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6 | 2-12 / 2-12 / 10-7 |
| Rear differential | hypoid gear oil API GL-5 SAE 75W/85, 0.56–0.67 qt / 0.53–0.63 L | 2-12 / 2-12 / 10-8 |
| Tires (table, page render) | 245/60R18, 245/50R20 at 35 psi all positions; compact spare T135/80D18 at 60 psi; wheel nut 79–94 lbf·ft | 2-10 / 2-10 / 10-4 |
| Fuel tank | 17.69 gal / 67 L | 2-12 / 2-12 / 10-8 |

**Read log — what changes by year:**

| Item | 2022 | 2023 and 2024 | 2025 |
|---|---|---|---|
| Automatic transmission fluid | ATF SP-IV (MICHANG, SK, NOCA, Hyundai genuine or other approved brands) | ATF SP4M-1 (SK, MICHANG, S-OIL, Hyundai genuine) | ATF SP4M-1 (SK, MICHANG, S-OIL; the book spells the Hyundai genuine brand "SP4-M1", not written) |
| Dual-clutch gear oil (G2.5 T-GDI) | GS WDCTF HD G (WDGO-1), 3.49–3.59 qt / 3.3–3.4 L | GS WDCTF HD G (GS Caltex), 3.4–3.6 qt / 3.3–3.4 L | not written (above) |
| Dual-clutch control oil | GS WDCTF HD H (WDHO-1), 2.59–2.64 qt / 2.45–2.50 L | GS WDCTF HD H (GS Caltex), 2.58–2.64 qt / 2.45–2.50 L | not written (above) |
| Coolant quantity, GDI / T-GDI | 10.00 qt / 9.46 L; 9.12 qt / 8.63 L | the same | 10 qt / 9.5 L; 9.09 qt / 8.6 L |
| Brake fluid quantity | "As required" — none | none | 0.87 qt / 0.82 L (printed ±0.02) |
| Transfer case | 0.66–0.72 qt / 0.62–0.68 L (GDI); 0.51–0.55 qt / 0.48–0.52 L (T-GDI) | the same | 0.65–0.71 qt / 0.62–0.68 L (automatic); 0.49–0.55 qt / 0.47–0.52 L (dual clutch) |
| Drive wording on the differential lines | AWD | AWD | 4WD |
| Compact spare | listed | listed | "if equipped" |
| Wheel nut in N·m | not printed (lbf·ft and kgf·m only) | 2023 not printed; 2024 prints 107–127 | 107–127 |

**Normal schedule, mi / mo** (rotated grids rendered upright for 2022–2024; upright grids for 2025, sparse rows rendered):

| Row | 2022 (p.9-8 to 9-11) | 2023, 2024 (p.9-9 to 9-12) | 2025 (p.9-11 to 9-15) |
|---|---|---|---|
| Engine oil and filter | 8,000 / 12 | 8,000 / 12 | 8,000 / 12 |
| Air cleaner filter | 24,000 / 36 | 24,000 / 36 | 24,000 / 36 |
| Spark plugs, G2.5 T-GDI | 48,000 / 72 | 48,000 / 72 | 48,000 / 72 |
| Spark plugs, G2.5 GDI | 96,000 | 96,000 | 96,000 |
| Coolant | first 120,000 / 120, then 24,000 / 24 | the same | the same |
| Brake fluid | 48,000 / 48 | 48,000 / 48 | 48,000 / 48 |
| Tire rotation | 8,000 / 12 (grid marks) | 8,000 / 12 (text) | 8,000 / 12 (text) |
| Cabin air filter | 16,000 / **12** (printed as text) | 16,000 / **24** (grid marks) | 16,000 / 24 (grid marks) |
| Automatic transmission fluid | prints disagree — no row | **60,000** | "No check, No service required" — no row |
| Rows written | 8 | 9 | 8 |

**Gates:** spark-plug part number and gap are published by none of the books; 12V battery — each book shows only an example capacity label (MF68L-DIN p.9-32 / 9-33; MF68R-DIN in 2025); brake-fluid quantity 2022–2024; electric power steering has no fluid. Wheel-nut N·m is left empty for 2022 and 2023 because those books do not print it (precedent: Santa Fe 2005 / 2006, Sonata 2006).

**Checks:** dry run 4 vehicles / 34 schedule rows / 61 unit pairs converted (a ratio test was added for quantities under one quart; the gallon tolerance follows both printed precisions, so 17.69 gal beside 67 L passes); per-year guards in the script (schedule line counts, the transmission-fluid row only on 2023 / 2024, cabin-filter months, SP-IV only on 2022, no dual-clutch text on 2025, 4WD wording on 2025, N·m only where printed); a guard keeps the left-out 2025 figures and the misspelt brand out of shipped columns; government rows untouched; bare rows 424; the rebuilt data differs from the previous deployed data in exactly these four objects; verifier PASS 58.

---

## ➕ SANTA CRUZ 2022 / 2023 / 2024 / 2025 — FOUR MISSING MODEL-YEAR ROWS ADDED (government data only) — `2026-11-14-hyundai-santa-cruz-rows`, commit 0f7bf88e — MISSING-YEAR STEP A
**What this is:** four Santa Cruz model-year rows the fleet lacked (ids 38727–38730), with EPA fuel economy and NHTSA recalls, safety ratings and complaints, and **no curated specification yet**. Fleet 3,676 → 3,680; tally stays 332 / 42 / 11 (Hyundai 56 verified rows). Script `_add_hyundai_rows.py santa-cruz-missing-years` (dry run, then the approved plan by hash); backup `wrench_vehicles.db.bak_rows_santa_cruz_missing_years_20261114_200645`. **LIVE CONFIRMED 2026-11-14 20:21:20** (version string served; the live data file `data.6fe6f7bf.js` has the same md5 as the local one).

**Every Santa Cruz file on the two manufacturer hosts, and what it holds:**

| File | Copyright | Pages | Finding |
|---|---|---|---|
| portal `2022-Santa-Cruz-Owners-Manual.pdf` | 2021 | 598 | PDF title "2022 Santa Cruz Owners Manual", created 2021-06-08 — **model year 2022** |
| second host `NX4OB/2021` | 2021 | 596 | proof marks dated 2021-12-23: a December 2021 print of the 2022 book. vPIC and EPA list no 2021 Santa Cruz — **model year 2022** |
| portal `2023-Santa Cruz-OM.pdf` (slug `santa-cruz`) | 2022 | 620 | portal folder 2023, created 2022-11-17 — **model year 2023**. Found 2026-11-14; the earlier note that the portal held only the 2022 book was wrong (2023 had not been asked) |
| second host `NX4OB/2022` | 2022 | 620 | carries the SAME proof marks as the portal 2023 book (`003_NX4(OB)_HMA.indd 3-1 2022-11-01 10:43:43`); 6 trivial pages differ — **model year 2023**, label shifted by one |
| second host `NX4OB/2023` | 2023 | 621 | the 2023 book with 17 changed pages (copyright year, tire date-code example 1523, digital key card notes, snow notes, a towing page). **UNASSIGNED:** a later 2023 print or an early 2024 print |
| second host `NX4OB/2024` | 2023 | 620 | 324 pages differ from `NX4OB/2023` (new "Vehicle handling instructions" section, an engine-oil additives notice, ignition-switch wording, LED bulb table, a vacuum-hose inspection line) — **model year 2024, SUPPORTED** (below) |
| second host `NX4OB/2025` | 2024 | 575 | facelift body, header `_NX4aOB_en_US`, created 2024-10-17, gives a separate XRT length — **model year 2025** |
| second host `NX4OB/2026` | 2026 | 567 | model year 2026 (existing row id 9981) |
| portal 2024 and 2025; second host `NX4OB/2027` | — | — | portal: 168 file-name forms per year, all HTTP 404; `NX4OB/2027`: HTTP 500 |

**Why `NX4OB/2024` is accepted as the 2024 book (ruling, Robert 2026-11-14, "Accept, start dry run"):** no titled 2024 book exists, so it cannot be proved against one. The support: (1) the manufacturer files it as 2024 and its 2023 copyright fits the first-print pattern; (2) it is not the 2023 book — it differs from the portal's 2023 book on 300+ pages; (3) its "Vehicle handling instructions" section appears in the 2024 books of Venue (titled portal book), Palisade (`LX2/2024`) and Kona (`SX2/2024`) and in no titled 2023 book of those nameplates; (4) it is the pre-facelift body, so it is not 2025; (5) no file on this host has been found filed under a year later than the model year it holds.

**Ruling on `NX4OB/2023`:** it is not assigned to a year. It serves as a cross-check for BOTH 2023 and 2024: in the curated-spec step a value is written for either year only where this book does not contradict it. On the dimension, tire, capacity, viscosity and schedule pages it is identical to the 2023 book.

**Self-identification (all eight files):** the pickup body with its open bed on the rear exterior overview (rendered side by side), the engine table "Smartstream G 2.5 GDI / Smartstream G 2.5 T-GDI, 152.4 cu. in (2,497 cc), 4, in-line" (p.2-8; 2025 p.10-2), wheelbase 118.30 in, overall length 195.67 in.

**Government data written:**

| Year | id | EPA entries (city / hwy / comb) | Recalls | Safety | Complaints | Engine label |
|---|---|---|---|---|---|---|
| 2022 | 38727 | 2.5T AWD 19 / 27 / 22; 2.5 AWD 21 / 27 / 23; 2.5 FWD 21 / 26 / 23 | 22V197000 (turbocharger oil pipe), 22V746000 (transmission), 23V038000 (roof moldings), 23V181000 (tow hitch harness) | two variants listed, neither rated — no row | 188 | 2.5L I4 |
| 2023 | 38728 | 2.5T AWD 19 / 27 / 22; 2.5 AWD 21 / 25 / 23; 2.5 FWD 22 / 26 / 23 | 23V038000, 23V181000 | overall 5, rollover 4, risk 16.4% | 80 | 2.5L I4 |
| 2024 | 38729 | the same three figures as 2023 | 24V412000 (power steering) | overall 5, rollover 4, risk 16.4% (four variants, early and later release, all identical) | 36 | 2.5L I4 |
| 2025 | 38730 | 2.5T AWD 19 / 27 / 22; 2.5 AWD 21 / 29 / 24; 2.5 FWD 22 / 30 / 25; XRT AWD 18 / 26 / 21 | 24V877000 (console wiring), 25V809000 (curtain air bag), 26V316000 (automatic emergency braking) | overall 5, rollover 4, risk 16.4% | 23 | 2.5L I4 |

- **EPA names:** "Santa Cruz AWD" and "Santa Cruz FWD" every year; 2025 adds "Santa Cruz XRT AWD". Ruling: the XRT is a trim of the same vehicle, covered by the same book, so its entry is taken. It shows as a second all-wheel-drive dual-clutch entry because the table has no trim column.
- **Engine label:** EPA gives 2.5 L and 4 cylinders; each book's engine table prints one cell for both engines with "4, in-line"; the vPIC decodes state no layout. One cell in the book = one entry in the batch (two entries would fail the one-match test).
- **Safety:** for 2022 NHTSA lists the AWD and FWD variants and rates neither, so no row is written and the app says no ratings are on file.
- **Pulls:** 68 requests, every answer HTTP 200. Totals: vehicles 4, fuel economy 13, recalls 10, safety ratings 3, complaints 327, pull-log lines 16.
- **Checks:** the build rehearsal passed on an in-memory copy before the write; the rebuilt data differs from the previous deployed data by the four new objects only; bare rows 424; verifier PASS 58.

**Not touched:** the existing 2026 row (id 9981) keeps its May fuel-economy rows (older annual-cost figures, one duplicated entry) and its empty engine label.

**Open after this step:** ~~step B, the curated specs for the four years~~ **done 2026-11-14**, see the section above (`2026-11-14-hyundai-santa-cruz-2022-2025`).

---

## ✅ KONA 2018 / 2019 / 2023 / 2025 — 4/4, Kona now 9/9 — `2026-11-14-hyundai-kona-2018-2025`, commit 69d9636d — THIRTEENTH HYUNDAI SLICE (missing-year step B)
**What this is:** the curated specs for the four rows added in step A (section below), each read from that year's own book. Tally **332 verified / 42 nameplates / 11 makes; Hyundai 56 rows.** Script `_write_hyundai_kona_2018_2025.py`; backup `wrench_vehicles.db.bak_kona_2018_2025_20261114_192717`. **LIVE CONFIRMED 2026-11-14 19:33:12** (version string served; the live data file `data.4ffa7c40.js` has the same md5 as the local one; CI green).

**Books and prints** (each identified by the Kona body on its exterior overview, the engine table and the wheelbase):

| Year | id | Primary book | Other prints of the same year | Result |
|---|---|---|---|---|
| 2018 | 38723 | portal `2018 Kona Owners Manual.pdf`, Copyright 2017, 463 pp | `OS/2018`, Copyright 2018, 463 pp | identical on every specification and schedule page |
| 2019 | 38724 | portal `2019 Kona OM.pdf`, Copyright 2018, 485 pp | `OS/2019`, Copyright 2019, 503 pp | identical except the brake-fluid grade |
| 2023 | 38725 | portal, PDF title "2023 Kona Owner's Manual", Copyright 2022, 602 pp | `OS/2023` (586 pp) and `OS/2022` (596 pp), both the 2023 book, neither on the US menu | every written value agrees |
| 2025 | 38726 | `SX2/2025`, PDF keywords name 2025, Copyright 2024, 713 pp | none | single print |

**⚠ EDITION CONFLICT — 2019 brake fluid (p.8-8):** first print "FMVSS116 DOT-3 or DOT-4"; later print "SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 CLASS-6". The quantity is the same. **Ruling (Robert, 2026-11-14, "Go, as recommended"): write the grade both prints name, FMVSS 116 DOT-4, with the agreed quantity.** (The 2018 prints agree on "DOT-3 or DOT-4"; the 2020 first print is the first to use the DOT-4 LV wording.)

**Read log — 2018 and 2019 (first generation; specifications chapter 8, schedules chapter 7):**

| Item | Value | Page |
|---|---|---|
| Engines | Gamma 1.6 T-GDI 1,591 cc; Nu 2.0 MPI 1,999 cc; both "In-line 4 cylinder" | 8-2 |
| Oil quantity | 4.23 qt / 4.0 L (Nu); 4.76 qt / 4.5 L (Gamma) | 8-7 |
| Oil grade (chart, page render) | Nu: 5W-20 recommended, also 5W-30 and 10W-30 by temperature. Gamma: 5W-30 recommended, also 5W-40, 10W-30, 15W-40, 20W-50 by temperature | 8-9 |
| Oil specification, 2018 | Nu: API SM and ILSAC GF-4 (or above), ACEA A5/B5. Gamma: ACEA A5/B5 | 8-7 |
| Oil specification, 2019 | Nu: API Latest (ILSAC Latest). Gamma: API Latest (ILSAC Latest) or ACEA A5/B5 | 8-7 |
| Automatic transmission (Nu) | ATF SP-IV, 7.08 qt / 6.7 L | 8-7 |
| Dual-clutch transmission (Gamma) | API GL-4 SAE 70W, 2.01–2.11 qt / 1.9–2.0 L; the 2018 book names "HK SYN DCTF 70W", the 2019 book "HK DCTF 70W" | 8-7 |
| Coolant | 6.8 qt / 6.5 L (Nu); 7.5 qt / 7.1 L (Gamma); phosphate-based ethylene glycol | 8-8 |
| Brake fluid | 0.74–0.85 qt / 0.7–0.8 L; grade per year as above | 8-8 |
| Rear differential and transfer case (AWD) | hypoid gear oil API GL-5 SAE 75W/90; quantities not written | 8-8 |
| Tires | 205/60R16, 215/55R17, 235/45R18 at 33 psi; spare T125/80D16 at 60 psi; lug nuts 79–94 lb-ft | 8-5 |
| Fuel tank | 13.2 gal / 50 L | 8-8 |
| Schedule, Nu | oil 7,500 mi / 12 mo; plugs 97,500 mi; air cleaner 30,000 mi / 48 mo; climate-control air filter 15,000 mi / 12 mo; rotation 7,500 mi; coolant 120,000 mi / 10 years, then 30,000 mi / 24 mo | 7-8 |
| Schedule, Gamma | oil 6,000 mi / 12 mo; plugs 42,000 mi; air cleaner 24,000 mi / 48 mo; filter 12,000 mi / 12 mo; rotation 6,000 mi; coolant as Nu | 7-13 |
| Brake fluid interval | inspection marks only in both prints of both years — no replacement line | 7-10, 7-15 |

**Why the 2018 / 2019 differential quantities fail:** the book prints 0.44–0.49 US qt beside 0.47–0.52 L and 0.36–0.4 US qt beside 0.38–0.42 L. Those quart figures are the litre figures DIVIDED by 1.057 instead of multiplied. Same page, same figures as the 2020 and 2021 books, which were left out for the same reason.

**Read log — 2023 (facelift; all three prints print capacities in US GALLONS, written as printed):**

| Item | Value | Page |
|---|---|---|
| Engines | Smartstream G1.6 T-GDi 1,598 cc; Smartstream G2.0 Atkinson 1,999 cc; "In-line 4 cylinder" | 2-9 |
| Oil | 0W-20 only (one bar on the chart); 1.14 gal / 4.3 L (G2.0); 1.27 gal / 4.8 L (G1.6T); full synthetic, API SN PLUS/SP or ILSAC GF-6 | 2-13, 2-14 |
| Intelligent variable transmission (G2.0) | SP-CVT1, 1.77 gal / 6.7 L | 2-13 |
| Dual-clutch transmission (G1.6T) | API GL-4 SAE 70W (HK D DCTF TGO-10, Spirax S6 GHDE 70W DCTF, 7 DCTF HKM), 0.42–0.45 gal / 1.6–1.7 L | 2-13 |
| Coolant | 1.59 gal / 6.0 L (G2.0); 1.82 gal / 6.9 L (G1.6T); ethylene glycol with phosphate, distilled water | 2-13 |
| Rear differential — printed "(AWD)" | GL-5 75W/90, 0.12–0.14 gal / 0.47–0.52 L | 2-13 |
| Transfer case — printed "(4WD)" | GL-5 75W/85; 0.49–0.55 qt / 0.47–0.52 L (G1.6T); 0.4–0.44 qt / 0.38–0.42 L (G2.0) | 2-14 |
| Brake fluid | SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6; quantity not written (0.5–0.6 qt beside 0.7–0.8 L) | 2-14 |
| Tires | as 2018 / 2019; compact spare "if equipped" | 2-11 |
| Fuel tank | 13.21 gal / 50 L | 2-14 |
| Schedule | oil 8,000 mi / 12 mo; plugs 96,000 mi (G2.0) and 48,000 mi (G1.6T); air cleaner 24,000 mi / 36 mo; cabin filter 16,000 mi / 24 mo; rotation 8,000 mi / 12 mo | 9-9 |
| | coolant 120,000 mi / 120 mo, then 24,000 mi / 24 mo | 9-10 |
| | brake fluid replace 48,000 mi / 48 mo | 9-11 |

**Read log — 2025 (second generation; its tire, capacity, chart and schedule pages equal the `SX2/2024` file's except one inspect-only line):**

| Item | Value | Page |
|---|---|---|
| Oil | 0W-20 only; 4.5 qt / 4.3 L (G2.0); 5.1 qt / 4.8 L (G1.6T); full synthetic, API SN PLUS/SP or ILSAC GF-6 | 31, 32 |
| Automatic transmission (G1.6T) | ATF SP4M-1, 6.8 qt / 6.5 L | 31 |
| Intelligent variable transmission (G2.0) | CVTF SP-CVT1; quantity not written (6.9 qt beside 6.7 L; 7.1 qt beside 6.9 L) | 31 |
| Coolant | 7.3 qt / 6.9 L (G2.0); 9.0 qt / 8.5 L (G1.6T); ethylene glycol base | 31 |
| Rear differential and transfer case (AWD) | GL-5 75W/85; quantities not written (0.6–0.7 qt beside 0.4–0.5 L; 0.8–0.9 qt beside 0.62–0.68 L) | 31 |
| Brake fluid | DOT-4, "as needed" | 31 |
| Tires | 215/60R17 at 36 psi; 215/55R18 and 235/45R19 at 33 psi; spare (if equipped) T145/90D16 at 60 psi; wheel nuts 79–94 lb-ft | 28 |
| Fuel tank | 12.4 gal / 47 L (G2.0); 13.2 gal / 50 L (G1.6T) | 31 |
| Schedule | oil 8,000 mi / 12 mo; air cleaner 24,000 mi / 36 mo; plugs 48,000 mi (G1.6T) and 96,000 mi (G2.0) | 625–626 |
| | coolant 120,000 mi / 120 mo, then 24,000 mi / 24 mo; brake fluid 48,000 mi / 48 mo; rotation 8,000 mi / 12 mo | 628 |
| | cabin filter 16,000 mi / 24 mo | 629 |

**Gates:** spark-plug part number and gap are published by none of the four books; 12V battery — 2018 / 2019 publish nothing, 2023 p.9-31 and 2025 p.655 show only an example capacity label; electric power steering has no fluid.

**Checks:** dry run 4 vehicles / 38 schedule rows / 41 unit pairs converted (the gallon check now tests both ends of a range); per-year guards in the script (schedule line counts and pages, brake-fluid line only on 2023 / 2025, gallon capacities only on 2023, AWD / 4WD wording); a guard keeps every non-converting printed quantity out of shipped columns; government rows untouched; bare rows 424; the rebuilt data differs from the previous deployed data in exactly these four objects; verifier PASS 58.

---

## ➕ KONA 2018 / 2019 / 2023 / 2025 — FOUR MISSING MODEL-YEAR ROWS ADDED + KONA FUEL-ECONOMY REPAIR — `2026-11-14-hyundai-kona-rows`, commit 4e936655 — MISSING-YEAR STEP A
**What this is:** four Kona model-year rows the fleet lacked, with EPA fuel economy and NHTSA recalls, safety ratings and complaints, and **no curated specification yet**. In the same change the fuel economy of the four existing Kona rows was repaired. Tally stays 328 / 42 / 11 (Hyundai 52 verified rows). Confirmed live 2026-11-14 19:01:49 local: the site serves version 2026-11-14-hyundai-kona-rows and data.f6179460.js, whose md5 f61794600900c3b11fc457772dc462e1 equals the local file. Verifier PASS 58 before staging; CI green.

**Book basis per year (rulings, Robert 2026-11-14, "Accept, start dry run"):**

| Year | id | Book | Basis |
|---|---|---|---|
| 2018 | 38723 | portal folder 2018, `2018 Kona Owners Manual.pdf`, 463 pp | Copyright 2017, PDF created 2017-12-01; 2018 is the Kona's first US model year. No PDF title names the year |
| 2019 | 38724 | portal folder 2019, `2019 Kona OM.pdf`, 485 pp | Copyright 2018, PDF created 2018-09-26; its own edition between the 2018 book and the titled 2020 book. No PDF title names the year |
| 2023 | 38725 | portal folder 2023, `2023-Kona-OM.pdf`, PDF title "2023 Kona Owner's Manual", 602 pp | the title names the year; Copyright 2022, created 2022-07-14 |
| 2025 | 38726 | second host `SX2/2025`, 713 pp | PDF keywords `en_US,hyundai,SX2,2025,engine,1.3` name the year; Copyright 2024; first posted 2024-10-14 (the portal serves nothing for 2024 or later) |

vPIC lists the Kona for all four years.

**Second-host files classified by vocabulary** (word counts are layout-proof; controls run): `OS/2018` (Copyright 2018, 463 pp) is a later print of 2018 — it uses none of the three words only the 2019 book has. `OS/2019` (Copyright 2019, 503 pp) is a later print of 2019 — it keeps "multimedia" 11 times and never says "infotainment", which the 2020 book uses 11 times. `OS/2022` and `OS/2023` are NOT on the US menu but are served; both hold the 2023 book (13 of 13 words only the 2023 book has, 0 of 6 only the 2022 book has). `SX2/2025` is its own edition between the 2024 and 2026 files.

**Government data written:**

| Year | EPA entries (city / hwy / comb) | Recalls | Safety | Complaints | Engine label |
|---|---|---|---|---|---|
| 2018 | 1.6T AWD 26 / 29 / 27; 2.0 AWD 25 / 30 / 27; 1.6T FWD 28 / 32 / 30; 2.0 FWD 27 / 33 / 30 | none | listed, not rated — no row | 75 | 1.6L I4 / 2.0L I4 |
| 2019 | same four figures | 21V301000 (ENGINE) | overall 5, rollover 4 | 198 | 1.6L I4 / 2.0L I4 |
| 2023 | 1.6T AWD 27 / 32 / 29; 2.0 AWD 28 / 33 / 30; 1.6T FWD 29 / 35 / 32; 2.0 FWD 30 / 35 / 32 | 23V526000 (transmission oil pump) | overall 5, rollover 4 | 67 | 1.6L I4 / 2.0L I4 |
| 2025 | six entries (2.0 AWD 26 / 29 / 27 and 27 / 29 / 28; 1.6T AWD 24 / 29 / 26; 2.0 FWD 28 / 35 / 31 and 29 / 34 / 31; 1.6T FWD 26 / 32 / 28) | 26V452000 (rear seat belt buckle) | overall 4, rollover 4 | 29 | empty |

- **EPA names:** EPA lists the nameplate as "Kona AWD" and "Kona FWD", and also lists "Kona Electric" (several names) and "Kona N". Ruling: the gasoline Kona row takes AWD and FWD only; the others are different vehicles with their own manuals.
- **Engine label:** the 2018, 2019 and 2023 books print "In-line 4 cylinder" for both engines (p.8-2, p.8-2, p.2-9), so the label is sourced. The 2025 book (p.25) prints "No. of cylinders 4" with no layout and vPIC states none, so the 2025 label is empty.
- **Safety:** NHTSA rates AWD and FWD separately. The stars agree and are stored; rollover risk differs (AWD / FWD: 2019 13.6% / 14.1%; 2023 13.6% / 14.1%; 2025 15.9% / 15.1%) and is left empty. For 2018 NHTSA lists both variants and rates neither, so no safety row is written and the app says no ratings are on file.
- **2018 recalls:** the "no results" answer is NHTSA's HTTP 400 with a count-0 body; the other three years supply the positive control.

**⚠ KONA FUEL-ECONOMY REPAIR (ruling "Go, write both"):** the May pull matched EPA model names loosely and folded "Kona Electric" into the gasoline Kona.

| Kona row | Stored before | Stored now |
|---|---|---|
| 2020 (id 673) | 4 gasoline entries typed "Electric" with the combined figure in the MPGe column and no city / highway / combined, plus the Kona Electric entry (120 MPGe) | 4 gasoline entries: 26 / 29 / 27, 26 / 30 / 28, 28 / 32 / 30, 27 / 33 / 30 |
| 2021 (id 2166) | same pattern | 4 gasoline entries: 26 / 29 / 27, 25 / 30 / 27, 28 / 32 / 30, 27 / 33 / 30 |
| 2022 (id 3694) | only the Kona Electric entry (120 MPGe) | 4 gasoline entries: 27 / 32 / 29, 28 / 33 / 30, 29 / 35 / 32, 30 / 35 / 32 |
| 2024 (id 6787) | only two Kona Electric entries (116 and 118 MPGe) | 6 gasoline entries, 26 to 31 combined |

13 rows out, 18 rows in. Only fuel economy on those four rows changed (the rebuilt data differs from the previous deployed data, for them, in the fuel-economy key alone).

**The same defect exists on other nameplates and is NOT repaired here** (reported to Robert 2026-11-14): rows typed "Electric" that carry a gasoline displacement — Genesis G80 2023–2026, Genesis GV70 2024–2026, Fiat 500 2018–2019, Porsche Macan 2024–2025, Dodge Charger 2026, Ford Mustang 2025, Kia Soul 2020, MINI Countryman 2026, Volvo XC40 2024; and vehicles that hold only an electric sibling's entries — Chevrolet Blazer 2024 and 2026, Dodge Charger 2024, Ford Explorer 2002.

**Method:** `_add_hyundai_rows.py kona-missing-years` (extended in this commit: EPA names to ignore, several engines per book, the optional fuel-economy repair guarded by a snapshot of the rows it replaces, no row for an unrated safety listing). Applied plan `b9a7f6552697f3209f735e20c27d3db22b4698e3e2ff4f184952b7fc718c5f9e`; backup `wrench_vehicles.db.bak_rows_kona_missing_years_20261114_185414`. New rows: vehicles 4, fuel_economy 18, recalls 3, safety_ratings 3, complaints 369, pull_log 16. Fleet 3,672 → 3,676; bare rows 424; 100 requests, one non-200 answer (the 2018 recalls reply); verifier PASS 58.

**Open after this step:** ~~step B, the curated specs for the four years~~ **done 2026-11-14**, see the section above (`2026-11-14-hyundai-kona-2018-2025`).

---

## ✅ PALISADE 2023 — 1/1, Palisade now 7/7 — `2026-11-14-hyundai-palisade-2023`, commit f4ab2817 — TWELFTH HYUNDAI SLICE (missing-year step B)
**What this is:** the curated specs for the 2023 row added in step A (section below), read from the 2023 book. Tally **328 verified / 42 nameplates / 11 makes; Hyundai 52 rows.** Script `_write_hyundai_palisade_2023.py`; backup `wrench_vehicles.db.bak_palisade_2023_20261114_182110`. Confirmed live 2026-11-14 18:27:55 local: the site serves version 2026-11-14-hyundai-palisade-2023 and data.003559e7.js, whose md5 003559e7babc09a0678df164ecf746d1 equals the local file. Verifier PASS 58 before staging; CI green.

**The two prints of the 2023 book** (identified by the Palisade facelift body on the exterior overview p.2-2, 3.8 GDI 3,778 cc as the only engine p.2-8, wheelbase 114.17 in, length 196.65 in):

| Print | File | Copyright | PDF created | Pages |
|---|---|---|---|---|
| first print | portal `2023-Palisade-Owners-Manual.pdf`, PDF title "2023 Palisade Owner's Manual" | 2022 | 2022-05-24 | 661 |
| later print | second host `LX2/2023` | 2023 | 2023-04-04 | 660 |
| (2024 book, for comparison) | second host `LX2/2024` | 2023 | 2023-10-23 | 630 |

**`LX2/2023` is a later print of the 2023 book, not the 2024 book.** It was created six months before the 2024 book, keeps the 2023 page count, and uses none of the wording that only the 2024 book has: the 2024 book says "two-wheeler" 25 times and "methods" 104 times; neither 2023 print uses either word.

**Tool lesson:** the two hosts typeset the same book differently. Whole-page identity and sentence matching therefore favour whichever book shares the layout, and both put `LX2/2023` wrongly beside the 2024 book. Word counts do not depend on layout. The vocabulary test (`word3way.py`) was checked on three controls first: Venue `QX/2022` (known to hold the next year's book: 0 of 23 same-year words, 24 of 25 next-year words), Palisade `LX2/2022` (known same year: 255 of 282 and 2 of 95), and the titled 2023 book against the 2024 / 2025 books (template effect only: 1 word each way).

**⚠ EDITION CONFLICT — the automatic transmission fluid:**

| Print | Page | Fluid | Quantity |
|---|---|---|---|
| first print | 2-12 | MICHANG ATF SP-IV, SK ATF SP-IV, NOCA ATF SP-IV, HYUNDAI genuine ATF SP-IV | 7.39 US qt (7.0 L) |
| later print | 2-13 | SK ATF SP4M-1, MICHANG ATF SP4M-1, S-OIL ATF SP4M-1, Hyundai Genuine ATF SP4M-1 | 7.39 US qt (7.0 L) |

The 2020–2022 books print SP-IV; the 2024 and 2025 books print SP4M-1. **Ruling (Robert, 2026-11-14, "Go, as recommended"): the standing edition rule applies — the fluid type is not written; the quantity both prints state is written in the capacity column.** This is the first verified row with an empty transmission fluid type.

**Read log — both prints agree** (capacities p.2-12, viscosity chart p.2-13 from a page render, tires and wheel nuts p.2-10; schedule p.9-8 / 9-9 / 9-10 from upright renders; the later print's pages were rendered too):

| Item | Value |
|---|---|
| Oil | 5W-30 only (one bar across the chart); 6.86 qt / 6.5 L; ACEA A5 or above; API latest (or ILSAC latest) or ACEA A5/B5 full synthetic required |
| Coolant | phosphate-based ethylene glycol; 12.44 qt / 11.79 L without trailer, 12.65 qt / 11.98 L with trailer |
| Brake fluid | SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6; quantity "as required" (the first print misprints "DOT0-4LV") |
| Rear differential | hypoid gear oil API GL-5 SAE 75W/85, 0.73 qt / 0.7 L (printed "HYPIO GEAR OIL") |
| Transfer case (AWD) | same oil, 0.73 qt / 0.7 L |
| Fuel tank | 18.75 gal / 71 L |
| Tires | 245/60R18 or 245/50R20, 35 psi front and rear; compact spare T155/90R18 at 60 psi |
| Wheel nuts | 79–94 lb-ft (107–127 N·m, 11–13 kgf·m) |
| Engine oil and filter | 8,000 mi / 12 mo |
| Spark plugs | 96,000 mi (no months printed) |
| Air cleaner filter | 24,000 mi / 36 mo |
| Tire rotation | 8,000 mi / 12 mo |
| Cabin air filter | 16,000 mi / 24 mo |
| Coolant | 120,000 mi / 120 mo, then 24,000 mi / 24 mo |
| Brake fluid | replace 48,000 mi / 48 mo |

**Not carried:** inspect-only schedule rows. The later print changes several of them — it puts inspection marks on the automatic transmission fluid row where the first print says "No check, No service required", and shifts the inspection grid of five other rows.

**Gates:** 12V battery (p.9-29 is only the capacity-label illustration AGM80L-DIN, captioned "the actual battery label in the vehicle may differ from the illustration"); spark-plug part number and gap are not published; MDPS has no fluid.

**Checks:** dry run 1 vehicle / 7 schedule rows / 7 unit pairs converted; the id held no curated rows; government rows untouched; bare rows 424; a guard keeps both disputed fluid names out of every shipped column; the rebuilt data differs from the previous deployed data in exactly this one object; verifier PASS 58.

---

## ➕ PALISADE 2023 — MISSING MODEL-YEAR ROW ADDED (government data only) — `2026-11-14-hyundai-palisade-2023-row`, commit cdcc454c — MISSING-YEAR STEP A
**What this is:** the fleet had Palisade rows for 2020, 2021, 2022, 2024, 2025 and 2026. This row fills 2023. It carries EPA fuel economy and NHTSA recalls, safety ratings and complaints, and **no curated specification yet**. Not counted as verified (tally stays 327 / 42 / 11). Confirmed live 2026-11-14 18:09:20 local: the site serves version 2026-11-14-hyundai-palisade-2023-row and data.952c82fe.js, whose md5 952c82fefd88674d95cf548157a78ca1 equals the local file. Verifier PASS 58 before staging; CI green.

| Item | Value |
|---|---|
| Row | id 38722 = 2023 Hyundai Palisade |
| Book that identifies the year | portal folder 2023, `2023-Palisade-Owners-Manual.pdf`, PDF title "2023 Palisade Owner's Manual", Copyright 2022, created 2022-05-24, 661 pp; overall length 196.65 in (the facelift body; the 2022 book prints 196.06) |
| vPIC | Palisade is listed for model year 2023 |
| EPA (two model names: "Palisade AWD", "Palisade FWD") | AWD 19 / 25 / 21; FWD 19 / 27 / 22; both 3.8 L, 6 cyl, Auto (S8), Regular |
| Recalls | 5: 23V180000 (wiper), 23V415000 (brake booster), 23V526000 (transmission oil pump), 25V607000 (rear seat belt buckle), 26V034000 (side curtain air bag) |
| Safety | two rated variants (AWD id 17098, FWD id 17097); stars identical: overall 5, frontal 5 / 5, side 5 / 5, rollover 4, side pole 5 |
| Complaints | 412, stored uncapped |

The 2023 EPA figures were checked against the neighbours: 2022, 2024 and 2025 are 19 / 24 / 21 (AWD) and 19 / 26 / 22 (FWD) on EPA today, as stored. 2023 really differs.

**Two rulings (Robert, 2026-11-14, "Go, as recommended") — standing rules for added rows:**
1. **The engine label stays empty when no allowed source states the layout.** EPA gives 3.8 L and 6 cylinders. The book's engine table p.2-8 prints "3.8 GDI — 230.55 cu. in (3,778 cc) — 3.78 x 3.43 in — firing order 1-2-3-4-5-6 — No. of cylinders 6" and no layout; the book never prints "V6" or "V-type". vPIC decodes of four complaint VIN prefixes state neither cylinders nor layout. (The 2020–2024 rows show "3.8L V6" from the earlier pipeline; the 2025 and 2026 rows are already empty.)
2. **When NHTSA rates drive variants separately, only the ratings all variants share are stored.** The table holds one row per vehicle. Here every star rating is identical; rollover risk is 14.3% for AWD and 15.9% for FWD, so that figure is left empty and the app hides the line. (Earlier pulls stored whichever variant NHTSA listed first.)

**Method:** script `_add_hyundai_rows.py palisade-2023` — the reusable successor of the Venue script: one batch per run from a table, several EPA model names per nameplate (an unexpected name stops the run), every rated variant fetched, engine layout from the book or else a vPIC decode. Applied plan `e3bb48f664c59a2d20eae1386669d0e66ae10a7b460088817a8ac1bd7f36d175`; backup `wrench_vehicles.db.bak_rows_palisade_2023_20261114_180127`. Rows: vehicles 1, fuel_economy 2, recalls 5, safety_ratings 1, complaints 412, pull_log 4. Fleet 3,671 → 3,672; bare rows 424; the rebuilt data differs from the previous deployed data by exactly this one object; all 15 requests answered HTTP 200.

**Open after this step:** ~~step B, the curated specs~~ **done 2026-11-14**, see the section above (`2026-11-14-hyundai-palisade-2023`); `LX2/2023` is classified there.

---

## ✅ VENUE 2022–2025 — 4/4, Venue now 7/7 — `2026-11-14-hyundai-venue-2022-2025`, commit 61c9be2c — ELEVENTH HYUNDAI SLICE (missing-year pilot, step B)
**What this is:** the curated specs for the four rows added in step A (section below), each read from that year's own book. Tally **327 verified / 42 nameplates / 11 makes; Hyundai 51 rows.** Script `_write_hyundai_venue_2022_2025.py`; backup `wrench_vehicles.db.bak_venue_2022_2025_20261114_174608`. Confirmed live 2026-11-14 17:51:41 local: the site serves version 2026-11-14-hyundai-venue-2022-2025 and data.3061682b.js, whose md5 3061682bf34ef0e8b5e296b31c90f343 equals the local file. Verifier PASS 58 before staging; CI green.

**Books and prints** (identified by the Venue body on the exterior overview p.2-2, wheelbase 99.2 in, length 159.0 in, Smartstream G1.6 1,598 cc as the only engine):

| Year | id | Primary book | Other prints of the same year | Result |
|---|---|---|---|---|
| 2022 | 38718 | titled portal book, Copyright 2021, 390 pp | none (`QX/2021` is the 2021 book, `QX/2022` holds the 2023 book) | single print |
| 2023 | 38719 | titled portal book, Copyright 2022, 403 pp | `QX/2022` (Copyright 2022): spec pages 2-7 to 2-12 and all four schedule pages identical. `QX/2023` (Copyright 2023): on those pages it only adds an engine-oil-additive notice and renumbers footnotes | no value differs |
| 2024 | 38720 | portal book, cover reads "2024 Owner's Manual VENUE", Copyright 2023, 410 pp | `QX/2024` (Copyright 2024): spec pages and all four schedule pages identical | no value differs |
| 2025 | 38721 | `QX/2025`, Copyright 2025, 413 pp | none (the portal serves no 2025 book) | single print |

**The 2025 book — accepted by ruling 2026-11-14.** No page names the model year. Support: the label was first posted 2024-10-16 and last updated 2025-05-29, before the separate `QX/2026` label was first posted (2025-08-19). The book is its own edition: it introduces the Oil Life Management System on p.9-7 (none in either 2024 print or in 2023; its p.9-7 is identical to the 2026 book's), and it lacks the 2026 changes (different bulb table, "MICHANG CVTF SP-CVT1" fluid naming, "Brake fluid" label, 397 pages). **Not a marker:** the tire date-code example ("week of 20xx") follows the COPYRIGHT year in every print.

**Read log — the same in all four years** (tires and lug nuts p.2-9; capacities p.2-11; viscosity chart p.2-12 from a page render):

| Item | Value |
|---|---|
| Oil | 0W-20 only (one bar across the whole chart); 4.02 qt / 3.8 L; API SN PLUS/SP or ILSAC GF-6; full synthetic required |
| Brake fluid | SAE J1704 DOT-4 LV, FMVSS 116 DOT-4, ISO 4925 Class 6; 0.74–0.85 qt / 0.7–0.8 L |
| Coolant type | mixture of antifreeze and water, phosphate-based ethylene glycol |
| Tires | 185/65R15 at 36 psi; 205/55R17 at 33 psi; compact spare T125/80D15 or T125/80D16 at 60 psi |
| Wheel lug nuts | 79–94 lb-ft (107–127 N·m, 11–13 kgf·m) |
| Fuel tank | 11.89 gal / 45 L |
| Automatic transmission fluid | CVTF SP-CVT1 |

**Read log — by year** (schedule grids read from upright page renders):

| Item | 2022 (p.8-8 / 8-10) | 2023, 2024, 2025 (p.9-8 / 9-10) |
|---|---|---|
| Manual transmission | still listed: fluid API GL-4 SAE 70W TGO-9, 1.59–1.69 qt / 1.5–1.6 L | not listed |
| Coolant quantity written | 5.94 qt / 5.62 L, manual transmission only | none |
| Refrigerant (not carried) | R-134a | R-1234yf |
| Engine oil and filter | 8,000 mi / 12 mo | 8,000 mi / 12 mo |
| Spark plugs | 96,000 mi / 144 mo | 96,000 mi (no months printed) |
| Air cleaner filter | 32,000 mi / 48 mo | 32,000 mi / 48 mo |
| Cabin air filter | 8,000 mi / 12 mo | 16,000 mi / 24 mo |
| Tire rotation | 8,000 mi (no months printed) | 8,000 mi / 12 mo |
| Coolant | 120,000 mi / 10 years, then 24,000 mi / 36 mo | 120,000 mi / 120 mo, then 24,000 mi / 24 mo |
| Brake fluid | replace 60,000 mi / 48 mo | replace 60,000 mi / 48 mo |

**Rulings applied (Robert, 2026-11-14, "Go, as recommended"):**
- **2022 manual transmission:** the book lists it while EPA lists only the automatic — written as printed, "if equipped", exactly as ruled for 2021; the coolant column carries the manual figure only.
- **Standing unit ruling:** the automatic's fluid quantity (6.34 US qt beside 6.7 L) and its coolant quantity (6.32 US qt beside 5.78 L) do not convert, in every book — neither is written. For 2023–2025 no other coolant figure is printed, so the quantity is null.
- **Gates:** spark-plug part number and gap, and the 12V battery, are not published in any of the four books. Electric power steering has no fluid (the 2022 book says EPS, 2023+ say MDPS).

**Checks:** dry run 4 vehicles / 28 schedule rows / 19 unit pairs converted; the four ids held no curated rows; government rows untouched; bare rows 424; the rebuilt data differs from the previous deployed data in exactly these four objects; verifier PASS 58.

**Quirk seen, no action:** the titled 2023 book's p.9-10 footnote says "an authorized HYUNDAI or KIA dealer"; the 2024 book drops "or KIA".

---

## ➕ VENUE 2022–2025 — FOUR MISSING MODEL-YEAR ROWS ADDED (government data only) — `2026-11-14-hyundai-venue-rows`, commit 2fbf604a — MISSING-YEAR PILOT, STEP A
**What this is:** the fleet had Venue rows for 2020, 2021 and 2026 only. These four rows fill the gap. They carry EPA fuel economy and NHTSA recalls, safety ratings and complaints. **They carry no curated specification yet** — oil, fluids, parts, torque and maintenance come from each year's book in step B. They are not counted as verified (tally stays 323 / 42 / 11; Hyundai 47 verified rows). No reliability, warranty or service-cost rows were written. Confirmed live 2026-11-14 17:34:33 local: the site serves version 2026-11-14-hyundai-venue-rows and data.9df6e963.js, whose md5 9df6e9639142f4c0cf7146f523a3f885 equals the local file. Verifier PASS 58 before staging; CI green.

**Rulings (Robert, 2026-11-14):** a new row needs BOTH a self-identified manufacturer book for the model year AND an NHTSA vPIC listing; it gets government data only, pulled status-aware; engine label from the EPA record; fleet-total text updated with the batch; static vehicle pages untouched; two gated steps per batch (rows first, curated specs second).

| Year | id | Book that identifies the year | vPIC | EPA city / hwy / comb | Recalls | Safety overall | Complaints |
|---|---|---|---|---|---|---|---|
| 2022 | 38718 | portal folder 2022, `2022-Venue-Owners-Manual.pdf`, PDF title "2022 Venue Owners Manual", Copyright 2021, 390 pp | listed | 29 / 33 / 31 | 22V458000 (SEAT BELTS:FRONT) | 4 | 22 |
| 2023 | 38719 | portal folder 2023, `2023-Venue-OM.pdf`, PDF title "2023 Venue Owner's Manual", Copyright 2022, 403 pp | listed | 29 / 33 / 31 | none | 4 | 24 |
| 2024 | 38720 | portal folder 2024, `2024 Venue OM.pdf`, cover reads "2024 Owner's Manual VENUE", Copyright 2023, 410 pp | listed | 29 / 33 / 31 | 24V308000 (EGR valve) | 4 | 20 |
| 2025 | 38721 | second host `QX/2025` only (the portal serves no 2025 book); no page names the year; Copyright 2025, 413 pp, first posted 2024-10-16; the host carries a separate `QX/2026` label | listed | 29 / 32 / 31 | none | 4 | 4 |

Each year: one EPA record (Auto AV-S1, 1.6 L, 4 cyl, front-wheel drive, Regular), annual cost as EPA states it on the pull date ($1,950). One NHTSA-rated variant per year ("5 HB FWD"). Complaints stored uncapped. `QX/2022` is NOT the 2022 source — the label audit showed it holds the 2023 book.

**Engine label `1.6L I4` — every part sourced:** EPA gives 1.6 L and 4 cylinders; each of the four books prints on p.2-7 "ENGINE — Smartstream G1.6 — Displacement 97.5 cu.in (1,598 cc) — No. of cylinders 4, in-line". A vPIC decode of the complaint VIN prefixes confirms year, make, model and 1.6 L, but states neither cylinder count nor layout.

**Method (script `_add_hyundai_rows_venue.py`):**
- Dry run by default. It prints every row, rehearses the real build (`files/04_rebuild_demo.py` gates and data assembly) on an in-memory copy of the database, saves the rows as a plan file and prints its sha256. `--write --sha <hash>` applies exactly that plan after a backup and makes no new pull. Applied plan: `c478d443af8f1548c949cef9ee45962a5e615ed0496f40070ce3d1c9f2d456c7`; backup `wrench_vehicles.db.bak_venue_rows_20261114_172733`.
- **An answer is judged by HTTP status AND body.** NHTSA `recallsByVehicle` answers a query that matches nothing with **HTTP 400** and a well-formed body (`Count 0`, `Message "Results returned successfully"`, `results []`), and gives an unknown model the identical answer. Only that exact shape is accepted as "no recalls", and only with a positive control: another year of the same make / model spelling returning rows on the same endpoint in the same run (2022 and 2024 did). Every other 400, 429 or 5xx stops the run. The 2023 and 2025 "none" entries rest on this.
- Rows inserted: vehicles 4, fuel_economy 4, recalls 2, safety_ratings 4, complaints 70, pull_log 16. Fleet 3,667 → 3,671. Bare rows 424. The rebuilt data differs from the previous deployed data by exactly the four new objects.

**Open after this step:**
1. ~~**Step B** — the curated-spec slice for Venue 2022–2025~~ **done 2026-11-14**, see the section above (`2026-11-14-hyundai-venue-2022-2025`).
2. **Annual fuel cost is time-dependent.** EPA now gives $1,950 for the 2021 and 2026 Venue too; the stored 2020 / 2021 / 2026 rows (pulled May 2026) show about $1,350–$1,450. A fleet-wide refresh is a separate decision.
3. **Static vehicle pages** (`wrench_deploy/vehicles/`) were not touched; the four new vehicles have no static page. That belongs to the separate pages lane.

---

## ⚠ LABEL AUDIT 2026-11-14 — second-host year labels tested against the titled portal books (read-only audit; row corrections follow separately)
**Why:** while identifying books for the missing Venue model years, the label `QX/2022` turned out to hold a book that matches the titled **2023** Venue manual, not the titled 2022 one. That contradicted the statement "QX label = model year — proved" made in the Venue section below (it was proved for 2020 only). Every second-host label cited by a shipped row was then tested.

**Method:** (1) posting dates from the host's listing API (`firstdate` / `lastdate`); (2) for each back-catalogue label, a three-way comparison with the titled portal books for that year (N) and the next (N+1) on values that DIFFER between N and N+1 — schedule step, replace-every intervals, coolant repeat, quart / gallon figures, oil grades, engine list, refrigerant, 4WD / AWD wording — plus whole-book similarity. A label is *proved* only when it matches N where N and N+1 differ.

**Posting dates:** the back catalogue was uploaded in waves (2024-08-26 / 27, 2024-09-06 / 10 / 12, 2024-10-15 / 21) regardless of model year. Current-year labels are posted when the model launches (e.g. `SX2/2024` 2023-12-12, `DN8/2024` 2023-11-08, the 2025 labels in 2024-10, the 2026 labels 2025-05 to 2025-10). Unlisted and therefore undated: `CN7` 2021 / 2022 / 2024 / 2025 / 2026, `OS` 2022 / 2023, `NX4OB` 2025 / 2026.

| Class | Label | Evidence | Shipped row that cites it |
|---|---|---|---|
| **CONTRADICTED** — holds the next model year's book | Kona `OS/2022` | 0 of 5 markers match the titled 2022 book, 5 match the titled 2023 book; similarity 0.876 vs 0.988 | Kona 2022 (id 3694) |
| | Elantra `CN7/2022` | 0 vs 2 markers; similarity 0.886 vs 0.976 | Elantra 2022 (id 3691) |
| | Venue `QX/2022` | no manual transmission, R-1234yf, wireless-charging pages = titled 2023; similarity 0.789 vs 0.984 | none |
| **UNPROVED** — matches the next year's titled book on every differing marker, but could be a later print of the row year | Sonata `DN8/2021` | 0 of 3 markers match the titled 2021 book, 3 match the 2022 portal book | Sonata 2021 (id 12853) — its G2.5 T-GDI values come from this book alone |
| | Elantra `CN7/2021` | closest to the 2022 portal book (4 unmatched pages; 48 against the titled 2021 book, which is the America-built 2.0-only book) | Elantra 2021 (id 2163) — its G1.6 T-GDi values come from this book alone |
| | Kona `OS/2020` | its one differing value matches the titled 2021 book | Kona 2020 (id 673) — no value rests on it |
| | Tucson `NX4a/2024` | Copyright 2023; its only differing value (coolant 10.11 qt) matches the 2022 / 2023 books; the 2024 portal book and `NX4/2024` print 10.04 | Tucson 2024 (id 6783) — the second coolant figure rests on it alone |
| **PROVED** = the row year | Palisade `LX2/2021`, `LX2/2022`, `LX2/2024`, `LX2/2025` | 2021 keeps the 2021 values; 2022 is the pre-facelift book (Copyright 2021, 663 pp like the titled 2022 book) with a revised schedule; 2024 is a Copyright-2023 first print; an LX2 book cannot be the 2026 LX3 | Palisade 2021 / 2022 / 2024 / 2025 |
| | Kona `OS/2021` | pre-facelift book, 8 of 8 markers | Kona 2021 |
| | Santa Fe `TMa` 2018 / 2019 / 2020 / 2022 | already assigned by content (label = copyright year = first print of the next model year; generation boundaries as proof) | Santa Fe 2019 / 2020 / 2021 / 2023 |
| | Venue `QX/2020`, `QX/2021` | 2020: schedule step; 2021: 0.997 to the titled 2021 book and lacks the 2022 changes | Venue 2020 / 2021 |
| | Tucson `NX4/2025`, `NX4a/2025` | 4WD wording (the 2026 books say AWD) | Tucson 2025 |
| | Sonata `DN8/2024` | identical to the portal 2024 book | Sonata 2024 |
| **SUPPORTED by launch-timed posting** | `SX2/2024`, `SX2/2026`, `DN8/2025`, `DN8/2026`, `MX5a/2025`, `MX5a/2026`, `LX3/2026`, `NX4/2026`, `NX4a/2026`, `QX/2026` | first posted when that model year launched; separate 2027 labels exist for SX2, DN8, LX3, MX5a | the 2024–2026 rows of those nameplates |
| **SUPPORTED, not provable by a changed value** | Elantra `CN7/2024`, `CN7/2025`, `CN7/2026`; Santa Cruz `NX4OB/2026` | 2024 / 2025 fit the first-print pattern (copyright = model year − 1); the two Copyright-2026 books rest on the host's practice of giving 2027 books their own label | Elantra 2024–2026, Santa Cruz 2026 |

**What this changes in earlier sections of this log:**
- The **Palisade 2022** and **Kona 2021** edition conflicts are REAL (two prints of the same model year).
- The **Kona 2022** and **Elantra 2022** "edition conflicts" (spark-plug interval 47,000 vs 48,000, coolant repeat 30,000 vs 24,000, filter / rotation months) were differences between MODEL YEARS. The values left out there can be restored from the titled 2022 books.
- **No shipped value is proved wrong.** Three sets are unproved for their row's model year and are being removed: the Sonata 2021 G2.5 T-GDI set, the Elantra 2021 G1.6 T-GDi set, and the second coolant figure added to Tucson 2024 on 2026-11-14.

**Pattern:** a first print carries the PREVIOUS year's copyright, and a back-catalogue label Y usually carries copyright Y — so label Y is often the first print of model year Y+1 (`TMa` 2018–2021, `OS/2022`, `CN7/2022`, `QX/2022`, probably `DN8/2021` and `CN7/2021`). Not always: `QX/2020`, `QX/2021` and `LX2/2021` are later prints of their own year, and `OS/2021` and `LX2/2022` carry the previous year's copyright. **Every label needs its own test.**

**New sources this uncovers:** `OS/2022` + titled 2023 → Kona 2023; `CN7/2022` + titled 2023 → Elantra 2023; `QX/2022` + titled 2023 → Venue 2023; 2022 portal book + `DN8/2021` → Sonata 2022.

**✅ CORRECTIONS APPLIED — `2026-11-14-hyundai-label-audit`, commit aab7a7ca** (live confirmed 16:48:28, blob `data.c3389d76.js` byte-identical to the local build at 16:48:31, old blob returns 404, CI green). Script `_fix_hyundai_label_audit_2026_11_14.py` (idempotent; backup `wrench_vehicles.db.bak_label_audit_20261114_163941`). Fleet tally unchanged at 323; bare-row freeze unchanged at 424.

| Row | Change | Reason |
|---|---|---|
| Sonata 2021 (id 12853) | G2.5 T-GDI set removed: viscosity now `0W-20`; oil capacity G1.6 T-GDi only; dual clutch fluids gone; coolant capacity empty; 48,000-mile plug row deleted (9 → 8 interval rows) | those values came from `DN8/2021` alone, whose model year is unproved |
| Elantra 2021 (id 2163) | G1.6 T-GDi set removed: oil, coolant and transmission are G2.0 only; 235/40R18 line and T125/80D16 spare gone; 47,000-mile plug row deleted (8 → 7 rows) | those values came from `CN7/2021` alone, whose model year is unproved; the titled 2021 book is the 2.0-only book |
| Tucson 2024 (id 6783) | coolant back to `10.04 qt / 9.5 L` | the second figure came from `NX4a/2024` alone (Copyright 2023, model year unproved) |
| Kona 2020 (673), Kona 2022 (3694), Elantra 2022 (3691) | source wording only; shipped data byte-identical | the second-host books they cited are not second prints of the row year |

Every value that remains on Sonata 2021 and Elantra 2021 was re-checked against the TITLED 2021 portal books (tires p.2-9, capacities p.2-11, full-synthetic note p.2-12). The Sonata 2021 G2.5 GDi oil capacity stays unwritten: the titled book prints 5.49 qt / 5.2 L while every later book prints 6.13 qt / 5.8 L, and the same table's coolant cells repeat its oil cells. The Elantra 2021 fuel tank keeps its gallon rendering by the earlier ruling (titled book: 47 L beside 49.66 US qt; `CN7a` books: 47 L beside 12.42 US gal).

**Re-run guards:** `_write_hyundai_sonata_elantra_reread.py`, `_write_hyundai_kona.py`, `_write_hyundai_tucson.py` and `_write_hyundai_newest_years.py` now refuse `--write` unless `--i-know-this-is-superseded` is passed; run the fix script again after any such re-run. Without the guard the newest-years script would have re-applied the two-figure Tucson coolant.

**✅ INTERVALS RESTORED — `2026-11-14-hyundai-restore-2022`, commit ea95000e** (live confirmed 17:06:43, blob `data.1ac13536.js` byte-identical to the local build at 17:06:45, old blob returns 404, CI green). Script `_fix_hyundai_restore_2022_intervals.py` (idempotent; run after the label-audit fix script; backup `wrench_vehicles.db.bak_restore_2022_20261114_170252`). Read from upright page renders of the TITLED 2022 books.

| Row | Restored | Page |
|---|---|---|
| Kona 2022 (id 3694) — `kona_2022_OSPE_portal_OM.pdf`, PDF title "2022 Kona Owner's Manual", Copyright 2021 | spark plugs, Smartstream G1.6 T-GDi: every 47,000 mi | 9-8 |
| | cabin air filter: 16,000 mi **or 12 months** (months were missing) | 9-8 |
| | coolant: first at 120,000 mi / 120 months, **thereafter every 30,000 mi / 24 months** | 9-9 |
| | wording: rear differential and transfer case now read **(4WD)** as this book prints; the row had the 2023 book's "(AWD)" | 2-13 / 2-14 |
| Elantra 2022 (id 3691) — `elantra_2022_portal_OM.pdf`, portal folder 2022 | spark plugs, Smartstream G1.6 T-GDi: every 47,000 mi | 9-8 |
| | coolant: **thereafter every 30,000 mi / 24 months** | 9-9 |

Each row now has 8 interval rows. Unchanged on Elantra 2022: tire rotation 8,000 mi with no months (the book prints none); the oil requirement (this book asks for API SN PLUS or above, not full synthetic). The whole rebuilt fleet was compared with the deployed data: these two vehicles are the only objects that changed.

**Cell audit (every number in both rows' shipped cells checked against the titled specification pages):** all present. The Kona 2022 litre figures are printed but missing from the PDF's text layer (confirmed on renders of p.2-13 / 2-14) — a text search that finds nothing means "look at the page".

**Observation (no action):** the portal's 2022 Elantra file is untitled, Copyright 2020, with page stamps dated 2020-12-03. Hyundai serves it as the 2022 manual, so it is the 2022 source; it was probably authored during the 2021 model year, but nothing from the manufacturer designates it as a 2021 book, so it does not restore the Elantra 2021 turbo values.

---

## ✅ VELOSTER 2/3 + SANTA CRUZ 1/1 — `2026-11-14-hyundai-veloster-santa-cruz`, commit 929886b9 — TENTH HYUNDAI SLICE
Recon, reads, write and deploy all 2026-11-14 (live confirmed 16:01:53, blob `data.40f286a4.js` byte-identical to the local build at 16:01:54, old blob returns 404, CI green). Write script `_write_hyundai_veloster_santa_cruz.py`. Backup `wrench_vehicles.db.bak_veloster_santa_cruz_20261114_155738`. Fleet tally 320 → 323, nameplates 40 → 42. The three written ids held only blacklisted-source rows (unsourced placeholders — oil "4.8", battery "Group 47" — or scraped rows, never shipped), which this replaces.

| Row | Book | Print status |
|---|---|---|
| **Veloster 2019** (id 38641) | portal `2019 Veloster OM.pdf` (491 pp, Copyright 2018, created 2018-08-01, no title metadata; the JS generation began with MY2019) | one print |
| **Veloster 2020** (id 38682) | **none — DEFERRED** | — |
| **Veloster 2021** (id 38683) | portal `2021-Veloster-Owners-Manual.pdf` (482 pp, titled, cover "2021 Owner's Manual VELOSTER", part no. LJ3O-EU05B, Copyright 2020) | one print |
| **Santa Cruz 2026** (id 9981) | second host `NX4OB/2026` (567 pp, book header `_NX4aOB_en_US`, Copyright 2026, created 2026-04-30) — served but absent from the US menu | one print |

**⛔ VELOSTER 2020 DEFERRED:** no manufacturer owner's manual is available. The portal answered HTTP 404 for 81 filename forms across seven folder spellings (`veloster`, `velostar`, `velostor`, `veloser`, `velostr`, `Veloster`, `veloster-n`); the second host carries no Veloster book (not on the US menu; `JS` and `JSN` answer HTTP 500). The row is untouched — the write script fingerprints it before and after.

**Self-ID.** Veloster: JS body on the exterior overview p.1-2 (image code OJS018001N, both books rendered), wheelbase 104.33 in, length 166.93 in, Gamma 1.6 T-GDI 1,591 cc + Nu 2.0 MPI 1,999 cc. Santa Cruz: pickup body on the exterior overview p.2-3 (rendered), wheelbase 118.30 in, length 195.67 in, Smartstream G2.5 GDI + G2.5 T-GDI 2,497 cc. Veloster N has its own book and is not covered. The DB engine label on the Veloster rows ("1.6L Turbo") was left as it is; both engines the books list are written, each labelled.

**⚠ WHICH MODEL YEAR IS `NX4OB/2026`?** NHTSA vPIC lists a Santa Cruz for both 2026 and 2027, so the label was tested, not assumed. (1) The host files 2027-model-year books under their own 2027 label — `SX2/2027` first posted 2026-06-30, `LX3/2027` 2026-09-11, `MX5a/2027` 2026-10-14, `DN8/2027` served — and `NX4OB/2027` does not exist. (2) It keeps updating 2026 labels in place after a 2027 book appears (`SX2/2026` updated 2026-07-14). (3) This book says AWD where the 2025-label book says 4WD, the change the Tucson books show between 2025 and 2026. Read as a later print of model year 2026. The same evidence supports the 2026 rows written earlier from `DN8/2026`, `NX4/2026` and `QX/2026`. **The early NX4OB labels ARE shifted:** label 2021 (Copyright 2021, 596 pp) is the model-year-2022 book (the titled portal `2022-Santa-Cruz-Owners-Manual.pdf` is Copyright 2021, 598 pp; no 2021 Santa Cruz exists); label 2025 (Copyright 2024, facelift) is model year 2025.

**Veloster 2019 and 2021 — values (the two books agree on every specification page except the brake-fluid specification):**

| Field | Gamma 1.6 T-GDI | Nu 2.0 MPI | Page |
|---|---|---|---|
| Engine oil | 4.76 qt / 4.5 L | 4.23 qt / 4.0 L | 8-7 |
| Viscosity (chart rendered) | 5W-30 recommended; chart also 5W-40, 10W-30, 15W-40, 20W-50 | 5W-20 recommended; chart also 5W-30, 10W-30 | 8-9 |
| Oil specification | ACEA A5/B5 | API SM and ILSAC GF-4 (or above), ACEA A5/B5 | 8-7 |
| Automatic / dual clutch | DCT fluid API GL-4 SAE 70W, 2.01–2.11 qt / 1.9–2.0 L | ATF SP-IV, 7.08 qt / 6.7 L | 8-7 |
| Coolant | 7.5 qt / 7.1 L | 6.8 qt / 6.5 L | 8-8 |

Both engines: manual transmission fluid API GL-4 SAE 70W TGO-9, 1.8–1.9 qt / 1.7–1.8 L · brake fluid 0.74–0.85 qt / 0.7–0.8 L (2019 FMVSS 116 DOT-3 or DOT-4; 2021 SAE J1704 DOT-4 LV / FMVSS 116 DOT-4 / ISO 4925 Class 6) · fuel tank 13.2 gal / 50 L · tires 215/45R17, 225/40R18, 225/40ZR18 at 33 psi front and rear · compact spare T125/80D16 at 60 psi · wheel lug nut 79–94 lb-ft (107–127 N·m, 11–13 kgf·m) · electric power steering. The books also print 36 psi for driving over 100 mph; not carried (the write script fails if it reaches a shipped column).

**Veloster normal schedule (upright grids; Nu 2.0 MPI p.7-8 to 7-10, Gamma 1.6 T-GDI p.7-13 to 7-15), mi / mo:**

| Item | Gamma 1.6 T-GDI | Nu 2.0 MPI |
|---|---|---|
| Engine oil & filter | 6,000 / 12 | 7,500 / 12 |
| Spark plugs | 42,000 | 97,500 |
| Air cleaner filter | 24,000 / 48 | 30,000 / 48 |
| Climate control air filter | 12,000 / 12 | 15,000 / 12 |
| Tire rotation | 6,200 (as printed; the grid steps by 6,000) | 6,200 (as printed; the grid steps by 7,500) |
| Coolant | first 120,000 / 120, then 30,000 / 24 | same |
| Brake fluid, 2019 | inspect only — no row | inspect only — no row |
| Brake fluid, 2021 (grid marks, rendered) | 30,000 / 60 (brake / clutch) | 30,000 / 48 |

2019 = 10 rows, 2021 = 12 rows.

**Santa Cruz 2026 — values:** oil 6.13 qt / 5.8 L (one cell spans both engines), 0W-20 (G2.5 GDI) / 0W-30 (G2.5 T-GDI), API SN PLUS/SP or ILSAC GF-6, full synthetic required (p.10-7; chart p.10-9 rendered) · automatic transmission ATF SP4M-1, 6.87 qt / 6.5 L (the only transmission listed) · coolant 10 qt / 9.5 L (G2.5 GDI, printed without decimals) and 9.09 qt / 8.6 L (G2.5 T-GDI) · brake fluid SAE J1704 DOT-4 LV / ISO 4925 Class 6 / FMVSS 116 DOT-4, 0.87 qt / 0.82 L · rear differential (AWD) 0.56–0.67 qt / 0.53–0.63 L and transfer case (AWD) 0.65–0.71 qt / 0.62–0.68 L, hypoid gear oil API GL-5 SAE 75W/85 (p.10-8) · fuel tank 17.69 gal / 67 L · tires 245/60R18 or 245/50R20 at 35 psi front and rear, compact spare T135/80D18 at 60 psi, wheel nut 79–94 lb-ft (p.10-4, rendered) · MDPS.

**Santa Cruz normal schedule (p.9-11 to 9-15), 8 rows, mi / mo:** oil 8,000 / 12 · spark plugs 96,000 (G2.5 GDI) and 48,000 / 72 (G2.5 T-GDI, grid marks on a render) · air cleaner 24,000 / 36 · cabin filter 16,000 / 24 (grid marks) · tire rotation 8,000 / 12 · coolant first 120,000 / 120 then 24,000 / 24 · brake fluid 48,000 / 48.

All 17 printed unit pairs convert. Each row has one print, so there was no second print to compare.

**Gates (null):** spark-plug part number and gap in all three · 12V battery (Veloster: not published; Santa Cruz: capacity-label illustration only, MF68R-DIN) · Veloster differential (front-wheel drive).

**⚠ PROBE TOOLING INCIDENT (2026-11-14).** After about 6,700 portal probe requests in one afternoon, two runs at once, `owners.hyundaiusa.com` (Cloudflare) answered HTTP 429 with `Retry-After: 442`. The first probe tool treated every failed request as "not found", so it could not tell a missing file from a rate-limited answer — and its negatives had already been recorded here (the Accent defer, the Venue "nothing for 2025 / 2026"). The tool was rebuilt: a miss counts only on HTTP 404, the run stops on 429, one request at a time with a pause. Every negative recorded on 2026-11-14 was then re-asked and holds: Accent 1995–2004 (21 forms a year), Venue 2025 / 2026, Santa Cruz 2025 / 2026, Veloster 2020 — all HTTP 404; Accent 2007, 2009–2013, 2015 — HTTP 404 on the core forms. The probe counts quoted in the Venue and Accent sections below (322, 552) come from the first tool.

**No vehicle row exists** for Santa Cruz 2022–2025, though books do (portal `2022-Santa-Cruz-Owners-Manual.pdf`; second host `NX4OB` labels 2021–2025). **Update 2026-11-14:** the four rows now exist (see the Santa Cruz rows section near the top); the portal also serves a 2023 book, found the same day.

---

## ✅ VENUE — 3/3 (2020 / 2021 / 2026 QX) — `2026-11-14-hyundai-venue`, commit 43c1f8c1 — NINTH HYUNDAI SLICE
Recon, reads, write and deploy all 2026-11-14 (live confirmed 15:21:01, blob `data.34209456.js` byte-identical to the local build at 15:21:02, old blob returns 404, CI green). Write script `_write_hyundai_venue.py`. Backup `wrench_vehicles.db.bak_venue_20261114_151436`. Fleet tally 317 → 320. The three ids held only blacklisted-source rows (ai-generated / scraped, never shipped), which this replaces.

| Row | Books | Print status |
|---|---|---|
| **2020** (id 677) | portal `2020 Venue Owner's Manual.pdf` (375 pp, Copyright 2019, titled) + second host `QX/2020` (392 pp, Copyright 2020) | two prints, identical on every page read |
| **2021** (id 2170) | portal `2021-Venue-Owners-Manual.pdf` (392 pp, Copyright 2020, titled, glyph-coded text) + `QX/2021` (392 pp, Copyright 2021) | two prints, identical on every page read (the later print adds a notice on p.8-7) |
| **2026** (id 9980) | `QX/2026` (397 pp, Copyright 2026, PDF created 2026-07-21, title `QX_ENG-HMA.indb`) | one available print; the portal has nothing for 2025 / 2026 (322 probes) |

**Self-ID (every book):** Venue body on the exterior overview p.2-2, wheelbase 99.2 in, overall length 159.0 in, Smartstream G1.6 1,598 cc, Copyright HYUNDAI Motor America. One engine in every year.

**⚠ QX LABELS — CORRECTED by the label audit above: label = model year is proved for 2020 (below) and 2021 only; `QX/2022` holds the 2023 book.** `QX/2020` has the same copyright year (2020) and the same page count (392) as the titled 2021 portal book, which looked like a shifted label (as on Santa Fe `TMa`). The maintenance grid settled it: `QX/2020` steps by 7,500 miles like the titled 2020 book; the titled 2021 book steps by 8,000. A later print of one model year resembles the next year's first print in everything except the values that changed between model years, so identify by such a value.

**Values (same in all three years unless a year is named):**

| Field | Value | Page |
|---|---|---|
| Engine oil | 4.02 qt / 3.8 L | 2-11 |
| Viscosity 2020 | 0W-20 recommended; chart also allows 5W-20, 0W-30, 5W-30 (all temperatures) and 10W-30 above 0 °F; API latest (SN PLUS), fallback API SL / ILSAC GF-3 / ACEA A3 | 2-12 (render) |
| Viscosity 2021, 2026 | 0W-20 only; API SN PLUS/SP or ILSAC GF-6, full synthetic required | 2-12 (render) |
| Manual transmission fluid (2020, 2021 books) | API GL-4 SAE 70W TGO-9, 1.59–1.69 qt / 1.5–1.6 L | 2-11 |
| Intelligent variable transmission fluid | CVTF SP-CVT1 (2026: MICHANG or Hyundai genuine); **quantity not written** | 2-11 |
| Coolant | phosphate-based ethylene glycol; manual 5.94 qt / 5.62 L; **automatic quantity not written** | 2-11 |
| Brake (/ clutch) fluid | SAE J1704 DOT-4 LV / FMVSS 116 DOT-4 / ISO 4925 Class 6; 0.74–0.85 qt / 0.7–0.8 L | 2-11 |
| Fuel tank | 11.89 gal / 45 L | 2-11 |
| Tires | 185/65R15 at 36 psi; 205/55R17 at 33 psi; front and rear; compact spare T125/80D15 or D16 at 60 psi | 2-9 |
| Wheel lug nut | 79–94 lb-ft (107–127 N·m, 11–13 kgf·m) | 2-9 |
| Steering | electric (EPS / MDPS), no fluid | text |

**⚠ UNIT CONFLICTS (unit ruling applied, "Go, as recommended" 2026-11-14):** every book prints the intelligent variable transmission fluid as `6.34 US qt. (6.7 L)` (6.7 L = 7.08 qt) and that transmission's coolant as `6.32 US qt. (5.78 L)` (5.78 L = 6.11 qt). Neither quantity is written. The 2020 / 2021 coolant column carries the manual-transmission figure only, labelled; the 2026 coolant quantity is null. The write script fails if any of the four figures reaches a shipped column.

**OM normal-schedule intervals written (20 rows; mi / mo):**

| Item | 2020 (p.8-8) | 2021 (p.8-8, 8-10) | 2026 (p.9-8, 9-10) |
|---|---|---|---|
| Engine oil & filter | 7,500 / 12 | 8,000 / 12 | 8,000 / 12 |
| Spark plugs | 97,500 | 96,000 / 144 | 96,000 |
| Air cleaner filter | 30,000 / 48 | 32,000 / 48 | 32,000 / 48 |
| Climate control / cabin air filter | 15,000 / 12 | 8,000 / 12 | 16,000 / 24 |
| Tire rotation | 7,500 | 8,000 | 8,000 / 12 |
| Coolant, first replacement | 120,000 / 120 | 120,000 / 120 | 120,000 / 120 |
| Coolant, thereafter | 30,000 / 24 | 24,000 / 36 | 24,000 / 24 |
| Brake fluid | inspect only — no row | 60,000 / 48 | 60,000 / 48 |

Grids are printed sideways; statement rows were decoded from text, grid rows (oil, air cleaner, cabin filter) read from upright renders. Exact page diffs (not similarity scores) confirmed the two prints agree for 2020 and 2021.

**Rulings on this slice (2026-11-14, "Go, as recommended"):** R1 the unit ruling as above; R2 the 2021 books still list a manual transmission → written as printed, marked "if equipped", for 2020 and 2021; R3 the 2020 severe-usage table is headed "Nu 2.0 MPI", an engine this vehicle does not have (both prints, gone from 2021 on) → severe rows are never written, and the 2020 normal schedule, which carries no engine label and is identical in both prints, is written.

**Gates (null):** spark-plug part number and gap, 12V battery (neither published) · numeric tire-pressure columns (pressure differs by wheel size, carried in the tire note) · differential (front-wheel drive only).

**Misprints noted:** `API Lastest` on the 2020 capacities table; the "Nu 2.0 MPI" heading above.

**No vehicle row exists** for Venue 2022–2025, though books do (portal `2022-Venue-Owners-Manual.pdf`, `2023-Venue-OM.pdf`, `2024 Venue OM.pdf`; second host `QX/2022`–`QX/2025`).

---

## ⛔ ACCENT — 0/8 DEFERRED (1995–2002, ids −140002 to −140009) — recon 2026-11-14
**DEFER, all eight rows: no manufacturer owner's manual is available for these years.** The US portal's Accent folder starts at 2005 — 552 filename probes across 1995–2006 found only `2005_Hyundai_Accent_OM.pdf` and `2006_Hyundai_Accent_OM.pdf`. The second host does not list Accent for the U.S.A at all. The eight rows have no curated data and stay that way (honest defer, not a gap). Nothing was written.

Portal Accent books that DO exist, for model years with no vehicle row: 2005, 2006, 2008, 2014 (`2014-Accent-Owners-Manual.pdf`), 2016, 2017, 2018 (`2018 Accent Owners Manual.pdf`), 2019 (`2019 Accent OM.pdf`), 2020 (`2020 Accent Owner's Manual.pdf`), 2021 (`2021 Accent OM.pdf`), 2022 (`2022-Accent-OM.pdf`); not found in 46 filename forms each: 2007, 2009–2013, 2015. Existence probes only — none was downloaded or read.

**Re-checked 2026-11-14 with a status-aware probe** (see the probe tooling incident in the Veloster / Santa Cruz section): 21 filename forms for each of 1995–2004 returned HTTP 404; the core forms for 2007, 2009–2013 and 2015 returned HTTP 404. The defer stands. **Update 2026-11-14 (later the same day):** rows were added for the eleven later years that do have a book — see the Accent rows section near the top. The eight 1995–2002 rows stay deferred.

---

## ✅ RE-READ — 8 rows (Sonata 2006/2018/2021/2024 + Elantra 2017/2020/2021/2022) — `2026-11-14-hyundai-reread`, commit a1950c1b — EIGHTH HYUNDAI SLICE
> **2026-11-14 label audit:** the Sonata 2021 G2.5 T-GDI values and the Elantra 2021 G1.6 T-GDi values described below were REMOVED (see the LABEL AUDIT section at the top) — the books they came from are not proved to be 2021 books. The Elantra 2022 'edition conflicts' below were model-year differences.
Recon, reads, write and deploy all 2026-11-14 (live confirmed 14:43:59, blob `data.abf31de5.js` byte-identical to the local build at 14:44:01, CI green). Write script `_write_hyundai_sonata_elantra_reread.py`, which supersedes `_write_hyundai_sonata.py` and `_write_hyundai_elantra.py` for these ids. Backup `wrench_vehicles.db.bak_reread_20261114_143853`. No new vehicle: the fleet tally stays 317.

**Why:** the eight rows written in the July pilot were in a thin format — one placeholder maintenance row with no interval, no tire pressures or trim note, capacities stored as quarts with no metric figure, no differential entries. Each was re-read from the same manual(s) and rewritten to the current standard. An inventory query found the eight; the first estimate from memory was four.

**⚠ THREE LIVE VALUES WERE WRONG (all on rows carrying a verified badge), now corrected:**

| Row | Was live | What the manual prints |
|---|---|---|
| Sonata 2006 (id 11226) | spark plugs "SK16PR-A11 / IFR5G-11" with a gap | **no plug number or gap anywhere** — text of all 276 pages searched, engine table p.9-3 rendered → removed |
| Sonata 2006 (id 11226) | power steering "PSF-3 type fluid" | **PSF-4 type fluid** (lubrication chart p.9-4, rendered) |
| Sonata 2018 (id 12523) | viscosity 5W-20 for a row covering three engines | 5W-20 for the 2.4 GDI only; **5W-30 for the 1.6 T-GDI and 2.0 T-GDI** (p.8-9) |

Also brought into line on Sonata 2024 (id 13049): the dual clutch quantities were single rounded figures (3.5 qt and 2.6 qt) and now carry the printed ranges with litres (3.49-3.59 qt / 3.3-3.4 L and 2.59-2.64 qt / 2.45-2.5 L); the AWD rear differential and transfer case entries were missing and were added.

**⚠ FROZEN ROWS:** seven of the eight ids hold a wheel-nut torque row whose source is the bare token (part of the 424 frozen grandfathered rows). A full rewrite would have dropped the freeze to 417. Their values match the manuals (79 lb-ft / 107 N·m), so they were left untouched: the script never deletes from `torque_specs` for them, asserts each is as expected, and checks the bare count BEFORE commit. Only Sonata 2006 gained a torque row (65–80 lb-ft, p.3-11), with a citation suffix.

| Row | Books | Engines | Oil | Visc | Coolant |
|---|---|---|---|---|---|
| **Sonata 2006 NF** (id 11226) | portal, single print | 2.4L + 3.3L | 4.54 qt / 4.3 L · 6.02 qt / 5.7 L | 5W-20 or 5W-30; 10W-30 above 0 °F | 6.87 / 6.66 / 8.66 qt |
| **Sonata 2018 LF** (id 12523) | portal, single print | 1.6T + 2.0T + 2.4 | 4.75 qt / 4.5 L · 5.07 qt / 4.8 L ×2 | 5W-30 turbo / 5W-20 2.4 | 7.50 / 7.92 / 7.60 qt |
| **Sonata 2021 DN8** (id 12853) | portal first print + later print | 1.6T + 2.5 + 2.5T | 5.07 qt / 4.8 L (1.6T) · 6.13 qt / 5.8 L (2.5T); 2.5 not written | 0W-20 / 0W-30 (2.5T) | 8.59 qt / 8.13 L (2.5T); others not written |
| **Sonata 2024 DN8 facelift** (id 13049) | portal first print = later print | 2.5 + 2.5T | 6.13 qt / 5.8 L both | 0W-20 / 0W-30 | 9.2 qt / 8.7 L · 9.3 qt / 8.8 L |
| **Elantra 2017 AD** (id 12379) | portal, single print | Nu 2.0 MPI | 4.23 qt / 4.0 L | 5W-20 | 6.34 / 6.97 qt |
| **Elantra 2020 AD facelift** (id 669) | portal, single print | 2.0 MPI + 1.6T | 4.23 qt / 4.0 L · 4.76 qt / 4.5 L | 5W-20 / 5W-30 | 6.45 / 6.34 / 6.97 qt |
| **Elantra 2021 CN7** (id 2163) | portal first print + `CN7a` + `CN7` later prints | G2.0 + G1.6T | 4.54 qt / 4.3 L · 5.07 qt / 4.8 L | 0W-20 | 7.82 qt / 7.4 L · 7.19 qt / 6.8 L |
| **Elantra 2022 CN7** (id 3691) | portal first print + `CN7` + `CN7a` later prints | G2.0 + G1.6T | same | 0W-20 | same |

**Engines only a later print carries (ruling 2026-11-14, written from that print, the source says so):** Sonata 2021 Smartstream G2.5 T-GDI (oil, 0W-30, wet dual clutch fluids, coolant, 48,000-mile plugs) and Elantra 2021 Smartstream G1.6 T-GDi (oil, dual clutch and manual transmission fluid, coolant, 235/40R18 tire, 47,000-mile plugs). The 2021 Elantra's titled first print is the America-built variant and covers the 2.0 only.

**Not written, and why (reasons live in the `source` suffix):**

| Row | Value | What the books say | Rule |
|---|---|---|---|
| Sonata 2021 | G2.5 GDi oil capacity | first print 5.49 qt / 5.2 L; later print 6.13 qt / 5.8 L | edition conflict (standing from the audit) |
| Sonata 2021 | coolant for G1.6 T-GDi and G2.5 GDi | first print 4.76 qt / 4.5 L and 5.49 qt / 5.2 L (they echo the oil figures); later print 8.03 qt / 7.6 L and 9.07 qt / 8.59 L | edition conflict |
| Elantra 2022 | G1.6 T-GDi spark-plug interval | first print 47,000 mi; later print 48,000 mi | whole rows only |
| Elantra 2022 | coolant interval after the first replacement | 30,000 mi (first print, `CN7a`); 24,000 mi (`CN7`) | first replacement only |
| Elantra 2022 | tire-rotation months | none in the first print; 12 in the later prints | 8,000 mi written, no months |
| Sonata 2018 | brake-fluid quantity | "0.7~0.8 US qt (0.7~0.8 l)" | same numbers for both units — spec only |
| Sonata 2006 | cold tire pressure | the book refers to the vehicle placard | not published |

**OM normal-schedule intervals written (64 rows replacing 8 placeholders; mi / mo):** Sonata 2006 (5; grid p.5-4/5-5) — oil 7,500 / 6, plugs 97,500 / 78, air cleaner 30,000 / 24, A/C filter 10,000 / 12, coolant first 60,000 / 60 then 30,000 / 24. Sonata 2018 (11) — turbo p.7-10: oil 6,000 / 12, plugs 42,000, air cleaner 18,000 / 36, climate filter 6,000 / 12, rotation 6,000; 2.4 p.7-15: 7,500 / 12, 97,500, 22,500 / 36, 7,500 / 12, 7,500; coolant first 120,000 / 120 then 30,000 / 24. Sonata 2021 (9) — oil 8,000 / 12, plugs 40,000 / 60 (1.6T, grid marks) · 96,000 (2.5) · 48,000 (2.5T), air cleaner 24,000 / 36, climate filter 16,000 / 24, rotation 8,000, coolant first 120,000 / 120 then 30,000 / 24, brake fluid 48,000 / 48. Sonata 2024 (8; p.9-11 to 9-14) — oil 8,000 / 12, plugs 96,000 (2.5) · 48,000 (2.5T), air cleaner 24,000 / 36, cabin filter 16,000 / 24, rotation 8,000 / 12, coolant first 120,000 / 120 then 24,000 / 24, brake fluid 48,000 / 48. Elantra 2017 (6; list-style p.7-8+) — oil 7,500 / 12, plugs 97,500 / 78, air cleaner 30,000 / 24, climate filter 15,000 / 12, rotation 7,500 / 6, coolant first 120,000 / 120 then 30,000 / 24. Elantra 2020 (10) — 2.0 p.7-8: oil 7,500 / 12, plugs 97,500, air cleaner 30,000 / 48, rotation 7,500; 1.6T p.7-13: 6,000 / 12, 42,000, 24,000 / 48, 6,000; climate filter every 12 months (no mileage printed); coolant first 120,000 / 120 then 30,000 / 24. Elantra 2021 (8; p.9-8 to 9-10) — oil 8,000 / 12, plugs 96,000 (2.0) · 47,000 (1.6T), air cleaner 24,000 / 36, cabin filter 16,000 / 24, rotation 8,000, coolant first 120,000 / 120 then 30,000 / 24, brake fluid 48,000 / 48. Elantra 2022 (7) — as 2021 without the 1.6T plug row, coolant first replacement only.

**Gates (null):** plug PN/gap in all eight · 12V battery except Sonata 2006 (MF68AH, Electrical table p.9-2) · EPS / MDPS except Sonata 2006 (hydraulic, written) · numeric tire-pressure columns for Elantra 2017 / 2020 (pressure differs by wheel size, so it is carried in the tire note).

**Left open:** whether to re-pin the freeze so the seven wheel-nut rows can carry citation suffixes like every other row.

---

## ✅ NEWEST-YEAR BACKFILL — 7 rows (Sonata 2025/2026 + Tucson 2025/2026 + Elantra 2024/2025/2026) — `2026-11-14-hyundai-newest-years`, commit 60895598 — SEVENTH HYUNDAI SLICE
> **2026-11-14 label audit:** the two-figure Tucson 2024 coolant described below was REVERTED to the single figure from the titled 2024 book (see the LABEL AUDIT section at the top).
Recon, reads, write and deploy all 2026-11-14 (live-confirmed 14:05 CST: kyr-version 2026-11-14-hyundai-newest-years, live blob data.d57ca1e3.js md5 = local, previous blob 404). Write script `_write_hyundai_newest_years.py` (dry-run default; asserts each target id's year/make/model; quart/litre and gallon/litre checks, gallon tolerance following the printed precision; guard against any US unit without a paired metric figure). Backup `wrench_vehicles.db.bak_newest_years_20261114_135816`. The US portal has no book for 2025–2027 on any of the three nameplates (1,320 probes) and only an abridged 2024 Elantra, so each row has one available print, from the second host. Hybrid, Plug-in Hybrid and N have their own books and are not written.

**Identity:** every book identified by wheelbase + engine table + copyright year; the label is the model year for all seven. Sonata `DN8` label 2025 (header `DN8_FL`, Copyright 2025) and 2026 (Copyright 2026). Tucson label 2025 exists as `NX4` AND `NX4a` (both Copyright 2025, facelift length 182.6 in) and the two agree on every page read; label 2026 `NX4` is complete (PDF keywords name 2026) while the `NX4a` 2026 file has no capacities chapter and no schedule tables. Elantra `CN7` label 2024 (header `CN7_PE`, Copyright 2023), 2025 (keywords name 2025, Copyright 2024) and 2026 (keywords name 2026, Copyright 2026) are served by the host but absent from its US menu, which stops at `CN7a` label 2023 — accepted by ruling 2026-11-14.

| Row | Engines | Oil (drain and refill) | Visc | Coolant | Trans |
|---|---|---|---|---|---|
| **Sonata 2025** (id 13115) | Smartstream G2.5 GDI + G2.5 T-GDI | **6.13 qt / 5.8 L** both | 0W-20 / 0W-30 | 9.2 qt / 8.7 L · 9.3 qt / 8.8 L | ATF SP4M-1 6.8 qt / 6.5 L; turbo wet dual clutch 3.49–3.59 + 2.59–2.64 qt |
| **Sonata 2026** (id 13181) | same | same | same | same | same |
| **Tucson 2025** (id 8358) | Smartstream G2.5 GDI | 6.13 qt / 5.8 L | 0W-20 | **8.99 qt / 8.51 L** | **ATF SP4M-1** 6.87 qt / 6.5 L |
| **Tucson 2026** (id 9972) | same | same | same | same | same |
| **Elantra 2024** (id 6785) | Smartstream G2.0 + G1.6 T-GDi | 4.54 qt / 4.3 L · 5.07 qt / 4.8 L | 0W-20 both | 7.82 qt / 7.4 L · 7.19 qt / 6.8 L | IVT SP-CVT1 6.87 qt / 6.5 L; dual clutch 1.7–1.8 qt / 1.6–1.7 L |
| **Elantra 2025** (id 8360) | same | same | same | same | same |
| **Elantra 2026** (id 9974) | same | same | same | same | same (adds MICHANG CVTF SP-CVT1) |

Common: wheel nut **79–94 lb-ft** · EPS / MDPS · full synthetic oil required in all seven · Sonata rear differential 0.62 qt / 0.58 L and transfer case 0.69 qt / 0.65 L (AWD), tires 215/55R17, 235/45R18, 245/40R19 @ 35 (**2026 adds 205/65R16**), fuel 15.9 gal / 60 L · Tucson rear differential 0.56–0.67 qt / 0.53–0.63 L and transfer case 0.65–0.71 qt / 0.62–0.68 L (the 2025 book says 4WD, the 2026 book AWD; written as printed), brake fluid 0.87 qt / 0.82 L, tires 235/65R17, 235/60R18, 235/55R19 @ 35, fuel 14.26 gal / 54 L · Elantra brake fluid 0.74–0.85 qt / 0.7–0.8 L, tires 195/65R15, 205/55R16, 225/45R17 @ **34 front / 31 rear** and 235/40R18 @ 33 / 33, fuel 12.4 gal / 47 L, front-drive only (no differential entries). Every viscosity chart was read from a page render and agrees with its capacities table (the Sonata turbo is 0W-30 in both — no internal conflict, unlike Santa Fe 2021).

**★ PLANT BOOKS and the correction to a live row.** The second host carries two books per year for some nameplates: a bare code and the same code + `a` (`NX4` / `NX4a`, `CN7` / `CN7a`). The US menu lists both Tucson codes; the US territories list only `NX4`. The `a` book is read as the America-built vehicle (an inference from the code and the listing — the books do not print it). Checked against the live rows:

| Live row | Result |
|---|---|
| Tucson 2022 (id 3689) | every written value agrees in both books |
| Tucson 2023 (id 5210) | the titled portal 2023 book IS the `a` book; the bare-code 2023 file has no capacities chapter, so there is no second opinion |
| **Tucson 2024 (id 6783)** | **coolant 10.04 qt / 9.5 L in the portal book and `NX4`, 10.11 qt / 9.57 L in `NX4a`**; everything else agrees → the row now carries both figures, unattributed (ruling 2026-11-14) |
| Elantra 2021–2023 | 2.0 values identical in `CN7` and `CN7a` (`CN7a` does not cover the 1.6 T-GDi) |

**Gates (null):** plug PN/gap (interval only) · 12V battery (capacity-label illustration only: AGM70L-DIN, or CMF60L-DIN / AGM70L-DIN in Elantra) · EPS / MDPS · Hybrid / Plug-in Hybrid / N.

**OM normal-schedule intervals written (54 rows; mi / mo), the same in all seven books:** oil 8,000 / 12 · air cleaner 24,000 / 36 · cabin filter 16,000 / 24 (grid read from renders) · rotation 8,000 / 12 · coolant first 120,000 / 120 then 24,000 / 24 · brake fluid 48,000 / 48 · spark plugs 96,000 (48,000 for the Sonata 2.5 T-GDI and the Elantra 1.6 T-GDi). Pages: Sonata p.9-11 to 9-14; Tucson 2025 p.9-11 to 9-15, 2026 p.654–658; Elantra 2024 p.9-11 to 9-14, 2025 p.594–597, 2026 p.596–599.

**Noted, not in scope:** the four July rows (Elantra 2021 / 2022, Sonata 2021 / 2024) are in the older thin format — one placeholder maintenance row, no tire pressures on Elantra, no AWD entries on Sonata 2024 — and could be re-read to the current standard.

---

## ✅ PALISADE — 6/6 (2020/2021/2022 LX2 + 2024/2025 LX2 facelift + 2026 LX3) — `2026-11-14-hyundai-palisade`, commit 8f0eb6b4 — SIXTH HYUNDAI
Recon, reads, write and deploy all 2026-11-14 (live-confirmed 12:41 CST: kyr-version 2026-11-14-hyundai-palisade, live blob data.26a62823.js md5 = local, previous blob 404). Write script `_write_hyundai_palisade.py` (dry-run default; asserts the six target ids are exactly the Palisade rows; quart/litre, gallon/litre and quart/millilitre checks on every shipped pair, plus a guard against any US unit shipping without a paired metric figure). Backup `wrench_vehicles.db.bak_palisade_20261114_123105`. Three book families, every year read on its own pages; the 2026 Hybrid has its own manual and is not written. The vehicles table has no 2023 Palisade row.

**Identity (ruling 2026-11-14, "Accept, go read"):** for this nameplate the second host's year label IS the model year. Labels 2021, 2022 and 2023 each match the US-portal book whose PDF Title names that year (2022: every page, zero strays; 2021 and 2023: later prints of the titled book). Labels 2024 (Copyright 2023, PDF created 2023-10-23) and 2025 (Copyright 2025, created 2025-04-24) have no titled portal book and are accepted on that proven sequence plus the book header `LX2_PE_en_US` and body / engine self-ID. 2026 is LX3; its PDF keywords name 2026. **Note added 2026-11-14:** the statement about label 2023 was made without a test against the 2024 book; it is now proved (PDF created 2023-04-04, before the 2024 book; none of the 2024 book's new wording), and the same check found that this later print names a different transmission fluid than the titled first print — see the PALISADE 2023 section.

| Row | Engine | Oil (drain and refill) | Visc | Coolant | Trans |
|---|---|---|---|---|---|
| **2020 LX2** (id 676) | 3.8 GDI 3,778cc | **6.87 qt / 6.5 L** | 5W-30; 10W-30 above 0 °F | 9.4 qt / 8.9 L | ATF SP-IV 7.4 qt / 7.0 L |
| **2021 LX2** (id 2169) | same | 6.87 qt / 6.5 L | 5W-30; 10W-30 above 0 °F | 9.4 qt / 8.9 L | ATF SP-IV 7.4 qt / 7.0 L |
| **2022 LX2** (id 3697) | same | **1.71 gal / 6.5 L** (as printed) | 5W-30 only | 2.35 gal / 8.9 L | ATF SP-IV 1.85 gal / 7.0 L |
| **2024 LX2 facelift** (id 6790) | same | 6.86 qt / 6.5 L | 5W-30, full synthetic required | **12.44 qt / 11.79 L** (12.65 / 11.98 with trailer) | **ATF SP4M-1** 7.39 qt / 7.0 L |
| **2025 LX2 facelift** (id 8365) | same | 6.86 qt / 6.5 L | 5W-30, full synthetic required | same | same |
| **2026 LX3** (id 9979) | Smartstream G3.5 GDi 3,470cc | **6.13 qt / 5.8 L** | 0W-20, full synthetic required | 12.44 qt / 11.77 L | ATF SP4M-1 7.39 qt / 7.0 L |

Common: wheel nut **79–94 lb-ft** every year · EPS / MDPS · brake DOT-4 (2024+ DOT-4 LV) · rear differential and transfer case GL-5 75W/85: 0.74 qt / 0.7 L each (2020/2021), 0.19 gal / 0.7 L each (2022), 0.73 qt / 0.7 L each (2024/2025), 0.67 qt / 0.65 L and 0.74 qt / 0.7 L (2026) · 2026 XRT Pro electronic limited slip differential: Shell TF0870C, 0.507 qt / 480 mL · tires 245/60R18, 245/50R20 @ 35 (2020–2025); 235/65R18, 255/50R20, 265/45R21 @ 36 and XRT Pro 255/60R18 @ 35 (2026) · fuel 18.75 gal / 71 L (2020–2025), 19 gal / 72 L (2026). Viscosity charts and the 2026 tire table were read from page renders.

**Rulings applied (2026-11-14, "Go, write Palisade"), and what is not written (reasons live in the `source` suffix):**

| Row | Value | What the books say | Rule |
|---|---|---|---|
| 2021 | Brake fluid interval | first print grid 30,000 mi / 48 months; later print "60,000 miles or 48 months" | whole rows only — not written |
| 2022 | Oil, air cleaner, rotation, cabin filter intervals; coolant interval after the first replacement | first print grid in 7,500-mile steps (some of its sentences already on the 8,000-mile basis); later print 8,000 throughout | whole rows only — not written; spark plugs, first coolant replacement and brake fluid agree and are written |
| 2022 | Capacities | both prints give US gallons beside litres | written as printed; gallon/litre check |
| 2021 | Capacities | first print US quarts, later print US gallons, same litres | one quantity — quarts written |
| 2024, 2025, 2026 | 12V battery | capacity-label illustration only (AGM80L-DIN; 2024/2025 captioned "may differ from the illustration") | not a vehicle spec (Tucson ruling) |

**Gates (null):** plug PN/gap every year (interval only) · 12V battery every year · EPS / MDPS · 2026 Hybrid.

**★ Carry outcomes (engine predicts, the OM decides):** the 3.8 GDI holds 6.5 L of oil from 2020 to 2025, but the permitted grades narrow (10W-30 dropped for 2022), the coolant fill grows from 8.9 L to 11.79 L at the facelift, and the ATF changes from SP-IV to SP4M-1 (the 2023 first print still says SP-IV and its later print SP4M-1 — the same pattern as Santa Fe 2023). First slice with capacities printed in gallons, with a later print that changes the UNIT of a capacity, and with a later print that changes the service schedule.

**OM normal-schedule intervals written (36 rows; mi / mo):** 2020, 2021 (6 each; p.7-8 to 7-10) — oil 7,500 / 12, plugs 97,500, air cleaner 22,500 / 36, climate control air filter 7,500 / 12, rotation 7,500, coolant first 120,000 / 120 then 30,000 / 24 (brake fluid is inspect-only in 2020). 2022 (3) — plugs 96,000, coolant first 120,000 / 120, brake fluid 48,000 / 48. 2024, 2025 (7 each; p.9-9 to 9-11) and 2026 (7; p.567–569) — oil 8,000 / 12, plugs 96,000, air cleaner 24,000 / 36, cabin filter 16,000 / 24 (**the 2025 book prints 24 months with no mileage**), rotation 8,000 / 12, coolant first 120,000 / 120 then 24,000 / 24, brake fluid 48,000 / 48.

---

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
> **2026-11-14 label audit:** `OS/2022` holds the 2023 book and `OS/2020` is unproved, so the Kona 2022 'print conflicts' below were model-year differences; `OS/2021` is proved, so the Kona 2021 conflict is real (see the LABEL AUDIT section at the top).
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
> **2026-11-14: every row in this section was RE-READ and rewritten — see the RE-READ section at the top. What follows is the July record, kept for history; three of its values were wrong (Sonata 2006 spark plugs and power-steering fluid, Sonata 2018 oil grade).**
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
> **2026-11-14: every row in this section was RE-READ and rewritten — see the RE-READ section at the top. What follows is the July record, kept for history; three of its values were wrong (Sonata 2006 spark plugs and power-steering fluid, Sonata 2018 oil grade).**
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
