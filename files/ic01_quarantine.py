"""IC-01 applicability quarantine contract (build-time only).

These fifth-generation CR-V records were populated from one 2018 owner's
manual whose tables combine engine, trim, tire, and drivetrain variants.  The
values remain in the local research database for later exact-year recovery,
but no maintenance/specification value may cross a shipped projection until
applicability is re-established.
"""

QUARANTINED_VEHICLE_IDS = frozenset({12372, 12511, 12777, 12847, 12912})
QUARANTINE_SOURCE = "quarantine-applicability-ic01"
HOMEPAGE_SAMPLE_ID = 467

EXPECTED_HOMEPAGE_SAMPLE = {
    "id": 467,
    "identity": (2020, "Nissan", "Sentra", None, "2.0L I4"),
    "oil_visc": "0W-20",
    "oil_cap_w": "4.4 qt",
    "recall_count": 4,
}

EXPECTED_PUBLIC_IDENTITIES = {
    12372: (2017, "Honda", "CR-V", None, "1.5L Turbo"),
    12511: (2018, "Honda", "CR-V", None, "1.5L Turbo"),
    12777: (2020, "Honda", "CR-V", None, "1.5L Turbo"),
    12847: (2021, "Honda", "CR-V", None, "1.5L Turbo"),
    12912: (2022, "Honda", "CR-V", None, "1.5L Turbo"),
}

EXPECTED_DB_ROWS = {
    "oil_change": 5,
    "parts": 5,
    "fluids": 5,
    "torque_specs": 5,
    "maintenance": 15,
}

_BARE_SHELL_KEYS = ("oil", "parts", "fluids")
_ABSENT_KEYS = ("torque", "maint", "maint_parts")


def projection_problems(records):
    """Return every violation of the public IC-01 quarantine shape."""
    by_id = {}
    duplicates = set()
    for record in records:
        vehicle_id = record.get("id")
        if vehicle_id in QUARANTINED_VEHICLE_IDS:
            if vehicle_id in by_id:
                duplicates.add(vehicle_id)
            by_id[vehicle_id] = record

    problems = []
    if duplicates:
        problems.append("duplicate quarantined vehicle id(s): %s" % sorted(duplicates))

    missing = sorted(QUARANTINED_VEHICLE_IDS - set(by_id))
    if missing:
        problems.append("missing quarantined vehicle id(s): %s" % missing)

    for vehicle_id in sorted(by_id):
        record = by_id[vehicle_id]
        identity = tuple(record.get(key) for key in ("year", "make", "model", "trim", "engine"))
        if identity != EXPECTED_PUBLIC_IDENTITIES[vehicle_id]:
            problems.append(
                "vehicle %s identity %r != %r"
                % (vehicle_id, identity, EXPECTED_PUBLIC_IDENTITIES[vehicle_id])
            )
        for key in _BARE_SHELL_KEYS:
            if record.get(key) != {"ver": 0}:
                problems.append(
                    "vehicle %s %s must be the bare {'ver': 0} shell" % (vehicle_id, key)
                )
        for key in _ABSENT_KEYS:
            if key in record:
                problems.append("vehicle %s must not ship %s" % (vehicle_id, key))
        if not isinstance(record.get("mpg"), list) or not record["mpg"]:
            problems.append("vehicle %s must retain its EPA MPG projection" % vehicle_id)
        if not isinstance(record.get("recalls"), list) or not record["recalls"]:
            problems.append("vehicle %s must retain its NHTSA recall projection" % vehicle_id)
        if not isinstance(record.get("safety"), dict) or not record["safety"]:
            problems.append("vehicle %s must retain its NHTSA safety projection" % vehicle_id)
        complaints = record.get("comps_agg")
        if (
            not isinstance(complaints, dict)
            or not complaints.get("n")
            or not complaints.get("topics")
            or not complaints.get("through")
        ):
            problems.append("vehicle %s must retain its NHTSA complaint projection" % vehicle_id)
    return problems
