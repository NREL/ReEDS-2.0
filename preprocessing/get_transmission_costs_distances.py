#########
#%% NOTES
"""
One-time procedure: Import transmission line costs and distances from reV
"""

##############
#%%### IMPORTS
import os
import site
import pandas as pd
import geopandas as gpd

os.environ['PROJ_NETWORK'] = 'OFF'

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
drivepath = 'Volumes' if sys.platform == 'darwin' else '/nrelnas01'
revpath = r'/{}/Users/pbrown/reV/ReEDS_BA-BA/'.format(drivepath)

site.addsitedir(os.path.join(reeds_path,'postprocessing','retail_rate_module'))
# import ferc_distadmin after setting the module path; if it's done before, it won't be found
import ferc_distadmin  # noqa: E402

##########
#%% INPUTS

inflatable = ferc_distadmin.get_inflatable(
    os.path.join(reeds_path,'inputs','financials','inflation_default.csv'))

crs = 'ESRI:102008'
input_dollaryear = 2019
output_dollaryear = 2004
inflator = inflatable[input_dollaryear, output_dollaryear]

infiles = {
    '500kVac': '1000MW_ReEDS_BA_1500MW_500kV.gpkg',
    '500kVdc': '3000MW_ReEDS_BA_3000MW_500kV.gpkg',
}
linecap_mw = {'500kVac': 1500, '500kVdc': 3000,}

#############
#%% PROCEDURE
for trtype in infiles:
    dftrans = gpd.read_file(os.path.join(revpath,'ReEDS_BA-BA',infiles[trtype]))

    dftrans.crs = crs
    index2ba = dftrans[['index','ba']].drop_duplicates().set_index('index').ba

    dftrans['length_miles'] = dftrans['length_km'] / 1.60934
    dftrans['start_ba'] = 'p' + dftrans['start_index'].map(index2ba).astype(str)
    dftrans['start_banum'] = dftrans['start_index'].map(index2ba).astype(str)
    dftrans['USDperMWmile'] = (dftrans['cost'] / (dftrans['length_miles']) / linecap_mw[trtype])
    dftrans['USDperMW'] = (dftrans['cost'] / linecap_mw[trtype])

    ###### Write clean version without geometries for ReEDS
    dfwrite = (
        dftrans
        .drop(['geometry','population','name','index','start_index','cost'],axis=1)
        .rename(columns={
            'ba_str':'rr','start_ba':'r','start_banum':'rnum','ba':'rrnum',
        })
        .astype({'rnum':int,'rrnum':int})
        .sort_values(['rnum','rrnum'])
        [['r','rr','length_km','length_miles','USDperMW','USDperMWmile','rnum','rrnum']]
    )
    ### Update some columns
    dfwrite['USD{}perMW'.format(output_dollaryear)] = dfwrite.USDperMW * inflator
    dfwrite['USD{}perMWmile'.format(output_dollaryear)] = dfwrite.USDperMWmile * inflator

    outcols = ['r','rr','length_miles','USD{}perMW'.format(output_dollaryear)]
    dfwrite.round(2)[outcols].to_csv(
        os.path.join(
            reeds_path,'inputs','transmission',
            'transmission_distance_cost_{}.csv'.format(trtype)),
        index=False)