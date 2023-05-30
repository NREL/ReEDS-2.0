#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

The purpose of this script is to collect 8760 data as it is output by
hourlize and perform a temporal aggregation to produce load and capacity 
factor parameters for the representative days that will be read by ReEDS. 
The other outputs are the hours/seasons to be modeled in ReEDS and linking 
sets used in the model.

The full set of outputs is at the very end of the file.

As a note, this script can also adjust time zones for ReEDS inputs. This
assumes that the outputs from hourlize are in 'local' time - implying
inputs will need to be shifted such that the sun doesn't rise everywhere
at the same time.

General notes:
* h: a timeslice with an h prefix, starting at h1
* hour: an hour of the full period, starting at 1 ([1-8760] for 1 year or [1-61320] for 7 years)
* dayhour: a clock hour starting at 1 [1-24]
* period: a day (if GSw_HourlyType=='day') or a wek (if GSw_HourlyType=='wek')
* wek: A consecutive 5-day period (365 is only divisible by 1, 5, 73, and 365)

TODO:
* Add compatibility with climate impacts (climateprep.py)
* Add compatibility with beyond-2050 modeling (forecast.py)
# Add compatibility with flexible demand

"""

#%% IMPORTS
import os
import sys
import math
import argparse
import logging
import shutil
## Turn off logging for imported packages
for i in ['matplotlib']:
    logging.getLogger(i).setLevel(logging.CRITICAL)
import json
import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.neighbors import NearestCentroid
import scipy
from scipy.cluster.vq import vq
from LDC_prep import read_file

##% Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()


##########
#%% INPUTS
select_year = 2012
decimals = 3
### Indicate whether to show plots interactively [default False]
interactive = False
### Indicate whether to save the old h17 inputs for comparison
debug = True

#############
#%% FUNCTIONS
def collect_regions(val_r,rs):
    rs = list(rs[rs["r"].isin(val_r)]["rs"])

    r_subset = val_r.copy()
    for x in rs:
        r_subset.append(x)

    return r_subset


def szn2yearperiod(szn):
    """
    szn's are formatted as 'y{20xx}{d or w}{day of year or wek of year}'
    where a 'wek' is a 5-day period (5*73 = 365)
    """
    year, period = szn.split('d') if 'd' in szn else szn.split('w')
    return int(year.strip('y')), int(period)


def szn2period(szn):
    """
    szn's are formatted as 'y{20xx}{d or w}{day of year or wek of year}'
    where a 'wek' is a 5-day period (5*73 = 365)
    """
    year, period = szn.split('d') if 'd' in szn else szn.split('w')
    return int(period)


###################################
# -- Capacity Factor Processing --
###################################

def convert_input(basedir, tech, siting, GSw_HourlyClusterMultiYear, select_year=2012):
    ##! TODO: It would be faster and easier to load these from inputs_case/recf.h5
    ### import resource variability data
    data_input = read_file(
        os.path.join(
            basedir, "inputs", "variability", "multi_year",
            "{}{}".format(tech, '' if not siting else '-' + siting))
    ).fillna(0)
    ### Get year map and add year to resource data
    h_dt_szn = pd.read_csv(os.path.join(basedir,'inputs','variability','h_dt_szn.csv'))
    data_input['year'] = data_input.index.map(h_dt_szn.set_index('hour').year)

    ### Subset to single year if necessary
    if int(GSw_HourlyClusterMultiYear) == 0:
        data_input = data_input[data_input['year']==select_year]

    ### Create hour-of-year index
    data_input['h'] = ['h'+str(i+1) for i in range(8760)] * int(len(data_input.index) / 8760)

    ### Columns are {class}_{r}; create maps to pull out i ({tech}_{class}) and r values
    data_input = data_input.set_index(['year','h'])
    col2i = {c: tech + '_' + c.split('_')[0] for c in data_input}
    col2r = {c: c.split('_')[1] for c in data_input}

    ### melt into long format and create i,r columns
    result = (
        data_input.stack().round(4).rename('value')
        .reset_index().rename(columns={'level_2':'i_r'})
    )
    result = (
        result
        .assign(i=result.i_r.map(col2i))
        .assign(r=result.i_r.map(col2r))
    )[['i','r','year','h','value']].copy()

    return result


def make_equal_periods(numperiods):
    '''
    Create referencing table that has columns ['hour','dayhour,'season'].
    This is useful to merge with load data and m_cf data to find seasonal 
    average later when using the equal_periods method to divide up the year
    into `numperiods` seasons of equal duration.

    arg: 
    numperiods: number of periods to divide 365 days into
    period_length: 24 for day, 168 for week

    return: pandas dataframe
    '''
    df_season = []
    remainder = 365 % numperiods
    for this_clust in range(1,numperiods + 1): 
        # distribute one extra day to each cluster until any remainder's gone
        if remainder > 0:
            days_in_this_period = math.floor(365/numperiods) + 1
            remainder -= 1
        else:
            days_in_this_period = math.floor(365/numperiods)
        df_season = df_season + ['szn' + str(this_clust)] * days_in_this_period * 24

    # roll months to center clusters on midnight Jan. 1 (such that when
    # numperiods == 4, szn1 reflects winter) if season is odd number of days,
    # have to have one more day on one side of the year than the other
    if sum([ 1 for x in df_season if x == 'szn1' ])/24 % 2 > 0:
        df_season = np.roll(df_season,-int(sum([ 1 for x in df_season if x == 'szn1' ])/2 - 12))
    else:
        df_season = np.roll(df_season,-int(sum([ 1 for x in df_season if x == 'szn1' ])/2))

    df = pd.DataFrame({
        'day': [y for x in range(1,366) for y in (x,)*24],
        'wek': [y for x in range(1,74) for y in (x,)*120],
        'hour': [f'h{h}' for h in range(1,8761)],
        'season': df_season,
        # add hours h01:h24
        'dayhour': list(range(1,25))*365,
        'wekhour': list(range(1,121))*73,
        # add morning, afternoon, evening, postmidnight (just for plotting comparison with h17)
        'period': (
            ['overnight']*6 + ["morning"]*7 + ["afternoon"]*4 + ["evening"]*5 + ['overnight']*2
        ) * 365,
    })

    return df


########################
# -- Load Processing --
########################

def create_load(val_r, sw, inputs_case, select_year=2012):
    load = read_file(
        os.path.join(inputs_case,'load'), index_columns=2,
    ### Subset to modeled regions
    )[val_r]
    ### Subset to cluster year; if it's not included, keep the latest year
    loadyears = load.index.get_level_values('year').unique()
    keepyear = (
        int(sw['GSw_HourlyClusterYear']) if int(sw['GSw_HourlyClusterYear']) in loadyears
        else max(loadyears))
    load = load.loc[keepyear].copy()
    ### load.h5 is busbar load, but b_inputs.gms ingests end-use load, so scale down by distloss
    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, usecols=[0,1], index_col=0, squeeze=True)
    load *= (1 - scalars['distloss'])
    ### If necessary, make 7 copies to line up with the 7 years of VRE data
    if ('EER' not in sw.GSw_EFS1_AllYearLoad) and ('historic' not in sw.GSw_EFS1_AllYearLoad):
        load = pd.concat([load]*7, axis=0, ignore_index=True)

    # Add year and hour indices
    load = (
        load
        .assign(year=np.ravel([[y]*8760 for y in range(2007,2014)]))
        .assign(hour=np.ravel([['h{}'.format(i) for i in range(1,8761)] for y in range(2007,2014)]))
    )

    #organize the data for gams to read in as a table with hours in 
    # the first column and regions in the proceeding columns.
    # Here, we keep the "year" column for use in the clustering.
    cols = ['year','hour'] + val_r

    #subset load based on GSw_HourlyClusterMultiYear switch
    if int(sw['GSw_HourlyClusterMultiYear'])==0:
        load = load[load['year']==select_year].reset_index(drop=True)

    load_out = pd.melt(load[cols],id_vars=['year','hour'])
    load_out.columns = ['year','hour','r','value']

    return load_out


def create_timeslice_profiles(cf_representative, load_representative, val_r, rs, sw):

    regions = collect_regions(val_r,rs)

    ### Downselect to modeled regions
    cf_rep = cf_representative[cf_representative['region'].isin(regions)].copy()
    load_rep = load_representative[load_representative['region'].isin(val_r)]

    ### As in cfgather.py, we duplicate the csp1 profiles for each CSP tech
    cfcsp = cf_rep.loc[cf_rep.property.str.startswith('csp')].copy()
    cfcsp['resource_class'] = cfcsp.property.map(lambda x: int(x.split('_')[1]))
    cfcsp = pd.concat([
        cfcsp.assign(property=cfcsp.property.str.replace('csp',f'csp{i}'))
        for i in sw['GSw_CSP_Types']
    ])

    ### csp-ns profile is copied from the best csp profile in each region
    r2class = (
        cfcsp.loc[cfcsp.property.str.startswith('csp1'), ['resource_class','region']]
        ## csp class number increases with resource quality, so keep the highest-numbered
        ## resource class in each region
        .sort_values('resource_class').drop_duplicates(subset=['region'], keep='last')
        .set_index('region').resource_class)
    r2class = 'csp1_' + r2class.astype(str)
    cfcspns = cfcsp.loc[
        (cfcsp.tech=='csp')
        & (cfcsp.region.map(r2class)==cfcsp.property)
    ].assign(property='csp-ns')
    ### Drop the original 'csp' profile and append the duplicated CSP profiles to rest of cf's
    cf_rep = pd.concat([cf_rep.loc[cf_rep.tech != 'csp'], cfcsp, cfcspns])

    cf_rep = (
        cf_rep.rename(columns={'region':'r', 'property':'i', 'hour':'h', 'value':'cf'})
        [['i','r','h','cf']])
    load_rep = (
        load_rep.rename(columns={'region':'r','hour':'h'})
        [['h','r','value']])

    return cf_rep, load_rep


def make_8760_map(period_szn, select_year, sw):
    """
    """
    hoursperperiod = {'day':24, 'wek':120, 'year':np.nan}[sw['GSw_HourlyType']]
    periodsperyear = {'day':365, 'wek':73, 'year':np.nan}[sw['GSw_HourlyType']]
    # create the reference season
    hmap_1yr = pd.DataFrame({
        'year': select_year,
        'day': (
            [y for x in range(1,366) for y in (x,)*24] if sw['GSw_HourlyType'] == 'year'
            else [y for x in range(1,periodsperyear+1) for y in (x,)*hoursperperiod]),
        'hour': range(1,8761),
        'season': (
            np.ravel([[x]*24 for x in period_szn]) if sw['GSw_HourlyType'] == 'year'
            else np.ravel([[x]*hoursperperiod for x in period_szn])),
        'periodhour': (
            list(range(1,25))*365 if sw['GSw_HourlyType'] == 'year'
            else list(range(1,hoursperperiod+1))*periodsperyear),
    })
    ### create the timestamp index: y{20xx}d{xxx}h{xx} (left-padded with 0)
    if sw['GSw_HourlyType'] == 'year':
        ### If using a chronological year (i.e. 8760) the day index uses actual days
        hmap_1yr['h'] = (
            f'y{select_year}'
            + 'd' + hmap_1yr.day.astype(str).map('{:>03}'.format)
            + 'h' + hmap_1yr.periodhour.astype(str).map('{:>03}'.format)
        )
    else:
        ### If using representative periods (days/weks) the period index uses
        ### representative periods, which are in the 'season' column
        hmap_1yr['h'] = (
            hmap_1yr.season
            + 'h' + hmap_1yr.periodhour.astype(str).map('{:>03}'.format)
        )

    ### Keep actual h and period for postprocessing
    hmap_1yr['actual_period'] = (
        f'y{select_year}'
        + sw['GSw_HourlyType'][0] + hmap_1yr.day.astype(str).map('{:>03}'.format)
    )
    hmap_1yr['actual_h'] = (
        hmap_1yr.actual_period
        + 'h' + hmap_1yr.periodhour.astype(str).map('{:>03}'.format)
    )

    ### Create the 7-year version for Augur
    hmap_7yr = pd.concat(
        {y: hmap_1yr.drop('year', axis=1) for y in range(2007,2014)}, names=('year',),
        axis=0,
    ).reset_index(level='year').reset_index(drop=True)
    hmap_7yr['hour'] = range(1, 8760*7+1)
    for col in ['actual_period', 'actual_h']:
        hmap_7yr[col] = 'y' + hmap_7yr.year.astype(str) + hmap_7yr[col].str[5:]

    return hmap_7yr, hmap_1yr


def duplicate_r_rs(df,mapper):
    dfm = pd.merge(mapper,df,on="r",how="left")
    #!!!! missing maps for some regions in eastern canada
    dfm.loc[pd.isnull(dfm['tz']), 'tz'] = 'ET'
    #drop the 'r' columns and rename 'rs' to 'r'
    dfm = dfm.drop('r',axis=1).rename(columns={'rs':'r'})
    #stack the original and now-rs dataframes
    df_out = pd.concat([df,dfm])

    return df_out


def get_season_peaks_hourly(load, sw, hierarchy, hour2szn):
    ### Aggregate demand by GSw_PRM_hierarchy_level
    load_agg = (
        load
        .assign(region=load.r.map(hierarchy[sw['GSw_PRM_hierarchy_level']]))
        ###! Assuming we have only one year; change if we use multiple years
        .groupby(['hour','region']).MW.sum()
        .unstack('region').reset_index()
    )
    ### Get the peak hour by season
    load_agg['szn'] = load_agg.hour.map(hour2szn)
    peakhour_agg_byseason = load_agg.set_index('hour').groupby('szn').idxmax()
    #%% Get the BA demand during the peak hour of the associated GSw_PRM_hierarchy_level
    seasons = hour2szn.unique()
    peak_out = {}
    for r in load.r.unique():
        load_r = load.loc[load.r==r].set_index('hour').MW
        peak_szn = peakhour_agg_byseason[hierarchy.loc[r,sw['GSw_PRM_hierarchy_level']]]
        for szn in seasons:
            peak_out[r,szn] = float(load_r[peak_szn[szn]])
    peak_out = (
        pd.Series(peak_out).rename('MW')
        .reset_index().rename(columns={'level_0':'r','level_1':'szn'}))
    return peak_out


def optimize_period_weights(profiles_fitperiods, numclusters=100, select_year=2012):
    """
    The optimization approach (minimizing sum of absolute errors) is described at
    https://optimization.mccormick.northwestern.edu/index.php/Optimization_with_absolute_values
    The general idea of optimizing period weights to reproduce regional variability is similar
    to the method used in the EPRI US-REGEN model, described at
    https://www.epri.com/research/products/000000003002016601
    """
    #%% Imports
    import pulp

    #%% Input processing
    profiles_day = (
        profiles_fitperiods.loc[select_year].groupby(['property','region'], axis=1).mean())
    profiles_mean = profiles_day.mean()
    numdays = len(profiles_day)
    days = profiles_day.index.values

    #%% Optimization: minimize sum of absolute errors
    m = pulp.LpProblem('LinearDaySelection', pulp.LpMinimize)
    ###### Variables
    ### day weights
    WEIGHT = pulp.LpVariable.dicts('WEIGHT', (d for d in days), lowBound=0, cat='Continuous')
    ### errors
    ERROR_POS = pulp.LpVariable.dicts(
        'ERROR_POS', (c for c in profiles_day.columns), lowBound=0, cat='Continuous')
    ERROR_NEG = pulp.LpVariable.dicts(
        'ERROR_NEG', (c for c in profiles_day.columns), lowBound=0, cat='Continuous')
    ###### Constraints
    ### weights must sum to 1
    m += pulp.lpSum([WEIGHT[d] for d in days]) == 1
    ### definition of errors
    for c in profiles_day.columns:
        m += (
            ### Full error for column (given by positive component minus negative component)...
            ERROR_POS[c] - ERROR_NEG[c]
            ### ...plus sum of values for weighted representative days...
            + pulp.lpSum([WEIGHT[d] * profiles_day[c][d] for d in days])
            ### ...equals the mean for that column
            == profiles_mean[c])
    ###### Objective: minimize the sum of absolute values of errors across all columns
    m += pulp.lpSum([
        ERROR_POS[c] + ERROR_NEG[c]
        for c in profiles_day.columns
    ])

    #%% Solve it
    m.solve(solver=pulp.PULP_CBC_CMD(msg=True))

    ### Collect weights, scaled by total number of days
    weights = pd.Series({d:WEIGHT[d].varValue for d in days}) * numdays

    #%% Truncate based on numclusters, scale appropriately, and convert to integers
    ### Keep the the 'numclusters' highest-weighted days
    rweights = (weights.sort_values(ascending=False)[:numclusters].iloc[::-1])
    ### Scale so that the weights sum to numdays (have to do if numclusters is small)
    rweights *= numdays / rweights.sum()
    ### Sort from smallest to largest and convert to integers
    iweights = rweights.iloc[::-1].round(0).astype(int)
    sumweights = iweights.sum()
    diffweights = sumweights - numdays
    ### Add or drop days as necessary to sum to numdays
    if diffweights < 0:
        ### Scale it up little by little until it sums to 365
        for i in range(1000000):
            iweights = (rweights.iloc[::-1]*(1+0.00001*i)).round(0).astype(int)
            sumweights = iweights.sum()
            diffweights = sumweights - numdays
            if diffweights >= 0:
                break
    elif diffweights > 0:
        for d in iweights.index:
            if iweights[d] >= diffweights:
                ### Just subtract diffweights from the smallest weight and stop
                iweights[d] -= diffweights
                break
            else:
                ### Subtract the whole value of the smallest weight, then keep going
                diffweights -= iweights[d]
                iweights[d] = 0

    iweights = iweights.replace(0,np.nan).dropna().astype(int).iloc[::-1]
    ### Make sure it worked
    if iweights.sum() != numdays:
        raise ValueError(f'Sum of rounded weights = {iweights.sum()} != {numdays}')

    return profiles_day, iweights


def assign_representative_days(profiles_day, rweights):
    """
    """
    #%% Imports
    import pulp

    #%% Input processing
    actualdays = profiles_day.index.values
    repdays = list(rweights.index)

    #%% Optimization: minimize sum of absolute errors
    m = pulp.LpProblem('RepDayAssignment', pulp.LpMinimize)
    ###### Variables
    ### Weighting of rep days (r) for each actual day (a).
    ### Can only use whole days, so it's a binary variable.
    WEIGHT = pulp.LpVariable.dicts(
        'WEIGHT', ((a,r) for a in actualdays for r in repdays),
        lowBound=0, upBound=1, cat=pulp.LpInteger)
    ### Errors. These are defined for features (c) and for actual days (a).
    ERROR_POS = pulp.LpVariable.dicts(
        'ERROR_POS', ((a,c) for a in actualdays for c in profiles_day.columns),
        lowBound=0, cat='Continuous')
    ERROR_NEG = pulp.LpVariable.dicts(
        'ERROR_NEG', ((a,c) for a in actualdays for c in profiles_day.columns),
        lowBound=0, cat='Continuous')
    ###### Constraints
    ### Each actual day can only be assigned to one representative day
    for a in actualdays:
        m += pulp.lpSum([WEIGHT[a,r] for r in repdays]) == 1
    ### Each representative day must be used a number of times equal to its weight
    for r in repdays:
        m += pulp.lpSum([WEIGHT[a,r] for a in actualdays]) == rweights[r]
    ### Define the error variables
    for a in actualdays:
        for c in profiles_day.columns:
            m += (
                ### Full error for column on actual day (given by positive
                ### component minus negative component)...
                ERROR_POS[a,c] - ERROR_NEG[a,c]
                ### ...plus value for its representative day (since WEIGHT is binary)...
                + pulp.lpSum([WEIGHT[a,r] * profiles_day[c][r] for r in repdays])
                ### ...equals the actual value for that column and day
                == profiles_day[c][a])
    ###### Objective: minimize the sum of absolute values of errors
    m += pulp.lpSum([
        ERROR_POS[a,c] + ERROR_NEG[a,c]
        for a in actualdays for c in profiles_day.columns
    ])

    #%% Solve it
    m.solve(solver=pulp.PULP_CBC_CMD(msg=True))

    ### Collect assignments
    assignments = pd.Series(
        {(a,r):WEIGHT[a,r].varValue for a in actualdays for r in repdays}).astype(int)
    assignments.index = assignments.index.rename(['act','rep'])
    a2r = assignments.replace(0,np.nan).dropna().reset_index(level='rep').rep

    return a2r


######################
#    -- Plots --     #
######################

def plot_unclustered_periods(profiles, profiles_scaled, basedir, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(basedir,'postprocessing'))
    import plots
    plots.plotparams()
    ### Overlapping days
    for label, dfin in [
        # ('unscaled',profiles),
        ('scaled',profiles_scaled),
    ]:
        properties = dfin.columns.get_level_values('property').unique()
        nhours = len(dfin.columns.get_level_values('region').unique())*(24 if sw['GSw_HourlyType']=='day' else 120)
        plt.close()
        f,ax = plt.subplots(1,len(properties),sharex=True,figsize=(nhours/12, 3.75))
        for col, prop in enumerate(properties):
            dfin[prop].T.reset_index(drop=True).plot(
                ax=ax[col], lw=0.2, legend=False)
            dfin[prop].mean(axis=0).reset_index(drop=True).plot(
                ax=ax[col], lw=1.5, color='k', legend=False)
            ax[col].set_title(prop)
            for x in np.arange(0,nhours+1,(24 if sw['GSw_HourlyType']=='day' else 120)):
                ax[col].axvline(x,c='k',ls=':',lw=0.3)
            ax[col].tick_params(labelsize=9)
            ax[col].set_ylim(0)
        ### Formatting
        title = ' | '.join(
            profiles_scaled.columns.get_level_values('region').drop_duplicates().tolist())
        ax[0].annotate(title,(0,1.12), xycoords='axes fraction', fontsize='large',)
        ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(12))
        ax[0].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(6))
        ax[0].set_xlim(0, nhours)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'profiles-day_hourly-{}.png'.format(label)))
        if interactive: plt.show()
        plt.close()

    ### Sequential days, unscaled and scaled
    for label, dfin in [
        # ('unscaled',profiles),
        ('scaled',profiles_scaled)
    ]:
        properties = dfin.columns.get_level_values('property').unique()
        regions = dfin.columns.get_level_values('region').unique()
        rows = [(p,r) for p in properties for r in regions]
        ### Hourly
        plt.close()
        f,ax = plt.subplots(len(rows),1,figsize=(12,12),sharex=True,sharey=False)
        for row, (p,r) in enumerate(rows):
            df = dfin[p][r].stack('h_of_period')
            ax[row].fill_between(range(len(df)), df.values, lw=0)
            ax[row].set_title('{} {}'.format(p,r),x=0.01,ha='left',va='top',pad=0)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'profiles-year_hourly-{}.png'.format(label)))
        if interactive: plt.show()
        plt.close()
        ### Daily
        plt.close()
        f,ax = plt.subplots(len(rows),1,figsize=(12,12),sharex=True,sharey=False)
        for row, (p,r) in enumerate(rows):
            df = dfin[p][r].mean(axis=1)
            ax[row].fill_between(range(len(df)), df.values, lw=0)
            ax[row].set_title('{} {}'.format(p,r),x=0.01,ha='left',va='top',pad=0)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'profiles-year_daily-{}.png'.format(label)))
        if interactive: plt.show()
        plt.close()


def plot_feature_scatter(profiles_fitperiods, basedir, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(basedir,'postprocessing'))
    import plots
    plots.plotparams()
    ### Settings
    colors = plots.rainbowmapper(profiles_fitperiods.columns.get_level_values('region').unique())
    props = ['load','upv','wind-ons']
    ### Plot it
    plt.close()
    f,ax = plt.subplots(3,3,figsize=(7,7),sharex='col',sharey='row')
    for row, yax in enumerate(props):
        for col, xax in enumerate(props):
            for region, c in colors.items():
                ax[row,col].plot(
                    profiles_fitperiods[xax][region].values,
                    profiles_fitperiods[yax][region].values,
                    c=c, lw=0, markeredgewidth=0, ms=5, alpha=0.5, marker='o',
                    label=(region if (row,col)==(1,2) else '_nolabel'),
                )
    ### Formatting
    ax[1,-1].legend(
        loc='center left', bbox_to_anchor=(1,0.5), frameon=False, fontsize='large',
        handletextpad=0.3,handlelength=0.7,
    )
    for i, prop in enumerate(props):
        ax[-1,i].set_xlabel(prop)
        ax[i,0].set_ylabel(prop)

    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'feature_scatter.png'))
    if interactive: plt.show()
    plt.close()


def plot_clustered_days(
        profiles_fitperiods_hourly, profiles_scaled, idx, rep_periods,
        forceperiods, nearest_period, sw, basedir, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(basedir,'postprocessing'))
    import plots
    plots.plotparams()

    ### Input processing
    numclusters = int(sw['GSw_HourlyNumClusters'])
    centroids = profiles_scaled.loc[select_year].loc[rep_periods]
    properties = profiles_fitperiods_hourly.columns.get_level_values('property').unique()
    nhours = (len(profiles_fitperiods_hourly.columns.get_level_values('region').unique())
              * (24 if sw['GSw_HourlyType']=='day' else 120))
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        len(properties), numclusters+len(forceperiods),
        sharey='row', sharex=True, figsize=(nhours/12*numclusters/3,6))
    for row, prop in enumerate(properties):
        for col in range(numclusters):
            profiles_fitperiods_hourly.loc[:,idx==col,:][prop].T.reset_index(drop=True).plot(
                ax=ax[row,col], lw=0.2, legend=False)
            centroids[prop].T[col].reset_index(drop=True).plot(
                ax=ax[row,col], lw=1.5, ls=':', c='k', legend=False)
            profiles_fitperiods_hourly.loc[:,nearest_period[col],:][prop].T.reset_index(drop=True).plot(
                ax=ax[row,col], lw=1.5, c='k', legend=False)
        for col, period in enumerate(forceperiods):
            profiles_scaled.loc[:,period,:][prop].T.reset_index(drop=True).plot(
                ax=ax[row,numclusters+col], lw=1.5, c='k', legend=False)
            ax[0,numclusters+col].set_title('{} (d{})'.format(numclusters+col, period))
        ax[row,0].set_ylabel(prop)
    ### Formatting
    label = ' | '.join(
        profiles_scaled.columns.get_level_values('region').drop_duplicates().tolist())
    ax[0,0].annotate(label,(0,1.25), xycoords='axes fraction', fontsize='large',)
    ax[0,0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(24))
    ax[0,0].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(6))
    ax[0,0].set_xlim(0, nhours)
    for col in range(numclusters):
        ax[0,col].set_title('{} ({})'.format(col, pd.Series(idx).value_counts()[col]))
        ax[-1,col].tick_params(axis='x',labelsize=9)
    for row in range(len(properties)):
        ax[row,0].set_ylim(0)
        for col in range(numclusters+len(forceperiods)):
            for x in np.arange(0,nhours+1,24):
                ax[row,col].axvline(x,c='k',ls=':',lw=0.3)
    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'profiles-day_hourly-clustered.png'))
    if interactive: plt.show()
    plt.close()


def plot_clusters_pca(profiles_fitperiods_hourly, idx, sw, basedir, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(basedir,'postprocessing'))
    import plots
    plots.plotparams()
    import sklearn.decomposition

    # ###### 3D version (not too informative)
    # pca = sklearn.decomposition.PCA(n_components=3)
    # transformed = pd.DataFrame(pca.fit_transform(profiles_fitperiods_hourly))
    # from mpl_toolkits import mplot3d
    # plt.close()
    # ax = plt.axes(projection='3d')
    # for y in colors:
    #     ax.scatter3D(
    #         transformed[0][idx==y], transformed[1][idx==y], transformed[2][idx==y], 
    #         color=colors[y], lw=0, s=10)
    # plots.despine(ax)
    # plt.show()

    pca = sklearn.decomposition.PCA(n_components=2)
    transformed = pd.DataFrame(pca.fit_transform(profiles_fitperiods_hourly))
    colors = plots.rainbowmapper(range(int(sw['GSw_HourlyNumClusters'])))

    plt.close()
    f,ax = plt.subplots()
    for y in colors:
        ax.scatter(
            transformed[0][idx==y], transformed[1][idx==y],
            color=colors[y], lw=0, s=10)
    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'clusters-pca-{}totaldays.png'.format(
        sw['GSw_HourlyNumClusters'])))
    if interactive: plt.show()
    plt.close()


def plot_ldc(
        period_szn, profiles_scaled, select_year, rep_periods,
        forceperiods_write, sw, basedir, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(basedir,'postprocessing'))
    import plots
    plots.plotparams()

    colors = plots.rainbowmapper(rep_periods, plt.cm.turbo)

    ### Get clustered load, repeating representative periods based on how many
    ### periods they represent
    numperiods = period_szn.value_counts().rename('numperiods').to_frame()
    numperiods['yperiod'] = numperiods.index.map(szn2period)
    periods = [[row[1].yperiod]*row[1].numperiods for row in numperiods.iterrows()]
    periods = [item for sublist in periods for item in sublist]

    #### Hourly
    hourly_in = (
        profiles_scaled
        .divide(sw['GSw_HourlyClusterWeights'], level='property')
        .stack('h_of_period')
        .loc[select_year]
    ).copy()
    hourly_out = hourly_in.unstack('h_of_period').loc[periods].stack('h_of_period')

    #### Daily
    periodly_in = hourly_in.groupby('yperiod').mean()
    ## Index doesn't matter; replace it so we can take daily mean
    periodly_out = hourly_out.copy()
    hourly_out.index = hourly_in.index.copy()
    periodly_out = hourly_out.groupby('yperiod').mean()

    ### Get axis coordinates: properties = rows, regions = columns
    properties = periodly_out.columns.get_level_values('property').unique().values
    regions = periodly_out.columns.get_level_values('region').unique().values
    nrows, ncols = len(properties), len(regions)
    coords = {}
    if ncols == 1:
        coords = dict(zip(
            [(prop, regions[0]) for prop in properties],
            range(nrows)))
    elif nrows == 1:
        coords = dict(zip(
            [(properties[0], region) for region in regions],
            range(ncols)))
    else:
        coords = dict(zip(
            [(prop, reg) for prop in properties for reg in regions],
            [(row, col) for row in range(nrows) for col in range(ncols)],
        ))

    ###### Plot it
    for plotlabel, xlabel, dfin, dfout in [
        ('hourly','Hour',hourly_in,hourly_out),
        ('periodly','Period',periodly_in,periodly_out),
    ]:
        plt.close()
        f,ax = plt.subplots(
            nrows,ncols,figsize=(len(regions)*1.2,9),sharex=True,sharey='row',
            gridspec_kw={'hspace':0.1,'wspace':0.1},
        )
        for region in regions:
            for prop in properties:
                df = dfout[prop][region].sort_values(ascending=False)
                ax[coords[prop,region]].plot(
                    range(len(dfout)), df.values,
                    label='Clustered', c='C1')
                #     label='Clustered', c='C7', lw=0.25)
                # ax[coords[prop,region]].scatter(
                #     range(len(dfout)), df.values,
                #     c=df.index.map(yperiod2color), s=10, lw=0,
                # )
                ax[coords[prop,region]].plot(
                    range(len(dfin)),
                    dfin[prop][region].sort_values(ascending=False).values,
                    ls=':', label='Original', c='k')
        ### Formatting
        for region in regions:
            ax[coords[properties[0], region]].set_title(region)
        for prop in properties:
            ax[coords[prop, regions[0]]].set_ylabel(prop)
            ax[coords[prop, regions[0]]].set_ylim(0)
        ax[coords[properties[0], regions[0]]].annotate(
            '{} periods: {} forced, {} clustered'.format(
                sw['GSw_HourlyNumClusters'], len(forceperiods_write),
                int(sw['GSw_HourlyNumClusters']) - len(forceperiods_write)),
            (0,1.15), xycoords='axes fraction', fontsize='x-large',
        )
        ax[coords[properties[0], regions[-1]]].legend(
            loc='lower right', bbox_to_anchor=(1,1.1), ncol=2)
        ax[coords[properties[-1], regions[0]]].set_xlabel(
            '{} of year'.format(xlabel), x=0, ha='left')
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'ldc-{}-{}totaldays.png'.format(
            plotlabel, sw['GSw_HourlyNumClusters'])))
        if interactive: plt.show()
        plt.close()


def plot_maps(sw, inputs_case, basedir, figpath):
    """
    """
    ### Imports
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    import geopandas as gpd
    import shapely
    site.addsitedir(os.path.join(basedir,'postprocessing'))
    import plots
    plots.plotparams()
    ### Settings
    cmaps = {
        'cf_full':'turbo', 'cf_hourly':'turbo', 'cf_diff':'coolwarm',
        'GW_full':'gist_earth_r', 'GW_hourly':'gist_earth_r',
        'GW_diff':'coolwarm', 'GW_frac':'coolwarm', 'GW_pct':'coolwarm', 
    }
    vm = {
        'wind-ons':{'cf_full':(0,0.8),'cf_hourly':(0,0.8),'cf_diff':(-0.05,0.05)},
        'upv':{'cf_full':(0,0.4),'cf_hourly':(0,0.4),'cf_diff':(-0.05,0.05)},
    }
    vlimload = 0.05
    title = (
        'Algorithm={}, NumClusters={}, RegionLevel={},\n'
        'PeakLevel={}, MinRElevel={}, ClusterWeights={}'
    ).format(
        sw['GSw_HourlyClusterAlgorithm'],
        sw['GSw_HourlyNumClusters'], sw['GSw_HourlyClusterRegionLevel'],
        sw['GSw_HourlyPeakLevel'], sw['GSw_HourlyMinRElevel'],
        '__'.join(['_'.join([
            str(i),str(v)]) for (i,v) in sw['GSw_HourlyClusterWeights'].iteritems()]))
    techs = ['wind-ons','upv']
    colors = {'cf_full':'k', 'cf_hourly':'C1'}
    lss = {'cf_full':':', 'cf_hourly':'-'}
    zorders = {'cf_full':10, 'cf_hourly':9}

    ### Get the CF data over all years, take the mean
    recf = pd.read_hdf(os.path.join(inputs_case,'recf.h5')).mean()

    ### Get supply curves
    dfsc = {}
    for tech in techs:
        dfsc[tech] = pd.read_csv(
            os.path.join(
                basedir,'inputs','supplycurvedata',
                '{}_supply_curve{}-{}.csv'.format(
                    tech,'_sreg' if tech == 'wind-ons' else '',sw['GSw_SitingWindOns']))
        ).rename(columns={'region':'r'})
        dfsc[tech]['i'] = tech + '_' + dfsc[tech]['class'].astype(str)

    dfsc = pd.concat(dfsc, axis=0, names=('tech',)).drop(
        ['dist_km','dist_mi','supply_curve_cost_per_mw'], errors='ignore', axis=1)

    ### Add geographic and CF information
    sitemap = pd.read_csv(
        os.path.join(basedir,'inputs','supplycurvedata','sitemap.csv'),
        index_col='sc_point_gid',
    )

    dfsc['latitude'] = dfsc.sc_point_gid.map(sitemap.latitude)
    dfsc['longitude'] = dfsc.sc_point_gid.map(sitemap.longitude)
    dfsc = plots.df2gdf(dfsc)
    dfsc['resource'] = dfsc.i + '_' + dfsc.r
    dfsc['cf_full'] = dfsc.resource.map(recf)

    ### Get the BA map
    dfba = gpd.read_file(os.path.join(basedir,'inputs','shapefiles','US_PCA')).set_index('rb')
    dfba['x'] = dfba.geometry.centroid.x
    dfba['y'] = dfba.geometry.centroid.y
    ### Aggregate to states
    dfstates = dfba.dissolve('st')

    ### Get the hourly data
    hours = pd.read_csv(
        os.path.join(inputs_case,'numhours.csv')
    ).rename(columns={'*h':'h'}).set_index('h').numhours
    dfcf = pd.read_csv(os.path.join(inputs_case,'cf_vre.csv')).rename(columns={'*i':'i'})

    for tech in techs:
        ### Get the annual average CF of the hourly-processed data
        cf_hourly = dfcf.loc[dfcf.i.str.startswith(tech)].pivot(
            index=['i','r'],columns='h',values='cf')
        cf_hourly = (
            (cf_hourly * cf_hourly.columns.map(hours)).sum(axis=1) / hours.sum()
        ).rename('cf_hourly').reset_index()
        cf_hourly['resource'] = cf_hourly.i + '_' + cf_hourly.r

        ### Merge with supply curve, take the difference
        cfmap = dfsc.assign(
            cf_hourly=dfsc.resource.map(cf_hourly.set_index('resource').cf_hourly)).loc[tech].copy()
        cfmap['cf_diff'] = cfmap.cf_hourly - cfmap.cf_full

        ### Plot the difference map
        plt.close()
        f,ax = plt.subplots(1,3,figsize=(13,4),gridspec_kw={'wspace':-0.05})
        for col in range(3):
            dfstates.plot(ax=ax[col], facecolor='none', edgecolor='k', lw=0.25, zorder=10000)
        for x,col in enumerate(['cf_full','cf_hourly','cf_diff']):
            cfmap.plot(
                ax=ax[x], column=col, cmap=cmaps[col],
                marker='s', markersize=0.4, lw=0, legend=True,
                legend_kwds={'shrink':0.75,'orientation':'horizontal',
                            'label':'{} {}'.format(tech,col), 'pad':0},
                vmin=vm[tech][col][0], vmax=vm[tech][col][1],
            )
            ax[x].axis('off')
        ax[0].set_title(title, y=0.95, x=0.05, ha='left', fontsize=10)
        plt.savefig(os.path.join(figpath,'cfmap-{}-{}totaldays.png'.format(
            tech.replace('-',''), sw['GSw_HourlyNumClusters'])))
        if interactive: plt.show()
        plt.close()

        ### Plot the distribution of capacity factors
        plt.close()
        f,ax = plt.subplots()
        for col in ['cf_full','cf_hourly']:
            ax.plot(
                np.linspace(0,100,len(cfmap)),
                cfmap.sort_values('cf_full', ascending=False)[col].values,
                label=col.split('_')[1],
                color=colors[col], ls=lss[col], zorder=zorders[col],
            )
        ax.set_ylim(0)
        ax.set_xlim(-1,101)
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
        ax.legend(fontsize='large', frameon=False)
        ax.set_ylabel('{} capacity factor [.]'.format(tech))
        ax.set_xlabel('Percent of sites [%]')
        ax.set_title(title.replace(' ','\n').replace(',',''), x=0, ha='left', fontsize=10)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'cfmapdist-{}-{}totaldays.png'.format(
            tech.replace('-',''), sw['GSw_HourlyNumClusters'])))
        if interactive: plt.show()
        plt.close()

    ###### Do it again for load
    ### Get the full hourly data, take the mean for the cluster year
    load_raw = pd.read_hdf(os.path.join(inputs_case, 'load.h5'))
    loadyears = load_raw.index.get_level_values('year').unique()
    keepyear = (
        int(sw['GSw_HourlyClusterYear']) if int(sw['GSw_HourlyClusterYear']) in loadyears
        else max(loadyears))
    load_raw = load_raw.loc[keepyear].mean() / 1000
    ## load.h5 is busbar load, but b_inputs.gms ingests end-use load, so scale down by distloss
    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, usecols=[0,1], index_col=0, squeeze=True)
    load_raw *= (1 - scalars['distloss'])
    ### Get the representative data, take the mean for the cluster year
    load_allyear = (
        pd.read_csv(os.path.join(inputs_case, 'load_allyear.csv'), index_col=['r','h'])
        [str(keepyear)]
        .multiply(hours).groupby('r').sum()
        / hours.sum()
    ) / 1000
    ### Map it
    dfmap = dfba.copy()
    dfmap['GW_full'] = load_raw
    dfmap['GW_hourly'] = load_allyear
    dfmap['GW_diff'] = dfmap.GW_hourly - dfmap.GW_full
    dfmap['GW_frac'] = dfmap.GW_hourly / dfmap.GW_full - 1

    ### Plot the difference map
    plt.close()
    f,ax = plt.subplots(1,3,figsize=(13,4),gridspec_kw={'wspace':-0.05})
    for col in range(3):
        dfstates.plot(ax=ax[col], facecolor='none', edgecolor='k', lw=0.25, zorder=10000)
    for x,col in enumerate(['GW_full','GW_hourly','GW_frac']):
        dfmap.plot(
            ax=ax[x], column=col, cmap=cmaps[col], legend=True,
            legend_kwds={'shrink':0.75,'orientation':'horizontal',
                        'label':'load {}'.format(col), 'pad':0},
            vmin=(0 if col != 'GW_frac' else -vlimload),
            vmax=(dfmap[['GW_full','GW_hourly']].max().max() if col != 'GW_frac' else vlimload),
        )
        ax[x].axis('off')
    ax[0].set_title(title, y=0.95, x=0.05, ha='left', fontsize=10)
    plt.savefig(os.path.join(figpath,'loadmap-{}totaldays.png'.format(
        sw['GSw_HourlyNumClusters'])))
    if interactive: plt.show()
    plt.close()

    ### Plot the distribution of load by region
    colors = {'GW_full':'k', 'GW_hourly':'C1'}
    lss = {'GW_full':':', 'GW_hourly':'-'}
    zorders = {'GW_full':10, 'GW_hourly':9}
    plt.close()
    f,ax = plt.subplots()
    for col in ['GW_full','GW_hourly']:
        ax.plot(
            range(1,len(dfmap)+1),
            dfmap.sort_values('GW_full', ascending=False)[col].values,
            label='{} ({:.1f} GW mean)'.format(col.split('_')[1], dfmap[col].sum()),
            color=colors[col], ls=lss[col], zorder=zorders[col],
        )
    ax.set_ylim(0)
    ax.set_xlim(0,len(dfmap)+1)
    ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
    ax.legend(fontsize='large', frameon=False)
    ax.set_ylabel('Average load [GW]')
    ax.set_xlabel('Number of BAs')
    ax.set_title(title.replace(' ','\n').replace(',',''), x=0, ha='left', fontsize=10)
    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'loadmapdist-{}totaldays.png'.format(
        sw['GSw_HourlyNumClusters'])))
    if interactive: plt.show()
    plt.close()


def plot_8760(profiles, period_szn, rep_periods, select_year, basedir, figpath):
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(basedir,'postprocessing'))
    import plots
    plots.plotparams()

    def get_profiles(regions):
        """Assemble 8760 profiles from original and representative days"""
        timeindex = pd.date_range('2001-01-01','2002-01-01',freq='H',closed='left')
        props = profiles.columns.get_level_values('property').unique()
        ### Original profiles
        dforig = {}
        for prop in props:
            df = profiles[prop].stack('h_of_period')[regions].sum(axis=1)
            dforig[prop] = df / df.max()
            dforig[prop].index = timeindex
        dforig = pd.concat(dforig, axis=1)

        ### Representative profiles
        periodmap = period_szn.map(szn2period)

        dfrep = {}
        for prop in props:
            df = (
                profiles[prop].loc[select_year].loc[periodmap.values]
                .stack('h_of_period')[regions].sum(axis=1))
            dfrep[prop] = df / df.max()
            dfrep[prop].index = timeindex
        dfrep = pd.concat(dfrep, axis=1)

        return dforig, dfrep

    ###### All regions
    props = profiles.columns.get_level_values('property').unique()
    regions = profiles.columns.get_level_values('region').unique()
    dforig, dfrep = get_profiles(regions)

    ### Original vs representative
    plt.close()
    f,ax = plt.subplots(38,1,figsize=(12,16),sharex=True,sharey=True)
    for i, prop in enumerate(props):
        plots.plotyearbymonth(
            dfrep[prop].rename('Representative').to_frame(),
            style='line', colors=['C1'], ls='-', f=f, ax=ax[i*12+i:(i+1)*12+i])
        plots.plotyearbymonth(
            dforig[prop].rename('Original').to_frame(),
            style='line', colors=['k'], ls=':', f=f, ax=ax[i*12+i:(i+1)*12+i])
    for i in [12,25]:
        ax[i].axis('off')
    for i, prop in list(zip(range(len(props)), props)):
        ax[i*12+i].set_title('{}: {}'.format(prop,' | '.join(regions)),x=0,ha='left',fontsize=12)
    ax[0].legend(loc='lower left', bbox_to_anchor=(0,1.5), ncol=2, frameon=False)
    plt.savefig(os.path.join(figpath,'8760-allregions.png'))
    if interactive: plt.show()
    plt.close()

    ### Load, wind, solar together; original
    plt.close()
    f,ax = plots.plotyearbymonth(
        dforig[['wind-ons','upv']], colors=['#0064ff','#ff0000'], alpha=0.5)
    plots.plotyearbymonth(dforig['load'], f=f, ax=ax, style='line', colors='k')
    plt.savefig(os.path.join(figpath,'8760-allregions-original.png'))
    if interactive: plt.show()
    plt.close()

    ### Load, wind, solar together; representative
    plt.close()
    f,ax = plots.plotyearbymonth(
        dfrep[['wind-ons','upv']], colors=['#0064ff','#ff0000'], alpha=0.5)
    plots.plotyearbymonth(dfrep['load'], f=f, ax=ax, style='line', colors='k')
    plt.savefig(os.path.join(figpath,'8760-allregions-representative.png'))
    if interactive: plt.show()
    plt.close()

    ###### Individual regions, original vs representative
    for region in profiles.columns.get_level_values('region').unique():
        dforig, dfrep = get_profiles([region])

        plt.close()
        f,ax = plt.subplots(38,1,figsize=(12,16),sharex=True,sharey=True)
        for i, prop in enumerate(props):
            plots.plotyearbymonth(
                dfrep[prop].rename('Representative').to_frame(),
                style='line', colors=['C1'], ls='-', f=f, ax=ax[i*12+i:(i+1)*12+i])
            plots.plotyearbymonth(
                dforig[prop].rename('Original').to_frame(),
                style='line', colors=['k'], ls=':', f=f, ax=ax[i*12+i:(i+1)*12+i])
        for i in [12,25]:
            ax[i].axis('off')
        for i, prop in list(zip(range(len(props)), props)):
            ax[i*12+i].set_title('{}: {}'.format(prop,region),x=0,ha='left',fontsize=12)
        ax[0].legend(loc='lower left', bbox_to_anchor=(0,1.5), ncol=2, frameon=False)
        plt.savefig(os.path.join(figpath,'8760-{}.png'.format(region)))
        if interactive: plt.show()


def plots_original(
        profiles_long, profiles,
        profiles_scaled, rep_periods, period_szn,
        select_year, sw, basedir, figpath, make_plots,
    ):
    """
    """
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import site
    site.addsitedir(os.path.join(basedir,'postprocessing'))
    import plots
    plots.plotparams()

    ### Input processing
    idx_reedsyr = period_szn.map(szn2period)
    medoid_profiles = profiles.loc[select_year].loc[rep_periods]
    centroids = profiles_scaled.loc[select_year].loc[rep_periods]
    centroid_profiles = centroids * profiles.stack('h_of_period').max()

    colors = plots.rainbowmapper(list(set(idx_reedsyr)), plt.cm.turbo)
    hoursperperiod = {'day':24, 'wek':120, 'year':24}[sw['GSw_HourlyType']]
    periodsperyear = {'day':365, 'wek':73, 'year':365}[sw['GSw_HourlyType']]

    ### plot a dendrogram
    if make_plots >= 3:
        plt.close()
        plt.figure(figsize=(12,9))
        plt.title("Dendrogram of Time Clusters")
        dend = scipy.cluster.hierarchy.dendrogram(
            scipy.cluster.hierarchy.linkage(profiles_scaled, method='ward'),
            color_threshold=7,
        )
        plt.gcf().savefig(os.path.join(figpath,'dendrogram.png'))
        if interactive: plt.show()
        plt.close()

    ### PLOT ALL DAYS ON SAME X AXIS:
    try:
        ## Map days to axes
        ncols = len(colors)
        nrows = 1
        coords = dict(zip(
            range(len(colors)),
            [col for col in range(ncols)]
        ))
        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(1.5*ncols,2.5*nrows), sharex=True, sharey=True)
        for day in range(len(idx_reedsyr)):
            szn = idx_reedsyr[day]
            this_profile = profiles.load.iloc[day].groupby('h_of_period').sum()
            ax[coords[szn]].plot(
                range(len(this_profile)), this_profile.values/1e3, color=colors[szn], alpha=0.5)
        ## add centroids and medoids to the plot:
        for i in range(len(set(idx_reedsyr))):
            ## centroids - only for clustered days, not force-included days
            try:
                ax[coords[i]].plot(
                    range(len(this_profile)),
                    centroid_profiles['load'].iloc[i].groupby('h_of_period').sum().values/1e3,
                    color='k', alpha=1, linewidth=2, label='centroid',
                )
            except IndexError:
                pass
            ## medoids
            ax[coords[i]].plot(
                range(len(this_profile)),
                medoid_profiles['load'].iloc[i].groupby('h_of_period').sum().values/1e3,
                ls='--', color='0.7', alpha=1, linewidth=2, label='medoid',
            )
            ## title
            ax[coords[i]].set_title('szn{}, {} days'.format(i+1, sum(idx_reedsyr == i)), size=9)

        ax[coords[0]].legend(loc='upper left', frameon=False, fontsize='small')
        ax[coords[0]].set_xlabel('Hour')
        ax[coords[0]].set_ylabel('Conterminous\nUS Load [GW]', y=0, ha='left')
        ax[coords[0]].xaxis.set_major_locator(
            mpl.ticker.MultipleLocator(6 if sw['GSw_HourlyType']=='day' else 24))
        ax[coords[0]].xaxis.set_minor_locator(
            mpl.ticker.MultipleLocator(3 if sw['GSw_HourlyType']=='day' else 12))
        ax[coords[0]].annotate(
            'Cluster Comparison (All Days in {} Shown)'.format(
                '2007–2013' if len(profiles.index.unique(level='year')) > 1 else '2012' ),
            xy=(0,1.2), xycoords='axes fraction', ha='left',
        )
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'day_comparison_all.png'))
        if interactive: plt.show()
        plt.close()
    except Exception as err:
        print('day_comparison_all.png failed with the following error:\n{}'.format(err))


    ### PLOT LOAD FOR THE ENTIRE ReEDS YEAR COLORED BY CLUSTER AND MEDOID:
    if make_plots >= 3:
        try:
            plt.close()
            f,ax = plt.subplots(figsize=(14,3.5))
            plotted = [False for i in range(int(sw['GSw_HourlyNumClusters']))]
            nationwide_reedsyr_load = profiles_long[
                (profiles_long['year']==select_year) & (profiles_long['property']=='load')
            ].groupby(['year','yperiod','hour'],as_index=False).sum()
            nationwide_reedsyr_load['hour_numeric'] = pd.to_numeric(
                nationwide_reedsyr_load['hour'].str.lstrip('h'))
            nationwide_reedsyr_load.sort_values(['year','hour_numeric'],inplace=True)
            for this_yperiod in nationwide_reedsyr_load.yperiod.unique():
                ax.fill_between(
                    nationwide_reedsyr_load.loc[
                        nationwide_reedsyr_load['yperiod']==this_yperiod,'hour_numeric'].to_numpy(),
                    nationwide_reedsyr_load.loc[
                        nationwide_reedsyr_load['yperiod'] == this_yperiod,'value'].to_numpy()/1e3,
                    ls='-', color=colors[idx_reedsyr[this_yperiod-1]], lw=0, alpha=0.5,
                    label=(
                        '{} ({} periods)'.format(
                            period_szn.loc[period_szn['period']==this_yperiod,'season'].iloc[0],
                            sum(idx_reedsyr == idx_reedsyr[this_yperiod-1]))
                        if not plotted[idx_reedsyr[this_yperiod-1]]
                        else '_nolabel'
                    )
                )
                plotted[idx_reedsyr[this_yperiod-1]] = True
            ### Plot the medoid profiles
            for i, (yperiod, row) in enumerate(medoid_profiles.iterrows()):
                ax.plot(
                    list(range((yperiod-1)*hoursperperiod+1,(yperiod)*hoursperperiod+1)),
                    row['load'].groupby('h_of_period').sum().values/1e3,
                    color=colors[i], alpha=1, linewidth=1.5,
                    label='{} Medoid'.format(period_szn.set_index('period').season[int(yperiod)])
                )
            ax.set_xlim(0,8760)
            ax.set_ylim(0)
            ax.legend(
                loc='upper left', bbox_to_anchor=(1,1), ncol=len(colors)//9+1)
            ax.set_ylabel('Conterminous US Load (GW)')
            ax.set_title('Cluster and Medoid Definitions')
            plots.despine(ax)
            plt.savefig(os.path.join(figpath,'year_clusters.png'))
            if interactive: plt.show()
            plt.close()
        except Exception as err:
            print('year_clusters.png failed with the following error:\n{}'.format(err))


    ### Plot daily profile for the US colored by representative period
    try:
        ## TODO: Switch to actual months...
        nrows, ncols = (12, 31) if sw['GSw_HourlyType'] in ['day','year'] else (13,6)
        coords = dict(zip(
            range(1,periodsperyear+1),
            [(row,col) for row in range(nrows) for col in range(ncols)]
        ))
        for prop in ['load','upv','wind-ons']:
            dfplot = profiles_long[
                (profiles_long['year']==select_year) & (profiles_long['property']==prop)
            ].groupby(['year','yperiod','hour'],as_index=False).sum()
            dfplot['hour_numeric'] = pd.to_numeric(
                dfplot['hour'].str.lstrip('h'))
            dfplot.sort_values(['year','hour_numeric'],inplace=True)

            plt.close()
            f,ax = plt.subplots(
                nrows, ncols, sharex=True, sharey=True,
                gridspec_kw={'wspace':0, 'hspace':0,},
                figsize=(12,6),
            )
            for this_yperiod in range(1,periodsperyear+1):
                ax[coords[this_yperiod]].fill_between(
                    range(hoursperperiod),
                    dfplot.loc[
                        dfplot['yperiod'] == this_yperiod,'value'].to_numpy()/1e3,
                    ls='-', color=colors[idx_reedsyr[this_yperiod]], alpha=0.35,
                )
                ### Label the szn
                ax[coords[this_yperiod]].annotate(
                    int(period_szn[this_yperiod][6:]),
                    (0.5,0), xycoords='axes fraction', va='bottom', ha='center',
                    fontsize=8, color=colors[idx_reedsyr[this_yperiod]],
                )
            ### Plot the medoid profiles
            for i, (yperiod, row) in enumerate(medoid_profiles.iterrows()):
                ax[coords[yperiod]].plot(
                    range(hoursperperiod), row[prop].groupby('h_of_period').sum().values/1e3,
                    color=colors[yperiod], alpha=1, linewidth=2,
                )
            for row in range(nrows):
                for col in range(ncols):
                    ax[row,col].axis('off')
            ax[0,0].set_title('Cluster and Medoid Definitions', x=0, ha='left')
            ax[0,0].set_ylim(0)
            ax[0,0].set_xlim(-1,hoursperperiod+1)
            plots.despine(ax)
            plt.savefig(os.path.join(figpath,f'year_clusters_daily-{prop}.png'))
            if interactive: plt.show()
            plt.close()
    except Exception as err:
        print('year_clusters_daily.png failed with the following error:\n{}'.format(err))


    ## PLOT LDCs:
    if make_plots >= 3:
        try:
            #set up the old quarterly season mapping for comparison
            df_season_quarterly = make_equal_periods(4)
            #avg day:
            quarterly_profiles = pd.merge(profiles_long,df_season_quarterly,on='hour')
            quarterly_avg_centroids = quarterly_profiles[
                quarterly_profiles['year']==select_year
            ].groupby(['property','region','season','h_of_period'], as_index=False).mean()
            quarterly_avg_centroids = quarterly_avg_centroids.pivot_table(
                index=['year','season'], columns=['property','region','h_of_period'])['value']
            # for prop in medoid_profiles.
            plt.close()
            f,ax = plt.subplots()
            weights = [sum(idx_reedsyr == x) for x in range(len(set(idx_reedsyr)))]
            medoid_sums = medoid_profiles['load'].groupby('h_of_period',axis=1).sum()
            medoid_ldc = np.repeat(np.array(medoid_sums),np.array(weights),axis=0)

            # centroid_sums = centroid_profiles['load'].groupby('h_of_period',axis=1).sum()
            # centroid_ldc = np.repeat(
            #     np.array(centroid_sums),np.array(weights[:len(centroid_profiles)]),axis=0)
            centroid_sums = pd.concat(
                [centroid_profiles, medoid_profiles.iloc[len(centroid_profiles):]], axis=0
            )['load'].groupby('h_of_period',axis=1).sum()
            centroid_ldc = np.repeat(np.array(centroid_sums),np.array(weights),axis=0)

            quarterly_avg_sums = quarterly_avg_centroids['load'].groupby('h_of_period',axis=1).sum()
            quarterly_avg_ldc = np.repeat(
                np.array(quarterly_avg_sums),
                np.array([92, 91, 91, 91]),
                axis=0)

            quarterly_h17_sums = quarterly_avg_centroids['load'].groupby('h_of_period',axis=1).sum()
            quarterly_h17_ldc = np.repeat(
                np.array(quarterly_h17_sums),
                np.array([92, 91, 91, 91]),
                axis=0)

            ax.plot(
                range(8760), sorted(medoid_ldc.flatten()/1e3)[::-1],
                color='C3', lw=1.0, label='2012 Medoids')
            ax.plot(
                range(8760), sorted(centroid_ldc.flatten()/1e3)[::-1],
                color='C0', lw=1.0, label='2012 Centroids')
            ax.plot(
                range(8760), sorted(quarterly_avg_ldc.flatten()/1e3)[::-1],
                color='C2', lw=1.0, label='Quarterly Season Average Days')
            ax.plot(
                range(8760), sorted(quarterly_h17_ldc.flatten()/1e3)[::-1],
                color='C1', lw=1.0, label='h17', ls='--')
            ax.plot(
                range(8760), np.sort(nationwide_reedsyr_load['value'])[::-1]/1e3,
                color='black', lw=1.0, alpha=0.5, label='2012 Actual')

            ax.legend()
            ax.set_ylabel('Conterminous US Load (GW)')
            ax.set_xlabel('Hours of %s' % select_year)
            ax.set_title('LDC Validation')
            plt.savefig(os.path.join(figpath,'LDC_all.png'))
            if interactive: plt.show()
            plt.close()
        except Exception as err:
            print('LDC_all.png failed with the following error:\n{}'.format(err))


###########################
#    -- Clustering --     #
###########################

def cluster_profiles(
        select_year, cf_full, load_full, sw, val_r, basedir, inputs_case, make_plots, figpath):
    """
    Cluster the load and (optionally) RE profiles to find representative days for dispatch in ReEDS.

    Args:
        GSw_HourlyClusterRegionLevel: Level of inputs/hierarchy.csv at which to aggregate
        profiles for clustering. VRE profiles are converted to available-capacity-weighted
        averages. That's not the best - it would be better to weight sites that are more likely
        to be developed more strongly - but it's better than not weighting at all.

    Returns:
        cf_representative - hourly profile of centroid or medoid capacity factor values
                            for all regions and technologies
        load_representative - hourly profile of centroid or medoid load values for all regions
        period_szn - day indices of each cluster center
    """
    ### Get region hierarchy for use with GSw_HourlyClusterRegionLevel
    hierarchy = pd.read_csv(
        os.path.join(inputs_case,'hierarchy.csv')).rename(columns={'*r':'r'})
    ## Get BA-to-aggregated-region lookup table
    if sw.GSw_HourlyClusterRegionLevel == 'r':
        rmap = pd.Series(hierarchy.r.values, index=hierarchy.r.values)
    else:
        rmap = hierarchy.set_index('r')[sw['GSw_HourlyClusterRegionLevel']]
    ### Get rs-to-rb map
    rsmap = pd.read_csv(
        os.path.join(basedir,'inputs','rsmap_sreg.csv'), index_col='rs', squeeze=True)
    ## Include rb-to-rb entries to speed up later merges
    rsmap = pd.concat([rsmap, pd.Series(index=rsmap.unique(), data=rsmap.unique())])

    if sw['GSw_HourlyType'] == 'day':
        ### map hours of year to days of year
        h_to_yperiod = pd.DataFrame({'yperiod': [ y for x in range(1,366) for y in (x,)*24 ]})
        h_of_period = list(range(1,25))*365
    elif sw['GSw_HourlyType'] == 'wek':
        h_to_yperiod = pd.DataFrame({'yperiod': [ y for x in range(1,74) for y in (x,)*120 ]})
        h_of_period = list(range(1,121))*73

    h_to_yperiod['hour'] = ['h'] + (h_to_yperiod.index+1).astype('str')
    ## have to use 3 zeros so that it works for weks
    h_of_period = pd.DataFrame({'h_of_period':[str(item).zfill(3) for item in h_of_period]})
    h_map = pd.concat([h_to_yperiod,h_of_period],axis=1)
    h_map['timestamp'] = (
        f'y{select_year}'
        ## d for day and w for wek 
        + sw.GSw_HourlyType[0] + h_map.yperiod.astype(str).map('{:>03}'.format)
        + 'h' + h_map.h_of_period
    )

    ### Create profiles dataframe, starting with load
    profiles = load_full.copy()
    profiles['property'] = 'load'
    ## Aggregate to GSw_HourlyClusterRegionLevel
    profiles.region = profiles.region.map(rmap)
    profiles = profiles.groupby(['year','region','hour','property'], as_index=False).value.sum()

    cf_full = cf_full.rename(columns={'h':'hour','i':'property','r':'region'})

    ### If clustering on more than load, add RE to profiles
    if len(sw['GSw_HourlyClusterWeights']) > 1:
        ### Load resource supply curves for available-capacity-weighted averages
        sc = {
            'wind-ons': pd.read_csv(
                os.path.join(basedir,'inputs','supplycurvedata',
                f"wind-ons_supply_curve_sreg-{sw['GSw_SitingWindOns']}.csv")
            ).groupby(['region','class'], as_index=False).capacity.sum(),
            'upv': pd.read_csv(
                os.path.join(basedir,'inputs','supplycurvedata',
                f"upv_supply_curve-{sw['GSw_SitingUPV']}.csv")
            ).groupby(['region','class'], as_index=False).capacity.sum(),
        }
        sc = (
            pd.concat(sc, names=['tech','drop'], axis=0)
            .reset_index(level='drop', drop=True).reset_index())
        sc['i'] = sc.tech+'_'+sc['class'].astype(str)

        ### Assemble profiles
        resource = (
            ### Only include profiles techs with weights
            cf_full.loc[
                (cf_full['tech'].isin(sw['GSw_HourlyClusterWeights'].keys()))
                & (cf_full.region.map(rsmap).isin(val_r))]
            .rename(columns={'value':'cf'})
            ### Merge with available capacity by (i,r)
            .merge(sc[['region','i','capacity']],
                   left_on=['region','property'], right_on=['region','i'], how='left')
        )
        ### Since we normalize the profiles later we don't need to divide by total capacity
        resource['value'] = resource.cf * resource.capacity
        ### Aggregate to GSw_HourlyClusterRegionLevel and sum by tech/region
        resource['aggregion'] = resource.region.map(rsmap).map(rmap)
        profiles = pd.concat([
            profiles,
            (resource
             .groupby(['tech','aggregion','year','hour'],as_index=False)['value'].sum()
             .rename(columns={'aggregion':'region', 'tech':'property'}))
        ], axis=0)

    ### Include hour of period and period of year
    profiles = pd.merge(profiles,h_map,on='hour',how='left')

    #format wide (with hours of period in columns) for clustering
    profiles_long = profiles.copy()
    profiles = profiles.pivot_table(
        index=['year','yperiod'], columns=['property','region','h_of_period'])['value']

    ### Normalize each profile by its max over all hours (so each profile is in [0-1])
    profiles_scaled = profiles / profiles.stack('h_of_period').max()

    ### Scale profiles according to GSw_HourlyClusterWeights
    if len(sw['GSw_HourlyClusterWeights']) > 1:
        profiles_scaled = profiles_scaled.multiply(sw['GSw_HourlyClusterWeights'], level='property')

    ###### Identify force-include periods if necessary
    forceperiods = set()
    forceperiods_load = set()
    forceperiods_minre = set()
    ##### Peak-load periods
    if sw['GSw_HourlyPeakLevel'].lower() == 'false':
        pass
    else:
        ## Map BAs to region aggregation level specified by GSw_HourlyPeakLevel
        rmap_peak = dict(zip(hierarchy.r, hierarchy[sw['GSw_HourlyPeakLevel']]))
        df = (
            load_full
            .assign(yperiod=load_full.hour.map(h_map.set_index('hour').yperiod))
            .assign(h_of_period=load_full.hour.map(h_map.set_index('hour').h_of_period))
            .assign(peakregion=load_full.region.map(rmap_peak))
            .groupby(['peakregion','yperiod','h_of_period']).value.sum()
            .groupby(['peakregion','yperiod']).max()
        )
        ## For each peak region, keep the yperiod with the largest peak load
        for region in df.index.get_level_values('peakregion').unique():
            forceperiods.add(df.loc[region].nlargest(1).index[0])
            forceperiods_load.add((df.loc[region].nlargest(1).index[0],'load',region,'max_hour'))

    ##### Min-RE periods
    #### Min-RE periods are periods with the lowest daily sumof generation
    #### at the region-aggregation level specified by GSw_HourlyMinRElevel
    if sw['GSw_HourlyMinRElevel'].lower() == 'false':
        pass
    else:
        ## Map BAs to region aggregation level specified by GSw_HourlyMinRElevel
        rmap_minre = dict(zip(hierarchy.r, hierarchy[sw['GSw_HourlyMinRElevel']]))
        df = (
            resource
            .assign(yperiod=resource.hour.map(h_map.set_index('hour').yperiod))
            .assign(minreregion=resource.region.map(rsmap).map(rmap_minre))
            .groupby(['tech','minreregion','yperiod']).value.sum()
        )
        ## For each min-RE region and tech, keep the yperiod with the lowest sum of generation
        for tech in df.index.get_level_values('tech').unique():
            for region in df.index.get_level_values('minreregion').unique():
                forceperiods.add(df.loc[tech].loc[region].nsmallest(1).index[0])
                forceperiods_minre.add(
                    (df.loc[tech].loc[region].nsmallest(1).index[0],tech,region,'min_period'))

    ### Add number of force-include periods to GSw_HourlyNumClusters for total number of periods
    numclusters = int(sw['GSw_HourlyNumClusters']) + len(forceperiods)

    ### Record the force-included periods
    print('representative periods: {}'.format(sw['GSw_HourlyNumClusters']))
    print('force-include periods: {}'.format(len(forceperiods)))
    print('    peak-load periods: {}'.format(len(forceperiods_load)))
    print('    min-RE periods: {}'.format(len(forceperiods_minre)))
    print('total periods: {}'.format(numclusters))
    forceperiods_write = pd.DataFrame(
        list(forceperiods_load)+list(forceperiods_minre),
        columns=['yperiod','property','region','reason'],
    )

    ### Remove the force-include periods from the profiles used for clustering
    ### (since they're already included)
    clusterperiods = [
        d for d in profiles_scaled.index.get_level_values('yperiod').unique()
        if d not in forceperiods
    ]
    profiles_fitperiods_hourly = profiles_scaled.loc[:, clusterperiods, :].copy()
    ### If aggregating from hours to periods, do so now
    if sw.GSw_HourlyClusterTimestep in ['period','day','wek','week']:
        profiles_fitperiods = (
            profiles_fitperiods_hourly.groupby(axis=1, level=['property','region']).mean())
    else:
        profiles_fitperiods = profiles_fitperiods_hourly.copy()

    #%% Plots
    if make_plots >= 3:
        try:
            plot_unclustered_periods(profiles, profiles_scaled, basedir, figpath)
        except Exception as err:
            print('plot_unclustered_periods failed with the following error:\n{}'.format(err))

        try:
            plot_feature_scatter(profiles_fitperiods, basedir, figpath)
        except Exception as err:
            print('plot_feature_scatter failed with the following error:\n{}'.format(err))

    ###### Run the clustering
    if sw['GSw_HourlyClusterAlgorithm'] == 'equal_periods':
        print("Performing equal_periods clustering")
        if sw['GSw_HourlyPeakLevel'].lower() != 'false':
            # grab the peak day (defined as the day where the peak nationally
            # coincident load hour occurs) for use in multiple time selection methods:
            peak_day = profiles_long[
                (profiles_long['year']==select_year) & (profiles_long['property']=='load')
            ].groupby(['year','yperiod','hour']).sum().idxmax()[0][1]  

            df_season_periods = make_equal_periods(int(sw['GSw_HourlyNumClusters']) - 1)
            period_szn = df_season_periods[['day','season']].drop_duplicates().reset_index(drop=True)
            #add one to other szns
            period_szn['season'] = period_szn['season'].str.replace('szn', '', regex=True).astype(int) + 1
            #recall peak_day is zero-indexed and thus need to reduce by one here
            # area to check on most-correct usage given previous implementation of:
            # period_szn.loc[peak_day,'season'] = 1 
            period_szn.loc[period_szn.day==peak_day-1,'season'] = 1 # set peak period to season 1
            period_szn['season'] = 'szn' + period_szn['season'].astype(str)
            df_season_periods = pd.merge(
                df_season_periods.drop('season',axis=1),
                period_szn,
                how='left',on='day')
        else: 
            df_season_periods = make_equal_periods(int(sw['GSw_HourlyNumClusters']))
            period_szn = df_season_periods[['day','season']].drop_duplicates().reset_index(drop=True)

        #avg day
        period_profiles = pd.merge(profiles_long,df_season_periods,on='hour')
        centroids_allyrs = period_profiles.groupby(
            ['property','region','season','h_of_period'], as_index=False).mean()
        centroids_allyrs = centroids_allyrs.pivot_table(
            index=['season'], columns=['property','region','h_of_period'])['value']

        #need select year profiles for plotting:
        centroid_profiles = period_profiles[
            period_profiles['year']==select_year
        ].groupby(['property','region','season','h_of_period'],as_index=False).mean()
        centroid_profiles = centroid_profiles.pivot_table(
            index=['season'], columns=['property','region','h_of_period'])['value']

        #get medoids where we grab actual days from the ReEDS year that are closest to the
        # ALL-YEARS centroids (if the peak day is included as a cluster,
        # it's already been defined as the centroid)
        # vector quantization to find medoids
        rep_periods, _ = vq(centroids_allyrs,profiles.loc[select_year])

    elif sw['GSw_HourlyClusterAlgorithm'] == 'hierarchical':
        print("Performing hierarchical clustering")
        #run the clustering and get centroids based on all years of data input
        clusters = AgglomerativeClustering(
            n_clusters=int(sw['GSw_HourlyNumClusters']), affinity='euclidean', linkage='ward')
        idx = clusters.fit_predict(profiles_fitperiods)
        centroids = pd.DataFrame(
            NearestCentroid().fit(profiles_fitperiods, idx).centroids_,
            columns=profiles_fitperiods.columns,
        )
        ### Get nearest period to each centroid
        nearest_period = {
            i:
            profiles_fitperiods.loc[:,idx==i,:].apply(
                lambda row: scipy.spatial.distance.euclidean(row, centroids.loc[i]),
                axis=1
            ).nsmallest(1).index[0][1]
            for i in range(int(sw['GSw_HourlyNumClusters']))
        }

        period_szn = pd.DataFrame({
            'period': profiles_fitperiods.index.get_level_values('yperiod'),
            'szn': [f"y{select_year}{sw['GSw_HourlyType'][0]}{i:>03}"
                       for i in pd.Series(idx).map(nearest_period)]
        ### Add the force-include periods to the end of the list of seasons
        }).append(
            pd.DataFrame({
                'period': list(forceperiods),
                'szn': [f"y{select_year}{sw['GSw_HourlyType'][0]}{i:>03}" for i in forceperiods]
            })
        ).sort_values('period').set_index('period').szn

    elif sw['GSw_HourlyClusterAlgorithm'] in ['opt','optimized','optimize']:
        print("Performing optimized clustering")
        ### Optimize the weights of representative days
        profiles_day, rweights = optimize_period_weights(
            profiles_fitperiods=profiles_fitperiods, numclusters=int(sw['GSw_HourlyNumClusters']),
            select_year=select_year)
        ### Optimize the assignment of actual days to representative days
        a2r = assign_representative_days(profiles_day=profiles_day, rweights=rweights)

        if len(rweights) < int(sw['GSw_HourlyNumClusters']):
            print(
                'Asked for {} representative periods but only needed {}'.format(
                    sw['GSw_HourlyNumClusters'], len(rweights)))

        period_szn = a2r.reset_index().rename(columns={'act':'period','rep':'szn'}).append(
            pd.DataFrame({'period':list(forceperiods), 'szn':list(forceperiods)})
            if len(forceperiods) else None
        ).sort_values('period').set_index('period').szn
        period_szn = period_szn.map(lambda x: f'y{select_year}{sw.GSw_HourlyType[0]}{x:>03}')


    ### Get the list of representative periods for convenience
    rep_periods = sorted(period_szn.map(szn2period).unique())
    ### Add seasons to forceperiods
    forceperiods_write['szn'] = forceperiods_write.yperiod.map(period_szn)

    if make_plots >= 3:
        try:
            plot_clustered_days(
                profiles_fitperiods_hourly, profiles_scaled, idx, rep_periods,
                forceperiods, nearest_period, sw, basedir, figpath)
        except Exception as err:
            print('plot_clustered_days failed with the following error:\n{}'.format(err))

        try:
            plot_clusters_pca(profiles_fitperiods_hourly, idx, sw, basedir, figpath)
        except Exception as err:
            print('plot_clusters_pca failed with the following error:\n{}'.format(err))

    if make_plots >= 2:
        try:
            plots_original(
                profiles_long, profiles,
                profiles_scaled, rep_periods, period_szn,
                select_year, sw, basedir, figpath, make_plots)
        except Exception as err:
            print('plots_original failed with the following error:\n{}'.format(err))


    ###### Create cluster center profiles for export
    ### timeslice index (h) is y{year}{d or w}{period of year}h{hour of period}
    periodh2hour = (
        h_map.set_index(['yperiod','h_of_period']).loc[rep_periods]
        .rename(columns={'timestamp':'h'}))

    load_representative = load_full.loc[load_full.year==select_year].merge(h_map, on='hour', how='left')
    load_representative = load_representative.loc[load_representative.yperiod.isin(rep_periods)].copy()
    load_representative['hour'] = (
        pd.Series(load_representative[['yperiod','h_of_period']].itertuples(index=False, name=None))
        .map(periodh2hour.h)).values
    load_representative = load_representative[['region','hour','value']].copy()

    cf_representative = cf_full.loc[cf_full.year==select_year].merge(h_map, on='hour', how='left')
    cf_representative = cf_representative.loc[cf_representative.yperiod.isin(rep_periods)].copy()
    cf_representative['hour'] = (
        pd.Series(cf_representative[['yperiod','h_of_period']].itertuples(index=False, name=None))
        .map(periodh2hour.h)).values
    cf_representative = cf_representative[['tech','property','region','hour','value']].copy()


    ### Plot duration curves
    if make_plots >= 1:
        try:
            plot_ldc(
                period_szn, profiles_scaled, select_year, rep_periods,
                forceperiods_write, sw, basedir, figpath)
        except Exception as err:
            print('plot_ldc failed with the following error:\n{}'.format(err))

    if make_plots >= 3:
        try:
            plot_8760(profiles, period_szn, rep_periods, select_year, basedir, figpath)
        except Exception as err:
            print('plot_8760 failed with the following error:\n{}'.format(err))

    return cf_representative, load_representative, period_szn, rep_periods, forceperiods_write


def window_overlap(sw, chunkmap, rep_periods, hmap_1yr):
    """
    """
    #test arguments
    #n_periods = 4
    #n_window = 6
    #n_ovlp = 2
    ### Input arguments
    n_periods=int(365 if sw['GSw_HourlyType'] == 'year' else len(rep_periods))
    n_window=int(sw['GSw_HourlyWindow'])
    n_ovlp=int(sw['GSw_HourlyOverlap'])
    hoursperperiod = {'day':24, 'wek':120, 'year':24}[sw['GSw_HourlyType']]

    print(
        "Creating hour groups for the minloading constraint with {} clusters, "
        "{} window length, and {} overlapping timeslices".format(n_periods, n_window, n_ovlp))
    ## create a list of full window
    list_periodhours = np.arange(1,hoursperperiod+1).tolist()
    list_output = []

    ## create a list consisting of first element of each expected window
    # gap between first elements of each window
    n_gap = n_window - n_ovlp 

    # list of first elements
    list_1st = []  
    k = 1
    while k  <= hoursperperiod:
        list_1st.append(k)
        k = k + n_gap

    ## list all element in a window 
    for i in list_1st:
        list_window = []

        for j in range(i, i + n_window ):  
            a_element = list_periodhours[(j % len(list_periodhours))-1]
            list_window.append(a_element)

        list_output.append(list_window)
        hourlist = np.array(list_output)

    ## scale up to multiple day
    for d in range(1, n_periods ):
        one_output = (np.array(list_output) + hoursperperiod*d)
        hourlist = np.concatenate((hourlist, one_output) )

    ###--- Formatting Exporting File ---###
    df = (
        ### convert to pandas dataframe, look up timestamp from hour of year
        pd.DataFrame(hourlist).applymap(hmap_1yr.set_index('hour').h.get)
        ### convert to hour chunks
        .applymap(chunkmap.get)
        ### drop duplicate columns; since .drop_duplicates() only works on rows,
        ## need to transpose it, then drop duplicates, then transpose back
        .T.drop_duplicates().T
        ### Add comma to all columns...
        + ','
    )
    ### then strip comma from last column
    df.iloc[:,-1] = df.iloc[:,-1].str.strip(',')
    ### Format for gams readability
    ## get data columns
    cols = df.columns
    ## add period column
    df['period'] = range(1, len(df)+1)
    ## add brackets and dots
    for x in '.()':
        df[x] = x
    ## assemble full output dataframe
    out = pd.concat([
        df[['period', '.', '(']], df[cols], df[[')', '.', '(']], df[cols], df[[')']]
    ], axis=1)

    return out


def get_yearly_demand(
        sw, period_szn, rep_periods, val_r,
        hmap_1yr, set_szn, basedir, inputs_case,
    ):
    """
    After clustering based on GSw_HourlyClusterYear and identifying the modeled days,
    reload the raw demand and extract the demand on the modeled days for each year.
    """
    hoursperperiod = {'day':24, 'wek':120, 'year':np.nan}[sw['GSw_HourlyType']]
    ### Get the set of szn's and h's
    szn_h = (
        hmap_1yr
        .drop_duplicates(['h','season'])
        .sort_values(['season','hour']).reset_index(drop=True)
        [['season','h']]
        .assign(periodhour=np.ravel(
            ([range(1,25)] * 365 if sw['GSw_HourlyType']=='year'
                else [range(1,hoursperperiod+1)] * len(set_szn))
        ))
        .set_index(['season','periodhour']).h
    ).copy()

    ### Get original demand data, subset to cluster year
    load_in = read_file(os.path.join(inputs_case,'load'), index_columns=2)[val_r].unstack(level=0)
    load_in.columns = load_in.columns.rename(['r','t'])
    ### load.h5 is busbar load, but b_inputs.gms ingests end-use load, so scale up by distloss
    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, usecols=[0,1], index_col=0, squeeze=True)
    load_in *= (1 - scalars['distloss'])
    ### Convert all profiles to eastern time
    r_shift = pd.read_csv(
        os.path.join(inputs_case, 'reeds_ba_tz_map.csv'),
        index_col='r', squeeze=True,
    ).map({'ET':0, 'CT':1, 'MT':2, 'PT':3})
    load_in = load_in.apply(lambda col: np.roll(col, r_shift[col.name[0]]))
    ### Subset to a single year if using 7-year data
    if ('EER' in sw.GSw_EFS1_AllYearLoad) or ('historic' in sw.GSw_EFS1_AllYearLoad):
        load_in['year'] = np.ravel([[y]*8760 for y in range(2007,2014)])
        load_in = load_in.loc[load_in.year==select_year].copy()
        load_in.index = range(1,8761)
        load_in.index = load_in.index.rename('hour')
        load_in = load_in.drop('year', axis=1)
    ### Add time indices ("season" is the identifier for modeled periods)
    load_in['period'] = (
        np.ravel([[d]*24 for d in range(1,366)]) if sw['GSw_HourlyType'] == 'year'
        else np.ravel([[d]*hoursperperiod for d in period_szn.index.values]))
    load_in['periodhour'] = (
        np.ravel([range(1,25) for d in range(365)]) if sw['GSw_HourlyType'] == 'year'
        else np.ravel([range(1,hoursperperiod+1) for d in period_szn.index.values])
    )
    load_in['season'] = load_in.period.map(period_szn)


    ### If modeling a full year, keep everything
    if sw['GSw_HourlyType'] == 'year':
        load_out = load_in.drop(['period','periodhour','season'], axis=1)
        load_out.index = hmap_1yr.h
    ### If using representative (i.e. medoid) periods, pull out the representative periods
    else:
        load_out = (
            load_in.loc[load_in.period.isin(rep_periods)]
            .drop('period',axis=1).set_index(['season','periodhour']).sort_index()
        )
        load_out.index = load_out.index.map(szn_h).rename('h')

    ### Reshape for ReEDS
    load_out = load_out.stack('r').reorder_levels(['r','h'], axis=0).sort_index()

    return load_in, load_out


###########################
#    -- Main Function --  #
###########################

def main(sw, basedir, inputs_case, select_year=2012, make_plots=1, figpathtail=''):
    """
    """
    #######################################
    #%% Quit if not using hourly resolution
    if not int(sw['GSw_Hourly']):
        toc(tic=tic, year=0, process='input_processing/hourly_process.py', 
            path=os.path.join(inputs_case,'..'))
        quit()

    # =============================================================================
    ### Direct plots to outputs folder
    figpath = os.path.join(inputs_case,'..','outputs',f'hourly{figpathtail}')
    os.makedirs(figpath, exist_ok=True)

    # gather relevant regions for capacity regions
    rs = pd.read_csv(os.path.join(basedir,"inputs","rsmap_sreg.csv"))
    rs = rs.rename(columns={'*r':'r'})

    val_r = pd.read_csv(
        os.path.join(inputs_case, 'val_r.csv'), squeeze=True, header=None).tolist()

    ### Get original seasons (for 8760)
    d_szn_in = pd.read_csv(
        os.path.join(basedir,'inputs','variability','d_szn_1.csv'),
        index_col='*d', squeeze=True)

    # -- 8760 data processing -- #

    # first need to gather all the data for 8760 for all regions that will be
    # non-17-timeslice resolution
    # note appending arguments passed in for site selection of pv/wind-ons/wind-ofs
    tech_siting = [
        ("csp", None),
        ("dupv", None),
        ("upv", sw['GSw_SitingUPV']),
        ("wind-ons", sw['GSw_SitingWindOns']),
        ("wind-ofs", sw['GSw_SitingWindOfs']),
    ]

    print("Collecting 8760 capacity factor data")
    cf_full = {}
    for tech, siting in tech_siting:
        #temp here is a dataframe that gets appended to the final set
        cf_full[tech] = convert_input(
            basedir, tech, siting, int(sw['GSw_HourlyClusterMultiYear']), select_year)
        print('finished loading resource data for: {}'.format(tech))

    # Note: we don't have dGen results for 2007-2013, so multi-year clustering
    # can't include distpv. We'll just always exclude distpv from the clustering.
    print("Appending 8760 distpv capacity factors")
    distpv = (
        pd.read_csv(os.path.join(inputs_case,"distPVCF_hourly.csv"))
        .rename(columns={'Unnamed: 0':'r'})
        .melt(id_vars=['r'])
    )
    distpv['h'] = 'h' + distpv['variable'].astype('str')
    distpv['i'] = 'distpv'
    distpv['year'] = select_year
    distpv['tech'] = 'distpv'
    cf_full['distpv'] = distpv[['i','r','year','h','value']].copy()

    ### Combine all CF profiles into one dataframe
    cf_full = (
        pd.concat(cf_full, axis=0)
        .reset_index().rename(columns={'level_0':'tech'}).drop('level_1', axis=1))

    print("Collecting 8760 load data")
    load_full = create_load(
        val_r=val_r, sw=sw, inputs_case=inputs_case, select_year=select_year)

    # -- Time Zone Adjustment -- #
    print("Adjust time zones for 8760 capacity factor and load")
    #basic steps: 
    # map timezone to ba
    # map cf and load data to tz
    # map new hour based on tz
    # remove original hour and new columns
    #same file used in Augur
    tz_ba_map = pd.read_csv(os.path.join(inputs_case,"reeds_ba_tz_map.csv"))
    #basic mapping file from original data to new tz-specific hour for each TZ
    allh = ['h' + str(i) for i in range(1,8761)]
    tz_8760_map = pd.DataFrame({'h':allh,'ET':allh,'CT':allh,'MT':allh,'PT':allh})
    tz_8760_map['CT'] = np.roll(tz_8760_map['CT'],-1)
    tz_8760_map['MT'] = np.roll(tz_8760_map['MT'],-2)
    tz_8760_map['PT'] = np.roll(tz_8760_map['PT'],-3)

    #need to map hours to supply regions as well
    r_rs = pd.read_csv(os.path.join(basedir,"inputs","rsmap_sreg.csv"))
    r_rs = r_rs.rename(columns={'*r':'r'})

    tz_ba = duplicate_r_rs(tz_ba_map,r_rs).reset_index().drop('index',axis=1)

    tz_fullm = pd.melt(tz_8760_map,id_vars=['h'])
    tz_fullm = tz_fullm.rename(columns={'variable':'tz'})
    tz_fullm = tz_fullm.rename(columns={'value':'h_out'})

    #make a full map of all r and h with corresponding shifted hour, h_out
    tz_ba_fullm = pd.merge(tz_ba,tz_fullm,on=['tz'],how='left').drop('tz',axis=1)

    #map regions tz-correct hour as a new columns
    cf_newhour = pd.merge(cf_full,tz_ba_fullm,on=['r','h'],how='left')
    load_newhour = pd.merge(
        load_full.rename(columns={'hour':'h'}),
        tz_ba_fullm,
        on=['r','h'], how='left')

    #drop the old hour column and rename h_out appropriately
    load_full = load_newhour.drop('h',axis=1).rename(columns={'h_out':'hour','r':'region'})
    cf_full = cf_newhour.drop('h',axis=1).rename(columns={'h_out':'h'})


    ### Clustering to determine representative periods to model in ReEDS
    print("Beginning clustering of capacity factors and load")
    #identify clusters mapping 8760 to some number of periods based on input arguments:
    ## Representative days or weeks
    if sw['GSw_HourlyType'] in ['day','wek']:
        cf_representative, load_representative, period_szn, rep_periods, forceperiods_write = (
            cluster_profiles(
                select_year=select_year, cf_full=cf_full, load_full=load_full, sw=sw, val_r=val_r,
                basedir=basedir, inputs_case=inputs_case, make_plots=make_plots,
                figpath=figpath,
            ))
    ## 8760
    elif sw['GSw_HourlyType']=='year':
        cf_representative = (
            cf_full.rename(columns={'i':'property','r':'region','h':'hour'}).drop('year',axis=1)
        ).copy()
        load_representative = load_full.drop('year',axis=1).copy()
        ### For 8760 we use the original seasons
        period_szn = pd.Series(d_szn_in.values, index=range(1,366), name='szn')
        period_szn.index = period_szn.index.rename('period')
        rep_periods = period_szn.index.tolist()
        forceperiods_write = pd.DataFrame(columns=['yperiod','property','region','reason'])

    print("Clustering complete")

    # -- Averaging or aggregating based on val_r assignments -- #

    # 8760 mapping
    hmap_7yr, hmap_1yr = make_8760_map(period_szn=period_szn, select_year=select_year, sw=sw)

    ### If using full year, switch from h1..h8760 to timestamps
    if sw['GSw_HourlyType'] == 'year':
        cf_representative = (
            cf_representative
            .assign(hour=cf_representative.hour.map(
                hmap_1yr.set_index('h'+hmap_1yr.hour.astype(str)).h))
        ).dropna(how='any')
        load_representative = (
            load_representative
            .assign(hour=load_representative.hour.map(
                hmap_1yr.set_index('h'+hmap_1yr.hour.astype(str)).h))
        ).dropna(how='any')

    print("Processing capacity factor and load for modeled timeslices")
    cf_out, load_out = create_timeslice_profiles(
        cf_representative=cf_representative,
        load_representative=load_representative, val_r=val_r, rs=rs, sw=sw)

    # calculate number of hours represented based on hmap_1yr
    hours = hmap_1yr.groupby('h').season.count().rename('numhours')

    # create the timeslice-to-season mapping
    h_szn = hmap_1yr[['h','season']].drop_duplicates().reset_index(drop=True)

    #create a szn set to adjust the 'szn' set in b_inputs.gms
    set_szn = pd.DataFrame({'szn':period_szn.sort_values().unique()})

    #create an hours set to adjust the 'h' set in b_inputs.gms
    hset = h_szn.h.sort_values().reset_index(drop=True)

    ### List of periods in which to apply operating reserve constraints
    if (sw['GSw_OpResPeriods'] == 'all') or (sw['GSw_HourlyType'] == 'year'):
        opres_periods = set_szn
    elif sw['GSw_OpResPeriods'] == 'representative':
        opres_periods =  set_szn.loc[~set_szn.szn.isin(forceperiods_write.szn)]
    elif sw['GSw_OpResPeriods'] == 'stress':
        opres_periods =  set_szn.loc[set_szn.szn.isin(forceperiods_write.szn)]
    elif sw['GSw_OpResPeriods'] in ['peakload','peak_load','peak','load','demand']:
        opres_periods =  set_szn.loc[
            set_szn.szn.isin(forceperiods_write.loc[forceperiods_write.property=='load'].szn)]
    elif sw['GSw_OpResPeriods'] in ['minre','re','vre','min_re']:
        opres_periods =  set_szn.loc[
            set_szn.szn.isin(forceperiods_write.loc[forceperiods_write.property!='load'].szn)]

    ###### Representative day peak demand hour linkage set for ndhydro PRM constraint
    h_szn_prm = pd.merge(load_out.groupby(['h'],as_index=False).sum(),h_szn,on='h')
    peak_demand_idx = h_szn_prm.groupby(['season'],as_index=False).idxmax()
    h_szn_prm = h_szn_prm.iloc[peak_demand_idx['value']]
    h_szn_prm = h_szn_prm[['h','season']]


    ###### Quarterly (spri, summ, fall, wint) season weights for setting parameters
    ### Use the ReEDS season definitions
    h_dt_szn = pd.read_csv(os.path.join(basedir,'inputs','variability','h_dt_szn.csv'))
    quarters = (
        h_dt_szn.assign(h_8760=[f'h{i+1}' for i in range(len(h_dt_szn))])
        .replace({'season':{'winter':'wint','spring':'spri','summer':'summ'}})
        .rename(columns={'season':'quarter'})
        .iloc[:8760][['h_8760','quarter']]
    )

    frac_h_quarter_weights = hmap_1yr.copy()
    frac_h_quarter_weights['h_8760'] = 'h' + frac_h_quarter_weights['hour'].astype(str)
    frac_h_quarter_weights = pd.merge(frac_h_quarter_weights,quarters,on='h_8760')
    #count the number of days in each szn that are part of each quarter
    #to category so that .count() includes zero counts
    frac_h_quarter_weights['quarter'] = frac_h_quarter_weights['quarter'].astype('category')
    frac_h_quarter_weights = frac_h_quarter_weights.groupby(
        ['h','quarter'], as_index=False
    ).count().drop(['h_8760'],axis=1)
    frac_h_quarter_weights = frac_h_quarter_weights.rename(columns={'season':'weight'})
    frac_h_quarter_weights['weight'] = frac_h_quarter_weights['weight'].fillna(0)
    #grab total length in days of each szn for denominator
    frac_h_quarter_weights = pd.merge(frac_h_quarter_weights,hours,on='h')
    frac_h_quarter_weights['weight'] = (
        frac_h_quarter_weights['weight'] / frac_h_quarter_weights['numhours'])
    frac_h_quarter_weights = frac_h_quarter_weights[['h','quarter','weight']]


    ###### Net trade with Canada for GSw_Canada=2
    ### Read the 8760 net trade [MW], which is described at
    ## https://github.nrel.gov/ReEDS/ReEDS-2.0_Input_Processing/tree/master/Exogenous_Canadian_Trade
    can_8760 = (
        pd.read_hdf(os.path.join(basedir,'inputs','canada_imports','can_trade_8760.h5'))
        .rename(columns={'h':'hour'}).astype({'r':str}))
    ## Drop the h
    can_8760.hour = can_8760.hour.str.strip('h').astype('int')
    ## Map 8760 hours to modeled hours
    can_8760['h'] = can_8760.hour.map(hmap_1yr.h)

    ### Sum by (r,h,t) to get net trade in MWh during modeled hours
    can_out = can_8760.groupby(['r','h','t']).net.sum().rename('MWh').reset_index()
    ## Only keep modeled regions
    can_out = can_out.loc[can_out.r.isin(val_r)].copy()


    #%%### Seasonal Canadian imports/exports for GSw_Canada=1
    ### Same processing as in all_year_load.py; would be better to do it only once but
    ### we need the new h_szn.
    #%% Exports: Spread equally over hours by quarter.
    can_exports_szn_frac = pd.read_csv(
        os.path.join(basedir, 'inputs', 'canada_imports', 'can_exports_szn_frac.csv'),
        header=0, names=['season','frac'], index_col='season', squeeze=True,
    )
    df = (
        frac_h_quarter_weights.astype({'h':'str','quarter':'str'})
        .replace({'weight':{0:np.nan}}).dropna(subset=['weight']).copy()
    )
    df = (
        df.assign(frac_exports=df.quarter.map(can_exports_szn_frac))
        .assign(season=df.h.map(h_szn.set_index('h').season))
        .assign(hours=df.h.map(hours))
    )
    df['quarter_hours'] = df.hours * df.weight
    df['hours_per_quarter'] = df.quarter.map(quarters.quarter.value_counts())
    df['frac_weighted'] = df.frac_exports * df.quarter_hours / df.hours_per_quarter
    can_exports_h_frac = df.groupby('h', as_index=False).frac_weighted.sum()
    ### Make sure it sums to 1
    assert can_exports_h_frac.frac_weighted.sum().round(5) == 1

    #%% Imports: Spread over seasons by quarter.
    can_imports_quarter_frac = pd.read_csv(
        os.path.join(basedir, 'inputs', 'canada_imports', 'can_imports_szn_frac.csv'),
        header=0, names=['season','frac'], index_col='season', squeeze=True,
    )
    hours_per_season = hmap_1yr.season.value_counts()
    df = hmap_1yr.assign(quarter=quarters.quarter.values)
    hours_per_quarter = df['quarter'].value_counts()
    ## Fraction of quarter made up by each season (typically rep period)
    quarter_season_weights = (
        df.groupby(['quarter','season']).year.count()
        .divide(hours_per_quarter, axis=0, level='quarter'))
    can_imports_szn_frac = (
        quarter_season_weights
        .multiply(can_imports_quarter_frac, level='quarter')
        .groupby('season').sum()
        .rename('frac_weighted').reset_index().rename(columns={'season':'szn'}))
    ### Make sure it sums to 1
    assert can_imports_szn_frac.frac_weighted.sum().round(5) == 1

    # =============================================================================
    # Hour, Region, and Timezone Mapping
    # =============================================================================

    period_szn_write = (
        period_szn.reset_index()
        .assign(period=sw['GSw_HourlyType'][0]+period_szn.index.astype(str))
    ).copy()

    rep_period_weights = (
        period_szn.value_counts().reset_index().rename(columns={'index':'szn','szn':'weight'}))

    ###### Mapping from hourly resolution to GSw_HourlyChunkLength resolution
    ### Aggregation is performed as an average over the hours to be aggregated
    ### For simplicity, midnight is always a boundary between chunks
    ### So if using 3-hour chunks, h1-h2-h3 will turn into h1

    ### First make sure the number of hours is divisible by the chunk length
    assert not len(hset) % int(sw['GSw_HourlyChunkLength']), (
        'Hours are not divisible by chunk length:'
        '\nlen(hset) = {}\nGSw_HourlyChunkLength = {}'
    ).format(len(hset), sw['GSw_HourlyChunkLength'])

    ### Map hours to chunks. Chunks are formatted as hour-ending.
    ## If GSw_HourlyChunkLength == 2,
    ## h1-h2-h3-h4-h5-h6 is mapped to h2-h2-h4-h4-h6-h6.
    outchunks = hset[int(sw.GSw_HourlyChunkLength)-1::int(sw.GSw_HourlyChunkLength)]
    chunkmap = dict(zip(
        hset.values,
        np.ravel([[c]*int(sw['GSw_HourlyChunkLength']) for c in outchunks])
    ))

    # =============================================================================
    # Season starting and ending hours
    # =============================================================================

    ### Start hour is the lowest-numbered h in each season
    ## End up with a series mapping season to start hour: {'szn1':'h1', ...}
    szn2starth = hmap_1yr.drop_duplicates('season', keep='first').set_index('season').h

    ### End hour is the highest-numbered h in each season
    szn2endh = hmap_1yr.drop_duplicates('season', keep='last').set_index('season').h

    # =============================================================================
    # Hour groups for eq_minloading
    # =============================================================================

    hour_group = window_overlap(
        sw=sw, chunkmap=chunkmap, rep_periods=rep_periods, hmap_1yr=hmap_1yr)

    # =============================================================================
    # Yearly demand
    # =============================================================================

    load_in, load_all = get_yearly_demand(
        sw=sw,  period_szn=period_szn, rep_periods=rep_periods,
        val_r=val_r, hmap_1yr=hmap_1yr, set_szn=set_szn, 
        basedir=basedir, inputs_case=inputs_case)

    ###### Get the peak demand in each (r,szn,year)
    ### Procedure reproduced from all_year_load.get_season_peaks()
    load_full_yearly = load_in.drop(['period','periodhour','season'], axis=1).stack('r').reset_index()
    load_full_yearly.hour = 'h' + load_full_yearly.hour.astype(str)

    hour2szn = hmap_1yr.assign(hour='h'+hmap_1yr.hour.astype(str)).set_index('hour').season
    hierarchy = pd.read_csv(
        os.path.join(inputs_case,'hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')

    years = pd.read_csv(
        os.path.join(inputs_case,'modeledyears.csv')
    ).columns.astype(int).values

    peak_all = {}
    for year in years:
        peak_all[year] = get_season_peaks_hourly(
            load=load_full_yearly[['r','hour',year]].rename(columns={year:'MW'}),
            sw=sw, hierarchy=hierarchy, hour2szn=hour2szn)
        print(f'determined season peaks for {year}')
    peak_all = (
        pd.concat(peak_all, names=['t','drop']).reset_index().drop('drop', axis=1)
        [['r','szn','t','MW']]
    ).copy()


    # =============================================================================
    ### Write outputs, aggregating hours to GSw_HourlyChunkLength if necessary
    # =============================================================================
    write = {
        ### Contents are [dataframe, header, index, sep]
        ## Annual timeslice demand
        'load_allyear': [
            (load_all.reset_index().assign(h=load_all.reset_index().h.map(chunkmap))
             .groupby(['r','h']).mean()
             .round(decimals)),
            True, True, ','],
        ## Seasonal peak demand
        'peak_szn': [peak_all.round(decimals), False, False, ','],
        ## Capacity factors (i,r,h)
        'cf_vre': [
            (cf_out.assign(h=cf_out.h.map(chunkmap))
             .groupby(['i','r','h'], as_index=False).cf.mean().round(5)),
            False, False, ','],
        ## Static Canadian trade [MWh] (r,h,t)
        'net_trade_can': [
            (can_out.assign(h=can_out.h.map(chunkmap))
             .groupby(['r','h','t'], as_index=False).MWh.sum()
             .round(decimals)),
            False, False, ','],
        ## Exports to Canada [fraction] (h)
        'can_exports_h_frac': [
            (can_exports_h_frac.assign(h=can_exports_h_frac.h.map(chunkmap))
             .groupby('h', as_index=False).sum().round(6)),
            False, False, ','],
        ## Imports from Canada [fraction] (szn)
        'can_imports_szn_frac': [can_imports_szn_frac.round(6), False, False, ','],
        ## Season-peak demand hour for each szn's representative day (h,szn)
        'h_szn_prm': [
            h_szn_prm.assign(h=h_szn_prm.h.map(chunkmap)),
            False, False, ','],
        ## 8760 hour linkage set for Augur (h,szn,year,hour)
        'h_dt_szn': [
            hmap_7yr[['h','season','year','hour']].assign(h=hmap_7yr.h.map(chunkmap)),
            True, False, ','],
        ## Number of hours represented by each timeslice (h)
        'numhours': [
            (hours.reset_index().assign(h=hours.index.map(chunkmap)).groupby('h').numhours.sum()
             .reset_index()),
            False, False, ','],
        ## Hours to season mapping (h,szn)
        'h_szn': [
            h_szn.assign(h=h_szn.h.map(chunkmap)).drop_duplicates(),
            False, False, ','],
        ## h set for subsetting allh (h)
        'set_h': [
            hset.map(chunkmap).drop_duplicates().to_frame(),
            False, False, ','],
        ## szn set for subsetting allszn (szn)
        'set_szn': [set_szn, False, False, ','],
        ## periods in which to apply operating reserve constraints (szn)
        'opres_periods': [opres_periods, False, False, ','],
        ## Quarterly season weights for assigning summer/winter dependent parameters (h,szn)
        'frac_h_quarter_weights': [
            (frac_h_quarter_weights.assign(h=frac_h_quarter_weights.h.map(chunkmap))
             .groupby(['h','quarter'], as_index=False).weight.mean()
             .round(decimals+3)),
            False, False, ','],
        ## Day to season mapping for Osprey (day,szn)
        'd_szn': [period_szn_write, False, False, ','],
        ## first timeslice in season (szn,h)
        'h_szn_start': [szn2starth.map(chunkmap).reset_index(), False, False, ','],
        ## last timeslice in season (szn,h)
        'h_szn_end': [szn2endh.map(chunkmap).reset_index(), False, False, ','],
        ## minload hour windows with overlap (h,h)
        'hour_group': [hour_group, False, False, ' '],
        ###### The next parameters are just diagnostics and are not actually used in ReEDS
        ## Representative period weights for postprocessing (szn)
        'rep_period_weights': [rep_period_weights, False, False, ','],
        ## Force-included periods
        'forceperiods': [forceperiods_write, True, False, ','],
        ## Mapping from representative h to actual h
        'hmap_1yr': [
            hmap_1yr.assign(h=hmap_1yr.h.map(chunkmap)),
            False, False, ','],
        ## Mapping from representative period to actual period
        'periodmap_1yr': [
            hmap_1yr[['actual_period','season']].drop_duplicates(),
            False, False, ','],
        ###### The folowing parameters don't yet work for hourly resolution, so overwrite
        ###### their old h17 inputs with empty dataframes
        ## Canada/Mexico
        'canmexload': [pd.DataFrame(columns=['*r','h']), True, False, ','],
        ## GSw_DR
        'dr_increase': [pd.DataFrame(columns=['*i','r','h']), True, False, ','],
        'dr_decrease': [pd.DataFrame(columns=['*i','r','h']), True, False, ','],
        'dr_shifts': [pd.DataFrame(columns=['*i','h','hh']), True, False, ','],
        'dr_shed': [pd.DataFrame(columns=['*i']), True, False, ','],
        ## GSw_EV
        'ev_static_demand': [pd.DataFrame(columns=['*r','h','t']), True, False, ','],
        ## GSw_EFS_Flex
        'flex_frac_all': [pd.DataFrame(columns=['*flex_type','r','h','t']), True, False, ','],
        'peak_h': [pd.DataFrame(columns=['*r','h','t','MW']), True, False, ','],
    }


    print("Writing data CSVs")
    for f in write:
        ### Rename first column so GAMS reads it as a comment
        if not write[f][1]:
            write[f][0].rename(
                columns={write[f][0].columns[0]: '*'+str(write[f][0].columns[0])},
                inplace=True
            )
        ### If the file already exists, add a '_h17' to the filename and save it
        if debug and os.path.isfile(os.path.join(inputs_case, f+'.csv')):
            shutil.copy(
                os.path.join(inputs_case, f+'.csv'),
                os.path.join(inputs_case, f+'_h17.csv'))
        ### Write the new hourly parameters
        write[f][0].to_csv(
            os.path.join(inputs_case, f+'.csv'),
            # os.path.join(inputs_case, f+f'{figpathtail}.csv'),
            index=write[f][2], sep=write[f][3])

    ###############################################################
    ### Map resulting annual capacity factor and deviation from h17
    if make_plots >= 1:
        try:
            plot_maps(sw, inputs_case, basedir, figpath)
        except Exception as err:
            print('plot_maps failed with the following error:\n{}'.format(err))


###########################
#    -- End Functions --  #
###########################

#------------------------------------------------------------------------------------------------

#############
#%% PROCEDURE

if __name__ == '__main__':
    ###################
    #%% Argument inputs
    parser = argparse.ArgumentParser(
        description="Create the necessary 8760 and capacity factor data for hourly resolution")
    parser.add_argument("basedir",
                        help="ReEDS-2.0 directory")
    parser.add_argument("inputs_case",
                        help="ReEDS-2.0/runs/{case}/inputs_case directory")

    args = parser.parse_args()
    basedir = args.basedir
    inputs_case = args.inputs_case

    # ################################
    # #%% Inputs for reproducing a run
    # basedir = os.path.expanduser('~/github/ReEDS-2.0/')
    # inputs_case = os.path.join(
    #     basedir,'runs',
    #     'v20230109_hourlymergeM0_Pacific','inputs_case','')
    # select_year = 2012
    # make_plots = 1

    # ######################
    # #%% Inputs for testing
    # basedir = os.path.expanduser('~/github/ReEDS-2.0/')
    # inputs_case = os.path.join(
    #     basedir,'runs','v20220103_clusterM0_Ref_d5h1_PeakCountry_NoMinLoad','inputs_case','')
    # sw = pd.read_csv(
    #     os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)
    # select_year = 2012
    # make_plots = 1
    # sw['GSw_Hourly'] = 1
    # sw['GSw_HourlyType'] = 'day'
    # sw['GSw_HourlyClusterMultiYear'] = 0
    # sw['GSw_HourlyWindow'] = 7
    # sw['GSw_HourlyOverlap'] = 2
    # sw['GSw_EFS1_AllYearLoad'] = 'Clean2035'
    # sw['GSw_HourlyClusterYear'] = 2035
    # sw['GSw_HourlyChunkLength'] = 1
    # sw['GSw_HourlyClusterRegionLevel'] = 'country'
    # sw['GSw_HourlyClusterWeights'] = pd.Series({"load":1, "upv":0.5, "wind-ons":0.5})
    # sw['GSw_HourlyClusterAlgorithm'] = 'optimized'
    # sw['GSw_HourlyNumClusters'] = 50
    # sw['GSw_HourlyMinRElevel'] = 'interconnect'
    # sw['GSw_HourlyPeakLevel'] = 'interconnect'

    #%% Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

    #################
    #%% Switch inputs
    sw = pd.read_csv(
        os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)
    make_plots = int(sw.hourly_cluster_plots)

    ## Parse the GSw_HourlyClusterWeights switch
    sw['GSw_HourlyClusterWeights'] = pd.Series(json.loads(
        '{"'
        + (':'.join(','.join(sw['GSw_HourlyClusterWeights'].split('__')).split('_'))
           .replace(':','":').replace(',',',"'))
        +'}'
    ))
    ## Hard-code a GSw_CSP_Types switch as in LDC_prep.py
    sw['GSw_CSP_Types'] = [1,2]
    figpathtail = ''

    ##########
    #%% Run it
    # make_plots = 1
    # for GSw_HourlyClusterAlgorithm in ['optimized']:
    #     for GSw_HourlyClusterRegionLevel in ['transreg']:
    #         for GSw_HourlyType in ['day']:
    #             for GSw_HourlyClusterTimestep in ['hour']:
    #                 for GSw_HourlyNumClusters in range(26,51):
    #                     sw.GSw_HourlyClusterAlgorithm = GSw_HourlyClusterAlgorithm
    #                     sw.GSw_HourlyClusterRegionLevel = GSw_HourlyClusterRegionLevel
    #                     sw.GSw_HourlyType = GSw_HourlyType
    #                     sw.GSw_HourlyClusterTimestep = GSw_HourlyClusterTimestep
    #                     sw.GSw_HourlyNumClusters = GSw_HourlyNumClusters
    main(
        sw=sw, basedir=basedir, inputs_case=inputs_case,
        select_year=select_year, make_plots=make_plots,
        figpathtail='',
        # figpathtail='_{}_{}_{}_{}{}'.format(
        #     sw.GSw_HourlyClusterAlgorithm,
        #     sw.GSw_HourlyClusterRegionLevel,
        #     sw.GSw_HourlyClusterTimestep,
        #     sw.GSw_HourlyType[0], sw.GSw_HourlyNumClusters,
        # )
    )

    toc(tic=tic, year=0, process='input_processing/hourly_process.py', 
        path=os.path.join(inputs_case,'..'))
