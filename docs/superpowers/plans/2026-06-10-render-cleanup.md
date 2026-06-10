# Render-layer Cleanup (Step 2 — specRow) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** DRY the 39 repeated `spec-item` blocks in the spec-modal renderers behind one `specRow()` helper, with provably byte-identical rendered output.

**Architecture:** Add one helper that emits the exact current `spec-item` string; replace the simple/uniform spec-item emissions with `specRow()` calls across the modal render functions; leave non-uniform note rows, tables, and wrapper chains untouched. A golden-output checksum (captured before the edit, re-checked after) guarantees zero output change.

**Tech Stack:** Vanilla JS in a single file (`wrench_demo.html`), built to `wrench_deploy/index.html` via `files/04_rebuild_demo.py` + `_deploy_sync_specs.py`. No test runner — verification is a `preview_eval` golden checksum + `node --check`.

---

## Testing approach (read first)

The success criterion is **byte-identical rendered output**. The test is a checksum captured on the current build **before any code change** (Task 1), then re-captured after the refactor (Task 3) and asserted equal. The controller holds the Task 1 golden value and compares in Task 3. `node --check` guards JS syntax per code task.

**The golden harness** (same expression used in Task 1 and Task 3):
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

## File structure

- **Modify:** `wrench_demo.html` — add `specRow` near the other render helpers (right after `function fmt(`); replace uniform `spec-item` emissions in the modal renderers.
- **Modify:** `_deploy_sync_specs.py` — bump `NEW_VER` (Task 4).
- **Generated:** `wrench_deploy/index.html` — produced by the build; not hand-edited.

---

### Task 1: Capture the golden output checksum (BEFORE any edit) — controller-run

**Files:** none (measurement only). Run as controller; record the result.

- [ ] **Step 1: Ensure the build is current (lightpaper-v30, unchanged).** No code edits yet. Confirm:
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && grep -o 'kyr-version" content="[^"]*"' wrench_deploy/index.html
```
Expected: `2026-06-10-lightpaper-v30`.

- [ ] **Step 2: Start a fresh preview server.** Add a config named `kyr-gold` on a free port (e.g. 8738, `runtimeArgs ["-m","http.server","8738","--directory","wrench_deploy"]`) to `.claude/launch.json` (stop a stale server first if at the 5-server cap via `preview_list`/`preview_stop`). `preview_start` name `kyr-gold`; keep the `serverId`.

- [ ] **Step 3: Run the golden harness** (the expression in "Testing approach") via `preview_eval`. **RECORD the returned `{len, hash, picks}`** — this is the golden value Task 3 must match. Also run `preview_console_logs` (error) → expect none.

- [ ] **Step 4: Record the golden value** in the task tracker / controller notes (e.g. `GOLDEN = {len: <n>, hash: <h>, picks: [<ids>]}`). No commit (nothing changed).

---

### Task 2: Extract `specRow` and convert the uniform rows — implementer: code-simplifier agent

**Files:**
- Modify: `wrench_demo.html` (render helpers + modal renderers)

Dispatch the **code-simplifier agent** for this task (per the design — this DRY is its wheelhouse), with the scope below. It must NOT alter any emitted string, and must NOT touch tables, wrapper chains, or non-uniform note rows.

- [ ] **Step 1: Add the helper.** Find the line `function fmt(v,sfx){return v===null||v===undefined?'&mdash;':v+(sfx||'');}` (the `fmt` helper near the modal renderers — if the exact body differs, find `function fmt(`). Immediately AFTER that function's closing `}`, add:
```js
function specRow(l,v,c){return '<div class="spec-item"><div class="sp-l">'+l+'</div><div class="sp-v'+(c?' '+c:'')+'">'+v+'</div></div>';}
```

- [ ] **Step 2: Convert ONLY the uniform spec-item emissions.** Across the modal render functions (`renderOil`, `renderEV`, `renderParts`, `renderFluids`, `renderPerf`, `renderSafety`, and any other using `spec-item`), replace emissions of this exact shape:
```
'<div class="spec-item"><div class="sp-l">LABEL</div><div class="sp-v">VALUE</div></div>'
'<div class="spec-item"><div class="sp-l">LABEL</div><div class="sp-v ac">VALUE</div></div>'
'<div class="spec-item"><div class="sp-l">LABEL</div><div class="sp-v gr">VALUE</div></div>'
'<div class="spec-item"><div class="sp-l">LABEL</div><div class="sp-v rd">VALUE</div></div>'
```
with, respectively:
```
specRow(LABEL, VALUE)
specRow(LABEL, VALUE, 'ac')
specRow(LABEL, VALUE, 'gr')
specRow(LABEL, VALUE, 'rd')
```
where `LABEL` and `VALUE` are the exact existing JS sub-expressions (e.g. `'Viscosity'` and `fmt(o.visc)` → `specRow('Viscosity', fmt(o.visc), 'ac')`). The string concatenation must reproduce the identical output.

**DO NOT convert** (leave exactly as-is): any `spec-item` that has `style="grid-column:1/-1"` on the item, OR a `style="..."` attribute on the `.sp-v` (the full-width note rows: "Notes", "Trim Variants", "Battery Notes", "Timing Notes", "Oil Interval Notes", and similar). DO NOT touch `<table class="tbl">` scaffolds, wrapper functions (`renderOilShop`, `renderPartsTieredYTG`, `renderMaintGated`, `renderWarrantyKbb`, etc.), or anything outside `spec-item` rows.

- [ ] **Step 3: Syntax check (against wrench_demo.html source).**
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python -c "import re;html=open('wrench_demo.html',encoding='utf-8').read();ds=html.find('const __D__=');de=html.find('</script>',ds);html=html[:ds]+'const __D__={v:[],dtc:{},fixes:{},fuseTsbsByCode:{}};'+html[de:];b=re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',html,re.S);open('_sc.js','w',encoding='utf-8').write('\n;\n'.join(b))" && node --check _sc.js && echo "NODE OK" && rm -f _sc.js
```
Expected: `NODE OK`.

- [ ] **Step 4: Report the count of conversions** (how many `specRow(` call sites now exist):
```bash
grep -c 'specRow(' wrench_demo.html
```
Report the number (expected roughly 30–39; some of the 39 measured may be note rows that are correctly left out).

- [ ] **Step 5: Commit (do NOT push, wrench_demo.html ONLY).**
```bash
git add wrench_demo.html
git commit -m "refactor: extract specRow() helper for uniform spec-item rows"
```

---

### Task 3: Golden verification — controller-run (GATE)

**Files:** none (verification only).

- [ ] **Step 1: Regenerate the build.**
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python files/04_rebuild_demo.py 2>&1 | tail -1 && python _deploy_sync_specs.py 2>&1 | tail -1
```

- [ ] **Step 2: Start a fresh preview server** (e.g. name `kyr-gold2`, port 8739, same `--directory wrench_deploy`; stop a stale one if at the cap). `preview_start`, keep `serverId`.

- [ ] **Step 3: Re-run the golden harness** (the SAME expression from "Testing approach") via `preview_eval`. `preview_console_logs` (error) → expect none.

- [ ] **Step 4: Assert identical.** Compare the returned `{len, hash, picks}` to the GOLDEN recorded in Task 1. **They MUST be identical** (same `len`, same `hash`, same `picks` ids).
  - If identical → output preserved, proceed.
  - If different → a conversion drifted the output. Diff the offending renderer (the changed tab will differ), fix the converted site so it emits the original string exactly (re-dispatch the code-simplifier agent with the specific mismatch, or fix the one site), rebuild, restart a fresh preview, re-run from Step 1. Do NOT deploy until `{len, hash}` match the golden exactly.

---

### Task 4: Deploy — controller-run

**Files:**
- Modify: `_deploy_sync_specs.py`

- [ ] **Step 1: Bump version.** In `_deploy_sync_specs.py`, change `NEW_VER` default from `2026-06-10-lightpaper-v30` to `2026-06-10-refactor-v31`.

- [ ] **Step 2: Rebuild + sync + verify version.**
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python files/04_rebuild_demo.py 2>&1 | tail -1 && python _deploy_sync_specs.py 2>&1 | tail -1 && grep -o 'kyr-version" content="[^"]*"' wrench_deploy/index.html
```
Expected: `kyr-version" content="2026-06-10-refactor-v31"`.

- [ ] **Step 3: Commit + push.**
```bash
git add wrench_demo.html wrench_deploy/index.html
git commit -m "refactor-v31: specRow() helper for spec rows (no visual change)"
git push origin main
```

- [ ] **Step 4: Poll live until deployed.**
```bash
for i in $(seq 1 9); do V=$(curl -s "https://knowyourride.net/?cb=$(date +%s)$i" | grep -o 'content="2026-06-10-refactor-v31"'); if [ -n "$V" ]; then echo "LIVE (attempt $i)"; break; fi; sleep 10; done
```
Expected: `LIVE`.

- [ ] **Step 5: Manual confirmation (user).** Open a couple of vehicles on `knowyourride.net`, tab through the spec sections — confirm everything looks exactly as before (no visual change; this was a pure refactor).

---

## Self-Review

**Spec coverage:**
- `specRow` helper (exact emit) → Task 2 Step 1. ✓
- Convert only uniform rows; leave note rows/tables/chains → Task 2 Step 2 (explicit convert/leave rules). ✓
- Golden-output checksum, captured BEFORE edit, asserted after → Task 1 (capture) + Task 3 (assert). ✓
- ICE-with-recalls / EV / rich-maint self-selection, all 9 tabs → harness in "Testing approach". ✓
- node --check + no console errors → Task 2 Step 3, Task 1/3 console checks. ✓
- code-simplifier agent does the extraction, scoped → Task 2 dispatch note + explicit DO-NOT rules. ✓
- Deploy refactor-v31 → Task 4. ✓
- Reversible → revert the commit (inherent). ✓

**Placeholder scan:** none — exact helper, exact convert/leave rules, exact commands, full harness code. (The golden `{len,hash}` is a runtime-captured value by design — Task 1 records it; this is data, not a plan placeholder.)

**Type/name consistency:** `specRow(l,v,c)` signature and the `'ac'/'gr'/'rd'` class args consistent across Task 2; harness identical in Task 1 and Task 3; version `2026-06-10-refactor-v31` consistent in Task 4. ✓
