import requests, sqlite3, json, time, sys, io, logging

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DB_FILE = "wrench_vehicles.db"
BASE = "https://vpic.nhtsa.dot.gov/api/vehicles"
DELAY = 0.2
LOG = "vpic_backfill.log"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(LOG, encoding="utf-8"), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

# Top models people still drive from 1981-2002
TARGET_MAKES_MODELS = [
    ("Toyota","Camry"),("Toyota","Corolla"),("Toyota","Tacoma"),("Toyota","4Runner"),
    ("Toyota","Land Cruiser"),("Toyota","Celica"),("Toyota","Supra"),("Toyota","MR2"),
    ("Toyota","Pickup"),("Toyota","Tercel"),("Toyota","Previa"),
    ("Honda","Civic"),("Honda","Accord"),("Honda","CR-V"),("Honda","Prelude"),
    ("Honda","Odyssey"),("Honda","Passport"),("Honda","Del Sol"),
    ("Ford","F-150"),("Ford","Explorer"),("Ford","Mustang"),("Ford","Ranger"),
    ("Ford","Bronco"),("Ford","Taurus"),("Ford","Escort"),("Ford","F-250"),
    ("Chevrolet","C/K 1500"),("Chevrolet","Silverado 1500"),("Chevrolet","Blazer"),
    ("Chevrolet","Camaro"),("Chevrolet","Corvette"),("Chevrolet","S-10"),
    ("Chevrolet","Suburban"),("Chevrolet","Tahoe"),("Chevrolet","Cavalier"),
    ("GMC","Sierra 1500"),("GMC","Jimmy"),("GMC","Yukon"),("GMC","Sonoma"),
    ("Nissan","Altima"),("Nissan","Sentra"),("Nissan","Maxima"),("Nissan","Pathfinder"),
    ("Nissan","Frontier"),("Nissan","Xterra"),("Nissan","240SX"),("Nissan","300ZX"),
    ("Dodge","Ram 1500"),("Dodge","Caravan"),("Dodge","Dakota"),("Dodge","Neon"),
    ("Dodge","Intrepid"),("Dodge","Viper"),
    ("Jeep","Grand Cherokee"),("Jeep","Wrangler"),("Jeep","Cherokee"),
    ("Subaru","Legacy"),("Subaru","Impreza"),("Subaru","Outback"),("Subaru","Forester"),
    ("BMW","3 Series"),("BMW","5 Series"),("BMW","7 Series"),("BMW","M3"),
    ("Mercedes-Benz","C-Class"),("Mercedes-Benz","E-Class"),("Mercedes-Benz","S-Class"),
    ("Volkswagen","Jetta"),("Volkswagen","Golf"),("Volkswagen","Passat"),("Volkswagen","Beetle"),
    ("Mazda","626"),("Mazda","Miata"),("Mazda","Protege"),("Mazda","MPV"),("Mazda","RX-7"),
    ("Pontiac","Firebird"),("Pontiac","Grand Am"),("Pontiac","Grand Prix"),("Pontiac","Trans Am"),
    ("Buick","LeSabre"),("Buick","Century"),("Buick","Regal"),("Buick","Riviera"),
    ("Oldsmobile","Cutlass Supreme"),("Oldsmobile","88"),("Oldsmobile","Aurora"),
    ("Cadillac","DeVille"),("Cadillac","Eldorado"),("Cadillac","Seville"),("Cadillac","Fleetwood"),
    ("Lincoln","Town Car"),("Lincoln","Continental"),("Lincoln","Mark VIII"),
    ("Mercury","Grand Marquis"),("Mercury","Villager"),("Mercury","Cougar"),
    ("Chrysler","Town & Country"),("Chrysler","LeBaron"),("Chrysler","300M"),
    ("Acura","Integra"),("Acura","Legend"),("Acura","NSX"),("Acura","TL"),
    ("Lexus","ES 300"),("Lexus","GS 300"),("Lexus","LS 400"),("Lexus","SC 300"),
    ("Infiniti","Q45"),("Infiniti","J30"),("Infiniti","G20"),
    ("Mitsubishi","Eclipse"),("Mitsubishi","Galant"),("Mitsubishi","3000GT"),("Mitsubishi","Montero"),
    ("Hyundai","Elantra"),("Hyundai","Sonata"),("Hyundai","Accent"),("Hyundai","Tiburon"),
    ("Kia","Sportage"),("Kia","Sephia"),
    ("Volvo","850"),("Volvo","940"),("Volvo","S70"),("Volvo","V70"),
    ("Saab","900"),("Saab","9000"),
    ("Audi","A4"),("Audi","A6"),("Audi","A8"),("Audi","80"),("Audi","90"),
    ("Porsche","911"),("Porsche","944"),("Porsche","968"),("Porsche","Boxster"),
    ("Isuzu","Rodeo"),("Isuzu","Trooper"),("Isuzu","Pickup"),
    ("Suzuki","Sidekick"),("Suzuki","Samurai"),("Suzuki","Swift"),
    ("Land Rover","Range Rover"),("Land Rover","Discovery"),
    ("Saturn","SL"),("Saturn","SC"),("Saturn","SW"),
]

YEARS = list(range(1981, 2003))  # 1981-2002

def vpic_get(path, params=None):
    p = params or {}
    p["format"] = "json"
    try:
        r = requests.get(f"{BASE}/{path}", params=p, timeout=10)
        r.raise_for_status()
        return r.json()
    except: return None

def get_models_for_make_year(make, year):
    data = vpic_get(f"GetModelsForMakeYear/make/{make}/modelyear/{year}")
    if data and data.get("Results"):
        return data["Results"]
    return []

def setup_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY, year INTEGER, make TEXT, model TEXT,
            engine TEXT, trim TEXT, pulled_at TEXT
        );
        CREATE TABLE IF NOT EXISTS vpic_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER UNIQUE,
            make_id INTEGER, model_id INTEGER,
            body_class TEXT, drive_type TEXT, engine_cylinders TEXT,
            displacement_l REAL, fuel_type TEXT, plant_city TEXT,
            vehicle_type TEXT, note TEXT
        );
    """)
    conn.commit()

def get_next_id(conn):
    r = conn.execute("SELECT MAX(id) FROM vehicles").fetchone()[0]
    return (r or 0) + 1

def main():
    conn = sqlite3.connect(DB_FILE)
    setup_db(conn)

    # unique, decreasing negative IDs (MAX(id)+1 collided because MAX is the positive id space)
    _min = conn.execute("SELECT MIN(id) FROM vehicles").fetchone()[0]
    next_neg = (_min if (_min is not None and _min < 0) else -100000) - 1

    added = 0
    skipped = 0
    req_count = 0

    for make, model in TARGET_MAKES_MODELS:
        for year in YEARS:
            # Check if already exists
            existing = conn.execute(
                "SELECT id FROM vehicles WHERE year=? AND make=? AND model=?",
                (year, make, model)
            ).fetchone()
            if existing:
                skipped += 1
                continue

            # Query vPIC
            results = get_models_for_make_year(make, year)
            req_count += 1
            time.sleep(DELAY)

            # Find matching model
            match = next((r for r in results
                if r.get("Model_Name","").lower() == model.lower()), None)
            if not match:
                match = next((r for r in results
                    if model.lower() in r.get("Model_Name","").lower()), None)

            if not match:
                continue

            # Insert vehicle with a unique, decreasing negative ID
            # (MAX(id)+1 collided: MAX is dominated by the positive id space and
            #  never moved, so every row got the same id and INSERT OR IGNORE dropped them)
            vid = next_neg
            next_neg -= 1

            conn.execute(
                "INSERT OR IGNORE INTO vehicles VALUES (?,?,?,?,?,?,?)",
                (vid, year, make, model, None, None,
                 f"vpic-{year}-{make}-{model}")
            )

            # Store vPIC metadata
            conn.execute("""
                INSERT OR IGNORE INTO vpic_specs
                (vehicle_id, make_id, model_id, vehicle_type, note)
                VALUES (?,?,?,?,?)
            """, (vid, match.get("Make_ID"), match.get("Model_ID"),
                  match.get("VehicleTypeName"), "vPIC data — partial specs"))

            conn.commit()
            added += 1

            if added % 50 == 0:
                total = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
                log.info(f"Added {added} vehicles | {req_count} reqs | {total} total in DB")

    total = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    log.info(f"DONE! Added {added} new vehicles. Skipped {skipped}. Total: {total}. Requests: {req_count}")
    conn.close()

if __name__ == "__main__":
    main()
