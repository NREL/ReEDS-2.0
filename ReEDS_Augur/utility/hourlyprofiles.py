# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 19:35:18 2021

@author: afrazier
"""

import os
import itertools
import networkx as nx
import numpy as np
import pandas as pd

from ReEDS_Augur.utility.switchsettings import SwitchSettings
from ReEDS_Augur.utility.functions import adjust_tz, \
    apply_series_to_df, agg_profiles, map_rs_to_r, \
    format_tranloss, format_trancap
#from ReEDS_Augur.utility.generatordata import GEN_DATA
from ReEDS_Augur.utility.inputs import INPUTS


class HourlyProfile(SwitchSettings):
    '''
    Class for handling CF profiles.
    '''

    def __init__(self, *args, **kwargs):
        self.profiles = None

    def get_data(self):
        if self.profiles is None:
            self.profiles = self.format_data()
        return self.profiles


class OspreyGen(HourlyProfile):
    '''
    Formatting Osprey generation results and saving them here.
    '''
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.names = None

    def format_data(self):
        '''
        Formatting generation from Osprey into a convenient format
        '''
        gen = INPUTS['osprey_gen'].get_data(SwitchSettings.prev_year)
        gen.i = gen.i.str.lower()  # Standardize generator names
        gen['idx_hr'] = ((gen.d.str[1:].astype(int) - 1)*24
                         + gen.hr.str[2:].astype(int) - 1)
        gen['generator'] = gen['i'] + gen['v'] + gen['r']
        gen_names = gen[['i', 'v', 'r', 'generator']].drop_duplicates(
                                                        ignore_index = True)
        gen = gen.pivot(index='idx_hr', columns='generator',
                        values='Val').fillna(0)
        gen = gen.reindex(range(SwitchSettings.switches['osprey_ts_length'])
                         ).fillna(0)
        return gen, gen_names
    
    def get_data(self):
        if self.profiles is None:
            self.profiles, self.names = self.format_data()
        return self.profiles.copy(), self.names.copy()
    
    
class OspreyProduce(HourlyProfile):
    '''
    Formatting hourly Produce profiles from Osprey and saving them here
    '''
    
    def format_data(self):
        ts_length = SwitchSettings.switches['osprey_ts_length']
        rfeas = INPUTS['rfeas'].get_data()
        produce = INPUTS['osprey_produce'].get_data(SwitchSettings.prev_year)
        produce['index_hr'] = ((produce.d.str[1:].astype(int) - 1)*24
                                  + produce.hr.str[2:].astype(int) - 1)
        produce = produce.pivot_table(index='index_hr', columns='r',
                                            values='Val', aggfunc='sum')
        produce = produce.reindex(index=np.arange(ts_length),
                                        columns=rfeas['r']).fillna(0)
        
        return produce
        
        
class OspreyRegionFlows(HourlyProfile):
    '''
    Formatting Osprey net region flows and saving them here.
    '''

    def format_data(self):
        '''
        Calculate the net AC and LCC DC transmission flows in/out of each region.
        We leave out VSC DC lines because in the script where we use the output
        of this function (C1_existing_curtailment.py, in the calculation of net
        load), we only need the net AC/DC conversion, not VSC line flows.
        '''
        # Transmission loss rates
        tranloss = format_tranloss()
        tranloss = (
            tranloss
            .assign(path=tranloss.r + '_' + tranloss.rr)
            .assign(transmit=1 - tranloss.tranloss)
            .loc[tranloss.trtype=='AC']
        )
        # Transmission flows
        flows = INPUTS['osprey_flows'].get_data(str(SwitchSettings.prev_year))
        flows = (
            flows
            .assign(path=(flows['r'] + '_' + flows['rr']))
            .assign(index_hr=((flows.d.str[1:].astype(int) - 1) * 24
                              + flows.hr.str[2:].astype(int) - 1))
            .loc[flows.trtype.isin(['AC','LCC','B2B'])]
            .assign(trtype='AC')
            .pivot(index='index_hr', columns='path', values='Val')
            # Reindex to include unused paths
            .reindex(index=np.arange(SwitchSettings.switches['osprey_ts_length']),
                     columns=tranloss['path'])
            .fillna(0)
        )
        # Make sure flows and losses have the same entries
        if not (flows.shape[1] == tranloss.shape[0]):
            print(flows.columns)
            print(tranloss)
            raise Exception('flows {} and tranloss {} have different entries'.format(
                    flows.shape, tranloss.shape))

        # Apply transmission losses only to imports
        imports = flows * tranloss.set_index('path').transmit

        # Get imports and exports by region
        imports = agg_profiles(imports, tranloss[['rr','path']])
        exports = agg_profiles(flows, tranloss[['r','path']])

        # Get the net transmission flows
        region_flows = imports - exports

        return region_flows


class OspreyStorageDispatch(HourlyProfile):
    '''
    Formatting Osprey net storage dispatch and saving it here
    '''
    
    def format_data(self):
        # Storage generation
        ts_length = SwitchSettings.switches['osprey_ts_length']
        techs = INPUTS['i_subsets'].get_data()
        rfeas = INPUTS['rfeas'].get_data()
        df, gen_names = OSPREY_RESULTS['gen'].get_data()
        stor_names = gen_names[gen_names['i'].isin(techs['storage'])]
        df = df[stor_names['generator']]
        df = agg_profiles(df, stor_names[['r', 'generator']])
        df = df.reindex(index=range(ts_length), columns=rfeas['r']).fillna(0)
        # Storage charging
        charge = INPUTS['osprey_charging'].get_data(SwitchSettings.prev_year)
        if len(charge) > 0:
            charge['index_hr'] = ((charge.d.str[1:].astype(int) - 1) * 24
                                + charge.hr.str[2:].astype(int) - 1)
            charge = (
                charge
                .groupby(['index_hr', 'r'], as_index=False).sum()
                ## Keep all columns even if empty
                .reindex(['index_hr','r','Val'], axis=1)
                .pivot(index='index_hr', columns='r', values='Val')
                .reindex(index=range(ts_length), columns=rfeas['r'])
                .fillna(0)
            )
        else:
            charge = 0
        df = df - charge

        return df

class OspreyDRDispatch(HourlyProfile):
    '''
    Formatting Osprey DR dispatch and saving it here
    '''

    def format_data(self):
        gen = INPUTS['osprey_dr'].get_data(SwitchSettings.prev_year)
        gen.i = gen.i.str.lower()  # Standardize generator names
        gen['idx_hr'] = ((gen.d.str[1:].astype(int) - 1)*24
                         + gen.hr.str[2:].astype(int) - 1)
        gen['generator'] = gen['i'] + gen['v'] + gen['r']
        gen = gen.pivot_table(index='idx_hr', columns='r',
                              values='Val', aggfunc='sum').fillna(0)
        gen = gen.reindex(range(SwitchSettings.switches['osprey_ts_length'])
                         ).fillna(0)
        return gen


class OspreyTransRegions(object):
    '''
    Determining the transmission-connected regions and saving
    them here.
    '''

    def __init__(self, *args, **kwargs):
        self.df = None

    def format_data(self, thresh=0.01):
        '''
        Finding the transmission-connected regions which should all have the same
        marginal energy price in the Osprey LP
        '''
        # Lists and counts
        bas = INPUTS['rfeas'].get_data()['r'].tolist()
        n_bas = len(bas)
        index_hr_map = INPUTS['index_hr_map'].get_data()
        hour_day_map = index_hr_map[['idx_hr', 'd']].drop_duplicates()
        index_hrs = list(hour_day_map['idx_hr'].drop_duplicates())
        n_hours = SwitchSettings.switches['osprey_ts_length']

        # Each region-hour gets a unique index (rh_idx). We can't just use the
        # pXX values, because then networkx would connect regions across time.
        r2int = dict(zip(bas, range(len(bas))))
        rh_idx_map = pd.DataFrame(itertools.product(bas, index_hrs),
                                  columns=['r', 'idx_hr'])
        rh_idx_map['rh_idx'] = (n_hours*(rh_idx_map['r'].map(r2int))
                                + rh_idx_map['idx_hr'])

        ### If using the VSC macrogrid, each region-hour gets a node in both the AC and
        ### VSC DC networks. VSC converters represent links between the two networks:
        ###     p1    p2    p3    p4    <-- ReEDS BAs
        ###     ---------------------   v-- Network node labels (showing a single hour)
        ###     1DC - 2DC - 3DC   4DC   <-- VSC DC links with spare capacity
        ###      |           |          <-- VSC converters with spare capacity
        ###     1AC - 2AC   3AC - 4AC   <-- AC links with spare capacity

        flows_uncapped_trtype = {}
        for trtype in ['AC','VSC']:
            # Get total flows
            flows = INPUTS['osprey_flows'].get_data(SwitchSettings.prev_year)
            flows = (
                flows.loc[flows.trtype==trtype].drop('trtype', axis=1)
                .reset_index(drop=True))

            # Get transmission capacity
            trancap = format_trancap()
            trancap = (
                trancap.loc[trancap.trtype==trtype].drop('trtype', axis=1)
                .reset_index(drop=True))

            # Get uncapped flows for D_Condor
            df = trancap.merge(flows, on=['r', 'rr'])
            idx = (df['MW'] - abs(df['Val'])) > thresh
            flows_uncapped_trtype[trtype] = (
                flows[idx].drop('Val', axis=1)
                # Merge the unique rh_idx onto both the source and destination
                .merge(index_hr_map, on=['d', 'hr'], how='left')
                .merge(rh_idx_map
                       .assign(rh_idx=rh_idx_map.rh_idx.astype(str)+trtype),
                       on=['r', 'idx_hr'], how='left')
                .rename(columns={'rh_idx': 'rh_source_idx'})
                .merge(rh_idx_map
                       .assign(rh_idx=rh_idx_map.rh_idx.astype(str)+trtype)
                       .rename(columns={'r':'rr'}),
                       on=['rr','idx_hr'], how='left')
                .rename(columns={'rh_idx': 'rh_dest_idx'})
            )

        ###### Uncongested VSC AC/DC converters create links between the AC and VSC DC networks
        ### Get total conversion
        conversion = INPUTS['osprey_conversion'].get_data(str(SwitchSettings.prev_year))
        if not len(conversion):
            cap_remaining = pd.DataFrame(columns=flows_uncapped_trtype['AC'].columns)
        else:
            conversion = (
                conversion
                ### Sum over AC->VSC and VSC->AC conversion since both can occur in one hour
                .groupby(['d','hr','r']).Val.sum().round(3).unstack('r')
            )
            conversion.index = conversion.index.map(index_hr_map.set_index(['d','hr']).idx_hr)

            cap_converter = INPUTS['cap_converter'].get_data().set_index('r').MW.round(3)

            cap_remaining = (
                ((cap_converter - conversion).stack() > thresh)
                .reset_index().rename(columns={'level_0':'idx_hr', 0: 'cap_remaining'})
            )
            cap_remaining = (
                cap_remaining
                .assign(rr=cap_remaining.r)
                # Merge the unique rh_idx onto both the source and destination
                .merge(index_hr_map, on='idx_hr', how='left')
                ### First do AC->VSC for each uncongested converter
                .merge(rh_idx_map
                       .assign(rh_idx=rh_idx_map.rh_idx.astype(str)+'AC'),
                       on=['r','idx_hr'], how='left').rename(columns={'rh_idx': 'rh_source_idx'})
                .merge(rh_idx_map
                       .assign(rh_idx=rh_idx_map.rh_idx.astype(str)+'VSC'),
                       on=['r','idx_hr'], how='left').rename(columns={'rh_idx': 'rh_dest_idx'})
                .loc[cap_remaining.cap_remaining].drop('cap_remaining', axis=1)
            )

        flows_uncapped = pd.concat(
            ### Include the VSC AC/DC links in the graph edges
            {**flows_uncapped_trtype, 'ACDC':cap_remaining,},
            axis=0, ignore_index=True)

        # Find all transmission-connected regions
        flows_uncapped['pairs'] = tuple(zip(list(flows_uncapped['rh_source_idx']),
                                            list(flows_uncapped['rh_dest_idx'])))
        graph = nx.from_edgelist(list(flows_uncapped['pairs']))
        connected = list(nx.connected_components(graph))

        # Reformatting the transmission-connected regions for later use.
        # "subset" because it only includes regions that have connections:
        # It's full if BAs have uncapped tranmsmission available to anywhere
        trans_region_map_subset = np.empty([n_hours*n_bas*2, 2], dtype='<U16')
        counter = 0
        for trans_region in range(len(connected)):
            ### Only nodes in the AC network matter for ultimate injection/withdrawal.
            ### If we kept the VSC nodes, we could end up with the following situation,
            ### in which p1 and p3 would NOT be connected:
            ###     p1    p2    p3 
            ###     ---------------
            ###     1DC - 2DC - 3DC
            ###      |
            ###     1AC - 2AC   3AC
            region_conns = [x for x in connected[trans_region] if x.endswith('AC')]
            n_conns = len(region_conns)
            trans_region_map_subset[counter:counter+n_conns, 0] = region_conns
            trans_region_map_subset[counter:counter+n_conns, 1] = trans_region
            counter = counter + n_conns

        trmap_subset = pd.DataFrame(
            trans_region_map_subset[:counter, :],
            columns=['rh_idx', 'trans_region'],
        ).astype({'trans_region':int})
        trmap_subset = (
            trmap_subset
            ### Drop the AC/VSC info; all we need is (region,hour)
            .assign(rh_idx=trmap_subset.rh_idx.str.rstrip('AC').astype(int))
            .drop_duplicates()
            .merge(rh_idx_map, on='rh_idx', how='left')
        )

        trmap = pd.DataFrame(itertools.product(bas, index_hrs),
                             columns=['r', 'idx_hr'])
        trmap = trmap.merge(
            trmap_subset[['r', 'idx_hr', 'trans_region']],
            on=['r', 'idx_hr'], how='left')

        trmap['trans_region_unique'] = np.arange(
            trmap['trans_region'].max(),
            trmap['trans_region'].max() + len(trmap))

        trmap['trans_region'] = np.where(
            trmap['trans_region'].isnull(),
            trmap['trans_region_unique'],
            trmap['trans_region'])

        trmap = trmap.drop('trans_region_unique', axis=1)

        return trmap

    def get_data(self):
        if self.df is None:
            self.df = self.format_data()
        return self.df


class Profile(HourlyProfile):
    '''
    Generic class for profiles to be formatted later on
    '''
    
    def format_profiles(self, *args, **kwargs):
        pass


class LoadProfile(HourlyProfile):
    '''
    Handling properties specific to load profiles.
    '''
    
    def add_can_exports(self, df, *args, **kwargs):
        '''
        Adding canadian exports to load
        '''
        h_map = INPUTS['h_dt_szn'].get_data()
        # If allyearload is used, map to just one year
        if (
            (self.switches['gsw_efs1_allyearload'] != 'default')
            and ('EER' not in self.switches['gsw_efs1_allyearload'])
        ):
            h_map = h_map[h_map['year'] == min(h_map['year'])]
        
        # h17, default representation for canadian export consideration
        if self.switches['gsw_canada'] == '1':
            print("Adjusting net load by Canadian exports given Sw_Canada = 1")
            can_exports = INPUTS['can_exports'].get_data()
            if not can_exports.empty:
                can_exports = can_exports.pivot(index = 'h', columns = 'r', 
                                                                values = 'MW')
                can_exports = can_exports.reindex(index = h_map['h'],
                                                  columns = df.columns).fillna(0)
                # Reindex so profiles can be added together
                can_exports.index = range(len(can_exports))
            
                df += can_exports
        
        #with exogenous trade, load in the 8760 trade data for canada by BA and adjust load accordingly
        if self.switches['gsw_canada'] == '2':
            # load in the 8760 trade data
            can_trade = INPUTS['can_trade_8760'].get_data().astype({'r':str,'hours':str})
            if not can_trade.empty:
                can_trade = can_trade[can_trade['t'] == self.next_year]
                can_trade['hours'] = can_trade['hours'].str.replace('h','').astype('int') - 1
                #format for adding/substracting to df
                can_trade = can_trade.pivot(index='hours', columns='r', 
                                            values='MW').reset_index().fillna(0)
                can_trade = can_trade.drop(columns=['hours']).reset_index(drop=True)
                # stack the can_trade dataset 7 times to make sure we're able to fill
                # in all hours related to load and that indices align
                ct_all = pd.concat([can_trade.copy()]*7, axis=0).reset_index(drop=True)

                #add columns that are in df but not in ct_all
                ct_all = ct_all.reindex(index=ct_all.index, 
                                        columns=df.columns).fillna(0)            

                df += ct_all

        return df

    def adjust_flex_load(self, df):
        '''
        Adjusting load profiles for flexible load
        '''
        flex_load = INPUTS['flex_load'].get_data()
        flex_load_opt = INPUTS['flex_load_opt'].get_data()
        h_map = INPUTS['h_dt_szn'].get_data()
        # If using yearly profiles then do this for a single year
        if (
            (SwitchSettings.switches['gsw_efs1_allyearload'] != 'default')
            and ('EER' not in SwitchSettings.switches['gsw_efs1_allyearload'])
        ):
            h_map = h_map[h_map['year'] == min(h_map['year'])]
    
        for r in df.columns:
    
            load_profiles_temp = df[[r]].reset_index()
            load_profiles_temp = pd.concat([h_map[['h']],
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
            df[r] += load_profiles_temp['opt'] - load_profiles_temp['exog']
    
        return df
    
    def apply_load_multiplier(self, df, *args, **kwargs):
        '''
        Applying load multiplier
        '''
        hierarchy = INPUTS['hierarchy'].get_data()
        r_cendiv = hierarchy[['r','cendiv']].drop_duplicates(
                                                    ignore_index = True)
        load_mult = INPUTS['load_multiplier'].get_data()
        load_mult = r_cendiv.merge(load_mult, on = 'cendiv')
        df = apply_series_to_df(df, load_mult[['r','load_mult']], 'multiply')
        return df
    
    def format_profiles(self, *args, **kwargs):
        '''
        Formatting load profiles based on the switch settings used in ReEDS.
        '''
        # If not using climate demand, grab the normal load profiles
        if self.switches['gsw_climatedemand'] == '0':
            df = INPUTS['load_profiles'].get_data()
        # If using climate demand, grab the proper load profiles
        elif self.switches['gsw_efs1_allyearload'] == 'default':
            df = INPUTS['load_climate_sevenyears'].get_data(
                self.next_year if SwitchSettings.switches['osprey_load_year'] == 'next'
                else self.prev_year)
        elif self.switches['gsw_efs1_allyearload'] != 'default':
            df = INPUTS['load_climate_allyears'].get_data()

        # Scale load unless load is specified for all years
        if self.switches['gsw_efs1_allyearload'] == 'default' and \
            self.switches['gsw_climatedemand'] == '0':
            df = self.apply_load_multiplier(df)

        # Apply the load flexibility solution from ReEDS
        if SwitchSettings.switches['gsw_efs_flex'] != '0':
            df = self.adjust_flex_load(df)
        df = self.add_can_exports(df)
        df = adjust_tz(df)
        df = df.round(self.switches['decimals'])
        # Duplicate load profiles for 7 years if load is specified for all
        # years (which implies there is not 7 years of load data to use)
        if (
            (SwitchSettings.switches['gsw_efs1_allyearload'] != 'default')
            and ('EER' not in SwitchSettings.switches['gsw_efs1_allyearload'])
        ):
            h_map = INPUTS['h_dt_szn'].get_data()
            numyears = len(h_map['year'].drop_duplicates())
            temp = df.copy()
            for i in range(numyears-1):
                df = pd.concat([df, temp], sort = False, ignore_index = True)
        ### Add (szn,year,h,hour) index
        hdtmap_index = (
            INPUTS['h_dt_szn'].get_data()
            .set_index(['season','year','h','hour']).index)
        df.index = hdtmap_index

        self.profiles = df
        
        
class NetLoadProfile(HourlyProfile):
    '''
    Net load cannot be calculated until we have VRE CFs, and VRE CFs cannot be
    calculated until we have wind profiles, so net load is calculated later
    when the "calculate_net_load" function is called.
    '''
    
    def format_profiles(self, *args, **kwargs):
        pass
        
        
class VREProfile(HourlyProfile):
    '''
    Wind and PV profiles are read in from the same file but separated here so 
    that wind profiles can efficiently be used to scale the wind capacity
    factor adjustments.
    '''
    
    def format_profiles(self, *args, **kwargs):
        if (
            (HOURLY_PROFILES['pv'].profiles is None)
            or (HOURLY_PROFILES['wind'].profiles is None)
            or (HOURLY_PROFILES['pvb'].profiles is None)
            or (HOURLY_PROFILES['csp'].profiles is None)
        ):
            ### Load additional inputs
            hdtmap_index = (
                INPUTS['h_dt_szn'].get_data()
                .set_index(['season','year','h','hour']).index)
            resources = INPUTS['resources'].get_data()
            r_resource = map_rs_to_r(resources)[['r','resource']]
            techs = INPUTS['i_subsets'].get_data()

            ### Load profiles
            df = INPUTS['vre_profiles'].get_data()
            df = adjust_tz(df, mapper = r_resource)

            ### Subset to modeled regions
            for tech in ['pv','wind','pvb','csp']:
                resources_tech = resources[resources['i'].isin(techs[tech])]
                df_tech = df[resources_tech['resource'].drop_duplicates()]
                ### Add (szn,year,h,hour) index
                df_tech.index = hdtmap_index
                ### Store the profile
                HOURLY_PROFILES[tech].profiles = df_tech


class DRProfile(HourlyProfile):
    '''
    DR data
    '''

    def __init__(self, direction, *args, **kwargs):
        super().__init__()
        if direction not in ['inc', 'dec']:
            raise ValueError("DRProfile direction must be one of 'inc' or 'dec'")
        self.prof_type = 'dr_{}'.format(direction)

    def format_profiles(self, *args, **kwargs):
        if HOURLY_PROFILES[self.prof_type].profiles is None:
            df = INPUTS[self.prof_type].get_data()
            # Identify columns in the model that also have DR
            rfeas = INPUTS['rfeas'].get_data()
            cols = [c for c in df.columns if c in list(rfeas['r'].values)]
            if cols:
                df = df[['i', 'hour']+cols]
            else:
                # Make a column for first r in rfeas; fill with zero as there is no DR
                df = df.reindex(
                    ['i','hour']+INPUTS['rfeas'].get_data().r.tolist()[:1], axis=1,
                ).fillna(0)
            # ## Add (szn,year,h,hour) index, set year = 2012 as that's the DR data year
            df = pd.merge(df, INPUTS['h_dt_szn'].get_data(), on=['hour'])
            df['year'] = 2012
            df.set_index(['season', 'year', 'h', 'hour'], inplace=True)

            HOURLY_PROFILES[self.prof_type].profiles = \
                df.round(SwitchSettings.switches['decimals'])


def calculate_vre_gen(profiles, cfs_exist, cfs_marg):
    '''
    Calculating VRE generation and using this information to get:
        - VRE generation by resource
        - Marginal VRE CF profiles
        - VRE generation by region
        - net_load by region
    All of these results are stored for later use.
    '''
    vre_gen = pd.concat([
        profiles['pv'].profiles,
        profiles['pvb'].profiles,
        profiles['wind'].profiles,
        profiles['csp'].profiles,
    ], axis = 1)
    ### vre_gen[dt x resources] * cfs_marg[resources]
    vre_cf_marg = (
        vre_gen 
        * cfs_marg.groupby('resource').cf_marg.mean()
    ).fillna(0)
    ### vre_gen[dt x resources] * cfs_exist[resources]
    vre_gen = (
        vre_gen 
        * cfs_exist.groupby('resource').MW.sum()
    ).fillna(0)

    r_resource = map_rs_to_r(cfs_exist)[['r','resource']]
    vre_gen_r = (
        vre_gen
        ### Map resources to BA regions
        .rename(columns=r_resource.set_index('resource').r.to_dict())
        ### Profiles that are in vre_gen but not in r_resource will not be mapped
        ### to BA regions, so downselect to the profiles that are mapped to BA
        ### regions (i.e. the resources that are present in r_resource)
        [sorted(r_resource.r.unique())]
        ### Sum over BA regions, giving vre_gen_r[dt x rb]
        .sum(axis=1, level=0)
    )
    # Round profiles
    vre_gen = vre_gen.round(SwitchSettings.switches['decimals'])
    vre_cf_marg = vre_cf_marg.round(SwitchSettings.switches['decimals'])
    vre_gen_r = vre_gen_r.round(SwitchSettings.switches['decimals'])
    # Save hourly profiles for further use
    HOURLY_PROFILES['vre_gen_r'].profiles = vre_gen_r
    HOURLY_PROFILES['vre_gen'].profiles = vre_gen.astype(np.float32)
    HOURLY_PROFILES['vre_cf_marg'].profiles = vre_cf_marg.astype(np.float32)

def format_marg_dr(profiles):
    '''
    Reformat the DR profiles for marginal analysis
    DR profiles are already
    '''
    techs = INPUTS['i_subsets'].get_data()
    resources = INPUTS['resources'].get_data()
    i_resource_r = map_rs_to_r(resources)[['i', 'resource', 'r']].drop_duplicates()
    # filter for utility-scale resources and distributed resources seperately
    i_resource_r_utility = i_resource_r[i_resource_r['i'].isin(
        techs['vre_utility']+techs['pvb'])].reset_index(drop=True)
    resource_r_dr = (i_resource_r_utility[['resource','r']].drop_duplicates()
        .set_index('resource')['r'])

    # format DR inc and dec
    for d in ['dr_inc', 'dr_dec']:
        rdr_idx = [i for i, x in enumerate(resource_r_dr.values)
                   if x in profiles[d].profiles.columns]
        # Get DR profiles, repeated for each resource region
        df = (
            profiles[d].profiles
            .reset_index()
            .drop(columns=['season', 'year', 'h'])
            .set_index(['hour', 'i'])
            )
        df = df*SwitchSettings.switches['marg_dr_mw']
        df = df[resource_r_dr.iloc[rdr_idx].values]
        df.columns = resource_r_dr.index[rdr_idx]
        HOURLY_PROFILES['{}_marg'.format(d)].profiles = df


def format_mustrun(avail):
    '''
    Formatting mustrun generation for net load. This includes:
        - non-dispatchable hydro
        - geothermal
        - nuclear
    '''
    # Format mustrun generation
    rfeas = INPUTS['rfeas'].get_data()
    techs = INPUTS['i_subsets'].get_data()
    must_sets = SwitchSettings.switches['mustrun_techs']
    imust = []
    for must_set in must_sets:
        imust += techs[must_set]
    mustrun = avail[avail['i'].isin(imust)]
    ### If making intermediate plots, save the tech-disaggregated capacities
    if SwitchSettings.switches['plots']:
        mustrun.to_hdf(
            os.path.join('ReEDS_Augur','augur_data',
                         'plot_mustrun_{}.h5'.format(SwitchSettings.prev_year)),
            key='data', complevel=4, format='table')
    ### Sum over all mustrun technologies
    mustrun = mustrun.groupby(['r', 'szn'], as_index=False).sum()
    mustrun = mustrun.pivot(index='szn',
                            columns='r',
                            values='MW').reset_index()
    h_map = INPUTS['h_dt_szn'].get_data()
    h_map.rename(columns={'season':'szn'}, inplace=True)
    h_map['szn'].replace('winter', 'wint', inplace=True)
    h_map['szn'].replace('summer', 'summ', inplace=True)
    h_map['szn'].replace('spring', 'spri', inplace=True)
    mustrun = pd.merge(left=mustrun,
                       right=h_map[['szn']],
                       on='szn')
    mustrun.drop('szn', axis=1, inplace=True)
    mustrun = mustrun.reindex(columns=rfeas['r']).fillna(0)
    ### Add (szn,year,h,hour) index
    hdtmap_index = (
        INPUTS['h_dt_szn'].get_data()
        .set_index(['season','year','h','hour']).index)
    mustrun.index = hdtmap_index

    HOURLY_PROFILES['mustrun'].profiles = mustrun

    avail = avail[~avail['i'].isin(imust)]
    avail.index = range(len(avail))
    
    return avail

# Dictionary where each entry corresponds to a set of hourly profiles
# that are used somewhere in Augur.
# NOTE that all profiles stored here are in EASTERN TIME!!!
HOURLY_PROFILES = {
    'dr_inc':           DRProfile('inc'),
    'dr_inc_marg':      Profile(),
    'dr_dec':           DRProfile('dec'),
    'dr_dec_marg':      Profile(),
    'csp':              VREProfile(),
    'load':             LoadProfile(),
    'mustrun':          Profile(),
    'net_load_osprey':  Profile(),
    'prod_noflex':      Profile(),
    'pv':               VREProfile(),
    'pvb':              VREProfile(),
    'vre_gen':          Profile(),
    'vre_cf_marg':      Profile(),
    'vre_gen_r':        Profile(),
    'wind':             VREProfile()
}
# Dictionary where each entry corresponds to a set of hourly profiles
# that come from the Osprey results and are used somewhere in Augur.
# NOTE that all profiles stored here are in EASTERN TIME!!!
OSPREY_RESULTS = {
    'gen':                  OspreyGen(),
    'dr_inc':               OspreyDRDispatch(),
    'produce':              OspreyProduce(),
    'region_flows':         OspreyRegionFlows(),
    'storage_dispatch_r':   OspreyStorageDispatch(),
    'trans_regions':        OspreyTransRegions(),
}
