#%% IMPORTS
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import os, sys, site, importlib
import traceback
import shapely

import geopandas as gpd
os.environ['PROJ_NETWORK'] = 'OFF'

#reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
reeds_path = "/scratch/bsergi/ReEDS-2.0"
site.addsitedir(os.path.join(reeds_path,'postprocessing'))
site.addsitedir(os.path.join(reeds_path,'input_processing'))
import plots
import reedsplots as rplots
from ticker import makelog
plots.plotparams()


##########
#%% SITE PLOT

def plot_vresites_transmission(
        casename, resultspath, year=2050, crs='ESRI:102008',
        routes=True, wscale=1.5, show_overlap=False,
        subtract_baseyear=None,
        alpha=0.25, colors='k', ms=1.15,
        techs=['upv','wind-ons','wind-ofs'],
        cm={'wind-ons':plt.cm.Blues, 'upv':plt.cm.Reds, 'wind-ofs':plt.cm.Purples},
        zorder={'wind-ons':-20002,'upv':-20001,'wind-ofs':-20000},
        cbarhoffset={'wind-ons':-0.8, 'upv':0.0, 'wind-ofs':0.8},
        label={'wind-ons':'Land-based wind [GW]',
               'upv':'Photovoltaics [GW]',
               'wind-ofs':'Offshore wind [GW]'},
        vmax={'upv':4.303, 'wind-ons':0.4, 'wind-ofs':0.6},
        trans_scale=True,
        show_transmission=True,
        title=True,
        dfba=None, dfstates=None, lakes=None,
    ):
    """
    """

    
    ### Get the reeds_to_rev.py outputs
    cap = {}
    ## TODO: modify paths here
    for tech in techs:
        try:
            cap[tech] = pd.read_csv(
                os.path.join(resultspath,f'{case}_{tech}_buildout.csv')
            ).rename(columns={'built_capacity':'capacity_MW'})
            cap[tech]['geometry'] = cap[tech].apply(
                lambda row: shapely.geometry.Point(row.longitude, row.latitude),
                axis=1)
            cap[tech] = gpd.GeoDataFrame(cap[tech]).set_crs('EPSG:4326').to_crs(crs)

        except FileNotFoundError as err:
            print(err)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(8,8), dpi=600)
    dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=0.1, zorder=100000)
    dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.25, zorder=100001)
    try:
        lakes.plot(ax=ax, edgecolor='#2CA8E7', facecolor='#D3EFFA', lw=0.2, zorder=-1)
    except NameError:
        pass

    for tech in cap:
        legend_kwds = {
            'shrink':0.5, 'pad':0.05,
            'label':label[tech],
            'orientation':'horizontal',
        }

        dfplot = cap[tech].loc[cap[tech].year==year].sort_values('capacity_MW')
        dfplot['GW'] = dfplot['capacity_MW'] / 1000

        dfplot.plot(
            ax=ax, column='GW', cmap=cm[tech],
            marker='s', markersize=ms, lw=0,
            legend=False, legend_kwds=legend_kwds,
            vmin=0, vmax=vmax[tech], zorder=zorder[tech],
        )

        plots.addcolorbarhist(
            f=f, ax0=ax, data=dfplot.GW.values, title=legend_kwds['label'], cmap=cm[tech],
            vmin=0., vmax=vmax[tech],
            orientation='horizontal', labelpad=2.25, cbarbottom=-0.01, histratio=1.,
            cbarwidth=0.025, cbarheight=0.25, cbarhoffset=cbarhoffset[tech],
        )

    ### Transmission scale
    if show_transmission and trans_scale:
        ymin = ax.get_ylim()[0]
        xmin = ax.get_xlim()[0]
        if routes or (not show_overlap):
            gpd.GeoSeries(
                shapely.geometry.LineString([(xmin*0.8,ymin*0.6),(xmin*0.6,ymin*0.6)])
            ).buffer(wscale*10e3).plot(
                ax=ax, color=(colors if isinstance(colors,str) else 'k'), alpha=alpha)
        else:
            ax.plot(
                [xmin*0.8,xmin*0.6], [ymin*0.6, ymin*0.6],
                color=(colors if isinstance(colors,str) else 'k'),
                lw=wscale*10e3, solid_capstyle='butt', alpha=alpha,
            )
        ax.annotate(
            'Transmission\n10 GW', (xmin*0.7, ymin*0.66),
            ha='center', va='top', weight='bold', fontsize='large')

    ### Formatting
    if title:
        ax.annotate(
            '{} ({})'.format(os.path.basename(case), year),
            (0.1,1), xycoords='axes fraction', fontsize=10)
    ax.axis('off')

    return f,ax


##########
#%% INPUTS
## Note that if your case builds lots of transmission, wscale might
## need to be reduced to avoid too much overlap in the plotted routes
wscale_straight = 0.0004
wscale_routes = 1.5
wscale_h2 = 3
routes = False
## Note that if you change the CRS you'll probably need to change
## the position of the annotations
crs = 'ESRI:102008'

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


#############
#%% PROCEDURE
#%% Set up logger

#%% Make output directory
savepath = "/scratch/bsergi/ReEDS-2.0/runs/landuse_results/maps-0.2MW"
resultspath = "/scratch/bsergi/ReEDS-2.0/runs/landuse_results/r2r_combined"
os.makedirs(savepath, exist_ok=True)

solar_scenarios = ["BAU", "High_Solar"]
land_scenarios = ["nlcd", "a1b", "a2", "b1", "b2"]

year = 2050
cases = [f"{s}_{l}" for s in solar_scenarios for l in land_scenarios]
# for testing
#cases = ["BAU_nlcd"]

### Get the BA map
print("Loading shapefiles")
dfba = rplots.getcountymap()
### Aggregate to states
dfstates = dfba.dissolve('st')
### Get the lakes
try:
    lakes = gpd.read_file(
        os.path.join(reeds_path,'inputs','shapefiles','greatlakes.gpkg')).to_crs(crs)
except FileNotFoundError as err:
    print(err)

for case in cases:
    print(f"Plotting {case}")
    #%% Site VRE capacity
    try:
        plt.close()
        f,ax = plot_vresites_transmission(
            case, resultspath, year, crs=crs, cm=gen_cmap,
            routes=False, wscale=wscale_straight, show_overlap=False,
            subtract_baseyear=None, show_transmission=False,
            alpha=transalpha, colors=transcolor, ms=ms,
            dfba=dfba, dfstates=dfstates, lakes=lakes,
            vmax={'upv':0.2, 'wind-ons':0.4, 'wind-ofs':0.6}
        )
        savename = f'{case}-map_VREsites-{year}.png'
        if write: plt.savefig(os.path.join(savepath, savename))
        if interactive: plt.show()
        plt.close()
        print(savename)
    except Exception as err:
        print('map_VREsites failed:')
        print(traceback.format_exc())


#%% Site VRE capacity overlaid with transmission
# try:
#     plt.close()
#     f,ax = rplots.plot_vresites_transmission(
#         casedir, year, crs=crs, cm=gen_cmap,
#         routes=routes, show_overlap=False,
#         wscale=wscale_routes,
#         subtract_baseyear=None, show_transmission=True,
#         alpha=transalpha, colors=transcolor, ms=ms,
#     )
#     savename = f'map_VREsites-translines-{year}.png'
#     if write: plt.savefig(os.path.join(savepath, savename))
#     if interactive: plt.show()
#     plt.close()
#     print(savename)
# except Exception as err:
#     print('map_VREsites-translines failed:')
#     print(traceback.format_exc())
