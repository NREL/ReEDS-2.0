#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import pandas as pd
import numpy as np
import os
from ticker import toc, makelog
import datetime
tic = datetime.datetime.now()

#%% Parse arguments
parser = argparse.ArgumentParser(description="Format and write climate inputs")
parser.add_argument('reeds_path', help='ReEDS directory')
parser.add_argument('inputs_case', help='output directory (inputs_case)')

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing ###
# reeds_path = os.path.expanduser('~/github/ReEDS-2.0/')
# inputs_case = os.path.join(reeds_path,'runs','mergetest2_western_st','inputs_case','')

#%%#################
### FIXED INPUTS ###

decimals = 5
drop_canmex = True
dollar_year = 2004
weight = 'cost'

costcol = 'USD{}perMW'.format(dollar_year)

### Indicate the source and year for the initial transmission capacity.
### 'NARIS2024' is a better starting point for future-oriented studies, but it becomes
### increasingly inaccurate for years earlier than 2024.
### 'REFS2009' does not inclue direction-dependent capacities or differentiated capacities
### for energy and PRM trading, but it better represents historical additions between 2010-2024.
networksource, trans_init_year = 'NARIS2024', 2024
# networksource, trans_init_year = 'REFS2009', 2009

### anchortype: 'load' sets rb with largest 2010 load as anchor reg;
### 'size' sets largest rb as anchor reg
anchortype = 'size'

#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))
print('Starting transmission.py', flush=True)

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0).squeeze(1)
GSw_TransScen = sw.GSw_TransScen
GSw_TransRestrict = sw.GSw_TransRestrict
GSw_VSC = int(sw.GSw_VSC)
GSw_TransSquiggliness = float(sw.GSw_TransSquiggliness)

# ReEDS only supports a single entry for agglevel right now, so use the
# first value from the list (copy_files.py already ensures that only one
# value is present)
# The 'lvl' variable ensures that BA and larger spatial aggregations use BA data and methods
agglevel = pd.read_csv(
    os.path.join(inputs_case, 'agglevels.csv')).squeeze(1).tolist()[0]
lvl = 'ba' if agglevel in ['ba','state','aggreg'] else 'county'

valid_regions = {}
for level in ['r','transgrp']:
    if (level == 'r') and (lvl == 'ba'):
        valid_regions[level] = pd.read_csv(
            os.path.join(inputs_case, 'val_ba.csv'), header=None).squeeze(1).tolist()
    else: 
        valid_regions[level] = pd.read_csv(
            os.path.join(inputs_case, f'val_{level}.csv'), header=None).squeeze(1).tolist()
        
#%% Process some inputs
## If transmission_capacity_future_{GSw_TransScen}.csv is not in inputs/transmission,
## look for it in inputs/transmission/cases.
trans_cap_future_file = os.path.join(
    reeds_path,'inputs','transmission',
    f'transmission_capacity_future_{lvl}_{GSw_TransScen}.csv'
)
if not os.path.isfile(trans_cap_future_file):
    trans_cap_future_file = os.path.join(
        reeds_path,'inputs','transmission','cases',
        f'transmission_capacity_future_{lvl}_{GSw_TransScen}.csv'
    )
if not os.path.isfile(trans_cap_future_file):
    raise FileNotFoundError(trans_cap_future_file)


### --- FUNCTIONS ---
### ===========================================================================

def val_r_filt(df, valid_regions, level='r'):
    """Filter to only the regions included in the run"""
    df = df.loc[
        df[level].isin(valid_regions[level])
        ## level+level[-1] turns 'r' into 'rr' and 'transgrp' into 'transgrpp'
        & df[level+level[-1]].isin(valid_regions[level])
    ].copy()
    return df

def finish(inputs_case=inputs_case):
    toc(tic=tic, year=0, process='input_processing/transmission.py', 
        path=os.path.join(inputs_case,'..'))
    print('Finished transmission.py', flush=True)
    quit()


def get_trancap_init(valid_regions, agglevel, networksource='NARIS2024', level='r'):
    ### Get alias for level (e.g. rr, transgrpp)
    levell = level + level[-1]
    if level == 'r':
        # Use county-level data if running at county-level resolution
        if agglevel == 'county':
            agglevel_tran = 'county'
        # Use ba-level resolution for any other model resolution
        else:
            agglevel_tran = 'ba'
    # If not using the r level, then just use level
    else:
        agglevel_tran = level
    ### AC capacity is defined for each direction and calculated using the scripts at
    ### https://github.nrel.gov/pbrown/TSC
    trancap_init_ac = pd.read_csv(
        os.path.join(
            reeds_path,'inputs','transmission',
            f'transmission_capacity_init_AC_{agglevel_tran}_{networksource}.csv'))
    ## Filter to valid regions
    trancap_init_ac = val_r_filt(trancap_init_ac, valid_regions, level=level)
    trancap_init_ac['trtype'] = 'AC'

    ## DC capacity is only defined in one direction, so duplicate it for the opposite direction
    if level == 'r':
        trancap_init_nonac_undup = pd.read_csv(
            os.path.join(reeds_path,'inputs','transmission',f'transmission_capacity_init_nonAC_{agglevel_tran}.csv'))
        ## Filter to valid regions
        trancap_init_nonac_undup = val_r_filt(trancap_init_nonac_undup, valid_regions, level='r')
        trancap_init_nonac = pd.concat(
            [trancap_init_nonac_undup, trancap_init_nonac_undup.rename(columns={'r':'rr', 'rr':'r'})],
            axis=0
        )
        ### SPECIAL CASE: p19 is islanded with NARIS transmission data, so connect it manually
        if (
            (networksource == 'NARIS2024')
            and ('p19' in valid_regions['r']) and ('p20' in valid_regions['r'])
        ):
            trancap_init_ac = pd.concat([
                trancap_init_ac,
                pd.Series({
                    'interface':'p19||p20', 'r':'p19', 'rr':'p20',
                    'MW_f0':0.001, 'MW_r0':0.001, 'MW_f1':0, 'MW_r1':0, 'trtype':'AC'})
            ], ignore_index=True)
    else:
        trancap_init_nonac = pd.DataFrame(
            columns=[level, levell, 'trtype', 'MW', 'Proect(s)', 'Notes'])

    ### Initial trading limit, using contingency levels specified by contingency level
    ### (but assuming full capacity of DC is available for both energy and capcity)
    trancap_init = {
        n: pd.concat([
            ## AC
            pd.concat([
                ## Forward direction
                (trancap_init_ac[[level,levell,'trtype',f'MW_f{n}']]
                .rename(columns={f'MW_f{n}':'MW'})),
                ## Reverse direction
                (trancap_init_ac[[level,levell,'trtype',f'MW_r{n}']]
                .rename(columns={level:levell, levell:level, f'MW_r{n}':'MW'}))
            ], axis=0),
            ## DC
            trancap_init_nonac[[level,levell,'trtype','MW']]
        ## Drop entries with zero capacity
        ], axis=0).replace(0.,np.nan).dropna()
        for n in [0,1]
    }

    return trancap_init


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

#%% Limits on PRMTRADE across nercr boundaries
solveyears = pd.read_csv(
    os.path.join(reeds_path,'inputs','modeledyears.csv'),
    usecols=[sw['yearset_suffix']],
).squeeze(1).dropna().astype(int).tolist()
solveyears = [y for y in solveyears if y <= int(sw['endyear'])]

val_nercr = pd.read_csv(
    os.path.join(inputs_case,'val_nercr.csv'), header=None,
).squeeze(1).values
## Take the max over all years for each region and drop negative values
planned_firm_transfers = pd.read_csv(
    os.path.join(reeds_path,'inputs','reserves','net_firm_transfers_nerc.csv'),
).pivot(index='t',columns='nercr',values='MW')[val_nercr].max().clip(lower=0).rename('MW')
## Keep planned firm transfers for years before GSw_PRMTRADE_limit to use in the
## eq_firm_transfer_limit / eq_firm_transfer_limit_cc constraints
if any([y < int(sw.GSw_PRMTRADE_limit) for y in solveyears]):
    firm_transfer_limit = pd.concat({
        y: planned_firm_transfers
        for y in solveyears
        if y <= int(sw.GSw_PRMTRADE_limit)
    }, names=['t']).reorder_levels(['nercr','t']).rename_axis(['*nercr','t'])
## Otherwise, if GSw_PRMTRADE_limit is set to a value before all solve years (such as 0),
## write an empty dataframe
else:
    firm_transfer_limit = pd.DataFrame(columns=['*nercr','t','MW']).set_index(['*nercr','t'])
firm_transfer_limit.to_csv(os.path.join(inputs_case, 'firm_transfer_limit.csv'))

### Planning reserve margin
(
    pd.read_csv(
        os.path.join(reeds_path,'inputs','reserves','prm_annual.csv'),
        index_col=['*nercr','t'])
    [sw['GSw_PRM_scenario']]
    ## Fill years before data begin with the first year's data
    .unstack('*nercr').reindex(solveyears).fillna(method='bfill').stack('*nercr')
    .reorder_levels(['*nercr','t']).loc[val_nercr].round(4)
).to_csv(os.path.join(inputs_case,'prm_annual.csv'))


#%% Get single-link distances and losses
# Get single-link distances [miles]
infiles = {'AC':'500kVac', 'LCC':'500kVdc', 'B2B':'500kVac'}
tline_data = pd.concat({
    trtype: pd.read_csv(
        os.path.join(
            reeds_path,'inputs','transmission',f'transmission_distance_cost_{infiles[trtype]}_{lvl}.csv'))
    for trtype in ['AC','LCC','B2B']
}, axis=0).reset_index(level=0).rename(columns={'level_0':'trtype','length_miles':'miles'})

# Filter data to just the regions that are included in the run
tline_data = val_r_filt(tline_data,valid_regions,level='r').copy()

# Apply the distance multiplier
tline_data['miles'] = tline_data['miles'] * GSw_TransSquiggliness

tline_data['r_rr'] = tline_data.r + '_' + tline_data.rr

# Make sure there are no duplicates
if (tline_data.loc[
        tline_data[['r','rr','trtype']].duplicated(keep=False)
    ].shape[0] != 0):
        print(
            tline_data.loc[
                tline_data[['r','rr','trtype']].duplicated(keep=False)
            ].sort_values(['r','rr'])
        )
        raise Exception('Duplicate entries in tline_data')


#%% Load the transmission scalars
scalars = pd.read_csv(
    os.path.join(inputs_case,'scalars.csv'),
    header=None, names=['scalar','value','comment'], index_col='scalar').value
### Get the contingency levels for energy and PRM trading
nlevel = {
    'energy': int(scalars['trans_contingency_level_energy']),
    'prm': int(scalars['trans_contingency_level_prm']),
    'transgroup': int(scalars['trans_contingency_level_transgroup']),
}

#%% Put some in dicts for easier access
tranloss_permile = {
    'AC': scalars['tranloss_permile_ac'],
    ### B2B converters are AC-AC/DC-DC/AC-AC, so use AC per-mile losses
    'B2B': scalars['tranloss_permile_ac'],
    'LCC': scalars['tranloss_permile_dc'],
    'VSC': scalars['tranloss_permile_dc'],
}
tranloss_fixed = {
    'AC': 1 - scalars['converter_efficiency_ac'],
    'B2B': 1 - scalars['converter_efficiency_lcc'],
    'LCC': 1 - scalars['converter_efficiency_lcc'],
    'VSC': 1 - scalars['converter_efficiency_vsc'],
}

### Calculate losses
def getloss(row):
    """
    Fixed losses are entered as per-endpoint values (e.g. for each AC/DC converter station
    on a LCC DC line). There are two endpoints per line, so multiply fixed losses by 2.
    Note that this approach only applies for LCC DC lines; tline_data does not
    have entries for VSC, and VSC AC/DC losses are applied later.
    """
    return row.miles * tranloss_permile[row.trtype] + tranloss_fixed[row.trtype] * 2

tline_data['loss'] = tline_data.apply(getloss, axis=1)

### Set the identifier index for easier indexing later
tline_data.set_index(['r','rr','trtype'], inplace=True)

#%% Include distances for existing lines
transmission_distance = tline_data.miles.copy()

#%% Write the line-specific transmission FOM costs [$/MW/year]
trans_fom_region_mult = int(scalars['trans_fom_region_mult'])
trans_fom_frac = scalars['trans_fom_frac']

### For simplicity we just take the unweighted average base cost across
### the four regions for which we have transmission cost data.
### Future work should identify a better assumption.
rev_transcost_base = pd.read_csv(
    os.path.join(inputs_case,'rev_transmission_basecost.csv'),
    header=[0], skiprows=[1],
).replace({'500ACsingle':'AC','500DCbipole':'LCC'}).set_index('Voltage')
transfom_USDperMWmileyear = {
    trtype: (
        rev_transcost_base.loc[trtype][['TEPPC','SCE','MISO','Southeast']].mean()
        * trans_fom_frac
    )
    for trtype in ['AC','LCC']
}

if trans_fom_region_mult:
    ### Multiply line-specific $/MW by FOM fraction to get $/MW/year
    transmission_line_fom = tline_data[costcol] * trans_fom_frac
    ### Use regional average * distance_initial for existing lines
    append = transmission_distance.loc[
        transmission_distance.reset_index().trtype.isin(
            ['AC','LCC','B2B']).set_axis(transmission_distance.index)
    ]
else:
    ### Multiply $/MW/mile/year by distance [miles] to get $/MW/year for ALL lines
    transmission_line_fom = (
        transmission_distance.reset_index().trtype.map(transfom_USDperMWmileyear)
        * transmission_distance.values
    ).set_axis(transmission_distance.index).rename('USDperMWyear')


#%%### Write files for ReEDS (adding * to make GAMS read column names as comment)
### transmission_distance
transmission_distance.round(3).reset_index().rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case,'transmission_distance.csv'), index=False)

### tranloss
tranloss = transmission_distance.reset_index()
tranloss['loss'] = tranloss.apply(getloss, axis=1)
tranloss[['r','rr','trtype','loss']].round(decimals).rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case,'tranloss.csv'), index=False, header=True)

### transmission_line_fom
transmission_line_fom.round(2).rename_axis(('*r','rr','trtype')).to_csv(
    os.path.join(inputs_case,'transmission_line_fom.csv'))

#%% Write the initial capacities   
for captype, level in [
    ('energy', 'r'),
    ('prm', 'r'),
    ('transgroup', 'transgrp'),
]:
    trancap_init = get_trancap_init(
        valid_regions=valid_regions, agglevel=agglevel, networksource=networksource, level=level)
    trancap_init[nlevel[captype]].rename(columns={level:'*'+level}).round(3).to_csv(
        os.path.join(inputs_case,f'trancap_init_{captype}.csv'),
        index=False,
    )

#%%#########################
#    -- trancap_fut --    #
############################

## note that '0' is used as a filler value in the t column for firstyear_trans, which is defined
## in inputs/scalars.csv. So we replace it whenever we load a transmission_capacity_future file.
trancap_fut = pd.concat([
    (
        pd.read_csv(
            os.path.join(
                reeds_path,'inputs','transmission',
                f'transmission_capacity_future_{lvl}_baseline.csv'),
            comment='#',
        )
        .drop(['Notes','notes','Note','note'], axis=1, errors='ignore')
        .replace({'t':{0:int(scalars['firstyear_trans_longterm'])}})
    ),
    (
        pd.read_csv(trans_cap_future_file)
        .drop(['Notes','notes','Note','note'], axis=1, errors='ignore')
        .replace({'t':{0:int(scalars['firstyear_trans_longterm'])}})
    ),
], axis=0, ignore_index=True)

### Filter to only regions in the run
trancap_fut = val_r_filt(trancap_fut, valid_regions, level='r')
                
### Drop prospective lines from years <= trans_init_year
trancap_fut = trancap_fut.loc[trancap_fut.t > trans_init_year].copy()

trancap_fut.rename(columns={'r':'*r'}).round(3).to_csv(
    os.path.join(inputs_case,'trancap_fut.csv'), index=False)

### transmission_line_capcost
tline_data[costcol].round(2).reset_index().rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case,'transmission_line_capcost.csv'), index=False)


#%%#####################################################################
#    -- Create the inputs for the VSC DC macrogrid, if necessary --    #
########################################################################

if not GSw_VSC:
    finish()

#%% Load candidate corridors for VSC
### 'all' includes initial AC and B2B links, but not existing/proposed DC (which is all LCC)
vsc_links = pd.read_csv(
    trans_cap_future_file, header=0,
).replace({'t':{0:int(scalars['firstyear_trans_longterm'])}})
### Only keep the VSC links and the modeled regions
vsc_links = vsc_links.loc[vsc_links.trtype=='VSC',['r','rr']].drop_duplicates()
vsc_links = val_r_filt(vsc_links, valid_regions, level='r')

### Add distance and losses (leaving out converter losses, which are treated separately)
distance_lookup = (
    tline_data
    .xs('LCC',level='trtype')['miles']
    .reset_index()
    .drop_duplicates()
    .set_index(['r','rr'])
    ['miles']
    .to_dict()
)
vsc_links['trtype'] = 'VSC'
vsc_links['miles'] = vsc_links.apply(
    lambda row: distance_lookup[row.r, row.rr],
    axis=1
)
vsc_links['loss'] = vsc_links.miles * tranloss_permile['VSC']


#%%### Overwrite the ReEDS files written above to include VSC
### tranloss
pd.concat([
    tranloss[['r','rr','trtype','loss']],
    vsc_links[['r','rr','trtype','loss']],
    vsc_links[['rr','r','trtype','loss']].rename(columns={'r':'rr','rr':'r'}),
], axis=0).round(decimals).drop_duplicates().rename(columns={'r':'*r','trtype':'trtype'}).to_csv(
    os.path.join(inputs_case,'tranloss.csv'), index=False, header=True
)

### transmission_distance
pd.concat([
    transmission_distance.reset_index()[['r','rr','trtype','miles']],
    vsc_links[['r','rr','trtype','miles']],
    vsc_links[['rr','r','trtype','miles']].rename(columns={'r':'rr','rr':'r'}),
], axis=0).round(3).drop_duplicates().rename(
    columns={'r':'*r','trtype':'trtype','miles':'miles'}
).to_csv(
    os.path.join(inputs_case,'transmission_distance.csv'), index=False, header=True
)

#%% Finish the timer
finish()
