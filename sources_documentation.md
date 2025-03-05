# ReEDS 2.0

## Table of Contents


  - ### [](#) 
    - #### [hourlize](#hourlize) 
      - ##### [inputs](#hourlize/inputs) 
      - ##### [plexos_to_reeds](#hourlize/plexos_to_reeds) 
      - ##### [tests](#hourlize/tests) 
    - #### [inputs](#inputs) 
      - ##### [canada_imports](#inputs/canada_imports) 
      - ##### [capacity_exogenous](#inputs/capacity_exogenous) 
      - ##### [climate](#inputs/climate) 
      - ##### [consume](#inputs/consume) 
      - ##### [ctus](#inputs/ctus) 
      - ##### [degradation](#inputs/degradation) 
      - ##### [demand_response](#inputs/demand_response) 
      - ##### [dgen_model_inputs](#inputs/dgen_model_inputs) 
      - ##### [disaggregation](#inputs/disaggregation) 
      - ##### [emission_constraints](#inputs/emission_constraints) 
      - ##### [financials](#inputs/financials) 
      - ##### [fuelprices](#inputs/fuelprices) 
      - ##### [geothermal](#inputs/geothermal) 
      - ##### [growth_constraints](#inputs/growth_constraints) 
      - ##### [hydro](#inputs/hydro) 
      - ##### [load](#inputs/load) 
      - ##### [national_generation](#inputs/national_generation) 
      - ##### [plant_characteristics](#inputs/plant_characteristics) 
      - ##### [reserves](#inputs/reserves) 
      - ##### [sets](#inputs/sets) 
      - ##### [shapefiles](#inputs/shapefiles) 
      - ##### [state_policies](#inputs/state_policies) 
      - ##### [storage](#inputs/storage) 
      - ##### [supply_curve](#inputs/supply_curve) 
      - ##### [techs](#inputs/techs) 
      - ##### [transmission](#inputs/transmission) 
      - ##### [upgrades](#inputs/upgrades) 
      - ##### [userinput](#inputs/userinput) 
      - ##### [valuestreams](#inputs/valuestreams) 
      - ##### [variability](#inputs/variability) 
      - ##### [waterclimate](#inputs/waterclimate) 
    - #### [postprocessing](#postprocessing) 
      - ##### [air_quality](#postprocessing/air_quality) 
      - ##### [bokehpivot](#postprocessing/bokehpivot) 
      - ##### [combine_runs](#postprocessing/combine_runs) 
      - ##### [land_use](#postprocessing/land_use) 
      - ##### [plots](#postprocessing/plots) 
      - ##### [retail_rate_module](#postprocessing/retail_rate_module) 
      - ##### [reValue](#postprocessing/reValue) 
      - ##### [tableau](#postprocessing/tableau) 
    - #### [preprocessing](#preprocessing) 
      - ##### [atb_updates_processing](#preprocessing/atb_updates_processing) 
    - #### [reeds2pras](#reeds2pras) 
      - ##### [test](#reeds2pras/test) 
    - #### [ReEDS_Augur](#ReEDS_Augur) 
    - #### [tests](#tests) 
      - ##### [data](#tests/data) 


## Input Files
Note: If you see a '#' before a header it means there may be further subdirectories within it but the Markdown file is only capable of showing 6 levels, so the header sizes are capped to that level and they cannot be any smaller to visually reflect the further subdirectory hierarchy.


## []() <a name=''></a>
  - [cases.csv](/cases.csv)
    - **File Type:** Switches file
    - **Description:** Contains the configuration settings for the ReEDS run(s).
    - **Dollar year:** 2004

    - **Citation:** [(https://github.nrel.gov/ReEDS/ReEDS-2.0/blob/38e6610a8c6a92291804598c95c11b707bf187b9/cases.csv)]
---

  - [cases_github.csv](/cases_github.csv)
---

  - [cases_hourly.csv](/cases_hourly.csv)
    - **Description:** This cases file contains the settings to demonstrate temporal flexibility (hourly) of ReEDS.
---

  - [cases_small.csv](/cases_small.csv)
    - **Description:** Contains settings to run ReEDS at a smaller scale to test operability of the ReEDS model. Turns off several technologies and reduces the model size to significantly improve solve times.
---

  - [cases_smaller.csv](/cases_smaller.csv)
    - **Description:** Another cases file which reduces the size of the model by reducing some constraints and operates at the largest spatial hierarchy to favor faster runtimes.
---

  - [cases_spatialflex.csv](/cases_spatialflex.csv)
    - **Description:** Contains sample scenarios that use the spatial flexibility capabilities
---

  - [cases_standardscenarios.csv](/cases_standardscenarios.csv)
    - **File Type:** StdScen Cases file
    - **Description:** Contains the configuration settings for the Standard Scenarios ReEDS runs.
---

  - [cases_test.csv](/cases_test.csv)
    - **Description:** Contains the configuration settings for doing test runs including the default Pacific census division test case.
---

  - [e_report_params.csv](/e_report_params.csv)
    - **Description:** Contains a parameter list used in the model along with descriptions of what they are and units used.
---

  - [runfiles.csv](/runfiles.csv)
    - **Description:** Contains the locations of input data that is copied from the repository into the runs folder for each respective case.
---

  - [sources.csv](/sources.csv)
    - **Description:** CSV file containing a list of all input files (csv, h5, csv.gz)
---


### [hourlize](hourlize) <a name='hourlize'></a>

#### [inputs](hourlize/inputs) <a name='hourlize/inputs'></a>

##### [load](hourlize/inputs/load) <a name='hourlize/inputs/load'></a>
  - [ba_timezone.csv](/hourlize/inputs/load/ba_timezone.csv)
    - **Description:** Contains timezone information for BAs with respect to GMT.
    - **Indices:** r
---

  - [EIA_2010loadbystate.csv](/hourlize/inputs/load/EIA_2010loadbystate.csv)
    - **Description:** Contains 2010 EIA load information (GWh) with respect to each state in the US.
    - **Indices:** r
---

  - [EIA_loadbystate.csv](/hourlize/inputs/load/EIA_loadbystate.csv)
    - **Description:** Contains historical (2010-2022) EIA load information (GWh) with respect to each state in the US.
    - **Indices:** t,r
---

  - [load_participation_factors_st_to_ba.csv](/hourlize/inputs/load/load_participation_factors_st_to_ba.csv)
    - **Description:** Contains load participation factors for each of the BAs
    - **Indices:** r
---


##### [resource](hourlize/inputs/resource) <a name='hourlize/inputs/resource'></a>
  - [egs_resource_classes.csv](/hourlize/inputs/resource/egs_resource_classes.csv)
---

  - [fair_market_value.csv](/hourlize/inputs/resource/fair_market_value.csv)
    - **Description:** Contains estimates of fair market land value in $ per hectare for each reV supply curve site

    - **Citation:** [(Provided by Anthony Lopez in June 2023)]
---

  - [geohydro_resource_classes.csv](/hourlize/inputs/resource/geohydro_resource_classes.csv)
---

  - [rev_sc_columns.csv](/hourlize/inputs/resource/rev_sc_columns.csv)
---

  - [state_abbrev.csv](/hourlize/inputs/resource/state_abbrev.csv)
    - **Description:** Contains state names and codesfor the US.
---

  - [upv_resource_classes.csv](/hourlize/inputs/resource/upv_resource_classes.csv)
    - **Description:** Contains information related to UPV class segregation based on mean irradiance levels.
---

  - [wind-ofs_resource_classes.csv](/hourlize/inputs/resource/wind-ofs_resource_classes.csv)
    - **File Type:** supply curve input
    - **Description:** Contains information related to Offshore wind class segregation and turbine type (fixed vs floating) based on water depth and site lcoe
    - **Indices:** n/a
---

  - [wind-ons_resource_classes.csv](/hourlize/inputs/resource/wind-ons_resource_classes.csv)
    - **Description:** Contains information related to Onshore wind class segregation based on mean wind speeds.
---


#### [plexos_to_reeds](hourlize/plexos_to_reeds) <a name='hourlize/plexos_to_reeds'></a>

##### [inputs](hourlize/plexos_to_reeds/inputs) <a name='hourlize/plexos_to_reeds/inputs'></a>
  - [month_to_season.csv](/hourlize/plexos_to_reeds/inputs/month_to_season.csv)
    - **Description:** Maps the season to month in a year
---

  - [plexos_node_monthly_lpf_ercot.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_monthly_lpf_ercot.csv)
---

  - [plexos_node_seasonal_lpf_wi.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_seasonal_lpf_wi.csv)
---

  - [plexos_node_to_reeds_ba.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_to_reeds_ba.csv)
---

  - [plexos_node_to_zone_ei.csv](/hourlize/plexos_to_reeds/inputs/plexos_node_to_zone_ei.csv)
---


#### [tests](hourlize/tests) <a name='hourlize/tests'></a>

##### [data](hourlize/tests/data) <a name='hourlize/tests/data'></a>

###### [r2r_expanded](hourlize/tests/data/r2r_expanded) <a name='hourlize/tests/data/r2r_expanded'></a>

####### [upv_case_1](hourlize/tests/data/r2r_expanded/upv_case_1) <a name='hourlize/tests/data/r2r_expanded/upv_case_1'></a>

####### [expected_results](hourlize/tests/data/r2r_expanded/upv_case_1/expected_results) <a name='hourlize/tests/data/r2r_expanded/upv_case_1/expected_results'></a>
  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/expected_results/df_sc_out_upv_reduced.csv)
---


####### [reeds](hourlize/tests/data/r2r_expanded/upv_case_1/reeds) <a name='hourlize/tests/data/r2r_expanded/upv_case_1/reeds'></a>

####### [inputs_case](hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case) <a name='hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case'></a>
  - [hierarchy_original.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/inputs_case/switches.csv)
---


####### [outputs](hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs) <a name='hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs'></a>
  - [cap.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/reeds/outputs/systemcost.csv)
---


####### [supply_curves](hourlize/tests/data/r2r_expanded/upv_case_1/supply_curves) <a name='hourlize/tests/data/r2r_expanded/upv_case_1/supply_curves'></a>
  - [upv_supply_curve_raw_unpacked.csv](/hourlize/tests/data/r2r_expanded/upv_case_1/supply_curves/upv_supply_curve_raw_unpacked.csv)
---


####### [upv_case_2](hourlize/tests/data/r2r_expanded/upv_case_2) <a name='hourlize/tests/data/r2r_expanded/upv_case_2'></a>

####### [expected_results](hourlize/tests/data/r2r_expanded/upv_case_2/expected_results) <a name='hourlize/tests/data/r2r_expanded/upv_case_2/expected_results'></a>
  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/expected_results/df_sc_out_upv_reduced.csv)
---


####### [reeds](hourlize/tests/data/r2r_expanded/upv_case_2/reeds) <a name='hourlize/tests/data/r2r_expanded/upv_case_2/reeds'></a>

####### [inputs_case](hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case) <a name='hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case'></a>
  - [hierarchy_original.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/inputs_case/switches.csv)
---


####### [outputs](hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs) <a name='hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs'></a>
  - [cap.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/reeds/outputs/systemcost.csv)
---


####### [supply_curves](hourlize/tests/data/r2r_expanded/upv_case_2/supply_curves) <a name='hourlize/tests/data/r2r_expanded/upv_case_2/supply_curves'></a>
  - [upv_supply_curve_raw_unpacked.csv](/hourlize/tests/data/r2r_expanded/upv_case_2/supply_curves/upv_supply_curve_raw_unpacked.csv)
---


####### [upv_case_3](hourlize/tests/data/r2r_expanded/upv_case_3) <a name='hourlize/tests/data/r2r_expanded/upv_case_3'></a>

####### [expected_results](hourlize/tests/data/r2r_expanded/upv_case_3/expected_results) <a name='hourlize/tests/data/r2r_expanded/upv_case_3/expected_results'></a>
  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/expected_results/df_sc_out_upv_reduced.csv)
---


####### [reeds](hourlize/tests/data/r2r_expanded/upv_case_3/reeds) <a name='hourlize/tests/data/r2r_expanded/upv_case_3/reeds'></a>

####### [inputs_case](hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case) <a name='hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case'></a>
  - [hierarchy_original.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/inputs_case/switches.csv)
---


####### [outputs](hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs) <a name='hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs'></a>
  - [cap.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/reeds/outputs/systemcost.csv)
---


####### [supply_curves](hourlize/tests/data/r2r_expanded/upv_case_3/supply_curves) <a name='hourlize/tests/data/r2r_expanded/upv_case_3/supply_curves'></a>
  - [upv_supply_curve_raw_unpacked.csv](/hourlize/tests/data/r2r_expanded/upv_case_3/supply_curves/upv_supply_curve_raw_unpacked.csv)
---


####### [wind-ons_case_1](hourlize/tests/data/r2r_expanded/wind-ons_case_1) <a name='hourlize/tests/data/r2r_expanded/wind-ons_case_1'></a>

####### [expected_results](hourlize/tests/data/r2r_expanded/wind-ons_case_1/expected_results) <a name='hourlize/tests/data/r2r_expanded/wind-ons_case_1/expected_results'></a>
  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/expected_results/df_sc_out_wind-ons_reduced.csv)
---


####### [reeds](hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds) <a name='hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds'></a>

####### [inputs_case](hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case) <a name='hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case'></a>
  - [hierarchy_original.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/switches.csv)
---


####### [supplycurve_metadata](hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/supplycurve_metadata) <a name='hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/supplycurve_metadata'></a>
  - [rev_supply_curves.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/inputs_case/supplycurve_metadata/rev_supply_curves.csv)
---


####### [outputs](hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs) <a name='hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs'></a>
  - [cap.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/reeds/outputs/systemcost.csv)
---


####### [supply_curves](hourlize/tests/data/r2r_expanded/wind-ons_case_1/supply_curves) <a name='hourlize/tests/data/r2r_expanded/wind-ons_case_1/supply_curves'></a>
  - [wind-ons_supply_curve_raw.csv](/hourlize/tests/data/r2r_expanded/wind-ons_case_1/supply_curves/wind-ons_supply_curve_raw.csv)
---


###### [r2r_from_config](hourlize/tests/data/r2r_from_config) <a name='hourlize/tests/data/r2r_from_config'></a>

####### [expected_results](hourlize/tests/data/r2r_from_config/expected_results) <a name='hourlize/tests/data/r2r_from_config/expected_results'></a>

####### [multiple_priority_inputs](hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs) <a name='hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs'></a>
  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_wind-ons_reduced.csv)
---


####### [no_bin_constraint](hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint) <a name='hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint'></a>
  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_wind-ons_reduced.csv)
---


####### [priority_inputs](hourlize/tests/data/r2r_from_config/expected_results/priority_inputs) <a name='hourlize/tests/data/r2r_from_config/expected_results/priority_inputs'></a>
  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_wind-ons_reduced.csv)
---


###### [r2r_integration](hourlize/tests/data/r2r_integration) <a name='hourlize/tests/data/r2r_integration'></a>

####### [expected_results](hourlize/tests/data/r2r_integration/expected_results) <a name='hourlize/tests/data/r2r_integration/expected_results'></a>
  - [df_sc_out_upv.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_upv.csv)
---

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_upv_reduced_simul_fill.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_upv_reduced_simul_fill.csv)
---

  - [df_sc_out_wind-ofs.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ofs.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ons.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_wind-ons_reduced.csv)
---


####### [reeds](hourlize/tests/data/r2r_integration/reeds) <a name='hourlize/tests/data/r2r_integration/reeds'></a>

####### [inputs_case](hourlize/tests/data/r2r_integration/reeds/inputs_case) <a name='hourlize/tests/data/r2r_integration/reeds/inputs_case'></a>
  - [hierarchy_original.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/switches.csv)
---


####### [outputs](hourlize/tests/data/r2r_integration/reeds/outputs) <a name='hourlize/tests/data/r2r_integration/reeds/outputs'></a>
  - [cap.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_integration/reeds/outputs/systemcost.csv)
---


####### [supply_curves](hourlize/tests/data/r2r_integration/supply_curves) <a name='hourlize/tests/data/r2r_integration/supply_curves'></a>

####### [upv_reference](hourlize/tests/data/r2r_integration/supply_curves/upv_reference) <a name='hourlize/tests/data/r2r_integration/supply_curves/upv_reference'></a>

####### [results](hourlize/tests/data/r2r_integration/supply_curves/upv_reference/results) <a name='hourlize/tests/data/r2r_integration/supply_curves/upv_reference/results'></a>
  - [upv_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/upv_reference/results/upv_supply_curve_raw.csv)
---


####### [wind-ofs_0_open_moderate](hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate'></a>

####### [results](hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results'></a>
  - [wind-ofs_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results/wind-ofs_supply_curve_raw.csv)
---


####### [wind-ons_reference](hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference'></a>

####### [results](hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference/results) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference/results'></a>
  - [wind-ons_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference/results/wind-ons_supply_curve_raw.csv)
---


###### [r2r_integration_geothermal](hourlize/tests/data/r2r_integration_geothermal) <a name='hourlize/tests/data/r2r_integration_geothermal'></a>

####### [expected_results](hourlize/tests/data/r2r_integration_geothermal/expected_results) <a name='hourlize/tests/data/r2r_integration_geothermal/expected_results'></a>
  - [df_sc_out_egs_allkm.csv](/hourlize/tests/data/r2r_integration_geothermal/expected_results/df_sc_out_egs_allkm.csv)
---

  - [df_sc_out_egs_allkm_reduced.csv](/hourlize/tests/data/r2r_integration_geothermal/expected_results/df_sc_out_egs_allkm_reduced.csv)
---

  - [df_sc_out_geohydro_allkm.csv](/hourlize/tests/data/r2r_integration_geothermal/expected_results/df_sc_out_geohydro_allkm.csv)
---

  - [df_sc_out_geohydro_allkm_reduced.csv](/hourlize/tests/data/r2r_integration_geothermal/expected_results/df_sc_out_geohydro_allkm_reduced.csv)
---


####### [reeds](hourlize/tests/data/r2r_integration_geothermal/reeds) <a name='hourlize/tests/data/r2r_integration_geothermal/reeds'></a>

####### [inputs_case](hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case) <a name='hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case'></a>
  - [hierarchy_original.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/hierarchy_original.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/maxage.csv)
---

  - [rev_paths.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/rev_paths.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/inputs_case/switches.csv)
---


####### [outputs](hourlize/tests/data/r2r_integration_geothermal/reeds/outputs) <a name='hourlize/tests/data/r2r_integration_geothermal/reeds/outputs'></a>
  - [cap.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_integration_geothermal/reeds/outputs/systemcost.csv)
---


####### [supply_curves](hourlize/tests/data/r2r_integration_geothermal/supply_curves) <a name='hourlize/tests/data/r2r_integration_geothermal/supply_curves'></a>
  - [egs_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration_geothermal/supply_curves/egs_supply_curve_raw.csv)
---

  - [geohydro_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration_geothermal/supply_curves/geohydro_supply_curve_raw.csv)
---


### [inputs](inputs) <a name='inputs'></a>
  - [county2zone.csv](/inputs/county2zone.csv)
---

  - [hierarchy.csv](/inputs/hierarchy.csv)
---

  - [hierarchy_agg1.csv](/inputs/hierarchy_agg1.csv)
---

  - [hierarchy_agg2.csv](/inputs/hierarchy_agg2.csv)
---

  - [hierarchy_agg3.csv](/inputs/hierarchy_agg3.csv)
---

  - [modeledyears.csv](/inputs/modeledyears.csv)
---

  - [scalars.csv](/inputs/scalars.csv)
---

  - [tech-subset-table.csv](/inputs/tech-subset-table.csv)
    - **Description:** Maps all technologies to specific subsets of technologies
---


#### [canada_imports](inputs/canada_imports) <a name='inputs/canada_imports'></a>
  - [can_exports.csv](/inputs/canada_imports/can_exports.csv)
    - **File Type:** Input
    - **Description:** Annual exports to Canada by BA
    - **Indices:** r,t
    - **Units:** MWh

---

  - [can_exports_szn_frac.csv](/inputs/canada_imports/can_exports_szn_frac.csv)
    - **File Type:** Input
    - **Description:** Fraction of annual exports to Canada by season
    - **Indices:** N/A
    - **Units:** rate (unitless)

---

  - [can_imports.csv](/inputs/canada_imports/can_imports.csv)
    - **File Type:** Input
    - **Description:** Annual imports from Canada by BA
    - **Indices:** r,t
    - **Units:** MWh

---

  - [can_imports_quarter_frac.csv](/inputs/canada_imports/can_imports_quarter_frac.csv)
    - **File Type:** Input
    - **Description:** Fraction of annual imports from Canada by season
    - **Indices:** N/A
    - **Units:** rate (unitless)

---


#### [capacity_exogenous](inputs/capacity_exogenous) <a name='inputs/capacity_exogenous'></a>
  - [cappayments.csv](/inputs/capacity_exogenous/cappayments.csv)
---

  - [cappayments_ba.csv](/inputs/capacity_exogenous/cappayments_ba.csv)
---

  - [demonstration_plants.csv](/inputs/capacity_exogenous/demonstration_plants.csv)
    - **File Type:** Prescribed capacity
    - **Description:** Nuclear-smr demonstration plants; active when GSw_NuclearDemo=1
    - **Indices:** t,r,i,coolingwatertech,ctt,wst,value

    - **Citation:** [(See 'notes' column in the file)]
    - **Units:** MW

---

  - [geohydro_allkm_exog_cap_reference.csv](/inputs/capacity_exogenous/geohydro_allkm_exog_cap_reference.csv)
---

  - [geohydro_allkm_prescribed_builds_reference.csv](/inputs/capacity_exogenous/geohydro_allkm_prescribed_builds_reference.csv)
---

  - [geohydro_exog_cap_reference_ba.csv](/inputs/capacity_exogenous/geohydro_exog_cap_reference_ba.csv)
---

  - [geohydro_exog_cap_reference_county.csv](/inputs/capacity_exogenous/geohydro_exog_cap_reference_county.csv)
---

  - [geohydro_prescribed_builds_reference_ba.csv](/inputs/capacity_exogenous/geohydro_prescribed_builds_reference_ba.csv)
---

  - [geohydro_prescribed_builds_reference_county.csv](/inputs/capacity_exogenous/geohydro_prescribed_builds_reference_county.csv)
---

  - [interconnection_queues.csv](/inputs/capacity_exogenous/interconnection_queues.csv)
---

  - [ReEDS_generator_database_final_EIA-NEMS.csv](/inputs/capacity_exogenous/ReEDS_generator_database_final_EIA-NEMS.csv)
    - **File Type:** Input
    - **Description:** EIA-NEMS database of existing generators
---

  - [rsmap.csv](/inputs/capacity_exogenous/rsmap.csv)
    - **Description:** Mapping for BAs to resource regions
    - **Indices:** r,rs
---

  - [upv_exog_cap_limited_ba.csv](/inputs/capacity_exogenous/upv_exog_cap_limited_ba.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) UPV capacity with limited siting assumptions at BA resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [upv_exog_cap_limited_county.csv](/inputs/capacity_exogenous/upv_exog_cap_limited_county.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) UPV capacity with limited siting assumptions at county resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [upv_exog_cap_open_ba.csv](/inputs/capacity_exogenous/upv_exog_cap_open_ba.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) UPV capacity with open siting assumptions at BA resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [upv_exog_cap_open_county.csv](/inputs/capacity_exogenous/upv_exog_cap_open_county.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) UPV capacity with open siting assumptions at county resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [upv_exog_cap_reference_ba.csv](/inputs/capacity_exogenous/upv_exog_cap_reference_ba.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) UPV capacity with reference siting assumptions at BA resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [upv_exog_cap_reference_county.csv](/inputs/capacity_exogenous/upv_exog_cap_reference_county.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) UPV capacity with reference siting assumptions at county resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [upv_prescribed_builds_limited_ba.csv](/inputs/capacity_exogenous/upv_prescribed_builds_limited_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with limited siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [upv_prescribed_builds_limited_county.csv](/inputs/capacity_exogenous/upv_prescribed_builds_limited_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with limited siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [upv_prescribed_builds_open_ba.csv](/inputs/capacity_exogenous/upv_prescribed_builds_open_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with open siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [upv_prescribed_builds_open_county.csv](/inputs/capacity_exogenous/upv_prescribed_builds_open_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with open siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [upv_prescribed_builds_reference_ba.csv](/inputs/capacity_exogenous/upv_prescribed_builds_reference_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with reference siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [upv_prescribed_builds_reference_county.csv](/inputs/capacity_exogenous/upv_prescribed_builds_reference_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** UPV prescribed builds with reference siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ofs_prescribed_builds_limited_ba.csv](/inputs/capacity_exogenous/wind-ofs_prescribed_builds_limited_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ofs prescribed builds with limited siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ofs_prescribed_builds_limited_county.csv](/inputs/capacity_exogenous/wind-ofs_prescribed_builds_limited_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ofs prescribed builds with limited siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ofs_prescribed_builds_open_ba.csv](/inputs/capacity_exogenous/wind-ofs_prescribed_builds_open_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ofs prescribed builds with open siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ofs_prescribed_builds_open_county.csv](/inputs/capacity_exogenous/wind-ofs_prescribed_builds_open_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ofs prescribed builds with open siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ofs_prescribed_builds_reference_ba.csv](/inputs/capacity_exogenous/wind-ofs_prescribed_builds_reference_ba.csv)
---

  - [wind-ofs_prescribed_builds_reference_county.csv](/inputs/capacity_exogenous/wind-ofs_prescribed_builds_reference_county.csv)
---

  - [wind-ons_exog_cap_limited_ba.csv](/inputs/capacity_exogenous/wind-ons_exog_cap_limited_ba.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) wind-ons capacity with limited siting assumptions at BA resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [wind-ons_exog_cap_limited_county.csv](/inputs/capacity_exogenous/wind-ons_exog_cap_limited_county.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) wind-ons capacity with limited siting assumptions at county resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [wind-ons_exog_cap_open_ba.csv](/inputs/capacity_exogenous/wind-ons_exog_cap_open_ba.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) wind-ons capacity with open siting assumptions at BA resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [wind-ons_exog_cap_open_county.csv](/inputs/capacity_exogenous/wind-ons_exog_cap_open_county.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) wind-ons capacity with open siting assumptions at county resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [wind-ons_exog_cap_reference_ba.csv](/inputs/capacity_exogenous/wind-ons_exog_cap_reference_ba.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) wind-ons capacity with reference siting assumptions at BA resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [wind-ons_exog_cap_reference_county.csv](/inputs/capacity_exogenous/wind-ons_exog_cap_reference_county.csv)
    - **File Type:** Exogenous capacity
    - **Description:** Exogenous (pre-2010) wind-ons capacity with reference siting assumptions at county resolution
    - **Indices:** tech,r,sc_point_grid,t
    - **Units:** MW

---

  - [wind-ons_prescribed_builds_limited_ba.csv](/inputs/capacity_exogenous/wind-ons_prescribed_builds_limited_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with limited siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ons_prescribed_builds_limited_county.csv](/inputs/capacity_exogenous/wind-ons_prescribed_builds_limited_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with limited siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ons_prescribed_builds_open_ba.csv](/inputs/capacity_exogenous/wind-ons_prescribed_builds_open_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with open siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ons_prescribed_builds_open_county.csv](/inputs/capacity_exogenous/wind-ons_prescribed_builds_open_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with open siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ons_prescribed_builds_reference_ba.csv](/inputs/capacity_exogenous/wind-ons_prescribed_builds_reference_ba.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with reference siting assumptions at BA resolution
    - **Indices:** r,t
    - **Units:** MW

---

  - [wind-ons_prescribed_builds_reference_county.csv](/inputs/capacity_exogenous/wind-ons_prescribed_builds_reference_county.csv)
    - **File Type:** Prescribed capacity
    - **Description:** wind-ons prescribed builds with reference siting assumptions at county resolution
    - **Indices:** r,t
    - **Units:** MW

---


#### [climate](inputs/climate) <a name='inputs/climate'></a>
  - [climate_heuristics_finalyear.csv](/inputs/climate/climate_heuristics_finalyear.csv)
---

  - [climate_heuristics_yearfrac.csv](/inputs/climate/climate_heuristics_yearfrac.csv)
---

  - [CoolSlopes.csv](/inputs/climate/CoolSlopes.csv)
---

  - [HeatSlopes.csv](/inputs/climate/HeatSlopes.csv)
---


##### [GFDL-ESM2M_RCP4p5_WM](inputs/climate/GFDL-ESM2M_RCP4p5_WM) <a name='inputs/climate/GFDL-ESM2M_RCP4p5_WM'></a>
  - [HDDCDD.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/HDDCDD.csv)
---

  - [hydadjann.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/hydadjann.csv)
---

  - [hydadjsea.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/hydadjsea.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/GFDL-ESM2M_RCP4p5_WM/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_RCP2p6](inputs/climate/HadGEM2-ES_RCP2p6) <a name='inputs/climate/HadGEM2-ES_RCP2p6'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_RCP2p6/HDDCDD.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_RCP2p6/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_RCP2p6/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_RCP2p6/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_rcp45_AT](inputs/climate/HadGEM2-ES_rcp45_AT) <a name='inputs/climate/HadGEM2-ES_rcp45_AT'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/HDDCDD.csv)
---

  - [hydadjann.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/hydadjann.csv)
---

  - [hydadjsea.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/hydadjsea.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_rcp45_AT/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_RCP4p5](inputs/climate/HadGEM2-ES_RCP4p5) <a name='inputs/climate/HadGEM2-ES_RCP4p5'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_RCP4p5/HDDCDD.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_RCP4p5/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_RCP4p5/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_RCP4p5/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_rcp85_AT](inputs/climate/HadGEM2-ES_rcp85_AT) <a name='inputs/climate/HadGEM2-ES_rcp85_AT'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/HDDCDD.csv)
---

  - [hydadjann.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/hydadjann.csv)
---

  - [hydadjsea.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/hydadjsea.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_rcp85_AT/UnappWaterSeaAnnDistr.csv)
---


##### [HadGEM2-ES_RCP8p5](inputs/climate/HadGEM2-ES_RCP8p5) <a name='inputs/climate/HadGEM2-ES_RCP8p5'></a>
  - [HDDCDD.csv](/inputs/climate/HadGEM2-ES_RCP8p5/HDDCDD.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/HadGEM2-ES_RCP8p5/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/HadGEM2-ES_RCP8p5/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/HadGEM2-ES_RCP8p5/UnappWaterSeaAnnDistr.csv)
---


##### [IPSL-CM5A-LR_RCP8p5_WM](inputs/climate/IPSL-CM5A-LR_RCP8p5_WM) <a name='inputs/climate/IPSL-CM5A-LR_RCP8p5_WM'></a>
  - [HDDCDD.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/HDDCDD.csv)
---

  - [hydadjann.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/hydadjann.csv)
---

  - [hydadjsea.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/hydadjsea.csv)
---

  - [UnappWaterMult.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/UnappWaterMult.csv)
---

  - [UnappWaterMultAnn.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/UnappWaterMultAnn.csv)
---

  - [UnappWaterSeaAnnDistr.csv](/inputs/climate/IPSL-CM5A-LR_RCP8p5_WM/UnappWaterSeaAnnDistr.csv)
---


#### [consume](inputs/consume) <a name='inputs/consume'></a>
  - [consume_char_low.csv](/inputs/consume/consume_char_low.csv)
    - **File Type:** Inputs
    - **Description:** Cost (capex, FOM, VOM) and efficiency (gas and electrical) as well as storage and transmission adder (stortran_adder) inputs for various H2 producing technologies, under Conservative assumptions.
    - **Indices:** i,t
    - **Dollar year:** Units vary based on the parameter - see commented text in b_inputs.gms.

    - **Citation:** [(N/A)]
---

  - [consume_char_ref.csv](/inputs/consume/consume_char_ref.csv)
    - **File Type:** Inputs
    - **Description:** Cost (capex, FOM, VOM) and efficiency (gas and electrical) as well as storage and transmission adder (stortran_adder) inputs for various H2 producing technologies, under Reference assumptions.
    - **Indices:** i,t
    - **Dollar year:** Units vary based on the parameter - see commented text in b_inputs.gms.

    - **Citation:** [(N/A)]
---

  - [dac_elec_BVRE_2021_high.csv](/inputs/consume/dac_elec_BVRE_2021_high.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using High assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a)]
---

  - [dac_elec_BVRE_2021_low.csv](/inputs/consume/dac_elec_BVRE_2021_low.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using Low assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a)]
---

  - [dac_elec_BVRE_2021_mid.csv](/inputs/consume/dac_elec_BVRE_2021_mid.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using Mid assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(https://www.netl.doe.gov/energy-analysis/details?id=d5860604-fbc7-44bb-a756-76db47d8b85a)]
---

  - [dac_gas_BVRE_2021_high.csv](/inputs/consume/dac_gas_BVRE_2021_high.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using High assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987)]
---

  - [dac_gas_BVRE_2021_low.csv](/inputs/consume/dac_gas_BVRE_2021_low.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using Low assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987)]
---

  - [dac_gas_BVRE_2021_mid.csv](/inputs/consume/dac_gas_BVRE_2021_mid.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex [$/(metric ton CO2/hr)], FOM [$/(metric ton CO2/hr)/yr], VOM [$/metric ton CO2]) and conversion rate, over time, using Mid assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(https://netl.doe.gov/energy-analysis/details?id=36385f18-3eaa-4f96-9983-6e2b607f6987)]
---

  - [dollaryear.csv](/inputs/consume/dollaryear.csv)
    - **File Type:** Inputs
    - **Description:** Dollar year for various Beyond VRE scenarios. 
    - **Indices:** N/A
    - **Dollar year:** Stated in document.

    - **Citation:** [(N/A)]
---

  - [h2_ba_share.csv](/inputs/consume/h2_ba_share.csv)
    - **File Type:** Inputs
    - **Description:** The fraction of hydrogen demand in that year that corresponds to a particular ReEDS BA.
    - **Indices:** r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [h2_exogenous_demand.csv](/inputs/consume/h2_exogenous_demand.csv)
    - **File Type:** Inputs
    - **Description:** Exogenous hydrogen demand by industries other than the power sector per year
    - **Indices:** t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [h2_storage_rb.csv](/inputs/consume/h2_storage_rb.csv)
    - **File Type:** Inputs
    - **Description:** Mapping of types of storage that exist in various ReEDS BAs.
    - **Indices:** r
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [h2_transport_and_storage_costs.csv](/inputs/consume/h2_transport_and_storage_costs.csv)
    - **File Type:** Inputs
    - **Description:** Transport and storage costs of hydrogen per year
    - **Indices:** t
    - **Dollar year:** 2004

    - **Citation:** [(N/A)]
---

  - [pipeline_cost_mult.csv](/inputs/consume/pipeline_cost_mult.csv)
    - **File Type:** Inputs
    - **Description:** Multiplier to the cost of hydrogen pipelines in various r-->r combinations.
    - **Indices:** r
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---


#### [ctus](inputs/ctus) <a name='inputs/ctus'></a>
  - [co2_site_char.csv](/inputs/ctus/co2_site_char.csv)
    - **Dollar year:** 2018
---

  - [cs.csv](/inputs/ctus/cs.csv)
---

  - [r_cs.csv](/inputs/ctus/r_cs.csv)
---

  - [r_cs_distance_mi.csv](/inputs/ctus/r_cs_distance_mi.csv)
---


#### [degradation](inputs/degradation) <a name='inputs/degradation'></a>
  - [degradation_annual_default.csv](/inputs/degradation/degradation_annual_default.csv)
---


#### [demand_response](inputs/demand_response) <a name='inputs/demand_response'></a>
  - [dr_decrease_none.csv](/inputs/demand_response/dr_decrease_none.csv)
---

  - [dr_decrease_profile_Baseline.csv](/inputs/demand_response/dr_decrease_profile_Baseline.csv)
    - **File Type:** inputs
    - **Description:** Average capacity factor for dr profile which leads to an increase in load in timeslice h for Baseline demand response profile. The demand response profiles are not being actively developed and may be outdated. 
    - **Units:** fraction

---

  - [dr_decrease_profile_Baseline_shed.csv](/inputs/demand_response/dr_decrease_profile_Baseline_shed.csv)
---

  - [dr_decrease_profile_Baseline_shift.csv](/inputs/demand_response/dr_decrease_profile_Baseline_shift.csv)
---

  - [dr_decrease_profile_none.csv](/inputs/demand_response/dr_decrease_profile_none.csv)
---

  - [dr_increase_none.csv](/inputs/demand_response/dr_increase_none.csv)
---

  - [dr_increase_profile_Baseline.csv](/inputs/demand_response/dr_increase_profile_Baseline.csv)
    - **File Type:** inputs
    - **Description:** Average capacity factor for dr profile which leads to a reduction in load in timeslice h for Baseline demand response profile. The demand response profiles are not being actively developed and may be outdated.
    - **Units:** fraction

---

  - [dr_increase_profile_Baseline_shed.csv](/inputs/demand_response/dr_increase_profile_Baseline_shed.csv)
---

  - [dr_increase_profile_Baseline_shift.csv](/inputs/demand_response/dr_increase_profile_Baseline_shift.csv)
---

  - [dr_increase_profile_none.csv](/inputs/demand_response/dr_increase_profile_none.csv)
---

  - [dr_rsc_Baseline.csv](/inputs/demand_response/dr_rsc_Baseline.csv)
---

  - [dr_rsc_Baseline_shed.csv](/inputs/demand_response/dr_rsc_Baseline_shed.csv)
---

  - [dr_rsc_Baseline_shift.csv](/inputs/demand_response/dr_rsc_Baseline_shift.csv)
---

  - [dr_rsc_none.csv](/inputs/demand_response/dr_rsc_none.csv)
---

  - [dr_shed_Baseline.csv](/inputs/demand_response/dr_shed_Baseline.csv)
---

  - [dr_shed_Baseline_shed.csv](/inputs/demand_response/dr_shed_Baseline_shed.csv)
---

  - [dr_shed_Baseline_shift.csv](/inputs/demand_response/dr_shed_Baseline_shift.csv)
---

  - [dr_shed_none.csv](/inputs/demand_response/dr_shed_none.csv)
---

  - [dr_shifts_Baseline.csv](/inputs/demand_response/dr_shifts_Baseline.csv)
    - **Description:** How much load each dr type is allowed to shift into h from hh
---

  - [dr_shifts_Baseline_shed.csv](/inputs/demand_response/dr_shifts_Baseline_shed.csv)
---

  - [dr_shifts_Baseline_shift.csv](/inputs/demand_response/dr_shifts_Baseline_shift.csv)
---

  - [dr_shifts_none.csv](/inputs/demand_response/dr_shifts_none.csv)
---

  - [dr_types_Baseline.csv](/inputs/demand_response/dr_types_Baseline.csv)
---

  - [dr_types_Baseline_shed.csv](/inputs/demand_response/dr_types_Baseline_shed.csv)
---

  - [dr_types_Baseline_shift.csv](/inputs/demand_response/dr_types_Baseline_shift.csv)
---

  - [dr_types_none.csv](/inputs/demand_response/dr_types_none.csv)
---

  - [ev_load_Baseline.h5](/inputs/demand_response/ev_load_Baseline.h5)
    - **File Type:** inputs
    - **Description:** Baseline electricity load from EV charging by timeslice h and year t
    - **Units:** MW

---

  - [evmc_rsc_Baseline.csv](/inputs/demand_response/evmc_rsc_Baseline.csv)
---

  - [evmc_shape_decrease_profile_Baseline.h5](/inputs/demand_response/evmc_shape_decrease_profile_Baseline.h5)
---

  - [evmc_shape_increase_profile_Baseline.h5](/inputs/demand_response/evmc_shape_increase_profile_Baseline.h5)
---

  - [evmc_storage_decrease_profile_Baseline.h5](/inputs/demand_response/evmc_storage_decrease_profile_Baseline.h5)
---

  - [evmc_storage_energy_Baseline.h5](/inputs/demand_response/evmc_storage_energy_Baseline.h5)
---

  - [evmc_storage_increase_profile_Baseline.h5](/inputs/demand_response/evmc_storage_increase_profile_Baseline.h5)
---


#### [dgen_model_inputs](inputs/dgen_model_inputs) <a name='inputs/dgen_model_inputs'></a>

##### [stscen2023_electrification](inputs/dgen_model_inputs/stscen2023_electrification) <a name='inputs/dgen_model_inputs/stscen2023_electrification'></a>
  - [distpvcap_stscen2023_electrification.csv](/inputs/dgen_model_inputs/stscen2023_electrification/distpvcap_stscen2023_electrification.csv)
---


##### [stscen2023_highng](inputs/dgen_model_inputs/stscen2023_highng) <a name='inputs/dgen_model_inputs/stscen2023_highng'></a>
  - [distpvcap_stscen2023_highng.csv](/inputs/dgen_model_inputs/stscen2023_highng/distpvcap_stscen2023_highng.csv)
    - **File Type:** distribution PV inputs 
    - **Description:** Setting for distpv scenario capacity - from standard scenarios 2023 with high NG (including distpv) costs
---


##### [stscen2023_highre](inputs/dgen_model_inputs/stscen2023_highre) <a name='inputs/dgen_model_inputs/stscen2023_highre'></a>
  - [distpvcap_stscen2023_highre.csv](/inputs/dgen_model_inputs/stscen2023_highre/distpvcap_stscen2023_highre.csv)
    - **File Type:** distribution PV inputs 
    - **Description:** Setting for distpv scenario capacity - from standard scenarios 2023 with high RE (including distpv) costs
---


##### [stscen2023_lowng](inputs/dgen_model_inputs/stscen2023_lowng) <a name='inputs/dgen_model_inputs/stscen2023_lowng'></a>
  - [distpvcap_stscen2023_lowng.csv](/inputs/dgen_model_inputs/stscen2023_lowng/distpvcap_stscen2023_lowng.csv)
    - **File Type:** distribution PV inputs 
    - **Description:** Setting for distpv scenario capacity - from standard scenarios 2023 with low NG (including distpv) costs
---


##### [stscen2023_lowre](inputs/dgen_model_inputs/stscen2023_lowre) <a name='inputs/dgen_model_inputs/stscen2023_lowre'></a>
  - [distpvcap_stscen2023_lowre.csv](/inputs/dgen_model_inputs/stscen2023_lowre/distpvcap_stscen2023_lowre.csv)
    - **File Type:** distribution PV inputs 
    - **Description:** Setting for distpv scenario capacity - from standard scenarios 2023 with low RE (including distpv) costs
---


##### [stscen2023_mid_case](inputs/dgen_model_inputs/stscen2023_mid_case) <a name='inputs/dgen_model_inputs/stscen2023_mid_case'></a>
  - [distpvcap_stscen2023_mid_case.csv](/inputs/dgen_model_inputs/stscen2023_mid_case/distpvcap_stscen2023_mid_case.csv)
    - **File Type:** distribution PV inputs 
---


##### [stscen2023_mid_case_95_by_2035](inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2035) <a name='inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2035'></a>
  - [distpvcap_stscen2023_mid_case_95_by_2035.csv](/inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2035/distpvcap_stscen2023_mid_case_95_by_2035.csv)
    - **File Type:** distribution PV inputs 
---


##### [stscen2023_mid_case_95_by_2050](inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2050) <a name='inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2050'></a>
  - [distpvcap_stscen2023_mid_case_95_by_2050.csv](/inputs/dgen_model_inputs/stscen2023_mid_case_95_by_2050/distpvcap_stscen2023_mid_case_95_by_2050.csv)
    - **File Type:** distribution PV inputs 
---


##### [stscen2023_taxcredit_extended2050](inputs/dgen_model_inputs/stscen2023_taxcredit_extended2050) <a name='inputs/dgen_model_inputs/stscen2023_taxcredit_extended2050'></a>
  - [distpvcap_stscen2023_taxcredit_extended2050.csv](/inputs/dgen_model_inputs/stscen2023_taxcredit_extended2050/distpvcap_stscen2023_taxcredit_extended2050.csv)
    - **File Type:** distribution PV inputs 
---


#### [disaggregation](inputs/disaggregation) <a name='inputs/disaggregation'></a>
  - [disagg_geosize.csv](/inputs/disaggregation/disagg_geosize.csv)
    - **Description:** The geographic area fraction of each county within a given ReEDS BA, used as multipliers for disaggregating spatial data
    - **Indices:** r
---

  - [disagg_hydroexist.csv](/inputs/disaggregation/disagg_hydroexist.csv)
    - **Description:** The hydropower capacity fraction of each county within a given ReEDS BA, used as multipliers for downselecting data
    - **Indices:** r
---

  - [disagg_population.csv](/inputs/disaggregation/disagg_population.csv)
    - **Description:** The population fraction of each county within a given ReEDS BA, used as multipliers for downselecting data
    - **Indices:** r
---

  - [disagg_translinesize.csv](/inputs/disaggregation/disagg_translinesize.csv)
    - **Description:** The ratio of transmission capacity between a given US county and Canadian BA in relation to the total transmission capacity between the Canadian BA and the US BA that said county is in. 
    - **Indices:** r
---


#### [emission_constraints](inputs/emission_constraints) <a name='inputs/emission_constraints'></a>
  - [ccs_link.csv](/inputs/emission_constraints/ccs_link.csv)
---

  - [ccs_link_water.csv](/inputs/emission_constraints/ccs_link_water.csv)
---

  - [co2_cap.csv](/inputs/emission_constraints/co2_cap.csv)
    - **Description:** Annual nationwide carbon cap
---

  - [co2_tax.csv](/inputs/emission_constraints/co2_tax.csv)
    - **Description:** Annual co2 tax
---

  - [county_co2_share_egrid_2022.csv](/inputs/emission_constraints/county_co2_share_egrid_2022.csv)
---

  - [csapr_group1_ex.csv](/inputs/emission_constraints/csapr_group1_ex.csv)
---

  - [csapr_group2_ex.csv](/inputs/emission_constraints/csapr_group2_ex.csv)
---

  - [csapr_ozone_season.csv](/inputs/emission_constraints/csapr_ozone_season.csv)
---

  - [emitrate.csv](/inputs/emission_constraints/emitrate.csv)
    - **Description:** Emition rates for thermal generator for SO2, NOx, and CO2
    - **Indices:** i,e
---

  - [methane_leakage_rate.csv](/inputs/emission_constraints/methane_leakage_rate.csv)
---

  - [ng_crf_penalty.csv](/inputs/emission_constraints/ng_crf_penalty.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment for NG techs in scenarios with national decarbonization targets
    - **Indices:** allt
    - **Dollar year:** N/A

    - **Citation:** [(https://github.nrel.gov/ReEDS/ReEDS-2.0/pull/1220)]
    - **Units:** rate (unitless)

---

  - [rggi_states.csv](/inputs/emission_constraints/rggi_states.csv)
---

  - [rggicon.csv](/inputs/emission_constraints/rggicon.csv)
    - **Description:** CO2 caps for RGGI states in metric tons
---

  - [state_cap.csv](/inputs/emission_constraints/state_cap.csv)
---


#### [financials](inputs/financials) <a name='inputs/financials'></a>
  - [cap_penalty.csv](/inputs/financials/cap_penalty.csv)
---

  - [construction_schedules_default.csv](/inputs/financials/construction_schedules_default.csv)
---

  - [construction_times_default.csv](/inputs/financials/construction_times_default.csv)
---

  - [currency_incentives.csv](/inputs/financials/currency_incentives.csv)
---

  - [deflator.csv](/inputs/financials/deflator.csv)
    - **Description:** Dollar year deflator to convert values to 2004$
---

  - [depreciation_schedules_default.csv](/inputs/financials/depreciation_schedules_default.csv)
---

  - [energy_communities.csv](/inputs/financials/energy_communities.csv)
---

  - [financials_hydrogen.csv](/inputs/financials/financials_hydrogen.csv)
---

  - [financials_sys_ATB2023.csv](/inputs/financials/financials_sys_ATB2023.csv)
---

  - [financials_sys_ATB2024.csv](/inputs/financials/financials_sys_ATB2024.csv)
---

  - [financials_tech_ATB2023.csv](/inputs/financials/financials_tech_ATB2023.csv)
---

  - [financials_tech_ATB2023_CRP20.csv](/inputs/financials/financials_tech_ATB2023_CRP20.csv)
---

  - [financials_tech_ATB2024.csv](/inputs/financials/financials_tech_ATB2024.csv)
---

  - [financials_transmission_30ITC_0pen_2022_2031.csv](/inputs/financials/financials_transmission_30ITC_0pen_2022_2031.csv)
---

  - [financials_transmission_default.csv](/inputs/financials/financials_transmission_default.csv)
---

  - [incentives_annual.csv](/inputs/financials/incentives_annual.csv)
---

  - [incentives_biennial.csv](/inputs/financials/incentives_biennial.csv)
---

  - [incentives_ira.csv](/inputs/financials/incentives_ira.csv)
---

  - [incentives_ira_45q_45v_extension.csv](/inputs/financials/incentives_ira_45q_45v_extension.csv)
---

  - [incentives_ira_hii.csv](/inputs/financials/incentives_ira_hii.csv)
---

  - [incentives_ira_lii.csv](/inputs/financials/incentives_ira_lii.csv)
---

  - [incentives_none.csv](/inputs/financials/incentives_none.csv)
---

  - [inflation_default.csv](/inputs/financials/inflation_default.csv)
    - **Description:** Annual inflation factors from 1914 through 2200; historical values use the avg-avg values from https://www.usinflationcalculator.com/inflation/consumer-price-index-and-annual-percent-changes-from-1913-to-2008/
    - **Indices:** t
---

  - [reg_cap_cost_mult_default.csv](/inputs/financials/reg_cap_cost_mult_default.csv)
    - **File Type:** parameter
    - **Description:** region-specific multipliers for capital cost of all resources. Note: RE resources have values of 1 since their multipliers are incorporated in hourlize
    - **Indices:** i,r
---

  - [retire_penalty.csv](/inputs/financials/retire_penalty.csv)
---

  - [supply_chain_adjust.csv](/inputs/financials/supply_chain_adjust.csv)
---

  - [tc_phaseout_schedule_ira2022.csv](/inputs/financials/tc_phaseout_schedule_ira2022.csv)
---


#### [fuelprices](inputs/fuelprices) <a name='inputs/fuelprices'></a>
  - [alpha_AEO_2022_HOG.csv](/inputs/fuelprices/alpha_AEO_2022_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004

    - **Citation:** [(AEO 2022)]
---

  - [alpha_AEO_2022_LOG.csv](/inputs/fuelprices/alpha_AEO_2022_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004

    - **Citation:** [(AEO 2022)]
---

  - [alpha_AEO_2022_reference.csv](/inputs/fuelprices/alpha_AEO_2022_reference.csv)
    - **File Type:** Input
    - **Description:** reference census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004

    - **Citation:** [(AEO 2022)]
---

  - [alpha_AEO_2023_HOG.csv](/inputs/fuelprices/alpha_AEO_2023_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004

    - **Citation:** [(AEO 2023)]
---

  - [alpha_AEO_2023_LOG.csv](/inputs/fuelprices/alpha_AEO_2023_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004

    - **Citation:** [(AEO 2023)]
---

  - [alpha_AEO_2023_reference.csv](/inputs/fuelprices/alpha_AEO_2023_reference.csv)
    - **File Type:** Input
    - **Description:** reference census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004

    - **Citation:** [(AEO 2023)]
---

  - [cd_beta0.csv](/inputs/fuelprices/cd_beta0.csv)
    - **File Type:** Input
    - **Description:** reference census division beta levels electric sector
    - **Indices:** cendiv
    - **Dollar year:** 2004
---

  - [cd_beta0_allsector.csv](/inputs/fuelprices/cd_beta0_allsector.csv)
    - **File Type:** Input
    - **Description:** reference census division beta levels all sectors
    - **Indices:** cendiv
    - **Dollar year:** 2004
---

  - [cendivweights.csv](/inputs/fuelprices/cendivweights.csv)
    - **Description:** weights to smooth gas prices between census regions to avoid abrupt price changes at the cendiv borders
    - **Indices:** r,cendiv
---

  - [coal_AEO_2022_reference.csv](/inputs/fuelprices/coal_AEO_2022_reference.csv)
    - **Description:** reference case census division fuel price of coal
    - **Indices:** t,cendiv
    - **Dollar year:** 2022
---

  - [coal_AEO_2023_reference.csv](/inputs/fuelprices/coal_AEO_2023_reference.csv)
    - **Description:** reference case census division fuel price of coal
    - **Indices:** t,cendiv
    - **Dollar year:** 2023
---

  - [dollaryear.csv](/inputs/fuelprices/dollaryear.csv)
    - **Description:** Dollar year mapping for each fuel price scenario
---

  - [h2-ct_10.csv](/inputs/fuelprices/h2-ct_10.csv)
---

  - [h2-ct_30.csv](/inputs/fuelprices/h2-ct_30.csv)
---

  - [h2-ct_reference.csv](/inputs/fuelprices/h2-ct_reference.csv)
---

  - [ng_AEO_2022_HOG.csv](/inputs/fuelprices/ng_AEO_2022_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2022_LOG.csv](/inputs/fuelprices/ng_AEO_2022_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2022_reference.csv](/inputs/fuelprices/ng_AEO_2022_reference.csv)
    - **File Type:** Input
    - **Description:** Reference scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2023_HOG.csv](/inputs/fuelprices/ng_AEO_2023_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2023_LOG.csv](/inputs/fuelprices/ng_AEO_2023_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** 2004$/MMBtu

---

  - [ng_AEO_2023_reference.csv](/inputs/fuelprices/ng_AEO_2023_reference.csv)
    - **File Type:** Input
    - **Description:** Reference scenario census division fuel price of natural gas
    - **Indices:** cendiv,t
    - **Dollar year:** 2004

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** 2004$/MMBtu

---

  - [ng_demand_AEO_2022_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2022_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_demand_AEO_2022_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2022_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_demand_AEO_2022_reference.csv](/inputs/fuelprices/ng_demand_AEO_2022_reference.csv)
    - **File Type:** Input
    - **Description:** Reference census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_demand_AEO_2023_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2023_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_demand_AEO_2023_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2023_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_demand_AEO_2023_reference.csv](/inputs/fuelprices/ng_demand_AEO_2023_reference.csv)
    - **File Type:** Input
    - **Description:** Reference census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2022_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2022_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2022_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2022_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2022_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2022_reference.csv)
    - **File Type:** Input
    - **Description:** Reference census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2023_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2023_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [ng_tot_demand_AEO_2023_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_reference.csv)
    - **File Type:** Input
    - **Description:** Reference census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
    - **Indices:** cendiv,t

    - **Citation:** [(AEO2023: https://www.eia.gov/outlooks/aeo/)]
    - **Units:** Quads

---

  - [uranium_AEO_2022_reference.csv](/inputs/fuelprices/uranium_AEO_2022_reference.csv)
---

  - [uranium_AEO_2023_reference.csv](/inputs/fuelprices/uranium_AEO_2023_reference.csv)
---


#### [geothermal](inputs/geothermal) <a name='inputs/geothermal'></a>
  - [geo_discovery_BAU.csv](/inputs/geothermal/geo_discovery_BAU.csv)
---

  - [geo_discovery_factor_ATB_2023.csv](/inputs/geothermal/geo_discovery_factor_ATB_2023.csv)
---

  - [geo_discovery_factor_reV.csv](/inputs/geothermal/geo_discovery_factor_reV.csv)
---

  - [geo_discovery_TI.csv](/inputs/geothermal/geo_discovery_TI.csv)
---

  - [geo_rsc_ATB_2023.csv](/inputs/geothermal/geo_rsc_ATB_2023.csv)
---


#### [growth_constraints](inputs/growth_constraints) <a name='inputs/growth_constraints'></a>
  - [gbin_min.csv](/inputs/growth_constraints/gbin_min.csv)
---

  - [growth_bin_size_mult.csv](/inputs/growth_constraints/growth_bin_size_mult.csv)
---

  - [growth_limit_absolute.csv](/inputs/growth_constraints/growth_limit_absolute.csv)
    - **Description:** Maximum expected annual builds for wind, batteries, and UPV from 2024-2026 using observed record builds.
    - **Units:** MW/year

---

  - [growth_penalty.csv](/inputs/growth_constraints/growth_penalty.csv)
---


#### [hydro](inputs/hydro) <a name='inputs/hydro'></a>
  - [hyd_fom.csv](/inputs/hydro/hyd_fom.csv)
    - **Description:** Regional FOM costs for hydro
---

  - [hydcf.h5](/inputs/hydro/hydcf.h5)
---

  - [hydro_mingen.csv](/inputs/hydro/hydro_mingen.csv)
---

  - [SeaCapAdj_hy.csv](/inputs/hydro/SeaCapAdj_hy.csv)
---


#### [load](inputs/load) <a name='inputs/load'></a>
  - [Adoption_Trajectories_Commercial.csv](/inputs/load/Adoption_Trajectories_Commercial.csv)
---

  - [Adoption_Trajectories_Residential.csv](/inputs/load/Adoption_Trajectories_Residential.csv)
---

  - [Baseline_load_hourly.h5](/inputs/load/Baseline_load_hourly.h5)
---

  - [cangrowth.csv](/inputs/load/cangrowth.csv)
    - **Description:** Canada load growth multiplier
---

  - [Clean2035_load_hourly.h5](/inputs/load/Clean2035_load_hourly.h5)
---

  - [Clean2035_LTS_load_hourly.h5](/inputs/load/Clean2035_LTS_load_hourly.h5)
---

  - [Clean2035clip1pct_load_hourly.h5](/inputs/load/Clean2035clip1pct_load_hourly.h5)
---

  - [Commercial_GHP_Delta.csv](/inputs/load/Commercial_GHP_Delta.csv)
---

  - [demand_AEO_2023_high.csv](/inputs/load/demand_AEO_2023_high.csv)
---

  - [demand_AEO_2023_low.csv](/inputs/load/demand_AEO_2023_low.csv)
---

  - [demand_AEO_2023_reference.csv](/inputs/load/demand_AEO_2023_reference.csv)
---

  - [demand_flat_2020_onward.csv](/inputs/load/demand_flat_2020_onward.csv)
---

  - [EER_100by2050_load_hourly.h5](/inputs/load/EER_100by2050_load_hourly.h5)
---

  - [EER_Baseline_AEO2022_load_hourly.h5](/inputs/load/EER_Baseline_AEO2022_load_hourly.h5)
---

  - [EER_IRAlow_load_hourly.h5](/inputs/load/EER_IRAlow_load_hourly.h5)
---

  - [EER_IRAmoderate_load_hourly.h5](/inputs/load/EER_IRAmoderate_load_hourly.h5)
---

  - [EPHIGH_load_hourly.h5](/inputs/load/EPHIGH_load_hourly.h5)
---

  - [EPMEDIUM_load_hourly.h5](/inputs/load/EPMEDIUM_load_hourly.h5)
---

  - [EPMEDIUMStretch2040_load_hourly.h5](/inputs/load/EPMEDIUMStretch2040_load_hourly.h5)
---

  - [EPMEDIUMStretch2046_load_hourly.h5](/inputs/load/EPMEDIUMStretch2046_load_hourly.h5)
---

  - [EPREFERENCE_load_hourly.h5](/inputs/load/EPREFERENCE_load_hourly.h5)
---

  - [historic_load_hourly.h5](/inputs/load/historic_load_hourly.h5)
---

  - [mex_growth_rate.csv](/inputs/load/mex_growth_rate.csv)
    - **Description:** Mexico load growth multiplier
---

  - [Residential_GHP_Delta.csv](/inputs/load/Residential_GHP_Delta.csv)
---


#### [national_generation](inputs/national_generation) <a name='inputs/national_generation'></a>
  - [gen_mandate_tech_list.csv](/inputs/national_generation/gen_mandate_tech_list.csv)
---

  - [gen_mandate_trajectory.csv](/inputs/national_generation/gen_mandate_trajectory.csv)
---

  - [national_rps_frac_allScen.csv](/inputs/national_generation/national_rps_frac_allScen.csv)
---


#### [plant_characteristics](inputs/plant_characteristics) <a name='inputs/plant_characteristics'></a>
  - [battery_ATB_2023_advanced.csv](/inputs/plant_characteristics/battery_ATB_2023_advanced.csv)
    - **Dollar year:** 2020
---

  - [battery_ATB_2023_conservative.csv](/inputs/plant_characteristics/battery_ATB_2023_conservative.csv)
    - **Dollar year:** 2020
---

  - [battery_ATB_2023_moderate.csv](/inputs/plant_characteristics/battery_ATB_2023_moderate.csv)
    - **Dollar year:** 2020
---

  - [battery_ATB_2024_advanced.csv](/inputs/plant_characteristics/battery_ATB_2024_advanced.csv)
    - **Dollar year:** 2021
---

  - [battery_ATB_2024_conservative.csv](/inputs/plant_characteristics/battery_ATB_2024_conservative.csv)
    - **Dollar year:** 2021
---

  - [battery_ATB_2024_moderate.csv](/inputs/plant_characteristics/battery_ATB_2024_moderate.csv)
    - **Dollar year:** 2021
---

  - [beccs_BVRE_2021_high.csv](/inputs/plant_characteristics/beccs_BVRE_2021_high.csv)
---

  - [beccs_BVRE_2021_low.csv](/inputs/plant_characteristics/beccs_BVRE_2021_low.csv)
---

  - [beccs_BVRE_2021_mid.csv](/inputs/plant_characteristics/beccs_BVRE_2021_mid.csv)
---

  - [beccs_lowcost.csv](/inputs/plant_characteristics/beccs_lowcost.csv)
---

  - [beccs_reference.csv](/inputs/plant_characteristics/beccs_reference.csv)
---

  - [caes_reference.csv](/inputs/plant_characteristics/caes_reference.csv)
    - **Description:** CAES costs for the reference cost scenario
---

  - [ccsflex_ATB_2020_cost.csv](/inputs/plant_characteristics/ccsflex_ATB_2020_cost.csv)
---

  - [ccsflex_ATB_2020_perf.csv](/inputs/plant_characteristics/ccsflex_ATB_2020_perf.csv)
---

  - [coal_fom_adj.csv](/inputs/plant_characteristics/coal_fom_adj.csv)
    - **Dollar year:** 2017
---

  - [conv_ATB_2023.csv](/inputs/plant_characteristics/conv_ATB_2023.csv)
---

  - [conv_ATB_2023_ccs_advanced.csv](/inputs/plant_characteristics/conv_ATB_2023_ccs_advanced.csv)
---

  - [conv_ATB_2023_ccs_conservative.csv](/inputs/plant_characteristics/conv_ATB_2023_ccs_conservative.csv)
---

  - [conv_ATB_2023_conservative.csv](/inputs/plant_characteristics/conv_ATB_2023_conservative.csv)
---

  - [conv_ATB_2023_low_nuclear_cost.csv](/inputs/plant_characteristics/conv_ATB_2023_low_nuclear_cost.csv)
---

  - [conv_ATB_2024.csv](/inputs/plant_characteristics/conv_ATB_2024.csv)
---

  - [conv_ATB_2024_adv_ccs.csv](/inputs/plant_characteristics/conv_ATB_2024_adv_ccs.csv)
---

  - [conv_ATB_2024_adv_nuclear.csv](/inputs/plant_characteristics/conv_ATB_2024_adv_nuclear.csv)
---

  - [conv_ATB_2024_con_ccs.csv](/inputs/plant_characteristics/conv_ATB_2024_con_ccs.csv)
---

  - [conv_ATB_2024_con_nuclear.csv](/inputs/plant_characteristics/conv_ATB_2024_con_nuclear.csv)
---

  - [cost_opres_default.csv](/inputs/plant_characteristics/cost_opres_default.csv)
---

  - [cost_opres_market.csv](/inputs/plant_characteristics/cost_opres_market.csv)
---

  - [csp_ATB_2023_advanced.csv](/inputs/plant_characteristics/csp_ATB_2023_advanced.csv)
---

  - [csp_ATB_2023_conservative.csv](/inputs/plant_characteristics/csp_ATB_2023_conservative.csv)
---

  - [csp_ATB_2023_moderate.csv](/inputs/plant_characteristics/csp_ATB_2023_moderate.csv)
---

  - [csp_ATB_2024_advanced.csv](/inputs/plant_characteristics/csp_ATB_2024_advanced.csv)
---

  - [csp_ATB_2024_conservative.csv](/inputs/plant_characteristics/csp_ATB_2024_conservative.csv)
---

  - [csp_ATB_2024_moderate.csv](/inputs/plant_characteristics/csp_ATB_2024_moderate.csv)
---

  - [csp_SunShot2030.csv](/inputs/plant_characteristics/csp_SunShot2030.csv)
    - **Description:** Csp costs from the SunShot2030 cost scenario
---

  - [dollaryear.csv](/inputs/plant_characteristics/dollaryear.csv)
    - **Description:** Dollar year mapping for each plant cost scenario
---

  - [dr_Baseline.csv](/inputs/plant_characteristics/dr_Baseline.csv)
---

  - [dr_Baseline_shed.csv](/inputs/plant_characteristics/dr_Baseline_shed.csv)
---

  - [dr_Baseline_shift.csv](/inputs/plant_characteristics/dr_Baseline_shift.csv)
---

  - [dr_none.csv](/inputs/plant_characteristics/dr_none.csv)
---

  - [dr_test.csv](/inputs/plant_characteristics/dr_test.csv)
---

  - [evmc_shape_Baseline.csv](/inputs/plant_characteristics/evmc_shape_Baseline.csv)
---

  - [evmc_storage_Baseline.csv](/inputs/plant_characteristics/evmc_storage_Baseline.csv)
---

  - [geo_ATB_2023_advanced.csv](/inputs/plant_characteristics/geo_ATB_2023_advanced.csv)
---

  - [geo_ATB_2023_conservative.csv](/inputs/plant_characteristics/geo_ATB_2023_conservative.csv)
---

  - [geo_ATB_2023_moderate.csv](/inputs/plant_characteristics/geo_ATB_2023_moderate.csv)
---

  - [geo_ATB_2024_advanced.csv](/inputs/plant_characteristics/geo_ATB_2024_advanced.csv)
---

  - [geo_ATB_2024_conservative.csv](/inputs/plant_characteristics/geo_ATB_2024_conservative.csv)
---

  - [geo_ATB_2024_moderate.csv](/inputs/plant_characteristics/geo_ATB_2024_moderate.csv)
---

  - [h2-ct_ATB_2023.csv](/inputs/plant_characteristics/h2-ct_ATB_2023.csv)
---

  - [h2-ct_ATB_2024.csv](/inputs/plant_characteristics/h2-ct_ATB_2024.csv)
---

  - [heat_rate_adj.csv](/inputs/plant_characteristics/heat_rate_adj.csv)
    - **Description:** Heat rate adjustment multiplier by technology
---

  - [heat_rate_penalty_spin.csv](/inputs/plant_characteristics/heat_rate_penalty_spin.csv)
---

  - [hydro_ATB_2019_constant.csv](/inputs/plant_characteristics/hydro_ATB_2019_constant.csv)
    - **Description:** Hydro costs from the 2019 ATB constant cost scenario
---

  - [hydro_ATB_2019_low.csv](/inputs/plant_characteristics/hydro_ATB_2019_low.csv)
    - **Description:** Hydro costs from the 2019 ATB low cost scenario
---

  - [hydro_ATB_2019_mid.csv](/inputs/plant_characteristics/hydro_ATB_2019_mid.csv)
    - **Description:** Hydro costs from the 2019 ATB mid cost scenario
---

  - [ice_fom.csv](/inputs/plant_characteristics/ice_fom.csv)
    - **Description:** Fixed O&M for ice storage
---

  - [maxage.csv](/inputs/plant_characteristics/maxage.csv)
    - **Description:** Maximum age allowed for each technology
---

  - [min_retire_age.csv](/inputs/plant_characteristics/min_retire_age.csv)
    - **Description:** Minimum retirement age for given technology
---

  - [minCF.csv](/inputs/plant_characteristics/minCF.csv)
    - **Description:** minimum annual capacity factor for each tech fleet - applied to i-rto
---

  - [mingen_fixed.csv](/inputs/plant_characteristics/mingen_fixed.csv)
---

  - [minloadfrac0.csv](/inputs/plant_characteristics/minloadfrac0.csv)
    - **Description:** characteristics/minloadfrac0 database of minloadbed generator cs
---

  - [nuke_fom_adj.csv](/inputs/plant_characteristics/nuke_fom_adj.csv)
    - **Dollar year:** 2017
---

  - [ofs-wind_ATB_2023_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 advanced ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2023_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 conservative ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2023_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 moderate ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2023_moderate_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2023_moderate_noFloating.csv)
---

  - [ofs-wind_ATB_2024_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2024_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 advanced ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2022
---

  - [ofs-wind_ATB_2024_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2024_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 conservative ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2022
---

  - [ofs-wind_ATB_2024_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2024_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 moderate ofs-wind capital, fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year 
    - **Dollar year:** 2022
---

  - [ofs-wind_ATB_2024_moderate_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2024_moderate_noFloating.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 moderate_noFloating ofs-wind capital (5x floating capital cost), fixed O&M, var O&M costs and rsc_mult (SC cost reduction mult) by class and year
    - **Dollar year:** 2022
---

  - [ons-wind_ATB_2023_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_advanced.csv)
---

  - [ons-wind_ATB_2023_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_conservative.csv)
---

  - [ons-wind_ATB_2023_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_moderate.csv)
---

  - [ons-wind_ATB_2024_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2024_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** Advanced cost and performance inputs from the 2024 Annual Technology Baseline for land-based wind
    - **Dollar year:** 2022
---

  - [ons-wind_ATB_2024_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2024_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** Conservative cost and performance inputs from the 2024 Annual Technology Baseline for land-based wind
    - **Dollar year:** 2022
---

  - [ons-wind_ATB_2024_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2024_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** Moderate cost and performance inputs from the 2024 Annual Technology Baseline for land-based wind
    - **Dollar year:** 2022
---

  - [outage_forced_static.csv](/inputs/plant_characteristics/outage_forced_static.csv)
    - **File Type:** Inputs file
    - **Description:** Forced outage rates by technology
---

  - [outage_planned_static.csv](/inputs/plant_characteristics/outage_planned_static.csv)
    - **Description:** Planned outage rate by technology
---

  - [pvb_benchmark2020.csv](/inputs/plant_characteristics/pvb_benchmark2020.csv)
---

  - [ramprate.csv](/inputs/plant_characteristics/ramprate.csv)
    - **Description:** Generator ramp rates by technology
---

  - [startcost.csv](/inputs/plant_characteristics/startcost.csv)
---

  - [temperature_outage_forced_murphy2019.csv](/inputs/plant_characteristics/temperature_outage_forced_murphy2019.csv)
---

  - [unitsize.csv](/inputs/plant_characteristics/unitsize.csv)
---

  - [upv_ATB_2023_advanced.csv](/inputs/plant_characteristics/upv_ATB_2023_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 advanced UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2023_conservative.csv](/inputs/plant_characteristics/upv_ATB_2023_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 conservative UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2023_moderate.csv](/inputs/plant_characteristics/upv_ATB_2023_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2023 moderate UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2024_advanced.csv](/inputs/plant_characteristics/upv_ATB_2024_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 advanced UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2024_conservative.csv](/inputs/plant_characteristics/upv_ATB_2024_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 conservative UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [upv_ATB_2024_moderate.csv](/inputs/plant_characteristics/upv_ATB_2024_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2024 moderate UPV capital, FOM and VOM costs, and capacity factor improvement multipliers by year
    - **Dollar year:** 2004
---

  - [years_until_endogenous.csv](/inputs/plant_characteristics/years_until_endogenous.csv)
---


#### [reserves](inputs/reserves) <a name='inputs/reserves'></a>
  - [net_firm_transfers_nerc.csv](/inputs/reserves/net_firm_transfers_nerc.csv)
---

  - [opres_periods.csv](/inputs/reserves/opres_periods.csv)
---

  - [orperc.csv](/inputs/reserves/orperc.csv)
---

  - [prm_annual.csv](/inputs/reserves/prm_annual.csv)
    - **Description:** Annual planning reserve margin by NERC region
---

  - [ramptime.csv](/inputs/reserves/ramptime.csv)
---


#### [sets](inputs/sets) <a name='inputs/sets'></a>
  - [aclike.csv](/inputs/sets/aclike.csv)
    - **File Type:** GAMS set
    - **Description:** set of AC transmission capacity types
---

  - [allt.csv](/inputs/sets/allt.csv)
    - **File Type:** GAMS set
    - **Description:** set of all potential years
---

  - [bioclass.csv](/inputs/sets/bioclass.csv)
    - **File Type:** GAMS set
    - **Description:** set of bio tech classes
---

  - [ccseason.csv](/inputs/sets/ccseason.csv)
    - **File Type:** GAMS set
---

  - [ccsflex_cat.csv](/inputs/sets/ccsflex_cat.csv)
    - **File Type:** GAMS set
    - **Description:** set of flexible ccs performance parameter categories
---

  - [climate_param.csv](/inputs/sets/climate_param.csv)
    - **File Type:** GAMS set
    - **Description:** set of parameters defined in climate_heuristics_finalyear
---

  - [consumecat.csv](/inputs/sets/consumecat.csv)
    - **File Type:** GAMS set
    - **Description:** set of categories for consuming facility characteristics
---

  - [csapr_cat.csv](/inputs/sets/csapr_cat.csv)
    - **File Type:** GAMS set
    - **Description:** set of CSAPR regulation categories
---

  - [csapr_group.csv](/inputs/sets/csapr_group.csv)
    - **File Type:** GAMS set
    - **Description:** set of CSAPR trading groups
---

  - [ctt.csv](/inputs/sets/ctt.csv)
    - **File Type:** GAMS set
    - **Description:** set of cooling technology types
---

  - [dupv_upv_corr.csv](/inputs/sets/dupv_upv_corr.csv)
    - **File Type:** GAMS set
    - **Description:** correlation set for cost of capital calculations of dupv
---

  - [e.csv](/inputs/sets/e.csv)
    - **File Type:** GAMS set
    - **Description:** set of emission categories used in model
---

  - [eall.csv](/inputs/sets/eall.csv)
    - **File Type:** GAMS set
    - **Description:** set of emission categories used in reporting
---

  - [f.csv](/inputs/sets/f.csv)
    - **File Type:** GAMS set
    - **Description:** set of fuel types
---

  - [flex_type.csv](/inputs/sets/flex_type.csv)
    - **File Type:** GAMS set
    - **Description:** set of demand flexibility types
---

  - [fuel2tech.csv](/inputs/sets/fuel2tech.csv)
    - **File Type:** GAMS set
    - **Description:** mapping between fuel types and generations
---

  - [fuelbin.csv](/inputs/sets/fuelbin.csv)
    - **File Type:** GAMS set
    - **Description:** set of gas usage brackets
---

  - [gb.csv](/inputs/sets/gb.csv)
    - **File Type:** GAMS set
    - **Description:** set of gas price bins
---

  - [gbin.csv](/inputs/sets/gbin.csv)
    - **File Type:** GAMS set
    - **Description:** set of growth bins
---

  - [geotech.csv](/inputs/sets/geotech.csv)
    - **File Type:** GAMS set
    - **Description:** set of geothermal technology categories
---

  - [h2_st.csv](/inputs/sets/h2_st.csv)
    - **File Type:** GAMS set
    - **Description:** defines investments needed to store and transport H2
---

  - [h2_stor.csv](/inputs/sets/h2_stor.csv)
    - **File Type:** GAMS set
    - **Description:** set of H2 storage options
---

  - [hintage_char.csv](/inputs/sets/hintage_char.csv)
    - **File Type:** GAMS set
    - **Description:** set of characteristics available in hintage_data
---

  - [i.csv](/inputs/sets/i.csv)
    - **File Type:** GAMS set
    - **Description:** set of technologies
---

  - [i_geotech.csv](/inputs/sets/i_geotech.csv)
    - **File Type:** GAMS set
    - **Description:** crosswalk between an individual geothermal technology and its category
---

  - [i_h2_ptc_gen.csv](/inputs/sets/i_h2_ptc_gen.csv)
    - **File Type:** GAMS set
    - **Description:** set of technologies which can produce energy for electrolyzers claiming the hydrogen production tax credit due to their low lifecycle carbon emissions
---

  - [i_p.csv](/inputs/sets/i_p.csv)
    - **File Type:** GAMS set
    - **Description:** mapping from technologies to the products they produce
---

  - [i_subtech.csv](/inputs/sets/i_subtech.csv)
    - **File Type:** GAMS set
    - **Description:** set of categories for subtechs
---

  - [i_water_nocooling.csv](/inputs/sets/i_water_nocooling.csv)
    - **File Type:** GAMS set
    - **Description:** set of technologies that use water, but are not differentiated by cooling tech and water source
---

  - [lcclike.csv](/inputs/sets/lcclike.csv)
    - **File Type:** GAMS set
    - **Description:** set of transmission capacity types where lines are bundled with AC/DC converters
---

  - [month.csv](/inputs/sets/month.csv)
    - **File Type:** GAMS set
---

  - [noretire.csv](/inputs/sets/noretire.csv)
    - **File Type:** GAMS set
    - **Description:** set of technologies that will never be retired
---

  - [notvsc.csv](/inputs/sets/notvsc.csv)
    - **File Type:** GAMS set
    - **Description:** set of transmission capacity types that are not VSC
---

  - [ofstype.csv](/inputs/sets/ofstype.csv)
    - **File Type:** GAMS set
    - **Description:** set of offshore types used in offshore requirement constraint (eq_RPS_OFSWind)
---

  - [ofstype_i.csv](/inputs/sets/ofstype_i.csv)
    - **File Type:** GAMS set
    - **Description:** crosswalk between ofstype and i
---

  - [orcat.csv](/inputs/sets/orcat.csv)
    - **File Type:** GAMS set
    - **Description:** set of operating reserve categories
---

  - [ortype.csv](/inputs/sets/ortype.csv)
    - **File Type:** GAMS set
    - **Description:** set of types of operating reserve constraints
---

  - [p.csv](/inputs/sets/p.csv)
    - **File Type:** GAMS set
    - **Description:** set of products produced
---

  - [pcat.csv](/inputs/sets/pcat.csv)
    - **File Type:** GAMS set
    - **Description:** set of prescribed technology categories
---

  - [plantcat.csv](/inputs/sets/plantcat.csv)
    - **File Type:** GAMS set
    - **Description:** set of categories for plant characteristics
---

  - [prepost.csv](/inputs/sets/prepost.csv)
    - **File Type:** GAMS set
---

  - [prescriptivelink0.csv](/inputs/sets/prescriptivelink0.csv)
    - **File Type:** GAMS set
    - **Description:** initial set of prescribed categories and their technologies - used in assigning prescribed builds
---

  - [pvb_agg.csv](/inputs/sets/pvb_agg.csv)
    - **File Type:** GAMS set
    - **Description:** crosswalk between hybrid pv+battery configurations and technology options
---

  - [pvb_config.csv](/inputs/sets/pvb_config.csv)
    - **File Type:** GAMS set
    - **Description:** set of hybrid pv+battery configurations
---

  - [quarter.csv](/inputs/sets/quarter.csv)
    - **File Type:** GAMS set
---

  - [resourceclass.csv](/inputs/sets/resourceclass.csv)
    - **File Type:** GAMS set
    - **Description:** set of renewable resource classes
---

  - [RPSCat.csv](/inputs/sets/RPSCat.csv)
    - **File Type:** GAMS set
    - **Description:** set of RPS constraint categories, including clean energy standards
---

  - [sc_cat.csv](/inputs/sets/sc_cat.csv)
    - **File Type:** GAMS set
    - **Description:** set of supply curve categories (capacity and cost)
---

  - [sdbin.csv](/inputs/sets/sdbin.csv)
    - **File Type:** GAMS set
    - **Description:** set of storage durage bins
---

  - [sw.csv](/inputs/sets/sw.csv)
    - **File Type:** GAMS set
    - **Description:** set of surface water types where access is based on consumption not withdrawal
---

  - [tg.csv](/inputs/sets/tg.csv)
    - **File Type:** GAMS set
    - **Description:** set of technology groups
---

  - [tg_rsc_cspagg.csv](/inputs/sets/tg_rsc_cspagg.csv)
    - **File Type:** GAMS set
    - **Description:** set of csp technologies that belong to the same class
---

  - [tg_rsc_upvagg.csv](/inputs/sets/tg_rsc_upvagg.csv)
    - **File Type:** GAMS set
    - **Description:** set of pv and pvb technologies that belong to the same class
---

  - [trancap_fut_cat.csv](/inputs/sets/trancap_fut_cat.csv)
    - **File Type:** GAMS set
    - **Description:** set of categories of near-term transmission projects that describe the likelihood of being completed
---

  - [trtype.csv](/inputs/sets/trtype.csv)
    - **File Type:** GAMS set
    - **Description:** set of transmission capacity types
---

  - [unitspec_upgrades.csv](/inputs/sets/unitspec_upgrades.csv)
    - **File Type:** GAMS set
    - **Description:** set of upgraded technologies that get unit-specific characteristics
---

  - [upgrade_hintage_char.csv](/inputs/sets/upgrade_hintage_char.csv)
    - **File Type:** GAMS set
    - **Description:** set to operate over in extension of hintage_data characteristics when sw_upgrades = 1
---

  - [w.csv](/inputs/sets/w.csv)
    - **File Type:** GAMS set
    - **Description:** set of water withdrawal or consumption options for water techs
---

  - [wst.csv](/inputs/sets/wst.csv)
    - **File Type:** GAMS set
    - **Description:** set of water source types
---

  - [wst_climate.csv](/inputs/sets/wst_climate.csv)
    - **File Type:** GAMS set
    - **Description:** set of water sources affected by climate change
---

  - [yearafter.csv](/inputs/sets/yearafter.csv)
    - **File Type:** GAMS set
    - **Description:** set to loop over for the final year calculation
---


#### [shapefiles](inputs/shapefiles) <a name='inputs/shapefiles'></a>
  - [ctus_cs_polygons_BVRE.csv](/inputs/shapefiles/ctus_cs_polygons_BVRE.csv)
---

  - [ctus_r_cs_spurlines_200mi.csv](/inputs/shapefiles/ctus_r_cs_spurlines_200mi.csv)
---

  - [r_rr_lines_to_25_nearest_neighbors.csv](/inputs/shapefiles/r_rr_lines_to_25_nearest_neighbors.csv)
---

  - [state_fips_codes.csv](/inputs/shapefiles/state_fips_codes.csv)
    - **Description:** Mapping of states to FIPS codes and postcal code abbreviations
---

  - [US_CAN_MEX_PCA_polygons.csv](/inputs/shapefiles/US_CAN_MEX_PCA_polygons.csv)
---

  - [US_transmission_endpoints_and_CAN_MEX_centroids.csv](/inputs/shapefiles/US_transmission_endpoints_and_CAN_MEX_centroids.csv)
---


##### [WKT_csvs](inputs/shapefiles/WKT_csvs) <a name='inputs/shapefiles/WKT_csvs'></a>
  - [cendiv_WKT.csv](/inputs/shapefiles/WKT_csvs/cendiv_WKT.csv)
---

  - [country_WKT.csv](/inputs/shapefiles/WKT_csvs/country_WKT.csv)
---

  - [customreg_WKT.csv](/inputs/shapefiles/WKT_csvs/customreg_WKT.csv)
---

  - [interconnect_WKT.csv](/inputs/shapefiles/WKT_csvs/interconnect_WKT.csv)
---

  - [nerc_new_WKT.csv](/inputs/shapefiles/WKT_csvs/nerc_new_WKT.csv)
---

  - [nerc_WKT.csv](/inputs/shapefiles/WKT_csvs/nerc_WKT.csv)
---

  - [rto_WKT.csv](/inputs/shapefiles/WKT_csvs/rto_WKT.csv)
---

  - [st_WKT.csv](/inputs/shapefiles/WKT_csvs/st_WKT.csv)
---

  - [transreg_WKT.csv](/inputs/shapefiles/WKT_csvs/transreg_WKT.csv)
---

  - [usda_WKT.csv](/inputs/shapefiles/WKT_csvs/usda_WKT.csv)
---


#### [state_policies](inputs/state_policies) <a name='inputs/state_policies'></a>
  - [acp_disallowed.csv](/inputs/state_policies/acp_disallowed.csv)
    - **Description:** List of states which do not allow alternative compliance payments in place of meeting RPS or CES requirements 
---

  - [acp_prices.csv](/inputs/state_policies/acp_prices.csv)
---

  - [ces_fraction.csv](/inputs/state_policies/ces_fraction.csv)
    - **Description:** Annual compliance for states with a CES policy
---

  - [forced_retirements.csv](/inputs/state_policies/forced_retirements.csv)
    - **Description:** List of regions with mandatory retirement policies for certain technologies
---

  - [hydrofrac_policy.csv](/inputs/state_policies/hydrofrac_policy.csv)
---

  - [ng_crf_penalty_st.csv](/inputs/state_policies/ng_crf_penalty_st.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment for NG techs in states where all NG techs must be retired by a certain year
    - **Indices:** allt,st
    - **Dollar year:** N/A

    - **Citation:** [(https://github.nrel.gov/ReEDS/ReEDS-2.0/pull/1220)]
    - **Units:** rate (unitless)

---

  - [nuclear_ba_ban_list.csv](/inputs/state_policies/nuclear_ba_ban_list.csv)
    - **Description:** List of BAs where nuclear technology development is banned.
---

  - [nuclear_subsidies.csv](/inputs/state_policies/nuclear_subsidies.csv)
---

  - [offshore_req_default.csv](/inputs/state_policies/offshore_req_default.csv)
    - **File Type:** Inputs
    - **Description:** default state mandates of offshore wind capacity
    - **Indices:** st,allt
---

  - [oosfrac.csv](/inputs/state_policies/oosfrac.csv)
    - **Description:** Defines the fraction of renewable and clean energy credits can be purchased from out of state (oos). Applied for RPS and CES
---

  - [recstyle.csv](/inputs/state_policies/recstyle.csv)
    - **Description:** Indication for how to apply state requirement (0 = end-use sales, 1 = bus-bar sales, 2 = generation). Default is 0.
---

  - [rectable.csv](/inputs/state_policies/rectable.csv)
    - **Description:** Table defining which states are allowed to trade RECs
---

  - [rps_fraction.csv](/inputs/state_policies/rps_fraction.csv)
    - **Description:** Indicates what fraction of sales or generation (based on recstyle.csv) must be from renewable energy 
---

  - [storage_mandates.csv](/inputs/state_policies/storage_mandates.csv)
    - **Description:** Energy storage mandates by region
---

  - [techs_banned.csv](/inputs/state_policies/techs_banned.csv)
    - **Description:** Table that bans certain technologies by state
---

  - [techs_banned_ces.csv](/inputs/state_policies/techs_banned_ces.csv)
    - **Description:** Indicates which technolgies are not eligible to contribute to CES 
---

  - [techs_banned_imports_rps.csv](/inputs/state_policies/techs_banned_imports_rps.csv)
---

  - [techs_banned_rps.csv](/inputs/state_policies/techs_banned_rps.csv)
    - **Description:** Indicates which technolgies are not eligible to contribute to RPS
---

  - [unbundled_limit_ces.csv](/inputs/state_policies/unbundled_limit_ces.csv)
    - **Description:** Limit on fraction of credits towards CES which can be purchased unbundled from other states 
---

  - [unbundled_limit_rps.csv](/inputs/state_policies/unbundled_limit_rps.csv)
    - **Description:** Limit on fraction of credits towards RPS which can be purchased unbundled from other states 
---


#### [storage](inputs/storage) <a name='inputs/storage'></a>
  - [PSH_supply_curves_durations.csv](/inputs/storage/PSH_supply_curves_durations.csv)
---

  - [storage_duration.csv](/inputs/storage/storage_duration.csv)
---

  - [storage_duration_pshdata.csv](/inputs/storage/storage_duration_pshdata.csv)
---

  - [storinmaxfrac.csv](/inputs/storage/storinmaxfrac.csv)
---


#### [supply_curve](inputs/supply_curve) <a name='inputs/supply_curve'></a>
  - [bio_supplycurve.csv](/inputs/supply_curve/bio_supplycurve.csv)
    - **Description:** Regional biomass supply and costs by resource class
    - **Dollar year:** 2015
---

  - [csp_supply_curve-reference_ba.csv](/inputs/supply_curve/csp_supply_curve-reference_ba.csv)
    - **Description:** CSP supply curve using reference siting assumptions at the BA resolution
---

  - [csp_supply_curve-reference_county.csv](/inputs/supply_curve/csp_supply_curve-reference_county.csv)
    - **Description:** CSP supply curve using reference siting assumptions at the county resolution
---

  - [dollaryear.csv](/inputs/supply_curve/dollaryear.csv)
---

  - [DUPV_supply_curves_capacity_2018.csv](/inputs/supply_curve/DUPV_supply_curves_capacity_2018.csv)
---

  - [DUPV_supply_curves_capacity_NARIS.csv](/inputs/supply_curve/DUPV_supply_curves_capacity_NARIS.csv)
---

  - [DUPV_supply_curves_cost_2018.csv](/inputs/supply_curve/DUPV_supply_curves_cost_2018.csv)
---

  - [DUPV_supply_curves_cost_NARIS.csv](/inputs/supply_curve/DUPV_supply_curves_cost_NARIS.csv)
---

  - [egs_supply_curve-reference_ba.csv](/inputs/supply_curve/egs_supply_curve-reference_ba.csv)
---

  - [egs_supply_curve-reference_county.csv](/inputs/supply_curve/egs_supply_curve-reference_county.csv)
---

  - [geo_supply_curve_site-reference.csv](/inputs/supply_curve/geo_supply_curve_site-reference.csv)
---

  - [geohydro_supply_curve-reference_ba.csv](/inputs/supply_curve/geohydro_supply_curve-reference_ba.csv)
---

  - [geohydro_supply_curve-reference_county.csv](/inputs/supply_curve/geohydro_supply_curve-reference_county.csv)
---

  - [hyd_add_upg_cap.csv](/inputs/supply_curve/hyd_add_upg_cap.csv)
---

  - [hydcap.csv](/inputs/supply_curve/hydcap.csv)
---

  - [hydcost.csv](/inputs/supply_curve/hydcost.csv)
---

  - [PSH_supply_curves_capacity_10hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_ref_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and reference exclusions as used in 2023 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_10hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_ref_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and reference exclusions as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_10hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_10hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_10hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_10hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_10hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 10 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_12hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_ref_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and reference exclusions as used in 2023 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_12hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_ref_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and reference exclusions as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_12hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_12hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_12hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_12hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_12hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 12 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_8hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_ref_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and reference exclusions as used in 2023 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_8hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_ref_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and reference exclusions as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_8hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_8hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_8hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_capacity_8hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_capacity_8hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve capacity assuming 8 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_10hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_ref_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and reference exclusions as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_10hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_ref_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and reference exclusions as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_10hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_10hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_10hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_10hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_10hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 10 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_12hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_ref_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and reference exclusions as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_12hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_ref_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and reference exclusions as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_12hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_12hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_12hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_12hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_12hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 12 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_8hr_ref_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_ref_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and reference exclusions as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_8hr_ref_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_ref_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and reference exclusions as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_8hr_wEphemeral_dec2022.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_wEphemeral_dec2022.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and allowing sites on ephemeral streams as used in 2023 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_8hr_wEphemeral_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_wEphemeral_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and allowing sites on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_8hr_wExist_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_wExist_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and allowing sites using existing reservoirs as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [PSH_supply_curves_cost_8hr_wExist_wEph_mar2024.csv](/inputs/supply_curve/PSH_supply_curves_cost_8hr_wExist_wEph_mar2024.csv)
    - **Description:** PSH supply curve cost assuming 8 hour duration and allowing sites  using existing reservoirs and on ephemeral streams as used in 2024 Annual Technology Baseline
    - **Dollar year:** 2004

    - **Citation:** [(https://www.nrel.gov/gis/psh-supply-curves.html)]
---

  - [rev_paths.csv](/inputs/supply_curve/rev_paths.csv)
---

  - [sitemap.csv](/inputs/supply_curve/sitemap.csv)
---

  - [sitemap_offshore.csv](/inputs/supply_curve/sitemap_offshore.csv)
---

  - [spurline_cost.csv](/inputs/supply_curve/spurline_cost.csv)
---

  - [trans_intra_cost_adder.csv](/inputs/supply_curve/trans_intra_cost_adder.csv)
---

  - [upv_supply_curve-limited_ba.csv](/inputs/supply_curve/upv_supply_curve-limited_ba.csv)
    - **Description:** UPV supply curve using limited siting assumptions at the BA resolution
---

  - [upv_supply_curve-limited_county.csv](/inputs/supply_curve/upv_supply_curve-limited_county.csv)
    - **Description:** UPV supply curve using limited siting assumptions at the county resolution
---

  - [upv_supply_curve-open_ba.csv](/inputs/supply_curve/upv_supply_curve-open_ba.csv)
    - **Description:** UPV supply curve using open siting assumptions at the BA resolution
---

  - [upv_supply_curve-open_county.csv](/inputs/supply_curve/upv_supply_curve-open_county.csv)
    - **Description:** UPV supply curve using open siting assumptions at the county resolution
---

  - [upv_supply_curve-reference_ba.csv](/inputs/supply_curve/upv_supply_curve-reference_ba.csv)
    - **Description:** UPV supply curve using reference siting assumptions at the BA resolution
---

  - [upv_supply_curve-reference_county.csv](/inputs/supply_curve/upv_supply_curve-reference_county.csv)
    - **Description:** UPV supply curve using reference siting assumptions at the county resolution
---

  - [wind-ofs_supply_curve-limited_ba.csv](/inputs/supply_curve/wind-ofs_supply_curve-limited_ba.csv)
    - **Description:** wind-ofs supply curve using limited siting assumptions at the BA resolution
---

  - [wind-ofs_supply_curve-limited_county.csv](/inputs/supply_curve/wind-ofs_supply_curve-limited_county.csv)
    - **Description:** wind-ofs supply curve using limited siting assumptions at the county resolution
---

  - [wind-ofs_supply_curve-open_ba.csv](/inputs/supply_curve/wind-ofs_supply_curve-open_ba.csv)
    - **Description:** wind-ofs supply curve using open siting assumptions at the BA resolution
---

  - [wind-ofs_supply_curve-open_county.csv](/inputs/supply_curve/wind-ofs_supply_curve-open_county.csv)
    - **Description:** wind-ofs supply curve using open siting assumptions at the county resolution
---

  - [wind-ofs_supply_curve-reference_ba.csv](/inputs/supply_curve/wind-ofs_supply_curve-reference_ba.csv)
---

  - [wind-ofs_supply_curve-reference_county.csv](/inputs/supply_curve/wind-ofs_supply_curve-reference_county.csv)
---

  - [wind-ons_supply_curve-limited_ba.csv](/inputs/supply_curve/wind-ons_supply_curve-limited_ba.csv)
    - **Description:** wind-ons supply curve using limited siting assumptions at the BA resolution
---

  - [wind-ons_supply_curve-limited_county.csv](/inputs/supply_curve/wind-ons_supply_curve-limited_county.csv)
    - **Description:** wind-ons supply curve using limited siting assumptions at the county resolution
---

  - [wind-ons_supply_curve-open_ba.csv](/inputs/supply_curve/wind-ons_supply_curve-open_ba.csv)
    - **Description:** wind-ons supply curve using open siting assumptions at the BA resolution
---

  - [wind-ons_supply_curve-open_county.csv](/inputs/supply_curve/wind-ons_supply_curve-open_county.csv)
    - **Description:** wind-ons supply curve using open siting assumptions at the county resolution
---

  - [wind-ons_supply_curve-reference_ba.csv](/inputs/supply_curve/wind-ons_supply_curve-reference_ba.csv)
    - **Description:** wind-ons supply curve using reference siting assumptions at the BA resolution
---

  - [wind-ons_supply_curve-reference_county.csv](/inputs/supply_curve/wind-ons_supply_curve-reference_county.csv)
    - **Description:** wind-ons supply curve using reference siting assumptions at the county resolution
---


#### [techs](inputs/techs) <a name='inputs/techs'></a>
  - [tech_resourceclass.csv](/inputs/techs/tech_resourceclass.csv)
---

  - [techs_default.csv](/inputs/techs/techs_default.csv)
    - **Description:** List of technologies to be used in the model
---

  - [techs_subsetForTesting.csv](/inputs/techs/techs_subsetForTesting.csv)
    - **Description:** Short list of technologies for testin
---


#### [transmission](inputs/transmission) <a name='inputs/transmission'></a>
  - [cost_hurdle_country.csv](/inputs/transmission/cost_hurdle_country.csv)
    - **File Type:** GAMS set
    - **Description:** Cost for transmission hurdle rate by country
    - **Indices:** country
    - **Dollar year:** 2004
---

  - [cost_hurdle_intra.csv](/inputs/transmission/cost_hurdle_intra.csv)
---

  - [r_rr_adj_ba.csv](/inputs/transmission/r_rr_adj_ba.csv)
    - **Description:** Set of adjacent regions at BA resolution
---

  - [r_rr_adj_county.csv](/inputs/transmission/r_rr_adj_county.csv)
    - **Description:** Set of adjacent regions at county resolution
---

  - [rev_transmission_basecost.csv](/inputs/transmission/rev_transmission_basecost.csv)
    - **File Type:** inputs
    - **Description:** Unweighted average base cost across the four regions for which we have transmission cost data.
    - **Indices:** Transreg
    - **Dollar year:** 2004
---

  - [transmission_capacity_future_ba_baseline.csv](/inputs/transmission/transmission_capacity_future_ba_baseline.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the baseline case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_default.csv](/inputs/transmission/transmission_capacity_future_ba_default.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the default case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_all.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_all.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_all case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_SeamsD2b.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_SeamsD2b.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_SeamsD2B case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_SeamsD3_certain.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_SeamsD3_certain.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_SeamsD3_certain case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_SeamsD3_possible.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_SeamsD3_possible.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_SeamsD3_possible case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_LCC_SeamsD3_possible_unconstrained.csv](/inputs/transmission/transmission_capacity_future_ba_LCC_SeamsD3_possible_unconstrained.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_SeamsD3_possible_unconstrained case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_ba_VSC_all.csv](/inputs/transmission/transmission_capacity_future_ba_VSC_all.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the VSC_all_case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_county_baseline.csv](/inputs/transmission/transmission_capacity_future_county_baseline.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the baseline case at county resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_county_default.csv](/inputs/transmission/transmission_capacity_future_county_default.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the default case at county resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_future_LCC_1000miles_demand1_wind1_subferc_20230629.csv](/inputs/transmission/transmission_capacity_future_LCC_1000miles_demand1_wind1_subferc_20230629.csv)
    - **File Type:** inputs
    - **Description:** Future transmission capacity additions for the LCC_1000miles_demand1_wind1_subferc_20230629 case at BA resolution
    - **Indices:** r,rr
---

  - [transmission_capacity_init_AC_ba_NARIS2024.csv](/inputs/transmission/transmission_capacity_init_AC_ba_NARIS2024.csv)
    - **Description:** Initial AC transmission capacity from the NARIS 2024 system at the BA resolution - 'NARIS2024' is a better starting point for future-oriented studies, but it becomes increasingly inaccurate for years earlier than 2024
---

  - [transmission_capacity_init_AC_ba_REFS2009.csv](/inputs/transmission/transmission_capacity_init_AC_ba_REFS2009.csv)
    - **Description:** Initial AC transmission capacity from the 2009 transmission system for ReEDS at the BA resolution - 'REFS2009' does not inclue direction-dependent capacities or differentiated capacities for energy and PRM trading but it better represents historical additions between 2010-2024
---

  - [transmission_capacity_init_AC_county_NARIS2024.csv](/inputs/transmission/transmission_capacity_init_AC_county_NARIS2024.csv)
    - **Description:** Initial AC transmission capacity from the NARIS 2024 system at the county resolution
---

  - [transmission_capacity_init_AC_transgrp_NARIS2024.csv](/inputs/transmission/transmission_capacity_init_AC_transgrp_NARIS2024.csv)
    - **Description:** Initial AC transmission capacity from the NARIS 2024 system at the transgrp resolution
---

  - [transmission_capacity_init_nonAC_ba.csv](/inputs/transmission/transmission_capacity_init_nonAC_ba.csv)
    - **Description:** Initial non-AC transmission capacity at the BA resolution
---

  - [transmission_capacity_init_nonAC_county.csv](/inputs/transmission/transmission_capacity_init_nonAC_county.csv)
    - **Description:** Initial non-AC transmission capacity at the county resolution
---

  - [transmission_distance_cost_500kVac_ba.csv](/inputs/transmission/transmission_distance_cost_500kVac_ba.csv)
    - **Description:** Transmission distance and costs for 500 kV AC at BA resolution
---

  - [transmission_distance_cost_500kVac_county.csv](/inputs/transmission/transmission_distance_cost_500kVac_county.csv)
    - **Description:** Transmission distance and costs for 500 kV AC at county resolution
---

  - [transmission_distance_cost_500kVdc_ba.csv](/inputs/transmission/transmission_distance_cost_500kVdc_ba.csv)
    - **Description:** Transmission distance and costs for 500 kV DC at BA resolution
---

  - [transmission_distance_cost_500kVdc_county.csv](/inputs/transmission/transmission_distance_cost_500kVdc_county.csv)
    - **Description:** Transmission distance and costs for 500 kV DC at county resolution
---


#### [upgrades](inputs/upgrades) <a name='inputs/upgrades'></a>
  - [i_coolingtech_watersource_upgrades.csv](/inputs/upgrades/i_coolingtech_watersource_upgrades.csv)
    - **File Type:** Inputs
    - **Description:** List of cooling technologies for water sources that can be upgraded.
    - **Indices:** i
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [i_coolingtech_watersource_upgrades_link.csv](/inputs/upgrades/i_coolingtech_watersource_upgrades_link.csv)
    - **File Type:** Inputs
    - **Description:** List of cooling technologies for water sources that can be upgraded + their to, from, ctt (cooling technology type) and wst (water source type)
    - **Indices:** i, ctt, wst
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [upgrade_costs_ccs_coal.csv](/inputs/upgrades/upgrade_costs_ccs_coal.csv)
---

  - [upgrade_costs_ccs_gas.csv](/inputs/upgrades/upgrade_costs_ccs_gas.csv)
---

  - [upgrade_link.csv](/inputs/upgrades/upgrade_link.csv)
    - **File Type:** Inputs
    - **Description:** Techs that can be upgraded including the original technology, the technology it is upgrading to, and the delta.
    - **Indices:** i
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [upgrade_mult_atb23_ccs_adv.csv](/inputs/upgrades/upgrade_mult_atb23_ccs_adv.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment (advanced) over various years for upgrade technologies
    - **Indices:** i,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [upgrade_mult_atb23_ccs_con.csv](/inputs/upgrades/upgrade_mult_atb23_ccs_con.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment (conservative) over various years for upgrade technologies
    - **Indices:** i,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [upgrade_mult_atb23_ccs_mid.csv](/inputs/upgrades/upgrade_mult_atb23_ccs_mid.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment (Mid) over various years for upgrade technologies
    - **Indices:** i,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [upgradelink_water.csv](/inputs/upgrades/upgradelink_water.csv)
    - **File Type:** Inputs
    - **Description:** Water techs that can be upgraded including the original technology, the technology it is upgrading to, and the delta (a H2-CT)
    - **Indices:** i
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---


#### [userinput](inputs/userinput) <a name='inputs/userinput'></a>
  - [futurefiles.csv](/inputs/userinput/futurefiles.csv)
---

  - [ivt_default.csv](/inputs/userinput/ivt_default.csv)
---

  - [ivt_small.csv](/inputs/userinput/ivt_small.csv)
---

  - [ivt_step.csv](/inputs/userinput/ivt_step.csv)
    - **Description:** ivt steps for endyears beyond 2050
---

  - [modeled_regions.csv](/inputs/userinput/modeled_regions.csv)
    - **Description:** Sets of BA regions that a user can model in a run. Each column is a different region option and can be specified in cases using GSw_Region.
---

  - [windows_2100.csv](/inputs/userinput/windows_2100.csv)
    - **Description:** Window size for using window solve method to 2100
---

  - [windows_default.csv](/inputs/userinput/windows_default.csv)
    - **Description:** Window size for using window solve method
---

  - [windows_step10.csv](/inputs/userinput/windows_step10.csv)
    - **Description:** Window size for beyond2050step10
---

  - [windows_step5.csv](/inputs/userinput/windows_step5.csv)
    - **Description:** Window size for beyond2050step5
---


#### [valuestreams](inputs/valuestreams) <a name='inputs/valuestreams'></a>
  - [var_map.csv](/inputs/valuestreams/var_map.csv)
---


#### [variability](inputs/variability) <a name='inputs/variability'></a>
  - [d_szn_1yr.csv](/inputs/variability/d_szn_1yr.csv)
---

  - [d_szn_7yr.csv](/inputs/variability/d_szn_7yr.csv)
---

  - [h_dt_szn.csv](/inputs/variability/h_dt_szn.csv)
---

  - [hourly_operational_characteristics.csv](/inputs/variability/hourly_operational_characteristics.csv)
---

  - [index_hr_map_1.csv](/inputs/variability/index_hr_map_1.csv)
    - **Description:** Mapping for day set to season for a single year (365 days)
---

  - [index_hr_map_7.csv](/inputs/variability/index_hr_map_7.csv)
    - **Description:** Mapping for day set to season for a 7 years (2555 days)
---

  - [period_szn_user.csv](/inputs/variability/period_szn_user.csv)
---

  - [reeds_region_tz_map.csv](/inputs/variability/reeds_region_tz_map.csv)
---

  - [set_allszn.csv](/inputs/variability/set_allszn.csv)
---

  - [set_szn.csv](/inputs/variability/set_szn.csv)
---

  - [stressperiods_user.csv](/inputs/variability/stressperiods_user.csv)
---


##### [multi_year](inputs/variability/multi_year) <a name='inputs/variability/multi_year'></a>
  - [csp-none_ba.h5](/inputs/variability/multi_year/csp-none_ba.h5)
    - **Description:** Concentrated Solar Power resource supply curve. Data is a capacity factor i.e. a fraction.
---

  - [distpv-reference_ba.h5](/inputs/variability/multi_year/distpv-reference_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Distributed photovoltaics resource supply curve. Data is a capacity factor i.e. a fraction.
    - **Indices:** r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [temperature_celsius-ba.h5](/inputs/variability/multi_year/temperature_celsius-ba.h5)
---

  - [upv-limited_ba.h5](/inputs/variability/multi_year/upv-limited_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Utility scale photovoltaics resource supply curve using Limited access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [upv-open_ba.h5](/inputs/variability/multi_year/upv-open_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Utility scale photovoltaics resource supply curve using Open access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [upv-reference_ba.h5](/inputs/variability/multi_year/upv-reference_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Utility scale photovoltaics resource supply curve using Reference access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [upv_140AC-reference_ba.h5](/inputs/variability/multi_year/upv_140AC-reference_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Utility scale photovoltaics resource supply curve (AC, using a 1.40 Inverter Load Ratio) using Reference access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [upv_220AC-reference_ba.h5](/inputs/variability/multi_year/upv_220AC-reference_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Utility scale photovoltaics resource supply curve (AC, using a 2.20 Inverter Load Ratio) using Reference access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [wind-ofs-limited_ba.h5](/inputs/variability/multi_year/wind-ofs-limited_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Offshore wind resource supply curve using Limited access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [wind-ofs-open_ba.h5](/inputs/variability/multi_year/wind-ofs-open_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Offshore wind resource supply curve using Open access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [wind-ofs-reference_ba.h5](/inputs/variability/multi_year/wind-ofs-reference_ba.h5)
---

  - [wind-ons-limited_ba.h5](/inputs/variability/multi_year/wind-ons-limited_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Land-based wind resource supply curve using Limited access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [wind-ons-open_ba.h5](/inputs/variability/multi_year/wind-ons-open_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Land-based wind resource supply curve using Open access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---

  - [wind-ons-reference_ba.h5](/inputs/variability/multi_year/wind-ons-reference_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Land-based wind resource supply curve using Reference access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]
---


#### [waterclimate](inputs/waterclimate) <a name='inputs/waterclimate'></a>
  - [cost_cap_mult.csv](/inputs/waterclimate/cost_cap_mult.csv)
---

  - [cost_vom_mult.csv](/inputs/waterclimate/cost_vom_mult.csv)
---

  - [heat_rate_mult.csv](/inputs/waterclimate/heat_rate_mult.csv)
---

  - [i_coolingtech_watersource.csv](/inputs/waterclimate/i_coolingtech_watersource.csv)
---

  - [i_coolingtech_watersource_link.csv](/inputs/waterclimate/i_coolingtech_watersource_link.csv)
---

  - [tg_rsc_cspagg_tmp.csv](/inputs/waterclimate/tg_rsc_cspagg_tmp.csv)
---

  - [unapp_water_sea_distr.csv](/inputs/waterclimate/unapp_water_sea_distr.csv)
---

  - [wat_access_cap_cost.csv](/inputs/waterclimate/wat_access_cap_cost.csv)
---

  - [water_req_psh_10h_1_51.csv](/inputs/waterclimate/water_req_psh_10h_1_51.csv)
---

  - [water_with_cons_rate.csv](/inputs/waterclimate/water_with_cons_rate.csv)
---


### [postprocessing](postprocessing) <a name='postprocessing'></a>
  - [example.csv](/postprocessing/example.csv)
---


#### [air_quality](postprocessing/air_quality) <a name='postprocessing/air_quality'></a>
  - [scenarios.csv](/postprocessing/air_quality/scenarios.csv)
---


##### [rcm_data](postprocessing/air_quality/rcm_data) <a name='postprocessing/air_quality/rcm_data'></a>
  - [counties_ACS_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/counties_ACS_high_stack_2017.csv)
---

  - [counties_H6C_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/counties_H6C_high_stack_2017.csv)
---

  - [states_ACS_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/states_ACS_high_stack_2017.csv)
---

  - [states_H6C_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/states_H6C_high_stack_2017.csv)
---


#### [bokehpivot](postprocessing/bokehpivot) <a name='postprocessing/bokehpivot'></a>
  - [reeds_scenarios.csv](/postprocessing/bokehpivot/reeds_scenarios.csv)
    - **Description:** Example data for ReEDS scenarios, each scenario with a custom style 
---


##### [in](postprocessing/bokehpivot/in) <a name='postprocessing/bokehpivot/in'></a>
  - [example_custom_styles.csv](/postprocessing/bokehpivot/in/example_custom_styles.csv)
    - **Description:** Examples of custom styles used for bokehpivot
---

  - [example_data_US_electric_power_generation.csv](/postprocessing/bokehpivot/in/example_data_US_electric_power_generation.csv)
    - **Description:** Example data for US electric power generation
---

  - [gis_centroid_rb.csv](/postprocessing/bokehpivot/in/gis_centroid_rb.csv)
---

  - [gis_nercr.csv](/postprocessing/bokehpivot/in/gis_nercr.csv)
---

  - [gis_nercr_new.csv](/postprocessing/bokehpivot/in/gis_nercr_new.csv)
---

  - [gis_rb.csv](/postprocessing/bokehpivot/in/gis_rb.csv)
---

  - [gis_rs.csv](/postprocessing/bokehpivot/in/gis_rs.csv)
---

  - [gis_rto.csv](/postprocessing/bokehpivot/in/gis_rto.csv)
---

  - [gis_st.csv](/postprocessing/bokehpivot/in/gis_st.csv)
---

  - [state_code.csv](/postprocessing/bokehpivot/in/state_code.csv)
    - **Description:** Abbreviation and code for each state
---


###### [reeds2](postprocessing/bokehpivot/in/reeds2) <a name='postprocessing/bokehpivot/in/reeds2'></a>
  - [class_map.csv](/postprocessing/bokehpivot/in/reeds2/class_map.csv)
    - **Description:** Class mapping for bokehpivot postprocessing
---

  - [class_style.csv](/postprocessing/bokehpivot/in/reeds2/class_style.csv)
    - **Description:** Custom styles for classes in bokehpivot 
---

  - [con_adj_map.csv](/postprocessing/bokehpivot/in/reeds2/con_adj_map.csv)
---

  - [con_adj_style.csv](/postprocessing/bokehpivot/in/reeds2/con_adj_style.csv)
---

  - [cost_cat_map.csv](/postprocessing/bokehpivot/in/reeds2/cost_cat_map.csv)
---

  - [cost_cat_style.csv](/postprocessing/bokehpivot/in/reeds2/cost_cat_style.csv)
---

  - [ctt_map.csv](/postprocessing/bokehpivot/in/reeds2/ctt_map.csv)
---

  - [ctt_style.csv](/postprocessing/bokehpivot/in/reeds2/ctt_style.csv)
---

  - [hours.csv](/postprocessing/bokehpivot/in/reeds2/hours.csv)
    - **Description:** Hours for each of the 17 timeslices
---

  - [m_bar_width.csv](/postprocessing/bokehpivot/in/reeds2/m_bar_width.csv)
---

  - [m_map.csv](/postprocessing/bokehpivot/in/reeds2/m_map.csv)
---

  - [m_style.csv](/postprocessing/bokehpivot/in/reeds2/m_style.csv)
---

  - [process_style.csv](/postprocessing/bokehpivot/in/reeds2/process_style.csv)
---

  - [tech_ctt_wst.csv](/postprocessing/bokehpivot/in/reeds2/tech_ctt_wst.csv)
---

  - [tech_map.csv](/postprocessing/bokehpivot/in/reeds2/tech_map.csv)
---

  - [tech_style.csv](/postprocessing/bokehpivot/in/reeds2/tech_style.csv)
    - **Description:** Custom colors for each technology used by bokehpivot
---

  - [trtype_map.csv](/postprocessing/bokehpivot/in/reeds2/trtype_map.csv)
---

  - [trtype_style.csv](/postprocessing/bokehpivot/in/reeds2/trtype_style.csv)
---

  - [wst_map.csv](/postprocessing/bokehpivot/in/reeds2/wst_map.csv)
---

  - [wst_style.csv](/postprocessing/bokehpivot/in/reeds2/wst_style.csv)
---


#### [combine_runs](postprocessing/combine_runs) <a name='postprocessing/combine_runs'></a>
  - [combinefiles.csv](/postprocessing/combine_runs/combinefiles.csv)
---

  - [runlist.csv](/postprocessing/combine_runs/runlist.csv)
---


#### [land_use](postprocessing/land_use) <a name='postprocessing/land_use'></a>

##### [inputs](postprocessing/land_use/inputs) <a name='postprocessing/land_use/inputs'></a>
  - [federal_land_categories.csv](/postprocessing/land_use/inputs/federal_land_categories.csv)
---

  - [field_definitions.csv](/postprocessing/land_use/inputs/field_definitions.csv)
---

  - [nlcd_categories.csv](/postprocessing/land_use/inputs/nlcd_categories.csv)
---

  - [nlcd_combined_categories.csv](/postprocessing/land_use/inputs/nlcd_combined_categories.csv)
---

  - [usgs_categories.csv](/postprocessing/land_use/inputs/usgs_categories.csv)
---

  - [usgs_combined_categories.csv](/postprocessing/land_use/inputs/usgs_combined_categories.csv)
---


#### [plots](postprocessing/plots) <a name='postprocessing/plots'></a>
  - [scghg_annual.csv](/postprocessing/plots/scghg_annual.csv)
---

  - [transmission-interface-coords.csv](/postprocessing/plots/transmission-interface-coords.csv)
---


#### [retail_rate_module](postprocessing/retail_rate_module) <a name='postprocessing/retail_rate_module'></a>
  - [capital_financing_assumptions.csv](/postprocessing/retail_rate_module/capital_financing_assumptions.csv)
---

  - [df_f861_contiguous.csv](/postprocessing/retail_rate_module/df_f861_contiguous.csv)
---

  - [df_f861_state.csv](/postprocessing/retail_rate_module/df_f861_state.csv)
---

  - [inputs.csv](/postprocessing/retail_rate_module/inputs.csv)
---

  - [inputs_default.csv](/postprocessing/retail_rate_module/inputs_default.csv)
---

  - [load_by_state_eia.csv](/postprocessing/retail_rate_module/load_by_state_eia.csv)
    - **Description:** End use load by state since 1960
---

  - [map_i_to_tech.csv](/postprocessing/retail_rate_module/map_i_to_tech.csv)
    - **Description:** Maps i to tech with custom coloring for each
---


##### [calc_historical_capex](postprocessing/retail_rate_module/calc_historical_capex) <a name='postprocessing/retail_rate_module/calc_historical_capex'></a>
  - [cap_cost_mult_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/cap_cost_mult_for_historical.csv)
---

  - [cost_cap_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/cost_cap_for_historical.csv)
---

  - [df_capex_init.csv](/postprocessing/retail_rate_module/calc_historical_capex/df_capex_init.csv)
---

  - [geo_cap_cost_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/geo_cap_cost_for_historical.csv)
---

  - [regions_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/regions_for_historical.csv)
---

  - [rsc_dat_for_historical.csv](/postprocessing/retail_rate_module/calc_historical_capex/rsc_dat_for_historical.csv)
---


##### [inputs](postprocessing/retail_rate_module/inputs) <a name='postprocessing/retail_rate_module/inputs'></a>
  - [Electric O & M Expenses-IOU-1993-2019.csv](/postprocessing/retail_rate_module/inputs/Electric%20O%20&%20M%20Expenses-IOU-1993-2019.csv)
---

  - [Electric Operating Revenues-IOU-1993-2019.csv](/postprocessing/retail_rate_module/inputs/Electric%20Operating%20Revenues-IOU-1993-2019.csv)
---

  - [Electric Plant in Service-IOU-1993-2019.csv](/postprocessing/retail_rate_module/inputs/Electric%20Plant%20in%20Service-IOU-1993-2019.csv)
---

  - [f861_cust_counts.csv](/postprocessing/retail_rate_module/inputs/f861_cust_counts.csv)
---

  - [overwrite-utility-energy_sales.csv](/postprocessing/retail_rate_module/inputs/overwrite-utility-energy_sales.csv)
---

  - [rsmap.csv](/postprocessing/retail_rate_module/inputs/rsmap.csv)
    - **Description:** Mapping for BAs to resource regions
    - **Indices:** r,rs
---

  - [state-meanbiaserror_rate-aggregation.csv](/postprocessing/retail_rate_module/inputs/state-meanbiaserror_rate-aggregation.csv)
---

  - [Table_9.8_Average_Retail_Prices_of_Electricity.xlsx](/postprocessing/retail_rate_module/inputs/Table_9.8_Average_Retail_Prices_of_Electricity.xlsx)
    - **Description:** Historical EIA861 rates (annual and monthly)
---


#### [reValue](postprocessing/reValue) <a name='postprocessing/reValue'></a>
  - [scenarios.csv](/postprocessing/reValue/scenarios.csv)
---


#### [tableau](postprocessing/tableau) <a name='postprocessing/tableau'></a>
  - [tables_to_aggregate.csv](/postprocessing/tableau/tables_to_aggregate.csv)
---


### [preprocessing](preprocessing) <a name='preprocessing'></a>

#### [atb_updates_processing](preprocessing/atb_updates_processing) <a name='preprocessing/atb_updates_processing'></a>

##### [input_files](preprocessing/atb_updates_processing/input_files) <a name='preprocessing/atb_updates_processing/input_files'></a>
  - [batt_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/batt_plant_char_format.csv)
---

  - [conv_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/conv_plant_char_format.csv)
---

  - [csp_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/csp_plant_char_format.csv)
---

  - [geo_fom_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/geo_fom_plant_char_format.csv)
---

  - [h2-ct_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/h2-ct_plant_char_format.csv)
---

  - [ofs-wind_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/ofs-wind_plant_char_format.csv)
---

  - [ofs-wind_rsc_mult_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/ofs-wind_rsc_mult_plant_char_format.csv)
---

  - [ons-wind_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/ons-wind_plant_char_format.csv)
---

  - [upv_plant_char_format.csv](/preprocessing/atb_updates_processing/input_files/upv_plant_char_format.csv)
---


### [reeds2pras](reeds2pras) <a name='reeds2pras'></a>

#### [test](reeds2pras/test) <a name='reeds2pras/test'></a>

##### [reeds_cases](reeds2pras/test/reeds_cases) <a name='reeds2pras/test/reeds_cases'></a>

###### [USA_VSC_2035](reeds2pras/test/reeds_cases/USA_VSC_2035) <a name='reeds2pras/test/reeds_cases/USA_VSC_2035'></a>
  - [cases_USA_VSC_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/cases_USA_VSC_2035.csv)
---

  - [meta.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/meta.csv)
---


####### [inputs_case](reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case) <a name='reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case'></a>
  - [forcedoutage_hourly.h5](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/forcedoutage_hourly.h5)
---

  - [outage_forced_static.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/outage_forced_static.csv)
---

  - [resources.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/resources.csv)
---

  - [tech-subset-table.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/tech-subset-table.csv)
---

  - [unitdata.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/unitdata.csv)
---

  - [unitsize.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/inputs_case/unitsize.csv)
---


####### [ReEDS_Augur](reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur) <a name='reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur'></a>

####### [augur_data](reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data) <a name='reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data'></a>
  - [cap_converter_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/cap_converter_2035.csv)
---

  - [energy_cap_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/energy_cap_2035.csv)
---

  - [max_cap_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/max_cap_2035.csv)
---

  - [pras_load_2035.h5](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/pras_load_2035.h5)
---

  - [pras_vre_gen_2035.h5](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/pras_vre_gen_2035.h5)
---

  - [tran_cap_2035.csv](/reeds2pras/test/reeds_cases/USA_VSC_2035/ReEDS_Augur/augur_data/tran_cap_2035.csv)
---


### [ReEDS_Augur](ReEDS_Augur) <a name='ReEDS_Augur'></a>
  - [augur_switches.csv](/ReEDS_Augur/augur_switches.csv)
---


### [tests](tests) <a name='tests'></a>

#### [data](tests/data) <a name='tests/data'></a>

##### [county](tests/data/county) <a name='tests/data/county'></a>
  - [csp.h5](/tests/data/county/csp.h5)
---

  - [distpv.h5](/tests/data/county/distpv.h5)
---

  - [upv.h5](/tests/data/county/upv.h5)
---

  - [wind-ofs.h5](/tests/data/county/wind-ofs.h5)
---

  - [wind-ons.h5](/tests/data/county/wind-ons.h5)
---

