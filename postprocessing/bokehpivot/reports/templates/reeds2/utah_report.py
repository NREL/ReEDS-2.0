utah_bas = ['p26','p25']
static_presets = [
    #Full
    {'name': 'Generation (TWh)', 'sheet_name':'gen', 'result': 'Generation National (TWh)', 'preset': 'Stacked Bars'},
    {'name': 'Capacity (GW)', 'sheet_name':'cap', 'result': 'Capacity National (GW)', 'preset': 'Stacked Bars'},
    {'name': 'New Annual Capacity (GW)', 'sheet_name':'cap_new_ann', 'result': 'New Annual Capacity National (GW)', 'preset': 'Stacked Bars'},
    {'name': 'Annual Retirements (GW)', 'sheet_name':'retire_ann', 'result': 'Annual Retirements National (GW)', 'preset': 'Stacked Bars'},
    {'name': 'Final Gen by timeslice (GW)', 'sheet_name':'gen_final_timeslice', 'result': 'Gen by timeslice national (GW)', 'preset': 'Stacked Bars Final'},
    {'name': 'Bulk System Electricity Price ($/MWh)', 'sheet_name':'elec_price', 'result': 'Requirement Prices and Quantities National', 'preset': 'Bulk System Electricity Price ($/MWh)'},
    {'name': 'Present Value of System Cost through 2050 (Bil $)', 'sheet_name':'sys_cost', 'result': 'Sys Cost Annualized (Bil $)', 'preset': 'Undiscounted by Year'},
    {'name': 'Emissions National (metric tons)', 'sheet_name':'emissions', 'result': 'Emissions National (metric tons)', 'preset': 'Scenario Lines Over Time'},
    {'name': 'Runtime (hours)', 'sheet_name':'runtime', 'result': 'Runtime', 'preset': 'Stacked Bars'},

    #Utah
    {'name': 'Generation (TWh) SoCo', 'sheet_name':'gen_soco', 'result': 'Generation BA (TWh)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':utah_bas}}},
    {'name': 'Capacity (GW) SoCo', 'sheet_name':'cap_soco', 'result': 'Capacity BA (GW)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':utah_bas}}},
    {'name': 'New Annual Capacity (GW)', 'sheet_name':'cap_new_ann', 'result': 'New Annual Capacity National (GW)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':utah_bas}}},
    {'name': 'Bulk System Electricity Price ($/MWh) SoCo', 'sheet_name':'elec_price_soco', 'result': 'Requirement Prices and Quantities BA', 'preset': 'Bulk System Electricity Price ($/MWh)', 'config':{'filter':{'rb':utah_bas}}},
    {'name': 'Present Value of System Cost through 2050 (Bil $) SoCo', 'sheet_name':'sys_cost_soco', 'result': 'Sys Cost Annualized BA/State (Bil $)', 'preset': 'Undiscounted by Year - BA', 'config':{'filter':{'r':utah_bas}}},
    {'name': 'CO2 Emissions (metric tons) SoCo', 'sheet_name':'emissions_soco', 'result': 'CO2 Emissions BA (metric tons)', 'preset': 'Scenario Lines Over Time', 'config':{'filter':{'rb':utah_bas}}},


]