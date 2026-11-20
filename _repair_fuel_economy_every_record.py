"""Fuel-economy repair, part 8: rows that lack some of their own EPA records.

Found by the full comparison against EPA's complete file (2026-11-15; re-run on the current database 2026-11-19 with
the same result): 260 rows lack at least one record that EPA lists under the vehicle's own names, and on 162 of them a
whole engine is absent. 256 of the 260 were filled by the May 2026 pull, which came through a third-party vehicle API
and often returned one engine per row. The rows pulled from EPA directly (June and November 2026) hold every own
record, as do 1,526 rows in all.

Ruling (Robert, 2026-11-19, "Yes, every record" to "Should rows show every own EPA record?"): a row shows every
record EPA lists under the vehicle's own names, every engine, transmission and drive, one line per distinct record
(the rule of part 1: city, highway, combined, engine size, transmission and drive).

ADDED: 873 records on 224 rows (77 of them verified, 468 records on those), of EPA fuel type gasoline (730),
flex-fuel (80; gasoline figures only, as on every flex-fuel line since part 2) and diesel (63). Where EPA lists two
records with the same six fields, the first in its file is taken (30 such lines pair a plain and a flex-fuel record).
NOT ADDED (HELD), each a kind that is not ruled; the rules are in HOLD below:
    58 hybrid or plug-in records sold under a plain own name (38 rows): hybrid versions (item c). On 18 of those rows
       the nameplate is a hybrid itself (Prius and similar).
    60 chassis-cab records of the Silverado 1500 / Sierra 1500 (20 rows, all verified).
    28 records under performance-leaning names (21 rows): BMW M35i / M40i / M50i, Mustang Bullitt / HO /
       Performance Package / Dark Horse SC, Camry TRD, Tacoma TRD, RAM 1500 HO, 911 Turbo S.
    21 four-door Wrangler records (6 rows): the longer body, like the Wrangler Unlimited lines held since 2026-11-15.
    6 SRT-8 records (the 6.1L) that EPA files under its shared "300/SRT-8" and "300C/SRT-8" names (6 rows).
    2 own records whose stored line holds figures EPA has since revised: revised figures are item (e).
    Nothing of a performance version, a longer or different body, another vehicle or a special-purpose version.
KEPT: every stored line stays (nothing is removed), including lines of the held kinds already stored. On the same
224 rows every stored line that equals an own record takes EPA's current yearly fuel cost, so a row's own lines share
one price year (653 lines; 2 lines whose record carries two different costs are left alone). Lines of unruled kinds
keep their stored cost until their ruling: 64 lines on 41 rows (13 verified), which therefore still show two price
years. New lines go after the stored ones, so the first line a row shows (the search card's figure) does not change.
The pull log is not touched, so the origin of each row's older lines stays traceable.

Own names follow the full comparison's rules unchanged: the nameplate with a plain drive, body or trim word, and
fourteen spellings EPA uses instead of the nameplate (Silverado C15 / K15, Cooper S Countryman, 3.2TL and similar).
Each operation below lists the names taken for its row; every added record must carry one of them.

Source: EPA fueleconomy.gov complete file vehicles.csv.zip (U.S. government), last modified by EPA on 2026-11-04,
SHA-256 pinned below. All 3,647 records pulled one by one from EPA's web service on 2026-11-15 equal this file in every
compared field. The file is untrusted data: its path is an argument, it is read into memory, it must hold exactly one
member, and that member is only parsed as CSV.

    python -I _repair_fuel_economy_every_record.py <path to vehicles.csv.zip>
        DRY RUN. Checks the file's hash, plans every row, prints every line added and every cost changed, rehearses
        the real build on in-memory copies of the database (before and after), saves the plan and prints its sha256.
        Writes nothing to wrench_vehicles.db.

    python -I _repair_fuel_economy_every_record.py --write --sha <sha256 printed by the dry run>
        Backs up the database, then applies EXACTLY the saved plan. Each vehicle is changed only if its stored
        lines still equal what the dry run showed.
"""
import sqlite3, shutil, datetime, sys, os, io, re, csv, json, zipfile, hashlib, importlib.util, contextlib, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
PLAN_FILE = os.path.join(ROOT, "_repair_fuel_economy_every_record_plan_cache.json")      # gitignored (*_cache.json)
ZIP_SHA256 = "1d553896a77898f6cf47128281337af268df053c90dc1365891c7c8abff82c82"
ZIP_MAX = 50 * 1024 * 1024
CSV_MAX = 200 * 1024 * 1024
WRITE = "--write" in sys.argv
BARE_FROZEN = 424
TAKE_ATV = ("", "FFV", "Diesel")            # EPA atvType: plain gasoline, flex-fuel, diesel
NOT_GAS = ("EV", "FCV")                     # electric records are never fuel-economy gasoline lines
HOLD = [   # (make, model or None, EPA name as a full regular-expression match, engine size or None, group): not ruled, not added
    ("Chrysler", "300", r"300C?/SRT-8", 6.1, "SRT-8 under the shared 300 / SRT-8 name"),
    ("Jeep", "Wrangler", r"Wrangler .*4dr.*", None, "four-door Wrangler"),
    ("Chevrolet", "Silverado 1500", r".*Cab Chassis.*", None, "chassis cab"),
    ("GMC", "Sierra 1500", r".*Cab Chassis.*", None, "chassis cab"),
    ("BMW", None, r".* M\d\di( .*)?", None, "performance-leaning name"),
    ("Ford", "Mustang", r"Mustang (Bullitt|HO .*|Performance Package|Dark Horse SC)( .*)?", None, "performance-leaning name"),
    ("Toyota", "Camry", r"Camry TRD.*", None, "performance-leaning name"),
    ("Toyota", "Tacoma", r".*TRD.*", None, "performance-leaning name"),
    ("RAM", "1500", r"1500 HO .*", None, "performance-leaning name"),
    ("Porsche", "911", r"911 Turbo S.*", None, "performance-leaning name"),
]
COLS = ("city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, transmission, drive, range_miles, mpge, "
        "fuel_type, range_ev, city_ev, hwy_ev, comb_ev")
CITY, HWY, COMB, COST, ENG, TRANS, DRIVE, RANGE, MPGE, FTYPE = range(10)


def R(vid, year, make, model, taken, add, cost):
    """taken = EPA names that are this vehicle's own; add = EPA record ids to add; cost = stored lines whose cost changes."""
    return dict(id=vid, year=year, make=make, model=model, taken=taken, add=add, cost=cost)


OPS = [
    R(164, 2020, "MINI", "Countryman", ["Cooper Countryman", "Cooper Countryman All4", "Cooper S Countryman", "Cooper S Countryman All4", "Cooper SE Countryman All4", "JCW Countryman All4"], [41736, 41737, 41739, 41810], 1),
    R(942, 2020, "Audi", "A4", ["A4", "A4 quattro"], [42360], 1),
    R(946, 2020, "Audi", "A3", ["A3", "A3 Cabriolet quattro", "A3 quattro"], [41984], 1),
    R(1663, 2021, "MINI", "Countryman", ["Cooper Countryman", "Cooper Countryman All4", "Cooper S Countryman", "Cooper S Countryman All4", "Cooper SE Countryman All4", "JCW Countryman All4"], [42823, 42824, 42826, 42827], 1),
    R(1717, 2021, "Ford", "Bronco", ["Bronco 4WD", "Bronco Badlands 4WD", "Bronco Black Diamond 4WD", "Bronco Sasquatch 4WD"], [43995, 43996, 43997], 7),
    R(1968, 2021, "Nissan", "Rogue", ["Rogue AWD", "Rogue AWD  SV/SL/Platinum", "Rogue AWD SL/Platinum", "Rogue FWD", "Rogue FWD  SV/SL/Platinum", "Rogue FWD SL/Platinum"], [43370, 43375, 43770, 43772], 4),
    R(3031, 2022, "Toyota", "Corolla", ["Corolla", "Corolla APEX", "Corolla Hatchback", "Corolla Hatchback XSE", "Corolla XLE", "Corolla XSE"], [44238], 9),
    R(3053, 2022, "Toyota", "Corolla Cross", ["Corolla Cross", "Corolla Cross 4WD"], [44593], 1),
    R(3111, 2022, "BMW", "530i", ["530i Sedan", "530i xDrive Sedan"], [44292], 1),
    R(3112, 2022, "BMW", "330i", ["330i Sedan", "330i xDrive Sedan"], [44182], 1),
    R(3167, 2022, "MINI", "Countryman", ["Cooper Countryman", "Cooper Countryman All4", "Cooper S Countryman", "Cooper S Countryman All4", "Cooper SE Countryman All4", "JCW Countryman All4"], [43796, 43797, 43837, 43838], 1),
    R(3194, 2022, "Ford", "Expedition", ["Expedition 2WD", "Expedition 4WD", "Expedition Timberline AWD"], [45149, 45150, 45152, 45153], 2),
    R(3221, 2022, "Ford", "Bronco", ["Bronco 4WD", "Bronco Badlands 4WD", "Bronco Black Diamond 4WD", "Bronco Sasquatch 4WD"], [44993, 44995, 44998], 8),
    R(3494, 2022, "Nissan", "Rogue", ["Rogue AWD", "Rogue AWD SL/Platinum", "Rogue FWD", "Rogue FWD SL/Platinum"], [44942, 44947], 2),
    R(4593, 2023, "Toyota", "Corolla Cross", ["Corolla Cross", "Corolla Cross 4WD"], [46296], 1),
    R(4653, 2023, "BMW", "330i", ["330i Sedan", "330i xDrive Sedan"], [46130], 1),
    R(4660, 2023, "BMW", "M4", ["M4 CSL Coupe", "M4 Competition Coupe", "M4 Competition M xDrive Convertible", "M4 Competition M xDrive Coupe", "M4 Coupe"], [45485], 4),
    R(4762, 2023, "Ford", "Bronco", ["Bronco 4WD", "Bronco Badlands 4WD", "Bronco Black Diamond 4WD", "Bronco Sasquatch 4WD"], [46189, 46190, 46191], 9),
    R(5100, 2023, "Volkswagen", "Atlas Cross Sport", ["Atlas Cross Sport", "Atlas Cross Sport 4motion"], [45701, 45702], 2),
    R(6217, 2024, "BMW", "M3", ["M3 CS Sedan", "M3 Competition M xDrive Sedan", "M3 Competition Sedan", "M3 Sedan"], [46658], 3),
    R(6232, 2024, "BMW", "330i", ["330i Sedan", "330i xDrive Sedan"], [46657], 1),
    R(6239, 2024, "BMW", "M4", ["M4 Competition Coupe", "M4 Competition M xDrive Convertible", "M4 Competition M xDrive Coupe", "M4 Coupe"], [46470], 3),
    R(6325, 2024, "Ford", "Expedition", ["Expedition 2WD", "Expedition 4WD", "Expedition Timberline AWD"], [47167, 47180], 1),
    R(6434, 2024, "Cadillac", "Escalade", ["Escalade 2WD", "Escalade 4WD"], [47394, 47395, 47415, 47416], 0),
    R(6460, 2024, "GMC", "Canyon", ["Canyon 2WD", "Canyon 4WD", "Canyon AT4X 4WD", "Canyon AT4X AEV 4WD", "Canyon Mud Terrain Tires 4WD"], [47596], 4),
    R(7734, 2025, "Toyota", "Corolla", ["Corolla", "Corolla FX", "Corolla Hatchback", "Corolla Hatchback XSE"], [47996], 5),
    R(7934, 2025, "Ford", "Bronco", ["Bronco 4WD", "Bronco Badlands 4WD", "Bronco Outer Banks 4WD", "Bronco Sasquatch 4WD"], [49053, 49054, 49055], 5),
    R(8019, 2025, "Cadillac", "Escalade", ["Escalade 2WD", "Escalade 4WD"], [48620, 48629], 0),
    R(9373, 2026, "Toyota", "Corolla", ["Corolla", "Corolla (1-mode TM)", "Corolla (3-mode TM)", "Corolla Hatchback", "Corolla Hatchback FX", "Corolla Hatchback XSE"], [49810], 5),
    R(9395, 2026, "Toyota", "Corolla Cross", ["Corolla Cross", "Corolla Cross AWD"], [49869], 1),
    R(9445, 2026, "BMW", "M3", ["M3 Competition M xDrive Sedan", "M3 Competition Sedan", "M3 Sedan"], [49237], 2),
    R(9463, 2026, "BMW", "M4", ["M4 Competition Coupe", "M4 Competition M xDrive Convertible", "M4 Competition M xDrive Coupe", "M4 Coupe"], [49209], 3),
    R(9568, 2026, "Ford", "Bronco", ["Bronco 4WD", "Bronco Badlands 4WD", "Bronco Outer Banks 4WD", "Bronco Sasquatch 4WD"], [50121, 50124], 5),
    R(9653, 2026, "Cadillac", "Escalade", ["Escalade 2WD", "Escalade 4WD"], [49899, 50138], 0),
    R(9684, 2026, "GMC", "Canyon", ["Canyon 2WD", "Canyon 4WD", "Canyon AT4X 4WD", "Canyon AT4X AEV 4WD", "Canyon Mud Terrain Tires 4WD"], [50284], 4),
    R(9781, 2026, "Chrysler", "Pacifica", ["Pacifica", "Pacifica AWD"], [51095], 1),
    R(9856, 2026, "Volkswagen", "Atlas Cross Sport", ["Atlas Cross Sport", "Atlas Cross Sport 4motion"], [49541], 1),
    R(9974, 2026, "Hyundai", "Elantra", ["Elantra", "Elantra non-ISG", "Elantra w/Stop-Start"], [49813], 2),
    R(9976, 2026, "Hyundai", "Kona", ["Kona AWD", "Kona AWD SX2 1.6T 8AT AWD", "Kona AWD w/Stop-Start", "Kona FWD", "Kona FWD SX2 1.6T 8AT FWD", "Kona FWD w/Stop-Start"], [49449, 49492], 4),
    R(11000, 2002, "Audi", "A4", ["A4", "A4 Avant quattro", "A4 quattro"], [17493, 17494, 17495, 17496], 3),
    R(11033, 2003, "Audi", "A4", ["A4", "A4 Avant quattro", "A4 Cabriolet", "A4 quattro"], [18463, 18464, 18465, 18466], 5),
    R(11063, 2003, "Subaru", "Impreza", ["Impreza AWD", "Impreza Wagon/Outback SPT AWD"], [18783], 4),
    R(11076, 2004, "Audi", "A4", ["A4", "A4 Avant quattro", "A4 Cabriolet", "A4 Cabriolet quattro", "A4 quattro"], [19450, 19532, 19533, 19534, 19870], 5),
    R(11087, 2004, "Ford", "F-150", ["F150 Pickup 2WD", "F150 Pickup 4WD"], [19980, 19981, 19982, 19983, 20049, 20050, 20051, 20052, 20053], 1),
    R(11128, 2005, "Audi", "A4", ["A4", "A4 Avant quattro", "A4 Cabriolet", "A4 Cabriolet quattro", "A4 quattro"], [20589, 20662, 20663, 20664, 20998, 21552, 21553, 21554], 7),
    R(11138, 2005, "Chrysler", "300", ["300C AWD", "300C/SRT-8"], [20962, 20964, 20965], 2),
    R(11187, 2005, "Toyota", "Tacoma", ["Tacoma 2WD", "Tacoma 4WD"], [21138, 21139, 21185, 21186], 3),
    R(11191, 2005, "Volkswagen", "Jetta", ["Jetta", "Jetta Wagon"], [21039], 11),
    R(11194, 2006, "Audi", "A4", ["A4", "A4 Avant quattro", "A4 Cabriolet", "A4 Cabriolet quattro", "A4 quattro"], [21710, 21786, 21787, 21788, 21789], 4),
    R(11205, 2006, "Chrysler", "300", ["300", "300C AWD", "300C/SRT-8"], [22041], 5),
    R(11259, 2006, "Toyota", "Tacoma", ["Tacoma 2WD", "Tacoma 4WD"], [22234, 22235, 22294, 22295], 3),
    R(11280, 2007, "Chrysler", "300", ["300 AWD", "300/SRT-8"], [23602, 23604, 23605], 2),
    R(11282, 2007, "Dodge", "Charger", ["Charger", "Charger AWD"], [23612], 5),
    R(11338, 2007, "Toyota", "Tacoma", ["Tacoma 2WD", "Tacoma 4WD"], [23663, 23664, 23693, 23694], 3),
    R(11349, 2008, "Audi", "A4", ["A4", "A4 Avant quattro", "A4 Cabriolet", "A4 Cabriolet quattro", "A4 quattro"], [24246, 24247, 24279, 24281], 4),
    R(11359, 2008, "Chevrolet", "Silverado 1500", ["Silverado C15 2WD", "Silverado K15 4WD"], [24528, 24529, 24530, 24531], 5),
    R(11362, 2008, "Chrysler", "300", ["300 AWD", "300/SRT-8"], [24888, 24890, 24891, 24892], 2),
    R(11366, 2008, "Dodge", "Charger", ["Charger", "Charger AWD"], [24898], 6),
    R(11424, 2008, "Toyota", "Tacoma", ["Tacoma 2WD", "Tacoma 4WD"], [24936, 24937, 24940], 4),
    R(11447, 2009, "Chevrolet", "Silverado 1500", ["Silverado C15 2WD", "Silverado C15 XFE 2WD", "Silverado K15 4WD"], [25575, 25576, 25577, 25583, 25584, 25585, 25735, 25774, 26064, 26080, 26081, 26217], 1),
    R(11452, 2009, "Chrysler", "300", ["300 AWD", "300/SRT-8"], [25991, 25993, 25994], 2),
    R(11455, 2009, "Dodge", "Charger", ["Charger", "Charger AWD"], [26002], 6),
    R(11510, 2009, "Toyota", "Highlander", ["Highlander 2WD", "Highlander 4WD"], [29380], 2),
    R(11516, 2009, "Toyota", "Tacoma", ["Tacoma 2WD", "Tacoma 4WD"], [25559, 25560, 25573, 25574], 3),
    R(11546, 2010, "Chrysler", "300", ["300 AWD", "300/SRT-8"], [29319, 29320, 29321], 2),
    R(11549, 2010, "Dodge", "Charger", ["Charger", "Charger AWD"], [29325], 5),
    R(11561, 2010, "Honda", "Accord", ["Accord", "Accord Coupe"], [29656, 29657], 3),
    R(11742, 2012, "Chevrolet", "Silverado 1500", ["Silverado C15 2WD", "Silverado C15 XFE 2WD", "Silverado K15 4WD"], [31435, 31436, 31437, 31438, 31439, 31447, 31448, 31449, 31450], 0),
    R(11812, 2012, "Toyota", "Camry", ["Camry"], [31765, 31766], 0),
    R(12102, 2015, "Ford", "F-150", ["F150 Pickup 2WD", "F150 Pickup 2WD FFV", "F150 Pickup 4WD", "F150 Pickup 4WD FFV"], [35918, 35919, 35920, 35922, 35923, 35924], 2),
    R(12202, 2016, "Chevrolet", "Silverado 1500", ["Silverado C15 2WD", "Silverado C15 Cab Chassis 2WD", "Silverado K15 4WD", "Silverado K15 Cab Chassis 4WD"], [37004, 37005, 37007, 37008, 37014, 37015, 37016, 37046], 0),
    R(12228, 2016, "Ford", "F-150", ["F150 2.7L 2WD GVWR>6649 LBS PAYLOAD PACKAGE", "F150 2.7L 4WD GVWR>6799 LBS PAYLOAD PACKAGE", "F150 3.5L 2WD GVWR>7599 LBS PAYLOAD PACKAGE", "F150 3.5L 4WD GVWR>7599 LBS PAYLOAD PACKAGE", "F150 5.0L 2WD FFV GVWR>7599 LBS PAYLOAD PACKAGE", "F150 5.0L 4WD FFV GVWR>7599 LBS PAYLOAD PACKAGE", "F150 Pickup 2WD", "F150 Pickup 2WD FFV", "F150 Pickup 4WD", "F150 Pickup 4WD FFV"], [37039, 37040, 37041, 37044, 37045, 37047, 37048, 37049, 37051, 37053], 4),
    R(12279, 2016, "RAM", "1500", ["1500 2WD", "1500 4WD", "1500 HFE 2WD"], [36542, 36543, 36545, 36546, 36547, 36548, 36597], 3),
    R(12291, 2016, "Toyota", "Camry", ["Camry"], [36795, 36798], 0),
    R(12332, 2017, "Chevrolet", "Silverado 1500", ["Silverado C15 2WD", "Silverado C15 Cab Chassis 2WD", "Silverado K15 4WD", "Silverado K15 Cab Chassis 4WD"], [37641, 37642, 37643, 37650, 37651, 37652, 37654, 38185], 0),
    R(12360, 2017, "Ford", "F-150", ["F150 2.7L 2WD GVWR>6649 LBS", "F150 2.7L 4WD GVWR>6799 LBS", "F150 2WD BASE PAYLOAD LT TIRE", "F150 3.5L 2WD GVWR>7599 LBS", "F150 3.5L 4WD GVWR>7599 LBS", "F150 4WD BASE PAYLOAD LT TIRE", "F150 4WD FFV BASE PAYLOAD LT TIRE", "F150 5.0L 2WD FFV GVWR>7599 LBS", "F150 5.0L 4WD FFV GVWR>7599 LBS", "F150 Pickup 2WD", "F150 Pickup 2WD FFV", "F150 Pickup 4WD", "F150 Pickup 4WD FFV"], [38215, 38261, 38262, 38265, 38266, 38267, 38269, 38270, 38271, 38274, 38277, 38278, 38279], 6),
    R(12370, 2017, "GMC", "Sierra 1500", ["Sierra C15 2WD", "Sierra C15 Cab Chassis 2WD", "Sierra K15 4WD", "Sierra K15 Cab Chassis 4WD"], [37645, 37646, 37647, 37656, 37657, 37658, 37660, 38186], 0),
    R(12372, 2017, "Honda", "CR-V", ["CR-V AWD", "CR-V FWD"], [38448, 38452], 2),
    R(12386, 2017, "Jeep", "Grand Cherokee", ["Grand Cherokee 2WD", "Grand Cherokee 4WD"], [37857, 37863], 1),
    R(12413, 2017, "RAM", "1500", ["1500 2WD", "1500 4WD"], [37991, 37993, 37994, 39384, 39385], 2),
    R(12449, 2018, "Audi", "A4", ["A4 Ultra", "A4 quattro"], [38572, 38573], 1),
    R(12467, 2018, "Chevrolet", "Silverado 1500", ["Silverado C15 2WD", "Silverado C15 Cab Chassis 2WD", "Silverado K15 4WD", "Silverado K15 Cab Chassis 4WD"], [38943, 38947, 38981, 38982, 38984, 38989, 38990, 39359], 0),
    R(12481, 2018, "Dodge", "Challenger", ["Challenger", "Challenger GT"], [39049], 5),
    R(12487, 2018, "Dodge", "Durango", ["Durango AWD", "Durango RWD"], [39316, 39318], 2),
    R(12496, 2018, "Ford", "F-150", ["F150 2.7L 2WD GVWR>6649 LBS", "F150 2.7L 4WD GVWR>6799 LBS", "F150 2WD BASE PAYLOAD LT TIRE", "F150 2WD FFV BASE PAYLOAD LT", "F150 2WD FFV BASE PAYLOAD LT TIRE", "F150 3.5L 2WD GVWR>7599 LBS", "F150 3.5L 4WD GVWR>7599 LBS", "F150 4WD BASE PAYLOAD LT TIRE", "F150 4WD FFV BASE PAYLOAD LT", "F150 4WD FFV BASE PAYLOAD LT TIRE", "F150 5.0L 2WD FFV GVWR>7599 LBS", "F150 5.0L 2WD GVWR>7599 LBS", "F150 5.0L 4WD FFV GVWR>7599 LBS", "F150 5.0L 4WD GVWR>7599 LBS", "F150 Pickup 2WD", "F150 Pickup 2WD FFV", "F150 Pickup 4WD", "F150 Pickup 4WD FFV"], [39238, 39239, 39240, 39244, 39245, 39246, 39247, 39248, 39252, 39253, 39254, 39258, 39259, 39260, 39261, 39262, 39449, 40220, 40221, 40222], 6),
    R(12506, 2018, "GMC", "Sierra 1500", ["Sierra C15 2WD", "Sierra C15 Cab Chassis 2WD", "Sierra K15 4WD", "Sierra K15 Cab Chassis 4WD"], [38945, 38949, 38985, 38986, 38988, 38991, 38992, 39360], 0),
    R(12508, 2018, "Honda", "Accord", ["Accord", "Accord 2.0T Sport/Touring"], [39751], 5),
    R(12511, 2018, "Honda", "CR-V", ["CR-V AWD", "CR-V FWD"], [39624, 39628], 2),
    R(12513, 2018, "Honda", "Civic", ["Civic 2Dr", "Civic 4Dr", "Civic 5Dr", "Civic 5Dr Sport"], [39558, 39559, 39565, 39566], 6),
    R(12522, 2018, "Hyundai", "Santa Fe", ["Santa Fe AWD", "Santa Fe FWD", "Santa Fe Ultimate AWD", "Santa Fe Ultimate FWD"], [38744, 38748], 2),
    R(12529, 2018, "Jeep", "Grand Cherokee", ["Grand Cherokee 2WD", "Grand Cherokee 4WD"], [39101, 39103, 40042, 40043], 1),
    R(12557, 2018, "RAM", "1500", ["1500 2WD", "1500 4WD"], [39619, 39620, 39868, 39869], 3),
    R(12569, 2018, "Toyota", "Camry", ["Camry", "Camry LE/SE", "Camry XLE/XSE", "Camry XSE"], [38883], 3),
    R(12595, 2019, "Audi", "A4", ["A4", "A4 quattro"], [40868], 1),
    R(12629, 2019, "Dodge", "Charger", ["Charger", "Charger AWD"], [40620], 4),
    R(12632, 2019, "Dodge", "Durango", ["Durango AWD", "Durango RWD"], [40669, 40672], 2),
    R(12641, 2019, "Ford", "F-150", ["F150 2.7L 2WD GVWR>6649 LBS", "F150 2.7L 4WD GVWR>6799 LBS", "F150 2WD BASE PAYLOAD LT TIRE", "F150 2WD FFV BASE PAYLOAD LT", "F150 3.5L 2WD GVWR>7599 LBS", "F150 3.5L 4WD GVWR>7599 LBS", "F150 4WD BASE PAYLOAD LT TIRE", "F150 4WD FFV BASE PAYLOAD LT", "F150 5.0L 2WD FFV GVWR>7599 LBS", "F150 5.0L 4WD FFV GVWR>7599 LBS", "F150 Pickup 2WD", "F150 Pickup 2WD FFV", "F150 Pickup 2WD Limited", "F150 Pickup 4WD", "F150 Pickup 4WD FFV", "F150 Pickup 4WD Limited"], [41015, 41016, 41017, 41018, 41019, 41020, 41021, 41028, 41029, 41030, 41031, 41033, 41034, 41035, 41040, 41105, 41106, 41113], 6),
    R(12653, 2019, "GMC", "Sierra 1500", ["Sierra C10 2WD", "Sierra C10 Cab Chassis 2WD", "Sierra C10 XFE 2WD", "Sierra K10 4WD", "Sierra K10 4WD AT4", "Sierra K10 Cab Chassis 4WD"], [40427, 40428, 40429, 40430, 40949, 40956, 40957, 40958, 40959, 41115], 6),
    R(12723, 2019, "Toyota", "Camry", ["Camry", "Camry LE/SE", "Camry XLE/XSE", "Camry XSE"], [40606, 40607, 40609], 2),
    R(12749, 2020, "Chevrolet", "Equinox", ["Equinox AWD", "Equinox FWD"], [41500, 41505], 2),
    R(12750, 2020, "Chevrolet", "Silverado 1500", ["Silverado 2WD", "Silverado 4WD", "Silverado Cab Chassis 2WD", "Silverado Cab Chassis 4WD"], [41818, 41820, 41821, 41824, 41837, 41838, 41842, 41844], 8),
    R(12754, 2020, "Chrysler", "300", ["300", "300 AWD"], [42329, 42390], 1),
    R(12760, 2020, "Dodge", "Durango", ["Durango AWD", "Durango RWD"], [41771, 41779], 2),
    R(12762, 2020, "Ford", "Escape", ["Escape AWD", "Escape FWD"], [42074, 42257], 1),
    R(12764, 2020, "Ford", "Explorer", ["Explorer AWD", "Explorer FFV AWD", "Explorer RWD"], [41485, 41487, 41512], 1),
    R(12766, 2020, "Ford", "F-150", ["F150 2WD BASE PAYLOAD LT TIRE", "F150 2WD FFV BASE PAYLOAD LT", "F150 5.0L 2WD FFV GVWR>7599 LBS", "F150 Pickup 2WD", "F150 Pickup 2WD FFV", "F150 Pickup 2WD Limited", "F150 Pickup 4WD", "F150 Pickup 4WD FFV", "F150 Pickup 4WD Limited"], [42167, 42171, 42172, 42173, 42174, 42176, 42177, 42179, 42517, 42518, 42520], 4),
    R(12769, 2020, "Ford", "Mustang", ["Mustang", "Mustang Bullitt", "Mustang Convertible", "Mustang HO Convertible", "Mustang HO Coupe"], [41951, 41952, 41953, 41956, 41957], 6),
    R(12771, 2020, "GMC", "Sierra 1500", ["Sierra 2WD", "Sierra 4WD", "Sierra Cab Chassis 2WD", "Sierra Cab Chassis 4WD"], [41825, 41827, 41828, 41831, 41850, 41851, 41855, 41858], 8),
    R(12778, 2020, "Honda", "Civic", ["Civic 2Dr", "Civic 4Dr", "Civic 5Dr"], [41747, 41748, 41749, 41884, 42140, 42141, 42149, 42150], 7),
    R(12785, 2020, "Jeep", "Cherokee", ["Cherokee 4WD", "Cherokee 4WD Active Drive II", "Cherokee FWD", "Cherokee Trailhawk 4WD"], [41659, 41660, 41661, 41670, 41671, 41672], 4),
    R(12787, 2020, "Jeep", "Grand Cherokee", ["Grand Cherokee 2WD", "Grand Cherokee 4WD"], [41781], 2),
    R(12790, 2020, "Jeep", "Wrangler", ["Wrangler 4WD"], [41677, 41764], 4),
    R(12794, 2020, "Mazda", "MX-5 Miata", ["MX-5"], [42439], 1),
    R(12797, 2020, "RAM", "1500", ["1500 2WD", "1500 4WD", "1500 HFE 2WD"], [42154, 42155], 4),
    R(12800, 2020, "Subaru", "Outback", ["Outback AWD"], [41570], 1),
    R(12802, 2020, "Toyota", "Camry", ["Camry", "Camry AWD LE/SE", "Camry AWD XLE/XSE", "Camry LE/SE", "Camry TRD", "Camry XLE/XSE", "Camry XSE"], [42011, 42012, 42015], 4),
    R(12805, 2020, "Toyota", "Highlander", ["Highlander", "Highlander AWD"], [42379, 42380], 1),
    R(12809, 2020, "Toyota", "Tacoma", ["Tacoma 2WD", "Tacoma 4WD", "Tacoma 4WD D-CAB MT TRD-ORP/PRO"], [42031, 42034], 4),
    R(12819, 2021, "Chevrolet", "Silverado 1500", ["Silverado 2WD", "Silverado 4WD", "Silverado Cab Chassis 2WD", "Silverado Cab Chassis 4WD"], [43088, 43089, 43090, 43091, 43096, 43098, 43099, 43100, 43101, 43104, 43185, 43366, 43816, 43868, 43870, 43872, 44025, 44027], 4),
    R(12824, 2021, "Dodge", "Challenger", ["Challenger", "Challenger AWD", "Challenger Widebody"], [43434, 43435, 43436, 43437, 43438], 1),
    R(12826, 2021, "Dodge", "Charger", ["Charger", "Charger AWD", "Charger Widebody"], [43396, 43451, 43452], 1),
    R(12828, 2021, "Dodge", "Durango", ["Durango AWD", "Durango RWD"], [43319, 43320], 2),
    R(12830, 2021, "Ford", "Escape", ["Escape AWD", "Escape FWD"], [43645, 43650], 1),
    R(12832, 2021, "Ford", "Explorer", ["Explorer AWD", "Explorer FFV AWD", "Explorer RWD", "Explorer Timberline AWD"], [43285, 43289, 43290], 5),
    R(12834, 2021, "Ford", "F-150", ["F150 Pickup 2WD", "F150 Pickup 2WD FFV", "F150 Pickup 4WD", "F150 Pickup 4WD FFV", "F150 Pickup Tremor 4WD"], [43457, 43458, 43459, 43463, 43464, 43466, 43616, 44364, 44366, 44369, 44374], 4),
    R(12839, 2021, "Ford", "Mustang", ["Mustang", "Mustang Convertible", "Mustang HO Convertible", "Mustang HO Coupe", "Mustang Mach 1"], [43667, 43669, 43672, 43673, 43676, 43677, 43680, 43681], 3),
    R(12841, 2021, "GMC", "Sierra 1500", ["Sierra 2WD", "Sierra 4WD", "Sierra Cab Chassis 2WD", "Sierra Cab Chassis 4WD"], [43092, 43093, 43094, 43095, 43107, 43108, 43109, 43111, 43113, 43115, 43188, 43189, 43196, 43315, 43817, 43818, 43869, 43873, 44031], 2),
    R(12845, 2021, "Honda", "Accord", ["Accord", "Accord Sport/Touring"], [43361, 43363], 1),
    R(12848, 2021, "Honda", "Civic", ["Civic 4Dr", "Civic 5Dr"], [43055, 43056, 43057, 43355, 43356], 3),
    R(12855, 2021, "Jeep", "Cherokee", ["Cherokee 4WD", "Cherokee 4WD Active Drive II", "Cherokee FWD", "Cherokee Trailhawk 4WD"], [43062, 43063, 43064, 43065, 43066, 43067], 3),
    R(12860, 2021, "Jeep", "Wrangler", ["Wrangler 2dr 4WD", "Wrangler 4dr 4WD", "Wrangler 4dr EcoDiesel 4WD", "Wrangler Rubic 4dr EcoDiesel 4WD"], [42910, 44091], 2),
    R(12863, 2021, "Mazda", "MX-5 Miata", ["MX-5"], [43626], 1),
    R(12865, 2021, "RAM", "1500", ["1500 2WD", "1500 4WD", "1500 HFE 2WD"], [43007, 43015, 43722], 4),
    R(12868, 2021, "Subaru", "Outback", ["Outback AWD"], [42858], 1),
    R(12870, 2021, "Toyota", "Camry", ["Camry", "Camry AWD LE/SE", "Camry AWD XLE/XSE", "Camry LE/SE", "Camry TRD", "Camry XLE/XSE", "Camry XSE"], [43302, 43305, 43306, 43309, 43310], 2),
    R(12872, 2021, "Toyota", "Highlander", ["Highlander", "Highlander AWD"], [43128, 43129], 1),
    R(12876, 2021, "Toyota", "Tacoma", ["Tacoma 2WD", "Tacoma 4WD", "Tacoma 4WD D-CAB MT TRD-ORP/PRO"], [43082, 43084, 43085], 2),
    R(12885, 2022, "Chevrolet", "Silverado 1500", ["Silverado 2WD", "Silverado 4WD", "Silverado Cab Chassis 2WD", "Silverado Cab Chassis 4WD"], [44580, 44582, 44628, 44634, 44635, 44727, 44728, 44735, 44742, 44827, 45159, 45164, 45166, 45195], 3),
    R(12889, 2022, "Chrysler", "300", ["300", "300 AWD"], [45077, 45078], 1),
    R(12895, 2022, "Dodge", "Durango", ["Durango AWD", "Durango RWD"], [45038, 45041], 2),
    R(12897, 2022, "Ford", "Escape", ["Escape AWD", "Escape FWD"], [44815], 2),
    R(12899, 2022, "Ford", "Explorer", ["Explorer AWD", "Explorer FFV AWD", "Explorer RWD", "Explorer Timberline AWD"], [44825, 44963, 44964, 44974, 44975, 44977, 44978], 4),
    R(12901, 2022, "Ford", "F-150", ["F150 Pickup 2WD", "F150 Pickup 2WD FFV", "F150 Pickup 4WD", "F150 Pickup 4WD FFV", "F150 Pickup Tremor 4WD"], [44866, 44867, 44868, 44869, 44870, 44872, 44873, 44874, 44876, 44878, 44883], 3),
    R(12904, 2022, "Ford", "Mustang", ["Mustang", "Mustang Convertible", "Mustang HO Convertible", "Mustang HO Coupe", "Mustang Mach 1"], [45044, 45045, 45047, 45049, 45050, 45054, 45055, 45056], 3),
    R(12906, 2022, "GMC", "Sierra 1500", ["Sierra 2WD", "Sierra 4WD", "Sierra Cab Chassis 2WD", "Sierra Cab Chassis 4WD"], [44581, 44584, 44629, 44639, 44640, 44731, 44744, 44747, 44749, 44829, 45161, 45169, 45171], 4),
    R(12910, 2022, "Honda", "Accord", ["Accord", "Accord Sport/Touring"], [44565, 44566], 1),
    R(12913, 2022, "Honda", "Civic", ["Civic 4Dr", "Civic 5Dr"], [44131, 44132, 44545, 44546, 44547, 44846], 5),
    R(12925, 2022, "Jeep", "Wrangler", ["Wrangler 2dr 4WD", "Wrangler 4dr 4WD", "Wrangler 4dr EcoDiesel 4WD", "Wrangler Rubic 4dr EcoDiesel 4WD"], [44909, 44910], 2),
    R(12931, 2022, "RAM", "1500", ["1500 2WD", "1500 4WD", "1500 HFE 2WD"], [44393, 44396, 44397, 44399, 44402], 3),
    R(12933, 2022, "Subaru", "Outback", ["Outback AWD", "Outback Wilderness AWD"], [43865], 2),
    R(12935, 2022, "Toyota", "Camry", ["Camry", "Camry AWD LE/SE", "Camry AWD XLE/XSE", "Camry LE/SE", "Camry TRD", "Camry XLE/XSE", "Camry XSE"], [44343, 44346, 44347, 44348, 44349], 2),
    R(12937, 2022, "Toyota", "Highlander", ["Highlander", "Highlander AWD"], [44649, 44650], 1),
    R(12941, 2022, "Toyota", "Tacoma", ["Tacoma 2WD", "Tacoma 4WD", "Tacoma 4WD D-CAB MT TRD-ORP/PRO"], [44475, 44480], 4),
    R(12950, 2023, "Chevrolet", "Silverado 1500", ["Silverado 2WD", "Silverado 4WD", "Silverado Cab Chassis 2WD", "Silverado Cab Chassis 4WD"], [45770, 45771, 45772, 45775, 45776, 45785, 45787, 45788, 45796], 1),
    R(12962, 2023, "Ford", "Escape", ["Escape AWD", "Escape FWD"], [46324, 46388], 1),
    R(12964, 2023, "Ford", "Explorer", ["Explorer AWD", "Explorer FFV AWD", "Explorer RWD", "Explorer Timberline AWD"], [46400, 46401, 46410, 46411, 46421, 46439, 46440], 6),
    R(12966, 2023, "Ford", "F-150", ["F150 Pickup 2WD", "F150 Pickup 2WD FFV", "F150 Pickup 4WD", "F150 Pickup 4WD FFV", "F150 Pickup Tremor 4WD", "F150 Pickup Tremor 4WD FFV"], [46161, 46162, 46163, 46164, 46165, 46171, 46172, 46173, 46174, 46175, 46177, 46179], 4),
    R(12971, 2023, "GMC", "Sierra 1500", ["Sierra 2WD", "Sierra 4WD", "Sierra Cab Chassis 2WD", "Sierra Cab Chassis 4WD"], [45777, 45778, 45779, 45800, 45802, 45805, 45810], 4),
    R(12978, 2023, "Honda", "Civic", ["Civic 4Dr", "Civic 5Dr"], [46051, 46052, 46053, 46137, 46138, 46139], 6),
    R(12990, 2023, "Jeep", "Wrangler", ["Wrangler 2dr 4WD", "Wrangler 4dr 4WD", "Wrangler 4dr EcoDiesel 4WD", "Wrangler Rubic 4dr EcoDiesel 4WD"], [45693, 45953], 2),
    R(12997, 2023, "RAM", "1500", ["1500 2WD", "1500 4WD", "1500 HFE 2WD"], [46226], 4),
    R(12999, 2023, "Subaru", "Outback", ["Outback AWD", "Outback Wilderness AWD"], [45408], 2),
    R(13001, 2023, "Toyota", "Camry", ["Camry", "Camry AWD LE/SE", "Camry AWD XLE/XSE", "Camry LE/SE", "Camry TRD", "Camry XLE/XSE", "Camry XSE"], [45719, 45721], 5),
    R(13007, 2023, "Toyota", "Tacoma", ["Tacoma 2WD", "Tacoma 4WD", "Tacoma 4WD D-CAB MT TRD-ORP/PRO"], [45865, 45869], 4),
    R(13016, 2024, "Chevrolet", "Silverado 1500", ["Silverado 2WD", "Silverado 4WD", "Silverado Cab Chassis 2WD", "Silverado Cab Chassis 4WD"], [46811, 46812, 46813, 46814, 46815, 46823, 46828, 46832, 46835, 46836, 47112, 47113, 47121, 47122], 1),
    R(13026, 2024, "Dodge", "Durango", ["Durango AWD", "Durango RWD"], [47403, 47425], 2),
    R(13030, 2024, "Ford", "Explorer", ["Explorer AWD", "Explorer FFV AWD", "Explorer RWD", "Explorer Timberline AWD"], [47672, 47673, 47679, 47680, 47683], 3),
    R(13032, 2024, "Ford", "F-150", ["F150 Pickup 2WD", "F150 Pickup 4WD", "F150 Pickup Tremor 4WD"], [47603, 47604, 47614, 47616, 48458, 48459], 2),
    R(13037, 2024, "GMC", "Sierra 1500", ["Sierra 2WD", "Sierra 4WD", "Sierra Cab Chassis 2WD", "Sierra Cab Chassis 4WD"], [46820, 46841, 46851, 47114, 47115, 47124, 47125], 8),
    R(13044, 2024, "Honda", "Civic", ["Civic 4Dr", "Civic 5Dr"], [47071, 47072, 47100, 47101, 47102, 47582], 6),
    R(13057, 2024, "Jeep", "Wrangler", ["Wrangler 2dr 4WD", "Wrangler 4dr 4WD", "Wrangler Rubicon 2dr 4WD", "Wrangler Rubicon 4dr 4WD"], [46886, 46888, 47379], 2),
    R(13065, 2024, "Subaru", "Outback", ["Outback AWD", "Outback Wilderness AWD"], [46541], 2),
    R(13067, 2024, "Toyota", "Camry", ["Camry", "Camry AWD LE/SE", "Camry AWD XLE/XSE", "Camry LE/SE", "Camry TRD", "Camry XLE/XSE", "Camry XSE"], [47085, 47087], 4),
    R(13082, 2025, "Chevrolet", "Silverado 1500", ["Silverado 2WD", "Silverado 4WD", "Silverado Cab Chassis 2WD", "Silverado Cab Chassis 4WD"], [48199, 48200, 48201, 48209, 48210, 48214, 48220], 6),
    R(13092, 2025, "Dodge", "Durango", ["Durango AWD", "Durango RWD"], [48280, 48288], 2),
    R(13094, 2025, "Ford", "Escape", ["Escape AWD", "Escape FWD"], [48602, 48608], 1),
    R(13096, 2025, "Ford", "Explorer", ["Explorer AWD", "Explorer RWD"], [48118, 48119, 48281, 48282], 2),
    R(13098, 2025, "Ford", "F-150", ["F150 Pickup 2WD", "F150 Pickup 4WD", "F150 Pickup Tremor 4WD"], [48885, 48886, 48894, 48896, 49143], 3),
    R(13103, 2025, "GMC", "Sierra 1500", ["Sierra 2WD", "Sierra 4WD", "Sierra Cab Chassis 2WD", "Sierra Cab Chassis 4WD"], [48204, 48205, 48206, 48207, 48208, 48229, 48232, 48233, 48235, 48240], 1),
    R(13107, 2025, "Honda", "Accord", ["Accord"], [48504], 0),
    R(13110, 2025, "Honda", "Civic", ["Civic 4Dr", "Civic 5Dr"], [48178], 6),
    R(13123, 2025, "Jeep", "Wrangler", ["Wrangler 2dr 4WD", "Wrangler 4dr 4WD"], [48530], 3),
    R(13128, 2025, "RAM", "1500", ["1500 2WD", "1500 4WD", "1500 HFE 2WD", "1500 HO 4WD"], [47722, 47725], 3),
    R(13131, 2025, "Subaru", "Outback", ["Outback AWD", "Outback Wilderness AWD"], [47801], 2),
    R(13135, 2025, "Toyota", "Highlander", ["Highlander", "Highlander AWD"], [48912, 48913, 48940], 0),
    R(13148, 2026, "Chevrolet", "Silverado 1500", ["Silverado 2WD", "Silverado 4WD", "Silverado Cab Chassis 2WD", "Silverado Cab Chassis 4WD"], [49358, 49362, 49384, 49394], 2),
    R(13158, 2026, "Dodge", "Durango", ["Durango AWD", "Durango RWD"], [49551, 49575, 50149, 50150], 1),
    R(13160, 2026, "Ford", "Escape", ["Escape AWD", "Escape FWD"], [49849], 2),
    R(13162, 2026, "Ford", "Explorer", ["Explorer AWD", "Explorer RWD", "Explorer Tremor AWD"], [49878, 49907, 49908], 3),
    R(13164, 2026, "Ford", "F-150", ["F150 Pickup 2WD", "F150 Pickup 4WD", "F150 Pickup Tremor 4WD"], [50092, 50093, 50098, 50099, 50102], 2),
    R(13167, 2026, "Ford", "Mustang", ["Mustang", "Mustang Dark Horse", "Mustang Dark Horse SC", "Mustang GTD", "Mustang Performance Package"], [49792, 49793, 49794, 50279], 2),
    R(13169, 2026, "GMC", "Sierra 1500", ["Sierra 2WD", "Sierra 4WD", "Sierra 4WD FFV", "Sierra Cab Chassis 2WD", "Sierra Cab Chassis 4WD"], [49366, 49367, 49404, 49406, 49413], 2),
    R(13173, 2026, "Honda", "Accord", ["Accord", "Accord SE"], [50055, 50070], 0),
    R(13176, 2026, "Honda", "Civic", ["Civic 4Dr", "Civic 5Dr"], [49286], 5),
    R(13187, 2026, "Jeep", "Wrangler", ["Wrangler 2dr 4WD", "Wrangler 4dr 4WD"], [49852], 3),
    R(13190, 2026, "RAM", "1500", ["1500 2WD", "1500 4WD", "1500 HO 4WD", "1500 Warlock 4WD"], [49368, 49420, 50108], 2),
    R(13193, 2026, "Subaru", "Outback", ["Outback AWD", "Outback Wilderness AWD"], [49531], 2),
    R(13197, 2026, "Toyota", "Highlander", ["Highlander AWD"], [50132], 0),
    R(13818, 2000, "Audi", "A4", ["A4", "A4 Avant", "A4 Avant quattro", "A4 quattro"], [15746, 15747, 15748, 15749, 16013], 5),
    R(13820, 2000, "Audi", "A6", ["A6", "A6 Avant quattro", "A6 quattro"], [15874, 15875, 15876, 15877, 15878], 1),
    R(14132, 2001, "Ford", "Explorer", ["Explorer 2WD", "Explorer 4WD"], [17126, 17219], 2),
    R(14435, 2001, "Volkswagen", "Jetta", ["Jetta", "Jetta Wagon"], [16893], 8),
    R(14588, 2001, "Suzuki", "Grand Vitara", ["Grand Vitara", "Grand Vitara 4WD"], [17280, 17281], 2),
    R(14718, 2001, "Audi", "A4", ["A4", "A4 Avant quattro", "A4 quattro"], [16577, 16578, 16579, 16580, 16873], 3),
    R(14720, 2001, "Audi", "A6", ["A6", "A6 Avant quattro", "A6 quattro"], [16737, 16738, 16739, 16740], 1),
    R(15374, 2002, "Volkswagen", "Jetta", ["Jetta", "Jetta Wagon"], [17828, 17829, 17830], 10),
    R(15524, 2002, "Suzuki", "Grand Vitara", ["Grand Vitara", "Grand Vitara 4WD"], [18237, 18238], 2),
    R(15682, 2002, "Audi", "A6", ["A6", "A6 Avant quattro", "A6 quattro"], [17667, 17668, 17669, 17670], 1),
    R(16327, 2003, "Volkswagen", "Jetta", ["Jetta", "Jetta Wagon"], [18793, 18794, 18795], 8),
    R(16632, 2003, "Audi", "A6", ["A6", "A6 Avant quattro", "A6 quattro"], [18632, 18633, 18634, 18635], 1),
    R(17303, 2004, "Volkswagen", "Jetta", ["Jetta", "Jetta Wagon"], [19905, 19907], 8),
    R(17633, 2004, "Audi", "A6", ["A6", "A6 Avant quattro", "A6 quattro"], [19714, 19715, 19716, 19717], 1),
    R(17646, 2004, "Porsche", "911", ["Carrera 2 Cabriolet", "Carrera 2 Cabriolet Kit", "Carrera 2 Coupe", "Carrera 2 Coupe Kit", "Carrera 4 Cabriolet", "Carrera 4 Cabriolet Kit", "Carrera 4 S Cabriolet", "Carrera 4 S Cabriolet Kit", "Carrera 4 S Coupe", "Carrera 4 S Kit", "Targa", "Targa Kit", "Turbo 4 911", "Turbo 4 911 Cab", "Turbo 4 911 Cab Kit", "Turbo 4 911 Kit"], [19415, 19416, 19421, 19422], 8),
    R(17921, 2005, "BMW", "M3", ["M3", "M3 Convertible"], [20521, 20522], 2),
    R(18624, 2005, "Porsche", "911", ["Carrera 2 Cabriolet", "Carrera 2 Cabriolet Kit", "Carrera 2 Coupe", "Carrera 2 Coupe Kit", "Carrera 2 S Cabriolet", "Carrera 2 S Coupe", "Carrera 4 Cabriolet", "Carrera 4 Cabriolet Kit", "Carrera 4 S Cabriolet", "Carrera 4 S Cabriolet Kit", "Carrera 4 S Coupe", "Carrera 4 S Kit", "Targa", "Targa Kit", "Turbo 4 911 Cab", "Turbo 4 911 Cab Kit", "Turbo 4 911 Kit", "Turbo 4 911 S", "Turbo 4 911 Turbo", "Turbo 4 911 Turbo Cab S"], [20538, 20539, 20540, 20548, 20549, 20552, 20553, 20560], 12),
    R(18912, 2006, "BMW", "M3", ["M3", "M3 Convertible"], [21675, 21676], 2),
    R(20655, 2007, "Porsche", "911", ["Carrera 2 Cabriolet", "Carrera 2 Coupe", "Carrera 2 S Cabriolet", "Carrera 2 S Coupe", "Carrera 4 Cabriolet", "Carrera 4 Coupe", "Carrera 4 S Cabriolet", "Carrera 4 S Coupe", "Carrera 4 S Targa", "Carrera 4 Targa", "Turbo 4 911 Turbo"], [23096, 23097, 23100, 23101, 23104, 23105, 23108, 23109], 2),
    R(21742, 2008, "Porsche", "911", ["911 Turbo", "911 Turbo Cabriolet", "Carrera 2 Cabriolet", "Carrera 2 Coupe", "Carrera 2 S Cabriolet", "Carrera 2 S Coupe", "Carrera 4 Cabriolet", "Carrera 4 Coupe", "Carrera 4 S Cabriolet", "Carrera 4 S Coupe", "Carrera 4 S Targa", "Carrera 4 Targa"], [24223, 24224, 24227, 24228, 24231, 24232, 24235, 24236], 4),
    R(32584, 2018, "MINI", "Countryman", ["Cooper Countryman", "Cooper Countryman All4", "Cooper S Countryman", "Cooper S Countryman All4", "Cooper SE Countryman All4", "JCW Countryman All4"], [39164, 39165, 39167, 39168, 39171, 39172, 39173], 2),
    R(33916, 2019, "MINI", "Countryman", ["Cooper Countryman", "Cooper Countryman All4", "Cooper S Countryman", "Cooper S Countryman All4", "Cooper SE Countryman All4", "JCW Countryman All4"], [40010, 40011, 40014, 40015, 40018, 40019], 2),
    R(38591, 2019, "Chevrolet", "Silverado 1500", ["Silverado C10 2WD", "Silverado C10 Cab Chassis 2WD", "Silverado C10 XFE 2WD", "Silverado K10 4WD", "Silverado K10 4WD TrailBoss", "Silverado K10 Cab Chassis 4WD"], [40426], 0),
    R(38684, 2020, "Volkswagen", "Golf GTI", ["GTI"], [42124], 0),
    R(38712, 2012, "Mazda", "Mazda3", ["3", "3 DI 4-Door", "3 DI 5-Door"], [32056, 32057, 32086], 0),
    R(38713, 2013, "Mazda", "Mazda3", ["3", "3 DI 4-Door", "3 DI 5-Door"], [32924, 32925, 32983], 0),
]
assert len({o["id"] for o in OPS}) == len(OPS) == 224
assert sum(len(o["add"]) for o in OPS) == 873 and sum(o["cost"] for o in OPS) == 653
assert len({i for o in OPS for i in o["add"]}) == 873


class PlanError(Exception):
    pass


def say(*a):
    print(" ".join(str(x) for x in a).encode("ascii", "replace").decode("ascii"), flush=True)


def num(x):
    try:
        return int(float(x)) if x not in ("", None) else None
    except ValueError:
        return None


def fnum(text):
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(text)) if text not in (None, "") else None
    return float(m.group(1)) if m else None


def load_epa(path):
    with open(path, "rb") as fh:
        data = fh.read(ZIP_MAX + 1)
    if len(data) > ZIP_MAX:
        sys.exit("%s is larger than %d bytes: not the pinned EPA file" % (path, ZIP_MAX))
    got = hashlib.sha256(data).hexdigest()
    if got != ZIP_SHA256:
        sys.exit("%s has sha256 %s, not the pinned EPA file %s" % (path, got, ZIP_SHA256))
    z = zipfile.ZipFile(io.BytesIO(data))
    info = z.infolist()
    if [i.filename for i in info] != ["vehicles.csv"] or info[0].file_size > CSV_MAX:
        sys.exit("the EPA file must hold exactly one member, vehicles.csv, of at most %d bytes" % CSV_MAX)
    by_id, by_ym = {}, collections.defaultdict(list)
    for r in csv.DictReader(io.StringIO(z.read("vehicles.csv").decode("utf-8", "replace"))):
        rec = {"id": int(r["id"]), "year": int(r["year"]), "make": r["make"].strip(), "name": r["model"].strip(),
               "atv": r["atvType"].strip(), "city": num(r["city08"]), "hwy": num(r["highway08"]), "comb": num(r["comb08"]),
               "cost": num(r["fuelCost08"]), "displ": r["displ"].strip() or None, "trans": r["trany"].strip() or None,
               "drive": r["drive"].strip() or None, "fuel": r["fuelType"].strip() or None}
        if rec["id"] in by_id:
            sys.exit("EPA record id %d appears twice in the file" % rec["id"])
        by_id[rec["id"]] = rec
        by_ym[(rec["year"], rec["make"].lower())].append(rec)
    return by_id, by_ym


def stored(cur, vid):
    return [list(r) for r in cur.execute("SELECT id, %s FROM fuel_economy WHERE vehicle_id=? ORDER BY id" % COLS, (vid,))]


def gas_row(rec):
    return [rec["city"], rec["hwy"], rec["comb"], rec["cost"], rec["displ"], rec["trans"], rec["drive"], None, None,
            rec["fuel"], None, None, None, None]


def key_line(d):
    return (d[CITY], d[HWY], d[COMB], fnum(d[ENG]), d[TRANS], d[DRIVE])


def key_rec(r):
    return (r["city"], r["hwy"], r["comb"], fnum(r["displ"]), r["trans"], r["drive"])


def hold_group(make, model, r):
    for hm, hmd, rx, size, grp in HOLD:
        if hm == make and (hmd is None or hmd == model) and re.fullmatch(rx, r["name"]) and (size is None or fnum(r["displ"]) == size):
            return grp
    return None


def fmt(d):
    return "%2s/%2s/%2s  %-4s %-28s %-26s cost %-5s fuel %s" % (d[CITY], d[HWY], d[COMB], d[ENG], d[TRANS], d[DRIVE], d[COST], d[FTYPE])


def after_rows(p):
    new_cost = {fid: new for fid, _old, new in p["cost_updates"]}
    rows = []
    for r in p["current"]:
        d = list(r[1:])
        if r[0] in new_cost:
            d[COST] = new_cost[r[0]]
        rows.append(d)
    return rows + [list(x) for x in p["insert"]]


def plan_op(cur, op, by_id, by_ym, verified):
    vid, year, make, model = op["id"], op["year"], op["make"], op["model"]
    row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
    if not row or tuple(row) != (year, make, model):
        raise PlanError("target %d is %r, not %d %s %s" % (vid, row and tuple(row), year, make, model))
    cur_rows = stored(cur, vid)
    if not cur_rows:
        raise PlanError("target %d holds no fuel-economy line" % vid)
    gas = [r for r in cur_rows if r[1 + FTYPE] != "Electric"]
    stored_keys = {key_line(r[1:]) for r in gas}
    recs = by_ym.get((year, make.lower()), [])
    taken = set(op["taken"])
    absent = sorted(taken - {r["name"] for r in recs})
    if absent:
        raise PlanError("id %d: EPA's file lists no %r for %d %s" % (vid, absent, year, make))
    first = collections.OrderedDict()
    for r in recs:
        if r["name"] in taken and r["atv"] not in NOT_GAS and r["city"] is not None:
            first.setdefault(key_rec(r), []).append(r)
    new, add_keys = [], set()
    for eid in op["add"]:
        r = by_id.get(eid)
        if r is None:
            raise PlanError("id %d: EPA record %d is not in the file" % (vid, eid))
        if (r["year"], r["make"].lower()) != (year, make.lower()) or r["name"] not in taken:
            raise PlanError("id %d: EPA record %d is %d %s %s, not one of the names taken" % (vid, eid, r["year"], r["make"], r["name"]))
        if r["atv"] not in TAKE_ATV:
            raise PlanError("id %d: EPA record %d is typed %r, which this repair does not add" % (vid, eid, r["atv"]))
        if hold_group(make, model, r):
            raise PlanError("id %d: EPA record %d (%s) is of a held kind: %s" % (vid, eid, r["name"], hold_group(make, model, r)))
        if None in (r["city"], r["hwy"], r["comb"], r["displ"], r["trans"], r["drive"]):
            raise PlanError("id %d: EPA record %d lacks a figure, an engine size, a transmission or a drive" % (vid, eid))
        k = key_rec(r)
        if k in stored_keys or k in add_keys:
            raise PlanError("id %d: EPA record %d equals a line already stored or already added" % (vid, eid))
        if first[k][0]["id"] != eid:
            raise PlanError("id %d: EPA record %d is not the first record of its line (%d is)" % (vid, eid, first[k][0]["id"]))
        add_keys.add(k)
        new.append((gas_row(r), r))
    # completeness: every own record is stored, added, held (a hybrid / plug-in, item c, or a HOLD kind), or the record
    # of a stored line whose figures EPA has since revised (item e). Anything else stops the run.
    hits = {key_rec(r) for r in recs}
    revised_twins = [key_line(r[1:]) for r in gas if key_line(r[1:]) not in hits]
    held, revised = [], []
    for k, rs in first.items():
        if k in stored_keys or k in add_keys:
            continue
        if all(r["atv"] not in TAKE_ATV for r in rs):
            held.append((rs[0], "%s, item (c)" % rs[0]["atv"]))
            continue
        if hold_group(make, model, rs[0]):
            held.append((rs[0], hold_group(make, model, rs[0])))
            continue
        tw = [t for t in revised_twins if t[3:] == k[3:]]
        if tw:
            revised_twins.remove(tw[0])
            revised.append(rs[0])
            continue
        raise PlanError("id %d: own EPA record %d (%s) is neither stored, added nor held -- needs a look" % (vid, rs[0]["id"], rs[0]["name"]))
    cost_updates, cost_left = [], []
    for r in gas:
        rs = first.get(key_line(r[1:]))
        if not rs:
            continue
        now = sorted({x["cost"] for x in rs if x["cost"] is not None})
        if len(now) == 1 and r[1 + COST] != now[0]:
            cost_updates.append([r[0], r[1 + COST], now[0]])
        elif len(now) > 1:
            cost_left.append([r[0], r[1 + COST], now])
    if len(cost_updates) != op["cost"]:
        raise PlanError("id %d: %d yearly costs to change, expected %d" % (vid, len(cost_updates), op["cost"]))
    say("")
    say("[FILL] id %d  %d %s %s%s   (%d stored line%s, %d added, %d cost%s changed)" % (
        vid, year, make, model, "  VERIFIED" if vid in verified else "", len(cur_rows), "" if len(cur_rows) == 1 else "s",
        len(new), len(cost_updates), "" if len(cost_updates) == 1 else "s"))
    say("  names taken: %s" % "; ".join(sorted(taken)))
    for r in cur_rows:
        d = r[1:]
        c = [u for u in cost_updates if u[0] == r[0]]
        say("    kept fe#%-5d %s%s" % (r[0], fmt(d), "   yearly cost %s -> %s" % (c[0][1], c[0][2]) if c else ""))
    for x, rec in new:
        say("    ADD          %s   <- %s (EPA %d%s)" % (fmt(x), rec["name"], rec["id"], ", " + rec["atv"] if rec["atv"] else ""))
    for rec, why in held:
        say("    held         %s, EPA %d: %s (not ruled)" % (rec["name"], rec["id"], why))
    for rec in revised:
        say("    left         %s, EPA %d: a stored line holds this record's figures before EPA revised them (item e)" % (rec["name"], rec["id"]))
    for fid, old, now in cost_left:
        say("    cost left    fe#%d keeps %s: its record carries the costs %s" % (fid, old, now))
    p = {"id": vid, "year": year, "make": make, "model": model, "verified": vid in verified, "current": cur_rows,
         "cost_updates": cost_updates, "insert": [x for x, _ in new], "sources": [[rec["name"], rec["id"]] for _, rec in new],
         "held": [[rec["name"], rec["id"], why] for rec, why in held], "revised_left": [[rec["name"], rec["id"]] for rec in revised],
         "cost_left": cost_left, "taken": sorted(taken)}
    return p


def plan_sha(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def apply(cur, plan):
    for p in plan:
        vid = p["id"]
        row = cur.execute("SELECT year, make, model FROM vehicles WHERE id=?", (vid,)).fetchone()
        if not row or tuple(row) != (p["year"], p["make"], p["model"]):
            raise RuntimeError("target %d is %r" % (vid, row and tuple(row)))
        if stored(cur, vid) != p["current"]:
            raise RuntimeError("target %d: the stored fuel-economy lines changed since the dry run" % vid)
        for fid, old, new in p["cost_updates"]:
            cur.execute("UPDATE fuel_economy SET annual_fuel_cost=? WHERE id=? AND vehicle_id=? AND annual_fuel_cost IS ?", (new, fid, vid, old))
            if cur.rowcount != 1:
                raise RuntimeError("target %d: the yearly cost of line fe#%d was not changed" % (vid, fid))
        cur.executemany("INSERT INTO fuel_economy (vehicle_id, " + COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [[vid] + list(x) for x in p["insert"]])
        if [r[1:] for r in stored(cur, vid)] != after_rows(p):
            raise RuntimeError("target %d does not hold the planned lines" % vid)


def bare_count(cur):
    return cur.execute("SELECT COUNT(*) FROM (SELECT source FROM oil_change UNION ALL SELECT source FROM parts UNION ALL "
                       "SELECT source FROM fluids UNION ALL SELECT source FROM torque_specs) "
                       "WHERE source='owner-manual-verified'").fetchone()[0]


def totals(plan):
    return sum(len(p["cost_updates"]) for p in plan), sum(len(p["insert"]) for p in plan)


def build(con):
    sys.path.insert(0, os.path.join(ROOT, "files"))
    spec = importlib.util.spec_from_file_location("kyr_build_04", os.path.join(ROOT, "files", "04_rebuild_demo.py"))
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    with contextlib.redirect_stdout(io.StringIO()):
        b._assert_registry_admission(cur)
        b.assert_frozen_landscape(cur)
        vlist, dtc, fixes, _with_comps = b.build_data(cur)
        b._strip_unverified(vlist)
        b._assert_ic01_projection(vlist)
    return {v["id"]: v for v in vlist}, dtc, fixes


def mem_copy():
    src = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def rehearse(plan):
    say("")
    say("REHEARSAL -- the real build on two in-memory copies of the database (untouched, and with the plan applied)")
    try:
        m0 = mem_copy()
        before, dtc0, fix0 = build(m0)
        m0.close()
        m1 = mem_copy()
        c1 = m1.cursor()
        n0 = c1.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        apply(c1, plan)
        m1.commit()
        ncost, inn = totals(plan)
        n1 = c1.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        if n1 != n0 + inn or bare_count(c1) != BARE_FROZEN:
            say("  REHEARSAL FAILED: row count or bare rows are off")
            return False
        after, dtc1, fix1 = build(m1)
        m1.close()
    except SystemExit as e:
        say("  REHEARSAL FAILED: the build stopped:", e)
        return False
    if sorted(before) != sorted(after) or dtc0 != dtc1 or fix0 != fix1:
        say("  REHEARSAL FAILED: the vehicle list, the code list or the fix list changed")
        return False
    want = {p["id"]: p for p in plan}
    bad = 0
    for vid, a in before.items():
        b = after[vid]
        if vid in want:
            diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            if diff != ["mpg"]:
                say("  UNEXPECTED: id %d differs in %s, expected fuel economy only" % (vid, diff))
                bad += 1
        elif a != b:
            say("  UNEXPECTED: id %d changed although the plan does not touch it" % vid)
            bad += 1
    first_same = 0
    for vid, p in want.items():
        mpg, rows = after[vid].get("mpg") or [], after_rows(p)
        if len(mpg) != len(rows) or len(before[vid].get("mpg") or []) != len(p["current"]):
            say("  UNEXPECTED: id %d ships %d lines, planned %d" % (vid, len(mpg), len(rows)))
            bad += 1
            continue
        for m, x in zip(mpg, rows):
            ok = (m.get("city"), m.get("hwy"), m.get("comb"), m.get("cost"), m.get("trans"), m.get("drive"), m.get("range"), m.get("mpge")) == (
                x[CITY], x[HWY], x[COMB], x[COST], x[TRANS], x[DRIVE], x[RANGE], x[MPGE])
            if not ok or fnum(m.get("eng")) != fnum(x[ENG]):
                say("  UNEXPECTED shipped line on id %d: %r" % (vid, m))
                bad += 1
        b0, b1 = before[vid]["mpg"][0], mpg[0]
        if {k: v for k, v in b0.items() if k != "cost"} == {k: v for k, v in b1.items() if k != "cost"}:
            first_same += 1
    if bad:
        return False
    n_ver = sum(1 for v in after.values() if isinstance(v.get("oil"), dict) and v["oil"].get("ver") == 1)
    ver = sorted(v for v in want if isinstance(before[v].get("oil"), dict) and before[v]["oil"].get("ver") == 1)
    say("  build gates passed on both copies; vehicles %d -> %d; owner's-manual-verified %d (unchanged)" % (len(before), len(after), n_ver))
    say("  %d vehicles differ, each in fuel economy only; all other %d vehicles identical" % (len(want), len(after) - len(want)))
    say("  fuel-economy rows %d -> %d (%d added; %d yearly costs changed); bare owner-manual rows %d" % (n0, n1, inn, ncost, BARE_FROZEN))
    say("  every shipped line on the changed vehicles equals a planned line; the first line shown is unchanged on %d of %d" % (first_same, len(want)))
    say("  verified vehicles among them: %d" % len(ver))
    return True


def dry_run(zip_path):
    say("FUEL-ECONOMY FILL, EVERY OWN EPA RECORD -- DRY RUN (nothing is written)  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    by_id, by_ym = load_epa(zip_path)
    say("EPA file: %d records, sha256 %s (pinned)" % (len(by_id), ZIP_SHA256))
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        if bare_count(cur) != BARE_FROZEN:
            sys.exit("bare owner-manual rows are not %d" % BARE_FROZEN)
        verified = {r[0] for r in cur.execute("SELECT vehicle_id FROM oil_change WHERE source LIKE 'owner-manual-verified%' OR source LIKE 'service-manual-verified%'")}
        plan = [plan_op(cur, op, by_id, by_ym, verified) for op in OPS]
    finally:
        con.close()
    ncost, inn = totals(plan)
    say("")
    say("SUMMARY")
    say("  rows filled: %d (verified %d); records added: %d (on verified rows %d)" % (
        len(plan), sum(p["verified"] for p in plan), inn, sum(len(p["insert"]) for p in plan if p["verified"])))
    kinds = collections.Counter(by_id[s[1]]["atv"] or "gasoline" for p in plan for s in p["sources"])
    say("  added by EPA type: %s" % ", ".join("%s %d" % (k if k != "FFV" else "flex-fuel", n) for k, n in sorted(kinds.items())))
    say("  yearly costs changed: %d; left alone (two costs on one record): %d" % (ncost, sum(len(p["cost_left"]) for p in plan)))
    hk = collections.Counter(h[2] for p in plan for h in p["held"])
    say("  held on these rows: %d (%s); revised figures left (item e): %d" % (
        sum(hk.values()), ", ".join("%s %d" % kv for kv in sorted(hk.items())), sum(len(p["revised_left"]) for p in plan)))
    say("  lines removed: 0")
    if not rehearse(plan):
        sys.exit("rehearsal failed -- no plan saved")
    sha = plan_sha(plan)
    with io.open(PLAN_FILE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"script": os.path.basename(__file__), "sha256": sha, "epa_file_sha256": ZIP_SHA256, "plan": plan}, fh, sort_keys=True, indent=1)
    say("")
    say("plan saved: %s" % PLAN_FILE)
    say("plan sha256: %s" % sha)
    say("to write exactly this plan (only on Robert's go):  python -I %s --write --sha %s" % (os.path.basename(__file__), sha))


def write():
    if "--sha" not in sys.argv:
        sys.exit("--write needs --sha <the sha256 a dry run printed>")
    want = sys.argv[sys.argv.index("--sha") + 1]
    with io.open(PLAN_FILE, encoding="utf-8") as fh:
        saved = json.load(fh)
    plan = saved["plan"]
    got = plan_sha(plan)
    if got != want or saved.get("sha256") != want or saved.get("epa_file_sha256") != ZIP_SHA256:
        sys.exit("plan file hash %s does not match --sha %s: run the dry run again and get a fresh go" % (got, want))
    if [(p["id"], p["year"]) for p in plan] != [(o["id"], o["year"]) for o in OPS]:
        sys.exit("the saved plan does not match this script's operations")
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    try:
        cur = con.cursor()
        bare, fleet, n0 = bare_count(cur), cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0], cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
    finally:
        con.close()
    if bare != BARE_FROZEN:
        sys.exit("bare owner-manual rows %d, expected %d" % (bare, BARE_FROZEN))
    bak = "%s.bak_fe_every_record_%s" % (DB, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(DB, bak)
    say("backup ->", bak)
    ncost, inn = totals(plan)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        apply(cur, plan)
        n1 = cur.execute("SELECT COUNT(*) FROM fuel_economy").fetchone()[0]
        if n1 != n0 + inn or cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] != fleet:
            raise RuntimeError("row count or fleet count is off")
        if bare_count(cur) != BARE_FROZEN:
            raise RuntimeError("bare owner-manual count moved")
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise
    con.close()
    say("WRITTEN: %d vehicles filled (%d lines added, %d yearly costs changed); fuel-economy rows %d -> %d; fleet %d; bare rows %d" % (
        len(plan), inn, ncost, n0, n1, fleet, BARE_FROZEN))


if __name__ == "__main__":
    if WRITE:
        write()
    else:
        if len(sys.argv) != 2:
            sys.exit("usage: python -I %s <path to vehicles.csv.zip>" % os.path.basename(__file__))
        try:
            dry_run(sys.argv[1])
        except PlanError as e:
            say("")
            say("STOPPED -- a check did not come back clean, so no plan was saved:")
            say("   ", e)
            sys.exit(2)
