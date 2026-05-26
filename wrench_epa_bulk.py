import requests, sqlite3, csv, io, zipfile, sys, logging

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = __import__('io').TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DB_FILE = "wrench_vehicles.db"
EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
EPA_CSV = "vehicles.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler("epa_bulk.log", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

def add_column_if_missing(conn, table, col, coltype):
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if col not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
        conn.commit()
        log.info(f"  Added column {table}.{col}")

def setup_db(conn):
    # Create epa_data table
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS epa_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER, make TEXT, model TEXT,
            city_mpg INTEGER, hwy_mpg INTEGER, comb_mpg INTEGER,
            annual_cost INTEGER, drive TEXT, transmission TEXT,
            engine TEXT, fuel_type TEXT,
            range_ev INTEGER, city_ev INTEGER, hwy_ev INTEGER, comb_ev INTEGER,
            UNIQUE(year, make, model, drive, transmission)
        );
        CREATE TABLE IF NOT EXISTS fuel_economy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER, city_mpg INTEGER, highway_mpg INTEGER,
            combined_mpg INTEGER, annual_fuel_cost INTEGER,
            engine TEXT, transmission TEXT, drive TEXT
        );
    """)
    # Safely add new columns to fuel_economy if missing
    for col, typ in [("range_ev","INTEGER"),("city_ev","INTEGER"),
                     ("hwy_ev","INTEGER"),("comb_ev","INTEGER"),("fuel_type","TEXT")]:
        add_column_if_missing(conn, "fuel_economy", col, typ)
    conn.commit()

def download_epa():
    log.info("Downloading EPA data from fueleconomy.gov...")
    r = requests.get(EPA_URL, timeout=120, stream=True)
    r.raise_for_status()
    total = int(r.headers.get('content-length', 0))
    data = b""
    downloaded = 0
    for chunk in r.iter_content(chunk_size=65536):
        data += chunk
        downloaded += len(chunk)
        if total:
            print(f"\r  {downloaded/total*100:.0f}% ({downloaded//1024//1024}MB/{total//1024//1024}MB)", end="", flush=True)
    print()
    z = zipfile.ZipFile(io.BytesIO(data))
    csv_data = z.read(EPA_CSV).decode("utf-8", errors="replace")
    log.info(f"Downloaded and extracted: {len(csv_data)//1024}KB")
    return csv_data

def parse_epa(csv_data):
    reader = csv.DictReader(io.StringIO(csv_data))
    rows = []
    for row in reader:
        try:
            year = int(row.get("year", 0))
            if not (1984 <= year <= 2026): continue
            make  = (row.get("make") or "").strip()
            model = (row.get("model") or "").strip()
            if not make or not model: continue

            city = row.get("city08") or ""
            hwy  = row.get("highway08") or ""
            comb = row.get("comb08") or ""
            cost = row.get("fuelCost08") or ""
            eng  = row.get("displ") or ""
            cyls = row.get("cylinders") or ""

            # Build engine string e.g. "2.5L I4"
            engine_str = None
            if eng:
                try:
                    disp = float(eng)
                    engine_str = f"{disp:.1f}L"
                    if cyls:
                        c = int(float(cyls))
                        cfg = {4:"I4",6:"V6",8:"V8",3:"I3",5:"I5",
                               10:"V10",12:"V12"}.get(c, f"V{c}" if c>4 else f"I{c}")
                        engine_str += f" {cfg}"
                except: pass

            rows.append({
                "year": year, "make": make, "model": model,
                "city":  int(float(city))  if city  else None,
                "hwy":   int(float(hwy))   if hwy   else None,
                "comb":  int(float(comb))  if comb  else None,
                "cost":  int(float(cost))  if cost  else None,
                "drive": row.get("drive",""), "trans": row.get("trany",""),
                "engine": engine_str, "fuel": row.get("fuelType1",""),
                "range_ev": int(float(row.get("range","0") or 0)) or None,
                "city_ev":  int(float(row.get("cityE","0")  or 0)) or None,
                "hwy_ev":   int(float(row.get("highwayE","0") or 0)) or None,
                "comb_ev":  int(float(row.get("combE","0")  or 0)) or None,
            })
        except: continue
    log.info(f"Parsed {len(rows):,} EPA records")
    return rows

def import_epa(conn, rows):
    vehicles = conn.execute("SELECT id, year, make, model FROM vehicles").fetchall()
    veh_lookup = {(yr, mk.lower(), mdl.lower()): vid for vid, yr, mk, mdl in vehicles}
    have_mpg = set(r[0] for r in conn.execute(
        "SELECT DISTINCT vehicle_id FROM fuel_economy WHERE city_mpg IS NOT NULL").fetchall())

    inserted_epa = matched = engines_filled = 0

    for i, row in enumerate(rows):
        yr, mk, mdl = row["year"], row["make"], row["model"]

        # Insert full EPA record
        try:
            conn.execute("""INSERT OR IGNORE INTO epa_data
                (year,make,model,city_mpg,hwy_mpg,comb_mpg,annual_cost,
                 drive,transmission,engine,fuel_type,range_ev,city_ev,hwy_ev,comb_ev)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (yr,mk,mdl,row["city"],row["hwy"],row["comb"],row["cost"],
                 row["drive"],row["trans"],row["engine"],row["fuel"],
                 row["range_ev"],row["city_ev"],row["hwy_ev"],row["comb_ev"]))
            inserted_epa += 1
        except: pass

        # Match to our vehicles
        vid = veh_lookup.get((yr, mk.lower(), mdl.lower()))
        if not vid:
            for (vyr,vmk,vmdl),v in veh_lookup.items():
                if vyr==yr and vmk==mk.lower() and (mdl.lower() in vmdl or vmdl in mdl.lower()):
                    vid=v; break

        if vid and vid not in have_mpg and row["city"]:
            try:
                conn.execute("""INSERT OR IGNORE INTO fuel_economy
                    (vehicle_id,city_mpg,highway_mpg,combined_mpg,annual_fuel_cost,
                     engine,transmission,drive,range_ev,city_ev,hwy_ev,comb_ev,fuel_type)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (vid,row["city"],row["hwy"],row["comb"],row["cost"],
                     row["engine"],row["trans"],row["drive"],
                     row["range_ev"],row["city_ev"],row["hwy_ev"],row["comb_ev"],row["fuel"]))
                have_mpg.add(vid)
                matched += 1
            except: pass

        if vid and row["engine"]:
            conn.execute("UPDATE vehicles SET engine=? WHERE id=? AND (engine IS NULL OR engine='')",
                (row["engine"], vid))
            engines_filled += 1

        if i % 5000 == 0 and i > 0:
            conn.commit()
            log.info(f"  Processed {i:,}/{len(rows):,} records...")

    conn.commit()
    return inserted_epa, matched, engines_filled

def main():
    log.info("=== EPA Bulk Fuel Economy Import ===")
    conn = sqlite3.connect(DB_FILE)
    setup_db(conn)

    before = conn.execute("SELECT COUNT(DISTINCT vehicle_id) FROM fuel_economy WHERE city_mpg IS NOT NULL").fetchone()[0]
    log.info(f"Vehicles with MPG before: {before}")

    csv_data = download_epa()
    rows = parse_epa(csv_data)
    inserted_epa, matched, engines = import_epa(conn, rows)

    after = conn.execute("SELECT COUNT(DISTINCT vehicle_id) FROM fuel_economy WHERE city_mpg IS NOT NULL").fetchone()[0]
    total_epa = conn.execute("SELECT COUNT(*) FROM epa_data").fetchone()[0]
    ev_count = conn.execute("SELECT COUNT(*) FROM fuel_economy WHERE range_ev > 0").fetchone()[0]

    log.info(f"""
=== DONE ===
  EPA records stored:    {total_epa:,}
  Vehicles with MPG:     {before} -> {after} (+{after-before})
  Engine strings added:  {engines}
  EV range entries:      {ev_count}
    """)
    conn.close()

if __name__ == "__main__":
    main()
