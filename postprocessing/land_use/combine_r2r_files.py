import pandas as pd
from glob import glob
import os

r2rfolder = "/scratch/bsergi/ReEDS-2.0/runs/landuse_results/r2r_data"
outfolder = "/scratch/bsergi/ReEDS-2.0/runs/landuse_results/r2r_combined"

cases = os.listdir(r2rfolder)

scenarios = ["BAU", "High_Solar"]
regions = ["east", "west", "ercot"]
land_use = ["nlcd", "a1b", "a2", "b1", "b2"]
techs = ["upv", "wind-ofs", "wind-ons"]

for scen in scenarios:
    for lu in land_use:
        for tech in techs:
            print(f"Processing {scen}_{lu}")
            file = f"df_sc_out_{tech}_reduced.csv"
            # read each file from each region
            df_combined = []
            for reg in regions:
                try:
                    df = pd.read_csv(os.path.join(r2rfolder, f"{scen}_{reg}_{lu}", file))
                    df_combined.append(df)
                except:
                    print(f"...could not read {os.path.join(f'{scen}_{reg}_{lu}', file)}, skipping")
            df_out = pd.concat(df_combined)
            # write combined file out
            df_out = df_out.sort_values(['year','sc_point_gid'])            
            df_out.to_csv(os.path.join(outfolder, f"{scen}_{lu}_{tech}_buildout.csv"))

print("Done processing r2r files")
