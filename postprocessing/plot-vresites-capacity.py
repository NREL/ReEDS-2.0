###############
#%% IMPORTS ###
import sys, os, site, math, time
import gdxpds
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import geopandas as gpd
import shapely

import plots
plots.plotparams()

os.environ['PROJ_NETWORK'] = 'OFF'
pd.options.display.max_rows = 20
pd.options.display.max_columns = 200

reedspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

###########################
#%% USER-DEFINED INPUTS ###

# revpath = os.path.expanduser('~/Projects/reV/Supply_Curve_Data/')
revpath = ('/Volumes/ReEDS/Supply_Curve_Data/')
runspath = '/Volumes/ReEDS/Users/pbrown/ReEDSruns/20210820_PBdecarbsites/'
case = 'v20210820_PBdecarbsitesD0_AllOptions'
savepath = os.path.expanduser('~/scratch/')

year = 2035
cm = {'wind-ons':plt.cm.gist_earth_r, 'upv':plt.cm.gist_earth_r}
colors = {'wind-ons':'C0', 'upv':'C1'}
alpha = 0.8
### reV default: 'ESRI:102008'
projout = (
    '+proj=aea +lat_0=37.5 +lon_0=-96 +lat_1=29.5 +lat_2=45.5 +x_0=0 +y_0=0 '
    '+ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs')
save_shapefile = False

#####################
#%% STATIC INPUTS ###
### Capacity density
mwperkm2 = {'wind-ons':3, 'upv':32}
### Generator-interconnection ratio (ILR for PV)
gir = {'wind-ons':1, 'upv':1.3}
### Fraction of supply-curve area that is direclty used (only for scale bar)
directusefrac = {'wind-ons':0.03, 'upv':0.9}

#################
#%% PROCEDURE ###

#%% Load site map
sitemap = pd.read_csv(
    os.path.join(reedspath,'inputs','supplycurvedata','sitemap.csv'),
    index_col='sc_point_gid'
)
sitemap['geometry'] = sitemap.apply(
    lambda row: shapely.geometry.Point(row.longitude, row.latitude),
    axis=1)
sitemap = gpd.GeoDataFrame(sitemap).set_crs('EPSG:4326').to_crs('ESRI:102008')

sitemap.index = 'i' + sitemap.index.astype(str)

#%% Load BA map
dfba = gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','US_PCA')).set_index('rb')
### Aggregate to states
dfstates = dfba.dissolve('st')

#%%### Load ReEDS results
### case-specific settings
switches = []
with open(os.path.join(runspath,case,'gamslog.txt'), 'r') as f:
    for l in f:
        if l.startswith('    --'):
            switches.append(l.strip().strip('--').split())
switches = (
    pd.DataFrame(switches, columns=['switch','value'])
    .drop_duplicates()
    .set_index('switch').value
    .drop(['next_year','cur_year'])
)

#%% Load supply curves with sc_point_gid
sc = {}
for tech in ['upv','wind-ons']:
    sc[tech] = pd.read_csv(
        os.path.join(
            reedspath,'inputs','supplycurvedata',
            '{}_supply_curve_{}1300bin-{}.csv'.format(
                tech,
                'sreg' if tech == 'wind-ons' else '',
                switches['GSw_SitingWindOns'] if tech == 'wind-ons' else switches['GSw_SitingUPV'],
            )
        )
    ).rename(columns={'region':'r'})
    sc[tech]['bin'] = 'bin' + sc[tech]['bin'].astype(str)
    sc[tech]['sc_point_gid'] = 'i' + sc[tech]['sc_point_gid'].astype(str)
sc = pd.concat(sc).reset_index().rename(columns={'level_0':'tech'}).drop('level_1', axis=1)
### Merge with geographic information
sc = gpd.GeoDataFrame(
    sc.merge(sitemap[['latitude','longitude','geometry']],
             left_on='sc_point_gid', right_index=True, how='left'))

#%% Load ReEDS outputs
cap_new_bin_out = pd.read_csv(
    os.path.join(runspath,case,'outputs','cap_new_bin_out.csv'),
    header=0,
    names=['i','v','r','t','bin','MW'],
    dtype={'t':int},
)
### Sum over vintages and years (since cap_new_bin_out records investment)
cap = (
    cap_new_bin_out.loc[cap_new_bin_out.t<=year]
    .groupby(['i','r','bin'], as_index=False).MW.sum())

### Only keep wind and UPV
cap = cap.loc[
    cap.i.str.startswith('wind-ons')
    | cap.i.str.startswith('upv')
].copy()
cap['tech'] = cap.i.map(lambda x: x.split('_')[0])
cap['class'] = cap.i.map(lambda x: int(x.split('_')[1]))

cap = gpd.GeoDataFrame(
    cap.merge(
        sc[['tech','r','class','bin','sc_point_gid','dist_mi',
            'supply_curve_cost_per_mw','geometry']],
        on=['tech','r','class','bin'], how='left',
    )
)

#############
#%% PLOTS ###

#%%### Plot #1: Deployed capacity
if 'ERCOT' in case:
    bounds = dfstates.loc['tx','geometry'].bounds
    ms = 6
else:
    bounds = [None]*4
    ms = 1.2

### Plot it
for tech in cm:
    legend_kwds = {
        'shrink':0.5, 'pad':0.05,
        'label':'{} {} capacity [MW]'.format(year, tech),
        'orientation':'horizontal',
    }
    dfplot = cap.loc[(cap.tech==tech)].copy()

    plt.close()
    f,ax = plt.subplots(figsize=(8,8), dpi=150)
    dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=0.1, zorder=100000)
    dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.25, zorder=100001)
    dfplot.plot(
        ax=ax, column='MW', cmap=cm[tech],
        marker='s', markersize=ms, lw=0,
        legend=False, legend_kwds=legend_kwds,
        vmin=0,
    )

    plots.addcolorbarhist(
        f=f, ax0=ax, data=dfplot.MW.values, title=legend_kwds['label'], cmap=cm[tech],
        vmin=0., vmax=dfplot.MW.max(),
        orientation='horizontal', labelpad=2.25, cbarbottom=-0.06,
        cbarheight=0.5,
    )

    ax.set_title('{} ({})'.format(case,year), y=0.95)
    ax.axis('off')
    ax.set_xlim(bounds[0],bounds[2])
    ax.set_ylim(bounds[1],bounds[3])

    plt.show()


#%%### Plot #2: Site utilization
if 'ERCOT' in case:
    bounds = dfstates.loc['tx','geometry'].bounds
    ms = 6
else:
    bounds = [None]*4
    ms = 1.2

### Plot it
for tech in cm:
    legend_kwds = {
        'shrink':0.5, 'pad':0.05,
        'label':'{} {} site utilization [frac.]'.format(year, tech),
        'orientation':'horizontal',
    }
    dfplot = cap.loc[(cap.tech==tech)].set_index('sc_point_gid').copy()
    dfplot['fraction_used'] = (
        dfplot.MW
        / sc.loc[sc.tech==tech].set_index('sc_point_gid').capacity
    ) * gir[tech]
    dfplot = dfplot.dropna().reset_index()

    plt.close()
    f,ax = plt.subplots(figsize=(8,8), dpi=150)
    dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=0.1, zorder=100000)
    dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.25, zorder=100001)
    dfplot.plot(
        ax=ax, column='fraction_used', cmap=cm[tech],
        marker='s', markersize=ms, lw=0,
        legend=False, legend_kwds=legend_kwds,
        vmin=0., vmax=1.,
    )

    plots.addcolorbarhist(
        f=f, ax0=ax, data=dfplot.fraction_used.values,
        title=legend_kwds['label'], cmap=cm[tech],
        vmin=0., vmax=1.,
        orientation='horizontal', labelpad=2.25, cbarbottom=-0.06,
        cbarheight=0.5, log=False,
    )

    ax.set_title('{} ({})'.format(case,year), y=0.95)
    ax.axis('off')
    ax.set_xlim(bounds[0],bounds[2])
    ax.set_ylim(bounds[1],bounds[3])

    plt.show()

#%%### Plot #3: Land usage
### Create GeoDataFrame with polygons for each site
dfwrite = cap.copy()

dfwrite['km2_spacing'] = dfwrite.apply(
    lambda row: row.MW / mwperkm2[row.tech], axis=1)

dfwrite['km2_direct'] = dfwrite.km2_spacing * dfwrite.tech.map(directusefrac)

### Add "both" category
shared_sites = dfwrite.pivot(index='sc_point_gid', columns='tech', values='km2_spacing').dropna()
shared_sites['both'] = shared_sites[['upv','wind-ons']].min(axis=1)

shared_sites = (
    shared_sites[['both']].reset_index()
    .melt(id_vars=['sc_point_gid'], value_name='km2_spacing')
    .set_index('sc_point_gid').km2_spacing
)
append = (
    cap.drop_duplicates('sc_point_gid')
    .set_index('sc_point_gid').loc[shared_sites.index.values]
    .reset_index()
    .assign(tech='both')
    .drop(['i','r','bin','MW','class','dist_mi','supply_curve_cost_per_mw'],axis=1)
    
)
append['km2_spacing'] = append.sc_point_gid.map(shared_sites)

dfwrite = dfwrite.append(append).reset_index(drop=True)

### Create a square for each site corresponding to the area used
dfwrite['geometry'] = dfwrite.apply(
    lambda row: row['geometry'].buffer((row['km2_spacing']**0.5)*1000/2, 1).envelope,
    axis=1
)
### Save as a shapefile (optional)
if save_shapefile:
    savename = '{}_{}_polygons'.format(case,year)
    dfwrite.to_crs(projout).to_file(os.path.join(savepath, savename))

### Plot it
if 'ERCOT' in case:
    bounds = dfstates.loc['tx','geometry'].bounds
    ms = 6
else:
    bounds = [None]*4
    ms = 1.2

centers = {'wind-ons': (-2.0e6,-1.2e6), 'upv':(-1.1e6, -1.2e6)}

plt.close()
f,ax = plt.subplots(figsize=(8,8), dpi=300)
dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=0.1, zorder=100000)
dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.25, zorder=100001)
for tech in cm:
    legend_kwds = {
        'shrink':0.5, 'pad':0.05,
        'label':'{} {} land usage [km^2]'.format(year, tech),
        'orientation':'horizontal',
    }
    dfplot = dfwrite.loc[(dfwrite.tech==tech)].copy()
    dfplot['area'] = dfplot.MW / mwperkm2[tech]

    dfplot.plot(
        ax=ax, color=colors[tech], alpha=alpha,
        lw=0, legend=False, legend_kwds=legend_kwds,
    )

    ### Add aggregated boxes showing total usage
    center = centers[tech]
    area = dfplot.area.sum()/1e6 # km^2
    width = np.sqrt(area) * 1000 # meters
    polygon = gpd.GeoSeries(shapely.geometry.Polygon([
        [center[0] - width/2, center[1] + width/2],
        [center[0] + width/2, center[1] + width/2],
        [center[0] + width/2, center[1] - width/2],
        [center[0] - width/2, center[1] - width/2],
        [center[0] - width/2, center[1] + width/2],
    ]))
    
    polygon.plot(ax=ax, color=colors[tech], alpha=alpha-0.2)

    ### Add another box showing direct usage
    area = dfplot.area.sum()/1e6 * directusefrac[tech] # km^2
    width = np.sqrt(area) * 1000 # meters
    polygon = gpd.GeoSeries(shapely.geometry.Polygon([
        [center[0] - width/2, center[1] + width/2],
        [center[0] + width/2, center[1] + width/2],
        [center[0] + width/2, center[1] - width/2],
        [center[0] - width/2, center[1] - width/2],
        [center[0] - width/2, center[1] + width/2],
    ]))

    polygon.plot(
        ax=ax, color=colors[tech], alpha=1,
    )
    ax.annotate(
        '{}\n{:.0f},000 km$^2$ total\n{:.0f},000 km$^2$ direct'.format(
            tech, area / directusefrac[tech] / 1000, area / 1000),
        (center[0], center[1] - 1.1e5 - (0.6e5 if tech == 'upv' else 0)),
        color='k', ha='center', va='top', fontsize=7,
    )

# ax.set_ylim(0.0e6,1.0e6)
# ax.set_xlim(0.5e6,1.5e6)

ax.set_title('{} ({})'.format(case,year), y=0.95)
ax.axis('off')
ax.set_xlim(bounds[0],bounds[2])
ax.set_ylim(bounds[1],bounds[3])
plt.show()
