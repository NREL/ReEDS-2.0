import datetime

#SHARED CONFIG
timeslice_path = 'inputs/timeslices_hourend.csv' #The index will be the hour number of the year, ie the first entry is Jan 1, 12am. Timeslices assume this is end-of-hour, e.g. H9 ends at 6am, so this is its last entry per day.
agg_outputs_timezone = 'local' #This is for the aggregated (non-hourly) outputs. 'local' means convert to local standard time of the respective region. UTC is 0. EST is -5.
hourly_outputs_timezone = 'local' #'local' means convert to local time of the respective region. UTC is 0. EST is -5.
start_1am = True #False means start at 12am
select_year = 2012 #This is the year used for load and resource profile-derived inputs, although the profile outputs may still be multiyear (see multiyear)
hourly_out_years = list(range(2007,2014)) #e.g. [2012] for just 2012 or list(range(2007,2014)) for 2007-2013

#RESOURCE CONFIG
#Test Mode:
test_mode = False #This limits the regions considered to those listed below.
test_filters = {'region':['s270']}

#Main inputs: Enter the tech, supply curve path, and profile path.
tech = 'wind-ons' #'wind-ons', 'wind-ofs', 'upv', 'dupv'
rev_prefix = '05_b_b_mid'
rev_case_path = r'//nrelqnap02/ReEDS/Supply_Curve_Data/ONSHORE/2020_Update/reV wind outputs 2020-05-30/' + rev_prefix #This path should have a supply curve file called [rev_prefix]_sc.csv and files for each year with hourly generation data for each supply curve point or gen_gid, called [rev_prefix]_rep_profiles_[select_year].h5.

#More consistent config: This may not need to change for different runs
out_dir = tech + '_' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + '/'
resource_source_timezone = 0 #UTC would be 0, Eastern standard time would be -5
class_path = 'inputs/resource/' + tech + '_resource_classes.csv'
reg_col = 'cnty_fips' #region from supply curve file (sc_path). 'cnty_fips' for county, could be 'model_region' if it is already in the supply curve. TODO: Add cnty_fips to pv supply curves so we map to regions with "p" in front.
reg_map_path = 'inputs/resource/county_map.csv' #This file maps counties to reeds regions and bas.
min_cap_path = 'inputs/resource/min_cap.csv' #None or path to file with minimum capacity cutoffs in MW by region. Region column must be in reg_map_path.
bin_group_cols = ['region','class']
bin_col = 'trans_cap_cost' #TODO: For onshore wind this is trans_cap_cost, but for offshore I NEED THE COLUMN NAME.
bin_num = 5
bin_method = 'equal_cap_cut' #'kmeans', 'equal_cap_man', 'equal_cap_cut'
rep_profile_method = 'rmse' #'rmse','ave'
cfmean_type = 'rep' #'rep', 'ave'
offshore_grid_cost_join = 'inputs/resource/offshore-grid-con-cost.csv'
add_h17 = True #Add h17 timeslice as equal to h3
driver = 'H5FD_CORE' #'H5FD_CORE', None. H5FD_CORE will load the h5 into memory for better perforamnce, but None must be used for low-memory machines.
gather_method = 'smart' # 'list', 'slice', 'smart'. This setting will take a slice of profile ids from the min to max, rather than using a list of ids, for improved performance when ids are close together for each group.
if tech in ['wind-ons','wind-ofs']:
    profile_dset = 'rep_profiles_0'
    profile_id_col = 'index' #'index' means use the index of the supply curve file, not a column name. 'sc_gid' was used previously for wind
    profile_weight_col = 'capacity'
    reg_out_col = 'reeds_region' #A column from reg_map_path that is desired for 'region' column, mapping from reg_col. If different than reg_col, make sure reg_col is unique in reg_map_path. Make the same as reg_col to use it directly.
elif tech in ['upv','dupv']:
    profile_dset = 'cf_profile'
    profile_id_col = 'gen_gids'
    profile_weight_col = 'gid_counts'
    reg_out_col = 'reeds_ba'
if tech == 'wind-ons':
    filter_cols = {'offshore':[0]} #This means filter the supply curve to rows for which offshore is 0.
elif tech == 'wind-ofs':
    filter_cols = {'offshore':[1]}
else:
    filter_cols = {} #this means use the full dataframe


#LOAD CONFIG
#Note that calcs assume UTC, although the current load source is in eastern time (delete this after updating)
load_source = 'plexos_to_reeds/outputs/load_hourly_ba_EST.csv' #e.g. '//nrelqnap02/ReEDS/PLEXOS_ReEDS_Load/combined/load_full.csv' This is a file (csv or compressed csv) with datetime as index and ba columns
load_source_timezone = -5 #UTC would be 0, Eastern standard time would be -5
calibrate_path = 'inputs/load/EIA_2010loadbystate.csv' #Enter string to calibrate path or False to leave uncalibrated
calibrate_year = 2010 #This is the year that the outputs of load.py represent, based on the EIA calibration year
ba_frac_path = 'inputs/load/load_participation_factors_st_to_ba.csv' #These are fractions of state load in each ba, unused if calibrate_path is False
hierarchy_path = 'inputs/load/hierarchy.csv' #Used for both calibration and variability outputs
season_path = 'inputs/load/seasons.csv' #These are fractions of state load in each ba, unused if calibrate_path is False
ba_timezone_path = 'inputs/load/ba_timezone.csv' #Should this be used for resource too, rather than site timezone?
hourly_process = True #If False, skip all hourly processing steps
truncate_leaps = True #Truncate leap years
us_only = True #Only run US BAs.
