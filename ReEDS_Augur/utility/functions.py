# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 19:31:59 2021

@author: afrazier
"""

import numba
import numpy as np
import os
import pandas as pd
import platform
import datetime
from glob import glob
import platform
import re

from ReEDS_Augur.utility.inputs import INPUTS
from ReEDS_Augur.utility.switchsettings import SwitchSettings

def adjust_tz(df, mapper=None, option='local_to_ET'):
    """Adjust hourly profiles between local and ET"""
    # Switch sign if translating ET to local
    sign = {'local_to_ET':1, 'ET_to_local':-1}[option]
    # if we're not adjusting timezones, the profiles loaded in are still
    # in local time and will require adjustment but the translation
    # back to eastern time does not need to occur, thus resetting
    # the sign appropriately based on both the switch setting and option argument
    if (option=='ET_to_local'):
        sign = 0
    shift = {'PT':3*sign, 'MT':2*sign, 'CT':1*sign, 'ET':0}
    # Get the region-to-shift map
    tz_map = INPUTS['map_BAtoTZ'].get_data()
    if mapper is not None:
        tz_map = tz_map.merge(mapper, on = 'r')
        tz_map.drop('r', axis = 1, inplace = True)
        tz_map.rename(columns = {tz_map.columns[-1]:'r'}, inplace = True)
    r_to_shift = tz_map.set_index('r').tz.map(shift).to_dict()
    # Roll each column (region) by the region-specific value of shift
    df_return = df.apply(lambda col: np.roll(col, r_to_shift[col.name]))

    return df_return

def agg_duplicates(df):
    '''
    Aggregating duplicate entries in a dataframe
    '''
    if duplicates_exist(df):
        cols = df.columns.tolist()
        val_col = cols[-1]
        cols.pop(-1)
        df = df.groupby(cols, as_index = False).sum()
        df[val_col] = df[val_col].round(
                            SwitchSettings.switches['decimals'])
        df.index = range(len(df))
    return df

def agg_profiles(df, mapper):
    '''
    Sums profiles together based on mapper. Mapper must be a dataframe with 2
    columns: the first of which has the desired profile columns and the second
    of which has the current profile columns. E.g. if you have a dataframe
    with net load by region r and want to aggregate it up to ccreg, mapper
    would need to be a dataframe with columns ['ccreg', 'r'].
    '''
    cols_to = mapper.columns[0]
    cols_from = mapper.columns[1]
    df = df.transpose().reset_index()
    df.rename(columns={df.columns[0]:cols_from}, inplace = True)
    df = mapper.merge(df, on = cols_from, how = 'right')
    df = df.groupby(cols_to).sum().transpose()
    return df

def agg_r_to_ccreg(df):
    hierarchy = INPUTS['hierarchy'].get_data()
    r_ccreg = hierarchy[['r','ccreg']]
    agg_profiles(df, r_ccreg)
    return df

def agg_rs_to_r(dfin):
    r_rs = INPUTS['r_rs'].get_data()
    ### If all r's are the same as all rs's, return the input dataframe
    if (r_rs.r == r_rs.rs).all():
        return dfin
    ### Continue
    data_col = dfin.columns[-1]
    cols = dfin.columns.tolist()
    group_cols = cols.copy()
    group_cols.remove(data_col)
    df_r = dfin[dfin['r'].isin(r_rs['r'])]
    df_rs = dfin[
        dfin['r'].isin(r_rs['rs'])
        & ~dfin['r'].isin(r_rs['r'])
    ].reset_index(drop=True)
    df_rs.rename(columns = {'r':'rs'}, inplace = True)
    df_rs = df_rs.merge(r_rs, on = 'rs')
    dfout = pd.concat([df_r, df_rs], sort = False, ignore_index = True)
    dfout = dfout.groupby(group_cols, as_index=False).sum().reindex(cols, axis=1)
    return dfout

def apply_series_to_df(df, series, method, invert = False):
    '''
    This function is used to apply mathematical operations on a dataframe with
    the values from a series with entries corresponding to the columns of the
    dataframe.
    Pass the invert argument to switch the operator for division and
    subtraction.
    '''
    series = series.set_index(series.columns[0]).transpose()
    series = series.reindex(columns = df.columns)
    series = np.tile(series.values, (len(df),1))
    if method == 'add':
        df = pd.DataFrame(columns = df.columns,
                          data = df.values + series)
    elif method == 'divide':
        if not invert:
            df = pd.DataFrame(columns = df.columns,
                              data = df.values / series)
        elif invert:
            df = pd.DataFrame(columns = df.columns,
                              data = series / df.values)
    elif method == 'multiply':
        df = pd.DataFrame(columns = df.columns,
                          data = df.values * series)
    elif method == 'subtract':
        if not invert:
            df = pd.DataFrame(columns = df.columns,
                              data = df.values - series)
        elif invert:
            df = pd.DataFrame(columns = df.columns,
                              data = series - df.values)
    return df

def convert_series_to_profiles(df, cols, vals, idx = 'index'):
    '''
    Some series are helpful to have in wide format as profiles with columns as
    the objects and the index as the hourly timeseries
    '''
    if idx == 'index':
        if 'index' not in df.columns: df['index'] = 0
    df = df.pivot(index = idx, columns = cols, values = vals)
    return df

def delete_csvs(keep=[]):
    """
    Delete temporary csv, pkl, and h5 files
    """
    dropfiles = glob(
        os.path.join('ReEDS_Augur','augur_data','*_{}*.pkl'.format(SwitchSettings.prev_year))
    ) + glob(
        os.path.join('ReEDS_Augur','augur_data','*_{}*.h5'.format(SwitchSettings.prev_year))
    ) + glob(
        os.path.join('ReEDS_Augur','augur_data','*_{}*.csv'.format(SwitchSettings.prev_year))
    ) + glob(
        os.path.join('ReEDS_Augur','augur_data',
                     'osprey_outputs_{}*.gdx'.format(SwitchSettings.prev_year))
    )
    if not len(keep):
        pass
    else:
        for keyword in keep:
            dropfiles = [f for f in dropfiles if keyword not in f]
    for f in dropfiles:
        os.remove(f)

def dr_curt_recovery(hrs, eff, ts_length, poss_dr_changes, hdtmap, marg_curt_h):
    """
    Determines the ratio of curtailment that could be used to shift DR.
    """
    # Get the battery level and curtailment recovery profiles
    curt_recovered = dr_dispatch(
        poss_dr_changes=poss_dr_changes.values,
        ts_length=ts_length, hrs=hrs, eff=eff
    )
    # Group recovered curtailment by timeslice
    curt_recovered_h = pd.DataFrame(columns=poss_dr_changes.columns.astype(str),
                                    data=curt_recovered)
    curt_recovered_h['h'] = hdtmap['h']
    curt_recovered_h = curt_recovered_h.groupby('h').sum()
    # Get the total amount of recovered curtailment
    curt_recovered = curt_recovered_h.sum()
    # Determine the fraction of recovered energy that was recovered during
    # each timeslice
    curt_recovered_h_frac = pd.DataFrame(
        columns=poss_dr_changes.columns,
        data=np.divide(curt_recovered_h.values,
                       curt_recovered.values,
                       out=np.zeros_like(curt_recovered_h),
                       where=curt_recovered != 0))

    # Get the ratio of recovered curtailment to total curtailment
    results = pd.DataFrame(
        index=marg_curt_h.index, columns=marg_curt_h.columns,
        data=np.divide(curt_recovered_h.values,
                       marg_curt_h.values,
                       out=np.zeros_like(curt_recovered_h.values),
                       where=marg_curt_h.values != 0))
    return results


def duplicates_exist(df, ignore_col = 'last'):
    '''
    Checking to see if there are duplicate entries in a dataframe
    '''
    if ignore_col == 'last':
        cols = df.columns.tolist()
        cols.pop(-1)
        df_test = df[cols]
        df_test = df_test[df_test.duplicated()]
        if len(df_test) > 0:
            result = True
        else:
            result = False
    else:
        result = None
    return result

def expand_df(df, expand, old_col, new_col, drop_cols):
    '''
    Expands the columns of a dataframe to have a finer resolution (e.g. from
    load by region to source load by transmission path)
    '''
    df = df.T
    cols = [old_col] + df.columns.tolist()
    df.reset_index(inplace=True)
    df.columns = cols
    df = pd.merge(left=expand, right=df, on=old_col, how='left')
    df.drop(drop_cols, axis=1, inplace=True)
    df.set_index(new_col, inplace=True)
    df = df.T

    return df


def expand_star(df, index=True, col=None):
    """
    expands technologies according to GAMS syntax
    if index=True, uses index as technology to expand
    otherwise uses col
    """
    def expand(df):
        df_new = pd.DataFrame(columns=df.columns)
        for subset in df.index:
            temp_save = []
            if '*' in subset:
                temp_remove = df.loc[[subset]]
                df.drop(subset,inplace=True)
                temp = subset.split('*')
                temp2 = temp[0].split('_')
                temp_low = pd.to_numeric(temp[0].split('_')[-1])
                temp_high = pd.to_numeric(temp[1].split('_')[-1])
                temp_tech = ''
                for n in range(0, len(temp2)-1):
                    temp_tech += temp2[n]
                    if not n == len(temp2)-2:
                        temp_tech += '_'
                for c in range(temp_low, temp_high+1):
                    temp_save.append('{}_{}'.format(temp_tech, str(c)))
                df_new = pd.concat([df_new,
                    pd.DataFrame(np.repeat(temp_remove.values, len(temp_save), axis=0),
                                 index=temp_save, columns=df.columns)])
        return pd.concat([df, df_new])

    if index:
        return expand(df)
    else:
        tmp = expand(df.set_index(col))
        return tmp.reset_index()


def filter_data_year(profile, data_years, reset_index=True):
    ### Integer index
    data_year_map = INPUTS['h_dt_szn'].get_data()
    if type(profile.index[0]) is int:
        data_year_index = data_year_map['year'].isin(data_years)
        profile = profile[data_year_index]
    ### Assume index is of form (season, year, h, hour)
    elif type(profile.index[0]) is tuple:
        if len(data_years) == 1:
            profile = profile.xs(data_years[0], level='year')
        elif len(data_years) == 7:
            ### Assume input profile is 7 years long
            pass
        else:
            raise Exception('Can only accept data_years (osprey_years) of 1 or 7 years')

    if reset_index:
        profile.reset_index(drop=True, inplace=True)

    return profile

def format_osprey_profiles(net_load):

    # Create hour and day columns
    order = pd.DataFrame()
    order_day_ahead = pd.DataFrame()
    def flatten(l): return [item for sublist in l for item in sublist]
    day = flatten([
        ['d'+str(i+1)]*24
        for i in range(365 * SwitchSettings.switches['osprey_num_years'])])
    order['d'] = day
    hour = ['hr'+str(i+1) for i in range(24)] * 365 * SwitchSettings.switches['osprey_num_years']
    order['hr'] = hour

    # Roll the hour and day columns for the day ahead load
    day = np.roll(order.d.values, 24)
    hour = np.roll(order.hr.values, 24)
    hour = np.array(['hr'+str(int(i[2:]) + 24) for i in hour])
    order_day_ahead['d'] = day
    order_day_ahead['hr'] = hour
    order_day_ahead.index = range(len(order),len(order)*2)

    # Combine the load and day ahead load into a single table
    order = pd.concat([order, order_day_ahead])
    order['c1'] = order.d.str[1:].astype(int)
    order['c2'] = order.hr.str[2:].astype(int)
    order = order.sort_values(by=['c1', 'c2'])
    order = order.drop(columns=['c1', 'c2'])

    # Combine the load and day ahead load into a single table
    df = pd.DataFrame()
    df['d'] = order['d']
    df['hr'] = order['hr']
    for col in net_load.columns:
        df[col] = np.array(
                        net_load[col].tolist() * 2)[order.index]
    df.index = range(0,len(df))
    return df

def format_prod_cap(avail_cap):
    '''
    Formatting H2 and DAC capacity for Osprey
    '''
    if SwitchSettings.switches['gsw_h2'] != '0':
        techs = INPUTS['i_subsets'].get_data()
        consume_flex = []
        for t in SwitchSettings.switches['flex_consume_techs']:
            consume_flex += techs[t]
        h2_cap = avail_cap[avail_cap['i'].isin(consume_flex)]
        h2_cap = h2_cap.groupby(['r', 'szn'], as_index = False).sum()
        h2_cap = map_szn_to_day(h2_cap)
        h2_cap = h2_cap[['d', 'r', 'MW']]
    else:
        h2_cap = pd.DataFrame(columns = ['d', 'r', 'MW'])
    return h2_cap

def format_prod_flex(cap_prod, net_load, prod_load):
    '''
    Distributing the produce requirement for flexible resource across the hours
    with lowest net load. Demand from inflexible techs is handled in
    format_prod_load.
    '''
    prod_load_formatted = pd.DataFrame(columns=['d', 'r', 'MWh'])
    def flatten(l): return [item for sublist in l for item in sublist]
    day = flatten([
        ['d'+str(i+1)]*24
        for i in range(365 * SwitchSettings.switches['osprey_num_years'])])
    net_load['d'] = day
    # Sort net load by region
    for r in prod_load['r'].drop_duplicates():
        temp_cap = cap_prod[cap_prod['r'] == r]
        # get total demand
        temp_load = prod_load.loc[prod_load['r'] == r, 'MWh'].sum()
        temp = net_load[['d', r]]
        temp = temp.sort_values(r, ignore_index = True)
        temp = temp.merge(temp_cap, on='d', how='left')
        temp['prod'] = temp[['MW']].cumsum()
        # Only produce electricity up to the total demand
        margin = temp[temp['prod'] > temp_load].reset_index(drop=True)[0:1]
        temp = temp[temp['prod'] < temp_load]
        temp = pd.concat([temp, margin], sort=False, ignore_index=True)

        # if only 1 hour is needed to cover demand, MW needed = temp_load
        if len(temp) == 1:
            temp.loc[len(temp)-1, 'prod'] = temp_load
            temp.loc[len(temp)-1, 'MW'] = temp_load
        # in all other cases, adjust MW of margin to add up to temp_load
        else:
            temp.loc[len(temp)-1, 'prod'] = temp_load
            temp.loc[len(temp)-1, 'MW'] = temp.loc[len(temp)-1, 'prod'] \
                                          - temp.loc[len(temp)-2, 'prod']

        # Sum demand up for each day to be sent to Osprey
        temp = temp[['d', 'r', 'MW']].groupby(['d', 'r'], as_index=False).sum()
        temp.rename(columns={'MW':'MWh'}, inplace=True)
        prod_load_formatted = pd.concat([prod_load_formatted, temp],
                                        sort=False,
                                        ignore_index=True)
    return prod_load_formatted

def format_prod_load():
    '''
    Fromatting consumption for H2 production and DAC for Osprey. Demand from
    flexible technologies (e.g. electrolyzers and DAC) is filtered out and
    sent to format_prod_flex later. Demand from inflexible technologies is
    summed together by BA and added to the net load profiles sent to Osprey.
    '''
    h_map = INPUTS['h_dt_szn'].get_data()
    rfeas = INPUTS['rfeas'].get_data()
    hdtmap_index = h_map.set_index(['season','year','h','hour']).index
    consumption = INPUTS['consumption_demand'].get_data()

    if SwitchSettings.switches['gsw_h2'] != '0' and \
       SwitchSettings.prev_year >= int(SwitchSettings.switches['gsw_h2_demand_start']) and \
       not consumption.empty:
        techs = INPUTS['i_subsets'].get_data()
        consume_flex = []
        for t in SwitchSettings.switches['flex_consume_techs']:
            consume_flex += techs[t]
        # Split flexible and inflexible consumption
        cons_flex = consumption[consumption['i'].isin(consume_flex)]
        cons_noflex = consumption[~consumption['i'].isin(consume_flex)]
        # Merge in hours and get demand in MWh
        cons_flex = get_prop(cons_flex, 'hours', merge_cols = ['h'])
        cons_flex['MWh'] *= cons_flex['hours']
        
        ## Get rid of the number of hours of operation since we want to distribute it evenly across all days
        cons_flex = cons_flex.drop(columns = ['hours'], axis = 1)
        ## Map seasons to total number of hours
        hrs_szn = get_prop(INPUTS['hours'].get_data(),
                           'h_szn', merge_cols = ['h']).drop(columns = ['h'],axis = 1).groupby(['szn']).sum()
        # Convert from h to szn and get average prod by day for each szn
        cons_flex = get_prop(cons_flex, 'h_szn', merge_cols = ['h'])
        cons_flex = cons_flex.groupby(['i', 'v', 'r', 'szn'],
                                          as_index = False).sum()
        ## Merge with the number of hours in the season 
        cons_flex = cons_flex.merge(hrs_szn, on = 'szn')
        
        cons_flex['MWh'] /= cons_flex['hours']
        cons_flex['MWh'] *= 24
        # Convert from szn to d for flexible consumption
        cons_flex = map_szn_to_day(cons_flex)
        cons_flex = cons_flex[['d', 'r', 'MWh']]
        cons_flex['MWh'] = round(cons_flex['MWh'],
                                       SwitchSettings.switches['decimals'])
        # Eliminate entries that round to zero. (They'll throw errors in format_prod_flex())
        cons_flex = cons_flex.loc[cons_flex['MWh'] > 0 ]
        # Create hourly profiles for inflexible consumption
        h_map.rename(columns={'season':'szn'}, inplace=True)
        h_map['szn'].replace('winter', 'wint', inplace=True)
        h_map['szn'].replace('summer', 'summ', inplace=True)
        h_map['szn'].replace('spring', 'spri', inplace=True)
        cons_noflex['MWh'] = cons_noflex['MWh'].round(
                                        SwitchSettings.switches['decimals'])
        cons_noflex = cons_noflex.groupby(['r', 'h'], as_index=False).sum()
        cons_noflex = cons_noflex.pivot(index='h',
                                        columns='r',
                                        values='MWh').reset_index()
        cons_noflex = cons_noflex.merge(h_map[['h']],
                                        on='h',
                                        how='right').fillna(0)
        cons_noflex.drop('h', axis=1, inplace=True)
        cons_noflex = cons_noflex.reindex(columns=rfeas['r']).fillna(0)
        ### Add (szn,year,h,hour) index
        cons_noflex.index = hdtmap_index

    else:
        cons_flex = pd.DataFrame(columns=['d', 'r', 'MWh'])
        cons_noflex = pd.DataFrame(
            columns=rfeas['r'], index=hdtmap_index, data=0)
    return cons_flex, cons_noflex

def format_trancap():
    '''
    Get transmission capacity. Combine AC and LCC DC lines.
    '''
    trancap = INPUTS['trancap'].get_data()
    trancap = (
        trancap.loc[trancap.trtype.isin(['AC','LCC','B2B'])]
        .groupby(['r','rr'], as_index=False).sum()
        .sort_values(['r','rr'], ignore_index=True)
        .assign(trtype='AC')
        .append(trancap.loc[trancap.trtype == 'VSC'])
        .reindex(['r','rr','trtype','MW'], axis=1)
        .round(SwitchSettings.switches['decimals'])
    ).set_index(['r','rr','trtype']).MW
    ### Add zeroes
    append = []
    for (r,rr,trtype), val in trancap.iteritems():
        if (rr,r,trtype) not in trancap:
            append.append(pd.DataFrame({'r':rr,'rr':r,'trtype':trtype,'MW':0}, index=[0]))
    trancap = trancap.reset_index().append(append).reset_index(drop=True)
    return trancap

def format_tranloss():
    """
    Get transmission losses. Take weighted average for AC and LCC DC lines.
    """
    tranloss = INPUTS['tranloss'].get_data()
    trancap = INPUTS['trancap'].get_data()
    tranloss = tranloss.merge(trancap, on=['r','rr','trtype'], how='right')
    tranloss = (
        weighted_average(
            df=tranloss.loc[tranloss.trtype.isin(['AC','LCC','B2B'])],
            data_cols=['tranloss'], weighter_col='MW', groupby_cols=['r','rr'])
        .sort_values(['r','rr'], ignore_index = True)
        .assign(trtype='AC')
        .append(tranloss.loc[tranloss.trtype=='VSC', ['r','rr','trtype','tranloss']])
        .reindex(['r','rr','trtype','tranloss'], axis=1)
        .round(SwitchSettings.switches['decimals'])
    )
    ### Add the opposite direction, then drop duplicates
    ### (since we need both directions for C2_marginal_curtailment)
    tranloss = pd.concat([tranloss, tranloss.rename(columns={'r':'rr','rr':'r'})]).drop_duplicates()
    return tranloss

def get_prop(df, prop, merge_cols = None, method = 'left', na_val = 0):
    '''
    Get a property and merge it in based on merge_cols specified
    '''
    assert merge_cols is not None
    prop_df = INPUTS[prop].get_data()
    df = pd.merge(left = df, right = prop_df, on = merge_cols, how = method)
    df.fillna(na_val)
    return df

def get_remaining_cycles_per_day(stor_level,
                                 marg_curt_exist_stor_recovery_ratio,
                                 resource_device_utility,
                                 d_hr, cap_stor, daily_cycle_limit):
    """
    Gets the remaining cycles per day available to existing storage
    """

    df = pd.DataFrame(columns=stor_level.columns,
                      data=np.diff(stor_level.values, axis=0))
    df.loc[len(df), :] = 0
    df = pd.DataFrame(columns=df.columns,
                      data=np.clip(df.values, a_min=0, a_max=None))
    df = pd.concat([d_hr[['d']], df], axis=1, sort=False)
    df = df.groupby('d').sum()
    df = df.mean().reset_index().rename(columns={'index': 'device',
                                                 0: 'avg_charge'})
    df = df.merge(cap_stor[['device', 'MWh', 'duration']], on='device')
    df['avg_cycles'] = df['avg_charge'] / df['MWh']
    df['avg_remaining'] = daily_cycle_limit - df['avg_cycles']
    df['avg_remaining'] = np.clip(df['avg_remaining'], a_min=0, a_max=None)
    df = pd.merge(left=resource_device_utility[['resource_device', 'device']],
                  right=df[['device', 'avg_remaining']],
                  on='device', how='right')
    df.sort_values('resource_device', inplace=True)
    df.drop('device', axis=1, inplace=True)
    df.set_index('resource_device', inplace=True)
    df = df.T
    columns = marg_curt_exist_stor_recovery_ratio.columns.to_list()
    unused = [x for x in columns if x not in df.columns]
    for col in unused:
        df[col] = 0
    df = df[columns]

    return df

def get_startup_costs():
    '''
    Start-up costs come from the TEPPC WECC database
    '''
    df = INPUTS['wecc_data'].get_data()
    df = df.loc[
        ~df.i.str.startswith('csp'),
        ['i','Start Cost/cap']
    ].fillna(0).round(SwitchSettings.switches['decimals'])
    return df

def get_storage_eff():
    '''
    Getting storage efficiency
    '''
    df = INPUTS['storage_eff'].get_data()
    techs = INPUTS['i_subsets'].get_data()
    df = df[df['i'].isin(techs['storage_standalone'])].reset_index(drop=True)
    return df

def get_relative_step_sizes(yearset, target_step):
    '''
    Checking the relative ReEDS temporal step sizes for this solve year and
    any previous solve year, specified by 'target_step'
    '''
    solve_year = SwitchSettings.prev_year
    i = yearset.index(solve_year)
    next_year = yearset[i+1]

    j = yearset.index(target_step)
    targ_prev = yearset[j-1]

    relative_step_sizes = (next_year - solve_year) / (target_step - targ_prev)
    return relative_step_sizes

def map_rs_to_r(df):
    '''
    Change the values in the 'r' column of a dataframe from 's' regions to
    'p' regions. The 'r' column could have a mixture of both 's' and 'p'
    regions and this will still work fine.
    '''
    r_rs = INPUTS['r_rs'].get_data()
    r_rs.columns = ['rs','r']
    df = df.merge(r_rs, on='r', how='left')
    df.rename(columns={'r':'rs','rs':'r'}, inplace = True)
    df['r'].fillna(df['rs'], inplace = True)
    df.drop('rs', axis = 1, inplace = True)
    return df

def map_szn_to_day(df):
    '''
    Map 'szn' column to 'd' column
    '''
    d_szn = INPUTS['d_szn'].get_data()
    df = df.merge(d_szn, on = 'szn')
    return df

def printscreen(txt, outlined=False):
    if platform.system() != 'Linux':
        if outlined:
            print('\n##############################')
            print(txt)
            print('##############################\n')
        else:
            print(txt)

def set_marg_vre_step_size():
    '''
    Marginal vre step size has a default floor value of 1000 MW but
    here we check to see if it needs to be higher. The function looks
    back by the number of steps specified by 'marg_vre_steps' and computes
    the max of the average new vre investment in those previous steps.
    We take the max of that value and 1000 MW to set the set size.
    The fuction also accounts for potentially varying step sizes in ReEDS.
    '''
    #  load yearset for getting various previous steps
    yearset = INPUTS['yearset'].get_data()['t'].tolist()

    # collect list of previous years and their relative step sizes
    prev_year_list = []
    step_sizes = []
    for step in range(0, SwitchSettings.switches['marg_vre_steps']):

        # try-except to handle cases where there aren't multiple
        # steps to go back to (e.g. running Augur after 1st solve)
        try:
            target_last_step = yearset[yearset.index(SwitchSettings.prev_year)-step]

            # only look at steps beyond the previous year if the step sizes
            # are less than 5 years
            if (SwitchSettings.prev_year - target_last_step) < 5:
                step_sizes.append(get_relative_step_sizes(yearset, target_last_step))
                prev_year_list.append(target_last_step)
        except:
            pass
    relative_step_sizes = pd.DataFrame(list(zip(prev_year_list, step_sizes)),
                                            columns=['t', 'step'])

    # load investment data for all techs
    techs = INPUTS['i_subsets'].get_data()
    inv = INPUTS['cap_inv'].get_data()

    # get investment from any previous steps under consideration
    inv_last_years = inv[inv['t'].isin(prev_year_list)]
    inv_vre = inv_last_years[inv_last_years['i'].isin(techs['vre'])]

    # map inv_vre to ccregions
    hierarchy = INPUTS['hierarchy'].get_data()
    r_ccreg = hierarchy[['r','ccreg']].drop_duplicates()
    inv_vre = inv_vre.merge(r_ccreg, on = 'r')

    # aggregate by tech and then and compute average across the appropriate
    # geographic resolution - r for curtailment, ccreg for capacity credit
    marg_vre_mw = {}
    for level in ['r','ccreg']:
        df = inv_vre.groupby([level, 't'], as_index = False).sum()
        df = df.groupby(['t'], as_index=False).mean()

        # adjust each previous step by its relative step size
        df = df.merge(relative_step_sizes, on='t')
        df['MW'] *= df['step']

        # now get max across all previous steps and set as marg_vre_mw
        marg_vre_mw[level] = int(round(df['MW'].max(), 0))

    SwitchSettings.switches['marg_vre_mw_curt'] = max(
        SwitchSettings.switches['marg_vre_mw'], marg_vre_mw['r'])
    SwitchSettings.switches['marg_vre_mw_cc'] = max(
        SwitchSettings.switches['marg_vre_mw'], marg_vre_mw['ccreg'])
    for i in ['marg_vre_mw_curt','marg_vre_mw_cc']:
        print(f'{i} set to {SwitchSettings.switches[i]}')


def storage_dispatch(poss_batt_changes, ts_length, eff, e):
    """
    Calculate the battery level and curtailment recovery profiles.
    Since everything here is in numpy, we can try using numba.jit to speed it up.
    """
    # Initialize some necessary arrays since numba can't do np.clip
    zeros = np.zeros((1, poss_batt_changes.shape[1]))
    es = np.ones((1, poss_batt_changes.shape[1])) * e
    # Initialize the state-of-charge to be 0 in all hours
    batt_e_level = np.zeros((ts_length, poss_batt_changes.shape[1]))
    # Allow for charging during the first hour, adjusting for losses.
    # NOTE: we are assuming storage starts the time-series with 0 state-of-charge
    batt_e_level[0, :] = np.maximum(poss_batt_changes[0, :] * eff, 0)
    # Account for any curtailment recovery that happens in this first hour
    curt_recovered = np.zeros((ts_length, poss_batt_changes.shape[1]))
    curt_recovered[0, :] = np.maximum(poss_batt_changes[0, :] * eff, 0)
    for n in range(1, ts_length):
        # Change the state-of-charge from the previous hour, either increasing
        # it for recovery of curtailment (and accounting for losses) or
        # decreasing it to serve load
        batt_e_level[n, :] = batt_e_level[n-1, :] + np.where(
            poss_batt_changes[n, :] > 0,
            poss_batt_changes[n, :] * eff,
            poss_batt_changes[n, :])
        # Constrain the state-of-charge to be between 0 and marg_stor_MWh
        # batt_e_level[n, :] = np.clip(batt_e_level[n, :], a_min=0, a_max=e)
        batt_e_level[n, :] = np.maximum(np.minimum(batt_e_level[n, :], es), zeros)
        # Determine the amount of otherwise-curtailed energy that was
        # recovered during this hour, accounting for losses
        curt_recovered[n, :] = np.maximum(
            0, (batt_e_level[n, :] - batt_e_level[n-1, :]) / eff)
    return batt_e_level, curt_recovered

def storage_curt_recovery(e, eff, ts_length, poss_batt_changes, hdtmap,
                          marg_curt_h):
    """
    Determines the ratio of curtailment that could be used to charge storage.
    """
    # Get the battery level and curtailment recovery profiles
    batt_e_level, curt_recovered = storage_dispatch(
        poss_batt_changes=poss_batt_changes.values, 
        ts_length=ts_length, eff=eff, e=e
    )
    # Group recovered curtailment by timeslice
    curt_recovered_h = pd.DataFrame(columns=poss_batt_changes.columns.astype(str),
                                    data=curt_recovered)
    curt_recovered_h['h'] = hdtmap['h']
    curt_recovered_h = curt_recovered_h.groupby('h').sum()
    # Get the total amount of recovered curtailment
    curt_recovered = curt_recovered_h.sum()
    # Determine the fraction of recovered energy that was recovered during
    # each timeslice
    curt_recovered_h_frac = pd.DataFrame(
        columns=poss_batt_changes.columns,
        data=np.divide(curt_recovered_h.values,
                       curt_recovered.values,
                       out=np.zeros_like(curt_recovered_h),
                       where=curt_recovered != 0))
    # Distribute the leftover "unrecovered" energy across all timeslices
    # according to the amount recovered in each timeslice.
    curt_unrecovered = np.tile(batt_e_level[-1, :], (len(curt_recovered_h), 1))
    curt_unrecovered *= curt_recovered_h_frac.values
    # Remove this excess energy from the recovered curtailment
    curt_recovered_h -= curt_unrecovered
    # Get the ratio of recovered curtailment to total curtailment
    results = pd.DataFrame(
        index=marg_curt_h.index, columns=marg_curt_h.columns,
        data=np.divide(curt_recovered_h.values,
                       marg_curt_h.values,
                       out=np.zeros_like(curt_recovered_h.values),
                       where=marg_curt_h.values != 0))

    return results

def toc(tic, year, process, path=''):
    """
    append timing data to meta file
    """
    now = datetime.datetime.now()
    try:
        with open(os.path.join(path,'meta.csv'), 'a') as METAFILE:
            METAFILE.writelines(
                '{},{},{},{},{}\n'.format(
                    year, process,
                    datetime.datetime.isoformat(tic), datetime.datetime.isoformat(now),
                    (now-tic).total_seconds()
                )
            )
    except:
        print('meta.csv not found or not writeable')
        pass

def weighted_average(df, data_cols, weighter_col, groupby_cols,
                     new_col = False, old_col = False):
    '''
    Get a weighted average of all data_cols indexed by groupby_cols and
    weighted by weighter_col. Options to rename the new resulting column.
    '''
    df_avg = df.copy()
    for data_col in data_cols:
        df_avg[data_col] = df_avg[data_col] * df_avg[weighter_col]
    df_avg = df_avg.groupby(by=groupby_cols, as_index=False).mean()
    for data_col in data_cols:
        df_avg[data_col] = df_avg[data_col] / df_avg[weighter_col]
    df_avg.drop(weighter_col, axis=1, inplace=True)
    if new_col and old_col:
        df_avg.rename(columns={old_col: new_col}, inplace=True)
    return df_avg

def dr_dispatch(poss_dr_changes, ts_length, hrs, eff=1):
    """
    Calculate the battery level and curtailment recovery profiles.
    Since everything here is in numpy, we can try using numba.jit to speed it up.
    """
    # Initialize some necessary arrays since numba can't do np.clip
    curt = np.where(poss_dr_changes > 0, poss_dr_changes, 0)
    avail = np.where(poss_dr_changes < 0, -poss_dr_changes, 0)
    # Initialize the dr shifting and curtailment recovery to be 0 in all hours
    curt_recovered = np.zeros((ts_length, poss_dr_changes.shape[1]))
    # Loop through all hours and identify how much curtailment that hour could
    # mitigate from the available load shifting
    for n in range(0, ts_length):
        n1 = max(0, n-hrs[0])
        n2 = min(ts_length, n+hrs[1])
        # maximum curtailment this hour can shift load into
        # calculated as the cumulative sum of curtailment across all hours
        # this hour can reach, identifying the max cumulative shifting allowed
        # and subtracting off the desired shifting that can't happen
        cum = np.cumsum(curt[n1:n2, :], axis=0)
        curt_shift = np.maximum(curt[n1:n2, :] - (cum - np.minimum(cum, avail[n, :] / eff)), 0)
        # Subtract realized curtailment reduction from appropriate hours
        curt[n1:n2, :] -= curt_shift
        # Record the amount of otherwise-curtailed energy that was
        # recovered during appropriate hours
        curt_recovered[n1:n2, :] += curt_shift
    return curt_recovered

def dr_capacity_credit(hrs, eff, ts_length, poss_dr_changes, marg_peak, cols,
                       maxhrs):
    """
    Determines the ratio of peak load that could be shifted by DR.
    """
    # Get the DR profiles
    # This is using the same function as curtailment, but with opposite meaning
    # ("how much can I increase load in this hour in order to reduce load in any
    # shiftable hours" instead of "how much can I decrease load in this hour
    # in order to increase load in any shiftable hours"), so the efficiency
    # gets applied to the opposite set of data. Hence the 1/eff.
    # If maxhrs is included, that is used as the total number of hours the
    # resource is able to be called. Really just for shed
    peak_shift = dr_dispatch(
        poss_dr_changes=poss_dr_changes,
        ts_length=ts_length, hrs=hrs, eff=1/eff
    )
    # Sort and only take maximum allowed hours
    sort_shift = np.sort(peak_shift, axis=0)[::-1]
    sort_shift = sort_shift[0:int(min(maxhrs, ts_length)), :]

    # Get the ratio of reduced peak to total peak
    results = pd.melt(
        pd.DataFrame(data=[np.round(sort_shift.sum(0) / marg_peak, decimals=5), ],
                     columns=cols)
        )
    return results
