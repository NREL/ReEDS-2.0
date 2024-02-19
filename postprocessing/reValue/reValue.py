import gdxpds
import pandas as pd
import numpy as np
import h5py
import os
import sys
from pdb import set_trace as b
import datetime
import shutil

#User inputs
output_prices = True
res_marg_style = 'max_net_load_2012' # 'max_net_load_2012' is the only currently supported option. 'max_load_price', the other option, only works on older versions of ReEDS
netload_num_hrs = 50 #Number of hours to include for each season. Only relevant if res_marg_style='max_net_load_2012'
netload_time_style = 'hour' #'hour' or 'timeslice'. 'Timeslice' means apply reserve margin price to all hours of the timeslice(s) with the peak net load hour(s).

#Global inputs
this_dir_path = os.path.dirname(os.path.realpath(__file__))
#Create new directory for outputs
time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
output_dir = f'{this_dir_path}/outputs_{time}'
os.makedirs(output_dir)
shutil.copy2(f'{this_dir_path}/reValue.py', output_dir)
shutil.copy2(f'{this_dir_path}/scenarios.csv', output_dir)
ira_incentive = 17.39 #(2019$/MWh). 12.85 2004$/MWh from ReEDS alldata.gdx, converted to 2019$ using ReEDS deflator.csv (0.7389)
dollar_year_conv = 1.353388734 #ReEDS is in 2004$ and rev is in 2019$. Converting ReEDS data to 2019$ using ReEDS deflator.csv
rev_county_path = f'{this_dir_path}/../../hourlize/inputs/resource/county_map.csv'
df_rev_county = pd.read_csv(rev_county_path, usecols=['cnty_fips','reeds_ba'])
df_ba_tz = pd.read_csv(f'{this_dir_path}/../../hourlize/inputs/load/ba_timezone.csv')
ba_tz_map = dict(zip(df_ba_tz['ba'], df_ba_tz['timezone']))
rev_year = 2012

def get_prices():
    print('Reading ReEDS prices and quantities')
    #ReEDS hours start at 12am EST (UTC-5)
    df_p = pd.read_csv(f'{reeds_run_path}/outputs/reqt_price.csv')
    df_q = pd.read_csv(f'{reeds_run_path}/outputs/reqt_quant.csv')
    pq_cols = ['reqt','reqt_cat','reeds_ba','h','year']
    df_p.columns = pq_cols + ['price']
    df_q.columns = pq_cols + ['quant']
    if year not in df_p['year'].values:
        sys.exit(f'ERROR: Chosen year of {year} is not in this run: {reeds_run_path}')
    #Adjust price with inflation
    df_p['price'] *= dollar_year_conv
    df_pq = df_p.merge(df_q, on=pq_cols, how='outer')
    df_pq = df_pq.fillna(0)
    #Restrict to year in question
    df_pq = df_pq[df_pq['year']==year].copy()
    #Gather hmaps
    df_hmap = pd.read_csv(f'{reeds_run_path}/inputs_case/hmap_myr.csv')
    # df_hmap_7yr = pd.read_csv(f'{reeds_run_path}/inputs_case/hmap_7yr.csv')
    df_h_num_hrs = df_hmap.groupby('h')['hour'].count().reset_index().rename(columns={'hour':'num_hrs'})
    #Gather region map for mapping of bas to ccreg for reserve_margin
    df_ba_cc_map = df_hier_run[['*r','ccreg']].copy()
    df_ba_cc_map.columns = ['reeds_ba','ccreg']

    print('- Load prices and quantities')
    if r['tech'] == 'load':
        #In this case we want the linked load constraint, but note it is in $/MW so we need to convert to $/MWh
        df_pq_load = df_pq[df_pq['reqt'] == 'eq_loadcon'].copy()
        #Join with number of hours. This will get rid of the stress period timeslices
        df_pq_load = df_pq_load.merge(df_h_num_hrs, on='h', how='inner')
        #Divide price by num_hrs to convert to $/MWh
        df_pq_load['price'] = df_pq_load['price'] / df_pq_load['num_hrs']
        #Multiply quant by num_hrs to convert to MWh
        df_pq_load['quant'] = df_pq_load['quant'] * df_pq_load['num_hrs']
    else:
        #Already in $/MWh
        df_pq_load = df_pq[df_pq['reqt'] == 'load'].copy()
    df_p_load = df_pq_load.pivot_table(index=['h'], columns='reeds_ba', values='price').reset_index()
    df_q_load = df_pq_load.pivot_table(index=['h'], columns='reeds_ba', values='quant').reset_index()
    #Map to hours
    df_p_load_h = df_hmap[['h']].merge(df_p_load, on=['h'], how='left').drop(columns=['h'])

    print('- Reserve margin prices')
    #Originally in $/kW-yr so need to convert to $/MWh
    #TODO: Use stress periods or a better method.
    df_pq_rm = df_pq[df_pq['reqt'] == 'res_marg'].copy()
    df_pq_rm_adj = df_pq_rm.rename(columns={'h':'season'})
    df_seas_h_map = df_hmap[['season','h']].drop_duplicates()
    if res_marg_style == 'max_net_load_2012':
        #Read in net_load_2012 of the appropriate ReEDS Augur file.
        #The file we want is for the highest year that is lower than r['year']
        #TODO: Perhaps we should use the file that has the same year as r['year'],
        #depending on if it represents the system of that year better.
        aug_files = os.listdir(f'{reeds_run_path}/ReEDS_Augur/augur_data')
        aug_file_yrs = [f for f in aug_files if 'ReEDS_Augur_' in f]
        yrs = [int(f.replace('ReEDS_Augur_','').replace('.gdx','')) for f in aug_file_yrs]
        yrs_less = [y for y in yrs if y < year]
        max_yr = max(yrs_less)
        df_aug = gdxpds.to_dataframe(f'{reeds_run_path}/ReEDS_Augur/augur_data/ReEDS_Augur_{max_yr}.gdx',
            'net_load_2012', old_interface=False)
        if int(df_aug['t'][0]) != year:
            sys.exit(f'ERROR: Augur year ({int(df_aug["t"][0])}) does not match current scenario year ({year})')
        df_aug = df_aug.sort_values('Value', ascending=False)
        df_aug_top = df_aug.groupby(['ccreg','ccseason'], as_index=False).head(netload_num_hrs).copy()
        df_aug_top = df_aug_top.rename(columns={'ccseason':'season'})
        if netload_time_style == 'hour':
            df_aug_top = df_aug_top[['ccreg','season','hour']].copy()
            df_aug_top['hour'] = df_aug_top['hour'].astype(int)
            #Convert the seasonal price to an hourly price over the set of hours assigned to that season (for that ba)
            df_pq_rm_adj['price'] = df_pq_rm_adj['price'] / netload_num_hrs
            #Restrict to prices only and add ccreg column
            df_p_rm = df_pq_rm_adj[['reeds_ba','season','price']].merge(df_ba_cc_map, on='reeds_ba', how='left')
            #Merge max net load hours into df_p_rm (which will duplicate rows if there are multiple timeslices in a ba/season)
            df_p_rm = df_p_rm.merge(df_aug_top, on=['ccreg','season'], how='left')
            #Hour is one-indexed. Re-index to the 2012 set of 8760 hours (43801 to 52560)
            df_p_rm_h = df_p_rm.pivot_table(index=['hour'], columns='reeds_ba', values='price')
            df_p_rm_h = df_p_rm_h.reindex(range(43801,52561)).reset_index(drop=True)
        elif netload_time_style == 'timeslice':
            #We assign reserve margin prices to the entire timeslice(s) that contain the top net load hour(s) of each season
            df_aug_top = df_aug_top[['ccreg','season','h']].drop_duplicates()
            #Find number of total hours that we're mapping prices to in each season
            df_seas_hrs = df_aug_top.merge(df_h_num_hrs, on=['h'], how='left')
            df_seas_hrs = df_seas_hrs.groupby(['ccreg','season'], as_index=False)['num_hrs'].sum()
            #Add ccreg and num_hrs columns to df_pq_rm_adj
            df_pq_rm_adj = df_pq_rm_adj.merge(df_ba_cc_map, on='reeds_ba', how='left')
            df_pq_rm_adj = df_pq_rm_adj.merge(df_seas_hrs, on=['ccreg','season'], how='left')
            #Adjust price by num_hrs
            df_pq_rm_adj['price'] = df_pq_rm_adj['price'] / df_pq_rm_adj['num_hrs']
            #Merge in the timeslices to which we'll be mapping prices. This might duplicate rows if there are
            #multiple timeslices in a ba/season (which is possible if netload_num_hrs is greater than 1)
            df_pq_rm_adj = df_pq_rm_adj.merge(df_aug_top, on=['ccreg','season'], how='left')
            #Isolate prices with h as first column and reeds_ba as other columns
            df_p_rm = df_pq_rm_adj.pivot_table(index=['h'], columns='reeds_ba', values='price').reset_index()
            #Merge with df_hmap, duplicating prices across all hours of the chosen timeslices.
            df_p_rm_h = df_hmap[['h']].merge(df_p_rm, on=['h'], how='left').drop(columns=['h'])
    elif res_marg_style == 'max_load_price':
        #Assign reserve margin prices to the timeslice with the max load price of each season
        df_pq_load_seas = df_pq_load.merge(df_seas_h_map, on='h', how='left')
        df_max_load = df_pq_load_seas.groupby(['reeds_ba','season'], as_index=False)['price'].max()
        df_max_load['max_flag'] = 1
        #Merge back with df_pq_load_seas to flag those timeslices that have max load prices (which could be
        #multiple per season)
        df_pq_load_seas = df_pq_load_seas.merge(df_max_load, on=['reeds_ba','season','price'], how='left')
        df_max_h = df_pq_load_seas[df_pq_load_seas['max_flag']==1][['reeds_ba','season','h']].copy()
        df_max_h_num_hrs = df_max_h.merge(df_h_num_hrs, on=['h'], how='left')
        df_seas_max_h_num_hrs = df_max_h_num_hrs.groupby(['reeds_ba','season'], as_index=False)['num_hrs'].sum()
        #Merge count of hours of max-load-price in each ba/season
        df_pq_rm_adj = df_pq_rm_adj.merge(df_seas_max_h_num_hrs, on=['reeds_ba','season'], how='left')
        #Convert the seasonal price to an hourly price over the set of hours assigned to that season (for that ba)
        df_pq_rm_adj['price'] = df_pq_rm_adj['price'] / df_pq_rm_adj['num_hrs']
        #Merge max-load-price timeslices into df_pq_rm_adj (which will duplicate rows if there are multiple timeslices in a ba/season)
        df_pq_rm_adj = df_pq_rm_adj.merge(df_max_h, on=['reeds_ba','season'], how='left')
        df_p_rm = df_pq_rm_adj.pivot_table(index=['h'], columns='reeds_ba', values='price').reset_index()
        df_p_rm_h = df_hmap[['h']].merge(df_p_rm, on=['h'], how='left').drop(columns=['h'])
    df_p_rm_h = df_p_rm_h.reindex(columns=df_p_load_h.columns).fillna(0)

    if r['tech'] != 'load':
        print('- Operating reserve prices')
        #Already in $/MWh
        df_orperc = pd.read_csv(f'{reeds_run_path}/inputs_case/orperc.csv')
        df_pq_or = df_pq[df_pq['reqt'] == 'oper_res'].copy()
        #Sum prices of all OR products
        df_p_or = df_pq_or.groupby(['reeds_ba','h'], as_index=False)['price'].sum()
        df_p_or = df_p_or.pivot_table(index=['h'], columns='reeds_ba', values='price').reset_index()
        df_p_or_h = df_hmap[['h']].merge(df_p_or, on=['h'], how='left').drop(columns=['h'])
        if r['tech'] in ['wind-ons','wind-ofs']:
            or_mult = -1 * df_orperc['or_wind'].sum()
        elif r['tech'] == 'upv':
            #TODO: For PV we should count a fraction of capacity rather than generation,
            #and just during dayhours(h)
            or_mult = -1 * df_orperc['or_pv'].sum()
        else:
            #TODO: in this case we shouldn't just add OR prices, we should take max of OR and energy prices.
            or_mult = 1
        df_p_or_h_mult = df_p_or_h * or_mult
        df_p_or_h_mult = df_p_or_h_mult.reindex(columns=df_p_load_h.columns).fillna(0)

        print('- State RPS prices')
        #Already in $/MWh
        df_pq_rps = df_pq[df_pq['reqt'] == 'state_rps'].copy()
        if r['tech'] in ['wind-ons','wind-ofs']:
            df_pq_rps = df_pq_rps[df_pq_rps['reqt_cat'].isin(['RPS_All', 'CES', 'RPS_Wind'])]
        elif r['tech'] == 'upv':
            df_pq_rps = df_pq_rps[df_pq_rps['reqt_cat'].isin(['RPS_All', 'CES', 'RPS_Solar'])]
        else:
            df_pq_rps = df_pq_rps[df_pq_rps['reqt_cat'].isin(['RPS_All', 'CES'])]
        #Sum prices of all RPS categories
        df_p_rps = df_pq_rps.groupby(['reqt','reeds_ba'], as_index=False)['price'].sum()
        df_p_rps = df_p_rps.pivot_table(index=['reqt'], columns='reeds_ba', values='price').reset_index()
        df_h_rps = pd.DataFrame({'reqt':['state_rps']*8760})
        df_p_rps_h = df_h_rps.merge(df_p_rps, on=['reqt'], how='left').drop(columns=['reqt'])
        df_p_rps_h = df_p_rps_h.reindex(columns=df_p_load_h.columns).fillna(0)

    print('Combining prices')
    #Store service components in a dict
    if r['tech'] == 'load':
        df_p_h_ba = df_p_load_h + df_p_rm_h
        df_p_h_serv = {'tot':df_p_h_ba, 'load': df_p_load_h, 'rm': df_p_rm_h}
    else:
        df_p_h_ba = df_p_load_h + df_p_rm_h + df_p_or_h_mult + df_p_rps_h
        df_p_h_serv = {'tot':df_p_h_ba, 'load': df_p_load_h, 'rm': df_p_rm_h, 'or': df_p_or_h_mult, 'rps':df_p_rps_h}

    for s in list(df_p_h_serv.keys()):
        #Roll prices from EST to UTC (this will bring prices from end of year to beginning of year)
        for col in df_p_h_serv[s]:
            df_p_h_serv[s][col] = np.roll(df_p_h_serv[s][col], 5)
        if sw_reg != 'ba':
            #In this case, we need to map prices to bas
            df_hier_red = df_hier[df_hier[sw_reg].isin(df_p_h_serv[s].columns)]
            df_p_h_serv[s] = df_p_h_serv[s][df_hier_red[sw_reg].tolist()]
            df_p_h_serv[s].columns = df_hier_red['ba'].tolist()
    return df_pq, df_q_load, df_p_h_serv

def calculate_benchmarks():
    print('Calculating benchmark annual average prices and system-wide price profile')
    #Calculate annual load by region and total load
    load_ba = df_q_load.drop(columns=['h']).sum()
    if sw_reg != 'ba':
        #In this case, we need to map load_ba from aggreg to ba, incorrectly assuming equal load for all bas in the same aggreg
        df_load_ba = df_hier[df_hier['aggreg'].isin(load_ba.index)].copy()
        df_load_ba['load'] = df_load_ba['aggreg'].map(load_ba.to_dict())
        df_load_ba['ba_count'] = df_load_ba.groupby('aggreg')['ba'].transform('count')
        df_load_ba['load'] = df_load_ba['load'] / df_load_ba['ba_count']
        df_load_ba = df_load_ba.set_index('ba')
        load_ba = df_load_ba['load']
    load_nat = load_ba.sum()
    #Calculate benchmark prices, assuming flat-block benchmark providing energy and firm capacity only,
    #so averages across time are simply time-weighted. But when averaging across space, we weight by load.
    df_p_h_ba_bench = df_p_h_serv['load'] + df_p_h_serv['rm']
    p_ba = df_p_h_ba_bench.mean()
    p_ba_load = df_p_h_serv['load'].mean()
    p_ba_rm = df_p_h_serv['rm'].mean()
    p_nat = p_ba.mul(load_ba).sum()/load_nat
    p_nat_load = p_ba_load.mul(load_ba).sum()/load_nat
    p_nat_rm = p_ba_rm.mul(load_ba).sum()/load_nat

    #Calculate a weighted average price that is unused but more comparable to ReEDS reported electricity prices.
    #Note that this dollar year is 2019 while ReEDS outputs are 2022 (multiplier of 1.1443), and operating reserves
    #and state RPS are included in ReEDS price outputs, while they may or may not be here ("load" tech should include these)
    # p_nat_wgt_chk = ((df_pq_load['price']*df_pq_load['quant']).sum() + (df_pq_rm['price']*df_pq_rm['quant']).sum())/(df_pq_load['quant'].sum())

    #System-wide price profile. Note that this is annual load-weighted. It could also be load-weighted per hour, which
    #we would do if using load-weighted prices instead of flat-block prices (to be symmetric). To be symmetric between space
    #and time for flat-block prices, we could also take the strict average across regions.
    p_h = df_p_h_ba_bench.mul(load_ba).sum(axis='columns').div(load_nat)
    return p_ba, p_ba_load, p_ba_rm, p_nat, p_nat_load, p_nat_rm, p_h

def get_profiles():
    df_rev_sc = None
    if r['rev_sc_path'] != 'none':
        print('Reading supply curve')
        rev_sc_path = r['rev_sc_path'].replace('"', '')
        #Profile hours start at 12am UTC
        df_rev_sc = pd.read_csv(rev_sc_path)
        #Add/rename columns
        df_rev_sc['MWh'] = df_rev_sc['annual_energy-means'] / 1000
        df_rev_sc = df_rev_sc.rename(columns={'total_lcoe':'LCOE', 'capacity_mw':'MW'})
        df_rev_sc = df_rev_sc.merge(df_rev_county, on='cnty_fips', how='left')

    print('Reading profile file')
    if r['tech'] == 'load':
        df_profile = pd.read_csv(profile_path)
        df_profile = df_profile.drop(columns=['hour'])
        #Convert kW to MW and convert negative to positive
        df_profile = -1 * df_profile/1000
        #Roll load profiles to UTC (this will bring prices from end of year to beginning of year)
        for col in df_profile:
            profile_tz = ba_tz_map[col] if r['profile_timezone'] == 'local' else int(r['profile_timezone'])
            df_profile[col] = np.roll(df_profile[col], -1 * profile_tz)
    else:
        h5_rev = h5py.File(profile_path, 'r')
        df_profile = pd.DataFrame(h5_rev[f'cf_profile-{rev_year}'][:])
        df_profile = df_profile/h5_rev[f'cf_profile-{rev_year}'].attrs['scale_factor']
        df_rev_meta = pd.DataFrame(h5_rev['meta'][:])
        h5_rev.close()
        df_profile.columns = df_profile.columns.map(df_rev_meta['sc_point_gid'])

    return df_profile, df_rev_sc

def calculate_metrics():
    print('Reducing profiles to only those that can be mapped to prices')
    #First find list of BAs associated with ReEDS run
    if sw_reg == 'ba':
        bas = df_pq['reeds_ba'].unique().tolist()
    else:
        bas = df_hier[df_hier[sw_reg].isin(df_pq['reeds_ba'])]['ba'].tolist()
    #Now restrict profile based on that list of bas
    if r['tech'] == 'load':
        #Assuming profiles are at the BA level
        df_profile = df_profile_full[bas].copy()
    else:
        df_rev_sc = df_rev_sc_full[df_rev_sc_full['reeds_ba'].isin(bas)].copy()
        df_profile = df_profile_full[df_rev_sc['sc_point_gid'].tolist()].copy()
    df_p_h_s = df_p_h_serv.copy() #Shallow copy so we don't duplicate so much data
    if r['rev_sc_path'] != 'none':
        print('Calculate price profile by reV site')
        ls_serv = list(df_p_h_s.keys())
        for s in ls_serv:
            df_p_h_s[f'{s}_site'] = df_p_h_s[s][df_rev_sc['reeds_ba'].tolist()]
            df_p_h_s[f'{s}_site'].columns = df_rev_sc['sc_point_gid'].tolist()

    print('Calculating metrics')
    df = df_profile.sum().to_frame(name='MWh_ann')
    serv = [s for s in df_p_h_s.keys() if '_site' not in s]
    for s in serv:
        s_key = s if r['rev_sc_path'] == 'none' else f'{s}_site'
        df[f'LVOE_{s}'] = df_profile.mul(df_p_h_s[s_key]).sum(axis='rows').div(df['MWh_ann'])
    df = df.rename(columns={'LVOE_tot':'LVOE'})
    df['LVOE_loc'] = p_ba if r['rev_sc_path'] == 'none' else p_ba[df_rev_sc['reeds_ba'].tolist()].to_list()
    #Output benchmark price components
    df['Pb_load_loc'] = p_ba_load if r['rev_sc_path'] == 'none' else p_ba_load[df_rev_sc['reeds_ba'].tolist()].to_list()
    df['Pb_rm_loc'] = p_ba_rm if r['rev_sc_path'] == 'none' else p_ba_rm[df_rev_sc['reeds_ba'].tolist()].to_list()
    df['Pb_load_nat'] = p_nat_load
    df['Pb_rm_nat'] = p_nat_rm
    df['LVOE_sys'] = df_profile.mul(p_h.tolist(), axis='rows').sum(axis='rows').div(df['MWh_ann'])
    df['VF'] = df['LVOE']/p_nat
    df['VF_temporal'] = df['LVOE_sys']/p_nat
    df['VF_spatial'] = df['LVOE_loc']/p_nat
    df['VF_temporal_local'] = df['LVOE']/df['LVOE_loc']
    df['VF_spatial_simult'] = df['LVOE']/df['LVOE_sys']
    df['VF_interaction'] = df['VF_spatial_simult']/df['VF_spatial']
    if r['tech'] == 'load' and r['buildings_file'] != 'none':
        df_buildings = pd.read_csv(r['buildings_file'], index_col='ba')
        df = df.merge(df_buildings, left_index=True, right_index=True)
        for col in ['LVOE','LVOE_load','LVOE_rm']:
            new_col = col.replace('LVOE','LVOB')
            df[new_col] = df[col]*df['MWh_ann']/df['number']
            new_col = col.replace('LVOE','LVOsqft')
            df[new_col] = df[col]*df['MWh_ann']/df['sqft']
    df = df.drop(columns=['LVOE_loc','LVOE_sys']).reset_index()

    if r['rev_sc_path'] != 'none':
        #Merge metrics with other supply curve columns
        df = df.rename(columns={'index':'sc_point_gid'})
        #Drop MWh_ann (annual MWh derived from 2012 CF profile) and replace with MWh derived from annual_energy-means (in kWh)
        #from the supply curve, where mean_cf = annual_energy-means/(capacity_mw*8760*1000), which are multi-year averages.
        df = df.drop(columns=['MWh_ann'])
        #Merge into rev supply curve and calculate cost metrics
        df = df_rev_sc[['sc_point_gid','latitude','longitude','MW','MWh','LCOE']].merge(df, on='sc_point_gid', how='left')
        #TODO: Change the following to apply to more techs (currently works for just onshore wind)
        if r['tech'] == 'wind-ons':
            #Apply multipliers to LCOE over time: 2020: 1.44, 2030: 1, 2050: 0.80
            if year <= 2030:
                mult = 1.44 + (year - 2020)*(1 - 1.44)/(2030 - 2020)
            else:
                mult = 1 + (year - 2030)*(0.8 - 1)/(2050 - 2030)
            df['LCOE'] = df['LCOE']*mult
        #Apply IRA incentive
        df['LCOE'] = df['LCOE'] - ira_incentive
        df['ASP'] = (df['LVOE'] - df['LCOE'])*df['MWh']
        df['BCR'] = df['LVOE'] / df['LCOE']
        df['PLCOE'] = df['LCOE'] / df['VF']

    #Add tech and scenario as the first two columns
    df.insert(loc=0, column='scenario', value=r['name'])
    df.insert(loc=0, column='tech', value=r['tech'])
    return df

print(f'Starting reValue')
df_scens = pd.read_csv(f'{this_dir_path}/scenarios.csv')
df_scens = df_scens[df_scens['activate'] == 1].copy()
if len(df_scens['tech'].unique()) > 1:
    sys.exit(f'ERROR: Only one tech currently allowed at a time. You have: {df_scens["tech"].unique().tolist()}')
ls_metrics = []
dct_prices = {} #Keys are tuples of (reeds_run_path, year). Values are tuples of (df_pq, df_q_load, df_p_h_serv)
dct_benchmarks = {} #Keys are tuples of (reeds_run_path, year). Values are tuples of (p_ba, p_ba_load, p_ba_rm, p_nat, p_nat_load, p_nat_rm, p_h)
dct_profiles = {} #Keys are profile_paths. Values are tuples of (df_profile_full, df_rev_sc_full).
for i,r in df_scens.iterrows():
    print(f'\nProcessing {r["name"]}')
    profile_path = r['profile_path'].replace('"', '')
    reeds_run_path = r['reeds_run_path'].replace('"', '')
    year = r['year']
    df_switches = pd.read_csv(f'{reeds_run_path}/inputs_case/switches.csv', header=None)
    switches = dict(zip(df_switches[0], df_switches[1]))
    sw_reg = switches['GSw_RegionResolution']
    sw_hier = switches['GSw_HierarchyFile']
    hier_suffix = '' if sw_hier == 'default' else '_' + sw_hier
    hier_file = f'{this_dir_path}/../../inputs/hierarchy{hier_suffix}.csv'
    df_hier = pd.read_csv(hier_file, usecols=['ba',sw_reg]).drop_duplicates()
    df_hier_run = pd.read_csv(f'{reeds_run_path}/inputs_case/hierarchy.csv')
    #Only fetch prices if we haven't already for this reeds run and year
    #TODO: Include tech here in the dct_prices tuple key? For now I disallow multiple techs
    if (reeds_run_path, year) not in dct_prices:
        dct_prices[(reeds_run_path, year)] = get_prices()
    else:
        print('Already got prices!')
    df_pq, df_q_load, df_p_h_serv = dct_prices[(reeds_run_path, year)]
    if (reeds_run_path, year) not in dct_benchmarks:
        dct_benchmarks[(reeds_run_path, year)] = calculate_benchmarks()
    else:
        print('Already got benchmarks!')
    p_ba, p_ba_load, p_ba_rm, p_nat, p_nat_load, p_nat_rm, p_h = dct_benchmarks[(reeds_run_path, year)]
    if r['profile_path'] == 'none':
        continue
    #Only grab profiles if we haven't already.
    if profile_path not in dct_profiles:
        dct_profiles[profile_path] = get_profiles()
    else:
        print('Already got profiles!')
    df_profile_full, df_rev_sc_full = dct_profiles[profile_path]
    df_metrics = calculate_metrics()
    ls_metrics.append(df_metrics)

print('\nConcatenating and outputting')
if output_prices:
    ls_prices = []
    #Loop through dict of prices
    for run_year in dct_prices:
        df_p_h_serv = dct_prices[run_year][2]
        for s in list(df_p_h_serv.keys()):
            #Round prices and keep only hours that have data for any BA
            df_p_out = df_p_h_serv[s].round(2)
            df_p_out = df_p_out[df_p_out.sum(axis=1)>0]
            df_p_out.index.name='hour_UTC'
            df_p_out = df_p_out.reset_index()
            df_p_out.insert(loc=0, column='type', value=s)
            df_p_out.insert(loc=0, column='year', value=run_year[1])
            df_p_out.insert(loc=0, column='reeds_run', value=run_year[0])
            ls_prices.append(df_p_out)
    df_p_out = pd.concat(ls_prices, ignore_index=True)
    df_p_out.to_csv(f'{output_dir}/prices.csv', index=False)
if len(ls_metrics) > 0:
    df_metrics = pd.concat(ls_metrics, ignore_index=True)
    df_metrics.to_csv(f'{output_dir}/reValue_out.csv', index=False)
print('reValue done!')
