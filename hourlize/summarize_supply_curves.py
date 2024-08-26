from run_hourlize import get_remote_path 
import argparse
import datetime
import os
import pandas as pd
import site
import sys

def load_raw_supply_curves(rev_paths):
    sc_files = []
    for i, rp in rev_paths.iterrows():
        print(f"Loading {rp['tech']}_{rp['access_case']} from {rp['sc_folder']}")
        sc_in = pd.read_csv(rp.sc_file)
        # for older vintages map columns to new names
        new_col_names = {
            "mean_cf_ac": "capacity_factor_ac",
            "capacity_mw_ac": "capacity_ac_mw",
            "capacity_mw_dc": "capacity_dc_mw",
            "area_sq_km": "area_developable_sq_km",
            "eos_mult":	"multiplier_cc_eos",
            "reg_mult":	"multiplier_cc_regional",
            "land_cap_adder_per_mw": "land_cap_adder_per_mw",
            "tie_line_cost_per_mw": "cost_spur_usd_per_mw",
            "trans_cap_cost_per_mw": "cost_spur_usd_per_mw",
            "reinforcement_cost_per_mw_ac": "cost_reinforcement_usd_per_mw",
            "capital_adder_per_MW": "capital_adder_per_mw",
            "trans_adder_per_MW": "trans_adder_per_mw",
            "supply_curve_cost_per_MW": "supply_curve_cost_per_mw",
            "total_lcoe": "lcoe_all_in_usd_per_mwh",
        }

        # don't rename thse for upv or else you'll end up with duplicate columns
        if (rp['tech'] != "upv") and ('capacity_ac_mw' not in sc_in.columns):
            new_col_names.update({"capacity": "capacity_ac_mw"})
        if (rp['tech'] != "upv") and ('capacity_factor_ac' not in sc_in.columns):
            new_col_names.update({"mean_cf": "capacity_factor_ac"})

        # only add this one if the ac cost isn't already present
        if ("reinforcement_cost_per_mw" in sc_in.columns) and ("reinforcement_cost_per_mw_ac" not in sc_in.columns):
            new_col_names.update({"reinforcement_cost_per_mw": "cost_reinforcement_usd_per_mw"})
        sc_in = sc_in.rename(columns=new_col_names)
        # add new columns with sc details
        for col in ['tech', 'sc_folder', 'access_case']:
            sc_in[col] = rp[col]

        # only keep select sc columns (these + new col names)
        # add more to list as needed
        keepcols = ['tech', 'sc_folder', 'access_case', 'sc_point_gid', 
                    'cnty_fips', 'latitude', 'longitude'
                    ] + list(set([new_col_names[col] for col in new_col_names]))
        # drop any columns that aren't in the supply curve
        missingcols = [col for col in keepcols if col not in sc_in.columns ]
        if len(missingcols):
            print(f"--> could not find the following columns: {missingcols}")
        keepcols = [col for col in keepcols if col not in missingcols]
        sc_in = sc_in[keepcols]

        # check for duplicate columns
        if sum(sc_in.columns.duplicated()):
            dupes = sc_in.columns[sc_in.columns.duplicated()]
            print(f"--> ERROR: the following columns are duplicated: {dupes}.")
            sys.exit(1)

        # add to list
        sc_files.append(sc_in)

    # create data frame
    sc_data = pd.concat(sc_files)
    return sc_data

if __name__== '__main__':
    ## Command line arguments to script
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description='Summarize reV supply curves.')
    parser.add_argument('--techs', '-t', nargs='+', default=['upv', 'wind-ofs', 'wind-ons'],
                        help='''Techs to summarize. Default runs upv, wind-ofs, and wind-ons''')
    parser.add_argument('--rev_paths', '-r', nargs='+', default=['default'],
                        help='''List of rev_paths files to evaluate. Enter 'default' to
                                include the rev_paths file in your current repo.''')
    #parser.add_argument('--county', '-c', default=False, action='store_true',,
    #                    help='''Summarize county supply curves''')

    args = parser.parse_args()
    rev_paths_files = args.rev_paths
    techs = args.techs
    # only summarize ba supply curves for now
    resolution = {'GSw_RegionResolution': 'ba'}

    ## set paths
    hourlize_path = os.path.dirname(os.path.realpath(__file__))
    reeds_path = os.path.abspath(os.path.join(hourlize_path, ".."))
    remotepath, _  = get_remote_path(local=False)
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    site.addsitedir(os.path.join(reeds_path))
    import runbatch as rb

    ## read list of rev_path files
    rev_paths = []
    for rp in rev_paths_files:
        if rp.lower() == 'default':
            rp = os.path.join(reeds_path, 'inputs', 'supply_curve', 'rev_paths.csv')
        if not os.path.exists(rp):
            print(f"{rp} is not a valid path, please re-specify")
            sys.exit(1)
        else:
            rev_path = pd.read_csv(rp)
            rev_path = rb.get_rev_paths(rev_path, resolution)
            # subset to base name for sc_path
            rev_path['sc_folder'] = rev_path['sc_path'].apply(lambda row: os.path.basename(row))
            # subset to relevant columns and techs
            rev_path = rev_path[['tech', 'sc_folder', 'access_case', 'rev_case', 'sc_file']]
            rev_path = rev_path.loc[rev_path.tech.isin(techs)]
            rev_paths.append(rev_path)
    rev_paths = pd.concat(rev_paths).drop_duplicates().reset_index(drop=True)

    ## read in supply curve data
    sc_data = load_raw_supply_curves(rev_paths)

    ## write it
    if len(techs) == 1:
        file_name = f"{today}_{techs[0]}"
    else:
        file_name = f"{today}"
    sc_data.to_csv(os.path.join(hourlize_path, "out", f"{file_name}_sc_summary.csv"), index=False)

    ## total capacity (MW)
    sc_total_cap = sc_data.groupby(['tech', 'sc_folder', 'access_case'])['capacity_ac_mw'].sum()
    sc_total_cap.to_csv(os.path.join(hourlize_path, "out", f"{file_name}_sc_totals.csv"))

    print("Done")
    