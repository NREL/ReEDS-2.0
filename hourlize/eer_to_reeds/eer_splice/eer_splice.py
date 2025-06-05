'''
This script develops BA-level load profiles for ReEDS (in GWh) based on EER state-level load profiles, load participation factors between states and BAs, and allows replacement of specified sectors with other data sources.

EER data starts at 12am hour beginning. TEMPO data starts at 12am local time (hour beginning?). Building data starts at 1am hour ending, so no roll is needed for buidlings. Output data starts at 12am hour beginning.

Requires: pandas, h5py. It previously required pyarrow as well and I made a new 'parquet' conda environment with these three packages (along with dependencies)
'''
import os
import h5py
import pandas as pd
import numpy as np
import datetime
import shutil

#USER INPUTS
eer_case = 'ira_con' #ira, ira_con, central, baseline
eer_load_path = '/projects/eerload/source_eer_load_profiles/20230604_eer_load'
weather_years = list(range(2007,2014))
model_years = [2021, 2025, 2030, 2035, 2040, 2045, 2050] #Should be df_eer_meta['YEAR'].unique() unless we reduce further
bas = [f'p{n}' for n in range(1,135)]
replace_sectors = False #If True, use the following parameters to remove and replace sectors
replace_type = 'Buildings' #'Transportation' or 'Buildings'

this_dir_path = os.path.dirname(os.path.realpath(__file__))

if replace_type == 'Transportation':
    sectors_remove = {'transportation': ['buses', 'heavy duty trucks', 'light duty autos','light duty trucks', 'medium duty trucks']}
    years_remove = [2025, 2030, 2035]
    replace_dir = '/projects/drprojects/evmc/data/full_run_2024-10-14'
    replace_scen = 'mid_baseline'
elif replace_type == 'Buildings':
    sectors_remove = {
        'commercial': ['commercial air conditioning', 'commercial space heating', 'commercial ventilation'],
        'residential': ['residential air conditioning', 'residential furnace fans', 'residential secondary heating','residential space heating'],
    }
    years_remove = model_years
    replace_files = [
        '/projects/eerload/mmowers/eer_splice/agg_res_eulp_hvac_elec_GWh_upgrade0.csv',
        '/projects/eerload/mmowers/eer_splice/agg_com_eulp_hvac_elec_GWh_upgrade0.csv',
    ]

time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
output_dir = f'{this_dir_path}/{eer_case}_{time}'
os.makedirs(output_dir)
shutil.copy2(f'{this_dir_path}/eer_splice.py', output_dir)
shutil.copy2(f'{this_dir_path}/load_factors.csv', output_dir)
shutil.copy2(f'{this_dir_path}/ba_timezone.csv', output_dir)

df_load_factors = pd.read_csv(f'{this_dir_path}/load_factors.csv')
ba_timezone = pd.read_csv(f'{this_dir_path}/ba_timezone.csv', index_col=0)['timezone']
for weather_year in weather_years:
    print(f'weather year: {weather_year}')
    f_eer = h5py.File(f'{eer_load_path}_{weather_year}.h5')
    df_eer_meta = pd.DataFrame(f_eer['meta'][:]).astype(str)
    df_eer_load = pd.DataFrame(f_eer['load'][:])
    f_eer.close()
    df_eer_meta['YEAR'] = df_eer_meta['YEAR'].astype(int)
    df_eer_meta = df_eer_meta[df_eer_meta['SCENARIO'].str.lower()==eer_case].copy()
    if replace_sectors:
        #Sector removal
        for sector, subsectors in sectors_remove.items():
            remove_criteria = (df_eer_meta['SECTOR'] == sector)&(df_eer_meta['SUBSECTOR'].isin(subsectors))&(df_eer_meta['YEAR'].isin(years_remove))
            df_eer_removed = df_eer_meta[remove_criteria].copy()
            df_eer_meta = df_eer_meta[~remove_criteria].copy()
    df_eer_load = df_eer_load[df_eer_meta.index].copy()
    hourly_timestamps = pd.date_range(start=f'1/1/{weather_year}  12:00:00 AM', end=f'12/31/{weather_year}  11:00:00 PM', freq='h')
    for model_year in model_years:
        print(f'model year: {model_year}')
        df_ba_load = pd.DataFrame({'timestamp': hourly_timestamps})
        df_ba_load['timestamp'] = df_ba_load['timestamp'].dt.strftime('%-m/%-d/%Y  %-I:%M:%S %p')
        df_ba_load.insert(0, 'year', int(model_year))
        df_ba_zeros = pd.DataFrame(np.zeros((len(df_ba_load), len(bas))), columns=bas)
        df_ba_load = pd.concat([df_ba_load, df_ba_zeros], axis='columns')
        df_eer_meta_yr = df_eer_meta[df_eer_meta['YEAR']==model_year].copy()
        df_eer_load_yr = df_eer_load[df_eer_meta_yr.index].copy()
        for ba in bas:
            for idx, ba_row in df_load_factors[df_load_factors['ba'] == ba].iterrows():
                #I really only need to iterrate through rows because of DC and p123
                df_eer_meta_st = df_eer_meta_yr[df_eer_meta_yr['STATE'] == ba_row['state']].copy()
                df_eer_load_st = df_eer_load_yr[df_eer_meta_st.index].sum(axis=1)
                df_ba_load[ba] = df_ba_load[ba] + df_eer_load_st * ba_row['load_factor']
        if replace_sectors and model_year in years_remove:
            #Sector replacement
            if replace_type == 'Transportation':
                #TODO: Confirm units of ev-ws-immediatecharging-hourly-weighted-sum-kWh-{model_year}.csv. Currently assuming Wh even though its labeled as kWh.
                df_load_r_ldv = pd.read_csv(f'{replace_dir}/scenario={replace_scen}/segment=ldv/year={model_year}/summaries/ev-ws-immediatecharging-hourly-weighted-sum-kWh-{model_year}.csv', index_col='datetime')
                df_load_r_mhdv = pd.read_csv(f'{replace_dir}/scenario={replace_scen}/segment=ldv/year={model_year}/summaries/ev-ws-immediatecharging-hourly-weighted-sum-kWh-{model_year}.csv', index_col='datetime')
                df_load_r = df_load_r_ldv + df_load_r_mhdv
                #Convert from Wh to GWh
                df_load_r = df_load_r/1e9
                #Duplicate the final day of TEMPO data for leap years, since EER data includes all hours but TEMPO EV data does not.
                if weather_year % 4 == 0:
                    df_load_r = pd.concat([df_load_r, df_load_r.iloc[-24:]])
                #Convert from local to EST and adjust df_ba_load with new load
                for ba in bas:
                    df_load_r[ba] = np.roll(df_load_r[ba], -5 - ba_timezone[ba])
                    df_ba_load[ba] = df_ba_load[ba] + df_load_r[ba].values
            elif replace_type == 'Buildings':
                ls_df = [pd.read_csv(f, index_col=0) for f in replace_files]
                df_load_r = pd.concat(ls_df).groupby(level=0).sum()
                #Duplicate the final day of Building data for leap years, since EER data includes all hours but Building data does not.
                if weather_year % 4 == 0:
                    df_load_r = pd.concat([df_load_r, df_load_r.iloc[-24:]])
                #Adjust df_ba_load with new load (no rolling needed because EER data starts at 12am hour beginning and building data starts at 1am hour ending)
                for ba in bas:
                    if ba in df_load_r:
                        df_ba_load[ba] = df_ba_load[ba] + df_load_r[ba].values
        for ba in bas:
            df_ba_load[ba] = df_ba_load[ba].round(4)
        df_ba_load.to_csv(f'{output_dir}/{eer_case}_e{model_year}_w{weather_year}.csv', index=False)
print('eer_splice.py Done!')
