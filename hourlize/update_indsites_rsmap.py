###############
#%% IMPORTS ###
import os
import shutil
import pandas as pd
from pdb import set_trace as b

reedspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

df_ons = pd.read_csv(os.path.join(reedspath, 'inputs','supplycurvedata','sitemap.csv'),
                     low_memory=False, usecols=['sc_point_gid','cnty_fips'])
df_ofs = pd.read_csv(os.path.join(reedspath, 'inputs','supplycurvedata','sitemap_offshore.csv'),
                     low_memory=False, usecols=['sc_point_gid','cnty_fips'])
df_county_map = pd.read_csv(os.path.join(reedspath, 'hourlize','inputs','resource','county_map.csv'),
                     low_memory=False, usecols=['cnty_fips','reeds_ba'])
df_rsmap_sreg = pd.read_csv(os.path.join(reedspath, 'inputs','rsmap_sreg.csv'),
                     usecols=['*r','rs'])

df_ons['sc_point_gid'] = 'i' + df_ons['sc_point_gid'].astype(str)
df_ofs['sc_point_gid'] = 'o' + df_ofs['sc_point_gid'].astype(str)

df_ind_sites = pd.concat([df_ons, df_ofs],sort=False,ignore_index=True)
df_ind_sites = df_ind_sites.merge(df_county_map, on='cnty_fips', how='left')
df_ind_sites.rename(columns={'sc_point_gid':'rs', 'reeds_ba':'*r'}, inplace=True)
df_ind_sites = df_ind_sites[['*r','rs']].copy()
df_ind_sites.drop_duplicates(subset=['rs'], inplace=True)
df_rsmap_ind = pd.concat([df_rsmap_sreg, df_ind_sites],sort=False,ignore_index=True)
df_nan = df_rsmap_ind[df_rsmap_ind.isnull().any(axis=1)].copy()
if len(df_nan) > 0:
    print('Uh oh, We have NaNs!')
else:
    print('Yay, no NaNs!')
df_rsmap_ind.to_csv(os.path.join(reedspath, 'inputs','rsmap.csv'), index=False)
