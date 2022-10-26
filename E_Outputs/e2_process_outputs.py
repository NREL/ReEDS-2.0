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
#%%
# suppress pandas chained assignments warning
pd.options.mode.chained_assignment = None

tag = sys.argv[1] #tag = "ilya2_test2"
cases = list(sys.argv[2:]) #cases = ["ilya2_test2_Ref","ilya2_test2_LCSolar"]

#%%
scenarios = [x.split('_')[1] + "_" + x.split('_')[2] for x in cases]
user = [x.split('_')[0] for x in cases][0]
root = os.path.join("reeds_server", "users_output", user)
SAVEDIR = os.path.join(root, tag, 'exceloutput')
Path(SAVEDIR).mkdir(parents=True, exist_ok=True)

#%%
# read the timeslice map
ts_name_map = pd.read_csv(os.path.join("A_Inputs", "inputs", "analysis", "time_slice_names.csv"))
params = pd.read_csv(os.path.join('A_Inputs', 'inputs', 'analysis', 'analysis_parameters.csv'))
tech_type_map = params[['reeds.category', 'Type']].dropna()
tech_order = params[['Gen.Order']].dropna()['Gen.Order'].to_list()
tech_order.reverse()
season_order = ['Winter', 'Spring', 'Summer', 'Rainy', 'Autumn']
time_order = ['night', 'sunrise', 'morning', 'afternoon', 'sunset', 'evening', 'peak']

def summarize(df, value, sumby, drop=True):
    """aggregation helper function"""
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
    gdxdirs = [os.path.join(root, x.split('_')[0] + '_' + x.split('_')[1], "runs", x, "outputs", "output_{}.gdx".format(x)) for x in cs]
    return gdxdirs

def add_scen_col(df, scenario):
    """scenario column helper function"""
    df['scenario'] = scenario
    return df

def read_gdxs(gdxdirs, cs):
    """reads gdx results file into memory"""
    vars = ['CAP', 'INV', 'GEN', 'LOAD', 'OPRES', 'STORAGE_IN', 'CAPTRAN']
    params = ['r_rs', 'hours', 'firm_conv', 'firm_hydro', 'firm_vg', 'firm_stor', 'txinv', 'import', 'peakdem_region', 'prm_region']
    keep = vars + params
    out = dict.fromkeys(keep)

    for i in range(len(gdxdirs)):
        if not os.path.exists(gdxdirs[i]):
            print("{} not found".format(gdxdirs[i]))
            exit()
        else:
            print("Reading {}".format(gdxdirs[i]))
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
def ProcessingGdx():
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
    cap = summarize(cap, 'Level', ['Type', 'r', 't', 'scenario'])
    cap = setnames(cap, 'capacity_MW')
    cap = cap[['Technology', 'State', 'Year', 'capacity_MW', 'scenario']]

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

    # region peak demand and PRM
    peakdem = gdxin['peakdem_region']
    prm = gdxin['prm_region']
    peakdem_prm = pd.merge(peakdem, prm, on = ['region', 't', 'scenario'], how="left")
    peakdem_prm.loc[peakdem_prm['Value_y'].isnull(), 'Value_y'] = 0 
    peakdem_prm = peakdem_prm.loc[peakdem_prm['t'].isin(firmcap['Year'].unique())]
    peakdem_prm['PRM_req'] = peakdem_prm['Value_x'] * (1+peakdem_prm['Value_y'])
    peakdem_prm.set_axis(['Region', 'Season', 'Year', 'peak_demand_MW', 'scenario', 'PRM', 'PRM_req'], axis=1, inplace=True)
    peakdem_prm = peakdem_prm.round(2)

    # Timeslice dispatch
    gen_tslc = gdxin['GEN']
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

    # demand - not included in excel output
    dem = dem.round(0)
    dem = sorting(dem, False, False, True)

    dem_tslc = map_h_to_tsname(dem_tslc, 'Timeslice')
    dem_tslc = dem_tslc.round(0)
    dem_tslc = sorting(dem_tslc, False, True, True)

    return annual_out, firmcap, tslc_out, tx_out, dem, dem_tslc, peakdem_prm
#%%

def write_outputs(dir):
    annual_out, firmcap, tslc_out, tx_out, dem, dem_tslc, peakdem_prm = ProcessingGdx()

    #timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    #outdir = os.path.join(dir, tag)
    #Path(outdir).mkdir(parents=True, exist_ok=True)
    csvsdir = os.path.join(dir, 'csvs')
    Path(csvsdir).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(csvsdir,'BAs')).mkdir(parents=True, exist_ok=True)

    #%%
    ######## EXPORT TO EXCEL
    # separate sheet for each table
    writer = pd.ExcelWriter(os.path.join(os.getcwd(), dir, "{}_outputs.xlsx".format(tag)))

    annual_out.to_excel(writer, sheet_name="Annual results", index=False)
    firmcap.to_excel(writer, sheet_name="Seasonal firm capacity", index=False)
    tslc_out.to_excel(writer, sheet_name="Timeslice results", index=False)
    tx_out.to_excel(writer, sheet_name='Transmission results', index=False)

    writer.save()
    print("Results saved to " + os.path.join(dir, "{}_outputs.xlsx".format(tag)))

    ######## WRITE OUTPUTS FOR VIZIT
    
    # cap.csv
    cap = annual_out[['State', 'scenario', 'Technology', 'Year', 'capacity_MW']]
    cap.set_axis(['st', 'scenario', 'tech', 'year', 'Capacity (MW)'], axis=1, inplace=True)
    cap.to_csv(os.path.join(csvsdir, 'cap.csv'), index=False)

    # cap_new_ann.csv
    cap_new = annual_out[['State', 'scenario', 'Technology', 'Year', 'investments_MW']]
    cap_new.set_axis(['st', 'scenario', 'tech', 'year', 'Investments (MW)'], axis=1, inplace=True)
    cap_new.to_csv(os.path.join(csvsdir, 'cap_new_ann.csv'), index=False)

    # cap_diff.csv
    cap_diff = cap.pivot_table(index=['st','tech','year'], columns='scenario', values='Capacity (MW)').reset_index()
    for i in scenarios[1:]:
        cap_diff[i] = cap_diff[scenarios[0]] - cap_diff[i]
    cap_diff.drop(scenarios[0], axis=1, inplace=True)
    cap_diff = cap_diff.set_index(['st','tech','year']).stack().reset_index(name='Difference (MW)')
    cap_diff.to_csv(os.path.join(csvsdir, 'cap_diff.csv'), index=False)

    # gen.csv
    gen = annual_out[['State', 'scenario', 'Technology', 'Year', 'generation_MWh']]
    gen.set_axis(['st', 'scenario', 'tech', 'year', 'Generation (MWh)'], axis=1, inplace=True)
    gen.to_csv(os.path.join(csvsdir, 'gen.csv'), index=False)

    # gen_timeslice_BA.csv
    gen_tslc_BA = tslc_out[['State', 'scenario', 'Technology', 'Year', 'time_slice', 'season', 'time', 'dispatch_MW']]
        
    # gen_timeslice.csv
    gen_tslc = summarize(gen_tslc_BA, 'dispatch_MW', ['scenario', 'Technology', 'Year', 'time_slice', 'season', 'time'])

    # add storage charging to gen
    stor_charge_BA = tslc_out[['State', 'scenario', 'Technology', 'Year', 'time_slice', 'season', 'time', 'STOR_IN_MW']]
    stor_charge = summarize(stor_charge_BA, 'STOR_IN_MW', ['scenario', 'Technology', 'Year', 'time_slice', 'season', 'time'])    
    stor_charge['dispatch_MW'] = stor_charge['STOR_IN_MW'] * -1
    stor_charge.drop('STOR_IN_MW', axis=1, inplace=True)

    gen_tslc = pd.concat([gen_tslc, stor_charge])
    gen_tslc = sorting(gen_tslc, True, True, False)
    gen_tslc.set_axis(['scenario', 'tech', 'year', 'timeslice', 'season', 'time', 'Generation (MW)'], axis=1, inplace=True)
    gen_tslc.to_csv(os.path.join(csvsdir, 'gen_timeslice.csv'), index=False)
    
    stor_charge_BA['dispatch_MW'] = stor_charge_BA['STOR_IN_MW'] * -1
    stor_charge_BA.drop('STOR_IN_MW', axis=1, inplace=True)
    gen_tslc_BA = pd.concat([gen_tslc_BA, stor_charge_BA])
    gen_tslc_BA = gen_tslc_BA.loc[gen_tslc_BA['dispatch_MW'].notnull()]
    gen_tslc_BA.set_axis(['st', 'scenario', 'tech', 'year', 'timeslice', 'season', 'time', 'Generation (MW)'], axis=1, inplace=True)
    gen_tslc_BA.to_csv(os.path.join(csvsdir, 'BAs', 'gen_timeslice_BA.csv'), index=False)

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
    dem_tslc.set_axis(['scenario', 'year', 'timeslice', 'season', 'time', 'type', 'Demand (MW)'], axis=1, inplace=True)
    dem_tslc.to_csv(os.path.join(csvsdir, 'demand_timeslice.csv'), index=False)

    dem_tslc_BA.set_axis(['st', 'scenario', 'year', 'timeslice', 'season', 'time', 'Demand (MW)', 'type'], axis=1, inplace=True)
    dem_tslc_BA.to_csv(os.path.join(csvsdir, 'BAs', 'demand_timeslice_BA.csv'), index=False)

    # transmission.csv
    tx_out.to_csv(os.path.join(csvsdir, 'transmission.csv'), index=False)

    # opres.csv
    opres = annual_out[['State', 'scenario', 'Technology', 'Year', 'operating_reserves_MWh']]
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

    # copy visit.html and report.json into the directory
    shutil.copyfile('vizit.html', os.path.join(csvsdir, 'vizit.html'))
    shutil.copyfile('vizit-config.json', os.path.join(csvsdir, 'vizit-config.json'))
    shutil.copyfile('style.csv', os.path.join(csvsdir, 'style.csv'))

write_outputs(SAVEDIR)