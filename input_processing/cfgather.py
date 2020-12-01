import pandas as pd
import os
import argparse
import gdxpds


# Model Inputs
parser = argparse.ArgumentParser(description="""This file outputs capacity factor data""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("distpvscen", help="distpv scenario")
parser.add_argument("outdir", help="output directory")

args = parser.parse_args()

reeds_dir = args.reeds_dir
distpvscen = args.distpvscen
outdir = args.outdir
#%%
#Inputs for testing
#reeds_dir = 'd:\\Danny_ReEDS\\ReEDS-2.0'
#distpvscen = 'StScen2019_Mid_Case'
#outdir = os.getcwd()

print('Beginning calculations in cfgather.py')


colid = ['i','j','k','l','m','n','o','p']

os.chdir(os.path.join(reeds_dir))

gdxfile = os.path.join('inputs','cf','cfdata.gdx')
rs = pd.read_csv(os.path.join('inputs','rsmap.csv'))
rs.columns = ['r','s']


###########
#Wind
###########

windons = pd.read_csv(os.path.join('inputs','cf','wind-ons_cfcorr_ts.csv'))
windons['type'] = 'wind-ons'
windofs = pd.read_csv(os.path.join('inputs','cf','wind-ofs_cfcorr_ts.csv'))
windofs['type'] = 'wind-ofs'
wind = pd.concat([windons,windofs])
wind['tech'] = wind['type'] + '_' + wind['class'].astype(str)
wind['class'] = 'class' + wind['class'].astype(str)
wind.columns = ['r','cl','h','value','it','i']
wind = wind[['r','i','h','value']]

##############
#UPV
##############

upv = gdxpds.to_dataframe(gdxfile,'CFUPV')
upv = pd.DataFrame(upv['CFUPV'])
upv['c'] = 'UPV_' + upv.k.str.strip('class')
upv.columns = ['r','h','cl','value','i']
upv = upv[['r','i','h','value']]


#############
#DUPV
#############

dupv = gdxpds.to_dataframe(gdxfile,'CFDUPV')
dupv = pd.DataFrame(dupv['CFDUPV'])
dupv['c'] = 'DUPV_' + dupv.k.str.strip('class')
dupv.columns = ['r','h','cl','value','i']
dupv = dupv[['r','i','h','value']]


#############
#disPV
#############

distpv = pd.read_csv(os.path.join('inputs','dGen_Model_Inputs',distpvscen,'distPVCF_'+distpvscen+'.csv')).rename(columns = {'Unnamed: 0':'r'})
distpv = distpv.melt('r')
distpv.columns = ['r','h','value']
distpv['i'] = 'distPV'
distpv = distpv[['r','i','h','value']]


#############
#CSP
#############

#Read in tech-subset-table.csv to determine number of configureations
tst = pd.read_csv(os.path.join('inputs','tech-subset-table.csv'))
csp_configs = tst[(tst['CSP']=='YES') & (tst['STORAGE'] == 'YES')].shape[0]

# CFCspwStorallyears in heritage ReEDS is the adjusted CSP-ws field capacity factor from CFCSPws_tower;
# data for tower system starts from 2018 and are the same across years (no need for a year dimension)
# Note that in the most version, CFCSPws_tower (read from field_capacity_factor.csv file) has already incorporated the availability factors
# (CFCSPws_adj_factor_tower and CSPws_avail_factor)
# so can directly read from CFCSPws_tower

# CF for CSP is from SAM modeling results, and assumes SM=1 (i.e. the numbers will need to be multiplied by the actual SM of certain configurations)
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
allcf = pd.concat([wind,upv,dupv,distpv])
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
#%%
print('writing capacity factor data to: '+outdir)
allcf.to_csv(os.path.join(outdir,'cfout.csv'),index=False)
hydro.to_csv(os.path.join(outdir,'minhyd.csv'),index=False)




