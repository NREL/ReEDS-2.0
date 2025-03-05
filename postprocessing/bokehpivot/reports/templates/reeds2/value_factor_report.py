'''
This makes a report of value and value factor outputs. Gen Frac is included
so that the value factors can be compared to market share. See comments in
in reeds2.py for a description of each preset.
'''
storage_techs = ['pumped-hydro','pumped-hydro-flex','battery', 'battery_2', 'battery_4', 'battery_6', 'battery_8', 'battery_10', 'battery_12', 'battery_24', 'battery_48', 'battery_72', 'battery_100']

static_presets = [
    {'name': 'Full Value New Techs', 'result': 'Value New Techs', 'download_full_source': True},
    {'name': 'VF by Year', 'result': 'Value New Techs', 'preset': 'VF by Year'},
    {'name': 'VF by Year Explode Scenario', 'result': 'Value New Techs', 'preset': 'VF by Year Explode Scenario'},
    {'name': 'VF Energy by Year', 'result': 'Value New Techs', 'preset': 'VF Energy by Year'},
    {'name': 'VF Firm Capacity by Year', 'result': 'Value New Techs', 'preset': 'VF Firm Capacity by Year'},
    {'name': 'VF No RPS by Year', 'result': 'Value New Techs', 'preset': 'VF No RPS by Year'},
    {'name': 'Gen Frac', 'result': 'Generation National (TWh)', 'preset': 'Stacked Bars Gen Frac', 'config':{'filter':{'tech':{'exclude':storage_techs}}}},
    {'name': 'Cap Frac', 'result': 'Capacity National (GW)', 'preset': 'Stacked Bars Cap Frac'},
]
