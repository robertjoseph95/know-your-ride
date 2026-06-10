# Light-paper Modal (Step 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the vehicle spec modal body on a warm cream "manual page" surface (dark ink, ruled cells, section marks) while the dark header + chapter tabs stay as the binder.

**Architecture:** CSS-only + a one-word markup change. The modal body is fully CSS-variable-driven, so adding `paper` to the body's class and one scoped `.m-body.paper { … }` block (remapping ~12 color vars + a few structural overrides) re-themes the entire subtree. A second small block overrides the handful of hardcoded-dark embedded blocks. Render functions are NOT edited.

**Tech Stack:** Vanilla JS/CSS in a single file (`wrench_demo.html`), built to `wrench_deploy/index.html` via `files/04_rebuild_demo.py` + `_deploy_sync_specs.py`. No test runner — verification is `node --check` (syntax) + `preview_eval` (computed styles, in-page WCAG contrast, dark-island scan) via the Claude_Preview MCP.

---

## Testing approach (read first)

This change is CSS + one HTML class, so `node --check` only confirms the JS wasn't accidentally broken; it cannot validate the visual. The real verification is **Task 3** (`preview_eval`): it opens the modal, iterates all nine tabs, computes WCAG contrast ratios in-page for the ink-on-cream pairs, and scans every modal descendant for a dark background ("dark island"). Code tasks 1–2 end with a build + `grep` marker check + commit; behavioral verification is consolidated in Task 3 (one rebuild + one fresh preview server).

Build + node --check helper (run from repo root after a code task):
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python files/04_rebuild_demo.py 2>&1 | tail -1
python -c "import re;html=open('wrench_demo.html',encoding='utf-8').read();ds=html.find('const __D__=');de=html.find('</script>',ds);html=html[:ds]+'const __D__={v:[],dtc:{},fixes:{},fuseTsbsByCode:{}};'+html[de:];b=re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',html,re.S);open('_sc.js','w',encoding='utf-8').write('\n;\n'.join(b))" && node --check _sc.js && echo "NODE OK" && rm -f _sc.js
```

## File structure

- **Modify:** `wrench_demo.html` — one markup class change (modal body) and CSS added to the existing head `<style>` block. No new files, no render-function edits.
- **Modify:** `_deploy_sync_specs.py` — bump `NEW_VER` (Task 4).
- **Generated:** `wrench_deploy/index.html` — produced by the build; not hand-edited.

---

### Task 1: Apply the `paper` class + the main scoped CSS block

**Files:**
- Modify: `wrench_demo.html` (modal body markup + head `<style>`)

- [ ] **Step 1: Add `paper` to the modal body class.** Find this exact line:

```
    <div class="m-body" id="m-body"></div>
```

Replace with:

```
    <div class="m-body paper" id="m-body"></div>
```

- [ ] **Step 2: Add the scoped CSS block.** Find this exact rule in the head `<style>`:

```
.m-body{padding:22px;max-height:72vh;overflow-y:auto}
```

Replace with that rule followed by the paper block:

```
.m-body{padding:22px;max-height:72vh;overflow-y:auto}
.m-body.paper{--panel:#e3dccb;--p2:#ddd5c0;--p3:#d3cab2;--border:#c3bca9;--b2:#a89f88;--text:#1b1e23;--dim:#5f5848;--faint:#8a8268;--accent:#b8500a;--a2:#8a5a14;--red:#a3380f;--green:#1f6b3a;--purple:#5b3a8a;background:#ece6d8;color:#1b1e23}
.m-body.paper .spec-item{background:transparent;border:0;border-bottom:1px solid var(--border);border-radius:0;padding:8px 2px}
.m-body.paper .recall-card,.m-body.paper .wty-card,.m-body.paper .mpg-row,.m-body.paper .pt-card{background:transparent;border:1px solid var(--border);border-radius:2px}
.m-body.paper .sec-head::before{content:"\00A7 ";color:var(--accent);font-weight:700}
```

- [ ] **Step 3: Build + marker check.**

Run:
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python files/04_rebuild_demo.py 2>&1 | tail -1
echo -n "paper class: "; grep -c 'class="m-body paper"' wrench_demo.html
echo -n "paper css block: "; grep -c '.m-body.paper{--panel:#e3dccb' wrench_demo.html
```
Expected: `paper class: 1` and `paper css block: 1`.

- [ ] **Step 4: Syntax check (JS untouched, confirm not broken).**

Run the node --check helper from "Testing approach". Expected: `NODE OK`.

- [ ] **Step 5: Commit.**

```bash
git add wrench_demo.html
git commit -m "lightpaper task1: scope .m-body.paper var-remap + ruled-cell structure"
```

---

### Task 2: Override the hardcoded-dark embedded blocks

**Files:**
- Modify: `wrench_demo.html` (head `<style>`)

Background: `.gh-banner` (AI-guide notice) and `.gh-safety` (safety warning) use hardcoded dark backgrounds that the var-remap does not catch, so on the cream page they would be dark islands. Add light overrides.

- [ ] **Step 1: Add the override rules.** Find this line (added in Task 1):

```
.m-body.paper .sec-head::before{content:"\00A7 ";color:var(--accent);font-weight:700}
```

Replace with that line followed by the overrides:

```
.m-body.paper .sec-head::before{content:"\00A7 ";color:var(--accent);font-weight:700}
.m-body.paper .gh-banner{background:#efe2c4;border-color:#b88a2e;color:#5a3d0a}
.m-body.paper .gh-safety{background:#f3dcd2;border-color:var(--red);color:#7a2a0c}
```

- [ ] **Step 2: Build + marker check.**

Run:
```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python files/04_rebuild_demo.py 2>&1 | tail -1
echo -n "gh-banner override: "; grep -c '.m-body.paper .gh-banner{background:#efe2c4' wrench_demo.html
echo -n "gh-safety override: "; grep -c '.m-body.paper .gh-safety{background:#f3dcd2' wrench_demo.html
```
Expected: both `1`.

- [ ] **Step 3: Commit.**

```bash
git add wrench_demo.html
git commit -m "lightpaper task2: light overrides for hardcoded-dark gh-banner/gh-safety"
```

---

### Task 3: Runtime verification (fresh preview + preview_eval)

**Files:** none (verification only). Run as controller.

- [ ] **Step 1: Regenerate canonical index.html.** Tasks 1–2 committed only `wrench_demo.html`; regenerate the build:

```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python files/04_rebuild_demo.py 2>&1 | tail -1 && python _deploy_sync_specs.py 2>&1 | tail -1
```

- [ ] **Step 2: Start a fresh preview server.** Add a config named `kyr-lp` on a new port (e.g. 8737, `runtimeArgs ["-m","http.server","8737","--directory","wrench_deploy"]`) to `.claude/launch.json`, then `mcp__Claude_Preview__preview_start` name `kyr-lp`; keep the `serverId`. Check `preview_console_logs` (error) → expect none.

- [ ] **Step 3: Run the contrast + dark-island sweep across all 9 tabs.**

`preview_eval` with this expression (uses a vehicle with rich data; 12802 = 2020 Camry, has recalls):
```js
(function(){
  function toRGB(c){c=(c||'').trim();if(c[0]==='#'){var h=c.slice(1);if(h.length===3)h=h.split('').map(function(x){return x+x;}).join('');return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)];}var m=c.match(/[\d.]+/g);return m?[+m[0],+m[1],+m[2]]:null;}
  function lum(c){var r=toRGB(c);if(!r)return null;var a=r.map(function(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});return 0.2126*a[0]+0.7152*a[1]+0.0722*a[2];}
  function contrast(fg,bg){var L1=lum(fg),L2=lum(bg);if(L1==null||L2==null)return null;var hi=Math.max(L1,L2),lo=Math.min(L1,L2);return Math.round(((hi+0.05)/(lo+0.05))*100)/100;}
  openModal('12802');
  var mb=document.getElementById('m-body');
  var cs=getComputedStyle(mb);
  var cream='#ece6d8';
  var ratios={
    text:contrast(cs.getPropertyValue('--text'),cream),
    dim:contrast(cs.getPropertyValue('--dim'),cream),
    faint:contrast(cs.getPropertyValue('--faint'),cream),
    accent:contrast(cs.getPropertyValue('--accent'),cream),
    red:contrast(cs.getPropertyValue('--red'),cream),
    green:contrast(cs.getPropertyValue('--green'),cream),
    a2:contrast(cs.getPropertyValue('--a2'),cream)
  };
  var bodyBg=cs.backgroundColor;
  var tabs=['oil','parts','fluids','maint','perf','safety','issues','warranty','comps'];
  var islands={};
  tabs.forEach(function(t){
    switchMTab(t,12802);
    var els=document.querySelectorAll('#m-body *');
    var dark=[];
    els.forEach(function(el){
      var bg=getComputedStyle(el).backgroundColor;
      if(bg==='rgba(0, 0, 0, 0)'||bg==='transparent')return;
      var L=lum(bg);
      if(L!=null&&L<0.22&&el.offsetWidth>40&&el.offsetHeight>10){dark.push(el.className||el.tagName);}
    });
    if(dark.length)islands[t]=Array.from(new Set(dark)).slice(0,6);
  });
  return {bodyBg:bodyBg, ratios:ratios, darkIslands:islands};
})()
```

**Expected / pass criteria:**
- `bodyBg` is the cream (`rgb(236, 230, 216)`).
- `ratios.text`, `.dim`, `.red`, `.green`, `.a2` are **≥ 4.5**; `ratios.accent` and `ratios.faint` are **≥ 3.0** (accent is used on large `.rel-score-big`; faint is small-label text — aim ≥ 4.5, accept ≥ 3.0 only for the large-text uses). If any required pair is below threshold, darken that token in the Task 1 CSS block (e.g. `--faint` → `#756c52`, `--accent` → `#a8470a`), rebuild, restart a fresh preview server, re-run.
- `darkIslands` is **empty `{}`**. If a tab lists a class, add a scoped light override for that class to the Task 2 block (same pattern as `.gh-banner`), rebuild, re-verify. (`.yt-thumb` may appear — it is the image well behind a thumbnail; if it shows, override `.m-body.paper .yt-thumb{background:#d3cab2}`.)

- [ ] **Step 4: Confirm no console errors** (`preview_console_logs` error → none) and, best-effort, `preview_screenshot` the modal for a visual sanity look (may time out on the 31 MB page — not blocking).

- [ ] **Step 5: Gate.** Do NOT proceed to deploy until `bodyBg` is cream, all contrast thresholds pass, and `darkIslands` is empty. Any fix loops back through Task 1 or Task 2 then re-runs this task.

---

### Task 4: Deploy

**Files:**
- Modify: `_deploy_sync_specs.py`

- [ ] **Step 1: Bump version.** In `_deploy_sync_specs.py`, change the `NEW_VER` default from `2026-06-10-deeplink2-v29` to `2026-06-10-lightpaper-v30`.

- [ ] **Step 2: Rebuild + sync + verify version.**

```bash
cd "C:/Users/Robert/OneDrive/Desktop/Wrench App Data" && python files/04_rebuild_demo.py 2>&1 | tail -1 && python _deploy_sync_specs.py 2>&1 | tail -1 && grep -o 'kyr-version" content="[^"]*"' wrench_deploy/index.html
```
Expected: `kyr-version" content="2026-06-10-lightpaper-v30"`

- [ ] **Step 3: Commit + push.**

```bash
git add wrench_demo.html wrench_deploy/index.html
git commit -m "lightpaper-v30: spec modal renders on a cream manual-page surface"
git push origin main
```

- [ ] **Step 4: Poll live until deployed.**

```bash
for i in $(seq 1 9); do V=$(curl -s "https://knowyourride.net/?cb=$(date +%s)$i" | grep -o 'content="2026-06-10-lightpaper-v30"'); if [ -n "$V" ]; then echo "LIVE (attempt $i)"; break; fi; sleep 10; done
```
Expected: `LIVE`

- [ ] **Step 5: Manual confirmation (user).** On `knowyourride.net`: open several vehicles (an ICE car, an EV, one with recalls), tab through all sections — confirm each reads as a cream manual page with legible ink, the dark header/tabs remain the binder, and nothing is an unreadable dark island.

---

## Self-Review

**Spec coverage:**
- Whole-body uniform paper via scoped var-remap → Task 1 Step 2. ✓
- Markup class change → Task 1 Step 1. ✓
- 12-var light remap (exact values) → Task 1 Step 2 CSS. ✓
- Burnt-orange accent `#b8500a` → in the Task 1 var block; contrast-gated in Task 3. ✓
- Structural ruled cells, grid kept, `§` mark → Task 1 Step 2. ✓
- Hardcoded-dark block overrides (`.gh-banner`, `.gh-safety`) → Task 2; other blocks caught by the Task 3 dark-island scan with a documented fix path. ✓
- Verification: all 9 tabs, computed bg/color, WCAG contrast in-page, dark-island scan, console errors → Task 3. ✓
- Reversible (class toggle) → inherent (drop `paper`). ✓
- Version bump `lightpaper-v30`, same pipeline → Task 4. ✓
- Render functions untouched / Step 2 cleanup out of scope → no task edits a render function. ✓

**Placeholder scan:** none — exact strings, exact CSS, exact commands, full eval code.

**Type/name consistency:** class `m-body paper`, selector `.m-body.paper`, override classes `.gh-banner`/`.gh-safety`/`.yt-thumb`, vars `--panel/--p2/--p3/--border/--b2/--text/--dim/--faint/--accent/--a2/--red/--green/--purple` used consistently across Tasks 1–3. Version string `2026-06-10-lightpaper-v30` consistent in Task 4. ✓
