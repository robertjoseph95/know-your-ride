# Common Customer Complaints — Design Specification

**Date:** 2026-07-12
**Status:** Approved design
**Product:** Know Your Ride
**Scope:** Consumer vehicle detail experience and its supporting verified-data pipeline

## Summary

Replace the empty **Known Issues** surface with **Common Customer Complaints**, using complaint patterns submitted to the National Highway Traffic Safety Administration (NHTSA). Pair each qualifying complaint topic with exact-applicable manufacturer service guidance when an authoritative manufacturer communication is available. Keep complaint evidence, manufacturer guidance, and recalls visibly separate so the product never implies that an owner report is a confirmed defect, that a bulletin establishes prevalence, or that a documented service action is a guaranteed repair.

The selected presentation is a mobile-first vertical evidence card:

1. customer-reported concern;
2. manufacturer-documented guidance;
3. related recall and VIN action;
4. permanent disclosure and source links.

The feature reuses the complaint aggregates that already ship, removes the duplicate **Consumer Reports** surface, and requires a verified rebuild of manufacturer-communication data before repair guidance can be published.

## Goals

- Help owners understand which concerns appear most often within NHTSA complaint records for their exact year, make, and model.
- Pair a reported pattern with manufacturer-documented symptoms, possible causes, and service actions when applicability can be defended.
- Preserve KYR's Data Integrity Gate across every generated artifact.
- Make the feature easy to read and operate on a phone.
- Provide useful next actions without diagnosing a vehicle or promising a repair.
- Reduce duplicate and empty vehicle-detail surfaces.

## Non-goals

- Estimating failure rates or vehicle reliability from complaint counts.
- Claiming that NHTSA verified an owner allegation.
- Calling a TSB a recall, warranty, or free repair.
- Predicting which repair will work from complaint narratives, AI, forums, retailers, or unrelated model years.
- Publishing raw complaint narratives.
- Building a public content-management system for the first release.
- Importing full bulletin PDFs into the public application payload.

## Existing State

The canonical database currently contains:

- 3,667 vehicles;
- 274,258 complaint records covering 1,040 vehicle IDs;
- 167,699 TSB rows covering 1,748 vehicles;
- 8,610 recall rows covering 1,657 vehicles;
- 1,199 `vehicle_notes` rows, all unsourced or AI-sourced and correctly gated;
- an empty `common_problems` table.

The shipped complaint projection already includes aggregate counts, most-reported components, crash/fire/injury/death totals, a plausible incident-date range, an NHTSA disclaimer, and a link to NHTSA. Raw narratives remain private because they are unverified owner allegations and may contain complainant-entered identifiers.

The current TSB table cannot support repair guidance. Every TSB summary is empty, applicability metadata is incomplete, and the table lacks the evidence required to publish a cause or correction. It remains quarantined for this feature until rebuilt from official manufacturer communications.

## Product Placement

### Before vehicle-tab consolidation

- Rename **Known Issues** to **Common Customer Complaints**.
- Render the new paired-evidence experience in that tab.
- Remove the duplicate **Consumer Reports** tab.

### After vehicle-tab consolidation

Place **Common Customer Complaints** inside the vehicle's **Safety** section, alongside NHTSA ratings and recalls. The top-level vehicle structure remains:

1. Overview;
2. Maintenance;
3. History;
4. Safety.

## Evidence Model

The public projection uses three provenance states that must never be collapsed into a generic `verified` label.

### `customer_reported`

The source is a consumer complaint received by NHTSA. This state proves that the report exists in NHTSA's records. It does not verify the alleged incident, defect, diagnosis, cause, or repair.

Required provenance:

- exact year, make, and model;
- distinct NHTSA/ODI complaint number;
- NHTSA component category;
- received or incident date when available;
- safety-event flags when present;
- source snapshot and retrieval date.

### `manufacturer_documented`

The source is an official manufacturer communication hosted or indexed by NHTSA. This state may support the manufacturer's documented symptom, possible cause, diagnostic direction, and service action for the communication's precise applicability.

Required provenance:

- NHTSA communication ID;
- manufacturer bulletin/document number;
- communication type and issue date;
- exact year/make/model applicability;
- engine, trim, build-date, or VIN restrictions when stated;
- symptom;
- manufacturer-stated possible cause, if stated;
- high-level service action;
- source document URL;
- revision or supersession state;
- retrieval date and source-file hash.

### `recall_confirmed`

The source is an official NHTSA recall record. This state may support the recall summary and official remedy. It does not prove that the recall explains every complaint in the same component category.

Required provenance:

- campaign number;
- affected component;
- summary and remedy;
- park/do-not-drive status when present;
- NHTSA source URL;
- retrieval date.

## Complaint Aggregation Rules

1. Group by exact year, make, and model.
2. Count distinct complaint/ODI numbers once per normalized topic.
3. A complaint may contribute to more than one topic when the source identifies multiple components; disclose that topic totals can exceed the distinct complaint total.
4. Prefer NHTSA's component classification. Any KYR-created component mapping is labeled as a KYR grouping and must be deterministic and reviewed.
5. Do not compute failure rates, ownership percentages, cross-model reliability rankings, or prevalence comparisons without a defensible exposure denominator.
6. Show the source-data cutoff date.

### Complaint topic text

The first release derives each public topic name from the normalized NHTSA component category, for example **Electrical system concerns**. It does not publish, paraphrase, or summarize complaint narratives.

A future curated symptom theme may be added only when:

- at least three distinct complaint/ODI numbers support the same controlled-vocabulary theme;
- the theme is labeled as a **KYR grouping of NHTSA reports** rather than an NHTSA finding;
- a human reviewer verifies every supporting complaint and removes any personal information;
- the publication record retains the supporting complaint IDs and reviewer decision; and
- the theme describes what owners reported without asserting a cause, defect, diagnosis, or repair.

AI may propose an internal theme for review but cannot publish one. This future capability is not required for Phase 1.

### Display thresholds

A topic is labeled **Frequently reported to NHTSA** only when:

- at least three distinct complaint numbers mention the normalized topic; and
- the topic represents at least 10% of the exact model-year's distinct complaint records.

When fewer than five total complaint records exist, show **Limited NHTSA complaint data** and do not rank topics. When no topic meets the threshold, say **No complaint pattern currently meets KYR's display threshold**. Never say that the vehicle has no problems or no complaints unless the exact statement is limited to the retrieved NHTSA record set and date.

Show the three highest-count qualifying topics initially, with a 44-pixel-or-larger **Show all complaint topics** control. The expanded list may contain no more than six topics in the initial release.

## Manufacturer-Communication Ingestion

Use NHTSA's documented manufacturer-communication bulk downloads and NHTSA-hosted manufacturer documents. Do not depend on an undocumented TSB API.

Pipeline:

1. Download a dated official snapshot.
2. Preserve its hash, retrieval timestamp, source URL, and format version.
3. Parse into staging tables without modifying the currently published projection.
4. Normalize make/model/year and component identifiers deterministically.
5. Extract structured applicability, symptom, possible cause, service action, document URL, revision, and supersession fields.
6. Generate candidate links between complaint topics and manufacturer communications.
7. Require a human reviewer to approve each publishable link.
8. Build a compact, verified public projection.
9. Run the shipped-surface verifier and feature-specific negative fixtures before deployment.

An AI model may propose internal classifications or draft a summary, but its output is never authoritative. A human reviewer must compare every published field with the manufacturer document, and the publication record must cite that document directly.

## Matching Rules

- The communication must match the exact year, make, and model represented by the vehicle record.
- Every stated engine, trim, transmission, drivetrain, build-date, plant, or VIN restriction must be satisfied by known vehicle information.
- If the application lacks information needed to resolve a restriction, the communication is ambiguous and is not paired as repair guidance.
- Never transfer guidance between model years or powertrains because symptoms appear similar.
- A complaint topic may link to multiple current communications only when each has distinct, defensible applicability.
- A superseded communication is not published; its current revision replaces it.
- A bulletin without a qualifying complaint pattern may remain available as manufacturer service information but is not labeled common.
- A related recall remains a separate action card and is never presented as proof of the complaint's cause.

## Mobile-First Experience

The feature uses one vertical column on phone, tablet, and desktop. It does not switch to a side-by-side evidence layout.

Each topic begins as a compact summary containing:

- normalized concern/component name;
- `X of Y NHTSA reports`;
- safety-event indicator when applicable;
- data-through date;
- expand/collapse control with a minimum 44-by-44-pixel target.

Expanded order:

1. **Customer-reported concern** — normalized NHTSA component, complaint count, and date span; an optional curated symptom theme may appear only under the separate rules above;
2. **Manufacturer-documented guidance** — bulletin number/date, applicability, documented symptom, possible cause, and high-level service action;
3. **Related safety recall** — VIN-check action and official remedy when applicable;
4. permanent disclaimer;
5. source links.

Mobile requirements:

- no horizontal tables or required horizontal scrolling;
- no information conveyed by color alone;
- accessible contrast and visible focus states;
- screen-reader labels for expansions, badges, and external links;
- preserve scroll position when expanding a card or returning from a source link;
- mark external bulletin documents as internet-required;
- keep complaint aggregates and approved high-level guidance available through the existing static/offline experience;
- do not add full source documents to the main data blob.

## User-Facing Language

Heading:

> Common Customer Complaints

Subtitle:

> Topics most often reported in NHTSA safety complaints for this model year, paired with related manufacturer service guidance where available.

Permanent disclosure:

> Complaints are reports submitted to NHTSA, not verified defects, and counts are not failure rates. Manufacturer bulletins are service guidance, not recalls or guarantees. Applicability can depend on trim, engine, build date, or VIN. Check your VIN for recalls and have the symptom diagnosed before repairs.

Approved labels:

- Customer-reported concern
- Frequently reported to NHTSA
- Manufacturer-documented guidance
- Manufacturer says this symptom may be caused by...
- Manufacturer-documented service action
- Related safety recall may apply
- No matching manufacturer guidance found
- Limited NHTSA complaint data

Disallowed labels unless later supported by separate outcome evidence:

- Confirmed defect
- Common failure
- Known defect
- Usually fixes it
- Guaranteed fix
- NHTSA-recommended repair
- Free repair
- Reliability score derived from complaint totals

## Failure Behavior

- Source download failure: retain the previous verified snapshot; never publish a partial refresh.
- Source schema change: stop the ingestion/build with a clear error.
- Ambiguous applicability: keep the candidate internal and unpublished.
- Missing or unreadable source document: do not publish symptom, cause, or service action fields from it.
- Superseded bulletin: remove it from the current projection and replace it only after the new revision is reviewed.
- Missing bulletin match: continue showing the qualifying complaint topic and state that no matching manufacturer guidance was found.
- No complaint coverage: state that KYR does not currently have NHTSA complaint coverage for the selected vehicle; do not imply an absence of concerns.
- AI, retailer, forum, blog, or unsourced fallback: prohibited.

## Performance and Payload

- Aggregate complaint records at build time; perform no complaint clustering on the phone.
- Ship only compact topic counts, dates, safety flags, approved summaries, applicability labels, source IDs, and links.
- Keep raw narratives, staging rows, source files, and full bulletin text out of the public blob.
- Limit the initial view to three topics and six expanded topics.
- Evaluate a per-vehicle or Safety-section data shard if the approved bulletin projection materially increases the decoded static payload.

## Privacy and Safety

- Do not ship raw complaint narratives because they are unverified and may contain complainant-entered identifiers.
- Do not expose full VINs from complaint records or use them as public cache keys.
- Treat safety-critical symptoms as a route to recall lookup and qualified diagnosis, not a DIY repair recommendation.
- Do not reproduce complete professional repair procedures; summarize the high-level manufacturer action and link to the official document.
- Do not imply warranty coverage unless the exact manufacturer communication expressly provides it and the vehicle meets every eligibility condition.

## Verification and Tests

### Data tests

- Count distinct complaint/ODI numbers per topic.
- Enforce the three-report and 10% thresholds.
- Verify limited-data behavior below five total reports.
- Verify deterministic component normalization.
- Reject wrong year, make, model, engine, trim, build-range, and VIN applicability.
- Reject superseded communications.
- Reject communications without a readable authoritative source document.
- Verify recall remedies remain a separate provenance state.

### Negative fixtures

- Duplicate ODI rows do not inflate counts.
- Similar symptoms across different model years do not create a match.
- Unknown engine or VIN restriction does not publish a paired service action.
- AI-generated or null-source `vehicle_notes` never enter the projection.
- Raw complaint narratives never enter any shipped artifact.
- A TSB never renders with recall or warranty language unless the authoritative source supports it.

### UI tests

- Render at 375, 390, and 430 CSS pixels without horizontal overflow.
- Verify minimum touch-target sizes.
- Verify keyboard and screen-reader expansion state.
- Verify visible focus, contrast, and non-color status cues.
- Verify scroll position is preserved.
- Verify the initial three-topic limit and Show all behavior.
- Verify source links, external-link labeling, and VIN recall action.
- Verify useful empty, limited-data, unmatched-guidance, and offline states.

### Artifact verification

Extend `_verify_shipped.py` or its generated checks so a deployment fails when:

- complaint narrative text ships;
- a service action lacks `manufacturer_documented` provenance;
- required source IDs or URLs are absent;
- an ambiguous or superseded match ships;
- forbidden framing such as confirmed defect or guaranteed fix appears;
- the old unsourced `vehicle_notes` surface returns.

## Rollout

### Phase 1 — Complaint surface consolidation

- Replace the empty Known Issues tab with Common Customer Complaints.
- Reuse existing NHTSA complaint aggregates.
- Use normalized NHTSA component labels only; do not generate narrative-derived symptom summaries.
- Remove the duplicate Consumer Reports tab.
- Apply the approved thresholds, mobile layout, language, and tests.
- Show `No matching manufacturer guidance found` until Phase 2 data is approved.

### Phase 2 — Manufacturer guidance

- Build the official manufacturer-communication ingestion and review workflow.
- Backfill a small, high-confidence vehicle cohort first.
- Publish only human-approved, exact-applicable pairings.
- Measure payload growth and mobile performance before broader rollout.

### Phase 3 — First-party repair outcomes, separate future project

If KYR eventually has enough consented, structured service-log outcomes, design a separate evidence lane such as **Most frequently logged resolution by KYR owners**. It must have its own sample-size threshold, privacy model, anti-gaming controls, and specification. It is not part of this implementation.

## Official Source References

- NHTSA datasets and APIs: https://www.nhtsa.gov/nhtsa-datasets-and-apis
- NHTSA complaint data dictionary: https://static.nhtsa.gov/odi/ffdd/cmpl/CMPL.txt
- NHTSA manufacturer-communication data dictionary: https://static.nhtsa.gov/odi/ffdd/tsbs/TSBS.txt
- NHTSA complaints, recalls, and manufacturer communications: https://www.nhtsa.gov/resources-investigations-recalls
- NHTSA vehicle recall and complaint search: https://www.nhtsa.gov/recalls

## Acceptance Criteria

The feature is ready for implementation planning when:

- the product uses the approved mobile-first vertical layout;
- complaint counts are clearly attributed to NHTSA and never framed as failure rates;
- complaint, manufacturer, and recall evidence remain distinct;
- the initial release can ship truthful complaint aggregates without waiting for TSB repair guidance;
- repair guidance cannot publish without an exact authoritative source and human approval;
- the existing integrity verifier can be extended to catch regression across shipped artifacts;
- no unresolved placeholders, ambiguous evidence states, or unstated matching rules remain in this specification.
