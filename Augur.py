# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:30:25 2020

@author: afrazier
"""

#%% Direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')

#%% Imports
import argparse
import gdxpds
import logging
import os
import subprocess
import traceback
import datetime

from ReEDS_Augur.A_prep_data import prep_data
from ReEDS_Augur.C1_existing_curtailment import existing_curtailment
from ReEDS_Augur.C2_marginal_curtailment import marginal_curtailment
from ReEDS_Augur.D_condor import get_marginal_storage_value
from ReEDS_Augur.E_capacity_credit import reeds_cc
from ReEDS_Augur.utility.functions import delete_csvs, toc, printscreen
from ReEDS_Augur.utility.switchsettings import SwitchSettings

# Not used in the script but useful for debugging
from ReEDS_Augur.utility.generatordata import GEN_DATA, GEN_TECHS
from ReEDS_Augur.utility.hourlyprofiles import HOURLY_PROFILES, OSPREY_RESULTS
from ReEDS_Augur.utility.inputs import INPUTS


#%% Functions
def ReEDS_Augur(next_year, prev_year, scen):

    # #%% To debug, uncomment these lines and update 'scen' and the run path
    # next_year = 2025
    # prev_year = 2020
    # scen = os.path.basename(os.getcwd())
    # scen = 'v20220511_clusterM1_h8760_CL4_CC40_CF1_NSMR0_noH2_TIagg'
    # assert next_year > prev_year
    # os.chdir(os.path.expanduser('~/github2/ReEDS-2.0/runs/{}/'.format(scen)))

    # Definiing all switches and arguments.
    # Values for switches are grabbed directly from the call_{scenario} batch/shell script
    # Default valules for Augur are grabbed from ReEDS_Augur/value_defaults.csv
    SwitchSettings.set_switches(next_year, prev_year, scen)
    #%%

    # Prepping data for Osprey: This includes hourly profiles and generator data.
    printscreen('Preparing data for Osprey...')
    tic = datetime.datetime.now()
    reeds_inputs = prep_data()
    toc(tic=tic, year=prev_year, process='ReEDS_Augur/A_prep_data.py')

    # Running Osprey
    printscreen('Running Osprey...')
    tic = datetime.datetime.now()
    if (
        int(SwitchSettings.switches['gsw_augurcurtailment'])
        or (prev_year in SwitchSettings.switches['run_osprey_years'])
    ):
        subprocess.call(
            [
                'gams', os.path.join('ReEDS_Augur', 'B1_osprey'),
                'o='+os.path.join('lstfiles', 'osprey_{}.lst'.format(str(prev_year))),
                'logOption=0',
                'logfile=gamslog.txt',
                'appendLog=1',
                '--solver=cplex',
                '--case='+scen,
                '--prev_year={}'.format(prev_year),
                '--threads={}'.format(SwitchSettings.switches['threads']),
                '--osprey_num_days={}'.format(SwitchSettings.switches['osprey_num_years']*365),
            ] + (['license=gamslice.txt'] if int(SwitchSettings.switches['hpc']) else []),
            cwd=os.getcwd()
        )
    toc(tic=tic, year=prev_year, process='ReEDS_Augur/B1_osprey.gms')

    # Writing Osprey results out to csv files.
    tic = datetime.datetime.now()
    if (
        int(SwitchSettings.switches['gsw_augurcurtailment'])
        or (prev_year in SwitchSettings.switches['run_osprey_years'])
    ):
        subprocess.call([
            'gams', os.path.join('ReEDS_Augur', 'B2_gdx_dump'),
            '--prev_year='+str(prev_year)
        ] + (['license=gamslice.txt'] if int(SwitchSettings.switches['hpc']) else []),
        cwd=os.getcwd())
    toc(tic=tic, year=prev_year, process='ReEDS_Augur/B2_gdx_dump.gms')

    printscreen('calculating curtailment...')
    tic = datetime.datetime.now()
    curt_results, curt_reeds = existing_curtailment()
    toc(tic=tic, year=prev_year, process='ReEDS_Augur/C1_existing_curtailment.py')

    printscreen('calculating effects on marginal curtailment...')
    tic = datetime.datetime.now()
    mc_results, trans_region_curt = marginal_curtailment(curt_results)
    toc(tic=tic, year=prev_year, process='ReEDS_Augur/C2_marginal_curtailment.py')

    printscreen('running Condor...')
    tic = datetime.datetime.now()
    condor_results = get_marginal_storage_value(trans_region_curt)
    toc(tic=tic, year=prev_year, process='ReEDS_Augur/D_condor.py')

    printscreen('calculating capacity credit...')
    tic = datetime.datetime.now()
    cc_results = reeds_cc()
    toc(tic=tic, year=prev_year, process='ReEDS_Augur/E_capacity_credit.py')

    # Package results for ReEDS
    results = {**reeds_inputs,
               **mc_results,
               **cc_results,
               **condor_results,
               **curt_reeds}

    # Write gdx file explicitly to ensure that all entries
    # (even empty dataframes) are written as parameters, not sets
    with gdxpds.gdx.GdxFile() as gdx:
        for key in results:
            gdx.append(
                gdxpds.gdx.GdxSymbol(
                    key, gdxpds.gdx.GamsDataType.Parameter,
                    dims=results[key].columns[:-1].tolist(),
                )
            )
            gdx[-1].dataframe = results[key]
        gdx.write(
            os.path.join(
                'ReEDS_Augur', 'augur_data',
                'ReEDS_Augur_{}.gdx'.format(str(prev_year)))
        )

    if SwitchSettings.switches['plots'] and (prev_year in SwitchSettings.switches['plot_years']):
        printscreen('plotting intermediate Augur results...')
        tic = datetime.datetime.now()
        try:
            import ReEDS_Augur.F_plots
        except Exception as err:
            print('F_plots.py failed with the following exception:')
            print(err)
            pass
        toc(tic=tic, year=prev_year, process='ReEDS_Augur/F_plots.py')

    # Remove intermediate csv files to save drive space
    if SwitchSettings.switches['remove_csv']:
        delete_csvs(SwitchSettings.switches['keepfiles'])


#%% Procedure
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="""Running ReEDS Augur""")

    parser.add_argument("next_year", help="Next ReEDS solve year", type=int)
    parser.add_argument("prev_year", help="Previous ReEDS solve year", type=int)
    parser.add_argument("scen", help="ReEDS scenario")

    args = parser.parse_args()

    next_year = args.next_year
    prev_year = args.prev_year
    scen = args.scen

    # IF an error occurs, write it to a .txt file in the lstfiles folder
    path_errorfile = 'lstfiles'
    errorfile = os.path.join(
        'lstfiles', 'Augur_errors_{}.txt'.format(prev_year))
    logging.basicConfig(filename = errorfile, level = logging.ERROR)
    logger = logging.getLogger(__name__)

    try:
        ReEDS_Augur(next_year, prev_year, scen)
    except:
        logger.error('{}'.format(str(prev_year)))
        logger.error(traceback.format_exc())
    logging.shutdown()
    if os.stat(errorfile).st_size == 0:
        os.remove(errorfile)
