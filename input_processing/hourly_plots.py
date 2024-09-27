#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================
import os
import site
import logging
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import geopandas as gpd
import cmocean

import hourly_repperiods

## Turn off logging for imported packages
for i in ['matplotlib']:
    logging.getLogger(i).setLevel(logging.CRITICAL)

#%%#################
### FIXED INPUTS ###
interactive = False

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def plot_unclustered_periods(profiles, sw, reeds_path, figpath):
    """
    """
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()
    ### Overlapping days
    for label, dfin in [
        # ('unscaled',profiles),
        ('scaled',profiles),
    ]:
        properties = dfin.columns.get_level_values('property').unique()
        nhours = len(dfin.columns.get_level_values('region').unique())*(24 if sw['GSw_HourlyType']=='day' else 120)
        plt.close()
        f,ax = plt.subplots(1,len(properties),sharex=True,figsize=(nhours/12, 3.75))
        for col, prop in enumerate(properties):
            dfin[prop].T.reset_index(drop=True).plot(
                ax=ax[col], lw=0.2, legend=False)
            dfin[prop].mean(axis=0).reset_index(drop=True).plot(
                ax=ax[col], lw=1.5, color='k', legend=False)
            ax[col].set_title(prop)
            for x in np.arange(0,nhours+1,(24 if sw['GSw_HourlyType']=='day' else 120)):
                ax[col].axvline(x,c='k',ls=':',lw=0.3)
            ax[col].tick_params(labelsize=9)
            ax[col].set_ylim(0)
        ### Formatting
        title = ' | '.join(
            profiles.columns.get_level_values('region').drop_duplicates().tolist())
        ax[0].annotate(title,(0,1.12), xycoords='axes fraction', fontsize='large',)
        ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(12))
        ax[0].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(6))
        ax[0].set_xlim(0, nhours)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'profiles-day_hourly-{}.png'.format(label)))
        if interactive:
            plt.show()
        plt.close()

    ### Sequential days, unscaled and scaled
    for label, dfin in [('unscaled',profiles)]:
        properties = dfin.columns.get_level_values('property').unique()
        regions = dfin.columns.get_level_values('region').unique()
        rows = [(p,r) for p in properties for r in regions]
        ### Hourly
        plt.close()
        f,ax = plt.subplots(len(rows),1,figsize=(12,12),sharex=True,sharey=False)
        for row, (p,r) in enumerate(rows):
            df = dfin[p][r].stack('h_of_period')
            ax[row].fill_between(range(len(df)), df.values, lw=0)
            ax[row].set_title('{} {}'.format(p,r),x=0.01,ha='left',va='top',pad=0)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'profiles-year_hourly-{}.png'.format(label)))
        if interactive:
            plt.show()
        plt.close()
        ### Daily
        plt.close()
        f,ax = plt.subplots(len(rows),1,figsize=(12,12),sharex=True,sharey=False)
        for row, (p,r) in enumerate(rows):
            df = dfin[p][r].mean(axis=1)
            ax[row].fill_between(range(len(df)), df.values, lw=0)
            ax[row].set_title('{} {}'.format(p,r),x=0.01,ha='left',va='top',pad=0)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'profiles-year_daily-{}.png'.format(label)))
        if interactive:
            plt.show()
        plt.close()


def plot_feature_scatter(profiles_fitperiods, reeds_path, figpath):
    """
    """
    import matplotlib.pyplot as plt
    import site
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()
    ### Settings
    colors = plots.rainbowmapper(profiles_fitperiods.columns.get_level_values('region').unique())
    props = ['load','upv','wind-ons']
    ### Plot it
    plt.close()
    f,ax = plt.subplots(3,3,figsize=(7,7),sharex='col',sharey='row')
    for row, yax in enumerate(props):
        for col, xax in enumerate(props):
            for region, c in colors.items():
                ax[row,col].plot(
                    profiles_fitperiods[xax][region].values,
                    profiles_fitperiods[yax][region].values,
                    c=c, lw=0, markeredgewidth=0, ms=5, alpha=0.5, marker='o',
                    label=(region if (row,col)==(1,2) else '_nolabel'),
                )
    ### Formatting
    ax[1,-1].legend(
        loc='center left', bbox_to_anchor=(1,0.5), frameon=False, fontsize='large',
        handletextpad=0.3,handlelength=0.7,
    )
    for i, prop in enumerate(props):
        ax[-1,i].set_xlabel(prop)
        ax[i,0].set_ylabel(prop)

    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'feature_scatter.png'))
    if interactive:
        plt.show()
    plt.close()


def plot_ldc(
        period_szn, profiles, rep_periods,
        forceperiods_write, sw, reeds_path, figpath):
    """
    """
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()

    ### Get clustered load, repeating representative periods based on how many
    ### periods they represent
    numperiods = period_szn.value_counts().rename('numperiods').to_frame()
    numperiods['yearperiod'] = numperiods.index.map(hourly_repperiods.szn2yearperiod).values
    numperiods['year'] = numperiods.index.map(hourly_repperiods.szn2yearperiod).map(lambda x: x[0])
    numperiods['yperiod'] = numperiods.index.map(hourly_repperiods.szn2period)
    periods = [[row.yearperiod] * row.numperiods for (i,row) in numperiods.iterrows()]
    periods = [item for sublist in periods for item in sublist]

    #### Hourly
    hourly_in = (
        profiles
        .divide(sw['GSw_HourlyClusterWeights'], level='property')
        .stack('h_of_period')
        .loc[sw['GSw_HourlyWeatherYears']]
    ).copy()
    hourly_out = hourly_in.unstack('h_of_period').loc[periods].stack('h_of_period')

    #### Daily
    periodly_in = hourly_in.groupby('yperiod').mean()
    ## Index doesn't matter; replace it so we can take daily mean
    periodly_out = hourly_out.copy()
    hourly_out.index = hourly_in.index.copy()
    periodly_out = hourly_out.groupby('yperiod').mean()

    ### Get axis coordinates: properties = rows, regions = columns
    properties = periodly_out.columns.get_level_values('property').unique().values
    regions = periodly_out.columns.get_level_values('region').unique().values
    nrows, ncols = len(properties), len(regions)
    coords = {}
    if ncols == 1:
        coords = dict(zip(
            [(prop, regions[0]) for prop in properties],
            range(nrows)))
    elif nrows == 1:
        coords = dict(zip(
            [(properties[0], region) for region in regions],
            range(ncols)))
    else:
        coords = dict(zip(
            [(prop, reg) for prop in properties for reg in regions],
            [(row, col) for row in range(nrows) for col in range(ncols)],
        ))

    ###### Plot it
    for plotlabel, xlabel, dfin, dfout in [
        ('hourly','Hour',hourly_in,hourly_out),
        ('periodly','Period',periodly_in,periodly_out),
    ]:
        plt.close()
        f,ax = plt.subplots(
            nrows,ncols,figsize=(len(regions)*1.2,9),sharex=True,sharey='row',
            gridspec_kw={'hspace':0.1,'wspace':0.1},
        )
        for region in regions:
            for prop in properties:
                df = dfout[prop][region].sort_values(ascending=False)
                ax[coords[prop,region]].plot(
                    range(len(dfout)), df.values,
                    label='Clustered', c='C1')
                #     label='Clustered', c='C7', lw=0.25)
                # ax[coords[prop,region]].scatter(
                #     range(len(dfout)), df.values,
                #     c=df.index.map(yperiod2color), s=10, lw=0,
                # )
                ax[coords[prop,region]].plot(
                    range(len(dfin)),
                    dfin[prop][region].sort_values(ascending=False).values,
                    ls=':', label='Original', c='k')
        ### Formatting
        for region in regions:
            ax[coords[properties[0], region]].set_title(region)
        for prop in properties:
            ax[coords[prop, regions[0]]].set_ylabel(prop)
            ax[coords[prop, regions[0]]].set_ylim(0)
        ax[coords[properties[0], regions[0]]].annotate(
            '{} periods: {} forced, {} clustered'.format(
                sw['GSw_HourlyNumClusters'], len(forceperiods_write),
                int(sw['GSw_HourlyNumClusters']) - len(forceperiods_write)),
            (0,1.15), xycoords='axes fraction', fontsize='x-large',
        )
        ax[coords[properties[0], regions[-1]]].legend(
            loc='lower right', bbox_to_anchor=(1,1.1), ncol=2)
        ax[coords[properties[-1], regions[0]]].set_xlabel(
            '{} of year'.format(xlabel), x=0, ha='left')
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'ldc-{}-{}totaldays.png'.format(
            plotlabel, sw['GSw_HourlyNumClusters'])))
        if interactive:
            plt.show()
        plt.close()


def plot_maps(sw, inputs_case, reeds_path, figpath):
    """
    """
    ### Imports
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    import reedsplots
    plots.plotparams()
    ### Settings
    cmaps = {
        'cf_actual':plt.cm.turbo, 'cf_rep':plt.cm.turbo, 'cf_diff':plt.cm.RdBu_r,
        'GW_full':cmocean.cm.rain, 'GW_hourly':cmocean.cm.rain,
        'GW_diff':plt.cm.RdBu_r, 'GW_frac':plt.cm.RdBu_r, 'GW_pct':plt.cm.RdBu_r, 
    }
    vm = {
        'wind-ons':{'cf_actual':(0,0.6),'cf_rep':(0,0.6),'cf_diff':(-0.05,0.05)},
        'upv':{'cf_actual':(0,0.3),'cf_rep':(0,0.3),'cf_diff':(-0.05,0.05)},
    }
    vlimload = 0.05
    title = (
        '{}\n'
        'Algorithm={}, NumClusters={}, RegionLevel={}, ClusterWeights={}'
    ).format(
        os.path.abspath(os.path.join(inputs_case,'..')),
        sw['GSw_HourlyClusterAlgorithm'],
        sw['GSw_HourlyNumClusters'], sw['GSw_HourlyClusterRegionLevel'],
        '__'.join(['_'.join([
            str(i),str(v)]) for (i,v) in sw['GSw_HourlyClusterWeights'].items()]))
    techs = ['wind-ons','upv']
    colors = {'cf_actual':'k', 'cf_rep':'C1'}
    lss = {'cf_actual':':', 'cf_rep':'-'}
    zorders = {'cf_actual':10, 'cf_rep':9}

    hierarchy = pd.read_csv(
        os.path.join(inputs_case, 'hierarchy.csv')).rename(columns={'*r':'r'}).set_index('r')
    dfmap = reedsplots.get_dfmap(os.path.abspath(os.path.join(inputs_case,'..')))

    ### Get the CF data over all years, take the mean over weather years
    recf = pd.read_hdf(os.path.join(inputs_case,'recf.h5'))
    fulltimeindex = np.ravel([
        pd.date_range(
            f'{y}-01-01', f'{y+1}-01-01',
            freq='H', inclusive='left', tz='EST',
        )[:8760]
        for y in range(2007,2014)
    ])
    recf.index = fulltimeindex
    recf = recf.loc[
        recf.index.map(lambda x: x.year in sw.GSw_HourlyWeatherYears)
    ].mean()

    agglevel = pd.read_csv(
        os.path.join(inputs_case, 'agglevels.csv')).squeeze(1).tolist()[0]
    lvl = 'ba' if agglevel in ['ba','state','aggreg'] else 'county'
    
    ### Get supply curves
    dfsc = {}
    for tech in techs:
        dfsc[tech] = pd.read_csv(
            os.path.join(inputs_case, f'{tech}_supply_curve.csv')
        ).rename(columns={'region':'r'})
        dfsc[tech]['i'] = tech + '_' + dfsc[tech]['class'].astype(str)

    dfsc = pd.concat(dfsc, axis=0, names=('tech',)).drop(
        ['dist_km','dist_mi','supply_curve_cost_per_mw'], errors='ignore', axis=1)

    ### Add geographic and CF information
    sitemap = pd.read_csv(
        os.path.join(inputs_case,'sitemap.csv'),
        index_col='sc_point_gid',
    )

    dfsc['latitude'] = dfsc.sc_point_gid.map(sitemap.latitude)
    dfsc['longitude'] = dfsc.sc_point_gid.map(sitemap.longitude)
    dfsc = plots.df2gdf(dfsc)
    dfsc['resource'] = dfsc.i + '_' + dfsc.r
    dfsc['cf_actual'] = dfsc.resource.map(recf)

    ### Get the BA map
    dfba = gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','US_PCA')).set_index('rb')
    dfba['x'] = dfba.geometry.centroid.x
    dfba['y'] = dfba.geometry.centroid.y

    ### Get the hourly data
    hours = pd.read_csv(
        os.path.join(inputs_case,'numhours.csv')
    ).rename(columns={'*h':'h'}).set_index('h').numhours
    dfcf = pd.read_csv(os.path.join(inputs_case,'cf_vre.csv')).rename(columns={'*i':'i'})

    for tech in techs:
        ### Get the annual average CF of the hourly-processed data
        cf_hourly = dfcf.loc[dfcf.i.str.startswith(tech)].pivot(
            index=['i','r'],columns='h',values='cf')
        cf_hourly = (
            (cf_hourly * cf_hourly.columns.map(hours)).sum(axis=1) / hours.sum()
        ).rename('cf_rep').reset_index()
        cf_hourly['resource'] = cf_hourly.i + '_' + cf_hourly.r

        ### Merge with supply curve, take the difference
        cfmap = dfsc.assign(
            cf_rep=dfsc.resource.map(cf_hourly.set_index('resource').cf_rep)).loc[tech].copy()
        cfmap['cf_diff'] = cfmap.cf_rep - cfmap.cf_actual

        ### Calculate the difference at different resolutions
        levels = ['r', 'st', 'transgrp', 'transreg', 'interconnect', 'country']
        dfdiffs = {}
        for col in levels:
            if col != 'r':
                cfmap[col] = cfmap.r.map(hierarchy[col])
            dfdiffs[col] = dfmap[col].copy()
            df = cfmap.copy()
            for i in ['cf_actual','cf_rep']:
                df['weighted'] = cfmap[i] * cfmap.capacity
                dfdiffs[col][i] = (
                    df.groupby(col).weighted.sum() / df.groupby(col).capacity.sum()
                )
            dfdiffs[col]['cf_diff'] = dfdiffs[col].cf_rep - dfdiffs[col].cf_actual

        ### Plot the difference map
        nrows, ncols, coords = plots.get_coordinates([
            'cf_actual', 'cf_rep', 'cf_diff',
            'r', 'st', 'transgrp',
            'transreg', 'interconnect', 'country',
        ], aspect=1)

        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(14,9), gridspec_kw={'wspace':-0.05, 'hspace':0},
        )
        ## Absolute and site difference
        for col in ['cf_actual','cf_rep','cf_diff']:
            cfmap.plot(
                ax=ax[coords[col]], column=col, cmap=cmaps[col],
                marker='s', markersize=0.35, lw=0,
                legend=False,
                vmin=vm[tech][col][0], vmax=vm[tech][col][1],
            )
            dfmap['st'].plot(ax=ax[coords[col]], facecolor='none', edgecolor='k', lw=0.1, zorder=1e6)
            ## Colorbar
            plots.addcolorbarhist(
                f=f, ax0=ax[coords[col]], data=cfmap[col]*100, nbins=51,
                cmap=cmaps[col],
                vmin=vm[tech][col][0]*100, vmax=vm[tech][col][1]*100,
                cbarleft=0.95, cbarbottom=0.1, ticklabel_fontsize=7,
            )
        ## Regional differences
        for level in levels:
            dfdiffs[level].plot(
                ax=ax[coords[level]], column='cf_diff', cmap=cmaps['cf_diff'],
                vmin=vm[tech]['cf_diff'][0], vmax=vm[tech]['cf_diff'][1], 
                lw=0, legend=False,
            )
            dfmap[level].plot(ax=ax[coords[level]], facecolor='none', edgecolor='k', lw=0.2)
            ## Text differences
            for r, row in (dfdiffs[level].assign(val=dfdiffs[level].cf_diff.abs()).sort_values('val')).iterrows():
                decimals = 0 if abs(row.cf_diff) >= 1 else 1
                ax[coords[level]].annotate(
                    f"{row.cf_diff*100:+.{decimals}f}",
                    [row.centroid_x, row.centroid_y],
                    ha='center', va='center', c='k', fontsize={'r':5}.get(level,7),
                    path_effects=[pe.withStroke(linewidth=1.5, foreground='w', alpha=0.5)],
                )
            ## Colorbar
            plots.addcolorbarhist(
                f=f, ax0=ax[coords[level]], data=dfdiffs[level].cf_diff*100, nbins=51,
                cmap=cmaps['cf_diff'],
                vmin=vm[tech]['cf_diff'][0]*100, vmax=vm[tech]['cf_diff'][1]*100,
                cbarleft=0.95, cbarbottom=0.1, ticklabel_fontsize=7,
            )
        ## Formatting
        ax[0,0].annotate(title+f', tech={tech}', (0.05,1.05), xycoords='axes fraction', fontsize=10)
        for level in coords:
        # for row in range(nrows):
        #     for col in range(ncols):
                ax[coords[level]].set_title({'cf_diff':'site'}.get(level,level), y=0.9, weight='bold')
                ax[coords[level]].axis('off')
        savename = f"cfmap-{tech.replace('-','')}-{sw.GSw_HourlyNumClusters}totaldays.png"
        print(savename)
        plt.savefig(os.path.join(figpath,savename))
        if interactive:
            plt.show()
        plt.close()

        ### Plot the distribution of capacity factors
        plt.close()
        f,ax = plt.subplots()
        for col in ['cf_actual','cf_rep']:
            ax.plot(
                np.linspace(0,100,len(cfmap)),
                cfmap.sort_values('cf_actual', ascending=False)[col].values,
                label=col.split('_')[1],
                color=colors[col], ls=lss[col], zorder=zorders[col],
            )
        ax.set_ylim(0)
        ax.set_xlim(-1,101)
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
        ax.legend(fontsize='large', frameon=False)
        ax.set_ylabel('{} capacity factor [.]'.format(tech))
        ax.set_xlabel('Percent of sites [%]')
        ax.set_title(
            '\n'.join(title.split('\n')[1:]).replace(' ','\n').replace(',',''),
            x=0, ha='left', fontsize=10)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'cfmapdist-{}-{}totaldays.png'.format(
            tech.replace('-',''), sw['GSw_HourlyNumClusters'])))
        if interactive:
            plt.show()
        plt.close()

    ###### Do it again for load
    ### Get the full hourly data, take the mean for the cluster year and weather year(s)
    load_raw = pd.read_hdf(os.path.join(inputs_case, 'load.h5'))
    loadyears = load_raw.index.get_level_values('year').unique()
    keepyear = (
        int(sw['GSw_HourlyClusterYear']) if int(sw['GSw_HourlyClusterYear']) in loadyears
        else max(loadyears))
    load_raw = load_raw.loc[keepyear].copy()
    load_raw.index = fulltimeindex
    load_raw = load_raw.loc[
        load_raw.index.map(lambda x: x.year in sw.GSw_HourlyWeatherYears)
    ].mean() / 1000
    ## load.h5 is busbar load, but b_inputs.gms ingests end-use load, so scale down by distloss
    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, usecols=[0,1], index_col=0).squeeze(1)
    load_raw *= (1 - scalars['distloss'])
    ### Get the representative data, take the mean for the cluster year
    load_allyear = (
        pd.read_csv(os.path.join(inputs_case, 'load_allyear.csv')).rename(columns={'*r':'r'})
        .set_index(['t','r','h']).MW.loc[keepyear]
        .multiply(hours).groupby('r').sum()
        / hours.sum()
    ) / 1000
    ### Map it
    dfmap = dfba.copy()
    dfmap['GW_full'] = load_raw
    dfmap['GW_hourly'] = load_allyear
    dfmap['GW_diff'] = dfmap.GW_hourly - dfmap.GW_full
    dfmap['GW_frac'] = dfmap.GW_hourly / dfmap.GW_full - 1

    ### Plot the difference map
    plt.close()
    f,ax = plt.subplots(1,3,figsize=(13,4),gridspec_kw={'wspace':-0.05})
    for col in range(3):
        dfmap['st'].plot(ax=ax[col], facecolor='none', edgecolor='k', lw=0.25, zorder=10000)
    for x,col in enumerate(['GW_full','GW_hourly','GW_frac']):
        dfmap.plot(
            ax=ax[x], column=col, cmap=cmaps[col], legend=True,
            legend_kwds={'shrink':0.75,'orientation':'horizontal',
                        'label':'load {}'.format(col), 'pad':0},
            vmin=(0 if col != 'GW_frac' else -vlimload),
            vmax=(dfmap[['GW_full','GW_hourly']].max().max() if col != 'GW_frac' else vlimload),
        )
        ax[x].axis('off')
    ax[0].set_title(title, y=0.95, x=0.05, ha='left', fontsize=10)
    plt.savefig(os.path.join(figpath,'loadmap-{}totaldays.png'.format(
        sw['GSw_HourlyNumClusters'])))
    if interactive:
        plt.show()
    plt.close()

    ### Plot the distribution of load by region
    colors = {'GW_full':'k', 'GW_hourly':'C1'}
    lss = {'GW_full':':', 'GW_hourly':'-'}
    zorders = {'GW_full':10, 'GW_hourly':9}
    plt.close()
    f,ax = plt.subplots()
    for col in ['GW_full','GW_hourly']:
        ax.plot(
            range(1,len(dfmap)+1),
            dfmap.sort_values('GW_full', ascending=False)[col].values,
            label='{} ({:.1f} GW mean)'.format(col.split('_')[1], dfmap[col].sum()),
            color=colors[col], ls=lss[col], zorder=zorders[col],
        )
    ax.set_ylim(0)
    ax.set_xlim(0,len(dfmap)+1)
    ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
    ax.legend(fontsize='large', frameon=False)
    ax.set_ylabel('Average load [GW]')
    ax.set_xlabel('Number of BAs')
    ax.set_title(title.replace(' ','\n').replace(',',''), x=0, ha='left', fontsize=10)
    plots.despine(ax)
    plt.savefig(os.path.join(figpath,'loadmapdist-{}totaldays.png'.format(
        sw['GSw_HourlyNumClusters'])))
    if interactive:
        plt.show()
    plt.close()


def plot_8760(profiles, period_szn, sw, reeds_path, figpath):
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()

    def get_profiles(regions, year):
        """Assemble 8760 profiles from original and representative days"""
        timeindex = pd.date_range(f'{year}-01-01',f'{year+1}-01-01',freq='H',inclusive='left')[:8760]
        props = profiles.columns.get_level_values('property').unique()
        ### Original profiles
        dforig = {}
        for prop in props:
            df = profiles[prop].loc[year].stack('h_of_period')[regions].sum(axis=1)
            dforig[prop] = df / df.max()
            dforig[prop].index = timeindex
        dforig = pd.concat(dforig, axis=1)

        ### Representative profiles
        periodmap = period_szn.map(hourly_repperiods.szn2yearperiod).to_frame()
        periodmap['year'] = periodmap.index.map(lambda x: x[0])
        periodmap['yperiod'] = periodmap.index.map(lambda x: x[1])
        periodmap = periodmap.loc[periodmap.year==year].yperiod

        dfrep = {}
        for prop in props:
            df = (
                profiles[prop].loc[year].loc[periodmap.values]
                .stack('h_of_period')[regions].sum(axis=1))
            dfrep[prop] = df / df.max()
            dfrep[prop].index = timeindex
        dfrep = pd.concat(dfrep, axis=1)

        return dforig, dfrep

    ###### All regions
    for year in sw['GSw_HourlyWeatherYears']:
        props = profiles.columns.get_level_values('property').unique()
        regions = profiles.columns.get_level_values('region').unique()
        dforig, dfrep = get_profiles(regions, year)

        ### Original vs representative
        plt.close()
        f,ax = plt.subplots(38,1,figsize=(12,16),sharex=True,sharey=True)
        for i, prop in enumerate(props):
            plots.plotyearbymonth(
                dfrep[prop].rename('Representative').to_frame(),
                style='line', colors=['C1'], ls='-', f=f, ax=ax[i*12+i:(i+1)*12+i])
            plots.plotyearbymonth(
                dforig[prop].rename('Original').to_frame(),
                style='line', colors=['k'], ls=':', f=f, ax=ax[i*12+i:(i+1)*12+i])
        for i in [12,25]:
            ax[i].axis('off')
        for i, prop in list(zip(range(len(props)), props)):
            ax[i*12+i].set_title(
                '{}: {}'.format(prop,' | '.join(regions)),x=0,ha='left',fontsize=12)
        ax[0].legend(loc='lower left', bbox_to_anchor=(0,1.5), ncol=2, frameon=False)
        plt.savefig(os.path.join(figpath,f'8760-allregions-{year}.png'))
        if interactive:
            plt.show()
        plt.close()

        ### Load, wind, solar together; original
        plt.close()
        f,ax = plots.plotyearbymonth(
            dforig[['wind-ons','upv']], colors=['#0064ff','#ff0000'], alpha=0.5)
        plots.plotyearbymonth(dforig['load'], f=f, ax=ax, style='line', colors='k')
        plt.savefig(os.path.join(figpath,f'8760-allregions-original-{year}.png'))
        if interactive:
            plt.show()
        plt.close()

        ### Load, wind, solar together; representative
        plt.close()
        f,ax = plots.plotyearbymonth(
            dfrep[['wind-ons','upv']], colors=['#0064ff','#ff0000'], alpha=0.5)
        plots.plotyearbymonth(dfrep['load'], f=f, ax=ax, style='line', colors='k')
        plt.savefig(os.path.join(figpath,f'8760-allregions-representative-{year}.png'))
        if interactive:
            plt.show()
        plt.close()

        ###### Individual regions, original vs representative
        for region in profiles.columns.get_level_values('region').unique():
            dforig, dfrep = get_profiles([region], year)

            plt.close()
            f,ax = plt.subplots(38,1,figsize=(12,16),sharex=True,sharey=True)
            for i, prop in enumerate(props):
                plots.plotyearbymonth(
                    dfrep[prop].rename('Representative').to_frame(),
                    style='line', colors=['C1'], ls='-', f=f, ax=ax[i*12+i:(i+1)*12+i])
                plots.plotyearbymonth(
                    dforig[prop].rename('Original').to_frame(),
                    style='line', colors=['k'], ls=':', f=f, ax=ax[i*12+i:(i+1)*12+i])
            for i in [12,25]:
                ax[i].axis('off')
            for i, prop in list(zip(range(len(props)), props)):
                ax[i*12+i].set_title('{}: {}'.format(prop,region),x=0,ha='left',fontsize=12)
            ax[0].legend(loc='lower left', bbox_to_anchor=(0,1.5), ncol=2, frameon=False)
            plt.savefig(os.path.join(figpath,f'8760-{region}-{year}.png'))
            if interactive:
                plt.show()


def plots_original(
        profiles, rep_periods, period_szn,
        sw, reeds_path, figpath,
    ):
    """
    """
    site.addsitedir(os.path.join(reeds_path,'postprocessing'))
    import plots
    plots.plotparams()

    ### Input processing
    idx_reedsyr = period_szn.map(hourly_repperiods.szn2yearperiod)
    medoid_profiles = profiles.loc[rep_periods]
    centroids = profiles.loc[rep_periods]
    centroid_profiles = centroids * profiles.stack('h_of_period').max()

    colors = plots.rainbowmapper(list(set(idx_reedsyr)), plt.cm.turbo)

    ### PLOT ALL DAYS ON SAME X AXIS:
    try:
        ## Map days to axes
        ncols = len(colors)
        nrows = 1
        coords = dict(zip(
            colors.keys(),
            [col for col in range(ncols)]
        ))
        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(1.5*ncols,2.5*nrows), sharex=True, sharey=True)
        for day in range(len(idx_reedsyr)):
            szn = idx_reedsyr[day]
            this_profile = profiles.load.iloc[day].groupby('h_of_period').sum()
            ax[coords[szn]].plot(
                range(len(this_profile)), this_profile.values/1e3, color=colors[szn], alpha=0.5)
        ## add centroids and medoids to the plot:
        for szn in colors:
            ## centroids - only for clustered days, not force-included days
            try:
                ax[coords[szn]].plot(
                    range(len(this_profile)),
                    centroid_profiles['load'].loc[szn].groupby('h_of_period').sum().values/1e3,
                    color='k', alpha=1, linewidth=2, label='centroid',
                )
            except IndexError:
                pass
            ## medoids
            ax[coords[szn]].plot(
                range(len(this_profile)),
                medoid_profiles['load'].loc[szn].groupby('h_of_period').sum().values/1e3,
                ls='--', color='0.7', alpha=1, linewidth=2, label='medoid',
            )
            ## title
            ax[coords[szn]].set_title(
                '{}, {} days'.format(szn, idx_reedsyr.value_counts()[szn]), size=9)

        ax[0].legend(loc='upper left', frameon=False, fontsize='small')
        ax[0].set_xlabel('Hour')
        ax[0].set_ylabel('Conterminous\nUS Load [GW]', y=0, ha='left')
        ax[0].xaxis.set_major_locator(
            mpl.ticker.MultipleLocator(6 if sw['GSw_HourlyType']=='day' else 24))
        ax[0].xaxis.set_minor_locator(
            mpl.ticker.MultipleLocator(3 if sw['GSw_HourlyType']=='day' else 12))
        ax[0].annotate(
            'Cluster Comparison (All Days in {} Shown)'.format(
                '2007–2013' if len(profiles.index.unique(level='year')) > 1 else '2012' ),
            xy=(0,1.2), xycoords='axes fraction', ha='left',
        )
        plots.despine(ax)
        plt.savefig(os.path.join(figpath,'day_comparison_all.png'))
        if interactive:
            plt.show()
        plt.close()
    except Exception as err:
        print('day_comparison_all.png failed with the following error:\n{}'.format(err))

