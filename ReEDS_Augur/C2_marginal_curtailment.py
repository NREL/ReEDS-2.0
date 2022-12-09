# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 11:43:05 2020

@author: afrazier
"""
#%% Imports
import pandas as pd
import numpy as np
import os

from ReEDS_Augur.utility.functions import apply_series_to_df, \
    filter_data_year, format_tranloss, map_rs_to_r, format_trancap, \
    convert_series_to_profiles, get_storage_eff, get_prop, expand_df, \
    adjust_tz, storage_curt_recovery, get_remaining_cycles_per_day, \
    expand_star, dr_curt_recovery

    
from ReEDS_Augur.utility.generatordata import GEN_DATA
from ReEDS_Augur.utility.hourlyprofiles import HOURLY_PROFILES, OSPREY_RESULTS
from ReEDS_Augur.utility.inputs import INPUTS
from ReEDS_Augur.utility.switchsettings import SwitchSettings

#%%
def marginal_curtailment(curt_results):
    '''

    Parameters
    ----------
    curt_results : Dictionary
        Existing curtailment results.

    Returns
    -------
    mc_results : Dictionary
        Marginal curtailment results.

    '''
    #%% Bypass this calculation if not running Augur
    if not int(SwitchSettings.switches['gsw_augurcurtailment']):
        mc_results = {
            'curt_stor': pd.DataFrame(columns=['i','v','r','h','src','t','value']),
            'curt_marg': pd.DataFrame(columns=['i','r','h','t','value']),
            'curt_tran': pd.DataFrame(columns=['r','rr','h','t','value']),
            'curt_prod': pd.DataFrame(columns=['r','h','t','value']),
            'net_load_adj_no_curt_h': pd.DataFrame(columns=['r','h','t','value']),
            'curt_dr': pd.DataFrame(columns=['i','v','r','h','src','t','value']),
        }
        trans_region_curt = pd.DataFrame()
        return mc_results, trans_region_curt

    #%% Continue
    # collect inputs
    techs = INPUTS['i_subsets'].get_data()

    # collect arguments
    year =         SwitchSettings.next_year
    marg_stor_MW = SwitchSettings.switches['marg_stor_mw']
    marg_dr_MW =   SwitchSettings.switches['marg_dr_mw']
    marg_vre_mw =  SwitchSettings.switches['marg_vre_mw_curt']
    marg_trans =   SwitchSettings.switches['curt_tran_step_size']
    marg_prod    = SwitchSettings.switches['marg_prod_size']

    # collect data from A_prep_data
    ts_length = SwitchSettings.switches['osprey_ts_length']
    cap_stor = GEN_DATA['max_cap'].copy()
    cap_stor = cap_stor[cap_stor['i'].isin(techs['storage_standalone'])]
    cap_stor['device'] = cap_stor['i'] + '_' + cap_stor['v'] + cap_stor['r']
    cap_stor_e = GEN_DATA['energy_cap'].copy()
    cap_stor = cap_stor.merge(cap_stor_e, on = ['i','v','r'])
    stor_eff = get_storage_eff()
    cap_stor = cap_stor.merge(stor_eff, on = 'i')
    cap_stor = get_prop(cap_stor, 'storage_duration', merge_cols = ['i'])
    # cap_stor_reeds =  marg_curt_data['cap_stor_reeds'].copy()
    cap_dr = GEN_DATA['max_cap'].copy()
    cap_dr = cap_dr[cap_dr['i'].isin(techs['dr1']+techs['dr2'])]
    cap_dr['device'] = cap_dr['i'] + '_' + cap_dr['v'] + cap_dr['r']
    dr_eff = get_storage_eff()
    cap_dr = cap_dr.merge(dr_eff, on = 'i')
    tranloss = format_tranloss()
    tranloss = (
        tranloss
        .rename(columns={'tranloss':'loss'})
        .assign(path=tranloss['r'] + '_' + tranloss['rr'])
        .loc[tranloss.trtype=='AC'].drop('trtype', axis=1)
    )
    resources_in = INPUTS['resources'].get_data()
    ### Remove CSP
    resources = resources_in.loc[~resources_in.resource.str.startswith('csp')].copy()
    resource_r = map_rs_to_r(resources)[['r','resource']].drop_duplicates()
    rfeas = INPUTS['rfeas'].get_data()['r'].tolist()
    ##! TODO: Do we need a `.groupby('resource').cf_marg.mean()` here?
    gen_marg_vre = filter_data_year(
        (HOURLY_PROFILES['vre_cf_marg'].profiles
         * SwitchSettings.switches['marg_vre_mw_curt']),
        data_years=SwitchSettings.osprey_years
    )[resources.resource.drop_duplicates().values].copy()
    gen_marg_vre_local = adjust_tz(gen_marg_vre, 
                                   mapper = resource_r,
                                   option = 'ET_to_local')
    # DR data only exists for 2012 weather year, so no filtering needed
    dr_inc = HOURLY_PROFILES['dr_inc_marg'].profiles.copy()
    dr_inc_local = adjust_tz(dr_inc,
                             mapper = resource_r,
                             option = 'ET_to_local')
    dr_dec = HOURLY_PROFILES['dr_dec_marg'].profiles.copy()
    dr_dec_local = adjust_tz(dr_dec,
                             mapper = resource_r,
                             option = 'ET_to_local')

    # collect osprey_results
    trancap = format_trancap()
    trancap = (
        trancap
        .assign(path=trancap['r'] + '_' + trancap['rr'])
        .loc[trancap.trtype=='AC'].drop('trtype', axis=1)
    )
    flows = INPUTS['osprey_flows'].get_data()
    flows = (
        flows
        .assign(path=(flows['r'] + '_' + flows['rr']))
        .assign(idx_hr=((flows.d.str[1:].astype(int) - 1) * 24
                        + flows.hr.str[2:].astype(int) - 1))
        .loc[flows.trtype=='AC']
        .pivot(index='idx_hr', columns='path', values='Val')
        .reindex(index=range(ts_length),
                 columns=trancap['path'].tolist())
        ## Fill empty flow directions
        .reindex(trancap.path, axis=1)
        .fillna(0)
    )
    ### BUG Ignore VSC for now
    export_trans_cap_remain = trancap.set_index('path').MW - flows
    trans_regions = OSPREY_RESULTS['trans_regions'].get_data()

    # collect curtailment results
    net_load_adj = curt_results['curt_load_adj'].copy()
    net_load_adj_local = adjust_tz(net_load_adj, option = 'ET_to_local')

    ### Include multi-link paths
    
    if SwitchSettings.switches['gsw_transmultilink'] != '0':
        path_mapper_multi = pd.read_csv(
            os.path.join('inputs_case','trans_multilink_paths.csv')
        )[['r','rr','path','loss']]

        path_mapper_multi['path'] = path_mapper_multi['path'].map(
            lambda x: x.replace('|','_'))
        ### Drop 0-link paths and out-of-model regions
        path_mapper_multi.drop(
            path_mapper_multi.loc[
                (path_mapper_multi.r == path_mapper_multi.rr)
                | (~path_mapper_multi.r.isin(rfeas))
                | (~path_mapper_multi.rr.isin(rfeas))
            ].index, inplace=True
        )
        ### Append to path_mapper and drop duplicates
        path_mapper = (
            tranloss.append(path_mapper_multi)
            ## keep='first' keeps adjacent links even if there are better
            ## (lower-loss or lower-cost) non-adjacent paths; keep='last' 
            ## always uses the best path even if non-adjacent
            .drop_duplicates(subset=['r','rr'], keep='first')
            .reset_index(drop=True)
        )

    ### Get path-to-loss mapper if sw_multilink = 0
    else:
        path_mapper = tranloss.copy()

    path_loss = pd.Series(
        index=path_mapper.path.values, data=path_mapper.loss.values)
    
    # Sort columns of flows alphabetically so we can align columns without
    # using flows (since curtailment reduction has more paths than flows)
    flows.sort_index(axis=1, inplace=True)

    # collecting miscellaneous
    hdtmap = pd.read_csv(
        os.path.join('inputs_case', 'h_dt_szn.csv'),
    )
    idx = hdtmap.year.isin(SwitchSettings.switches['osprey_years'])
    hdtmap_single = hdtmap[idx].reset_index(drop=True)
    d_hr = pd.read_csv(
        os.path.join('inputs_case', 'index_hr_map.csv')
    )[['d', 'hr']].copy()
    d_hr['d_hr'] = d_hr['d'] + '_' + d_hr['hr']
    marg_stor_props = get_prop(stor_eff,
                               'storage_duration', merge_cols = ['i'])
    marg_stor_props = marg_stor_props.set_index('i')
    marg_stor_props['MWh'] = marg_stor_props['duration'] * marg_stor_MW

    marg_dr_props = stor_eff[(stor_eff['i'].isin(techs['dr1']))]

    dr_hrs = INPUTS['dr_hrs'].get_data()
    dr_hrs['hrs'] = list(zip(dr_hrs.pos_hrs, -dr_hrs.neg_hrs))
    dr_hrs['max_hrs'] = 8760
    dr_shed = INPUTS['dr_shed'].get_data()
    dr_shed['hrs'] = [(1, 1)]*len(dr_shed.index)
    dr_hrs = pd.concat([dr_hrs, dr_shed])

    marg_dr_props = pd.merge(marg_dr_props, dr_hrs, on='i', how='right').set_index('i')
    # Fill missing data
    marg_dr_props.loc[marg_dr_props.RTE != marg_dr_props.RTE, 'RTE'] = 1
    marg_dr_props = marg_dr_props[['hrs', 'max_hrs', 'RTE']]

    # map all vre resources in the "i" set to the "r" set - wind is normally
    # mapped to s-region rather than p-region
    i_resource_r = map_rs_to_r(resources)[['i', 'resource', 'r']].drop_duplicates()
    # filter for utility-scale resources and distributed resources seperately
    i_resource_r_utility = i_resource_r[i_resource_r['i'].isin(
        techs['vre_utility']+techs['pvb'])].reset_index(drop=True)
    i_resource_r_dist = i_resource_r[i_resource_r['i'].isin(
        techs['vre_distributed'])].reset_index(drop=True)

    # Map each resource in a region to each storage device in the same region
    resource_device_utility = pd.merge(left=i_resource_r_utility,
                                       right=cap_stor[['r', 'device']],
                                       on='r', how='right')
    if SwitchSettings.switches['gsw_storage'] != '0':
        resource_device_utility['resource_device'] = (
            resource_device_utility['resource'].astype(str) 
            + '_' + resource_device_utility['device'])
        # Add source types to resource_device_utility and i_resource_r_utility
        for tech in ['pv','wind']:
            resource_device_utility.loc[
                resource_device_utility['i'].isin(techs[tech]), 'src'] = tech
            i_resource_r_utility.loc[
                i_resource_r_utility['i'].isin(techs[tech]), 'src'] = tech
        ### 'pvb' counts as 'pv'
        resource_device_utility.loc[
            resource_device_utility['i'].isin(techs['pvb']), 'src'] = 'pv'
        i_resource_r_utility.loc[
            i_resource_r_utility['i'].isin(techs['pvb']), 'src'] = 'pv'
    # Map each resource in a region to each DR device in the same region
    resource_dr_utility = pd.merge(left=i_resource_r_utility,
                                   right=cap_dr[['r', 'device']],
                                   on='r', how='right')
    resource_dr_utility['resource_device'] = \
        resource_dr_utility['resource'].astype(str) + '_' \
        + resource_dr_utility['device']
    resource_dr_utility = resource_dr_utility.assign(src=None)
    resource_dr_utility.loc[
        resource_dr_utility['i'].isin(techs['pv']), 'src'] = 'pv'
    resource_dr_utility.loc[
        resource_dr_utility['i'].isin(techs['wind']), 'src'] = 'wind'

    # =========================================================================
    # Find transmission regions that have curtailment
    # =========================================================================

    # Pivot the trans_region df to wide format
    trans_regions = trans_regions.pivot(index='idx_hr', columns='r',
                                        values='trans_region')
    # Find the trans_regions that have a curtailing BA inside them
    trans_regions_with_curt = trans_regions[net_load_adj < 0].fillna(0).melt()
    # Filter out zeros, which represent no curtailment
    trans_regions_with_curt = trans_regions_with_curt[
        trans_regions_with_curt['value'] > 0].reset_index(drop=True).rename(
            columns={'r': 'curtailing BA', 'value': 'trans_region'})

    # Get this information in wide format to use as a conditional for adding
    # transmission capacity to load profiles. Limit to trans-connected regions.
    trans_region_curt = trans_regions.isin(
        trans_regions_with_curt['trans_region'].unique())



    # =========================================================================
    # Marginal transmission reducing existing curtailment
    # =========================================================================

    # expand to include a column for each transmission path with
    # the load of the source region for each path
    load_path_source = expand_df(
        df=net_load_adj, expand=path_mapper[['path', 'r']], 
        old_col='r', new_col='path', drop_cols=['r']
    ).sort_index(axis=1)

    # Only consider curtailment in source profiles
    # curt_path_source is the amount of curtailment in the source region
    # before any marginal transmission is added
    ##! mem
    curt_path_source = pd.DataFrame(columns=load_path_source.columns,
                                    data=np.clip(load_path_source.values,
                                                 a_min=-marg_trans, a_max=0))

    # expand to include a column for each transmission path with
    # the load of the destination region for each path
    load_path_dest = expand_df(
        df=net_load_adj, expand=path_mapper[['path', 'rr']], 
        old_col='rr', new_col='path', drop_cols=['rr']
    ).sort_index(axis=1)

    # Remove curtailment from destination profiles and adjust for transmission
    # losses
    load_path_dest = pd.DataFrame(
        columns=load_path_dest.columns,
        data=np.clip(load_path_dest / (1 - path_loss), a_min=0, a_max=None))

    # Reduce curtailment by the effects of marginal transmission
    # curt_trans_path_source is the amount of curtailment in the source region
    # after marginal transmission has been added
    ##! mem
    curt_trans_path_source = pd.DataFrame(
        columns=curt_path_source.columns,
        data=np.clip(
            curt_path_source.values + np.minimum(load_path_dest.values, marg_trans),
            a_min=None, a_max=0)
    )

    ####### Convert to local time and timeslice resolution and store for ReEDS
    ### Note that CURT_REDUCT_TRANS applies to curtailment in the source region
    ### (not net-load-reduction in the sink region), so we report curt_tran_h
    ### in the timezone of the source region

    curt_path_source_local = adjust_tz(
        df=curt_path_source, mapper=path_mapper[['r','path']], option='ET_to_local')
    
    curt_trans_path_source_local = adjust_tz(
        df=curt_trans_path_source, mapper=path_mapper[['r','path']], option='ET_to_local')

    # Group results by timeslice
    curt_path_source_h = pd.concat(
        [hdtmap_single[['h']], curt_path_source_local], sort=False, axis=1
    ).groupby('h').sum() * -1

    curt_trans_path_source_h = pd.concat(
        [hdtmap_single[['h']], curt_trans_path_source_local], sort=False, axis=1
    ).groupby('h').sum() * -1

    # curt_trans_reduced is the amount of curtailment that was reduced by
    # adding marginal transmission
    curt_trans_reduced = curt_path_source_h - curt_trans_path_source_h

    # Convert to fraction for ReEDS
    curt_tran_h = (
        (curt_trans_reduced / curt_path_source_h).fillna(0)
        ### curt_tran must be a fraction, so cap at 1
        .clip(None,1).round(SwitchSettings.switches['decimals'])
        .transpose().reset_index()
        .rename(columns={'index': 'path'})
        .merge(path_mapper, on='path').drop(['path','loss'], axis=1)
        .melt(id_vars=['r', 'rr'], var_name='h')
    )
    curt_tran_h['t'] = SwitchSettings.next_year
    curt_tran_h = curt_tran_h[['r', 'rr', 'h', 't', 'value']]



    # =========================================================================
    # Adjusting marg curt profiles for existing transmission
    # =========================================================================

    # removing curtailment from load profile for marginal curtailment
    # calculations
    net_load_adj_no_curt = pd.DataFrame(
        columns=net_load_adj.columns,
        data=np.clip(net_load_adj.values, a_min=0, a_max=None,
                     out=net_load_adj.values.copy()))

    # expand to include a column for each transmission path with
    # the load of the source region for each path
    load_path_source_nocurt = expand_df(
        df=net_load_adj_no_curt, expand=path_mapper[['path', 'r']], 
        old_col='r', new_col='path', drop_cols=['r']
    ).sort_index(axis=1)

    # ability to reduce imports is the minimum of the flow along a path
    # and the load in the source region.
    imports_can_reduce = pd.DataFrame(
        columns=flows.columns,
        data=np.minimum(
            flows.values, load_path_source_nocurt[flows.columns].values))

    # expand to include a column for each transmission path with
    # the load of the destination region for each path
    load_path_dest_nocurt = expand_df(
        df=net_load_adj_no_curt, expand=path_mapper[['path', 'rr']], 
        old_col='rr', new_col='path', drop_cols=['rr'])
    # Reformatting the columns to match flows
    load_path_dest_nocurt = load_path_dest_nocurt[flows.columns]

    # Subtract the load associated with reducing imports from the load
    # associated with increasing exports before comparing remaining export
    # capacity with the load in the destination region. This avoids
    # double-counting load in neighboring regions when accounting for
    # transmission capacity in marginal calculations.
    neighboring_load_served = pd.merge(left=path_mapper.drop('loss',axis=1),
                                       right=imports_can_reduce.T.reset_index(),
                                       on='path')
    # reverse the transmission path so this can be subtracted from
    # load_path_dest_nocurt
    neighboring_load_served['path_reverse'] = \
        neighboring_load_served['rr'] + '_' + neighboring_load_served['r']
    neighboring_load_served.drop(['r', 'rr', 'path'], axis=1, inplace=True)
    neighboring_load_served = neighboring_load_served.set_index(
        'path_reverse').T
    neighboring_load_served = neighboring_load_served[flows.columns]
    # Subtract load that could be served from reducing imports from
    # load_path_dest_nocurt
    load_path_dest_nocurt = pd.DataFrame(
        columns=load_path_dest_nocurt.columns,
        data=load_path_dest_nocurt.values - neighboring_load_served.values)

    # scale the imports that can be reduced down by the transmission loss rate
    imports_can_reduce = pd.DataFrame(
        columns=imports_can_reduce.columns,
        data=imports_can_reduce * (1 - path_loss[imports_can_reduce.columns]))

    # scale the load of the destination region up by the transmission loss rate
    load_path_dest_nocurt = pd.DataFrame(
        columns=load_path_dest_nocurt.columns,
        data=(load_path_dest_nocurt 
              / (1 - path_loss[load_path_dest_nocurt.columns].values)))

    # remaining transmission capacity to export power is the minimum of the
    # remaining transmission capacity and the load in the destination region
    # (adjusted for losses)
    exports_avail_path = pd.DataFrame(
        columns=flows.columns,
        data=np.minimum(
            export_trans_cap_remain.values, load_path_dest_nocurt.values))

    # group the eligible imports and exports by region
    imports_can_reduce = pd.merge(
        left=path_mapper[['rr', 'path']], right=imports_can_reduce.T.reset_index(), 
        on='path'
    ).groupby('rr').sum().T.reindex(rfeas, axis=1).fillna(0)

    exports_avail_path = pd.merge(
        left=path_mapper[['r', 'path']], right=exports_avail_path.T.reset_index(), 
        on='path'
    ).groupby('r').sum().T.reindex(rfeas, axis=1).fillna(0)

    # Adjust the marginal net load by the available transmission to get
    # available load for marginal resources. Only do this where there is
    # curtailment in net_load_adj.
    load_avail_utility = pd.DataFrame(
        columns=net_load_adj_no_curt.columns,
        data=np.where(
            trans_region_curt, 0, 
            net_load_adj_no_curt.values + exports_avail_path.values + imports_can_reduce.values))

    # A seperate adjusted net load profile is used for distributed resources
    # since distributed resources cannot be exported to a neighboring region
    load_avail_dist = pd.DataFrame(
        columns=load_avail_utility.columns,
        data=np.where(
            trans_region_curt, 0,
            load_avail_utility.values - exports_avail_path.values))



    # =========================================================================
    # Marginal curtailment
    # =========================================================================

    # expand load_avail_dist to include a profile for each distributed
    # resource in the "i" set
    load_avail_resource_dist = expand_df(
        df=load_avail_dist, expand=i_resource_r_dist,
        old_col='r', new_col='resource', drop_cols=['i', 'r'])

    # expand load_avail_utility to include a profile for each utility-scale
    # resource in the "i" set
    load_avail_resource_utility = expand_df(
        df=load_avail_utility, expand=i_resource_r_utility[['resource','r']].drop_duplicates(), 
        old_col='r', new_col='resource', drop_cols=['r'])

    # combine utility and distributed resources for marginal curtailment
    # calculations
    load_avail_resource = pd.concat([load_avail_resource_utility,
                                     load_avail_resource_dist],
                                    axis=1, sort=False
    # align the column order the recf_marg
    )[gen_marg_vre.columns]

    # get the marginal net load profile for each resource in the "i" set
    ##! mem
    net_load_marg = pd.DataFrame(
        columns=gen_marg_vre.columns,
        data=(load_avail_resource.values - gen_marg_vre.values))

    # get the marginal curtailment profile for each resource in the "i" set
    marg_curt = pd.DataFrame(
        columns=net_load_marg.columns,
        data=np.clip(net_load_marg.values, a_min=None, a_max=0) * -1)

    ###### Convert to local time, then to timeslice for ReEDS
    marg_curt_local = adjust_tz(
        df=marg_curt, mapper=resource_r, option='ET_to_local')

    # get marginal curtailment by time slice
    marg_curt_h = pd.concat([hdtmap_single[['h']], marg_curt_local], sort=False,
                            axis=1).groupby('h').sum()

    # get the total generation of each marginal resource before curtailment
    marg_gen_h = pd.concat([hdtmap_single[['h']], gen_marg_vre_local], sort=False,
                           axis=1).groupby('h').sum()

    # get the marginal curtailment ratio
    curt_ratio_h = (marg_curt_h / marg_gen_h).fillna(0)



    # =========================================================================
    # Calculate recovery of marginal curtailment with marginal storage
    # =========================================================================
    
    if SwitchSettings.switches['gsw_storage'] != '0':
    
        # Clip the curtailment profiles to the size of marginal storage and
        # recompute curtailment that could be recovered by storage if the
        # marginal storage size is smaller than the marginal vre size
        if marg_stor_MW < marg_vre_mw:
            marg_curt_stor = pd.DataFrame(
                columns=marg_curt.columns,
                # Use local since we convert to timeslices for ReEDS
                data=np.clip(marg_curt_local.values,
                             a_min=0,
                             a_max=marg_stor_MW))
            marg_curt_stor_h = pd.concat(
                    [hdtmap_single[['h']], marg_curt_stor],
                    sort=False, axis=1).groupby('h').sum()
        else:
            marg_curt_stor_h = marg_curt_h.copy()
    
        # Distributed resources are not considered in curtailment recovery
        # calculations, so filtering them out here
        ### Also convert to local to align with marg_curt_h_utility
        net_load_marg_utility_local = adjust_tz(
            df=net_load_marg[load_avail_resource_utility.columns],
            mapper=i_resource_r_utility[['r','resource']].drop_duplicates(), option='ET_to_local'
        )
        marg_curt_h_utility = marg_curt_stor_h[
                load_avail_resource_utility.columns]
    
        # clip net_load_marg_utility at +/- marg_stor_MW to get the available
        # charge/discharge profile of marginal storage with marginal VRE
        poss_batt_changes_marg_local = pd.DataFrame(
            columns=load_avail_resource_utility.columns,
            data=-1*np.clip(net_load_marg_utility_local,
                            a_min=-marg_stor_MW,
                            a_max=marg_stor_MW))
    
        ### Calculate the marginal curtailment recovery from marginal storage
        marg_curt_marg_stor_recovery_ratio = dict()
        for i in marg_stor_props.index:
            marg_stor_MWh = marg_stor_props.loc[i, 'MWh']
            marg_stor_eff = marg_stor_props.loc[i, 'RTE']
            marg_curt_marg_stor_recovery_ratio[i] = storage_curt_recovery(
                e=marg_stor_MWh, eff=marg_stor_eff, ts_length=ts_length, 
                poss_batt_changes=poss_batt_changes_marg_local,
                hdtmap=hdtmap_single, marg_curt_h=marg_curt_h_utility)

    # =========================================================================
    # Repeat for marginal storage with existing curtailment
    # =========================================================================

        ### Use local time since outputs are by timeslice
        # clip net_load_adj at +/- marg_stor_MW to get the available
        # charge/discharge profile of marginal storage with existing VRE
        poss_batt_changes_margexist_local = pd.DataFrame(
            columns=net_load_adj_local.columns,
            data=-1*np.clip(net_load_adj_local,
                            a_min=-marg_stor_MW,
                            a_max=marg_stor_MW))
    
        # Clip curtailment at the storage power capacity level and recompute so
        # that curtailment recovery is relative to how much marginal storage could
        # have recovered
        curt_region_local = pd.DataFrame(
            columns=net_load_adj_local.columns,
            data=np.clip(net_load_adj_local.values,
                         a_min=-marg_stor_MW,
                         a_max=0))
        # Get existing curtailment by timeslice
        curt_region_h = pd.concat([hdtmap_single[['h']], curt_region_local], 
                                  sort=False, axis=1).groupby('h').sum()
        curt_region_h.loc[:, :] *= -1
    
        # Get the existing curtailment recovery rate for each marginal storage
        # technology
        exist_curt_marg_stor_recovery_ratio = dict()
        for i in marg_stor_props.index:
            marg_stor_MWh = marg_stor_props.loc[i, 'MWh']
            marg_stor_eff = marg_stor_props.loc[i, 'RTE']
            exist_curt_marg_stor_recovery_ratio[i] = storage_curt_recovery(
                e=marg_stor_MWh, eff=marg_stor_eff, ts_length=ts_length,
                poss_batt_changes=poss_batt_changes_margexist_local, 
                hdtmap=hdtmap_single, marg_curt_h=curt_region_h)



    # =========================================================================
    # Repeating for marginal prod production with existing curtailment
    # =========================================================================
    
        curt_region_local_prod = pd.DataFrame(
            columns=net_load_adj_local.columns,
            data=-1*np.clip(net_load_adj_local.values, a_min=-marg_prod, a_max=0)) 
        
        prod_cap8760 = curt_region_local_prod.copy()
        prod_cap8760.loc[:,:] = marg_prod
        prod_cap8760['h'] = hdtmap_single['h']
        prod_cap8760 = prod_cap8760.groupby('h').sum()
        curt_region_local_prod['h'] = hdtmap_single['h']
        curt_region_local_prod = curt_region_local_prod.groupby('h').sum()
        
        prod_curt_recovery = curt_region_local_prod / prod_cap8760
        prod_curt_recovery = prod_curt_recovery.reset_index()
        prod_curt_recovery = prod_curt_recovery.melt(id_vars = 'h',
                                                     var_name = 'r')
        prod_curt_recovery['t'] = year
        prod_curt_recovery = prod_curt_recovery[['r','h','t','value']]

    # =========================================================================
    # Calculating ability of existing storage to reduce marginal curtailment
    # =========================================================================

        # Map storage devices to resource_device combinations
        cap_stor_resource_device = pd.merge(
            left=resource_device_utility[
                    ['device', 'resource_device']].drop_duplicates(),
            right=cap_stor, how='right', on='device')
    
        # expand net_load_marg_utility to include a profile for every utility
        # scale resource-storage device combination
        net_load_marg_resource_device_utility_local = expand_df(
            df=net_load_marg_utility_local,
            expand=resource_device_utility[
                ['resource', 'device', 'r', 'resource_device']].drop_duplicates(),
            old_col='resource', new_col='resource_device', 
            drop_cols=['resource', 'device', 'r'])
        # reorder columns to match cap_stor_resource_device
        net_load_marg_resource_device_utility_local = (
            net_load_marg_resource_device_utility_local[
                cap_stor_resource_device['resource_device']])
    
        # Create lists for existing storage properties
        exist_stor_MWh = cap_stor_resource_device['MWh'].values
        exist_stor_MW = cap_stor_resource_device['MW'].values
        exist_stor_eff = cap_stor_resource_device['RTE'].values
    
        # Get the hourly curtailment for each utility-scale resource-device
        # combination
        curt_resource_device_utility_local = pd.DataFrame(
            columns=net_load_marg_resource_device_utility_local.columns,
            data=-1*np.clip(net_load_marg_resource_device_utility_local.values,
                            a_min=-exist_stor_MW, a_max=0))
    
        ##! speed+
        # aggregate this curtailment by timeslice
        curt_resource_device_utility_h = pd.concat(
            [hdtmap_single[['h']], curt_resource_device_utility_local],
            sort=False, axis=1).groupby('h').sum()
    
        # get the possible storage level changes for each device for each
        # resource-device combination (all in local time)
        poss_batt_changes_exist_local = pd.DataFrame(
            columns=net_load_marg_resource_device_utility_local.columns,
            data=-1*np.clip(net_load_marg_resource_device_utility_local.values,
                            a_min=-exist_stor_MW, a_max=exist_stor_MW))
    
        marg_curt_exist_stor_recovery_ratio = storage_curt_recovery(
            e=exist_stor_MWh, eff=exist_stor_eff, ts_length=ts_length, 
            poss_batt_changes=poss_batt_changes_exist_local,
            hdtmap=hdtmap_single,
            marg_curt_h=curt_resource_device_utility_h)
    
        # get the state-of-charge of storage from Osprey (in eastern time)
        stor_level = INPUTS['osprey_SOC'].get_data(SwitchSettings.prev_year)
        stor_level['device'] = stor_level['i'] + stor_level['v'] + \
                                stor_level['r']
        stor_level['idx_hr'] = ((stor_level.d.str[1:].astype(int) - 1)*24
                         + stor_level.hr.str[2:].astype(int) - 1)
        stor_level = stor_level.pivot(index='idx_hr', columns='device',
                        values='Val').fillna(0)
        stor_level = stor_level.reindex(
                range(SwitchSettings.switches['osprey_ts_length'])).fillna(0)
    
        # get the remaining cycles-per-day for storage in Osprey
        remaining_cycles_per_day = get_remaining_cycles_per_day(
            stor_level=stor_level, 
            marg_curt_exist_stor_recovery_ratio=marg_curt_exist_stor_recovery_ratio,
            resource_device_utility=resource_device_utility, 
            d_hr=d_hr, cap_stor=cap_stor,
            daily_cycle_limit=SwitchSettings.switches['marg_curt_cycles_per_day']
        ### Reformat as series so we can multiply by marg_curt_existing_stor
        ).T['avg_remaining']
    
        # Adjust curt_recovery_ratio_exist by the cycles remaining per day
        marg_curt_exist_stor_recovery_ratio *= (
            remaining_cycles_per_day.reset_index().drop_duplicates()
            .set_index('resource_device')['avg_remaining']
        )

    # =========================================================================
    # Getting the average amount of clipping for PVB to derate curt_stor
    # =========================================================================
    
        pvb_profiles = filter_data_year(
            HOURLY_PROFILES['pvb'].profiles.copy(),
            data_years=SwitchSettings.osprey_years
        ).round(SwitchSettings.switches['decimals'])
    
        resources = INPUTS['resources'].get_data()
        pvb_resources = resources[resources['i'].isin(techs['pvb'])].copy()
    
        ### Get the ILR to identify hours with clipping
        pvb_ilr = (
            INPUTS['ilr_pvb_config'].get_data()
            .set_index('pvb_config')['ilr']
            .round(SwitchSettings.switches['decimals'])
        )
    
        clip_pvb = []
        for pvb_type in [1,2,3]:
            pvbtype_ilr = pvb_ilr['PVB{}'.format(pvb_type)]
            pvbtype_resources = pvb_resources[pvb_resources['i'].isin(techs['pvb{}'.format(pvb_type)])]
            pvbtype_clipcheck = pvb_profiles[pvbtype_resources['resource']]
            ### Clipping occurs when the inverter output is equal to 1/ILR
            clip = pvbtype_clipcheck == round(1/pvbtype_ilr, SwitchSettings.switches['decimals'])
            clip_pvb.append(clip)
        clip_pvb = pd.concat(clip_pvb, sort=False, axis=1)
    
        pvb_resources.set_index('resource', inplace=True)
        for col in clip_pvb:
            pvb_resources.loc[col, 'hours_clipped'] = len(clip_pvb[col][clip_pvb[col]])
        if len(pvb_resources):
            pvb_resources['derate'] = (
                pvb_resources['hours_clipped']
                * int(SwitchSettings.switches['gsw_pvb_dur'])
                / 8760)
        else:
            pvb_resources['derate'] = None
        pvb_resources.loc[pvb_resources['derate'] > 1, 'derate'] = 1
        pvb_resources['derate'] = abs(pvb_resources['derate'] - 1)

    # =========================================================================
    # Packaging results for ReEDS
    # =========================================================================

        # Take the average of curt_stor across source and device
        curt_stor = marg_curt_exist_stor_recovery_ratio.T.reset_index()
        curt_stor = pd.merge(
            left=resource_device_utility[
                ['src', 'device', 'resource_device']].rename(
                    columns={'resource_device': 'index'}),
            right=curt_stor, on='index')
        curt_stor = curt_stor.groupby(['src', 'device'], as_index=False).mean()
        # Merge in the storage technology and regions
        curt_stor = pd.merge(
            left=cap_stor_resource_device[['i', 'r', 'device']].drop_duplicates(),
            right=curt_stor, on='device', how='right'
        ).drop('device', axis=1)
        # Collapse to long fromat for ReEDS
        curt_stor = curt_stor.melt(id_vars=['i', 'r', 'src'], var_name='h')
        # Merge in the reeds vintages that exist
    
        # Get the marginal vintage of each storage tech
        ivt = pd.read_csv(os.path.join('inputs_case', 'ivt.csv'), index_col=0)
        for i in marg_stor_props.index:
            marg_stor_props.loc[i, 'v'] = 'new' + str(ivt.loc[i, str(year)])
        ivt = pd.melt(ivt.reset_index(), id_vars = 'index')
        ivt.rename(columns = {'index':'i', 'variable':'t'}, inplace = True)
        ivt['v'] = 'new' + ivt['value'].astype(str)
        ivt['t'] = pd.to_numeric(ivt['t'])
        ivt = ivt[ivt['t'] <= SwitchSettings.prev_year]
        ivt_stor = ivt[ivt['i'].isin(techs['storage_standalone'])]
        ivt_stor = ivt_stor[['i','v']].drop_duplicates()
            
        curt_stor = pd.merge(left=ivt_stor, right=curt_stor,
                             on=['i'])
        # Reorder columns to match ReEDS convention
        curt_stor = curt_stor[['i', 'v', 'r', 'h', 'src', 'value']]
    
        # Set up the list for concatenating results
        toadd = []
        # Collect exist curt/marg stor results
        for i in exist_curt_marg_stor_recovery_ratio.keys():
            # Get results for one tech at a time, collapse to long format
            temp = (exist_curt_marg_stor_recovery_ratio[i].reset_index()
                    .melt(id_vars='h', var_name='r'))
            # Define tech and vintage
            temp['i'] = i
            temp['v'] = marg_stor_props.loc[i, 'v']
            # Charging from existing curtailment is in the "old" category
            temp['src'] = 'old'
            # Concatenate these results with the rest
            toadd.append(temp)
    
        # Collect marg curt/marg stor results
        for i in marg_curt_marg_stor_recovery_ratio.keys():
            # Get results for one tech at a time, collapse to long format
            temp = (marg_curt_marg_stor_recovery_ratio[i].reset_index()
                    .melt(id_vars='h', var_name='resource'))
            # Take the average of curt_stor across source
            temp = pd.merge(
                left=i_resource_r_utility, right=temp, on='resource',
                how='right').groupby(['r', 'h', 'src'], as_index=False).mean()
            # Define tech and vintage
            temp['i'] = i
            temp['v'] = marg_stor_props.loc[i, 'v']
            # Concatenate these results with the rest
            toadd.append(temp)
    
        # Concat with existing and marginal storage curtailment results
        curt_stor = pd.concat([curt_stor]+toadd, axis=0, sort=False, ignore_index=True)
    
        # Set the year and organize the columns to match ReEDS
        curt_stor['t'] = str(year)
        curt_stor = curt_stor[['i', 'v', 'r', 'h', 'src', 't', 'value']]
        
        pvb_bat = 'battery_' + SwitchSettings.switches['gsw_pvb_dur']
        curt_pvb = curt_stor[curt_stor['i'] == pvb_bat].copy()
        curt_pvb.index = range(len(curt_pvb))
        curt_pvb.drop('i', axis=1, inplace=True)
        curt_pvb = pd.merge(left=curt_pvb,
                            right=pvb_resources[['i','r','derate']],
                            on='r')
        curt_pvb['value'] *= curt_pvb['derate']
        curt_pvb = curt_pvb[['i', 'v', 'r', 'h', 'src', 't', 'value']]
        curt_stor = pd.concat([curt_stor, curt_pvb], sort=False, ignore_index=True)
        # Remove small numbers and round results
        curt_stor.loc[
            curt_stor['value'] < SwitchSettings.switches['min_val'], 'value'] = 0
        curt_stor['value'] = curt_stor[
                    'value'].round(SwitchSettings.switches['decimals'])
        
    elif SwitchSettings.switches['gsw_storage'] == '0':
        curt_stor = pd.DataFrame(
                columns=['i', 'v', 'r', 'h', 'src', 't', 'value'])
        curt_pvb = pd.DataFrame(
                columns=['i', 'v', 'r', 'h', 'src', 't', 'value'])
        prod_curt_recovery = pd.DataFrame(columns=['r', 'h', 't', 'value'])

    # =========================================================================
    # Calculate recovery of marginal curtailment with marginal DR
    # =========================================================================

    if int(SwitchSettings.switches['gsw_dr']):

        # each resource region is calculated individually, and then the results
        # are averaged across VG type

        marg_curt_marg_dr_recovery_ratio = dict()
        shift_techs = [i for i in dr_inc_local.index.get_level_values(level='i').drop_duplicates()
                    if i in dr_dec_local.index.get_level_values(level='i').drop_duplicates()]
        for i in shift_techs:
            # Get DR profiles, repeated for each resource region
            dr_inc_tmp = dr_inc_local.xs(i, level='i').reset_index(drop=True)
            dr_dec_tmp = dr_dec_local.xs(i, level='i').reset_index(drop=True)

            cols = [c for c in dr_inc_tmp.columns
                    if c in net_load_marg.columns]
            ### Also convert to local to align with marg_curt_h_utility
            net_load_marg_utility_local = adjust_tz(
                df=net_load_marg[cols],
                mapper = resource_r,
                option='ET_to_local'
            )

            # clip marg_curt_local at +/- marg_DR_MW to get the available
            # charge/discharge profile of marginal DR for marginal VRE
            clip_tmp = net_load_marg_utility_local.where(
                net_load_marg_utility_local > -dr_inc_tmp, -dr_inc_tmp)
            poss_dr_changes_marg_local = - clip_tmp.where(
                clip_tmp < dr_dec_tmp, dr_dec_tmp)

            marg_curt_dr = poss_dr_changes_marg_local.where(
                poss_dr_changes_marg_local > 0, 0)
            marg_curt_dr_h = pd.concat([hdtmap_single[['h']], marg_curt_dr],
                                        sort=False, axis=1).groupby('h').sum()

            # Get the marginal curtialment recovery rate for each marginal DR 
            # technology
            marg_curt_marg_dr_recovery_ratio[i] = dr_curt_recovery(
                hrs=marg_dr_props.loc[i, 'hrs'], eff=marg_dr_props.loc[i, 'RTE'],
                ts_length=ts_length, poss_dr_changes=poss_dr_changes_marg_local,
                hdtmap=hdtmap_single, marg_curt_h=marg_curt_dr_h)
        
        # =========================================================================
        # Repeating for marginal DR with existing curtailment
        # =========================================================================

        exist_curt_marg_dr_recovery_ratio = dict()
        ### Use local time since outputs are by timeslice
        # clip net_load_adj at +/- marg_DR_MW to get the available
        # charge/discharge profile of marginal DR with existing VRE
        shift_techs = [i for i in dr_inc_local.index.get_level_values(level='i').drop_duplicates()
                    if i in dr_dec_local.index.get_level_values(level='i').drop_duplicates()]
        for i in shift_techs:
            cols = [c for c in dr_inc_local.columns
                    if c in net_load_marg_utility_local.columns]
            if not cols:
                continue
            dr_inc_tmp = dr_inc_local.xs(i, level='i').reset_index(drop=True)
            dr_dec_tmp = dr_dec_local.xs(i, level='i').reset_index(drop=True)
            clip_tmp = net_load_marg_utility_local[cols].where(
                net_load_marg_utility_local[cols] > -dr_inc_tmp, -dr_inc_tmp)
            poss_dr_changes_margexist_local = - clip_tmp.where(clip_tmp < dr_dec_tmp, dr_dec_tmp)
        
            # Identify total curtailment marginal DR could have recovered so
            # that curtailment recovery is relative to how much marginal DR could
            # have recovered if it was able to recover at a flat MW level
            # "could have recovered" for DR is the availibility to increase load
            # during hours of curtailment, and is just the positive values from above
            curt_region_local = poss_dr_changes_margexist_local.where(
                poss_dr_changes_margexist_local > 0, 0)
            # Get existing curtailment by timeslice
            curt_region_h = pd.concat([hdtmap_single[['h']], curt_region_local], sort=False,
                                    axis=1).groupby('h').sum()

            # Get the existing curtailment recovery rate for marginal DR
            # technology i
            marg_dr_hr = marg_dr_props.loc[i, 'hrs']
            exist_curt_marg_dr_recovery_ratio[i] = dr_curt_recovery(
                hrs=marg_dr_hr, eff=marg_dr_props.loc[i, 'RTE'], ts_length=ts_length,
                poss_dr_changes=poss_dr_changes_margexist_local, 
                hdtmap=hdtmap_single, marg_curt_h=curt_region_h[cols])

        # =========================================================================
        # Calculating ability of existing DR to reduce marginal curtailment
        # =========================================================================

        if cap_dr.size > 0:
            # Reset net load marg
            net_load_marg_utility_local = adjust_tz(
                df=net_load_marg[load_avail_resource_utility.columns],
                mapper = resource_r, option='ET_to_local'
            )

            # Map DR devices to resource_device combinations
            cap_dr_resource_device = pd.merge(
                left=resource_dr_utility[['device', 'resource_device']],
                right=cap_dr, how='right', on='device')

            # expand net_load_marg_utility to include a profile for every utility
            # scale resource-DR device combination
            net_load_marg_resource_dr_utility_local = expand_df(
                df=net_load_marg_utility_local,
                expand=resource_dr_utility[
                    ['resource', 'device', 'r', 'resource_device']],
                old_col='resource', new_col='resource_device',
                drop_cols=['resource', 'device', 'r'])
            # reorder columns to match cap_dr_resource_device
            net_load_marg_resource_dr_utility_local = \
                net_load_marg_resource_dr_utility_local[
                    cap_dr_resource_device['resource_device']]

            # Get existing DR usage in Osprey in same format as above
            dr_inc_osprey = OSPREY_RESULTS['dr_inc'].get_data()
            dr_inc_osprey.i = dr_inc_osprey.i.str.lower()  # Standardize names
            dr_inc_osprey['idx_hr'] = ((dr_inc_osprey.d.str[1:].astype(int) - 1)*24
                                    + dr_inc_osprey.hr.str[2:].astype(int) - 1)
            dr_dec_osprey = OSPREY_RESULTS['gen'].get_data()[resource_dr_utility.device.values]
            dr_dec_osprey = dr_dec_osprey.reset_index().melt(id_vars='idx_hr', var_name='device',
                                                            value_name='Val')

            # Expand DR increase data and subtract off osprey results
            dr_inc_local['idx_hr'] = list(range(0, 8760)) * len(dr_inc_local.index.drop_duplicates())
            dr_inc_local = dr_inc_local.reset_index().set_index('idx_hr')
            dr_inc_tmp = pd.merge(dr_inc_local.melt(id_vars='i', var_name='r'),
                                cap_dr, on=['i', 'r'])
            dr_inc_tmp = pd.merge(dr_inc_tmp, dr_inc_osprey.drop(['d', 'hr'], axis=1),
                                on=['idx_hr', 'i', 'r', 'v'], how='left').fillna(0)
            dr_inc_tmp.loc[:,'value'] = dr_inc_tmp['value']*dr_inc_tmp['MW'] - dr_inc_tmp['Val']
            dr_inc_tmp = dr_inc_tmp.pivot(index='idx_hr',
                                        columns='generator',
                                        values='value').fillna(0)
            dr_inc_tmp = expand_df(
                df=dr_inc_tmp,
                expand=resource_dr_utility[['resource', 'device', 'r', 'resource_device']],
                old_col='device', new_col='resource_device',
                drop_cols=['resource','device','r'])

            # Expand DR decrease data and subtract off osprey results
            dr_dec_tmp = pd.merge(dr_dec_local.reset_index().melt(id_vars='i', var_name='r'),
                                cap_dr, on=['i', 'r'])
            dr_dec_tmp['idx_hr'] = list(range(0, 8760)) * len(cap_dr.i.drop_duplicates())
            dr_dec_tmp = pd.merge(dr_dec_tmp, dr_dec_osprey,
                                on=['idx_hr', 'device'], how='left').fillna(0)
            dr_dec_tmp.loc[:,'value'] = dr_dec_tmp['value']*dr_dec_tmp['MW'] - dr_dec_tmp['Val']
            dr_dec_tmp = dr_dec_tmp.pivot(index='idx_hr',
                                        columns='device',
                                        values='value').fillna(0)
            dr_dec_tmp = expand_df(
                df=dr_dec_tmp,
                expand=resource_dr_utility[['resource', 'device', 'r', 'resource_device']],
                old_col='device', new_col='resource_device',
                drop_cols=['resource','device','r'])

            # clip marg_curt_local at +/- marg_DR_MW to get the available
            # charge/discharge profile of marginal DR for marginal VRE
            clip_tmp = net_load_marg_resource_dr_utility_local.where(
                net_load_marg_resource_dr_utility_local > -dr_inc_tmp, -dr_inc_tmp)
            poss_dr_changes_exist_local = - clip_tmp.where(
                clip_tmp < dr_dec_tmp, dr_dec_tmp)

            curt_resource_dr_utility_local = poss_dr_changes_exist_local.where(
                poss_dr_changes_exist_local > 0, 0)
            curt_resource_dr_utility_h = pd.concat(
                [hdtmap_single[['h']], curt_resource_dr_utility_local],
                sort=False, axis=1
                ).groupby('h').sum()

            marg_dr_hr = marg_dr_props.loc[i, 'hrs']
            marg_curt_exist_dr_recovery_ratio = dr_curt_recovery(
                hrs=marg_dr_hr, eff=marg_dr_props.loc[i, 'RTE'], ts_length=ts_length,
                poss_dr_changes=poss_dr_changes_exist_local, hdtmap=hdtmap_single,
                marg_curt_h=curt_resource_dr_utility_h)
            curt_dr = marg_curt_exist_dr_recovery_ratio.T.reset_index()
        else:
            cap_dr_resource_device = pd.merge(
                left=resource_dr_utility[['device', 'resource_device']],
                right=cap_dr, how='right', on='device')
            curt_dr = pd.DataFrame(data=[0]*len(hdtmap_single['h'].drop_duplicates()),
                                index=hdtmap_single['h'].drop_duplicates()).T.reset_index()

        # DR processing for output
        # Take the average of curt_dr across source and device
        curt_dr = pd.merge(
            left=resource_dr_utility[
                ['src', 'device', 'resource_device']].rename(
                    columns={'resource_device': 'index'}),
            right=curt_dr, on='index')
        curt_dr = curt_dr.groupby(['src', 'device'], as_index=False).mean()
        # Merge in the storage technology and regions
        curt_dr = pd.merge(
            left=cap_dr_resource_device[['i', 'r', 'device']].drop_duplicates(),
            right=curt_dr, on='device', how='right'
        ).drop('device', axis=1)
        # Collapse to long fromat for ReEDS
        curt_dr = curt_dr.melt(id_vars=['i', 'r', 'src'], var_name='h')
        # Merge in the reeds vintages that exist
        curt_dr = pd.merge(left=cap_dr[['i', 'v', 'r']], right=curt_dr,
                        on=['i', 'r'])
        # Reorder columns to match ReEDS convention
        curt_dr = curt_dr[['i', 'v', 'r', 'h', 'src', 'value']]

        # Get the marginal vintage of each storage tech
        ivt = pd.read_csv(os.path.join('inputs_case', 'ivt.csv'), index_col=0)
        ivt = expand_star(ivt)
        for i in marg_stor_props.index:
            marg_stor_props.loc[i, 'v'] = 'new' + str(ivt.loc[i, str(year)])
        ivt = pd.melt(ivt.reset_index(), id_vars='index')
        ivt.rename(columns={'index': 'i', 'variable': 't'}, inplace=True)
        ivt['v'] = 'new' + ivt['value'].astype(str)
        ivt['t'] = pd.to_numeric(ivt['t'])
        # Get the marginal vintage of each DR tech
        for i in [d for d in marg_dr_props.index if d in ivt.i.values]:
            marg_dr_props.loc[i, 'v'] = ivt.loc[(ivt.i==i) & (ivt.t==year),'v'].values[0]

        # Collect exist curt/marg dr results
        for i in exist_curt_marg_dr_recovery_ratio.keys():
            # Get results for one tech at a time, collapse to long format
            temp = (exist_curt_marg_dr_recovery_ratio[i].reset_index()
                    .melt(id_vars='h', var_name='r'))
            # Define tech and vintage
            temp['i'] = i
            temp['v'] = marg_dr_props.loc[i, 'v']
            # Charging from existing curtailment is in the "old" category
            temp['src'] = 'old'
            # Concatenate these results with the rest
            curt_dr = pd.concat([curt_dr, temp], sort=False).reset_index(
                drop=True)

        # Collect marg curt/marg dr results
        for i in marg_curt_marg_dr_recovery_ratio.keys():
            # Get results for one tech at a time, collapse to long format
            temp = (marg_curt_marg_dr_recovery_ratio[i].reset_index()
                    .melt(id_vars='h', var_name='resource'))
            # Take the average of curt_dr across source
            temp = pd.merge(
                left=i_resource_r_utility, right=temp, on='resource',
                how='right').groupby(['r', 'h', 'src'], as_index=False).mean()
            # Define tech and vintage
            temp['i'] = i
            temp['v'] = marg_dr_props.loc[i, 'v']
            # Concatenate these results with the rest
            curt_dr = pd.concat([curt_dr, temp], sort=False).reset_index(
                drop=True)

        # Set the year and organize the columns to match ReEDS
        curt_dr['t'] = str(year)
        curt_dr = curt_dr[['i', 'v', 'r', 'h', 'src', 't', 'value']]
        # Remove small numbers and round results
        curt_dr.loc[curt_dr['value'] < SwitchSettings.switches['min_val'], 'value'] = 0
        curt_dr['value'] = curt_dr['value'].round(SwitchSettings.switches['decimals'])
        # Add in H17
        curt_dr_h17 = curt_dr[curt_dr['h'] == 'h3'].reset_index(drop=True)
        curt_dr_h17['h'] = 'h17'
        curt_dr = pd.concat([curt_dr, curt_dr_h17], sort=False).reset_index(
            drop=True)

    else:
        curt_dr = pd.DataFrame(columns=['i','v','r','h','src','t','value'])


    # =========================================================================
    # Format results for ReEDS
    # =========================================================================

    # Format marginal curtailment results for ReEDS
    curt_marg = curt_ratio_h.reset_index().melt(id_vars='h').rename(
        columns={'variable': 'resource'})
    curt_marg = pd.merge(left=curt_marg, right=resources,
                         on='resource', how='left')
    curt_marg['t'] = SwitchSettings.next_year
    curt_marg = curt_marg[['i', 'r', 'h', 't', 'value']]
    # Marginal curtailment must be a fraction
    curt_marg.loc[curt_marg['value'] > 1, 'value'] = 1
    # Remove small numbers and round results
    curt_marg.loc[curt_marg['value'] < SwitchSettings.switches['min_val'], 'value'] = 0
    curt_marg['value'] = curt_marg['value'].round(SwitchSettings.switches['decimals'])

    ###### Get net load at timeslice resolution for ReEDS
    ### Convert from ET to local first
    net_load_adj_no_curt_h = pd.concat(
        [hdtmap_single[['h']], 
         adjust_tz(
             df=net_load_adj_no_curt, option='ET_to_local')], 
        sort=False, axis=1,
    ).groupby('h').mean()
    ### Reformat for output
    net_load_adj_no_curt_h = pd.melt(
        net_load_adj_no_curt_h.reset_index().round(SwitchSettings.switches['decimals']), 
        id_vars=['h'], var_name='r')
    ### Add year column and reorder
    net_load_adj_no_curt_h['t'] = str(year)
    net_load_adj_no_curt_h = net_load_adj_no_curt_h[['r','h','t','value']].copy()

    ### Store and return results
    mc_results = {
        'curt_stor': curt_stor,
        'curt_dr': curt_dr,
        'curt_marg': curt_marg,
        'curt_tran': curt_tran_h,
        'curt_prod': prod_curt_recovery,
        'net_load_adj_no_curt_h': net_load_adj_no_curt_h,
    }

    #%%
    return mc_results, trans_region_curt
