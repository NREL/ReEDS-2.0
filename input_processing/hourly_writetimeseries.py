#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================
import os
import sys
import logging
import shutil
import datetime
import pandas as pd
import numpy as np
import h5py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
##% Time the operation of this script
tic = datetime.datetime.now()
## Turn off logging for imported packages
for i in ['matplotlib']:
    logging.getLogger(i).setLevel(logging.CRITICAL)


#%%#################
### FIXED INPUTS ###
decimals = 3
### Indicate whether to show plots interactively [default False]
interactive = False
### Indicate whether to save the old h17 inputs for comparison
debug = True


#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================
def make_8760_map(period_szn, sw):
    """
    """
    hoursperperiod = {'day':24, 'wek':120, 'year':24}[sw['GSw_HourlyType']]
    periodsperyear = {'day':365, 'wek':73, 'year':365}[sw['GSw_HourlyType']]
    fulltimeindex = reeds.timeseries.get_timeindex(sw.resource_adequacy_years_list)
    ### Start with all weather years
    hmap_allyrs = pd.DataFrame({
        'timestamp': fulltimeindex,
        'year': np.ravel([[y]*8760 for y in sw.resource_adequacy_years_list]),
        'yearperiod': np.ravel([
            [h+1 for d in range(365) for h in (d,)*24] if sw['GSw_HourlyType'] == 'year'
            else [h+1 for d in range(periodsperyear)
                  for h in (d,)*hoursperperiod]
            for y in sw.resource_adequacy_years_list]),
        'hour': range(1, 8760*len(sw.resource_adequacy_years_list) + 1),
        'hour0': range(8760*len(sw.resource_adequacy_years_list)),
        'yearhour': np.ravel(list(range(1,8761))*len(sw.resource_adequacy_years_list)),
        'periodhour': (
            list(range(1,25))*365*len(sw.resource_adequacy_years_list)
            if sw['GSw_HourlyType'] == 'year'
            else (
                list(range(1, hoursperperiod+1))
                * periodsperyear
                * len(sw.resource_adequacy_years_list))
        ),
    })
    hmap_allyrs['actual_period'] = (
        'y' + hmap_allyrs.year.astype(str)
        + ('w' if sw.GSw_HourlyType == 'wek' else 'd')
        + hmap_allyrs.yearperiod.astype(str).map('{:>03}'.format)
    )
    hmap_allyrs['actual_h'] = (
        hmap_allyrs.actual_period
        + 'h' + hmap_allyrs.periodhour.astype(str).map('{:>03}'.format)
    )
    hmap_allyrs['season'] = hmap_allyrs.actual_period.map(
        period_szn.set_index('actual_period').season)
    hmap_allyrs['month'] = hmap_allyrs.timestamp.dt.strftime('%b').str.upper()
    ### create the timestamp index: y{20xx}d{xxx}h{xx} (left-padded with 0)
    if sw['GSw_HourlyType'] == 'year':
        ### If using a chronological year (i.e. 8760) the day index uses actual days
        hmap_allyrs['h'] = (
            'y' + hmap_allyrs.year.astype(str)
            + 'd' + hmap_allyrs.yearperiod.astype(str).map('{:>03}'.format)
            + 'h' + hmap_allyrs.periodhour.astype(str).map('{:>03}'.format)
        )
    else:
        ### If using representative periods (days/weks) the period index uses
        ### representative periods, which are in the 'season' column
        hmap_allyrs['h'] = (
            hmap_allyrs.season
            + 'h' + hmap_allyrs.periodhour.astype(str).map('{:>03}'.format)
        )
    ### hmap_myr (for "model years") only contains the actually-modeled periods
    hmap_myr = hmap_allyrs.dropna(subset=['season']).copy()

    return hmap_allyrs, hmap_myr


def get_ccseason_peaks_hourly(load, sw, inputs_case, hierarchy, h2ccseason, val_r_all):
    ### Aggregate demand by GSw_PRM_hierarchy_level
    if sw['GSw_PRM_hierarchy_level'] == 'r':
        rmap = pd.Series(hierarchy.index, index=hierarchy.index)
    else:
        rmap = hierarchy[sw['GSw_PRM_hierarchy_level']]
    load_agg = (
        load.assign(region=load.r.map(rmap))
        .groupby(['h','region']).MW.sum()
        .unstack('region').reset_index()
        )
    ### Get the peak hour by ccseason for aggregated load
    load_agg['ccseason'] = load_agg.h.map(h2ccseason)
    #Get the peak hours for the aggregated region associated with GSw_PRM_hierarchy_level
    peakhour_agg_byccseason = load_agg.set_index('h').groupby('ccseason').idxmax()
    ### Get the BA/region resolution demand during the peak hour of the associated GSw_PRM_hierarchy_level

    peak_out = {}

    # Determination of season peaks: We merge the peak_agg_byccseason dataframe to rmap and load.
    # By changing the peak_agg_byccseason to long format we are able to merge based on the aggregated GSw_PRM_hierarchy_level region 
    # Then by merging the resultant dataframe to load based on 'r' and peak hour 'h',
    # we get the peak hours for each region of interest at the desired region resolution by ccseason.
    peak_out = (
        peakhour_agg_byccseason.unstack().rename('h').reset_index()
        .merge(rmap.rename('region').reset_index(), on='region')
        .merge(load, on=['r','h'], how='left')
        [['r','ccseason','MW']]
    )

    return peak_out


def append_csp_profiles(cf_rep, sw):
    ### Parse switch data (hourly_repperiods.py does this already but stress_periods.py does not)
    if isinstance(sw['GSw_CSP_Types'],str):
        sw['GSw_CSP_Types'] = [int(i) for i in sw['GSw_CSP_Types'].split('_')]
    ### Get the CSP profiles
    cfcsp = cf_rep[[c for c in cf_rep if c.startswith('csp')]].copy()
    ### As in cfgather.py, we duplicate the csp1 profiles for each CSP tech
    cfcsp_out = pd.concat((
        [cfcsp.rename(columns={c:c.replace('csp',f'csp{i}') for c in cfcsp.columns})
         for i in sw['GSw_CSP_Types']]
    ), axis=1)
    ### Drop the original 'csp' profiles and append the duplicated CSP profiles to rest of cf's
    cf_combined = pd.concat([
        cf_rep[[c for c in cf_rep if not c.startswith('csp')]],
        cfcsp_out], axis=1
    )

    return cf_combined


def get_dr_shifts(
    sw,
    inputs_case,
    native_data=True,
    hmap_7yr=None,
    chunkmap=None,
    hours=None,
):
    """
    part of shift demand response handling compatible both with h17 and hourly ReEDS
    hours, hmap_7yr, and chunkmap are needed for mapping hourly because there is no
    fixed assumption for temporal structure of run
    """

    dr_hrs = pd.read_csv(
        os.path.join(
            inputs_case, 'dr_shifts.csv')
    )
    
    # write out dr_hrs for Augur
    dr_hrs.to_csv(os.path.join(inputs_case, 'dr_hrs.csv'), index=False)

    dr_pos = dr_hrs[['dr_type', 'pos_hrs']].reindex(dr_hrs.index.repeat(dr_hrs.pos_hrs))
    dr_pos['shift'] = dr_pos['pos_hrs'] - dr_pos.groupby(['dr_type']).cumcount()

    dr_neg = dr_hrs[['dr_type', 'neg_hrs']].reindex(dr_hrs.index.repeat(-1*dr_hrs.neg_hrs))
    dr_neg['shift'] = dr_neg['neg_hrs'] + dr_neg.groupby(['dr_type']).cumcount()

    dr_shifts = pd.concat([dr_pos.rename({'pos_hrs': 'hrs'}, axis=1),
                           dr_neg.rename({'neg_hrs': 'hrs'}, axis=1)])

    #### native_data reads in inputs directly
    if native_data:
        hr_ts = pd.read_csv(
            os.path.join(inputs_case, 'h_dt_szn.csv'))
        hr_ts = hr_ts.loc[(hr_ts['hour'] <= 8760), ['h', 'hour', 'season']]

        num_hrs = pd.read_csv(
            os.path.join(inputs_case, 'numhours.csv'),
            header=0, names=['h', 'numhours'], index_col='h').squeeze(1)
    # otherwise reformat to hourly timeslice subsets
    else:
        hr_ts = hmap_7yr[['h','season','year','hour']].assign(h=hmap_7yr.h.map(chunkmap))
        hr_ts = hr_ts.loc[(hr_ts['hour'] <= 8760), ['h', 'hour', 'season']]
        num_hrs = (
            hours.reset_index().assign(h=hours.index.map(chunkmap))
            .groupby('h').numhours.sum().reset_index())

    #### after here the rest is the same
    dr_shifts['key'] = 1
    hr_ts['key'] = 1
    hr_shifts = pd.merge(dr_shifts, hr_ts, on='key').drop('key', axis=1)
    hr_shifts['shifted_hr'] = hr_shifts['hour'] + hr_shifts['shift']
    # Adjust hrs to be between 1 and 8760
    lt0 = hr_shifts.shifted_hr <= 0
    gt8760 = hr_shifts.shifted_hr > 8760
    hr_shifts.loc[lt0, 'shifted_hr'] += 8760
    hr_shifts.loc[gt8760, 'shifted_hr'] -= 8760

    # Merge on hr_ts again to the shifted hours to see what timeslice DR
    # can move load into
    hr_shifts = pd.merge(hr_shifts,
                         hr_ts.rename({'h':'shifted_h', 'hour':'shifted_hr',
                                       'season':'shifted_season'}, axis=1),
                         on='shifted_hr').drop('key', axis=1)
    # Only allow shifts within the same season
    hr_shifts = hr_shifts[hr_shifts.season == hr_shifts.shifted_season]
    hr_shifts.drop(['shifted_season'], axis=1, inplace=True)

    hr_shifts2 = (
        hr_shifts[['dr_type','h','hour','shifted_h']]
        .drop_duplicates()
        .groupby(['dr_type','h','shifted_h'])
        .size()
        .reset_index()
    )

    ts_shifts = pd.merge(hr_shifts2, num_hrs, on='h')
    ts_shifts['shift_frac'] = ts_shifts[0] / ts_shifts['numhours']

    shift_out = ts_shifts.loc[ts_shifts['h'] != ts_shifts['shifted_h'], :]
    shift_out = shift_out.round(4)

    return shift_out, dr_shifts


def get_minloading_windows(sw, h_szn, chunkmap):
    """
    Create combinations of h's within GSw_HourlyWindow of each other,
    beginning every GSw_HourlyWindowOverlap
    """
    ### Inputs for testing
    # sw['GSw_HourlyWindow'] = 2
    # sw['GSw_HourlyWindowOverlap'] = 1
    h_szn_chunked = h_szn.assign(h=h_szn.h.map(chunkmap)).drop_duplicates()
    seasons = h_szn_chunked.season.unique()
    hour_szn_group = set()
    for season in seasons:
        ## 2 copies so we can loop around the end
        timeslices = h_szn_chunked.loc[h_szn_chunked.season==season,'h'].tolist() * 2
        numslices = len(set(timeslices))
        all_combos = [
            (t1,t2) for (i,t1) in enumerate(timeslices) for (j,t2) in enumerate(timeslices)
            if (
                ## Drop duplicates
                (i != j)
                ## Must be within GSw_HourlyWindow steps of each other
                and (abs(i - j) < int(sw['GSw_HourlyWindow']))
                ## First index must be in the first pass
                and (i <= numslices)
                ## Only keep the windows that start from overlaps that are kept
                and not (i % (int(sw['GSw_HourlyWindowOverlap'])+1))
            )
        ]
        ### Add both polarities
        hour_szn_group.update(all_combos)
        hour_szn_group.update([(j,i) for (i,j) in all_combos])

    ### Format as dataframe and return
    hour_szn_group = pd.DataFrame(hour_szn_group, columns=['h','hh']).sort_values(['h','hh'])

    return hour_szn_group


def get_yearly_demand(
        sw, hmap_myr, hmap_allyrs, inputs_case,
    ):
    """
    After clustering based on GSw_HourlyClusterYear and identifying the modeled days,
    reload the raw demand and extract the demand on the modeled days for each year.
    """
    ### Get original demand data, subset to cluster year
    load_in = reeds.io.read_file(
        os.path.join(inputs_case,'load.h5'), parse_timestamps=True).unstack(level=0)
    load_in.columns = load_in.columns.rename(['r','t'])
    ### load.h5 is busbar load, but b_inputs.gms ingests end-use load, so scale down by distloss
    scalars = reeds.io.get_scalars(inputs_case)
    load_in *= (1 - scalars['distloss'])

    ### Add time index
    load_in.index = load_in.index.map(hmap_allyrs.set_index('timestamp')['actual_h']).rename('h')

    load_out = load_in.copy()
    ### If using representative (i.e. medoid) periods, pull out the representative periods.
    if sw['GSw_HourlyType'] != 'year':
        load_out = load_out.loc[hmap_myr.h.unique()].copy()
    ### Otherwise, if using full year, we keep the modeled years
    else:
        load_out = load_out.loc[
            load_out.index.map(hmap_allyrs.set_index('actual_h').year)
            .isin(sw['GSw_HourlyWeatherYears'])
        ].copy()

    ### Reshape for ReEDS
    load_out = load_out.stack('r').reorder_levels(['r','h'], axis=0).sort_index()

    return load_in, load_out


def get_yearly_flexibility(
        sw, period_szn, rep_periods,
        hmap_1yr, set_szn, inputs_case,
        drcat='dr',
    ):
    """
    After clustering based on GSw_HourlyClusterYear and identifying the modeled days,
    reload the raw flexible DR or EV profiles and extract for the modeled days of each year
    """
    hoursperperiod = {'day':24, 'wek':120, 'year':np.nan}[sw['GSw_HourlyType']]
    ### Get the set of szn's and h's
    szn_h = (
        hmap_1yr
        .drop_duplicates(['h','season'])
        .sort_values(['season','hour']).reset_index(drop=True)
        [['season','h']]
        .assign(periodhour=np.ravel(
            ([range(1,25)] * 365 if sw['GSw_HourlyType']=='year'
                else [range(1,hoursperperiod+1)] * len(set_szn))
        ))
        .set_index(['season','periodhour']).h
    ).copy()

    idx_vals = [i+1 for i in period_szn.index.values]
    period_szn_dict = period_szn.set_index('yperiod').to_dict()['season']

    ### Original flexibility data
    shape = {}
    shape_out = {}
    
    for stype in ['increase','decrease','energy']:
        if stype == 'energy':
            if drcat.lower() == 'evmc_storage':
                shape[stype] = pd.read_csv(
                    os.path.join(inputs_case, f'evmc_storage_{stype}.csv'))
            else:
                continue
        elif drcat.lower() == 'dr':
            shape[stype] = pd.read_csv(
                os.path.join(inputs_case, f'dr_{stype}.csv'))
        elif drcat.lower() == 'evmc_shape':
            shape[stype] = pd.read_csv(
                os.path.join(inputs_case, f'evmc_shape_profile_{stype}.csv'))
        elif drcat.lower() == 'evmc_storage':
            shape[stype] = pd.read_csv(
                os.path.join(inputs_case, f'evmc_storage_profile_{stype}.csv'))
        else:
            raise ValueError(f"drcat must be in ['dr','evmc_shape','evmc_storage'] but is '{drcat}'")

        unique_techs = len(shape[stype].i.unique())
        unique_years = len(shape[stype].year.unique())
        ### Add time indices ("season" is the identifier for modeled periods)
        shape[stype]['yperiod'] = (
            np.ravel([[d]*24 for d in range(1,366)] * unique_techs * unique_years)
            if sw['GSw_HourlyType'] == 'year'
            else np.ravel([[d]*hoursperperiod for d in idx_vals] * unique_techs * unique_years))
        shape[stype]['periodhour'] = (
            np.ravel([range(1,25) for d in range(365)] * unique_techs * unique_years)
            if sw['GSw_HourlyType'] == 'year'
            else np.ravel([range(1,hoursperperiod+1) for d in idx_vals] * unique_techs * unique_years)
        )
        shape[stype]['season'] = shape[stype].yperiod.map(period_szn_dict)

        ### If modeling a full year, keep everything
        if sw['GSw_HourlyType'] == 'year':
            shape_out[stype] = shape[stype].drop(['yperiod','periodhour','season'], axis=1)
            shape_out[stype].index = hmap_1yr.h
        ### If using representative periods, pull out the representative periods
        elif unique_years==1:
            shape_out[stype] = (
                shape[stype].loc[shape[stype].season.isin(rep_periods)]
                .drop(['yperiod','hour','year'],axis=1)
                .set_index(['season','periodhour']).sort_index()
            )
            shape_out[stype].index = shape_out[stype].index.map(szn_h).rename('h')
            shape_out[stype] = (
                shape_out[stype].reset_index().set_index(['h','i']).stack().reset_index()
                .rename(columns={'i':'*i','level_2':'r',0:'Values'})[['*i','r','h','Values']])
        else:
            shape_out[stype] = (
                shape[stype].loc[shape[stype].season.isin(rep_periods)]
                .drop(['yperiod','hour'],axis=1)
                .set_index(['season','periodhour']).sort_index()
            )
            
            shape_out[stype].index = shape_out[stype].index.map(szn_h).rename('h')
            shape_out[stype] = (
                shape_out[stype].reset_index().set_index(['h','i','year']).stack().reset_index()
                .rename(columns={'i':'*i','level_3':'r','year':'t',0:'Values'})[['*i','r','h','t','Values']])
            
    if 'energy' in shape.keys():
        return shape_out['decrease'], shape_out['increase'], shape_out['energy']
    else:
        return shape_out['decrease'], shape_out['increase']


#%% ===========================================================================
### --- MAIN FUNCTION ---
### ===========================================================================
def main(sw, reeds_path, inputs_case, periodtype='rep', make_plots=1, figpathtail=''):
    """
    """
    # #%% Settings for testing
    # reeds_path = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
    # inputs_case = os.path.join(reeds_path, 'runs', 'v20240708_tforM3_Pacific', 'inputs_case')
    # sw = reeds.io.get_switches(inputs_case)
    # periodtype = 'rep'
    # periodtype = 'stress2010i0'
    # make_plots = int(sw.hourly_cluster_plots)
    # make_plots = 0
    # figpathtail = ''

    #%% Set up logger
    _log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    #%% Parse some switches
    if not isinstance(sw['GSw_HourlyWeatherYears'], list):
        sw['GSw_HourlyWeatherYears'] = [int(y) for y in sw['GSw_HourlyWeatherYears'].split('_')]
    # Ensure the GSw_CSP_Types is a list, as hourly_writetimeseries is called in F_stress_periods.py as well
    if not isinstance(sw['GSw_CSP_Types'],list):
        sw['GSw_CSP_Types'] = [int(i) for i in sw['GSw_CSP_Types'].split('_')]
    ## Designate where to write the outputs, and prefix for timestamps
    if 'rep' in periodtype.lower():
        prefix = ''
        tprefix = ''
    else:
        os.makedirs(os.path.join(inputs_case, periodtype), exist_ok=True)
        prefix = os.path.join(periodtype, '')
        tprefix = 's'

    ### Direct plots to outputs folder
    figpath = os.path.join(inputs_case,'..','outputs',f'hourly{figpathtail}')
    os.makedirs(figpath, exist_ok=True)

    #%%### Load shared files
    val_r_all = pd.read_csv(
        os.path.join(inputs_case, 'val_r_all.csv'), header=None).squeeze(1).tolist()
    hierarchy = pd.read_csv(
        os.path.join(inputs_case, 'hierarchy.csv')).rename(columns={'*r':'r'}).set_index('r')

    #%%### Load period-szn map, get representative and stress periods
    period_szn = pd.read_csv(os.path.join(inputs_case, prefix+'period_szn.csv'))
    try:
        forceperiods = pd.read_csv(os.path.join(inputs_case, prefix+'forceperiods.csv'))
    except FileNotFoundError:
        forceperiods = pd.DataFrame(
            columns=['property','region','reason','year','yperiod','szn'])
    ### Strip off prefix to start with a fresh slate
    for col in ['rep_period','actual_period']:
        period_szn[col] = period_szn[col].str.strip(tprefix)
        if len(forceperiods):
            for col in ['szn']:
                forceperiods[col] = forceperiods[col].str.strip(tprefix)
    if 'season' not in period_szn:
        period_szn['season'] = period_szn['rep_period'].copy()


    #%%### If there are no periods, write empty dataframes and stop here
    if not len(period_szn):
        write = {
            'set_h': ['*h'],
            'set_szn': ['*szn'],
            'h_preh': ['*h','preh'],
            'szn_actualszn': ['*season', 'actual_period'],
            'numpartitions': ['*actual_period', 'next_actual_period'],
            'nextpartition': ['*actual_period', 'next_actual_period'],
            'h_szn': ['*h','season'],
            'h_dt_szn': ['h','season','ccseason','year','hour'],
            'numhours': ['*h','numhours'],
            'nexth': ['*h','h'],
            'frac_h_ccseason_weights': ['*h','ccseason','weight'],
            'frac_h_quarter_weights': ['*h','quarter','weight'],
            'h_szn_start': ['*season','h'],
            'h_szn_end': ['*season','h'],
            'hour_szn_group': ['*h','hh'],
            'opres_periods': ['*szn'],
            'h_ccseason_prm': ['*h','ccseason'],
            'load_allyear': ['*r','h','t','MW'],
            'peak_ccseason': ['*r','ccseason','t','MW'],
            'cf_vre': ['*i','r','h','cf'],
            'cf_hyd': ['*i','szn','r','t','cf'],
            'cap_hyd_szn_adj': ['*i','szn','r','value'],
            'can_exports_h_frac': ['*h','frac_weighted'],
            'can_imports_szn_frac': ['*szn','frac_weighted'],
            'period_weights': ['*szn','rep_period'],
            'hmap_myr': ['*year','yearperiod','hour','hour0','yearhour',
                         'periodhour','actual_period','actual_h','season','h'],
            'periodmap_1yr': ['*actual_period','season'],
            'canmexload': ['*r','h'],
            'forcedoutage_h': ['*i','r','h'],
            'dr_increase': ['*i','r','h'],
            'dr_decrease': ['*i','r','h'],
            'dr_shifts': ['*i','h','hh'],
            'dr_shed': ['*i'],
            'evmc_baseline_load': ['r','h','t'],
            'evmc_shape_generation': ['*i','r','h'],
            'evmc_shape_load': ['*i','r','h'],
            'evmc_storage_discharge': ['*i','r','h','t'],
            'evmc_storage_charge': ['*i','r','h','t'],
            'evmc_storage_energy': ['*i','r','h','t'],
            'flex_frac_all': ['*flex_type','r','h','t'],
            'peak_h': ['*r','h','t','MW'],
        }
        for f, columns in write.items():
            pd.DataFrame(columns=columns).to_csv(
                os.path.join(inputs_case, prefix+f+'.csv'), index=False)

        return write


    #%%### Process the representative period weights
    #%% Generate map from actual to representative periods
    hmap_allyrs, hmap_myr = make_8760_map(period_szn=period_szn, sw=sw)
    ### Add prefix if necessary
    if tprefix:
        for col in ['actual_period','actual_h','season','h']:
            hmap_myr[col] = tprefix + hmap_myr[col]
            hmap_allyrs[col] = tprefix + hmap_allyrs[col]
        for col in ['rep_period','actual_period']:
            period_szn[col] = tprefix + period_szn[col]
        if not ((sw['GSw_HourlyType'] == 'year') and (periodtype == 'rep')):
            period_szn['season'] = tprefix + period_szn['season']
        if len(forceperiods):
            for col in ['szn']:
                forceperiods[col] = tprefix + forceperiods[col]

    ### Add ccseasons
    h_dt_szn_h17 = pd.read_csv(os.path.join(inputs_case,'h_dt_szn_h17.csv'))
    hmap_allyrs['ccseason'] = h_dt_szn_h17.ccseason.values

    #%%### Load full hourly RE CF, for downselection below
    #%% VRE
    recf = reeds.io.read_file(os.path.join(inputs_case, 'recf.h5'), parse_timestamps=True)
    ### Overwrite CSP CF (which in recf.h5 is post-storage) with solar field CF
    cspcf = reeds.io.read_file(os.path.join(inputs_case, 'csp.h5'), parse_timestamps=True)
    recf = (
        recf.drop([c for c in recf if c.startswith('csp')], axis=1)
        .merge(cspcf, left_index=True, right_index=True)
    ).loc[hmap_allyrs.timestamp]
    recf.index = hmap_allyrs.actual_h

    #%% Get data for representative periods
    rep_periods = sorted(period_szn.rep_period.unique())

    ### Broadcast CSP values for all techs
    cf_rep = recf.loc[
        recf.index.map(lambda x: any([x.startswith(i) for i in rep_periods]))]
    
    if int(sw['GSw_CSP']) != 0:
        cf_rep = append_csp_profiles(cf_rep=cf_rep, sw=sw)

    cf_out = cf_rep.rename_axis('h').copy()
    i = cf_rep.columns.map(lambda x: x.split('|')[0])
    r = cf_rep.columns.map(lambda x: x.split('|')[1])
    cf_out.columns = pd.MultiIndex.from_arrays([i,r], names=['i','r'])
    cf_out = cf_out.stack(['i','r']).reorder_levels(['i','r','h']).rename('cf').reset_index()


    #%%### Create the temporal sets used by ReEDS
    ### Calculate number of hours represented by each timeslice
    hours = (
        hmap_myr.groupby('h').season.count().rename('numhours')
        / (len(sw['GSw_HourlyWeatherYears']) if periodtype == 'rep' else 1))
    ## Stress period hours are scaled to sum to 6 hours, making 8766 hours (365.25 days) per year
    if periodtype != 'rep':
        hours = hours / hours.sum() * 6
    ### Make sure it lines up
    if periodtype == 'rep':
        assert int(np.around(hours.sum(), 0)) % 8760 == 0
    else:
        assert np.around(hours.sum(), 0) == 6

    # create the timeslice-to-season and timeslice-to-ccseason mappings
    h_szn = hmap_myr[['h','season']].drop_duplicates().reset_index(drop=True)
    h_ccseason = hmap_allyrs[['h','ccseason']].drop_duplicates().reset_index(drop=True)

    ### create the set of szn's modeled in ReEDS
    set_szn = pd.DataFrame({'szn':period_szn.season.sort_values().unique()})

    ### create the set of timeslicess modeled in ReEDS
    hset = h_szn.h.sort_values().reset_index(drop=True)


    ### List of periods in which to apply operating reserve constraints
    if (periodtype == 'rep') and ('user' in sw['GSw_HourlyClusterAlgorithm']):
        period_szn_user = pd.read_csv(
            os.path.join(inputs_case,'period_szn_user.csv')
        )
        opres_periods = period_szn_user.loc[
            (period_szn_user.scenario==sw['GSw_HourlyClusterAlgorithm'])
            & (~period_szn_user.opres.isnull())
        ].rep_period.drop_duplicates().rename('szn').to_frame()
    elif (sw['GSw_OpResPeriods'] == 'all') or (sw['GSw_HourlyType'] == 'year'):
        opres_periods = set_szn
    elif sw['GSw_OpResPeriods'] == 'representative':
        opres_periods =  set_szn.loc[~set_szn.szn.isin(forceperiods.szn)]
    elif sw['GSw_OpResPeriods'] == 'stress':
        opres_periods =  set_szn.loc[set_szn.szn.isin(forceperiods.szn)]
    elif sw['GSw_OpResPeriods'] in ['peakload','peak_load','peak','load','demand']:
        opres_periods =  set_szn.loc[
            set_szn.szn.isin(forceperiods.loc[forceperiods.property=='load'].szn)]
    elif sw['GSw_OpResPeriods'] in ['minre','re','vre','min_re']:
        opres_periods =  set_szn.loc[
            set_szn.szn.isin(forceperiods.loc[forceperiods.property!='load'].szn)]

    ### Calculate the fraction of each h associated with each ReEDS quarter, for compatibility
    ### with model inputs that are defined by quarter
    ## Get a map from hour-of-year to ReEDS quarter
    quarters = (
        h_dt_szn_h17.iloc[:8760]
        .replace({'quarter':{'winter':'wint','spring':'spri','summer':'summ'}})
        .set_index('hour').quarter
    )
    ccseasons = (
        h_dt_szn_h17.iloc[:8760]
        .set_index('hour').ccseason
    )

    #%% Calculate the fraction of hours of each timeslice associated with each quarter
    frac_h_weights = {}
    if periodtype == 'rep':
        for season in ['quarter','ccseason']:
            frac_h_weights[season] = hmap_myr.copy()
            frac_h_weights[season][season] = hmap_myr.yearhour.map(
                {'quarter':quarters, 'ccseason':ccseasons}[season])
            frac_h_weights[season] = (
                ## Count the number of days in each szn that are part of each quarter
                frac_h_weights[season].groupby(['h',season])['season'].count()
                ## Normalize by the total number of hours per timeslice
                / hours
                / len(sw['GSw_HourlyWeatherYears'])
            ).rename('weight')
            frac_h_weights[season] = frac_h_weights[season].reset_index()
    else:
        for season in ['quarter','ccseason']:
            frac_h_weights[season] = hmap_allyrs.copy()
            frac_h_weights[season][season] = hmap_allyrs.yearhour.map(
                {'quarter':quarters, 'ccseason':ccseasons}[season])
            frac_h_weights[season] = (
                frac_h_weights[season].groupby(['actual_h',season]).actual_period.count()
            ).rename_axis(['h',season]).rename('weight').reset_index()

    ### Make sure it lines up
    for season in ['quarter','ccseason']:    
        assert (frac_h_weights[season].groupby('h').weight.sum().round(5) == 1).all()

    ### Calculate the fraction of hours of each h associated with each calendar month,
    ### for compatibility with model inputs that are defined by quarter
    # Get a map from hour-of-year to ReEDS month
    months = hmap_allyrs.iloc[:8760].set_index('hour').month
    
    if periodtype == 'rep':
        frac_h_month_weights = hmap_myr.copy()
        frac_h_month_weights['month'] = hmap_myr.yearhour.map(months)
        frac_h_month_weights = (
            ## Count the number of days in each szn that are part of each month
            frac_h_month_weights.groupby(['h','month']).season.count()
            ## Normalize by the total number of hours per timeslice
            / hours
            / len(sw['GSw_HourlyWeatherYears'])
        ).rename('weight')
        frac_h_month_weights = frac_h_month_weights.reset_index()
    else:
        frac_h_month_weights = hmap_allyrs.copy()
        frac_h_month_weights['month'] = hmap_allyrs.yearhour.map(months)
        frac_h_month_weights = (
            frac_h_month_weights.groupby(['actual_h','month']).actual_period.count()
        ).rename_axis(['h','month']).rename('weight').reset_index()

    ### Make sure it lines up
    assert (frac_h_month_weights.groupby('h').weight.sum().round(5) == 1).all()

    #%%### Seasonal Canadian imports/exports for GSw_Canada=1
    #%% Exports: Spread equally over hours by quarter.
    can_exports_szn_frac = pd.read_csv(
        os.path.join(inputs_case, 'can_exports_szn_frac.csv'),
        header=0, names=['season','frac'], index_col='season',
    ).squeeze(1)
    df = (
        frac_h_weights['quarter'].astype({'h':'str','quarter':'str'})
        .replace({'weight':{0:np.nan}}).dropna(subset=['weight']).copy()
    )
    df = (
        df.assign(frac_exports=df.quarter.map(can_exports_szn_frac))
        .assign(season=df.h.map(h_szn.set_index('h').season))
        .assign(hours=df.h.map(hours))
    )
    df['quarter_hours'] = df.hours * df.weight
    df['hours_per_quarter'] = df.quarter.map(quarters.value_counts())
    df['frac_weighted'] = df.frac_exports * df.quarter_hours / df.hours_per_quarter
    can_exports_h_frac = df.groupby('h', as_index=False).frac_weighted.sum()
    ### Make sure it sums to 1
    if periodtype == 'rep':
        assert can_exports_h_frac.frac_weighted.sum().round(5) == 1

    #%% Imports: Spread over seasons by quarter.
    can_imports_quarter_frac = pd.read_csv(
        os.path.join(inputs_case, 'can_imports_quarter_frac.csv'),
        header=0, names=['season','frac'], index_col='season',
    ).squeeze(1)
    df = hmap_myr.assign(quarter=hmap_myr.yearhour.map(quarters))
    hours_per_quarter = df['quarter'].value_counts()
    ## Fraction of quarter made up by each season (typically rep period)
    quarter_season_weights = (
        df.groupby(['quarter','season']).year.count()
        .divide(hours_per_quarter, axis=0, level='quarter'))
    can_imports_szn_frac = (
        quarter_season_weights
        .multiply(can_imports_quarter_frac, level='quarter')
        .groupby('season').sum()
        .rename('frac_weighted').reset_index().rename(columns={'season':'szn'}))
    ### Make sure it sums to 1
    if periodtype == 'rep':
        assert can_imports_szn_frac.frac_weighted.sum().round(5) == 1

    ##################################################
    #    -- Hour, Region, and Timezone Mapping --    #
    ##################################################

    period_weights = (
        period_szn.rep_period.value_counts() / len(sw['GSw_HourlyWeatherYears'])
    ).reset_index().rename(columns={'index':'szn','szn':'weight'})

    ###### Mapping from hourly resolution to GSw_HourlyChunkLength resolution
    ### Aggregation is performed as an average over the hours to be aggregated
    ### For simplicity, midnight is always a boundary between chunks

    ### First make sure the number of hours is divisible by the chunk length
    GSw_HourlyChunkLength = int(
        sw[f"GSw_HourlyChunkLength{periodtype.strip('i0123456789').title()}"])
    assert not len(hset) % GSw_HourlyChunkLength, (
        'Hours are not divisible by chunk length:'
        '\nlen(hset) = {}\nGSw_HourlyChunkLength = {}'
    ).format(len(hset), GSw_HourlyChunkLength)

    ### Map hours to chunks. Chunks are formatted as hour-ending.
    ## If GSw_HourlyChunkLength == 2,
    ## h1-h2-h3-h4-h5-h6 is mapped to h2-h2-h4-h4-h6-h6.
    outchunks = hmap_myr.actual_h[GSw_HourlyChunkLength-1::GSw_HourlyChunkLength]
    chunkmap = dict(zip(
        hmap_myr.actual_h.values,
        np.ravel([[c]*GSw_HourlyChunkLength for c in outchunks])
    ))

    outchunks_allyrs = hmap_allyrs.actual_h[GSw_HourlyChunkLength-1::GSw_HourlyChunkLength]
    chunkmap_allyrs = dict(zip(
        hmap_allyrs.actual_h.values,
        np.ravel([[c]*GSw_HourlyChunkLength for c in outchunks_allyrs])
    ))

    #%%### h_dt_szn for Augur
    if not len(hmap_myr) % 8760:
        ## Important: When modeling a single weather year, rep periods in the
        ## h_dt_szn table are just the single-year periods concatenated n times.
        ## In that case electrolyzer demand (optimized for GSw_HourlyWeatherYears, usually
        ## 2012) won't line up with optimal operation times (low demand / high wind/solar)
        ## outside of the single reprsentative year.
        h_dt_szn = pd.concat(
            {y: hmap_myr.drop_duplicates(['yearhour']).drop('year', axis=1)
            for y in sw.resource_adequacy_years_list}, names=('year',),
            axis=0,
        ).reset_index(level='year').reset_index(drop=True)
        h_dt_szn['ccseason'] = h_dt_szn_h17.ccseason.values
        h_dt_szn['hour0'] = h_dt_szn.index
        h_dt_szn['hour'] = h_dt_szn['hour0'] + 1
        for col in ['actual_period', 'actual_h']:
            h_dt_szn[col] = 'y' + h_dt_szn.year.astype(str) + h_dt_szn[col].str[5:]
    ## If hmap_myr contains less than a full year (e.g. for stress periods),
    ## just use hmap_myr as-is.
    else:
        h_dt_szn = hmap_myr.copy()
        h_dt_szn['ccseason'] = h_dt_szn.actual_h.map(hmap_allyrs.set_index('actual_h').ccseason)

    ################################################
    #    -- Season starting and ending hours --    #
    ################################################

    ### Start hour is the lowest-numbered h in each season
    ## End up with a series mapping season to start hour: {'szn1':'h1', ...}
    szn2starth = hmap_myr.drop_duplicates('season', keep='first').set_index('season').h

    ### End hour is the highest-numbered h in each season
    szn2endh = hmap_myr.drop_duplicates('season', keep='last').set_index('season').h

    ### next timeslice
    nexth_actualszn = (
        hmap_myr.assign(h=hmap_myr.h.map(chunkmap))
        [[('season' if ((sw.GSw_HourlyType == 'year') and (periodtype == 'rep')) 
           else 'actual_period'),'h']]
        .drop_duplicates()
        .rename(columns={'actual_period':'allszn', 'season':'allszn'})
    ).copy()
    ## Roll to make a lookup table for GAMS
    nexth_actualszn['allsznn'] = np.roll(nexth_actualszn['allszn'], -1)
    nexth_actualszn['hh'] = np.roll(nexth_actualszn['h'], -1)

    ### h-to-actual-period mapping for inter-period storage
    h_actualszn = (
        hmap_myr.assign(h=hmap_myr.h.map(chunkmap))
        [['h',('season' if ((sw.GSw_HourlyType == 'year') and (periodtype == 'rep'))
                else 'actual_period')]]
        .drop_duplicates())
    
    ### The following four sets are used for the inter-day linkage constraints for energy storage
    ### Inter-day linkage only applicable to rep day and wek scenarios, so we only need to calculate these sets for
    ### rep day and wek scenarios, otherwise they are empty
    if sw.GSw_HourlyType in ['day', 'wek']:
        ### Write rep period to actual period mapping set for inter-day storage linkage
        szn_actualszn = (
            hmap_myr.assign(h=hmap_myr.h.map(chunkmap))
            [['season', 'actual_period']]
            .drop_duplicates())
        
        ### Group actual period to partitions and count number of partitions of for each actual period
        numpartitions = (
            hmap_myr.assign(h=hmap_myr.h.map(chunkmap))
            [['season', 'actual_period']]
            .drop_duplicates()).copy()

        if 'actual_period' not in numpartitions.columns:
            numpartitions['actual_period'] = numpartitions['season']

        numpartitions['partition'] = (
            numpartitions['season'] != numpartitions['season'].shift()
        ).cumsum()

        count_partition = numpartitions.groupby('partition').size()
        numpartitions['partition_count'] = numpartitions['partition'].map(count_partition)

        numpartitions = (
            numpartitions.drop_duplicates('partition')
            [['actual_period', 'partition_count']]
            .reset_index(drop=True)
        )

        ### Write next partition mapping set
        nextpartition = numpartitions[['actual_period']].copy()
        nextpartition['next_actual_period'] = nextpartition['actual_period'].shift(-1)
        nextpartition.iloc[-1, nextpartition.columns.get_loc('next_actual_period')
                           ] = nextpartition['actual_period'].iloc[0]

        ### Write mapping set between current hour and previous hours before current hour 
        ### of the period to assist the inter-day linkage constraints. For example:
        ### y2012d001h004 -> [y2012d001h004]
        ### y2012d001h008 -> [y2012d001h004, y2012d001h008]
        ### y2012d001h012 -> [y2012d001h004, y2012d001h008, y2012d001h012]
        unique_timeslices = (
            hmap_myr
            .assign(h=hmap_myr.h.map(chunkmap))
            .drop_duplicates('h')
            .sort_values('h')
        )
        h_preh = pd.Series(
            index=unique_timeslices.h,
            data=(
                unique_timeslices
                .groupby('season')
                .h.apply(lambda x: (x+' ').cumsum().str.strip().str.split())
                .values
            ),
            name='preh',
        ).explode().reset_index()

    else:
        szn_actualszn = pd.DataFrame(columns=['season', 'actual_period'])
        numpartitions = pd.DataFrame(columns=['actual_period', 'partition_count'])
        nextpartition = pd.DataFrame(columns=['actual_period', 'next_actual_period'])
        h_preh = pd.DataFrame(columns=['h', 'preh'])

    ### Number of times one h follows another h (for startup/ramping costs)
    numhours_nexth = (
        hmap_myr.assign(h=hmap_myr.h.map(chunkmap))
        [['actual_period','h']].drop_duplicates()).copy()
    ## Roll to make a lookup table for GAMS
    numhours_nexth = (
        numhours_nexth.assign(nexth=np.roll(numhours_nexth['h'], -1))
        .groupby(['h','nexth']).count()
        .reset_index().rename(columns={'nexth':'hh','actual_period':'hours'})
    )

    #%%### Adjacent hour linkages (including links across adjacent stress periods)
    if periodtype == 'rep':
        if (sw.GSw_HourlyType == 'year') and (sw.GSw_HourlyWrapLevel == 'year'):
            nexth_unchunked = dict(zip(
                hmap_myr.actual_h.values,
                np.roll(hmap_myr.actual_h.values, -1)
            ))
        else:
            nexth_unchunked = {}
            for period in hmap_myr.season.unique():
                hs = hmap_myr.loc[hmap_myr.season==period,'h'].values
                nexth_unchunked = {
                    **nexth_unchunked,
                    **dict(zip(hs, np.roll(hs, -1)))
                }
    else:
        ### Get runs of periods
        ## Two copies in case it loops from end of timeseries to beginning
        unique_periods = list(hmap_myr.actual_period.unique())*2
        ## Map from each actual period to the next actual period
        next_actual_period = dict(zip(
            hmap_allyrs.actual_period.drop_duplicates().values,
            np.roll(hmap_allyrs.actual_period.drop_duplicates().values, -1),
        ))
        _runs = []
        for period in unique_periods:
            ## Start a run for each period
            this_run = [period]
            for nextperiod in unique_periods:
                ## If the next period is a stress period, add it to the run, then
                ## do the same for the period after that (and so forth)
                if next_actual_period[period] == nextperiod:
                    this_run += [nextperiod]
                    period = nextperiod
            _runs.append(this_run)

        runs = pd.Series(_runs).drop_duplicates()

        ### For each period, get the longest run containing it
        _longest_run = {}
        for i, period in enumerate(unique_periods):
            _longest_run[period] = []
            for j, row in runs.items():
                if (period in row) and (len(row) > len(_longest_run[period])):
                    _longest_run[period] = row

        longest_run = pd.Series(_longest_run.values()).drop_duplicates()

        ### Cyclic boundary conditions within each run of periods
        nexth_unchunked = {}
        for i, row in longest_run.items():
            hs = hmap_allyrs.set_index('actual_period').loc[row,'h']
            nexth_unchunked = {
                **nexth_unchunked,
                **dict(zip(hs, np.roll(hs, -1)))
            }

    nexth = pd.Series({
        chunkmap_allyrs[k]: chunkmap_allyrs[v] for k,v in nexth_unchunked.items()
    }).rename_axis('*h').rename('h')


    #%%##########################################
    #    -- Hour groups for eq_minloading --    #
    #############################################

    hour_szn_group = get_minloading_windows(sw=sw, h_szn=h_szn, chunkmap=chunkmap)

    #############################
    #    -- Yearly demand --    #
    #############################

    load_in, load_h = get_yearly_demand(
        sw=sw, hmap_myr=hmap_myr, hmap_allyrs=hmap_allyrs, inputs_case=inputs_case)

    ###### Get the peak demand in each (r,szn,modelyear) for GSw_HourlyWeatherYears
    load_full_yearly = load_in.loc[
        load_in.index.map(hmap_allyrs.set_index('actual_h').year.isin(sw['GSw_HourlyWeatherYears']))
    ].stack('r').reset_index()

    h2ccseason = hmap_allyrs.set_index('actual_h').ccseason
    years = pd.read_csv(os.path.join(inputs_case,'modeledyears.csv')).columns.astype(int).values

    peak_all = {}
    for year in years:
        peak_all[year] = get_ccseason_peaks_hourly(
            load=load_full_yearly[['r','h',year]].rename(columns={year:'MW'}),
            sw=sw, inputs_case=inputs_case, hierarchy=hierarchy, 
            h2ccseason=h2ccseason, val_r_all=val_r_all)
    peak_all = (
        pd.concat(peak_all, names=['t','drop']).reset_index().drop('drop', axis=1)
        [['r','ccseason','t','MW']]
    ).copy()

    ##############################################
    #%%  -- Hydro Month-to-Szn Adjustments --    #
    ##############################################
    
    ### Import and format hydro capacity factors
    h_szn_chunked = h_szn.assign(h=h_szn.h.map(chunkmap)).drop_duplicates()

    ## Calculate fraction of each month associated with each season.
    szn_month_weights = (
        frac_h_month_weights
        .merge(h_szn_chunked, on='h', how='inner')
        .drop('h',axis=1)
        .drop_duplicates()
        [['season','month','weight']]
    )
 
    cf_hyd = pd.read_csv(
        os.path.join(inputs_case,'hydcf.csv'), header=0,
    ).rename(columns={'value':'cf_month'})
    ## Filter for modeled years
    buildyears = [y for y in np.arange(2010,2021)] + [y for y in years if y > 2020]
    cf_hyd = cf_hyd.loc[cf_hyd['t'].isin(buildyears)]
    ## Calculate the month-weighted-average capacity factor by season
    cf_hyd_out = szn_month_weights.merge(cf_hyd, on='month', how='outer')
    cf_hyd_out['cf'] = cf_hyd_out['weight'] * cf_hyd_out['cf_month']
    cf_hyd_out = (
        cf_hyd_out
        .groupby(['*i','season','r','t']).sum()
        .drop(['month','weight','cf_month'], axis=1)
        .cf
        ## For rep periods, sum of season weights is 1, so the next line has no effect.
        ## For full chronological year (GSw_HourlyType=year), we use four seasons,
        ## so the sum of season weights is the number of months in that season and
        ## we need to divide sum{cf*weight} by sum{weight}.
        / szn_month_weights.groupby('season').weight.sum()  
    ).rename('cf').reset_index().rename(columns={'season':'szn'})
    
    ### Import and format monthly hydro capacity adjustment factors
    hydcapadj = pd.read_csv(
        os.path.join(inputs_case,'hydcapadj.csv'),header=0
    ).rename(columns={'value':'cap_month'})
    ## Calculate the month-weighted-average capacity factor by season
    hydcapadj_out = szn_month_weights.merge(hydcapadj, on='month', how='outer')
    hydcapadj_out['cap'] = hydcapadj_out['weight'] * hydcapadj_out['cap_month']
    hydcapadj_out = (
        hydcapadj_out
        .groupby(['*i','season','r']).sum()
        .drop(['month','weight','cap_month'], axis=1)
        .cap
        ## For rep periods, sum of season weights is 1, so the next line has no effect.
        ## For full chronological year (GSw_HourlyType=year), we use four seasons,
        ## so the sum of season weights is the number of months in that season and
        ## we need to divide sum{cf*weight} by sum{weight}.
        / szn_month_weights.groupby('season').weight.sum()        
    ).rename('value').reset_index().rename(columns={'season':'szn'})

    ### Calculate the peak demand timeslice of each ccseason.
    ## Used for hydro_nd PRM constraint.
    h_ccseason_prm = (
        pd.merge(load_h[max(years)].groupby('h').sum().rename('MW'), h_ccseason, on='h')
        .sort_values('MW').drop_duplicates('ccseason', keep='last')
        .drop('MW', axis=1).sort_values('ccseason')
    )


    #%%### Outage rates ######
    infile = os.path.join(inputs_case, 'forcedoutage_hourly.h5')
    tz = 'Etc/GMT+6'
    with h5py.File(infile, 'r') as f:
        forcedoutage_hourly = pd.DataFrame(
            index=pd.to_datetime(pd.Series(f['index']).map(lambda x: x.decode())),
            columns=pd.Series(f['columns']).map(lambda x: x.decode()),
            data=f['data'],
        ).tz_localize('UTC').tz_convert(tz)

    forcedoutage_hourly.columns = pd.MultiIndex.from_tuples(
        forcedoutage_hourly.columns.map(lambda x: tuple(x.split('|'))),
        names=['i','r'],
    )

    ### Aggregate to model resolution
    aggmethod = 'mean' if periodtype == 'rep' else 'max'

    forcedoutage_h = forcedoutage_hourly.loc[hmap_myr.timestamp].copy()
    forcedoutage_h.index = hmap_myr.h.map(chunkmap)
    forcedoutage_h = (
        forcedoutage_h
        .groupby(forcedoutage_h.index).agg(aggmethod)
        .stack(['i','r']).reorder_levels(['i','r','h'])
        .rename('forced_outage_rate')
    ).reset_index()


    ###############################
    #%%  -- Demand Response --    #
    ###############################

    if int(sw.GSw_DR):
        dr_dec, dr_inc = get_yearly_flexibility(
            sw=sw,  period_szn=period_szn, rep_periods=rep_periods,
            hmap_1yr=hmap_myr, set_szn=set_szn, 
            inputs_case=inputs_case, drcat='dr')
        shift_out, dr_shifts = get_dr_shifts(
            sw=sw, inputs_case=inputs_case, native_data=False,
            hmap_allyrs=hmap_allyrs, hours=hours, chunkmap=chunkmap)
    else:
        dr_inc = pd.DataFrame(columns=['*i','r','h'])
        dr_dec = pd.DataFrame(columns=['*i','r','h'])
        shift_out = pd.DataFrame(columns=['dr_type','shifted_h','h','shift_frac'])
    
    #############################
    # -- EV Managed Charging -- #
    #############################

    if int(sw.GSw_EVMC):
        evmc_baseline_load = (
            pd.read_hdf(os.path.join(inputs_case,'ev_baseline_load.h5'))
        .rename(columns={'h':'hour'}).astype({'r':str}))
        ## Drop the h
        evmc_baseline_load.hour = evmc_baseline_load.hour.str.strip('h').astype('int')
        ## Concat for each weather year
        evmc_baseline_load_weatheryears = evmc_baseline_load.pivot(index='hour', columns=['t','r'], values='net')
        evmc_baseline_load_weatheryears = pd.concat(
            {y: evmc_baseline_load_weatheryears for y in sw.resource_adequacy_years_list},
            axis=0, ignore_index=True).loc[hmap_myr.hour0]
        ## Map 8760 hours to modeled hours
        evmc_baseline_load_weatheryears.index = hmap_myr.h
        ### Sum by (r,h,t) to get net trade in MWh during modeled hours
        evmc_baseline_load_out = (
            evmc_baseline_load_weatheryears.stack(['r','t']).groupby(['r','h','t']).sum().rename('MWh')
            ## Divide by number of weather years since we concatted that number of weather years
            / (len(sw['GSw_HourlyWeatherYears']) if periodtype == 'rep' else 1)
        ).reset_index()
        ## Only keep modeled regions
        evmc_baseline_load_out = evmc_baseline_load_out.loc[evmc_baseline_load_out.r.isin(val_r_all)].copy()

        evmc_shape_dec, evmc_shape_inc = get_yearly_flexibility(
            sw=sw,  period_szn=period_szn, rep_periods=rep_periods,
            hmap_1yr=hmap_myr, set_szn=set_szn, 
            inputs_case=inputs_case, drcat='evmc_shape')
        
        evmc_storage_dec, evmc_storage_inc, evmc_storage_energy = get_yearly_flexibility(
            sw=sw,  period_szn=period_szn, rep_periods=rep_periods,
            hmap_1yr=hmap_myr, set_szn=set_szn, 
            inputs_case=inputs_case, drcat='evmc_storage')
    else:
        evmc_shape_dec = pd.DataFrame(columns=['*i','r','h'])
        evmc_shape_inc = pd.DataFrame(columns=['*i','r','h'])
        evmc_storage_dec = pd.DataFrame(columns=['*i','r','h','t'])
        evmc_storage_inc = pd.DataFrame(columns=['*i','r','h','t'])
        evmc_storage_energy = pd.DataFrame(columns=['*i','r','h','t'])
        evmc_baseline_load_out = pd.DataFrame(columns=['r','h','t','MWh'])

    #%%###################################################################################
    #    -- Write outputs, aggregating hours to GSw_HourlyChunkLength if necessary --    #
    ######################################################################################

    write = {
        ### Contents are [dataframe, header, index]
        ## h set for representative timeslices
        'set_h': [hset.map(chunkmap).drop_duplicates().to_frame(), False, False],
        ## szn set for representative periods
        'set_szn': [set_szn, False, False],
        ## Previous hour for each h of the period
        'h_preh': [h_preh, False, False],
        ## Hours to season mapping (h,szn)
        'h_szn': [
            h_szn.assign(h=h_szn.h.map(chunkmap)).drop_duplicates(),
            False, False],
        ## 8760 hour linkage set for Augur (h,szn,year,hour)
        'h_dt_szn': [
            h_dt_szn[['h','season','ccseason','year','hour']].assign(h=h_dt_szn.h.map(chunkmap)),
            True, False],
        ## Number of hours represented by each timeslice (h)
        'numhours': [
            (hours.reset_index().assign(h=hours.index.map(chunkmap)).groupby('h').numhours.sum()
             .reset_index().round(decimals+3)),
            False, False],
        ## Number of times in actual year that one timeslice follows another (h,hh)
        'numhours_nexth': [numhours_nexth, False, False],
        ## Quarterly season weights for assigning quarter-dependent parameters (h,quarter)
        'frac_h_quarter_weights': [
            (frac_h_weights['quarter'].assign(h=frac_h_weights['quarter'].h.map(chunkmap))
             .groupby(['h','quarter'], as_index=False).weight.mean()
             .round(decimals+3)),
            False, False],
        ## ccseason weights for assigning ccseason-dependent parameters (h,ccseason)
        'frac_h_ccseason_weights': [
            (frac_h_weights['ccseason'].assign(h=frac_h_weights['ccseason'].h.map(chunkmap))
             .groupby(['h','ccseason'], as_index=False).weight.mean()
             .round(decimals+3)),
            False, False],
        ## Hydro capacity factors by szn
        'cf_hyd': [cf_hyd_out.round(decimals), True, False],
        ## Hydro capacity adjustment factors by szn
        'cap_hyd_szn_adj': [hydcapadj_out.round(decimals+2), True, False],
        ## mapping from one timeslice to the next
        'nexth': [nexth, True, True],
        ## Hours to actual season mapping (h,allszn)
        'h_actualszn': [h_actualszn, False, False],
        ## season to actual season mapping (szn,allszn)
        'szn_actualszn': [szn_actualszn, False, False],
        ## actual season partition
        'numpartitions': [numpartitions, False, False],
        ## next partition
        'nextpartition': [nextpartition, False, False],
        ## mapping from one timeslice to the next for actual periods
        'nexth_actualszn': [nexth_actualszn, False, False],
        ## first timeslice in season (szn,h)
        'h_szn_start': [szn2starth.map(chunkmap).reset_index(), False, False],
        ## last timeslice in season (szn,h)
        'h_szn_end': [szn2endh.map(chunkmap).reset_index(), False, False],
        ## minload hour windows with overlap (h,h)
        'hour_szn_group': [hour_szn_group, False, False],
        ## periods in which to apply operating reserve constraints (szn)
        'opres_periods': [opres_periods, False, False],
        ## Season-peak demand hour for each szn's representative day (h,szn)
        'h_ccseason_prm': [
            h_ccseason_prm.assign(h=h_ccseason_prm.h.map(chunkmap)),
            False, False],
        ## Annual timeslice demand
        'load_allyear': [
            (load_h.reset_index().assign(h=load_h.reset_index().h.map(chunkmap))
             .groupby(['r','h'])
             .agg((sw['GSw_PRM_StressLoadAggMethod'] if 'stress' in periodtype else 'mean'))
             .stack('t').rename('MW')
             .round(decimals).reset_index()),
            False, False],
        ## Seasonal peak demand
        'peak_ccseason': [peak_all.round(decimals), False, False],
        ## Capacity factors (i,r,h)
        'cf_vre': [
            (cf_out.assign(h=cf_out.h.map(chunkmap))
             .groupby(['i','r','h'], as_index=False).cf.mean().round(5)),
            False, False],
        ## Exports to Canada [fraction] (h)
        'can_exports_h_frac': [
            (can_exports_h_frac.assign(h=can_exports_h_frac.h.map(chunkmap))
             .groupby('h', as_index=False).sum().round(6)),
            False, False],
        ## Imports from Canada [fraction] (szn)
        'can_imports_szn_frac': [can_imports_szn_frac.round(6), False, False],
        ## Forced outage rates
        'forcedoutage_h': [forcedoutage_h.round(3), False, False],
        ## Demand response
        'dr_increase': [
            (dr_inc.assign(h=dr_inc.h.map(chunkmap))
             .groupby(['*i','r','h']).mean()
             .round(decimals).reset_index()),
             False, False],
        'dr_decrease': [
            (dr_dec.assign(h=dr_dec.h.map(chunkmap))
             .groupby(['*i','r','h']).mean()
             .round(decimals).reset_index()),
             False, False],
        'dr_shifts': [
            (shift_out[['dr_type', 'shifted_h', 'h', 'shift_frac']]
             .rename(columns={'dr_type':'*dr_type'})),
             False, False],
        ## EVMC
        'evmc_baseline_load': [
            (evmc_baseline_load_out.assign(h=evmc_baseline_load_out.h.map(chunkmap))
             .groupby(['r','h','t'], as_index=False).MWh.sum()
             .round(decimals)),
            False, False],
        'evmc_shape_generation': [
            (evmc_shape_dec.assign(h=evmc_shape_dec.h.map(chunkmap))
             .groupby(['*i','r','h']).mean()
             .round(decimals).reset_index()),
             False, False],
        'evmc_shape_load': [
            (evmc_shape_inc.assign(h=evmc_shape_inc.h.map(chunkmap))
             .groupby(['*i','r','h']).mean()
             .round(decimals).reset_index()),
             False, False],
        'evmc_storage_discharge': [
            (evmc_storage_dec.assign(h=evmc_storage_dec.h.map(chunkmap))
             .groupby(['*i','r','h','t']).mean()
             .round(decimals).reset_index()),
             False, False],
        'evmc_storage_charge': [
            (evmc_storage_inc.assign(h=evmc_storage_inc.h.map(chunkmap))
             .groupby(['*i','r','h','t']).mean()
             .round(decimals).reset_index()),
             False, False],
        'evmc_storage_energy': [
            (evmc_storage_energy.assign(h=evmc_storage_energy.h.map(chunkmap))
             .groupby(['*i','r','h','t']).mean()
             .round(decimals).reset_index()),
             False, False],
        ##################################################################################
        ###### The next parameters are just diagnostics and are not actually used in ReEDS
        ## Representative period weights for postprocessing (szn)
        'period_weights': [period_weights, False, False],
        ## Mapping from representative h to actual h
        'hmap_myr': [
            hmap_myr.assign(h=hmap_myr.h.map(chunkmap)),
            False, False],
        ## Mapping from representative h to actual h for full set of years
        'hmap_allyrs': [
            hmap_allyrs.assign(h=hmap_allyrs.h.map(chunkmap)),
            False, False],
        ## Mapping from representative period to actual period
        'periodmap_1yr': [
            hmap_myr[['actual_period','season']].drop_duplicates(),
            False, False],
        ###################################################################
        ###### The folowing parameters don't yet work for hourly resolution
        ## Canada/Mexico
        'canmexload': [pd.DataFrame(columns=['*r','h']), True, False],
        ## GSw_EFS_Flex
        'flex_frac_all': [pd.DataFrame(columns=['*flex_type','r','h','t']), True, False],
        'peak_h': [pd.DataFrame(columns=['*r','h','t','MW']), True, False],
    }

    #%% Write output csv files
    for f in write:
        ### Rename first column so GAMS reads it as a comment
        if not write[f][1]:
            write[f][0] = write[f][0].rename(
                columns={write[f][0].columns[0]: '*'+str(write[f][0].columns[0])})
        ### If the file already exists and we're creating representative period data,
        ### add a '_h17' to the filename and save it as a backup
        if (debug
            and os.path.isfile(os.path.join(inputs_case, f+'.csv'))
            and ('rep' in periodtype)):
            shutil.copy(
                os.path.join(inputs_case, f+'.csv'),
                os.path.join(inputs_case, f+'_h17.csv'))
        ### Write the new hourly parameters
        write[f][0].to_csv(
            os.path.join(inputs_case, prefix+f+'.csv'),
            # os.path.join(inputs_case, f+f'{figpathtail}.csv'),
            index=write[f][2])


    ###########################################################################
    #    -- Map resulting annual capacity factor and deviation from h17 --    #
    ###########################################################################
    
    if make_plots >= 1:
        try:
            import hourly_plots as plots_h
            plots_h.plot_maps(sw, inputs_case, reeds_path, figpath)
        except Exception as err:
            print('plot_maps failed with the following error:\n{}'.format(err))

    return write