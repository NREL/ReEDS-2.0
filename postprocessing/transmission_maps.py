#%% IMPORTS
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import os, sys, math, site

import geopandas as gpd
os.environ['PROJ_NETWORK'] = 'OFF'

reedspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
site.addsitedir(os.path.join(reedspath,'postprocessing'))
import plots
import reedsplots as rplots
plots.plotparams()

##########
#%% INPUTS
## Note that if your case builds lots of transmission, wscale might
## need to be reduced to avoid too much overlap in the plotted routes
wscale_straight = 0.0004
wscale_routes = 1.5
routes = False
## Note that if you change the CRS you'll probably need to change
## the position of the annotations
crs = 'ESRI:102008'
### For generation capacity map
cmap = plt.cm.gist_earth_r
ncols = 3
techs = [
    'Utility PV', 'Land-based wind', 'Offshore wind',
    'Nuclear', 'H2 turbine', 'Battery/PSH',
    'Fossil', 'Fossil+CCS', 'CO2 removal',
]
techmap = {
    **{f'upv_{i}':'Utility PV' for i in range(20)},
    **{f'dupv_{i}':'Utility PV' for i in range(20)},
    **{f'wind-ons_{i}':'Land-based wind' for i in range(20)},
    **{f'wind-ofs_{i}':'Offshore wind' for i in range(20)},
    **dict(zip(['nuclear','nuclear-smr'], ['Nuclear']*20)),
    **dict(zip(
        ['gas-cc_re-cc','gas-ct_re-ct','re-cc','re-ct',
         'gas-cc_h2-cc','gas-ct_h2-ct','h2-cc','h2-ct',],
        ['H2 turbine']*20)),
    **{f'battery_{i}':'Battery/PSH' for i in range(20)}, **{'pumped-hydro':'Battery/PSH'},
    **dict(zip(
        ['coal-igcc', 'coaloldscr', 'coalolduns', 'gas-cc', 'gas-ct', 'coal-new', 'o-g-s',],
        ['Fossil']*20)),
    **dict(zip(
        ['gas-cc_gas-cc-ccs_mod','gas-cc_gas-cc-ccs_max','gas-cc-ccs_mod','gas-cc-ccs_max',
         'gas-cc_gas-cc-ccs_mod','coal-igcc_coal-ccs_mod','coal-new_coal-ccs_mod',
        'coaloldscr_coal-ccs_mod','coalolduns_coal-ccs_mod','cofirenew_coal-ccs_mod',
        'cofireold_coal-ccs_mod','gas-cc_gas-cc-ccs_max','coal-igcc_coal-ccs_max',
        'coal-new_coal-ccs_max','coaloldscr_coal-ccs_max','coalolduns_coal-ccs_max',
        'cofirenew_coal-ccs_max','cofireold_coal-ccs_max',],
        ['Fossil+CCS']*50)),
    **dict(zip(['dac','beccs_mod','beccs_max'],['CO2 removal']*20)),
}
### For VRE siting & transmission maps
transalpha = 0.25
transcolor = 'k'
ms = 1.15
gen_cmap = {
    'wind-ons':plt.cm.Blues,
    'upv':plt.cm.Reds,
    'wind-ofs':plt.cm.Purples,
}
### For testing
interactive = False
write = True

###################
#%% ARGUMENT INPUTS

import argparse
parser = argparse.ArgumentParser(description='transmission maps')
parser.add_argument('--casedir', '-c', type=str,
                    help='path to ReEDS run folder')
parser.add_argument('--year', '-y', type=int,
                    help='year to plot')
parser.add_argument('--routes', '-r', action='store_true',
                    help='if True, show actual transmission routes')

args = parser.parse_args()
casedir = args.casedir
year = args.year
routes = args.routes

# #%% Inputs for testing
# casedir = (
#     '/Volumes/ReEDS/FY22-NTP/Candidates/Archive/ReEDSruns/20220929/'
#     'v20220929_PTDFg0_VSC_DemHi_100by2035EarlyPhaseout__core')
# year = 2050
# routes = False
# interactive = True

#############
#%% PROCEDURE
#%% direct print and errors to log file
import sys
sys.stdout = open(os.path.join(casedir, 'gamslog.txt'), 'a')
sys.stderr = open(os.path.join(casedir, 'gamslog.txt'), 'a')

#%% Make output directory
savepath = os.path.join(casedir,'outputs','maps')
os.makedirs(savepath, exist_ok=True)

#%% Load colors
trtypes = pd.read_csv(
    os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
    index_col='raw')['display']
colors = pd.read_csv(
    os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
    index_col='order')['color']
colors = colors.append(trtypes.map(colors))

#%% Load switches
sw = pd.read_csv(
    os.path.join(casedir, 'inputs_case', 'switches.csv'),
    header=None, index_col=0, squeeze=True)
years = pd.read_csv(
    os.path.join(casedir,'inputs_case','modeledyears.csv')
).columns.astype(int).values
yearstep = years[-1] - years[-2]

#%% Transmission line map with disaggregated transmission types
try:
    plt.close()
    f,ax = rplots.plot_trans_onecase(
        case=casedir, pcalabel=False,
        routes=routes, simpletypes=None,
        wscale=(wscale_routes if routes else wscale_straight),
        yearlabel=False, year=year, alpha=1.0,
    )
    ax.annotate(
        'AC', (-1.75e6, -1.12e6), ha='center', va='top',
        weight='bold', fontsize=15, color=colors['ac'])
    ax.annotate(
        'LCC/B2B DC',
        (-1.75e6, -1.24e6), ha='center', va='top',
        weight='bold', fontsize=15, color=colors['lcc'])
    ax.annotate(
        'VSC DC', (-1.75e6, -1.36e6), ha='center', va='top',
        weight='bold', fontsize=15, color=colors['vsc'])
    if write:
        plt.savefig(os.path.join(savepath,'map-translines_all-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map-translines_all failed:\n{}\n'.format(err))


#%% Transmission utilization maps
try:
    for plottype in ['mean','max']:
        plt.close()
        f,ax = rplots.plot_transmission_utilization(
            case=casedir, year=year, plottype=plottype,
            wscale=wscale_straight, alpha=1.0, cmap=cmap,
        )
        if write:
            plt.savefig(os.path.join(savepath,f'map-transmission_utilization-{plottype}-{year}.png'))
        if interactive: plt.show()
        plt.close()
except Exception as err:
    print(f'map-transmission_utilization failed:\n{err}\n')

try:
    plt.close()
    f,ax = rplots.plot_average_flow(
        case=casedir, year=year,
        wscale=wscale_straight*17500,
    )
    if write:
        plt.savefig(os.path.join(savepath,f'map-transmission_utilization-flowdirection-{year}.png'))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print(f'map-transmission_utilization-flowdirection failed:\n{err}\n')

try:
    plt.close()
    f,ax = rplots.plot_prmtrade(
        case=casedir, year=year,
        wscale=wscale_straight*17500,
    )
    if write:
        plt.savefig(os.path.join(savepath,f'map-transmission_utilization-prmtrade-{year}.png'))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print(f'map-transmission_utilization-prmtrade failed:\n{err}\n')


#%% Macrogrid map
try:
    plt.close()
    f,ax = rplots.plot_trans_vsc(
        case=casedir, year=year, wscale=wscale_straight*1e3,
        alpha=1.0, miles=300,
    )
    if write:
        plt.savefig(os.path.join(savepath,'map-translines_vsc-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map-translines_vsc failed:\n{}\n'.format(err))


#%% Generation capacity maps
try:
    ### Shared data
    rsmap = pd.read_csv(
        os.path.join(reedspath,'inputs','rsmap.csv'),
        header=0, names=['r','rs']
    )
    s2r = rsmap.set_index('rs').r

    dfba = rplots.get_zonemap(casedir)
    dfstates = dfba.dissolve('st')
    ### Case data
    dfcap = pd.read_csv(
        os.path.join(casedir,'outputs','cap.csv'),
        names=['i','r','t','MW'], header=0,
    )
    dfcap.r = dfcap.r.map(lambda x: s2r.get(x,x))
    dfcap.i = dfcap.i.str.lower().map(lambda x: techmap.get(x,x))
    ### Arrange the subplots
    nrows = len(techs) // ncols
    coords = dict(zip(
        techs,
        [(row,col) for row in range(nrows) for col in range(ncols)]
    ))
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(3*ncols,3*nrows),
        gridspec_kw={'wspace':0.0,'hspace':-0.05}, dpi=150)
    for tech in techs:
        dfval = dfcap.loc[
            (dfcap.i==tech)
            & (dfcap.t.astype(int)==year)
        ].groupby('r').MW.sum()
        dfplot = dfba.copy()
        dfplot['GW'] = (dfval / 1000).fillna(0)

        dfba.plot(
            ax=ax[coords[tech]],
            facecolor='none', edgecolor='k', lw=0.1, zorder=10000)
        dfstates.plot(
            ax=ax[coords[tech]],
            facecolor='none', edgecolor='k', lw=0.2, zorder=10001)
        dfplot.plot(
            ax=ax[coords[tech]], column='GW', cmap=cmap, legend=True, vmin=0,
            legend_kwds={
                'shrink':0.75, 'pad':0, 'orientation':'horizontal',
                'label': '{} [GW]'.format(tech),
            }
        )
        ax[coords[tech]].axis('off')
    ax[0,0].set_title(
        '{} ({})'.format(os.path.basename(casedir), year),
        x=0.1, ha='left', va='top')
    if write:
        plt.savefig(os.path.join(savepath,'map-capacity-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map-capacity failed:\n{}\n'.format(err))

#%% Site VRE capacity
try:
    plt.close()
    f,ax = rplots.plot_vresites_transmission(
        casedir, year, crs=crs, cm=gen_cmap,
        routes=False, wscale=wscale_straight, show_overlap=False,
        subtract_baseyear=None, show_transmission=False,
        alpha=transalpha, colors=transcolor, ms=ms,
    )
    if write:
        plt.savefig(os.path.join(savepath,'map-VREsites-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map-VREsites failed:\n{}\n'.format(err))


#%% Site VRE capacity overlaid with transmission
try:
    plt.close()
    f,ax = rplots.plot_vresites_transmission(
        casedir, year, crs=crs, cm=gen_cmap,
        routes=routes, show_overlap=False,
        wscale=wscale_routes,
        subtract_baseyear=None, show_transmission=True,
        alpha=transalpha, colors=transcolor, ms=ms,
    )
    if write:
        plt.savefig(os.path.join(savepath,'map-VREsites-translines-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map-VREsites-translines failed:\n{}\n'.format(err))

#%% Aggregated capacity, generation, and transmission by FERC region
try:
    for val in ['cap','gen']:
        plt.close()
        f,ax = rplots.map_agg(case=casedir, data=val, width_step=yearstep)
        if write:
            plt.savefig(os.path.join(savepath,'map_agg-FERC-{}-{}.png'.format(val,year)))
        if interactive: plt.show()
        plt.close()

    plt.close()
    f,ax = rplots.map_trans_agg(case=casedir, wscale=1000, drawzones=0.05)
    if write:
        plt.savefig(os.path.join(savepath,'map_agg-FERC-trans-{}.png'.format(year)))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    print('map_agg failed:\n{}\n'.format(err))

#%% Hybrid-specific plots
try:
    if int(sw.GSw_SpurScen):
        for (val,tech,cmap,vmax) in [
            ('site_cap','upv',plt.cm.Oranges,400),
            ('site_cap','wind-ons',plt.cm.Blues,400),
            ('site_hybridization',None,plt.cm.gist_earth_r,1),
            ('site_pv_fraction',None,plt.cm.turbo,1),
            ('site_spurcap',None,plt.cm.gist_earth_r,400),
            ('site_gir','upv',plt.cm.turbo,2),
            ('site_gir','wind-ons',plt.cm.turbo,2),
        ]:
            f,ax = rplots.map_hybrid_pv_wind(
                case=casedir,
                year=year,
                val=val, tech=tech, cmap=cmap, vmax=vmax,
                markersize=10.75,
            )
            if write:
                plt.savefig(
                    os.path.join(
                        savepath, f"map-hybrid-{val.replace('site_','')}-{tech}-{year}.png"))
            if interactive: plt.show()
except Exception as err:
    print('map-hybrids failed:\n{}\n'.format(err))
