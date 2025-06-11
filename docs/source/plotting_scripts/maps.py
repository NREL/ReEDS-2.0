### Use the dlr4 environment

#%% Imports
import os
import sys
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import geopandas as gpd
import mapclassify

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
import reeds
from reeds import plots

plots.plotparams()

reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


#%% Fixed inputs
interactive = False
write = 'png'
date = datetime.datetime.now().strftime('%Y%m%d')
savepath = os.path.expanduser(f'~/Projects/ReEDS/figures/{date}')
os.makedirs(savepath, exist_ok=True)


#%% Shared data
dfmap = reeds.io.get_dfmap()

dfcounty = gpd.read_file(
    os.path.join(reeds_path, 'inputs', 'shapefiles', 'US_county_2022'),
).simplify(1000)
greatlakes = gpd.read_file(
    os.path.join(reeds_path, 'inputs', 'shapefiles', 'greatlakes.gpkg'),
)


#%% Region hierarchy
cm = plt.cm.tab20
cm2 = plt.cm.tab20c
c = {'r':cm(7), 'g':cm(5), 'b':cm(1), 'y':cm(3)}
cmap = {
    'transreg': {
        'CAISO':plt.cm.tab20(3),
        'NorthernGrid':plt.cm.tab20(1),
        'WestConnect':plt.cm.tab20(5),
        'SPP':plt.cm.tab20(3),
        'MISO':plt.cm.tab20(5),
        'ERCOT':plt.cm.tab20(1),
        'PJM':plt.cm.tab20(3),
        'SERTP':plt.cm.tab20(1),
        'FRCC':plt.cm.tab20(5),
        'NYISO':plt.cm.tab20(1),
        'ISONE':plt.cm.tab20(5),
    },
    'transgrp': {
        'CAISO':plt.cm.tab20c(6),
        'NorthernGrid_West':plt.cm.tab20c(1),
        'NorthernGrid_East':plt.cm.tab20c(2),
        'NorthernGrid_South':plt.cm.tab20c(3),
        'WestConnect_North':plt.cm.tab20c(9),
        'WestConnect_South':plt.cm.tab20c(10),
        'SPP_North':plt.cm.tab20c(5),
        'SPP_South':plt.cm.tab20c(6),
        'MISO_North':plt.cm.tab20c(9),
        'MISO_Central':plt.cm.tab20c(10),
        'MISO_South':plt.cm.tab20c(11),
        'ERCOT':plt.cm.tab20c(2),
        'PJM_West':plt.cm.tab20c(5),
        'PJM_East':plt.cm.tab20c(6),
        'SERTP':plt.cm.tab20c(2),
        'FRCC':plt.cm.tab20c(10),
        'NYISO':plt.cm.tab20c(2),
        'ISONE':plt.cm.tab20c(10),
    },
    'st': {
        'WA':c['b'], 'OR':c['y'], 'CA':c['b'], 'ID':c['r'], 'NV':c['g'],
        'MT':c['b'], 'WY':c['g'], 'UT':c['b'], 'AZ':c['r'], 'CO':c['y'],
        'NM':c['g'], 'ND':c['r'], 'SD':c['y'], 'NE':c['b'], 'KS':c['g'],
        'OK':c['r'], 'TX':c['b'], 'MN':c['g'], 'IA':c['r'], 'MO':c['y'],
        'AR':c['g'], 'LA':c['y'], 'WI':c['y'], 'IL':c['g'], 'MI':c['b'],
        'IN':c['y'], 'KY':c['b'], 'TN':c['r'], 'MS':c['b'], 'AL':c['g'],
        'OH':c['g'], 'WV':c['r'], 'VA':c['g'], 'NC':c['y'], 'SC':c['g'],
        'GA':c['b'], 'FL':c['y'], 'NY':c['g'], 'PA':c['b'], 'NJ':c['y'],
        'MD':c['y'], 'DE':c['g'], 'NH':c['r'], 'VT':c['b'], 'MA':c['y'],
        'CT':c['b'], 'RI':c['r'], 'ME':c['g'],
    },
    'interconnect': {
        'western':c['b'],
        'eastern':c['y'],
        'ercot':c['g'],
    },
    'usda_region': {
        'pacific':c['b'],
        'mountain':c['y'],
        'northern-plains':c['b'],
        'southern-plains':c['g'],
        'lake-states':c['g'],
        'corn-belt':c['y'],
        'delta-states':c['b'],
        'southeast':c['y'],
        'appalachia':c['g'],
        'northeast':c['b'],
    },
    'cendiv': {
        'Pacific':c['b'],
        'Mountain':c['y'],
        'West_North_Central':c['b'],
        'West_South_Central':c['g'],
        'East_North_Central':c['g'],
        'East_South_Central':c['y'],
        'South_Atlantic':c['b'],
        'Mid_Atlantic':c['y'],
        'New_England':c['b'],
    },
    'nercr': {
        'WECC_CA':c['y'],
        'WECC_NW':c['b'],
        'WECC_SW':c['g'],
        'SPP':c['y'],
        'ERCOT':c['b'],
        'MISO':c['g'],
        'NPCC_NE':c['g'],
        'NPCC_NY':c['b'],
        'PJM':c['y'],
        # 'SERC':c['b'],
        'SERC_C':cm2(2),
        'SERC_E':cm2(1),
        'SERC_SE':cm2(3),
        'SERC_F':cm2(2),
    },
}

offset = {
    'transreg': {
        'WestConnect': (0,-1e5),
    },
    'transgrp': {
        'MISO_Central': (-1e5,-2e5),
        'SPP_North': (1e5,0),
        'CAISO': (-0.1e5,-0.5e5),
        'NorthernGrid_East': (0,-1e5),
        'WestConnect_North': (0,-1e5),
    }
}

### Plot it
alpha = 0.8
draw_states = True
draw_zones = True
label_zones = {'r': False}
draw_lakes = True
draw_counties = False
label_regions = {'hurdlereg': False}

for level in dfmap:
    dfregion = dfmap[level].copy()
    if level in cmap:
        colors = cmap[level]
        alpha_region = alpha
    else:
        colors = 'C' + mapclassify.greedy(dfregion, strategy='smallest_last').astype(str)
        alpha_region = 0.4

    plt.close()
    f,ax = plt.subplots(figsize=(10,6))
    dfregion.plot(
        ax=ax, facecolor='none', edgecolor='k', lw={'r':0.3}.get(level,1), zorder=1e9,
    )
    if draw_states:
        dfmap['st'].plot(ax=ax, facecolor='none', edgecolor='C7', lw=0.6, zorder=1e8)
    if draw_zones:
        dfmap['r'].plot(ax=ax, facecolor='none', edgecolor='C7', lw=0.3, zorder=1e7)
    if draw_counties:
        dfcounty.plot(ax=ax, facecolor='none', edgecolor='C7', lw=0.02, zorder=1e6)
    if draw_lakes:
        greatlakes.plot(ax=ax, edgecolor='#2CA8E7', facecolor='#D3EFFA', lw=0.2, zorder=-1)
    for r, row in dfregion.iterrows():
        dfregion.loc[[r]].plot(ax=ax, color=colors[r], alpha=alpha_region, lw=0, zorder=1)
        if label_regions.get(level, True):
            x, y = (
                np.array([row.geometry.centroid.x, row.geometry.centroid.y])
                + np.array(offset.get(level, {}).get(r, (0,0)))
            )
            ax.annotate(
                r.replace('_','\n'),
                (x, y),
                ha='center', va='center', weight='bold',
                size={'r':7, 'hurdlereg':7, 'st':10}.get(level,11),
                color='k', zorder=1e11,
                path_effects=[pe.withStroke(linewidth=1.5, foreground='w', alpha=1)]
            )
    if label_zones.get(level, True):
        for r, row in dfmap['r'].iterrows():
            ax.annotate(
                r,
                (row.geometry.centroid.x, row.geometry.centroid.y),
                ha='center', va='center', size=6, weight='normal',
                color='C7', zorder=1e10,
                path_effects=[pe.withStroke(linewidth=0.7, foreground='w', alpha=1)]
            )

    ax.axis('off')
    savename = (
        f"{level}"
        f"-z{int(draw_zones)}"
        f"-s{int(draw_states)}"
        f"-l{int(draw_lakes)}"
        f"-zl{int(label_zones.get(level, True))}"
        f"-rl{int(label_regions.get(level, True))}"
        f"-c{int(draw_counties)}"
    )
    plt.savefig(
        os.path.join(savepath, savename+'.png'),
        transparent=True,
        bbox_inches='tight',
    )
    plt.show()
