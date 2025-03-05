# -*- coding: utf-8 -*-
"""
Code to process allowed shifting hours for demand response into
fraction of hours that can be shifted into each time slice
At some point, it may be nice to instead read in the actual DR
shifting potential and change to fraction of load that can be shifted
but haven't done that yet.

Created on Feb 24 2021
@author: bstoll
"""
#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================
import os
import sys
import argparse
import pandas as pd
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
# Time the operation of this script
tic = datetime.datetime.now()

#%%#################
### FIXED INPUTS ###

decimals = 4


#%% ===========================================================================
### --- MAIN FUNCTION ---
### ===========================================================================

if __name__ == '__main__':

    ### Parse arguments
    parser = argparse.ArgumentParser(description='This file produces the DR shiftability inputs')
    parser.add_argument('reeds_path', help='ReEDS directory')
    parser.add_argument('inputs_case', help='output directory')

    args = parser.parse_args()
    inputs_case = args.inputs_case
    reeds_path = args.reeds_path
    
    # Settings for testing
    # reeds_path = os.getcwd()
    # inputs_case = os.path.join(reeds_path,'runs','dr1_Pacific','inputs_case')

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )
    print('Starting writedrshift.py')

    #%% Inputs from switches
    sw = reeds.io.get_switches(inputs_case)

    val_r = pd.read_csv(
        os.path.join(inputs_case, 'val_r.csv'), header=None).squeeze(1).tolist()

    ### Read in DR shed for specified scenario
    dr_shed = pd.read_csv(
        os.path.join(inputs_case, 'dr_shed.csv'))
    dr_shed[['dr_type', 'yr_hrs']].to_csv(
        os.path.join(inputs_case, 'dr_shed.csv'), index=False, header=False)

    ### Create empty EVMC data files if GSw_EVMC == 0:
    evmc_files = [
        'evmc_shape_profile_decrease',
        'evmc_shape_profile_increase',
        'evmc_storage_profile_decrease',
        'evmc_storage_profile_increase',
        'evmc_storage_energy'
    ]
    for file in evmc_files:
        if int(sw['GSw_EVMC']):
            pass
        else:
            # Overwrite empty dataframes created in copy_files.py
            df = pd.DataFrame(columns=['i','hour','year']+val_r)
            df.to_csv(os.path.join(inputs_case,file+'.csv'),index=False)
    
    print('Finished writedrshift.py')

    reeds.log.toc(tic=tic, year=0, process='input_processing/writedrshift.py', 
        path=os.path.join(inputs_case,'..'))
