# /// script
# This script can be used to take a subset of the h5 files (upv, wind-ofs, wind-ons, and csp)
# 
# requires-python = '>=3.10'
# dependencies = [
#     'h5py',
#     'numpy',
# ]
# ///
import h5py
import numpy as np
import os
import pandas as pd
import pathlib
import site

# load h5
this_dir_path = os.path.dirname(os.path.realpath(__file__))
reeds_path = os.path.realpath(os.path.join(this_dir_path,'..'))
site.addsitedir(reeds_path)
from input_processing.ldc_prep import read_file, write_h5_file

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
rev_paths_ref = pd.Series(['/scratch/bsergi/ReEDS-2.0-2/hourlize/out/upv_reference_county/results',
                           '/scratch/bsergi/ReEDS-2.0-2/hourlize/out/wind-ons_reference_county/results',
                           '/scratch/bsergi/ReEDS-2.0-2/hourlize/out/wind-ofs_reference_county/results',
                           '/kfs2/shared-projects/reeds/Supply_Curve_Data/CSP/2019_Existing/csp_none_county/results'],
                           index=['upv','wind-ons','wind-ofs','csp']
                        )

# iterate over tech/path
for idx, h5path in rev_paths_ref.items():
    fname_in = os.path.join(h5path, idx + '.h5')
    print(f'Reading {fname_in}')
    f = read_file(fname_in)
    # get region from column names (assumes 'class|region' format)
    columns = [str(x).split('|')[1].strip('"') for x in f.columns.tolist()]

    # subset to counties of interest
    mask = [x in counties for x in columns]  # Create a mask that are for the 
    subset_f = f.loc[:, mask].copy()

    # write file back out
    dir_out = os.path.join(this_dir_path, 'data', 'county')
    print(f'Saving subset to {os.path.join(dir_out, idx + ".h5")}')
    write_h5_file(subset_f, idx + '.h5', dir_out)

print("Finished updated county test profiles.")