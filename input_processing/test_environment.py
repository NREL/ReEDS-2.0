
import os

os.chdir('.') # Set the current working directory to the location of the script, to load cFuncs
import calc_financial_inputs as cFuncs
os.chdir('..') # Set the current working directory to be one lower then the current folder, so it is called from the same place that runbatch would be


batch = 'test_environment'
case = 'test'
switches = dict({'region_type':'country',
                 'GSw_region':'usa',
                 'depreciation_schedules_suffix':'default',
                 'dollar_year':2004,
                 'financials_tech_suffix':'ATB2019_mid',
                 'inflation_suffix':'default',
                 'incentives_suffix':'annual',
                 'inflation':1.025,
                 'reg_cap_cost_mult_suffix':'default',
                 'regions_suffix':'default',
                 'techs_suffix':'subsetForTesting',
                 'yearset_suffix':'default',
                 'construction_times_suffix':'default',
                 'construction_schedules_suffix':'default',
                 'financials_sys_suffix':'ATB2019',
                 'sys_eval_years':20, 
                 'endyear':2050,
                 'timetype':'seq',
                 'degrade_suffix':'default'})

# Create a runs directory, if it doesn't exist
if os.path.isdir('runs') == False:
    os.mkdir('runs')

# Create a test_environment directory in the runs directory, if it doesn't exist
if os.path.isdir(os.path.join('runs', '%s_%s' % (batch, case))) == False:
    os.mkdir(os.path.join('runs', '%s_%s' % (batch, case)))
    os.mkdir(os.path.join('runs', '%s_%s' % (batch, case), 'inputs_case'))


# Extract some objects from the results dictionary, for manual examination. 
results_dict = cFuncs.calc_financial_inputs(batch, case, switches, return_results=True)
df_inv = results_dict['df_inv']
financials_sys = results_dict['financials_sys']


#%% Scratch area
