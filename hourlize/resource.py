#%% Imports
import argparse
import pandas as pd
import numpy as np
import sklearn.cluster as sc
import datetime
import os
import sys
import shutil
import json
import logging
import h5py
from collections import OrderedDict
from types import SimpleNamespace 

#%% Functions
def copy_rev_jsons(outpath, rev_jsons, rev_path):
    os.makedirs(os.path.join(outpath, 'inputs', 'rev_configs'), exist_ok=True)
    for jsonfile in rev_jsons:
        try:
            shutil.copy2(
                os.path.join(rev_path, jsonfile),
                os.path.join(outpath, 'inputs', 'rev_configs', os.path.basename(jsonfile)),
            )
        except FileNotFoundError as err:
            print(f"WARNING: {err}")
    print('Done copying rev json files')

def get_supply_curve_and_preprocess(tech, sc_file, rev_prefix, reg_col, reg_out_col, reg_map_file, min_cap, 
                                    capacity_col, existing_sites, state_abbrev, start_year, 
                                    filter_cols={}, rev_id_cols=["sc_point_gid"], test_mode=False, test_filters={}):
    #Retrieve and filter the supply curve. Also, add a 'region' column, apply minimum capacity thresholds, and apply test mode if necessary.
    print('Reading supply curve inputs and filtering...')
    startTime = datetime.datetime.now()
    df = pd.read_csv(sc_file, low_memory=False)
    #Add 'capacity' column to match specified capacity_col
    df['capacity'] = df[capacity_col]
    cnty_na_cond = df['cnty_fips'].isna()
    cnty_na_count = len(df[cnty_na_cond])
    if(cnty_na_count > 0):
        print("WARNING: " + str(cnty_na_count) + " site(s) don't have cnty_fips. Removing them now.")
        df = df[~cnty_na_cond].copy()
    df['cnty_fips'] = df['cnty_fips'].astype(int)
    for k in filter_cols.keys():
        #Apply any filtering of the supply curve, e.g. to select onshore or offshore wind.
        if filter_cols[k][0] == '=':
            df = df[df[k] == filter_cols[k][1]].copy()
        elif filter_cols[k][0] == '>':
            df = df[df[k] > filter_cols[k][1]].copy()
        elif filter_cols[k][0] == '<':
            df = df[df[k] < filter_cols[k][1]].copy()
    if 'dist_to_coast' in df:
        df['dist_to_coast'] /= 1000 #converting from meters to km
    #Define region    
    if reg_out_col == 'cnty_fips':
        #For county-level supply curves create region names based on FIPS
        df['region'] = 'p'+df.cnty_fips.astype(str).map('{:>05}'.format)
    elif reg_out_col is not reg_col:
        #This means we must map the regions from reg_col to reg_out_col
        df_map = pd.read_csv(reg_map_file, low_memory=False, usecols=[reg_col,reg_out_col])
        df = pd.merge(left=df, right=df_map, how='left', on=[reg_col], sort=False)
        df.rename(columns={reg_out_col:'region'}, inplace=True)
    else:
        df['region'] = df[reg_col]
    if existing_sites != None:
        print('Assigning existing sites...')
        #Read in existing sites and filter
        df_exist = pd.read_csv(existing_sites, low_memory=False)
        df_exist = df_exist[
            ['tech','TSTATE','reeds_ba','resource_region','Unique ID',
            'T_LONG','T_LAT','cap','StartYear','RetireYear']
        ].rename(columns={
            'TSTATE':'STATE', 'T_LAT':'LAT', 'T_LONG':'LONG', 'reeds_ba':'pca',
            'Unique ID':'UID', 'StartYear':'Commercial.Online.Year',
        }).copy()
        df_exist = df_exist[(df_exist['tech'].str.lower() == tech) & (df_exist['RetireYear'] > start_year)].reset_index(drop=True)
        df_exist['LONG'] = df_exist['LONG'] * -1
        df_exist.sort_values('cap', ascending=False, inplace=True)
        #Map the state codes of df_exist to the state names in df
        df_cp = df.copy()
        df_st = pd.read_csv(state_abbrev, low_memory=False)
        dict_st = dict(zip(df_st['ST'], df_st['State']))
        df_exist['STATE'] = df_exist['STATE'].map(dict_st)
        df_cp = df_cp[rev_id_cols + ['state','latitude','longitude','capacity']].copy()
        df_cp['existing_capacity'] = 0.0
        df_cp['existing_uid'] = 0
        df_cp['online_year'] = 0
        df_cp['retire_year'] = 0
        df_cp_out = pd.DataFrame()
        #Restrict matching to within the same State
        for st in df_exist['STATE'].unique():
            print('Existing sites state: ' + st)
            df_exist_st = df_exist[df_exist['STATE'] == st].copy()
            df_cp_st = df_cp[df_cp['state'] == st].copy()
            for i_exist, r_exist in df_exist_st.iterrows():
                #Current way to deal with lats and longs that don't exist
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
                    # TODO: handle missing UIDs
                    try:
                        df_cp_st.at[i_avail, 'existing_uid'] = r_exist['UID']
                    except:
                        df_cp_st.at[i_avail, 'existing_uid'] = 0
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
                    print('WARNING: Existing site shortfall: ' + str(exist_cap_remain))
                #Build output and take the available sites with existing capacity out of consideration for the next exisiting site
                df_cp_out_add = df_cp_st[df_cp_st['existing_capacity'] > 0].copy()
                df_cp_out = pd.concat([df_cp_out, df_cp_out_add], sort=False).reset_index(drop=True)
                df_cp_st = df_cp_st[df_cp_st['existing_capacity'] == 0].copy()
        df_cp_out['exist_mi_diff'] = df_cp_out['mi_sq']**0.5
        df_cp_out = df_cp_out[rev_id_cols + ['existing_capacity', 'existing_uid', 'online_year', 'retire_year', 'exist_mi_diff']].copy()
        df = pd.merge(left=df, right=df_cp_out, how='left', on=rev_id_cols, sort=False)
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
    print('Done reading supply curve inputs and filtering: '+ str(datetime.datetime.now() - startTime))
    return df

def add_classes(df_sc, class_path, class_bin, class_bin_col, class_bin_method, class_bin_num):
    #Add 'class' column to supply curve, based on specified class definitions in class_path.
    print('Adding classes...')
    startTime = datetime.datetime.now()
    #Create class column.
    if class_path == None:
        df_sc['class'] = '1'
    else:
        df_sc['class'] = 'NA' #Initialize to NA to make sure we have full coverage of classes here.
        df_class = pd.read_csv(class_path, index_col='class')
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
    # Add dynamic, region-specific class bins based on class_bin_method
    if class_bin:
        #In this case, class names in class_path must be numbered, starting at 1
        df_sc = df_sc.rename(columns={'class':'class_orig'})
        df_sc['class_orig'] = df_sc['class_orig'].astype(int)
        df_sc = (df_sc.groupby(['class_orig'], sort=False)
                      .apply(get_bin, bin_in_col=class_bin_col, bin_out_col='class_bin', weight_col= "capacity",
                             bin_num=class_bin_num, bin_method=class_bin_method)
                      .reset_index(drop=True))
        df_sc['class'] = (df_sc['class_orig'] - 1) * class_bin_num + df_sc['class_bin']
    print('Done adding classes: '+ str(datetime.datetime.now() - startTime))
    return df_sc

def get_bin(df_in, bin_in_col, bin_out_col, weight_col, bin_num, bin_method):
    df = df_in.copy()
    ser = df[bin_in_col]
    #If we have less than or equal unique points than bin_num, we simply group the points with the same values.
    if ser.unique().size <= bin_num:
        bin_ser = ser.rank(method='dense')
        df[bin_out_col] = bin_ser.values
    elif bin_method == 'kmeans':
        nparr = ser.to_numpy().reshape(-1,1)
        weights = df[weight_col].to_numpy()
        kmeans = sc.KMeans(n_clusters=bin_num, random_state=0, n_init=10).fit(nparr, sample_weight=weights)
        bin_ser = pd.Series(kmeans.labels_)
        #but kmeans doesn't necessarily label in order of increasing value because it is 2D,
        #so we replace labels with cluster centers, then rank
        kmeans_map = pd.Series(kmeans.cluster_centers_.flatten())
        bin_ser = bin_ser.map(kmeans_map).rank(method='dense')
        df[bin_out_col] = bin_ser.values
    elif bin_method == 'equal_cap_man':
        #using a manual method instead of pd.cut because i want the first bin to contain the
        #first sc point regardless, even if its weight_col value is more than the capacity of the bin,
        #and likewise for other bins, so i don't skip any bins.
        orig_index = df.index
        df.sort_values(by=[bin_in_col], inplace=True)
        cumcaps = df[weight_col].cumsum().tolist()
        totcap = df[weight_col].sum()
        vals = df[bin_in_col].tolist()
        bins = []
        curbin = 1
        for i, _v in enumerate(vals):
            bins.append(curbin)
            if cumcaps[i] >= totcap*curbin/bin_num:
                curbin += 1
        df[bin_out_col] = bins
        df = df.reindex(index=orig_index) #we need the same index ordering for apply to work.
    elif bin_method == 'equal_cap_cut':
        #Use pandas.cut with cumulative capacity in each class. This will assume equal capacity bins
        #to bin the data.
        orig_index = df.index
        df.sort_values(by=[bin_in_col], inplace=True)
        df['cum_cap'] = df[weight_col].cumsum()
        bin_ser = pd.cut(df['cum_cap'], bin_num, labels=False)
        bin_ser = bin_ser.rank(method='dense')
        df[bin_out_col] = bin_ser.values
        df = df.reindex(index=orig_index) #we need the same index ordering for apply to work.
    df[bin_out_col] = df[bin_out_col].astype(int)
    return df

def add_cost(df_sc, tech, upv_type, bin_col, reg_out_col):

    # for PV costs make sure that costs are based on the appropriate capacity type (either DC or AC)
    if tech == "upv":
        # default capital costs are $/kW-DC, convert to $ ($/kW-DC * 1E3 kW/MW * MW-DC = $)
        df_sc['capital_cost'] = df_sc['capital_cost'] * 1000 * df_sc['capacity_mw_dc']
        if upv_type == 'ac':
            # default network upgrade costs are $/MW-AC, so leave as is
            df_sc['trans_cap_cost_per_mw'] = df_sc['trans_cap_cost_per_mw_ac']
            df_sc['reinforcement_cost_per_mw'] = df_sc['reinforcement_cost_per_mw_ac']
            # land use costs are $/MW-DC, convert to $/MW-AC
            df_sc['land_cap_adder_per_mw'] = df_sc['land_cap_adder_per_mw'] * (df_sc['capacity_mw_dc'] / df_sc['capacity_mw_ac'])
        else:
            # default network upgrade costs are $/MW-AC, convert to $/MW-DC
            df_sc['trans_cap_cost_per_mw'] = df_sc['trans_cap_cost_per_mw_ac'] * (df_sc['capacity_mw_ac'] / df_sc['capacity_mw_dc'])
            df_sc['reinforcement_cost_per_mw'] = df_sc['reinforcement_cost_per_mw_ac'] * (df_sc['capacity_mw_ac'] / df_sc['capacity_mw_dc'])

    # set network reinforcement costs to zero if running county-level supply curves
    if reg_out_col == 'cnty_fips':
        print('Running county-level supply curves, so setting any network reinforcement costs to zero.')
        df_sc['reinforcement_cost_per_mw'] = 0 

    # Generate the supply_curve_cost_per_mw column. Special bin_col values correspond to
    # a calculation using one or more columns, but the default is to use the bin_col
    # directly as supply_curve_cost_per_mw
    if bin_col == 'combined_eos_trans':
        #Note that capital_cost includes eos_mult and reg_mult
        df_sc['trans_adder_per_MW'] = df_sc['trans_cap_cost_per_mw'] + df_sc['reinforcement_cost_per_mw']
        df_sc['capital_adder_per_MW'] = (df_sc['capital_cost']/df_sc['capacity'] 
                                          - df_sc['capital_cost']/(df_sc['capacity']*df_sc['eos_mult']*df_sc['reg_mult'])
                                          + df_sc['land_cap_adder_per_mw'].fillna(0)
                                        )
        df_sc['supply_curve_cost_per_mw'] = df_sc['trans_adder_per_MW'] + df_sc['capital_adder_per_MW']
    elif bin_col == 'combined_off_ons_trans':
        # 'mean_export' and 'mean_array' are the $ costs for a full (unexcluded) offshore wind farm (600 MW = 15 MW/turbine x 40 turbines) at each site.
        df_sc['supply_curve_cost_per_mw'] = (df_sc['mean_export'] + df_sc['mean_array']) / (df_sc['mean_system_capacity'] * 40) * 1000 + df_sc['trans_cap_cost_per_mw'] + df_sc['reinforcement_cost_per_mw']
    elif bin_col == 'combined_trans':
        df_sc['supply_curve_cost_per_mw'] = df_sc['trans_cap_cost_per_mw'] + df_sc['reinforcement_cost_per_mw']
    else:
        #By default use the specified column as supply_curve_cost_per_mw
        df_sc['supply_curve_cost_per_mw'] = df_sc[bin_col]

    print('Done adding supply-curve cost column.')

    return df_sc

def save_sc_outputs(
        df_sc, existing_sites, start_year, outpath, tech,
        reg_map_file, distance_cols, cost_adder_components, subtract_exog, rev_id_cols):
    #Save resource supply curve outputs
    print('Saving supply curve outputs...')
    startTime = datetime.datetime.now()
    #Create local copy of df_sc so that we don't modify the df_sc passed by reference
    df_sc = df_sc.copy()
    df_sc.to_csv(os.path.join(outpath, 'results', tech + '_supply_curve_raw.csv'), index=False)
    #Round now to prevent infeasibility in model because existing (pre-2010 + prescribed) capacity is slightly higher than supply curve capacity
    decimals = 3
    df_sc[['capacity','existing_capacity']] = df_sc[['capacity','existing_capacity']].round(decimals)
    if existing_sites:
        # bincol = ['sc_point_gid'] if exog_bin else []
        df_exist = df_sc[df_sc['existing_capacity'] > 0].copy()
        #Exogenous (pre-start-year) capacity output
        df_exog = df_exist[df_exist['online_year'] < start_year].copy()
        # # Write the full existing-capacity table
        # df_exog[[
        #     'region','class','bin','sc_point_gid','cnty_fips','online_year','retire_year',
        #     'dist_km','trans_cap_cost_per_mw','supply_curve_cost_per_mw','existing_capacity',
        # ]].to_csv(os.path.join(outpath, 'results', tech+'_existing_cap_pre{}.csv'.format(start_year)), index=False)
        # Aggregate existing capacity to (i,rs,t)
        if not df_exog.empty:
            df_exog = df_exog[rev_id_cols + ['class','region','retire_year','existing_capacity']].copy()
            max_exog_ret_year = df_exog['retire_year'].max()
            ret_year_ls = list(range(start_year,max_exog_ret_year + 1))
            df_exog = df_exog.pivot_table(index=rev_id_cols + ['class','region'], columns='retire_year', values='existing_capacity')
            # Make a column for every year until the largest retirement year
            df_exog = df_exog.reindex(columns=ret_year_ls).fillna(method='bfill', axis='columns')
            df_exog = pd.melt(
                df_exog.reset_index(), id_vars= rev_id_cols + ['class','region'],
                value_vars=ret_year_ls, var_name='year', value_name='capacity')
            df_exog = df_exog[df_exog['capacity'].notnull()].copy()
            df_exog['tech'] = tech + '_' + df_exog['class'].astype(str)
            df_exog = df_exog[rev_id_cols + ['tech','region','year','capacity']].copy()
            df_exog = df_exog.groupby(['tech','region','year'] + rev_id_cols, sort=False, as_index=False).sum()
            df_exog['capacity'] =  df_exog['capacity'].round(decimals)
            df_exog = df_exog.sort_values(['year'] + rev_id_cols)
            df_exog.to_csv(os.path.join(outpath, 'results', tech + '_exog_cap.csv'), index=False)
        #Prescribed capacity output
        df_pre = df_exist[df_exist['online_year'] >= start_year].copy()
        if not df_pre.empty:
            df_pre = df_pre[['region','online_year','existing_capacity']].copy()
            df_pre = df_pre.rename(columns={'online_year':'year', 'existing_capacity':'capacity'})
            df_pre = df_pre.groupby(['region','year'], sort=False, as_index =False).sum()
            df_pre['capacity'] =  df_pre['capacity'].round(decimals)
            df_pre = df_pre.sort_values(['year','region'])
            df_pre.to_csv(os.path.join(outpath, 'results', tech + '_prescribed_builds.csv'), index=False)
        #Reduce supply curve based on exogenous (pre-start-year) capacity
        if subtract_exog:
            criteria = (df_sc['online_year'] > 0) & (df_sc['online_year'] < start_year)
            df_sc.loc[criteria, 'capacity'] = (
                df_sc.loc[criteria, 'capacity'] - df_sc.loc[criteria, 'existing_capacity'])

    keepcols = ['capacity', 'supply_curve_cost_per_mw'] + cost_adder_components + distance_cols

    df_sc_out = df_sc[['region','class'] + rev_id_cols + keepcols].copy()
    df_sc_out[keepcols] = df_sc_out[keepcols].round(decimals)
    df_sc_out = df_sc_out.sort_values(['region','class'] + rev_id_cols)
    df_sc_out.to_csv(os.path.join(outpath, 'results', tech + '_supply_curve.csv'), index=False)

    print('Done saving supply curve outputs: '+ str(datetime.datetime.now() - startTime))

def get_profiles_allyears_weightedave(
        df_sc, rev_path, rev_prefix, hourly_out_years, profile_dset,
        profile_dir, profile_id_col, profile_weight_col, select_year, profile_file_format, single_profile):
    """
    Get the weighted average profiles for all years rather than representative profiles
    """
    print('Getting multiyear profiles...')
    startTime = datetime.datetime.now()
    ### Create df_rep, the dataframe to map reigon,class to timezone, using capacity weighting to assign timezone.
    def wm(x):
        return np.average(x, weights=df_sc.loc[x.index, 'capacity']) if df_sc.loc[x.index, 'capacity'].sum() > 0 else 0
    df_rep = df_sc.groupby(['region','class'], as_index =False).agg({'timezone':wm})
    df_rep['timezone'] = df_rep['timezone'].round().astype(int)
    #%% Get the weights
    dfweight_regionclass = df_sc.groupby(['region','class'])[profile_weight_col].sum()
    #%% consolidate sc to dimensions used to match with profile
    df_sc_grouped = df_sc.groupby(['region','class',profile_id_col], as_index=False)[profile_weight_col].sum()
    dfweight_id = (
        df_sc_grouped[['region','class',profile_weight_col,profile_id_col]]
        .merge(
            dfweight_regionclass, left_on=['region','class'], right_index=True,
            suffixes=['_index','_regionclass'])
        .sort_values(profile_id_col)
    )
    dfweight_id['weight'] = (
        dfweight_id[profile_weight_col+'_index']
        / dfweight_id[profile_weight_col+'_regionclass'])
    colweight = dfweight_id.set_index(profile_id_col).weight.copy()
    id_to_regionclass = pd.Series(
        index=dfweight_id[profile_id_col],
        data=zip(dfweight_id.region, dfweight_id['class']),
    )
    ### Load hourly profile for each year
    dfyears = []
    for year in hourly_out_years:
        if single_profile: #only one profile file
            h5path = os.path.join(
                rev_path, profile_dir,
                f'{rev_prefix}_bespoke.h5')
            with h5py.File(h5path, 'r') as h5:
                dfall = pd.DataFrame(h5[f'cf_profile-{year}'][:])
                dfall = dfall/h5[f'cf_profile-{year}'].attrs['scale_factor']
                df_meta = pd.DataFrame(h5['meta'][:])
        else:
            h5path = os.path.join(
                rev_path, profile_dir, f'{profile_file_format}.h5')
            with h5py.File(h5path, 'r') as h5:
                dfall = pd.DataFrame(h5[profile_dset][:])
                df_meta = pd.DataFrame(h5['meta'][:])
        ### Check that meta and profile are the same dimensions
        assert dfall.shape[1] == df_meta.shape[0], f"Dimensions of profile ({dfall.shape[1]}) do not match meta file dimensions ({df_meta.shape[0]}) in {profile_file_format}_{year}.h5"        
        ### Change hourly profile column names from simple index to associated sc_point_gid
        dfall.columns = dfall.columns.map(df_meta[profile_id_col])
        ### Multiply each column by its weight, then drop the unweighted columns
        dfall *= colweight
        dfall.dropna(axis=1, inplace=True)
        ### Switch to (region,class) index
        dfall.columns = dfall.columns.map(id_to_regionclass)
        ### Sum by (region,class)
        dfall = dfall.T.groupby(level=[0,1]).sum().T
        ### Keep columns in the (region,class) order from df_rep
        dfall = dfall[list(zip(df_rep.region, df_rep['class']))].copy()
        dfyears.append(dfall)
        #If this is select_year, save avgs_arr for output
        if year == select_year:
            avgs_arr = dfall.values
        print('Done with ' + str(year))

    ### Concatenate individual years, drop indices
    reps_arr_out = pd.concat(dfyears, axis=0).values
    print('Done getting multiyear profiles: '+ str(datetime.datetime.now() - startTime))
    return df_rep, reps_arr_out, avgs_arr

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

def save_time_outputs(reps_arr_out, df_rep, start_1am, outpath, tech,
                      filetype='h5', compression_opts=4, dtype=np.float16):
    #Save performance characteristics (capacity factor means, standard deviations, and corrections) and hourly profiles.
    print('Saving time-dependent outputs...')
    startTime = datetime.datetime.now()
    df_hr = pd.DataFrame(reps_arr_out.round(4))
    df_rep['class_reg'] = df_rep['class'].astype(str) + '_' + df_rep['region'].astype(str)
    df_hr.columns = df_rep['class_reg']
    if start_1am is True:
        #to start at 1am instead of 12am, roll the data by -1 and add 1 to index
        df_hr.index = df_hr.index + 1
        for col in df_hr:
            df_hr[col] = np.roll(df_hr[col], -1)

    if 'csv' in filetype:
        df_hr.to_csv(os.path.join(outpath, 'results', tech + '.csv.gz'))
    else:
        # validate and convert dtype entry
        if isinstance(dtype, str):
            if dtype not in ["np.float16", "np.float32"]:
                print(f"{dtype} is not a valid dtype entry. Reverting to 'np.float16'")
                dtype = np.float16
            else:
                dtype = getattr(np, dtype.replace("np.", "")) 

        with h5py.File(os.path.join(outpath,'results',f'{tech}.h5'), 'w') as f:
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

    df_rep.to_csv(os.path.join(outpath, 'results', tech + '_rep_profiles_meta.csv'), index=False)
    print('Done saving time-dependent outputs: '+ str(datetime.datetime.now() - startTime))

def copy_outputs(outpath, reedspath, sc_file, sc_path, casename, reg_out_col,
                 copy_to_reeds, copy_to_shared, rev_jsons, configpath):

    #Save outputs to the shared drive and to this reeds repo.
    print('Copying outputs to shared drive and/or reeds repo')
    startTime = datetime.datetime.now()

    # tech should be the first part of the case name
    tech = casename.split("_")[0]
    # case is the rest of the case (usually access case + regionality)
    case = casename.replace(tech+"_", "")
    
    resultspath = os.path.join(outpath, 'results')
    inputspath = os.path.join(reedspath, 'inputs')

    if copy_to_reeds:
   
        #Supply curve
        shutil.copy2(
            os.path.join(resultspath, f'{tech}_supply_curve.csv'),
            os.path.join(inputspath, 'supplycurvedata',f'{tech}_supply_curve-{case}.csv')
        )
        #Hourly profiles
        if reg_out_col == "cnty_fips" or "county" in casename:
            print("""County-level profiles are not kept in the repo due to their size 
                    and will not be copied to ReEDS. The profiles should be saved to
                    the shared drive by setting 'copy_to_shared' to True.""")
        else:
            shutil.copy2(
                os.path.join(resultspath, f'{tech}.h5'),
                os.path.join(inputspath,'variability','multi_year',f'{tech}-{case}.h5')
            )
        #Prescribed builds and exogenous capacity (if they exist)
        try:
            shutil.copy2(
                os.path.join(resultspath, f'{tech}_prescribed_builds.csv'),
                os.path.join(inputspath,'capacitydata',f'{tech}_prescribed_builds_{case}.csv')
            )
        except:
            print('WARNING: No prescribed builds')
        try:
            df = pd.read_csv(os.path.join(resultspath,f'{tech}_exog_cap.csv'))
            df.rename(columns={df.columns[0]: '*'+str(df.columns[0])}, inplace=True)
            df.to_csv(
                os.path.join(inputspath,'capacitydata',f'{tech}_exog_cap_{case}.csv'),
                index=False
            )
        except:
            print('WARNING: No exogenous capacity')

        ## Metadata
        # rev configs
        meta_path = os.path.join(inputspath,'supplycurvedata','metadata',f'{casename}')
        if os.path.exists(meta_path):
            shutil.rmtree(meta_path)
        os.makedirs(meta_path)
        for metafile in rev_jsons:
            try:
                shutil.copy(
                    os.path.join(outpath, 'inputs', 'rev_configs', os.path.basename(metafile)),
                    os.path.join(meta_path,os.path.basename(metafile)),
                )
            except FileNotFoundError as err:
                print(err)
        
        # hourlize config
        shutil.copy(
                configpath,
                os.path.join(meta_path,os.path.basename(configpath)),
            )

        # Copy the readme file if there is one
        for ext in ['.yaml', '.yml', '.md', '.txt', '']:
            try:
                shutil.copy2(
                    os.path.join(outpath,'inputs','readme'+ext),
                    os.path.join(meta_path,''),
                )
            except:
                pass

    if copy_to_shared:
        shared_drive_path = os.path.join(sc_path, os.path.basename(os.path.normpath(outpath)))
        #Create output directory, creating backup if one already exists.
        if os.path.exists(shared_drive_path):
            time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            os.rename(shared_drive_path, shared_drive_path + '-archive-'+time)
        shutil.copytree(outpath, shared_drive_path)
        
    print('Done copying outputs to shared drive and/or reeds repo: '+ str(datetime.datetime.now() - startTime))

def map_supplycurve(
        tech, reg_out_col, sc_file, outpath, reedspath,
        cm=None, dpi=None,
    ):
    #%%### Imports
    ## Turn off loggers for imported packages
    for i in ['matplotlib','shapely','fiona','pyproj']:
        logging.getLogger(i).setLevel(logging.CRITICAL)
    import pandas as pd
    import matplotlib.pyplot as plt
    import os, site
    import geopandas as gpd
    os.environ['PROJ_NETWORK'] = 'OFF'

    site.addsitedir(os.path.join(reedspath,'postprocessing'))
    import plots
    plots.plotparams()
    os.makedirs(os.path.join(outpath, 'plots'), exist_ok=True)

    #%%### Format inputs
    if not cm:
        cmap = plt.cm.gist_earth_r
    else:
        cmap = cm
    ms = {'wind-ofs':1.75, 'wind-ons':2.65, 'upv':2.65}[tech]
    
    labels = {
        'capacity_mw': 'Available capacity [MW]',
        'trans_cap_cost_per_kw': 'Spur-line cost [$/kW]',
        'reinforcement_cost_per_kw': 'Reinforcement cost [$/kW]',
        'interconnection_cost_per_kw': 'Interconnection cost [$/kW]',
        'land_cap_adder_per_kw': 'Land cost adder [$/kW]',
        'reg_mult': 'Regional multipler',
        'mean_cf': 'Capacity factor [.]',
        'dist_km': 'Spur-line distance [km]',
        'reinforcement_dist_km': 'Reinforcement distance [km]',
        'area_sq_km': 'Area [km^2]',
        'mean_lcoe': 'LCOE [$/MWh]',
        'lcot': 'LCOT [$/MWh]',
        'dist_to_coast': 'Distance to coast [km?]',
    }
    vmax = {
        ## use 402 for wind with 6 MW turbines
        'capacity_mw': {'wind-ons':400.,'wind-ofs':600.,'upv':4000.}[tech],
        'trans_cap_cost_per_kw': 2000.,
        'reinforcement_cost_per_kw': 2000.,
        'interconnection_cost_per_kw': 2000.,
        'land_cap_adder_per_kw': 2000.,
        'reg_mult': 1.5,
        'mean_cf': 0.60,
        'dist_km': 200.,
        'reinforcement_dist_km': 200.,
        'area_sq_km': 11.5**2,
        'mean_lcoe': 100.,
        'lcot': 100.,
        'dist_to_coast': 437.,
    }
    vmin = {
        'capacity_mw': 0.,
        'trans_cap_cost_per_kw': 0.,
        'reinforcement_cost_per_kw': 0.,
        'interconnection_cost_per_kw': 0.,
        'land_cap_adder_per_kw': 0.,
        'reg_mult': 0.5,
        'mean_cf': 0.,
        'dist_km': 0.,
        'reinforcement_dist_km': 0.,
        'area_sq_km': 0.,
        'mean_lcoe': 0.,
        'lcot': 0.,
        'dist_to_coast': 0.,
    }
    background = {
        'capacity_mw': False,
        'trans_cap_cost_per_kw': True,
        'reinforcement_cost_per_kw': True,
        'interconnection_cost_per_kw': True,
        'land_cap_adder_per_kw': True,
        'reg_mult': True,
        'mean_cf': True,
        'dist_km': True,
        'reinforcement_dist_km': True,
        'area_sq_km': False,
        'mean_lcoe': True,
        'lcot': True,
        'dist_to_coast': True,
    }

    #%%### Load data
    dfsc = pd.read_csv(sc_file, index_col='sc_point_gid')

    ### adjust some column names as needed 
    if tech == 'upv':
        dfsc.rename(columns={'reinforcement_cost_per_mw_ac':'reinforcement_cost_per_mw',
                             'trans_cap_cost_per_mw_ac': 'trans_cap_cost_per_mw'}, inplace=True)
        
        # land use costs are $/MW-DC, convert to $/MW-AC
        dfsc['land_cap_adder_per_mw'] = (
            dfsc['land_cap_adder_per_mw']
            * (dfsc['capacity_mw_dc'] / dfsc['capacity_mw_ac'])
        )

    ### Convert to geopandas dataframe
    dfsc = plots.df2gdf(dfsc)

    #%% Load ReEDS regions
    if reg_out_col == 'cnty_fips':
        dfba = (
            gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','US_COUNTY_2022'))
            .set_index('rb'))
        dfba.rename(columns={'STCODE':'st'}, inplace=True)
        dfba['st'] = dfba['st'].str.lower()
    else:
        dfba = (
            gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','US_PCA'))
            .set_index('rb'))
    ### Aggregate to states
    dfstates = dfba.dissolve('st')
    ### Get the lakes
    lakes = gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','greatlakes.gpkg'))

    #%% Processing
    dfplot = dfsc.rename(columns={
        'capacity_mw_ac':'capacity_mw',
        'mean_cf_ac':'mean_cf',
        'trans_cap_cost_per_mw_ac':'trans_cap_cost_per_mw',
        'reinforcement_cost_per_mw_ac':'reinforcement_cost_per_mw',
    }).copy()
    ## Convert to $/kW
    dfplot['trans_cap_cost_per_kw'] = dfplot['trans_cap_cost_per_mw'] / 1000
    dfplot['reinforcement_cost_per_kw'] = dfplot['reinforcement_cost_per_mw'] / 1000
    dfplot['interconnection_cost_per_kw'] = (
        dfplot['trans_cap_cost_per_kw'] + dfplot['reinforcement_cost_per_kw'])
    dfplot['land_cap_adder_per_kw'] = dfplot['land_cap_adder_per_mw'] / 1000
    if 'dist_to_coast' in dfplot:
        dfplot['dist_to_coast'] /= 1000

    #%% Plot it
    for col in labels:
        if col not in dfplot:
            print(f"{col} is not in the supply curve table")
            continue
        plt.close()
        f,ax = plt.subplots(figsize=(12,9), dpi=dpi)
        ### Background
        if background[col]:
            dfba.plot(ax=ax, facecolor='C7', edgecolor='none', lw=0.3, zorder=-1e6)
        dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.3, zorder=1e6)
        dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.5, zorder=2e6)
        lakes.plot(ax=ax, edgecolor='#2CA8E7', facecolor='#D3EFFA', lw=0.2, zorder=-1)
        ### Map of data
        dfplot.plot(
            ax=ax, column=col,
            cmap=cmap, marker='s', markersize=ms, lw=0,
            legend=False, vmin=vmin[col], vmax=vmax[col],
        )
        ### Colorbar-histogram
        plots.addcolorbarhist(
            f=f, ax0=ax, data=dfplot[col].values,
            title=labels[col], cmap=cmap,
            vmin=vmin[col], vmax=vmax[col],
            orientation='horizontal', labelpad=2.1, cbarbottom=-0.06,
            cbarheight=0.7, log=False,
            ## use nbins=68 for wind with 6 MW turbines
            nbins=101, histratio=2,
            ticklabel_fontsize=20, title_fontsize=24,
            extend='neither',
        )
        ### Annotation
        ax.set_title(sc_file, fontsize='small', y=0.97)
        note = str(dfplot[col].describe().round(3))
        note = note[:note.index('\nName')]
        ax.annotate(note, (-1.05e6, -1.05e6), ha='right', va='top', fontsize=8)
        ### Formatting
        ax.axis('off')
        plt.savefig(os.path.join(outpath, 'plots', f'{tech}-{col}.png'), dpi=dpi)
        plt.close()
        print(f'mapped {col}')

#%% Run it
if __name__== '__main__':
    #%% load arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='', help='path to config file for this run')
    parser.add_argument('--nolog', '-nl', default=False, action='store_true',
                         help='turn off logging (helpful for using pdb)')
    args = parser.parse_args()
    configpath = args.config
    nolog = args.nolog
    startTime = datetime.datetime.now()

    #%% load config information
    with open(configpath, "r") as f:
        config = json.load(f, object_pairs_hook=OrderedDict)
    cf = SimpleNamespace(**config)

    #%% setup logging
    sys.path.insert(0, os.path.join(f'{cf.reedspath}', 'input_processing'))
    if not nolog:
        from ticker import toc, makelog
        log = makelog(scriptname=__file__, logpath=os.path.join(cf.outpath, f'log_{cf.batchcase}.txt'))

    #%% Make copies of rev jsons
    copy_rev_jsons(cf.outpath, cf.rev_jsons, cf.rev_path)
    
    #%% Get supply curves
    df_sc = get_supply_curve_and_preprocess(
        cf.tech, cf.sc_file, cf.rev_prefix, cf.reg_col, cf.reg_out_col, 
        cf.reg_map_file, cf.min_cap, cf.capacity_col, cf.existing_sites, cf.state_abbrev,
        cf.start_year, cf.filter_cols, cf.rev_id_cols, cf.test_mode, cf.test_filters)
    
    #%% Add classes
    df_sc = add_classes(
        df_sc, cf.class_path, cf.class_bin, cf.class_bin_col, 
        cf.class_bin_method, cf.class_bin_num)
    
    #%% Add bins
    df_sc = add_cost(df_sc, cf.tech, cf.upv_type, cf.bin_col, cf.reg_out_col)
    
    #%% Save the supply curve
    save_sc_outputs(
        df_sc, cf.existing_sites,cf.start_year, cf.outpath, cf.tech,
        cf.reg_map_file, cf.distance_cols, cf.cost_adder_components, cf.subtract_exog, cf.rev_id_cols)
    
    #%% Get the profiles
    df_rep, reps_arr_out, avgs_arr = get_profiles_allyears_weightedave(
        df_sc, cf.rev_path, cf.rev_prefix,
        cf.hourly_out_years, cf.profile_dset,
        cf.profile_dir, cf.profile_id_col,
        cf.profile_weight_col, cf.select_year, cf.profile_file_format, cf.single_profile)
    
    #%% Shift timezones
    reps_arr_out = shift_timezones(
        arr=reps_arr_out, df_rep=df_rep,
        source_timezone=cf.resource_source_timezone, output_timezone=cf.output_timezone)
    avgs_arr = shift_timezones(
        arr=avgs_arr, df_rep=df_rep,
        source_timezone=cf.resource_source_timezone, output_timezone=cf.output_timezone)
    
    #%% Save hourly profiles
    save_time_outputs(
        reps_arr_out,df_rep, cf.start_1am, cf.outpath, cf.tech,
        cf.filetype, cf.compression_opts, cf.dtype)
    
    #%% Map the supply curve
    try:
        map_supplycurve(
            cf.tech, cf.reg_out_col, cf.sc_file, cf.outpath, cf.reedspath,
            cm=None, dpi=None)
    except Exception as err:
        print(f'map_cupplycurve() failed with the following exception:\n{err}')
    
    #%% Copy outputs to ReEDS and/or the shared drive
    copy_outputs(
        cf.outpath, cf.reedspath, cf.sc_file, cf.sc_path, cf.casename, 
        cf.reg_out_col, cf.copy_to_reeds, cf.copy_to_shared, cf.rev_jsons, configpath)
    print('All done! total time: '+ str(datetime.datetime.now() - startTime))
