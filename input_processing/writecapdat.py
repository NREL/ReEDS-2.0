"""
The purpose of this script is to gather individual generator data from the 
NEMS generator database and organize this data into various categories, such as:
    - Non-RSC Existing Capacity
    - Non-RSC Prescribed Capacity
    - RSC Existing Capacity
    - RSC Prescribed Capacity
    - Retirement Data
        - Generator Retirements
        - Wind Retirements
        - Non-RSC Retirements
    - Hydro Capacity Factors
The categorized datasets are then written out to various csv files for use
throughout the ReEDS model.
"""

#%% IMPORTS
import gdxpds
import pandas as pd
import os
import argparse
import numpy as np

#%% direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()

#%% Fixed inputs
# Start year for ReEDS prescriptive builds (default: 2010):
Sw_startyear = 2010
# Generator database column seletions:
Sw_onlineyearcol = 'StartYear'

#%% Model Inputs
parser = argparse.ArgumentParser(description="""This file processes plant cost data by tech""")
parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("inputs_case", help="path to runs/{case}/inputs_case")

args = parser.parse_args()
reeds_dir = args.reeds_dir
inputs_case = args.inputs_case

# #%% Testing inputs
# reeds_dir = os.path.expanduser('~/github/ReEDS-2.0')
# inputs_case = os.path.join(
#     reeds_dir,'runs','v20220913_NTPm1_ercot_seq','inputs_case')

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

unitdata = sw.unitdata
retscen = sw.retscen
GSw_WaterMain = int(sw.GSw_WaterMain)

#%% Functions
def season_names(df,col):
	df[col] = df[col].str.replace('summer','summ')
	df[col] = df[col].str.replace('spring','spri')
	df[col] = df[col].str.replace('winter','wint')
	return df

##=================================
#   --- Supplemental Data ---
#==================================
## Dictionaries ------------------
TECH = {
    'nonrsc'   : ['coaloldscr', 'coalolduns', 'biopower', 'coal-igcc', 
                  'coal-new', 'gas-cc', 'gas-ct', 'geothermal', 'lfill-gas', 
                  'nuclear', 'o-g-s', 'battery_2', 'battery_4', 'battery_6', 
                  'battery_8', 'battery_10', 'pumped-hydro'
                  ],
    'pnonrsc'  : ['coal-new', 'lfill-gas', 'gas-ct', 'o-g-s', 'gas-cc',
                  'hydED', 'hydEND', 'hydUD', 'hydUND', 'geothermal', 'biopower', 'coal-igcc', 'nuclear',
                  'battery_2', 'battery_4', 'battery_6', 'battery_8', 
                  'battery_10', 'pumped-hydro', 'coaloldscr'
                  ],
    'storage'  : ['battery_2', 'battery_4', 'battery_6', 'battery_8', 
                  'battery_10', 'pumped-hydro'
                  ],
    'rsc_all'  : ['dupv','upv','pvb','csp-ns'
                  ],
    'rsc_csp'  : ['csp-ns'
                  ],
    'rsc_wsc'  : ['dupv','upv','pvb','csp-ns','csp-ws','wind-ons','wind-ofs'
                  ],
    'prsc_all' : ['dupv','upv','pvb','csp-ns','csp-ws'
                  ],
    'prsc_upv' : ['dupv','upv','pvb'
                  ],
    'prsc_w'   : ['wind-ons','wind-ofs'
                  ],
    'prsc_csp' : ['csp-ns','csp-ws'
                  ],   
    'retdat'   : ['coalolduns', 'o-g-s', 'hydED', 'hydEND', 'gas-ct', 'lfill-gas',
                  'coaloldscr', 'biopower', 'gas-cc', 'coal-new', 
                  'battery_2','nuclear', 'pumped-hydro', 'coal-igcc'
                  ],      
    'windret'  : ['wind-ons'
                  ],
    # This is not all technologies that do not having cooling, but technologies
    # that are (or could be) in the plant database.
    'no_cooling':['dupv', 'upv', 'pvb', 'gas-ct', 'geothermal',
                  'battery_2', 'battery_4', 'battery_6', 'battery_8', 
                  'battery_10', 'pumped-hydro', 'pumped-hydro-flex', 'hydUD', 
                  'hydUND', 'hydD', 'hydND', 'hydSD', 'hydSND', 'hydNPD',
                  'hydNPND', 'hydED', 'hydEND', 'wind-ons', 'wind-ofs', 'caes'
                  ]
    }
COLNAMES = {
    'nonrsc'   : (
                  ['tech','coolingwatertech','reeds_ba','ctt','wst','cap'],
                  ['i','coolingwatertech','r','ctt','wst','value']
                  ),
    'pnonrsc'  : (
                  [Sw_onlineyearcol,'reeds_ba','tech','coolingwatertech','ctt','wst','cap'],
                  ['t','r','i','coolingwatertech','ctt','wst','value']
                  ),
    'rsc'      : (
                  ['tech','reeds_ba','ctt','wst','cap'],
                  ['i','r','ctt','wst','value']
                  ),
    'rsc_wsc'  : (
                  ['reeds_ba','resource_region','tech','cap'],
                  ['r','s','i','value']
                  ),  
    'prsc_upv' : (
                  [Sw_onlineyearcol,'reeds_ba','tech','cap'],
                  ['t','r','i','value']
                  ),
    'prsc_w'   : (
                  [Sw_onlineyearcol,'resource_region','tech','cap'],
                  ['t','r','i','value']
                  ),
    'prsc_csp' : (
                  [Sw_onlineyearcol,'resource_region','tech','ctt','wst','cap'],
                  ['t','r','i','ctt','wst','value']
                  ),              
    'retdat'   : (
                  [retscen,'reeds_ba','tech','coolingwatertech','ctt','wst','cap'],
                  ['t','r','i','coolingwatertech','ctt','wst','value']
                  ),                      
    'windret'  : (
                  ['resource_region','tech','RetireYear','cap'],
                  ['r','i','t','value']
                  ),
    }

#%% PROCEDURE ------------------------------------------------------------------------
print('Beginning calculation of inputs\\capacitydata\\writecapdat.py')
cappath = os.path.join(reeds_dir,'inputs','capacitydata')

### Create map for converting resource region to ReEDS BA region (s to r):
rs = pd.read_csv(os.path.join(cappath,'rsmap.csv')).rename(columns={'Unnamed: 0':'rs'})
rsm = rs.melt('rs')
rsm.columns = ['rs','r','val']
rsm = rsm.loc[rsm.val=='Y',:]
rsnew = rsm[['r','rs']]

print('Importing generator database:')
gdb_use = pd.read_csv(os.path.join(cappath,'ReEDS_generator_database_final_EIA-NEMS.csv'))

# Change tech category of hydro that will be prescribed to use upgrade tech
# This is a coarse assumption that all recent new hydro is upgrades
# Existing hydro techs (hydED/hydEND) specifically refer to hydro that exists in 2010
# Future work could incorporate this change into unit database creation and possibly
#    use data from ORNL HydroSource to assign a more accurate hydro category.
gdb_use['tech'][(gdb_use['tech']=='hydEND') & (gdb_use[Sw_onlineyearcol] >= Sw_startyear)] = 'hydUND'
gdb_use['tech'][(gdb_use['tech']=='hydED') & (gdb_use[Sw_onlineyearcol] >= Sw_startyear)] = 'hydUD'

# If using cooling water, set the coolingwatertech of technologies with no 
# cooling to be the same as the tech
if GSw_WaterMain == 1:
    gdb_use.loc[gdb_use['tech'].isin(TECH['no_cooling']),
                'coolingwatertech'] = gdb_use.loc[gdb_use['tech'].isin(TECH['no_cooling']),
                                                  'tech']

#=================================
#%% --- ALL EXISTING CAPACITY ---
#=================================
### Used as the starting point for intra-zone network reinforcement costs
poi_cap_init = gdb_use.loc[
    (gdb_use[Sw_onlineyearcol] < Sw_startyear)
    & (gdb_use['RetireYear'] > Sw_startyear) 
].groupby('reeds_ba').cap.sum().rename('MW').round(3)
poi_cap_init.index = poi_cap_init.index.rename('*rb')

#=================================
#%% --- NONRSC EXISTING CAPACITY ---
#=================================
print('Gathering non-RSC Existing Capacity...')
nonrsc = gdb_use.loc[(gdb_use['tech'].isin(TECH['nonrsc']))     &
                     (gdb_use[Sw_onlineyearcol] < Sw_startyear) &
                     (gdb_use['RetireYear']     > Sw_startyear) 
                     ]
nonrsc = nonrsc[COLNAMES['nonrsc'][0]]
nonrsc.columns = COLNAMES['nonrsc'][1]
nonrsc = nonrsc.groupby(COLNAMES['nonrsc'][1][:-1]).sum().reset_index()

#====================================
#%% --- NONRSC PRESCRIBED CAPACITY ---
#====================================
print('Gathering non-RSC Prescribed Capacity...')
pnonrsc = gdb_use.loc[(gdb_use['tech'].isin(TECH['pnonrsc'])) &
                      (gdb_use[Sw_onlineyearcol] >= Sw_startyear) 
                      ]
pnonrsc = pnonrsc[COLNAMES['pnonrsc'][0]]
pnonrsc.columns = COLNAMES['pnonrsc'][1]
# Remove ctt and wst data from storage, set coolingwatertech to tech type ('i')
for j, row in pnonrsc.iterrows():
    if row['i'] in TECH['storage']:
        pnonrsc.loc[j,['ctt','wst','coolingwatertech']] = ['n','n',row['i']]
pnonrsc = pnonrsc.groupby(COLNAMES['pnonrsc'][1][:-1]).sum().reset_index()

#===============================
#%% --- RSC EXISTING CAPACITY ---
#===============================
'''
The following are RSC tech that are treated differently in the model
'''
print('Gathering RSC Existing Capacity...')
# DUPV and UPV values are collected at the same time here:
allout_RSC = gdb_use.loc[(gdb_use['tech'].isin(TECH['rsc_all'][:2])) &
                         (gdb_use[Sw_onlineyearcol] < Sw_startyear)  & 
                         (gdb_use['RetireYear']     > Sw_startyear)
                         ]
allout_RSC = allout_RSC[COLNAMES['rsc'][0]]
allout_RSC.columns = COLNAMES['rsc'][1]
allout_RSC = allout_RSC.groupby(COLNAMES['rsc'][1][:-2]).sum().reset_index()
allout_RSC['value'] = allout_RSC['value'] * 1.3 #Multiply all PV by ILR

# Add existing CSP builds:
#   Note: Since CSP data is affected by GSw_WaterMain, it must be dealt with
#       separate from the other RSC tech (UPV, DUPV, wind, etc)
csp = gdb_use.loc[(gdb_use['tech'].isin(TECH['rsc_csp']))    &
                  (gdb_use[Sw_onlineyearcol] < Sw_startyear) &
                  (gdb_use['RetireYear']     > Sw_startyear)
                  ]
csp = csp[COLNAMES['rsc'][0]]
csp.columns = COLNAMES['rsc'][1]
csp = csp.groupby(COLNAMES['rsc'][1][:-1]).sum().reset_index()
if GSw_WaterMain == 1:
    csp['i'] = csp['i'] + '_' + csp['ctt'] + '_' + csp['wst']
csp.drop('wst', axis=1, inplace=True)

# Add existing hydro builds:
gendb = gdb_use[["tech", "reeds_ba", "cap"]]
gendb = gendb[(gendb.tech == 'hydED') | (gendb.tech == 'hydEND')]

hyd = gendb.groupby(['tech', 'reeds_ba']).sum() \
    .reset_index() \
    .rename({"tech": "i", "reeds_ba": "r", "cap": "value"}, axis=1)

hyd['ctt'] = 'n'

# Concat all RSC Existing Data to one dataframe:
allout_RSC = pd.concat([allout_RSC, csp, hyd])

# Export Existing RSC data specifically used in writesupplycurves.py
rsc_wsc = gdb_use.loc[(gdb_use['tech'].isin(TECH['rsc_wsc'])) &
                      (gdb_use[Sw_onlineyearcol] < Sw_startyear)  & 
                      (gdb_use['RetireYear']     > Sw_startyear)
                      ]
rsc_wsc = rsc_wsc[COLNAMES['rsc_wsc'][0]]
rsc_wsc['resource_region'] = 's' + rsc_wsc['resource_region'].astype(str)
rsc_wsc.columns = COLNAMES['rsc_wsc'][1]
    # Multiply all PV by ILR
for j,row in rsc_wsc.iterrows():
    if row['i'] in ['DUPV','UPV']:
        rsc_wsc.loc[j,'value'] *= 1.3
rsc_wsc.to_csv(os.path.join(inputs_case,'rsc_wsc.csv'),index=False)

#=================================
#%% --- RSC PRESCRIBED CAPACITY ---
#=================================
print('Gathering RSC Prescribed Capacity...')
# DUPV and UPV values are collected at the same time here:
pupv = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_upv'])) &
                   (gdb_use[Sw_onlineyearcol] >= Sw_startyear)
                   ]
pupv = pupv[COLNAMES['prsc_upv'][0]]
pupv.columns = COLNAMES['prsc_upv'][1]
pupv = pupv.groupby(['t','r','i']).sum().reset_index()
# Multiply all PV by ILR
pupv['value'] = pupv['value'] * 1.3
    
# Load in wind builds:
pwind = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_w'])) &
                    (gdb_use[Sw_onlineyearcol] >= Sw_startyear)
                    ]
pwind = pwind[COLNAMES['prsc_w'][0]]
pwind.columns = COLNAMES['prsc_w'][1]
pwind['r'] = 's' + pwind['r'].astype(int).astype(str)

pwind = pwind.groupby(['t','r','i']).sum().reset_index()
pwind.sort_values(['t','r'], inplace=True)

# Add prescribed csp builds:
#   Note: Since csp is affected by GSw_WaterMain, it must be dealt with separate
#         from the other RSC tech (dupv, upv, wind, etc)
pcsp = gdb_use.loc[(gdb_use['tech'].isin(TECH['prsc_csp'])) &
                   (gdb_use[Sw_onlineyearcol] >= Sw_startyear)
                   ]
pcsp = pcsp[COLNAMES['prsc_csp'][0]]
pcsp['resource_region'] = 's' + pcsp['resource_region'].astype(int).astype(str)
pcsp.columns = COLNAMES['prsc_csp'][1]
if GSw_WaterMain == 1:
    pcsp['i'] = np.where(pcsp['i']=='csp-ns',pcsp['i']+'_'+pcsp['ctt']+'_'+pcsp['wst'],'csp-ws')


# Concat all RSC Existing Data to one dataframe:
prsc = pd.concat([pupv,pwind,pcsp],sort=False)

#------------------------------------------------------------------------------
#=================================
#   --- Retirements Data ---      
#=================================
print('Gathering Retirement Data...')
retdat = gdb_use.loc[(gdb_use['tech'].isin(TECH['retdat'])) & 
                     (gdb_use[retscen]>Sw_startyear)
                     ]
retdat = retdat[COLNAMES['retdat'][0]]
retdat.columns = COLNAMES['retdat'][1]
retdat.sort_values(by=COLNAMES['retdat'][1],inplace=True)
retdat = retdat.groupby(COLNAMES['retdat'][1][:-1]).sum().reset_index()

#================================
#   --- Wind Retirements ---     
#================================
print('Gathering Wind Retirement Data...')
wnew = gdb_use.loc[(gdb_use['tech'].isin(TECH['windret']))          &
                   (gdb_use[Sw_onlineyearcol] <= Sw_startyear)      & 
                   (gdb_use['RetireYear']     >  Sw_startyear)      &
                   (gdb_use['RetireYear']     <  Sw_startyear + 30)
                   ]
wnew = wnew[COLNAMES['windret'][0]]
wnew.columns = COLNAMES['windret'][1]
wnew['r'] = 's' + wnew['r'].astype(str)
wnew['v'] = 'init-1'
wnew = wnew.groupby(['i','v','r','t']).sum().reset_index()

wnew = (wnew
         .pivot_table(index = ['i','v','r'], columns = 't', values='value')
         .reset_index()
         .fillna(0)
         )

#------------------------------------------------------------------------------
#=================================
#%% --- HYDRO Capacity Factor ---
#=================================
hydcf = pd.read_csv(os.path.join(cappath, "hydcf.csv"))
hydcf['value'] = hydcf['value'].round(6)
hydcf = season_names(hydcf, 'szn') #need names to match

#hydro cf adjustment by szn
hydcfadj = pd.read_csv(os.path.join(cappath, "SeaCapAdj_hy.csv"))
hydcfadj['value'] = hydcfadj['value'].round(6)
hydcfadj = season_names(hydcfadj,'szn') #need names to match

#%%
#=================================
# --- waterconstraint indexing ---
#=================================

retdat['i'] = retdat['i'].str.lower()
pnonrsc['i'] = pnonrsc['i'].str.lower()

#when water constraints are enabled, retirements are also indexed by cooling technology and cooling water source
#otherwise, they only have the indices of year, region, and tech'
if GSw_WaterMain == 1:
    ### Group by all cols except 'value'
    retdat = retdat.groupby(COLNAMES['retdat'][1][:-1]).sum().reset_index()
    retdat.columns = COLNAMES['retdat'][1]

    nonrsc = nonrsc.groupby(COLNAMES['nonrsc'][1][:-1]).sum().reset_index()
    nonrsc.columns = COLNAMES['nonrsc'][1]

    pnonrsc = pnonrsc.groupby(COLNAMES['pnonrsc'][1][:-1]).sum().reset_index()
    pnonrsc.columns = COLNAMES['pnonrsc'][1]

    retdat['i'] = retdat['coolingwatertech']
    retdat = retdat.groupby(['t','r','i']).sum().reset_index()
    retdat.columns = ['t','r','i','value']
    
    nonrsc['i'] = nonrsc['coolingwatertech']
    nonrsc = nonrsc.groupby(['i','r']).sum().reset_index()
    nonrsc.columns = ['i','r','value']

    pnonrsc['i'] = pnonrsc['coolingwatertech']
    pnonrsc = pnonrsc.groupby(['t','r','i']).sum().reset_index()
    pnonrsc.columns = ['t','r','i','value']
else: 
# Group by [year, region, tech]
    retdat = retdat.groupby(['t','r','i']).sum().reset_index()
    retdat.columns = ['t','r','i','value']
    
    nonrsc = nonrsc.groupby(['i','r']).sum().reset_index()
    nonrsc.columns = ['i','r','value']

    pnonrsc = pnonrsc.groupby(['t','r','i']).sum().reset_index()
    pnonrsc.columns = ['t','r','i','value']

# Final Groupby step for capacity groupings not affected by GSw_WaterMain:
allout_RSC = allout_RSC.groupby(['i','r']).sum().reset_index()
prsc = prsc.groupby(['t','i','r']).sum().reset_index()

#%%
#=================================
# --- Data Write-Out ---
#=================================

#Round outputs before writing out
for df in [retdat, nonrsc, pnonrsc, allout_RSC, prsc]:
    df['value'] = df['value'].round(6)
    # Set all years to integer datatype
    if 't' in df.columns:
        df['t'] = (df
                   .t
                   .astype(float)
                   .round()
                   .astype(int)
                   )

#%% Write it
print('Writing capacity data in: '+inputs_case)
nonrsc[['i','r','value']].to_csv(os.path.join(inputs_case,'capnonrsc.csv'),index=False)
retdat[['t','r','i','value']].to_csv(os.path.join(inputs_case,'retirements.csv'),index=False)
pnonrsc[['t','i','r','value']].to_csv(os.path.join(inputs_case,'prescribed_nonRSC.csv'),index=False)
allout_RSC[['i','r','value']].to_csv(os.path.join(inputs_case,'caprsc.csv'),index=False)
prsc[['t','i','r','value']].to_csv(os.path.join(inputs_case,'prescribed_rsc.csv'),index=False)
wnew.to_csv(os.path.join(inputs_case,'wind_retirements.csv'),index=False)
poi_cap_init.to_csv(os.path.join(inputs_case,'poi_cap_init.csv'))
### Add '*' to first column name so GAMS reads it as a comment
hydcf[['i','szn','r','t','value']] \
    .rename(columns={'i': '*i'}) \
    .to_csv(os.path.join(inputs_case,'hydcf.csv'), index=False)
hydcfadj[['i','szn','r','value']] \
    .rename(columns={'i': '*i'}) \
    .to_csv(os.path.join(inputs_case,'hydcfadj.csv'), index=False)

toc(tic=tic, year=0, process='input_processing/writecapdat.py', 
    path=os.path.join(inputs_case,'..'))
print('Finished writing capacity data')

