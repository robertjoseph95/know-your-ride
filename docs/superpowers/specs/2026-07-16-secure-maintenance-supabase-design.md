# Secure Maintenance and Supabase Tier-2 Migration Design

**Status:** Approved by the user on 2026-07-16; implementation remains separately gated

**Scope:** Know Your Ride consumer identity, billing entitlement, garage ownership, maintenance history, costs, account lifecycle, and migration from Redis-backed durable storage

**Deployment:** This document authorizes design and implementation planning only. It does not authorize a schema change, data migration, environment-variable change, deployment, or provider cancellation.

## 1. Purpose

Know Your Ride will replace its email-keyed Redis account and maintenance storage with Supabase Auth and PostgreSQL. The migration is intended to make the existing maintenance workflow complete, secure, relational, and recoverable before receipts, sharing, fleet features, or offline writes are added.

This design preserves the verified-data product boundary:

- Tier 1 remains the static SQLite-to-artifact vehicle-reference core. It has no runtime Supabase dependency and remains DoD-severable.
- Tier 2 remains the commercial workflow layer hosted behind KYR APIs. Tier 2 expands from Vercel functions, Redis, and Stripe to Vercel functions, Supabase Auth/PostgreSQL, optional Redis caching/rate limits, and Stripe.
- Supabase never becomes the authority for oil, fluid, part, maintenance, recall, complaint, safety, MPG, or other public vehicle facts.
- All verified static reference information remains free. Pro sells workflow capacity and convenience.

The current Supabase project `know-your-ride` was verified active and healthy in US West with PostgreSQL 17, an empty public schema, and no security-advisor findings. Its existing $25/month Pro plan is approved for this program; paid branches, extra projects, Point-in-Time Recovery, or other added spend require separate approval. No production configuration currently points to it.

## 2. Current problem

The existing Tier-2 implementation has structural defects that cannot be safely repaired by adding fields to the current Redis arrays:

1. Accounts, sessions, subscriptions, garage vehicles, logs, and expenses are keyed primarily by email rather than an immutable user ID.
2. Email ownership is not verified before an account can claim email-linked entitlement state.
3. Browser sessions live in local storage for 30 days and cannot be reliably revoked as a complete set.
4. Account deletion leaves sessions and entitlement records behind.
5. Garage, service, expense, and quota mutations are non-atomic read-modify-write operations.
6. Service and expense APIs accept arbitrary vehicle identifiers without proving that the vehicle belongs to the authenticated garage.
7. Redis read failures can be interpreted as empty arrays and later overwrite real records.
8. Stripe entitlement logic is copied across endpoints and can disagree with the browser, Redis, or Stripe.
9. The service API already accepts cost, shop, and parts, but the main form does not collect them or update mileage, due state, history, and totals as one operation.
10. There is no automated identity, authorization, billing, migration, or maintenance-workflow test suite.

Supabase Auth and PostgreSQL are selected over a Redis V2 rebuild because KYR's roadmap is relational: users own garage vehicles; vehicles own service events, mileage readings, parts, expenses, receipts, and later share grants or organization assignments. PostgreSQL transactions, constraints, foreign keys, and audit records directly address the current failure modes while Supabase Auth removes the need for a solo developer to maintain password recovery and email verification infrastructure.

## 3. Approved product rules

The following decisions are binding.

### 3.1 Access and plans

- Anonymous visitors may browse public reference data and maintain a temporary local-only garage.
- Verified email is required before cloud synchronization, service-history writes, or Stripe Checkout.
- Free accounts may have one active garage vehicle.
- Pro accounts may have three active garage vehicles.
- Both plans may retain unlimited read-only archived vehicles.
- Free accounts receive three lifetime successful service-event creation credits per account, not per vehicle.
- Pro accounts may create unlimited service events while entitled.
- Deleting a service event never restores a consumed Free credit.
- Editing an existing service event consumes no additional credit.
- Service events created while Pro do not consume Free credits retroactively after downgrade.
- User-created records remain readable after downgrade.

### 3.2 Migration and grandfathering

- Every verified migrated account receives three fresh Free credits.
- Imported legacy service events consume no credits.
- Existing vehicles and records are preserved.
- Accounts already above their plan's active-vehicle limit are grandfathered at migration. They may retain those active vehicles but cannot add or restore another vehicle while above the limit.
- Archiving a grandfathered vehicle relinquishes that grandfathered active position. Restoring it must satisfy the then-current active limit.
- Migration grandfathering markers survive an upgrade. The first later Pro-to-Free transition clears every remaining marker and follows the downgrade rule below.
- Existing passwords and browser sessions are not migrated.
- Existing users reclaim data only after proving ownership of the normalized legacy email through Supabase Auth.

### 3.3 Archive, downgrade, and deletion

- Removing a vehicle archives it by default. An archive retains its complete history, is read-only, and can be restored only within the active limit.
- A separate permanent-delete path may be offered later; archive is the core release behavior.
- When Pro ends, no data is deleted. If more than one vehicle is active, all records remain readable but new writes pause until the user chooses one active vehicle; the others become archives.
- Account deletion immediately blocks normal access and revokes all sessions.
- Account deletion remains recoverable for 30 days.
- A deletion request schedules Stripe cancellation at the paid period's end. Recovery never silently restarts renewal.
- After 30 days, KYR application data and Supabase Auth identity are purged. Stripe retains only records it must retain for billing, accounting, fraud, and legal obligations.

## 4. System boundary

```text
Verified SQLite and build pipeline (Tier 1)
                |
                | stable public vehicle/configuration ID only
                v
Static browser application
                |
                | same-origin HTTPS + HttpOnly session + CSRF
                v
KYR Vercel API boundary
        |       |        |
        |       |        `-- Stripe Checkout, Portal, signed webhooks
        |       `----------- Upstash cache/rate limits during transition
        `------------------- Supabase Auth + private PostgreSQL schema
```

### 4.1 Tier 1

Tier 1 remains unchanged by this program. PostgreSQL records may reference a stable public vehicle or configuration identifier, but PostgreSQL cannot override, enrich, or publish vehicle facts. A garage record stores a small identity snapshot so history remains intelligible if the public catalog changes, while verified specifications continue to come from Tier 1.

The API deployment receives one generated, read-only allowlist of verified schedule keys keyed by the stable Tier-1 vehicle/configuration ID. Its generator consumes the same gated projection as the site, names its source/version, and is covered by the existing shipped-artifact verifier. When a submitted key belongs to the selected vehicle, the server stores the canonical label from this allowlist. A missing or mismatched key is never treated as verified: the request must either fail or be stored explicitly as a user-defined service with `schedule_key = null` and a bounded user label. PostgreSQL does not become a second schedule authority.

### 4.2 Browser boundary

The browser never receives a PostgreSQL connection string, Supabase secret/service credential, or direct write grant. Private reads and writes go through KYR's same-origin APIs. Public Supabase tables are not part of the first release.

The browser may receive only non-sensitive state required for the current session and interface. Authorization does not depend on browser plan flags, editable user metadata, query strings, or local storage.

### 4.3 API boundary

KYR's APIs own authentication enforcement, CSRF protection, body validation, authorization, rate limits, transactions, and response shaping. A single shared security component replaces duplicated endpoint-specific session, entitlement, and ownership logic. Vercel packaging must prove that this component is included identically in every relevant Python function; copying and manually editing security blocks is not acceptable.

The runtime PostgreSQL connection uses Supabase's serverless-appropriate pooled connection mode and a dedicated least-privilege database role. The identity-admin worker uses a different restricted database role. Neither runtime role receives arbitrary table access; each may execute only its separately reviewed operations in a non-exposed schema. Table ownership, owner-scoped user commands, and provider/migration/deletion operations use separate `NOLOGIN`, `NOINHERIT`, `NOBYPASSRLS` roles with table-specific privileges so a user command owner never inherits the operational queue surface.

The private schema is not treated as a substitute for row-level protection. Row Level Security is enabled and forced on every user-owned table as defense in depth, with default-deny behavior. `anon` and `authenticated` receive neither table grants nor user-data policies. Any policy or transaction-local identity context used by the dedicated API execution path must derive from the server-validated Supabase user ID, be set only for the current transaction, and be covered by cross-user negative tests. Direct table access must remain unavailable to browser-facing roles.

Database functions use `SECURITY INVOKER` wherever granular grants and forced RLS can support the operation. Where an atomic command genuinely requires `SECURITY DEFINER`, it must:

- live outside the exposed `public` schema;
- be owned by a dedicated `NOLOGIN`, `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOREPLICATION`, `NOBYPASSRLS` role rather than `postgres`, a service role, or a table owner that can evade forced RLS;
- revoke `EXECUTE` from `PUBLIC`, `anon`, and `authenticated`;
- grant execution only to the dedicated API role;
- use a locked, minimal `search_path` and fully qualified object names;
- receive only a server-validated user ID;
- repeat ownership, account-state, entitlement, and limit checks inside the transaction;
- avoid dynamic SQL;
- have negative authorization and concurrency tests.

Supabase secret/service credentials are project-wide and bypass RLS, so "narrow use" in code is not sufficient isolation. They live only in a separate minimal identity-admin worker deployment; ordinary KYR API functions do not receive those environment variables. The worker rejects every Supabase API origin except the exact approved KYR project origin before the credential can be used. It does not accept a caller-supplied user ID. It claims durable, server-created jobs from a restricted queue and is allowlisted to two Auth administration effects: revoke all sessions for a user and delete an Auth user after the purge gate. Signup, verification, login, refresh, recovery, JWT verification, and normal user-data operations do not use the secret/service credential. Deployment manifests and bundle/environment tests prove the credential is absent from the browser and ordinary API runtime.

### 4.4 Redis boundary

The current `wrenchapp-cache` Upstash resource is on the Free plan. It remains available during and after migration for bounded caching, throttling, AI budget counters, and the independent non-reversible purge-suppression manifest unless each use is deliberately replaced and restore-tested.

Redis stops being the durable source of truth for accounts, sessions, garages, maintenance history, expenses, credits, migration state, and billing entitlement. The purge-suppression manifest is the sole narrow durability exception: it contains keyed tombstones, not recoverable customer records, and exists to prevent deleted records from returning after a PostgreSQL restore. No application failure may silently fall back from PostgreSQL to stale Redis user data.

## 5. PostgreSQL model

All application tables live in a non-exposed `private` schema. UUID primary keys are generated server-side. Every user-owned child row carries an immutable `user_id` foreign key even when ownership is also derivable through another relation; this permits simple ownership checks and detects corrupt cross-user links with composite constraints. User-owned root rows reference `profiles(user_id)` with `ON DELETE CASCADE`, and dependent child rows use equally explicit cascading parent constraints so the final account purge is complete and testable.

### 5.1 `profiles`

One row per `auth.users.id`, enforced by a foreign key with `ON DELETE CASCADE`:

- `user_id` UUID primary key;
- `account_status`: `active` or `deletion_pending`;
- `deletion_requested_at` and `scheduled_purge_at`;
- `legacy_claimed_at` and migration revision where applicable;
- creation and update timestamps.

Email is read from Supabase Auth when required and is never a primary or authorization key.

### 5.2 `entitlements`

One current entitlement row per user:

- `user_id` UUID primary key;
- source: Stripe, explicit admin grant, or none;
- plan and normalized subscription status;
- Stripe customer, subscription, product, and price identifiers;
- current paid-period end and cancellation state;
- latest reconciled Stripe event ID, provider-state observation time, and update time. Event creation timestamps are diagnostic only and never determine ordering or access.

Only the signed webhook processor or an audited administrative operation may change paid entitlement. Browser state and `user_metadata` never authorize Pro access. Exact product and price allowlists are server configuration.

### 5.3 `garage_vehicles`

- server-generated garage vehicle UUID;
- immutable owner UUID;
- stable Tier-1 public vehicle/configuration identifier when known;
- year, make, model, engine, and trim identity snapshot;
- optional normalized VIN, private and excluded from logs and analytics;
- current mileage projection;
- `active` or `archived` state and archive timestamp;
- migration identifier and grandfathered-active marker;
- creation and update timestamps.

The active count is enforced inside a locking transaction. Public catalog IDs and VINs are attributes, never authorization identifiers.

### 5.4 `service_events`

- service-event UUID and owner UUID;
- owned garage-vehicle UUID;
- client request UUID with a unique owner-scoped constraint;
- canonical validated-request hash bound to that client request UUID;
- stable verified schedule/service key when the event corresponds to a known maintenance item;
- user-facing service label;
- performed date and mileage;
- authoritative total paid in integer cents;
- shop name and notes;
- creation, update, and soft-deletion timestamps;
- legacy source/checksum where migrated.

`total_cost_cents` is the only value included in running totals. Itemized part costs are supporting detail and are never added a second time.

### 5.5 `service_event_parts`

- part-row UUID, owner UUID, and service-event UUID;
- name, optional part number, quantity, and optional item cost in cents;
- creation and update timestamps.

Part rows cannot outlive or cross owners with their parent service event.

### 5.6 `mileage_readings`

- reading UUID, owner UUID, and garage-vehicle UUID;
- mileage, observation date/time, and source;
- optional unique service-event reference;
- creation timestamp.

A historical service may record mileage below the current vehicle projection but cannot reduce that projection. A higher reading updates the projection atomically.

### 5.7 `expense_events`

Existing non-service expenses are preserved separately:

- expense UUID, owner UUID, and garage-vehicle UUID;
- date, controlled category, integer amount in cents, and notes;
- creation, update, and soft-deletion timestamps;
- legacy source/checksum where migrated.

Running vehicle cost equals non-deleted authoritative service totals plus non-deleted expense amounts.

### 5.8 `credit_ledger`

Credits use an append-only ledger rather than a mutable counter:

- ledger UUID and owner UUID;
- signed delta;
- reason: initial grant, migration grant, service consumption, or audited correction;
- optional unique service-event reference;
- creation timestamp and actor.

One successful Free service creation inserts one `-1` entry in the same transaction as the service. A unique relation to the service event prevents duplicate consumption. Exactly one initial-or-migration grant may exist per account and it is always `+3`; invalid grant amounts and a second seed grant are database constraint failures. Soft deletion inserts no refund, and ordinary hard deletion cannot remove the service merely to cascade away its consumption entry. Balance is computed from the ledger and may be cached only as a rebuildable projection.

### 5.9 Operational tables

- `stripe_webhook_events` stores event ID, type, Stripe creation time, payload hash, processing status, attempt/lease metadata, a monotonically increasing fencing token, relevant Stripe object IDs, and timestamps. A database transition guard requires every first attempt or retry to enter `processing` with a newly incremented fence before it may fail or complete; terminal rows and envelope identity are immutable. Full payloads are not retained by default.
- `app_sessions` stores the Supabase `session_id`, immutable user ID, creation/last-seen/maximum-expiry timestamps, and revocation time. It contains no access or refresh token and is checked on every private request.
- `migration_records` stores source entity type, a keyed HMAC of any normalized source identity, target ID, checksum, migration revision, and import timestamp. An account manifest may exist unclaimed before email verification; the only allowed identity transition is one-way from unclaimed to one matching immutable user/target pair. It cannot be unclaimed or reassigned. One account identity maps to one claimed user per revision, one user cannot claim two legacy accounts in that revision, and imported child rows bind to the claimed account-manifest row. The HMAC key is a separately managed migration secret; plain or unsalted hashes of email addresses are not stored.
- `account_deletion_requests` stores the single authoritative user, keyed deletion identity, optional minimum unresolved provider identifier, request time, exact 30-day purge time, and completion/cancellation state for each deletion request. A bidirectional deferred database binding requires the profile and every open request to agree on user, request ID, request time, and deadline at commit. Recovery before the deadline atomically cancels and detaches the preserved request while returning the profile to active; only live or completed requests reserve the keyed identity, so the recovered account may request deletion again later. Identity and deadline fields are immutable; cancellation must occur before the deadline, completion cannot occur before it, and the user foreign key becomes null only through the ruled recovery transition or Auth/profile deletion action. A provider identifier may be attached when resolved and remains on a canceled request until its cancellation work reaches a safe terminal state, then is cleared.
- `account_deletion_jobs` is a durable child outbox with one uniquely keyed row per deletion request and provider operation: session revocation, Stripe cancellation, confirmation delivery, external purge-manifest write, Auth deletion, and application-cascade verification. Identity is never repeated on child jobs, so siblings cannot disagree about which account they operate on. Each row has its own state, not-before time, attempts, lease, fencing token, and last safe error code so one failed effect can retry without replaying successful siblings. Recovery terminalizes pending purge, Auth-deletion, and obsolete message jobs while preserving completed work and the Stripe cancellation-at-period-end job; only the parent request's keyed deletion identity and minimum unresolved provider identifier remain until that surviving provider effect is safely terminal. Provider side effects are never represented only by an in-memory request.
- `purge_tombstones` retains only keyed, non-reversible user/migration/Stripe identifiers and purge time for longer than the longest backup/export retention window. Before destructive deletion, the worker must also persist the same versioned tombstone in an independent append-only Upstash suppression manifest; deletion does not proceed if that external write fails. It exists solely to prevent a database restore or migration rerun from resurrecting a purged account and is covered by the privacy retention policy. If Upstash is ever retired, this manifest must first move to another independently retained store and pass a restore drill.
- Security/audit events store identifiers and outcomes necessary for incident review without tokens, passwords, full VINs, maintenance notes, or payment data.

## 6. Identity and session design

### 6.1 Signup and verification

- Supabase Auth owns password hashing, email verification, password recovery, token issuance, and immutable identity.
- Hosted email confirmation is required.
- Production uses a configured custom SMTP provider before public cutover.
- Signup, login, verification, resend, and recovery endpoints have IP- and account-aware throttles and enumeration-safe responses.
- Anonymous/local data is not synchronized until the email is verified.
- Checkout rejects unverified accounts.

### 6.2 Server-managed cookies

The KYR API exchanges Supabase Auth responses for `Secure`, `HttpOnly`, `SameSite=Lax`, host-only cookies using the `__Host-` prefix and `Path=/`. Auth tokens never persist in local storage.

- Access tokens expire after 15 minutes.
- Refresh sessions expire after seven days of inactivity or 30 days maximum.
- Refresh rotation occurs server-side.
- Every state-changing request requires an exact allowed `Origin` plus an unguessable CSRF token bound to the session.
- Private responses use `Cache-Control: private, no-store`.
- The `www` host redirects to the canonical apex before account cookies are issued.

Before production cutover, the project uses an asymmetric Supabase JWT signing key and completes the documented rotation/cache window. KYR never distributes or locally verifies with the legacy HS256 shared secret. If asymmetric keys are temporarily unavailable during development, token validity is checked against the Supabase Auth server with the publishable key; that fallback is not permission to expose a shared signing secret.

On successful login or refresh, the API verifies the returned access token before creating/updating the matching `app_sessions` row and rotating cookies. Refresh requests must match that active server-side session row; a refresh token by itself does not recreate a revoked KYR session.

Every private request verifies the access JWT server-side with a pinned, maintained JWT library and the project's current Supabase JWKS, cached no longer than current provider guidance and explicitly purgeable during rotation. Validation requires a valid signature under an explicit algorithm allowlist, exact project issuer, expected `authenticated` audience, valid `exp` and any present `nbf`, UUID `sub`, expected role, and a `session_id` registered to that same user in `app_sessions`. The verifier rejects `none`, algorithm confusion, an unexpected project, a merely decoded token, browser `getSession()` output as proof, and any session row that is missing, expired, or revoked.

Sensitive actions such as deletion require recent reauthentication and validate current account/session state rather than trusting an unexpired access token alone. Sign-out-all, password-security events, and deletion mark the relevant `app_sessions` rows revoked in the same local state transition, then enqueue Supabase refresh-session revocation in the isolated admin worker. Thus a surviving access JWT immediately fails KYR authorization even during an Auth provider outage. The 15-minute token lifetime remains an outer bound rather than the sole revocation control.

### 6.3 Authorization

- The API derives `user_id` from the validated session.
- Email, browser-submitted owner IDs, user metadata, and plan flags are ignored for authorization.
- Every private object command proves both user ownership and account state.
- Cross-user or nonexistent object requests return the same generic not-found response.
- Archived vehicles reject writes until restored within the limit.
- The service credential is never bundled into browser JavaScript, returned by an endpoint, or printed in logs.

## 7. Atomic maintenance command

The core user journey is one authenticated command, not a chain of unrelated browser writes.

### 7.1 Request

The browser generates a client request UUID and submits:

- owned garage vehicle ID;
- service/schedule key and label;
- performed date;
- mileage;
- total cost;
- shop;
- notes;
- optional structured parts.

The JSON body is capped at 64 KiB. Dates must be valid Gregorian dates and cannot be more than one day in the future. Mileage must be an integer from 0 through 9,999,999. Total and item costs must be integer cents from 0 through 100,000,000. User-defined service labels and shop text are capped at 200 characters, notes at 4,000 characters, part count at 50, and each part name/number at 200 characters. Unsupported fields, non-finite numbers, and invalid encodings are rejected.

After validation and canonical normalization, the server serializes a versioned, sorted-key UTF-8 JSON request object, hashes it with SHA-256, and binds that hash to the client request UUID. Reuse with the same hash returns the prior canonical result. Reuse with different content returns a 409 idempotency conflict and never substitutes the old response for the new request.

### 7.2 Transaction

One PostgreSQL transaction:

1. locks the always-present profile row as the per-user mutex and validates the active account;
2. validates the idempotency key and request hash, returning the prior canonical result only for an identical completed request;
3. locks and verifies the owned active garage vehicle;
4. locks and resolves entitlement, then computes the append-only credit-ledger balance while the profile mutex remains held;
5. rejects an exhausted Free balance without changing data;
6. inserts the service event and parts;
7. inserts a mileage reading and raises, but never lowers, current mileage;
8. consumes one Free credit only for a genuinely new Free event;
9. recomputes canonical history and cost state;
10. commits all changes together.

The response returns the saved event, current mileage, remaining credits, history summary, and cost total. The browser replaces its state with this canonical response rather than assuming success.

The owner-scoped idempotency uniqueness constraint resolves concurrent requests. Two identical in-flight requests serialize: one commits and the other returns that canonical event. A competing request that reuses the UUID with different content fails with 409. Because the profile row is locked before the balance is read, two concurrent attempts cannot both spend the final Free credit.

Maintenance due state remains a derived value based on Tier-1 verified schedules, canonical mileage, and service history. It is not stored as a mutable status that can drift. The first release recomputes it in the existing verified client projection; future reminders must consume the same verified schedule projection rather than create a separate interval source.

### 7.3 Edit and delete

- Edit revalidates ownership and inputs, updates the existing event atomically, and consumes no credit.
- Soft delete removes the event from visible history and totals but retains a tombstone and consumes no refund.
- Associated mileage history remains auditable. If editing or deleting the highest reading changes the correct current projection, the transaction recomputes it from remaining valid readings rather than decrementing blindly.
- Hard deletion occurs only during final account purge or a separately designed permanent-record deletion flow.

### 7.4 Error behavior

- Validation failure: 422 and no mutation.
- Unauthenticated or expired session: 401.
- Unverified or deletion-pending account: 403 with a safe account-state code.
- Missing/unowned object: generic 404.
- Plan, credit, active-limit, or idempotency conflict: 409 with a safe product-state code.
- Rate limit: 429 with bounded retry guidance.
- Database, Auth, or required dependency failure: 503; never an empty successful history.

No partial state is returned as success. Retryable requests preserve the client request UUID.

## 8. Billing and entitlement lifecycle

### 8.1 Checkout

- Checkout is an authenticated, CSRF-protected POST.
- The internal Supabase user ID is carried through Stripe's supported reference/metadata fields.
- A stored Stripe Customer is reused.
- Duplicate active subscriptions are rejected.
- Stripe idempotency protects Checkout retries.
- Checkout never retries anonymously.
- Dynamic payment methods remain Stripe-configured; KYR does not hardcode a card-only list.

### 8.2 Webhooks

- Verify the Stripe signature before parsing or processing.
- Persist a validated event envelope as `received` before applying an effect. A duplicate `completed` event returns success; a duplicate `received` or `failed` event is reclaimed after its processing lease expires and is never acknowledged merely because its ID already exists.
- Serialize reconciliation per Stripe subscription. Every lease acquisition increments a fencing token; after retrieving current authoritative subscription state, the entitlement transaction must still own the current token or abort without writing. This prevents an expired worker from resuming after its replacement and committing an older projection. The winning worker validates exact product and price allowlists, then updates entitlement and marks the inbox event `completed` in one PostgreSQL transaction.
- If retrieval or the local transaction fails, retain a retryable state and return non-2xx. A fail-after-receipt test must prove that a later Stripe retry completes the missing effect exactly once.
- Do not order entitlement with Stripe event `created` timestamps. Delayed and out-of-order events each trigger a fresh authoritative projection, so an old delivery cannot write an old snapshot over current state.
- A periodic reconciliation job compares every non-terminal paid subscription with Stripe so a missed webhook cannot become permanent drift.

Before creating or updating an entitlement, webhook and reconciliation paths check the profile and the internal plus independent purge manifests using keyed user/customer/subscription identifiers. An event for a purged identity is marked terminal `ignored_deleted`, never recreates a profile or entitlement, and may only advance the surviving cancellation job. An unknown event with no valid profile or approved Checkout binding also cannot create entitlement implicitly.

The exact status-to-access contract is default-deny:

| Stripe subscription state | KYR access |
|---|---|
| `trialing` | Pro only for an intentionally configured approved trial, through `trial_end` |
| `active` | Pro for the approved product/price; `cancel_at_period_end` keeps Pro only through the paid period end |
| `past_due` | Pro for at most seven calendar days from the first failed renewal payment while Stripe still reports `past_due`; then Free until recovery |
| `unpaid` | Free |
| `paused` | Free |
| `incomplete` | Free |
| `incomplete_expired` | Free |
| `canceled` | Free |
| missing, unknown, disallowed product/price, or retrieval failure | No new privileged write; preserve last readable user data and fail closed until reconciled |

The first-failure time and computed grace end are stored explicitly. A later successful payment and authoritative `active` state restore Pro. Browser flags, Checkout success redirects, invoices by themselves, and customer email never grant access.

### 8.3 Customer management

Stripe's hosted Customer Portal handles payment-method updates and cancellation. Cancellation keeps Pro through the paid period and then applies the Free rules.

On downgrade, all data remains readable. If active vehicles exceed one, writes pause until the user selects one vehicle to remain active; the others archive. Pro-created service events are not charged retroactively against the Free ledger.

### 8.4 Account deletion

Deletion requires recent authentication and begins with one local PostgreSQL transaction: lock the profile, mark it `deletion_pending`, set the 30-day purge time, and insert the durable outbox operations for Stripe cancellation-at-period-end, Supabase session revocation, confirmation delivery, and final purge. Once that transaction commits, every normal KYR API rejects the account even if Stripe, Auth administration, or email is temporarily unavailable.

The request then triggers best-effort immediate processing. PostgreSQL Cron also invokes narrow HMAC-authenticated triggers that carry no user ID. The ordinary job worker claims Stripe-cancellation and message jobs; the separately deployed identity-admin worker claims only Auth session-revocation and due Auth-deletion jobs through its restricted database role. Unfinished operations retry with bounded backoff, leases, `FOR UPDATE SKIP LOCKED`, and safe terminal states. Repeated Stripe cancellation, session revocation, and message attempts use provider-appropriate idempotency or deduplication. Provider failure cannot roll the local profile back to active, cannot permit normal access, and cannot be mistaken for completed cancellation. The cancellation intent survives recovery: recovering KYR access never silently resumes Stripe renewal.

Only the recovery endpoint may return a deletion-pending profile to `active` during the 30-day window. In one transaction it detaches the canceled request, terminalizes the pending purge/Auth-deletion jobs, and leaves any completed session revocation intact. It does not cancel the already-recorded Stripe cancellation intent: an unresolved Stripe job remains actionable and its parent retains the minimum provider identifier until that job is terminal. After the deadline, the purge runner removes active application data and the Auth identity. Once the Stripe operation finishes, the provider identifier is removed under the documented retention policy.

Recovery restores application access but does not silently reverse Stripe cancellation. The user explicitly reactivates billing if desired.

The final purge is driven by PostgreSQL-native Supabase Cron (`pg_cron`), not a browser request or Edge Function. Once daily, Cron triggers the identity-admin worker, which claims only eligible jobs. A reviewed private database operation rechecks `deletion_pending` and `scheduled_purge_at` and prepares the versioned tombstone. The worker must persist it to the independent append-only suppression manifest and the internal table before the operation authorizes deletion; only then may it delete the Auth user with the isolated Supabase admin credential, causing the declared application cascade. Auth "user not found" on retry is terminal success only after the worker proves the application rows are absent and both tombstones exist. Job ownership is restricted, database functions use a locked `search_path`, no trigger accepts a user ID, and nothing is executable by `PUBLIC`, `anon`, or `authenticated`. Session revocation is attempted immediately and retried from the outbox; Auth-user deletion is not the immediate access-control mechanism. Before production enablement, implementation must verify current Auth deletion, Cron/HTTP, job-claim, external-manifest, and cascade behavior on disposable accounts.

"Purged after 30 days" means removed from active KYR tables and Supabase Auth. Encrypted managed backups and the temporary cutover snapshot can retain inaccessible copies only until their fixed provider/documented destruction dates. Privacy copy must disclose that distinction. Before any database restore, Redis reimport, or migration rerun is allowed to serve traffic, the restore runbook first loads the independent append-only suppression manifest, reapplies all tombstones to the restored database, and proves the deleted identities and records remain absent. A tombstone stored only inside the database being restored is never sufficient. Cutover exports receive explicit destruction dates, owners, and deletion evidence rather than indefinite retention.

## 9. Migration and cutover

### 9.1 Preparation

- Build and test schema migrations outside production.
- Before implementation, inspect the current Supabase changelog and topic documentation for relevant Auth, session, connection, and migration changes.
- Use local Supabase for repeatable development where available. A paid Supabase branch or additional project requires separate cost approval.
- Preview deployments never receive production database credentials.
- Take an encrypted read-only Redis export and record key counts, entity counts, hashes, and export time.
- Take a separate Stripe entitlement reconciliation snapshot using customer/subscription IDs rather than trusting Redis flags.

### 9.2 Identity claim

Legacy passwords and tokens are rejected at cutover. Existing users enter their email and complete a Supabase verification/recovery link. Only then may the server compute the keyed HMAC of that verified normalized email and claim the matching migration record into the immutable user ID.

Legacy claim normalization is fixed to the behavior of the retiring system: trim leading/trailing whitespace and lowercase the complete address before HMAC. The export process first validates address shape and inventories normalization collisions. Any duplicate normalized legacy key, one-to-many Stripe match, or disagreement between Auth, legacy, and Stripe identities is quarantined for manual resolution; the system never auto-merges accounts or lets the claimant choose among colliding records. Database constraints permit each legacy identity to be claimed once and each imported entity to attach to one Supabase user.

Claim is atomic and idempotent. It cannot be repeated under another user. Redis subscription state alone never grants Pro; Stripe is queried or reconciled to the claimed user. `PRO_WHITELIST` and promo records are not automatically converted into permanent paid access. Any non-Stripe grant requires an explicit, audited, time-bounded administrative decision.

### 9.3 Data conversion

- Create server garage UUIDs and retain legacy identifiers only in migration metadata.
- Preserve every vehicle identity snapshot, mileage, service event, part, expense, and timestamp that can be parsed unambiguously.
- Quarantine malformed and orphan records with reasons; do not silently drop or attach them.
- Imported events receive legacy checksums and consume no credit.
- Insert the three-credit migration grant exactly once per claimed account.
- Preserve over-limit active vehicles with grandfathered markers.
- Derive current mileage and cost totals independently and compare them with migrated projections.

### 9.4 Cutover sequence

1. Prove schema, Auth, APIs, and migration using fixtures and internal accounts.
2. Dry-run the complete Redis export and produce a reconciliation report without changing production traffic.
3. Briefly disable legacy account and maintenance writes.
4. Take the final encrypted snapshot and reconcile it to the dry-run manifest.
5. Deploy forced legacy-session invalidation and Supabase claim/login.
6. Route new users and claimed users to PostgreSQL.
7. Run a small production canary before general access.
8. Verify per-user counts, checksums, entitlements, costs, credits, and sampled rendered histories.

Legacy Redis user-data namespaces remain frozen as recovery evidence for 30 days. Cache and rate-limit namespaces may continue operating. Once PostgreSQL accepts real writes, the application never resumes Redis user-data writes or silently reads stale Redis user data as a fallback.

If a cutover defect is found, disable affected writes, preserve PostgreSQL and Redis evidence, and repair or re-run idempotent imports. Do not create two writable sources of truth.

After 30 verified days, delete obsolete Redis user data and remove unused legacy environment variables. The free Upstash resource may remain for bounded cache/rate-limit uses.

## 10. Observability and privacy

- Correct the production environment name from `SENTRY_DNS` to the `SENTRY_DSN` consumed by code, then verify a test event before cutover.
- Structured logs use request, user, garage, event, and migration correlation IDs where necessary, but never include passwords, tokens, refresh cookies, full VINs, shop/maintenance notes, Stripe payment data, or secret values.
- Alerts cover repeated Auth failures, database failures, webhook failures, migration checksum mismatches, exhausted AI budgets, and deletion-purge failures.
- Analytics receive only aggregate workflow events and never VINs, garage contents, service history, notes, email, or Stripe session identifiers.
- Production uses Supabase Pro daily backups. A test restore is performed before cutover; Point-in-Time Recovery is a later separately priced decision.
- Custom SMTP is configured and tested for verification, recovery, deletion, and security messages.
- Legal and privacy copy is updated only after behavior matches this design and receives counsel review where appropriate.

## 11. Verification contract

All existing shipped-artifact checks remain unchanged because Tier 1 remains unchanged. New Tier-2 tests are additive.

### 11.1 Schema and database security

Tests prove:

- foreign keys, composite ownership constraints, check constraints, and unique idempotency constraints;
- no `anon`, `authenticated`, or `PUBLIC` table/function access beyond the intended Auth surface;
- dedicated API role cannot query arbitrary user tables;
- privileged operations reject missing, deleted, cross-user, or archived ownership;
- every definer function has the dedicated non-`BYPASSRLS` owner, remains constrained by forced RLS, and cannot change policy/table ownership or bypass user ownership in adversarial tests;
- ordinary API deployments cannot access the Supabase secret/service credential, and the isolated admin worker cannot execute any operation outside its two-item allowlist or outside a durable eligible job;
- Supabase security advisors are clean or every remaining notice has an explicit ruling;
- migration output is deterministic and repeatable.

### 11.2 Identity and authorization

Tests cover:

- unverified users cannot sync, write, or check out;
- legacy local-storage tokens and sessions fail after cutover;
- HttpOnly cookie flags, refresh rotation, idle expiry, maximum lifetime, and sign-out-all;
- asymmetric-key rotation/JWKS cache behavior; rejection of HS256/local shared-secret verification; valid and invalid signature/algorithm/issuer/audience/time/project/subject/role/session-ID combinations; and immediate rejection of a locally revoked `app_sessions` row;
- CSRF and foreign-origin rejection on every mutation;
- generic cross-user denial for vehicles, events, parts, expenses, and deletion;
- password recovery, deletion-pending restriction, 30-day recovery, and final purge;
- the scheduled purge selects only accounts past `scheduled_purge_at`, cascades all intended private rows, leaves younger/recovered accounts untouched, records failures without exposing identity, and succeeds idempotently on retry;
- every failure boundary among the local deletion transaction, Stripe cancellation, Auth session revocation, email delivery, recovery, and final purge, including worker lease expiry and retry;
- no browser bundle or endpoint contains a secret/service credential.

### 11.3 Product and concurrency rules

Tests cover:

- Free one-active and Pro three-active vehicle limits;
- unlimited archives and restore enforcement;
- migration grandfathering, relinquishment after archive, and its explicit precedence across upgrade/downgrade;
- three lifetime credits, concurrent final-credit attempts, no refund on delete, and no extra charge on edit/retry;
- concurrent vehicle, service, expense, webhook, and deletion requests;
- transaction rollback at every injected failure point.

### 11.4 Maintenance workflow

Tests cover:

- complete service creation and canonical response;
- duplicate retry returning one event and one consumption;
- concurrent identical requests returning one event, and idempotency-key reuse with different content returning 409;
- verified schedule-key/vehicle matching, generated-projection drift rejection, and user-defined fallback with no false verified key;
- historical lower mileage without current-mileage regression;
- higher mileage updating garage and due-state inputs;
- cost totals without part double-counting;
- edit/delete recomputation;
- database failure never returning an empty-success history;
- stale cross-vehicle browser responses never rendering under the newly selected vehicle.

### 11.5 Stripe

Tests cover:

- authenticated verified Checkout binding;
- exact product/price allowlists;
- every status/access row in the normative table, including the seven-day `past_due` boundary and unknown-state fail-closed behavior;
- signed, duplicate, malformed, delayed, and out-of-order webhook events;
- failure after inbox receipt, expired-lease reclaim, periodic reconciliation, and exactly-once local effect;
- fencing rejects a resumed expired worker, and post-purge events terminate without recreating profile or entitlement state;
- transient database failure returning retryable failure;
- trial, active, grace/retry, cancellation, period end, downgrade, and Customer Portal states;
- account deletion scheduling cancellation without silently restarting billing on recovery.

### 11.6 Migration

For every dry run and production run, verify:

- source and target entity counts;
- per-user and global checksums;
- no silent orphan loss;
- legacy email normalization collision, duplicate Stripe match, and one-to-one claim enforcement;
- exact one-time credit grants;
- imported events consume zero credits;
- Stripe-derived entitlements match approved subscriptions;
- sampled garage, mileage, history, part, expense, and total rendering;
- all legacy sessions are invalid.

Restore drills additionally prove that the independent append-only suppression manifest is available without the database, its purge tombstones are applied before traffic, deleted accounts cannot be resurrected from Supabase backups or Redis snapshots, and expired cutover exports have recorded destruction evidence.

### 11.7 Browser and accessibility

At minimum, test desktop and 390 x 844 mobile journeys:

- signup, verification, login, refresh, and recovery;
- local garage to verified cloud account;
- add vehicle, log service, and synchronized garage/due/history/cost updates;
- archive/restore, upgrade/downgrade, deletion/recovery;
- offline or dependency failure with honest non-destructive states;
- keyboard order, focus visibility, labels, announcements, contrast, and no horizontal overflow.

## 12. Delivery sequence

This is one architecture program delivered as independently gated blocks. Each block has its own implementation plan section, targeted commit, tests, preview, and explicit production approval.

### S1 - Foundation

- Add pinned dependencies and migration tooling.
- Create the private schema, roles, constraints, and automated database tests outside production.
- Add a shared API security/response component, the separate identity-admin worker skeleton, and prove deployment/environment isolation.
- Add no production traffic and migrate no users.

### S2 - Identity and sessions

- Implement Supabase signup, verification, JWT/session validation, `app_sessions`, login, refresh, recovery, CSRF, canonical host, and private/no-store responses behind a feature flag.
- Configure and test custom SMTP.
- Prove forced legacy-session rejection in preview/internal testing.

### S3 - Entitlement and billing

- Implement UID-bound Checkout, the normative status projection, webhook inbox/leases, exact-product entitlement, Customer Portal, downgrade rules, and periodic Stripe reconciliation.
- Remove email-based public subscription restoration from the new path.

### S4 - Garage and maintenance core

- Generate the gated Tier-1 schedule-key allowlist and implement garage ownership, archive/restore, mileage readings, credit ledger, content-bound idempotency, service/parts/expense transactions, complete service form, and canonical UI refresh.
- Keep receipts, PDF, sharing, email reminders, and offline writes out of scope.

### S5 - Migration and cutover

- Run dry migration, reconciliation, internal accounts, production canary, forced session rotation, and general cutover.
- Freeze legacy Redis user data for 30 days.

### S6 - Account lifecycle and cleanup

- Enable the durable deletion outbox, worker/Cron retries, recovery, purge tombstones, restore suppression, and final purge; remove obsolete email-keyed endpoints and environment variables; delete frozen legacy user data after the retention gate; correct privacy/product copy; and verify monitoring/backups.

No block authorizes the next automatically. Production migration and provider-data deletion require separate explicit approval.

## 13. Success criteria

The secure maintenance program is complete when:

- every cloud user has verified email and an immutable Supabase user ID;
- no session token is stored in browser local storage;
- every private read/write passes through KYR's authenticated API boundary;
- every garage, service, part, mileage, and expense operation proves ownership;
- service creation, mileage, credit consumption, and totals are one atomic command;
- Free 1/3 and Pro 3/unlimited rules are race-safe and machine-tested;
- Stripe is the only authority for paid subscription state;
- deletion revokes all sessions immediately and purges after the recoverable period;
- every migrated record and entitlement reconciles with a durable manifest;
- PostgreSQL is the sole durable user-data source and Redis cannot silently override it;
- Tier 1 remains byte- and behavior-independent of the Supabase runtime;
- all schema, API, migration, billing, browser, accessibility, and existing artifact tests pass locally and in CI;
- a user can complete the full verified account -> garage -> service -> due/history/cost journey on mobile without data loss or false state.

## 14. Non-goals

This design does not:

- move the verified vehicle-reference database into PostgreSQL;
- add direct browser database writes;
- replace Vercel hosting or Stripe billing;
- cancel or delete Upstash during initial cutover;
- add receipt/photo storage, PDF export, public sharing, reminders, fleet organizations, offline writes, telematics, or military workflows;
- rebuild AI guides, YouTube recommendations, or the part scanner;
- use Supabase Edge Functions in the first release;
- make legal conclusions about source redistribution or privacy-law compliance.

## 15. Authoritative implementation references

- [Supabase Auth architecture](https://supabase.com/docs/guides/auth/architecture)
- [Supabase JSON Web Tokens](https://supabase.com/docs/guides/auth/jwts)
- [Supabase Auth sessions](https://supabase.com/docs/guides/auth/sessions)
- [Supabase database connections](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Supabase API and Row Level Security](https://supabase.com/docs/guides/api/securing-your-api)
- [Supabase user management](https://supabase.com/docs/guides/auth/managing-user-data)
- [Supabase Cron](https://supabase.com/docs/guides/cron)
- [Supabase production checklist](https://supabase.com/docs/guides/deployment/going-into-prod)
- [Supabase backups](https://supabase.com/docs/guides/platform/backups)
- [Stripe subscription integration](https://docs.stripe.com/billing/subscriptions/design-an-integration)
- [Stripe subscription status object](https://docs.stripe.com/api/subscriptions/object)
- [Stripe Customer Portal](https://docs.stripe.com/customer-management/integrate-customer-portal)
- [Stripe webhook security](https://docs.stripe.com/webhooks)
- [Stripe restricted API keys](https://docs.stripe.com/keys/restricted-api-keys)
- [Upstash Vercel integration](https://upstash.com/docs/redis/howto/vercelintegration)
