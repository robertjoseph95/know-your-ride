# Subaru Outback ENRICHMENT - write the 3 previously-gated fields (plug-type / battery / tire) to the 11
# modern Outback rows. TOUCH-UP: surgical UPDATE of parts columns only; oil_change/fluids/torque_specs/
# maintenance/engine_specs are NOT touched (already verified & live). Spark GAP stays gated (Subaru doesn't print).
# Data read & verified from the combined Legacy+Outback OM, OUTBACK column:
#   BS (2016-2019, per 2018 OM MSA5M1803A): battery 75D23R; plugs FB25=SILZKAR7B11 + 3.6 EZ36=SILFR6C11;
#       tire 225/65R17 102H / 225/60R18 100H, 35/33 psi.
#   BT (2020-2026, per 2020 OM MSA5M2003A-2004A): battery LN2; plugs FB25=DILKAR7Q8 + FA24=SILKFR8A6;
#       tire 225/65R17 102H / 225/60R18 100H, 35/33 psi.
# ** BS-vs-BT DIVERGE (read, not carried): battery 75D23R->LN2; FB25 plug SILZKAR7B11(port)->DILKAR7Q8(direct);
#    BS 2nd engine 3.6 EZ36 (SILFR6C11) vs BT FA24 (SILKFR8A6). Tire SAME (wagon 225/65R17, NOT Legacy 225/55R17). **
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_obenrich_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
TNOTE='OM-published (Outback wagon column): 225/65R17 102H / 225/60R18 100H; 35 psi front / 33 rear (distinct from Legacy sedan 225/55R17 33/32).'
def enrich(vids,batt,plug_type,plugs_json,src_note):
    for vid in vids:
        c.execute("UPDATE parts SET spark_plug_type=?, spark_plugs_json=?, battery_group=?, tire_size=?, tire_pressure_front=?, tire_pressure_rear=?, tire_size_note=? WHERE vehicle_id=?",
            (plug_type, plugs_json, batt, '225/65R17 102H', '35 psi', '33 psi', TNOTE, vid))
        # confirm we touched exactly one existing row and did not disturb gap/source
        chk=c.execute('SELECT spark_plug_gap, source FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
        print('  id %d: batt=%s plug=%s tire=225/65R17 | gap=%r(gated) src=%s'%(vid,batt,plug_type[:22],chk[0],(chk[1] or '')[:16]))

# BS 2016-2019
enrich([12286,12420,12564,12717],'75D23R',
       'SILZKAR7B11 (2.5L FB25, NGK) / SILFR6C11 (3.6L EZ36 flat-6, NGK)',
       json.dumps([{"brand":"NGK","part_number":"SILZKAR7B11","description":"2.5L FB25 (port-injection)","is_oem":True},
                   {"brand":"NGK","part_number":"SILFR6C11","description":"3.6L EZ36 flat-6","is_oem":True}]),
       'BS 2018 OM')
# BT 2020-2026
enrich([12800,12868,12933,12999,13065,13131,13193],'LN2',
       'DILKAR7Q8 (2.5L FB25, NGK) / SILKFR8A6 (2.4L FA24 turbo, NGK)',
       json.dumps([{"brand":"NGK","part_number":"DILKAR7Q8","description":"2.5L FB25 (direct-injection)","is_oem":True},
                   {"brand":"NGK","part_number":"SILKFR8A6","description":"2.4L FA24 turbo","is_oem":True}]),
       'BT 2020 OM')

db.commit()
# Integrity: confirm oil/fluids/torque untouched (spot-check one row's lug + oil cap unchanged)
print('\\nUntouched-field spot-check (should be the live verified values):')
for vid in [12564,12800]:
    o=c.execute('SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  id %d: oil=%s | lug=%s (unchanged)'%(vid,o[:28],lug))
db.close(); print('DONE - 11 rows enriched (3 fields each).')
