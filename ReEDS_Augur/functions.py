# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 19:31:59 2021

@author: afrazier
"""
#%%### Imports
import numpy as np
import os
import sys
import logging
import pandas as pd
import datetime
import h5py
from glob import glob

#%%### Functions
def get_hierarchy(casepath):
    """
    Read the hierarchy file for this case and clean up the index.
    """
    hierarchy = pd.read_csv(
        os.path.join(casepath, 'inputs_case', 'hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    return hierarchy


def make_fulltimeindex():
    """
    Generate pandas index of 7x8760 timestamps in EST for 2007-2013,
    dropping December 31 on leap years.
    """
    fulltimeindex = np.ravel([
        pd.date_range(
            f'{y}-01-01', f'{y+1}-01-01', freq='H', inclusive='left', tz='EST',
        )[:8760]
        for y in range(2007,2014)
    ])
    return fulltimeindex


def read_pras_results(filepath):
    """Read a run_pras.jl output file"""
    with h5py.File(filepath, 'r') as f:
        keys = list(f)
        df = pd.concat({c: pd.Series(f[c][...]) for c in keys}, axis=1)
        return df


def makelog(scriptname, logpath):
    ### Set up logger
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    eh = logging.StreamHandler(sys.stderr)
    eh.setLevel(logging.CRITICAL)
    class StreamToLogger(object):
        """
        https://stackoverflow.com/questions/19425736/
        how-to-redirect-stdout-and-stderr-to-logger-in-python
        """
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level
            self.linebuf = ''

        def write(self, buf):
            for line in buf.rstrip().splitlines():
                self.logger.log(self.level, line.rstrip())
        
        def flush(self):
            pass

    logging.basicConfig(
        level=logging.INFO,
        format=(os.path.basename(scriptname)+' | %(asctime)s | %(levelname)s | %(message)s'),
        handlers=[logging.FileHandler(logpath, mode='a'), sh, eh],
    )
    log = logging.getLogger(__name__)
    sys.stdout = StreamToLogger(log, logging.INFO)
    sys.stderr = StreamToLogger(log, logging.ERROR)

    return log


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
    return dtype(result.replace(param_name,"").replace("=","").strip())


def get_switches(casedir):
    """
    """
    ### ReEDS switches
    rsw = pd.read_csv(
        os.path.join(casedir, 'inputs_case', 'switches.csv'),
        index_col=0, header=None).squeeze(1)
    ### Augur-specific switches
    asw = pd.read_csv(
        os.path.join(casedir, 'ReEDS_Augur', 'augur_switches.csv'),
        index_col='key')
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
    ### Format a few datatypes
    for key in ['osprey_years']:
        sw[key] = [int(y) for y in sw[key].split('_')]
    ### Get number of threads to use in Osprey/PRAS
    threads = get_param_value(os.path.join(casedir, 'cplex.opt'), "threads", dtype=int)
    sw['threads'] = threads
    ### Determine whether run is on HPC
    sw['hpc'] = True if int(os.environ.get('REEDS_USE_SLURM',0)) else False
    ### Add the run location
    sw['casedir'] = casedir
    sw['reeds_path'] = os.path.dirname(os.path.dirname(casedir))
    ### Get the number of hours per period to use in Osprey
    sw['hoursperperiod'] = {'day':24, 'wek':120, 'year':24}[sw['GSw_HourlyType']]
    sw['periodsperyear'] = {'day':365, 'wek':73, 'year':365}[sw['GSw_HourlyType']]

    return sw


def delete_csvs(sw):
    """
    Delete temporary csv, pkl, and h5 files
    """
    dropfiles = (
        glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"*_{sw['t']}.pkl"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"*_{sw['t']}.h5"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"*_{sw['t']}.csv"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','augur_data',f"osprey_outputs_{sw['t']}.gdx"))
        + glob(os.path.join(sw['casedir'],'ReEDS_Augur','PRAS',f"PRAS_{sw['t']}*.pras"))
    )

    for keyword in sw['keepfiles']:
        dropfiles = [f for f in dropfiles if not os.path.basename(f).startswith(keyword)]

    for f in dropfiles:
        os.remove(f)


def write_last_pras_runtime(year, path=''):
    """Write latest ReEDS2PRAS and PRAS runtimes from gamslog.txt to meta.csv"""
    times = {
        'start_ReEDS2PRAS': [],
        'stop_ReEDS2PRAS': [],
        'start_PRAS': [],
        'stop_PRAS': [],
    }
    prefix = '[ Info: '
    postfix = ' | '
    with open(os.path.join(path,'gamslog.txt'),'r') as f:
        for _line in f:
            line = _line.strip()
            if line.endswith('| Running ReEDS2PRAS with the following inputs:'):
                times['start_ReEDS2PRAS'].append(line[len(prefix):line.index(postfix)])
            elif line.endswith('| Finished ReEDS2PRAS'):
                times['stop_ReEDS2PRAS'].append(line[len(prefix):line.index(postfix)])
            elif line.endswith('| Running PRAS'):
                times['start_PRAS'].append(line[len(prefix):line.index(postfix)])
            elif line.endswith('| Finished PRAS'):
                times['stop_PRAS'].append(line[len(prefix):line.index(postfix)])
    for key, val in times.items():
        times[key] = [pd.Timestamp(t) for t in val][-1]
    durations = {
        process: (times[f'stop_{process}'] - times[f'start_{process}']).total_seconds()
        for process in ['ReEDS2PRAS','PRAS']
    }
    with open(os.path.join(path,'meta.csv'), 'a') as METAFILE:
        for process in durations:
            METAFILE.writelines(
                '{},{},{},{},{}\n'.format(
                    year,
                    process,
                    times[f'start_{process}'].isoformat(),
                    times[f'stop_{process}'].isoformat(),
                    durations[process],
                )
            )


def toc(tic, year, process, path=''):
    """
    append timing data to meta file
    """
    now = datetime.datetime.now()
    try:
        with open(os.path.join(path,'meta.csv'), 'a') as METAFILE:
            METAFILE.writelines(
                '{},{},{},{},{}\n'.format(
                    year, process,
                    datetime.datetime.isoformat(tic), datetime.datetime.isoformat(now),
                    (now-tic).total_seconds()
                )
            )
    except Exception:
        print('meta.csv not found or not writeable')
        pass


def dr_dispatch(poss_dr_changes, ts_length, hrs, eff=1):
    """
    Calculate the battery level and curtailment recovery profiles.
    Since everything here is in numpy, we can try using numba.jit to speed it up.
    """
    # Initialize some necessary arrays since numba can't do np.clip
    curt = np.where(poss_dr_changes > 0, poss_dr_changes, 0)
    avail = np.where(poss_dr_changes < 0, -poss_dr_changes, 0)
    # Initialize the dr shifting and curtailment recovery to be 0 in all hours
    curt_recovered = np.zeros((ts_length, poss_dr_changes.shape[1]))
    # Loop through all hours and identify how much curtailment that hour could
    # mitigate from the available load shifting
    for n in range(0, ts_length):
        n1 = max(0, n-hrs[0])
        n2 = min(ts_length, n+hrs[1])
        # maximum curtailment this hour can shift load into
        # calculated as the cumulative sum of curtailment across all hours
        # this hour can reach, identifying the max cumulative shifting allowed
        # and subtracting off the desired shifting that can't happen
        cum = np.cumsum(curt[n1:n2, :], axis=0)
        curt_shift = np.maximum(curt[n1:n2, :] - (cum - np.minimum(cum, avail[n, :] / eff)), 0)
        # Subtract realized curtailment reduction from appropriate hours
        curt[n1:n2, :] -= curt_shift
        # Record the amount of otherwise-curtailed energy that was
        # recovered during appropriate hours
        curt_recovered[n1:n2, :] += curt_shift
    return curt_recovered

def dr_capacity_credit(hrs, eff, ts_length, poss_dr_changes, marg_peak, cols,
                       maxhrs):
    """
    Determines the ratio of peak load that could be shifted by DR.
    """
    # Get the DR profiles
    # This is using the same function as curtailment, but with opposite meaning
    # ("how much can I increase load in this hour in order to reduce load in any
    # shiftable hours" instead of "how much can I decrease load in this hour
    # in order to increase load in any shiftable hours"), so the efficiency
    # gets applied to the opposite set of data. Hence the 1/eff.
    # If maxhrs is included, that is used as the total number of hours the
    # resource is able to be called. Really just for shed
    peak_shift = dr_dispatch(
        poss_dr_changes=poss_dr_changes,
        ts_length=ts_length, hrs=hrs, eff=1/eff
    )
    # Sort and only take maximum allowed hours
    sort_shift = np.sort(peak_shift, axis=0)[::-1]
    sort_shift = sort_shift[0:int(min(maxhrs, ts_length)), :]
    # Get the ratio of reduced peak to total peak
    return pd.melt(
        pd.DataFrame(data=[np.round(sort_shift.sum(0) / marg_peak, decimals=5), ],
                     columns=cols)
        )
