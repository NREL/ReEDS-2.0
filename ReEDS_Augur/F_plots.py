#%%### Imports
import sys, os, site, math, time
import gdxpds
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from ReEDS_Augur.utility.switchsettings import SwitchSettings
Sw = SwitchSettings.switches

# #%% Debugging
# Sw['basedir'] = os.path.expanduser('~/github2/ReEDS-2.0/')
# Sw['casedir'] = os.path.join(Sw['basedir'],'runs','v20221013_PTDFm0_USA')

site.addsitedir(os.path.join(Sw['basedir'],'postprocessing'))
import plots
plots.plotparams()

pd.options.display.max_rows = 20
pd.options.display.max_columns = 200

#%%### INPUTS
dpi = None
interactive = False
savefig = True
capcredit_szn_hours = Sw['capcredit_szn_hours']
### Day used for merit order curve (d200 is in the middle of summer)
day = 'd200'
### aggregation levels to use for dispatch plots
dispatchregions = [
    ('country','USA'),
    ('interconnect','western'),
    ('interconnect','texas'),
    ('interconnect','eastern'),
]

#%%### Functions

#%%### Procedure
savepath = os.path.join(Sw['casedir'], 'outputs', 'Augur_plots')
os.makedirs(savepath, exist_ok=True)
failed_plots = []

#%%## Load shared parameters
timeindex = pd.date_range(
    '{}-01-01'.format(Sw['reeds_data_year']),
    '{}-01-01'.format(Sw['reeds_data_year']+1),
    freq='H', closed='left', tz='US/Eastern',
)[:8760]
fulltimeindex = np.ravel([
    pd.date_range(
        '{}-01-01'.format(y),
        '{}-01-01'.format(y+1),
        freq='H', closed='left', tz='US/Eastern',
    )[:8760]
    for y in range(2007,2014)
])

h_dt_szn = (
    pd.read_csv(os.path.join(Sw['casedir'],'inputs_case','h_dt_szn.csv'))
    .assign(d=['d{}'.format(i//24+1) for i in range(8760*7)])
    .assign(hr=['hr{}'.format(i+1) for i in range(24)]*365*7)
    .assign(datetime=fulltimeindex)
)
season2szn = {'winter':'wint','spring':'spri','summer':'summ','fall':'fal'}

tech_map = pd.read_csv(
    os.path.join(Sw['basedir'],'postprocessing','bokehpivot','in','reeds2','tech_map.csv'),
    index_col='raw', squeeze=True,
)

tech_style = pd.read_csv(
    os.path.join(Sw['basedir'],'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
    index_col='order', squeeze=True,
)
## Add some techs
for i in [1,2]:
    tech_style[f'csp{i}'] = tech_style['csp']
for i in [1,2,3]:
    tech_style[f'pvb{i}'] = tech_style['pvb']

hierarchy = pd.read_csv(
    os.path.join(Sw['casedir'],'inputs_case','hierarchy.csv')
).rename(columns={'*r':'r'}).set_index('r')
hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()

resources = pd.read_csv(
    os.path.join(Sw['casedir'],'inputs_case','resources.csv')
).set_index('resource')
resources['tech'] = resources.i.map(lambda x: x.split('_')[0])

s2r = pd.read_csv(
    os.path.join(Sw['casedir'],'inputs_case','rsmap.csv'),
    header=0, names=['r','rs'], index_col='rs', squeeze=True,
)
resources['rb'] = resources.r.map(lambda x: s2r.get(x,x))

#%%## Hourly dispatch by month
#%% Load and aggregate the VRE generation profiles by tech group
vre_gen = pd.read_hdf(
    os.path.join('ReEDS_Augur','augur_data',
                 'plot_vre_gen_{}.h5'.format(Sw['prev_year'])))
### Get vre_gen by tech (only ReEDS year)
vre_gen_usa = (
    vre_gen
    .rename(columns=resources.tech)
    .sum(axis=1, level=0)
    .xs(Sw['reeds_data_year'], level='year', axis=0)
    .set_index(timeindex)
)
### Get vre_gen summed over tech by BA (full 7 years)
vre_gen_r = (
    vre_gen
    .rename(columns=resources.rb.to_dict())
    .sum(axis=1, level=0)
)

def get_vre_gen(level='interconnect', region='western'):
    """
    Return the sum of vre_gen by tech for hierarchy level/region
    """
    keeper = resources.r.map(lambda x: s2r.get(x,x)).map(hierarchy[level])
    vre_gen_out = vre_gen.iloc[:,vre_gen.columns.map(keeper)==region]
    vre_gen_out = (
        vre_gen_out
        .rename(columns=resources.tech)
        .sum(axis=1, level=0)
        .xs(Sw['reeds_data_year'], level='year', axis=0)
        .set_index(timeindex)
    )
    return vre_gen_out


#%% Broadcast mustrun capacity to timeindex
mustrun = pd.read_hdf(
    os.path.join('ReEDS_Augur','augur_data',
                 'plot_mustrun_{}.h5'.format(Sw['prev_year'])))

def get_mustrun(level='interconnect', region='western'):
    """
    Return the sum of mustrun by tech for hierarchy level/region
    """
    mustrun_out = (
        mustrun
        .assign(region=mustrun.r.map(hierarchy[level]))
        .groupby(['i','szn','region']).MW.sum()
        .unstack('region')[region]
        .unstack('i')
        .merge(
            h_dt_szn.loc[h_dt_szn.year==Sw['reeds_data_year']]
            .replace(season2szn)[['season','hour']],
            left_index=True, right_on='season', how='right')
        .drop(['season','hour'], axis=1)
        .rename(columns=tech_map)
        .rename(columns={'hydro':'hydro_nd'})
        .sum(axis=1, level=0)
        .set_index(timeindex)
    )
    return mustrun_out

mustrun_usa = get_mustrun('country','USA')

#%% Load load
load_r = pd.read_hdf(
    os.path.join('ReEDS_Augur','augur_data',
                 'plot_load_{}.h5'.format(Sw['prev_year'])))
### Sum over US
load_usa = (
    load_r
    .sum(axis=1)
    .xs(Sw['reeds_data_year'], level='year', axis=0)
    .rename('Demand')
    .sort_index(level='hour')
    .set_axis(timeindex)
)

def get_load(level='interconnect', region='western'):
    """
    Return the sum of load for hierarchy level/region
    """
    load_out = (
        load_r
        .rename(columns=hierarchy[level])
        .sum(axis=1, level=0)
        [region]
        .xs(Sw['reeds_data_year'], level='year', axis=0)
        .rename('Demand')
        .sort_index(level='hour')
        .set_axis(timeindex)
    )
    return load_out

#%% Load and aggregate Osprey generation profiles
try:
    gen = pd.read_csv(
        os.path.join('ReEDS_Augur','augur_data',
                    'gen_{}.csv'.format(Sw['prev_year'])))
    gen.i = gen.i.map(lambda x: x if x == 'Canada' else x.lower())

    def get_gen(level='interconnect', region='western'):
        """
        Return the sum of gen by tech for hierarchy level/region
        """
        gen_out = (
            gen
            .assign(region=gen.r.map(hierarchy[level]))
            .groupby(['d','hr','i','region']).Val.sum()
            .unstack('region')[region]
            .unstack('i').fillna(0)
            .loc[h_dt_szn.loc[h_dt_szn.year==2007,['d','hr']].values.tolist()]
            .rename(columns=tech_map)
            .rename(columns={'hyded':'hydro_d','hydud':'hydro_d','gas-ct_re-ct':'h2-ct'})
            .sum(axis=1, level=0)
            .set_index(timeindex)
        )
        return gen_out

    gen_usa = get_gen('country','USA')

except Exception as err:
    failed_plots.append(('gen_{}.csv'.format(Sw['prev_year']), err))

#%% Load storage charging
try:
    stor_charge = pd.read_csv(
        os.path.join('ReEDS_Augur','augur_data',
                    'storage_in_{}.csv'.format(Sw['prev_year'])))

    def get_stor_charge(level='interconnect', region='western'):
        """
        Return the sum of gen by tech for hierarchy level/region
        """
        if stor_charge.empty:
            return pd.DataFrame(index=timeindex)
        stor_charge_out = (
            stor_charge
            .assign(region=stor_charge.r.map(hierarchy[level]))
            .groupby(['d','hr','i','region']).Val.sum()
            .unstack('region')[region]
            .unstack('i')
            .reindex(h_dt_szn.loc[h_dt_szn.year==2007,['d','hr']].values, axis=0)
            .fillna(0)
            .set_index(timeindex)
            * -1
        )
        return stor_charge_out

    stor_charge_usa = get_stor_charge('country','USA')
    stortechs = stor_charge_usa.columns.values

except Exception as err:
    failed_plots.append(('storage_in_{}.csv'.format(Sw['prev_year']), err))

#%% Load H2/CO2 production load
try:
    produce = pd.read_csv(
        os.path.join('ReEDS_Augur','augur_data',
                    'produce_{}.csv'.format(Sw['prev_year'])))

    def get_produce(level='interconnect', region='western'):
        """
        Return the sum of gen by tech for hierarchy level/region
        """
        if produce.empty:
            return pd.Series(index=timeindex, data=0, name=region)
        produce_out = (
            produce
            .assign(region=produce.r.map(hierarchy[level]))
            .groupby(['d','hr','region']).Val.sum()
            .unstack('region').reindex(hierarchy[level].unique(), axis=1)[region]
            .reindex(h_dt_szn.loc[h_dt_szn.year==2007,['d','hr']].values, axis=0)
            .fillna(0)
            .set_axis(timeindex)
            * -1
        )
        return produce_out

    produce_usa = get_produce('country','USA')

except Exception as err:
    failed_plots.append(('produce_{}.csv'.format(Sw['prev_year']), err))

#%% Load storage energy level
try:
    stor_energy = (
        pd.read_csv(
            os.path.join('ReEDS_Augur','augur_data',
                        'storage_level_{}.csv'.format(Sw['prev_year'])))
        .groupby(['d','hr','i']).Val.sum()
        .unstack('i')
        .reindex(h_dt_szn.loc[h_dt_szn.year==2007,['d','hr']].values, axis=0)
        .fillna(0)
        .set_index(timeindex)
    )

except Exception as err:
    failed_plots.append(('storage_level_{}.csv'.format(Sw['prev_year']), err))

#%% Load dropped load
try:
    dropped_load = (
        pd.read_csv(
            os.path.join('ReEDS_Augur','augur_data',
                        'dropped_load_{}.csv'.format(Sw['prev_year'])))
        .groupby(['d','hr']).Val.sum()
        .reindex(h_dt_szn.loc[h_dt_szn.year==2007,['d','hr']].values, axis=0)
        .fillna(0)
    )
    dropped_load.index = timeindex

except Exception as err:
    failed_plots.append(('dropped_load_{}.csv'.format(Sw['prev_year']), err))

#%%### Get net load profiles
### Get net load by BA
net_load_r = load_r - vre_gen_r
### Get net load by ccreg
net_load_ccreg = net_load_r.rename(columns=hierarchy.ccreg).sum(axis=1, level=0)
### Get net load for the USA for a single year
net_load_usa = net_load_r.set_index(fulltimeindex).sum(axis=1).loc[str(Sw['reeds_data_year'])]

#%% Assign colors based on bokeh defaults
colors = {
    'coal':tech_style['coal'], 'hydro':tech_style['hydro'],
    'hydro_nd':tech_style['hydro'], 'hydro_d':tech_style['hydro'],
    're-cc':tech_style['re-cc'], 're-ct':tech_style['re-ct'],
    'produce':tech_style['electrolyzer'],
    'csp1':tech_style['csp'], 'csp2':tech_style['csp'],
    'pvb1':tech_style['pvb'], 'pvb2':tech_style['pvb'], 'pvb3':tech_style['pvb'],
}
try:
    for i in gen_usa.columns.tolist() + vre_gen_usa.columns.tolist() + mustrun_usa.columns.tolist():
        if i in colors:
            pass
        elif i in tech_style:
            colors[i] = tech_style[i]
        elif i in tech_map:
            colors[i] = tech_style[tech_map[i]]
        else:
            colors[i] = 'k'
            print('missing color for {}'.format(i))
except Exception as err:
    print(err)




#%%##########
### PLOTS ###

#%%### Plot: Osprey hourly dispatch, full year full US
savename = 'B1-dispatch-usa-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    dfall = (
        mustrun_usa
        .merge(gen_usa, left_index=True, right_index=True)
        .merge(vre_gen_usa, left_index=True, right_index=True)
    )
    ### Aggregate some columns
    groupcols = {
        **{c: 'coal' for c in dfall if c.startswith('coal')},
        **{c: 'hydro' for c in dfall if c.startswith('hydro')},
        **{c: 're-cc' for c in dfall if c.endswith('re-cc')},
        **{c: 're-ct' for c in dfall if c.endswith('re-ct')},
        # **tech_map.map(tech_style).to_dict(),
    }
    dfpos = dfall.rename(columns=groupcols).sum(axis=1, level=0)
    order = [c for c in tech_style.index if c in dfpos]
    if not len(order) == dfpos.shape[1]:
        raise Exception(
            "order and dfpos don't match: {} {} {}".format(
                len(order), dfpos.shape[1], ','.join([c for c in dfpos if c not in order])))
    dfpos = dfpos[order].cumsum(axis=1)[order[::-1]]
    ### Negative components
    dfneg = (
        pd.concat([stor_charge_usa, produce_usa.rename('produce')], axis=1)
        .cumsum(axis=1)
        [['produce']+stor_charge_usa.columns[::-1].tolist()]
    )

    ### Plot it
    plt.close()
    ## Generation
    f,ax = plots.plotyearbymonth(
        dfpos, colors=[colors[c] for c in dfpos], dpi=dpi,
    )
    ## Storage charging and H2/DAC production load
    plots.plotyearbymonth(
        dfneg, f=f, ax=ax, colors=[colors[c] for c in dfneg],
    )
    ## Load
    plots.plotyearbymonth(
        load_usa.to_frame(), f=f, ax=ax, colors=['k'], style='line', lwforline=0.75,
    )
    ## Legend
    leg = ax[0].legend(
        loc='upper left', bbox_to_anchor=(1,1.25),
        fontsize=11, frameon=False, ncol=2,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    leg.set_title('Generation', prop={'size':'large'})

    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%% Table: Hourly profiles for USA
savename = 'B1C1-profiles-usa-{}-{}.csv.gz'.format(Sw['scen'],Sw['prev_year'])
try:
    #%% Get existing curtailment
    curtailment = (
        pd.read_hdf(
            os.path.join('ReEDS_Augur','augur_data',
                        'curt_C1_{}.h5'.format(Sw['prev_year'])))
        .set_index(timeindex)
    )
    #%% Combine results
    dfout = pd.concat({
        'gen_pos': dfall.rename(columns=groupcols).sum(axis=1, level=0)[order],
        'gen_neg': pd.concat([stor_charge_usa, produce_usa.rename('produce')], axis=1),
        'load': pd.concat([
            load_usa.rename('total'),
            net_load_usa.rename('net'),
            dropped_load.rename('dropped'),
        ], axis=1),
        'curtailment': curtailment.sum(axis=1).rename('curtailment').to_frame(),
        'energy': stor_energy,
    }, axis=1).round(1)

    if savefig: dfout.to_csv(os.path.join(savepath,savename))

except Exception as err:
    failed_plots.append((savename, err))




#%%### Plot: Load & generation duration curve
savename = 'B1-load-duration-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    sorted_index = load_usa.sort_values(ascending=False).index
    dfplot = dfpos.loc[sorted_index].set_index(np.linspace(0,100,len(dfpos))) / 1000
    plt.close()
    f,ax = plt.subplots(figsize=(7,3.75), dpi=dpi)
    ## Generation
    dfplot.plot.area(ax=ax, color=colors, lw=0, stacked=False, alpha=1)
    ## Wash it out
    dfplot.sum(axis=1).plot.area(ax=ax, color='w', lw=0, alpha=0.3)
    ## Load
    ax.plot(
        np.linspace(0,100,len(load_usa)),
        load_usa.loc[sorted_index].values / 1000,
        c='k', ls='-', lw=2, solid_capstyle='butt')
    ## Mark the extrema
    ax.plot(
        [0], [load_usa.max()/1000],
        lw=0, marker=1, ms=5, c='k',)
    ax.plot(
        [100], [load_usa.min()/1000],
        lw=0, marker=0, ms=5, c='k',)
    ## Formatting
    ax.set_ylabel('Load [GW]')
    ax.set_xlabel('Percent of year [%]')
    ax.set_xlim(0,100)
    ax.legend(
        loc='center left', bbox_to_anchor=(1,0.5),
        fontsize=11, frameon=False, ncol=2,
        columnspacing=0.5, handletextpad=0.5, handlelength=0.75,
    )
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%%### Plot: Net load duration curve
savename = 'B1-netload-duration-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    sorted_index = net_load_usa.sort_values(ascending=False).index
    dfplot = dfpos.loc[sorted_index].set_index(np.linspace(0,100,len(dfpos))) / 1000
    plt.close()
    f,ax = plt.subplots(figsize=(7,3.75), dpi=dpi)
    ## Generation
    dfplot.plot.area(ax=ax, color=colors, lw=0, stacked=False, alpha=1)
    ## Wash it out
    dfplot.sum(axis=1).plot.area(ax=ax, color='w', lw=0, alpha=0.3)
    ## Net load
    ax.plot(
        np.linspace(0,100,len(net_load_usa)),
        net_load_usa.loc[sorted_index].values / 1000,
        c='k', ls='-', lw=2, solid_capstyle='butt')
    ## Mark the extrema
    ax.plot(
        [0], [net_load_usa.max()/1000],
        lw=0, marker=1, ms=5, c='k',)
    ax.plot(
        [net_load_usa.sort_values(ascending=False).abs().argmin() / len(net_load_usa) * 100],
        [0],
        lw=0, marker=2, ms=5, c='k',)
    ## Formatting
    ax.set_ylabel('Net load [GW]')
    ax.set_xlabel('Percent of year [%]')
    ax.set_xlim(0,100)
    # ax.set_ylim(net_load_usa.min()/1000)
    ax.legend(
        loc='center left', bbox_to_anchor=(1,0.5),
        fontsize=11, frameon=False, ncol=2,
        columnspacing=0.5, handletextpad=0.5, handlelength=0.75,
    )
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%%### Plot: Net load profile
savename = 'A-netload-profile-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    dfpos = net_load_usa.clip(lower=0)
    dfneg = net_load_usa.clip(upper=0)
    plt.close()
    f,ax = plots.plotyearbymonth(
        dfpos, colors=['C3'], dpi=dpi,
    )
    plots.plotyearbymonth(
        dfneg, colors=['C0'],
        f=f, ax=ax,
    )
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    failed_plots.append((savename,err))




#%%### Plot: Osprey hourly dispatch for max/min net load days ±3 days
savename = 'B1-dispatch-maxmin_netload_weeks-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    plottimes = {}
    for level, region in dispatchregions:
        net_load_region = (
            net_load_r.rename(columns=hierarchy[level])
            .sum(axis=1, level=0)
            .set_index(fulltimeindex)
            .loc[str(Sw['reeds_data_year'])]
            [region]
        )
        net_load_region_day = net_load_region.groupby([
            net_load_region.index.month, net_load_region.index.day
        ]).sum()
        peakdays = {
            'min': net_load_region_day.nsmallest(1).index.values[0],
            'max': net_load_region_day.nlargest(1).index.values[0],
        }
        ### Add 3 days on either side
        for i in peakdays:
            peakdaystart = pd.Timestamp(
                '{}-{}-{} 00:00'.format(Sw['reeds_data_year'], *peakdays[i]), tz='US/Eastern')
            ### Loop back to beginning of year (messes up datetime x axis on plots)
            # peakrange = range(
            #     (list(timeindex).index(peakdaystart) - 72),
            #     (list(timeindex).index(peakdaystart) + 96))
            # plottimes[level,region,i] = timeindex[[h % 8760 for h in peakrange]]
            ### Just keep the timestamps that are in the next year, then drop from plot
            plottimes[level,region,i] = pd.date_range(
                peakdaystart - pd.Timedelta('72H'),
                peakdaystart + pd.Timedelta('95H'),
                freq='H',
            )

    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        len(dispatchregions)*2, 1, figsize=(10,len(dispatchregions)*3.0),
        gridspec_kw={'hspace':0.75},
    )
    for row, (level,region) in enumerate(dispatchregions):
        dfall = (
            get_mustrun(level,region)
            .merge(get_gen(level,region), left_index=True, right_index=True)
            .merge(get_vre_gen(level,region), left_index=True, right_index=True)
        ) / 1000
        ### Aggregate some columns
        groupcols = {
            **{c: 'coal' for c in dfall if c.startswith('coal')},
            **{c: 'hydro' for c in dfall if c.startswith('hydro')},
            **{c: 're-cc' for c in dfall if c.endswith('re-cc')},
            **{c: 're-ct' for c in dfall if c.endswith('re-ct')},
            # **tech_map.map(tech_style).to_dict(),
        }
        dfpos = dfall.rename(columns=groupcols).sum(axis=1, level=0)
        order = [c for c in tech_style.index if c in dfpos]
        if not len(order) == dfpos.shape[1]:
            raise Exception(
                "order and dfpos don't match: {} {} {}".format(
                    len(order), dfpos.shape[1], ','.join([c for c in dfpos if c not in order])))
        dfpos = dfpos[order].cumsum(axis=1)[order[::-1]]
        ### Negative components
        dfneg = (
            pd.concat(
                [get_stor_charge(level,region),
                get_produce(level,region).rename('produce')],
                axis=1)
            .cumsum(axis=1)
            [['produce']+get_stor_charge(level,region).columns[::-1].tolist()]
        ) / 1000

        ### Plot the max net load week
        for plotcol in dfpos:
            ax[row*2].fill_between(
                plottimes[level,region,'max'],
                dfpos.reindex(plottimes[level,region,'max'])[plotcol].fillna(0).values,
                lw=0, color=colors[plotcol], label=plotcol,
            )
        for plotcol in dfneg:
            ax[row*2].fill_between(
                plottimes[level,region,'max'],
                dfneg.reindex(plottimes[level,region,'max'])[plotcol].fillna(0).values,
                lw=0, color=colors[plotcol], label=plotcol,
            )
        ax[row*2].plot(
            plottimes[level,region,'max'],
            get_load(level,region).reindex(plottimes[level,region,'max']).fillna(0).values / 1000,
            color='k', lw=1.5,
        )
        ax[row*2].set_title(
            '{} max'.format(region), x=0.01, ha='left', va='top', y=1.0, weight='bold')
        ### Plot the min net load week
        for plotcol in dfpos:
            ax[row*2+1].fill_between(
                plottimes[level,region,'min'],
                dfpos.reindex(plottimes[level,region,'min'])[plotcol].fillna(0).values,
                lw=0, color=colors[plotcol], label=plotcol,
            )
        for plotcol in dfneg:
            ax[row*2+1].fill_between(
                plottimes[level,region,'min'],
                dfneg.reindex(plottimes[level,region,'min'])[plotcol].fillna(0).values,
                lw=0, color=colors[plotcol], label=plotcol,
            )
        ax[row*2+1].plot(
            plottimes[level,region,'min'],
            get_load(level,region).reindex(plottimes[level,region,'min']).fillna(0).values / 1000,
            color='k', lw=1.5,
        )
        ax[row*2+1].set_title(
            '{} min'.format(region), x=0.01, ha='left', va='top', y=1.0, weight='bold')
    ## Legend
    leg = ax[0].legend(
        loc='upper left', bbox_to_anchor=(1.02,1),
        fontsize=11, frameon=False, ncol=1,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    ax[0].set_ylabel('Generation [GW]', ha='right', y=1)

    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%%### Plot: Osprey storage energy level
savename = 'B1-storage_energy-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    dfplot = stor_energy.cumsum(axis=1)[stor_charge_usa.columns[::-1]]
    plt.close()
    f,ax = plots.plotyearbymonth(
        dfplot, colors=[colors[c] for c in dfplot], dpi=dpi,
    )
    ## Legend
    ax[0].legend(
        loc='upper left', bbox_to_anchor=(1,1.25),
        fontsize=11, frameon=False, ncol=1,
        title='Energy level',
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%%### Plot: Augur C1 curtailment timeseries
savename = 'C1-curtailment-timeseries-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    plt.close()
    ## VRE gen
    f,ax = plots.plotyearbymonth(
        vre_gen_usa.cumsum(axis=1)[vre_gen_usa.columns[::-1]],
        colors=[colors[c] for c in vre_gen_usa.columns[::-1]],
        dpi=dpi, alpha=1,
    )
    ## Wash it out
    plots.plotyearbymonth(
        vre_gen_usa.sum(axis=1).rename('_nolabel_').to_frame(),
        f=f, ax=ax, colors=['w'], alpha=0.4,
    )
    ## Curtailment
    plots.plotyearbymonth(
        curtailment.sum(axis=1).rename('curtailment').to_frame(),
        f=f, ax=ax, colors=['k'],
    )
    ## Legend
    ax[0].legend(
        loc='upper left', bbox_to_anchor=(1,1.25),
        fontsize=11, frameon=False, ncol=1,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%%### Plot: Load, net load, curtailment
savename = 'C1-load_netload_curtailment-profile-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    MWperTW = 1e6
    dfpos = net_load_usa.clip(lower=0)
    dfneg = net_load_usa.clip(upper=0)
    plt.close()
    f,ax = plt.subplots(figsize=(10,3.75))
    ### Load
    (load_usa/MWperTW).plot(
        ax=ax, color='k', lw=0.25, label='End-use electricity demand')
    ### Net load including storage dispatch
    ((net_load_usa - gen_usa[stortechs].sum(axis=1)).clip(lower=0)/MWperTW).plot.area(
        ax=ax, color='C3', lw=0, label='Demand – (VRE + storage)')
    ### Curtailment
    (-curtailment.sum(axis=1)/MWperTW).plot.area(
        ax=ax, color='C0', lw=0, label='Curtailment')
    ax.axhline(0,c='k',ls=':',lw=0.5)
    ax.set_ylim(-curtailment.sum(axis=1).max()/MWperTW, load_usa.max()/MWperTW)
    ax.legend(
        frameon=False,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.75,
    )
    ax.set_ylabel('TW (national total)')
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()
except Exception as err:
    failed_plots.append((savename,err))



#%%### Plot: Augur C1 curtailment duration curve
savename = 'C1-curtailment-duration-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    sorted_index = curtailment.sum(axis=1).sort_values(ascending=False).index
    dfplot = (
        vre_gen_usa.cumsum(axis=1)[vre_gen_usa.columns[::-1]]
        .loc[sorted_index]
        .set_index(np.linspace(0,100,len(vre_gen_usa)))
        / 1000
    )
    curtailment_plot = curtailment.sum(axis=1).loc[sorted_index].copy()
    curtailment_plot.loc[curtailment_plot==0] = np.nan
    plt.close()
    f,ax = plt.subplots(figsize=(7,3.75), dpi=dpi)
    ## Generation
    dfplot.plot.area(ax=ax, color=colors, lw=0, stacked=False, alpha=1)
    ## Wash it out
    dfplot.sum(axis=1).plot.area(ax=ax, color='w', lw=0, alpha=0.3)
    ## Curtailment
    ax.plot(
        np.linspace(0,100,len(load_usa)),
        curtailment_plot.values / 1000,
        c='k', ls='-', lw=2, label='curtailment', solid_capstyle='butt')
    ## Mark the extrema
    ax.plot(
        [0], [curtailment_plot.max()/1000],
        lw=0, marker=1, ms=5, c='k',)
    ax.plot(
        [(curtailment_plot.fillna(0)>0).sum()/len(load_usa)*100], [0],
        lw=0, marker=2, ms=5, c='k',)
    ## Formatting
    ax.set_ylabel('Generation [GW]')
    ax.set_xlabel('Percent of year [%]')
    ax.set_xlim(0,100)
    # ax.set_xlim(0,(curtailment_plot>0).sum()/len(curtailment)*100)
    ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(4))
    ax.legend(
        loc='center left', bbox_to_anchor=(1,0.5),
        fontsize=11, frameon=False, ncol=1,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.75,
    )
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%%### Plot: Osprey dropped load timeseries
savename = 'B1-dropped_load-timeseries-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    plt.close()
    ## Load
    f,ax = plots.plotyearbymonth(
        load_usa.to_frame(), colors=['0.8'], dpi=dpi
    )
    ## Dropped load
    plots.plotyearbymonth(
        dropped_load.rename('Dropped').to_frame(),
        f=f, ax=ax, colors=['C3'], dpi=dpi,
    )
    ## Legend
    ax[0].legend(
        loc='upper left', bbox_to_anchor=(1,1.25),
        fontsize=11, frameon=False, ncol=1,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%%### Plot: Osprey dropped load duration
savename = 'B1-dropped_load-duration-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    plt.close()
    f,ax = plt.subplots(dpi=dpi)
    ## Load
    ax.fill_between(
        np.linspace(0,100,len(load_usa)),
        load_usa.sort_values(ascending=False).values / 1000,
        color='0.8', lw=0, label='Demand',
    )
    ## Dropped load
    ax.fill_between(
        np.linspace(0,100,len(load_usa)),
        dropped_load.rename('Dropped').sort_values(ascending=False).values / 1000,
        color='C3', lw=0, label='Dropped',
    )
    ## Mark the extrema
    ax.plot(
        [0], [dropped_load.max()/1000],
        lw=0, marker=1, ms=5, c='C3',)
    ax.plot(
        [(dropped_load>0).sum()/len(load_usa)*100], [0],
        lw=0, marker=2, ms=5, c='C3',)
    ## Formatting
    ax.set_ylabel('Demand [GW]')
    ax.set_xlabel('Percent of year [%]')
    ax.set_xlim(0,(dropped_load>0).sum()/len(load_usa)*100)
    ax.set_ylim(0)
    ax.legend(
        # loc='upper left', bbox_to_anchor=(1,1.25),
        fontsize=11, frameon=False, ncol=1,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%% Plot: Osprey energy prices, pre-startup-cost adder
savename = 'B1-prices-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    #%% Load Osprey prices by BA
    prices = (
        pd.read_csv(
            os.path.join('ReEDS_Augur','augur_data',
                        'prices_{}.csv'.format(Sw['prev_year'])))
        .pivot(index=['d','hr'], columns='r', values='Val')
        .reindex(h_dt_szn.loc[h_dt_szn.year==2007,['d','hr']].values, axis=0)
        .fillna(0)
        .set_index(timeindex)
    )
    ### Plot it
    plt.close()
    f,ax = plots.plotyearbymonth(
        prices, style='line', lwforline='0.25', dpi=dpi,
    )
    ax[0].set_title(
        '{} ({}) (y = {:.0f}–{:.0f} $/MWh)'.format(
            Sw['scen'], Sw['prev_year'],
            prices.min().min(), prices.max().max()))
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%% Plot: Osprey energy price duration, pre-startup-cost adder
savename = 'B1-price_duration-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    plt.close()
    f,ax = plt.subplots(dpi=dpi)
    for r in prices:
        ax.plot(
            np.linspace(0,100,len(prices)),
            prices[r].sort_values(ascending=False).values,
            label=r, lw=0.5,
        )
    ax.set_ylabel('Osprey price [2004$/MWh]')
    ax.set_xlabel('Percent of year [%]')
    ax.set_title('{} ({})'.format(Sw['scen'], Sw['prev_year']))
    ax.set_xlim(0,100)
    ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(5))
    ax.axhline(0,c='0.5',lw=0.5,ls='--')
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%% Plot: Condor energy prices, post-startup-cost adder
savename = 'D-prices-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    ### Load prices with startup cost adder (used in Condor)
    prices_condor = (
        pd.read_hdf(
            os.path.join('ReEDS_Augur','augur_data',
                        'plot_prices_condor_{}.h5'.format(Sw['prev_year'])))
        .reindex(range(Sw['osprey_ts_length']))
        .fillna(0)
        .set_index(timeindex)
    )
    ### Plot it
    plt.close()
    f,ax = plots.plotyearbymonth(
        prices_condor, style='line', lwforline='0.25', dpi=dpi,
    )
    ax[0].set_title(
        '{} ({}) (y = {:.0f}–{:.0f} $/MWh)'.format(
            Sw['scen'], Sw['prev_year'], *ax[0].get_ylim()))
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%% Plot: Condor energy price duration, post-startup-cost adder
savename = 'D-price_duration-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    plt.close()
    f,ax = plt.subplots(dpi=dpi)
    for r in prices_condor:
        ax.plot(
            np.linspace(0,100,len(prices)),
            prices[r].sort_values(ascending=False).values,
            label=r, lw=0.5,
        )
    ax.set_ylabel('Osprey price [2004$/MWh]')
    ax.set_xlabel('Percent of year [%]')
    ax.set_title('{} ({})'.format(Sw['scen'], Sw['prev_year']))
    ax.set_xlim(0,100)
    ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(5))
    ax.axhline(0,c='0.5',lw=0.5,ls='--')
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%% Plot: CO2 emissions
savename = 'B1-CO2emissions-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    ###### Load the data
    emit_rate = pd.read_csv(
        os.path.join('ReEDS_Augur','augur_data','emit_rate_{}.csv'.format(Sw['prev_year']))
    ) ### ton/MWh
    emit_rate = (
        emit_rate
        .loc[emit_rate.e=='CO2'].drop(['e'],axis=1)
        .set_index(['i','v','r'])
        .emit_rate
    )

    co2_emissions = (
        gen
        .set_index(['d','hr','i','v','r'])
        .unstack(['i','v','r']).fillna(0)
        .loc[h_dt_szn.loc[h_dt_szn.year==2007,['d','hr']].values.tolist()]
        .set_index(timeindex)['Val']
        # .T
        * emit_rate
    ).dropna(axis=1, how='all').sum(axis=1,level='i')

    negcols = co2_emissions.sum().loc[co2_emissions.sum() < 0].index.values
    poscols = [c for c in co2_emissions if c not in negcols]
    df = co2_emissions.sum(axis=1).cumsum()/1E6

    ###### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(12,3.75))
    # ax.fill_between(df.index, df.values)
    df.plot(ax=ax, color='C5', zorder=6, label='Cumulative [MT]')
    ax.fill_between(
        df.index, (co2_emissions[poscols].sum(axis=1).values/1E3),
        color='C1', lw=0, label='Hourly, positive [kT]',
    )
    ax.fill_between(
        df.index, (co2_emissions[negcols].sum(axis=1).values/1E3),
        color='C0', lw=0, label='Hourly, negative [kT]',
    )
    # (co2_emissions[poscols].sum(axis=1)/1E3).plot(
    #     ax=ax, color='C3', lw=0.5, zorder=4, label='Hourly, positive [kT]')
    # (co2_emissions[negcols].sum(axis=1)/1E3).plot(
    #     ax=ax, color='C0', lw=0.5, zorder=3, label='Hourly, negative [kT]')
    ax.legend(frameon=False, handletextpad=0.5, handlelength=0.7, fontsize='large')
    ax.axhline(0,c='k',lw=0.75,ls='-',zorder=5)
    ax.set_ylabel('CO2 emissions')
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%% Plot: Osprey merit order curve
savename = 'A-meritorder-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    avail_cap_d = (
        pd.read_csv(os.path.join(
            'ReEDS_Augur','augur_data',
            'avail_cap_d_{}.csv'.format(Sw['prev_year'])))
        .set_index(['i','v','r'])
        [day]
    )

    ### Load gen cost
    gen_cost = gdxpds.to_dataframe(
        os.path.join('ReEDS_Augur','augur_data',
                    'osprey_inputs_{}.gdx'.format(Sw['prev_year'])),
        'gen_cost')['gen_cost']
    gen_cost_cap = gen_cost.merge(
        avail_cap_d.rename('cap').to_frame(),
        left_on=['i','v','r'], right_index=True,
        # how='outer',
        how='left',
    )
    ### The only missing costs are for pumped hydro
    ### But actually we probably shouldn't do any value-filling, since
    ### Osprey uses these (i,v,r) directly
    gen_cost_cap = gen_cost_cap.fillna(0)
    costcolors = {
        **tech_map.map(tech_style).to_dict(),
        **colors,
    }
    gen_cost_cap['color'] = gen_cost_cap.i.map(costcolors)
    gen_cost_cap = gen_cost_cap.sort_values('Value')

    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(7,3.75), dpi=dpi)
    ax.scatter(
        gen_cost_cap.cap.cumsum().values / 1000,
        gen_cost_cap.Value.values,
        color=gen_cost_cap.color.values,
        s=5,
    )
    # ax.bar(
    #     x=gen_cost_cap.cap.cumsum().values / 1000,
    #     height=gen_cost_cap.Value.values,
    #     width=gen_cost_cap.cap.values / 1000 + 1,
    #     color=gen_cost_cap.color.values,
    # )
    ax.set_ylabel('Cost [2004$/MWh]')
    ax.set_xlabel('Cumulative capacity [GW')
    ax.set_xlim(0)
    ax.set_ylim(0)
    ax.set_title('{} ({}) {}'.format(Sw['scen'], Sw['prev_year'], day))
    ## Legend
    handles = [
        mpl.patches.Patch(facecolor=costcolors[i], edgecolor='none', label=i)
        for i in costcolors if i in gen_cost_cap.i.unique()
    ]
    ax.legend(
        handles=handles, loc='upper left', frameon=False,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        ncol=3,
    )
    plots.despine(ax, right=True)

    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%% Plot: Marginal capacity credit
param = 'cc_mar'
savename = 'E-{}-{}-{}.png'.format(param,Sw['scen'],Sw['prev_year'])
try:
    cc_results = gdxpds.to_dataframes(os.path.join(
        'ReEDS_Augur','augur_data',
        'ReEDS_Augur_{}.gdx'.format(Sw['prev_year'])
    ))

    dfplot = cc_results[param].drop('t',axis=1).copy()
    dfplot['tech'] = dfplot.i.map(lambda x: x.split('_')[0])
    techs = sorted(dfplot.tech.unique())
    numrows = len(techs)
    bootstrap = 5
    squeeze = 0.7
    ### Use seasons appropriate to resolution
    if 'wint' in dfplot.szn.values:
        seasons = ['wint','spri','summ','fall']
        histcolor = ['C0','C2','C1','C3']
        xticklabels = seasons
    else:
        seasons = [f'szn{s}' for s in sorted(dfplot.szn.str.strip('szn').astype(int).unique())]
        histcolor = plots.rainbowmapper(seasons)
        xticklabels = [s.strip('szn') for s in seasons]

    plt.close()
    f,ax = plt.subplots(numrows, figsize=(6,8), sharex=True, sharey=True)
    for row, tech in enumerate(techs):
        df = dfplot.loc[(dfplot.tech==tech)].copy()
        ### Each observation in the histogram is a (i,r) pair
        df['i_r'] = df.i + '_' + df.r
        df = df.pivot(columns='szn',values='Value',index='i_r')[seasons]

        plots.plotquarthist(
            ax[row], df, histcolor=histcolor,
            bootstrap=bootstrap, density=True, squeeze=squeeze,
            pad=0.03,
        )

        ### Formatting
        ax[row].set_ylabel(tech)
        ax[row].yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1))
        ax[row].yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5))
        ax[row].set_ylim(0,1)

    ax[0].set_title('{} ({}) {}'.format(Sw['scen'], Sw['prev_year'], param),
                    weight='bold', fontsize='x-large')
    ax[-1].set_xticklabels(xticklabels)

    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%% Plot: Marginal curtailment
param = 'curt_marg'
savename = 'C2-{}-{}-{}.png'.format(param,Sw['scen'],Sw['prev_year'])
try:
    cc_results = gdxpds.to_dataframes(os.path.join(
        'ReEDS_Augur','augur_data',
        'ReEDS_Augur_{}.gdx'.format(Sw['prev_year'])
    ))

    dfplot = cc_results[param].drop('t',axis=1).copy()
    dfplot['tech'] = dfplot.i.map(lambda x: x.split('_')[0])
    techs = sorted(dfplot.tech.unique())
    numrows = len(techs)
    bootstrap = 50
    squeeze = 0.7
    ### h17 isn't included
    hs = ['h{}'.format(i+1) for i in range(16)]
    # import cmocean
    # hcolors = plots.rainbowmapper(hs, cmocean.cm.phase)
    # hcolors = dict(zip(hs, [plt.cm.tab20c(i) for i in range(len(hs))]))
    ### (h1*h4,h17).summ, (h5*h8).fall, (h9*h12).wint, (h13*h16).spri
    hcolors = dict(zip(hs, ['C1']*4 + ['C3']*4 + ['C0']*4 + ['C2']*4))

    plt.close()
    f,ax = plt.subplots(numrows, figsize=(8,8), sharex=True, sharey=True)
    for row, tech in enumerate(techs):
        df = dfplot.loc[(dfplot.tech==tech)].copy()
        ### Each observation in the histogram is a (i,r) pair
        df['i_r'] = df.i + '_' + df.r
        df = df.pivot(columns='h',values='Value',index='i_r')[hs]

        plots.plotquarthist(
            ax[row], df, histcolor=[hcolors[h] for h in hs],
            bootstrap=bootstrap, density=True, squeeze=squeeze,
            pad=0.03,
        )

        ### Formatting
        ax[row].set_ylabel(tech)
        ax[row].yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1))
        ax[row].yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5))
        ax[row].set_ylim(0,1)

    ax[0].set_title('{} ({}) {}'.format(Sw['scen'], Sw['prev_year'], param),
                    weight='bold', fontsize='x-large')

    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))



#%%### Plot: Peak net load hours by ccreg
savename = 'E-netloadhours-timeseries-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    ### Get top load hours by season
    hour2datetime = h_dt_szn.set_index('hour').datetime.copy()
    ### Use seasons appropriate to resolution
    seasons = net_load_ccreg.index.get_level_values('season').unique()
    if 'fall' in seasons:
        seasons = ['winter','spring','summer','fall']
        histcolor = ['C0','C2','C1','C3']
        xticklabels = seasons
    elif 'winter' in seasons:
        seasons = ['winter','spring','summer','fall']
        histcolor = ['C0','C2','C1','C3']
        xticklabels = seasons
    else:
        seasons = [f'szn{s}' for s in sorted([int(s.strip('szn')) for s in seasons])]
        histcolor = plots.rainbowmapper(seasons)
        xticklabels = [s.strip('szn') for s in seasons]
    ccregs = sorted(net_load_ccreg.columns)
    peakhours = {}
    for season in seasons:
        for ccreg in ccregs:
            peakhours[season,ccreg] = (
                net_load_ccreg.loc[season][ccreg]
                .nlargest(capcredit_szn_hours).index.get_level_values('hour'))

    dfpeak = (
        pd.DataFrame(peakhours)
        .stack(level=0)
        .reorder_levels([1,0], axis=0)
        .stack().map(hour2datetime).rename('datetime').to_frame()
        .assign(peak=1)
        .reset_index(level=2).rename(columns={'level_2':'ccreg'})
        .pivot(index='datetime', columns='ccreg', values='peak')
        .reindex(fulltimeindex)
        .fillna(0).astype(int)
    )
    ### Plot it
    years = range(2007,2014)
    peakcolors = plots.rainbowmapper(ccregs, plt.cm.tab20)
    plt.close()
    f,ax = plt.subplots(len(years),1,sharex=True,sharey=True,figsize=(12,6))
    for row, year in enumerate(years):
        df = dfpeak.loc[str(year)].set_index(timeindex).cumsum(axis=1)[ccregs[::-1]]
        df.plot.area(
            ax=ax[row], color=peakcolors, stacked=False, alpha=1,
            legend=False,
        )
        ax[row].annotate(
            year,(0.005,0.95),xycoords='axes fraction',ha='left',va='top',
            weight='bold',fontsize='large')
        # ax[row].xaxis.set_major_locator(mpl.dates.MonthLocator())
        # ax[row].set_xticklabels([])
    h,l = ax[0].get_legend_handles_labels()
    ax[0].legend(
        h[::-1], l[::-1],
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        loc='upper left', bbox_to_anchor=(1,1), frameon=False, title='ccreg',
    )
    ax[3].set_ylabel('Net load peak instances [#]')
    # ax[-1].xaxis.set_major_locator(mpl.dates.MonthLocator())
    # ax[-1].xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))




#%%### Plot: histograms of peak net load occurrence
savename = 'E-netloadhours-histogram-{}-{}.png'.format(Sw['scen'],Sw['prev_year'])
try:
    ### Plot it
    plt.close()
    f,ax = plt.subplots(1,3,figsize=(12,3.75))
    ### hour
    dfpeak.groupby(dfpeak.index.hour).sum()[ccregs[::-1]].plot.bar(
        ax=ax[0], color=peakcolors, stacked=True, alpha=1,
        width=0.95, legend=False,
    )
    ax[0].set_xlabel('Hour [EST]')
    ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(4))
    ax[0].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))
    ax[0].tick_params(labelrotation=0)
    ### Month
    dfpeak.groupby(dfpeak.index.month).sum()[ccregs[::-1]].plot.bar(
        ax=ax[1], color=peakcolors, stacked=True, alpha=1,
        width=0.95, legend=False,
    )
    ax[1].set_xlabel('Month')
    ax[1].tick_params(labelrotation=0)
    ### Year
    dfpeak.groupby(dfpeak.index.year).sum()[ccregs[::-1]].plot.bar(
        ax=ax[2], color=peakcolors, stacked=True, alpha=1,
        width=0.95, legend=False,
    )
    ax[2].set_xlabel('Year')
    ax[2].set_xticks(range(len(years)))
    ax[2].set_xticklabels(
        years,
        rotation=35, ha='right', rotation_mode='anchor')
    # ax[2].tick_params(labelrotation=45)
    ### Formatting
    h,l = ax[2].get_legend_handles_labels()
    ax[2].legend(
        h[::-1], l[::-1],
        loc='center left', bbox_to_anchor=(1,0.5), frameon=False,
        title=Sw['capcredit_hierarchy_level'],
        ncol=1, columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
    )
    ax[0].set_ylabel('Net peak load instances [#]')
    plots.despine(ax)
    if savefig: plt.savefig(os.path.join(savepath,savename))
    if interactive: plt.show()
    plt.close()

except Exception as err:
    failed_plots.append((savename, err))

### Report any exceptions
if len(failed_plots):
    with open('gamslog.txt', 'a') as f:
        print(
            '\n#########\n'.join(['\n'.join([str(i) for i in c]) for c in failed_plots]),
            file=f)
    raise Exception('{} failed plots'.format(len(failed_plots)))
