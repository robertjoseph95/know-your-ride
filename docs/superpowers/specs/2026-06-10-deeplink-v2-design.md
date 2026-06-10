# Deep-link v2 — Browser Back/Forward through the spec modal

Date: 2026-06-10
Status: Approved design (pre-implementation)
Builds on: `deeplink-v27` (v1)

## Goal

Make the browser **Back/Forward** buttons step through in-app modal state:
opening a vehicle pushes a history entry, and Back closes the modal (Forward
reopens it). This is the one follow-up from the v1 deep-link work.

## Scope (decided)

- **Modal only.** Opening a vehicle creates a history entry. Tabs and DTC code
  lookups stay on `replaceState` (no new history entries) exactly as in v1.
- **Stay-in-app on deep-link close.** When the modal is the visitor's first
  history entry (a shared `/?v=ID` link, or the sessionStorage auto-reopen),
  closing it swaps the URL to the base and shows the Garage — the visitor is
  never bounced off-site.

Out of scope (YAGNI): tabs/codes in Back history, modal sub-tabs (Oil/Parts/…)
in history, any routing library or History `state` objects.

## Approach

"Modal = one history entry" (symmetric): push on a user open; close by any means
behaves identically to Back; a single `popstate` handler re-applies state from
the URL; a replay guard prevents loops.

## State model

Two new module-level flags, added alongside v1's `__kyrCurV` / `__kyrBooting`:

- `__kyrReplaying` (bool) — true while applying state *from* the URL (on-load
  apply and inside the `popstate` handler). Suppresses all history writes so
  re-applying never creates entries or triggers `history.back()`.
- `__kyrPushedModal` (bool) — true once a modal entry has been `pushState`-d
  this session. Distinguishes a user-opened modal (we own an entry to pop) from
  a deep-link / auto-reopen entry (we do not).

## Transition rules

| Trigger | History action |
|---|---|
| Open vehicle (user: card, placard CTA, VIN match, sample, multi-trim pick) | `pushState(?v=ID)`; `__kyrPushedModal = true` |
| Open vehicle during replay (on-load `?v=`, popstate Forward) | UI only, no push (on load, `replaceState` to normalize the URL) |
| Close (✕ / Escape / backdrop / Change Vehicle), user-initiated | if `__kyrPushedModal`: `history.back()` (popstate performs the UI close); else: `replaceState(base)` + UI close + show Garage |
| Close during replay (popstate Back) | UI only, no history write |
| Switch tab / look up code | unchanged from v1 — `replaceState` |

## popstate flow

A single `popstate` listener, body wrapped in `__kyrReplaying = true … = false`
(in a `try/finally`):

1. Read `?v` from the new (post-navigation) URL.
2. `?v` present, valid (`VEH[v]`), modal currently closed → open modal UI.
3. `?v` absent, modal currently open → close modal UI + show the tab/garage the
   URL describes.
4. Otherwise → no-op (tab/code params are replaceState-only and don't normally
   surface via popstate).

All open/close performed here run under `__kyrReplaying`, so none of them push
or call `history.back()`.

## Loop prevention & coexistence with v1

- `kyrSyncURL()` gets one guard line at the top: `if (__kyrReplaying) return;`
  so replay never rewrites history.
- Only the **modal-open** write changes from v1's `replaceState` to a
  `pushState` — and only on genuine user opens. Tab/code sync is byte-for-byte
  v1 behavior.
- `kyrApplyURL()` (on-load) runs with `__kyrReplaying = true` so the initial
  `?v=` open does not push; it `replaceState`s to keep the URL canonical.
- **sessionStorage auto-reopen** (v1 reopens the last vehicle on a bare load):
  kept, but treated as a non-pushed entry (identical to a deep-link landing), so
  closing it lands on the Garage with no off-site bounce.

## Edge cases

- **Deep-link `/?v=ID` is the first entry** → `__kyrPushedModal` stays false →
  close does `replaceState(base)` + Garage (stays in app). A real Back from
  there goes to whatever preceded the site, which is correct.
- **Open A, then open B without closing** (e.g. VIN decode with a modal already
  open) → a fresh `pushState(?v=B)`, so Back returns to A.
- **Rapid Back/Forward** → `__kyrReplaying` serializes each popstate;
  open/close act only when the target state differs from the current state
  (idempotent), preventing double-toggle.
- **Invalid/stale `?v=`** (id not in `VEH`) → ignored; falls through to
  tab/code, then to the sessionStorage path (same as v1).

## Components touched (single-file app: `wrench_demo.html`)

- New: `__kyrReplaying`, `__kyrPushedModal` globals; one `popstate` listener
  (registered in the existing `DOMContentLoaded`).
- Modified: the modal-open URL write (push-vs-replace split); `closeModal`
  user-close logic (history.back vs replaceState); `kyrSyncURL` replay guard.
- Unchanged: `switchTab`, `lookupCode`, `kyrApplyURL`'s read logic, tabs/code
  params, the entire non-modal app.

## Testing / verification

1. `node --check` on the extracted inline JS (syntax).
2. Fresh-server `preview_eval` sequence on the real page:
   - user `openModal` → assert `location.search === '?v=…'` and
     `history.length` increased and `__kyrPushedModal === true`;
   - `history.back()` → assert modal closed and URL is base;
   - `history.forward()` → assert modal reopened with the same vehicle;
   - simulate deep-link entry (`replaceState('?v=ID')`, reset flags, apply) then
     user close → assert URL base + Garage visible + no off-site navigation;
   - no-param load → assert nothing opens;
   - switch tab / look up code → assert still `replaceState` (history.length
     unchanged).
3. Post-deploy manual Back/Forward pass on `knowyourride.net`.

## Deploy

Same pipeline: edit `wrench_demo.html` → `04_rebuild_demo.py` →
`_deploy_sync_specs.py` (bump `kyr-version` to `2026-06-10-deeplink2-v29`) →
verify → commit `wrench_demo.html` + `wrench_deploy/index.html` → push → poll
live. (`v28` is current production; `v29` is the next free version.)
