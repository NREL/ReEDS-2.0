#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 15:53:24 2019

@author: ngates
This file contains helpful functions used throughout the Augur module.
"""

import gdxpds
import os
import numpy as np
import pandas as pd
import time
import platform

#%% Define utility functions

_tstart_stack = []


# The tic and toc functions are used to track the run time of any code changes
def tic():
    _tstart_stack.append(time.time())


def toc(fmt='Elapsed: %s s'):
    print1(fmt % (time.time() - _tstart_stack.pop()))


# Adjusts hourly profiles from local to ET and back
def adjust_tz(df, tz_map, option='local_to_ET'):

    pt_shift = 3
    mt_shift = 2
    ct_shift = 1

    if option == 'ET_to_local':
        pt_shift *= -1
        mt_shift *= -1
        ct_shift *= -1

    df_pt = df[tz_map[tz_map['tz'] == 'PT']['r'].tolist()]
    df_pt = pd.DataFrame(columns=df_pt.columns,
                         data=np.roll(df_pt.values, pt_shift, axis=0))
    df_mt = df[tz_map[tz_map['tz'] == 'MT']['r'].tolist()]
    df_mt = pd.DataFrame(columns=df_mt.columns,
                         data=np.roll(df_mt.values, mt_shift, axis=0))
    df_ct = df[tz_map[tz_map['tz'] == 'CT']['r'].tolist()]
    df_ct = pd.DataFrame(columns=df_ct.columns,
                         data=np.roll(df_ct.values, ct_shift, axis=0))
    df_et = df[tz_map[tz_map['tz'] == 'ET']['r'].tolist()]
    df_return = pd.concat([df_pt, df_mt, df_ct, df_et], sort=True, axis=1)
    df_return = df_return[tz_map['r'].tolist()]

    return df_return


# Grabs all the tech subsets from the tech_subset_table.csv file
def tech_types(args):

    # Read from tech-subset-table.csv
    tech_table = pd.read_csv(os.path.join(args['reeds_path'],'A_Inputs','inputs','generators','tech_subset_table.csv'), index_col=0)

    techs = {tech: list() for tech in list(tech_table)}
    for tech in techs.keys():
        techs[tech] = tech_table[
            tech_table[tech] == 'YES'].index.values.tolist()
        techs[tech] = [x.lower() for x in techs[tech]]
        temp_save = []
        temp_remove = []
        # Interpreting GAMS syntax in tech-subset-table.csv
        for subset in techs[tech]:
            if '*' in subset:
                temp_remove.append(subset)
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
        for subset in temp_remove:
            techs[tech].remove(subset)
        techs[tech].extend(temp_save)

    return techs


# Gets wind capacity by build year
def get_wind_cap(gdxin):
    df_start = gdxin['cap_wind_init'].copy()
    df_new = gdxin['cap_wind_inv'].copy()
    df_ret = gdxin['cap_wind_ret'].copy()
    # Set column names
    df_start.columns = ['i', 'v', 'r', 't', 'MW']
    df_new.columns = ['i', 'v', 'r', 't', 'MW']
    df_ret.columns = ['i', 'v', 'r', 'Ret Capacity']
    # Combine the starting capacity and new capacity additions into a single df
    df = pd.concat([df_start, df_new], sort=False).sort_values(
            ['i', 'v', 'r', 't']).reset_index(drop=True)
    # Retire renewable generators by oldest year first
    df['count'] = df.groupby([c for c in ['i', 'v', 'r']]).cumcount()+1
    if not df_ret.empty:
        df = pd.merge(left=df, right=df_ret, on=['i', 'v', 'r'],
                      how='left').fillna(0)
        df.loc[df['count'] == 1, 'Left to retire'] = \
            df.loc[df['count'] == 1, 'Ret Capacity']
        for i in range(0, len(df), 1):
            if i + 1 < len(df):
                if df.loc[i+1, 'count'] == 1 + df.loc[i, 'count']:
                    df.loc[i+1, 'Left to retire'] = \
                        df.loc[i, 'Left to retire'] - df.loc[i, 'MW']
                if df.loc[i+1, 'Left to retire'] < 0:
                    df.loc[i+1, 'Left to retire'] = 0
            df.loc[i, 'MW'] -= df.loc[i, 'Left to retire']
    if not df.empty:
        df = df[df['MW'] > 0.01].reset_index(drop=True)

    return df[['i', 'v', 'r', 't', 'MW']]


# Gets capacity, sets the "i" column values to all lower case.
# Also aggregates capacity up to the "return_cols" that are specified.
def get_cap(gdxin, key, col_names=['i', 'v', 'r', 'MW'],
            return_cols=['i', 'v', 'r']):
    if key == 'cap_wind':
        df = get_wind_cap(gdxin)
    else:
        df = gdxin[key].copy()
        df.columns = col_names
        df.i = df.i.str.lower()
    if not df.empty:
        df = df.groupby(return_cols, as_index=False).sum()
    return df


# Perform a spatial aggregation on a dataframe in long format
def spatial_agg(df, mapper, base_region, map_region, value_col):

    df = pd.merge(left=df, right=mapper, on=base_region, how='left')
    merge_cols = df.columns.tolist()
    merge_cols.remove(value_col)
    merge_cols.remove(base_region)
    df = df.groupby(merge_cols, as_index=False).sum()

    return df


# Gets the capacity of PV and aggregate csp-ns with the best UPV resource
#   class available.
def get_solar_cap(gdxin, r_rs, resources, techs, args):

    # def agg_cspns_with_pv(cap_cspns, cap_pv, techs):

    #     resources_upv = resources[resources['i'].isin(techs['UPV'])]
    #     resources_upv = resources_upv.reset_index(drop=True)
    #     best_resources_upv = resources_upv[['i', 'r']].drop_duplicates(
    #             subset='r', keep='last').set_index('r')
    #     # for r in cap_cspns['r'].tolist():
    #     #     cap_cspns.loc[cap_cspns['r'] == r, 'i'] = \
    #     #         best_resources_upv.loc[r, 'i']
    #     # cap_solar = pd.concat([cap_pv, cap_cspns], sort=False)
    #     cap_solar = cap_solar.reset_index(drop=True)
    #     cap_solar = cap_solar.groupby(['i', 'r'], as_index=False).sum()

    #     return cap_solar

    # Get capacities
    # cap_cspns = get_cap(gdxin, 'cap_cspns', col_names=['i', 'v', 'rs', 'MW'],
    #                     return_cols=['i', 'rs'])
    # cap_cspns = spatial_agg(cap_cspns, r_rs, 'rs', 'r', 'MW')
    cap_pv = get_cap(gdxin, 'cap_pv', return_cols=['i', 'r'])

    # if not cap_cspns.empty:
    #     cap_solar = agg_cspns_with_pv(cap_cspns, cap_pv, techs)
    # else:
    cap_solar = cap_pv.copy()

    return cap_solar


# Gets the amount of csp-ns that is added to upv so capacity credit and
# marginal curtailment can be allocated accordingly.
def get_cspns_frac(gdxin, r_rs, resources, techs):

    cap_pv = get_cap(gdxin, 'cap_pv', return_cols=['i', 'r'])
    resources_upv = resources[resources['i'].isin(techs['UPV'])].reset_index(
            drop=True)
    best_resources_upv = resources_upv[['i', 'r']].drop_duplicates(
            subset='r', keep='last').reset_index(drop=True)
    best_resources_upv = best_resources_upv.merge(
        cap_pv, on=['i', 'r'], how='left').fillna(0).rename(
            columns={'MW': 'upv'})
    cap_cspns = get_cap(gdxin, 'cap_cspns', col_names=['i', 'v', 'rs', 'MW'],
                        return_cols=['i', 'rs'])
    if not cap_cspns.empty:
        cap_cspns = r_rs.merge(cap_cspns, on='rs', how='right')[
                ['i', 'r', 'rs', 'MW']].rename(columns={'MW': 'cspns'})
        for r in cap_cspns['r'].tolist():
            cap_cspns.loc[cap_cspns['r'] == r, 'i'] = best_resources_upv.loc[
                    best_resources_upv['r'] == r, 'i'].values[0]
        cap_csp_pv = cap_cspns.merge(best_resources_upv, on=['i', 'r'],
                                     how='right').fillna(0)
        cap_solar = cap_csp_pv.copy()
        cap_solar['total'] = cap_solar['upv'] + cap_solar['cspns']
        cap_solar = cap_solar[['i', 'r', 'total']].groupby(
                ['i', 'r'], as_index=False).sum()
        cap_csp_pv = cap_csp_pv.merge(cap_solar, on=['i', 'r'], how='left')
        cap_csp_pv['cspns_frac'] = cap_csp_pv['cspns'] / cap_csp_pv['total']
        cap_csp_pv = cap_csp_pv[cap_csp_pv['rs'] != 0].reset_index(drop=True)
        df = cap_csp_pv[['i', 'r', 'rs', 'cspns_frac']]
    else:
        df = pd.DataFrame(columns=['i', 'r', 'rs', 'cspns_frac'])

    return df


# Gets capacity used in Osprey
def get_osprey_cap(gdxin, r_rs, min_plant_size=5):
    '''
    Getting capacity used in Osprey.
        - Thermal capacity
        - CSP capacity
    Actions performed:
        - aggregated CSP capacity up to the BA level
        - drop all capacity that is less than X MW
            - The default value of X is 5 MW
    '''

    # Get capacities
    # cap_csp = get_cap(gdxin, 'cap_csp', col_names=['i', 'v', 'rs', 'MW'],
    #                   return_cols=['i', 'v', 'rs'])
    cap_thermal = get_cap(gdxin, 'cap_thermal')

    # Aggregate CSP capacity up to the BA level
    # cap_csp = spatial_agg(cap_csp, r_rs, 'rs', 'r', 'MW')

    # Drop all capacity that is less than 5 MW
    df = pd.concat([cap_thermal], sort=False).reset_index(drop=True)
    cap_dropped = df[df['MW'] < min_plant_size].reset_index(drop=True)
    cap_dropped = cap_dropped.groupby('i').sum()
    print1('capacity dropped from Osprey:\n{}'.format(str(cap_dropped)))
    df = df[df['MW'] > min_plant_size].reset_index(drop=True)

    return df


# Gets an average for all columns in data_cols weighted by the weighter_col
def weighted_average(df, data_cols, weighter_col, groupby_cols, new_col,
                     old_col):

    df_avg = df.copy()
    for data_col in data_cols:
        df_avg[data_col] = df_avg[data_col] * df_avg[weighter_col]
    df_avg = df_avg.groupby(by=groupby_cols, as_index=False).mean()
    for data_col in data_cols:
        df_avg[data_col] = df_avg[data_col] / df_avg[weighter_col]
    df_avg.drop(weighter_col, 1, inplace=True)
    if new_col and old_col:
        df_avg.rename(columns={old_col: new_col}, inplace=True)
    return df_avg


# Pivots from long to wide format
def get_as_hourly(df, ind, cols, vals, load, d_hr):

    # Index manipulations before pivot
    if ind == 'index':
        df['index'] = 0
    elif ind == 'd_hr':
        df['d_hr'] = df['d'] + '_' + df['hr']

    # Pivot dataframe
    df = df.pivot(index=ind, columns=cols, values=vals)

    # Index manipulations after pivot
    if ind == 'index':
        df = pd.DataFrame(columns=df.columns,
                          data=np.tile(df.values, (len(load), len(df))))
    elif ind == 'd_hr':
        df = pd.merge(left=d_hr[['d_hr']],
                      right=df, on='d_hr', how='left').fillna(0)
        df.drop('d_hr', 1, inplace=True)

    # Make sure all regions are present if columns are regions
    if cols == 'r':
        for col in load.columns:
            if col not in df.columns:
                df[col] = 0
        df = df[load.columns.tolist()]

    return df


# Sums transmission flows across many paths
def sum_flows(flows, paths):
    try:
        df = flows[paths].sum(axis=1)
    except:
        used_paths = []
        for p in paths:
            if p in flows.columns:
                used_paths.append(p)
        df = flows[used_paths].sum(axis=1)

    return df


# Expands the columns of a dataframe to have a finer resolution (e.g. from
#   load by region to source load by transmission path)
def expand_df(df, expand, old_col, new_col, drop_cols):

    df = df.T
    cols = [old_col] + df.columns.tolist()
    df.reset_index(inplace=True)
    df.columns = cols
    df = pd.merge(left=expand, right=df, on=old_col, how='left')
    df.drop(drop_cols, 1, inplace=True)
    df.set_index(new_col, inplace=True)
    df = df.T

    return df


# Determines the ratio of curtailment that could be used to charge storage
def storage_curt_recovery(e, eff, ts_length, poss_batt_changes, hdtmap,
                          marg_curt_h):

    # Initialize the state-of-charge to be 0 in all hours
    batt_e_level = np.zeros([ts_length, len(poss_batt_changes.columns)])
    # Allow for charging during the first hour, adjusting for losses. NOTE:
    #   we are assuming storage starts the time-series with 0 state-of-charge
    batt_e_level[0, :] = np.maximum(poss_batt_changes.values[0, :] * eff, 0)
    # Account for any curtailment recovery that happens in this first hour
    curt_recovered = np.zeros([ts_length, len(poss_batt_changes.columns)])
    curt_recovered[0, :] = np.maximum(poss_batt_changes.values[0, :] * eff, 0)
    for n in range(1, ts_length):
        # Change the state-of-charge from the previous hour, either increasing
        # it for recovery of curtailment (and accounting for losses) or
        # decreasing it to serve load
        batt_e_level[n, :] = batt_e_level[n-1, :] \
                             + np.where(poss_batt_changes.values[n, :] > 0,
                                        poss_batt_changes.values[n, :] * eff,
                                        poss_batt_changes.values[n, :])
        # Constrain the state-of-charge to be between 0 and marg_stor_MWh
        batt_e_level[n, :] = np.clip(batt_e_level[n, :], a_min=0, a_max=e)
        # Determine the amount of otherwise-curtailed energy that was
        #   recovered during this hour, accounting for losses
        curt_recovered[n, :] = \
            np.maximum(0, (batt_e_level[n, :] - batt_e_level[n-1, :]) / eff)
    # Group recovered curtailment by timeslice
    curt_recovered_h = pd.DataFrame(columns=poss_batt_changes.columns,
                                    data=curt_recovered)
    curt_recovered_h = pd.concat([hdtmap[['h']], curt_recovered_h],
                                 sort=False, axis=1)
    curt_recovered_h = curt_recovered_h.groupby('h').sum()
    # Get the total amount of recovered curtailment
    curt_recovered = curt_recovered_h.sum()
    # Determine the fraction of recovered energy that was recovered during
    #   each timeslice
    curt_recovered_h_frac = pd.DataFrame(
        columns=poss_batt_changes.columns,
        data=np.divide(curt_recovered_h.values,
                       curt_recovered.values,
                       out=np.zeros_like(curt_recovered_h),
                       where=curt_recovered != 0))
    # Distribute the leftover "unrecovered" energy across all timeslices
    #   according to the amount recovered in each timeslice.
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


# Gets the remaining cycles per day available to existing storage
def get_remaining_cycles_per_day(stor_level,
                                 marg_curt_exist_stor_recovery_ratio,
                                 resource_device_utility,
                                 d_hr, cap_stor, daily_cycle_limit):

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
    df.drop('device', 1, inplace=True)
    df.set_index('resource_device', inplace=True)
    df = df.T
    columns = marg_curt_exist_stor_recovery_ratio.columns.to_list()
    unused = [x for x in columns if x not in df.columns]
    for col in unused:
        df[col] = 0
    df = df[columns]

    return df


def adjust_flex_load(load_profiles, flex_load, flex_load_opt, dt8760):

    for r in load_profiles.columns:

        load_profiles_temp = load_profiles[[r]].reset_index()
        load_profiles_temp = pd.concat([dt8760[['h']],
                                        load_profiles_temp], axis=1)
        flex_load_temp = flex_load[flex_load['r'] == r].reset_index(drop=True)
        flex_load_opt_temp = flex_load_opt[
            flex_load_opt['r'] == r].reset_index(drop=True)
        h3_load = load_profiles_temp[
            load_profiles_temp['h'] == 'h3'].reset_index(drop=True)
        temp = h3_load[['index', r]].sort_values(
            r, ascending=False).reset_index(drop=True)
        h17 = temp.loc[0:39, 'index']
        load_profiles_temp.loc[h17, 'h'] = 'h17'
        load_profiles_temp = pd.merge(left=load_profiles_temp,
                                      right=flex_load_temp[['h', 'exog']],
                                      on='h', how='left').fillna(0)
        load_profiles_temp = pd.merge(left=load_profiles_temp,
                                      right=flex_load_opt_temp[['h', 'opt']],
                                      on='h', how='left').fillna(0)
        load_profiles[r] += load_profiles_temp['opt'] \
            - load_profiles_temp['exog']

    return load_profiles


# Delete extraneous csv files
def delete_csvs(args):
    files = ['cap_max_model', 'dropped_load', 'flows', 'gen', 'net_load_day',
             'net_load_osprey', 'prices', 'storage_in', 'storage_level']
    file_names = [f + '_' + args['tag'] + '.csv' for f in files]
    
    user, runname = args['scenario'].split('_')[0], args['scenario'].split('_')[0] + '_' +  args['scenario'].split('_')[1]
    for f in file_names:
        if os.path.isfile(os.path.join(args['reeds_path'],'reeds_server','users_output',user, runname,'runs',args['scenario'],'augur_data', f)):
            os.remove(os.path.join(args['reeds_path'],'reeds_server','users_output',user, runname, 'runs',args['scenario'], 'augur_data', f))
    os.remove(os.path.join(args['reeds_path'],'reeds_server','users_output',user, runname,'runs',args['scenario'], 'augur_data',
                           'osprey_outputs_{}.gdx'.format(args['tag'])))


def print1(txt, outlined=False):
    if platform.system() != 'Linux':
        if outlined:
            print('\n##############################')
            print(txt)
            print('##############################\n')
        else:
            print(txt)
