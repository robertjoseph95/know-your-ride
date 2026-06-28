# KYR — Subaru Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified · FIRST non-GM make

Parallel to the GM-group / Ford / Honda / Nissan / Mazda logs. Make characterization + reusable
source pattern in `KYR_OEM_Manual_Source_Map.md` (Subaru section). **Host:** `cdn.subarunet.com/stis/doc/ownerManual/`.

> **Subaru status:** **Outback ✅ 11/20** · **Forester ✅ 8/19** · **Crosstrek ✅ 7/7 COMPLETE** · **Impreza ✅ 5/10** · **Legacy ✅ 2/2 COMPLETE** · **Ascent ✅ 4/4 COMPLETE** · **WRX ✅ 4/10** (modern VA+VB; 2003–08 old-EJ deferred). **WRITABLE SUBARU MAKE COMPLETE — 7 nameplates verified end-to-end.** Pairs closed: Crosstrek⇄Impreza (platform-twin), Legacy⇄Outback (combined-manual), WRX/STI (combined book). DB also has BRZ + Solterra (EV) — pending. **Only remaining Subaru work = old-gen discovery passes** (pre-2015 EJ-era rows across Outback BH/BP, Forester SF/SG, Impreza GD/GG, WRX EJ 2003–08) + Forester 2025/26 + Outback 2025/26 refresh check.

## ✅ WRX — modern 4/4 (2003–08 old-EJ deferred) — `2026-06-27-subaru-wrx`, commit 938e1efc — FINISHES THE WRITABLE SUBARU MAKE
Separate performance model. Self-ID: VA 2021 = **combined WRX/STI book** (A1760, "05") — base-WRX "Except STI" column isolated; STI (EJ257, hydraulic PS) excluded. VB 2022 (A9020) / 2026 (A9100) = WRX-only.
| Gen / engine | Oil | Cooling (MT/CVT) | Plug | Tire |
|---|---|---|---|---|
| **VA FA20-DIT** (2020–21) | **5W-30, 5.4 qt** | 8.6 / 8.8 | ILKAR8H6 | 235/45R17 |
| **VB FA24-DIT** (2022) | **0W-20, 4.8 qt** | 9.0 / 9.2 | **SILKFR8D6Y** | 235/45R17 |
| **VB FA24-DIT** (2026) | 0W-20, 4.8 qt | 9.0 / 9.2 | **SILKFR8A6** | 245/40R18 |
Common: 6MT gear oil GL-5 75W-90 3.5 qt (written) + CVT (consult dealer, gated); front diff (CVT) 1.5 (VA)/1.3 (VB), rear 0.8; brake FMVSS No.116 DOT 3/4; lug 89; battery 75D23L; EPS (base WRX). Sources: 2021 WRX/STI OM MSA5M2105A, 2022 OM MSA5M2205A, 2026 OM MSA5M2605A.

**★ The body-vs-engine thesis gets a THIRD axis (TUNE):**
- **FA20-DIT = own engine** (5W-30/5.4 — pure-discovery, NOT the mainstream NA 0W-20).
- **FA24-DIT cross-check vs mainstream FA24:** **oil/cooling HOLD** (0W-20/4.8, 9.2 CVT = same as Outback; WRX lighter than Ascent's 11.7) but **PLUG MOVES** (SILKFR8D6Y vs mainstream SILKFR8A6) — and drifts **per-year within VB** (2022 D6Y → 2026 A6). → **ENGINE decides oil; BODY decides cooling; TUNE decides plug.** No shortcut produces this; only reading each field does.
- **Transmission break:** NOT CVT-universal — 6MT gear oil writable + CVT gated, read per row; 2026 still offers 6MT.
- **VA combined WRX/STI book** — base-WRX column isolated (STI EJ257/hydraulic excluded), the Legacy/Outback discipline applied to a performance pairing.

**DEFER:** 2003–2008 old EJ (EJ205/EJ255, EPA-empty "Impreza WRX" era) → old-doc discovery. STI excluded (no DB row).

---

## ✅ ASCENT — COMPLETE 4/4 — `2026-06-27-subaru-ascent`, commit f6df22a9
Subaru sibling #6, 3-row SUV. Standalone manual, **FA24-only** all years. Self-ID: model code **A32xx** (unique block, no twin), filename segment **"00"**. The campaign's purest body-vs-engine isolation (same engine, no twin, no shared book).
| Era | Oil | Cooling | Battery | Plug | Tire | Fuel |
|---|---|---|---|---|---|---|
| **pre-refresh 2020–22** | 0W-20, 4.8 qt | **11.7 qt** | 75D23L | SILKFR8A6 | 245/60R18 105H | 19.3 gal |
| **2026 (post-refresh)** | 0W-20, 4.8 qt | 11.7 qt | **LN2** | SILKFR8A6 | 245/60R18 105H | 19.3 gal |
Common: SUBARU Super Coolant; diff front 1.3 / rear 0.8 GL-5 75W-90; brake FMVSS No.116 DOT 3/4; **lug 89 lb-ft**; EPS. Sources: 2021 OM `MSA5M2100A` (A3220BE-A), 2026 OM `MSA5M2600A` (A3270BE-A).

**★ BODY-vs-ENGINE split (campaign's purest demo):**
- **FA24 engine-bound fields HELD across bodies:** 0W-20, 4.8 qt oil, plug SILKFR8A6, lug 89 — identical to Outback/Legacy FA24.
- **★ COOLING is BODY-bound — DIVERGED 9.2 qt (Outback) → 11.7 qt (Ascent), +2.5 qt** = the largest same-engine cross-body divergence in the campaign (heavier 3-row body). Plus fuel 19.3 (vs 18.5) and tire 245/60R18 (vs 225/65R17).
- **★ FA24 STAYS 0W-20** — did NOT follow FB20/FB25 to 0W-16 → 0W-16 is an FB-new-gen-specific fact, not Subaru-wide (mirror of the spark-plug-travels-with-injection-era rule).
- **2026 refresh moved exactly ONE field:** battery 75D23L → LN2; cooling/oil/fuel/tire/lug all held (refresh-boundary discipline: didn't assume nothing changed, didn't assume everything did).

**No defers** (Ascent is 2019+). No 2nd engine, no electrified rows.

---

## ✅ LEGACY — COMPLETE 2/2 — `2026-06-27-subaru-legacy`, commit 2b647b70
Subaru sibling #5, Outback's combined-manual mate. Read from the **Legacy column** of the combined Legacy+Outback OM `MSA5M2003A-2004A` (2021 = 2020 BT rep + stability note; full 2021 combined OM not on CDN, only 140pp partial 2113A).
| Engine (2020-21) | Oil | Cooling | Plug |
|---|---|---|---|
| **FB25** (DI 12.0:1) | 0W-20, 4.4 qt | 9.5 qt | DILKAR7Q8 |
| **FA24** (2.4T 10.6:1) | 0W-20, 4.8 qt | 9.2 qt | **SILKFR8A6** |
Common: SUBARU Super Coolant; diff front 1.3-1.4 / rear 0.8; brake FMVSS No.116 DOT 3/4; **lug 88.5 lb-ft** (combined-book value, NOT the standalone 89); battery LN2; fuel 18.5 gal; EPS. Tire (Legacy sedan): 225/55R17 97V, 33/32 psi.

**★ Column-isolation cross-check (the cleanest "shares a manual ≠ shares the specs" demo):**
- **Predicted divergence read IDENTICAL:** fuel 18.5 gal (both Legacy sedan & Outback wagon) — read, not assumed.
- **Actual divergences elsewhere (Legacy column isolated):** tire 225/55R17 (vs Outback 225/65R17), pressure 33/32 (vs 35/33), CVT capacity 11.9/12.3 (vs 12.4/12.6).
- **Same (per-engine/common):** FB25/FA24 oil+cool, battery LN2, plugs, diff, lug 88.5.
- **New on record:** FA24 turbo plug **SILKFR8A6 (NGK)**; lug **88.5 in the combined book** (vs 89 standalone).

**No defers** (1990–2002 = neg-id phantoms). **No 3.6 flat-6, no WRX** in scope.

---

## ✅ IMPREZA — modern 5/5 (2000–2004 EJ deferred) — `2026-06-27-subaru-impreza`, commit 343adc14
Subaru sibling #4, Crosstrek mirror-twin. Self-ID via mirror differential **`impreza=0 AND crosstrek=0`** + filename **"01"** (model codes A1380/A1530/A1640 = Crosstrek's **+10** in the shared A1xxx block — the differential, not the code prefix, is the gate). Each engine read fresh — **twin predicts, OM decides.**
| Era (rows) | Engine | Oil | Cooling | Plug | Battery | Fuel | Tire |
|---|---|---|---|---|---|---|---|
| **GK 2019–21** | FB20 (DI 12.5:1) | **0W-20, 4.7 qt** | 8.2 qt | DILKAR7B8 | 75D23L | 13.2 gal | P205/55R16 |
| **new-gen 2024** | FB20+FB25 | **0W-16 req**, 4.7 qt | 8.4 / 8.9 | DILKAR7Q8 | Q-85 | 16.6 gal | 205/55R16 |
| **2026 refresh** | FB20+FB25 (kept) | **0W-16 req**, 4.7 qt | 8.4 / **7.9** | DILKAR7Q8 | Q-85 | 16.6 gal | 205/55R16 |
Common: SUBARU Super Coolant; diff front 1.4 / rear 0.8 qt GL-5 75W-90; brake FMVSS No. 116 DOT 3/4; **lug 89 lb-ft / 120 N·m** (read from Impreza OM); EPS. OM publishes → WRITTEN: plug type, battery, tire. GATED: spark GAP, CVT fluid. Sources: 2020 OM `MSA5M2001A` (A1380BE-A), 2024 OM `MSA5M2401A` (A1530BE-A), 2026 OM `MSA5M2601A` (A1640BE-A).

**★ Cross-check = the principle this sibling arc was building toward (twin predicts, OM decides):**
- **Confirmed twin MATCHES:** FB20 0W-20/4.7 (GK); new-gen 0W-16/4.7 + FB25; **2026 FB25-coolant refresh 8.9→7.9 now on BOTH twins** = platform-wide 2026 change, not a Crosstrek one-off.
- **Caught 4 real twin DIVERGENCES (read, reported not reconciled — proof a cross-check catches as well as confirms):** fuel 13.2(GK)→16.6 (Crosstrek 16.6 throughout) · tire 205/55R16 (Crosstrek 225/60R17) · 2026 keeps FB20+FB25 (Crosstrek dropped FB20) · battery Q-85 (Crosstrek LN2).
- **Self-ID #3 verified in mirror direction:** codes are Crosstrek **+10** (adjacent A1xxx siblings) → a code-prefix rule would mis-claim every Impreza as a Crosstrek; the `crosstrek=0` differential + filename "01" cut cleanly. WRX excluded (separate model).

**DEFERRED:** 2000–2004 GD/GG EJ-series (EJ22/EJ25, pre-DI/pre-CVT) — old-doc discovery. **EXCLUDED:** WRX/STI (separate model). **Ignored:** 1993–1999 neg-id phantoms. Illustration (likely G4-fax) not rendered → self-ID held via differential.

---

## ✅ CROSSTREK — COMPLETE 7/7 — `2026-06-27-subaru-crosstrek`, commit 18f3ff53
Subaru sibling #3 — first genuinely NEW engine reads of the line. Self-ID via twin-exclusion (impreza=0 + filename "07" + provenance; A1xxx is the shared Impreza/Crosstrek platform code; illustration = G4-fax, unrenderable → follow-up).
| Era (rows) | Engine | Oil | Cooling | Plug | Battery |
|---|---|---|---|---|---|
| **GU 2018–20** | FB20 (DI 12.5:1) | **0W-20, 4.7 qt** | 8.2 qt | DILKAR7B8 | 75D23L |
| **GU 2021** | + FB25 (DI 12.0:1) | 0W-20, 4.4 qt | 8.8 qt | DILKAR7Q8 | 75D23L |
| **3rd 2024–25** | FB20 + FB25 | **0W-16 req** (0W-20 alt), 4.7 qt | 8.4 / 8.9 | DILKAR7Q8 | LN2 |
| **2026 refresh** | FB25 only (FB20 dropped) | **0W-16 req**, 4.7 qt | **7.9 qt** | DILKAR7Q8 | LN2 |
Common: SUBARU Super Coolant; diff front 1.4 / rear 0.8 qt GL-5 75W-90 (2026 read, not carried); brake FMVSS No. 116 DOT 3/4; **lug 89 lb-ft / 120 N·m** (read from Crosstrek OM); fuel 16.6 gal; EPS. OM publishes → WRITTEN: plug type, battery, tire (P225/60R17 or 225/55R18). GATED: spark GAP, CVT fluid (consult dealer). Sources: 2020 OM `MSA5M2007C` (A1370BE-C), 2021 OM `MSA5M2107A` (A1410BE-A), 2024 OM `MSA5M2407A` (A1520BE-A), 2026 OM `MSA5M2607B` (A1630BE-B).

**★ New artifacts (none predictable from platform knowledge — the payoff of sequencing Crosstrek after the pattern was proven):**
- **FB20 = first FB20 on record** (DI; 0W-20/4.7 qt GU, 0W-16/4.7 qt 3rd-gen). Read fresh, not assumed-from-FB25.
- **0W-16 = new viscosity grade for the campaign** (3rd-gen 2024+, REQUIRED vs 0W-20 alternative).
- **FB25 oil cap 4.4 (GU) → 4.7 (3rd-gen)** — proven via the FB25-only 2026 OM (the 2024 common-capacity page couldn't disambiguate per-engine).
- Per-era shifts read: FB20 plug DILKAR7B8→DILKAR7Q8; battery 75D23L→LN2; coolant 8.9 (2024) → 7.9 (2026 refresh).
- **PHEV (2019–21) + Hybrid (2026): gated variant notes** — gas-side written on generic rows, HV never touched (no electrified DB row).
- **Self-ID refinement #3** (platform-twin): own-model differential `impreza=0` discriminates Crosstrek from its A1xxx twin — carries directly to the Impreza slice (mirror: crosstrek=0).

**KNOWN FOLLOW-UP:** Crosstrek front-illustration is a CCITT-G4-fax raster unrenderable in this environment (fitz/pdf2image absent) — visual self-ID confirmation deferred; self-ID held via the stronger differential route.

---

> **✅ OUTBACK ENRICHMENT — COMPLETE** (`2026-06-27-outback-enrichment`, commit 88243b92). All 11 modern Outback rows now carry **plug-type / battery / tire** (previously gated). Surgical UPDATE of 3 parts fields only; oil/cooling/fuel/lug/diff untouched. Spark GAP stays gated. **BS read earned its keep — 3 of 4 fields diverged from BT (read, not carried):**
> - **BS 2016–19** (2018 OM, Outback column): battery **75D23R**; plugs FB25 **SILZKAR7B11** + 3.6 EZ36 **SILFR6C11**; tire 225/65R17 102H, 35/33 psi.
> - **BT 2020–26** (2020 OM, Outback column): battery **LN2**; plugs FB25 **DILKAR7Q8** + FA24 **SILKFR8A6**; tire 225/65R17 102H, 35/33 psi.
> - Divergences caught: battery 75D23R→LN2; **FB25 plug SILZKAR7B11(port)→DILKAR7Q8(direct) — the port→direct boundary moves the PLUG, not just oil cap**; BS 3.6 EZ36 (SILFR6C11) vs BT FA24 (SILKFR8A6). Tire SAME (wagon 225/65R17, NOT Legacy sedan 225/55R17).
> - **⚠ Open future-slice candidate (logged, not resolved):** BT plug/battery/tire on the 2020-rep basis (same as live BT oil/cooling) → **Outback 2025/26 per-year refresh check** (did the refresh move battery/tire as the Crosstrek/Impreza 2026 refreshes moved coolant?) remains a separate slice that would also re-examine the live oil/cooling for those years.

## ✅ FORESTER — modern (8/8 modern; 2025/26 + 2000–06 deferred) — `2026-06-27-subaru-forester`, commit dd487488
Subaru sibling #2. Standalone manual (self-ID = `A82xx` model code + p2 vehicle illustration; body says "Forester" 0× — normal for standalone). Each engine read fresh from rendered spec pages.
| Era (rows) | Engine | Oil | Coolant | Plug type | Battery | Fuel |
|---|---|---|---|---|---|---|
| **SJ 2017–18** | FB25 (port, 10.3:1) | **0W-20, 5.1 qt** | 8.1 qt | SILZKAR7B11 (NGK) | 75D23L | 15.9 gal |
| **SJ 2017–18** | FA20 **turbo** | **5W-30, 5.4 qt** | 9.5 qt | ILKAR8H6 (NGK) | 75D23L | 15.9 gal |
| **SK 2019–24** | FB25 (**direct-inj**, 12.0:1) | **0W-20, 4.4 qt** | 9.0 qt | DILKAR7Q8 (NGK) | Q85 | 16.6 gal |
Common: SUBARU Super Coolant; front diff GL-5 75W-90 (SJ 1.3 NT/1.5 turbo, SK 1.4); rear diff 0.8 qt; brake **FMVSS No. 116, DOT 3 or DOT 4**; **lug 89 lb-ft / 120 N·m** (Forester prints 89 vs Outback 88.5); EPS. **OM publishes (WRITTEN): plug type, battery, tire size/pressure** (P225/60R17 or P225/55R18, per trim). **GATED: spark-plug GAP** (genuinely not printed), CVT fluid (consult dealer), drain/oil-filter torque, oil-filter PN. Sources: 2018 OM `MSA5M1802B` (SJ rep, A8230BE-B) + 2019 OM `MSA5M1902B` (SK rep, A8240BE-B).

**★ Headline catches:**
- **FB25 port→direct divergence reproduces** (2nd independent confirmation → platform-level FB25 fact): SJ 5.1 qt/8.1 qt cool (10.3:1) → SK 4.4 qt/9.0 qt cool (12.0:1) at the 2019 redesign. Travels to Crosstrek.
- **FA20 2.0 turbo = its own read** (5W-30/5.4 qt) — distinct from NA 0W-20 and from Outback's FA24.
- **Pattern refinements:** (1) standalone-manual self-ID = illustration + model code, NOT name-count (Forester says "Forester" 0×, which is normal). (2) Subaru OM **publishes** plug-type/battery/tire (write them); only the gap is genuinely omitted.
- Per-gen shifts all read: battery 75D23L→Q85, plug SILZKAR7B11→DILKAR7Q8, fuel 15.9→16.6 gal.

**DEFERRED:** **2025/2026** (ids 8614/10234) — no full OM on CDN (only a 216pp partial, no Specifications chapter) **+** new Hybrid variant; gate until full new-gen OM surfaces. **2000–2006** (7 rows) — EJ25 + EJ255 turbo (2004–06), pre-CVT; old Forester doc-number discovery + per-doc self-ID (like Outback BH/BP).

---

## ✅ OUTBACK — modern (11/11 modern; 9 old-gen deferred) — `2026-06-27-subaru-outback`, commit dcb1183d
First Subaru / first non-GM make. Each engine read FRESH from the Subaru OM's own (image-rendered) spec pages.
| Era (rows) | Engine | Oil | Coolant | Front diff |
|---|---|---|---|---|
| **BS 2016–19** | 2.5 FB25 (port-inj, 10.3:1) | **0W-20, 5.1 qt** | 8.2 qt | 1.3 qt |
| **BS 2016–19** | 3.6 EZ36 flat-6 | **5W-30, 6.9 qt** | 7.4 qt | 1.5 qt |
| **BT 2020–26** | 2.5 FB25 (DIRECT-inj, 12.0:1) | **0W-20, 4.4 qt** | 9.5 qt | 1.3 qt |
| **BT 2020–26** | 2.4T FA24 turbo | **0W-20, 4.8 qt** | 9.2 qt | 1.3 qt |
Common: SUBARU Super Coolant; rear diff 0.8 qt GL-5 75W-90 (BT Outback rear: 75W-90 or 90); brake **FMVSS No. 116, DOT 3 or DOT 4** (as stated); **lug 88.5 lb-ft / 120 N·m** (NOT GM 140); fuel 18.5 gal; EPS. CVT (Lineartronic) fluid = consult dealer → GATED. **Spark gap GATED — Subaru OM does not publish it** (make-level fact). Sources: 2018 OM `MSA5M1803A` (BS rep, self-ID A2540BE-A) + 2020 OM `MSA5M2003A-2004A` (BT rep, A2570BE-A).

**★ Headline catches:**
- **Source-confirmation gate fired on unfamiliar ground:** `MSA5M0803A` is the **2008 Forester**, not Outback — `MSA5M` is a shared family prefix. Self-ID via in-body model-code (**A25xxBE** = Legacy/Outback), never the filename. Re-verified both modern reps after the catch.
- **FB25 diverges across the 2020 redesign** (port→direct injection): oil 5.1→4.4 qt, cooling 8.2→9.5 qt — same engine-family name, different gen. The "read each era" rule at its hardest case (compression 10.3→12.0 is the tell).
- **3.6 EZ36 flat-6 = 5W-30** while the 4-cylinders take 0W-20 — engine-specific viscosity, not a nameplate default.
- **Name-collision trap avoided:** EPA "Impreza Wagon / Outback SPT" = *Impreza Outback Sport* (2.0T), a different vehicle — excluded.

**DEFERRED (gated 2nd pass):** BH/BP 2000–2009 (9 rows: 2000–06, 2008–09) — old Outback doc-number discovery + per-doc self-ID needed (old OMs are legible text, not scanned; the blocker is doc-number→model mapping, not legibility). 2000/2001 fold under "Legacy" in EPA+vPIC → engine roster from OM. Pre-CVT era (conventional 4-spd auto / 5-spd manual) — read its own ATF, NOT CVT.

---
*Page citations are OM printed-page numbers. Spec tables are image-rendered → read via render-to-image. OM PDFs kept locally (exceed GitHub 100MB limit, gitignored); provenance = doc number + self-ID code above.*
