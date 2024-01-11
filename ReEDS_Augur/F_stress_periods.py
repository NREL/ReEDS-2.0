#%%### General imports
import os
import site
import traceback
import pandas as pd
import numpy as np
from glob import glob
from distutils.dir_util import copy_tree
### Local imports
import ReEDS_Augur.functions as functions

# #%% Debugging
# sw['reeds_path'] = os.path.expanduser('~/github/ReEDS-2.0/')
# sw['casedir'] = os.path.join(sw['reeds_path'],'runs','v20230123_prmM3_Pacific_d7sIrh4sh2_y2')
# import importlib
# importlib.reload(functions)


#%%### Functions
def write_last_years_periods(t, sw, outpath):
    """
    Copy the stress periods from the last model year and use them for the next model year.
    Used if there is no unmet PRM / dropped load.
    """
    last_stressperiod = sorted(glob(
        os.path.join(sw['casedir'], 'inputs_case', 'stress*')))[-1]
    copy_tree(
        last_stressperiod,
        os.path.join(sw['casedir'], 'inputs_case', outpath)
    )


def get_and_write_neue(sw, write=True):
    """
    Write dropped load across all completed years to outputs
    so it can be plotted alongside other ReEDS outputs
    """
    infiles = sorted(glob(
        os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', 'PRAS_*.h5')))
    eue = {}
    for infile in infiles:
        year_iteration = os.path.basename(infile).strip('PRAS_.h5').split('i')
        year = int(year_iteration[0])
        iteration = int(year_iteration[1])
        eue[year,iteration] = functions.read_pras_results(infile)['USA_EUE'].sum()
    eue = pd.Series(eue).rename('MWh')
    eue.index = eue.index.rename(['year','iteration'])

    site.addsitedir(os.path.join(sw['reeds_path'], 'input_processing'))
    import LDC_prep
    load = LDC_prep.read_file(os.path.join(sw['casedir'],'inputs_case','load'))
    loadyear = load.sum(axis=1).groupby('year').sum()

    neue = (eue / loadyear * 1e6).rename('NEUE [ppm]').rename_axis(['t','iteration'])

    if write:
        neue.to_csv(os.path.join(sw['casedir'],'outputs','neue.csv'))
    return neue


def get_osprey_eue(sw, t):
    dfosprey = pd.read_csv(
        os.path.join(
            sw['casedir'], 'ReEDS_Augur', 'augur_data', f"dropped_load_{t}.csv")
    ).rename(columns={'Val':'MW'})
    ## Parse the day/hour indices
    dfosprey['h'] = (
        (dfosprey.d + dfosprey.hr.map(lambda x: x.replace('hr','h')))
        .map(functions.h2timestamp)
    )
    dfeue = (
        dfosprey.set_index('h')
        .pivot(columns='r', values='MW').fillna(0)
    )
    return dfeue


def get_rmap(sw, hierarchy_level='country'):
    """
    """
    ### Make the region aggregator
    hierarchy = functions.get_hierarchy(sw.casedir)

    if hierarchy_level == 'r':
        rmap = pd.Series(hierarchy.index, index=hierarchy.index)
    else:
        rmap = hierarchy[hierarchy_level]

    return rmap


def get_pras_eue(sw, t, iteration=0):
    """
    """
    ### Get PRAS outputs
    dfpras = functions.read_pras_results(
        os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', f"PRAS_{t}i{iteration}.h5")
    )
    ### Create the time index
    dfpras.index = functions.make_fulltimeindex()

    ### Keep the EUE columns by zone
    eue_tail = '_EUE'
    dfeue = dfpras[[
        c for c in dfpras
        if (c.endswith(eue_tail) and not c.startswith('USA'))
    ]].copy()
    ## Drop the tailing _EUE
    dfeue = dfeue.rename(
        columns=dict(zip(dfeue.columns, [c[:-len(eue_tail)] for c in dfeue])))

    return dfeue


def get_stress_periods(
        sw, t, iteration=0,
        hierarchy_level='country',
        stress_metric='EUE',
        period_agg_method='sum',
    ):
    """_summary_

    Args:
        sw (pd.series): ReEDS switches for this run.
        t (int): Model solve year.
        iteration (int, optional): Iteration number of this solve year. Defaults to 0.
        hierarchy_level (str, optional): column of hierarchy.csv specifying the spatial
            level over which to calculate stress_metric. Defaults to 'country'.
        stress_metric (str, optional): 'EUE' or 'NEUE'. Defaults to 'EUE'.
        period_agg_method (str, optional): 'sum' or 'max', indicating how to aggregate
            over the hours in each period. Defaults to 'sum'.

    Raises:
        NotImplementedError: if invalid value for stress_metric or GSw_PRM_StressModel

    Returns:
        pd.DataFrame: Table of periods sorted in descending order by stress metric.
    """    
    ### Get the region aggregator
    rmap = get_rmap(sw=sw, hierarchy_level=hierarchy_level)

    ### Get EUE from PRAS
    dfeue = get_pras_eue(sw=sw, t=t, iteration=iteration)
    ## Aggregate to hierarchy_level
    dfeue = (
        dfeue
        .rename_axis('r', axis=1).rename_axis('h', axis=0)
        .rename(columns=rmap).groupby(axis=1, level=0).sum()
    )

    ###### Calculate the stress metric by period
    if stress_metric.upper() == 'EUE':
        ### Aggregate according to period_agg_method
        dfmetric_period = (
            dfeue
            .groupby([dfeue.index.year, dfeue.index.month, dfeue.index.day])
            .agg(period_agg_method)
            .rename_axis(['y','m','d'])
        )
    elif stress_metric.upper() == 'NEUE':
        ### Get load at hierarchy_level
        dfload = pd.read_hdf(
            os.path.join(
                sw['casedir'],'ReEDS_Augur','augur_data',f'pras_load_{sw.t}.h5')
        ).rename(columns=rmap).groupby(level=0, axis=1).sum()
        dfload.index = dfeue.index

        ### Recalculate NEUE [ppm] and aggregate appropriately
        if period_agg_method == 'sum':
            dfmetric_period = (
                dfeue
                .groupby([dfeue.index.year, dfeue.index.month, dfeue.index.day])
                .agg(period_agg_method)
                .rename_axis(['y','m','d'])
            ) / (
                dfload
                .groupby([dfload.index.year, dfload.index.month, dfload.index.day])
                .agg(period_agg_method)
                .rename_axis(['y','m','d'])
            ) * 1e6
        elif period_agg_method == 'max':
            dfmetric_period = (
                (dfeue / dfload)
                .groupby([dfeue.index.year, dfeue.index.month, dfeue.index.day])
                .agg(period_agg_method)
                .rename_axis(['y','m','d'])
            ) * 1e6

    ### Sort and drop zeros and duplicates
    dfmetric_top = (
        dfmetric_period.stack('r')
        .sort_values(ascending=False)
        .replace(0,np.nan).dropna()
        .reset_index().drop_duplicates(['y','m','d'], keep='first')
        .set_index(['y','m','d','r']).squeeze(1).rename(stress_metric)
        .reset_index('r')
    )
    ## Convert to timestamp, then to ReEDS period
    dfmetric_top['actual_period'] = [
        functions.timestamp2h(pd.Timestamp(*d), sw['GSw_HourlyType']).split('h')[0]
        for d in dfmetric_top.index.values
    ]

    return dfmetric_top


def get_annual_neue(sw, t, iteration=0):
    """
    """
    ### Get the hierarchy
    hierarchy = functions.get_hierarchy(sw.casedir)

    ### Get EUE from PRAS
    dfeue = get_pras_eue(sw=sw, t=t, iteration=iteration)

    ### Get load (for calculating NEUE)
    dfload = pd.read_hdf(
        os.path.join(
            sw['casedir'],'ReEDS_Augur','augur_data',f'pras_load_{sw.t}.h5')
    )
    dfload.index = dfeue.index

    levels = (
        hierarchy.drop(columns=['aggreg','ccreg'], errors='ignore').columns.tolist()
        + ['r']
    )
    _neue = {}
    for hierarchy_level in levels:
        ### Get the region aggregator
        rmap = get_rmap(sw=sw, hierarchy_level=hierarchy_level)
        ### Get NEUE summed over year
        _neue[hierarchy_level,'sum'] = (
            dfeue.rename(columns=rmap).groupby(axis=1, level=0).sum().sum()
            / dfload.rename(columns=rmap).groupby(axis=1, level=0).sum().sum()
        ) * 1e6
        ### Get max NEUE hour
        _neue[hierarchy_level,'max'] = (
            dfeue.rename(columns=rmap).groupby(axis=1, level=0).sum()
            / dfload.rename(columns=rmap).groupby(axis=1, level=0).sum()
        ).max() * 1e6

    ### Combine it
    neue = pd.concat(_neue, names=['level','metric','region']).rename('NEUE_ppm')
    return neue


#%%### Procedure
def main(sw, t, iteration=0):
    """
    """
    #%% More imports and settings
    site.addsitedir(os.path.join(sw['reeds_path'],'input_processing'))
    import hourly_writetimeseries

    savepath = os.path.join(sw['casedir'], 'outputs', 'Augur_plots')
    os.makedirs(savepath, exist_ok=True)
    outpath = f'stress{t}i{iteration}'

    #%% Write consolidated NEUE so far
    try:
        neue_simple = get_and_write_neue(sw, write=True)
        neue = get_annual_neue(sw, t, iteration=iteration)
        neue.round(2).to_csv(
            os.path.join(sw.casedir, 'outputs', f"neue_{outpath.strip('stre')}.csv")
        )
    except Exception as err:
        if int(sw['pras']) == 2:
            print(traceback.format_exc())
        if not int(sw.GSw_PRM_CapCredit):
            raise Exception(err)

    #%% Stop here if not using stress periods
    if int(sw.GSw_PRM_CapCredit):
        return None

    #%% Get EUE for the last GSw_PRM_StressPrevYears solve years
    solveyears = pd.read_csv(
        os.path.join(sw['casedir'],'inputs_case','modeledyears.csv')
    ).columns.astype(int)
    thisyear = list(solveyears).index(sw['t'])
    keepyears = solveyears[thisyear-int(sw['GSw_PRM_StressPrevYears'])+1:thisyear+1]

    #%% Get the list of PRAS results to draw from
    infiles = sorted(glob(
        os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', 'PRAS_*.h5')))
    keepfiles = [
        i for i in infiles
        if int(os.path.basename(i).split('_')[1].split('i')[0]) in keepyears]

    #%% Parse the stress-period selection criteria and keep the associated periods
    _keep_periods = {}

    ## Example: sw.GSw_PRM_StressCriteria = 'country_25_EUE_sum/transreg_5_NEUE_max'
    for criterion in sw.GSw_PRM_StressCriteria.split('/'):
        ## Example: criterion = 'country_30_EUE_sum'
        (hierarchy_level, _, stress_metric, period_agg_method) = criterion.split('_')

        _stress_periods = {}
        for infile in keepfiles:
            year_iteration = os.path.basename(infile).strip('PRAS_.h5').split('i')
            year = int(year_iteration[0])
            _iteration = int(year_iteration[1])
            try:
                _stress_periods[year,_iteration] = get_stress_periods(
                    sw=sw, t=year, iteration=_iteration,
                    hierarchy_level=hierarchy_level,
                    stress_metric=stress_metric,
                    period_agg_method=period_agg_method,
                )
            except FileNotFoundError as err:
                print(err)

        stress_periods = pd.concat(_stress_periods, names=['t','i'])

        ### Sort in descending stress_metric order across all iterations
        _keep_periods[criterion] = (
            stress_periods
            .sort_values(stress_metric, ascending=False)
            ## Drop duplicate periods from different years, keeping the worst year
            .drop_duplicates('actual_period', keep='first')
            .reset_index().set_index('actual_period')
        )

    keep_periods = pd.concat(_keep_periods, names=['criterion'])

    #%% Process multiple criteria in order. If a period is used for one criterion,
    ### it is removed from consideration for the following criteria.
    final_periods = []
    for criterion in sw.GSw_PRM_StressCriteria.split('/'):
        (_, max_stress_periods, stress_metric, _) = criterion.split('_')
        non_overlapping_periods = [
            p for p in _keep_periods[criterion].index.tolist() if p not in final_periods
        ]
        final_periods += non_overlapping_periods[:int(max_stress_periods)]
    final_periods = pd.Series(final_periods)

    #%% Reproduce the format of inputs_case/stress_period_szn.csv
    final_periods_write = pd.DataFrame({
        'rep_period': final_periods,
        'year': final_periods.map(
            lambda x: int(x.strip('sy').split(sw['GSw_HourlyType'][0])[0])),
        'yperiod': final_periods.map(
            lambda x: int(x.strip('sy').split(sw['GSw_HourlyType'][0])[1])),
        'actual_period': final_periods,
    })

    #%% If there are no days with dropped load, stop here and use last year's days
    if not len(final_periods_write):
        write_last_years_periods(t, sw, outpath)

    else:
        ### Write the stress periods
        os.makedirs(os.path.join(sw['casedir'], 'inputs_case', outpath), exist_ok=True)
        final_periods_write.to_csv(
            os.path.join(sw['casedir'], 'inputs_case', outpath, 'period_szn.csv'),
            index=False,
        )
        ### Write timeseries data for stress periods for the next iteration of ReEDS
        write_timeseries = hourly_writetimeseries.main(
            sw=sw, reeds_path=sw['reeds_path'],
            inputs_case=os.path.join(sw['casedir'], 'inputs_case'),
            periodtype=outpath,
            make_plots=0, figpathtail='',
        )
        ### Write keep_periods for debugging
        keep_periods.round(2).rename(columns={'EUE':'EUE_MWh','NEUE':'NEUE_ppm'}).to_csv(
            os.path.join(sw.casedir, 'inputs_case', outpath, 'stress_periods.csv')
        )

    #%% Done; return _keep_periods for debugging
    return keep_periods
