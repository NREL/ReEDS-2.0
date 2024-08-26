# Overview
This folder includes scripts and inputs to postprocess the outputs from regional ReEDS runs into one national run. This is typically useful for county-level runs which are too computionally intensive to run nationally. The scripts can be run locally or on the HPC.

# Overview
* Scripts to create combined outputs, a combined bokehpivot report, and combined transmission and VRE site maps are run from `combine_runs.py`.
* The file `combinefiles.csv` contains all the ouputs currently supported to be combined and the methods for combining them (concatenate, sum, keep first). 

# How to run combine_runs.py

There are two approaches to running `combine_runs.py`: 

1. **Infer run names**: User specifies arguments for the batch name corresponding to the relevant set of runs and the keywords used to indicate which regional runs belong to set. The script infers the scenario from what remains after the batch and keywords are removed. Keywords are specified as separate arguments (no commas) and are case-insensitive.

    As an example, suppose you have the following 6 runs:

    ```
    20240705_Interconnection_BAU_Eastern_county
    20240705_Interconnection_BAU_ERCOT_county
    20240705_Interconnection_BAU_Western_county
    20240705_Interconnection_Decarb_Eastern_county
    20240705_Interconnection_Decarb_ERCOT_county
    20240705_Interconnection_Decarb_Western_county
    ```
    Example call: `python combine_runs.py -b 20240705_Interconnection -k Eastern ERCOT Western` 

    This call combine the first 3 runs into `20240705_Interconnection_BAU_county_combined` and the last 3 runs into `20240705_Interconnection_Decarb_county_combined`.

    
2. **Specify runs directly**: User specifies path to a csv file with information specific runs to combine. This approach is useful if you have runs in different locations aside from your ReEDS runs folder. See format and instructions in the `runlist.csv` file in this folder.

    Example call: `python combine_runs.py -r "runlist.csv"`

# Outputs
* Combined outputs are put in a newly created folder with the common scenario name + `_combined`. 
  * Users can overwrite this format by specifying an argument for `folder_name` in the call to `combine_runs.py`. Note that setting this manually won't work if trying to combine folders across a range of scenarios.
* Only outputs specified specified in `combinefiles.csv` are combined. Please add outputs in new rows in `combinefiles.csv` if you wish to combine ones that are not currently supported.
* 4 combined maps are created in the `maps` folder under `outputs`: map_translines_all-2050, map_translines_all-2050-since2020, map_VREsites-2050, and map_VREsites-translines-2050.
* Combined bokehpivot report is in `reeds-report-combined` folder under `outputs`.

# HPC
The `combine_runs.py` script supports a number of arguments for running on the HPC. To run on the HPC users must specify an allocation (`--account` or `-a`). Walltime is set to 4 hours by default but can be specified directly (`--time` or `-t`). Users can run with high priority (`--priority` or `-p`) or on a debug node (`--debugnode` or `-d`). 

See argument list in `combine_runs.py` for additional details.

# Example usage

```
python combine_runs.py -b 20240705_USA   
# Combine runs in batch '20240705_USA' using default keywords ('east','west','ercot')
```

```
python combine_runs.py -b 20240705_USA -k Pacific ERCOT  
# Combine runs in batch '20240705_USA' using 'Pacific' and 'ERCOT' as keywords
```

```
python combine_runs.py -b 20240705_USA -k Pacific ERCOT --dryrun
# Same as above but only prints out table of runs to combine without actually combining; this is useful if you want to verify your run set.
```

```
python combine_runs.py -r "path/to/runlist.csv"   
# Combine runs as specified in path/to/runlist.csv
```

```
python combine_runs.py -b 20240705_USA -k Pacific ERCOT -a [hpc allocation] -p  
# Same as above but on an HPC node with high priority using a 4:00:00 walltime
```

```
python combine_runs.py -b 20240705_USA -k Pacific ERCOT -a [hpc allocation] -d  
# Same as above but on an HPC debug node
```