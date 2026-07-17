# S1 Secure Maintenance Supabase Foundation Implementation Plan

**Status:** Rulings reconciled 2026-07-17; no implementation or remote action is authorized by this document alone

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:using-git-worktrees` before Task 1, then `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:test-driven-development` for every code task and `superpowers:verification-before-completion` before claiming S1 complete. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a replayable, tested, least-privilege Supabase/PostgreSQL and shared-Python foundation for the secure maintenance program without routing production traffic, migrating users, or changing production secrets.

**Architecture:** Create all Tier-2 tables in a non-exposed `private` schema. Separate login-capable API and identity-worker roles can execute only their reviewed functions and cannot read or write tables directly. Separate `NOLOGIN` user-command and operational-command owners operate under forced RLS with table-specific privileges; user commands use a transaction-local server-validated user UUID. Shared Python code lives at `wrench_deploy/kyr_api/`, outside `api/`, and is explicitly bundled into Vercel functions. The Auth administration credential is forbidden in the main deployment and reserved for a disabled worker skeleton under a separate project root.

**Tech Stack:** Python 3.12, Vercel Python Functions (`BaseHTTPRequestHandler`), psycopg 3, PostgreSQL 17, Supabase CLI 2.109.1, pgTAP, Python `unittest`, GitHub Actions, Vercel CLI 56.2.0.

**Approved design:** `docs/superpowers/specs/2026-07-16-secure-maintenance-supabase-design.md`

**Roadmap:** `docs/superpowers/plans/2026-07-16-secure-maintenance-roadmap.md`

## Global Constraints

- Tier 1 remains static-over-SQLite and gains no Supabase runtime dependency.
- S1 changes no existing production route behavior, migrates no user, and writes no durable application row.
- Every remote action is separately PAUSE-gated; no `--prod`, `main` push, provider cancellation, or production environment mutation is authorized.
- Python is exactly 3.12 in Vercel and CI; runtime dependencies use exact `==` pins.
- All application tables live in unexposed schema `private`, have RLS enabled and forced, and grant no table privilege or policy to `PUBLIC`, `anon`, `authenticated`, or either runtime login.
- Browser/runtime roles execute only explicitly reviewed functions; Auth administration credentials exist only in the separate, disabled identity-worker deployment.
- S1 creates `kyr_api_runtime` and `kyr_identity_worker_runtime` with `LOGIN PASSWORD NULL`. S1 does not generate, transmit, install, rotate, or revoke either password. S2 owns that separately gated credential lifecycle and the first authenticated connectivity proof.
- Monetary values use integer cents; user/garage identities use UUIDs; request hashes and identity HMACs are 32-byte values.
- Git staging is path-targeted only. Never use `git add -A`, `git add .`, or `git commit -a`.

---

## S1 authorization boundary

This plan has four gates:

0. **Program/repository prerequisite:** do not begin Task 1 until roadmap Section 0 rows `IC-01` through `IC-05`, `OA-A2`, and `REPO-VIS-01` are `COMPLETE` with their required evidence linked. Re-run `gh repo view robertjoseph95/know-your-ride --json visibility --jq '.visibility'` and require `PRIVATE` immediately before execution. Changing repository visibility is a separate external action requiring explicit approval; this plan does not authorize it. If any prerequisite is unmet, report and stop without editing.
1. **Local implementation gate:** creating code, migrations, tests, and focused commits is allowed only after Gate 0 and a separate execution approval. No remote state changes.
2. **CI/preview gate:** pushing the dedicated S1 feature branch and creating Vercel preview deployments require explicit approval. Neither action may target `main` or production.
3. **Remote schema gate:** applying the tested migration to Supabase project `cajushswdwuthhakuevp` requires a second explicit approval. Until then, that paid project remains unchanged.

Repository privacy does not permit secrets in source. The schema, migrations, tests, CI, role names, and project reference are non-secret architecture; all credentials and customer/export data remain outside git.

S1 never:

- edits Vercel production environment variables;
- adds a Supabase Auth secret/service credential anywhere;
- creates or migrates a real user;
- changes an existing public API's behavior;
- writes durable user data to PostgreSQL;
- deletes or cancels Redis, Stripe, Vercel, or Supabase resources;
- merges or pushes to `main`;
- deploys with `--prod`.

At the start of an authorized S1 execution, use the required worktree skill to create an isolated worktree on `codex/s1-supabase-foundation` from the approved post-Option-A base. Before Task 1 changes any file, assert and capture that branch and baseline:

```powershell
$repoRoot = (git rev-parse --show-toplevel).Trim()
$targetBranch = 'codex/s1-supabase-foundation'
$branch = (git branch --show-current).Trim()
$head = (git rev-parse HEAD).Trim()
if (-not $repoRoot -or $branch -ne $targetBranch -or -not $head) {
  throw "S1 must run on named branch $targetBranch with a captured HEAD"
}
$storedBranch = (git config --local --get kyr.s1-branch | Out-String).Trim()
$storedBase = (git config --local --get kyr.s1-base | Out-String).Trim()
if ($storedBranch -or $storedBase) {
  if ($storedBranch -ne $targetBranch -or -not $storedBase) {
    throw 'existing S1 worktree has an incomplete or mismatched branch/base contract'
  }
  $base = $storedBase
} else {
  $base = $head
  git config --local kyr.s1-branch $branch
  if ($LASTEXITCODE -ne 0) { throw 'S1 branch was not persisted to local git config' }
  git config --local kyr.s1-base $base
  if ($LASTEXITCODE -ne 0) { throw 'S1 baseline was not persisted to local git config' }
}
git cat-file -e "$base`^{commit}"
if ($LASTEXITCODE -ne 0) { throw 'S1 baseline is not a commit' }
$mergeBase = (git merge-base $base HEAD).Trim()
if ($mergeBase -ne $base) { throw 'S1 baseline is not an ancestor of HEAD' }
[pscustomobject]@{ repo = $repoRoot; branch = $branch; base = $base }
```

Repo-local git config survives separate agent shells and cannot enter a commit. Reload and validate both `kyr.s1-branch` and `kyr.s1-base` wherever the plan compares or pushes S1 commits. Record both values in every S1 report. The base is the approved-plan execution start, not the earlier design commit or an Option-A branch.

## Current constraints

- Production contains a legacy `wrench_deploy/runtime.txt`, CI uses 3.12, and the workstation has only 3.14. Current Vercel Python documentation recognizes `.python-version`, `pyproject.toml`, or `Pipfile.lock`, not `runtime.txt`. S1 replaces the legacy file with root-level `.python-version` files pinned to 3.12; workstation runs are fast feedback only, and GitHub Actions/Vercel preview are authoritative.
- Docker is not installed locally. The clean-database proof therefore runs in GitHub Actions using Docker. Installing Docker Desktop is optional and not part of S1.
- At the 2026-07-17 reconciliation, the GitHub repository was public. Gate 0 blocks S1 implementation and any Tier-2 branch push until a separately approved visibility change has been completed and verified; this plan does not perform that change.
- The repository clone is not linked to the correct Vercel project. The old OneDrive link points to stale `project-sj4at`; never use it.
- The correct Vercel project is `know-your-ride`, whose configured Root Directory is `wrench_deploy`.
- The current Supabase project is active and empty/unconnected. It is not mutated before the remote schema gate.
- Supabase reports project `cajushswdwuthhakuevp` in `us-west-2` on PostgreSQL 17. Future runtime URLs must include a nonempty dedicated-role password and use the dashboard's exact shared transaction-pooler host, port `6543`, database `/postgres`, `sslmode=require`, and either the exact main username `kyr_api_runtime.cajushswdwuthhakuevp` or worker username `kyr_identity_worker_runtime.cajushswdwuthhakuevp`. S1's allowlist contains only the two current `us-west-2` Supavisor cluster hostnames; the environment selects the one shown by Connect, and any mismatch stops configuration instead of falling through to libpq credential sources. These URL shapes are S2's future runtime contract, not an S1 credential: S1 leaves both role passwords null and creates no `KYR_DATABASE_URL` or `KYR_IDENTITY_WORKER_DATABASE_URL` value.
- Replacing `wrench_deploy/runtime.txt` and changing the shared requirements rebuilds all 13 pre-S1 Python functions on the next deployment. Task 9 therefore cold-starts every legacy function in one non-production Python 3.12 preview before S1 may close.

## Execution-tool preflight

Run this repository/provider-read-only preflight at the start of an authorized execution. The pinned `npx` invocation may populate the local npm cache but changes no project or provider state. Docker remains optional locally because the authoritative database replay runs in CI.

```powershell
foreach ($command in 'git', 'gh', 'node', 'npm', 'npx', 'python', 'vercel') {
  if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
    throw "$command is required for S1"
  }
}

$vercelVersion = (& vercel --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $vercelVersion -notmatch '(^|\s)56\.2\.0(\s|$)') {
  throw "Vercel CLI 56.2.0 is required; observed: $vercelVersion"
}
$supabaseVersion = (& npx --yes supabase@2.109.1 --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $supabaseVersion -notmatch '(^|\s)2\.109\.1(\s|$)') {
  throw "Supabase CLI 2.109.1 is required; observed: $supabaseVersion"
}

git --version
gh --version
node --version
npm --version
npx --version
python --version
[pscustomobject]@{ vercel = $vercelVersion; supabase = $supabaseVersion }
```

Expected: every command resolves, Vercel reports `56.2.0`, and the pinned Supabase CLI reports `2.109.1`. Authentication checks remain just-in-time in Task 9 before remote CI/preview actions.

---

### Task 1: Pin the Tier-2 runtime and establish the unit-test harness

**Files:**

- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/test_runtime_contract.py`
- Create: `wrench_deploy/.python-version`
- Delete: `wrench_deploy/runtime.txt`
- Modify: `wrench_deploy/api/requirements.txt`

**Interfaces:**

- Consumes: existing Vercel Python requirements and GitHub's Python 3.12 contract.
- Produces: `wrench_deploy/.python-version` = `3.12`, exact dependency pins, and importable `tests.unit` package used by Tasks 2-8.

- [ ] **Step 1: Write the failing runtime/dependency contract.**

Create `tests/unit/test_runtime_contract.py`:

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PYTHON_VERSION = ROOT / "wrench_deploy" / ".python-version"
LEGACY_RUNTIME = ROOT / "wrench_deploy" / "runtime.txt"
REQUIREMENTS = ROOT / "wrench_deploy" / "api" / "requirements.txt"


class RuntimeContractTests(unittest.TestCase):
    def test_vercel_runtime_matches_ci(self):
        self.assertEqual(PYTHON_VERSION.read_text(encoding="utf-8").strip(), "3.12")
        self.assertFalse(LEGACY_RUNTIME.exists(), "unsupported runtime.txt must be removed")

    def test_every_runtime_dependency_is_exact_pinned(self):
        lines = [
            line.strip()
            for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        unpinned = [line for line in lines if not re.search(r"==[^=\s]+$", line)]
        self.assertEqual(unpinned, [], f"runtime dependencies must use == pins: {unpinned}")

    def test_postgres_driver_is_present(self):
        text = REQUIREMENTS.read_text(encoding="utf-8")
        self.assertIn("psycopg[binary]==3.3.4", text)


if __name__ == "__main__":
    unittest.main()
```

Create empty `tests/__init__.py` and `tests/unit/__init__.py`.

- [ ] **Step 2: Run the narrow test and confirm the expected failure.**

```powershell
python -m unittest tests.unit.test_runtime_contract -v
```

Expected: failures report missing `.python-version`, the unsupported legacy `runtime.txt`, the non-exact Sentry range, and missing psycopg.

- [ ] **Step 3: Make the minimum runtime changes.**

Create `wrench_deploy/.python-version` with:

```text
3.12
```

Delete `wrench_deploy/runtime.txt`; retaining it would falsely imply that Vercel still honors that selector.

Keep the existing requirements and replace the Sentry range/add psycopg so the non-comment lines are exactly:

```text
anthropic==0.105.2
requests==2.34.2
stripe==15.2.0
upstash-redis==1.7.0
sentry-sdk==2.66.0
psycopg[binary]==3.3.4
```

Do not add `supabase-py`; S1 uses Auth HTTP APIs later and direct pooled PostgreSQL, avoiding a second client abstraction.

- [ ] **Step 4: Run the narrow test.**

```powershell
python -m unittest tests.unit.test_runtime_contract -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Verify the complete requirements set resolves for Python 3.12 in CI later; do not claim workstation Python 3.14 as the production proof.**

- [ ] **Step 6: Commit only Task 1 files.**

```powershell
git add -- tests/__init__.py tests/unit/__init__.py tests/unit/test_runtime_contract.py wrench_deploy/.python-version wrench_deploy/runtime.txt wrench_deploy/api/requirements.txt
git diff --cached --check
git diff --cached --name-only
python _deploy_check.py
git commit -m "test(tier2): pin Python and database runtime"
git show --stat --oneline HEAD
```

---

### Task 2: Block private migration exports before migration tooling exists

**Files:**

- Create: `tests/unit/test_deploy_guard_private_exports.py`
- Modify: `.gitignore`
- Modify: `_deploy_check.py`

**Interfaces:**

- Consumes: the staged-file list already parsed by `_deploy_check.main()`.
- Produces: `is_private_export(path: str) -> bool`, ignored `.venv-tier2/` and private-export patterns, and a commit guard consumed by every later task.

- [ ] **Step 1: Write failing helper-level tests.**

Create `tests/unit/test_deploy_guard_private_exports.py`:

```python
import unittest

import _deploy_check


class PrivateExportGuardTests(unittest.TestCase):
    def test_blocks_known_private_export_paths(self):
        blocked = (
            "migration_exports/redis-users.json",
            "legacy_exports/final-snapshot.enc",
            "scripts/migration/output/reconciliation.private.json",
            "dump.rdb",
            "2026-07-16.redis-export.json",
            "claim.migration-private.csv",
        )
        for path in blocked:
            with self.subTest(path=path):
                self.assertTrue(_deploy_check.is_private_export(path))

    def test_allows_replayable_migration_source(self):
        allowed = (
            "supabase/migrations/20260716000000_tier2_foundation.sql",
            "supabase/tests/database/001_foundation_security.test.sql",
            "scripts/migration/export_redis_v1.py",
        )
        for path in allowed:
            with self.subTest(path=path):
                self.assertFalse(_deploy_check.is_private_export(path))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and confirm failure because `is_private_export` does not exist.**

```powershell
python -m unittest tests.unit.test_deploy_guard_private_exports -v
```

Expected: import/attribute failure.

- [ ] **Step 3: Add the reusable guard.**

Immediately after `BLOB_GLOB` in `_deploy_check.py`, add:

```python
PRIVATE_EXPORT_GLOBS = (
    "migration_exports/**",
    "legacy_exports/**",
    "scripts/migration/output/**",
    "*.rdb",
    "*.redis-export*",
    "*.migration-private.*",
)


def is_private_export(path):
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in PRIVATE_EXPORT_GLOBS)
```

In `main()`, before the PDF/DOCX check inside `for code, path in live:`, add:

```python
        if is_private_export(path):
            fails.append("private migration/export artifact staged (%s): %s" % (code, path))
            continue
```

- [ ] **Step 4: Append ignore rules and explicit safe examples.**

Append to `.gitignore`:

```gitignore

# Tier-2 migration exports/reconciliation outputs (customer data; NEVER commit)
migration_exports/
legacy_exports/
scripts/migration/output/
.venv-tier2/
*.rdb
*.redis-export*
*.migration-private.*

# Environment examples contain names only and are intentionally tracked.
!.env.example
!**/.env.example
```

- [ ] **Step 5: Run tests and the existing deploy guard.**

```powershell
python -m unittest tests.unit.test_deploy_guard_private_exports -v
python _deploy_check.py
```

Expected: tests pass; guard passes with no staged violations.

- [ ] **Step 6: Commit only Task 2 files.**

```powershell
git add -- .gitignore _deploy_check.py tests/unit/test_deploy_guard_private_exports.py
git diff --cached --check
git diff --cached --name-only
python _deploy_check.py
git commit -m "security(migration): block private export artifacts"
git show --stat --oneline HEAD
```

---

### Task 3: Create the replayable private PostgreSQL foundation

**Database TDD execution order:** follow this single linear sequence even though the reference bodies are grouped by artifact: Task 3 Steps 1-2 (empty CLI stubs) -> Task 4 Steps 1-3 (all contracts plus a guaranteed failing empty-migration source test) -> Task 3 Steps 2a-5 (configuration and migration implementation) -> Task 4 Steps 4-5 (GREEN and focused commit). Do not implement any migration SQL before the source-contract RED is recorded.

**Files:**

- Create via CLI: `supabase/config.toml`
- Create via CLI: the timestamped path printed by `supabase migration new tier2_foundation` (filename ends `_tier2_foundation.sql`)

**Interfaces:**

- Consumes: Task 4's pgTAP/config contracts through the declared interleaved TDD order.
- Produces: five fixed database roles, schema `private`, 15 foundation tables, exact ACL/RLS contracts, `private.current_user_id() -> uuid`, and `private.foundation_health() -> jsonb`.

- [ ] **Step 1: Inspect the pinned CLI before using it.**

```powershell
npx --yes supabase@2.109.1 --version
npx --yes supabase@2.109.1 init --help
npx --yes supabase@2.109.1 migration new --help
```

Expected version: `2.109.1`. Stop if the commands or flags differ from the plan.

- [ ] **Step 2: Initialize local Supabase source without linking or touching the remote project.**

```powershell
npx --yes supabase@2.109.1 init
npx --yes supabase@2.109.1 migration new tier2_foundation
Get-ChildItem supabase/migrations/*_tier2_foundation.sql | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
git status --short -- supabase
```

Expected: a new timestamped migration path. Do not rename it or invent a timestamp. Inspect any CLI-generated `supabase/.gitignore`; keep it only if every rule is appropriate, and account for it explicitly in Task 4's targeted stage set.

- [ ] **Step 2a: Pin the clean-replay database major and keep `private` out of the generated API schema list.**

In the CLI-generated `supabase/config.toml`, ensure these existing keys have these values; do not duplicate their sections:

```toml
[api]
schemas = ["public", "graphql_public"]

[db]
major_version = 17
```

The `private` schema must never appear in `api.schemas` or `api.extra_search_path`.

- [ ] **Step 3: Only after Task 4's contracts exist and their RED state is recorded, complete Step 2a and put this complete SQL into the CLI-created migration.**

```sql
-- KYR Tier-2 foundation. Tier 1 vehicle facts never enter this schema.

-- S1 intentionally leaves both runtime logins unable to password-authenticate.
-- S2 separately provisions, installs, verifies, rotates, and revokes their
-- generated credentials; no role password belongs in migration history.

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'kyr_table_owner') then
    create role kyr_table_owner nologin nosuperuser nocreatedb nocreaterole
      noinherit noreplication nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'kyr_user_function_owner') then
    create role kyr_user_function_owner nologin nosuperuser nocreatedb nocreaterole
      noinherit noreplication nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'kyr_ops_function_owner') then
    create role kyr_ops_function_owner nologin nosuperuser nocreatedb nocreaterole
      noinherit noreplication nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'kyr_api_runtime') then
    create role kyr_api_runtime login password null nosuperuser nocreatedb nocreaterole
      noinherit noreplication nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'kyr_identity_worker_runtime') then
    create role kyr_identity_worker_runtime login password null nosuperuser nocreatedb nocreaterole
      noinherit noreplication nobypassrls;
  end if;
end
$$;

alter role kyr_table_owner with
  nologin nosuperuser nocreatedb nocreaterole noinherit noreplication nobypassrls;
alter role kyr_user_function_owner with
  nologin nosuperuser nocreatedb nocreaterole noinherit noreplication nobypassrls;
alter role kyr_ops_function_owner with
  nologin nosuperuser nocreatedb nocreaterole noinherit noreplication nobypassrls;
alter role kyr_api_runtime with
  login password null nosuperuser nocreatedb nocreaterole noinherit noreplication nobypassrls;
alter role kyr_identity_worker_runtime with
  login password null nosuperuser nocreatedb nocreaterole noinherit noreplication nobypassrls;

-- Hosted Supabase runs migrations as managed postgres (CREATEROLE/BYPASSRLS,
-- not superuser). SET membership is required before ownership transfers and
-- is deliberately retained for future reviewed migrations and pgTAP.
grant kyr_table_owner to postgres with admin true, set true, inherit false;
grant kyr_user_function_owner to postgres with admin true, set true, inherit false;
grant kyr_ops_function_owner to postgres with admin true, set true, inherit false;
grant kyr_api_runtime to postgres with admin true, set true, inherit false;
grant kyr_identity_worker_runtime to postgres with admin true, set true, inherit false;

alter role kyr_api_runtime set statement_timeout = '15s';
alter role kyr_api_runtime set lock_timeout = '3s';
alter role kyr_api_runtime set idle_in_transaction_session_timeout = '10s';
alter role kyr_identity_worker_runtime set statement_timeout = '30s';
alter role kyr_identity_worker_runtime set lock_timeout = '3s';
alter role kyr_identity_worker_runtime set idle_in_transaction_session_timeout = '10s';

create schema if not exists private authorization postgres;
revoke all on schema private from public, anon, authenticated;
grant usage on schema private
  to kyr_table_owner, kyr_user_function_owner, kyr_ops_function_owner,
     kyr_api_runtime, kyr_identity_worker_runtime;
grant create on schema private
  to kyr_table_owner, kyr_user_function_owner, kyr_ops_function_owner;
do $$
begin
  execute format('grant create on database %I to kyr_table_owner', current_database());
end
$$;

create table private.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  account_status text not null default 'active'
    check (account_status in ('active', 'deletion_pending')),
  deletion_request_id uuid,
  deletion_requested_at timestamptz,
  scheduled_purge_at timestamptz,
  legacy_claimed_at timestamptz,
  migration_revision text check (migration_revision is null or char_length(migration_revision) <= 80),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint profiles_deletion_state_ck check (
    (account_status = 'active' and deletion_request_id is null
      and deletion_requested_at is null and scheduled_purge_at is null)
    or
    (account_status = 'deletion_pending' and deletion_request_id is not null
      and deletion_requested_at is not null
      and scheduled_purge_at is not null and scheduled_purge_at > deletion_requested_at)
  ),
  constraint profiles_deletion_identity_uq unique (
    user_id, deletion_request_id, deletion_requested_at, scheduled_purge_at
  )
);

create table private.entitlements (
  user_id uuid primary key references private.profiles(user_id) on delete cascade,
  source text not null default 'none' check (source in ('none', 'stripe', 'admin')),
  plan text not null default 'free' check (plan in ('free', 'pro')),
  subscription_status text not null default 'none' check (
    subscription_status in (
      'none', 'trialing', 'active', 'past_due', 'unpaid', 'paused', 'canceled',
      'incomplete', 'incomplete_expired', 'admin_grant'
    )
  ),
  stripe_customer_id text check (stripe_customer_id is null or char_length(stripe_customer_id) between 4 and 255),
  stripe_subscription_id text check (stripe_subscription_id is null or char_length(stripe_subscription_id) between 4 and 255),
  stripe_product_id text check (stripe_product_id is null or char_length(stripe_product_id) between 4 and 255),
  stripe_price_id text check (stripe_price_id is null or char_length(stripe_price_id) between 4 and 255),
  current_period_end timestamptz,
  trial_end timestamptz,
  past_due_started_at timestamptz,
  grace_ends_at timestamptz,
  admin_grant_expires_at timestamptz,
  cancel_at_period_end boolean not null default false,
  latest_stripe_event_id text check (latest_stripe_event_id is null or char_length(latest_stripe_event_id) <= 255),
  provider_observed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint entitlements_source_shape_ck check (
    (
      source = 'none' and plan = 'free' and subscription_status = 'none'
      and stripe_customer_id is null and stripe_subscription_id is null
      and stripe_product_id is null and stripe_price_id is null
      and current_period_end is null and cancel_at_period_end = false
      and latest_stripe_event_id is null and provider_observed_at is null
      and trial_end is null and past_due_started_at is null and grace_ends_at is null
      and admin_grant_expires_at is null
    )
    or
    (
      source = 'admin' and plan = 'pro' and subscription_status = 'admin_grant'
      and stripe_customer_id is null and stripe_subscription_id is null
      and stripe_product_id is null and stripe_price_id is null
      and current_period_end is null and cancel_at_period_end = false
      and latest_stripe_event_id is null and provider_observed_at is null
      and trial_end is null and past_due_started_at is null and grace_ends_at is null
      and admin_grant_expires_at is not null and admin_grant_expires_at > created_at
    )
    or
    (
      source = 'stripe'
      and subscription_status in (
        'trialing', 'active', 'past_due', 'unpaid', 'paused', 'canceled',
        'incomplete', 'incomplete_expired'
      )
      and stripe_customer_id is not null and stripe_subscription_id is not null
      and stripe_product_id is not null and stripe_price_id is not null
      and provider_observed_at is not null
      and admin_grant_expires_at is null
      and (
        plan = 'free'
        or subscription_status in ('trialing', 'active', 'past_due')
      )
      and (
        subscription_status not in (
          'unpaid', 'paused', 'canceled', 'incomplete', 'incomplete_expired'
        )
        or plan = 'free'
      )
      and (
        (subscription_status = 'trialing' and trial_end is not null
          and past_due_started_at is null and grace_ends_at is null)
        or
        (subscription_status = 'past_due' and trial_end is null
          and past_due_started_at is not null
          and grace_ends_at = past_due_started_at + interval '7 days')
        or
        (subscription_status not in ('trialing', 'past_due') and trial_end is null
          and past_due_started_at is null and grace_ends_at is null)
      )
      and (plan = 'free' or current_period_end is not null)
    )
  ),
  constraint entitlements_cancel_shape_ck check (
    not cancel_at_period_end
    or (
      source = 'stripe'
      and subscription_status in ('trialing', 'active', 'past_due')
      and current_period_end is not null
    )
  )
);

create table private.garage_vehicles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references private.profiles(user_id) on delete cascade,
  public_vehicle_id bigint check (public_vehicle_id is null or public_vehicle_id > 0),
  year smallint not null check (year between 1886 and 2200),
  make text not null check (char_length(btrim(make)) between 1 and 80),
  model text not null check (char_length(btrim(model)) between 1 and 120),
  engine text check (engine is null or char_length(engine) <= 160),
  trim text check (trim is null or char_length(trim) <= 120),
  vin text check (vin is null or vin ~ '^[A-HJ-NPR-Z0-9]{17}$'),
  current_mileage integer check (current_mileage is null or current_mileage between 0 and 9999999),
  state text not null default 'active' check (state in ('active', 'archived')),
  archived_at timestamptz,
  migration_id uuid,
  grandfathered_active boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint garage_state_ck check (
    (state = 'active' and archived_at is null)
    or (state = 'archived' and archived_at is not null and grandfathered_active = false)
  ),
  constraint garage_vehicles_owner_uq unique (user_id, id)
);

create table private.service_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references private.profiles(user_id) on delete cascade,
  garage_vehicle_id uuid not null,
  client_request_id uuid not null,
  request_hash bytea not null check (octet_length(request_hash) = 32),
  schedule_key text check (schedule_key is null or schedule_key ~ '^[a-z0-9][a-z0-9-]{0,63}$'),
  service_label text not null check (char_length(btrim(service_label)) between 1 and 200),
  performed_on date not null,
  mileage integer not null check (mileage between 0 and 9999999),
  total_cost_cents bigint not null default 0 check (total_cost_cents between 0 and 100000000),
  shop_name text check (shop_name is null or char_length(shop_name) <= 200),
  notes text check (notes is null or char_length(notes) <= 4000),
  deleted_at timestamptz,
  legacy_source text check (legacy_source is null or char_length(legacy_source) <= 80),
  legacy_checksum bytea check (legacy_checksum is null or octet_length(legacy_checksum) = 32),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint service_events_vehicle_fk foreign key (user_id, garage_vehicle_id)
    references private.garage_vehicles(user_id, id) on delete cascade,
  constraint service_events_request_uq unique (user_id, client_request_id),
  constraint service_events_owner_id_uq unique (user_id, id),
  constraint service_events_owner_vehicle_id_uq unique (user_id, id, garage_vehicle_id)
);

create table private.service_event_parts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references private.profiles(user_id) on delete cascade,
  service_event_id uuid not null,
  name text not null check (char_length(btrim(name)) between 1 and 200),
  part_number text check (part_number is null or char_length(part_number) <= 200),
  quantity numeric(10,3) not null default 1 check (quantity > 0 and quantity <= 10000),
  item_cost_cents bigint check (item_cost_cents is null or item_cost_cents between 0 and 100000000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint service_event_parts_event_fk foreign key (user_id, service_event_id)
    references private.service_events(user_id, id) on delete cascade
);

create table private.mileage_readings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references private.profiles(user_id) on delete cascade,
  garage_vehicle_id uuid not null,
  mileage integer not null check (mileage between 0 and 9999999),
  observed_at timestamptz not null,
  source text not null check (source in ('manual', 'service', 'migration', 'garage_import')),
  service_event_id uuid,
  created_at timestamptz not null default now(),
  constraint mileage_readings_vehicle_fk foreign key (user_id, garage_vehicle_id)
    references private.garage_vehicles(user_id, id) on delete cascade,
  constraint mileage_readings_service_fk foreign key (user_id, service_event_id, garage_vehicle_id)
    references private.service_events(user_id, id, garage_vehicle_id) on delete cascade,
  constraint mileage_readings_service_uq unique (service_event_id),
  constraint mileage_service_source_ck check (
    (source = 'service' and service_event_id is not null)
    or (source <> 'service' and service_event_id is null)
  )
);

create table private.expense_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references private.profiles(user_id) on delete cascade,
  garage_vehicle_id uuid not null,
  expense_on date not null,
  category text not null check (category in ('registration', 'insurance', 'fuel', 'other')),
  amount_cents bigint not null check (amount_cents between 1 and 100000000),
  notes text check (notes is null or char_length(notes) <= 2000),
  deleted_at timestamptz,
  legacy_source text check (legacy_source is null or char_length(legacy_source) <= 80),
  legacy_checksum bytea check (legacy_checksum is null or octet_length(legacy_checksum) = 32),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint expense_events_vehicle_fk foreign key (user_id, garage_vehicle_id)
    references private.garage_vehicles(user_id, id) on delete cascade
);

create table private.credit_ledger (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references private.profiles(user_id) on delete cascade,
  delta smallint not null check (delta between -100 and 100 and delta <> 0),
  reason text not null check (
    reason in ('initial_grant', 'migration_grant', 'service_consumption', 'audited_correction')
  ),
  service_event_id uuid,
  actor text not null check (char_length(btrim(actor)) between 1 and 120),
  created_at timestamptz not null default now(),
  constraint credit_ledger_service_fk foreign key (user_id, service_event_id)
    references private.service_events(user_id, id)
    on delete no action deferrable initially deferred,
  constraint credit_ledger_service_uq unique (service_event_id),
  constraint credit_reason_ck check (
    (reason = 'service_consumption' and delta = -1 and service_event_id is not null)
    or (reason in ('initial_grant', 'migration_grant') and delta = 3 and service_event_id is null)
    or (reason = 'audited_correction' and delta <> 0 and service_event_id is null)
  )
);

create table private.stripe_webhook_events (
  event_id text primary key check (char_length(event_id) between 4 and 255),
  event_type text not null check (char_length(event_type) between 3 and 255),
  stripe_created_at timestamptz not null,
  payload_hash bytea not null check (octet_length(payload_hash) = 32),
  processing_status text not null default 'received'
    check (processing_status in ('received', 'processing', 'failed', 'completed', 'terminal')),
  attempt_count integer not null default 0 check (attempt_count >= 0),
  lease_until timestamptz,
  fencing_token bigint not null default 0 check (fencing_token >= 0),
  stripe_customer_id text,
  stripe_subscription_id text,
  processed_at timestamptz,
  last_error_code text check (last_error_code is null or char_length(last_error_code) <= 120),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint stripe_webhook_events_state_ck check (
    (
      processing_status in ('received', 'failed')
      and lease_until is null and processed_at is null
    )
    or (
      processing_status = 'processing'
      and lease_until is not null and processed_at is null
    )
    or (
      processing_status in ('completed', 'terminal')
      and lease_until is null and processed_at is not null
    )
  )
);

create or replace function private.guard_stripe_webhook_event_update()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
begin
  if tg_op = 'INSERT' then
    if new.processing_status <> 'received'
      or new.attempt_count <> 0
      or new.fencing_token <> 0
      or new.lease_until is not null
      or new.processed_at is not null
      or new.last_error_code is not null
    then
      raise exception 'new Stripe webhook envelope must enter as unclaimed received state'
        using errcode = '23514';
    end if;
    return new;
  end if;

  if new.event_id is distinct from old.event_id
    or new.event_type is distinct from old.event_type
    or new.stripe_created_at is distinct from old.stripe_created_at
    or new.payload_hash is distinct from old.payload_hash
    or new.created_at is distinct from old.created_at
  then
    raise exception 'Stripe webhook envelope identity is immutable' using errcode = '23514';
  end if;

  if old.processing_status in ('completed', 'terminal') then
    raise exception 'terminal Stripe webhook state is immutable' using errcode = '23514';
  end if;

  if old.processing_status in ('received', 'failed') then
    if new.processing_status <> 'processing'
      or new.fencing_token <> old.fencing_token + 1
      or new.attempt_count <> old.attempt_count + 1
      or new.lease_until <= statement_timestamp()
    then
      raise exception 'Stripe webhook retry must acquire a new fenced processing lease'
        using errcode = '23514';
    end if;
    return new;
  end if;

  if old.processing_status = 'processing' then
    if new.processing_status = 'processing' then
      if not (
        (
          new.fencing_token = old.fencing_token
          and new.attempt_count = old.attempt_count
          and old.lease_until > statement_timestamp()
          and new.lease_until > statement_timestamp()
        )
        or (
          old.lease_until <= statement_timestamp()
          and new.fencing_token = old.fencing_token + 1
          and new.attempt_count = old.attempt_count + 1
          and new.lease_until > statement_timestamp()
        )
      ) then
        raise exception 'Stripe webhook lease renewal or reclaim has invalid fencing state'
          using errcode = '23514';
      end if;
      return new;
    end if;

    if new.processing_status in ('failed', 'completed', 'terminal')
      and new.fencing_token = old.fencing_token
      and new.attempt_count = old.attempt_count
      and old.lease_until > statement_timestamp()
    then
      return new;
    end if;
  end if;

  raise exception 'illegal Stripe webhook state transition' using errcode = '23514';
end
$$;
revoke all on function private.guard_stripe_webhook_event_update()
  from public, anon, authenticated, kyr_api_runtime, kyr_identity_worker_runtime;
create trigger stripe_webhook_events_state_guard
before insert or update on private.stripe_webhook_events
for each row execute function private.guard_stripe_webhook_event_update();

create table private.app_sessions (
  session_id uuid primary key,
  user_id uuid not null references private.profiles(user_id) on delete cascade,
  created_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  idle_expires_at timestamptz not null,
  maximum_expires_at timestamptz not null,
  revoked_at timestamptz,
  constraint app_sessions_expiry_ck check (
    idle_expires_at > created_at and maximum_expires_at >= idle_expires_at
      and (revoked_at is null or revoked_at >= created_at)
  )
);

create table private.migration_records (
  id uuid primary key default gen_random_uuid(),
  source_entity_type text not null check (
    source_entity_type in ('account', 'garage_vehicle', 'mileage', 'service_event', 'part', 'expense', 'entitlement')
  ),
  source_identity_hmac bytea not null check (octet_length(source_identity_hmac) = 32),
  source_key_hmac bytea not null check (octet_length(source_key_hmac) = 32),
  claimed_user_id uuid references private.profiles(user_id) on delete cascade,
  account_claim_id uuid,
  account_claim_type text generated always as ('account') stored,
  target_id uuid,
  checksum bytea not null check (octet_length(checksum) = 32),
  migration_revision text not null check (char_length(migration_revision) between 1 and 80),
  imported_at timestamptz not null default now(),
  constraint migration_records_source_uq
    unique (migration_revision, source_entity_type, source_key_hmac),
  constraint migration_records_claim_reference_uq
    unique (id, migration_revision, source_identity_hmac, claimed_user_id, source_entity_type),
  constraint migration_records_account_shape_ck check (
    (
      source_entity_type = 'account' and account_claim_id is null
      and (
        (claimed_user_id is null and target_id is null)
        or (
          claimed_user_id is not null and target_id is not null
          and target_id = claimed_user_id
        )
      )
    )
    or (
      source_entity_type <> 'account' and account_claim_id is not null
      and claimed_user_id is not null and target_id is not null
    )
  ),
  constraint migration_records_account_claim_fk foreign key (
    account_claim_id, migration_revision, source_identity_hmac,
    claimed_user_id, account_claim_type
  ) references private.migration_records (
    id, migration_revision, source_identity_hmac,
    claimed_user_id, source_entity_type
  ) on delete cascade
);

create table private.account_deletion_requests (
  deletion_request_id uuid primary key,
  user_id uuid references private.profiles(user_id) on delete set null,
  deletion_identity_hmac bytea not null check (octet_length(deletion_identity_hmac) = 32),
  stripe_customer_id text check (stripe_customer_id is null or char_length(stripe_customer_id) between 4 and 255),
  requested_at timestamptz not null default now(),
  scheduled_purge_at timestamptz not null,
  canceled_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint account_deletion_requests_profile_identity_uq unique (
    user_id, deletion_request_id, requested_at, scheduled_purge_at
  ),
  constraint account_deletion_requests_state_ck check (
    scheduled_purge_at = requested_at + interval '30 days'
    and (
      (canceled_at is null and completed_at is null)
      or (
        canceled_at is not null and completed_at is null
        and canceled_at >= requested_at and canceled_at < scheduled_purge_at
      )
      or (
        completed_at is not null and canceled_at is null
        and completed_at >= scheduled_purge_at
      )
    )
  )
);

alter table private.account_deletion_requests
  add constraint account_deletion_requests_profile_fk foreign key (
    user_id, deletion_request_id, requested_at, scheduled_purge_at
  ) references private.profiles (
    user_id, deletion_request_id, deletion_requested_at, scheduled_purge_at
  ) deferrable initially deferred;

alter table private.profiles
  add constraint profiles_deletion_request_fk foreign key (
    user_id, deletion_request_id, deletion_requested_at, scheduled_purge_at
  ) references private.account_deletion_requests (
    user_id, deletion_request_id, requested_at, scheduled_purge_at
  ) deferrable initially deferred;

create table private.account_deletion_jobs (
  id uuid primary key default gen_random_uuid(),
  deletion_request_id uuid not null references private.account_deletion_requests(deletion_request_id) on delete cascade,
  operation text not null check (
    operation in (
      'revoke_auth_sessions', 'cancel_stripe_at_period_end',
      'send_deletion_confirmation', 'write_purge_manifest',
      'purge_application_data', 'delete_auth_user'
    )
  ),
  state text not null default 'pending' check (
    state in ('pending', 'processing', 'retryable', 'succeeded', 'terminal', 'canceled')
  ),
  not_before timestamptz not null default now(),
  attempt_count integer not null default 0 check (attempt_count >= 0),
  lease_until timestamptz,
  fencing_token bigint not null default 0 check (fencing_token >= 0),
  provider_reference text check (provider_reference is null or char_length(provider_reference) <= 255),
  last_error_code text check (last_error_code is null or char_length(last_error_code) <= 120),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz,
  constraint account_deletion_jobs_operation_uq unique (deletion_request_id, operation),
  constraint account_deletion_jobs_state_ck check (
    (state in ('pending', 'retryable') and lease_until is null and completed_at is null)
    or (state = 'processing' and lease_until is not null and completed_at is null)
    or (state in ('succeeded', 'terminal', 'canceled') and lease_until is null and completed_at is not null)
  )
);

create or replace function private.guard_migration_record_update()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
begin
  if old.source_entity_type <> 'account' then
    raise exception 'imported migration child rows are immutable' using errcode = '23514';
  end if;
  if new.id is distinct from old.id
    or new.source_entity_type is distinct from old.source_entity_type
    or new.source_identity_hmac is distinct from old.source_identity_hmac
    or new.source_key_hmac is distinct from old.source_key_hmac
    or new.account_claim_id is distinct from old.account_claim_id
    or new.checksum is distinct from old.checksum
    or new.migration_revision is distinct from old.migration_revision
    or new.imported_at is distinct from old.imported_at
  then
    raise exception 'migration manifest identity is immutable' using errcode = '23514';
  end if;
  if old.claimed_user_id is null then
    if new.claimed_user_id is null and new.target_id is null then
      return new;
    end if;
    if new.claimed_user_id is not null
      and new.target_id is not null
      and new.target_id = new.claimed_user_id
    then
      return new;
    end if;
    raise exception 'migration claim must bind one matching immutable user' using errcode = '23514';
  end if;
  if new.claimed_user_id is distinct from old.claimed_user_id
    or new.target_id is distinct from old.target_id
  then
    raise exception 'migration claim cannot be removed or reassigned' using errcode = '23514';
  end if;
  return new;
end
$$;
revoke all on function private.guard_migration_record_update()
  from public, anon, authenticated, kyr_api_runtime, kyr_identity_worker_runtime;
create trigger migration_records_immutable_guard
before update on private.migration_records
for each row execute function private.guard_migration_record_update();

create or replace function private.guard_account_deletion_request_update()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
begin
  if new.deletion_request_id is distinct from old.deletion_request_id
    or new.deletion_identity_hmac is distinct from old.deletion_identity_hmac
    or new.requested_at is distinct from old.requested_at
    or new.scheduled_purge_at is distinct from old.scheduled_purge_at
    or new.created_at is distinct from old.created_at
  then
    raise exception 'deletion request identity and deadline are immutable' using errcode = '23514';
  end if;
  if old.user_id is null and new.user_id is not null then
    raise exception 'purged deletion identity cannot be rebound' using errcode = '23514';
  end if;
  if old.user_id is not null and new.user_id is null and pg_trigger_depth() < 2 then
    if not (old.canceled_at is null and new.canceled_at is not null and new.completed_at is null) then
      raise exception 'deletion request user may clear only through recovery or the profile FK action'
        using errcode = '23514';
    end if;
    if (
      select count(*) <> 6
      from private.account_deletion_jobs
      where deletion_request_id = old.deletion_request_id
    ) or exists (
      select 1
      from private.account_deletion_jobs
      where deletion_request_id = old.deletion_request_id
        and operation <> 'cancel_stripe_at_period_end'
        and state not in ('succeeded', 'terminal', 'canceled')
    ) or not exists (
      select 1
      from private.account_deletion_jobs
      where deletion_request_id = old.deletion_request_id
        and operation = 'cancel_stripe_at_period_end'
        and state <> 'canceled'
    ) then
      raise exception 'recovery requires a complete outbox, terminal destructive jobs, and preserved Stripe intent'
        using errcode = '23514';
    end if;
  end if;
  if old.user_id is not null and new.user_id is not null
    and new.user_id is distinct from old.user_id
  then
    raise exception 'deletion request cannot move to another user' using errcode = '23514';
  end if;
  if old.canceled_at is not null and new.canceled_at is distinct from old.canceled_at then
    raise exception 'canceled deletion request is immutable' using errcode = '23514';
  end if;
  if old.completed_at is not null and new.completed_at is distinct from old.completed_at then
    raise exception 'completed deletion request is immutable' using errcode = '23514';
  end if;
  if old.stripe_customer_id is not null and new.stripe_customer_id is not null
    and new.stripe_customer_id is distinct from old.stripe_customer_id
  then
    raise exception 'deletion request cannot move to another Stripe customer' using errcode = '23514';
  end if;
  if old.stripe_customer_id is not null and new.stripe_customer_id is null then
    if new.canceled_at is null and new.completed_at is null then
      raise exception 'unresolved Stripe identity cannot be cleared from an open request'
        using errcode = '23514';
    end if;
    if not exists (
      select 1
      from private.account_deletion_jobs
      where deletion_request_id = old.deletion_request_id
        and operation = 'cancel_stripe_at_period_end'
        and state in ('succeeded', 'terminal')
    ) then
      raise exception 'Stripe identity cannot clear before cancellation reaches a safe terminal state'
        using errcode = '23514';
    end if;
  end if;
  if old.stripe_customer_id is null and new.stripe_customer_id is not null
    and not exists (
      select 1
      from private.account_deletion_jobs
      where deletion_request_id = old.deletion_request_id
        and operation = 'cancel_stripe_at_period_end'
        and state in ('pending', 'retryable', 'processing')
    )
  then
    raise exception 'provider identity may attach only while Stripe cancellation remains actionable'
      using errcode = '23514';
  end if;
  return new;
end
$$;
revoke all on function private.guard_account_deletion_request_update()
  from public, anon, authenticated, kyr_api_runtime, kyr_identity_worker_runtime;
create trigger account_deletion_requests_immutable_guard
before update on private.account_deletion_requests
for each row execute function private.guard_account_deletion_request_update();

create table private.purge_tombstones (
  id uuid primary key default gen_random_uuid(),
  deletion_identity_hmac bytea not null unique check (octet_length(deletion_identity_hmac) = 32),
  migration_identity_hmac bytea check (migration_identity_hmac is null or octet_length(migration_identity_hmac) = 32),
  stripe_customer_hmac bytea check (stripe_customer_hmac is null or octet_length(stripe_customer_hmac) = 32),
  purged_at timestamptz not null,
  manifest_version text not null check (char_length(manifest_version) between 1 and 80),
  created_at timestamptz not null default now()
);

create table private.security_audit_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references private.profiles(user_id) on delete set null,
  event_type text not null check (char_length(event_type) between 1 and 120),
  outcome text not null check (outcome in ('allowed', 'denied', 'failed')),
  correlation_id uuid not null,
  metadata jsonb not null default '{}'::jsonb check (jsonb_typeof(metadata) = 'object'),
  created_at timestamptz not null default now()
);

create unique index entitlements_stripe_customer_uq
  on private.entitlements (stripe_customer_id) where stripe_customer_id is not null;
create unique index profiles_deletion_request_uq
  on private.profiles (deletion_request_id) where deletion_request_id is not null;
create unique index entitlements_stripe_subscription_uq
  on private.entitlements (stripe_subscription_id) where stripe_subscription_id is not null;
create index garage_vehicles_user_state_idx on private.garage_vehicles (user_id, state, created_at);
create unique index garage_vehicles_user_vin_uq
  on private.garage_vehicles (user_id, vin) where vin is not null;
create index service_events_vehicle_date_idx
  on private.service_events (user_id, garage_vehicle_id, performed_on desc) where deleted_at is null;
create index service_events_owner_vehicle_fk_idx
  on private.service_events (user_id, garage_vehicle_id);
create index service_event_parts_event_idx on private.service_event_parts (user_id, service_event_id);
create index mileage_readings_vehicle_observed_idx
  on private.mileage_readings (user_id, garage_vehicle_id, observed_at desc);
create index expense_events_vehicle_date_idx
  on private.expense_events (user_id, garage_vehicle_id, expense_on desc) where deleted_at is null;
create index expense_events_owner_vehicle_fk_idx
  on private.expense_events (user_id, garage_vehicle_id);
create index credit_ledger_user_created_idx on private.credit_ledger (user_id, created_at);
create unique index credit_ledger_single_grant_uq
  on private.credit_ledger (user_id)
  where reason in ('initial_grant', 'migration_grant');
create index stripe_webhook_claim_idx
  on private.stripe_webhook_events (processing_status, lease_until, stripe_created_at)
  where processing_status in ('received', 'failed', 'processing');
create index app_sessions_user_active_idx
  on private.app_sessions (user_id, maximum_expires_at) where revoked_at is null;
create index app_sessions_user_fk_idx on private.app_sessions (user_id);
create index migration_records_claimed_user_idx
  on private.migration_records (claimed_user_id) where claimed_user_id is not null;
create index migration_records_account_claim_fk_idx
  on private.migration_records (account_claim_id) where account_claim_id is not null;
create unique index migration_records_account_identity_uq
  on private.migration_records (migration_revision, source_identity_hmac)
  where source_entity_type = 'account';
create unique index migration_records_account_user_uq
  on private.migration_records (migration_revision, claimed_user_id)
  where source_entity_type = 'account';
create unique index migration_records_target_uq
  on private.migration_records (migration_revision, source_entity_type, target_id)
  where target_id is not null;
create index account_deletion_jobs_claim_idx
  on private.account_deletion_jobs (state, not_before, lease_until)
  where state in ('pending', 'retryable', 'processing');
create index account_deletion_requests_user_fk_idx
  on private.account_deletion_requests (user_id) where user_id is not null;
create unique index account_deletion_requests_live_identity_uq
  on private.account_deletion_requests (deletion_identity_hmac)
  where canceled_at is null;
create unique index account_deletion_requests_open_user_uq
  on private.account_deletion_requests (user_id)
  where user_id is not null and canceled_at is null and completed_at is null;
create index security_audit_events_user_created_idx
  on private.security_audit_events (user_id, created_at desc) where user_id is not null;
create index security_audit_events_user_fk_idx
  on private.security_audit_events (user_id);

do $$
declare
  table_name text;
begin
  foreach table_name in array array[
    'profiles', 'entitlements', 'garage_vehicles', 'service_events',
    'service_event_parts', 'mileage_readings', 'expense_events', 'credit_ledger',
    'stripe_webhook_events', 'app_sessions', 'migration_records',
    'account_deletion_requests', 'account_deletion_jobs',
    'purge_tombstones', 'security_audit_events'
  ]
  loop
    execute format('alter table private.%I enable row level security', table_name);
    execute format('alter table private.%I force row level security', table_name);
    execute format(
      'revoke all on table private.%I from public, anon, authenticated, kyr_api_runtime, kyr_identity_worker_runtime',
      table_name
    );
  end loop;
end
$$;

grant select, insert, update on private.profiles
  to kyr_user_function_owner, kyr_ops_function_owner;
grant select on private.entitlements to kyr_user_function_owner;
grant select, insert, update on private.entitlements to kyr_ops_function_owner;
grant select, insert, update on private.garage_vehicles, private.service_events,
  private.expense_events to kyr_user_function_owner, kyr_ops_function_owner;
grant select, insert, update, delete on private.service_event_parts
  to kyr_user_function_owner;
grant select, insert, update on private.service_event_parts
  to kyr_ops_function_owner;
grant select, insert on private.mileage_readings, private.credit_ledger
  to kyr_user_function_owner, kyr_ops_function_owner;
grant insert on private.security_audit_events to kyr_user_function_owner;
grant select, insert, update on private.app_sessions
  to kyr_user_function_owner, kyr_ops_function_owner;
grant select, insert, update on private.stripe_webhook_events,
  private.migration_records, private.account_deletion_requests,
  private.account_deletion_jobs
  to kyr_ops_function_owner;
grant select, insert on private.purge_tombstones, private.security_audit_events
  to kyr_ops_function_owner;

create or replace function private.current_user_id()
returns uuid
language sql
stable
security invoker
set search_path = pg_catalog
as $$
  select nullif(current_setting('kyr.user_id', true), '')::uuid
$$;
revoke all on function private.current_user_id() from public, anon, authenticated, kyr_api_runtime;
revoke all on function private.current_user_id() from kyr_identity_worker_runtime;
grant execute on function private.current_user_id() to kyr_user_function_owner;

-- No ALL policies: each command is explicit so a later accidental table grant
-- cannot silently activate a previously unused DELETE path.
do $$
declare
  policy_row record;
begin
  for policy_row in
    select * from (values
      ('profiles', 'select'), ('profiles', 'insert'), ('profiles', 'update'),
      ('entitlements', 'select'),
      ('garage_vehicles', 'select'), ('garage_vehicles', 'insert'), ('garage_vehicles', 'update'),
      ('service_events', 'select'), ('service_events', 'insert'), ('service_events', 'update'),
      ('service_event_parts', 'select'), ('service_event_parts', 'insert'),
      ('service_event_parts', 'update'), ('service_event_parts', 'delete'),
      ('mileage_readings', 'select'), ('mileage_readings', 'insert'),
      ('expense_events', 'select'), ('expense_events', 'insert'), ('expense_events', 'update'),
      ('credit_ledger', 'select'), ('credit_ledger', 'insert'),
      ('app_sessions', 'select'), ('app_sessions', 'insert'), ('app_sessions', 'update'),
      ('security_audit_events', 'insert')
    ) as policies(table_name, command_name)
  loop
    if policy_row.command_name = 'insert' then
      execute format(
        'create policy %I on private.%I for insert to kyr_user_function_owner with check (user_id = private.current_user_id())',
        policy_row.table_name || '_user_insert', policy_row.table_name
      );
    elsif policy_row.command_name = 'update' then
      execute format(
        'create policy %I on private.%I for update to kyr_user_function_owner using (user_id = private.current_user_id()) with check (user_id = private.current_user_id())',
        policy_row.table_name || '_user_update', policy_row.table_name
      );
    else
      execute format(
        'create policy %I on private.%I for %s to kyr_user_function_owner using (user_id = private.current_user_id())',
        policy_row.table_name || '_user_' || policy_row.command_name,
        policy_row.table_name,
        policy_row.command_name
      );
    end if;
  end loop;
end
$$;

do $$
declare
  policy_row record;
begin
  for policy_row in
    select * from (values
      ('profiles', 'select'), ('profiles', 'insert'), ('profiles', 'update'),
      ('entitlements', 'select'), ('entitlements', 'insert'), ('entitlements', 'update'),
      ('garage_vehicles', 'select'), ('garage_vehicles', 'insert'), ('garage_vehicles', 'update'),
      ('service_events', 'select'), ('service_events', 'insert'), ('service_events', 'update'),
      ('service_event_parts', 'select'), ('service_event_parts', 'insert'), ('service_event_parts', 'update'),
      ('mileage_readings', 'select'), ('mileage_readings', 'insert'),
      ('expense_events', 'select'), ('expense_events', 'insert'), ('expense_events', 'update'),
      ('credit_ledger', 'select'), ('credit_ledger', 'insert'),
      ('app_sessions', 'select'), ('app_sessions', 'insert'), ('app_sessions', 'update'),
      ('stripe_webhook_events', 'select'), ('stripe_webhook_events', 'insert'), ('stripe_webhook_events', 'update'),
      ('migration_records', 'select'), ('migration_records', 'insert'), ('migration_records', 'update'),
      ('account_deletion_requests', 'select'), ('account_deletion_requests', 'insert'), ('account_deletion_requests', 'update'),
      ('account_deletion_jobs', 'select'), ('account_deletion_jobs', 'insert'), ('account_deletion_jobs', 'update'),
      ('purge_tombstones', 'select'), ('purge_tombstones', 'insert'),
      ('security_audit_events', 'select'), ('security_audit_events', 'insert')
    ) as policies(table_name, command_name)
  loop
    if policy_row.command_name = 'insert' then
      execute format(
        'create policy %I on private.%I for insert to kyr_ops_function_owner with check (true)',
        policy_row.table_name || '_ops_insert', policy_row.table_name
      );
    elsif policy_row.command_name = 'update' then
      execute format(
        'create policy %I on private.%I for update to kyr_ops_function_owner using (true) with check (true)',
        policy_row.table_name || '_ops_update', policy_row.table_name
      );
    else
      execute format(
        'create policy %I on private.%I for select to kyr_ops_function_owner using (true)',
        policy_row.table_name || '_ops_select', policy_row.table_name
      );
    end if;
  end loop;
end
$$;

create or replace function private.foundation_health()
returns jsonb
language sql
stable
security invoker
set search_path = pg_catalog
as $$
  select jsonb_build_object(
    'schema_revision', 's1-v1',
    'private_table_count', (
      select count(*)
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'private' and c.relkind = 'r'
    )
  )
$$;
revoke all on function private.foundation_health()
  from public, anon, authenticated, kyr_identity_worker_runtime;
grant execute on function private.foundation_health() to kyr_api_runtime;

alter default privileges for role postgres in schema private
  revoke all on tables from public, anon, authenticated,
    kyr_api_runtime, kyr_identity_worker_runtime;
alter default privileges for role postgres in schema private
  revoke all on sequences from public, anon, authenticated,
    kyr_api_runtime, kyr_identity_worker_runtime;
alter default privileges for role postgres in schema private
  revoke execute on functions from public, anon, authenticated,
    kyr_api_runtime, kyr_identity_worker_runtime;
alter default privileges for role kyr_table_owner in schema private
  revoke all on tables from public, anon, authenticated,
    kyr_api_runtime, kyr_identity_worker_runtime;
alter default privileges for role kyr_table_owner in schema private
  revoke all on sequences from public, anon, authenticated,
    kyr_api_runtime, kyr_identity_worker_runtime;
alter default privileges for role kyr_table_owner in schema private
  revoke execute on functions from public, anon, authenticated,
    kyr_api_runtime, kyr_identity_worker_runtime;
alter default privileges for role kyr_user_function_owner in schema private
  revoke execute on functions from public, anon, authenticated,
    kyr_api_runtime, kyr_identity_worker_runtime;
alter default privileges for role kyr_ops_function_owner in schema private
  revoke execute on functions from public, anon, authenticated,
    kyr_api_runtime, kyr_identity_worker_runtime;

alter function private.current_user_id() owner to kyr_user_function_owner;
alter function private.foundation_health() owner to kyr_user_function_owner;
alter function private.guard_stripe_webhook_event_update() owner to kyr_table_owner;
alter function private.guard_migration_record_update() owner to kyr_table_owner;
alter function private.guard_account_deletion_request_update() owner to kyr_table_owner;

do $$
declare
  table_name text;
begin
  foreach table_name in array array[
    'profiles', 'entitlements', 'garage_vehicles', 'service_events',
    'service_event_parts', 'mileage_readings', 'expense_events', 'credit_ledger',
    'stripe_webhook_events', 'app_sessions', 'migration_records',
    'account_deletion_requests', 'account_deletion_jobs',
    'purge_tombstones', 'security_audit_events'
  ]
  loop
    execute format('alter table private.%I owner to kyr_table_owner', table_name);
  end loop;
end
$$;

alter schema private owner to kyr_table_owner;
set role kyr_table_owner;
revoke create on schema private from kyr_user_function_owner, kyr_ops_function_owner;
reset role;
do $$
begin
  execute format('revoke create on database %I from kyr_table_owner', current_database());
end
$$;
```

In this outbox, `purge_application_data` means post-Auth-delete cascade verification and any separately reviewed final cleanup; it does not pre-delete the profile. S6 must enforce operation dependencies and the external-manifest-before-Auth-delete rule.

- [ ] **Step 4: Confirm the migration contains no secret or email value.**

```powershell
Select-String -Path supabase/migrations/*_tier2_foundation.sql -Pattern 'password\s+''[^'']+''|@|service_role|secret_key' -CaseSensitive:$false
```

Expected: no matches. `password null` is intentionally safe and may be visually confirmed.

- [ ] **Step 5: Do not link or push Supabase yet. Commit the replayable source only after Task 4 adds tests.**

---

### Task 4: Add database security and constraint tests

**Files:**

- Create: `supabase/tests/database/001_foundation_security.test.sql`
- Create: `supabase/tests/database/002_foundation_constraints.test.sql`
- Create: `supabase/tests/database/003_foundation_behavior.test.sql`
- Create: `supabase/tests/database/004_foundation_invariants.test.sql`
- Create: `supabase/tests/database/005_linked_test_rollback.test.sql`
- Create: `tests/deployment/__init__.py`
- Create: `tests/deployment/test_supabase_config.py`
- Create: `tests/deployment/test_foundation_migration_source.py`

**Interfaces:**

- Consumes: the CLI-created empty config/migration stubs from Task 3 Steps 1-2.
- Produces: local config and migration-source contracts plus five transactional pgTAP suites that are the RED/GREEN authority for Task 3's schema and Task 9's clean replay.

- [ ] **Step 1: Add the structural security suite.**

Create `supabase/tests/database/001_foundation_security.test.sql`:

```sql
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = extensions, public, pg_catalog;
select no_plan();

select ok(to_regnamespace('private') is not null, 'private schema exists');
select is(
  (select count(*)::integer from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'private' and c.relkind = 'r'),
  15,
  'exact foundation table count'
);
select ok(
  not exists (
    select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'private' and c.relkind = 'r' and not c.relrowsecurity
  ),
  'all private tables enable RLS'
);
select ok(
  not exists (
    select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'private' and c.relkind = 'r' and not c.relforcerowsecurity
  ),
  'all private tables force RLS'
);
select ok(not has_schema_privilege('anon', 'private', 'USAGE'), 'anon has no private schema usage');
select ok(not has_schema_privilege('authenticated', 'private', 'USAGE'), 'authenticated has no private schema usage');
select ok(
  not exists (
    select 1 from information_schema.role_table_grants
    where table_schema = 'private' and grantee in ('PUBLIC', 'anon', 'authenticated')
  ),
  'browser roles have no private table grants'
);
select ok(
  not exists (
    select 1 from information_schema.role_table_grants
    where table_schema = 'private' and grantee = 'kyr_api_runtime'
  ),
  'API runtime has no arbitrary table grant'
);
select ok(
  exists (select 1 from pg_roles where rolname = 'kyr_api_runtime' and rolcanlogin
    and not rolsuper and not rolcreaterole and not rolcreatedb and not rolbypassrls
    and not rolinherit and not rolreplication),
  'API runtime is a constrained login role'
);
select ok(
  exists (select 1 from pg_roles where rolname = 'kyr_table_owner' and not rolcanlogin
    and not rolsuper and not rolcreaterole and not rolcreatedb and not rolbypassrls
    and not rolinherit and not rolreplication),
  'table owner is NOLOGIN and cannot bypass RLS'
);
select ok(
  not exists (
    select 1 from pg_roles
    where rolname in ('kyr_user_function_owner', 'kyr_ops_function_owner')
      and (rolcanlogin or rolsuper or rolcreaterole or rolcreatedb
        or rolbypassrls or rolinherit or rolreplication)
  ),
  'both function owners are NOLOGIN, NOINHERIT, and non-privileged'
);
select ok(
  exists (
    select 1 from pg_roles
    where rolname = 'kyr_identity_worker_runtime' and rolcanlogin
      and not rolsuper and not rolcreaterole and not rolcreatedb
      and not rolbypassrls and not rolinherit and not rolreplication
  ),
  'identity worker has its own constrained login role'
);
select ok(
  pg_has_role('postgres', 'kyr_table_owner', 'SET')
  and pg_has_role('postgres', 'kyr_user_function_owner', 'SET')
  and pg_has_role('postgres', 'kyr_ops_function_owner', 'SET')
  and pg_has_role('postgres', 'kyr_api_runtime', 'SET')
  and pg_has_role('postgres', 'kyr_identity_worker_runtime', 'SET'),
  'managed postgres retains SET membership for replayable migrations'
);
select ok(
  not pg_has_role('kyr_api_runtime', 'kyr_user_function_owner', 'MEMBER')
  and not pg_has_role('kyr_api_runtime', 'kyr_ops_function_owner', 'MEMBER')
  and not pg_has_role('kyr_identity_worker_runtime', 'kyr_user_function_owner', 'MEMBER')
  and not pg_has_role('kyr_identity_worker_runtime', 'kyr_ops_function_owner', 'MEMBER'),
  'runtime roles cannot inherit or SET either function-owner role'
);
select ok(
  not exists (
    select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'private' and c.relkind = 'r'
      and pg_get_userbyid(c.relowner) <> 'kyr_table_owner'
  ),
  'every private table has the non-bypass table owner'
);
select is(
  (select nspowner::regrole::text from pg_namespace where nspname = 'private'),
  'kyr_table_owner',
  'private schema ownership transfers last'
);
select ok(
  not has_database_privilege('kyr_table_owner', current_database(), 'CREATE'),
  'temporary database CREATE was revoked after schema transfer'
);
select ok(has_function_privilege('kyr_api_runtime', 'private.foundation_health()', 'EXECUTE'),
  'API role can execute reviewed health function');
select ok(not has_function_privilege('anon', 'private.foundation_health()', 'EXECUTE'),
  'anon cannot execute health function');
select ok(not has_function_privilege('authenticated', 'private.foundation_health()', 'EXECUTE'),
  'authenticated cannot execute health function');
select ok(not has_function_privilege('kyr_identity_worker_runtime', 'private.foundation_health()', 'EXECUTE'),
  'identity worker cannot execute the main probe');
select ok(
  exists (
    select 1
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'private' and p.proname = 'foundation_health'
      and not p.prosecdef and pg_get_userbyid(p.proowner) = 'kyr_user_function_owner'
      and p.proconfig @> array['search_path=pg_catalog']
  ),
  'health function is SECURITY INVOKER with reviewed owner and locked search_path'
);
select ok(
  exists (
    select 1
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'private' and p.proname = 'current_user_id'
      and not p.prosecdef and pg_get_userbyid(p.proowner) = 'kyr_user_function_owner'
      and p.proconfig @> array['search_path=pg_catalog']
  ),
  'identity helper is SECURITY INVOKER with reviewed owner and locked search_path'
);
select ok(
  not exists (
    select 1 from pg_policies
    where schemaname = 'private'
      and (cmd = 'ALL' or roles && array['public', 'anon', 'authenticated',
        'kyr_api_runtime', 'kyr_identity_worker_runtime']::name[])
  ),
  'policies are command-specific and never target browser/runtime roles'
);
select ok(
  not has_function_privilege('kyr_ops_function_owner', 'private.guard_migration_record_update()', 'EXECUTE')
  and not has_function_privilege('kyr_ops_function_owner', 'private.guard_account_deletion_request_update()', 'EXECUTE')
  and not has_function_privilege('kyr_ops_function_owner', 'private.guard_stripe_webhook_event_update()', 'EXECUTE')
  and not has_function_privilege('kyr_user_function_owner', 'private.guard_migration_record_update()', 'EXECUTE')
  and not has_function_privilege('kyr_user_function_owner', 'private.guard_account_deletion_request_update()', 'EXECUTE')
  and not has_function_privilege('kyr_user_function_owner', 'private.guard_stripe_webhook_event_update()', 'EXECUTE')
  and not has_function_privilege('kyr_api_runtime', 'private.guard_migration_record_update()', 'EXECUTE')
  and not has_function_privilege('kyr_api_runtime', 'private.guard_account_deletion_request_update()', 'EXECUTE')
  and not has_function_privilege('kyr_api_runtime', 'private.guard_stripe_webhook_event_update()', 'EXECUTE')
  and not has_function_privilege('kyr_identity_worker_runtime', 'private.guard_migration_record_update()', 'EXECUTE')
  and not has_function_privilege('kyr_identity_worker_runtime', 'private.guard_account_deletion_request_update()', 'EXECUTE')
  and not has_function_privilege('kyr_identity_worker_runtime', 'private.guard_stripe_webhook_event_update()', 'EXECUTE'),
  'guard trigger functions cannot be invoked as runtime commands'
);
select ok(
  (
    select count(*) = 3
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'private'
      and p.proname in (
        'guard_stripe_webhook_event_update',
        'guard_migration_record_update',
        'guard_account_deletion_request_update'
      )
      and not p.prosecdef
      and pg_get_userbyid(p.proowner) = 'kyr_table_owner'
      and p.proconfig @> array['search_path=pg_catalog']
  ),
  'guard triggers use invoker rights, locked search_path, and the table owner'
);

select * from finish();
rollback;
```

- [ ] **Step 2: Add the ownership/constraint/index suite.**

Create `supabase/tests/database/002_foundation_constraints.test.sql`:

```sql
begin;
create extension if not exists pgtap with schema extensions;
-- Transactional test-only grants; rollback removes them after role-switch assertions.
grant usage on schema extensions
  to kyr_user_function_owner, kyr_ops_function_owner, kyr_api_runtime;
set local search_path = extensions, public, pg_catalog;
select no_plan();

select ok(
  exists (select 1 from pg_constraint
    where conrelid = 'private.service_events'::regclass
      and conname = 'service_events_vehicle_fk' and confdeltype = 'c'),
  'service event ownership cascades from garage vehicle'
);
select ok(
  exists (select 1 from pg_constraint
    where conrelid = 'private.service_event_parts'::regclass
      and conname = 'service_event_parts_event_fk' and confdeltype = 'c'),
  'part ownership cascades from service event'
);
select ok(
  exists (select 1 from pg_constraint
    where conrelid = 'private.mileage_readings'::regclass
      and conname = 'mileage_readings_service_fk' and confdeltype = 'c'),
  'service mileage is tied to same owner and vehicle'
);
select ok(
  exists (select 1 from pg_constraint
    where conrelid = 'private.service_events'::regclass
      and conname = 'service_events_request_uq' and contype = 'u'),
  'service request UUID is owner-idempotent'
);
select ok(
  exists (select 1 from pg_constraint
    where conrelid = 'private.credit_ledger'::regclass
      and conname = 'credit_ledger_service_uq' and contype = 'u'),
  'one service can consume at most one credit'
);
select ok(to_regclass('private.garage_vehicles_user_state_idx') is not null, 'garage limit index exists');
select ok(to_regclass('private.service_events_vehicle_date_idx') is not null, 'service history index exists');
select ok(to_regclass('private.mileage_readings_vehicle_observed_idx') is not null, 'mileage index exists');
select ok(to_regclass('private.expense_events_vehicle_date_idx') is not null, 'expense index exists');
select ok(to_regclass('private.stripe_webhook_claim_idx') is not null, 'webhook claim index exists');
select ok(to_regclass('private.account_deletion_jobs_claim_idx') is not null, 'deletion claim index exists');
select ok(to_regclass('private.account_deletion_requests_live_identity_uq') is not null,
  'only live deletion requests reserve a keyed identity');
select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'private.credit_ledger'::regclass
      and conname = 'credit_ledger_service_fk'
      and confdeltype = 'a' and condeferrable and condeferred
  ),
  'credit consumption survives ordinary hard-delete attempts'
);
select ok(to_regclass('private.credit_ledger_single_grant_uq') is not null,
  'one initial-or-migration grant index exists');
select ok(to_regclass('private.migration_records_account_identity_uq') is not null,
  'legacy account identity can be claimed once');
select ok(to_regclass('private.migration_records_account_user_uq') is not null,
  'one user can claim one legacy account per migration revision');
select ok(to_regclass('private.migration_records_target_uq') is not null,
  'one migration target maps from one source');
select ok(to_regclass('private.migration_records_account_claim_fk_idx') is not null,
  'migration child-to-account claim FK has a leading index');
select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'private.entitlements'::regclass
      and conname = 'entitlements_source_shape_ck'
  ),
  'entitlement source/status/provider fields are cross-constrained'
);
select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'private.stripe_webhook_events'::regclass
      and conname = 'stripe_webhook_events_state_ck'
  ),
  'Stripe inbox status, lease, and completion timestamp are cross-constrained'
);
select ok(
  exists (
    select 1 from pg_trigger
    where tgrelid = 'private.stripe_webhook_events'::regclass
      and tgname = 'stripe_webhook_events_state_guard' and tgenabled = 'O'
  ),
  'Stripe inbox retries and terminal transitions have a fencing guard'
);
select ok(
  (
    select count(*) = 2
    from pg_constraint
    where conname in (
      'account_deletion_requests_profile_fk',
      'profiles_deletion_request_fk'
    ) and contype = 'f' and condeferrable and condeferred
  ),
  'deletion request and profile have bidirectional deferred identity bindings'
);
select ok(
  exists (
    select 1 from pg_trigger
    where tgrelid = 'private.migration_records'::regclass
      and tgname = 'migration_records_immutable_guard' and tgenabled = 'O'
  ),
  'migration claims have an immutable one-way update guard'
);
select ok(
  exists (
    select 1 from pg_trigger
    where tgrelid = 'private.account_deletion_requests'::regclass
      and tgname = 'account_deletion_requests_immutable_guard' and tgenabled = 'O'
  ),
  'deletion request identity and deadline have an immutable update guard'
);
select is(
  (
    select array_agg(a.attname order by k.ordinality)
    from pg_class i
    join pg_namespace n on n.oid = i.relnamespace
    join pg_index x on x.indexrelid = i.oid
    cross join lateral unnest(x.indkey) with ordinality as k(attnum, ordinality)
    join pg_attribute a on a.attrelid = x.indrelid and a.attnum = k.attnum
    where n.nspname = 'private' and i.relname = 'service_events_owner_vehicle_fk_idx'
  ),
  array['user_id', 'garage_vehicle_id']::text[],
  'service-event FK has a full owner/vehicle index'
);
select is(
  (
    select array_agg(a.attname order by k.ordinality)
    from pg_class i
    join pg_namespace n on n.oid = i.relnamespace
    join pg_index x on x.indexrelid = i.oid
    cross join lateral unnest(x.indkey) with ordinality as k(attnum, ordinality)
    join pg_attribute a on a.attrelid = x.indrelid and a.attnum = k.attnum
    where n.nspname = 'private' and i.relname = 'expense_events_owner_vehicle_fk_idx'
  ),
  array['user_id', 'garage_vehicle_id']::text[],
  'expense FK has a full owner/vehicle index'
);
select is(
  (
    select array_agg(a.attname order by k.ordinality)
    from pg_class i
    join pg_namespace n on n.oid = i.relnamespace
    join pg_index x on x.indexrelid = i.oid
    cross join lateral unnest(x.indkey) with ordinality as k(attnum, ordinality)
    join pg_attribute a on a.attrelid = x.indrelid and a.attnum = k.attnum
    where n.nspname = 'private' and i.relname = 'app_sessions_user_fk_idx'
  ),
  array['user_id']::text[],
  'session FK has a full user index'
);
select is(
  (
    select array_agg(a.attname order by k.ordinality)
    from pg_class i
    join pg_namespace n on n.oid = i.relnamespace
    join pg_index x on x.indexrelid = i.oid
    cross join lateral unnest(x.indkey) with ordinality as k(attnum, ordinality)
    join pg_attribute a on a.attrelid = x.indrelid and a.attnum = k.attnum
    where n.nspname = 'private' and i.relname = 'account_deletion_requests_user_fk_idx'
  ),
  array['user_id']::text[],
  'deletion-request FK has a full user index'
);
select ok(
  not has_table_privilege('kyr_user_function_owner', 'private.service_events', 'DELETE')
  and not has_table_privilege('kyr_user_function_owner', 'private.credit_ledger', 'UPDATE')
  and not has_table_privilege('kyr_user_function_owner', 'private.credit_ledger', 'DELETE')
  and not has_table_privilege('kyr_ops_function_owner', 'private.purge_tombstones', 'UPDATE')
  and not has_table_privilege('kyr_ops_function_owner', 'private.purge_tombstones', 'DELETE')
  and not has_table_privilege('kyr_ops_function_owner', 'private.security_audit_events', 'UPDATE')
  and not has_table_privilege('kyr_ops_function_owner', 'private.security_audit_events', 'DELETE'),
  'soft-delete and append-only ACLs are exact'
);
set local role kyr_ops_function_owner;
select throws_ok(
  $$insert into private.purge_tombstones
      (deletion_identity_hmac, purged_at, manifest_version)
    values (decode('00', 'hex'), now(), 'v1')$$,
  '23514',
  null,
  'tombstone HMAC must be 32 bytes'
);
reset role;

set local role kyr_api_runtime;
select throws_ok(
  $$select * from private.profiles$$,
  '42501',
  null,
  'API runtime cannot select private tables'
);
reset role;

select * from finish();
rollback;
```

- [ ] **Step 2a: Add executable two-user RLS behavior tests.**

Create supabase/tests/database/003_foundation_behavior.test.sql:

~~~sql
begin;
create extension if not exists pgtap with schema extensions;
-- Transactional test-only grants; rollback removes them after role-switch assertions.
grant usage on schema extensions
  to kyr_user_function_owner, kyr_ops_function_owner, kyr_api_runtime;
set local search_path = extensions, public, pg_catalog;
select no_plan();

insert into auth.users (
  id, aud, role, email, encrypted_password, email_confirmed_at,
  raw_app_meta_data, raw_user_meta_data, created_at, updated_at
) values
  ('11111111-1111-1111-1111-111111111111', 'authenticated', 'authenticated',
    's1-one@example.invalid', '', now(), '{}'::jsonb, '{}'::jsonb, now(), now()),
  ('22222222-2222-2222-2222-222222222222', 'authenticated', 'authenticated',
    's1-two@example.invalid', '', now(), '{}'::jsonb, '{}'::jsonb, now(), now());

set local role kyr_ops_function_owner;
insert into private.profiles (user_id) values
  ('11111111-1111-1111-1111-111111111111'),
  ('22222222-2222-2222-2222-222222222222');
reset role;

set local role kyr_user_function_owner;
select is((select count(*)::integer from private.profiles), 0,
  'missing transaction-local identity sees no profile');
select set_config('kyr.user_id', '11111111-1111-1111-1111-111111111111', true);
select is((select count(*)::integer from private.profiles), 1,
  'user sees only their profile');
select lives_ok(
  $$insert into private.garage_vehicles (user_id, year, make, model)
    values ('11111111-1111-1111-1111-111111111111', 2022, 'Honda', 'CR-V')$$,
  'user may create an owned garage row'
);
select throws_ok(
  $$insert into private.garage_vehicles (user_id, year, make, model)
    values ('22222222-2222-2222-2222-222222222222', 2022, 'Honda', 'CR-V')$$,
  '42501',
  null,
  'cross-owner insert is denied'
);
select is(
  (
    with changed as (
      update private.profiles
      set updated_at = now()
      where user_id = '22222222-2222-2222-2222-222222222222'
      returning 1
    )
    select count(*)::integer from changed
  ),
  0,
  'cross-owner update affects zero rows'
);
select is(
  (
    with changed as (
      update private.profiles
      set updated_at = now()
      where user_id = '11111111-1111-1111-1111-111111111111'
      returning 1
    )
    select count(*)::integer from changed
  ),
  1,
  'own update succeeds'
);
reset role;

set local role kyr_api_runtime;
select set_config('kyr.user_id', '22222222-2222-2222-2222-222222222222', true);
select throws_ok(
  $$select count(*) from private.profiles$$,
  '42501',
  null,
  'forged identity cannot overcome the runtime role table deny'
);
reset role;

select * from finish();
rollback;
~~~

- [ ] **Step 2b: Add executable credit, deletion-outbox, migration, and entitlement invariant tests.**

Create supabase/tests/database/004_foundation_invariants.test.sql:

~~~sql
begin;
create extension if not exists pgtap with schema extensions;
-- Transactional test-only grants; rollback removes them after role-switch assertions.
grant usage on schema extensions
  to kyr_user_function_owner, kyr_ops_function_owner, kyr_api_runtime;
set local search_path = extensions, public, pg_catalog;
select no_plan();

insert into auth.users (
  id, aud, role, email, encrypted_password, email_confirmed_at,
  raw_app_meta_data, raw_user_meta_data, created_at, updated_at
) values
  ('33333333-3333-3333-3333-333333333333', 'authenticated', 'authenticated',
    's1-three@example.invalid', '', now(), '{}'::jsonb, '{}'::jsonb, now(), now()),
  ('44444444-4444-4444-4444-444444444444', 'authenticated', 'authenticated',
    's1-four@example.invalid', '', now(), '{}'::jsonb, '{}'::jsonb, now(), now());

set local role kyr_ops_function_owner;
insert into private.profiles (user_id) values
  ('33333333-3333-3333-3333-333333333333'),
  ('44444444-4444-4444-4444-444444444444');
insert into private.garage_vehicles (id, user_id, year, make, model)
values (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '33333333-3333-3333-3333-333333333333',
  2022, 'Honda', 'CR-V'
);
insert into private.service_events (
  id, user_id, garage_vehicle_id, client_request_id, request_hash,
  service_label, performed_on, mileage
) values (
  'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
  '33333333-3333-3333-3333-333333333333',
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  'cccccccc-cccc-cccc-cccc-cccccccccccc',
  decode(repeat('11', 32), 'hex'),
  'Oil change', date '2026-07-16', 50000
);
select throws_ok(
  $$insert into private.stripe_webhook_events (
      event_id, event_type, stripe_created_at, payload_hash,
      processing_status, processed_at
    ) values (
      'evt_direct_complete', 'customer.subscription.updated', now(),
      decode(repeat('46', 32), 'hex'), 'completed', now()
    )$$,
  '23514',
  null,
  'a Stripe envelope cannot be inserted directly into a terminal state'
);
select lives_ok(
  $$insert into private.stripe_webhook_events (
      event_id, event_type, stripe_created_at, payload_hash
    ) values (
      'evt_foundation', 'customer.subscription.updated', now(),
      decode(repeat('47', 32), 'hex')
    )$$,
  'verified Stripe envelope enters the inbox as received'
);
select throws_ok(
  $$update private.stripe_webhook_events
    set processing_status = 'completed'
    where event_id = 'evt_foundation'$$,
  '23514',
  null,
  'completed Stripe inbox state requires a completion timestamp'
);
select lives_ok(
  $$update private.stripe_webhook_events
    set processing_status = 'processing',
        lease_until = statement_timestamp() + interval '1 minute',
        fencing_token = fencing_token + 1,
        attempt_count = attempt_count + 1
    where event_id = 'evt_foundation'$$,
  'Stripe inbox processing state owns a lease and fencing token'
);
select lives_ok(
  $$update private.stripe_webhook_events
    set processing_status = 'failed', lease_until = null,
        last_error_code = 'provider_unavailable'
    where event_id = 'evt_foundation'$$,
  'failed Stripe inbox state releases its lease for retry'
);
select throws_ok(
  $$update private.stripe_webhook_events
    set processing_status = 'completed', processed_at = now(),
        last_error_code = null
    where event_id = 'evt_foundation'$$,
  '23514',
  null,
  'failed Stripe inbox event cannot bypass fenced lease reacquisition'
);
select lives_ok(
  $$update private.stripe_webhook_events
    set processing_status = 'processing',
        lease_until = statement_timestamp() + interval '100 milliseconds',
        fencing_token = fencing_token + 1,
        attempt_count = attempt_count + 1
    where event_id = 'evt_foundation'$$,
  'Stripe inbox retry reacquires processing with a new fence and attempt'
);
select is(
  (select fencing_token from private.stripe_webhook_events
    where event_id = 'evt_foundation'),
  2::bigint,
  'Stripe inbox retry advances the fencing token'
);
select lives_ok(
  $$select pg_sleep(0.5)$$,
  'the retry lease is allowed to expire for stale-worker testing'
);
select throws_ok(
  $$update private.stripe_webhook_events
    set lease_until = statement_timestamp() + interval '1 minute'
    where event_id = 'evt_foundation'
      and processing_status = 'processing'
      and fencing_token = 2$$,
  '23514',
  null,
  'an expired Stripe worker cannot renew with the same fence'
);
select throws_ok(
  $$update private.stripe_webhook_events
    set processing_status = 'completed', processed_at = statement_timestamp(),
        lease_until = null, last_error_code = null
    where event_id = 'evt_foundation'
      and processing_status = 'processing'
      and fencing_token = 2$$,
  '23514',
  null,
  'an expired Stripe worker cannot complete with the same fence'
);
select lives_ok(
  $$update private.stripe_webhook_events
    set lease_until = statement_timestamp() + interval '1 minute',
        fencing_token = fencing_token + 1,
        attempt_count = attempt_count + 1
    where event_id = 'evt_foundation'
      and processing_status = 'processing'
      and fencing_token = 2$$,
  'an expired Stripe lease is reclaimed with a new fence and attempt'
);
select is(
  (select fencing_token from private.stripe_webhook_events
    where event_id = 'evt_foundation'),
  3::bigint,
  'Stripe inbox reclaim advances the fencing token again'
);
select is(
  (
    with stale_completion as (
      update private.stripe_webhook_events
      set processing_status = 'completed', processed_at = now(),
          lease_until = null, last_error_code = null
      where event_id = 'evt_foundation'
        and processing_status = 'processing'
        and fencing_token = 2
      returning 1
    )
    select count(*)::integer from stale_completion
  ),
  0,
  'the expired Stripe worker cannot complete after a fenced reclaim'
);
select is(
  (
    with current_completion as (
      update private.stripe_webhook_events
      set processing_status = 'completed', processed_at = now(),
          lease_until = null, last_error_code = null
      where event_id = 'evt_foundation'
        and processing_status = 'processing'
        and fencing_token = 3
      returning 1
    )
    select count(*)::integer from current_completion
  ),
  1,
  'the current fenced Stripe worker completes the event exactly once'
);
reset role;

set local role kyr_user_function_owner;
select set_config('kyr.user_id', '33333333-3333-3333-3333-333333333333', true);
select lives_ok(
  $$insert into private.credit_ledger (user_id, delta, reason, actor)
    values ('33333333-3333-3333-3333-333333333333', 3, 'initial_grant', 'system')$$,
  'one three-credit seed grant succeeds'
);
select throws_ok(
  $$insert into private.credit_ledger (user_id, delta, reason, actor)
    values ('33333333-3333-3333-3333-333333333333', 3, 'migration_grant', 'migration')$$,
  '23505',
  null,
  'a second initial-or-migration grant is impossible'
);
select set_config('kyr.user_id', '44444444-4444-4444-4444-444444444444', true);
select throws_ok(
  $$insert into private.credit_ledger (user_id, delta, reason, actor)
    values ('44444444-4444-4444-4444-444444444444', 2, 'initial_grant', 'system')$$,
  '23514',
  null,
  'seed grants must be exactly three credits'
);
select throws_ok(
  $$insert into private.credit_ledger (user_id, delta, reason, actor)
    values (
      '44444444-4444-4444-4444-444444444444',
      -1, 'service_consumption', 'service-command'
    )$$,
  '23514',
  null,
  'service consumption requires a service event'
);
select set_config('kyr.user_id', '33333333-3333-3333-3333-333333333333', true);
select lives_ok(
  $$insert into private.credit_ledger
      (user_id, delta, reason, service_event_id, actor)
    values (
      '33333333-3333-3333-3333-333333333333', -1, 'service_consumption',
      'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'service-command'
    )$$,
  'one service consumes one credit'
);
select throws_ok(
  $$update private.credit_ledger set delta = 3
    where user_id = '33333333-3333-3333-3333-333333333333'$$,
  '42501',
  null,
  'credit ledger is not mutable'
);
select throws_ok(
  $$delete from private.service_events
    where id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'$$,
  '42501',
  null,
  'ordinary service hard deletion is unavailable'
);
reset role;

set local role kyr_ops_function_owner;
insert into private.account_deletion_requests (
  deletion_request_id, user_id, deletion_identity_hmac,
  requested_at, scheduled_purge_at
) values (
  'dddddddd-dddd-dddd-dddd-dddddddddddd',
  '44444444-4444-4444-4444-444444444444',
  decode(repeat('22', 32), 'hex'),
  timestamptz '2026-07-16 12:00:00+00',
  timestamptz '2026-08-15 12:00:00+00'
);
update private.profiles
set account_status = 'deletion_pending',
    deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd',
    deletion_requested_at = timestamptz '2026-07-16 12:00:00+00',
    scheduled_purge_at = timestamptz '2026-08-15 12:00:00+00'
where user_id = '44444444-4444-4444-4444-444444444444';
set constraints account_deletion_requests_profile_fk, profiles_deletion_request_fk immediate;
set constraints account_deletion_requests_profile_fk, profiles_deletion_request_fk deferred;
select is(
  (
    select count(*)::integer
    from private.account_deletion_requests d
    join private.profiles p
      on (p.user_id, p.deletion_request_id, p.deletion_requested_at, p.scheduled_purge_at)
       = (d.user_id, d.deletion_request_id, d.requested_at, d.scheduled_purge_at)
    where d.deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
  ),
  1,
  'deletion request and profile are bound to the same user, request, and deadline'
);
select throws_ok(
  $$update private.account_deletion_requests
    set deletion_identity_hmac = decode(repeat('23', 32), 'hex')
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  '23514',
  null,
  'deletion identity cannot be rewritten after request creation'
);
select throws_ok(
  $$update private.account_deletion_requests
    set user_id = null
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  '23514',
  null,
  'deletion request user cannot be cleared by an ordinary ops update'
);
select throws_ok(
  $$update private.account_deletion_requests
    set canceled_at = scheduled_purge_at
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  '23514',
  null,
  'recovery cancellation is rejected at or after the purge deadline'
);
select throws_ok(
  $$update private.account_deletion_requests
    set completed_at = scheduled_purge_at - interval '1 second'
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  '23514',
  null,
  'purge completion is rejected before the 30-day deadline'
);
insert into private.account_deletion_jobs (
  deletion_request_id, operation, not_before
)
select
  'dddddddd-dddd-dddd-dddd-dddddddddddd',
  operation,
  now()
from unnest(array[
  'revoke_auth_sessions', 'cancel_stripe_at_period_end',
  'send_deletion_confirmation', 'write_purge_manifest',
  'purge_application_data', 'delete_auth_user'
]) as operation;
select is(
  (select count(*)::integer from private.account_deletion_jobs
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'),
  6,
  'all six independently retryable deletion effects coexist'
);
select throws_ok(
  $$insert into private.account_deletion_jobs
      (deletion_request_id, operation)
    values (
      'dddddddd-dddd-dddd-dddd-dddddddddddd',
      'revoke_auth_sessions'
    )$$,
  '23505',
  null,
  'one deletion request cannot duplicate an operation'
);
select ok(
  not exists (
    select 1 from information_schema.columns
    where table_schema = 'private' and table_name = 'account_deletion_jobs'
      and column_name in ('user_id', 'deletion_identity_hmac', 'stripe_customer_id')
  ),
  'deletion-job siblings cannot carry conflicting request identity'
);
select throws_ok(
  $$insert into private.account_deletion_requests (
      deletion_request_id, user_id, deletion_identity_hmac,
      requested_at, scheduled_purge_at
    ) values (
      'dcdcdcdc-dcdc-dcdc-dcdc-dcdcdcdcdcdc',
      '33333333-3333-3333-3333-333333333333',
      decode(repeat('22', 32), 'hex'),
      timestamptz '2026-07-16 12:00:00+00',
      timestamptz '2026-08-15 12:00:00+00'
    )$$,
  '23505',
  null,
  'one keyed deletion identity cannot be attached to a second request or user'
);
update private.account_deletion_jobs
set state = 'processing', lease_until = now() + interval '1 minute', attempt_count = 1
where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
  and operation = 'revoke_auth_sessions';
update private.account_deletion_jobs
set state = 'succeeded', lease_until = null, completed_at = now()
where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
  and operation = 'revoke_auth_sessions';
select is(
  (select count(*)::integer from private.account_deletion_jobs
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
      and state = 'pending'),
  5,
  'completing one deletion effect leaves five siblings independently pending'
);
select throws_ok(
  $$update private.account_deletion_requests
    set canceled_at = requested_at + interval '1 day', user_id = null
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  '23514',
  null,
  'recovery cannot detach the user while destructive jobs remain actionable'
);
update private.account_deletion_jobs
set state = 'canceled', lease_until = null, completed_at = now()
where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
  and operation not in ('revoke_auth_sessions', 'cancel_stripe_at_period_end')
  and state in ('pending', 'retryable');
select lives_ok(
  $$update private.account_deletion_requests
    set canceled_at = requested_at + interval '1 day',
        user_id = null
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  'recovery before the deadline detaches the user while retaining actionable Stripe intent'
);
update private.profiles
set account_status = 'active',
    deletion_request_id = null,
    deletion_requested_at = null,
    scheduled_purge_at = null
where user_id = '44444444-4444-4444-4444-444444444444';
set constraints account_deletion_requests_profile_fk, profiles_deletion_request_fk immediate;
set constraints account_deletion_requests_profile_fk, profiles_deletion_request_fk deferred;
select is(
  (select account_status from private.profiles
    where user_id = '44444444-4444-4444-4444-444444444444'),
  'active',
  '30-day recovery returns the profile to active'
);
select is(
  (
    select array[
      count(*) filter (where state = 'succeeded'),
      count(*) filter (where state = 'pending'),
      count(*) filter (where state = 'canceled')
    ]::bigint[]
    from private.account_deletion_jobs
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
  ),
  array[1, 1, 4]::bigint[],
  'recovery cancels destructive jobs but preserves completed revocation and pending Stripe cancellation'
);
select lives_ok(
  $$update private.account_deletion_requests
    set stripe_customer_id = 'cus_late_resolved'
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  'a late-resolved provider identity may attach after recovery while Stripe cancellation is actionable'
);
select is(
  (select stripe_customer_id from private.account_deletion_requests
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'),
  'cus_late_resolved',
  'recovery retains the minimum provider identity until Stripe cancellation is terminal'
);
select throws_ok(
  $$update private.account_deletion_requests
    set stripe_customer_id = null
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  '23514',
  null,
  'a canceled request cannot drop provider identity while Stripe cancellation is pending'
);
update private.account_deletion_jobs
set state = 'processing', lease_until = now() + interval '1 minute',
    attempt_count = attempt_count + 1, fencing_token = fencing_token + 1
where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
  and operation = 'cancel_stripe_at_period_end' and state = 'pending';
update private.account_deletion_jobs
set state = 'succeeded', lease_until = null, completed_at = now()
where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
  and operation = 'cancel_stripe_at_period_end' and state = 'processing';
select lives_ok(
  $$update private.account_deletion_requests
    set stripe_customer_id = null
    where deletion_request_id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  'provider identity clears only after the preserved cancellation job succeeds'
);
insert into private.account_deletion_requests (
  deletion_request_id, user_id, deletion_identity_hmac,
  requested_at, scheduled_purge_at
) values (
  'dadadada-dada-dada-dada-dadadadadada',
  '44444444-4444-4444-4444-444444444444',
  decode(repeat('22', 32), 'hex'),
  timestamptz '2026-07-20 12:00:00+00',
  timestamptz '2026-08-19 12:00:00+00'
);
update private.profiles
set account_status = 'deletion_pending',
    deletion_request_id = 'dadadada-dada-dada-dada-dadadadadada',
    deletion_requested_at = timestamptz '2026-07-20 12:00:00+00',
    scheduled_purge_at = timestamptz '2026-08-19 12:00:00+00'
where user_id = '44444444-4444-4444-4444-444444444444';
set constraints account_deletion_requests_profile_fk, profiles_deletion_request_fk immediate;
set constraints account_deletion_requests_profile_fk, profiles_deletion_request_fk deferred;
insert into private.account_deletion_jobs (
  deletion_request_id, operation, not_before
)
select
  'dadadada-dada-dada-dada-dadadadadada',
  operation,
  now()
from unnest(array[
  'revoke_auth_sessions', 'cancel_stripe_at_period_end',
  'send_deletion_confirmation', 'write_purge_manifest',
  'purge_application_data', 'delete_auth_user'
]) as operation;
select is(
  (select count(*)::integer from private.account_deletion_requests
    where deletion_identity_hmac = decode(repeat('22', 32), 'hex')),
  2,
  'a recovered account may submit a later deletion request with the same keyed identity'
);
select is(
  (select count(*)::integer from private.account_deletion_jobs
    where deletion_request_id = 'dadadada-dada-dada-dada-dadadadadada'),
  6,
  'a later deletion request creates its own six durable effects'
);

select lives_ok(
  $$insert into private.migration_records (
      id, source_entity_type, source_identity_hmac, source_key_hmac,
      checksum, migration_revision
    ) values (
      'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'account',
      decode(repeat('33', 32), 'hex'), decode(repeat('34', 32), 'hex'),
      decode(repeat('35', 32), 'hex'), 'legacy-v1'
    )$$,
  'an account migration manifest may exist before verified identity claim'
);
select throws_ok(
  $$insert into private.migration_records (
      source_entity_type, source_identity_hmac, source_key_hmac,
      claimed_user_id, checksum, migration_revision
    ) values (
      'account', decode(repeat('28', 32), 'hex'), decode(repeat('29', 32), 'hex'),
      '33333333-3333-3333-3333-333333333333',
      decode(repeat('27', 32), 'hex'), 'legacy-v2'
    )$$,
  '23514',
  null,
  'claimed migration manifest cannot exploit a null target CHECK hole'
);
select throws_ok(
  $$insert into private.migration_records (
      source_entity_type, source_identity_hmac, source_key_hmac,
      claimed_user_id, account_claim_id, target_id, checksum, migration_revision
    ) values (
      'expense', decode(repeat('33', 32), 'hex'), decode(repeat('30', 32), 'hex'),
      '44444444-4444-4444-4444-444444444444',
      'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
      'cdcdcdcd-cdcd-cdcd-cdcd-cdcdcdcdcdcd',
      decode(repeat('31', 32), 'hex'), 'legacy-v1'
    )$$,
  '23503',
  null,
  'child imports cannot bind to an unclaimed account manifest'
);
select lives_ok(
  $$update private.migration_records
    set claimed_user_id = '44444444-4444-4444-4444-444444444444',
        target_id = '44444444-4444-4444-4444-444444444444'
    where id = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'$$,
  'verified identity claim atomically binds the account manifest'
);
select throws_ok(
  $$update private.migration_records
    set claimed_user_id = null, target_id = null
    where id = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'$$,
  '23514',
  null,
  'verified migration claim cannot be unclaimed'
);
select throws_ok(
  $$update private.migration_records
    set claimed_user_id = '33333333-3333-3333-3333-333333333333',
        target_id = '33333333-3333-3333-3333-333333333333'
    where id = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'$$,
  '23514',
  null,
  'verified migration claim cannot be reassigned'
);
select throws_ok(
  $$insert into private.migration_records (
      source_entity_type, source_identity_hmac, source_key_hmac,
      claimed_user_id, target_id, checksum, migration_revision
    ) values (
      'account', decode(repeat('33', 32), 'hex'), decode(repeat('36', 32), 'hex'),
      '33333333-3333-3333-3333-333333333333',
      '33333333-3333-3333-3333-333333333333',
      decode(repeat('37', 32), 'hex'), 'legacy-v1'
    )$$,
  '23505',
  null,
  'one legacy account identity cannot be claimed by two users'
);
select throws_ok(
  $$insert into private.migration_records (
      source_entity_type, source_identity_hmac, source_key_hmac,
      claimed_user_id, target_id, checksum, migration_revision
    ) values (
      'account', decode(repeat('38', 32), 'hex'), decode(repeat('39', 32), 'hex'),
      '44444444-4444-4444-4444-444444444444',
      '44444444-4444-4444-4444-444444444444',
      decode(repeat('40', 32), 'hex'), 'legacy-v1'
    )$$,
  '23505',
  null,
  'one user cannot claim two legacy accounts in one revision'
);
insert into private.migration_records (
  source_entity_type, source_identity_hmac, source_key_hmac,
  claimed_user_id, account_claim_id, target_id, checksum, migration_revision
) values (
  'expense', decode(repeat('33', 32), 'hex'), decode(repeat('41', 32), 'hex'),
  '44444444-4444-4444-4444-444444444444',
  'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
  'ffffffff-ffff-ffff-ffff-ffffffffffff',
  decode(repeat('42', 32), 'hex'), 'legacy-v1'
);
select throws_ok(
  $$insert into private.migration_records (
      source_entity_type, source_identity_hmac, source_key_hmac,
      claimed_user_id, account_claim_id, target_id, checksum, migration_revision
    ) values (
      'expense', decode(repeat('33', 32), 'hex'), decode(repeat('43', 32), 'hex'),
      '44444444-4444-4444-4444-444444444444',
      'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
      'ffffffff-ffff-ffff-ffff-ffffffffffff',
      decode(repeat('44', 32), 'hex'), 'legacy-v1'
    )$$,
  '23505',
  null,
  'one imported target cannot map from two source records'
);
select throws_ok(
  $$insert into private.migration_records (
      source_entity_type, source_identity_hmac, source_key_hmac,
      claimed_user_id, account_claim_id, target_id, checksum, migration_revision
    ) values (
      'expense', decode(repeat('33', 32), 'hex'), decode(repeat('45', 32), 'hex'),
      '33333333-3333-3333-3333-333333333333',
      'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
      'abababab-abab-abab-abab-abababababab',
      decode(repeat('46', 32), 'hex'), 'legacy-v1'
    )$$,
  '23503',
  null,
  'a child row cannot attach an account identity to a different user'
);
select lives_ok(
  $$insert into private.entitlements (user_id)
    values ('44444444-4444-4444-4444-444444444444')$$,
  'default Free entitlement has a valid none-source shape'
);
select lives_ok(
  $$insert into private.entitlements (
      user_id, source, plan, subscription_status, admin_grant_expires_at
    ) values (
      '33333333-3333-3333-3333-333333333333',
      'admin', 'pro', 'admin_grant', now() + interval '1 day'
    )$$,
  'admin grant is valid only with an explicit expiry'
);
select throws_ok(
  $$update private.entitlements set plan = 'pro'
    where user_id = '44444444-4444-4444-4444-444444444444'$$,
  '23514',
  null,
  'source none can never project Pro'
);
select lives_ok(
  $$update private.entitlements set
      source = 'stripe',
      plan = 'pro',
      subscription_status = 'active',
      stripe_customer_id = 'cus_test',
      stripe_subscription_id = 'sub_test',
      stripe_product_id = 'prod_test',
      stripe_price_id = 'price_test',
      current_period_end = now() + interval '30 days',
      provider_observed_at = now()
    where user_id = '44444444-4444-4444-4444-444444444444'$$,
  'authoritative Stripe reconciliation may establish entitlement without a webhook event ID'
);
select is(
  (select latest_stripe_event_id from private.entitlements
    where user_id = '44444444-4444-4444-4444-444444444444'),
  null::text,
  'reconciled entitlement retains an optional event ID'
);
select lives_ok(
  $$update private.entitlements set cancel_at_period_end = true
    where user_id = '44444444-4444-4444-4444-444444444444'$$,
  'active Stripe entitlement may cancel at its known period end'
);
select throws_ok(
  $$update private.entitlements set
      plan = 'free', subscription_status = 'canceled'
    where user_id = '44444444-4444-4444-4444-444444444444'$$,
  '23514',
  null,
  'cancel-at-period-end cannot survive a terminal subscription state'
);
select throws_ok(
  $$update private.entitlements set
      plan = 'pro',
      subscription_status = 'canceled',
      cancel_at_period_end = false
    where user_id = '44444444-4444-4444-4444-444444444444'$$,
  '23514',
  null,
  'terminal Stripe status cannot project Pro'
);
reset role;

select lives_ok(
  $$delete from auth.users where id = '33333333-3333-3333-3333-333333333333'$$,
  'whole-account Auth cascade may remove service and ledger together'
);
set local role kyr_ops_function_owner;
select is(
  (
    (select count(*) from private.service_events
      where user_id = '33333333-3333-3333-3333-333333333333')
    +
    (select count(*) from private.credit_ledger
      where user_id = '33333333-3333-3333-3333-333333333333')
  )::integer,
  0,
  'final account cascade leaves no service or credit rows'
);
reset role;

select lives_ok(
  $$delete from auth.users where id = '44444444-4444-4444-4444-444444444444'$$,
  'Auth deletion may invoke the FK-driven request-user null transition'
);
set local role kyr_ops_function_owner;
select is(
  (select count(*)::integer from private.account_deletion_requests
    where deletion_request_id = 'dadadada-dada-dada-dada-dadadadadada'),
  1,
  'Auth deletion preserves the current durable deletion request'
);
select is(
  (select user_id from private.account_deletion_requests
    where deletion_request_id = 'dadadada-dada-dada-dada-dadadadadada'),
  null::uuid,
  'open deletion request retains only keyed identity after Auth deletion'
);
select is(
  (select count(*)::integer from private.account_deletion_jobs
    where deletion_request_id = 'dadadada-dada-dada-dada-dadadadadada'),
  6,
  'the current request jobs survive Auth deletion'
);
reset role;

select * from finish();
rollback;
~~~

- [ ] **Step 2c: Prove suites 003/004 leave no synthetic Auth or application state.**

Create `supabase/tests/database/005_linked_test_rollback.test.sql`:

```sql
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = extensions, public, pg_catalog;
select plan(3);

select is(
  (
    select count(*)::integer
    from auth.users
    where id in (
      '11111111-1111-1111-1111-111111111111',
      '22222222-2222-2222-2222-222222222222',
      '33333333-3333-3333-3333-333333333333',
      '44444444-4444-4444-4444-444444444444'
    )
  ),
  0,
  'prior pgTAP suites leave no synthetic auth.users rows'
);

select is(
  (
    select count(*)::integer
    from private.account_deletion_requests
    where deletion_request_id in (
      'dddddddd-dddd-dddd-dddd-dddddddddddd',
      'dadadada-dada-dada-dada-dadadadadada'
    )
  ),
  0,
  'prior pgTAP suites leave no synthetic deletion requests'
);

select is(
  (
    select count(*)::integer
    from private.credit_ledger
    where user_id in (
      '33333333-3333-3333-3333-333333333333',
      '44444444-4444-4444-4444-444444444444'
    )
  ),
  0,
  'prior pgTAP suites leave no synthetic credit rows'
);

select * from finish();
rollback;
```

Suite 005 is intentionally ordered after suites 003/004. It proves the prior files' known synthetic rows are absent before it performs its own rollback.

- [ ] **Step 3: Add and record a guaranteed RED database-source contract before writing Task 3 Step 3; do not substitute the paid remote project.**

Before the environment check, create empty `tests/deployment/__init__.py`, then create `tests/deployment/test_supabase_config.py`:

```python
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "supabase" / "config.toml"


class SupabaseConfigTests(unittest.TestCase):
    def test_clean_replay_matches_remote_postgres_major(self):
        config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["db"]["major_version"], 17)

    def test_private_schema_is_not_exposed_by_data_api(self):
        config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertNotIn("private", config["api"]["schemas"])
        self.assertNotIn("private", config["api"].get("extra_search_path", []))


if __name__ == "__main__":
    unittest.main()
```

Create `tests/deployment/test_foundation_migration_source.py`:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TABLES = (
    "profiles",
    "entitlements",
    "garage_vehicles",
    "service_events",
    "service_event_parts",
    "mileage_readings",
    "expense_events",
    "credit_ledger",
    "stripe_webhook_events",
    "app_sessions",
    "migration_records",
    "account_deletion_requests",
    "account_deletion_jobs",
    "purge_tombstones",
    "security_audit_events",
)


class FoundationMigrationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths = sorted((ROOT / "supabase" / "migrations").glob("*_tier2_foundation.sql"))
        if len(paths) != 1:
            raise AssertionError(f"expected one Tier-2 foundation migration, found {len(paths)}")
        cls.source = paths[0].read_text(encoding="utf-8").lower()

    def test_empty_stub_has_been_replaced_by_the_complete_schema(self):
        for table in EXPECTED_TABLES:
            with self.subTest(table=table):
                self.assertIn(f"create table private.{table}", self.source)

    def test_role_and_rls_contract_is_present(self):
        for fragment in (
            "create role kyr_api_runtime",
            "create role kyr_identity_worker_runtime",
            "enable row level security",
            "force row level security",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.source)


if __name__ == "__main__":
    unittest.main()
```

```powershell
python -m unittest tests.deployment.test_supabase_config tests.deployment.test_foundation_migration_source -v
docker --version
```

Expected before Task 3 Steps 2a-3: `test_foundation_migration_source` fails against the empty CLI-created migration regardless of the generated config defaults. Record that executable RED. On the current workstation Docker is command-not-found, so record pgTAP as environment-blocked, not as a test failure and never as a reason to use the paid project. If Docker is available on the execution machine, run `npx --yes supabase@2.109.1 db start` and `npx --yes supabase@2.109.1 test db`; the empty migration must also fail the pgTAP contracts before implementation.

- [ ] **Step 4: Run source-level checks that do not require PostgreSQL.**

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q _deploy_check.py tests
```

Expected after Task 3 Steps 2a-3: all Python tests pass. If Docker is available, rerun `npx --yes supabase@2.109.1 db start` and `npx --yes supabase@2.109.1 test db`; all five pgTAP files must pass. If Docker remains unavailable, CI in Task 9 is the first authoritative database GREEN and no remote schema action may precede it.

- [ ] **Step 5: Commit the Supabase source and tests with exact paths.**

First capture the real migration path:

```powershell
$migration = Get-ChildItem supabase/migrations/*_tier2_foundation.sql | Sort-Object Name -Descending | Select-Object -First 1
$migration.FullName
```

Then stage only:

```powershell
$paths = @(
  'supabase/config.toml',
  $migration.FullName,
  'supabase/tests/database/001_foundation_security.test.sql',
  'supabase/tests/database/002_foundation_constraints.test.sql',
  'supabase/tests/database/003_foundation_behavior.test.sql',
  'supabase/tests/database/004_foundation_invariants.test.sql',
  'supabase/tests/database/005_linked_test_rollback.test.sql',
  'tests/deployment/__init__.py',
  'tests/deployment/test_supabase_config.py',
  'tests/deployment/test_foundation_migration_source.py'
)
if (Test-Path 'supabase/.gitignore') { $paths += 'supabase/.gitignore' }
git add -- $paths
git diff --cached --check
git diff --cached --name-only
python _deploy_check.py
git commit -m "db(tier2): define private maintenance foundation"
git show --stat --oneline HEAD
```

Expected staged set: one config, one migration, five SQL test files, the deployment-test package marker, the Python config contract, and the inspected CLI-generated `supabase/.gitignore` only if it exists. No `.temp`, credentials, or export files.

---


### Task 5: Build the shared main-API foundation behind a disabled probe

**Files:**

- Create: `wrench_deploy/kyr_api/__init__.py`
- Create: `wrench_deploy/kyr_api/config.py`
- Create: `wrench_deploy/kyr_api/db.py`
- Create: `wrench_deploy/kyr_api/responses.py`
- Create: `wrench_deploy/kyr_api/security.py`
- Create: `wrench_deploy/api/foundation.py`
- Create: `wrench_deploy/.env.example`
- Create: `tests/unit/test_kyr_api_config.py`
- Create: `tests/unit/test_kyr_api_db.py`
- Create: `tests/unit/test_kyr_api_responses.py`
- Create: `tests/unit/test_kyr_api_security.py`
- Create: `tests/deployment/test_main_bundle_contract.py`
- Modify: `wrench_deploy/vercel.json`
- Read-only baseline dependency: `.vercelignore` (must already be tracked; Task 5 neither modifies nor stages it)

**Interfaces:**

- Consumes: Task 1's Python/runtime pins, Task 3's runtime role/function names, and the tracked root `.vercelignore` upload boundary.
- Produces: `MainSettings`, `load_main_settings(...)`, `connect(settings)`, `transaction(settings, user_id=None)`, `HTTPProblem`, `read_json(...)`, `write_json(...)`, `validate_mutation_origin(...)`, and the off-by-default `/api/foundation` probe.

- [ ] **Step 1: Write the failing configuration and bundle tests first.**

Create `tests/unit/test_kyr_api_config.py`:

```python
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "wrench_deploy"))

from kyr_api.config import ConfigError, load_main_settings  # noqa: E402


class MainConfigTests(unittest.TestCase):
    def test_rejects_every_auth_admin_secret_name(self):
        names = (
            "KYR_SUPABASE_SECRET_KEY",
            "SUPABASE_SECRET_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_SERVICE_KEY",
            "SB_SECRET_KEY",
        )
        for name in names:
            with self.subTest(name=name), self.assertRaises(ConfigError):
                load_main_settings({name: "must-not-be-here"}, require_database=False)

    def test_database_url_is_required_for_database_operations(self):
        with self.assertRaisesRegex(ConfigError, "KYR_DATABASE_URL"):
            load_main_settings({}, require_database=True)

    def test_foundation_probe_defaults_off(self):
        settings = load_main_settings({}, require_database=False)
        self.assertFalse(settings.foundation_enabled)

    def test_accepts_only_https_canonical_origin(self):
        invalid = (
            "http://knowyourride.net",
            "https://user@knowyourride.net",
            "https://knowyourride.net:444",
            "https://knowyourride.net?next=evil",
            "https://knowyourride.net#fragment",
        )
        for origin in invalid:
            with self.subTest(origin=origin), self.assertRaisesRegex(ConfigError, "KYR_CANONICAL_ORIGIN"):
                load_main_settings({"KYR_CANONICAL_ORIGIN": origin}, require_database=False)

    def test_rejects_admin_secret_value_even_under_an_unknown_name(self):
        secret_fixture = "sb_" + "secret_example"
        with self.assertRaises(ConfigError):
            load_main_settings({"ACCIDENTAL_KEY": secret_fixture}, require_database=False)

    def test_database_role_must_be_the_main_runtime(self):
        with self.assertRaisesRegex(ConfigError, "kyr_api_runtime"):
            load_main_settings(
                {
                    "KYR_DATABASE_URL": (
                        "postgresql://postgres:"
                        + "test-only"
                        + "@aws-0-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
                    ),
                    "KYR_SUPABASE_POOLER_HOST": "aws-0-us-west-2.pooler.supabase.com",
                },
                require_database=True,
            )

    def test_accepts_the_dedicated_main_database_role(self):
        database_url = (
            "postgresql://kyr_api_runtime.cajushswdwuthhakuevp:"
            + "test-only"
            + "@aws-0-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
        )
        settings = load_main_settings(
            {
                "KYR_DATABASE_URL": database_url,
                "KYR_SUPABASE_POOLER_HOST": "aws-0-us-west-2.pooler.supabase.com",
            },
            require_database=True,
        )
        self.assertEqual(settings.database_url, database_url)

    def test_rejects_a_passwordless_pooler_url(self):
        with self.assertRaises(ConfigError):
            load_main_settings(
                {
                    "KYR_DATABASE_URL": (
                        "postgresql://kyr_api_runtime.cajushswdwuthhakuevp"
                        "@aws-0-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
                    ),
                    "KYR_SUPABASE_POOLER_HOST": "aws-0-us-west-2.pooler.supabase.com",
                },
                require_database=True,
            )

    def test_rejects_unreviewed_pooler_host_or_connection_shape(self):
        prefix = (
            "postgresql://kyr_api_runtime.cajushswdwuthhakuevp:"
            + "test-only"
            + "@"
        )
        for database_url, pooler_host in (
            (
                prefix + "evil.invalid:6543/postgres?sslmode=require",
                "evil.invalid",
            ),
            (
                prefix + "aws-0-us-west-2.pooler.supabase.com:5432/postgres?sslmode=require",
                "aws-0-us-west-2.pooler.supabase.com",
            ),
            (
                prefix + "aws-0-us-west-2.pooler.supabase.com:6543/other?sslmode=require",
                "aws-0-us-west-2.pooler.supabase.com",
            ),
        ):
            with self.subTest(database_url=database_url), self.assertRaises(ConfigError):
                load_main_settings(
                    {
                        "KYR_DATABASE_URL": database_url,
                        "KYR_SUPABASE_POOLER_HOST": pooler_host,
                    },
                    require_database=True,
                )


if __name__ == "__main__":
    unittest.main()
```

Verify the upload boundary is tracked baseline state before writing its contract:

```powershell
$vercelIgnore = (git ls-files -- .vercelignore | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $vercelIgnore -ne '.vercelignore') {
  throw '.vercelignore must already be tracked before Task 5'
}
```

Expected: exactly `.vercelignore`. Do not modify or stage it in Task 5.

Create `tests/deployment/test_main_bundle_contract.py` (the package marker already exists from Task 4):

```python
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
VERCEL = ROOT / "wrench_deploy" / "vercel.json"
MAIN_ENV = ROOT / "wrench_deploy" / ".env.example"
VERCELIGNORE = ROOT / ".vercelignore"
FOUNDATION = ROOT / "wrench_deploy" / "api" / "foundation.py"
NESTED_VIN = ROOT / "wrench_deploy" / "api" / "vin" / "[vin].py"


class MainBundleContractTests(unittest.TestCase):
    def test_shared_package_is_explicitly_included(self):
        config = json.loads(VERCEL.read_text(encoding="utf-8"))
        functions = config["functions"]
        self.assertEqual(functions["api/**/*.py"]["includeFiles"], "kyr_api/**")
        self.assertIn("kyr_api/**", functions["api/guide.py"]["includeFiles"])
        self.assertEqual(functions["api/youtube.py"]["includeFiles"], "kyr_api/**")
        self.assertEqual(functions["api/identify-part.py"]["includeFiles"], "kyr_api/**")
        self.assertTrue(NESTED_VIN.exists(), "nested VIN route must remain in the deployment tree")

    def test_probe_imports_database_and_security_modules(self):
        source = FOUNDATION.read_text(encoding="utf-8")
        self.assertIn("from kyr_api import db as _db", source)
        self.assertIn("from kyr_api import security as _security", source)

    def test_main_environment_example_has_no_admin_credential(self):
        text = MAIN_ENV.read_text(encoding="utf-8")
        self.assertIn("KYR_SUPABASE_PUBLISHABLE_KEY=", text)
        self.assertIn("KYR_SUPABASE_POOLER_HOST=", text)
        self.assertNotIn("KYR_SUPABASE_ANON_KEY", text)
        for forbidden in (
            "KYR_SUPABASE_SECRET_KEY",
            "SUPABASE_SECRET_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_SERVICE_KEY",
            "SB_SECRET_KEY",
        ):
            self.assertNotIn(forbidden, text)

    def test_main_cli_upload_excludes_worker_root(self):
        self.assertTrue(
            VERCELIGNORE.is_file(),
            ".vercelignore is a required tracked baseline dependency",
        )
        text = VERCELIGNORE.read_text(encoding="utf-8")
        self.assertIn("/*", text)
        self.assertIn("!/wrench_deploy", text)
        self.assertNotIn("!/identity_admin_worker", text)


if __name__ == "__main__":
    unittest.main()
```

Before Step 2, also create `tests/unit/test_kyr_api_db.py`, `tests/unit/test_kyr_api_responses.py`, and `tests/unit/test_kyr_api_security.py` using the exact complete test bodies printed in Steps 10 and 11 below. Those later headings are placement anchors, not permission to defer the tests: create all five contracts before creating any `kyr_api` implementation file.

- [ ] **Step 2: Run all five contracts and confirm import/file failures before implementation.**

```powershell
python -m unittest tests.unit.test_kyr_api_config tests.unit.test_kyr_api_db tests.unit.test_kyr_api_responses tests.unit.test_kyr_api_security tests.deployment.test_main_bundle_contract -v
```

Expected: missing `kyr_api` modules and `.env.example`/function configuration failures. Record this RED result before Step 3.

- [ ] **Step 3: Create the shared package version and fail-closed configuration.**

Create `wrench_deploy/kyr_api/__init__.py`:

```python
FOUNDATION_VERSION = "s1-v1"
```

Create `wrench_deploy/kyr_api/config.py`:

```python
from dataclasses import dataclass
import os
from typing import Mapping
from urllib.parse import urlsplit


ADMIN_SECRET_NAMES = (
    "KYR_SUPABASE_SECRET_KEY",
    "SUPABASE_SECRET_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_SERVICE_KEY",
    "SB_SECRET_KEY",
)
ADMIN_SECRET_VALUE_PREFIX = "sb_" + "secret_"
PROJECT_REF = "cajushswdwuthhakuevp"
MAIN_POOLER_USERNAME = f"kyr_api_runtime.{PROJECT_REF}"
REVIEWED_POOLER_HOSTS = frozenset(
    {
        "aws-0-us-west-2.pooler.supabase.com",
        "aws-1-us-west-2.pooler.supabase.com",
    }
)


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class MainSettings:
    database_url: str | None
    pooler_host: str | None
    canonical_origin: str
    foundation_enabled: bool


def load_main_settings(
    source: Mapping[str, str] | None = None,
    *,
    require_database: bool = True,
) -> MainSettings:
    env = os.environ if source is None else source
    leaked = [name for name in ADMIN_SECRET_NAMES if env.get(name)]
    leaked_value = any(
        str(value).strip().lower().startswith(ADMIN_SECRET_VALUE_PREFIX)
        for value in env.values()
    )
    if leaked or leaked_value:
        raise ConfigError("Auth administration credentials are forbidden in the main API")

    database_url = (env.get("KYR_DATABASE_URL") or "").strip() or None
    pooler_host = (env.get("KYR_SUPABASE_POOLER_HOST") or "").strip().lower() or None
    if require_database and database_url is None:
        raise ConfigError("KYR_DATABASE_URL is required")
    if database_url is not None:
        database = urlsplit(database_url)
        try:
            database_port = database.port
        except ValueError as exc:
            raise ConfigError("KYR_DATABASE_URL has an invalid port") from exc
        if (
            pooler_host not in REVIEWED_POOLER_HOSTS
            or database.scheme not in ("postgres", "postgresql")
            or database.username != MAIN_POOLER_USERNAME
            or not database.password
            or database.hostname != pooler_host
            or database_port != 6543
            or database.path != "/postgres"
            or database.query != "sslmode=require"
            or database.fragment
        ):
            raise ConfigError(
                "KYR_DATABASE_URL must use the reviewed Supavisor transaction pooler "
                "and dedicated kyr_api_runtime project role"
            )

    canonical_origin = (env.get("KYR_CANONICAL_ORIGIN") or "https://knowyourride.net").strip()
    parsed = urlsplit(canonical_origin)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.netloc != parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ConfigError("KYR_CANONICAL_ORIGIN must be an HTTPS origin without a path")

    return MainSettings(
        database_url=database_url,
        pooler_host=pooler_host,
        canonical_origin=canonical_origin.rstrip("/"),
        foundation_enabled=env.get("KYR_TIER2_FOUNDATION_ENABLED") == "1",
    )
```

- [ ] **Step 4: Create the transaction helper with transaction-pooler-safe settings.**

Create `wrench_deploy/kyr_api/db.py`:

```python
from contextlib import contextmanager
from collections.abc import Iterator
from uuid import UUID

import psycopg

from .config import MainSettings


def connect(settings: MainSettings) -> psycopg.Connection:
    if settings.database_url is None:
        raise RuntimeError("database URL was not loaded")
    return psycopg.connect(
        settings.database_url,
        autocommit=False,
        connect_timeout=5,
        prepare_threshold=None,
    )


@contextmanager
def transaction(
    settings: MainSettings,
    *,
    user_id: UUID | None = None,
) -> Iterator[psycopg.Connection]:
    with connect(settings) as connection:
        if user_id is not None:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select set_config('kyr.user_id', %s, true)",
                    (str(user_id),),
                )
        yield connection
```

`prepare_threshold=None` is required for Supabase's transaction pooler: it prevents connection-bound prepared-statement state. The user context is transaction-local (`true`) and never persists into a pooled connection.

- [ ] **Step 5: Create bounded JSON response primitives.**

Create `wrench_deploy/kyr_api/responses.py`:

```python
import json
from typing import Any


MAX_JSON_BODY = 64 * 1024


class HTTPProblem(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def read_json(handler: Any, *, max_bytes: int = MAX_JSON_BODY) -> dict[str, Any]:
    content_type = (handler.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise HTTPProblem(415, "unsupported_media_type", "Expected application/json")

    raw_length = handler.headers.get("Content-Length")
    if raw_length is None:
        raise HTTPProblem(411, "length_required", "Content-Length is required")
    try:
        length = int(raw_length)
    except ValueError as exc:
        raise HTTPProblem(400, "invalid_content_length", "Invalid Content-Length") from exc
    if length < 0 or length > max_bytes:
        raise HTTPProblem(413, "body_too_large", "Request body is too large")

    raw = handler.rfile.read(length)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPProblem(400, "invalid_json", "Malformed JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPProblem(400, "invalid_json_shape", "JSON body must be an object")
    return payload


def write_json(handler: Any, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "private, no-store, max-age=0")
    handler.send_header("Pragma", "no-cache")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    handler.wfile.write(body)
```

- [ ] **Step 6: Create the canonical-origin primitive without wiring it into legacy endpoints.**

Create `wrench_deploy/kyr_api/security.py`:

```python
import hmac
from collections.abc import Mapping
from urllib.parse import urlsplit

from .responses import HTTPProblem


def _first_header_value(value: str) -> str:
    return value.split(",", 1)[0].strip()


def validate_mutation_origin(headers: Mapping[str, str], canonical_origin: str) -> None:
    expected = urlsplit(canonical_origin)
    origin = (headers.get("Origin") or "").rstrip("/")
    if not origin or not hmac.compare_digest(origin, canonical_origin):
        raise HTTPProblem(403, "origin_denied", "Request origin is not allowed")

    host = _first_header_value(headers.get("X-Forwarded-Host") or headers.get("Host") or "")
    proto = _first_header_value(headers.get("X-Forwarded-Proto") or "https")
    if host.lower() != expected.netloc.lower() or proto.lower() != "https":
        raise HTTPProblem(403, "host_denied", "Request host is not allowed")
```

- [ ] **Step 7: Add an off-by-default bundle probe.**

Create `wrench_deploy/api/foundation.py`:

```python
from http.server import BaseHTTPRequestHandler

from kyr_api import FOUNDATION_VERSION
from kyr_api.config import ConfigError, load_main_settings
from kyr_api import db as _db  # noqa: F401 -- forces Vercel to prove psycopg/package bundling
from kyr_api import security as _security  # noqa: F401 -- proves security primitive bundling
from kyr_api.responses import write_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            settings = load_main_settings(require_database=False)
        except ConfigError:
            return write_json(self, 500, {"ok": False, "error": "configuration_error"})
        if not settings.foundation_enabled:
            return write_json(self, 404, {"ok": False, "error": "not_found"})
        return write_json(self, 200, {"ok": True, "foundation": FOUNDATION_VERSION})
```

This endpoint has no database or user-data behavior. Production lacks the enable flag and therefore returns 404. It exists only to prove Vercel imports the shared package before legacy endpoints depend on it.

- [ ] **Step 8: Add a names-only main environment example.**

Create `wrench_deploy/.env.example`:

```dotenv
KYR_TIER2_FOUNDATION_ENABLED=0
KYR_CANONICAL_ORIGIN=https://knowyourride.net
KYR_DATABASE_URL=
KYR_SUPABASE_POOLER_HOST=
KYR_SUPABASE_URL=
KYR_SUPABASE_PUBLISHABLE_KEY=
```

The database URL is a secret because it contains the dedicated role password. The Supabase publishable key is not an administration credential, but it still belongs in managed configuration rather than source values.

- [ ] **Step 9: Configure explicit bundle inclusion.**

In `wrench_deploy/vercel.json`, preserve all current rewrites and headers. Change only the `functions` object to this shape:

```json
"functions": {
  "api/**/*.py": {
    "includeFiles": "kyr_api/**"
  },
  "api/guide.py": {
    "includeFiles": "{api/specs.json,kyr_api/**}",
    "maxDuration": 30
  },
  "api/youtube.py": {
    "includeFiles": "kyr_api/**",
    "maxDuration": 30
  },
  "api/identify-part.py": {
    "includeFiles": "kyr_api/**",
    "maxDuration": 30
  }
}
```

Do not change the current header policy in this task; CSP and full API header migration are separate ruled work.

- [ ] **Step 10: Confirm the transaction contract authored in Step 1 still has this exact body.**

Create an ignored local virtual environment and install the one new runtime import for workstation fast feedback before importing `kyr_api.db`:

```powershell
python -m venv .venv-tier2
& .\.venv-tier2\Scripts\python.exe -m pip install "psycopg[binary]==3.3.4"
& .\.venv-tier2\Scripts\python.exe -c "import psycopg; assert psycopg.__version__ == '3.3.4'"
```

CI still installs the complete exact runtime requirements under Python 3.12 and remains authoritative.

Create `tests/unit/test_kyr_api_db.py`:

```python
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "wrench_deploy"))

from kyr_api.config import MainSettings  # noqa: E402
from kyr_api.db import connect, transaction  # noqa: E402


SETTINGS = MainSettings(
    database_url="postgresql://example.invalid/db",
    pooler_host=None,
    canonical_origin="https://knowyourride.net",
    foundation_enabled=False,
)


class DatabaseHelperTests(unittest.TestCase):
    @patch("kyr_api.db.psycopg.connect")
    def test_disables_prepared_statements_for_transaction_pooling(self, mocked_connect):
        connect(SETTINGS)
        mocked_connect.assert_called_once_with(
            SETTINGS.database_url,
            autocommit=False,
            connect_timeout=5,
            prepare_threshold=None,
        )

    @patch("kyr_api.db.connect")
    def test_user_context_is_transaction_local(self, mocked_connect):
        connection = MagicMock()
        mocked_connect.return_value.__enter__.return_value = connection
        cursor = connection.cursor.return_value.__enter__.return_value
        user_id = UUID("11111111-1111-1111-1111-111111111111")

        with transaction(SETTINGS, user_id=user_id) as yielded:
            self.assertIs(yielded, connection)

        cursor.execute.assert_called_once_with(
            "select set_config('kyr.user_id', %s, true)",
            (str(user_id),),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 11: Confirm the response and security contracts authored in Step 1 still have these exact bodies.**

Create `tests/unit/test_kyr_api_responses.py`:

```python
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "wrench_deploy"))

from kyr_api.responses import HTTPProblem, read_json, write_json  # noqa: E402


class FakeHandler:
    def __init__(self, body=b"", headers=None):
        self.headers = headers or {}
        self.rfile = BytesIO(body)
        self.wfile = BytesIO()
        self.status = None
        self.sent_headers = {}

    def send_response(self, status):
        self.status = status

    def send_header(self, name, value):
        self.sent_headers[name] = value

    def end_headers(self):
        pass


class ResponseTests(unittest.TestCase):
    def test_rejects_oversized_body_before_read(self):
        handler = FakeHandler(
            b"{}",
            {"Content-Type": "application/json", "Content-Length": "70000"},
        )
        with self.assertRaises(HTTPProblem) as raised:
            read_json(handler)
        self.assertEqual(raised.exception.status, 413)
        self.assertEqual(handler.rfile.tell(), 0)

    def test_requires_json_object(self):
        raw = b"[]"
        handler = FakeHandler(raw, {"Content-Type": "application/json", "Content-Length": str(len(raw))})
        with self.assertRaises(HTTPProblem) as raised:
            read_json(handler)
        self.assertEqual(raised.exception.code, "invalid_json_shape")

    def test_private_response_is_no_store(self):
        handler = FakeHandler()
        write_json(handler, 200, {"ok": True})
        self.assertEqual(handler.status, 200)
        self.assertEqual(handler.sent_headers["Cache-Control"], "private, no-store, max-age=0")
        self.assertEqual(json.loads(handler.wfile.getvalue()), {"ok": True})


if __name__ == "__main__":
    unittest.main()
```

Create `tests/unit/test_kyr_api_security.py`:

```python
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "wrench_deploy"))

from kyr_api.responses import HTTPProblem  # noqa: E402
from kyr_api.security import validate_mutation_origin  # noqa: E402


class OriginTests(unittest.TestCase):
    def test_accepts_exact_production_origin_and_forwarded_host(self):
        validate_mutation_origin(
            {
                "Origin": "https://knowyourride.net",
                "X-Forwarded-Host": "knowyourride.net",
                "X-Forwarded-Proto": "https",
            },
            "https://knowyourride.net",
        )

    def test_rejects_similar_but_foreign_origin(self):
        with self.assertRaises(HTTPProblem) as raised:
            validate_mutation_origin(
                {
                    "Origin": "https://knowyourride.net.attacker.example",
                    "X-Forwarded-Host": "knowyourride.net",
                    "X-Forwarded-Proto": "https",
                },
                "https://knowyourride.net",
            )
        self.assertEqual(raised.exception.status, 403)

    def test_rejects_wrong_forwarded_host(self):
        with self.assertRaises(HTTPProblem):
            validate_mutation_origin(
                {
                    "Origin": "https://knowyourride.net",
                    "X-Forwarded-Host": "attacker.example",
                    "X-Forwarded-Proto": "https",
                },
                "https://knowyourride.net",
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 12: Run the complete Task 5 suite.**

```powershell
& .\.venv-tier2\Scripts\python.exe -m unittest tests.unit.test_kyr_api_config tests.unit.test_kyr_api_db tests.unit.test_kyr_api_responses tests.unit.test_kyr_api_security tests.deployment.test_main_bundle_contract -v
& .\.venv-tier2\Scripts\python.exe -m compileall -q wrench_deploy/api wrench_deploy/kyr_api
```

Expected: all tests pass and compileall is silent.

- [ ] **Step 13: Commit only Task 5 files.**

```powershell
git add -- wrench_deploy/kyr_api/__init__.py wrench_deploy/kyr_api/config.py wrench_deploy/kyr_api/db.py wrench_deploy/kyr_api/responses.py wrench_deploy/kyr_api/security.py wrench_deploy/api/foundation.py wrench_deploy/.env.example wrench_deploy/vercel.json tests/unit/test_kyr_api_config.py tests/unit/test_kyr_api_db.py tests/unit/test_kyr_api_responses.py tests/unit/test_kyr_api_security.py tests/deployment/test_main_bundle_contract.py
git diff --cached --check
git diff --cached --name-only
python _deploy_check.py
git commit -m "feat(tier2): add shared API foundation"
git show --stat --oneline HEAD
```

---

### Task 6: Create the disabled, separately deployable identity-admin worker skeleton

**Files:**

- Create: `identity_admin_worker/api/trigger.py`
- Create: `identity_admin_worker/kyr_identity_worker/__init__.py`
- Create: `identity_admin_worker/kyr_identity_worker/config.py`
- Create: `identity_admin_worker/.env.example`
- Create: `identity_admin_worker/.python-version`
- Create: `identity_admin_worker/vercel.json`
- Create: `tests/unit/test_identity_worker_config.py`
- Create: `tests/deployment/test_identity_worker_isolation.py`

**Interfaces:**

- Consumes: Python 3.12 and database role `kyr_identity_worker_runtime`.
- Produces: `WorkerSettings`, `load_worker_settings(...)`, a separate Vercel root, and a disabled POST handler that accepts no user-selected identity or job body.

- [ ] **Step 1: Write the failing isolation tests.**

Create `tests/deployment/test_identity_worker_isolation.py`:

```python
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "identity_admin_worker"


class IdentityWorkerIsolationTests(unittest.TestCase):
    def test_worker_has_its_own_vercel_root(self):
        config = json.loads((WORKER / "vercel.json").read_text(encoding="utf-8"))
        self.assertEqual(
            config["functions"]["api/trigger.py"]["includeFiles"],
            "kyr_identity_worker/**",
        )

    def test_worker_runtime_matches_main_runtime(self):
        self.assertEqual(
            (WORKER / ".python-version").read_text(encoding="utf-8").strip(),
            "3.12",
        )

    def test_only_worker_environment_example_names_admin_secret(self):
        worker_env = (WORKER / ".env.example").read_text(encoding="utf-8")
        main_env = (ROOT / "wrench_deploy" / ".env.example").read_text(encoding="utf-8")
        self.assertIn("KYR_SUPABASE_SECRET_KEY", worker_env)
        self.assertNotIn("KYR_SUPABASE_SECRET_KEY", main_env)

    def test_skeleton_accepts_no_user_identifier_contract(self):
        source = (WORKER / "api" / "trigger.py").read_text(encoding="utf-8")
        self.assertNotIn("user_id", source)
        self.assertNotIn("rfile.read", source)


if __name__ == "__main__":
    unittest.main()
```

Before Step 2, create `tests/unit/test_identity_worker_config.py` using the exact complete body printed in Step 6. The Step 6 heading is a placement anchor only; both worker contracts must exist before any worker implementation file.

- [ ] **Step 2: Run both contracts and confirm missing-file/import failures.**

```powershell
python -m unittest tests.unit.test_identity_worker_config tests.deployment.test_identity_worker_isolation -v
```

- [ ] **Step 3: Add the worker's strict configuration.**

Create `identity_admin_worker/kyr_identity_worker/__init__.py`:

```python
WORKER_FOUNDATION_VERSION = "s1-v1"
```

Create `identity_admin_worker/kyr_identity_worker/config.py`:

```python
from dataclasses import dataclass
import os
from typing import Mapping


PROJECT_REF = "cajushswdwuthhakuevp"
EXPECTED_SUPABASE_URL = f"https://{PROJECT_REF}.supabase.co"
WORKER_POOLER_USERNAME = f"kyr_identity_worker_runtime.{PROJECT_REF}"
REVIEWED_POOLER_HOSTS = frozenset(
    {
        "aws-0-us-west-2.pooler.supabase.com",
        "aws-1-us-west-2.pooler.supabase.com",
    }
)


class WorkerConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkerSettings:
    enabled: bool
    supabase_url: str | None
    supabase_secret_key: str | None
    database_url: str | None
    pooler_host: str | None
    trigger_secret: str | None


def load_worker_settings(source: Mapping[str, str] | None = None) -> WorkerSettings:
    env = os.environ if source is None else source
    enabled = env.get("KYR_IDENTITY_WORKER_ENABLED") == "1"
    settings = WorkerSettings(
        enabled=enabled,
        supabase_url=(env.get("KYR_SUPABASE_URL") or "").strip() or None,
        supabase_secret_key=(env.get("KYR_SUPABASE_SECRET_KEY") or "").strip() or None,
        database_url=(env.get("KYR_IDENTITY_WORKER_DATABASE_URL") or "").strip() or None,
        pooler_host=(env.get("KYR_SUPABASE_POOLER_HOST") or "").strip().lower() or None,
        trigger_secret=(env.get("KYR_IDENTITY_WORKER_TRIGGER_SECRET") or "").strip() or None,
    )
    if settings.supabase_url is not None and settings.supabase_url != EXPECTED_SUPABASE_URL:
        raise WorkerConfigError("KYR_SUPABASE_URL must be the approved KYR project origin")
    if enabled and not all(
        (
            settings.supabase_url,
            settings.supabase_secret_key,
            settings.database_url,
            settings.pooler_host,
            settings.trigger_secret,
        )
    ):
        raise WorkerConfigError("enabled worker requires all managed secrets")
    if settings.database_url is not None:
        from urllib.parse import urlsplit

        database = urlsplit(settings.database_url)
        try:
            database_port = database.port
        except ValueError as exc:
            raise WorkerConfigError("worker database URL has an invalid port") from exc
        if (
            settings.pooler_host not in REVIEWED_POOLER_HOSTS
            or database.scheme not in ("postgres", "postgresql")
            or database.username != WORKER_POOLER_USERNAME
            or not database.password
            or database.hostname != settings.pooler_host
            or database_port != 6543
            or database.path != "/postgres"
            or database.query != "sslmode=require"
            or database.fragment
        ):
            raise WorkerConfigError(
                "KYR_IDENTITY_WORKER_DATABASE_URL must use the reviewed Supavisor "
                "transaction pooler and kyr_identity_worker_runtime project role"
            )
    return settings
```

- [ ] **Step 4: Add a disabled handler that cannot perform or receive an admin operation.**

Create `identity_admin_worker/api/trigger.py`:

```python
import json
from http.server import BaseHTTPRequestHandler

from kyr_identity_worker.config import WorkerConfigError, load_worker_settings


def _send(handler, status, payload):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "private, no-store, max-age=0")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    handler.wfile.write(body)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            settings = load_worker_settings()
        except WorkerConfigError:
            return _send(self, 500, {"ok": False, "error": "configuration_error"})
        if not settings.enabled:
            return _send(self, 404, {"ok": False, "error": "not_found"})
        return _send(self, 503, {"ok": False, "error": "worker_not_implemented"})
```

The S1 handler does not read a body and therefore cannot accept a caller-selected identity. Actual job claiming and the two-item Auth allowlist belong to S6 and must be built from durable queue tests.

- [ ] **Step 5: Add the separate manifest and names-only environment example.**

Create `identity_admin_worker/vercel.json`:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": {
    "api/trigger.py": {
      "includeFiles": "kyr_identity_worker/**",
      "maxDuration": 30
    }
  }
}
```

Create `identity_admin_worker/.env.example`:

```dotenv
KYR_IDENTITY_WORKER_ENABLED=0
KYR_SUPABASE_URL=
KYR_SUPABASE_SECRET_KEY=
KYR_SUPABASE_POOLER_HOST=
KYR_IDENTITY_WORKER_DATABASE_URL=
KYR_IDENTITY_WORKER_TRIGGER_SECRET=
```

Create `identity_admin_worker/.python-version`:

```text
3.12
```

- [ ] **Step 6: Confirm the worker configuration contract authored in Step 1 still has this exact body, then run both contracts.**

Create `tests/unit/test_identity_worker_config.py`:

```python
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "identity_admin_worker"))

from kyr_identity_worker.config import WorkerConfigError, load_worker_settings  # noqa: E402


class WorkerConfigTests(unittest.TestCase):
    def test_worker_defaults_disabled_without_secrets(self):
        settings = load_worker_settings({})
        self.assertFalse(settings.enabled)
        self.assertIsNone(settings.supabase_secret_key)

    def test_enabled_worker_fails_closed_if_any_secret_is_missing(self):
        with self.assertRaises(WorkerConfigError):
            load_worker_settings({"KYR_IDENTITY_WORKER_ENABLED": "1"})

    def test_enabled_worker_accepts_complete_managed_configuration(self):
        database_url = (
            "postgresql://kyr_identity_worker_runtime.cajushswdwuthhakuevp:"
            + "test-only"
            + "@aws-0-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
        )
        settings = load_worker_settings(
            {
                "KYR_IDENTITY_WORKER_ENABLED": "1",
                "KYR_SUPABASE_URL": "https://cajushswdwuthhakuevp.supabase.co",
                "KYR_SUPABASE_SECRET_KEY": "test-only",
                "KYR_SUPABASE_POOLER_HOST": "aws-0-us-west-2.pooler.supabase.com",
                "KYR_IDENTITY_WORKER_DATABASE_URL": database_url,
                "KYR_IDENTITY_WORKER_TRIGGER_SECRET": "test-only",
            }
        )
        self.assertTrue(settings.enabled)

    def test_worker_rejects_any_other_supabase_origin(self):
        with self.assertRaisesRegex(WorkerConfigError, "approved KYR project origin"):
            load_worker_settings({"KYR_SUPABASE_URL": "https://attacker.invalid"})

    def test_worker_rejects_main_or_admin_database_role(self):
        with self.assertRaisesRegex(WorkerConfigError, "kyr_identity_worker_runtime"):
            load_worker_settings(
                {
                    "KYR_SUPABASE_POOLER_HOST": "aws-0-us-west-2.pooler.supabase.com",
                    "KYR_IDENTITY_WORKER_DATABASE_URL": (
                        "postgresql://kyr_api_runtime.cajushswdwuthhakuevp:"
                        + "test-only"
                        + "@aws-0-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
                    ),
                }
            )

    def test_worker_rejects_passwordless_pooler_url(self):
        with self.assertRaises(WorkerConfigError):
            load_worker_settings(
                {
                    "KYR_SUPABASE_POOLER_HOST": "aws-0-us-west-2.pooler.supabase.com",
                    "KYR_IDENTITY_WORKER_DATABASE_URL": (
                        "postgresql://kyr_identity_worker_runtime.cajushswdwuthhakuevp"
                        "@aws-0-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
                    ),
                }
            )


if __name__ == "__main__":
    unittest.main()
```

Run:

```powershell
python -m unittest tests.unit.test_identity_worker_config tests.deployment.test_identity_worker_isolation -v
python -m compileall -q identity_admin_worker
```

Expected: all tests pass; compileall is silent.

- [ ] **Step 7: Commit only the worker skeleton and tests.**

```powershell
git add -- identity_admin_worker/api/trigger.py identity_admin_worker/kyr_identity_worker/__init__.py identity_admin_worker/kyr_identity_worker/config.py identity_admin_worker/.env.example identity_admin_worker/.python-version identity_admin_worker/vercel.json tests/unit/test_identity_worker_config.py tests/deployment/test_identity_worker_isolation.py
git diff --cached --check
git diff --cached --name-only
python _deploy_check.py
git commit -m "security(auth): isolate identity worker skeleton"
git show --stat --oneline HEAD
```

---

### Task 7: Add additive Tier-2 CI with a clean PostgreSQL replay

**Files:**

- Create: `.github/workflows/tier2.yml`
- Create: `tests/deployment/test_tier2_workflow.py`

**Interfaces:**

- Consumes: all Task 1-6 Python contracts, the replayable migration, and five pgTAP suites.
- Produces: additive `tier2-foundation / python` and `tier2-foundation / database` checks; existing shipped-artifact workflow remains untouched.

- [ ] **Step 0: Write and run the failing workflow contract before creating YAML.**

Create `tests/deployment/test_tier2_workflow.py`:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "tier2.yml"


class Tier2WorkflowTests(unittest.TestCase):
    def test_runtime_and_clean_database_jobs_are_pinned(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        required = (
            'python-version: "3.12"',
            "version: 2.109.1",
            "supabase db start",
            "supabase test db",
            'python -m unittest discover -s tests -p "test_*.py" -v',
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_workflow_has_read_only_repository_permission(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", text)


if __name__ == "__main__":
    unittest.main()
```

```powershell
python -m unittest tests.deployment.test_tier2_workflow -v
```

Expected: FAIL because `.github/workflows/tier2.yml` does not exist.

- [ ] **Step 1: Add the workflow without editing `.github/workflows/verify.yml`.**

Create `.github/workflows/tier2.yml`:

```yaml
name: tier2-foundation

on:
  push:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  python:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: wrench_deploy/api/requirements.txt
      - name: Install exact runtime dependencies
        run: python -m pip install --requirement wrench_deploy/api/requirements.txt
      - name: Compile Tier-2 Python
        run: python -m compileall -q wrench_deploy/api wrench_deploy/kyr_api identity_admin_worker tests
      - name: Run Tier-2 unit and deployment-contract tests
        run: python -m unittest discover -s tests -p "test_*.py" -v

  database:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v2
        with:
          version: 2.109.1
      - name: Start clean PostgreSQL and replay migrations
        run: supabase db start
      - name: Run pgTAP database tests
        run: supabase test db
```

The database job uses GitHub's disposable Docker environment and no production credential. A clean replay is stronger than testing only the already-mutated paid project.

- [ ] **Step 2: Validate YAML structure locally without adding a YAML dependency.**

```powershell
Select-String -Path .github/workflows/tier2.yml -Pattern 'python-version: "3.12"|version: 2.109.1|supabase db start|supabase test db'
python -m unittest tests.deployment.test_tier2_workflow -v
git diff -- .github/workflows/verify.yml
```

Expected: all four required lines are present; existing verifier workflow has no diff.

- [ ] **Step 3: Run every locally available test.**

```powershell
& .\.venv-tier2\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
& .\.venv-tier2\Scripts\python.exe -m compileall -q wrench_deploy/api wrench_deploy/kyr_api identity_admin_worker tests
```

- [ ] **Step 4: Commit only the new workflow.**

```powershell
git add -- .github/workflows/tier2.yml tests/deployment/test_tier2_workflow.py
git diff --cached --check
git diff --cached --name-only
python _deploy_check.py
git commit -m "ci(tier2): test Python and clean database replay"
git show --stat --oneline HEAD
```

---

### Task 8: Run the complete local S1 gate and pause before every remote action

**Files:** none unless a test exposes a defect.

**Interfaces:**

- Consumes: focused commits and all local gates from Tasks 1-7.
- Produces: the immutable S1 local evidence report and explicit requests for CI/preview and later remote-schema approval.

- [ ] **Step 1: Run the S1 Python suite.**

```powershell
& .\.venv-tier2\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
& .\.venv-tier2\Scripts\python.exe -m compileall -q wrench_deploy/api wrench_deploy/kyr_api identity_admin_worker tests
```

Expected: all tests pass. Remember this is Python 3.14 fast feedback; Task 9 CI is the Python 3.12 authority.

- [ ] **Step 2: Run all existing Tier-1 gates unchanged.**

```powershell
python _verify_shipped.py --ci
python _verify_shipped.py
```

Expected: every pre-existing shipped-artifact check passes. If either fails, stop and identify whether S1 caused it; never weaken a check.

- [ ] **Step 3: Verify no secret value or private export entered the new tracked files.**

```powershell
git grep -n -I -E 'sk_live_|whsec_|sb_secret_|service_role.*=.+|postgres(ql)?://[^[:space:]]+:[^[:space:]]+@' -- . ':!docs/superpowers/plans/**'
git status --short
```

Expected: no credential-value match. Environment examples contain blank values only. Existing unrelated dirty/untracked files remain untouched.

- [ ] **Step 4: Verify commit contents since the approved design commit.**

```powershell
$storedBase = git config --local --get kyr.s1-base
if (-not $storedBase) { throw 'repo-local S1 base state is required' }
$env:KYR_S1_BASE = $storedBase.Trim()
git cat-file -e "$($env:KYR_S1_BASE)`^{commit}" 2>$null
if ($LASTEXITCODE -ne 0) { throw 'stored S1 base is not a commit' }
$mergeBase = (git merge-base $env:KYR_S1_BASE HEAD).Trim()
if ($mergeBase -ne $env:KYR_S1_BASE) { throw 'stored S1 base is stale or not an ancestor of HEAD' }
git log --oneline "$env:KYR_S1_BASE..HEAD"
git diff --stat "$env:KYR_S1_BASE..HEAD"
git diff --name-only "$env:KYR_S1_BASE..HEAD"
```

Expected: only S1 source, tests, migrations, manifests, and guards listed by Tasks 1-7.

- [ ] **Step 5: PAUSE and report exactly:**

- S1 commit list and changed paths;
- local unit/compile/verifier results;
- migration filename and table/assertion counts;
- confirmation that `cajushswdwuthhakuevp` was not mutated;
- confirmation that no Vercel project was linked, configured, or deployed;
- confirmation that no branch was pushed;
- the two requested approvals: feature-branch CI/preview and later remote schema application.

Do not continue on silence or an echoed report.

---

### Task 9: After explicit CI/preview approval, prove clean replay and Vercel packaging

**Files:** no tracked changes expected; `.vercel/` and Supabase `.temp/` remain ignored local state.

**Interfaces:**

- Consumes: explicit CI/preview approval, Task 7 workflows, the correct Vercel project metadata, and the pre-push production fingerprint.
- Produces: a green current-commit clean-replay run, Task 8's local legacy-verifier evidence, a non-production main preview, legacy-route smoke evidence, byte-identical production proof, and—only after a further approval—a disabled worker preview.

- [ ] **Step 0: Fail closed if the remote CLIs are not authenticated.**

```powershell
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI is not authenticated' }
$vercelIdentity = (& vercel whoami 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $vercelIdentity) {
  throw 'Vercel CLI is not authenticated'
}
$vercelIdentity
```

Expected: a valid GitHub session and a nonempty Vercel identity. These checks are read-only.

- [ ] **Step 0a: Before pushing, capture the actual production version, blob name, and byte hashes.**

```powershell
function Get-KyrProductionFingerprint {
  $stamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $dir = Join-Path $env:TEMP "kyr-s1-production-$stamp"
  New-Item -ItemType Directory -Path $dir -Force | Out-Null
  $indexPath = Join-Path $dir 'index.html'
  Invoke-WebRequest -UseBasicParsing -Uri "https://knowyourride.net/?cb=$stamp" -OutFile $indexPath
  $html = Get-Content -Raw -LiteralPath $indexPath
  $version = [regex]::Match(
    $html,
    '<meta\s+name="kyr-version"\s+content="([^"]+)"'
  ).Groups[1].Value
  $dataFile = [regex]::Match($html, '/(data\.[a-f0-9]+\.js)').Groups[1].Value
  if (-not $version -or -not $dataFile) { throw 'production version/blob reference missing' }
  $dataPath = Join-Path $dir $dataFile
  Invoke-WebRequest -UseBasicParsing -Uri "https://knowyourride.net/$dataFile?cb=$stamp" -OutFile $dataPath
  [ordered]@{
    version = $version
    data_file = $dataFile
    index_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $indexPath).Hash
    data_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $dataPath).Hash
  }
}

$baseline = Get-KyrProductionFingerprint
foreach ($entry in @(
  @('kyr.s1-production-version', $baseline.version),
  @('kyr.s1-production-data-file', $baseline.data_file),
  @('kyr.s1-production-index-sha256', $baseline.index_sha256),
  @('kyr.s1-production-data-sha256', $baseline.data_sha256)
)) {
  git config --local $entry[0] $entry[1]
  if ($LASTEXITCODE -ne 0) { throw "production baseline key $($entry[0]) was not persisted" }
}
$baseline
```

Expected: all four properties are non-empty. This baseline is captured before any branch push or preview deployment and lives only in repo-local git config, which cannot be committed.

- [ ] **Step 1: Push only the feature branch, never `main`.**

```powershell
$visibility = (gh repo view robertjoseph95/know-your-ride --json visibility --jq '.visibility' | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $visibility -ne 'PRIVATE') {
  throw "Tier-2 branch push requires a private repository; observed: $visibility"
}

$branch = (git config --local --get kyr.s1-branch | Out-String).Trim()
$current = (git branch --show-current).Trim()
if (-not $branch -or $branch -eq 'main' -or $branch -notlike 'codex/s1-*') {
  throw "stored S1 branch is missing or unsafe: $branch"
}
if ($current -ne $branch) {
  throw "current branch $current does not match stored S1 branch $branch"
}

git push --set-upstream origin "HEAD:refs/heads/$branch"
if ($LASTEXITCODE -ne 0) { throw "failed to push $branch" }
```

Expected: repository visibility is `PRIVATE`, and only the persisted dedicated S1 branch—currently `codex/s1-supabase-foundation`—is pushed; never `main` and never an Option-A implementation branch. This step checks privacy but does not authorize or change repository visibility.

- [ ] **Step 2: Wait for and watch the new workflow for the exact pushed commit.**

```powershell
$head = (git rev-parse HEAD).Trim()
$deadline = (Get-Date).AddMinutes(5)
$run = $null
do {
  $runs = gh run list --commit $head --event push --limit 20 --json databaseId,headSha,status,conclusion,workflowName | ConvertFrom-Json
  $run = $runs | Where-Object { $_.headSha -eq $head -and $_.workflowName -eq 'tier2-foundation' } | Select-Object -First 1
  if (-not $run -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 5 }
} while (-not $run -and (Get-Date) -lt $deadline)
if (-not $run) { throw "no tier2-foundation push run appeared for $head" }
$run | Format-List workflowName,databaseId,headSha,status,conclusion
gh run watch $run.databaseId --exit-status
if ($LASTEXITCODE -ne 0) { throw 'current-commit tier2-foundation run failed' }
```

Expected:

- `tier2-foundation / python` green on Python 3.12;
- `tier2-foundation / database` green after a clean PostgreSQL replay and pgTAP suite;
- Task 8's unchanged local shipped-surface verifier results remain the legacy evidence. A remote legacy-verifier run is not claimed because a feature-branch push does not trigger `.github/workflows/verify.yml`; a PR remains separately gated.

If the database job fails, use its logs and fix the migration/tests locally. Do not use the paid Supabase project as a shortcut around a failing clean replay.

- [ ] **Step 3: Deliberately link the correct main Vercel project only after confirming CLI syntax.**

```powershell
vercel link --help
vercel link --yes --project know-your-ride --scope robertjoseph95s-projects
vercel project inspect know-your-ride --scope robertjoseph95s-projects
```

Expected: linked project name `know-your-ride`, configured Root Directory `wrench_deploy`, production domain `knowyourride.net`. If any value differs, stop. Never reuse `project-sj4at`.

- [ ] **Step 4: Build a preview bundle and inspect shared-package inclusion.**

```powershell
vercel build
$bundled = Get-ChildItem -LiteralPath .vercel/output/functions -Recurse -File -ErrorAction Stop | Where-Object { $_.FullName -match 'kyr_api' }
$bundled | Select-Object -ExpandProperty FullName
if (-not $bundled) { throw 'kyr_api was not found in Vercel function output' }
```

Expected: `kyr_api` files appear in function output. Inspect the foundation function bundle specifically; if only unrelated output includes the package, stop.

- [ ] **Step 5: Create a non-production preview with the probe enabled only for that deployment.**

```powershell
$preview = (vercel deploy --prebuilt --env KYR_TIER2_FOUNDATION_ENABLED=1 | Select-Object -Last 1).Trim()
if ($preview -notmatch '^https://') { throw 'preview URL was not captured' }
git config --local kyr.s1-main-preview $preview
if ($LASTEXITCODE -ne 0) { throw 'preview URL was not persisted to local git config' }
$preview
vercel curl /api/foundation --deployment $preview
```

Expected response: `{"ok":true,"foundation":"s1-v1"}`. The command must not contain `--prod`.

- [ ] **Step 5a: Exercise every one of the 13 pre-S1 Python functions without entering a paid, external-fetch, or write path.**

```powershell
$preview = (git config --local --get kyr.s1-main-preview | Out-String).Trim()
if ($preview -notmatch '^https://') { throw 'stored preview URL is invalid' }

$cases = @(
  [pscustomobject]@{ name='auth';                path='/api/auth';                       method='GET';  data=$null; json=$false; status=400; pattern='Use POST\.' },
  [pscustomobject]@{ name='expenses';            path='/api/expenses';                   method='GET';  data=$null; json=$false; status=501; pattern="Unsupported method \('GET'\)" },
  [pscustomobject]@{ name='garage';              path='/api/garage';                     method='GET';  data=$null; json=$false; status=501; pattern="Unsupported method \('GET'\)" },
  [pscustomobject]@{ name='guide';               path='/api/guide';                      method='GET';  data=$null; json=$false; status=200; pattern='"pro_required"\s*:\s*true' },
  [pscustomobject]@{ name='identify-part';       path='/api/identify-part';              method='GET';  data=$null; json=$false; status=501; pattern="Unsupported method \('GET'\)" },
  [pscustomobject]@{ name='promo';               path='/api/promo';                      method='GET';  data=$null; json=$false; status=501; pattern="Unsupported method \('GET'\)" },
  [pscustomobject]@{ name='recalls';             path='/api/recalls';                    method='GET';  data=$null; json=$false; status=400; pattern='make, model and year are required' },
  [pscustomobject]@{ name='service-log';         path='/api/service-log';                method='GET';  data=$null; json=$false; status=501; pattern="Unsupported method \('GET'\)" },
  [pscustomobject]@{ name='subscribe';           path='/api/subscribe';                  method='POST'; data=$null; json=$false; status=501; pattern="Unsupported method \('POST'\)" },
  [pscustomobject]@{ name='verify-subscription'; path='/api/verify-subscription';         method='GET';  data=$null; json=$false; status=400; pattern='email parameter required' },
  [pscustomobject]@{ name='vin';                 path='/api/vin/INVALID';                 method='GET';  data=$null; json=$false; status=400; pattern='VIN must be 17 characters' },
  [pscustomobject]@{ name='webhook';             path='/api/webhook';                    method='GET';  data=$null; json=$false; status=501; pattern="Unsupported method \('GET'\)" },
  [pscustomobject]@{ name='youtube';             path='/api/youtube';                    method='GET';  data=$null; json=$false; status=200; pattern='"pro_required"\s*:\s*true' }
)

$smokeRoot = Join-Path $env:TEMP ("kyr-s1-function-smoke-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $smokeRoot -Force | Out-Null
try {
  $results = foreach ($case in $cases) {
    $bodyPath = Join-Path $smokeRoot "$($case.name).body"
    $curlArgs = @(
      $case.path, '--deployment', $preview, '--',
      '--request', $case.method, '--silent', '--show-error',
      '--output', $bodyPath, '--write-out', '%{http_code}'
    )
    if ($case.json) { $curlArgs += @('--header', 'Content-Type: application/json') }
    if ($null -ne $case.data) { $curlArgs += @('--data', $case.data) }

    $rawStatus = (& vercel curl @curlArgs 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "$($case.name) invocation failed: $rawStatus" }
    $statusMatch = [regex]::Match($rawStatus, '(\d{3})\s*$')
    if (-not $statusMatch.Success) {
      throw "$($case.name) returned no parseable HTTP status: $rawStatus"
    }
    $actualStatus = [int]$statusMatch.Groups[1].Value
    $body = if (Test-Path $bodyPath) { Get-Content -Raw -LiteralPath $bodyPath } else { '' }
    if ($actualStatus -ne $case.status) {
      throw "$($case.name) expected $($case.status), received $actualStatus; body=$body"
    }
    if (-not [regex]::IsMatch($body, $case.pattern)) {
      throw "$($case.name) omitted expected response contract: $($case.pattern)"
    }
    [pscustomobject]@{ function=$case.name; method=$case.method; status=$actualStatus }
  }
  if (@($results).Count -ne 13) { throw 'not all 13 legacy Python functions were exercised' }
  $results | Format-Table -AutoSize
} finally {
  $resolvedSmokeRoot = [IO.Path]::GetFullPath($smokeRoot)
  $resolvedTempRoot = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
  if (-not $resolvedSmokeRoot.StartsWith($resolvedTempRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "refusing to remove smoke directory outside TEMP: $resolvedSmokeRoot"
  }
  Remove-Item -LiteralPath $smokeRoot -Recurse -Force -ErrorAction SilentlyContinue
}

$logs = (& vercel logs $preview --since 10m --json 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'preview logs could not be inspected' }
if ($logs -match 'ModuleNotFoundError|ImportError|No module named|Traceback') {
  throw 'preview logs contain a Python import/runtime failure'
}
```

Expected: all 13 named functions return the exact safe contract above. Seven single-method handlers deliberately receive their unsupported method and must return BaseHTTPRequestHandler's exact `Unsupported method ('GET'|'POST')` 501 text; this proves module import/dispatch without depending on Redis or Stripe configuration. No request sends authorization, cookies, a real email, a promo code, a valid VIN, a Stripe plan/signature, or a service payload. Any 404, unexpected status, non-matching 501 body, import traceback, external provider call, or state mutation stops S1. `/api/foundation` in Step 5 separately proves that `kyr_api` and psycopg import in the new fourteenth function.

- [ ] **Step 6: Prove the production site was not changed.**

```powershell
function Get-KyrProductionFingerprint {
  $stamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $dir = Join-Path $env:TEMP "kyr-s1-production-$stamp"
  New-Item -ItemType Directory -Path $dir -Force | Out-Null
  $indexPath = Join-Path $dir 'index.html'
  Invoke-WebRequest -UseBasicParsing -Uri "https://knowyourride.net/?cb=$stamp" -OutFile $indexPath
  $html = Get-Content -Raw -LiteralPath $indexPath
  $version = [regex]::Match(
    $html,
    '<meta\s+name="kyr-version"\s+content="([^"]+)"'
  ).Groups[1].Value
  $dataFile = [regex]::Match($html, '/(data\.[a-f0-9]+\.js)').Groups[1].Value
  if (-not $version -or -not $dataFile) { throw 'production version/blob reference missing' }
  $dataPath = Join-Path $dir $dataFile
  Invoke-WebRequest -UseBasicParsing -Uri "https://knowyourride.net/$dataFile?cb=$stamp" -OutFile $dataPath
  [ordered]@{
    version = $version
    data_file = $dataFile
    index_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $indexPath).Hash
    data_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $dataPath).Hash
  }
}
$before = [pscustomobject]@{
  version = git config --local --get kyr.s1-production-version
  data_file = git config --local --get kyr.s1-production-data-file
  index_sha256 = git config --local --get kyr.s1-production-index-sha256
  data_sha256 = git config --local --get kyr.s1-production-data-sha256
}
if (@($before.version, $before.data_file, $before.index_sha256, $before.data_sha256) | Where-Object { -not $_ }) {
  throw 'pre-push production baseline is missing from local git config'
}
$after = Get-KyrProductionFingerprint
foreach ($property in 'version','data_file','index_sha256','data_sha256') {
  if ($before.$property -ne $after.$property) {
    throw "production changed at ${property}: before=$($before.$property) after=$($after.$property)"
  }
}
$after
```

Expected: version, exact `data.<hash>.js` filename, index SHA-256, and blob SHA-256 all remain byte-for-byte unchanged.

- [ ] **Step 7: PAUSE before creating the separate worker Vercel project.**

Report main preview URL, bundle evidence, production-unchanged evidence, and the green CI run links. Ask for explicit authorization to create `kyr-identity-admin-worker` as a separate Vercel project. Do not create it yet.

- [ ] **Step 8: Only after that separate approval, discover the current project-add command and create/link the worker project.**

```powershell
vercel project --help
vercel project add --help
```

Use the confirmed current syntax to create `kyr-identity-admin-worker` under scope `robertjoseph95s-projects`. Then:

```powershell
Push-Location identity_admin_worker
vercel link --yes --project kyr-identity-admin-worker --scope robertjoseph95s-projects
$workerPreview = (vercel deploy | Select-Object -Last 1).Trim()
$workerPreview
vercel curl /api/trigger --deployment $workerPreview -- --request POST
Pop-Location
```

Expected: worker preview responds 404 because `KYR_IDENTITY_WORKER_ENABLED` is absent. Do not add the Supabase secret/service credential in S1.

- [ ] **Step 9: Inspect environment-variable names, never values.**

For each linked project, run `vercel env ls` from its root. Expected:

- main project does not list `KYR_SUPABASE_SECRET_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_SERVICE_KEY`, or `SB_SECRET_KEY`;
- worker project has no Auth administration credential yet;
- no environment variable was added or removed in S1.

---

### Task 10: After separate remote-schema approval, apply the clean migration and close S1

**Files:** no migration edit is allowed during remote application; any defect returns to Task 3/4 and a new clean replay.

**Interfaces:**

- Consumes: separate remote-schema approval, green Task 9 CI/preview evidence, and the exact committed migration dry run.
- Produces: one applied empty foundation migration, linked pgTAP/advisor/provider-setting evidence, and the fixed schema/role contracts that S2 may plan against.

- [ ] **Step 1: Reconfirm the target immediately before mutation.**

Target must be:

```text
project ref: cajushswdwuthhakuevp
name: know-your-ride
region: us-west-2
PostgreSQL: 17
status: ACTIVE_HEALTHY
```

If any value differs or the schema is no longer empty/unconnected as expected, stop and reconcile.

- [ ] **Step 2: Inspect CLI link/push help; do not expose a database password in a command or transcript.**

```powershell
npx --yes supabase@2.109.1 link --help
npx --yes supabase@2.109.1 db push --help
npx --yes supabase@2.109.1 test db --help
```

If CLI authentication requires entering or printing a secret in an observable command, stop and use the connected Supabase migration operation instead. Never paste a database password into chat, source, shell history, or a plan report.

- [ ] **Step 3: Link, dry-run, then apply exactly the committed migration.**

```powershell
npx --yes supabase@2.109.1 link --project-ref cajushswdwuthhakuevp
npx --yes supabase@2.109.1 db push --linked --dry-run
```

Expected dry run: exactly one `*_tier2_foundation.sql` migration. If anything else appears, stop.

After the user has approved this exact dry-run output:

The linked pgTAP run deliberately performs transient SQL writes on the paid project. Suites 003 and 004 insert four synthetic `@example.invalid` rows directly into `auth.users` plus related private rows. They do not use the Auth API, send email, call a provider, or represent real users. The [current Supabase CLI reference](https://supabase.com/docs/reference/cli/supabase-projects-list) states that each test is transaction-wrapped and individually rolled back; these files also end in `ROLLBACK`, and suite 005 runs afterward to prove the known Auth, deletion-request, and credit fixtures are absent. Approval of the command below explicitly includes those rollback-only writes.

```powershell
npx --yes supabase@2.109.1 db push --linked
npx --yes supabase@2.109.1 test db --linked
```

Expected: migration applied once; all five pgTAP suites pass, including suite 005's post-suite rollback proof. No synthetic Auth or application row persists after the command.

- [ ] **Step 4: Run Supabase security and performance advisors through the connected Supabase tooling.**

Expected: no security error and no unexplained warning. Record every remaining notice verbatim with an explicit ruling; do not suppress it by weakening RLS or grants.

- [ ] **Step 5: Verify the remote contract read-only.**

Report:

- 15 private tables;
- RLS enabled and forced on all 15;
- no `anon`, `authenticated`, `PUBLIC`, or `kyr_api_runtime` table grant;
- `kyr_api_runtime` can execute only `private.foundation_health()` from S1;
- `kyr_identity_worker_runtime` has no table privilege and no executable S1 function;
- both function owners are `NOLOGIN`, `NOINHERIT`, non-superuser, and `NOBYPASSRLS`;
- both runtime roles are `LOGIN PASSWORD NULL` and therefore cannot password-authenticate in S1;
- zero application profiles, garage vehicles, service events, and entitlements;
- no Auth administration credential was copied or distributed into source, bundles, the main Vercel environment, logs, shell history, or reports; S1 makes no claim about provider-managed key existence.

Open the hosted Data API settings at `https://supabase.com/dashboard/project/cajushswdwuthhakuevp/integrations/data_api/settings` and record the exposed-schema list. Assert that `private` is absent. The local `supabase/config.toml` test is necessary but is not evidence of this provider-side setting; a mismatch stops S1 before any API connection is configured.

- [ ] **Step 6: Run final repository gates and produce the S1 close report.**

```powershell
& .\.venv-tier2\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
python _verify_shipped.py --ci
python _verify_shipped.py
git status --short
$storedBase = git config --local --get kyr.s1-base
if (-not $storedBase) { throw 'repo-local S1 base state is required' }
$env:KYR_S1_BASE = $storedBase.Trim()
git cat-file -e "$($env:KYR_S1_BASE)`^{commit}" 2>$null
if ($LASTEXITCODE -ne 0) { throw 'stored S1 base is not a commit' }
$mergeBase = (git merge-base $env:KYR_S1_BASE HEAD).Trim()
if ($mergeBase -ne $env:KYR_S1_BASE) { throw 'stored S1 base is stale or not an ancestor of HEAD' }
git log --oneline "$env:KYR_S1_BASE..HEAD"
```

The close report must include CI run links, preview URLs, remote table/advisor evidence, the exact commit list, confirmation that production traffic and production environment remained unchanged, and the statement: **S2 is not authorized by S1 completion.**

---

## Rollback and recovery

Before the remote schema gate, rollback means reverting the focused feature-branch commits; no provider state exists.

After a preview deployment, rollback means deleting/ignoring the preview or disabling its one-deployment probe flag. Production is untouched.

After the remote schema migration, do not write an automatic destructive down migration. The schema contains no user rows and is disconnected from production; if the migration is defective, stop S2, preserve evidence, and create a separately reviewed corrective migration. Dropping roles/schema remotely requires explicit destructive approval.

## S1 handoff contract for S2 planning

The S2 plan may rely only on these S1 outputs after they are proven:

- Python 3.12 and exact dependency pins;
- `wrench_deploy/kyr_api` import and Vercel bundle path;
- environment names and main/worker project isolation;
- the committed private table/role/RLS names;
- the transaction-local `kyr.user_id` convention;
- the absence of direct table grants for the runtime role;
- the deliberate `LOGIN PASSWORD NULL` state for both runtime roles;
- clean-replay and advisor results.

S2 may not infer a session/JWT/cookie API from the foundation probe. Those contracts must be designed and tested explicitly in the S2 plan. S2 must also begin with a separately approved credential-lifecycle task: generate distinct high-entropy main/worker role passwords without printing them, install each pooled URL only in the correct Vercel project, prove cross-project isolation and the first authenticated connection, and define rotation, incident revocation, final retirement, and rollback to `PASSWORD NULL`. No role password may enter a migration, source file, transcript, log, or report.

---

## Self-review

**Design coverage:** S1 creates every approved foundation table, the five-role split between table ownership, user commands, operations, the main runtime, and the identity-worker runtime, forced RLS, shared API primitives, transaction-pooler configuration, a separate worker root, tests, CI, and export guards. It routes no production traffic and migrates no user.

**Security coverage:** Browser roles and both runtime logins have no table grants. Both runtime logins remain `PASSWORD NULL` throughout S1. The user and operational function owners are `NOLOGIN`/`NOINHERIT`/`NOBYPASSRLS` with table-specific ACLs; user-owned policies depend on a transaction-local immutable UUID. Main configuration fails closed if an Auth administration credential is injected. The worker skeleton cannot accept an identity or execute an Auth operation.

**Concurrency/data coverage:** Composite owner foreign keys, owner-scoped request UUIDs, request hashes, one-credit-per-service uniqueness, webhook/deletion lease fields, fencing tokens, integer cents, archive consistency, and required indexes exist before command functions are added.

**Current-code safety:** Existing auth, billing, garage, service, expense, guide, YouTube, and scanner behavior remains untouched. The probe is off by default. Existing shipped-artifact CI is additive and unmodified.

**External-state coverage:** Feature-branch push, preview deployment, worker-project creation, and remote Supabase schema application each have an explicit PAUSE. There is no `--prod`, provider cancellation, `main` push, or user migration.

**Placeholder scan:** There are no placeholder markers, ellipses, invented migration timestamps, or unspecified source files. The CLI creates the timestamp; the plan captures and stages the returned path.

**Type/name consistency:** `user_id` is UUID; owned `garage_vehicle_id` is UUID; `public_vehicle_id` is a positive bigint reference; money is integer cents; HMAC/checksum values are 32-byte `bytea`; timestamps use `timestamptz`; `kyr.user_id` is transaction-local.

**Operational caveat surfaced:** The workstation lacks Docker and Python 3.12. Local Python 3.14 runs are non-authoritative; the GitHub clean-replay jobs are required before the remote schema gate.
