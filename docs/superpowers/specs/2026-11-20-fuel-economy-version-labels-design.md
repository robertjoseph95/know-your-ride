# Fuel-economy version labels: design

Date: 2026-11-20. Status: approved by Robert 2026-11-20 and deployed the same day (commit `0ffb831f`, live as
`2026-11-20-fe-labels`). The plan is `docs/superpowers/plans/2026-11-20-fuel-economy-version-labels.md`.

## Why

Each fuel-economy card on a vehicle page shows engine size, transmission and drive, then the
city / highway / combined figures and a yearly fuel cost. EPA tells its records apart by model
name and fuel type, but the database never kept either. So different versions look alike: a hybrid
line reads like the plain engine with better mileage, and a coupe line looks like a duplicate of
the sedan with different figures.

Measured on 2026-11-20 against EPA's complete file: 1,154 groups of cards on 665 vehicles (183 of
them verified) show two or more different sets of figures under one identical card label. Before
the every-own-record fill (deploy `cb4deda3`) it was 958 groups on 617 vehicles.

The open ruling on performance, hybrid and body-style versions (item c) depends on this. A version
shown without a label misleads the reader; a version removed loses figures its owners need.
Labels come first (Robert, 2026-11-20, "Yes, labels first").

## What Robert decided

- **The label is EPA's model name plus tags** (2026-11-20, "EPA name plus tags"). The words come
  from EPA's own record, as EPA prints them. No wording of ours.

## Goals

1. Every fuel-economy line that matches an EPA record carries a label built from that record.
2. Cards that look alike today show different labels wherever EPA's name, fuel type or
   turbo / supercharger flag differs. Measured: 924 of the 1,154 look-alike groups.
3. Each label can be traced to the EPA record ids behind it.
4. The verifier proves the shipped label key is allowed and well formed.

## Non-goals

- Changing which lines a vehicle shows. That is ruling (c), which comes after this.
- The search-result card (it shows the first line's combined figure and stays as it is).
- SEO pages, the paid-guide input (`specs.json`), the API functions and the `ev` summary card.
  None of them reads fuel-economy lines today, and none will.
- Refreshing yearly fuel costs (item d).

## Anti-goals (a failure even if it works)

- Any label word that does not come from EPA's record.
- A tag that is not true of every EPA record behind the line.
- A label on a line that matches no EPA record.
- Shortening or rewording EPA's model name. The distinguishing word may be the one cut.
- Internal provenance (record ids) or process notes in the shipped data.

## Constraints

- The data rule: a shipped value needs a government or manufacturer source. EPA fueleconomy.gov is
  the source for fuel economy. The source is EPA's complete file `vehicles.csv.zip`, last modified
  by EPA 2026-11-04, SHA-256 `1d553896a77898f6cf47128281337af268df053c90dc1365891c7c8abff82c82`,
  already validated against 3,647 records pulled one by one from EPA's web service. The file is
  untrusted data: kept in its own folder, its path passed as an argument, read in memory, one
  member only, parsed as CSV, any Python that reads it run with `-I`.
- Tier 1 stays static over SQLite with no runtime service.
- `python _verify_shipped.py` must print PASS before anything is staged; staging is targeted
  (`git add <path>`), never the whole tree. `docs/shipped-surfaces-ledger.md` carries unrelated
  uncommitted hunks: stage only this work's hunks.
- Every step is paused for Robert: label dry run, write, preview, deploy.

## How a label is built

### Which EPA records stand behind a line

- **Gasoline-type lines** (every line whose `fuel_type` is not `Electric`): the EPA records of the
  same make and model year whose six fields equal the line's: city, highway and combined figures,
  engine size, transmission, drive. This is the matching every fuel-economy repair since
  2026-11-15 has used.
- **Electric lines**: matched the way the full comparison matches them: combined figure, range,
  transmission and drive, on EPA records typed `EV` or `FCV`.
- **Which of those names the label keeps** follows the full comparison's naming rules, used
  unchanged. They live in `_compare_fuel_economy_epa.py` (repo root; a copy of the comparison script
  of 2026-11-15/20, everything above the line `res, empties = [], []`: the word sets, the fourteen
  EPA spellings in `OTHER_SPELLING`, and `name_classes()`). The label script carries the same rules.
  A "fleet nameplate" there is any (make, model) in `vehicles`, in any year.
  - Kept: names classed as the vehicle's own, or as one of its versions: performance version,
    hybrid or alternative fuel, longer or different body, special-purpose version.
  - Dropped: names classed as another vehicle, as a performance model already ruled out (the
    Hyundai N models), or as unrelated. That includes vehicles outside the fleet, such as
    Silverado LD or Van 1500.
  - Exception: if every matching name would be dropped, the label shows them. It is the truth
    about that line, and such a line is already on the open repair list (today one Tacoma 2026
    line that equals a 4Runner Hybrid record).
  - Examples: a Tahoe record with the same figures on a Silverado 1500 line is dropped; a Yukon XL
    record on a Yukon line is kept, because the fleet has no Yukon XL and the rules class it as
    the Yukon's longer body.
- No match: no label.

### The label text

`<names> · <tags>`

- **Names**: EPA's `model` field of every record behind the line, verbatim, without duplicates,
  sorted alphabetically, joined with `, `. Example: `430i xDrive Coupe, 430i xDrive Gran Coupe`.
- **Tags**, in this order, each shown only if every record behind the line carries it:

  | Tag | EPA field and value |
  |---|---|
  | Hybrid | `atvType` = `Hybrid` |
  | Plug-in hybrid | `atvType` = `Plug-in Hybrid` |
  | Flex-fuel | `atvType` = `FFV` |
  | Diesel | `atvType` = `Diesel` |
  | CNG | `atvType` = `CNG` |
  | Dual-fuel CNG | `atvType` = `Bifuel (CNG)` |
  | Dual-fuel LPG | `atvType` = `Bifuel (LPG)` |
  | Turbo | `tCharger` not empty |
  | Supercharged | `sCharger` not empty |

- A tag is not repeated when its full text already appears, as a whole word or words and
  ignoring case, in every name behind the line (`Civic Hybrid`, not `Civic Hybrid · Hybrid`;
  `911 Turbo S` without a Turbo tag). Abbreviations and parts of words do not count: `PHEV`,
  `FFV`, `SC` and `EcoDiesel` hide nothing, so `Pacifica Hybrid`, typed Plug-in Hybrid by EPA,
  reads `Pacifica Hybrid · Plug-in hybrid`.
- No tags: the label is the names alone, without the separator.

Examples, computed by this rule from today's data and EPA's file:

| Vehicle | Card label today (identical on each card) | Version labels |
|---|---|---|
| 2020 Volvo XC90 | 2.0L · Automatic (S8), All-Wheel Drive (3 cards) | `XC90 AWD · Turbo` / `XC90 AWD · Turbo, Supercharged` / `XC90 AWD PHEV · Plug-in hybrid, Turbo, Supercharged` |
| 2016 Chevrolet Silverado 1500 | 5.3L · Automatic 8-spd, Rear-Wheel Drive | `Silverado 15 Hybrid 2WD` / `Silverado C15 2WD` |
| 2016 Toyota Camry | 2.5L · Automatic (variable gear ratios), Front-Wheel Drive | `Camry Hybrid LE` / `Camry Hybrid XLE/SE` |
| 2025 Toyota 4Runner | 2.4L · Automatic (S8), 4-Wheel Drive | `4Runner 4WD · Turbo` / `4Runner 4WD · Hybrid, Turbo` |
| 2021 Ford Mustang | 2.3L · Manual 6-spd, Rear-Wheel Drive | `Mustang · Turbo` / `Mustang Convertible · Turbo` |
| 2020 BMW 430i | 2.0L · Automatic (S8), All-Wheel Drive | `430i xDrive Convertible · Turbo` / `430i xDrive Coupe, 430i xDrive Gran Coupe · Turbo` |

Two cases the rule handles on purpose:
- A line whose figures equal records under two names lists both: the 2021 Mustang's 5.0L
  automatic line reads `Mustang Convertible, Mustang Mach 1`.
- A tag appears only if every record behind the line carries it. The 2016 Silverado 1500's
  5.3L 6-speed line matches a plain and a flex-fuel record with the same figures, so it reads
  `Silverado C15 2WD` with no Flex-fuel tag.

## Where it lives

- **Database**: two new columns on `fuel_economy`: `epa_ids` (the EPA record ids behind the line,
  ascending, comma-separated) and `epa_label` (the label text). Both empty where nothing matches.
  `epa_ids` is provenance and never ships.
- **Label script**: a new `_label_fuel_economy.py`, built like `_repair_fuel_economy_every_record.py`:
  pinned file hash, dry run by default, a saved plan with its sha256, a rehearsal of the real build
  on in-memory copies (only `mpg` entries may change, and only by gaining the label), then
  `--write --sha` with a backup. It is re-runnable: a later run labels lines written since and
  leaves a matching label unchanged.
- **Build** (`files/04_rebuild_demo.py`): each `mpg` entry gains `"lbl": <epa_label>` when the
  label is not empty; the key is absent otherwise.
- **Card** (`renderPerf` in the page template): the label shows as a third line in the card's
  left block, under the drive line, in the same small monospace style. Applied as an idempotent
  template migration in the build's `main()` with an assert, the pattern the differential-fluids
  fix uses (`_DIFF_JS_OLD` / `_DIFF_JS_NEW`). Text is escaped before it is inserted.
- **Verifier** (`_verify_shipped.py`): a new check that every `mpg` entry's keys lie in
  {city, hwy, comb, cost, eng, trans, drive, range, mpge, lbl}; that `lbl`, where present, is a
  non-empty string with no forbidden process words; and that no `epa_ids` key ships. A database-
  tier check: every non-empty `epa_label` has non-empty `epa_ids`. The count of lines without a
  label is reported, not failed.
- **Ledger** (`docs/shipped-surfaces-ledger.md`, section S1): the new invariants and the label
  script as a generator of the shipped text.

## My calls (Robert can overrule any)

1. The label shows on every card, also where the row has only one line. Same rule everywhere, no
   hidden logic about when it appears.
2. Tags are limited to fuel type and turbo / supercharger. EPA's engine notes (stop-start,
   cylinder deactivation) would separate 219 more look-alike groups but lengthen every label; left
   out for now.
3. Several matching names are all listed, in alphabetical order, never shortened.
4. Labels also go on lines of unruled kinds (performance, hybrid, body style). Seeing what they
   are is the point before ruling on them.
5. Electric lines get a label too, by the comparison's electric matching.
6. Existing write scripts are not changed now. After any future fuel-economy write, the label
   script is re-run; until then the new line simply has no label, and the verifier reports it.
7. A name of another vehicle is dropped from a label whenever a name of the vehicle itself or one
   of its versions also matches (rules above).
8. A tag is hidden only by its full text as whole words in every name; abbreviations never hide it.
9. The measured counts are reported against, not pinned as stop points.

## What success looks like

The numbers below were measured on 2026-11-20 with the comparison script and the same EPA file.
They are checks the dry run reports against, not stop points: a different count is shown to
Robert with its cause, and the dry run stops only on an integrity failure (file hash, a label word
not taken from EPA, a change outside the `lbl` key in the rehearsal).

A **look-alike group** is a set of lines on one vehicle with identical card text (engine size,
transmission, drive) and two or more different sets of city / highway / combined figures. Lines
that differ only in yearly cost are not a group. Electric lines were not part of the measurement.

- The dry run labels every line that matches EPA (today 7,893 gasoline-type lines plus the
  electric lines) and none that does not (26 today).
- At least 924 of the 1,154 look-alike groups show different labels. The rest are listed by
  vehicle with the first EPA field that does tell them apart, checked in this order: `eng_dscr`
  (engine notes), `VClass`, `startStop`, `trans_dscr`, `engId` (EPA's internal engine code); or
  "no EPA field" (5 today) or "a line matches no EPA record" (6 today).
- The rehearsal shows only `mpg` entries changing, by the `lbl` key only.
- The preview shows labels on, at least, the 2009 Silverado 1500, the 2016 Silverado 1500, the
  2024 Escalade and the 2020 XC90.
- Verifier PASS; the live blob carries the labels after deploy.

## Left to the builder

- Column types and the exact migration statement.
- The CSS for the label line, within the card's existing look.
- The verifier check's number and the ledger wording.
- Plan file layout, dry-run report layout and test fixtures.
