# Analysis tools and helper scripts

The ReEDS model includes several tools for setting up new cases, managing active cases, and analyzing case results.
Most of these scripts have command-line interfaces, the details of which can be printed by running `python path/to/scriptname.py -h`.

## Setting up new cases

### Create a new cases_{}.csv file: `preprocessing/casemaker.py`

This script does not have a command-line interface, but can be edited by the user and used to create a cases_{}.csv file with a matrix of switch settings.

### Fix representative/stress periods: `preprocessing/get_case_periods.py`

This script takes as its required argument a filepath to a completed ReEDS case.

- If the optional `-r/--rep` flag is added (as in `python preprocessing/get_case_periods.py path/to/casename -r`), the representative periods for the provided run are written to `inputs/variability/period_szn_user_{name}.csv`, where `name` is either provided by the `-n/--name` argument or (if no name is provided) given by the case name.
  - In a subsequent case, these representative periods can be used by setting `GSw_HourlyClusterAlgorithm` to `user_{name}`.
- If the optional `-s/--stress` flag is added, the stress periods for the provided run are written to `inputs/variability/stressperiods_user_{name}.csv`.
  - In a subsequent case, these stress periods can be used by setting `GSw_PRM_StressModel` to `user_{name}`.

## Managing currently-running cases

### Print details for active HPC runs: `runstatus.py`

This script prints details about cases that are currently running on the HPC.

- If run without arguments (`python runstatus.py`), it uses `squeue` to get a list of the active runs under your username.
- If run with an argument (e.g. `python runstatus.py v20250310`), it only prints details for runs whose name begins with the provided argument.
- Adding the `-f` flag will print the names of the finished runs: `python runstatus.py v20231112 -f`
- If you increase the verbosity by adding `-v` flags, it prints a number of lines from the end of that run's gamslog.txt equal to the number of v's in the flag: `python runstatus.py v20231112 -vvvvv`

### Manage HPC runs: `restart_runs.py`

This script restarts failed runs on the HPC whose case name starts with the provided prefix: `python restart_runs.py case_name_prefix`

## Analyzing finished cases

### Compare results: `postprocessing/compare_cases.py`

This script creates a powerpoint file comparing the results of the cases provided via the `caselist` argument.
The list of cases to compare can be provided in one of two ways: as a space-delimited list of filepaths, or as a single filepath to a .csv file in the format of postprocessing/example.csv.
The first case in the list is treated as the base case, and other cases are all compared to that same case.

Example for two cases:

```bash
python postprocessing/compare_cases.py /Users/username/github/ReEDS-2.0/runs/v20250310_main_USA /Users/username/github/ReEDS-2.0/runs/v20250310_newthing_USA
```

Example for three cases:

```bash
python postprocessing/compare_cases.py /Users/username/github/ReEDS-2.0/runs/v20250310_main_USA /Users/username/github/ReEDS-2.0/runs/v20250310_newthing1_USA /Users/username/github/ReEDS-2.0/runs/v20250310_newthing2_USA
```

Example for a .csv file of cases:

```bash
python postprocessing/compare_cases.py /Users/username/github/ReEDS-2.0/postprocessing/example.csv
```

### Run PRAS: `postprocessing/run_reeds2pras.py`

The PRAS model is typically run multiple times during each ReEDS case (as long as `GSw_PRM_CapCredit = 0`) to ensure resource adequacy.
This script reruns PRAS on a finished ReEDS case (provided by the single required command-line argument) and allows the settings to be changed.
For example, to use a different number of samples than are specified by the default `pras_samples` switch, use the `-s/--samples` command-line argument.

### Run a dispatch model: `run_pcm.py`

This script reruns a completed ReEDS case as a dispatch simulation at higher time resolution.
The operational constraints in `c_supplymodel.gms` are used directly, but the investment and capacity variables are fixed to their previously optimized values; only the operational variables are re-optimized.
365 representative 1-day periods at 1-hour resolution are used by default, but these settings can be changed using the `-s/--switch_mods` switch.

This approach is distinct from the [R2X](https://github.com/NREL/R2X) tool, which formats the results of a ReEDS case as inputs to a separate production cost modeling tool such as [Sienna](https://github.com/NREL-Sienna) or [PLEXOS](https://www.energyexemplar.com/plexos).
Those tools provide more advanced and realistic features like unit commitment and rolling forecast horizons;
by contrast, `run_pcm.py` simply reuses the existing ReEDS formulation at higher time resolution,
and is subject to all the normal caveats and limitations of ReEDS (linear variables, pipe-and-bubble transmission flow, etc.).

### Generate static plots: `postprocessing/transmission_maps.py`

This script runs automatically at the end of a ReEDS case and writes static maps to the {case}/outputs/maps folder as .png files.

### Generate interactive plots: `postprocessing/bokehpivot`

The bokehpivot module can be used to visualize the outputs of ReEDS runs.
For more information on how to use bokehpivot, see the [bokehpivot guide](bokehpivot.md).

If you're new to bokehpivot, the following YouTube video will be a good starting point: [Viewing ReEDS Outputs Using the BokehPivot Module](https://www.youtube.com/watch?v=8Xi59M4bB6I&list=PLmIn8Hncs7bG558qNlmz2QbKhsv7QCKiC&index=3)

### Calculate hourly prices and technology value metrics: `postprocessing/reValue`

reValue is used for two main things:

- extracting regional hourly prices from ReEDS scenarios and years
- (Optional) using extracted prices to calculate value and competitiveness-related metrics for a set of regional generation or load profiles.

More more information on reValue, see the [reValue documentation](revalue.md).

### Estimate retail rates: `postprocessing/retail_rate_module`

The retail rate module can be used after finishing a ReEDS run to calculate retail electricity rates by state and year, where each state is served by its own investor-owned utility (IOU).

For more information on this module, see the [retail_rate_module documentation](retail_rate_module.md).

### Generate a Tableau results viewer: `postprocessing/tableau`

Tableau can be used for the analysis of ReEDS and ReEDS-to-PLEXOS results in Tableau.

For more information on how to use Tableau with ReEDS, see the [Tableau documentation](tableau.md).
