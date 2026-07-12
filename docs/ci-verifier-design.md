# CI Verifier — design (doc only, pre-implementation)

**Goal.** Turn `docs/shipped-surfaces-ledger.md` into executable, standing enforcement: every
ledger invariant runs as a test over the **built, tracked artifacts**, locally before every
deploy and in GitHub Actions on every push/PR. This is the audit's Phase-1 "regression
harness" (P2-13) scoped to the integrity surfaces first.

## 1. What runs — one verifier, a check registry

A single stdlib-only script, **`_verify_shipped.py`** (repo root, tracked — same style as
`_deploy_check.py`: no pip deps, plain prints, exit codes). Internally: a registry of small
check functions, each declaring:

```
{id: "S1.1-ver0-shell", surface: "blob", tier: FAIL|WARN, venue: CI|DB}
```

- **CI-venue checks** read only tracked files: parse the `data.<hash>.js` JSON once, share the
  parsed object across all blob checks; string/regex scans over both HTML files, the 3,540
  vehicle pages, sitemap/robots, `specs.json`. Every [CI] invariant in the ledger maps 1:1 to
  a check. Estimated runtime: a few seconds (one 13 MB JSON parse + streamed grep of ~3,600
  small files).
- **DB-venue checks** additionally open `wrench_vehicles.db` (read-only URI) and run:
  regeneration equivalence for `specs.json` (run `_gen_guide_specs.py` to a temp path,
  byte-compare), `_assert_gate_sources`, count reconciliation, and — once a `--check` mode
  exists — blob↔DB equivalence.

CLI: `python _verify_shipped.py` (auto-detects the DB: present → full suite; absent → CI
subset with a printed notice). `--ci` forces the subset; `--json` for machine output later.

## 2. When it runs — the split, stated honestly

| Venue | Trigger | Can reach | Cannot reach |
|---|---|---|---|
| **Workstation (full suite)** | Deploy ritual step, right after `_deploy_sync_specs.py` and before `git add`; optionally rerun by the `git_guard` hook | Everything: tracked artifacts + the canonical DB (315 MB, gitignored) | — |
| **GitHub Actions (CI subset)** | `push` + `pull_request` on `main` (`.github/workflows/verify.yml`: checkout → setup-python → `python _verify_shipped.py --ci`) | All tracked artifacts — which is every shipped surface, since the blob, both HTMLs, specs.json, SEO pages, sitemap/robots are all committed | The DB (local-only), Redis/Stripe/env, the OM source PDFs, the live site |

**What CI genuinely proves:** the committed artifacts satisfy every artifact-level invariant —
no regression can be *merged* that reintroduces ver:0 leaks, narratives, notes, false
attribution, a desynced blob, an unmarked specs.json, or "documented" framing. This covers
~85% of ledger invariants and 100% of the classes that actually bit us this week.

**What CI cannot prove (and we don't pretend):** that the committed artifact *matches the DB*
(equivalence/regeneration checks), or anything about the live deployment or runtime services.
Those stay in the workstation full suite (DB tier) and the existing post-deploy pollers.
Consequence to accept: a hand-edited-but-internally-consistent blob would pass CI and only
fail the local DB-tier run — acceptable because the deploy ritual runs the full suite and
`_deploy_check.py` still guards the commit path.

## 3. What it needs

- **Nothing new for CI**: artifacts are tracked; the workflow is checkout + python + one
  script. No secrets, no DB artifact, no network. (Do NOT upload the DB or any OM-derived
  content to CI — the DB is deliberately local-only.)
- **One generator change (later, at implementation):** a `--check`/dry-run mode on
  `files/04_rebuild_demo.py` that builds the data JSON in memory and compares against the
  committed blob without writing files — enables S1.7. Until then S1.7 is approximated by
  the existing build-time guards plus S4.4's specs.json equivalence.
- **Guard relationship:** `_deploy_check.py` (commit-scoped, staged-set) stays as-is;
  `_verify_shipped.py` is artifact-scoped. They overlap on 2 checks (blob forbidden-strings,
  specs marker) — intentional redundancy at different lifecycle points, same pattern as the
  build-time payload guards.

## 3b. The anti-drift mechanism — schema whitelists (default-deny)

S4 (specs.json) and S5 (`comps_agg`) are enforced as **key whitelists**: any key not
enumerated fails, so an unanticipated shape — a narrative field returning under a new name,
a gated spec field reappearing — is rejected *by default*, without anyone having to predict
it. This is the pattern future surface-additions must follow: **when a new surface or field
ships, add its own whitelist entry to the ledger + verifier in the same commit — never widen
an existing whitelist to make something pass, and never fall back to blocklisting known-bad
keys** (blocklists rot; default-deny doesn't). A failing whitelist check on new work is the
system working, not an obstacle to route around.

## 4. Reporting

- **FAIL tier** → printed as `x <check-id>: <detail>` and exit 1 (red CI, ritual stops).
  Every integrity invariant is FAIL.
- **WARN tier** → printed as `! <check-id>: <detail>`, exit stays 0 (size budgets, robots
  crawlability, whole-blob PII sweep, the deferred P1-6 copy check). A WARN that pages
  repeatedly gets promoted or fixed.
- Summary line mirrors the guard style: `SHIPPED-SURFACES VERIFY: PASS (N checks, M warns)`.

## 5. Rollout order (when implementation is approved)

1. `_verify_shipped.py` with all [CI] checks; run locally against HEAD — must PASS clean
   (the ten shipped fixes are the fixture).
2. Negative fixtures: temporarily inject each violation class in a scratch copy and confirm
   each check fires (same discipline as the specs-marker guard test).
3. `.github/workflows/verify.yml` (first workflow in the repo; public — contents are
   invariant names only, nothing sensitive).
4. Add the DB-tier checks behind the auto-detect.
5. Wire into the deploy ritual doc (CLAUDE.md pipeline step) — and only then consider the
   04_rebuild `--check` mode as a follow-up.

## 6. Open questions for the ruling

1. **Commit the docs?** `docs/` is untracked by default. The ledger + this design are
   public-safe (they describe invariants already visible in committed guard code). Proposal:
   commit both alongside the verifier; keep the audit doc itself untracked.
2. **Hook wiring:** run the CI subset inside the `git_guard` pre-commit hook too (~seconds,
   catches drift before commit), or keep the hook fast and rely on ritual + CI? Proposal:
   ritual + CI only, revisit if drift recurs.
3. **Workflow scope:** run on all pushes/PRs to `main` (proposal), or path-filter to shipped
   files (faster, but path lists rot — against the audit-surfaces lesson).
