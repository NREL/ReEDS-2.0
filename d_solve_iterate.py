#%% Imports
import os
import site
import argparse
import pandas as pd
import subprocess
from glob import glob
from input_processing.ticker import toc, makelog
from ReEDS_Augur.functions import get_switches

#%% Functions
def met_threshold(casepath, t, iteration=0):
    """
    Determine whether the last iteration failed the threshold
    """
    sw = get_switches(casepath)

    ### Get the latest NEUE data
    neue = pd.read_csv(
        os.path.join(casepath,'outputs',f'neue_{t}i{iteration}.csv'),
        index_col=['level','metric','region'],
    ).squeeze(1)

    ### Get the threshold(s) and see if any of them failed
    failed = 0
    ## Example: GSw_PRM_StressThreshold = 'country_sum_5/transgrp_sum_10'
    for threshold in sw.GSw_PRM_StressThreshold.split('/'):
        ## Example: threshold = 'country_sum_10'
        (hierarchy_level, period_agg_method, ppm) = threshold.split('_')
        this_test = neue[hierarchy_level][period_agg_method]
        if (this_test > float(ppm)).any():
            print(f"GSw_PRM_StressThreshold={threshold} failed for:")
            print(this_test.loc[this_test > float(ppm)])
            failed = 1

    if failed:
        print(f"At least one of GSw_PRM_StressThreshold={sw.GSw_PRM_StressThreshold} failed")
        return False
    else:
        print(f"All of GSw_PRM_StressThreshold={sw.GSw_PRM_StressThreshold} passed")
        return True


#%% Main function
def run_reeds(casepath, t, onlygams=False, iteration=0):
    """
    """
    # #%% Arguments for testing
    # casepath = os.path.expanduser('~/github/ReEDS-2.0/runs/v20230512_prasM0_ERCOT')
    # t = 2020
    # onlygams = 0
    # iteration = 0
    # os.chdir(casepath)

    #%% Inferred inputs
    reeds_path = os.path.dirname(os.path.dirname(casepath))
    site.addsitedir(reeds_path)
    import runbatch

    #%% Get the run settings
    sw = get_switches(casepath)
    years = pd.read_csv(
        os.path.join(casepath,'inputs_case','modeledyears.csv')
    ).columns.astype(int).values
    tprev = {**{years[0]:years[0]}, **dict(zip(years[1:], years))}
    tnext = {**dict(zip(years, years[1:])), **{years[-1]:years[-1]}}

    #%%### Run GAMS LP
    if not onlyaugur:
        #%% Get the command to run GAMS for this solve year
        batch_case = os.path.basename(casepath)
        ### Get the stress_year
        ## If using user-defined stress periods, read the current year
        if 'user' in sw.GSw_PRM_StressModel:
            stress_year = f"{t}i0"
        ## If we're on iteration 0, use stress periods from the previous year
        elif not iteration:
            stress_year = f"{tprev[t]}i{iteration}"
        ## Otherwise use stress periods from this year from the previous iteration
        else:
            stress_year = f"{t}i{iteration-1}"
        ### Get the restartfile (last iteration from previous year)
        if t == min(years):
            restartfile = batch_case
        else:
            restartfile = sorted(
                glob(os.path.join(casepath,'g00files',f"{batch_case}_{tprev[t]}i*"))
            )[-1]

        cmd_gams = runbatch.solvestring_sequential(
            batch_case=batch_case,
            caseSwitches=sw,
            cur_year=t,
            next_year=tnext[t],
            prev_year=tprev[t],
            stress_year=stress_year,
            restartfile=restartfile,
            hpc=int(sw['hpc']),
            iteration=iteration,
        )
        print(cmd_gams)

        ### Run GAMS LP
        subprocess.run(cmd_gams, shell=True)

        #%% Run ticker
        try:
            cmd_ticker = (
                f"python {os.path.join(casepath,'input_processing','ticker.py')}"
                f" --year={t}\n"
            )
            subprocess.run(cmd_ticker, shell=True)
        except Exception as err:
            print(err)

        #%% Check to see if the restart file exists
        savefile = f"{batch_case}_{t}i{iteration}"
        if not os.path.isfile(os.path.join("g00files", savefile+".g00")):
            raise Exception(f"Missing {savefile}.g00")


    #%%### Run Augur
    if (not onlygams) and (tnext[t] > int(sw.GSw_SkipAugurYear)):
        cmd_augur = f"python Augur.py {tnext[t]} {t} {casepath} --iteration={iteration}"
        result = subprocess.run(cmd_augur, shell=True)
        if result.returncode:
            raise Exception(f'Augur.py failed with return code {result.returncode}')

        # ## Check to make sure Augur ran successfully; quit otherwise
        # cmd_errorcheck = runbatch.writeerrorcheck(
        #     os.path.join("ReEDS_Augur", "augur_data", f"ReEDS_Augur_{t}.gdx")
        # )


#%% Driver function
def main(casepath, t):
    """
    """
    ### Get the run settings
    sw = get_switches(casepath)
    for iteration in range(int(sw.GSw_PRM_StressIterateMax)+1):
        #%% Run ReEDS and Augur
        run_reeds(casepath, t, iteration=iteration)

        #%% Stop here if we're before GSw_StartMarkets...
        if (t < int(sw['GSw_StartMarkets'])):
            print(f'{t} < GSw_StartMarkets ({sw.GSw_StartMarkets}) so skipping iteration')
            break
        ### or if not iterating...
        elif (
            (not int(sw['GSw_PRM_StressIterateMax']))
            or ('user' in sw.GSw_PRM_StressModel)
            or int(sw.GSw_PRM_CapCredit)
        ):
            print('Not iterating, so moving to next solve year')
            break
        ### or if the threshold was met
        elif met_threshold(casepath, t, iteration):
            print('NEUE threshold was met, so moving to next solve year')
            break
        ### Otherwise continue iterating
        else:
            print(f'NEUE threshold was not met, so performing iteration {iteration+1}')

    ### Delete old restart files if desired
    years = pd.read_csv(
        os.path.join(casepath,'inputs_case','modeledyears.csv')
    ).columns.astype(int).values
    tprev = {**{years[0]:years[0]}, **dict(zip(years[1:], years))}

    if not int(sw['keep_g00_files']) and (min(years) < t):
        g00files = glob(os.path.join(casepath, 'g00files', f'*{tprev[t]}i*.g00'))
        for i in g00files:
            os.remove(i)


#%% Procedure
if __name__ == '__main__':
    #%% Argument inputs
    import argparse
    parser = argparse.ArgumentParser(description='Sequential ReEDS')
    parser.add_argument('casepath', type=str,
                        help='path to ReEDS run folder')
    parser.add_argument('t', type=int,
                        help='year to run')
    parser.add_argument('--iteration', '-i', type=int, default=0,
                        help='iteration counter for this run')
    parser.add_argument('--onlygams', '-g', action='store_true',
                        help='indicate whether to only run GAMS (skip Augur)')
    parser.add_argument('--onlyaugur', '-a', action='store_true',
                        help='indicate whether to only run Augur (skip GAMS)')

    args = parser.parse_args()
    casepath = args.casepath
    t = args.t
    iteration = args.iteration
    onlygams = args.onlygams
    onlyaugur = args.onlyaugur

    #%% Switch to run folder
    os.chdir(casepath)

    #%% Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(casepath,'gamslog.txt'))

    #%% Run it
    main(casepath=casepath, t=t)
