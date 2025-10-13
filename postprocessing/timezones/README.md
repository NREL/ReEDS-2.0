The `calculate_region_timezones.py` script uses the time zone shapefile from the U.S. Bureau of Transportation Statistics (https://geodata.bts.gov/datasets/usdot::time-zones/) and the ReEDS model regions shapefile of a given ReEDS run to determine the prevailing time zone of each region. The output is written to the `inputs_case` folder of the given ReEDS run folder.

The script is called as follows:
```console
python calculate_region_timezones.py {ReEDS run folder path}
```