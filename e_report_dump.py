""" This script dumps outputs from gdx files to csvs
"""
# %% Imports
# System packages
import argparse
import ctypes
import datetime
import os
import site
import traceback
import sys
import h5py

# Third-party packages
import numpy as np
import pandas as pd
import gdxpds


#%% Generic functions
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


def dfdict_to_csv(dfdict, filepath, symbol_list=None, rename=dict(), decimals=6):
    """
    Write dictionary of dataframes to individual .csv files

    Inputs
    ------
    * rename: dictionary of file names that are different from the variable name
    """
    # unless a subset is specified, iterate over all keys in dict
    _symbol_list = dfdict.keys() if symbol_list is None else symbol_list

    # iterate over symbols and save as csv
    for symbol in _symbol_list:
        file_out = rename.get(symbol, symbol)
        try:
            df_out = (
                dfdict[symbol].records
                if "gdxpds" not in sys.modules
                else dfdict[symbol]
            )
        except Exception:
            print(f"Missing {symbol} in gdx, skipping.")
            continue

        print(f"Saving {symbol} as {file_out}.csv")

        # NOTE: Gams transfer appends junk to the end of the column name, this will
        # get rid of it. We can probably remove this if they change this
        # function in future versions.
        if "gdxpds" not in sys.modules and df_out is not None:
            df_out.columns = df_out.columns.str.replace(r"_\d+$", "", regex=True)

        # If df_out is empty just create an empty dataframe to save the data
        if df_out is None:
            df_out = pd.DataFrame()

        df_out.round(decimals).to_csv(os.path.join(filepath, f"{file_out}.csv"), index=False)


def write_to_h5(
    df,
    key,
    filepath,
    overwrite=False,
    drop_ctypes=False,
    verbose=0,
    compression='gzip',
    compression_opts=4,
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
    if (
        drop_ctypes
        and ("Value" in dfwrite)
        and isinstance(dfwrite.Value.values[0], ctypes.c_bool)
    ):
        dfwrite.drop("Value", axis=1, inplace=True)
    ## Make column names unique (necessary if '*' is overused)
    make_columns_unique(dfwrite)
    ## Normalize column data types
    dfwrite = dfwrite.astype({col: get_dtype(col, dfwrite) for col in dfwrite})
    ### Write to .h5 file
    with h5py.File(filepath, 'a') as f:
        if (key in list(f)):
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
        ## Write data
        for col in dfwrite:
            group.create_dataset(
                col,
                data=dfwrite[col],
                dtype=dfwrite.dtypes[col],
                compression=compression,
                compression_opts=compression_opts,
                **kwargs,
            )

    return dfwrite


def dfdict_to_h5(
    dfdict,
    filepath,
    overwrite=True,
    symbol_list=None,
    rename=dict(),
    errors="warn",
    **kwargs,
):
    """
    Write dictionary of dataframes to one .h5 file
    """
    ### unless a subset is specified, iterate over all keys in dict
    _symbol_list = dfdict.keys() if symbol_list is None else symbol_list

    ### Check for existing file
    _filepath = filepath if filepath.endswith(".h5") else filepath + ".h5"
    if os.path.exists(_filepath):
        if overwrite:
            os.remove(_filepath)
        else:
            raise NameError(
                f"{_filepath} already exists; to overwrite set overwrite=True"
            )
    ### iterate over symbols and add to .h5 file
    for key in _symbol_list:
        try:
            write_to_h5(
                df=dfdict[key],
                key=rename.get(key, key),
                filepath=_filepath,
                overwrite=overwrite,
                drop_ctypes=True,
            )
        except Exception as err:
            print(key)
            print(traceback.format_exc())
            if errors == "raise":
                raise Exception(err)


def dfdict_to_excel(
    dfdict,
    filepath,
    overwrite=True,
    symbol_list=None,
    rename=dict(),
    errors="warn",
    **kwargs,
):
    """
    Write dictionary of dataframes to one .xlsx file
    """
    ### unless a subset is specified, iterate over all keys in dict
    _symbol_list = dfdict.keys() if symbol_list is None else symbol_list

    ### Check for existing file
    _filepath = filepath if filepath.endswith(".xlsx") else filepath + ".xlsx"
    if os.path.exists(_filepath):
        if overwrite:
            os.remove(_filepath)
        else:
            raise NameError(
                f"{_filepath} already exists; to overwrite set overwrite=True"
            )
    ### iterate over symbols and add to .h5 file
    with pd.ExcelWriter(_filepath) as w:
        for key in _symbol_list:
            try:
                dfdict[key].to_excel(w, sheet_name=rename.get(key, key), index=False)
            except Exception as err:
                print(key)
                print(traceback.format_exc())
                if errors == "raise":
                    raise Exception(err)


def write_dfdict(
    dfdict,
    outputs_path,
    write_csv=False,
    write_xlsx=False,
    overwrite=True,
    symbol_list=None,
    rename=dict(),
    errors="warn",
    **kwargs,
):
    """
    Write dictionary of dataframes
    Notes
    * If filepath ends with .h5 or .xlsx, filetype will be overwritten to match
    * To read single dataframes from the resulting .h5 file, use:
      `pd.read_hdf('path/to/outputs.h5', 'cap')` (for example)
    """
    ## Always write the h5
    dfdict_to_h5(
        dfdict=dfdict,
        filepath=os.path.join(outputs_path, 'outputs.h5'),
        overwrite=overwrite,
        symbol_list=symbol_list,
        rename=rename,
        errors=errors,
        **kwargs,
    )
    if write_csv:
        dfdict_to_csv(
            dfdict=dfdict,
            filepath=outputs_path,
            symbol_list=symbol_list,
            rename=rename,
        )
    if write_xlsx:
        dfdict_to_excel(
            dfdict=dfdict,
            filepath=os.path.join(outputs_path, 'outputs.xlsx'),
            overwrite=overwrite,
            symbol_list=symbol_list,
            rename=rename,
            errors=errors,
            **kwargs,
        )


#%% Functions for extra postprocessing of particular outputs
def timeslice_to_timestamp(case, param):
    ### Load the timestamps and other ReEDS settings
    # timestamps = pd.read_csv(os.path.join(case,'inputs_case','timestamps.csv'))
    # h_szn = pd.read_csv(os.path.join(case,'inputs_case','h_szn.csv'))
    h_dt_szn = pd.read_csv(os.path.join(case,'inputs_case','h_dt_szn.csv'))
    sw = pd.read_csv(
        os.path.join(runname, 'inputs_case', 'switches.csv'), header=None, index_col=0
    ).squeeze(1)
    sw['GSw_HourlyWeatherYears'] = [int(y) for y in sw['GSw_HourlyWeatherYears'].split('_')]
    ### Get the timestamps for the modeled weather yeras
    hs = h_dt_szn.loc[
        h_dt_szn.year.isin(sw['GSw_HourlyWeatherYears']),
        'h'
    ].to_frame()
    hs['timestamp'] = pd.concat([
        pd.Series(
            pd.date_range(
                f'{y}-01-01', f'{y+1}-01-01', inclusive='left', freq='H', tz='EST',
            )[:8760])
        for y in sw['GSw_HourlyWeatherYears']
    ]).values
    hs = hs.set_index('timestamp').h.tz_localize('UTC').tz_convert('EST')
    ### Load the ReEDS output file
    rename = {'allh':'h', 'allt':'t'}
    dfin_timeslice = pd.read_csv(
        os.path.join(case,'outputs',f'{param}.csv')
    ).rename(columns=rename)
    ## check if empty
    if dfin_timeslice.empty:
        raise Exception(f'{param}.csv is empty; skipping timestamp processing')
    indices = [c for c in dfin_timeslice if c != 'Value']
    if 'h' not in indices:
        raise Exception(f"{param} does not have an h index: {indices}")
    indices_fixed = [c for c in indices if c != 'h']
    ### Convert to an hourly timeseries
    dfout_h = (
        dfin_timeslice
        .pivot(index='h', columns=indices_fixed, values='Value')
        ## Create entries for each timestamp but labeled by timeslices
        .loc[hs]
        .fillna(0)
        ## Add the timestamp index
        .set_index(hs.index)
    )
    return dfout_h


def timestamp_to_month(dfin_timestamp):
    """
    Index should be a DateTimeIndex
    Output is average over month
    """
    dfout_month = (
        dfin_timestamp.groupby(dfin_timestamp.index.month).mean()
        .rename_axis('month')
        .T.stack('month').rename('Value')
        .reset_index()
    )
    ## Convert format of month for plexos
    dfout_month['month'] = dfout_month['month'].astype(str).map('M{:0>2}'.format)
    return dfout_month


#%% Procedure
if __name__ == '__main__':
    tic = datetime.datetime.now()
    # parse arguments
    parser = argparse.ArgumentParser(
        description="Convert ReEDS run results from gdx to specified filetype"
    )
    parser.add_argument("runname", help="ReEDS scenario name")
    parser.add_argument('--csv', '-c', action='store_true', help='write csv files')
    parser.add_argument('--xlsx', '-x', action='store_true', help='write xlsx file')

    args = parser.parse_args()
    runname = args.runname
    write_csv = args.csv
    write_xlsx = args.xlsx

    # #%% Inputs for debugging
    # runname = os.path.expanduser('~/github2/ReEDS-2.0/runs/v20260106_h5M0_Pacific')

    #%% Set up logger
    reeds_path = os.path.abspath(os.path.dirname(__file__))
    site.addsitedir(os.path.join(reeds_path, 'input_processing'))
    try:
        from ticker import toc, makelog
        log = makelog(scriptname=__file__, logpath=os.path.join(runname, "gamslog.txt"))
    except ModuleNotFoundError:
        print("ticker.py not found, so not logging output")

    print("Starting e_report_dump.py")

    # %%### Parse inputs and get switches
    outputs_path = os.path.join(runname, "outputs")

    ### Get switches
    sw = pd.read_csv(
        os.path.join(runname, "inputs_case", "switches.csv"), header=None, index_col=0
    ).squeeze(1)

    ### Get new file names if applicable
    dfparams = pd.read_csv(
        os.path.join(runname, "e_report_params.csv"),
        comment="#",
        index_col="param",
    )
    rename = dfparams.loc[~dfparams.output_rename.isnull(), "output_rename"].to_dict()
    ## drop the indices
    rename = {k.split("(")[0]: v for k, v in rename.items()}
    print(f"renamed parameters: {rename}")

    # %%### Write results for each gdx file
    ### outputs gdx
    print("Loading outputs gdx")
    dict_out = gdxpds.to_dataframes(
        os.path.join(outputs_path, f"rep_{os.path.basename(runname)}.gdx")
    )
    print("Finished loading outputs gdx")

    write_dfdict(
        dfdict=dict_out,
        outputs_path=outputs_path,
        write_csv=write_csv,
        write_xlsx=write_xlsx,
        rename=rename,
    )

    ### powerfrac results
    if int(sw.GSw_calc_powfrac):
        print("Loading powerfrac gdx")
        dict_powerfrac = gdxpds.to_dataframes(
            os.path.join(outputs_path, f"rep_powerfrac_{os.path.basename(runname)}.gdx")
        )
        print("Finished loading powerfrac gdx")

        dfdict_to_csv(
            dict_powerfrac,
            outputs_path=outputs_path,
            rename=rename,
        )

    #%% Special handling of particular outputs
    ## Hydrogen prices by month
    try:
        dfin_timestamp = timeslice_to_timestamp(runname, 'h2_price_h')
        dfout_month = timestamp_to_month(dfin_timestamp)
        dfout_month.rename(columns={'Value':'$2004/kg'}).to_csv(
            os.path.join(outputs_path, 'h2_price_month.csv'), index=False)
    except Exception:
        if int(sw.GSw_H2):
            print(traceback.format_exc())

    #%% All done
    print("Completed e_report_dump.py")
    try:
        toc(tic=tic, year=0, path=runname, process="e_report_dump.py")
    except NameError:
        print("ticker.py not found, so not logging output")
