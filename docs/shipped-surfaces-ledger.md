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
- **Ships:** `var __D__ = {v:[3,667 vehicles], dtc, fixes, fuseTsbsByCode:{}}` — the Tier-1
  verified-data core. Per vehicle: identity, gated curated specs (`ver` flags), recalls,
  safety, mpg, warranty, `comp_n`/`comps_agg`.
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
  4. [CI][FAIL] Zero `comps[]` / `fuse_tsbs[]` arrays; `fuseTsbsByCode == {}`. *(Consumer-reports fix)*
  4b. [CI][FAIL] Zero vehicle-level `costs{}` and zero `rel{}`; top-level `fixes == {}`.
     *(Block-1 paid-feature gate, 2026-07-13: `costs` = CarMD/national-only, sold as
     "Regional service costs"; `rel` = unsourced computed reliability score; `fixes` =
     CarMD DTC fix-rate probabilities/costs. The `dtc` definitions map is separate and stays.)*
  5. [CI][FAIL] Blob filename hash == md5-8 of file content; `index.html` references exactly
     one `data.<hash>.js` and that file exists in the repo. *(Desync/404 class)*
  6. [CI][WARN] Payload size budget: warn > 16 MB (was 25.7 pre-fix; ~10.7 after Block-1).
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

## S5. Consumer-reports aggregates — `comps_agg` in the blob + tab/hero copy
- **Ships:** per-vehicle `{by_comp[[component,count]…≤6], crash, fire, inj, deaths, first?,
  last?}` + `comp_n`; "Consumer Reports (NHTSA)" tab with disclaimer + NHTSA link; hero badge
  "N WITH CONSUMER REPORTS".
- **Generator:** `files/04_rebuild_demo.py` (aggregation + hero badge line);
  renderer persisted in `wrench_demo.html`.
- **Current guards:** the aggregation code itself; no output check.
- **Invariants:**
  1. [CI][FAIL] `comps_agg` schema whitelist: keys ⊆ `{by_comp, crash, fire, inj, deaths,
     first, last}` — any extra key (e.g. a narrative field) fails. *(Complaint narratives
     can never return under a new name in this subtree)*
  2. [CI][FAIL] Markup contains the disclaimer string `Unverified consumer-submitted reports
     to NHTSA` and the tab label `Consumer Reports` (not `Complaints`).
  3. [CI][FAIL] Hero badge says `WITH CONSUMER REPORTS`, never `WITH COMPLAINTS`.
  4. [CI][WARN] PII sweep over the `comps_agg` subtree only: zero email/phone/VIN-like
     matches. (Whole-blob sweep stays WARN: recall-remedy text legitimately contains
     manufacturer 1-800 numbers.)

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
  3. [CI][WARN] *(deferred, P1-6 — not yet fixed)*: `No subscriptions, no paywalls` absent
     while Pro plans are sold. **WARN→FAIL flip condition (definition-of-done):** this check
     is promoted to FAIL in the same commit that ships the P1-6 marketing-copy reconciliation
     (the string removed or rewritten to truthful copy). Until then it WARNS on every run —
     deliberately visible noise. It may NOT be silenced any other way; if the copy fix hasn't
     shipped within a reasonable window, the WARN escalates to a scheduled work item, not a
     suppression.

## S8. Cross-cutting
1. [CI][FAIL] `index.html` `kyr-version` matches `^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$`.
2. [CI][FAIL] `index.html` and `wrench_demo.html` agree on every marker this ledger checks
   in both (sample card, footer, disclaimers, empty state) — the two-file drift class.
3. [DB][WARN] Count reconciliation: blob `ver:1` vehicle counts == DB verified counts ==
   `specs.json` `record_count`.
