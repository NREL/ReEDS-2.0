from preprocess_rev import match_to_counties, df2gdf
import pandas as pd
import geopandas as gpd
import os
import shapely

if __name__== '__main__':

    reedspath = "/scratch/bsergi/ReEDS-2.0"
    
    # read in no exclusions file
    sc = pd.read_csv("/scratch/bsergi/ReEDS-2.0/postprocessing/land_use/inputs/14_all_landcover_area_characterization_supply-curve-aggregation.csv")

    # read in county shapefile
    cnty_shapefile = os.path.join(reedspath, "inputs", "shapefiles", "US_COUNTY_2022")
    # for lat/lon matching it is better to have a geographic CRS as opposed to a projected on
    crs_out = "EPSG:4326"
    cnty_shp = gpd.read_file(cnty_shapefile).to_crs(crs_out)

    # match to counties
    sc_out = match_to_counties(sc, cnty_shp)
    sc_out.to_csv("/scratch/bsergi/ReEDS-2.0/postprocessing/land_use/inputs/14_all_landcover_area_characterization_supply-curve-aggregation.csv")

