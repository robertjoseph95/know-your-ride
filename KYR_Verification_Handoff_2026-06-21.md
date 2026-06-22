# KYR Spec-Verification Campaign — Session Handoff
**Date:** 2026-06-21 · **Status as of this handoff:** 99 vehicles verified, 14 nameplates, 5 makes · live prod version `2026-06-21-ford-mustang`

This document hands off the owner's-manual spec-verification campaign for KYR (Know Your Ride / knowyourride.net) so a fresh session can continue without re-deriving context.

---

## 1. What the campaign is

Flip AI-fabricated (`ai-haiku-4.5` / `scraped`) curated specs to genuinely **owner's-manual-verified, manufacturer-sourced, page-cited** data. The **Data Integrity Gate** (shipped earlier, commit `6f983297`) auto-hides any unverified spec behind `specSoon()` "pending verification" in the UI — so the discipline is: **verify to a manufacturer source or leave it gated. NEVER write a spec value without an authoritative source.**

- `_ver()` in `files/04_rebuild_demo.py` computes a `ver` boolean per spec. Verified = source contains `owner-manual` / `service-manual` / `vpic` / `epa` / `nhtsa` AND not `ai-`/`haiku`/`scraped`.
- Gated tables: `oil_change, fluids, parts, torque_specs, engine_specs, maintenance` (each has a `source` column).
- Government tables (NOT gated, always shown): `fuel_economy, recalls, safety_ratings, complaints, tsb, warranty, reliability, epa_data, vpic_specs`.
- Raw source string is NOT shipped to users (only the `ver` boolean) — internal model names never leak.

Canonical references in the repo: `KYR_Source_Authority_Matrix.md`, `KYR_Verification_Pipeline_Design.md`, `KYR_Data_Inconsistencies_To_Fix.md`, and the per-make logs (`KYR_Ford_Verification_Log.md`, `KYR_Nissan_Verification_Log.md`, `KYR_Honda_Verification_Log.md`, `KYR_Mazda3_Spec_Verification_Log.md`).

---

## 2. The proven workflow (repeat per nameplate)

1. **DB inventory:** list the nameplate's rows by year, identify generation(s), confirm which are gated vs done. Query `vehicles LEFT JOIN oil_change` on `source`.
2. **EPA per-year roster** (the standing rule — roster is NOT generation-stable): `fueleconomy.gov/ws/rest/vehicle/menu/model?year=&make=` → models; `menu/options?...&model=` → trims. Pin engine availability **per year** (additions/drops). vPIC returns only ONE engine/year for multi-engine vehicles → unreliable for Ford; **use EPA**.
3. **Download the OM** via **chunked range-request** (Ford/Lincoln throttle large PDFs — plain GET/curl/WebFetch time out). Pattern below.
4. **Source-confirmation gate:** confirm page 1 self-IDs the year+model (or the footer edition date). Pre-2008 manuals that don't self-ID → HELD/gated.
5. **Extract the Capacities & Specifications chapter**, page-cited: oil cap/viscosity, coolant (color/spec), brake, transmission (fluid + speed), PS type, lug torque, battery group, per-engine Motorcraft part #s.
6. **CONFIRM-DON'T-ASSUME** — read every field; siblings/generations diverge (see §4 lessons).
7. **NULL/gate** what the OM doesn't carry: drain-plug torque, oil-filter torque, spark-plug gap, tire size/pressure when placard-only, halo/EV variants without clean OM coverage.
8. **Write** a `_write_<name>.py` script: backup DB (`shutil.copy2`), DELETE the 6 spec tables for each vehicle, INSERT per-year/per-engine multi-value strings, `source='owner-manual-verified (...)'`.
9. **Rebuild** → `python files/04_rebuild_demo.py` (produces `wrench_demo.html`).
10. **Preview-verify** via the preview MCP (`window.location.href='http://localhost:8752/wrench_demo.html'`, then `__D__.v.find(x=>x.id===ID)` — check the generational/per-engine distinctions render + `ver===1`).
11. **Deploy:** `KYR_NEW_VER='2026-06-21-<name>' python _deploy_sync_specs.py` → commit (add `wrench_demo.html`, `wrench_deploy/index.html`, new `wrench_deploy/data.*.js`, `git rm --cached` the old data file) → `git push origin main` → poll `knowyourride.net` for the `kyr-version` meta.
12. **Update** the per-make log + the `data-integrity-gate.md` memory tally.

**ALWAYS show the verification log and pause for user review BEFORE writing.** Map inventory + flag EV/halo variants BEFORE downloading.

### Chunked range-request download (the Ford workaround)
```python
import urllib.request
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
r=urllib.request.urlopen(urllib.request.Request(url,headers=dict(UA,Range='bytes=0-1')),timeout=40)
total=int(r.headers.get('Content-Range').split('/')[1])
buf=bytearray(); CH=512*1024; pos=0; fails=0
while pos<total and fails<8:
    end=min(pos+CH-1,total-1)
    try:
        d=urllib.request.urlopen(urllib.request.Request(url,headers=dict(UA,Range='bytes=%d-%d'%(pos,end))),timeout=45).read()
        buf+=d; pos+=len(d); fails=0
    except: fails+=1
open(fn,'wb').write(buf)  # if buf[:4]==b'%PDF' and len>=total*0.98
```
Ford/Lincoln OM URL pattern: `fordservicecontent.com/Ford_Content/Catalog/owner_information/<YEAR>-Ford-<MODEL>-Owners-Manual-version-N_om_EN-US_<MM_YYYY>.pdf` (date suffix varies — web-search to confirm exact URL). Extract text with `pdfplumber`; write to UTF-8 file then Read (avoids cp1252 UnicodeEncodeError on ℓ/∙ and the false-positive content classifier on big Bash reads).

---

## 3. DONE so far — 99 vehicles / 14 nameplates / 5 makes

| Make | Nameplates verified | Count |
|---|---|---|
| **Ford** | F-150 (13th+14th gen ×12), Explorer 6th (×7), Escape 4th (×6), Mustang gas S550+S650 (×5) | 30 |
| **Lincoln** | Aviator 2nd gen (×7) | 7 |
| **Nissan** | Rogue ×12, Altima ×7, Sentra ×6, Pathfinder ×5, Maxima ×3 | 33 |
| **Honda** | Civic ×7, CR-V ×5, Accord ×4 | 16 |
| **Mazda** | Mazda 3 (2005–2017 ×13) | 13 |

Recent commits (newest first): `674ef14c` mustang · `b5186f6e` aviator · `e8301703` f150-bulk · `e265d933` explorer · `f1ddc624` nhtsa-backfill · `2879eb1f` epa-mpg-backfill · `93c4a03e` escape.

### Government-API backfill (separate, COMPLETE for the 127 cohort)
The 127 never-pulled vehicles (ids ≥38591) were filled: EPA MPG (96/114, 511 rows), NHTSA recalls/safety/complaints (all 127 logged). `pull_log` is the audit instrument (status ok/empty). **OPEN:** broader complaints gap (~1,849 vehicles) HELD pending a one-time logging-sweep decision; `tsb`/`warranty`/`reliability` correctly not pulled (wrong source/derived). Reusable pullers: `_pull_epa_mpg.py`, `_pull_nhtsa.py`. Anchor never-pulled cohorts on the `recalls` endpoint (not "logged anything" — that shrinks after each pull).

---

## 4. Hard-won CONFIRM-DON'T-ASSUME lessons (do not re-learn these)

- **Engine roster is NOT generation-stable** — verify per YEAR via EPA. (Explorer hybrid dropped 2024; F-150 V6→3.3 in 2018, diesel 2018–2021, 5.2 Raptor R added 2023; Mustang V6 dropped 2018; Aviator PHEV dropped 2024.)
- **Coolant color is generation-specific** — F-150 13th gen = **Orange** (WSS-M97B44-D2), 14th gen = **Yellow** (WSS-M97B57-A2). Always read.
- **Transmission fluid & speed are NOT nameplate/generation-stable:** F-150 = MERCON **LV**, 6-spd(6R80)→10-spd(10R80); Explorer/Aviator (CD6) = MERCON **ULV**, 10-spd(10R60); Escape = MERCON ULV 8-spd / eCVT hybrid. **Mustang manual fluid varies by GEARBOX** (MT82 = Dual Clutch Fluid XT-11-QDC, NOT MERCON; Tremec TR-3160 = MERCON LV; auto 10R80 = MERCON LV).
- **Engine-specific fields travel with the ENGINE; generation fields travel with the GENERATION** (e.g., 2021 F-150 diesel = engine's own oil spec + 14th-gen Yellow coolant).
- **Battery group varies by trim** — F-150 48/94R, Aviator 94R (luxury), Mustang S550 96R, Mustang S650 = OM punts to dealer → GATE.
- **Lug torque:** trucks/Explorer/Aviator/Mustang all M14×1.5 @ **150**; Escape M12×1.5 @ **100**. Read it.
- **Corporate twins are a HYPOTHESIS, not a shortcut** — read the sibling's own OM (Aviator confirmed Explorer's MERCON ULV/Yellow/EPAS but diverged on battery 94R + PHEV).
- **If a spec isn't literally in the OM**, pull an authoritative manufacturer source rather than infer (Aviator 10-speed came from `media.lincoln.com` tech-specs, not the OM).
- **EV trap:** Mach-E / Lightning / Leaf / Bolt / Ioniq / EV6 / Solterra etc. are NOT the gas vehicle — NEVER write gas specs. Confirm no Lightning/Mach-E rows get oil/trans. They need a separate EV-spec method.
- **Halo variants without clean OM coverage** (5.2 Raptor R, 5.2 GTD/Shelby, GT350/GT500): GATE, don't fabricate.

---

## 5. PRIORITIZED WORKLIST (next targets — reviewed, not started)

Full fleet = 1,976 live vehicles. Ranked by gated (unverified) count.

**Make-level gated totals:** Toyota 189 · Chevrolet 128 · Honda 112 (16 done) · Ford 100 (30 done) · BMW 93 · Subaru 78 · Hyundai 77 · Nissan 77 (33 done) · VW 75 · Audi 60 · Kia 60 · Cadillac 58 · Dodge 53 · GMC 52 · Porsche 50 · Jeep 49 · Mazda 49 (13 done) · Lincoln 39 (7 done) · … · **Tesla 28 (all EV)**.

### Top reachable-make nameplates to verify next (gated count)
- **Ford (finish the make):** Ranger (10), Expedition (7), F-250 (6), Bronco (5), Focus (5), F-350 (4), Maverick (4), Edge (3), Bronco Sport (3).
- **Chevrolet (GM portal, 0 done):** Silverado 1500 (21), Suburban (13), Tahoe (13), Camaro (12), Equinox (9), Colorado (8), Corvette (7), Malibu (7).
- **Subaru (0 done):** Outback (20), Forester (17), Impreza (10), WRX (10), Crosstrek (7), Ascent (4), BRZ (4).
- **Hyundai (0 done):** Sonata (14), Elantra (13), Santa Fe (13), Tucson (10), Palisade (6), Kona (5).
- **Honda (16 done):** Accord (19/4 done), Civic (17/7), CR-V (15/5), Odyssey (12), Pilot (10), Ridgeline (8).
- **Nissan (33 done):** Altima (15/7), Frontier (11), Pathfinder (8/5), Murano (7), Titan (5), Xterra (5).
- **Kia (0 done):** Sorento (14), Sportage (11), Carnival (5).

### ⚠️ Special handling
- **Toyota/Lexus (207 gated combined — biggest prize):** OM portal is **JS-gated** (dynamic, not static PDF URLs). Needs its own acquisition approach before any verification. NOT started.
- **EV queue (separate EV-spec method — battery coolant, reduction-gear fluid, HV + 12V aux battery, charging; NO engine oil/conventional trans):** Ford Mustang Mach-E ×5, Nissan Leaf ×4, Hyundai Ioniq 5/6/9 ×9, Subaru Solterra ×4, Kia EV6/Niro EV, Chevy Bolt, BMW i4/iX ×8, Tesla ×28, Lucid ×6, Toyota bZ4X, VW ID.4.
- **Reachable makes** (free static OEM OM portals, method proven): Ford/Lincoln, GM (Chevy/GMC/Buick/Cadillac), Nissan/Infiniti, Subaru, Hyundai/Kia/Genesis, Honda/Acura, Mazda, VW/Audi, Stellantis (Dodge/Jeep/RAM/Chrysler).
- **Data-quality dupe:** Chevrolet has both `TrailBlazer` and `Trailblazer` (casing) — normalize.

---

## 6. Working-directory artifacts (untracked unless noted)

- **`wrench_vehicles.db`** — source SQLite (NOT git-tracked). Backed up before every write (`.bak_<name>_<timestamp>`).
- **`_write_*.py`** — per-nameplate write scripts (escape, f150_pilot, f150_bulk, explorer, aviator, mustang, + Nissan ones). Committed.
- **`_pull_epa_mpg.py`, `_pull_nhtsa.py`** — government backfill pullers. Committed.
- **OM PDFs** (untracked, in working dir): `_ford_f150_2016/2017/2018/2022_om.pdf`, `_ford_explorer_2022_om.pdf`, `_ford_escape_2024_om.pdf`, `_lincoln_aviator_2023_om.pdf`, `_aviator_techspecs.pdf`, `_ford_mustang_2022_om.pdf`, `_ford_mustang_2025_om.pdf`, + Nissan PDFs. `_*_caps.txt` are extracted chapters.
- Deploy pipeline files: `files/04_rebuild_demo.py`, `_deploy_sync_specs.py`.

## 7. Standing security/discipline constraints (preserve verbatim)
- "never write a spec value without an authoritative source."
- Pull ONLY never-pulled gov rows — do NOT re-hammer genuinely-empty; LOG every pull (ok/empty).
- Do NOT scrub aggregators / Vehicle Finder / "car finder" — leads-only, gated. CARFAX/directories used ONLY to find each OEM's own portal — NEVER cited for a spec value.
- Do NOT write gas specs to EV rows. Gate halo variants without OM coverage.
- Show the verification log + pause for review before writing; map inventory + flag EV/halo before downloading.

---

## 8. Recommended first action next session
Pick a target from §5. Highest-leverage not-yet-started + reachable: **Chevrolet Silverado 1500 (21)** or **Subaru Outback+Forester (37)** or **Hyundai Sonata+Elantra+Santa Fe (40)**. Or **finish Ford** (Ranger/Expedition/Bronco). Or **solve the Toyota JS-gated portal** (unlocks 207). Or **start the EV-spec method**. Then run the §2 workflow.
