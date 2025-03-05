#%%### Imports
import pandas as pd
import numpy as np
import os
import sys
import datetime
import argparse
import h5py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
## Time the operation of this script
tic = datetime.datetime.now()

reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))

#%%### Fixed inputs
tz_in = 'UTC'
tz_out = 'Etc/GMT+6'
temp_min = -50
temp_max = 60
ignore_techs = ['ocean', 'caes', 'ice']
h5pytypes = ['h5py', 'julia', 'simple', 'manual']

primemover2techgroup = {
    'CC': ['GAS_CC'],
    'CT': ['GAS_CT', 'H2_CT'],
    'DS': ['OGS'],
    'HD': ['HYDRO'],
    'NU': ['NUCLEAR'],
    'ST': ['COAL', 'BIO'],
}

#%%### Functions
def extrapolate_forward_backward(
        dfin, xmin, xmax,
        numfitvals=2, polyfit_deg=1, ymin=0, ymax=1,
    ):
    """Extrapolate slopes forward and backward and fill gaps in integer steps.
    Parameters
    ----------
    dfin: pd.DataFrame
        Dataframe with x values to extrapolate as the index
    xmin: int
        Minimum x value to extrapolate to
    xmax: int
        Maximum x value to extrapolate to
    numfitvals: int, default 2
        Number of values from the beginning and end of the series to use to fit the
        backward and forward slopes, respectively
    polyfit_deg: int, default 1
        Degree of fitting polynomial to use in forward/backward extrapolations
    ymin: float, default 0
        Lower limit for extrapolated values
    ymax: float, default 1
        Upper limit for extrapolated values

    Returns
    -------
    pd.DataFrame
        Dataframe extrapolated forward and backward
    """
    xs_low = dfin.index[:numfitvals].values
    xs_high = dfin.index[-numfitvals:].values

    slope_low, intercept_low = np.polyfit(
        x=xs_low, y=dfin.loc[xs_low].values, deg=polyfit_deg)
    slope_high, intercept_high = np.polyfit(
        x=xs_high, y=dfin.loc[xs_high].values, deg=polyfit_deg)

    ## Combine back-casted, input, and forward-casted data into a single dataframe
    dfout = pd.concat([
        pd.DataFrame(
            {xmin: intercept_low + slope_low * xmin},
            index=dfin.columns,
        ).T,
        dfin,
        pd.DataFrame(
            {xmax: intercept_high + slope_high * xmax},
            index=dfin.columns,
        ).T,
    ]).reindex(range(xmin, xmax+1)).interpolate('linear').clip(upper=ymax, lower=ymin)

    return dfout


def get_temperatures(case, tz_in='UTC', tz_out='Etc/GMT+6', subset_years=True):
    ### Derived inputs
    inputs_case = case if 'inputs_case' in case else os.path.join(case, 'inputs_case')
    h5path = os.path.join(inputs_case, 'temperature_celsius-ba.h5')
    sw = reeds.io.get_switches(inputs_case)
    ## Add one more year on either end of weather years to allow for timezone conversion
    weather_years = sw.resource_adequacy_years_list
    read_years = [min(weather_years) - 1] + weather_years + [max(weather_years) + 1]
    val_ba = (
        pd.read_csv(os.path.join(inputs_case, 'val_ba.csv'), header=None)
        .squeeze(1).values
    )
    ### Load temperatures
    _temperatures = {}
    with h5py.File(h5path, 'r') as f:
        years = read_years if subset_years else [int(i) for i in list(f) if i.isdigit()]
        for year in years:
            timeindex = pd.to_datetime(
                pd.Series(f[f"index_{year}"][:])
                .str.decode('utf-8')
            )
            _temperatures[year] = pd.DataFrame(
                index=timeindex,
                columns=pd.Series(f['columns']).map(lambda x: x.decode()),
                data=f[str(year)],
            )

    temperatures = (
        pd.concat(_temperatures, names=('year','timestamp')).rename_axis(columns='r')
        ## Round to integers for lookup
        .round(0).astype(int)
        .reset_index('year', drop=True)
        .tz_localize(tz_in)
        .tz_convert(tz_out)
        ## Subset to weather years used in ReEDS
        .loc[str(min(weather_years)):str(max(weather_years))]
    )
    ### On leap years, drop Dec 31
    leap_year = temperatures.iloc[:,:1].groupby(temperatures.index.year).count().squeeze(1) == 8784
    for year in weather_years:
        if leap_year[year]:
            temperatures.drop(temperatures.loc[f'{year}-12-31'].index, inplace=True)
    assert len(temperatures) == len(weather_years) * 8760
    ### Subset to states used in this run
    temperatures = temperatures[[c for c in temperatures if c in val_ba]].copy()

    return temperatures


def get_tech_subset_table(case):
    """Output techs are in lower case"""
    inputs_case = case if 'inputs_case' in case else os.path.join(case, 'inputs_case')
    tech_subset_table = (
        pd.read_csv(os.path.join(inputs_case, 'tech-subset-table.csv'), index_col=0)
        .rename_axis(index='i', columns='tech_group')
        .stack().dropna()
        .reorder_levels(['tech_group','i']).sort_index()
        .reset_index('i').i
        .str.lower()
    )
    return tech_subset_table


def get_techlist_after_bans(case):
    sw = reeds.io.get_switches(case)
    tech_subset_table = get_tech_subset_table(case)
    techlist = sorted(tech_subset_table.unique())
    if not int(sw.GSw_BECCS):
        techlist = [i for i in techlist if 'beccs' not in i]
    if not int(sw.GSw_Biopower):
        techlist = [i for i in techlist if i != 'biopower']
    if not int(sw.GSw_DAC):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['DAC'].values]
    if not int(sw.GSw_H2_SMR):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['SMR'].values]
    match int(sw.GSw_Storage):
        case 0:
            techlist = [i for i in techlist if i not in tech_subset_table.loc['STORAGE_STANDALONE'].values]
        case 3:
            techlist = [
                i for i in techlist if (
                    (i not in tech_subset_table.loc['STORAGE_STANDALONE'].values)
                    or (i in ['battery_4','battery_8','pumped-hydro'])
                )
            ]
    if not int(sw.GSw_CCSFLEX_BYP):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['CCSFLEX_BYP'].values]
    if not int(sw.GSw_CCSFLEX_STO):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['CCSFLEX_STO'].values]
    if not int(sw.GSw_CCSFLEX_DAC):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['CCSFLEX_DAC'].values]

    return techlist


def get_forcedoutage_hourly(case, tz='Etc/GMT+6', multilevel=True):
    inputs_case = case if 'inputs_case' in case else os.path.join(case, 'inputs_case')
    with h5py.File(os.path.join(inputs_case, 'forcedoutage_hourly.h5'), 'r') as f:
        if multilevel:
            columns = {
                c: pd.Series(f[f'columns_{c}']).map(lambda x: x.decode()) for c in ['i','r']
            }
            columns = pd.MultiIndex.from_arrays(list(columns.values()), names=columns.keys())
        else:
            columns = pd.Series(f['columns']).map(lambda x: x.decode())
        forcedoutage_hourly = pd.DataFrame(
            index=pd.to_datetime(pd.Series(f['index']).map(lambda x: x.decode())),
            columns=columns,
            data=f['data'],
        ).tz_localize('UTC').tz_convert(tz)
    return forcedoutage_hourly


#%%### Main function
def main(reeds_path, inputs_case, hdftype='h5py', debug=0, interactive=False):
    """
    """
    # #%% Settings for testing
    # reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # inputs_case = os.path.join(
    #     reeds_path,'runs',
    #     'v20240709_tforM0_USA','inputs_case','')
    # hdftype = 'h5py'
    # debug = 1
    # interactive = True

    #%% Derived inputs
    sw = reeds.io.get_switches(inputs_case)
    val_ba = (
        pd.read_csv(os.path.join(inputs_case, 'val_ba.csv'), header=None)
        .squeeze(1).values
    )
    ## Static forced outage rates (for filling empties)
    outage_forced_static = pd.read_csv(
        os.path.join(inputs_case, 'outage_forced_static.csv'),
        header=None, index_col=0,
    ).squeeze(1)
    outage_forced_static.index = outage_forced_static.index.str.lower()
    outage_forced_static = outage_forced_static.drop(ignore_techs, errors='ignore').copy()

    tech_subset_table = get_tech_subset_table(inputs_case)

    #%% Input data
    if sw.GSw_OutageScen.lower() == 'static':
        ### Fill static data for all techs and modeled regions
        fulltimeindex = reeds.timeseries.get_timeindex(sw.resource_adequacy_years_list)
        forcedoutage_prefill = pd.concat(
            {
                (i,r): pd.Series(index=fulltimeindex, data=outage_forced_static[i])
                for i in outage_forced_static.index for r in val_ba
            }, axis=1, names=('i','r'),
        )
    else:
        ### Load temperatures
        print('Load temperatures')
        temperatures = get_temperatures(inputs_case)
        fits_forcedoutage_in = pd.read_csv(
            os.path.join(inputs_case, 'temperature_outage_forced.csv'),
            comment='#',
        ).pivot(index='deg_celsius', columns='prime_mover', values='outage_frac')

        ### Extrapolate slopes and fill gaps in integer steps
        fits_forcedoutage = extrapolate_forward_backward(
            dfin=fits_forcedoutage_in, xmin=temp_min, xmax=temp_max)

        ### Get temperature-dependent outage rate by prime mover and state
        print('Calculate outage rates')
        forcedoutage_pm = pd.concat(
            {pm: temperatures.replace(fits_forcedoutage[pm]) for pm in fits_forcedoutage},
            axis=1, names=('prime_mover',),
        ).astype(np.float32)

        ### Map from prime movers to techs
        forcedoutage_prefill = pd.concat(
            {
                i: forcedoutage_pm[pm]
                for pm in fits_forcedoutage_in
                for i in tech_subset_table.loc[primemover2techgroup[pm]].unique()
            },
            axis=1, names=('i',)
        )

    #%% Identify techs with nonzero FORs that are not yet included in hourly FORs
    techlist = get_techlist_after_bans(inputs_case)
    keep_techs = [i for i in outage_forced_static.index if i in techlist]

    included_techs = forcedoutage_prefill.columns.get_level_values('i').unique()
    missing_techs = [
        c for c in outage_forced_static.loc[outage_forced_static > 0].index
        # if (c.lower() not in included_techs)
        if ((c.lower() not in included_techs) and (c.lower() in keep_techs))
    ]
    print(f"included ({len(included_techs)}): {' '.join(included_techs)}")
    print(f"missing ({len(missing_techs)}): {' '.join(missing_techs)}")

    #%% Fill data for missing techs
    if len(missing_techs):       
        forcedoutage_filled = pd.concat(
            {
                (i,r): pd.Series(index=forcedoutage_prefill.index, data=outage_forced_static[i])
                for i in missing_techs for r in val_ba
            },
            axis=1, names=('i','r'),
        )
        forcedoutage_hourly = pd.concat([forcedoutage_prefill, forcedoutage_filled], axis=1)
    else:
        forcedoutage_hourly = forcedoutage_prefill

   
    #%% forcedoutage_hourly.h5 has a unique format so aggregate it now if necessary
    val_r = pd.read_csv(os.path.join(inputs_case, 'val_r.csv'), header=None).squeeze(1)
    r2aggreg = pd.read_csv(
        os.path.join(inputs_case, 'hierarchy_original.csv')
    ).rename(columns={'ba':'r'}).set_index('r').aggreg
    agglevel_variables = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)

    county2zone = pd.read_csv(os.path.join(inputs_case, 'county2zone.csv'), dtype={'FIPS':str})
    county2zone.FIPS = 'p' + county2zone.FIPS
    county2zone = county2zone.set_index('FIPS').ba.loc[agglevel_variables['county_regions']]

    if 'aggreg' in agglevel_variables['agglevel']:
        county2zone = county2zone.map(r2aggreg)
        forcedoutage_hourly.columns = forcedoutage_hourly.columns.map(
            lambda x: (x[0], r2aggreg[x[1]]))
        forcedoutage_hourly = forcedoutage_hourly.groupby(axis=1, level=['i','r']).mean()

    if 'county' in agglevel_variables['agglevel']:
        forcedoutage_hourly = pd.concat(
            {
                i: (
                    forcedoutage_hourly[i]
                    ## Get the zone for each county, or if it's already a zone, keep the zone.
                    ## Every county in a zone thus gets the same profile.
                    [val_r.map(lambda x: county2zone.get(x,x))]
                    ## Set the actual regions (could be mix of zones and counties) as index
                    .set_axis(val_r.values, axis=1)
                )
                for i in forcedoutage_hourly.columns.get_level_values('i').unique()
            },
            axis=1, names=('i','r'),
        )

    #%% Write it at tech resolution
    print('Write outage rates')
    outfile = os.path.join(inputs_case, 'forcedoutage_hourly.h5')
    if hdftype.lower() in h5pytypes:
        names = ['i', 'r']
        namelengths = {
            name: forcedoutage_hourly.columns.get_level_values(name).map(len).max()
            for name in names
        }
        with h5py.File(outfile, 'w') as f:
            f.create_dataset('index', data=forcedoutage_hourly.index, dtype='S29')
            ## Save both the individual column levels and the single-level delimited version
            for name in names:
                f.create_dataset(
                    f'columns_{name}',
                    data=forcedoutage_hourly.columns.get_level_values(name),
                    dtype=f'S{namelengths[name]}')
            f.create_dataset(
                'columns',
                data=forcedoutage_hourly.columns.map(lambda x: '|'.join(x)).rename('|'.join(names)),
                dtype=f'S{sum(namelengths.values()) + 1}')
            f.create_dataset(
                'data', data=forcedoutage_hourly, dtype=np.float32,
                compression='gzip', compression_opts=4,
            )
    else:
        forcedoutage_hourly.to_hdf(
            outfile, mode='w', complevel=4, key='data', format='fixed')

    #%% Test it
    if debug:
        #%% Prep plots
        import matplotlib.pyplot as plt
        from reeds import plots
        plots.plotparams()
        case = os.path.dirname(inputs_case.rstrip(os.sep))
        figpath = os.path.join(case,'outputs','hourly')
        os.makedirs(figpath, exist_ok=True)

        #%% Plot the fits
        plt.close()
        f,ax = plt.subplots()
        (fits_forcedoutage*100).plot(ax=ax)
        ax.set_ylabel('Outage rate [%]')
        ax.set_xlabel('Temperature [°C]')
        ax.set_ylim(0,100)
        ax.set_xlim(temp_min, temp_max)
        plots.despine(ax)
        plt.savefig(os.path.join(figpath, 'FOR-fits.png'))
        if interactive:
            plt.show()
        else:
            plt.close()

        #%% Make sure output is readable
        if hdftype.lower() in h5pytypes:
            get_forcedoutage_hourly(case)
        else:
            pd.read_hdf(outfile)

        #%% Plot forced outage rates
        dfmap = reeds.io.get_dfmap(case)
        dfzones = dfmap['r'].loc[val_ba]
        aggfunc = 'mean'

        for pm in primemover2techgroup:
            dfdata = forcedoutage_pm[pm].copy() * 100

            plt.close()
            f, ax = plots.map_years_months(
                dfzones=dfzones, dfdata=dfdata, aggfunc=aggfunc,
                title=f"Monthly {aggfunc}\nforced outage rate,\n{pm} [%]",
            )
            plt.savefig(os.path.join(figpath, f'FOR_monthly-{aggfunc}-{pm}.png'))
            if interactive:
                plt.show()
            else:
                plt.close()


#%%### Run it
if __name__ == '__main__':
    #%% Parse args
    parser = argparse.ArgumentParser(
        description='Calculate temperature-dependent forced-outage rates',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('reeds_path', help='ReEDS-2.0 directory')
    parser.add_argument('inputs_case', help='ReEDS-2.0/runs/{case}/inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    #%% Run it
    main(reeds_path=reeds_path, inputs_case=inputs_case)

    #%% All done
    reeds.log.toc(
        tic=tic, year=0, process='input_processing/outage_rates.py', 
        path=os.path.join(inputs_case,'..'),
    )
