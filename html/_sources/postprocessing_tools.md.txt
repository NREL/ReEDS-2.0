# Post-Processing and Analysis Tools
There are several tools that can be found in the ReEDS repository. 

## Helper Scripts and Tools
### Comparison

**postprocessing/compare_cases.py**

Compare_cases.py will take two ReEDS case paths and create a powerpoint comparing the cases.

Command to run this script: `python postprocessing/compare_cases.py [path to ReEDS run #1] [path to ReEDS run #2]`

Example: 
```
$ python postprocessing/compare_cases.py /Users/km/ReEDS-2.0/runs/v20231221_USA /Users/km/ReEDS-2.0/runs/v20231221_USA_ref
```

**postprocessing/compare_casegroup.py**

Compare_casegroup.py will take any number of ReEDS case paths and create a powerpoint comparing all cases. The only required argument is a comma-delimited list of ReEDS case paths. 

Example: 

```
$ python postprocessing/compare_casegroup.py /Volumes/ReEDS/Users/pb/ReEDSruns/20231103_stress/v20231218_casegroupK0_USA_ref,/Volumes/ReEDS/Users/pb/ReEDSruns/20231103_stress/v20231218_casegroupK0_USA_lim,/Volumes/ReEDS/Users/pb/ReEDSruns/20231103_stress/v20231218_casegroupK0_USA_open,/Volumes/ReEDS/Users/pb/ReEDSruns/20231103_stress/v20231218_casegroupK0_USA_transgrp --casenames=Ref,Lim,Open,transgrp
```

or similarly: 

```
$ python postprocessing/compare_casegroup.py /Volumes/ReEDS/Users/pb/ReEDSruns/20231103_stress/v20231218_casegroupK0_USA_ref,/Volumes/ReEDS/Users/pb/ReEDSruns/20231103_stress/v20231218_casegroupK0_USA_lim,/Volumes/ReEDS/Users/pb/ReEDSruns/20231103_stress/v20231218_casegroupK0_USA_open,/Volumes/ReEDS/Users/pb/ReEDSruns/20231103_stress/v20231218_casegroupK0_USA_transgrp --titleshorten=26
```

Other optional arguments are: 

```
 --casenames CASENAMES, -n CASENAMES
      comma-delimited list of shorter case names to use in plots (default: )
 --titleshorten TITLESHORTEN, -s TITLESHORTEN
      characters to cut from start of case name (only used if no casenames) (default: 0)
 --startyear STARTYEAR, -y STARTYEAR
      First year to show (default: 2020)
```

### Run Management

**runstatus.py**

runstatus.py can be used to print details about runs that are currently running on the HPC.

Command to run this script: `python runstatus.py [batch prefix]`

Example:
```
$ python runstatus.py v20231112
```

Adding the `-f` flag will print the names of the finished runs: `$ python runstatus.py v20231112 -f`

If you increase the verbosity by adding `-v` flags, it prints a number of lines from the end of that run's gamslog.txt equal to the number of v's in the flag: `$ python runstatus.py v20231112 -vvvvv`

**restart_runs.py**

restart_runs.py can be used to restart any failed runs for a given batch. **This only works on HPC currently.**

Command to run this script: `python restart_runs.py [batch prefix]`

Example:
```
$ python restart_runs.py v20231112
```

**interim_report.py**

interim_report.py can be used to [**todo: fill in additional details**]

Command to run this script: `python interim_report.py [path to ReEDS run]`

Example:
```
$ python interim_report.py /Users/km/ReEDS-2.0/runs/v20231221_USA_ref
```

**runs/{case}/meta.csv**

The meta.csv file is generated for each run. 

Information found in the meta.csv file: 
   1. Computer & Github information for the run (computer, repo, branch, commit, description)
   2. Information for each process of the run (year, process, starttime, stoptime, processtime)  


### Preprocessing

**preprocessing/casemaker.py**

**[todo: add additional information]**

Example: 
```
$ python casemaker.py ...
```

**preprocessing/get_case_periods.py**

**[todo: add additional information]**

Example: 
```
$ python get_case_periods.py ...
```


### Tool Linkages

**postprocessing/run_reeds2pras.py**

run_reeds2pras.py can be used to [**todo: fill in additional details**]

Example:
```
$ python postprocessing/run_reeds2pras.py ...
```

### Visualization

**postprocessing/plots.py**

**[todo: add additional information]**

Example:
```
$ python postprocessing/plots.py
```

**postprocessing/reedsplots.py**

**[todo: add additional information]**

Example:
```
$ python postprocessing/reedsplots.py
```

**postprocessing/transmission_maps.py**

**[todo: add additional information]**

Example:
```
$ python postprocessing/transmission_maps.py
```


## Analysis Modules
### BokehPivot
Bokehpivot can be used for visualizing the outputs of ReEDS runs. For more information on how to use bokehpivot, see the [bokehpivot guide](bokehpivot.md).

If you're new to BokehPivot, the following YouTube video will be a good starting point: [Viewing ReEDS Outputs Using the BokehPivot Module](https://www.youtube.com/watch?v=8Xi59M4bB6I&list=PLmIn8Hncs7bG558qNlmz2QbKhsv7QCKiC&index=3)

### reValue
reValue is used for two main things: 
   * extracting regional hourly prices from ReEDS scenarios and years
   * (Optional) using extracted prices to calculate value and competitiveness-related metrics for a set of regional generation or load profiles.

More more information on reValue, see the [reValue documentation](revalue.md).

### retail_rate_module
The retail rate module can be used after finishing a ReEDS run to calculate retail electricity rates by state and year, where each state is served by its own investor-owned utility (IOU). 

For more information on this module, see the [retail_rate_module documentation](retail_rate_module.md).

### Analysis of ReEDS in Tableau
Tableau can be used for the analysis of ReEDS and ReEDS-to-PLEXOS results in Tableau. 

For more information on how to use Tableau with ReEDS, see the [Tableau documentation](tableau.md).