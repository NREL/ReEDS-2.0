# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 08:59:00 2020

@author: afrazier
"""

import gdxpds
import pandas as pd
import numpy as np
import os
from utilities import get_cap, tech_types, weighted_average, adjust_tz, \
    get_cspns_frac, get_solar_cap, get_osprey_cap, print1, adjust_flex_load, adjust_elastic_load

#%%


def prep_data(args):
    '''
    This function prepares the data for Osprey and packages it into a single
        gdx file.
    Outputs:
        - osprey_inputs_{scenario}_{year}.gdx for Osprey
        - Returns condor_data, reeds_cc_data, curt_data, marg_curt_data
            - These are dictionaries containing data that is used downstream
              in the augur workflow
    Details on data that is processed:
        - spatial mappers
            - rfeas, r_rs, r_cendiv
        - generator capacity
            - cap_osprey has any generator less than 5 MW dropped and includes
              only thermal and CSP-TES capacities
            - cap_solar has csp-ns added to the highest quality PV resource
              class in the same region
            - cap_csp, cap_cspns, cap_pv, cap_storage_cap_thermal_cap_wind
            - capacities sent to reeds_cc are aggregated by v (and t for wind)
        - generator availability
            - thermal generator availabilities come straight from ReEDS
            - hydro availability is done like it is in the ReEDS2PLEXOS
              translation
            - Canadian hydro varies by season based on the values in the
              inputs_case folder
        - mingen data
            - mingen comes from hourly_operational_characteristics.csv
            - hydro mingen levels are calculated as they are in the
              ReEDS2PLEXOS translation
                - The default in ReEDS is 0.5. This value is often higher than
                  the hydro availability numbers described above, so instead
                  we use the capacity-weighted average mingen level from the
                  available data, which is 0.0985. In some cases, even 0.0985
                  is higher then the seasonal CF. In these rare cases, we
                  assign the CF to be the mingen value, essentially making
                  these few generators non-dispatchable.
        - start cost data
            - also comes from hourly_operational_characteristics.py
        - fuel costs
            - for biopower, marginal fuel costs results are taken from ReEDS
              (because of the supply curve associated with biofuels in ReEDS).
              For any region in which biopower was not used during a given
              ReEDS iteration, the lowest cost biofuel power for that region
              is used. For all other resources, fuel costs are taken directly
              from ReEDS
        - heat rates
            - these are taken directly from ReEDS and are used to adjust fuel
              costs to $/MWh
        - vom
            - CANADIAN HYDRO IS HARD CODED to be equal to domestic
              dispatchable hydro
            - all other numbers are taken directly from ReEDS
        - VRE generation profiles
            - wind profiles are scaled by a capacity-weighted average of their
              vintage-specific capacity factors
                - These generation profiles are capped at a capacity factor of
                  1 for capacity credit calculations
                - They are allowed to exceed 1 in Osprey, so the total
                  generation in ReEDS and Osprey match
            - solar profiles included csp-ns (see "cap_solar" in generator
              capacities above)
            - marginal cf profiles are scaled by the wind vintage of the next
              ReEDS iteration
        - net load profiles
            - load_LP is used in Osprey and is calculated just as load is
              adjusted in ReEDS2PLEXOS
                - transmission losses and canadian exports are added to the
                  region sending the power
            - load_CC is used in the reeds_capacity_credit and is not adjusted
              by transmission losses
        - transmission capacity and loss factors
            - for any regions with both AC and DC transmission, these are
              combined into a single line and a capcaity-weighted average loss
              factor is used
        - Storage energy capacity and round-trip efficiencies come straight
          from ReEDS
    '''
#%%

    print1('getting Osprey generator data...')

    scenario = args['scenario']
    next_year = args['next_year']

    # technology types from tech_subset_table
    techs = tech_types(args)
    # data from ReEDS
    gdx_file = os.path.join(args['data_dir'],
                            'reeds_data_{}.gdx'.format(args['tag']))
    gdxin = gdxpds.to_dataframes(gdx_file)
    # hourly temporal mapper
    hdtmap = pd.read_csv(os.path.join('inputs_case', 'h_dt_szn.csv'))
    idx = hdtmap.year == args['osprey_reeds_data_year']
    hdtmap_single = hdtmap[idx].reset_index(drop=True)

    # Getting hours in each timeslice
    hours = gdxin['hours'].copy()
    hours.columns = ['h', 'hours']
    # Consolidating superpeak hours to their host timeslice
    # TODO! Make this dynamic, such that if h18 is added it will also be
    # handled here
    # TODO! Is there anywhere in this script that we need the number of hours
    # in each timeslice?
    hours.loc[hours['h'] == 'h3', 'hours'] += hours.loc[hours['h'] == 'h17',
                                                        'hours'].values[0]
    hours = hours[hours['h'] != 'h17'].reset_index(drop=True)

    # Gettting timeslice to season mapper
    h_szn = gdxin['h_szn'].copy()
    h_szn.drop('Value', axis=1, inplace=True)

    # Getting number of hours in each season
    szn_hours = pd.merge(left=h_szn, right=hours, on='h', how='inner')
    szn_hours = szn_hours.groupby('szn').sum()
    szn_hours['total'] = szn_hours['hours'].sum()
    # Fraction of total hours that are in each season
    szn_hours['szn_frac'] = szn_hours['hours'] / szn_hours['total']

    # =========================================================================
    # Get spatial mappers
    # =========================================================================

    # Regions that exist in this scenario
    rfeas = gdxin['rfeas'].drop('Value', 1)

    # Mapping resource regions to BAs
    r_rs = gdxin['r_rs'].drop('Value', 1)
    # Filter for regions that exist in this scenario
    r_rs = r_rs[r_rs['r'].isin(rfeas['r'])].reset_index(drop=True)
    # TODO! eventually "sk" will be removed entirely from the model
    r_rs = r_rs[r_rs['rs'] != 'sk'].reset_index(drop=True)

    # Mapping BA to census region (for load scaling)
    r_cendiv = gdxin['r_cendiv'].drop('Value', 1)
    # Filter for regions that exist in this scenario
    r_cendiv = r_cendiv[r_cendiv['r'].isin(rfeas['r'])].reset_index(drop=True)

    # Hiearchy maps BAs to ccregs, but also includes all other spatial mapping
    hierarchy = gdxin['hierarchy'].copy().drop('Value', 1)
    hierarchy = hierarchy[hierarchy['r'].isin(rfeas['r'])].reset_index(
        drop=True)
    hierarchy = pd.merge(left=r_rs, right=hierarchy, on='r', how='right')

    # =========================================================================
    # Generator capacity
    # =========================================================================

    # Capacity for Osprey - includes cap_thermal and cap_csp from reeds_data
    # gdx file.
    # CSP is aggregated up to the BA level.
    # Generators smaller than than osprey_min_plant_size (default=5MW) are
    # dropped.
    cap_osprey = get_osprey_cap(gdxin, r_rs,
                                min_plant_size=args['osprey_min_plant_size'])
    # Get storage capacity, aggregating over vintage
    cap_storage_osprey = get_cap(gdxin, 'cap_storage', return_cols=['i', 'r'])
    # Define a generic vintage for storage
    cap_storage_osprey['v'] = 'new1'
    # Filter storage devices for osprey by osprey_min_storage_size
    idx = cap_storage_osprey['MW'] > args['osprey_min_storage_size']
    cap_storage_osprey = cap_storage_osprey[idx].reset_index(drop=True)
    # Concatenate storage capacity with Osprey capacity
    cap_osprey = pd.concat([cap_osprey, cap_storage_osprey],
                           sort=False).reset_index(drop=True)

    # =========================================================================
    # Generator availability - outage rates and seasonal hydro capacity factors
    # =========================================================================

    # Availability rates for thermal technologies
    avail = gdxin['avail_filt'].copy().rename(columns={'Value': 'avail'})
    avail.i = avail.i.str.lower()
    # avail is indexed by i, v, and szn. We want it indexed by r as well, so
    # we merge it with cap_osprey here. This will also remove any values in
    # avail that don't have a matching value in cap_osprey.
    avail = pd.merge(left=avail,
                     right=cap_osprey[['i', 'v', 'r']].drop_duplicates(),
                     on=['i', 'v'], how='inner')
    # reorder the columns to match ReEDS convention
    avail = avail[['i', 'v', 'r', 'szn', 'avail']]

    # Canadian hydro seasonal availability - this is the fraction of annual
    # imports that come in each season
    can_import_frac = pd.read_csv(
        os.path.join('inputs_case', 'can_imports_szn_frac.csv'), header=None)
    can_import_frac.columns = ['szn', 'frac']
    can_import_frac.set_index('szn', inplace=True)
    # Divide the fraction of energy that comes in each season by the fraction
    # of hours in each season to get the seasonal availability
    can_import_frac['avail'] = can_import_frac.frac / szn_hours.szn_frac
    # Normalize this seasonal can-imports availability result to the season
    # with the highest availability
    can_import_max_avail = can_import_frac['avail'].max()
    can_import_frac.avail /= can_import_max_avail
    # Replace the values in avail for can-imports with these seasonal values
    for szn in can_import_frac.index:
        avail.loc[(avail['i'].isin(techs['CANADA'])) & (avail['szn'] == szn),
                  'avail'] = can_import_frac.loc[szn, 'avail']

    # Seasonal hydro capacity factors
    cfhyd = gdxin['cf_hyd_filt'].copy().rename(columns={'Value': 'cf'})
    cfhyd.i = cfhyd.i.str.lower()
    # cfhyd is indexed by i, r, and szn. We want it indexed by v as well, so
    # we merge it with cap_osprey here. This will also remove any values in
    # cf_hyd that don't have a matching value in cap_osprey.
    cfhyd = pd.merge(left=cfhyd,
                     right=cap_osprey[['i', 'v', 'r']].drop_duplicates(),
                     on=['i', 'r'], how='inner')
    # reorder the columns to match ReEDS convention
    cfhyd = cfhyd[['i', 'v', 'r', 'szn', 'cf']]
    # Combine seasonal hydro CFs with outage rates
    avail = pd.merge(left=avail, right=cfhyd, on=['i', 'v', 'r', 'szn'],
                     how='left').fillna(1)
    avail['avail'] *= avail['cf']
    avail = avail[['i', 'v', 'r', 'szn', 'avail']]

    # =========================================================================
    # WECC data - mingen levels & start costs
    # =========================================================================

    # Read in WECC data
    wecc_data = pd.read_csv(
        os.path.join('inputs_case', 'hourly_operational_characteristics.csv'))

    # Expand WECC data to be indexed by watertech if necessary
    if args['waterswitch'] == '1':
        watertechs = pd.read_csv(
            os.path.join('inputs_case', 'i_coolingtech_watersource_link.csv'))
        watertechs.columns = ['watertech', 'category', 'ctt', 'wst']
        watertechs = watertechs[['watertech', 'category']]
        watertechs.watertech = watertechs.watertech.str.lower()
        watertechs.category = watertechs.category.str.lower()
        wecc_data = pd.merge(left=watertechs, right=wecc_data, on='category',
                             how='right')
        wecc_data['watertech'].fillna(wecc_data['category'], inplace=True)
        wecc_data.drop('category', axis=1, inplace=True)
        wecc_data.rename(columns={'watertech': 'category'}, inplace=True)

    # Get mingen data
    mingen = wecc_data[['category',
                        'Min Stable Level/capacity']].reset_index(drop=True)
    mingen.columns = ['i', 'mingen']
    mingen.i = mingen.i.str.lower()
    # mingen is indexed by i. We want it indexed by r and szn as well, so we
    # merge it with cap_osprey here. This will also remove any values in
    # mingen that don't have a matching value in cap_osprey.
    mingen = pd.merge(left=mingen,
                      right=avail[['i', 'r', 'szn']].drop_duplicates(),
                      on='i', how='right')
    # Assign all geothermal technologies the same mingen value
    mingen_geo = wecc_data.loc[wecc_data['category'] == 'geothermal',
                               'Min Stable Level/capacity'].values[0]
    mingen.loc[mingen['i'].isin(techs['GEO']), 'mingen'] = mingen_geo

    # Hydro mingen is done separately to reflect the seasonal variarions
    mingen = mingen[~mingen['i'].isin(techs['HYDRO'])].reset_index(drop=True)
    # NOTE There is a lot of missing data in the mingen numbers for hydro in
    # ReEDS. The default in ReEDS is 0.5
    # This value is often higher than the seasonal availability factor, so
    # instead we use the capacity-weighted average mingen level from the
    # available data, which is 0.0985.
    hydmin = gdxin['hydmin'].copy().rename(columns={'Value': 'mingen'})
    hydmin.i = hydmin.i.str.lower()
    hydmin['mingen'].replace(0.5, 0.0985, inplace=True)
    # In some cases, even 0.0985 is higher then the seasonal CF. In these rare
    # cases, we assign the CF to be the mingen value, essentially making these
    # few generators non-dispatchable.
    hydmin = pd.merge(left=hydmin, right=avail[['i', 'r', 'szn', 'avail']],
                      on=['i', 'r', 'szn'], how='inner')
    hydmin.loc[hydmin['avail'] < hydmin['mingen'], 'mingen'] = hydmin.loc[
        hydmin['avail'] < hydmin['mingen'], 'avail']
    hydmin['mingen'] /= hydmin['avail']
    hydmin.drop('avail', 1, inplace=True)

    # mingen level for non-dispatchable hydro is equal to the seasonal CF
    hydmin_nd = avail[['i', 'r', 'szn', 'avail']].drop_duplicates()
    hydmin_nd = hydmin_nd[hydmin_nd['i'].isin(techs['HYDRO_ND'])].reset_index(
        drop=True).rename(columns={'avail': 'mingen'})
    hydmin = pd.concat([hydmin, hydmin_nd], sort=False).reset_index(drop=True)

    # Consolidate all mingen levels
    mingen = pd.concat([mingen, hydmin], sort=False).reset_index(drop=True)
    mingen = mingen[['i', 'r', 'szn', 'mingen']]

    # Get start cost data
    startcost = wecc_data[['category', 'Start Cost/capacity']].fillna(0)
    startcost.columns = ['i', 'startcost']
    # Filter for the startcosts that are included in each i column
    startcost = pd.merge(left=startcost,
                         right=cap_osprey[['i']].drop_duplicates(),
                         on='i', how='inner')

    # =========================================================================
    # Calculate marginal generator costs
    # =========================================================================

    # Get the marginal biomass fuel price by region from ReEDS
    biofuel = gdxin['repbioprice_filt'].rename(
        columns={'Value': 'fuel $/MMBtu'})
    # Regions where biomass didn't generate report a price of -inf. Filter
    # these out.
    biofuel = biofuel[biofuel['fuel $/MMBtu'] > 0].reset_index(drop=True)
    # For regions with a -inf marginal biomass price, get the price of biomass
    # in the cheapest supply curve bin.
    biosupply = pd.read_csv(
        os.path.join('inputs_case', 'bio_supplycurve.csv')).rename(
            columns={'j': 'r'})
    biosupply = biosupply[biosupply['var'] == 'cost'].reset_index(drop=True)
    # Filter for regions in this run that don't have a marginal bioprice
    # reported by ReEDS
    biosupply = biosupply[(biosupply['r'].isin(rfeas['r'])) &
                          (~biosupply['r'].isin(biofuel['r']))].reset_index(
                              drop=True)
    biosupply = biosupply[['r', 'bioclass1']].rename(
        columns={'bioclass1': 'fuel $/MMBtu'})
    # Concatenate marginal prices with data from supply curve
    biofuel = pd.concat([biofuel, biosupply],
                        sort=False).reset_index(drop=True)
    # Fuel prices are indexed by i and r, so adding the i index for biopower
    biofuel['i'] = 'biopower'
    # Adjusting the "i" set here to include water cooling tech and source
    if args['waterswitch'] == '1':
        biowatertechs = watertechs[
            watertechs['category'] == 'biopower'].reset_index(drop=True)
        biowatertechs.columns = ['iwt', 'i']
        biocap_osprey = cap_osprey[
            cap_osprey['i'] == 'biopower'][['i', 'r']].drop_duplicates()
        biowatertechs = pd.merge(left=biowatertechs, right=biocap_osprey,
                                 on='i', how='right')
        biofuel = pd.merge(left=biowatertechs, right=biofuel, on=['i', 'r'],
                           how='left')
        biofuel.drop('i', axis=1, inplace=True)
        biofuel.rename(columns={'iwt': 'i'}, inplace=True)

    # Get fuel costs
    fuel = gdxin['fuel_price_filt'].rename(columns={'Value': 'fuel $/MMBtu'})
    fuel.i = fuel.i.str.lower()
    # Concatenate fuel prices with biofuel prices
    fuel = pd.concat([fuel, biofuel], sort=False).reset_index(drop=True)

    # Fuel prices will be adjusted by heat rate to convert to $/MWh
    heatrate = gdxin['heat_rate_filt'].rename(columns={'Value': 'heatrate'})
    heatrate.i = heatrate.i.str.lower()

    # NOTE: lfill gas has a heat rate but no fuel cost, so we want to fill na
    # with 0 here. BUT! some CofireNew has a fuel cost but no heat rate (or
    # vom). This is also being set to 0 here. We could set how='left' here to
    # drop these instances of no heat rate.
    fuel = pd.merge(left=heatrate, right=fuel, on=['i', 'r'],
                    how='outer').fillna(0)
    fuel['fuel $/MWh'] = fuel['heatrate'] * fuel['fuel $/MMBtu']

    # Add vom costs to fuel prices to get marginal operating costs
    vom = gdxin['cost_vom_filt'].rename(columns={'Value': 'vom $/MWh'})
    vom.i = vom.i.str.lower()
    vom = pd.merge(left=vom, right=fuel[['i', 'v', 'r', 'fuel $/MWh']],
                   on=['i', 'v', 'r'], how='outer').fillna(0)
    vom['op_cost'] = vom['vom $/MWh'] + vom['fuel $/MWh']

    # Filter for only installed capacities in ReEDS
    vom = pd.merge(left=vom, right=cap_osprey[['i', 'v', 'r']],
                   on=['i', 'v', 'r'], how='right').fillna(0)

    # Fix the VO&M of Canadian imports to be equal to hydro
    vom_hyd = gdxin['vom_hyd'].values[0][0]
    vom.loc[vom['i'].isin(techs['CANADA']), 'op_cost'] = vom_hyd

    gen_cost = vom[['i', 'v', 'r', 'op_cost']].copy()

    # =========================================================================
    # Calculate VRE generation profiles
    # =========================================================================

    print1('getting VRE capacity...')

    # Get CF profiles and resources
    recf = pd.read_pickle(
        os.path.join('inputs_case', 'recf_{}.pkl'.format(scenario)))  # 0.4 s
    resources = pd.read_pickle(
        os.path.join('inputs_case', 'resources_{}.pkl'.format(scenario)))

    # Filter datetime mapper to a single year if only running with one year of
    # data
    if len(recf) == args['osprey_ts_length']:
        hdtmap = hdtmap_single

    # Map resource to BA
    resource_r = pd.merge(
        left=resources[['resource', 'r']].rename(columns={'r': 'rs'}),
        right=r_rs, on='rs', how='outer')
    resource_r['r'].fillna(resource_r['rs'], inplace=True)
    resource_r.drop('rs', 1, inplace=True)

    # Get wind capacity factors by year
    wind_cf = gdxin['cf_adj_t_filt'].copy()
    wind_cf.columns = ['i', 'v', 't', 'windCF']

    # Filter for valid vintage-build year combinations
    ivt = pd.read_csv(os.path.join('inputs_case', 'ivt.csv'), index_col=0)
    ivt_wind = ivt.loc['wind-ons_1*wind-ons_10'].reset_index()
    ivt_wind.columns = ['t', 'v']
    ivt_wind['v'] = 'new' + ivt_wind['v'].astype(str)
    # Get all of the init vintages in the v set
    vintages = gdxin['v'].copy()
    vintages = vintages[vintages['*'].str.contains('init')]['*'].tolist()
    for v in vintages:
        ivt_wind.loc[len(ivt_wind)] = ['2010', v]
    # Filter for valid vintage-build year combinations
    wind_cf = pd.merge(left=wind_cf, right=ivt_wind, on=['t', 'v'],
                       how='right')

    # Get the mean of all CF profiles
    wind_scaling = recf.mean().reset_index()  # 0.25 s
    wind_scaling.columns = ['resource', 'Mean']

    # Scale wind CFs by the ratio between the CF from ReEDS and the mean of
    # the CF profile
    wind_scaling = pd.merge(left=resources, right=wind_scaling, on='resource')
    wind_scaling = pd.merge(left=wind_scaling, right=wind_cf, on='i',
                            how='left')
    index_wind = (wind_scaling['i'].isin(techs['WIND']))
    index_notwind = (~wind_scaling['i'].isin(techs['WIND']))
    wind_scaling.loc[index_wind, 'scaling_factor'] = wind_scaling.loc[
        index_wind, 'windCF'] / wind_scaling.loc[index_wind, 'Mean']
    wind_scaling.loc[index_notwind, 'scaling_factor'] = 1

    # Get a capacity weighted average scaling factor for all wind capacity
    cap_wind = get_cap(gdxin, 'cap_wind', return_cols=['i', 'v', 'r', 't'])
    cap_wind = pd.merge(left=cap_wind, right=wind_scaling[
        ['i', 'v', 'r', 't', 'scaling_factor']].drop_duplicates(),
        on=['i', 'v', 'r', 't'], how='left')
    scale_factor = weighted_average(cap_wind, ['scaling_factor'], 'MW',
                                    ['i', 'r'], False, False)

    # Aggregate all wind capacity by resource region
    cap_wind = cap_wind[['i', 'r', 'MW']].groupby(
        ['i', 'r'], as_index=False).sum()

    # Get solar capacity. This includes csp-ns capacity, aggregated to the BA
    # level and assigned to the highest available UPV resource class in the BA.
    cap_solar = get_solar_cap(gdxin, r_rs, resources, techs, args)

    # Create a single DataFrame of all VRE capacity
    cap_vre = pd.concat([cap_solar, cap_wind],
                        sort=False).reset_index(drop=True)
    cap_vre['resource'] = cap_vre['i'] + '_' + cap_vre['r']
    cap_vre = pd.merge(left=resources[['i', 'r', 'resource']], right=cap_vre,
                       on=['i', 'r', 'resource'], how='left').fillna(0)
    cap_vre = pd.merge(left=cap_vre, right=scale_factor, on=['i', 'r'],
                       how='left').fillna(1)

    # Since we aggregate csp-ns to the BA level and add it to the best UPV
    # resource class available in the BA, we get the fraction of the csp-ns
    # capacity vs. UPV capacity for these resource. This way, results for
    # csp-ns can be allocated correctly.
    cap_frac_cspns = get_cspns_frac(gdxin, r_rs, resources, techs)

    print1('getting vre gen profiles...')
    # Create a DataFrame of all VRE generation: RECF * VRE cap * scaling_factor
    vre_gen = recf.copy()
    cap_vre_temp = cap_vre['MW'].values
    cap_vre_temp = np.tile(cap_vre_temp.reshape(1, len(cap_vre)),
                           (len(vre_gen), 1))
    scaling_factor_temp = cap_vre['scaling_factor'].values
    scaling_factor_temp = np.tile(scaling_factor_temp.reshape(1, len(cap_vre)),
                                  (len(vre_gen), 1))
    vre_gen *= cap_vre_temp * scaling_factor_temp
    # Create another DataFrame with this information clipped at CF=1 for the
    # capacity credit script
    vre_gen_cc = pd.DataFrame(
        columns=vre_gen.columns,
        data=np.clip(vre_gen.values, a_min=0, a_max=cap_vre_temp,
                     out=vre_gen.values))
    vre_gen_cc = pd.concat([hdtmap, vre_gen_cc], axis=1)

    # For marginal wind, use only the scaling factor for the next solve year
    wind_scaling_marginal = wind_scaling[
        wind_scaling['t'] == str(next_year)].reset_index(drop=True)
    pv_scaling_marginal = wind_scaling[
        wind_scaling['i'].isin(techs['PV'])].reset_index(drop=True)
    wind_scaling_marginal = pd.concat([pv_scaling_marginal,
                                       wind_scaling_marginal],
                                      sort=False).reset_index(drop=True)
    wind_scaling_marginal = pd.merge(left=resources[['resource']],
                                     right=wind_scaling_marginal,
                                     on='resource', how='left')
    wind_scaling_marginal = wind_scaling_marginal['scaling_factor'].values
    wind_scaling_marginal = np.tile(
        wind_scaling_marginal.reshape(1, len(resources)), (len(recf), 1))
    marg_vre_mw = np.tile(args['reedscc_marg_vre_mw'],
                          (len(recf), len(resources)))

    # Scale recf by wind scaling factor and by the marginal VRE step size
    recf_marginal = recf * wind_scaling_marginal * marg_vre_mw
    # Clip the CF to be no greater than 1 for the CC script
    recf_marginal_cc = pd.DataFrame(
        columns=recf_marginal.columns,
        data=np.clip(recf_marginal.values, a_min=0, a_max=marg_vre_mw,
                     out=recf_marginal.values))
    recf_marginal_cc = pd.concat([hdtmap, recf_marginal], axis=1)
    # When running for multiple years, this includes hourly data for 7 years
    # Subsetting marginal resource CF to online include the 2012 profile for
    # curtailment calculation
    idx = recf_marginal_cc.year == args['osprey_reeds_data_year']
    recf_marginal = recf_marginal_cc[idx].reset_index(drop=True)
    recf_marginal = recf_marginal.drop(list(hdtmap.columns), axis=1)

    # Get the max generation from vre in each timeslice
    m_cf = gdxin['m_cf_filt'].copy()
    m_cf.i = m_cf.i.str.lower()
    vre_cap = get_cap(gdxin, 'cap_wind')
    vre_cap = pd.concat([vre_cap, get_cap(gdxin, 'cap_pv')],
                        sort=False).reset_index(drop=True)
    vre_cap = pd.concat([vre_cap, get_cap(gdxin, 'cap_cspns')],
                        sort=False).reset_index(drop=True)
    vre_max_cf = pd.merge(left=vre_cap, right=m_cf, on=['i', 'v', 'r'],
                          how='left')
    vre_max_cf['MW'] *= vre_max_cf['Value']
    vre_max_cf.drop('Value', axis=1, inplace=True)
    vre_max_cf = pd.merge(left=r_rs, right=vre_max_cf.rename(
        columns={'r': 'rs'}), on='rs', how='right')
    vre_max_cf['r'].fillna(vre_max_cf['rs'], inplace=True)
    vre_max_cf = vre_max_cf.groupby(['r', 'h'], as_index=False).sum()

    # =========================================================================
    # Calculate load
    # =========================================================================

    print1('getting load and net load profiles...')

    # Get load profiles
    load = pd.read_pickle(os.path.join('inputs_case',
                                       'load_{}.pkl'.format(scenario)))
    # EFS profiles are indexed by year and hour index
    # If there are two index names for load, then we know we are using EFS
    # profiles
    if(len(load.index.names) == 2):
        YearIndexed = True
        load = load.loc[int(next_year)]
        load = load.reset_index(drop=True)
    else:
        YearIndexed = False
        load = load.reset_index(drop=True)

    # Adjust load for EFS flexibility
    if len(hdtmap) == 8760:
        flex_load = gdxin['flex_load'].copy()
        flex_load.columns = ['r', 'h', 't', 'exog']
        flex_load_opt = gdxin['flex_load_opt'].copy()
        flex_load_opt.columns = ['r', 'h', 't', 'opt']
        load = adjust_flex_load(load, flex_load, flex_load_opt, hdtmap)

    # Adjust load for elastic demand changes
    if gdxin['Sw_DemElas']['Value'][0] == 1.0:
        #load in the ratio of endogenous to exogenous, benchmark load
        load_ratio = gdxin['elastic_load_ratio']
        load_ratio.columns = ['r','h','t','ratio']
        load = adjust_elastic_load(load, load_ratio, hdtmap)



    # Adjust load for growth for both Osprey and reeds_cc
    load_mult = gdxin['load_multiplier'].copy()
    load_mult.columns = ['cendiv', 't', 'Value']
    load_mult = load_mult.pivot(index='cendiv', columns='t',
                                values='Value').reset_index()
    load_mult = pd.merge(left=r_cendiv, right=load_mult, on='cendiv',
                         how='left')
    load_mult = load_mult.sort_values('r')[str(next_year)].values
    load_mult = np.tile(load_mult.reshape(1, len(rfeas)), (len(load), 1))

    # Do not apply load multiplier for EFS load
    if(not YearIndexed):
        load *= load_mult

    # Get Canadian exports by region for the next year
    can_exports_mwh = pd.read_csv(
        os.path.join('inputs_case', 'can_exports.csv'), index_col=0)
    can_exports_mwh = can_exports_mwh[[str(next_year)]].reset_index()
    can_exports_mwh.columns = ['r', 'exports']
    can_exports_mwh = can_exports_mwh[
        can_exports_mwh['r'].isin(rfeas['r'])].reset_index(drop=True)
    # Add in regions with no Canadian exports to create a comlete set
    can_exports_none = pd.DataFrame(columns=['r', 'exports'])
    can_exports_none['r'] = rfeas[~rfeas['r'].isin(
        can_exports_mwh['r'])]['r'].reset_index(drop=True)
    can_exports_none['exports'] = 0
    # Concatenate these together
    can_exports_mwh = pd.concat([can_exports_mwh,
                                 can_exports_none]).reset_index(
                                     drop=True).sort_values('r')
    can_exports_mwh = np.tile(
        can_exports_mwh['exports'].values.reshape(1, len(can_exports_mwh)),
        (len(load), 1))

    # Getting timeslice energy fractions
    can_exports_frac = pd.read_csv(
        os.path.join('inputs_case', 'can_exports_h_frac.csv'), header=None)
    can_exports_frac.columns = ['h', 'fraction']
    # Add the fraction for superpeak timeslices to their host timeslice
    # TODO: make this dynamic!!
    can_exports_frac.loc[can_exports_frac['h'] == 'h3', 'fraction'] += \
        can_exports_frac.loc[can_exports_frac['h'] == 'h17',
                             'fraction'].values[0]
    can_exports_frac = can_exports_frac[
        can_exports_frac['h'] != 'h17'].reset_index(drop=True)
    # Divide the fraction of energy by timeslice by the number of hours in
    # each timeslice
    can_exports_frac = pd.merge(left=can_exports_frac, right=hours, on='h')
    can_exports_frac['fraction'] /= can_exports_frac['hours']
    # Merge with hdtmap to get the fraction of the annual energy during each
    # hour of the year
    can_exports_frac = pd.merge(left=hdtmap[['h']],
                                right=can_exports_frac[['h', 'fraction']],
                                on='h', how='left')
    can_exports_frac = np.tile(can_exports_frac['fraction'].values.reshape(
        len(load), 1), (1, len(rfeas)))

    can_exports_hourly = can_exports_mwh * can_exports_frac
    load += can_exports_hourly

    # Sum the load profiles for each ccreg for reeds_cc
    load_ccreg = load.T.reset_index()
    load_ccreg = pd.merge(
        left=hierarchy[['ccreg', 'r']].drop_duplicates().rename(
            columns={'r': 'index'}),
        right=load_ccreg, on='index', how='right').drop('index', 1)
    load_ccreg = load_ccreg.groupby('ccreg').sum().T
    load_ccreg = pd.concat([hdtmap, load_ccreg], axis=1)

    # =========================================================================
    # Calculate net load for Osprey
    # =========================================================================

    # Sum the VRE generation by BA to get the net load
    vre_BA = vre_gen.T.reset_index()
    vre_BA = pd.merge(left=resource_r[['r', 'resource']].rename(
        columns={'resource': 'index'}), right=vre_BA,
        on='index').drop('index', 1)
    vre_BA = vre_BA.groupby('r').sum().T
    # When running for multiple years, this includes hourly data for 7 years.
    # Filter data to 2012 to subtract from net load profile for osprey and
    # curtailment calculation.
    vre_BA = pd.concat([vre_BA, hdtmap['year']], axis=1)
    idx = vre_BA.year == args['osprey_reeds_data_year']
    vre_BA = vre_BA[idx].reset_index(drop=True)
    vre_BA = vre_BA.drop('year', axis=1)

    # When running for multiple years, this includes hourly data for 7 years.
    # Filter data to 2012 to subtract from net load profile for osprey and
    # curtailment calculation.
    load = pd.concat([hdtmap['year'], load], axis=1)
    idx = load.year == args['osprey_reeds_data_year']
    load = load[idx].reset_index(drop=True)
    load = load.drop('year', axis=1)

    # Adjust load for transmission losses only for Osprey
    if 'reeds_transloss' not in args.keys():
        args['reeds_transloss'] = False

    if args['reeds_transloss']:
        hmap = pd.read_csv(os.path.join('inputs_case',
                                        'superpeak_hour_mapper.csv'))
        hours = gdxin['hours'].copy()
        hours.columns = ['h', 'hours']
        losses = gdxin['losses_trans_h'].groupby(
            ['r', 'h'], as_index=False).sum()
        losses = pd.merge(left=losses, right=hours, on='h', how='left')
        losses = pd.merge(left=losses, right=hmap, on='h', how='left')
        losses = weighted_average(losses, ['Value'], 'hours', ['r', 'h_true'],
                                  'h', 'h_true')
        losses = losses.pivot(index='h', columns='r',
                              values='Value').reset_index()
        losses = pd.merge(left=hdtmap_single, right=losses, on='h',
                          how='right').fillna(0)
        for col in load.columns:
            if col not in losses.columns:
                losses.loc[:, col] = 0
        losses = pd.merge(left=hdtmap_single[['hour']], right=losses,
                          on='hour', how='left')
        losses = losses[load.columns.tolist()].values

        load_Osprey = load + losses

    else:
        load_Osprey = load.copy()

    # Get net load
    net_load_Osprey = load_Osprey - vre_BA

    # Get timezone mapper
    tz_map = pd.read_csv(os.path.join('inputs_case', 'reeds_ba_tz_map.csv'))
    tz_map = tz_map[tz_map['r'].isin(rfeas['r'])].reset_index(drop=True)
    tz_map = tz_map.sort_values('r').reset_index(drop=True)

    # Adjust from local time to ET
    net_load_Osprey_ET = adjust_tz(net_load_Osprey, tz_map)

    # Create hour and day columns
    flatten = lambda l: [item for sublist in l for item in sublist]
    day = flatten([['d'+str(i+1)]*24 for i in range(365)])
    net_load_Osprey_ET['d'] = day
    hour = ['hr'+str(i+1) for i in range(24)]*365
    net_load_Osprey_ET['hr'] = hour

    # Roll the hour and day columns for the day ahead load
    net_load_day_ahead = net_load_Osprey_ET.copy()
    day = np.roll(net_load_day_ahead.d.values, 24)
    hour = np.roll(net_load_day_ahead.hr.values, 24)
    hour = np.array(['hr'+str(int(i[2:]) + 24) for i in hour])
    net_load_day_ahead.d = day
    net_load_day_ahead.hr = hour

    # Combine the load and day ahead load into a single table
    net_load_guss = pd.concat([net_load_Osprey_ET, net_load_day_ahead])
    net_load_guss['c1'] = net_load_guss.d.str[1:].astype(int)
    net_load_guss['c2'] = net_load_guss.hr.str[2:].astype(int)
    net_load_guss = net_load_guss.sort_values(by=['c1', 'c2'])
    net_load_guss = net_load_guss.drop(columns=['c1', 'c2'])
    net_load_guss = net_load_guss.set_index(['d', 'hr'])
    net_load_guss = net_load_guss.round(3)

    # Write net load to a csv file
    net_load_guss.to_csv(
        os.path.join(args['data_dir'],
                     'net_load_osprey_{}.csv'.format(args['tag'])))

    # =========================================================================
    # Transmission capacity and losses
    # =========================================================================

    print1('getting storage and transmission properties...')

    # Get transmission capacity
    cap_trans = gdxin['cap_trans'].rename(columns={'Value': 'MW'})

    # Get a capacity weighted average of transmission losses (combine AC and
    # DC lines)
    tranloss = gdxin['tranloss'].rename(columns={'Value': 'loss_factor'})
    tranloss = pd.merge(left=tranloss, right=cap_trans,
                        on=['r', 'rr', 'trtype'], how='right')
    tranloss = weighted_average(tranloss, ['loss_factor'], 'MW', ['r', 'rr'],
                                False, False)

    # Combine capacity of coinincident AC and DC lines
    cap_trans = cap_trans.groupby(['r', 'rr'], as_index=False).sum()

    # Get the transmission routes
    routes = gdxin['routes_filt'].copy()
    routes = pd.merge(left=routes, right=cap_trans[['r', 'rr']],
                      on=['r', 'rr'], how='right')

    # =========================================================================
    # Storage properties
    # =========================================================================

    # Storage duration
    durations = gdxin['storage_duration'].rename(
        columns={'Value': 'duration'})
    durations.i = durations.i.str.lower()

    # Energy capacity
    energy_cap_osprey = pd.merge(left=cap_storage_osprey,
                                 right=durations, on='i', how='left')
    energy_cap_osprey['MWh'] = energy_cap_osprey['MW'] \
        * energy_cap_osprey['duration']
    energy_cap_osprey = energy_cap_osprey[['i', 'v', 'r', 'MWh']]

    # Get the efficiency for storage technologies for the next solve year
    storage_eff = gdxin['storage_eff'].copy()

    # For incremental storage calculations, grab the efficiency for the next
    # solve year
    marg_storage_props = storage_eff[
        storage_eff['t'] == str(next_year)].reset_index(drop=True)
    marg_storage_props.i = marg_storage_props.i.str.lower()
    marg_storage_props.drop('t', axis=1, inplace=True)
    marg_storage_props.rename(columns={'Value': 'rte'}, inplace=True)
    # Filter out CSP
    marg_storage_props = marg_storage_props[marg_storage_props['i'].isin(
        techs['STORAGE_NO_CSP'])].reset_index(drop=True)
    # Merge in duration by i
    marg_storage_props = pd.merge(left=marg_storage_props, right=durations,
                                  on='i', how='inner')

    # TODO: this round-trip efficiency stuff assumes efficiency does not
    # change over time
    rte = storage_eff[['i', 'Value']].drop_duplicates().rename(
        columns={'Value': 'rte'})
    rte_osprey = rte.copy()
    # Filter out CSP
    rte_osprey = rte_osprey[rte_osprey['i'].isin(
        techs['STORAGE_NO_CSP'])].reset_index(drop=True)

    # Add duration, efficiency, energy cap, and device columns to cap_Osprey
    # for marginal curtailment script
    cap_storage_marg_curt = pd.merge(left=cap_storage_osprey, right=durations,
                                     on='i', how='inner')
    cap_storage_marg_curt['MWh'] = cap_storage_marg_curt['MW'] \
        * cap_storage_marg_curt['duration']
    cap_storage_marg_curt = pd.merge(left=cap_storage_marg_curt, right=rte,
                                     on='i', how='left')
    cap_storage_marg_curt['device'] = cap_storage_marg_curt['i'] \
        + cap_storage_marg_curt['v'] + cap_storage_marg_curt['r']

    # Storage capacity for reeds_cc -- aggregate over v index
    cap_storage_cc = cap_storage_marg_curt[
        ['i', 'r', 'MW', 'duration', 'MWh']].copy()
    # Aggregate storage by ccreg for cc script
    cap_storage_cc_agg = pd.merge(
        left=hierarchy[['r', 'ccreg']].drop_duplicates(),
        right=cap_storage_cc, on=['r'], how='right')
    # Get capacity weighted average efficiency by ccreg
    rte_cc_agg = pd.merge(left=cap_storage_cc_agg, right=rte, on='i',
                          how='left')
    rte_cc_agg = weighted_average(rte_cc_agg, ['rte'], 'MW', ['ccreg'], False,
                                  False)
    # Aggregate all storage capacity by ccreg
    cap_storage_ccreg = cap_storage_cc_agg[
        ['ccreg', 'MW', 'MWh']].groupby('ccreg', as_index=False).sum()
    cap_storage_ccreg = pd.merge(left=cap_storage_ccreg,
                                 right=rte_cc_agg[['ccreg', 'rte']],
                                 on='ccreg', how='left')

    # Storage duration bin set
    sdb = gdxin['sdbin'].copy()
    sdb.columns = ['bins', 'boolean']
    sdb.bins = sdb.bins.astype(int)
    sdb = sdb[['bins']]

    # Get storage capacity as it exists in ReEDS so curtailment recovery
    # results can be allocated correctly
    cap_storage_reeds = get_cap(gdxin, 'cap_storage')

    # Get the total storage capacity in each region and timeslice. This will
    # limit the storage_in_min parameter to
    # prevent infeasibilities in ReEDS. We derate the capacity by its seasonal
    # availability.
    cap_storage_r = pd.merge(left=cap_storage_osprey[['i', 'r', 'MW']],
                             right=avail[['i', 'r', 'szn', 'avail']],
                             on=['i', 'r'], how='left')
    cap_storage_r['MW'] *= cap_storage_r['avail']
    cap_storage_r = pd.merge(left=cap_storage_r, right=h_szn, on='szn')
    cap_storage_r.drop(['szn', 'avail'], axis=1, inplace=True)
    cap_storage_r = cap_storage_r.groupby(['r', 'h'], as_index=False).sum()

    # Get storage capital costs
    rsc_cost = gdxin['rsc_dat_filt'].copy()
    cost_cap = gdxin['cost_cap_filt'].copy()
    pvf = gdxin['pvf_onm'].rename(columns={'Value': 'pvf'})
    # Note the capital cost multipliers are indexed by valinv
    cost_cap_mult = gdxin['cost_cap_fin_mult_filt'].rename(
        columns={'Value': 'mult'})

    # Get the most expensive supply curve bin
    rsc_cost = rsc_cost[['i', 'r', 'Value']].groupby(
        ['i', 'r'], as_index=False).max()
    # Merge in capital cost multipliers
    rsc_cost = pd.merge(left=rsc_cost, right=cost_cap_mult, on=['i', 'r'],
                        how='inner')
    cost_cap = pd.merge(left=cost_cap, right=cost_cap_mult, on=['i', 't'],
                        how='inner')

    # Concatenate battery and pumped-hydro costs together
    marg_stor_techs = pd.concat([rsc_cost, cost_cap],
                                sort=False).reset_index(drop=True)
    # Merge in PVF
    marg_stor_techs = pd.merge(left=marg_stor_techs, right=pvf, on='t',
                               how='left')
    # Multiply capital cost by regional capital cost multipliers
    marg_stor_techs['Value'] *= marg_stor_techs['mult']
    # Divide by PVF
    marg_stor_techs['Value'] /= marg_stor_techs['pvf']
    marg_stor_techs.drop(['mult', 'pvf'], axis=1, inplace=True)
    marg_stor_techs = pd.merge(left=marg_stor_techs,
                               right=marg_storage_props, on='i', how='left')
    marg_stor_techs.rename(columns={'Value': 'cost'}, inplace=True)

    # CSP-TES data
    cap_csp_cc = get_cap(gdxin, 'cap_csp', return_cols=['i', 'r'])
    if cap_csp_cc.empty:
        cap_csp_cc = pd.DataFrame(columns=['i', 'r', 'MW'])
    csp_resources = pd.read_pickle(
        os.path.join('inputs_case', 'csp_resources_{}.pkl'.format(scenario)))
    csp_sm = gdxin['csp_sm'].copy()
    csp_sm.columns = ['i', 'sm']
    cap_csp_cc = cap_csp_cc.merge(csp_sm, on='i', how='left')
    cap_csp_cc = cap_csp_cc.merge(durations, on='i', how='left')
    cap_csp_cc['MWh'] = cap_csp_cc.MW * cap_csp_cc.duration
    cap_csp_cc = cap_csp_cc.merge(csp_resources, on=['i', 'r'], how='left')
    csp_resources = csp_resources.merge(csp_sm, on='i', how='left')
    csp_resources = csp_resources.merge(durations, on='i', how='left')

    # =========================================================================
    # Send formatted data to the CC script, LP, and dynamic programming script
    # =========================================================================

    print1('writing gdx file for osprey...')
    # Rounding inputs
    gen_cost = gen_cost.round(2)
    cap_osprey = cap_osprey.round(2)
    cap_trans = cap_trans.round(2)
    avail = avail.round(2)
    mingen = mingen.round(2)
    startcost = startcost.round(2)
    energy_cap_osprey = energy_cap_osprey.round(2)
    rte = rte.round(4)
    rte_osprey = rte_osprey.round(2)
    tranloss = tranloss.round(4)

    osprey_inputs = {'avail': avail,
                     'gen_cost': gen_cost,
                     'cap': cap_osprey,
                     'cap_trans': cap_trans,
                     'energy_cap': energy_cap_osprey,
                     'mingen': mingen,
                     'rfeas': rfeas,
                     'routes': routes,
                     'start_cost': startcost,
                     'storage_rte': rte_osprey,
                     'tranloss': tranloss}

    condor_data = {'cap': cap_osprey,
                   'cap_trans': cap_trans,
                   'gen_cost': gen_cost,
                   'marg_stor_techs': marg_stor_techs,
                   'rfeas': rfeas}

    curt_data = {'cap_storage_r': cap_storage_r,
                 'hours': hours,
                 'rfeas': rfeas,
                 'tz_map': tz_map,
                 'vre_gen_BA': vre_BA,
                 'cap': cap_osprey,
                 'mingen': mingen,
                 'vre_max_cf': vre_max_cf}

    marg_curt_data = {'cap_stor': cap_storage_marg_curt,
                      'cap_stor_reeds': cap_storage_reeds,
                      'cap_trans': cap_trans,
                      'cf_marginal': recf_marginal,
                      'durations': durations,
                      'hours': hours,
                      'marg_stor': marg_stor_techs,
                      'r_rs': r_rs,
                      'resources': resources,
                      'loss_rate': tranloss}

    reeds_cc_data = {'cap_csp': cap_csp_cc,
                     'cap_frac_cspns': cap_frac_cspns,
                     'cap_storage': cap_storage_cc,
                     'cap_storage_agg': cap_storage_ccreg,
                     'cf_marginal': recf_marginal_cc,
                     'csp_resources': csp_resources,
                     'hierarchy': hierarchy,
                     'load': load_ccreg,
                     'resources': resources,
                     'sdbin': sdb,
                     'vre_gen': vre_gen_cc}

    #%%
    osprey_input_file = os.path.join(
        args['data_dir'], 'osprey_inputs_{}.gdx'.format(args['tag']))
    gdxpds.to_gdx(osprey_inputs, osprey_input_file)

    return osprey_inputs, curt_data, marg_curt_data, condor_data, reeds_cc_data
