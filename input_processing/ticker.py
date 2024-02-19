#%% Imports
import os
import sys
import logging
from datetime import datetime
import pandas as pd

#%% Functions
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
                if line.strip() != '^':
                    self.logger.log(self.level, line.rstrip())
        
        def flush(self):
            pass

    logging.basicConfig(
        level=logging.INFO,
        format=(os.path.basename(scriptname)+' | %(asctime)s | %(levelname)s | %(message)s'),
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(logpath, mode='a'), sh, eh],
    )
    log = logging.getLogger(__name__)
    sys.stdout = StreamToLogger(log, logging.INFO)
    sys.stderr = StreamToLogger(log, logging.ERROR)

    return log


def toc(tic, year, process, path=''):
    """append timing data to meta file"""
    now = datetime.now()
    try:
        with open(os.path.join(path,'meta.csv'), 'a') as METAFILE:
            METAFILE.writelines(
                '{year},{process},{start},{stop},{elapsed}\n'.format(
                    year=year, process=process,
                    start=datetime.isoformat(tic),
                    stop=datetime.isoformat(now),
                    elapsed=(now-tic).total_seconds()
                )
            )
    except Exception:
        print('meta.csv not found or not writeable')
        pass


def get_solve_times(path=''):
    """Get all solve times, disaggregated by GAMS/barrier/crossover/remainder.
    Disaggregation only works when using CPLEX as the solver."""
    # path = '/Users/pbrown/github/ReEDS-2.0/runs/v20240111_stressM0_stress_WECC_crossover'
    lengths = {
        'gams': {},
        'barrier': {},
        'crossover': {},
        'total': {},
    }
    times = {
        'start': {},
        'stop': {},
    }
    with open(os.path.join(path,'gamslog.txt'),'r') as f:
        for _line in f:
            line = _line.strip()
            ## Get the year/iteration
            if line.startswith('--stress_year'):
                stress_year = line.split()[1]
            ## Get the solve durations
            if line.startswith('--- Executing CPLEX'):
                x = 'elapsed '
                lengths['gams'][stress_year] = pd.Timedelta(line[line.index(x)+len(x):])
            elif line.startswith('Barrier time = '):
                x = 'Barrier time = '
                lengths['barrier'][stress_year] = (
                    pd.Timedelta(seconds=float(line[len(x):line.index(' sec.')]))
                )
            elif line.startswith('Total crossover time = '):
                x = 'Total crossover time = '
                lengths['crossover'][stress_year] = (
                    pd.Timedelta(seconds=float(line[len(x):line.index(' sec.')]))
                )
            elif line.startswith('--- Job ') and (' Stop ' in line):
                process = line[len('--- Job '):line.index(' Stop ')]
                x = f'--- Job {process} Stop '
                y = ' elapsed '
                label = process if process != 'd_solveoneyear.gms' else stress_year
                lengths['total'][label] = pd.Timedelta(line[line.index(y)+len(y):])
                times['stop'][label] = pd.Timestamp(line[len(x):line.index(y)])
                times['start'][label] = (
                    times['stop'][label] - lengths['total'][label])
    ## Combine
    dftime = pd.concat([pd.DataFrame(times), pd.DataFrame(lengths)], axis=1)
    dftime['remainder'] = (
        dftime['total']
        - pd.to_timedelta(dftime[['gams','barrier','crossover']].sum(axis=1))
    )
    return dftime


def write_last_solve_time(path=''):
    """Get last solve time, disaggregated by GAMS/barrier/crossover/remainder.
    Disaggregation only works when using CPLEX as the solver."""
    dftime = get_solve_times(path)
    lasttime = dftime.iloc[-1]
    if lasttime.name.endswith('.gms'):
        scriptname = lasttime.name
        year = 0
    else:
        scriptname = 'd_solveoneyear.gms'
        year = int(lasttime.name.split('i')[0])
    towrite = {
        'gams': scriptname,
        'barrier': 'solver/barrier',
        'crossover': 'solver/crossover',
        'remainder': 'solver/remainder',
    }
    with open(os.path.join(path,'meta.csv'), 'a') as METAFILE:
        if (scriptname == 'd_solveoneyear.gms') and all([i in lasttime for i in towrite]):
            for i, process in enumerate(towrite):
                METAFILE.writelines(
                    '{},{},{},{},{}\n'.format(
                        year,
                        towrite.get(process,process),
                        (lasttime.start
                         + pd.Timedelta(lasttime[list(towrite.keys())[:i]].sum())
                        ).isoformat(),
                        (lasttime.start
                         + pd.Timedelta(lasttime[list(towrite.keys())[:i+1]].sum())
                        ).isoformat(),
                        lasttime[process].total_seconds(),
                    )
                )
        else:
            METAFILE.writelines(
                '{},{},{},{},{}\n'.format(
                    year,
                    scriptname,
                    lasttime.start.isoformat(),
                    lasttime.stop.isoformat(),
                    lasttime.total.total_seconds(),
                )
            )
    return lasttime


#%% Procedure
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='ticker')
    parser.add_argument('-p', '--path', default='', type=str, help='case directory')
    parser.add_argument('-y', '--year', default='0', type=str, help='process year')
    args = parser.parse_args()

    try:
        write_last_solve_time(args.path)
    except Exception as _err:
        print('meta.csv not found or not writeable:')
        print(_err)
        pass
