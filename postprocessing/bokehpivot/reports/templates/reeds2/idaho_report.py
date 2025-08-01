report_bas = [
    'p14','p15','p16', 'p16009', 'p16017', 'p16021', 'p16055', 'p16057', 'p16061', 'p16069', 'p16001', 'p16003', 
    'p16013', 'p16015', 'p16023', 'p16025', 'p16027', 'p16035', 'p16037', 'p16039', 'p16045', 
    'p16047', 'p16049', 'p16053', 'p16059', 'p16063', 'p16067', 'p16073', 'p16075', 'p16079', 
    'p16085', 'p16087', 'p16005', 'p16007', 'p16011', 'p16019', 'p16029', 'p16031', 'p16033', 
    'p16041', 'p16043', 'p16051', 'p16065', 'p16071', 'p16077', 'p16081', 'p16083'
 ]
            
static_presets = [

    #Idaho, 
    {'name': 'Generation (TWh) Idaho', 'sheet_name':'gen_Idaho', 'result': 'Generation BA (TWh)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'Capacity (GW) Idaho', 'sheet_name':'cap_Idaho', 'result': 'Capacity BA (GW)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'New Annual Capacity (GW)', 'sheet_name':'cap_new_ann', 'result': 'New Annual Capacity BA (GW) [no-index]', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'Bulk System Electricity Price ($/MWh) Idaho', 'sheet_name':'elec_price_Idaho', 'result': 'Requirement Prices and Quantities BA', 'preset': 'Bulk System Electricity Price ($/MWh)', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'Present Value of System Cost through 2050 (Bil $) Idaho', 'sheet_name':'sys_cost_Idaho', 'result': 'Sys Cost Annualized BA/State (Bil $)', 'preset': 'Undiscounted by Year - BA', 'config':{'filter':{'r':report_bas}}},
    {'name': 'CO2 Emissions (metric tons) Idaho', 'sheet_name':'emissions_Idaho', 'result': 'CO2 Emissions BA (metric tons)', 'preset': 'Scenario Lines Over Time', 'config':{'filter':{'rb':report_bas}}},


]
