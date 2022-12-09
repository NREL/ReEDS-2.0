import pandas as pd
import numpy as np
import sklearn.cluster as sc
from pdb import set_trace as pdbst
import datetime
import os
import sys
import shutil
import json
import config as cf
import logging

#Set load config in config.py. Then run 'python load.py' from the command prompt,
#and the output will be in out/

#Setup logger
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
if cf.logToTerminal:
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
logger.info('Load logger setup.')

def setup(this_dir_path, out_dir, paths):
    time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    #Create output directory, creating backup if one already exists.
    if os.path.exists(out_dir):
        os.rename(out_dir, os.path.dirname(out_dir) + '-archive-'+time)
    os.makedirs(out_dir)
    os.makedirs(out_dir + 'inputs/')
    os.makedirs(out_dir + 'results/')

    #Add output file for logger
    fh = logging.FileHandler(out_dir + 'log.txt', mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    #Copy inputs to outputs
    shutil.copy2(this_dir_path + 'load.py', out_dir + 'inputs/')
    shutil.copy2(this_dir_path + 'config.py', out_dir + 'inputs/')
    for key in paths:
        shutil.copy2(paths[key], out_dir + 'inputs/')

def get_hourly_load(load_source, us_only):
    logger.info('Gathering and combining hourly inputs...')
    startTime = datetime.datetime.now()
    df = pd.read_csv(load_source, low_memory=False, index_col=0, parse_dates=True)
    if us_only:
        us_bas = ['p'+str(i+1) for i in range(134)]
        df = df[us_bas].copy()
    df = df.reindex(sorted(df.columns), axis=1)
    logger.info('Done gathering hourly inputs: '+ str(datetime.datetime.now() - startTime))
    return df

def process_hourly(df_hr_input, load_source_timezone, paths, hourly_out_years, select_year, agg_outputs_timezone, hourly_outputs_timezone, truncate_leaps):
    logger.info('Processing hourly data...')
    startTime = datetime.datetime.now()
    df_hr = df_hr_input.copy()
    df_hr.index.rename('datetime', inplace=True)

    #Add logic for testmode?

    #We remove years and last day of leap year before rolling to local to mimic what is done for resource, which gets us close, although resource is in UTC
    #First remove other years' data
    df_hr = df_hr[df_hr.index.year.isin(hourly_out_years)].copy()

    if truncate_leaps is True:
        #Remove December 31 for leap years
        df_hr = df_hr[~((df_hr.index.year % 4 == 0) & (df_hr.index.month == 12) & (df_hr.index.day == 31))].copy()

    if 'p19' not in df_hr:
        #Fill p19 with p20 and scale by guess of 1/6 (although calibration below will obviate this scaling)
        df_hr['p19'] = df_hr['p20'] / 6

    if paths['calibrate_path'] != False:
        #Scale the ba hourly profiles to state-level annual loads with state-to-ba participation factors
        #First, combine the calibrated state-level energy with ba participation factors to calculate the calibrated energy by BA
        df_st_energy = pd.read_csv(paths['calibrate_path'])
        df_ba_frac = pd.read_csv(paths['ba_frac_path'])
        df_hier = pd.read_csv(paths['hierarchy_path'], usecols=['n','st'])
        df_hier.drop_duplicates(inplace=True)
        df_ba_frac = pd.merge(left=df_ba_frac, right=df_hier, how='left', on=['n'], sort=False)
        df_ba_energy = pd.merge(left=df_ba_frac, right=df_st_energy, how='left', on=['st'], sort=False)
        df_ba_energy['GWh cal'] = df_ba_energy['GWh'] * df_ba_energy['factor']
        df_ba_energy = df_ba_energy[['n','GWh cal']]
        #Calculate the annual energy by ba from the hourly profile in GWh and use this to find scaling factors
        df_hr_yr_ls = []
        for year in df_hr.index.year.unique().tolist():
            df_hr_yr = df_hr[df_hr.index.year == year].copy()
            df_hr_sum = df_hr_yr.sum()/1e3
            df_hr_sum = df_hr_sum.reset_index().rename(columns={'index':'n', 0:'GWh orig'})
            df_scale = pd.merge(left=df_hr_sum, right=df_ba_energy, how='left', on=['n'], sort=False)
            df_scale['factor'] = df_scale['GWh cal'] / df_scale['GWh orig']
            scales = dict(zip(df_scale['n'], df_scale['factor']))
            #Scale the profiles
            for ba in df_hr:
                df_hr_yr[ba] = df_hr_yr[ba] * scales[ba]
            df_hr_yr_ls.append(df_hr_yr)
        df_hr = pd.concat(df_hr_yr_ls, sort=False)

    df_hr = df_hr.reindex(sorted(df_hr.columns), axis=1)
    df_hr = df_hr.round()

    #Create df_hour_out, which will be used for hourly outputs, whereas df_hr is used for aggregated outputs
    df_hr_out = df_hr.copy()

    #Shift hourly data based on desired timezones
    df_hr = shift_timezones(df_hr, paths, load_source_timezone, agg_outputs_timezone)
    df_hr_out = shift_timezones(df_hr_out, paths, load_source_timezone, hourly_outputs_timezone)

    logger.info('Done processing hourly: '+ str(datetime.datetime.now() - startTime))
    return df_hr, df_hr_out

def shift_timezones(df_hr, paths, source_timezone, output_timezone):
    #Shift timezone of hourly data
    if output_timezone != source_timezone:
        if output_timezone == 'local':
            #Shift from source timezone to local standard time
            df_tz = pd.read_csv(paths['ba_timezone_path'])
            timezones = dict(zip(df_tz['ba'], df_tz['timezone']))
            for ba in df_hr:
                df_hr[ba] = np.roll(df_hr[ba], timezones[ba] - source_timezone)
        else:
            #Shift from source timezone to output timezone
            for ba in df_hr:
                df_hr[ba] = np.roll(df_hr[ba], output_timezone - source_timezone)
    return df_hr

def calc_outputs(df_hr, paths, hourly_out_years, select_year, calibrate_year):
    logger.info('Calculating outputs...')
    startTime = datetime.datetime.now()

    #Join timeslices and seasons
    df_ts = pd.read_csv(paths['timeslice_path'], low_memory=False)
    df_seas = pd.read_csv(paths['season_path'])
    df_ts_seas = pd.merge(left=df_ts, right=df_seas, on=['timeslice'], how='left', sort=False)

    #Add year column to df_hr and reset index
    df_hr = df_hr.reset_index()
    df_hr['year'] = df_hr['datetime'].dt.year

    #If we have calibrated to a year and are not using multiyear, year should be calibrate_year
    if hourly_out_years == [select_year] and paths['calibrate_path'] != False:
        df_hr['year'] = calibrate_year

    #duplicate df_ts_seas to cover all years of df_hr
    for y in range(len(df_hr['year'].unique()) - 1):
        df_ts_seas = pd.concat([df_ts_seas, df_ts_seas], sort=False).reset_index(drop=True)

    #join timeslices, seasons to df_hr
    df_hr_ts_seas = pd.merge(left=df_hr, right=df_ts_seas, left_index=True, right_index=True, how='left', sort=False)

    #flatten df_hr_ts_seas
    df_hr_ts_seas = pd.melt(df_hr_ts_seas, id_vars=['datetime','year','timeslice','season'], var_name='ba', value_name= 'MWh')

    #calculate max by season
    df_seas_max = df_hr_ts_seas.groupby(['year','ba','season'], sort=False, as_index =False).agg({'MWh': 'max'})

    #Add H17
    df_h3_flat = df_hr_ts_seas[df_hr_ts_seas['timeslice']=='H3'].copy()
    df_h17_flat = df_h3_flat.sort_values(['MWh'],ascending=False).groupby(['year','ba']).head(40)
    df_h17_flat['timeslice'] = 'H17'
    df_hr_ts_seas_wh17 = pd.concat([df_hr_ts_seas, df_h17_flat], sort=False).reset_index(drop=True)

    #calculate average by timeslice
    df_ts_mean = df_hr_ts_seas_wh17.groupby(['year','ba','timeslice'], sort=False, as_index =False).agg({'MWh': 'mean'})

    #calculate variance, mean, and variance over mean squared by timeslice and rto, without h17
    df_hier_rto = pd.read_csv(paths['hierarchy_path'], usecols=['n','rto'])
    df_hier_rto.rename(columns={'n':'ba'}, inplace=True)
    df_hr_ts_seas_rto = pd.merge(left=df_hr_ts_seas, right=df_hier_rto, on=['ba'], how='left', sort=False)
    df_hr_ts_seas_rto = df_hr_ts_seas_rto.groupby(['rto','datetime','year','timeslice'], sort=False, as_index =False).sum()
    df_hr_ts_seas_rto['mean'] = df_hr_ts_seas_rto['MWh']
    df_hr_ts_seas_rto['var'] = df_hr_ts_seas_rto['MWh']
    df_lk2factorRTO = df_hr_ts_seas_rto.groupby(['year','rto','timeslice'], sort=False, as_index =False).agg({'mean': 'mean', 'var': 'var'})
    df_lk2factorRTO['lk2factor'] = df_lk2factorRTO['var'] / df_lk2factorRTO['mean']**2
    logger.info('Done calculating outputs: '+ str(datetime.datetime.now() - startTime))

    return df_ts_mean, df_seas_max, df_lk2factorRTO

def save_outputs(df_hr_out, df_ts_mean, df_seas_max, df_lk2factorRTO, start_1am, out_dir):
    logger.info('Saving outputs...')
    startTime = datetime.datetime.now()
    df_hr_out = df_hr_out.reset_index(drop=True)

    if start_1am is True:
        #to start at 1am instead of 12am, roll the data by -1 and add 1 to index
        df_hr_out.index = df_hr_out.index + 1
        for ba in df_hr_out:
            df_hr_out[ba] = np.roll(df_hr_out[ba], -1)

    df_hr_out.to_csv(out_dir + 'results/load_hourly.csv.gz')
    df_ts_mean_out = df_ts_mean.rename(columns={'ba':'r'})
    df_ts_mean_out = df_ts_mean_out.pivot_table(index=['year','r'], columns='timeslice', values='MWh')
    df_ts_mean_out.to_csv(out_dir + 'results/load.csv')
    df_seas_max_out = df_seas_max.rename(columns={'ba':'r'})
    df_seas_max_out = df_seas_max_out.pivot_table(index=['year','r'], columns='season', values='MWh')
    df_seas_max_out.to_csv(out_dir + 'results/peak.csv')
    df_lk2factorRTO_out = df_lk2factorRTO.pivot_table(index=['year','rto'], columns='timeslice', values='lk2factor')
    df_lk2factorRTO_out.to_csv(out_dir + 'results/lk2factorRTO.csv')

    logger.info('Done saving outputs: '+ str(datetime.datetime.now() - startTime))

if __name__== '__main__':
    startTime = datetime.datetime.now()
    this_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    out_dir = this_dir_path + 'out/load_' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + '/'
    paths = {'ba_timezone_path':cf.ba_timezone_path,
             'calibrate_path':cf.calibrate_path,
             'ba_frac_path':cf.ba_frac_path,
             'hierarchy_path':cf.hierarchy_path,
             'timeslice_path':cf.timeslice_path,
             'season_path':cf.season_path,
            }
    setup(this_dir_path, out_dir, paths)
    df_hr_input = get_hourly_load(cf.load_source, cf.us_only)
    if cf.hourly_process == True:
        df_hr, df_hr_out = process_hourly(df_hr_input, cf.load_source_timezone, paths, cf.hourly_out_years, cf.select_year, cf.agg_outputs_timezone, cf.hourly_outputs_timezone, cf.truncate_leaps)
    else:
        df_hr = df_hr_input.copy()
        df_hr_out = df_hr_input.copy()
    #Compare df_hr and df_hr_input to see the combined effect of all the processing steps.
    df_ts_mean, df_seas_max, df_lk2factorRTO = calc_outputs(df_hr, paths, cf.hourly_out_years, cf.select_year, cf.calibrate_year)
    save_outputs(df_hr_out, df_ts_mean, df_seas_max, df_lk2factorRTO, cf.start_1am, out_dir)
    logger.info('All done! total time: '+ str(datetime.datetime.now() - startTime))
