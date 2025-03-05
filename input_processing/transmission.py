#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import pandas as pd
import numpy as np
import os
import sys
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
tic = datetime.datetime.now()

#%% Parse arguments
parser = argparse.ArgumentParser(description="Format and write climate inputs")
parser.add_argument('reeds_path', help='ReEDS directory')
parser.add_argument('inputs_case', help='output directory (inputs_case)')

args = parser.parse_args()
reeds_path = args.reeds_path
inputs_case = args.inputs_case

# #%% Settings for testing ###
# reeds_path = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
# inputs_case = os.path.join(reeds_path,'runs','v20240916_unitsM0_TN','inputs_case','')

#%%#################
### FIXED INPUTS ###

decimals = 5
drop_canmex = True
dollar_year = 2004
weight = 'cost'

costcol = 'USD{}perMW'.format(dollar_year)

#%% Set up logger
log = reeds.log.makelog(
    scriptname=__file__,
    logpath=os.path.join(inputs_case,'..','gamslog.txt'),
)
print('Starting transmission.py', flush=True)

#%% Inputs from switches
sw = reeds.io.get_switches(inputs_case)
GSw_TransScen = sw.GSw_TransScen
GSw_TransRestrict = sw.GSw_TransRestrict
GSw_VSC = int(sw.GSw_VSC)
GSw_TransSquiggliness = float(sw.GSw_TransSquiggliness)
networksource = sw.GSw_TransNetworkSource
GSw_TransHurdleLevel1 = sw.GSw_TransHurdleLevel1
GSw_TransHurdleLevel2 = sw.GSw_TransHurdleLevel2
GSw_TransHurdleRate = sw.GSw_TransHurdleRate

## networksource must end in a 4-digit year indicating the year represented by the network
trans_init_year = int(networksource[-4:])


valid_regions = {}
for level in ['r','transgrp']:
    valid_regions[level] = pd.read_csv(
        os.path.join(inputs_case, f'val_{level}.csv'), header=None).squeeze(1).tolist()    
#%% Process some inputs
trans_cap_future_file = os.path.join(
    inputs_case, 'transmission_capacity_future.csv')

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def finish(inputs_case=inputs_case):
    reeds.log.toc(tic=tic, year=0, process='input_processing/transmission.py', 
        path=os.path.join(inputs_case,'..'))
    print('Finished transmission.py', flush=True)
    quit()


def get_trancap_init(valid_regions, networksource='NARIS2024', level='r'):
    ### Get alias for level (e.g. rr, transgrpp)
    levell = level + level[-1]

    ### AC capacity is defined for each direction and calculated using the scripts at
    ### https://github.nrel.gov/pbrown/TSC
    trancap_init_ac = pd.read_csv(
        os.path.join(
            inputs_case,f'transmission_capacity_init_AC_{level}.csv'))
    trancap_init_ac['trtype'] = 'AC'

    ## DC capacity is only defined in one direction, so duplicate it for the opposite direction
    if level == 'r':
        trancap_init_nonac_undup = pd.read_csv(
            os.path.join(inputs_case,'transmission_capacity_init_nonAC.csv'))
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
        n: (pd.concat([
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
            .groupby([level,levell,'trtype']).sum().reset_index())
        for n in [0,1]
    }

    return trancap_init


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

#%% Limits on PRMTRADE across nercr boundaries
if not int(sw.GSw_PRM_NetImportLimit):
    ## No limit
    firm_import_limit = pd.DataFrame(columns=['*nercr','t','fraction']).set_index(['*nercr','t'])
else:
    limits = pd.Series(
        {int(i.split('_')[0]): i.split('_')[1] for i in sw.GSw_PRM_NetImportLimitScen.split('/')}
    )

    solveyears = pd.read_csv(
        os.path.join(inputs_case,'modeledyears.csv')
    ).columns.astype(int).tolist()
    startyear = min(solveyears)
    endyear = max(solveyears)
    allyears = range(startyear, max(endyear, limits.index.max())+1)

    ## Take the max over all years for each region and drop negative values
    net_firm_transfers_nerc = pd.read_csv(
        os.path.join(inputs_case,'net_firm_transfers_nerc.csv'),
        index_col=['nercr','t']
    )
    net_firm_import_frac = (
        net_firm_transfers_nerc.MW / net_firm_transfers_nerc.MW_TotalDemand
    ).unstack('nercr').max().clip(lower=0)
    nercrs = net_firm_import_frac.index

    _dfout = {}
    for key, val in limits.items():
        ## If 'hist' is in GSw_PRM_NetImportLimitScen,
        ## all years up until that year use the historical regional max
        if val == 'hist':
            for y in range(startyear, key+1):
                _dfout[y] = net_firm_import_frac
        ## If 'histmax', all prior years use the historical max across all regions
        elif val == 'histmax':
            for y in range(startyear, key+1):
                _dfout[y] = net_firm_import_frac.clip(lower=net_firm_import_frac.max())
        else:
            ## Input values are percentages so convert to fractions
            _dfout[key] = pd.Series(index=nercrs, data=float(val) / 100)
    firm_import_limit = (
        pd.concat(_dfout, names=('t',)).unstack('nercr')
        ## Linear interpolation between values; flat projections before and after
        .reindex(allyears).interpolate('linear').bfill().ffill()
        .loc[solveyears]
        .unstack('t').rename('fraction').rename_axis(['*nercr','t'])
    )

firm_import_limit.to_csv(os.path.join(inputs_case, 'firm_import_limit.csv'))


#%% Get single-link distances and losses
# Get single-link distances [miles]
infiles = {'AC':'500kVac', 'LCC':'500kVdc', 'B2B':'500kVac'}
tline_data = pd.concat({
    trtype: pd.read_csv(
        os.path.join(inputs_case,f'transmission_distance_cost_{infiles[trtype]}.csv'),
        dtype={'r':str, 'rr':str, 'trtype':str, 'length_miles':float, 'USD2004perMW':float},
    )
    for trtype in ['AC','LCC','B2B']
}, axis=0).reset_index(level=0).rename(columns={'level_0':'trtype','length_miles':'miles'})

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
scalars = reeds.io.get_scalars(inputs_case)
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

if tline_data.empty:
    tline_data['loss'] = None
else:
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
### B2B is treated like (AC line)-(AC/DC converter)-(AC/DC converter)-(AC line) so uses AC line FOM
transfom_USDperMWmileyear['B2B'] = transfom_USDperMWmileyear['AC']

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
if tranloss.empty:
    tranloss['loss'] = None
else:
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
        valid_regions=valid_regions, networksource=networksource, level=level)
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
                inputs_case,
                'transmission_capacity_future_baseline.csv'),
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
                
### Drop prospective lines from years <= trans_init_year
trancap_fut = trancap_fut.loc[trancap_fut.t > trans_init_year].copy()

trancap_fut.rename(columns={'r':'*r'}).astype({'t':int}).round(3).to_csv(
    os.path.join(inputs_case,'trancap_fut.csv'), index=False)

### transmission_line_capcost
tline_data[costcol].round(2).reset_index().rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case,'transmission_line_capcost.csv'), index=False)

#%%#########################
# -- cost_hurdle_rates --  #
############################
hurdle_levels = [1, 2]
cost_hurdle_intra = (
    pd.read_csv(os.path.join(inputs_case, 'cost_hurdle_intra.csv'))
    .rename(columns={'t':'*t'}).set_index('*t').round(3)
)
cost_hurdle_rate = {
    i: (
        cost_hurdle_intra[sw[f'GSw_TransHurdleLevel{i}']] if int(sw.GSw_TransHurdleRate)
        else pd.Series(name='region').rename_axis('*t')
    )
    for i in hurdle_levels
}
for i in hurdle_levels:
    cost_hurdle_rate[i].to_csv(os.path.join(inputs_case, f'cost_hurdle_rate{i}.csv'))

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
