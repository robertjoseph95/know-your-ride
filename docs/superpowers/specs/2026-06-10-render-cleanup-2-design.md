# Render cleanup 2 — all 6 simplifier findings (refactor-v32)

Date: 2026-06-10
Status: Approved design (pre-implementation)
Follows: render cleanup Step 2 (`refactor-v31`, the `specRow` extraction)
Input: the code-simplifier ANALYSIS report (6 findings)

## Goal

Apply all 6 code-simplifier findings to the render layer in `wrench_demo.html` as
ONE output-preserving refactor. Success criterion: **byte-identical rendered
output and zero behavior change**, proven by a golden checksum plus
by-construction/grep proofs for the parts not exercised by the modal.

## Caveats — verified resolved during brainstorming

- **#4 dead functions are safe to delete.** `renderPartsTiered` /
  `renderPartsTieredYT` are injected by `files/04_rebuild_demo.py`, but each
  inject step is sentinel-guarded (`if "/*WRENCH_PARTTIERS*/" in html: return`),
  so a rebuild will NOT re-add them once removed; the dispatch table already
  points at `renderPartsTieredYTG`.
- **#5 `affRock`/`affAz` have zero call-sites** (grep: definition lines only) —
  delete the two defs; no call-site removal needed.
- **#1** there are 18 call-sites for the four body-text escapers
  (`ghEsc`×4, `kypEsc`×4, `dtcEsc`×5, `rclEsc`×5); `ytEsc`×8 stays (it also
  escapes `"` for attributes).
- Current prod golden (`refactor-v31`, output-identical to v30) is
  `len 72884 / hash -1768306184` — reused as the v32 baseline.

## The 6 changes (all in `wrench_demo.html`, all output-preserving)

1. **Consolidate escapers.** Add `function htmlEsc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}`.
   Rename the 18 call-sites of `ghEsc`/`kypEsc`/`dtcEsc`/`rclEsc` to `htmlEsc`,
   then delete those 4 function definitions. Leave `ytEsc` untouched (its body
   differs — it escapes `"`).
2. **`specNote` helper.** Add `function specNote(l,v,sz){return '<div class="spec-item" style="grid-column:1/-1"><div class="sp-l">'+l+'</div><div class="sp-v" style="font-size:'+(sz||11)+'px;font-weight:500;color:var(--dim)">'+v+'</div></div>';}`.
   Replace the 5 full-width note rows ("Notes", "Trim Variants", "Battery Notes",
   "Timing Notes", "Oil Interval Notes") with `specNote(...)` calls. The
   `renderSafety` "Top Issue" row uses `font-size:12px` — convert it as
   `specNote(label, value, 12)`. Each emitted string must match exactly; **if any
   note row's markup deviates from this template in any other way, leave it
   inline** rather than distort the helper.
3. **`partRow` helper.** Add `function partRow(x,extra){return '<tr><td style="font-weight:700">'+(x.brand||'&mdash;')+'</td><td><span class="pn">'+(x.part_number||'&mdash;')+'</span></td>'+(extra||'')+'</tr>';}`.
   Replace the 5 part-table row lambdas (plugs, batts, air, cabin, wipers) so the
   shared first two `<td>` cells come from `partRow`, with each table's remaining
   cells passed as the `extra` string. Emitted HTML must be identical; **if any
   table's first two cells differ from the shared template, leave that table
   inline.** Headers are NOT unified (they differ per part type).
4. **Delete dead functions** `renderPartsTiered` and `renderPartsTieredYT`
   (only `renderPartsTieredYTG` is wired in the dispatch table).
5. **Delete dead stubs** `affRock` and `affAz` (uncalled, return `''`).
6. **`renderMaintGated` clone.** Replace the manual `for…in` shallow copy with
   `var clone=Object.assign({},v,{maint:v.maint.slice(0,3)});`.

## Verification (per finding)

| # | Gate |
|---|------|
| 1 | by-construction (htmlEsc body == the 4 deleted bodies) + `node --check` (no undefined) + grep: 0 occurrences of `ghEsc(`/`kypEsc(`/`dtcEsc(`/`rclEsc(` remain |
| 2 | golden checksum (renders in oil/parts/safety modal tabs) |
| 3 | golden checksum (renders in parts modal tab) |
| 4 | golden checksum + grep: `function renderPartsTiered(`/`renderPartsTieredYT(` gone after rebuild (not re-injected) |
| 5 | golden checksum (covers `affRow`) + grep: 0 `affRock(`/`affAz(` |
| 6 | golden checksum (maint modal tab) |

**Golden checksum** (same harness as refactor-v31): `preview_eval` hashes
`#m-body.innerHTML` across all 9 modal tabs for `DB.v.find` ICE-with-recalls / EV
/ rich-maint vehicles; MUST return `{len:72884, hash:-1768306184}`. Captured on
the current build before edits (or reuse the known value), asserted after the
refactor. Plus `node --check` and a no-console-errors check.

## Execution & ship

The code-simplifier agent applies all 6 in one pass (it already analyzed them),
strictly to the scope above — it must NOT change any emitted HTML string or
behavior. One golden gate after. Ship via the normal pipeline, version
`2026-06-10-refactor-v32`. Reversible (revert the commit).

## Out of scope

- Any behavior/visual change; any change to a rendered HTML string.
- Touching `ytEsc` (kept — different body), the data blob, build scripts, or
  non-render code.
- Unifying the part-table HEADERS (#3 covers row bodies only; headers differ per
  part type and stay as-is).
