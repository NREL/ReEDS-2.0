import pandas as pd
import numpy as np
from pdb import set_trace as pdbst
import datetime
import os
import sys
import shutil
import config as cf
import logging
import h5py

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
        if paths[key] != False:
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

def process_hourly(df_hr_input, load_source_timezone, paths, hourly_out_years, select_year, output_timezone, truncate_leaps, calibrate_type, calibrate_year, use_default_before_yr, load_source_hr_type):
    logger.info('Processing hourly data...')
    startTime = datetime.datetime.now()
    df_hr = df_hr_input.copy()
    df_hr.index.rename('datetime', inplace=True)
    df_hr = df_hr.sort_index()

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
        if calibrate_type == 'all_years': #switch for calibrating multiple years
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
        elif calibrate_type == 'one_year': #switch for calibrating to a single year and then using as coeffecient for additional years
            df_hr_yr = df_hr[df_hr.index.year == calibrate_year].copy()
            df_hr_sum = df_hr_yr.sum()/1e3
            df_hr_sum = df_hr_sum.reset_index().rename(columns={'index':'n', 0:'GWh orig'})
            df_scale = pd.merge(left=df_hr_sum, right=df_ba_energy, how='left', on=['n'], sort=False)
            df_scale['factor'] = df_scale['GWh cal'] / df_scale['GWh orig']
            scales = dict(zip(df_scale['n'], df_scale['factor']))
            #Scale the profiles
            for ba in df_hr:
                df_hr[ba] = df_hr[ba] * scales[ba]

    df_hr = df_hr.reindex(sorted(df_hr.columns), axis=1)
    df_hr = df_hr.round()

    #Shift hourly data based on desired timezones. Shift each year independently.
    df_hr_ls = []
    for year in hourly_out_years:
        df_hr_yr = df_hr[df_hr.index.year == year].copy()
        df_hr_yr = roll_hourly_data(df_hr_yr, paths, load_source_timezone, output_timezone, load_source_hr_type)
        df_hr_ls.append(df_hr_yr)
    df_hr = pd.concat(df_hr_ls)

    #Splice in default data, for which the first entry is Jan 1, 1am hour ending, which is 12am-1am, which is 12am hour beginning.
    if use_default_before_yr != False:
        logger.info('Splicing in default load before ' + str(use_default_before_yr))
        df_hier = pd.read_csv('../inputs/hierarchy.csv')
        df_hier = df_hier.rename(columns= {'*r' : 'r'})
        logger.info('Reading default load and selecting ' + str(select_year) + ' profiles')
        df_bau = pd.read_csv('../inputs/variability/multi_year/load.csv.gz')
        df_bau = df_bau[(df_bau.index >= 8760*(select_year-2007)) &
                        (df_bau.index < 8760*(select_year-2006))].reset_index(drop=True) #selecting select_year profiles, which have been scaled to 2010 totals
        df_bau = df_bau.drop(columns=['Unnamed: 0'])
        #Since the default load data starts at 1am hour ending while our load source
        #data starts at 12 am hour ending, we need to roll to line them up.
        for ba in df_bau:
            df_bau[ba] = np.roll(df_bau[ba], 1) #There is only one year of load being rolled here.
        df_bau['hour'] = df_bau.index + 1
        df_bau['year'] = 2010
        df_bau = pd.melt(df_bau, id_vars=['year','hour'], var_name='r', value_name= 'value')
        df_hier_cendiv = df_hier[['r', 'cendiv']].copy()
        df_bau = df_bau.merge(df_hier_cendiv, how='inner', on='r') #this filters to only the ISOs of interest as well.
        logger.info('Growing default load')
        df_loadgrowth = pd.read_csv('../inputs/loaddata/demand_AEO_2021_reference.csv')
        df_loadgrowth = pd.melt(df_loadgrowth, id_vars=['cendiv'], var_name='year', value_name= 'mult')
        df_loadgrowth['year'] = df_loadgrowth['year'].astype(int)
        df_bau_2010 = df_bau.copy()
        ls_df_yr = [df_bau_2010]
        for year in range(2011,use_default_before_yr):
            df_yr = df_bau_2010.copy()
            df_yr['year'] = year
            ls_df_yr.append(df_yr)
        df_bau = pd.concat(ls_df_yr, ignore_index=True)
        df_bau = df_bau.merge(df_loadgrowth, how='left', on=['year','cendiv'])
        df_bau['value'] = df_bau['value'] * df_bau['mult']
        logger.info('Reshaping default load')
        df_bau = df_bau.pivot_table(index=['year','hour'], columns='r', values='value').reset_index()
        logger.info('Concatenating with default load')
        ls_df_bau = []
        for year in range(2010,use_default_before_yr):
            df_yr = df_bau[df_bau['year'] == year].copy()
            df_yr['year'] = year
            df_yr.drop(columns=['year','hour'], inplace=True)
            df_yr.index = pd.date_range('1/1/' + str(year) + ' 00:00', periods=8760, freq='1H')
            ls_df_bau.append(df_yr)
        df_bau = pd.concat(ls_df_bau).round().astype(int)
        df_bau.index.rename('datetime', inplace=True)
        df_hr = pd.concat([df_bau,df_hr])
        logger.info('Done splicing in default load')

    logger.info('Done processing hourly: '+ str(datetime.datetime.now() - startTime))
    return df_hr

def roll_hourly_data(df_hr, paths, source_timezone, output_timezone, load_source_hr_type):
    #If hour-beginning, we shift data down (+1) to convert to hour ending
    hour_end_shift = 1 if load_source_hr_type == 'begin' else 0
    #Shift timezone of hourly data
    if output_timezone != source_timezone:
        if output_timezone == 'local':
            #Shift from source timezone to local standard time
            df_tz = pd.read_csv(paths['ba_timezone_path'])
            timezones = dict(zip(df_tz['ba'], df_tz['timezone']))
            for ba in df_hr:
                df_hr[ba] = np.roll(df_hr[ba], timezones[ba] - source_timezone + hour_end_shift)
        else:
            #Shift from source timezone to output timezone
            for ba in df_hr:
                df_hr[ba] = np.roll(df_hr[ba], output_timezone - source_timezone + hour_end_shift)
    return df_hr

def calc_outputs(df_hr, paths, hourly_out_years, select_year, calibrate_year):
    logger.info('Calculating outputs...')
    startTime = datetime.datetime.now()
    df_hr = df_hr.copy()

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
    df_ts_seas_dup = pd.concat([df_ts_seas]*len(df_hr['year'].unique()), ignore_index=True)

    #join timeslices, seasons to df_hr
    df_hr_ts_seas = pd.merge(left=df_hr, right=df_ts_seas_dup, left_index=True, right_index=True, how='left', sort=False)

    #flatten df_hr_ts_seas
    df_hr_ts_seas = pd.melt(df_hr_ts_seas, id_vars=['datetime','year','timeslice','season'], var_name='ba', value_name= 'MWh')

    #Add H17 and remove those hours from H3
    h3_num_hrs = len(df_ts[df_ts['timeslice'] == 'H3'])
    df_h3 = df_hr_ts_seas[df_hr_ts_seas['timeslice'] == 'H3'].copy()
    df_non_h3 = df_hr_ts_seas[df_hr_ts_seas['timeslice'] != 'H3'].copy()
    df_h3_grp = df_h3.sort_values(['MWh'],ascending=False).groupby(['year','ba'])
    df_h17 = df_h3_grp.head(40).copy()
    df_h3 = df_h3_grp.tail(h3_num_hrs - 40).copy()
    df_h17['timeslice'] = 'H17'
    df_hr_ts_seas_wh17 = pd.concat([df_non_h3, df_h3, df_h17], ignore_index=True)

    #calculate average by timeslice
    df_ts_mean = df_hr_ts_seas_wh17.groupby(['year','ba','timeslice'], sort=False, as_index =False).agg({'MWh': 'mean'})

    logger.info('Done calculating outputs: '+ str(datetime.datetime.now() - startTime))
    return df_ts_mean

def shift_to_1am(df_hr):
    #to start at 1am instead of 12am, roll the data by -1
    df_hr_ls = []
    for year in df_hr.index.year.unique():
        df_hr_yr = df_hr[df_hr.index.year == year].copy()
        df_hr_yr = df_hr_yr.reindex(np.roll(df_hr_yr.index,-1))
        df_hr_ls.append(df_hr_yr)
    df_hr = pd.concat(df_hr_ls)
    return df_hr

def save_outputs(df_hr, df_ts_mean, out_dir, output_style, compression_opts, dtypeLoad):
    logger.info('Saving outputs...')
    startTime = datetime.datetime.now()
    df_hr = df_hr.copy()
    if output_style == 'default':
        df_hr = df_hr.reset_index(drop=True)
        df_hr.index = df_hr.index + 1 #Index starts at 1.
        df_hr.astype(dtypeLoad).to_hdf(out_dir + 'results/load_hourly.h5', key='data', complevel=compression_opts, index=True)
    elif output_style == 'EFS':
        df_hr['year'] = df_hr.index.year
        df_hr['hour'] = df_hr.groupby('year').cumcount() + 1
        df_hr = df_hr.reset_index(drop=True)
        new_cols = ['year','hour'] + [c for c in df_hr.columns if c not in ['year','hour']]
        df_hr = df_hr[new_cols]
        #TODO: change the following to h5 if we ever need efs style load again
        df_hr.to_csv(out_dir + 'results/load_hourly.csv.gz', index=False)
        df_ts_mean_out = df_ts_mean.rename(columns={'ba':'r'})
        df_ts_mean_out = df_ts_mean_out.pivot_table(index=['r', 'timeslice'], columns='year', values='MWh')
        df_ts_mean_out.to_csv(out_dir + 'results/load.csv')
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
    #If load source is a directory (as it is for EER load), the csv files inside need to be labeled like w2007.csv.
    if os.path.isdir(cf.load_source):
        #TODO: Should we move the following to a separate function, e.g. process_eer_style_load(out_dir, paths)?
        f = h5py.File(os.path.join(out_dir,'results','load_hourly_multi.h5'), 'w')
        ls_df_hr = []
        for year in list(range(2007,2014)):
            logger.info('processing weather year ' + str(year) + '...')
            df_hr_input = get_hourly_load(os.path.join(cf.load_source,'w'+str(year)+'.csv'), cf.us_only)
            df_hr = df_hr_input.copy() if cf.hourly_process == False else process_hourly(df_hr_input, cf.load_source_timezone, paths, cf.hourly_out_years, year, cf.output_timezone, cf.truncate_leaps, cf.calibrate_type, cf.calibrate_year, cf.use_default_before_yr, cf.load_source_hr_type)
            if year == cf.select_year:
                df_ts_mean = calc_outputs(df_hr, paths, cf.hourly_out_years, cf.select_year, cf.calibrate_year)
                if cf.start_1am:
                    df_hr = shift_to_1am(df_hr)
                save_outputs(df_hr, df_ts_mean, out_dir, 'EFS', cf.compression_opts, cf.dtypeLoad)
            else:
                if cf.start_1am:
                    df_hr = shift_to_1am(df_hr)
            df_hr['weather_year'] = year
            df_hr['model_year'] = df_hr.index.year
            ls_df_hr.append(df_hr)
        df_multi = pd.concat(ls_df_hr, ignore_index=True)
        #Save ba columns. Remove the final two columns (weather_year and model_year).
        f.create_dataset('columns', data=df_multi.columns[:-2], dtype=h5py.special_dtype(vlen=str))
        #Create h5 datasets, one for each model year
        for year in df_multi['model_year'].unique():
            df_h = df_multi[df_multi['model_year'] == year].copy()
            df_h.drop(columns=['weather_year','model_year'], inplace=True)
            f.create_dataset(str(year), data=df_h, dtype=cf.dtypeload, compression='gzip')
        f.close()
    else:
        df_hr_input = get_hourly_load(cf.load_source, cf.us_only)
        df_hr = df_hr_input.copy() if cf.hourly_process == False else process_hourly(df_hr_input, cf.load_source_timezone, paths, cf.hourly_out_years, cf.select_year, cf.output_timezone, cf.truncate_leaps, cf.calibrate_type, cf.calibrate_year, cf.use_default_before_yr, cf.load_source_hr_type)
        #Compare df_hr and df_hr_input to see the combined effect of all the processing steps.
        df_ts_mean = calc_outputs(df_hr, paths, cf.hourly_out_years, cf.select_year, cf.calibrate_year)
        if cf.start_1am:
            df_hr = shift_to_1am(df_hr)
        save_outputs(df_hr, df_ts_mean, out_dir, cf.output_style, cf.compression_opts, cf.dtypeLoad)
    logger.info('All done! total time: '+ str(datetime.datetime.now() - startTime))
