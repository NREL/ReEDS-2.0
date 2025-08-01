report_bas = [
    'p21','p22', 'p23', 'p24','p56003', 'p56013', 'p56017', 'p56023', 'p56029', 'p56035', 'p56037', 'p56039', 
    'p56041', 'p56043', 'p56019', 'p56033', 'p56005', 'p56011', 'p56045', 'p56001', 
    'p56007', 'p56009', 'p56015', 'p56021', 'p56025', 'p56027', 'p56031' ]
            
static_presets = [

    # Wyoming
    {'name': 'Generation (TWh) Wyoming', 'sheet_name':'gen_Wyoming', 'result': 'Generation BA (TWh)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'Capacity (GW) Wyoming', 'sheet_name':'cap_Wyoming', 'result': 'Capacity BA (GW)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'New Annual Capacity (GW)', 'sheet_name':'cap_new_ann', 'result': 'New Annual Capacity BA (GW) [no-index]', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'Bulk System Electricity Price ($/MWh) Wyoming', 'sheet_name':'elec_price_Wyoming', 'result': 'Requirement Prices and Quantities BA', 'preset': 'Bulk System Electricity Price ($/MWh)', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'Present Value of System Cost through 2050 (Bil $) Wyoming', 'sheet_name':'sys_cost_Wyoming', 'result': 'Sys Cost Annualized BA/State (Bil $)', 'preset': 'Undiscounted by Year - BA', 'config':{'filter':{'r':report_bas}}},
    {'name': 'CO2 Emissions (metric tons) Wyoming', 'sheet_name':'emissions_Wyoming', 'result': 'CO2 Emissions BA (metric tons)', 'preset': 'Scenario Lines Over Time', 'config':{'filter':{'rb':report_bas}}},


]
