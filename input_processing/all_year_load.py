# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 11:55:00 2020
@author: jho
"""
#%% Imports
import gdxpds
import pandas as pd
import numpy as np
import os
import re
import argparse
import shutil
# direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()

#%% Argument inputs
parser = argparse.ArgumentParser(
    description="""This file produces the static and flexible load inputs""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("GSw_EFS_Flex", type=int, default=0,
                    help="Switch for turning EFS load flexibility on or off")
parser.add_argument("GSw_EFS1_AllYearLoad", type=str, default='default',
                    help="Switch to choose EFS profiles [default, EPREFERENCE, EPMEDIUM, EPHIGH]")
parser.add_argument("GSw_EFS2_FlexCase", type=str, default='EPREFERENCE_Baseflex',
                    help=("Case used for EFS flex_type - format is {1}_{2}, where "
                          "1 in [EPREFERENCE, EPMEDIUM, EPHIGH] and "
                          "2 in [Baseflex, Currentflex, Enhancedflex]"))
parser.add_argument("GSw_DR", type=int, default=0,
                    help="Switch to turn on DR investment")
parser.add_argument("drscen", type=str, default='none',
                    help='DR scenario for supply curve and flex load')
parser.add_argument("inputs_case", help="output directory")
parser.add_argument('-t','--ldcProfiles', type=str, default='standard',
                        help='Load profiles to use')

#add argument values to local variables
locals().update(vars(parser.parse_args()))

#%% Settings for testing ###
# reeds_dir = os.path.expanduser('~/github/ReEDS-2.0/')
# GSw_EFS_Flex = 0
# GSw_EFS1_AllYearLoad = "default"
# GSw_EFS2_FlexCase = "EPREFERENCE_Baseflex"
# inputs_case = os.path.expanduser('~/github/ReEDS-2.0/runs/v20200911_master_Ref/inputs_case/')


#%% Additional inputs
decimals = 4
### Note that we save the outputs as load_2010.csv and peak_2010.csv, as 2010 is the 
### conventional model start year for load growth. reeds_data_year specifies
### the year to use for weather and load variability profiles.
reeds_data_year = int(
    pd.read_csv(os.path.join(reeds_dir, 'ReEDS_Augur', 'value_defaults.csv'), index_col='key')
    .loc['reeds_data_year','value']
)
### Link between peak-timeslices and parent-timeslices (in case we add more peak-slices)
slicetree = {'h17': 'h3',}

#%%### Calculate timeslice-average and -peak load from hourly load
###### Load additional inputs
### Get the number of hours per timeslice
numhours = pd.read_csv(
    os.path.join(reeds_dir,'inputs','numhours.csv'),
    names=['h','numhours'],index_col='h',squeeze=True)

# Get fraction of timeslice split off
slicefrac = pd.merge(
    pd.DataFrame(slicetree.items(), slicetree.values())
      .reset_index()
      .melt(id_vars='index', )
      .drop('variable', 1),
    numhours, right_on='h', left_on='value'
    )
slicefrac = (
    pd.merge(slicefrac, slicefrac.groupby('index')['numhours'].sum(),
             on='index', suffixes=['','_tot'])
    .rename(columns={'value':'h'})
    )
slicefrac['frac'] = slicefrac['numhours'] / slicefrac['numhours_tot']
### Get the hour-mapper
h_dt_szn = (
    pd.read_csv(os.path.join(reeds_dir,'inputs','variability','h_dt_szn.csv'), index_col='hour')
    .replace({'winter':'wint','spring':'spri','summer':'summ'})
    .rename(columns={'season':'szn','year':'t',})
)
### Get the 7-year hourly demand, downselect to reeds_data_year
if ldcProfiles == 'standard':
    folder = 'multi_year'
else:
    folder = 'test_profiles'
load_hourly = pd.read_csv(
    os.path.join(reeds_dir,'inputs','variability',folder,'load.csv.gz'), 
    index_col=0, float_precision='round_trip')
load_hourly.columns.name = 'r'
load_hourly['t'] = load_hourly.index.map(h_dt_szn.t)
load_hourly = load_hourly.loc[load_hourly.t==reeds_data_year].drop(['t'],axis=1).copy()

#%% Calculate the seasonal-peak demand by region, save as peak_2010.csv
load_hourly['szn'] = load_hourly.index.map(h_dt_szn.szn)
### Get the peak and write it
peak_2010 = load_hourly.groupby('szn').max().T
peak_2010.to_csv(os.path.join(inputs_case, 'peak_2010.csv'))

#%% Calculate the timeslice-average demand by region for the base year, save as load_2010.csv
load_hourly['h'] = load_hourly.index.map(h_dt_szn.h)
load_2010 = (
    load_hourly
    ### Drop extra columns, take the mean by timeslice
    .drop(['szn'], axis=1).groupby('h').mean()
    ### Add peak rows, which we fill below
    .append(pd.DataFrame(index=list(slicetree.keys())))
)
load_2010.index.name = 'h'
load_2010.columns.name = 'r'
### Loop over peak slices (e.g. h17), get peak and (parent-peak) averages
for peakslice in slicetree:
    parentslice = slicetree[peakslice]
    for r in load_2010.columns:
        ### Take peakslice (e.g. h17) from the top hours of parent slice (e.g. h3)
        load_2010.loc[peakslice,r] = (
            load_hourly.loc[load_hourly.h==parentslice,r]
            .nlargest(numhours[peakslice]).mean())
        ### Overwrite parent slice with average over the remaining hours in parent slice
        ### Note that numhours already includes the correct number of hours (e.g. h3: 268-40=228)
        load_2010.loc[parentslice,r] = (
            load_hourly.loc[load_hourly.h==parentslice,r]
            .nsmallest(numhours[parentslice]).mean()
        )
### Capitalize the timeslices to match the original format
load_2010.index = load_2010.index.map(lambda x: x.upper())
### Write it
load_2010.T.round(decimals).sort_index(1).to_csv(os.path.join(inputs_case, 'load_2010.csv'))

#%%### Calculate peak load by season and timeslice
flexcase = ""
os.chdir(reeds_dir)
if (GSw_EFS1_AllYearLoad=="default"):
    #%% Calculate the timeslice-peak demand by region, to save as h_peak_all.csv
    h_peak_data = (
        load_hourly.drop('szn',axis=1).groupby('h').max()
        ### Add peak row(s), which we'll fill below
        .append(pd.DataFrame(index=list(slicetree.keys()))))
    h_peak_data.index.name = 'h'
    h_peak_data.columns.name = 'r'
    for peakslice in slicetree:
        parentslice = slicetree[peakslice]
        for r in h_peak_data.columns:
            ### Take peak from the top hours of parent
            h_peak_data.loc[peakslice,r] = (
                load_hourly.loc[load_hourly.h==parentslice,r]
                .nlargest(numhours[peakslice]).max())
            ### Take parent from the remaining hours in parent
            h_peak_data.loc[parentslice,r] = (
                load_hourly.loc[load_hourly.h==parentslice,r]
                .nsmallest(numhours[parentslice]).max()
            )
    ### Put in standard format and save
    h_peak_data = (
        h_peak_data.T.stack().rename(2010).reset_index().rename(columns={'timeslice':'h'}))
    h_peak_data.h = h_peak_data.h.map(lambda x: x.upper())

    # Get peak load by season, put in same format as EFS
    peak_data = pd.read_csv(os.path.join(inputs_case,'peak_2010.csv'))
    peak_data = pd.melt(peak_data,id_vars='r',var_name='szn').rename(columns={"value":"2010"})

    if GSw_EFS_Flex > 0:
        flex_data = pd.read_csv(
            os.path.join('inputs','loaddata','{}_frac.csv'.format(GSw_EFS2_FlexCase)))
        flexcase=GSw_EFS2_FlexCase

else:
    # Just use the input data directly; don't scale it by inputs/variability.
    load_data = pd.read_csv(
        os.path.join('inputs','loaddata','{}load.csv'.format(GSw_EFS1_AllYearLoad)))
    peak_data = pd.read_csv(
        os.path.join('inputs','loaddata','{}peak.csv'.format(GSw_EFS1_AllYearLoad)))
    h_peak_data = pd.read_csv(
        os.path.join('inputs','loaddata','{}ts_peak.csv'.format(GSw_EFS1_AllYearLoad))
    ).rename(columns={'timeslice':'h'})
    ### Read the superpeak timeslice values (e.g. h17) from the parents (e.g. h3)
    for peakslice in slicetree:
        parentslice = slicetree[peakslice]
        h_peak_data_peakslice = h_peak_data.copy()
        index_parent = h_peak_data_peakslice['h']==parentslice.upper()
        h_peak_data_peakslice = h_peak_data_peakslice[index_parent]
        h_peak_data_peakslice['h'] = peakslice.upper()
        h_peak_data = h_peak_data.append(h_peak_data_peakslice,ignore_index=True)
    #if flexibility is turned on...
    if GSw_EFS_Flex > 0:
        #load in the %GSw_EFS_AllYearLoad%_%GSw_EFS_Case%_frac.csv file
        flex_data = pd.read_csv(
            os.path.join('inputs','loaddata','{}_frac.csv'.format(GSw_EFS2_FlexCase)))
        flexcase = GSw_EFS1_AllYearLoad + "_" + GSw_EFS2_FlexCase

    #round values
    load_data = load_data.round(decimals)
    peak_data = peak_data.round(decimals)
    h_peak_data = h_peak_data.round(decimals)
    if GSw_EFS_Flex > 0:
        flex_data = flex_data.round(decimals)
    load_data.rename(columns={'timeslice':'h'}).to_csv(
        os.path.join(inputs_case,'load_all.csv'),index=False)

#%% if flexibility is not turned on, load in the reference case
#%% Not needed for DR, as reference case is loaded based on default scenario
if GSw_EFS_Flex == 0:
    flex_data = pd.read_csv(
        os.path.join('inputs','loaddata','EPREFERENCE_Baseflex_frac.csv'))
    for col in flex_data.columns:
        #if the value is a number, replace it with zero
        if np.issubdtype(flex_data[col].dtype, np.number):
            flex_data[col].values[:] = 0
else:
    flex_data = flex_data.round(decimals)
    flexcasenamefile = open(os.path.join(inputs_case,'flex_case_name.txt'),"w")
    flexcasenamefile.write(flexcase)
    flexcasenamefile.close()

# Don't need switch for DR - no DR has default (none) scenario
shutil.copy(os.path.join('inputs','demand_response','dr_increase_profile_{}.csv').format(drscen),
            os.path.join(inputs_case, 'dr_inc.csv'))
shutil.copy(os.path.join('inputs','demand_response','dr_decrease_profile_{}.csv').format(drscen),
            os.path.join(inputs_case, 'dr_dec.csv'))
dr_data1 = pd.read_csv(
    os.path.join('inputs','demand_response','dr_increase_{}.csv').format(drscen))
dr_data2 = pd.read_csv(
    os.path.join('inputs','demand_response','dr_decrease_{}.csv').format(drscen))
# If Using DR, adjust data for H17
if GSw_DR > 0:
    # Add H17 based on fraction of hours. Should change if we do something
    # fancier with the DR processing
    dr_data1 = pd.merge(dr_data1, slicefrac, left_on='timeslice', right_on='index', how='outer')
    dr_data1.drop(['index','numhours','numhours_tot'], axis=1, inplace=True)
    ts_adj = dr_data1.frac==dr_data1.frac
    dr_data1.loc[ts_adj,'value'] = dr_data1[ts_adj]['value'] * dr_data1[ts_adj]['frac']
    dr_data1.loc[(dr_data1.timeslice!=dr_data1.h) & ts_adj,'timeslice'] = \
        dr_data1.loc[(dr_data1.timeslice!=dr_data1.h) & ts_adj,'h']
    dr_data1 = dr_data1.round(decimals).drop(['h','frac'], axis=1)

    dr_data2 = pd.merge(dr_data2, slicefrac, left_on='timeslice', right_on='index', how='outer')
    dr_data2.drop(['index','numhours','numhours_tot'], axis=1, inplace=True)
    ts_adj = dr_data2.frac==dr_data2.frac
    dr_data2.loc[ts_adj,'value'] = dr_data2[ts_adj]['value'] * dr_data2[ts_adj]['frac']
    dr_data2.loc[(dr_data2.timeslice!=dr_data2.h) & ts_adj,'timeslice'] = \
        dr_data2.loc[(dr_data2.timeslice!=dr_data2.h) & ts_adj,'h']
    dr_data2 = dr_data2.round(decimals).drop(['h','frac'], axis=1)

#%% Write outputs
h_peak_data.to_csv(os.path.join(inputs_case,'h_peak_all.csv'),index=False)
peak_data.rename(columns={'season':'szn'}).to_csv(
    os.path.join(inputs_case,'peak_all.csv'),index=False)
flex_data.rename(columns={'timeslice':'h'}).to_csv(
    os.path.join(inputs_case,'flex_frac_all.csv'),index=False)
dr_data1.to_csv(
    os.path.join(inputs_case,'dr_increase.csv'),index=False, header=False)
dr_data2.to_csv(
    os.path.join(inputs_case,'dr_decrease.csv'),index=False, header=False)

toc(tic=tic, year=0, process='input_processing/all_year_load.py', 
    path=os.path.join(inputs_case,'..'))
