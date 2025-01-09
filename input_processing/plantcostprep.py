#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import pandas as pd
import numpy as np
import os
import argparse
import support_functions as sFuncs
# Time the operation of this script
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()

#%% Parse arguments
parser = argparse.ArgumentParser(description="""This file processes plant cost data by tech""")
parser.add_argument("reeds_path", help="ReEDS directory")
parser.add_argument("inputs_case", help="output directory")

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing
#reeds_path = os.path.expanduser('~/github2/ReEDS-2.0/')
#inputs_case = os.path.join(reeds_path,'runs','v20220421_prmM0_ercot_seq','inputs_case')
#reeds_path = '/Users/apham/Documents/GitHub/ReEDS/ReEDS-2.0/'
#inputs_case = '/Users/apham/Documents/GitHub/ReEDS/ReEDS-2.0/runs/test_Pacific/inputs_case/'

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))
print('Starting plantcostprep.py')

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0).squeeze(1)
convscen = sw.convscen
onswindscen = sw.onswindscen
ofswindscen = sw.ofswindscen
upvscen = sw.upvscen
cspscen = sw.cspscen
batteryscen = sw.batteryscen
drscen = sw.drscen
evmcscen = sw.evmcscen
pvbscen = sw.pvbscen
geoscen = sw.geoscen
hydroscen = sw.hydroscen
beccsscen = sw.beccsscen
ccsflexscen = sw.ccsflexscen
h2ctscen = sw.h2ctscen
dacscen = sw.dacscen
GSw_DAC_Gas_Case = sw.GSw_DAC_Gas_Case
upgradescen = sw.upgradescen
degrade_suffix = sw.degrade_suffix
caesscen = "caes_reference"
GSw_PVB_Dur = int(sw.GSw_PVB_Dur)
GSw_UpgradeCost_Mult = int(sw.GSw_UpgradeCost_Mult)

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def deflate_func(data,case):
    deflate = dollaryear.loc[dollaryear['Scenario'] == case,'Deflator'].values[0]
    if 'capcost' in data.columns:
        data['capcost'] *= deflate
    if 'fom' in data.columns:
        data['fom'] *= deflate
        data['vom'] *= deflate
    return data

#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

dollaryear = pd.concat(
    [pd.read_csv(os.path.join(inputs_case,"dollaryear_plant.csv")),
     pd.read_csv(os.path.join(inputs_case,"dollaryear_consume.csv"))]
)
deflator = pd.read_csv(
    os.path.join(inputs_case,"deflator.csv"),
    header=0, names=['Dollar.Year','Deflator'], index_col='Dollar.Year').squeeze(1)

dollaryear = dollaryear.merge(deflator,on="Dollar.Year",how="left")

#%% Get ILR_ATB from scalars
scalars = pd.read_csv(
    os.path.join(inputs_case,'scalars.csv'),
    header=None, names=['scalar','value','comment'], index_col='scalar')['value']

#%%###############
#    -- PV --    #
##################

# Adjust cost data to 2004$
upv = pd.read_csv(os.path.join(inputs_case,'plantchar_upv.csv'))
upv = deflate_func(upv,upvscen).set_index('t')

# Prior to ATB 2020, PV costs are in $/kW_DC
# Starting with ATB 2020 cost inputs, PV costs are in $/kW_AC
# ReEDS uses DC capacity, so divide by inverter loading ratio
if '2019' not in upvscen:
    upv[['capcost','fom','vom']] = upv[['capcost','fom','vom']] / scalars['ilr_utility']

# Broadcast costs to all UPV resource classes
upv_stack = pd.concat(
    {'UPV_{}'.format(c): upv for c in range(1,11)},
    axis=0, names=['i','t']
).reset_index()

#%%########################
#    -- Other Techs --    #
###########################

conv = pd.read_csv(os.path.join(inputs_case,'plantchar_conv.csv'))
conv = deflate_func(conv,convscen)

ccsflex = pd.read_csv(os.path.join(inputs_case,'plantchar_ccsflex_cost.csv'))
ccsflex = deflate_func(ccsflex,ccsflexscen)

beccs = pd.read_csv(os.path.join(inputs_case,'plantchar_beccs.csv'))
beccs = deflate_func(beccs,beccsscen)

h2ct = pd.read_csv(os.path.join(inputs_case,'plantchar_h2ct.csv'))
h2ct = deflate_func(h2ct,h2ctscen)

if upgradescen != 'default':
    upgrade = pd.read_csv(os.path.join(inputs_case,'plantchar_upgrades.csv'))
    upgrade = deflate_func(upgrade,upgradescen)
    upgrade = upgrade.rename(columns={'capcost':'upgradecost'})
    upgrade = upgrade[['i','t','upgradecost']]
    upgrade['upgradecost'] *= 1000
    upgrade['upgradecost'] = upgrade['upgradecost'].round(0).astype(int)

#%%#########################
#    -- Onshore Wind --    #
############################

onswinddata = pd.read_csv(os.path.join(inputs_case,'plantchar_onswind.csv'))
#We will have a 'Turbine' column. For each turbine, we assume 10 classes
onswinddata.columns= ['turbine','t','cf_mult','capcost','fom','vom']
onswinddata['tech'] = 'ONSHORE'
class_bin_num = 10
turb_ls = []
for turb in onswinddata['turbine'].unique():
    turb_ls += [turb]*class_bin_num
df_class_turb = pd.DataFrame({'turbine':turb_ls, 'class':range(1, len(turb_ls) + 1)})
onswinddata = onswinddata.merge(df_class_turb, on='turbine', how='inner')
onswinddata = onswinddata[['tech','class','t','cf_mult','capcost','fom','vom']]
onswinddata = deflate_func(onswinddata,onswindscen)

#%%##########################
#    -- Offshore Wind --    #
#############################

ofswinddata = pd.read_csv(os.path.join(inputs_case,'plantchar_ofswind.csv'))
if 'Turbine' in ofswinddata:
    #ATB 2024 style
    #We will have a 'Turbine' column (fixed vs floating). For each turbine, we assume 5 classes
    #(fixed = 1-5 and floating = 6-10)
    ofswinddata.columns= ['turbine','t','cf_mult','capcost','fom','vom','rsc_mult']
    ofswinddata['tech'] = 'OFFSHORE'
    class_bin_num = 5
    turb_ls = []
    for turb in ofswinddata['turbine'].unique():
        turb_ls += [turb]*class_bin_num
    df_class_turb = pd.DataFrame({'turbine':turb_ls, 'class':range(1, len(turb_ls) + 1)})
    ofswinddata = ofswinddata.merge(df_class_turb, on='turbine', how='inner')
    ofswind_rsc_mult = ofswinddata[['t','class','rsc_mult']].copy()
    ofswind_rsc_mult['tech'] = 'wind-ofs_' + ofswind_rsc_mult['class'].astype(str)
    ofswind_rsc_mult = ofswind_rsc_mult.pivot_table(index='t',columns='tech', values='rsc_mult')
    ofswinddata = ofswinddata[['tech','class','t','cf_mult','capcost','fom','vom']]
else:
    #ATB 2023 style
    #We need to reduce to 5 classes for fixed and 5 for floating. We'll leave classes 1-5 alone (for fixed), remove classes 6,7,13, and 14, and then rename classes 8-12 to 6-10 (for floating)
    ofswinddata = ofswinddata[~ofswinddata['Wind class'].isin([6,7,13,14])]
    float_cond = ofswinddata['Wind class'] > 7
    ofswinddata.loc[float_cond, 'Wind class'] = ofswinddata.loc[float_cond, 'Wind class'] - 2
    ofswind_rsc_mult = ofswinddata[['Year','Wind class','rsc_mult']].copy()
    ofswind_rsc_mult['tech'] = 'wind-ofs_' + ofswind_rsc_mult['Wind class'].astype(str)
    ofswind_rsc_mult = ofswind_rsc_mult.rename(columns={'Year':'t'})
    ofswind_rsc_mult = ofswind_rsc_mult.pivot_table(index='t',columns='tech', values='rsc_mult')
    ofswinddata = ofswinddata.drop(columns=['rsc_mult'])
    ofswinddata.columns = ['tech','class','t','cf_mult','capcost','fom','vom']
ofswinddata = deflate_func(ofswinddata,ofswindscen)
winddata = pd.concat([onswinddata.copy(),ofswinddata.copy()])

winddata.loc[winddata['tech'].str.contains('ONSHORE'),'tech'] = 'wind-ons'
winddata.loc[winddata['tech'].str.contains('OFFSHORE'),'tech'] = 'wind-ofs'
winddata['i'] = winddata['tech'] + '_' + winddata['class'].astype(str)
wind_stack = winddata[['t','i','capcost','fom','vom']].copy()

#%%#######################
#    -- Geothermal --    #
##########################

geodata = pd.read_csv(os.path.join(inputs_case,'plantchar_geo.csv'))
geodata.columns = ['tech','class','depth','t','capcost','fom','vom']
geodata['i'] = geodata['tech'] + '_' + geodata['depth'] + '_' + geodata['class'].astype(str)
geodata = deflate_func(geodata,geoscen)
geo_stack = geodata[['t','i','capcost','fom','vom']].copy()


#%%################
#    -- CSP --    #
###################


csp = pd.read_csv(os.path.join(inputs_case,'plantchar_csp.csv'))
csp = deflate_func(csp,cspscen)

csp_stack = pd.DataFrame(columns=csp.columns)

#create categories for all upv categories
for n in range(1,13):
	tcsp = csp.copy()
	tcsp['i'] = csp['type']+"_"+str(n)
	csp_stack = pd.concat([csp_stack,tcsp],sort=False)

csp_stack = csp_stack[['t','capcost','fom','vom','i']]

#%%####################
#    -- Storage --    #
#######################

battery = pd.read_csv(os.path.join(inputs_case,'plantchar_battery.csv'))
battery = deflate_func(battery,batteryscen)

dr = pd.read_csv(os.path.join(inputs_case,'plantchar_dr.csv'))
dr = deflate_func(dr,'dr_'+drscen)

evmc_storage = pd.read_csv(os.path.join(inputs_case,'plantchar_evmc_storage.csv'))
evmc_storage = deflate_func(evmc_storage,'evmc_storage_'+evmcscen)

evmc_shape = pd.read_csv(os.path.join(inputs_case,'plantchar_evmc_shape.csv'))
evmc_shape = deflate_func(evmc_shape,'evmc_shape_'+evmcscen)

caes = pd.read_csv(os.path.join(inputs_case,'plantchar_caes.csv'))
caes = deflate_func(caes,caesscen)
caes['i'] = 'caes'

#%%############################
#    -- Concat all data --    #
###############################

alldata = pd.concat([conv,upv_stack,wind_stack,geo_stack,csp_stack,battery,dr,evmc_storage,evmc_shape,caes,beccs,ccsflex,h2ct],sort=False)

if upgradescen != 'default':
    alldata = pd.concat([alldata,upgrade])

alldata['t'] = alldata['t'].astype(int)

#Convert from $/kw to $/MW
alldata['capcost'] = alldata['capcost']*1000
alldata['fom'] = alldata['fom']*1000

alldata['capcost'] = alldata['capcost'].round(0).astype(int)
alldata['fom'] = alldata['fom'].round(0).astype(int)
alldata['vom'] = alldata['vom'].round(4)
alldata['heatrate'] = alldata['heatrate'].round(4)

# Fill empty values with 0, melt to long format
outdata = (
	alldata.fillna(0)
	.melt(id_vars=['i','t'])
	### Rename the columns so GAMS reads them as a comment
	.rename(columns={'i':'*i'})
)

outdata = outdata.loc[outdata.variable.isin(['capcost','fom','vom','heatrate','upgradecost','rte'])]

#%%##################################
#    -- Wind Capacity Factors --    #
#####################################

windcfmult = winddata[['t','i','cf_mult']].set_index(['i','t'])['cf_mult']
windcfmult = windcfmult.round(6)
outwindcfmult = windcfmult.reset_index().pivot_table(index='t',columns='i', values='cf_mult')

#%%###########################################################
#    -- Electrolyzer Stack Replacement Cost Adjustment --    #
##############################################################

consume_char = pd.read_csv(os.path.join(reeds_path,'inputs','consume','consume_char_'+sw.GSw_H2_Inputs+'.csv'))

# grab the electrolyzer cost 'h2_elec_stack_replace_year' years into the future
current_year = datetime.date.today().year
mask = (consume_char['*i'].isin(['electrolyzer'])) & (consume_char['parameter'].isin(['cost_cap']) & (consume_char['t'].isin([current_year+scalars['h2_elec_stack_replace_year']]))) 
elec_cost_future = consume_char[mask]['value'].values[0]

# read in financials_sys from inputs_case and take the average of all past years to get an average discount rate
financials_sys = pd.read_csv(os.path.join(inputs_case,'financials_sys.csv')) 
discount_rate = np.average(financials_sys[(financials_sys['t'] <= current_year)]['d_real'].values)

# the capital cost of electrolyzers needs to be increased by the cost to replace the stack ('h2_elec_stack_replace_perc')
# this replacement cost is represented as a percent of the capital cost of a new electrolyzer in that year. This cost occurs 'h2_elec_stack_replace_year' years in the future so we discount it.
mask = (consume_char['*i'].isin(['electrolyzer'])) & (consume_char['parameter'].isin(['cost_cap'])) 
consume_char.loc[mask, 'value'] = consume_char[mask]['value'] + round( (elec_cost_future * scalars['h2_elec_stack_replace_perc'])/(discount_rate**scalars['h2_elec_stack_replace_year']) ,3)

#%%###############################
#    -- Other Technologies --    #
##################################

ccsflex_perf = pd.read_csv(os.path.join(inputs_case,'plantchar_ccsflex_perf.csv'),index_col=0).round(6)
hydro = pd.read_csv(os.path.join(inputs_case,'plantchar_hydro.csv'), index_col=0).round(6)
degrade = pd.read_csv(
	os.path.join(inputs_case,'degradation_annual.csv'),
	header=None)
degrade.columns = ['i','rate']
degrade = sFuncs.expand_GAMS_tech_groups(degrade)
degrade = degrade.set_index('i').round(6)

#%%##################################
#    -- PV+Battery Cost Model --    #
#####################################

# Get PVB designs
pvb_ilr = pd.read_csv(
    os.path.join(inputs_case, 'pvb_ilr.csv'),
    header=0, names=['pvb_type','ilr'], index_col='pvb_type').squeeze(1)
pvb_bir = pd.read_csv(
    os.path.join(inputs_case, 'pvb_bir.csv'),
    header=0, names=['pvb_type','bir'], index_col='pvb_type').squeeze(1)
# Get PV and battery $/Wac costs for PVB
battery_USDperWac = battery.loc[battery.i=='battery_{}'.format(GSw_PVB_Dur)].set_index('t').capcost
UPV_defaultILR_USDperWac = upv.capcost * scalars['ilr_utility']
# Get cost-sharing assumptions
pvbvalues = pd.read_csv(os.path.join(inputs_case,'plantchar_pvb.csv'), index_col='parameter')
fixed_ac_noninverter_cost_USDperWac = (
    pvbvalues.loc['fixed','value']
    * deflator[pvbvalues.loc['fixed','dollaryear']]
    # Input units are in $/Wac, so convert to $/MWac to match units used in ReEDS
    * 1000
)

def get_pvb_cost(
        UPV_defaultILR_USDperWac, battery_USDperWac,
        ILR_user=1.8, BIR_user=0.5,
        inverter_cost_ac_fraction=0.05,
        fixed_ac_noninverter_cost_USDperWac=0.0455,
        ILR_ATB=1.3,
):
    # Inverter cost is taken as a fixed fraction of UPV AC cost
    inverter_USDperWac = UPV_defaultILR_USDperWac * inverter_cost_ac_fraction
    # Standalone PV $/Wdc is [$/Wac] * [Wac/Wdc], where [$/Wac] is the full
    # $/Wac minus the inverter cost and AC fixed costs
    UPV_USDperWdc = (
        UPV_defaultILR_USDperWac
        - inverter_USDperWac
        - fixed_ac_noninverter_cost_USDperWac
    ) / ILR_ATB
    # Standalone PV $/Wac for the user-defined ILR: [$/Wac] + [$/Wdc] * ILR
    UPV_USDperWac = (
        inverter_USDperWac
        + fixed_ac_noninverter_cost_USDperWac
        + UPV_USDperWdc * ILR_user
    )
    # PVB system cost
    PVB_USDperWac = (
        ## PV
        UPV_USDperWac
        ## Battery sized relative to PV
        + BIR_user * (
            battery_USDperWac
            ## Minus fixed AC costs
            - fixed_ac_noninverter_cost_USDperWac
            - inverter_USDperWac
        )
    )
    # Standalone system cost for two systems with same DC capacity;
    # here the battery needs its own inverter and AC fixed costs,
    # so we don't subtract them out as we did above for PVB
    standalone_USDperWac = (
        # PV
        UPV_USDperWac
        # Battery sized relative to PV
        + BIR_user * battery_USDperWac
    )
    ### Savings vs standalone
    # savings_fraction = 1 - PVB_USDperWac / standalone_USDperWac
    # savings_USDperWac = standalone_USDperWac - PVB_USDperWac
    pvb_cost_fraction = PVB_USDperWac / standalone_USDperWac
    ### Outputs
    out = {
        'pvb': PVB_USDperWac,
        'standalone_pv_dc': UPV_USDperWdc,
        'standalone_pv_ac': UPV_USDperWac,
        'standalone_both': standalone_USDperWac,
        'inverter': inverter_USDperWac,
        'pvb_cost_fraction': pvb_cost_fraction,
    }
    return out

#%% Calculate PVB cost fraction for each PVB design
pvb = {}
for i in sw['GSw_PVB_Types'].split('_'):
    pvb['pvb{}'.format(i)] = get_pvb_cost(
        UPV_defaultILR_USDperWac=UPV_defaultILR_USDperWac,
        battery_USDperWac=battery_USDperWac,
        ILR_user=pvb_ilr['pvb{}'.format(i)],
        BIR_user=pvb_bir['pvb{}'.format(i)],
        inverter_cost_ac_fraction=pvbvalues.loc['inverter_fraction','value'],
        fixed_ac_noninverter_cost_USDperWac=fixed_ac_noninverter_cost_USDperWac,
        ILR_ATB=scalars['ilr_utility'],
    )['pvb_cost_fraction']
pvb = pd.concat(pvb, axis=1)


## Create Electric DAC scenario output
# For electric DAC, we assume a sorbent system: https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a
# FYI, for DAC-gas we assume a solvent system: https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987
dac_elec = pd.read_csv(os.path.join(inputs_case,'dac_elec.csv'))
dac_elec = deflate_func(dac_elec, f'dac_elec_{dacscen}').round(4)
# Fill empty values with 0, melt to long format
outdac_elec = (
    dac_elec.fillna(0)
    .melt(id_vars=['i','t'],value_vars=['capcost','fom','vom','conversionrate'])
    ### Rename the columns so GAMS reads them as a comment
    .rename(columns={'i':'*i'})
)


## Create Gas DAC scenario output
# For DAC-gas we assume a solvent system: https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987
filename = f'dac_gas_{sw.GSw_DAC_Gas_Case}'
dac_gas = pd.read_csv(os.path.join(reeds_path,'inputs','consume',f'{filename}.csv'))
dac_gas = deflate_func(dac_gas, filename).round(4)


#%%###################################################
#    -- Cost Adjustment for cost_upgrade Techs --    #
######################################################
upgrade_mult_mid = pd.read_csv(os.path.join(inputs_case,"upgrade_mult_mid.csv"))
upgrade_mult_advanced = pd.read_csv(os.path.join(inputs_case,"upgrade_mult_advanced.csv"))
upgrade_mult_conservative = pd.read_csv(os.path.join(inputs_case,"upgrade_mult_conservative.csv"))

if GSw_UpgradeCost_Mult == 0:
    upgrade_mult = upgrade_mult_mid
elif GSw_UpgradeCost_Mult == 1:
    upgrade_mult = upgrade_mult_advanced
elif GSw_UpgradeCost_Mult == 2:
    upgrade_mult = upgrade_mult_conservative
elif GSw_UpgradeCost_Mult == 3:
    upgrade_mult = 1
elif GSw_UpgradeCost_Mult == 4:
    upgrade_mult = 1 + (1-upgrade_mult_mid)
elif GSw_UpgradeCost_Mult == 5:
    upgrade_mult = 1.2

#%%###########################
#    -- Data Write-Out --    #
##############################

print('writing plant data to:', os.getcwd())
outdata.to_csv(os.path.join(inputs_case,'plantcharout.csv'), index=False)
upv.cf_improvement.round(3).to_csv(os.path.join(inputs_case,'pv_cf_improve.csv'), header=False)
outwindcfmult.to_csv(os.path.join(inputs_case,'windcfmult.csv'))
ccsflex_perf.to_csv(os.path.join(inputs_case,'ccsflex_perf.csv'))
consume_char.to_csv(os.path.join(inputs_case,'consume_char.csv'),index=False)
hydro.to_csv(os.path.join(inputs_case,'hydrocapcostmult.csv'))
ofswind_rsc_mult.to_csv(os.path.join(inputs_case,'ofswind_rsc_mult.csv'))
degrade.to_csv(os.path.join(inputs_case,'degradation_annual.csv'),header=False)
pvb.to_csv(os.path.join(inputs_case,'pvbcapcostmult.csv'))
upgrade_mult.round(4).to_csv(os.path.join(inputs_case,'upgrade_mult_final.csv'), index=False)
outdac_elec.to_csv(os.path.join(inputs_case,'consumechardac.csv'), index=False)
dac_gas.to_csv(os.path.join(inputs_case,'dac_gas.csv'), index=False)

toc(tic=tic, year=0, process='input_processing/plantcostprep.py', 
    path=os.path.join(inputs_case,'..'))

print('Finished plantcostprep.py')
