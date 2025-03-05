""" This script dumps outputs from gdx files to csvs
"""
# %% Imports
# System packages
import argparse
import datetime
import os
import site
import traceback
import sys

# Third-party packages
import pandas as pd
import gdxpds

import reeds

#%% Generic functions


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
            reeds.io.write_output_to_h5(
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
    parser.add_argument("case", help="ReEDS scenario name")
    parser.add_argument('--csv', '-c', action='store_true', help='write csv files')
    parser.add_argument('--xlsx', '-x', action='store_true', help='write xlsx file')

    args = parser.parse_args()
    case = args.case
    write_csv = args.csv
    write_xlsx = args.xlsx

    # #%% Inputs for debugging
    # case = os.path.expanduser('~/github2/ReEDS-2.0/runs/v20250302_commonM0_Pacific')

    #%% Set up logger
    reeds_path = os.path.abspath(os.path.dirname(__file__))
    site.addsitedir(os.path.join(reeds_path, 'input_processing'))
    try:
        from reeds.log import toc, makelog
        log = makelog(scriptname=__file__, logpath=os.path.join(case, "gamslog.txt"))
    except ModuleNotFoundError:
        print("reeds/log.py not found, so not logging output")

    print("Starting e_report_dump.py")

    # %%### Parse inputs and get switches
    outputs_path = os.path.join(case, "outputs")

    ### Get switches
    sw = reeds.io.get_switches(case)

    ### Get new file names if applicable
    dfparams = pd.read_csv(
        os.path.join(case, "e_report_params.csv"),
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
        os.path.join(outputs_path, f"rep_{os.path.basename(case)}.gdx")
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
            os.path.join(outputs_path, f"rep_powerfrac_{os.path.basename(case)}.gdx")
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
        dfin_timestamp = reeds.timeseries.timeslice_to_timestamp(case, 'h2_price_h')
        dfout_month = timestamp_to_month(dfin_timestamp)
        dfout_month.rename(columns={'Value':'$2004/kg'}).to_csv(
            os.path.join(outputs_path, 'h2_price_month.csv'), index=False)
    except Exception:
        if int(sw.GSw_H2):
            print(traceback.format_exc())

    #%% All done
    print("Completed e_report_dump.py")
    try:
        toc(tic=tic, year=0, path=case, process="e_report_dump.py")
    except NameError:
        print("reeds/log.py not found, so not logging output")
