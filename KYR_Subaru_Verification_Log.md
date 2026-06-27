# KYR — Subaru Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified · FIRST non-GM make

Parallel to the GM-group / Ford / Honda / Nissan / Mazda logs. Make characterization + reusable
source pattern in `KYR_OEM_Manual_Source_Map.md` (Subaru section). **Host:** `cdn.subarunet.com/stis/doc/ownerManual/`.

> **Subaru status:** **Outback ✅ 11/20** (modern BS+BT; BH/BP 2000–2009 deferred). DB also has Forester, Crosstrek, Legacy, Impreza, Ascent, WRX, BRZ + Solterra (EV) — pending, reuse the Subaru source pattern.

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
