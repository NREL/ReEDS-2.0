# Value Streams
Created by: Matt Mowers, 2018-04-12

## Requirements
* Python (version 2.7)
* gdxpds
* pandas
Note that these requirements are satisfied on Orion and Scorpio.

## Summary/Outputs
When the `pythonValueStreams` switch is on in ReEDS, `valuestreams.py` will be called after each solve. It in turn calls `get_value_streams()` from `raw_value_streams.py`, which uses the ReEDS mps file along with the gdx solution file to calculate value streams. `valuestreams.py` does further processing to categorize and group variables and constraints, and produces these outputs in the `out/` directory:
* *valuestreams_chosen.csv*: Value streams for techs that were built
* *valuestreams_potential.csv*: Value streams for all potential plants, whether built or not
* *load_pca_chosen.csv*: Contributions to load_pca (MWh) for chosen plants
* *load_pca_potential.csv*: Contributions to load_pca (MWh/kW) for potential plants
    * Note: Currently only covers wind, upv, and dupv
* *levels_potential.csv*: MW of potential plants that were chosen.
* *available_potential.csv*: The solar and wind resource supply curve bins that are available during each solve, i.e. where there is still available capacity.

At the end of the run, these three files are copied to the run folder in the `gdxfiles/valuestreams/` directory. Bokehpivot may subsequently be used to visualize the results.

To learn more about the `valuestreams.py` file, see comments in that file.

## Adding/Editing Variables
Variables are configured in *var_map.csv*. Only the variables listed in this file will be analyzed. These are the columns:
* *var_name*: The name of the variable in GAMS, lowercased.
* *tech*: Either the name of the tech or the index of the tech set.
* *reg_type*: The regional level, e.g. i or n.
* *reg*: The index of the region set.
* *m*: The index of the timeslice set, if this variable has a timeslice set
* *obj_type*: The cost category to be used for this variables contribution to the objective function
* *new_old*: Either 'new', 'old', 'mixed', or 'retire'
* *potential_group*: The name of the group to be used in the potential plants analysis, if applicable. Variables with the same group name are grouped and analyzed together
    * Note: Only capacity variables are used for convential plants. Generation costs and values show up as `cap_fo_po`, but currently are not disaggregated beyond that.
* *var_set_names*: For potential plants analysis, the full dot separated set names. This is used to combine the variables of a group appropriately. Notes:
    * Names of sets do not have to match their names in GAMS. But they must be consistent between all the variables of a potential_group.
    * Currently, do not use i or n as the set identifier names, or the code will break because of column name collisions. Use j,i2,p,n2 etc instead.
    * We maybe should refactor by adding `var_set_names` for all variables. This may allow us to remove tech, reg_type, reg, and m columns, and may fix the issue in the previous bullet as well.
* *potential_base*: For potential plants analysis, the name of the variable to be used as the base variable. The outputs will have the set dimensions of the base variable.

## Adding/Editing Constraints
Constraints are configured in *con_map.csv*. This file is used to map constraints to categories. All constraints not listed here are mapped to the "other" category in the results. These are the columns:
* *con_name*: The name of the constraint in GAMS, lowercased.
* *type*: The category to which the constraint is mapped
* *m_con*: The index of the timeslice set, if this constraint has a timeslice set. When variables don't have timeslices, the script will apply the constraint's timeslices instead.

## Extracting raw value streams
`raw_value_streams.py` contains functions for extracting the data from any combination of an mps file and corresponding solution gdx file. See comments in this file.
