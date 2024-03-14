
'''
This script takes uses the outputs from reeds_to_rev.py to evaluate
land-use impacts for a ReEDS scenario. It is run automatically during a ReEDS
run when the `reeds_to_rev` switch is enabled. 

The processing is currently only configured to work for UPV, but will
hopefully be expanded to work for other technologies in the future. 

Note that land-use fields must be processed as part of the rev run to be analyzed here.

Passed arguments: 
    - path to ReEDS scenario 

Other input data:
    - rev supply curve aggreation file that contains land-use charactistics
    - mapping files for relevant land use categories (see /postprocessing/land_use/inputs)

Outputs:
    - land_use_[category].csv: saved to the output folder of the ReEDS runs.
'''

import os
import sys
import pandas as pd
import argparse
import time
import site
from glob import glob
import json
from collections import OrderedDict

#######################
# Helper functions 
#######################

# calculates total land area required
def totalLand(scen_path, upv_land_use, total_area, capacity_col):

    print("...processing total land use.")

    # check whether each supply curve point is full (within tolerance of 0.1 MW)
    upv_land_use['sc_full_bool'] = (abs(upv_land_use[capacity_col] - upv_land_use['built_capacity']) < 0.1)
    upv_land_use['fraction_built'] =  upv_land_use['built_capacity'] / upv_land_use[capacity_col]
    upv_land_use['built_area_sq_km'] = upv_land_use['area_sq_km'] * upv_land_use['fraction_built']

    # calculate total area
    upv_land_use['built_capacity_MW'] = upv_land_use['built_capacity']
    upv_area = upv_land_use.groupby(['year'])[["built_capacity_MW", "built_area_sq_km"]].sum()

    # current total is area available for development, not total non-excluded area
    # does not currently use multiple years of land-use data
    upv_area['avail_area_sq_km'] = total_area

    # save output
    upv_area.to_csv(os.path.join(scen_path, "outputs", "land_use_upv.csv"), float_format='%.2f')

# calculates capacity deployed by land use category
# assumes for now that capacity is evenly distributed by land-use type,
# but in the future we will want to revisit this assumption.
def calculateCapacityByUse(df, tag):

    # NAs indicate no cells or builds in that supply curve point
    # df = df.fillna(0)
    df['built_capacity_MW'] = df['built_capacity_MW'].fillna(0)
    df['fraction_built'] = df['fraction_built'].fillna(0)

    frac_column = "fraction_sc_area"
    # this is the fraction of the land use category to the total supply curve
    df[frac_column] =  df['area_sq_km_land_use'] / df['area_sq_km'] 
    
    # amount of capacity built in each land class is (total capacity built in sc_point) x (share of land use / total sc point)
    df[tag + '_built_capacity_MW'] = df[frac_column] *  df['built_capacity_MW']

    # area used is a function of the fraction of total sc curve area used
    df[tag + '_area_sq_km_built'] = df[frac_column] *  df['area_sq_km'] * df['fraction_built']

    # drop fraction column
    df.drop(frac_column, axis=1, inplace=True)
    return df


# helper function to parse any columns with JSON data
def parseJSON(df, col, var, reedspath, mapping=None, 
              keepcols=["sc_point_gid", "latitude", "longitude", "cnty_fips", "area_sq_km"]):

    # select data based on column (can be a regular expression for multiple columns)
    # TODO: test with actual usgs scenario
    jsondata = df.filter(regex=(col))

    # check to make sure there is only 1 column
    if jsondata.shape[1] == 0:
         print("Warning: no columns matched. Check regular expression "
              f"used to select supply curve columns: {col}. "
         )
         print(f"List of available columns: {df.columns}")
         raise Exception("No matching columns")

    elif jsondata.shape[1] > 1:
        print(f"Warning: identified {jsondata.columns} as columns matching the "
              f"supplied regular expression {col}. "
              "Will select the first column to proceed; if that isn't correct "
              "review the column selection expression."
              )
    jsondata = jsondata[jsondata.columns[0]]
    print(f"...column to process: {jsondata.name}")
    
    st = time.time()
    elements = ','.join(jsondata.tolist())
    col_data = json.loads(f"[{elements}]")
    out = pd.DataFrame(col_data)
    et = time.time()
    print("...elapsed time for json.loads function: %0.2f seconds" % (et - st))

    # drop any columns named '0' tagged with 0; these are actually areas outside the U.S. that get
    # captured as excluded for sc_points on the border with Canada or Mexico.
    out = out.drop([0, '0'] , axis=1, errors='ignore')

    # NAs are zeros
    out.fillna(0, inplace=True)
    
    # convert to cell count to area. 
    # assumes each cell is 90x90 m and converts to sq km.
    cell_area = 90*90 / 1E6 
    out = out * cell_area

    # line up sc_point_gid, year, and other info from original mapping data
    dropcols = []
    for kc in keepcols:
        if kc in df.columns:
            out[kc] = df[kc]
        else:
            print(f"...Warning: missing {kc} in the supply curve data so will skip in output.")
            dropcols.append(kc)
    keepcols = [kc for kc in keepcols if kc not in dropcols]
                       
    # melt mapping data to long format
    out = out.melt(id_vars=keepcols, var_name=var, value_name="area_sq_km_land_use")

    # convert codes to integers
    out[var] = out[var].astype('int')

    # identify codes in the data
    codes_to_map = list(out[var].unique())
    codes_to_map.sort()
    print(f"Land use codes identified: {codes_to_map}")

    # add mapping details (files found in ReEDS postprocessing module)
    if mapping is not None:
        try:
            df_map = pd.read_csv(os.path.join(reedspath, "postprocessing", "land_use", "inputs", mapping + ".csv"))
        except:
            print("Error: could not read specified mapping file. Check file path:"
                  f"{os.path.join(reedspath, 'postprocessing', 'land_use', 'inputs', mapping + '.csv')}"
                  )
        try:    
            df_map_subset = df_map.loc[df_map[var].isin(codes_to_map)]
            print("Applying the following mapping: ")
            print(df_map_subset)

            out = out.merge(df_map.drop("color", axis=1, errors="ignore"), how="left", on=var)

            # check for missing values
            missing = [v for v in out[var].unique() if v not in df_map[var].unique()]
            if len(missing) > 0:
                print(f"Warning: missing the following {var} values from mapping file: {missing}\n"
                      "Will be assigned as 'missing'."
                      )        
                new_cols = df_map.drop([var, "color"], axis=1, errors="ignore").columns
                out.update(out[new_cols].fillna('missing'))
        except:
            print(f"Error: merge with mapping file failed. Check column value in file for {var}:")

    return out

# this function processes land-use categories defined by JSONs
def processLandUseJSON(df_name, df_vals, scen_path, reedspath, land_use_map, upv_land_use=None, area_only=False):

    print("...processing %s classification." % df_name)

    # get land classifications
    land_class = parseJSON(land_use_map, df_vals["colname"], df_vals["newcolname"], reedspath, mapping=df_vals["mapping"])

    # if only running to get area (no capacity buildouts), save results and end here
    if area_only:

        land_class = land_class.assign(cnty_fips='p'+land_class.cnty_fips.astype(str).map('{:>05}'.format))

        land_class.to_csv(os.path.join(
        os.path.dirname(scen_path), "area_%s.csv.gz" % df_name
        ), float_format='%.6f', index=False)
    
    else:
        # select data based on column (can be a regular expression for multiple columns)
        # expand landjsondata classification to match 
    
        # build years to focus on for results
        land_class_merge = expandYears(land_class, upv_land_use)
        upv_land_use_merge = upv_land_use.loc[upv_land_use.year.isin(land_class_merge.year.unique())]

        # merge buildout with land use categories
        land_use = land_class_merge.merge(
            upv_land_use_merge[['year', 'sc_point_gid', 'built_capacity_MW', 'fraction_built']], 
            on=["sc_point_gid", "year"], how="outer"
            )    

        # allocate capacity to each land use category    
        land_use = calculateCapacityByUse(land_use, df_name)

        # rename some columns
        land_use.rename(columns={'built_capacity_MW': 'sc_built_capacity_MW',
                                'fraction_built': 'sc_fraction_built'}, inplace=True)
        
        # preserve leading zero in fips code
        land_use = land_use.assign(cnty_fips='p'+land_use.cnty_fips.astype(str).map('{:>05}'.format))

        # save outputs    
        land_use.to_csv(os.path.join(
            scen_path, "outputs", "land_use_%s.csv.gz" % df_name
            ), float_format='%.6f', index=False)

# expand land-use mapping for all ReEDS years
def expandYears(land_mapping, reeds_results, yearsub='firstlast'):
    df_out = pd.DataFrame()
    years_all = reeds_results['year'].unique().tolist()
    if yearsub == 'firstlast':
        #firstyear = max(y for y in [years_all[0], 2020, 2021, 2022, 2023] if y in years_all)
        firstyear = 2020
        years = [firstyear, years_all[-1]]
    elif yearsub == 'all':
        years = years_all
    else:
        print("Years not specified; defaulting to last.")
        years = [years_all[-1]]

    for y in years:
        df = land_mapping.copy()
        df['year'] = y
        df_out = pd.concat([df_out, df])
    return df_out

# process use of land identified as species range/habitat
# TODO: species function needs to be adapted to remove n_gids 
def getSpeciesImpact(scen_path, upv_land_use):
    
    print("...processing species habitat and range information.")
    
    species_cols = [col for col in upv_land_use.columns if 'range' in col or 'habitat' in col]
    id_cols = ['year','region','sc_point_gid','sc_full_bool',
               'n_gids','fraction_built','area_sq_km','built_area_sq_km'
              ]
    species_land_use = upv_land_use[id_cols+ species_cols]
    
    # melt to long
    species_land_use = pd.melt(species_land_use, id_vars=id_cols, 
        value_vars=species_cols, var_name="species", value_name="species_n_gids")

    # categorize by species and impact type
    species_land_use['species_extent'] = species_land_use['species'].str.replace(".*_", "", regex=True)
    species_land_use['species'] = species_land_use['species'].str.replace("_.*", "", regex=True)

    # calculate density
    species_land_use['species_density'] = species_land_use['species_n_gids'] / species_land_use['n_gids']

    # save outputs
    species_land_use.to_csv(os.path.join(scen_path, "outputs", "land_use_species.csv.gz"), float_format='%.2f', index=False)

# primary process function called by main loop for each tech
def getLandUse(scenario, scen_path, rev_paths, reedspath, tech, capacity_col="capacity_mw_ac"):

    print("Getting %s land-use data for %s" % (tech, scenario))
    # select rev case for tech being processed
    rev_paths = rev_paths.loc[rev_paths.tech == tech].squeeze()

    # first attempt should be the specified rev sc file for the run
    sc_file = rev_paths.eagle_sc_file
    try:
        land_use_map = pd.read_csv(sc_file)
    except:
        print("...Warning: failed to read default sc file. Will attempt to read secondary sc file.")
        # for older UPV rev runs land-use data had to be added in a separate file. 
        # newer runs using the 2022 UPV sc will now have this directly in the "aggregation" sc file
        rev_folder = os.path.join(rev_paths.sc_path, "reV", rev_paths.rev_case)
        if "2021_Update" in rev_paths.rev_path:
            map_file = os.path.join(rev_folder, "%s_agg_land_use.csv.gz" % rev_paths.rev_case)
        else:
            # using glob here to catch differences between "-" and "_" in the sc file name
            sc_matches = glob(os.path.join(rev_folder, "**supply*curve*aggregation**"))
            if len(sc_matches) > 1:
                print(f"Multiple sc curve aggregation files detected; using {os.basename(sc_matches[0])}")
            map_file = sc_matches[0]            
        try:
            land_use_map = pd.read_csv(map_file)
        except:
            sys.exit("Error reading rev mapping file. Check that appropriate file is in the rev folder.")
    # load ouputs from reeds_to_rev.py script
    try:
        builds_upv = pd.read_csv(os.path.join(scen_path, "outputs", "df_sc_out_upv_reduced.csv"))
    except:
        sys.exit("Error reading df_sc_out_upv_reduced; check that reeds_to_rev.py ran successuflly.")

    # if using land-use features that change over time then merge on year, otherwise ignore year
    upv_land_use = builds_upv[['year','sc_point_gid','built_capacity']].merge(
        land_use_map[['sc_point_gid', 'area_sq_km', capacity_col]], on=['sc_point_gid']
        )
    
    ## Total land area estimates ####
    # estimate of total developable area 
    total_area = land_use_map['area_sq_km'].sum()
    # calculate total built area
    totalLand(scen_path, upv_land_use, total_area, capacity_col)

    ## Land classifications defined by JSON mappings ####
    # dictionary defines land use categories specified with JSON files
    # format is short name: (name of column in rev mapping, new column name, mapping file for renaming values if any)
    #TODO: this should be an input file
    json_data = {
                #"fed_land": ("fed_land_owner", "fed_land_owner", "federal_land_lookup"), # federal land ownership
                #"nlcd": ("usa_mrlc_nlcd2011", "nlcd_value", "nlcd_categories"),     # national land cover database
                "nlcd": {"colname": "nlcd_2019$", "newcolname":"nlcd_value", "mapping":"nlcd_categories"},
                "usgs": {"colname": "conus_.*_y2050", "newcolname":"usgs_code", "mapping":"usgs_categories"}
                }
    
    for df_name in json_data:    
        st = time.time()
        try:
            processLandUseJSON(df_name, json_data[df_name], scen_path, reedspath, land_use_map, upv_land_use)
        except Exception as err:
            print(f"Error processing {df_name}")
            print(err)
            print("\n skipping to next item for processing.")
        et = time.time()
        print("(elapsed time: %0.2f seconds)" % (et - st))

    ## Species habitat and range ####
    # getSpeciesImpact(scen_path, upv_land_use)


#######################
# Main 
#######################

# function to bypass ReEDS results and just summarize area for a supply curve
def summarizeSupplyCurve(scpath, reedspath, debug=False):
    
    # read in sc data
    land_use_map = pd.read_csv(scpath)

    configpath = os.path.join(reedspath, "postprocessing", "land_use", "inputs", "sc_cols_to_process.json")
    with open(configpath, "r") as f:
        json_data = json.load(f, object_pairs_hook=OrderedDict)

    for df_name in json_data:    
        st = time.time()
        try:
            processLandUseJSON(df_name, json_data[df_name], scpath, reedspath, land_use_map, area_only=True)
        except Exception as err:
            print(f"Error processing {df_name}")
            print(err)
            print("\n skipping to next item for processing.")
        et = time.time()
        print("(elapsed time: %0.2f seconds)" % (et - st))
    
def runLandUse(scen_path, reedspath, debug=False):
    print("\nRunning 'land_use_analysis.py' script.\n")

    scen = os.path.basename(scen_path)

    site.addsitedir(os.path.join(reedspath,'input_processing'))
    from ticker import makelog

    #%% Set up logger
    if debug:
        print("In debug mode, skipping logging")
    else:
        log = makelog(scriptname=__file__, logpath=os.path.join(args.scenario,'gamslog.txt'))
    
    try:
        # get path to relevant rev files and switch settings 
        rev_paths = pd.read_csv(
            os.path.join(scen_path, "inputs_case", "supplycurve_metadata", "rev_supply_curves.csv")
            )

        # eventual plan is to add function calls for other techs (namely wind-ons)
        getLandUse(scen, scen_path, rev_paths, reedspath, tech="upv")
    except Exception as err:
        print(err)
    print("")
    
    print("Completed 'land_use_analysis.py' script.")

if __name__ == '__main__':
    
    # Argument inputs
    parser = argparse.ArgumentParser(description="""This script calculates evaluates land-use implications for 
                                                    solar buildouts from one or more ReEDS runs. 
                                                    Requires the 'reeds_to_rev.py' to have been run.""")
    parser.add_argument("scenario", help="Folder of ReEDS run (or path to sc file if running with 'area_only'")
    parser.add_argument('--debug', '-d', action="store_true",
                        help="Turn off log for debugging")
    parser.add_argument('--area_only', '-a', action="store_true",
                        help="Only estimate supply-curve area (no ReEDS build)")
    args = parser.parse_args()
    
    thispath = os.path.dirname(os.path.realpath(__file__))
    reedspath = os.path.abspath(os.path.join(thispath, "..",  ".."))

    if args.area_only:
        summarizeSupplyCurve(args.scenario, reedspath, args.debug)
    else:
        runLandUse(args.scenario, reedspath, args.debug)

    # debugging 
    # python postprocessing/land_use/land_use_analysis.py /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/runs/2022_03_26_AllOptions_sites
    # python /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/postprocessing/bokehpivot/reports/interface_report_model.py "ReEDS 2.0" /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/runs/2022_03_26_AllOptions_sites all No none /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/postprocessing/bokehpivot/reports/templates/reeds2/land_use.py one /Users/bsergi/Documents/Projects/Solar-siting/ReEDS-2.0/runs/2022_03_26_AllOptions_sites/outputs/reeds-report-land no

# Notes from Travis about land use
# for nlcd use 'nlcd_2019', otherwise use 'conus_<scenario>_<model_year>'

# python /scratch/bsergi/ReEDS-2.0/postprocessing/land_use/land_use_analysis.py /scratch/bsergi/ReEDS-2.0/runs/20231117_landuse_High_Solar_west_a1b
# python /scratch/bsergi/ReEDS-2.0/postprocessing/land_use/land_use_analysis.py /scratch/bsergi/ReEDS-2.0/runs/20231122_landuse_High_Solar_west_nlcd