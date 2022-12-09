import pandas as pd
import os
import argparse
# direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()
print("Starting calculation of fuelcostprep.py")

#%% Argument Inputs
parser = argparse.ArgumentParser(description="""This file organizes fuel cost data by techonology""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("inputs_case", help="output directory")

args = parser.parse_args()
reeds_dir = args.reeds_dir
inputs_case = args.inputs_case

#%% Inputs for testing
# reeds_dir = 'd:\\Danny_ReEDS\\ReEDS-2.0'
# inputs_case = os.getcwd()

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

coalscen = sw.coalscen
uraniumscen = sw.uraniumscen
ngscen = sw.ngscen
GSw_GasSector = sw.GSw_GasSector
rectfuelscen = sw.rectfuelscen
GSw_EFS1_AllYearLoad = sw.GSw_EFS1_AllYearLoad

os.chdir(os.path.join(reeds_dir,"inputs","fuelprices"))


# Remove files that will be created as outputs
files = ["fprice.csv","ng_price_cendiv.csv","ng_demand_elec.csv","ng_demand_tot.csv","alpha.csv"]
for f in files:
	if os.path.exists(f):
		os.remove(f)


r_cendiv = pd.read_csv('../r_cendiv.csv')

dollaryear = pd.read_csv("dollaryear.csv")
deflator = pd.read_csv("../deflator.csv")
deflator.columns = ["Dollar.Year","Deflator"]

dollaryear = dollaryear.merge(deflator,on="Dollar.Year",how="left")

#coal
coal = pd.read_csv("coal_"+coalscen+".csv")
coal = coal.melt(id_vars = ['year']).rename(columns={'variable':'cendiv'})

#Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == coalscen,'Deflator'].values[0]
coal.loc[:,'value'] = coal['value'] * deflate

coal = coal.merge(r_cendiv,on='cendiv',how='left')
coal = coal.drop('cendiv', axis=1)
coal = coal[['year','r','value']].rename(columns={'year':'t','value':'coal'})
coal.coal = coal.coal.round(8)
#urnaium
uranium = pd.read_csv("uranium_"+uraniumscen+'.csv')

#Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == uraniumscen,'Deflator'].values[0]
uranium.loc[:,'cost'] = uranium['cost'] * deflate
uranium = pd.concat([uranium]*205).sort_values(['year'])
uranium['r'] = ['p'+str(r) for r in list(range(1,206))*41]
uranium = uranium.reset_index(drop=True)
uranium = uranium[['year','r','cost']].rename(columns={'year':'t','cost':'uranium'})
uranium.uranium = uranium.uranium.round(8)

#RE-CT
rect = pd.read_csv('re-ct_'+rectfuelscen+'.csv')

#Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == rectfuelscen,'Deflator'].values[0]
rect.loc[:,'cost'] = rect['cost'] * deflate
rect = pd.concat([rect]*205).sort_values(['year'])
rect['r'] = ['p'+str(r) for r in list(range(1,206))*41]
rect = rect.reset_index(drop=True)
rect = rect[['year','r','cost']].rename(columns={'year':'t','cost':'rect'})
rect.rect = rect.rect.round(8)

#Natural gas
ngprice = pd.read_csv('ng_'+ngscen+'.csv')
ngprice = ngprice.melt(id_vars=['year']).rename(columns={'variable':'cendiv'})

#Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == ngscen,'Deflator'].values[0]
ngprice.loc[:,'value'] = ngprice['value'] * deflate

#Save ng prices by census region
ngprice_cendiv = ngprice.copy()
ngprice_cendiv = ngprice_cendiv.pivot_table(index='cendiv',columns='year',values='value')
ngprice_cendiv = ngprice_cendiv.round(8)

#Map cenus regions to BAs
ngprice = ngprice.merge(r_cendiv,on='cendiv',how='left')
ngprice = ngprice.drop('cendiv', axis=1)
ngprice = ngprice[['year','r','value']].rename(columns={'year':'t','value':'naturalgas'})
ngprice.naturalgas = ngprice.naturalgas.round(8)

#Combine all data
fuel = coal.merge(uranium,on=['t','r'],how='left')
fuel = fuel.merge(ngprice,on=['t','r'],how='left')
fuel = fuel.merge(rect,on=['t','r'],how='left')
fuel = fuel.sort_values(['t','r'])

#Natural gas demand
ngdemand = pd.read_csv("ng_demand_" + ngscen + ".csv")
ngdemand.index = ngdemand.year
ngdemand = ngdemand.drop('year', axis=1)
ngdemand = ngdemand.transpose()
ngdemand = ngdemand.round(8)

#Total demand
ngtotdemand = pd.read_csv('ng_tot_demand_' + ngscen + ".csv")
ngtotdemand.index = ngtotdemand.year
ngtotdemand = ngtotdemand.drop('year', axis=1)
ngtotdemand = ngtotdemand.transpose()
ngtotdemand = ngtotdemand.round(8)

### Natural Gas Alphas (already in 2004$)
if(GSw_GasSector=="electric_sector"):
    alpha = pd.read_csv("alpha_"+ngscen+".csv")
elif(GSw_GasSector=="energy_sector"):
    alpha = pd.read_csv("alpha_"+ngscen+"_"+GSw_EFS1_AllYearLoad+".csv")
alpha = alpha.round(8)
#%%
fuel.to_csv(os.path.join(inputs_case,"fprice.csv"),index=False)
ngprice_cendiv.to_csv(os.path.join(inputs_case,'ng_price_cendiv.csv'))
ngdemand.to_csv(os.path.join(inputs_case,'ng_demand_elec.csv'))
ngtotdemand.to_csv(os.path.join(inputs_case,'ng_demand_tot.csv'))
alpha.to_csv(os.path.join(inputs_case,'alpha.csv'),index=False)

toc(tic=tic, year=0, process='input_processing/fuelcostprep.py', 
    path=os.path.join(inputs_case,'..'))
print('fuelcostprep.py completed succesfully')
