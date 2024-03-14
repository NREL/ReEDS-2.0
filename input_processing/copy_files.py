# -*- coding: utf-8 -*-
"""
Created on Thu Dec 15 10:45:39 2022

@author: wcole
"""
#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import os
import numpy as np
import pandas as pd
import argparse
import shutil
import subprocess
import sys
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()


#%% Parse arguments
parser = argparse.ArgumentParser(description="Copy files needed for this run")
parser.add_argument('reeds_path', help='ReEDS directory')
parser.add_argument('inputs_case', help='output directory')

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing ###
# reeds_path = os.getcwd()
# reeds_path = os.path.join('E:\\','Vincent','ReEDS-2.0_SpFl')
# inputs_case = os.path.join(reeds_path,'runs','mergetest_Western_state','inputs_case','')

#%% Additional inputs
casedir = os.path.dirname(inputs_case)
NARIS = False
decimals = 6

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def scalar_csv_to_txt(path_to_scalar_csv):
    """
    Write a scalar csv to GAMS-readable text
    Format of csv should be: scalar,value,comment
    """
    ### Load the csv
    dfscalar = pd.read_csv(
        path_to_scalar_csv,
        header=None, names=['scalar','value','comment'], index_col='scalar').fillna(' ')
    ### Create the GAMS-readable string (comments can only be 255 characters long)
    scalartext = '\n'.join([
        'scalar {:<30} "{:<5.255}" /{}/ ;'.format(
            i, row['comment'], row['value'])
        for i, row in dfscalar.iterrows()
    ])
    ### Write it to a file, replacing .csv with .txt in the filename
    with open(path_to_scalar_csv.replace('.csv','.txt'), 'w') as w:
        w.write(scalartext)

    return dfscalar


def param_csv_to_txt(path_to_param_csv, writelist=True):
    """
    Write a parameter csv to GAMS-readable text
    Format of csv should be: parameter(indices),units,comment
    """
    ### Load the csv
    dfparams = pd.read_csv(
        path_to_param_csv,
        index_col='param', comment='#',
    )
    ### Create the GAMS-readable param definition string (comments must be ≤255 characters)
    paramtext = '\n'.join([
        f'parameter {i:<50} "--{row.units}-- {row.comment:.255}" ;'
        ## Don't define parameters with an input flag because they already exist
        for i, row in dfparams.loc[dfparams.input != 1].iterrows()
    ])
    ### Write it to a file, replacing .csv with .gms in the filename
    param_gms_path = path_to_param_csv.replace('.csv','.gms')
    with open(param_gms_path, 'w') as w:
        w.write(paramtext)
    ### Write the list of parameters if desired
    if writelist:
        ### Create the GAMS-readable list of parameters (without indices)
        paramlist = '\n'.join(dfparams.index.map(lambda x: x.split('(')[0]).tolist())
        param_list_path = (
            path_to_param_csv.replace('params','paramlist').replace('.csv','.txt'))
        with open(param_list_path, 'w') as w:
            w.write(paramlist)

    return dfparams


#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))
print('Starting copy_files.py')

#%% Identify files that have a region index versus those that do not

runfiles = (
    pd.read_csv(
        os.path.join(reeds_path, 'runfiles.csv'),
        dtype={'fix_cols':str},
        comment='#',
    ).fillna({'fix_cols':''})
    .rename(columns={'filepath (for input files only)':'filepath',
                     'post_copy (files are created after copy_files)':'post_copy'})
)

# Non-region files that need copied either do not have an entry in region_col
# or have 'ignore' as the entry. They also have a filepath specified.
nonregionFiles = (
    runfiles[
        ((runfiles['region_col'].isna()) | (runfiles['region_col'] == 'ignore'))
        & (~runfiles['filepath'].isna())]
    )

# Region files are those that have a region and do not specify 'ignore'
# Also ignore files that are created after this script runs (i.e., post_copy = 1)
regionFiles = (
    runfiles[
        (~runfiles['region_col'].isna())
        & (runfiles['region_col'] != 'ignore')
        & (runfiles['post_copy'] != 1)]
    )

#%% Copy relevant files from runfiles.csv that do not include regions
for i,row in nonregionFiles.iterrows():
    if row['filepath'].split('/')[0] in ['inputs','postprocessing']:
        dir_dst = inputs_case
    else:
        dir_dst = casedir
    src_file = os.path.join(reeds_path, row['filepath'])
    if (os.path.exists(src_file)) and (row['filename']!='rev_paths.csv'):
        shutil.copy(src_file, dir_dst)
            
#%% Rewrite the scalar and switches tables as GAMS-readable definitions

scalar_csv_to_txt(os.path.join(inputs_case,'scalars.csv'))
scalar_csv_to_txt(os.path.join(inputs_case,'gswitches.csv'))
### Do the same for the e_report parameters
param_csv_to_txt(os.path.join(inputs_case,'..','e_report_params.csv'))

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0).squeeze(1)

solveyears = pd.read_csv(
    os.path.join(reeds_path,'inputs','modeledyears.csv'),
    usecols=[sw['yearset_suffix']],
).squeeze(1).dropna().astype(int).tolist()
solveyears = [y for y in solveyears if y <= int(sw['endyear'])]

#%%###########################
#    -- Region Mapping --    #
##############################

### Load the full regions list
hierarchy = pd.read_csv(
    os.path.join(reeds_path, 'inputs', 'hierarchy{}.csv'.format(
        '' if (sw['GSw_HierarchyFile'] == 'default')
        else '_'+sw['GSw_HierarchyFile']))
)
# Remove asterisk from the first column
new_column_name = hierarchy.columns[0].replace('*', '')
hierarchy.rename(columns={hierarchy.columns[0]:new_column_name},
                 inplace = True)
if not NARIS:
    hierarchy = hierarchy.loc[hierarchy.country.str.lower()=='usa'].copy()

# Read region resolution switch to determine agglevel
agglevel = sw['GSw_RegionResolution'].lower()

#%% Parse the GSw_Region switch. If it includes a '/' character, it has the format
### {column of hierarchy.csv}/{period-delimited entries to keep from that column}.
if '/' in sw['GSw_Region']:
    GSw_RegionLevel, GSw_Region = sw['GSw_Region'].split('/')
    GSw_Region = GSw_Region.split('.')
    if len(GSw_Region) == 1:
        hier_sub = hierarchy[hierarchy[GSw_RegionLevel] == GSw_Region[0]].copy()
    else: 
        for idx in range(0,len(GSw_Region)):
            if idx == 0:
                hier_sub = hierarchy[hierarchy[GSw_RegionLevel] == GSw_Region[idx]].copy()
            else:
                hier_sub = pd.concat([
                    hier_sub,
                    hierarchy[hierarchy[GSw_RegionLevel] == GSw_Region[idx]]
                ])
# Otherwise use the modeled_regions.csv file to define the regions
else:     
    modeled_regions = pd.read_csv(
        os.path.join(reeds_path,'inputs','userinput','modeled_regions.csv'))
    modeled_regions.columns = modeled_regions.columns.str.lower()
    val_r_in = list(
        modeled_regions[~modeled_regions[sw['GSw_Region'].lower()].isna()]['r'].unique())
    hier_sub = hierarchy[hierarchy['ba'].isin(val_r_in)].copy()

hier_sub['resolution'] = agglevel
# Write out all unique aggregation levels present in the hierarchy resolution column
# Note: this is only a single value for now, but will be able to accept multiple
# values in the future
agglevels = hier_sub['resolution'].unique()

#write agglevel
pd.DataFrame(agglevels, columns=['agglevels']).to_csv(
    os.path.join(inputs_case, 'agglevels.csv'), index=False)

# ReEDS currently only supports a single agglevel, so convert the
# list to a single value
# The 'lvl' variable ensures that BA and larger spatial aggregations use BA data and procedure
if (len(agglevels) > 1):
    raise Exception("ReEDS only allows a single agglevels value, but multiple agglevels values are present")
else:
    agglevel = agglevels[0]
    lvl = 'ba' if agglevel in ['ba','state','aggreg'] else 'county'


#%%
# Create an r column at the front of the dataframe and populate it with the
# county-level regions (overwritten if needed)
hier_sub.insert(0,'r',hier_sub['county'])

# Overwrite the regions with the ba, state, or aggreg values as specififed
hier_sub['r'][hier_sub['resolution']=='ba'] = hier_sub['ba'][hier_sub['resolution']=='ba']
hier_sub['r'][hier_sub['resolution']=='state'] = hier_sub['st'][hier_sub['resolution']=='state']
hier_sub['r'][hier_sub['resolution']=='aggreg'] = hier_sub['aggreg'][hier_sub['resolution']=='aggreg']

# Write out a mapping of r to all counties
hier_sub[['r','county']].to_csv(
    os.path.join(inputs_case, 'r_county.csv'), index=False)

# Write out a mapping of r to ba regions
hier_sub[['r','ba']].drop_duplicates().to_csv(
    os.path.join(inputs_case, 'r_ba.csv'), index=False)

# Write out mapping of r to census divisions
hier_sub[['r','cendiv']].drop_duplicates().to_csv(
    os.path.join(inputs_case, 'r_cendiv.csv'), index=False)

# Write out mapping of rb to aggreg (for writesupplycurves.py)
hier_sub[['ba','aggreg']].drop_duplicates().to_csv(
    os.path.join(inputs_case, 'rb_aggreg.csv'), index=False)

# Write out val_county and val_ba before collapsing to unique regions
hier_sub['county'].to_csv(
    os.path.join(inputs_case, 'val_county.csv'), header=False, index=False)
hier_sub['ba'].drop_duplicates().to_csv(
    os.path.join(inputs_case, 'val_ba.csv'), header=False, index=False)

# Drop county name and resolution columns
hier_sub = hier_sub.drop(['county_name','resolution'],axis=1)

# Find all the unique elements that might define a region
val_r_all = []
for column in hier_sub.columns:
    val_r_all.extend(hier_sub[column].unique().tolist())

# Converting to a set ensures that only unique values are kept
val_r_all = sorted(list(set(val_r_all)))

pd.Series(val_r_all).to_csv(
    os.path.join(inputs_case, 'val_r_all.csv'), header=False, index=False)

# Collapse to only unique regions
hier_sub = hier_sub.drop_duplicates(subset=['r'])

# Sort hier_sub by r so that "ord(r)" commands in GAMS result in the properly
# ordered outputs
hier_sub['numeric_value'] = hier_sub['r'].str.extract('(\d+)').astype(float)
hier_sub = hier_sub.sort_values(by='numeric_value').drop('numeric_value', axis=1)

# Drop any substate region columns as these will no longer be needed
hier_sub = hier_sub.drop(['county','ba','st_interconnect'],axis=1)

# Populate val_st as unique states (not st_int) from the subsetted hierarchy table
# Also include "voluntary" state for modeling voluntary market REC trading
val_st = list(hier_sub['st'].unique()) + ['voluntary']

# Write out the unique values of each column in hier_sub to val_[column name].csv
# Note the conversion to a pd Series is necessary to leverage the to_csv function
for i in hier_sub.columns:
    pd.Series(hier_sub[i].unique()).to_csv(
        os.path.join(inputs_case,'val_' + i + '.csv'),index=False,header=False)
    
# Overwrite val_st with the val_st used here (which includes 'voluntary')
pd.Series(val_st).to_csv(
    os.path.join(inputs_case, 'val_st.csv'), header=False, index=False)

# Rename columns and save as hierarchy.csv
hier_sub.rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case, 'hierarchy.csv'), index=False)

levels = list(hier_sub.columns)
valid_regions = {level: list(hier_sub[level].unique()) for level in levels}

# Extract subsets for use in subsetting operations
val_cendiv = valid_regions['cendiv']
val_r = valid_regions['r']

# Export region files
pd.Series(val_r).to_csv(
    os.path.join(inputs_case, 'val_r.csv'), header=False, index=False)

# Create list of CS regions that are included in modeled regions
r_cs = pd.read_csv(os.path.join(reeds_path, 'inputs', 'ctus', 'r_cs.csv'))
r_cs = r_cs[r_cs['*r'].isin(val_r_all)]

# Export valid cs files to val_cs.csv
val_cs = pd.Series(r_cs['cs'].unique())
val_cs.to_csv(os.path.join(inputs_case, 'val_cs.csv'), header=False, index=False)
# Export filtered r_cs to r_cs.csv
r_cs.to_csv(os.path.join(inputs_case, 'r_cs.csv'), index=False)

#%%#####################################
#    -- Write run-specific files --    #
########################################

shutil.copy(os.path.join(reeds_path,'inputs','capacitydata',
                            f'wind-ons_prescribed_builds_{sw.GSw_SitingWindOns}_{lvl}.csv'),
            os.path.join(inputs_case,'wind-ons_prescribed_builds.csv'))
shutil.copy(os.path.join(reeds_path,'inputs','capacitydata',
                            f'wind-ofs_prescribed_builds_{sw.GSw_SitingWindOfs}_{lvl}.csv'),
            os.path.join(inputs_case,'wind-ofs_prescribed_builds.csv'))

### Specific versions of files ###

osprey_num_years = len(sw['osprey_years'].split('_'))
shutil.copy(
    os.path.join(
        reeds_path,'inputs','variability',f'index_hr_map_{osprey_num_years}.csv'),
    os.path.join(inputs_case,'index_hr_map.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','variability',f'd_szn_{osprey_num_years}.csv'),
    os.path.join(inputs_case,'d_szn.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','state_policies',f'offshore_req_{sw["GSw_OfsWindForceScen"]}.csv'),
    os.path.join(inputs_case,'offshore_req.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','consume',f'dac_gas_{sw["GSw_DAC_Gas_Case"]}.csv'),
    os.path.join(inputs_case,'dac_gas.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','carbonconstraints',f'capture_rates_{sw["GSw_CCS_Rate"]}.csv'),
    os.path.join(inputs_case,'capture_rates.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','capacitydata',
        f'ReEDS_generator_database_final_{sw["unitdata"]}.csv'),
    os.path.join(inputs_case,'unitdata.csv')
)
shutil.copy(
    os.path.join(
        reeds_path,'inputs','transmission',f'r_rr_adj_{lvl}.csv'),
    os.path.join(inputs_case,'r_rr_adj.csv')
)
for f in ['distPVcap','distPVCF_hourly']:
    shutil.copy(
        os.path.join(
            reeds_path,'inputs','dGen_Model_Inputs','{s}','{f}_{s}.csv').format(
                f=f, s=sw['distpvscen']),
        os.path.join(inputs_case, f'{f}.csv')
    )
pd.read_csv(
    os.path.join(reeds_path,'inputs','loaddata',f'demand_{sw["demandscen"]}.csv'),
).round(6).to_csv(os.path.join(inputs_case,'load_multiplier.csv'),index=False)

### Hourly RE profiles
# The BA-level files are part of the repository, so only need to check for
# these files if running at the county-level
if agglevel == 'county':
    # Read in the supply curve meta data
    revData = pd.read_csv(
                os.path.join(inputs_case,'rev_paths.csv')
            )
    # There is not county-level DUPV data, so drop DUPV from consideration
    revData = revData[revData['tech'] != 'dupv']
    
    # Create a dataframe to hold the new file version information
    file_version_new = pd.DataFrame(columns = ['tech','file version'])
    file_version_new['tech'] = revData['tech']
    
    # Check to see if there is a file version file for existing county-level
    # profiles, if not, then we'll need to copy over the files. If they are
    # present, then we need to check to see if they are the right version.
    if not os.path.isfile(os.path.join(reeds_path,'inputs','variability','multi_year','file_version.csv')):
        existing_fv = 0
        profile_data = revData
        profile_data['present'] = False
    else:
        existing_fv = 1
        file_version = pd.read_csv(os.path.join(reeds_path,'inputs','variability','multi_year','file_version.csv'))
        profile_data = pd.merge(revData,file_version,on='tech')
        # Check to see if the file version in the repo is already present
        profile_data['present'] = profile_data['sc_path'].str.contains('|'.join(profile_data['file version']))
        # Populate the new file version file with the existing file version
        # information
        file_version_new = file_version
    
    # If the profile data doesn't exist for the correct version of the supply
    # curve, then copy it over and put the supply curve version in
    # file_version.csv
    hpc = True if (int(os.environ.get('REEDS_USE_SLURM',0))) else False
    present_in_fv = 0
    file_version_updates = 0
    missing_file_versions = []
    for i,row in profile_data.iterrows():
        # If the profile is already present, do nothing
        if row['present'] == True:
            present_in_fv += 1
            continue
        # Otherwise copy the profile over
        else:
            # Check if ReEDS is being run by a non-NREL user. Non-NREL users must 
            # download county-level data manually from OpenEI to the ReEDS 
            # multi-year input folder. NREL users will auto-magically have the 
            # county-level data downloaded from the remote location that coincides 
            # with where they are running ReEDS from.
            try:
                remote_data = subprocess.check_output('git remote -v', stderr=subprocess.STDOUT, shell=True)                
                remote_url = (remote_data.splitlines()[0].split()[1].decode('utf-8'))
            except:
                # Set remote_url to 'no remote' if ReEDS was downloaded via zip file
                remote_url = 'no remote'
            # If NREL user, then attempt to copy data from the remote location defined in 
            # rev_paths.csv.
            if 'github.nrel.gov' in remote_url:
                sc_path = row['sc_path']
                access_case = row['access_case']
                print(f'Copying county-level hourly profiles for {row["tech"]}')
                try:
                    shutil.copy(
                        os.path.join(sc_path,f'{row["tech"]}_{access_case}_county','results',f'{row["tech"]}.h5'),
                        os.path.join(reeds_path,'inputs','variability','multi_year',f'{row["tech"]}-{access_case}_county.h5')
                    )
                except FileNotFoundError:
                    print("ERROR: cannot copy {}.\nCheck that you are connected to external drive ({}).".format(
                        os.path.join(f'{row["tech"]}_{access_case}_county','results',f'{row["tech"]}.h5'),
                        sc_path))
                    sys.exit(1)
                # Update the file version information
                file_version_new.loc[file_version_new['tech'] == row['tech'], 'file version'] = sc_path.split("/")[-1]
                file_version_updates += 1
            # If non-NREL user, then save the name of the missing file, and write it out 
            # in the error message below
            else:
                missing_file_versions.append(f'{row["tech"]}-{access_case}_county.h5')
    # If any county-level file is missing from the inputs folder but a file_version.csv exists, 
    # then print out an error message to delete the file_version.csv and restart the run
    if (existing_fv) and (present_in_fv < 1):
        error = ("It appears that there is a file_version.csv present in\n"
            "/inputs/variability/multi-year/ despite a county-level file(s) missing\n"
            "from the folder. Delete file_version.csv from the folder and restart the run\n"
            "to have ReEDS redownload the missing county-level file(s)."
        )
        raise ValueError(error) 
    # If any missing files for non-NREL users, then print out an error message with those
    # file names and where to download them
    if len(missing_file_versions) > 0:
        error = ("To run ReEDS at county-level spatial resolution, please download the following\n"
            "county-level data files from OpenEI to /inputs/variability/multi-year/\n\n"
            "Files:\n"
            +"\n".join(missing_file_versions)+"\n\n"
            +"OpenEI files link:\n"
            "[https://data.openei.org/submissions/5986]"
        )
        raise ValueError(error)   
    # Write out the new file version file if there are any updates
    if file_version_updates > 0:
        file_version_new.to_csv(os.path.join(reeds_path,'inputs','variability','multi_year','file_version.csv'), index = False)

### Files defined from case inputs ###

pd.DataFrame(
    {'*pvb_type': [f'pvb{i}' for i in range(1,4)],
     'ilr': [np.around(float(c) / 100, 2) for c in sw['GSw_PVB_ILR'].split('_')]}
).to_csv(os.path.join(inputs_case, 'pvb_ilr.csv'), index=False)

pd.DataFrame(
    {'*pvb_type': [f'pvb{i}' for i in range(1,4)],
     'bir': [np.around(float(c) / 100, 2) for c in sw['GSw_PVB_BIR'].split('_')]}
).to_csv(os.path.join(inputs_case, 'pvb_bir.csv'), index=False)

### Constant value if input is float, otherwise named profile
try:
    rate = float(sw['GSw_MethaneLeakageScen'])
    pd.Series(index=range(2010,2051), data=rate, name='constant').rename_axis('*t').round(5).to_csv(
        os.path.join(inputs_case,'methane_leakage_rate.csv'))
except ValueError:
    pd.read_csv(
        os.path.join(reeds_path,'inputs','carbonconstraints','methane_leakage_rate.csv'),
        index_col='t',
    )[sw['GSw_MethaneLeakageScen']].rename_axis('*t').round(5).to_csv(
        os.path.join(inputs_case,'methane_leakage_rate.csv'))


### Single column from input table ###

pd.read_csv(
    os.path.join(reeds_path,'inputs','carbonconstraints','ng_crf_penalty.csv'), index_col='t',
)[sw['GSw_NG_CRF_penalty']].rename_axis('*t').to_csv(
    os.path.join(inputs_case,'ng_crf_penalty.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','carbonconstraints','co2_cap.csv'), index_col='t',
).loc[sw['GSw_AnnualCapScen']].rename_axis('*t').to_csv(
    os.path.join(inputs_case,'co2_cap.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','carbonconstraints','co2_tax.csv'), index_col='t',
)[sw['GSw_CarbTaxOption']].rename_axis('*t').round(2).to_csv(
    os.path.join(inputs_case,'co2_tax.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','reserves','prm_annual.csv'), index_col=['*nercr','t'],
)[sw['GSw_PRM_scenario']].round(5).to_csv(
    os.path.join(inputs_case,'prm_annual.csv')
)
pd.DataFrame(columns=solveyears).to_csv(
    os.path.join(inputs_case,'modeledyears.csv'), index=False)
pd.read_csv(
    os.path.join(reeds_path,'inputs','national_generation','gen_mandate_trajectory.csv'),
    index_col='GSw_GenMandateScen'
).loc[sw['GSw_GenMandateScen']].rename_axis('*t').round(5).to_csv(
    os.path.join(inputs_case,'gen_mandate_trajectory.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','national_generation','gen_mandate_tech_list.csv'),
    index_col='*i',
)[sw['GSw_GenMandateList']].to_csv(
    os.path.join(inputs_case,'gen_mandate_tech_list.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','climate','climate_heuristics_yearfrac.csv'),
    index_col='*t',
)[sw['GSw_ClimateHeuristics']].round(3).to_csv(
    os.path.join(inputs_case,'climate_heuristics_yearfrac.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','climate','climate_heuristics_finalyear.csv'),
    index_col='*parameter',
)[sw['GSw_ClimateHeuristics']].round(3).to_csv(
    os.path.join(inputs_case,'climate_heuristics_finalyear.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','capacitydata','upgrade_costs_ccs_coal.csv'),
    index_col='t',
)[sw['ccs_upgrade_cost_case']].round(3).rename_axis('*t').to_csv(
    os.path.join(inputs_case,'upgrade_costs_ccs_coal.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','capacitydata','upgrade_costs_ccs_gas.csv'),
    index_col='t',
)[sw['ccs_upgrade_cost_case']].round(3).rename_axis('*t').to_csv(
    os.path.join(inputs_case,'upgrade_costs_ccs_gas.csv')
)
pd.read_csv(
    os.path.join(reeds_path,'inputs','consume','h2_exogenous_demand.csv'),
    index_col=['p','t']
)[sw['GSw_H2_Demand_Case']].round(3).rename_axis(['*p','t']).to_csv(
    os.path.join(inputs_case,'h2_exogenous_demand.csv')
)

#%% Sets folder
shutil.copytree(
    os.path.join(reeds_path,'inputs','sets'),
    os.path.join(inputs_case,'sets'),
    dirs_exist_ok=True,
    ignore=shutil.ignore_patterns('README*','readme*'),
)
#%% Write commands to load sets
sets = runfiles.loc[runfiles.GAMStype=='set'].copy()
settext = '$offlisting\n' + '\n\n'.join([
    f"set {row.GAMSname} '{row.comment:.255}'"
    '\n/'
    f"\n$include inputs_case%ds%{row.filename}"
    '\n/ ;'
    for i, row in sets.iterrows()
]) + '\n$onlisting\n'
## Write to file
with open(os.path.join(casedir,'b_sets.gms'), 'w') as f:
    f.write(settext)

#%%########################################################
#    -- Filter and copy data for files with regions --    #
###########################################################

for i, row in regionFiles.iterrows():
    filepath = row['filepath']
    filename = row['filename']
    filetype = row['filetype']
    region_col = row['region_col']
    fix_cols = row['fix_cols'].split(',')

    # If a filename isn't specified, that means it is already in the
    # inputs_case folder, otherwise use the filepath
    if filepath != filepath:
        full_path = os.path.join(inputs_case,filename)
    else:
        full_path = os.path.join(reeds_path,filepath)

    # Read if file that needs filtered
    if filetype == '.h5':
        df = pd.read_hdf(full_path)
    elif filetype == '.csv':
        df = pd.read_csv(full_path)
    else:
        raise('filetype for {} is not .csv or .h5'.format(full_path))

    # Filter data to valid regions
    if region_col == 'wide':
        # Check to see if the regions are listed in the columns. If they are,
        # then use those columns
        if df.columns.isin(val_r_all).any():
            df = df.loc[:,df.columns.isin(fix_cols + val_r_all)]
        # Otherwise just use a empty dataframe
        else:
            df = pd.DataFrame()

    # If there is a region to region mapping set
    elif region_col.strip('*') in ['r,rr','r,rs','rs,r']:
        # make sure both the r and rr regions are in val_r
        r,rr = region_col.split(',')
        df = df.loc[df[r].isin(val_r_all) & df[rr].isin(val_r_all)]

    # Subset on the valid regions except for r regions
    # (r regions might also include s regions, which complicates things...)
    elif ((region_col.strip('*') in levels) & (region_col.strip('*') != 'r')):
        df = df.loc[df[region_col].isin(valid_regions[region_col.strip('*')])]
        
    elif (region_col == 'cs' or region_col == '*cs'):
        # subset to just cs regions
        df = df.loc[df[region_col].isin(val_cs)]

    # Subset both column of 'st' and columns of state if st_st
    elif (region_col.strip('*') == 'st_st'):
        # make sure both the state regions are in val_st
        df = df.loc[df['st'].isin(val_st)]
        df = df.loc[:,df.columns.isin(fix_cols + val_st)]

    elif (region_col.strip('*') == 'r_cendiv'):
        # Make sure both the r is in val_r and cendiv is in val_cendiv
        df = df.loc[df['r'].isin(val_r_all)]
        df = df.loc[:,df.columns.isin(["r"] + val_cendiv)]

    # Subset on val_st if region_col == st
    elif region_col == 'wide_st':
        # Check to see if the states are listed in the columns. If they are,
        # then use those columns
        if df.columns.isin(val_st).any():
            df = df.loc[:,df.columns.isin(fix_cols + val_st)]
        # Otherwise just use a empty dataframe
        else:
            df = pd.DataFrame()

    # If region_col is not wide, st, or aliased..
    else:
        df = df.loc[df[region_col].isin(val_r_all)]
    
    # Write data to inputs_case folder
    if filetype == '.h5':
        df.to_hdf(
            os.path.join(inputs_case,filename), key='data', complevel=4, format='table')
    else:
        df.to_csv(
            os.path.join(inputs_case,filename), index=False)

### All files from the user input folder
userinputs = os.listdir(os.path.join(reeds_path,"inputs","userinput"))

for file_name in userinputs:
    full_file_name = os.path.join(reeds_path,"inputs","userinput", file_name)
    # ivt is now a special case written in calc_financial_inputs, so skip it here
    if (os.path.isfile(full_file_name) and (file_name != 'ivt.csv')):
        shutil.copy(full_file_name, inputs_case)


#%% Special-case set modifications
## Expand i (technologies) set if modeling water use
if int(sw.GSw_WaterMain):
    i = pd.concat([
        pd.read_csv(
            os.path.join(reeds_path,'inputs','sets','i.csv'),
            comment='*', header=None).squeeze(1),
        pd.read_csv(
            os.path.join(inputs_case,'i_coolingtech_watersource.csv'),
            comment='*', header=None).squeeze(1),
        pd.read_csv(
            os.path.join(inputs_case,'i_coolingtech_watersource_upgrades.csv'),
            comment='*', header=None).squeeze(1),
    ])
    i.to_csv(os.path.join(inputs_case,'sets','i.csv'), header=False, index=False)


### Legacy files - no longer used
if sw['unitdata'] == 'ABB':
    nas = '//nrelnas01/ReEDS/FY18-ReEDS-2.0/data/'
    out = os.path.join(reeds_path,'inputs','capacitydata')
    shutil.copy(os.path.join(nas,'ExistingUnits_ABB.gdx'), out)
    shutil.copy(os.path.join(nas,'PrescriptiveBuilds_ABB.gdx'), out)
    shutil.copy(os.path.join(nas,'PrescriptiveRetirements_ABB.gdx'), out)
    shutil.copy(os.path.join(nas,'ReEDS_generator_database_final_ABB.gdx'), out)

### Make opt file change for value streams
if sw['GSw_ValStr'] != '0':
    if int(sw['GSw_gopt']) == 1:
        origOptExt = 'opt'
    elif int(sw['GSw_gopt']) < 10:
        origOptExt = 'op' + sw['GSw_gopt']
    else:
        origOptExt = 'o' + sw['GSw_gopt']
    #Add writemps statement to opt file
    with open(casedir + '/cplex.'+origOptExt, 'a') as file:
        file.write('\nwritemps ReEDSmodel.mps')

toc(tic=tic, year=0, process='input_processing/copy_files.py',
    path=os.path.join(inputs_case,'..'))

print('Finished copy_files.py')
