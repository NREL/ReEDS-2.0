'''This script ingests dsgrid data, reshapes the data & outputs the data to the 
same folder as csvs in the terminal's current directory.  The resulting csv can 
be used in load.py.'''

import pandas as pd
from datetime import datetime
from pandas.tseries.offsets import DateOffset
from pdb import set_trace as b
import numpy as np

input_file = 'all_sector_electricity_MWh_2010_2050_projections_rev1.parquet'

startTime = datetime.now()

# Read dsgrid parquet file in as df 
df = pd.read_parquet(input_file)
print('Done reading .parquet: '+ str(datetime.now() - startTime))

# change 'model_year' from type categorical to integer and 'scenario' from type categorical to string
df['model_year'] = df['model_year'].astype('int')
df['scenario'] = df['scenario'].astype('string')
print('Done changing column types: '+ str(datetime.now() - startTime))

# Round 'electricity_MWh' to whole #s then convert to int (from float)
df['electricity_MWh'] = df['electricity_MWh'].round(0).astype(int)
print('Done rounding: '+ str(datetime.now() - startTime))

#Pivot df and reset index for operational efficiency
#DELETE - switch timestamp and model_year?
df = df.pivot(index=['timestamp','model_year', 'scenario'], columns='geography', values='electricity_MWh')
print('Done with pivot: '+ str(datetime.now() - startTime))
df = df.reset_index()
print('Done with reset index: '+ str(datetime.now() - startTime))

# Convert 'timestamp' column from UTC to EST & then strip timezone off (timestamp in EST)
df['timestamp'] = df['timestamp'].dt.tz_localize("UTC").dt.tz_convert("EST").dt.tz_localize(None)
print('Done changing timestamp: '+ str(datetime.now() - startTime))

#Remove December 31 for non-leap years - (reduces hours from 8784 to 8760 for non-leap years)
df = df[~((df['timestamp'].dt.month == 12) & (df['timestamp'].dt.day == 31) & (df['model_year'] % 4 != 0))].copy()
print('Done removing 12/31 '+ str(datetime.now() - startTime))

#boolean of dates greater than or equal to 2/29 in non-leap years
non_leap_offset = ((df['timestamp'] >= pd.Timestamp(2012, 2, 29)) & (df['model_year'] % 4 != 0))
# addition (offset) of 1 day to the timestamp column 'DATETIME' for dates 2/29 to 12/30 in non-leap years and keep the same DATETIME otherwise
df['DATETIME'] = np.where(non_leap_offset, df['timestamp'] + pd.DateOffset(days=1), df['timestamp'])
print('Done with offset: '+ str(datetime.now() - startTime))

#Replacement of year in DATETIME with the actual model year
for ind, ts in df.iterrows():
    df['DATETIME'][ind] = ts['DATETIME'].replace(year=ts['model_year'])
print('Done with iterrows: '+ str(datetime.now() - startTime))

#Drop unnecessary datetime columns
df = df.drop(columns=['model_year','timestamp'])

#Isolate scenario, explode pivot by geography, output each scenario to csv
for s in df['scenario'].unique():
    df_scen = df[df['scenario'] == s]
    df_scen = df_scen.drop(columns='scenario')
    df_scen = df_scen.set_index('DATETIME')
    df_scen.to_csv('load_hourly_ba_EST_TEMPO' + s + '.csv')
    print('Done with ' + s + ': ' + str(datetime.now() - startTime))

print('Done: '+ str(datetime.now() - startTime))