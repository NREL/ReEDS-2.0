#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 16:31:43 2020

This file computes the curtailment of existing resources based on the results
from Osprey. Net load profiles are adjusted by transmission flows and storage
operation in Osprey. Generation in Osprey is adjusted for minimum generation
levels such that generators that are generating very low are forced to come
up to their mingen level. Net load is subtracted from the adjusted generation,
and any negative values are interpreted as curtailment. Adjusted load profiles
are sent to C2_marginal_curtailment.

@author: ngates
"""

import numpy as np
import os
import pandas as pd

from ReEDS_Augur.utility.functions import filter_data_year, \
    adjust_tz
from ReEDS_Augur.utility.generatordata import GEN_DATA
from ReEDS_Augur.utility.hourlyprofiles import HOURLY_PROFILES, OSPREY_RESULTS
from ReEDS_Augur.utility.inputs import INPUTS
from ReEDS_Augur.utility.switchsettings import SwitchSettings


def existing_curtailment():

    #%% Bypass this calculation if not running Augur
    if not int(SwitchSettings.switches['gsw_augurcurtailment']):
        curt_results = {
            'curt': pd.DataFrame(),
            'curt_h': pd.DataFrame(),
            'curt_load_adj': pd.DataFrame(),
            'curt_mingen': pd.DataFrame(),
        }
        curt_reeds = {
            'curt_old': pd.DataFrame(columns=['r','h','t','value']),
            'curt_mingen': pd.DataFrame(columns=['r','h','t','value']),
            'storage_in_min': pd.DataFrame(columns=['r','h','t','value']),
            'storage_starting_soc' : pd.DataFrame(columns=['i','v','r','h','t','Val']),
        }
        return curt_results, curt_reeds

    #%% Load the inputs
    decimals = SwitchSettings.switches['decimals']
    year = int(SwitchSettings.next_year)  # Year must be an integer, not a string
    marginal_curtailment_step = SwitchSettings.switches['curt_mingen_step_size']
    techs = INPUTS['i_subsets'].get_data()
    rfeas = INPUTS['rfeas'].get_data()['r']
    ts_length = SwitchSettings.switches['osprey_ts_length']
    converter_efficiency_vsc = INPUTS['converter_efficiency_vsc'].get_data().loc[0,'value']

    # Import vre generation
    vre_gen = HOURLY_PROFILES['vre_gen_r'].profiles.copy()
    vre_gen = filter_data_year(profile=vre_gen, data_years=SwitchSettings.osprey_years)

    # Get generation (raw osprey output)
    gen, gen_names = OSPREY_RESULTS['gen'].get_data()
    # Filter for generators with and without storage
    gen_names_no_stor = gen_names[~gen_names['i'].isin(
        techs['storage'])].reset_index(drop=True)
    gen_names_dr = gen_names[gen_names['i'].isin(
        techs['dr1'] + techs['dr2'])].reset_index(drop=True)
    gen_names_no_stor_dr = gen_names[
        (~gen_names['i'].isin(techs['storage']))
        & (~gen_names['i'].isin(techs['dr1']))
        & (~gen_names['i'].isin(techs['dr2']))
        ].reset_index(drop=True)

    # Get generation from dr
    dr_out = gen[gen_names_dr['generator']]
    # Aggregate storage generation by region
    dr_out = dr_out.T.reset_index()
    dr_out = pd.merge(left=gen_names_dr[['r', 'generator']],
                      right=dr_out,
                      on='generator').drop('generator', axis=1)
    dr_out = dr_out.groupby('r').sum().T
    dr_out = dr_out.reindex(
        index=np.arange(SwitchSettings.switches['osprey_ts_length']),
        columns=rfeas).fillna(0)

    # Remove storage from gen dataframe
    gen = gen[gen_names_no_stor_dr['generator']]

    # Create a capacity dataframe in wide format
    cap = gen_names_no_stor_dr.merge(GEN_DATA['max_cap'], on = ['i', 'v', 'r'],
                                     how = 'left')
    cap_save = cap.copy()
    cap['index'] = 0
    # Remove canadian imports -- this will be replaced by generation because
    #   we are treating canadian imports as a must-run tech in these
    #   calculations.
    cap = cap[~cap['i'].isin(techs['canada'])].reset_index(drop=True)
    cap = cap.pivot(index='index', columns='generator', values='MW')
    cap = pd.DataFrame(columns = cap.columns,
                       data = np.tile(cap.values, (ts_length, 1)))
    # Replace the capacity values for canadian imports with their gen values
    gen_can = gen[gen_names[gen_names['i'].isin(techs['canada'])]['generator']]
    cap = pd.concat([gen_can, cap], sort=False, axis=1)
    # Reorder the columns to match the gen dataframe
    cap = cap[gen.columns]

    #%% Compute mingen

    # Create a mingen_frac dataframe in wide fromat
    min_gen = GEN_DATA['mingen'].copy()
    # Take a mingen average for now
    # There are hydro duplicates. Removing these now by taking an average.
    #   NOTE we are assuming mingen levels do not vary by season, but it
    #   would be simple to add this capability.
    min_gen = min_gen.groupby(['i','v','r'], as_index = False).mean()
    mingen_frac = min_gen.merge(cap_save, on = ['i','v','r'])
    mingen_frac['mingen'] /= mingen_frac['MW']
    mingen_frac.drop('MW', axis = 1, inplace = True)
    mingen_frac['mingen'] = mingen_frac['mingen'].round(decimals)
    # Setting default mingen levels for can-imports and Hydro
    mingen_frac.loc[mingen_frac['i'].isin(techs['canada']), 'mingen'] = 1
    mingen_frac.loc[mingen_frac['i'].isin(techs['hydro']),
                    'mingen'] = SwitchSettings.switches['curt_hydro_mingen']
    mingen_frac['index'] = 0
    mingen_frac = mingen_frac.pivot(index='index', columns='generator',
                                    values='mingen')
    mingen_frac = pd.DataFrame(columns=mingen_frac.columns,
                        data=np.tile(mingen_frac.values, (ts_length, 1)))
    # Reorder columns to match the gen dataframe
    mingen_frac = mingen_frac[gen.columns]

    # Conditions for setting mingen levels
    large_cap = cap.values >= SwitchSettings.switches[
                                                    'curt_max_generator_size']
    low_gen = gen.values < SwitchSettings.switches['curt_max_generator_size']
    large_cap_low_gen = large_cap & low_gen

    # Create a mingen_level dataframe in wide format using the conditions
    #   above. For generators with capacity greater than the max size, the
    #   mingen level is the mingen fraction multiplied by the generation in
    #   each hour. For reasonably sized generators, the mingen level is the
    #   mingen fraction multiplied by the capacity.
    mingen_level = pd.DataFrame(
        columns=mingen_frac.columns,
        data=np.where(large_cap,
                      mingen_frac.values * gen.values,
                      mingen_frac.values * cap.values))
    # When generators larger that the max generator size are generating below
    #   the max generator size, we instead use the mingen fraction multiplied
    #   by the max generator size. This is supposed to simulate the idea that
    #   the large generator is actually several smaller generators, but in
    #   this case all but 1 of the several smaller generators are off.
    mingen_level = pd.DataFrame(
        columns=mingen_level.columns,
        data=np.where(large_cap_low_gen,
                      mingen_frac.values * SwitchSettings.switches[
                                                  'curt_max_generator_size'],
                      mingen_level.values))

    # Create a headroom dataframe in wide format
    headroom = gen - mingen_level
    # Clip headroom values that are less than 0
    headroom[headroom < 0] = 0

    # Identify instances when generators are on but operating below their
    #   mingen level.
    mingen_adj = (0 < gen.values) & (gen.values < mingen_level.values)

    # Create a dataframe that has the mingen-adjusted generation levels
    gen_adj = pd.DataFrame(columns=gen.columns,
                           data=np.where(mingen_adj, mingen_level.values,
                                         gen.values))
    # Aggregate mingen-adjusted generation up to the BA level
    gen_adj_r = gen_adj.T.reset_index()
    gen_adj_r = pd.merge(left=gen_names_no_stor_dr[['r', 'generator']],
                         right=gen_adj_r,
                         on='generator').drop('generator', 1)
    gen_adj_r = gen_adj_r.groupby('r').sum().T
    gen_adj_r = gen_adj_r.reindex(index = np.arange(ts_length),
                                  columns = vre_gen.columns).fillna(0)

    # Aggregate headroom up to the BA level
    headroom_r = headroom.T.reset_index()
    headroom_r = pd.merge(left=gen_names[['r', 'generator']],
                          right=headroom_r,
                          on='generator').drop('generator', 1)
    headroom_r = headroom_r.groupby('r').sum().T
    headroom_r = headroom_r.reindex(index=np.arange(ts_length),
                                    columns=vre_gen.columns).fillna(0)

    #%% Compute curtailment

    # Get net regional transmission flows
    region_flows = OSPREY_RESULTS['region_flows'].get_data().reindex(rfeas, axis=1).fillna(0)
    
    # Get Osprey hydrogen production demand
    produce = OSPREY_RESULTS['produce'].get_data()

    # Compute storage_charge
    storage_dispatch = OSPREY_RESULTS['storage_dispatch_r'].get_data()

    # Get DR load increase and convert to wide format
    dr_in = OSPREY_RESULTS['dr_inc'].get_data()

    # Compute dr_charge
    if dr_in.empty:
        dr_charge = - dr_out
    else:
        dr_charge = dr_in - dr_out

    # Get net VSC AC/DC conversion
    conversion = INPUTS['osprey_conversion'].get_data(str(SwitchSettings.prev_year))
    if not len(conversion):
        conversion = 0
    else:
        conversion = (
            conversion
            .assign(Val=(
                conversion.Val * conversion.intype.map({
                    ## AC->VSC is a power sink; AC use is scaled up by 1/eff
                    'AC': -1 / converter_efficiency_vsc,
                    ## VSC->AC is a power source; AC production is scaled down by eff
                    'VSC': converter_efficiency_vsc})))
            .drop(['intype','outtype'], axis=1)
            ## Get the complete hourly index
            .assign(index_hr=((conversion.d.str[1:].astype(int) - 1) * 24
                              + conversion.hr.str[2:].astype(int) - 1))
            ## Add duplicates to get net conversion (since it's not a MIP there
            ## can be AC->VSC and VSC->AC conversion in the same (region,hour))
            .groupby(['index_hr','r']).Val.sum()
            .unstack('r')
            .reindex(index=np.arange(SwitchSettings.switches['osprey_ts_length']),
                     columns=region_flows.columns)
            .fillna(0)
        )

    # Adjust net_load_day by transmission and storage
    net_load_adj = (
        HOURLY_PROFILES['net_load_osprey'].profiles
        - region_flows
        - storage_dispatch
        + produce
        + dr_charge
        - conversion
    )

    # Compute curtailment: adjusted generation minus adjusted net load
    curt_adj = gen_adj_r - net_load_adj
    # Clip small numbers to 0
    curt_adj[curt_adj.abs() < SwitchSettings.switches['min_val']] = 0  
    # Curtailment cannot be greater than vre_gen
    curt_exceeds_gen = curt_adj.values > vre_gen.values
    curt_adj = pd.DataFrame(columns=curt_adj.columns,
                            data=np.where(curt_exceeds_gen, vre_gen.values,
                                          curt_adj.values))
    # Curtailment cannot be negative (which it will be if there's dropped load)
    curt_adj[curt_adj < 0] = 0

    # Allow head room to ramp down to mingen levels
    curt = curt_adj - headroom_r
    # Negative values mean excess head_room that could be stored or
    #   transmitted to another BA. Assuming transmission and storage cannot
    #   act to alleviate mingen, the excess head_room is lost.
    curt[curt < 0] = 0
    curt = curt.fillna(0)
    # Cannot be greater than vre_gen
    idx = curt > vre_gen
    curt[idx] = vre_gen[idx]
    # Cannot be negative (redundant)
    idx = curt < 0
    curt[idx] = 0

    #%% Write cutailment for plots if necessary
    if SwitchSettings.switches['plots']:
        curt.to_hdf(
            os.path.join(
                'ReEDS_Augur','augur_data',
                'curt_C1_{}.h5'.format(SwitchSettings.prev_year)),
            key='data', complevel=4)

    #%% Process outputs for ReEDS
    # Convert curtailment from ET to local time
    curt_ET = curt.reset_index(drop=True)
    curt_ET.index.name = 'idx_hr'
    curt_tz = adjust_tz(curt_ET, option = 'ET_to_local')

    # Aggregate curtailment by timeslice
    dt_szn_h = INPUTS['h_dt_szn'].get_data()
    dt_szn_h_single = dt_szn_h[
        dt_szn_h.year.isin(SwitchSettings.switches['osprey_years'])
    ].reset_index(drop=True)

    curt_tz_agg = pd.merge(
        curt_tz.reset_index(), dt_szn_h_single.reset_index(), 
        left_index=True, right_index=True)
    curt_tz_agg = curt_tz_agg.drop(
            columns=['index', 'hour', 'year', 'season']).groupby('h').sum()
    curt_tz_agg = curt_tz_agg.reindex(index=['h'+str(i+1) for i in range(16)],
                                      columns=rfeas)
    # In the future, compute this accurately using the max 40 hours by BA

    # Convert to MWh and format for ReEDS
    # Since curt_tz_agg is summed above, sum hours over all Osprey years
    hours = INPUTS['hours'].get_data()
    hours.hours *= SwitchSettings.switches['osprey_num_years']
    if 'h18' not in hours['h'].tolist():
        hours.loc[hours['h']=='h3','hours'] += hours.loc[
            hours['h']=='h17', 'hours'].values[0]
        hours = hours[hours['h'] != 'h17'].reset_index(drop=True)
    curt_h = curt_tz_agg.reset_index()
    curt_h = curt_h.melt(id_vars='h').rename(columns={'variable': 'r'})
    curt_h['t'] = year
    curt_h = curt_h[['r', 'h', 't', 'value']]
    curt_h = curt_h.merge(hours, on='h', how='left')
    curt_h.value /= curt_h.hours  # Convert from MWh to MW
    curt_h = curt_h.drop(columns='hours')
    # Make sure there are no infeasibilities in ReEDS by capping curtailment
    #   at the max timeslice CF in ReEDS
    
    cap_vre = GEN_DATA['max_cap'].copy()
    techs = INPUTS['i_subsets'].get_data()
    cap_vre = cap_vre[cap_vre['i'].isin(techs['vre'])]
    m_cf = INPUTS['m_cf'].get_data()
    max_cf = cap_vre.merge(m_cf, on = ['i', 'v', 'r'], how = 'left')
    max_cf['MW'] *= max_cf['CF']
    max_cf.drop('CF', axis = 1, inplace = True)
    max_cf = max_cf.groupby(['r', 'h'], as_index = False).sum()
    curt_h = curt_h.merge(max_cf, on=['r', 'h'], how='left').fillna(0)
    curt_h.loc[curt_h['value'] > curt_h['MW'], 'value'] = \
        curt_h.loc[curt_h['value'] > curt_h['MW'], 'MW']
    # Organize columns for ReEDS
    curt_h = curt_h[['r', 'h', 't', 'value']]
    # Remove small numbers and round results
    curt_h.loc[curt_h['value'] < SwitchSettings.switches['min_val'],
                                                           'value'] = 0
    curt_h['value'] = curt_h['value'].round(SwitchSettings.switches['decimals'])

    # Compute net_load_adj_mingen, which adjusts the load accurately for
    #   mingen changes
    net_load_adj_mingen = net_load_adj - curt
    idx = curt > 0
    net_load_adj_mingen[idx] = -curt[idx]
    net_load_adj_mingen[abs(net_load_adj_mingen.values) < 
                        SwitchSettings.switches['min_val']] = 0
    # Convert curtailment adjusted load from ET to local time
    curt_load_adj = net_load_adj_mingen.copy()
    curt_load_adj.index = range(len(curt_load_adj))

    # Recompute curtailment with a baseload power adjustment
    step = marginal_curtailment_step
    curt_mingen_step = curt - step
    curt_mingen_step[curt_mingen_step < 0] = 0
    curt_mingen_step = (curt - curt_mingen_step) / step
    curt_mingen_step = curt_mingen_step.reset_index(drop=True)
    curt_mingen_step.index.name = 'idx_hr'

    # Convert curt_mingen_step from ET to local time
    curt_mingen_step_tz = adjust_tz(curt_mingen_step,
                                    option = 'ET_to_local')

    # Aggregate to time slices and format for ReEDS
    curt_mingen = curt_mingen_step_tz.copy()
    curt_mingen = pd.concat([dt_szn_h_single[['h']], curt_mingen],
                            sort=False, axis=1)
    curt_mingen = curt_mingen.groupby('h').mean().reset_index().melt(
            id_vars='h').rename(columns={'variable': 'r'})
    curt_mingen['t'] = year
    curt_mingen = curt_mingen[['r', 'h', 't', 'value']]
    # Remove small numbers and round results
    curt_mingen.loc[curt_mingen['value'] < 
                    SwitchSettings.switches['min_val'], 'value'] = 0
    curt_mingen['value'] = curt_mingen['value'].round(decimals)

    # Prepare storage_in_min for ReEDS - adjusting to local time
    storage_in = storage_dispatch[storage_dispatch < 0].fillna(0)
    storage_in *= -1
    storage_in_min = adjust_tz(storage_in, option = 'ET_to_local')
    # Summing over timeslice for ReEDS
    storage_in_min = pd.concat([dt_szn_h_single[['h']], storage_in_min],
                               sort=False, axis=1)
    storage_in_min = storage_in_min.groupby('h').sum().reset_index().melt(
            id_vars='h').rename(columns={'variable': 'r'})
    # Convert from MWh to MW
    storage_in_min = storage_in_min.merge(hours, on='h', how='left')
    storage_in_min['value'] /= storage_in_min['hours']
    # Make sure we don't charge more than is available in ReEDS
    
    cap_stor_r = GEN_DATA['max_cap'].copy()
    cap_stor_r = cap_stor_r[cap_stor_r['i'].isin(techs['storage_standalone'])]
    cap_stor_r = cap_stor_r.groupby('r', as_index = False).sum()
    storage_in_min = storage_in_min.merge(cap_stor_r, on='r',
                                          how='left').fillna(0)
    idx = storage_in_min['value'] > storage_in_min['MW']
    storage_in_min.loc[idx, 'value'] = storage_in_min.loc[idx, 'MW']
    storage_in_min['t'] = year
    storage_in_min = storage_in_min[['r', 'h', 't', 'value']]
    # Remove small numbers and round results
    storage_in_min.loc[storage_in_min['value'] < SwitchSettings.switches['min_val'], 'value'] = 0
    storage_in_min['value'] = storage_in_min['value'].round(SwitchSettings.switches['decimals'])


    # Compute starting state of charge 
    storage_soc = INPUTS['osprey_SOC'].get_data(SwitchSettings.prev_year)
    storage_soc['hour'] = ((storage_soc.d.str[1:].astype(int)-1)*24
                              + storage_soc.hr.str[2:].astype(int)-1)
    if len(storage_soc):
        storage_starting_soc = (
            storage_soc[['i', 'v', 'r', 'hour', 'Val']]
            .merge(dt_szn_h, on=['hour'], how='left')
            [['i', 'v', 'r', 'h', 'Val']]
            .groupby(['i', 'v', 'r', 'h']).mean().reset_index()
            .assign(t=year)
            [['i', 'v', 'r', 'h', 't','Val']]
            .round(SwitchSettings.switches['decimals'])
        )
    else:
        storage_starting_soc = pd.DataFrame(columns=['i', 'v', 'r', 'h', 't','Val'])

    curt_results = {
        'curt': curt,
        'curt_h': curt_h,
        'curt_load_adj': curt_load_adj,
        'curt_mingen': curt_mingen,
    }
    curt_reeds = {
        'curt_old': curt_h,
        'curt_mingen': curt_mingen,
        'storage_in_min': storage_in_min,
        'storage_starting_soc' : storage_starting_soc,
    }

    return curt_results, curt_reeds
