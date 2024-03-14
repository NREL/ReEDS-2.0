import pandas as pd

east = pd.read_csv("/scratch/bsergi/ReEDS-2.0/postprocessing/land_use/results/20231127_landuse/BAU_east_a1b_land_use_nlcd.csv.gz")
west = pd.read_csv("/scratch/bsergi/ReEDS-2.0/postprocessing/land_use/results/20231127_landuse/BAU_west_a1b_land_use_nlcd.csv.gz")
ercot = pd.read_csv("/scratch/bsergi/ReEDS-2.0/postprocessing/land_use/results/20231127_landuse/BAU_ercot_a1b_land_use_nlcd.csv.gz")

breakpoint()

land_use = pd.concat([east,west,ercot])

test = land_use.loc[land_use.year == 2050].groupby(['nlcd_class']).agg({"nlcd_area_sq_km":sum, "nlcd_built_capacity_MW": sum})

#['nlcd_area_sq_km', 'nlcd_built_capacity_MW', 'nlcd_area_sq_km_built'].sum()


