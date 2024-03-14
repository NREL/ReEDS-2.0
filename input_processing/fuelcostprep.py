'''
The purpose of this script is to write out fuel costs for the following fuels at 
census division level:
    - coal
    - uranium
    - H2 (for H2-CT tech)
    - natural gas
Additionally, this script also writes out natural gas demand (total NG demand as 
well as NG demand for electricity generation) and natural gas alphas
'''
#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import pandas as pd
import os
import argparse
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()

#%% Parse arguments
parser = argparse.ArgumentParser(description="""This file organizes fuel cost data by techonology""")

parser.add_argument("reeds_path", help="ReEDS directory")
parser.add_argument("inputs_case", help="output directory")

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing
#reeds_path = 'd:\\Danny_ReEDS\\ReEDS-2.0'
#reeds_path = os.getcwd()
#inputs_case = os.path.join('runs','nd5_ND','inputs_case')

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))
print("Starting fuelcostprep.py")

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0).squeeze(1)

# Load valid regions
val_r = pd.read_csv(
    os.path.join(inputs_case, 'val_r.csv'), header=None).squeeze(1).tolist()
val_r_all = pd.read_csv(
    os.path.join(inputs_case, 'val_r_all.csv'), header=None).squeeze(1).tolist()

# filter natural gas supply curve dimensions 
# on val_cendiv, written by copy_files.py
val_cendiv = pd.read_csv(os.path.join(inputs_case,"val_cendiv.csv"), 
                         header=None).squeeze(1).tolist()

input_dir = os.path.join(reeds_path,'inputs','fuelprices','')

r_cendiv = pd.read_csv(os.path.join(inputs_case,"r_cendiv.csv"))

dollaryear = pd.read_csv(os.path.join(input_dir, "dollaryear.csv"))
deflator = pd.read_csv(os.path.join(reeds_path,'inputs','deflator.csv'))
deflator.columns = ["Dollar.Year","Deflator"]
dollaryear = dollaryear.merge(deflator,on="Dollar.Year",how="left")

#%% ===========================================================================
### --- PROCEDURE: FUEL PRICE CALCULATIONS ---
### ===========================================================================

####################
#    -- Coal --    #
####################
coal = pd.read_csv(os.path.join(input_dir, f'coal_{sw.coalscen}.csv'))
coal = coal.melt(id_vars = ['year']).rename(columns={'variable':'cendiv'})

# Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == sw.coalscen,'Deflator'].values[0]
coal.loc[:,'value'] = coal['value'] * deflate

coal = coal.merge(r_cendiv,on='cendiv',how='left')
coal = coal.drop('cendiv', axis=1)
coal = coal[['year','r','value']].rename(columns={'year':'t','value':'coal'})
coal = coal.loc[coal['r'].isin(val_r_all)]
coal.coal = coal.coal.round(6)

#######################
#    -- Uranium --    #
#######################
uranium = pd.read_csv(os.path.join(input_dir, f'uranium_{sw.uraniumscen}.csv'))

# Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == sw.uraniumscen,'Deflator'].values[0]
uranium.loc[:,'cost'] = uranium['cost'] * deflate
uranium = pd.concat([uranium.assign(r=i) for i in val_r], ignore_index=True)
uranium = uranium[['year','r','cost']].rename(columns={'year':'t','cost':'uranium'})
uranium.uranium = uranium.uranium.round(6)

#####################
#    -- H2-CT --    #
#####################
# note that these fuel inputs are not used when H2 production is run endogenously in ReEDS (GSw_H2 > 0)
h2ct = pd.read_csv(os.path.join(input_dir, f'h2-ct_{sw.h2ctfuelscen}.csv'), index_col='year')

#Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == sw.h2ctfuelscen,'Deflator'].squeeze()
h2ct['cost'] = h2ct['cost'] * deflate
# Reshape from [:,[t,cost]] to [:,[t,r,cost]]
h2ct = (
    pd.concat({r:h2ct for r in val_r}, axis=0, names=['r'])
    .reset_index().rename(columns={'year':'t','cost':'h2ct'})
    [['t','r','h2ct']]
    .round(6)
)

###########################
#    -- Natural Gas --    #
###########################

ngprice = pd.read_csv(os.path.join(input_dir,f'ng_{sw.ngscen}.csv'))
ngprice = ngprice.melt(id_vars=['year']).rename(columns={'variable':'cendiv'})

# Adjust prices to 2004$
deflate = dollaryear.loc[dollaryear['Scenario'] == sw.ngscen,'Deflator'].values[0]
ngprice.loc[:,'value'] = ngprice['value'] * deflate

# Save Natural Gas prices by census region
ngprice_cendiv = ngprice.copy()
ngprice_cendiv = ngprice_cendiv.pivot_table(index='cendiv',columns='year',values='value')
ngprice_cendiv = ngprice_cendiv.round(6)

# Map cenus regions to BAs
ngprice = ngprice.merge(r_cendiv,on='cendiv',how='left')
ngprice = ngprice.drop('cendiv', axis=1)
ngprice = ngprice[['year','r','value']].rename(columns={'year':'t','value':'naturalgas'})
ngprice = ngprice.loc[ngprice['r'].isin(val_r_all)]
ngprice.naturalgas = ngprice.naturalgas.round(6)

# Combine all fuel data
fuel = coal.merge(uranium,on=['t','r'],how='left')
fuel = fuel.merge(ngprice,on=['t','r'],how='left')
fuel = fuel.merge(h2ct,on=['t','r'],how='left')
fuel = fuel.sort_values(['t','r'])

#%%#################################### 
### Natural Gas Demand Calculations ###

# Natural Gas demand
ngdemand = pd.read_csv(os.path.join(input_dir,f'ng_demand_{sw.ngscen}.csv'))
ngdemand.index = ngdemand.year
ngdemand = ngdemand.drop('year', axis=1)
ngdemand = ngdemand.transpose()
ngdemand = ngdemand.round(6)

# Total Natural Gas demand
ngtotdemand = pd.read_csv(os.path.join(input_dir, f'ng_tot_demand_{sw.ngscen}.csv'))
ngtotdemand.index = ngtotdemand.year
ngtotdemand = ngtotdemand.drop('year', axis=1)
ngtotdemand = ngtotdemand.transpose()
ngtotdemand = ngtotdemand.round(6)

### Natural Gas Alphas (already in 2004$)
if sw.GSw_GasSector == 'electric_sector':
    alpha = pd.read_csv(os.path.join(input_dir, f'alpha_{sw.ngscen}.csv'))
else:
    alpha = pd.read_csv(
        os.path.join(input_dir, f'alpha_{sw.ngscen}_{sw.GSw_EFS1_AllYearLoad}.csv'))
alpha = alpha.round(6)

#%%###################
### Data Write-Out ###
######################

fuel.to_csv(os.path.join(inputs_case,'fprice.csv'),index=False)
ngprice_cendiv.loc[val_cendiv].to_csv(os.path.join(inputs_case,'ng_price_cendiv.csv'))

ngdemand.loc[val_cendiv].to_csv(os.path.join(inputs_case,'ng_demand_elec.csv'))
ngtotdemand.loc[val_cendiv].to_csv(os.path.join(inputs_case,'ng_demand_tot.csv'))
alpha[['t']+val_cendiv].to_csv(os.path.join(inputs_case,'alpha.csv'),index=False)

toc(tic=tic, year=0, process='input_processing/fuelcostprep.py', 
    path=os.path.join(inputs_case,'..'))

print('Finished fuelcostprep.py')
