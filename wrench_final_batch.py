import os
import requests, sqlite3, json, time, sys, io, logging
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_KEY  = os.environ.get("VEHICLE_FINDER_KEY", "")
BASE_URL = "https://api.vehicle-finder.com/v1"
DB_FILE  = "wrench_vehicles.db"
DELAY    = 0.25

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler("wrench_final.log", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

TARGET = [
    # ── 1990-1995 classics still on the road ──
    (1995,"Toyota","Camry"),(1994,"Toyota","Camry"),(1993,"Toyota","Camry"),
    (1992,"Toyota","Camry"),(1991,"Toyota","Camry"),(1990,"Toyota","Camry"),
    (1995,"Toyota","Corolla"),(1994,"Toyota","Corolla"),(1993,"Toyota","Corolla"),
    (1992,"Toyota","Corolla"),(1991,"Toyota","Corolla"),(1990,"Toyota","Corolla"),
    (1995,"Toyota","4Runner"),(1994,"Toyota","4Runner"),(1993,"Toyota","4Runner"),
    (1992,"Toyota","4Runner"),(1991,"Toyota","4Runner"),(1990,"Toyota","4Runner"),
    (1995,"Toyota","Pickup"),(1994,"Toyota","Pickup"),(1993,"Toyota","Pickup"),
    (1992,"Toyota","Pickup"),(1991,"Toyota","Pickup"),(1990,"Toyota","Pickup"),
    (1995,"Toyota","Land Cruiser"),(1994,"Toyota","Land Cruiser"),
    (1993,"Toyota","Land Cruiser"),(1992,"Toyota","Land Cruiser"),
    (1995,"Toyota","Celica"),(1994,"Toyota","Celica"),(1993,"Toyota","Celica"),
    (1995,"Toyota","Supra"),(1994,"Toyota","Supra"),(1993,"Toyota","Supra"),
    (1995,"Honda","Civic"),(1994,"Honda","Civic"),(1993,"Honda","Civic"),
    (1992,"Honda","Civic"),(1991,"Honda","Civic"),(1990,"Honda","Civic"),
    (1995,"Honda","Accord"),(1994,"Honda","Accord"),(1993,"Honda","Accord"),
    (1992,"Honda","Accord"),(1991,"Honda","Accord"),(1990,"Honda","Accord"),
    (1995,"Honda","Prelude"),(1994,"Honda","Prelude"),(1993,"Honda","Prelude"),
    (1995,"Honda","CR-V"),
    (1995,"Honda","Passport"),(1994,"Honda","Passport"),
    (1995,"Ford","F-150"),(1994,"Ford","F-150"),(1993,"Ford","F-150"),
    (1992,"Ford","F-150"),(1991,"Ford","F-150"),(1990,"Ford","F-150"),
    (1995,"Ford","Explorer"),(1994,"Ford","Explorer"),(1993,"Ford","Explorer"),
    (1992,"Ford","Explorer"),(1991,"Ford","Explorer"),
    (1995,"Ford","Mustang"),(1994,"Ford","Mustang"),(1993,"Ford","Mustang"),
    (1992,"Ford","Mustang"),(1991,"Ford","Mustang"),(1990,"Ford","Mustang"),
    (1995,"Ford","Ranger"),(1994,"Ford","Ranger"),(1993,"Ford","Ranger"),
    (1992,"Ford","Ranger"),(1991,"Ford","Ranger"),(1990,"Ford","Ranger"),
    (1995,"Ford","Bronco"),(1994,"Ford","Bronco"),(1993,"Ford","Bronco"),
    (1992,"Ford","Bronco"),(1991,"Ford","Bronco"),(1990,"Ford","Bronco"),
    (1995,"Ford","Taurus"),(1994,"Ford","Taurus"),(1993,"Ford","Taurus"),
    (1992,"Ford","Taurus"),(1991,"Ford","Taurus"),(1990,"Ford","Taurus"),
    (1995,"Chevrolet","C/K 1500"),(1994,"Chevrolet","C/K 1500"),
    (1993,"Chevrolet","C/K 1500"),(1992,"Chevrolet","C/K 1500"),
    (1991,"Chevrolet","C/K 1500"),(1990,"Chevrolet","C/K 1500"),
    (1995,"Chevrolet","Suburban"),(1994,"Chevrolet","Suburban"),
    (1993,"Chevrolet","Suburban"),(1992,"Chevrolet","Suburban"),
    (1995,"Chevrolet","Blazer"),(1994,"Chevrolet","Blazer"),
    (1993,"Chevrolet","Blazer"),(1992,"Chevrolet","Blazer"),
    (1995,"Chevrolet","Camaro"),(1994,"Chevrolet","Camaro"),
    (1993,"Chevrolet","Camaro"),(1992,"Chevrolet","Camaro"),
    (1991,"Chevrolet","Camaro"),(1990,"Chevrolet","Camaro"),
    (1995,"Chevrolet","Corvette"),(1994,"Chevrolet","Corvette"),
    (1993,"Chevrolet","Corvette"),(1992,"Chevrolet","Corvette"),
    (1991,"Chevrolet","Corvette"),(1990,"Chevrolet","Corvette"),
    (1995,"Chevrolet","S-10"),(1994,"Chevrolet","S-10"),
    (1993,"Chevrolet","S-10"),(1992,"Chevrolet","S-10"),
    (1995,"Chevrolet","Cavalier"),(1994,"Chevrolet","Cavalier"),
    (1993,"Chevrolet","Cavalier"),(1992,"Chevrolet","Cavalier"),
    (1995,"GMC","Sierra 1500"),(1994,"GMC","Sierra 1500"),
    (1993,"GMC","Sierra 1500"),(1992,"GMC","Sierra 1500"),
    (1995,"GMC","Yukon"),(1994,"GMC","Yukon"),(1993,"GMC","Yukon"),
    (1995,"GMC","Jimmy"),(1994,"GMC","Jimmy"),(1993,"GMC","Jimmy"),
    (1995,"Nissan","Altima"),(1994,"Nissan","Altima"),(1993,"Nissan","Altima"),
    (1995,"Nissan","Sentra"),(1994,"Nissan","Sentra"),(1993,"Nissan","Sentra"),
    (1992,"Nissan","Sentra"),(1991,"Nissan","Sentra"),(1990,"Nissan","Sentra"),
    (1995,"Nissan","Pathfinder"),(1994,"Nissan","Pathfinder"),
    (1993,"Nissan","Pathfinder"),(1992,"Nissan","Pathfinder"),
    (1995,"Nissan","Maxima"),(1994,"Nissan","Maxima"),(1993,"Nissan","Maxima"),
    (1995,"Nissan","240SX"),(1994,"Nissan","240SX"),(1993,"Nissan","240SX"),
    (1995,"Dodge","Ram 1500"),(1994,"Dodge","Ram 1500"),(1993,"Dodge","Ram 1500"),
    (1992,"Dodge","Ram 1500"),(1991,"Dodge","Ram 1500"),(1990,"Dodge","Ram 1500"),
    (1995,"Dodge","Caravan"),(1994,"Dodge","Caravan"),(1993,"Dodge","Caravan"),
    (1992,"Dodge","Caravan"),(1991,"Dodge","Caravan"),(1990,"Dodge","Caravan"),
    (1995,"Dodge","Dakota"),(1994,"Dodge","Dakota"),(1993,"Dodge","Dakota"),
    (1995,"Dodge","Neon"),(1994,"Dodge","Neon"),
    (1995,"Jeep","Grand Cherokee"),(1994,"Jeep","Grand Cherokee"),
    (1993,"Jeep","Grand Cherokee"),
    (1995,"Jeep","Wrangler"),(1994,"Jeep","Wrangler"),(1993,"Jeep","Wrangler"),
    (1992,"Jeep","Wrangler"),(1991,"Jeep","Wrangler"),(1990,"Jeep","Wrangler"),
    (1995,"Jeep","Cherokee"),(1994,"Jeep","Cherokee"),(1993,"Jeep","Cherokee"),
    (1992,"Jeep","Cherokee"),(1991,"Jeep","Cherokee"),(1990,"Jeep","Cherokee"),
    (1995,"Subaru","Legacy"),(1994,"Subaru","Legacy"),(1993,"Subaru","Legacy"),
    (1992,"Subaru","Legacy"),(1991,"Subaru","Legacy"),(1990,"Subaru","Legacy"),
    (1995,"Subaru","Impreza"),(1994,"Subaru","Impreza"),(1993,"Subaru","Impreza"),
    (1995,"Subaru","SVX"),(1994,"Subaru","SVX"),(1993,"Subaru","SVX"),
    (1995,"BMW","325i"),(1994,"BMW","325i"),(1993,"BMW","325i"),
    (1992,"BMW","325i"),(1991,"BMW","325i"),(1990,"BMW","325i"),
    (1995,"BMW","M3"),(1994,"BMW","M3"),
    (1995,"BMW","530i"),(1994,"BMW","530i"),(1993,"BMW","530i"),
    (1995,"Acura","Integra"),(1994,"Acura","Integra"),(1993,"Acura","Integra"),
    (1992,"Acura","Integra"),(1991,"Acura","Integra"),(1990,"Acura","Integra"),
    (1995,"Acura","Legend"),(1994,"Acura","Legend"),(1993,"Acura","Legend"),
    (1992,"Acura","Legend"),(1991,"Acura","Legend"),(1990,"Acura","Legend"),
    (1995,"Acura","NSX"),(1994,"Acura","NSX"),(1993,"Acura","NSX"),
    (1995,"Lexus","ES 300"),(1994,"Lexus","ES 300"),(1993,"Lexus","ES 300"),
    (1992,"Lexus","ES 300"),(1991,"Lexus","ES 300"),
    (1995,"Lexus","GS 300"),(1994,"Lexus","GS 300"),(1993,"Lexus","GS 300"),
    (1995,"Lexus","LS 400"),(1994,"Lexus","LS 400"),(1993,"Lexus","LS 400"),
    (1992,"Lexus","LS 400"),(1991,"Lexus","LS 400"),(1990,"Lexus","LS 400"),
    (1995,"Lexus","SC 300"),(1994,"Lexus","SC 300"),(1993,"Lexus","SC 300"),
    (1992,"Lexus","SC 300"),
    (1995,"Infiniti","Q45"),(1994,"Infiniti","Q45"),(1993,"Infiniti","Q45"),
    (1992,"Infiniti","Q45"),(1991,"Infiniti","Q45"),(1990,"Infiniti","Q45"),
    (1995,"Infiniti","J30"),(1994,"Infiniti","J30"),(1993,"Infiniti","J30"),
    (1995,"Mercedes-Benz","C-Class"),(1994,"Mercedes-Benz","C-Class"),
    (1993,"Mercedes-Benz","C-Class"),
    (1995,"Mercedes-Benz","E-Class"),(1994,"Mercedes-Benz","E-Class"),
    (1993,"Mercedes-Benz","E-Class"),
    (1995,"Volkswagen","Jetta"),(1994,"Volkswagen","Jetta"),
    (1993,"Volkswagen","Jetta"),(1992,"Volkswagen","Jetta"),
    (1995,"Volkswagen","Golf"),(1994,"Volkswagen","Golf"),
    (1993,"Volkswagen","Golf"),(1992,"Volkswagen","Golf"),
    (1995,"Volkswagen","Passat"),(1994,"Volkswagen","Passat"),
    (1995,"Volkswagen","Cabrio"),(1994,"Volkswagen","Cabrio"),
    (1995,"Mazda","626"),(1994,"Mazda","626"),(1993,"Mazda","626"),
    (1992,"Mazda","626"),(1991,"Mazda","626"),(1990,"Mazda","626"),
    (1995,"Mazda","Miata"),(1994,"Mazda","Miata"),(1993,"Mazda","Miata"),
    (1992,"Mazda","Miata"),(1991,"Mazda","Miata"),(1990,"Mazda","Miata"),
    (1995,"Mazda","Protege"),(1994,"Mazda","Protege"),(1993,"Mazda","Protege"),
    (1995,"Mazda","MPV"),(1994,"Mazda","MPV"),
    (1995,"Pontiac","Firebird"),(1994,"Pontiac","Firebird"),
    (1993,"Pontiac","Firebird"),(1992,"Pontiac","Firebird"),
    (1995,"Pontiac","Grand Prix"),(1994,"Pontiac","Grand Prix"),
    (1993,"Pontiac","Grand Prix"),(1992,"Pontiac","Grand Prix"),
    (1995,"Pontiac","Grand Am"),(1994,"Pontiac","Grand Am"),
    (1993,"Pontiac","Grand Am"),(1992,"Pontiac","Grand Am"),
    (1995,"Buick","LeSabre"),(1994,"Buick","LeSabre"),
    (1993,"Buick","LeSabre"),(1992,"Buick","LeSabre"),
    (1995,"Buick","Riviera"),(1994,"Buick","Riviera"),
    (1995,"Buick","Regal"),(1994,"Buick","Regal"),(1993,"Buick","Regal"),
    (1995,"Oldsmobile","Cutlass Supreme"),(1994,"Oldsmobile","Cutlass Supreme"),
    (1993,"Oldsmobile","Cutlass Supreme"),
    (1995,"Oldsmobile","Aurora"),(1994,"Oldsmobile","Aurora"),
    (1995,"Oldsmobile","88"),(1994,"Oldsmobile","88"),(1993,"Oldsmobile","88"),
    (1995,"Cadillac","DeVille"),(1994,"Cadillac","DeVille"),
    (1993,"Cadillac","DeVille"),(1992,"Cadillac","DeVille"),
    (1995,"Cadillac","Seville"),(1994,"Cadillac","Seville"),
    (1993,"Cadillac","Seville"),(1992,"Cadillac","Seville"),
    (1995,"Lincoln","Town Car"),(1994,"Lincoln","Town Car"),
    (1993,"Lincoln","Town Car"),(1992,"Lincoln","Town Car"),
    (1995,"Lincoln","Continental"),(1994,"Lincoln","Continental"),
    (1995,"Mercury","Grand Marquis"),(1994,"Mercury","Grand Marquis"),
    (1993,"Mercury","Grand Marquis"),
    (1995,"Chrysler","LeBaron"),(1994,"Chrysler","LeBaron"),
    (1995,"Chrysler","Town & Country"),(1994,"Chrysler","Town & Country"),
    (1993,"Chrysler","Town & Country"),
    (1995,"Mitsubishi","Eclipse"),(1994,"Mitsubishi","Eclipse"),
    (1993,"Mitsubishi","Eclipse"),(1992,"Mitsubishi","Eclipse"),
    (1995,"Mitsubishi","Galant"),(1994,"Mitsubishi","Galant"),
    (1993,"Mitsubishi","Galant"),(1992,"Mitsubishi","Galant"),
    (1995,"Mitsubishi","3000GT"),(1994,"Mitsubishi","3000GT"),
    (1993,"Mitsubishi","3000GT"),(1992,"Mitsubishi","3000GT"),
    (1995,"Isuzu","Rodeo"),(1994,"Isuzu","Rodeo"),(1993,"Isuzu","Rodeo"),
    (1995,"Isuzu","Trooper"),(1994,"Isuzu","Trooper"),(1993,"Isuzu","Trooper"),
    (1995,"Suzuki","Sidekick"),(1994,"Suzuki","Sidekick"),
    (1993,"Suzuki","Sidekick"),(1992,"Suzuki","Sidekick"),
    (1995,"Land Rover","Range Rover"),(1994,"Land Rover","Range Rover"),
    (1993,"Land Rover","Range Rover"),(1992,"Land Rover","Range Rover"),
    (1995,"Land Rover","Discovery"),(1994,"Land Rover","Discovery"),
    (1993,"Land Rover","Discovery"),
    (1995,"Volvo","850"),(1994,"Volvo","850"),(1993,"Volvo","850"),
    (1995,"Volvo","940"),(1994,"Volvo","940"),(1993,"Volvo","940"),
    (1992,"Volvo","940"),(1991,"Volvo","940"),(1990,"Volvo","940"),
    (1995,"Saab","900"),(1994,"Saab","900"),(1993,"Saab","900"),
    (1992,"Saab","900"),(1991,"Saab","900"),(1990,"Saab","900"),
    (1995,"Saab","9000"),(1994,"Saab","9000"),(1993,"Saab","9000"),
    (1995,"Audi","A4"),(1995,"Audi","A6"),(1994,"Audi","A6"),
    (1993,"Audi","A6"),(1992,"Audi","A6"),
    (1995,"Porsche","911"),(1994,"Porsche","911"),(1993,"Porsche","911"),
    (1992,"Porsche","911"),(1991,"Porsche","911"),(1990,"Porsche","911"),
    (1995,"Porsche","968"),(1994,"Porsche","968"),
    (1995,"Hyundai","Elantra"),(1994,"Hyundai","Elantra"),
    (1993,"Hyundai","Elantra"),(1992,"Hyundai","Elantra"),
    (1995,"Hyundai","Sonata"),(1994,"Hyundai","Sonata"),
    (1993,"Hyundai","Sonata"),(1992,"Hyundai","Sonata"),
    (1995,"Hyundai","Accent"),(1994,"Hyundai","Accent"),
    (1995,"Kia","Sephia"),(1994,"Kia","Sephia"),
    # ── Missing makes not yet covered ──
    (2020,"MINI","Cooper S"),(2021,"MINI","Cooper S"),(2022,"MINI","Cooper S"),
    (2020,"MINI","Cooper SE"),(2021,"MINI","Cooper SE"),
    (2020,"MINI","Clubman"),(2021,"MINI","Clubman"),(2022,"MINI","Clubman"),
    (2018,"MINI","Countryman"),(2019,"MINI","Countryman"),
    (2020,"Fiat","500X"),(2021,"Fiat","500X"),(2022,"Fiat","500X"),
    (2020,"Fiat","500L"),(2021,"Fiat","500L"),
    (2019,"Fiat","124 Spider"),(2020,"Fiat","124 Spider"),
    (2018,"Fiat","500"),(2019,"Fiat","500"),(2020,"Fiat","500"),
    (2020,"Jaguar","F-Pace"),(2021,"Jaguar","F-Pace"),(2022,"Jaguar","F-Pace"),
    (2020,"Jaguar","XE"),(2021,"Jaguar","XE"),
    (2020,"Jaguar","XF"),(2021,"Jaguar","XF"),
    (2020,"Jaguar","E-Pace"),(2021,"Jaguar","E-Pace"),
    (2020,"Jaguar","I-Pace"),(2021,"Jaguar","I-Pace"),(2022,"Jaguar","I-Pace"),
    (2020,"McLaren","720S"),(2021,"McLaren","720S"),
    (2020,"McLaren","GT"),(2021,"McLaren","GT"),
    (2021,"McLaren","765LT"),
    (2020,"Rolls-Royce","Ghost"),(2021,"Rolls-Royce","Ghost"),
    (2020,"Rolls-Royce","Cullinan"),(2021,"Rolls-Royce","Cullinan"),
    (2020,"Aston Martin","Vantage"),(2021,"Aston Martin","Vantage"),
    (2020,"Aston Martin","DB11"),(2021,"Aston Martin","DB11"),
    (2020,"Aston Martin","DBX"),(2021,"Aston Martin","DBX"),
    (2022,"Aston Martin","DBX"),
    # ── More Lexus history ──
    (2005,"Lexus","RX 330"),(2004,"Lexus","RX 330"),(2003,"Lexus","RX 300"),
    (2005,"Lexus","ES 330"),(2004,"Lexus","ES 330"),(2003,"Lexus","ES 300"),
    (2005,"Lexus","IS 300"),(2004,"Lexus","IS 300"),(2003,"Lexus","IS 300"),
    (2006,"Lexus","IS 250"),(2007,"Lexus","IS 250"),(2008,"Lexus","IS 250"),
    (2005,"Lexus","GS 300"),(2004,"Lexus","GS 300"),(2003,"Lexus","GS 300"),
    (2000,"Lexus","LS 400"),(1999,"Lexus","LS 400"),(1998,"Lexus","LS 400"),
    # ── More Infiniti history ──
    (2005,"Infiniti","G35"),(2004,"Infiniti","G35"),(2003,"Infiniti","G35"),
    (2006,"Infiniti","G35"),(2007,"Infiniti","G35"),(2008,"Infiniti","G35"),
    (2005,"Infiniti","FX35"),(2004,"Infiniti","FX35"),(2003,"Infiniti","FX35"),
    (2005,"Infiniti","M45"),(2006,"Infiniti","M35"),
    # ── More Acura history ──
    (2005,"Acura","TSX"),(2004,"Acura","TSX"),(2006,"Acura","TSX"),
    (2007,"Acura","TSX"),(2008,"Acura","TSX"),
    (2005,"Acura","TL"),(2004,"Acura","TL"),(2006,"Acura","TL"),
    (2003,"Acura","TL"),(2002,"Acura","TL"),
    (2005,"Acura","MDX"),(2004,"Acura","MDX"),(2003,"Acura","MDX"),
    # ── More Cadillac history ──
    (2005,"Cadillac","CTS"),(2004,"Cadillac","CTS"),(2003,"Cadillac","CTS"),
    (2006,"Cadillac","CTS"),(2007,"Cadillac","CTS"),(2008,"Cadillac","CTS"),
    (2005,"Cadillac","STS"),(2006,"Cadillac","STS"),(2007,"Cadillac","STS"),
    (2005,"Cadillac","SRX"),(2006,"Cadillac","SRX"),(2007,"Cadillac","SRX"),
    (2005,"Cadillac","Escalade"),(2004,"Cadillac","Escalade"),
    (2003,"Cadillac","Escalade"),
    # ── Lincoln history ──
    (2005,"Lincoln","Town Car"),(2004,"Lincoln","Town Car"),
    (2003,"Lincoln","Town Car"),(2006,"Lincoln","Town Car"),
    (2005,"Lincoln","Navigator"),(2004,"Lincoln","Navigator"),
    (2003,"Lincoln","Navigator"),
    (2005,"Lincoln","LS"),(2004,"Lincoln","LS"),(2003,"Lincoln","LS"),
    # ── More Dodge/Chrysler ──
    (2005,"Dodge","Magnum"),(2006,"Dodge","Magnum"),(2007,"Dodge","Magnum"),
    (2005,"Dodge","Charger"),(2006,"Dodge","Charger"),(2007,"Dodge","Charger"),
    (2008,"Dodge","Charger"),(2009,"Dodge","Charger"),(2010,"Dodge","Charger"),
    (2005,"Chrysler","300"),(2006,"Chrysler","300"),(2007,"Chrysler","300"),
    (2008,"Chrysler","300"),(2009,"Chrysler","300"),(2010,"Chrysler","300"),
    # ── More performance/enthusiast cars ──
    (2005,"Ford","Mustang GT"),(2006,"Ford","Mustang GT"),
    (2007,"Ford","Mustang GT"),(2008,"Ford","Mustang GT"),
    (2007,"Ford","Mustang Shelby GT500"),
    (2008,"Ford","Mustang Shelby GT500"),
    (2005,"Chevrolet","Corvette"),(2006,"Chevrolet","Corvette"),
    (2007,"Chevrolet","Corvette"),(2008,"Chevrolet","Corvette"),
    (2009,"Chevrolet","Corvette"),(2010,"Chevrolet","Corvette"),
    (2005,"Chevrolet","Camaro"),(2010,"Chevrolet","Camaro"),
    (2011,"Chevrolet","Camaro"),(2012,"Chevrolet","Camaro"),
    (2013,"Chevrolet","Camaro"),(2014,"Chevrolet","Camaro"),
    (2005,"Pontiac","GTO"),(2006,"Pontiac","GTO"),
    (2004,"Pontiac","GTO"),
    (2003,"Dodge","Viper"),(2004,"Dodge","Viper"),(2005,"Dodge","Viper"),
    (2006,"Dodge","Viper"),(2007,"Dodge","Viper"),(2008,"Dodge","Viper"),
    (2005,"Ford","GT"),(2006,"Ford","GT"),
    (2017,"Ford","GT"),(2018,"Ford","GT"),
    # ── More Volkswagen ──
    (2005,"Volkswagen","Jetta"),(2006,"Volkswagen","Jetta"),
    (2007,"Volkswagen","Jetta"),(2008,"Volkswagen","Jetta"),
    (2005,"Volkswagen","GTI"),(2006,"Volkswagen","GTI"),
    (2007,"Volkswagen","GTI"),(2008,"Volkswagen","GTI"),
    (2010,"Volkswagen","GTI"),(2012,"Volkswagen","GTI"),
    (2015,"Volkswagen","GTI"),(2017,"Volkswagen","GTI"),
    (2005,"Volkswagen","Golf"),(2006,"Volkswagen","Golf"),
    (2010,"Volkswagen","Golf"),(2012,"Volkswagen","Golf"),
    (2005,"Volkswagen","Passat"),(2006,"Volkswagen","Passat"),
    (2007,"Volkswagen","Passat"),(2008,"Volkswagen","Passat"),
    (2005,"Volkswagen","Touareg"),(2006,"Volkswagen","Touareg"),
    (2007,"Volkswagen","Touareg"),(2008,"Volkswagen","Touareg"),
    (2010,"Volkswagen","Touareg"),(2012,"Volkswagen","Touareg"),
    # ── More Subaru history ──
    (2005,"Subaru","WRX"),(2004,"Subaru","WRX"),(2003,"Subaru","WRX"),
    (2006,"Subaru","WRX"),(2007,"Subaru","WRX"),(2008,"Subaru","WRX"),
    (2005,"Subaru","WRX STI"),(2006,"Subaru","WRX STI"),
    (2007,"Subaru","WRX STI"),(2008,"Subaru","WRX STI"),
    (2005,"Subaru","Outback"),(2004,"Subaru","Outback"),(2003,"Subaru","Outback"),
    (2005,"Subaru","Forester"),(2004,"Subaru","Forester"),
    (2003,"Subaru","Forester"),
    # ── More BMW ──
    (2005,"BMW","M3"),(2006,"BMW","M3"),(2007,"BMW","M3"),(2008,"BMW","M3"),
    (2005,"BMW","M5"),(2006,"BMW","M5"),(2007,"BMW","M5"),(2008,"BMW","M5"),
    (2010,"BMW","M3"),(2011,"BMW","M3"),(2012,"BMW","M3"),
    (2005,"BMW","330i"),(2004,"BMW","330i"),(2003,"BMW","330i"),
    (2005,"BMW","X3"),(2004,"BMW","X3"),(2003,"BMW","X3"),
    (2005,"BMW","X5"),(2004,"BMW","X5"),(2003,"BMW","X5"),
    # ── More Mercedes ──
    (2005,"Mercedes-Benz","C-Class"),(2004,"Mercedes-Benz","C-Class"),
    (2003,"Mercedes-Benz","C-Class"),
    (2005,"Mercedes-Benz","E-Class"),(2004,"Mercedes-Benz","E-Class"),
    (2003,"Mercedes-Benz","E-Class"),
    (2005,"Mercedes-Benz","SL-Class"),(2004,"Mercedes-Benz","SL-Class"),
    (2003,"Mercedes-Benz","SL-Class"),
    (2005,"Mercedes-Benz","ML 350"),(2004,"Mercedes-Benz","ML 350"),
    (2003,"Mercedes-Benz","ML 350"),
    (2006,"Mercedes-Benz","C-Class"),(2007,"Mercedes-Benz","C-Class"),
    (2008,"Mercedes-Benz","C-Class"),
    # ── More Audi ──
    (2005,"Audi","A4"),(2004,"Audi","A4"),(2003,"Audi","A4"),
    (2006,"Audi","A4"),(2007,"Audi","A4"),(2008,"Audi","A4"),
    (2005,"Audi","A6"),(2004,"Audi","A6"),(2003,"Audi","A6"),
    (2005,"Audi","TT"),(2006,"Audi","TT"),(2007,"Audi","TT"),(2008,"Audi","TT"),
    (2000,"Audi","TT"),(2001,"Audi","TT"),(2002,"Audi","TT"),
    (2005,"Audi","S4"),(2004,"Audi","S4"),(2003,"Audi","S4"),
    (2006,"Audi","S4"),(2007,"Audi","S4"),(2008,"Audi","S4"),
    # ── More Porsche ──
    (2005,"Porsche","911"),(2004,"Porsche","911"),(2003,"Porsche","911"),
    (2006,"Porsche","911"),(2007,"Porsche","911"),(2008,"Porsche","911"),
    (2005,"Porsche","Boxster"),(2004,"Porsche","Boxster"),
    (2003,"Porsche","Boxster"),(2006,"Porsche","Boxster"),
    (2007,"Porsche","Boxster"),(2008,"Porsche","Boxster"),
    (2005,"Porsche","Cayenne"),(2004,"Porsche","Cayenne"),
    (2003,"Porsche","Cayenne"),(2006,"Porsche","Cayenne"),
    (2007,"Porsche","Cayenne"),(2008,"Porsche","Cayenne"),
    # ── Honda/Toyota mid-2000s gaps ──
    (2005,"Honda","S2000"),(2004,"Honda","S2000"),(2003,"Honda","S2000"),
    (2006,"Honda","S2000"),(2007,"Honda","S2000"),(2008,"Honda","S2000"),
    (2000,"Honda","S2000"),(2001,"Honda","S2000"),(2002,"Honda","S2000"),
    (2005,"Toyota","MR2 Spyder"),(2004,"Toyota","MR2 Spyder"),
    (2003,"Toyota","MR2 Spyder"),
    (2005,"Toyota","Matrix"),(2004,"Toyota","Matrix"),(2003,"Toyota","Matrix"),
    (2006,"Toyota","Matrix"),(2007,"Toyota","Matrix"),(2008,"Toyota","Matrix"),
    (2005,"Toyota","FJ Cruiser"),(2006,"Toyota","FJ Cruiser"),
    (2007,"Toyota","FJ Cruiser"),(2008,"Toyota","FJ Cruiser"),
    (2009,"Toyota","FJ Cruiser"),(2010,"Toyota","FJ Cruiser"),
    # ── Scion more models ──
    (2005,"Scion","tC"),(2006,"Scion","tC"),(2007,"Scion","tC"),
    (2008,"Scion","tC"),(2009,"Scion","tC"),
    (2005,"Scion","xA"),(2006,"Scion","xA"),
    (2004,"Scion","xA"),
]

ENDPOINTS = ["oil-change","parts","maintenance","fluids","torque-specs",
             "recalls","engine-specs","fuel-economy","safety-ratings",
             "warranty","reliability","tsb","service-costs"]

session = requests.Session()
session.headers.update({"X-API-Key": API_KEY})
req_count = 0

def api_get(path, params=None):
    global req_count
    try:
        r = session.get(f"{BASE_URL}/{path}", params=params, timeout=15)
        req_count += 1
        time.sleep(DELAY)
        if r.status_code == 200: return r.json().get("data")
        if r.status_code == 429:
            log.warning("Rate limited - sleeping 15s")
            time.sleep(15)
            return api_get(path, params)
        return None
    except Exception as e:
        log.error(f"Request error: {e}")
        return None

def setup_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY, year INTEGER, make TEXT, model TEXT, engine TEXT, trim TEXT, pulled_at TEXT);
        CREATE TABLE IF NOT EXISTS oil_change (vehicle_id INTEGER PRIMARY KEY, viscosity TEXT, oil_type TEXT, capacity_with_filter REAL, capacity_without_filter REAL, oem_spec TEXT, filters_json TEXT, drain_bolt_json TEXT);
        CREATE TABLE IF NOT EXISTS parts (vehicle_id INTEGER PRIMARY KEY, spark_plug_type TEXT, spark_plug_gap TEXT, spark_plug_qty INTEGER, battery_group TEXT, battery_cca INTEGER, tire_size TEXT, tire_pressure_front INTEGER, tire_pressure_rear INTEGER, spark_plugs_json TEXT, air_filters_json TEXT, cabin_filters_json TEXT, wiper_blades_json TEXT, batteries_json TEXT);
        CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY, vehicle_id INTEGER, mileage_interval INTEGER, months_interval INTEGER, description TEXT, source TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS maintenance_parts (id INTEGER PRIMARY KEY AUTOINCREMENT, maintenance_id INTEGER, vehicle_id INTEGER, part_type TEXT, brand TEXT, part_number TEXT, description TEXT, qty INTEGER);
        CREATE TABLE IF NOT EXISTS fluids (vehicle_id INTEGER PRIMARY KEY, transmission_fluid TEXT, transmission_capacity REAL, brake_fluid TEXT, coolant_type TEXT, coolant_capacity REAL, power_steering_fluid TEXT, differential_fluids_json TEXT);
        CREATE TABLE IF NOT EXISTS torque_specs (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, component TEXT, torque_ft_lbs REAL, torque_nm REAL, notes TEXT);
        CREATE TABLE IF NOT EXISTS recalls (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, campaign_number TEXT, component TEXT, summary TEXT, remedy TEXT, park_it INTEGER);
        CREATE TABLE IF NOT EXISTS engine_specs (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, variant TEXT, horsepower INTEGER, torque_ft_lbs INTEGER, displacement_l REAL, cylinders INTEGER, cylinder_config TEXT, aspiration TEXT, fuel_system TEXT);
        CREATE TABLE IF NOT EXISTS fuel_economy (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, city_mpg INTEGER, highway_mpg INTEGER, combined_mpg INTEGER, annual_fuel_cost INTEGER, engine TEXT, transmission TEXT, drive TEXT);
        CREATE TABLE IF NOT EXISTS safety_ratings (vehicle_id INTEGER PRIMARY KEY, overall_rating INTEGER, frontal_crash_driver INTEGER, frontal_crash_passenger INTEGER, side_crash_driver INTEGER, side_crash_passenger INTEGER, rollover_rating INTEGER, rollover_risk_pct REAL, side_pole_rating INTEGER);
        CREATE TABLE IF NOT EXISTS warranty (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, warranty_type TEXT, months INTEGER, miles INTEGER, notes TEXT);
        CREATE TABLE IF NOT EXISTS reliability (vehicle_id INTEGER PRIMARY KEY, overall_score REAL, rating TEXT, complaint_count INTEGER, crash_count INTEGER, fire_count INTEGER, injury_count INTEGER, top_issue TEXT);
        CREATE TABLE IF NOT EXISTS service_costs (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, service_type TEXT, region TEXT, cost_low INTEGER, cost_high INTEGER, cost_average INTEGER, labor_hours_low REAL, labor_hours_high REAL);
        CREATE TABLE IF NOT EXISTS tsb (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, tsb_number TEXT, title TEXT, component TEXT, summary TEXT, date TEXT);
        CREATE TABLE IF NOT EXISTS dtc_codes (code TEXT PRIMARY KEY, description TEXT, urgency TEXT, cost_low INTEGER, cost_high INTEGER, possible_causes TEXT, systems TEXT);
        CREATE TABLE IF NOT EXISTS pull_log (vehicle_id INTEGER, endpoint TEXT, status TEXT, pulled_at TEXT, PRIMARY KEY (vehicle_id, endpoint));
    """)
    conn.commit()

def save_all(conn, vid, ep, data):
    try:
        if ep == "oil-change" and data:
            s = data.get("oil_spec") or {}
            conn.execute("INSERT OR REPLACE INTO oil_change VALUES (?,?,?,?,?,?,?,?)",
                (vid, s.get("viscosity"), s.get("oil_type"), s.get("capacity_with_filter"),
                 s.get("capacity_without_filter"), s.get("oem_spec"),
                 json.dumps(data.get("filters")), json.dumps(data.get("drain_bolt"))))
        elif ep == "parts" and data:
            sp=data.get("spark_plug_spec") or {}; bat=data.get("battery_spec") or {}; ti=data.get("tire_spec") or {}
            conn.execute("INSERT OR REPLACE INTO parts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (vid,sp.get("plug_type"),sp.get("gap"),sp.get("quantity"),
                 bat.get("group_size"),bat.get("cca"),ti.get("size"),
                 ti.get("pressure_front_psi"),ti.get("pressure_rear_psi"),
                 json.dumps(data.get("spark_plugs")),json.dumps(data.get("air_filters")),
                 json.dumps(data.get("cabin_filters")),json.dumps(data.get("wiper_blades")),
                 json.dumps(data.get("batteries"))))
        elif ep == "maintenance" and data:
            for item in (data.get("schedules",[]) if isinstance(data,dict) else []):
                sid=item.get("id")
                conn.execute("INSERT OR REPLACE INTO maintenance VALUES (?,?,?,?,?,?,?)",
                    (sid,vid,item.get("mileage_interval"),item.get("months_interval"),
                     item.get("description"),item.get("source"),item.get("notes")))
                for part in (item.get("parts") or []):
                    conn.execute("INSERT OR IGNORE INTO maintenance_parts (maintenance_id,vehicle_id,part_type,brand,part_number,description,qty) VALUES (?,?,?,?,?,?,?)",
                        (sid,vid,part.get("part_type"),part.get("brand"),part.get("part_number"),part.get("description"),part.get("qty")))
        elif ep == "fluids" and data:
            tf=data.get("transmission_fluid") or {}; c=data.get("coolant") or {}
            conn.execute("INSERT OR REPLACE INTO fluids VALUES (?,?,?,?,?,?,?,?)",
                (vid,tf.get("fluid_type"),tf.get("capacity_quarts"),
                 (data.get("brake_fluid") or {}).get("dot_type"),
                 c.get("coolant_type"),c.get("capacity_quarts"),
                 (data.get("power_steering_fluid") or {}).get("fluid_type"),
                 json.dumps(data.get("differential_fluids"))))
        elif ep == "torque-specs" and data:
            for t in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes) VALUES (?,?,?,?,?)",
                    (vid,t.get("component"),t.get("torque_ft_lbs"),t.get("torque_nm"),t.get("notes")))
        elif ep == "recalls" and data:
            for r in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO recalls (vehicle_id,campaign_number,component,summary,remedy,park_it) VALUES (?,?,?,?,?,?)",
                    (vid,r.get("campaign_number") or r.get("nhtsa_campaign_number"),
                     r.get("component"),r.get("summary"),r.get("remedy"),1 if r.get("park_it") else 0))
        elif ep == "engine-specs" and data:
            for e in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO engine_specs (vehicle_id,variant,horsepower,torque_ft_lbs,displacement_l,cylinders,cylinder_config,aspiration,fuel_system) VALUES (?,?,?,?,?,?,?,?,?)",
                    (vid,e.get("engine_variant"),e.get("horsepower"),e.get("torque_ft_lbs"),
                     e.get("displacement_liters"),e.get("cylinders"),e.get("cylinder_config"),
                     e.get("aspiration"),e.get("fuel_system")))
        elif ep == "fuel-economy" and data:
            for f in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO fuel_economy (vehicle_id,city_mpg,highway_mpg,combined_mpg,annual_fuel_cost,engine,transmission,drive) VALUES (?,?,?,?,?,?,?,?)",
                    (vid,f.get("city_mpg"),f.get("highway_mpg"),f.get("combined_mpg"),
                     f.get("annual_fuel_cost"),f.get("engine_displacement"),
                     f.get("transmission"),f.get("drive")))
        elif ep == "safety-ratings" and data:
            conn.execute("INSERT OR REPLACE INTO safety_ratings VALUES (?,?,?,?,?,?,?,?,?)",
                (vid,data.get("overall_rating"),data.get("frontal_crash_driver"),
                 data.get("frontal_crash_passenger"),data.get("side_crash_driver"),
                 data.get("side_crash_passenger"),data.get("rollover_rating"),
                 data.get("rollover_risk_pct"),data.get("side_pole_rating")))
        elif ep == "warranty" and data:
            for w in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO warranty (vehicle_id,warranty_type,months,miles,notes) VALUES (?,?,?,?,?)",
                    (vid,w.get("warranty_type"),w.get("months"),w.get("miles"),w.get("notes")))
        elif ep == "reliability" and data:
            conn.execute("INSERT OR REPLACE INTO reliability VALUES (?,?,?,?,?,?,?,?)",
                (vid,data.get("overall_score"),data.get("rating"),data.get("complaint_count"),
                 data.get("crash_count"),data.get("fire_count"),data.get("injury_count"),data.get("top_issue")))
        elif ep == "service-costs" and data:
            for s in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO service_costs (vehicle_id,service_type,region,cost_low,cost_high,cost_average,labor_hours_low,labor_hours_high) VALUES (?,?,?,?,?,?,?,?)",
                    (vid,s.get("service_type"),s.get("region"),s.get("cost_low"),
                     s.get("cost_high"),s.get("cost_average"),s.get("labor_hours_low"),s.get("labor_hours_high")))
        elif ep == "tsb" and data:
            for t in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO tsb (vehicle_id,tsb_number,title,component,summary,date) VALUES (?,?,?,?,?,?)",
                    (vid,t.get("tsb_number") or t.get("number"),t.get("title"),
                     t.get("component"),t.get("summary"),t.get("date") or t.get("issued_date")))
        conn.commit()
    except Exception as e:
        log.error(f"  Save error [{ep}]: {e}")

def pull_vehicle(conn, year, make, model):
    existing = conn.execute("SELECT id FROM vehicles WHERE year=? AND make=? AND model=?", (year,make,model)).fetchone()
    if existing:
        vid=existing[0]
        done=conn.execute("SELECT COUNT(*) FROM pull_log WHERE vehicle_id=? AND status='ok'",(vid,)).fetchone()[0]
        if done >= len(ENDPOINTS)-2:
            log.info(f"  SKIP"); return vid
    result = api_get("vehicles", {"year":year,"make":make,"model":model})
    if not result: log.warning(f"  No results"); return None
    vehicles = result if isinstance(result,list) else [result]
    v = next((x for x in vehicles if x.get("engine")), vehicles[0])
    vid = v["id"]
    conn.execute("INSERT OR IGNORE INTO vehicles VALUES (?,?,?,?,?,?,?)",
        (vid,year,make,model,v.get("engine"),v.get("trim"),datetime.now().isoformat()))
    conn.commit()
    log.info(f"  -> ID {vid} | {v.get('engine','?')}")
    for ep in ENDPOINTS:
        done=conn.execute("SELECT status FROM pull_log WHERE vehicle_id=? AND endpoint=?",(vid,ep)).fetchone()
        if done and done[0]=="ok": continue
        data=api_get(f"vehicles/{vid}/{ep}")
        if data: save_all(conn,vid,ep,data)
        conn.execute("INSERT OR REPLACE INTO pull_log VALUES (?,?,?,?)",
            (vid,ep,"ok" if data else "empty",datetime.now().isoformat()))
        conn.commit()
    return vid

def main():
    log.info(f"Wrench FINAL BATCH - {len(TARGET)} targets")
    conn = sqlite3.connect(DB_FILE)
    setup_db(conn)
    ok = 0
    for i,(yr,mk,mdl) in enumerate(TARGET,1):
        log.info(f"[{i}/{len(TARGET)}] {yr} {mk} {mdl}")
        try:
            if pull_vehicle(conn,yr,mk,mdl): ok+=1
        except Exception as e:
            log.error(f"  Error: {e}")
        if i%25==0:
            total=conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
            log.info(f"--- {ok}/{i} ok | {req_count} reqs | {total} total ---")
    total=conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    log.info(f"DONE! Added {ok}. Total: {total}. Requests: {req_count}")
    conn.close()

if __name__=="__main__":
    main()
