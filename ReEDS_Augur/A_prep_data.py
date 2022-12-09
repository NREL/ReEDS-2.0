# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 12:35:08 2021

@author: afrazier
"""

import gdxpds
import os

import pandas as pd

from ReEDS_Augur.utility.functions import agg_duplicates, agg_rs_to_r, \
    filter_data_year, format_osprey_profiles, format_trancap, \
    format_tranloss, get_startup_costs, get_storage_eff, map_szn_to_day, \
    set_marg_vre_step_size, format_prod_load, format_prod_cap, format_prod_flex
from ReEDS_Augur.utility.generatordata import GEN_DATA, GEN_TECHS
from ReEDS_Augur.utility.hourlyprofiles import HOURLY_PROFILES, \
    calculate_vre_gen, format_mustrun, format_marg_dr
from ReEDS_Augur.utility.inputs import INPUTS
from ReEDS_Augur.utility.switchsettings import SwitchSettings


def prep_data():

    # =========================================================================
    # Get Marginal Step Sizes based on previous investments
    # =========================================================================
    set_marg_vre_step_size()

    # =========================================================================
    # Get Hourly Profiles
    # =========================================================================
    '''
    Hourly profiles are read in, formatted, and stored for further use. See the
    class "HourlyProfiles" as well as its sub-classes for formatting specifics.
    Fromatting of profiles includes:
            - shifting from local time to eastern time
            - applying any changes to load e.g. load growth, flexibility, etc.
    '''
    
    for key in HOURLY_PROFILES:
        HOURLY_PROFILES[key].format_profiles()
        
    # =========================================================================
    # Get Generator Data
    # =========================================================================
    '''
    Generator data are sensitive to individual generators (i.e. they depend on
    the region, vintage, or capacity of a specific generator). They are handled
    via a set of sub-classes based on the "GeneratorData" class so that
    properties specific to certain technologies can be handled accordingly in
    an organized manner.
    '''

    for tech in GEN_TECHS:

        for key in GEN_DATA.keys():

            # Get data and append it to GEN_DATA
            GEN_DATA[key] = pd.concat([GEN_DATA[key],
                                       GEN_TECHS[tech].prep_data(key)],
                                       sort = False,
                                       ignore_index = True)

            # Some technologies are aggregated together in Osprey. Performing
            # that aggregation here.
            GEN_DATA[key] = agg_duplicates(GEN_DATA[key])

    # =============================================================================
    # Format Data for Osprey
    # =========================================================================
    
    # Format mustrun generation
    GEN_DATA['avail_cap'] = format_mustrun(GEN_DATA['avail_cap'])

    # Format consumption and capacity for H2 and DAC
    cap_prod = format_prod_cap(GEN_DATA['avail_cap'])
    prod_load, HOURLY_PROFILES['prod_noflex'].profiles = format_prod_load()
    # Remove h2 and DAC from all other data
    techs = INPUTS['i_subsets'].get_data()
    for key in GEN_DATA.keys():
        GEN_DATA[key] = GEN_DATA[key][~GEN_DATA[key]['i'].isin(
                                                        techs['consume'])]

    # Calculating vre generation and getting net load
    calculate_vre_gen(
        profiles=HOURLY_PROFILES,
        cfs_exist=GEN_DATA['hourly_cfs_exist'],
        cfs_marg=GEN_DATA['hourly_cfs_marg'],
    )
    
    # Reformat DR profiles
    format_marg_dr(profiles=HOURLY_PROFILES)

    # Downselect to the appropriate data year for Osprey and format the data
    net_load = (
        HOURLY_PROFILES['load'].profiles
        - HOURLY_PROFILES['vre_gen_r'].profiles
        - HOURLY_PROFILES['mustrun'].profiles
        + HOURLY_PROFILES['prod_noflex'].profiles
    )
    net_load = filter_data_year(profile=net_load, data_years=SwitchSettings.osprey_years)
    net_load = net_load.round(SwitchSettings.switches['decimals'])
    HOURLY_PROFILES['net_load_osprey'].profiles = net_load.copy()
    net_load = format_osprey_profiles(net_load)

    # Format DR data for Osprey
    dr_inc = HOURLY_PROFILES['dr_inc'].profiles.copy()
    dr_dec = HOURLY_PROFILES['dr_dec'].profiles.copy()
    if not int(SwitchSettings.switches['gsw_dr']):
        rtmp = INPUTS['rfeas'].get_data()['r'].values[0]
        dr_inc_day = pd.DataFrame(columns=['d', 'hr', 'i', rtmp]).append(
            {'d': 'd1', 'hr': 'hr1', 'i': 'dr1_1', rtmp: 0},
            ignore_index=True)
    else:
        dr_inc_day = format_osprey_profiles(dr_inc)
    if not int(SwitchSettings.switches['gsw_dr']):
        rtmp = INPUTS['rfeas'].get_data()['r'].values[0]
        dr_dec_day = pd.DataFrame(columns=['d', 'hr', 'i', rtmp]).append(
            {'d': 'd1', 'hr': 'hr1', 'i': 'dr1_1', rtmp: 0},
            ignore_index=True)
    else:
        dr_dec_day = format_osprey_profiles(dr_dec)

    # Get hours for shedding DR
    dr_tmp = dr_dec.reset_index().drop(columns=['season', 'year', 'h'])
    dr_reg_tech = pd.merge(dr_tmp[dr_tmp['hour'] == 1].melt(
                                id_vars=['i', 'hour'])[['i', 'variable']],
                           INPUTS['dr_shed'].get_data(), on='i', how='left'
                           ).fillna(0)
    rank_hrs = pd.merge(net_load.melt(id_vars=['d', 'hr']),
                        dr_reg_tech,
                        on='variable')
    rank_hrs['rank'] = (
        rank_hrs
        .groupby(['variable', 'i'])['value']
        .rank(method='first', ascending=False)
        )
    rank_out = rank_hrs[rank_hrs['rank'] <= rank_hrs.max_hrs][['d', 'hr', 'i', 'variable']]
    rank_out['value'] = 1
    if rank_out.empty:
        # Ensure there is some value here, and that it is 0
        rtmp = INPUTS['rfeas'].get_data()['r'].values[0]
        rank_out = pd.DataFrame(columns=['d', 'hr', 'i', 'r']).append(
            {'d': 'd1', 'hr': 'hr1', 'i': 'dr1_1', 'r': rtmp, 'value': 0},
            ignore_index=True)

    # Format flexible H2 and DAC production
    prod_load = format_prod_flex(
            cap_prod,
            HOURLY_PROFILES['net_load_osprey'].profiles.copy(),
            prod_load)

    # Get available capacity by day for Osprey
    avail_cap_d = map_szn_to_day(GEN_DATA['avail_cap'])
    avail_cap_d = pd.pivot_table(avail_cap_d, index = ['i','v','r'],
                                              columns = 'd',
                                              values = 'MW').reset_index()

    # Aggregate daily energy budget of hybrids and dispatchable hydro
    daily_energy_budget = agg_rs_to_r(GEN_DATA['daily_energy_budget']).rename(columns={'i':'*i'})

    # =========================================================================
    # Write data for Osprey
    # =========================================================================

    osprey_inputs = {
        'cap_prod': cap_prod,
        'energy_cap': GEN_DATA['energy_cap'],
        'gen_cost': GEN_DATA['gen_cost'],
        'mingen': GEN_DATA['mingen'],
        'prod_load': prod_load,
        'routes': INPUTS['routes'].get_data(),
        'startup_costs': get_startup_costs(),
        'storage_eff': get_storage_eff(),
        'top_hours_day': rank_out,
        'trancap': format_trancap(),
        'tranloss': format_tranloss(),
        'cap_converter': (INPUTS['cap_converter'].get_data()
                          .round(SwitchSettings.switches['decimals'])),
        'converter_efficiency_vsc': INPUTS['converter_efficiency_vsc'].get_data(),
        'Sw_VSC': pd.DataFrame({'value':[int(SwitchSettings.switches['gsw_vsc'])]}),
    }

    ReEDS_inputs = {
        'ret_frac': GEN_DATA['ret_frac']
    }

    avail_cap_d.to_csv(
        os.path.join(
            'ReEDS_Augur',
            'augur_data',
            'avail_cap_d_{}.csv'.format(str(SwitchSettings.prev_year))),
        index=False)
    daily_energy_budget.to_csv(
        os.path.join(
            'ReEDS_Augur',
            'augur_data',
            'daily_energy_budget_{}.csv'.format(str(SwitchSettings.prev_year))),
        index=False)
    net_load.to_csv(
        os.path.join(
            'ReEDS_Augur',
            'augur_data',
            'net_load_osprey_{}.csv'.format(str(SwitchSettings.prev_year))),
        index=False)
    dr_inc_day.to_csv(
        os.path.join(
            'ReEDS_Augur',
            'augur_data',
            'dr_inc_osprey_{}.csv'.format(str(SwitchSettings.prev_year))),
        index=False)
    dr_dec_day.to_csv(
        os.path.join(
            'ReEDS_Augur',
            'augur_data',
            'dr_dec_osprey_{}.csv'.format(str(SwitchSettings.prev_year))),
        index=False)
    with gdxpds.gdx.GdxFile() as gdx:
        for key in osprey_inputs:
            gdx.append(
                gdxpds.gdx.GdxSymbol(
                    key, gdxpds.gdx.GamsDataType.Parameter,
                    dims=osprey_inputs[key].columns[:-1].tolist(),
                )
            )
            gdx[-1].dataframe = osprey_inputs[key]
        gdx.write(
            os.path.join(
                'ReEDS_Augur', 'augur_data',
                'osprey_inputs_{}.gdx'.format(str(SwitchSettings.prev_year)))
        )

    ### Write data for plots if necessary
    if SwitchSettings.switches['plots']:
        HOURLY_PROFILES['load'].profiles.to_hdf(
            os.path.join('ReEDS_Augur','augur_data',
                         'plot_load_{}.h5'.format(SwitchSettings.prev_year)),
            key='data', complevel=4)
        HOURLY_PROFILES['vre_gen'].profiles.to_hdf(
            os.path.join('ReEDS_Augur','augur_data',
                         'plot_vre_gen_{}.h5'.format(SwitchSettings.prev_year)),
            key='data', complevel=4)
        HOURLY_PROFILES['prod_noflex'].profiles.to_hdf(
            os.path.join('ReEDS_Augur','augur_data',
                         'plot_prod_noflex_{}.h5'.format(SwitchSettings.prev_year)),
            key='data', complevel=4)

    return ReEDS_inputs

