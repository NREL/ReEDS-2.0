'''
This script creates a parquet file from an eer h5 load file, for use by dsgrid. It also creates dimension csv files.

Requires: pandas, h5py, pyarrow. I made a new 'parquet' conda environment with these three packages (along with dependencies)
'''
import os
import h5py
import pandas as pd
import shutil
from pdb import set_trace as b

this_dir_path = os.path.dirname(os.path.realpath(__file__))

#switches
eer_load_dir = '/projects/eerload/source_eer_load_profiles'
eer_load_pre = '20230604_eer_load'
output_dir = f'{eer_load_dir}/dsgrid_{eer_load_pre}'

weather_years = list(range(2007,2014))

#Make directory to contain parquet and copy this file into that directory
#If parquet container already exists, this will throw an error
os.mkdir(output_dir)
os.mkdir(f'{output_dir}/dimensions')
shutil.copy2(os.path.realpath(__file__), output_dir)
os.mkdir(f'{output_dir}/{eer_load_pre}.parquet')
counter = 1
for weather_year in weather_years:
    print(f'weather year: {weather_year}')
    with h5py.File(f'{eer_load_dir}/{eer_load_pre}_{weather_year}.h5') as f_eer:
        df_eer_meta = pd.DataFrame(f_eer['meta'][:]).astype(str)
        df_eer_load = pd.DataFrame(f_eer['load'][:])
    #Rename columns
    df_eer_meta.columns = [c.lower() for c in df_eer_meta.columns]
    df_eer_meta = df_eer_meta.rename(columns={'year':'model_year', 'state':'geography'})
    #Output dimension csv files for 2012, which has full set of 8784 hours
    if weather_year == 2012:
        ls_time = df_eer_load.index.tolist()
        df_time = pd.DataFrame({'id':ls_time, 'name': ls_time})
        df_time.to_csv(f'{output_dir}/dimensions/time_index.csv', index=False)
        for col in df_eer_meta:
            ls_unique = df_eer_meta[col].unique().tolist()
            df_dim = pd.DataFrame({'id':ls_unique, 'name': ls_unique})
            df_dim.to_csv(f'{output_dir}/dimensions/{col}.csv', index=False)

    #Output parquet files
    scenarios = df_eer_meta['scenario'].unique().tolist()
    geographies = df_eer_meta['geography'].unique().tolist()
    model_years = df_eer_meta['model_year'].unique().tolist()
    num_tot = len(scenarios) * len(geographies) * len(model_years) * len(weather_years)

    for model_year in model_years:
        for scenario in scenarios:
            for geography in geographies:
                print(f'{counter}/{num_tot} ({round(100*counter/num_tot, 1)}%) w{weather_year} m{model_year} {scenario} {geography}')
                outdir = f'{output_dir}/{eer_load_pre}.parquet/scenario={scenario}/geography={geography}/model_year={model_year}/weather_year={weather_year}'
                os.makedirs(outdir)
                mask = (df_eer_meta['scenario'] == scenario)&(df_eer_meta['geography'] == geography)&(df_eer_meta['model_year'] == model_year)
                df_meta = df_eer_meta[mask].copy()
                df_meta = df_meta[['sector','subsector']].copy()
                df_load = df_eer_load[df_meta.index].copy()
                df_combined = pd.concat([df_meta, df_load.T], axis=1)
                df_long = df_combined.melt(id_vars=['sector','subsector'], var_name="time_index", value_name="value")
                df_long.to_parquet(f'{outdir}/load.parquet')
                counter = counter + 1