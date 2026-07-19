"""IC-02 Phase A: the exact-token source registry (THE LAW, made byte-exact).

Single production classifier for the data-integrity gate. Replaces the copied
substring `_ver()` implementations in files/04_rebuild_demo.py and
_gen_guide_specs.py; the shipped-surfaces verifier keeps its own independent
parser and pins this mapping separately (a registry must never verify itself).

Contract (Phase A):
- Tokens match BYTE-EXACTLY and case-sensitively. No lowercasing, no trimming;
  a null, empty, or boundary-whitespace source is a hard failure.
- A source splits ONCE on the exact delimiter " (". Everything after it is an
  OPAQUE legacy provenance suffix: not parsed, not required to balance
  parentheses, and never able to confer verification (citation text != source).
- For VERIFIED tokens, a blacklisted provenance marker anywhere in the suffix
  is a hard failure (a verified token may not launder blacklisted provenance).
- A token is registered only if OBSERVED in the database at freeze time; an
  unknown token, or a registered token in a table outside its observed scope,
  is a hard failure -- fail-closed, never fail-open to 0.
- `quarantine-applicability-ic01` stays UNVERIFIED, must appear exactly (no
  suffix), only in its five tables, and -- when a vehicle id is supplied --
  only for the IC-01 cohort. S9.6's database-level scope checks are unchanged.
- Every table that carries a `source` column must have an explicit disposition
  below; a source-bearing table with no disposition is a hard failure, so a
  future EV-like table cannot bypass the gate by omission.
- `ev_specs` is BLOCKED pending IC-02E: `epa-manufacturer-specs` is NOT a
  verified token, the classifier hard-fails if it is ever presented, and the
  table is frozen at its current shape (see EV_* constants). This registry
  covers token-level admission only; field-level authority (OA-A2) is a
  separate, unfinished contract.

Citation-debt freeze: the historical rows whose source is exactly the bare
`owner-manual-verified` token (no per-row citation suffix) are grandfathered as
a FROZEN set -- pinned by exact count and a content digest over canonical
serialization. Any new, removed, or edited row under the bare token fails the
build until deliberately ruled; new or changed verified rows must carry a
provenance suffix.
"""
import hashlib
import json
import sys

try:
    from ic01_quarantine import QUARANTINED_VEHICLE_IDS, QUARANTINE_SOURCE
except ImportError:  # imported as part of the files package (repo root on sys.path)
    from files.ic01_quarantine import QUARANTINED_VEHICLE_IDS, QUARANTINE_SOURCE

# This module is imported under two names: "source_registry" (build scripts run
# from files/) and "files.source_registry" (repo-root tools and the verifier).
# Alias both names to THIS instance so there is exactly one SourceRegistryError
# class per process -- otherwise `except SourceRegistryError` in one context
# silently fails to catch the exception raised in the other.
for _alias in ("source_registry", "files.source_registry"):
    sys.modules.setdefault(_alias, sys.modules[__name__])


class SourceRegistryError(ValueError):
    """Hard failure of the source-registry contract. Never catch-and-continue in
    a generator: the build must die before any output file is written."""


TOKEN_DELIMITER = " ("

DISPOSITION_GATED = "registry-gated"
DISPOSITION_BLOCKED_IC02E = "blocked-pending-ic02e"
DISPOSITION_EXCLUDED = "excluded-never-ships"

# Every source-bearing table in the canonical database, each with an explicit
# disposition. assert_frozen_landscape() holds this set EQUAL to the database's
# actual source-bearing tables, so additions AND removals both fail loudly.
TABLE_DISPOSITIONS = {
    "oil_change":     DISPOSITION_GATED,
    "parts":          DISPOSITION_GATED,
    "fluids":         DISPOSITION_GATED,
    "torque_specs":   DISPOSITION_GATED,
    "engine_specs":   DISPOSITION_GATED,
    "maintenance":    DISPOSITION_GATED,
    # Blocked pending the IC-02E ruling: not verified, not classifiable, frozen.
    "ev_specs":       DISPOSITION_BLOCKED_IC02E,
    # Gated out of every shipped surface (2026-07-14 strip / P0-4): rows stay in
    # the DB for internal reference and are never emitted, so they are excluded
    # from classification rather than registered.
    "fuse_locations": DISPOSITION_EXCLUDED,
    "vehicle_notes":  DISPOSITION_EXCLUDED,
}

GATED_TABLES = tuple(
    t for t, d in TABLE_DISPOSITIONS.items() if d == DISPOSITION_GATED
)

# VERIFIED tokens -> the tables they were observed in at the IC-02 freeze.
# Register only observed tokens; hypothetical tokens (generic EPA/NHTSA/vPIC,
# unobserved makes) are NOT preauthorized -- they hard-fail until ruled.
VERIFIED_TOKEN_TABLES = {
    "owner-manual-verified": frozenset(
        {"oil_change", "parts", "fluids", "torque_specs"}
    ),
    "Buick Owner's Manual":     frozenset({"maintenance"}),
    "Cadillac Owner's Manual":  frozenset({"maintenance"}),
    "Chevrolet Owner's Manual": frozenset({"maintenance"}),
    "Ford Owner's Manual":      frozenset({"maintenance"}),
    "GMC Owner's Manual":       frozenset({"maintenance"}),
    "Honda Owner's Manual":     frozenset({"maintenance"}),
    "Hyundai Owner's Manual":   frozenset({"maintenance"}),
    "Lincoln Owner's Manual":   frozenset({"maintenance"}),
    "Mazda Owner's Manual":     frozenset({"maintenance"}),
    "Nissan Owner's Manual":    frozenset({"maintenance"}),
    "Owner's Manual":           frozenset({"maintenance"}),
    "Subaru Owner's Manual":    frozenset({"maintenance"}),
}

# Known UNVERIFIED tokens -> observed table scope. These return 0 (the row ships
# as a bare {ver:0} shell or is dropped); everything else is a hard failure.
UNVERIFIED_TOKEN_TABLES = {
    "ai-haiku-4.5": frozenset(GATED_TABLES),
    "scraped":      frozenset(GATED_TABLES),
    "unknown":      frozenset(
        {"oil_change", "parts", "fluids", "torque_specs", "engine_specs"}
    ),
    "engine_classifier_v1": frozenset({"maintenance"}),
    QUARANTINE_SOURCE: frozenset(
        {"oil_change", "parts", "fluids", "torque_specs", "maintenance"}
    ),
}

# D1 blacklist markers: a VERIFIED token whose suffix contains any of these
# (case-insensitive) is laundering blacklisted provenance -> hard failure.
# IC-02 correction 4 added "unknown" (the registered-unverified token; also the
# plain word -- any verified suffix needing the word "unknown" must be ruled)
# and the blocked EV token "epa-manufacturer-specs". Zero existing verified
# suffixes contain either string, so the closure is output-neutral.
BLACKLIST_SUFFIX_MARKERS = (
    "ai-", "haiku", "scraped", "classifier", "quarantine-applicability",
    "unknown", "epa-manufacturer-specs",
)

# Citation-debt freeze (grandfathered pre-suffix rows; see module docstring).
BARE_VERIFIED_TOKEN = "owner-manual-verified"
BARE_ROW_TABLES = ("oil_change", "parts", "fluids", "torque_specs")
BARE_ROW_COUNT = 424
BARE_ROW_SHA256 = "ca156c69ed4cc8df34ff1244a612d497494a725ec3efcdd7d502f2aa179c8980"

# IC-02E freeze: current shape of the blocked ev_specs table.
EV_TABLE = "ev_specs"
EV_FROZEN_ROW_COUNT = 75
EV_FROZEN_SOURCE = "epa-manufacturer-specs"


def classify(source, table, vehicle_id=None):
    """Return 1 (verified) or 0 (known-unverified) for a gated-table row, or
    raise SourceRegistryError. Pass vehicle_id when available so quarantine
    cohort membership is enforced at classification time."""
    if not isinstance(table, str) or table not in TABLE_DISPOSITIONS:
        raise SourceRegistryError(
            "table %r has no registry disposition (IC-02: every source-bearing "
            "table needs an explicit ruling)" % (table,))
    if TABLE_DISPOSITIONS[table] != DISPOSITION_GATED:
        raise SourceRegistryError(
            "table %r is not registry-gated (disposition: %s)"
            % (table, TABLE_DISPOSITIONS[table]))
    if not isinstance(source, str):
        raise SourceRegistryError(
            "null/non-string source in gated table %r" % (table,))
    if not source or source != source.strip():
        raise SourceRegistryError(
            "empty or boundary-whitespace source %r in %s" % (source, table))

    token, sep, suffix = source.partition(TOKEN_DELIMITER)
    if sep and not suffix:
        raise SourceRegistryError(
            "malformed source %r in %s: empty provenance suffix" % (source, table))

    if token in VERIFIED_TOKEN_TABLES:
        if table not in VERIFIED_TOKEN_TABLES[token]:
            raise SourceRegistryError(
                "verified token %r is not registered for table %s" % (token, table))
        if sep:
            lowered = suffix.lower()
            for marker in BLACKLIST_SUFFIX_MARKERS:
                if marker in lowered:
                    raise SourceRegistryError(
                        "blacklisted provenance marker %r in verified suffix of "
                        "%r (%s)" % (marker, source, table))
        return 1

    if token in UNVERIFIED_TOKEN_TABLES:
        if table not in UNVERIFIED_TOKEN_TABLES[token]:
            raise SourceRegistryError(
                "unverified token %r is outside its observed tables (%s)"
                % (token, table))
        if token == QUARANTINE_SOURCE:
            if sep:
                raise SourceRegistryError(
                    "reserved quarantine token may not carry a suffix: %r" % (source,))
            if vehicle_id is not None and vehicle_id not in QUARANTINED_VEHICLE_IDS:
                raise SourceRegistryError(
                    "quarantine token used outside the IC-01 cohort "
                    "(vehicle %r, table %s)" % (vehicle_id, table))
        return 0

    raise SourceRegistryError(
        "unknown source token %r in %s (register-by-ruling only)" % (token, table))


def bare_rows_digest(cur):
    """(count, sha256hex) over the grandfathered bare-token rows. Canonical
    serialization: per row, a JSON array of the table name followed by
    [column, value] pairs for every non-source column in schema order; all rows
    sorted lexicographically, each line hashed with a trailing newline."""
    lines = []
    for table in BARE_ROW_TABLES:
        cols = [r[1] for r in cur.execute(
            'PRAGMA table_info("%s")' % table).fetchall()]
        non_source = [c for c in cols if c != "source"]
        for row in cur.execute(
                'SELECT * FROM "%s" WHERE source = ?' % table,
                (BARE_VERIFIED_TOKEN,)).fetchall():
            values = dict(zip(cols, row))
            lines.append(json.dumps(
                [table] + [[c, values[c]] for c in non_source],
                ensure_ascii=True, separators=(",", ":")))
    digest = hashlib.sha256()
    for line in sorted(lines):
        digest.update(line.encode())
        digest.update(b"\n")
    return len(lines), digest.hexdigest()


def assert_frozen_landscape(cur):
    """Hold the database's source landscape equal to the registry's frozen
    declarations: source-bearing tables == dispositioned tables, the blocked
    ev_specs table keeps its exact frozen shape, and the grandfathered bare-token
    rows keep their exact count and content digest. Raises SourceRegistryError."""
    table_names = [name for (name,) in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'").fetchall()]
    source_tables = set()
    for table in table_names:
        cols = {r[1] for r in cur.execute(
            'PRAGMA table_info("%s")' % table.replace('"', '""')).fetchall()}
        if "source" in cols:
            source_tables.add(table)
    if source_tables != set(TABLE_DISPOSITIONS):
        raise SourceRegistryError(
            "source-bearing tables drifted from the registry dispositions: "
            "undispositioned=%s missing=%s"
            % (sorted(source_tables - set(TABLE_DISPOSITIONS)),
               sorted(set(TABLE_DISPOSITIONS) - source_tables)))

    ev_count = cur.execute(
        'SELECT COUNT(*) FROM "%s"' % EV_TABLE).fetchone()[0]
    if ev_count != EV_FROZEN_ROW_COUNT:
        raise SourceRegistryError(
            "ev_specs is frozen pending IC-02E: %d row(s), expected %d"
            % (ev_count, EV_FROZEN_ROW_COUNT))
    ev_sources = {s for (s,) in cur.execute(
        'SELECT DISTINCT source FROM "%s"' % EV_TABLE).fetchall()}
    if ev_sources != {EV_FROZEN_SOURCE}:
        raise SourceRegistryError(
            "ev_specs is frozen pending IC-02E: sources %s, expected exactly %r"
            % (sorted(map(repr, ev_sources)), EV_FROZEN_SOURCE))

    count, digest = bare_rows_digest(cur)
    if count != BARE_ROW_COUNT or digest != BARE_ROW_SHA256:
        raise SourceRegistryError(
            "citation-debt freeze violated: bare %r rows count=%d digest=%s "
            "(frozen: count=%d digest=%s). New/changed verified rows require a "
            "provenance suffix; changes to the grandfathered set need a ruling."
            % (BARE_VERIFIED_TOKEN, count, digest, BARE_ROW_COUNT, BARE_ROW_SHA256))
