
import gdxpds 
import numpy as np
import pandas as pd
import os
import logging
import traceback
import argparse

#   DEFINE FUNCTIONS

# ------------------ CALC CC OF EXISTING VG RESOURCES -------------------------
def cc_vg(cf, load, cap_vg, top_hours_n, cap_marg):
    '''
    Calculate the capacity credit of existing and marginal variable generation capacity using a top hour approximation
    More details on the methodology used in this approximation can be found here: <file location>
    Args:
        cf: numpy matrix containing capacity factor profile for all hours_n for each variable generating resource
        load: numpy array containing time-synchronous load profile for all hours_n. Units: MW
        cap_MW: nompy array containing capacity of each variable generating resource. Units: MW
        top_hours_n: number of top hours to consider for the calculation
    Returns:
        cc_marg: marginal capacity credit for each variable generating resource
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


# -----------------------CALC REQUIRED MWHS CSP--------------------------------
def calc_required_mwh_csp(load_profile, cspcaps, solar_multiples, cspcfs, inc, combine_profiles=False):
    '''
    Determine the energy storage capacity required to acheive a certain peak load reduction for a given load profile
    Args:
        load_profile: time-synchronous load profile
        cspcaps: array of csp capacities by tech, type, and region
        solar_multiples: solar multiples of charging capacity to generator size
        cspcfs: matrix of csp profiles by tech and region
        inc: number of peak reductions considered
        combine_profiles: this set set to true for calculating existing CC of CSP so that all existing is treated at once
    Returns:
        required_MWhs: set of energy storage capacities required for each peak reduction size
        csp_powers: set of peak reduction sizes corresponding to required_MWhs
    '''
    
    csps = len(cspcaps)
    hours_n = len(load_profile)
    
    # Adjust the cf profiles by the solar multiple
    cspcfs *= solar_multiples
    cspcfs = cspcfs.transpose()
    
    csp_charge = cspcfs * cspcaps.reshape(csps,1)
        
    # Combine charging profiles only for CC of existing CSP
    if combine_profiles:
        csp_charge = csp_charge.sum(axis=0).reshape(1,hours_n)

        poss_charges = np.zeros((inc,hours_n))
        for i in range(0,hours_n):
            poss_charges[:,i] = np.linspace(0,csp_charge[0,i], inc)
        
        peak_reductions = np.linspace(0,cspcaps.sum(axis=0),inc)
        
    else:
        poss_charges = csp_charge.copy()
        peak_reductions = cspcaps.copy()
    
    csp_powers = peak_reductions.reshape(inc,1)
    
    max_demands = np.tile((np.max(load_profile)-peak_reductions).reshape(inc,1), (1, hours_n))
    
    necessary_discharges = (max_demands-load_profile)
    
    # Note CSP can charge while discharging
    necessary_discharges = np.clip(necessary_discharges, a_min=None, a_max=0.0, out=necessary_discharges)
    poss_batt_changes = poss_charges + necessary_discharges
    
    batt_e_level = np.zeros([inc, hours_n])
    batt_e_level[:, 0] = np.minimum(poss_batt_changes[:, 0], 0)
    for n in np.arange(1, hours_n):
        batt_e_level[:, n] = batt_e_level[:, n-1] + poss_batt_changes[:, n]
        batt_e_level[:, n] = np.clip(batt_e_level[:, n], a_min=None, a_max=0.0, out=batt_e_level[:, n]) #
    
    required_MWhs = - np.min(batt_e_level, axis=1)
    
    return required_MWhs, csp_powers

   
# -------------------------CALC REQUIRED MWHS----------------------------------
def calc_required_mwh(load_profile, peak_reductions, eff_charge):
    '''
    Determine the energy storage capacity required to acheive a certain peak load reduction for a given load profile
    Args:
        load_profile: time-synchronous load profile
        peak_reductions: set of peak reductions (in MW) to be tested
        eff_charge: RTE of charging
    Returns:
        required_MWhs: set of energy storage capacities required for each peak reduction size
        batt_powers: corresponding peak reduction sizes for required_MWhs
    '''
    
    hours_n = len(load_profile)
    
    inc = len(peak_reductions)
    max_demands = np.tile((np.max(load_profile)-peak_reductions).reshape(inc,1), (1, hours_n))
    batt_powers = np.tile(peak_reductions.reshape(inc,1), (1, hours_n))
    
    poss_charges = np.minimum(batt_powers*eff_charge, (max_demands-load_profile)*eff_charge)
    necessary_discharges = (max_demands-load_profile)
    
    poss_batt_changes = np.where(necessary_discharges<=0, necessary_discharges, poss_charges)
    
    batt_e_level = np.zeros([inc, hours_n])
    batt_e_level[:, 0] = np.minimum(poss_batt_changes[:, 0], 0)
    for n in np.arange(1, hours_n):
        batt_e_level[:, n] = batt_e_level[:, n-1] + poss_batt_changes[:, n]
        batt_e_level[:, n] = np.clip(batt_e_level[:, n], a_min=None, a_max=0.0, out=batt_e_level[:, n]) #
    
    required_MWhs = - np.min(batt_e_level, axis=1)
    
    return required_MWhs, batt_powers
    
# -------------------------CALC REQUIRED MWHS----------------------------------
def fill_in_charging(load_profile, peak_reductions, eff_charge, storage_fleet_MWh, storage_fleet_MW):
    '''
    Fill in the load profile with the storage charging load
    Args:
        load_profile: time-synchronous load profile
        peak_reductions: peak reduction acheived as determined from the existing storage cc calculations
        eff_charge: charging efficiency of storage
        storage_fleet_MWh: energy capacity of the conventional storage fleet
    Returns:
        load_profile: load profile adjusted for conventional storage charging
    '''
    
    hours_n = len(load_profile)
    
    inc = len(peak_reductions)
    max_demands = np.tile((np.max(load_profile)-peak_reductions).reshape(inc,1), (1, hours_n))
    batt_powers = np.tile(storage_fleet_MW.reshape(inc,1), (1, hours_n))
    
    poss_charges = np.minimum(batt_powers*eff_charge, (max_demands-load_profile)*eff_charge)
    necessary_discharges = (max_demands-load_profile)
    
    poss_batt_changes = np.where(necessary_discharges<=0, necessary_discharges, poss_charges)
    
    batt_e_level = np.zeros([inc, hours_n])
    batt_e_level[:, 0] = np.minimum(poss_batt_changes[:, 0], 0)
    for n in np.arange(1, hours_n):
        batt_e_level[:, n] = batt_e_level[:, n-1] + poss_batt_changes[:, n]
        batt_e_level[:, n] = np.clip(batt_e_level[:, n], a_min=None, a_max=0.0, out=batt_e_level[:, n])
    
    # Get the time blocks for storage charging
    discharging_hours = np.argwhere(poss_batt_changes<=0)[:,1]
    charging_hours = np.argwhere(poss_batt_changes>0)[:,1]
    df = pd.DataFrame(columns=['hour','discharge','potential','load','block'])
    df['hour'] = np.arange(0,hours_n)
    df.loc[discharging_hours,'discharge'] = poss_batt_changes[0,discharging_hours]
    df.loc[charging_hours,'potential'] = poss_batt_changes[0,charging_hours]
    df.loc[:,'load'] = load_profile
    df.loc[:,'block'] = -1
    df.fillna(0,inplace=True)
    charge_blocks = pd.DataFrame(columns=['end discharge','begin discharge'])
    block = []
    for i in np.arange(1,len(discharging_hours-1),1):
        if discharging_hours[i] != discharging_hours[i-1] + 1:
            block.extend(discharging_hours[i-1:i+1])
            charge_blocks.loc[len(charge_blocks),:] = block
            block = []
    if poss_batt_changes[0,0] > 0:
        charge_blocks.loc[-1,:] = [-1,discharging_hours[0]]
        charge_blocks.index += 1
        charge_blocks.sort_index(inplace=True)
    charge_blocks.loc[len(charge_blocks),:] = [discharging_hours[-1], len(load_profile)]
    # Get the energy requirements for meeting peak discharging
    charge_blocks.loc[:,:] = charge_blocks.loc[:,:].astype(int)
    for i in np.arange(0,len(charge_blocks)-1,1):
        charge_blocks.loc[i,'required_MWh'] = -np.min(batt_e_level[0, \
            charge_blocks.loc[i,'begin discharge']:charge_blocks.loc[i+1,'end discharge']+1])
    charge_blocks.fillna(0,inplace=True)
    charge_blocks.loc[:,'MWh_charged'] = 0
    # Optimize charging
    for i in range(0,len(charge_blocks)):
        df.loc[charge_blocks.loc[i,'end discharge']+1:charge_blocks.loc[i,'begin discharge']-1,'block'] = i
        t0 = charge_blocks.loc[i,'begin discharge']
        MWh_needed = charge_blocks.loc[0:i,'required_MWh'].sum() - charge_blocks.loc[0:i,'MWh_charged'].sum()
        MWh = 0.0
        df_subset = df[df['hour']<t0].reset_index(drop=True)
        df_subset = df_subset[df_subset['potential']>0].reset_index(drop=True)
        df_subset = df_subset.sort_values('load').reset_index(drop=True)
        hour = 0
        while MWh_needed > MWh:
            try:
                MWh_add = min(df_subset.loc[hour,'potential'], MWh_needed-MWh)
                Hr = df_subset.loc[hour,'hour']
                Blk = df_subset.loc[hour,'block']
                if charge_blocks.loc[Blk,'MWh_charged'] + MWh_add > storage_fleet_MWh:
                    MWh_add = storage_fleet_MWh - charge_blocks.loc[Blk,'MWh_charged']
                    df.loc[df['block']==Blk,'potential'] = 0
                    df_subset = df_subset[df_subset['block']!=Blk].reset_index(drop=True)
                else:
                    df.loc[Hr,'potential'] -= MWh_add
                df.loc[Hr,'load'] += MWh_add / eff_charge
                load_profile[Hr] += MWh_add / eff_charge
            except:
                MWh_add = MWh_needed-MWh
            charge_blocks.loc[Blk,'MWh_charged'] += MWh_add
            hour += 1
            MWh += MWh_add
    
    load_profile = np.clip(load_profile, a_min=None, a_max=max_demands[0,0], out=load_profile)    
    
    return load_profile

# --------------------- CALC CC OF MARGINAL STORAGE ---------------------------
def cc_storage_csp(required_MWhs, batt_powers, stor_MWh, stor_MW):
    '''Determine the capacity credit of CSP-TES
       Can use several discrete values for storage duration or a single value
       More details on the methodology used can be found here: <file location>
       Args:
           required_MWhs: energy storage capacities needed to satisfy associated demand reductions
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
        
    # existing cc calculation for case where peak reduction is less than installed power capacity
    else:
        # get effective capacity of installed storage
        cap_eff = np.interp(stor_MWh, required_MWhs, batt_powers[:,0])
        # get CC of existing storage
        cc_stor = cap_eff/stor_MW
        # rounding outputs to the nearest 5 decimal points
        cc_stor = np.around(cc_stor, decimals=5)
        
    return cc_stor


# --------------------- CALC CC OF MARGINAL STORAGE ---------------------------
def cc_storage_conv(required_MWhs, batt_powers, stor_MWh, stor_MW, marg_durations, marg_stor_step_MW):
    '''Determine the existing and marginal capacity credit of conventional storage
       Can use several discrete values for storage duration or a single value
       More details on the methodology used can be found here: <file location>
       Args:
           required_MWhs: energy storage capacities needed to satisfy associated demand reductions
           batt_powers: demand reductions explored
           stor_MWh: energy storage capacity of the existing fleet
           stor_MW: power storage capacity of the existing fleet
           marg_durations: duration(s) of marginal storage for marginal cc calculation
           marg_stor_step_MW: marginal power capacity
       Returns:
           cc_stor: capacity credit of the existing storage fleet
           cc_stor_marg: capacity credit(s) of marginal storage, depending on duration of marginal addition
    '''
    
    stor_inc = len(required_MWhs) - 1
    
    # cc for case where peak reduction equals installed power capacity
    if (required_MWhs[stor_inc-1] <= stor_MWh):
        # get CC of existing storage
        cc_stor = 1.0
        
    # existing cc calculation for case where peak reduction is less than installed power capacity
    else:
        # get effective capacity of installed storage
        cap_eff = np.interp(stor_MWh, required_MWhs, batt_powers[:,0])
        # get CC of existing storage
        cc_stor = cap_eff/stor_MW
        # rounding outputs to the nearest 5 decimal points
        cc_stor = np.around(cc_stor, decimals=5)
    
    # marginal and existing cc calculations for case where peak reduction equals installed power capacity
    if (required_MWhs[stor_inc-1] <= stor_MWh):
        # get the marginal CC of storage, depending on the shape of the marginal use curve and the duration of the marginal addition
        slope = (batt_powers[stor_inc,0] - batt_powers[stor_inc-1,0]) / (required_MWhs[stor_inc] - required_MWhs[stor_inc-1])
        # I think since the conditional statement changes here for each duration d that this is more efficient than using np.clip
        cc_stor_marg = np.array([np.where(required_MWhs[stor_inc] <= (stor_MWh + marg_stor_step_MW * d), 1.0, slope * d) for d in marg_durations])

        
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
def do_a_year(input_gdx_file, output_gdx_file, scenario, year, next_year, annual_hours, season_hours, marg_stor_step_MW, marg_VG_step_MW, marg_CSP_step_MW, csp, calc_annual=False):
    
#%% GETTING INPUTS FROM REEDS FIRST THAT ARE NEEDED FOR MODIFYING STATIC INPUTS IF NECESSARY

    # -------Get the gdx file from ReEDS -------
    
    gdxin = gdxpds.to_dataframes(input_gdx_file)
       

    # ------- Get all spatial & temporal mappers for the current run -------
    
    # BAs present in the current run
    rfeas = gdxin['rfeas'].copy().drop('Value',1)
    
    # Mapping BAs to resource regions
    r_rs = gdxin['r_rs'].copy().drop('Value',1)
    r_rs = r_rs[r_rs['r'].isin(rfeas['r'])].reset_index(drop=True)
    r_rs = r_rs[r_rs['rs']!='sk'].sort_values(['r','rs']).reset_index(drop=True) 
    
    # Hierarchy for all other areas
    hierarchy = gdxin['hierarchy'].copy().drop('Value',1)
    hierarchy = hierarchy[hierarchy['r'].isin(rfeas['r'])].reset_index(drop=True)
    hierarchy = pd.merge(left=r_rs, right=hierarchy, on='r', how='right')  
    
    # Temporal mapper defining which seasons contain which hours
    dt8760 = pd.read_excel(os.path.join('inputs_case','h_dt_szn.xlsx'))  
    
    
    # ------- Get all technology subsets -------
    
    # Read from tech-subset-table.csv
    tech_table = pd.read_csv(os.path.join('inputs_case','tech-subset-table.csv'), index_col=0)
    techs = {tech:list() for tech in list(tech_table)}
    for tech in techs.keys():
        techs[tech] = tech_table[tech_table[tech]=='YES'].index.values.tolist()
        techs[tech] = [x.lower() for x in techs[tech]]
        temp_save = []
        temp_remove = []
        # Interpreting GAMS syntax in tech-subset-table.csv
        for subset in techs[tech]:
            if '*' in subset:
                temp_remove.append(subset)
                temp = subset.split('*')
                temp2 = temp[0].split('_')
                temp_low = pd.to_numeric(temp[0].split('_')[-1])
                temp_high = pd.to_numeric(temp[1].split('_')[-1])
                temp_tech = ''
                for n in range(0,len(temp2)-1):
                    temp_tech += temp2[n]
                    if not n == len(temp2)-2: temp_tech += '_'
                for c in range(temp_low,temp_high+1):
                    temp_save.append('{}_{}'.format(temp_tech,str(c)))
        for subset in temp_remove:
            techs[tech].remove(subset)
        techs[tech].extend(temp_save)
    del tech_table
    
    
    # ------- Load run-specific data from pickle files -------
    
    load_profiles = pd.read_pickle(os.path.join('inputs_case','load_{}.pkl'.format(scenario)))
    load_profiles.index = dt8760['datetime']
    recf = pd.read_pickle(os.path.join('inputs_case','recf_{}.pkl'.format(scenario)))
    recf.index = dt8760['datetime']
    cspcf = pd.read_pickle(os.path.join('inputs_case','csp_profiles_{}.pkl'.format(scenario)))
    cspcf.index = dt8760['datetime']
    resources = pd.read_pickle(os.path.join('inputs_case','resources_{}.pkl'.format(scenario)))
    csp_resources = pd.read_pickle(os.path.join('inputs_case','csp_resources_{}.pkl'.format(scenario)))
    
#   GET REEDS SOLVE VARIABLES AND PERFORM YEAR OVER YEAR ADJUSTMENTS
    
    
    # ------- Get all capacities -------
    
    cap = gdxin['cap_export'].copy()
    cap.columns = ['i','r','t','MW']
    cap.loc[:,'i'] = cap.loc[:,'i'].str.lower()
    cap.loc[:,'resource'] = cap.loc[:,'i'] + '_' + cap.loc[:,'r']
    
    # ------- Getting all VRE capacities -------
    
    cap_vre = cap[cap['i'].isin(techs['VRE_NO_CSP'])].reset_index(drop=True)
    cap_csp = cap[cap['i'].isin(techs['CSP'])].reset_index(drop=True)
    cap_csp_ns = cap[cap['i'].isin(techs['CSP_NOSTORAGE'])].reset_index(drop=True)
    
    # ------- Getting all storage capacities -------

    # Getting storage duration by tech
    durations = gdxin['storage_duration'].copy()
    durations.columns = ['i','duration']
    
    # Getting energy capacities for storage
    cap_stor = cap[cap['i'].isin(techs['STORAGE_NO_CSP'])]
    cap_stor = pd.merge(left=cap_stor, right=hierarchy[['r','rto']].drop_duplicates(), on='r', how='left')
    cap_stor = pd.merge(left=cap_stor, right=durations, on='i', how='left')
    cap_stor.loc[:,'MWh'] = cap_stor.loc[:,'MW'] * cap_stor.loc[:,'duration']
    
    # Getting round-trip efficiencies
    stor_RTE = gdxin['storage_eff'].copy()
    stor_RTE.columns = ['i','t','RTE']    
    stor_RTE = stor_RTE[stor_RTE['t']==year].drop('t',1)
    stor_RTE = pd.merge(left=stor_RTE, right=cap_stor[['i','MWh','rto']], on='i', how='right')
    stor_RTE.loc[:,'RTE'] = stor_RTE.loc[:,'RTE'] * stor_RTE.loc[:,'MWh']
    stor_RTE = stor_RTE.groupby(by='rto').mean()
    stor_RTE.loc[:,'RTE'] = stor_RTE.loc[:,'RTE'] / stor_RTE.loc[:,'MWh']
    stor_RTE.drop('MWh',1,inplace=True)
    
    # Aggregrating storage capacities by RTO
    cap_stor_rto = cap_stor.drop('duration',1).groupby(by='rto').sum()
    cap_stor = cap_stor[['i','r','MW']]
    
    # ------- Getting csp solar multiple information -------
    
    csp_sm = gdxin['csp_sm'].copy()
    csp_sm.columns = ['i','sm']
    cap_csp = pd.merge(left=cap_csp, right=csp_sm, on='i', how='left')
    cap_csp = pd.merge(left=cap_csp, right=durations, on='i', how='left')
    cap_csp.loc[:,'MWh'] = cap_csp.loc[:,'MW'] * cap_csp.loc[:,'duration']
    csp_resources = pd.merge(left=csp_resources, right=csp_sm, on='i', how='left')
    csp_resources = pd.merge(left=csp_resources, right=durations, on='i', how='left')
    
    
    # ------- Adjust load profiles by this year's load multiplier by BA -------

    # Getting the scaling factors
    load_mult = gdxin['load_multiplier'].copy()
    load_mult = load_mult.pivot(index='cendiv', columns='t', values='Value').reset_index()
    load_mult = pd.merge(left=hierarchy[['r','cendiv']].drop_duplicates(), right=load_mult, on='cendiv', how='left') 
    load_mult = load_mult.sort_values('r')[year].values
    load_mult = np.tile(load_mult.reshape(1,len(rfeas)), (len(load_profiles),1))    
    
    # Scaling the load profiles
    load_profiles = load_profiles * load_mult 
    
    
    # ------- Adjust wind capacity factor profiles for this year -------
    ### This scaling method will cause some hourly CFs after 2030 to be greater than one and up to 1.91 under ATB Mid 2019
    # Capacity factors of wind for scaling wind CF profiles
    wind_cf = gdxin['windcfin'].copy()
    wind_cf.columns = ['t','i','windCF']
    wind_cf = wind_cf[wind_cf['t']==str(year)].reset_index(drop=True)

    # Get the mean of all CF profiles
    wind_scaling = recf.mean().reset_index()
    wind_scaling.columns = ['resource','Mean']
    wind_scaling = pd.merge(left=resources,right=wind_scaling, on='resource')
    wind_scaling = pd.merge(left=wind_scaling,right=wind_cf, on='i', how='left')
    
    # Scale wind CFs by the ratio between the CF from ReEDS and the mean of the CF profile
    index_wind = (wind_scaling['i'].isin(techs['WIND']))
    index_notwind = (wind_scaling['i'].isin(techs['WIND'])==False)
    wind_scaling.loc[index_wind,'scaling_factor'] = wind_scaling.loc[index_wind,'windCF'] / wind_scaling.loc[index_wind,'Mean']
    wind_scaling.loc[index_notwind,'scaling_factor'] = 1

    wind_scaling = wind_scaling['scaling_factor'].values
    wind_scaling = np.tile(wind_scaling.reshape(1,len(resources)), (len(load_profiles),1))

    # Scale the CF profiles
    recf = recf * wind_scaling
    del wind_scaling, wind_cf, index_wind, index_notwind
    
    # Clipping all profiles at 1
    recf = np.clip(recf, a_min=None, a_max=1.0)
    
#  INITIALIZE DATAFRAMES TO STORE RESULTS
    if calc_annual:
        annual_all_cc = pd.DataFrame(columns=['i','r','t','MW'])
        annual_all_cc_mar = pd.DataFrame(columns=['i','r','t','CC'])
        annual_timeslice_hours_all = pd.DataFrame(columns=['h','rto','%TopHrs'])
    
    season_all_cc = pd.DataFrame(columns=['i','r','season','t','MW'])
    season_all_cc_mar = pd.DataFrame(columns=['i','r','season','t','CC'])
    season_timeslice_hours_all = pd.DataFrame(columns=['h','rto','season','%TopHrs'])

    
#%%  FOR LOOP FOR RTOS

    # March through this for all RTOs
    for rto in hierarchy['rto'].drop_duplicates():
        
#%%  RTO DATA
        
        print("Calculating capacity credit for {}".format(rto))
        # ------- Get load profile, RECF profiles, VG capacity, storage capacity, and storage RTE for this RTO -------
        
        # Select the load profiles of the BAs in this RTO and merge in columns for season, hour, and timeslice
        load_profile_rto = load_profiles[hierarchy[hierarchy['rto']==rto]['r'].drop_duplicates()]
        load_profile_rto = load_profile_rto.sum(axis=1).reset_index().rename(columns={0:'Load'})
        load_profile_rto = pd.merge(left=dt8760,right=load_profile_rto,on='datetime')
        
        # Select the VG CF profiles of the resources in this RTO and merge in columns for season, hour, and timeslice
        recf_rto = recf[resources[resources['rto']==rto]['resource']].reset_index()
        recf_rto = pd.merge(left=dt8760, right=recf_rto, on='datetime')
        
        # Select the resources that are in this RTO
        resources_rto = resources[resources['resource'].isin(list(recf_rto))].reset_index(drop=True)
        resources_rto_csp = csp_resources[csp_resources['rto']==rto].reset_index(drop=True)
        
        # Get the VG capacity for this rto in this year in the same order as the columns in the recf DataFrame
        cap_vre_rto = pd.DataFrame({'resource':list(recf_rto.drop(list(dt8760),1))})
        cap_vre_rto = pd.merge(left=cap_vre_rto, right=cap_vre, on='resource', how='left').drop(['r','i'],1).fillna(0)
        
        # Assume all storage RTE losses happen in charging
        try:
            eff_charge = stor_RTE.loc[rto,'RTE']
        except:
            eff_charge = 0.81
        
        # Get the fleet-wide power and energy capacity of storage for this RTO
        try:
            storage_fleet_MW = cap_stor_rto.loc[rto,'MW']
            storage_fleet_MWh = cap_stor_rto.loc[rto,'MWh']
        except:
            storage_fleet_MW = 0
            storage_fleet_MWh = 0
            
        # Make a numpy array of power capacities for the calc_required_MWh function
        reductions_considered = 100
        peak_reductions = np.linspace(0, storage_fleet_MW, reductions_considered)
        peak_reductions = np.append(peak_reductions, storage_fleet_MW + marg_stor_step_MW)
        
        # Energy storage of the CSP fleet and CSP profiles if they exist
        if not resources_rto_csp.empty:
            cap_csp_rto = cap_csp[cap_csp['resource'].isin(resources_rto_csp['resource'])].reset_index(drop=True)
            cspcf_rto_all = cspcf[resources_rto_csp['resource']].reset_index()
            cspcf_rto_all = pd.merge(left=dt8760, right=cspcf_rto_all, on='datetime')
            cspcf_rto_cols = list(dt8760) + cap_csp_rto['resource'].tolist()
            cspcf_rto = cspcf_rto_all[cspcf_rto_cols]
            csp_fleet_MW = cap_csp_rto['MW'].sum()
            csp_fleet_MWh = cap_csp_rto['MWh'].sum()
        

        # ---------------------------- CALL FUNCTIONS ---------------------------------
        if calc_annual:
            
            # Call cc_vg
            cc_vg_results = cc_vg(recf_rto.drop(list(dt8760),1).values.copy(), load_profile_rto['Load'].values.copy(),
                                  cap_vre_rto['MW'].values.copy(), annual_hours, marg_VG_step_MW)
            
    
            # Get the fractions of top hours in each timeslice
            temp = dt8760.loc[dt8760.index.isin(cc_vg_results['top_hours_net']),'h'].value_counts()/annual_hours
            temp = temp.reset_index().rename(columns={"index":"timeslice","timeslice":"%TopHrs"})
            temp.loc[:,'rto'] = rto
            annual_timeslice_hours_all = pd.concat([annual_timeslice_hours_all,temp],sort=False).reset_index(drop=True)
            
            # Get the CC of wind and PV
            vg_cc_rto = resources_rto[['i','r']].copy()
            vg_cc_rto.loc[:,'t'] = next_year
            vg_cc_rto['MW'] = cc_vg_results['cap_useful_MW']
            annual_all_cc = pd.concat([annual_all_cc, vg_cc_rto],sort=False).reset_index(drop=True)
            
            # Get the marginal cc of wind and PV
            vg_cc_rto_mar = vg_cc_rto.drop('MW',1)
            vg_cc_rto_mar['CC'] = cc_vg_results['cc_marg']
            annual_all_cc_mar = pd.concat([annual_all_cc_mar, vg_cc_rto_mar],sort=False).reset_index(drop=True)
            
            # Set the net load profile
            net_load_profile = cc_vg_results['load_net']
            
            if not resources_rto_csp.empty:
                
                if csp == '0':
                    # If not calculating CC for CSP, set its CC to 1
                    annual_cc_csp = 1.0
                
                if csp == '1':
                    # Call csp storage cc functions for existing csp
                    annual_required_MWhs_csp, annual_csp_powers = calc_required_mwh_csp(net_load_profile.copy(), cap_csp_rto['MW'].values.copy(), cap_csp_rto['sm'].values.copy(),
                                                        cspcf_rto.drop(dt8760,1).values.copy(), reductions_considered, combine_profiles=True)
                    annual_cc_csp = cc_storage_csp(annual_required_MWhs_csp.copy(), annual_csp_powers.copy(), csp_fleet_MWh, csp_fleet_MW)
                    
                    # Clip load according to existing csp cc
                    net_load_profile = np.clip(net_load_profile, a_min=None, a_max = (max(net_load_profile) - (csp_fleet_MW * annual_cc_csp)), out=net_load_profile)
                
                # Get the CC of CSP
                csp_cc_rto = resources_rto_csp[['i','r','resource']]
                csp_cc_rto = pd.merge(left=csp_cc_rto, right=cap_csp_rto[['i','r','resource','MW']], on=['i','r','resource'], how='left').fillna(0)
                csp_cc_rto.loc[:,'MW'] *= annual_cc_csp
                csp_cc_rto.loc[:,'t'] = next_year
                csp_cc_rto.drop('resource',1,inplace=True)
                annual_all_cc = pd.concat([annual_all_cc,csp_cc_rto], sort=False).reset_index(drop=True)
            
            # Call storage cc functions for existing and marginal conventional storage
            annual_required_MWhs, annual_batt_powers = calc_required_mwh(net_load_profile.copy(), peak_reductions.copy(), eff_charge)
            annual_cc_stor, annual_cc_stor_mar = cc_storage_conv(annual_required_MWhs.copy(), annual_batt_powers.copy(), storage_fleet_MWh, storage_fleet_MW, durations[durations['i'].isin(techs['STORAGE_NO_CSP'])]['duration'].tolist(), marg_stor_step_MW)
            
            # Get the CC of storage
            temp_rto = [rto] * len(techs['STORAGE_NO_CSP'])
            temp_cc_stor = [annual_cc_stor] * len(techs['STORAGE_NO_CSP'])
            stor_cc_rto = pd.DataFrame({'rto': temp_rto, 'i': techs['STORAGE_NO_CSP'], 'CC': temp_cc_stor})
            stor_cc_rto = pd.merge(left=hierarchy[['r','rto']].drop_duplicates(), right=stor_cc_rto, on='rto', how='inner').drop('rto',1)
            stor_cc_rto.loc[:,'t'] = next_year
            stor_cc_rto = pd.merge(left = stor_cc_rto, right = cap_stor, on=['i','r'], how='left').fillna(0)
            stor_cc_rto.loc[:,'MW'] = stor_cc_rto.loc[:,'CC'] * stor_cc_rto.loc[:,'MW']
            stor_cc_rto = stor_cc_rto.drop('CC',1)
            annual_all_cc = pd.concat([annual_all_cc, stor_cc_rto],sort=False).reset_index(drop=True)
            
            # Get the marginal CC for each storage tech
            stor_cc_rto_mar = pd.DataFrame({'rto': temp_rto, 'i': techs['STORAGE_NO_CSP'], 'CC': annual_cc_stor_mar})
            stor_cc_rto_mar = pd.merge(left=stor_cc_rto_mar, right=hierarchy[['r','rto']].drop_duplicates(), on='rto', how='inner').drop('rto',1)
            stor_cc_rto_mar.loc[:,'t'] = next_year
            annual_all_cc_mar = pd.concat([annual_all_cc_mar, stor_cc_rto_mar],sort=False).fillna(1).reset_index(drop=True)
            
            # Fill in troughs with storage charging
                    
            
            if not resources_rto_csp.empty:
                if csp == '0':
                    # Set the marginal CC for CSP equal to 1
                    csp_cc_rto.drop('MW',1,inplace=True)
                    csp_cc_rto.loc[:,'CC'] = 1
                    annual_all_cc_mar = pd.concat([annual_all_cc_mar,csp_cc_rto], sort=False).reset_index(drop=True)
                    
                if csp == '1':
                    # Add the current charging load if needed
                    if storage_fleet_MW > 0:
                        peak_reductions = np.array([storage_fleet_MW * annual_cc_stor])
                        net_load_profile = fill_in_charging(net_load_profile, peak_reductions, eff_charge, storage_fleet_MWh, storage_fleet_MW)
                    # Call csp storage marginal cc functions for each csp resource
                    peak_reductions = (np.ones((1,len(resources_rto_csp))) * marg_CSP_step_MW).reshape(len(resources_rto_csp))
                    annual_required_MWhs_csp_marg, annual_csp_powers_marg = calc_required_mwh_csp(net_load_profile.copy(), peak_reductions.copy(), resources_rto_csp['sm'].values.copy(),
                            cspcf_rto_all.drop(list(dt8760),1).values.copy(), len(resources_rto_csp))
                    csp_cc_rto_mar = resources_rto_csp[['i','r','duration','resource','sm']].copy()
                    csp_cc_rto_mar['MW'] = peak_reductions
                    csp_cc_rto_mar.loc[:,'required_MWh'] = annual_required_MWhs_csp_marg
                    csp_cc_rto_mar.loc[:,'MWh'] = csp_cc_rto_mar.loc[:,'MW'] * csp_cc_rto_mar.loc[:,'duration']
                    csp_cc_rto_mar_full = pd.DataFrame(columns=list(csp_cc_rto_mar)+['CC','t'])
                    csp_cc_rto_mar_part = pd.DataFrame(columns=list(csp_cc_rto_mar)+['CC','t'])
                    for i in range(0,len(csp_cc_rto_mar)):
                        if csp_cc_rto_mar.loc[i,'required_MWh'] > csp_cc_rto_mar.loc[i,'MWh']:
                            csp_cc_rto_mar_part.loc[len(csp_cc_rto_mar_part),:] = csp_cc_rto_mar.loc[i,:]
                        else:
                            csp_cc_rto_mar_full.loc[len(csp_cc_rto_mar_full),:] = csp_cc_rto_mar.loc[i,:]
                    if not csp_cc_rto_mar_full.empty:
                        csp_cc_rto_mar_full.loc[:,'t'] = next_year
                        csp_cc_rto_mar_full.loc[:,'CC'] = 1
                        annual_all_cc_mar = pd.concat([annual_all_cc_mar,csp_cc_rto_mar_full[list(annual_all_cc_mar)]], sort=False).reset_index(drop=True)
                    
                    for i in range(0,len(csp_cc_rto_mar_part)):
                        sm = csp_cc_rto_mar_part.loc[i,'sm']
                        duration = csp_cc_rto_mar_part.loc[i,'duration']
                        resource = csp_cc_rto_mar_part.loc[i,'resource']
                        peak_reductions = np.linspace(0, marg_CSP_step_MW, reductions_considered)
                        annual_required_MWhs_csp_marg_part, annual_csp_powers_marg_part = calc_required_mwh_csp(net_load_profile.copy(), peak_reductions.copy(), sm, cspcf_rto_all[resource].values.copy(), reductions_considered)
                        annual_cc_csp_mar_part = cc_storage_csp(annual_required_MWhs_csp_marg_part.copy(), annual_csp_powers_marg_part.copy(), marg_CSP_step_MW*duration, marg_CSP_step_MW)
                        csp_cc_rto_mar_part.loc[i,'CC'] = annual_cc_csp_mar_part
                        csp_cc_rto_mar_part.loc[i,'t'] = next_year
                    annual_all_cc_mar = pd.concat([annual_all_cc_mar,csp_cc_rto_mar_part[list(annual_all_cc_mar)]], sort=False).reset_index(drop=True)
            
            # Assigning the marginal CC of the highest class of UPV in each region as the marginal CC of CSP-NS
            csp_ns_cc_rto = resources_rto[resources_rto['i'].isin(techs['UPV'])].drop(['rto','resource'],1)
            csp_ns_cc_rto = csp_ns_cc_rto.drop_duplicates(subset='r', keep='last')
            csp_ns_cc_rto = pd.merge(left=csp_ns_cc_rto, right=vg_cc_rto_mar, on=['r','i'], how='left').rename(columns={'area': 'ba'})
            csp_ns_cc_rto = pd.merge(left=csp_ns_cc_rto, right=r_rs, on='r', how='inner').drop('r',1).rename(columns={'rs':'r'})
            csp_ns_cc_rto.loc[:,'i'] = 'csp-ns'
            csp_ns_cc_rto_mar = csp_ns_cc_rto.copy()
            csp_ns_cc_rto = pd.merge(left=csp_ns_cc_rto, right=cap_csp_ns[['i','r','MW']], on=['i','r'], how='left').fillna(0)
            csp_ns_cc_rto.loc[:,'MW'] = csp_ns_cc_rto.loc[:,'MW'] * csp_ns_cc_rto.loc[:,'CC']
            csp_ns_cc_rto = csp_ns_cc_rto.drop('CC',1)
            annual_all_cc = pd.concat([annual_all_cc, csp_ns_cc_rto],sort=False).reset_index(drop=True)
            annual_all_cc_mar = pd.concat([annual_all_cc_mar, csp_ns_cc_rto_mar],sort=False).reset_index(drop=True)
        
        
#%%  FOR LOOP FOR SEASONS
        
        for season in dt8760['season'].drop_duplicates():

            
#%%  SEASONAL DATA MANIPULATIONS
            
            # Get the load and CF profiles for this season
            load_profile_season = load_profile_rto[load_profile_rto['season']==season].sort_values('datetime').reset_index(drop=True)
            recf_season = recf_rto[recf_rto['season']==season].sort_values('datetime').reset_index(drop=True)
            cspcf_season_all = cspcf_rto_all[cspcf_rto_all['season']==season].sort_values('datetime').reset_index(drop=True)
            cspcf_season = cspcf_rto[cspcf_rto['season']==season].sort_values('datetime').reset_index(drop=True)
            dt_season = dt8760[dt8760['season']==season].sort_values('datetime').reset_index(drop=True)
            
#   CALL FUNTIONS SEASONALLY
            
            # ---------------------------- CALL FUNCTIONS ---------------------------------
            
            # Call cc_vg
            season_cc_vg_results = cc_vg(recf_season.drop(list(dt8760),1).values.copy(), load_profile_season['Load'].values.copy(),
                                  cap_vre_rto['MW'].values.copy(), season_hours, marg_VG_step_MW)
            
            # Get the fractions of top hours in each timeslice
            temp = dt_season.loc[dt_season.index.isin(season_cc_vg_results['top_hours_net']),'h'].value_counts()/season_hours
            temp = temp.reset_index().rename(columns={"index":"h","h":"%TopHrs"})
            temp.loc[:,'rto'] = rto
            temp.loc[:,'season'] = season
            season_timeslice_hours_all = pd.concat([season_timeslice_hours_all,temp],sort=False).reset_index(drop=True)
            
            # Get the CC of wind and PV
            vg_cc_season = resources_rto[['i','r']].copy()
            vg_cc_season.loc[:,'t'] = next_year
            vg_cc_season.loc[:,'season'] = season
            vg_cc_season['MW'] = season_cc_vg_results['cap_useful_MW']
            season_all_cc = pd.concat([season_all_cc, vg_cc_season],sort=False).reset_index(drop=True)
            
            # Get the marginal CC of wind and PV
            vg_cc_season_mar = vg_cc_season.drop('MW',1)
            vg_cc_season_mar['CC'] = season_cc_vg_results['cc_marg']
            season_all_cc_mar = pd.concat([season_all_cc_mar,vg_cc_season_mar],sort=False).reset_index(drop=True)
            
            # Set the net load profile
            net_load_profile = season_cc_vg_results['load_net']
            
            if not resources_rto_csp.empty:
                if csp == '0':
                    # If not calculating csp cc, set it to 1
                    season_cc_csp = 1.0
                    
                if csp == '1':
                    # If calculating csp cc, call csp storage cc functions for existing csp
                    season_required_MWhs_csp, season_csp_powers = calc_required_mwh_csp(net_load_profile.copy(), cap_csp_rto['MW'].values.copy(), cap_csp_rto['sm'].values.copy(), cspcf_season.drop(list(dt_season),1).values.copy(), reductions_considered, combine_profiles=True)
                    season_cc_csp = cc_storage_csp(season_required_MWhs_csp.copy(), season_csp_powers.copy(), csp_fleet_MWh, csp_fleet_MW)
                
                    # Clip load according to existing csp cc
                    net_load_profile = np.clip(net_load_profile, a_min=None, a_max = (max(net_load_profile) - (csp_fleet_MW * season_cc_csp)), out=net_load_profile)
                    
                # Get the CC of CSP
                csp_cc_season = resources_rto_csp[['i','r','resource']]
                csp_cc_season = pd.merge(left=csp_cc_season, right=cap_csp_rto[['i','r','resource','MW']], on=['i','r','resource'], how='left').fillna(0)
                csp_cc_season.loc[:,'MW'] *= season_cc_csp
                csp_cc_season.loc[:,'t'] = next_year
                csp_cc_season.loc[:,'season'] = season
                csp_cc_season.drop('resource',1,inplace=True)
                season_all_cc = pd.concat([season_all_cc,csp_cc_season],sort=False).reset_index(drop=True)
                
            # Call storage cc functions for existing conventional storage
            peak_reductions = np.linspace(0, storage_fleet_MW, reductions_considered).tolist()
            peak_reductions = np.array(peak_reductions + [storage_fleet_MW + marg_stor_step_MW])
            season_required_MWhs, season_batt_powers = calc_required_mwh(net_load_profile.copy(), peak_reductions.copy(), eff_charge)
            season_cc_stor, season_cc_stor_mar = cc_storage_conv(season_required_MWhs.copy(), season_batt_powers.copy(), storage_fleet_MWh, storage_fleet_MW, durations[durations['i'].isin(techs['STORAGE_NO_CSP'])]['duration'].tolist(), marg_stor_step_MW)
            
            # Get the CC of storage
            temp_season = [season] * len(techs['STORAGE_NO_CSP'])
            temp_rto = [rto] * len(techs['STORAGE_NO_CSP'])
            temp_cc_stor = [season_cc_stor] * len(techs['STORAGE_NO_CSP'])
            stor_cc_season = pd.DataFrame({'rto': temp_rto, 'i': techs['STORAGE_NO_CSP'], 'season': temp_season, 'CC': temp_cc_stor})
            stor_cc_season = pd.merge(left=hierarchy[['r','rto']].drop_duplicates(), right=stor_cc_season, on='rto', how='inner').drop('rto',1)
            stor_cc_season.loc[:,'t'] = next_year
            stor_cc_season = pd.merge(left=stor_cc_season, right=cap_stor, on=['i','r'], how='left').fillna(0)
            stor_cc_season.loc[:,'MW'] = stor_cc_season.loc[:,'MW'] * stor_cc_season.loc[:,'CC']
            stor_cc_season = stor_cc_season.drop('CC',1)
            season_all_cc = pd.concat([season_all_cc, stor_cc_season],sort=False).fillna(1).reset_index(drop=True)
            
            # Get the marginal CC for each storage tech
            stor_cc_season_mar = pd.DataFrame({'rto': temp_rto, 'i': techs['STORAGE_NO_CSP'], 'season': temp_season, 'CC': season_cc_stor_mar})
            stor_cc_season_mar = pd.merge(left=stor_cc_season_mar, right=hierarchy[['r','rto']].drop_duplicates(), on='rto', how='inner').drop('rto',1)
            stor_cc_season_mar.loc[:,'t'] = next_year
            season_all_cc_mar = pd.concat([season_all_cc_mar, stor_cc_season_mar],sort=False).fillna(1).reset_index(drop=True)
            
            if not resources_rto_csp.empty:
                if csp == '0':
                    # Set the marginal CC for CSP equal to 1
                    csp_cc_season.drop('MW',1,inplace=True)
                    csp_cc_season.loc[:,'CC'] = 1
                    season_all_cc_mar = pd.concat([season_all_cc_mar,csp_cc_season], sort=False).reset_index(drop=True)
                
                if csp == '1':
                    # Fill in troughs with storage charging if needed
                    if storage_fleet_MW > 0:
                        peak_reductions = np.array([storage_fleet_MW * season_cc_stor])
                        net_load_profile = fill_in_charging(net_load_profile.copy(), peak_reductions.copy(), eff_charge, storage_fleet_MWh, storage_fleet_MW)      
                    
                    # Call csp storage marginal cc functions for each csp resource
                    peak_reductions = (np.ones((1,len(resources_rto_csp))) * marg_CSP_step_MW).reshape(len(resources_rto_csp))
                    season_required_MWhs_csp_marg, season_csp_powers_marg = calc_required_mwh_csp(net_load_profile.copy(), peak_reductions.copy(), resources_rto_csp['sm'].values.copy(),
                            cspcf_season_all.drop(list(dt_season),1).values.copy(), len(resources_rto_csp))
                    csp_cc_season_mar = resources_rto_csp[['i','r','duration','resource','sm']].copy()
                    csp_cc_season_mar['MW'] = peak_reductions
                    csp_cc_season_mar['required_MWh'] = season_required_MWhs_csp_marg
                    csp_cc_season_mar.loc[:,'MWh'] = csp_cc_season_mar.loc[:,'MW'] * csp_cc_season_mar.loc[:,'duration']
                    csp_cc_season_mar_full = pd.DataFrame(columns=list(csp_cc_season_mar)+['CC','t','season'])
                    csp_cc_season_mar_part = pd.DataFrame(columns=list(csp_cc_season_mar)+['CC','t','season'])
                    for i in range(0,len(csp_cc_season_mar)):
                        if csp_cc_season_mar.loc[i,'required_MWh'] > csp_cc_season_mar.loc[i,'MWh']:
                            csp_cc_season_mar_part.loc[len(csp_cc_season_mar_part),:] = csp_cc_season_mar.loc[i,:]
                        else:
                            csp_cc_season_mar_full.loc[len(csp_cc_season_mar_full),:] = csp_cc_season_mar.loc[i,:]
                    if not csp_cc_season_mar_full.empty:
                        csp_cc_season_mar_full.loc[:,'season'] = season
                        csp_cc_season_mar_full.loc[:,'t'] = next_year
                        csp_cc_season_mar_full.loc[:,'CC'] = 1
                        season_all_cc_mar = pd.concat([season_all_cc_mar,csp_cc_season_mar_full[list(season_all_cc_mar)]], sort=False).reset_index(drop=True)
                    for i in range(0,len(csp_cc_season_mar_part)):
                        sm = csp_cc_season_mar_part.loc[i,'sm']
                        resource = csp_cc_season_mar_part.loc[i,'resource']
                        duration = csp_cc_season_mar_part.loc[i,'duration']
                        peak_reductions = np.linspace(0, marg_CSP_step_MW, reductions_considered)
                        season_required_MWhs_csp_marg_part, season_csp_powers_marg_part = calc_required_mwh_csp(net_load_profile.copy(), peak_reductions.copy(), sm, cspcf_season_all[resource].values.copy(), reductions_considered)
                        season_cc_csp_mar_part = cc_storage_csp(season_required_MWhs_csp_marg_part.copy(), season_csp_powers_marg_part.copy(), marg_CSP_step_MW*duration, marg_CSP_step_MW)
                        csp_cc_season_mar_part.loc[i,'CC'] = season_cc_csp_mar_part
                        csp_cc_season_mar_part.loc[i,'t'] = next_year
                        csp_cc_season_mar_part.loc[i,'season'] = season
                    csp_cc_season_mar_part.loc[csp_cc_season_mar_part['CC']>1.0,'CC'] = 1.0
                    season_all_cc_mar = pd.concat([season_all_cc_mar,csp_cc_season_mar_part[list(season_all_cc_mar)]], sort=False).reset_index(drop=True)
            # Assigning the marginal cc of the highest class of UPV in each region as the marginal CC of CSP-NS
            csp_ns_cc_season = resources_rto[resources_rto['i'].isin(techs['UPV'])].drop(['rto','resource'],1)
            csp_ns_cc_season = csp_ns_cc_season.drop_duplicates(subset='r', keep='last')
            csp_ns_cc_season = pd.merge(left=csp_ns_cc_season, right=vg_cc_season_mar, on=['r','i'], how='left').rename(columns={'area': 'ba'})
            csp_ns_cc_season = pd.merge(left=csp_ns_cc_season, right=r_rs, on='r', how='inner').drop('r',1).rename(columns={'rs':'r'})
            csp_ns_cc_season.loc[:,'i'] = 'csp-ns'
            csp_ns_cc_season_mar = csp_ns_cc_season.copy()
            csp_ns_cc_season = pd.merge(left=csp_ns_cc_season, right=cap_csp_ns[['i','r','MW']], on=['i','r'], how='left').fillna(0)
            csp_ns_cc_season.loc[:,'MW'] = csp_ns_cc_season.loc[:,'MW'] * csp_ns_cc_season.loc[:,'CC']
            csp_ns_cc_season = csp_ns_cc_season.drop('CC',1)
            season_all_cc = pd.concat([season_all_cc, csp_ns_cc_season],sort=False).reset_index(drop=True)
            season_all_cc_mar = pd.concat([season_all_cc_mar, csp_ns_cc_season_mar],sort=False).reset_index(drop=True)
           
            
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
    
    if calc_annual:
        annual_all_cc.columns = ['i','r','t','value']
        annual_all_cc_mar.columns = ['i','r','t','value']
        annual_timeslice_hours_all.columns = ['h','rto','value']
    
    season_all_cc_mar.columns = ['i','r','szn','t','value']
    season_all_cc.columns = ['i','r','szn','t','value']
    season_timeslice_hours_all.columns = ['h','rto','szn','value']
    
    # ---------------- WRITE OUT A GDX FILE WITH THE OUTPUTS FOR REEDS ----------------
    
    outputs = {
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
    parser.add_argument("csp", help="""Switch to activate marginal CSP-TES calculations or set CC of CSP to 1""", type=str)
    
    # Optional arguments
    parser.add_argument("-a","--annual", help="""Number of top hours to use for annual VG calculations""", default = 20)
    parser.add_argument("-s","--seasonal", help="""Number of top hours to use for seasonal VG calculations""", default = 10)
    parser.add_argument("-m","--marg_stor_mw", help="""Number of MW used to project marginal storage results""", default = 1000)
    parser.add_argument("-c","--marg_csp_mw", help="""Number of MW used to project marginal CSP-TES results""", default = 1000)
    parser.add_argument("-v","--marg_vg_mw", help="""Number of MW used to project marginal VG results""", default = 1000)
    
    args = parser.parse_args()
    
    
    #%%
    # Preparing to log any errors if they occur
    path_errors = os.path.join('outputs','variabilityFiles','ErrorFile')
    if not os.path.exists(path_errors): os.mkdir(path_errors)
    errorfile = os.path.join(path_errors,'ReEDS_CC_errors_{}_{}.txt'.format(args.scenario,args.next_year))
    logging.basicConfig(filename=errorfile,level=logging.ERROR)
    logger = logging.getLogger(__name__)
    
    # If an error occurs during the script write it to a txt file
    try:
        do_a_year(args.inputs, args.output, args.scenario, args.year, args.next_year, args.annual, args.seasonal, args.marg_stor_mw, args.marg_vg_mw, args.marg_csp_mw, args.csp)
    except:
        logger.error(traceback.format_exc())
    # Removing the error file if it is empty
    logging.shutdown()
    if os.stat(errorfile).st_size == 0:
        os.remove(errorfile)
