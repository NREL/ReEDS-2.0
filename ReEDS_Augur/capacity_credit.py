#%% IMPORTS
import os
import numpy as np
import pandas as pd
import gdxpds
import reeds


#%% Functions
def get_relative_step_sizes(t, yearset, target_step):
    '''
    Checking the relative ReEDS temporal step sizes for this solve year and
    any previous solve year, specified by 'target_step'
    '''
    i = yearset.index(t)
    tnext = yearset[i+1]

    j = yearset.index(target_step)
    targ_prev = yearset[j-1]

    relative_step_sizes = (tnext - t) / (target_step - targ_prev)
    return relative_step_sizes


def set_marg_vre_step_size(t, sw, gdx, hierarchy):
    '''
    Marginal vre step size has a default floor value of 1000 MW but
    here we check to see if it needs to be higher. The function looks
    back by the number of steps specified by 'marg_vre_steps' and computes
    the max of the average new vre investment in those previous steps.
    We take the max of that value and 1000 MW to set the set size.
    The fuction also accounts for potentially varying step sizes in ReEDS.

    Inputs
    * marg_vre_steps [int]: Number of previous solve years to consider when
      evaluating the marginal VRE step size (default: 2). Must be at least 1;
      a value of 2 can help reduce oscillations. Augur will automatically drop
      from consideration solves that are more than 5 years from the previous solve.
    '''
    # load yearset for getting various previous steps
    yearset = gdx['tmodel_new'].allt.astype(int).tolist()

    # collect list of previous years and their relative step sizes
    prev_year_list = []
    step_sizes = []
    for step in range(int(sw['marg_vre_steps'])):

        # try-except to handle cases where there aren't multiple
        # steps to go back to (e.g. running Augur after 1st solve)
        try:
            target_last_step = yearset[yearset.index(t)-step]

            # only look at steps beyond the previous year if the step sizes
            # are less than 5 years
            if (t - target_last_step) < 5:
                step_sizes.append(get_relative_step_sizes(t, yearset, target_last_step))
                prev_year_list.append(target_last_step)
        except Exception:
            print('First Augur year so no previous steps')

    relative_step_sizes = pd.DataFrame(list(zip(prev_year_list, step_sizes)),
                                            columns=['t', 'step'])

    # load investment data for all techs
    techs = gdx['i_subsets'].pivot(columns='i_subtech',index='i',values='Value')
    inv = gdx['inv_ivrt'].astype({'t':int})

    # get investment from any previous steps under consideration
    inv_last_years = inv[inv['t'].isin(prev_year_list)]
    inv_vre = inv_last_years[inv_last_years['i'].isin(techs['VRE'].dropna().index)]

    # map inv_vre to ccregions
    r_ccreg = hierarchy[['r','ccreg']].drop_duplicates()
    inv_vre = inv_vre.merge(r_ccreg, on = 'r')

    # aggregate by tech and then and compute average across the appropriate
    # geographic resolution - r for curtailment, ccreg for capacity credit
    level = 'ccreg'
    df = (
        inv_vre.groupby([level, 't'], as_index=False).Value.sum()
        .groupby(['t'], as_index=False).Value.mean()
    )
    # adjust each previous step by its relative step size
    df = df.merge(relative_step_sizes, on='t')
    df['Value'] *= df['step']

    # now get max across all previous steps and set as marg_vre_mw
    marg_vre_mw = round(df['Value'].max(), 0)

    marg_vre_mw_cc = int(max(int(sw['marg_vre_mw']), marg_vre_mw))
    print(f'marg_vre_mw_cc set to {marg_vre_mw_cc}')

    return marg_vre_mw_cc

def load_dr_data(csv_path,inputs_case,h_dt_szn,
                set_h_szn_cols=['h','ccseason','hour'],
                set_idx_cols=['h','hour', 'year','ccseason']):
    df = pd.read_csv(os.path.join(inputs_case,csv_path))
    df = pd.merge(df,h_dt_szn[set_h_szn_cols],on='hour',how='left')
    return df.set_index(set_idx_cols)
     

#%% Main function
def reeds_cc(t, tnext, casedir):
    '''
    This function directs all of the capacity credit calculations for ReEDS
    It writes out a gdx file which is then read back in to ReEDS during the
    next iteration.
    '''
    #%% Get the switches
    sw = reeds.io.get_switches(casedir)

    #%% Set up log
    log = reeds.log.makelog(
        'capacity_credit.py',
        os.path.join(sw['casedir'], 'gamslog.txt'),
    )

    #%% Load some inputs
    inputs_case = os.path.join(casedir, 'inputs_case')
    hierarchy = reeds.io.get_hierarchy(casedir).reset_index()
    resources = pd.read_csv(os.path.join(inputs_case, 'resources.csv'))
    
    augur_data = os.path.join(casedir,'ReEDS_Augur','augur_data')
    cap = pd.read_csv(os.path.join(augur_data, f'max_cap_{t}.csv'))

    gdx = gdxpds.to_dataframes(os.path.join(augur_data,f'reeds_data_{t}.gdx'))
    techs = gdx['i_subsets'].pivot(columns='i_subtech',index='i',values='Value')
    techs.columns = techs.columns.str.lower()
    r = gdx['rfeas']

    cap_stor = cap.loc[cap['i'].isin(gdx['storage_standalone'].i)].rename(columns={'Value':'MW'})
    cap_stor['duration'] = cap_stor.i.map(gdx['storage_duration'].set_index('i').Value)
    cap_stor['MWh'] = cap_stor['MW'] * cap_stor['duration']
    #Adding a check if there is no storage - populate with 0 MW and 0 MWh in each r
    if cap_stor.empty:
        stor_techs = gdx['storage_standalone'].i.tolist()
        r_values = r['r'].tolist()
        for tech_name in stor_techs:
            for r_val in r_values:
                        cap_stor.loc[len(cap_stor)] = [tech_name,'', r_val,  0, 0, 0]
                        cap_stor['duration'] = cap_stor.i.map(gdx['storage_duration'].set_index('i').Value)

    cap_stor_agg = cap_stor.merge(hierarchy[['r','ccreg']], on = 'r')
    cap_stor_agg = cap_stor_agg.groupby('ccreg', as_index=False)[['MW','MWh']].sum()
    sdb = gdx['sdbin'].rename(columns={'*':'bin'})[['bin']]

    ### Get the marginal step size
    marg_vre_mw_cc = set_marg_vre_step_size(t, sw, gdx, hierarchy)

    ### Get the non-duplicated profiles
    resource_profiles = resources.drop_duplicates('resource')

    # Remove the "8760" safety valve bin
    safety_bin = max(sdb['bin'].values)
    sdb = sdb[sdb['bin'] != max(sdb['bin'])]
    sdb = [int(x) for x in sdb['bin']]

    # Temporal definitions
    h_dt_szn = pd.read_csv(os.path.join('inputs_case', 'h_dt_szn.csv'))

    ccseasons = []
    if sw['cc_calc_annual']:
        ccseasons += ['year']
    if sw['cc_calc_seasonal']:
        ccseasons += h_dt_szn['ccseason'].drop_duplicates().tolist()

    ### Prepare the seasonal profiles
    ## vre_gen needs to have tech_class_r columns
    ## last version has (ccseason,year,h,hour) index
    vre_gen = pd.read_hdf(os.path.join(augur_data,f'vre_gen_exist_{t}.h5'))
    ## vre_cf_marg has same columns and index as vre_gen
    vre_cf_marg = pd.read_hdf(os.path.join(augur_data,f'vre_cf_marg_{t}.h5'))

    if int(sw['GSw_PRM_CapCreditMulti']) == 0:
        # Restrict capacity credit evaluation to use 2012 only (rather than multi-year)
        vre_gen = vre_gen[vre_gen.index.get_level_values('year') == 2012].copy()
        vre_cf_marg = vre_cf_marg[vre_cf_marg.index.get_level_values('year') == 2012].copy()

    vregen_ccseason = {}
    vregen_marginal_ccseason = {}
    for ccseason in ccseasons:
        if ccseason == 'year':
            vregen_ccseason[ccseason] = vre_gen
            vregen_marginal_ccseason[ccseason] = vre_cf_marg * marg_vre_mw_cc
        else:
            vregen_ccseason[ccseason] = vre_gen.loc[ccseason]
            vregen_marginal_ccseason[ccseason] = (vre_cf_marg * marg_vre_mw_cc).loc[ccseason]

    load_profiles = (
        # HOURLY_PROFILES['load'].profiles
        pd.read_hdf(os.path.join(augur_data,f'load_{t}.h5'))
        ### Map BA regions to ccreg's and sum over them
        .rename(columns=hierarchy.set_index('r').ccreg)
        .groupby(axis=1, level=0).sum()
    )

    if int(sw['GSw_PRM_CapCreditMulti']) == 0:
        # Restrict capacity credit evaluation to use 2012 only (rather than multi-year)
        load_profiles = load_profiles[load_profiles.index.get_level_values('year') == 2012].copy()

    if int(sw['GSw_DR']):
        # Get DR props
        marg_dr_props = gdx['storage_eff'][gdx['storage_eff']['i'].str.contains('dr1')]
        dr_hrs = pd.read_csv(os.path.join(inputs_case,'dr_hrs.csv'))
        dr_hrs['hrs'] = list(zip(dr_hrs.pos_hrs, -dr_hrs.neg_hrs))
        dr_hrs['max_hrs'] = 8760
        dr_shed = pd.read_csv(os.path.join(inputs_case,'dr_shed.csv'), header=None,names=['dr_type','max_hrs'])
        dr_shed['hrs'] = [(1, 1)]*len(dr_shed.index)
        dr_hrs = pd.concat([dr_hrs, dr_shed])
        dr_hrs.rename(columns={"dr_type": "i"},inplace=True)
        marg_dr_props.rename(columns={"Value":"RTE"},inplace=True)
        marg_dr_props = pd.merge(marg_dr_props, dr_hrs, on='i', how='right').drop_duplicates('i').set_index('i')
        # Fill missing data
        marg_dr_props.loc[marg_dr_props.RTE != marg_dr_props.RTE, 'RTE'] = 1
        marg_dr_props = marg_dr_props[['hrs', 'max_hrs', 'RTE']]
        drcf_inc = load_dr_data('dr_increase.csv',inputs_case,h_dt_szn)
        drcf_dec = load_dr_data('dr_decrease.csv',inputs_case,h_dt_szn)

    # Get EVMC data if necessary
    if int(sw['GSw_EVMC']):
        # Get EVMC props
        evmccf_shape_increase = load_dr_data('evmc_shape_profile_increase.csv',inputs_case,h_dt_szn)
        evmccf_shape_decrease = load_dr_data('evmc_shape_profile_decrease.csv',inputs_case,h_dt_szn)

    # Initialize dataframes to store results
    dict_cc_old = {}
    dict_cc_mar = {}
    dict_sdbin_size = {}
    dict_cc_dr = {}
    dict_net_load = {}
    dict_net_load_2012 = {}

    #%% Loop over CCREGs
    for ccreg in hierarchy['ccreg'].drop_duplicates():
        #%  CCREG DATA
        # ccreg = 'cc6'  # Uncomment for debugging
        # ------- Get load profile, RECF profiles, VG capacity, storage
        # capacity, and storage RTE for this CCREG -------

        log.info('Calculating capacity credit for {}'.format(ccreg))

        # Resources to be used
        resources_ccreg = resource_profiles[resource_profiles['ccreg'] == ccreg]
        resourcelist = (
            slice(None) if sw['cc_all_resources']
            else resources_ccreg.resource.tolist()
        )

        # Hourly profiles
        load_profile_ccreg = load_profiles[ccreg]
        # DR profile
        if int(sw['GSw_DR']):
            dr_reg = [r for r in resources_ccreg.r.drop_duplicates()
                      if r in drcf_inc.columns]
            dr_inc_ccreg = drcf_inc[['i'] + dr_reg]
            dr_reg = [r for r in resources_ccreg.r.drop_duplicates()
                      if r in drcf_dec.columns]
            dr_dec_ccreg = drcf_dec[['i'] + dr_reg]
        # EVMC profile
        if int(sw['GSw_EVMC']):
            evmc_shape_reg = [r for r in resources_ccreg.r.drop_duplicates()
                      if r in evmccf_shape_increase.columns]
            evmccf_shape_increase_ccreg = evmccf_shape_increase[['i'] + evmc_shape_reg]
            evmc_shape_reg = [r for r in resources_ccreg.r.drop_duplicates()
                      if r in evmccf_shape_decrease.columns]
            evmccf_shape_decrease_ccreg = evmccf_shape_decrease[['i'] + evmc_shape_reg]

        # Storage information
        # Note that we only calculate storage capacity credit for storage in the same ccreg
        cap_stor_agg_ccreg = cap_stor_agg[
            cap_stor_agg['ccreg'] == ccreg].reset_index(drop=True)

        cap_stor_ccreg = cap_stor[
            cap_stor['r'].isin(hierarchy[hierarchy['ccreg'] == ccreg]['r'])
        ].reset_index(drop=True)
        # df = cap_stor.assign(ccreg=cap_stor.r.map(hierarchy.set_index('r').ccreg))
        # df.groupby('ccreg').MW.max()
        # df.groupby('ccreg').MWh.max()

        try:
            eff_charge = cap_stor_agg_ccreg['rte'].values[0]
        except Exception:
            eff_charge = float(sw['cc_default_rte'])

        max_demand = load_profile_ccreg.max() / (1/float(sw['cc_max_stor_pen']))
        reductions_considered = int(max_demand // float(sw['cc_stor_stepsize']))
        peak_reductions = np.linspace(0, max_demand, reductions_considered)
        #Skip CC calculation if number of reductions_considered is only 1. Avoids error in interpolation within cc_storage function.
        if reductions_considered == 1:
            continue

        # log.debug(f'max_demand = {max_demand}')
        # log.debug(f'reductions_considered = {reductions_considered}')
        # log.debug(f'peak_reductions diff = {peak_reductions[1] - peak_reductions[0]}')

        # ---------------------------- CALL FUNCTIONS -------------------------
        #%%  Loop over ccseasons
        for ccseason in ccseasons:
            #%%
            # ccseason = 'winter'  # Uncomment for debugging
            # Get the load and CF profiles for this ccseason
            if ccseason == 'year':
                load_profile_ccseason = load_profile_ccreg.copy()
                hours_considered = int(sw['cc_ann_hours'])
                if int(sw['GSw_DR']):
                    dr_inc_ccseason = dr_inc_ccreg.copy()
                    dr_dec_ccseason = dr_dec_ccreg.copy()
                if int(sw['GSw_EVMC']):
                    evmc_shape_load_ccseason = evmccf_shape_increase_ccreg.copy()
                    evmc_shape_gen_ccseason = evmccf_shape_decrease_ccreg.copy()

            else:
                load_profile_ccseason = load_profile_ccreg.xs(
                    ccseason, axis=0, level='ccseason').reset_index()
                hours_considered = int(sw['GSw_PRM_CapCreditHours'])

                if int(sw['GSw_DR']):
                    dr_inc_ccseason = dr_inc_ccreg.xs(
                        ccseason, axis=0, level='ccseason').reset_index()
                    dr_dec_ccseason = dr_dec_ccreg.xs(
                        ccseason, axis=0, level='ccseason').reset_index()
                if int(sw['GSw_EVMC']):
                    evmc_shape_load_ccseason = evmccf_shape_increase_ccreg.xs(
                        ccseason, axis=0, level='ccseason').reset_index()
                    evmc_shape_gen_ccseason = evmccf_shape_decrease_ccreg.xs(
                        ccseason, axis=0, level='ccseason').reset_index()

            # log.debug(ccseason, int(len(load_profile_ccseason) / 7))
            ###### Calculate the capacity credit for each resource
            cc_vg_results = cc_vg(
                vg_power=vregen_ccseason[ccseason][resourcelist].values,
                load=load_profile_ccseason[ccreg].values,
                vg_marg_power=vregen_marginal_ccseason[ccseason][resourcelist].values,
                top_hours_n=hours_considered, cap_marg=marg_vre_mw_cc)

            ###### Store the existing and marginal capacity credit results
            dict_cc_old[ccreg, ccseason] = pd.DataFrame({
                'resource': resource_profiles.set_index('resource').loc[resourcelist].index,
                'MW': cc_vg_results['cap_useful_MW'][:,0],
            })

            dict_cc_mar[ccreg, ccseason] = (
                resource_profiles.loc[resource_profiles.resource.isin(resourcelist)]
                .drop('ccreg', axis=1)
                .assign(CC=cc_vg_results['cc_marg'])
            )

            net_load_ccreg_ccseason = (
                load_profile_ccseason.drop(columns=ccreg)
                .assign(MW=cc_vg_results['load_net'])
                .sort_values(['MW'], ascending=False)
            )
            #Save top n hrs of net load for ccreg and ccseason across all years, and for 2012 alone
            net_load_out_numhrs = 500
            dict_net_load[ccreg, ccseason] = net_load_ccreg_ccseason.head(net_load_out_numhrs)
            dict_net_load_2012[ccreg, ccseason] = (
                net_load_ccreg_ccseason[net_load_ccreg_ccseason['year']==2012].head(net_load_out_numhrs)
            )

            ###### Calculate the storage capacity credit
            # The call to this function gives the MWh required for each
            # peak reduction capacity. For each data year, loop through
            # and get get the MWh needed for each peak reduction capacity.
            # Get a "ccseason_required_MWhs" for each year.
            # Get the maximum value for each position in the array.
            # Make a new "ccseason_required_MWhs" array to send to the
            # cc_storage function.
            # Call storage cc functions for existing and marginal
            # conventional storage.
            net_load_profile_timestamp = pd.DataFrame(
                cc_vg_results['load_net'], load_profile_ccseason.year)
            years = list(net_load_profile_timestamp.index.unique())

            for y in years:
                net_load_profile_temp = net_load_profile_timestamp.iloc[
                    :, 0][net_load_profile_timestamp.index == y].to_numpy()
                required_MWhs_temp, batt_powers = calc_required_mwh(
                    load_profile=net_load_profile_temp.copy(),
                    peak_reductions=peak_reductions.copy(),
                    eff_charge=eff_charge, stor_buffer_minutes=float(sw['cc_stor_buffer']))

                if years.index(y) == 0:
                    required_MWhs = required_MWhs_temp.copy()
                else:
                    required_MWhs = np.maximum(required_MWhs, required_MWhs_temp)

            # Get the peaking storage potential by duration
            peaking_stor = cc_storage(
                storage=cap_stor_ccreg.copy(), pr=peak_reductions.copy(),
                re=required_MWhs.copy(), sdb=sdb.copy(), log=log)
            # Store it
            dict_sdbin_size[ccreg, ccseason] = pd.concat([
                peaking_stor[['duration','MW']],
                ### Add the safety bin
                pd.DataFrame(
                    {'duration': [safety_bin], 'MW': float(sw['cc_safety_bin_size'])}
                ),
            ], ignore_index=True)
            
            def pivot_melt_data(df):
                return pd.pivot_table(
                    pd.melt(df,
                        id_vars=['h','year','hour','i'],
                        var_name='r'),
                index=['year','hour','h'],
                columns=['i','r'], values='value')

            if int(sw['GSw_EVMC']):
                evmc_shape_inc_timestamp = pivot_melt_data(evmc_shape_load_ccseason)
                evmc_shape_dec_timestamp = pivot_melt_data(evmc_shape_gen_ccseason)
                evmc_years = evmc_shape_dec_timestamp.index.get_level_values('year').unique()
                #do as evmc cap credit instead?
                if len(evmc_years)==1:
                    gen_array = evmc_shape_dec_timestamp.values - evmc_shape_inc_timestamp.values 
                    evmc_shape_marg_power = np.tile(gen_array,(7,1))
                elif len(evmc_years)==7:
                    evmc_shape_marg_power = evmc_shape_dec_timestamp.values - evmc_shape_inc_timestamp.values 
                else:
                    log.info("no weather year data on EVMC for any relevant regions; skipping")
                    continue
                
                ###### Calculate the capacity credit for each evmc_shape resource
                results_evmc_shape = cc_evmc_shape(load=cc_vg_results['load'],
                    load_net=cc_vg_results['load_net'],
                    top_hours_net=cc_vg_results['top_hours_net'],
                    top_hours_n=hours_considered,
                    evmc_shape_marg_power=evmc_shape_marg_power*float(sw['marg_dr_mw']),
                    cap_marg=float(sw['marg_dr_mw']))

                evmc_cc_i = pd.melt(pd.DataFrame(data=[np.round(results_evmc_shape, decimals=5), ],
                                        columns=evmc_shape_dec_timestamp.columns))

                if (ccreg, ccseason) in dict_cc_dr.keys():
                    dict_cc_dr[ccreg, ccseason] = pd.concat(
                    [dict_cc_dr[ccreg, ccseason],
                    evmc_cc_i[['r', 'i', 'value']]])
                else:
                    dict_cc_dr[ccreg, ccseason] = evmc_cc_i[['r', 'i', 'value']]
            
            if int(sw['GSw_DR']):
                # Pivot DR data
                inc_timestamp = pd.pivot_table(
                    pd.melt(dr_inc_ccseason,
                            id_vars=['h','year','hour','i'],
                            var_name='r'),
                    index=['h','year','hour'],
                    columns=['i','r'], values='value')
                dec_timestamp = pd.pivot_table(
                    pd.melt(dr_dec_ccseason,
                            id_vars=['h','year','hour','i'],
                            var_name='r'),
                    index=['h','year','hour'],
                    columns=['i','r'], values='value')
                # Loop through techs with a DR profile
                for i in dec_timestamp.columns.get_level_values(0).unique()[1:]:
                    if 2012 not in years:
                        log.info("WARNING!\nDR data does not exist for weather years "+
                                 "other than 2012.\nYou are running without 2012")
                    for y in years:
                        if y not in dec_timestamp.index.get_level_values('year').unique():
                            continue

                        # Get DR data in numpy array and multiply by marginal capacity
                        dec_temp = dec_timestamp[i].xs(y, level='year').values * float(sw['marg_dr_mw'])
                        if i in techs['dr2']:
                            # For shed, there is no increase in energy required so just make sure
                            # there is sufficient energy to shift into from the decrease hour
                            inc_temp = dec_temp.copy() * 2
                        else:
                            inc_temp = inc_timestamp[i].xs(y, level='year').values * float(sw['marg_dr_mw'])
                        # Replicate net load data for each DR type and region
                        net_load_profile_temp = net_load_profile_timestamp.iloc[
                            :, 0][net_load_profile_timestamp.index == y].to_numpy()

                        net_load_profile_temp = np.array([net_load_profile_temp, ]*len(dec_timestamp[i].columns)
                                                         ).transpose()
                        # Get load to shift out of top hours, analagous to curtailment
                        top_load = (net_load_profile_temp
                                    - (net_load_profile_temp.max() - float(sw['marg_dr_mw'])) )
                        tot_top_load = top_load.clip(min=0).sum(0)
                        top_load = top_load.clip(-inc_temp, dec_temp)
                        dr_cc_i = dr_capacity_credit(
                            hrs=marg_dr_props.loc[i, 'hrs'], eff=marg_dr_props.loc[i, 'RTE'],
                            ts_length=top_load.shape[0], poss_dr_changes=top_load,
                            marg_peak=tot_top_load, cols=dec_timestamp[i].columns,
                            maxhrs=marg_dr_props.loc[i, 'max_hrs'])

                        # If more than just 2012 DR year added, add min as above
                    dr_cc_i['i'] = i
                    if (ccreg, ccseason) in dict_cc_dr.keys():
                        dict_cc_dr[ccreg, ccseason] = pd.concat(
                            [dict_cc_dr[ccreg, ccseason],
                             dr_cc_i[['r', 'i', 'value']]])
                    else:
                        dict_cc_dr[ccreg, ccseason] = dr_cc_i[['r', 'i', 'value']]


    # ------ AGGREGATE OUTPUTS ------
    cc_old = (
        pd.concat(dict_cc_old, axis=0)
        ### Drop the ccreg and numbered indices
        .reset_index().drop(['level_2'], axis=1)
        .rename(columns={'level_0':'ccreg', 'level_1':'ccseason', 'MW':'value'})
        .assign(t=str(tnext))
        .merge(resources.drop('ccreg',axis=1), on='resource', how='left')
    )
    ### Reorder to match ReEDS convention
    cc_old = cc_old.reindex(['i','r','ccreg','ccseason','t','value'], axis=1)

    sdbin_size = (
        pd.concat(dict_sdbin_size, axis=0)
        ### Keep the ccreg and ccseason indices but drop the numbered index
        .reset_index().drop('level_2', axis=1)
        .rename(columns={'level_0':'ccreg', 'level_1':'ccseason', 'duration':'bin'})
        .astype({'bin':str})
        .assign(t=str(tnext))
        .reindex(['ccreg','ccseason','bin','t','MW'], axis=1)
    )

    cc_mar = (
        pd.concat(dict_cc_mar, axis=0)
        .reset_index().drop('level_2', axis=1)
        .rename(columns={'level_0':'ccreg', 'level_1':'ccseason', 'CC':'value'})
        .assign(t=str(tnext))
    )
    ### Reorder to match ReEDS convention
    cc_mar = cc_mar.reindex(['i','r','ccreg','ccseason','t','value'], axis=1)

    net_load = (
        pd.concat(dict_net_load, axis=0)
        .reset_index().drop(['level_2'], axis=1)
        .rename(columns={'level_0':'ccreg', 'level_1':'ccseason', 'MW':'value'})
        ### Rename seasons to match ReEDS convention and add year index
        .replace({'winter':'wint', 'spring':'spri', 'summer':'summ'})
        .assign(t=str(tnext))
        .sort_values(['ccreg','hour'])
    )
    ### Reorder to match ReEDS convention
    net_load = net_load.reindex(['ccreg','ccseason','year','h','hour','t','value'], axis=1)

    net_load_2012 = (
        pd.concat(dict_net_load_2012, axis=0)
        .reset_index().drop(['level_2'], axis=1)
        .rename(columns={'level_0':'ccreg', 'level_1':'ccseason', 'MW':'value'})
        ### Rename seasons to match ReEDS convention and add year index
        .replace({'winter':'wint', 'spring':'spri', 'summer':'summ'})
        .assign(t=str(tnext))
        .sort_values(['ccreg','hour'])
    )
    ### Reorder to match ReEDS convention
    net_load_2012 = net_load_2012.reindex(['ccreg','ccseason','year','h','hour','t','value'], axis=1)

    if int(sw['GSw_DR']) or int(sw['GSw_EVMC']):
        cc_dr = (
            pd.concat(dict_cc_dr, axis=0)
            .reset_index().drop(['level_2', 'level_0'], axis=1)
            .rename(columns={'level_1':'ccseason'})
            .assign(t=str(tnext))
            .reindex(['i','r','ccseason','t','value'], axis=1)
            )
    else:
        cc_dr = pd.DataFrame(columns=['i', 'r', 'ccseason', 't', 'value'])

    # ---------------- RETURN A DICTIONARY WITH THE OUTPUTS FOR REEDS --------

    cc_results = {
        'cc_mar': cc_mar,
        'cc_old': cc_old,
        'cc_dr': cc_dr,
        'sdbin_size': sdbin_size,
        'net_load': net_load,
        'net_load_2012': net_load_2012,
    }

    return cc_results

#%% Additional functions
# ------------------ CALC CC OF EXISTING VG RESOURCES -------------------------
# @numba.jit(cache=True)
def cc_vg(vg_power, load, vg_marg_power, top_hours_n, cap_marg):
    '''
    Calculate the capacity credit of existing and marginal variable generation
    capacity using a top hour approximation. More details on the methodology
    used in this approximation can be found here:
    //nrelnas01/ReEDS/8760_Method_Inputs/8760 Method Documentation
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
    Notes:
        Currently only built for hourly profiles. Generalize to any duration
            timestep.
    '''

    # number of hours in the load and CF profiles
    hours_n = len(load)

    # get the net load that must be met with conventional generation
    load_net = load - np.sum(vg_power, axis=1)

    # get the indices of the top hours of net load
    top_hours_net = load_net.argsort()[np.arange(hours_n-1, (hours_n-top_hours_n)-1, -1)]

    # get the indices of the top hours of load
    top_hours = load.argsort()[np.arange(hours_n-1, (hours_n-top_hours_n)-1, -1)]

    # get the differences and reductions in load as well as the ratio between the two

    # load_ratio is the effective reduction in load from wind and PV for each top load
    # hour, and is used to scale the contributions of wind and PV respectively
    # see slide 5 of "\\nrelnas01\ReEDS\8760_Method_Inputs\8760 Method Documentation\
    # VG Capacity credit allocation documentation.pptx" for additional details
    load_dif = load[top_hours] - load_net[top_hours]
    load_reduct = load[top_hours] - load_net[top_hours_net]
    load_ratio = np.tile(
        np.divide(
            load_reduct, load_dif,
            out=np.zeros_like(load_reduct),
            where=load_dif != 0,
        ).reshape(top_hours_n, 1),
        (1, vg_power.shape[1])
    )
    # get the existing cc for each resource
    gen_tech = (
        vg_power[top_hours_net, :]
        + np.where(
            load_ratio < 1,
            vg_power[top_hours, :]*load_ratio,
            vg_power[top_hours, :]))

    gen_sum = np.tile(
        np.sum(gen_tech, axis=1).reshape(top_hours_n, 1),
        (1, vg_power.shape[1]))

    gen_frac = np.divide(
        gen_tech, gen_sum,
        out=np.zeros_like(gen_tech), where=gen_sum != 0)

    cap_useful_MW = (
        np.sum(
            gen_frac
            * np.tile(load_reduct.reshape(top_hours_n, 1), (1, vg_power.shape[1])),
            axis=0)
        / top_hours_n
    ).reshape(vg_power.shape[1], 1)

    # get the marg net load for each VG resource [hours x resources]
    load_marg = (
        np.tile(load_net.reshape(hours_n, 1), (1, vg_marg_power.shape[1]))
        - vg_marg_power)

    ### Get the peak net load hours [top_hours_n x resources]
    peak_net_load = np.transpose(np.array(
        ### np.partition returns the max top_hours_n values, unsorted; then np.sort sorts.
        ### So we only sort top_hours_n values instead of the whole array, saving time.
        [np.sort(
            np.partition(load_marg[:,n], -top_hours_n)[-top_hours_n:]
         )[::-1]
         for n in range(load_marg.shape[1])]
    ))

    # get the reductions in load for each resource
    load_reduct_marg = np.tile(
        load_net[top_hours_net].reshape(top_hours_n, 1),
        (1, vg_marg_power.shape[1])
    ) - peak_net_load

    # get the marginal CCs for each resource
    cc_marg = np.sum(load_reduct_marg, axis=0) / top_hours_n / cap_marg

    # setting the lower bound for marginal CC to be 0.01
    cc_marg[cc_marg < 0.01] = 0.0

    # round the outputs
    load_net = np.around(load_net, decimals=3)
    cc_marg = np.around(cc_marg, decimals=5)
    cap_useful_MW = np.around(cap_useful_MW, decimals=5)

    results = {
        'load': load,
        'load_net': load_net,
        'cc_marg': cc_marg,
        'cap_useful_MW': cap_useful_MW,
        'top_hours_net': top_hours_net,
        'peak_net_load': peak_net_load
    }

    return results

def cc_evmc_shape(load,load_net,top_hours_net,top_hours_n,evmc_shape_marg_power,cap_marg):
    '''
    Calculate the capacity credit of marginal evmc_shape resources
    using a top hour approximation.
    Args:
        load: numpy array containing time-synchronous load profile for all
            hours_n. Units: MW
        load_net: net load profile. Units: MW
        top_hours_net: arguments for the highest net load hours in load_net,
            calculated in cc_vg(). Is of length top_hours_n
        top_hours_n: number of top hours to consider for the calculation
        evmc_shape_marg: numpy array containing capacity factor profiles for marginal
            builds of each evmc_shape resource bin
        cap_marg: marginal capacity used to calculate marginal capacity credit
    Returns:
        cc_marg: marginal capacity credit for each evmc_shape resource
    Notes:
        Currently only built for hourly profiles. Generalize to any duration
            timestep.
    '''
    hours_n = len(load)

    # get the marg net load for each evmc_shape resource [hours x resources]
    load_marg = (
        np.tile(load_net.reshape(hours_n, 1), (1, evmc_shape_marg_power.shape[1]))
        - evmc_shape_marg_power)

    ### Get the peak net load hours [top_hours_n x evmc_shape resources]
    peak_net_load = np.transpose(np.array(
        ### np.partition returns the max top_hours_n values, unsorted; then np.sort sorts.
        ### So we only sort top_hours_n values instead of the whole array, saving time.
        [np.sort(
            np.partition(load_marg[:,n], -top_hours_n)[-top_hours_n:]
         )[::-1]
         for n in range(load_marg.shape[1])]
    ))

    load_reduct_marg = np.tile(
        load_net[top_hours_net].reshape(top_hours_n, 1),
        (1, evmc_shape_marg_power.shape[1])
    ) - peak_net_load
    # get the marginal CCs for each resource
    cc_marg = np.sum(load_reduct_marg, axis=0) / top_hours_n / cap_marg

    # setting the lower bound for marginal CC to be 0.01
    cc_marg[cc_marg < 0.01] = 0.0
    return cc_marg

# -------------------------CALC REQUIRED MWHS----------------------------------
# @numba.jit(nopython=True, cache=True)
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


# --------------------- CALC CC OF MARGINAL STORAGE ---------------------------
def cc_storage(storage, pr, re, sdb, log):
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
        # If the duration is already the min duration, don't interpolate
        if len(min_dur_temp) == 0:
            peak_stor.loc[min_bin,'peaking potential'] = lower_bound_p
        else:
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
        except Exception:
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
            error = 0
            p = p_base
            condition = True
            while condition:
                p_test = p + p_step_small
                e_test = e_base + ((p_test - p_base) * d)
                if np.interp(p_test, pr, re) >= e_test:
                    condition = False
                else:
                    p += p_step_small
                error += 1
                if error > 1e7:
                    log.info(d)
                    condition = False
                    log.info('**** Runaway while loop in capacity_credit.py')
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

    # Setting the data type for peaking potential so that it can be rounded
    # before sent back to ReEDS
    peak_stor['peaking potential'] = pd.to_numeric(
        peak_stor['peaking potential'])

    # CC is used to determine the peak shaving & charging needed to adjust the
    # load profile for marginal CSP-TES CC calculations.
    return peak_stor[['peaking potential']].round(decimals=2).reset_index(
        ).rename(columns={'index': 'duration', 'peaking potential': 'MW'})


def dr_dispatch(poss_dr_changes, ts_length, hrs, eff=1):
    """
    Calculate the battery level and curtailment recovery profiles.
    Since everything here is in numpy, we can try using numba.jit to speed it up.
    """
    # Initialize some necessary arrays since numba can't do np.clip
    curt = np.where(poss_dr_changes > 0, poss_dr_changes, 0)
    avail = np.where(poss_dr_changes < 0, -poss_dr_changes, 0)
    # Initialize the dr shifting and curtailment recovery to be 0 in all hours
    curt_recovered = np.zeros((ts_length, poss_dr_changes.shape[1]))
    # Loop through all hours and identify how much curtailment that hour could
    # mitigate from the available load shifting
    for n in range(0, ts_length):
        n1 = max(0, n-hrs[0])
        n2 = min(ts_length, n+hrs[1])
        # maximum curtailment this hour can shift load into
        # calculated as the cumulative sum of curtailment across all hours
        # this hour can reach, identifying the max cumulative shifting allowed
        # and subtracting off the desired shifting that can't happen
        cum = np.cumsum(curt[n1:n2, :], axis=0)
        curt_shift = np.maximum(curt[n1:n2, :] - (cum - np.minimum(cum, avail[n, :] / eff)), 0)
        # Subtract realized curtailment reduction from appropriate hours
        curt[n1:n2, :] -= curt_shift
        # Record the amount of otherwise-curtailed energy that was
        # recovered during appropriate hours
        curt_recovered[n1:n2, :] += curt_shift
    return curt_recovered


def dr_capacity_credit(hrs, eff, ts_length, poss_dr_changes, marg_peak, cols,
                       maxhrs):
    """
    Determines the ratio of peak load that could be shifted by DR.
    """
    # Get the DR profiles
    # This is using the same function as curtailment, but with opposite meaning
    # ("how much can I increase load in this hour in order to reduce load in any
    # shiftable hours" instead of "how much can I decrease load in this hour
    # in order to increase load in any shiftable hours"), so the efficiency
    # gets applied to the opposite set of data. Hence the 1/eff.
    # If maxhrs is included, that is used as the total number of hours the
    # resource is able to be called. Really just for shed
    peak_shift = dr_dispatch(
        poss_dr_changes=poss_dr_changes,
        ts_length=ts_length, hrs=hrs, eff=1/eff
    )
    # Sort and only take maximum allowed hours
    sort_shift = np.sort(peak_shift, axis=0)[::-1]
    sort_shift = sort_shift[0:int(min(maxhrs, ts_length)), :]
    # Get the ratio of reduced peak to total peak
    return pd.melt(
        pd.DataFrame(data=[np.round(sort_shift.sum(0) / marg_peak, decimals=5), ],
                     columns=cols)
    )
