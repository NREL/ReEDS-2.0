import pandas as pd
import os
import argparse
import gdxpds
import numpy as np
# direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')

#%%
# Model Inputs
parser = argparse.ArgumentParser(description="""This file processes plant cost data by tech""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("gdxname", help="wind characteristics")
parser.add_argument("gdxnamePRES", help="wind characteristics")
parser.add_argument("gdxnameRET", help="upv characteristics")
parser.add_argument("nukescen", help="csp characteristics")
parser.add_argument("outdir", help="battery characteristics")
parser.add_argument("waterconstraints", help="hydro characteristics")

args = parser.parse_args()

reeds_dir = args.reeds_dir
gdxname = args.gdxname
gdxnamePRES = args.gdxnamePRES
gdxnameRET = args.gdxnameRET
nukescen = args.nukescen
outdir = args.outdir
gdxhydro = 'hydrounitdata.gdx'
waterconstraints = args.waterconstraints

#%%
#Testing inputs
#reeds_dir = "D:\\Danny_ReEDS\\ReEDS-2.0"
#gdxname = "ExistingUnits_EIA-NEMS.gdx"
#gdxnamePRES = "PrescriptiveBuilds_EIA-NEMS.gdx"
#gdxnameRET = "PrescriptiveRetirements_EIA-NEMS.gdx"
#nukescen = "NukeRefRetireYear"
#gdxhydro = 'hydrounitdata.gdx'
#waterconstraints = 0
#outdir = os.path.join(reeds_dir,'inputs','capacitydata')

def season_names(df,col):
	df[col] = df[col].str.replace('summer','summ')
	df[col] = df[col].str.replace('spring','spri')
	df[col] = df[col].str.replace('winter','wint')
	return df

print('Beginning calculation of inputs\\capacitydata\\writecapdat.py')

os.chdir(os.path.join(reeds_dir,'inputs','capacitydata'))

rs = pd.read_csv('rsmap.csv').rename(columns={'Unnamed: 0':'rs'})
rsm = rs.melt('rs')
rsm.columns = ['rs','r','val']
rsm = rsm.loc[rsm.val=='Y',:]
rsnew = rsm[['r','rs']]

#original names follow the names from the respective files

#capacitydata gdx files, ExistingUnits_EIA-NEMS.gdx, PrescriptiveBuilds_EIA-NEMS.gdx, and
#PrescriptiveRetirements_EIA-NEMS.gdx, have been updated with cooling and water data
#created by processing scripts located in 
#"\\nrelqnap02\ReEDS\_ReEDS Documentation\Public unit database_cooling water". This is 
#the modified version of "\\nrelqnap02\ReEDS\_ReEDS Documentation\Public unit database" 
#that was previously used to create those gdx files.

#=================================
#   --- Retirements Data ---
#=================================

retdat = gdxpds.to_dataframe(gdxnameRET,nukescen)
retdat = pd.DataFrame(retdat[nukescen])
retdat.columns = ['t','r','i','coolingwatertech','ctt','wst','value']
#=================================
# --- NONRSC EXISTING CAPACITY ---
#=================================


#following are indexed by BA
#this one's easy
nonrsc = gdxpds.to_dataframe(gdxname,'CONVOLDqctn')
nonrsc = pd.DataFrame(nonrsc['CONVOLDqctn'])
nonrsc.columns = ['i','coolingwatertech','r','ctt','wst','value']

#also need to add storage capacities
stor = gdxpds.to_dataframe(gdxname,'import_store_power_cap_at_grid')
stor = pd.DataFrame(stor['import_store_power_cap_at_grid'])
stor.columns = ['i','r','value']
stor['ctt'] = 'n'
stor['coolingwatertech'] = stor['i'].copy()
#using 'n' as a temporary placeholder for wst to match dimension
stor['wst'] = 'n'
stor = stor[['i','coolingwatertech','r','ctt','wst','value']]

nonrsc = pd.concat([nonrsc,stor],sort=False)

#====================================
# --- NONRSC PRESCRIBED CAPACITY ---
#====================================

#following are indexed by BA
pnonrsc = gdxpds.to_dataframe(gdxnamePRES,'PrescriptiveBuildsnqct')
pnonrsc = pd.DataFrame(pnonrsc['PrescriptiveBuildsnqct'])
pnonrsc.columns = ['t','r','i','coolingwatertech','ctt','wst','value']

pnonrsc_storage = gdxpds.to_dataframe(gdxnamePRES,'PrescriptiveBuildsStorage')
pnonrsc_storage = pd.DataFrame(pnonrsc_storage['PrescriptiveBuildsStorage'])
pnonrsc_storage.columns = ['t','r','i','value']
pnonrsc_storage['ctt'] = 'n'
pnonrsc_storage['coolingwatertech'] = pnonrsc_storage['i'].copy()
pnonrsc_storage['wst'] = 'n'
pnonrsc_storage = pnonrsc_storage[['t','r','i','coolingwatertech','ctt','wst','value']]
pnonrsc = pd.concat([pnonrsc,pnonrsc_storage],sort=False)

#===============================
# --- RSC EXISTING CAPACITY ---
#===============================

#following are RSC tech that are treated differently in the model
dupv = gdxpds.to_dataframe(gdxname,'tmpDUPVOn')
dupv = pd.DataFrame(dupv['tmpDUPVOn'])
upv = gdxpds.to_dataframe(gdxname,'tmpUPVOn')
upv = pd.DataFrame(upv['tmpUPVOn'])
csp = gdxpds.to_dataframe(gdxname,'tmpCSPOct')
csp = pd.DataFrame(csp['tmpCSPOct'])

dupv.columns = ['r','value']
upv.columns = ['r','value']
csp.columns = ['rs','ctt','wst','value']

#add cooling tech
dupv['ctt'] = 'n'
upv['ctt'] = 'n'

#DUPV AND UPV both have the same resource region
dupv['rs'] = 'sk'
upv['rs'] = 'sk'

#lables need to match
csp['rs'] = 's'+csp['rs']
csp = csp.merge(rsnew,on = 'rs',how='left',sort=False)

#data for hydro
hyd = pd.read_csv('hydrocap.csv')
hyd = hyd.melt(['tech','class'])
hyd = hyd.dropna()
hyd['rs'] = 'sk'
hyd['n'] = 'n'
hyd['i'] = hyd['tech'].copy()
hyd.columns = ['tech','class','r','value','rs','ctt','i']

#we can drop the class column as only has one place (HYDclass1)
hyd = hyd[['rs','ctt','value','r','i']]

#assign tech labels
dupv['i'] = 'dupv_her'
upv['i'] = 'upv_her'
csp['i'] = 'csp_her'

if waterconstraints == 1:
    csp['i'] = csp['i'] + '_' + csp['ctt'] + '_' + csp['wst']
#water source type (wst) doesn't have any none placeholder like n in cooling tech type
csp = csp.drop('wst',1)
allout_RSC = pd.concat([dupv,upv,csp,hyd],sort=False)

#====================
#Wind Retirements
#====================

#loading in selected plant retirement data
if 'EIA-NEMS' in gdxnameRET:
    wnew = gdxpds.to_dataframe(gdxnameRET,'WindRetireExisting')
    wnew = pd.DataFrame(wnew['WindRetireExisting'])
    wnew.columns = ['rs','i','t','value']
elif 'ABB' in gdxnameRET:
    wnew = gdxpds.to_dataframe(gdxnameRET,'WindRetire')
    wnew = pd.DataFrame(wnew['WindRetire'])
    wnew.columns = ['rs','c','i','t','value']
    wnew['i'] = wnew['i'] + wnew.c.str.replace("class","_")
wnew['rs'] = 's' + wnew['rs']
wnew['c'] = 'init-1'
wnew['value'] = wnew['value'].round(6)

wnew = wnew.pivot_table(index = ['i','c','rs'],columns = 't',values='value').reset_index().fillna(0)

#=================================
# --- RSC PRESCRIBED CAPACITY ---
#=================================

pupv = gdxpds.to_dataframe(gdxnamePRES,"PrescriptiveBuildsNonQn")
pupv = pd.DataFrame(pupv["PrescriptiveBuildsNonQn"])
pupv.columns = ['t','r','i','value']
pupv['i'] = pupv.i.str.replace('DUPV','dupv_her')
pupv['i'] = pupv.i.str.replace('UPV','upv_her')
pupv['rs'] = 'sk'
#Substitution below is based on the manual observation on unit database file instead of 
#defaulting to some cooling technology type and water source type.
#These CSPs below inside pupv set (not sure how it originally included these CSPs)
#had recirculating cooling and fresh groundwater water source type in the unit database.

if waterconstraints == 1:
    pupv['i'] = pupv.i.str.replace('csp-ns','csp-ns_r_fg') # Valid for these sets of data only
    
#load in wind builds
pwind = gdxpds.to_dataframe(gdxnamePRES,'PrescriptiveBuildsWind')
pwind = pd.DataFrame(pwind["PrescriptiveBuildsWind"])
pwind.columns = ['t','rs','i','value']
pwind['rs'] = 's' + pwind['rs']
pwind = pwind.merge(rsnew,on='rs',how='left',sort=False)

phyd = gdxpds.to_dataframe(gdxhydro,'PrescriptiveBuildshydcats')
phyd = pd.DataFrame(phyd["PrescriptiveBuildshydcats"])
phyd.columns = ['t','r','i','value']
phyd['rs'] = 'sk'

pcsp = pd.read_csv('prescribed_csp.csv')
pcsp['rs'] = 's' + pcsp['rs'].astype(str)
pcsp = pcsp.merge(rsnew,on='rs',how='left',sort=False).dropna()
#replace numeraire CSPs (i.e., csp-ns and csp-ws) by its non-numeraire techs if it is csp-ns, 
#but keep as it is for csp-ws because csp-ws is handled differently in model with sets csp1_1*csp1_12...
if waterconstraints == 1:
    pcsp['i'] = np.where(pcsp['i']=='csp-ns',pcsp['i']+'_'+pcsp['ctt']+'_'+pcsp['wst'],'csp-ws')

pcsp = pcsp[['t','r','i','value','rs']]
prsc = pd.concat([pupv,pwind,phyd,pcsp],sort=False)

#=================================
# --- NONRSC RETIREMENTS ---
#=================================

#X_ed indicates dispatchable
#X_end indicates non dispatchable
ret = gdxpds.to_dataframe(gdxnameRET,nukescen)
ret = pd.DataFrame(ret[nukescen])
ret.columns = ['t','r','i','coolingwatertech','ctt','wst','value']

hydret_ed = gdxpds.to_dataframe(gdxhydro,'PRetire_hydro_all_ed')
hydret_ed = pd.DataFrame(hydret_ed["PRetire_hydro_all_ed"])
hydret_ed.columns = ['t','r','value']
hydret_end = gdxpds.to_dataframe(gdxhydro,'PRetire_hydro_all_end')
hydret_end = pd.DataFrame(hydret_end["PRetire_hydro_all_end"])
hydret_end.columns = ['t','r','value']
hydret_ed['i'] = 'hyded'
hydret_end['i'] = 'hydend'

hydret = pd.concat([hydret_ed,hydret_end],sort=False)

hydret['ctt'] = 'n'
hydret['coolingwatertech'] = hydret['i'].copy()
hydret['wst'] = 'n'
hydret = hydret[['t','r','i','coolingwatertech','ctt','wst','value']]

ret = pd.concat([ret,hydret],sort=False)

#=================================
# --- HYDRO Capacity Factor ---
#=================================

hydcf = gdxpds.to_dataframe(gdxhydro,'hydcfsn')
hydcf = pd.DataFrame(hydcf['hydcfsn'])
hydcf.columns = ['i','szn','r','value']
hydcf['value'] = hydcf['value'].round(6)

#need names to match
hydcf = season_names(hydcf, 'szn')
hydcf['id'] = '(' + hydcf.i + '.' + hydcf.szn + '.' + hydcf['r'] + ')  ' + hydcf.value.astype(str) + ','
hydcf.loc[hydcf.shape[0]-1,'id'] = hydcf.loc[hydcf.shape[0]-1,'id'][0:-1]

#hydro cf adjustment by szn
hydcfadj = gdxpds.to_dataframe(gdxhydro,'SeaCapAdj_hy')
hydcfadj = pd.DataFrame(hydcfadj['SeaCapAdj_hy'])
hydcfadj.columns = ['i','szn','r','value']
hydcfadj['value'] = hydcfadj['value'].round(6)

#need names to match
hydcfadj = season_names(hydcfadj,'szn')
hydcfadj['id'] = '(' + hydcfadj.i + '.' + hydcfadj.szn + '.' + hydcfadj['r'] + ')  ' + hydcfadj.value.astype(str) + ','
hydcfadj.loc[hydcfadj.shape[0]-1,'id'] = hydcfadj.loc[hydcfadj.shape[0]-1,'id'][0:-1]

#historical capacity factors for calibation
#not always used - see b_inputs.gms
hydcfhist = pd.read_csv('cf_hyd_hist.csv')
hydcfhist = hydcfhist.melt('r')
hydcfhist['value'] = hydcfhist['value'].round(6)

#hydcfhist['variable'] = hydcfhist['variable'].str.replace('X','')
hydcfhist['id'] = '(' + hydcfhist['r'] + '.' + hydcfhist['variable'] + ') ' + hydcfhist.value.astype(str) + ',' 
hydcfhist = season_names(hydcfhist,'id')
hydcfhist.loc[hydcfhist.shape[0]-1,'id'] = hydcfhist.loc[hydcfhist.shape[0]-1,'id'][0:-1]

#substitutions for new representation of pcat (and not i)
prsc['i'] = prsc['i'].str.replace("_her","")
allout_RSC['i'] = allout_RSC['i'].str.replace("_her","")
allout_RSC['i'] = allout_RSC['i'].str.replace("csp","csp-ns")

#note that wind is loaded in a separate file
allout_RSC = allout_RSC.loc[allout_RSC['i'] != 'wind_her', :]
pnonrsc['i'] = pnonrsc['i'].str.replace('Gas-CC-NSP','gas-CC-NSP')
pnonrsc['i'] = pnonrsc['i'].str.lower()
pnonrsc['i'] = pnonrsc['i'].str.replace('-nsp','')


if waterconstraints == 1:
    pnonrsc = pnonrsc.groupby(['t','r','i','coolingwatertech','ctt','wst'],as_index = False).agg('sum')
    pnonrsc.columns = ['t','r','i','coolingwatertech','ctt','wst','value']
else:
    pnonrsc = pnonrsc.groupby(['t','r','i'],as_index = False).agg('sum')
    pnonrsc.columns = ['t','r','i','value']

retdat['i'] = retdat['i'].str.replace('Gas-CC-NSP','gas-CC-NSP')
retdat['i'] = retdat['i'].str.lower()
retdat['i'] = retdat['i'].str.replace('-nsp','')

#when water constraints are enabled, retirements are also indexed by cooling technology and cooling water source
#otherwise, they only have the indices of year, region, and tech'
if waterconstraints == 1:
    retdat = retdat.groupby(['t','r','i','coolingwatertech','ctt','wst'],as_index = False).agg('sum')
    retdat.columns = ['t','r','i','coolingwatertech','ctt','wst','value']

    nonrsc = nonrsc.groupby(['t','r','i','coolingwatertech','ctt','wst'],as_index = False).agg('sum')
    nonrsc.columns = ['i','coolingwatertech','r','ctt','wst','value']

    pnonrsc['i'] = pnonrsc['coolingwatertech']
    pnonrsc = pnonrsc.groupby(['t','r','i'],as_index = False).agg('sum')
    pnonrsc.columns = ['t','r','i','value']
    
    retdat['i'] = retdat['coolingwatertech']
    retdat = retdat.groupby(['t','r','i'],as_index = False).agg('sum')
    retdat.columns = ['t','r','i','value']
    
    nonrsc['i'] = nonrsc['coolingwatertech']
    nonrsc = nonrsc.groupby(['i','r'],as_index = False).agg('sum')
    nonrsc.columns = ['i','r','value']
else:
    retdat = retdat.groupby(['t','r','i'],as_index = False).agg('sum')
    retdat.columns = ['t','r','i','value']
    
    nonrsc = nonrsc.groupby(['i','r'],as_index = False).agg('sum')
    nonrsc.columns = ['i','r','value']

#Round outputs before writing out
nonrsc['value'] = nonrsc['value'].round(6)
retdat['value'] = retdat['value'].round(6)
pnonrsc['value'] = pnonrsc['value'].round(6)
allout_RSC['value'] = allout_RSC['value'].round(6)
prsc['value'] = prsc['value'].round(6)

print('Writing capacity data in: '+outdir)
nonrsc[['i','r','value']].to_csv(os.path.join(outdir,'allout_nonRSC.csv'),index=False)
retdat[['t','r','i','value']].to_csv(os.path.join(outdir,'retirements.csv'),index=False)
pnonrsc[['t','i','r','value']].to_csv(os.path.join(outdir,'prescribed_nonRSC.csv'),index=False)
allout_RSC[['i','r','rs','value']].to_csv(os.path.join(outdir,'allout_RSC.csv'),index=False)
prsc[['t','i','r','rs','value']].to_csv(os.path.join(outdir,'prescribed_rsc.csv'),index=False)
wnew.to_csv(os.path.join(outdir,'wind_retirements.csv'),index=False)
with open(os.path.join(outdir,'hydcf.txt'), 'w') as filehandle:
    filehandle.writelines("%s\n" % i for i in hydcf['id'])
with open(os.path.join(outdir,'hydcfadj.txt'), 'w') as filehandle:
    filehandle.writelines("%s\n" % i for i in hydcfadj['id'])
with open(os.path.join(outdir,'hydcfhist.txt'), 'w') as filehandle:
    filehandle.writelines("%s\n" % i for i in hydcfhist['id'])
print('Finished writing capacity data')