"""IC-02 Phase A: tests for the exact-token source registry (files/source_registry.py).

TDD contract for the registry that replaces the three copied substring `_ver()`
implementations (build / guide generator / verifier mirror stays independent).
Fixtures pin every required literal outcome INDEPENDENTLY of the registry's own
declarative tables -- expectations here are literals, never imports of the data
under test.

DB-dependent classes use the repo-root wrench_vehicles.db READ-ONLY, or private
temporary copies for negative fixtures. No test may ever mutate a real database
file. Generator fail-closed tests drive the REAL main() paths against temporary
DB/output locations and prove a pre-existing sentinel output file survives
byte-for-byte with no backup created.

Discovered by CI via:  python -m unittest discover -s tests -v
"""
import gc
import importlib.util
import io
import json
import os
import re
import warnings
import shutil
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FILES_DIR = os.path.join(ROOT, "files")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if FILES_DIR not in sys.path:
    sys.path.insert(0, FILES_DIR)

from files.source_registry import (  # noqa: E402
    SourceRegistryError,
    assert_frozen_landscape,
    bare_rows_digest,
    classify,
)

DB = os.path.join(ROOT, "wrench_vehicles.db")
HAS_DB = os.path.exists(DB)

# Independent pins (literals, NOT imported from the registry).
GATED = ("oil_change", "parts", "fluids", "torque_specs", "engine_specs", "maintenance")
OMV = "owner-manual-verified"
OMV_TABLES = ("oil_change", "parts", "fluids", "torque_specs")
MAINT_TOKENS = (
    "Buick Owner's Manual", "Cadillac Owner's Manual", "Chevrolet Owner's Manual",
    "Ford Owner's Manual", "GMC Owner's Manual", "Honda Owner's Manual",
    "Hyundai Owner's Manual", "Lincoln Owner's Manual", "Mazda Owner's Manual",
    "Nissan Owner's Manual", "Owner's Manual", "Subaru Owner's Manual",
)
QTOKEN = "quarantine-applicability-ic01"
QTABLES = ("oil_change", "parts", "fluids", "torque_specs", "maintenance")
QIDS = (12372, 12511, 12777, 12847, 12912)
BARE_ROW_COUNT = 424
BARE_ROW_SHA256 = "ca156c69ed4cc8df34ff1244a612d497494a725ec3efcdd7d502f2aa179c8980"

ORPHAN_VID = 999999999           # never a real vehicles.id
UNKNOWN_TOKEN = "ic02-forced-unknown-token"
SENTINEL = b"IC02-SENTINEL-OUTPUT: this file must never be rewritten by a failing build\n"

# Real irregular legacy suffixes observed in the database (verbatim). All are
# output-neutral under the Phase-A opaque-suffix rule: byte-exact token before
# the first " (", everything after is opaque provenance (no balanced-parens
# requirement, trailing text after ")" allowed).
IRREGULAR_VERIFIED = (
    ("owner-manual-verified (per 2003 Cadillac Escalade OM, self-ID p1; GMT800 - "
     "2003 OM legible (471pp text PDF), gap read directly, no scanned-OM gating)",
     "oil_change"),
    ("owner-manual-verified (per 2024 Hyundai Sonata OM (24 Sonata OM.pdf), "
     "MyHyundai glovebox-manual; DN8 facelift)", "parts"),
    ("GMC Owner's Manual (Sierra 2500HD) + 6.6L Duramax Supplement", "maintenance"),
    ("Honda Owner's Manual (2017 Civic Sedan, 10th gen, OG-05950) - "
     "generation-stable (shared drivetrain)", "maintenance"),
    ("Lincoln Owner's Manual (2023 Aviator, 2nd gen) + 2020 Aviator Technical "
     "Specifications", "maintenance"),
)


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestClassifyVerified(unittest.TestCase):
    def test_bare_verified_token_per_allowed_table(self):
        for t in OMV_TABLES:
            self.assertEqual(classify(OMV, t), 1, t)

    def test_regular_suffix_is_opaque(self):
        self.assertEqual(
            classify("owner-manual-verified (2019 Silverado 1500 OM p.337)",
                     "oil_change"), 1)

    def test_current_irregular_legacy_suffixes(self):
        for src, t in IRREGULAR_VERIFIED:
            self.assertEqual(classify(src, t), 1, src)

    def test_maintenance_only_tokens(self):
        for tok in MAINT_TOKENS:
            self.assertEqual(classify(tok, "maintenance"), 1, tok)

    def test_vehicle_id_passthrough_for_verified(self):
        self.assertEqual(classify(OMV, "oil_change", vehicle_id=467), 1)


class TestClassifyKnownUnverified(unittest.TestCase):
    def test_registered_unverified_tokens(self):
        for tok, tables in (
            ("ai-haiku-4.5", GATED),
            ("scraped", GATED),
            ("unknown", ("oil_change", "parts", "fluids", "torque_specs", "engine_specs")),
            ("engine_classifier_v1", ("maintenance",)),
        ):
            for t in tables:
                self.assertEqual(classify(tok, t), 0, (tok, t))

    def test_quarantine_token_in_cohort(self):
        for t in QTABLES:
            for vid in (QIDS[0], QIDS[-1]):
                self.assertEqual(classify(QTOKEN, t, vehicle_id=vid), 0, (t, vid))
            self.assertEqual(classify(QTOKEN, t), 0, t)  # census scan: id unknown

    def test_citation_text_never_confers_verification(self):
        # An unverified token stays 0 even when its suffix NAMES a verified token.
        self.assertEqual(classify("scraped (owner-manual-verified)", "oil_change"), 0)
        self.assertEqual(classify("scraped (2019 OM p.3)", "maintenance"), 0)


class TestClassifyHardFailures(unittest.TestCase):
    def _fails(self, src, table, vehicle_id=None):
        with self.assertRaises(SourceRegistryError, msg=repr((src, table))):
            classify(src, table, vehicle_id=vehicle_id)

    def test_null_empty_and_boundary_whitespace(self):
        for src in (None, "", "   ", " owner-manual-verified",
                    "owner-manual-verified ", "\towner-manual-verified",
                    "owner-manual-verified\n"):
            self._fails(src, "oil_change")

    def test_case_changed_tokens(self):
        for src, t in (("Owner-Manual-Verified", "oil_change"),
                       ("OWNER-MANUAL-VERIFIED", "oil_change"),
                       ("honda owner's manual", "maintenance"),
                       ("HONDA OWNER'S MANUAL", "maintenance"),
                       ("Gmc Owner's Manual", "maintenance")):
            self._fails(src, t)

    def test_unknown_and_unregistered_tokens(self):
        # Only OBSERVED tokens are registered; plausible-but-unobserved ones fail.
        for src in ("toyota-owner-manual", "Toyota Owner's Manual", "vpic",
                    "nhtsa-verified", UNKNOWN_TOKEN):
            self._fails(src, "maintenance")
        self._fails("epa-manufacturer-specs", "oil_change")

    def test_compound_and_malformed_tokens(self):
        self._fails("scraped-owner-manual", "oil_change")
        self._fails("owner-manual-verified+scraped", "oil_change")
        self._fails("owner-manual-verified (", "oil_change")      # empty suffix
        self._fails("owner-manual-verified  (p.3)", "oil_change")  # token keeps a space

    def test_blacklisted_provenance_in_verified_suffix(self):
        for src, t in (
            ("owner-manual-verified (backfilled from scraped table)", "oil_change"),
            ("owner-manual-verified (ai-haiku-4.5 assisted)", "parts"),
            ("owner-manual-verified (engine_classifier_v1)", "fluids"),
            ("Honda Owner's Manual (via ai-haiku)", "maintenance"),
            ("owner-manual-verified (quarantine-applicability-ic01)", "torque_specs"),
            # IC-02 correction 4: the registered-unverified `unknown` token and the
            # blocked EV token are blacklisted provenance too -- a verified token
            # may not launder either through its citation suffix.
            ("owner-manual-verified (unknown)", "oil_change"),
            ("owner-manual-verified (source unknown, backfilled)", "parts"),
            ("owner-manual-verified (epa-manufacturer-specs)", "fluids"),
            ("Honda Owner's Manual (per epa-manufacturer-specs pull)", "maintenance"),
        ):
            self._fails(src, t)

    def test_blacklist_markers_are_case_insensitive(self):
        # IC-02 correction 4: mixed/uppercase variants of every marker hard-fail.
        for src, t in (
            ("owner-manual-verified (SCRAPED copy)", "oil_change"),
            ("owner-manual-verified (AI-Haiku assisted)", "parts"),
            ("owner-manual-verified (Engine_Classifier_V1)", "fluids"),
            ("owner-manual-verified (Unknown provenance)", "torque_specs"),
            ("owner-manual-verified (EPA-Manufacturer-Specs)", "oil_change"),
            ("Honda Owner's Manual (QUARANTINE-APPLICABILITY-IC01)", "maintenance"),
        ):
            self._fails(src, t)

    def test_verified_token_in_wrong_table(self):
        self._fails(OMV, "maintenance")
        self._fails(OMV, "engine_specs")
        self._fails("Honda Owner's Manual", "oil_change")
        self._fails("Mazda Owner's Manual", "parts")

    def test_unverified_token_outside_observed_scope(self):
        self._fails("engine_classifier_v1", "engine_specs")
        self._fails("unknown", "maintenance")

    def test_quarantine_restrictions(self):
        self._fails(QTOKEN + " (x)", "oil_change", vehicle_id=QIDS[0])  # concatenation
        self._fails(QTOKEN + "-v2", "oil_change", vehicle_id=QIDS[0])   # concatenation
        self._fails(QTOKEN, "oil_change", vehicle_id=467)   # outside the IC-01 cohort
        self._fails(QTOKEN, "engine_specs", vehicle_id=QIDS[0])  # outside its tables

    def test_non_gated_or_undispositioned_tables(self):
        self._fails(OMV, "ev_specs")
        self._fails("epa-manufacturer-specs", "ev_specs")
        self._fails(OMV, "fuse_locations")
        self._fails(OMV, "vehicle_notes")
        self._fails(OMV, "brand_new_specs_table")
        self._fails(OMV, None)
        self._fails(OMV, "")


@unittest.skipUnless(HAS_DB, "wrench_vehicles.db not present (CI)")
class TestFrozenLandscapePositive(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)

    def tearDown(self):
        self.con.close()

    def test_real_database_passes(self):
        assert_frozen_landscape(self.con.cursor())  # must not raise

    def test_bare_row_freeze_values(self):
        count, digest = bare_rows_digest(self.con.cursor())
        self.assertEqual(count, BARE_ROW_COUNT)
        self.assertEqual(digest, BARE_ROW_SHA256)


@unittest.skipUnless(HAS_DB, "wrench_vehicles.db not present (CI)")
class TestFrozenLandscapeNegatives(unittest.TestCase):
    """Every fixture mutates an UNCOMMITTED transaction on a TEMPORARY COPY of the
    database and rolls back afterwards. The real DBs are never touched.

    autocommit is disabled and the transaction opened EXPLICITLY: under the
    sqlite3 module's legacy implicit-transaction mode, DDL (CREATE/DROP TABLE)
    autocommits and would survive the rollback, leaking one scenario into the
    next. SQLite itself supports transactional DDL, so an explicit BEGIN makes
    every scenario -- DML and DDL alike -- fully isolated."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="ic02_registry_test_")
        cls.tmp_db = os.path.join(cls.tmpdir, "landscape_copy.db")
        shutil.copyfile(DB, cls.tmp_db)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def setUp(self):
        self.con = sqlite3.connect(self.tmp_db, isolation_level=None)
        self.cur = self.con.cursor()
        self.cur.execute("BEGIN")

    def tearDown(self):
        self.cur.execute("ROLLBACK")
        self.con.close()

    def _fails(self):
        with self.assertRaises(SourceRegistryError):
            assert_frozen_landscape(self.cur)

    def test_new_source_bearing_table_needs_disposition(self):
        self.cur.execute(
            "CREATE TABLE zz_ic02_probe (vehicle_id INTEGER, source TEXT)")
        self._fails()

    def test_dropping_a_dispositioned_table_fails(self):
        self.cur.execute("DROP TABLE ev_specs")
        self._fails()

    def test_bare_row_added_fails(self):
        self.cur.execute(
            "UPDATE oil_change SET source=? WHERE rowid=(SELECT rowid FROM oil_change"
            " WHERE source LIKE ? LIMIT 1)", (OMV, OMV + " (%"))
        self._fails()

    def test_bare_row_removed_fails(self):
        self.cur.execute(
            "UPDATE oil_change SET source=? WHERE rowid=(SELECT rowid FROM oil_change"
            " WHERE source=? LIMIT 1)", (OMV + " (relabeled)", OMV))
        self._fails()

    def test_bare_row_content_change_fails(self):
        self.cur.execute(
            "UPDATE oil_change SET viscosity='9W-99' WHERE rowid="
            "(SELECT rowid FROM oil_change WHERE source=? LIMIT 1)", (OMV,))
        self._fails()

    def test_ev_row_removed_fails(self):
        self.cur.execute(
            "DELETE FROM ev_specs WHERE rowid=(SELECT rowid FROM ev_specs LIMIT 1)")
        self._fails()

    def test_ev_token_change_fails(self):
        self.cur.execute(
            "UPDATE ev_specs SET source='epa-manufacturer-specs-v2' WHERE rowid="
            "(SELECT rowid FROM ev_specs LIMIT 1)")
        self._fails()


class _TempDbSentinelCase(unittest.TestCase):
    """Base harness: each test gets a PRIVATE temporary copy of the database and
    a pre-created sentinel output file. The generator under test must raise
    SourceRegistryError and leave the sentinel byte-for-byte intact with no
    backup file created -- proving failure precedes every write."""

    PREFIX = "ic02_gen_fixture_"

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix=self.PREFIX)
        self.tmp_db = os.path.join(self.tmpdir, "copy.db")
        shutil.copyfile(DB, self.tmp_db)
        self.sentinel = os.path.join(self.tmpdir, "sentinel_output")
        with open(self.sentinel, "wb") as f:
            f.write(SENTINEL)

    def tearDown(self):
        # Both generators close their SQLite connection via try/finally on every
        # path (IC-02 final correction 2), so no leaked-handle workaround is
        # needed here and the temp tree removes cleanly.
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _exec(self, sql, params=()):
        con = sqlite3.connect(self.tmp_db)
        con.execute(sql, params)
        con.commit()
        con.close()

    def _assert_sentinel_intact(self):
        with open(self.sentinel, "rb") as f:
            self.assertEqual(f.read(), SENTINEL, "sentinel output was rewritten")
        baks = [n for n in os.listdir(self.tmpdir) if ".bak" in n]
        self.assertEqual(baks, [], "backup file created despite failing build")


@unittest.skipUnless(HAS_DB, "wrench_vehicles.db not present (CI)")
class TestGuideGeneratorFailsClosed(_TempDbSentinelCase):
    """_gen_guide_specs.py must enforce the frozen landscape and the exact-token
    registry BEFORE writing specs.json (IC-02 corrections 2 and the original
    forced-unknown contract). Runs the REAL main() against a private DB copy
    with OUT pointed at the sentinel."""

    def _run_expect_failure(self):
        mod = _load_module(os.path.join(ROOT, "_gen_guide_specs.py"),
                           "_gen_guide_specs_ic02_test")
        mod.DB = self.tmp_db
        mod.OUT = self.sentinel
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SourceRegistryError):
                mod.main()
        self._assert_sentinel_intact()

    def test_unknown_token_fails_before_output(self):
        self._exec(
            "UPDATE oil_change SET source=? WHERE rowid=(SELECT rowid FROM oil_change"
            " WHERE source='ai-haiku-4.5' AND vehicle_id IN (SELECT id FROM vehicles)"
            " LIMIT 1)", (UNKNOWN_TOKEN,))
        self._run_expect_failure()

    def test_changed_grandfathered_bare_row_fails_before_output(self):
        self._exec(
            "UPDATE oil_change SET viscosity='9W-99' WHERE rowid="
            "(SELECT rowid FROM oil_change WHERE source=? LIMIT 1)", (OMV,))
        self._run_expect_failure()

    def test_added_bare_row_fails_before_output(self):
        self._exec(
            "UPDATE oil_change SET source=? WHERE rowid=(SELECT rowid FROM oil_change"
            " WHERE source LIKE ? LIMIT 1)", (OMV, OMV + " (%"))
        self._run_expect_failure()

    def test_removed_bare_row_fails_before_output(self):
        self._exec(
            "UPDATE oil_change SET source=? WHERE rowid=(SELECT rowid FROM oil_change"
            " WHERE source=? LIMIT 1)", (OMV + " (relabeled)", OMV))
        self._run_expect_failure()


@unittest.skipUnless(HAS_DB, "wrench_vehicles.db not present (CI)")
class TestDemoBuildMainFailsClosed(_TempDbSentinelCase):
    """files/04_rebuild_demo.py must reject unknown tokens AND orphaned gated
    rows (vehicle_id absent from vehicles) in a pre-projection admission scan
    (IC-02 corrections 3 and 6). Runs the REAL main() with DB_PATH/OUT_FILE
    pointed at the private copy and the sentinel; every fixture must fail
    before the template read, the .bak backup, and the output write."""

    def _run_expect_failure(self):
        mod = _load_module(os.path.join(FILES_DIR, "04_rebuild_demo.py"),
                           "_rebuild_demo_ic02_test")
        mod.DB_PATH = self.tmp_db
        mod.OUT_FILE = self.sentinel
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SourceRegistryError):
                mod.main()
        self._assert_sentinel_intact()

    def test_unknown_token_fails_before_output(self):
        self._exec(
            "UPDATE oil_change SET source=? WHERE rowid=(SELECT rowid FROM oil_change"
            " WHERE source='ai-haiku-4.5' AND vehicle_id IN (SELECT id FROM vehicles)"
            " LIMIT 1)", (UNKNOWN_TOKEN,))
        self._run_expect_failure()

    def test_orphan_row_with_unknown_token_fails(self):
        self._exec(
            "UPDATE oil_change SET vehicle_id=?, source=? WHERE rowid="
            "(SELECT rowid FROM oil_change WHERE source='ai-haiku-4.5' LIMIT 1)",
            (ORPHAN_VID, UNKNOWN_TOKEN))
        self._run_expect_failure()

    def test_orphan_row_with_quarantine_token_fails(self):
        self._exec(
            "UPDATE oil_change SET vehicle_id=? WHERE rowid="
            "(SELECT rowid FROM oil_change WHERE source=? LIMIT 1)",
            (ORPHAN_VID, QTOKEN))
        self._run_expect_failure()

    def test_orphan_row_with_registered_token_fails(self):
        # Even a legitimately registered verified token is rejected on an orphan
        # row: orphans are invisible to the projection joins, so they must never
        # be admitted at all. (A suffixed row keeps the bare-row freeze intact,
        # proving the ORPHAN check fires -- not the citation-debt digest.)
        self._exec(
            "UPDATE oil_change SET vehicle_id=? WHERE rowid="
            "(SELECT rowid FROM oil_change WHERE source LIKE ? LIMIT 1)",
            (ORPHAN_VID, OMV + " (%"))
        self._run_expect_failure()


class TestS10WiringCheckNegatives(unittest.TestCase):
    """Permanent, DB-independent tamper fixtures for the verifier's S10.3
    structural wiring check (IC-02 final correction 1): a call that merely
    exists somewhere must NOT satisfy the contract. Each fixture doctors a copy
    of one real generator file in a temp tree and asserts S10.3 fires; the
    positive control proves the harness passes on verbatim copies."""

    BUILD_REL = os.path.join("files", "04_rebuild_demo.py")
    GUIDE_REL = "_gen_guide_specs.py"

    @classmethod
    def setUpClass(cls):
        cls.vs = _load_module(os.path.join(ROOT, "_verify_shipped.py"),
                              "_verify_shipped_ic02_wiring_test")
        with open(os.path.join(ROOT, cls.BUILD_REL), encoding="utf-8") as f:
            cls.build_txt = f.read()
        with open(os.path.join(ROOT, cls.GUIDE_REL), encoding="utf-8") as f:
            cls.guide_txt = f.read()

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="ic02_wiring_fixture_")
        os.makedirs(os.path.join(self.tmpdir, "files"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, build_txt, guide_txt):
        with open(os.path.join(self.tmpdir, self.BUILD_REL), "w",
                  encoding="utf-8") as f:
            f.write(build_txt)
        with open(os.path.join(self.tmpdir, self.GUIDE_REL), "w",
                  encoding="utf-8") as f:
            f.write(guide_txt)
        fake = type("FakeArtifacts", (), {
            "root": self.tmpdir,
            "_read": staticmethod(self.vs.Artifacts._read),
        })()
        return self.vs.s10_3_generator_wiring(fake)

    def _mutate(self, txt, pattern, replacement, count=1):
        mutated, n = re.subn(pattern, replacement, txt, count=count, flags=re.M)
        self.assertEqual(n, count, "tamper mutation did not apply: %r" % pattern)
        return mutated

    def test_positive_control_verbatim_files_pass(self):
        self.assertEqual(self._run(self.build_txt, self.guide_txt), [])

    def test_admission_call_removed_from_main_fires(self):
        doctored = self._mutate(
            self.build_txt, r"^\s*_assert_registry_admission\(cur\)\s*\n", "")
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_gates_only_in_uncalled_helper_fire(self):
        doctored = self._mutate(
            self.build_txt, r"^\s*_assert_registry_admission\(cur\)\s*\n", "")
        doctored = self._mutate(
            doctored, r"^\s*assert_frozen_landscape\(cur\)\s*\n", "")
        doctored += ("\n\ndef _zz_never_called(cur):\n"
                     "    _assert_registry_admission(cur)\n"
                     "    assert_frozen_landscape(cur)\n")
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_gates_only_under_if_false_fire(self):
        doctored = self._mutate(
            self.build_txt, r"^\s*_assert_registry_admission\(cur\)\s*\n", "")
        doctored += "\n\nif False:\n    _assert_registry_admission(None)\n"
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_rebound_classifier_fires(self):
        doctored = self.build_txt + "\n\n_classify = None\n"
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_shadowing_local_definition_fires(self):
        doctored = (self.build_txt
                    + "\n\ndef assert_frozen_landscape(cur):\n    pass\n")
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_local_substitute_gate_fires(self):
        doctored = self._mutate(
            self.build_txt, r"^(\s*)_assert_registry_admission\(cur\)\s*\n",
            r"\g<1>_zz_local_gate(cur)\n")
        doctored += "\n\ndef _zz_local_gate(cur):\n    pass\n"
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_guide_landscape_call_removed_fires(self):
        doctored = self._mutate(
            self.guide_txt, r"^\s*assert_frozen_landscape\(cur\)\s*\n", "")
        self.assertTrue(self._run(self.build_txt, doctored))

    def test_guide_classifier_call_removed_fires(self):
        doctored = self._mutate(
            self.guide_txt,
            r"_classify\(r\[\"source\"\], \"oil_change\", r\[\"vehicle_id\"\]\) != 1",
            "0 != 1")
        self.assertTrue(self._run(self.build_txt, doctored))

    # ---- IC-02 bounded correction 1: dead-code bypass fixtures ----

    def test_admission_rebound_to_noop_fires(self):
        doctored = self.build_txt + "\n\n_assert_registry_admission = lambda cur: None\n"
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_build_data_rebound_fires(self):
        doctored = self.build_txt + "\n\nbuild_data = lambda cur: ([], {}, {}, 0)\n"
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_gates_unreachable_after_control_flow_fires(self):
        doctored = self._mutate(
            self.build_txt, r"^(\s*)cur = conn\.cursor\(\)\s*\n",
            "\\1cur = conn.cursor()\n\\1if cur is None:\n\\1    raise SystemExit(1)\n")
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_dead_projection_calls_do_not_satisfy_coverage(self):
        # The reviewer's exploit: every real emitted ver becomes a fake constant 1
        # while six classifier calls sit under `if False`. Coverage must fail.
        doctored, n = re.subn(
            r'"ver": _classify\((?:[^()]|\([^()]*\))*\)', '"ver": 1',
            self.build_txt)
        self.assertEqual(n, 6, "expected to fake exactly the six gated projections")
        doctored += ("\n\nif False:\n"
                     "    _classify(None, \"oil_change\", None)\n"
                     "    _classify(None, \"parts\", None)\n"
                     "    _classify(None, \"fluids\", None)\n"
                     "    _classify(None, \"torque_specs\", None)\n"
                     "    _classify(None, \"engine_specs\", None)\n"
                     "    _classify(None, \"maintenance\", None)\n")
        self.assertTrue(self._run(doctored, self.guide_txt))

    def test_guide_dead_call_substitution_fires(self):
        doctored, n = re.subn(
            r'_classify\(r\["source"\], "(oil_change|parts|torque_specs)", '
            r'r\["vehicle_id"\]\) != 1',
            "0 != 1", self.guide_txt)
        self.assertEqual(n, 3, "expected to neutralize exactly the three guide guards")
        doctored += ("\n\nif False:\n"
                     "    _classify(None, \"oil_change\", None)\n"
                     "    _classify(None, \"parts\", None)\n"
                     "    _classify(None, \"torque_specs\", None)\n")
        self.assertTrue(self._run(self.build_txt, doctored))


@unittest.skipUnless(HAS_DB, "wrench_vehicles.db not present (CI)")
class TestGeneratorsSucceedCleanly(unittest.TestCase):
    """IC-02 bounded correction 2: the SUCCESS paths must also close every
    handle. Runs each generator to completion against temporary DB/output
    copies with ResourceWarnings captured; zero may occur."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="ic02_success_")
        self.tmp_db = os.path.join(self.tmpdir, "copy.db")
        shutil.copyfile(DB, self.tmp_db)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _assert_no_resource_warnings(self, run):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            run()
            gc.collect()   # surface any finalizer-time ResourceWarnings NOW
        leaks = [str(w.message) for w in caught
                 if issubclass(w.category, ResourceWarning)]
        self.assertEqual(leaks, [], "success path leaked handles")

    def test_demo_build_succeeds_without_resource_warnings(self):
        tmp_out = os.path.join(self.tmpdir, "wrench_demo.html")
        shutil.copyfile(os.path.join(ROOT, "wrench_demo.html"), tmp_out)
        mod = _load_module(os.path.join(FILES_DIR, "04_rebuild_demo.py"),
                           "_rebuild_demo_ic02_success_test")
        mod.DB_PATH = self.tmp_db
        mod.OUT_FILE = tmp_out
        def run():
            with redirect_stdout(io.StringIO()):
                mod.main()
        self._assert_no_resource_warnings(run)
        self.assertGreater(os.path.getsize(tmp_out), 1_000_000,
                           "successful build did not write the demo output")

    def test_guide_generation_succeeds_without_resource_warnings(self):
        tmp_out = os.path.join(self.tmpdir, "specs.json")
        mod = _load_module(os.path.join(ROOT, "_gen_guide_specs.py"),
                           "_gen_guide_specs_ic02_success_test")
        mod.DB = self.tmp_db
        mod.OUT = tmp_out
        def run():
            with redirect_stdout(io.StringIO()):
                mod.main()
        self._assert_no_resource_warnings(run)
        with open(tmp_out, encoding="utf-8") as f:
            self.assertIn("_meta", json.load(f))


if __name__ == "__main__":
    unittest.main()
