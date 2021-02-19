"""
@author: pbrown
@date: 20201104 14:47
* Adapted from input_processing/R/writesupplycurves.R
* Reminder: upv and dupv by ba whereas csp and wnd are by s
# TODO: Add option to apply flexible bins to PV, CSP, wind-ofs in addition to wind-ons
# Would be nice: Write rsc_combined as a .csv with header instead of .txt
"""

#%%########
### IMPORTS

import gdxpds
import pandas as pd
import numpy as np
import os, sys
import argparse
#%% Direct print and errors to log file
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')

#%%####################
### ARGUMENT INPUTS ###

parser = argparse.ArgumentParser(description='Format and supply curves')
parser.add_argument('-i', '--basedir', help='path to ReEDS directory')
parser.add_argument('-u', '--unitdata', default='EIA-NEMS', 
                    help='Unit Database: "EIA-NEMS" for NEMS and "ABB" for ventyx')
parser.add_argument('-d', '--deduct', type=int, default=0, help='deduct')
parser.add_argument('-s', '--supplycurve', type=str, default='default',
                    help='Wind and Solar Supply Curves')
parser.add_argument('-o', '--inputs_case', help='path to inputs_case directory')
parser.add_argument('-g', '--geosupplycurve', default='ATB_2020',
                    help='Geothermal Supply Curve')
parser.add_argument('-e', '--geodiscov', default='BAU',
                    help='Annual discover rates for new geothermal sites')
#parser.add_argument('-n', '--numbins_wind', type=int, default=5, 
#                    help='Number of interconnection supply curve bins for wind')

args = parser.parse_args()
basedir = args.basedir
unitdata = args.unitdata
deduct = args.deduct
supplycurve = args.supplycurve
inputs_case = os.path.join(args.inputs_case, '')
geosupplycurve = args.geosupplycurve
geodiscov = args.geodiscov
#numbins_wind = args.numbins_wind

#%%#################
### FIXED INPUTS ###
### setting to default value for open access version
numbins_wind = 5
### Number of bins used for everything other than wind-ons
numbins_other = 5
### Rounding precision
decimals = 7

# #%%#########################
# ### Settings for testing ###
# basedir = '/Users/pbrown/github/ReEDS-2.0/'
# unitdata = 'EIA-NEMS'
# deduct = 0
# supplycurve = 'default'
# inputs_case = '/Users/pbrown/github/ReEDS-2.0/runs/v20201104_flexiblescbins/inputs_case/'
# geosupplycurve = 'ATB_2020'
# geodiscov = 'BAU'
# numbins_wind = 5

#%%##############
### FUNCTIONS ###

def name_gdxcols(df):
    """
    Rename columns of a long gdxpds dataframe with alphabetical labels
    """
    colid = list('ijklmnopqrstuvwxyz')
    df.columns = colid[:df.shape[1]-1] + ['value']
    return df

#%%##############
### PROCEDURE ###

#%% Set the gdx paths
gdxin = os.path.join(
    basedir,'inputs','capacitydata','ExistingUnits_{}.gdx').format(unitdata)
gdxinprescribe = os.path.join(
    basedir,"inputs","capacitydata","PrescriptiveBuilds_{}.gdx").format(unitdata)
gdxinretire = os.path.join(
    basedir,'inputs','capacitydata','PrescriptiveRetirements_{}.gdx').format(unitdata)
gdxPHS = os.path.join(basedir,'inputs','supplycurvedata','PHSsupplycurvedata.gdx')
gdxBio = os.path.join(basedir,'inputs','supplycurvedata','Biosupplycurvedata.gdx')
### Set inputs and supplycurvedata paths for convenience
inputsdir = os.path.join(basedir,'inputs','')
scdir = os.path.join(inputsdir,'supplycurvedata','')

#%% Read in tech-subset-table.csv to determine number of csp configurations
tech_subset_table = pd.read_csv(os.path.join(inputsdir, "tech-subset-table.csv"))
csp_configs = tech_subset_table.loc[
    (tech_subset_table.CSP== 'YES' ) & (tech_subset_table.STORAGE == 'YES')].shape[0]

#%% Read the r-to-s map and rewrite it as a (r x s) matrix
rsnew = pd.read_csv(os.path.join(inputsdir, 'rsmap.csv'), names=['r','s'], header=0)
rsout = rsnew.copy()
rsout['val'] = 1
rsout = rsout.set_index(['r','s']).unstack('s').fillna(0).astype(int)['val']
### Write it
rsout.to_csv(os.path.join(inputs_case,'rsout.csv'), index_label='r')

#%% Load the existing wind and CSP units
twnd = name_gdxcols(gdxpds.to_dataframe(gdxin,'tmpWTOi')['tmpWTOi'])
tcsp = name_gdxcols(gdxpds.to_dataframe(gdxin,'tmpCSPOct')['tmpCSPOct'])
### Fix the region labels
twnd.i = 's' + twnd.i.astype(str)
tcsp.i = 's' + tcsp.i.astype(str)
### Downselect CSP
tcsp = tcsp[['i','value']].copy()
### concatenate CSP and wind
tcsp['tech'] = 'csp'
twnd['tech'] = 'wind-ons'
tcsp.columns = ['i','value','tech']
ts = pd.concat([tcsp, twnd])
ts.columns = ['s','value','tech']
ts = ts.merge(rsnew, on='s')

#%% Load the existing PV plants
tupv = name_gdxcols(gdxpds.to_dataframe(gdxin,'tmpUPVOn')['tmpUPVOn'])
tdupv = name_gdxcols(gdxpds.to_dataframe(gdxin,'tmpDUPVOn')['tmpDUPVOn'])
tupv['s'] = 'sk'
tdupv['s'] = 'sk'
tupv.columns = ['r','value','s']
tdupv.columns = ['r','value','s']
tupv['tech'] = 'upv'
tdupv['tech'] = 'dupv'

### Concatenate all the existing capacity
tout = pd.concat([ts, tupv, tdupv]).rename(columns={'value':'exist'})
### Change the units
tout.exist /= 1000

##########################
#%% Load supply curve file

#%% default
if supplycurve == 'default':
    print("Using 2019 version of wind. Using 2018 version for everything else")

    windons = pd.read_csv(scdir + 'wind-ons_supply_curve-{}bin.csv'.format(numbins_wind))
    windons['type'] = 'wind-ons'
    windofs = pd.read_csv(scdir + 'wind-ofs_supply_curve.csv')
    windofs['type'] = 'wind-ofs'
    windall = pd.concat([windons, windofs], axis=0)
    windall['region'] = windall.region.map(lambda x: x.lstrip('s'))
    windall['class'] = 'class' + windall['class'].astype(str)
    windall['bin'] = 'wsc' + windall['bin'].astype(str)
    ### Pivot, with bins in long format
    windcost = (
        windall.pivot(index=['region','class','type'], columns='bin', values='trans_cap_cost')
        .fillna(0).reset_index())
    windcap = (
        windall.pivot(index=['region','class','type'], columns='bin', values='capacity')
        .fillna(0).reset_index())
    
    dupvcost = pd.read_csv(scdir + 'DUPV_supply_curves_cost_2018.csv')
    upvcost = pd.read_csv(scdir + 'UPV_supply_curves_cost_2018.csv')

    dupvcap = pd.read_csv(scdir + 'DUPV_supply_curves_capacity_2018.csv')
    upvcap = pd.read_csv(scdir + 'UPV_supply_curves_capacity_2018.csv')

    cspcap = pd.read_csv(scdir + 'CSP_supply_curves_capacity_2018.csv').fillna(0)
    cspcost = pd.read_csv(scdir + 'CSP_supply_curves_cost_2018.csv').fillna(0)

#%% 0
if supplycurve == '0':
    ### Import capacity data
    dupvcap = pd.read_csv(scdir + 'DUPV_supply_curves_capacity.csv')
    upvcap = pd.read_csv(scdir + 'UPV_supply_curves_capacity.csv')
    windcap = pd.read_csv(scdir + 'wind_supply_curves_capacity.csv')

    ### Import cost data
    dupvcost = pd.read_csv(scdir + 'DUPV_supply_curves_cost.csv')
    upvcost = pd.read_csv(scdir + 'UPV_supply_curves_cost.csv')
    windcost = pd.read_csv(scdir + 'wind_supply_curves_cost.csv')

    ### now using the argument-indicated gdx file for CSP supply curves
    cspcap = name_gdxcols(gdxpds.to_dataframe(gdxin, 'CSP2G')['CSP2G'])
    cspcost = name_gdxcols(gdxpds.to_dataframe(gdxin, 'CSP2GPTS')['CSP2GPTS'])

    ### need to match formatting from before
    cspcap = cspcap.pivot(index=['i','j'], columns='k').fillna(0)
    cspcost = cspcost.pivot(index=['i','j'], columns='k').fillna(0)

#%% naris
if supplycurve == 'naris':
    print("using NARIS version of wind, upv, and dupv supply cost curves")

    dupvcost = pd.read_csv(scdir + 'DUPV_supply_curves_cost_NARIS.csv')
    upvcost = pd.read_csv(scdir + 'UPV_supply_curves_cost_NARIS.csv')
    windcost = pd.read_csv(scdir + 'wind_supply_curves_cost_NARIS.csv')

    dupvcap = pd.read_csv(scdir + 'DUPV_supply_curves_capacity_NARIS.csv')
    upvcap = pd.read_csv(scdir + 'UPV_supply_curves_capacity_NARIS.csv')
    windcap = pd.read_csv(scdir + 'wind_supply_curves_capacity_NARIS.csv')

    ### specify the column names
    for df in [dupvcost, upvcost, windcost, dupvcap, upvcap, windcap]:
        df.rename(columns={'Unnamed: 0':'region', 'Unnamed: 1':'class', 'Unnamed: 2': 'type'},
                  inplace=True)

    ### now using the argument-indicated gdx file for CSP supply curves
    cspcap = name_gdxcols(gdxpds.to_dataframe(gdxin, 'CSP2G')['CSP2G'])
    cspcost = name_gdxcols(gdxpds.to_dataframe(gdxin, 'CSP2GPTS')['CSP2GPTS'])

    ### need to match formatting from before
    cspcap = cspcap.pivot(index=['i','j'], columns='k').fillna(0)
    cspcost = cspcost.pivot(index=['i','j'], columns='k').fillna(0)

#%% 2018
if supplycurve == '2018':
    print("using 2018 version of wind, upv, and dupv supply cost curves")

    dupvcost = pd.read_csv(scdir + 'DUPV_supply_curves_cost_2018.csv')
    upvcost = pd.read_csv(scdir + 'UPV_supply_curves_cost_2018.csv')
    windcost = pd.read_csv(scdir + 'wind_supply_curves_cost_2018.csv')

    dupvcap = pd.read_csv(scdir + 'DUPV_supply_curves_capacity_2018.csv')
    upvcap = pd.read_csv(scdir + 'UPV_supply_curves_capacity_2018.csv')
    windcap = pd.read_csv(scdir + 'wind_supply_curves_capacity_2018.csv')

    ### now using the 2018 csv files for CSP
    cspcap = pd.read_csv(scdir + 'CSP_supply_curves_capacity_2018.csv').fillna(0)
    cspcost = pd.read_csv(scdir + 'CSP_supply_curves_cost_2018.csv').fillna(0)

#%% Add capacity to supply curve to accomodate the max of existing + prescriptive 
### onshore capacity, accounting for retirements
### First load existing capacity as of 2010. 
### Assign this capacity to 2009 for cumulative sum purposes
existing_wind = gdxpds.to_dataframe(gdxin, 'tmpWTOi')['tmpWTOi'].rename(
    columns={'*':'region','Value':'capacity'})
existing_wind['year'] = 2009
### Now load prescriptive wind builds post 2010
prescriptive_wind = gdxpds.to_dataframe(
    gdxinprescribe, 'PrescriptiveBuildsWind')['PrescriptiveBuildsWind']
prescriptive_wind.columns = ['year','region','type','capacity']
prescriptive_wind = prescriptive_wind.loc[prescriptive_wind.type=='wind-ons'].copy()
prescriptive_wind.drop('type', axis=1, inplace=True)
### Combine prescriptive and existing builds to calculate total cumulative builds
total_wind_builds = pd.concat([existing_wind, prescriptive_wind])
total_wind_builds = total_wind_builds.pivot(
    index='year',columns='region',values='capacity').fillna(0).cumsum()
total_wind_builds = pd.melt(
    total_wind_builds, ignore_index=False, value_name='built_capacity').reset_index()

#%% Load retired capacity and calculate total cumulative retirements
retire_wind = gdxpds.to_dataframe(gdxinretire, 'WindRetireExisting')['WindRetireExisting']
retire_wind.columns = ['region','type','year','capacity']
retire_wind = retire_wind.loc[retire_wind.type=='wind-ons'].copy()
retire_wind.drop('type', axis=1, inplace=True)
retire_wind = (
    retire_wind.pivot(index='year', columns='region', values='capacity')
    .fillna(0).cumsum().stack().rename('retired_capacity').reset_index()
)
#%% Combine cumulative builds and cumulative retirements to calculate cumulative 
### capacity by region and year. Use left join because we don't care about years 
### after the last build because capacity will only go down.
cumulative_wind = total_wind_builds.merge(retire_wind, on=['region','year'], how='left').fillna(0)
cumulative_wind['capacity'] = cumulative_wind.built_capacity - cumulative_wind.retired_capacity
#%% Get the max forced wind capacity by region
max_wind = (
    cumulative_wind.groupby('region')['capacity'].max().rename('forced_capacity').reset_index())
#%% Now find the available onshore wind by region from the supply curve and 
### compare to the forced wind
available_onshore = windcap.loc[windcap.type=='wind-ons'].copy()
available_onshore['capacity'] = available_onshore.drop(['region','class','type'],1).sum(1)
available_onshore = (
    available_onshore.groupby('region')['capacity'].sum()
    .rename('available_capacity').reset_index())
#%% Take the difference between available and forced capacity and identify shortfalls
wind_diff = available_onshore.merge(max_wind, on='region', how='left').fillna(0)
wind_diff['diff_capacity'] = wind_diff.available_capacity - wind_diff.forced_capacity
wind_shortfalls = wind_diff.loc[wind_diff.diff_capacity < 0].copy()
#%% If we have more forced capacity than available capacity in a region, add the difference 
### to the best class/bin of windcap, with an additional 1 kW just to make sure.
if len(wind_shortfalls) > 0:
    print('Adjusting onshore wind supply curve to accomodate forced capacity. '
          'Here are the shortfalls:\n{}'.format(wind_shortfalls))
    ### Use windcap and reduce to onshore and just one class for each region. Because 
    ### rownames are preserved, we can use them to modify the appropriate elements of windcap.
    windcapons = windcap.copy()
    windcapons['class'] = windcapons['class'].map(lambda x: int(x.lstrip('class')))
    windcapons = windcapons.loc[windcapons['type'] == 'wind-ons'].copy()
    ### Sorting by region/class and then removing duplicates does the trick for selecting 
    ### best class for a region
    windcapons = windcapons.sort_values('class').drop_duplicates(subset=['region'], keep='first')
    ### Overwrite the supply curve for the shortfall regions
    for row in wind_shortfalls.index:
        windcaponshort = windcapons.loc[windcapons.region==wind_shortfalls.loc[row,'region']]
        wcrow = windcaponshort.index[0]
        windcap.loc[wcrow,"wsc1"] = (
            windcap.loc[wcrow,"wsc1"] - wind_shortfalls.loc[row, "diff_capacity"] + .001)

#%% Reformat the supply curve dataframes
### Non-wind bins
bins = list(range(1, numbins_other + 1))
bincols = ['bin{}'.format(i) for i in bins]
### Onshore wind bins (flexible)
bins_wind = list(range(1, numbins_wind + 1))
bincols_wind = ['bin{}'.format(i) for i in bins_wind]

rcolnames = {'Unnamed: 0':'r', 'Unnamed: 1':'class'}
scolnames = {'Unnamed: 0':'s', 'Unnamed: 1':'class'}

dupvcap.rename(
    columns={**rcolnames, **{'dupvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
upvcap.rename(
    columns={**rcolnames, **{'upvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
cspcap.rename(
    columns={**scolnames, **{'cspsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)

dupvcost.rename(
    columns={**rcolnames, **{'dupvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
upvcost.rename(
    columns={**rcolnames, **{'upvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
cspcost.rename(
    columns={**scolnames, **{'cspsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)

### Note: wind capacity and costs also differentiate between 'class' and 'tech'
windcap.rename(
    columns={
        **{'region':'s', 'type':'tech', 
           'Unnamed: 0':'s', 'Unnamed: 1':'class', 'Unnamed 2': 'tech'},
        **{'wsc{}'.format(i): 'bin{}'.format(i) for i in bins_wind}}, 
    inplace=True)
windcost.rename(
    columns={
        **{'region':'s', 'type':'tech',
           'Unnamed: 0':'s', 'Unnamed: 1':'class', 'Unnamed 2': 'tech'},
        **{'wsc{}'.format(i): 'bin{}'.format(i) for i in bins_wind}}, 
    inplace=True)

dupvcap['tech'] = 'dupv'
upvcap['tech'] = 'upv'

dupvcost['tech'] = 'dupv'
upvcost['tech'] = 'upv'

#%% Duplicate the CSP supply curve for each CSP class
cspcap = (
    pd.concat({'csp{}'.format(i): cspcap for i in range(1,csp_configs+1)}, axis=0)
    .reset_index(level=0).rename(columns={'level_0':'tech'}).reset_index(drop=True))
cspcost = (
    pd.concat({'csp{}'.format(i): cspcost for i in range(1,csp_configs+1)}, axis=0)
    .reset_index(level=0).rename(columns={'level_0':'tech'}).reset_index(drop=True))

#%% Combine the supply curves; CSP/wind together (s) and UPV/DUPV together (r)
scap = pd.concat([windcap, cspcap])
scost = pd.concat([windcost, cspcost])

rcap = pd.concat([upvcap, dupvcap])
rcost = pd.concat([upvcost, dupvcost])

scap['class'] = scap['class'].map(lambda x: x.lstrip('cspclass'))
scap['class'] = scap['class'].map(lambda x: x.lstrip('class'))
scost['class'] = scost['class'].map(lambda x: x.lstrip('cspclass'))
scost['class'] = scost['class'].map(lambda x: x.lstrip('class'))

rcap['class'] = rcap['class'].map(lambda x: x.lstrip('class'))
rcost['class'] = rcost['class'].map(lambda x: x.lstrip('class'))

rcap['s'] = 'sk'
rcost['s'] = 'sk'

scap['s'] = 's' + scap.s.astype(str)
scost['s'] = 's' + scost.s.astype(str)

scap = scap.merge(rsnew, on='s')
scost = scost.merge(rsnew, on='s')

scap['var'] = 'cap'
scost['var'] = 'cost'
rcap['var'] = 'cap'
rcost['var'] = 'cost'

#%% Combine everything
alloutcap = pd.concat([scap, rcap])
alloutcost = pd.concat([scost, rcost])

alloutcap['class'] = 'class' + alloutcap['class'].astype(str)
t1 = alloutcap.pivot(
    index=['r','s','tech','var'], columns='class', 
    values=[c for c in alloutcap.columns if c.startswith('bin')]).reset_index()
### Concat the multi-level column names to a single level
t1.columns = ['_'.join(i).strip('_') for i in t1.columns.tolist()]

t2 = t1.merge(tout, on=['s','r','tech'], how='outer').fillna(0)

#%% Subset to single-tech curves
wndonst2 = t2.loc[t2.tech=="wind-ons"].copy()
wndofst2 = t2.loc[t2.tech=="wind-ofs"].copy()
cspt2 = t2.loc[t2.tech.isin(['csp{}'.format(i) for i in range(1,csp_configs+1)])]
upvt2 = t2.loc[t2.tech=="upv"].copy()
dupvt2 = t2.loc[t2.tech=="dupv"].copy()

#%% In the following loops, the order of each technology is specified
### from least-to-most expensive in terms of capacity. The amount of existing
### capacity is deducted from the best bin, computed as [bin capacity available] minus [existing]
### if existing exceeds the bin's capacity, the residual amount is stored in temp
### and that bin's capacity is set to zero. The example is notated in the wind bin
### calculations then repeated for other technologies

binopt = list(range(1, numbins_other + 1))
binopt_wind = list(range(1, numbins_wind + 1))

### Class order. For wind, lower class is better resource; for PV and CSP it's reversed
ordwnd = list(range(1,16))
ordcsp = list(range(1,6))[::-1]
ordpv = list(range(1,10))[::-1]

#%% Deduct if desired
if deduct:
    ### Wind
    for i in ordwnd:
        for j in binopt_wind:
            yn = 'bin{}_class{}'.format(j,i)

            wndonst2['temp'] = wndonst2[yn] - wndonst2.exist
            ### If existing is greater than the bin/class combo, temp is less than zero
            ### the remaining existing amount (to be subtracted off the next class/bin combo) 
            ### is the absolute value of the remainder
            wndonst2.loc[wndonst2.temp<0, 'exist'] = abs(wndonst2.loc[wndonst2.temp<0, 'temp'])
            ### The remaining amount in that class/bin combo is zero
            wndonst2.loc[wndonst2.temp<0, yn] = 0

            ### If existing is less than the bin/class combo, temp is greater than zero
            ### The remaining existing amount (to be subtracted off the next class/bin combo) 
            ### is the absolute value of the remainder
            wndonst2.loc[wndonst2.temp>=0, 'exist'] = 0
            ### The remaining amount in that class/bin combo is the temp
            wndonst2.loc[wndonst2.temp>=0, yn] = wndonst2.loc[wndonst2.temp>=0, 'temp']

    ### CSP
    for i in ordcsp:
        for j in binopt:
            yn = 'bin{}_class{}'.format(j,i)
            cspt2['temp'] = cspt2[yn] - cspt2.exist
            cspt2.loc[cspt2.temp<0, 'exist'] = abs(cspt2.loc[cspt2.temp<0, 'temp'])
            cspt2.loc[cspt2.temp<0, yn] = 0
            cspt2.loc[cspt2.temp>=0, 'exist'] = 0
            cspt2.loc[cspt2.temp>=0, yn] = cspt2.loc[cspt2.temp>=0, 'temp']

    ### PV
    for i in ordpv:
        for j in binopt:
            yn = 'bin{}_class{}'.format(j,i)
            upvt2['temp'] = upvt2[yn] - upvt2.exist
            upvt2.loc[upvt2.temp<0, 'exist'] = abs(upvt2.loc[upvt2.temp<0, 'temp'])
            upvt2.loc[upvt2.temp<0, yn] = 0
            upvt2.loc[upvt2.temp>=0, 'exist'] = 0
            upvt2.loc[upvt2.temp>=0, yn] = upvt2.loc[upvt2.temp>=0, 'temp']

            dupvt2['temp'] = dupvt2[yn] - dupvt2.exist
            dupvt2.loc[dupvt2.temp<0, 'exist'] = abs(dupvt2.loc[dupvt2.temp<0, 'temp'])
            dupvt2.loc[dupvt2.temp<0, yn] = 0
            dupvt2.loc[dupvt2.temp>=0, 'exist'] = 0
            dupvt2.loc[dupvt2.temp>=0, yn] = dupvt2.loc[dupvt2.temp>=0, 'temp']
    
    wndofst2['temp'] = 0

#%% Get the combined outputs
outcap = pd.concat([wndonst2, wndofst2, upvt2, dupvt2, cspt2])

moutcap = pd.melt(outcap, id_vars=['s','r','tech','var'])
moutcap = moutcap.loc[~moutcap.variable.isin(['exist','temp'])].copy()

moutcap['bin'] = moutcap.variable.map(lambda x: x.split('_')[0])
moutcap['class'] = moutcap.variable.map(lambda x: x.split('_')[1].lstrip('class'))
outcols = ['s','r','tech','var','bin','class','value']
moutcap = moutcap.loc[moutcap.value != 0, outcols].copy()

outcapfin = moutcap.pivot(
    index=['s','r','tech','var','class'], columns='bin', values='value'
).fillna(0).reset_index()

allout = pd.concat([outcapfin, alloutcost])
allout['tech'] = allout['tech'] + '_' + allout['class'].astype(str)


#%%###############
### Hydropower ###

### Adding hydro costs and capacity separate as it does not 
### require the calculations to reduce capacity by existing amounts.
### Goal  here is to acquire a data frame that matches the format
### of alloutm so that we can simply stack the two.

hydcap = pd.read_csv(scdir + 'hydcap.csv')
hydcost = pd.read_csv(scdir + 'hydcost.csv')

hydcap = pd.melt(hydcap, id_vars=['tech','class'])
hydcost = pd.melt(hydcost, id_vars=['tech','class'])

hydcap['var'] = 'cap'
hydcost['var'] = 'cost'

hyddat = pd.concat([hydcap, hydcost])
hyddat['s'] = 'sk'
hyddat['bin'] = hyddat['class'].map(lambda x: x.replace('hydclass','bin'))
hyddat['class'] = hyddat['class'].map(lambda x: x.replace('hydclass',''))

hyddat.rename(columns={'variable':'r', 'bin':'variable'}, inplace=True)
hyddat = hyddat[['tech','r','value','var','s','variable']].fillna(0)


#%%#########################
### Pumped-hydro storage ###

phs_cap = name_gdxcols(gdxpds.to_dataframe(gdxPHS, 'PHSmax')['PHSmax'])
phs_cost = name_gdxcols(gdxpds.to_dataframe(gdxPHS, 'PHScostn')['PHScostn'])

phs_cap['var'] = 'cap'
phs_cost['var'] = 'cost'

phs_out = pd.concat([phs_cap, phs_cost]).fillna(0).rename(columns={'j':'r'})
phs_out['tech'] = 'pumped-hydro'
phs_out['variable'] = phs_out.i.map(lambda x: x.replace('phsclass','bin'))
phs_out['s'] = 'sk'
phs_out = phs_out[hyddat.columns].copy()


#%%#######################
### Combine everything ###
### Stack the final versions

alloutm = pd.melt(allout, id_vars=['r','s','tech','var'])
alloutm = alloutm.loc[alloutm.variable != 'class'].copy()
alloutm = pd.concat([alloutm, hyddat, phs_out]).round(decimals)

### Create a label that GAMS can easily read
alloutf = alloutm.copy()
alloutf['label'] = (
    '('+alloutf.r+'.'+alloutf.s+'.'+alloutf.tech+'.'+alloutf.variable+'.'+alloutf['var']+')'
)
alloutf['value'] = alloutf['value'].astype(float).round(decimals).astype(str) + ','

## Add the opening and closing brackets: /.../;
alloutf = alloutf[['label','value']].reset_index(drop=True).copy()
alloutf.loc[0,'label'] = '/' + alloutf.loc[0,'label']
alloutf.iloc[-1,1] = alloutf.iloc[-1,1].replace(',','/;')


#%%############
### Biomass ###

bio_cap = name_gdxcols(gdxpds.to_dataframe(gdxBio, 'BioSupplyCurve')['BioSupplyCurve'])
bio_cost = name_gdxcols(gdxpds.to_dataframe(gdxBio, 'BioFeedstockPrice')['BioFeedstockPrice'])
bio_cap['var'] = 'cap'
bio_cost['var'] = 'cost'

bio_out = pd.concat([bio_cap, bio_cost])
bio_out = bio_out.pivot(index=['j','var'], columns=['i'], values='value').reset_index()

bio_ramp = name_gdxcols(gdxpds.to_dataframe(gdxBio, 'BioFeedstockRamp')['BioFeedstockRamp'])
bio_ramp = bio_ramp.pivot(index=['j'], columns=['i'], values='value').reset_index()


#%%###############
### Geothermal ###

geo_disc = pd.read_csv(
    os.path.join(inputsdir,'geothermal','geo_discovery_{}.csv'.format(geodiscov)))
geo_fom = pd.read_csv(
    os.path.join(inputsdir,'geothermal','geo_fom_{}.csv'.format(geosupplycurve)))
geo_rsc = pd.read_csv(
    os.path.join(inputsdir,'geothermal','geo_rsc_{}.csv'.format(geosupplycurve)))


#%%######################
### Write the outputs ###
alloutf.to_csv(inputs_case + 'rsc_combined.txt', index=False, header=False, quoting=3, sep=' ')
windcap.to_csv(inputs_case + 'wind_supply_curves_capacity.csv', index=False)
rsout.to_csv(inputs_case + 'rsout.csv')
bio_out.round(decimals).to_csv(inputs_case + 'bio_supplycurve.csv', index=False)
bio_ramp.round(decimals).to_csv(inputs_case + 'bio_priceramp.csv', index=False)
geo_disc.round(decimals).to_csv(inputs_case + 'geo_discovery.csv', index=False)
geo_fom.round(decimals).to_csv(inputs_case + 'geo_fom.csv', index=False)
geo_rsc.round(decimals).to_csv(inputs_case + 'geo_rsc.csv', index=False)

print('writesupplycurves.py completed successfully')
