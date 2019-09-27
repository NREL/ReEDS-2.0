
import pandas as pd
import os
import csv
import support_functions as sFuncs


def calc_financial_inputs(batch, case, switches, return_results=False):
    print('Starting calculation of financial parameters for',case)
 
    input_dir = os.path.join('inputs')
    output_dir = os.path.join('runs', '%s_%s' % (batch, case), 'inputs_case')
    switches['endyear'] = int(switches['endyear'])
    switches['sys_eval_years'] = int(switches['sys_eval_years'])

    #%% Import some general data and maps
    
    # Import inflation (which includes both historical and future inflation). Used for adjusting currency inputs to the specified dollar year, and financial calculations. 
    inflation_df = pd.read_csv(os.path.join(input_dir, 'inflation', 'inflation_%s.csv' % switches['inflation_suffix']))

    # Import tech groups. Used to expand data inputs (e.g., 'UPV' expands to all of the upv subclasses, like upv_1, upv_2, etc)
    tech_groups = sFuncs.import_tech_groups(os.path.join('inputs', 'tech-subset-table.csv'))
    
    # Set up scen_settings object
    scen_settings = sFuncs.scen_settings(int(switches['dollar_year']), tech_groups, input_dir)
    
    
#%% Ingest data, determine what regions have been specified, and build df_inv and df_gen_pol
    # df_inv is a df for investment-related parameters (e.g. capital cost multipliers)
    # df_gen_pol is a df for generation-policy-related parameters (e.g. present value factors)

    techs = pd.read_csv(os.path.join(input_dir, 'techs', 'techs_%s.csv' % switches['techs_suffix']))
    ivt_df = pd.read_csv(os.path.join(input_dir, 'userinput', 'ict.csv'))
    years, modeled_years, year_map = sFuncs.ingest_years(switches['yearset_suffix'], switches['sys_eval_years'], switches['endyear'])
    regions, valid_ba_list, valid_regions_list = sFuncs.ingest_regions(switches['regions_suffix'] , switches['region_type'] , switches['GSw_region'], scen_settings)
    
    df_inv = sFuncs.build_dfs(years, techs, regions, ivt_df, year_map, switches['GSw_region'])
    print('df_inv created for', case)
    
    
    #%% Import and merge data onto df_inv and df_gen_pol
    
    # Import system-wide real discount rates, calculate present-value-factors, merge onto df's
    financials_sys = sFuncs.import_sys_financials(switches['financials_sys_suffix'], inflation_df, modeled_years, years, year_map, switches['sys_eval_years'], scen_settings)
    df_inv = df_inv.merge(financials_sys[['t', 'pvf_capital', 'crf', 'd_real', 'd_nom', 'interest_rate_nom', 'tax_rate', 'debt_fraction', 'rroe_nom']], on=['t'], how='left')
    
    # Merge inflation into investment df
    df_inv = df_inv.merge(inflation_df, on=['t'], how='left')
    
    # Import and merge financial assumptions
    financials_tech = sFuncs.import_data('financials_tech', switches['financials_tech_suffix'], ['i','country','t'], scen_settings=scen_settings)
    df_inv = df_inv.merge(financials_tech, on=['i', 't', 'country'], how='left')
        
    # Import incentives, shift eligibility by construction times, merge incentives
    incentive_df = sFuncs.import_and_mod_incentives(switches['incentives_suffix'], switches['construction_times_suffix'],
                                                                          ivt_df, years, financials_sys, inflation_df, scen_settings)
    df_inv = df_inv.merge(incentive_df, on=['i', 't', 'country'], how='left')
    
    # Import schedules for financial calculations
    construction_schedules = pd.read_csv(os.path.join(input_dir, 'construction_schedules', 'construction_schedules_%s.csv' % switches['construction_schedules_suffix']))
    depreciation_schedules = pd.read_csv(os.path.join(input_dir, 'depreciation_schedules', 'depreciation_schedules_%s.csv' % switches['depreciation_schedules_suffix']))
    
    # Perform derivative financial calculations
    print('Calculating financial multipliers for', case, '...')
    df_inv = sFuncs.calc_financial_multipliers(df_inv, construction_schedules, depreciation_schedules)
    
    # Calculate the "unit value" of the PTC
    df_inv = sFuncs.calc_ptc_unit_value(df_inv)
        
    # Import and merge regional capital cost multipliers, calculate final capital cost multipliers
    reg_cap_cost_mult = sFuncs.import_data('reg_cap_cost_mult', switches['reg_cap_cost_mult_suffix'], ['i','r'], scen_settings=scen_settings)
    df_inv = df_inv.merge(reg_cap_cost_mult, on=['i', 'r'], how='left')
    
    # Calculate the final capital cost multiplier
    df_inv['cap_cost_mult'] = df_inv['reg_cap_cost_mult'] * df_inv['finMult'] * df_inv['financing_risk_mult']
    df_inv['cap_cost_mult_noITC'] = df_inv['reg_cap_cost_mult'] * df_inv['finMult_noITC'] * df_inv['financing_risk_mult']
    
    
    
    #%% Before writing outputs, change "x" to "newx" in [v]
    df_inv['v'] = ['new%s' % v for v in df_inv['v']]
    
    
    #%% Write the scenario-specific output files
    df_inv.to_pickle(os.path.join(output_dir, 'df_inv.pkl'))
    sFuncs.inv_param_exporter(df_inv, modeled_years, 'cap_cost_mult', ['i', 'r', 't'], 'cap_cost_mult', output_dir)
    sFuncs.inv_param_exporter(df_inv, modeled_years, 'cap_cost_mult_noITC', ['i', 'r', 't'], 'cap_cost_mult_noITC', output_dir)
    
    # Select the PTC unit value for each modeled year. This will select the PTC with the highest "unit value",
    # (if there are PTC's of different levels or some years without a PTC). This is a slight disconnect, because
    # ReEDS is nominally only actually building things in the actual solve year, but this disconnect outweighs
    # not having a PTC over a whole window because one was not available on the specific solve year
    ptc_unit_value = df_inv[['i','v','r','modeled_year','ptc_unit_value']].copy()
    ptc_unit_value[['ptc_unit_value']] = ptc_unit_value[['ptc_unit_value']].fillna(0)
    ptc_unit_value = ptc_unit_value[ptc_unit_value['ptc_unit_value']!=0]
    ptc_unit_value = ptc_unit_value.groupby(by=['i','v','r','modeled_year']).max()
    ptc_unit_value = ptc_unit_value.reset_index()
    ptc_unit_value = ptc_unit_value.rename(columns={'modeled_year':'t'})
    sFuncs.param_exporter(ptc_unit_value[['i', 'v', 'r', 't', 'ptc_unit_value']], 'ptc_unit_value', 'ptc_unit_value', output_dir)


    # CRF used in sequential case for calculating pvf_onm values (pvf)
    crf_df = financials_sys[financials_sys['t']==financials_sys['modeled_year']].copy()
    sFuncs.param_exporter(crf_df[['t', 'crf']], 'crf', 'crf', output_dir)

        
    # pvf_onm used in intertemporal
    pvf_onm_int = financials_sys[['modeled_year', 'pvf_onm']].groupby(by=['modeled_year']).sum()
    pvf_onm_int = pvf_onm_int.reset_index()
    pvf_onm_int = pvf_onm_int.rename(columns={'modeled_year':'t'})
    sFuncs.param_exporter(pvf_onm_int, 'pvf_onm', 'pvf_onm_int', output_dir)


    # pvf_cap (used in both seq and int modes)
    sFuncs.inv_param_exporter(df_inv, modeled_years, 'pvf_capital', ['t'], 'pvf_cap', output_dir)
    
    
    # Export valid region lists
    with open(os.path.join(output_dir, 'valid_ba_list.csv'), 'w') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(valid_ba_list)
    
    with open(os.path.join(output_dir, 'valid_regions_list.csv'), 'w') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(valid_regions_list)


        
    print('Finished calculation of financial parameters for',case)

    #%% If specified, write a dictionary of any results. Useful for debugging.     
    if return_results==True:
        results_dict = {'df_inv':df_inv,
                        'financials_sys':financials_sys,
                        }
        
        return results_dict

    
