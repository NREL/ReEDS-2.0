###############
#%% IMPORTS ###
import os
import shutil
import pandas as pd

##############
#%% INPUTS ###

reeds_path = os.path.expanduser('~/github/ReEDS-2.0/')
# reeds_path = 'D:/Matt/ReEDS-2.0_ind/'

###### nrelnas01
### Note: Some runs are labeled as '2000bin' in hourlize outputs but '1300bin' for the ReEDS files.
### We use 2000 bins in hourlize to make sure we end up with no more than one site per bin,
### but we don't end up using all the bins. As of 20210822, the largest number of bins per
### region/class when using an upper limit of 2000 bins is 1300 (for upv), so we use numbins=1300
### to avoid creating more bins than we need in ReEDS.

##### onshore, individual sites
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'reference', 'wind-ons_10_reference_moderate_eos_flicker_2021-07-19-18-19-10-566297',True)
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'limited', 'wind-ons_11_limited_moderate_eos_flicker_2021-07-19-18-18-27-792746',True)
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'open', 'wind-ons_08_open_moderate_eos_flicker_2021-07-19-18-19-36-748656',True)

##### offshore, individual sites
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ofs', 'open', 'wind-ofs_2_moderate_open_2021-07-19-18-20-07-221449',True)
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ofs', 'limited', 'wind-ofs_3_moderate_limited_2021-07-19-18-20-34-673354',True)

##### onshore, s regions
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'limited', 'wind-ons_11_limited_moderate_eos_flicker_2021-07-07', False)
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'reference', 'wind-ons_10_reference_moderate_eos_flicker_2021-07-06', False)
# tech, scenario, hourlize_run, GSw_IndividualSites = (
#     'wind-ons', 'open', 'wind-ons_08_open_moderate_eos_flicker_2021-07-06', False)

##### onshore, 2000 bins (sufficient for 1 bin per site)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ons', 'limited', 'wind-ons_2000bin_11_limited_moderate_eos_flicker_2021-08-16-17-09-53-188639', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ons', 'reference', 'wind-ons_2000bin_10_reference_moderate_eos_flicker_2021-08-16-16-32-20-374555', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ons', 'open', 'wind-ons_2000bin_08_open_moderate_eos_flicker_2021-08-16-16-10-56-437907', False, 1300)

##### offshore, s regions, 5 bins
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ofs', 'limited', 'wind-ofs_3_moderate_limited_2021-07-07', False, 5)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ofs', 'open', 'wind-ofs_2_moderate_open_2021-07-07', False, 5)

##### offshore, s regions, 1300 bins (sufficient for 1 bin per site)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ofs', 'limited', 'wind-ofs_1300bin_3_moderate_limited_2021-08-31-18-53-58-694124', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'wind-ofs', 'open', 'wind-ofs_1300bin_2_moderate_open_2021-08-31-18-56-44-219670', False, 1300)

#### upv, 20 bins [default]
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'open', 'upv_20bin_scen_128_ed0_2021-08-30-17-57-35-744464', False, 20)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'reference', 'upv_20bin_scen_128_ed1_2021-08-30-18-04-12-761130', False, 20)
tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
    'upv', 'limited', 'upv_20bin_scen_128_ed4_2021-08-30-18-09-19-176157', False, 20)

# ### upv, 1300 bins [one bin per site]
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'open', 'upv_1300bin_scen_128_ed0_2021-08-30-18-18-35-789756', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'reference', 'upv_1300bin_scen_128_ed1_2021-08-30-18-24-58-166581', False, 1300)
# tech, scenario, hourlize_run, GSw_IndividualSites, numbins = (
#     'upv', 'limited', 'upv_1300bin_scen_128_ed4_2021-08-30-18-31-13-221406', False, 1300)

#################
#%% PROCEDURE ###

#%% Get the file locations
if os.name == 'posix':
    drive = '/Volumes/'
else:
    drive = '//nrelnas01/'


if GSw_IndividualSites:
    hourlize_base = os.path.join('ReEDS','Supply_Curve_Data','individual_sites','2021-07-20','')
else:
    if tech == 'wind-ons':
        hourlize_base = os.path.join('ReEDS','Supply_Curve_Data','ONSHORE','2021_Update','')
    elif tech == 'wind-ofs':
        hourlize_base = os.path.join('ReEDS','Supply_Curve_Data','OFFSHORE','2021_Update','')
    elif tech == 'upv':
        hourlize_base = os.path.join('ReEDS','Supply_Curve_Data','UPV','2021_Update','')

### Overwrite to a different path if desired
# hourlize_base = '/Volumes/ReEDS/Users/pbrown/hourlize/'

hourlize_path = os.path.join(drive, hourlize_base, hourlize_run, 'results','')

binlabel = '{}bin'.format(numbins)
if GSw_IndividualSites:
    resolutionlabel = '_site'
elif (tech in ['wind-ons', 'wind-ofs']):
    resolutionlabel = '_sreg{}'.format(binlabel)
else:
    resolutionlabel = '_{}'.format(binlabel)

#################
#%% PROCEDURE ###

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
    shutil.copy(
        os.path.join(hourlize_path,'{}.csv.gz'.format(tech)),
        os.path.join(
            reeds_path,'inputs','variability','multi_year','{}-{}.csv.gz'.format(
                tech, scenario))
    )

#%% Prescribed and exogenous capacity
if tech == 'wind-ons':
    shutil.copy(
        os.path.join(hourlize_path,'{}_prescribed_builds.csv'.format(tech)),
        os.path.join(reeds_path,'inputs','capacitydata','{}_prescribed_builds{}_{}.csv'.format(
            tech, resolutionlabel, scenario))
    )

    shutil.copy(
        os.path.join(hourlize_path,'{}_exog_cap.csv'.format(tech)),
        os.path.join(reeds_path,'inputs','capacitydata','{}_exog_cap{}_{}.csv'.format(
            tech, resolutionlabel, scenario))
    )
elif tech == 'wind-ofs':
    shutil.copy(
        os.path.join(hourlize_path,'{}_prescribed_builds.csv'.format(tech)),
        os.path.join(reeds_path,'inputs','capacitydata','{}_prescribed_builds{}_{}.csv'.format(
            tech, resolutionlabel, scenario))
    )
