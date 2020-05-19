# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 14:31:05 2018
@author: afrazier
"""

import gdxpds 
import numpy as np
import pandas as pd
import os
import logging
import traceback
import argparse

#%%  DEFINE FUNCTIONS

# ------------------ CALC CC OF EXISTING VG RESOURCES -------------------------
def cc_vg(cf, load, cap_vg, top_hours_n, cap_marg):
    
    '''
    Calculate the capacity value of existing and marginal variable generation capacity using a top hour approximation
    More details on the methodology used in this approximation can be found here: <file location>
    Args:
        cf: numpy matrix containing capacity factor profile for all hours_n for each variable generating resource
        load: numpy array containing time-synchronous load profile for all hours_n. Units: MW
        cap_MW: nompy array containing capacity of each variable generating resource. Units: MW
        top_hours_n: number of top hours to consider for the calculation
    Returns:
        cc_marg: marginal capacity value for each variable generating resource
        load_net: net load profile. Units: MW
        top_hours_net: arguments for the highest net load hours in load_net, length top_hours_n
        top_hours: argumnets for the highest load hours in load, length top_hours_n
    To Do:
        Currently only built for hourly profiles. Generalize to any duration timestep.
    '''
                              
    # number of hours in the load and CF profiles
    hours_n = len(load)
    

    # get the time-synchronous VG profiles
    vg_power = cf * cap_vg
    
    # get the net load that must be met with conventional generation
    load_net = load - np.sum(vg_power, axis = 1)
    
    # get the indices of the top hours of net load
    top_hours_net = load_net.argsort()[np.arange(hours_n-1, (hours_n-top_hours_n)-1, -1)]
    
    # get the indices of the top hours of load
    top_hours = load.argsort()[np.arange(hours_n-1, (hours_n-top_hours_n)-1, -1)]
    
    # get the differences and reductions in load as well as the ratio between the two
    load_dif = load[top_hours] - load_net[top_hours]
    load_reduct = load[top_hours] - load_net[top_hours_net]
    load_ratio = np.tile(np.divide(load_reduct, load_dif, out = np.zeros_like(load_reduct),
                                      where = load_dif != 0).reshape(top_hours_n,1), (1,len(cf[0,:])))
    # get the existing cc for each resource
    gen_tech = vg_power[top_hours_net,:] + np.where(load_ratio < 1, vg_power[top_hours,:]*load_ratio, vg_power[top_hours,:])
    gen_sum = np.tile(np.sum(gen_tech, axis = 1).reshape(top_hours_n,1), (1,len(cf[0,:])))
    gen_frac = np.divide(gen_tech, gen_sum, out = np.zeros_like(gen_tech), where = gen_sum != 0)
    cap_useful_MW = (np.sum(gen_frac * np.tile(load_reduct.reshape(top_hours_n,1),(1,len(cf[0,:]))), axis = 0)/
                     top_hours_n).reshape(len(cf[0,:]),1)
    
    # get the time-synchonous marginal VG matrix
    vg_marg_power = cf * cap_marg
    
    # get the marg net load for each VG resource
    load_marg = np.tile(load_net.reshape(hours_n,1),(1,len(cf[0,:]))) - vg_marg_power 
    
    # sort each marginal load profile
    for n in np.arange(0,len(cf[0,:]),1):
        load_marg[:,n] = np.flip(load_marg[np.argsort(load_marg[:,n], axis=0),n], axis=0)
        
    # get the reductions in load for each resource
    load_reduct_marg = np.tile(load_net[top_hours_net].reshape(top_hours_n,1), (1,len(cf[0,:]))) - load_marg[0:top_hours_n,:]
    
    # get the marginal CCs for each resource
    cc_marg = (np.sum(load_reduct_marg, axis = 0)/top_hours_n)/cap_marg
    
    # setting the lower bound for marginal CC to be 0.01
    cc_marg[cc_marg < 0.01] = 0.0
    
    # rounding outputs to the nearest 5 decimal points
    load_net = np.around(load_net, decimals=5)
    cc_marg = np.around(cc_marg, decimals=5)
    cap_useful_MW = np.around(cap_useful_MW, decimals=5)
    top_hours_net = np.around(top_hours_net, decimals=5)
    
    results = {
                'load_net':load_net,
                'cc_marg':cc_marg,
                'cap_useful_MW':cap_useful_MW,
                'top_hours_net':top_hours_net,
                }
    
    return results


# -------------------------CALC REQUIRED MWHS----------------------------------
def calc_required_mwh(load_profile, peak_reductions, eff_charge, eff_discharge):
    '''
    Determine the energy storage capacity required to acheive a certain peak load reduction for a given load profile
    Args:
        load_profile: time-synchronous load profile
        peak_reductions: set of peak reductions (in MW) to be tested
    Returns:
        required_MWhs: set of energy storage capacities required for each peak reduction size
    '''
    
    hours_n = len(load_profile)
    
    inc = len(peak_reductions)
    max_demands = np.tile((np.max(load_profile)-peak_reductions).reshape(inc,1), (1, hours_n))
    batt_powers = np.tile(peak_reductions.reshape(inc,1), (1, hours_n))

    poss_charges = np.minimum(batt_powers*eff_charge, (max_demands-load_profile)*eff_charge)
    necessary_discharges = (max_demands-load_profile)/eff_discharge
    
    
    poss_batt_changes = np.where(necessary_discharges<=0, necessary_discharges, poss_charges)
    
    batt_e_level = np.zeros([inc, hours_n])
    batt_e_level[:, 0] = np.minimum(poss_batt_changes[:, 0], 0)
    for n in np.arange(1, hours_n):
        batt_e_level[:, n] = batt_e_level[:, n-1] + poss_batt_changes[:, n]
        batt_e_level[:, n] = np.clip(batt_e_level[:, n], a_min=None, a_max=0.0, out=batt_e_level[:, n]) #
    
    required_MWhs = - np.min(batt_e_level, axis=1)
    
    return required_MWhs, batt_powers


# -------------- CALC CC OF MARGINAL AND EXISTING STORAGE ---------------------
def cc_storage(required_MWhs, batt_powers, stor_MWh, stor_MW, marg_durations, marg_stor_step_MW):
    '''Determine the existing and marginal capacity value of storage
       Can use several discrete values for srotage duration or a single value
       More details on the methodology used can be found here: <file location>
       Args:
           required_MWhs: energy storage capacities needed to satisfy associated demand reductions
           batt_powers: demand reductions explored
           stor_MWh: energy storage capacity of the existing fleet
           stor_MW: power storage capacity of the existing fleet
           marg_durations: duration(s) of marginal storage for marginal cc calculation
       Returns:
           cc_stor: capacity value of the existing storage fleet
           cc_sto_marg: capacity value(s) of marginal storage, depending on duration of marginal addition
    '''
 
    stor_inc = len(required_MWhs) - 1
    
    # marginal and existing cc calculations for case where peak reduction equals installed power capacity
    if (required_MWhs[stor_inc-1] <= stor_MWh):
        # get the marginal CC of storage, depending on the shape of the marginal use curve and the duration of the marginal addition
        slope = (batt_powers[stor_inc,0] - batt_powers[stor_inc-1,0]) / (required_MWhs[stor_inc] - required_MWhs[stor_inc-1])
        # since the conditional statement changes here for each duration d, this is more efficient than using np.clip
        cc_stor_marg = np.array([np.where(required_MWhs[stor_inc] <= (stor_MWh + marg_stor_step_MW * d), 1.0, slope * d) for d in marg_durations])
        # get CC of existing storage
        cc_stor = 1.0
        
    # marginal and existing cc calculations for case where peak reduction is less than installed power capacity
    else:
        # get effective capacity of installed storage
        cap_eff = np.interp(stor_MWh, required_MWhs, batt_powers[:,0])
        # get CC of existing storage
        cc_stor = cap_eff/stor_MW
        # get the maximum possible marginal CC value
        cc_stor_marg_max = (marg_stor_step_MW + stor_MW*(1-cc_stor) ) / marg_stor_step_MW
        # find nearest data point to actual system
        closest = np.argmin(abs(required_MWhs - stor_MWh))
        # get the marginal CC of storage, depending where the fleet lies on the optimal use curve and the duration of the marginal addition
        slope = abs( (batt_powers[closest,0] - cap_eff) / (required_MWhs[closest] - stor_MWh) )
        cc_stor_marg = np.array([slope * d for d in marg_durations])
        # note we do not clip marginal CC at 1, we clip it at the value that brings the system CC up to 1
        cc_stor_marg = np.clip(cc_stor_marg, a_min = None, a_max = cc_stor_marg_max, out = cc_stor_marg)
        
        # rounding outputs to the nearest 5 decimal points
        cc_stor = np.around(cc_stor, decimals=5)
        cc_stor_marg = np.around(cc_stor_marg, decimals=5)
        
        
    return cc_stor, cc_stor_marg


#%%  DRIVING FUNCTION

# -------------------------- READ IN GDX FILES --------------------------------
def do_a_year(input_gdx_file, output_gdx_file, scenario, year, next_year, annual_hours, season_hours, marg_stor_step_MW, marg_VG_step_MW):
#%% DEFINING FILEPATHS

#    input_gdx_file_name = 'CC_py_inputs_' + scenario + '_' + next_year + '.gdx'
#    output_gdx_file_name = 'cc_out_' + scenario + '_' + next_year + '.gdx'
#    input_gdx_file = os.path.join('runs',scenario,'outputs','variabilityFiles',input_gdx_file_name)
#    output_gdx_file = os.path.join('runs',scenario,'outputs','variabilityFiles',output_gdx_file_name)
#    year = '2047'
#    next_year = '2047'
#    annual_hours = 20
#    season_hours = 10
#    marg_stor_step_MW = 100
#    marg_VG_step_MW = 1000
    
    #%%
    path_pickles = os.path.join('E_Outputs','runs',scenario,'outputs','variabilityFiles','pickles')
    path_variability = os.path.join('A_Inputs','inputs','variability')
    path_static = os.path.join('D_8760','LDCfiles')
    if not os.path.exists(path_pickles): os.mkdir(path_pickles)

    # -------Get the gdx file from ReEDS -------
    
    gdxin = gdxpds.to_dataframes(input_gdx_file)
    
    # storage durations
    durations = gdxin['storage_duration']
    durations.columns = ['tech','duration'] 

    # ------- Get all spatial mappers for the current run -------
    
    # BAs present in the current run
    BAs_true = gdxin['rfeas']
    BAs_true.columns = ['area','boolean']
    BAs_true = BAs_true.drop('boolean',1).sort_values('area').reset_index(drop=True)
    
    map_BAtoRTO = gdxin['r_region']
    map_BAtoRTO.columns = ['area','region','boolean']
    map_BAtoRTO = map_BAtoRTO[map_BAtoRTO['area'].isin(BAs_true['area'])].drop('boolean',1).sort_values('area').reset_index(drop=True)
     
    # ------- Get all technology subsets -------
    
    tech_list = ['dupv','upv','wind','storage','vre']
    techs = {tech:pd.DataFrame() for tech in tech_list}
    for tech in tech_list:
        techs[tech] = gdxin[tech]
        techs[tech] = techs[tech]['i']


    # ------- Load run-specific data from pickle files -------
        
    load_profiles = pd.read_pickle(os.path.join(path_pickles,'load_{}.pkl'.format(scenario)))
    recf = pd.read_pickle(os.path.join(path_pickles,'recf_{}.pkl'.format(scenario)))
    resources= pd.read_pickle(os.path.join(path_pickles,'resources_{}.pkl'.format(scenario)))
        
#%%  GET REEDS SOLVE VARIABLES AND PERFORM YEAR OVER YEAR ADJUSTMENTS
    
    # ------- Get the temporal mappers for the current run -------
    
    map_TIMESLICEtoHOURtoSEASON = pd.read_pickle(os.path.join(path_static,'India_hour_season_ts_map.pkl'))
      
#     Create a mapping for indices to hours for all seasons
    map_SEASONHOURStoINDICES = pd.concat([map_TIMESLICEtoHOURtoSEASON.loc[map_TIMESLICEtoHOURtoSEASON['season']=='Winter',:].reset_index(drop=True),
                                          map_TIMESLICEtoHOURtoSEASON.loc[map_TIMESLICEtoHOURtoSEASON['season']=='Spring',:].reset_index(drop=True),
                                          map_TIMESLICEtoHOURtoSEASON.loc[map_TIMESLICEtoHOURtoSEASON['season']=='Summer',:].reset_index(drop=True),
                                          map_TIMESLICEtoHOURtoSEASON.loc[map_TIMESLICEtoHOURtoSEASON['season']=='Rainy',:].reset_index(drop=True),
                                          map_TIMESLICEtoHOURtoSEASON.loc[map_TIMESLICEtoHOURtoSEASON['season']=='Autumn',:].reset_index(drop=True)],sort=False).reset_index().rename(columns={"index":"hours_ts"})
    
    
    # ------- Get all capacities -------
    
    cap = gdxin['cap_export']
    cap.columns = ['tech','area','year','MW']
    cap.loc[:,'tech'] = cap.loc[:,'tech']#.str.lower()
    cap.loc[:,'resource'] = cap.loc[:,'tech'] + '_' + cap.loc[:,'area']
    
    
    # ------- Add in resources that are not in the static inputs CF profiles or supply curves csv files ------

    # Get resources that are missing capacity factor profile
    resources_dupv = resources[resources['tech'].isin(techs['dupv'])]
    resources_upv = resources[resources['tech'].isin(techs['upv'])]
    index_missing_resource = ~cap['resource'].isin(resources['resource'])
    missing_resources = cap[index_missing_resource].drop('resource',1)
    missing_dupv = missing_resources[missing_resources['tech']=='dupv_her']
    missing_upv = missing_resources[missing_resources['tech']=='upv_her']
    missing_dupv = pd.merge(left=missing_dupv, right=resources_dupv, on='area', how='left')
    missing_upv = pd.merge(left=missing_upv, right=resources_upv, on='area', how='left')
    missing_dupv = missing_dupv.drop_duplicates(subset='MW', keep='first')
    missing_upv = missing_dupv.drop_duplicates(subset='MW', keep='first')
    missing_dupv = missing_dupv.drop(['tech_x','region'],1).rename(columns={'tech_y':'tech'})
    missing_upv = missing_upv.drop(['tech_x','region'],1).rename(columns={'tech_y':'tech'})
    cap = pd.concat([cap,pd.concat([missing_dupv,missing_upv],sort=False)],sort=False)
    drop_resources = ['dupv_her','upv_her','wind_her','wind_ofs']
    cap = cap[~cap['tech'].isin(drop_resources)]
    cap = cap.groupby(by=['tech','area','year','resource'],as_index=False).sum()
    
    del missing_upv, missing_dupv, resources_upv, resources_dupv, index_missing_resource, missing_resources, drop_resources
    
    # ------- Getting all VRE capacities -------
    
    cap_vre = cap[cap['tech'].isin(techs['vre'])]
    
    # ------- Getting all storage capacities -------
    
    # Getting energy capacities for storage
    cap_stor = cap[cap['tech'].isin(techs['storage'])]
    cap_stor = pd.merge(left=cap_stor, right=map_BAtoRTO, on='area', how='left')
    cap_stor = pd.merge(left=cap_stor, right=durations, on='tech', how='left')
    cap_stor.loc[:,'MWh'] = cap_stor.loc[:,'MW'] * cap_stor.loc[:,'duration']
    
    # Getting round-trip efficiencies
    stor_RTE = gdxin['storage_eff']
    stor_RTE.columns = ['tech','RTE']    
    stor_RTE = pd.merge(left=stor_RTE, right=cap_stor[['tech','MWh','region']], on='tech', how='right')
    stor_RTE.loc[:,'RTE'] = stor_RTE.loc[:,'RTE'] * stor_RTE.loc[:,'MWh']
    stor_RTE = stor_RTE.groupby(by='region').mean()
    stor_RTE.loc[:,'RTE'] = stor_RTE.loc[:,'RTE'] / stor_RTE.loc[:,'MWh']
    
    # Aggregrating storage capacities by RTO
    cap_stor_region = cap_stor.drop('duration',1).groupby(by='region').sum()
    cap_stor = cap_stor[['tech','area','MW']]
    
    
    # Select this year's load profile
    load_profiles = load_profiles.loc[load_profiles['Year'] == int(year)]
    
    # ------- Superpeak hours for weighted average calculation -------
    
    hours_superpeak = pd.read_csv(os.path.join(path_variability,'superpeak_hours.csv'))
    
    # ------- Adjust load profiles by this year's transmission by BA -------
    
    annual_all_cc = pd.DataFrame(columns=['tech','area','year','MW'])
    annual_all_cc_mar = pd.DataFrame(columns=['tech','area','year','CC'])
    annual_timeslice_hours_all = pd.DataFrame(columns=['timeslice','region','%TopHrs'])
    
    season_all_cc = pd.DataFrame(columns=['tech','area','season','year','MW'])
    season_all_cc_mar = pd.DataFrame(columns=['tech','area','season','year','CC'])
    season_timeslice_hours_all = pd.DataFrame(columns=['timeslice','region','season','%TopHrs'])
    
    
#%%  FOR LOOP FOR REGIONS

    # March through this for all Regions
    for region in map_BAtoRTO['region'].drop_duplicates():
        
#%%  Region DATA
        # ------- Get load profile, RECF profiles, VG capacity, storage capacity, and storage RTE for this Region -------
        
        # Select the load profiles of the BAs in this RTO and merge in columns for season, hour, and timeslice
        this_region_load_profile = load_profiles[map_BAtoRTO[map_BAtoRTO['region']==region]['area']]
        this_region_load_profile = this_region_load_profile.sum(axis=1).reset_index()
        this_region_load_profile.columns = ['hour','Load'] ; this_region_load_profile['hour'] = [i for i in range(1,8761)]
        this_region_load_profile = pd.merge(left=map_TIMESLICEtoHOURtoSEASON,right=this_region_load_profile,on='hour')
        
        # Select the VG CF profiles of the resources in this RTO and merge in columns for season, hour, and timeslice
        this_region_recf = recf[resources[resources['region']==region]['resource']]
        this_region_recf = this_region_recf.reset_index().rename(columns={"index":'hour'})
        this_region_recf.loc[:,'hour'] = pd.to_numeric(this_region_recf.loc[:,'hour']) + 1
        this_region_recf = pd.merge(left=map_TIMESLICEtoHOURtoSEASON, right=this_region_recf, on='hour')
        
        # Select the resources that are in this RTO
        this_region_resources = resources[resources['resource'].isin(list(this_region_recf))]
        
        # Get the VG capacity for this region in this year in the same order as the columns in the recf DataFrame
        this_region_VG_MW = pd.DataFrame({'resource':list(this_region_recf.drop(['timeslice','hour','season'],1))})
        this_region_VG_MW = pd.merge(left=this_region_VG_MW, right=cap_vre, on='resource', how='left').drop(['area','tech'],1).fillna(0)
        
        # Distribute RTE evenly between charging and discharging
        try:
            eff_charge = np.sqrt(stor_RTE.loc[region,'RTE'])
            eff_discharge = np.sqrt(stor_RTE.loc[region,'RTE'])
        except:
            print("\n")
            print("Message from CC_py: No round-trip storage efficiency was found for " + region + ". A default of 0.9 will be used")
            eff_charge = 0.9
            eff_discharge = 0.9
        
        # Get the fleet-wide power and energy capacity of storage for this Region
        try:
            storage_fleet_MW = cap_stor_region.loc[region,'MW']
            storage_fleet_MWh = cap_stor_region.loc[region,'MWh']
        except:
            print("\n")
            print("Message from CC_py: " + region + " has no storage capacity so it is being assigned a capacity of 0")
            storage_fleet_MW = 0
            storage_fleet_MWh = 0
            
        # Make a numpy array of power capacities for the calc_required_MWh function
        reductions_considered = 20
        peak_reductions = np.linspace(0, storage_fleet_MW, reductions_considered)
        peak_reductions = np.append(peak_reductions, storage_fleet_MW + marg_stor_step_MW)
        
        
#%%  CALL FUNCTIONS ANNUALLY
        
        # ---------------------------- CALL FUNCTIONS ---------------------------------
        
        # this_region_load_profile.to_csv('load.csv')
        this_region_recf.to_csv(os.path.join('D_8760','LDCfiles','recf.csv'))
        # Call c_vg
        cc_vg_results = cc_vg(this_region_recf.drop(['hour','timeslice','season'],1).values, this_region_load_profile['Load'].values,
                              this_region_VG_MW['MW'].values, annual_hours, marg_VG_step_MW)
        
        # Call storage cc functions
        annual_required_MWhs, annual_batt_powers = calc_required_mwh(cc_vg_results['load_net'], peak_reductions, eff_charge, eff_discharge)
        annual_cc_stor, annual_cc_stor_marg = cc_storage(annual_required_MWhs, annual_batt_powers, storage_fleet_MWh, storage_fleet_MW, durations['duration'].values, marg_stor_step_MW)
        
#%%  STORING ANNUAL DATA
        
        # ------- Store all data that will be sent back to ReEDS
        
        # Get the fractions of top hours in each timeslice
        # Note here we are matching hours (1-8760) with the index of the top hours (0-8759) so we add 1 to the index
        index_top_hours = (map_TIMESLICEtoHOURtoSEASON['hour'].isin(cc_vg_results['top_hours_net']+1))
        temp = map_TIMESLICEtoHOURtoSEASON.loc[index_top_hours,'timeslice'].value_counts()/annual_hours
        temp = temp.reset_index().rename(columns={"index":"timeslice","timeslice":"%TopHrs"})
        temp.loc[:,'region'] = region
        annual_timeslice_hours_all = pd.concat([annual_timeslice_hours_all,temp],sort=False).reset_index(drop=True)
        
        # Get the CC of storage
        temp_region = [region] * len(techs['storage'])
        temp_cc_stor = [annual_cc_stor] * len(techs['storage'])
        this_region_stor_cc = pd.DataFrame({'region': temp_region, 'tech': techs['storage'], 'CC': temp_cc_stor})
        this_region_stor_cc = pd.merge(left=map_BAtoRTO, right=this_region_stor_cc, on='region', how='inner').drop('region',1)
        this_region_stor_cc.loc[:,'year'] = next_year
        this_region_stor_cc = pd.merge(left = this_region_stor_cc, right = cap_stor, on=['tech','area'], how='left').fillna(0)
        this_region_stor_cc.loc[:,'MW'] = this_region_stor_cc.loc[:,'CC'] * this_region_stor_cc.loc[:,'MW']
        this_region_stor_cc = this_region_stor_cc.drop('CC',1)
        annual_all_cc = pd.concat([annual_all_cc, this_region_stor_cc],sort=False).reset_index(drop=True)
        
        # Get the marginal CC for each storage tech
        this_region_stor_cc_mar = pd.DataFrame({'region': temp_region, 'tech': techs['storage'], 'CC': annual_cc_stor_marg})
        this_region_stor_cc_mar = pd.merge(left=this_region_stor_cc_mar, right=map_BAtoRTO, on='region', how='inner').drop('region',1)
        this_region_stor_cc_mar.loc[:,'year'] = next_year
        annual_all_cc_mar = pd.concat([annual_all_cc_mar, this_region_stor_cc_mar],sort=False).fillna(1).reset_index(drop=True)
        
        # Get the CC of wind and PV
        this_region_vg_cc = this_region_resources[['tech','area']].copy()
        this_region_vg_cc.loc[:,'year'] = next_year
        this_region_vg_cc['MW'] = cc_vg_results['cap_useful_MW']
        annual_all_cc = pd.concat([annual_all_cc, this_region_vg_cc],sort=False).reset_index(drop=True)
        
        # Get the marginal CC of wind and PV
        this_region_vg_cc_mar = this_region_vg_cc.drop('MW',1)
        this_region_vg_cc_mar['CC'] = cc_vg_results['cc_marg']
        annual_all_cc_mar = pd.concat([annual_all_cc_mar, this_region_vg_cc_mar],sort=False).reset_index(drop=True)
        

#%%  RESORTING LOAD AND CF PROFILES FOR SEASONAL CALCULATIONS
        
        # Resort the load and CF profiles so that winter storage calculations are done in proper time-series
        this_region_load_profile_resorted = pd.merge(left=map_SEASONHOURStoINDICES, right=this_region_load_profile, on=['timeslice','hour','season'])
        this_region_recf_resorted = pd.merge(left=map_SEASONHOURStoINDICES, right=this_region_recf, on=['timeslice','hour','season'])
        
#%%  FOR LOOP FOR SEASONS
        
        for season in map_TIMESLICEtoHOURtoSEASON['season'].drop_duplicates():
            
#%%  SEASONAL DATA MANIPULATIONS
            
            # Get the load and CF profiles for this season
            this_season_load_profile = this_region_load_profile_resorted[this_region_load_profile_resorted['season']==season]
            this_season_recf = this_region_recf_resorted[this_region_recf_resorted['season']==season]
            
#%%  CALL FUNTIONS SEASONALLY
            
            # ---------------------------- CALL FUNCTIONS ---------------------------------
            
            # Call cc_vg
            season_cc_vg_results = cc_vg(this_season_recf.drop(['hours_ts','hour','timeslice','season'],1).values, this_season_load_profile['Load'].values,
                                         this_region_VG_MW['MW'].values, season_hours, marg_VG_step_MW)
            
            # Call storage CC functions
            season_required_MWhs, season_batt_powers = calc_required_mwh(season_cc_vg_results['load_net'], peak_reductions, eff_charge, eff_discharge)
            season_cc_stor, season_cc_stor_marg = cc_storage(season_required_MWhs, season_batt_powers, storage_fleet_MWh, storage_fleet_MW, durations['duration'].values, marg_stor_step_MW)
            
#%%  STORING SEASONAL DATA
            
            # ------- Store all data that will be sent back to ReEDS -------
            
            # Get the fractions of top hours in each timeslice
            index_top_hours = (map_SEASONHOURStoINDICES['season']==season) & (map_SEASONHOURStoINDICES['hours_ts'].isin(season_cc_vg_results['top_hours_net']))
            temp = map_SEASONHOURStoINDICES.loc[index_top_hours,'timeslice'].value_counts()/season_hours
            temp = temp.reset_index().rename(columns={"index":"timeslice","timeslice":"%TopHrs"})
            temp.loc[:,'region'] = region
            temp.loc[:,'season'] = season
            season_timeslice_hours_all = pd.concat([season_timeslice_hours_all,temp],sort=False).reset_index(drop=True)
            
            # Get the CC of storage
            temp_season = [season] * len(techs['storage'])
            temp_region = [region] * len(techs['storage'])
            temp_cc_stor = [season_cc_stor] * len(techs['storage'])
            this_season_stor_cc = pd.DataFrame({'region': temp_region, 'tech': techs['storage'], 'season': temp_season, 'CC': temp_cc_stor})
            this_season_stor_cc = pd.merge(left=map_BAtoRTO, right=this_season_stor_cc, on='region', how='inner').drop('region',1)
            this_season_stor_cc.loc[:,'year'] = next_year
            this_season_stor_cc = pd.merge(left=this_season_stor_cc, right=cap_stor, on=['tech','area'], how='left').fillna(0)
            this_season_stor_cc.loc[:,'MW'] = this_season_stor_cc.loc[:,'MW'] * this_season_stor_cc.loc[:,'CC']
            this_season_stor_cc = this_season_stor_cc.drop('CC',1)
            season_all_cc = pd.concat([season_all_cc, this_season_stor_cc],sort=False).fillna(1).reset_index(drop=True)
            
            # Get the marginal CC for each storage tech
            this_season_stor_cc_mar = pd.DataFrame({'region': temp_region, 'tech': techs['storage'], 'season': temp_season, 'CC': season_cc_stor_marg})
            this_season_stor_cc_mar = pd.merge(left=this_season_stor_cc_mar, right=map_BAtoRTO, on='region', how='inner').drop('region',1)
            this_season_stor_cc_mar.loc[:,'year'] = next_year
            season_all_cc_mar = pd.concat([season_all_cc_mar, this_season_stor_cc_mar],sort=False).fillna(1).reset_index(drop=True)
        
            # Get the CC of wind and PV
            this_season_vg_cc = this_region_resources[['tech','area']].copy()
            this_season_vg_cc.loc[:,'year'] = next_year
            this_season_vg_cc.loc[:,'season'] = season
            this_season_vg_cc['MW'] = season_cc_vg_results['cap_useful_MW']
            season_all_cc = pd.concat([season_all_cc, this_season_vg_cc],sort=False).reset_index(drop=True)
            
            # Get the marginal CC of wind and PV
            this_season_vg_cc_mar = this_season_vg_cc.drop('MW',1)
            this_season_vg_cc_mar['CC'] = season_cc_vg_results['cc_marg']
            season_all_cc_mar = pd.concat([season_all_cc_mar,this_season_vg_cc_mar],sort=False).reset_index(drop=True)
                
#%%  WRITE DATA TO GDX FILE
    
    # -------------- RENAMING SEASONS TO MATCH REEDS CONVENTION ---------------
    season_all_cc = season_all_cc.replace(to_replace='winter', value='wint')
    season_all_cc = season_all_cc.replace(to_replace='spring', value='spri')
    season_all_cc = season_all_cc.replace(to_replace='summer', value='summ')
    season_all_cc_mar = season_all_cc_mar.replace(to_replace='winter', value='wint')
    season_all_cc_mar = season_all_cc_mar.replace(to_replace='spring', value='spri')
    season_all_cc_mar = season_all_cc_mar.replace(to_replace='summer', value='summ')
    season_timeslice_hours_all = season_timeslice_hours_all.replace(to_replace='winter', value='wint')
    season_timeslice_hours_all = season_timeslice_hours_all.replace(to_replace='spring', value='spri')
    season_timeslice_hours_all = season_timeslice_hours_all.replace(to_replace='summer', value='summ')
    
    # --------------- RENAME COLUMNS TO MATCH REEDS CONVENTION ----------------
    
    annual_all_cc.columns = ['i','r','t','value']
    annual_all_cc_mar.columns = ['i','r','t','value']
    annual_timeslice_hours_all.columns = ['h','region','value']
    
    season_all_cc_mar.columns = ['i','r','szn','t','value']
    season_all_cc.columns = ['i','r','szn','t','value']
    season_timeslice_hours_all.columns = ['h','region','szn','value']
    
    # ---------------- WRITE OUT A GDX FILE WITH THE OUTPUTS FOR REEDS ----------------
    
    outputs = {
                'annual_all_cc':                annual_all_cc,
                'annual_all_cc_mar':            annual_all_cc_mar,
                'annual_timeslice_hours_all':   annual_timeslice_hours_all,
                
                'season_all_cc_mar':            season_all_cc_mar,
                'season_all_cc':                season_all_cc,
                'season_timeslice_hours_all':   season_timeslice_hours_all
                }
    
    gdxpds.to_gdx(outputs, output_gdx_file)
    
    
#%%  MAIN

if __name__ == '__main__':
    
    # ------------------------------ PARSE ARGUMENTS ------------------------------
    
    parser = argparse.ArgumentParser(description="""Perform 8760 calculations on variable and energy constrained resources""")
    
    # Mandatory arguments
    parser.add_argument("inputs", help="""Filename of the input gdx file with necessary data for 8760 calaculations""", type=str)
    parser.add_argument("output", help="""Filename of the output gdx file with results from 8760 calculations""", type=str)
    parser.add_argument("scenario", help="""Scenario name""", type=str)
    parser.add_argument("year", help="""Previous ReEDS solve year""", type=str)
    parser.add_argument("next_year", help="Upcoming ReEDS solve year""", type=str)
    
    # Optional arguments
    parser.add_argument("-a","--annual", help="""Number of top hours to use for annual VG calculations""", default = 20)
    parser.add_argument("-s","--seasonal", help="""Number of top hours to use for seasonal VG calculations""", default = 10)
    parser.add_argument("-m","--marg_stor_step_mw", help="""Number of MW used to project margainal storage results""", default = 100)
    parser.add_argument("-v","--marg_vg_step_mw", help="""Number of MW used to project marginal VG results""", default = 1000)
    
    args = parser.parse_args()
   
    
    #%%
    # Preparing to log any errors if they occur
    path_errors = os.path.join('E_Outputs','runs',args.scenario,'outputs','variabilityFiles','ErrorFile')
    if not os.path.exists(path_errors): os.mkdir(path_errors)
    errorfile = os.path.join(path_errors,'CC_py_errors_{}_{}.txt'.format(args.scenario,args.next_year))
    logging.basicConfig(filename=errorfile,level=logging.ERROR)
    logger = logging.getLogger(__name__)
    
    # If an error occurs during the script write it to a txt file
    try:
        do_a_year(args.inputs, args.output, args.scenario, args.year, args.next_year, args.annual, args.seasonal, args.marg_stor_step_mw, args.marg_vg_step_mw)
    except:
        logger.error(traceback.format_exc())
    # Removing the error file if it is empty
    logging.shutdown()
    if os.stat(errorfile).st_size == 0:
        os.remove(errorfile)