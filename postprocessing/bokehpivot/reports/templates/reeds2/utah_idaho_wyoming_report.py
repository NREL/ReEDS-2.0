report_bas = ['p26','p25', 'p49001', 'p49003', 'p49005', 'p49007', 'p49011', 'p49015', 'p49017', 
    'p49019', 'p49021', 'p49023', 'p49025', 'p49027', 'p49031', 'p49035', 
    'p49037', 'p49039', 'p49041', 'p49045', 'p49049', 'p49053', 'p49055', 
    'p49057', 'p49009', 'p49013', 'p49029', 'p49033', 'p49043', 'p49047', 
    'p49051'
    'p14','p15','p16', 'p16009', 'p16017', 'p16021', 'p16055', 'p16057', 'p16061', 'p16069', 'p16001', 'p16003', 
    'p16013', 'p16015', 'p16023', 'p16025', 'p16027', 'p16035', 'p16037', 'p16039', 'p16045', 
    'p16047', 'p16049', 'p16053', 'p16059', 'p16063', 'p16067', 'p16073', 'p16075', 'p16079', 
    'p16085', 'p16087', 'p16005', 'p16007', 'p16011', 'p16019', 'p16029', 'p16031', 'p16033', 
    'p16041', 'p16043', 'p16051', 'p16065', 'p16071', 'p16077', 'p16081', 'p16083'
    'p21','p22', 'p23', 'p24','p56003', 'p56013', 'p56017', 'p56023', 'p56029', 'p56035', 'p56037', 'p56039', 
    'p56041', 'p56043', 'p56019', 'p56033', 'p56005', 'p56011', 'p56045', 'p56001', 
    'p56007', 'p56009', 'p56015', 'p56021', 'p56025', 'p56027', 'p56031' ]
            
static_presets = [

    #UT_ID_WY
    {'name': 'Generation (TWh) UT_ID_WY', 'sheet_name':'gen_UT_ID_WY', 'result': 'Generation BA (TWh)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'Capacity (GW) UT_ID_WY', 'sheet_name':'cap_UT_ID_WY', 'result': 'Capacity BA (GW)', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'New Annual Capacity (GW)', 'sheet_name':'cap_new_ann', 'result': 'New Annual Capacity BA (GW) [no-index]', 'preset': 'Stacked Bars', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'Bulk System Electricity Price ($/MWh) UT_ID_WY', 'sheet_name':'elec_price_UT_ID_WY', 'result': 'Requirement Prices and Quantities BA', 'preset': 'Bulk System Electricity Price ($/MWh)', 'config':{'filter':{'rb':report_bas}}},
    {'name': 'Present Value of System Cost through 2050 (Bil $) UT_ID_WY', 'sheet_name':'sys_cost_UT_ID_WY', 'result': 'Sys Cost Annualized BA/State (Bil $)', 'preset': 'Undiscounted by Year - BA', 'config':{'filter':{'r':report_bas}}},
    {'name': 'CO2 Emissions (metric tons) UT_ID_WY', 'sheet_name':'emissions_UT_ID_WY', 'result': 'CO2 Emissions BA (metric tons)', 'preset': 'Scenario Lines Over Time', 'config':{'filter':{'rb':report_bas}}},


]
