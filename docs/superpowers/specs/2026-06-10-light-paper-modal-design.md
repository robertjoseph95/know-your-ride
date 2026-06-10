# Light-paper spec modal — Step 1 (the paper surface)

Date: 2026-06-10
Status: Approved design (pre-implementation)
Part of: the "Service Manual" visual direction (see kyr-visual-redesign memory)

## Goal

Render the vehicle spec modal's BODY on a warm cream "manual page" surface (dark
ink, ruled rows, section marks) while keeping the dark header + chapter tabs as
the "binder" shell — the deepest expression of the service-manual direction.

## Scope

**This spec is Step 1 only: the paper surface (CSS).** The exploration found the
modal body is fully CSS-variable-driven, so the visual change is achievable as a
single scoped CSS block with NO render-function edits. That makes it independent
of the render-layer code cleanup, which is deferred to **Step 2** (a separate
`code-simplifier` spec/effort). Do not mix the refactor into this change.

Decisions locked during brainstorming:
- **Whole modal body, uniform** — every tab and embedded block renders on cream.
- **Burnt-orange/rust accent** — `--accent` darkens to `#b8500a` on the page (the
  bright `#ff6b00` fails contrast on cream for small text).
- **Targeted cleanup only** (and that's Step 2, not here).

## Mechanism (Approach A: scoped CSS-variable + structural override)

1. Markup: change the modal body element from `class="m-body"` to
   `class="m-body paper"` (the only non-CSS edit). The body is static markup
   (`<div class="m-body paper" id="m-body">`); its content is still rendered by
   `renderMBody` unchanged.
2. Add one CSS block `.m-body.paper { … }` that (a) remaps the color vars to
   light values, (b) restructures spec layout into ruled rows, (c) adds the
   manual section mark. Because every body class and every inline `var(--…)` in
   the render strings inherits these scoped vars, the whole subtree re-themes.
3. The header (`.m-top`) and chapter tabs (`.m-tabs`/`.m-tab`) are OUTSIDE
   `.m-body`, so they are untouched and stay dark (the binder).

Fully reversible: removing the `paper` class restores the dark modal exactly.

## Color tokens (set on `.m-body.paper`)

Body: `background:#ece6d8; color:#1b1e23;`

| Var | Paper value | Role |
|---|---|---|
| `--panel` | `#e3dccb` | nested surfaces |
| `--p2` | `#ddd5c0` | table header / chip bg |
| `--border` | `#c3bca9` | ink hairline |
| `--b2` | `#a89f88` | strong rule (sec-head) |
| `--text` | `#1b1e23` | primary ink |
| `--dim` | `#5f5848` | secondary ink |
| `--faint` | `#8a8268` | tertiary ink / labels |
| `--accent` | `#b8500a` | rust highlight (values, score) |
| `--red` | `#a3380f` | recalls / warnings |
| `--green` | `#1f6b3a` | pass / good |
| `--a2` | `#8a5a14` | amber / watch |
| `--purple` | `#5b3a8a` | misc |

Contrast intent: every ink-on-cream pairing must clear WCAG AA (4.5:1 for body
text, 3:1 for large text/`.rel-score-big`). Verified in Verification below; if
any pair misses, darken that token until it passes (do not ship a failing pair).

## Structural overrides (CSS-only, inside `.m-body.paper`)

Keep `.spec-grid` as the existing 2-column grid (do NOT switch to flex
label-left/value-right rows: full-width items that span `grid-column:1/-1`, e.g.
the "Notes" / "Trim Variants" prose rows, would right-align awkwardly). Just
flatten the cells into hairline-ruled entries so the grid reads as a printed
spec sheet:

- `.spec-item { background:transparent; border:0; border-bottom:1px solid var(--border); border-radius:0; padding:8px 2px }` — flat ruled cells, label-above-value preserved (handles both short values and full-width prose).
- `.recall-card, .wty-card, .mpg-row, .pt-card { background:transparent; border:1px solid var(--border); border-radius:2px }` (recall keeps its accent `border-left`).
- `.sec-head::before { content:"\00A7 "; color:var(--accent); font-weight:700 }` — the manual section mark (no render edit).
- Tables: `.tbl th`/`.tbl td` already use vars (re-theme automatically); confirm header legibility on the lighter `--p2`.

## Hardcoded-background blocks (the only eyes-on part)

A few embedded blocks use hardcoded DARK backgrounds that the var-remap will not
catch; without overrides they would be dark islands on the cream page. Add light
overrides inside `.m-body.paper`:

- `.gh-banner` (AI-guide notice; hardcoded `background:#3a2e00;color:#ffd97a`) →
  parchment amber, e.g. `background:#efe2c4; border-color:#b88a2e; color:#5a3d0a`.
- `.gh-safety` (safety warning; hardcoded `background:#3a1500`) →
  light warning, e.g. `background:#f3dcd2; border-color:var(--red); color:#7a2a0c`.
- `.gh-guide` and the YouTube / parts-tier hint backgrounds: mostly reference
  `--p2`/vars and should re-theme — VERIFY each during implementation and add an
  override only if a hardcoded dark value surfaces.
- `#000`/`#fff` text occurrences are on COLORED chips/badges (badge text), which
  remain legible on cream — leave as-is.

The implementer must visually/computed-check each tab for any remaining dark
island and add a scoped override; this enumerated list is the starting set.

## Verification

1. `node --check` on extracted inline JS (the only JS change is the class name).
2. Fresh preview server + `preview_eval`, iterating ALL nine modal tabs
   (`oil, parts, fluids, maint, perf, safety, issues, warranty, comps`) for a
   vehicle with rich data:
   - Assert `getComputedStyle('.m-body')` background is the cream and `.sp-v`
     color is dark ink.
   - For each of these foreground/background pairs, compute the WCAG contrast
     ratio in-page and assert it passes: ink `--text` on cream, label `--faint`
     on cream, value `--dim` on cream, accent `--accent` on cream (≥3:1 as it is
     used on `.rel-score-big` large text; ≥4.5:1 anywhere it is small), `--red`
     / `--green` / `--a2` on cream.
   - Switch to each tab and scan for any element whose computed background is a
     dark color (luminance below a threshold) sitting inside `.m-body` — flag as
     a missed dark island.
   - Confirm no console errors.
3. Screenshot the modal if the preview tool cooperates (best-effort).
4. Post-deploy manual pass: open several vehicles (ICE, EV, one with recalls),
   tab through, confirm the page reads as a manual and nothing is unreadable.

## Rollout

- Reversible class toggle; no feature flag needed.
- Deploy pipeline unchanged: edit `wrench_demo.html` → `04_rebuild_demo.py` →
  `_deploy_sync_specs.py` (bump `kyr-version` to `2026-06-10-lightpaper-v30`) →
  verify → commit `wrench_demo.html` + `wrench_deploy/index.html` → push → poll.

## Out of scope (explicitly)

- Render-function refactor / `code-simplifier` pass → Step 2 (separate spec).
- Any change to the dark binder (header, chapter tabs), the garage, the placard
  hero, or non-modal surfaces.
- Light theme for anything outside the modal body.
