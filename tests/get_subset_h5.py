# /// script
# This script can be used to take a subset of the h5 files (upv, wind-ofs, wind-ons, and csp)
# 
# requires-python = ">=3.10"
# dependencies = [
#     "h5py",
#     "numpy",
# ]
# ///
import h5py
import numpy as np
import pathlib

# counties in p6
counties = [
    'p41011',
    'p41015',
    'p41019',
    'p41029',
    'p41033',
    'p41035',
]


# counties in RI & p22
# counties = [
#     "p44001",
#     "p44003",
#     "p44005",
#     "p44007",
#     "p44009",
#     "p56019",
#     "p56033",
# ]

## to get a subset of the upv, wind-ofs, and wind-ons data

fname = "/Volumes/reeds/Supply_Curve_Data/UPV/2024_07_09_Standard_Scenarios/upv_reference_county/results/upv.h5"
# fname = "/Volumes/ReEDS/Supply_Curve_Data/OFFSHORE/2024_07_23_Update/wind-ofs_reference_county/results/wind-ofs.h5"
# fname = "/Volumes/ReEDS/Supply_Curve_Data/ONSHORE/2024_06_20_Update/wind-ons_reference_county/results/wind-ons.h5"

f = h5py.File(fname, "r")
# <KeysViewHDF5 ['cf', 'columns', 'index']>

cf = f["cf"]
cols = f["columns"]
index = f["index"]
columns = [str(x).split("_")[1].strip("'") for x in cols[:].tolist()]
mask = [x in counties for x in columns]  # Create a mask that are for the 
subset_cf = cf[:, mask]
subset_cols = cols[:][mask]
subset_index = index[:]


# assert subset_cf.shape[1] == len(counties), "Not all counties found."

# start here for non-csp
output_fname = "wind-ofs.h5"
output_fpath = pathlib.Path.cwd() / output_fname
if output_fpath.exists():
    output_fpath.unlink()


# Create subset h5 file
subset = h5py.File("wind-ofs.h5", "w")

cf_data = subset.create_dataset(
    "cf", shape=(subset_cf.shape[0], subset_cf.shape[1]), dtype=np.float16
)
column_data = subset.create_dataset(
    "columns",
    shape=(subset_cf.shape[1],),
    data=subset_cols,
    dtype=subset_cols.dtype
)
index_data = subset.create_dataset(
    "index",
    shape=index.shape,  # Use the original shape for the index
    data=subset_index,  # Include the full index or subset if needed
    dtype=index.dtype
)

cf_data.write_direct(subset_cf)
# TODO: Maybe we need to add the index as well?
subset.close()
 


## to get a subset of the csp data
from ldc_prep import read_file, read_h5py_file

fname = "/Volumes/ReEDS/Supply_Curve_Data/CSP/2019_Existing/csp_none_county/results/csp.h5"
f = read_file(fname)
subset_df = f.loc[:, f.columns.isin([
    "1_p44001",
    "1_p44003",
    "1_p44005",
    "1_p44007",
    "1_p44009",
    "1_p56019",
    "1_p56033",
])]

subset_df.to_hdf("csp.h5", key="data", data_columns=True)