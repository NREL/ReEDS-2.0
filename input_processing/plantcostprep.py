import pandas as pd
import os
import argparse
# direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Model Inputs
parser = argparse.ArgumentParser(description="""This file processes plant cost data by tech""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("convcase", help="thermal plant characteristics")
parser.add_argument("onswindcase", help="wind characteristics")
parser.add_argument("ofswindcase", help="wind characteristics")
parser.add_argument("upvcase", help="upv characteristics")
parser.add_argument("cspcase", help="csp characteristics")
parser.add_argument("batterycase", help="battery characteristics")
parser.add_argument("geocase", help="geothermal characteristics")
parser.add_argument("hydrocase", help="hydro characteristics")
parser.add_argument("degradecase", help="annual degradation characteristics")
parser.add_argument("outdir", help="output directory")

args = parser.parse_args()

reeds_dir = args.reeds_dir
convcase = args.convcase
onswindcase = args.onswindcase
ofswindcase = args.ofswindcase
upvcase = args.upvcase
cspcase = args.cspcase
batterycase = args.batterycase
geocase = args.geocase
hydrocase = args.hydrocase
degradecase = args.degradecase
caescase = "caes_reference"
rectcase = 're-ct_reference'
outdir = args.outdir

#%%
#Testing inputs
#reeds_dir = "d:\\Danny_ReEDS\\ReEDS-2.0\\"
#convcase = "conv_ATB_2019"
#windcase = "wind_ATB_2019_mid"
#upvcase = "upv_ATB_2019_mid"
#cspcase = "csp_ATB_2019_mid"
#batterycase = "battery_ATB_2019_mid"
#geocase = "geo_ATB_2019_mid"
#hydrocase = "hydro_ATB_2019_mid"
#caescase = "caes_reference"
#rectcase = 're-ct_reference'
#outdir = os.getcwd()
#degradecase = 'default'

#function for applying dollar year deflator
def deflate_func(data,case):
	deflate = dollaryear.loc[dollaryear['Scenario'] == case,'Deflator'].values[0]
	data.loc[:,'capcost'] = data['capcost'] * deflate
	data.loc[:,'fom'] = data['fom'] * deflate
	data.loc[:,'vom'] = data['vom'] * deflate

	return data

os.chdir(os.path.join(reeds_dir,"inputs","plant_characteristics"))

# Remove files that will be created as outputs
files = ["plantcharout.txt","windcfout.txt"]
for f in files:
	if os.path.exists(f):
		os.remove(f)

convfile = convcase+'.csv'
onswindfile = onswindcase+'.csv'
ofswindfile = ofswindcase+'.csv'
ofswindgridfile = ofswindcase+'_rsc_mult.csv'
upvfile = upvcase+'.csv'
cspfile = cspcase+'.csv'
batteryfile = batterycase+'.csv'
geofile = geocase+'.csv'
hydrofile = hydrocase+'.csv'
caesfile = caescase+'.csv'
rectfile = rectcase+'.csv'
degradefile = 'degradation_annual_' + degradecase + '.csv'

dollaryear = pd.read_csv("dollaryear.csv")
deflator = pd.read_csv("../deflator.csv")
deflator.columns = ["Dollar.Year","Deflator"]

dollaryear = dollaryear.merge(deflator,on="Dollar.Year",how="left")

#Adjust cost data to 2004$
upv = pd.read_csv(upvfile)
upv = deflate_func(upv,upvcase)
pv_cf_improve = upv[['t','cf_improvement']]
pv_cf_improve = pv_cf_improve.round(3)
upv['i'] ="UPV"

#Prior to ATB 2020, PV costs are in $/kW_DC
#Starting with ATB 2020 cost inputs, PV costs are in $/kW_AC
#ReEDS uses DC capacity, so divide by inverter loading ration of 1.3
if '2020' in upvcase:
    upv[['capcost','fom','vom']] = upv[['capcost','fom','vom']] / 1.3
    
upv_stack = pd.DataFrame(columns=upv.columns)

#create categories for all upv categories
for n in range(1,11):
	tupv = upv.copy()
	tupv['i'] = "UPV_"+str(n)
	upv_stack = pd.concat([upv_stack,tupv],sort=False)

conv = pd.read_csv(convfile)
conv = deflate_func(conv,convcase)

rect = pd.read_csv(rectfile)
rect = deflate_func(rect,rectcase)

onswinddata = pd.read_csv(onswindfile)
onswinddata.columns= ['tech','trg','t','cf','capcost','fom','vom']
onswinddata = deflate_func(onswinddata,onswindcase)

if '2020' in ofswindcase:
    ofswinddata = pd.read_csv(ofswindfile)
    ofswinddata.columns= ['tech','trg','t','cf','capcost','fom','vom']
    ofswinddata = deflate_func(ofswinddata,ofswindcase)
    winddata = pd.concat([onswinddata.copy(),ofswinddata.copy()])
else:
	winddata = onswinddata.copy()

# onswinddata = pd.read_csv(onswindfile)
# ofswinddata = pd.read_csv(ofswindfile)


winddata.loc[winddata['tech'].str.contains('ONSHORE'),'tech'] = 'wind-ons'
winddata.loc[winddata['tech'].str.contains('OFFSHORE'),'tech'] = 'wind-ofs'
winddata['i'] = winddata['tech'] + '_' + winddata['trg'].astype(str)
wind_stack = winddata[['t','i','capcost','fom','vom']].copy()

csp = pd.read_csv(cspfile)
csp = deflate_func(csp,cspcase)

csp_stack = pd.DataFrame(columns=csp.columns)

#create categories for all upv categories
for n in range(1,13):
	tcsp = csp.copy()
	tcsp['i'] = csp['type']+"_"+str(n)
	csp_stack = pd.concat([csp_stack,tcsp],sort=False)

csp_stack = csp_stack[['t','capcost','fom','vom','i']]

battery = pd.read_csv(batteryfile)
battery = deflate_func(battery,batterycase)

caes = pd.read_csv(caesfile)
caes = deflate_func(caes,caescase)
caes['i'] = 'caes'

alldata = pd.concat([conv,upv_stack,wind_stack,csp_stack,battery,caes,rect],sort=False)
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

### wind capacity factors
windcf = winddata[['t','i','cf']].copy()
windcf.loc[:,'cf'] = windcf['cf'].round(8)
outwindcf = windcf.pivot_table(index = 't',columns = 'i', values = 'cf')

geo = pd.read_csv(geofile,index_col=0).round(6)
hydro = pd.read_csv(hydrofile, index_col=0).round(6)
ofswind_rsc_mult = pd.read_csv(ofswindgridfile,index_col=0).round(6)
degrade = pd.read_csv(os.path.join(reeds_dir,"inputs","degradation",degradefile),index_col=0,header=None).round(6)

#%%
print('writing plant data to: ' +os.getcwd())
geo.to_csv(os.path.join(outdir,'geocapcostmult.csv'))
hydro.to_csv(os.path.join(outdir,'hydrocapcostmult.csv'))
ofswind_rsc_mult.to_csv(os.path.join(outdir,'ofswind_rsc_mult.csv'))
degrade.to_csv(os.path.join(outdir,'degradation_annual.csv'),header=False)
outwindcf.to_csv(os.path.join(outdir,'windcfout.csv'))
pv_cf_improve.to_csv(os.path.join(outdir,'pv_cf_improve.csv'),index=False,header=False)
with open(os.path.join(outdir,'plantcharout.txt'), 'w') as filehandle:
    filehandle.writelines("%s\n" % i for i in outdata)
print('plantcostprep.py completed successfully')