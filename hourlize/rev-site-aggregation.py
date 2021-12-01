"""
Patrick.Brown@nrel.gov 20210520
"""

###############
#%% IMPORTS ###
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
import geopandas as gpd
import shapely
### Set up projection environment - needed for geopandas
os.environ['PROJ_NETWORK'] = 'OFF'
pd.options.display.max_rows = 20
pd.options.display.max_columns = 200

##############
#%% INPUTS ###
### Indicate whether to run for offshore
offshore = True
### Filepaths
if os.name == 'posix':
    scpath = '/Volumes/ReEDS/Supply_Curve_Data/'
else:
    scpath = '//nrelnas01/ReEDS/Supply_Curve_Data/'
### Get the ReEDS-2.0 path from this file's path (ReEDS-2.0/hourlize/rev-site-aggregation.py)
reedspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
outpath = os.path.join(reedspath,'inputs','supplycurvedata')

pvpath = os.path.join(scpath,'UPV','2021_Update','reV','scenarios_aux')
windpath = os.path.join(scpath,'ONSHORE','2021_Update','reV')
offshorepath = os.path.join(scpath,'OFFSHORE','2021_Update','reV')

### Indicate whether to make plots for output investigation
makeplots = True
### Set threshold for distance between x columns and y rows [units: meters]
### Should be a few km less than the rough spacing between reV sites
### (currently 11500 km for onshore)
thresh = 8000
### Aggregation levels (agglevel=2 indicates 2x2 aggregation)
agglevels = list(range(1,11)) + [500]
### reV runs for metadata. Use all scenarios to make sure that we get all sites.
scens = {
    # 'windons_ref': os.path.join(
    #     windpath,'10_reference_moderate_eos_flicker','10_reference_moderate_eos_flicker_sc.csv'),
    # 'windons_lim': os.path.join(
    #     windpath,'11_limited_moderate_eos_flicker','11_limited_moderate_eos_flicker_sc.csv'),
    'windons_open': os.path.join(
        windpath,'08_open_moderate_eos_flicker','08_open_moderate_eos_flicker_sc.csv'),
    # 'upv_ref': os.path.join(
    #     pvpath,'scen_128_ed1','scen_128_ed1_sc.csv'),
    # 'upv_lim': os.path.join(
    #     pvpath,'scen_128_ed4','scen_128_ed4_sc.csv'),
    'upv_open': os.path.join(
        pvpath,'scen_128_ed0','scen_128_ed0_sc.csv'),
}
### For offshore we can use a single open-access scenario
offshorescens = {
    'open': os.path.join(offshorepath,'2_moderate_open','2_moderate_open_sc.csv'),
    'limited': os.path.join(offshorepath,'3_moderate_limited','3_moderate_limited_sc.csv'),
}
### reV projection string
### (https://spatialreference.org/ref/esri/north-america-albers-equal-area-conic/)
projstring = 'ESRI:102008'

#################
#%% PROCEDURE ###

#%% Get ReEDS regions from county map
fipsmap = pd.read_csv(
    os.path.join(reedspath,'hourlize','inputs','resource','county_map.csv'),
)
fipsmap.cnty_fips = fipsmap.cnty_fips.map(lambda x: '{:0>5}'.format(int(x)))
fipsmap = fipsmap.set_index('cnty_fips')

#%% Simpler procedure for offshore
if offshore:
    #%% Get meta for offshore sites
    dictmeta = {}
    for scen in tqdm(offshorescens, desc='load metadata'):
        dictmeta[scen] = pd.read_csv(
            offshorescens[scen],
            low_memory=False, dtype={'sc_point_gid':int},
        )
    dfmeta = (
        pd.concat(dictmeta, axis=0, ignore_index=True)
        .drop_duplicates('sc_point_gid').set_index('sc_point_gid').sort_index())
    dfmeta.cnty_fips = dfmeta.cnty_fips.map(lambda x: '{:0>5}'.format(int(x)))
    #%% Map to ReEDS BAs & resource resgions
    dfmeta['rb'] = dfmeta.cnty_fips.map(fipsmap.reeds_ba)
    dfmeta['rs'] = dfmeta.cnty_fips.map(fipsmap.reeds_region)

    #%% Make the key
    dfkey = dfmeta[['cnty_fips','latitude','longitude','rb']].copy()

### Otherwise use all scenarios
else:
    #%% Get meta for all sites (wind and pv)
    dfmeta = {}
    for scen in tqdm(scens, desc='load metadata'):
        dfmeta[scen] = pd.read_csv(scens[scen], index_col=0, low_memory=False)
    dfmeta = pd.concat(dfmeta, axis=0)
    dfmeta.sc_point_gid = dfmeta.sc_point_gid.astype(int)
    dfmeta.cnty_fips = dfmeta.cnty_fips.map(lambda x: '{:0>5}'.format(int(x)))

    # ###### Make sure they overlap
    # dftest = dfmeta.reset_index(level=0).rename(columns={'level_0':'scen'}).pivot(
    #     index='sc_point_gid', columns='scen', values=['latitude','longitude'])

    # ### Looks ok; largest deviation is 0.0006°. 
    # ### Wind values match each other exactly.
    # ### UPV values match each other within float precision (1E-15).
    # print(dftest['latitude'].T.std().dropna().nlargest(10))
    # print(dftest['latitude'].T.mean().dropna().nlargest(10))
    # print(dftest['longitude'].T.std().dropna().nlargest(10))
    # print(dftest['longitude'].T.mean().dropna().nlargest(10))

    ### Same length
    # print(len(sc_point_gids))
    # print(len(latlon))

    latlon = (
        dfmeta.loc[dfmeta.offshore != 1.]
        .reset_index(level=0).rename(columns={'level_0':'scen'})
        .pivot(
            index='sc_point_gid', columns='scen', 
            values=['latitude','longitude','state','county','cnty_fips'])
    )
    ### Keep wind value if there is one; otherwise use UPV
    sc_point_gids = sorted(latlon.index.unique())
    latitudes, longitudes = {}, {}
    dflat = latlon['latitude'][scens.keys()].copy()
    dflon = latlon['longitude'][scens.keys()].copy()
    dffips = latlon['cnty_fips'][scens.keys()].copy()
    data = {}
    for sc_point_gid in tqdm(sc_point_gids, desc='assign metadata to sites'):
        data['latitude',sc_point_gid] = (
            dflat.loc[sc_point_gid].dropna().drop_duplicates(keep='first').values[0])
        data['longitude',sc_point_gid] = (
            dflon.loc[sc_point_gid].dropna().drop_duplicates(keep='first').values[0])
        data['cnty_fips',sc_point_gid] = (
            dffips.loc[sc_point_gid].dropna().drop_duplicates(keep='first').values[0])
        data['rb',sc_point_gid] = fipsmap.loc[data['cnty_fips',sc_point_gid], 'reeds_ba']
        data['rs',sc_point_gid] = fipsmap.loc[data['cnty_fips',sc_point_gid], 'reeds_region']

    #%% Make the key
    dfkey = (
        pd.Series(data)
        .reset_index().rename(columns={'level_1':'sc_point_gid'})
        .pivot(columns='level_0',index='sc_point_gid',values=0)
    ).drop('rs', axis=1)
    dfkey.columns.name = None

#%% Do the equal-area projection
dfkey['geometry'] = dfkey.apply(
    lambda row: shapely.geometry.Point(row['longitude'],row['latitude']),
    axis=1
)
dfkey = gpd.GeoDataFrame(dfkey).set_crs('EPSG:4326').to_crs(projstring)

dfkey['x'] = dfkey.geometry.x
dfkey['y'] = dfkey.geometry.y

#%%### Sort the reV points into x columns and y rows
### (Need to do so because they aren't on a perfect grid)
### Use the fact that they're sorted
xs = sorted(dfkey.x.values)
ys = sorted(dfkey.y.values)
xbins, ybins = {}, {}

### x
ibin = 0
for i, x in enumerate(xs):
    ### Put the first point in its own bin
    if i == 0:
        xbins[ibin] = [x]
    else:
        ### Get the distance
        distance = x - xs[i-1]
        ### If it's closer than threshold, put in same bin
        if distance < thresh:
            xbins[ibin].append(x)
        ### If it's farther away than threshhold, put it in a new bin
        else:
            ibin += 1
            xbins[ibin] = [x]
### Get the mean locations
xmeans = {i: np.mean(xbins[i]) for i in xbins}

### y
ibin = 0
for i, y in enumerate(ys):
    if i == 0:
        ybins[ibin] = [y]
    else:
        distance = y - ys[i-1]
        if distance < thresh:
            ybins[ibin].append(y)
        else:
            ibin += 1
            ybins[ibin] = [y]
### Get the mean locations
ymeans = {i: np.mean(ybins[i]) for i in ybins}

#%% Make the grid
dfgrid = pd.DataFrame(
    [(x,y) for x in xmeans.values() for y in ymeans.values()],
    columns=['x','y']
)

#%% Aggregate them
df = dfgrid.copy()
df['dummy'] = 1
fullgrid = df.pivot(index='x',columns='y',values='dummy')

for agglevel in agglevels:
    agggrid = fullgrid.copy()

    ### Get the aggregation indices
    agggrid.index = [
        item for sublist in 
        [[i]*agglevel for i in range(fullgrid.shape[0])]
        for item in sublist
    ][:fullgrid.shape[0]]
    agggrid.index.name = 'x_agg{}'.format(agglevel)

    agggrid.columns = [
        item for sublist in 
        [[i]*agglevel for i in range(fullgrid.shape[1])]
        for item in sublist
    ][:fullgrid.shape[1]]
    agggrid.columns.name = 'y_agg{}'.format(agglevel)

    ### Reshape to dfgrid
    agggrid = agggrid.stack().reset_index().drop(0, axis=1)

    agggrid['agg{}'.format(agglevel)] = (
        'x' + agggrid['x_agg{}'.format(agglevel)].astype(str) 
        + 'y' + agggrid['y_agg{}'.format(agglevel)].astype(str)
    )

    ### Append to dfgrid
    dfgrid['agg{}'.format(agglevel)] = agggrid['agg{}'.format(agglevel)].copy()

#%% Merge with actual sites
dfout = dfkey.rename(columns={'x':'x_real','y':'y_real'}).copy()
dfout.reset_index(inplace=True)

xgrid = dfgrid.x.unique()
ygrid = dfgrid.y.unique()

dfout['x_grid'] = dfout.x_real.map(lambda x: xgrid[abs(xgrid - x).argmin()])
dfout['y_grid'] = dfout.y_real.map(lambda y: ygrid[abs(ygrid - y).argmin()])

dfout = dfout.merge(
    dfgrid, left_on=['x_grid','y_grid'], right_on=['x','y'], how='left'
).drop(['x','y'], axis=1)

### Account for BA boundaries in the aggregation
for agglevel in ['agg{}'.format(i) for i in agglevels]:
    ### Just concat names
    dfout['r'+agglevel] = dfout.rb + dfout[agglevel]

#%% Make plots for inspection (optional)
if makeplots:
    #%%### Plot the number of sites per aggregation level
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    df = pd.DataFrame({
        'x': agglevels,
        'y': [len(dfout['ragg{}'.format(agglevel)].unique()) for agglevel in agglevels]
    })

    plt.close()
    f,ax = plt.subplots(dpi=100)
    ax.barh(df.x.astype(str).values, df.y.values)
    ax.set_ylim(10.5,-0.5)
    ax.set_xlim(0)
    ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(1))
    ax.set_xlabel('Number of aggregated sites')
    ax.set_ylabel('n×n aggregation level')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for location, i in enumerate(df.index):
        ax.annotate(
            df.loc[i,'y'],
            (df.loc[i,'y']+1000, location),
            # (df.loc[i,'y']*1.1, location), ### for log plot
            va='center', fontsize=12
        )
    plt.show()

    #%%### Plot the resulting aggregation levels
    ### Load BA map
    dfba = gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','US_PCA'))

    ### Plot it
    for agglevel in agglevels:
        labelcol = 'ragg{}'.format(agglevel)

        colors = {}
        for label in dfout[labelcol].unique():
            r = int(label.split('x')[0].lstrip('p'))
            colorbase = (r%10)*2
            ### Special cases
            if r in [5,26]:
                colorbase=0
            if r in [60]:
                colorbase = 8
            if r in [76]:
                colorbase = 4
            if r in [70,101]:
                colorbase = 6
            if r in [61,71]:
                colorbase = 12
            if r in [85]:
                colorbase = 18

            x = int(label.split('y')[0].split('x')[1])
            y = int(label.split('y')[1])
            if ((x%2==0) and (y%2==0)) or ((x%2==1) and (y%2==1)):
                coloradder = 1
            else:
                coloradder = 0

            colors[label] = plt.cm.tab20(colorbase+coloradder)

        dfplot = dfout.copy()
        dfplot['color'] = dfplot[labelcol].map(colors)

        plt.close()
        f,ax = plt.subplots(figsize=(16,16), dpi=100)
        ax.scatter(
            dfplot.x_real.values, dfplot.y_real.values, c=dfplot.color.values,
            lw=0, marker='s', s=5,
        )
        ### BA boundaries
        dfba.plot(ax=ax, edgecolor='k', facecolor='none', lw=0.5)
        ax.set_aspect('equal')
        ax.axis('off')
        plt.show()

#%%### Write it
dfwrite = (
    dfout
    .drop(['agg{}'.format(i) for i in agglevels]+['geometry','x_grid','y_grid',], axis=1)
    .rename(columns={
        'x_real':'x', 'y_real':'y', 'ragg500':'raggBA',
    })
).set_index('sc_point_gid')

dfwrite.x = dfwrite.x.astype(int)
dfwrite.y = dfwrite.y.astype(int)
dfwrite.latitude = dfwrite.latitude.astype(float).round(4)
dfwrite.longitude = dfwrite.longitude.astype(float).round(4)
### Save it
dfwrite.to_csv(os.path.join(outpath,'sitemap{}.csv'.format('_offshore' if offshore else '')))
