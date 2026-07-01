# KYR — Hyundai Owner's-Manual Verification Log
### Know Your Ride Technologies LLC · page-cited, owner-manual-verified · FIRST Hyundai Motor Group make

Parallel to the GM-group / Ford / Honda / Nissan / Mazda / Subaru logs. Make characterization + reusable
source pattern in `KYR_OEM_Manual_Source_Map.md` (Hyundai section). **Host:** `owners.hyundaiusa.com` MyHyundai
glovebox-manual (free, no auth, citable manufacturer source). **This is the HMG foundation — it pre-characterizes
Kia (~80 rows / 12 nameplates), and specifically Optima/K5 as a near-twin of the Sonata (shared platform + Theta II/Smartstream engines).**

> **Hyundai status:** **Sonata ✅ 5/14** (2005/2006 NF + 2018 LF + 2021 DN8 + 2024 DN8-FL; **9 deferred**). First Hyundai slice — make source characterized + engine families on record. DB also has Elantra 21, Santa Fe 13, Tucson 10, Accent, Tiburon, Palisade, Kona, Venue, Veloster, Ioniq (EV) — all pending. **Next Hyundai:** Elantra (Sonata's smaller sibling, shared engine families) or straight to **Kia (Optima/K5 = Sonata twin)** to cash the unlock.

## ✅ SONATA — pilot 5/14 (2005/06 NF + 2018 LF + 2021 DN8 + 2024 DN8-FL) — `2026-07-01-hyundai-sonata`, commit df2f8d07 — FIRST HYUNDAI
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
