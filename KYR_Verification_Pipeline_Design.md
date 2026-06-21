# KYR — Verification Pipeline Design (human-in-the-loop)
### Know Your Ride Technologies LLC · 20 June 2026 · **Design only — no build**

**Purpose:** run the owner's-manual verification method (proven on Mazda 3 + 2012 Civic) repeatably, to flip gated AI-sourced vehicles to genuinely verified. The pilot proved the *method*; this scopes how to *operate it at volume* given what does and doesn't automate.

**Reuses existing infrastructure** (no new gate needed): the `source` columns + `ver` boolean + `_ver()` in `04_rebuild_demo.py`, the `specSoon()` gate, the per-vehicle write-script pattern (`_write_civic_2012_pilot.py`), and the page-cited verification-log format (`KYR_Mazda3_Spec_Verification_Log.md`). Setting `source` to an authoritative value + rebuild auto-flips a vehicle from "pending" to verified — already live.

---

## 0. Division of labor (the core principle, from the pilot)

| The TOOL does (automatable) | The HUMAN does (not automatable) |
|---|---|
| Download a manual PDF from a **confirmed** URL | **Discovery** — find the right manual (opaque per-make codes, not derivable from year/model) |
| Extract text; confirm it's not image-based (char-count threshold) | **Confirmation** — does this PDF actually match the vehicle? (the Toyota "doesn't self-identify" problem) |
| Locate the specifications section; parse candidate values | **Judgment** — L→qt, which engine is "base," dual-engine strings, what to leave NULL |
| Surface each candidate **with its page citation + text snippet** | **Source confirmation (mandatory)** — confirm the document matches the vehicle (§1b.1) |
| Auto-write **clean** extractions from a confirmed source; rebuild; gate auto-flips | **Resolve the flag queue** — judgment only on ambiguous fields (units, dual-engine, conflicts) |
| Emit OM-absent fields to the Jazerie queue | **Source-manual triage** — route OM-absent fields to Jazerie's service-manual queue |

> **Design stance: the tool never writes "verified" from an *unconfirmed source*.** The mandatory human gate is **source confirmation** (not per-value sign-off). Once the source is confirmed, clean extractions are trusted and auto-written; only ambiguous fields stop for human judgment (§1b). This preserves the "never a fabricated specification" guarantee while keeping human time small.

---

## 1. The workflow

```
1. DISCOVER   Human supplies a confirmed manual URL.
              (Tool may suggest candidate URLs from the per-make source map; human confirms the right one.)
2. CONFIRM    Tool fetches PDF -> text-extract -> assert not image-based -> show its match evidence
   SOURCE     (model/year string + page). HUMAN confirms the document matches (§1b.1) — MANDATORY GATE.
              If the manual can't self-confirm (Toyota), the tool blocks until the human verifies.
3. PARSE      Tool locates the spec section (per-make anchor map) and parses candidate values, each tagged
              with {field, value(s), page #, snippet, confidence, engine-divergence flag}.
4. AUTO+FLAG  Clean unambiguous values are auto-written (tagged owner-manual-verified). ONLY ambiguous
              fields (unit/dual-engine/conflict/low-confidence) go to the human flag queue; OM-absent
              fields go to Jazerie (§1b.3, §5).
5. APPLY      Tool runs 04_rebuild_demo.py; the integrity gate auto-flips the vehicle to verified.
              Spot-check a sample vs the cited page (§1b.5), preview, deploy.
```

One **generation** is the unit of work (a generation covers multiple DB model-year rows — e.g. 9th-gen Civic = 2012–2015 = ~4 rows), so one verification flips several vehicles.

---

## 1b. Verification / review efficiency model

**Goal:** minimize human review time by **trusting clean extraction from a CONFIRMED source**, while **never auto-writing "verified" without source confirmation.** This is the Toyota Camry lesson — the tool fetched a plausible PDF (`OM33840U`) that did **not** match the vehicle; only a human source-check caught it. The expensive human attention belongs on *which document*, not on re-typing every value the manual plainly states.

> **THE HARD RULE:** the human confirms the **source document is correct**. Never auto-write "verified" on data from an unconfirmed source. *Clean extraction from a confirmed source is trustworthy; "the tool thinks this source is reliable" is not.*

This reframes the §0 division of labor: the **mandatory, non-removable** human gate is **source confirmation** (step 1). Per-value sign-off is **not** mandatory — only the exceptions (step 3) need human judgment.

### 1. Source confirmation — the mandatory human gate (cannot be removed)
A human confirms the fetched manual genuinely matches the vehicle (make / model / year / generation). **The tool must show its evidence so the human can confirm in seconds**, e.g.:
> *"Confidence the manual matches 2012 Civic: model string **'2013 Civic Sedan'** found on p.1; engine families **1.8 ℓ / 2.4 ℓ** match; spec section located p.348. Same generation (9th, 2012–2015). **Confirm match? [Y/correct/reject]**"*
- **Fast** when the manual self-identifies (Honda "2013 Civic Sedan" on p1, Mazda on cover) → one-click confirm.
- **Requires care** when it doesn't (Toyota opaque codes, no model name inside) → the tool flags "**cannot self-confirm — human must verify this is the right manual**" and blocks auto-extraction until confirmed.
- This gate is **per source document**, not per value — confirm once, then trust the extraction from it.

> ### ⚠️ STANDING RULE — Engine config is NOT generation-stable
> **Before writing dual-value (multi-engine) strings across a generation's year-rows, verify EACH YEAR's actual engine options against its own manual.** Engine options get added or dropped mid-generation — e.g. **Mazda 3 Gen 2 added SkyActiv mid-cycle**; the **Altima 2.0T was dropped for 2025** (the L34 generation was NOT engine-stable); the **Sentra B17 1.6T turbo launched 2017** (not present 2013–2016). **Never assume the lineup is stable across a generation.** A generation-representative manual is fine for the spec *values* (which are generation-stable), but the *engine roster* must be confirmed per model-year — cheap to check (grep each year's PDF for the engine codes). **Write a dual-value string to a year only if that year actually offered both engines; write single-value for years that didn't. Flag any year you cannot confirm rather than guess — leave it gated.**

### 2. Auto-extract + auto-tag from a confirmed source
Once the source is confirmed, the tool extracts spec values (each with page citation) and tags them `owner-manual-verified`. **Clean, unambiguous extractions do NOT require individual human sign-off** — they are written directly. (Clean = single unambiguous value, units explicit, regex high-confidence, single engine or clearly-labeled per-engine.)

### 3. Flag-for-review — the ONLY values needing human judgment
The tool routes to human review **only**:
- Values it couldn't parse cleanly (anchor found, value regex failed → show the page snippet).
- **Unit ambiguity** (liters vs quarts — convert to the UI-label unit).
- **Dual-engine splits it's uncertain about** (multiple values, unclear which engine).
- **Low extraction confidence** (fuzzy table, OCR-ish text).
- **Conflicts** (the manual lists multiple values for one field).

Everything else flows through without stopping the human. The review queue is therefore *small* — only the genuinely ambiguous fields, not the whole spec sheet.

### 4. Status dashboard (so the human filters, never re-checks clean data)
A per-vehicle (and per-field) status view with filters:
| Status | Meaning | Human action |
|---|---|---|
| **Verified** (manual-confirmed) | source confirmed + clean extraction written | **leave alone** — never re-check |
| **Unverified / gated** | AI/scraped/null — still "pending verification" | needs a verification pass |
| **Flagged-for-review** | source confirmed but ≥1 ambiguous field | **human judgment** on the flagged fields only |
| **Source-unconfirmed** | tool fetched a PDF it can't self-confirm matches | **human must confirm or reject the document** |
| **→ Jazerie** | OM-absent fields (§5) | service-manual queue |

The human works **only** the *Unverified*, *Flagged-for-review*, and *Source-unconfirmed* buckets — **clean Verified data is never re-opened.** This is where the time savings come from.

### 5. Spot-check validation (sampling, not full re-check)
Periodically re-verify a **sample** of auto-extracted values against the actual manual page to confirm extraction accuracy (the tool stored the page #, so this is fast). If extraction proves reliable, **trust grows** (sample less); if accuracy drifts, **tighten review** (sample more, or re-flag a field type). **Always fully validate a new make's extraction against ground truth before trusting it at volume** (ties to §7 — the Mazda 3 / Civic regression set + per-make calibration).

**Net effect:** human time concentrates on (a) confirming the *document* and (b) resolving a short flag queue — not on signing off every plainly-stated value. The Toyota failure mode is structurally prevented because **no value is ever written "verified" from a source the human didn't confirm.**

---

## 2. Per-make source map (top makes by gated volume)

Characterized columns: **Portal** (discovery), **PDF host** (direct file), **Direct-fetch?** (no login), **Self-ID?** (manual names the model/year inside), **Grade**. Only the top 3 are pilot-confirmed; the rest are starting points that each **require a 1-vehicle characterization pilot before bulk** (do not trust un-piloted URL patterns).

> **Navigation companion:** `KYR_OEM_Manual_Source_Map.md` is the owner's-portal *navigation* view of this same set — portal URL, direct-PDF vs JS/VIN-gated, VIN requirement, year coverage, access confidence. (June 2026 pass: Ford, Chevrolet/GM, Nissan, Subaru, Hyundai PDF-verified as direct/login-free/VIN-free by year+model; Toyota confirmed JS-gated.) This table stays the *tool-extraction* view (Self-ID / Grade / PDF pattern).

| # | Make | Gated | Portal | PDF host / pattern | Direct? | Self-ID? | Grade | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | Toyota | 348 | toyota.com/owners (JS) | `assets.sia.toyota.com/publications/en/om-s/<CODE>/pdf/<CODE>.pdf` | yes (if code known) | **NO** | **D** | PILOT-CONFIRMED. Full OM doesn't name the model inside → can't confirm match. Use the QRG (addressable) for limited fields, or require human model-confirmation. Hard. |
| 2 | Ford | 272 | owner.ford.com (JS/login) | (per-vehicle, behind login) | likely no | TBD | TBD | Needs pilot. Ford gates manuals behind account login — expect human-fetch. |
| 3 | Chevrolet | 257 | my.chevrolet.com (JS/login) | GM Owner Center | likely no | TBD | TBD | Needs pilot. GM portal typically login-gated. |
| 4 | Honda | 207 | owners.honda.com → mygarage (JS) | `techinfo.honda.com/rjanisis/pubs/om/<code>/<code>om.pdf` | **YES** | **YES** | **B+** | PILOT-CONFIRMED. Full OM directly downloadable, self-identifies, text-extractable. Codes opaque (discovery is JS). Best non-Mazda. |
| 5 | Nissan | 197 | nissanusa.com/owners | (per-vehicle) | TBD | TBD | TBD | Needs pilot. |
| 6 | Cadillac | 137 | my.cadillac.com | GM Owner Center | likely no | TBD | TBD | GM — same as Chevrolet. |
| 7 | Volkswagen | 125 | vw.com/owners | (per-vehicle) | TBD | TBD | TBD | Needs pilot. |
| 8 | **Mazda** | 120 | mazdausa.com | `mazdausa.com/siteassets/pdf/owners-optimized/<YEAR>/mazda3-4door/...` | **YES** | **YES** | **A** | PILOT-CONFIRMED (gold standard). Near-predictable URLs, self-ID, text. 13 vehicles already done. |
| 9 | Dodge | 114 | mopar.com (Ram/Mopar) | (per-vehicle) | TBD | TBD | TBD | Needs pilot. Stellantis/Mopar portal. |
| 10 | Hyundai | 110 | owners.hyundai.com | (per-vehicle) | TBD | TBD | TBD | Needs pilot. |
| 11 | BMW | 104 | bmwusa.com/ownership | (per-vehicle) | TBD | TBD | TBD | Needs pilot. |
| 12 | Buick | 102 | my.buick.com | GM Owner Center | likely no | TBD | TBD | GM. |
| 13 | Acura | 100 | owners.acura.com | `techinfo.honda.com` (Honda group) | likely YES | likely YES | likely B+ | Honda-group — expect Honda-like access. Needs pilot. |
| 14 | Subaru | 100 | subaru.com/owners | (per-vehicle) | TBD | TBD | TBD | Needs pilot. |
| 15 | Jeep | 94 | mopar.com | (per-vehicle) | TBD | TBD | TBD | Stellantis/Mopar. |
| 16 | GMC | 91 | gmc.com/owner-center | GM Owner Center | likely no | TBD | TBD | GM. |
| 17 | Audi | 87 | audiusa.com/owners | (per-vehicle) | TBD | TBD | TBD | VW-group. |
| 18 | Lincoln | 87 | lincoln.com/owners | (Ford group) | likely no | TBD | TBD | Ford-group. |
| 19 | Pontiac/Porsche/etc. | 80+ | — | — | TBD | TBD | TBD | Lower priority / niche. |

**Grouping shortcut:** characterizing one brand often unlocks its corporate siblings — Honda↔Acura (techinfo), Chevy↔Cadillac↔Buick↔GMC (GM Owner Center), Ford↔Lincoln, VW↔Audi, Jeep↔Dodge↔Ram (Mopar). So ~8–10 portal characterizations cover the top ~20 makes.

---

## 3. Candidate-extraction approach

The specifications section is **consistently located** within each make's manuals (Mazda: "Specifications" chapter near the end; Honda: pp. ~348–351; Toyota: spec section near end). The tool uses a **per-make locator config** + generic field parsers.

**a. Locate the spec section** — scan pages for anchor terms and record the page: `Specifications`, `Capacities`, `Recommended Oil` / `Engine Oil`, `Spark Plug`, `Tire` + `Inflation`, `Brake Fluid`, `Lubricant`, `Maintenance` / `Maintenance Minder` / `Schedule`. (This is exactly the `grep terms → page list` step from the pilots — generalizable.)

**b. Field parsers** (regex/heuristic, each returns value + page + snippet):
- Oil viscosity: `SAE \d+W-\d+` / `0W-20`.
- Oil capacity: `\d+\.\d+ (US qt|qt|L)` near "with filter" / "without filter".
- Coolant: type name near "coolant/antifreeze" + capacity.
- Brake fluid: `DOT [34]` / `J1703 / FMVSS116`.
- Trans fluid: `ATF \w+` / `DW-1 / WS / FZ / M-V` / `GL-[45]`.
- Tire: `P?\d{3}/\d{2}R\d{2}` + `\d+ psi` / `\d+ kPa`.
- Spark plug: `NGK \w+` / `DENSO \w+` / Mfr OE `\w+-18-110`.
- Lug torque: `\d{2,3} (lbf?·?ft|N·m)` in the flat-tire section.
- Intervals: fixed-mileage numbers in the maintenance table **OR** detect flexible systems (`Maintenance Minder`, `oil life`, `wrench indicator`) → emit `interval = flexible`.

**c. Confidence + flags:**
- **Engine-divergence flag:** if a field returns >1 distinct value (e.g. two oil capacities) → flag "dual-engine — human writes labeled dual string."
- **Unit flag:** value in liters → flag for L→qt conversion (UI convention is the unit the label shows).
- **Low-confidence:** anchor found but value regex failed → present the page snippet for the human to read manually.
- **Not-found:** field absent from the spec section → candidate = NULL (route to §4 if it's a service-manual field).

**d. Output:** a structured candidate record per vehicle (JSON) + a human-readable review artifact (§3 below) — the same shape as the verification log, pre-filled.

---

## 4. Human review / approval interface

**MVP (lowest friction, reuses current stack):** the tool emits a **pre-filled markdown/CSV review file** per generation — one row per field with `value | page | snippet | confidence | flag`. The human edits it inline (approve as-is, correct, set NULL, or write `→JAZERIE`), then runs an **apply script** that turns approved rows into the write-script pattern (`_write_<vehicle>_specs.py`-style), runs `04_rebuild_demo.py`, and reports the gate flip. This *is* the verification log — review and audit trail in one file.

**Field actions:** `APPROVE` (write value) · `EDIT` (human value) · `NULL` (leave gated/blank) · `→JAZERIE` (service-manual field, §5).

**V2 (if volume warrants):** a tiny local web form (reuse the Python/Vercel stack) showing each candidate with the **PDF page rendered alongside** the parsed value + Approve/Edit/NULL buttons → writes directly. Faster for high throughput, but the markdown MVP is enough to start.

---

## 5. Fields that are NEVER in owner's manuals → Jazerie service-manual handoff

The pilots confirmed (Mazda **and** Honda) these are **not in owner's manuals** — do **not** ask the OM pipeline for them; route to **Jazerie's service-manual verification** ($1.25/verified row):

- **Battery group size + CCA** (OMs give Ah only)
- **Oil drain-plug torque** and **spark-plug torque** (service-manual data)
- **Spark-plug gap** (factory pre-set on modern iridium; not published)
- **Fixed intervals on flexible-system cars** (Honda Maintenance Minder, Mazda/Toyota oil-life) — the OM gives "flexible/oil-life," the *mileage* backstops for plugs/coolant/trans come from the service manual.

**Authoritative source for this stage = licensed service-manual data: ALLDATA / Mitchell 1, or a factory service manual** (see canonical `KYR_Source_Authority_Matrix.md`). **NOT acceptable** — even though convenient and often correct: AutoZone/O'Reilly repair guides, parts-lookup fitment, dealership spec pages, blogs, AI. Convenient-but-unverified is exactly the trap that produced the legacy fabricated data.

**Handoff mechanism:** when the OM pipeline marks these NULL, it **emits a per-vehicle "service-manual-needed" row** to a Jazerie queue CSV (same format as `KYR_Mazda3_Curated_Specs_Needed_v2.csv`). **Two-stage verification:** (1) OM pipeline fills what the OM has → vehicle flips to verified for those fields; (2) Jazerie fills the service-manual remainder from ALLDATA/Mitchell 1 later. Both set `source` to an authoritative value (`owner-manual-verified` or `service-manual-verified`) → both count as `ver=1`. A vehicle can be partially verified (OM fields visible, service-manual fields still gated) — the gate is per-field-table, so this is already supported.

---

## 6. Throughput + priority order

**Human time:** ~**20–30 min per generation** (pilot). The bottleneck is discovery + confirmation, not extraction — and the tool removes the extraction/typing time, so post-tool this should drop toward ~**10–15 min/generation** once a make's portal is characterized.

**Leverage:** one generation = **~4–6 DB vehicle rows** (e.g. 9th-gen Civic = 2012–2015). So generation-level verification is the efficient unit.

**Realistic cadence (part-time, ~2–3 focused hrs/day):**
- ~**8–12 generations/day** post-tool → ~**40–60 generations/week** → ~**200–300 vehicle rows/week**.
- The ~1,668 AI vehicles (+ no-curated rows) ≈ **6–10 weeks** of focused part-time work solo, or faster split with Jazerie on the service-manual fields in parallel.
- **First vehicle of each new make is slower** (full hand-verify to characterize the portal + calibrate the parser — see §7).

**Priority order (highest gated volume first — proxy for traffic; no real analytics yet):**
1. **By make:** Toyota (348) → Ford (272) → Chevrolet (257) → Honda (207) → Nissan (197) → then Cadillac/VW/Mazda/Dodge/Hyundai.
2. **By nameplate (do these first within each make):** F-150, Accord, Civic ✅(started), Camry, Corolla, Jetta, Wrangler, Sentra, Mustang, Altima, Suburban, Explorer, 4Runner, Sonata, Cherokee.
3. **Start where access is easiest:** Honda/Acura (techinfo direct) and Mazda (gold standard) give early wins while the harder portals (Ford/GM login, Toyota no-self-ID) get characterized.

---

## 7. Validation (trust-but-verify the extractor)

The tool's extraction must be **validated against hand-verified ground truth before it's trusted:**

1. **Regression set = the hand-verified Mazda 3 + 2012 Civic.** Run the extractor against *their* manuals and assert it **reproduces the already-approved values** (oil 0W-20, Civic dual capacity 3.9/4.4 qt, FL22, lug torques, etc.). If it can't reproduce known-good values, **fix the parser before using it on new makes.**
2. **Per-make calibration:** the **first vehicle of each new make is fully hand-verified** (the pilot method) to characterize the manual layout + tune the locator/parsers for that make. Only after a make is calibrated does the tool run semi-automated for the rest of that make.
3. **Ongoing spot-check:** for the first ~3 vehicles per make, the human re-reads the cited page to confirm each parsed value (the tool gives the page #, so this is fast). Sample-audit thereafter.
4. **Never silent:** the apply step records the source URL + page per value in the verification log (audit trail), and the review file is retained. Any value the human didn't explicitly approve is **not written** (stays gated).

---

## Risks & notes
- **Login-gated portals (Ford, GM, Stellantis):** the tool can't fetch behind a login → human downloads the PDF, hands the local file to the tool. Design supports "local PDF path" as an input, not only a URL.
- **Toyota's no-self-ID problem:** treat Toyota as human-confirmation-required; consider the QRG for the limited fields it carries, and accept Toyota will be slower.
- **Image-based manuals (older years):** the tool's "not image-based" assertion catches these → route to manual transcription or skip.
- **The gate already protects users** during rollout: anything not yet verified simply stays "pending verification" — there is no pressure to rush and no risk of shipping a wrong value.

---

## 8. Build sequence (phased)

**The logic:** deliver verified popular vehicles *fastest* (Phase 1 needs no tool at all), build the tool *only* once a hand-verified regression set exists to validate it against, and **never let the tool write anything it can't reproduce against hand-verified ground truth.**

### PHASE 1 — Manual method, easy makes, NOW (no tool)
Before building **any** tool, hand-verify the highest-volume **easy-access** nameplates using the exact pilot method (which already works end-to-end):
- **Honda / Acura** (direct `techinfo` PDFs, self-identifying): **Accord, Civic, CR-V** (top gated Honda nameplates). Acura unlocks on the same techinfo access.
- **Mazda** (gold standard, already proven — 13 vehicles done; extend to other Mazda nameplates).

Each vehicle verified by hand now is **two things at once: immediate product value** (a popular vehicle flips gated → verified, live) **and a regression test case** for Phase 2. Target **~10–15 hand-verified vehicles/generations** to form the ground-truth set. Zero tool-build time; pure delivery + test-fixture creation.

*Exit criteria:* ~10–15 hand-verified vehicles exist, each with a page-cited verification log (the Mazda 3 + Civic logs are the template).

### PHASE 2 — Build the extractor + review artifact
**Only after** the Phase 1 regression set exists, build the extraction tool (extractor + per-make locator config + markdown review artifact + apply script, per §3–§4).
- **Hard validation gate:** the tool must **reproduce ALL hand-verified values exactly** — Mazda 3 **+** 2012 Civic **+** the new Phase 1 Honda batch — before it is trusted on anything new. If it can't reproduce a known-good value, fix the parser; do not proceed.
- Source-confirmation gate (§1b.1) and flag-for-review (§1b.3) are built in from the start.

*Exit criteria:* tool reproduces 100% of the regression set; only ambiguous fields flag.

### PHASE 3 — Tool-assisted, scale to login-gated makes
With a validated tool, take on the high-volume **login-gated** makes — **Ford (272), Chevrolet/GM (257 + Cadillac 137 + Buick 102 + GMC 91), Stellantis (Dodge/Jeep/Ram)**. The human downloads the PDF (fetch can't be automated behind login), then the tool extracts + proposes with citations and the human confirms the source + resolves the flag queue. **The tool speeds extraction even when the fetch is manual** — that's its value on these makes.
- Toyota stays human-confirmation-heavy (no self-ID); use the QRG for its limited fields or full human verification.

### PHASE 4 — Jazerie service-manual queue, in parallel throughout
The **service-manual-only fields** (battery group/CCA, drain-plug & spark-plug torque, spark-plug gap, fixed intervals on flexible-system cars — §5) route to **Jazerie from the start**, running **parallel to Phases 1–3**. As each vehicle is OM-verified, its OM-absent fields are emitted to the Jazerie queue CSV. This means a vehicle reaches **full** verification via two independent streams (OM pipeline + service-manual queue) without either blocking the other — and the per-field-table gate already supports partial verification in the meantime.

---

### Sequencing summary
| Phase | What | Tool? | Output |
|---|---|---|---|
| **1** | Hand-verify Honda/Acura (Accord/Civic/CR-V) + more Mazda | **No** | ~10–15 verified vehicles **+ regression set** |
| **2** | Build extractor + review artifact | Build | Tool that **reproduces 100% of Phase 1** ground truth |
| **3** | Tool-assisted on Ford / GM / Stellantis / Toyota | Use | Bulk verification of login-gated, high-volume makes |
| **4** | Jazerie service-manual fields (battery, torque, gap, intervals) | Parallel | Full verification (OM + service-manual streams) |

*Design only — no build yet. Phase 1 can start immediately with the proven manual method.*
