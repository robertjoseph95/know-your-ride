# KYR — Hyundai Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified · FIRST Hyundai Motor Group make

Parallel to the GM-group / Ford / Honda / Nissan / Mazda / Subaru logs. Make characterization + reusable
source pattern in `KYR_OEM_Manual_Source_Map.md` (Hyundai section). **Host:** `owners.hyundaiusa.com` MyHyundai
glovebox-manual (free, no auth, citable manufacturer source). **This is the HMG foundation — it pre-characterizes
Kia (~80 rows / 12 nameplates), and specifically Optima/K5 as a near-twin of the Sonata (shared platform + Theta II/Smartstream engines).**

> **Hyundai status (2026-11-14, after the Veloster / Santa Cruz slice): 47 rows, all at the current standard.** **Sonata 6/14** · **Elantra ✅ 7/13** · **Tucson ✅ 8/10** · **Kona ✅ 5/5** · **Santa Fe ✅ 9/13** · **Palisade ✅ 6/6** · **Venue ✅ 3/3** · **Veloster ✅ 2/3 (2020 deferred)** · **Santa Cruz ✅ 1/1** · **Accent ⛔ 0/8 (deferred, no manufacturer manual before 2005)**. Two manufacturer hosts are in use (US portal = first print, `ownersmanual.hyundai.com` = later print); the second host also carries plant-specific books (a bare code and the same code + `a`). Values two prints contradict, values a book contradicts internally, and capacities whose units do not convert are not written; a maintenance row whose interval two prints dispute is left out whole; a value two plant books give differently ships with both figures, unattributed; an engine only a later print carries is written from that print. **⚠ Label audit 2026-11-14: a second-host year label is NOT automatically the model year — three labels hold the next year's book and four are unproved; see the LABEL AUDIT section. Row corrections are in progress.** DB also has Tiburon (1997–2002, not probed; the portal floor has been 2005 for every nameplate checked) and Ioniq (EV) — pending. **Kia does NOT cheaply unlock** (source boundary — full OMs behind a JS viewer; queued viewer-spike). **Next Hyundai:** nothing queued. Every Hyundai vehicle row that has a manufacturer book is now written; what remains is deferred for lack of a book, electrified, or has no vehicle row (Venue 2022–2025, Santa Cruz 2022–2025, Accent 2005+, Palisade 2023, Kona 2018 / 2019 / 2023 / 2025).

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

**No vehicle row exists** for Santa Cruz 2022–2025, though books do (portal `2022-Santa-Cruz-Owners-Manual.pdf`; second host `NX4OB` labels 2021–2025).

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

**Re-checked 2026-11-14 with a status-aware probe** (see the probe tooling incident in the Veloster / Santa Cruz section): 21 filename forms for each of 1995–2004 returned HTTP 404; the core forms for 2007, 2009–2013 and 2015 returned HTTP 404. The defer stands.

---

## ✅ RE-READ — 8 rows (Sonata 2006/2018/2021/2024 + Elantra 2017/2020/2021/2022) — `2026-11-14-hyundai-reread`, commit a1950c1b — EIGHTH HYUNDAI SLICE
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

**Identity (ruling 2026-11-14, "Accept, go read"):** for this nameplate the second host's year label IS the model year. Labels 2021, 2022 and 2023 each match the US-portal book whose PDF Title names that year (2022: every page, zero strays; 2021 and 2023: later prints of the titled book). Labels 2024 (Copyright 2023, PDF created 2023-10-23) and 2025 (Copyright 2025, created 2025-04-24) have no titled portal book and are accepted on that proven sequence plus the book header `LX2_PE_en_US` and body / engine self-ID. 2026 is LX3; its PDF keywords name 2026.

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
