#%% IMPORTS ###
import pandas as pd
import os
import argparse
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()

#%% Model Inputs
parser = argparse.ArgumentParser(description="""This file outputs capacity factor data""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("inputs_case", help="output directory")

args = parser.parse_args()
reeds_dir = args.reeds_dir
inputs_case = args.inputs_case

# #%% Inputs for testing
# reeds_dir = os.path.expanduser('~/github2/ReEDS-2.0/')
# inputs_case = os.path.join(
#     reeds_dir,'runs','v20221215_hourlycleanupM4_Pacific','inputs_case')

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

distpvscen = sw.distpvscen
GSw_IndividualSites = int(sw.GSw_IndividualSites)
GSw_SitingWindOns = sw.GSw_SitingWindOns
GSw_SitingWindOfs = sw.GSw_SitingWindOfs
GSw_SitingUPV = sw.GSw_SitingUPV
GSw_PVB = int(sw.GSw_PVB)
GSw_PVB_Types = (
    [int(i) for i in sw.GSw_PVB_Types.split('_')] if int(GSw_PVB)
    else []
)

#%% Procedure
print('Beginning calculations in cfgather.py')

# Read in set of valid regions
val_r = pd.read_csv(
        os.path.join(inputs_case, 'val_r.csv'), squeeze=True, header=None).tolist()
val_r_cap = pd.read_csv(
        os.path.join(inputs_case, 'val_r_cap.csv'), squeeze=True, header=None).tolist()

colid = ['i','j','k','l','m','n','o','p']

rs = pd.read_csv(os.path.join(inputs_case,'rsmap.csv')).rename(columns={'*r':'r'})
rs.columns = ['r','s']

rs = rs.loc[rs['r'].isin(val_r)]


###########
#Wind
###########
windons = pd.read_csv(
    os.path.join(
        reeds_dir, 'inputs', 'cf','wind-ons_cf_ts_{}-{}.csv'
    .format('site' if GSw_IndividualSites else 'sreg', GSw_SitingWindOns))
).drop('cfsigma', axis=1, errors='ignore').assign(type='wind-ons')


#%% Offshore wind
windofs = pd.read_csv(
    os.path.join(
        reeds_dir, 'inputs', 'cf','wind-ofs_cf_ts_{}-{}.csv'
    .format('site' if GSw_IndividualSites else 'sreg', GSw_SitingWindOfs))
).drop('cfsigma', axis=1, errors='ignore').assign(type='wind-ofs')

wind = pd.concat([windons,windofs])
wind['tech'] = wind['type'] + '_' + wind['class'].astype(str)
wind['class'] = 'class' + wind['class'].astype(str)
wind.columns = ['r','cl','h','value','it','i']
wind = wind[['r','i','h','value']]

##############
#UPV
##############

upv = (
    pd.read_csv(os.path.join(reeds_dir,'inputs','cf','upv_cf_ts-{}.csv'.format(GSw_SitingUPV)))
    .rename(columns={'region':'r','timeslice':'h','class':'i','cfmean':'value'})
    .drop('cfsigma', axis=1, errors='ignore')
)
upv.i = upv.i.map(lambda x: 'upv_{}'.format(x))
upv = upv.drop(upv.loc[upv.value==0].index).reset_index(drop=True)

#############
#DUPV
#############

dupv = pd.read_csv(os.path.join(reeds_dir,'inputs','cf','cf_dupv.csv'))

#############
#distpv
#############

distpv = pd.read_csv(
    os.path.join(reeds_dir,'inputs','dGen_Model_Inputs',distpvscen,'distPVCF_'+distpvscen+'.csv')
).rename(columns = {'Unnamed: 0':'r'})

distpv = distpv.melt('r')
distpv.columns = ['r','h','value']
distpv['i'] = 'distpv'
distpv = distpv[['r','i','h','value']]


#####################
#%% Hybrid PV+battery
#####################

### Get the PVB types
pvb_ilr = pd.read_csv(
    os.path.join(inputs_case, 'pvb_ilr.csv'),
    header=0, names=['pvb_type','ilr'], index_col='pvb_type', squeeze=True)

pvb = {}
for pvb_type in GSw_PVB_Types:
    ilr = int(pvb_ilr['pvb{}'.format(pvb_type)] * 100)
    ### UPV uses ILR = 1.3, so use its AC profile if ILR = 1.3
    acfile = 'upv' if ilr == 130 else 'upv{}'.format(ilr)
    ### Get timeslice AC output
    pvb_cf_ac = (
        pd.read_csv(os.path.join(reeds_dir,'inputs','cf','{}_cf_ts-{}.csv'.format(
            acfile, GSw_SitingUPV)))
        .rename(columns={'region':'r','timeslice':'h','class':'i','cfmean':'value'})
        .set_index(['r','i','h'])['value']
    )
    ### Get timeslice clipping (given as AC CF, i.e. after inverter losses are applied)
    pvb_cf_clipping = (
        pd.read_csv(os.path.join(reeds_dir,'inputs','cf','upv{}clip_cf_ts-{}.csv'.format(
            ### NOTE: We don't yet have clipping profiles for limited and open access
            ### from reV, so for now we use clipping from reference access for all PV
            ### siting scenarios. Once the open and limited clipping profiles are
            ### added, change 'reference' to GSw_SitingUPV in the next line.
            ilr, 'reference')))
        .rename(columns={'region':'r','timeslice':'h','class':'i','cfmean':'value'})
        .set_index(['r','i','h'])['value']
    )
    ### Sum the AC and clipping profiles and rename to match ReEDS usage
    pvb_cf = (
        pvb_cf_ac 
        + pvb_cf_clipping.to_frame().merge(
            pvb_cf_ac.to_frame()[[]],
            left_index=True, right_index=True,
            ### If there are any missing [r,i,h] values in the clipping file,
            ### set clipping to zero for those values
            how='right').fillna(0)['value']
    ).loc[pvb_cf_ac.index].reset_index()

    pvb_cf.i = pvb_cf.i.map(lambda x: 'PVB{}_{}'.format(pvb_type, x))
    pvb[pvb_type] = pvb_cf.drop(pvb_cf.loc[pvb_cf.value==0].index)

pvb = (
    pd.concat(pvb, axis=0, ignore_index=True) if GSw_PVB
    else pd.DataFrame(columns=['r','i','h','value']))

#############
#CSP
#############

#Read in tech-subset-table.csv to determine number of configureations
tst = pd.read_csv(os.path.join(reeds_dir,'inputs','tech-subset-table.csv'))
csp_configs = tst[(tst['CSP']=='YES') & (tst['STORAGE'] == 'YES')].shape[0]

# Note that in the most version, cf_csp_ws_tower (read from field_capacity_factor.csv file) has 
# already incorporated the availability factors (CFCSPws_adj_factor_tower and CSPws_avail_factor
# from Heritage ReEDS) so can directly read from cf_csp_ws_tower

# CF for CSP is from SAM modeling results, and assumes a solar multiple (SM) = 1.
# The solar multiple is applied in c_supplymodel.
csp_in = pd.read_csv(os.path.join(reeds_dir,'inputs','cf','cf_csp_ws_tower.csv'))

### Add profiles for each csp tech
csp = pd.concat([
    csp_in.assign(i=csp_in.i.str.replace('csp1',f'csp{i+1}')) for i in range(csp_configs)
], axis=0)

###### csp-ns
# Capacity factors for CSP-ns are developed using typical DNI year (TDY) hourly resource data
# (Habte et al. 2014) from 18 representative sites. The TDY weather files are processed through
# the CSP modules of SAM to develop performance characteristics for a system with a
# solar multiple of 1.4. These representative sites have an average DNI range of
# 7.25-7.5 kWh/m2/day (see "Class 3" in Table 4 of the ReEDS Model Documnetation: Version 2016).
# Habte, A., A. Lopez, M. Sengupta, and S. Wilcox. 2014. Temporal and Spatial Comparison of
# Gridded TMY, TDY, and TGY Data Sets. Golden, CO: National Renewable Energy Laboratory.
# http://www.osti.gov/scitech/biblio/1126297.
cf_cspns = pd.read_csv(
    os.path.join(reeds_dir,'inputs','cf','cf_cspns.csv'),
    header=None, names=['h','value'], index_col='h')
### Scale by availability
scalars = pd.read_csv(
    os.path.join(inputs_case,'scalars.csv'),
    header=None, names=['scalar','value','comment'], index_col='scalar')['value']
cf_cspns *= scalars['avail_cspns']
### All regions use the same CF for csp-ns
cspns = pd.concat({(r,'csp-ns'): cf_cspns for r in rs.s}, names=['r','i','h']).reset_index()

#######################
### Combine VRE CFs
#######################
allcf = pd.concat([wind,upv,dupv,distpv,pvb,csp,cspns])
allcf.h = allcf.h.str.lower()
allcf = (
    ## Filter for valid regions
    allcf.loc[allcf.r.isin(val_r_cap)]
    .rename(columns={'i':'*i','value':'cf'})
    [['*i','r','h','cf']]
).copy()

#######################
#Hydro mingen
#######################

hydro = pd.read_csv(os.path.join(reeds_dir,'inputs','cf','hydro_mingen.csv'))

# Filter for valid regions
hydro = hydro.loc[hydro['r'].isin(val_r)]

hydro = hydro.pivot_table(index =['i','r'],columns = 'szn',values = 'value').fillna(0).reset_index()
hydro = hydro.round(8)

#%% Save the outputs
print('writing capacity factor data to: '+inputs_case)
allcf.round(6).to_csv(os.path.join(inputs_case,'cf_vre.csv'), index=False)
hydro.to_csv(os.path.join(inputs_case,'hydmin.csv'),index=False)

toc(tic=tic, year=0, process='input_processing/cfgather.py', 
    path=os.path.join(inputs_case,'..'))
