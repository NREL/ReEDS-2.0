#%% Imports
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import argparse
import subprocess as sp
import platform
import cmocean
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
from reeds.results import SLIDE_HEIGHT

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
reeds.plots.plotparams()


#%% Argument inputs
parser = argparse.ArgumentParser(
    description='Compare multiple ReEDS cases',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    'caselist', type=str, nargs='+',
    help=('space-delimited list of cases to plot, OR shared casename prefix, '
          'OR csv file of cases. The first case is treated as the base case '
          'unless a different one is provided via the --basecase/-b argument.'))
parser.add_argument(
    '--casenames', '-n', type=str, default='',
    help='comma-delimited list of shorter case names to use in plots')
parser.add_argument(
    '--titleshorten', '-s', type=str, default='',
    help='characters to cut from start of case name (only used if no casenames)')
parser.add_argument(
    '--plotyear', '-y', type=int, default=0,
    help='Year to plot (or 0 for last year)')
parser.add_argument(
    '--label', '-l', type=str, default='d1h',
    help='Label for PCM outputs (same as in run_pcm.py)')
parser.add_argument(
    '--basecase', '-b', type=str, default='',
    help='Substring of case path to use as default (if empty, uses first case in list)')

args = parser.parse_args()
caselist = args.caselist
casenames = args.casenames
try:
    titleshorten = int(args.titleshorten)
except ValueError:
    titleshorten = len(args.titleshorten)
plotyear = args.plotyear
label = args.label
basecase_in = args.basecase
interactive = False

#%% Inputs for testing
# reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# caselist = [os.path.join(reeds_path,'postprocessing','example.csv')]
# casenames = ''
# titleshorten = 0
# plotyear = 2035
# label = 'd1h'
# basecase_in = ''
# interactive = True


#%% Parse arguments
cases, colors, basecase, basemap = reeds.results.parse_caselist(
    caselist,
    casenames,
    basecase_in,
    titleshorten,
)
maxlength = max([len(c) for c in cases])
if not plotyear:
    plotyear = max(
        pd.read_csv(os.path.join(cases[basecase], 'inputs_case', 'modeledyears.csv'))
        .columns.astype(int)
        .values
    )

## Arrange the maps
nrows, ncols, coords = reeds.plots.get_coordinates(cases, aspect=2)

### Set up powerpoint file
prs = reeds.results.init_pptx()


#%% Create output folder
firstcasepath = list(cases.values())[0]
outpath = os.path.join(firstcasepath, 'outputs', 'comparisons')
os.makedirs(outpath, exist_ok=True)
## Remove disallowed characters and clip filename to max length
max_filename_length = 250
savename = os.path.join(
    outpath,
    (f"pcm_{label}_{plotyear}-{','.join(cases.keys())}"
     .replace(':','').replace('/','').replace(' ','').replace('\\n','').replace('\n','')
     [:max_filename_length-len('.pptx')]) + '.pptx'
)
print(f'Saving results to {savename}')


#%%### Read outputs ######
dictin_dropped = {
    case: reeds.io.read_output(
        os.path.join(cases[case], 'outputs', f'pcm_{label}_{plotyear}', 'outputs.h5'),
        'dropped_load',
    )
    for case in cases
}


###### Plots ######
#%% Total dropped load
dfdropped = pd.Series({
    case:
    dictin_dropped[case].loc[dictin_dropped[case].t==plotyear].Value.sum() / 1e3
    for case in cases
})

plt.close()
f,ax = plt.subplots()
ax.bar(
    x=dfdropped.index,
    height=dfdropped.values,
    color=[colors[case] for case in dfdropped.index],
)
ax.set_ylabel(f'Dropped load {plotyear} [GWh]')
ax.set_xticks(range(len(cases)))
ax.set_xticklabels(cases.keys(), rotation=45, rotation_mode='anchor', ha='right')
reeds.plots.despine(ax)
## Save it
title = 'Total dropped load'
slide = reeds.results.add_to_pptx(title, prs=prs, width=None, height=SLIDE_HEIGHT)
if interactive:
    plt.show()


#%% Regions
scale = 3
cmap = cmocean.cm.rain
dfmaps = {case: reeds.io.get_dfmap(cases[case]) for case in cases}

nrows, ncols, coords = reeds.plots.get_coordinates(cases)

plt.close()
f,ax = plt.subplots(
    nrows, ncols, figsize=(scale*ncols, scale*nrows*0.75), sharex=True, sharey=True,
    gridspec_kw={'wspace':0, 'hspace':-0.1}, dpi=200,
)
for case in cases:
    _ax = ax[coords[case]]
    dfmaps[case]['st'].plot(ax=_ax, facecolor='none', edgecolor='C7', lw=0.1)
    dfmaps[case]['transreg'].plot(ax=_ax, facecolor='none', edgecolor='k', lw=0.2)
    for r, row in dfmaps[case]['r'].iterrows():
        _ax.annotate(
            r.strip('p'), (row.centroid_x, row.centroid_y),
            ha='center', va='center', fontsize=3,
            color='0.8',
        )
    df = dfmaps[case]['r'].copy()
    df['GWh'] = (
        dictin_dropped[case].loc[dictin_dropped[case].t==plotyear]
        .groupby('r').Value.sum()
        / 1e3
    )
    df.plot(ax=_ax, column='GWh', cmap=cmap)
    _ax.axis('off')
    _ax.set_title(case, y=0.9)
reeds.plots.trim_subplots(ax, nrows, ncols, len(cases))
## Save it
title = 'Dropped load'
slide = reeds.results.add_to_pptx(title, prs=prs)
if interactive:
    plt.show()


#%% Timing of dropped load
dfdropped = pd.Series({
    case:
    dictin_dropped[case].loc[dictin_dropped[case].t==plotyear].Value.sum() / 1e3
    for case in cases
})

for case in dfdropped.loc[dfdropped > 0].index:
    sw = reeds.io.get_switches(cases[case])
    y = int(sw.GSw_HourlyWeatherYears.split('_')[0])
    fullyear = pd.date_range(f'{y}-01-01', f'{y+1}-01-01', freq='H', tz='Etc/GMT+6')[:8760]
    df = (dictin_dropped[case].loc[dictin_dropped[case].t==plotyear]).groupby('h').Value.sum()
    df.index = df.index.map(reeds.timeseries.h2timestamp)
    df = df.reindex(fullyear).fillna(0)

    plt.close()
    f, ax = reeds.plots.plotyearbymonth(df, colors='r')
    # ax[0].set_title(case, fontsize=14)
    ## Save it
    title = f'Dropped load ({case})'
    slide = reeds.results.add_to_pptx(title, prs=prs)
    if interactive:
        plt.show()


#%%### Dispatch
max_regions = 3
max_arrows = 100

dfdropped = pd.concat({
    case: (
        dictin_dropped[case].loc[dictin_dropped[case].t==plotyear]
        .groupby('r').Value.sum()
    )
    for case in cases
})

plot_regions = list(
    dfdropped
    .groupby('r').max()
    .sort_values(ascending=False)
    .index[:max_regions]
)

for r in plot_regions:
    for case in cases:
        try:
            title = f"{case}: {r} ({dfdropped[case][r]/1e3:.1f} GWh)"
        except KeyError:
            continue
        sw = reeds.io.get_switches(cases[case])
        y = int(sw.GSw_HourlyWeatherYears.split('_')[0])
        fullyear = pd.date_range(f'{y}-01-01', f'{y+1}-01-01', freq='H', tz='Etc/GMT+6')[:8760]
        ## Dispatch
        plt.close()
        f, ax, dfplot = reeds.reedsplots.plot_dispatch_yearbymonth(
            case=cases[case],
            t=plotyear,
            periodtype=f'pcm_{label}',
            highlight_rep_periods=False,
            region=f'r/{r}',
        )
        ## Dropped, as white areas at the bottom
        df = (
            dictin_dropped[case]
            .loc[
                (dictin_dropped[case].t==plotyear)
                & (dictin_dropped[case].r==r)
            ]
        ).groupby('h').Value.sum()
        df.index = df.index.map(reeds.timeseries.h2timestamp)
        df = df.reindex(fullyear).fillna(0) / 1e3
        reeds.plots.plotyearbymonth(df, colors='w', f=f, ax=ax)
        ## Annotate the hours with dropped load
        nonzero_dropped_load = df.loc[df > 0].sort_values(ascending=False)
        for i in range(min(max_arrows, len(nonzero_dropped_load))):
            dt = nonzero_dropped_load.index[i]
            row = dt.month - 1
            ## plots.plotyearbymonth() plots each month as January 2001
            _dt = pd.Timestamp(f'2001-01-{dt.day:02} {dt.hour}:00:00')
            ax[row].annotate(
                '',
                xy=(_dt, -ax[row].get_ylim()[1]*0.05),
                xytext=(_dt, -ax[row].get_ylim()[1]*0.25),
                arrowprops={
                    'headwidth':2.5,
                    'headlength':3,
                    'width':0.5,
                    'color':'k',
                    'lw':0.5,
                },
                annotation_clip=False,
            )
        ## Save it
        slide = reeds.results.add_to_pptx(title, prs=prs)
        if interactive:
            plt.show()


#%% Save the powerpoint file
prs.save(savename)
print(f'\ncompare_casegroup.py results saved to:\n{savename}')

### Open it
if sys.platform == 'darwin':
    sp.run(f"open '{savename}'", shell=True)
elif platform.system() == 'Windows':
    sp.run(f'"{savename}"', shell=True)
