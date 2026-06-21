# KYR — OEM Owner's-Manual Source Map (navigation aid)
### Know Your Ride Technologies LLC · 21 June 2026

> **What this is.** A navigation map to each manufacturer's **own free owner's-manual portal** — the clean, citable **Tier-1 source** for the free verification stream (oil/fluids/coolant/tire/intervals → `owner-manual-verified`). It tells a researcher *where the manual lives* and *how to reach it* per make.
>
> **Provenance discipline (non-negotiable).** The portal list was *navigated to* via a third-party directory article (CARFAX). **CARFAX/the directory is used ONLY to find each OEM's own portal — it is NEVER cited for any spec value.** Every fact written to the DB is cited to the **specific OEM manual + printed page** (the [Source Authority Matrix](KYR_Source_Authority_Matrix.md) rule). A value is `owner-manual-verified` only when pulled from the manufacturer's own manual, confirmed to match the vehicle (self-ID on p1), and page-cited.
>
> **No DB writes** — this is a routing aid. Companion to **§2 of `KYR_Verification_Pipeline_Design.md`** (which characterizes the same portals for the *extraction tool*: PDF host pattern, Self-ID, Grade). This file adds the **navigation lens**: portal type, VIN requirement, year coverage, access confidence.

---

## Confidence tiers
- 🟢 **PILOT-CONFIRMED** — used in production verification (Honda, Mazda). Trusted at volume.
- 🔵 **PDF-VERIFIED (this pass)** — a real owner's-manual PDF was reached hands-on (HTTP 200 + `%PDF` bytes), login-free, by year+model. Reachable; still needs a 1-vehicle pipeline pilot to characterize URL/filename templates + Self-ID before bulk.
- ⚪ **NEEDS-CHARACTERIZATION** — portal known, access not yet confirmed this pass; pilot before bulk. Corporate-sibling inheritance noted where it applies.

## Map — ordered by gated volume

| Make | Gated | Official OEM portal | Portal type | VIN req'd? | Year coverage | Confidence |
|---|---|---|---|---|---|---|
| **Toyota** | 348 | [toyota.com/owners](https://www.toyota.com/owners/warranty-owners-manuals/) | **JS-gated** (Salesforce SPA viewer; PDF behind it) | No — year+model | ~1996+ | ⚪ JS viewer blocks plain fetch → **needs browser pilot** to extract PDF URL. Pre-1990/service → paid TIS. |
| **Ford** | 272 | [ford.com/support/owner-manuals](https://www.ford.com/support/owner-manuals/) | **Direct PDF** (no login) | No — year+model (VIN optional) | ~1996–2026 | 🔵 Verified real F-150 PDFs. PDFs on `fordservicecontent.com`; filename scheme differs pre/post ~2010. |
| **Chevrolet** | 257 | [chevrolet.com/support…/manuals-guides](https://www.chevrolet.com/support/vehicle/manuals-guides) | **Direct PDF** (no login; **anti-bot 403** to non-browser UA) | No — VIN not usable; year+model | 1993+ | 🔵 Verified real Silverado PDFs (2017+2026). Spoof a browser UA. GM Owner Center pattern. |
| **Honda** | 207 | [owners.honda.com](https://owners.honda.com) → techinfo | **Direct PDF** `techinfo.honda.com/rjanisis/pubs/om/<code>/<code>om.pdf` | No — year+model | decades | 🟢 PILOT-CONFIRMED. Self-IDs, text-extractable. Codes opaque (discovery is JS). |
| **Nissan** | 197 | [nissanusa.com/owners/manuals-guides](https://www.nissanusa.com/owners/manuals-guides.html) | **Direct PDF** (no login) | No — year+model | ~2008/2010+ | 🟢 **PILOT-CONFIRMED** (Altima L34 2019–2025, 7 vehicles). Self-IDs p1; spec-dense 592-pp full OM. **★ Nissan OM publishes drain-plug + oil-filter + lug torque** (Honda/Mazda OMs don't) → more verified per vehicle. Multi-section layout (see note). Filename scheme varies by year (`/content/dam/…/<yr>-nissan-<model>-owner-manual.pdf` for newer; `owners.nissanusa.com/content/techpub/ManualsAndGuides/<Model>/<Yr>/<Yr>-<Model>-owner-manual.pdf` for ~2019) — probe both. |
| **Cadillac** | 137 | [my.cadillac.com](https://my.cadillac.com) (GM Owner Center) | Direct PDF likely (GM pattern) | No — year+model | 1993+ likely | ⚪ GM sibling of Chevrolet → inherits direct-PDF + UA-spoof. Pilot to confirm. |
| **Volkswagen** | 125 | [vw.com/en/owners](https://www.vw.com/en/owners.html) | per-vehicle | TBD | ~10+ yrs | ⚪ Needs pilot. VW-group (↔ Audi). |
| **Mazda** | 120 | [mazdausa.com](https://www.mazdausa.com) | **Direct PDF** `mazdausa.com/siteassets/pdf/owners-optimized/<YEAR>/…` | No — year+model | ~20 yrs (2005+ optimized) | 🟢 PILOT-CONFIRMED (gold standard). 13 vehicles done. Near-predictable URLs. |
| **Dodge** | 114 | [mopar.com](https://www.mopar.com/en-us/my-vehicle/owners-manual.html) (Mopar) | per-vehicle | TBD | ~10+ yrs | ⚪ Needs pilot. Stellantis/Mopar (↔ Jeep/Ram/Chrysler). |
| **Hyundai** | 110 | [owners.hyundaiusa.com](https://owners.hyundaiusa.com) + CDN | **Direct PDF** (regional CDN) + JS viewer | No — year/model/trim | US MY2005+ | 🔵 Verified real Elantra PDF. Pilot: confirm US-spec PDF path (not India-market file) via the `/content/dam/` CDN. |
| **BMW** | 104 | [bmwusa.com/…/owners-manuals](https://www.bmwusa.com/explore/bmw-genius/owners-manuals.html) | per-vehicle (VIN-lookup likely) | likely yes | ~10+ yrs | ⚪ Needs pilot. BMW often VIN-keyed. |
| **Buick** | 102 | [my.buick.com](https://my.buick.com) (GM Owner Center) | Direct PDF likely (GM pattern) | No — year+model | 1993+ likely | ⚪ GM sibling → inherits Chevrolet. Pilot to confirm. |
| **Acura** | 100 | [owners.acura.com](https://owners.acura.com) → techinfo | Direct PDF likely (Honda group) | No — year+model | decades | ⚪ Honda sibling → expect Honda-like `techinfo` direct PDF + Self-ID. Pilot to confirm. |
| **Subaru** | 100 | [subaru.com/owners](https://www.subaru.com/owners/vehicle-resources.html) → STIS | **Direct PDF** `techinfo.subaru.com/stis/doc/ownerManual/` (skip the JS shell) | No — year+model | ~1997+ (~20 yrs) | 🔵 Verified 2 real PDFs. Filename codes (e.g. `MSA5B2304A`) not publicly indexed → pilot the year/model→filename map. |
| **Jeep** | 94 | [mopar.com](https://www.mopar.com/en-us/my-vehicle/owners-manual.html) | per-vehicle | TBD | ~10+ yrs | ⚪ Stellantis/Mopar sibling of Dodge/Ram. |
| **GMC** | 91 | [gmc.com/owner-center](https://www.gmc.com/owner-center) | Direct PDF likely (GM pattern) | No — year+model | 1993+ likely | ⚪ GM sibling → inherits Chevrolet. |
| **Audi** | 87 | [audiusa.com/…/ownersmanuals](https://www.audiusa.com/us/web/en/owners.html) | per-vehicle | TBD | ~10+ yrs | ⚪ VW-group sibling. |
| **Lincoln** | 87 | [lincoln.com/owner/resources/owner-manuals](https://www.lincoln.com/owner/resources/owner-manuals/) | Direct PDF likely (Ford group) | No — year+model likely | ~1996+ likely | ⚪ Ford sibling → inherits Ford direct-PDF. Pilot to confirm. |
| Volvo / Acura / others | 80+ | per-make | per-vehicle | TBD | Volvo: decades | ⚪ Lower priority. Article: Volvo/Acura/Chevy/Honda go back decades. |

*Gated counts from `KYR_Verification_Pipeline_Design.md` §2. Year-coverage notes blend the directory article (most brands ~10+ yrs; Volvo/Acura/Chevy/Honda decades; Subaru/Mazda ~20 yrs) with hands-on findings.*

---

## Key takeaways for the free OM stream

1. **The owner's-manual portals are overwhelmingly clean Tier-1 access.** Of the six high-volume un-piloted makes characterized this pass, **five (Ford, Chevrolet, Nissan, Subaru, Hyundai) are direct, login-free, VIN-free PDFs** reachable by year+model — they qualify as VERIFIED (manufacturer) sources under the [data-integrity gate](KYR_Source_Authority_Matrix.md). Plus Honda + Mazda already in production = **7 of the top makes are confirmed-reachable.**
2. **VIN is NOT required** for the owner's manual on any portal checked — year+model selection reaches it. (VIN walls appear for *service* info, not the owner's manual.) This keeps the free stream frictionless.
3. **Toyota (348, our #1) is the lone hard case** — a JS/SPA viewer with no plain-fetch PDF. It needs a real-browser/headless pilot to extract the manual URL, OR fall back to the addressable Quick Reference Guide for the limited fields it carries (per §2, Toyota is also Grade-D for Self-ID — the full OM doesn't name the model inside, so model-match must be confirmed another way).
4. **Two access wrinkles to plan for:** GM (Chevy/Cadillac/Buick/GMC) returns **403 to non-browser User-Agents** — spoof a normal UA; and several portals (Nissan, Subaru, Ford, GM) changed PDF **filename schemes across eras** — run a short per-make URL-template probe before any bulk pass.
5. **Corporate-sibling inheritance cuts the work:** characterizing one brand unlocks its group — **GM** (Chevy→Cadillac/Buick/GMC), **Honda** (Honda→Acura, both `techinfo`), **Ford** (Ford→Lincoln), **VW** (VW→Audi), **Stellantis/Mopar** (Dodge→Jeep→Ram→Chrysler). ~8 portal characterizations cover the top ~20 makes.

### ★ Nissan pilot finding (June 2026) — torque bonus changes Nissan's value
Piloted on the Altima L34 (2019–2025). **Nissan's owner's manual publishes the claim-critical service-torque fields that Honda's and Mazda's OMs omit** — **drain-plug torque (22–28 ft-lb, §8-12), oil-filter torque (11–15 ft-lb, §8-12), and lug torque (83 ft-lb, §6-8)** — all manufacturer-authoritative, so they go straight in as `owner-manual-verified` with no service-manual stage. **This means Nissan vehicles get *more* verified from the free stream than Honda/Mazda do** (including drain-plug torque, an audit claim-critical field). Still gated for Nissan: spark-plug type/gap, battery group/CCA, CVT-fluid capacity (NS-3 *type* is in the OM; capacity isn't).
- **Spec layout is multi-section** (not one consolidated table like Mazda): fluids/capacities §10-2/10-3, tire **size** §10-9, tire **pressure** §8-33, **torque** §8-12 & §6-8, maintenance §9. Engine codes (**PR25DD** 2.5L / **KR20DDET** 2.0T VC-Turbo) split the specs → a per-make locator needs ~5 page anchors.
- **Verify engine config per model-year, don't assume:** the L34 2.0T was offered **2019–2024, dropped for 2025** — confirmed by probing each year's own manual (the "2021+ is 2.5L-only" assumption was wrong by four years). Cheap to check: grep each year's PDF for the turbo engine code.
- **Time:** ~30 min for the generation (more sections than Honda, but spec-dense and reliable; no 403/login).

## Recommended pilot order (free OM stream)
**Already in production:** 🟢 Honda, Mazda, **Nissan** (Altima L34 done — extend to Sentra/Rogue/Maxima/Pathfinder next; Nissan's torque bonus makes it high-value).
**Quick wins next (PDF-verified, clean):** **Ford** (272, direct) → **Chevrolet** (257, direct + UA spoof, unlocks Cadillac/Buick/GMC = +330 siblings) → **Subaru** (100) → **Hyundai** (110).
**Then the hard one:** ⚪ **Toyota** (348) — browser-pilot or QRG fallback.
**Sibling sweeps (cheap once parent is done):** Acura (Honda), Lincoln (Ford), Cadillac/Buick/GMC (Chevy).

---
*Navigation aid only — no spec data herein. Every fact is cited to the specific OEM manual + page, never to CARFAX or any directory. Companions: [Verification Pipeline Design §2](KYR_Verification_Pipeline_Design.md) · [Source Authority Matrix](KYR_Source_Authority_Matrix.md) · [Verification Sourcing Cost Analysis](KYR_Verification_Sourcing_Cost_Analysis.md). Portal URLs/schemes point-in-time June 2026 — verify on navigation.*
