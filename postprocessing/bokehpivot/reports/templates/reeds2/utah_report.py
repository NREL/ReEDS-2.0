utah_bas = ['p26','p25', 'p49001', 'p49003', 'p49005', 'p49007', 'p49011', 'p49015', 'p49017', 
    'p49019', 'p49021', 'p49023', 'p49025', 'p49027', 'p49031', 'p49035', 
    'p49037', 'p49039', 'p49041', 'p49045', 'p49049', 'p49053', 'p49055', 
    'p49057', 'p49009', 'p49013', 'p49029', 'p49033', 'p49043', 'p49047', 
    'p49051']
static_presets = [

    #Utah
    {'name': 'Generation (TWh) Utah', 'sheet_name':'gen_Utah', 'result': 'Generation BA (TWh)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':utah_bas}}},
    {'name': 'Capacity (GW) Utah', 'sheet_name':'cap_Utah', 'result': 'Capacity BA (GW)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':utah_bas}}},
    {'name': 'New Annual Capacity (GW)', 'sheet_name':'cap_new_ann', 'result': 'New Annual Capacity National (GW)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':utah_bas}}},
    {'name': 'Bulk System Electricity Price ($/MWh) Utah', 'sheet_name':'elec_price_Utah', 'result': 'Requirement Prices and Quantities BA', 'preset': 'Bulk System Electricity Price ($/MWh)', 'config':{'filter':{'rb':utah_bas}}},
    {'name': 'Present Value of System Cost through 2050 (Bil $) Utah', 'sheet_name':'sys_cost_Utah', 'result': 'Sys Cost Annualized BA/State (Bil $)', 'preset': 'Undiscounted by Year - BA', 'config':{'filter':{'r':utah_bas}}},
    {'name': 'CO2 Emissions (metric tons) Utah', 'sheet_name':'emissions_Utah', 'result': 'CO2 Emissions BA (metric tons)', 'preset': 'Scenario Lines Over Time', 'config':{'filter':{'rb':utah_bas}}},


]



