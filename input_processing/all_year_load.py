# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 11:55:00 2020
@author: jho
"""
#%% Imports
import pandas as pd
import numpy as np
import os
import argparse
import shutil
import LDC_prep
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()

#%% Argument inputs
parser = argparse.ArgumentParser(
    description="""This file produces the static and flexible load inputs""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("inputs_case", help="output directory")

#%% Parse args
args = parser.parse_args()
reeds_dir = args.reeds_dir
inputs_case = args.inputs_case

# #%% Settings for testing ###
# reeds_dir = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
# inputs_case = os.path.join(
#     reeds_dir,'runs','v20230104_hourlymergeM0_default','inputs_case')

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

#%% Additional inputs
decimals = 4
### Note that we save the outputs as load_2010.csv, as 2010 is the 
### conventional model start year for load growth. reeds_data_year specifies
### the year to use for weather and load variability profiles.
reeds_data_year = int(
    pd.read_csv(os.path.join(reeds_dir, 'ReEDS_Augur', 'value_defaults.csv'), index_col='key')
    .loc['reeds_data_year','value']
)
### Link between peak-timeslices and parent-timeslices (in case we add more peak-slices)
slicetree = {'h17': 'h3',}

# Get valid regions
val_r = pd.read_csv(
        os.path.join(inputs_case, 'val_r.csv'), squeeze=True, header=None).tolist()

#%%### FUNCTIONS
def get_season_peaks(load_hourly_local, hierarchy, h_dt_szn, tzmap, reeds_data_year, sw):
    """
    """
    ### Convert to uniform timezone
    tzshift = tzmap.map({'PT':+3,'MT':+2,'CT':+1,'ET':0})
    load_hourly_aligned = load_hourly_local.drop(['szn','h'], axis=1, errors='ignore').copy()
    for r in load_hourly_aligned:
        load_hourly_aligned[r] = np.roll(load_hourly_aligned[r], tzshift[r])
        # ### Roll everything by 1 since start_1am = 1 ???
        # load_hourly_aligned[r] = np.roll(load_hourly_aligned[r], -1, axis=0)
    ### Downselect to reeds_data_year if necessary
    if len(load_hourly_aligned) > 8760:
        load_hourly_aligned = load_hourly_aligned.loc[
            h_dt_szn.loc[h_dt_szn.t==reeds_data_year].index]
    load_hourly_aligned.index = h_dt_szn.loc[h_dt_szn.t==reeds_data_year, 'timestamp']
    #%% Aggregate demand by GSw_PRM_hierarchy_level
    load_hourly_agg = (
        load_hourly_aligned
        ## Map BA to GSw_PRM_hierarchy_level
        .rename(columns=hierarchy[sw.GSw_PRM_hierarchy_level])
        ## Sum by GSw_PRM_hierarchy_level
        .groupby(axis=1, level=0).sum()
    )
    ### Get the peak hour by season
    peakhour_agg_byseason = (
        load_hourly_agg
        .assign(szn=load_hourly_agg.index.map(h_dt_szn.set_index('timestamp').szn))
        .groupby('szn').idxmax()
    )
    #%% Get the BA demand during the peak hour of the associated GSw_PRM_hierarchy_level
    peak_out = {}
    for r in load_hourly_aligned:
        for szn in peakhour_agg_byseason.index:
            peak_out[r,szn] = load_hourly_aligned.loc[
                peakhour_agg_byseason.loc[szn, hierarchy[sw.GSw_PRM_hierarchy_level][r]],
                r
            ]
    peak_out = pd.Series(peak_out).unstack()
    peak_out.index.name = 'r'
    peak_out.columns.name = 'szn'

    return peak_out


def get_timeslice_peaks(
        load_hourly_local, hierarchy, h_dt_szn, tzmap, reeds_data_year, numhours, sw,
    ):
    """
    """
    ### Input formatting
    timeslices = numhours.index
    tzshift = tzmap.map({'PT':+3,'MT':+2,'CT':+1,'ET':0})
    ### Convert to uniform timezone
    load_hourly_aligned = load_hourly_local.drop(['szn','h'], axis=1, errors='ignore').copy()
    for r in load_hourly_aligned:
        load_hourly_aligned[r] = np.roll(load_hourly_aligned[r], tzshift[r])
        # ### Roll everything by 1 since start_1am = 1 ???
        # load_hourly_aligned[r] = np.roll(load_hourly_aligned[r], -1, axis=0)
    ### Downselect to reeds_data_year if necessary
    if len(load_hourly_aligned) > 8760:
        load_hourly_aligned = load_hourly_aligned.loc[
            h_dt_szn.loc[h_dt_szn.t==reeds_data_year].index]
    load_hourly_aligned.index = h_dt_szn.loc[h_dt_szn.t==reeds_data_year, 'timestamp']
    #%% Aggregate demand by GSw_PRM_hierarchy_level
    load_hourly_agg = (
        load_hourly_aligned
        ## Map BA to GSw_PRM_hierarchy_level
        .rename(columns=hierarchy[sw.GSw_PRM_hierarchy_level])
        ## Sum by GSw_PRM_hierarchy_level
        .groupby(axis=1, level=0).sum()
    )
    ### Timeslices break down when GSw_PRM_hierarchy_level includes BAs in different timezones.
    ### Here we assign a timezone to each GSw_PRM_hierarchy_level based on the most common
    ### timezone among the BAs represented by GSw_PRM_hierarchy_level.
    ### It would probably be better to weight the BAs by average demand.
    ### But it's even better to just use hourly resolution in a uniform timezone.
    #%% Get most common timezone for each GSw_PRM_hierarchy_level
    prmreg2tz = hierarchy[sw.GSw_PRM_hierarchy_level].to_frame()
    prmreg2tz.index.name = None
    prmreg2tz['tz'] = prmreg2tz.index.map(tzmap)
    prmreg2tz = pd.Series(dict(
        prmreg2tz
        ## Get number of occurrences of timezone
        .groupby(sw.GSw_PRM_hierarchy_level).tz.value_counts()
        ## Get index with the highest number of occurrences
        .groupby(sw.GSw_PRM_hierarchy_level).idxmax().values
        ## Convert to hours to shift
    )).map({'PT':+3,'MT':+2,'CT':+1,'ET':0})
    #%% Get the hour associated with the peak demand in each GSw_PRM_hierarchy_level by timeslice
    ### in the dominant timezone for that GSw_PRM_hierarchy_level
    peakhour_agg_bytimeslice = {}
    for ragg in load_hourly_agg:
        ### Add the timeslices
        load_hourly_agg_h = (
            load_hourly_agg[[ragg]]
            .assign(h=load_hourly_agg.index.map(h_dt_szn.set_index('timestamp').h))
        )
        ### Shift to uniform timezone to match the timestamp
        ### (have to do so since timeslices are defined in local time)
        load_hourly_agg_h['h'] = np.roll(load_hourly_agg_h['h'], prmreg2tz[ragg])
        ### Get the peak hours for the normal timeslices and create an empty row for peak timeslices
        peakhour_agg_bytimeslice[ragg] = load_hourly_agg_h.groupby('h').idxmax().reindex(timeslices)
        ### Now the subset timeslices
        for peakslice, parentslice in slicetree.items():
            ### Take peak from the top hour of parent
            peakhour_agg_bytimeslice[ragg].loc[peakslice,ragg] = (
                load_hourly_agg_h.loc[load_hourly_agg_h.h==parentslice, ragg]
                .idxmax()
            )
            ### Overwrite parent based on the remaining hours in parent
            peakhour_agg_bytimeslice[ragg].loc[parentslice,ragg] = (
                load_hourly_agg_h.loc[load_hourly_agg_h.h==parentslice, ragg]
                .nsmallest(numhours[parentslice])
                .idxmax()
            )
    peakhour_agg_bytimeslice = pd.concat(peakhour_agg_bytimeslice, axis=1).droplevel(0, axis=1)

    #%% Get the BA demand during the peak hour of the associated GSw_PRM_hierarchy_level
    peak_h = {}
    for r in load_hourly_aligned:
        for h in peakhour_agg_bytimeslice.index:
            peak_h[r,h] = load_hourly_aligned.loc[
                peakhour_agg_bytimeslice.loc[h, hierarchy[sw.GSw_PRM_hierarchy_level][r]],
                r
            ]
    peak_h = pd.Series(peak_h)
    peak_h.index = peak_h.index.rename(('r','h'))

    return peak_h


#%%### Calculate timeslice-average and -peak load from hourly load
###### Load additional inputs
### Get the number of hours per timeslice
numhours = pd.read_csv(
    os.path.join(reeds_dir,'inputs','numhours.csv'),
    header=0, names=['h','numhours'], index_col='h', squeeze=True)

# Get fraction of timeslice split off
slicefrac = pd.merge(
    pd.DataFrame(slicetree.items(), slicetree.values())
      .reset_index()
      .melt(id_vars='index', )
      .drop('variable', axis=1),
    numhours, right_on='h', left_on='value'
    )
slicefrac = (
    pd.merge(slicefrac, slicefrac.groupby('index')['numhours'].sum(),
             on='index', suffixes=['','_tot'])
    .rename(columns={'value':'h'})
    )
slicefrac['frac'] = slicefrac['numhours'] / slicefrac['numhours_tot']
### Get the timezone map, convert everything to shifts relative to eastern time
tzmap = pd.read_csv(
    os.path.join(reeds_dir,'inputs','variability','reeds_ba_tz_map.csv'),
    index_col='r', squeeze=True,
)[val_r]
### Get the region hierarchy
hierarchy = pd.read_csv(
    os.path.join(inputs_case,'hierarchy.csv')
).rename(columns={'*r':'r'}).set_index('r')
hierarchy['r'] = hierarchy.index

### Get the hour-mapper
h_dt_szn = (
    pd.read_csv(os.path.join(reeds_dir,'inputs','variability','h_dt_szn.csv'), index_col='hour')
    .replace({'winter':'wint','spring':'spri','summer':'summ'})
    .rename(columns={'season':'szn','year':'t',})
)
h_dt_szn['timestamp'] = pd.concat([
    pd.Series(
        index=pd.date_range(f'{y}-01-01', f'{y+1}-01-01', freq='h', closed='left')[:8760],
        dtype=float)
    for y in range(2007,2014)
]).index


#%%### Calculate peak load by season and timeslice for non-default (EFS-like) demand
### NOTE: The summer peak timeslice (h17) is defined by BA, so corresponds to different hours
### for different BAs. But we need the hour of the peak demand by GSw_PRM_hierarchy_level.
### For this purpose, we calculate the h17 hours by GSw_PRM_hierarchy_level instead of by BA.
### That's inconsistent with the treatment of average load. But the peak timeslice doesn't
### make sense for tranmsission anyway (since different BAs peak during different hours,
### transmission flows during h17 are not physical), so this problem will always apply to h17.
if sw.GSw_EFS1_AllYearLoad == 'historic':
    #%% Get the 7-year hourly demand, downselect to reeds_data_year
    load_hourly_local = pd.read_hdf(
        os.path.join(reeds_dir,'inputs','loaddata','historic_load_hourly.h5'))[val_r]
    load_hourly_local.columns.name = 'r'
    load_hourly_local['t'] = load_hourly_local.index.map(h_dt_szn.t)
    load_hourly_local = load_hourly_local.loc[
        load_hourly_local.t==reeds_data_year].drop(['t'],axis=1).copy()

    #%% Calculate the timeslice-average demand by region for the base year, save as load_2010.csv
    load_hourly_local['szn'] = load_hourly_local.index.map(h_dt_szn.szn)
    load_hourly_local['h'] = load_hourly_local.index.map(h_dt_szn.h)

    load_2010 = (
        load_hourly_local
        ### Drop extra columns, take the mean by timeslice
        .drop(['szn'], axis=1).groupby('h').mean()
        ### Add peak rows, which we fill below
        .append(pd.DataFrame(index=list(slicetree.keys())))
    )
    load_2010.index.name = 'h'
    load_2010.columns.name = 'r'
    ### Loop over peak slices (e.g. h17), get peak and (parent-peak) averages
    for peakslice, parentslice in slicetree.items():
        for r in load_2010.columns:
            ### Take peakslice (e.g. h17) from the top hours of parent slice (e.g. h3)
            load_2010.loc[peakslice,r] = (
                load_hourly_local.loc[load_hourly_local.h==parentslice,r]
                .nlargest(numhours[peakslice]).mean())
            ### Overwrite parent slice with average over the remaining hours in parent slice
            ### Note that numhours already includes the correct number of hours (e.g. h3: 268-40=228)
            load_2010.loc[parentslice,r] = (
                load_hourly_local.loc[load_hourly_local.h==parentslice,r]
                .nsmallest(numhours[parentslice]).mean()
            )

    #%%### Calculate load for all modeled years by scaling by load_multiplier
    ### load multiplier by cendiv
    load_multiplier = pd.read_csv(
        os.path.join(inputs_case,'load_multiplier.csv'), index_col='cendiv')
    load_multiplier.columns = load_multiplier.columns.astype(int)
    ### map to regions
    load_multiplier_r = hierarchy[['cendiv']].merge(
        load_multiplier, left_on='cendiv', right_index=True).drop('cendiv', axis=1)
    load_multiplier_r.index = load_multiplier_r.index.rename('r')

    ### Scale load_2010 by load_multiplier
    load_allyear = load_multiplier_r.multiply(load_2010.unstack('h'), axis=0).reset_index()

    ###### Peak demand, scaled up by load_multiplier
    #%% Get the BA demand during the peak hour of the associated GSw_PRM_hierarchy_level
    peak_szn = (
        get_season_peaks(
            load_hourly_local, hierarchy, h_dt_szn, tzmap, reeds_data_year, sw)
        .stack().rename('MW').to_frame().assign(t=2010).reset_index()
    )
    ### Scale up by load_multiplier
    peak_szn = (
        load_multiplier_r.multiply(peak_szn.set_index(['r','szn']).MW, axis=0)
        .stack().rename('MW').reset_index()
        .rename(columns={'r':'*r', 'level_2':'t'})
    )

    #%% Calculate peak demand by timeslice
    peak_h = get_timeslice_peaks(
        load_hourly_local, hierarchy, h_dt_szn, tzmap, reeds_data_year, numhours, sw,
    )
    ### Scale up by load_multiplier
    peak_h = load_multiplier_r.multiply(peak_h, axis=0)

else:
    # Just use the input data directly; don't scale it by inputs/variability.
    ### Get timeslice load directly
    load_allyear = pd.read_csv(
        os.path.join(reeds_dir, 'inputs','loaddata',f'{sw.GSw_EFS1_AllYearLoad}load.csv'))

    ### Get hourly load, used to calculate peak demand
    load_hourly_local_byyear = LDC_prep.read_file(
        os.path.join(
            reeds_dir ,'inputs', 'loaddata', f'{sw.GSw_EFS1_AllYearLoad}_load_hourly'),
        index_columns=(
            2 if (('EER' not in sw.GSw_EFS1_AllYearLoad) and (sw.GSw_EFS1_AllYearLoad != 'historic'))
            else 1)
    )[val_r]
    if 'year' in load_hourly_local_byyear:
        load_hourly_local_byyear = load_hourly_local_byyear.set_index(['year','hour'])
    years = load_hourly_local_byyear.index.get_level_values('year').unique()
    ### Get peak demand by year and season
    peak_szn = {}
    for year in years:
        peak_szn[year] = get_season_peaks(
            load_hourly_local_byyear.loc[year], hierarchy, h_dt_szn, tzmap, reeds_data_year, sw
        ).stack()
    peak_szn = (
        pd.concat(peak_szn, axis=0, names=('t','r','szn')).rename('MW')
        .reset_index().rename(columns={'r':'*r'})
        [['*r','szn','t','MW']]
    )
    ### Get peak demand by year and timeslice
    peak_h = {}
    for year in years:
        peak_h[year] = get_timeslice_peaks(
            load_hourly_local_byyear.loc[year], hierarchy, h_dt_szn, tzmap,
            reeds_data_year, numhours, sw)
    peak_h = pd.concat(peak_h, axis=1)

### Reshape to long format
peak_h = peak_h.stack().rename_axis(['*r','h','t']).rename('MW')

#%% Read in the flexibility inputs; if flexibility is not turned on, load in
#   the reference case as a placeholder
if int(sw.GSw_EFS_Flex) > 0:
        #load in the %GSw_EFS_AllYearLoad%_%GSw_EFS_Case%_frac.csv file
        flex_data = pd.read_csv(
            os.path.join(reeds_dir, 'inputs','loaddata','{}_frac.csv'.format(sw.GSw_EFS2_FlexCase)))
elif int(sw.GSw_EFS_Flex) == 0:
    flex_data = pd.read_csv(
        os.path.join(reeds_dir, 'inputs','loaddata','EPREFERENCE_Baseflex_frac.csv'))
    for col in flex_data.columns:
        #if the value is a number, replace it with zero
        if np.issubdtype(flex_data[col].dtype, np.number):
            flex_data[col].values[:] = 0

dr_profile_increase = pd.read_csv(
    os.path.join(reeds_dir, 'inputs','demand_response',f'dr_increase_profile_{sw.drscen}.csv'))
dr_profile_decrease = pd.read_csv(
    os.path.join(reeds_dir, 'inputs','demand_response',f'dr_decrease_profile_{sw.drscen}.csv'))
dr_data1 = pd.read_csv(
    os.path.join(reeds_dir, 'inputs','demand_response',f'dr_increase_{sw.drscen}.csv'))
dr_data2 = pd.read_csv(
    os.path.join(reeds_dir, 'inputs','demand_response',f'dr_decrease_{sw.drscen}.csv'))

# Filter by regions
dr_profile_increase = dr_profile_increase.loc[:,dr_profile_increase.columns.isin(['i','hour','year'] + val_r)]
dr_profile_decrease = dr_profile_decrease.loc[:,dr_profile_decrease.columns.isin(['i','hour','year'] + val_r)]
dr_data1 = dr_data1.loc[dr_data1['r'].isin(val_r)]
dr_data2 = dr_data2.loc[dr_data1['r'].isin(val_r)]


#%% If Using DR, adjust data for H17
if int(sw.GSw_DR) > 0:
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

#%% Filter by valid regions
load_allyear = load_allyear.loc[load_allyear['r'].isin(val_r)]
flex_data = (
    flex_data.loc[flex_data['r'].isin(val_r)]
    .rename(columns={'timeslice':'h'})
    .set_index(['flextype','r','h'])
    .stack().rename_axis(['*flextype','r','h','t'])
    .rename('MW')
)

#%% Canadian exports: spread equally over timeslices by quarter
can_exports_szn_frac = pd.read_csv(
    os.path.join(reeds_dir, 'inputs', 'canada_imports', 'can_exports_szn_frac.csv'),
    header=0, names=['szn','frac'],
)
h_szn = pd.read_csv(
    os.path.join(reeds_dir,'inputs','variability','h_szn.csv'),
    header=0, names=['h','szn'], index_col='h', squeeze=True,
)
df = can_exports_szn_frac.merge(h_szn.reset_index(), on='szn')
## Calculate the fraction of year hours represented by each timeslice by scaling
## the season frac (frac) by the fraction of the season that the timeslice represents
## (hours / hours_per_szn)
df['hours'] = df.h.map(numhours)
df['hours_per_szn'] = (
    df.szn.map(df.groupby('szn').hours.sum()))
df['frac_weighted'] = (
    df.frac * df.hours / df.hours_per_szn)
can_exports_h_frac = df[['h','frac_weighted']].rename(columns={'h':'*h'})

#%% Write outputs
load_allyear.round(decimals).rename(columns={'timeslice':'h'}).to_csv(
    os.path.join(inputs_case,'load_allyear.csv'),index=False)
peak_h.round(decimals).to_csv(os.path.join(inputs_case,'peak_h.csv'))
peak_szn.round(decimals).rename(columns={'season':'szn'}).to_csv(
    os.path.join(inputs_case,'peak_szn.csv'),index=False)
flex_data.round(decimals).to_csv(
    os.path.join(inputs_case,'flex_frac_all.csv'))
dr_profile_increase.to_csv(
    os.path.join(inputs_case,'dr_inc.csv'),index=False)
dr_profile_decrease.to_csv(
    os.path.join(inputs_case,'dr_dec.csv'),index=False)
dr_data1.to_csv(
    os.path.join(inputs_case,'dr_increase.csv'),index=False, header=False)
dr_data2.to_csv(
    os.path.join(inputs_case,'dr_decrease.csv'),index=False, header=False)
if sw.GSw_EFS1_AllYearLoad == 'historic':
    load_multiplier_r.stack().rename_axis(['r','t']).rename('mulitplier').round(decimals).to_csv(
        os.path.join(inputs_case,'load_multiplier_r.csv'))
can_exports_h_frac.round(decimals).to_csv(
    os.path.join(inputs_case, 'can_exports_h_frac.csv'), index=False)

toc(tic=tic, year=0, process='input_processing/all_year_load.py', 
    path=os.path.join(inputs_case,'..'))
