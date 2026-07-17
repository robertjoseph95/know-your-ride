# Secure Maintenance and Supabase Migration Roadmap

**Status:** Draft implementation roadmap; execution and every remote gate await explicit approval

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to execute each approved block. Use `superpowers:test-driven-development` for implementation tasks and `superpowers:verification-before-completion` before any completion claim. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Know Your Ride's email-keyed Redis account and maintenance storage with a secure Supabase Auth/PostgreSQL Tier-2 workflow while preserving the static, verified Tier-1 vehicle-data product.

**Architecture:** Keep the SQLite-to-static-artifact reference core independent. Put all private user workflow behind same-origin Vercel APIs backed by Supabase Auth and a private PostgreSQL schema. Use immutable user and owned-garage UUIDs, atomic database commands, UID-bound Stripe entitlements, revocable server-managed sessions, and a separate identity-admin worker for the only credential that can administer Auth users.

**Tech Stack:** Static HTML/JavaScript and SQLite build artifacts, Vercel Python Functions on Python 3.12, psycopg 3, Supabase Auth/PostgreSQL 17, Stripe, transition-only Upstash Redis, GitHub Actions, pgTAP, and browser automation.

**Approved specification:** `docs/superpowers/specs/2026-07-16-secure-maintenance-supabase-design.md`

**Delivery rule:** This roadmap does not authorize schema mutation, environment-variable changes, a Vercel deployment, a data migration, a provider cancellation, a merge to `main`, or a production cutover. Each block has an explicit approval gate. Later implementation plans are written only after the previous block's interfaces and tests are proven.

## Global Constraints

- Tier 1 remains static-over-SQLite, government/manufacturer gated, and severable from every Tier-2 runtime.
- Private workflow data is UID-owned, same-origin API mediated, default-deny, transactionally consistent, and never browser-authoritative.
- Free/Pro limits, lifetime credits, grandfathering, archive behavior, 30-day deletion recovery, and the data/workflow paywall boundary remain exactly as approved below.
- Every block starts with a failing contract, keeps existing shipped-artifact checks additive, stages exact paths only, and pauses before unapproved remote or destructive action.

---

## 1. Binding product rules

- [ ] Anonymous users retain public reference access and a temporary local-only garage.
- [ ] Verified email is required for cloud sync, maintenance writes, and Checkout.
- [ ] Free accounts may keep **1 active vehicle** and receive **3 lifetime successful service-event creation credits per account**.
- [ ] Pro accounts may keep **3 active vehicles** and create unlimited service events while entitled.
- [ ] Both plans may retain unlimited read-only archived vehicles.
- [ ] Deleting a service event never restores a Free credit; editing consumes no new credit.
- [ ] Imported legacy events consume no credits; every verified migrated account receives three fresh credits.
- [ ] Existing over-limit garages are grandfathered, but an archived grandfathered slot cannot be restored above the current limit.
- [ ] A Pro-to-Free transition preserves data and pauses writes until the user chooses the one active vehicle.
- [ ] Account deletion revokes access immediately, remains recoverable for 30 days, and then purges active KYR data and the Auth identity.
- [ ] Tier 1 remains static-over-SQLite and has no Supabase runtime dependency.
- [ ] Verified static reference data remains free; Pro sells workflow capacity and convenience.

## 2. Provider disposition

No provider is cancelled during S1-S5.

| Provider | Roadmap role | Cancellation rule |
|---|---|---|
| Supabase Pro | Auth, private PostgreSQL, backups | Keep; it becomes the Tier-2 durable user-data system after cutover. |
| Vercel | Static app and Python API hosting | Keep; production continues to deploy from GitHub `main`. |
| Stripe | Payment and subscription authority | Keep; Redis and browser flags stop being entitlement authorities. |
| Upstash Redis | Transition evidence, bounded caches, rate limits, AI budgets, purge-suppression manifest | Keep through S6. Delete only obsolete user-data namespaces after the 30-day retention gate. Do not cancel the resource while retained uses remain. |

## 3. Repository boundaries

```text
Tier 1 (unchanged runtime boundary)
  wrench_vehicles.db -> files/04_rebuild_demo.py -> wrench_demo.html
  -> _deploy_sync_specs.py -> wrench_deploy/index.html + data.<hash>.js

Tier 2 main API project
  wrench_deploy/api/**/*.py
  wrench_deploy/kyr_api/*.py       # shared, non-route Python package
  Supabase pooled PostgreSQL connection using a least-privilege role

Tier 2 identity-admin worker
  identity_admin_worker/           # separate Vercel project and environment
  Supabase Auth secret credential  # never present in the main API project

Database source of truth
  supabase/migrations/*.sql
  supabase/tests/database/*.sql
```

The canonical frontend source remains `wrench_demo.html`; `wrench_deploy/index.html` is derived and must never be the only edited copy.

## 4. Block sequence

### S1 - Foundation

**Executable plan:** `docs/superpowers/plans/2026-07-16-s1-supabase-foundation.md`

Outputs:

- [ ] Python 3.12 is the single tested Vercel/CI Tier-2 runtime.
- [ ] Runtime dependencies are exact-pinned.
- [ ] Private PostgreSQL schema, roles, constraints, indexes, forced RLS, and pgTAP tests exist as replayable migrations.
- [ ] The main API role has no arbitrary table access.
- [ ] Shared `kyr_api` configuration, database, response, and request-security primitives are unit-tested.
- [ ] The main API rejects startup if an Auth administration credential is injected.
- [ ] The identity-admin worker exists as a disabled skeleton in a separate deploy root.
- [ ] CI adds Tier-2 unit and clean-database jobs without weakening the shipped-artifact verifier.
- [ ] Migration/export artifacts are both ignored and blocked by the staged-file guard.
- [ ] No production route consumes PostgreSQL; no user is migrated.

Exit evidence:

- Unit and compile tests pass on Python 3.12.
- A fresh PostgreSQL 17/Supabase local stack replays the migration and pgTAP suite in CI.
- Supabase lint/security advisors have no unexplained findings in the approved test target.
- A Vercel preview proves `kyr_api` is bundled; production remains untouched.
- Static and preview evidence proves the Auth administration credential cannot enter the main API deployment.

### S2 - Identity and sessions

Write the exact S2 plan only after S1 fixes the schema names, package imports, runtime, and preview packaging contract.

Outputs:

- [ ] Supabase signup, confirmation, resend, login, refresh, recovery, and logout are implemented behind a disabled feature flag.
- [ ] Production uses asymmetric JWT signing; the API validates algorithm, signature, issuer, audience, expiry, project, subject, role, and session ID against JWKS.
- [ ] Tokens live only in `Secure`, `HttpOnly`, `SameSite=Lax`, host-only `__Host-` cookies.
- [ ] Every private request checks the local `app_sessions` row so revocation is immediate.
- [ ] Mutation endpoints enforce canonical host, exact Origin, CSRF, body limits, rate limits, and no-store responses through the shared component.
- [ ] Custom SMTP is configured and tested before any public Auth cutover.
- [ ] Existing Redis sessions remain the production path until a separately approved cutover.

Required tests include unverified-user denial, enumeration-safe responses, refresh rotation, idle and maximum expiry, sign-out-all, cookie flags, CSRF, foreign Origin, JWKS rotation, locally revoked session denial, and legacy-session rejection under the new feature flag.

### S3 - Entitlement and billing

Write the exact S3 plan only after S2 produces the immutable UID/session API contract.

Outputs:

- [ ] Checkout is a verified-session POST bound to the immutable UID; anonymous fallback is removed from the new path.
- [ ] Stripe customer, subscription, product, and price identifiers are stored and exact-allowlisted.
- [ ] Signed webhooks enter a durable inbox with lease, fencing, retry, and idempotent local effects.
- [ ] A normative status table controls Pro access; unknown states fail closed.
- [ ] Customer Portal and periodic Stripe reconciliation exist.
- [ ] Public email-based subscription restoration and browser-authoritative Pro state are absent from the new path.
- [ ] Promo access is retired or converted into an audited, UID-bound, time-bounded grant.

Required tests include duplicate, delayed, malformed, and out-of-order events; retry after partial failure; stale-worker fencing; exact price/product rejection; grace-boundary behavior; and post-purge events that cannot recreate an account.

### S4 - Garage and maintenance core

Write the exact S4 plan only after S2 and S3 fix the identity and entitlement interfaces.

Outputs:

- [ ] Every cloud garage row has an owned UUID separate from the public Tier-1 vehicle ID.
- [ ] Archive/restore enforces Free 1 and Pro 3 active limits transactionally.
- [ ] Mileage uses an append-only reading ledger and cannot regress the current projection.
- [ ] Free credits use an append-only ledger and survive concurrent final-credit attempts.
- [ ] One service command atomically creates service, parts, mileage, cost, and credit effects and returns canonical state.
- [ ] Non-service expense create/edit/delete is owner-checked, content-idempotent, transaction-safe, and included in canonical totals.
- [ ] Request UUID plus canonical request hash provides content-bound idempotency.
- [ ] The complete form collects date, mileage, service, total paid, shop, parts, and notes.
- [ ] One successful response refreshes garage mileage, due state, history, and cost totals.
- [ ] A generated schedule-key allowlist comes from the same verified Tier-1 projection as the site.
- [ ] Client-only paywalls are removed from verified static maintenance/reference rows; workflow entitlements remain server-enforced.

S4 must not persist current `maintenance.id` values as durable keys; those IDs can change when verification scripts delete and reinsert rows. Before defining any vocabulary, S4 inventories every maintenance label/item in the complete shipped, gated Tier-1 projection and proposes a deterministic, versioned semantic mapping for explicit approval. The generator then derives the full allowlist from that approved mapping. Every unmatched verified item remains visible as verified reference information; a maintenance write may use it only after the mapping is expanded, otherwise the write is stored explicitly as user-defined with `schedule_key = null`. No item may be silently demoted, omitted, or guessed into a key.

Required browser proof includes a 390 x 844 journey and a delayed-response test proving a request for vehicle A cannot render under newly selected vehicle B.

Required transaction tests include concurrent and duplicate expense commands, cross-user denial, archive-state denial, soft-delete total recomputation, and rollback after injected failure.

### S5 - Migration and cutover

Write the exact S5 plan only after the new identity, billing, and maintenance paths are complete and internally proven.

Inputs to inventory independently:

```text
user:{email}
session:{token}
user_vehicles:{email}
user_mileage:{email}:{legacy_vehicle_id}
user_logs:{email}:{legacy_vehicle_id}
user_expenses:{email}:{legacy_vehicle_id}
sub:{email}
promo:* email/device grant keys
```

Outputs:

- [ ] Migration tooling defaults to dry-run and never logs email, tokens, VINs, notes, or raw records.
- [ ] Normalized legacy identities use a keyed HMAC, not plain email or an unsalted hash.
- [ ] Counts, checksums, collisions, malformed values, ambiguous Stripe matches, and orphan records are reconciled and quarantined.
- [ ] Legacy passwords and sessions are rejected; users reclaim data only after Supabase proves the normalized email.
- [ ] Imported events consume no credits and each claimed account receives one three-credit grant.
- [ ] A maintenance-mode switch freezes legacy writes before the final snapshot.
- [ ] PostgreSQL and Redis are never simultaneously writable user-data authorities.
- [ ] Canary and general cutover have explicit go/no-go and rollback procedures.

Before S5 may begin, select an encryption format and key custodian, prove a restore, and name the destruction date for every cutover export. No suitable encryption CLI is currently installed, so the S5 plan may not invent an export command before that ruling.

### S6 - Account lifecycle and cleanup

Write the exact S6 plan only after PostgreSQL is the sole durable user-data source and the deletion worker's interfaces can be tested against real internal accounts.

Outputs:

- [ ] Deletion immediately changes account status, revokes local sessions, and creates durable provider jobs.
- [ ] The isolated worker claims jobs; it never accepts a caller-supplied user ID.
- [ ] Stripe cancellation is scheduled at period end and recovery never silently restarts renewal.
- [ ] Recovery inside 30 days restores access, terminalizes destructive purge/Auth jobs, and keeps unresolved Stripe cancellation actionable with only the minimum provider identifier until it reaches a safe terminal state.
- [ ] Final purge deletes active KYR rows and the Auth identity, then retains only the approved irreversible tombstones.
- [ ] The independent Upstash suppression manifest is written before destructive purge and is tested in a restore drill.
- [ ] Obsolete Redis user namespaces, old email-keyed endpoints, local-storage tokens, and unused environment variables are removed after the retention gate.
- [ ] Privacy, Terms, Cookie, retention, and monitoring copy matches verified behavior.

## 5. Global stop conditions

Stop the active block and report evidence if any of these occurs:

- A proposed change gives Supabase authority over Tier-1 vehicle facts.
- A browser-facing role gains direct table access.
- `anon`, `authenticated`, or `PUBLIC` gains private-table or private-command access.
- A definer function is owned by `postgres`, a service role, a table owner that can evade policy, or a `BYPASSRLS` role.
- The Auth administration credential is found in the main Vercel project, ordinary API bundle, browser bundle, logs, or repository.
- Redis and PostgreSQL would both accept durable user-data writes.
- A database read failure is represented as an empty-success response.
- A schema, billing, or migration operation is not content-idempotent and concurrency-tested.
- Existing `_verify_shipped.py` checks are removed, weakened, or made non-additive.
- A command would stage broadly (`git add -A`, `git add .`, or `git commit -a`).
- A task requires an unapproved paid Supabase branch/project, production deployment, provider cancellation, or destructive data operation.

## 6. Verification ladder for every block

1. [ ] Write a failing unit, integration, database, verifier, or browser test for the rule being added.
2. [ ] Run the narrow failing test and record the expected failure.
3. [ ] Implement the minimum scoped change.
4. [ ] Run the narrow test until green.
5. [ ] Run the block suite.
6. [ ] Run `python _verify_shipped.py --ci` and `python _verify_shipped.py`; existing checks remain additive.
7. [ ] Stage only exact intended paths.
8. [ ] Run `git diff --cached --check`, inspect `git diff --cached --name-only`, and run `python _deploy_check.py`.
9. [ ] Commit one focused task and inspect `git show --stat --oneline HEAD`.
10. [ ] Pause before any remote schema mutation, environment change, preview deployment, push, merge, production deployment, or data deletion not already explicitly approved for that block.

## 7. Planning policy

S1 has a complete executable plan now because its interfaces can be grounded in the present repository and approved architecture. S2-S6 are intentionally just-in-time plans, not omitted work: each consumes concrete schemas, response contracts, and failure evidence produced by its predecessor. Writing all six exact plans before those interfaces exist would create speculative file paths and silently conflicting contracts.

After each block closes:

- [ ] Update this roadmap's evidence links and actual commit IDs.
- [ ] Record any approved deviation in the design specification before implementation continues.
- [ ] Write the next block's exact task plan against the proven repository state.
- [ ] Obtain explicit approval for the next block.

---

## Self-review

**Approved rule coverage:** Free 1/3, Pro 3/unlimited, archive, grandfathering, 30-day recovery, Supabase/Auth/PostgreSQL, Stripe authority, and Tier-1 independence are all mapped to a block and test gate.

**Current-code coverage:** The roadmap explicitly retires email-keyed authorization, browser/local-storage tokens, email subscription restoration, arbitrary public-vehicle ownership, non-atomic Redis arrays, mutable maintenance IDs, and stale cross-vehicle UI responses.

**Provider coverage:** Supabase, Vercel, Stripe, and Upstash each have an explicit keep/cancel rule; nothing is cancelled prematurely.

**Placeholder scan:** No implementation placeholder is treated as executable. Exact implementation details live in the gated block plans, beginning with S1.

**Type/name consistency:** `user_id` is the immutable Auth UUID; `garage_vehicle_id` is the owned UUID; `public_vehicle_id` is a Tier-1 reference only; `schedule_key` is generated semantic identity or null; money is integer cents.
