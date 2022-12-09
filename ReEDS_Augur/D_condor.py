# -*- coding: utf-8 -*-
"""
Created on Sun Jan 19 13:29:06 2020

This file calculates the energy arbitrage revenue for marginal storage
additions. It uses the regional hourly price profiles from Osprey with an
adjustment for start costs. To adjust for start costs, each generator is
assumed to have a bid price equal to its marginal operating cost. If a
generator turned on during a day, its fractional start cost for that day is
determined and applied uniformly across its generation for that day. These bid
profiles (adjusted for start costs) are compared to the regional price
profiles from Osprey. For each hour in each region, we check to see if there
is a start cost adjusted bid price that is higher than the energy price from
Osprey that is connected to the region via transmission lines with no
congestion. If there is, then the energy price for that hour in that region
is replaced with the bid price from the most expensive transmission-connected
generator. Energy revenue is calculated using Condor, a dynamic program
dispatch algorithm. Revenue can be calculated for each storage technology, or
for a single technology with the others interpolated from that result (this is
the default).

@author: pgagnon
"""

import numpy as np
import os
import pandas as pd

from ReEDS_Augur.utility.functions import filter_data_year, get_storage_eff, \
    get_prop
from ReEDS_Augur.utility.generatordata import GEN_DATA
from ReEDS_Augur.utility.hourlyprofiles import HOURLY_PROFILES, OSPREY_RESULTS
from ReEDS_Augur.utility.inputs import INPUTS
from ReEDS_Augur.utility.switchsettings import SwitchSettings


#%%
def get_marginal_storage_value(trans_region_curt):
    '''
    This function performs a simulated storage dispatch
    '''
    #%% Bypass this calculation if Augur curtailment is turned off,
    ### if arbitrage value is completely derated,
    ### or if storage is turned off
    if ((not int(SwitchSettings.switches['gsw_augurcurtailment']))
        or (not float(SwitchSettings.switches['gsw_storagearbitragemult']))
        or (not int(SwitchSettings.switches['gsw_storage']))
    ):
        return {'hourly_arbitrage_value': pd.DataFrame(columns=['i','r','t','revenue'])}

    # Default efficiency value for Condor
    eta_discharge = SwitchSettings.switches['condor_discharge_eff']
    # List of technology types that are considered when adjusting price
    #   profiles for start costs
    keep_techs = SwitchSettings.switches['condor_keep_techs']

    techs = INPUTS['i_subsets'].get_data()
    techs_to_keep = []
    for t in keep_techs:
        techs_to_keep += techs[t.lower()]

    # Results from Condor are adjusted for when it charges storage from
    # curtailment. The potential for marginal storage to charge from
    # curtailment is captured in C2_marginal_curtailment, and the value of
    # this is captured in ReEDS.
    df_curt = trans_region_curt.reset_index(drop=True)

    # Generation
    gen, gen_names = OSPREY_RESULTS['gen'].get_data()
    gen_names = gen_names[gen_names['i'].isin(techs_to_keep)]
    gen = gen[gen_names['generator']]

    # Prices
    prices = INPUTS['osprey_prices'].get_data(SwitchSettings.prev_year)
    prices['idx_hr'] = ((prices.d.str[1:].astype(int) - 1)*24
                        + prices.hr.str[2:].astype(int) - 1)
    prices = prices.rename(columns={'Val': 'price_org'})
    prices.loc[prices['price_org'] < 0.001, 'price_org'] = 0

    # Get the transmission connected regions
    trans_region_map_df = OSPREY_RESULTS['trans_regions'].get_data()

    # Lists and counts
    index_hr_map = pd.read_csv(os.path.join('inputs_case', 'index_hr_map.csv'))
    hour_day_map = index_hr_map[['idx_hr', 'd']].drop_duplicates()

    #% Import generator characteristics

    generator_data = pd.read_csv(
        os.path.join('inputs_case', 'hourly_operational_characteristics.csv'))
    generator_data = generator_data.rename(
        columns={'Start Cost/capacity': 'start_cost_per_MW',
                    'category': 'i', 'Min Stable Level/capacity': 'mingen_f'})
    generator_df = pd.merge(left=gen_names,
                            right=generator_data[['i', 'start_cost_per_MW']],
                            on='i', how='left')

    # Module works better when all generators are assigned CT startup costs
    idx = generator_data['i'] == 'gas-ct'
    ct_start_cost_per_MW = float(generator_data[idx]['start_cost_per_MW'])
    generator_df['start_cost_per_MW'] = ct_start_cost_per_MW

    # Ingest and merge each generator's operating cost onto generator_df
    op_costs = GEN_DATA['gen_cost'].copy().rename(columns = {'gen_cost':'op_cost'})
    op_costs['generator'] = op_costs['i'] + op_costs['v'] + op_costs['r']
    generator_df = generator_df.merge(op_costs[['generator', 'op_cost']],
                                        on='generator')

    # Create arrays for broadcasting later
    startup_costs_perMW = generator_df.set_index('generator')
    startup_costs_perMW = startup_costs_perMW['start_cost_per_MW']
    op_costs_lookup = generator_df.set_index('generator')['op_cost']

    #% Modify LP prices to get price spikes

    # Generation
    gen = gen.merge(hour_day_map, on='idx_hr', how='left')

    # Get max, min, and total gen by day
    gen_maxes = gen[gen_names['generator'].tolist()+['d']].groupby('d').max(
        ).fillna(0)
    gen_mins = gen[gen_names['generator'].tolist()+['d']].groupby('d').min(
        ).fillna(0)
    gen_sums = gen[gen_names['generator'].tolist()+['d']].groupby('d').sum(
        ).fillna(0)

    # Convert back to long format, which works better since there are so
    #   many transmission regions.
    gen = gen.melt(id_vars=['idx_hr', 'd']).rename(
        columns={'variable': 'generator'})
    gen = pd.merge(left=gen_names[['r', 'generator']], right=gen,
                    on='generator', how='right')
    gen = gen[gen['value'] > 0].reset_index(drop=True)

    startup_bool = gen_mins == 0.0
    startup_bool = startup_bool.astype(int)

    # Only apply start costs to the fraction of the unit that starts up.
    gen_starts = (gen_maxes - gen_mins) * startup_bool
    startup_expenditures = gen_starts * \
                            startup_costs_perMW.reindex(gen_starts.columns)

    # Spread out total start cost ($) over the sum of the generation that day
    startup_costs_perMWh = startup_expenditures / gen_sums
    startup_costs_perMWh = startup_costs_perMWh.fillna(0.0)

    # Each generator's "bid price" is its operating cost plus the amount to
    #   recover the startup cost for that day
    bid_prices = \
        startup_costs_perMWh + \
        op_costs_lookup.reindex(startup_costs_perMWh.columns)
    bid_prices = bid_prices.reset_index()
    bid_prices_long = bid_prices.melt(id_vars='d', value_name='bid_price',
                                        var_name='generator')

    # Find the maximum price price of all generators generating in each
    #   transmission region each hour
    gen = gen.merge(bid_prices_long, on=['d', 'generator'], how='left')
    gen = gen.merge(trans_region_map_df[['idx_hr', 'r', 'trans_region']],
                    on=['idx_hr', 'r'], how='left')
    bid_price_maxes = gen[['trans_region', 'bid_price']].groupby(
        by=['trans_region'], as_index=False).max()

    # Merge on the maximum bid price within each transmission region. The new
    #   price is the maximum of either the LP's price or the bid price.
    prices = prices.merge(trans_region_map_df[['idx_hr', 'r', 'trans_region']],
                            on=['idx_hr', 'r'], how='left')
    prices = prices.merge(bid_price_maxes[['trans_region', 'bid_price']],
                            on=['trans_region'], how='left')
    prices['bid_price'].fillna(0.0, inplace=True)
    prices['price_startup'] = np.max(prices[['bid_price', 'price_org']],
                                        axis=1)

    prices_pivot = pd.DataFrame(columns=['idx_hr'],
                                data=index_hr_map['idx_hr'].values)
    prices_pivot = pd.merge(left=prices_pivot, right=prices.pivot(
        index='idx_hr', columns='r', values='price_startup'),
        on='idx_hr', how='left').fillna(0)
    prices_pivot = prices_pivot.set_index('idx_hr')
    ### Write the final prices for plots if necessary
    if SwitchSettings.switches['plots']:
        prices_pivot.to_hdf(
            os.path.join(
                'ReEDS_Augur','augur_data',
                'plot_prices_condor_{}.h5'.format(SwitchSettings.prev_year)),
            key='data', complevel=4)

    # Initialize empty data frame for storing the results
    df_results = pd.DataFrame(columns=['i', 'r', 't', 'revenue'])
    df_results_pvb = pd.DataFrame(columns=['i', 'r', 't', 'revenue'])

    # These are the storage technologies to compute the marginal arbitrage
    #   revenue of
    # marg_stor_techs = condor_data['marg_stor_techs'].copy()# Get storage capital costs
    marg_storage_props = get_storage_eff()
    marg_storage_props.i = marg_storage_props.i.str.lower()
    marg_storage_props.rename(columns={'RTE': 'rte'}, inplace=True)
    # Filter out CSP
    marg_storage_props = marg_storage_props[
            marg_storage_props['i'].isin(techs['storage_standalone'])]
    marg_storage_props.index = range(0,len(marg_storage_props))
    # Merge in duration by i
    marg_storage_props = get_prop(marg_storage_props, 'storage_duration', merge_cols = ['i'])
    rsc_cost = INPUTS['rsc_dat'].get_data()
    cost_cap = INPUTS['cost_cap'].get_data().rename(
                                            columns = {'cost_cap':'Value'})
    
    pvf = INPUTS['pvf_onm'].get_data()
    # Note the capital cost multipliers are indexed by valinv
    cost_cap_mult = INPUTS['cost_cap_fin_mult'].get_data()

    # Get the most expensive supply curve bin
    rsc_cost = rsc_cost[['i', 'r', 'Value']].groupby(['i', 'r'], as_index=False).max()
    # Merge in capital cost multipliers
    rsc_cost = pd.merge(left=rsc_cost,
                        right=cost_cap_mult,
                        on=['i', 'r'],
                        how='left')
    rsc_cost['t'].fillna(SwitchSettings.next_year, inplace=True)
    rsc_cost['t'] = rsc_cost['t'].astype(int)
    rsc_cost['fin_mult'].fillna(1, inplace=True)
    
    cost_cap = pd.merge(left=cost_cap,
                        right=cost_cap_mult,
                        on=['i', 't'],
                        how='inner')
    
    marg_stor_techs = pd.concat([rsc_cost, cost_cap],
                                sort=False).reset_index(drop=True)
    # Merge in PVF
    marg_stor_techs = pd.merge(left=marg_stor_techs,
                                right=pvf,
                                on='t',
                                how='left')
    
    # Multiply capital cost by regional capital cost multipliers
    marg_stor_techs['Value'] *= marg_stor_techs['fin_mult']
    # Divide by PVF
    marg_stor_techs['Value'] /= marg_stor_techs['pvf']
    marg_stor_techs.drop(['fin_mult', 'pvf'], axis=1, inplace=True)
    marg_stor_techs = pd.merge(left=marg_stor_techs,
                                right=marg_storage_props,
                                on='i',
                                how='left')
    marg_stor_techs.rename(columns={'Value': 'cost'}, inplace=True)
    marg_stor_techs_save = marg_stor_techs.copy()
    marg_stor_techs_save['t'] = marg_stor_techs_save['t'].astype(str)
    
    # This number determines the resolution of Condor
    condor_res = SwitchSettings.switches['condor_res']
    
    # Add appropriate resolution ('res') column and values to the dataframe
    if marg_stor_techs.empty:
        marg_stor_techs['res'] = None # Needs this column still
    else:
        # Modify marg_stor_techs to have the appropriate 'res' column
        #   Can add in A_prep_data.py so it's in condor_inputs...
        condor_res_method = SwitchSettings.switches['condor_res_method']
        if condor_res_method == 'equal':
            # equal: condor_res is the resolution for all storage techs
            marg_stor_techs['res'] = int(condor_res)
        elif condor_res_method == 'scaled':
            # scaled: condor_res is the resolution for battery_2; get the
            #   resolution for remaining techs by scaling up using duration
            #   relative to battery_2
            i_duration = INPUTS['storage_duration'].get_data()
            i_duration = i_duration[i_duration['i'].isin(techs['storage_standalone'])]
            i_duration = i_duration.sort_values(by='duration').set_index('i')
            i_duration.duration -= (SwitchSettings.switches['reedscc_stor_buffer']/60)
            res = i_duration.copy()
            res['scale'] = i_duration.divide(i_duration.duration.iloc[0], 
                axis=0)
            res['res'] = res.scale * condor_res
            res.res = res.res.astype(int) # Condor resolution must be an integer
            res = res.reset_index()
            i_res_map = dict(zip(res.i, res.res))
            marg_stor_techs['res'] = marg_stor_techs.i.map(i_res_map)
        else:
            print('ERROR: options for condor_res_method are equal or scaled')

    # If we are interpolating data for the remaining durations:
    if not SwitchSettings.switches['condor_stor_techs'] == 'all':
        i_data = ['battery_4', 'battery_8']
        has4 = (marg_stor_techs.i == i_data[0]).any()
        has8 = (marg_stor_techs.i == i_data[1]).any()
        if (has4 & has8):  # Needs to have both of these techs to interpolate
            marg_stor_techs['i'].isin(i_data)
            marg_stor_techs = marg_stor_techs[marg_stor_techs['i'].isin(
                i_data)].reset_index(drop=True)
            missing_techs = False
            # This assumes every region has these two techs as well; will break
            # if some regions have 4 and 8 hr storage when others don't and it
            # tries to interpolate for all the regions. Figure out why the
            # storage technologies are being limited in
            # condor_data['marg_stor_techs']
        else:  # Otherwise compute the values manually for each duration
            missing_techs = True
    marg_stor_props = marg_stor_techs[['i', 'rte', 'duration', 'res']]
    marg_stor_props = marg_stor_props.drop_duplicates().set_index('i')

    stor_MW = SwitchSettings.switches['condor_stor_MW']


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

    cost_pvb_max = marg_stor_techs[
        marg_stor_techs['i'] == 'battery_{}'.format(SwitchSettings.switches['gsw_pvb_dur'])
    ]['cost'].max()

    pvb_resources['t'] = SwitchSettings.next_year
    pvb_resources['rte'] = (
        marg_storage_props.set_index('i')
        .loc['battery_{}'.format(SwitchSettings.switches['gsw_pvb_dur']),'rte']
    )
    pvb_resources['duration'] = int(SwitchSettings.switches['gsw_pvb_dur'])
    pvb_resources['res'] = condor_res

    # Loop through each storage technology
    for i, row in marg_stor_props.iterrows():
        e_level_n = int(row.res)
        # Note that we subtract an hour off of the storage duration to account
        # for the inevitable overestimation of storage revenue using a price-\
        # taking model with perfect foresight.
        stor_MWh = stor_MW * (row.duration - (SwitchSettings.switches['reedscc_stor_buffer']/60))
        eta_charge = row.rte
        ba_list = marg_stor_techs.loc[marg_stor_techs.i == i, 'r'].tolist()
        # ba_list = marg_stor_techs_new.loc[marg_stor_techs_new.i == i, 'r'].tolist()
        for ba in ba_list:
            df_temp = pd.DataFrame(columns=['i', 'r', 't', 'revenue'])

            try:
                ba_prices_startup = prices_pivot[ba].values
            except KeyError:
                # If the ba isn't in prices_pivot its price is zero in all hours
                ba_prices_startup = np.zeros(len(prices_pivot))

            # Dispatch against the startup-modified LP prices
            dispatch_results = dispatch_storage(
                ba_prices_startup, stor_MW, stor_MWh, e_level_n, eta_charge,
                eta_discharge)

            df_temp['revenue'] = [dispatch_results['revenue']]
            df_temp['i'] = i
            df_temp['r'] = ba
            df_temp['t'] = str(SwitchSettings.next_year)

            # Figure out when storage is charging while there is curtailment
            dispatch = dispatch_results['dispatch_profile']
            idx_charge = dispatch > 0

            dispatch[idx_charge].sum()  # Total charging
            idx_curt = df_curt[ba]
            idx_curt.sum()

            # Total charging when there is not curtailment:
            dispatch[idx_charge & ~idx_curt].sum()
            stor_rev_fraction = np.divide(
                dispatch[idx_charge & ~idx_curt].sum(),
                dispatch[idx_charge].sum(),
                where=dispatch[idx_charge].sum() != 0)

            # Adjust the total revenue by this fraction to remove the revenue
            #   from charging during curtailment
            df_temp['revenue'] *= stor_rev_fraction
            
            # Store results
            df_results.loc[len(df_results), :] = df_temp.loc[0, :]# Loop through each storage technology

    for i in pvb_resources.index:
        df_temp = pd.DataFrame(columns=['i', 'r', 't', 'revenue'])
        ba = pvb_resources.loc[i, 'r']
        resource = pvb_resources.loc[i, 'resource']
        stor_MWh = stor_MW * (pvb_resources.loc[i, 'duration'] - \
                    (SwitchSettings.switches['reedscc_stor_buffer']/60))
        e_level_n = pvb_resources.loc[i, 'res']
        eta_charge = pvb_resources.loc[i, 'rte']
        restrict = clip_pvb[resource]
        tech = pvb_resources.loc[i, 'i']

        try:
            ba_prices_startup = prices_pivot[ba].values
        except KeyError:
            # If the ba isn't in prices_pivot its price is zero in all hours
            ba_prices_startup = np.zeros(len(prices_pivot))

        # Dispatch against the startup-modified LP prices
        dispatch_results = dispatch_storage(
            ba_prices_startup, stor_MW, stor_MWh, e_level_n, eta_charge,
            eta_discharge, restrict=restrict)

        df_temp['revenue'] = [dispatch_results['revenue']]
        df_temp['i'] = tech
        df_temp['r'] = ba
        df_temp['t'] = str(SwitchSettings.next_year)

        # Figure out when storage is charging while there is curtailment
        dispatch = dispatch_results['dispatch_profile']
        idx_charge = dispatch > 0

        dispatch[idx_charge].sum()  # Total charging
        idx_curt = df_curt[ba]
        idx_curt = idx_curt[~restrict].reset_index(drop=True)

        # Total charging when there is not curtailment:
        dispatch[idx_charge & ~idx_curt].sum()
        stor_rev_fraction = np.divide(
            dispatch[idx_charge & ~idx_curt].sum(),
            dispatch[idx_charge].sum(),
            where=dispatch[idx_charge].sum() != 0)

        # Adjust the total revenue by this fraction to remove the revenue
        #   from charging during curtailment
        df_temp['revenue'] *= stor_rev_fraction
        
        # Store results
        df_results_pvb.loc[len(df_results_pvb), :] = df_temp.loc[0, :]


    # The results come on with dtype=object, so convert to float
    df_results.revenue = df_results.revenue.astype(float)
    df_results_pvb.revenue = df_results_pvb.revenue.astype(float)

    # Divide by the number of Osprey years to get the annual revenue
    df_results.revenue /= SwitchSettings.switches['osprey_num_years']
    df_results_pvb.revenue /= SwitchSettings.switches['osprey_num_years']

    # If we are interpolating data for the remaining durations:
    if not SwitchSettings.switches['condor_stor_techs'] == 'all':
        if not missing_techs:
            # Interpolate revenue for remaining durations
            storage_revenue_pair = df_results.copy()
            df_results = interpolate_other_durations(storage_revenue_pair)
            
    # Don't let the revenue exceed the capital costs in ReEDS
    df_results = pd.merge(
        left=df_results,
        right=marg_stor_techs_save.reset_index()[['i', 'r', 't', 'cost']],
        on=['i', 'r', 't'])
    df_results.revenue = df_results.revenue.clip(upper=df_results.cost)
    df_results.drop('cost', axis=1, inplace=True)
    
    df_results_pvb ['cost'] = cost_pvb_max
    df_results_pvb.revenue = df_results_pvb.revenue.clip(upper=df_results_pvb.cost)
    df_results_pvb.drop('cost', axis=1, inplace=True)
            
    df_results = pd.concat([df_results, df_results_pvb], sort=False)

    # Remove small numbers and round results
    df_results.loc[df_results['revenue'] < SwitchSettings.switches['min_val'], 'revenue'] = 0
    df_results['revenue'] = (
        df_results['revenue'].astype(float).round(SwitchSettings.switches['decimals']))

    # DR calculations
    df_results_dr = pd.DataFrame(columns=['i', 'r', 't', 'revenue'])
    stor_eff = get_storage_eff()
    # Get DR properties
    marg_dr_props = stor_eff[stor_eff['i'].isin(techs['dr1'])]

    dr_hrs = INPUTS['dr_hrs'].get_data()
    dr_hrs['hrs'] = list(zip(dr_hrs.pos_hrs, -dr_hrs.neg_hrs))
    dr_hrs['max_hrs'] = 8760
    dr_shed = INPUTS['dr_shed'].get_data()
    dr_shed.max_hrs = dr_shed.max_hrs.astype('int')
    dr_shed['hrs'] = [(1, 1)]*len(dr_shed.index)
    dr_hrs = pd.concat([dr_hrs, dr_shed])

    marg_dr_props = pd.merge(marg_dr_props, dr_hrs, on='i', how='right').set_index('i')
    # Fill missing data
    marg_dr_props.loc[marg_dr_props.RTE != marg_dr_props.RTE, 'RTE'] = 1
    marg_dr_props = marg_dr_props[['hrs', 'max_hrs', 'RTE']]
    rsc_cost_dr = INPUTS['rsc_dat_dr'].get_data()
    rsc_cost_dr = rsc_cost_dr[['i', 'r', 'cost']].groupby(['i', 'r'],
                                                           as_index=False).max()
    rsc_cost_dr['t'] = SwitchSettings.next_year
    rsc_cost_dr['t'] = rsc_cost_dr['t'].astype(int)
    marg_dr_techs = pd.merge(marg_dr_props, rsc_cost_dr,
                             left_index=True, right_on='i').set_index('i')
    marg_dr_techs_save = marg_dr_techs.copy()
    marg_dr_techs_save['t'] = marg_dr_techs_save['t'].astype(str)

    # Get DR value
    # These are the DR technologies to compute the marginal arbitrage
    #   revenue of
    dr_inc = HOURLY_PROFILES['dr_inc'].profiles.copy()
    dr_dec = HOURLY_PROFILES['dr_dec'].profiles.copy()
    dr_max_dec = pd.melt(dr_dec.groupby('i').max(),
                         ignore_index=False, var_name='r', value_name='max_dec'
                         ).round()
    dr_max_inc = pd.melt(dr_inc.groupby('i').max(),
                         ignore_index=False, var_name='r', value_name='max_inc'
                         ).round()
    # Add max decrease onto techs, for scaled method
    marg_dr_techs = pd.merge(marg_dr_techs.reset_index(),
                             dr_max_dec.reset_index(),
                             on=['i', 'r']).set_index('i')

    # Add appropriate resolution ('res') column and values to the dataframe
    if marg_dr_techs.empty:
        marg_dr_techs['res'] = None  # Needs this column still
    else:
        # Modify marg_dr_techs to have the appropriate 'res' column
        #   Can add in A_prep_data.py so it's in condor_inputs...
        condor_res_method = SwitchSettings.switches['condor_res_method']
        if condor_res_method == 'equal':
            # equal: condor_res is the resolution for all DR techs
            marg_dr_techs['res'] = int(condor_res)
        elif condor_res_method == 'scaled':
            # scaled: condor_res is the resolution for max decrease ~=1; get
            #   resolution for remaining techs by scaling up using max_dec
            marg_dr_techs['res'] = np.maximum(condor_res,
                                              marg_dr_techs['max_dec'] * condor_res)
        else:
            print('ERROR: options for condor_res_method are equal or scaled')

    # i is index already
    marg_dr_props = marg_dr_techs[['RTE', 'hrs', 'max_hrs', 'res']]
    marg_dr_props = marg_dr_props[~marg_dr_props.index.duplicated()]

    dr_MW = SwitchSettings.switches['condor_dr_MW']
    dr_MWh = SwitchSettings.switches['condor_dr_MWh']

    # Split out Shed and Shift based on the number of hours it can operate
    # This may or may not hold true in the future, so check if DR changes
    marg_dr_shed = marg_dr_props[marg_dr_props.max_hrs < 8760]
    marg_dr_shift = marg_dr_props[marg_dr_props.max_hrs == 8760]

    prices_pivot = pd.DataFrame(columns=['idx_hr'],
                                data=index_hr_map['idx_hr'].values)
    prices_pivot = pd.merge(left=prices_pivot, right=prices.pivot(
        index='idx_hr', columns='r', values='price_startup'),
        on='idx_hr', how='left').fillna(0)
    prices_pivot = prices_pivot.set_index('idx_hr')

    # Loop through each dr technology
    for i, row in marg_dr_shift.iterrows():
        # For DR, resolution is for each direction, so double here
        # +1 to ensure 0 is at mid point
        e_level_n = int(row.res) * 2 + 1
        # Note that we account for the hourly shifting requirements by
        # forcing the storage to cycle every N hrs (ie, at hour 0, 4, 8 etc)
        # While this is likely overly restrictive for DR, the error there
        # helps account for the inevitable overestimation of dr revenue using
        # a price-taking model with perfect foresight.
        eta_charge = row.RTE
        print('calculating dr energy revenue for {}...'.format(i))
        ba_list = marg_dr_techs.loc[i, 'r'].tolist()
        for ba in ba_list:
            df_temp = pd.DataFrame(columns=['i', 'r', 't', 'revenue'])

            try:
                ba_prices_startup = prices_pivot[ba].values
            except KeyError:
                # If the ba isn't in prices_pivot its price is zero in all hours
                ba_prices_startup = np.zeros(len(prices_pivot))

            dr_ba_max_inc = dr_max_inc[(dr_max_inc.index == i)
                                       & (dr_max_inc.r == ba)].max_inc
            dr_ba_max_dec = dr_max_dec[(dr_max_dec.index == i)
                                       & (dr_max_dec.r == ba)].max_dec
            # Dispatch against the startup-modified LP prices
            dispatch_results = dispatch_dr(
                ba_prices_startup, dr_MW, dr_MWh, e_level_n, eta_charge,
                eta_discharge, int(np.array(row.hrs).mean()),
                dr_inc[dr_inc.i == i][ba].values,
                dr_dec[dr_dec.i == i][ba].values,
                dr_ba_max_inc, dr_ba_max_dec)

            df_temp['revenue'] = [dispatch_results['revenue']]
            df_temp['i'] = i
            df_temp['r'] = ba
            df_temp['t'] = str(SwitchSettings.next_year)

            # Figure out when DR is charging while there is curtailment
            dispatch = dispatch_results['dispatch_profile']
            idx_charge = dispatch > 0

            dispatch[idx_charge].sum()  # Total charging
            idx_curt = df_curt[ba]
            idx_curt.sum()

            # Total charging when there is not curtailment:
            dispatch[idx_charge & ~idx_curt].sum()
            stor_rev_fraction = np.divide(
                dispatch[idx_charge & ~idx_curt].sum(),
                dispatch[idx_charge].sum(),
                where=dispatch[idx_charge].sum() != 0)

            # Adjust the total revenue by this fraction to remove the revenue
            #   from charging during curtailment
            df_temp['revenue'] *= stor_rev_fraction

            # Store results
            df_results_dr.loc[len(df_results_dr), :] = df_temp.loc[0, :]

    # Loop through each dr technology
    for i, row in marg_dr_shed.iterrows():
        if i not in marg_dr_techs.index:
            # The tech profile is all 0's, so skip
            continue
        print('calculating dr energy revenue for {}...'.format(i))
        ba_list = marg_dr_techs.loc[i, 'r'].tolist()
        for ba in ba_list:
            df_temp = pd.DataFrame(columns=['i', 'r', 't', 'revenue'])

            try:
                ba_prices_startup = prices_pivot[ba].values
            except KeyError:
                # If the ba isn't in prices_pivot its price is zero in all hours
                ba_prices_startup = np.zeros(len(prices_pivot))

            # For shed, take N highest hours of revenue
            dr_neg = dr_dec[dr_dec.i==i][ba].values
            revenue = np.sum(np.sort(dr_neg * ba_prices_startup)[-int(row.max_hrs):])

            df_temp['revenue'] = [revenue]
            df_temp['i'] = i
            df_temp['r'] = ba
            df_temp['t'] = str(SwitchSettings.next_year)

            # Store results
            df_results_dr.loc[len(df_results_dr), :] = df_temp.loc[0, :]
    # The results come on with dtype=object, so convert to float
    df_results_dr.revenue = df_results_dr.revenue.astype(float)

    # Divide by the number of Osprey years to get the annual revenue
    df_results_dr.revenue /= SwitchSettings.switches['osprey_num_years']

    # Don't let the revenue exceed the capital costs in ReEDS
    df_results_dr = pd.merge(
        left=df_results_dr,
        right=marg_dr_techs_save.reset_index()[['i', 'r', 't', 'cost']],
        on=['i', 'r', 't'])
    df_results_dr.revenue = df_results_dr.revenue.clip(upper=df_results_dr.cost)
    df_results_dr.drop('cost', axis=1, inplace=True)

    # Remove small numbers and round results
    df_results_dr.loc[df_results_dr['revenue'] < SwitchSettings.switches['min_val'], 'revenue'] = 0
    df_results_dr['revenue'] = (
        df_results_dr['revenue'].astype(float)).round(SwitchSettings.switches['decimals'])

    df_results = pd.concat([df_results, df_results_dr], sort=False)

    condor_results = {
        'hourly_arbitrage_value': df_results.reindex(['i','r','t','revenue'], axis=1)
    }
    #%%
    return condor_results

#%%

def dispatch_storage(e_price_profile, stor_MW, stor_MWh, e_level_n,
                     eta_charge, eta_discharge, restrict=None):
    '''
    Optimal dispatch of a generic storage unit.
    - Perfect foresight.
    - Price-taking for a given price profile.
    - Power is the limit of the unit's influence on load
    - If energy input is desired as effective output, set eta_discharge=1.0
        and all inefficiencies into eta_charge
        ba_prices_startup, stor_MW, stor_MWh, e_level_n, eta_charge,
            eta_discharge, restrict=restrict)
    '''
    # Removing hours with pvb clipping
    if restrict is not None:
        e_price_profile = e_price_profile[~restrict]

    n_timesteps = len(e_price_profile)

    # Calculate the energy levels of the storage unit for the specified
    #   resolution, and calculate the resolution between steps
    e_levels = np.linspace(stor_MWh, 0, e_level_n)
    e_level_res = stor_MWh/(e_level_n-1)

    # Initialize some objects for later use in Condor
    # +1 for expected costs, because of column for penalizing ending without
    #   being full:
    expected_costs = np.zeros((e_level_n, n_timesteps+1), float)
    costs_to_go = np.zeros((e_level_n, n_timesteps), float)
    option_choices_change = np.zeros((e_level_n, n_timesteps), int)

    # Determine how many energy levels the storage unit can move each
    #   timestep, based on its power limit.
    # The number of steps you can move "up" in storage level each timestep:
    charge_n = int(np.floor(stor_MW*eta_charge/e_level_res))
    # The number of steps you can move "down" in storage level each timestep:
    discharge_n = int(np.floor(stor_MW/eta_discharge/e_level_res))
    e_change_n = charge_n + discharge_n + 1

    # The energy level changes, given the possible steps that can be taken
    e_changes = np.append(np.arange(charge_n, 0, -1) * e_level_res,
                          0.0)
    e_changes = np.append(e_changes,
                          np.arange(-1, -discharge_n-1, -1) * e_level_res)

    # The influence on demand for each energy level change (i.e. the impact of
    #   charging and discharging inefficiencies)
    influence_on_demand = np.tile(e_changes, [e_level_n, 1])
    influence_on_demand[:, :charge_n] = \
        influence_on_demand[:, :charge_n] / eta_charge
    influence_on_demand[:, discharge_n:] = \
        influence_on_demand[:, discharge_n:] * eta_discharge

    # Expected value of final states is the energy required to fill the
    #   storage up at an arbitrarily high value of $100/MWh. This encourages
    #   the storage to end full, but solves the issue of certain demand
    #   reductions being impossible because there isn't enough time to fill
    #   the storage completely if they occur right before the end of the
    #   analysis period.
    expected_costs[:, -1] = (stor_MWh - e_levels) / eta_charge * 100.0

    # option_indicies is a map of the indicies corresponding to the possible
    #   points within the expected_value matrix that that state can reach.
    #   Each row is the set of options for a single storage state.
    option_indicies = (np.ones((e_level_n, e_change_n), int)
                       * np.array(range(e_level_n)).reshape([e_level_n, 1]))
    option_indicies[:, :] += np.arange(-charge_n, discharge_n+1)

    # A matrix to impose a penalty to avoid impossible moves (e.g. charging
    #   when the storage is already full). Zero when allowed, infinity cost
    #   when illegal.
    possible_moves = np.zeros((e_level_n, e_change_n), float)
    possible_moves = np.where(option_indicies < 0, float('inf'),
                              possible_moves)
    possible_moves = np.where(option_indicies > e_level_n-1, float('inf'),
                              possible_moves)

    # Cannot discharge below "empty":
    option_indicies[option_indicies < 0] = 0
    # Cannot charge above "full":
    option_indicies[option_indicies > e_level_n-1] = e_level_n-1

    # Build an adjustment that adds a very small amount to the cost-to-go, as
    #   a function of rate of charge. Makes the Condor prefer to charge
    #   slowly, all else being equal
    adjuster = np.zeros(e_change_n, float)
    base_adjustment = 0.0000001
    adjuster[e_change_n-discharge_n-1:] = (base_adjustment
                                           * np.array(range(discharge_n+1))
                                           * np.array(range(discharge_n+1))
                                           / (discharge_n*discharge_n))
    adjuster[np.arange(charge_n, -1, -1)] = (base_adjustment
                                             * np.array(range(charge_n+1))
                                             * np.array(range(charge_n+1))
                                             / (charge_n*charge_n))

    ###################################################################
    ############################# CONDOR ##############################
    ###################################################################
    ############## Dynamic Programming Energy Trajectory ##############

    for hour in np.arange(n_timesteps-1, -1, -1):
        # Expected_costs is hour-beginning, i.e. it is the expected cost if
        #   you start that hour at that storage state. It is the sum of the
        #   best option available within that hour and the cost of where you
        #   would end up.

        # For costs_to_go, rows are storage energy levels and columns are the
        #   movements available. So (0,0) is full and charging, which isn't
        #   possible. (0,middle) is full and not doing anything. (0,-1) is
        #   full and discharging at max power.

        # Determine the incremental cost-to-go for each option
        costs_to_go = influence_on_demand * e_price_profile[hour]
        costs_to_go += possible_moves

        # add very small cost as a function of storage motion, to discourage
        #   unnecessary motion
        costs_to_go += adjuster

        # Calculate the total option costs, cost-to-go plus the cumulative
        #   cost of the point you're going to
        total_option_costs = costs_to_go + expected_costs[option_indicies,
                                                          hour+1]

        # Determine the expected value for each state in hour, which is the
        #   minimum of each state's total_option_costs. This is saying, "if
        #   you wind up at this energy level at the beginning of this hour,
        #   the expected costs going forward are X"
        expected_costs[:, hour] = np.min(total_option_costs, 1)

        # Record the indicies of the optimal storage movement for each state.
        #   Movement, not absolute energy levels. This is saying "if you wind
        #   up at this energy level at the beginning of this hour, this is the
        #   index of the movement that is optimal for this hour"
        option_choices_change[:, hour] = np.argmin(total_option_costs, 1)


    #=================================================================#
    ################## Reconstruct Optimal Dispatch ###################
    #=================================================================#
    # Determine what the optimal trajectory was, starting with a full storage
    #   unit.
    # traj_i is the indicies of the storage's internal energy level
    #   trajectory. Hour-ending.
    # actions_i is the indicies of the storage's actions

    # +1 to give room for the "starting full" condition:
    traj_i = np.zeros(n_timesteps+1, int)
    traj_i[0] = 0  # Start full.
    actions_i = np.zeros(n_timesteps, int)

    for n in np.arange(1, n_timesteps+1):
        traj_i[n] = \
            traj_i[n-1] + option_choices_change[traj_i[n-1], n-1] - charge_n
        actions_i[n-1] = option_choices_change[traj_i[n-1], n-1]

    # Determine the storage energy level over time
    e_level_traj = e_levels[traj_i[1:]]

    # Determine the optimal storage dispatch
    dispatch_profile = influence_on_demand[0, actions_i]

    # Revenue is the reduction in the system's cost
    revenue = -np.sum(dispatch_profile * e_price_profile)

    #=================================================================#
    ################## Package and return results #####################
    #=================================================================#

    results_dict = {'dispatch_profile': dispatch_profile,
                    'e_price_profile': e_price_profile,
                    'e_level_traj': e_level_traj,
                    'revenue': revenue}

    return results_dict




#%%
def dispatch_dr(e_price_profile, dr_MW, dr_MWh, e_level_n,
                eta_charge, eta_discharge, max_shift, dr_pos, dr_neg,
                max_pos, max_neg):
    '''
    Optimal dispatch of a generic dr unit.
    - Perfect foresight.
    - Price-taking for a given price profile.
    - Power is the limit of the unit's influence on load
    - Represent as large storage with requirement to be at midline end of day
    - If energy input is desired as effective output, set eta_discharge=1.0
        and all inefficiencies into eta_charge
    '''

    n_timesteps = len(e_price_profile)
    # midpoint of storage
    mid = int((e_level_n - 1) / 2)

    # Calculate the energy levels of the dr unit for the specified
    #   resolution, and calculate the resolution between steps
    e_levels = np.linspace(dr_MWh, -dr_MWh, e_level_n)
    e_level_res = dr_MWh/(e_level_n-1)

    # Initialize some objects for later use in Condor
    # +1 for expected costs, because of column for penalizing ending without
    #   being full:
    expected_costs = np.zeros((e_level_n, n_timesteps+1), float)
    costs_to_go = np.zeros((e_level_n, n_timesteps), float)
    option_choices_change = np.zeros((e_level_n, n_timesteps), int)

    # Determine how many energy levels the dr unit can move each
    #   timestep, based on its power limit.
    # The number of steps you can move "up" in dr level each timestep:
    charge_n = int(np.floor(dr_MW*max_pos*eta_charge/e_level_res))
    # The max number of steps you can move "down" in dr level each timestep:
    discharge_n = int(np.floor(dr_MW*max_neg/eta_discharge/e_level_res))
    e_change_n = charge_n + discharge_n + 1

    # The energy level changes, given the possible steps that can be taken
    e_changes = np.append(np.arange(charge_n, 0, -1) * e_level_res,
                          0.0)
    e_changes = np.append(e_changes,
                          np.arange(-1, -discharge_n-1, -1) * e_level_res)

    # The influence on demand for each energy level change (i.e. the impact of
    #   charging and discharging inefficiencies)
    influence_on_demand = np.tile(e_changes, [e_level_n, 1])
    influence_on_demand[:, :charge_n] = \
        influence_on_demand[:, :charge_n] / eta_charge
    influence_on_demand[:, discharge_n:] = \
        influence_on_demand[:, discharge_n:] * eta_discharge

    # Expected value of final states is the energy required to get to the
    #   midpoint at an arbitrarily high value of $100/MWh.
    #   This encourages the dr to end at mid and solves the issue of certain
    #   demand reductions being impossible because there isn't enough time to
    #   fill the dr completely if they occur right before the end of the
    #   analysis period.
    expected_costs[:, -1] = abs(e_levels) / eta_charge * 100.0
    # if n_timesteps is a multiple of max_shift, enforce midpoint ending
    if n_timesteps % max_shift == 0:
        expected_costs[0:mid, -1] = float('inf')
        expected_costs[mid+1:, -1] = float('inf')

    # option_indicies is a map of the indicies corresponding to the possible
    #   points within the expected_value matrix that that state can reach.
    #   Each row is the set of options for a single dr state.
    option_indicies = (np.ones((e_level_n, e_change_n), int)
                       * np.array(range(e_level_n)).reshape([e_level_n, 1]))
    option_indicies[:, :] += np.arange(-charge_n, discharge_n+1)

    # A matrix to impose a penalty to avoid impossible moves (e.g. charging
    #   when the dr is already full). Zero when allowed, infinity cost
    #   when illegal.
    possible_moves = np.zeros((e_level_n, e_change_n, n_timesteps), float)
    possible_moves = np.where(option_indicies[:, :, None] < 0, float('inf'),
                              possible_moves)
    possible_moves = np.where(option_indicies[:, :, None] > e_level_n-1,
                              float('inf'), possible_moves)
    # Remove from possible set all moves that don't have enough DR availability
    possible_moves = np.where(influence_on_demand[:, :, None] > dr_pos[None, None, :],
                              float('inf'), possible_moves)
    possible_moves = np.where(influence_on_demand[:, :, None] < -dr_neg[None, None, :],
                              float('inf'), possible_moves)
    # Force the storage to return to mid-line during hours that are multiples
    # of max_shift to enforce cycling of DR at appropriate intervals. While
    # this is more restrictive than in reality, the potential reduction in value
    # is balanced by this being a perfect foresight model, so overly optimistic.
    possible_moves[0:mid, :, np.arange(0, n_timesteps, max_shift)] = float('inf')
    possible_moves[mid+1:, :, np.arange(0, n_timesteps, max_shift)] = float('inf')

    # Cannot discharge below "empty":
    option_indicies[option_indicies < 0] = 0
    # Cannot charge above "full":
    option_indicies[option_indicies > e_level_n-1] = e_level_n-1

    # Build an adjustment that adds a very small amount to the cost-to-go, as
    #   a function of rate of charge. Makes the Condor prefer to charge
    #   slowly, all else being equal
    adjuster = np.zeros(e_change_n, float)
    base_adjustment = 0.0000001
    adjuster[e_change_n-discharge_n-1:] = (base_adjustment
                                           * np.array(range(discharge_n+1))
                                           * np.array(range(discharge_n+1))
                                           / (discharge_n*discharge_n))
    adjuster[np.arange(charge_n, -1, -1)] = (base_adjustment
                                             * np.array(range(charge_n+1))
                                             * np.array(range(charge_n+1))
                                             / (charge_n*charge_n))

    ###################################################################
    ############################# CONDOR ##############################
    ###################################################################
    ############## Dynamic Programming Energy Trajectory ##############

    for hour in np.arange(n_timesteps-1, -1, -1):
        # Expected_costs is hour-beginning, i.e. it is the expected cost if
        #   you start that hour at that dr state. It is the sum of the
        #   best option available within that hour and the cost of where you
        #   would end up.

        # For costs_to_go, rows are dr energy levels and columns are the
        #   movements available. So (0,0) is full and charging, which isn't
        #   possible. (0,middle) is full and not doing anything. (0,-1) is
        #   full and discharging at max power.

        # Determine the incremental cost-to-go for each option
        costs_to_go = influence_on_demand * e_price_profile[hour]
        costs_to_go += possible_moves[:, :, hour]

        # add very small cost as a function of dr motion, to discourage
        #   unnecessary motion
        costs_to_go += adjuster

        # Calculate the total option costs, cost-to-go plus the cumulative
        #   cost of the point you're going to
        total_option_costs = costs_to_go + expected_costs[option_indicies,
                                                          hour+1]

        # Determine the expected value for each state in hour, which is the
        #   minimum of each state's total_option_costs. This is saying, "if
        #   you wind up at this energy level at the beginning of this hour,
        #   the expected costs going forward are X"
        expected_costs[:, hour] = np.min(total_option_costs, 1)

        # Record the indicies of the optimal dr movement for each state.
        #   Movement, not absolute energy levels. This is saying "if you wind
        #   up at this energy level at the beginning of this hour, this is the
        #   index of the movement that is optimal for this hour"
        option_choices_change[:, hour] = np.argmin(total_option_costs, 1)


    #=================================================================#
    ################## Reconstruct Optimal Dispatch ###################
    #=================================================================#
    # Determine what the optimal trajectory was, starting with a full dr
    #   unit.
    # traj_i is the indicies of the dr's internal energy level
    #   trajectory. Hour-ending.
    # actions_i is the indicies of the dr's actions

    # +1 to give room for the "starting full" condition:
    traj_i = np.zeros(n_timesteps+1, int)
    traj_i[0] = mid  # Start at half.
    actions_i = np.zeros(n_timesteps, int)

    for n in np.arange(1, n_timesteps+1):
        traj_i[n] = \
            traj_i[n-1] + option_choices_change[traj_i[n-1], n-1] - charge_n
        actions_i[n-1] = option_choices_change[traj_i[n-1], n-1]

    # Determine the dr energy level over time
    e_level_traj = e_levels[traj_i[1:]]

    # Determine the optimal dr dispatch
    dispatch_profile = influence_on_demand[mid, actions_i]

    # Revenue is the reduction in the system's cost
    revenue = -np.sum(dispatch_profile * e_price_profile)

    #=================================================================#
    ################## Package and return results #####################
    #=================================================================#

    results_dict = {'dispatch_profile': dispatch_profile,
                    'e_price_profile': e_price_profile,
                    'e_level_traj': e_level_traj,
                    'revenue': revenue}

    return results_dict

#%%


def interpolate_other_durations(storage_revenue_pair):
    '''
    This function takes the storage revenue for 4 hr and 8 hr batteries and
    uses linear interpolation to estimate the storage revenue for the other 4
    durations.
    This is only compatible with 2, 4, 6, 8, and 10 hour battery storage as
    well as pumped-hydro, which is treated as if it was a 12-hr battery.
    '''

    # Prepare input data
    durations = [2, 4, 6, 8, 10, 12]
    duration_map = {'battery_2': 2,
                    'battery_4': 4,
                    'battery_6': 6,
                    'battery_8': 8,
                    'battery_10': 10,
                    'pumped-hydro': 12}
    duration_map_r = {v: k for k, v in duration_map.items()}

    # Just use types in duration_map for interpolation
    df_in = storage_revenue_pair[storage_revenue_pair.i.isin(duration_map.keys())].copy()
    df_in['r_t'] = df_in.r+'<><>'+df_in.t
    df_in['duration'] = df_in.i.map(duration_map)
    df_in = df_in.pivot(index='duration', columns='r_t', values='revenue')
    df_in = df_in.reindex(durations)
    pair = [4, 8]  # The durations with the data

    # Normalize by duration
    d = df_in.divide(df_in.index, axis=0)

    # Compute slope for linear regression
    x1, x2 = pair[0], pair[1]
    y1, y2 = d.loc[pair[0]], d.loc[pair[1]]
    m = (y2 - y1) / (x2 - x1)

    # Create data frame with slope for correct broadcasting behavior below
    n = len(durations)
    m_df = pd.DataFrame(m)
    m_df = pd.concat([m_df]*n, axis=1)
    m_df.columns = durations
    m_df = m_df.T

    # Durations to interpolate for
    x = d.index.to_frame()

    # Interpolate: y = y1 + m*(x - x1)
    df_fit = y1 + m_df * (x - x1).values

    # Un-normalize by duration
    df_fit *= d.index.to_frame().values

    # Prepare output data
    df_out = df_fit.stack().reset_index().rename(
            columns={'level_0': 'duration', 0: 'revenue'})
    df_out[['r', 't']] = df_out.r_t.str.split('<><>', expand=True)
    df_out['i'] = df_out.duration.map(duration_map_r)
    # Append back on other types for output
    df_out = pd.concat(
        [df_out[['i', 'r', 't', 'revenue']],
         storage_revenue_pair[~storage_revenue_pair.i.isin(duration_map.keys())]
         ])

    return df_out
