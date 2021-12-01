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
# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()

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
parser.add_argument('-dr', '--drscen', default='none',
                    help='DR Supply Curve')
parser.add_argument('-e', '--geodiscov', default='BAU',
                    help='Annual discover rates for new geothermal sites')
parser.add_argument('-n', '--numbins_windons', type=int, default=5,
                    help='Number of interconnection supply curve bins for onshore wind')
parser.add_argument('-c', '--numbins_windofs', type=int, default=5,
                    help='Number of interconnection supply curve bins for offshore wind')
parser.add_argument('-x', '--GSw_IndividualSites', type=int, default=1, 
                    choices=[0,1], help='Switch to use individual sites')
parser.add_argument('-psh', '--pshsupplycurve', default='10hr_15bin_wcontingency',
                    help='PSH Supply Curve')                    
parser.add_argument('-b', '--numbins_upv', type=int, default=5,
                    help='Number of interconnection supply curve bins for upv')
parser.add_argument('-w', '--GSw_SitingWindOns', type=str, default='reference',
                    choices=['reference','open','limited'],
                    help='siting access scenario for onshore wind')
parser.add_argument('-f', '--GSw_SitingWindOfs', type=str, default='open',
                    choices=['open','limited'],
                    help='siting access scenario for offshore wind')
parser.add_argument('-p', '--GSw_SitingUPV', type=str, default='reference',
                    choices=['reference','open','limited'],
                    help='siting access scenario for UPV')
parser.add_argument('-y', '--end_year', type=int, default=2050,
                    help="End year for data model")

args = parser.parse_args()
basedir = args.basedir
unitdata = args.unitdata
deduct = args.deduct
supplycurve = args.supplycurve
inputs_case = os.path.join(args.inputs_case, '')
geosupplycurve = args.geosupplycurve
drsupplycurve = args.drscen
geodiscov = args.geodiscov
numbins_windons = args.numbins_windons
numbins_windofs = args.numbins_windofs
end_year = args.end_year
GSw_IndividualSites = args.GSw_IndividualSites
pshsupplycurve = args.pshsupplycurve
numbins_upv = args.numbins_upv
GSw_SitingWindOns = args.GSw_SitingWindOns
GSw_SitingWindOfs = args.GSw_SitingWindOfs
GSw_SitingUPV = args.GSw_SitingUPV

#%%#################
### FIXED INPUTS ###
### Number of bins used for everything other than wind-ons
numbins_other = 5
### Rounding precision
decimals = 7

# #%%#########################
# ### Settings for testing ###
# basedir = os.path.expanduser('~/github2/ReEDS-2.0/')
# unitdata = 'EIA-NEMS'
# deduct = 0
# supplycurve = 'default'
# inputs_case = os.path.join(basedir,'runs','v20210816_PVsitesM0_RefSites_ERCOT','inputs_case','')
# geosupplycurve = 'ATB_2020'
# geodiscov = 'BAU'
# numbins_windons = 5
# numbins_windofs = 5
# GSw_IndividualSites = 0
# pshsupplycurve = '10hr_15bin_wcontingency'
# numbins_upv = 1300
# GSw_SitingWindOns = 'reference'
# GSw_SitingWindOfs = 'open'
# GSw_SitingUPV = 'reference'
# pshsupplycurve = '10hr_15bin_wcontingency'

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
### Set inputs and supplycurvedata paths for convenience
inputsdir = os.path.join(basedir,'inputs','')
scdir = os.path.join(inputsdir,'supplycurvedata','')

#%% Read in tech-subset-table.csv to determine number of csp configurations
tech_subset_table = pd.read_csv(os.path.join(inputsdir, "tech-subset-table.csv"))
csp_configs = tech_subset_table.loc[
    (tech_subset_table.CSP== 'YES' ) & (tech_subset_table.STORAGE == 'YES')].shape[0]

#%% Read the r-to-s map
rsnew = pd.read_csv(os.path.join(inputs_case, 'rsmap.csv')).rename(columns={'*r':'r','rs':'s'})

# Read in dollar year conversions for RSC data
dollaryear = pd.read_csv(os.path.join(scdir, 'dollaryear.csv'))
deflator = pd.read_csv(os.path.join(inputsdir,"deflator.csv"))
deflator.columns = ["Dollar.Year","Deflator"]
dollaryear = dollaryear.merge(deflator,on="Dollar.Year",how="left").set_index('Scenario')

#%% Load the existing wind and CSP units
twnd = name_gdxcols(gdxpds.to_dataframe(gdxin,'tmpWTOi')['tmpWTOi'])
tcsp = name_gdxcols(gdxpds.to_dataframe(gdxin,'tmpCSPOct')['tmpCSPOct'])
### Fix the region labels
twnd.i = 's' + twnd.i.astype(float).astype(int).astype(str)
tcsp.i = 's' + tcsp.i.astype(float).astype(int).astype(str)
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

    if GSw_IndividualSites:
        windons = pd.read_csv(scdir + 'wind-ons_supply_curve_site-{}.csv'.format(GSw_SitingWindOns))
        windofs = pd.read_csv(scdir + 'wind-ofs_supply_curve_site-{}.csv'.format(GSw_SitingWindOfs))
        ### Drop sites with zero capacity
        windons = windons.loc[windons.capacity > 0].reset_index(drop=True)
        windofs = windofs.loc[windofs.capacity > 0].reset_index(drop=True)
    else:
        windons = pd.read_csv(
            scdir + 'wind-ons_supply_curve_sreg{}bin-{}.csv'.format(numbins_windons, GSw_SitingWindOns))
        windofs = pd.read_csv(
            scdir + 'wind-ofs_supply_curve_sreg{}bin-{}.csv'.format(numbins_windofs, GSw_SitingWindOfs))
    windons['type'] = 'wind-ons'
    windofs['type'] = 'wind-ofs'
    # Convert dollar year
    windons['supply_curve_cost_per_mw'] *= dollaryear.loc['wind-ons_supply_curve']['Deflator']
    windofs['supply_curve_cost_per_mw'] *= dollaryear.loc['wind-ofs_supply_curve']['Deflator']

    windall = pd.concat([windons, windofs], axis=0)
    windall['class'] = 'class' + windall['class'].astype(str)
    windall['bin'] = 'wsc' + windall['bin'].astype(str)
    ### Pivot, with bins in long format
    windcost = (
        windall.pivot(index=['region','class','type'], columns='bin', values='supply_curve_cost_per_mw')
        .fillna(0).reset_index())
    windcap = (
        windall.pivot(index=['region','class','type'], columns='bin', values='capacity')
        .fillna(0).reset_index())

    upv_in = pd.read_csv(scdir + 'upv_supply_curve_{}bin-{}.csv'.format(numbins_upv,GSw_SitingUPV))
    upv_in['class'] = 'class' + upv_in['class'].astype(str)
    upv_in['bin'] = 'upvsc' + upv_in['bin'].astype(str)
    ### Pivot, with bins in long format
    upvcost = (
        upv_in.pivot(columns='bin',values='supply_curve_cost_per_mw',index=['region','class'])
        .fillna(0).reset_index())
    upvcap = (
        upv_in.pivot(columns='bin',values='capacity',index=['region','class'])
        .fillna(0).reset_index())

    dupvcost = pd.read_csv(scdir + 'DUPV_supply_curves_cost_2018.csv')
    dupvcap = pd.read_csv(scdir + 'DUPV_supply_curves_capacity_2018.csv')

    cspcap = pd.read_csv(scdir + 'CSP_supply_curves_capacity_2018.csv').fillna(0)
    cspcost = pd.read_csv(scdir + 'CSP_supply_curves_cost_2018.csv').fillna(0)

    # Convert dollar years
    dupvcost[dupvcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['DUPV_supply_curves_cost_2018']['Deflator']
    upvcost[upvcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['UPV_supply_curves_cost_2018']['Deflator']
    cspcost[[c for c in cspcost.select_dtypes(include=['number']).columns if c!='Unnamed: 0']] \
        *= dollaryear.loc['CSP_supply_curves_cost_2018']['Deflator']

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

    # Convert dollar years
    dupvcost[dupvcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['DUPV_supply_curves_cost']['Deflator']
    upvcost[upvcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['UPV_supply_curves_cost']['Deflator']
    windcost[[c for c in windcost.select_dtypes(include=['number']).columns if c!='Unnamed: 0']] \
        *= dollaryear.loc['wind_supply_curves_cost']['Deflator']
    cspcost[cspcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['CSP2GPTS']['Deflator']

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

    # Convert dollar years
    dupvcost[dupvcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['DUPV_supply_curves_cost_NARIS']['Deflator']
    upvcost[upvcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['UPV_supply_curves_cost_NARIS']['Deflator']
    windcost[[c for c in windcost.select_dtypes(include=['number']).columns if c!='Unnamed: 0']] \
        *= dollaryear.loc['wind_supply_curves_cost_NARIS']['Deflator']
    cspcost[cspcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['CSP2GPTS']['Deflator']

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

    # Convert dollar years
    dupvcost[dupvcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['DUPV_supply_curves_cost_2018']['Deflator']
    upvcost[upvcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['UPV_supply_curves_cost_2018']['Deflator']
    windcost[[c for c in windcost.select_dtypes(include=['number']).columns if c!='Unnamed: 0']] \
        *= dollaryear.loc['wind_supply_curves_cost_2018']['Deflator']
    cspcost[[c for c in cspcost.select_dtypes(include=['number']).columns if c!='Unnamed: 0']] \
        *= dollaryear.loc['CSP_supply_curves_cost_2018']['Deflator']


#%% Reformat the supply curve dataframes
### Non-wind bins
bins = list(range(1, numbins_other + 1))
bincols = ['bin{}'.format(i) for i in bins]
### Onshore wind bins (flexible)
bins_wind = list(range(1, numbins_windons + 1))
bincols_wind = ['bin{}'.format(i) for i in bins_wind]
### UPV bins (flexible)
bins_upv = list(range(1, numbins_upv + 1))
bincols_upv = ['bin{}'.format(i) for i in bins_upv]

rcolnames = {'Unnamed: 0':'r', 'region':'r', 'Unnamed: 1':'class'}
scolnames = {'Unnamed: 0':'s', 'Unnamed: 1':'class'}

dupvcap.rename(
    columns={**rcolnames, **{'dupvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
upvcap.rename(
    columns={**rcolnames, **{'upvsc{}'.format(i): 'bin{}'.format(i) for i in bins_upv}}, inplace=True)
cspcap.rename(
    columns={**scolnames, **{'cspsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)

dupvcost.rename(
    columns={**rcolnames, **{'dupvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
upvcost.rename(
    columns={**rcolnames, **{'upvsc{}'.format(i): 'bin{}'.format(i) for i in bins_upv}}, inplace=True)
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
### Fix region names
cspcap.s = 's' + cspcap.s.astype(str)
cspcost.s = 's' + cspcost.s.astype(str)

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

# Convert dollar year
hydcost[hydcost.select_dtypes(include=['number']).columns] *= dollaryear.loc['hydcost']['Deflator']

hydcap['var'] = 'cap'
hydcost['var'] = 'cost'

hyddat = pd.concat([hydcap, hydcost])
hyddat['s'] = 'sk'
hyddat['bin'] = hyddat['class'].map(lambda x: x.replace('hydclass','bin'))
hyddat['class'] = hyddat['class'].map(lambda x: x.replace('hydclass',''))

hyddat.rename(columns={'variable':'r', 'bin':'variable'}, inplace=True)
hyddat = hyddat[['tech','r','value','var','s','variable']].fillna(0)


#%%#########################
### Pumped Storage Hydropower###
# Input processing currently assumes that cost data in CSV file is in 2004$

psh_cap = pd.read_csv(scdir + 'PSH_supply_curves_capacity_{}.csv'.format(pshsupplycurve))
psh_cost = pd.read_csv(scdir + 'PSH_supply_curves_cost_{}.csv'.format(pshsupplycurve))
psh_cap.rename(columns={psh_cap.columns[0]:'r'}, inplace=True)
psh_cost.rename(columns={psh_cost.columns[0]:'r'}, inplace=True)

psh_cap = pd.melt(psh_cap, id_vars=['r'])
psh_cost = pd.melt(psh_cost, id_vars=['r'])

# Convert dollar year
psh_cost[psh_cost.select_dtypes(include=['number']).columns] *= dollaryear.loc['PHScostn']['Deflator']

psh_cap['var'] = 'cap'
psh_cost['var'] = 'cost'

psh_out = pd.concat([psh_cap, psh_cost]).fillna(0)
psh_out['tech'] = 'pumped-hydro'
psh_out['variable'] = psh_out.variable.map(lambda x: x.replace('phsclass','bin'))
psh_out['s'] = 'sk'
psh_out = psh_out[hyddat.columns].copy()


#%%####################
### Demand Response ###

dr_rsc = pd.read_csv(
    os.path.join(inputsdir,'demand_response','dr_rsc_{}.csv'.format(drsupplycurve)),
    header=None, names=['r','tech','variable','year','var','value'])
# Convert dollar year
dr_rsc.loc[dr_rsc['var']=='Cost', 'value'] *= dollaryear.loc['dr_rsc_{}'.format(drsupplycurve)]['Deflator']
dr_rsc['s'] = 'sk'


#%%#######################
### Combine everything ###
### Stack the final versions
alloutm = pd.melt(allout, id_vars=['r','s','tech','var'])
alloutm = alloutm.loc[alloutm.variable != 'class'].copy()
alloutm = pd.concat([alloutm, hyddat, psh_out]).round(decimals)

### Drop the (cap,cost) entries with nan cost
alloutm = (
    alloutm
    .pivot(index=['r','s','tech','variable'], columns=['var'], values=['value'])
    .dropna()['value']
    .reset_index()
    .melt(id_vars=['r','s','tech','variable'])
    [alloutm.columns]
)

# Duplicate or interpolate data for all years between start (assumed 2010) and
# end year. Currently (as of 05-2021) only DR has yearly supply data
yrs = pd.DataFrame(list(range(2010, end_year+1)), columns=['year'])
yrs['tmp'] = 1

alloutf = pd.DataFrame()
for dat in [alloutm, dr_rsc]:
    if 'year' in dat.columns:
        # Get all years for all parts of data
        tmp = dat[[c for c in dat.columns if c not in ['year','value']]].drop_duplicates()
        tmp['tmp'] = 1
        tmp = pd.merge(tmp,yrs, on='tmp').drop('tmp',axis=1)
        tmp = pd.merge(tmp, dat, how='outer', on=list(tmp.columns))
        # Interpolate between years that exist using a linear spline interpolation
        # extrapolating any values at the beginning or end as required
        # Include all years here then filter later to get spline correct if data
        # covers more than the years modeled
        dat = (tmp
               .groupby([c for c in tmp.columns if c not in ['value','year']])
               .apply(lambda group: group.interpolate(limit_direction='both',
                                                      method='slinear',
                                                      fill_value='extrapolate'))
               )
        dat = dat[dat.year.isin(yrs.year)]
        # Ensure no values are < 0
        dat['value'].clip(lower=0, inplace=True)
    else:
        dat['tmp'] = 1
        dat = pd.merge(dat, yrs, on='tmp').drop('tmp', axis=1)
    alloutf = pd.concat([alloutf, dat])

alloutf['year'] = alloutf['year'].astype(str)

### Create a label that GAMS can easily read
alloutf['label'] = (
    '('+alloutf.r+'.'+alloutf.s+'.'+alloutf.tech+'.'+alloutf.year+'.'+alloutf.variable+'.'+alloutf['var']+')'
)
alloutf['value'] = alloutf['value'].astype(float).round(decimals).astype(str) + ','

## Add the opening and closing brackets: /.../;
alloutf = alloutf[['label','value']].reset_index(drop=True).copy()
alloutf.loc[0,'label'] = '/' + alloutf.loc[0,'label']
alloutf.iloc[-1,1] = alloutf.iloc[-1,1].replace(',','/;')


#%%############
### Biomass ###

# Note that biomass is currently being handled directly in b_inputs.gms

#%%###############
### Geothermal ###

geo_disc = pd.read_csv(
    os.path.join(inputsdir,'geothermal','geo_discovery_{}.csv'.format(geodiscov)))
geo_fom = pd.read_csv(
    os.path.join(inputsdir,'geothermal','geo_fom_{}.csv'.format(geosupplycurve)))
geo_rsc = pd.read_csv(
    os.path.join(inputsdir,'geothermal','geo_rsc_{}.csv'.format(geosupplycurve)),
    header=None)
# Convert dollar year
geo_rsc.loc[geo_rsc[2]=='Cost', 3] *= dollaryear.loc['geo_rsc_{}'.format(geosupplycurve)]['Deflator']

#%%######################
### Write the outputs ###
alloutf.to_csv(inputs_case + 'rsc_combined.txt', index=False, header=False, quoting=3, sep=' ')
windcap.to_csv(inputs_case + 'wind_supply_curves_capacity.csv', index=False)
geo_disc.round(decimals).to_csv(inputs_case + 'geo_discovery.csv', index=False)
geo_fom.round(decimals).to_csv(inputs_case + 'geo_fom.csv', index=False)
geo_rsc.round(decimals).to_csv(inputs_case + 'geo_rsc.csv', index=False, header=False)

toc(tic=tic, year=0, process='input_processing/writesupplycurves.py',
    path=os.path.join(inputs_case,'..'))
print('writesupplycurves.py completed successfully')
