# -*- coding: utf-8 -*-
"""
Process ReEDS model results from gams
Arrange the tables, summarize the data, and save key results in Excel format

@author Ilya Chernyakhovskiy

"""

#%%
import os
import subprocess

if os.name == 'posix':
    os.environ['GAMS_DIR'] = os.path.dirname(subprocess.check_output(['which', 'gams'])).decode()

import gdxpds
import pandas as pd
import datetime
import sys

# suppress pandas chained assignments warning
pd.options.mode.chained_assignment = None

# Bokeh libraries
from bokeh.io import output_file, output_notebook
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
from bokeh.layouts import row, column, gridplot
from bokeh.models.widgets import Tabs, Panel
from bokeh.transform import factor_cmap
from pathlib import Path

case = str(sys.argv[1])

# read the timeslice map
ts_name_map = pd.read_csv(os.path.join("A_Inputs","inputs","analysis","time_slice_names.csv"))

# read the gens map
params = pd.read_csv(os.path.join("A_Inputs","inputs","analysis","analysis_parameters.csv"))

def summarize(df, sumby):
    out = df.groupby(sumby).sum().reset_index()
    return(out)

def setnames(df, lvl_name):
    out = df.rename(columns={'i':'Technology','h':'Timeslice','r':'State','t':'Year','Level':lvl_name})
    return(out)

def map_rs_to_state(df, rmap):
    out = pd.merge(df, rmap, left_on = 'r', right_on = 'rs', how='left')
    out['r_y'].loc[out['r_y'].isnull()] = out['r_x']
    out.rename(columns = {'r_y':'r'}, inplace = True)
    return(out)

def get_tslc_hours(df, left_on, tslc_hours):
    df = df.merge(tslc_hours, left_on = left_on, right_on = 'h')
    df.rename(columns = {'Value':'Timeslice_hours'}, inplace = True)
    return(df)

def map_h_to_tsname(df, left_on):
    df = df.merge(ts_name_map, left_on=left_on, right_on='h')
    return(df)

def map_type_category(df, left_on):
    df = df.merge(params[['reeds.category','Type']], left_on=left_on, right_on='reeds.category')
    return(df)
# %%

#%%
def ProcessingGdx():
    # developing mode - start with a single gdx file
    #%%
    case_gdx = "output_{}.gdx".format(case)
    run_name = case.split('_')[0] + '_' + case.split('_')[1]
    gdxdir = os.path.join("reeds_server","users_output", case.split('_')[0], run_name,"runs", case, "outputs", case_gdx)

    savedir = os.path.join("reeds_server", "users_output", case.split('_')[0], run_name, 'exceloutput') # TODO: change save location to user-specific folder
    Path(savedir).mkdir(parents=True, exist_ok=True)

    # check that file exists
    if (not os.path.exists(gdxdir)):
        print("{} not found".format(gdxdir))
        exit()
    else:
        print("Processing {}".format(gdxdir))

    gdxin = gdxpds.to_dataframes(gdxdir)
    #%%

    # get mapping of resource regions to states
    rmap = gdxin['r_rs'][['r','rs']]

    # timeslice hours map
    tslc_hours = gdxin['hours']
    #%%
    ####### Begin data queries 
    #######

    # Installed capacity
    global cap
    cap = gdxin['CAP']
    cap = map_rs_to_state(cap, rmap)
    cap = map_type_category(cap, 'i')
    cap = summarize(cap, ['Type','r','t'])
    cap = setnames(cap, 'capacity_MW')
    cap = cap[['Type','State','Year','capacity_MW']]

    #%%
    # Capacity investments
    inv = gdxin['INV']
    inv = map_rs_to_state(inv, rmap)
    inv = map_type_category(inv, 'i')
    inv = summarize(inv, ['Type','r','t'])
    inv = setnames(inv, 'investments_MW')
    inv = inv[['Type','State','Year','investments_MW']]

    #%%
    # Firm capacity 
    pdlist = [gdxin['firm_conv'],gdxin['firm_hydro'],gdxin['firm_vg'],gdxin['firm_stor']]
    firmcap = pd.concat(pdlist)
    firmcap.set_axis(['Region','Season','Year','Technology','firm_capacity_MW'], axis = 1, inplace = True)
    firmcap = firmcap.round(0)

    #%%
    # Timeslice dispatch
    gen_tslc = gdxin['GEN']
    gen_tslc = map_type_category(gen_tslc, 'i')
    gen_tslc = summarize(gen_tslc, ['Type','r','h','t'])
    gen_tslc = setnames(gen_tslc, 'dispatch_MW')
    gen_tslc = get_tslc_hours(gen_tslc, 'Timeslice', tslc_hours)
    gen_tslc = gen_tslc[['Type','State','Year','Timeslice','Timeslice_hours','dispatch_MW']]
    gen_tslc['generation_MWh'] = gen_tslc['dispatch_MW'] * gen_tslc['Timeslice_hours']

    # Annual generation
    gen = summarize(gen_tslc, ['Type','State','Year'])
    gen = gen[['Type','State','Year','generation_MWh']]

    #%%
    # Timeslice operating reserves
    opres_tslc = gdxin['OPRES']
    opres_tslc = map_type_category(opres_tslc, 'i')
    opres_tslc = summarize(opres_tslc, ['Type','r','h','t'])
    opres_tslc = setnames(opres_tslc, 'operating_reserves_MW')
    opres_tslc = opres_tslc[['Type','State','Timeslice','Year','operating_reserves_MW']]
    opres_tslc = get_tslc_hours(opres_tslc, 'Timeslice', tslc_hours)
    opres_tslc = opres_tslc[['Type','State','Year','Timeslice','Timeslice_hours','operating_reserves_MW']]
    opres_tslc['operating_reserves_MWh'] = opres_tslc['operating_reserves_MW'] * opres_tslc['Timeslice_hours']

    # Annual operating reserves
    opres = summarize(opres_tslc, ['Type','State','Year'])
    opres = opres[['Type','State','Year','operating_reserves_MWh']]

    #%%
    # Storage operation
    storin = gdxin['STORAGE_IN']
    storin = map_type_category(storin, 'i')
    storin = summarize(storin, ['Type','r','h','t'])
    storin = setnames(storin, 'STOR_IN_MW')

    storlev = gdxin['STORAGE_LEVEL']
    storlev = map_type_category(storlev, 'i')
    storlev = summarize(storlev, ['Type','r','h','t'])
    storlev = setnames(storlev, 'STOR_LVL_MWh')

    storgen = gen_tslc.loc[pd.Series(gen_tslc['Type']).str.contains('BESS|Pumped').tolist()]
    storgen.rename(columns = {"dispatch_MW":"STOR_GEN_MW"}, inplace = True)
    
    storops = pd.merge(storin, storlev, on = ['Type','State','Year','Timeslice'])
    storops = pd.merge(storops, storgen, on = ['Type','State','Year','Timeslice'])
    storops = storops[['Type','State','Year','Timeslice','STOR_IN_MW','STOR_LVL_MWh','STOR_GEN_MW']]

    #%%
    # Transmission capacity
    txcap = summarize(gdxin['CAPTRAN'], ['r','rr','t'])
    txcap = txcap[['r','rr','t','Level']]
    txcap.set_axis(['State_from','State_to','Year','transmission_capacity_MW'], axis = 1, inplace = True)

    # Transmission investments
    txinv = gdxin['txinv'].copy()
    txinv.set_axis(['State_from','State_to','Year','transmission_investment_MW'], axis = 1, inplace = True)

    # Emissions
    emit = gdxin['EMIT']

    #%%
    ##### Organize sheets
    # Sheet 1: Annual results - cap, inv, gen, opres, emit
    annual_out = pd.merge(cap, inv, on = ['Type','State','Year'], how='left')
    annual_out = annual_out.merge(gen, on = ['Type','State','Year'], how='left')
    annual_out = annual_out.merge(opres, on = ['Type','State','Year'], how='left')
    annual_out = annual_out.round(0)
    #annual_out = annual_out.merge(emit, on = ['Technology','State','Year'])

    # Sheet 2: Seasonal firm capacity - firmcap
    # just firmcap here

    # Sheet 3: Timeslice results - gen_tslc, opres_tslc, storops
    tslc_out = pd.merge(gen_tslc, opres_tslc, on = ['Type','State','Year','Timeslice','Timeslice_hours'], how = 'outer')
    tslc_out = tslc_out.merge(storops, on = ['Type','State','Year','Timeslice'], how = 'outer')
    tslc_out = map_h_to_tsname(tslc_out, 'Timeslice')
    tslc_out.drop(columns=['Timeslice','h'], inplace=True)
    tslc_out = tslc_out.round(0)

    # Sheet 4: Transmission results - txcap, txinv
    tx_out = pd.merge(txcap, txinv, on = ['State_from','State_to','Year'], how='left')
    tx_out = tx_out.round(0)
    #%%
    #%%
    ######## EXPORT TO EXCEL
    ########
    # separate sheet for each table
    writer = pd.ExcelWriter(os.path.join(os.getcwd(),savedir,"{}_results.xlsx".format(case)))

    annual_out.to_excel(writer, sheet_name = "Annual results", index=False)
    firmcap.to_excel(writer, sheet_name = "Seasonal firm capacity", index=False)
    tslc_out.to_excel(writer, sheet_name = "Timeslice results", index=False)
    tx_out.to_excel(writer, sheet_name='Transmission results', index=False)

    writer.save()
    print("Results saved to " + os.path.join(savedir,"{}_results.xlsx".format(case)))
# %%

#%%
# read gdx output and save results as excel
ProcessingGdx()


