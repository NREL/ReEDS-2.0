#%% IMPORTS
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
parser = argparse.ArgumentParser(description="""This file processes plant cost data by tech""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("convscen", help="thermal plant characteristics")
parser.add_argument("onswindscen", help="wind characteristics")
parser.add_argument("ofswindscen", help="wind characteristics")
parser.add_argument("upvscen", help="upv characteristics")
parser.add_argument("cspscen", help="csp characteristics")
parser.add_argument("batteryscen", help="battery characteristics")
parser.add_argument("drscen", help="dr characteristics")
parser.add_argument("pvbscen", help="pv+battery characteristics")
parser.add_argument("geoscen", help="geothermal characteristics")
parser.add_argument("hydroscen", help="hydro characteristics")
parser.add_argument("beccsscen", help="BECCS characteristics")
parser.add_argument("rectscen", help="RE-CT characteristics")
parser.add_argument("degrade_suffix", help="annual degradation characteristics")
parser.add_argument("outdir", help="output directory")
parser.add_argument("revcfyear", help="year that reV capacity factors are defined for")
parser.add_argument("rev_onswindscen", help="onshore wind scenario assumed in reV")
parser.add_argument("rev_ofswindscen", help="offshore wind scenario assumed in reV")

args = parser.parse_args()

reeds_dir = args.reeds_dir
convscen = args.convscen
onswindscen = args.onswindscen
ofswindscen = args.ofswindscen
upvscen = args.upvscen
cspscen = args.cspscen
batteryscen = args.batteryscen
drscen = args.drscen
pvbscen = args.pvbscen
geoscen = args.geoscen
hydroscen = args.hydroscen
beccsscen = args.beccsscen
rectscen = args.rectscen
degrade_suffix = args.degrade_suffix
caesscen = "caes_reference"
outdir = args.outdir
revcfyear = args.revcfyear
rev_onswindscen = args.rev_onswindscen
rev_ofswindscen = args.rev_ofswindscen

# #%% Testing inputs
# reeds_dir = os.path.expanduser('~/github2/ReEDS-2.0/')
# convscen = "conv_ATB_2021"
# onswindscen = "ons-wind_ATB_2021_moderate"
# ofswindscen = "ofs-wind_ATB_2021_moderate"
# upvscen = "upv_ATB_2021_moderate"
# cspscen = "csp_ATB_2021_moderate"
# batteryscen = "battery_ATB_2021_moderate"
# pvbscen = "pvb_ATB_2021_P-moderate_B-moderate"
# geoscen = "geo_ATB_2021_moderate"
# hydroscen = "hydro_ATB_2019_mid"
# rectscen = 're-ct_ATB_2021'
# beccsscen = 'beccs_reference'
# outdir = os.getcwd()
# degrade_suffix = 'default'
# caesscen = "caes_reference"
# revcfyear = 2030

#%% FUNCTIONS
#function for applying dollar year deflator
def deflate_func(data,case):
	deflate = dollaryear.loc[dollaryear['Scenario'] == case,'Deflator'].values[0]
	data.loc[:,'capcost'] = data['capcost'] * deflate
	data.loc[:,'fom'] = data['fom'] * deflate
	data.loc[:,'vom'] = data['vom'] * deflate

	return data

#%% PROCEDURE
os.chdir(os.path.join(reeds_dir,"inputs","plant_characteristics"))

# Remove files that will be created as outputs
files = ["plantcharout.txt","windcfout.txt"]
for f in files:
	if os.path.exists(f):
		os.remove(f)

dollaryear = pd.read_csv("dollaryear.csv")
deflator = pd.read_csv("../deflator.csv")
deflator.columns = ["Dollar.Year","Deflator"]

dollaryear = dollaryear.merge(deflator,on="Dollar.Year",how="left")

#%% PV
#Adjust cost data to 2004$
upv = pd.read_csv(upvscen+'.csv')
upv = deflate_func(upv,upvscen)
pv_cf_improve = upv[['t','cf_improvement']]
pv_cf_improve = pv_cf_improve.round(3)
upv['i'] ="UPV"

#Prior to ATB 2020, PV costs are in $/kW_DC
#Starting with ATB 2020 cost inputs, PV costs are in $/kW_AC
#ReEDS uses DC capacity, so divide by inverter loading ration of 1.3
if not '2019' in upvscen:
    upv[['capcost','fom','vom']] = upv[['capcost','fom','vom']] / 1.3
    
upv_stack = pd.DataFrame(columns=upv.columns)

#create categories for all upv categories
for n in range(1,11):
	tupv = upv.copy()
	tupv['i'] = "UPV_"+str(n)
	upv_stack = pd.concat([upv_stack,tupv],sort=False)

#%% Other techs
conv = pd.read_csv(convscen+'.csv')
conv = deflate_func(conv,convscen)

beccs = pd.read_csv(beccsscen+'.csv')
beccs = deflate_func(beccs,beccsscen)

rect = pd.read_csv(rectscen+'.csv')
rect = deflate_func(rect,rectscen)

onswinddata = pd.read_csv(onswindscen+'.csv')
onswinddata.columns= ['tech','trg','t','cf','capcost','fom','vom']
onswinddata = deflate_func(onswinddata,onswindscen)

#%% Wind
# the wind data changed format after 2019, so use the new format if using a 
# newer dataset
if '2019' in ofswindscen:
    winddata = onswinddata.copy()
else:
    ofswinddata = pd.read_csv(ofswindscen+'.csv')
    ofswinddata.columns = ['tech','trg','t','cf','capcost','fom','vom']
    ofswinddata = deflate_func(ofswinddata,ofswindscen)
    winddata = pd.concat([onswinddata.copy(),ofswinddata.copy()])

winddata.loc[winddata['tech'].str.contains('ONSHORE'),'tech'] = 'wind-ons'
winddata.loc[winddata['tech'].str.contains('OFFSHORE'),'tech'] = 'wind-ofs'
winddata['i'] = winddata['tech'] + '_' + winddata['trg'].astype(str)
wind_stack = winddata[['t','i','capcost','fom','vom']].copy()

rev_onswinddata = pd.read_csv(rev_onswindscen+'.csv')
rev_onswinddata.columns= ['tech','trg','t','cf','capcost','fom','vom']
rev_onswinddata = deflate_func(rev_onswinddata,rev_onswindscen)
rev_ofswinddata = pd.read_csv(rev_ofswindscen+'.csv')
rev_ofswinddata.columns= ['tech','trg','t','cf','capcost','fom','vom']
rev_ofswinddata = deflate_func(rev_ofswinddata,rev_ofswindscen)
rev_winddata = pd.concat([rev_onswinddata.copy(),rev_ofswinddata.copy()])
rev_winddata.loc[rev_winddata['tech'].str.contains('ONSHORE'),'tech'] = 'wind-ons'
rev_winddata.loc[rev_winddata['tech'].str.contains('OFFSHORE'),'tech'] = 'wind-ofs'
rev_winddata['i'] = rev_winddata['tech'] + '_' + rev_winddata['trg'].astype(str)

#%% CSP
csp = pd.read_csv(cspscen+'.csv')
csp = deflate_func(csp,cspscen)

csp_stack = pd.DataFrame(columns=csp.columns)

#create categories for all upv categories
for n in range(1,13):
	tcsp = csp.copy()
	tcsp['i'] = csp['type']+"_"+str(n)
	csp_stack = pd.concat([csp_stack,tcsp],sort=False)

csp_stack = csp_stack[['t','capcost','fom','vom','i']]

#%% Storage
battery = pd.read_csv(batteryscen+'.csv')
battery = deflate_func(battery,batteryscen)

dr = pd.read_csv('dr_'+drscen+'.csv')
dr = deflate_func(dr,'dr_'+drscen)

caes = pd.read_csv(caesscen+'.csv')
caes = deflate_func(caes,caesscen)
caes['i'] = 'caes'

#%% Combine
alldata = pd.concat([conv,upv_stack,wind_stack,csp_stack,battery,dr,caes,beccs,rect],sort=False)
alldata['t'] = alldata['t'].astype(int)

#Convert from $/kw to $/MW
alldata['capcost'] = alldata['capcost']*1000
alldata['fom'] = alldata['fom']*1000

alldata['capcost'] = alldata['capcost'].round(0).astype(int)
alldata['fom'] = alldata['fom'].round(0).astype(int)
alldata['vom'] = alldata['vom'].round(8)
alldata['heatrate'] = alldata['heatrate'].round(8)

#Fill empty value with 0
alldata = alldata.fillna(0)

#Save data into series
outdata_series = ['('+alldata['i']+'.'+alldata['t'].astype(str)+'.capcost)'+' '+alldata['capcost'].astype(str)+',',
           '('+alldata['i']+'.'+alldata['t'].astype(str)+'.fom)'+' '+alldata['fom'].astype(str)+',',
           '('+alldata['i']+'.'+alldata['t'].astype(str)+'.vom)'+' '+alldata['vom'].astype(str)+',',
           '('+alldata['i']+'.'+alldata['t'].astype(str)+'.heatrate)'+' '+alldata['heatrate'].astype(str)+',',
           '('+alldata['i']+'.'+alldata['t'].astype(str)+'.rte)'+' '+alldata['rte'].astype(str)+',']

#Concat series into a single list for output
outdata = list(outdata_series[0]) + list(outdata_series[1]) + list(outdata_series[2]) + list(outdata_series[3]) + list(outdata_series[4])
#Drop comma for last item in the list
outdata[-1] = outdata[-1][:-1]

#%% wind capacity factors
windcf = winddata[['t','i','cf']].set_index(['i','t'])['cf']
rev_windcf = rev_winddata[['t','i','cf']].set_index(['i','t'])['cf']
### Wind capacity factor from ATB is defined as a ratio with the reV CF
windtechs = [i for i in winddata.i.unique() if i.startswith('wind')]
for i in windtechs:
	windcf.loc[i] = (windcf.loc[i] / rev_windcf.loc[i,int(revcfyear)]).values
windcf = windcf.round(6)
outwindcf = windcf.reset_index().pivot_table(index='t',columns='i', values='cf')

#%% Other technologies
pvb = pd.read_csv(pvbscen+'.csv',index_col=0).round(6)
geo = pd.read_csv(geoscen+'.csv',index_col=0).round(6)
hydro = pd.read_csv(hydroscen+'.csv', index_col=0).round(6)
ofswind_rsc_mult = pd.read_csv(ofswindscen+'_rsc_mult.csv',index_col=0).round(6)
degrade = pd.read_csv(
	os.path.join(reeds_dir,"inputs","degradation",'degradation_annual_' + degrade_suffix + '.csv'),
	index_col=0,header=None).round(6)

#%% Write hte outputs
print('writing plant data to:', os.getcwd())
pvb.to_csv(os.path.join(outdir,'pvbcapcostmult.csv'))
geo.to_csv(os.path.join(outdir,'geocapcostmult.csv'))
hydro.to_csv(os.path.join(outdir,'hydrocapcostmult.csv'))
ofswind_rsc_mult.to_csv(os.path.join(outdir,'ofswind_rsc_mult.csv'))
degrade.to_csv(os.path.join(outdir,'degradation_annual.csv'),header=False)
outwindcf.to_csv(os.path.join(outdir,'windcfout.csv'))
pv_cf_improve.to_csv(os.path.join(outdir,'pv_cf_improve.csv'),index=False,header=False)
with open(os.path.join(outdir,'plantcharout.txt'), 'w') as filehandle:
    filehandle.writelines("%s\n" % i for i in outdata)

toc(tic=tic, year=0, process='input_processing/plantcostprep.py', 
    path=os.path.join(outdir,'..'))
print('plantcostprep.py completed successfully')
