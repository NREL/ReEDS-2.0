#%% Imports
import os
import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import geopandas as gpd
import shapely
import argparse
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
from reeds import plots

plots.plotparams()


#%% Fixed inputs
interactive = False


#%% Plotting functions
def plot_outage_scheduled(case, f=None, ax=None, color='C0', aspect=1):
    """Plot scheduled outage rate by month, one subplot for each tech"""
    sw = reeds.io.get_switches(case)

    outage_scheduled = reeds.io.get_outage_hourly(case, 'scheduled')

    techs = reeds.techs.get_techlist_after_bans(case)
    techs = [i.split('*')[0] for i in techs if i not in reeds.techs.ignore_techs]

    dfplot = outage_scheduled.loc[
        sw.GSw_HourlyWeatherYears.split('_')[0],
        [c for c in outage_scheduled if c in techs]
    ] * 100

    if (f is None) and (ax is None):
        nrows, ncols, coords = plots.get_coordinates(dfplot.columns, aspect=aspect)

        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(ncols*1.7, nrows*1.25), sharex=True, sharey=True,
            gridspec_kw={'hspace':0.5},
        )
    else:
        nrows = ax.shape[0]
        ncols = ax.shape[1]
        _, _, coords = plots.get_coordinates(dfplot.columns, nrows=nrows, ncols=ncols)

    for tech in dfplot:
        ax[coords[tech]].plot(dfplot.index, dfplot[tech], color=color)
        ax[coords[tech]].set_title(
            tech, y=1,
            path_effects=[pe.withStroke(linewidth=2.0, foreground='w', alpha=0.8)]
        )

    ax[-1,0].set_ylabel('Scheduled outage rate [%]', va='bottom', ha='left', y=0)
    ax[-1,0].yaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
    ax[-1,0].yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax[-1,0].xaxis.set_major_locator(mpl.dates.MonthLocator(bymonth=[1,4,7,10]))
    ax[-1,0].xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
    ax[-1,0].xaxis.set_minor_locator(mpl.dates.MonthLocator())
    ax[-1,0].set_xlim(dfplot.index[0]-pd.Timedelta('1D'), dfplot.index[-1])
    ax[-1,0].set_ylim(0)
    plots.despine(ax)
    plots.trim_subplots(ax, nrows, ncols, dfplot.shape[1])

    return f, ax, dfplot


def plot_profile(
    case,
    datum='demand',
    year=0,
    region=None,
    weatheryears=None,
    color='k',
    hourly=False,
    f=None,
    ax=None,
    figsize=(6,4),
    yscale_zero=True,
):
    """
    Plot daily electricity demand over all weather years.
    Dark line shows daily mean; filled area shows range from daily min to daily max.
    If `hourly == True`, also show the hourly demand (need to increase the figure width
    using the `figsize` parameter and set `weatheryears` to a single year to be able to
    discern the hourly values).
    """
    ## Parse inputs
    sw = reeds.io.get_switches(case)
    t = reeds.io.get_years(case)[-1] if year in [0, None, 'last'] else year
    rs = reeds.inputs.parse_regions((region if region else case), case)
    if weatheryears is None:
        weatheryears = sw.resource_adequacy_years_list
    elif isinstance(weatheryears, int):
        weatheryears = [weatheryears]

    ## Data
    if datum in ['demand', 'load']:
        ylabel = 'Electricity demand [GW]'
        dfprofile = reeds.io.read_file(
            os.path.join(case, 'inputs_case', 'load.h5'),
            parse_timestamps=True,
        ## Convert to GW
        ) / 1e3
        dfprofile = (
            dfprofile
            .loc[t, [r for r in dfprofile if r in rs]]
            .sum(axis=1)
        )
    elif datum in ['temperature']:
        ylabel = 'Temperature [°C]'
        ...
    else:
        recf = reeds.io.get_available_capacity_weighted_cf(case, level='country') * 100
        if datum in ['wind', 'wind-ons']:
            ylabel = 'Wind CF [%]'
            dfprofile = recf['wind-ons'].squeeze(1)
        elif datum in ['upv', 'pv', 'solar']:
            ylabel = 'PV CF [%]'
            dfprofile = recf['upv'].squeeze(1)

    dfprofile = dfprofile.loc[str(min(weatheryears)):str(max(weatheryears))].copy()

    dayindex = pd.concat([
        pd.Series(index=pd.date_range(f'{y}-01-01', f'{y}-12-31', freq='D')[:365])
        for y in weatheryears
    ]).index
    dfday = {
        agg: dfprofile.groupby(
            [dfprofile.index.year, dfprofile.index.month, dfprofile.index.day]
        ).agg(agg).set_axis(dayindex)
        for agg in ['min', 'max', 'mean']
    }

    ## Plot it
    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=figsize)
    dfday['mean'].plot(ax=ax, lw=0.5, color=color)
    if hourly:
        dfprofile.plot(ax=ax, lw=0.1, color=color)
    ax.fill_between(
        dfday['mean'].index, dfday['max'], dfday['min'],
        lw=0, alpha=0.25, color=color,
    )
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax.set_ylabel(ylabel)
    ax.set_xlabel(None)
    if yscale_zero:
        ax.set_ylim(0)
    if len(weatheryears) > 1:
        ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(4))
        ax.set_xlim(str(weatheryears[0]), str(weatheryears[-1]+1))
    reeds.plots.despine(ax)

    return f, ax, dfday


def plot_units_existing(
    case=None,
    year=None,
    markers=None,
    scale=0.2,
    alpha=0.8,
    f=None,
    ax=None,
    figsize=(12,9),
    drawstates=0.75,
    drawzones=0.,
    onlytechs=None,
    gw_label=True,
    scalemw=[200, 500, 1000],
):
    """
    Scatter map of existing units, with marker size proportional to unit capacity.
    If case == None, use EIA-NEMS database from inputs/ folder.
    """
    ### Data cleaning (20250508: Offshore PV units)
    bad_locations = ['Hendry Isles', 'Georges Lake', 'Laurel Oaks Solar', 'Norton Creek']
    ### Get data
    if case is None:
        fpath = os.path.join(
            reeds.io.reeds_path, 'inputs', 'capacity_exogenous',
            'ReEDS_generator_database_final_EIA-NEMS.csv',
        )
    else:
        fpath = os.path.join(case, 'inputs_case', 'unitdata.csv')

    dfunits = pd.read_csv(fpath)
    dfunits = reeds.plots.df2gdf(
        dfunits.assign(T_LONG=-dfunits.T_LONG.abs()), lat='T_LAT', lon='T_LONG',
    )
    dfunits.tech = reeds.reedsplots.simplify_techs(dfunits.tech)
    rename = {
        **{'dupv':'upv'},
        **{f'battery_{i}':'battery' for i in range(101)},
    }
    dfunits.tech = dfunits.tech.map(lambda x: rename.get(x,x))
    ## Downselect to specified year
    if year is None:
        if case is None:
            year = int(
                pd.read_csv(
                    os.path.join(reeds.io.reeds_path, 'cases.csv'),
                    index_col=0,
                )['Default Value'].GSw_StartMarkets
            )
        else:
            year = int(reeds.io.get_switches(case).GSw_StartMarkets)
    dfunits = dfunits.loc[
        (dfunits.StartYear <= year)
        & (dfunits.RetireYear > year)
        & ~dfunits.T_PNM.isin(bad_locations)
    ].copy()
    ## Sort techs by installed capacity
    techs = dfunits.groupby('tech').cap.sum().sort_values(ascending=False).index
    if onlytechs:
        if isinstance(onlytechs, str):
            techs = [onlytechs]
        elif isinstance(onlytechs, list):
            techs = [i for i in techs if i in onlytechs]

    ### Parse inputs
    if markers is None:
        techmarkers = reeds.reedsplots.techmarkers
    elif isinstance(markers, str):
        techmarkers = dict(zip(techs, markers(len(techs))))
    elif isinstance(markers, dict):
        techmarkers = markers
    else:
        raise ValueError(f'Invalid markers ({type(markers)}): {markers}')

    colors = pd.read_csv(
        os.path.join(
            reeds.io.reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order',
    ).squeeze(1)
    colors.index = colors.index.str.lower()

    dfmap = reeds.io.get_dfmap(case)

    ## Create scale
    dfscale = pd.DataFrame({'cap': scalemw}).sort_values('cap')
    dfscale['x'] = -0.8e6
    dfscale['y'] = -1.4e6 - np.arange(0, 0.1e6*len(dfscale), 0.1e6)
    dfscale['geometry'] = dfscale.apply(lambda row: shapely.geometry.Point(row.x, row.y), axis=1)
    dfscale = gpd.GeoDataFrame(dfscale)

    ### Plot it
    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=figsize)
    ## Region outlines
    if drawzones:
        dfmap['r'].plot(ax=ax, facecolor='none', edgecolor='k', lw=drawzones, zorder=1e6)
    if drawstates:
        dfmap['st'].plot(ax=ax, facecolor='none', edgecolor='k', lw=drawstates, zorder=1e7)
    ## Units
    for tech in techs:
        df = dfunits.loc[dfunits.tech==tech]
        label = f'{tech} ({df.cap.sum()/1e3:.0f})' if gw_label else tech
        df.plot(
            ax=ax, color=colors.get(tech,'k'), marker=techmarkers.get(tech,'o'),
            markersize=df.cap*scale, lw=0, label=label, alpha=alpha,
        )
    ## Legend
    leg = ax.legend(
        loc='lower left', bbox_to_anchor=(0.04,0.04), ncol=2, frameon=False,
        handletextpad=0.3, handlelength=0.7, columnspacing=0.6, labelspacing=0.3,
        title=('Tech (GW)' if gw_label else 'Tech'),
        alignment='left', title_fontproperties={'weight':'bold', 'size':12},
    )
    for handle in leg.legend_handles:
        handle.set_sizes([50])
        handle.set_alpha(1)
    ## Scale
    if len(scalemw):
        dfscale.plot(ax=ax, color='k', marker='o', markersize=dfscale.cap*scale, lw=0)
        for i, row in dfscale.iterrows():
            ax.annotate(
                f'{row.cap/1e3:.1f}'+(' GW' if i == len(dfscale) - 1 else ''),
                (row.x+1e5, row.y), va='center')
    ## Formatting
    ax.axis('off')
    return f, ax, dfunits


def plot_regional_cost_difference(
    case=None,
    nicelabels={
        'CONSUME': 'Electrolyzer, DAC, steam methane reforming',
        'OGS': 'Oil-gas-steam',
        'LFILL': 'Landfill gas',
        'CSP': 'CSP',
        'PVB': '(including in PV/battery hybrid)',
    },
    cmap=plt.cm.RdBu_r,
    scale=4,
):
    ### Get data
    if case is None:
        fpath = os.path.join(
            reeds.io.reeds_path, 'inputs', 'financials', 'reg_cap_cost_diff_default.csv',
        )
    else:
        fpath = os.path.join(case, 'inputs_case', 'regional_cap_cost_diff.csv')
    ## Convert to percent
    dfin = pd.read_csv(fpath, index_col='r') * 100
    ### Get shapefiles
    dfmap = reeds.io.get_dfmap(case)
    dfcounty = gpd.read_file(
        os.path.join(reeds.io.reeds_path, 'inputs', 'shapefiles', 'US_county_2022')
    ).set_index('rb')
    dfcounty.geometry = dfcounty.intersection(dfmap['country'].geometry.squeeze()).simplify(1000)
    dfplot = dfcounty.merge(dfin, left_index=True, right_index=True)
    ### Set up plot
    vlim = max(abs(dfin.min().min()), dfin.max().max())
    nrows, ncols, coords = reeds.plots.get_coordinates(dfin.columns, ncols=3)
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(ncols*scale, nrows*scale*0.8),
        sharex=True, sharey=True, gridspec_kw={'wspace':0},
    )
    for column in dfin:
        _ax = ax[coords[column]]
        ## Data
        dfplot.plot(
            ax=_ax, column=column, vmin=-vlim, vmax=vlim, cmap=cmap,
        )
        ## States
        dfmap['st'].plot(ax=_ax, facecolor='none', edgecolor='k', lw=0.3)
        ## Formatting
        _ax.axis('off')
        _ax.set_title(
            '\n'.join([nicelabels.get(i, i.title()).replace('_',' ') for i in column.split('|')]),
            y=0.92,
        )
    ## Colorbar
    reeds.plots.addcolorbarhist(
        f=f, ax0=ax[0,1], data=dfplot[column].values,
        histcolor='w', histratio=0.01, vmin=-vlim, vmax=vlim,
        orientation='horizontal', cbarwidth=0.05, cbarheight=0.9, cbarhoffset=10,
        cbarbottom=-0.075, labelpad=2,
        title='Cost difference [%]',
        cmap=cmap,
    )
    return f, ax, dfplot


#%%### Procedure
if __name__ == '__main__':
    #%% Argument inputs
    parser = argparse.ArgumentParser(
        description='Check inputs.gdx parameters against objective_function_params.yaml',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('case', help='ReEDS-2.0/runs/{case} directory')
    parser.add_argument(
        '--write', '-w', choices=['png', 'ppt', 'pptx'], default='png',
        help='Output format (png or pptx)')
    args = parser.parse_args()
    case = args.case
    write = args.write

    # #%% Inputs for testing
    # reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
    # case = os.path.expanduser('~/github3/ReEDS-2.0/runs/v20250408_tforM0_USA')
    # interactive = True
    # write = 'png'

    #%% Create output container
    if write.strip('.') == 'png':
        savepath = os.path.join(case, 'outputs', 'maps', 'inputs')
        os.makedirs(savepath, exist_ok=True)

        def saveit(savename):
            outpath = os.path.join(savepath, savename.lower().replace(' ', '-') + '.png')
            plt.savefig(outpath)
            print(os.path.basename(outpath))
            if interactive:
                plt.show()

    elif write.strip('.') in ['ppt', 'pptx']:
        savepath = os.path.join(case, 'outputs', 'maps', 'inputs.pptx')
        prs = reeds.results.init_pptx()
        def saveit(savename, **kwargs):
            reeds.results.add_to_pptx(savename, prs=prs, **kwargs)
            if interactive:
                plt.show()


    #%% Plots
    sw = reeds.io.get_switches(case)

    ### Scheduled outage rates
    try:
        f, ax, df = plot_outage_scheduled(case)
        saveit('outage_scheduled')
    except Exception:
        print(traceback.format_exc())

    ### Demand, PV, and wind profiles
    colors = {'demand':'k', 'pv':'C1', 'wind':'C0'}
    for datum in colors:
        try:
            f, ax, df = plot_profile(case, datum=datum, color=colors[datum])
            saveit(f"{datum}{'_lastyear' if datum in ['demand','load'] else ''}_ra")
        except Exception:
            print(traceback.format_exc())

        try:
            f, ax, df = plot_profile(
                case,
                datum=datum,
                color=colors[datum],
                hourly=True,
                weatheryears=[int(y) for y in sw.GSw_HourlyWeatherYears.split('_')],
                figsize=(13.33, 4),
            )
            saveit(f"{datum}{'_lastyear' if datum in ['demand','load'] else ''}_rep")
        except Exception:
            print(traceback.format_exc())

    try:
        plt.close()
        f,ax = plt.subplots(len(colors), 1, figsize=(5, 3.75), sharex=True)
        for row, (datum, color) in enumerate(colors.items()):
            plot_profile(case, datum=datum, color=color, ax=ax[row], yscale_zero=False)
        ## Formatting
        ax[0].set_ylabel('Demand\n[GW]', color=colors['demand'])
        ax[1].set_ylabel('PV CF\n[%]', color=colors['pv'])
        ax[2].set_ylabel('Wind CF\n[%]', color=colors['wind'])
        cfmax = max(ax[1].get_ylim()[1], ax[2].get_ylim()[1])
        for row in [1, 2]:
            ax[row].set_ylim(0, cfmax)
        saveit(f"{','.join(colors.keys())}_ra")
    except Exception:
        print(traceback.format_exc())

    ### Existing units
    try:
        f, ax, df = plot_units_existing(case=case)
        saveit('Existing capacity')
    except Exception:
        print(traceback.format_exc())

    ### Regional cost differences
    try:
        f, ax, df = plot_regional_cost_difference(case=case)
        saveit('Regional cost differences')
    except Exception:
        print(traceback.format_exc())

    #%% Save the powerpoint file if necessary
    if write.strip('.') in ['ppt', 'pptx']:
        print(f'\ninput_plots.py results saved to:\n{savepath}')
        prs.save(savepath)
