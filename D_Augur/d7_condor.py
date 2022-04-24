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

import pandas as pd
import numpy as np
import os
from utilities import tech_types, print1


#%%
def get_marginal_storage_value(args, condor_data, osprey_results,
                               trans_region_curt):
    '''
    This function performs a simulated storage dispatch
    '''
#%%
    print1('reading in data for Condor...')

    # Default efficiency value for Condor
    eta_discharge = args['condor_discharge_eff']
    # List of technology types that are considered when adjusting price
    #   profiles for start costs
    keep_techs = args['condor_keep_techs']

    techs = tech_types(args)
    techs_to_keep = []
    for t in keep_techs:
        techs_to_keep += techs[t]

    # Results from Condor are adjusted for when it charges storage from
    # curtailment. The potential for marginal storage to charge from
    # curtailment is captured in C2_marginal_curtailment, and the value of
    # this is captured in ReEDS.
    df_curt = trans_region_curt.reset_index(drop=True)

    # Generation
    gen_names = osprey_results['gen_names'].copy()
    gen_names = gen_names[gen_names['i'].isin(techs_to_keep)]
    gen_names = gen_names.reset_index(drop=True)
    gen = osprey_results['gen'].copy()
    gen = gen[gen_names['generator']]

    # Prices
    prices = osprey_results['prices'].copy()
    prices['idx_hr'] = ((prices.d.str[1:].astype(int) - 1)*24
                        + prices.hr.str[2:].astype(int) - 1)
    prices = prices.rename(columns={'Val': 'price_org'})
    prices.loc[prices['price_org'] < 0.001, 'price_org'] = 0

    # Get the transmission connected regions
    trans_region_map_df = osprey_results['tran_region_map'].copy()

    # Lists and counts
    bas = condor_data['rfeas']['r'].tolist()
    index_hr_map = pd.read_csv(os.path.join('A_Inputs','inputs','variability','index_hr_map.csv'))
    hour_day_map = index_hr_map[['idx_hr', 'd']].drop_duplicates()

    #%% Import generator characteristics

    generator_data = pd.read_csv(os.path.join('A_Inputs','inputs','variability','hourly_operational_characteristics.csv'))
    generator_data.loc[:,'category'] = generator_data.loc[:,'category'].str.lower()
    generator_data = generator_data.rename(
        columns={'Start Cost/capacity': 'start_cost_per_MW',
                 'category': 'i', 'Min Stable Level/capacity': 'mingen_f'})
    generator_df = pd.merge(left=gen_names,
                            right=generator_data[['i', 'start_cost_per_MW']],
                            on='i', how='left')

    # Module works better when all generators are assigned CT startup costs
    # DEBUG
    #idx = generator_data['i'] == 'ct-gas'
    #ct_start_cost_per_MW = float(generator_data[idx]['start_cost_per_MW'])
    #generator_df['start_cost_per_MW'] = ct_start_cost_per_MW

    # Ingest and merge each generator's operating cost onto generator_df
    op_costs = condor_data['gen_cost'].copy()
    op_costs['generator'] = op_costs['i'] + op_costs['v'] + op_costs['r']
    generator_df = generator_df.merge(op_costs[['generator', 'op_cost']],
                                      on='generator')

    # Create arrays for broadcasting later
    startup_costs_perMW = generator_df.set_index('generator')
    startup_costs_perMW = startup_costs_perMW['start_cost_per_MW']
    op_costs_lookup = generator_df.set_index('generator')['op_cost']

    #%% Modify LP prices to get price spikes
    print1('adjusting price profiles for start costs...')

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
    startup_expenditures = gen_starts * startup_costs_perMW[gen_starts.columns]

    # Spread out total start cost ($) over the sum of the generation that day
    startup_costs_perMWh = startup_expenditures / gen_sums
    startup_costs_perMWh = startup_costs_perMWh.fillna(0.0)

    # Each generator's "bid price" is its operating cost plus the amount to
    #   recover the startup cost for that day
    bid_prices = \
        startup_costs_perMWh + op_costs_lookup[startup_costs_perMWh.columns]
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

    # Initialize empty data frame for storing the results
    df_results = pd.DataFrame(columns=['i', 'r', 't', 'revenue'])

    # These are the storage technologies to compute the marginal arbitrage
    #   revenue of
    marg_stor_techs = condor_data['marg_stor_techs'].copy()
    
    # This number determines the resolution of Condor
    condor_res = args['condor_res']
#%%    
    # Add appropriate resolution ('res') column and values to the dataframe
    if marg_stor_techs.empty:
        marg_stor_techs['res'] = None # Needs this column still
    else:
        # Modify marg_stor_techs to have the appropriate 'res' column
        #   Can add in A_prep_data.py so it's in condor_inputs...
        condor_res_method = args['condor_res_method']
        if condor_res_method == 'equal':
            # equal: condor_res is the resolution for all storage techs
            marg_stor_techs['res'] = int(condor_res)
        elif condor_res_method == 'scaled':
            # scaled: condor_res is the resolution for battery_2; get the
            #   resolution for remaining techs by scaling up using duration
            #   relative to battery_2
            i_duration = condor_data['storage_durations'].copy()
            i_duration = i_duration.sort_values(by='duration').set_index('i')
            i_duration.duration -= (args['reedscc_stor_buffer']/60)
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
#%%
    # If we are interpolating data for the remaining durations:
    if not args['condor_stor_techs'] == 'all':
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
    # do not calculate energy revenue for 1hr storage
    marg_stor_props = marg_stor_props.loc[marg_stor_props['i'] != 'battery_1', ]

    marg_stor_props = marg_stor_props.drop_duplicates().set_index('i')

    stor_MW = args['condor_stor_MW']
#%%   
    # Loop through each storage technology
    for i, row in marg_stor_props.iterrows():
        e_level_n = int(row.res)
        # Note that we subtract an hour off of the storage duration to account
        # for the inevitable overestimation of storage revenue using a price-\
        # taking model with perfect foresight.
        stor_MWh = stor_MW * (row.duration - (args['reedscc_stor_buffer']/60))
        eta_charge = row.rte
        print1('calculating storage energy revenue for {}...'.format(i))
        ba_list = marg_stor_techs.loc[marg_stor_techs.i == i, 'r'].tolist()
#            ba_list = marg_stor_techs_new.loc[marg_stor_techs_new.i == i, 'r'].tolist()
        for ba in ba_list:
            df_temp = pd.DataFrame(columns=['i', 'r', 't', 'revenue'])

            ba_prices_startup = prices_pivot[ba].values

            # Dispatch against the startup-modified LP prices
            dispatch_results = dispatch_storage(
                ba_prices_startup, stor_MW, stor_MWh, e_level_n, eta_charge,
                eta_discharge)

            df_temp['revenue'] = [dispatch_results['revenue']]
            df_temp['i'] = i
            df_temp['r'] = ba
            df_temp['t'] = str(args['next_year'])

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
            df_results.loc[len(df_results), :] = df_temp.loc[0, :]

    # The results come on with dtype=object, so convert to float
    df_results.revenue = df_results.revenue.astype(float)

    # If we are interpolating data for the remaining durations:
    if not args['condor_stor_techs'] == 'all':
        if not missing_techs:
            # Interpolate revenue for remaining durations
            storage_revenue_pair = df_results.copy()
            df_results = interpolate_other_durations(storage_revenue_pair)

    # Don't let the revenue exceed the capital costs in ReEDS
    # marg_stor_techs = condor_data['marg_stor_techs'].copy()  # Re-define
    # df_results = pd.merge(
    #     left=df_results,
    #     right=marg_stor_techs.reset_index()[['i', 'r', 't', 'cost']],
    #     on=['i', 'r', 't'])
    # df_results.loc[df_results['revenue'] > df_results['cost'], 'revenue'] = \
    #     df_results.loc[df_results['revenue'] > df_results['cost'], 'cost']
    # df_results.drop('cost', axis=1, inplace=True)

    # Remove small numbers and round results
    df_results.loc[df_results['revenue'] < args['min_val'], 'revenue'] = 0
    df_results['revenue'] = df_results['revenue'].round(args['decimals'])

    # The model will fail if this dataframe is empty
    if df_results.empty:
        df_results.loc[0, :] = ['battery_2', bas[0], str(args['next_year']), 0]

    condor_results = {'hourly_arbitrage_value': df_results}
    #%%
    return condor_results


#%%
def dispatch_storage(e_price_profile, stor_MW, stor_MWh, e_level_n,
                     eta_charge, eta_discharge):
    '''
    Optimal dispatch of a generic storage unit.
    - Perfect foresight.
    - Price-taking for a given price profile.
    - Power is the limit of the unit's influence on load
    - If energy input is desired as effective output, set eta_discharge=1.0
        and all inefficiencies into eta_charge
    '''

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
    expected_costs[:, -1] = (stor_MWh - e_levels) / eta_charge * 7000.0

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

    df_in = storage_revenue_pair.copy()
    df_in['r_t'] = df_in.r+'_'+df_in.t
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
    df_out[['r', 't']] = df_out.r_t.str.split('_', expand=True)
    df_out['i'] = df_out.duration.map(duration_map_r)
    df_out = df_out[['i', 'r', 't', 'revenue']]

    return df_out
