
# reValue
reValue has two main purposes:
1. Extract regional hourly prices from ReEDS scenarios and years
1. (Optional) Use extracted prices to calculate value and competitiveness-related metrics for a set of regional generation or load profiles.

# Instructions
1. Edit scenarios.csv. The columns are:
    - **name**: A unique name for this scenario
    - **activate**: Whether or not to activate this scenario for the reValue run. 1 means activate and 0 means de-activate
    - **tech**:  *wind-ons* and *load* are currently the only supported technologies, and only one technology is allowed for a given run of reValue (use *activate=0* for other technologies). *wind-ons* will use reV supply curves and profiles, while *load* uses BA-level load profiles
    - **year**: The year to extract from the ReEDS run
    - **color**: This column is currently unused, but could be useful for scenario styling in output visualizations
    - **reeds_run_path**: The path to the ReEDS run
    - **rev_sc_path**: The path to a reV supply curve. Use *none* if not using reV site-level profiles, e.g. if using *load*.
    - **profile_path**: The path to a file containing generation profiles, or *none* if gathering only prices . For onshore wind reV data, this will be the path to an h5 file, and for BA-level load data, this will be a path to a csv file.
    - **profile_timezone**: The timezone of the profile relative to UTC (e.g. *-6* for CST), or *local* to indicate that the profiles are in local time of the associated balancing areas.
    - **buildings_file**: A file containing number of buildings and sqft by BA, used for calculating additional metrics of GHP-based load adjustments. Otherwise use *none*
 1. (Optional) Configure switches at the top of reValue.py:
     - **output_prices**: Set to *False* if you don't care about the price outputs, otherwise *True*.
     - **res_marg_style**: *max_net_load_2012* is the only currently supported option, and assigns reserve margin prices equally to the peak net load hours. *max_load_price*, the other option, would assign reserve margin prices to the associated timeslice with max load prices, but this option only works on older versions of ReEDS.
     - **netload_num_hrs**: When **res_marg_style** = *max_net_load_2012*, this allows the user to specify the number of max net load hours to assign the reserve margin prices (default in ReEDS is 20, but the default here is 50 so that technologies don't randomly align with peak net load hours as often). Higher **netload_num_hrs** mean lower reserve margin prices in each hour, such that total value of firm capacity stays constant.
     - **netload_time_style**: When **res_marg_style** = *max_net_load_2012*, This allows the user to keep reserve margin prices at the hour level (**netload_time_style**=*hour*), or to assign prices to the entire timeslice(s) containing the hour(s) (**netload_time_style**=*timeslice*).
 3. Run activated scenarios with `python reValue.py` (from the reeds2 conda environment).
 4. Gather price and value metric outputs from output folder at *ReEDS-2.0/postprocessing/reValue/outputs_[timestamp]*. Here are the main outputs:
     - **reValue_out.csv**: This file contains the various value metrics:
         - *LVOE*: Value per unit energy
         - *LVOE_load*: Value per unit energy (load, or energy requirement, component. For *load* technology, this includes influence on operating reserves, state rps, and all model requirements that are linked to the LOAD variable)
         - *LVOE_rm*: Value per unit energy (reserve margin component)
         - *LVOE_or*: Value per unit energy (operating reserve component, only present if tech is not *load*)
         - *LVOE_rps*: Value per unit energy (state rps component, only present if the tech is not *load*)
         - *Pb_load_loc*: A benchmark price for the load component at this location (assuming flat block technology).
         - *Pb_rm_loc*: A benchmark price for the reserve margin component at this location (assuming flat block technology).
         - *Pb_load_nat*: A national benchmark price for the load component (assuming flat block technology).
         - *Pb_rm_nat*: A national benchmark price for the reserve margin component (assuming flat block technology).
         - *VF*: Value factor (LVOE/Pb).
         - *VF_temporal*: Temporal component of value factor
         - *VF_spatial*: Spatial component of value factor
         - *VF_interaction*: Spatio-temporal interaction, where *VF=VF_temporal\*VF_spatial\*VF_interaction*
     - **prices.csv**: This file contains prices for each ReEDS run and model year considered. The *type* column reflects total price by hour, *tot*, as well as the breakdown by service.

