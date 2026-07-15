# Shipped-Surfaces Ledger — the verifier's spec

**Purpose.** One entry per user-reaching surface: what ships → which generator produces it →
which guard protects it today → the invariants that must hold forever. This is both the spec
for the CI verifier and the standing answer to the 2026-07-11 audit's central finding ("the
integrity gate was enforced on one path; every other surface bypassed it"). Doctrine
(CLAUDE.md): *every file that ships must name its generator; every generator must consume the
gate; audit surfaces, not fixes.*

Invariant tags: **[CI]** = checkable from tracked files alone (runs in GitHub Actions).
**[DB]** = needs the local-only canonical DB (runs pre-deploy on the workstation).
**FAIL** = hard-fail tier. **WARN** = advisory tier.

---

## S1. The data blob — `wrench_deploy/data.<md5-8>.js`
- **Ships:** `var __D__ = {v:[3,667 vehicles], dtc, fixes:{}}` — the Tier-1 verified-data
  core. Per vehicle: identity, gated curated specs (`ver` flags), recalls, safety, mpg, ev,
  `comps_agg`, and (D-2) `guidance`. The full top-level field set is the S1.10 allowlist in
  `_verify_shipped.py`. `warranty` (vehicle-finder aggregator) and `fuse_loc` (AI-generated)
  were stripped 2026-07-14 on provenance grounds — quarantined in the DB, absent here.
- **Generator:** `files/04_rebuild_demo.py` (splices into `wrench_demo.html`) →
  `_deploy_sync_specs.py` (externalizes to `data.<hash>.js`, stamps `index.html`).
- **Current guards:** build-time `_assert_gate_sources` + `_strip_unverified`/`enforce_ver0`
  + 3 `PAYLOAD GUARD` aborts; commit-time `_deploy_check.py` content scan + index↔blob
  desync check.
- **Invariants:**
  1. [CI][FAIL] No object anywhere carries `ver:0` alongside value-bearing keys (bare
     `{ver:0}` shells only). *(P1-1)*
  2. [CI][FAIL] Forbidden strings absent: `"source":`, `last_verified_at`, `ai-haiku`,
     `oilchangediy`. *(C1/F2)*
  3. [CI][FAIL] Zero vehicle-level `notes[]`. *(Known-issues gate)*
  4. [CI][FAIL] Zero `comps[]` / `fuse_tsbs[]` arrays; **`fuseTsbsByCode` root key ABSENT**
     (Block-3 flipped this from "== {}" to "absent" — a TSB-derived root key may not ship at all).
  4b. [CI][FAIL] Zero vehicle-level `costs{}` and zero `rel{}`; top-level `fixes == {}`.
     *(Block-1 paid-feature gate, 2026-07-13: `costs` = CarMD/national-only, sold as
     "Regional service costs"; `rel` = unsourced computed reliability score; `fixes` =
     CarMD DTC fix-rate probabilities/costs. The `dtc` definitions map is separate and stays.)*
  5. [CI][FAIL] Blob filename hash == md5-8 of file content; `index.html` references exactly
     one `data.<hash>.js` and that file exists in the repo. *(Desync/404 class)*
  6. [CI][WARN] Payload size budget: warn > 16 MB (was 25.7 pre-fix; ~9.5 after the
     2026-07-14 warranty/fuse_loc strip).
  6b. [CI][FAIL] **Top-level vehicle field allowlist (default-deny, S1.10):** every key on
     every vehicle object must be in `VEHICLE_FIELDS`; unenumerated fields fail. Closes the
     warranty/fuse_loc class — a field the generator attaches without a `_ver()` path can no
     longer ship unnoticed. New surface ⇒ deliberate new allowlist entry. *(2026-07-14)*
  7. [DB][FAIL] Verified-value equivalence: rebuilding the data JSON from the canonical DB
     reproduces the committed blob (requires a `--check` mode on the rebuild; see design).
  8. [DB][FAIL] `_assert_gate_sources` over the live DB: no blacklisted source computes `ver=1`.

## S2. SEO vehicle pages — `wrench_deploy/vehicles/*/index.html` (3,540) + `sitemap.xml` + `robots.txt`
- **Ships:** static per-vehicle pages (meta, JSON-LD, prose, quick-spec table), currently
  containing unverified values but **contained** (noindex + delisted). DTC pages
  (`wrench_deploy/dtc/*`) remain indexable.
- **Generator:** `wrench_seo.py` (reads the DB directly — pre-gate path; verified-only
  regeneration is the deferred Phase-3 fix).
- **Current guards:** none beyond the containment being baked into the generator. This ledger
  entry is the guard.
- **Invariants (containment, until the verified regen ships):**
  1. [CI][FAIL] Every `vehicles/*/index.html` contains `<meta name="robots" content="noindex`.
  2. [CI][FAIL] No vehicle page contains `sourced from EPA, NHTSA and manufacturer` (the
     false attribution). *(P0-1)*
  3. [CI][FAIL] `sitemap.xml` contains zero `/vehicles/` URLs.
  4. [CI][FAIL] DTC pages contain **no** noindex (they must stay indexable), and the sitemap
     retains `/dtc/` URLs.
  5. [CI][WARN] `robots.txt` still allows crawl (noindex only works if crawlable).
  *(When the verified-only regen lands, invariants 1–3 flip to "verified-values-only" checks
  and this entry is rewritten.)*

## S3. Homepage sample card — `#kyr-sample` in `index.html` / `wrench_demo.html` (+ `kyrHsDefaultPlacard`)
- **Ships:** one hard-coded hero card + a JS placard, both featuring vehicle id **12912**
  (2022 Honda CR-V, owner's-manual-verified).
- **Generator:** hand-maintained in canonical `wrench_demo.html`; `_deploy_sync_specs.py`
  propagates to `index.html`.
- **Current guards:** none (fixed by P0-3, unprotected since).
- **Invariants:**
  1. [CI][FAIL] The static card and `kyrHsDefaultPlacard` reference the same vehicle id, and
     that id's blob record has `oil.ver == 1` (and `parts.ver == 1`).
  2. [CI][FAIL] Every hard-coded spec value in the card (viscosity, capacity) appears verbatim
     in that vehicle's `ver:1` blob record — no value drift, no fabrication. *(P0-3)*
  3. [CI][FAIL] The old fabricated strings (`0W-20 Full Synthetic`, `14mm &middot; M12x1.25`,
     `openModal(12802)`) are absent.

## S4. Paid-guide input — `wrench_deploy/api/specs.json` (+ `guide.py` consumption)
- **Ships:** 290 owner's-manual-verified vehicle records `{label, oil, parts, torque}` +
  `_meta` provenance header, bundled into the Pro guide function.
- **Generator:** `_gen_guide_specs.py` (deterministic; verified rows only).
- **Current guards:** commit-time `_deploy_check.py` marker check (staged specs.json must
  carry `_meta.generated_by == "_gen_guide_specs.py"`).
- **Invariants:**
  1. [CI][FAIL] `_meta.generated_by == "_gen_guide_specs.py"` and
     `_meta.record_count == len(records)`.
  2. [CI][FAIL] Schema whitelist: record keys ⊆ `{label, oil, parts, torque}`; oil keys ⊆
     `{viscosity, oil_type, capacity, oem_spec}` (gated fields — `oil_filter`,
     `drain_socket/thread/gasket` — must be ABSENT); torque keys ⊆
     `{lug_nut, drain_bolt, spark_plug}`. *(P0-2: the old fabricated file fails this)*
  3. [CI][WARN] File size < 500 KB (the fabricated legacy file was 1.0 MB).
  4. [DB][FAIL] Regeneration equivalence: running `_gen_guide_specs.py` against the canonical
     DB reproduces the committed file byte-for-byte (determinism makes this exact).

## S5. Common Customer Complaints — `comps_agg` in the blob + Safety-tab card
- **Ships:** per-vehicle `{n, topics[[label,count]…≤6], crash, fire, inj, deaths, through?}` —
  normalized NHTSA component topics (distinct-ODI, KYR grouping), a distinct-ODI denominator
  `n`, and a month-granularity incident cutoff `through` ("YYYY-MM"). Rendered as three provenance
  lanes inside **Safety** (customer-reported / manufacturer-documented teal empty-state / recall);
  hero badge "N WITH CONSUMER REPORTS". **No TSB / manufacturer-guidance data ships (Phase 1).**
- **Generator:** `files/04_rebuild_demo.py` — component normalization (split on comma-not-
  followed-by-space, roll up to NHTSA parent; never naive-split), year/make/model distinct-ODI
  union projected onto engine-variant ids (fixes 2020/2021 RAM 1500 double-count), month cutoff,
  hero badge line. Renderer + 3-lane copy persisted in `wrench_demo.html` (the fossil `inject_tab`
  injector was deleted — the tab is fully hand-authored).
- **Current guards:** S5.1–S5.8 below.
- **Invariants:**
  1. [CI][FAIL] `comps_agg` schema whitelist: keys ⊆ `{n, topics, crash, fire, inj, deaths,
     through}`; each topic is a `[label, int]` pair (no narrative, no nested guidance object).
  2. [CI][FAIL] Markup ships the `Common Customer Complaints` heading + the permanent NHTSA
     disclaimer (`Complaints are reports submitted to NHTSA, not verified defects`); the obsolete
     standalone `Consumer Reports` tab label is absent.
  3. [CI][FAIL] Hero badge says `WITH CONSUMER REPORTS`, never a bare `WITH COMPLAINTS`.
  4. [CI][WARN] PII sweep over the `comps_agg` subtree only: zero email/phone/VIN-like matches.
  5. [CI][FAIL] **Labeled count** — the render carries `NHTSA complaint records mention {topic}`
     (label + denominator); no bare ratio may ship. No forbidden framing (confirmed/known defect,
     guaranteed/usual fix, NHTSA-recommended/free repair) — matched affirmatively, so the honest
     `not confirmed defects` footer is allowed.
  6. [CI][FAIL] **Incident-date phrasing** — approved `Incident dates through {Month Year}` present;
     banned `data through` / `retrieved` / `updated as of` / `reported through` absent (the field is
     `dateOfIncident`, and `pull_log` covers only 127/1040, so no ingest guarantee may be implied).
  7. [CI][FAIL] **TSB gate — no *unverified* TSB content** (evolved from "no TSB content" in
     Block D-1; threshold ruling 2026-07-14). Top-level blob keys ⊆ `{v, dtc, fixes}`; raw
     TSB-family keys (`tsb`/`bulletin`/`manufacturer_documented`/`service_action`/`fuseTsbsByCode`/…)
     still forbidden. A per-vehicle **`guidance`** object is the ONE allowed door and ships only if
     every entry is a complete human-verification record: full stub (`tsb`/`url`/`vhash`/`vby`/`vat`),
     an **official NHTSA host** URL, whitelisted keys only
     (`{topic,tsb,date,comp,sym,act,applies,url,tcount,n,vby,vat,vhash}`), `tcount`/`n` integers, short
     KYR descriptors (≤220 chars, ≤2 sentences, one line — never abstract prose), and **no frequency
     framing** in `sym`/`act`/`topic`. The topic need NOT be a threshold-clearing customer topic (a
     verified pairing may surface a below-threshold topic); its count honesty is enforced DB-side (9).
     The teal `No matching manufacturer guidance found` empty-state string must remain in the source.
     *(Default-deny intact: an unverified pairing is structurally incapable of shipping.)*
  8. [DB][FAIL] **Retrieval date matches DB** — every shipped `comps_agg.through` equals the
     DB-derived clamped max incident month for that year/make/model, and is not a hardcoded literal
     (values must vary and match the recomputation).
  9. [DB][FAIL] **Guidance count matches DB** — every shipped `guidance.topic` is a real normalized
     complaint component for the vehicle, and `tcount`/`n` equal the DB-derived distinct-ODI counts
     (a below-threshold pairing may surface its topic, but never with a fabricated count).

**Manufacturer-communication pairing pipeline (Block D-1).** Local-only `tsb_pairings` table +
`_tsb_pairing.py` CLI (`init` / `add` / `list` / `recheck` / `candidates`). A pairing is created
only as a COMPLETE verification record — the CLI enforces topic-ships / official-host / length
bounds / bulletin-on-file before writing, and fetches+hashes the reviewed NHTSA document. The
generator emits a `guidance` blob object only from complete, non-superseded rows (never NHTSA
abstract prose or a PDF). `recheck` refetches each `source_url` and flags a hash mismatch as
`superseded` (supersession/rot detection), which drops the guidance from the next build. The 394
import-cap-truncated vehicles are flagged in `tsb_truncated` for D-2 targeting — never surfaced in
the UI (per ruling: never claim completeness, no per-vehicle caveat). D-2 = the content campaign
(verifying bulletins one at a time); D-1 makes it structurally safe to run incrementally.
**Shipped pipeline-only (2026-07-14): zero guidance objects in the blob; the gate holds vacuously.**
The first production pairing must be topic-exact and deliberate (it sets the D-2 precedent), not
chosen because a topic happens to clear the display threshold.

**RESOLVED (2026-07-14 ruling).** A human-verified pairing MAY surface its own topic **below** the
customer-reported display threshold — a verified manufacturer document a human confirmed applies to
this exact vehicle is categorically stronger evidence than a sparse count, and shouldn't be
suppressed because complaints happen to be few. This also removes the pressure that pushed the
Ascent pairing toward a threshold-clearing topic. Constraints, verifier-enforced:
- a below-threshold pairing is a **distinct card state** that leads with the manufacturer evidence,
  not the count; it may never carry "Frequently reported to NHTSA" or any frequency framing
  (`S5.7-tsb-gate`: `FREQ_FRAMING` forbidden in guidance `sym`/`act`/`topic`);
- its count, if shown, is honestly labeled and **unemphasized** — "{tcount} of {n} NHTSA complaint
  records mention {topic}." — and **omitted at tcount = 0** (showing "0 of N" would undercut the
  evidence). *(Implemented: shown unemphasized when ≥1, omitted at 0 — reads more transparently than
  a blanket omit.)*
- the count must be **honest**: `S5.9-guidance-count` (DB-tier) asserts the topic is a real
  normalized complaint component for the vehicle and `tcount`/`n` equal the DB-derived values;
- the **orange (customer) lane threshold is unchanged** — a topic with no verified pairing still
  needs ≥3 records and ≥10% to appear at all.
The gate no longer requires a guidance topic to be a shipping customer topic (that requirement was
removed from `S5.7-tsb-gate` invariant 7); it requires a complete verification record, an official
source, no frequency framing, and a DB-honest count.

## S6. Known-issues gate — absent `notes[]` + empty-state markup
- **Ships:** nothing (the gate). `renderIssues` shows the honest empty state with cross-links;
  no count chip, no tab badge.
- **Generator:** gate lives in `files/04_rebuild_demo.py` (export removed); empty state in
  `wrench_demo.html`.
- **Current guards:** none beyond the code being gone.
- **Invariants:**
  1. [CI][FAIL] Blob: zero vehicle-level `notes[]` (shared with S1.3 — listed here as the
     surface's defining invariant).
  2. [CI][FAIL] Markup (both HTML files, data excluded): zero matches for
     `known issues? documented|Documented model-specific|issues documented`.
  3. [CI][FAIL] The empty-state string `No verified model-specific issues on file` present
     exactly once per HTML file.
  *(Rewritten when the TSB/recall-derived rebuild (option D) ships.)*

## S7. Footer & attribution claims — `wrench_demo.html` / `index.html` footer
- **Ships:** per-source attribution: NHTSA structured data; EPA/FuelEconomy.gov (U.S.
  DOE/ORNL); unverified-consumer-reports note; non-affiliation line.
- **Generator:** hand-maintained in canonical `wrench_demo.html`; sync propagates.
- **Current guards:** none.
- **Invariants:**
  1. [CI][FAIL] Required strings present: `U.S. DOE/ORNL`, `not confirmed defects`,
     `not affiliated with NHTSA`.
  2. [CI][FAIL] Forbidden blanket claim absent: `(U.S. Government, public domain)`.
  3. [CI][**FAIL**] `No subscriptions, no paywalls` absent while Pro plans are sold.
     **P1-6 CLOSED (Block-2, 2026-07-13):** the copy was rewritten to truthful free-core +
     optional-Pro framing and this check flipped WARN→FAIL in the same commit, per the
     definition-of-done. Absence is now a hard invariant; the string may never return.
  4. [CI][FAIL] **OBD-II panel fully absent** — no `obd-panel` / `OBD-II Live Diagnostics` /
     `obdConnect` / `/*WRENCH_OBD*/` / `/api/obd` in either HTML file; `wrench_deploy/api/obd.py`
     does not exist; `vercel.json` does not route `/api/obd`; and the DTC Code Lookup pane
     (`id="pane-codes"`) still survives. *(Block-2 OBD removal: dead stub feature — no companion
     app ever shipped — quarantined at every surface incl. the generator's fossil injectors.)*

## S8. Cross-cutting
1. [CI][FAIL] `index.html` `kyr-version` matches `^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$`.
2. [CI][FAIL] `index.html` and `wrench_demo.html` agree on every marker this ledger checks
   in both (sample card, footer, disclaimers, empty state) — the two-file drift class.
3. [DB][WARN] Count reconciliation: blob `ver:1` vehicle counts == DB verified counts ==
   `specs.json` `record_count`.
