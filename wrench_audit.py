import sqlite3, json, os

# Repo-relative so the audit reads the canonical in-tree DB, not a frozen absolute
# copy (2026-07-04: removed a hardcoded OneDrive path during the off-OneDrive migration).
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wrench_vehicles.db")
conn = sqlite3.connect(DB)
c = conn.cursor()

total = c.execute("SELECT COUNT(*) FROM vehicles WHERE id > 0").fetchone()[0]
print(f"\n{'='*60}")
print(f"KNOW YOUR RIDE — DATA AUDIT")
print(f"Total Vehicle Finder vehicles: {total}")
print(f"{'='*60}\n")

checks = [
    ("Maintenance schedules", "SELECT COUNT(DISTINCT vehicle_id) FROM maintenance WHERE vehicle_id > 0"),
    ("Oil change data", "SELECT COUNT(*) FROM oil_change WHERE vehicle_id > 0 AND viscosity IS NOT NULL"),
    ("Spark plug data", "SELECT COUNT(*) FROM parts WHERE vehicle_id > 0 AND spark_plug_type IS NOT NULL"),
    ("Air filter data", "SELECT COUNT(*) FROM parts WHERE vehicle_id > 0 AND air_filters_json IS NOT NULL"),
    ("Battery data", "SELECT COUNT(*) FROM parts WHERE vehicle_id > 0 AND batteries_json IS NOT NULL"),
    ("Transmission fluid", "SELECT COUNT(*) FROM fluids WHERE vehicle_id > 0 AND transmission_fluid IS NOT NULL"),
    ("Coolant data", "SELECT COUNT(*) FROM fluids WHERE vehicle_id > 0 AND coolant_type IS NOT NULL"),
    ("Torque specs", "SELECT COUNT(DISTINCT vehicle_id) FROM torque_specs WHERE vehicle_id > 0"),
    ("Service costs", "SELECT COUNT(DISTINCT vehicle_id) FROM service_costs WHERE vehicle_id > 0"),
    ("Safety ratings", "SELECT COUNT(*) FROM safety_ratings WHERE vehicle_id > 0 AND overall_rating IS NOT NULL"),
    ("Fuel economy", "SELECT COUNT(DISTINCT vehicle_id) FROM fuel_economy WHERE vehicle_id > 0"),
    ("Warranty data", "SELECT COUNT(DISTINCT vehicle_id) FROM warranty WHERE vehicle_id > 0"),
    ("Fuse locations", "SELECT COUNT(*) FROM fuse_locations WHERE primary_fuse_box IS NOT NULL"),
    ("Recalls", "SELECT COUNT(DISTINCT vehicle_id) FROM recalls WHERE vehicle_id > 0"),
]

print(f"{'Data Type':<25} {'Have Data':>10} {'Missing':>10} {'Coverage':>10}")
print("-"*60)
for label, query in checks:
    try:
        count = c.execute(query).fetchone()[0]
        missing = total - count
        pct = (count/total*100) if total > 0 else 0
        print(f"{label:<25} {count:>10,} {missing:>10,} {pct:>9.1f}%")
    except Exception as e:
        print(f"{label:<25} ERROR: {e}")

# 2020 Toyota Camry specific check
print(f"\n{'='*60}")
print("2020 TOYOTA CAMRY — DETAILED CHECK")
print(f"{'='*60}")
v = c.execute("SELECT id FROM vehicles WHERE year=2020 AND make='Toyota' AND model='Camry' AND id > 0").fetchone()
if v:
    vid = v[0]
    print(f"Vehicle ID: {vid}")
    checks2 = [
        ("Oil change", f"SELECT COUNT(*) FROM oil_change WHERE vehicle_id={vid}"),
        ("Parts", f"SELECT COUNT(*) FROM parts WHERE vehicle_id={vid}"),
        ("Maintenance schedules", f"SELECT COUNT(*) FROM maintenance WHERE vehicle_id={vid}"),
        ("Fluids", f"SELECT COUNT(*) FROM fluids WHERE vehicle_id={vid}"),
        ("Torque specs", f"SELECT COUNT(*) FROM torque_specs WHERE vehicle_id={vid}"),
        ("Service costs", f"SELECT COUNT(*) FROM service_costs WHERE vehicle_id={vid}"),
        ("Safety ratings", f"SELECT COUNT(*) FROM safety_ratings WHERE vehicle_id={vid}"),
        ("Fuel economy", f"SELECT COUNT(*) FROM fuel_economy WHERE vehicle_id={vid}"),
        ("Warranty", f"SELECT COUNT(*) FROM warranty WHERE vehicle_id={vid}"),
        ("Recalls", f"SELECT COUNT(*) FROM recalls WHERE vehicle_id={vid}"),
        ("Fuse location", f"SELECT COUNT(*) FROM fuse_locations WHERE vehicle_id={vid}"),
    ]
    for label, query in checks2:
        count = c.execute(query).fetchone()[0]
        status = "✅" if count > 0 else "❌ MISSING"
        print(f"  {label:<25} {count:>5} rows  {status}")
else:
    print("  2020 Toyota Camry not found in database!")

# Top 20 most complained-about vehicles missing maintenance
print(f"\n{'='*60}")
print("TOP 20 HIGH-COMPLAINT VEHICLES MISSING MAINTENANCE DATA")
print(f"{'='*60}")
missing_maint = c.execute("""
    SELECT v.year, v.make, v.model, COUNT(comp.id) as complaints
    FROM vehicles v
    LEFT JOIN complaints comp ON comp.vehicle_id = v.id
    WHERE v.id > 0
    AND v.id NOT IN (SELECT DISTINCT vehicle_id FROM maintenance WHERE vehicle_id > 0)
    GROUP BY v.id
    ORDER BY complaints DESC
    LIMIT 20
""").fetchall()
print(f"{'Year':<6} {'Make':<20} {'Model':<25} {'Complaints':>10}")
print("-"*65)
for row in missing_maint:
    print(f"{row[0]:<6} {row[1]:<20} {row[2]:<25} {row[3]:>10,}")

conn.close()
print(f"\n{'='*60}")
print("AUDIT COMPLETE")
print(f"{'='*60}")
