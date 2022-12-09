"""
main contact: Patrick.Brown@nrel.gov
Notes:
* AC/DC converter costs and losses are bundled in with LCC DC and B2B lines, but are
  disaggregated for VSC lines (since not every node in a VSC macrogrid needs a converter)

TODO:
* Adapt VSC procedure to allow mixed VSC and non-VSC links (for example if we exclude
certain links or converter sites due to economies of scale)
"""
#%% direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()


###############
#%% IMPORTS ###

import pandas as pd
import numpy as np
import os
import argparse
import networkx as nx

print('Starting transmission_multilink.py', flush=True)

##############
#%% INPUTS ###

#%% Fixed inputs
decimals = 5
drop_canmex = True
dollar_year = 2004
weight = 'cost'
### Indicate the source and year for the initial transmission capacity.
### 'NARIS2024' is a better starting point for future-oriented studies, but it becomes
### increasingly inaccurate for years earlier than 2024.
### 'REFS2009' does not inclue direction-dependent capacities or differentiated capacities
### for energy and PRM trading, but it better represents historical additions between 2010-2024.
networksource, trans_init_year = 'NARIS2024', 2024
# networksource, trans_init_year = 'REFS2009', 2009

#%% Argument inputs
parser = argparse.ArgumentParser(description="Format and write climate inputs")
parser.add_argument('reedsdir', help='ReEDS directory')
parser.add_argument('inputs_case', help='output directory (inputs_case)')

args = parser.parse_args()
reedsdir = args.reedsdir
inputs_case = args.inputs_case

# #%% DEBUG
# reedsdir = os.path.expanduser('~/github/ReEDS-2.0/')
# inputs_case = os.path.join(reedsdir,'runs','v20221106_NTPm0_ercot_seq','inputs_case','')

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

GSw_TransScen = sw.GSw_TransScen
GSw_TransMultiLink = int(sw.GSw_TransMultiLink)
GSw_TransRestrict = sw.GSw_TransRestrict
GSw_VSC = int(sw.GSw_VSC)
GSw_TransSquiggliness = float(sw.GSw_TransSquiggliness)

#################
#%% FUNCTIONS ###

def get_multilink_paths(transmission_paths, weight='cost'):
    """
    """
    ### Initialize the graph
    import networkx as nx
    G = nx.Graph()
    ### Add the nodes (BAs)
    G.add_nodes_from(
        sorted(list(set(
            transmission_paths.r.tolist() + transmission_paths.rr.tolist()
        )))
    )
    ### Add the edges
    G.add_edges_from(
        [(*key, val)
         for key,val in
         transmission_paths.set_index(['r','rr'])[[weight]].T.to_dict().items()]
    )
    ### Loop it
    paths, weights = {}, {}
    for r in list(G.nodes):
        for rr in list(G.nodes):
            try:
                path = nx.dijkstra_path(
                    G, source=r, target=rr, weight=weight)
                weightval = nx.shortest_path_length(
                    G, source=r, target=rr, weight=weight)
            except ValueError:
                path = []
                weightval = np.nan
            paths[r,rr] = path
            weights[r,rr] = weightval
    ### Return it
    dfweights = pd.Series(weights).round(6)
    dfpaths = pd.Series(paths).map(lambda x: '|'.join(x))
    dfout = pd.concat({weight:dfweights, 'path':dfpaths},axis=1)
    dfout.index = dfout.index.rename(['r','rr'])
    return dfout

def sort_regions(regions, GSw_AggregateRegions):
    if not int(GSw_AggregateRegions):
        return ['p{}'.format(r) for r in sorted([int(r[1:]) for r in regions])]
    else:
        return sorted(regions)

def finish(inputs_case=inputs_case):
    toc(tic=tic, year=0, process='input_processing/transmission_multilink.py', 
        path=os.path.join(inputs_case,'..'))
    print('Finished transmission_multilink.py', flush=True)
    quit()

#################
#%% PROCEDURE ###

#%% Additional inputs
costcol = 'USD{}perMW'.format(dollar_year)

#%% Get the spatial hierarchy
hierarchy = pd.read_csv(
    os.path.join(inputs_case,'hierarchy.csv')
).rename(columns={'*r':'r'}).set_index('r')

#%%### Get single-link distances and losses
### Get single-link distances [miles]
infiles = {'AC':'500kVac', 'LCC':'500kVdc', 'B2B':'500kVac'}
tline_data = pd.concat({
    trtype: pd.read_csv(
        os.path.join(
            reedsdir,'inputs','transmission','transmission_distance_cost_{}.csv'.format(
                infiles[trtype])))
    for trtype in ['AC','LCC','B2B']
}, axis=0).reset_index(level=0).rename(columns={'level_0':'trtype', 'length_miles':'miles'})
### Apply the distance multiplier
tline_data.miles *= GSw_TransSquiggliness

tline_data['r_rr'] = tline_data.r + '_' + tline_data.rr

### Make sure there are no duplicates
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
}

#%% Put some in dicts for easier access
cost_acdc_lcc = scalars['cost_acdc_lcc']
cost_acdc_vsc = scalars['cost_acdc_vsc']
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

#%% trancap_init
### AC capacity is defined for each direction and calculated using the scripts at
### https://github.nrel.gov/pbrown/TSC
trancap_init_ac = pd.read_csv(
    os.path.join(
        reedsdir,'inputs','transmission',f'transmission_capacity_init_AC_{networksource}.csv'))
trancap_init_ac['trtype'] = 'AC'
## DC capacity is only defined in one direction, so duplicate it for the opposite direction
trancap_init_nonac_undup = pd.read_csv(
    os.path.join(reedsdir,'inputs','transmission',f'transmission_capacity_init_nonAC.csv'))
trancap_init_nonac = pd.concat(
    [trancap_init_nonac_undup, trancap_init_nonac_undup.rename(columns={'r':'rr', 'rr':'r'})],
    axis=0
)
### SPECIAL CASE: p19 is islanded with NARIS transmission data, so connect it manually
if networksource == 'NARIS2024':
    trancap_init_ac = trancap_init_ac.append(
        {'interface':'p19||p20', 'r':'p19', 'rr':'p20',
        'MW_f0':0.001, 'MW_r0':0.001, 'MW_f1':0, 'MW_r1':0, 'trtype':'AC'},
        ignore_index=True
    )

### Initial trading limit, using contingency levels specified by contingency level (nlevel)
### (but assuming full capacity of DC is available for both energy and capcity)
trancap_init = {
    n: pd.concat([
        ## AC
        pd.concat([
            ## Forward direction
            (trancap_init_ac[['r','rr','trtype',f'MW_f{nlevel[n]}']]
             .rename(columns={f'MW_f{nlevel[n]}':'MW'})),
            ## Reverse direction
            (trancap_init_ac[['r','rr','trtype',f'MW_r{nlevel[n]}']]
             .rename(columns={'r':'rr', 'rr':'r', f'MW_r{nlevel[n]}':'MW'}))
        ], axis=0),
        ## DC
        trancap_init_nonac[['r','rr','trtype','MW']]
    ## Drop entries with zero capacity
    ], axis=0).replace(0.,np.nan).dropna()
    for n in nlevel
}
#%% Write the initial capacities
for n in nlevel:
    trancap_init[n].rename(columns={'r':'*r'}).round(3).to_csv(
        os.path.join(inputs_case,f'trancap_init_{n}.csv'),
        index=False,
    )

#%% trancap_fut
## note that '0' is used as a filler value in the t column for firstyear_trans, which is defined
## in inputs/scalars.csv. So we replace it whenever we load a transmission_capacity_future file.
trancap_fut = pd.concat([
    (
        pd.read_csv(os.path.join(
            reedsdir,'inputs','transmission','transmission_capacity_future_baseline.csv'))
        .drop(['Notes','notes','Note','note'], axis=1, errors='ignore')
        .replace({'t':{0:int(scalars['firstyear_trans'])}})
    ),
    (
        pd.read_csv(os.path.join(
            reedsdir,'inputs','transmission','transmission_capacity_future_{}.csv').format(
                GSw_TransScen))
        .drop(['Notes','notes','Note','note'], axis=1, errors='ignore')
        .replace({'t':{0:int(scalars['firstyear_trans'])}})
    ),
], axis=0, ignore_index=True)

### Drop prospective lines from years <= trans_init_year
trancap_fut = trancap_fut.loc[trancap_fut.t > trans_init_year].copy()
trancap_fut.rename(columns={'r':'*r'}).round(3).to_csv(
    os.path.join(inputs_case,'trancap_fut.csv'), index=False)

### transmission_line_capcost
tline_data[costcol].round(2).reset_index().rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case,'transmission_line_capcost.csv'), index=False)

##########################################################
#%% Quit here if multi-link transmission assessment is off
if not GSw_TransMultiLink:
    print('Skipping the rest of transmission_multilink.py', flush=True)
    finish()

#%% Load existing and possible transmission capacity
transmission_capacity = {
    ending.lower(): (
        pd.read_csv(os.path.join(
            reedsdir,'inputs','transmission','transmission_capacity_{}.csv'.format(ending)))
        .drop(['Project(s)','Notes','rnum','rrnum'], axis=1, errors='ignore')
        .replace({'t':{0:int(scalars['firstyear_trans'])}})
    )
    for ending in ['future_baseline','future_{}'.format(GSw_TransScen)]
}
transmission_capacity['initial'] = pd.concat([
    trancap_init_ac.assign(MW=trancap_init_ac[['MW_f0','MW_r0']].max(axis=1)),
    trancap_init_nonac_undup
], axis=0)[['r','rr','trtype','MW']].copy()
for ending in transmission_capacity:
    transmission_capacity[ending.lower()]['r_rr'] = (
        transmission_capacity[ending.lower()].r + '_' + transmission_capacity[ending.lower()].rr)
transmission_capacity_future = pd.concat([
    transmission_capacity['future_baseline'],
    transmission_capacity['future_{}'.format(GSw_TransScen).lower()]
], axis=0, ignore_index=True)
### Drop VSC links for now (VSC is handled separately below)
transmission_capacity_future = transmission_capacity_future.loc[
    transmission_capacity_future.trtype != 'VSC'
].copy()
### Drop prospective lines from years <= trans_init_year
transmission_capacity_future = transmission_capacity_future.loc[
    transmission_capacity_future.t > trans_init_year].copy()

#%% Include extra lines from chosen transmission scenario
addlinks = [
    r_rr for r_rr in transmission_capacity_future.r_rr.values
    if r_rr not in transmission_capacity['initial'].r_rr.values
]

#%% Include future links based on transmission scenario
transmission_paths = transmission_capacity['initial'].append(
    transmission_capacity_future.loc[transmission_capacity_future.r_rr.isin(addlinks)],
    ignore_index=True,
)
transmission_paths = transmission_paths.replace({'trtype':{'B2B':'LCC'}})
### Add chosen multi-link extent
transmission_paths['extent1'] = transmission_paths.r.map(hierarchy[GSw_TransRestrict])
transmission_paths['extent2'] = transmission_paths.rr.map(hierarchy[GSw_TransRestrict])
transmission_paths['extents'] = (
    transmission_paths.extent1 + '_' + transmission_paths.extent2
)
### Add interconnect (so that we can drop cross-interconnect AC lines if using aggregated regions)
transmission_paths['interconnect1'] = transmission_paths.r.map(hierarchy.interconnect)
transmission_paths['interconnect2'] = transmission_paths.rr.map(hierarchy.interconnect)
transmission_paths['interconnects'] = (
    transmission_paths.interconnect1 + '_' + transmission_paths.interconnect2
)

### Drop links to Canada and Mexico if desired
if drop_canmex:
    transmission_paths.drop(
        transmission_paths.loc[
            (transmission_paths.r.map(hierarchy.country) != 'USA')
            | (transmission_paths.rr.map(hierarchy.country) != 'USA')
        ].index,
        inplace=True
    )

#%%### Aggregate regions if necessary (special case for multi-link; all the
### rest of the region-aggregation is handled in aggregate_regions.py)
if int(sw['GSw_AggregateRegions']):
    rb2aggreg = hierarchy.aggreg.copy()
    #%%### Get the "anchor" zone for each aggregation region (same as aggregate_regions.py)
    ## Get annual average load
    load = pd.read_csv(
        os.path.join(reedsdir, 'inputs', 'variability', 'multi_year', 'load.csv.gz'),
        index_col=0,
    ).mean().rename_axis('r').rename('MW').to_frame()
    ## Add column for new regions
    load['aggreg'] = load.index.map(rb2aggreg)
    ## Take the original zone with largest demand
    aggreg2anchorreg = load.groupby('aggreg').idxmax()['MW'].rename('rb')
    anchorreg2aggreg = pd.Series(index=aggreg2anchorreg.values, data=aggreg2anchorreg.index)

    #%%### Map original regions to aggregated regions
    for c in ['r','rr']:
        transmission_paths[c] = transmission_paths[c].map(rb2aggreg)
    transmission_paths['r_rr'] = transmission_paths.r + '_' + transmission_paths.rr
    ### Drop intra-aggreg paths and duplicate paths
    transmission_paths = transmission_paths.loc[
        transmission_paths.r != transmission_paths.rr
    ].drop_duplicates(subset=['r','rr']).copy()
    ### Drop AC links that cross interconnect boundaries
    transmission_paths = transmission_paths.loc[
        ~(
            (transmission_paths.interconnect1 != transmission_paths.interconnect2)
            & (transmission_paths.trtype.isin(['AC']))
        )
    ].copy()

    #%%### Keep anchor regions from tline_data, then map to aggregated regions
    tline_data = tline_data.loc[
        tline_data.index.get_level_values('r').isin(aggreg2anchorreg)
        & tline_data.index.get_level_values('rr').isin(aggreg2anchorreg)
    ].reset_index().copy()
    ### Map to aggregated retions
    for c in ['r','rr']:
        tline_data[c] = tline_data[c].map(anchorreg2aggreg)
    ## Switch back to original index
    tline_data = tline_data.set_index(['r','rr','trtype'])

#%% Add distance to transmission_paths
distances = []
for i in transmission_paths.index:
    r,rr,trtype = transmission_paths.loc[i,['r','rr','trtype']].values
    try:
        distance = tline_data.loc[(r,rr,trtype),'miles']
    except KeyError:
        distance = tline_data.loc[(rr,r,trtype),'miles']
    distances.append(distance)
transmission_paths['miles'] = distances

#%% Add losses
transmission_paths['loss'] = transmission_paths.apply(getloss, axis=1)

#%% Add costs
def cost(row):
    """Transmission line cost plus LCC converter if necessary [returns $/MW]"""
    out = (
        tline_data.loc[(row.r, row.rr, row.trtype), costcol]
        + (2 * cost_acdc_lcc if row.trtype in ['LCC','B2B'] else 0)
    )
    return out

transmission_paths['cost'] = transmission_paths.apply(cost, axis=1)

#%% For any duplicate r,rr pairs, drop the entry with higher weight
### (since we already know it's not optimal)
transmission_paths.drop(
    transmission_paths.loc[
        transmission_paths.sort_values(weight)[['r','rr']].duplicated(keep='first')
    ].index,
    inplace=True
)

### Check if there are entries with r,rr reversed
for r,rr in transmission_paths[['r','rr']].values:
    if transmission_paths.loc[(transmission_paths.r==rr)&(transmission_paths.rr==r)].shape[0] > 0:
        ## Drop the duplicates if aggregating (since we expect some)
        if int(sw['GSw_AggregateRegions']):
            print(f'dropping duplicate entry for {r},{rr}')
            transmission_paths.drop(
                transmission_paths.loc[(transmission_paths.r==r)&(transmission_paths.rr==rr)].index,
                inplace=True
            )
        else:
            dfdup = transmission_paths.loc[
                ((transmission_paths.r==rr)&(transmission_paths.rr==r))
                | (transmission_paths.r==r)&(transmission_paths.rr==rr)
            ]
            print(dfdup)
            raise Exception('Duplicate (r,rr) pairs')

### Drop nulls
transmission_paths.dropna(subset=[weight], inplace=True)

#%% Find optimal paths
print('reticulating splines...', flush=True)

### Simpler usage to apply to whole US:
### dfout = get_multilink_paths(transmission_paths=transmission_paths, weight=weight)

### Run for each region in desired spatial extent
dictout = {}
extents = list(set(
    transmission_paths.extent1.unique().tolist()
    + transmission_paths.extent2.unique().tolist()))
for extent in extents:
    transmission_paths_extent = transmission_paths.loc[
        (transmission_paths.extent1 == extent)
        & (transmission_paths.extent2 == extent)
    ]
    if not transmission_paths_extent.empty:
        dictout[extent] = get_multilink_paths(
            transmission_paths=transmission_paths_extent, weight=weight)
dfout = pd.concat(dictout, axis=0).reset_index(level=0,drop=True)

#%% Get path loss even if weight != loss (since we need it for Augur)
if weight != 'loss':
    linkloss = pd.concat(
        ### Define each path as (r,rr) and (rr,r)
        [transmission_paths[['r','rr','loss']],
        transmission_paths.rename(columns={'r':'rr','rr':'r'})[['r','rr','loss']]]
    ).drop_duplicates(subset=['r','rr']).set_index(['r','rr'])['loss']

    def get_pathloss(pathin):
        path = pathin.split('|')
        links = [(path[i],path[i+1]) for i in range(len(path)-1)]
        pathloss = sum([linkloss[link] for link in links])
        return pathloss

    dfout['loss'] = dfout.path.map(get_pathloss)

### No VSC lines (for compatibility with VSC macrogrid)
dfout['VSC'] = 0

#%% Save it
dfout.round(decimals).to_csv(os.path.join(inputs_case,'trans_multilink_paths.csv'))

#%%### Generate the linking matrix
### Format:
### * r: source region
### * rr: sink region
### * n: first node of link
### * nn: second node of link
### So path (A,B,C) would have two rows:
### (r, rr,  n, nn, linkage)
### (A,  C,  A,  B, YES)
### (A,  C,  B,  C, YES)

df = dfout.copy()
def make_linkage_set(dfin, transmission_paths=transmission_paths.copy(), sinklabel='rr'):
    df = dfin.copy()
    ### Make the trtype lookup
    trtype = (
        transmission_paths
        .append(transmission_paths[['rr','r','trtype']].rename(columns={'r':'rr','rr':'r'}))
        [['r','rr','trtype']].set_index(['r','rr']).trtype
        .to_dict()
    )
    vsc = dfin.VSC.to_dict()
    ### Drop the diagonal
    df.drop(df.loc[df.path.map(lambda x: '|' not in x)].index, inplace=True)
    ### One row per link
    linkage = []
    for (r,sink) in df.index:
        nodes = df.loc[(r,sink),'path'].split('|')
        for i in range(len(nodes)-1):
            linkage.append([r,sink,nodes[i],nodes[i+1]])
    ### First column starts with '*' so that GAMS reads it as a comment
    dflinkage = pd.DataFrame(linkage, columns=['*r',sinklabel,'n','nn'])

    ### For each (n,nn) pair, put the lower-numbered region in n
    dflinkage_sorted = dflinkage.copy()
    dflinkage_sorted[['n','nn']] = [
        sort_regions(i, int(sw['GSw_AggregateRegions'])) for i in dflinkage[['n','nn']].values]

    ### Add the transmission type
    dflinkage_sorted['trtype'] = dflinkage_sorted.apply(
        lambda row: 'VSC' if vsc[row['*r'], row.rr] else trtype[row.n, row.nn],
        axis=1)

    return dflinkage_sorted

#%% Make it
dflinkage_r = make_linkage_set(dfout)
### Repeat for r-ccreg version
# dflinkage_ccreg = make_linkage_set(dfout_ccreg, sinklabel='ccreg')

#%% Save the outputs
dflinkage_r.to_csv(
    os.path.join(inputs_case,'trans_multilink_segments.csv'), 
    index=False, header=True)


################################################################
#%% Create the inputs for the VSC DC macrogrid, if necessary ###

## We still want a single optimal multilink path between each pair of BAs to control
## problem size. So we calculate optimal paths through the VSC macrogrid and compare
## the cost of each path to the cost/loss of optimal paths through AC+LCC+B2B lines
## calculated above, keeping the better option. If an optimal path only exists in
## one of the two groups (VSC vs AC+LCC+B2B), keep whichever one exists.

if not GSw_VSC:
    finish()

#%% Load candidate corridors for VSC
### 'all' includes initial AC and B2B links, but not existing/proposed DC (which is all LCC)
vsc_links = pd.read_csv(
    os.path.join(
        reedsdir,'inputs','transmission',
        'transmission_capacity_future_{}.csv'.format(GSw_TransScen)),
    header=0,
).replace({'t':{0:int(scalars['firstyear_trans'])}})
### Only keep the VSC links
vsc_links = vsc_links.loc[vsc_links.trtype=='VSC',['r','rr']].drop_duplicates()

### Convert to aggregate regions if necessary
if int(sw['GSw_AggregateRegions']):
    for c in ['r','rr']:
        vsc_links[c] = vsc_links[c].map(rb2aggreg)
    vsc_links = vsc_links.loc[vsc_links.r != vsc_links.rr].drop_duplicates()

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

#%% Get the cost table for VSC
### Length-dependent cost (same as LCC DC but leave out converter)
transmission_paths_vsc = vsc_links.merge(
    tline_data[costcol].reset_index().replace({'LCC':'VSC'}),
    on=['r','rr','trtype'], how='left').rename(columns={costcol:'cost'})
### Length-dependent losses are the same for LCC and VSC (both assumed to be 500 kV)
transmission_paths_vsc.loss = transmission_paths_vsc.miles * tranloss_permile['VSC']
### The macrogrid is assumed to connect the entire USA, so we don't apply GSw_TransRestrict
dfout_vsc = get_multilink_paths(
    transmission_paths=transmission_paths_vsc, weight=weight)
### Each optimized VSC multilink path gets 2x cost_acdc_vsc and 2x converter losses,
### one for each endpoint. The full line + converter losses are used in Augur, where
### we only care about losses along the entire path; for ReEDS they're treated separately
dfout_vsc.cost += (2 * cost_acdc_vsc)
linkloss = pd.concat(
    ### Define each path as (r,rr) and (rr,r)
    [transmission_paths_vsc[['r','rr','loss']], 
    transmission_paths_vsc.rename(columns={'r':'rr','rr':'r'})[['r','rr','loss']]]
).drop_duplicates(subset=['r','rr']).set_index(['r','rr'])['loss']

def get_pathloss_vsc(pathin):
    path = pathin.split('|')
    links = [(path[i],path[i+1]) for i in range(len(path)-1)]
    pathloss = sum([linkloss[link] for link in links]) + 2 * tranloss_fixed['VSC']
    return pathloss

dfout_vsc['loss'] = dfout_vsc.path.map(get_pathloss_vsc)

### Compare to the optimal paths through AC+LCC+B2B and keep the better option
## Missing values of either type get infinite cost/losses to keep them from being picked
dfout_both = pd.concat({'nonvsc':dfout, 'vsc':dfout_vsc}, axis=1).fillna(np.inf)
keepvsc = dfout_both['vsc'][weight] < dfout_both['nonvsc'][weight]
dfout_best = pd.concat([
    dfout_both['nonvsc'].loc[~keepvsc].assign(VSC=0),
    dfout_both['vsc'].loc[keepvsc].assign(VSC=1)
], axis=0)

#%% Save it, overwriting the old version
dfout_best.round(decimals).to_csv(os.path.join(inputs_case,'trans_multilink_paths.csv'))


#%% Generate the linking matrix
dflinkage_vsc = make_linkage_set(dfout_best)

#%% Save it, overwriting the old version
dflinkage_vsc.to_csv(
    os.path.join(inputs_case,'trans_multilink_segments.csv'), 
    index=False, header=True)


#%% Save the (r,rr) pairs for which VSC is optimal, so that ReEDS knows
### it must build VSC converters at either end to get the curtailment reduction
dfout_best.loc[dfout_best.VSC==1].reset_index()[['r','rr']].rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case,'trans_multilink_converters.csv'),
    index=False, header=True)

#%%### Overwrite the ReEDS files written above to include VSC
### tranloss
pd.concat([
    tranloss[['r','rr','trtype','loss']],
    vsc_links[['r','rr','trtype','loss']],
    vsc_links[['rr','r','trtype','loss']].rename(columns={'r':'rr','rr':'r'}),
], axis=0).round(decimals).drop_duplicates().rename(columns={'r':'*r','trtype':'trtype'}).to_csv(
    os.path.join(inputs_case,'tranloss.csv'), index=False, header=True
)

#%% transmission_distance
pd.concat([
    transmission_distance.reset_index()[['r','rr','trtype','miles']],
    vsc_links[['r','rr','trtype','miles']],
    vsc_links[['rr','r','trtype','miles']].rename(columns={'r':'rr','rr':'r'}),
], axis=0).round(3).drop_duplicates().rename(
    columns={'r':'*r','trtype':'trtype','miles':'miles'}
).to_csv(
    os.path.join(inputs_case,'transmission_distance.csv'), index=False, header=True
)

#%% Write investment sets for ReEDS
pd.concat([
    vsc_links[['r','rr']],
    vsc_links[['rr','r']].rename(columns={'r':'rr','rr':'r'})
]).drop_duplicates().rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case, 'transmission_vsc_routes.csv'),
    index=False,
)

#%% Finish the timer
finish()
