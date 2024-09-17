#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 16:31:43 2020
@author: ngates
This file computes the curtailment of existing resources based on the results
from Osprey. Net load profiles are adjusted by transmission flows and storage
operation in Osprey. Generation in Osprey is adjusted for minimum generation
levels such that generators that are generating very low are forced to come
up to their mingen level. Net load is subtracted from the adjusted generation,
and any negative values are interpreted as curtailment. Adjusted load profiles
are sent to d6_marginal_curtailment.
"""

#%%
import pandas as pd
import numpy as np
import os
from utilities import tech_types

#%%

def existing_curtailment(args, curt_data, osprey_results):
#%%
    #%% Import data
    
    identifier = args['tag']
    directory = args['data_dir']
    year = int(args['next_year']) # Year must be an integer, not a string
    marginal_curtailment_step = args['curt_mingen_step_size']
    techs = tech_types(args)
    
    # Import regional transmission flows
    region_flows = osprey_results['region_flows']
    timestamp = region_flows.index
    
    # Read in rfeas
    rfeas = curt_data['rfeas'].copy()
    regions = rfeas.r.to_list()
    
    # Storage capacity by region
    cap_stor_r = curt_data['cap_storage_r'].copy()
    
    # Import vre generation
    vre_gen = curt_data['vre_gen_BA'].copy() 
    vre_gen = vre_gen[sorted(vre_gen.columns)]
    vre_gen.index = timestamp # vre_gen needs datetime index
    
    # Get generation (raw osprey output)
    gen = osprey_results['gen'].copy()
    gen = gen.reindex(range(args['osprey_ts_length']))
    gen.fillna(0, inplace=True)
    gen_names = osprey_results['gen_names'].copy()


    # Filter for with and without storage
    gen_names_stor = gen_names[gen_names['i'].isin(techs['STORAGE'])].reset_index(drop=True)
    gen_names_no_stor = gen_names[~gen_names['i'].isin(techs['STORAGE'])].reset_index(drop=True)
    # Get generation from storage
    storage_out = gen[gen_names_stor['generator']]
    # Aggregate storage generation by region
    storage_out = storage_out.transpose().reset_index()
    storage_out = pd.merge(left=gen_names_stor[['r','generator']], right=storage_out, on='generator').drop('generator', 1)
    storage_out = storage_out.groupby('r').sum().transpose()
    storage_out = storage_out.reindex(index=np.arange(args['osprey_ts_length']),columns=regions).fillna(0)
    
    # Remove storage from gen dataframe
    gen = gen[gen_names_no_stor['generator']]
    
    # Create a capacity dataframe in wide format
    cap = pd.merge(left=gen_names_no_stor, right=curt_data['cap'], on=['i','v','r'], how='left')
    cap['index'] = 0
    cap = cap.pivot(index='index', columns='generator', values='MW')
    cap = pd.DataFrame(columns=cap.columns, data=np.tile(cap.values, (args['osprey_ts_length'],1)))
#%%
    # Reorder the columns to match the gen dataframe
    cap = cap[gen.columns]
  
    if os.name!="posix":
        print('calculating mingen levels...')

    # Create a mingen_frac dataframe in wide fromat
    min_gen = curt_data['mingen'].copy()
    mingen_frac = pd.merge(left=gen_names_no_stor, right=min_gen, on=['i','r'], how='left')
    # Setting default mingen levels for c Hydro
    mingen_frac.loc[mingen_frac['i'].isin(techs['HYDRO']),'mingen'] = args['curt_hydro_mingen']
    # If there are hydro duplicates, removing these now by taking an average
    # NOTE we are assuming mingen levels do not vary by season, but tt would be 
    # simple to add this capability.
    mingen_frac = mingen_frac.groupby('generator', as_index=False).mean()
    mingen_frac['index'] = 0
    mingen_frac = mingen_frac.pivot(index='index', columns='generator', values='mingen')
    mingen_frac = pd.DataFrame(columns=mingen_frac.columns, data=np.tile(mingen_frac.values, (args['osprey_ts_length'],1)))
    # Reorder columns to match the gen dataframe
    mingen_frac = mingen_frac[gen.columns]
    
    # Conditions for setting mingen levels
    large_cap = cap.values >= args['curt_max_generator_size']
    low_gen = gen.values < args['curt_max_generator_size']
    large_cap_low_gen = large_cap & low_gen
    
    # Create a mingen_level dataframe in wide format using the conditions above
    # For generators with capacity greater than the max size, the mingen level
    # is the mingen fraction multiplied by the generation in each hour. For
    # reasonably sized generators, the mingen level is the mingen fraction
    # multiplied by the capacity
    mingen_level = pd.DataFrame(columns=mingen_frac.columns, data=np.where(large_cap, mingen_frac.values * gen.values, mingen_frac.values * cap.values))
    # When generators larger that the max generator size are generating below
    # the max generator size, we instead use the mingen fraction multiplied by
    # the max generator size. This is supposed to simulate the idea that the
    # large generator is actually several smaller generators, but in this case
    # all but 1 of the several smaller generators are off.
    mingen_level = pd.DataFrame(columns=mingen_level.columns, data=np.where(large_cap_low_gen, mingen_frac.values * args['curt_max_generator_size'], mingen_level.values))
    
    # create a headroom dataframe in wide format
    headroom = gen - mingen_level
    # Clip headroom values that are less than 0
    headroom[headroom < 0] = 0
    
    # Identify instances when generators are on but operating below their mingen level.
    mingen_adj = (0 < gen.values) & (gen.values < mingen_level.values)
    
    # Create a gen_adj dataframe that has the mingen-adjusted generation levels
    gen_adj = pd.DataFrame(columns=gen.columns, data=np.where(mingen_adj, mingen_level.values, gen.values))
    # Aggregate mingen-adjusted generation up to the BA level
    gen_adj_r = gen_adj.transpose().reset_index()
    gen_adj_r = pd.merge(left=gen_names_no_stor[['r','generator']], right=gen_adj_r, on='generator').drop('generator',1)
    gen_adj_r = gen_adj_r.groupby('r').sum().transpose()
    gen_adj_r = gen_adj_r.reindex(index=np.arange(args['osprey_ts_length']),columns=vre_gen.columns).fillna(0)
    
    # Aggregate headroom up to the BA level
    headroom_r = headroom.transpose().reset_index()
    headroom_r = pd.merge(left=gen_names[['r','generator']], right=headroom_r, on='generator').drop('generator', 1)
    headroom_r = headroom_r.groupby('r').sum().transpose()
    headroom_r = headroom_r.reindex(index=np.arange(args['osprey_ts_length']),columns=vre_gen.columns).fillna(0)
    
    if os.name!="posix":
        print('computing curtailment...')
#%%
    # Import net_load_day and convert to wide format
    # Note this has the mustrun generators' generation removed 
    net_load_day = pd.read_csv(os.path.join(
        directory, 'net_load_day_{}.csv'.format(identifier)))
    net_load_day['idx_hr'] = (net_load_day.d.str[1:].astype(int)-1)*24 + \
                              net_load_day.hr.str[2:].astype(int)-1
    net_load_day = net_load_day.pivot(index='idx_hr', columns='r', 
                                      values='Val').fillna(0)
    net_load_day.index = timestamp
    
    # Get storage charging and convert to wide format
    storage_in = osprey_results['charging'].copy()
    storage_in['index_hr'] = (storage_in.d.str[1:].astype(int) - 1)*24 + \
                              storage_in.hr.str[2:].astype(int) - 1
    storage_in = storage_in.pivot_table(index='index_hr', columns='r', 
                                        values='Val', aggfunc='sum')
    storage_in = storage_in.reindex(index=np.arange(args['osprey_ts_length']),
                                    columns=regions).fillna(0)
    storage_in.index = timestamp
    
    # Compute storage_charge
    storage_charge = storage_in - storage_out
    
    # Adjust net_load_day by transmission and storage
    net_load_adj = net_load_day - region_flows + storage_charge[net_load_day.columns]
#%%
    # Compute curtailment: adjusted generation minus adjusted net load
    curt_adj = gen_adj_r - net_load_adj # Could round these as well
    curt_adj[curt_adj.abs() < args['min_val']] = 0 # Clip small numbers to 0
    # Curtailment cannot be greater than vre_gen
    curt_exceeds_gen = curt_adj.values > vre_gen.values
    curt_adj = pd.DataFrame(columns=curt_adj.columns, data=np.where(curt_exceeds_gen, vre_gen.values, curt_adj.values))
    # Curtailment cannot be negative (which it will be if there's dropped load)
    curt_adj[curt_adj < 0] = 0
    
    # Allow head room to ramp down to mingen levels
    curt = curt_adj - headroom_r
    # Negative values mean excess head_room that could be stored or
    # transmitted to another BA. 
    curt[curt < 0] = 0
    # Assuming transmission and storage cannot act to alleviate mingen,
    # and thus that excess head_room is lost.
    curt = curt.fillna(0)
    # Cannot be greater than vre_gen
    idx = curt > vre_gen
    curt[idx] = vre_gen[idx]
    # Cannot be negative (redundant)
    idx = curt < 0
    curt[idx] = 0
    
    # Aggregate curtailment by timeslice
    dt_szn_h = pd.read_csv(os.path.join('A_Inputs','inputs','variability','h_dt_szn.csv'))
    dt_szn_h_single = dt_szn_h[dt_szn_h.year == args['year']].reset_index(drop=True)

    curt_agg = pd.merge(curt.reset_index(),
                           dt_szn_h_single.reset_index())
    curt_agg = curt_agg.drop(
            columns=['index', 'hour','year', 'season']).groupby('h').sum()
    curt_agg = curt_agg.reindex(index=['H'+str(i+1) for i in range(35)],
                                      columns=[x for x in regions if x in curt_agg.columns])
#%%  
    # Convert to MWh and format for ReEDS
    hours = curt_data['hours'].copy()
    curt_h = curt_agg.reset_index()
    curt_h = curt_h.melt(id_vars='h').rename(columns={'variable':'r'})
    curt_h['t'] = year
    curt_h = curt_h[['r','h','t','value']]
    curt_h = curt_h.merge(hours, on='h', how='left')
    curt_h.value /= curt_h.hours # Convert from MWh to Mw
    curt_h = curt_h.drop(columns='hours') 
    # Make sure there are no infeasibilities in ReEDS by capping curtailment at the max timeslice CF in ReEDS
    max_cf = curt_data['vre_max_cf'].copy()
    curt_h = pd.merge(left=curt_h, right=max_cf, on=['r','h'], how='left').fillna(0)
    curt_h.loc[curt_h['value']>curt_h['MW'],'value'] = curt_h.loc[curt_h['value']>curt_h['MW'],'MW']
    # Organize columns for ReEDS
    curt_h = curt_h[['r','h','t','value']]
    # Remove small numbers and round results
    curt_h.loc[curt_h['value']<args['min_val'],'value'] = 0
    curt_h['value'] = curt_h['value'].round(args['decimals'])
    
    # Compute net_load_adj_mingen, which adjusts the load accurately for mingen changes
    net_load_adj_mingen = net_load_adj - curt
    idx = curt > 0
    net_load_adj_mingen[idx] = -curt[idx]
    net_load_adj_mingen[abs(net_load_adj_mingen.values)<args['min_val']] = 0
    # Convert curtailment adjusted load from ET to local time
    curt_load_adj = net_load_adj_mingen.copy()
    curt_load_adj = curt_load_adj.reset_index(drop=True)
    curt_load_adj.index.name = 'idx_hr'
#%%
    # Recompute curtailment with a baseload power adjustment
    step = marginal_curtailment_step
    curt_mingen_step = curt - step
    curt_mingen_step[curt_mingen_step < 0] = 0
    curt_mingen_step = (curt - curt_mingen_step) / step
    curt_mingen_step = curt_mingen_step.reset_index(drop=True)
    curt_mingen_step.index.name = 'idx_hr'
      
    # Aggregate to time slices and format for ReEDS
    curt_mingen = curt_mingen_step.copy()
    curt_mingen = pd.concat([dt_szn_h_single[['h']],curt_mingen], sort=False, axis=1)
    curt_mingen = curt_mingen.groupby('h').mean().reset_index().melt(
            id_vars='h').rename(columns={'variable':'r'})
    curt_mingen['t'] = year
    curt_mingen = curt_mingen[['r','h','t','value']]
 #   curt_mingen = pd.concat([curt_mingen, df]).reset_index(drop=True)
    # Remove small numbers and round results
    curt_mingen.loc[curt_mingen['value']<args['min_val'],'value'] = 0
    curt_mingen['value'] = curt_mingen['value'].round(args['decimals'])
#%%   
    # Summing over timeslice for ReEDS
    storage_in_min = pd.concat([dt_szn_h_single[['h']],storage_in], sort=False, axis=1)
    storage_in_min = storage_in_min.groupby('h').sum().reset_index().melt(
            id_vars='h').rename(columns={'variable':'r'})
    # Convert from MWh to MW
    storage_in_min = pd.merge(left=storage_in_min, right=hours, on='h', how='left')
    storage_in_min['value'] /= storage_in_min['hours']
    # Make sure we don't charge more than is available in ReEDS
    storage_in_min = pd.merge(left=storage_in_min, right=cap_stor_r, on=['r','h'], how='left').fillna(0)
    storage_in_min.loc[storage_in_min['value']>storage_in_min['MW'],'value'] = storage_in_min.loc[storage_in_min['value']>storage_in_min['MW'],'MW']
    storage_in_min['t'] = year
    storage_in_min = storage_in_min[['r','h','t','value']]
    # Remove small numbers and round results
    storage_in_min.loc[storage_in_min['value']<args['min_val'],'value'] = 0
    storage_in_min['value'] = storage_in_min['value'].round(args['decimals'])
    
    outputs = {'curt': curt,
               'curt_h': curt_h,
               'curt_load_adj': curt_load_adj,
               'curt_mingen': curt_mingen}
    
    reeds_inputs = {'curt_old': curt_h,
                    'curt_mingen': curt_mingen,
                    'storage_in_min':storage_in_min}
#%%
    return outputs, reeds_inputs

#%%    