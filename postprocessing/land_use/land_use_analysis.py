
'''
This script uses the outputs from reeds_to_rev.py to estimate total land use from a ReEDS scenario
for a set of specified reV characterizations.  It is run automatically during a ReEDS
run with `land_use_analysis=1` (`reeds_to_rev` must also be enabled). 

The processing is currently only configured to work for upv and wind-ons.

For more details see the README in the postprocessing/land_use folder.

Author: bsergi
'''

import argparse
import json
import os
import pandas as pd
import site
import sys
import time
import traceback
from collections import OrderedDict
from glob import glob

#######################
# Helper functions 
#######################

# loads information on supply curve columns to process from input json
def loadCategoriesToProcess(reeds_path, jsonfilename="process_categories"):
    configpath = os.path.join(reeds_path, "postprocessing", "land_use", "inputs", f"{jsonfilename}.json")

    with open(configpath, "r") as f:
        json_data = json.load(f, object_pairs_hook=OrderedDict)
    return json_data

# calculates total land area required
def totalLand(scen_path, tech_land_use, total_area, tech, capacity_col):

    print("...processing total land use.")

    # check whether each supply curve point is full (within tolerance of 0.1 MW)
    tech_land_use['sc_full_bool'] = (abs(tech_land_use[capacity_col] - tech_land_use['built_capacity']) < 0.1)
    tech_land_use['fraction_built'] =  tech_land_use['built_capacity'] / tech_land_use[capacity_col]
    tech_land_use['built_area_sq_km'] = tech_land_use['area_developable_sq_km'] * tech_land_use['fraction_built']

    # calculate total area
    tech_land_use['built_capacity_mw'] = tech_land_use['built_capacity']
    tech_area = tech_land_use.groupby(['year'])[["built_capacity_mw", "built_area_sq_km"]].sum()

    # current total is area available for development, not total non-excluded area
    # does not currently use multiple years of land-use data
    tech_area['avail_area_sq_km'] = total_area

    # save output
    tech_area.to_csv(os.path.join(scen_path, "outputs", f"land_use_{tech}.csv"), float_format='%.6f')

# calculates capacity deployed by land use category
# assumes for now that capacity is evenly distributed by land-use type,
# but in the future we will want to revisit this assumption.
def calculateCapacityByUse(df, tag):

    # NAs indicate no cells or builds in that supply curve point
    # df = df.fillna(0)
    df['built_capacity_mw'] = df['built_capacity_mw'].fillna(0)
    df['fraction_built'] = df['fraction_built'].fillna(0)

    frac_column = "fraction_sc_area"
    # this is the fraction of the land use category to the total supply curve
    df[frac_column] =  df['area_sq_km_land_use'] / df['area_developable_sq_km'] 
    
    # amount of capacity built in each land class is (total capacity built in sc_point) x (share of land use / total sc point)
    df[tag + '_built_capacity_mw'] = df[frac_column] *  df['built_capacity_mw']

    # area used is a function of the fraction of total sc curve area used
    df[tag + '_area_built_sq_km'] = df[frac_column] *  df['area_developable_sq_km'] * df['fraction_built']

    # drop fraction column
    df.drop(frac_column, axis=1, inplace=True)
    return df


# helper function to parse any columns with JSON data
def parseJSON(df, col, var, reeds_path, mapping=None, 
              keepcols=["sc_point_gid", "latitude", "longitude", "cnty_fips", "area_developable_sq_km"]):

    # select data based on column (can be a regular expression for multiple columns)
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

    # drop any columns named '0'; these are actually areas outside the U.S. that get
    # captured as excluded for sc_points on the border with Canada or Mexico.
    out = out.drop([0, '0'] , axis=1, errors='ignore')

    # NAs are zeros
    out.fillna(0, inplace=True)
    
    # convert to cell count to area 
    # assumes each cell is 90x90 m and converts to sq km
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
    out[var] = out[var].astype('float').astype('int')

    # identify codes in the data
    codes_to_map = list(out[var].unique())
    codes_to_map.sort()
    print(f"Land use codes identified: {codes_to_map}")

    # add mapping details (files found in ReEDS postprocessing module)
    if mapping is not None:
        try:
            df_map = pd.read_csv(os.path.join(reeds_path, "postprocessing", "land_use", "inputs", mapping + ".csv"))
        except:
            print("Error: could not read specified mapping file. Check file path:"
                  f"{os.path.join(reeds_path, 'postprocessing', 'land_use', 'inputs', mapping + '.csv')}"
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
def processLandUseJSON(df_name, tech, df_vals, scen_path, reeds_path, rev_sc, tech_land_use=None, area_only=False):

    print("...processing %s classification." % df_name)

    # get land classifications
    land_class = parseJSON(rev_sc, df_vals["colname"], df_vals["newcolname"], reeds_path, mapping=df_vals["mapping"])

    # if only running to get area (no capacity buildouts), save results and end here
    if area_only:
        land_class = land_class.assign(cnty_fips='p'+land_class.cnty_fips.astype(str).map('{:>05}'.format))

        print(f"Writing outputs to {os.path.join(os.path.dirname(scen_path), f'area_{df_name}.csv.gz')}")
        land_class.to_csv(os.path.join(
            os.path.dirname(scen_path), f"area_{df_name}.csv.gz" 
            ), float_format='%.6f', index=False)
    
    else:
        # select data based on column (can be a regular expression for multiple columns)
        # expand landjsondata classification to match 
    
        # build years to focus on for results
        land_class_merge = expandYears(land_class, tech_land_use)
        tech_land_use_merge = tech_land_use.loc[tech_land_use.year.isin(land_class_merge.year.unique())]

        # merge buildout with land use categories
        # use outer join to include available land from areas with no capacity
        land_use = land_class_merge.merge(tech_land_use_merge[['year', 'sc_point_gid', 'built_capacity_mw', 'fraction_built']], on=["sc_point_gid", "year"], how="outer")    

        # allocate capacity to each land use category    
        land_use = calculateCapacityByUse(land_use, df_name)

        # rename some columns
        land_use.rename(columns={'area_sq_km_land_use': f'{df_name}_area_avail_sq_km',
                                 'area_developable_sq_km': 'sc_area_avail_sq_km',
                                 'built_capacity_mw': 'sc_built_capacity_mw',
                                 'fraction_built': 'sc_fraction_built'}, inplace=True)
        
        # preserve leading zero in fips code
        land_use = land_use.assign(cnty_fips='p'+land_use.cnty_fips.astype(str).map('{:>05}'.format))

        # reorder columns
        allcols = land_use.columns
        sccols = [col for col in allcols if 'sc_' in col] + ['latitude', 'longitude', 'cnty_fips', 'year']
        landcols = [col for col in allcols if col not in sccols]
        land_use = land_use[sccols + landcols]
    
        # save outputs    
        print(f"Writing outputs to {os.path.join(scen_path, 'outputs', f'land_use_{tech}_{df_name}.csv.gz')}")
        land_use.to_csv(os.path.join(
            scen_path, "outputs", f"land_use_{tech}_{df_name}.csv.gz"
            ), float_format='%.6f', index=False)

# expand land-use mapping for all ReEDS years
def expandYears(land_mapping, reeds_results, yearsub='firstlast'):
    df_out = pd.DataFrame()
    years_all = reeds_results['year'].unique().tolist()
    if yearsub == 'firstlast':
        firstyear = max(y for y in [years_all[0], 2020, 2021, 2022, 2023, 2024] if y in years_all)
        #firstyear = 2020
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
# unlike other land use categories (which have the number of cells by category stored in a json file),
# these columns include just one number that reflects the number of cells in the category
def getSpeciesImpact(tech, scen_path, rev_sc, tech_land_use, species_col_list):
    
    print("...processing species habitat and range information.")
    species_cols = []
    for species_col in species_col_list['colname']:
        species_cols.extend([col for col in rev_sc.columns if species_col in col ])

    if len(species_cols) == 0:
        print("No species columns found that contain specified substrings; "
              "check colname values in process_categories.json against available supply curve columns")
        print(f"List of available columns: {rev_sc.columns}")
    else:
        print(f"Found the following species colums: {species_cols}")
    
    id_cols = ['year','region','sc_point_gid','sc_full_bool','fraction_built','area_developable_sq_km','built_area_sq_km','built_capacity_mw']
    species_land_use = tech_land_use[id_cols]

    # using left join here for now but may want to revise to capture species habitat/range outside of built areas
    species_land_use = pd.merge(species_land_use, rev_sc[['sc_point_gid'] + species_cols], on='sc_point_gid', how='left')
    
    # melt to long
    species_land_use = pd.melt(species_land_use, id_vars=id_cols, 
        value_vars=species_cols, var_name="species_var", value_name="species_var_cells")

    # categorize by species and impact type
    # only works for certain formats for reV so needs some modifications before folding into main workflow
    # species_land_use['species_extent'] = species_land_use['species'].str.replace(".*_", "", regex=True)
    # species_land_use['species'] = species_land_use['species'].str.replace("_.*", "", regex=True)

    # calculate area for species variable
    # assumes each cell is 90x90 m and converts to sq km
    cell_area = 90*90 / 1E6 
    species_land_use['species_area_sq_km'] = species_land_use['species_var_cells'] * cell_area

    # calculate density as a fraction of developable area (consider converting calculation to total area in sc point)
    #species_land_use['species_density'] = species_land_use['species_area'] / species_land_use['area_developable_sq_km']

    species_land_use.rename(columns={
                                 'area_developable_sq_km': 'sc_area_avail_sq_km',
                                 'built_area_sq_km': 'sc_built_area_sq_km',
                                 'built_capacity_mw': 'sc_built_capacity_mw'
                                }, inplace=True)
    
    species_land_use.drop("species_var_cells", axis=1, inplace=True)

    # save outputs
    species_land_use.to_csv(os.path.join(scen_path, "outputs", f"land_use_{tech}_species.csv.gz"), float_format='%.6f', index=False)

# primary process function called by main loop for each tech
def getLandUse(scen_path, jsonfile, rev_paths, reeds_path, tech, capacity_col="capacity_mw_ac"):

    scenario = os.path.basename(scen_path)
    print("Getting %s land-use data for %s" % (tech, scenario))

    # select rev case for tech being processed
    rev_paths = rev_paths.loc[rev_paths.tech == tech].squeeze()

    # first attempt for supply curve should be the specified rev sc file for the run
    sc_file = rev_paths.sc_file
    try:
        rev_sc = pd.read_csv(sc_file)
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
            rev_sc = pd.read_csv(map_file)
        except:
            sys.exit("Error reading rev mapping file. Check that appropriate file is in the rev folder.")
    # load ouputs from reeds_to_rev.py script
    try:
        builds_tech = pd.read_csv(os.path.join(scen_path, "outputs", f"df_sc_out_{tech}_reduced.csv"))
    except:
        sys.exit(f"Error reading df_sc_out_{tech}_reduced.csv file; check that reeds_to_rev.py ran successuflly.")

    # if using land-use features that change over time then merge on year, otherwise ignore year
    tech_land_use = builds_tech[['year','region','sc_point_gid','built_capacity']].merge(
        rev_sc[['sc_point_gid', 'area_developable_sq_km', capacity_col]], on=['sc_point_gid']
        )
    
    # estimate of total developable area from reV
    total_area = rev_sc['area_developable_sq_km'].sum()
    # calculate total built area
    totalLand(scen_path, tech_land_use, total_area, tech, capacity_col)
    
    # load supply curve categories to process
    json_data = loadCategoriesToProcess(reeds_path, jsonfile)
    
    # iterate over list of categories to process from input json file
    for df_name in json_data:    
        st = time.time()
        try:
            # species-like reV columns get special treatment
            if df_name == "species":
                getSpeciesImpact(tech, scen_path, rev_sc, tech_land_use, json_data[df_name])
            # all other columns are assumed to have json information with the number of cells by land category
            else:
                processLandUseJSON(df_name, tech, json_data[df_name], scen_path, reeds_path, rev_sc, tech_land_use)
        except Exception as err:
            print(f"Error processing {df_name}")
            print(err)
            print("\n skipping to next item for processing.")
        et = time.time()
        print("(elapsed time: %0.2f seconds)" % (et - st))

#######################
# Main 
#######################
        
# function to bypass ReEDS results and just summarize area for a supply curve
def summarizeSupplyCurve(scpath, reeds_path, jsonfile, techs):
    print("\nSummarizing supply curves via 'land_use_analysis.py' script.\n")

    # read in sc data
    rev_sc = pd.read_csv(scpath)

    # load supply curve categories to process
    json_data = loadCategoriesToProcess(reeds_path, jsonfile)

    for df_name in json_data:    
        st = time.time()
        for tech in techs:
            try:
                processLandUseJSON(df_name, tech, json_data[df_name], scpath, reeds_path, rev_sc, area_only=True)
            except Exception:
                print(f"Error processing {df_name}")
                #print(err)
                print(traceback.format_exc())
                print("\n skipping to next item for processing.")
        et = time.time()
        print("(elapsed time: %0.2f seconds)" % (et - st))
    
def runLandUse(scen_path, reeds_path, jsonfile, techs):
    print("\nRunning 'land_use_analysis.py' script.\n")

    # dictionary of capacity colum to use by tech (depends on reV format)
    capacity_cols = {'upv': 'capacity_mw_ac', 'wind-ons':'capacity_mw'}
    
    try:
        # get path to relevant rev files and switch settings 
        rev_paths = pd.read_csv(
            os.path.join(scen_path, "inputs_case", "rev_paths.csv")
            )
    except FileNotFoundError:
        sys.exit(f"Could not read {os.path.join(scen_path, 'inputs_case', 'rev_paths.csv')}")
    
    # run land use analysis for each tech
    for tech in techs:
        try:
            getLandUse(scen_path, jsonfile, rev_paths, reeds_path, tech, capacity_cols[tech])
        except Exception as err:
            print(err)
    
    print("\nCompleted 'land_use_analysis.py' script.")

if __name__ == '__main__':
    
    # Argument inputs
    parser = argparse.ArgumentParser(description="""This script calculates evaluates land-use implications for 
                                                    solar buildouts from one or more ReEDS runs. 
                                                    Requires the 'reeds_to_rev.py' to have been run.""")
    parser.add_argument("scenario", help="Folder of ReEDS run (or path to sc file if running with 'area_only' equal to True")
    parser.add_argument('--area_only', '-a', action="store_true",
                        help="Only estimate supply-curve area (no ReEDS build)")
    parser.add_argument('--debug', '-d', action="store_true",
                        help="Turn off log for debugging")
    parser.add_argument('--json', '-j', type=str, default='process_categories',
                        help='Name of json file that sets which land use categories to process')
    parser.add_argument('--tech', '-t', type=str, default='all', 
                    choices=['upv', 'wind-ons', 'all'], help='techs to process')
    
    args = parser.parse_args()
    
    thispath = os.path.dirname(os.path.realpath(__file__))
    reeds_path = os.path.abspath(os.path.join(thispath, "..",  ".."))

    # Set up logger
    if args.debug:
        print("In debug mode, skipping logging")
    else:
        site.addsitedir(reeds_path)
        from reeds.log import makelog
        makelog(scriptname=__file__, logpath=os.path.join(args.scenario,'gamslog.txt'))

    # convert techs to list
    if args.tech == "all":
        techs = ['upv', 'wind-ons']
    else:
        techs = [args.tech]

    if args.area_only:
        summarizeSupplyCurve(args.scenario, reeds_path, args.json, techs)
    else:
        runLandUse(args.scenario, reeds_path, args.json, techs)
