# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 10:17:40 2019

@author: afrazier
"""

import argparse
import os
import subprocess

if os.name == 'posix':
    os.environ['GAMS_DIR'] = os.path.dirname(subprocess.check_output(['which', 'gams'])).decode()

import gdxpds
import pandas as pd
import numpy as np

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="""Create run-specific pickle files for the ReEDS-2.0 CC script""")
    
    # Mandatory arguments
    parser.add_argument("filename", help="""Filename of the LDC_static_inputs file used for this ReEDS run""", type=str)
    parser.add_argument("scenario", help="""Scenario name""", type=str)
    parser.add_argument("casepath", help="""File path of augur data""")
 
    args = parser.parse_args()

    # Get the scenario name
    scenario = args.scenario
    
    # Get the static input switch
    load_input = args.filename
    
    # -------- Define the file paths --------
    user, runname = scenario.split('_')[0], scenario.split('_')[0] + '_' + scenario.split('_')[1]
    path_pickles = os.path.join(args.casepath, 'augur_data')
    path_static = os.path.join('D_Augur','LDCfiles')
    path_variability = os.path.join('A_Inputs','inputs','variability')
    if not os.path.exists(path_pickles): os.mkdir(path_pickles)
    
    # -------- Get spatial mappers --------
    
    # Read in the gdx file
    gdxin = gdxpds.to_dataframes(os.path.join(path_pickles,'pickle_prep.gdx'))
    
    # BAs present in the current run
    BAs_true = gdxin['rb']
    BAs_true.columns = ['area','boolean']
    BAs_true = BAs_true.drop('boolean',1).sort_values('area').reset_index(drop=True)
    
    map_BAtoregion = gdxin['r_region']
    map_BAtoregion.columns = ['area','region','boolean']
    map_BAtoregion = map_BAtoregion[map_BAtoregion['area'].isin(BAs_true['area'])].drop('boolean',1).sort_values('area').reset_index(drop=True)
    
    map_BAtoWINDREG = gdxin['r_rs']
    map_BAtoWINDREG.columns = ['ba','area','boolean']
    map_BAtoWINDREG = map_BAtoWINDREG[map_BAtoWINDREG['ba'].isin(BAs_true['area'])]
    map_BAtoWINDREG = map_BAtoWINDREG[map_BAtoWINDREG['area']!='sk'].drop('boolean',1).sort_values(['ba','area']).reset_index(drop=True) 
    
    # Resource regions present in the current run
    ResReg_true = pd.concat([BAs_true,map_BAtoWINDREG],sort=False).drop('ba',1).reset_index(drop=True)  
    
    # Get technology subsets
    
    tech_table = pd.read_csv(os.path.join('A_Inputs','inputs','generators','tech_subset_table.csv')).set_index('Unnamed: 0',1)
    
    vre_utility = tech_table[tech_table['VRE_UTILITY']=='YES'].index.values.tolist()
    vre_dist = tech_table[tech_table['VRE_DISTRIBUTED']=='YES'].index.values.tolist()
    
    # get load profiles

    load_profiles = pd.read_pickle(os.path.join(path_static,'{}_load.pkl'.format(load_input)))
    recf = pd.read_pickle(os.path.join(path_static,'India_8760_recf.pkl'))
    resources = pd.read_pickle(os.path.join(path_static,'India_8760_resources.pkl'))


    # ------- Performin load modifications -------
    
    # Filtering out load profiles not included in this run
    columns_to_keep = list(BAs_true['area'])
    columns_to_keep = ['Year'] + columns_to_keep

    load_profiles = load_profiles[columns_to_keep]

    # ------- Performing recf modifications -------
      
    # Resetting indices before merging to assure there are no issues in the merge
    recf = recf.reset_index(drop=True)
    
    # Filtering out profiles of resources not included in this run and sorting to match the order of the rows in resources
    resources = resources[resources['area'].isin(ResReg_true['area'])]
    recf = recf[resources['resource']]        
    

    # ------- Dump static data into pickle files for future years -------
    		
    load_profiles.to_pickle(os.path.join(path_pickles,'load_{}.pkl'.format(scenario)), protocol=4)
    recf.to_pickle(os.path.join(path_pickles,'recf_{}.pkl'.format(scenario)), protocol=4)
    resources.to_pickle(os.path.join(path_pickles,'resources_{}.pkl'.format(scenario)), protocol=4)