# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:30:25 2020
@author: afrazier
This is the driving script for the ReEDS Augur module. It is called directly from
the command line after every ReEDS solve. It calls a series of files in a specific
order and writes its results to a gdx file that are then read back in to ReEDS.
These results include:
    - surpold
        -- curtailment from existing resources
    - MRsurplusmarginal
        -- curtailment from existing resources after an adjustment to baseload power
    - surplusmarginal
        -- curtailment rates for marginal resources
    - stor_in
        -- the amount of storage charging in Osprey. ReEDS must charge storage at least this much
    - storage_pv
        -- the fraction of storage charging that can come from otherwise curtailed PV generation
    - storage_wind
        -- the fraction of storage charging that can come from otherwise curtailed wind generation
    - storage_other
        -- the fraction of marginal storage charging that can come from existing curtailment
    - storage_revenue
        -- The energy arbitrage revenue for marginal storage
    - season_all_cc
        -- capacity credit of existing resources by season
    - season_timeslice_hours_all
        -- the fraction of top hours used for CC calculations that occur in each timeslice
    - season_all_cc_mar
        -- marginal capacity credit of VRE
    - season_peaking_stor_all
        -- the potential for all modeled durations of storage to serve peak demand
See the augur_data folder for data files:
    - reeds_data_{scenario}_{year}.gdx
        -- This file contains the data from ReEDS needed in the Augur module
    - D_Augur_{scenario}_{year}.gdx
        -- This file contains the results from the Augur module
See the ErrorFile folder if any errors occur in the Augur module. If any errors occurred, 
a txt file will appear here with the error logged.
"""
#%%
import os
import time
import logging
import traceback
import argparse
import subprocess

if os.name == 'posix':
    os.environ['GAMS_DIR'] = os.path.dirname(subprocess.check_output(['which', 'gams'])).decode()

import gdxpds
import pandas as pd
import pathlib
from d1_prep_data import prep_data
from d4_process_osprey_results import process_osprey_results
from d5_existing_curtailment import existing_curtailment
from d6_marginal_curtailment import marginal_curtailment
from d7_condor import get_marginal_storage_value
from d8_capacity_credit import reeds_cc
from utilities import delete_csvs
#%%
def ReEDS_augur(args):
    
# RUN SCRIPTS
    
    ##############################
#%% # ReEDS data dump
    ##############################
    if args['data_dump'] and args['timetype'] != 'seq':
        if os.name!="posix":
            print('\n##############################')
            print('dumping ReEDS data...')
            print('\n##############################')
        subprocess.call(['gams', os.path.join('C_Solve','c3_augur_data_dump.gms'),
                         'o='+os.path.join(args['data_dir'],'..','lstfiles','data_dump.lst'),
                         'logOption='+args['log_option'],
                         'logfile=gamslog.txt',
                         'appendLog=1',
                         'r='+os.path.join(args['data_dir'],'..','g00files','{}.g00'.format(args['g00'])),
                         '--case='+args['scenario'],
                         '--cur_year='+str(args['year']),
                         '--next_year='+str(args['next_year']),
                         '--timetype='+args['timetype'],
                         '--data_dir='+args['data_dir']
                         ], 
                         cwd=os.getcwd())
    else:
        if os.name!="posix":
            print('skipping data dump...')
            time.sleep(args['sleep_time'])
    
    ##############################
#%% # d1_prep_data
    ##############################

    if args['prep_data']:
        if os.name!="posix":
            print('\n##############################')
            print('ReEDS Augur: d1_prep_data')
            print('##############################\n')
        osprey_inputs, curt_data, marg_curt_data, condor_data, reeds_cc_data = prep_data(args)
    else:
        if os.name!="posix":
            print('skipping data prep...')
            time.sleep(args['sleep_time'])
    
    ##############################
#%% # d2_Osprey
    ##############################
    
    if args['osprey']:
        if os.name!="posix":
            print('\n##############################')
            print('ReEDS Augur: d2_Osprey')
            print('##############################\n')
        subprocess.call(['gams', os.path.join('D_Augur','d2_osprey'),
                         'o='+os.path.join(args['data_dir'],'..','lstfiles','osprey_{}.lst'.format(args['tag'])),
                         'logOption='+args['log_option'], 
                         'logfile=gamslog.txt',
                         'appendLog=1',
                         '--case='+args['scenario'],
                         '--next_year='+str(args['next_year']),
                         '--data_dir='+args['data_dir']
                         ], cwd=os.getcwd())
    else:
        if os.name!="posix":
            print('skipping Osprey...')
            time.sleep(args['sleep_time'])
    
    ##############################
    # d3_gdx_dump
    ##############################

    if args['gdx_dump']:
        if os.name!="posix":
            print('\n##############################')
            print('ReEDS Augur: d3_gdx_dump')
            print('##############################\n')
        subprocess.call(['gams', os.path.join('D_Augur','d3_gdx_dump'),
                         '--case='+args['scenario'],
                         '--next_year='+str(args['next_year']),
                         '--data_dir='+args['data_dir']
                         ], cwd=os.getcwd())
    else:
        if os.name!="posix":
            print('skipping Osprey csv output...')
            time.sleep(args['sleep_time'])
#%% 
    ##############################
    # d4_process_osprey_results
    ##############################
        
    if args['process_osprey_results']:
        if os.name!="posix":
            print('\n##############################')
            print('ReEDS Augur: d4_process_osprey_results')
            print('##############################\n')
        osprey_results = process_osprey_results(args, osprey_inputs)
    else:
        if os.name!="posix":
            print('skipping Osprey results processing...')
            time.sleep(args['sleep_time'])
 
    ##############################
    # d5_existing_curtailment
    ##############################

    if args['curtailment']:
        if os.name!="posix":
            print('\n##############################')
            print('ReEDS Augur: d5_existing_curtailment')
            print('##############################\n')
        curt_results, curt_reeds = existing_curtailment(args, curt_data, osprey_results)
    else:
        if os.name!="posix":
            print('skipping curtailment calculations...')
            time.sleep(args['sleep_time'])
    
    ##############################
    # d6_marginal_curtailment
    ##############################

    if args['marg_curt']:
        if os.name!="posix":
            print('\n##############################')
            print('ReEDS Augur: d6_marginal_curtailment')
            print('##############################\n')
        mc_results, trans_region_curt = marginal_curtailment(args, marg_curt_data, osprey_results, curt_results)
    else:
        if os.name!="posix":
            print('skipping marginal curtailment...')
            time.sleep(args['sleep_time'])
#%%    
    ##############################
    # d7_Condor
    ##############################

    if args['condor']:
        if os.name!="posix":
            print('\n##############################')
            print('ReEDS Augur: d7_Condor')
            print('##############################\n')
        condor_results = get_marginal_storage_value(args, condor_data, osprey_results, trans_region_curt)
    else:
        if os.name!="posix":
            print('skipping storage dispatch...')
            time.sleep(args['sleep_time'])
    
    ##############################
#%% # d8_capacity_credit
    ##############################

    if args['capacity_credit']:
        if os.name!="posix":
            print('\n##############################')
            print('ReEDS Augur: d8_capacity_credit')
            print('##############################\n')
        cc_results = reeds_cc(args, reeds_cc_data)
    else:
        if os.name!="posix":
            print('skipping capacity credit...')
            time.sleep(args['sleep_time'])
    
    ##############################
#%% # Write results to gdx file
    ##############################

    # delete csv files
    if args['remove_csv']:
        delete_csvs(args)
    
    # package results
    results = {**mc_results, **cc_results, **condor_results, **curt_reeds}
    
    # write gdx file
    gdxpds.to_gdx(results, os.path.join(args['data_dir'],'ReEDS_augur_{}.gdx'.format(args['tag'])))
  
    if os.name!="posix":
        print('\n\n\nReEDS Augur is all finished!')
        time.sleep(args['sleep_time'])
    #%%
    return None


#%%  MAIN

if __name__ == '__main__':
    
    # ------------------------------ PARSE ARGUMENTS ------------------------------
    
    parser = argparse.ArgumentParser(description="""Perform 8760 calculations on variable and energy constrained resources""")
    
    # Mandatory arguments
    parser.add_argument("scenario", help="""Scenario name""", default='Base', type=str)
    parser.add_argument("year", help="""Previous ReEDS solve year""", default=2030, type=int)
    parser.add_argument("next_year", help="""Upcoming ReEDS solve year""", default=2030, type=int)
    parser.add_argument("timetype", help="""ReEDS temporal solve method""", default='seq', type=str)
    parser.add_argument("iteration", help="""Iteration number for intertemporal and window solve""", default='0', type=str)
    parser.add_argument("casepath", help="""Path to case files""", default='', type=str)

    # Optional arguments: booleans to turn on/off scripts for debugging purposes
    parser.add_argument("-c3","--data_dump", help="""Switch to turn off data_dump. Default is true""", action="store_false")
    parser.add_argument("-d1","--prep_data", help="""Swtich to turn off prep_data. Default is true""", action="store_false")
    parser.add_argument("-d2","--osprey", help="""Swtich to turn off osprey. Default is true""", action="store_false")
    parser.add_argument("-d3","--gdx_dump", help="""Switch to turn off osprey csv outputs. Default is true""", action="store_false")
    parser.add_argument("-d4","--process_osprey_results", help="""Switch to turn off osprey results processing. Default is true""", action="store_false")
    parser.add_argument("-d5","--curtailment", help="""Switch to turn off curtailment calculation. Default is true""", action="store_false")
    parser.add_argument("-d6","--marg_curt", help="""Switch to turn off curtailment calculation. Default is true""", action="store_false")
    parser.add_argument("-d7","--condor", help="""Switch to turn off storage dispatch. Default is true""", action="store_false")
    parser.add_argument("-d8","--capacity_credit", help="""Switch to turn of capacity credit scrip. Default is true""", action="store_false")
    parser.add_argument("-rm","--remove_csv", help="""Switch to turn off the deletion of csv files. Default is true""", action="store_false")
    
    ReEDS_args = parser.parse_args()
    
    args = dict()
    for arg in vars(ReEDS_args):
        args[arg] = getattr(ReEDS_args, arg)
    
    args['reeds_path'] = pathlib.Path().resolve()
#%% DEBUG MODE
    if False:
        #os.chdir('D:\\pjoshi\ReEDS_UP\reeds_india_api')
        os.chdir(os.path.join('D:\\','pjoshi', 'ReEDS_UP', 'reeds_india_api'))
    # To debug in spyder, start here and adjust values as needed
    # If new arguments are added, you can test them in debug mode by adding them here
        args = dict()
        # Command line args
        args['scenario'] = 'PJTest1_UPPrescribedOff'
        args['casepath'] = os.path.join('E_Outputs', 'runs', 'PJTest1_UPPrescribedOff')
        args['year'] = 2022
        args['next_year'] = 2022
        args['timetype'] = 'int'
        args['iteration'] = '0'
        # Files to run
        args['data_dump'] = True
        args['prep_data'] = True
        args['osprey'] = True
        args['gdx_dump'] = True
        args['process_osprey_results'] = True
        args['curtailment'] = True
        args['marg_curt'] = True
        args['condor'] = True
        args['capacity_credit'] = True
        args['remove_csv'] = True
        args['reeds_path'] = pathlib.Path().resolve()

    defaults = pd.read_csv(os.path.join('D_Augur','value_defaults.csv'))
    for i in range(0,len(defaults)):
        key = defaults.loc[i,'key']
        value = defaults.loc[i,'value']
        dtype = defaults.loc[i,'dtype']
        if dtype == 'float':
            value = float(value)
        if dtype == 'int':
            value = int(value)
        if dtype == 'list':
            value = value.split(',')
        if dtype == 'boolean':
            if value == 'FALSE':
                value = bool(False)
            elif value == 'TRUE':
                value = bool(True)
        args[key] = value
    args['tag'] = args['scenario'] + '_' + str(args['next_year'])
    args['g00'] = args['scenario'] + '_' + str(args['iteration'])

    args['data_dir'] = os.path.join(args['casepath'], 'augur_data')
#%%
        
    # Preparing to log any errors if they occur
    path_errors = os.path.join('D_Augur', 'ErrorFile')
    if not os.path.exists(path_errors): os.mkdir(path_errors)
    errorfile = os.path.join(path_errors, 'ReEDS_augur_errors_{}_{}.txt'.format(args['scenario'],args['next_year']))
    logging.basicConfig(filename=errorfile, level=logging.ERROR)
    logger = logging.getLogger(__name__)
    
    # If an error occurs during the script write it to a txt file
    try:
        ReEDS_augur(args)
    except:
        logger.error('{}_{}'.format(args['scenario'], args['next_year']))
        logger.error(traceback.format_exc())
    # Removing the error file if it is empty
    logging.shutdown()
    if os.stat(errorfile).st_size == 0:
        os.remove(errorfile)      