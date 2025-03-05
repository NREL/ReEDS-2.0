# /// script
# This script can be used to take a subset of the h5 files (upv, wind-ofs, wind-ons, and csp)
# 
# requires-python = '>=3.10'
# dependencies = [
#     'h5py',
#     'numpy',
# ]
# ///
import os
import sys
import pandas as pd
import site

#Switches
techs_to_update = ['upv','wind-ons','wind-ofs','csp'] #downselect if updating only certain techs

# load h5
this_dir_path = os.path.dirname(os.path.realpath(__file__))
reeds_path = os.path.realpath(os.path.join(this_dir_path,'..'))
site.addsitedir(reeds_path)
import reeds

# counties in p6
counties = [
    'p41011',
    'p41015',
    'p41019',
    'p41029',
    'p41033',
    'p41035',
]

# series of paths to updated county h5 files
hpc = True if ('NREL_CLUSTER' in os.environ) else False
if hpc:
    remotepath = '/kfs2/shared-projects/reeds' #kestrel
else:
    remotepath = f"{('/Volumes' if sys.platform == 'darwin' else '//nrelnas01')}/ReEDS"
df_rev_paths = pd.read_csv(f'{reeds_path}/inputs/supply_curve/rev_paths.csv', usecols=['tech','access_case','sc_path'])
df_rev_paths = df_rev_paths[df_rev_paths['tech'].isin(techs_to_update)]
df_rev_paths = df_rev_paths[df_rev_paths['access_case'].isin(['reference','none'])]
df_rev_paths['county_h5_path'] =  remotepath + '/Supply_Curve_Data/' + df_rev_paths['sc_path'] + '/' + df_rev_paths['tech'] + '_' + df_rev_paths['access_case'] + '_county/results'
rev_paths_ref = df_rev_paths.set_index('tech')['county_h5_path']

# iterate over tech/path
for idx, h5path in rev_paths_ref.items():
    fname_in = os.path.join(h5path, idx + '.h5')
    print(f'Reading {fname_in}')
    f = reeds.io.read_file(fname_in)
    # get region from column names (assumes 'class|region' format)
    columns = [str(x).split('|')[1].strip('"') for x in f.columns.tolist()]

    # subset to counties of interest
    mask = [x in counties for x in columns]  # Create a mask that are for the 
    subset_f = f.loc[:, mask].copy()

    # write file back out
    dir_out = os.path.join(this_dir_path, 'data', 'county')
    print(f'Saving subset to {os.path.join(dir_out, idx + ".h5")}')
    reeds.io.write_profile_to_h5(subset_f, idx + '.h5', dir_out)

print("Finished updated county test profiles.")
