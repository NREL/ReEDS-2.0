import pandas as pd
import os
import csv
import support_functions as sFuncs
# Time the operation of this script
from ticker import toc
import datetime

def calc_financial_inputs(batch, case, switches):
    """
    Write the following files to runs/{batch_case}/inputs_case/:
    - ivt.csv
    - ptc_values.csv
    - itc_fractions.csv
    - regions.csv
    - depreciation_schedules.csv
    - inflation.csv
    - valid_ba_list.csv
    - valid_regions_list.csv
    - cap_cost_mult.csv
    - cap_cost_mult_noITC.csv
    - cap_cost_mult_for_ratebase.csv
    - ptc_unit_value.csv
    - crf.csv
    - pvf_onm_int.csv
    - pvf_cap.csv
    - retail_cap_cost_mult.pkl
    - retail_eval_period.pkl
    - retail_depreciation_sch.pkl
    """
    print('Starting calculation of financial parameters for',case)
    tic = datetime.datetime.now()
 
    #%% Input processing
    input_dir = os.path.join('inputs')
    output_dir = os.path.join('runs', '%s_%s' % (batch, case), 'inputs_case')
    switches['endyear'] = int(switches['endyear'])
    switches['sys_eval_years'] = int(switches['sys_eval_years'])

    #%% Import some general data and maps
    
    # Import inflation (which includes both historical and future inflation). 
    # Used for adjusting currency inputs to the specified dollar year, and financial calculations. 
    inflation_df = pd.read_csv(os.path.join(
        input_dir, 'inflation', 'inflation_%s.csv' % switches['inflation_suffix']))

    # Import tech groups. Used to expand data inputs 
    # (e.g., 'UPV' expands to all of the upv subclasses, like upv_1, upv_2, etc)
    tech_groups = sFuncs.import_tech_groups(os.path.join('inputs', 'tech-subset-table.csv'))
    
    # Set up scen_settings object
    scen_settings = sFuncs.scen_settings(
        dollar_year=int(switches['dollar_year']), tech_groups=tech_groups, input_dir=input_dir,
        switches=switches)
    
    #%% Extend ivt if necessary
    ### (similar functionality for other inputs is in input_processing/forecast.py)
    ivt = pd.read_csv(os.path.join(
        input_dir, 'userinput', 'ivt_%s.csv' % switches['ivt_suffix']), index_col=0)
    ivt_step = pd.read_csv(os.path.join(input_dir, 'userinput', 'ivt_step.csv'), 
                           index_col=0, squeeze=True)
    lastdatayear = max([int(c) for c in ivt.columns])
    addyears = list(range(lastdatayear + 1, switches['endyear'] + 1))
    num_added_years = len(addyears)
    ### Add v for the extra years
    ivt_add = {}
    for i in ivt.index:
        vlast = ivt.loc[i,str(lastdatayear)]
        if ivt_step[i] == 0:
            ### Use the same v forever
            ivt_add[i] = [vlast] * num_added_years
        else:
            ### Use the same spacing forever
            forever = [[vlast + 1 + x] * ivt_step[i] for x in range(1000)]
            forever = [item for sublist in forever for item in sublist]
            ivt_add[i] = forever[:num_added_years]
    ivt_add = pd.DataFrame(ivt_add, index=addyears).T
    ### Concat and resave
    ivtout = pd.concat([ivt, ivt_add], axis=1)
    ivtout.to_csv(os.path.join(output_dir, 'ivt.csv'))
    ### Get numclass, which is used in b_inputs.gms
    numclass = ivtout.max().max()

    
    #%% Ingest data, determine what regions have been specified, and build df_inv and df_gen_pol
    # df_inv is a df for investment-related parameters (e.g. capital cost multipliers)
    # df_gen_pol is a df for generation-policy-related parameters (e.g. present value factors)

    techs = pd.read_csv(os.path.join(input_dir, 'techs', 'techs_%s.csv' % switches['techs_suffix']))
    ivt_df = pd.read_csv(os.path.join(output_dir, 'ivt.csv'))

    annual_degrade = pd.read_csv(
        os.path.join(input_dir,'degradation','degradation_annual_%s.csv' % switches['degrade_suffix']),
        header=None, names=['i','annual_degradation'])
    ### Assign the PV+battery values to values for standalone batteries
    annual_degrade = sFuncs.append_pvb_parameters(
        dfin=annual_degrade, 
        tech_to_copy='battery_{}'.format(scen_settings.switches['GSw_PVB_Dur']))
    
    years, modeled_years, year_map = sFuncs.ingest_years(
        switches['yearset_suffix'], switches['sys_eval_years'], switches['endyear'])
    regions, valid_ba_list, valid_regions_list = sFuncs.ingest_regions(
        switches['regions_suffix'], switches['region_type'], switches['GSw_region'], scen_settings)
    
    df_inv = sFuncs.build_dfs(years, techs, regions, ivt_df, year_map, switches['GSw_region'])
    print('df_inv created for', case)
    
    
    #%% Import and merge data onto df_inv and df_gen_pol
    
    # Import system-wide real discount rates, calculate present-value-factors, merge onto df's
    financials_sys = sFuncs.import_sys_financials(
        switches['financials_sys_suffix'], inflation_df, modeled_years, 
        years, year_map, switches['sys_eval_years'], scen_settings)
    df_inv = df_inv.merge(
        financials_sys[['t', 'pvf_capital', 'crf', 'd_real', 'd_nom', 'interest_rate_nom', 
                        'tax_rate', 'debt_fraction', 'rroe_nom']], 
        on=['t'], how='left')
    
    # Merge inflation into investment df
    df_inv = df_inv.merge(inflation_df, on=['t'], how='left', )
    
    #Merge annual degradation into investment df
    
    df_inv = df_inv.merge(annual_degrade, on=['i'], how='left')
    df_inv['annual_degradation'] = df_inv['annual_degradation'].fillna(0.0)
    
    # Import financial assumptions
    financials_tech = sFuncs.import_data(
        file_root='financials_tech', file_suffix=switches['financials_tech_suffix'], 
        indices=['i','country','t'], scen_settings=scen_settings)
    # Apply the values for standalone batteries to PV+B batteries
    financials_tech = sFuncs.append_pvb_parameters(
        dfin=financials_tech, 
        tech_to_copy='battery_{}'.format(scen_settings.switches['GSw_PVB_Dur']))
    # If the battery in PV+B gets the ITC, it gets 5-year MACRS depreciation as well
    if float(scen_settings.switches['GSw_PVB_ITC_Qual_Award']) >= 0.75:
        financials_tech.loc[
            financials_tech.i.str.startswith('pvb') & (financials_tech.country == 'usa'),
            'depreciation_sch'
        ] = 5
    # Project financials_tech forward
    financials_tech_projected = financials_tech.pivot(
        index=['i','country','depreciation_sch','eval_period','construction_sch'], 
        columns=['t'])['finance_diff_real']
    lastdatayear = max(financials_tech_projected.columns)
    for addyear in range(lastdatayear+1, switches['endyear']+1):
        financials_tech_projected[addyear] = financials_tech_projected[lastdatayear]
    # Overwrite with projected values
    financials_tech = financials_tech_projected.stack().rename('finance_diff_real').reset_index()
    # Merge with df_inv
    df_inv = df_inv.merge(financials_tech, on=['i', 't', 'country'], how='left')
        
    # Import incentives, shift eligibility by construction times, merge incentives
    incentive_df = sFuncs.import_and_mod_incentives(
        incentive_file_suffix=switches['incentives_suffix'], 
        construction_times_suffix=switches['construction_times_suffix'],
        ivt_df=ivt_df, years=years, sys_financials=financials_sys, 
        inflation_df=inflation_df, scen_settings=scen_settings)
    df_inv = df_inv.merge(incentive_df, on=['i', 't', 'country'], how='left')
    
    # Import schedules for financial calculations
    construction_schedules = pd.read_csv(os.path.join(
        input_dir, 'construction_schedules', 
        'construction_schedules_%s.csv' % switches['construction_schedules_suffix']))
    depreciation_schedules = pd.read_csv(os.path.join(
        input_dir, 'depreciation_schedules', 
        'depreciation_schedules_%s.csv' % switches['depreciation_schedules_suffix']))
    
    # Perform derivative financial calculations
    print('Calculating financial multipliers for', case, '...')
    df_inv = sFuncs.calc_financial_multipliers(
        df_inv, construction_schedules, depreciation_schedules, switches['timetype'])
    
    # Calculate the "unit value" of the PTC
    df_inv = sFuncs.calc_ptc_unit_value(df_inv)
        
    # Import regional capital cost multipliers, create multipliers for csp configurations
    reg_cap_cost_mult = sFuncs.import_data(
        file_root='reg_cap_cost_mult', file_suffix=switches['reg_cap_cost_mult_suffix'], 
        indices=['i','r'], scen_settings=scen_settings)
    # Apply the values for standalone batteries to PV+B batteries
    reg_cap_cost_mult = sFuncs.append_pvb_parameters(
        dfin=reg_cap_cost_mult, 
        tech_to_copy='battery_{}'.format(scen_settings.switches['GSw_PVB_Dur']))

    reg_cap_cost_mult_csp = reg_cap_cost_mult[reg_cap_cost_mult['i'].str.contains('csp1_')].copy()
    # Read in techs subset table to determine number of csp configurations
    tech_subset_table = pd.read_csv(os.path.join('inputs', 'tech-subset-table.csv'))
    csp_configs =  int(len(tech_subset_table.query('CSP == "YES" and STORAGE == "YES"')))
    del tech_subset_table
    for i in range(2, csp_configs + 1):
        configuration = 'csp' + str(i)
        mult_temp = reg_cap_cost_mult_csp.copy()
        mult_temp['i'] = mult_temp.i.replace({'csp1':configuration}, regex=True)
        reg_cap_cost_mult = reg_cap_cost_mult.append(mult_temp)
        del mult_temp
    del reg_cap_cost_mult_csp

    # Merge regional capital cost multipliers, calculate final capital cost multipliers
    df_inv = df_inv.merge(reg_cap_cost_mult, on=['i', 'r'], how='left')
    
    # Calculate the final capital cost multiplier
    df_inv['cap_cost_mult'] = df_inv['reg_cap_cost_mult'] * df_inv['finMult'] * df_inv['financing_risk_mult']
    df_inv['cap_cost_mult_noITC'] = df_inv['reg_cap_cost_mult'] * df_inv['finMult_noITC'] * df_inv['financing_risk_mult']
    # This is for the actual capital expenditures. Not adjusted for any tax incentives (depreciation or ITC). 
    df_inv['cap_cost_mult_for_ratebase'] = df_inv['CCmult'] * df_inv['reg_cap_cost_mult']
    
    
    #%% Before writing outputs, change "x" to "newx" in [v]
    df_inv['v'] = ['new%s' % v for v in df_inv['v']]
    
    
    #%% Write the scenario-specific output files
    sFuncs.inv_param_exporter(
        df_inv, modeled_years, 'cap_cost_mult', ['i', 'r', 't'], 
        'cap_cost_mult', output_dir)
    sFuncs.inv_param_exporter(
        df_inv, modeled_years, 'cap_cost_mult_noITC', ['i', 'r', 't'], 
        'cap_cost_mult_noITC', output_dir)
    sFuncs.inv_param_exporter(
        df_inv, modeled_years, 'cap_cost_mult_for_ratebase', ['i', 'r', 't'], 
        'cap_cost_mult_for_ratebase', output_dir)
    
    # Select the PTC unit value for each modeled year. This will select the PTC with the highest "unit value",
    # (if there are PTC's of different levels or some years without a PTC). This is a slight disconnect, because
    # ReEDS is nominally only actually building things in the actual solve year, but this disconnect outweighs
    # not having a PTC over a whole window because one was not available on the specific solve year
    ptc_unit_value = df_inv[['i','v','r','modeled_year','ptc_unit_value', 'ptc_value', 'ptc_grossup_value', 'ptc_dur']].copy()
    ptc_unit_value[['ptc_unit_value']] = ptc_unit_value[['ptc_unit_value']].fillna(0)
    ptc_unit_value = ptc_unit_value[ptc_unit_value['ptc_unit_value']!=0]
    ptc_unit_value = ptc_unit_value.sort_values(
        'ptc_unit_value', ascending=False).drop_duplicates(['i','v','r','modeled_year'], keep='first')
    ptc_unit_value = ptc_unit_value.reset_index()
    ptc_unit_value = ptc_unit_value.rename(columns={'modeled_year':'t'})
    sFuncs.param_exporter(
        ptc_unit_value[['i', 'v', 'r', 't', 'ptc_unit_value']], 
        'ptc_unit_value', 'ptc_unit_value', output_dir)
    
    # Write out the PTC's nominal value, grossup value, and duration. This is
    #   used in the retail rate module. 
    ptc_unit_value[['i', 'v', 'r', 't', 'ptc_value', 'ptc_grossup_value', 'ptc_dur']].to_csv(
        os.path.join(output_dir, 'ptc_values.csv'), index=False)
    
    # Write out the ITC fractions, for use in retail rate calculations
    itc_df = incentive_df[incentive_df['itc_frac']!=0]
    itc_df[['i', 'country', 't', 'itc_frac']].to_csv(os.path.join(output_dir, 'itc_fractions.csv'), index=False)


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
        
    # Copy input files into inputs_case
    regions.to_csv(os.path.join(output_dir, 'regions.csv'), index=False)
    depreciation_schedules.to_csv(os.path.join(output_dir, 'depreciation_schedules.csv'), index=False)
    inflation_df.to_csv(os.path.join(output_dir, 'inflation.csv'), index=False)
    
    # Output some values used in the retail rate module
    
    # This is for the actual capital expenditures. Not adjusted for any tax incentives (depreciation or ITC). 
    df_inv['cap_cost_mult_for_ratebase'] = df_inv['CCmult'] * df_inv['reg_cap_cost_mult']
    retail_cap_cost_mult = df_inv[['i', 't', 'r', 'cap_cost_mult_for_ratebase']].drop_duplicates(['i', 'r', 't'])
    retail_cap_cost_mult = retail_cap_cost_mult[retail_cap_cost_mult['cap_cost_mult_for_ratebase'].isnull()==False]
    retail_eval_period = df_inv[['i', 't', 'r', 'eval_period']].drop_duplicates(['i', 'r', 't'])
    retail_depreciation_sch = df_inv[['i', 't', 'r', 'depreciation_sch']].drop_duplicates(['i', 'r', 't'])

    retail_cap_cost_mult.to_csv(
        os.path.join(output_dir, 'retail_cap_cost_mult.csv.gz'), index=False)
    retail_eval_period.to_csv(
        os.path.join(output_dir, 'retail_eval_period.csv.gz'), index=False)
    retail_depreciation_sch.to_csv(
        os.path.join(output_dir, 'retail_depreciation_sch.csv.gz'), index=False)

        
    print('Finished calculation of financial parameters for',case)
    toc(tic=tic, year=0, process='input_processing/calc_financial_inputs.py', 
        path=os.path.join(output_dir,'..'))

    #%% Write a dictionary of the results
    finance_dict = {
        'numclass': numclass,
        'df_inv': df_inv,
        'financials_sys': financials_sys,
    }
    
    return finance_dict
