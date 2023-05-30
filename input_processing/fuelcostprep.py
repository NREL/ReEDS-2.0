import pandas as pd
import os
import argparse
# Time the operation of this script
from ticker import toc, makelog
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
# reeds_dir = os.getcwd()
# inputs_case = os.path.join('runs','a5_ercot_seq','inputs_case')

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

# Load valid regions
val_r = pd.read_csv(
        os.path.join(inputs_case, 'val_r.csv'), squeeze=True, header=None).tolist()

# filter natural gas supply curve dimensions 
# on val_cendiv, written by copy_files.py
val_cendiv = pd.read_csv(os.path.join(inputs_case,"val_cendiv.csv"), 
                         squeeze=True, header=None).tolist()


coalscen = sw.coalscen
uraniumscen = sw.uraniumscen
ngscen = sw.ngscen
GSw_GasSector = sw.GSw_GasSector
rectfuelscen = sw.rectfuelscen
GSw_EFS1_AllYearLoad = sw.GSw_EFS1_AllYearLoad

input_dir = os.path.join(reeds_dir,'inputs','fuelprices','')

r_cendiv = pd.read_csv(os.path.join(reeds_dir,'inputs','r_cendiv.csv'))

dollaryear = pd.read_csv(os.path.join(input_dir, "dollaryear.csv"))
deflator = pd.read_csv(os.path.join(reeds_dir,'inputs','deflator.csv'))
deflator.columns = ["Dollar.Year","Deflator"]

dollaryear = dollaryear.merge(deflator,on="Dollar.Year",how="left")

#coal
coal = pd.read_csv(os.path.join(input_dir, f'coal_{coalscen}.csv'))
coal = coal.melt(id_vars = ['year']).rename(columns={'variable':'cendiv'})

#Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == coalscen,'Deflator'].values[0]
coal.loc[:,'value'] = coal['value'] * deflate

coal = coal.merge(r_cendiv,on='cendiv',how='left')
coal = coal.drop('cendiv', axis=1)
coal = coal[['year','r','value']].rename(columns={'year':'t','value':'coal'})
coal = coal.loc[coal['r'].isin(val_r)]
coal.coal = coal.coal.round(6)
#urnaium
uranium = pd.read_csv(os.path.join(input_dir, f'uranium_{uraniumscen}.csv'))

#Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == uraniumscen,'Deflator'].values[0]
uranium.loc[:,'cost'] = uranium['cost'] * deflate
uranium = pd.concat([uranium]*205).sort_values(['year'])
uranium['r'] = ['p'+str(r) for r in list(range(1,206))*41]
uranium = uranium.reset_index(drop=True)
uranium = uranium[['year','r','cost']].rename(columns={'year':'t','cost':'uranium'})
uranium = uranium.loc[uranium['r'].isin(val_r)]
uranium.uranium = uranium.uranium.round(6)

#RE-CT
rect = pd.read_csv(os.path.join(input_dir, f're-ct_{rectfuelscen}.csv'), index_col='year')

#Adjust prices to 2004$
deflate = float(dollaryear.loc[dollaryear['Scenario'] == rectfuelscen,'Deflator'])
rect['cost'] = rect['cost'] * deflate
# Reshape from [:,[t,cost]] to [:,[t,r,cost]]
rect = (
    pd.concat({r:rect for r in val_r}, axis=0, names=['r'])
    .reset_index().rename(columns={'year':'t','cost':'rect'})
    [['t','r','rect']]
    .round(6)
)

#Natural gas
ngprice = pd.read_csv(input_dir + 'ng_' + ngscen + '.csv')
ngprice = ngprice.melt(id_vars=['year']).rename(columns={'variable':'cendiv'})

#Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == ngscen,'Deflator'].values[0]
ngprice.loc[:,'value'] = ngprice['value'] * deflate

#Save ng prices by census region
ngprice_cendiv = ngprice.copy()
ngprice_cendiv = ngprice_cendiv.pivot_table(index='cendiv',columns='year',values='value')
ngprice_cendiv = ngprice_cendiv.round(6)

#Map cenus regions to BAs
ngprice = ngprice.merge(r_cendiv,on='cendiv',how='left')
ngprice = ngprice.drop('cendiv', axis=1)
ngprice = ngprice[['year','r','value']].rename(columns={'year':'t','value':'naturalgas'})
ngprice = ngprice.loc[ngprice['r'].isin(val_r)]
ngprice.naturalgas = ngprice.naturalgas.round(6)

#Combine all data
fuel = coal.merge(uranium,on=['t','r'],how='left')
fuel = fuel.merge(ngprice,on=['t','r'],how='left')
fuel = fuel.merge(rect,on=['t','r'],how='left')
fuel = fuel.sort_values(['t','r'])

#Natural gas demand
ngdemand = pd.read_csv(input_dir + 'ng_demand_' + ngscen + '.csv')
ngdemand.index = ngdemand.year
ngdemand = ngdemand.drop('year', axis=1)
ngdemand = ngdemand.transpose()
ngdemand = ngdemand.round(6)

#Total demand
ngtotdemand = pd.read_csv(input_dir + 'ng_tot_demand_' + ngscen + '.csv')
ngtotdemand.index = ngtotdemand.year
ngtotdemand = ngtotdemand.drop('year', axis=1)
ngtotdemand = ngtotdemand.transpose()
ngtotdemand = ngtotdemand.round(6)

### Natural Gas Alphas (already in 2004$)
if(GSw_GasSector=='electric_sector'):
    alpha = pd.read_csv(input_dir + 'alpha_' + ngscen + '.csv')
elif(GSw_GasSector=='energy_sector'):
    alpha = pd.read_csv(input_dir + 'alpha_' + ngscen + '_' + GSw_EFS1_AllYearLoad + '.csv')
alpha = alpha.round(6)
#%%
fuel.to_csv(os.path.join(inputs_case,"fprice.csv"),index=False)

ngprice_cendiv.loc[val_cendiv].to_csv(os.path.join(inputs_case,'ng_price_cendiv.csv'))
ngdemand.loc[val_cendiv].to_csv(os.path.join(inputs_case,'ng_demand_elec.csv'))
ngtotdemand.loc[val_cendiv].to_csv(os.path.join(inputs_case,'ng_demand_tot.csv'))
alpha[['t']+val_cendiv].to_csv(os.path.join(inputs_case,'alpha.csv'),index=False)

toc(tic=tic, year=0, process='input_processing/fuelcostprep.py', 
    path=os.path.join(inputs_case,'..'))
print('fuelcostprep.py completed succesfully')
