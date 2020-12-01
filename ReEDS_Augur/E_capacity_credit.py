
import os
import numpy as np
import pandas as pd
from utilities import tech_types, print1

#%%


def reeds_cc(args, reeds_cc_data):
    '''
    This function directs all of the capacity credit calculations for ReEDS
    It writes out a gdx file which is then read back in to ReEDS during the
    next iteration.
    '''
    #%%
    # Collect arguments
    scenario =              args['scenario']
    next_year =             args['next_year']
    calc_csp =              args['calc_csp_cc']
    annual_hours =          args['reedscc_ann_hours']
    season_hours =          args['reedscc_szn_hours']
    demand_percentage =     args['reedscc_max_stor_pen']
    stor_eff =              args['reedscc_default_rte']
    demand_step_size =      args['reedscc_stor_stepsize']
    stor_buffer_minutes =   args['reedscc_stor_buffer']
    cc_csp_default =        args['reedscc_csp_cc_default']
    marg_CSP_step_MW =      args['reedscc_marg_csp_mw']
    marg_VG_step_MW =       args['reedscc_marg_vre_mw']
    calc_annual =           args['reedscc_calc_annual']
    calc_seasonal =         args['reedscc_calc_seasonal']
    safety_bin_size =       args['reedscc_safety_bin_size']
    csp_step_size =         args['reedscc_csp_step_size']

    # Unpack input data
    cap_csp =           reeds_cc_data['cap_csp'].copy()
    cap_frac_cspns =    reeds_cc_data['cap_frac_cspns'].copy()
    cap_stor =          reeds_cc_data['cap_storage'].copy()
    cap_stor_agg =      reeds_cc_data['cap_storage_agg'].copy()
    csp_resources =     reeds_cc_data['csp_resources'].copy()
    hierarchy =         reeds_cc_data['hierarchy'].copy()
    sdb =               reeds_cc_data['sdbin'].copy()
    resources =         reeds_cc_data['resources'].copy()

    # Get tech subsets
    techs = tech_types(args)

    # Remove the "8760" safety valve bin
    safety_bin = max(sdb['bins'].values)
    sdb = sdb[sdb['bins'] != max(sdb['bins'])]['bins'].tolist()

    # Check length of load data for multiple year CC calculation
    mult_year = False
    if len(reeds_cc_data['load']) > args['osprey_ts_length']:
        mult_year = True

    # Temporal definitions
    dt_map = pd.read_csv(os.path.join('inputs_case', 'h_dt_szn.csv'))
    if not mult_year:
        idx = dt_map['year'] == args['osprey_reeds_data_year']
        dt_map = dt_map[idx].reset_index(drop=True)

    dt_cols = dt_map.columns.tolist()
    seasons = []
    if calc_annual:
        seasons += ['year']
    if calc_seasonal:
        seasons += dt_map['season'].drop_duplicates().tolist()

    # Get CSP data if necessary
    if calc_csp == '1':
        cspcf = pd.read_pickle(
            os.path.join('inputs_case',
                         'csp_profiles_{}.pkl'.format(scenario)))
        cspcf = cspcf.reset_index(drop=True)
        cspcf = pd.concat([dt_map, cspcf], axis=1)

    # Initialize dataframes to store results
    all_cc = pd.DataFrame(columns=['i', 'r', 'season', 't', 'MW'])
    all_cc_mar = pd.DataFrame(columns=['i', 'r', 'season', 't', 'CC'])
    peaking_stor_all = pd.DataFrame(
        columns=['ccreg', 'season', 'duration', 't', 'MW'])
    timeslice_hours_all = pd.DataFrame(
        columns=['h', 'ccreg', 'season', '%TopHrs'])

#%%  FOR LOOP FOR CCREGS

    # March through this for all CCREGs
    for ccreg in hierarchy['ccreg'].drop_duplicates():

        #%%  CCREG DATA
        # ccreg = 'cc2'  # Uncomment for debugging
        print1('Calculating capacity credit for {}'.format(ccreg))
        # ------- Get load profile, RECF profiles, VG capacity, storage
        # capacity, and storage RTE for this CCREG -------

        # Resources to be used
        resources_ccreg = resources[resources['ccreg'] == ccreg].reset_index(
            drop=True)

        # Hourly profiles
        recf_ccreg = reeds_cc_data['vre_gen'][
            dt_cols + resources_ccreg['resource'].tolist()].reset_index(
                drop=True)
        cf_marginal_ccreg = reeds_cc_data['cf_marginal'][
            dt_cols + resources_ccreg['resource'].tolist()].reset_index(
                drop=True)
        load_profile_ccreg = reeds_cc_data['load'][
            dt_cols + [ccreg]].reset_index(drop=True)

        # Storage information
        cap_stor_agg_ccreg = cap_stor_agg[
            cap_stor_agg['ccreg'] == ccreg].reset_index(
                drop=True)
        cap_stor_ccreg = cap_stor[cap_stor['r'].isin(
            hierarchy[hierarchy['ccreg'] == ccreg]['r'])].reset_index(
                drop=True)
        try:
            eff_charge = cap_stor_agg_ccreg['rte'].values[0]
        except:
            eff_charge = stor_eff
        max_demand = load_profile_ccreg[ccreg].max() / (1/demand_percentage)
        reductions_considered = int(max_demand // demand_step_size)
        peak_reductions = np.linspace(0, max_demand, reductions_considered)

        # CSP information
        resources_ccreg_csp = csp_resources[
            csp_resources['ccreg'] == ccreg].reset_index(drop=True)
        if not resources_ccreg_csp.empty:
            cap_csp_ccreg = cap_csp[cap_csp['resource'].isin(
                resources_ccreg_csp['resource'])].reset_index(drop=True)
            if calc_csp == '1':
                cspcf_ccreg_all = cspcf[dt_cols + resources_ccreg_csp[
                    'resource'].tolist()].reset_index(drop=True)
                cspcf_ccreg = cspcf_ccreg_all[dt_cols + cap_csp_ccreg[
                    'resource'].tolist()].reset_index(drop=True)
                csp_fleet_MW = cap_csp_ccreg['MW'].sum()
                csp_fleet_MWh = cap_csp_ccreg['MWh'].sum()


#%%  LOOP FOR SEASONS

        # ---------------------------- CALL FUNCTIONS -------------------------
        for season in seasons:

            #%%
            # season = 'winter'  # Uncomment for debugging
            # Get the load and CF profiles for this season
            if season == 'year':
                load_profile_season = load_profile_ccreg.copy()
                recf_season = recf_ccreg.copy()
                cf_marginal_season = cf_marginal_ccreg.copy()
                dt_season = dt_map.copy()
                hours_considered = annual_hours
                if not resources_ccreg_csp.empty and calc_csp == '1':
                    cspcf_season_all = cspcf_ccreg_all.copy()
                    cspcf_season = cspcf_ccreg.copy()
            else:
                load_profile_season = load_profile_ccreg[load_profile_ccreg[
                    'season'] == season].sort_values('hour').reset_index(
                        drop=True)
                recf_season = recf_ccreg[recf_ccreg[
                    'season'] == season].sort_values('hour').reset_index(
                        drop=True)
                cf_marginal_season = cf_marginal_ccreg[cf_marginal_ccreg[
                    'season'] == season].sort_values('hour').reset_index(
                        drop=True)
                dt_season = dt_map[dt_map['season'] == season].sort_values(
                    'hour').reset_index(drop=True)
                hours_considered = season_hours
                if not resources_ccreg_csp.empty and calc_csp == '1':
                    cspcf_season_all = cspcf_ccreg_all[cspcf_ccreg_all[
                        'season'] == season].sort_values('hour').reset_index(
                            drop=True)
                    cspcf_season = cspcf_ccreg[cspcf_ccreg[
                        'season'] == season].sort_values('hour').reset_index(
                            drop=True)

            # Call cc_vg
            cc_vg_results = \
                cc_vg(recf_season.drop(list(dt_cols), 1).values.copy(),
                      load_profile_season[ccreg].values.copy(),
                      cf_marginal_season.drop(list(dt_cols), 1).values.copy(),
                      hours_considered, marg_VG_step_MW)

            # Collect and organize the results
            timeslice_hours_all = get_top_hours(
                dt_season.reset_index(), cc_vg_results['top_hours_net'],
                ccreg, timeslice_hours_all, season)
            all_cc = get_vg_cc(
                resources_ccreg, next_year, cc_vg_results['cap_useful_MW'],
                cap_frac_cspns, hierarchy, ccreg, all_cc, season)
            all_cc_mar = get_vg_cc_marg(
                resources_ccreg, next_year, cc_vg_results['cc_marg'],
                hierarchy, all_cc_mar, season, techs)

            # Set the net load profile
            net_load_profile = cc_vg_results['load_net']

            if mult_year:
                # The call to this function gives the MWh required for each
                # peak reduction capacity. For each data year, loop through
                # and get get the MWh needed for each peak reduction capacity.
                # Get a "season_required_MWhs" for each year.
                # Get the maximum value for each position in the array.
                # Make a new "season_required_MWhs" array to send to the
                # cc_storage function.
                # Call storage cc functions for existing and marginal
                # conventional storage.
                net_load_profile_timestamp = pd.DataFrame(
                    net_load_profile, load_profile_season.year)
                years = list(net_load_profile_timestamp.index.unique())
                for y in years:
                    net_load_profile_temp = net_load_profile_timestamp.iloc[
                        :, 0][net_load_profile_timestamp.index == y].to_numpy()
                    required_MWhs_temp, batt_powers = calc_required_mwh(
                        net_load_profile_temp.copy(), peak_reductions.copy(),
                        eff_charge, stor_buffer_minutes)
                    if years.index(y) == 0:
                        required_MWhs = required_MWhs_temp.copy()
                    else:
                        required_MWhs = np.maximum(required_MWhs,
                                                   required_MWhs_temp)
            else:
                required_MWhs, batt_powers = calc_required_mwh(
                    net_load_profile.copy(), peak_reductions.copy(),
                    eff_charge, stor_buffer_minutes)

            cc_stor, peaking_stor = cc_storage(
                cap_stor_ccreg.copy(), peak_reductions.copy(),
                required_MWhs.copy(), sdb.copy())
            # Get the peaking storage potential by duration
            peaking_stor_all = get_peaking_stor(
                peaking_stor, ccreg, next_year, peaking_stor_all, season,
                safety_bin, safety_bin_size)

            if not resources_ccreg_csp.empty:
                if calc_csp == '0':
                    # If not calculating CC for CSP, set its CC to the default
                    # value
                    cc_csp = cc_csp_default

                if calc_csp == '1':

                    # Add storage charging to the net load profile
                    storage_fleet_MW = cap_stor_ccreg['MW'].sum()
                    storage_fleet_MWh = cap_stor_ccreg['MWh'].sum()
                    stor_peak_reduct = np.array([storage_fleet_MW * cc_stor])
                    net_load_profile_stor_adj = np.array([])

                    if storage_fleet_MW > 0:
                        if mult_year:
                            for y in years:
                                net_load_profile_temp = pd.DataFrame()
                                net_load_profile_temp['year'] = \
                                    load_profile_season['year'].values
                                net_load_profile_temp['load'] = \
                                    net_load_profile
                                net_load_profile_year = net_load_profile_temp[
                                    net_load_profile_temp['year'] == y][
                                        'load'].values
                                net_load_profile_year = fill_in_charging(
                                    net_load_profile_year, stor_peak_reduct,
                                    eff_charge, storage_fleet_MWh,
                                    storage_fleet_MW)
                                net_load_profile_stor_adj = np.concatenate(
                                    (net_load_profile_stor_adj,
                                     net_load_profile_year))
                        else:
                            net_load_profile_stor_adj = fill_in_charging(
                                net_load_profile, stor_peak_reduct, eff_charge,
                                storage_fleet_MWh, storage_fleet_MW)
                    else:
                        net_load_profile_stor_adj = net_load_profile.copy()

                    # Only do this if there is CSP capacity
                    if len(cap_csp_ccreg) > 0:
                        reductions_considered_csp = int(
                            (csp_fleet_MW + csp_step_size) // csp_step_size)
                        if mult_year:
                            net_load_profile_timestamp = pd.DataFrame(
                                net_load_profile_stor_adj,
                                load_profile_season.year)
                            for y in years:
                                idx = net_load_profile_timestamp.index == y
                                net_load_profile_temp = \
                                    net_load_profile_timestamp[idx][0].values
                                cspcf_season_temp = cspcf_season[
                                    cspcf_season['year'] == y].reset_index(
                                        drop=True)
                                required_MWhs_csp_temp, csp_powers = \
                                    calc_required_mwh_csp(
                                        net_load_profile_temp.copy(),
                                        cap_csp_ccreg['MW'].values.copy(),
                                        cap_csp_ccreg['sm'].values.copy(),
                                        cspcf_season_temp.drop(
                                            dt_cols, 1).values.copy(),
                                        reductions_considered_csp,
                                        combine_profiles=True)
                                if years.index(y) == 0:
                                    required_MWhs_csp = \
                                        required_MWhs_csp_temp.copy()
                                else:
                                    required_MWhs_csp = np.maximum(
                                        required_MWhs_csp,
                                        required_MWhs_csp_temp)
                        else:
                            # Call csp storage cc functions for existing csp
                            required_MWhs_csp, csp_powers = \
                                calc_required_mwh_csp(
                                    net_load_profile_stor_adj.copy(),
                                    cap_csp_ccreg['MW'].values.copy(),
                                    cap_csp_ccreg['sm'].values.copy(),
                                    cspcf_season.drop(
                                        dt_cols, 1).values.copy(),
                                    reductions_considered_csp,
                                    combine_profiles=True)
                        cc_csp = cc_storage_csp(
                            required_MWhs_csp.copy(), csp_powers.copy(),
                            csp_fleet_MWh, csp_fleet_MW)

                        # Clip load according to existing csp cc
                        net_load_profile_stor_adj = np.clip(
                            net_load_profile_stor_adj, a_min=None,
                            a_max=(max(net_load_profile_stor_adj)
                                   - (csp_fleet_MW * cc_csp)),
                            out=net_load_profile_stor_adj)

                    # If there is no existing CSP then it gets no capacity
                    # credit
                    else:
                        cc_csp = 0

                # Collect and organize the results
                all_cc = get_csp_cc(resources_ccreg_csp, cap_csp_ccreg,
                                    cc_csp, next_year, all_cc, season)

            if not resources_ccreg_csp.empty:
                if calc_csp == '0':
                    # Set the marginal CC for CSP equal to 1
                    all_cc_mar = csp_cc_marg_equals1(resources_ccreg_csp,
                                                     next_year, all_cc_mar,
                                                     season)

                if calc_csp == '1':
                    # Call csp storage marginal cc functions for each csp
                    # resource
                    reductions_considered_csp_marg = int(marg_CSP_step_MW //
                                                         csp_step_size)
                    if mult_year:
                        all_cc_mar = calc_marg_cc_csp(
                            net_load_profile_stor_adj, cspcf_season_all,
                            resources_ccreg_csp, marg_CSP_step_MW,
                            reductions_considered_csp_marg, next_year,
                            all_cc_mar, season, mult_year,
                            load_profile_season, dt_cols, years=years)
                    else:
                        all_cc_mar = calc_marg_cc_csp(
                            net_load_profile_stor_adj, cspcf_season_all,
                            resources_ccreg_csp, marg_CSP_step_MW,
                            reductions_considered_csp_marg, next_year,
                            all_cc_mar, season, mult_year,
                            load_profile_season, dt_cols)

#%%  WRITE DATA TO GDX FILE

    # -------------- RENAMING SEASONS TO MATCH REEDS CONVENTION ---------------
    all_cc = all_cc.replace('winter', 'wint')  # to_replace, value
    all_cc = all_cc.replace('spring', 'spri')
    all_cc = all_cc.replace('summer', 'summ')
    all_cc_mar = all_cc_mar.replace('winter', 'wint')
    all_cc_mar = all_cc_mar.replace('spring', 'spri')
    all_cc_mar = all_cc_mar.replace('summer', 'summ')
    peaking_stor_all = peaking_stor_all.replace('winter', 'wint')
    peaking_stor_all = peaking_stor_all.replace('spring', 'spri')
    peaking_stor_all = peaking_stor_all.replace('summer', 'summ')
    timeslice_hours_all = timeslice_hours_all.replace('winter', 'wint')
    timeslice_hours_all = timeslice_hours_all.replace('spring', 'spri')
    timeslice_hours_all = timeslice_hours_all.replace('summer', 'summ')

    # --------------- RENAME COLUMNS TO MATCH REEDS CONVENTION ----------------

    all_cc_mar.columns = ['i', 'r', 'szn', 't', 'value']
    all_cc.columns = ['i', 'r', 'szn', 't', 'value']
    peaking_stor_all.columns = ['ccreg', 'szn', 'bin', 't', 'MW']
    timeslice_hours_all.columns = ['h', 'ccreg', 'szn', 'value']

    # ---------------- WRITE OUT A GDX FILE WITH THE OUTPUTS FOR REEDS --------

    outputs = {
                'cc_mar':        all_cc_mar,
                'cc_old':        all_cc,
                'peak_h_frac':   timeslice_hours_all,
                'sdbin_size':    peaking_stor_all
                }

    return outputs
    #%%


# ------------------ CALC CC OF EXISTING VG RESOURCES -------------------------
def cc_vg(vg_power, load, vg_marg_power, top_hours_n, cap_marg):
    '''
    Calculate the capacity credit of existing and marginal variable generation
    capacity using a top hour approximation. More details on the methodology
    used in this approximation can be found here: <file location>
    Args:
        vg_power: numpy matrix containing power output profiles for all
            hours_n for each variable generating resource
        load: numpy array containing time-synchronous load profile for all
            hours_n. Units: MW
        cf_marg: numpy array containing capacity factor profiles for marginal
            builds of each variable generating resource
        top_hours_n: number of top hours to consider for the calculation
        cap_marg: marginal capacity used to calculate marginal capacity credit
    Returns:
        cc_marg: marginal capacity credit for each variable generating resource
        load_net: net load profile. Units: MW
        top_hours_net: arguments for the highest net load hours in load_net,
            length top_hours_n
        top_hours: argumnets for the highest load hours in load, length
            top_hours_n
    To Do:
        Currently only built for hourly profiles. Generalize to any duration
            timestep.
    '''

    # number of hours in the load and CF profiles
    hours_n = len(load)

    # get the net load that must be met with conventional generation
    load_net = load - np.sum(vg_power, axis=1)

    # get the indices of the top hours of net load
    top_hours_net = load_net.argsort()[
        np.arange(hours_n-1, (hours_n-top_hours_n)-1, -1)]

    # get the indices of the top hours of load
    top_hours = load.argsort()[
        np.arange(hours_n-1, (hours_n-top_hours_n)-1, -1)]

    # get the differences and reductions in load as well as the ratio between
    # the two
    load_dif = load[top_hours] - load_net[top_hours]
    load_reduct = load[top_hours] - load_net[top_hours_net]
    load_ratio = np.tile(np.divide(
        load_reduct, load_dif, out=np.zeros_like(load_reduct),
        where=load_dif != 0).reshape(top_hours_n, 1),
        (1, len(vg_power[0, :])))
    # get the existing cc for each resource
    gen_tech = vg_power[top_hours_net, :] + np.where(
        load_ratio < 1, vg_power[top_hours, :]*load_ratio,
        vg_power[top_hours, :])
    gen_sum = np.tile(np.sum(gen_tech, axis=1).reshape(top_hours_n, 1),
                      (1, len(vg_power[0, :])))
    gen_frac = np.divide(gen_tech, gen_sum, out=np.zeros_like(gen_tech),
                         where=gen_sum != 0)
    cap_useful_MW = (np.sum(gen_frac * np.tile(
        load_reduct.reshape(top_hours_n, 1), (1, len(vg_power[0, :]))),
        axis=0) / top_hours_n).reshape(len(vg_power[0, :]), 1)

    # get the marg net load for each VG resource
    load_marg = np.tile(load_net.reshape(hours_n, 1),
                        (1, len(vg_marg_power[0, :]))) - vg_marg_power

    # sort each marginal load profile
    for n in np.arange(0, len(vg_marg_power[0, :]), 1):
        load_marg[:, n] = np.flip(load_marg[np.argsort(load_marg[:, n],
                                                       axis=0), n], axis=0)

    # get the reductions in load for each resource
    load_reduct_marg = np.tile(
        load_net[top_hours_net].reshape(top_hours_n, 1),
        (1, len(vg_marg_power[0, :]))) - load_marg[0: top_hours_n, :]

    # get the marginal CCs for each resource
    cc_marg = (np.sum(load_reduct_marg, axis=0) / top_hours_n) / cap_marg

    # setting the lower bound for marginal CC to be 0.01
    cc_marg[cc_marg < 0.01] = 0.0

    # rounding outputs to the nearest 5 decimal points
    load_net = np.around(load_net, decimals=5)
    cc_marg = np.around(cc_marg, decimals=5)
    cap_useful_MW = np.around(cap_useful_MW, decimals=5)
    top_hours_net = np.around(top_hours_net, decimals=5)

    results = {
                'load_net': load_net,
                'cc_marg': cc_marg,
                'cap_useful_MW': cap_useful_MW,
                'top_hours_net': top_hours_net,
                }

    return results


# -----------------------CALC REQUIRED MWHS CSP--------------------------------
def calc_required_mwh_csp(load_profile, cspcaps, solar_multiples, cspcfs, inc,
                          combine_profiles=False):
    '''
    Determine the energy storage capacity required to acheive a certain peak
        load reduction for a given load profile
    Args:
        load_profile: time-synchronous load profile
        cspcaps: array of csp capacities by tech, type, and region
        solar_multiples: solar multiples of charging capacity to generator size
        cspcfs: matrix of csp profiles by tech and region
        inc: number of peak reductions considered
        combine_profiles: this set set to true for calculating existing CC of
            CSP so that all existing is treated at once
    Returns:
        required_MWhs: set of energy storage capacities required for each peak
            reduction size
        csp_powers: set of peak reduction sizes corresponding to required_MWhs
    '''

    csps = len(cspcaps)
    hours_n = len(load_profile)

    # Adjust the cf profiles by the solar multiple
    cspcfs *= solar_multiples
    cspcfs = cspcfs.T

    csp_charge = cspcfs * cspcaps.reshape(csps, 1)

    # Combine charging profiles only for CC of existing CSP
    if combine_profiles:
        csp_charge = csp_charge.sum(axis=0).reshape(1, hours_n)

        poss_charges = np.zeros((inc, hours_n))
        for i in range(0, hours_n):
            poss_charges[:, i] = np.linspace(0, csp_charge[0, i], inc)

        peak_reductions = np.linspace(0, cspcaps.sum(axis=0), inc)

    else:
        poss_charges = csp_charge.copy()
        peak_reductions = cspcaps.copy()

    csp_powers = peak_reductions.reshape(inc, 1)

    max_demands = np.tile(
        (np.max(load_profile) - peak_reductions).reshape(inc, 1), (1, hours_n))

    necessary_discharges = (max_demands - load_profile)

    # Note CSP can charge while discharging
    necessary_discharges = np.clip(necessary_discharges, a_min=None,
                                   a_max=0.0, out=necessary_discharges)
    poss_batt_changes = poss_charges + necessary_discharges

    batt_e_level = np.zeros([inc, hours_n])
    batt_e_level[:, 0] = np.minimum(poss_batt_changes[:, 0], 0)
    for n in np.arange(1, hours_n):
        batt_e_level[:, n] = batt_e_level[:, n-1] + poss_batt_changes[:, n]
        batt_e_level[:, n] = np.clip(batt_e_level[:, n], a_min=None,
                                     a_max=0.0, out=batt_e_level[:, n])

    required_MWhs = -np.min(batt_e_level, axis=1)

    return required_MWhs, csp_powers


# -------------------------CALC REQUIRED MWHS----------------------------------
def calc_required_mwh(load_profile, peak_reductions, eff_charge, stor_buffer_minutes):
    '''
    Determine the energy storage capacity required to acheive a certain peak
        load reduction for a given load profile
    Args:
        load_profile: time-synchronous load profile
        peak_reductions: set of peak reductions (in MW) to be tested
        eff_charge: RTE of charging
    Returns:
        required_MWhs: set of energy storage capacities required for each peak
            reduction size
        batt_powers: corresponding peak reduction sizes for required_MWhs
    '''

    hours_n = len(load_profile)

    inc = len(peak_reductions)
    max_demands = np.tile(
        (np.max(load_profile) - peak_reductions).reshape(inc, 1), (1, hours_n))
    batt_powers = np.tile(peak_reductions.reshape(inc, 1), (1, hours_n))

    poss_charges = np.minimum(batt_powers * eff_charge,
                              (max_demands - load_profile) * eff_charge)
    necessary_discharges = (max_demands - load_profile)

    poss_batt_changes = np.where(necessary_discharges <= 0,
                                 necessary_discharges, poss_charges)

    batt_e_level = np.zeros([inc, hours_n])
    batt_e_level[:, 0] = np.minimum(poss_batt_changes[:, 0], 0)
    for n in np.arange(1, hours_n):
        batt_e_level[:, n] = batt_e_level[:, n-1] + poss_batt_changes[:, n]
        batt_e_level[:, n] = np.clip(batt_e_level[:, n], a_min=None,
                                     a_max=0.0, out=batt_e_level[:, n])

    required_MWhs = -np.min(batt_e_level, axis=1)

# This line of code will implement a buffer on all storage duration
# requirements, i.e. if the stor_buffer_minutes is set to 60 minutes
# then a 2-hour peak would be served by a 3-hour device, a 3-hour peak
# by a 4-hour device, etc.
    stor_buffer_hrs = stor_buffer_minutes / 60
    required_MWhs = required_MWhs + (batt_powers[:, 0] * stor_buffer_hrs)

    return required_MWhs, batt_powers


# -------------------------CALC REQUIRED MWHS----------------------------------
def fill_in_charging(load_profile, peak_reductions, eff_charge,
                     storage_fleet_MWh, storage_fleet_MW):
    '''
    Fill in the load profile with the storage charging load
    Args:
        load_profile: time-synchronous load profile
        peak_reductions: peak reduction acheived as determined from the
            existing storage cc calculations
        eff_charge: charging efficiency of storage
        storage_fleet_MWh: energy capacity of the conventional storage fleet
    Returns:
        load_profile: load profile adjusted for conventional storage charging
    '''

    hours_n = len(load_profile)

    inc = len(peak_reductions)
    max_demands = np.tile(
        (np.max(load_profile) - peak_reductions).reshape(inc, 1), (1, hours_n))
    batt_powers = np.tile(storage_fleet_MW.reshape(inc, 1), (1, hours_n))

    poss_charges = np.minimum(batt_powers * eff_charge,
                              (max_demands - load_profile) * eff_charge)
    necessary_discharges = (max_demands - load_profile)

    poss_batt_changes = np.where(necessary_discharges <= 0,
                                 necessary_discharges, poss_charges)

    batt_e_level = np.zeros([inc, hours_n])
    batt_e_level[:, 0] = np.minimum(poss_batt_changes[:, 0], 0)
    for n in np.arange(1, hours_n):
        batt_e_level[:, n] = batt_e_level[:, n-1] + poss_batt_changes[:, n]
        batt_e_level[:, n] = np.clip(batt_e_level[:, n], a_min=None,
                                     a_max=0.0, out=batt_e_level[:, n])

    # Get the time blocks for storage charging
    discharging_hours = np.argwhere(poss_batt_changes <= 0)[:, 1]
    charging_hours = np.argwhere(poss_batt_changes > 0)[:, 1]
    df = pd.DataFrame(columns=['hour', 'discharge', 'potential', 'load',
                               'block'])
    df['hour'] = np.arange(0, hours_n)
    df.loc[discharging_hours, 'discharge'] = poss_batt_changes[
        0, discharging_hours]
    df.loc[charging_hours, 'potential'] = poss_batt_changes[0, charging_hours]
    df['load'] = load_profile
    df['block'] = -1
    df.fillna(0, inplace=True)
    charge_blocks = pd.DataFrame(columns=['end discharge', 'begin discharge'])
    block = []
    for i in np.arange(1, len(discharging_hours - 1), 1):
        if discharging_hours[i] != discharging_hours[i-1] + 1:
            block.extend(discharging_hours[i-1:i+1])
            charge_blocks.loc[len(charge_blocks), :] = block
            block = []
    if poss_batt_changes[0, 0] > 0:
        charge_blocks.loc[-1, :] = [-1, discharging_hours[0]]
        charge_blocks.index += 1
        charge_blocks.sort_index(inplace=True)
    charge_blocks.loc[len(charge_blocks), :] = [discharging_hours[-1],
                                                len(load_profile)]
    # Get the energy requirements for meeting peak discharging
    charge_blocks = charge_blocks.astype(int)
    for i in np.arange(0, len(charge_blocks)-1, 1):
        charge_blocks.loc[i, 'required_MWh'] = -np.min(batt_e_level[
            0, charge_blocks.loc[i, 'begin discharge']:charge_blocks.loc[
                i+1, 'end discharge'] + 1])
    charge_blocks.fillna(0, inplace=True)
    charge_blocks['MWh_charged'] = 0
    # Optimize charging
    for i in range(0, len(charge_blocks)):
        df.loc[charge_blocks.loc[i, 'end discharge']+1:charge_blocks.loc[
            i, 'begin discharge']-1, 'block'] = i
        t0 = charge_blocks.loc[i, 'begin discharge']
        MWh_needed = charge_blocks.loc[0: i, 'required_MWh'].sum() \
            - charge_blocks.loc[0: i, 'MWh_charged'].sum()
        MWh = 0.0
        df_subset = df[df['hour'] < t0].reset_index(drop=True)
        df_subset = df_subset[df_subset['potential'] > 0].reset_index(
            drop=True)
        df_subset = df_subset.sort_values('load').reset_index(drop=True)
        hour = 0
        while MWh_needed > MWh:
            try:
                MWh_add = min(df_subset.loc[hour, 'potential'],
                              MWh_needed - MWh)
                Hr = df_subset.loc[hour, 'hour']
                Blk = df_subset.loc[hour, 'block']
                val = charge_blocks.loc[Blk, 'MWh_charged'] + MWh_add
                if val > storage_fleet_MWh:
                    MWh_add = storage_fleet_MWh \
                        - charge_blocks.loc[Blk, 'MWh_charged']
                    df.loc[df['block'] == Blk, 'potential'] = 0
                    df_subset = df_subset[
                        df_subset['block'] != Blk].reset_index(drop=True)
                else:
                    df.loc[Hr, 'potential'] -= MWh_add
                df.loc[Hr, 'load'] += MWh_add / eff_charge
                load_profile[Hr] += MWh_add / eff_charge
            except:
                MWh_add = MWh_needed - MWh
            charge_blocks.loc[Blk, 'MWh_charged'] += MWh_add
            hour += 1
            MWh += MWh_add

    load_profile = np.clip(load_profile, a_min=None, a_max=max_demands[0, 0],
                           out=load_profile)

    return load_profile


# --------------------- CALC CC OF MARGINAL STORAGE ---------------------------
def cc_storage_csp(required_MWhs, batt_powers, stor_MWh, stor_MW):
    '''Determine the capacity credit of CSP-TES
       Can use several discrete values for storage duration or a single value
       More details on the methodology used can be found here: <file location>
       Args:
           required_MWhs: energy storage capacities needed to satisfy
               associated demand reductions
           batt_powers: demand reductions explored
           stor_MWh: energy storage capacity of the existing fleet
           stor_MW: power storage capacity of the existing fleet
       Returns:
           cc_stor: capacity credit of the existing storage fleet
    '''

    stor_inc = len(required_MWhs)

    # cc for case where peak reduction equals installed power capacity
    if (required_MWhs[stor_inc-1] <= stor_MWh):
        # get CC of existing storage
        cc_stor = 1.0

    # existing cc calculation for case where peak reduction is less than
    # installed power capacity
    else:
        # get effective capacity of installed storage
        cap_eff = np.interp(stor_MWh, required_MWhs, batt_powers[:, 0])
        # get CC of existing storage
        cc_stor = cap_eff/stor_MW
        # rounding outputs to the nearest 5 decimal points
        cc_stor = np.around(cc_stor, decimals=5)

    return cc_stor


def cc_storage(storage, pr, re, sdb):
    '''Determine the amount of peaking capacity that can be provided by
       energy storage with incrementally increasing durations.
       Args:
           storage: cap_stor_ccreg - dataframe with existing storage capacity
           pr: peak_reductions - set of storage power capacities analyzed
           re: required_MWhs - set of corresponding energy capacities
           sdb: storage duration bins - set of storage duration bins in ReEDS
       Returns:
           cc: storage capacity credit
           peak_stor: peaking potential of storage by duration
    '''

    # Initializing terms
    ds = sdb.copy()
    min_bin = min(ds)
    ds.remove(min_bin)
    peak_stor = pd.DataFrame(columns=['peaking potential', 'existing power'])

    # Get the step size and make a smaller step size for interpolation
    p_step = (pr[1] - pr[0])
    rel_step = 100
    p_step_small = p_step / rel_step

    # Get duration and marginal duration as a function of storage penetration
    dur = np.zeros(len(pr))
    dur[1:] = re[1:] / pr[1:]
    dur = dur.round(3)
    dur_marg = np.zeros(len(pr))
    for i in range(1, len(pr)):
        dur_marg[i] = ((re[i] - re[i-1]) / (pr[i] - pr[i-1]))
    dur_marg = dur_marg.round(3)

    # Find the limit of 2-hour storage capacity
    dur_temp = dur[dur <= min_bin].copy()
    dur_marg_temp = dur_marg[dur_marg < float(min(ds))].copy()
    # If the storage potential for the lowest duration bin bleeds into the
    # marginal addition of the next storage bin, grab the capacity before the
    # marginal duration is equal to the duration of the next bin.
    if len(dur_marg_temp) < len(dur_temp):
        peak_stor.loc[min_bin, 'peaking potential'] = pr[len(dur_marg_temp)-1]
    # If there is storage potential for the lowest duration bin, find the
    # potential.
    elif len(dur_temp) > 1:
        # If the marginal duration is acceptable at the crossover point, find
        # the crossover point.
        lower_bound_p = pr[len(dur_temp) - 1]
        upper_bound_p = pr[len(dur_temp)]
        lower_bound_e = re[len(dur_temp) - 1]
        upper_bound_e = re[len(dur_temp)]
        min_p = np.linspace(lower_bound_p, upper_bound_p, (rel_step**2) + 1)
        min_e = np.linspace(lower_bound_e, upper_bound_e, (rel_step**2) + 1)
        min_dur = min_e / min_p
        min_dur_temp = min_dur[min_dur <= min_bin].copy()
        # Find the max addition that could be made without exceeding the
        # marginal duration limit.
        dur_marg_test = min(min(ds), dur_marg[len(dur_temp)])
        max_interp = ((p_step * (min(ds) - dur_marg_test))
                      / (min(ds) - min_bin)) + lower_bound_p
        # Set the peaking potential for the lowest bin to be the minimum
        # between the crossover point and the maximum allowed interpolated
        # value (limited by the marg duration and p_step size).
        peak_stor.loc[min_bin, 'peaking potential'] = min(
            max_interp, min_p[len(min_dur_temp) - 1])
    # If there is not storage potential for lowest duration bin, set it to 0.
    elif len(dur_temp) == 1:
        peak_stor.loc[min_bin, 'peaking potential'] = 0

    # Iterate through the rest of the storage duration bins to find the
    # peaking potential.
    for i in range(0, len(ds)):
        d = ds[i]
        try:
            d1 = ds[i+1]
        except:
            d1 = d * 2
        e_base = 0
        p_base = 0
        for key in peak_stor.index:
            e_base += peak_stor.loc[key, 'peaking potential'] * key
            p_base += peak_stor.loc[key, 'peaking potential']
        # First check to see if this bin size will be limited by marginal
        # duration.
        dur_marg_temp = dur_marg[dur_marg < float(d1)].copy()
        p_temp = pr[len(dur_marg_temp) - 1] - p_base
        e_temp = e_base + (p_temp * d)
        e_test = re[len(dur_marg_temp) - 1]
        if e_test <= e_temp:
            peak_stor.loc[d, 'peaking potential'] = p_temp
        else:
            # Now add small incremental capacity until we reach the crossover
            # point
            p = p_base
            condition = True
            while condition:
                p_test = p + p_step_small
                e_test = e_base + ((p_test - p_base) * d)
                if np.interp(p_test, pr, re) >= e_test:
                    condition = False
                else:
                    p += p_step_small
            # Find the max addition that could be made without exceeding the
            # marginal duration limit
            pr_temp = pr[pr <= p]
            dur_marg_test = dur_marg[len(pr_temp) - 1]
            max_interp = ((p_step * (d1 - dur_marg_test))
                          / (d1 - d)) + pr_temp[-1]
            # Set the peaking potential to be the minimum of the crossover
            # point and  maximum interpolation value (limited by the marg
            # duration and p_step size).
            peak_stor.loc[d, 'peaking potential'] = min(max_interp, p) - p_base

    peak_stor['existing power'] = 0

    # Allocate storage into bins to get the fleetwide capacity credit
    for i in range(0, len(storage)):
        p = storage.loc[i, 'MW']
        d = storage.loc[i, 'duration']
        if peak_stor.loc[d, 'peaking potential'] > peak_stor.loc[
                d, 'existing power'] + p:
            p_temp = peak_stor.loc[d, 'existing power']
            peak_stor.loc[d, 'existing power'] += p
            p -= (peak_stor.loc[d, 'peaking potential'] - p_temp)
        else:
            p -= (peak_stor.loc[d, 'peaking potential']
                  - peak_stor.loc[d, 'existing power'])
            peak_stor.loc[d, 'existing power'] = peak_stor.loc[
                d, 'peaking potential']
        if p > 0:
            ds_temp = [i for i in ds if i < d]
            ds_temp.reverse()
            for d1 in ds_temp:
                val = peak_stor.loc[d1, 'existing power'] + p
                if peak_stor.loc[d1, 'peaking potential'] > val:
                    p_temp = peak_stor.loc[d1, 'existing power']
                    peak_stor.loc[d1, 'existing power'] += p
                    p -= (peak_stor.loc[d1, 'peaking potential'] - p_temp)
                else:
                    p -= (peak_stor.loc[d1, 'peaking potential']
                          - peak_stor.loc[d1, 'existing power'])
                    peak_stor.loc[d1, 'existing power'] = peak_stor.loc[
                        d1, 'peaking potential']
                if p < 0:
                    break
        if p > 0:
            ds_temp = [i for i in ds if i > d]
            ds_temp.remove(max(ds_temp))
            for d1 in ds_temp:
                val = peak_stor.loc[d1, 'existing power'] + p * (d/d1)
                if peak_stor.loc[d1, 'peaking potential'] > val:
                    p_temp = peak_stor.loc[d1, 'existing power']
                    peak_stor.loc[d1, 'existing power'] += (p * (d/d1))
                    p -= (peak_stor.loc[d1, 'peaking potential']
                          - p_temp) * (d1/d)
                else:
                    p -= (peak_stor.loc[d1, 'peaking potential']
                          - peak_stor.loc[d1, 'existing power']) * (d1/d)
                    peak_stor.loc[d1, 'existing power'] = peak_stor.loc[
                        d1, 'peaking potential']
                if p < 0:
                    break
        if p > 0:
            d_max = max(ds)
            peak_stor.loc[d_max, 'existing power'] = min(
                peak_stor.loc[d_max, 'peaking potential'],
                peak_stor.loc[d_max, 'existing power'] + (p * (d/d_max)))

    peak_stor['remaining potential'] = peak_stor['peaking potential'] \
        - peak_stor['existing power']

    # Capacity credit of existing storage is approximated here so that the
    # load profile can be adjusted before the assessment of the marginal
    # capacity credit of CSP with thermal energy storage
    if storage.empty:
        cc = 0
    else:
        cc = peak_stor['existing power'].sum() / storage['MW'].sum()

    # Setting the data type for peaking potential so that it can be rounded
    # before sent back to ReEDS
    peak_stor['peaking potential'] = pd.to_numeric(
        peak_stor['peaking potential'])

    # CC is used to determine the peak shaving & charging needed to adjust the
    # load profile for marginal CSP-TES CC calculations.
    return cc, peak_stor[['peaking potential']].round(decimals=2).reset_index(
        ).rename(columns={'index': 'duration', 'peaking potential': 'MW'})


def get_top_hours(hdtmap, top_hr_results, ccreg, df, season):
    '''
    Getting the top hours by timeslice that were used to compute capacity
    credit
    '''
#    hdtmap = dt_season.reset_index()
#    top_hr_results = cc_vg_results['top_hours_net'].copy()
#    df = timeslice_hours_all

    temp = hdtmap.loc[hdtmap.index.isin(top_hr_results), 'h'].value_counts() \
        / len(top_hr_results)
    temp = temp.reset_index().rename(columns={'index': 'h', 'h': '%TopHrs'})
    temp['ccreg'] = ccreg
    if not season == 'year':
        temp['season'] = season
    df = pd.concat([df, temp[list(df)]], sort=False).reset_index(drop=True)

    return df


def get_vg_cc(resources_ccreg, next_year, cc_results, cap_frac_cspns,
              hierarchy, ccreg, df, season):
    '''
    Getting the capacity credit of existing VG capacity.
    This function finds where csp-ns was added to upv capacity and allocates
    the credit accordingly.
    '''
#    cc_results = cc_vg_results['cap_useful_MW'].copy()
#    df = all_cc.copy()

    temp_cap_frac = cap_frac_cspns[cap_frac_cspns['r'].isin(
        hierarchy[hierarchy['ccreg'] == ccreg]['r'])]
    temp = resources_ccreg[['i', 'r']].copy()
    temp['t'] = str(next_year)
    temp['MW'] = cc_results
    temp_csp = pd.merge(left=temp, right=temp_cap_frac, on=['i', 'r'],
                        how='right')
    temp = pd.merge(left=temp, right=temp_cap_frac, on=['i', 'r'],
                    how='left').fillna(0)
    temp = temp[temp['rs'] == 0].reset_index(drop=True)
    temp = temp[['i', 'r', 't', 'MW']]
    temp_upv = temp_csp.groupby(['i', 'r', 't'], as_index=False).agg(
        {'MW': 'mean', 'cspns_frac': 'sum'})
    temp_upv['upv_frac'] = 1 - temp_upv['cspns_frac']
    temp_upv['MW'] *= temp_upv['upv_frac']
    temp_upv = temp_upv[['i', 'r', 't', 'MW']]
    temp_csp['i'] = 'csp-ns'
    temp_csp.drop('r', 1, inplace=True)
    temp_csp.rename(columns={'rs': 'r'}, inplace=True)
    temp_csp['MW'] *= temp_csp['cspns_frac']
    temp_csp = temp_csp[['i', 'r', 't', 'MW']]
    temp_upv_csp = pd.concat([temp_upv, temp_csp],
                             sort=False).reset_index(drop=True)
    temp = pd.concat([temp, temp_upv_csp], sort=False).reset_index(drop=True)
    all_rs = hierarchy[hierarchy['ccreg'] == ccreg]['rs'].drop_duplicates(
        ).tolist()
    for rs in all_rs:
        if rs not in temp_csp['r'].tolist():
            temp.loc[len(temp), :] = ['csp-ns', rs, str(next_year), 0]
    if not season == 'year':
        temp['season'] = season
    df = pd.concat([df, temp[list(df)]], sort=False).reset_index(drop=True)

    return df


def get_vg_cc_marg(resources_ccreg, next_year, cc_results, hierarchy, df,
                   season, techs):
    '''
    Getting the marginal capacity credit of VG
    This function assigns csp-ns the same marginal capacity credit as the best
    upv resource in that region
    '''
#    cc_results = cc_vg_results['cc_marg'].copy()
#    df = all_cc_mar.copy()

    temp = resources_ccreg[['i', 'r']].copy()
    temp['t'] = str(next_year)
    temp['CC'] = cc_results
    resources_upv = resources_ccreg[resources_ccreg['i'].isin(
        techs['UPV'])].reset_index(drop=True)
    best_resources_upv = resources_upv[['i', 'r']].drop_duplicates(
        subset='r', keep='last').reset_index(drop=True)
    temp_csp = pd.merge(left=temp, right=best_resources_upv, on=['i', 'r'],
                        how='right')
    temp_csp = pd.merge(left=temp_csp,
                        right=hierarchy[['r', 'rs']].drop_duplicates(),
                        on='r', how='left')
    temp_csp['i'] = 'csp-ns'
    temp_csp.drop('r', 1, inplace=True)
    temp_csp.rename(columns={'rs': 'r'}, inplace=True)
    temp = pd.concat([temp, temp_csp], sort=False).reset_index(drop=True)
    if not season == 'year':
        temp['season'] = season
    df = pd.concat([df, temp[list(df)]], sort=False).reset_index(drop=True)

    return df


def get_peaking_stor(results, ccreg, next_year, df, season, safety_bin,
                     safety_bin_size):
    '''
    Getting the peaking storage potential
    '''
#    results = peaking_stor.copy()
#    df = peaking_stor_all.copy()

    results['ccreg'] = ccreg
    results['t'] = str(next_year)
    if not season == 'year':
        results['season'] = season
        results = results[['ccreg', 'season', 'duration', 't', 'MW']].copy()
        results.loc[len(results), :] = [ccreg, season, safety_bin,
                                        str(next_year), safety_bin_size]
    else:
        results = results[['ccreg', 'duration', 't', 'MW']]
        results.loc[len(results), :] = [ccreg, safety_bin, str(next_year),
                                        safety_bin_size]
    results.duration = results.duration.astype(int).astype(str)
    df = pd.concat([df, results[list(df)]], sort=False).reset_index(drop=True)

    return df


def get_csp_cc(resources_ccreg_csp, cap_csp_ccreg, annual_cc_csp, next_year,
               df, season):
    '''
    Getting the capacity credit of CSP-TES
    '''
#    df = all_cc.copy()

    temp = resources_ccreg_csp[['i', 'r', 'resource']].copy()
    temp = pd.merge(left=temp,
                    right=cap_csp_ccreg[['i', 'r', 'resource', 'MW']],
                    on=['i', 'r', 'resource'], how='left').fillna(0)
    temp['MW'] *= annual_cc_csp
    temp['t'] = str(next_year)
    temp.drop('resource', 1, inplace=True)
    if not season == 'year':
        temp['season'] = season
    df = pd.concat([df, temp[list(df)]], sort=False).reset_index(drop=True)

    return df


def csp_cc_marg_equals1(resources_csp_ccreg, next_year, df, season):
    '''
    Setting the marginal cc of CSP-TES equal to 1
    '''
#    df = all_cc_mar.copy()

    temp = resources_csp_ccreg[['i', 'r']].copy()
    temp['t'] = str(next_year)
    temp['CC'] = 1
    if not season == 'year':
        temp['season'] = season
    df = pd.concat([df, temp[list(df)]], sort=False).reset_index(drop=True)

    return df


def calc_marg_cc_csp(net_load_profile, cspcf_used, resources_ccreg_csp,
                     marg_CSP_step_MW, reductions_considered, next_year, df,
                     season, mult_year, load_profile_season, dt_cols,
                     years=None):
    '''
    Calculating the marginal cc of csp
    '''
#    net_load_profile = net_load_profile_stor_adj.copy()
#    cspcf_used = cspcf_season_all.copy()
#    df = all_cc_mar.copy()
#    reductions_considered = reductions_considered_csp_marg

    # Get the required MWhs for 1000 MW (or whatever step size is chosen) for
    # each resource
    peak_reductions = (np.ones((1, len(resources_ccreg_csp)))
                       * marg_CSP_step_MW).reshape(len(resources_ccreg_csp))
    required_MWhs_csp, csp_powers = calc_required_mwh_csp(
        net_load_profile.copy(), peak_reductions.copy(),
        resources_ccreg_csp['sm'].values.copy(),
        cspcf_used.drop(dt_cols, 1).values.copy(), len(resources_ccreg_csp))
    temp = resources_ccreg_csp[['i', 'r', 'duration', 'resource', 'sm']].copy()
    # Find all the resources where the marginal capacity credit will be less
    # than 1
    temp['MW'] = peak_reductions
    temp['required_MWh'] = required_MWhs_csp
    temp['MWh'] = temp['MW'] * temp['duration']
    temp_full = pd.DataFrame(columns=list(temp) + ['CC', 't'])
    temp_part = pd.DataFrame(columns=list(temp) + ['CC', 't'])
    for i in range(0, len(temp)):
        if temp.loc[i, 'required_MWh'] > temp.loc[i, 'MWh']:
            temp_part.loc[len(temp_part), :] = temp.loc[i, :]
        else:
            temp_full.loc[len(temp_full), :] = temp.loc[i, :]
    # For resources with full marginal capacity credit, assign this value
    if not temp_full.empty:
        temp_full['t'] = str(next_year)
        temp_full['CC'] = 1
        if not season == 'year':
            temp_full['season'] = season
        df = pd.concat([df, temp_full[list(df)]], sort=False).reset_index(
            drop=True)
    # For resources with partial capacity credit, do a full analysis of that
    # resource with its given profile
    if not temp_part.empty:
        for i in range(0, len(temp_part)):
            sm = temp_part.loc[i, 'sm']
            duration = temp_part.loc[i, 'duration']
            resource = temp_part.loc[i, 'resource']
            peak_reductions = np.linspace(0, marg_CSP_step_MW,
                                          reductions_considered)
            required_MWhs_part = np.array([])
            if mult_year:
                net_load_profile_timestamp = pd.DataFrame(
                    net_load_profile, load_profile_season.year)
                for y in years:
                    net_load_profile_temp = net_load_profile_timestamp[
                        net_load_profile_timestamp.index == y][0].values
                    cspcf_used_temp = cspcf_used[
                        cspcf_used['year'] == y].reset_index(drop=True)
                    required_MWhs_part_temp, csp_powers_part = \
                        calc_required_mwh_csp(
                            net_load_profile_temp.copy(),
                            peak_reductions.copy(), sm,
                            cspcf_used_temp[resource].values.copy(),
                            reductions_considered)
                    if years.index(y) == 0:
                        required_MWhs_part = required_MWhs_part_temp.copy()
                    else:
                        required_MWhs_part = np.maximum(
                            required_MWhs_part, required_MWhs_part_temp)
            else:
                # Call csp storage cc functions for existing csp
                required_MWhs_part, csp_powers_part = calc_required_mwh_csp(
                    net_load_profile, peak_reductions.copy(), sm,
                    cspcf_used[resource].values.copy(), reductions_considered)
            cc_csp_mar_part = cc_storage_csp(
                required_MWhs_part.copy(), csp_powers_part.copy(),
                marg_CSP_step_MW*duration, marg_CSP_step_MW)
            temp_part.loc[i, 'CC'] = cc_csp_mar_part
            temp_part.loc[i, 't'] = str(next_year)
            if not season == 'year':
                temp_part.loc[:, 'season'] = season
        df = pd.concat([df, temp_part[list(df)]],
                       sort=False).reset_index(drop=True)

    return df
