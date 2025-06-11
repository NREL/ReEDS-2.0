'''
This makes a report of value and value factor outputs. Gen Frac is included
so that the value factors can be compared to market share. See comments in
in reeds2.py for a description of each preset.
'''
storage_techs = ['pumped-hydro','pumped-hydro-flex','battery', 'battery_2', 'battery_4', 'battery_6', 'battery_8', 'battery_10', 'battery_12', 'battery_24', 'battery_48', 'battery_72', 'battery_100']

static_presets = [
    {'name': 'Full Value New Techs', 'sheet_name':'vf_full', 'result': 'Value New Techs', 'download_full_source': True},
    {'name': 'Gen Frac', 'sheet_name':'gen_frac', 'result': 'Generation National (TWh)', 'preset': 'Stacked Bars Gen Frac', 'config':{'filter':{'tech':{'exclude':storage_techs}}}},
    {'name': 'Cap Frac', 'sheet_name':'cap_frac', 'result': 'Capacity National (GW)', 'preset': 'Stacked Bars Cap Frac'},
    {'name': 'LVOE by Year', 'sheet_name':'lvoe', 'result': 'Value New Techs', 'preset': 'LVOE by Year'},
    {'name': 'LVOE Energy by Year', 'sheet_name':'lvoe_energy', 'result': 'Value New Techs', 'preset': 'LVOE Energy by Year'},
    {'name': 'LVOE Firm Capacity by Year', 'sheet_name':'lvoe_resmarg', 'result': 'Value New Techs', 'preset': 'LVOE Firm Capacity by Year'},
    {'name': 'LVOE Operating Reserves by Year', 'sheet_name':'lvoe_opres', 'result': 'Value New Techs', 'preset': 'LVOE Operating Reserves by Year'},
    {'name': 'LVOE State RPS by Year', 'sheet_name':'lvoe_rps', 'result': 'Value New Techs', 'preset': 'LVOE State RPS by Year'},
    {'name': 'VF by Year', 'sheet_name':'vf', 'result': 'Value New Techs', 'preset': 'VF by Year'},
    {'name': 'VF Energy by Year', 'sheet_name':'vf_energy', 'result': 'Value New Techs', 'preset': 'VF Energy by Year'},
    {'name': 'VF Firm Capacity by Year', 'sheet_name':'vf_resmarg', 'result': 'Value New Techs', 'preset': 'VF Firm Capacity by Year'},
    {'name': 'VF Spatial by Year', 'sheet_name':'vf_spatial', 'result': 'Value New Techs', 'preset': 'VF Spatial by Year'},
    {'name': 'VF Temporal by Year', 'sheet_name':'vf_temporal', 'result': 'Value New Techs', 'preset': 'VF Temporal by Year'},
    {'name': 'VF Interaction by Year', 'sheet_name':'vf_interaction', 'result': 'Value New Techs', 'preset': 'VF Interaction by Year'},
    {'name': 'VF Spatial Simultaneous by Year', 'sheet_name':'vf_spatial_simult', 'result': 'Value New Techs', 'preset': 'VF Spatial Simultaneous by Year'},
    {'name': 'VF Temporal Local by Year', 'sheet_name':'vf_temporal_local', 'result': 'Value New Techs', 'preset': 'VF Temporal Local by Year'},
]
