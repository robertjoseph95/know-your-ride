# Fuel-Economy Version Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every fuel-economy line that matches an EPA record ships a label built from that record (EPA model name plus tags) and the card shows it under the drive line.

**Architecture:** Two pure modules in `files/` (EPA naming rules; label text) feed a new root script `_label_fuel_economy.py` that matches each stored line to EPA's complete file and writes two new columns. The build ships the label as one new `mpg` entry key, a template migration shows it on the card, and the verifier pins the entry shape and the label's provenance.

**Tech Stack:** Python 3 stdlib (`sqlite3`, `csv`, `zipfile`, `re`, `unittest`), the static page template `wrench_demo.html` (vanilla JS), the existing build `files/04_rebuild_demo.py` and verifier `_verify_shipped.py`.

**Spec:** `docs/superpowers/specs/2026-11-20-fuel-economy-version-labels-design.md` (approved by Robert 2026-11-20, "Approve design"). Read it with this plan.

## Global Constraints

- Source file: EPA `vehicles.csv.zip`, SHA-256 `1d553896a77898f6cf47128281337af268df053c90dc1365891c7c8abff82c82`, kept in a folder outside the repo and never committed. Untrusted data: its path is an argument, read into memory, exactly one member `vehicles.csv`, parsed as CSV only; every Python that reads it runs with `-I`. Downloading a fresh copy needs Robert's OK.
- Label text: `<names> · <tags>`; names = EPA `model` verbatim, unique, sorted alphabetically, joined `, `; no tags → names alone. Never shorten or reword EPA text.
- Tags, in this order, shown only if every record behind the line carries it: Hybrid (`atvType` = `Hybrid`), Plug-in hybrid (`Plug-in Hybrid`), Flex-fuel (`FFV`), Diesel (`Diesel`), CNG (`CNG`), Dual-fuel CNG (`Bifuel (CNG)`), Dual-fuel LPG (`Bifuel (LPG)`), Turbo (`tCharger` not empty), Supercharged (`sCharger` not empty).
- A tag is hidden only when its full text appears as whole words, ignoring case, in every name behind the line. Abbreviations and parts of words never hide a tag.
- Names kept: classes `own`, `performance version`, `hybrid or alternative fuel`, `longer or different body`, `special-purpose version`. Dropped: `another vehicle`, `performance model (N, already ruled out)`, `unrelated`. If every matching name would be dropped, keep them all.
- Database: new columns `fuel_economy.epa_ids` (EPA ids ascending, comma-separated) and `fuel_economy.epa_label`. Builder's convention (the spec leaves column semantics to the builder): assessed with no match → `epa_ids = ''`, `epa_label = NULL`; never assessed → both `NULL`. Neither column is named `source`.
- Shipped: `mpg` entry key `lbl` only when `epa_label` is non-empty. `mpg` entry keys allowed: `city, hwy, comb, cost, eng, trans, drive, range, mpge, lbl`. `epa_ids` never ships.
- Project rules: `python _verify_shipped.py` prints PASS before anything is staged; targeted `git add <path>` only, never the whole tree; `docs/shipped-surfaces-ledger.md` has unrelated uncommitted hunks, so stage only this work's hunks; canonical DB is root `wrench_vehicles.db` (never `files/wrench_vehicles.db`); bare owner-manual rows stay 424.
- Gates: nothing is committed or pushed until Robert's deploy go. The dry run (Task 6), the write (Task 7) and the deploy (Task 8) each run only on Robert's explicit go. A background-task notification is not a go.
- Tests: `unittest`, run with `python -m unittest discover -s tests -v` (CI runs the same). Tests that need `wrench_vehicles.db` or the EPA file skip with a reason when they are absent (CI has neither).

## Review Focus

1. Re-running the label script over already-labelled lines must change nothing → Task 5, `test_plan_is_empty_after_apply`.
2. A line written later by another script has no label: the card shows none and the verifier warns, never fails → Task 3, `test_build_omits_lbl_when_label_null`; Task 4, `test_unassessed_lines_warn_only`.
3. EPA names containing `&`, `<`, `/` or quotes must show as text, not markup → Task 3, `test_card_escapes_label`.
4. A line whose every matching name belongs to another vehicle still shows the true names → Task 2, `test_kept_records_falls_back_to_all`.
5. An electric line with no stored MPGe or range gets no label rather than a wrong one → Task 5, `test_electric_without_range_matches_nothing`.

---

### Task 1: EPA naming rules as an importable module

**Files:**
- Create: `files/epa_name_rules.py`
- Test: `tests/test_fe_labels.py` (new; holds the tests of Tasks 1–5)

**Interfaces:**
- Produces: `name_classes(year: int, make: str, model: str, recs: list[dict], plates: dict[str, set[str]]) -> tuple[dict[str, str], bool]` — `recs` need keys `name`, `atv`; returns EPA name → class, and whether a plain name exists. `fleet_plates(cur) -> dict[str, set[str]]` — make → every model in `vehicles`, any year.

- [ ] **Step 1: Write the failing tests**

```python
def classes(mk, md, names, plates):
    return epa_name_rules.name_classes(2016, mk, md, [{"name": n, "atv": a} for n, a in names], plates)[0]

def test_silverado_spellings(self):
    c = classes("Chevrolet", "Silverado 1500", [("Silverado C15 2WD", ""), ("Silverado K15 4WD", ""),
        ("Silverado C15 Cab Chassis 2WD", ""), ("Silverado 15 Hybrid 2WD", "Hybrid"), ("Tahoe C1500 2WD", "")],
        {"Chevrolet": {"Silverado 1500", "Tahoe"}})
    self.assertEqual(c, {"Silverado C15 2WD": "own", "Silverado K15 4WD": "own", "Silverado C15 Cab Chassis 2WD": "own",
                         "Silverado 15 Hybrid 2WD": "hybrid or alternative fuel", "Tahoe C1500 2WD": "unrelated"})

def test_yukon_xl_depends_on_fleet(self):
    names = [("Yukon 2WD", ""), ("Yukon XL 2WD", "")]
    self.assertEqual(classes("GMC", "Yukon", names, {"GMC": {"Yukon"}})["Yukon XL 2WD"], "longer or different body")
    self.assertEqual(classes("GMC", "Yukon", names, {"GMC": {"Yukon", "Yukon XL"}})["Yukon XL 2WD"], "another vehicle")

def test_kona_n_ruled_out(self):
    self.assertEqual(classes("Hyundai", "Kona", [("Kona FWD", ""), ("Kona N", "")], {"Hyundai": {"Kona"}})["Kona N"],
                     "performance model (N, already ruled out)")
```

Plus `test_rules_equal_comparison_script` (skips unless `wrench_vehicles.db` exists and env `KYR_EPA_ZIP` names the EPA file): for every fleet vehicle with EPA records of its make and year, `name_classes` equals the classes produced by executing `_compare_fuel_economy_epa.py`'s two rule parts (the text from the `name rules` marker to the `EPA's file` marker, and from `def name_classes(` to `key_rec = lambda`) with a `plates` global.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m unittest tests.test_fe_labels -v`
Expected: FAIL / ERROR, `No module named 'epa_name_rules'`.

- [ ] **Step 3: Create `files/epa_name_rules.py`**

Copy the two rule parts of `_compare_fuel_economy_epa.py` verbatim (word sets, `ALIAS` … `ORDER`, `words` … `num`, and `name_classes`), with one change: `name_classes` takes `plates` as its last parameter instead of reading a module global, and drops the unused `vid` parameter. Add `fleet_plates(cur)`. No file or database access at import.

- [ ] **Step 4: Run to verify they pass**

Run: `python -m unittest tests.test_fe_labels -v`, then locally with the file: `KYR_EPA_ZIP=<zip path> python -m unittest tests.test_fe_labels -v`
Expected: PASS; the equivalence test runs locally and skips in CI.

### Task 2: Label text

**Files:**
- Create: `files/fe_labels.py`
- Test: `tests/test_fe_labels.py`

**Interfaces:**
- Consumes: class strings from Task 1.
- Produces: `TAGS: tuple[tuple[str, Callable[[dict], bool]], ...]`; `KEEP_CLASSES: frozenset[str]`; `kept_records(recs: list[dict], classes: dict[str, str]) -> list[dict]`; `label_text(recs: list[dict]) -> str`; `ids_text(recs: list[dict]) -> str`. A record dict carries at least `id: int`, `name: str`, `atv: str`, `tcharger: str`, `scharger: str`.

- [ ] **Step 1: Write the failing tests**

```python
R = lambda i, n, atv="", t="", s="": {"id": i, "name": n, "atv": atv, "tcharger": t, "scharger": s}

def test_xc90_tags(self):
    self.assertEqual(fe_labels.label_text([R(1, "XC90 AWD", t="T")]), "XC90 AWD · Turbo")
    self.assertEqual(fe_labels.label_text([R(2, "XC90 AWD", t="T", s="S")]), "XC90 AWD · Turbo, Supercharged")
    self.assertEqual(fe_labels.label_text([R(3, "XC90 AWD PHEV", "Plug-in Hybrid", "T", "S")]),
                     "XC90 AWD PHEV · Plug-in hybrid, Turbo, Supercharged")

def test_names_sorted_and_merged(self):
    self.assertEqual(fe_labels.label_text([R(5, "Mustang Mach 1"), R(4, "Mustang Convertible")]),
                     "Mustang Convertible, Mustang Mach 1")
    self.assertEqual(fe_labels.ids_text([R(5, "a"), R(4, "b"), R(5, "a")]), "4,5")

def test_tag_needs_every_record(self):
    self.assertEqual(fe_labels.label_text([R(6, "Silverado C15 2WD", "FFV"), R(7, "Silverado C15 2WD")]), "Silverado C15 2WD")

def test_tag_hidden_only_by_whole_words(self):
    self.assertEqual(fe_labels.label_text([R(8, "Camry Hybrid LE", "Hybrid")]), "Camry Hybrid LE")
    self.assertEqual(fe_labels.label_text([R(9, "911 Turbo S", t="T")]), "911 Turbo S")
    self.assertEqual(fe_labels.label_text([R(10, "Pacifica Hybrid", "Plug-in Hybrid")]), "Pacifica Hybrid · Plug-in hybrid")
    self.assertEqual(fe_labels.label_text([R(11, "Wrangler 4dr EcoDiesel 4WD", "Diesel")]), "Wrangler 4dr EcoDiesel 4WD · Diesel")

def test_kept_records_drops_other_vehicles(self):
    recs = [R(12, "Silverado C15 2WD"), R(13, "Tahoe C1500 2WD")]
    self.assertEqual([r["id"] for r in fe_labels.kept_records(recs, {"Silverado C15 2WD": "own", "Tahoe C1500 2WD": "unrelated"})], [12])

def test_kept_records_falls_back_to_all(self):
    recs = [R(14, "4Runner Hybrid 4WD", "Hybrid")]
    self.assertEqual(fe_labels.kept_records(recs, {"4Runner Hybrid 4WD": "another vehicle"}), recs)
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m unittest tests.test_fe_labels -v` — Expected: ERROR, `No module named 'fe_labels'`.

- [ ] **Step 3: Implement `files/fe_labels.py`**

The separator is ` · ` (space, U+00B7, space). Whole-word hiding: a case-insensitive search for the tag text bounded by non-alphanumerics, required in every name.

- [ ] **Step 4: Run to verify they pass** — `python -m unittest tests.test_fe_labels -v`, Expected: PASS.

### Task 3: The build ships `lbl` and the card shows it

**Files:**
- Modify: `files/04_rebuild_demo.py` — the `fuel_economy` loop in `build_data` (around line 498–511); new constants beside `_DIFF_JS_OLD` (line 146); `main()` beside `html.replace(_DIFF_JS_OLD, …)` (line 2029) and its assert (line 2038).
- Test: `tests/test_fe_labels.py`

**Interfaces:**
- Consumes: column `fuel_economy.epa_label` when it exists.
- Produces: `mpg` entries gain `"lbl": <epa_label>` when non-empty; `migrate_mpg_label(html: str) -> str` (idempotent) in `files/04_rebuild_demo.py`; page class `mpg-ver`.

- [ ] **Step 1: Write the failing tests**

- `test_mpg_label_migration_idempotent`: load `files/04_rebuild_demo.py` with `importlib`; read `wrench_demo.html`; `once = migrate_mpg_label(html)`; assert `migrate_mpg_label(once) == once`, `once.count('<div class="mpg-ver">') == 1`, `once.count(".mpg-ver{") == 1`, and the old card string `<div class="mpg-dr">'+(m.drive||'')+'</div></div>'` is absent from `once`.
- `test_card_escapes_label`: the migrated card contains `'+htmlEsc(m.lbl)+'` and does not contain `'+m.lbl+'` (the label never enters the markup unescaped).
- `test_build_ships_lbl` (skips without `wrench_vehicles.db`): back the DB up into memory, add the two columns, set `epa_label = 'X · Turbo'` and `epa_ids = '1'` on one line of vehicle 11447, run `build_data`; that vehicle's entry for the line has `lbl == 'X · Turbo'`, its other entries have no `lbl`, and no other vehicle changes.
- `test_build_omits_lbl_when_label_null`: same fixture, no label set → no `mpg` entry anywhere has `lbl`; also passes when the columns do not exist.

- [ ] **Step 2: Run to verify they fail** — Expected: `AttributeError: … has no attribute 'migrate_mpg_label'`, and no `lbl` key.

- [ ] **Step 3: Implement**

Build: in the `fuel_economy` loop, `if "epa_label" in fe_cols and r["epa_label"]: e["lbl"] = r["epa_label"]`.

Template migration, exact strings:
- card old: `<div class="mpg-dr">'+(m.drive||'')+'</div></div>'`
- card new: `<div class="mpg-dr">'+(m.drive||'')+'</div>'+(m.lbl?'<div class="mpg-ver">'+htmlEsc(m.lbl)+'</div>':'')+'</div>'`
- style old: `.mpg-dr{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--dim)}`
- style new: the old rule followed by `\n.mpg-ver{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--dim);margin-top:2px;overflow-wrap:anywhere}`

The new style text contains the old, so `migrate_mpg_label` replaces only when `.mpg-ver{` is absent. Call it in `main()` next to the differential-fluids migration and assert afterwards: card old absent, card new once, `.mpg-ver{` once. Check that `fix_js_quotes` leaves both new strings unchanged.

- [ ] **Step 4: Run to verify they pass** — `python -m unittest tests.test_fe_labels -v`, Expected: PASS (the DB tests skip in CI).

### Task 4: Verifier checks and ledger

**Files:**
- Modify: `_verify_shipped.py` — new functions after `s1_12_no_process_jargon` (line 247); entries in `CHECKS` (line 1734).
- Modify: `docs/shipped-surfaces-ledger.md` — section S1 (line 16).
- Test: `tests/test_fe_labels.py`

**Interfaces:**
- Produces: `MPG_ENTRY_KEYS = {"city","hwy","comb","cost","eng","trans","drive","range","mpge","lbl"}`; `s1_13_mpg_entry_shape(a) -> list[str]` (FAIL, CI); `s1_14_label_provenance(a) -> list[str]` (FAIL, DB); `s1_15_unassessed_lines(a) -> list[str]` (WARN, DB). `a` is the verifier's artefact object (`a.D["v"]`, `a.db_path`).

- [ ] **Step 1: Write the failing tests** (artefact stand-in: `types.SimpleNamespace(D={"v": [...]})`)

- `test_entry_shape_ok`: one vehicle, `mpg=[{"city":1,"hwy":2,"comb":3,"lbl":"A · Turbo"}]` → `[]`.
- `test_entry_shape_rejects`: an entry with key `epa_ids` → one message; `lbl == ""` → one message; `lbl` of 401 characters → one message.
- `test_label_provenance` (temporary SQLite file with a `fuel_economy` table): a row with `epa_label='A'` and `epa_ids=''` → one message; with `epa_ids='5'` → `[]`; table without the columns → `[]`.
- `test_unassessed_lines_warn_only`: rows with `epa_ids IS NULL` → one message naming the count; the entry in `CHECKS` has tier `WARN`.

- [ ] **Step 2: Run to verify they fail** — Expected: `AttributeError` for the missing functions.

- [ ] **Step 3: Implement**

`s1_13`: every `mpg` entry's keys lie in `MPG_ENTRY_KEYS`; `lbl`, where present, is a non-empty `str` of at most 400 characters (the jargon scan of S1.12 already walks `mpg` strings). `s1_14`: if both columns exist, no row has a non-empty `epa_label` with `epa_ids` NULL or empty. `s1_15`: if the columns exist, report the count of rows with `epa_ids IS NULL`. Register: `("S1.13-mpg-entry-shape","FAIL","CI",…)`, `("S1.14-label-provenance","FAIL","DB",…)`, `("S1.15-unassessed-lines","WARN","DB",…)`.

Ledger S1: add the three invariants in the section's style, and name `_label_fuel_economy.py` as the generator of `lbl` text (via `fuel_economy.epa_label`).

- [ ] **Step 4: Run to verify they pass** — `python -m unittest tests.test_fe_labels -v` and `python _verify_shipped.py` (PASS; S1.14 and S1.15 report nothing while the columns do not exist yet).

### Task 5: The label script

**Files:**
- Create: `_label_fuel_economy.py` (repo root; pattern: `_repair_fuel_economy_every_record.py`)
- Test: `tests/test_fe_labels.py`

**Interfaces:**
- Consumes: `epa_name_rules.name_classes`, `epa_name_rules.fleet_plates`, `fe_labels.kept_records`, `fe_labels.label_text`, `fe_labels.ids_text`; the build's `build_data`, `_strip_unverified`, `_assert_registry_admission`, `assert_frozen_landscape`, `_assert_ic01_projection` (as the every-record script loads them).
- Produces:
  - `load_epa(path: str) -> dict[tuple[int, str], list[dict]]` — key `(year, make.lower())`; record dicts carry `id, year, make, name, atv, city, hwy, comb, displ (float), trans, drive, range, tcharger, scharger, eng_dscr, vclass, startstop, trans_dscr, engid`. Refuses any file whose SHA-256 is not the pinned one.
  - `match_line(line: dict, recs: list[dict]) -> list[dict]` — `line` keys `city_mpg, highway_mpg, combined_mpg, engine, transmission, drive, fuel_type, mpge, range_miles`. A line with `fuel_type == "Electric"` matches records typed `EV` or `FCV` with `comb == mpge`, `range == range_miles`, equal transmission and drive; any other line matches on city, highway, combined, engine size (as float), transmission and drive.
  - `ensure_columns(cur) -> list[str]` — adds `epa_ids TEXT`, `epa_label TEXT` when absent; returns the names added.
  - `plan_labels(cur, epa: dict, plates: dict) -> list[dict]` — one item per line whose computed `(epa_ids, epa_label)` differs from what is stored: `{"fe_id", "vehicle_id", "old": [ids, label], "new": [ids, label]}`; no match → `new = ["", None]`.
  - `apply(cur, plan: list[dict]) -> None` — `UPDATE … WHERE id=? AND vehicle_id=? AND epa_ids IS ? AND epa_label IS ?`, each `rowcount == 1`.
  - CLI: `python -I _label_fuel_economy.py <zip>` (dry run: plan, report, rehearsal, save `_label_fuel_economy_plan_cache.json`, print sha256) and `python -I _label_fuel_economy.py --write --sha <sha>` (backup `wrench_vehicles.db.bak_fe_labels_<timestamp>`, `ensure_columns`, `apply`, re-read check, bare rows 424, fleet unchanged).

- [ ] **Step 1: Write the failing tests** (pure fixtures and an in-memory SQLite with minimal `vehicles` and `fuel_economy` tables)

- `test_gas_line_matches_six_fields`: a line `20/27/23, "2.0", "Automatic (S8)", "All-Wheel Drive"` matches a record with `displ 2.0` and those figures, and not one with `comb 24`.
- `test_electric_line_matches_mpge_and_range`: a line with `fuel_type "Electric"`, `mpge 110`, `range_miles 256` matches an `EV` record with `comb 110, range 256` and the same transmission and drive; a gasoline record with the same numbers does not match.
- `test_electric_without_range_matches_nothing`: same line with `range_miles None` → `[]`.
- `test_plan_is_empty_after_apply`: fixture fleet of two vehicles, three lines, a fake `epa` dict; `ensure_columns`, `apply(plan_labels(...))`, then `plan_labels` again returns `[]`.
- `test_unmatched_line_marked_assessed`: a line with no matching record plans `new == ["", None]`.

- [ ] **Step 2: Run to verify they fail** — Expected: ERROR, the script module is missing.

- [ ] **Step 3: Implement `_label_fuel_economy.py`**

Rehearsal (as in `_repair_fuel_economy_every_record.py::rehearse`): two in-memory copies; on the second, `ensure_columns` and `apply`; build both; only vehicles in the plan differ, only in `mpg`; each changed entry differs only by `lbl`; each shipped `lbl` equals the planned label for its line (lines ship in row order); vehicle count, verified count and bare rows unchanged.

The dry-run report goes to `_fe_labels_dry_run_<YYYY-MM-DD>.md` (repo root, local only, never staged) and holds:
- lines labelled, lines assessed without a match, electric lines labelled
- look-alike groups (spec definition) told apart, against the spec's 924 of 1,154
- the leftover groups with the first separating EPA field in the order `eng_dscr`, `vclass`, `startstop`, `trans_dscr`, `engid`, else "no EPA field" or "a line matches no EPA record"
- the longest label, and the count of labels that S1.12's jargon pattern would flag

A jargon hit, a hash mismatch or a failed rehearsal stops the run with no plan saved. A count that differs from the spec is reported, not stopped.

- [ ] **Step 4: Run to verify they pass** — `python -m unittest tests.test_fe_labels -v`, Expected: PASS.

### Task 6: GATE A — label dry run (only on Robert's go)

- [ ] **Step 1:** `python -m unittest discover -s tests -v` — Expected: all PASS (DB and EPA-file tests may skip only where noted).
- [ ] **Step 2:** `python -I _label_fuel_economy.py <zip path>` — Expected: rehearsal passes, plan sha256 printed, report written, jargon hits 0, the database file's modification time unchanged.
- [ ] **Step 3:** Present the report to Robert (counts against the spec, leftover groups, longest label, sample labels for the 2020 XC90, 2016 Silverado 1500, 2016 Camry, 2021 Mustang). **PAUSE** for his write go.

### Task 7: GATE B — write, rebuild, preview (only on Robert's go)

- [ ] **Step 1:** `python -I _label_fuel_economy.py --write --sha <sha from Task 6>` — Expected: backup path printed, counts as planned.
- [ ] **Step 2:** Compare the database with the backup table by table: only `fuel_economy` differs, only in `epa_ids` and `epa_label`, only on planned line ids.
- [ ] **Step 3:** `python files/04_rebuild_demo.py` — Expected: gates pass, the label migration assert holds.
- [ ] **Step 4:** Compare the rebuilt data with the deployed data: only planned vehicles differ, only by `lbl` keys equal to the plan.
- [ ] **Step 5:** `python _verify_shipped.py` — Expected: PASS (S1.15 reports 0 unassessed lines).
- [ ] **Step 6:** Preview `kyr-demo` (port 8752) with a fresh cache-buster: the label line shows under the drive line on the 2009 and 2016 Silverado 1500, the 2024 Escalade and the 2020 XC90, at desktop and phone width; no console errors beyond the preview's known font and service-worker 404s. **PAUSE** for Robert's deploy go.

### Task 8: GATE C — deploy and record (only on Robert's go)

- [ ] **Step 1:** Fix the header of `_repair_fuel_economy_every_record.py`: replace "On 18 of those rows the nameplate is a hybrid itself (Prius and similar)." with the measured fact: on 18 of those rows every own record of that year is typed Hybrid — 5 are hybrid-only models (Prius 2020–2022 and 2026, RAV4 2026) and 13 are 48-volt mild hybrids (BMW, RAM 1500 2024).
- [ ] **Step 2:** `KYR_NEW_VER=<YYYY-MM-DD>-fe-labels python _deploy_sync_specs.py`, then `python _verify_shipped.py` — Expected: PASS.
- [ ] **Step 3:** Targeted add, then `git show --stat HEAD` after the commit:

```bash
git add files/epa_name_rules.py files/fe_labels.py files/04_rebuild_demo.py _verify_shipped.py tests/test_fe_labels.py \
        _label_fuel_economy.py _compare_fuel_economy_epa.py _repair_fuel_economy_every_record.py \
        wrench_deploy/data.<new>.js wrench_deploy/index.html wrench_demo.html
git diff docs/shipped-surfaces-ledger.md > <scratch>/ledger_all.patch   # keep only this work's S1 hunks in a copy:
git apply --cached <scratch>/ledger_fe_labels.patch                       # then confirm with git diff --cached
git rm --cached -q wrench_deploy/data.cf95fb96.js
git commit -q -F <message file ending "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>">
```

The design and this plan are committed only if Robert says so (the repo is public).
- [ ] **Step 4:** Push; live check in the background (version tag, live blob md5 equals the committed blob, old blob 404, every planned label read back); CI green.
- [ ] **Step 5:** Docs: the source map's fuel-economy note, `vision.md`, memory; governance snapshot (`refresh.py`, inspect, credential scan, push, remote matches); stop the preview.
