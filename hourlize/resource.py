import pandas as pd
import numpy as np
import sklearn.cluster as sc
from pdb import set_trace as pdbst
import datetime
import os
import sys
import shutil
import tables
import json
import config as cf
import logging

#Set resource config in config.py. Then run 'python resource.py' from the command prompt,
#and the output will be in out/

#Setup logger
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
logger.info('Resource logger setup.')

def setup(this_dir_path, out_dir, paths):
    time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
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
    shutil.copy2(this_dir_path + 'resource.py', out_dir + 'inputs/')
    shutil.copy2(this_dir_path + 'config.py', out_dir + 'inputs/')
    for path in paths:
        if path != None:
            shutil.copy2(path, out_dir + 'inputs/')

def get_supply_curve_and_filter_and_add_reg(rev_case_path, rev_prefix, reg_col, profile_id_col, reg_out_col, reg_map_path, min_cap_path, filter_cols={}, test_mode=False, test_filters={}):
    #Retrieve and filter the supply curve. Also, add a 'region' column, apply minimum capacity thresholds, and apply test mode if necessary.
    logger.info('Reading supply curve inputs and filtering...')
    startTime = datetime.datetime.now()
    df = pd.read_csv(rev_case_path + '/' + rev_prefix + '_sc.csv', dtype={reg_col:int}, low_memory=False)
    if profile_id_col == 'index':
        #This means we assume the columns in the profile file correspond to the rows in the supply curve file.
        df['index'] = df.index
    for k in filter_cols.keys():
        #Apply any filtering of the supply curve, e.g. to select onshore or offshore wind.
        df = df[df[k].isin(filter_cols[k])].copy()
    if reg_out_col is not reg_col:
        #This means we must map the regions from reg_col to reg_out_col
        df_map = pd.read_csv(reg_map_path, low_memory=False, usecols=[reg_col,reg_out_col])
        df = pd.merge(left=df, right=df_map, how='left', on=[reg_col], sort=False)
        df.rename(columns={reg_out_col:'region'}, inplace=True)
    else:
        df['region'] = df[reg_col]
    if min_cap_path is not None:
        #Apply a minimum capacity threshold, which can be region-dependent, and remove all rows that do not meet
        #the minimum threshold (with an exception to make sure each region is representated by a row in case precribed
        #builds occur in that region).
        df_mincap = pd.read_csv(min_cap_path, low_memory=False)
        min_cap_reg_col = df_mincap.columns[0]
        if min_cap_reg_col is not reg_col:
            #This means we need to map regions from reg_col to min_cap_reg_col to apply the minimum capacity thresholds 
            df_regmap = pd.read_csv(reg_map_path, low_memory=False, usecols=[reg_col,min_cap_reg_col])
            df = pd.merge(left=df, right=df_regmap, how='left', on=[reg_col], sort=False)
        df = pd.merge(left=df, right=df_mincap, how='left', on=[min_cap_reg_col], sort=False)
        if min_cap_reg_col is not reg_col:
            #After the thresholds have been applied to each row, we drop the added min_cap_reg_col column.
            df.drop(columns=[min_cap_reg_col], inplace=True)
        #We make sure to keep the row with the highest capacity in each region, even if it has less capacity
        #Than the minimum threshold. We eventually will set this capacity to zero, but we need to do this
        #so that we can accomodate prescribed builds in R2.
        df_max_cap_reg = df.sort_values('capacity', ascending=False).groupby('region').head(1)
        df_max_cap_reg['force_keep'] = df_max_cap_reg['capacity'] < df_max_cap_reg['min_cap']
        df_max_cap_reg = df_max_cap_reg[['force_keep']].copy()
        df = pd.merge(left=df, right=df_max_cap_reg, how='left', left_index=True, right_index=True, sort=False)
        df = df[(df['capacity'] >= df['min_cap']) | (df['force_keep'] == True)].copy()
        df.loc[df['force_keep'] == True, 'capacity'] = .001 #This is to make sure we get profiles. We'll convert to 0 in the outputs by rounding.
        df.drop(columns=['min_cap', 'force_keep'], inplace=True)
    if test_mode:
        #Test mode allows us to reduce the dataset further for speed
        for k in test_filters.keys():
            df = df[df[k].isin(test_filters[k])].copy()
    logger.info('Done reading supply curve inputs and filtering: '+ str(datetime.datetime.now() - startTime))
    return df

def add_classes(df_sc, class_path):
    #Add 'class' column to supply curve, based on specified class definitions in class_path.
    logger.info('Adding classes...')
    startTime = datetime.datetime.now()
    df_class = pd.read_csv(class_path, index_col='class')
    #Crreate class column.
    df_sc['class'] = 'NA'
    #Now loop through classes (rows in df_class). Classes may have multiple defining criteria (columns in df_class),
    #so we loop through columns to build the selection criteria for each class, building up a 'mask' of criteria for each class.
    #Numeric ranges in class definitions (e.g. min and max wind speeds) are indicated by the pipe symbol, e.g. '5|6'
    #for 'mean_res' would mean 'mean_res' must fall between 5 and 6 for that class.
    for cname, row in df_class.iterrows():
        #Start with mask=True, and then build up the full conditional based on each column of df_class.
        mask = True
        for col, val in row.items():
            if '|' in val:
                #Pipe is a special character that indicates a numeric range.
                rng = val.split('|')
                rng = [float(n) for n in rng]
                mask = mask & (df_sc[col] >= min(rng))
                mask = mask & (df_sc[col] < max(rng))
            else:
                #No pipe symbol means we do a simple match.
                mask = mask & (df_sc[col] == val)
        #Finally, apply the mask that has been built for this class.
        df_sc.loc[mask, 'class'] = cname
    logger.info('Done adding classes: '+ str(datetime.datetime.now() - startTime))
    return df_sc

def add_bins(df_sc, bin_group_cols, bin_col, bin_num, bin_method, tech, offshore_grid_cost_join):
    #Add 'bin' column to supply curve using bin_method after grouping by bin_group_cols.
    logger.info('Adding bins...')
    startTime = datetime.datetime.now()
    if tech == 'wind-ofs' and offshore_grid_cost_join != None:
        df_gridcon = pd.read_csv(offshore_grid_cost_join)
        df_sc = df_sc.merge(df_gridcon, how='left', on='sc_point_gid', sort=False)
        df_sc[bin_col] = df_sc[bin_col] + df_sc['array_cable_CAPEX'] + df_sc['export_cable_CAPEX']
    df_sc = df_sc.groupby(bin_group_cols, sort=False).apply(get_bin, bin_col, bin_num, bin_method)
    df_sc = df_sc.reset_index(drop=True).sort_values('sc_gid')
    logger.info('Done adding bins: '+ str(datetime.datetime.now() - startTime))
    return df_sc

def get_bin(df_in, bin_col, bin_num, bin_method):
    df = df_in.copy()
    ser = df[bin_col]
    #If we have less than or equal unique points than bin_num, we simply group the points with the same values.
    if ser.unique().size <= bin_num:
        bin_ser = ser.rank(method='dense')
        df['bin'] = bin_ser.values
    elif bin_method == 'kmeans':
        nparr = ser.to_numpy().reshape(-1,1)
        kmeans = sc.KMeans(n_clusters=bin_num, random_state=0).fit(nparr)
        bin_ser = pd.Series(kmeans.labels_)
        #but kmeans doesn't necessarily label in order of increasing value because it is 2D,
        #so we replace labels with cluster centers, then rank
        kmeans_map = pd.Series(kmeans.cluster_centers_.flatten())
        bin_ser = bin_ser.map(kmeans_map).rank(method='dense')
        df['bin'] = bin_ser.values
    elif bin_method == 'equal_cap_man':
        #using a manual method instead of pd.cut because i want the first bin to contain the
        #first sc point regardless, even if its capacity is more than the capacity of the bin,
        #and likewise for other bins, so i don't skip any bins.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        cumcaps = df['capacity'].cumsum().tolist()
        totcap = df['capacity'].sum()
        vals = df[bin_col].tolist()
        bins = []
        curbin = 1
        for i,v in enumerate(vals):
            bins.append(curbin)
            if cumcaps[i] >= totcap*curbin/bin_num:
                curbin += 1
        df['bin'] = bins
        df = df.reindex(index=orig_index) #we need the same index ordering for apply to work.
    elif bin_method == 'equal_cap_cut':
        #Use pandas.cut with cumulative capacity in each class. This will assume equal capacity bins
        #to bin the data.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        df['cum_cap'] = df['capacity'].cumsum()
        bin_ser = pd.cut(df['cum_cap'], bin_num, labels=False)
        bin_ser = bin_ser.rank(method='dense')
        df['bin'] = bin_ser.values
        df = df.reindex(index=orig_index) #we need the same index ordering for apply to work.
    df['bin'] = df['bin'].astype(int)
    return df

def aggregate_sc(df_sc, bin_col):
    #Calculate the capacity, trans_cap_cost, and distance for each region,class,bin. Trans_cap_cost
    #And distance are weighted averages, with capacity as the weighting factor.
    logger.info('Aggregating supply curve...')
    startTime = datetime.datetime.now()
    # Define a lambda function to compute the weighted mean:
    wm = lambda x: np.average(x, weights=df_sc.loc[x.index, 'capacity'])
    aggs = {'capacity': 'sum', bin_col:wm, 'dist_mi':wm }
    df_sc_agg = df_sc.groupby(['region','class','bin']).agg(aggs)
    logger.info('Done aggregating supply curve: '+ str(datetime.datetime.now() - startTime))
    return df_sc_agg

def get_profiles(df_sc, rev_case_path, rev_prefix, select_year, profile_dset, profile_id_col, profile_weight_col,
                 rep_profile_method, driver, gather_method):
    #Get the hourly profiles for each supply curve point, calculate weighted average profile for each
    #region,class (avgs_arr). Also select one of the original profiles to represent each region,class (reps_arr)
    #based on  a specified method (rep_profile_method e.g. root mean square error using differences from avgs_arr).
    logger.info('Getting profiles...')
    startTime = datetime.datetime.now()
    #get unique combinations of region and class
    df_rep = df_sc[['region','class']].drop_duplicates().sort_values(by=['region','class']).reset_index(drop=True)
    num_profiles = len(df_rep)
    #Get the hourly profiles from the provided h5 file path.
    with tables.open_file(rev_case_path + '/' + rev_prefix + '_rep_profiles_' + str(select_year) + '.h5', 'r', driver=driver) as h5:
        #iniitialize avgs_arr and reps_arr with the right dimensions
        avgs_arr = np.zeros((8760,num_profiles))
        reps_arr = avgs_arr.copy()
        reps_idx = []
        timezones = []
        #get idxls, the index of the profiles, which excludes half hour for pv, e.g.
        times = h5.root['time_index'][:].astype('datetime64')
        time_df = pd.DataFrame({'datetime':times})
        idxls = time_df[time_df['datetime'].dt.minute == 0].index.tolist()
        t0 = datetime.datetime.now()
        #For each region+class combination, gather all the associated profiles to calculate the
        #weighted average and representative profile (adding to avgs_arr and reps_arr respectively).
        for i,r in df_rep.iterrows():
            t1 = datetime.datetime.now()
            df_rc = df_sc[(df_sc['region'] == r['region']) & (df_sc['class'] == r['class'])].copy()
            df_rc = df_rc.reset_index(drop=True)
            #Get the list of IDs, weights, and timezones for each region+class
            idls = df_rc[profile_id_col].tolist()
            wtls = df_rc[profile_weight_col].tolist()
            tzls = df_rc['timezone'].tolist()
            tzls = [int(t) for t in tzls]
            if df_rc[profile_id_col].dtype == object:
                #This means there is a list of IDs and weights for each supply curve row (e.g. for PV).
                #So we need additional processing to gather all the IDs for profile retrieval:
                idls = [json.loads(l) for l in idls]
                wtls = [json.loads(l) for l in wtls]
                #We need to duplicate tzls entries to match up with idls
                for n in range(len(tzls)):
                    tzls[n] = [tzls[n]] * len(idls[n])
                #flatten lists and gather into dataframe
                idls = [item for sublist in idls for item in sublist]
                wtls = [item for sublist in wtls for item in sublist]
                tzls = [item for sublist in tzls for item in sublist]
                df_ids = pd.DataFrame({'idls':idls, 'wtls':wtls, 'tzls':tzls})
                #Remove duplicate IDs by summing the weighting factors for each ID.
                #This also ends up sorting by id, important for h5 retrieval:
                df_ids =  df_ids.groupby(['idls'], as_index =False).agg({'wtls':sum, 'tzls':lambda x: x.iloc[0]})
                idls = df_ids['idls'].tolist()
                wtls = df_ids['wtls'].tolist()
                tzls = df_ids['tzls'].tolist()
            if len(idls) != len(wtls):
                logger.info('ERROR: IDs and weights have different length!')
            t2 = datetime.datetime.now()
            #The 'smart' method will grab profiles as a slice if the average spacing of those profiles
            #is less than 250 (based on some manual speed tests). If the average spacing is greater than 250,
            #this method simply grabs each profile separately (which requires separate io steps).
            ave_spacing = (max(idls) - min(idls))/len(idls)
            if gather_method == 'slice' or (gather_method == 'smart' and ave_spacing < 250):
                min_idls = min(idls)
                orig_idls_idx = [j - min_idls for j in idls]
                arr = h5.root[profile_dset][:,min_idls:max(idls)+1]
                arr = arr[:, orig_idls_idx].copy()
            else:
                arr = h5.root[profile_dset][:,idls]
            t3 = datetime.datetime.now()
            #reduce elements to on the hour using idxls
            arr = arr[idxls,:]
            arr = arr.T
            #Take weighted average and add to avgs_arr
            avg_arr = np.average(arr, axis=0, weights=wtls)
            avgs_arr[:,i] = avg_arr
            #Now find the profile in arr that is most representative, ie has the minimum error
            if rep_profile_method == 'rmse':
                errs = np.sqrt(((arr-avg_arr)**2).mean(axis=1))
            elif rep_profile_method == 'ave':
                errs = abs(arr.sum(axis=1) - avg_arr.sum())
            min_idx = np.argmin(errs)
            reps_arr[:,i] = arr[min_idx]
            #For reference, save the id and timezone, of the represenative profile
            reps_idx.append(idls[min_idx])
            timezones.append(tzls[min_idx])
            #Output to logger the time spent on this region+class and progress made.
            t4 = datetime.datetime.now()
            frac = (i+1)/num_profiles
            pct = round(frac*100)
            tthis = round((t4 - t1).total_seconds(),2)
            th5 = round((t3 - t2).total_seconds(),2)
            ttot = (t4 - t0).total_seconds()
            mtot, stot = divmod(round(ttot), 60)
            tlft = ttot*(1- frac)/frac
            mlft, slft = divmod(round(tlft), 60)
            logger.info(str(pct)+'%'+
                  '\treg='+str(r['region'])+
                  '\tcls='+str(r['class'])+
                  '\tt='+str(tthis)+'s'+
                  '\th5= '+str(th5)+'s'+
                  '\ttot='+str(mtot)+'m,'+str(stot)+'s'+
                  '\tlft='+str(mlft)+'m,'+str(slft)+'s')

        #scale the data as necessary
        if 'scale_factor' in h5.root[profile_dset].attrs:
            scale = h5.root[profile_dset].attrs['scale_factor']
            reps_arr = reps_arr / scale
            avgs_arr = avgs_arr / scale
    df_rep['rep_gen_gid'] = reps_idx
    df_rep['timezone'] = timezones

    logger.info('Done getting profiles: '+ str(datetime.datetime.now() - startTime))
    return df_rep, avgs_arr, reps_arr

def get_profiles_allyears(df_rep, rev_case_path, rev_prefix, hourly_out_years, profile_dset, driver):
    #Based on the representative profiles selected in get_profiles(), gather the profiles for all other years
    logger.info('Getting multiyear profiles...')
    startTime = datetime.datetime.now()
    idls = df_rep['rep_gen_gid'].tolist()
    reps_arr_out = np.empty((0, len(idls)))
    for year in hourly_out_years:
        with tables.open_file(rev_case_path + '/' + rev_prefix + '_rep_profiles_' + str(year) + '.h5', 'r', driver=driver) as h5:
            arr = h5.root[profile_dset][:,idls]
            reps_arr_out = np.vstack((reps_arr_out, arr))
        logger.info('Done with ' + str(year))
    logger.info('Done getting multiyear profiles: '+ str(datetime.datetime.now() - startTime))
    return reps_arr_out

def shift_timezones(arr, df_rep, source_timezone, output_timezone):
    #Shift timezone of hourly data
    if output_timezone != source_timezone:
        arr = arr.T
        if output_timezone == 'local':
            timezones = dict(zip(df_rep.index, df_rep['timezone']))
            for n in range(len(arr)):
                arr[n] = np.roll(arr[n], timezones[n] - source_timezone)
        else:
            #Shift from source timezone to output timezone
            for n in range(len(arr)):
                arr[n] = np.roll(arr[n], output_timezone - source_timezone)
        arr = arr.T
    return arr

def calc_performance(avgs_arr, reps_arr, df_rep, timeslice_path, cfmean_type, add_h17):
    #Calculated aggregated performance characteristics for each region+class, including capacity factor,
    #capacity factor corrections, and standard deviations by timeslice, based on representative
    #profiles.
    logger.info('Calculate peformance characteristics...')
    startTime = datetime.datetime.now()
    #Read in timeslice definitions
    df_ts = pd.read_csv(timeslice_path, low_memory=False)
    df_cf = df_rep[['region','class']].copy()
    df_cfmean_ts = df_cf.copy()
    df_cfsigma_ts = df_cf.copy()
    df_cfcorr_ts = df_cf.copy()
    #Use either avgs_arr or reps_arr for average capacity factors, depending on cfmean_type.
    if cfmean_type == 'ave':
        cfmean_arr = avgs_arr.copy()
    elif cfmean_type == 'rep':
        cfmean_arr = reps_arr.copy()
    #Calculate average capacity factor across the entire year for each region+class.
    df_cf['cfmean'] = np.mean(cfmean_arr, axis=0)
    #For each timeslice, calculate capacity factor, correction factor (timeslice capacity factor divided
    #by annual average capacity factor), and standard deviation of capacity factor.
    ts_ls = df_ts['timeslice'].unique().tolist()
    for ts in ts_ls:
        ts_idx = df_ts[df_ts['timeslice'] == ts].index
        df_cfmean_ts[ts] = np.mean(cfmean_arr[ts_idx], axis=0)
        df_cfcorr_ts[ts] = df_cfmean_ts[ts] / df_cf['cfmean']
        #We use reps_arr regardless for standard deviations. Perhaps we should use the average of the standard deviations tho...
        df_cfsigma_ts[ts] = np.std(reps_arr[ts_idx], ddof=1, axis=0)
    if add_h17:
        #Fill in H17 with H13.
        df_cfmean_ts['H17'] = df_cfmean_ts['H3']
        df_cfcorr_ts['H17'] = df_cfcorr_ts['H3']
        df_cfsigma_ts['H17'] = df_cfsigma_ts['H3']
    #Flatten capacity factor correction table.
    df_cfcorr_ts = pd.melt(df_cfcorr_ts, id_vars=['region','class'], var_name='timeslice', value_name= 'cfcorr')
    df_cfcorr_ts.sort_values(by=['region', 'class', 'timeslice'], inplace=True)
    #Combine and flatten capacity factor means and standard deviations.
    df_cfmean_ts['type'] = 'cfmean'
    df_cfsigma_ts['type'] = 'cfsigma'
    df_cf_ts = pd.concat([df_cfmean_ts,df_cfsigma_ts], sort=False).reset_index(drop=True)
    df_cf_ts = pd.melt(df_cf_ts, id_vars=['region','class','type'], var_name='timeslice', value_name= 'value')
    df_cf_ts = df_cf_ts.pivot_table(index=['region','class','timeslice'], columns='type', values='value')
    logger.info('Done with performance calcs: '+ str(datetime.datetime.now() - startTime))
    return df_cf, df_cf_ts, df_cfcorr_ts

def save_sc_outputs(df_sc, df_sc_agg, out_dir, tech):
    #Save resource outputs: supply curve, performance characteristics (capacity factor means,
    #standard deviations, and corrections) and hourly profiles.
    logger.info('Saving supply curve outputs...')
    startTime = datetime.datetime.now()
    df_sc_raw = df_sc.copy()
    df_sc_raw['capacity'] = df_sc_raw['capacity'].round(2)
    df_sc_raw.to_csv(out_dir + 'results/' + tech + '_supply_curve_raw.csv', index=False)
    df_sc_agg[['capacity','trans_cap_cost','dist_mi']] = df_sc_agg[['capacity','trans_cap_cost','dist_mi']].round(2)
    df_sc_agg.to_csv(out_dir + 'results/' + tech + '_supply_curve.csv')
    logger.info('Done saving supply curve outputs: '+ str(datetime.datetime.now() - startTime))


def save_time_outputs(df_cf, df_cf_ts, df_cfcorr_ts, reps_arr_out, df_rep, start_1am, out_dir, tech):
    #Save resource outputs: supply curve, performance characteristics (capacity factor means,
    #standard deviations, and corrections) and hourly profiles.
    logger.info('Saving time-dependent outputs...')
    startTime = datetime.datetime.now()
    df_cf.to_csv(out_dir + 'results/' + tech + '_cf.csv', index=False)
    df_cf_ts.to_csv(out_dir + 'results/' + tech + '_cf_ts.csv')
    df_cfcorr_ts.to_csv(out_dir + 'results/' + tech + '_cfcorr_ts.csv', index=False)
    df_hr = pd.DataFrame(reps_arr_out.round(4))
    df_rep['class_reg'] = df_rep['class'].astype(str) + '_' + df_rep['region'].astype(str)
    df_hr.columns = df_rep['class_reg']
    if start_1am is True:
        #to start at 1am instead of 12am, roll the data by -1 and add 1 to index
        df_hr.index = df_hr.index + 1
        for col in df_hr:
            df_hr[col] = np.roll(df_hr[col], -1)
    df_hr.to_csv(out_dir + 'results/' + tech + '.csv.gz')
    df_rep.to_csv(out_dir + 'results/' + tech + '_rep_profiles_meta.csv', index=False)
    logger.info('Done saving time-dependent outputs: '+ str(datetime.datetime.now() - startTime))

if __name__== '__main__':
    startTime = datetime.datetime.now()
    this_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    out_dir = this_dir_path + 'out/' + cf.out_dir
    setup(this_dir_path, out_dir, [cf.timeslice_path, cf.class_path, cf.reg_map_path, cf.min_cap_path, cf.offshore_grid_cost_join])
    df_sc = get_supply_curve_and_filter_and_add_reg(cf.rev_case_path, cf.rev_prefix, cf.reg_col, cf.profile_id_col, cf.reg_out_col, cf.reg_map_path, cf.min_cap_path, cf.filter_cols, cf.test_mode, cf.test_filters)
    df_sc = add_classes(df_sc, cf.class_path)
    df_sc = add_bins(df_sc, cf.bin_group_cols, cf.bin_col, cf.bin_num, cf.bin_method, cf.tech, cf.offshore_grid_cost_join)
    df_sc_agg = aggregate_sc(df_sc, cf.bin_col)
    save_sc_outputs(df_sc, df_sc_agg, out_dir, cf.tech)
    df_rep, avgs_arr, reps_arr = get_profiles(df_sc, cf.rev_case_path, cf.rev_prefix, cf.select_year, cf.profile_dset, cf.profile_id_col,
        cf.profile_weight_col, cf.rep_profile_method, cf.driver, cf.gather_method)
    reps_arr_out = get_profiles_allyears(df_rep, cf.rev_case_path, cf.rev_prefix, cf.hourly_out_years, cf.profile_dset, cf.driver)
    reps_arr = shift_timezones(reps_arr, df_rep, cf.resource_source_timezone, cf.agg_outputs_timezone)
    reps_arr_out = shift_timezones(reps_arr_out, df_rep, cf.resource_source_timezone, cf.hourly_outputs_timezone)
    avgs_arr = shift_timezones(avgs_arr, df_rep, cf.resource_source_timezone, cf.agg_outputs_timezone)
    df_cf, df_cf_ts, df_cfcorr_ts = calc_performance(avgs_arr, reps_arr, df_rep, cf.timeslice_path, cf.cfmean_type, cf.add_h17)
    save_time_outputs(df_cf, df_cf_ts, df_cfcorr_ts, reps_arr_out, df_rep, cf.start_1am, out_dir, cf.tech)
    logger.info('All done! total time: '+ str(datetime.datetime.now() - startTime))
