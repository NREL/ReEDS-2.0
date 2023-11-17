# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 08:59:00 2020
@author: afrazier
"""
#%%
import os
import subprocess

if os.name == 'posix':
    os.environ['GAMS_DIR'] = os.path.dirname(subprocess.check_output(['which', 'gams'])).decode()

import gdxpds
import pandas as pd
import numpy as np
from utilities import get_cap, tech_types, weighted_average, get_solar_cap, get_osprey_cap
#%%
def prep_data(args):
    '''
    This funciton prepares the data for Osprey and packages it into a single gdx file.
    Outputs:
        - osprey_inputs_{scenario}_{year}.gdx for Osprey
        - Returns condor_data, reeds_cc_data, curt_data, marg_curt_data
            - These are dictionaries containing data that is used downstream in the augur workflow
    Details on data that is processed:
        - spatial mappers
            - rfeas, r_rs, r_region
        - generator capacity
            - cap_osprey has any generator less than 5 MW dropped and includes only thermal capacities
            - cap_solar has csp-ns, if applicable, added to the highest quality PV resource class in the same region
            - cap_pv, cap_storage_cap_thermal_cap_wind
            - capacities sent to reeds_cc are aggregated by v (and t for wind)
        - generator availability
            - thermal generator availabilities come straight from ReEDS
            - hydro availability is done like it is in the ReEDS2PLEXOS translation
        - mingen data
            - mingen comes from ohourly_operational_characteristics.csv
            - hydro mingen levels are calculated as they are in the ReEDS2PLEXOS translation
                - The default in ReEDS is 0.5. This value is often higher than the hydro availability
                  numbers described above, so instead we use the capacity-weighted average mingen level 
                  from the available data, which is 0.0985. In some cases, even 0.0985 is higher then 
                  the seasonal CF. In these rare cases, we assign the CF to be the mingen value, 
                  essentially making these few generators non-dispatchable.
        - start cost data
            - also comes from hourly_operational_characteristics.py
        - fuel costs
            - taken directly from ReEDS
        - heat rates
            - these are taken directly from ReEDS and are used to adjust fuel costs to Rs/MWh
        - vom
            - taken directly from ReEDS
        - VRE generation profiles
            - wind profiles are scaled by a capacity-weighted average of their vintage-specific capacity factors
                - These generation profiles are capped at a capacity factor of 1 for capacity credit calculations
                - They are allowed to exceed 1 in Osprey, so the total generation in ReEDS and Osprey match
            - solar profiles included csp-ns (see "cap_solar" in generator capacities above)
            - marginal cf profiles are scaled by the wind vintage of the next ReEDS iteration
        - net load profiles
            - load_LP is used in Osprey and is calculated just as load is adjusted in ReEDS2PLEXOS
                - transmission losses are added to the region sending the power
            - load_CC is used in the reeds_capacity_credit and is not adjusted by transmission losses
        - transmission capacity and loss factors
            - for any regions with both AC and DC transmission, these are combined into a single line
              and a capcaity-weighted average loss factor is used
        - Storage energy capacity and round-trip efficiencies come straight from ReEDS
    '''

#%%  

    
    if os.name!="posix":
        print('getting Osprey generator data...')
    
    scenario = args['scenario']
    user, runname = scenario.split('_')[0], scenario.split('_')[0] + '_' + scenario.split('_')[1]
    next_year = args['next_year']

    # technology types from tech_subset_table
    techs = tech_types(args)
    # data from ReEDS
    gdx_file = os.path.join(args['data_dir'],'reeds_data_{}.gdx'.format(args['tag']))
    gdxin = gdxpds.to_dataframes(gdx_file)
    # hourly temporal mapper
    hdtmap = pd.read_csv(os.path.join('A_Inputs','inputs','variability','h_dt_szn.csv'))
    hdtmap_single = hdtmap[hdtmap.year == args['year']].reset_index(drop = True)

    # Getting hours in each timeslice
    hours = gdxin['hours'].copy()
    hours.columns = ['h','hours']
    
    # Gettting timeslice to season mapper
    h_szn = gdxin['h_szn'].copy()
    h_szn.drop('Value', axis=1, inplace=True)
    
    # Getting number of hours in each season
    szn_hours = pd.merge(left=h_szn, right=hours, on='h', how='inner')
    szn_hours = szn_hours.groupby('szn').sum()
    szn_hours['total'] = szn_hours['hours'].sum()
    # Fraction of total hours that are in each season
    szn_hours['szn_frac'] = szn_hours['hours'] / szn_hours['total']
   
    # =============================================================================
    # Get spatial mappers
    # =============================================================================
    
    # Regions that exist in this scenario
    rfeas = gdxin['rfeas'].drop('Value',1)
            
    # Mapping resource regions to BAs
    r_rs = gdxin['r_rs'].drop('Value',1)
    # Filter for regions that exist in this scenario
    r_rs = r_rs[r_rs['r'].isin(rfeas['r'])].reset_index(drop=True)
    # TODO! eventually "sk" will be removed entirely from the model
    r_rs = r_rs[r_rs['rs']!='sk'].reset_index(drop=True)
    
    # Mapping BA to regions (for load scaling)
    r_region = gdxin['r_region'].drop('Value',1)
    # Filter for regions that exist in this scenario
    r_region = r_region[r_region['r'].isin(rfeas['r'])].reset_index(drop=True)
    
    # Hiearchy maps BAs to regions, but also includes all other spatial mapping
    hierarchy = gdxin['hierarchy'].copy().drop('Value',1)
    hierarchy = hierarchy[hierarchy['r'].isin(rfeas['r'])].reset_index(drop=True)
    hierarchy = pd.merge(left=r_rs, right=hierarchy, on='r', how='right')
#%%     
    # =============================================================================
    # Generator capacity
    # =============================================================================
    
    # Capacity for Osprey - includes cap_thermal from reeds_data gdx file.
    # Generators smaller than than osprey_min_plant_size (default=5MW) are dropped.
    cap_osprey = get_osprey_cap(gdxin, r_rs, min_plant_size=args['osprey_min_plant_size'])
    # Get storage capacity, aggregating over vintage
    cap_storage_osprey = get_cap(gdxin, 'cap_storage', return_cols=['i','r'])
    # Define a generic vintage for storage
    cap_storage_osprey['v'] = 'new1'
    # Filter storage devices for osprey by osprey_min_storage_size
    cap_storage_osprey = cap_storage_osprey[cap_storage_osprey['MW']>args['osprey_min_storage_size']].reset_index(drop=True)
    # Concatenate storage capacity with Osprey capacity
    cap_osprey = pd.concat([cap_osprey,cap_storage_osprey], sort=False).reset_index(drop=True)
    
    # =============================================================================
    # Generator availability - outage rates and seasonal hydro capacity factors
    # =============================================================================
    
    # Availability rates for thermal technologies
    avail = gdxin['avail_filt'].copy().rename(columns={'Value':'avail'})
    avail.loc[:,'i'] = avail.loc[:,'i'].str.lower()
    # avail is indexed by i, v, and szn. We want it indexed by r as well, so we
    # merge it with cap_osprey here. This will also remove any values in avail
    # that don't have a matching value in cap_osprey.
    avail = pd.merge(left=avail, right=cap_osprey[['i','v','r']].drop_duplicates(), on=['i','v'], how='inner')
    # reorder the columns to match ReEDS convention
    avail = avail[['i','v','r','szn','avail']]
   
    # Seasonal hydro capacity factors
    cfhyd = gdxin['cf_hyd_filt'].copy().rename(columns={'Value':'cf'})
    cfhyd.loc[:,'i'] = cfhyd.loc[:,'i'].str.lower()
    # cfhyd is indexed by i, r, and szn. We want it indexed by v as well, so we
    # merge it with cap_osprey here. This will also remove any values in cf_hyd
    # that don't have a matching value in cap_osprey.
    cfhyd = pd.merge(left=cfhyd, right=cap_osprey[['i','v','r']].drop_duplicates(), on=['i','r'], how='inner')
    # reorder the columns to match ReEDS convention
    cfhyd = cfhyd[['i','v','r','szn','cf']]
    # Combine seasonal hydro CFs with outage rates
    avail = pd.merge(left=avail, right=cfhyd, on=['i','v','r','szn'], how='left').fillna(1)
    avail['avail'] *= avail['cf']
    avail = avail[['i','v','r','szn','avail']]
    
    # =============================================================================
    # mingen levels & start costs
    # =============================================================================
    
    # Read in data
    oper_data = pd.read_csv(os.path.join('A_Inputs','inputs','variability','hourly_operational_characteristics.csv'))

    # Get mingen data
    mingen = oper_data[['category','Min Stable Level/capacity']].reset_index(drop=True)
    mingen.columns = ['i','mingen']
    mingen.loc[:,'i'] = mingen.loc[:,'i'].str.lower()
    # mingen is indexed by i. We want it indexed by r and szn as well, so we
    # merge it with cap_osprey here. This will also remove any values in mingen
    # that don't have a matching value in cap_osprey.
    mingen = pd.merge(left=mingen, right=avail[['i','r','szn']].drop_duplicates(), on='i', how='right')

    # Hydro mingen is done separately to reflect the seasonal variarions
    mingen = mingen[~mingen['i'].isin(techs['HYDRO'])].reset_index(drop=True)
    hydmin = gdxin['hydmin'].copy().rename(columns={'Value':'mingen'})
    hydmin.loc[:,'i'] = hydmin.loc[:,'i'].str.lower()

    # mingen level for non-dispatchable hydro is equal to the seasonal CF
    hydmin_nd = avail[['i','r','szn','avail']].drop_duplicates()
    hydmin_nd = hydmin_nd[hydmin_nd['i'].isin(techs['HYDRO_ND'])].reset_index(drop=True).rename(columns={'avail':'mingen'})
    hydmin = pd.concat([hydmin,hydmin_nd], sort=False).reset_index(drop=True)
    
    # Consolidate all mingen levels
    mingen = pd.concat([mingen,hydmin], sort=False).reset_index(drop=True)
    mingen = mingen[['i','r','szn','mingen']]
    
    # Get start cost data
    startcost = oper_data[['category','Start Cost/capacity']].fillna(0)
    startcost.columns = ['i','startcost']
    startcost.loc[:,'i'] = startcost.loc[:,'i'].str.lower()
    # Filter for the startcosts that are included in each i column
    startcost = pd.merge(left=startcost, right=cap_osprey[['i']].drop_duplicates(), on='i', how='inner')
    
    # =============================================================================
    # Calculate marginal generator costs
    # =============================================================================
    
    # Get fuel costs
    fuel = gdxin['fuel_price_filt'].copy().rename(columns={'Value':'fuel Rs/MMBtu'})
    fuel.i = fuel.i.str.lower()
    # Concatenate fuel prices with biofuel prices
    #fuel = pd.concat([fuel,biofuel], sort=False).reset_index(drop=True)
    
    # Fuel prices will be adjusted by heat rate to convert to $/MWh
    heatrate = gdxin['heat_rate_filt'].copy().rename(columns={'Value':'heatrate'})
    heatrate.loc[:,'i'] = heatrate.loc[:,'i'].str.lower()
    
    # NOTE: for techs with heat rate but no fuel cost, we want to fill na with 0.
    # for those with fuel cost but no heat rate (or vom), this is also being set to 0 here.
    # We could set how='left' here to drop these instances of no heat rate.
    fuel = pd.merge(left=heatrate, right=fuel, on=['i','r'], how='outer').fillna(0)
    fuel['fuel Rs/MWh'] = fuel['heatrate'] * fuel['fuel Rs/MMBtu']
    
    # Add vom costs to fuel prices to get marginal operating costs
    vom = gdxin['cost_vom_filt'].copy().rename(columns={'Value':'vom Rs/MWh'})
    vom.i = vom.i.str.lower()
    vom = pd.merge(left=vom, right=fuel[['i','v','r','fuel Rs/MWh']], on=['i','v','r'], how='outer').fillna(0)
    vom['op_cost'] = vom['vom Rs/MWh'] + vom['fuel Rs/MWh']
    
    # Filter for only installed capacities in ReEDS
    vom = pd.merge(left=vom, right=cap_osprey[['i','v','r']], on=['i','v','r'], how='right').fillna(0)

    gen_cost = vom[['i','v','r','op_cost']].copy()
    
    # =============================================================================
    # Calculate VRE generation profiles
    # =============================================================================
#%%    
    if os.name!="posix":
        print('getting VRE capacity...')
    
    # Get CF profiles and resources
    recf = pd.read_pickle(os.path.join(args['data_dir'],'recf_{}.pkl'.format(scenario)))
    resources = pd.read_pickle(os.path.join(args['data_dir'],'resources_{}.pkl'.format(scenario)))

    #Filter datetime mapper to a single year if only running with one year of data
    if len(recf) == 8760:
        hdtmap = hdtmap_single

    # Map resource to BA
    resource_r = pd.merge(left=resources[['resource','area']].rename(columns={'area':'rs'}), right=r_rs, on='rs', how='outer')
    resource_r['r'].fillna(resource_r['rs'], inplace=True)
    resource_r.drop('rs',1,inplace=True)
    
    # Get wind capacity factors by year
    # wind_cf = gdxin['cf_adj_t_filt'].copy()
    # wind_cf.columns = ['i','v','t','windCF']
   
    # Filter for valid vintage-build year combinations 
    # - not relevant for India because wind CFs do not change over time
    # ivt = pd.read_csv(os.path.join('A_Inputs','inputs','generators','ivt.csv'), index_col=0)
    # ivt_wind = ivt.loc['WIND'].reset_index()
    # ivt_wind.columns = ['t','v']
    # ivt_wind['v'] = 'new' + ivt_wind['v'].astype('int').astype(str)
    # # Get all of the init vintages in the v set
    # vintages = gdxin['v'].copy()
    # vintages = vintages[vintages['*'].str.contains('init')]['*'].tolist()
    # for v in vintages:
    #     ivt_wind.loc[len(ivt_wind)] = [next_year,v]
    # # Filter for valid vintage-build year combinations
    # wind_cf = pd.merge(left=wind_cf, right=ivt_wind, on=['t','v'], how='right')
    
    # Get the mean of all CF profiles
#     wind_scaling = recf.mean().reset_index() # 0.25 s
#     wind_scaling.columns = ['resource','Mean']
    
#     # Scale wind CFs by the ratio between the CF from ReEDS and the mean of the CF profile
#     wind_scaling = pd.merge(left=resources,right=wind_scaling, on='resource')
#     wind_scaling = wind_scaling.rename(columns={'tech':'i','area':'r'})
#     wind_scaling = pd.merge(left=wind_scaling,right=wind_cf, on='i', how='left')
#     index_wind = (wind_scaling['i'].isin(techs['WIND']))
#     index_notwind = (wind_scaling['i'].isin(techs['WIND'])==False)
#     wind_scaling.loc[index_wind,'scaling_factor'] = wind_scaling.loc[index_wind,'windCF'] / wind_scaling.loc[index_wind,'Mean']
#     wind_scaling.loc[index_notwind,'scaling_factor'] = 1
    
    # Get a capacity weighted average scaling factor for all wind capacity
    cap_onswind = gdxin['cap_onswind'].copy()
    cap_ofswind = gdxin['cap_ofswind'].copy()
    #cap_wind = pd.merge(left=cap_wind, right=wind_scaling[['i','v','r','t','scaling_factor']].drop_duplicates(), on=['i','v','r','t'], how='left')
    #scale_factor = weighted_average(cap_wind, ['scaling_factor'], 'MW', ['i','r'], False, False)
   
    # Aggregate all wind capacity by resource region
    cap_onswind = cap_onswind.rename(columns={'Value':'MW'})
    cap_ofswind = cap_ofswind.rename(columns={'Value':'MW'})
    cap_onswind = cap_onswind[['i','r','MW']].groupby(['i','r'], as_index=False).sum()
    cap_ofswind = cap_ofswind[['i','r','MW']].groupby(['i','r'], as_index=False).sum()
    
    # Get solar capacity. This includes csp-ns capacity, aggregated to the BA
    # level and assigned to the highest available UPV resource class in the BA.
    cap_solar = get_solar_cap(gdxin, r_rs, resources, techs, args)
    
    # Create a single DataFrame of all VRE capacity
    cap_vre = pd.concat([cap_solar,cap_onswind,cap_ofswind], sort=False).reset_index(drop=True)
    cap_vre['i'] = cap_vre.i.str.upper()
    cap_vre['resource'] = cap_vre['i'] + '_' + cap_vre['r']
    cap_vre = pd.merge(left=resources[['tech','area','resource']].rename(columns={'tech':'i','area':'r'}), right=cap_vre, on=['i','r','resource'], how='left').fillna(0)
#    cap_vre = pd.merge(left=cap_vre, right=scale_factor, on=['i','r'], how='left').fillna(1)
#%%    
    if os.name!="posix":
        print('getting VRE gen profiles...')
    # Create a DataFrame of all VRE generation: RECF * VRE cap * scaling_factor
    vre_gen = recf.copy()
    cap_vre_temp = cap_vre['MW'].values
    cap_vre_temp = np.tile(cap_vre_temp.reshape(1,len(cap_vre)), (len(vre_gen),1))
    # scaling_factor_temp = cap_vre['scaling_factor'].values
    # scaling_factor_temp = np.tile(scaling_factor_temp.reshape(1,len(cap_vre)), (len(vre_gen),1))
   # vre_gen *= cap_vre_temp * scaling_factor_temp
    vre_gen *= cap_vre_temp
    # Create another DataFrame with this information clipped at CF=1 for the capacity credit script
    vre_gen_cc = pd.DataFrame(columns=vre_gen.columns, data=np.clip(vre_gen.values, a_min=0, a_max = cap_vre_temp, out=vre_gen.values))
    vre_gen_cc = pd.concat([hdtmap,vre_gen_cc], axis=1)
    
    # For marginal wind, use only the scaling factor for the next solve year 
    # - skipping for India
    # wind_scaling_marginal = wind_scaling[wind_scaling['t']==str(next_year)].reset_index(drop=True)
    # pv_scaling_marginal = wind_scaling[wind_scaling['i'].isin([techs[x] for x in ['UPV','DISTPV']])].reset_index(drop=True)
    # wind_scaling_marginal = pd.concat([pv_scaling_marginal,wind_scaling_marginal], sort=False).reset_index(drop=True)
    # wind_scaling_marginal = pd.merge(left=resources[['resource']], right=wind_scaling_marginal, on='resource', how='left')
    # wind_scaling_marginal = wind_scaling_marginal['scaling_factor'].values
    # wind_scaling_marginal = np.tile(wind_scaling_marginal.reshape(1,len(resources)), (len(recf),1))
    marg_vre_mw = np.tile(args['reedscc_marg_vre_mw'], (len(recf),len(resources)))
    
    # Scale recf by wind scaling factor and by the marginal VRE step size
    # recf_marginal = recf * wind_scaling_marginal * marg_vre_mw
    recf_marginal = recf * marg_vre_mw
    # Clip the CF to be no greater than 1 for the CC script
    recf_marginal_cc = pd.DataFrame(columns=recf_marginal.columns, data=np.clip(recf_marginal.values, a_min=0, a_max=marg_vre_mw, out=recf_marginal.values))
    recf_marginal_cc = pd.concat([hdtmap,recf_marginal],axis=1) 
    # When running for multiple years, this includes hourly data for 7 years
    # Subsetting marginal resource CF to online include the 2012 profile for curtailment calculation
    recf_marginal = recf_marginal_cc[recf_marginal_cc.year==args['year']].reset_index(drop=True)
    recf_marginal = recf_marginal.drop(list(hdtmap.columns),axis=1)
#%%     
    # Get the max generation from vre in each timeslice
    m_cf = gdxin['m_cf_filt'].copy()
    m_cf.loc[:,'i'] = m_cf.loc[:,'i'].str.lower()
    vre_cap_ons = gdxin['cap_onswind']
    vre_cap_ofs = gdxin['cap_ofswind']
    vre_cap_ons = vre_cap_ons.rename(columns={'Value':'MW'})
    vre_cap_ofs = vre_cap_ofs.rename(columns={'Value':'MW'})
    vre_cap = pd.concat([vre_cap_ons, vre_cap_ofs, get_cap(gdxin, 'cap_pv')], sort=False).reset_index(drop=True)
    vre_cap.loc[:,'i'] = vre_cap.loc[:,'i'].str.lower()

    vre_max_cf = pd.merge(left=vre_cap, right=m_cf, on=['i','v','r'], how='left')
    vre_max_cf['MW'] *= vre_max_cf['Value']
    vre_max_cf.drop('Value', axis=1, inplace=True)
    vre_max_cf = pd.merge(left=r_rs, right=vre_max_cf.rename(columns={'r':'rs'}), on='rs', how='right')
    vre_max_cf['r'].fillna(vre_max_cf['rs'], inplace=True)
    vre_max_cf = vre_max_cf.groupby(['r','h'], as_index=False).sum()
#%%    
    # =============================================================================
    # Calculate load
    # =============================================================================
    
    if os.name!="posix":
        print('getting load and net load profiles...')

    # Get load profiles
    load = pd.read_pickle(os.path.join(args['data_dir'],'load_{}.pkl'.format(scenario)))
    # EFS profiles are indexed by year and hour index
    # If there are two index names for load, then we know we are using EFS profiles
    # if(len(load.index.names)==2):
        # YearIndexed=True
    load=load.loc[load['Year']==int(next_year)]
    load=load.drop('Year',axis=1)
    load=load.reset_index(drop=True)
    # else:
        # YearIndexed=False
        # load=load.reset_index(drop=True)
        
    # Adjust load for growth for both Osprey and reeds_cc
    # load_mult = gdxin['load_multiplier'].copy()
    # load_mult.columns = ['region','t','Value']
    # load_mult = load_mult.pivot(index='region', columns='t', values='Value').reset_index()
    # load_mult = pd.merge(left=r_region, right=load_mult, on='region', how='left') 
    # load_mult = load_mult.sort_values('r')[str(next_year)].values
    # load_mult = np.tile(load_mult.reshape(1,len(rfeas)), (len(load),1))

    # # Do not apply load multiplier for EFS load
    # if(not YearIndexed):
    # 	load *= load_mult
#%% 
    # Get SA imports and exports
    # Add/subtract exports/imports to load if including South Asia
    Sw_SAsia_Trade = gdxin['Sw_SAsia_Trade'].copy()

    if Sw_SAsia_Trade.loc[0,'Value'] == 1:
        trade = pd.read_pickle(os.path.join('D_Augur','LDCfiles','SAsia_8760_Trade.pkl'))
        trade=trade.loc[trade['Year']==int(next_year)]
        trade=trade.drop('Year',axis=1)
        trade=trade.reset_index(drop=True)
        trade = trade.round(2)

        trade_states = np.intersect1d(load.columns, trade.columns).tolist()

        load[trade_states] = load[trade_states] + trade[trade_states] 

#%%

    # Sum the load profiles for each region for reeds_cc
    load_region = load.transpose().reset_index()
    load_region = pd.merge(left=hierarchy[['region','r']].drop_duplicates().rename(columns={'r':'index'}), right=load_region, on='index', how='right').drop('index',1)
    load_region = load_region.groupby('region').sum().transpose()
    load_region = pd.concat([hdtmap,load_region], axis=1)
#%%    
    # =============================================================================
    # Calculate net load for Osprey
    # =============================================================================
    
    # Sum the VRE generation by BA to get the net load
    vre_BA = vre_gen.transpose().reset_index()
    vre_BA = pd.merge(left=resource_r[['r','resource']].rename(columns={'resource':'index'}), right=vre_BA, on='index').drop('index',1)
    vre_BA = vre_BA.groupby('r').sum().transpose()
    # When running for multiple years, this includes hourly data for 7 years
    # filter data to current year to subtract from net load profile for osprey and curtailment calculation
    vre_BA = pd.concat([vre_BA,hdtmap['year']], axis=1)
    vre_BA = vre_BA[vre_BA.year==args['year']].reset_index(drop=True)
    vre_BA = vre_BA.drop('year',axis=1)

    # When running for multiple years, this includes hourly data for 7 years
    # filter data to current year to subtract from net load profile for osprey and curtailment calculation
    load = pd.concat([hdtmap['year'],load], axis=1)
    load = load[load.year==args['year']].reset_index(drop=True)
    load = load.drop('year',axis=1)

    # Adjust load for transmission losses only for Osprey
    if 'reeds_transloss' not in args.keys():
        args['reeds_transloss'] = False
        
    if args['reeds_transloss']:
        hmap = pd.read_csv(os.path.join('A_Inputs','inputs','variability','superpeak_hour_mapper.csv'))
        hours = gdxin['hours'].copy()
        hours.columns = ['h','hours']
        losses = gdxin['losses_trans_h'].groupby(['r','h'], as_index=False).sum()
        losses = pd.merge(left=losses, right=hours, on='h', how='left')
        losses = pd.merge(left=losses, right=hmap, on='h', how='left')
        losses = weighted_average(losses, ['Value'], 'hours', ['r','h_true'], 'h', 'h_true')
        losses = losses.pivot(index='h', columns='r', values='Value').reset_index()
        losses = pd.merge(left=hdtmap_single, right=losses, on='h', how='right').fillna(0)
        for col in load.columns:
            if col not in losses.columns:
                losses.loc[:,col] = 0
        losses = pd.merge(left=hdtmap_single[['hour']], right=losses, on='hour', how='left')
        losses = losses[load.columns.tolist()].values
        
        load_Osprey = load + losses
        
    else:
        load_Osprey = load.copy()
    
    # Get net load
    net_load_Osprey = load_Osprey - vre_BA
#%%     
    # Create hour and day columns
    flatten = lambda l: [item for sublist in l for item in sublist]
    day = flatten([['d'+str(i+1)]*24 for i in range(365)])
    net_load_Osprey['d'] = day
    hour = ['hr'+str(i+1) for i in range(24)]*365
    net_load_Osprey['hr'] = hour
    
    # Roll the hour and day columns for the day ahead load
    net_load_day_ahead = net_load_Osprey.copy()
    day = np.roll(net_load_day_ahead.d.values, 24)
    hour = np.roll(net_load_day_ahead.hr.values, 24)
    hour = np.array(['hr'+str(int(i[2:]) + 24) for i in hour])
    net_load_day_ahead.d = day
    net_load_day_ahead.hr = hour
    
    # Combine the load and day ahead load into a single table
    net_load_guss = pd.concat([net_load_Osprey, net_load_day_ahead])
    net_load_guss['c1'] = net_load_guss.d.str[1:].astype(int)
    net_load_guss['c2'] = net_load_guss.hr.str[2:].astype(int)
    net_load_guss = net_load_guss.sort_values(by=['c1', 'c2'])
    net_load_guss = net_load_guss.drop(columns=['c1', 'c2'])
    net_load_guss = net_load_guss.set_index(['d', 'hr'])
    net_load_guss = net_load_guss.round(3)
#    net_load_guss = net_load_guss.drop('Year', axis=1)

    # Write net load to a csv file
    net_load_guss.to_csv(os.path.join(args['data_dir'], 'net_load_osprey_{}.csv'.format(args['tag'])))
    
    # =============================================================================
    # Transmission capacity and losses
    # =============================================================================
    
    if os.name!="posix":
        print('getting storage and transmission properties...')
    
    # Get transmission capacity
    cap_trans = gdxin['cap_trans'].copy().rename(columns={'Value':'MW'})
    
    # Get a capacity weighted average of transmission losses (combine AC and DC lines)
    tranloss = gdxin['tranloss'].copy().rename(columns={'Value':'loss_factor'})
    tranloss = pd.merge(left=tranloss, right=cap_trans, on=['r','rr'], how='right')
    tranloss = weighted_average(tranloss, ['loss_factor'], 'MW', ['r','rr'], False, False)
    
    # Combine capacity of coinincident AC and DC lines
    cap_trans = cap_trans.groupby(['r','rr'], as_index=False).sum()
    
    # Get the transmission routes
    routes = gdxin['routes_filt'].copy()
    routes = pd.merge(left=routes, right=cap_trans[['r','rr']], on=['r','rr'], how='right')
    
    # =============================================================================
    # Storage properties
    # =============================================================================
#%%    
    # Storage duration
    durations = gdxin['storage_duration'].copy().rename(columns={'Value':'duration'})
    durations.loc[:,'i'] = durations.loc[:,'i'].str.lower()
    
    # Energy capacity
    energy_cap_osprey = pd.merge(left=cap_storage_osprey, right=durations, on='i', how='left')
    energy_cap_osprey['MWh'] = energy_cap_osprey['MW'] * energy_cap_osprey['duration']
    energy_cap_osprey = energy_cap_osprey[['i','v','r','MWh']]
    
    # Get the efficiency for storage technologies for the next solve year
    storage_eff = gdxin['storage_eff'].copy()
    storage_eff.loc[:,'i'] = storage_eff.loc[:,'i'].str.lower()
#%%   
    # For incremental storage calculations, grab the efficiency for the next solve year 
    # - different for India because storage efficiency does not change over time
    #marg_storage_props = storage_eff[storage_eff['t']==str(next_year)].reset_index(drop=True)
    marg_storage_props = storage_eff.copy()
    marg_storage_props.loc[:,'i'] = marg_storage_props.loc[:,'i']
    #marg_storage_props.drop('t', axis=1, inplace=True)
    marg_storage_props.rename(columns={'Value':'rte'}, inplace=True)
    # Merge in duration by i
    marg_storage_props = pd.merge(left=marg_storage_props, right=durations, on='i', how='inner')
    
    # TODO: this round-trip efficiency stuff assumes efficiency does not change over time
    rte = storage_eff[['i','Value']].drop_duplicates().rename(columns={'Value':'rte'})
    rte_osprey = rte.copy()
 
    # Add duration, efficiency, energy cap, and device columns to cap_Osprey for marginal curtailment script
    cap_storage_marg_curt = pd.merge(left=cap_storage_osprey, right=durations, on='i', how='inner')
    cap_storage_marg_curt['MWh'] = cap_storage_marg_curt['MW'] * cap_storage_marg_curt['duration']
    cap_storage_marg_curt = pd.merge(left=cap_storage_marg_curt, right=rte, on='i', how='left')
    cap_storage_marg_curt['device'] = cap_storage_marg_curt['i'] + cap_storage_marg_curt['v'] + cap_storage_marg_curt['r']
    
    # Storage capacity for reeds_cc -- aggregate over v index
    cap_storage_cc = cap_storage_marg_curt[['i','r','MW','duration','MWh']].copy()
    # Aggregate storage by region for cc script
    cap_storage_cc_agg = pd.merge(left=hierarchy[['r','region']].drop_duplicates(), right=cap_storage_cc, on=['r'], how='right')
    # Get capacity weighted average efficiency by region
    rte_cc_agg = pd.merge(left=cap_storage_cc_agg, right=rte, on='i', how='left')
    rte_cc_agg = weighted_average(rte_cc_agg, ['rte'], 'MW', ['region'], False, False)
    # Aggregate all storage capacity by region
    cap_storage_region = cap_storage_cc_agg[['region','MW','MWh']].groupby('region', as_index=False).sum()
    cap_storage_region = pd.merge(left=cap_storage_region, right=rte_cc_agg[['region','rte']], on='region', how='left')
#%%
    # Storage duration bin set
    sdb = gdxin['sdbin'].copy()
    sdb.columns = ['bins','boolean']
    sdb.loc[:,'bins'] = sdb.loc[:,'bins'].astype(int)
    sdb = sdb[['bins']]
    
    # Get storage capacity as it exists in ReEDS so curtailment recovery results can be allocated correctly
    cap_storage_reeds = get_cap(gdxin, 'cap_storage')
    
    # Get the total storage capacity in each region and timeslice. This will limit the storage_in_min parameter to 
    # prevent infeasibilities in ReEDS. We derate the capacity by its seasonal availability.
    cap_storage_r = pd.merge(left=cap_storage_osprey[['i','r','MW']], right=avail[['i','r','szn','avail']], on=['i','r'], how='left')
    cap_storage_r['MW'] *= cap_storage_r['avail']
    cap_storage_r = pd.merge(left=cap_storage_r, right=h_szn, on='szn')
    cap_storage_r.drop(['szn','avail'], axis=1, inplace=True)
    cap_storage_r = cap_storage_r.groupby(['r','h'], as_index=False).sum()
    
    # Get storage capital costs
    #rsc_cost = gdxin['rsc_dat_filt'].copy()
    #rsc_cost['i'] = rsc_cost['i'].str.lower()
    cost_cap = gdxin['cost_cap_filt'].copy()
    cost_cap['i'] = cost_cap['i'].str.lower()
    # pvf_onm = gdxin['pvf_onm'].copy().rename(columns={'Value':'pvf_o'})
    # pvf_capital = gdxin['pvf_capital'].copy().rename(columns={'Value':'pvf_c'})

    # # Note the capital cost multipliers are indexed by valinv
    cost_cap_mult = gdxin['cost_cap_fin_mult_filt'].copy().rename(columns={'Value':'mult'})
    cost_cap_mult['i'] = cost_cap_mult['i'].str.lower()

    # # Get the most expensive supply curve bin
    # #rsc_cost = rsc_cost[['i','r','Value']].groupby(['i','r'], as_index=False).max()
    # # Merge in capital cost multipliers
    # #rsc_cost = pd.merge(left=rsc_cost, right=cost_cap_mult, on=['i','r'], how='inner')
    cost_cap = pd.merge(left=cost_cap, right=cost_cap_mult, on=['i','t'], how='inner')
    
    # Concatenate battery and pumped-hydro costs together
    marg_stor_techs = cost_cap.copy()
    # Merge in PVF
    # marg_stor_techs = pd.merge(left=marg_stor_techs, right=pvf_onm, on='t', how='left')
    # marg_stor_techs = pd.merge(left=marg_stor_techs, right=pvf_capital, on='t', how='left')

    # # Multiply capital cost by regional capital cost multipliers
    # marg_stor_techs['Value'] *= marg_stor_techs['mult']
    # # Multiply by PFV_CAPITAL
    # marg_stor_techs['Value'] *= marg_stor_techs['pvf_c']
    # # Divide by PVF_ONM
    # marg_stor_techs['Value'] /= marg_stor_techs['pvf_o']
    # marg_stor_techs.drop(['mult','pvf_o','pvf_c'], axis=1, inplace=True)
    marg_stor_techs = pd.merge(left=marg_stor_techs, right=marg_storage_props, on='i', how='left')
    marg_stor_techs.rename(columns={'Value':'cost'}, inplace = True)
#%%   
    # =============================================================================
    # Send formatted data to the CC script, LP, and dynamic programming script
    # =============================================================================
    
    if os.name!="posix":
        print('writing gdx file for osprey...')
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
    
    osprey_inputs = {'avail':avail,
                     'gen_cost':gen_cost,
                     'cap':cap_osprey,
                     'cap_trans':cap_trans,
                     'energy_cap':energy_cap_osprey,
                     'mingen':mingen,
                     'rfeas':rfeas,
                     'routes':routes,
                     'start_cost':startcost,
                     'storage_rte':rte_osprey,
                     'tranloss':tranloss}
    
    condor_data = {'cap':cap_osprey,
                             'cap_trans':cap_trans,
                             'gen_cost':gen_cost,
                             'marg_stor_techs':marg_stor_techs,
                             'rfeas':rfeas}
    
    curt_data = {'cap_storage_r':cap_storage_r,
                 'hours':hours,
                 'rfeas':rfeas,
                 'vre_gen_BA':vre_BA,
                 'cap':cap_osprey,
                 'mingen':mingen,
                 'vre_max_cf':vre_max_cf}
    
    marg_curt_data = {'cap_stor':cap_storage_marg_curt,
                      'cap_stor_reeds':cap_storage_reeds,
                      'cap_trans':cap_trans,
                      'cf_marginal':recf_marginal,
                      'durations':durations,
                      'hours':hours,
                      'marg_stor':marg_stor_techs,
                      'r_rs':r_rs,
                      'resources':resources,
                      'loss_rate':tranloss}
    
    reeds_cc_data = {'cap_solar':cap_solar,
                     'cap_storage':cap_storage_cc,
                     'cap_storage_agg':cap_storage_region,
                     'cf_marginal':recf_marginal_cc,
                     'hierarchy':hierarchy,
                     'load':load_region,
                     'resources':resources,
                     'sdbin':sdb,
                     'vre_gen':vre_gen_cc}
    
    #%%
    osprey_input_file = os.path.join(args['data_dir'],'osprey_inputs_{}.gdx'.format(args['tag']))
    gdxpds.to_gdx(osprey_inputs, osprey_input_file)

    return osprey_inputs, curt_data, marg_curt_data, condor_data, reeds_cc_data