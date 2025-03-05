### Imports
import os
import sys
import re
import datetime
import h5py
import ctypes
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
from pandas.api.types import is_float_dtype

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if 'runs' in reeds_path.split(os.path.sep):
    reeds_path = reeds_path[: reeds_path.index(os.sep + 'runs' + os.sep)]

#   ########  ########    ###    ########
#   ##     ## ##         ## ##   ##     ##
#   ##     ## ##        ##   ##  ##     ##
#   ########  ######   ##     ## ##     ##
#   ##   ##   ##       ######### ##     ##
#   ##    ##  ##       ##     ## ##     ##
#   ##     ## ######## ##     ## ########


### Read files from the repo
def inflatifier(inyear, outyear, inflation):
    if inyear < outyear:
        return inflation.loc[inyear + 1 : outyear, 'inflation_rate'].cumprod()[outyear]
    elif inyear > outyear:
        return 1 / inflation.loc[outyear + 1 : inyear, 'inflation_rate'].cumprod()[inyear]
    else:
        return 1


def get_inflatable(inflationpath=None, tmin=1960, tmax=2050):
    """Get an [inyear,outyear] lookup table for inflation"""
    if inflationpath is None:
        filepath = os.path.join(reeds_path, 'inputs', 'financials', 'inflation_default.csv')
    else:
        filepath = inflationpath
    inflation = pd.read_csv(filepath, index_col='t')
    assert tmin >= inflation.index.min()
    assert tmax <= inflation.index.max()
    ### Make the output table
    inflatable = {}
    for inyear in range(tmin, tmax + 1):
        for outyear in range(tmin, tmax + 1):
            inflatable[inyear, outyear] = inflatifier(inyear, outyear, inflation)
    inflatable = pd.Series(inflatable)
    return inflatable


### Read files from the repo or from a ReEDS case
def get_hierarchy(case=None, original=False, country='USA'):
    """Get hierarchy for ReEDs case if provided, or for country if case not provided"""
    if case:
        if original:
            filepath = os.path.join(case, 'inputs_case', 'hierarchy_original.csv')
        else:
            filepath = os.path.join(case, 'inputs_case', 'hierarchy.csv')
    else:
        filepath = os.path.join(reeds_path, 'inputs', 'hierarchy.csv')
    hierarchy = (
        pd.read_csv(filepath)
        .rename(columns={'*r': 'r', 'ba': 'r'})
        .set_index('r')
        .drop(columns=['st_interconnect'], errors='ignore')
    )
    hierarchy = hierarchy.loc[hierarchy.country.str.lower() == country.lower()].copy()
    return hierarchy


def get_zonemap(case=None):
    """
    Get geodataframe of model zones, applying aggregation if necessary
    """
    if case:
        agglevel_variables = reeds.spatial.get_agglevel_variables(
            reeds_path,
            os.path.join(case, 'inputs_case'),
        )

    else:
        agglevel_variables = {'lvl': 'ba'}

    # Mixed resolution procedure
    if agglevel_variables['lvl'] == 'mult':
        ### Model zones
        dfba = gpd.read_file(os.path.join(reeds_path, 'inputs', 'shapefiles', 'US_PCA'))
        ### Use transmission endpoints from reV
        endpoints = gpd.read_file(
            os.path.join(reeds_path, 'inputs', 'shapefiles', 'transmission_endpoints')
        ).set_index('ba_str')
        endpoints['x'] = endpoints.centroid.x
        endpoints['y'] = endpoints.centroid.y

        dfba['x'] = dfba['rb'].map(endpoints.x)
        dfba['y'] = dfba['rb'].map(endpoints.y)
        dfba['centroid_x'] = dfba.geometry.centroid.x
        dfba['centroid_y'] = dfba.geometry.centroid.y

        # Filter to regions being solved at BA resolution
        dfba = dfba[dfba['rb'].isin(agglevel_variables['ba_regions'])].set_index('rb')

        if 'aggreg' in agglevel_variables['agglevel']:
            r2aggreg = (
                pd.read_csv(os.path.join(case, 'inputs_case', 'hierarchy_original.csv'))
                .rename(columns={'ba': 'r'})
                .set_index('r')
                .aggreg
            )
            aggreg2anchorreg = pd.read_csv(
                os.path.join(case, 'inputs_case', 'aggreg2anchorreg.csv')
            )
            aggreg2anchorreg = aggreg2anchorreg[
                aggreg2anchorreg['aggreg'].isin(agglevel_variables['ba_regions'])
            ]
            dfba = dfba.reset_index()
            dfba.rb = dfba.rb.map(r2aggreg)
            dfba = dfba.dissolve('rb').loc[aggreg2anchorreg.aggreg].copy()

        ### Get the county map
        crs = 'ESRI:102008'
        dfcounty = gpd.read_file(
            os.path.join(reeds_path, 'inputs', 'shapefiles', 'US_COUNTY_2022')
        ).to_crs(crs)
        state_fips = pd.read_csv(
            os.path.join(reeds_path, 'inputs', 'shapefiles', "state_fips_codes.csv"),
            names=["STATE", "STCODE", "STATEFP", "CONUS"],
            dtype={"STATEFP": "string"},
            header=0,
        )
        state_fips = state_fips.loc[state_fips['CONUS'], :]
        dfcounty = dfcounty.merge(state_fips, on="STATEFP")
        dfcounty = dfcounty[['rb', 'NAMELSAD', 'STATE_x', 'geometry']]

        ## Use the centroid for both the transmission endpoint and centroid
        for prefix in ['', 'centroid_']:
            dfcounty[prefix + 'x'] = dfcounty.geometry.centroid.x
            dfcounty[prefix + 'y'] = dfcounty.geometry.centroid.y

        dfcounty.rename(columns={'NAMELSAD': 'county', 'STCODE': 'st'}, inplace=True)

        # Filter to regions being solved at county resolution
        dfcounty = dfcounty[dfcounty['rb'].isin(agglevel_variables['county_regions'])].set_index(
            'rb'
        )
        dfcounty = dfcounty.drop(columns=['county'])

        # Combine BA and County
        dfcounty = dfcounty.to_crs(dfba.crs)
        dfba = pd.concat([dfba, dfcounty])

        ### Include all hierarchy levels
        hierarchy = get_hierarchy(case)

        for col in hierarchy:
            dfba[col] = dfba.index.map(hierarchy[col])

    ######## Single Resolution Procedure ########
    else:
        ### Check if resolution is at county level
        if case:
            sw = pd.read_csv(
                os.path.join(case, 'inputs_case', 'switches.csv'), header=None, index_col=0
            ).squeeze(1)
        else:
            sw = pd.Series()

        ## Backwards compatibility
        if 'GSw_RegionResolution' not in sw:
            sw['GSw_RegionResolution'] = 'ba'

        if sw.GSw_RegionResolution != 'county':
            hierarchy = get_hierarchy(case, original=True)
            ### Model zones
            dfba = gpd.read_file(
                os.path.join(reeds_path, 'inputs', 'shapefiles', 'US_PCA')
            ).set_index('rb')
            ### Use transmission endpoints from reV
            endpoints = gpd.read_file(
                os.path.join(reeds_path, 'inputs', 'shapefiles', 'transmission_endpoints')
            ).set_index('ba_str')
            endpoints['x'] = endpoints.centroid.x
            endpoints['y'] = endpoints.centroid.y

            dfba['x'] = dfba.index.map(endpoints.x)
            dfba['y'] = dfba.index.map(endpoints.y)
            dfba['centroid_x'] = dfba.geometry.centroid.x
            dfba['centroid_y'] = dfba.geometry.centroid.y

        else:
            hierarchy = (
                pd.read_csv(os.path.join(case, 'inputs_case', 'hierarchy.csv'))
                .rename(columns={'*r': 'r', 'ba': 'r'})
                .set_index('r')
            )
            ### Get the county map
            crs = 'ESRI:102008'
            dfba = gpd.read_file(
                os.path.join(reeds_path, 'inputs', 'shapefiles', 'US_COUNTY_2022')
            ).to_crs(crs)

            ### Add US state code and drop states outside of CONUS
            state_fips = pd.read_csv(
                os.path.join(reeds_path, 'inputs', 'shapefiles', "state_fips_codes.csv"),
                names=["STATE", "STCODE", "STATEFP", "CONUS"],
                dtype={"STATEFP": "string"},
                header=0,
            )
            state_fips = state_fips.loc[state_fips['CONUS'], :]
            dfba = dfba.merge(state_fips, on="STATEFP")
            dfba = dfba[['rb', 'NAMELSAD', 'STATE_x', 'geometry']].set_index('rb')

            ## Use the centroid for both the transmission endpoint and centroid
            for prefix in ['', 'centroid_']:
                dfba[prefix + 'x'] = dfba.geometry.centroid.x
                dfba[prefix + 'y'] = dfba.geometry.centroid.y

            dfba.rename(columns={'NAMELSAD': 'county', 'STATE_x': 'st'}, inplace=True)

        ### Include all hierarchy levels
        for col in hierarchy:
            dfba[col] = dfba.index.map(hierarchy[col])

    return dfba


def get_dfmap(case=None):
    """Get dictionary of maps at different hierarchy levels"""
    hierarchy = get_hierarchy(case, original=True).drop(columns=['aggreg'], errors='ignore')

    mapsfile = os.path.join(str(case), 'inputs_case', 'maps.gpkg')
    if os.path.exists(mapsfile):
        dfmap = {}
        for level in ['r'] + list(hierarchy.columns):
            dfmap[level] = gpd.read_file(mapsfile, layer=level).rename(columns={'rb': 'r'})
            dfmap[level] = dfmap[level].set_index(dfmap[level].columns[0])
        return dfmap

    dfba = get_zonemap(case)

    dfmap = {'r': dfba.dropna(subset='country').copy()}
    dfmap['r']['centroid_x'] = dfmap['r'].centroid.x
    dfmap['r']['centroid_y'] = dfmap['r'].centroid.y
    for col in hierarchy:
        dfmap[col] = dfba.copy()
        dfmap[col]['geometry'] = dfmap[col].buffer(0.0)
        dfmap[col] = dfmap[col].dissolve(col)
        for prefix in ['', 'centroid_']:
            dfmap[col][prefix + 'x'] = dfmap[col].centroid.x
            dfmap[col][prefix + 'y'] = dfmap[col].centroid.y

    return dfmap


### Read files from a ReEDS case
def read_output(case, filename=None, valname=None):
    """
    Read a ReEDS output csv file or a key from outputs.h5.
    If outputs.h5 doesn't exist, falls back to outputs/{filename}.csv file.

    Args:
        case: Path to a single ReEDS run folder
        filename: Name of a ReEDS output (e.g. 'cap', 'tran_out').
            If filename ends with '.csv', always read the .csv version.
            Otherwise, read the {filename} key from {case}/outputs/outputs.h5.
        valname (optional): If provided, rename 'Value' column to {valname}

    Returns:
        dict of pd.DataFrame's if filename is None, otherwise pd.DataFrame
    """
    h5path = os.path.join(case, 'outputs', 'outputs.h5')
    if os.path.exists(h5path) and not filename.endswith('.csv'):
        key = os.path.basename(filename)
        try:
            with h5py.File(h5path, 'r') as f:
                columns = [i.decode() for i in list(f[key]['columns'])]
                df = pd.DataFrame({col: f[key][col] for col in columns})
            for col in df:
                if df[col].dtype == 'O':
                    df[col] = df[col].str.decode('utf-8')
        except KeyError:
            ## Empty dataframes aren't written to h5 file, so make one ourselves
            e_report_params = pd.read_csv(
                os.path.join(case, 'e_report_params.csv'),
                comment='#',
            )
            _index = e_report_params.loc[
                e_report_params.param.map(lambda x: x.split('(')[0]) == key, 'param'
            ].squeeze()
            if not len(_index):
                raise KeyError(f"{filename} is not in {h5path}")
            index = _index.split('(')[-1].strip(')').split(',')
            df = pd.DataFrame(columns=index + ['Value'])
    else:
        _filename = filename if filename.endswith('.csv') else filename + '.csv'
        df = pd.read_csv(os.path.join(case, 'outputs', _filename))

    if valname is not None:
        df = df.rename(columns={'Value': valname})
    df = df.rename(columns={'allh': 'h', 'eall': 'e'})
    to_retype = df.dtypes.loc[df.dtypes == 'category'].index
    for col in to_retype:
        if col in df:
            df = df.astype({col: str})

    return df


def get_report_sheetmap(case):
    """
    Create a dictionary of report.xlsx fields to excel sheet names
    """
    import openpyxl

    excel = openpyxl.load_workbook(
        os.path.join(case, 'outputs', 'reeds-report', 'report.xlsx'),
        read_only=True,
        keep_links=False,
    )
    sheets = excel.sheetnames
    val2sheet = dict(zip([sheet.split('_', maxsplit=1)[-1] for sheet in sheets], sheets))
    return val2sheet


def read_report(case, sheet=None, val2sheet=None, reportname='reeds-report'):
    """
    Read a ReEDS bokeh report.xlsx.

    Args:
        case: Path to a single ReEDS run folder
        sheet: Name of a sheet from report.xlsx (written by bokeh).
            If sheet is a sheet name (with or without leading number), return that sheet.
            If sheet is None, return a dictionary of all sheets.
        val2sheet: Dictionary produced by get_report_sheetmap(). Keys are sheet names
            without leading numbers; values are full sheet names.
        reportname: directory of bokeh outputs (e.g. 'reeds-report', 'reeds-report-reduced')

    Returns:
        pd.DataFrame (if sheet is not None) else dict of dataframes
    """
    if val2sheet is None:
        val2sheet = get_report_sheetmap(case)
    if sheet is None:
        dfout = {}
        for val, sheet in val2sheet.items():
            dfout[val] = pd.read_excel(
                os.path.join(case, 'outputs', reportname, 'report.xlsx'),
                sheet_name=sheet,
                engine='openpyxl',
            ).drop('scenario', axis=1, errors='ignore')
    else:
        _sheet = val2sheet.get(sheet, sheet)
        dfout = pd.read_excel(
            os.path.join(case, 'outputs', reportname, 'report.xlsx'),
            sheet_name=_sheet,
            engine='openpyxl',
        ).drop('scenario', axis=1, errors='ignore')
    return dfout


def get_param_value(opt_file, param_name, dtype=float, assert_exists=True):
    result = None
    with open(opt_file, mode="r") as f:
        line = f.readline()
        while line:
            if line.startswith(param_name):
                result = line
                break
            line = f.readline()
    if assert_exists:
        assert result, f"{param_name=} not found in {opt_file=}"
    return dtype(result.replace(param_name, "").replace("=", "").strip())


def standardize_case(case):
    """Remove inputs_case and trailing directory separator if present"""
    if 'inputs_case' in case:
        case = os.path.dirname(os.path.abspath(case))
    else:
        case = os.path.abspath(case)
    return case


def get_switches(case):
    """
    Get pd.Series of switch values from switches.csv, augur_switches.csv,
    and CPLEX opt file.
    Accepts either {case} or {case}/inputs_case as input.
    """
    case = standardize_case(case)
    inputs_case = os.path.join(case, 'inputs_case')
    ### ReEDS switches
    rsw = pd.read_csv(
        os.path.join(inputs_case, 'switches.csv'),
        index_col=0,
        header=None,
    ).squeeze(1)
    ### Augur-specific switches
    asw = pd.read_csv(
        os.path.join(case, 'ReEDS_Augur', 'augur_switches.csv'),
        index_col='key',
    )
    for i, row in asw.iterrows():
        if row['dtype'] == 'list':
            row.value = row.value.split(',')
            try:
                row.value = [int(i) for i in row.value]
            except ValueError:
                pass
        elif row['dtype'] == 'boolean':
            row.value = False if row.value.lower() == 'false' else True
        elif row['dtype'] == 'str':
            row.value = str(row.value)
        elif row['dtype'] == 'int':
            row.value = int(row.value)
        elif row['dtype'] == 'float':
            row.value = float(row.value)
    ### Combine
    sw = pd.concat([rsw, asw.value])
    ### Add derivative switches
    sw['resource_adequacy_years_list'] = [int(y) for y in sw['resource_adequacy_years'].split('_')]
    sw['num_resource_adequacy_years'] = len(sw['resource_adequacy_years_list'])
    ### Get number of threads to use in PRAS
    opt_file = 'cplex.opt' if int(sw.GSw_gopt) == 1 else f'cplex.op{sw.GSw_gopt}'
    try:
        threads = get_param_value(os.path.join(case, opt_file), "threads", dtype=int)
    except FileNotFoundError:
        threads = get_param_value(os.path.join(reeds_path, opt_file), "threads", dtype=int)
    sw['threads'] = threads
    ### Determine whether run is on HPC
    sw['hpc'] = True if int(os.environ.get('REEDS_USE_SLURM', 0)) else False
    ### Add the run location
    sw['casedir'] = case
    sw['reeds_path'] = os.path.dirname(os.path.dirname(case))
    ### Get the number of hours per period to use in plots
    sw['hoursperperiod'] = {'day': 24, 'wek': 120, 'year': 24}[sw['GSw_HourlyType']]
    sw['periodsperyear'] = {'day': 365, 'wek': 73, 'year': 365}[sw['GSw_HourlyType']]

    return sw


def get_scalars(case=None, full=False):
    """
    Read the scalars.csv file and return:
        - the full dataframe if full = True
        - a pd.Series if full = False (default)
    """
    if case is None:
        filepath = os.path.join(reeds_path, 'inputs', 'scalars.csv')
    else:
        filepath = os.path.join(standardize_case(case), 'inputs_case', 'scalars.csv')

    if full:
        scalars = pd.read_csv(
            filepath,
            header=None,
            names=['name', 'value', 'comment'],
            index_col='name',
        )
    else:
        scalars = pd.read_csv(
            filepath,
            header=None,
            usecols=[0, 1],
            index_col=0,
        ).squeeze(1)

    return scalars


def read_h5py_file(filename):
    """Return dataframe object for a h5py file.

    This function returns a pandas dataframe of a h5py file. If the file has multiple dataset on it
    means it has yearly index.

    Parameters
    ----------
    filename
        File path to read

    Returns
    -------
    pd.DataFrame
        Pandas dataframe of the file
    """

    valid_data_keys = ["data", "cf", "load", "evload"]

    with h5py.File(filename, "r") as f:
        # Identify keys in h5 file and check for overlap with valid key set
        keys = list(f.keys())
        datakey = list(set(keys).intersection(valid_data_keys))

        # Adding safety check to validate that it only returns one key
        assert len(datakey) <= 1, f"Multiple keys={datakey} found for {filename}"
        datakey = datakey[0] if datakey else None

        if datakey in keys:
            # load data
            df = pd.DataFrame(f[datakey][:])
        else:
            df = pd.DataFrame()

        # add columns to data if supplied
        if 'columns' in keys:
            df.columns = (
                pd.Series(f["columns"])
                .map(lambda x: x if isinstance(x, str) else x.decode("utf-8"))
                .values
            )

        # add any index values
        idx_cols = [c for c in keys if re.match('index_[0-9]', c)]
        if len(idx_cols) > 0:
            idx_cols.sort()
            for idx_col in idx_cols:
                df[idx_col] = pd.Series(f[idx_col]).values
            df = df.set_index(idx_cols)

        # add index names if supplied
        if 'index_names' in keys:
            df.index.names = (
                pd.Series(f["index_names"])
                .map(lambda x: x if isinstance(x, str) else x.decode("utf-8"))
                .values
            )

    return df


def read_file(filename, parse_timestamps=False):
    """Return dataframe object of input file for multiple file formats.

    This function read multiple file formats for h5 file sand returns a dataframe from the file.

    Parameters
    ----------
    filename
        File path to read

    Returns
    -------
    pd.DataFrame
        Pandas dataframe of the file

    Raises
    ------
    FileNotFoundError
        If the file does not exists
    """
    if isinstance(filename, str):
        filename = Path(filename)

    if not filename.exists():
        raise FileNotFoundError(f"Mandatory file {filename} does not exist.")

    # We have two cases, either the data is contained as a single dataframe or we have multiple
    # datasets that composes the h5 file. For a single dataset we use pandas (since it is the most
    # convenient) and h5py for the custom h5 file.
    try:
        df = read_h5py_file(filename)
    except TypeError:
        df = pd.read_hdf(filename)

    # parse timestamps if specified and if there is a datetime index
    if parse_timestamps and ('datetime' in df.index.names):
        if not isinstance(df.index.get_level_values('datetime')[0], bytes):
            raise ValueError(
                f"The indices for timestamp-indexed dataframes should be encoded as bytes. \
                Please update {filename}."
            )

        df['datetime'] = pd.to_datetime(df.index.get_level_values('datetime').str.decode('utf-8'))
        if isinstance(df.index, pd.MultiIndex):
            df = df.droplevel('datetime').set_index('datetime', append=True)
        else:
            df = df.set_index('datetime')

    # All values being NaN indicates that the region filtering in copy_files.py removed all
    # data, leaving an empty dataframe.
    # Return an empty dataframe with the original file's index if all values are NaN
    if all(df.isnull().all()):
        df = df.drop(columns=df.columns)
        return df

    # NOTE: Some files are saved as float16, so we cast to float32 to prevent issues with
    # large/small numbers
    numeric_cols = [c for c in df if is_float_dtype(df[c].dtype)]
    df = df.astype({column: np.float32 for column in numeric_cols})

    return df


def read_pras_results(filepath):
    """Read a run_pras.jl output file"""
    with h5py.File(filepath, 'r') as f:
        keys = list(f)
        if len(keys):
            df = pd.concat({c: pd.Series(f[c][...]) for c in keys}, axis=1)
        else:
            df = pd.DataFrame()
        return df


#   ##      ## ########  #### ######## ########
#   ##  ##  ## ##     ##  ##     ##    ##
#   ##  ##  ## ##     ##  ##     ##    ##
#   ##  ##  ## ########   ##     ##    ######
#   ##  ##  ## ##   ##    ##     ##    ##
#   ##  ##  ## ##    ##   ##     ##    ##
#    ###  ###  ##     ## ####    ##    ########


### Write files
def get_dtype(col, df=None):
    if col.lower() == "value":
        return np.float32
    elif col in ["t", "allt"]:
        return np.uint16
    else:
        maxlength = df[col].str.len().max()
        return f"S{maxlength}"


def make_columns_unique(df):
    """
    Rename columns in place to avoid duplicates.
    Example: [*,*,r,*,t,Value] becomes [*,*.1,r,*.2,t,Value].
    """
    duplicated = df.columns.duplicated()
    if any(duplicated):
        columns_old = df.columns
        columns_new = []
        times_used = {}
        for i, column in enumerate(columns_old):
            if not duplicated[i]:
                columns_new.append(column)
            else:
                times_used[column] = times_used.get(column, 1)
                columns_new.append(f'{column}.{times_used[column]}')
                times_used[column] += 1
        df.columns = columns_new


def write_to_h5(
    dfwrite,
    key,
    filepath,
    attrs={},
    overwrite=False,
    compression='gzip',
    compression_opts=4,
    **kwargs,
):
    """ """
    with h5py.File(filepath, 'a') as f:
        if key in list(f):
            if overwrite:
                del f[key]
            else:
                raise ValueError(f'{key} is already used in {filepath}')

        group = f.create_group(key)
        ## Write columns to maintain order
        group.create_dataset(
            'columns',
            data=dfwrite.columns,
            dtype=f"S{dfwrite.columns.str.len().max()}",
        )
        if len(attrs):
            for key, val in attrs:
                group.attrs[key] = val
        ## Write data
        if len(dfwrite):
            for col in dfwrite:
                group.create_dataset(
                    col,
                    data=dfwrite[col],
                    dtype=dfwrite.dtypes[col],
                    compression=compression,
                    compression_opts=compression_opts,
                    **kwargs,
                )


def write_output_to_h5(
    df,
    key,
    filepath,
    drop_ctypes=False,
    verbose=0,
    **kwargs,
):
    """
    Write a dataframe of GAMS outputs to a .h5 file.
    This function only works for long dataframes where the single column
    of numeric data is named "Value".
    A group of name {key} is created in the .h5 file at {filepath} and each column
    in {df} is written to its own dataset.
    String columns need to be decoded when read.
    """
    dfwrite = df.copy()
    if not len(dfwrite):
        if verbose:
            print(f'{key} dataframe is empty, so it was not written to {filepath}')
        return dfwrite
    ## Sets have `c_bool(True)` as the value for every entry, so just
    ## drop the Value column if it's a set
    if drop_ctypes and ("Value" in dfwrite) and isinstance(dfwrite.Value.values[0], ctypes.c_bool):
        dfwrite.drop("Value", axis=1, inplace=True)
    ## Make column names unique (necessary if '*' is overused)
    make_columns_unique(dfwrite)
    ## Normalize column data types
    dfwrite = dfwrite.astype({col: get_dtype(col, dfwrite) for col in dfwrite})
    ### Write to .h5 file
    write_to_h5(dfwrite, key, filepath, **kwargs)

    return dfwrite


def write_profile_to_h5(df, filename, outfolder, compression_opts=4):
    """Writes dataframe to h5py file format used by ReEDS. Used in ReEDS and hourlize

    This function takes a pandas dataframe and saves to a h5py file. Data is saved to h5 file as follows:
        - the data itself is saved to a dataset named "data"
        - column names are saved to a dataset named "columns"
        - the index of the data is saved to a dataset named "index"; in the case of a multindex,
          each index is saved to a separate dataset with the format "index_{index order}"
        - the names of the index (or multindex) are saved to a dataset named "index_names"

    Parameters
    ----------
    df
        pandas dataframe to save to h5
    filename
        Name of h5 file
    outfolder
        Path to folder to save the file (in ReEDS this is usually the inputs_case folder)

    Returns
    -------
    None
    """
    outfile = os.path.join(outfolder, filename)
    with h5py.File(outfile, 'w') as f:
        # save index or multi-index in the format 'index_{index order}')
        for i in range(df.index.nlevels):
            # get values for specified index level
            indexvals = df.index.get_level_values(i)
            # save index
            if isinstance(indexvals[0], bytes):
                # if already formatted as bytes keep that way
                f.create_dataset(f'index_{i}', data=indexvals, dtype='S30')
            elif indexvals.name == 'datetime':
                # if we have a formatted datetime index that isn't bytes, save as such
                timeindex = (
                    indexvals.to_series().apply(datetime.datetime.isoformat).reset_index(drop=True)
                )
                f.create_dataset(f'index_{i}', data=timeindex.str.encode('utf-8'), dtype='S30')
            else:
                # Other indices can be saved using their data type
                f.create_dataset(f'index_{i}', data=indexvals, dtype=indexvals.dtype)

        # save index names
        index_names = pd.Index(df.index.names)
        if len(index_names):
            f.create_dataset(
                'index_names', data=index_names, dtype=f'S{index_names.map(len).max()}'
            )

        # save column names as string type
        if len(df.columns):
            f.create_dataset('columns', data=df.columns, dtype=f'S{df.columns.map(len).max()}')

        # save data if it exists
        if df.empty:
            pass
        elif len(df.dtypes.unique()) == 1:
            dtype = df.dtypes.unique()[0]
            f.create_dataset(
                'data',
                data=df.values,
                dtype=dtype,
                compression='gzip',
                compression_opts=compression_opts,
            )
        else:
            types = df.dtypes.unique()
            print(df)
            raise ValueError(f"{outfile} can only contain one datatype but it contains {types}")

        return df
