"""
Functions for processing reV wind and solar resource supply curve and profile data for use in ReEDS.
Typically called from "run_hourlize.py" -- see README for setup and details.
"""

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================
import argparse
import datetime
import h5py
import json
import logging
import math
import numpy as np
import os
import pandas as pd
import pytz
import shutil
import site
import sklearn.cluster as sc
import sys
from collections import OrderedDict
from types import SimpleNamespace 
from glob import glob

import shapely
import geopandas as gpd

## ReEDS modules imported using reeds_path in main procedure

#%% ===========================================================================
### --- HELPER FUNCTIONS ---
### ===========================================================================

def get_latlonlabels(dfin, columns=None):
    """function to identify column names with latitude and longitude info in supply curve file

    Parameters
    ----------
    dfin
        data to look for lat/lon columns
    columns, optional
        list of column names to check, by default None

    Returns
    -------
        tuple with name of columns containing latitude and longitude
    """
    if columns is None:
        columns = dfin.columns
        
    if ('latitude' in columns) and ('longitude' in columns):
        latlabel, lonlabel = 'latitude', 'longitude'
    elif ('Latitude' in columns) and ('Longitude' in columns):
        latlabel, lonlabel = 'Latitude', 'Longitude'
    elif ('LATITUDE' in columns) and ('LONGITUDE' in columns):
        latlabel, lonlabel = 'LATITUDE', 'LONGITUDE'
    elif ('lat' in columns) and ('lon' in columns):
        latlabel, lonlabel = 'lat', 'lon'
    elif ('lat' in columns) and ('lng' in columns):
        latlabel, lonlabel = 'lat', 'lng'
    elif ('Lat' in columns) and ('Lon' in columns):
        latlabel, lonlabel = 'Lat', 'Lon'
    elif ('lat' in columns) and ('long' in columns):
        latlabel, lonlabel = 'lat', 'long'
    elif ('Lat' in columns) and ('Long' in columns):
        latlabel, lonlabel = 'Lat', 'Long'
    elif ('latitude_poi' in columns) and ('longitude_poi' in columns):
        latlabel, lonlabel = 'latitude_poi', 'longitude_poi'
    
    return latlabel, lonlabel

def df2gdf(dfin, crs='ESRI:102008'):
    """function to convert a dataframe from pandas to geopandas 

    Parameters
    ----------
    dfin
        pandas dataframe with lat/lon information 
    crs, optional
        coordinate reference system to use, by default 'ESRI:102008'

    Returns
    -------
        geopandas dataframe
    """

    os.environ['PROJ_NETWORK'] = 'OFF'
    df = dfin.copy()
    latlabel, lonlabel = get_latlonlabels(df)
    df['geometry'] = df.apply(
        lambda row: shapely.geometry.Point(row[lonlabel], row[latlabel]), axis=1)
    df = gpd.GeoDataFrame(df, crs='EPSG:4326').to_crs(crs)

    return df

def copy_rev_jsons(outpath, rev_path):
    """helper function to copy reV json config files into repo as metadata

    Parameters
    ----------
    outpath
        path to direcotry for this hourlize run 
    rev_path
        path to reV folder with jsons 
    """
    os.makedirs(os.path.join(outpath, 'inputs', 'rev_configs'), exist_ok=True)
    rev_jsons = glob(os.path.join(rev_path, "*.json*"))
    for jsonfile in rev_jsons:
        try:
            shutil.copy2(
                jsonfile,
                os.path.join(outpath, 'inputs', 'rev_configs', os.path.basename(jsonfile)),
            )
        except FileNotFoundError as err:
            print(f"WARNING: {err}")
    print('Done copying rev json files')
    rev_jsons_out = [os.path.basename(jsonfile) for jsonfile in rev_jsons]
    return rev_jsons_out

#%% ===========================================================================
### --- SUPPLY CURVE PROCESSING ---
### ===========================================================================

def match_to_counties(sc, profile_id_col, reeds_path, outpath, tech):
    """adds county FIPS code to reV supply curve

    Parameters
    ----------
    sc
        pandas dataframe of supply curve 
    reeds_path
        path to ReEDS directory

    Returns
    -------
        pandas dataframe with updated supply curve with columns that have county FIPS code and county name
    """

    print("Adding county FIPS code")

    # load county shapefile
    cnty_shp = os.path.join(reeds_path, "inputs", "shapefiles", "US_COUNTY_2022")
    # for lat/lon matching it is better to have a geographic CRS as opposed to a projection
    crs_out = "EPSG:4326"
    cnty_shp = gpd.read_file(cnty_shp).to_crs(crs_out)
    
    # convert sc to geopandas (helpful to reduce dimensions)
    # use POI lat/lon for offshore wind, and site lat/lon for UPV and LBW
    if tech == 'wind-ofs':
        sc_sub = sc[[profile_id_col, 'state', 'latitude_poi', 'longitude_poi']].copy()
    else:
        sc_sub = sc[[profile_id_col, 'state', 'latitude', 'longitude']].copy()
    sc_sub = df2gdf(sc_sub, crs=cnty_shp.crs)
    
    # Offshore Wind State-Specific Nearest Matching
    if tech == 'wind-ofs':
        matched_data = []

        for state in sc_sub['state'].unique():
            # Filter counties and sites by state
            state_counties = cnty_shp[cnty_shp['STATE'] == state]
            state_sites = sc_sub[sc_sub['state'] == state]

            # Perform nearest join within the state
            state_matched = gpd.sjoin_nearest(
                state_sites.to_crs('ESRI:102008'),
                state_counties.to_crs('ESRI:102008'),
                how="left"
            ).drop("index_right", axis=1).to_crs(crs_out)

            matched_data.append(state_matched)

        # Concatenate state-matched data
        sc_matched_final = pd.concat(matched_data, ignore_index=True)
        # Prepare final output DataFrame
        sc_out = sc_matched_final[[profile_id_col, 'state', 'FIPS', 'NAME']].rename(
        columns={"FIPS": "cnty_fips", "NAME": "county"}
        )  

    else:
        # Onshore Wind and UPV: Original Spatial Matching with Unmatched Handling
        # spatial join to match with counties (matches if lat/lon are within polygon)
        sc_matched = gpd.sjoin(sc_sub, cnty_shp, how="left").drop("index_right", axis=1)

        # the above match gets most sc points but some are unmatched, likey because they are on
        # a polygon border. for those we perform a second join to the nearest area
        # only uses this second method for unmatched points since it is signifcally slower than sjoin
        sc_unmatched = sc_matched.loc[sc_matched.rb.isna(), sc_sub.columns]
        # for this matching we need distances, so use the ESRI projection
        sc_unmatched = gpd.sjoin_nearest(
            sc_unmatched.to_crs('ESRI:102008'), cnty_shp.to_crs('ESRI:102008'), how="left"
            ).drop("index_right", axis=1).to_crs(sc_matched.crs)

        # drop any duplicated points (this can happen is a rev supply curve point is equidistant from two zones)
        sc_unmatched = sc_unmatched.drop_duplicates(subset=profile_id_col, ignore_index=True)
    
        # remerge into original sc 
        sc_out = pd.concat([sc_matched[~sc_matched.rb.isna()], sc_unmatched])
        sc_out = sc_out[[profile_id_col,'state','FIPS','NAME']].rename(columns={"FIPS":"cnty_fips", "NAME":"county"})        
    
    sc_final = sc.merge(sc_out, on=[profile_id_col, "state"], how="outer", suffixes=('_old', ''))

    ## some checks on the results
    # drop updated columns
    drop_cols = [c for c in sc_final.columns if "old" in c]
    if len(drop_cols) > 0:
        print(f"Replaced the following columns: {[col.replace('_old', '') for col in drop_cols]}")
        sc_final.drop(drop_cols, axis=1, inplace=True)

    # track new columns
    new_cols = [c for c in sc_final.columns if c not in sc.columns]
    if len(new_cols) > 0:
        print(f"Added the following columns: {new_cols}")

    # check for missing columns
    missing_cols = [c for c in sc.columns if c not in sc_final.columns]
    if len(missing_cols) > 0:
        print("Caution: the following columns from the original supply curve"
              f" are missing in the updated: {missing_cols}"
              )
        
    # make sure all points were matched and that no points are duplicated
    error_msg = ""
    failed_check = False
    if sc_final.cnty_fips.isna().sum() > 0:
        error_msg += "Some county fips code are missing; check county fips code matching in sc file saved for debugging.\n"
        failed_check = True
    if sc.shape[0] != sc_final.shape[0]:
        error_msg += "Final supply curve has a different number of rows; check county fips code matching in sc file saved for debugging.\n"
        failed_check = True
    # if a test fails write out supply curve for debugging and throw Exception
    if failed_check:
        sc_final.to_csv(os.path.join(outpath, 'results', 'DEBUG_processed_supply_curve_file.csv'), index=False)
        raise Exception(error_msg)
    
    return sc_final 

def add_land_fom(sc, tech, profile_id_col, hourlize_path, reeds_path, crf_year=2050):
    """adds capital cost to supply curve that serves as a proxy for land lease costs

    Parameters
    ----------
    sc
        pandas dataframe of supply curve
    tech
        technology being processed
    hourlize_path
        path to hourlize directory
    reeds_path
        path to ReEDS directory
    crf_year, optional
        year to select for crf, by default 2050

    Returns
    -------
        pandas dataframe with updated supply curve with columns that have land costs
    """
    
    print("Adding land cost adder based on fair market value")

    # no land cap adder for offshore wind, egs or geohydro at the moment
    if tech == "wind-ofs" or tech == "egs" or tech == "geohydro":
        sc['land_cap_adder_per_mw'] = 0
        return sc

    # lease component of FO&M from ATB 2023 ($/kW-yr)
    # note that upv is on a per kW-DC basis; we convert to AC later on to keep all costs in AC terms.
    LEASE_FOM = {'upv': 2.1, 'wind-ons': 4.2}

    ## calculate capital reovery factor (crf) using baseline ReEDS financial assumptions
    # note: a better approach would be to pass on as a fixed operating cost and then use the 
    # ReEDS internal CRF.

    # first get default financial assumptions
    sys_financials = pd.read_csv(os.path.join(reeds_path, "inputs", "financials", "financials_sys_ATB2023.csv"))
    inflation_df = pd.read_csv(os.path.join(reeds_path, "inputs", "financials",'inflation_default.csv'))
    sys_financials = sys_financials.merge(inflation_df, on='t', how='left')
    sys_financials['d_nom'] = (
        (1 - sys_financials['debt_fraction']) * (sys_financials['rroe_nom'] - 1) 
        + (sys_financials['debt_fraction']
           * (sys_financials['interest_rate_nom'] - 1)
           * (1 - sys_financials['tax_rate']))
        + 1
    )
    sys_financials['d_real'] = sys_financials['d_nom'] / sys_financials['inflation_rate']

    # next calculate the CRF
    def calc_crf(discount_rate, financial_lifetime):
      crf = (
        (discount_rate - 1)
            / (1 - (1 / discount_rate**financial_lifetime))
        )
      return crf
    sys_financials['crf'] = calc_crf(sys_financials['d_real'], 30)

    # select a year for CRF 
    crf = sys_financials.loc[sys_financials.t == crf_year].crf.squeeze()

    ## fair market values

    # read in updated fair market values from the reV team 
    fmv = pd.read_csv(os.path.join(hourlize_path, "inputs", "resource", "fair_market_value.csv"))

    # get median land cost
    fmv_med = fmv.places_fmv_all_rev.median()

    # drop any pre-existing land value columns (any original data was in log scale
    # but not corrected so should be replaced)
    sc = sc.drop(['places_fmv_all_rev'],axis=1,errors='ignore')

    # merge in updated land costs
    sc = sc.merge(fmv[[profile_id_col,'places_fmv_all_rev']], on=profile_id_col, how='left' )

    # calculate land cost adder ($/MW). this is computed by taking the difference in normalized land cost,
    # multiplying by the typical land cost FO&M related, and then using the CRF to convert to capital cost    
    # PV land FOM cost is originally in units of $/kW-DC, so convert to $/kw-AC by multiplying by the ILR here.
    sc['land_cap_adder_per_mw'] = (sc['places_fmv_all_rev'] - fmv_med)/fmv_med * (LEASE_FOM[tech] * 1e3 / crf ) * sc['ilr']

    # check number of rows is the same 
    assert sc.shape[0] == sc.shape[0], 'Updated data does not have the same number of rows as incoming data'

    print("Added 'land_cap_adder_per_mw' column")

    return sc

def adjust_rev_cols(tech, df, hourlize_path):
    """ identifies any missing columns that can be filled in. The run_hourlize script calls this function earlier to
    check for required columns before submitting a job, but calling again here to fill in missing values where possible.

    Parameters
    ----------
    tech
        technology being processed
    df
        pandas dataframe of supply curve

    Returns
    -------
        pandas dataframe with updated supply curve with columns that have land costs

    Raises
    ------
    Exception
        fails if there is a required column missing but no method defined to replace it
    """
    opt_cols_tech = ["multiplier_cc_eos", "multiplier_cc_regional"]

    from run_hourlize import check_cols
    __, missing_cols = check_cols(df, hourlize_path, [], opt_cols_tech)

    # these are instances of columns to rename to help manage differences 
    # in column names across rev versions or technologies
    RENAME_COLS = {}
    
    df_new = df.copy()
    for col in missing_cols:
        # if missing either of these set all values to 1
        if col in ['multiplier_cc_eos', 'multiplier_cc_regional']:
            df_new[col] = 1
            print(f"Missing {col}--will set to 1 by default")
        # if missing one of the 'rename' columns then just need to rename 
        elif col in RENAME_COLS:
            df_new.rename(columns={RENAME_COLS[col]:col}, inplace=True)
            print(f"Renamed {col} to {RENAME_COLS[col]}")
        else:
            raise Exception(f"There is no data for '{col}' and no method supplied for filling it.")
        
    return df_new

def add_ilr(tech, df, reeds_path, casename):
    # For UPV compute the inverter loading ratio (assume 1 for other techs)
    if tech == "upv":
        df['ilr'] = df['capacity_dc_mw'] / df['capacity_ac_mw']

        # check that value is unique to 2 decimal points
        ilr_unique = df['ilr'].round(2).unique()
        if len(ilr_unique) > 1:
            print(f"WARNING: Multiple ILRs detected for UPV: {ilr_unique}."
                  "Hourlize will run, but check whether ReEDS ILR assumptions to need to be updated.")
        # otherwise check that ILR matches ReEDS value
        else:
            scalars = reeds.io.get_scalars()
            ilr_reeds = scalars["ilr_utility"]
            ilr_rev = ilr_unique[0]

            if not math.isclose(ilr_rev, ilr_reeds, abs_tol=0.01):
                print(f"WARNING: the upv inverter-loading ratio for this reV supply curve data is {ilr_rev} "
                      f"but ReEDS currently assumes an ILR of {ilr_reeds}. It is recommended to update "
                      "the ReEDS assumption; see details in the 'UPDATE_ILR_WARNING.txt' file in the repo."
                      )

                ilr_update_file = os.path.join(reeds_path, 'inputs', "UPDATE_ILR_WARNING.txt")
                with open(ilr_update_file, "a") as file:
                    file.write(f"The upv inverter-loading ratio for {casename} from reV is {ilr_rev}\n"
                               f"but ReEDS currently assumes {ilr_reeds}. Please update the value\n"
                               "of 'ilr_utility' in the scalars.csv file. Delete this file after updating.\n\n"
                               )
            else:
                print("Confirmed reV and ReEDS ILR assumptions match.")
    else:
        df['ilr'] = 1

    return df

def get_supply_curve_and_preprocess(tech, original_sc_file, reeds_path, hourlize_path, outpath,
                                    reg_out_col, reg_map_file, min_cap, capacity_col, 
                                    existing_sites, state_abbrev, start_year, casename, 
                                    filter_cols={}, profile_id_col="sc_point_gid"):
    """processes reV supply curve file; output is a dataframe with a row for each supply curve point

    Parameters
    ----------
    tech
        technology to be processed
    original_sc_file
        path to original supply curve file
    reeds_path
        path to ReEDS directory
    hourlize_path
        path to hourlize directory
    reg_out_col
        column in supply curve file to use for 'region'
    reg_map_file
        path to file with region mapping
    min_cap
        capacity threshold for filtering out sites
    capacity_col
        column in supply curve file to use for 'capacity'
    existing_sites
        path to existing sites file
    state_abbrev
        path to state abbreviation file
    start_year
        start year to yse for existing sites
    filter_cols, optional
        dictionary identifying columns to filter as well as filtering condition, by default {}
    profile_id_col, optional
        id for columns that links profiles with supply curve , by default "sc_point_gid"

    Returns
    -------
        pandas dataframe with updated supply curve 
    """
    #Retrieve and filter the supply curve. Also, add a 'region' column, apply minimum capacity thresholds, and apply test mode if necessary.
    print('Reading supply curve inputs and filtering...')
    startTime = datetime.datetime.now()
    dfin = pd.read_csv(original_sc_file, low_memory=False)
    df = dfin.copy()

    # add ILR information
    df = add_ilr(tech, df, reeds_path, casename)

    # add county fips information; will replace existing county columns
    # in rev supply curve with version used in ReEDS
    df = match_to_counties(df, profile_id_col, reeds_path, outpath, tech)

    # add land cost using fair market value information from reV
    df = add_land_fom(df, tech, profile_id_col, hourlize_path, reeds_path)

    # handle any missing columns
    df = adjust_rev_cols(tech, df, hourlize_path)

    # Add 'capacity' column to match specified capacity_col
    if 'capacity' not in df.columns:
        df['capacity'] = df[capacity_col]
    if 'cnty_fips' in df.columns:
        cnty_na_cond = df['cnty_fips'].isna()
        cnty_na_count = len(df[cnty_na_cond])
        if(cnty_na_count > 0):
            print("WARNING: " + str(cnty_na_count) + " site(s) don't have cnty_fips. Removing them now.")
            df = df[~cnty_na_cond].copy()
        df['cnty_fips'] = df['cnty_fips'].astype(int)
    for k in filter_cols.keys():
        #Apply any filtering of the supply curve, e.g. to select onshore or offshore wind.
        if filter_cols[k][0] == '=':
            df = df[df[k] == filter_cols[k][1]].copy()
        elif filter_cols[k][0] == '>':
            df = df[df[k] > filter_cols[k][1]].copy()
        elif filter_cols[k][0] == '<':
            df = df[df[k] < filter_cols[k][1]].copy()
    
    ## define region    
    if reg_out_col == 'cnty_fips':
        # for county-level supply curves create region names based on county FIPS
        df['region'] = 'p'+df.cnty_fips.astype(str).map('{:>05}'.format)
    else:
        # if the specified regionality is already in the reV supply curve then use that column
        if reg_out_col in df.columns:
            print(f"Using '{reg_out_col}' directly from supply curve file")
            df['region'] = df[reg_out_col]
        # if not this means we must map the regions from county to reg_out_col using the mapping file supplied
        else:
            print(f"Mapping '{reg_out_col}' from {reg_map_file}")
            # assuming mapping file has a column called "county" with p+FIPS code and the column of interest
            try:
                df_map = pd.read_csv(reg_map_file, low_memory=False, usecols=["FIPS",reg_out_col])
            except ValueError as err:
                print(err)
                print(f"Check columns in {reg_map_file}")
                sys.exit(1)
            except FileNotFoundError:
                print(f"Could not read {reg_map_file} file, check path")
                sys.exit(1)
            df['county'] = 'p'+df.cnty_fips.astype(str).map('{:>05}'.format)
            df_map['county'] = 'p'+df_map.FIPS.astype(str).map('{:>05}'.format)
            df = pd.merge(left=df, right=df_map, how='left', on=["county"], sort=False)
            df.rename(columns={reg_out_col:'region'}, inplace=True)
    
    ## process existing sites
    if existing_sites is not None:
        print('Assigning existing sites...')
        #Read in existing sites and filter
        df_exist = pd.read_csv(existing_sites, low_memory=False)
        df_exist = df_exist[
            ['tech','TSTATE','reeds_ba','resource_region','Unique ID',
            'T_LONG','T_LAT','cap','StartYear','RetireYear']
        ].rename(columns={
            'TSTATE':'STATE', 'T_LAT':'LAT', 'T_LONG':'LONG', 'reeds_ba':'pca',
            'Unique ID':'UID', 'StartYear':'Commercial.Online.Year',
        }).copy()
        df_exist = df_exist[(df_exist['tech'].str.lower().str.contains(tech.lower())) & (df_exist['RetireYear'] > start_year)].reset_index(drop=True)
        df_exist['LONG'] = df_exist['LONG'] * -1
        df_exist.sort_values('cap', ascending=False, inplace=True)
        #Map the state codes of df_exist to the state names in df
        df_cp = df.copy()
        df_st = pd.read_csv(state_abbrev, low_memory=False)
        dict_st = dict(zip(df_st['ST'], df_st['State']))
        df_exist['STATE'] = df_exist['STATE'].map(dict_st)
        df_cp = df_cp[[profile_id_col, 'state','latitude','longitude','capacity']].copy()
        df_cp['existing_capacity'] = 0.0
        df_cp['existing_uid'] = 0
        df_cp['online_year'] = 0
        df_cp['retire_year'] = 0
        df_cp_out = pd.DataFrame()
        #Restrict matching to within the same state
        print("{:<18} {:>} MW".format("Total", round(df_exist.cap.sum()))) 
        print("{:<18} {:>}".format("-------", "-------")) 
        for st in df_exist['STATE'].unique():
            df_exist_st = df_exist[df_exist['STATE'] == st].copy()
            print("{:<18} {:>} MW".format(st, round(df_exist_st.cap.sum()))) 
            df_cp_st = df_cp[df_cp['state'] == st].copy()
            for i_exist, r_exist in df_exist_st.iterrows():
                #Current way to deal with lats and longs that don't exist
                if r_exist['LONG'] == 0:
                    continue
                #Assume each lat is ~69 miles and each long is ~53 miles
                df_cp_st['mi_sq'] =  ((df_cp_st['latitude'] - r_exist['LAT'])*69)**2 + ((df_cp_st['longitude'] - r_exist['LONG'])*53)**2
                #Sort by closest
                df_cp_st.sort_values(['mi_sq'], inplace=True)
                #Step through the available sites and fill up the closest ones until we are done with this existing capacity
                exist_cap_remain = r_exist['cap']
                for i_avail, r_avail in df_cp_st.iterrows():
                    avail_cap = df_cp_st.at[i_avail, 'capacity']
                    # TODO: handle missing UIDs
                    try:
                        df_cp_st.at[i_avail, 'existing_uid'] = r_exist['UID']
                    except Exception:
                        df_cp_st.at[i_avail, 'existing_uid'] = 0
                    df_cp_st.at[i_avail, 'online_year'] = r_exist['Commercial.Online.Year']
                    df_cp_st.at[i_avail, 'retire_year'] = r_exist['RetireYear']
                    if exist_cap_remain <= avail_cap:
                        df_cp_st.at[i_avail, 'existing_capacity'] = exist_cap_remain
                        exist_cap_remain = 0
                        break
                    else:
                        df_cp_st.at[i_avail, 'existing_capacity'] = avail_cap
                        exist_cap_remain = exist_cap_remain - avail_cap
                if exist_cap_remain > 0:
                    print('WARNING: Existing site shortfall: ' + str(exist_cap_remain))
                #Build output and take the available sites with existing capacity out of consideration for the next exisiting site
                df_cp_out_add = df_cp_st[df_cp_st['existing_capacity'] > 0].copy()
                df_cp_out = pd.concat([df_cp_out, df_cp_out_add], sort=False).reset_index(drop=True)
                df_cp_st = df_cp_st[df_cp_st['existing_capacity'] == 0].copy()
        df_cp_out['exist_mi_diff'] = df_cp_out['mi_sq']**0.5
        df_cp_out = df_cp_out[[profile_id_col, 'existing_capacity', 'existing_uid', 'online_year', 'retire_year', 'exist_mi_diff']].copy()
        df = pd.merge(left=df, right=df_cp_out, how='left', on=profile_id_col, sort=False)
        df[['existing_capacity','existing_uid','online_year','retire_year','exist_mi_diff']] = df[['existing_capacity','existing_uid','online_year','retire_year','exist_mi_diff']].fillna(0)
        df[['existing_uid','online_year','retire_year']] = df[['existing_uid','online_year','retire_year']].astype(int)
    else:
        df['existing_capacity'] = 0.0
    if min_cap > 0:
        #Remove sites with less than minimum capacity threshold, but keep sites that have existing capacity
        df = df[(df['capacity'] >= min_cap) | (df['existing_capacity'] > 0)].copy()
    print('Done reading supply curve inputs and filtering: '+ str(datetime.datetime.now() - startTime))
    return df

# add wind and solar class information to supply curve file. typical approach is to define 
# national classes based on capacity factor but can vary depending on the settings in the tech config
# files (see hourlize README for more details)
def add_classes(df_sc, class_path, class_bin, class_bin_col, class_bin_method, class_bin_num):
    #Add 'class' column to supply curve, based on specified class definitions in class_path.
    print('Adding classes...')
    startTime = datetime.datetime.now()
    #Create class column.
    if class_path is None:
        df_sc['class'] = '1'
    else:
        df_sc['class'] = 'NA' #Initialize to NA to make sure we have full coverage of classes here.
        df_class = pd.read_csv(class_path, index_col='class')
        #Now loop through classes (rows in df_class). Classes may have multiple defining criteria (columns in df_class),
        #so we loop through columns to build the selection criteria for each class, building up a 'mask' of criteria for each class.
        #Numeric ranges in class definitions (e.g. min and max wind speeds) are indicated by the pipe symbol, e.g. '5|6'
        #for 'mean_res' would mean 'mean_res' must fall between 5 and 6 for that class.
        for cname, row in df_class.iterrows():
            #Start with mask=True, and then build up the full conditional based on each column of df_class.
            mask = True
            for col, val in row.items():
                if '|' in val:
                    #Pipe is a special character that indicates a numeric range.
                    rng = val.split('|')
                    rng = [float(n) for n in rng]
                    mask = mask & (df_sc[col] >= min(rng))
                    mask = mask & (df_sc[col] < max(rng))
                else:
                    #No pipe symbol means we do a simple match.
                    mask = mask & (df_sc[col] == val)
            #Finally, apply the mask that has been built for this class.
            df_sc.loc[mask, 'class'] = cname
    # Add dynamic, region-specific class bins based on class_bin_method
    if class_bin:
        #In this case, class names in class_path must be numbered, starting at 1
        df_sc = df_sc.rename(columns={'class':'class_orig'})
        df_sc['class_orig'] = df_sc['class_orig'].astype(int)
        df_sc = (df_sc.groupby(['class_orig'], sort=False)
                      .apply(get_bin, bin_col=class_bin_col, bin_out_col='class_bin', weight_col= "capacity",
                             bin_num=class_bin_num, bin_method=class_bin_method)
                      .reset_index(drop=True))
        df_sc['class'] = (df_sc['class_orig'] - 1) * class_bin_num + df_sc['class_bin']
    print('Done adding classes: '+ str(datetime.datetime.now() - startTime))
    return df_sc

# bin supply curve points based on a specified bin column. Used here to created 'bins' for the 
# resource classes (typically using capacity factor) and then later used  by writesupplycurves.py 
# in ReEDS to create bins based on supply curve cost.
def get_bin(df_in, bin_num, bin_method='equal_cap_cut', 
            bin_col='supply_curve_cost_per_mw', bin_out_col='bin', weight_col='capacity'):
    df = df_in.copy()
    ser = df[bin_col]
    #If we have less than or equal unique points than bin_num, we simply group the points with the same values.
    if ser.unique().size <= bin_num:
        bin_ser = ser.rank(method='dense')
        df[bin_out_col] = bin_ser.values
    elif bin_method == 'kmeans':
        nparr = ser.to_numpy().reshape(-1,1)
        weights = df[weight_col].to_numpy()
        kmeans = sc.KMeans(n_clusters=bin_num, random_state=0, n_init=10).fit(nparr, sample_weight=weights)
        bin_ser = pd.Series(kmeans.labels_)
        #but kmeans doesn't necessarily label in order of increasing value because it is 2D,
        #so we replace labels with cluster centers, then rank
        kmeans_map = pd.Series(kmeans.cluster_centers_.flatten())
        bin_ser = bin_ser.map(kmeans_map).rank(method='dense')
        df[bin_out_col] = bin_ser.values
    elif bin_method == 'equal_cap_man':
        #using a manual method instead of pd.cut because i want the first bin to contain the
        #first sc point regardless, even if its weight_col value is more than the capacity of the bin,
        #and likewise for other bins, so i don't skip any bins.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        cumcaps = df[weight_col].cumsum().tolist()
        totcap = df[weight_col].sum()
        vals = df[bin_col].tolist()
        bins = []
        curbin = 1
        for i, _v in enumerate(vals):
            bins.append(curbin)
            if cumcaps[i] >= totcap*curbin/bin_num:
                curbin += 1
        df[bin_out_col] = bins
        df = df.reindex(index=orig_index) #we need the same index ordering for apply to work.
    elif bin_method == 'equal_cap_cut':
        #Use pandas.cut with cumulative capacity in each class. This will assume equal capacity bins
        #to bin the data.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        df['cum_cap'] = df[weight_col].cumsum()
        bin_ser = pd.cut(df['cum_cap'], bin_num, labels=False)
        bin_ser = bin_ser.rank(method='dense')
        df[bin_out_col] = bin_ser.values
        df = df.reindex(index=orig_index) #we need the same index ordering for apply to work.
    df[bin_out_col] = df[bin_out_col].astype(int)
    return df

# calculate supply curve cost components and total for ReEDS.
# note that all transmission costs and adders are always defined in terms of $/MW-AC (not $/MW-DC),
# even when running with upv_type=DC. Conversion of this costs to $/MW-DC for UPV occurs downstream in
# ReEDS (see "convert UPV costs from $/MW-AC to $/MW-DC" comment in b_inputs.gms) 
def add_cost(df_sc, tech, reg_out_col):
    # set network reinforcement costs to zero if running county-level supply curves
    if reg_out_col == 'cnty_fips':
        print('Running county-level supply curves, so setting any network reinforcement costs to zero.')
        if tech == "egs" or tech == "geohydro":
            df_sc['trans_adder_per_mw'] = df_sc['trans_cap_cost_per_mw'] - df_sc['reinforcement_cost_per_mw']
            df_sc['reinforcement_cost_per_mw'] = 0
        else:
            df_sc['cost_total_trans_usd_per_mw'] = df_sc['cost_total_trans_usd_per_mw'] - df_sc['cost_reinforcement_usd_per_mw']
            df_sc['cost_reinforcement_usd_per_mw'] = 0 

    # Generate the supply_curve_cost_per_mw column. Special cost_out values correspond to
    # a calculation using one or more columns, but the default is to use the cost_out
    # directly as supply_curve_cost_per_mw
    if tech in ['upv', 'wind-ons']:
        ## capital cost adders
        # first term computes the combined eos and regional multiplier by subtracting the 'base' costs (without the multipliers)
        # from the 'full' site costs (with the multipliers); second term adds in the land capital cost adder to the eos/regional adders.
        df_sc['capital_adder_per_mw'] = (
            (df_sc['cost_site_occ_usd_per_ac_mw'] - df_sc['cost_base_occ_usd_per_ac_mw'] )
            + df_sc['land_cap_adder_per_mw']
        )
        
        ## transmission cost adders    
        df_sc['trans_adder_per_mw'] = df_sc['cost_total_trans_usd_per_mw']
        
        ## total supply curve cost adders
        df_sc['supply_curve_cost_per_mw'] = df_sc['trans_adder_per_mw'] + df_sc['capital_adder_per_mw']

    elif tech == "egs" or tech == "geohydro":
        df_sc['capital_adder_per_mw'] = 0
        df_sc['trans_adder_per_mw'] = df_sc['cost_total_trans_usd_per_mw']

        ## total supply curve cost adders
        df_sc['supply_curve_cost_per_mw'] = df_sc['trans_adder_per_mw'] + df_sc['capital_adder_per_mw']

    elif tech == 'wind-ofs':   
        ## transmission cost adders
        df_sc['trans_adder_per_mw'] = (df_sc['cost_spur_usd_per_mw'] + df_sc['cost_reinforcement_usd_per_mw']
                                    + df_sc['cost_export_usd_per_mw'] + df_sc['cost_array_usd_per_mw'] + df_sc['cost_poi_usd_per_mw']
        )
        ## capital cost adders
        # Since the site capex (column cost_capex_2035_usd_per_mw) has site specific multipliers (tech specific) baked in, we need to divide the capex by the multipliers to obtain the base capex 
        df_sc['capital_adder_per_mw'] = (df_sc['cost_capex_2035_usd_per_mw'] * df_sc['multiplier_cc_eos'] * df_sc['multiplier_cc_regional']
                                    - (df_sc['cost_capex_2035_usd_per_mw'] / df_sc['multiplier_cc_site_specific'])
        )
        ## total supply curve cost adders
        df_sc['supply_curve_cost_per_mw'] = df_sc['trans_adder_per_mw'] + df_sc['capital_adder_per_mw']

    else:
        error_msg = (f"No cost method defined for {tech}; "
                     "please update the 'add_cost' function in resource.py to support your tech." 
                    )
        raise Exception(error_msg)

    print('Done adding supply-curve cost column.')

    return df_sc

#%% ===========================================================================
### --- PROFILES ---
### ===========================================================================

# get resource profiles for aggregated supply curve, using a weighted average based on a user specified column
def get_profiles_allyears_weightedave(
        df_sc, rev_path, rev_case, hourly_out_years, profile_dset,
        profile_dir, profile_id_col, profile_weight_col, tech, upv_type_out, profile_file_format, single_profile):
    """
    Get the weighted average profiles for all years rather than representative profiles
    """
    print('Getting multiyear profiles...')
    startTime = datetime.datetime.now()
    ## Create df_rep, the dataframe to map region,class to timezone, using capacity weighting to assign timezone.
    def wm(x):
        return np.average(x, weights=df_sc.loc[x.index, 'capacity']) if df_sc.loc[x.index, 'capacity'].sum() > 0 else 0
    df_rep = df_sc.groupby(['region','class'], as_index =False).agg({'timezone':wm})
    df_rep['timezone'] = df_rep['timezone'].round().astype(int)
    #%% Get the weights for weighted average of profiles
    dfweight_regionclass = df_sc.groupby(['region','class'])[profile_weight_col].sum()
    #%% consolidate sc to dimensions used to match with profile
    df_sc_grouped = df_sc.groupby(['region','class',profile_id_col], as_index=False)[profile_weight_col].sum()
    ## check for duplicates here (otherwise colweights will break)
    if df_sc_grouped[profile_id_col].duplicated().sum() > 0:
        duplicates = df_sc_grouped.loc[df_sc_grouped[profile_id_col].duplicated(), profile_id_col].tolist()
        error_msg = (f"The following entries for {profile_id_col} are duplicated in the supply curve: {duplicates}. "
                     "Check your supply curve file and correct before re-running hourlize."
                    )
        raise Exception(error_msg)
    dfweight_id = (
        df_sc_grouped[['region','class',profile_weight_col,profile_id_col]]
        .merge(
            dfweight_regionclass, left_on=['region','class'], right_index=True,
            suffixes=['_index','_regionclass'])
        .sort_values(profile_id_col)
    )
    dfweight_id['weight'] = (
        dfweight_id[profile_weight_col+'_index']
        / dfweight_id[profile_weight_col+'_regionclass'])
    colweight = dfweight_id.set_index(profile_id_col).weight.copy()
    ## get mappping of sites to region,class
    id_to_regionclass = pd.Series(
        index=dfweight_id[profile_id_col],
        data=zip(dfweight_id.region, dfweight_id['class']),
    )
    ## Load hourly profile for each year
    dfyears = []
    for year in hourly_out_years:
        if single_profile: #only one profile file
            h5path = os.path.join(
                rev_path, profile_dir,
                f'{rev_case}_bespoke.h5')
            with h5py.File(h5path, 'r') as h5:
                dfall = pd.DataFrame(h5[f'cf_profile-{year}'][:])
                # adjust profiles by scaling factor
                scale_factor = h5[f'cf_profile-{year}'].attrs['scale_factor']
                dfall = dfall/scale_factor
                # read meta and time index
                df_meta = pd.DataFrame(h5['meta'][:])
                df_index = pd.Series(h5[f'time_index-{year}'][:])
        else:
            h5path = os.path.join(
                rev_path, profile_dir, f'{profile_file_format}_{year}.h5')
            with h5py.File(h5path, 'r') as h5:
                dfall = pd.DataFrame(h5[profile_dset][:])
                # read meta and time index
                df_meta = pd.DataFrame(h5['meta'][:])
                df_index = pd.Series(h5['time_index'][:])

        ## Check that meta and profile are the same dimensions
        assert dfall.shape[1] == df_meta.shape[0], f"Dimensions of profile ({dfall.shape[1]}) do not match meta file dimensions ({df_meta.shape[0]}) in {profile_file_format}_{year}.h5"        
        ## Change hourly profile column names from simple index to associated id specified by profile_id_col (usually sc_point_gid)
        dfall.columns = dfall.columns.map(df_meta[profile_id_col])
        ## Add time index
        df_index = pd.to_datetime(df_index.str.decode("utf-8"))
        dfall = dfall.set_index(df_index)

        ## reV only produces AC profiles so we always read in those. If we're running hourlize to produce 
        ## DC UPV outputs then we convert to 'DC' profiles here. Note that these do not actually represent 
        ## pre-inverter profiles, but rather are just AC output / DC capacity.
        if tech == "upv" and upv_type_out.lower() == "dc":
            ilr_by_site = df_sc.set_index(profile_id_col).ilr.copy() 
            dfall /= ilr_by_site

        ### Multiply each column by its weight, then drop the unweighted columns
        dfall *= colweight
        dfall.dropna(axis=1, inplace=True)
        ### Switch to (region,class) index
        dfall.columns = dfall.columns.map(id_to_regionclass)
        ### Sum by (region,class) to finish weighted average of site profiles
        dfall = dfall.T.groupby(level=[0,1]).sum().T
        ### Keep columns in the (region,class) order from df_rep
        dfall = dfall[list(zip(df_rep.region, df_rep['class']))].copy()
        dfyears.append(dfall)
        print('Done with ' + str(year))
    
    
    ### Concatenate individual years, drop indices
    df_prof_out = pd.concat(dfyears, axis=0)
    print('Done getting multiyear profiles: '+ str(datetime.datetime.now() - startTime))
    return df_rep, df_prof_out

def shift_timezones(df_prof, hourly_out_years, output_timezone):
    # make sure profiles are sorted by timeindex
    df_prof = df_prof.sort_index()
    # preserve copy of original profile
    df_prof_out = df_prof.copy()
    # shift timezone of hourly data
    if isinstance(output_timezone, int):
        output_timezone = f"Etc/GMT{'+' if output_timezone > 0 else ''}{output_timezone}"
    try:
        df_prof_out = df_prof_out.tz_convert(output_timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"{output_timezone} is not a valid specification for 'output_timezone'.")        
    # wrap hours shifted to years outside the dataset
    data_years = df_prof_out.index.year.unique()
    hourly_out_years.sort()
    extra_years = [year for year in data_years if year not in hourly_out_years]
    # identify groups of consecutive years in the data by looking for gaps > 1 year
    year_diffs = np.diff(hourly_out_years)
    year_groups = np.split(hourly_out_years, np.where(year_diffs != 1)[0]+1) 
    year_groups = [(group[0], group[-1]) for group in year_groups]
    # number of "extra" to wrap should match the number of consecutive year groups
    assert (len(extra_years) == len(year_groups)
            ), "ERROR: number extra years after timezone shifting do not match consecutive year groups."
    for (ey, yg) in zip(extra_years, year_groups):
        # determine whether wrapped data goes at the start or the end
        if ey < yg[0]:
            year_to_wrap = yg[1]
        else:
            year_to_wrap = yg[0]
        # subset extra year, update the year, and then add back to data
        prof_wrap = df_prof_out.loc[df_prof_out.index.year == ey]
        prof_wrap.index = prof_wrap.index.map(lambda t: t.replace(year=year_to_wrap))
        df_prof_out = pd.concat([df_prof_out.loc[df_prof_out.index.year != ey], prof_wrap]).sort_index()

    # for any leap years we need to adjust Dec 31 back to Dec 30 (Dec 31 dropped in reV to maintain 8760)
    leap_years = [year for year in hourly_out_years if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)]
    for ly in leap_years:
        # get last 24 hours of the profile in that year
        last_day = df_prof_out[df_prof_out.index.year == ly].tail(24)
        # if there are two different dates in the last 24 hours, update the latter date to match the former
        last_day_list = last_day.index.day.unique().to_list()
        if len(last_day_list) > 1:
            last_day_list.sort()
            last_day_drop = last_day.index
            last_day.index = last_day.index.map(lambda t: t.replace(day=last_day_list[0]))
            df_prof_out = pd.concat([df_prof_out.drop(index=last_day_drop), last_day]).sort_index()

    # verify that wrapping leaves same number of rows
    assert (len(df_prof_out) == len(df_prof)
            ), "ERROR: wrapping after timezone adjustment resulted in a different number of rows in the profile."
    # check that we have the right years
    assert len([year for year in df_prof_out.index.year.unique() if year not in hourly_out_years]
               ) == 0, "ERROR: timezone shift resulted in a year outside of those specified in hourly_out_years."

    return df_prof_out

#%% ===========================================================================
### --- SAVE OUTPUTS ---
### ===========================================================================

# save supply curve output files
def save_sc_outputs(
        df_sc, existing_sites, start_year, outpath, tech,
        distance_cols, cost_adder_components, subtract_exog, profile_id_col, decimals):
    #Save resource supply curve outputs
    print('Saving supply curve outputs...')
    startTime = datetime.datetime.now()
    #Create local copy of df_sc so that we don't modify the df_sc passed by reference
    df_sc = df_sc.copy()
    # save copy of pre-processed reV supply curve
    df_sc.to_csv(os.path.join(outpath, 'results', tech + '_supply_curve_raw.csv'), index=False)
    #Round now to prevent infeasibility in model because existing (pre-2010 + prescribed) capacity is slightly higher than supply curve capacity
    df_sc[['capacity','existing_capacity']] = df_sc[['capacity','existing_capacity']].round(decimals)
    if existing_sites:
        # bincol = ['sc_point_gid'] if exog_bin else []
        df_exist = df_sc[df_sc['existing_capacity'] > 0].copy()
        #Exogenous (pre-start-year) capacity output
        df_exog = df_exist[df_exist['online_year'] < start_year].copy()
        # # Write the full existing-capacity table
        # df_exog[[
        #     'region','class','bin','sc_point_gid','cnty_fips','online_year','retire_year',
        #     'dist_km','trans_cap_cost_per_mw','supply_curve_cost_per_mw','existing_capacity',
        # ]].to_csv(os.path.join(outpath, 'results', tech+'_existing_cap_pre{}.csv'.format(start_year)), index=False)
        # Aggregate existing capacity to (i,rs,t)
        if not df_exog.empty:
            df_exog = df_exog[[profile_id_col, 'class','region','retire_year','existing_capacity']].copy()
            max_exog_ret_year = df_exog['retire_year'].max()
            ret_year_ls = list(range(start_year,max_exog_ret_year + 1))
            df_exog = df_exog.pivot_table(index=[profile_id_col,'class','region'], columns='retire_year', values='existing_capacity')
            # Make a column for every year until the largest retirement year
            df_exog = df_exog.reindex(columns=ret_year_ls).fillna(method='bfill', axis='columns')
            df_exog = pd.melt(
                df_exog.reset_index(), id_vars= [profile_id_col,'class','region'],
                value_vars=ret_year_ls, var_name='year', value_name='capacity')
            df_exog = df_exog[df_exog['capacity'].notnull()].copy()
            if(tech == 'egs' or tech == 'geohydro'):
                df_exog['tech'] = tech + '_allkm_' + df_exog['class'].astype(str)
            else:
                df_exog['tech'] = tech + '_' + df_exog['class'].astype(str)
            df_exog = df_exog[[profile_id_col,'tech','region','year','capacity']].copy()
            df_exog = df_exog.groupby(['tech','region','year',profile_id_col], sort=False, as_index=False).sum()
            df_exog['capacity'] =  df_exog['capacity'].round(decimals)
            df_exog = df_exog.sort_values(['year',profile_id_col])
            df_exog.to_csv(os.path.join(outpath, 'results', tech + '_exog_cap.csv'), index=False)
        #Prescribed capacity output
        df_pre = df_exist[df_exist['online_year'] >= start_year].copy()
        if not df_pre.empty:
            df_pre = df_pre[['region','online_year','existing_capacity']].copy()
            df_pre = df_pre.rename(columns={'online_year':'year', 'existing_capacity':'capacity'})
            df_pre = df_pre.groupby(['region','year'], sort=False, as_index =False).sum()
            df_pre['capacity'] =  df_pre['capacity'].round(decimals)
            df_pre = df_pre.sort_values(['year','region'])
            df_pre.to_csv(os.path.join(outpath, 'results', tech + '_prescribed_builds.csv'), index=False)
        #Reduce supply curve based on exogenous (pre-start-year) capacity
        if subtract_exog:
            criteria = (df_sc['online_year'] > 0) & (df_sc['online_year'] < start_year)
            df_sc.loc[criteria, 'capacity'] = (
                df_sc.loc[criteria, 'capacity'] - df_sc.loc[criteria, 'existing_capacity'])

    keepcols = ['capacity', 'supply_curve_cost_per_mw'] + cost_adder_components + distance_cols

    df_sc_out = df_sc[['region','class',profile_id_col] + keepcols].copy()
    df_sc_out[keepcols] = df_sc_out[keepcols].round(decimals)
    df_sc_out = df_sc_out.sort_values(['region','class',profile_id_col])
    df_sc_out.to_csv(os.path.join(outpath, 'results', tech + '_supply_curve.csv'), index=False)

    print('Done saving supply curve outputs: '+ str(datetime.datetime.now() - startTime))

def save_time_outputs(df_prof_out, df_rep, outpath, tech,
                      filetype='h5', compression_opts=4, dtype=np.float16, decimals=4):
    #Save performance characteristics (capacity factor means, standard deviations, and corrections) and hourly profiles.
    print('Saving time-dependent outputs...')
    startTime = datetime.datetime.now()
    # round hourly profiles number of decimals specified in config
    df_hr = df_prof_out.round(decimals)
    # combine class,regional column index into 1 name using '|' delimiter 
    df_hr.columns = df_hr.columns.map('{0[1]}|{0[0]}'.format)

    if 'csv' in filetype:
        df_hr.to_csv(os.path.join(outpath, 'results', tech + '.csv.gz'))
    else:
        # validate and convert dtype entry
        if isinstance(dtype, str):
            if dtype not in ["np.float16", "np.float32"]:
                print(f"{dtype} is not a valid dtype entry. Reverting to 'np.float16'")
                dtype = np.float16
            else:
                dtype = getattr(np, dtype.replace("np.", "")) 

        df_hr.index.name = "datetime"
        reeds.io.write_profile_to_h5(
            df_hr, f'{tech}.h5', os.path.join(outpath, 'results'),
            compression_opts=compression_opts)

    df_rep.to_csv(os.path.join(outpath, 'results', tech + '_rep_profiles_meta.csv'), index=False)
    print('Done saving time-dependent outputs: '+ str(datetime.datetime.now() - startTime))

def copy_outputs(outpath, reeds_path, sc_path, casename, reg_out_col,
                 copy_to_reeds, copy_to_shared, rev_jsons, configpath):

    #Save outputs to the shared drive and to this reeds repo.
    print('Copying outputs to shared drive and/or reeds repo')
    startTime = datetime.datetime.now()

    # tech should be the first part of the case name
    tech = casename.split("_")[0]
    # case is the rest of the case (usually access case + regionality)
    case = casename.replace(tech+"_", "")
    
    resultspath = os.path.join(outpath, 'results')
    inputspath = os.path.join(reeds_path, 'inputs')

    if copy_to_reeds:
        #Supply curve
        shutil.copy2(
            os.path.join(resultspath, f'{tech}_supply_curve.csv'),
            os.path.join(inputspath, 'supply_curve',f'{tech}_supply_curve-{case}.csv')
        )
        #Prescribed builds and exogenous capacity (if they exist)
        try:
            shutil.copy2(
                os.path.join(resultspath, f'{tech}_prescribed_builds.csv'),
                os.path.join(inputspath,'capacity_exogenous',f'{tech}_prescribed_builds_{case}.csv')
            )
        except Exception:
            print('WARNING: No prescribed builds')
        try:
            df = pd.read_csv(os.path.join(resultspath,f'{tech}_exog_cap.csv'))
            df.rename(columns={df.columns[0]: '*'+str(df.columns[0])}, inplace=True)
            df.to_csv(
                os.path.join(inputspath,'capacity_exogenous',f'{tech}_exog_cap_{case}.csv'),
                index=False
            )
        except Exception:
            print('WARNING: No exogenous capacity')
        #Hourly profiles
        if reg_out_col == "cnty_fips" or "county" in casename:
            print("""County-level supply profiles are not kept in the repo due to their size 
                    and will not be copied to ReEDS""")
        else:
            #Hourly profiles
            try:
                shutil.copy2(
                    os.path.join(resultspath, f'{tech}.h5'),
                    os.path.join(inputspath,'variability','multi_year',f'{tech}-{case}.h5')
                )
            except Exception:
                print('WARNING: No hourly profiles')

        ## Metadata
        # rev configs
        meta_path = os.path.join(inputspath,'supply_curve','metadata',f'{casename}')
        if os.path.exists(meta_path):
            shutil.rmtree(meta_path)
        os.makedirs(meta_path)
        for metafile in rev_jsons:
            try:
                shutil.copy(
                    os.path.join(outpath, 'inputs', 'rev_configs', os.path.basename(metafile)),
                    os.path.join(meta_path,os.path.basename(metafile)),
                )
            except FileNotFoundError as err:
                print(err)
        
        # hourlize config
        shutil.copy(
                configpath,
                os.path.join(meta_path,os.path.basename(configpath)),
            )

        # Copy the readme file if there is one
        for ext in ['.yaml', '.yml', '.md', '.txt', '']:
            try:
                shutil.copy2(
                    os.path.join(outpath,'inputs','readme'+ext),
                    os.path.join(meta_path,''),
                )
            except Exception:
                pass

    if copy_to_shared:
        shared_drive_path = os.path.join(sc_path, os.path.basename(os.path.normpath(outpath)))
        #Create output directory, creating backup if one already exists.
        if os.path.exists(shared_drive_path):
            time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            os.rename(shared_drive_path, shared_drive_path + '-archive-'+time)
        shutil.copytree(outpath, shared_drive_path)
        
    print('Done copying outputs to shared drive and/or reeds repo: '+ str(datetime.datetime.now() - startTime))

#%% ===========================================================================
### --- PLOTTING ---
### ===========================================================================

def map_supplycurve(
        tech, reg_out_col, df_sc, sc_file, outpath, reeds_path,
        cm=None, dpi=None, profile_id_col="sc_point_gid",
    ):
    #%%### Imports
    ## Turn off loggers for imported packages
    for i in ['matplotlib','shapely','fiona','pyproj']:
        logging.getLogger(i).setLevel(logging.CRITICAL)
    import matplotlib.pyplot as plt
    import os
    import site
    import geopandas as gpd
    import cmocean
    os.environ['PROJ_NETWORK'] = 'OFF'

    site.addsitedir(reeds_path)
    from reeds import plots
    plots.plotparams()
    os.makedirs(os.path.join(outpath, 'plots'), exist_ok=True)

    #%%### Format inputs
    if not cm:
        cmap = cmocean.cm.rain
    else:
        cmap = cm
    ms = {'wind-ofs':1.75, 'wind-ons':2.65, 'upv':2.65}[tech]  
    
    labels = {
        'capacity_mw': 'Available capacity [MW]',
        'spur_cost_per_kw': 'Spur-line cost [$/kW]', 
        'poi_cost_per_kw': 'Substation interconnection cost [$/kW]',
        'export_cost_per_kw': 'Offshore wind export cable cost [$/kW]',
        'reinforcement_cost_per_kw': 'Reinforcement cost [$/kW]',
        'trans_cap_cost_per_kw': 'Total transmission interconnection cost [$/kW]',
        'land_cap_adder_per_kw': 'Land cost adder [$/kW]',
        'multiplier_cc_regional': 'Regional multipler',
        'mean_cf': 'Capacity factor [.]',
        'dist_spur_km': 'Spur-line distance [km]',
        'dist_export_km': 'Offshore export cable distance [km]',
        'dist_reinforcement_km': 'Reinforcement distance [km]',
        'area_developable_sq_km': 'Area [km^2]',
        'lcoe_site_usd_per_mwh': 'LCOE [$/MWh]',
        'lcot_usd_per_mwh': 'LCOT [$/MWh]',
        'lcoe_all_in_usd_per_mwh': 'LCOE + LCOT [$/MWh]',

    }
    vmax = {
        ## use 402 for wind with 6 MW turbines
        'capacity_mw': {'wind-ons':400.,'wind-ofs':1100.,'upv':4000.}[tech],
        'spur_cost_per_kw': 2000.,
        'poi_cost_per_kw': 2000.,
        'export_cost_per_kw': 2000.,
        'reinforcement_cost_per_kw': 2000.,
        'trans_cap_cost_per_kw': 2000.,
        'land_cap_adder_per_kw': 2000.,
        'multiplier_cc_regional': 1.5,
        'mean_cf': 0.60,
        'dist_spur_km': 50.,
        'dist_export_km': 200.,
        'dist_reinforcement_km': 200.,
        'area_developable_sq_km': 11.5**2,
        'lcoe_site_usd_per_mwh': 100.,
        'lcot_usd_per_mwh': 100.,
        'lcoe_all_in_usd_per_mwh': 100.,
    }
    vmin = {
        'capacity_mw': 0.,
        'spur_cost_per_kw': 0.,
        'poi_cost_per_kw': 0.,
        'export_cost_per_kw': 0.,
        'reinforcement_cost_per_kw': 0.,
        'trans_cap_cost_per_kw': 0.,
        'land_cap_adder_per_kw': 0.,
        'multiplier_cc_regional': 0.5,
        'mean_cf': 0.,
        'dist_spur_km': 0.,
        'dist_export_km': 0.,
        'dist_reinforcement_km': 0.,
        'area_developable_sq_km': 0.,
        'mean_lcoe': 0.,
        'lcoe_site_usd_per_mwh': 0.,
        'lcot_usd_per_mwh': 0.,
        'lcoe_all_in_usd_per_mwh': 0.,
    }
    background = {
        'capacity_mw': False,
        'spur_cost_per_kw': True,
        'poi_cost_per_kw': True,
        'export_cost_per_kw': True,
        'reinforcement_cost_per_kw': True,
        'trans_cap_cost_per_kw': True,
        'land_cap_adder_per_kw': True,
        'multiplier_cc_regional': True,
        'mean_cf': True,
        'dist_spur_km': True,
        'dist_export_km': True,
        'dist_reinforcement_km': True,
        'area_developable_sq_km': False,
        'lcoe_site_usd_per_mwh': True,
        'lcot_usd_per_mwh': True,
        'lcoe_all_in_usd_per_mwh': True,
    }

    # list of plots to not run for each tech
    exclude = {
        'wind-ofs': ['land_cap_adder_per_kw'],
        'wind-ons': ['dist_export_km', 'export_cost_per_kw'],
        'upv'     : ['dist_export_km', 'export_cost_per_kw']
    }

    #%%### Load data
    dfsc = df_sc.set_index(profile_id_col)

    ### Convert to geopandas dataframe
    dfsc = plots.df2gdf(dfsc)

    #%% Load ReEDS regions
    if reg_out_col == 'cnty_fips':
        dfba = (
            gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','US_COUNTY_2022'))
            .set_index('rb'))
        dfba.rename(columns={'STCODE':'st'}, inplace=True)
        dfba['st'] = dfba['st'].str.lower()
    else:
        dfba = (
            gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','US_PCA'))
            .set_index('rb'))
    ### Aggregate to states
    dfstates = dfba.dissolve('st')
    ### Get the lakes
    lakes = gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','greatlakes.gpkg'))

    #%% Processing
    dfplot = dfsc.rename(columns={
        'capacity':'capacity_mw',
        'capacity_factor_ac':'mean_cf',
    }).copy()
    ## Convert to $/kW
    dfplot['spur_cost_per_kw'] = dfplot['cost_spur_usd_per_mw'] / 1000
    dfplot['poi_cost_per_kw'] = dfplot['cost_poi_usd_per_mw'] / 1000
    dfplot['reinforcement_cost_per_kw'] = dfplot['cost_reinforcement_usd_per_mw'] / 1000
    if tech == 'wind-ofs' and 'cost_export_usd_per_mw' in dfplot:
        dfplot['export_cost_per_kw'] = dfplot['cost_export_usd_per_mw'] / 1000
    dfplot['trans_cap_cost_per_kw'] = dfplot['cost_total_trans_usd_per_mw'] / 1000
    dfplot['land_cap_adder_per_kw'] = dfplot['land_cap_adder_per_mw'] / 1000

    #%% Plot it
    for col in labels:
        if col not in dfplot:
            print(f"{col} is not in the supply curve table")
            continue
        if col in exclude[tech]:
            print(f"skipping {col} for {tech}")
            continue
        plt.close()
        f,ax = plt.subplots(figsize=(12,9), dpi=dpi)
        ### Background
        if background[col]:
            dfba.plot(ax=ax, facecolor='C7', edgecolor='none', lw=0.3, zorder=-1e6)
        dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.3, zorder=1e6)
        dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.5, zorder=2e6)
        lakes.plot(ax=ax, edgecolor='#2CA8E7', facecolor='#D3EFFA', lw=0.2, zorder=-1)
        ### Map of data
        dfplot.plot(
            ax=ax, column=col,
            cmap=cmap, marker='s', markersize=ms, lw=0,
            legend=False, vmin=vmin[col], vmax=vmax[col],
        )
        ### Colorbar-histogram
        plots.addcolorbarhist(
            f=f, ax0=ax, data=dfplot[col].values,
            title=labels[col], cmap=cmap,
            vmin=vmin[col], vmax=vmax[col],
            orientation='horizontal', labelpad=2.1, cbarbottom=-0.06,
            cbarheight=0.7, log=False,
            ## use nbins=68 for wind with 6 MW turbines
            nbins=101, histratio=2,
            ticklabel_fontsize=20, title_fontsize=24,
            extend='neither',
        )
        ### Annotation
        ax.set_title(sc_file, fontsize='small', y=0.97)
        note = str(dfplot[col].describe().round(3))
        note = note[:note.index('\nName')]
        ax.annotate(note, (-1.05e6, -1.05e6), ha='right', va='top', fontsize=8)
        ### Formatting
        ax.axis('off')
        plt.savefig(os.path.join(outpath, 'plots', f'{tech}-{col}.png'), dpi=dpi)
        plt.close()
        print(f'mapped {col}')

#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__== '__main__':
    #%% load arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='', help='path to config file for this run')
    parser.add_argument('--nolog', '-n', default=False, action='store_true', help='turn off logging for debugging')

    args = parser.parse_args()
    configpath = args.config
    nolog = args.nolog
    startTime = datetime.datetime.now()

    #%% load config information
    with open(configpath, "r") as f:
        config = json.load(f, object_pairs_hook=OrderedDict)
    cf = SimpleNamespace(**config)

    #%% look for upv output type (AC or DC)
    if cf.tech == "upv":
        upv_type_out = cf.upv_type_out
    else:
        upv_type_out = None

    #%% import additional modules using path to ReEDS
    site.addsitedir(cf.reeds_path)
    from preprocessing import geo_supply_curve_aggregation
    import reeds
    
    #%% setup logging
    if not nolog:
        log = reeds.log.makelog(
            scriptname=__file__,
            logpath=os.path.join(cf.outpath, f'log_{cf.casename}.txt'),
        )

    #%% Make copies of rev jsons
    rev_jsons = copy_rev_jsons(cf.outpath, cf.rev_path)

    if cf.tech == 'egs' or cf.tech == 'geohydro':
        if cf.geo_run_supply_curve_aggregation:
            print('Aggregating raw geothermal supply curves...')
            if cf.geo_aggregation_method == 'lowest_lcoe':
                geo_supply_curve_aggregation.process_raw_supply_curves(
                    rev_cases_path=cf.rev_path, rev_sc_file_path=cf.original_sc_file)
            else:
                raise NotImplementedError(f'Specified aggregation method {cf.geo_aggregation_method} has not been implemented')

    #%% Get supply curves
    df_sc = get_supply_curve_and_preprocess(
        cf.tech, cf.original_sc_file, cf.reeds_path, cf.hourlize_path, cf.outpath,
        cf.reg_out_col, cf.reg_map_file, cf.min_cap, cf.capacity_col, cf.existing_sites, cf.state_abbrev,
        cf.start_year, cf.casename, cf.filter_cols, cf.profile_id_col)

    #%% Add classes
    df_sc = add_classes(
        df_sc, cf.class_path, cf.class_bin, cf.class_bin_col, 
        cf.class_bin_method, cf.class_bin_num)

    #%% Add cost
    df_sc = add_cost(df_sc, cf.tech, cf.reg_out_col)

    #%% Save the supply curve
    save_sc_outputs(
        df_sc, cf.existing_sites,cf.start_year, cf.outpath, cf.tech,
        cf.distance_cols, cf.cost_adder_components, cf.subtract_exog, cf.profile_id_col, cf.decimals)

    if cf.process_profiles:
        #%% Get the profiles
        df_rep, df_prof_out = get_profiles_allyears_weightedave(
        df_sc, cf.rev_path, cf.rev_case,
            cf.hourly_out_years, cf.profile_dset,
            cf.profile_dir, cf.profile_id_col,
            cf.profile_weight_col, cf.tech, upv_type_out, cf.profile_file_format, cf.single_profile)
    
        #%% Shift timezones
        df_prof_out = shift_timezones(
            df_prof_out, cf.hourly_out_years, cf.output_timezone)

        #%% Save hourly profiles
        save_time_outputs(
            df_prof_out,df_rep, cf.outpath, cf.tech,
            cf.filetype, cf.compression_opts, cf.dtype)

    if cf.map_supply_curve:
        #%% Map the supply curve
        try:
            map_supplycurve(
            cf.tech, cf.reg_out_col, df_sc, cf.sc_file, cf.outpath, cf.reeds_path,
            cm=None, dpi=None, profile_id_col=cf.profile_id_col)
        except Exception as err:
            print(f'map_cupplycurve() failed with the following exception:\n{err}')

    #%% Copy outputs to ReEDS and/or the shared drive
    copy_outputs(
        cf.outpath, cf.reeds_path, cf.sc_path, cf.casename, 
        cf.reg_out_col, cf.copy_to_reeds, cf.copy_to_shared, rev_jsons, configpath)
    print('All done! total time: '+ str(datetime.datetime.now() - startTime))
