
import argparse
import os
import gdxpds
import pandas as pd
import numpy as np
import shutil
import logging
import traceback
#%%    

def hourly_prep(all_year_load,scenario,static_inputs,basedir):
#%%
    #Get the scenario name
#    scenario = "scenario"
#    static_inputs =  "multi_year"
#    basedir =  "D:\\Danny_ReEDS\\ReEDS-2.0"
#    all_year_load = "default"
#%%
    # -------- Check if using EFS ----------

    if all_year_load != 'default':
        static_inputs = 'single_year'

    # -------- Define the file paths --------
    
    path_variability = os.path.join(basedir,'inputs','variability')
    
    # -------- Datetime mapper --------
    
    hdtmap = pd.read_csv(os.path.join('inputs_case', 'h_dt_szn.csv'))
    if static_inputs == 'single_year':
        hdtmap = hdtmap[hdtmap.year == 2012]

    # -------- Get spatial mappers --------
    
    # Read in the gdx file
    gdxin = gdxpds.to_dataframes(os.path.join('inputs_case','LDC_prep.gdx'))
    
    # BAs present in the current run
    BAs_true = gdxin['rfeas']
    BAs_true.columns = ['area','boolean']
    BAs_true = BAs_true.drop('boolean',1).sort_values('area').reset_index(drop=True)
    
    map_BAtoCCREG = gdxin['r_ccreg']
    map_BAtoCCREG.columns = ['area','ccreg','boolean']
    map_BAtoCCREG = map_BAtoCCREG[map_BAtoCCREG['area'].isin(BAs_true['area'])].drop('boolean',1).sort_values('area').reset_index(drop=True)
    
    ### MODIFY THIS WHEN "SK" IS FINALLY REMOVED FROM THE RESOURCE REGIONS!!!
    map_BAtoWINDREG = gdxin['r_rs']
    map_BAtoWINDREG.columns = ['ba','area','boolean']
    map_BAtoWINDREG = map_BAtoWINDREG[map_BAtoWINDREG['ba'].isin(BAs_true['area'])]
    map_BAtoWINDREG = map_BAtoWINDREG[map_BAtoWINDREG['area']!='sk'].drop('boolean',1).sort_values(['ba','area']).reset_index(drop=True)
    
    map_WINDREGtoCCREG = pd.merge(left=map_BAtoWINDREG, right=map_BAtoCCREG.rename(columns={'area':'ba'}), on='ba', how='left')
    map_WINDREGtoCCREG = map_WINDREGtoCCREG.drop('ba',1).reset_index(drop=True)
    map_AREAtoCCREG = pd.concat([map_BAtoCCREG,map_WINDREGtoCCREG]).reset_index(drop=True)
    
    # Resource regions present in the current run
    ResReg_true = pd.concat([BAs_true,map_BAtoWINDREG],sort=False).drop('ba',1).reset_index(drop=True)  
    
    # Get technology subsets
    tech_table = pd.read_csv(os.path.join('inputs_case','tech-subset-table.csv')).set_index('Unnamed: 0',1)
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
    vre_utility = techs['VRE_UTILITY']
    vre_dist = techs['VRE_DISTRIBUTED']

    # Get number of csp configurations
    configs =  int(len(tech_table.query('CSP == "YES" and STORAGE == "YES"')))

    # Get load adjustment factors
    distloss = gdxin['distloss'].values[0][0]

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
    if(all_year_load=="default"):
        load_profiles = pd.read_csv(os.path.join(path_variability, static_inputs, 'load.csv.gz'), index_col=0, float_precision='round_trip')
    else:
        load_profiles = pd.read_csv(os.path.join(path_variability, 'EFS_Load', (all_year_load +'_load_hourly.csv.gz')), index_col=[0,1], float_precision='round_trip')
    df_windons = pd.read_csv(os.path.join(path_variability, static_inputs, 'wind-ons.csv.gz'), index_col=0, float_precision='round_trip')
    df_windons.columns = ['wind-ons_' + col for col in df_windons]
    df_windofs = pd.read_csv(os.path.join(path_variability, static_inputs, 'wind-ofs.csv.gz'), index_col=0, float_precision='round_trip')
    df_windofs.columns = ['wind-ofs_' + col for col in df_windofs]
    df_upv = pd.read_csv(os.path.join(path_variability, static_inputs, 'upv.csv.gz'), index_col=0, float_precision='round_trip')
    df_upv.columns = ['upv_' + col for col in df_upv]
    df_dupv = pd.read_csv(os.path.join(path_variability, static_inputs, 'dupv.csv.gz'), index_col=0, float_precision='round_trip')
    df_dupv.columns = ['dupv_' + col for col in df_dupv]
    cspcf = pd.read_csv(os.path.join(path_variability, static_inputs, 'csp.csv.gz'), index_col=0, float_precision='round_trip')
    recf = pd.concat([df_windons,df_windofs,df_upv,df_dupv],sort=False,axis=1)
    resources = pd.DataFrame({'resource':sorted(recf.columns)})
    resources['tech'] = [r.rsplit('_', 1)[0] for r in resources['resource']]
    resources['area'] = [r.rsplit('_', 1)[1] for r in resources['resource']]
    resources = resources[['area', 'tech', 'resource']]
        
    if static_inputs == 'multi_year':
        distPVCF = pd.read_csv(os.path.join('inputs_case','distPVCF.csv')).rename(columns={'Unnamed: 0':'resource'})
    else:
        distPVCF = pd.read_csv(os.path.join('inputs_case','distPVCF_hourly.csv')).rename(columns={'Unnamed: 0':'resource'})

    # ------- Performin load modifications -------
    if(all_year_load=='default'):

        #Importing timeslice hours for performing load scaling
        hours = pd.read_csv(os.path.join('inputs_case','numhours.csv'),header = None)
        hours.columns = ['h','numhours']
        hours.h = hours.h.str.upper()
        hours.index = hours.h
        
        #Prepare a dataframe for scaling the load profiles
        #Scaling is done using the annual 2010 timeslice load by BA
        load_TS_2010 = pd.read_csv(os.path.join('inputs_case','load_2010.csv'))
        load_TS_2010.index = load_TS_2010.r
        load_TS_2010 = load_TS_2010.drop('r',1)
        for i in load_TS_2010.columns:
            #Get total load in each timeslice and region
            load_TS_2010.loc[:,i] = load_TS_2010.loc[:,i] * hours.loc[i,'numhours']
        #Get annual load by region
        load_TS_2010_total = load_TS_2010.sum(1)
        
        regions = list(load_profiles.columns)
        load_profiles['year'] = list(hdtmap.year)
        #normalize load profiles with 2010 load timeslices
        for y in load_profiles.year.unique():
            for i in regions:
                load_profiles.loc[load_profiles.year==y,i] = load_profiles.loc[:,i][load_profiles.year == y] * (load_TS_2010_total.loc[i] / load_profiles.loc[:,i][load_profiles.year == y].sum())

    # Filtering out load profiles not included in this run
    load_profiles = load_profiles[BAs_true['area']]
    
    # Adjusting load profiles by distribution loss factor and load calibration factor
    load_profiles.loc[:,:] = load_profiles.loc[:,:] / (1 - distloss)
    
    
    # ------- Performing resource modifications -------
    
    # Getting all distpv resources and filtering out those not included in this run
    distPV_resources = pd.DataFrame(distPVCF['resource'])
    distPV_resources.loc[:,'tech'] = 'distpv'
    distPV_resources.loc[:,'area'] = distPV_resources.loc[:,'resource']
    distPV_resources.loc[:,'resource'] = distPV_resources.loc[:,'tech'] + '_' + distPV_resources.loc[:,'resource']
    
    # Adding distpv resources to resources
    resources = pd.concat([resources,distPV_resources], sort=False).reset_index(drop=True)
    
    
    # ------- Performing recf modifications -------
    
    # There is only one year of data for distpv
    # Create multi year distpv profiles by scaling dupv profiles
    if static_inputs == 'multi_year':
        # Subset dupv resources
        dupv_resource = ['dupv_' + str(n) for n in range(1,11)]
        resource_temp = resources[resources['tech'].isin(dupv_resource)].reset_index(drop=True)
        missing_dupv_bas = resources[~(resources.area.isin(resource_temp.area)) & (resources.tech.str.contains('upv'))].drop_duplicates(subset = 'area',keep = 'last') # Missing several BA's to scale by dupv; use upv instead
        resource_temp = resource_temp.drop_duplicates(subset=['area'], keep='last')
        resource_temp = pd.concat([resource_temp,missing_dupv_bas])
        resource_temp.sort_values('resource', inplace=True)
        
        # Grab the resource profiles for each region to be scaled 
        distpv_profiles = recf[resource_temp['resource'].tolist()]
        distpv_profiles.columns = resource_temp['area'].tolist()

        # Aggregate to timeslices for scaling
        distpv_profiles.index = hdtmap['h']
        distpv_timeslice_cf = distpv_profiles.groupby('h').mean().transpose()

        distPVCF.drop('H17', 1, inplace=True)
        distPVCF.set_index('resource', inplace=True)
        distPVCF.columns = ['h' + str(n) for n in range(1, 17)]
        # Create and apply scaling factor for each timeslice
        temp_scaling_factor = distPVCF / distpv_timeslice_cf
        temp_scaling_factor = temp_scaling_factor.fillna(0)
        temp_scaling_factor.replace(np.inf, 0, inplace=True)
        temp_scaling_factor = temp_scaling_factor.transpose().reset_index().rename(columns={'index':'h'})
        temp_scaling_factor = pd.merge(left=pd.DataFrame(hdtmap['h']), right=temp_scaling_factor, on='h', how='left').set_index('h')
        distpv_profiles *= temp_scaling_factor
        distpv_profiles = distpv_profiles.clip(upper=1.0) # Capacity factor must be < 1
        distpv_cols = distpv_profiles.columns.tolist()
        distpv_cols.sort()
        distpv_profiles = distpv_profiles[distpv_cols]
        distpv_cols_rename = ['distpv_' + col for col in distpv_cols]
        distpv_profiles.columns = distpv_cols_rename
        distpv_profiles = distpv_profiles.reset_index(drop=True)
    else:
        distPVCF.loc[:,'resource'] = 'distpv_' + distPVCF.loc[:,'resource']
        distPVCF = distPVCF.set_index('resource').transpose().reset_index(drop=True)
        distpv_profiles = distPVCF

    # Resetting indices before merging to assure there are no issues in the merge
    recf = recf.reset_index(drop=True)
    recf = pd.merge(left=recf, right=distpv_profiles, left_index=True, right_index=True)
    
    # Filtering out profiles of resources not included in this run and sorting to match the order of the rows in resources
    resources = resources[resources['area'].isin(ResReg_true['area'])]
    recf = recf[resources['resource']]
    
    # Create a scaling matrix to scale the appropriate columns of recf by the appropriate adjustment facotrs
    index_dist = resources['tech'].isin(vre_dist).reset_index(drop=True)
    index_tiein = resources['tech'].isin(vre_utility).reset_index(drop=True)
    multiplier = pd.DataFrame(index=np.arange(0,len(resources),1))
    multiplier.loc[:,'scale_factor'] = 1.0
    multiplier.loc[index_dist,'scale_factor'] = multiplier.loc[index_dist,'scale_factor'] / (1 - distloss)
    multiplier.loc[index_tiein,'scale_factor'] = multiplier.loc[index_tiein,'scale_factor']
    multiplier = multiplier.values
    if(all_year_load=="default"):
        multiplier = np.tile(multiplier.reshape(1,len(resources)), (len(load_profiles),1))
    else:
        multiplier = np.tile(multiplier.reshape(1,len(resources)), (8760,1))
    
    # Scale the appropriate resource CF profiles
    recf = recf * multiplier
    
    # Set the column names for resources to match ReEDS-2.0
    resources = pd.merge(left=resources, right=map_AREAtoCCREG, on='area', how='left')
    resources.columns = ['r','i','resource','ccreg']
    resources = resources[['r','i','ccreg','resource']]
    
    # Format CSP resources
    csp_resources = pd.DataFrame(columns=['i','r','resource','ccreg'])
    csp_profiles = pd.DataFrame()
    
    get_csp_resources = pd.DataFrame(columns=['resource'])
    get_csp_resources['resource'] = cspcf.columns
    for i in range(0,len(get_csp_resources)):
        c, underscore, r = get_csp_resources.loc[i,'resource'].partition('_')
        get_csp_resources.loc[i,'area'] = r
        get_csp_resources.loc[i,'class'] =c
    get_csp_resources = pd.merge(left=get_csp_resources, right=map_BAtoWINDREG, on='area')
    get_csp_resources.rename(columns={'area':'r','ba':'area'},inplace=True)
    get_csp_resources = pd.merge(left=get_csp_resources, right=map_BAtoCCREG, on='area').drop('area',1)
    
    for i in range(0,configs):
        temp_csp_resources = get_csp_resources.copy()
        temp_csp_resources.loc[:,'i'] = 'csp{}_'.format(str(i+1)) + temp_csp_resources.loc[:,'class']
        temp_csp_resources.drop('class',1,inplace=True)
        temp_csp_resources.loc[:,'resource'] = temp_csp_resources.loc[:,'i'] + '_' + temp_csp_resources.loc[:,'r']
        csp_resources = pd.concat([csp_resources,temp_csp_resources],sort=False).reset_index(drop=True)
        temp_cspcf = cspcf.copy()
    
        #filter csp columns in csp cf for those that have strings contained in resreg_true
        newcspcols = [col for col in temp_cspcf.columns if col.split('_')[1] in ResReg_true['area'].values]
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

if __name__ == '__main__':
#%%
    # Preparing to log any errors if they occur
    path_errors = os.path.join('ReEDS_Augur', 'ErrorFile')
    if not os.path.exists(path_errors): os.mkdir(path_errors)
    errorfile = os.path.join(path_errors, 'LDC_prep_errors.txt')
    logging.basicConfig(filename=errorfile, level=logging.ERROR)
    logger = logging.getLogger(__name__)
   
    # If an error occurs during the script write it to a txt file
    try:
        parser = argparse.ArgumentParser(description="""Create run-specific pickle files for the ReEDS-2.0 CV script""")
        # Mandatory arguments
        parser.add_argument("filename", help="""Filename of the LDC_static_inputs file used for this ReEDS run""", type=str)
        parser.add_argument("scenario", help="""Scenario name""", type=str)
        parser.add_argument("basedir", help="""Base directory for all batch runs""", type=str)
        parser.add_argument("all_year_load",help="""All year load name for EFS or SingleYear""",type=str)
    
        args = parser.parse_args()

        all_year_load = args.all_year_load
        scenario = args.scenario
    
        # Get the static input switch
        static_inputs = args.filename

        basedir = args.basedir

        hourly_prep(all_year_load,scenario,static_inputs,basedir)
    except:
        logger.error(traceback.format_exc())

    # Removing the error file if it is empty
    logging.shutdown()
    if os.stat(errorfile).st_size == 0:
        os.remove(errorfile)  