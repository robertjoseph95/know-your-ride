"""Fuel-economy version labels: tests for the naming rules, the label text, the build key, the
verifier checks and the label script (plan docs/superpowers/plans/2026-11-20-fuel-economy-version-labels.md).

Expectations are literals taken from the approved design and from running the full comparison's
own rules on the same fixtures; they never import the data under test. Tests that need the
canonical wrench_vehicles.db or EPA's complete file (env KYR_EPA_ZIP) skip when either is absent,
as in CI. No test writes to a real database file.

    python -m unittest discover -s tests -v
"""
import collections
import csv
import io
import os
import sqlite3
import sys
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FILES_DIR = os.path.join(ROOT, "files")
for p in (ROOT, FILES_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

DB = os.path.join(ROOT, "wrench_vehicles.db")
COMPARE = os.path.join(ROOT, "_compare_fuel_economy_epa.py")
EPA_ZIP = os.environ.get("KYR_EPA_ZIP", "")


def _classes(mk, md, names, plates):
    import epa_name_rules
    return epa_name_rules.name_classes(2016, mk, md, [{"name": n, "atv": a} for n, a in names], plates)[0]


class TestNameRules(unittest.TestCase):
    def test_silverado_spellings(self):
        c = _classes("Chevrolet", "Silverado 1500", [("Silverado C15 2WD", ""), ("Silverado K15 4WD", ""),
                     ("Silverado C15 Cab Chassis 2WD", ""), ("Silverado 15 Hybrid 2WD", "Hybrid"), ("Tahoe C1500 2WD", "")],
                     {"Chevrolet": {"Silverado 1500", "Tahoe"}})
        self.assertEqual(c, {"Silverado C15 2WD": "own", "Silverado K15 4WD": "own", "Silverado C15 Cab Chassis 2WD": "own",
                             "Silverado 15 Hybrid 2WD": "hybrid or alternative fuel", "Tahoe C1500 2WD": "unrelated"})

    def test_yukon_xl_depends_on_fleet(self):
        names = [("Yukon 2WD", ""), ("Yukon XL 2WD", "")]
        self.assertEqual(_classes("GMC", "Yukon", names, {"GMC": {"Yukon"}})["Yukon XL 2WD"], "longer or different body")
        self.assertEqual(_classes("GMC", "Yukon", names, {"GMC": {"Yukon", "Yukon XL"}})["Yukon XL 2WD"], "another vehicle")

    def test_kona_n_ruled_out(self):
        self.assertEqual(_classes("Hyundai", "Kona", [("Kona FWD", ""), ("Kona N", "")], {"Hyundai": {"Kona"}})["Kona N"],
                         "performance model (N, already ruled out)")

    @unittest.skipUnless(os.path.exists(DB) and EPA_ZIP and os.path.exists(EPA_ZIP) and os.path.exists(COMPARE),
                         "needs wrench_vehicles.db, KYR_EPA_ZIP and _compare_fuel_economy_epa.py (local only)")
    def test_rules_equal_comparison_script(self):
        import epa_name_rules
        src = io.open(COMPARE, encoding="utf-8").read()
        a = src.index("# ---------------------------------------------------------------- name rules")
        b = src.index("# ---------------------------------------------------------------- EPA's file")
        c = src.index("def name_classes(")
        d = src.index("key_rec = lambda")
        g = {"__name__": "compare_rules"}
        exec(compile("import re, collections\n" + src[a:b] + src[c:d], COMPARE, "exec"), g)
        z = zipfile.ZipFile(EPA_ZIP)
        recs = collections.defaultdict(list)
        for r in csv.DictReader(io.StringIO(z.read("vehicles.csv").decode("utf-8", "replace"))):
            recs[(int(r["year"]), r["make"].strip().lower())].append({"name": r["model"].strip(), "atv": r["atvType"].strip()})
        con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
        try:
            vehicles = con.execute("SELECT id, year, make, model FROM vehicles ORDER BY id").fetchall()
            plates = epa_name_rules.fleet_plates(con.cursor())
        finally:
            con.close()
        g["plates"] = collections.defaultdict(set, plates)
        checked = 0
        for vid, yr, mk, md in vehicles:
            rr = recs.get((yr, mk.lower()))
            if not rr:
                continue
            want = g["name_classes"](vid, yr, mk, md, rr)
            got = epa_name_rules.name_classes(yr, mk, md, rr, plates)
            self.assertEqual(got, want, "%d %s %s %s" % (vid, yr, mk, md))
            checked += 1
        self.assertGreater(checked, 3000)


def R(i, n, atv="", t="", s=""):
    return {"id": i, "name": n, "atv": atv, "tcharger": t, "scharger": s}


class TestLabelText(unittest.TestCase):
    def setUp(self):
        import fe_labels
        self.fl = fe_labels

    def test_xc90_tags(self):
        self.assertEqual(self.fl.label_text([R(1, "XC90 AWD", t="T")]), "XC90 AWD · Turbo")
        self.assertEqual(self.fl.label_text([R(2, "XC90 AWD", t="T", s="S")]), "XC90 AWD · Turbo, Supercharged")
        self.assertEqual(self.fl.label_text([R(3, "XC90 AWD PHEV", "Plug-in Hybrid", "T", "S")]),
                         "XC90 AWD PHEV · Plug-in hybrid, Turbo, Supercharged")

    def test_names_sorted_and_merged(self):
        self.assertEqual(self.fl.label_text([R(5, "Mustang Mach 1"), R(4, "Mustang Convertible")]),
                         "Mustang Convertible, Mustang Mach 1")
        self.assertEqual(self.fl.ids_text([R(5, "a"), R(4, "b"), R(5, "a")]), "4,5")

    def test_tag_needs_every_record(self):
        self.assertEqual(self.fl.label_text([R(6, "Silverado C15 2WD", "FFV"), R(7, "Silverado C15 2WD")]), "Silverado C15 2WD")

    def test_tag_hidden_only_by_whole_words(self):
        self.assertEqual(self.fl.label_text([R(8, "Camry Hybrid LE", "Hybrid")]), "Camry Hybrid LE")
        self.assertEqual(self.fl.label_text([R(9, "911 Turbo S", t="T")]), "911 Turbo S")
        self.assertEqual(self.fl.label_text([R(10, "Pacifica Hybrid", "Plug-in Hybrid")]), "Pacifica Hybrid · Plug-in hybrid")
        self.assertEqual(self.fl.label_text([R(11, "Wrangler 4dr EcoDiesel 4WD", "Diesel")]), "Wrangler 4dr EcoDiesel 4WD · Diesel")

    def test_kept_records_drops_other_vehicles(self):
        recs = [R(12, "Silverado C15 2WD"), R(13, "Tahoe C1500 2WD")]
        kept = self.fl.kept_records(recs, {"Silverado C15 2WD": "own", "Tahoe C1500 2WD": "unrelated"})
        self.assertEqual([r["id"] for r in kept], [12])

    def test_kept_records_falls_back_to_all(self):
        recs = [R(14, "4Runner Hybrid 4WD", "Hybrid")]
        self.assertEqual(self.fl.kept_records(recs, {"4Runner Hybrid 4WD": "another vehicle"}), recs)


def _load_build():
    import importlib.util
    spec = importlib.util.spec_from_file_location("kyr_build_04_test", os.path.join(FILES_DIR, "04_rebuild_demo.py"))
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    return b


CARD_OLD = "<div class=\"mpg-dr\">'+(m.drive||'')+'</div></div>'"


class TestCardMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = _load_build()
        with open(os.path.join(ROOT, "wrench_demo.html"), "rb") as f:
            cls.html = f.read().decode("utf-8")

    def test_mpg_label_migration_idempotent(self):
        once = self.b.migrate_mpg_label(self.html)
        self.assertEqual(self.b.migrate_mpg_label(once), once)
        self.assertEqual(once.count('<div class="mpg-ver">'), 1)
        self.assertEqual(once.count(".mpg-ver{"), 1)
        self.assertNotIn(CARD_OLD, once)
        self.assertEqual(self.b.fix_js_quotes(once).count('<div class="mpg-ver">'), 1)
        self.assertEqual(self.b.fix_js_quotes(once).count(".mpg-ver{"), 1)

    def test_card_escapes_label(self):
        once = self.b.migrate_mpg_label(self.html)
        self.assertIn("'+htmlEsc(m.lbl)+'", once)
        self.assertNotIn("'+m.lbl+'", once)


@unittest.skipUnless(os.path.exists(DB), "needs wrench_vehicles.db (local only)")
class TestBuildLabel(unittest.TestCase):
    VID = 11447
    LABEL = "X · Turbo"

    @classmethod
    def _build(cls, columns, label_line=None):
        src = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
        mem = sqlite3.connect(":memory:")
        src.backup(mem)
        src.close()
        # Start every variant from the pre-label schema, whatever the canonical database holds today.
        if {r[1] for r in mem.execute("PRAGMA table_info(fuel_economy)")} >= {"epa_ids", "epa_label"}:
            for (trigger,) in mem.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'fe_label_%'").fetchall():
                mem.execute('DROP TRIGGER "%s"' % trigger)
            mem.execute("ALTER TABLE fuel_economy DROP COLUMN epa_label")
            mem.execute("ALTER TABLE fuel_economy DROP COLUMN epa_ids")
        if columns:
            mem.execute("ALTER TABLE fuel_economy ADD COLUMN epa_ids TEXT")
            mem.execute("ALTER TABLE fuel_economy ADD COLUMN epa_label TEXT")
        if label_line:
            mem.execute("UPDATE fuel_economy SET epa_ids='1', epa_label=? WHERE id=?", (cls.LABEL, label_line))
        mem.row_factory = sqlite3.Row
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            vlist = cls.b.build_data(mem.cursor())[0]
        mem.close()
        return {v["id"]: v for v in vlist}

    @classmethod
    def setUpClass(cls):
        cls.b = _load_build()
        con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
        cls.lines = [r[0] for r in con.execute("SELECT id FROM fuel_economy WHERE vehicle_id=? ORDER BY id", (cls.VID,))]
        con.close()
        cls.target = cls.lines[1]
        cls.plain = cls._build(False)
        cls.empty = cls._build(True)
        cls.labelled = cls._build(True, cls.target)

    def test_build_omits_lbl_when_label_null(self):
        for data in (self.plain, self.empty):
            self.assertFalse(any("lbl" in m for v in data.values() for m in (v.get("mpg") or [])))
        self.assertEqual(self.plain, self.empty)

    def test_build_ships_lbl(self):
        changed = [i for i in self.labelled if self.labelled[i] != self.empty[i]]
        self.assertEqual(changed, [self.VID])
        mpg = self.labelled[self.VID]["mpg"]
        self.assertEqual(len(mpg), len(self.lines))
        self.assertEqual([m.get("lbl") for m in mpg], [self.LABEL if i == self.target else None for i in self.lines])


def _verifier():
    import _verify_shipped
    return _verify_shipped


def _fe_db(path, columns, rows):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE fuel_economy (id INTEGER PRIMARY KEY, vehicle_id INTEGER, city_mpg INTEGER%s)"
                % (", epa_ids TEXT, epa_label TEXT" if columns else ""))
    for r in rows:
        con.execute("INSERT INTO fuel_economy VALUES (%s)" % ",".join("?" * len(r)), r)
    con.commit()
    con.close()


class TestVerifierChecks(unittest.TestCase):
    def setUp(self):
        import tempfile
        import types
        self.vs = _verifier()
        self.ns = types.SimpleNamespace
        self.tmp = tempfile.mkdtemp(prefix="kyr_fe_labels_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _a(self, *mpg):
        return self.ns(D={"v": [{"id": 1, "mpg": list(mpg)}]})

    def test_entry_shape_ok(self):
        self.assertEqual(self.vs.s1_13_mpg_entry_shape(self._a({"city": 1, "hwy": 2, "comb": 3, "lbl": "A · Turbo"})), [])

    def test_entry_shape_rejects(self):
        self.assertEqual(len(self.vs.s1_13_mpg_entry_shape(self._a({"city": 1, "epa_ids": "5"}))), 1)
        self.assertEqual(len(self.vs.s1_13_mpg_entry_shape(self._a({"city": 1, "lbl": ""}))), 1)
        self.assertEqual(len(self.vs.s1_13_mpg_entry_shape(self._a({"city": 1, "lbl": "x" * 401}))), 1)

    def test_label_provenance(self):
        bad, good, none = (os.path.join(self.tmp, n) for n in ("bad.db", "good.db", "none.db"))
        _fe_db(bad, True, [(1, 1, 20, "", "A")])
        _fe_db(good, True, [(1, 1, 20, "5", "A")])
        _fe_db(none, False, [(1, 1, 20)])
        self.assertEqual(len(self.vs.s1_14_label_provenance(self.ns(db_path=bad))), 1)
        self.assertEqual(self.vs.s1_14_label_provenance(self.ns(db_path=good)), [])
        self.assertEqual(self.vs.s1_14_label_provenance(self.ns(db_path=none)), [])

    def test_unassessed_lines_warn_only(self):
        path = os.path.join(self.tmp, "warn.db")
        _fe_db(path, True, [(1, 1, 20, None, None), (2, 1, 21, None, None), (3, 1, 22, "", None)])
        out = self.vs.s1_15_unassessed_lines(self.ns(db_path=path))
        self.assertEqual(len(out), 1)
        self.assertIn("2", out[0])
        tiers = {cid: tier for cid, tier, _venue, _fn in self.vs.CHECKS}
        self.assertEqual(tiers["S1.15-unassessed-lines"], "WARN")
        self.assertEqual(tiers["S1.13-mpg-entry-shape"], "FAIL")
        self.assertEqual(tiers["S1.14-label-provenance"], "FAIL")


def E(i, name, city, hwy, comb, displ, trans, drive, atv="", rng=None, t="", s=""):
    """An EPA record as _label_fuel_economy.load_epa returns it (report-only fields left empty)."""
    return {"id": i, "year": 0, "make": "", "name": name, "atv": atv, "city": city, "hwy": hwy, "comb": comb,
            "displ": displ, "trans": trans, "drive": drive, "range": rng, "tcharger": t, "scharger": s,
            "eng_dscr": "", "vclass": "", "startstop": "", "trans_dscr": "", "engid": ""}


def L(city, hwy, comb, engine, trans, drive, fuel_type=None, mpge=None, rng=None):
    return {"city_mpg": city, "highway_mpg": hwy, "combined_mpg": comb, "engine": engine, "transmission": trans,
            "drive": drive, "fuel_type": fuel_type, "mpge": mpge, "range_miles": rng}


AWD8 = ("Automatic (S8)", "All-Wheel Drive")
EV_ROW = (None, None, None, None, "Automatic (A1)", "All-Wheel Drive", "Electric", 113, 353)


class TestLabelScript(unittest.TestCase):
    EPA = {(2020, "volvo"): [E(101, "XC90 AWD", 20, 27, 23, 2.0, *AWD8, t="T"),
                             E(102, "XC90 AWD", 18, 26, 21, 2.0, *AWD8, t="T", s="S")],
           (2021, "tesla"): [E(201, "Model 3 Long Range AWD", None, None, 113, None, "Automatic (A1)", "All-Wheel Drive",
                               atv="EV", rng=353)]}
    PLATES = {"Volvo": {"XC90"}, "Tesla": {"Model 3"}}

    def setUp(self):
        import _label_fuel_economy
        self.lf = _label_fuel_economy

    def _fleet(self):
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE vehicles (id INTEGER PRIMARY KEY, year INTEGER, make TEXT, model TEXT)")
        con.execute("CREATE TABLE fuel_economy (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, city_mpg INTEGER, "
                    "highway_mpg INTEGER, combined_mpg INTEGER, annual_fuel_cost INTEGER, engine TEXT, transmission TEXT, "
                    "drive TEXT, range_miles INTEGER, mpge INTEGER, fuel_type TEXT)")
        con.executemany("INSERT INTO vehicles VALUES (?,?,?,?)", [(1, 2020, "Volvo", "XC90"), (2, 2021, "Tesla", "Model 3")])
        rows = [(1, 20, 27, 23, 2.0, *AWD8, None, None, None), (1, 18, 26, 21, 2.0, *AWD8, None, None, None),
                (1, 30, 30, 30, 2.0, *AWD8, None, None, None),
                (2, None, None, None, None, "Automatic (A1)", "All-Wheel Drive", 353, 113, "Electric")]
        con.executemany("INSERT INTO fuel_economy (vehicle_id, city_mpg, highway_mpg, combined_mpg, engine, transmission, "
                        "drive, range_miles, mpge, fuel_type) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        [(r[0], r[1], r[2], r[3], str(r[4]) if r[4] is not None else None, r[5], r[6], r[7], r[8], r[9])
                         for r in rows])
        con.commit()          # an open write transaction would block Connection.backup() forever
        return con

    def test_gas_line_matches_six_fields(self):
        recs = [E(1, "A", 20, 27, 23, 2.0, *AWD8), E(2, "B", 20, 27, 24, 2.0, *AWD8)]
        self.assertEqual([r["id"] for r in self.lf.match_line(L(20, 27, 23, "2.0", *AWD8), recs)], [1])

    def test_electric_line_matches_mpge_and_range(self):
        recs = [E(3, "EV", None, None, 110, None, "Automatic (A1)", "All-Wheel Drive", atv="EV", rng=256),
                E(4, "Gas", None, None, 110, None, "Automatic (A1)", "All-Wheel Drive", rng=256)]
        line = L(None, None, None, None, "Automatic (A1)", "All-Wheel Drive", "Electric", 110, 256)
        self.assertEqual([r["id"] for r in self.lf.match_line(line, recs)], [3])

    def test_electric_without_range_matches_nothing(self):
        recs = [E(3, "EV", None, None, 110, None, "Automatic (A1)", "All-Wheel Drive", atv="EV", rng=256)]
        line = L(None, None, None, None, "Automatic (A1)", "All-Wheel Drive", "Electric", 110, None)
        self.assertEqual(self.lf.match_line(line, recs), [])

    def test_plan_labels_values(self):
        con = self._fleet()
        plan = self.lf.plan_labels(con.cursor(), self.EPA, self.PLATES)
        self.assertEqual([(p["fe_id"], p["old"], p["new"]) for p in plan],
                         [(1, [None, None], ["101", "XC90 AWD · Turbo"]),
                          (2, [None, None], ["102", "XC90 AWD · Turbo, Supercharged"]),
                          (3, [None, None], ["", None]),
                          (4, [None, None], ["201", "Model 3 Long Range AWD"])])

    def test_unmatched_line_marked_assessed(self):
        con = self._fleet()
        plan = {p["fe_id"]: p for p in self.lf.plan_labels(con.cursor(), self.EPA, self.PLATES)}
        self.assertEqual(plan[3]["new"], ["", None])

    def test_plan_is_empty_after_apply(self):
        con = self._fleet()
        cur = con.cursor()
        self.assertEqual(self.lf.ensure_columns(cur), ["epa_ids", "epa_label"])
        self.lf.apply(cur, self.lf.plan_labels(cur, self.EPA, self.PLATES))
        self.assertEqual(self.lf.plan_labels(cur, self.EPA, self.PLATES), [])
        self.assertEqual(self.lf.ensure_columns(cur), [])
        self.assertEqual(cur.execute("SELECT COUNT(*) FROM fuel_economy WHERE epa_ids IS NULL").fetchone()[0], 0)

    def test_rehearsal_accepts_a_rerun(self):
        ok = self.lf.label_change_ok
        base = {"city": 20, "hwy": 27, "comb": 23, "cost": 2000}
        self.assertTrue(ok(dict(base), dict(base, lbl="A"), 7, {7: "A"}))                 # first run: label added
        self.assertTrue(ok(dict(base, lbl="A"), dict(base, lbl="A"), 7, {}))              # re-run: line not planned, label kept
        self.assertTrue(ok(dict(base, lbl="A"), dict(base, lbl="B"), 7, {7: "B"}))        # re-run: label changed as planned
        self.assertTrue(ok(dict(base, lbl="A"), dict(base), 7, {7: None}))                # re-run: label planned away
        self.assertFalse(ok(dict(base), dict(base, lbl="B"), 7, {7: "A"}))                # wrong label
        self.assertFalse(ok(dict(base), dict(base, cost=2100, lbl="A"), 7, {7: "A"}))     # a figure moved
        self.assertFalse(ok(dict(base, lbl="A"), dict(base), 7, {}))                      # label lost without a plan

    def test_lookalike_verdicts(self):
        def item(vid, fid, comb, label, dscr="SIDI", kept=True):
            rec = dict(E(fid, "X", 20, 27, comb, 2.0, *AWD8), eng_dscr=dscr)
            return {"fe_id": fid, "vehicle_id": vid, "line": L(20, 27, comb, "2.0", *AWD8),
                    "kept": [rec] if kept else [], "hit": [rec] if kept else [], "new": ["1", label] if kept else ["", None]}
        assessed = [item(1, 1, 23, "A"), item(1, 2, 24, "B"),                         # told apart
                    item(2, 3, 23, "A"), item(2, 4, 24, "A", "SIDI; Stop-Start"),     # only engine notes differ
                    item(3, 5, 23, "A"), item(3, 6, 24, None, kept=False),            # a line has no EPA record
                    item(4, 7, 23, "A"), item(4, 8, 23, "A")]                         # same figures: not a group
        verdicts = {key[0]: self.lf.group_verdict(figs) for key, figs in self.lf.lookalike_groups(assessed)}
        self.assertEqual(verdicts, {1: "told apart", 2: "only EPA engine notes differ", 3: "a line matches no EPA record"})

    # ---------------------------------------------------------------- final-review fixes (2026-11-20)
    def _item(self, vid, fid, comb, kept, hit=None):
        return {"fe_id": fid, "vehicle_id": vid, "line": L(20, 27, comb, "2.0", *AWD8), "kept": kept,
                "hit": hit if hit is not None else kept, "new": ["1", self.lf.fe_labels.label_text(kept)] if kept else ["", None]}

    def test_verdict_names_the_review_causes(self):
        own = lambda i, n, **k: dict(E(i, n, 20, 27, 23, 2.0, *AWD8), **k)
        a = [self._item(1, 1, 23, [own(1, "Tahoe 2WD")], [own(1, "Tahoe 2WD")]),                       # another vehicle's name
             self._item(1, 2, 24, [own(2, "Tahoe 2WD")], [own(2, "Tahoe 2WD"), own(9, "Silverado TrailBoss")]),
             self._item(2, 3, 23, [own(3, "Sierra 2WD"), own(4, "Sierra 2WD", atv="FFV")]),             # fuel held by some
             self._item(2, 4, 24, [own(5, "Sierra 2WD")]),
             self._item(3, 5, 23, [own(6, "9-5 Sedan")]), self._item(3, 6, 24, [own(7, "9-5 Wagon")]),   # partly told apart
             self._item(3, 7, 25, [own(8, "9-5 Wagon")])]
        verdicts = {key[0]: self.lf.group_verdict(figs) for key, figs in self.lf.lookalike_groups(a)}
        self.assertEqual(verdicts, {1: "only another vehicle's name differs (dropped by the keep rule)",
                                    2: "a fuel type or charger only some records carry (hidden by the every-record rule)",
                                    3: "partly told apart"})

    def test_label_words_come_from_epa(self):
        ok = self.lf.label_words_ok
        rec = E(1, "XC90 AWD", 20, 27, 23, 2.0, *AWD8, t="T")
        self.assertTrue(ok("XC90 AWD · Turbo", "1", [rec]))
        self.assertTrue(ok(None, "", []))
        self.assertFalse(ok("XC90 AWD · Hybrid", "1", [rec]))                # tag no record carries
        self.assertFalse(ok("XC90 AWD Sport · Turbo", "1", [rec]))           # a name no record has
        self.assertFalse(ok("XC90 AWD · Turbo", "2", [rec]))                 # ids that are not the records'
        self.assertFalse(ok("XC90 AWD · Fast", "1", [rec]))                  # a word that is no tag

    def test_apply_refuses_a_changed_line_or_vehicle(self):
        for change in ("UPDATE fuel_economy SET combined_mpg=24 WHERE id=1", "UPDATE vehicles SET model='XC60' WHERE id=1"):
            con = self._fleet()
            cur = con.cursor()
            plan = self.lf.plan_labels(cur, self.EPA, self.PLATES)
            self.lf.ensure_columns(cur)
            cur.execute(change)
            with self.assertRaises(RuntimeError, msg=change):
                self.lf.apply(cur, plan)

    def test_trigger_clears_label_when_matched_fields_change(self):
        con = self._fleet()
        cur = con.cursor()
        self.lf.ensure_columns(cur)
        self.lf.apply(cur, self.lf.plan_labels(cur, self.EPA, self.PLATES))
        lab = lambda i: cur.execute("SELECT epa_ids, epa_label FROM fuel_economy WHERE id=?", (i,)).fetchone()
        cur.execute("UPDATE fuel_economy SET annual_fuel_cost=2500 WHERE id=1")            # cost is not matched on
        self.assertEqual(lab(1), ("101", "XC90 AWD · Turbo"))
        cur.execute("UPDATE fuel_economy SET combined_mpg=24 WHERE id=1")
        self.assertEqual(lab(1), (None, None))
        self.assertEqual(lab(2), ("102", "XC90 AWD · Turbo, Supercharged"))
        cur.execute("UPDATE fuel_economy SET mpge=NULL WHERE id=4")                       # electric figure cleared
        self.assertEqual(lab(4), (None, None))
        cur.execute("UPDATE vehicles SET model='XC60' WHERE id=1")
        self.assertEqual(lab(2), (None, None))

    def test_write_is_one_transaction(self):
        import tempfile
        import shutil
        tmp = tempfile.mkdtemp(prefix="kyr_fe_write_")
        try:
            db = os.path.join(tmp, "fleet.db")
            disk = sqlite3.connect(db)
            self._fleet().backup(disk)
            disk.execute("CREATE TABLE oil_change (source TEXT)")
            for t in ("parts", "fluids", "torque_specs"):
                disk.execute("CREATE TABLE %s (source TEXT)" % t)
            disk.executemany("INSERT INTO oil_change VALUES (?)", [("owner-manual-verified",)] * self.lf.BARE_FROZEN)
            disk.commit()
            plan = self.lf.plan_labels(disk.cursor(), self.EPA, self.PLATES)
            disk.execute("UPDATE fuel_economy SET combined_mpg=24 WHERE id=3")               # stale after the dry run
            disk.commit()
            disk.close()
            saved = (self.lf.DB, self.lf.PLAN_FILE)
            self.lf.DB, self.lf.PLAN_FILE = db, os.path.join(tmp, "plan_cache.json")
            try:
                sha = self.lf.save_plan(plan, self.lf.plates_sha(self.PLATES))
                with self.assertRaises(RuntimeError):
                    self.lf.write(sha)
            finally:
                self.lf.DB, self.lf.PLAN_FILE = saved
            con = sqlite3.connect(db)
            cols = {r[1] for r in con.execute("PRAGMA table_info(fuel_economy)")}
            triggers = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
            con.close()
            self.assertNotIn("epa_ids", cols)
            self.assertEqual(triggers, 0)
            self.assertEqual(len([n for n in os.listdir(tmp) if ".bak_fe_labels_" in n]), 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestLabelEquivalence(unittest.TestCase):
    def test_shipped_labels_equal_the_database(self):
        import tempfile
        import shutil
        import types
        vs = _verifier()
        tmp = tempfile.mkdtemp(prefix="kyr_fe_equiv_")
        try:
            path = os.path.join(tmp, "eq.db")
            _fe_db(path, True, [(1, 7, 20, "5", "A"), (2, 7, 21, "", None), (3, 8, 22, "6", "B")])
            a = lambda m7, m8: types.SimpleNamespace(db_path=path, D={"v": [{"id": 7, "mpg": m7}, {"id": 8, "mpg": m8}]})
            self.assertEqual(vs.s1_14_label_provenance(a([{"lbl": "A"}, {}], [{"lbl": "B"}])), [])
            self.assertEqual(len(vs.s1_14_label_provenance(a([{"lbl": "A"}, {}], [{}]))), 1)           # label not shipped
            self.assertEqual(len(vs.s1_14_label_provenance(a([{"lbl": "X"}, {}], [{"lbl": "B"}]))), 1)  # wrong label
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
