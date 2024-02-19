# ReEDS 2.0

## Table of Contents


  - ### [](#) 
    - #### [hourlize](#hourlize) 
      - ##### [eer_to_reeds](#hourlize/eer_to_reeds) 
      - ##### [inputs](#hourlize/inputs) 
      - ##### [plexos_to_reeds](#hourlize/plexos_to_reeds) 
      - ##### [tests](#hourlize/tests) 
    - #### [inputs](#inputs) 
      - ##### [canada_imports](#inputs/canada_imports) 
      - ##### [capacitydata](#inputs/capacitydata) 
      - ##### [carbonconstraints](#inputs/carbonconstraints) 
      - ##### [climate](#inputs/climate) 
      - ##### [consume](#inputs/consume) 
      - ##### [csapr](#inputs/csapr) 
      - ##### [ctus](#inputs/ctus) 
      - ##### [degradation](#inputs/degradation) 
      - ##### [demand](#inputs/demand) 
      - ##### [demand_response](#inputs/demand_response) 
      - ##### [dGen_Model_Inputs](#inputs/dGen_Model_Inputs) 
      - ##### [disaggregation](#inputs/disaggregation) 
      - ##### [financials](#inputs/financials) 
      - ##### [fuelprices](#inputs/fuelprices) 
      - ##### [geothermal](#inputs/geothermal) 
      - ##### [growth_constraints](#inputs/growth_constraints) 
      - ##### [hydrodata](#inputs/hydrodata) 
      - ##### [loaddata](#inputs/loaddata) 
      - ##### [national_generation](#inputs/national_generation) 
      - ##### [plant_characteristics](#inputs/plant_characteristics) 
      - ##### [reserves](#inputs/reserves) 
      - ##### [RPSdata](#inputs/RPSdata) 
      - ##### [sets](#inputs/sets) 
      - ##### [shapefiles](#inputs/shapefiles) 
      - ##### [state_policies](#inputs/state_policies) 
      - ##### [storagedata](#inputs/storagedata) 
      - ##### [supplycurvedata](#inputs/supplycurvedata) 
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
      - ##### [land_use](#postprocessing/land_use) 
      - ##### [plots](#postprocessing/plots) 
      - ##### [retail_rate_module](#postprocessing/retail_rate_module) 
      - ##### [reValue](#postprocessing/reValue) 
      - ##### [tableau](#postprocessing/tableau) 
    - #### [preprocessing](#preprocessing) 
      - ##### [atb_updates_processing](#preprocessing/atb_updates_processing) 
    - #### [ReEDS_Augur](#ReEDS_Augur) 


## Input Files


## []() <a name=''></a>
  - [cases.csv](/cases.csv)
    - **File Type:** Switches file
    - **Description:** Contains the configuration settings for the ReEDS run(s).
    - **Dollar year:** 2004

    - **Citation:** [(https://github.nrel.gov/ReEDS/ReEDS-2.0/blob/38e6610a8c6a92291804598c95c11b707bf187b9/cases.csv)]

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
  - [county_map.csv](/hourlize/inputs/resource/county_map.csv)
    - **Description:** Contains a mapping between counties, states, and several other regions.
---

  - [state_abbrev.csv](/hourlize/inputs/resource/state_abbrev.csv)
    - **Description:** Contains state names and codesfor the US.
---

  - [upv_resource_classes.csv](/hourlize/inputs/resource/upv_resource_classes.csv)
    - **Description:** Contains information related to UPV class segregation based on mean irradiance levels.
---

  - [wind-ofs_resource_classes.csv](/hourlize/inputs/resource/wind-ofs_resource_classes.csv)
    - **Description:** Contains information related to Offshore wind class segregation based on mean wind speeds.
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

####### [expected_results](hourlize/tests/data/r2r_expanded/expected_results) <a name='hourlize/tests/data/r2r_expanded/expected_results'></a>
  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_expanded/expected_results/df_sc_out_wind-ons_reduced.csv)
---


####### [reeds](hourlize/tests/data/r2r_expanded/reeds) <a name='hourlize/tests/data/r2r_expanded/reeds'></a>

######## [inputs_case](hourlize/tests/data/r2r_expanded/reeds/inputs_case) <a name='hourlize/tests/data/r2r_expanded/reeds/inputs_case'></a>
  - [hierarchy.csv](/hourlize/tests/data/r2r_expanded/reeds/inputs_case/hierarchy.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_expanded/reeds/inputs_case/maxage.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_expanded/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_expanded/reeds/inputs_case/switches.csv)
---


######### [supplycurve_metadata](hourlize/tests/data/r2r_expanded/reeds/inputs_case/supplycurve_metadata) <a name='hourlize/tests/data/r2r_expanded/reeds/inputs_case/supplycurve_metadata'></a>
  - [rev_paths.csv](/hourlize/tests/data/r2r_expanded/reeds/inputs_case/supplycurve_metadata/rev_paths.csv)
---

  - [rev_supply_curves.csv](/hourlize/tests/data/r2r_expanded/reeds/inputs_case/supplycurve_metadata/rev_supply_curves.csv)
---


######## [outputs](hourlize/tests/data/r2r_expanded/reeds/outputs) <a name='hourlize/tests/data/r2r_expanded/reeds/outputs'></a>
  - [cap.csv](/hourlize/tests/data/r2r_expanded/reeds/outputs/cap.csv)
---

  - [cap_exog.csv](/hourlize/tests/data/r2r_expanded/reeds/outputs/cap_exog.csv)
---

  - [cap_new_bin_out.csv](/hourlize/tests/data/r2r_expanded/reeds/outputs/cap_new_bin_out.csv)
---

  - [cap_new_ivrt_refurb.csv](/hourlize/tests/data/r2r_expanded/reeds/outputs/cap_new_ivrt_refurb.csv)
---

  - [systemcost.csv](/hourlize/tests/data/r2r_expanded/reeds/outputs/systemcost.csv)
---


####### [supply_curves](hourlize/tests/data/r2r_expanded/supply_curves) <a name='hourlize/tests/data/r2r_expanded/supply_curves'></a>
  - [wind-ons_supply_curve_raw.csv](/hourlize/tests/data/r2r_expanded/supply_curves/wind-ons_supply_curve_raw.csv)
---


###### [r2r_from_config](hourlize/tests/data/r2r_from_config) <a name='hourlize/tests/data/r2r_from_config'></a>

####### [expected_results](hourlize/tests/data/r2r_from_config/expected_results) <a name='hourlize/tests/data/r2r_from_config/expected_results'></a>

######## [multiple_priority_inputs](hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs) <a name='hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs'></a>
  - [df_sc_out_dupv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_dupv_reduced.csv)
---

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/multiple_priority_inputs/df_sc_out_wind-ons_reduced.csv)
---


######## [no_bin_constraint](hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint) <a name='hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint'></a>
  - [df_sc_out_dupv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_dupv_reduced.csv)
---

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/no_bin_constraint/df_sc_out_wind-ons_reduced.csv)
---


######## [priority_inputs](hourlize/tests/data/r2r_from_config/expected_results/priority_inputs) <a name='hourlize/tests/data/r2r_from_config/expected_results/priority_inputs'></a>
  - [df_sc_out_dupv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_dupv_reduced.csv)
---

  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ofs_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_wind-ofs_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/priority_inputs/df_sc_out_wind-ons_reduced.csv)
---


######## [wind-ons_6mw_inputs](hourlize/tests/data/r2r_from_config/expected_results/wind-ons_6mw_inputs) <a name='hourlize/tests/data/r2r_from_config/expected_results/wind-ons_6mw_inputs'></a>
  - [df_sc_out_upv_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/wind-ons_6mw_inputs/df_sc_out_upv_reduced.csv)
---

  - [df_sc_out_wind-ons_reduced.csv](/hourlize/tests/data/r2r_from_config/expected_results/wind-ons_6mw_inputs/df_sc_out_wind-ons_reduced.csv)
---


###### [r2r_integration](hourlize/tests/data/r2r_integration) <a name='hourlize/tests/data/r2r_integration'></a>

####### [expected_results](hourlize/tests/data/r2r_integration/expected_results) <a name='hourlize/tests/data/r2r_integration/expected_results'></a>
  - [df_sc_out_dupv.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_dupv.csv)
---

  - [df_sc_out_dupv_reduced.csv](/hourlize/tests/data/r2r_integration/expected_results/df_sc_out_dupv_reduced.csv)
---

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

######## [inputs_case](hourlize/tests/data/r2r_integration/reeds/inputs_case) <a name='hourlize/tests/data/r2r_integration/reeds/inputs_case'></a>
  - [hierarchy.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/hierarchy.csv)
---

  - [maxage.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/maxage.csv)
---

  - [site_bin_map.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/site_bin_map.csv)
---

  - [switches.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/switches.csv)
---


######### [supplycurve_metadata](hourlize/tests/data/r2r_integration/reeds/inputs_case/supplycurve_metadata) <a name='hourlize/tests/data/r2r_integration/reeds/inputs_case/supplycurve_metadata'></a>
  - [rev_supply_curves.csv](/hourlize/tests/data/r2r_integration/reeds/inputs_case/supplycurve_metadata/rev_supply_curves.csv)
---


######## [outputs](hourlize/tests/data/r2r_integration/reeds/outputs) <a name='hourlize/tests/data/r2r_integration/reeds/outputs'></a>
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
  - [dupv_sc_naris_scaled.csv](/hourlize/tests/data/r2r_integration/supply_curves/dupv_sc_naris_scaled.csv)
---


######## [upv_reference](hourlize/tests/data/r2r_integration/supply_curves/upv_reference) <a name='hourlize/tests/data/r2r_integration/supply_curves/upv_reference'></a>

######### [results](hourlize/tests/data/r2r_integration/supply_curves/upv_reference/results) <a name='hourlize/tests/data/r2r_integration/supply_curves/upv_reference/results'></a>
  - [upv_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/upv_reference/results/upv_supply_curve_raw.csv)
---


######## [wind-ofs_0_open_moderate](hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate'></a>

######### [results](hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results'></a>
  - [wind-ofs_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/wind-ofs_0_open_moderate/results/wind-ofs_supply_curve_raw.csv)
---


######## [wind-ons_reference](hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference'></a>

######### [results](hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference/results) <a name='hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference/results'></a>
  - [wind-ons_supply_curve_raw.csv](/hourlize/tests/data/r2r_integration/supply_curves/wind-ons_reference/results/wind-ons_supply_curve_raw.csv)
---


### [inputs](inputs) <a name='inputs'></a>
  - [DebtFractionAdjustmentBounds.csv](/inputs/DebtFractionAdjustmentBounds.csv)
---

  - [deflator.csv](/inputs/deflator.csv)
    - **Description:** Dollar year deflator to convert values to 2004$
---

  - [hierarchy.csv](/inputs/hierarchy.csv)
---

  - [hierarchy_agg2.csv](/inputs/hierarchy_agg2.csv)
---

  - [modeledyears.csv](/inputs/modeledyears.csv)
---

  - [orperc.csv](/inputs/orperc.csv)
---

  - [r_cendiv.csv](/inputs/r_cendiv.csv)
    - **Description:** Mapping for BAs to census regions
---

  - [region_country_map.csv](/inputs/region_country_map.csv)
    - **Description:** Mapping for BAs to countries
---

  - [scalars.csv](/inputs/scalars.csv)
---

  - [tech-subset-table.csv](/inputs/tech-subset-table.csv)
    - **Description:** Maps all technologies to specific subsets of technologies
---


#### [canada_imports](inputs/canada_imports) <a name='inputs/canada_imports'></a>
  - [can_exports.csv](/inputs/canada_imports/can_exports.csv)
    - **Description:** Annual exports to Canada by BA
---

  - [can_exports_szn_frac.csv](/inputs/canada_imports/can_exports_szn_frac.csv)
---

  - [can_imports.csv](/inputs/canada_imports/can_imports.csv)
    - **Description:** Annual imports from Canada by BA
---

  - [can_imports_szn_frac.csv](/inputs/canada_imports/can_imports_szn_frac.csv)
---

  - [can_trade_8760.h5](/inputs/canada_imports/can_trade_8760.h5)
---


#### [capacitydata](inputs/capacitydata) <a name='inputs/capacitydata'></a>
  - [cappayments.csv](/inputs/capacitydata/cappayments.csv)
---

  - [cappayments_ba.csv](/inputs/capacitydata/cappayments_ba.csv)
---

  - [coal_fom_adj.csv](/inputs/capacitydata/coal_fom_adj.csv)
---

  - [demonstration_plants.csv](/inputs/capacitydata/demonstration_plants.csv)
    - **File Type:** Prescribed capacity
    - **Description:** Nuclear-smr demonstration plants; active when GSw_NuclearDemo=1
    - **Indices:** t,r,i,coolingwatertech,ctt,wst,value

    - **Citation:** [(See 'notes' column in the file)]

---

  - [firstyear.csv](/inputs/capacitydata/firstyear.csv)
    - **Description:** First year each technology is allowed to be built
---

  - [hydcf.csv](/inputs/capacitydata/hydcf.csv)
---

  - [maxage.csv](/inputs/capacitydata/maxage.csv)
    - **Description:** Maximum age allowed for each technology
---

  - [min_retire_age.csv](/inputs/capacitydata/min_retire_age.csv)
---

  - [nuke_fom_adj.csv](/inputs/capacitydata/nuke_fom_adj.csv)
---

  - [ReEDS_generator_database_final_EIA-NEMS.csv](/inputs/capacitydata/ReEDS_generator_database_final_EIA-NEMS.csv)
    - **Description:** EIA-NEMS database of existing generators
---

  - [rsmap.csv](/inputs/capacitydata/rsmap.csv)
    - **Description:** Mapping for BAs to resource regions
    - **Indices:** r,rs
---

  - [SeaCapAdj_hy.csv](/inputs/capacitydata/SeaCapAdj_hy.csv)
---

  - [upgrade_costs_ccs_coal.csv](/inputs/capacitydata/upgrade_costs_ccs_coal.csv)
---

  - [upgrade_costs_ccs_gas.csv](/inputs/capacitydata/upgrade_costs_ccs_gas.csv)
---

  - [upv_exog_cap_limited_ba.csv](/inputs/capacitydata/upv_exog_cap_limited_ba.csv)
    - **Description:** Exogenous (pre-2010) UPV capacity with limited siting assumptions at BA resolution
---

  - [upv_exog_cap_limited_county.csv](/inputs/capacitydata/upv_exog_cap_limited_county.csv)
    - **Description:** Exogenous (pre-2010) UPV capacity with limited siting assumptions at county resolution
---

  - [upv_exog_cap_open_ba.csv](/inputs/capacitydata/upv_exog_cap_open_ba.csv)
    - **Description:** Exogenous (pre-2010) UPV capacity with open siting assumptions at BA resolution
---

  - [upv_exog_cap_open_county.csv](/inputs/capacitydata/upv_exog_cap_open_county.csv)
    - **Description:** Exogenous (pre-2010) UPV capacity with open siting assumptions at county resolution
---

  - [upv_exog_cap_reference_ba.csv](/inputs/capacitydata/upv_exog_cap_reference_ba.csv)
    - **Description:** Exogenous (pre-2010) UPV capacity with reference siting assumptions at BA resolution
---

  - [upv_exog_cap_reference_county.csv](/inputs/capacitydata/upv_exog_cap_reference_county.csv)
    - **Description:** Exogenous (pre-2010) UPV capacity with reference siting assumptions at county resolution
---

  - [upv_prescribed_builds_limited_ba.csv](/inputs/capacitydata/upv_prescribed_builds_limited_ba.csv)
    - **Description:** UPV prescribed builds with limited siting assumptions at BA resolution
---

  - [upv_prescribed_builds_limited_county.csv](/inputs/capacitydata/upv_prescribed_builds_limited_county.csv)
    - **Description:** UPV prescribed builds with limited siting assumptions at county resolution
---

  - [upv_prescribed_builds_open_ba.csv](/inputs/capacitydata/upv_prescribed_builds_open_ba.csv)
    - **Description:** UPV prescribed builds with open siting assumptions at BA resolution
---

  - [upv_prescribed_builds_open_county.csv](/inputs/capacitydata/upv_prescribed_builds_open_county.csv)
    - **Description:** UPV prescribed builds with open siting assumptions at county resolution
---

  - [upv_prescribed_builds_reference_ba.csv](/inputs/capacitydata/upv_prescribed_builds_reference_ba.csv)
    - **Description:** UPV prescribed builds with reference siting assumptions at BA resolution
---

  - [upv_prescribed_builds_reference_county.csv](/inputs/capacitydata/upv_prescribed_builds_reference_county.csv)
    - **Description:** UPV prescribed builds with reference siting assumptions at county resolution
---

  - [wind-ofs_prescribed_builds_limited_ba.csv](/inputs/capacitydata/wind-ofs_prescribed_builds_limited_ba.csv)
    - **Description:** wind-ofs prescribed builds with limited siting assumptions at BA resolution
---

  - [wind-ofs_prescribed_builds_limited_county.csv](/inputs/capacitydata/wind-ofs_prescribed_builds_limited_county.csv)
    - **Description:** wind-ofs prescribed builds with limited siting assumptions at county resolution
---

  - [wind-ofs_prescribed_builds_open_ba.csv](/inputs/capacitydata/wind-ofs_prescribed_builds_open_ba.csv)
    - **Description:** wind-ofs prescribed builds with open siting assumptions at BA resolution
---

  - [wind-ofs_prescribed_builds_open_county.csv](/inputs/capacitydata/wind-ofs_prescribed_builds_open_county.csv)
    - **Description:** wind-ofs prescribed builds with open siting assumptions at county resolution
---

  - [wind-ons_exog_cap_limited_ba.csv](/inputs/capacitydata/wind-ons_exog_cap_limited_ba.csv)
    - **Description:** Exogenous (pre-2010) wind-ons capacity with limited siting assumptions at BA resolution
---

  - [wind-ons_exog_cap_limited_county.csv](/inputs/capacitydata/wind-ons_exog_cap_limited_county.csv)
    - **Description:** Exogenous (pre-2010) wind-ons capacity with limited siting assumptions at county resolution
---

  - [wind-ons_exog_cap_open_ba.csv](/inputs/capacitydata/wind-ons_exog_cap_open_ba.csv)
    - **Description:** Exogenous (pre-2010) wind-ons capacity with open siting assumptions at BA resolution
---

  - [wind-ons_exog_cap_open_county.csv](/inputs/capacitydata/wind-ons_exog_cap_open_county.csv)
    - **Description:** Exogenous (pre-2010) wind-ons capacity with open siting assumptions at county resolution
---

  - [wind-ons_exog_cap_reference_ba.csv](/inputs/capacitydata/wind-ons_exog_cap_reference_ba.csv)
    - **Description:** Exogenous (pre-2010) wind-ons capacity with reference siting assumptions at BA resolution
---

  - [wind-ons_exog_cap_reference_county.csv](/inputs/capacitydata/wind-ons_exog_cap_reference_county.csv)
    - **Description:** Exogenous (pre-2010) wind-ons capacity with reference siting assumptions at county resolution
---

  - [wind-ons_prescribed_builds_limited_ba.csv](/inputs/capacitydata/wind-ons_prescribed_builds_limited_ba.csv)
    - **Description:** wind-ons prescribed builds with limited siting assumptions at BA resolution
---

  - [wind-ons_prescribed_builds_limited_county.csv](/inputs/capacitydata/wind-ons_prescribed_builds_limited_county.csv)
    - **Description:** wind-ons prescribed builds with limited siting assumptions at county resolution
---

  - [wind-ons_prescribed_builds_open_ba.csv](/inputs/capacitydata/wind-ons_prescribed_builds_open_ba.csv)
    - **Description:** wind-ons prescribed builds with open siting assumptions at BA resolution
---

  - [wind-ons_prescribed_builds_open_county.csv](/inputs/capacitydata/wind-ons_prescribed_builds_open_county.csv)
    - **Description:** wind-ons prescribed builds with open siting assumptions at county resolution
---

  - [wind-ons_prescribed_builds_reference_ba.csv](/inputs/capacitydata/wind-ons_prescribed_builds_reference_ba.csv)
    - **Description:** wind-ons prescribed builds with reference siting assumptions at BA resolution
---

  - [wind-ons_prescribed_builds_reference_county.csv](/inputs/capacitydata/wind-ons_prescribed_builds_reference_county.csv)
    - **Description:** wind-ons prescribed builds with reference siting assumptions at county resolution
---


##### [distpv](inputs/capacitydata/distpv) <a name='inputs/capacitydata/distpv'></a>
  - [distPVcap_Tariff_Final.csv](/inputs/capacitydata/distpv/distPVcap_Tariff_Final.csv)
---

  - [distPVCF_Tariff_Final.csv](/inputs/capacitydata/distpv/distPVCF_Tariff_Final.csv)
---


#### [carbonconstraints](inputs/carbonconstraints) <a name='inputs/carbonconstraints'></a>
  - [capture_rates_CCS_80.csv](/inputs/carbonconstraints/capture_rates_CCS_80.csv)
---

  - [capture_rates_CCS_95.csv](/inputs/carbonconstraints/capture_rates_CCS_95.csv)
---

  - [capture_rates_CCS_99.csv](/inputs/carbonconstraints/capture_rates_CCS_99.csv)
---

  - [capture_rates_default.csv](/inputs/carbonconstraints/capture_rates_default.csv)
---

  - [ccs_link.csv](/inputs/carbonconstraints/ccs_link.csv)
---

  - [co2_cap.csv](/inputs/carbonconstraints/co2_cap.csv)
    - **Description:** Annual nationwide carbon cap
---

  - [co2_tax.csv](/inputs/carbonconstraints/co2_tax.csv)
    - **Description:** Annual co2 tax
---

  - [emit_scale.csv](/inputs/carbonconstraints/emit_scale.csv)
---

  - [emitrate.csv](/inputs/carbonconstraints/emitrate.csv)
    - **Description:** Emition rates for thermal generator for SO2, Nox, Hg, and CO2
    - **Indices:** i,e
---

  - [methane_leakage_rate.csv](/inputs/carbonconstraints/methane_leakage_rate.csv)
---

  - [ng_crf_penalty.csv](/inputs/carbonconstraints/ng_crf_penalty.csv)
    - **File Type:** Inputs
    - **Description:** Cost adjustment for NG techs in scenarios with national decarbonization targets
    - **Indices:** allt
    - **Dollar year:** N/A

    - **Citation:** [(https://github.nrel.gov/ReEDS/ReEDS-2.0/pull/1220)]

---

  - [rggi_states.csv](/inputs/carbonconstraints/rggi_states.csv)
---

  - [rggicon.csv](/inputs/carbonconstraints/rggicon.csv)
    - **Description:** CO2 caps for RGGI states in metric tons
---

  - [state_cap.csv](/inputs/carbonconstraints/state_cap.csv)
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
    - **Description:** DAC costs (capex, FOM, VOM) and conversion rate, over time, using High assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(Beyond VRE project with Exxon Mobile and NETL.)]

---

  - [dac_elec_BVRE_2021_low.csv](/inputs/consume/dac_elec_BVRE_2021_low.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex, FOM, VOM) and conversion rate, over time, using Low assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(Beyond VRE project with Exxon Mobile and NETL.)]

---

  - [dac_elec_BVRE_2021_mid.csv](/inputs/consume/dac_elec_BVRE_2021_mid.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex, FOM, VOM) and conversion rate, over time, using Mid assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(Beyond VRE project with Exxon Mobile and NETL.)]

---

  - [dac_gas_BVRE_2021_high.csv](/inputs/consume/dac_gas_BVRE_2021_high.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex, FOM, VOM) and conversion rate, over time, using High assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(Beyond VRE project with Exxon Mobile and NETL.)]

---

  - [dac_gas_BVRE_2021_low.csv](/inputs/consume/dac_gas_BVRE_2021_low.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex, FOM, VOM) and conversion rate, over time, using Low assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(Beyond VRE project with Exxon Mobile and NETL.)]

---

  - [dac_gas_BVRE_2021_mid.csv](/inputs/consume/dac_gas_BVRE_2021_mid.csv)
    - **File Type:** Inputs
    - **Description:** DAC costs (capex, FOM, VOM) and conversion rate, over time, using Mid assumptions.
    - **Indices:** i,t
    - **Dollar year:** As specified in inputs/consume/dollaryear

    - **Citation:** [(Beyond VRE project with Exxon Mobile and NETL.)]

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


#### [csapr](inputs/csapr) <a name='inputs/csapr'></a>
  - [csapr_group1_ex.csv](/inputs/csapr/csapr_group1_ex.csv)
---

  - [csapr_group2_ex.csv](/inputs/csapr/csapr_group2_ex.csv)
---

  - [csapr_ozone_season.csv](/inputs/csapr/csapr_ozone_season.csv)
---


#### [ctus](inputs/ctus) <a name='inputs/ctus'></a>
  - [co2_site_char.csv](/inputs/ctus/co2_site_char.csv)
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


#### [demand](inputs/demand) <a name='inputs/demand'></a>

##### [information](inputs/demand/information) <a name='inputs/demand/information'></a>
  - [Improvements log.xlsx](/inputs/demand/information/Improvements%20log.xlsx)
---


##### [processed data](inputs/demand/processed%20data) <a name='inputs/demand/processed data'></a>
  - [base-device-set.csv](/inputs/demand/processed%20data/base-device-set.csv)
---

  - [commercial-load.csv](/inputs/demand/processed%20data/commercial-load.csv)
---

  - [device-class-set.csv](/inputs/demand/processed%20data/device-class-set.csv)
---

  - [device-option-set.csv](/inputs/demand/processed%20data/device-option-set.csv)
---

  - [discount-rates.csv](/inputs/demand/processed%20data/discount-rates.csv)
---

  - [end-use-set.csv](/inputs/demand/processed%20data/end-use-set.csv)
---

  - [income-class-set.csv](/inputs/demand/processed%20data/income-class-set.csv)
---

  - [industrial-load.csv](/inputs/demand/processed%20data/industrial-load.csv)
---

  - [new-device-set.csv](/inputs/demand/processed%20data/new-device-set.csv)
---

  - [price-adders.csv](/inputs/demand/processed%20data/price-adders.csv)
---

  - [ref-consumption.csv](/inputs/demand/processed%20data/ref-consumption.csv)
---

  - [total-device-counts.csv](/inputs/demand/processed%20data/total-device-counts.csv)
---

  - [use-dvc-map.csv](/inputs/demand/processed%20data/use-dvc-map.csv)
---

  - [use-dvc-opt-map.csv](/inputs/demand/processed%20data/use-dvc-opt-map.csv)
---


##### [raw data](inputs/demand/raw%20data) <a name='inputs/demand/raw data'></a>
  - [AEO2017 browser data.xlsx](/inputs/demand/raw%20data/AEO2017%20browser%20data.xlsx)
---

  - [Area fractions.csv](/inputs/demand/raw%20data/Area%20fractions.csv)
---

  - [Commercial load shapes.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes.csv)
---

  - [Commercial sales.csv](/inputs/demand/raw%20data/Commercial%20sales.csv)
---

  - [County demographics.xlsx](/inputs/demand/raw%20data/County%20demographics.xlsx)
---

  - [EIA 2016 electricity prices.xlsx](/inputs/demand/raw%20data/EIA%202016%20electricity%20prices.xlsx)
---

  - [EIA 2016 electricity sales.xlsx](/inputs/demand/raw%20data/EIA%202016%20electricity%20sales.xlsx)
---

  - [EIA mapping sets.xlsx](/inputs/demand/raw%20data/EIA%20mapping%20sets.xlsx)
---

  - [EIA NEMS commercial.xlsx](/inputs/demand/raw%20data/EIA%20NEMS%20commercial.xlsx)
---

  - [EIA NEMS residential.xlsx](/inputs/demand/raw%20data/EIA%20NEMS%20residential.xlsx)
---

  - [files_in_NEMS_output_folder.xlsx](/inputs/demand/raw%20data/files_in_NEMS_output_folder.xlsx)
---

  - [Households.xlsx](/inputs/demand/raw%20data/Households.xlsx)
---

  - [Industrial load disaggregation.xlsx](/inputs/demand/raw%20data/Industrial%20load%20disaggregation.xlsx)
---

  - [Industrial load shapes.csv](/inputs/demand/raw%20data/Industrial%20load%20shapes.csv)
---

  - [Mapping sets.xlsx](/inputs/demand/raw%20data/Mapping%20sets.xlsx)
---

  - [NEMS industrial.xlsx](/inputs/demand/raw%20data/NEMS%20industrial.xlsx)
---

  - [NEMS price adders.xlsx](/inputs/demand/raw%20data/NEMS%20price%20adders.xlsx)
---

  - [NEMS residential - v2.xlsx](/inputs/demand/raw%20data/NEMS%20residential%20-%20v2.xlsx)
---

  - [NEMS-ReEDS Region Mapping.csv](/inputs/demand/raw%20data/NEMS-ReEDS%20Region%20Mapping.csv)
---

  - [nems_input_files.xlsx](/inputs/demand/raw%20data/nems_input_files.xlsx)
---

  - [Other technology options.xlsx](/inputs/demand/raw%20data/Other%20technology%20options.xlsx)
---

  - [Parameters.xlsx](/inputs/demand/raw%20data/Parameters.xlsx)
---

  - [Population.xlsx](/inputs/demand/raw%20data/Population.xlsx)
---

  - [Residential load shapes.csv](/inputs/demand/raw%20data/Residential%20load%20shapes.csv)
---


###### [Commercial load shapes](inputs/demand/raw%20data/Commercial%20load%20shapes) <a name='inputs/demand/raw%20data/Commercial load shapes'></a>
  - [2016-08-08 - Comm Load by End Use - AL.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20AL.csv)
---

  - [2016-08-08 - Comm Load by End Use - AR.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20AR.csv)
---

  - [2016-08-08 - Comm Load by End Use - AZ.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20AZ.csv)
---

  - [2016-08-08 - Comm Load by End Use - CA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20CA.csv)
---

  - [2016-08-08 - Comm Load by End Use - CO.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20CO.csv)
---

  - [2016-08-08 - Comm Load by End Use - CT.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20CT.csv)
---

  - [2016-08-08 - Comm Load by End Use - DC.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20DC.csv)
---

  - [2016-08-08 - Comm Load by End Use - DE.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20DE.csv)
---

  - [2016-08-08 - Comm Load by End Use - FL.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20FL.csv)
---

  - [2016-08-08 - Comm Load by End Use - GA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20GA.csv)
---

  - [2016-08-08 - Comm Load by End Use - HI.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20HI.csv)
---

  - [2016-08-08 - Comm Load by End Use - IA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20IA.csv)
---

  - [2016-08-08 - Comm Load by End Use - ID.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20ID.csv)
---

  - [2016-08-08 - Comm Load by End Use - IL.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20IL.csv)
---

  - [2016-08-08 - Comm Load by End Use - IN.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20IN.csv)
---

  - [2016-08-08 - Comm Load by End Use - KS.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20KS.csv)
---

  - [2016-08-08 - Comm Load by End Use - KY.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20KY.csv)
---

  - [2016-08-08 - Comm Load by End Use - LA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20LA.csv)
---

  - [2016-08-08 - Comm Load by End Use - MA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MA.csv)
---

  - [2016-08-08 - Comm Load by End Use - MD.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MD.csv)
---

  - [2016-08-08 - Comm Load by End Use - ME.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20ME.csv)
---

  - [2016-08-08 - Comm Load by End Use - MI.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MI.csv)
---

  - [2016-08-08 - Comm Load by End Use - MN.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MN.csv)
---

  - [2016-08-08 - Comm Load by End Use - MO.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MO.csv)
---

  - [2016-08-08 - Comm Load by End Use - MS.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MS.csv)
---

  - [2016-08-08 - Comm Load by End Use - MT.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20MT.csv)
---

  - [2016-08-08 - Comm Load by End Use - NC.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NC.csv)
---

  - [2016-08-08 - Comm Load by End Use - ND.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20ND.csv)
---

  - [2016-08-08 - Comm Load by End Use - NE.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NE.csv)
---

  - [2016-08-08 - Comm Load by End Use - NH.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NH.csv)
---

  - [2016-08-08 - Comm Load by End Use - NJ.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NJ.csv)
---

  - [2016-08-08 - Comm Load by End Use - NM.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NM.csv)
---

  - [2016-08-08 - Comm Load by End Use - NV.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NV.csv)
---

  - [2016-08-08 - Comm Load by End Use - NY.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20NY.csv)
---

  - [2016-08-08 - Comm Load by End Use - OH.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20OH.csv)
---

  - [2016-08-08 - Comm Load by End Use - OK.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20OK.csv)
---

  - [2016-08-08 - Comm Load by End Use - OR.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20OR.csv)
---

  - [2016-08-08 - Comm Load by End Use - PA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20PA.csv)
---

  - [2016-08-08 - Comm Load by End Use - RI.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20RI.csv)
---

  - [2016-08-08 - Comm Load by End Use - SC.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20SC.csv)
---

  - [2016-08-08 - Comm Load by End Use - SD.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20SD.csv)
---

  - [2016-08-08 - Comm Load by End Use - TN.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20TN.csv)
---

  - [2016-08-08 - Comm Load by End Use - TX.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20TX.csv)
---

  - [2016-08-08 - Comm Load by End Use - UT.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20UT.csv)
---

  - [2016-08-08 - Comm Load by End Use - VA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20VA.csv)
---

  - [2016-08-08 - Comm Load by End Use - VT.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20VT.csv)
---

  - [2016-08-08 - Comm Load by End Use - WA.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20WA.csv)
---

  - [2016-08-08 - Comm Load by End Use - WI.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20WI.csv)
---

  - [2016-08-08 - Comm Load by End Use - WV.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20WV.csv)
---

  - [2016-08-08 - Comm Load by End Use - WY.csv](/inputs/demand/raw%20data/Commercial%20load%20shapes/2016-08-08%20-%20Comm%20Load%20by%20End%20Use%20-%20WY.csv)
---


#### [demand_response](inputs/demand_response) <a name='inputs/demand_response'></a>
  - [dr_decrease_none.csv](/inputs/demand_response/dr_decrease_none.csv)
---

  - [dr_decrease_profile_Baseline.csv](/inputs/demand_response/dr_decrease_profile_Baseline.csv)
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


#### [dGen_Model_Inputs](inputs/dGen_Model_Inputs) <a name='inputs/dGen_Model_Inputs'></a>

##### [StScen2018_Mid_Case](inputs/dGen_Model_Inputs/StScen2018_Mid_Case) <a name='inputs/dGen_Model_Inputs/StScen2018_Mid_Case'></a>
  - [distPVcap_StScen2018_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2018_Mid_Case/distPVcap_StScen2018_Mid_Case.csv)
---

  - [distPVCF_hourly_StScen2018_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2018_Mid_Case/distPVCF_hourly_StScen2018_Mid_Case.csv)
---


##### [StScen2019_Carbon_cap](inputs/dGen_Model_Inputs/StScen2019_Carbon_cap) <a name='inputs/dGen_Model_Inputs/StScen2019_Carbon_cap'></a>
  - [distPVcap_StScen2019_Carbon_cap.csv](/inputs/dGen_Model_Inputs/StScen2019_Carbon_cap/distPVcap_StScen2019_Carbon_cap.csv)
---

  - [distPVCF_hourly_StScen2019_Carbon_cap.csv](/inputs/dGen_Model_Inputs/StScen2019_Carbon_cap/distPVCF_hourly_StScen2019_Carbon_cap.csv)
---


##### [StScen2019_High_NG_Price](inputs/dGen_Model_Inputs/StScen2019_High_NG_Price) <a name='inputs/dGen_Model_Inputs/StScen2019_High_NG_Price'></a>
  - [distPVcap_StScen2019_High_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2019_High_NG_Price/distPVcap_StScen2019_High_NG_Price.csv)
---

  - [distPVCF_hourly_StScen2019_High_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2019_High_NG_Price/distPVCF_hourly_StScen2019_High_NG_Price.csv)
---


##### [StScen2019_High_PV_Cost](inputs/dGen_Model_Inputs/StScen2019_High_PV_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_High_PV_Cost'></a>
  - [distPVcap_StScen2019_High_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_High_PV_Cost/distPVcap_StScen2019_High_PV_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_High_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_High_PV_Cost/distPVCF_hourly_StScen2019_High_PV_Cost.csv)
---


##### [StScen2019_High_RE_Cost](inputs/dGen_Model_Inputs/StScen2019_High_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_High_RE_Cost'></a>
  - [distPVcap_StScen2019_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_High_RE_Cost/distPVcap_StScen2019_High_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_High_RE_Cost/distPVCF_hourly_StScen2019_High_RE_Cost.csv)
---


##### [StScen2019_Low_Bat_Cost](inputs/dGen_Model_Inputs/StScen2019_Low_Bat_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_Low_Bat_Cost'></a>
  - [distPVcap_StScen2019_Low_Bat_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_Bat_Cost/distPVcap_StScen2019_Low_Bat_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_Low_Bat_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_Bat_Cost/distPVCF_hourly_StScen2019_Low_Bat_Cost.csv)
---


##### [StScen2019_Low_NG_Price](inputs/dGen_Model_Inputs/StScen2019_Low_NG_Price) <a name='inputs/dGen_Model_Inputs/StScen2019_Low_NG_Price'></a>
  - [distPVcap_StScen2019_Low_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_NG_Price/distPVcap_StScen2019_Low_NG_Price.csv)
---

  - [distPVCF_hourly_StScen2019_Low_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_NG_Price/distPVCF_hourly_StScen2019_Low_NG_Price.csv)
---


##### [StScen2019_Low_PV_Cost](inputs/dGen_Model_Inputs/StScen2019_Low_PV_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_Low_PV_Cost'></a>
  - [distPVcap_StScen2019_Low_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_PV_Cost/distPVcap_StScen2019_Low_PV_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_Low_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_PV_Cost/distPVCF_hourly_StScen2019_Low_PV_Cost.csv)
---


##### [StScen2019_Low_RE_Cost](inputs/dGen_Model_Inputs/StScen2019_Low_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2019_Low_RE_Cost'></a>
  - [distPVcap_StScen2019_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_RE_Cost/distPVcap_StScen2019_Low_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2019_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2019_Low_RE_Cost/distPVCF_hourly_StScen2019_Low_RE_Cost.csv)
---


##### [StScen2019_Mid_Case](inputs/dGen_Model_Inputs/StScen2019_Mid_Case) <a name='inputs/dGen_Model_Inputs/StScen2019_Mid_Case'></a>
  - [distPVcap_StScen2019_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2019_Mid_Case/distPVcap_StScen2019_Mid_Case.csv)
---

  - [distPVCF_hourly_StScen2019_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2019_Mid_Case/distPVCF_hourly_StScen2019_Mid_Case.csv)
---


##### [StScen2019_National_RPS_80](inputs/dGen_Model_Inputs/StScen2019_National_RPS_80) <a name='inputs/dGen_Model_Inputs/StScen2019_National_RPS_80'></a>
  - [distPVcap_StScen2019_National_RPS_80.csv](/inputs/dGen_Model_Inputs/StScen2019_National_RPS_80/distPVcap_StScen2019_National_RPS_80.csv)
---

  - [distPVCF_hourly_StScen2019_National_RPS_80.csv](/inputs/dGen_Model_Inputs/StScen2019_National_RPS_80/distPVCF_hourly_StScen2019_National_RPS_80.csv)
---


##### [StScen2019_PTC_ITC_extension](inputs/dGen_Model_Inputs/StScen2019_PTC_ITC_extension) <a name='inputs/dGen_Model_Inputs/StScen2019_PTC_ITC_extension'></a>
  - [distPVcap_StScen2019_PTC_ITC_extension.csv](/inputs/dGen_Model_Inputs/StScen2019_PTC_ITC_extension/distPVcap_StScen2019_PTC_ITC_extension.csv)
---

  - [distPVCF_hourly_StScen2019_PTC_ITC_extension.csv](/inputs/dGen_Model_Inputs/StScen2019_PTC_ITC_extension/distPVCF_hourly_StScen2019_PTC_ITC_extension.csv)
---


##### [StScen2020_Carbon_cap](inputs/dGen_Model_Inputs/StScen2020_Carbon_cap) <a name='inputs/dGen_Model_Inputs/StScen2020_Carbon_cap'></a>
  - [distPVcap_StScen2020_Carbon_cap.csv](/inputs/dGen_Model_Inputs/StScen2020_Carbon_cap/distPVcap_StScen2020_Carbon_cap.csv)
---

  - [distPVCF_hourly_StScen2020_Carbon_cap.csv](/inputs/dGen_Model_Inputs/StScen2020_Carbon_cap/distPVCF_hourly_StScen2020_Carbon_cap.csv)
---


##### [StScen2020_High_NG_Price](inputs/dGen_Model_Inputs/StScen2020_High_NG_Price) <a name='inputs/dGen_Model_Inputs/StScen2020_High_NG_Price'></a>
  - [distPVcap_StScen2020_High_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2020_High_NG_Price/distPVcap_StScen2020_High_NG_Price.csv)
---

  - [distPVCF_hourly_StScen2020_High_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2020_High_NG_Price/distPVCF_hourly_StScen2020_High_NG_Price.csv)
---


##### [StScen2020_High_PV_Cost](inputs/dGen_Model_Inputs/StScen2020_High_PV_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_High_PV_Cost'></a>
  - [distPVcap_StScen2020_High_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_High_PV_Cost/distPVcap_StScen2020_High_PV_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_High_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_High_PV_Cost/distPVCF_hourly_StScen2020_High_PV_Cost.csv)
---


##### [StScen2020_High_RE_Cost](inputs/dGen_Model_Inputs/StScen2020_High_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_High_RE_Cost'></a>
  - [distPVcap_StScen2020_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_High_RE_Cost/distPVcap_StScen2020_High_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_High_RE_Cost/distPVCF_hourly_StScen2020_High_RE_Cost.csv)
---


##### [StScen2020_Low_Bat_Cost](inputs/dGen_Model_Inputs/StScen2020_Low_Bat_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_Low_Bat_Cost'></a>
  - [distPVcap_StScen2020_Low_Bat_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_Bat_Cost/distPVcap_StScen2020_Low_Bat_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_Low_Bat_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_Bat_Cost/distPVCF_hourly_StScen2020_Low_Bat_Cost.csv)
---


##### [StScen2020_Low_NG_Price](inputs/dGen_Model_Inputs/StScen2020_Low_NG_Price) <a name='inputs/dGen_Model_Inputs/StScen2020_Low_NG_Price'></a>
  - [distPVcap_StScen2020_Low_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_NG_Price/distPVcap_StScen2020_Low_NG_Price.csv)
---

  - [distPVCF_hourly_StScen2020_Low_NG_Price.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_NG_Price/distPVCF_hourly_StScen2020_Low_NG_Price.csv)
---


##### [StScen2020_Low_PV_Cost](inputs/dGen_Model_Inputs/StScen2020_Low_PV_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_Low_PV_Cost'></a>
  - [distPVcap_StScen2020_Low_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_PV_Cost/distPVcap_StScen2020_Low_PV_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_Low_PV_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_PV_Cost/distPVCF_hourly_StScen2020_Low_PV_Cost.csv)
---


##### [StScen2020_Low_RE_Cost](inputs/dGen_Model_Inputs/StScen2020_Low_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2020_Low_RE_Cost'></a>
  - [distPVcap_StScen2020_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_RE_Cost/distPVcap_StScen2020_Low_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2020_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2020_Low_RE_Cost/distPVCF_hourly_StScen2020_Low_RE_Cost.csv)
---


##### [StScen2020_Mid_Case](inputs/dGen_Model_Inputs/StScen2020_Mid_Case) <a name='inputs/dGen_Model_Inputs/StScen2020_Mid_Case'></a>
  - [distPVcap_StScen2020_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2020_Mid_Case/distPVcap_StScen2020_Mid_Case.csv)
---

  - [distPVCF_hourly_StScen2020_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2020_Mid_Case/distPVCF_hourly_StScen2020_Mid_Case.csv)
---


##### [StScen2020_National_RPS_80](inputs/dGen_Model_Inputs/StScen2020_National_RPS_80) <a name='inputs/dGen_Model_Inputs/StScen2020_National_RPS_80'></a>
  - [distPVcap_StScen2020_National_RPS_80.csv](/inputs/dGen_Model_Inputs/StScen2020_National_RPS_80/distPVcap_StScen2020_National_RPS_80.csv)
---

  - [distPVCF_hourly_StScen2020_National_RPS_80.csv](/inputs/dGen_Model_Inputs/StScen2020_National_RPS_80/distPVCF_hourly_StScen2020_National_RPS_80.csv)
---


##### [StScen2020_PTC_ITC_extension](inputs/dGen_Model_Inputs/StScen2020_PTC_ITC_extension) <a name='inputs/dGen_Model_Inputs/StScen2020_PTC_ITC_extension'></a>
  - [distPVcap_StScen2020_PTC_ITC_extension.csv](/inputs/dGen_Model_Inputs/StScen2020_PTC_ITC_extension/distPVcap_StScen2020_PTC_ITC_extension.csv)
---

  - [distPVCF_hourly_StScen2020_PTC_ITC_extension.csv](/inputs/dGen_Model_Inputs/StScen2020_PTC_ITC_extension/distPVCF_hourly_StScen2020_PTC_ITC_extension.csv)
---


##### [StScen2022_High_RE_Cost](inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost'></a>
  - [distPVcap_StScen2022_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost/distPVcap_StScen2022_High_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2022_High_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost/distPVCF_hourly_StScen2022_High_RE_Cost.csv)
---


##### [StScen2022_High_RE_Cost_LMI](inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_LMI) <a name='inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_LMI'></a>
  - [distPVcap_StScen2022_High_RE_Cost_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_LMI/distPVcap_StScen2022_High_RE_Cost_LMI.csv)
---

  - [distPVCF_hourly_StScen2022_High_RE_Cost_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_LMI/distPVCF_hourly_StScen2022_High_RE_Cost_LMI.csv)
---


##### [StScen2022_High_RE_Cost_noIRA](inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_noIRA) <a name='inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_noIRA'></a>
  - [distPVcap_StScen2022_High_RE_Cost_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_noIRA/distPVcap_StScen2022_High_RE_Cost_noIRA.csv)
---

  - [distPVCF_hourly_StScen2022_High_RE_Cost_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_High_RE_Cost_noIRA/distPVCF_hourly_StScen2022_High_RE_Cost_noIRA.csv)
---


##### [StScen2022_Low_RE_Cost](inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost) <a name='inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost'></a>
  - [distPVcap_StScen2022_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost/distPVcap_StScen2022_Low_RE_Cost.csv)
---

  - [distPVCF_hourly_StScen2022_Low_RE_Cost.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost/distPVCF_hourly_StScen2022_Low_RE_Cost.csv)
---


##### [StScen2022_Low_RE_Cost_LMI](inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_LMI) <a name='inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_LMI'></a>
  - [distPVcap_StScen2022_Low_RE_Cost_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_LMI/distPVcap_StScen2022_Low_RE_Cost_LMI.csv)
---

  - [distPVCF_hourly_StScen2022_Low_RE_Cost_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_LMI/distPVCF_hourly_StScen2022_Low_RE_Cost_LMI.csv)
---


##### [StScen2022_Low_RE_Cost_noIRA](inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_noIRA) <a name='inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_noIRA'></a>
  - [distPVcap_StScen2022_Low_RE_Cost_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_noIRA/distPVcap_StScen2022_Low_RE_Cost_noIRA.csv)
---

  - [distPVCF_hourly_StScen2022_Low_RE_Cost_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_Low_RE_Cost_noIRA/distPVCF_hourly_StScen2022_Low_RE_Cost_noIRA.csv)
---


##### [StScen2022_Mid_Case](inputs/dGen_Model_Inputs/StScen2022_Mid_Case) <a name='inputs/dGen_Model_Inputs/StScen2022_Mid_Case'></a>
  - [distPVcap_StScen2022_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case/distPVcap_StScen2022_Mid_Case.csv)
---

  - [distPVCF_hourly_StScen2022_Mid_Case.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case/distPVCF_hourly_StScen2022_Mid_Case.csv)
---


##### [StScen2022_Mid_Case_LMI](inputs/dGen_Model_Inputs/StScen2022_Mid_Case_LMI) <a name='inputs/dGen_Model_Inputs/StScen2022_Mid_Case_LMI'></a>
  - [distPVcap_StScen2022_Mid_Case_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case_LMI/distPVcap_StScen2022_Mid_Case_LMI.csv)
---

  - [distPVCF_hourly_StScen2022_Mid_Case_LMI.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case_LMI/distPVCF_hourly_StScen2022_Mid_Case_LMI.csv)
---


##### [StScen2022_Mid_Case_noIRA](inputs/dGen_Model_Inputs/StScen2022_Mid_Case_noIRA) <a name='inputs/dGen_Model_Inputs/StScen2022_Mid_Case_noIRA'></a>
  - [distPVcap_StScen2022_Mid_Case_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case_noIRA/distPVcap_StScen2022_Mid_Case_noIRA.csv)
---

  - [distPVCF_hourly_StScen2022_Mid_Case_noIRA.csv](/inputs/dGen_Model_Inputs/StScen2022_Mid_Case_noIRA/distPVCF_hourly_StScen2022_Mid_Case_noIRA.csv)
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


#### [financials](inputs/financials) <a name='inputs/financials'></a>
  - [construction_schedules_default.csv](/inputs/financials/construction_schedules_default.csv)
---

  - [construction_times_default.csv](/inputs/financials/construction_times_default.csv)
---

  - [currency_incentives.csv](/inputs/financials/currency_incentives.csv)
---

  - [depreciation_schedules_default.csv](/inputs/financials/depreciation_schedules_default.csv)
---

  - [financials_hydrogen.csv](/inputs/financials/financials_hydrogen.csv)
---

  - [financials_sys_ATB2020.csv](/inputs/financials/financials_sys_ATB2020.csv)
---

  - [financials_sys_ATB2021.csv](/inputs/financials/financials_sys_ATB2021.csv)
---

  - [financials_sys_ATB2022.csv](/inputs/financials/financials_sys_ATB2022.csv)
---

  - [financials_sys_ATB2023.csv](/inputs/financials/financials_sys_ATB2023.csv)
---

  - [financials_tech_ATB2020.csv](/inputs/financials/financials_tech_ATB2020.csv)
---

  - [financials_tech_ATB2021.csv](/inputs/financials/financials_tech_ATB2021.csv)
---

  - [financials_tech_ATB2022.csv](/inputs/financials/financials_tech_ATB2022.csv)
---

  - [financials_tech_ATB2023.csv](/inputs/financials/financials_tech_ATB2023.csv)
---

  - [financials_tech_ATB2023_CRP20.csv](/inputs/financials/financials_tech_ATB2023_CRP20.csv)
---

  - [financials_transmission_30ITC_0pen_2022_2031.csv](/inputs/financials/financials_transmission_30ITC_0pen_2022_2031.csv)
---

  - [financials_transmission_default.csv](/inputs/financials/financials_transmission_default.csv)
---

  - [incentives_annual.csv](/inputs/financials/incentives_annual.csv)
---

  - [incentives_biennial.csv](/inputs/financials/incentives_biennial.csv)
---

  - [incentives_ext_ce_dir_solPTC_r02.csv](/inputs/financials/incentives_ext_ce_dir_solPTC_r02.csv)
---

  - [incentives_ira.csv](/inputs/financials/incentives_ira.csv)
---

  - [incentives_ira_45q_extension.csv](/inputs/financials/incentives_ira_45q_extension.csv)
---

  - [incentives_ira_hii.csv](/inputs/financials/incentives_ira_hii.csv)
---

  - [incentives_ira_lii.csv](/inputs/financials/incentives_ira_lii.csv)
---

  - [incentives_PTC_ITC_ext.csv](/inputs/financials/incentives_PTC_ITC_ext.csv)
---

  - [incentives_wind_PTC_PV_ITC_2050.csv](/inputs/financials/incentives_wind_PTC_PV_ITC_2050.csv)
---

  - [inflation_default.csv](/inputs/financials/inflation_default.csv)
---

  - [reg_cap_cost_mult_default.csv](/inputs/financials/reg_cap_cost_mult_default.csv)
---

  - [retire_penalty.csv](/inputs/financials/retire_penalty.csv)
---

  - [supply_chain_adjust.csv](/inputs/financials/supply_chain_adjust.csv)
---

  - [tc_phaseout_schedule_ira2022.csv](/inputs/financials/tc_phaseout_schedule_ira2022.csv)
---


#### [fuelprices](inputs/fuelprices) <a name='inputs/fuelprices'></a>
  - [alpha_AEO_2021_HOG.csv](/inputs/fuelprices/alpha_AEO_2021_HOG.csv)
    - **File Type:** Input
    - **Description:** High Oil and Gas scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004

    - **Citation:** [(AEO 2021)]

---

  - [alpha_AEO_2021_LOG.csv](/inputs/fuelprices/alpha_AEO_2021_LOG.csv)
    - **File Type:** Input
    - **Description:** Low Oil and Gas scenario census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004

    - **Citation:** [(AEO 2021)]

---

  - [alpha_AEO_2021_reference.csv](/inputs/fuelprices/alpha_AEO_2021_reference.csv)
    - **File Type:** Input
    - **Description:** reference census division alpha values, used in the calculation of natural gas demand curves
    - **Indices:** allt,cendiv
    - **Dollar year:** 2004

    - **Citation:** [(AEO 2021)]

---

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

  - [coal_AEO_2021_reference.csv](/inputs/fuelprices/coal_AEO_2021_reference.csv)
    - **Description:** reference case census division fuel price of coal
    - **Indices:** t,cendiv
    - **Dollar year:** 2021
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

  - [ng_AEO_2021_HOG.csv](/inputs/fuelprices/ng_AEO_2021_HOG.csv)
    - **Description:** High Oil and Gas scenario census division fuel price of natural gas
---

  - [ng_AEO_2021_LOG.csv](/inputs/fuelprices/ng_AEO_2021_LOG.csv)
    - **Description:** Low Oil and Gas scenario census division fuel price of natural gas
---

  - [ng_AEO_2021_reference.csv](/inputs/fuelprices/ng_AEO_2021_reference.csv)
    - **Description:** Reference scenario census division fuel price of natural gas
---

  - [ng_AEO_2022_HOG.csv](/inputs/fuelprices/ng_AEO_2022_HOG.csv)
    - **Description:** High Oil and Gas scenario census division fuel price of natural gas
---

  - [ng_AEO_2022_LOG.csv](/inputs/fuelprices/ng_AEO_2022_LOG.csv)
    - **Description:** Low Oil and Gas scenario census division fuel price of natural gas
---

  - [ng_AEO_2022_reference.csv](/inputs/fuelprices/ng_AEO_2022_reference.csv)
    - **Description:** Reference scenario census division fuel price of natural gas
---

  - [ng_AEO_2023_HOG.csv](/inputs/fuelprices/ng_AEO_2023_HOG.csv)
    - **Description:** High Oil and Gas scenario census division fuel price of natural gas
---

  - [ng_AEO_2023_LOG.csv](/inputs/fuelprices/ng_AEO_2023_LOG.csv)
    - **Description:** Low Oil and Gas scenario census division fuel price of natural gas
---

  - [ng_AEO_2023_reference.csv](/inputs/fuelprices/ng_AEO_2023_reference.csv)
    - **Description:** Reference scenario census division fuel price of natural gas
---

  - [ng_demand_AEO_2021_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2021_HOG.csv)
    - **Description:** High Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
---

  - [ng_demand_AEO_2021_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2021_LOG.csv)
    - **Description:** Low Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
---

  - [ng_demand_AEO_2021_reference.csv](/inputs/fuelprices/ng_demand_AEO_2021_reference.csv)
    - **Description:** Reference census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
---

  - [ng_demand_AEO_2022_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2022_HOG.csv)
    - **Description:** High Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
---

  - [ng_demand_AEO_2022_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2022_LOG.csv)
    - **Description:** Low Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
---

  - [ng_demand_AEO_2022_reference.csv](/inputs/fuelprices/ng_demand_AEO_2022_reference.csv)
    - **Description:** Reference census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
---

  - [ng_demand_AEO_2023_HOG.csv](/inputs/fuelprices/ng_demand_AEO_2023_HOG.csv)
    - **Description:** High Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
---

  - [ng_demand_AEO_2023_LOG.csv](/inputs/fuelprices/ng_demand_AEO_2023_LOG.csv)
    - **Description:** Low Oil and Gas census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
---

  - [ng_demand_AEO_2023_reference.csv](/inputs/fuelprices/ng_demand_AEO_2023_reference.csv)
    - **Description:** Reference census division natural gas demand for the electric sector, used in the calculation of natural gas demand curves
---

  - [ng_tot_demand_AEO_2021_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2021_HOG.csv)
    - **Description:** High Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
---

  - [ng_tot_demand_AEO_2021_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2021_LOG.csv)
    - **Description:** Low Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
---

  - [ng_tot_demand_AEO_2021_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2021_reference.csv)
    - **Description:** Reference census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
---

  - [ng_tot_demand_AEO_2022_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2022_HOG.csv)
    - **Description:** High Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
---

  - [ng_tot_demand_AEO_2022_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2022_LOG.csv)
    - **Description:** Low Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
---

  - [ng_tot_demand_AEO_2022_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2022_reference.csv)
    - **Description:** Reference census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
---

  - [ng_tot_demand_AEO_2023_HOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_HOG.csv)
    - **Description:** High Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
---

  - [ng_tot_demand_AEO_2023_LOG.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_LOG.csv)
    - **Description:** Low Oil and Gas census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
---

  - [ng_tot_demand_AEO_2023_reference.csv](/inputs/fuelprices/ng_tot_demand_AEO_2023_reference.csv)
    - **Description:** Reference census division natural gas demand across all sectors, used in the calculation of natural gas demand curves
---

  - [re-ct_40.csv](/inputs/fuelprices/re-ct_40.csv)
---

  - [uranium_AEO_2021_reference.csv](/inputs/fuelprices/uranium_AEO_2021_reference.csv)
---

  - [uranium_AEO_2022_reference.csv](/inputs/fuelprices/uranium_AEO_2022_reference.csv)
---

  - [uranium_AEO_2023_reference.csv](/inputs/fuelprices/uranium_AEO_2023_reference.csv)
---


#### [geothermal](inputs/geothermal) <a name='inputs/geothermal'></a>
  - [geo_discovery_BAU.csv](/inputs/geothermal/geo_discovery_BAU.csv)
---

  - [geo_discovery_factor.csv](/inputs/geothermal/geo_discovery_factor.csv)
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
---

  - [growth_penalty.csv](/inputs/growth_constraints/growth_penalty.csv)
---


#### [hydrodata](inputs/hydrodata) <a name='inputs/hydrodata'></a>
  - [hyd_fom.csv](/inputs/hydrodata/hyd_fom.csv)
    - **Description:** Regional FOM costs for hydro
---

  - [hydro_mingen.csv](/inputs/hydrodata/hydro_mingen.csv)
---


#### [loaddata](inputs/loaddata) <a name='inputs/loaddata'></a>
  - [Adoption_Trajectories_Commercial.csv](/inputs/loaddata/Adoption_Trajectories_Commercial.csv)
---

  - [Adoption_Trajectories_Residential.csv](/inputs/loaddata/Adoption_Trajectories_Residential.csv)
---

  - [Baseline_load_hourly.h5](/inputs/loaddata/Baseline_load_hourly.h5)
---

  - [cangrowth.csv](/inputs/loaddata/cangrowth.csv)
    - **Description:** Canada load growth multiplier
---

  - [Clean2035_load_hourly.h5](/inputs/loaddata/Clean2035_load_hourly.h5)
---

  - [Clean2035_LTS_load_hourly.h5](/inputs/loaddata/Clean2035_LTS_load_hourly.h5)
---

  - [Clean2035clip1pct_load_hourly.h5](/inputs/loaddata/Clean2035clip1pct_load_hourly.h5)
---

  - [Commercial_GHP_Delta.csv](/inputs/loaddata/Commercial_GHP_Delta.csv)
---

  - [demand_AEO_2021_high.csv](/inputs/loaddata/demand_AEO_2021_high.csv)
---

  - [demand_AEO_2021_low.csv](/inputs/loaddata/demand_AEO_2021_low.csv)
---

  - [demand_AEO_2021_reference.csv](/inputs/loaddata/demand_AEO_2021_reference.csv)
---

  - [demand_AEO_2022_high.csv](/inputs/loaddata/demand_AEO_2022_high.csv)
---

  - [demand_AEO_2022_low.csv](/inputs/loaddata/demand_AEO_2022_low.csv)
---

  - [demand_AEO_2022_reference.csv](/inputs/loaddata/demand_AEO_2022_reference.csv)
---

  - [demand_AEO_2023_high.csv](/inputs/loaddata/demand_AEO_2023_high.csv)
---

  - [demand_AEO_2023_low.csv](/inputs/loaddata/demand_AEO_2023_low.csv)
---

  - [demand_AEO_2023_reference.csv](/inputs/loaddata/demand_AEO_2023_reference.csv)
---

  - [demand_flat_2020_onward.csv](/inputs/loaddata/demand_flat_2020_onward.csv)
---

  - [EER_100by2050_load_hourly.h5](/inputs/loaddata/EER_100by2050_load_hourly.h5)
---

  - [EER_Baseline_AEO2022_load_hourly.h5](/inputs/loaddata/EER_Baseline_AEO2022_load_hourly.h5)
---

  - [EER_IRAlow_load_hourly.h5](/inputs/loaddata/EER_IRAlow_load_hourly.h5)
---

  - [EER_IRAmoderate_load_hourly.h5](/inputs/loaddata/EER_IRAmoderate_load_hourly.h5)
---

  - [EPHIGH_load_hourly.h5](/inputs/loaddata/EPHIGH_load_hourly.h5)
---

  - [EPMEDIUM_load_hourly.h5](/inputs/loaddata/EPMEDIUM_load_hourly.h5)
---

  - [EPMEDIUMStretch2040_load_hourly.h5](/inputs/loaddata/EPMEDIUMStretch2040_load_hourly.h5)
---

  - [EPMEDIUMStretch2046_load_hourly.h5](/inputs/loaddata/EPMEDIUMStretch2046_load_hourly.h5)
---

  - [EPREFERENCE_load_hourly.h5](/inputs/loaddata/EPREFERENCE_load_hourly.h5)
---

  - [historic_load_hourly.h5](/inputs/loaddata/historic_load_hourly.h5)
---

  - [mex_growth_rate.csv](/inputs/loaddata/mex_growth_rate.csv)
    - **Description:** Mexico load growth multiplier
---

  - [Residential_GHP_Delta.csv](/inputs/loaddata/Residential_GHP_Delta.csv)
---


#### [national_generation](inputs/national_generation) <a name='inputs/national_generation'></a>
  - [gen_mandate_tech_list.csv](/inputs/national_generation/gen_mandate_tech_list.csv)
---

  - [gen_mandate_trajectory.csv](/inputs/national_generation/gen_mandate_trajectory.csv)
---


#### [plant_characteristics](inputs/plant_characteristics) <a name='inputs/plant_characteristics'></a>
  - [battery_ATB_2020_advanced.csv](/inputs/plant_characteristics/battery_ATB_2020_advanced.csv)
---

  - [battery_ATB_2020_conservative.csv](/inputs/plant_characteristics/battery_ATB_2020_conservative.csv)
---

  - [battery_ATB_2020_moderate.csv](/inputs/plant_characteristics/battery_ATB_2020_moderate.csv)
---

  - [battery_ATB_2021_advanced.csv](/inputs/plant_characteristics/battery_ATB_2021_advanced.csv)
---

  - [battery_ATB_2021_conservative.csv](/inputs/plant_characteristics/battery_ATB_2021_conservative.csv)
---

  - [battery_ATB_2021_moderate.csv](/inputs/plant_characteristics/battery_ATB_2021_moderate.csv)
---

  - [battery_ATB_2022_advanced.csv](/inputs/plant_characteristics/battery_ATB_2022_advanced.csv)
---

  - [battery_ATB_2022_conservative.csv](/inputs/plant_characteristics/battery_ATB_2022_conservative.csv)
---

  - [battery_ATB_2022_moderate.csv](/inputs/plant_characteristics/battery_ATB_2022_moderate.csv)
---

  - [battery_ATB_2023_advanced.csv](/inputs/plant_characteristics/battery_ATB_2023_advanced.csv)
---

  - [battery_ATB_2023_conservative.csv](/inputs/plant_characteristics/battery_ATB_2023_conservative.csv)
---

  - [battery_ATB_2023_moderate.csv](/inputs/plant_characteristics/battery_ATB_2023_moderate.csv)
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

  - [conv_ATB_2020.csv](/inputs/plant_characteristics/conv_ATB_2020.csv)
    - **Description:** Convential generator costs from the 2020 ATB
---

  - [conv_ATB_2020_low_ccs_cost.csv](/inputs/plant_characteristics/conv_ATB_2020_low_ccs_cost.csv)
---

  - [conv_ATB_2020_low_nuclear_cost.csv](/inputs/plant_characteristics/conv_ATB_2020_low_nuclear_cost.csv)
---

  - [conv_ATB_2021.csv](/inputs/plant_characteristics/conv_ATB_2021.csv)
---

  - [conv_ATB_2021_CCS_95_max.csv](/inputs/plant_characteristics/conv_ATB_2021_CCS_95_max.csv)
---

  - [conv_ATB_2021_low_ccs_cost.csv](/inputs/plant_characteristics/conv_ATB_2021_low_ccs_cost.csv)
---

  - [conv_ATB_2021_low_nuclear_and_ccs_cost.csv](/inputs/plant_characteristics/conv_ATB_2021_low_nuclear_and_ccs_cost.csv)
---

  - [conv_ATB_2021_low_nuclear_cost.csv](/inputs/plant_characteristics/conv_ATB_2021_low_nuclear_cost.csv)
---

  - [conv_ATB_2021_low_smr.csv](/inputs/plant_characteristics/conv_ATB_2021_low_smr.csv)
---

  - [conv_ATB_2021_very_low_smr.csv](/inputs/plant_characteristics/conv_ATB_2021_very_low_smr.csv)
---

  - [conv_ATB_2022.csv](/inputs/plant_characteristics/conv_ATB_2022.csv)
---

  - [conv_ATB_2022_low_nuclear_and_ccs_cost.csv](/inputs/plant_characteristics/conv_ATB_2022_low_nuclear_and_ccs_cost.csv)
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

  - [cost_opres_default.csv](/inputs/plant_characteristics/cost_opres_default.csv)
---

  - [cost_opres_market.csv](/inputs/plant_characteristics/cost_opres_market.csv)
---

  - [csp_ATB_2020_advanced.csv](/inputs/plant_characteristics/csp_ATB_2020_advanced.csv)
---

  - [csp_ATB_2020_conservative.csv](/inputs/plant_characteristics/csp_ATB_2020_conservative.csv)
---

  - [csp_ATB_2020_moderate.csv](/inputs/plant_characteristics/csp_ATB_2020_moderate.csv)
---

  - [csp_ATB_2021_advanced.csv](/inputs/plant_characteristics/csp_ATB_2021_advanced.csv)
---

  - [csp_ATB_2021_conservative.csv](/inputs/plant_characteristics/csp_ATB_2021_conservative.csv)
---

  - [csp_ATB_2021_moderate.csv](/inputs/plant_characteristics/csp_ATB_2021_moderate.csv)
---

  - [csp_ATB_2022_advanced.csv](/inputs/plant_characteristics/csp_ATB_2022_advanced.csv)
---

  - [csp_ATB_2022_conservative.csv](/inputs/plant_characteristics/csp_ATB_2022_conservative.csv)
---

  - [csp_ATB_2022_moderate.csv](/inputs/plant_characteristics/csp_ATB_2022_moderate.csv)
---

  - [csp_ATB_2023_advanced.csv](/inputs/plant_characteristics/csp_ATB_2023_advanced.csv)
---

  - [csp_ATB_2023_conservative.csv](/inputs/plant_characteristics/csp_ATB_2023_conservative.csv)
---

  - [csp_ATB_2023_moderate.csv](/inputs/plant_characteristics/csp_ATB_2023_moderate.csv)
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

  - [h2-ct_ATB_2020.csv](/inputs/plant_characteristics/h2-ct_ATB_2020.csv)
---

  - [h2-ct_ATB_2021.csv](/inputs/plant_characteristics/h2-ct_ATB_2021.csv)
---

  - [h2-ct_ATB_2022.csv](/inputs/plant_characteristics/h2-ct_ATB_2022.csv)
---

  - [h2-ct_ATB_2023.csv](/inputs/plant_characteristics/h2-ct_ATB_2023.csv)
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

  - [hydro_lowPSH.csv](/inputs/plant_characteristics/hydro_lowPSH.csv)
---

  - [ice_fom.csv](/inputs/plant_characteristics/ice_fom.csv)
    - **Description:** Fixed O&M for ice storage
---

  - [minCF.csv](/inputs/plant_characteristics/minCF.csv)
    - **Description:** minimum annual capacity factor for each tech fleet - applied to i-rto
---

  - [mingen_fixed.csv](/inputs/plant_characteristics/mingen_fixed.csv)
---

  - [minloadfrac0.csv](/inputs/plant_characteristics/minloadfrac0.csv)
    - **Description:** characteristics/minloadfrac0 database of minloadbed generator cs
---

  - [ofs-wind_ATB_2020_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2020 advanced capacity factor, capital, fixed O&M and var O&M costs of ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2020_advanced_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_advanced_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2020 advanced ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2020_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2020 conservative capacity factor, capital, fixed O&M and var O&M costs of ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2020_conservative_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_conservative_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2020 conservative ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2020_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2020 moderate capacity factor, capital, fixed O&M and var O&M costs of ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2020_moderate_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2020_moderate_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2020 moderate ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2021_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2021 advanced capacity factor, capital, fixed O&M and var O&M costs of ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2021_advanced_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_advanced_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2021 advanced ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2021_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2021 conservative capacity factor, capital, fixed O&M and var O&M costs of ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2021_conservative_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_conservative_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2021 conservative ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2021_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2021 moderate capacity factor, capital, fixed O&M and var O&M costs of ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2021_moderate_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2021_moderate_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2021 moderate ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2022_advanced.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_advanced.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 advanced capital, fixed O&M and var O&M costs of ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2022_advanced_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_advanced_noFloating.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 advanced capital, fixed O&M and var O&M costs of non-floating type ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2022_advanced_noFloating_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_advanced_noFloating_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 advanced non-floating type ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2022_advanced_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_advanced_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 advanced ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2022_conservative.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_conservative.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 conservative capital, fixed O&M and var O&M costs of ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2022_conservative_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_conservative_noFloating.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 conservative capital, fixed O&M and var O&M costs of non-floating type ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2022_conservative_noFloating_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_conservative_noFloating_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 conservative non-floating type ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2022_conservative_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_conservative_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 conservative ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2022_moderate.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_moderate.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 moderate capital, fixed O&M and var O&M costs of ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2022_moderate_noFloating.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_moderate_noFloating.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 moderate capital, fixed O&M and var O&M costs of non-floating type ofs-wind by class and year
    - **Dollar year:** 2004
---

  - [ofs-wind_ATB_2022_moderate_noFloating_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_moderate_noFloating_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 moderate non-floating type ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
---

  - [ofs-wind_ATB_2022_moderate_rsc_mult.csv](/inputs/plant_characteristics/ofs-wind_ATB_2022_moderate_rsc_mult.csv)
    - **File Type:** Inputs file
    - **Description:** 2022 moderate ofs-wind rsc mult (SC cost reduction mult) by class and year
    - **Dollar year:** N/A
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

  - [ons-wind_ATB_2020_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2020_advanced.csv)
---

  - [ons-wind_ATB_2020_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2020_conservative.csv)
---

  - [ons-wind_ATB_2020_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2020_moderate.csv)
---

  - [ons-wind_ATB_2021_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2021_advanced.csv)
---

  - [ons-wind_ATB_2021_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2021_conservative.csv)
---

  - [ons-wind_ATB_2021_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2021_moderate.csv)
---

  - [ons-wind_ATB_2022_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2022_advanced.csv)
---

  - [ons-wind_ATB_2022_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2022_conservative.csv)
---

  - [ons-wind_ATB_2022_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2022_moderate.csv)
---

  - [ons-wind_ATB_2023_advanced.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_advanced.csv)
---

  - [ons-wind_ATB_2023_conservative.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_conservative.csv)
---

  - [ons-wind_ATB_2023_moderate.csv](/inputs/plant_characteristics/ons-wind_ATB_2023_moderate.csv)
---

  - [outage_forced.csv](/inputs/plant_characteristics/outage_forced.csv)
    - **Description:** Forced outage rates by technology
---

  - [outage_planned.csv](/inputs/plant_characteristics/outage_planned.csv)
    - **Description:** Planned outage rate by technology
---

  - [pvb_benchmark2020.csv](/inputs/plant_characteristics/pvb_benchmark2020.csv)
---

  - [ramprate.csv](/inputs/plant_characteristics/ramprate.csv)
    - **Description:** Generator ramp rates by technology
---

  - [startcost.csv](/inputs/plant_characteristics/startcost.csv)
---

  - [unitsize.csv](/inputs/plant_characteristics/unitsize.csv)
---

  - [upv_ATB_2020_advanced.csv](/inputs/plant_characteristics/upv_ATB_2020_advanced.csv)
---

  - [upv_ATB_2020_conservative.csv](/inputs/plant_characteristics/upv_ATB_2020_conservative.csv)
---

  - [upv_ATB_2020_moderate.csv](/inputs/plant_characteristics/upv_ATB_2020_moderate.csv)
---

  - [upv_ATB_2021_advanced.csv](/inputs/plant_characteristics/upv_ATB_2021_advanced.csv)
---

  - [upv_ATB_2021_conservative.csv](/inputs/plant_characteristics/upv_ATB_2021_conservative.csv)
---

  - [upv_ATB_2021_moderate.csv](/inputs/plant_characteristics/upv_ATB_2021_moderate.csv)
---

  - [upv_ATB_2022_advanced.csv](/inputs/plant_characteristics/upv_ATB_2022_advanced.csv)
---

  - [upv_ATB_2022_conservative.csv](/inputs/plant_characteristics/upv_ATB_2022_conservative.csv)
---

  - [upv_ATB_2022_moderate.csv](/inputs/plant_characteristics/upv_ATB_2022_moderate.csv)
---

  - [upv_ATB_2023_advanced.csv](/inputs/plant_characteristics/upv_ATB_2023_advanced.csv)
---

  - [upv_ATB_2023_conservative.csv](/inputs/plant_characteristics/upv_ATB_2023_conservative.csv)
---

  - [upv_ATB_2023_moderate.csv](/inputs/plant_characteristics/upv_ATB_2023_moderate.csv)
---


#### [reserves](inputs/reserves) <a name='inputs/reserves'></a>
  - [opres_periods.csv](/inputs/reserves/opres_periods.csv)
---

  - [prm_annual.csv](/inputs/reserves/prm_annual.csv)
    - **Description:** Annual planning reserve margin by NERC region
---

  - [ramptime.csv](/inputs/reserves/ramptime.csv)
---


#### [RPSdata](inputs/RPSdata) <a name='inputs/RPSdata'></a>
  - [national_rps_frac_allScen.csv](/inputs/RPSdata/national_rps_frac_allScen.csv)
---


#### [sets](inputs/sets) <a name='inputs/sets'></a>
  - [ctt.csv](/inputs/sets/ctt.csv)
    - **File Type:** GAMS set
    - **Description:** set of cooling technology types
---

  - [geotech.csv](/inputs/sets/geotech.csv)
    - **File Type:** GAMS set
    - **Description:** set of geothermal technology categories
---

  - [i.csv](/inputs/sets/i.csv)
    - **File Type:** GAMS set
    - **Description:** set of technologies
---

  - [i_subtech.csv](/inputs/sets/i_subtech.csv)
    - **File Type:** GAMS set
    - **Description:** set of categories for subtechs
---

  - [pcat.csv](/inputs/sets/pcat.csv)
    - **File Type:** GAMS set
    - **Description:** set of prescribed technology categories
---

  - [sdbin.csv](/inputs/sets/sdbin.csv)
    - **File Type:** GAMS set
    - **Description:** set of storage durage bins
---

  - [tg.csv](/inputs/sets/tg.csv)
    - **File Type:** GAMS set
    - **Description:** set of technology groups
---

  - [w.csv](/inputs/sets/w.csv)
    - **File Type:** GAMS set
    - **Description:** set of water withdrawal or consumption options for water techs
---

  - [wst.csv](/inputs/sets/wst.csv)
    - **File Type:** GAMS set
    - **Description:** set of water source types
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

---

  - [nuclear_ba_ban_list.csv](/inputs/state_policies/nuclear_ba_ban_list.csv)
    - **Description:** List of BAs where nuclear technology development is banned.
---

  - [nuclear_subsidies.csv](/inputs/state_policies/nuclear_subsidies.csv)
---

  - [offshore_req_30by30.csv](/inputs/state_policies/offshore_req_30by30.csv)
---

  - [offshore_req_default.csv](/inputs/state_policies/offshore_req_default.csv)
---

  - [oosfrac.csv](/inputs/state_policies/oosfrac.csv)
---

  - [recstyle.csv](/inputs/state_policies/recstyle.csv)
---

  - [rectable.csv](/inputs/state_policies/rectable.csv)
    - **Description:** Table defining which states are allowed to trade RECs
---

  - [rps_fraction.csv](/inputs/state_policies/rps_fraction.csv)
---

  - [storage_mandates.csv](/inputs/state_policies/storage_mandates.csv)
    - **Description:** Energy storage mandates by region
---

  - [techs_banned.csv](/inputs/state_policies/techs_banned.csv)
    - **Description:** Table that bans certain technologies by state
---

  - [techs_banned_ces.csv](/inputs/state_policies/techs_banned_ces.csv)
---

  - [techs_banned_imports_rps.csv](/inputs/state_policies/techs_banned_imports_rps.csv)
---

  - [techs_banned_rps.csv](/inputs/state_policies/techs_banned_rps.csv)
---

  - [unbundled_limit_ces.csv](/inputs/state_policies/unbundled_limit_ces.csv)
---

  - [unbundled_limit_rps.csv](/inputs/state_policies/unbundled_limit_rps.csv)
---


#### [storagedata](inputs/storagedata) <a name='inputs/storagedata'></a>
  - [PSH_supply_curves_durations.csv](/inputs/storagedata/PSH_supply_curves_durations.csv)
---

  - [storage_duration.csv](/inputs/storagedata/storage_duration.csv)
---

  - [storage_duration_pshdata.csv](/inputs/storagedata/storage_duration_pshdata.csv)
---

  - [storinmaxfrac.csv](/inputs/storagedata/storinmaxfrac.csv)
---


#### [supplycurvedata](inputs/supplycurvedata) <a name='inputs/supplycurvedata'></a>
  - [bio_supplycurve.csv](/inputs/supplycurvedata/bio_supplycurve.csv)
    - **Description:** Regional biomass supply and costs by resource class
---

  - [csp_supply_curve-reference_ba.csv](/inputs/supplycurvedata/csp_supply_curve-reference_ba.csv)
    - **Description:** CSP supply curve using reference siting assumptions at the BA resolution
---

  - [csp_supply_curve-reference_county.csv](/inputs/supplycurvedata/csp_supply_curve-reference_county.csv)
    - **Description:** CSP supply curve using reference siting assumptions at the county resolution
---

  - [dollaryear.csv](/inputs/supplycurvedata/dollaryear.csv)
---

  - [DUPV_supply_curves_capacity_2018.csv](/inputs/supplycurvedata/DUPV_supply_curves_capacity_2018.csv)
---

  - [DUPV_supply_curves_capacity_NARIS.csv](/inputs/supplycurvedata/DUPV_supply_curves_capacity_NARIS.csv)
---

  - [DUPV_supply_curves_cost_2018.csv](/inputs/supplycurvedata/DUPV_supply_curves_cost_2018.csv)
---

  - [DUPV_supply_curves_cost_NARIS.csv](/inputs/supplycurvedata/DUPV_supply_curves_cost_NARIS.csv)
---

  - [geo_supply_curve_site-reference.csv](/inputs/supplycurvedata/geo_supply_curve_site-reference.csv)
---

  - [hyd_add_upg_cap.csv](/inputs/supplycurvedata/hyd_add_upg_cap.csv)
---

  - [hydcap.csv](/inputs/supplycurvedata/hydcap.csv)
---

  - [hydcost.csv](/inputs/supplycurvedata/hydcost.csv)
---

  - [PSH_supply_curves_capacity_10hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_10hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_capacity_10hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_10hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_capacity_10hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_10hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_capacity_10hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_10hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_capacity_12hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_12hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_capacity_12hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_12hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_capacity_12hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_12hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_capacity_12hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_12hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_capacity_8hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_8hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_capacity_8hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_8hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_capacity_8hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_8hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_capacity_8hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_8hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_capacity_vision.csv](/inputs/supplycurvedata/PSH_supply_curves_capacity_vision.csv)
---

  - [PSH_supply_curves_cost_10hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_10hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_cost_10hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_10hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_cost_10hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_10hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_cost_10hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_10hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_cost_12hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_12hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_cost_12hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_12hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_cost_12hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_12hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_cost_12hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_12hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_cost_8hr_15bin_dec2021.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_8hr_15bin_dec2021.csv)
---

  - [PSH_supply_curves_cost_8hr_15bin_may2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_8hr_15bin_may2022.csv)
---

  - [PSH_supply_curves_cost_8hr_ref_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_8hr_ref_dec2022.csv)
---

  - [PSH_supply_curves_cost_8hr_wEphemeral_dec2022.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_8hr_wEphemeral_dec2022.csv)
---

  - [PSH_supply_curves_cost_vision.csv](/inputs/supplycurvedata/PSH_supply_curves_cost_vision.csv)
---

  - [rev_paths.csv](/inputs/supplycurvedata/rev_paths.csv)
---

  - [sitemap.csv](/inputs/supplycurvedata/sitemap.csv)
---

  - [sitemap_offshore.csv](/inputs/supplycurvedata/sitemap_offshore.csv)
---

  - [spurline_cost_1.csv](/inputs/supplycurvedata/spurline_cost_1.csv)
---

  - [trans_intra_cost_adder.csv](/inputs/supplycurvedata/trans_intra_cost_adder.csv)
---

  - [upv_supply_curve-limited_ba.csv](/inputs/supplycurvedata/upv_supply_curve-limited_ba.csv)
    - **Description:** UPV supply curve using limited siting assumptions at the BA resolution
---

  - [upv_supply_curve-limited_county.csv](/inputs/supplycurvedata/upv_supply_curve-limited_county.csv)
    - **Description:** UPV supply curve using limited siting assumptions at the county resolution
---

  - [upv_supply_curve-open_ba.csv](/inputs/supplycurvedata/upv_supply_curve-open_ba.csv)
    - **Description:** UPV supply curve using open siting assumptions at the BA resolution
---

  - [upv_supply_curve-open_county.csv](/inputs/supplycurvedata/upv_supply_curve-open_county.csv)
    - **Description:** UPV supply curve using open siting assumptions at the county resolution
---

  - [upv_supply_curve-reference_ba.csv](/inputs/supplycurvedata/upv_supply_curve-reference_ba.csv)
    - **Description:** UPV supply curve using reference siting assumptions at the BA resolution
---

  - [upv_supply_curve-reference_county.csv](/inputs/supplycurvedata/upv_supply_curve-reference_county.csv)
    - **Description:** UPV supply curve using reference siting assumptions at the county resolution
---

  - [wind-ofs_supply_curve-limited_ba.csv](/inputs/supplycurvedata/wind-ofs_supply_curve-limited_ba.csv)
    - **Description:** wind-ofs supply curve using limited siting assumptions at the BA resolution
---

  - [wind-ofs_supply_curve-limited_county.csv](/inputs/supplycurvedata/wind-ofs_supply_curve-limited_county.csv)
    - **Description:** wind-ofs supply curve using limited siting assumptions at the county resolution
---

  - [wind-ofs_supply_curve-open_ba.csv](/inputs/supplycurvedata/wind-ofs_supply_curve-open_ba.csv)
    - **Description:** wind-ofs supply curve using open siting assumptions at the BA resolution
---

  - [wind-ofs_supply_curve-open_county.csv](/inputs/supplycurvedata/wind-ofs_supply_curve-open_county.csv)
    - **Description:** wind-ofs supply curve using open siting assumptions at the county resolution
---

  - [wind-ons_supply_curve-limited_ba.csv](/inputs/supplycurvedata/wind-ons_supply_curve-limited_ba.csv)
    - **Description:** wind-ons supply curve using limited siting assumptions at the BA resolution
---

  - [wind-ons_supply_curve-limited_county.csv](/inputs/supplycurvedata/wind-ons_supply_curve-limited_county.csv)
    - **Description:** wind-ons supply curve using limited siting assumptions at the county resolution
---

  - [wind-ons_supply_curve-open_ba.csv](/inputs/supplycurvedata/wind-ons_supply_curve-open_ba.csv)
    - **Description:** wind-ons supply curve using open siting assumptions at the BA resolution
---

  - [wind-ons_supply_curve-open_county.csv](/inputs/supplycurvedata/wind-ons_supply_curve-open_county.csv)
    - **Description:** wind-ons supply curve using open siting assumptions at the county resolution
---

  - [wind-ons_supply_curve-reference_ba.csv](/inputs/supplycurvedata/wind-ons_supply_curve-reference_ba.csv)
    - **Description:** wind-ons supply curve using reference siting assumptions at the BA resolution
---

  - [wind-ons_supply_curve-reference_county.csv](/inputs/supplycurvedata/wind-ons_supply_curve-reference_county.csv)
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
    - **Description:** Initial AC transmission capacity from the NARIS 2024 system at the BA resolution
---

  - [transmission_capacity_init_AC_ba_REFS2009.csv](/inputs/transmission/transmission_capacity_init_AC_ba_REFS2009.csv)
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
  - [d_szn_1.csv](/inputs/variability/d_szn_1.csv)
---

  - [d_szn_7.csv](/inputs/variability/d_szn_7.csv)
---

  - [h_dt_szn.csv](/inputs/variability/h_dt_szn.csv)
---

  - [hourly_operational_characteristics.csv](/inputs/variability/hourly_operational_characteristics.csv)
---

  - [index_hr_map_1.csv](/inputs/variability/index_hr_map_1.csv)
---

  - [index_hr_map_7.csv](/inputs/variability/index_hr_map_7.csv)
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
---

  - [dupv_ba.h5](/inputs/variability/multi_year/dupv_ba.h5)
    - **File Type:** Resource supply curve
    - **Description:** Distributed utility scale photovoltaics resource supply curve. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]

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

  - [upv_140AC_ba-reference.h5](/inputs/variability/multi_year/upv_140AC_ba-reference.h5)
    - **File Type:** Resource supply curve
    - **Description:** Utility scale photovoltaics resource supply curve (AC, using a 1.40 Inverter Load Ratio) using Reference access assumptions. Data is a capacity factor i.e. a fraction.
    - **Indices:** v,r,t
    - **Dollar year:** N/A

    - **Citation:** [(N/A)]

---

  - [upv_220AC_ba-reference.h5](/inputs/variability/multi_year/upv_220AC_ba-reference.h5)
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

#### [air_quality](postprocessing/air_quality) <a name='postprocessing/air_quality'></a>
  - [scenarios.csv](/postprocessing/air_quality/scenarios.csv)
---


##### [rcm_data](postprocessing/air_quality/rcm_data) <a name='postprocessing/air_quality/rcm_data'></a>
  - [counties_ACS_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/counties_ACS_high_stack_2017.csv)
---

  - [counties_H6C_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/counties_H6C_high_stack_2017.csv)
---

  - [marginal_damages_by_ReEDS_BA.csv](/postprocessing/air_quality/rcm_data/marginal_damages_by_ReEDS_BA.csv)
---

  - [states_ACS_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/states_ACS_high_stack_2017.csv)
---

  - [states_H6C_high_stack_2017.csv](/postprocessing/air_quality/rcm_data/states_H6C_high_stack_2017.csv)
---


#### [bokehpivot](postprocessing/bokehpivot) <a name='postprocessing/bokehpivot'></a>

##### [in](postprocessing/bokehpivot/in) <a name='postprocessing/bokehpivot/in'></a>
  - [example_custom_styles.csv](/postprocessing/bokehpivot/in/example_custom_styles.csv)
---

  - [example_data_US_electric_power_generation.csv](/postprocessing/bokehpivot/in/example_data_US_electric_power_generation.csv)
---

  - [example_reeds_scenarios.csv](/postprocessing/bokehpivot/in/example_reeds_scenarios.csv)
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
---


###### [reeds2](postprocessing/bokehpivot/in/reeds2) <a name='postprocessing/bokehpivot/in/reeds2'></a>
  - [class_map.csv](/postprocessing/bokehpivot/in/reeds2/class_map.csv)
---

  - [class_style.csv](/postprocessing/bokehpivot/in/reeds2/class_style.csv)
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
---

  - [trtype_map.csv](/postprocessing/bokehpivot/in/reeds2/trtype_map.csv)
---

  - [trtype_style.csv](/postprocessing/bokehpivot/in/reeds2/trtype_style.csv)
---

  - [wst_map.csv](/postprocessing/bokehpivot/in/reeds2/wst_map.csv)
---

  - [wst_style.csv](/postprocessing/bokehpivot/in/reeds2/wst_style.csv)
---


#### [land_use](postprocessing/land_use) <a name='postprocessing/land_use'></a>

##### [inputs](postprocessing/land_use/inputs) <a name='postprocessing/land_use/inputs'></a>
  - [federal_land_lookup.csv](/postprocessing/land_use/inputs/federal_land_lookup.csv)
---

  - [field_definitions.csv](/postprocessing/land_use/inputs/field_definitions.csv)
---

  - [nlcd_classifications.csv](/postprocessing/land_use/inputs/nlcd_classifications.csv)
---


#### [plots](postprocessing/plots) <a name='postprocessing/plots'></a>
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
---

  - [map_i_to_tech.csv](/postprocessing/retail_rate_module/map_i_to_tech.csv)
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


### [ReEDS_Augur](ReEDS_Augur) <a name='ReEDS_Augur'></a>
  - [augur_switches.csv](/ReEDS_Augur/augur_switches.csv)
---

