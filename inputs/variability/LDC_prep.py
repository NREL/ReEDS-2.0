
import argparse
import os
import gdxpds
import pandas as pd
import numpy as np

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="""Create run-specific pickle files for the ReEDS-2.0 CV script""")
    
    # Mandatory arguments
    parser.add_argument("filename", help="""Filename of the LDC_static_inputs file used for this ReEDS run""", type=str)
    parser.add_argument("scenario", help="""Scenario name""", type=str)
    parser.add_argument("basedir", help="""Base directory for all batch runs""", type=str)
    parser.add_argument("csp_configs", help="""Number of CSP configurations for this run""", type=str)
    
    args = parser.parse_args()

    # Get the scenario name
    scenario = args.scenario
    
    # Get the static input switch
    static_inputs = args.filename

    basedir = args.basedir
    
    configs = int(args.csp_configs)
    
    # -------- Define the file paths --------
    
    path_variability = os.path.join(basedir,'inputs','variability')
    
    
    # -------- Get spatial mappers --------
    
    # Read in the gdx file
    gdxin = gdxpds.to_dataframes(os.path.join('inputs_case','LDC_prep.gdx'))
    
    # BAs present in the current run
    BAs_true = gdxin['rfeas']
    BAs_true.columns = ['area','boolean']
    BAs_true = BAs_true.drop('boolean',1).sort_values('area').reset_index(drop=True)
    
    map_BAtoRTO = gdxin['r_rto']
    map_BAtoRTO.columns = ['area','rto','boolean']
    map_BAtoRTO = map_BAtoRTO[map_BAtoRTO['area'].isin(BAs_true['area'])].drop('boolean',1).sort_values('area').reset_index(drop=True)
    
    ### MODIFY THIS WHEN "SK" IS FINALLY REMOVED FROM THE RESOURCE REGIONS!!!
    map_BAtoWINDREG = gdxin['r_rs']
    map_BAtoWINDREG.columns = ['ba','area','boolean']
    map_BAtoWINDREG = map_BAtoWINDREG[map_BAtoWINDREG['ba'].isin(BAs_true['area'])]
    map_BAtoWINDREG = map_BAtoWINDREG[map_BAtoWINDREG['area']!='sk'].drop('boolean',1).sort_values(['ba','area']).reset_index(drop=True) 
    
    # Resource regions present in the current run
    ResReg_true = pd.concat([BAs_true,map_BAtoWINDREG],sort=False).drop('ba',1).reset_index(drop=True)  
    
    # Get technology subsets
    
    tech_table = pd.read_csv(os.path.join('inputs_case','tech-subset-table.csv')).set_index('Unnamed: 0',1)
    
    vre_utility = tech_table[tech_table['VRE_UTILITY']=='YES'].index.values.tolist()
    vre_dist = tech_table[tech_table['VRE_DISTRIBUTED']=='YES'].index.values.tolist()
    
    # Get load adjustment factors
    
    load_adj = pd.read_csv(os.path.join(path_variability,'hourly_load_adjustments.csv')).set_index('Index')
    load_adj_distribution = load_adj.loc['distloss','factor']
    load_adj_calibration = load_adj.loc['load_calibration','factor']
    load_adj_tieloss = load_adj.loc['tieloss','factor']
    
    #HANDLING STATIC INPUTS FOR THE FIRST SOLVE YEAR
    # Load
    #       - Filter out load profiles not included in this run
    #       - Scale load profiles by distribution loss factor and load calibration factor
    # Resources:
    #       - Filter out all resources not included in this run
    #       - Add the distributed PV resources
    # RECF: 
    #       - Add the distributed PV profiles
    #       - Filter out all resources not included in this run
    #       - Sort the columns in recf to be in the same order as the rows in resources
    #       - Scale distributed resource CF profiles by distribution loss factor and tiein loss factor
    # ------- Read in the static inputs for this run -------
    
    load_profiles = pd.read_pickle(os.path.join(path_variability,'{}_load.pkl'.format(static_inputs)))
    wind1 = pd.read_pickle(os.path.join(path_variability,'{}_wind1.pkl'.format(static_inputs)))
    wind2 = pd.read_pickle(os.path.join(path_variability,'{}_wind2.pkl'.format(static_inputs)))
    wind3 = pd.read_pickle(os.path.join(path_variability,'{}_wind3.pkl'.format(static_inputs)))
    wind4 = pd.read_pickle(os.path.join(path_variability,'{}_wind4.pkl'.format(static_inputs)))
    upv = pd.read_pickle(os.path.join(path_variability,'{}_upv.pkl'.format(static_inputs)))
    cspcf = pd.read_pickle(os.path.join(path_variability,'{}_csp.pkl'.format(static_inputs)))
    recf = pd.concat([wind1,wind2,wind3,wind4,upv],sort=False,axis=1)
    resources = pd.read_pickle(os.path.join(path_variability,'{}_resources.pkl.'.format(static_inputs)))
    distPVCF = pd.read_csv(os.path.join('inputs_case','distPVCF_hourly.csv')).rename(columns={'Unnamed: 0':'resource'})
    
    
    # ------- Performin load modifications -------
    
    # Filtering out load profiles not included in this run
    load_profiles = load_profiles[BAs_true['area']]
    
    # Adjusting load profiles by distribution loss factor and load calibration factor
    load_profiles.loc[:,:] = load_profiles.loc[:,:] * load_adj_distribution * load_adj_calibration
    
    
    # ------- Performing resource modifications -------
    
    # Getting all distpv resources and filtering out those not included in this run
    distPV_resources = pd.DataFrame(distPVCF['resource'])
    distPV_resources.loc[:,'tech'] = 'distpv'
    distPV_resources.loc[:,'area'] = distPV_resources.loc[:,'resource']
    distPV_resources.loc[:,'resource'] = distPV_resources.loc[:,'tech'] + '_' + distPV_resources.loc[:,'resource']
    distPV_resources = pd.merge(left=map_BAtoRTO, right=distPV_resources, on='area', how='left')
    
    # Adding distpv resources to resources
    resources = pd.concat([resources,distPV_resources], sort=False).reset_index(drop=True)
    
    
    # ------- Performing recf modifications -------
    
    # Adding the distpv profiles to recf
    distPVCF.loc[:,'resource'] = 'distpv_' + distPVCF.loc[:,'resource']
    
    # Resetting indices before merging to assure there are no issues in the merge
    distPVCF = distPVCF.set_index('resource').transpose().reset_index(drop=True)
    recf = recf.reset_index(drop=True)
    recf = pd.merge(left=recf, right=distPVCF, left_index=True, right_index=True)
    
    # Filtering out profiles of resources not included in this run and sorting to match the order of the rows in resources
    resources = resources[resources['area'].isin(ResReg_true['area'])]
    recf = recf[resources['resource']]        
    
    # Create a scaling matrix to scale the appropriate columns of recf by the appropriate adjustment facotrs
    index_dist = resources['tech'].isin(vre_dist).reset_index(drop=True)
    index_tiein = resources['tech'].isin(vre_utility).reset_index(drop=True)
    multiplier = pd.DataFrame(index=np.arange(0,len(resources),1))
    multiplier.loc[:,'scale_factor'] = 1.0
    multiplier.loc[index_dist,'scale_factor'] = multiplier.loc[index_dist,'scale_factor'] * load_adj_distribution
    multiplier.loc[index_tiein,'scale_factor'] = multiplier.loc[index_tiein,'scale_factor'] * load_adj_tieloss
    multiplier = multiplier.values
    multiplier = np.tile(multiplier.reshape(1,len(resources)), (len(load_profiles),1))
    
    # Scale the appropriate resource CF profiles
    recf = recf * multiplier
    
    # Set the column names for resources to match ReEDS-2.0
    resources.columns = ['r','i','rto','resource']
    
    # Format CSP resources
    csp_resources = pd.DataFrame(columns=['i','r','resource','rto'])
    csp_profiles = pd.DataFrame()
    
    get_csp_resources = pd.DataFrame(columns=['resource'])
    get_csp_resources['resource'] = cspcf.columns
    for i in range(0,len(get_csp_resources)):
        c, underscore, r = get_csp_resources.loc[i,'resource'].partition('_')
        get_csp_resources.loc[i,'area'] = r
        get_csp_resources.loc[i,'class'] =c
    get_csp_resources = pd.merge(left=get_csp_resources, right=map_BAtoWINDREG, on='area')
    get_csp_resources.rename(columns={'area':'r','ba':'area'},inplace=True)
    get_csp_resources = pd.merge(left=get_csp_resources, right=map_BAtoRTO, on='area').drop('area',1)
    
    for i in range(0,configs):
        temp_csp_resources = get_csp_resources.copy()
        temp_csp_resources.loc[:,'i'] = 'csp{}_'.format(str(i+1)) + temp_csp_resources.loc[:,'class']
        temp_csp_resources.drop('class',1,inplace=True)
        temp_csp_resources.loc[:,'resource'] = temp_csp_resources.loc[:,'i'] + '_' + temp_csp_resources.loc[:,'r']
        csp_resources = pd.concat([csp_resources,temp_csp_resources],sort=False).reset_index(drop=True)
        temp_cspcf = cspcf.copy()
    
        #filter csp columns in csp cf for those that contain have strings contained in resreg_true
        newcspcols = [col for col in temp_cspcf.columns if any(rs in col for rs in ResReg_true['area'])]
        temp_cspcf = temp_cspcf[newcspcols]
        temp_cspcf.columns = temp_csp_resources['resource']
        csp_profiles = pd.concat([csp_profiles,temp_cspcf],sort=False, axis=1)
    
    #%%
    # ------- Dump static data into pickle files for future years -------
    		
    load_profiles.to_pickle(os.path.join('inputs_case','load_{}.pkl'.format(scenario)))
    recf.to_pickle(os.path.join('inputs_case','recf_{}.pkl'.format(scenario)))
    resources.to_pickle(os.path.join('inputs_case','resources_{}.pkl'.format(scenario)))
    csp_profiles.to_pickle(os.path.join('inputs_case','csp_profiles_{}.pkl'.format(scenario)))
    csp_resources.to_pickle(os.path.join('inputs_case','csp_resources_{}.pkl'.format(scenario)))
