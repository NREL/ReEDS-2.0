
import pandas as pd
import numpy as np
import csv
import scipy
import os
import sys
import itertools

# Turning off pandas' SettingWithCopyWarning for chained assignments (which would otherwise be raised for an issue that isn't a problem). 
pd.options.mode.chained_assignment = None


#%%
class scen_settings():
        
    def __init__(self, dollar_year, tech_groups, input_dir):
        self.dollar_year = dollar_year
        self.tech_groups = tech_groups
        self.input_dir = input_dir



#%%
def import_tech_groups(file_path):
    ''' 
    Creates a dictionary of different tech groups from a csv. 
    Used during the import process -- if a particular assumption applies to a family of technologies, 
        this dictionary creates the mapping. 
        
    First column of the input csv is the dictionary key for that tech family. There cannot be duplicate keys, and they must differ from a tech name. 
    '''    
    
        
    tech_subset_table = pd.read_csv(file_path)
    tech_subset_table = tech_subset_table.rename(columns={'Unnamed: 0':'i'})

    tech_subset_table = expand_GAMS_tech_groups(tech_subset_table)
    
    tech_subset_table = tech_subset_table.set_index('i')
    tech_groups = {}    
    for col in list(tech_subset_table.columns):
        tech_groups[col] = list(tech_subset_table[col][tech_subset_table[col]=='YES'].index) 
                
            
    return tech_groups

#%%
def ingest_years(year_set_suffix, sys_eval_years, end_year):
    '''
    modeled_years: The years that will be solved in the GAMS model. Specified by the modeled_years input, cut off by the specified end year. 
    years: All years, not just solve years. Bounded by minimum solve year and max solve year + however long the model looks ahead for evaluating technologies
    year_map: Mapping of each year to the solve year it is associated with
    
    '''
    
    yearset_path = os.path.join('inputs','userinput','modeledyears_%s.csv' % year_set_suffix)
    
    with open(os.path.join(yearset_path)) as f:
        reader = csv.reader(f)
        modeled_years = next(reader)
    modeled_years = np.array(modeled_years, dtype=int)
    modeled_years = modeled_years[modeled_years<=end_year]
    
    # Determine the full range of years, based on modeled_years
    # Extend beyond the last modeled year by the evaluation horizon of the model
    years = np.arange(np.min(modeled_years), np.max(modeled_years)+sys_eval_years, 1)

    # Create the mapping between years and modeled_year (used for grouping values to their modeled year later), merge
    # Contains additional years beyond final year for handling termination year continuation 
    year_map = pd.DataFrame(data={'t':np.arange(np.min(modeled_years), np.max(years)+1, 1)})
    year_map['modeled_year'] = [np.max(modeled_years[year>=modeled_years]) for year in year_map['t']]

    return years, modeled_years, year_map


#%%
def ingest_regions(regions_suffix, reg_type, reg_name, scen_settings):
     
    regions = pd.read_csv(os.path.join(scen_settings.input_dir, 'regions', 'regions_%s.csv' % regions_suffix))

    # Downselect to just the regions in the area specified
    if reg_type=='custom':
        # Custom regions can currently only be specified as a list of 'p' regions
        custom_region = pd.read_csv(os.path.join(scen_settings.input_dir, 'regions', '%s.csv' % reg_name))
        regions = regions[regions['p'].isin(custom_region['p'])]
        
    else:
        regions = regions[regions[reg_type]==reg_name]
        
    # Build a list of the 'p' and 's' regions that are valid
    valid_ba_list = list(regions['p'].drop_duplicates())
    regions_s = list(regions['s'].drop_duplicates())
    valid_regions_list = valid_ba_list + regions_s
    
    return regions, valid_ba_list, valid_regions_list


#%%
def build_dfs(years, techs, regions, ivt_df, year_map, reg_switch):
    
    ''' Build the df_inv and df_gen_pol
    df_inv: df for investment-related parameters (e.g. capital costs). 
    
    Notes:
     - available_for_build means that that [i,v] combo is specified as the vintage available for investment in
       the given year, per the ivt file. 
     
    '''
    
    # Downselect to only the specified region
    # Only [usa] option right now. Better to have 'region_type' and 'regions' option in inputs, and remove rfeas from GAMS. 
    if reg_switch=='usa':    
        regions = regions[regions['country']==reg_switch]
    
    # Expand for subtechs, melt
    # ivt_long is a melted version of the ivt input file
    ivt_df = ivt_df.rename(columns={'Unnamed: 0':'i'})
    ivt_df = expand_GAMS_tech_groups(ivt_df)    
    ivt_long = ivt_df.melt(id_vars='i', var_name='t', value_name='v')
    ivt_long['t'] = ivt_long['t'].astype(int)

    # Determine the first and last year that each [i,v] combination appears
    iv_year_bounds = ivt_long.groupby(by=['i', 'v']).min()
    iv_year_bounds.reset_index(inplace=True)
    iv_year_bounds = iv_year_bounds.rename(columns={'t':'first_year_v_available'})
    iv_last_year = ivt_long.groupby(by=['i', 'v']).max()
    iv_last_year.reset_index(inplace=True)
    iv_last_year.rename(columns={'t':'last_year'}, inplace=True)
    iv_year_bounds = iv_year_bounds.merge(iv_last_year, on=['i', 'v'])
    
    itv_map = pd.DataFrame()
    for tech in techs['i']:
        max_c = np.max(ivt_long[ivt_long['i']==tech]['v'])
        tech_itv_df = pd.DataFrame(list(itertools.product(years, np.arange(1,max_c+1,1))), columns=['t', 'v'])
        tech_itv_df['i'] = tech
        itv_map = pd.concat([itv_map, tech_itv_df], ignore_index=True)
    itv_map = itv_map.merge(iv_year_bounds, on=['i', 'v'])
    itv_map = itv_map[itv_map['t']>=itv_map['first_year_v_available']] # drop all [i,v] combos before the year that v is first available
    itv_map['available_for_build'] = np.where(itv_map['t']<=itv_map['last_year'], True, False) # Flag which vintages are available for building in any given year    
    
    # Split regions into 'p' and 's' regions
    p_regions = regions['p'].drop_duplicates()
    s_regions = regions['s'].drop_duplicates()
    
    # Split techs into 'p' and 's' techs
    p_techs = techs[techs['region_type']=='p']
    s_techs = techs[techs['region_type']=='s']

    # Remove duplicates for each of 's' and 'p' regions, combine into stacked df that has both types in an 'r' column
    regions_s = regions.drop(columns='p').drop_duplicates(keep='first')
    regions_s = regions_s.rename(columns={'s':'r'})
    regions_p = regions.drop(columns='s').drop_duplicates(keep='first')
    regions_p = regions_p.rename(columns={'p':'r'})
    regions_stacked = pd.concat([regions_p, regions_s], ignore_index=True)

    ########################### Build df_inv ##################################
    # Because investment happens on the resource region level, 's' techs have their 's' region for [r]

    # Build the df_itr. Building in two steps, p regions then s regions
    df_inv_p = pd.DataFrame(list(itertools.product(p_techs['i'], years, p_regions)), columns=['i', 't', 'r'])
    df_inv_s = pd.DataFrame(list(itertools.product(s_techs['i'], years, s_regions)), columns=['i', 't', 'r'])
    df_inv = pd.concat([df_inv_p, df_inv_s], ignore_index=True)    
    
    # Merge on other region mappings, to enable later data to be merged using those columns
    df_inv = df_inv.merge(regions_stacked, on=['r'], how='left')
    
    # Since df_inv only contains generators available for build, filter itc map down
    itv_map_inv = itv_map[itv_map['available_for_build']==True]
    
    # Merge on itv_map_inv to expand by [v]
    df_inv = df_inv.merge(itv_map_inv[['i', 't', 'v', 'first_year_v_available']], on=['i', 't']) # Expand for [v]
    
    # Merge on year_map, for useful information later on
    df_inv = df_inv.merge(year_map, on='t', how='left')
    
    
    return df_inv


#%%
def import_sys_financials(financials_sys_suffix, inflation_df, modeled_years, years, year_map, sys_eval_years, scen_settings):
    '''
    Import system-wide financial parameters, and calculate discount rate from them
    
    '''
    
    # Import and merge on inflation rate data
    sys_financials = import_data('financials_sys', financials_sys_suffix, ['t'], scen_settings=scen_settings) 
    sys_financials = sys_financials.merge(inflation_df, on='t', how='left')
    
    # Calculate system-wide discount rates, directly using WACC as discount rate       
    sys_financials['d_nom'] = ((1-sys_financials['debt_fraction'])*(sys_financials['rroe_nom'] - 1) 
                                            + sys_financials['debt_fraction']*(sys_financials['interest_rate_nom'] - 1)
                                            * (1 - sys_financials['tax_rate']) + 1)

    sys_financials['d_nom'] = (sys_financials['debt_fraction']*(sys_financials['interest_rate_nom']-1.0)*(1.0-sys_financials['tax_rate'])
                              + (1.0-sys_financials['debt_fraction'])*(sys_financials['rroe_nom']-1.0)) + 1.0    
    
    
    sys_financials['d_real'] = sys_financials['d_nom'] / sys_financials['inflation_rate']
            
    
    # Calculate present value factors. 
    # Treating as pvf at the beginning of the year, so the first year equals 1, all other years are discounted by cumulation of preceding year's discount rates
    sys_financials = sys_financials.set_index('t')

    # Calculate pvf_capital. 
    sys_financials['pvf_capital'] = 1
    for year in np.arange(np.min(modeled_years)+1, np.max(years)+1):
        sys_financials.loc[year,'pvf_capital'] = sys_financials.loc[year-1,'pvf_capital'] / sys_financials.loc[year-1,'d_real']
        
    # Calculate pvf_onm (only for intertemporal mode). 
    sys_financials.loc[np.min(modeled_years), 'pvf_onm'] = 1 / sys_financials.loc[np.min(modeled_years),'d_real']
    for year in np.arange(np.min(modeled_years)+1, np.max(years)+1):
        sys_financials.loc[year,'pvf_onm'] = sys_financials.loc[year-1,'pvf_onm'] / sys_financials.loc[year,'d_real']
        
    sys_financials = sys_financials.reset_index()
    
    # Calculate the capital recovery factor for each year (for pvf_onm for sequentail mode).
    sys_financials['crf'] = (sys_financials['d_real'] - 1.0) / (1 - (1 / sys_financials['d_real']**sys_eval_years))

    # Merge on year_map for the model year column
    # As an inner merge, this removes any extraneous years, that weren't part of year_map
    sys_financials = sys_financials.merge(year_map, on='t')


    return sys_financials


#%%
def import_data(file_root, file_suffix, indices, scen_settings, inflation_df=[], 
                expand_tech_groups=True, adjust_units=True, check_for_dups=True):
    '''
    Description: General importer that does several useful things
        - If there are currency data inputs, this adjusts them to the model's dollar year
        - If there is an 'i' column, it will expand any tech groups to their full members (making it easier to input data for groups)
        - Checks to make sure there wasn't duplicated entries for the specified indices (could be a problem when expanding)
        
    Arguments:
        indices = column headers that indicate unique entries. E.g. for [i,t,cap_cost,cost_mult], [i,t] would be the indices. 
    
    
    '''
    
    df = pd.read_csv(os.path.join(scen_settings.input_dir, file_root, '%s_%s.csv' % (file_root, file_suffix)))
    
    # Expand tech groups, if there is an 'i' column and the argument is True
    if 'i' in df.columns and expand_tech_groups==True:
        for tech_group in scen_settings.tech_groups.keys():
            if tech_group in list(df['i']):
                
                df_subset = df[df['i']==tech_group] # Extract the tech group from the main df
                df = df[df['i'] != tech_group] # Drop the tech group from the main df
                
                df_list = []
                
                for tech in scen_settings.tech_groups[tech_group]:
                    df_expanded_single = df_subset.copy()
                    df_expanded_single['i'] = tech
                    df_list = df_list + [df_expanded_single]
                    
                df = pd.concat([df]+df_list, ignore_index=True)
                
                
    # Check if a currency_file_root file exists - it should exist if there are 
    # any columns with currency data. If currency data exists, adjust the dollar
    # year of the input data to the scen_settings's dollar year
    if os.path.isfile(os.path.join(scen_settings.input_dir, file_root, 'currency_%s.csv' % file_root)) and adjust_units==True:
        currency_meta = pd.read_csv(os.path.join(scen_settings.input_dir, file_root, 'currency_%s.csv' % file_root), index_col='file')
        inflation_df = inflation_df.set_index('t')
                
        # Check if a row exists in file_root_currency, for the specified input data
        if file_suffix not in currency_meta.index:
            raise Exception('The input data {0}_{1} has a currency input\nbut the currency type is not specified. In the {0} data\ndirectory, open the currency_{0}.csv and enter a new row with metadata\nfor dataset {0}_{1}.csv'.format(file_root, file_suffix))
            
        scenario_currency = currency_meta.loc[file_suffix, :]
    
        for col in scenario_currency.index:
            input_currency = scenario_currency[col]
            input_dollar_year = int(input_currency.replace('USD','')) # Remove the USD. This should be generalized when other currencies are introduced.
            
            if input_dollar_year < scen_settings.dollar_year:
                inflation_adjust = np.array(np.cumprod(inflation_df.loc[input_dollar_year+1:scen_settings.dollar_year]))[-1]
            elif input_dollar_year > scen_settings.dollar_year:
                inflation_adjust = 1.0 / np.array(np.cumprod(inflation_df.loc[scen_settings.dollar_year+1:input_dollar_year]))[-1]
            elif input_dollar_year == scen_settings.dollar_year:
                inflation_adjust = 1.0
                
            df[col] = df[col] * inflation_adjust
            
    # Check to see if there are any duplicate entries for the given indices
    if check_for_dups==True:
        df_index_check = df[indices].copy()
        if len(df_index_check) != len(df_index_check.drop_duplicates()):
            print('Error: Duplicate entries for', file_root, file_suffix, 'on indices', indices)
            sys.exit()
            
                
    return df
   

#%% 
def import_and_mod_incentives(incentive_file_suffix, construction_times_suffix, ivt_df, years, sys_financials, inflation_df, scen_settings):
    '''      
        
    This code assumes any generation policy (gen_pol) is a tax credit, therefore needs to be adjusted later to get in pre-tax terms. 
        If a non-tax-credit generation policy is ever implemented, it would be best to split tax and non-tax apart and sum them together later.
        
    Other assumptions:
        - All eligibility of incentives is assumed to be "start construction", as opposed to "start operation". Therefore, all
            incentives are time shifted by construction times. If a "start operation" incentive is implemented, a column to specify
            whether a given incentive is shifted or not should be added to the input file. 
            
    Notes:
        - Data handling for incentives are more difficult to generalize then other model inputs. This code may be useful for new 
            incentives, but the processed model inputs for any new incentive should be examined and custom code may need to be written.
        - xx_monetized is the value (or fraction) of an incentive, after penalizing it for the costs to monetize, either a time-value-of-money
            "penalty" due to having to wait until tax burden is sufficient, or through the costs of monetizing through tax equity
    
    '''
    
    # Import construction times
    construction_times = import_data('construction_times', construction_times_suffix, ['i', 't_online'], scen_settings=scen_settings, adjust_units=False)
    construction_times['t_start_construction'] = construction_times['t_online'].astype(int) - construction_times['construction_time'].astype(int)
    construction_times = construction_times.rename(columns={'t_online':'t'})
    
    # Expand for subtechs, melt
    ivt_df = ivt_df.rename(columns={'Unnamed: 0':'i'})
    ivt_df = expand_GAMS_tech_groups(ivt_df)    
    ivt_long = ivt_df.melt(id_vars='i', var_name='t', value_name='v')
    ivt_long['t'] = ivt_long['t'].astype(int)
    
    # Import incentives, determine the year the tech would be built based on construction times
    incentive_df = import_data('incentives', incentive_file_suffix, ['i','country','t_start_construction'], inflation_df=inflation_df, scen_settings=scen_settings)
    incentive_df = incentive_df.merge(construction_times, on=['i', 't_start_construction'], how='left')

    # Because of changing construction durations, some incentives don't apply to any online years. Drop those rows. 
    incentive_df = incentive_df[incentive_df['t'].isnull()==False]
    
    # Apply a penalty for monetizing the tax credits through tax equity (or waiting to internally monetize them)
    # The simple reduction of credit value is a simple implementation - more sophisticated estimates of lost
    # value should be made for future analysis that is focused on tax credits. pgagnon 5-7-19
    incentive_df['ptc_value_monetized'] = incentive_df['ptc_value'] * (1 - incentive_df['ptc_tax_equity_penalty'])
    incentive_df['itc_frac_monetized'] = incentive_df['itc_frac'] * (1 - incentive_df['itc_tax_equity_penalty'])
    
    
    return incentive_df[['i', 't', 'country', 'ptc_value', 'ptc_value_monetized', 'ptc_dur', 'itc_frac',
                         'itc_frac_monetized', 'ptc_tax_equity_penalty', 'itc_tax_equity_penalty']]

    
def calc_degradation_adj(d_real,eval_period,annual_degradation):
    if(annual_degradation==0):   
        return 1.0
    else:
        pv_year = 0
        pv = 0
        pv_degraded= 0
        for i in range(0,int(eval_period)+1):
            pv_year = 1/(d_real)**i
            pv = pv + pv_year
            pv_degraded = pv_degraded+ pv_year*(1-annual_degradation)**i
        return pv/pv_degraded
    
#%%
def calc_financial_multipliers(df_inv, construction_schedules, depreciation_schedules, timetype):
    '''

    
    '''

    ###### Calculate the present value multiplier of financing differences for this tech  #########
    # This input is for deviations from the system-wide average financing. For example, a new
    # technology might have financers demanding higher expected dividends before investing,
    # which would result in a penalty here. Conversely, some type of government loan program
    # could result in overall cheaper financing, which would be represented as a benefit here. 

    df_inv['financing_risk_mult'] = 1.0 + df_inv['finance_diff_real'] * ((1-(1/df_inv['d_real']**df_inv['eval_period']))/(df_inv['d_real']-1.0))

    
    #################### Calculate Financial Multiplier  ############################
    df_inv['itc_frac_monetized'] = df_inv['itc_frac_monetized'].fillna(0)
    
    # Multiply the Overnight Capital Cost (OCC) by this to arrive at the total CAPEX    
    Fin = 1 + (1 - np.array(df_inv['tax_rate'])).reshape(len(df_inv),1) * (np.power.outer(df_inv['interest_rate_nom'].values, scipy.append([0],scipy.arange(0.5,10.5,1.)))  - 1)

    # Calculate the construction cost multiplier
    df_inv['CCmult'] = np.array(np.sum(construction_schedules[df_inv['construction_sch']].T * Fin, axis=1))

    # Calculate the (fractional) present value of depreciation 
    df_inv['PV_fraction_of_depreciation'] = np.array(np.sum(depreciation_schedules[df_inv['depreciation_sch'].astype(str)].T / np.power.outer(df_inv['d_nom'].values, scipy.arange(1,22)), axis=1))
    
    # Calculate the Degradation_Adjustment
    if(timetype == 'seq'):
        df_inv['Degradation_Adj'] = df_inv.apply(lambda x: calc_degradation_adj(x['d_real'],x['eval_period'],x['annual_degradation']),axis=1)    
    else:
        df_inv['Degradation_Adj'] = 1.0

    # Calculate the financial multiplier
    df_inv['finMult'] = df_inv['CCmult'] / (1 - df_inv['tax_rate']) * (1 - df_inv['tax_rate'] * (1-df_inv['itc_frac_monetized']/2)*df_inv['PV_fraction_of_depreciation'] - df_inv['itc_frac_monetized'])*df_inv['Degradation_Adj'] 
    df_inv['finMult_noITC'] = df_inv['CCmult'] / (1 - df_inv['tax_rate']) * (1 - df_inv['tax_rate'] *df_inv['PV_fraction_of_depreciation'] )*df_inv['Degradation_Adj'] 
    
        
    return df_inv


#%%
def calc_ptc_unit_value(df_inv):
    '''

    
    '''

    # Calculate the PTC's tax value
    #   Since the PTC reduces income taxes (which are levied on a utility's 
    #   return on their rate base), the actual value of the PTC higher than its
    #   nominal value by 1/(1-taxRate). This component is the grossup value. 
    #   Note that this effect is already included for the ITC when financial
    #   multipliers are calculated.
    df_inv[['ptc_value_monetized', 'ptc_dur', 'ptc_value']] = df_inv[['ptc_value_monetized', 'ptc_dur', 'ptc_value']].fillna(0)
    df_inv['ptc_value_monetized_posttax'] = df_inv['ptc_value_monetized']*(1/(1-df_inv['tax_rate']))
    df_inv['ptc_grossup_value'] = df_inv['ptc_value']*(1/(1-df_inv['tax_rate']) - 1.0)

    
    # ptc_unit_value is the full present-value of the PTC over its duration (in pretax terms, after penalty of monetization is applied),
    # expressed in "unit" terms, in this case meaning this would be the value if a 1 MW generator was operated at CF=1 for one hour with no curtailment. 
    df_inv['ptc_unit_value'] = df_inv['ptc_value_monetized_posttax'] * ((1-(1/df_inv['d_real']**df_inv['ptc_dur']))/(df_inv['d_real']-1.0))
            
    return df_inv



#%% Export parameters for the model. General exporter for most, some need custom exporters. 
    
def inv_param_exporter(df, modeled_years, parameter, indices, file_name, output_dir):
    ''' 
    General exporter for investment parameters, to be used in the GAMS model. 
    
    Collapses parameter down to the indicated indices, throwing an error if 
        the parameter varied over another index that wasn't given. 
    Currently only exports the values during the modeled_years (as opposed to, 
        for example, averaging over the years associated with a solve year). 
    '''

    # For investment parameters we only care about modeled_year values 
    df = df[df['t'].isin(modeled_years)]
    
    df_param = df[indices+[parameter]].copy()
    df_param = df_param.drop_duplicates()
    
    df_check_size = df[indices].copy()
    df_check_size = df_check_size.drop_duplicates()
    
    if len(df_param) != len(df_check_size):
        print('Attempting to collapse parameter down, but it varies across a non-specified index\nParameter:', parameter)
        print('To debug, use df_param.duplicated(indices), pick something that is duplicated, then filter down to that\nin the larger df, looking for reasons why it would vary across the indices given.')
        sys.exit()

    df_param[parameter] = np.round(df_param[parameter], 6)
    df_param.to_csv(os.path.join(output_dir, '%s.csv' % file_name), index=False, header=False)
    
    
#%% Export parameters
    
def param_exporter(df, parameter, file_name, output_dir):
                   
    df[parameter] = np.round(df[parameter], 5)
    df.to_csv(os.path.join(output_dir, '%s.csv' % file_name), index=False, header=False)
    
    
#%%
def expand_GAMS_tech_groups(df):
    '''
    GAMS has a convention for expanding rows (e.g. upv_1*upv_10 is expanded to upv_1, upv_2, etc)
    This function expands a df with the same convention, for the instances where a file is ingested
    by both python and GAMS. 
    '''
    
    tech_groups = [group for group in df['i'] if '*' in group]
    
    for tech_group in tech_groups:
        tech_group_root = tech_group.split('*')[0]
        tech_group_root = tech_group_root[:[pos for pos, char in enumerate(tech_group_root) if char == '_'][-1]]
        tech_group_n = int(tech_group.split('_')[-1])
        techs = ['%s_%s' % (tech_group_root, num) for num in np.arange(1,tech_group_n+1)]
        

        df_subset = df[df['i']==tech_group] # Extract the tech group from the main df
        df = df[df['i'] != tech_group] # Drop the tech group from the main df
        
        df_list = []
        
        for tech in techs:
            df_expanded_single = df_subset.copy()
            df_expanded_single['i'] = tech
            df_list = df_list + [df_expanded_single]
            
        df = pd.concat([df]+df_list, ignore_index=True)
        
    return df