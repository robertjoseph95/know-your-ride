# Render Cleanup 2 (all 6 findings) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply all 6 code-simplifier findings to the render layer as one output-preserving refactor (`refactor-v32`), with byte-identical rendered output.

**Architecture:** Six small edits in `wrench_demo.html` (add `htmlEsc`/`specNote`/`partRow` helpers; rename escaper call-sites; delete dead `renderPartsTiered`/`renderPartsTieredYT`/`affRock`/`affAz`; `Object.assign` clone). The code-simplifier agent applies them in one pass; a golden checksum (must stay `len 72884 / hash -1768306184`) plus `node --check` and greps prove nothing changed.

**Tech Stack:** Vanilla JS in a single file, built to `wrench_deploy/index.html` via `files/04_rebuild_demo.py` + `_deploy_sync_specs.py`. No test runner — verification is the golden `preview_eval` checksum + `node --check` + targeted greps.

---

## Testing approach (read first)

Success = byte-identical rendered output. The **golden checksum** (below) hashes the modal body for representative vehicles across all 9 tabs; it must return the same `{len, hash}` before and after. It covers findings #2/#3/#6 (and #5 via `affRow`). Findings #1 (escaper merge) and #4 (dead-code) are not all exercised by the modal, so they are proven by construction (identical function bodies) + `node --check` (no undefined references) + greps. Capture the golden on the current build first (Task 1); assert after (Task 3).

**Golden harness** (same as refactor-v31):
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
Known golden (from refactor-v31, current prod): `{len:72884, hash:-1768306184}`.

## File structure

- **Modify:** `wrench_demo.html` — render helpers + render functions (all 6 changes).
- **Modify:** `_deploy_sync_specs.py` — bump `NEW_VER` (Task 4).
- **Generated:** `wrench_deploy/index.html` — built; not hand-edited.

---

### Task 1: Confirm the golden baseline — controller-run

**Files:** none.

- [ ] **Step 1: Confirm current build is refactor-v31.**
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && grep -o 'kyr-version" content="[^"]*"' wrench_deploy/index.html
```
Expected: `2026-06-10-refactor-v31`.

- [ ] **Step 2: Start a fresh preview server** (config `kyr-g3`, port 8740, `--directory wrench_deploy`; stop a stale server first if at the 5-cap via `preview_list`/`preview_stop`). `preview_start`, keep `serverId`.

- [ ] **Step 3: Run the golden harness** (Testing approach) via `preview_eval`. Confirm it returns `{len:72884, hash:-1768306184}`. (If it differs, the baseline moved — record the new value and use THAT as the golden.) `preview_console_logs` (error) → none.

- [ ] **Step 4: Record the golden** as `GOLDEN = {len:72884, hash:-1768306184}` (or the value from Step 3) for Task 3. No commit.

---

### Task 2: Apply all 6 findings — implementer: code-simplifier agent

**Files:**
- Modify: `wrench_demo.html`

Dispatch the **code-simplifier agent**. It must change NO emitted HTML string and NO behavior. All 6 changes below, then `node --check` + greps + commit (NO push). Edit `wrench_demo.html` ONLY.

- [ ] **Step 1: Finding 1 — consolidate escapers.** Add near the other escape helpers:
```js
function htmlEsc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
```
Rename every call of `ghEsc(`, `kypEsc(`, `dtcEsc(`, `rclEsc(` to `htmlEsc(` (18 call-sites total). Then DELETE the four function definitions `function ghEsc(...)`, `function kypEsc(...)`, `function dtcEsc(...)`, `function rclEsc(...)`. Leave `ytEsc` entirely untouched (its body also escapes `"`).

- [ ] **Step 2: Finding 2 — `specNote` helper.** Add:
```js
function specNote(l,v,sz){return '<div class="spec-item" style="grid-column:1/-1"><div class="sp-l">'+l+'</div><div class="sp-v" style="font-size:'+(sz||11)+'px;font-weight:500;color:var(--dim)">'+v+'</div></div>';}
```
Replace the full-width note rows that EXACTLY match the template `'<div class="spec-item" style="grid-column:1/-1"><div class="sp-l">LABEL</div><div class="sp-v" style="font-size:11px;font-weight:500;color:var(--dim)">VALUE</div></div>'` with `specNote(LABEL, VALUE)`. For the `renderSafety` "Top Issue" row (uses `font-size:12px`) use `specNote(LABEL, VALUE, 12)`. **If a row deviates from the template in any other way, LEAVE IT INLINE.**

- [ ] **Step 3: Finding 3 — `partRow` helper.** Add:
```js
function partRow(x,extra){return '<tr><td style="font-weight:700">'+(x.brand||'&mdash;')+'</td><td><span class="pn">'+(x.part_number||'&mdash;')+'</span></td>'+(extra||'')+'</tr>';}
```
In `renderParts`, the five `.map(function(x){return '<tr>...'})` lambdas for plugs/batteries/air/cabin/wipers share the first two cells `'<td style="font-weight:700">'+(x.brand||'&mdash;')+'</td><td><span class="pn">'+(x.part_number||'&mdash;')+'</span></td>'`. Replace each so the row body uses `partRow(x, EXTRA)` where `EXTRA` is that table's remaining `<td>...` cells (the exact existing expressions). **If a table's first two cells differ from the shared template, LEAVE that table inline.** Do NOT change any table HEADER.

- [ ] **Step 4: Finding 4 — delete dead functions.** Delete the two function definitions:
```js
function renderPartsTiered(v){return renderPartTiers(v)+renderParts(v);}
function renderPartsTieredYT(v){return renderPartTiers(v)+renderWatchItDone(v)+renderParts(v);}
```
Leave `renderPartsTieredYTG` (it is the one wired into the dispatch table).

- [ ] **Step 5: Finding 5 — delete dead stubs.** Delete:
```js
function affRock(v){return '';}
function affAz(pn){return '';}
```
(They are uncalled — confirmed zero call-sites.)

- [ ] **Step 6: Finding 6 — `Object.assign` clone.** In `renderMaintGated`, replace `var clone={};for(var k in v)clone[k]=v[k];clone.maint=v.maint.slice(0,3);` with:
```js
var clone=Object.assign({},v,{maint:v.maint.slice(0,3)});
```

- [ ] **Step 7: Syntax + grep checks.**
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data"
python -c "import re;html=open('wrench_demo.html',encoding='utf-8').read();ds=html.find('const __D__=');de=html.find('</script>',ds);html=html[:ds]+'const __D__={v:[],dtc:{},fixes:{},fuseTsbsByCode:{}};'+html[de:];b=re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',html,re.S);open('_sc.js','w',encoding='utf-8').write('\n;\n'.join(b))" && node --check _sc.js && echo "NODE OK" && rm -f _sc.js
echo -n "old escaper calls remaining (expect 0): "; grep -c "ghEsc(\|kypEsc(\|dtcEsc(\|rclEsc(" wrench_demo.html
echo -n "htmlEsc defined (expect 1): "; grep -c "function htmlEsc" wrench_demo.html
echo -n "affRock/affAz remaining (expect 0): "; grep -c "affRock(\|affAz(" wrench_demo.html
echo -n "dead render fns remaining (expect 0): "; grep -c "function renderPartsTiered(v){return\|function renderPartsTieredYT(v){return" wrench_demo.html
echo -n "renderPartsTieredYTG kept (expect 1): "; grep -c "function renderPartsTieredYTG" wrench_demo.html
```
Expected: `NODE OK`; old escapers `0`; htmlEsc `1`; affRock/affAz `0`; dead fns `0`; YTG `1`.

- [ ] **Step 8: Commit (wrench_demo.html ONLY, no push).**
```bash
git add wrench_demo.html
git commit -m "refactor: apply 6 simplifier findings (htmlEsc/specNote/partRow, delete dead code)"
```

---

### Task 3: Golden verification gate — controller-run

**Files:** none.

- [ ] **Step 1: Regenerate build + confirm dead code not re-injected.**
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python files/04_rebuild_demo.py 2>&1 | tail -1 && python _deploy_sync_specs.py 2>&1 | tail -1
echo -n "dead render fns in BUILT index (expect 0): "; grep -c "function renderPartsTiered(v){return\|function renderPartsTieredYT(v){return" wrench_deploy/index.html
echo -n "htmlEsc in build (expect 1): "; grep -c "function htmlEsc" wrench_deploy/index.html
```
Expected: dead fns `0` (the sentinel-guarded inject did NOT re-add them), htmlEsc `1`.

- [ ] **Step 2: Start a fresh preview server** (config `kyr-g4`, port 8741). `preview_start`, keep `serverId`.

- [ ] **Step 3: Re-run the golden harness** via `preview_eval`. `preview_console_logs` (error) → none.

- [ ] **Step 4: Assert identical to GOLDEN.** The returned `{len, hash}` MUST equal Task 1's GOLDEN (`72884 / -1768306184`).
  - Identical → output preserved, proceed.
  - Different → a conversion drifted output. Identify the differing tab/renderer, fix the offending conversion (or revert that one finding to inline), rebuild, restart preview, re-run from Step 1. Do NOT deploy until `{len, hash}` match exactly.

---

### Task 4: Deploy — controller-run

**Files:**
- Modify: `_deploy_sync_specs.py`

- [ ] **Step 1: Bump version.** Change `NEW_VER` default from `2026-06-10-refactor-v31` to `2026-06-10-refactor-v32`.

- [ ] **Step 2: Rebuild + sync + verify version.**
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python files/04_rebuild_demo.py 2>&1 | tail -1 && python _deploy_sync_specs.py 2>&1 | tail -1 && grep -o 'kyr-version" content="[^"]*"' wrench_deploy/index.html
```
Expected: `2026-06-10-refactor-v32`.

- [ ] **Step 3: Commit + push.**
```bash
git add wrench_demo.html wrench_deploy/index.html
git commit -m "refactor-v32: consolidate escapers + specNote/partRow helpers + remove dead code (no visual change)"
git push origin main
```

- [ ] **Step 4: Poll live.**
```bash
for i in $(seq 1 9); do V=$(curl -s "https://knowyourride.net/?cb=$(date +%s)$i" | grep -o 'content="2026-06-10-refactor-v32"'); if [ -n "$V" ]; then echo "LIVE (attempt $i)"; break; fi; sleep 10; done
```
Expected: `LIVE`.

- [ ] **Step 5: Manual confirmation (user).** Open a couple of vehicles, tab through the spec sections + a DTC code lookup + (if convenient) the "Watch It Done"/AI-guide buttons — confirm everything works and looks identical (this was a pure refactor).

---

## Self-Review

**Spec coverage:**
- #1 htmlEsc + 18 renames + delete 4 defs, keep ytEsc → Task 2 Step 1; grep gate Task 2 Step 7. ✓
- #2 specNote + 5 note rows + Top Issue 12 + leave-inline guard → Task 2 Step 2. ✓
- #3 partRow + 5 tables + leave-inline + headers untouched → Task 2 Step 3. ✓
- #4 delete dead render fns; not re-injected → Task 2 Step 4 + Task 3 Step 1 build grep. ✓
- #5 delete affRock/affAz → Task 2 Step 5; grep Task 2 Step 7. ✓
- #6 Object.assign clone → Task 2 Step 6. ✓
- Golden checksum 72884/-1768306184 captured before, asserted after → Task 1 + Task 3. ✓
- node --check + greps → Task 2 Step 7; build grep → Task 3 Step 1. ✓
- Deploy refactor-v32 → Task 4. ✓

**Placeholder scan:** none — exact helper code, exact deletions, exact commands, full harness. (GOLDEN is a runtime-captured value, recorded in Task 1 by design.)

**Type/name consistency:** `htmlEsc`, `specNote(l,v,sz)`, `partRow(x,extra)`, `renderPartsTieredYTG` (kept), `renderMaintGated`, golden `{len:72884,hash:-1768306184}`, version `2026-06-10-refactor-v32` — consistent across tasks. ✓
