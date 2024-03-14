''''
Script perform preprocessing on rev supply curves and check 
for validity with hourlize

- checks for missing columns and flags as needed
- adds county fips when needed
- summarizes totals


TODO:
- create new column named 'capital_cost' equal to 'mean_capital_cost'
- include land_use adder (add to this script)
- add columns for 'eos_mult' and 'reg_mult' with both equal to 1
- rename 'trans_cap_cost_per_mw' and 'reinforcement_cost_per_mw' to inlude "_ac" suffix (or adjust treatment in resource.py)

'''

import os
import sys
import pandas as pd
import geopandas as gpd
import shapely

# TODO: add more columns to check
HOURLIZE_COLS = {
                "all": ["cnty_fips", "sc_point_gid", "capital_cost", 
                        "eos_mult", "reg_mult", "land_cap_adder_per_mw"],
                "upv": ["capacity_mw_dc", "capacity_mw_ac", 
                        "reinforcement_cost_per_mw_ac", "trans_cap_cost_per_mw_ac"],
                "wind-ons": ["capacity_mw"],
                }

## Functions ####

# figure out lat/lon columns
def get_latlonlabels(dfin, latlonlabels=None, columns=None):
    if latlonlabels is not None:
        latlabel, lonlabel = latlonlabels[0], latlonlabels[1]
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
    
    return latlabel, lonlabel

# convert pandas to geopandas
def df2gdf(dfin, crs='ESRI:102008'):
    os.environ['PROJ_NETWORK'] = 'OFF'

    ### Convert
    df = dfin.copy()
    latlabel, lonlabel = get_latlonlabels(df)
    df['geometry'] = df.apply(
        lambda row: shapely.geometry.Point(row[lonlabel], row[latlabel]), axis=1)
    df = gpd.GeoDataFrame(df, crs='EPSG:4326').to_crs(crs)

    return df

# load rev supply curve file
def load_sc_df(row, remotepath):
    # read from rev file path
    sc = pd.read_csv(os.path.join(remotepath, row['sc_file']))
    return sc

# check for columns need for hourlize
def check_cols(row, sc):
    cols_to_check = HOURLIZE_COLS["all"] + HOURLIZE_COLS[row['tech']]
    missing = [c for c in cols_to_check if c not in sc.columns]
    return missing

# if missing cnty_fips column, match to counties manually
def match_to_counties(sc, cnty_shp):
    
    # convert sc to geopandas (helpful to reduce dimensions)
    sc_sub = sc[['sc_point_gid', 'state', 'latitude', 'longitude']].copy()
    sc_sub = df2gdf(sc_sub, crs=cnty_shp.crs)

    # spatial join to match with counties (matches if lat/lon are within polygon)
    sc_matched = gpd.sjoin(sc_sub, cnty_shp, how="left").drop("index_right", axis=1)

    # the above match gets most sc points but some are unmatched, likey because they are on
    # a polygon border. for those we perform a second join to the nearest area
    # only uses this second method for unmatched points since it is signifcally slower than sjoin
    sc_unmatched = sc_matched.loc[sc_matched.rb.isna(), sc_sub.columns]
    # for this matched we need distances, so use the ESRI projection
    sc_unmatched = gpd.sjoin_nearest(
        sc_unmatched.to_crs('ESRI:102008'), cnty_shp.to_crs('ESRI:102008'), how="left"
        ).drop("index_right", axis=1).to_crs(sc_matched.crs)
    
    sc_out = pd.concat([sc_matched[~sc_matched.rb.isna()], sc_unmatched])

    # remerge into original sc 
    sc_out = sc_out[['sc_point_gid','state','FIPS','NAME']].rename(columns={"FIPS":"cnty_fips", "NAME":"county"})
    sc_final = sc.merge(sc_out, on=["sc_point_gid", "state"], how="outer", suffixes=('_old', ''))

    ## some checks on the results
    
    # drop updated columns
    drop_cols = [c for c in sc_final.columns if "old" in c]
    print(f"Dropping the following columns: {drop_cols}")
    sc_final.drop(drop_cols, axis=1, inplace=True)

    # track new columns
    new_cols = [c for c in sc_final.columns if c not in sc.columns]
    print(f"Added the following columns: {new_cols}")

    # check for missing columns
    missing_cols = [c for c in sc.columns if c not in sc_final.columns]
    if len(missing_cols) > 0:
        print("Caution: the following columns from the original supply curve"
              f" are missing in the updated: {drop_cols}"
              )
        
    # make sure all points were matched
    if sc_final.cnty_fips.isna().sum() > 0:
        print("Error: some county fips code are missing; check matching")
    if sc.shape[0] != sc_final.shape[0]:
        print("Error: final supply curve has a different number of rows; check matching")
    
    return sc_final 


# function to add capital cost
def add_land_fom(tech, df_in):
 
    # lease component of FO&M from ATB ($/kW-yr)
    lease_fom = {'upv': 2.1, 'wind-ons': 4.2}
    # long term CRF from recent ReEDS (March 2023)
    crf = 0.06866

    # read in updated fair market values from Antony 
    fmv = pd.read_csv(os.path.join(hourlizepath, "inputs", "resource", "fair_market_value.csv"))

    # get median land cost
    fmv_med = fmv.places_fmv_all_rev.median()

    # drop pre-existing land value column -- any original data was in ln scale
    # but not corrected (Note: reV plans to correct this eventually, so may not
    # need to continue after 2023)
    #df = df_in.drop(['places_fmv_all_rev', 'land_cap_adder_per_mw'],axis=1)
    df = df_in.drop(['places_fmv_all_rev'],axis=1)

    # drop any index columns
    df.drop(df.columns[df.columns.str.contains('Unnamed')], axis=1, inplace=True)

    # merge in updated land costs
    df = df.merge(fmv[['sc_point_gid','places_fmv_all_rev']], on='sc_point_gid', how='left' )

    # calculate land cost adder ($/MW)
    #Cap_Adder = (LC-LC_med)/LC_med*FOM_med/CRF
    # Difference in normalized land cost * median FO&M cost 
    # convert FO&M cost from $/kW-yr to $/MW for 20 year lifetime, then convert to lump payment with CRF 
    # note: PV originally in units of $/kW-DC
    df['land_cap_adder_per_mw'] = (df['places_fmv_all_rev'] - fmv_med)/fmv_med * (lease_fom[tech] * 1e3 / crf )

    # check number of rows is the same 
    assert df.shape[0] == df_in.shape[0], 'Updated data does not have the same number of rows as incoming data'

    return df

def fill_missing_cols(row, sc, missing_cols, cnty_shp):
    rename_cols = {
                    'capital_cost' : 'mean_capital_cost',
                    'capacity_mw' : 'capacity',
                    'capacity_mw_ac' : 'capacity_ac',
                    'capacity_mw_dc' : 'capacity',
                    'trans_cap_cost_per_mw_ac' : 'trans_cap_cost_per_mw',
                    'reinforcement_cost_per_mw_ac' : 'reinforcement_cost_per_mw'
                   }

    sc_new = sc.copy()
    for col in missing_cols:
        print(f"...updated {col}")
        # if missing cnty_fips match to shapefile
        if col == 'cnty_fips':
            sc_new = match_to_counties(sc_new, cnty_shp)
        # if missing these just set to 1
        elif col in ['eos_mult', 'reg_mult']:
            sc_new[col] = 1
        # if missing one of the 'rename' columns then just need to rename 
        elif col in rename_cols:
            sc_new.rename(columns={rename_cols[col]:col}, inplace=True)
        elif col == 'land_cap_adder_per_mw':
            sc_new = add_land_fom(row['tech'], sc_new)
        else:
            raise Exception(f"No method defined for filling in {col}.")
        
    return sc_new
    
## Procedure ####
if __name__== '__main__':

    hourlizepath = os.path.dirname(os.path.realpath(__file__)) 
    reedspath = os.path.normpath(os.path.join(hourlizepath, '..'))

    # option to save new sc in a separate post-processed folder 
    # note: if this script has already been run and the rev_paths file updated to 
    # match this folder, then the post processed version will be overwritten
    post_processed_folder = "post_processed_supply_curves"

    # get remotepath
    hpc = True if ('NREL_CLUSTER' in os.environ) else False
    if hpc:
        #For running hourlize on the HPC link to shared-projects folder
        if os.environ.get('NREL_CLUSTER') == 'kestrel':
            remotepath = '/projects/shared-projects-reeds/reeds/Supply_Curve_Data'
        else: 
            remotepath = '/shared-projects/reeds/Supply_Curve_Data' 
    else:
        #If not on the hpc running link to nrelnas01
        remotepath = ('Volumes' if sys.platform == 'darwin' else '/nrelnas01') + '/ReEDS/Supply_Curve_Data'

    # load rev paths
    rev_paths = pd.read_csv(
        os.path.join(reedspath, "inputs", "supplycurvedata", "metadata", "rev_paths.csv")
        )
    
    # TODO: set this up as an argument
    cases = [
            #  ('upv', 'reference_nlcd'),
            #  ('upv', 'reference_a1b'),
            #  ('upv', 'reference_a2'),
            #  ('upv', 'reference_b1'),
            #  ('upv', 'reference_b2'),
             ('wind-ons', 'reference_nlcd'),
             ('wind-ons', 'reference_a1b'),
             ('wind-ons', 'reference_a2'),
             ('wind-ons', 'reference_b1'),
             ('wind-ons', 'reference_b2')
             ]
    
    # for testing
    # cases = [('upv', 'reference_nlcd')]
    
    # subset to relevant rows
    rev_paths_sub = rev_paths[(rev_paths[['tech','access_case']].values[:,None] == cases).all(2).any(1)]

    # load county shapefile
    cnty_shapefile = os.path.join(reedspath, "inputs", "shapefiles", "US_COUNTY_2022")
    # for lat/lon matching it is better to have a geographic CRS as opposed to a projected on
    crs_out = "EPSG:4326"
    cnty_shp = gpd.read_file(cnty_shapefile).to_crs(crs_out)

    print("\nRunning reV supply curve checks and pre-processing")

    # iterate over rev paths of interest
    for i,row in rev_paths_sub.iterrows():

        print(f"\nProcessing {row['tech']} {row['access_case']}")
        # read in supply curve
        sc = load_sc_df(row, remotepath)

        # check for missing columns
        missing_cols = check_cols(row, sc)
        if len(missing_cols) > 0:
            print(f"Identified the following missing columns: {missing_cols}")
            sc_new = fill_missing_cols(row, sc, missing_cols, cnty_shp)
        else:
            print("No missing columns detected")
            sc_new = sc.copy()
        
        # rewrite updated sc (if necessary)
        outpath = os.path.join(remotepath, row['sc_path'], 'reV', post_processed_folder)

        if not os.path.exists(outpath):
            os.makedirs(outpath, exist_ok=True)
        filename = os.path.basename(row['sc_file'])
        sc_new.to_csv(os.path.join(outpath, filename), index=False)

        print(f"Updated sc file {filename} save to {outpath}")
        
        print(f"Completed processing {row['tech']} {row['access_case']}")


