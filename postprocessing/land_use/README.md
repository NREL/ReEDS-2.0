# Overview

The `land_use_analysis.py` script uses the outputs from `reeds_to_rev.py` to 
estimate total land use from a ReEDS scenario for a set of specified reV characterizations.  

# How to run 

The land_use analysis processing can be run as part of a ReEDS run by setting `land_use_analysis=1` (`reeds_to_rev` must also be enabled). By default the script runs for all supported technologies (upv and wind-ons).

Alternatively, the script can be run as a standalone for a specified ReEDS run by passing the folder of the run: `python postprocessing/land_use/land_use_analysis.py /kfs3/scratch/bsergi/ReEDS-2.0/runs/[run folder]`. See the passed arguments options in the script for some additional options for running in standalone mode.

When running, users specify which land characterizations from the reV supply curve they want to process in `postprocessing/land_use/inputs/process_categories.json`. Each entry has a format like the following:

```
"nlcd": {"colname": "nlcd_2019_90x90", "newcolname":"nlcd_value", "mapping": "nlcd_combined_categories"}
```

In this example, "nlcd" is a characterization name provided by the user reflecting the column of interest. It is also use for formatting the name of the output file (see details below). 

The dictionary that follows the characterization name provides information on the column to be processed. 
- The entry specified for "colname" indicates the reV supply curve column to process. Typically this is a single string but can be a list if the shorthand name is specified as "species".
- An optional entry for "mapping" that specifies a file in `postprocessing/land_use/inputs` to use for mapping the reV json values to new categories.
- An optional entry for "newcolname" that specifies which column in the mapping file to map to (must be specified if mapping is present).

Users should configure the `process_categories.json` as needed before running. 

# Outputs

The script produces files named in the format `land_use_[tech]_[chracterization].csv.gz` in the outputs folder of the ReEDS run for each characterization specified in the json configure file. For characterizations defined by json files the outputs will include 1 row of data per supply curve point / land cover type / ReEDS built out year. To reduce file size this only includes data for the first simulation year (usually 2023 or 2024) and the last year. The columns include information on the area and built capacity for the supply curve point as a whole and each land cover category within that supply curve point.  

For characterizations defined by the number of cells of coverage (typically species habitat and range), all columns are combined into one "species" land use file in long format by characterization, with output including total supply curve area and buildout and the area of the species habitat/range in that supply curve.

# Notes

The `land_use_analysis.py` requires outputs from `reeds_to_rev.py` as well as the ability to read in the reV supply curves for the corresponding run. Path information for the supply curves is taken from the run's `rev_paths.csv` file. 

Area estimates are derived assuming a reV cell resolution of 90x90 m resolution. For wind the area estimates include indirect land use (i.e., land needed between turbines for spacing).    