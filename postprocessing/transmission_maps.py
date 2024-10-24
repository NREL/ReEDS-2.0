#%% IMPORTS
import pandas as pd
import matplotlib.pyplot as plt
import os
import site
import argparse
import traceback
import cmocean
import plots
import reedsplots as rplots 

os.environ['PROJ_NETWORK'] = 'OFF'

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
site.addsitedir(os.path.join(reeds_path,'postprocessing'))
site.addsitedir(os.path.join(reeds_path,'input_processing'))

# import makelog after setting the module path; if it's done before, the ticker module won't be found
from ticker import makelog  # noqa: E402

plots.plotparams()

##########
#%% INPUTS
## Note that if your case builds lots of transmission, wscale might
## need to be reduced to avoid too much overlap in the plotted routes
wscale_straight = 0.0004
wscale_routes = 1.5
wscale_h2 = 10
routes = False
## Note that if you change the CRS you'll probably need to change
## the position of the annotations
crs = 'ESRI:102008'
### For generation capacity map
cmap = cmocean.cm.rain
ncols = 4
techs = [
    'Utility PV', 'Land-based wind', 'Offshore wind', 'Electrolyzer',
    'Battery (4h)', 'Battery (8h)', 'PSH', 'H2 turbine',
    'Nuclear', 'Gas CCS', 'Coal CCS', 'Fossil',
]
techmap = {
    **{f'upv_{i}':'Utility PV' for i in range(20)},
    **{f'dupv_{i}':'Utility PV' for i in range(20)},
    **{f'wind-ons_{i}':'Land-based wind' for i in range(20)},
    **{f'wind-ofs_{i}':'Offshore wind' for i in range(20)},
    **dict(zip(['nuclear','nuclear-smr'], ['Nuclear']*20)),
    **dict(zip(
        ['gas-cc_re-cc','gas-ct_re-ct','re-cc','re-ct',
         'gas-cc_h2-ct','gas-ct_h2-ct','h2-cc','h2-ct',],
        ['H2 turbine']*20)),
    **{'electrolyzer':'Electrolyzer'},
    **{'battery_4':'Battery (4h)', 'battery_8':'Battery (8h)', 'pumped-hydro':'PSH'},
    **dict(zip(
        ['coal-igcc', 'coaloldscr', 'coalolduns', 'gas-cc', 'gas-ct', 'coal-new', 'o-g-s',],
        ['Fossil']*20)),
    **dict(zip(
        ['coal-igcc_coal-ccs_mod','coal-new_coal-ccs_mod',
         'coaloldscr_coal-ccs_mod','coalolduns_coal-ccs_mod','cofirenew_coal-ccs_mod',
         'cofireold_coal-ccs_mod','coal-igcc_coal-ccs_max',
         'coal-new_coal-ccs_max','coaloldscr_coal-ccs_max','coalolduns_coal-ccs_max',
         'cofirenew_coal-ccs_max','cofireold_coal-ccs_max',],
        ['Coal CCS']*50)),
    **dict(zip(
        ['gas-cc_gas-cc-ccs_mod','gas-cc_gas-cc-ccs_max',
         'gas-cc-ccs_mod','gas-cc-ccs_max',],
        ['Gas CCS']*50)),
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
parser = argparse.ArgumentParser(description='transmission maps')
parser.add_argument('--case', '-c', type=str,
                    help='path to ReEDS run folder')
parser.add_argument('--year', '-y', type=int, default=2050,
                    help='year to plot')
parser.add_argument('--routes', '-r', action='store_true',
                    help='if True, show actual transmission routes')

args = parser.parse_args()
case = args.case
year = args.year
routes = args.routes

# #%% Inputs for testing
# case = (
#     '/Volumes/ReEDS/Users/pbrown/ReEDSruns/20240112_stresspaper/20240313/'
#     'v20240313_stresspaperE0_SP_DemHi_90by2035__core')
# case = os.path.join(reeds_path,'runs','v20240806_tforK0_Ref_TFOR')
# year = 2050
# routes = False
# interactive = True
# write = False
# import importlib
# importlib.reload(rplots)

#############
#%% PROCEDURE
#%% Set up logger
log = makelog(scriptname=__file__, logpath=os.path.join(case,'gamslog.txt'))

#%% Make output directory
savepath = os.path.join(case,'outputs','maps')
os.makedirs(savepath, exist_ok=True)

#%% Load colors
trtypes = pd.read_csv(
    os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
    index_col='raw')['display']
colors = pd.read_csv(
    os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
    index_col='order')['color']
colors = pd.concat([colors, trtypes.map(colors)])

#%% Load switches
sw = pd.read_csv(
    os.path.join(case, 'inputs_case', 'switches.csv'),
    header=None, index_col=0).squeeze(1)
years = pd.read_csv(
    os.path.join(case,'inputs_case','modeledyears.csv')
).columns.astype(int).values
yearstep = years[-1] - years[-2]
val_r = pd.read_csv(
    os.path.join(case, 'inputs_case', 'val_r.csv'), header=None).squeeze(1).tolist()

#%% Transmission line map with disaggregated transmission types
### Plot both total capacity (subtract_baseyear=None) and new (subtract_baseyear=2020)
for subtract_baseyear in [None, 2020]:
    try:
        plt.close()
        f, ax, _ = rplots.plot_trans_onecase(
            case=case, pcalabel=False,
            routes=routes, simpletypes=None,
            wscale=(wscale_routes if routes else wscale_straight),
            yearlabel=False, year=year, alpha=1.0,
            subtract_baseyear=subtract_baseyear,
            label_line_capacity=1,
        )
        ### Add legend
        ax.annotate(
            'AC', (-1.75e6, -1.12e6), ha='center', va='top',
            weight='bold', fontsize=15, color=colors['ac'])
        ax.annotate(
            'LCC DC',
            (-1.75e6, -1.24e6), ha='center', va='top',
            weight='bold', fontsize=15, color=colors['lcc'])
        ax.annotate(
            'B2B',
            (-1.75e6, -1.36e6), ha='center', va='top',
            weight='bold', fontsize=15, color=colors['b2b'])
        ax.annotate(
            'VSC DC', (-1.75e6, -1.48e6), ha='center', va='top',
            weight='bold', fontsize=15, color=colors['vsc'])
        end = f'-since{subtract_baseyear}' if subtract_baseyear else ''
        savename = f'map_translines_all-{year}{end}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('map_translines_all failed:')
        print(traceback.format_exc())


#%% Transmission utilization maps
try:
    for network in ['rep','stress']:
        for plottype in ['mean','max']:
            plt.close()
            f, ax, df = rplots.plot_transmission_utilization(
                case=case, year=year, plottype=plottype, network=network,
                wscale=wscale_straight, alpha=1.0, cmap=cmap,
            )
            savename = f'map_transmission_utilization-{network}-{plottype}-{year}'
            if write:
                plt.savefig(os.path.join(savepath, savename))
            if interactive:
                plt.show()
            plt.close()
            print(savename)
except Exception:
    print('map_transmission_utilization failed:')
    print(traceback.format_exc())

try:
    plt.close()
    f,ax = rplots.plot_average_flow(
        case=case, year=year, wscale=wscale_routes*8e3,
    )
    savename = f'map_transmission_utilization-flowdirection-{year}.png'
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)
except Exception:
    print('map_transmission_utilization-flowdirection failed:')
    print(traceback.format_exc())

try:
    plt.close()
    f,ax = rplots.plot_prmtrade(
        case=case, year=year, wscale=wscale_straight*8e3,
    )
    savename = f'map_transmission_utilization-prmtrade-{year}.png'
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)
except Exception:
    print('map_transmission_utilization-prmtrade failed:')
    print(traceback.format_exc())

try:
    for level in ['r','st']:
        plt.close()
        f,ax = rplots.map_net_imports(case=case, level=level)
        savename = f'map_net_imports-{level}'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
except Exception:
    print('map_net_imports failed:')
    print(traceback.format_exc())

try:
    level = 'nercr'
    plt.close()
    f, ax, df = rplots.plot_max_imports(case=case, level=level)
    savename = f"plot_max_imports-{level}"
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)
except Exception:
    print('plot_max_imports failed:')
    print(traceback.format_exc())


#%% Macrogrid map
try:
    if int(sw.GSw_VSC):
        plt.close()
        f,ax = rplots.plot_trans_vsc(
            case=case, year=year, wscale=wscale_straight*1e3,
            alpha=1.0, miles=300,
        )
        savename = f'map_translines_vsc-{year}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
except Exception:
    print('map_translines_vsc failed:')
    print(traceback.format_exc())


#%% Generation capacity maps
### Plot with tech-specific (vmax='each') and uniform (vmax='shared') color axis
for vmax in ['each', 'shared']:
    try:
        dfmap = rplots.get_dfmap(case)
        dfba = dfmap['r']
        dfstates = dfmap['st']
        ### Case data
        dfcap = pd.read_csv(
            os.path.join(case,'outputs','cap.csv'),
            names=['i','r','t','MW'], header=0,
        )
        dfcap.i = dfcap.i.str.lower().map(lambda x: techmap.get(x,x))
        ### Get the vmax
        if vmax == 'shared':
            _vmax = dfcap.loc[
                dfcap.i.isin(techs) & (dfcap.t.astype(int)==year)
            ].groupby(['i','r']).MW.sum().max() / 1e3
        else:
            _vmax = None
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
            ].groupby('r').MW.sum().round(3)
            dfplot = dfba.copy()
            dfplot['GW'] = (dfval / 1000).fillna(0)

            dfba.plot(
                ax=ax[coords[tech]],
                facecolor='none', edgecolor='k', lw=0.1, zorder=10000)
            dfstates.plot(
                ax=ax[coords[tech]],
                facecolor='none', edgecolor='k', lw=0.2, zorder=10001)
            dfplot.plot(
                ax=ax[coords[tech]], column='GW', cmap=cmap, legend=True,
                vmin=0, vmax=_vmax,
                legend_kwds={
                    'shrink':0.75, 'pad':0, 'orientation':'horizontal',
                    'label': '{} [GW]'.format(tech),
                }
            )
            ax[coords[tech]].axis('off')
        ax[0,0].set_title(
            '{} ({})'.format(os.path.basename(case), year),
            x=0.1, ha='left', va='top')
        savename = f'map_capacity-{year}-{vmax}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('map_capacity failed:')
        print(traceback.format_exc())

#%% Site VRE capacity
try:
    plt.close()
    f,ax = rplots.plot_vresites_transmission(
        case, year, crs=crs, cm=gen_cmap,
        routes=False, wscale=wscale_straight, show_overlap=False,
        subtract_baseyear=None, show_transmission=False,
        alpha=transalpha, colors=transcolor, ms=ms,
    )
    savename = f'map_VREsites-{year}.png'
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)
except Exception:
    print('map_VREsites failed:')
    print(traceback.format_exc())


#%% Site VRE capacity overlaid with transmission
try:
    plt.close()
    f,ax = rplots.plot_vresites_transmission(
        case, year, crs=crs, cm=gen_cmap,
        routes=routes, show_overlap=False,
        wscale=wscale_routes,
        subtract_baseyear=None, show_transmission=True,
        alpha=transalpha, colors=transcolor, ms=ms,
    )
    savename = f'map_VREsites-translines-{year}.png'
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)
except Exception:
    print('map_VREsites-translines failed:')
    print(traceback.format_exc())

#%% Aggregated capacity, generation, and transmission by FERC region
try:
    for val in ['cap','gen']:
        plt.close()
        f,ax = rplots.map_agg(case=case, data=val, width_step=yearstep)
        savename = f'map_agg-FERC-{val}-{year}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)

    plt.close()
    f,ax = rplots.map_trans_agg(case=case, wscale=1000, drawzones=0.05, width_step=yearstep)
    savename = f'map_agg-FERC-trans-{year}.png'
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)

    plt.close()
    f,ax = rplots.map_agg(case=case, data='cap', width_step=yearstep, transmission=True)
    savename = f'map_agg-FERC-cap,trans-{year}.png'
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)
except Exception:
    print('map_agg failed:')
    print(traceback.format_exc())

#%% Dispatch plots
### Specify techs to include (None = all techs)
tech_subset_table = pd.read_csv(
    os.path.join(reeds_path,'inputs', 'tech-subset-table.csv'), index_col=0)
subtechs = {
    '': None,
    'storage': tech_subset_table.loc[tech_subset_table['STORAGE_STANDALONE']=='YES'].index.tolist()
}
### Specify BAs to plot (None = aggregate all together)
bas = [None]
if int(sw['plot_ba_level']):
    bas += pd.read_csv(
        os.path.join(case, 'inputs_case', 'val_r.csv'), header=None,
    ).squeeze(1).tolist()
    savepath_ba = os.path.join(savepath, 'ba')
    os.makedirs(savepath_ba, exist_ok=True)
else:
    figpath = savepath

### Plot dispatch and state of charge
for label, plottechs in subtechs.items():
    plottypes = ['dispatch', 'soc'] if label == 'storage' else ['dispatch']
    try:
        for ba in bas:
            figpath = savepath_ba if ba else savepath
            for plottype in plottypes:
                for v in ([1] if ba else [0, 1]):
                    plt.close()
                    f, ax, df = rplots.plot_dispatch_yearbymonth(
                        case=case, t=year, plottype=plottype, ba=ba,
                        techs=plottechs, highlight_rep_periods=v,
                    )
                    savename = (
                        f"plot_{plottype}{'_'+label if len(label) else ''}-yearbymonth"
                        + f"{'-'+ba if ba else ''}-{v}-{year}.png")
                    if write and (df is not None):
                        plt.savefig(os.path.join(figpath, savename))
                        print(savename)
                    if interactive and (df is not None):
                        plt.show()
                    plt.close()
    except Exception:
        print('plot_dispatch-yearbymonth failed:')
        print(traceback.format_exc())

try:
    plt.close()
    f,ax = rplots.plot_dispatch_weightwidth(case=case)
    savename = f'plot_dispatch-weightwidth-{sw.endyear}.png'
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)
except Exception:
    print('plot_dispatch-weightwidth failed:')
    print(traceback.format_exc())


#%% All-in-one map
try:
    for sideplots in [False, True]:
        plt.close()
        f,ax,eax = rplots.map_zone_capacity(case=case, year=year, sideplots=sideplots)
        savename = f'map_gencap_transcap-{year}{"-sideplots" if sideplots else ""}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
except Exception:
    print('map_gencap_transcap failed:')
    print(traceback.format_exc())


#%% Interregional transmission / peak demand
try:
    for level in ['transreg']:
        f, ax, dfplot = rplots.plot_interreg_transfer_cap_ratio(case=case, level=level)
        savename = f'plot_interreg_transfer_ratio-{level}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
except Exception:
    print('plot_interreg_transfer_ratio failed:')
    print(traceback.format_exc())


#%% Differences betweens solve years
try:
    plt.close()
    f,ax = rplots.plot_retire_add(case=case)
    savename = 'bars_retirements_additions.png'
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)
except Exception:
    print('bars_retirements_additions failed:')
    print(traceback.format_exc())


#%% H2 pipelines and storage
try:
    if int(sw.GSw_H2):
        plt.close()
        f,ax = rplots.map_h2_capacity(
            case=case, year=year, cmap=cmap, wscale_h2=wscale_h2)
        savename = f'map_h2_capacity-{sw.endyear}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
except Exception:
    print('map_h2_capacity failed:')
    print(traceback.format_exc())


#%% H2 pipeline utilization
try:
    if int(sw['GSw_H2_Transport']):
        for plottype in ['mean','max']:
            plt.close()
            f,ax = rplots.plot_transmission_utilization(
                case=case, year=year, plottype=plottype, network='h2',
                wscale=wscale_h2/1000, alpha=1.0, cmap=cmap, extent='modeled',
            )
            savename = f'map_pipeline_utilization-{plottype}-{year}.png'
            if write:
                plt.savefig(os.path.join(savepath, savename))
            if interactive:
                plt.show()
            plt.close()
            print(savename)
except Exception:
    print('map_pipeline_utilization failed:')
    print(traceback.format_exc())

try:
    if int(sw['GSw_H2_Transport']):
        plt.close()
        f,ax = rplots.plot_average_flow(
            case=case, year=year, network='h2',
            cm=plt.cm.magma_r, extent='modeled', wscale=wscale_h2*1e4,
        )
        savename = f'map_pipeline_utilization-flowdirection-{year}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
except Exception:
    print('map_pipeline_utilization-flowdirection failed:')
    print(traceback.format_exc())


#%% H2 storage level, production, and usage
## Can set grid=0.25 to visually line up subplots
try:
    if int(sw['GSw_H2']):
        agglevel = ('r' if len(val_r) <= 20 else ('st' if len(val_r) <= 30 else 'transreg'))
        plt.close()
        f, ax, df = rplots.plot_h2_timeseries(
            case=case, year=year, agglevel=agglevel, grid=0)
        savename = f'plot_h2_timeseries-{year}.png'
        if write and not df.empty:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
except Exception:
    print('plot_h2_timeseries failed:')
    print(traceback.format_exc())


#%% Stress periods
if (not int(sw.GSw_PRM_CapCredit)) or (int(sw.pras == 2)):
    try:
        plt.close()
        f,ax = rplots.plot_seed_stressperiods(case=case)
        savename = 'map_stressperiod_seeds.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('map_stressperiod_seeds failed:')
        print(traceback.format_exc())

    try:
        plt.close()
        level, regions = 'country', ['USA']
        f,ax = rplots.plot_stressperiod_dispatch(case=case, level=level, regions=regions)
        savename = f'plot_stressperiod_dispatch-{",".join(regions)}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('plot_stressperiod_dispatch failed:')
        print(traceback.format_exc())

    try:
        plt.close()
        f,ax = rplots.plot_stressperiod_days(case=case, repcolor='none', sharey=True)
        savename = 'plot_stressperiod_dates.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('plot_stressperiod_days failed:')
        print(traceback.format_exc())

    try:
        metric = 'sum'
        level = 'transgrp'
        plt.close()
        f,ax = rplots.plot_stressperiod_evolution(
            case=case, level=level, metric=metric)
        savename = f'plot_stressperiod_evolution-{metric}-{level}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('plot_stressperiod_evolution failed:')
        print(traceback.format_exc())

    try:
        plt.close()
        levels = ['country','interconnect','transreg','transgrp']
        f, ax, _ = rplots.plot_neue_bylevel(case=case, levels=levels)
        savename = f"plot_stressperiod_neue-{','.join(levels)}.png"
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('plot_stressperiod_neue failed:')
        print(traceback.format_exc())

    try:
        levels = ['r','transreg']
        periods = ['max gen','max load','min solar','min wind','min vre']
        for level, period in [(level,p) for level in levels for p in periods]:
            plt.close()
            f, ax, _ = rplots.map_period_dispatch(
                case=case, year=year, level=level, period=period, transmission=False,
                )
            savename = f"map_dispatch_stressperiod-{level}-{year}-{period.replace(' ','')}.png"
            if write:
                plt.savefig(os.path.join(savepath, savename))
            if interactive:
                plt.show()
            plt.close()
            print(savename)
    except Exception:
        print('map_period_dispatch failed:')

    try:
        plt.close()
        f, ax, _ = rplots.plot_interface_flows(case=case, year=year)
        savename = f'plot_PRAS_flows-{year}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('plot_interface_flows failed:')
        print(traceback.format_exc())

    try:
        plt.close()
        f, ax, _ = rplots.plot_storage_soc(case=case, year=year)
        savename = f'plot_PRAS_storage-{year}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('plot_PRAS_storage failed:')
        print(traceback.format_exc())

    try:
        level = 'transgrp'
        iteration = 'last'
        plt.close()
        f, ax, df, i = rplots.plot_pras_eue_timeseries_full(
            case=case, year=year, level=level, iteration=iteration)
        savename = f'plot_PRAS_EUE-{level}-{year}i{i}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('plot_pras_eue_timeseries_full failed:')
        print(traceback.format_exc())

    try:
        for y in [y for y in years if y >= 2025]:
            plt.close()
            # f, ax, neue, _iteration = rplots.map_neue(case=case, year=y, iteration=0)
            f, ax, neue, _iteration = rplots.map_neue(case=case, year=y)
            savename = f"map_PRAS_neue-{y}i{_iteration}.png"
            if write:
                plt.savefig(os.path.join(savepath, savename))
            if interactive:
                plt.show()
            plt.close()
            print(savename)
    except Exception:
        print('map_neue failed:')
        print(traceback.format_exc())

    try:
        level = 'transreg'
        for units in ['percent', 'GW']:
            plt.close()
            f, ax, df = rplots.plot_cap_rep_stress_mix(
                case=case, year=year, level=level, units=units)
            savename = f'plot_cap_rep_stress_mix-{units}-{level}-{year}.png'
            if write:
                plt.savefig(os.path.join(savepath, savename))
            if interactive:
                plt.show()
            plt.close()
            print(savename)
    except Exception:
        print('plot_cap_rep_stress_mix failed:')
        print(traceback.format_exc())

    try:
        level = 'transgrp'
        plot_for = False
        plottype = ('forced_outage_rate' if plot_for else 'capacity_offline')
        plt.close()
        f, ax, df = rplots.plot_capacity_offline(
            case=case, year=year, level=level, plot_for=plot_for)
        savename = f'plot_{plottype}-{level}-{year}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    except Exception:
        print('plot_capacity_offline failed:')
        print(traceback.format_exc())


#%% Capacity markers
try:
    ### Just capacity
    ms = {'r':5, 'st':7}
    for level in ['r','st']:
        plt.close()
        f,ax = rplots.map_capacity_markers(
            case=case, level=level, year=year, ms=ms[level])
        savename = f'map_units-gencap-{level}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    ### Just transmission
    for subtract_baseyear in [None, 2020]:
        end = f'-since{subtract_baseyear}' if subtract_baseyear else ''
        plt.close()
        f,ax = rplots.map_transmission_lines(
            case=case, level='r', year=year, subtract_baseyear=subtract_baseyear)
        savename = f'map_units-transcap{end}.png'
        if write:
            plt.savefig(os.path.join(savepath, savename))
        if interactive:
            plt.show()
        plt.close()
        print(savename)
    ### Both
    plt.close()
    f,ax = rplots.map_transmission_lines(
        case=case, level='r', year=year, alpha=0.5, lw=0.15)
    rplots.map_capacity_markers(case=case, level='r', year=year, f=f, ax=ax)
    savename = 'map_units-gencap-transcap.png'
    if write:
        plt.savefig(os.path.join(savepath, savename))
    if interactive:
        plt.show()
    plt.close()
    print(savename)
except Exception:
    print('map_capacity_markers failed:')
    print(traceback.format_exc())


#%% Hybrid-specific plots
try:
    if int(sw.GSw_SpurScen):
        for (val,tech,cmap,vmax) in [
            ('site_cap','upv',plt.cm.Oranges,400),
            ('site_cap','wind-ons',plt.cm.Blues,400),
            ('site_hybridization',None,cmap,1),
            ('site_pv_fraction',None,plt.cm.turbo,1),
            ('site_spurcap',None,cmap,400),
            ('site_gir','upv',plt.cm.turbo,2),
            ('site_gir','wind-ons',plt.cm.turbo,2),
        ]:
            f,ax = rplots.map_hybrid_pv_wind(
                case=case,
                year=year,
                val=val, tech=tech, cmap=cmap, vmax=vmax,
                markersize=10.75,
            )
            savename = f"map_hybrid-{val.replace('site_','')}-{tech}-{year}.png"
            if write:
                plt.savefig(os.path.join(savepath, savename))
            if interactive:
                plt.show()
            print(savename)
except Exception:
    print('map_hybrids failed:')
    print(traceback.format_exc())
