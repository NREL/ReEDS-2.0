"""
main contact: Patrick.Brown@nrel.gov
Notes:
* 'DC' refers only to LCC DC lines; 'VSC' refers to VSC macrogrid lines
* AC/DC converter costs and losses are bundled in with LCC DC lines, but are
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
### Multiply losses by 3x for lines beginning or ending in New England
### (3x is the ratio of 345kV/500kV losses from the WECC/TEPPC calculator)
extra_newengland_loss_multiplier = 3

#%% Argument inputs
parser = argparse.ArgumentParser(description="Format and write climate inputs")
parser.add_argument('-i', '--reedsdir', help='ReEDS directory')
parser.add_argument('-o', '--inputs_case', help='output directory (inputs_case)')
parser.add_argument('-t', '--GSw_TranScen', type=str, default='default',
                    help='transmission scenario (e.g. default, HVDC_Certain, HVDC_Possible)')
parser.add_argument('-l', '--GSw_TransMultiLink', type=int, default=0)
parser.add_argument('-e', '--GSw_TransExtent', type=str, default='country',
                    help='Allowed extent of multi-link transmission paths; see hierarchy.csv',
                    choices=['country','interconnect','nercr','rto', 'rto_agg', 'st'])
parser.add_argument('-w', '--weight', type=str, default='loss',
                    choices=['distance','loss','cost'],
                    help='metric to minimize for optimal multi-link paths')
parser.add_argument('-v', '--GSw_VSC', type=int, default=0,
                    help='turn on/off multi-terminal VSC HVDC macrogrid')
parser.add_argument('-b', '--GSw_VSC_BAlist', type=str, default='all',
                    help='Suffix of file with list of candidate BAs for VSC AC/DC converters')
parser.add_argument('-s', '--GSw_VSC_LinkList', type=str, default='all',
                    help='Suffix of file with list of candidate links for VSC HVDC lines')

args = parser.parse_args()
reedsdir = args.reedsdir
inputs_case = args.inputs_case
GSw_TranScen = args.GSw_TranScen
GSw_TransMultiLink = args.GSw_TransMultiLink
GSw_TransExtent = args.GSw_TransExtent
weight = args.weight
GSw_VSC = args.GSw_VSC
GSw_VSC_BAlist = args.GSw_VSC_BAlist
GSw_VSC_LinkList = args.GSw_VSC_LinkList

# #%% DEBUG
# reedsdir = os.path.expanduser('~/github/ReEDS-2.0/')
# inputs_case = os.path.join(reedsdir,'runs','v20210630_VSC1_Z35_VSC_all','inputs_case','')
# GSw_TranScen = 'VSC_ACpaths'
# GSw_TransMultiLink = 1
# GSw_TransExtent = 'country'
# weight = 'cost'
# GSw_VSC = 1
# GSw_VSC_BAlist = 'all'
# GSw_VSC_LinkList = 'all'

#################
#%% FUNCTIONS ###

def scalar_csv_to_txt(path_to_scalar_csv):
    """
    Write a scalar csv to GAMS-readable text
    Format of csv should be: scalar,value,comment
    """
    ### Load the csv
    dfscalar = pd.read_csv(
        path_to_scalar_csv,
        header=None, names=['scalar','value','comment'], index_col='scalar')
    ### Create the GAMS-readable string
    scalartext = '\n'.join([
        'scalar {:<25} "{:<100}" /{}/ ;'.format(
            i, dfscalar.loc[i,'comment'], dfscalar.loc[i,'value'])
        for i in dfscalar.index
    ])
    ### Write it to a file, replacing .csv with .txt in the filename
    with open(path_to_scalar_csv.replace('.csv','.txt'), 'w') as w:
        w.write(scalartext)

    return dfscalar


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

def sort_regions(regions):
    return ['p{}'.format(r) for r in sorted([int(r[1:]) for r in regions])]

def finish(inputs_case=inputs_case):
    toc(tic=tic, year=0, process='input_processing/transmission_multilink.py', 
        path=os.path.join(inputs_case,'..'))
    print('Finished transmission_multilink.py', flush=True)
    quit()

#################
#%% PROCEDURE ###

#%% Get the spatial hierarchy
hierarchy = pd.read_csv(
    os.path.join(reedsdir,'inputs','hierarchy.csv'),
    names=['r','nercr','nercr_new','rto','rto_agg','cendiv','st',
        'interconnect','country','customreg','ccreg','usda'],
)
### Clean up the first and last columns
hierarchy.r = hierarchy.r.map(lambda x: x.replace('(',''))
hierarchy.ccreg = hierarchy.ccreg.map(lambda x: x.replace(')','').replace(',',''))
### Set r as the index
hierarchy.set_index('r',inplace=True)

#%%### Get single-link distances and losses; write transmission scalars
### Get single-link distances [miles]
transmission_distance = pd.read_csv(
    os.path.join(reedsdir,'inputs','transmission','transmission_distance.csv')
)

transmission_distance['r_rr'] = transmission_distance.r + '_' + transmission_distance.rr

### Merge the AC and DC columns
transmission_distance = transmission_distance.melt(
    id_vars=['r','rr','Source','Project(s)','Vintage','r_rr'],
    value_vars=['AC','DC',], var_name='transtype', value_name='distance')

### Drop the entries with null distance (AC entries from NARIS)
transmission_distance.drop(
    transmission_distance.loc[transmission_distance.distance.isnull()].index,
    inplace=True)

### Make sure there are no duplicates
if (transmission_distance.loc[
        transmission_distance[['r','rr','transtype']].duplicated(keep=False)
    ].shape[0] != 0):
        print(
            transmission_distance.loc[
                transmission_distance[['r','rr','transtype']].duplicated(keep=False),
                ['r','rr','Source','distance','transtype','Project(s)']
            ].sort_values(['r','rr'])
        )
        raise Exception('Duplicate entries in transmission_distance')


### Load and write the transmission scalars
scalars_transmission = scalar_csv_to_txt(os.path.join(inputs_case,'scalars_transmission.csv'))
### Put some in dicts for easier access
cost_acdc_lcc = scalars_transmission.loc['cost_acdc_lcc','value']
cost_acdc_vsc = scalars_transmission.loc['cost_acdc_vsc','value']
tranloss_permile = {'AC': scalars_transmission.loc['tranloss_permile_ac','value'],
                    'DC': scalars_transmission.loc['tranloss_permile_dc','value'],}
tranloss_fixed = {
    'AC': 1 - scalars_transmission.loc['converter_efficiency_ac','value'],
    'DC': 1 - scalars_transmission.loc['converter_efficiency_lcc','value'],
    'VSC': 1 - scalars_transmission.loc['converter_efficiency_vsc','value'],
}

### Calculate losses
def getloss(row):
    """
    Fixed losses are entered as per-endpoint values (e.g. for each AC-DC converter station
    on a DC line). There are two endpoints per line, so multiply fixed losses by 2.
    ! NOTE: Change this approach if converter stations are modeled explicitly
    """
    return row.distance * tranloss_permile[row.transtype] + tranloss_fixed[row.transtype] * 2

transmission_distance['loss'] = transmission_distance.apply(getloss, axis=1)

### Apply the New-England-specific losses.
### To only apply it to lines within New England (not lines into and out of New England,
### change '|' to '&'.
### ! NOTE: Other region-dependent losses could be added here as well
transmission_distance.loc[
    transmission_distance.r.isin(hierarchy.loc[hierarchy.cendiv=='NE'].index)
    | transmission_distance.rr.isin(hierarchy.loc[hierarchy.cendiv=='NE'].index),
    'loss'
] *= extra_newengland_loss_multiplier

### Write the single-link loss table (adding * to make GAMS read column names as comment)
(transmission_distance[['r','rr','transtype','loss']]
 .round(decimals).rename(columns={'r':'*r','transtype':'trtype'})
).to_csv(os.path.join(inputs_case,'tranloss.csv'), index=False, header=True)

### Set the identifier index for easier indexing later
transmission_distance.set_index(['r','rr','transtype'], inplace=True)

#%% Write the regional transmission FOM costs [$/MW-mile/year]
### Load the transmission component costs
transmission_cost_components = pd.read_csv(
    os.path.join(reedsdir,'inputs','transmission','transmission_line_cost_components.csv'),
    header=0, index_col='r',
)
trans_fom_frac = scalars_transmission.loc['trans_fom_frac','value']
trans_fom_region_mult = int(scalars_transmission.loc['trans_fom_region_mult','value'])
if trans_fom_region_mult:
    cost_columns = ['AC_final','DC_final']
else:
    cost_columns = ['AC_base','DC_base']

trans_fom = (
    ## Take capital cost in $/MW-mile
    transmission_cost_components[cost_columns]
    .rename(columns=dict(zip(cost_columns, ['AC','DC'])))
    ## Multiply by fraction/year to get $/MW-mile/year
    * trans_fom_frac
)

### Write it
trans_fom.round(decimals).to_csv(os.path.join(inputs_case,'trans_fom.csv'))

#%% Process the initial-capacity, future-capacity, and distance files
### trancap_init
trancap_init = pd.read_csv(
    os.path.join(reedsdir,'inputs','transmission','transmission_capacity_initial.csv')
).melt(
    id_vars=['r','rr'], value_vars=['AC','DC'],
    var_name='trtype', value_name='value',
)
trancap_init.loc[
    trancap_init.value > 0
].rename(columns={'r':'*r'}).round(3).to_csv(
    os.path.join(inputs_case,'trancap_init.csv'),
    index=False,
)

### trancap_fut
trancap_fut = pd.read_csv(
    os.path.join(
        reedsdir,'inputs','transmission','transmission_capacity_future_{}.csv'
    ).format(GSw_TranScen)
).melt(
    id_vars=['r','rr','status','t'], value_vars=['AC','DC'],
    var_name='trtype', value_name='value',
)
trancap_fut.loc[
    trancap_fut.value > 0
].rename(columns={'r':'*r'}).round(3).to_csv(
    os.path.join(inputs_case,'trancap_fut.csv'),
    index=False,
)

### distance
(
    transmission_distance.distance.round(3)
    .reset_index().rename(columns={'r':'*r','transtype':'trtype'})
).to_csv(
    os.path.join(inputs_case,'transmission_distance.csv'),
    index=False,
)

##########################################################
#%% Quit here if multi-link transmission assessment is off
if not GSw_TransMultiLink:
    print('Skipping the rest of transmission_multilink.py', flush=True)
    finish()

#%% Load existing and possible transmission capacity
transmission_capacity = {
    ending.lower(): pd.read_csv(os.path.join(
        reedsdir,'inputs','transmission','transmission_capacity_{}.csv'.format(ending)))
    for ending in ['initial','future_{}'.format(GSw_TranScen)]
}
for ending in transmission_capacity:
    transmission_capacity[ending.lower()]['r_rr'] = (
        transmission_capacity[ending.lower()].r + '_' + transmission_capacity[ending.lower()].rr)

#%% Include extra lines from chosen transmission scenario
addlinks = [
    r_rr for r_rr in transmission_capacity['future_{}'.format(GSw_TranScen).lower()].r_rr.values
    if r_rr not in transmission_capacity['initial'].r_rr.values
]

#%% Include future links based on transmission scenario
transmission_paths = transmission_capacity['initial'].append(
    transmission_capacity['future_{}'.format(GSw_TranScen).lower()].loc[
        transmission_capacity['future_{}'.format(GSw_TranScen).lower()].r_rr.isin(addlinks)
    ],
    ignore_index=True
)
### Remove rows that are marked as "removed" in Notes column
transmission_paths.drop(
    transmission_paths.loc[transmission_paths.Notes.map(lambda x: 'removed' in str(x))].index,
    inplace=True
)
### Get the rows with both AC and DC capacity
duprows = transmission_paths.loc[
    (transmission_paths.DC != 0) & (transmission_paths.AC != 0)]

### Split the rows with both AC/DC into two rows
for i in duprows.index:
    ### Add a line for DC only
    transmission_paths = transmission_paths.append(duprows.loc[i], ignore_index=True)
    ### Zero out the original DC
    transmission_paths.loc[i,'DC'] = 0
    ### Zero out the new AC
    transmission_paths.loc[transmission_paths.iloc[-1].name,'AC'] = 0

if (transmission_paths.loc[
        (transmission_paths.AC!=0) & (transmission_paths.DC!=0)
    ].shape[0] != 0):
        raise Exception('Duplicate entries in transmission_paths')
### Identify line type
transmission_paths['transtype'] = transmission_paths.AC.map(
    lambda x: 'AC' if x != 0 else 'DC')

### Add chosen multi-link extent
transmission_paths['extent1'] = transmission_paths.r.map(hierarchy[GSw_TransExtent])
transmission_paths['extent2'] = transmission_paths.rr.map(hierarchy[GSw_TransExtent])
transmission_paths['extents'] = (
    transmission_paths.extent1 + '_' + transmission_paths.extent2
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

#%% Add distance to transmission_paths
distances = []
for i in transmission_paths.index:
    r,rr,transtype = transmission_paths.loc[i,['r','rr','transtype']].values
    try:
        distance = transmission_distance.loc[(r,rr,transtype),'distance']
    except KeyError:
        distance = transmission_distance.loc[(rr,r,transtype),'distance']
    distances.append(distance)
transmission_paths['distance'] = distances

#%% Add losses
transmission_paths['loss'] = transmission_paths.apply(getloss, axis=1)

#%% Add costs
### $/MW-mile cost
transmission_line_cost = pd.read_csv(
    os.path.join(reedsdir,'inputs','transmission','transmission_line_cost.csv'),
    header=0, index_col='r',
)

def cost(row):
    """Average of regional costs time distance. Returns $/MW."""
    out = (
        (transmission_line_cost.loc[row['r'],row['transtype']]
         + transmission_line_cost.loc[row['rr'],row['transtype']]
        ) / 2
        * row['distance']
        + (2 * cost_acdc_lcc if row['DC'] else 0)
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
        print(transmission_paths.loc[(transmission_paths.r==r)&(transmission_paths.rr==rr)])
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
dfout.to_csv(os.path.join(inputs_case,'trans-multilink-paths.csv'))

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
    trtype = transmission_paths.set_index(['r','rr']).transtype.to_dict()
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
    dflinkage_sorted[['n','nn']] = [sort_regions(i) for i in dflinkage[['n','nn']].values]

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
    os.path.join(inputs_case,'trans-multilink-segments.csv'), 
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

### Load candidate AC/DC VSC converter locations
vsc_bas = pd.read_csv(
    os.path.join(reedsdir,'inputs','transmission',
                 'converter_vsc_bas_{}.csv'.format(GSw_VSC_BAlist)),
    squeeze=True, header=None, names=['r'],
)

#%% Load candidate corridors for VSC
### 'all' includes initial AC and B2B links, but not existing/proposed DC (which is all LCC)
vsc_links = pd.read_csv(
    os.path.join(reedsdir,'inputs','transmission',
                 'transmission_vsc_links_{}.csv'.format(GSw_VSC_LinkList)),
    header=0, names=['r','rr'],
)
### Add distance and losses (leaving out converter losses, which are treated separately)
distance_lookup = (
    transmission_distance
    .xs(slice(None),level='transtype')['distance']
    .reset_index()
    .drop_duplicates()
    .set_index(['r','rr'])
    ['distance']
    .to_dict()
)
vsc_links['transtype'] = 'VSC'
vsc_links['distance'] = vsc_links.apply(
    lambda row: distance_lookup[row.r, row.rr],
    axis=1
)
vsc_links['loss'] = vsc_links.distance * tranloss_permile['DC']

#%% Get the cost table for VSC
def cost_vsc(row):
    """
    Average of regional costs time distance. Returns $/MW.
    Differs from cost() in that here we only use DC, and don't apply the converter cost
    (which applies to each multilink line, not to each link)
    """
    out = (
        (transmission_line_cost.loc[row['r'],'DC'] 
         + transmission_line_cost.loc[row['rr'],'DC']
        ) / 2 
        * row['distance']
    )
    return out

transmission_paths_vsc = (transmission_paths_extent.merge(vsc_links[['r','rr']], on=['r','rr']))
transmission_paths_vsc.cost = transmission_paths_vsc.apply(cost_vsc, axis=1)
transmission_paths_vsc.loss = transmission_paths_vsc.distance * tranloss_permile['DC']
### The macrogrid is assumed to connect the entire USA, so we don't apply GSw_TransExtent
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
dfout_best.to_csv(os.path.join(inputs_case,'trans-multilink-paths.csv'))


#%% Generate the linking matrix
dflinkage_vsc = make_linkage_set(dfout_best)

#%% Save it, overwriting the old version
dflinkage_vsc.to_csv(
    os.path.join(inputs_case,'trans-multilink-segments.csv'), 
    index=False, header=True)


#%% Save the (r,rr) pairs for which VSC is optimal, so that ReEDS knows
### it must build VSC converters at either end to get the curtailment reduction
dfout_best.loc[dfout_best.VSC==1].reset_index()[['r','rr']].rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case,'trans-multilink-converters.csv'),
    index=False, header=True)


#%% Add VSC lines to tranloss(r,rr,trtype) used in ReEDS
pd.concat([
    transmission_distance.reset_index()[['r','rr','transtype','loss']],
    vsc_links[['r','rr','transtype','loss']],
    vsc_links[['rr','r','transtype','loss']].rename(columns={'r':'rr','rr':'r'}),
], axis=0).round(decimals).drop_duplicates().rename(columns={'r':'*r','transtype':'trtype'}).to_csv(
    os.path.join(inputs_case,'tranloss.csv'), index=False, header=True
)

#%% Add VSC lines to distance(r,rr,trtype) used in ReEDS
pd.concat([
    transmission_distance.reset_index()[['r','rr','transtype','distance']],
    vsc_links[['r','rr','transtype','distance']],
    vsc_links[['rr','r','transtype','distance']].rename(columns={'r':'rr','rr':'r'}),
], axis=0).round(3).drop_duplicates().rename(columns={'r':'*r','transtype':'trtype'}).to_csv(
    os.path.join(inputs_case,'transmission_distance.csv'), index=False, header=True
)

#%% Write investment sets for ReEDS
pd.concat([
    vsc_links[['r','rr']],
    vsc_links[['rr','r']].rename(columns={'r':'rr','rr':'r'})
]).drop_duplicates().rename(columns={'r':'*r'}).to_csv(
    os.path.join(inputs_case, 'transmission_vsc_routes.csv'),
    index=False, sep='.',
)
vsc_bas.to_csv(
    os.path.join(inputs_case, 'transmission_vsc_regions.csv'),
    index=False, header=False,
)

#%% Finish the timer
finish()
