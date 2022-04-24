#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 12:54:25 2020
@author: ngates
"""

import pandas as pd
import numpy as np
import os
import networkx as nx
import itertools

#%%
def compute_region_flows(flows, osprey_inputs, args):
    
    # Get transmission capacity
    transCapacity = osprey_inputs['cap_trans'].copy()
    
    # Get uncapped flows for D_Condor
    flows_uncapped = pd.merge(left=transCapacity, right=flows, on=['r','rr'])
    flows_uncapped = flows[(flows_uncapped['MW']-abs(flows_uncapped['Val']))>0.01].reset_index(drop=True)
    
    # Create a path column for directional connections between r and rr
    transCapacity['path'] = transCapacity.r + '_' + transCapacity.rr
    # Get a mapper for source region, destination region, and path
    path_mapper = transCapacity[['r','rr','path']].copy()
    transCapacity['index'] = 0
    # Pivot transmission capacity to wide format
    transCapacity = transCapacity.pivot(index='index', columns='path', values='MW')
    transCapacity = pd.DataFrame(columns=transCapacity.columns, data=np.tile(transCapacity.values, (args['osprey_ts_length'],1)))
    
    # Get transmission loss rates in wide format
    tranLoss = osprey_inputs['tranloss'].copy()
    tranLoss['path'] = tranLoss.r + '_' + tranLoss.rr
    tranLoss['index'] = 0
    tranLoss = tranLoss.pivot(index='index', columns='path', values='loss_factor')
    tranLoss = pd.DataFrame(columns=tranLoss.columns, data=np.tile(tranLoss.values, (args['osprey_ts_length'],1)))
    
    # Get transmission flows in wide format
    flows['path'] = flows['r'] + '_' + flows['rr'] #add path column
    flows['index_hr'] = (flows.d.str[1:].astype(int) - 1)*24 + flows.hr.str[2:].astype(int) - 1
    flows = flows.pivot(index='index_hr', columns='path', values='Val')
    # Reindex to include unused paths
    flows = flows.reindex(index=np.arange(args['osprey_ts_length']), columns=transCapacity.columns).fillna(0)
    
    # Apply transmission losses only to imports
    imports = pd.DataFrame(columns=flows.columns, data=flows.values * (1 - tranLoss.values))
    
    # Get exports by region
    imports = imports.transpose().reset_index()
    imports = pd.merge(left=path_mapper[['rr','path']], right=imports, on='path')
    imports = imports.groupby('rr').sum().transpose()
    # Get imports by region
    exports = flows.copy().transpose().reset_index()
    exports = pd.merge(left=path_mapper[['r','path']], right=exports, on='path')
    exports = exports.groupby('r').sum().transpose()
    
    # Get the net transmission flows
    region_flows = pd.DataFrame(columns=imports.columns, data=imports.values - exports.values)
    
    # Get the remaining transmission capacity for each path
    trancap_remain = pd.DataFrame(columns=flows.columns, data=transCapacity.values - flows.values)
    # To account for any rounding issues, force the transcap_remaining values to be positive
    trancap_remain = pd.DataFrame(columns=flows.columns, data=np.clip(trancap_remain.values, a_max=None, a_min=0))
    
    if os.name!="posix":
        print('determining transmission-connected regions...')

    # Lists and counts
    bas = pd.unique(osprey_inputs['routes'][['r','rr']].values.ravel('K')).tolist()
    n_bas = len(bas)
    index_hr_map = pd.read_csv(os.path.join('A_Inputs','inputs','variability','index_hr_map.csv'))
    hour_day_map = index_hr_map[['idx_hr', 'd']].drop_duplicates()
    index_hrs = list(hour_day_map['idx_hr'].drop_duplicates())
    n_hours = args['osprey_ts_length']
    
    # Each region-hour gets a unique index (rh_idx). We can't just use the pXX values, because then the networkx package would connect regions across time. 
    rh_idx_map = pd.DataFrame(itertools.product(bas, index_hrs), columns=['r', 'idx_hr'])
    rh_idx_map['rh_idx'] = rh_idx_map.merge( rh_idx_map.drop_duplicates(['r','idx_hr']).reset_index(), on=['r','idx_hr'] )['index']
    #rh_idx_map['rh_idx'] = n_hours*(rh_idx_map['r'].str[1:].astype(int) - 1) +  rh_idx_map['idx_hr']
    rh_idx_map['rr'] = rh_idx_map['r'].copy() # Just copy these for use in merging below

    # Merge the unique rh_idx onto both the source and destination
    flows_uncapped = flows_uncapped.merge(index_hr_map, on=['d', 'hr'], how='left')
    flows_uncapped = flows_uncapped.merge(rh_idx_map[['r', 'idx_hr', 'rh_idx']], on=['r', 'idx_hr'], how='left')
    flows_uncapped = flows_uncapped.rename(columns={'rh_idx':'rh_source_idx'})
    flows_uncapped = flows_uncapped.merge(rh_idx_map[['rr', 'idx_hr', 'rh_idx']], on=['rr', 'idx_hr'], how='left')
    flows_uncapped = flows_uncapped.rename(columns={'rh_idx':'rh_dest_idx'})

    # Find all transmission-connected regions
    flows_uncapped['pairs'] = tuple(zip(list(flows_uncapped['rh_source_idx']), list(flows_uncapped['rh_dest_idx'])))
    graph = nx.from_edgelist(list(flows_uncapped['pairs']))
    connected = list(nx.connected_components(graph))

    # Reformatting the transmission-connected regions for later use
    trans_region_map_subset = np.empty([n_hours*n_bas, 2]) # "subset" because it only includes regions that have connections. 
    counter = 0
    for trans_region in range(len(connected)):
        region_conns = list(connected[trans_region])
        n_conns = len(region_conns)
        trans_region_map_subset[counter:counter+n_conns,0] = region_conns
        trans_region_map_subset[counter:counter+n_conns,1] = trans_region
        counter = counter + n_conns
    trans_region_map_subset = trans_region_map_subset[:counter,:] # It isn't full if BAs didn't have uncapped transmission available to anywhere
        
    trans_region_map_subset_df = pd.DataFrame()
    trans_region_map_subset_df['rh_idx'] = trans_region_map_subset[:,0]
    trans_region_map_subset_df['trans_region'] = trans_region_map_subset[:,1]
    trans_region_map_subset_df = trans_region_map_subset_df.merge(rh_idx_map[['rh_idx', 'r', 'idx_hr']], on='rh_idx', how='left')

    trans_region_map_df = pd.DataFrame(itertools.product(bas, index_hrs), columns=['r', 'idx_hr'])
    trans_region_map_df = trans_region_map_df.merge(trans_region_map_subset_df[['r', 'idx_hr', 'trans_region']], on=['r', 'idx_hr'], how='left')
    trans_region_map_df['trans_region_unique'] = np.arange(trans_region_map_df['trans_region'].max(), trans_region_map_df['trans_region'].max()+len(trans_region_map_df))
    trans_region_map_df['trans_region'] = np.where(trans_region_map_df['trans_region'].isnull(), trans_region_map_df['trans_region_unique'], trans_region_map_df['trans_region'])
    trans_region_map_df = trans_region_map_df.drop(columns=['trans_region_unique'])
    
    tran_results = {'flows': flows,
                    'region_flows': region_flows,
                    'tranloss': tranLoss,
                    'trancap_remain': trancap_remain,
                    'tran_region_map': trans_region_map_df,
                    'tranpath_map': path_mapper}
    
    return tran_results
#%%
def process_osprey_results(args, osprey_inputs):
    

    if os.name!="posix":
        print('reading in osprey results...')
    charging = pd.read_csv(os.path.join(args['data_dir'],'storage_in_{}.csv'.format(args['tag'])))
    prices = pd.read_csv(os.path.join(args['data_dir'], 'prices_{}.csv'.format(args['tag'])))
    state_of_charge = pd.read_csv(os.path.join(args['data_dir'], 'storage_level_{}.csv'.format(args['tag'])))
    gen = pd.read_csv(os.path.join(args['data_dir'],'gen_{}.csv'.format(args['tag'])))
    flows = pd.read_csv(os.path.join(args['data_dir'],'flows_{}.csv'.format(args['tag'])))
    
    if os.name!="posix":
        print('processing generation results...')
    gen.i = gen.i.str.lower() # Standardize generator names
    gen['idx_hr'] = (gen.d.str[1:].astype(int) - 1)*24 + \
                     gen.hr.str[2:].astype(int) - 1
    gen['generator'] = gen['i'] + gen['v'] + gen['r']
    gen_names = gen[['i','v','r','generator']].drop_duplicates()
    gen = gen.pivot(index='idx_hr', columns='generator', values='Val').fillna(0)
    
    if os.name!="posix":
        print('processing transmission results...')
    tran_results = compute_region_flows(flows, osprey_inputs, args)
    
    osprey_results = {'charging':charging,
                      'gen':gen,
                      'gen_names':gen_names,
                      'prices':prices,
                      'state_of_charge':state_of_charge
                      }
    
    osprey_results = {**osprey_results, **tran_results}
    
    return osprey_results