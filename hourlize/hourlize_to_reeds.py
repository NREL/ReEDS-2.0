###############
#%% IMPORTS ###
import os
import shutil
import pandas as pd

##############
#%% INPUTS ###

this_dir_path = os.path.dirname(os.path.realpath(__file__))
reeds_path = os.path.realpath(os.path.join(this_dir_path,'..'))
# reeds_path = os.path.expanduser('~/github/ReEDS-2.0/')

###### nrelnas01
### Note: Some runs are labeled as '2000bin' in hourlize outputs but '1300bin' for the ReEDS files.
### We use 2000 bins in hourlize to make sure we end up with no more than one site per bin,
### but we don't end up using all the bins. As of 20210822, the largest number of bins per
### region/class when using an upper limit of 2000 bins is 1300 (for upv), so we use numbins=1300
### to avoid creating more bins than we need in ReEDS.

##### onshore, individual sites
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'open', 'wind-ons_ind_00_open_moderate',True)
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'reference', 'wind-ons_ind_01_reference_moderate',True)
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'limited', 'wind-ons_ind_02_limited_moderate',True)
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'limitedplus', 'wind-ons_ind_21_limited_moderate_eos_flicker_lc_rl',True)

##### offshore, individual sites
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ofs', 'open', 'wind-ofs_ind_0_open_moderate',True)
tech, scenario, hourlize_run, GSw_IndividualSites = (
    'wind-ofs', 'limited', 'wind-ofs_ind_1_limited_moderate',True)

##### onshore, s regions, 5 bins
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ons', 'open', 'wind-ons_5bin_00_open_moderate', False, 5)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'wind-ons', 'reference', 'wind-ons_5bin_01_reference_moderate', False, 5)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ons', 'limited', 'wind-ons_5bin_02_limited_moderate', False, 5)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ons', 'limitedplus', 'wind-ons_5bin_21_limited_moderate_eos_flicker_lc_rl', False, 5)

##### onshore, s regions, 1300 bins
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ons', 'open', 'wind-ons_1300bin_00_open_moderate', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'wind-ons', 'reference', 'wind-ons_1300bin_01_reference_moderate', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ons', 'limited', 'wind-ons_1300bin_02_limited_moderate', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ons', 'limitedplus', 'wind-ons_1300bin_21_limited_moderate_eos_flicker_lc_rl', False, 1300)

##### offshore, s regions, 5 bins
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'wind-ofs', 'open', 'wind-ofs_5bin_0_open_moderate', False, 5)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ofs', 'limited', 'wind-ofs_5bin_1_limited_moderate', False, 5)

##### offshore, s regions, 1300 bins (sufficient for 1 bin per site)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ofs', 'open', 'wind-ofs_1300bin_0_open_moderate', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ofs', 'limited', 'wind-ofs_1300bin_1_limited_moderate', False, 1300)

#### upv, 20 bins [default]
#tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'open', 'upv_20bin_0_moderate_open', False, 20)
#tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'reference', 'upv_20bin_1_moderate_reference', False, 20)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#      'upv', 'limited', 'upv_20bin_2_moderate_limited', False, 20)

# ### upv, 1300 bins [one bin per site]
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'open', 'upv_1300bin_scen_128_ed0_2021-08-30-18-18-35-789756', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'reference', 'upv_1300bin_1_moderate_reference', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'limited', 'upv_1300bin_scen_128_ed4_2021-08-30-18-31-13-221406', False, 1300)
# ## 20220110 - binned exogenous capacity
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'reference', 'upv_1300bin_scen_128_ed1', False, 1300)

###### binless
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'wind-ons', 'open', 'wind-ons_00_open_moderate', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'wind-ons', 'reference', 'wind-ons_01_reference_moderate', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'wind-ons', 'limited', 'wind-ons_02_limited_moderate', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'upv', 'open', 'upv_0_moderate_open', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'upv', 'reference', 'upv_1_moderate_reference', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'upv', 'limited', 'upv_2_moderate_limited', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'wind-ofs', 'open', 'wind-ofs_0_open_moderate', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#    'wind-ofs', 'limited', 'wind-ofs_1_limited_moderate', False, None)

###### Load
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'load', 'EERbaseClip40', 'load_EER_20220906_baseline_RegularClip40_NEclip0', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'load', 'EERbaseClip80', 'load_EER_20220906_baseline_RegularClip80_NEclip80', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'load', 'EERhighClip40', 'load_EER_20220906_central_RegularClip40_NEclip0', False, None)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'load', 'EERhighClip80', 'load_EER_20220906_central_RegularClip80_NEclip80', False, None)

#################
#%% PROCEDURE ###

#%% Get the file locations
if os.name == 'posix':
    drive = '/Volumes/'
else:
    drive = '//nrelnas01/'


if GSw_IndividualSites:
    hourlize_base = os.path.join('ReEDS','Supply_Curve_Data','individual_sites','2022-09-29','')
elif tech == 'load':
    hourlize_base = os.path.join('ReEDS','Supply_Curve_Data','LOAD','2022_Update','')
else:
    # get supply curve path on nrelnas01 from supply curve metada file. 
    df_rev = pd.read_csv(os.path.join(this_dir_path, '../inputs/supplycurvedata/metadata/rev_paths.csv'))
    df_rev = df_rev[(df_rev['tech'] == tech)&(df_rev['access_case'] == scenario)].squeeze()
    hourlize_base = os.path.join('ReEDS','Supply_Curve_Data', df_rev['sc_path'])       

### Overwrite to a different path if desired
# hourlize_base = '/Volumes/ReEDS/Users/pbrown/hourlize/'
# hourlize_base = '/Users/pbrown/github2/ReEDS-2.0/hourlize/out/'
# hourlize_base = '/Volumes/ReEDS/FY22-Bespoke/NTPS/EER_20220819_reeds_load_central_2022-09-05/'

hourlize_path = os.path.join(drive, hourlize_base, hourlize_run, 'results','')

if GSw_IndividualSites:
    noresolutionlabel = '_site'
    resolutionlabel = '_site'
else:
    noresolutionlabel = '_sreg'
    binlabel = '{}bin'.format(numbins) if numbins else ''
    if tech in ['wind-ons', 'wind-ofs']:
        resolutionlabel = '_sreg{}'.format(binlabel)
    else:
        resolutionlabel = '_{}'.format(binlabel) if numbins else ''

#################
#%% PROCEDURE ###

#%% Load
if tech == 'load':
    ### Timeslice
    shutil.copy(
        os.path.join(hourlize_path,'load.csv'),
        os.path.join(reeds_path,'inputs','loaddata',f'{scenario}load.csv')
    )
    ### Hourly
    shutil.copy(
        os.path.join(hourlize_path,'load_hourly_multi.h5'),
        os.path.join(
            reeds_path,'inputs','variability',
            ('multi_year' if scenario in ['default','AEO'] else 'EFS_Load'),
            f'{scenario}_load_hourly.h5')
    )
    quit()

#%% Supply curve
shutil.copy(
    os.path.join(hourlize_path,'{}_supply_curve.csv'.format(tech)),
    os.path.join(reeds_path,'inputs','supplycurvedata','{}_supply_curve{}-{}.csv'.format(
        tech, resolutionlabel, scenario))
)

#%% Capacity factor
pd.read_csv(
    os.path.join(hourlize_path,'{}_cf_ts.csv'.format(tech))
).drop('cfsigma', axis=1, errors='ignore').round({'cfmean':5}).to_csv(
    os.path.join(
        reeds_path,'inputs','cf','{}_cf_ts{}-{}.csv'.format(
            tech,
            '_site' if GSw_IndividualSites else ('_sreg' if tech in ['wind-ons','wind-ofs'] else ''),
            scenario)),
    index=False,
)

#%% Hourly profiles
if not GSw_IndividualSites:
    try:
        shutil.copy(
            os.path.join(hourlize_path,'{}.csv.gz'.format(tech)),
            os.path.join(
                reeds_path,'inputs','variability','multi_year','{}-{}.csv.gz'.format(
                    tech, scenario))
        )
    except FileNotFoundError:
        shutil.copy(
            os.path.join(hourlize_path,'{}.h5'.format(tech)),
            os.path.join(
                reeds_path,'inputs','variability','multi_year','{}-{}.h5'.format(
                    tech, scenario))
        )

#%% Prescribed and exogenous capacity
if tech == 'wind-ons':
    shutil.copy(
        os.path.join(hourlize_path,'{}_prescribed_builds.csv'.format(tech)),
        os.path.join(reeds_path,'inputs','capacitydata','{}_prescribed_builds{}_{}.csv'.format(
            tech, noresolutionlabel, scenario))
    )

    df = pd.read_csv(os.path.join(hourlize_path,'{}_exog_cap.csv'.format(tech)))
    if 'bin' in df:
        df['bin'] = 'bin' + df['bin'].astype(str)
    df.rename(columns={df.columns[0]: '*'+str(df.columns[0])}, inplace=True)
    df.to_csv(
        os.path.join(reeds_path,'inputs','capacitydata','{}_exog_cap{}_{}.csv'.format(
            tech, noresolutionlabel, scenario)),
        index=False
    )

elif tech == 'wind-ofs':
    shutil.copy(
        os.path.join(hourlize_path,'{}_prescribed_builds.csv'.format(tech)),
        os.path.join(reeds_path,'inputs','capacitydata','{}_prescribed_builds{}_{}.csv'.format(
            tech, noresolutionlabel, scenario))
    )
    # shutil.copy(
    #     os.path.join(hourlize_path,'{}_exog_cap.csv'.format(tech)),
    #     os.path.join(reeds_path,'inputs','capacitydata','{}_exog_cap{}_{}.csv'.format(
    #         tech, noresolutionlabel, scenario))
    # )

#%% Metadata
metafiles = [
    'config.py',
    'config_aggregation.json', 'config_pipeline.json',
    'config_rep-profiles.json', 'config_supply-curve.json',
    ### These two files are only included for PV, so don't worry about them for wind
    'config_rep-profiles_aggprof.json', 'config_rep-profiles_repprof.json',
]
outpath = os.path.join(
    reeds_path,'inputs','supplycurvedata','metadata',
    '{}{}_{}'.format(tech, resolutionlabel, scenario))
os.makedirs(outpath, exist_ok=True)

for metafile in metafiles:
    try:
        shutil.copy(
            os.path.join(hourlize_path,'..','inputs',metafile),
            os.path.join(reeds_path,'inputs','supplycurvedata','metadata',outpath,''),
        )
    except FileNotFoundError as err:
        print(err)

### Copy the readme file if there is one
for ext in ['.yaml', '.yml', '.md', '.txt', '']:
    try:
        shutil.copy2(
            os.path.join(hourlize_path,'..','inputs','readme'+ext),
            os.path.join(reeds_path,'inputs','supplycurvedata','metadata',outpath,''),
        )
    except:
        pass
