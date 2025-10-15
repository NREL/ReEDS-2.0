#### This file uses the time zone shapefile from the
#### U.S. Bureau of Transportation Statistics
#### (https://geodata.bts.gov/datasets/usdot::time-zones/)
#### and the ReEDS model regions shapefile of a given ReEDS
#### run to determine the prevailing time zone of each region.

import geopandas as gpd
import sys
import argparse
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import reeds

timezone_abbreviation_map = {
    'Central': 'CT',
    'Eastern': 'ET',
    'Pacific': 'PT',
    'Mountain': 'MT'
}

def main(casedir, reeds_path):
    print("Calculating ReEDS region time zones...")
    dfzones = (
        reeds.io.get_dfmap(casedir, levels=['r'])
        ['r']
        .reset_index()
    )
    tz_map = (
        gpd.read_file(
            os.path.join(reeds_path, "inputs/shapefiles/timezones.gpkg")
        )
        .to_crs(dfzones.crs)
    )
    tz_map['tz'] = tz_map['zone'].map(timezone_abbreviation_map)

    # Calculate the areas of intersection between the ReEDS regions and timezones
    # and determine the timezone that overlaps most with each ReEDS region
    region_tz_intersects = gpd.overlay(
        dfzones,
        tz_map,
        how='intersection',
        keep_geom_type=False
    )
    region_tz_intersects['area'] = region_tz_intersects.geometry.area
    region_tz_map = (
        region_tz_intersects.sort_values('area', ascending=False)
        .rename(columns={'rb': 'r'})
        .drop_duplicates('r', keep='first')
        .sort_values('r')
        [['r', 'tz']]
    )

    out_fpath = os.path.join(casedir, "inputs_case", "reeds_region_tz_map.csv")
    region_tz_map.to_csv(out_fpath, index=False)
    
    print(f"Run complete. See {out_fpath} for output.")
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Calculate the prevailing time zone of each ReEDS region"
    )
    parser.add_argument("casedir", help="Folder of ReEDS run")
    
    args = parser.parse_args()
    
    thispath = os.path.dirname(os.path.realpath(__file__))
    reeds_path = os.path.abspath(os.path.join(thispath, "..",  ".."))
    
    main(args.casedir, reeds_path)
