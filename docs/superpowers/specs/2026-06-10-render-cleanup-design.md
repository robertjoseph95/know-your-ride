# Render-layer cleanup — Step 2 (`specRow` extraction)

Date: 2026-06-10
Status: Approved design (pre-implementation)
Follows: light-paper modal Step 1 (`lightpaper-v30`)

## Goal

DRY the most-repeated markup pattern in the spec-modal render functions — the
`spec-item` row — behind one helper, with **zero change to the rendered output
or behavior**. A maintainability refactor of the core spec-viewing flow, made
safe by a golden-output checksum.

## Scope (decided)

- **`specRow` helper only.** Measurement found the genuine duplication is narrow:
  39 identical `spec-item` blocks; 11 tables (vary by columns — out of scope);
  wrapper-composition chains (`renderOilShop`, `renderPartsTieredYTG`, …) are
  clean composition, not duplication — **leave them**.
- **Ship normally** (regenerate build, version `refactor-v31`).
- Success criterion: the rendered HTML of every modal tab, for several vehicles,
  is **byte-identical** before vs after (verified by checksum).

Out of scope: table helper, wrapper-chain changes, any behavior/visual change,
anything outside the modal render functions.

## The helper

```js
function specRow(l,v,c){return '<div class="spec-item"><div class="sp-l">'+l+'</div><div class="sp-v'+(c?' '+c:'')+'">'+v+'</div></div>';}
```

This emits the EXACT current string for the simple case: `c` omitted →
`<div class="sp-v">`; `c='ac'` → `<div class="sp-v ac">` (and likewise `gr`,
`rd`). Class ordering and markup match what is there today, so output is
identical.

**Replace:** the simple `spec-item` emissions of the form
`'<div class="spec-item"><div class="sp-l">LABEL</div><div class="sp-v[ CLS]">VALUE</div></div>'`
with `specRow(LABEL, VALUE [, 'CLS'])`.

**Leave as raw strings:** the non-uniform `spec-item`s — the full-width note rows
that carry `style="grid-column:1/-1"` on the item and/or a custom `style="…"` on
the `.sp-v` (e.g. "Notes", "Trim Variants", "Battery Notes", "Timing Notes", "Oil
Interval Notes"). Forcing these into the helper would add parameters and reduce
clarity. Only the clean label/value/class rows are converted.

These appear across `renderOil`, `renderEV`, `renderParts`, `renderFluids`,
`renderPerf`, `renderSafety` (and any other modal renderer using `spec-item`).

## Verification harness (the centerpiece)

A `preview_eval` expression that self-selects representative vehicles from the
live dataset and checksums the rendered body of every tab:

```js
(function(){
  var picks=[
    DB.v.find(function(v){return v.oil&&v.oil.visc&&v.recalls&&v.recalls.length;}),
    DB.v.find(function(v){return v.ev;}),
    DB.v.find(function(v){return v.maint&&v.maint.length>3;})
  ].filter(Boolean);
  var tabs=['oil','parts','fluids','maint','perf','safety','issues','warranty','comps'];
  var all='';
  picks.forEach(function(v){tabs.forEach(function(t){openModal(v.id);switchMTab(t,v.id);all+=document.getElementById('m-body').innerHTML;});});
  var h=0;for(var i=0;i<all.length;i++){h=((h<<5)-h+all.charCodeAt(i))|0;}
  return {len:all.length,hash:h,picks:picks.map(function(v){return v.id;})};
})()
```

Procedure:
1. **Capture golden** on the CURRENT prod build (before any edit): record
   `{len, hash, picks}`.
2. Do the refactor.
3. **Re-run** on the refactored build: assert `len` and `hash` are **identical**
   and `picks` are the same ids. Any difference = output drift → fix until equal.
4. Also: `node --check` on extracted inline JS; `preview_console_logs` shows no
   errors.

Determinism notes: the picks are `DB.v.find` (first match — stable across builds,
same data). Render output is data-driven (no `Math.random`/`Date` in the spec
HTML). Run both captures in a fresh, non-Pro browser so gated content
(`renderMaintGated`) is in the same state. `openModal` pushing history entries
does not affect `innerHTML`, so it does not affect the checksum.

## Execution

Use the **code-simplifier agent** to perform the `specRow` extraction (this DRY
is its wheelhouse), strictly bounded to the `specRow` scope above — it must NOT
touch tables, wrapper chains, or the non-uniform note rows, and must not alter
any emitted string. The golden-output gate is the backstop that proves it
stayed in bounds.

## Rollout

- Reversible: revert the commit.
- Pipeline unchanged: edit `wrench_demo.html` → `04_rebuild_demo.py` →
  `_deploy_sync_specs.py` (bump `kyr-version` to `2026-06-10-refactor-v31`) →
  golden-verify → commit `wrench_demo.html` + `wrench_deploy/index.html` → push →
  poll. The version label records a no-visual-change refactor.

## Risks

- **Output drift** (a converted row differs by a byte): caught by the golden
  checksum before deploy — the entire point of the harness.
- **Scope creep** (simplifier "improves" beyond `specRow`): bounded by explicit
  instruction + the golden gate flags any unexpected change.
- Low blast radius otherwise: one new function + mechanical call-site swaps, no
  data or pipeline change.
