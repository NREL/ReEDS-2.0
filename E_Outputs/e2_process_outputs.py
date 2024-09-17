# -*- coding: utf-8 -*-
"""
Process ReEDS model results from gams
Arrange the tables, summarize the data, and save key results in Excel format

@author Ilya Chernyakhovskiy

"""

#%%
import os
from re import S
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import sys
if os.name == 'posix':
    os.environ['GAMS_DIR'] = os.path.dirname(subprocess.check_output(['which', 'gams'])).decode()
import gdxpds
import pandas as pd
import argparse
from functools import reduce
#%%
# suppress pandas chained assignments warning
pd.options.mode.chained_assignment = None

parser = argparse.ArgumentParser(description="""Create analysis outputs for VIZIT""")

parser.add_argument("solutions_dir", help="""Directory of runs folder with solutions""", type=str)
parser.add_argument("excel", help="""Save to excel file""", type=str)
parser.add_argument("solutions", help="""List of solutions""", nargs='+', type=str)
input_args = parser.parse_args()

args = dict()
for arg in vars(input_args):
    args[arg] = getattr(input_args, arg)

cases = args['solutions'] #cases = ["ilya2_test2_Ref","ilya2_test2_LCSolar"]

#%%
if len(cases[0].split('_')) == 3:
    user = [x.split('_')[0] for x in cases][0]
    scenarios = [x.split('_')[1] + "_" + x.split('_')[2] for x in cases]
    root = args['solutions_dir']
    SAVEDIR = os.path.join(root, 'exceloutput', 'vizit')
else:
    user = ""
    scenarios = [x.split('_')[1] for x in cases]
    root = os.path.join("E_Outputs", "runs")
    SAVEDIR = os.path.join(root, "..", 'vizit_{}'.format("-".join(cases)))
    if len(SAVEDIR) > 200:
        SAVEDIR = os.path.join(root, "..", 'visit_{}'.format(datetime.now().strftime("%Y-%m-%d-%H-%M")))

Path(SAVEDIR).mkdir(parents=True, exist_ok=True)

#%%
# read the timeslice map
ts_name_map = pd.read_csv(os.path.join("A_Inputs", "inputs", "analysis", "time_slice_names_UP.csv"))
# Change the analysis_parameters.csv file for UP
#params = pd.read_csv(os.path.join('A_Inputs', 'inputs', 'analysis', 'analysis_parameters.csv'))
params = pd.read_csv(os.path.join('A_Inputs', 'inputs', 'analysis', 'analysis_parameters_UP_AQ.csv'))
tech_type_map = params[['reeds.category', 'Type']].dropna()
tech_order = params[['Gen.Order']].dropna()['Gen.Order'].to_list()
tech_order.reverse()
season_order = ['Winter', 'Spring', 'Summer', 'Rainy', 'Autumn']
time_order = ['night', 'sunrise', 'morning', 'afternoon', 'sunset', 'evening', 'peak']

latlon = params[['reeds.states','json.states','lon','lat']]

def summarize(df, value, sumby, drop=True):
    """aggregation helper function"""
    if len(df) == 0:
        df = df[sumby+[value]]
        df.loc[len(df),value] = 1
        out = df.copy()
    else:
        out = df.groupby(sumby).sum().reset_index()
    if drop:
        out = out.loc[out[value] != 0]
    return out

def setnames(df, lvl_name):
    """renaming helper function"""
    out = df.rename(columns={'Type':'Technology', 'h':'Timeslice', 'r':'State', 't':'Year', 'Level':lvl_name})
    return out

def map_rs_to_state(df, rmap):
    """maps resource regions to states/UTs"""
    out = pd.merge(df, rmap, left_on='r', right_on='rs', how='left')
    out['r_y'].loc[out['r_y'].isnull()] = out['r_x']
    out.rename(columns = {'r_y':'r'}, inplace=True)
    return out

def get_tslc_hours(df, left_on, tslc_hours):
    """maps timeslices to number of hours"""
    df = df.merge(tslc_hours, left_on=left_on, right_on='h')
    df.rename(columns={'Value':'Timeslice_hours'}, inplace=True)
    return df

def map_h_to_tsname(df, left_on):
    """maps timeslice codes to time-season names"""
    df = df.merge(ts_name_map, left_on=left_on, right_on='h')
    df[['season', 'time']] = df['time_slice'].str.split('_', expand=True)
    return df

def map_tech_to_type(df, left_on):
    """maps reeds techs to aggregated types"""
    df = df.merge(tech_type_map, left_on=left_on, right_on='reeds.category')
    return df

def sorting(df, techs=False, tslcs=False, BAs=False):
    df['scenario'] = pd.Categorical(df['scenario'], scenarios)
    if techs:
        df['Technology'] = pd.Categorical(df['Technology'], tech_order)
    if tslcs:
        df['season'] = pd.Categorical(df['season'], season_order)   
        df['time'] = pd.Categorical(df['time'], time_order)
    if BAs:
        df['State'] = pd.Categorical(df['State'], df['State'].unique().tolist().sort())
    
    if techs==False and tslcs==False and BAs==False:
        df.sort_values(['Year', 'scenario'], inplace=True)
    
    if techs and tslcs==False and BAs==False:
        df.sort_values(['Technology', 'scenario', 'Year'], inplace=True)
    
    if techs and tslcs and BAs==False:
        df.sort_values(['Technology', 'season', 'time', 'scenario', 'Year'], inplace=True)
    
    if techs and tslcs and BAs:
        df.sort_values(['Technology', 'season', 'time', 'scenario', 'Year', 'State'], inplace=True)
    
    if techs and tslcs==False and BAs:
        df.sort_values(['Technology', 'scenario', 'Year',  'State'], inplace=True)
        
    if techs==False and tslcs==False and BAs:
        df.sort_values(['Year', 'State', 'scenario'], inplace=True)

    if techs==False and tslcs and BAs:
        df.sort_values(['season', 'time', 'scenario', 'Year', 'State'], inplace=True)
    
    if techs==False and tslcs and BAs==False:
        df.sort_values(['season', 'time', 'scenario', 'Year'], inplace=True)
    
    df.reset_index(inplace=True, drop=True)
    return(df)

def get_gdxdirs(cs):
    """finds path directories for gdx outputs"""
    if user == '':
        gdxdirs = [os.path.join(root, x, "outputs", "output_{}.gdx".format(x)) for x in cs]
    else:
        gdxdirs = [os.path.join(root, "runs", x, "outputs", "output_{}.gdx".format(x)) for x in cs]
    return gdxdirs

def add_scen_col(df, scenario):
    """scenario column helper function"""
    df['scenario'] = scenario
    return df

def read_gdxs(gdxdirs, cs):
    """reads gdx results file into memory"""
    vars = ['CAP', 'INV', 'GEN', 'LOAD', 'OPRES', 'STORAGE_IN', 'CAPTRAN']
    params = ['r_rs', 'hours', 'firm_conv', 'firm_hydro', 'firm_vg', 'firm_stor', 'txinv', 'import', 'peakdem_region', 'prm_region', 'm_cf', 'm_capacity_exog']
    costs = ['capcost', 'txcapcost', 'substcost', 'vomcost', 'fomcost', 'oprescost', 'fuelcost']
    keep = vars + params + costs
    out = dict.fromkeys(keep)

    for i in range(len(gdxdirs)):
        if not os.path.exists(gdxdirs[i]):
            print("{} not found".format(gdxdirs[i]))
            exit()
        else:
            print("Reading {}".format(gdxdirs[i]))
        if user == '':
            scenario = cs[i].split('_')[1] 
        else:
            scenario = cs[i].split('_')[1] + "_" + cs[i].split('_')[2]
        dat = dict.fromkeys(keep)
        with gdxpds.gdx.GdxFile(lazy_load=False) as f:
            f.read(gdxdirs[i])
            for symbol in keep:
                dat[symbol] = f[symbol].dataframe
        dat = {k: add_scen_col(v, scenario) for k, v in dat.items()}
        for k in dat.keys():
            out[k] = pd.concat([out[k], dat[k]], axis=0)
    return out
#%%
def ProcessGdx():
    gdxdirs = get_gdxdirs(cases)

    gdxin = read_gdxs(gdxdirs, cases)

    # get mapping of resource regions to states
    rmap = gdxin['r_rs'][['r', 'rs']]
    rmap = rmap.groupby(['r', 'rs']).size().reset_index()

    # timeslice hours map
    tslc_hours = gdxin['hours']
    tslc_hours = tslc_hours.groupby(['h','Value']).size().reset_index()

    ####### Begin data queries 
    #######

    # Installed capacity
    cap = gdxin['CAP']
    cap = map_rs_to_state(cap, rmap)
    cap = map_tech_to_type(cap, 'i')
    #cap.drop(cap[cap['Type'] == 'Imports'].index, inplace=True)
    cap_rs = summarize(cap, 'Level',['Type','rs','t','scenario'])
    cap_rs = setnames(cap_rs, 'capacity_MW')
    cap_rs = cap_rs[['Technology', 'rs', 'Year', 'capacity_MW', 'scenario']]

    cap = summarize(cap, 'Level', ['Type', 'r', 't', 'scenario'])
    cap = setnames(cap, 'capacity_MW')
    cap = cap[['Technology', 'State', 'Year', 'capacity_MW', 'scenario']]

    # Capacity difference
    cap_diff = cap.pivot_table(index=['State','Technology','Year'], columns='scenario', values='capacity_MW').reset_index()
    for i in scenarios[1:]:
        cap_diff[i] = cap_diff[i].fillna(0) - cap_diff[scenarios[0]].fillna(0)
    if len(scenarios) == 1:
        cap_diff[scenarios[0]] = 0
    else:
        cap_diff.drop(scenarios[0], axis=1, inplace=True)
    cap_diff = cap_diff.set_index(['State','Technology','Year']).stack().reset_index(name='capacity_MW')

    # Capacity investments
    inv = gdxin['INV']
    inv = map_rs_to_state(inv, rmap)
    inv = map_tech_to_type(inv, 'i')
    inv = summarize(inv, 'Level', ['Type', 'r', 't', 'scenario'])
    inv = setnames(inv, 'investments_MW')
    inv = inv[['Technology', 'State', 'Year', 'investments_MW', 'scenario']]

    # Firm capacity 
    pdlist = [gdxin['firm_conv'], gdxin['firm_hydro'], gdxin['firm_vg'], gdxin['firm_stor']]
    firmcap = pd.concat(pdlist)
    firmcap.set_axis(['Region', 'Season', 'Year', 'Technology', 'firm_capacity_MW', 'scenario'], axis = 1, inplace = True)
    firmcap = map_tech_to_type(firmcap, 'Technology')
    firmcap = summarize(firmcap, 'firm_capacity_MW', ['Type', 'Region', 'Season', 'Year', 'scenario'])
    firmcap.rename(columns={'Type':'Technology'}, inplace=True)
    firmcap = firmcap.round(0)

    # Regional peak demand and PRM
    peakdem = gdxin['peakdem_region']
    prm = gdxin['prm_region']
    peakdem_prm = pd.merge(peakdem, prm, on = ['region', 't', 'scenario'], how="left")
    peakdem_prm.loc[peakdem_prm['Value_y'].isnull(), 'Value_y'] = 0 
    peakdem_prm = peakdem_prm.loc[peakdem_prm['t'].isin(firmcap['Year'].unique())]
    peakdem_prm['PRM_req'] = peakdem_prm['Value_x'] * (1+peakdem_prm['Value_y'])
    peakdem_prm.set_axis(['Region', 'Season', 'Year', 'peak_demand_MW', 'scenario', 'PRM', 'PRM_req'], axis=1, inplace=True)
    peakdem_prm = peakdem_prm.round(2)

    # Timeslice dispatch
    gen_tslc = gdxin['GEN'].copy()
    gen_tslc = map_tech_to_type(gen_tslc, 'i')

    # add import parameter
    trade = gdxin['import']
    trade = trade.loc[trade['t'].isin(gen_tslc['t'].unique())]
    trade = summarize(trade, 'Value', ['r', 'h', 't', 'scenario'])
    trade['Type'] = 'Imports'
    trade.rename(columns={'Value':'Level'}, inplace=True)
    gen_tslc = pd.concat([gen_tslc, trade])

    gen_tslc = summarize(gen_tslc, 'Level', ['Type', 'r', 'h', 't', 'scenario'])
    gen_tslc = setnames(gen_tslc, 'dispatch_MW')
    gen_tslc = get_tslc_hours(gen_tslc, 'Timeslice', tslc_hours)
    gen_tslc = gen_tslc[['Technology', 'State', 'Year', 'Timeslice', 'Timeslice_hours', 'dispatch_MW', 'scenario']]
    gen_tslc['generation_MWh'] = gen_tslc['dispatch_MW'] * gen_tslc['Timeslice_hours']

    # Annual generation
    gen = summarize(gen_tslc, 'generation_MWh', ['Technology', 'State', 'Year', 'scenario'])
    gen = gen[['Technology', 'State', 'Year', 'generation_MWh', 'scenario']]

    # Generation difference
    gen_diff = gen.pivot_table(index=['State','Technology','Year'], columns='scenario', values='generation_MWh').reset_index()
    for i in scenarios[1:]:
        gen_diff[i] = gen_diff[i].fillna(0) - gen_diff[scenarios[0]].fillna(0)
    if len(scenarios) == 1:
        gen_diff[scenarios[0]] = 0
    else:
        gen_diff.drop(scenarios[0], axis=1, inplace=True)
    gen_diff = gen_diff.set_index(['State','Technology','Year']).stack().reset_index(name='generation_MWh')

    # VRE curtailment
    gen_vre = gdxin['GEN'].loc[gdxin['GEN']['i'].isin(['WIND','UPV','DISTPV'])].drop(columns={'Marginal','Lower','Upper','Scale'})
    gen_vre = summarize(gen_vre, 'Level', ['i','r','h','t','scenario']).rename(columns={'Level':'Gen'})
    cap_vre = gdxin['CAP'].loc[gdxin['CAP']['i'].isin(['WIND','UPV','DISTPV'])].drop(columns={'Marginal','Lower','Upper','Scale'})
    cap_vre = summarize(cap_vre, 'Level', ['i','r','t','scenario'])
    cap_vre = pd.merge(gdxin['m_cf'], cap_vre, on = ['i','r','scenario'])
    cap_vre['potential'] = cap_vre['Value'] * cap_vre['Level']
    cap_vre = map_rs_to_state(cap_vre, rmap)
    cap_vre = summarize(cap_vre, 'potential', ['i','r','h','t','scenario'])
    curt = pd.merge(cap_vre, gen_vre, on = ['i', 'r', 'h', 't', 'scenario'], how = 'left')
    curt['curtailment'] = curt['potential'] - curt['Gen'].fillna(0)
    curt = map_tech_to_type(curt, 'i')
    curt = summarize(curt, ['potential','curtailment'], ['Type','h','t','scenario', 'r'], drop=False)
    curt['curt_frac'] = curt['curtailment'] / curt['potential']

    # Demand
    dem_tslc = gdxin['LOAD']
    dem_tslc = setnames(dem_tslc, 'demand_MW')
    dem_tslc = get_tslc_hours(dem_tslc, 'Timeslice', tslc_hours)
    dem_tslc = dem_tslc[['State', 'Year', 'Timeslice', 'Timeslice_hours', 'demand_MW', 'scenario']]
    dem_tslc['demand_MWh'] = dem_tslc['demand_MW'] * dem_tslc['Timeslice_hours']

    # Annual demand
    dem = summarize(dem_tslc, 'demand_MWh', ['State', 'Year', 'scenario'])
    dem = dem[['State', 'Year', 'demand_MWh', 'scenario']]

    # Timeslice operating reserves
    opres_tslc = gdxin['OPRES']
    opres_tslc = map_tech_to_type(opres_tslc, 'i')
    opres_tslc = summarize(opres_tslc, 'Level', ['Type', 'r', 'h', 't', 'scenario'])
    opres_tslc = setnames(opres_tslc, 'operating_reserves_MW')
    opres_tslc = opres_tslc[['Technology', 'State', 'Timeslice', 'Year', 'operating_reserves_MW', 'scenario']]
    opres_tslc = get_tslc_hours(opres_tslc, 'Timeslice', tslc_hours)
    opres_tslc = opres_tslc[['Technology', 'State', 'Year', 'Timeslice', 'Timeslice_hours', 'operating_reserves_MW', 'scenario']]
    opres_tslc['operating_reserves_MWh'] = opres_tslc['operating_reserves_MW'] * opres_tslc['Timeslice_hours']

    # Annual operating reserves
    opres = summarize(opres_tslc, 'operating_reserves_MWh', ['Technology', 'State', 'Year', 'scenario'])
    opres = opres[['Technology', 'State', 'Year', 'operating_reserves_MWh', 'scenario']]

    # Storage operation
    storin = gdxin['STORAGE_IN']
    storin = map_tech_to_type(storin, 'i')
    storin = summarize(storin, 'Level', ['Type', 'r', 'h', 't', 'scenario'], drop=False)
    storin = setnames(storin, 'STOR_IN_MW')

 #   storlev = summarize(gdxin['STORAGE_LEVEL'], ['i', 'r', 'h', 't', 'scenario'])
 #   storlev = setnames(storlev, 'STOR_LVL_MWh')

    storgen = gen_tslc.loc[pd.Series(gen_tslc['Technology']).str.contains('BESS|Pumped').tolist()]
    storgen.rename(columns={"dispatch_MW":"STOR_GEN_MW"}, inplace=True)

  #  storops = pd.merge(storin, storlev, on = ['Technology', 'State', 'Year', 'Timeslice', 'scenario'])
    storops = pd.merge(storin, storgen, on = ['Technology', 'State', 'Year', 'Timeslice', 'scenario'], how = 'left')
    storops = storops[['Technology', 'State', 'Year', 'Timeslice', 'STOR_IN_MW', 'STOR_GEN_MW', 'scenario']]
    storops = storops.drop(storops[(storops['STOR_IN_MW']==0) & (storops['STOR_GEN_MW'].isnull())].index)
    storops.loc[storops['STOR_GEN_MW'].isnull(), 'STOR_GEN_MW'] = 0 

    # Transmission capacity
    txcap = summarize(gdxin['CAPTRAN'], 'Level', ['r', 'rr', 't', 'scenario'])
    txcap = txcap[['r', 'rr', 't', 'Level', 'scenario']]
    txcap.set_axis(['State_from', 'State_to', 'Year', 'transmission_capacity_MW', 'scenario'], axis = 1, inplace = True)

    # Transmission investments
    txinv = gdxin['txinv'].copy()
    txinv.set_axis(['State_from', 'State_to', 'Year', 'transmission_investment_MW', 'scenario'], axis = 1, inplace = True)
    txinv['tx_inv_cumulative'] = txinv.groupby(['State_from','State_to','scenario'])['transmission_investment_MW'].cumsum()

    # Costs
    capcost, txcost, sstcost = gdxin['capcost'], gdxin['txcapcost'], gdxin['substcost']
    vmcost, fmcost, oprcost, fcost = gdxin['vomcost'], gdxin['fomcost'], gdxin['oprescost'], gdxin['fuelcost']

    capcost.set_axis(['i', 'r', 't', 'capacity', 'scenario'], axis = 1, inplace = True)
    capcost = map_rs_to_state(capcost, rmap)
    capcost = map_tech_to_type(capcost, 'i')
    # Create capcost_state
    capcost_state = summarize(capcost, 'capacity', ['t', 'scenario', 'r'])
    #
    capcost = summarize(capcost, 'capacity', ['t', 'scenario']).drop(0, axis=1)

    txcost.set_axis(['r', 'rr', 't', 'trtype', 'transmission', 'scenario'], axis = 1, inplace = True)
    # Create txcost_state
    txcost_state_1 = summarize(txcost, 'transmission', ['t', 'scenario', 'r', 'rr'])
    txcost_state_2 = txcost_state_1.copy()
    txcost_state_2['r'], txcost_state_2['rr'] = txcost_state_1['rr'], txcost_state_1['r']
    txcost_state = pd.concat([txcost_state_1, txcost_state_2], ignore_index=True)
    txcost_state = txcost_state.drop(columns=['rr'])
    txcost_state['transmission'] = txcost_state['transmission'] / 2
    #
    txcost = summarize(txcost, 'transmission', ['t', 'scenario'])

    sstcost.set_axis(['r', 't', 'substations', 'scenario'], axis = 1, inplace = True)
    # Create sscost_state
    sstcost_state = summarize(sstcost, 'substations', ['t', 'scenario', 'r'])
    #
    sstcost = summarize(sstcost, 'substations', ['t', 'scenario'])

    vmcost.set_axis(['i', 'r', 't', 'variable_O&M', 'scenario'], axis = 1, inplace = True)
    # Create vmcost_state
    vmcost_state = summarize(vmcost, 'variable_O&M', ['t', 'scenario', 'r'])
    #
    vmcost = summarize(vmcost, 'variable_O&M', ['t', 'scenario'])
    
    fmcost.set_axis(['i', 'r', 't', 'fixed_O&M', 'scenario'], axis = 1, inplace = True)
    # Create fmcost_state
    fmcost_state = fmcost.copy()
    fmcost_state.rename(columns={"r": "rs"}, inplace=True)
    r_rs_map = pd.read_csv('A_Inputs/inputs/analysis/r_rs_map_UP_vizit.csv')
    r_rs_map['rs'] = r_rs_map['rs'].astype(str)
    fmcost_state = fmcost_state.merge(r_rs_map, on='rs', how='left')    
    fmcost_state.rename(columns={"rs": "r"}, inplace=True)
    fmcost_state['r'] = fmcost_state['state']
    fmcost_state = fmcost_state.drop(columns=['state'])
    fmcost_state = summarize(fmcost_state, 'fixed_O&M', ['t', 'scenario', 'r'])
    #
    fmcost = summarize(fmcost, 'fixed_O&M', ['t', 'scenario'])

    oprcost.set_axis(['i', 'r', 't', 'operating_reserves', 'scenario'], axis = 1, inplace = True)
    # Create oprcost_state
    oprcost_state = summarize(oprcost, 'operating_reserves', ['t', 'scenario', 'r'])
    #
    oprcost = summarize(oprcost, 'operating_reserves', ['t', 'scenario'])

    fcost.set_axis(['i', 'r', 't', 'fuel', 'scenario'], axis = 1, inplace = True)
    # Create fcost_state
    fcost_state = summarize(fcost, 'fuel', ['t', 'scenario', 'r'])
    #
    fcost = summarize(fcost, 'fuel', ['t', 'scenario'])

    costs = [capcost, txcost, sstcost, vmcost, fmcost, oprcost, fcost]
    costs = reduce(lambda  left,right: pd.merge(left, right, on=['t', 'scenario'], how='outer'), costs).fillna('NA')
    costs = costs.set_index(['t','scenario']).stack().reset_index(name='Cost')
    costs = costs.loc[costs['t'] != 'NA']
    costs.loc[costs['Cost'] == 'NA','Cost'] = 0
    costs.set_axis(['Year', 'scenario', 'cost_cat', 'Cost'], axis = 1, inplace = True)
    
    # State-level cost information
    costs_state = [capcost_state, txcost_state, sstcost_state, vmcost_state, fmcost_state, oprcost_state, fcost_state]
    costs_state = reduce(lambda  left,right: pd.merge(left, right, on=['t', 'scenario', 'r'], how='outer'), costs_state).fillna('NA')
    costs_state = costs_state.set_index(['t','scenario', 'r']).stack().reset_index(name='Cost')
    costs_state = costs_state.loc[costs_state['t'] != 'NA']
    costs_state.loc[costs_state['Cost'] == 'NA','Cost'] = 0
    costs_state.set_axis(['Year', 'scenario', 'state', 'cost_cat', 'Cost'], axis = 1, inplace = True)
    costs_state = costs_state[costs_state['cost_cat'] != 0]
    #

    costs_diff = costs.copy()
    costs_diff['Cost'] = costs_diff['Cost'].astype(float)
    costs_diff = costs_diff.pivot_table(index=['cost_cat','Year'], columns='scenario', values='Cost').reset_index()
    for i in scenarios[1:]:
        costs_diff[i] = costs_diff[i].fillna(0) - costs_diff[scenarios[0]].fillna(0)
    if len(scenarios) == 1:
        costs_diff[scenarios[0]] = 0
    else:
        costs_diff.drop(scenarios[0], axis=1, inplace=True)
    costs_diff = costs_diff.set_index(['Year','cost_cat']).stack().reset_index(name='Cost')
        
    # Emissions
  #  emit = gdxin['EMIT']

    ##### Organize sheets
    # Sheet 1: Annual results - cap, inv, gen, opres, emit
    annual_out = pd.merge(cap, inv, on=['Technology', 'State', 'Year', 'scenario'], how='left')
    annual_out = annual_out.merge(gen, on=['Technology', 'State', 'Year', 'scenario'], how='left')
    annual_out = annual_out.merge(opres, on=['Technology', 'State', 'Year', 'scenario'], how='left')
    annual_out = annual_out.round(0)
    annual_out = sorting(annual_out, True, False, True)

    # Sheet 2: Seasonal firm capacity - firmcap
    firmcap = sorting(firmcap, True, False, False)

    # Sheet 3: Timeslice results - gen_tslc, opres_tslc, storops
    tslc_out = pd.merge(gen_tslc, opres_tslc, on=['Technology', 'State', 'Year', 'Timeslice', 'Timeslice_hours', 'scenario'], how = 'outer')
    tslc_out = tslc_out.merge(storops, on=['Technology', 'State', 'Year', 'Timeslice', 'scenario'], how = 'outer')
    tslc_out = map_h_to_tsname(tslc_out, 'Timeslice')
    tslc_out.drop(columns=['Timeslice', 'h', 'Timeslice_hours', 'generation_MWh'], inplace=True)
    tslc_out = tslc_out.round(0)
    tslc_out = sorting(tslc_out, True, True, True)

    # Sheet 4: Transmission results - txcap, txinv
    tx_out = pd.merge(txcap, txinv, on=['State_from', 'State_to', 'Year', 'scenario'], how='left')
    tx_out = tx_out.round(0)
    tx_out = sorting(tx_out)

    # Sheet 5: Costs
    costs = costs.round(0)
    costs = sorting(costs)
    costs_state = costs_state.round(0)
    costs_state = sorting(costs_state)
    
    # costs diff - not included in excel output
    costs_diff = costs_diff.round(0)
    costs_diff = sorting(costs_diff)

    # cap diff - not included in excel output
    cap_diff = cap_diff.round(2)
    cap_diff = sorting(cap_diff, True, False, True)

    # gen diff - not included in excel output
    gen_diff = gen_diff.round(2)
    gen_diff = sorting(gen_diff, True, False, True)     

    # demand - not included in excel output
    dem = dem.round(0)
    dem = sorting(dem, False, False, True)

    dem_tslc = map_h_to_tsname(dem_tslc, 'Timeslice')
    dem_tslc = dem_tslc.round(0)
    dem_tslc = sorting(dem_tslc, False, True, True)

    # curt - not included in excel output
    curt_tslc = map_h_to_tsname(curt, 'h')
    curt_tslc.drop(columns=['h',0], inplace=True)
    curt_tslc.rename(columns={'t':'Year','Type':'Technology', 'r': 'st', 'potential': 'Potential Generation (MW)', 'Gen': 'Generation (MW)', 'curtailment': 'Curtailment (MW)'}, inplace=True)
    curt_tslc = sorting(curt_tslc, True, True, False)

    return annual_out, firmcap, tslc_out, tx_out, dem, dem_tslc, peakdem_prm, costs, costs_diff, curt_tslc, cap_rs, cap_diff, gen_diff, costs_state
#%%

def write_outputs(dir):
    annual_out, firmcap, tslc_out, tx_out, dem, dem_tslc, peakdem_prm, costs, costs_diff, curt_tslc, cap_rs, cap_diff, gen_diff, costs_state = ProcessGdx()

    #timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    #outdir = os.path.join(dir, tag)
    #Path(outdir).mkdir(parents=True, exist_ok=True)
    csvsdir = os.path.join(dir)
    Path(csvsdir).mkdir(parents=True, exist_ok=True)
   # Path(os.path.join(csvsdir,'BAs')).mkdir(parents=True, exist_ok=True)

    #%%
    ######## EXPORT TO EXCEL
    # separate sheet for each table
    if args['excel'] == 'T':
        writer = pd.ExcelWriter(os.path.join(os.getcwd(), dir,"..","outputs_{}.xlsx".format("-".join(cases))))

        annual_out.to_excel(writer, sheet_name="Annual results", index=False)
        firmcap.to_excel(writer, sheet_name="Seasonal firm capacity", index=False)
        tslc_out.to_excel(writer, sheet_name="Timeslice results", index=False)
        tx_out.to_excel(writer, sheet_name='Transmission results', index=False)
        costs.to_excel(writer, sheet_name='Costs', index=False)

        writer.save()
        print("Results saved to " + os.path.join(dir,"..","outputs_{}.xlsx".format("-".join(cases))))

    ######## WRITE OUTPUTS FOR VIZIT
    
    # cap.csv
    cap = annual_out[['State', 'scenario', 'Technology', 'Year', 'capacity_MW']]
    # Remove "Imports" from the "cap" data frame
    cap = cap[cap['Technology'] != 'Imports']
    cap.set_axis(['st', 'scenario', 'tech', 'year', 'Capacity (MW)'], axis=1, inplace=True)
    cap = pd.merge(cap, latlon[['reeds.states','json.states']], left_on='st', right_on='reeds.states', how='left').drop('reeds.states',axis=1)
    cap.to_csv(os.path.join(csvsdir, 'cap.csv'), index=False)

    # cap_new_ann.csv
    cap_new = annual_out[['State', 'scenario', 'Technology', 'Year', 'investments_MW']]
    # Remove "Imports" from the "cap_new" data frame
    cap_new = cap_new[cap_new['Technology'] != 'Imports']
    cap_new.set_axis(['st', 'scenario', 'tech', 'year', 'Investments (MW)'], axis=1, inplace=True)

    #### Code to add Hydro and Pumped hydro from cap to cap_new #### 
    # Define the conditions for updating cap_new
    conditions = (cap_new['tech'].isin(['Hydro', 'Pumped hydro'])) & \
                (cap_new['Investments (MW)'].isnull())
    # Create a temporary DataFrame with relevant columns from cap
    temp_df = cap[['st', 'scenario', 'tech', 'year', 'Capacity (MW)']]
    # Merge the temporary DataFrame with cap_new based on the matching columns
    cap_new = cap_new.merge(temp_df, on=['st', 'scenario', 'tech', 'year'], how='left')
    # Reset the index values for both cap_new and conditions
    cap_new.reset_index(drop=True, inplace=True)
    conditions.reset_index(drop=True, inplace=True)
    # Update the Investments (MW) column in cap_new with non-null values from cap
    cap_new.loc[conditions, 'Investments (MW)'] = cap_new.loc[conditions, 'Capacity (MW)']
    # Sort the DataFrame by 'st', 'scenario', 'tech', and 'year' columns
    cap_new.sort_values(by=['st', 'scenario', 'tech', 'year'], inplace=True)
    # Define the conditions for rows where "tech" is "Hydro" or "Pumped hydro" and the year is within 2021-2050
    cap_new['year'] = cap_new['year'].astype(int)
    conditions1 = (cap_new['tech'].isin(['Hydro', 'Pumped hydro'])) & (cap_new['year'].between(2020, 2050))
    conditions2 = (cap_new['tech'].isin(['Hydro', 'Pumped hydro'])) & (cap_new['year'].between(2021, 2050))
    # Initialize a new column for differences
    cap_new['Difference in Capacity (MW)'] = 0 
    # Calculate the differences based on conditions
    cap_new['Difference in Capacity (MW)'] = cap_new.loc[conditions1, 'Investments (MW)'] - cap_new.loc[conditions1, 'Investments (MW)'].shift()
    # Replace the original 'Investments (MW)' column with the calculated differences
    cap_new['Investments (MW)'] = cap_new['Difference in Capacity (MW)'].where(conditions2, cap_new['Investments (MW)'])
    # Replace any negative values in the 'Investments (MW)' column with zeroes
    cap_new['Investments (MW)'] = cap_new['Investments (MW)'].apply(lambda x: max(0, x))
    # Fix the issue for Uttarakhand in 2023 for Pumped Hydro
    # Define the conditions for the rows to update
    conditions3 = (cap_new['st'] == 'Uttarakhand') & (cap_new['year'] == 2023) & (cap_new['tech'] == 'Pumped hydro')
    # Update the "Investments (MW)" column with values from the "Capacity (MW)" column
    cap_new.loc[conditions3, 'Investments (MW)'] = cap_new.loc[conditions, 'Capacity (MW)']
    # Drop the 'Difference' column
    cap_new.drop('Difference in Capacity (MW)', axis=1, inplace=True)
    # Drop the temporary 'Capacity (MW)' column from cap_new
    cap_new.drop('Capacity (MW)', axis=1, inplace=True)
    ## Manually fix the input for UP_Varanasi, Pumped hydro, 2024 (only for scenario = "UPRefPSH...")
    conditions = (
        (cap_new['scenario'].str.contains('UPRefPSH')) &
        (cap_new['st'] == 'UP_Varanasi') &
        (cap_new['tech'] == 'Pumped hydro') &
        (cap_new['year'] == 2024)
    )
    cap_new.loc[conditions, 'Investments (MW)'] = 3660
    ##
    ############################################################################
    cap_new.to_csv(os.path.join(csvsdir, 'cap_new_ann.csv'), index=False)

    # cap_rs.csv
    cap_rs.set_axis(['tech','rs','year','capacity_MW', 'scenario'], axis=1, inplace=True)
    cap_rs.to_csv(os.path.join(csvsdir, 'cap_rs.csv'), index=False)

    # cap_diff.csv
    # Remove "Imports" from the "cap_diff" data frame
    cap_diff = cap_diff[cap_diff['Technology'] != 'Imports']
    cap_diff.set_axis(['st','tech','year','scenario','Difference (MW)'], axis=1, inplace=True)
    cap_diff.to_csv(os.path.join(csvsdir, 'cap_diff.csv'), index=False)

    # gen.csv
    gen = annual_out[['State', 'scenario', 'Technology', 'Year', 'generation_MWh']]
    gen['Technology'] = gen['Technology'].replace('Imports', 'Imports (Nepal & Bhutan)')
    gen.set_axis(['st', 'scenario', 'tech', 'year', 'Generation (MWh)'], axis=1, inplace=True)
    gen.to_csv(os.path.join(csvsdir, 'gen.csv'), index=False)

    # gen_diff.csv
    gen_diff.set_axis(['st','tech','year','scenario','Difference (MWh)'], axis=1, inplace=True)
    gen_diff['tech'] = gen_diff['tech'].replace('Imports', 'Imports (Nepal & Bhutan)')
    gen_diff.to_csv(os.path.join(csvsdir, 'gen_diff.csv'), index=False)

    # gen_timeslice_BA.csv
    gen_tslc_BA = tslc_out[['State', 'scenario', 'Technology', 'Year', 'time_slice', 'season', 'time', 'dispatch_MW']]
    gen_tslc_BA['Technology'] = gen_tslc_BA['Technology'].replace('Imports', 'Imports (Nepal & Bhutan)')
        
    # gen_timeslice.csv
    gen_tslc = summarize(gen_tslc_BA, 'dispatch_MW', ['scenario', 'Technology', 'Year', 'time_slice', 'season', 'time'])

    # add storage charging to gen
    stor_charge_BA = tslc_out[['State', 'scenario', 'Technology', 'Year', 'time_slice', 'season', 'time', 'STOR_IN_MW']]
    stor_charge = summarize(stor_charge_BA, 'STOR_IN_MW', ['scenario', 'Technology', 'Year', 'time_slice', 'season', 'time'])    
    stor_charge['dispatch_MW'] = stor_charge['STOR_IN_MW'] * -1
    stor_charge.drop('STOR_IN_MW', axis=1, inplace=True)

    gen_tslc = pd.concat([gen_tslc, stor_charge])
    gen_tslc = sorting(gen_tslc, True, True, False)
    gen_tslc['Technology'] = gen_tslc['Technology'].astype(str)
    gen_tslc['Technology'] = gen_tslc['Technology'].replace('nan', 'Imports (Nepal & Bhutan)')
    gen_tslc['time'] = gen_tslc['time'].astype(str)
    gen_tslc['time'] = gen_tslc['time'].replace('peak', 'national peak')
    gen_tslc.set_axis(['scenario', 'tech', 'year', 'timeslice', 'season', 'time', 'Generation (MW)'], axis=1, inplace=True)
    gen_tslc.to_csv(os.path.join(csvsdir, 'gen_timeslice.csv'), index=False)
    
    stor_charge_BA['dispatch_MW'] = stor_charge_BA['STOR_IN_MW'] * -1
    stor_charge_BA.drop('STOR_IN_MW', axis=1, inplace=True)
    gen_tslc_BA = pd.concat([gen_tslc_BA, stor_charge_BA])
    gen_tslc_BA = gen_tslc_BA.loc[gen_tslc_BA['dispatch_MW'].notnull()]
    gen_tslc_BA['time'] = gen_tslc_BA['time'].astype(str)
    gen_tslc_BA['time'] = gen_tslc_BA['time'].replace('peak', 'national peak')
    gen_tslc_BA.set_axis(['st', 'scenario', 'tech', 'year', 'timeslice', 'season', 'time', 'Generation (MW)'], axis=1, inplace=True)
    gen_tslc_BA.to_csv(os.path.join(csvsdir, 'gen_timeslice_BA.csv'), index=False)

    # curt_timeslice.csv
    curt_tslc.rename(columns={'Year':'year'}, inplace=True)
    curt_tslc['time'] = curt_tslc['time'].astype(str)
    curt_tslc['time'] = curt_tslc['time'].replace('peak', 'national peak')
    curt_tslc['tech'] = 'Curtailment'
    curt_tslc['Curtailment (MWh)'] = curt_tslc['hours'] * curt_tslc['Curtailment (MW)']
    curt_tslc.to_csv(os.path.join(csvsdir, 'curt_timeslice.csv'), index=False)

    # curt_frac.csv
    curt_tslc['Technology'] = curt_tslc['Technology'].astype('object')
    curt_frac = summarize(curt_tslc, ['Potential Generation (MW)','Curtailment (MW)', 'Curtailment (MWh)'], ['Technology','year', 'st', 'scenario'], drop=False)
    curt_frac.rename(columns={'Technology':'tech'}, inplace=True)
    curt_frac['curt_frac'] = curt_frac['Curtailment (MW)'] / curt_frac['Potential Generation (MW)']
    curt_frac['tech'] = 'Curtailment'
    curt_frac.to_csv(os.path.join(csvsdir,'curt_frac.csv'), index=False)

    # curt_diff.csv
    curt_diff = curt_frac.pivot_table(index=['st','tech','year'], columns='scenario', values='Curtailment (MWh)').reset_index()
    for i in scenarios[1:]:
        curt_diff[i] = curt_diff[i].fillna(0) - curt_diff[scenarios[0]].fillna(0)
    if len(scenarios) == 1:
        curt_diff[scenarios[0]] = 0
    else:
        curt_diff.drop(scenarios[0], axis=1, inplace=True)
    curt_diff = curt_diff.set_index(['st','tech','year']).stack().reset_index(name='Difference (MWh)')
    curt_diff.to_csv(os.path.join(csvsdir,'curt_diff.csv'), index=False)

    #%%
    # demand.csv
    dem = dem[['State', 'scenario', 'Year', 'demand_MWh']]
    dem['type'] = 'Demand'
    dem.set_axis(['st', 'scenario', 'year', 'Demand (MWh)', 'type'], axis=1, inplace=True)
    dem.to_csv(os.path.join(csvsdir, 'demand.csv'), index=False)

    # demand_timeslice_BA.csv
    dem_tslc_BA = dem_tslc[['State', 'scenario', 'Year', 'time_slice', 'season', 'time', 'demand_MW']]
    dem_tslc_BA['type'] = 'Demand'
    
    # demand_timeslice.csv
    dem_tslc = summarize(dem_tslc_BA, 'demand_MW', ['scenario', 'Year', 'time_slice', 'season', 'time', 'type'])
    dem_tslc = sorting(dem_tslc, False, True, False)
    dem_tslc['time'] = dem_tslc['time'].astype(str)
    dem_tslc['time'] = dem_tslc['time'].replace('peak', 'national peak')
    dem_tslc.set_axis(['scenario', 'year', 'timeslice', 'season', 'time', 'type', 'Demand (MW)'], axis=1, inplace=True)
    dem_tslc.to_csv(os.path.join(csvsdir, 'demand_timeslice.csv'), index=False)

    dem_tslc_BA['time'] = dem_tslc_BA['time'].astype(str)
    dem_tslc_BA['time'] = dem_tslc_BA['time'].replace('peak', 'national peak')
    dem_tslc_BA.set_axis(['st', 'scenario', 'year', 'timeslice', 'season', 'time', 'Demand (MW)', 'type'], axis=1, inplace=True)
    dem_tslc_BA.to_csv(os.path.join(csvsdir, 'demand_timeslice_BA.csv'), index=False)

    # transmission.csv
    tx_out = pd.merge(tx_out, latlon, left_on=['State_from'], right_on='reeds.states')
    tx_out.rename(columns={'lon':'lon_from','lat':'lat_from','json.states':'map_from'}, inplace=True)
    tx_out = pd.merge(tx_out, latlon, left_on=['State_to'], right_on='reeds.states')
    tx_out.rename(columns={'lon':'lon_to','lat':'lat_to','json.states':'map_to','Year':'year'}, inplace=True)
    tx_out.drop(['reeds.states_x','reeds.states_y'], axis=1, inplace=True)
    tx_out.to_csv(os.path.join(csvsdir, 'transmission.csv'), index=False)

    # opres.csv
    opres = annual_out[['State', 'scenario', 'Technology', 'Year', 'operating_reserves_MWh']]
    # Remove "Imports" from the "opres" data frame
    opres = opres[opres['Technology'] != 'Imports']
    opres.set_axis(['st', 'scenario', 'tech', 'year', 'Operating Reserves (MWh)'], axis=1, inplace=True)
    opres.to_csv(os.path.join(csvsdir, 'opres.csv'), index=False)

    # firmcap.csv
    firmcap.set_axis(['tech', 'region', 'season', 'year', 'scenario', 'Firm Capacity (MW)'], axis=1, inplace=True)
    firmcap['tech'] = pd.Categorical(firmcap['tech'], tech_order)
    firmcap['season'] = pd.Categorical(firmcap['season'], season_order)
    firmcap['scenario'] = pd.Categorical(firmcap['scenario'], scenarios)
    firmcap.sort_values(['tech', 'season', 'region', 'year', 'scenario'], inplace=True) 
    firmcap.to_csv(os.path.join(csvsdir, 'firmcap.csv'), index=False)

    # peak_demand.csv
    peakdem_prm.set_axis(['region', 'season', 'year', 'Peak Demand (MW)', 'scenario', 'PRM (%)', 'PRM requirement (MW)'], axis=1, inplace=True)
    peakdem_prm['type'] = 'PRM'
    peakdem_prm['season'] = pd.Categorical(peakdem_prm['season'], season_order)
    peakdem_prm['scenario'] = pd.Categorical(peakdem_prm['scenario'], scenarios)
    peakdem_prm.sort_values(['season', 'region', 'year', 'scenario'], inplace=True) 
    peakdem_prm.to_csv(os.path.join(csvsdir, 'peakdem.csv'), index=False)

    # costs.csv
    costs.set_axis(['year', 'scenario', 'cost_cat', 'Cost'], axis = 1, inplace = True)
    costs.to_csv(os.path.join(csvsdir, 'costs.csv'), index=False)

    # costs_state.csv
    costs_state.set_axis(['year', 'scenario', 'state', 'cost_cat', 'Cost'], axis = 1, inplace = True)
    costs_state.to_csv(os.path.join(csvsdir, 'costs_state.csv'), index=False)

    # costs_diff.csv
    costs_diff.set_axis(['year', 'cost_cat', 'scenario', 'Cost'], axis = 1, inplace = True)
    costs_diff.to_csv(os.path.join(csvsdir, 'costs_diff.csv'), index=False)

    # percent non-fossil cap and gen
    pnf = pd.merge(cap, gen, on = ['st', 'scenario', 'tech', 'year'])
    pnf.loc[pnf['tech'].isin(params['NonFossil']), 'type'] = 'non-fossil'
    pnf.loc[~((pnf['tech'].isin(params['NonFossil'])) | (pnf['tech'].str.contains('BESS|Pumped'))), 'type'] = 'fossil'
    pnf = pnf.groupby(['scenario', 'year', 'type'])[['Capacity (MW)', 'Generation (MWh)']].sum().reset_index()
    pnf['cap_frac'] = pnf['Capacity (MW)'] / pnf.groupby(['scenario', 'year'])['Capacity (MW)'].transform('sum')
    pnf['gen_frac'] = pnf['Generation (MWh)'] / pnf.groupby(['scenario', 'year'])['Generation (MWh)'].transform('sum')
    pnf.to_csv(os.path.join(csvsdir, 'pnf.csv'), index = False)

    # copy visit.html and report.json into the directory
    if user != "":
        shutil.copyfile('vizit.html', os.path.join(csvsdir, "..", 'vizit.html'))
    shutil.copyfile('vizit-config_UP.json', os.path.join(csvsdir, 'vizit-config_UP.json'))
    shutil.copyfile('style.csv', os.path.join(csvsdir, 'style.csv'))

write_outputs(SAVEDIR)
print('Done writing files for VIZIT')