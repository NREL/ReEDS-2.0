#%% IMPORTS ###
import gdxpds
import pandas as pd
import os
import argparse
#%% direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()

#%% Model Inputs
parser = argparse.ArgumentParser(description="""This file outputs capacity factor data""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("inputs_case", help="output directory")

args = parser.parse_args()
reeds_dir = args.reeds_dir
inputs_case = args.inputs_case

#%% Inputs for testing
# reeds_dir = os.path.expanduser('~/github2/ReEDS-2.0/')
# inputs_case = os.path.join(reeds_dir,'runs','v20210630_pvbdc1_Ref_ERCOT','inputs_case','')

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


colid = ['i','j','k','l','m','n','o','p']

gdxfile = os.path.join(reeds_dir,'inputs','cf','cfdata.gdx')
rs = pd.read_csv(os.path.join(inputs_case,'rsmap.csv')).rename(columns={'*r':'r'})
rs.columns = ['r','s']


###########
#Wind
###########
windons = pd.read_csv(
    os.path.join(
        reeds_dir, 'inputs', 'cf','wind-ons_cf_ts_{}-{}.csv'
    .format('site' if GSw_IndividualSites else 'sreg', GSw_SitingWindOns))
).drop('cfsigma', axis=1, errors='ignore')
windons['type'] = 'wind-ons'

#%% Offshore wind
windofs = pd.read_csv(
    os.path.join(
        reeds_dir, 'inputs', 'cf','wind-ofs_cf_ts_{}-{}.csv'
    .format('site' if GSw_IndividualSites else 'sreg', GSw_SitingWindOfs))
).drop('cfsigma', axis=1, errors='ignore')
windofs['type'] = 'wind-ofs'

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

dupv = gdxpds.to_dataframe(gdxfile,'CFDUPV')
dupv = pd.DataFrame(dupv['CFDUPV'])
dupv['c'] = 'dupv_' + dupv.k.str.strip('class')
dupv.columns = ['r','h','cl','value','i']
dupv = dupv[['r','i','h','value']]


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

# CFCspwStorallyears in heritage ReEDS is the adjusted CSP-ws field capacity factor from CFCSPws_tower;
# data for tower system starts from 2018 and are the same across years (no need for a year dimension)
# Note that in the most version, CFCSPws_tower (read from field_capacity_factor.csv file) has 
# already incorporated the availability factors (CFCSPws_adj_factor_tower and CSPws_avail_factor)
# so can directly read from CFCSPws_tower

# CF for CSP is from SAM modeling results, and assumes SM=1 (i.e. the numbers will need to be 
# multiplied by the actual SM of certain configurations)
csp = gdxpds.to_dataframe(gdxfile,'CFCSPws_tower')
csp = pd.DataFrame(csp['CFCSPws_tower'])
csp.columns = ['r','h','i','value']
csp['i'] = 'csp1_' + csp.i.str.strip('cspclass')
csp['r'] = 's' + csp['r']
csp = csp[['r','h','i','value']]

csp = csp.pivot_table(index=['r','i'], columns='h', values = 'value').fillna(0).reset_index()
csp['H5'] = 0
csp['H9'] = 0
csp1 = csp.copy()
for i in list(range(2,csp_configs+1)):
    config = 'csp'+str(i)
    csp_temp = csp1.copy()
    csp_temp.i = csp_temp.i.str.replace('csp1',config)
    csp = pd.concat([csp,csp_temp])
    
#Output writing
allcf = pd.concat([wind,upv,dupv,distpv,pvb])
allcf = allcf.pivot_table(index=['r','i'],columns='h',values='value').fillna(0).reset_index()
allcf = pd.concat([allcf,csp],sort=False)
allcf = allcf.round(8)
 
#######################
#Hydro mingen
#######################

hydro = gdxpds.to_dataframe(gdxfile,'minplantload_hy')
hydro = pd.DataFrame(hydro['minplantload_hy'])
hydro['j'] = hydro['j'].str[0:4]
hydro.columns = ['i','szn','r','value']
hydro = hydro.pivot_table(index =['i','r'],columns = 'szn',values = 'value').fillna(0).reset_index()

#%% Save the outputs
print('writing capacity factor data to: '+inputs_case)
allcf.to_csv(os.path.join(inputs_case,'cfout.csv'),index=False)
hydro.to_csv(os.path.join(inputs_case,'minhyd.csv'),index=False)

toc(tic=tic, year=0, process='input_processing/cfgather.py', 
    path=os.path.join(inputs_case,'..'))
