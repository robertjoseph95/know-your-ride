# KYR — Subaru Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified · FIRST non-GM make

Parallel to the GM-group / Ford / Honda / Nissan / Mazda logs. Make characterization + reusable
source pattern in `KYR_OEM_Manual_Source_Map.md` (Subaru section). **Host:** `cdn.subarunet.com/stis/doc/ownerManual/`.

> **Subaru status:** **Outback ✅ 11/20** (modern BS+BT; BH/BP 2000–2009 deferred) · **Forester ✅ 8/19** (modern SJ+SK; 2025/26 + 2000–2006 deferred) · **Crosstrek ✅ 7/7 COMPLETE** (all DB years 2018–2026 written). DB also has Legacy, Impreza, Ascent, WRX, BRZ + Solterra (EV) — pending, reuse the Subaru source pattern. **★ Impreza is Crosstrek's platform twin — self-ID via `impreza≥0 AND crosstrek=0` + filename "01" (mirror of Crosstrek's "07").**

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

> **★ KNOWN FOLLOW-UP (bounded touch-up):** **Outback plug-type / battery / tire enrichment.** The Outback rows GATED those three fields only because the Electrical/Tires spec pages (two sheets past the fluids pages) weren't rendered — the Outback OMs *do* publish them (confirmed via Forester). Re-render those pages from the 2018 + 2020 Outback OMs (still local), write spark_plug_type + battery_group + tire to the 11 Outback rows, redeploy. Separate small task, own attention — not bolted onto another deploy.

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
