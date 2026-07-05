# KYR — Know Your Ride (knowyourride.net)

Consumer vehicle-maintenance web app. This repo = the public deploy repo (`wrench_deploy/`
served by Vercel) plus the spec-verification campaign workspace (local-only files, untracked).

## Read first (before any campaign slice)
1. `vision.md` (local-only, untracked) — resume context: tally, make-by-make status, in-flight work, next tasks
2. `KYR_OEM_Manual_Source_Map.md` — per-make OM source/self-ID navigation
3. `KYR_Source_Authority_Matrix.md` (local-only, untracked) — which source is authoritative for which field

## THE LAW — Data Integrity Gate
**NEVER write a spec value without an authoritative source.**
- VERIFIED = manufacturer or government ONLY (owner's manual / licensed service manual / vPIC / EPA / NHTSA — per field type, see the authority matrix).
- Blacklisted sources (parts retailers, dealer pages, blogs, forums, AI, unverified APIs) are **never acceptable even when convenient or correct** — leads only.
- OM ambiguous or silent on a value → **GATE** (write `null`; it renders as absent, not fabricated).
- No clean/legible/free-citable OM for a year → **DEFER the row with reason** (honest defer ≠ gap).
- Performance-variant oil/viscosity is exactly where forums diverge from the OM → OM only, page-cited.
- Read every value fresh per year: **engine predicts, the OM decides** (body decides cooling/fuel/tire/lug).
- Confirm the OM self-IDs the vehicle (illustration + engine-roster + gen-code) BEFORE extracting — never name-count or filename alone.
- Electrified (HEV/PHEV/BEV) systems → gate; write gas-engine specs only where separable.
- **The 2025/26 SCRAPE is blacklisted by SOURCE, not by year** (D1, 2026-07-02): OM/gov-verified rows ship regardless of model year. The build hard-fails if any blacklisted source (ai-*/haiku/scraped/classifier) ever computes `ver=1`.
- **ver:0 values are STRIPPED from the shipped payload at build** (C1, 2026-07-02): render-time gating alone is not enough — unverified oil/parts/fluids ship as bare `{ver:0}` shells, unverified torque/maint rows drop, and internal provenance keys (`source`/`last_verified_at`) never ship.

## Two-tier doctrine (D0, 2026-07-02)
- **Tier 1 — the verified-data core** (static HTML + data blob): stays static-over-SQLite with ZERO runtime dependency; never add a runtime service to it.
- **Tier 2 — the Pro layer** (`wrench_deploy/api/`): a commercial shell. Runtime deps allowed but must stay DECOUPLED and PORTABLE — plain serverless functions + Redis + Stripe only; **no Vercel-proprietary services** (KV/Blob/Edge-middleware).

## Repo map
- `wrench_vehicles.db` (repo root) = **the canonical DB**. ⚠ `files/wrench_vehicles.db` is a stale partial copy with no curated tables — never read or write it.
- `_write_<make>_<nameplate>.py` (root) = per-slice DB write scripts (backup DB → DELETE 6 curated tables per id → INSERT, all fields source-cited).
- `wrench_deploy/` = the live site (has its own scoped CLAUDE.md — deploy ritual lives there).
- `files/` = build pipeline (has its own scoped CLAUDE.md — `_ver()` gate rules live there).

## Pipeline (per slice)
1. Run the write script (root DB)
2. `python files/04_rebuild_demo.py` (rebuild + compute `ver`)
3. Preview: MCP server "kyr-demo" port 8752 → reload with a fresh cache-buster (the `__D__.v` blob caches in browser memory). **PAUSE for user check.**
4. `KYR_NEW_VER=<version> python _deploy_sync_specs.py`
5. Commit with targeted `git add` (NEVER `git add -A`)
6. Confirm live: `curl -s "https://knowyourride.net/?cb=<rand>" | grep kyr-version` (~2–4 min Vercel build)
7. Update `KYR_OEM_Manual_Source_Map.md` + the make's `KYR_<Make>_Verification_Log.md`

## Workflow discipline
- Slices are **PAUSE-gated**: inventory → source recon **PAUSE** → engine map **PAUSE** → reads **PAUSE (present log)** → write/deploy **only on explicit user go**.
- **Echo ≠ approval**: if the user pastes back a preview without a new instruction, HOLD and ask.

## Git — CRITICAL
- **NEVER `git add -A` / `git add .`** — the working tree holds many untracked local-only files; use targeted `git add <path>` so only intended files are committed. A pre-commit guard also blocks whole-tree adds and enforces this.
- Always: targeted `git add <path>` → `git show --stat HEAD` to verify contents → push.
- This root `CLAUDE.md` is committed (shared project context). Machine-local or sensitive operational notes belong in `CLAUDE.local.md` (gitignored). The scoped `wrench_deploy/CLAUDE.md` and `files/CLAUDE.md` remain untracked.

## Environment
- Windows 11 / PowerShell primary + Bash tool (POSIX). Python: `pdfplumber` available (text + `page.to_image(resolution=N).save()`); **NO fitz / PyMuPDF / pdf2image**. CCITT-G4-fax OM illustrations are unrenderable.
- OM fetches generally need a browser User-Agent (GM also needs it; Subaru needs Referer `https://www.subaru.com/`).
