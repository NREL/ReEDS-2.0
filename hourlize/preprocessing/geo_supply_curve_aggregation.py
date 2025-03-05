import pandas as pd
import os

def aggregate_by_lowest_lcoe_depth(sc_list):
    df_sc_agg = pd.concat(sc_list)
    df_sc_lowest_lcoe = (
        df_sc_agg.sort_values(["lcoe_all_in_usd_per_mwh", "lcoe_site_usd_per_mwh"], ascending=True)
        .groupby(["sc_point_gid"], as_index=False)
        .first()
        .reset_index(drop=True)
    )
    return df_sc_lowest_lcoe

def process_raw_supply_curves(rev_cases_path, rev_sc_file_path):
    raw_sc_files = os.path.join(rev_cases_path, "raw_supply_curves")

    sc_list = []
    for _, _, files in os.walk(raw_sc_files):
            for file in files:
                sc_list.append(pd.read_csv(os.path.join(raw_sc_files, file)))
    
    sc_agg = aggregate_by_lowest_lcoe_depth(sc_list)
    sc_agg.to_csv(rev_sc_file_path)