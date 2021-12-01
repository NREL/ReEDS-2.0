#%% Imports
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
import h5py

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

#%% Functions
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
    logger.info('Done copying inputs.')

def get_supply_curve_and_preprocess(tech, rev_case_path, rev_prefix, reg_col, profile_id_col, reg_out_col, reg_map_path, min_cap, individual_sites, existing_sites, start_year, filter_cols={}, test_mode=False, test_filters={}):
    #Retrieve and filter the supply curve. Also, add a 'region' column, apply minimum capacity thresholds, and apply test mode if necessary.
    logger.info('Reading supply curve inputs and filtering...')
    startTime = datetime.datetime.now()
    df = pd.read_csv(rev_case_path + '/' + rev_prefix + '_sc.csv', dtype={reg_col:int}, low_memory=False)
    if profile_id_col == 'index':
        #This means we assume the columns in the profile file correspond to the rows in the supply curve file.
        df['index'] = df.index
    for k in filter_cols.keys():
        #Apply any filtering of the supply curve, e.g. to select onshore or offshore wind.
        if filter_cols[k][0] == '=':
            df = df[df[k] == filter_cols[k][1]].copy()
        elif filter_cols[k][0] == '>':
            df = df[df[k] > filter_cols[k][1]].copy()
        elif filter_cols[k][0] == '<':
            df = df[df[k] < filter_cols[k][1]].copy()
    if individual_sites:
        if tech == 'wind-ofs':
            df['region'] = 'o'+df.sc_point_gid.astype(int).astype(str)
        else:
            df['region'] = 'i'+df.sc_point_gid.astype(int).astype(str)
    elif reg_out_col is not reg_col:
        #This means we must map the regions from reg_col to reg_out_col
        df_map = pd.read_csv(reg_map_path, low_memory=False, usecols=[reg_col,reg_out_col])
        df = pd.merge(left=df, right=df_map, how='left', on=[reg_col], sort=False)
        df.rename(columns={reg_out_col:'region'}, inplace=True)
    else:
        df['region'] = df[reg_col]
    if existing_sites != None:
        logger.info('Assigning existing sites...')
        #Read in existing sites and filter
        df_exist = pd.read_csv(existing_sites, low_memory=False)
        df_exist = df_exist[['tech','STATE','pca','resource_region','UID','LONG','LAT','cap','Commercial.Online.Year','RetireYear']].copy()
        df_exist = df_exist[(df_exist['tech'].str.lower() == tech) & (df_exist['RetireYear'] > start_year)].reset_index(drop=True)
        df_exist['LONG'] = df_exist['LONG'] * -1
        df_exist.sort_values('cap', ascending=False, inplace=True)
        #Map the state codes of df_exist to the state names in df
        df_cp = df.copy()
        df_st = pd.read_csv('inputs/resource/state_abbrev.csv', low_memory=False)
        dict_st = dict(zip(df_st['ST'], df_st['State']))
        df_exist['STATE'] = df_exist['STATE'].map(dict_st)
        df_cp = df_cp[['sc_gid','state','latitude','longitude','capacity']].copy()
        df_cp['existing_capacity'] = 0.0
        df_cp['existing_uid'] = 0
        df_cp['online_year'] = 0
        df_cp['retire_year'] = 0
        df_cp_out = pd.DataFrame()
        #Restrict matching to within the same State
        for st in df_exist['STATE'].unique():
            logger.info('Existing sites state: ' + st)
            df_exist_st = df_exist[df_exist['STATE'] == st].copy()
            df_cp_st = df_cp[df_cp['state'] == st].copy()
            for i_exist, r_exist in df_exist_st.iterrows():
                #TODO: Need to fix lats and longs that don't exist
                if r_exist['LONG'] == 0:
                    continue
                #Assume each lat is ~69 miles and each long is ~53 miles
                df_cp_st['mi_sq'] =  ((df_cp_st['latitude'] - r_exist['LAT'])*69)**2 + ((df_cp_st['longitude'] - r_exist['LONG'])*53)**2
                #Sort by closest
                df_cp_st.sort_values(['mi_sq'], inplace=True)
                #Step through the available sites and fill up the closest ones until we are done with this existing capacity
                exist_cap_remain = r_exist['cap']
                for i_avail, r_avail in df_cp_st.iterrows():
                    avail_cap = df_cp_st.at[i_avail, 'capacity']
                    df_cp_st.at[i_avail, 'existing_uid'] = r_exist['UID']
                    df_cp_st.at[i_avail, 'online_year'] = r_exist['Commercial.Online.Year']
                    df_cp_st.at[i_avail, 'retire_year'] = r_exist['RetireYear']
                    if exist_cap_remain <= avail_cap:
                        df_cp_st.at[i_avail, 'existing_capacity'] = exist_cap_remain
                        exist_cap_remain = 0
                        break
                    else:
                        df_cp_st.at[i_avail, 'existing_capacity'] = avail_cap
                        exist_cap_remain = exist_cap_remain - avail_cap
                if exist_cap_remain > 0:
                    logger.info('WARNING: Existing site shortfall: ' + str(exist_cap_remain))
                #Build output and take the available sites with existing capacity out of consideration for the next exisiting site
                df_cp_out_add = df_cp_st[df_cp_st['existing_capacity'] > 0].copy()
                df_cp_out = pd.concat([df_cp_out, df_cp_out_add], sort=False).reset_index(drop=True)
                df_cp_st = df_cp_st[df_cp_st['existing_capacity'] == 0].copy()
        df_cp_out['exist_mi_diff'] = df_cp_out['mi_sq']**0.5
        df_cp_out = df_cp_out[['sc_gid', 'existing_capacity', 'existing_uid', 'online_year', 'retire_year', 'exist_mi_diff']].copy()
        df = pd.merge(left=df, right=df_cp_out, how='left', on=['sc_gid'], sort=False)
        df[['existing_capacity','existing_uid','online_year','retire_year','exist_mi_diff']] = df[['existing_capacity','existing_uid','online_year','retire_year','exist_mi_diff']].fillna(0)
        df[['existing_uid','online_year','retire_year']] = df[['existing_uid','online_year','retire_year']].astype(int)
    else:
        df['existing_capacity'] = 0.0
    if min_cap > 0:
        #Remove sites with less than minimum capacity threshold, but keep sites that have existing capacity
        df = df[(df['capacity'] >= min_cap) | (df['existing_capacity'] > 0)].copy()
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
    #Create class column.
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

def add_bins(df_sc, individual_sites, bin_group_cols, bin_col, bin_num, bin_method, tech):
    #Add 'bin' column to supply curve using bin_method after grouping by bin_group_cols.
    if bin_col == 'combined_eos_trans':
        df_sc[bin_col] = df_sc['mean_capital_cost'] / df_sc['mean_system_capacity'] * (df_sc['capital_cost_scalar'] - 1)*1000 + df_sc['trans_cap_cost']
    if bin_col == 'combined_off_ons_trans':
        df_sc[bin_col] = (df_sc['mean_export'] + df_sc['mean_array']) / (df_sc['mean_system_capacity'] * 40) * 1000 + df_sc['trans_cap_cost_per_mw']
    if individual_sites:
        #In this case, we just call each bin 1 and return it.
        df_sc['bin'] = 1
        logger.info('Done adding bin column for individual sites.')
    else:
        logger.info('Adding bins...')
        startTime = datetime.datetime.now()
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

def save_sc_outputs(df_sc, individual_sites, existing_sites, start_year, bin_col, out_dir, tech, reg_map_path):
    #Save resource supply curve outputs
    logger.info('Saving supply curve outputs...')
    startTime = datetime.datetime.now()
    #Create local copy of df_sc so that we don't modify the df_sc passed by reference
    df_sc = df_sc.copy()
    df_sc['supply_curve_cost_per_mw'] = df_sc[bin_col]
    df_sc.to_csv(out_dir + 'results/' + tech + '_supply_curve_raw.csv', index=False)
    #Round now to prevent infeasibility in model because existing (pre-2010 + prescribed) capacity is slightly higher than supply curve capacity
    decimals = 4
    df_sc[['capacity','existing_capacity']] = df_sc[['capacity','existing_capacity']].round(decimals)
    if existing_sites:
        df_exist = df_sc[df_sc['existing_capacity'] > 0].copy()
        #Exogenous (pre-start-year) capacity output
        df_exog = df_exist[df_exist['online_year'] < start_year].copy()
        if not df_exog.empty:
            df_exog = df_exog[['sc_gid','class','region','retire_year','existing_capacity']].copy()
            max_exog_ret_year = df_exog['retire_year'].max()
            ret_year_ls = list(range(start_year,max_exog_ret_year + 1))
            df_exog = df_exog.pivot_table(index=['sc_gid','class','region'], columns='retire_year', values='existing_capacity')
            df_exog = df_exog.reindex(columns=ret_year_ls).fillna(method='bfill', axis='columns')
            df_exog = pd.melt(df_exog.reset_index(), id_vars=['sc_gid','class','region'], value_vars=ret_year_ls, var_name='year', value_name= 'capacity')
            df_exog = df_exog[df_exog['capacity'].notnull()].copy()
            df_exog['tech'] = tech + '_' + df_exog['class'].astype(str)
            df_exog = df_exog[['tech','region','year','capacity']].copy()
            df_exog = df_exog.groupby(['tech','region','year'], sort=False, as_index =False).sum()
            df_exog['capacity'] =  df_exog['capacity'].round(decimals)
            df_exog.to_csv(out_dir + 'results/' + tech + '_exog_cap.csv', index=False)
        #Prescribed capacity output
        df_pre = df_exist[df_exist['online_year'] >= start_year].copy()
        if not df_pre.empty:
            df_pre = df_pre[['region','online_year','existing_capacity']].copy()
            df_pre = df_pre.rename(columns={'online_year':'year', 'existing_capacity':'capacity'})
            df_pre = df_pre.groupby(['region','year'], sort=False, as_index =False).sum()
            df_pre['capacity'] =  df_pre['capacity'].round(decimals)
            df_pre.to_csv(out_dir + 'results/' + tech + '_prescribed_builds.csv', index=False)
        #Reduce supply curve based on exogenous (pre-start-year) capacity
        criteria = (df_sc['online_year'] > 0) & (df_sc['online_year'] < start_year)
        df_sc.loc[criteria, 'capacity'] = df_sc.loc[criteria, 'capacity'] - df_sc.loc[criteria, 'existing_capacity']
    
    distance_col = 'dist_to_coast' if tech == 'wind-ofs' else 'dist_mi'
    keepcols = ['capacity', 'supply_curve_cost_per_mw', distance_col]
    if individual_sites:
        df_reg_map = df_sc[['region','cnty_fips']].copy()
        df_county_map = pd.read_csv(reg_map_path, low_memory=False, usecols=['cnty_fips','reeds_ba'])
        df_reg_map = pd.merge(left=df_reg_map, right=df_county_map, how='left', on=['cnty_fips'], sort=False)
        df_reg_map = df_reg_map.rename(columns={'reeds_ba':'rb'}).drop(columns=['cnty_fips'])
        df_reg_map.to_csv(out_dir + 'results/region_map.csv', index=False)
        df_sc_ind = df_sc[['region','class','bin'] + keepcols].copy()
        df_sc_ind[keepcols] = df_sc_ind[keepcols].round(decimals)
        df_sc_ind.to_csv(out_dir + 'results/' + tech + '_supply_curve.csv', index=False)
    else:
        #Aggregate: Calculate the capacity, supply_curve_cost_per_mw, and distance for each region,class,bin.
        #supply_curve_cost_per_mw and distance are weighted averages, with capacity as the weighting factor.
        def wm(x):
            return np.average(x, weights=df_sc.loc[x.index, 'capacity']) if df_sc.loc[x.index, 'capacity'].sum() > 0 else 0
        def concat_sc_point_gid(x):
            return x.astype(str).str.cat(sep=',')
        aggs = {
            'capacity': 'sum',
            'supply_curve_cost_per_mw': wm,
            distance_col: wm,
            'sc_point_gid': concat_sc_point_gid,
        }
        df_sc_agg = df_sc.groupby(['region','class','bin']).agg(aggs)
        df_sc_agg[keepcols] = df_sc_agg[keepcols].round(decimals)
        df_sc_agg.to_csv(out_dir + 'results/' + tech + '_supply_curve.csv')
    logger.info('Done saving supply curve outputs: '+ str(datetime.datetime.now() - startTime))

def get_profiles(df_sc, rev_case_path, rev_prefix, select_year, profile_dset, profile_id_col, profile_weight_col,
                 rep_profile_method, driver, gather_method, profile_dir):
    #Get the hourly profiles for each supply curve point, calculate weighted average profile for each
    #region,class (avgs_arr). Also select one of the original profiles to represent each region,class (reps_arr)
    #based on  a specified method (rep_profile_method e.g. root mean square error using differences from avgs_arr).
    logger.info('Getting profiles...')
    startTime = datetime.datetime.now()
    #get unique combinations of region and class
    df_rep = df_sc[['region','class']].drop_duplicates().sort_values(by=['region','class']).reset_index(drop=True)
    num_profiles = len(df_rep)
    #Get the hourly profiles from the provided h5 file path.
    h5path = os.path.join(
        rev_case_path, profile_dir, 
        '{}_rep_profiles_{}.h5'.format(
            rev_prefix if profile_dir == '' else profile_dir, select_year))
    with tables.open_file(h5path, 'r', driver=driver) as h5:
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

def get_individual_profiles(df_sc, rev_case_path, rev_prefix, select_year, profile_dset, profile_id_col, driver):
    logger.info('Getting individual site profiles for select year')
    startTime = datetime.datetime.now()
    df_rep = df_sc[['region','class',profile_id_col,'timezone']].copy().reset_index(drop=True)
    df_rep = df_rep.rename(columns={profile_id_col:'rep_gen_gid'})
    df_rep['timezone'] = df_rep['timezone'].astype(int)
    h5 = tables.open_file(rev_case_path + '/' + rev_prefix + '_rep_profiles_' + str(select_year) + '.h5', 'r', driver=driver)
    reps_arr = h5.root[profile_dset][:]
    reps_arr = reps_arr[:, df_rep['rep_gen_gid'].tolist()].copy()
    if 'scale_factor' in h5.root[profile_dset].attrs:
        scale = h5.root[profile_dset].attrs['scale_factor']
        reps_arr = reps_arr / scale
    h5.close()
    avgs_arr = reps_arr.copy()
    logger.info('Done getting profiles: '+ str(datetime.datetime.now() - startTime))
    return df_rep, avgs_arr, reps_arr

def get_profiles_allyears(df_rep, rev_case_path, rev_prefix, hourly_out_years, profile_dset, driver, profile_dir):
    #Based on the representative profiles selected in get_profiles(), gather the profiles for all other years
    logger.info('Getting multiyear profiles...')
    startTime = datetime.datetime.now()
    idls = df_rep['rep_gen_gid'].tolist()
    reps_arr_out = np.empty((0, len(idls)))
    for year in hourly_out_years:
        h5path = os.path.join(
            rev_case_path, profile_dir, 
            '{}_rep_profiles_{}.h5'.format(
                rev_prefix if profile_dir == '' else profile_dir, year))
        with tables.open_file(h5path, 'r', driver=driver) as h5:
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

def save_time_outputs(df_cf, df_cf_ts, df_cfcorr_ts, reps_arr_out, df_rep, start_1am, out_dir, tech,
                      filetype='h5', compression_opts=4, dtype=cf.dtype):
    #Save performance characteristics (capacity factor means, standard deviations, and corrections) and hourly profiles.
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

    if 'csv' in filetype:
        df_hr.to_csv(out_dir + 'results/' + tech + '.csv.gz')
    else:
        with h5py.File(os.path.join(out_dir,'results','{}.h5'.format(tech)), 'w') as f:
            f.create_dataset(
                'cf', data=df_hr, dtype=dtype,
                ### https://docs.h5py.org/en/stable/high/dataset.html#dataset-compression
                compression='gzip', compression_opts=compression_opts,
                ### chunking may speed up individual column reads, but slows down write;
                ### for now we do not use chunking
                # chunks=(df_windons.shape[0],1), 
            )
            f.create_dataset('columns', data=df_hr.columns, dtype=h5py.special_dtype(vlen=str))
            f.create_dataset('index', data=df_hr.index, dtype=int)

    df_rep.to_csv(out_dir + 'results/' + tech + '_rep_profiles_meta.csv', index=False)
    logger.info('Done saving time-dependent outputs: '+ str(datetime.datetime.now() - startTime))

if __name__== '__main__':
    #%% Initial setup - copy input files, create output directories
    startTime = datetime.datetime.now()
    this_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    out_dir = this_dir_path + 'out/' + cf.out_dir
    setup(
        this_dir_path=this_dir_path, out_dir=out_dir,
        paths=[cf.timeslice_path, cf.class_path, cf.reg_map_path])
    #%% Get supply curves
    df_sc = get_supply_curve_and_preprocess(
        tech=cf.tech, rev_case_path=cf.rev_case_path, rev_prefix=cf.rev_prefix, reg_col=cf.reg_col,
        profile_id_col=cf.profile_id_col, reg_out_col=cf.reg_out_col,
        reg_map_path=cf.reg_map_path, min_cap=cf.min_cap,
        individual_sites=cf.individual_sites, existing_sites=cf.existing_sites,
        start_year=cf.start_year, filter_cols=cf.filter_cols,
        test_mode=cf.test_mode,test_filters=cf.test_filters)
    #%% Add classes
    df_sc = add_classes(df_sc=df_sc, class_path=cf.class_path)
    #%% Add bins
    df_sc = add_bins(
        df_sc=df_sc, individual_sites=cf.individual_sites, bin_group_cols=cf.bin_group_cols,
        bin_col=cf.bin_col, bin_num=cf.bin_num, bin_method=cf.bin_method, tech=cf.tech)
    #%% Save the supply curve
    save_sc_outputs(
        df_sc=df_sc, individual_sites=cf.individual_sites, existing_sites=cf.existing_sites,
        start_year=cf.start_year, bin_col=cf.bin_col, out_dir=out_dir, tech=cf.tech,
        reg_map_path=cf.reg_map_path)
    #%% Get the profiles
    if cf.individual_sites:
        df_rep, avgs_arr, reps_arr = get_individual_profiles(
            df_sc=df_sc, rev_case_path=cf.rev_case_path, rev_prefix=cf.rev_prefix,
            select_year=cf.select_year, profile_dset=cf.profile_dset,
            profile_id_col=cf.profile_id_col, driver=cf.driver)
    else:
        df_rep, avgs_arr, reps_arr = get_profiles(
            df_sc=df_sc, rev_case_path=cf.rev_case_path, rev_prefix=cf.rev_prefix,
            select_year=cf.select_year, profile_dset=cf.profile_dset,
            profile_id_col=cf.profile_id_col, profile_weight_col=cf.profile_weight_col,
            rep_profile_method=cf.rep_profile_method, driver=cf.driver,
            gather_method=cf.gather_method, profile_dir=cf.profile_dir)
    reps_arr_out = get_profiles_allyears(
        df_rep=df_rep, rev_case_path=cf.rev_case_path, rev_prefix=cf.rev_prefix,
        hourly_out_years=cf.hourly_out_years, profile_dset=cf.profile_dset, driver=cf.driver,
        profile_dir=cf.profile_dir)
    #%% Shift timezones
    reps_arr = shift_timezones(
        arr=reps_arr, df_rep=df_rep,
        source_timezone=cf.resource_source_timezone, output_timezone=cf.agg_outputs_timezone)
    reps_arr_out = shift_timezones(
        arr=reps_arr_out, df_rep=df_rep,
        source_timezone=cf.resource_source_timezone, output_timezone=cf.hourly_outputs_timezone)
    avgs_arr = shift_timezones(
        arr=avgs_arr, df_rep=df_rep,
        source_timezone=cf.resource_source_timezone, output_timezone=cf.agg_outputs_timezone)
    #%% Get timeslice outputs
    df_cf, df_cf_ts, df_cfcorr_ts = calc_performance(
        avgs_arr=avgs_arr, reps_arr=reps_arr, df_rep=df_rep, timeslice_path=cf.timeslice_path,
        cfmean_type=cf.cfmean_type, add_h17=cf.add_h17)
    #%% Save timeslice outputs
    save_time_outputs(
        df_cf=df_cf, df_cf_ts=df_cf_ts, df_cfcorr_ts=df_cfcorr_ts, reps_arr_out=reps_arr_out,
        df_rep=df_rep, start_1am=cf.start_1am, out_dir=out_dir, tech=cf.tech,
        filetype=cf.filetype, compression_opts=cf.compression_opts, dtype=cf.dtype)
    logger.info('All done! total time: '+ str(datetime.datetime.now() - startTime))
