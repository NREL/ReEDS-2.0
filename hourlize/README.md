# Hourlize

## Overview
Hourlize processes hourly resource and load data into ReEDS inputs. The vision is for this module to allow maximum flexibility
temporally and spatially.

Hourlize is run by a call to `run_hourlize.py`, which assembles information on the cases to run and then executes a call to either
 `resource.py` and `load.py`. The `run_hourlize.py` script can be used to set up jobs to submit to the HPC to run in parallel or to run hourlize jobs directly in sequence. 

### Quickstart: Resource
1. Copy any new reV supply curves to the supply curve folder and update the rev_paths file ([details](#setup-for-rev-supply-curves)).
1. Update settings in `config_base.json` as needed ([details](#config-jsons)).
1. Update settings in the relevant `config_[tech].json` files as needed ([details](#config-jsons)).
1. Specify cases to run in `cases.json` or create your own cases file ([details](#cases-json)).
1. If running on the HPC, specify run allocation or other submission settings in `hourlize/inputs/configs/srun_template.sh` ([details](#config-jsons)).
1. Run using `run_hourlize.py resource` ([details](#running-hourlize)). 

### Quickstart: Load
1. Update settings in `config_base.json` as needed ([details](#config-jsons)).
1. If running on the HPC, specify run allocation or other submission settings in `inputs/configs/srun_template.sh` ([details](#config-jsons)).
1. Run using `run_hourlize.py load` ([details](#running-hourlize)). 

For more details and run options see further below.

## Setup for reV supply curves

If you don't have new reV supply curves you can probably skip this section and go down to [running hourlize](#running-hourlize). However, if you are planning on pushing your supply curve outputs to the repo don't forget to [sync the shared directories](#4-synchronize-shared-directories).

#### 1. Copy reV runs to reeds shared directory

Before running resource hourlize the reV runs should be copied from their original location to the shared folder. Currently reV data used in ReEDS (along with hourlize inputs and outputs) are stored in three places:
* on the nrelnas01 device at `\\nrelnas01\ReEDS\Supply_Curve_Data`
* on Eagle at `/shared-projects/reeds/Supply_Curve_Data`
* on Kestrel at `/projects/shared-projects-reeds/reeds/Supply_Curve_Data`

Under the appropriate tech folder (UPV, ONSHORE, OFFSHORE, etc.) create a directory with a descrptive name for the supply curves (e.g., 2023_06_06_Update). Then copy the reV supply curves and profiles into a folder called `reV`. A good approach is to use rsync; below is an example copying original reV files from Eagle to Kestrel:

```
rsync -aPu [username]@eagle.hpc.nrel.gov://shared-projects/rev/projects/seto/fy23/rev/standard_scenarios/aggregation/  /projects/shared-projects-reeds/reeds/Supply_Curve_Data/UPV/2023_06_06_Update/reV
```

Note that sometimes all the necessary files are in each supply curve folder and sometimes the reV team creates a separate "post_processed_supply_curves" folder that should also be copied. 

#### 2. Update the rev_paths files

Update the reV paths file at `ReEDS-2.0/inputs/supplycurvedata/rev_paths.csv`. Typically this means updating the information for whichever techs (e.g., upv, wind-ons, wind-ofs) and access cases (e.g., reference, open, limited) you want to run. Some details on the columns to update:
-  `sc_path`: path to the supply curve folder on the shared drive; should be of the format tech/update_name (e.g. UPV/2023_06_06_Update, ONSHORE/2023_07_28_Update).
-  `rev_path`: path to the folder with the copied reV run; typically this should be in a folder called "reV" within the sc_path folder (e.g., UPV/2023_06_06_Update/reV/02_limited).
- `sc_file`: relative path to the reV supply curve csv file.
- `hpc_sc_file`: full path to the reV supply curve csv file on the HPC. Needed for R2P.
- `original_rev_folder`: full path of the original location of the supply curves passed by the reV team. Not actively used but useful for debugging issues with the reV runs.
- `cf_path`: full path to the generation file used for the reV runs. This can typically be found in the `config_aggregation.json` file from the reV run as `gen_fpath`. An exception is for bespoke wind runs, in which case this should point to the reV profiles. Needed for R2P.

#### 3. Run hourlize

Follow setup details [here](#running-hourlize).

#### 4. Synchronize shared directories

If you're copying the hourlize outputs back to the shared repository (`copy_to_shared=True`) you'll want to sync up the two shared folders, as the copy function currently only copies to one directory. 

When starting from the HPC be sure to open up permissions to the supply curve outputs you've just created (e.g., `chmod -R 777 UPV/2023_06_06_Update`). Then from your local computer use WinSCP or rsync to copy the files from Kestrel to nrelnas01:

```
rsync -aPu [username]@kestrel.nrel.gov://projects/shared-projects-reeds/reeds/Supply_Curve_Data/UPV/2023_11_02_LandCover /Volumes/ReEDS/Supply_Curve_Data/UPV
```

(back to [overview](#overview))

## Running hourlize
 
### run_hourlize.py 
The `run_hourlize.py` script serves as a wrapper for calling either `load.py` or `resource.py`. It does the following:
* Collect run(s) configuration settings from the relevant config files to build a consolidated config file for each run.
* Runs formatting on config file entries. 
  * Entries with {variable} in the text will have the {variable} text replaced with the value referenced by 'variable', which typically refers to another config entry or a file path.
  * Entries with {eval_expression} will evaluate 'expression' as a python expression; useful for creating lists using ranges.
  * Combines all configs into a single config.json sent to resource.py.
* Creates an output folder for the supply curve run in `hourlize/out/[casename]`, where casename is defined in the `cases.json file`.
* Creates a .sh or .bat script to run the case with a call to `resource.py`.
* Optionally submits jobs to the HPC or initiates the runs directly.

Example calls:
```
python run_hourlize.py load                  # run load.py
python run_hourlize.py resource              # run resource.py with default cases
python run_hourlize.py resource -c suffix    # run resource.py with cases from cases_suffix.json
python run_hourlize.py resource --local      # if on HPC run all cases sequentially on current node without batch submission to slurm
python run_hourlize.py resource --nosubmit   # if on HPC create launch scripts and input folders but don't submit runs
```
To see details on all command line arguments run `python run_hourlize.py -h`.

After setting up the run, if specified `run_hourlize.py` will launch the .sh or .bat file which performs the following call to `resource.py`: 
```
python resource.py --config /path/to/hourlize/[casename]/inputs/config.json
```

### Config jsons

Hourlize uses a set of json config files to provide information on how to process the supply curves. These files are located in `hourlize/inputs/configs`: 
* **Cases file** (`cases.json`): list of resource cases to run (currently not applicable to load.py)
* **Tech config** (`config_[tech].json`): tech specific settings for the `resource.py` script for upv, wind-ons, and wind-ofs 
* **Base config** (`config_base.json`): general hourlize settings (shared) as well as specific settings for the resource and load processes  

The `run_hourlize.py` process will generate a final config (`config.json`) from the relevant base and tech configs for each run, as depicted in the figure below. In general the settings in the `cases.json` file unique to each run while the settings in the tech and base configs aren't frequently changed. In the case of duplicated entries across configs hourlize uses the following order of precedence: cases > tech > base. 

![hourlize_configs](https://media.github.nrel.gov/user/1374/files/e4c990fa-fa12-47c2-9b0c-0d7bdbc255d0)

The `srun_template.sh` file is used to govern HPC submission settings. Update with your allocation, email, and any other slurm specifications before submitting jobs. There is also a command line argument to via `run_hourlize.py` for running jobs using the debug partition.

For more details on the meaning of the different config settings see the tables at the bottom of this README ([link](#details-on-config-file-settings)).

### Cases json

The cases json provides a list of resource supply curve cases to process. The default cases file (`case.json`) includes all supply curves typically needed for ReEDS for BA- and county-resolution runs. Users can also build their own cases file of the format `cases_[case_suffix].json`. 

Each entry should be given a `casename` for the supply curve run in the format [`tech`]\_[`access_case`]\_[`resolution`].
* Supported values for `tech`: upv, wind-ofs, wind-ons.
* Supported values for `resolution`: ba, county.
  * Make sure the entry for `resolution` aligns with the `reg_out_col` entry (ba: "reeds_ba", county: "cnty_fips").
* Typical values for `access_case`: reference, open, or limited.
  * Other values allowed but must match values in `access_case` column of the rev_paths file (typically at `ReEDS-2.0/inputs/supplycurvedata/rev_paths.csv` but can be specified in `config_base.json`). 

To link a case to a custom set of config files users can add entries for `config_base` and `config_tech` in the case defintion. For example, adding `config_base:test` would link that case to the settings in `config_base_test.json` instead of the typical `config_base.json` file.

Other key/value pairs in the `cases.json` file can also be used as subsetting variables for downselecting relevant rows from the corresponding rev_paths file. This can helpful when running hourlize for cases that don't just differ by access and tech. To use this add the key/value pair from the rev_paths_file to the relevant cases and to the list of `subsetvars` in the base config.

The current `cases.json` file in the repository contains all the settings to run the supply curves currently maintained by ReEDS. 

### Tips

* If you want the hourlize runs to be copied back the shared supply curve folder, set `copy_to_shared = true`.
  * Note: this script currently only copies to one of the shared folders (the HPC or nrelnas01), so you'll need to sync up the two after copying.
* By default hourlize is set up to copy outputs into the ReEDS repo (`copy_to_reeds = true`).
* `reg_out_col`  is typically either 'reeds_ba' for ReEDS regions or 'cnty_fips' for county-level supply curves, but can also be set to any column in the file specified by `reg_map_path` (which will be merged to the supply curve file via `reg_col`) or to a column in the supply curve file itself (if set to the same value as `reg_col`).

(back to [overview](#overview))

## Resource Logic (resource.py)
### Inputs
The main inputs to hourlize are reV outputs for a given reV scenario:
* `sc_path` (in rev_paths.csv): a supply curve csv file for a given technology, with rows for each resource site and columns of metadata.
* `rev_path` (in rev_paths.csv): A directory that contains h5 file(s) with hourly generation profiles for each site of the supply curve file for weather years 2007-2013.

### Outputs
By default, the outputs will be dumped to a subdirectory named `results` within `hourlize/out/[casename]`. In addition, with `copy_to_reeds` set to true (as is default), we'll copy the results to the ReEDS repo containing this hourlize directory, and with`copy_to_shared` set to true (not default), we'll copy to the shared drive (see Shared Drive Locations below).

* `{tech}_supply_curve.csv`: A supply curve with rows for each site and columns for region, class, available capacity, and costs. E.g. see `inputs/supplycurvedata/wind-ons_supply_curve-reference_ba.csv` (within ReEDS repo)
* `{tech}_exog_cap.csv`: Exogenous (built pre-2010) capacity with columns for region, site and year. This is not capacity builds in each year, but rather cumulative capacity of each existing site over time. E.g. see `inputs/capacitydata/wind-ons_exog_cap_reference_ba.csv` (within ReEDS repo)
* `{tech}_prescribed_builds.csv`: Capacity prescribed builds (2010 - present) with columns for region, year, capacity. This is the installed capacity in each year rather than cumulative capacity over time. E.g. see `inputs/capacitydata/wind-ons_prescribed_builds_reference_ba.csv` (within ReEDS repo)
* `{tech}_.h5`: An hourly (7 weather year) generation profile file with a separate profile for each region/class. E.g. see `inputs/variability/multi_year/wind-ons-reference_ba.h5` (within ReEDS repo)

### Shared Drive Locations
Hourlize resource inputs and outputs in the same places as the copies of the reV supply curves (see details [here](#1-copy-rev-runs-to-reeds-shared-directory)). Whereas the reV supply curves are stored within a folder called `reV`, the hourlize runs can be found directly in the corresponding tech folder (e.g., UPV, OFFSHORE, ONSHORE).

### Logic
The `resource.py` script follows the following logic (in order of execution):
1. `get_supply_curve_and_preprocess()`
    - The supply curve is filtered if necessary, based on `filter_cols`.
    - A 'region' column is added to the supply curve and filled with the selected regionality (`reg_out_col`).
    - Existing sites from a generator database (`existing_sites`) are assigned to supply curve points for exogenous and prescribed capacity outputs.
    - If we have minimum capacity thresholds for the supply curve points, these are applied to further filter the supply curve.
1. `add_classes()`
    - A 'class' column is added to the supply curve and filled with the associated class. Classes can be based on statically defined conditions for columns in the supply curve (`class_path`). Otherwise (or layered on top of static class definitions), dynamic classes can be assigned (`class_bin`=true) using a binning method (`class_bin_method`, e.g. "kmeans"), a number of bins (`class_bin_num`), and the supply curve column to bin (`class_bin_col`). The binning logic itself is in `get_bin()`. The current default classes for onshore wind and utility-scale PV are based on national k-means clustering of average annual capacity factor (where higher class number corresponds with higher annual CF). Offshore wind, by contrast, uses statically defined classes from `hourlize/inputs/resource/wind-ofs_resource_classes.csv`.
1. `add_cost()`
    - A column of overall supply curve costs is added to the supply curve (`supply_curve_cost_per_mw`), as well as certain components of that cost (e.g. `trans_adder_per_mw` and `capital_adder_per_MW`). Logic for these costs depends on `tech`, and the value of `cost_out` in config (e.g. `combined_eos_trans` for onshore wind).
1. `save_sc_outputs()`
    - Supply curve outputs are saved (`{tech}_supply_curve.csv`) as well as exogenous capacity (`{tech}_exog_cap.csv`), which is built pre-2010, and prescribed builds (`{tech}_prescribed_builds.csv`), which are built between 2010 and present day.
1. `get_profiles_allyears_weightedave()`
    - The hourly generation profiles are gathered, and capacity-weighted average profiles are calculated for each region/class.
1. `shift_timezones()`
    - Roll the hourly profiles from `resource_source_timezone` to `output_timezone`.
1. `save_time_outputs()`
    - Save the weighted average profiles by region/class to a `{tech}.h5` file.
1. `map_supplycurve()`
    - Create output maps for supply curve
1. `copy_outputs()`
    - Copy outputs from the new directory within hourlize/out to the corresponding input files in the ReEDS repo (`copy_to_reeds`) and/or shared drive (`copy_to_shared`)

## Load Logic (load.py, THIS SECTION IS OUTDATED)
* Hourly PLEXOS region load data is first converted into ReEDS BA-level data by `plexos_to_reeds/plexos_to_reeds.py`
   * See `plexos_to_reeds/README.md` for more details
1. If specified, we reduce the hourly data to one year.
1. If specified, we remove the final day from leap years.
1. If specified, we shift the data into local time of each BA.
1. If specified, we calibrate each year of hourly data to EIA 2010 load data by state combined with load participation factors by BA. These load participation factors are from heritage ReEDS load inputs, which I believe were derived from Ventyx 2006 county-level load data.
1. For each BA we calculate average load by timeslice and peak load by season.
1. The load profiles, means by timeslice, and peaks by season are sent to a new folder in `out/`
* Current inputs and outputs are stored here: `\\nrelnas01\ReEDS\Supply_Curve_Data\LOAD\`

See comments in those files for more information.

(back to [overview](#overview))

## Details on config file settings

This section provides some descriptions and typical values for the settings in the config files (see [above](#config-jsons) for a general overview of these config files).

### Shared config		
| Setting | Description | Default |   
| :------ | :---------- | :------ |   
|	compression_opts 	|	 file compression options. can select from 0-9: 0 is faster and larger, 9 is slower and smaller, 4 is default	|	4	
|	filetype 	|	 output filetype: 'csv' or 'h5'. Note that load.py uses h5 regardless for default (historical) and EER load	|	 'h5'	
|	output_timezone 	      |	'local' means convert to local standard time of the respective region. UTC is 0. EST is -5.	|	 'local' 	
|	select_year 	|	this is the year used for load and resource profile-derived inputs, although the profile outputs may still be multiyear (see hourly_out_years)	|	2012	
|	start_1am 	|	False means start at 12am	|	 True 	
|		|		|		

### Resource config

| Setting | Description | Default |   
| :------ | :---------- | :------ |   
|	bin_group_cols 	|		|	 ['region','class']	
|	bin_method 	|	'equal_cap_man', 'equal_cap_cut'. 'kmeans' currently commented out to prevent numpy depracation warnings from sklearn.	|	 'equal_cap_cut' 		
|	copy_to_reeds 	|	Copy hourlize outputs to ReEDS inputs	|	 True 	
|	copy_to_shared 	|	Copy hourlize outputs to the shared drive	|	 False 	
|	driver 	|	'H5FD_CORE', None. H5FD_CORE will load the h5 into memory for better perforamnce, but None must be used for low-memory machines.	|	 'H5FD_CORE' 	
|	dtype 	|	data type used to save hourly profiles	|	 np.float16 	
|	existing_sites 	|	None or path to file with existing capacity	|	 this_dir_path + '../inputs/capacitydata/ReEDS_generator_database_final_EIA-NEMS.csv' 	
|	gather_method 	|	 'list', 'slice', 'smart'. This setting will take a slice of profile ids from the min to max, rather than using a list of ids, for improved performance when ids are close together for each group.	|	 'smart' 	
|	hourly_out_years 	|	e.g. [2012] for just 2012 or list(range(2007,2014)) for 2007-2013	|	 list(range(2007,2014)) 
| inputfiles	| list of files to copy over to hourlize input folder | ["reg_map_file", "class_path"]
|	reg_col 	|	region column from supply curve file (sc_path). 'cnty_fips' for county, could be 'model_region' if it is already in the supply curve.	|	 'cnty_fips' 	
|	reg_map_path 	|	This file maps counties to reeds regions and bas.	|	 this_dir_path + 'inputs/resource/county_map.csv' 		
|	resource_source_timezone 	|	UTC would be 0, Eastern standard time would be -5	|	0	
|	start_year 	|	The start year of the model, for existing and sites purposes.	|	2010	
|	state_abbrev 	|		|	 this_dir_path + 'inputs/resource/state_abbrev.csv'	
|   subsetvars | list of columns in the rev_paths file to use to select the appropriate rev_path   | ['tech', 'access_case'] | 
|	subtract_exog 	|	Indicate whether to remove exogenous (pre-start_year) capacity from the supply curve [default False]	|	 False 	
|	test_filters 	|	dictionary definiting a set of columns and the corresponding values to subset the supply curve on	|	 {'region':['p97', 'p98']}	
|	test_mode 	|	This limits the supply curve based on the dictionary defined in test_filers |	 False 	

### Tech configs

| Setting | Description | Default |   
| :------ | :---------- | :------ |   
|	cost_out 	|	'combined_eos_trans' is a computed column from economies of scale and transmission cost. To turn off economies of scale, use 'trans_cap_cost'. 'combined_off_ons_trans' is a computed column from offshore (array and export) as well as onshore transmission cost.  	|	 upv, wind-ons: 'combined_eos_trans'<br>wind-ofs: 'combined_off_ons_trans' |
|	capacity_col 	|	Format of the supply curve capacity column	|	 upv: 'capacity_mw_{upv_type}'<br>wind-ofs: 'capacity_mw'<br>wind-ons: 'capacity'  	
|	class_bin 	|	This will layer dynamic bins. If class_path != None, we add region-specific bins for each of the classes defined in class_path.	|	 upv, wind-ons: true<br>wind-ofs: false
|	class_bin_col 	|	The column to be binned (only used if class_bin = True)	|	 upv: 'mean_cf_{upv_type}'<br>wind-ofs,wind-ons: 'mean_cf'
|	class_bin_method 	|	The bin method, either 'kmeans', 'equal_cap_cut', or 'equal_cap_man' (only used if class_bin = True) 	|	 'kmeans' 	
|	class_bin_num 	|	The number of class bins (only used if class_bin = True) 	|	upv: 10<br> wind-ofs, wind-ons: 10
|	class_path 	|	null or path to class definitions file	|	 upv, wind-ons: null<br>wind-ofs: {hourlizepath}/inputs/resource/{tech}_resource_classes.csv  |
|	cost_adder_components 	|	Supply curve cost columns to carry over to outputs	|	 upv, wind-ons: ['trans_adder_per_MW', 'capital_adder_per_MW']<br>wind-ofs: []	
|	distance_cols 	|	dist_to_coast is currently in meters, so we convert to km in get_supply_curve_and_preprocess()	|	 upv, wind-ons: ['dist_km','reinforcement_dist_km']<br>wind-ofs: ['dist_km','dist_to_coast','reinforcement_dist_km'] 	
|	filter_cols 	|	{} means use the entire dataframe; {'offshore':['=',0]} means filter the supply curve to rows for which offshore is 0.	|	 upv, wind-ons: {}<br>wind-ofs: {'offshore':['=',0]} 
|	min_cap 	|	MW  (LBNL utility-scale solar report & NREL PV cost benchmarks define utility-scale as ≥5 MW)	|	upv: 5, wind-ofs: 15, wind-ons: 0	
|	profile_dir 	|	Use '' if .h5 files are in same folder as metadata, else point to them, e.g. f'../{rev_prefix}'	|	 upv: '{access_case}_{upv_type}'<br>wind-ons, wind-ofs: '' 	
|	profile_dset 	|	Name of hourly profiles in reV runs	|	 'rep_profiles_0'	
|	profile_file_format 	|	Format for hourly profiles filename. Note: unused if single_profile	|	 upv: {rev_prefix}_rep-profiles<br>wind-ons, wind-ofs: '' 	
|	profile_id_col 	|	Unique identifier for reV supply curve and profiles	|	 'sc_point_gid'	
|	profile_weight_col 	|	Name of column to use for weighted average of profiles. Using 'capacity' will link to whatever value is specified by 'capacity_col' 	|	 'capacity'	
|	single_profile 	|	single_profile has different columns and a single h5 profile file (for all years).	|	 upv, wind-ofs: false, wind-ons: true 	
|	upv_type 	|	type of UPV capacity and profiles to use; options are 'ac' and 'dc' 	|	 upv: 'dc'; wind-ons, wind-ofs: null
|rev_jsons | list of reV json files to copy over | upv: ["config_aggregation.json", "config_pipeline.json", "config_supply-curve.json", "{access_case}_{upv_type}/config_rep-profiles_aggprof.json"] <br>wind-ofs: ["config_aggregation.json", "config_pipeline.json", "config_supply-curve.json", "config_rep-profiles.json"]<br>wind-ons: ["config_pipeline.json", "config_supply-curve.json", "sam.json", "config_bespoke.json"]


### Load config		

| Setting | Description | Default |   
| :------ | :---------- | :------ |      
|	aeo_default 	|	To calibrate data pre-use_default_before_yr	|	  os.path.join('..','inputs','loaddata','demand_AEO_2023_reference.csv') 	
|	ba_frac_path 	|	These are fractions of state load in each ba, unused if calibrate_path is False	|	 os.path.join(this_dir_path,'inputs','load','load_participation_factors_st_to_ba.csv') 	
|	ba_timezone_path 	|	Should this be used for resource too, rather than site timezone?	|	 os.path.join(this_dir_path,'inputs','load','ba_timezone.csv') 	
|	calibrate_path 	|	Enter path to calibration file or 'False' to leave uncalibrated	|	 os.path.join(this_dir_path,'inputs','load','EIA_loadbystate.csv') 	
|	calibrate_type 	|	either 'one_year' or 'all_years'. Unused if calibrate_path is False. 'one_year' means to only calibrate one year to the EIA data and then apply the same scaling factor to all years. 'all_years' will calibrate all each year to the EIA data.	|	 'all_years' 	
|	calibrate_year 	|	This is the year that the outputs of load.py represent, based on the EIA calibration year. Unused if calibrate_path is False.	|	2010	
|	dtypeLoad 	|	Use int if the file size ends up too large.	|	 np.float32 	
|	hierarchy_path 	|	Used for both calibration and variability outputs	|	 os.path.join(this_dir_path,'inputs','load','hierarchy.csv') 	
|	hourly_out_years 	|	e.g. list(range(2021,2051)) for 2021-2050; must be a list even if only one year	|	 list(range(2021,2051)) 	
|	hourly_process 	|	If False, skip all hourly processing steps	|	 True 	
|	load_source 	|	The load source file's first column should be datetime, starting at Jan 1, 12am, stepping by 1 hour, and one column for each BA. It should be a csv or a compressed csv.	|	 '//nrelnas01/ReEDS/Supply_Curve_Data/LOAD/2020_Update/plexos_to_reeds/outputs/load_hourly_ba_EST.csv' 	
|	load_source_hr_type 	|	Use 'end' if load_source data hour-ending or 'begin' for hour-beginning. For instantaneous use 'end'. For EER load use 'begin'.	|	 'begin' 	
|	load_source_timezone 	|	UTC would be 0, Eastern standard time would be -5	|	-5	
|	truncate_leaps 	|	Truncate leap years. This currently needs to be True for mapping properly to timeslices.	|	 True 	
|	us_only 	|	Run only US BAs.	|	 True 	
|	use_default_before_yr 	|	Either False or a year. If set to a year, this will pull in ReEDS default load data before that year (2012 weather year)	|	2021	

(back to [overview](#overview))