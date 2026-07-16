# Option A: Integrity and Mobile Performance Design

**Status:** Approved in chat on 2026-07-16
**Scope:** Know Your Ride consumer application, its public data artifacts, Pro-guide inputs, and vehicle SEO generator
**Deployment:** This document authorizes design and planning only. Every implementation release remains preview- and approval-gated.

## 1. Purpose

Know Your Ride will first contain remaining public data-integrity risks, then move every public consumer surface onto one verified-data projection, and finally replace the full-catalog initial render with a search-first mobile experience.

This work must preserve the existing two-tier doctrine:

- Tier 1 remains a static, DoD-severable reference artifact with no runtime database or proprietary Vercel service dependency.
- Tier 2 remains a decoupled commercial layer. This design does not expand its runtime footprint.

## 2. Current problem

The 2026-07-16 audit established four related problems:

1. Public vehicle SEO pages still read raw database tables through a pre-gate generator. They are noindexed and delisted, but they still contain material that the application correctly strips.
2. Verification is not enough without exact applicability. A source-cited value can still be wrong for the selected engine or configuration, as demonstrated by the Honda CR-V projection.
3. The browser receives and renders far more data than the first screen needs. The current mobile page mounts all 3,667 vehicle cards and loads the detailed vehicle blob up front.
4. The application, guide input, and SEO pages do not yet consume one identical public projection, leaving room for gate drift.

The current controlled-vocabulary complaint parser, complaint projection-equivalence checks, warranty/fuse payload removal, and existing shipped-artifact checks are retained. This design is additive and must not recreate or weaken those controls.

## 3. Approved product rulings

The following decisions are binding:

- Vehicle SEO pages remain noindexed and outside the sitemap during containment.
- During containment, those pages show vehicle identity plus verified government recall and safety information only. They do not show maintenance specifications, complaint excerpts, complaint aggregates, unpaired bulletin counts, or inferred repair content.
- Configuration-dependent values remain hidden until every required applicability dimension is confirmed.
- The vehicle finder becomes search-first. It does not render the full catalog before a query.
- Offline support includes the compact identity index, garage vehicles, and recently viewed vehicle details. It does not preload every vehicle's detailed data.
- Delivery is incremental: contain first, build the shared projection second, cut the frontend over third, and retire legacy artifacts last.

## 4. Shared verified-data architecture

The canonical SQLite database remains private and build-time only. A deterministic projection step becomes the sole source of public vehicle facts.

```text
Canonical SQLite database
          |
          v
Exact source + applicability validation
          |
          v
Shared verified projection
          |-- compact vehicle identity index
          |-- per-vehicle detail artifacts
          |-- Pro-guide inputs
          `-- safe SEO render models
```

No public generator may query a raw specification table after the migration. It must consume the shared projection or a deliberately narrower projection derived from it.

### 4.1 Exact source contract

Source approval changes from substring recognition to an exact-token registry governed by the Source Authority Matrix.

For every projected field, the registry defines:

- accepted exact source identifiers;
- the vehicle field types that source is authoritative for;
- required citation metadata;
- whether the source may be redistributed, linked, or used only for internal verification;
- any expiry or review requirement.

Unknown tokens, compound tokens that have not been explicitly registered, blacklisted sources, and a source used outside its approved field type fail validation. They never degrade into a warning or `ver:0` value-bearing object.

Internal evidence may remain richer than the public artifact. The public projection emits only an allowlisted citation label, official URL where permitted, and verification/revision metadata approved for redistribution. Private notes, extracted manual text, internal file paths, and confidential source material never ship.

### 4.2 Applicability contract

Verification and applicability are independent gates. A value ships only when both pass.

Each curated value declares the applicability dimensions required by that fact, selected from:

- model year;
- make and model;
- engine family/code and displacement;
- fuel or electrification type;
- transmission;
- drivetrain;
- body or chassis;
- trim/package;
- production/build-date range;
- VIN restriction.

The exact required dimensions vary by field. For example, oil capacity commonly requires engine identity, while an NHTSA recall can require a VIN or production range. The projection must not substitute a vehicle-wide match where the source is configuration-specific.

If a required dimension is blank, combined, contradictory, or not confirmed for the selected vehicle, the value is omitted with a machine-readable omission reason. The UI renders a configuration-confirmation state, not a likely value or a union of possible values.

The Honda CR-V case becomes a permanent negative regression fixture: a 2.4L-only fact must be structurally unable to project onto a 1.5L vehicle.

### 4.3 Complaint identity contract

The existing controlled NHTSA component vocabulary, distinct-ODI counting, parent-topic collapse, thresholds, labeling, and evidence-lane framing remain unchanged.

Identity is repaired before aggregation:

- Preserve and use the original NHTSA product assignment when complaints are ingested.
- Normalize year/make/model only after retaining the source product identity.
- Quarantine an ODI record when its source identity is missing, contradictory, or maps to more than one normalized vehicle identity and cannot be resolved deterministically.
- Emit a reconciliation report listing affected ODIs, identities, and resulting topic-count deltas.
- Never silently assign an ambiguous complaint to every matching database vehicle.

Complaint narratives continue to remain private. Public output is limited to the already-approved aggregate schema and verified manufacturer-guidance door.

## 5. Public artifacts

The shared projection produces a versioned artifact set and a deterministic manifest.

### 5.1 Identity index

The compact identity index contains only information needed to search and choose a vehicle:

- stable public vehicle identifier;
- year, make, and model;
- available configuration labels/options;
- coarse coverage flags used for honest result messaging;
- detail-artifact reference and revision.

It contains no detailed specifications, recall prose, complaint data, service history, VIN, or user data.

### 5.2 Per-vehicle detail artifact

A detail artifact contains only allowlisted projected fields for one confirmed public vehicle identity/configuration. It may include:

- verified overview specifications;
- verified maintenance schedule and parts where applicable;
- government recall and safety data;
- approved complaint aggregates and verified guidance;
- public evidence labels and revision metadata.

Unverified shells and inapplicable alternative-engine values are absent rather than null-filled payloads.

### 5.3 Guide input

Guide input is derived from the same in-memory projected record used for the public detail artifact. It cannot run a separate specification query or accept an older ungated data file. If the selected configuration lacks the required verified inputs, guide generation returns the existing honest unavailable state and does not call the model.

### 5.4 SEO render model

Release A1 uses a deliberately narrower safety-only model: identity plus verified government recall/safety facts. Existing noindex and sitemap-delisting guards stay active.

After the shared projection is proven, a later ruled release may add configuration-specific verified specifications. A model-year page with unresolved configuration may not publish engine-specific values.

## 6. Mobile and offline experience

### 6.1 Initial screen

The first screen contains:

- vehicle search/VIN entry;
- signed-in garage vehicles when available;
- recently viewed vehicles stored on the device;
- clear online/offline state.

It mounts no complete catalog and no hidden card wall.

### 6.2 Search and selection

- Search uses the compact identity index.
- Results are ranked by exact year/make/model matches and rendered in bounded batches, initially no more than 20 cards.
- Additional results load only through an explicit continuation action or bounded progressive loading.
- Choosing an identity with more than one required configuration opens a confirmation step before dependent facts render.
- A user may browse identity-level recall/safety information without pretending an engine configuration has been confirmed, where those facts are genuinely identity-level.

### 6.3 Detail loading

Selecting a vehicle fetches its detail artifact. Loading, absent, unavailable, and invalid-revision states are distinct. Failure never falls back to the legacy raw database, a stale embedded object, or inferred values.

### 6.4 Offline boundary

The service worker caches:

- the application shell;
- the compact identity index;
- detail artifacts for garage vehicles;
- a bounded set of recently viewed detail artifacts;
- the manifest needed to label cached revisions.

An uncached vehicle displays an honest connection-required state. A cached, previously verified record remains readable offline and is labeled with its data revision. When connectivity returns, the client checks the manifest and refreshes changed records without deleting a usable cached record before its replacement verifies successfully.

### 6.5 Mobile and accessibility requirements

- No horizontal document overflow at a 390 x 844 viewport.
- Initially mounted vehicle-result cards: zero before search and at most 20 after the first query.
- Wide tabular content becomes a stacked or horizontally-contained mobile component, never a page-width expansion.
- Interactive targets, focus indicators, keyboard order, headings, labels, and evidence-lane contrast meet WCAG 2.2 AA expectations.
- Empty states distinguish not verified, not applicable, configuration required, unavailable online, and no matching government record.

## 7. Failure handling and privacy

- Projection output is atomic. The generator writes a candidate artifact tree, validates every file and manifest hash, and only then makes the set eligible for commit/deployment.
- Any invalid source, unexpected public key, applicability conflict, ambiguous identity, broken reference, or artifact-hash mismatch fails the build.
- Missing detail files return a safe unavailable state and generate a diagnostic event without including VINs or user content.
- Analytics may record aggregate events such as search started, results count bucket, configuration requested, and detail load success/failure. Analytics must not receive VINs, full search text, service notes, receipt data, garage contents, or maintenance history.
- No user-specific data is added to Tier 1 artifacts or service-worker shared caches.

## 8. Verification contract

All current shipped-artifact checks remain. New checks are additive.

### 8.1 Unit and fixture tests

Required coverage includes:

- exact-token source acceptance and rejection;
- field/source authority mismatches;
- every applicability dimension and missing-dimension failure;
- the CR-V cross-engine regression;
- ambiguous NHTSA product identities;
- controlled complaint parsing and distinct-ODI aggregation;
- artifact schema allowlists and reference integrity;
- cache revision selection and offline fallback behavior.

Negative fixtures must prove that blacklisted, unknown, compound-unregistered, inapplicable, conflicting, and unexpected-field inputs cannot ship.

### 8.2 Projection equivalence

Integration tests independently recompute representative records from the canonical database and assert:

- the app detail artifact, guide input, and any enabled SEO field agree exactly;
- safety-only SEO contains no maintenance, complaint, bulletin-pairing, repair, or cost fields;
- every public artifact is referenced by the manifest and every reference hash matches;
- output is byte-for-byte deterministic for the same database and explicit release version.

### 8.3 Browser tests

Browser coverage includes:

- clean first load at 390 x 844;
- no full-catalog render and no horizontal overflow;
- bounded search result rendering;
- exact configuration confirmation;
- unavailable configuration-specific facts before confirmation;
- garage and recently viewed records offline;
- uncached offline behavior;
- keyboard navigation and visible focus;
- loading, missing-file, hash-failure, and stale-cache states.

### 8.4 Performance budgets

The release gate enforces structural budgets rather than relying only on timing-sensitive scores:

- zero detailed vehicle records in the initial identity index;
- zero vehicle-result cards before a search;
- no more than 20 initially mounted result cards;
- fewer than 2,000 DOM nodes on the clean mobile first screen;
- document scroll width no greater than client width at the target mobile viewport;
- explicit compressed-size budgets for the identity index and largest detail artifact, set from the A2 baseline and prevented from regressing without a ruling.

## 9. Delivery sequence

### A1 - Immediate containment

- Reduce vehicle SEO pages to identity plus verified government recall/safety facts.
- Preserve noindex and sitemap delisting.
- Quarantine the known CR-V applicability error and any equivalently proven cross-configuration projections.
- Quarantine demonstrably ambiguous complaint identities and report every count delta.
- Replace substring source acceptance with the exact registry.
- Run all existing and new containment fixtures.
- Pause with artifact deltas and representative rendered pages before deployment approval.

### A2 - Shared projection

- Implement the shared projection, manifest, identity index, per-vehicle details, guide input, and safety-only SEO model.
- Generate legacy and new artifacts side by side.
- Prove verified-value equivalence where the contracts overlap and explain every deliberate omission.
- Do not cut the frontend over in this release.

### A3 - Mobile cutover

- Move search and vehicle details to the split artifacts.
- Add bounded rendering, configuration confirmation, service-worker revision handling, and honest offline states.
- Retain the legacy artifact as an immediate rollback path during production verification.

### A4 - Cleanup

- Remove the legacy initial-load detailed blob only after live verification.
- Retire direct raw-table reads from public generators.
- Update the shipped-surfaces ledger, artifact inventory, and deployment checks.

Each release uses its own targeted commit, local proof, preview, explicit deployment approval, live verification, and rollback record. No release automatically authorizes the next.

## 10. Success criteria

Option A is complete when:

- every public vehicle fact comes from the shared verified projection or an explicitly narrower derivative;
- configuration-specific values cannot ship without confirmed applicability;
- ambiguous complaint identities cannot affect public counts;
- vehicle SEO contains no raw-table specification path;
- the clean mobile page does not load or render the detailed catalog;
- saved and recently viewed vehicle details work offline with revision labeling;
- app, guide, and enabled SEO facts are machine-proven equivalent;
- all legacy checks plus the new semantic, browser, and performance gates pass in CI and locally.

## 11. Non-goals

This design does not:

- add telematics or KYR hardware;
- add offline writes or conflict resolution;
- redesign account/session security;
- add receipt uploads, PDF export, public sharing, fleet workflows, or new paid features;
- reintroduce warranty, service-cost, reliability, fuse-location, raw complaint, or unverified TSB data;
- make a legal conclusion about third-party redistribution rights.
