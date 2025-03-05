#%%### General imports
import os
import site
import traceback
import pandas as pd
import numpy as np
from glob import glob
import re
### Local imports
import reeds

# #%% Debugging
# sw['reeds_path'] = os.path.expanduser('~/github/ReEDS-2.0/')
# sw['casedir'] = os.path.join(sw['reeds_path'],'runs','v20230123_prmM3_Pacific_d7sIrh4sh2_y2')
# import importlib
# importlib.reload(functions)


#%%### Functions
def get_and_write_neue(sw, write=True):
    """
    Write dropped load across all completed years to outputs
    so it can be plotted alongside other ReEDS outputs.

    Notes
    -----
    * The denominator of NEUE is exogenous electricity demand; it does not include
    endogenous load from losses or H2 production or exogenous H2 demand.
    """
    infiles = [
        i for i in sorted(glob(
            os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', 'PRAS_*.h5')))
        if re.match(r"PRAS_[0-9]+i[0-9]+.h5", os.path.basename(i))
    ]
    eue = {}
    for infile in infiles:
        year_iteration = os.path.basename(infile)[len('PRAS_'):-len('.h5')].split('i')
        year = int(year_iteration[0])
        iteration = int(year_iteration[1])
        eue[year,iteration] = reeds.io.read_pras_results(infile)['USA_EUE'].sum()
    eue = pd.Series(eue).rename('MWh')
    eue.index = eue.index.rename(['year','iteration'])

    load = reeds.io.read_file(os.path.join(sw['casedir'],'inputs_case','load.h5'))
    loadyear = load.sum(axis=1).groupby('year').sum()

    neue = (
        (eue / loadyear * 1e6).rename('NEUE [ppm]')
        .rename_axis(['t','iteration']).sort_index()
    )

    if write:
        neue.to_csv(os.path.join(sw['casedir'],'outputs','neue.csv'))
    return neue


def get_rmap(sw, hierarchy_level='country'):
    """
    """
    ### Make the region aggregator
    hierarchy = reeds.io.get_hierarchy(sw.casedir)

    if hierarchy_level == 'r':
        rmap = pd.Series(hierarchy.index, index=hierarchy.index)
    else:
        rmap = hierarchy[hierarchy_level]

    return rmap


def get_pras_eue(sw, t, iteration=0):
    """
    """
    ### Get PRAS outputs
    dfpras = reeds.io.read_pras_results(
        os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', f"PRAS_{t}i{iteration}.h5")
    )
    ### Create the time index
    dfpras.index = reeds.timeseries.get_timeindex(sw['resource_adequacy_years'])

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
                sw['casedir'],'ReEDS_Augur','augur_data',f'pras_load_{t}.h5')
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
        reeds.timeseries.timestamp2h(pd.Timestamp(*d), sw['GSw_HourlyType']).split('h')[0]
        for d in dfmetric_top.index.values
    ]

    return dfmetric_top


def get_annual_neue(sw, t, iteration=0):
    """
    """
    ### Get EUE from PRAS
    dfeue = get_pras_eue(sw=sw, t=t, iteration=iteration)

    ### Get load (for calculating NEUE)
    dfload = pd.read_hdf(
        os.path.join(
            sw['casedir'],'ReEDS_Augur','augur_data',f'pras_load_{t}.h5')
    )
    dfload.index = dfeue.index

    levels = ['country','interconnect','nercr','transreg','transgrp','st','r']
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
    site.addsitedir(os.path.join(sw['casedir'],'input_processing'))
    import hourly_writetimeseries

    #%% Write consolidated NEUE so far
    try:
        _neue_simple = get_and_write_neue(sw, write=True)
        neue = get_annual_neue(sw, t, iteration=iteration)
        neue.round(2).to_csv(
            os.path.join(sw.casedir, 'outputs', f"neue_{t}i{iteration}.csv")
        )
    except Exception as err:
        if int(sw['pras']) == 2:
            print(traceback.format_exc())
        if not int(sw.GSw_PRM_CapCredit):
            raise Exception(err)

    #%% Stop here if not using stress periods or if before ReEDS can build new capacity
    if int(sw.GSw_PRM_CapCredit) or (t < int(sw['GSw_StartMarkets'])):
        return None

    #%% Load this year's stress periods so we don't duplicate
    stressperiods_this_iteration = pd.read_csv(
        os.path.join(
            sw['casedir'], 'inputs_case', f'stress{t}i{iteration}', 'period_szn.csv')
    )

    #%% Get storage state of charge (SOC) to use in selection of "shoulder" stress periods
    dfenergy = reeds.io.read_pras_results(
        os.path.join(sw['casedir'], 'ReEDS_Augur', 'PRAS', f"PRAS_{t}i{iteration}-energy.h5")
    )
    timeindex = reeds.timeseries.get_timeindex(sw['resource_adequacy_years'])
    dfenergy.index = timeindex
    ### Sum by region
    dfenergy_r = (
        dfenergy
        .rename(columns={c: c.split('|')[1] for c in dfenergy.columns})
        .groupby(axis=1, level=0).sum()
    )
    hierarchy = reeds.io.get_hierarchy(sw.casedir)

    #%% Parse the stress-period selection criteria and keep the associated periods
    _eue_sorted_periods = {}
    failed = {}
    high_eue_periods = {}
    shoulder_periods = {}
    for criterion in sw.GSw_PRM_StressThreshold.split('/'):
        ## Example: criterion = 'transgrp_10_EUE_sum'
        (hierarchy_level, ppm, stress_metric, period_agg_method) = criterion.split('_')

        eue_periods = get_stress_periods(
            sw=sw, t=t, iteration=iteration,
            hierarchy_level=hierarchy_level,
            stress_metric=stress_metric,
            period_agg_method=period_agg_method,
        )

        ### Sort in descending stress_metric order
        _eue_sorted_periods[criterion] = (
            eue_periods
            .sort_values(stress_metric, ascending=False)
            .reset_index().set_index('actual_period')
        )

        ### Get the threshold(s) and see if any of them failed
        this_test = neue[hierarchy_level][period_agg_method]
        if (this_test > float(ppm)).any():
            failed[criterion] = this_test.loc[this_test > float(ppm)]
            print(f"GSw_PRM_StressThreshold = {criterion} failed for:")
            print(failed[criterion])
            ###### Add GSw_PRM_StressIncrement periods to the list for the next iteration
            high_eue_periods[criterion, f'high_{stress_metric}'] = (
                _eue_sorted_periods[criterion].loc[
                    ## Only include new stress periods for the region(s) that failed
                    _eue_sorted_periods[criterion].r.isin(failed[criterion].index)
                    ## Don't repeat existing stress periods
                    & ~(_eue_sorted_periods[criterion].index.isin(
                        stressperiods_this_iteration.actual_period))
                ]
                ## Don't add dates more than once
                .drop_duplicates(subset=['y','m','d'])
                ## Keep the GSw_PRM_StressIncrement worst periods for each region.
                ## If you instead want to keep the GSw_PRM_StressIncrement worst periods
                ## overall, use .nlargest(int(sw.GSw_PRM_StressIncrement), stress_metric)
                .groupby('r').head(int(sw.GSw_PRM_StressIncrement))
            )

            ###### Include "shoulder periods" before or after each period if the storage
            ###### state of charge is low.
            if sw.GSw_PRM_StressStorageCutoff.lower() in ['off','0','false']:
                print(
                    f"GSw_PRM_StressStorageCutoff={sw.GSw_PRM_StressStorageCutoff} "
                    "so not adding shoulder stress periods based on storage level"
                )
                break
            if dfenergy_r.empty:
                print(
                    "No storage capacity, so no shoulder stress periods will be added "
                    "based on storage level"
                )
                break

            cutofftype, cutoff = sw.GSw_PRM_StressStorageCutoff.lower().split('_')
            periodhours = {'day':24, 'wek':24*5, 'year':24}[sw.GSw_HourlyType]

            ## Aggregate storage energy to hierarchy_level
            dfenergy_agg = (
                dfenergy_r.rename(columns=hierarchy[hierarchy_level])
                .groupby(axis=1, level=0).sum()
            )
            dfheadspace_MWh = dfenergy_agg.max() - dfenergy_agg
            dfheadspace_frac = dfheadspace_MWh / dfenergy_agg.max()

            for i, row in high_eue_periods[criterion, f'high_{stress_metric}'].iterrows():
                if row.r not in dfheadspace_MWh:
                    continue

                day = pd.Timestamp('-'.join(row[['y','m','d']].astype(str).tolist()))

                start_headspace_MWh = dfheadspace_MWh.loc[day.strftime('%Y-%m-%d'),row.r].iloc[0]
                end_headspace_MWh = dfheadspace_MWh.loc[day.strftime('%Y-%m-%d'),row.r].iloc[-1]

                start_headspace_frac = dfheadspace_frac.loc[day.strftime('%Y-%m-%d'),row.r].iloc[0]
                end_headspace_frac = dfheadspace_frac.loc[day.strftime('%Y-%m-%d'),row.r].iloc[-1]

                day_eue = high_eue_periods[criterion, f'high_{stress_metric}'].loc[i,'EUE']
                day_index = np.where(
                    timeindex == dfenergy_agg.loc[day.strftime('%Y-%m-%d')].iloc[0].name
                )[0][0]

                day_before = timeindex[day_index - periodhours]
                day_after = timeindex[(day_index + periodhours) % len(timeindex)]

                if (
                    ((cutofftype == 'eue') and (end_headspace_MWh / day_eue >= float(cutoff)))
                    or ((cutofftype[:3] == 'cap') and (end_headspace_frac  >= float(cutoff)))
                    or (cutofftype[:3] == 'abs')
                ):
                    shoulder_periods[criterion, f'after_{row.name}'] = pd.Series({
                        'actual_period':day_after.strftime('y%Yd%j'),
                        'y':day_after.year, 'm':day_after.month, 'd':day_after.day, 'r':row.r,
                    }).to_frame().T.set_index('actual_period')
                    print(f"Added {day_after} as shoulder stress period after {day}")

                if (
                    ((cutofftype == 'eue') and (start_headspace_MWh / day_eue >= float(cutoff)))
                    or ((cutofftype[:3] == 'cap') and (start_headspace_frac  >= float(cutoff)))
                    or (cutofftype[:3] == 'abs')
                ):
                    shoulder_periods[criterion, f'before_{row.name}'] = pd.Series({
                        'actual_period':day_before.strftime('y%Yd%j'),
                        'y':day_before.year, 'm':day_before.month, 'd':day_before.day, 'r':row.r,
                    }).to_frame().T.set_index('actual_period')
                    print(f"Added {day_before} as shoulder stress period before {day}")

            ### Dealing with earlier criteria may also address later criteria, so stop here
            break

        else:
            print(f"GSw_PRM_StressThreshold = {criterion} passed")

    eue_sorted_periods = pd.concat(_eue_sorted_periods, names=['criterion'])

    #%% Add them to the stress periods used for this year/iteration, then write
    if len(failed):
        new_stress_periods = pd.concat(
            {**high_eue_periods, **shoulder_periods}, names=['criterion','periodtype'],
        ).reset_index().drop_duplicates(subset='actual_period', keep='first')

        ## Reproduce the format of inputs_case/stress_period_szn.csv
        p = 'w' if sw.GSw_HourlyType == 'wek' else 'd'
        new_stressperiods_write = pd.DataFrame({
            'rep_period': new_stress_periods.actual_period,
            'year': new_stress_periods.actual_period.map(
                lambda x: int(x.strip('sy').split(p)[0])),
            'yperiod': new_stress_periods.actual_period.map(
                lambda x: int(x.strip('sy').split(p)[1])),
            'actual_period': new_stress_periods.actual_period,
        })

        ### If there are no new stress periods, stop here
        if len(new_stressperiods_write) == 0:
            print('High-EUE periods are already stress periods, so stopping here')
            return eue_sorted_periods

        combined_periods_write = pd.concat(
            [stressperiods_this_iteration, new_stressperiods_write],
            axis=0,
        ).drop_duplicates(keep='first')

        ### Write new stress periods
        newstresspath = f'stress{t}i{iteration+1}'
        os.makedirs(os.path.join(sw['casedir'], 'inputs_case', newstresspath), exist_ok=True)
        combined_periods_write.to_csv(
            os.path.join(sw['casedir'], 'inputs_case', newstresspath, 'period_szn.csv'),
            index=False,
        )

        ### Write timeseries data for stress periods for the next iteration of ReEDS
        _write_timeseries = hourly_writetimeseries.main(
            sw=sw, reeds_path=sw['reeds_path'],
            inputs_case=os.path.join(sw['casedir'], 'inputs_case'),
            periodtype=newstresspath,
            make_plots=0, figpathtail='',
        )
        ### Write a few tables for debugging
        eue_sorted_periods.round(2).rename(columns={'EUE':'EUE_MWh','NEUE':'NEUE_ppm'}).to_csv(
            os.path.join(sw.casedir, 'inputs_case', newstresspath, 'stress_periods.csv')
        )
        new_stress_periods.round(2).rename(columns={'EUE':'EUE_MWh','NEUE':'NEUE_ppm'}).to_csv(
            os.path.join(sw.casedir, 'inputs_case', newstresspath, 'new_stress_periods.csv')
        )

    #%% Done
    return eue_sorted_periods
