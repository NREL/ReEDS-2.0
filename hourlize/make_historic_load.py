"""
Simple script for creating historic load h5 profile from h5 files without model year dimension
"""

import os
import site
import pandas as pd
this_dir_path = os.path.dirname(os.path.realpath(__file__))
site.addsitedir(f'{this_dir_path}/../')
import reeds
from pdb import set_trace as b

print('Read hourly load and load multipliers')
hierarchy = pd.read_csv(f'{this_dir_path}/../inputs/hierarchy.csv').rename(columns={'ba':'r'}).set_index('r')
load_historical_pre2015 = reeds.io.read_file(f'{this_dir_path}/../inputs/load/historic_load_hourly.h5', parse_timestamps=True)
load_historical_post2015 = reeds.io.read_file(f'{this_dir_path}/../inputs/load/historic_post2015_load_hourly.h5', parse_timestamps=True)
load_historical = pd.concat([load_historical_pre2015,load_historical_post2015],axis=0)

load_multiplier = pd.read_csv(f'{this_dir_path}/../inputs/load/demand_AEO_2023_reference.csv')
load_multiplier_agglevel = 'st'
print('Map multipliers to BAs')
r2ba = hierarchy.reset_index(drop=False)[['r', load_multiplier_agglevel]]
load_multiplier = load_multiplier.rename(columns={'r': load_multiplier_agglevel})
load_multiplier = (
    load_multiplier.merge(r2ba, on=[load_multiplier_agglevel], how='outer')
    .dropna(axis=0, how='any')
)
load_multiplier = load_multiplier[['year', 'r', 'multiplier']]
print('Reformat hourly load profiles to merge with load multipliers')
load_historical = load_historical.reset_index()
load_historical = pd.melt(load_historical, id_vars=['datetime'], var_name='r', value_name='load')
print('Merge load multipliers into hourly load profiles')
load_historical = load_historical.merge(load_multiplier, on=['r'], how='outer')
load_historical.sort_values(by=['r', 'year'], ascending=True, inplace=True)
load_historical['load'] *= load_historical['multiplier']
load_historical = load_historical[['year', 'datetime', 'r', 'load']]
print('Reformat hourly load profiles')
load_profiles = load_historical.pivot_table(index=['year', 'datetime'], columns='r', values='load')
## the projected load profiles have an integer 'year' index. This is currently a float and needs to be set to an int format.
load_profiles.index = load_profiles.index.set_levels([load_profiles.index.levels[0].astype(int), load_profiles.index.levels[1]], level=['year', 'datetime'])

print('Write out full hourly load profiles')
reeds.io.write_profile_to_h5(load_profiles, f'historic_full_load_hourly.h5', f'{this_dir_path}/out', compression_opts=4)
