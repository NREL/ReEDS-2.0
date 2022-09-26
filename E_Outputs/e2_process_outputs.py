# -*- coding: utf-8 -*-
"""
Process ReEDS model results from gams
Arrange the tables, summarize the data, and save key results in Excel format

@author Ilya Chernyakhovskiy

"""

#%%
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import sys
if os.name == 'posix':
    os.environ['GAMS_DIR'] = os.path.dirname(subprocess.check_output(['which', 'gams'])).decode()
import gdxpds
import pandas as pd

# suppress pandas chained assignments warning
pd.options.mode.chained_assignment = None

cases = list(sys.argv[1:])
user = [x.split('_')[0] for x in cases][0]
root = os.path.join("reeds_server", "users_output", user)
SAVEDIR = os.path.join(root, 'outputs')
Path(SAVEDIR).mkdir(parents=True, exist_ok=True)

#%%
# read the timeslice map
ts_name_map = pd.read_csv(os.path.join("A_Inputs", "inputs", "analysis", "time_slice_names.csv"))
params = pd.read_csv(os.path.join('A_Inputs', 'inputs', 'analysis', 'analysis_parameters.csv'))
tech_type_map = params[['reeds.category', 'Type']].dropna()
tech_order = params[['Gen.Order']].dropna()['Gen.Order'].to_list()
season_order = ['Winter','Spring','Summer','Rainy','Autumn']
time_order = ['night', 'sunrise', 'morning', 'afternoon', 'sunset', 'evening', 'peak']

def summarize(df, sumby):
    """aggregation helper function"""
    out = df.groupby(sumby).sum().reset_index()
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
    df = df.merge(tech_type_map, left_on=left_on, right_on='reeds.category')
    return df

def sort_techs(df):
    df['Technology'] = pd.Categorical(df['Technology'], tech_order)
    df.sort_values('Technology', ascending=False, inplace=True)
    return df

def sort_timeslices(df):
    df['season'] = pd.Categorical(df['season'], season_order)   
    df['time'] = pd.Categorical(df['time'], time_order)
    df.sort_values(['season','time'], inplace=True)
    return df

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
    vars = ['CAP', 'INV', 'GEN', 'OPRES', 'STORAGE_IN', 'CAPTRAN']
    params = ['r_rs', 'hours', 'firm_conv', 'firm_hydro', 'firm_vg', 'firm_stor', 'txinv']
    keep = vars + params
    out = dict.fromkeys(keep)

    for i in range(len(gdxdirs)):
        if not os.path.exists(gdxdirs[i]):
            print("{} not found".format(gdxdirs[i]))
            exit()
        else:
            print("Reading {}".format(gdxdirs[i]))
        scenario = cs[i].split('_')[1] + "_" + cs[i].split('_')[2]
        dat = gdxpds.to_dataframes(gdxdirs[i])
        dat = {x: dat[x] for x in keep}
        dat = {k: add_scen_col(v, scenario) for k, v in dat.items()}
        for k in dat.keys():
            out[k] = pd.concat([out[k], dat[k]], axis=0)
    return out
#%%
def ProcessingGdx():
    # developing mode - use these cases for testing
    # cases = ["ilyac_marmot3_test","ilyac_marmot3_newtest"]
    #%%
    gdxdirs = get_gdxdirs(cases)

    #%%
    gdxin = read_gdxs(gdxdirs, cases)
    #%%

    # get mapping of resource regions to states
    rmap = gdxin['r_rs'][['r', 'rs']]
    rmap = rmap.groupby(['r', 'rs']).size().reset_index()

    # timeslice hours map
    tslc_hours = gdxin['hours']
    tslc_hours = tslc_hours.groupby(['h','Value']).size().reset_index()
    #%%
    ####### Begin data queries 
    #######

    # Installed capacity
    cap = gdxin['CAP']
    cap = map_rs_to_state(cap, rmap)
    cap = map_tech_to_type(cap, 'i')
    cap = summarize(cap, ['Type', 'r', 't', 'scenario'])
    cap = setnames(cap, 'capacity_MW')
    cap = cap[['Technology', 'State', 'Year', 'capacity_MW', 'scenario']]

    #%%
    # Capacity investments
    inv = gdxin['INV']
    inv = map_rs_to_state(inv, rmap)
    inv = map_tech_to_type(inv, 'i')
    inv = summarize(inv, ['Type', 'r', 't', 'scenario'])
    inv = setnames(inv, 'investments_MW')
    inv = inv[['Technology', 'State', 'Year', 'investments_MW', 'scenario']]

    #%%
    # Firm capacity 
    pdlist = [gdxin['firm_conv'], gdxin['firm_hydro'], gdxin['firm_vg'], gdxin['firm_stor']]
    firmcap = pd.concat(pdlist)
    firmcap.set_axis(['Region', 'Season', 'Year', 'Technology', 'firm_capacity_MW', 'scenario'], axis = 1, inplace = True)
    firmcap = map_tech_to_type(firmcap, 'Technology')
    firmcap = summarize(firmcap, ['Type','Region','Season','Year','scenario'])
    firmcap = setnames(firmcap, 'firm_capacity_MW')
    firmcap = sort_techs(firmcap)
    firmcap = firmcap.round(0)

    #%%
    # Timeslice dispatch
    gen_tslc = gdxin['GEN']
    gen_tslc = map_tech_to_type(gen_tslc, 'i')
    gen_tslc = summarize(gen_tslc, ['Type', 'r', 'h', 't', 'scenario'])
    gen_tslc = setnames(gen_tslc, 'dispatch_MW')
    gen_tslc = get_tslc_hours(gen_tslc, 'Timeslice', tslc_hours)
    gen_tslc = gen_tslc[['Technology', 'State', 'Year', 'Timeslice', 'Timeslice_hours', 'dispatch_MW', 'scenario']]
    gen_tslc['generation_MWh'] = gen_tslc['dispatch_MW'] * gen_tslc['Timeslice_hours']

    # Annual generation
    gen = summarize(gen_tslc, ['Technology', 'State', 'Year', 'scenario'])
    gen = gen[['Technology', 'State', 'Year', 'generation_MWh', 'scenario']]

    #%%
    # Timeslice operating reserves
    opres_tslc = gdxin['OPRES']
    opres_tslc = map_tech_to_type(opres_tslc, 'i')
    opres_tslc = summarize(opres_tslc, ['Type', 'r', 'h', 't', 'scenario'])
    opres_tslc = setnames(opres_tslc, 'operating_reserves_MW')
    opres_tslc = opres_tslc[['Technology', 'State', 'Timeslice', 'Year', 'operating_reserves_MW', 'scenario']]
    opres_tslc = get_tslc_hours(opres_tslc, 'Timeslice', tslc_hours)
    opres_tslc = opres_tslc[['Technology', 'State', 'Year', 'Timeslice', 'Timeslice_hours', 'operating_reserves_MW', 'scenario']]
    opres_tslc['operating_reserves_MWh'] = opres_tslc['operating_reserves_MW'] * opres_tslc['Timeslice_hours']

    # Annual operating reserves
    opres = summarize(opres_tslc, ['Technology', 'State', 'Year', 'scenario'])
    opres = opres[['Technology', 'State', 'Year', 'operating_reserves_MWh', 'scenario']]

    #%%
    # Storage operation
    storin = gdxin['STORAGE_IN']
    storin = map_tech_to_type(storin, 'i')
    storin = summarize(storin, ['Type', 'r', 'h', 't', 'scenario'])
    storin = setnames(storin, 'STOR_IN_MW')

 #   storlev = summarize(gdxin['STORAGE_LEVEL'], ['i', 'r', 'h', 't', 'scenario'])
 #   storlev = setnames(storlev, 'STOR_LVL_MWh')

    storgen = gen_tslc.loc[pd.Series(gen_tslc['Technology']).str.contains('BESS|Pumped').tolist()]
    storgen.rename(columns={"dispatch_MW":"STOR_GEN_MW"}, inplace=True)

  #  storops = pd.merge(storin, storlev, on = ['Technology', 'State', 'Year', 'Timeslice', 'scenario'])
    storops = pd.merge(storin, storgen, on = ['Technology', 'State', 'Year', 'Timeslice', 'scenario'])
    storops = storops[['Technology', 'State', 'Year', 'Timeslice', 'STOR_IN_MW', 'STOR_GEN_MW', 'scenario']]

    #%%
    # Transmission capacity
    txcap = summarize(gdxin['CAPTRAN'], ['r', 'rr', 't', 'scenario'])
    txcap = txcap[['r', 'rr', 't', 'Level', 'scenario']]
    txcap.set_axis(['State_from', 'State_to', 'Year', 'transmission_capacity_MW', 'scenario'], axis = 1, inplace = True)

    # Transmission investments
    txinv = gdxin['txinv'].copy()
    txinv.set_axis(['State_from', 'State_to', 'Year', 'transmission_investment_MW', 'scenario'], axis = 1, inplace = True)

    # Emissions
  #  emit = gdxin['EMIT']

    #%%
    ##### Organize sheets
    # Sheet 1: Annual results - cap, inv, gen, opres, emit
    annual_out = pd.merge(cap, inv, on=['Technology', 'State', 'Year', 'scenario'], how='left')
    annual_out = annual_out.merge(gen, on=['Technology', 'State', 'Year', 'scenario'], how='left')
    annual_out = annual_out.merge(opres, on=['Technology', 'State', 'Year', 'scenario'], how='left')
    annual_out = sort_techs(annual_out)
    annual_out = annual_out.round(0)
    #annual_out = annual_out.merge(emit, on = ['Technology','State','Year'])

    # Sheet 2: Seasonal firm capacity - firmcap
    # just firmcap here

    # Sheet 3: Timeslice results - gen_tslc, opres_tslc, storops
    tslc_out = pd.merge(gen_tslc, opres_tslc, on=['Technology', 'State', 'Year', 'Timeslice', 'Timeslice_hours', 'scenario'], how = 'outer')
    tslc_out = tslc_out.merge(storops, on=['Technology', 'State', 'Year', 'Timeslice', 'scenario'], how = 'outer')
    tslc_out = map_h_to_tsname(tslc_out, 'Timeslice')
    tslc_out = sort_techs(tslc_out)
    tslc_out = sort_timeslices(tslc_out)
    tslc_out.drop(columns=['Timeslice', 'h', 'Timeslice_hours'], inplace=True)
    tslc_out = tslc_out.round(0)

    # Sheet 4: Transmission results - txcap, txinv
    tx_out = pd.merge(txcap, txinv, on=['State_from', 'State_to', 'Year', 'scenario'], how='left')
    tx_out = tx_out.round(0)

    # TODO: add helper function to change tech order

    return annual_out, firmcap, tslc_out, tx_out
#%%

def write_outputs(dir):
    annual_out, firmcap, tslc_out, tx_out = ProcessingGdx()

    timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    outdir = os.path.join(dir, timestamp)
    Path(outdir).mkdir(parents=True, exist_ok=True)
    csvsdir = os.path.join(outdir,'csvs')
    Path(csvsdir).mkdir(parents=True, exist_ok=True)

    #%%
    ######## EXPORT TO EXCEL
    # separate sheet for each table
    writer = pd.ExcelWriter(os.path.join(os.getcwd(), outdir, "{}_outputs.xlsx".format(timestamp)))

    annual_out.to_excel(writer, sheet_name = "Annual results", index=False)
    firmcap.to_excel(writer, sheet_name = "Seasonal firm capacity", index=False)
    tslc_out.to_excel(writer, sheet_name = "Timeslice results", index=False)
    tx_out.to_excel(writer, sheet_name='Transmission results', index=False)

    writer.save()
    print("Results saved to " + os.path.join(outdir, "{}_outputs.xlsx".format(timestamp)))

    ######## WRITE OUTPUTS FOR VIZIT
    
    # cap.csv
    cap = annual_out[['State', 'scenario', 'Technology', 'Year', 'capacity_MW']]
    cap.set_axis(['st', 'scenario', 'tech', 'year', 'Capacity (MW)'], axis=1, inplace=True)
    cap.to_csv(os.path.join(csvsdir, 'cap.csv'), index=False)

    # cap_new_ann.csv
    cap_new = annual_out[['State', 'scenario', 'Technology', 'Year', 'investments_MW']]
    cap_new.set_axis(['st', 'scenario', 'tech', 'year', 'Investments (MW)'], axis=1, inplace=True)
    cap_new.to_csv(os.path.join(csvsdir, 'cap_new_ann.csv'), index=False)

    # gen.csv
    gen = annual_out[['State', 'scenario', 'Technology', 'Year', 'generation_MWh']]
    gen.set_axis(['st', 'scenario', 'tech', 'year', 'Generation (MWh)'], axis=1, inplace=True)
    gen.to_csv(os.path.join(csvsdir, 'gen.csv'), index=False)

    # gen_timeslice.csv
    gen_tslc = tslc_out[['State', 'scenario', 'Technology', 'Year', 'time_slice', 'season', 'time', 'dispatch_MW']]
    gen_tslc.set_axis(['st', 'scenario', 'tech', 'year', 'timeslice', 'season', 'time', 'Generation (MW)'], axis=1, inplace=True)
    gen_tslc.to_csv(os.path.join(csvsdir, 'gen_timeslice.csv'), index=False)

    # copy visit.html and report.json into the directory
    shutil.copyfile('vizit.html', os.path.join(csvsdir, 'vizit.html'))
    shutil.copyfile('report.json', os.path.join(csvsdir, 'report.json'))
    shutil.copyfile('style.csv', os.path.join(csvsdir, 'style.csv'))

write_outputs(SAVEDIR)