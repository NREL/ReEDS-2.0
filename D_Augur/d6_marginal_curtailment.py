# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 11:43:05 2020
@author: afrazier
"""
#%%
import pandas as pd
import numpy as np
import os
from utilities import tech_types, get_as_hourly, expand_df, storage_curt_recovery, get_remaining_cycles_per_day
#%%

def marginal_curtailment(args, marg_curt_data, osprey_results, curt_results):
#%%
    if os.name!="posix":
        print('calculating marginal curtailment...')
    
    # collect arguments
    year =         args['next_year']
    marg_stor_MW = args['marg_curt_marg_stor_mw']
    marg_vre_mw =  args['reedscc_marg_vre_mw']
    marg_trans =   args['curt_tran_step_size']
    
    # collect data from A_prep_data
    cap_stor =        marg_curt_data['cap_stor'].copy()
    cap_stor_reeds =  marg_curt_data['cap_stor_reeds'].copy()
    recf_marg =       marg_curt_data['cf_marginal'].copy()
    tranlossrates =   marg_curt_data['loss_rate'].copy()
    marg_stor_props = marg_curt_data['marg_stor'].copy()
    resources =       marg_curt_data['resources'].copy()
    
    # collect osprey_results
    flows =                   osprey_results['flows'].copy()
    tranlossrates =           osprey_results['tranloss'].copy()
    export_trans_cap_remain = osprey_results['trancap_remain'].copy()
    path_mapper =             osprey_results['tranpath_map'].copy()
    trans_regions =           osprey_results['tran_region_map'].copy()
    
    # collect curtailment results
    net_load_adj = curt_results['curt_load_adj'].reset_index(drop=True)
    
    # collecting miscellaneous
    techs = tech_types(args)
    hdtmap = pd.read_csv(os.path.join('A_Inputs','inputs','variability','h_dt_szn.csv'))
    hdtmap_single = hdtmap[hdtmap.year == 2017].reset_index(drop=True)
    d_hr = pd.read_csv(os.path.join('A_Inputs','inputs','variability','index_hr_map.csv'))
    d_hr = d_hr[['d','hr']].copy()
    d_hr['d_hr'] = d_hr['d'] + '_' + d_hr['hr']
    r_rs = marg_curt_data['r_rs'].copy()
    r_rs.set_index('rs', inplace=True)
    ts_length = len(net_load_adj)
    marg_stor_props = marg_stor_props[['i','rte','duration']].drop_duplicates()
    marg_stor_props.set_index('i', inplace=True)
    marg_stor_props['MWh'] = marg_stor_props['duration'] * marg_stor_MW
#%%
    # map all vre resources in the "i" set to the "r" set 
    i_resource_r = pd.merge(left=r_rs.reset_index(), right=resources.rename(columns={'area':'rs','tech':'i'}), on='rs', how='outer')
    i_resource_r['r'].fillna(i_resource_r['rs'], inplace=True)
    i_resource_r = i_resource_r[['i','resource','r']]
    i_resource_r['i'] = i_resource_r['i'].str.lower()
#%%
    # filter for utility-scale resources and distributed resources seperately
    util_techs = [item for sublist in [techs[x] for x in ['UPV','WIND']] for item in sublist]
    i_resource_r_utility = i_resource_r[i_resource_r['i'].str.lower().isin(util_techs)].reset_index(drop=True)
    i_resource_r_dist = i_resource_r[i_resource_r['i'].str.lower().isin(techs['DISTPV'])].reset_index(drop=True)
    
    # Map each resource in a region to each storage device in the same region
    resource_device_utility = pd.merge(left=i_resource_r_utility, right=cap_stor[['r','device']], on='r', how='right')
    resource_device_utility['resource_device'] = resource_device_utility['resource'] + '_' + resource_device_utility['device']
    
    # removing curtailment from load profile for marginal curtailment calculations
    net_load_adj_no_curt = pd.DataFrame(columns=net_load_adj.columns, data=np.clip(net_load_adj.values, a_min=0, a_max=None, out=net_load_adj.values.copy()))
    
     # =========================================================================
    # Find transmission regions that have curtailment
    # =========================================================================
    
    # Pivot the trans_region df to wide format
    trans_regions = trans_regions.pivot(index='idx_hr', columns='r', values='trans_region')
    # Find the trans_regions that have a curtailing BA inside them.
    curt_true = net_load_adj < 0
    trans_regions_with_curt = trans_regions[curt_true].fillna(0)
    # Filter out zeros, which represent no curtailment
    trans_regions_with_curt = trans_regions_with_curt.melt()
    trans_regions_with_curt = trans_regions_with_curt[trans_regions_with_curt['value']>0].reset_index(drop=True).rename(columns={'r':'curtailing BA','value':'trans_region'})
    
    # Get the list of transmission connected regions
    trans_regions_with_curt_unique = trans_regions_with_curt['trans_region'].unique()
    # Get this information in wide format to use as a conditional for adding transmission capacity to load profiles
    trans_region_curt = trans_regions.isin(trans_regions_with_curt_unique)
    
    # =========================================================================
    # Marginal transmission reducing existing curtailment
    # =========================================================================

    # expand net_load_marg to include a column for each transmission path with
    # the load of the source region for each path
    load_path_source = expand_df(net_load_adj, path_mapper[['path', 'r']],
                                 'r', 'path', ['r'])
    # Reformatting the columns to match flows
    load_path_source = load_path_source[flows.columns]
    # Only consider curtailment in source profiles
    # curt_path_source is the amount of curtailment in the source region
    # before any marginal transmission is added
    curt_path_source = pd.DataFrame(columns=load_path_source.columns,
                                    data=np.clip(load_path_source.values,
                                                 a_min=-marg_trans, a_max=0))

    # expand net_load_marg to include a column for each transmission path with
    # the load of the destination region for each path
    load_path_dest = expand_df(net_load_adj, path_mapper[['path', 'rr']],
                               'rr', 'path', ['rr'])
    # Reformatting the columns to match flows
    load_path_dest = load_path_dest[flows.columns]
    # Remove curtailment from destination profiles and adjust for transmission
    # losses
    load_path_dest = pd.DataFrame(
        columns=load_path_dest.columns,
        data=np.clip(load_path_dest.values / (1 - tranlossrates.values),
                     a_min=0, a_max=None))

    # Reduce curtailment by the effects of marginal transmission
    # curt_trans_path_source is the amount of curtailment in the source region
    # after marginal transmission has been added
    curt_trans_path_source = pd.DataFrame(
        columns=curt_path_source.columns,
        data=curt_path_source.values + np.minimum(load_path_dest.values,
                                                  marg_trans))
    curt_trans_path_source = pd.DataFrame(
        columns=curt_trans_path_source.columns,
        data=np.clip(curt_trans_path_source.values, a_min=None, a_max=0))

    # Group results by timeslice
    curt_path_source_h = pd.concat([hdtmap_single[['h']], curt_path_source],
                                   sort=False, axis=1)
    curt_path_source_h = curt_path_source_h.groupby('h').sum() * -1
    curt_trans_path_source_h = pd.concat([hdtmap_single[['h']],
                                          curt_trans_path_source],
                                         sort=False, axis=1)
    curt_trans_path_source_h = curt_trans_path_source_h.groupby('h').sum() * -1

    # curt_trans_reduced is the amount of curtailment that was reduced by
    # adding marginal transmission
    curt_trans_reduced = curt_path_source_h - curt_trans_path_source_h

    # Convert to fraction for ReEDS
    curt_tran_h = curt_trans_reduced / curt_path_source_h
    curt_tran_h.fillna(0, inplace=True)
    curt_tran_h = curt_tran_h.transpose().reset_index()
    curt_tran_h = pd.merge(left=path_mapper,
                           right=curt_tran_h.rename(columns={'index': 'path'}),
                           on='path').drop('path', 1)
    curt_tran_h = pd.melt(curt_tran_h, id_vars=['r', 'rr'], var_name='h')
    curt_tran_h['t'] = args['next_year']
    curt_tran_h = curt_tran_h[['r', 'rr', 'h', 't', 'value']]
    # curt_tran must be a fraction, so cap at 1
    curt_tran_h.loc[curt_tran_h['value'] > 1, 'value'] = 1
    # Remove small numbers and round results
    curt_tran_h.loc[curt_tran_h['value'] < args['min_val'], 'value'] = 0
    curt_tran_h['value'] = curt_tran_h['value'].round(args['decimals'])

    # Get the total load in the destination region to limit CURT_REDUCT_TRANS
    # in ReEDS. Only include hours that have curtailment in the source region,
    # otherwise sending power would not reduce curtailment
    curt_reduct_tran_max = pd.DataFrame(
        columns=load_path_dest.columns,
        data=np.where(curt_path_source.values < 0,
                      load_path_dest.values, np.nan))
    curt_reduct_tran_max = pd.concat([hdtmap_single[['h']],
                                      curt_reduct_tran_max], sort=False,
                                     axis=1)
    curt_reduct_tran_max = curt_reduct_tran_max.groupby('h').mean()
    curt_reduct_tran_max = curt_reduct_tran_max.fillna(0)
    curt_reduct_tran_max = curt_reduct_tran_max.transpose().reset_index()
    curt_reduct_tran_max = pd.merge(
        left=path_mapper,
        right=curt_reduct_tran_max.rename(columns={'index': 'path'}),
        on='path').drop('path', 1)
    curt_reduct_tran_max = pd.melt(curt_reduct_tran_max, id_vars=['r', 'rr'],
                                   var_name='h')
    curt_reduct_tran_max['t'] = args['next_year']
    curt_reduct_tran_max = curt_reduct_tran_max[['r', 'rr', 'h', 't', 'value']]
    # Remove small numbers and round results
    curt_reduct_tran_max.loc[curt_reduct_tran_max['value'] < args['min_val'],
                             'value'] = 0
    curt_reduct_tran_max['value'] = curt_reduct_tran_max['value'].round(
        args['decimals'])


    # =========================================================================
    # Adjusting marg curt profiles for existing transmission
    # =========================================================================

    # expand net_load_marg to include a column for each transmission path with
    # the load of the source region for each path
    load_path_source = expand_df(net_load_adj_no_curt, path_mapper[['path','r']], 'r', 'path', ['r'])
    # Reformatting the columns to match flows
    load_path_source = load_path_source[flows.columns]
    
    # ability to reduce imports is the minimum of the flow along a path
    # and the load in the source region.
    imports_can_reduce = pd.DataFrame(columns=flows.columns, data=np.minimum(flows.values, load_path_source.values))
    
    # expand net_load_marg to include a column for each transmission path with
    # the load of the destination region for each path
    load_path_dest = expand_df(net_load_adj_no_curt, path_mapper[['path','rr']], 'rr', 'path', ['rr'])
    # Reformatting the columns to match flows
    load_path_dest = load_path_dest[flows.columns]
    
    # Subtract the load associated with reducing imports from the load associated
    # with increasing exports before comparing remaining export capacity with the
    # load in the destination region. This avoids double-counting load in neighboring
    # regions when accounting for transmission capacity in marginal calculations.
    neighboring_load_served = imports_can_reduce.transpose().reset_index()
    neighboring_load_served = pd.merge(left=path_mapper, right=neighboring_load_served, on='path')
    # reverse the transmission path so this can be subtracted from load_path_dest
    neighboring_load_served['path_reverse'] = neighboring_load_served['rr'] + '_' + neighboring_load_served['r']
    neighboring_load_served.drop(['r','rr','path'], axis=1, inplace=True)
    neighboring_load_served = neighboring_load_served.set_index('path_reverse').transpose()
    neighboring_load_served = neighboring_load_served[flows.columns]
    # Subtract load that could be served from reducing imports from load_path_dest
    load_path_dest = pd.DataFrame(columns=load_path_dest.columns, data=load_path_dest.values - neighboring_load_served.values)
    
    # scale the imports that can be reduced down by the transmission loss rate
    imports_can_reduce = pd.DataFrame(columns=imports_can_reduce.columns, data=imports_can_reduce.values * (1 - tranlossrates.values))
    
    # scale the load of the destination region up by the transmission loss rate
    load_path_dest = pd.DataFrame(columns=load_path_dest.columns, data=load_path_dest.values / (1 - tranlossrates.values))
    
    # remaining transmission capacity to export power is the minimum of the remaining
    # transmission capacity and the load in the destination region (adjusted for losses)
    exports_avail_path = pd.DataFrame(columns=flows.columns, data=np.minimum(export_trans_cap_remain.values, load_path_dest.values))
    
    # group the eligible imports and exports by region
    imports_can_reduce = imports_can_reduce.transpose().reset_index()
    imports_can_reduce = pd.merge(left=path_mapper[['rr','path']], right=imports_can_reduce, on='path')
    imports_can_reduce = imports_can_reduce.groupby('rr').sum().transpose()
    exports_avail_path = exports_avail_path.transpose().reset_index()
    exports_avail_path = pd.merge(left=path_mapper[['r','path']], right=exports_avail_path, on='path')
    exports_avail_path = exports_avail_path.groupby('r').sum().transpose()
    
    # Adjust the marginal net load by the available transmission to get available
    # load for marginal resources
    # Only do this where there is curtailment in net_load_adj
    load_avail_utility = pd.DataFrame(columns=net_load_adj_no_curt.columns, data=np.where(trans_region_curt[net_load_adj_no_curt.columns], 0, net_load_adj_no_curt.values + exports_avail_path.values + imports_can_reduce.values))
    
    # A seperate adjusted net load profile is used for distributed resources since
    # distributed resources cannot be exported to a neighboring region
    load_avail_dist = pd.DataFrame(columns=load_avail_utility.columns, data=np.where(trans_region_curt[net_load_adj_no_curt.columns], 0, load_avail_utility.values - exports_avail_path.values))
    
    # =============================================================================
    # Marginal curtailment
    # =============================================================================
    
    # expand load_avail_dist to include a profile for each distributed resource in the "i" set
    load_avail_resource_dist = expand_df(load_avail_dist, i_resource_r_dist, 'r', 'resource', ['i','r'])
    
    # expand load_avail_utility to include a profile for each utility-scale resource in the "i" set
    load_avail_resource_utility = expand_df(load_avail_utility, i_resource_r_utility, 'r', 'resource', ['i','r'])
    
    # combine utility and distributed resources for marginal curtailment calculations
    load_avail_resource = pd.concat([load_avail_resource_utility,load_avail_resource_dist], axis=1, sort=False)
    # align the column order the recf_marg
    load_avail_resource = load_avail_resource[recf_marg.columns]
    
    # get the marginal net load profile for each resource in the "i" set
    net_load_marg = pd.DataFrame(columns=recf_marg.columns, data=(load_avail_resource.values - recf_marg.values))
    
    # get the marginal curtailment profile for each resource in the "i" set
    marg_curt = pd.DataFrame(columns=net_load_marg.columns, data=np.clip(net_load_marg.values, a_min=None, a_max=0) * -1)
    
    # get marginal curtailment by time slice
    marg_curt_h = pd.concat([hdtmap_single[['h']],marg_curt], sort=False, axis=1)
    marg_curt_h = marg_curt_h.groupby('h').sum()
    
    # get the total generation of each marginal resource before curtailment
    marg_gen_h = pd.concat([hdtmap_single[['h']],recf_marg], sort=False, axis=1)
    marg_gen_h = marg_gen_h.groupby('h').sum()
    
    # get the marginal curtailment ratio
    curt_ratio_h = marg_curt_h / marg_gen_h
    curt_ratio_h.fillna(0,inplace=True)
#%%    
    # =============================================================================
    # Calculate recovery of marginal storage with marginal curtailment
    # =============================================================================
    
    if os.name!="posix":
        print('calculating potential recovery of marginal curtailment from marginal storage...')
        
    # Clip the curtailment profiles to the size of marginal storage and recompute
    # curtailment that could be recovered by storage if the marginal storage size
    # is smaller than the marginal vre size
    if marg_stor_MW < marg_vre_mw:
        marg_curt_stor = pd.DataFrame(columns=marg_curt.columns, data=np.clip(marg_curt.values, a_min=0, a_max=marg_stor_MW))
        marg_curt_stor_h = pd.concat([hdtmap_single[['h']],marg_curt_stor], sort=False, axis=1)
        marg_curt_stor_h = marg_curt_stor_h.groupby('h').sum()
    else:
        marg_curt_stor_h = marg_curt_h.copy()
    
    # distributed resources are not considered in curtailment recovery calculations,
    # so filtering them out here
    net_load_marg_utility = net_load_marg[load_avail_resource_utility.columns]
    marg_curt_h_utility = marg_curt_stor_h[load_avail_resource_utility.columns]
    
    # clip net_load_marg_utility at +/- marg_stor_MW to get the available charge/discharge profile of marginal storage with marginal VRE
    poss_batt_changes_marg = pd.DataFrame(columns=load_avail_resource_utility.columns, data=-1*np.clip(net_load_marg_utility, a_min=-marg_stor_MW, a_max=marg_stor_MW))
    
    # Get the marginal curtialment recovery rate for each marginal storage technology
    marg_curt_marg_stor_recovery_ratio = dict()
    for i in marg_stor_props.index:
        marg_stor_MWh = marg_stor_props.loc[i,'MWh']
        marg_stor_eff = marg_stor_props.loc[i,'rte']
        marg_curt_marg_stor_recovery_ratio[i] = storage_curt_recovery(marg_stor_MWh, marg_stor_eff, ts_length, poss_batt_changes_marg, hdtmap_single, marg_curt_h_utility)
#%%    
    # =============================================================================
    # Repeating for marginal storage with existing curtailment
    # =============================================================================
    
    if os.name!="posix":
        print('calculating potential recovery of existing curtailment from marginal storage...')
    
    # clip net_load_adj at +/- marg_stor_MW to get the available charge/discharge profile of marginal storage with existing VRE
    poss_batt_changes_margexist = pd.DataFrame(columns=net_load_adj.columns, data=-1*np.clip(net_load_adj, a_min=-marg_stor_MW, a_max=marg_stor_MW))
    
    # Clip curtailment at the storage power capacity level and recompute so that 
    # curtailment recovery is relative to how much marginal storage could have recovered
    curt_region = pd.DataFrame(columns=net_load_adj.columns, data=np.clip(net_load_adj.values, a_min=-marg_stor_MW, a_max=0))
    # Get existing curtailment by timeslice
    curt_region_h = pd.concat([hdtmap_single[['h']],curt_region], sort=False, axis=1)
    curt_region_h = curt_region_h.groupby('h').sum()
    curt_region_h.loc[:,:] *= -1
    
    # Get the existing curtailment recovery rate for each marginal storage technology
    exist_curt_marg_stor_recovery_ratio = dict()
    for i in marg_stor_props.index:
        marg_stor_MWh = marg_stor_props.loc[i,'MWh']
        marg_stor_eff = marg_stor_props.loc[i,'rte']
        exist_curt_marg_stor_recovery_ratio[i] = storage_curt_recovery(marg_stor_MWh, marg_stor_eff, ts_length, poss_batt_changes_margexist, hdtmap_single, curt_region_h)
    
    # =============================================================================
    # Calculating ability of existing storage to reduce marginal curtailment
    # =============================================================================
    
    if os.name!="posix":
        print('calculating potential recovery of marginal curtailment from existing storage...')
    
    # Map storage devices to resource_device combinations
    cap_stor_resource_device = pd.merge(left=resource_device_utility[['device','resource_device']], right=cap_stor, how='right', on='device')
    
    # expand net_load_marg_utility to include a profile for every utility scale resource-storage device combination
    net_load_marg_resource_device_utility = expand_df(net_load_marg_utility, resource_device_utility[['resource','device','r','resource_device']], 'resource', 'resource_device', ['resource','device','r'])
    # reorder columns to match cap_stor_resource_device
    net_load_marg_resource_device_utility = net_load_marg_resource_device_utility[cap_stor_resource_device['resource_device']]
    
    # Create lists for existing storage properties
    exist_stor_MWh = cap_stor_resource_device['MWh'].values
    exist_stor_MW = cap_stor_resource_device['MW'].values
    exist_stor_eff = cap_stor_resource_device['rte'].values
    
    # Get the hourly curtailment for each utility-scale resource-device combination
    curt_resource_device_utility = pd.DataFrame(columns=net_load_marg_resource_device_utility.columns, data=-1*np.clip(net_load_marg_resource_device_utility.values, a_min=-exist_stor_MW, a_max=0))
    
    # aggregate this curtailment by timeslice
    curt_resource_device_utility_h = pd.concat([hdtmap_single[['h']],curt_resource_device_utility], sort=False, axis=1)
    curt_resource_device_utility_h = curt_resource_device_utility_h.groupby('h').sum()
    
    # get the possible storage level changes for each device for each resource-device combination
    poss_batt_changes_exist = pd.DataFrame(columns=net_load_marg_resource_device_utility.columns, data=-1*np.clip(net_load_marg_resource_device_utility.values, a_min=-exist_stor_MW, a_max=exist_stor_MW))
    
    marg_curt_exist_stor_recovery_ratio = storage_curt_recovery(exist_stor_MWh, exist_stor_eff, ts_length, poss_batt_changes_exist, hdtmap_single, curt_resource_device_utility_h)
    
    # get the state-of-charge of storage from Osprey
    stor_level = osprey_results['state_of_charge'].copy()
    stor_level['device'] = stor_level['i'] + stor_level['v'] + stor_level['r']
    stor_level = get_as_hourly(stor_level,'d_hr','device','Val',net_load_adj,d_hr)
    
    # get the remaining cycles-per-day for storage in Osprey
    remaining_cycles_per_day = get_remaining_cycles_per_day(stor_level, marg_curt_exist_stor_recovery_ratio, resource_device_utility, d_hr, cap_stor, args['marg_curt_cycles_per_day'])
    
    # Adjust curt_recovery_ratio_exist by the cycles remaining per day
    marg_curt_exist_stor_recovery_ratio = pd.DataFrame(index=marg_curt_exist_stor_recovery_ratio.index, columns=marg_curt_exist_stor_recovery_ratio.columns, data=marg_curt_exist_stor_recovery_ratio.values*remaining_cycles_per_day.values)
#%%    
    # =============================================================================
    # Packaging results for ReEDS
    # =============================================================================
    
    # Add source types to resource_device_utility and i_resource_r_utility
    pv_techs = [item for sublist in [techs[x] for x in ['UPV','DISTPV']] for item in sublist]
    resource_device_utility.loc[resource_device_utility['i'].isin(pv_techs),'src'] = 'pv'
    resource_device_utility.loc[resource_device_utility['i'].isin(techs['WIND']),'src'] = 'wind'
    i_resource_r_utility.loc[i_resource_r_utility['i'].isin(pv_techs),'src'] = 'pv'
    i_resource_r_utility.loc[i_resource_r_utility['i'].isin(techs['WIND']),'src'] = 'wind'
#%%    
    # Take the average of curt_stor across source and device
    curt_stor = marg_curt_exist_stor_recovery_ratio.transpose().reset_index()
    curt_stor = pd.merge(left=resource_device_utility[['src','device','resource_device']].rename(columns={'resource_device':'index'}), right=curt_stor, on='index')
    curt_stor = curt_stor.groupby(['src','device'], as_index=False).mean()
    # Merge in the storage technology and regions
    curt_stor = pd.merge(left=cap_stor_resource_device[['i','r','device']].drop_duplicates(), right=curt_stor, on='device', how='right')
    curt_stor.drop('device', axis=1, inplace=True)
    # Collapse to long fromat for ReEDS
    curt_stor = curt_stor.melt(id_vars=['i','r','src'], var_name='h')
    # Merge in the reeds vintages that exist
    curt_stor = pd.merge(left=cap_stor_reeds[['i','v','r']], right=curt_stor, on=['i','r'])
    # Reorder columns to match ReEDS convention
    curt_stor = curt_stor[['i','v','r','h','src','value']]
    
    # Get the marginal vintage of each storage tech
    ivt = pd.read_csv(os.path.join('A_Inputs','inputs','generators','ivt.csv'), index_col=0)
    ivt.index = ivt.index.str.lower()
    ivt = ivt.astype('Int64')
    for i in marg_stor_props.index:
        marg_stor_props.loc[i,'v'] = 'new' + str(ivt.loc[i,str(year)])
#%%   
    # Collect exist curt/marg stor results
    for i in exist_curt_marg_stor_recovery_ratio.keys():
        # Get results for one tech at a time
        temp = exist_curt_marg_stor_recovery_ratio[i].reset_index()
        # Collapse to long format
        temp = temp.melt(id_vars='h', var_name='r')
        # Define tech and vintage
        temp['i'] = i
        temp['v'] = marg_stor_props.loc[i,'v']
        # Charging from existing curtailment is in the "old" category
        temp['src'] = 'old'
        # Concatenate these results with the rest
        curt_stor = pd.concat([curt_stor, temp], sort=False).reset_index(drop=True)
      
    # Collect marg curt/marg stor results
    for i in marg_curt_marg_stor_recovery_ratio.keys():
        # Get results for one tech at a time
        temp = marg_curt_marg_stor_recovery_ratio[i].reset_index()
        # Collapse to long format
        temp = temp.melt(id_vars='h', var_name='resource')
        # Take the average of curt_stor across source
        temp = pd.merge(left=i_resource_r_utility, right=temp, on='resource', how='right')
        temp = temp.groupby(['r','h','src'], as_index=False).mean()
        # Define tech and vintage
        temp['i'] = i
        temp['v'] = marg_stor_props.loc[i,'v']
        # Concatenate these results with the rest
        curt_stor = pd.concat([curt_stor, temp], sort=False).reset_index(drop=True)
#%%    
    # Set the year and organize the columns to match ReEDS
    curt_stor['t'] = str(year)
    curt_stor = curt_stor[['i','v','r','h','src','t','value']]
    # Remove small numbers and round results
    curt_stor.loc[curt_stor['value']<args['min_val'],'value'] = 0
    curt_stor['value'] = curt_stor['value'].round(args['decimals'])
   
    # Format marginal curtailment results for ReEDS
    surplusmarginal = curt_ratio_h.reset_index().melt(id_vars='h').rename(columns={'variable':'resource'})
    surplusmarginal = pd.merge(left=surplusmarginal, right=resources, on='resource', how='left')
    surplusmarginal['t'] = args['next_year']
    surplusmarginal = surplusmarginal.rename(columns={'tech':'i','area':'r'})
    surplusmarginal = surplusmarginal[['i','r','h','t','value']]

    # Marginal curtailment must be a fraction
    surplusmarginal.loc[surplusmarginal['value']>1,'value'] = 1
    # Remove small numbers and round results
    surplusmarginal.loc[surplusmarginal['value']<args['min_val'],'value'] = 0
    surplusmarginal['value'] = surplusmarginal['value'].round(args['decimals'])
    
    results = {'curt_stor':curt_stor,
               'curt_marg':surplusmarginal,
               'curt_tran':curt_tran_h,
               'curt_reduct_tran_max':curt_reduct_tran_max}
    #%%
    return results, trans_region_curt

# %%
