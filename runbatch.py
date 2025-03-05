#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import os
import queue
import threading
import time
import shutil
import csv
import numpy as np
import pandas as pd
import subprocess
import re
from datetime import datetime
import argparse
from builtins import input
from glob import glob
import reeds


# Assert core programs are accessible
CORE_PROGRAMS = ["gams"]
if not all(shutil.which(program) for program in CORE_PROGRAMS):
    msg = (
        "Programs needed to run reeds not accessible on the environment. "
        f"Check that all the {CORE_PROGRAMS=} are accessible on the PATH."
    )
    raise ImportError(msg)

#%% Constants
LINUXORMAC = True if os.name == 'posix' else False
YAMPASERVERS = ['constellation01','cepheus','corvus','dorado','delphinus']

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def writeerrorcheck(checkfile, errorcode=17):
    """
    Inputs
    ------
    checkfile: Filename to check. If it does not exist, stop the run.
    errorcode: Value to return if check fails. Should be >0.
    """
    if LINUXORMAC:
        return f'if [ ! -f {checkfile} ]; then echo "missing {checkfile}"; exit {errorcode}; fi\n'
    else:
        return f'\nif not exist {checkfile} (\n echo file {checkfile} missing \n goto:eof \n) \n \n'

def writescripterrorcheck(script, errorcode=18):
    """
    """
    if LINUXORMAC:
        return f'if [ $? != 0 ]; then echo "{script} returned $?" >> gamslog.txt; exit {errorcode}; fi\n'
    else:
        return f'if not %errorlevel% == 0 (echo {script} returned %errorlevel%\ngoto:eof\n)\n'


def write_delete_file(checkfile, deletefile, PATH):
    if LINUXORMAC:
        PATH.writelines(f"if [ -f {checkfile} ]; then rm {deletefile}; fi\n")
    else:
        PATH.writelines("if exist " + checkfile + " (del " + deletefile + ')\n' )


def comment(text, PATH):
    commentchar = '#' if LINUXORMAC else '::'
    PATH.writelines(f'{commentchar} {text}\n')


def big_comment(text, PATH):
    commentchar = '#' if LINUXORMAC else '::'
    PATH.writelines(f'\n{commentchar}\n')
    comment(text, PATH)
    PATH.writelines(f'{commentchar}\n')


def get_ivt_numclass(reeds_path, casedir, caseSwitches):
    """
    Extend ivt if necessary and calculate numclass
    """
    ivt = pd.read_csv(
        os.path.join(
            reeds_path, 'inputs', 'userinput', 'ivt_{}.csv'.format(caseSwitches['ivt_suffix'])),
        index_col=0)
    ivt_step = pd.read_csv(os.path.join(reeds_path, 'inputs', 'userinput', 'ivt_step.csv'),
                           index_col=0).squeeze(1)
    lastdatayear = max([int(c) for c in ivt.columns])
    addyears = list(range(lastdatayear + 1, int(caseSwitches['endyear']) + 1))
    num_added_years = len(addyears)
    ### Add v for the extra years
    ivt_add = {}
    for i in ivt.index:
        vlast = ivt.loc[i,str(lastdatayear)]
        if ivt_step[i] == 0:
            ### Use the same v forever
            ivt_add[i] = [vlast] * num_added_years
        else:
            ### Use the same spacing forever
            forever = [[vlast + 1 + x] * ivt_step[i] for x in range(1000)]
            forever = [item for sublist in forever for item in sublist]
            ivt_add[i] = forever[:num_added_years]
    ivt_add = pd.DataFrame(ivt_add, index=addyears).T
    ### Concat and resave
    ivtout = pd.concat([ivt, ivt_add], axis=1)
    ivtout.to_csv(os.path.join(casedir, 'inputs_case', 'ivt.csv'))
    ### Get numclass, which is used in b_inputs.gms
    numclass = ivtout.max().max()

    return numclass


def get_rev_paths(revswitches, caseSwitches):
    # Expand on reV path based on where this run is happening
    # when running on the HPC this links to the shared-projects folder
    hpc = True if (int(os.environ.get('REEDS_USE_SLURM',0))) else False
    if os.environ.get('NREL_CLUSTER') == 'kestrel':
        hpc_path = '/kfs2/shared-projects/reeds/Supply_Curve_Data'
    else:
        hpc_path = '/shared-projects/reeds/Supply_Curve_Data'

    if hpc:
        rev_prefix = hpc_path
    else:
        hostname = os.environ.get('HOSTNAME')
        if (hostname) and (hostname.split('.')[0] in YAMPASERVERS):
            drive = '/data/shared/shared_data'
        elif LINUXORMAC:
            drive = '/Volumes'
        else:
            drive = '//nrelnas01'
        rev_prefix = os.path.join(drive,'ReEDS','Supply_Curve_Data')
    revswitches['hpc_sc_path'] = revswitches['sc_path'].apply(lambda row: os.path.join(hpc_path,row))
    revswitches['sc_path'] = revswitches['sc_path'].apply(lambda row: os.path.join(rev_prefix,row))
    revswitches['rev_path'] = revswitches.apply(lambda row: os.path.join(row.sc_path, "reV", row.rev_case), axis=1)

    # link to the pre-processed reV supply curves from hourlize
    def get_rev_sc_file_name(caseSwitches, rev_row, use_hpc=False):
        if pd.isnull(rev_row.original_sc_file):
            return ""
        else:
            if caseSwitches['GSw_RegionResolution'] == "county":
                sc_folder_suffix = "_county"
            else:
                sc_folder_suffix = "_ba"

            # link to HPC or other sc_path
            if use_hpc:
                sc_path = rev_row.hpc_sc_path
            else:
                sc_path = rev_row.sc_path

            # supply curve name should be in format of {tech}_rev_supply_curves_raw.csv
            # in the hourlize results folder (must match format in 'save_sc_outputs' function of hourlize/resource.py)
            sc_file = os.path.join(sc_path,
                            rev_row.tech + "_" + rev_row.access_case + sc_folder_suffix,
                            "results",
                            rev_row.tech + "_supply_curve_raw.csv"
                            )
            return sc_file
    revswitches['sc_file'] = revswitches.apply(lambda row: get_rev_sc_file_name(caseSwitches, row), axis=1)
    revswitches['hpc_sc_file'] = revswitches.apply(lambda row: get_rev_sc_file_name(caseSwitches, row, use_hpc=True), axis=1)

    return revswitches

def check_compatibility(sw):
    ### Hourly resolution
    if (
        (int(sw['endyear']) > 2050)
        or (int(sw['startyear']) < 2010)
        or int(sw['GSw_ClimateHydro'])
        or int(sw['GSw_ClimateDemand'])
        or int(sw['GSw_ClimateWater'])
        or int(sw['GSw_EFS_Flex'])
        or (int(sw['GSw_Canada']) == 2)
        or int(sw['GSw_DUPV'])
    ):
        raise NotImplementedError(
            'At least one of GSw_Canada, GSw_ClimateHydro, GSw_ClimateDemand, GSw_ClimateWater, '
            'endyear, startyear, GSw_EFS_Flex, or GSw_DUPV '
            'are using a currently-unsupported setting.')
    
    if (sw['GSw_HourlyType'] in ['year']) and int(sw['GSw_InterDayLinkage']):
        raise ValueError(
            "GSw_HourlyType cannot be 'year' when GSw_InterDayLinkage is enabled. "
            f"Current values: GSw_HourlyType={sw['GSw_HourlyType']}, GSw_InterDayLinkage={sw['GSw_InterDayLinkage']}"
        )

    if 24 % (int(sw['GSw_HourlyWindowOverlap']) * int(sw['GSw_HourlyChunkLengthRep'])):
        raise ValueError(
            ('24 must be divisible by GSw_HourlyWindowOverlap * GSw_HourlyChunkLengthRep:'
            '\nGSw_HourlyWindowOverlap = {}\nGSw_HourlyChunkLengthRep = {}'.format(
                sw['GSw_HourlyWindowOverlap'], sw['GSw_HourlyChunkLengthRep'])))

    if int(sw['GSw_HourlyWindow']) <= int(sw['GSw_HourlyWindowOverlap']):
        raise ValueError(
            ('GSw_HourlyWindow must be greater than GSw_HourlyWindowOverlap:'
            '\nGSw_HourlyWindow = {}\nGSw_HourlyWindowOverlap = {}'.format(
                sw['GSw_HourlyWindow'], sw['GSw_HourlyWindowOverlap'])))

    if ((sw['GSw_HourlyClusterAlgorithm'] not in ['hierarchical','optimized'])
        and ('user' not in sw['GSw_HourlyClusterAlgorithm'])
    ):
        raise ValueError(
            "GSw_HourlyClusterAlgorithm must be set to 'hierarchical' or 'optimized', or must "
            "contain the substring 'user' and match a scenario in "
            "inputs/variability/period_szn_user.csv"
        )

    if ((sw['GSw_PRM_StressModel'].lower() not in ['pras'])
        and ('user' not in sw['GSw_PRM_StressModel'])):
        raise ValueError(
            "GSw_PRM_StressModel must be set to 'pras' or must "
            "contain the substring 'user' and match a scenario at "
            "inputs/variability/stressperiods_{GSw_PRM_StressModel}.csv"
        )

    if (int(sw['GSw_H2_PTC']) == 1) and (int(sw['GSw_H2']) != 2):
        raise ValueError(
            'When running with the H2 PTC enabled, GSw_H2 should be set to 2.\n'
            f"GSw_H2_PTC={sw['GSw_H2_PTC']}, GSw_H2={sw['GSw_H2']}"
        )

    if ('usa' not in sw['GSw_Region'].lower()) and (int(sw['GSw_GasCurve']) != 2):
        raise ValueError(
            'Should use GSw_GasCurve=2 (fixed prices) when running sub-nationally\n'
            f"GSw_Region={sw['GSw_Region']}, GSw_GasCurve={sw['GSw_GasCurve']}"
        )

    ### Aggregation
    if (sw['GSw_RegionResolution'] != 'aggreg') and (
        (int(sw['GSw_NumCSPclasses']) != 12)
        or (int(sw['GSw_NumDUPVclasses']) != 7)
    ):
        raise NotImplementedError(
            'Aggregated CSP/DUPV classes only work with aggregated regions. '
            'At least one of GSw_NumCSPclasses and GSw_NumDUPVclasses are incompatible with '
            'GSw_RegionResolution != aggreg')

    ### Parsed string switches
    ## Automatic inputs
    reeds_path = os.path.dirname(__file__)
    hierarchy = pd.read_csv(os.path.join(reeds_path,'inputs','hierarchy.csv'))

    for threshold in sw['GSw_PRM_StressThreshold'].split('/'):
        ## Example: threshold = 'transgrp_10_EUE_sum'
        allowed_levels = ['country','interconnect','nercr','transreg','transgrp','st','r']
        (hierarchy_level, ppm, stress_metric, period_agg_method) = threshold.split('_')
        if hierarchy_level not in allowed_levels:
            raise ValueError(
                f"GSw_PRM_StressThreshold: level={hierarchy_level} but must be in:\n"
                + '\n'.join(allowed_levels)
            )
        if period_agg_method.lower() not in ['sum','max']:
            raise ValueError("Fix period agg method in GSw_PRM_StressThreshold")
        if not (float(ppm) >= 0):
            raise ValueError(
                "ppm in GSw_PRM_StressThreshold must be a positive number "
                f"but '{ppm}' was provided"
            )
        if stress_metric.upper() not in ['EUE','NEUE']:
            raise ValueError(
                "stress metric in GSw_PRM_StressThreshold must be 'EUE' or 'NEUE' "
                f"but '{stress_metric}' was provided"
            )

    if sw['GSw_PRM_StressStorageCutoff'].lower() not in ['off','0','false']:
        metric, value = sw['GSw_PRM_StressStorageCutoff'].split('_')
        if metric.lower()[:3] not in ['eue', 'cap', 'abs']:
            raise ValueError(
                "The first argument of GSw_PRM_StressStorageCutoff must be in "
                f"['eue', 'cap', 'abs'] but {metric} was provided"
            )
        try:
            float(value)
        except ValueError:
            raise ValueError(
                "The second argument of GSw_PRM_StressStorageCutoff must be a number "
                f"but {value} was provided"
            )
        if (metric.lower()[:3] == 'abs') and (int(value) != 1):
            raise NotImplementedError(
                "GSw_PRM_StressStorageCutoff: only abs_1 is implemented for abs but "
                f"{metric}_{value} was provided"
            )

    for keyval in sw['GSw_PRM_NetImportLimitScen'].split('/'):
        err = (
            "GSw_PRM_NetImportLimitScen accepts inputs in the format "
            "{year1}_{'hist' or float}/{year2}_{float}/{year3}_{float} "
            "or a single value given as {year1}_{'hist' or float}. Examples are "
            "2024_hist/2035_40, 2025_20/2032_40, 2024_hist, 2025_20/2032_40/2050_60. "
            f"You entered {sw['GSw_PRM_NetImportLimitScen']}."
        )
        year, limit = keyval.split('_')
        try:
            int(year)
        except ValueError:
            raise ValueError(err)
        if limit not in ['hist', 'histmax']:
            try:
                float(limit)
            except ValueError:
                raise ValueError(err)

    for bir in sw['GSw_PVB_BIR'].split('_'):
        if not (float(bir) >= 0):
            raise ValueError("Fix GSw_PVB_BIR")

    for ilr in sw['GSw_PVB_ILR'].split('_'):
        if not (float(ilr) >= 0):
            raise ValueError("Fix GSw_PVB_ILR")

    for pvbtype in sw['GSw_PVB_Types'].split('_'):
        if not (1 <= int(pvbtype) <= 3):
            raise ValueError("Fix GSw_PVB_Types")

    scalars = reeds.io.get_scalars()
    ilr_upv = scalars['ilr_utility'] * 100

    if (int(sw['GSw_PVB'])) and (sw['GSw_SitingUPV'] != 'reference'):
        if (all(ilr != ilr_upv for ilr in sw['GSw_PVB_ILR'].split('_'))):
            raise ValueError(f'PVB with ILR!={scalars["ilr_utility"]} only works with GSw_SitingUPV == "reference".'
                             '\nSet GSw_SitingUPV to "reference".')

    if (int(sw['GSw_PVB'])) and (sw['GSw_RegionResolution'] == 'county'):
        if (all(ilr != ilr_upv for ilr in sw['GSw_PVB_ILR'].split('_'))):
            raise ValueError(f'PVB with ILR!={scalars["ilr_utility"]} does not work at county resolution.'
                             f'\nRemove any ILR!={scalars["ilr_utility"]} from GSw_PVB_ILR.')

    for year in sw['resource_adequacy_years'].split('_'):
        if not ((2007 <= int(year) <= 2013) or (2016 <= int(year) <= 2023)):
            raise ValueError("Fix resource_adequacy_years")

    for year in sw['GSw_HourlyWeatherYears'].split('_'):
        if not ((2007 <= int(year) <= 2013) or (2016 <= int(year) <= 2023)):
            raise ValueError("Fix GSw_HourlyWeatherYears")

    if '/' in sw['GSw_Region']:
        level, regions = sw['GSw_Region'].split('/')
        if level not in hierarchy:
            raise ValueError("Fix level in GSw_Region")
        for region in regions.split('.'):
            if region.lower() not in hierarchy[level].str.lower().values:
                err = f'GSw_Region: {region} needs to be in {hierarchy[level].unique()}'
                raise Exception(err)
    else:
        modeled_regions = pd.read_csv(
            os.path.join(reeds_path,'inputs','userinput','modeled_regions.csv')
        )
        if sw['GSw_Region'] not in modeled_regions:
            raise ValueError("No column in modeled_regions.csv matching GSw_Region")

    ### Compatible switch combinations
    if sw['GSw_EFS1_AllYearLoad'] == 'historic' :
        if ('demand_' + sw['demandscen'] +'.csv') not in os.listdir(os.path.join(reeds_path, 'inputs','load')) :
            raise ValueError("The demand file specified by the demandscen switch is not in the inputs/load folder")

    if sw['GSw_PRM_scenario'] == 'none':
        if int(sw['GSw_PRM_CapCredit']) !=1 :
            raise ValueError("To disable both the capacity credit and stress period formulations GSw_PRM_CapCredit must be set to 1")

    ### Dependent model availability
    if (
        ((not int(sw['GSw_PRM_CapCredit'])) or (int(sw['pras']) == 2))
        and (not os.path.isfile(os.path.join(reeds_path, 'Manifest.toml')))
    ):
        err = (
            "Manifest.toml does not exist. "
            "Please set up julia by following the instructions at "
            "https://pages.github.nrel.gov/ReEDS/ReEDS-2.0/internal/additional_setup.html#reeds2pras-julia-and-stress-periods-setup"
        )
        raise Exception(err)

    ### Land use and reeds_to_rev
    if (int(sw['land_use_analysis'])) and (not int(sw['reeds_to_rev'])):
        raise ValueError(
            "'reeds_to_rev' must be enable for land_use analysis to run."
        )


def solvestring_sequential(
        batch_case, caseSwitches,
        cur_year, next_year, prev_year, restartfile,
        toLogGamsString=' logOption=4 logFile=gamslog.txt appendLog=1 ',
        hpc=0, iteration=0, stress_year=None,
    ):
    """
    Typical inputs:
    * restartfile: batch_case if first solve year else {batch_case}_{prev_year}
    * caseSwitches: loaded from {batch_case}/inputs_case/switches.csv
    """
    savefile = f"{batch_case}_{cur_year}i{iteration}"
    _stress_year = f"{cur_year}i0" if stress_year is None else stress_year
    out = (
        "gams d_solveoneyear.gms"
        + (" license=gamslice.txt" if hpc else '')
        + " o=" + os.path.join("lstfiles", f"{savefile}.lst")
        + " r=" + os.path.join("g00files", restartfile)
        + " gdxcompress=1"
        + " xs=" + os.path.join("g00files", savefile)
        + toLogGamsString
        + f" --case={batch_case}"
        + f" --cur_year={cur_year}"
        + f" --next_year={next_year}"
        + f" --prev_year={prev_year}"
        + f" --stress_year={_stress_year}"
        + ''.join([f" --{s}={caseSwitches[s]}" for s in [
            'GSw_SkipAugurYear',
            'GSw_HourlyType', 'GSw_HourlyWrapLevel', 'GSw_ClimateWater',
            'GSw_Canada', 'GSw_ClimateHydro',
            'GSw_HourlyChunkLengthRep', 'GSw_HourlyChunkLengthStress',
            'GSw_StateCO2ImportLevel',
            'GSw_PVB_Dur',
            'GSw_ValStr', 'GSw_gopt', 'solver',
            'debug','startyear','diagnose','diagnose_year'
        ]])
        + '\n'
    )

    return out


def setup_sequential_year(
        cur_year, prev_year, next_year,
        caseSwitches, hpc,
        solveyears, casedir, batch_case, toLogGamsString, OPATH, logger,
        restart_switches,
    ):
    ## Get save file (for this year) and restart file (from previous year)
    savefile = f"{batch_case}_{cur_year}i0"
    restartfile = batch_case if cur_year == min(solveyears) else f"{batch_case}_{prev_year}i0"

    ## Run the ReEDS LP
    if (
        (not restart_switches['restart'])
        or (cur_year > min(solveyears))
        or (restart_switches['restart'] and not restart_switches['restart_Augur'])
    ):
        ## solve one year
        OPATH.writelines(
            solvestring_sequential(
                batch_case, caseSwitches,
                cur_year, next_year, prev_year, restartfile,
                toLogGamsString, hpc,
            ))
        OPATH.writelines(writescripterrorcheck(f"d_solveoneyear.gms_{cur_year}"))
        OPATH.writelines(f'python {logger} --year={cur_year}\n')

        if int(caseSwitches['GSw_ValStr']):
            OPATH.writelines("python valuestreams.py" + '\n')

        ## check to see if the restart file exists
        OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))
    ## Run Augur if it not the final solve year and if not skipping Augur
    if ((
        (cur_year < max(solveyears))
        and (next_year > int(caseSwitches['GSw_SkipAugurYear']))
    ) or (cur_year == max(solveyears))):
        OPATH.writelines(
            f"\npython Augur.py {next_year} {cur_year} {casedir}\n")
        ## Check to make sure Augur ran successfully; quit otherwise
        OPATH.writelines(
            writeerrorcheck(os.path.join(
                "ReEDS_Augur", "augur_data", f"ReEDS_Augur_{cur_year}.gdx")))

    ## delete the previous restart file unless we're keeping them
    if (cur_year > min(solveyears)) and (not int(caseSwitches['keep_g00_files'])):
        write_delete_file(
            checkfile=os.path.join("g00files", savefile + ".g00"),
            deletefile=os.path.join("g00files", restartfile + '.g00'),
            PATH=OPATH,
        )


def setup_sequential(
        caseSwitches, reeds_path, hpc,
        solveyears, casedir, batch_case, toLogGamsString, OPATH, logger,
        restart_switches,
    ):
    ### loop over solve years
    for i in range(len(solveyears)):
        ## current year is the value in solveyears
        cur_year = solveyears[i]

        if cur_year < max(solveyears):
            ## next year becomes the next item in the solveyears vector
            next_year = solveyears[i+1]
        ## Get previous year if after first year
        if i:
            prev_year = solveyears[i-1]
        else:
            if restart_switches['restart']:
                prev_year = restart_switches['restart_year']
            else:
                prev_year = solveyears[i]

        ### make an indicator in the batch file for what year is being solved
        big_comment(f'Year: {cur_year}', OPATH)

        ### Write the tax credit phaseout call
        OPATH.writelines(f"python tc_phaseout.py {cur_year} {casedir}\n\n")

        ### Write the GAMS LP and Augur calls
        if (
            int(caseSwitches['GSw_PRM_StressIterateMax'])
            and (not int(caseSwitches['GSw_PRM_CapCredit']))
        ):
            OPATH.writelines(
                f"python d_solve_iterate.py {casedir} {cur_year}\n"
            )
            OPATH.writelines(writescripterrorcheck(f"d_solve_iterate.py_{cur_year}"))
        else:
            setup_sequential_year(
                cur_year, prev_year, next_year,
                caseSwitches, hpc,
                solveyears, casedir, batch_case, toLogGamsString, OPATH, logger,
                restart_switches,
            )

        ### Run input parameter error checks after the first solve year (since financial
        ### multipliers aren't created until the first solve year is run)
        if cur_year == min(solveyears):
            OPATH.writelines(
                f"\npython {os.path.join(casedir, 'input_processing', 'check_inputs.py')} "
                f"{casedir}\n"
            )
            OPATH.writelines(writescripterrorcheck('check_inputs.py')+'\n')

        ### Run Augur plots in background
        OPATH.writelines(
            f"python {os.path.join('ReEDS_Augur','diagnostic_plots.py')} "
            f"--reeds_path={reeds_path} --casedir={casedir} --t={cur_year} &\n")


def setup_intertemporal(
        caseSwitches, startiter, niter, ccworkers,
        solveyears, endyear, batch_case, toLogGamsString, yearset_augur, OPATH,
    ):
    ### beginning year is passed to augurbatch
    begyear = min(solveyears)
    ### first save file from d_solveprep is just the case name
    savefile = batch_case
    ### if this is the first iteration
    if startiter == 0:
        ## restart file becomes the previous calls save file
        restartfile=savefile
        ## if this is not the first iteration...
    if startiter > 0:
        ## restart file is now the case name plus the iteration number
        restartfile = batch_case+"_"+startiter

    ### per the instructions, iterations are
    ### the number of iterations after the first solve
    niter = niter+1

    ### for the number of iterations we have...
    for i in range(startiter,niter):
        ## make an indicator in the batch file for what iteration is being solved
        big_comment(f'Iteration: {i}', OPATH)
        ## call the intertemporal solve
        savefile = batch_case+"_"+str(i)

        if i==0:
            ## check to see if the restart file exists
            ## only need to do this with the zeroth iteration
            ## as the other checks will all be after the solves
            OPATH.writelines(writeerrorcheck(os.path.join("g00files",restartfile + ".g*")))

        OPATH.writelines(
            "gams d_solveallyears.gms o="+os.path.join("lstfiles",batch_case + "_" + str(i) + ".lst")
            +" r="+os.path.join("g00files",restartfile)
            + " gdxcompress=1 xs="+os.path.join("g00files",savefile) + toLogGamsString
            + " --niter=" + str(i) + " --case=" + batch_case  + ' \n')

        ## check to see if the save file exists
        OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))

        ## start threads for cc/curt
        ## no need to run cc curt scripts for final iteration
        if i < niter-1:
            ## batch out calls to augurbatch
            OPATH.writelines(
                "python augurbatch.py " + batch_case + " " + str(ccworkers) + " "
                + yearset_augur + " " + savefile + " " + str(begyear) + " "
                + str(endyear) + " " + caseSwitches['distpvscen'] + " "
                + str(caseSwitches['calc_csp_cc']) + " "
                + str(caseSwitches['GSw_DR']) + " "
                + str(caseSwitches['timetype']) + " "
                + str(caseSwitches['GSw_WaterMain']) + " " + str(i) + " "
                + str(caseSwitches['marg_vre_mw']) + " "
                + str(caseSwitches['marg_stor_mw']) + " "
                + str(caseSwitches['marg_dr_mw']) + " "
                + '\n')
            ## merge all the resulting gdx files
            ## the output file will be for the next iteration
            nextiter = i+1
            gdxmergedfile = os.path.join(
                "ReEDS_Augur","augur_data","ReEDS_Augur_merged_" + str(nextiter))
            OPATH.writelines(
                "gdxmerge "+os.path.join("ReEDS_Augur","augur_data","ReEDS_Augur*")
                + " output=" + gdxmergedfile  + ' \n')
            ## check to make sure previous calls were successful
            OPATH.writelines(writeerrorcheck(gdxmergedfile+".gdx"))

        ## restart file becomes the previous save file
        restartfile=savefile

    if caseSwitches['GSw_ValStr'] != '0':
        OPATH.writelines( "python valuestreams.py" + '\n')


def setup_window(
        caseSwitches, startiter, niter, ccworkers, reeds_path,
        batch_case, toLogGamsString, yearset_augur, OPATH,
    ):
    ### load the windows
    win_in = list(csv.reader(open(
        os.path.join(
            reeds_path,"inputs","userinput",
            "windows_{}.csv".format(caseSwitches['windows_suffix'])),
        'r'), delimiter=","))

    restartfile = batch_case

    ### for windows indicated in the csv file
    for win in win_in[1:]:

        ## beginning year is the first column (start)
        begyear = win[1]
        ## end year is the second column (end)
        endyear = win[2]
        ## for the number of iterations we have...
        for i in range(startiter,niter):
            big_comment(f'Window: {win}', OPATH)
            comment(f'Iteration: {i}', OPATH)

            ## call the window solve
            savefile = batch_case+"_"+str(i)
            ## check to see if the save file exists
            OPATH.writelines(writeerrorcheck(os.path.join("g00files",restartfile + ".g*")))
            ## solve via the window solve file
            OPATH.writelines(
                "gams d_solvewindow.gms o=" + os.path.join("lstfiles",batch_case + "_" + str(i) + ".lst")
                +" r=" + os.path.join("g00files",restartfile)
                + " gdxcompress=1 xs=g00files\\"+savefile + toLogGamsString + " --niter=" + str(i)
                + " --maxiter=" + str(niter-1) + " --case=" + batch_case + " --window=" + win[0] + ' \n')
            ## start threads for cc/curt
            OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))
            OPATH.writelines(
                "python augurbatch.py " + batch_case + " " + str(ccworkers) + " "
                + yearset_augur + " " + savefile + " " + str(begyear) + " "
                + str(endyear) + " " + caseSwitches['distpvscen'] + " "
                + str(caseSwitches['calc_csp_cc']) + " "
                + str(caseSwitches['GSw_DR']) + " "
                + str(caseSwitches['timetype']) + " "
                + str(caseSwitches['GSw_WaterMain']) + " " + str(i) + " "
                + str(caseSwitches['marg_vre_mw']) + " "
                + str(caseSwitches['marg_stor_mw']) + " "
                + str(caseSwitches['marg_dr_mw']) + " "
                + '\n')
            ## merge all the resulting r2_in gdx files
            ## the output file will be for the next iteration
            nextiter = i+1
            ## create names for then merge the curt and cc gdx files
            gdxmergedfile = os.path.join(
                "ReEDS_Augur","augur_data","ReEDS_Augur_merged_" + str(nextiter))
            OPATH.writelines(
                "gdxmerge " + os.path.join("ReEDS_Augur","augur_data","ReEDS_Augur*")
                + " output=" + gdxmergedfile  + ' \n')
            ## check to make sure previous calls were successful
            OPATH.writelines(writeerrorcheck(gdxmergedfile+".gdx"))
            restartfile=savefile
        if caseSwitches['GSw_ValStr'] != '0':
            OPATH.writelines( "python valuestreams.py" + '\n')


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

def setupEnvironment(
        BatchName=False, cases_suffix=False, single='', simult_runs=0,
        forcelocal=0, restart=False, skip_checks=False,
        debug=False, debugnode=False):
    # #%% Settings for testing
    # BatchName = 'v20230508_prasM0_Pacific'
    # cases_suffix = 'test'
    # WORKERS = 1
    # forcelocal = 0
    # restart = False

    #%% Automatic inputs
    reeds_path = os.path.dirname(__file__)

    #%% User inputs
    print(" ")
    print("------------- ")
    print(" ")
    print("WINDOWS USERS - This script will open multiple command prompts, the number of which")
    print("is based on the number of simultaneous runs you've chosen")
    print(" ")
    print("MAC/LINUX USERS - Your cases will run in the background. All console output")
    print("is written to the cases' appropriate gamslog.txt file in the cases' runs folders")
    print(" ")
    print("------------- ")
    print(" ")
    print(" ")

    if not BatchName:
        print("-- Specify the batch prefix --")
        print(" ")
        print("The batch prefix is attached to the beginning of all cases' outputs files")
        print("Note - it must start with a letter and not a number or symbol")
        print(" ")
        print("A value of 0 will assign the date and time as the batch name (e.g. v20190520_072310)")
        print(" ")

        BatchName = str(input('Batch Prefix: '))

    if BatchName == '0':
        BatchName = 'v' + time.strftime("%Y%m%d_%H%M%S")

    #check for period in batchname and replace with underscore
    BatchName = BatchName.replace('.', '_')

    if not cases_suffix:
        print("\n\nSpecify the suffix for the cases_suffix.csv file")
        print("A blank input will default to the cases.csv file\n")

        cases_suffix = str(input('Case Suffix: '))

    #%% Check whether to submit slurm jobs (if on HPC) or run locally
    hpc = True if (int(os.environ.get('REEDS_USE_SLURM',0))) else False
    hpc = False if forcelocal else hpc
    ### If on NREL HPC but NOT submitting slurm job, ask for confirmation
    if ('NREL_CLUSTER' in os.environ) and (not hpc):
        print(
            "It looks like you're running on the NREL HPC but the REEDS_USE_SLURM environment "
            "variable is not set to 1, meaning the model will run locally rather than being "
            "submitted as a slurm job. Are you sure you want to run locally?"
        )
        confirm_local = str(input('Run job locally? y/[n]: ') or 'n')
        if confirm_local not in ['y','Y','yes','Yes','YES']:
            quit()

    #%% Check whether the ReEDS conda environment is activated
    if (not skip_checks) and (
        ('reeds2' not in os.environ['CONDA_DEFAULT_ENV'].lower())
        or (not pd.__version__.startswith('2'))
    ):
        print(
            f"Your environment is {os.environ['CONDA_DEFAULT_ENV']} and your pandas "
            f"version is {pd.__version__}.\nThe default environment is 'reeds2', with\n"
            "pandas version 2.x, so the python parts of ReEDS are unlikely to work.\n"
            "To build the environment for the first time, run:\n"
            "    `conda env create -f environment.yml`\n"
            "To activate the created environment, run:\n"
            "    `conda activate reeds2` (or `activate reeds2` on Windows)\n"
            "Do you want to continue without activating the environment?"
        )
        confirm_env = str(input("Continue? y/[n]: ") or 'n')
        if confirm_env not in ['y','Y','yes','Yes','YES']:
            quit()

    #%% Load specified case file, infer other settings from cases.csv
    df_cases = pd.read_csv(
        os.path.join(reeds_path, 'cases.csv'), dtype=object, index_col=0)
    cases_filename = 'cases.csv'

    # If we have a case suffix, use cases_[suffix].csv for cases.
    if cases_suffix not in ['','default']:
        df_cases = df_cases[['Choices', 'Default Value']]
        cases_filename = 'cases_' + cases_suffix + '.csv'
        df_cases_suf = pd.read_csv(
            os.path.join(reeds_path, cases_filename), dtype=object, index_col=0)
        # Replace periods and spaces in case names with _
        df_cases_suf.columns = [
            c.replace(' ','_').replace('.','_') if c != 'Default Value' else c
            for c in df_cases_suf.columns]

        # Check to make sure user-specified cases file has up-to-date switches
        missing_switches = [s for s in df_cases_suf.index if s not in df_cases.index]
        if len(missing_switches):
            error = ("The following switches are in {} but have changed names or are no longer "
                      "supported by ReEDS:\n\n{} \n\nPlease update your cases file; "
                      "for the full list of available switches see cases.csv."
                      "Note that switch names are case-sensitive."
                    ).format(cases_filename, '\n'.join(missing_switches))
            raise ValueError(error)

        # First use 'Default Value' from cases_[suffix].csv to fill missing switches
        # Later, we will also use 'Default Value' from cases.csv to fill any remaining holes.
        if 'Default Value' in df_cases_suf.columns:
            case_i = df_cases_suf.columns.get_loc('Default Value') + 1
            casenames = df_cases_suf.columns[case_i:].tolist()
            for case in casenames:
                df_cases_suf[case] = df_cases_suf[case].fillna(df_cases_suf['Default Value'])
        df_cases_suf.drop(['Choices','Default Value'], axis='columns',inplace=True, errors='ignore')
        df_cases = df_cases.join(df_cases_suf, how='outer')

    # Initiate the empty lists which will be filled with info from cases
    caseList = []
    caseSwitches = [] #list of dicts, one dict for each case
    casenames = [c for c in df_cases.columns if c not in ['Description','Default Value','Choices']]
    # Get the list of switch choices
    choices = df_cases.Choices.copy()

    for case in casenames:
        #Fill any missing switches with the defaults in cases.csv
        df_cases[case] = df_cases[case].fillna(df_cases['Default Value'])
        # Ignore cases with ignore flag
        if int(df_cases.loc['ignore',case]) == 1:
            continue
        # Ignore cases that don't match the "single" case
        if len(single) and (case not in single.split(',')):
            continue
        # Check to make sure the switch setting is valid
        for i, val in df_cases[case].items():
            if skip_checks:
                continue
            ### Split choices by either '; ' or ','
            if choices[i] in ['N/A',None,np.nan]:
                pass
            elif choices[i].lower() in ['int','integer']:
                try:
                    int(val)
                except ValueError:
                    error = (
                        f'Invalid entry for "{i}" for case "{case}".\n'
                        f'Entered "{val}" but must be an integer.'
                    )
                    raise ValueError(error)
            elif choices[i].lower() in ['float','numeric','number','num']:
                try:
                    float(val)
                except ValueError:
                    error = (
                        f'Invalid entry for "{i}" for case "{case}".\n'
                        f'Entered "{val}" but must be a float (number).'
                    )
                    raise ValueError(error)
            else:
                i_choices = [
                    str(j).strip() for j in
                    np.ravel([i.split(',') for i in choices[i].split(';')]).tolist()
                ]
                matches = [re.match(choice, str(val)) for choice in i_choices]
                if not any(matches):
                    error = (
                        f'Invalid entry for "{i}" for case "{case}".\n'
                        f'Entered "{val}" but must match one of the following:\n> '
                        + '\n> '.join(i_choices)
                        + '\n'
                    )
                    raise ValueError(error)

        #Check GSw_Region switch and ask user to correct if commas are used instead of periods to list multiple regions
        if ',' in (df_cases[case].loc['GSw_Region']) :
            print("Please change the delimeter in the GSw_Region switch from ',' to '.'")
            quit()

        # Propagate debug setting
        if debug:
            df_cases.loc['debug',case] = str(debug)

        # Add switch settings to list of options passed to GAMS
        shcom = ' --case=' + BatchName + "_" + case
        for i,v in df_cases[case].items():
            #exclude certain switches that don't need to be passed to GAMS
            if i not in ['file_replacements','keep_run_terminal']:
                shcom = shcom + ' --' + i + '=' + v
        caseList.append(shcom)
        caseSwitches.append(df_cases[case].to_dict())

    # ignore cases with ignore flag
    casenames = [case for case in casenames if int(df_cases.loc['ignore',case]) != 1]
    df_cases.drop(
        df_cases.loc['ignore'].loc[df_cases.loc['ignore']=='1'].index, axis=1, inplace=True)
    # If the "single" argument is provided, only run that case
    if single:
        for s in single.split(','):
            if s not in df_cases:
                err = (
                    f'Specified single={single} but available cases are:\n'
                    + '\n> '.join([
                        c for c in df_cases.columns
                        if c not in ['Choices','Description','Default Value']
                    ])
                )
                raise KeyError(err)
        df_cases = df_cases[single.split(',')].copy()
        casenames = single.split(',')

    # Make sure the run folders don't already exist
    outpaths = [os.path.join(reeds_path,'runs',f'{BatchName}_{case}') for case in casenames]
    existing_outpaths = [i for i in outpaths if os.path.isdir(i)]
    if len(existing_outpaths) and not restart:
        print(
            f'The following {len(existing_outpaths)} output directories already exist:\n'
            + 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv\n'
            + '\n'.join([os.path.basename(i) for i in existing_outpaths])
            + '\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
        )
        overwrite = str(input('Do you want to overwrite them? y/[n]: ') or 'n')
        if overwrite in ['y','Y','yes','Yes','YES']:
            for outpath in existing_outpaths:
                shutil.rmtree(outpath)
        else:
            keep = [i for (i,c) in enumerate(outpaths) if c not in existing_outpaths]
            caseList = [caseList[i] for i in keep]
            casenames = [casenames[i] for i in keep]
            caseSwitches = [caseSwitches[i] for i in keep]
            print(
                f"\nThe following {(len(keep))} output directories don't exist:\n"
                + 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv\n'
                + '\n'.join([f'{BatchName}_{c}' for c in casenames])
                + '\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
            )
            skip = str(input('Do you want to run them and skip the rest? [y]/n: ') or 'y')
            if skip.lower() not in ['y','yes']:
                raise IsADirectoryError('\n'+'\n'.join(existing_outpaths))

    df_cases.drop(
        ['Choices','Description','Default Value'],
        axis='columns', inplace=True, errors='ignore')

    print("{} cases being run:".format(len(caseList)))
    for case in casenames:
        print(case)
    print(" ")

    reschoice = 0
    startiter = 0
    ccworkers = 5
    niter = 5
    #%% Set number of workers, with user input if necessary
    if len(caseList)==1:
        print("Only one case is to be run, therefore only one thread is needed")
        WORKERS = 1
    elif simult_runs < 0 or hpc:
        WORKERS = len(caseList)
    elif simult_runs > 0:
        WORKERS = simult_runs
    else:
        WORKERS = int(input('Number of simultaneous runs [integer]: '))

    print(WORKERS)
    print("")

    if 'int' in df_cases.loc['timetype'].tolist() or 'win' in df_cases.loc['timetype'].tolist():
        ccworkers = int(input('Number of simultaneous CC/Curt runs [integer]: '))
        print("")
        print("The number of iterations defines the number of combinations of")
        print(" solving the model and computing capacity credit and curtailment")
        print(" Note this does not include the initial solve")
        print("")
        niter = int(input('How many iterations between the model and CC/Curt scripts: '))
        # reschoice = int(input('Do you want to restart from a previous convergence attempt (0=no, 1=yes): '))

        if reschoice==1:
            startiter = int(input('Iteration to start from (recall it starts at zero): '))


    envVar = {
        'WORKERS': WORKERS,
        'ccworkers': ccworkers,
        'casenames': casenames,
        'BatchName': BatchName,
        'caseList': caseList,
        'caseSwitches': caseSwitches,
        'reeds_path' : reeds_path,
        'niter' : niter,
        'startiter' : startiter,
        'cases_filename': cases_filename,
        'hpc': hpc,
        'restart': restart,
        'debugnode': debugnode,
    }

    return envVar


def createmodelthreads(envVar):

    q = queue.Queue()
    num_worker_threads = envVar['WORKERS']

    def worker():
        while True:
            ThreadInit = q.get()
            if ThreadInit is None:
                break
            runModel(
                options=ThreadInit['scen'],
                caseSwitches=ThreadInit['caseSwitches'],
                niter=ThreadInit['niter'],
                reeds_path=ThreadInit['reeds_path'],
                ccworkers=ThreadInit['ccworkers'],
                startiter=ThreadInit['startiter'],
                BatchName=ThreadInit['BatchName'],
                case=ThreadInit['casename'],
                cases_filename=ThreadInit['cases_filename'],
                hpc=envVar['hpc'],
                restart=envVar['restart'],
                debugnode=envVar['debugnode'],
            )
            print(ThreadInit['batch_case'] + " has finished \n")
            q.task_done()


    threads = []

    for i in range(num_worker_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for i in range(len(envVar['caseList'])):
        q.put({
            'scen': envVar['caseList'][i],
            'caseSwitches': envVar['caseSwitches'][i],
            'batch_case':envVar['BatchName']+'_'+envVar['casenames'][i],
            'niter':envVar['niter'],
            'reeds_path':envVar['reeds_path'],
            'ccworkers':envVar['ccworkers'],
            'startiter':envVar['startiter'],
            'BatchName':envVar['BatchName'],
            'casename':envVar['casenames'][i],
            'cases_filename':envVar['cases_filename'],
            'restart':envVar['restart'],
            })

    # block until all tasks are done
    q.join()

    # stop workers
    for i in range(num_worker_threads):
        q.put(None)

    for t in threads:
        t.join()


def runModel(options, caseSwitches, niter, reeds_path, ccworkers, startiter,
             BatchName, case, cases_filename, hpc=False, restart=False, debugnode=False):
    ### For testing/debugging
    # caseSwitches = caseSwitches[0]
    # options = caseList[0]
    ### Inferred inputs
    batch_case = f'{BatchName}_{case}'
    startyear = int(caseSwitches['startyear'])
    endyear = int(caseSwitches['endyear'])

    casedir = os.path.join(reeds_path,'runs',batch_case)
    inputs_case = os.path.join(casedir,"inputs_case")

    # Indicate this run is a restart
    if restart:
        print("Restarting from previous run.")
    else:
        if os.path.exists(os.path.join(reeds_path,'runs',batch_case)):
            print('Caution, case ' + batch_case + ' already exists in runs \n')

        #%% Set up case-specific directory structure
        os.makedirs(os.path.join(reeds_path,'runs',batch_case), exist_ok=True)
        os.makedirs(os.path.join(reeds_path,'runs',batch_case,'g00files'), exist_ok=True)
        os.makedirs(os.path.join(reeds_path,'runs',batch_case,'lstfiles'), exist_ok=True)
        os.makedirs(os.path.join(reeds_path,'runs',batch_case,'outputs'), exist_ok=True)
        os.makedirs(os.path.join(reeds_path,'runs',batch_case,'outputs','tc_phaseout_data'), exist_ok=True)
        os.makedirs(os.path.join(reeds_path,'runs',batch_case,'outputs','model_diagnose'), exist_ok=True) if int(caseSwitches['diagnose'])!=0 else ''
        os.makedirs(inputs_case, exist_ok=True)

    #%% Stop now if any switches are incompatible
    check_compatibility(caseSwitches)

    #%% Write the GAMS switches
    gswitches = pd.Series(caseSwitches)
    ## Only keep switches that start with 'GSw' and have a numeric value
    def isnumeric(x):
        try:
            float(x)
            if '_' not in x:
                return True
        except Exception:
            return False
    gswitches = gswitches.loc[
        gswitches.index.str.lower().str.startswith('gsw')
        & gswitches.map(isnumeric)
    ].copy()
    ## In GAMS we change 'GSw' to 'Sw'
    gswitches.index = gswitches.index.map(lambda x: x[1:])
    ## Add a 'comment' column and write to csv and GAMS-readable text
    gswitches.reset_index().assign(comment='').to_csv(
        os.path.join(inputs_case,'gswitches.csv'), header=False, index=False)

    #%% Information on reV supply curves associated with this run
    shutil.copytree(os.path.join(reeds_path,'inputs','supply_curve','metadata'),
                    os.path.join(inputs_case,'supplycurve_metadata'), dirs_exist_ok=True)
    rev_paths = pd.read_csv(
            os.path.join(reeds_path,'inputs','supply_curve','rev_paths.csv')
        )

    # Separate techs with no associated switch
    rev_paths_none = rev_paths.loc[rev_paths.access_switch == "none",:].copy()
    rev_paths = rev_paths.loc[rev_paths.access_switch != "none",:]

    # Match possible supply curves with switches from this run
    revswitches = pd.DataFrame.from_dict({s:caseSwitches[s] for s in rev_paths.access_switch.unique()},
                                orient='index').reset_index().rename(columns={'index':'access_switch', 0:'access_case'})
    revswitches = revswitches.merge(rev_paths, on=['access_switch', 'access_case'])
    revswitches = pd.concat([revswitches[rev_paths_none.columns.tolist()], rev_paths_none])

    # Get bin information
    bins = {"wind-ons":"numbins_windons", "wind-ofs": "numbins_windofs", "upv":"numbins_upv"}
    binSwitches = pd.DataFrame.from_dict({b:caseSwitches[bins[b]] for b in bins},
                                orient='index').reset_index().rename(columns={'index':'tech', 0:'bins'})

    revswitches = revswitches.merge(binSwitches, on=['tech'], how='left')

    # format rev paths
    revswitches = get_rev_paths(revswitches, caseSwitches)

    # save rev paths file for run
    revswitches[['tech','access_switch','access_case','rev_case','bins','sc_path',
                 'sc_file','hpc_sc_file','cf_path','original_rev_folder']
                ].to_csv(os.path.join(inputs_case,'rev_paths.csv'), index=False)

    #%% Set up the meta.csv file to track repo information and runtime
    logger = os.path.join(reeds_path, 'reeds', 'log.py')
    loglines = ['computer,repo,branch,commit,description\n']
    ### Get some git metadata
    try:
        import git
        import socket
        repo = git.Repo()
        try:
            branch = repo.active_branch.name
            description = repo.git.describe()
        except TypeError:
            branch = 'DETACHED_HEAD'
            description = ''
        loglines.append(
            '{},{},{},{},{}\n'.format(
                socket.gethostname(),
                repo.git_dir, branch, repo.head.object.hexsha, description))
    except Exception:
        ### In case the user hasn't installed GitPython (conda install GitPython)
        ### or isn't in a git repo or anything else goes wrong
        loglines.append('None,None,None,None,None\n')

    with open(os.path.join(casedir,'meta.csv'),'a') as METAFILE:
        ### Header for timing metadata
        for line in loglines:
            METAFILE.writelines(line)
        METAFILE.writelines('#,#,#,#,#\n')
        METAFILE.writelines('year,process,starttime,stoptime,processtime\n')
    ### Also write the git metadata to gamslog.txt for debugging
    with open(os.path.join(casedir,'gamslog.txt'),'a') as LOGFILE:
        for line in loglines:
            LOGFILE.writelines(line)

    ### Write the environment info for debugging
    try:
        environment = subprocess.run('conda list', capture_output=True, shell=True)
        pd.Series(environment.stdout.decode().split('\n')).to_csv(
            os.path.join(casedir,'lstfiles','environment.csv'),
            header=False, index=False,
        )
    except Exception as err:
        print(err)

    ### Copy over the cases file
    shutil.copy2(os.path.join(reeds_path, cases_filename), casedir)

    ### Get hpc setting (used in Augur)
    caseSwitches['hpc'] = int(hpc)
    options += f' --hpc={int(hpc)}'
    ### Get numclass from the max value in ivt
    caseSwitches['numclass'] = get_ivt_numclass(
        reeds_path=reeds_path, casedir=casedir, caseSwitches=caseSwitches)
    options += ' --numclass={}'.format(caseSwitches['numclass'])
    ### Get numbins from the max of individual technology bins
    caseSwitches['numbins'] = max(
        int(caseSwitches['numbins_windons']),
        int(caseSwitches['numbins_windofs']),
        int(caseSwitches['numbins_upv']),
        15)
    options += ' --numbins={}'.format(caseSwitches['numbins'])
    options += f' --reeds_path={reeds_path}{os.sep} --casedir={casedir}'

    #%% Record the switches for this run
    pd.Series(caseSwitches).to_csv(
        os.path.join(inputs_case,'switches.csv'), header=False)

    solveyears = pd.read_csv(
        os.path.join(reeds_path, 'inputs','modeledyears.csv'),
        usecols=[caseSwitches['yearset_suffix']],
    ).squeeze(1).dropna().astype(int).tolist()
    
    # If start year is not in solveyears, start year is added into solveyears set
    if startyear not in solveyears:
        solveyears.append(startyear)
        solveyears = sorted(solveyears)

    solveyears = [y for y in solveyears if (y <= endyear and y >= startyear)]

    yearset_augur = os.path.join('inputs_case','modeledyears.csv')
    toLogGamsString = ' logOption=4 logFile=gamslog.txt appendLog=1 '

    if not restart:
        ## Copy code folders
        for dirname in ['reeds', 'ReEDS_Augur', 'input_processing', 'reeds2pras']:
            shutil.copytree(
                os.path.join(reeds_path, dirname),
                os.path.join(casedir, dirname),
                ignore=shutil.ignore_patterns('test'),
            )

        #make the augur_data folder
        os.makedirs(os.path.join(casedir,'ReEDS_Augur','augur_data'), exist_ok=True)
        os.makedirs(os.path.join(casedir,'ReEDS_Augur','PRAS'), exist_ok=True)

    ###### Replace files according to 'file_replacements' in cases. Ignore quotes in input text.
    # << is used to separate the file that is to be replaced from the file that is used
    # || is used to separate multiple replacements.
    if caseSwitches['file_replacements'] != 'none':
        file_replacements = caseSwitches['file_replacements'].replace('"','').replace("'","").split('||')
        for file_replacement in file_replacements:
            replace_arr = file_replacement.split('<<')
            replaced_file = replace_arr[0].strip()
            replaced_file = os.path.join(casedir, replaced_file)
            if not os.path.isfile(replaced_file):
                raise FileNotFoundError('FILE REPLACEMENT ERROR: "' + replaced_file + '" was not found')
            used_file = replace_arr[1].strip()
            if not os.path.isfile(used_file):
                raise FileNotFoundError('FILE REPLACEMENT ERROR: "' + used_file + '" was not found')
            if os.path.isfile(replaced_file) and os.path.isfile(used_file):
                shutil.copy(used_file, replaced_file)
                print('FILE REPLACEMENT SUCCESS: Replaced "' + replaced_file + '" with "' + used_file + '"')

    ext = '.sh' if LINUXORMAC else '.bat'

    restart_switches = {'restart':restart}
    if restart:
        ### If restarting, get the year from the most recent .g00 file
        g00files = glob(os.path.join(reeds_path,'runs',batch_case,'g00files','*'))
        g00years = []
        for f in g00files:
            try:
                ### Keep it if it ends with _{year}
                g00years.append(int(os.path.splitext(f)[0].split('_')[-1]))
            except ValueError:
                ### If we can't turn the piece after the '_' into an int, it's not a year
                pass

        ### Keep the first year -- this will be the last solve with a completely saved g00 file
        restart_switches['restart_year'] = min(g00years)

        ### Also get last Augur solve
        Augurfiles = glob(os.path.join(reeds_path,'runs',batch_case,'ReEDS_Augur','augur_data','ReEDS_Augur_*.gdx'))
        auguryears = [int(os.path.basename(f).split("_")[-1].split(".")[0]) for f in Augurfiles]

        #  If there is an Augur solve for this year, start the model in next year after the restart
        if restart_switches['restart_year'] in auguryears:
            solveyears = [y for y in solveyears if y > restart_switches['restart_year']]
            restart_switches['restart_Augur'] = False
        else:
        # If there is no Augur solve for this year, start with Augur in the year of the restart
            solveyears = [y for y in solveyears if y >= restart_switches['restart_year']]
            restart_switches['restart_Augur'] = True
    else:
        restart_switches['restart_Augur'] = False

    # Flag for a restart or an original one
    call = 'call_restart_' if restart else 'call_'

    #%% Write the call script
    with open(os.path.join(casedir, call + batch_case + ext), 'w+') as OPATH:
        OPATH.writelines(f"echo 'Running {batch_case}'\n")
        OPATH.writelines("cd " + casedir + '\n' + '\n' + '\n')

        if hpc:
            comment('Set up nodal environment for run', OPATH)
            OPATH.writelines(". $HOME/.bashrc \n")
            OPATH.writelines("module purge \n")

            if os.environ.get('NREL_CLUSTER') == 'kestrel':
                OPATH.writelines("source /nopt/nrel/apps/env.sh \n")
                OPATH.writelines("module load anaconda3 \n")
                OPATH.writelines("module use /nopt/nrel/apps/software/gams/modulefiles \n")
                OPATH.writelines("module load gams \n")
            else:
                OPATH.writelines("module load conda \n")
                OPATH.writelines("module load gams \n")

            OPATH.writelines("conda activate reeds2 \n")
            OPATH.writelines('export R_LIBS_USER="$HOME/rlib" \n\n\n')

        if restart:
            #%% Skip input_processing and model creation if restarting, and set restart file to last available
            restartfile = f'{batch_case}_{restart_switches["restart_year"]}'
        else:
            #%% Write the input_processing script calls
            big_comment('Input processing', OPATH)
            for s in [
                'copy_files',
                'aggregate_regions',
                'calc_financial_inputs',
                'fuelcostprep',
                'writecapdat',
                'writesupplycurves',
                'writedrshift',
                'plantcostprep',
                'climateprep',
                'ldc_prep',
                'forecast',
                'WriteHintage',
                'transmission',
                'outage_rates',
                'hourly_repperiods',
            ]:
                OPATH.writelines(f"echo {'-'*12+'-'*len(s)}\n")
                OPATH.writelines(f"echo 'starting {s}.py'\n")
                OPATH.writelines(f"echo {'-'*12+'-'*len(s)}\n")
                OPATH.writelines(
                    f"python {os.path.join(casedir,'input_processing',s)}.py {reeds_path} {inputs_case}\n")
                OPATH.writelines(writescripterrorcheck(s)+'\n')

            if int(caseSwitches['input_processing_only']):
                OPATH.writelines('\n' + ('exit' if LINUXORMAC else 'goto:eof') + '\n\n')

            big_comment('Compile model', OPATH)

            OPATH.writelines(
                "\ngams createmodel.gms gdxcompress=1 xs="+os.path.join("g00files",batch_case)
                + (' license=gamslice.txt' if hpc else '')
                + " o="+os.path.join("lstfiles","1_Inputs.lst") + options + " " + toLogGamsString + '\n')
            OPATH.writelines(f'python {logger}\n')
            restartfile = batch_case
            OPATH.writelines(writeerrorcheck(os.path.join('g00files',restartfile + '.g*')))

        ################################
        #    -- CORE MODEL SETUP --    #
        ################################
        if caseSwitches['timetype'] == 'seq':
            setup_sequential(
                caseSwitches, reeds_path, hpc,
                solveyears, casedir, batch_case, toLogGamsString, OPATH, logger,
                restart_switches,
            )
        elif caseSwitches['timetype'] == 'int':
            setup_intertemporal(
                caseSwitches, startiter, niter, ccworkers,
                solveyears, endyear, batch_case, toLogGamsString, yearset_augur, OPATH,
            )
        elif caseSwitches['timetype'] == 'win':
            setup_window(
                caseSwitches, startiter, niter, ccworkers, reeds_path,
                batch_case, toLogGamsString, yearset_augur, OPATH,
            )

        #################################
        #    -- OUTPUT PROCESSING --    #
        #################################

        #create reporting files
        big_comment('Output processing', OPATH)
        if not LINUXORMAC:
            OPATH.writelines("setlocal enabledelayedexpansion\n")
        ### If not using stress periods, run for iteration 0
        if int(caseSwitches['GSw_PRM_CapCredit']):
            OPATH.writelines(
                f"r={os.path.join('g00files', f'{batch_case}_{max(solveyears)}i0')}\n"
                if LINUXORMAC else
                f'set "r={os.path.join("g00files", f"{batch_case}_{max(solveyears)}i0")}"\n'
            )
        ### If using stress periods, run for the last iteration (lexicographically sorted)
        else:
            OPATH.writelines(
                f"for r in g00files/{batch_case}_*.g00; do true; done\n"
                if LINUXORMAC else
                f'for %%i in (g00files\{batch_case}_*.g00) do (set "r=%%i")\n'
            )
        OPATH.writelines(
            "gams e_report.gms"
            + f" o={os.path.join('lstfiles',f'report_{batch_case}.lst')}"
            + (' license=gamslice.txt' if hpc else '')
            + (' r=$r' if LINUXORMAC else ' r=!r!')
            + ' gdxcompress=1'
            + toLogGamsString
            + f"--fname={batch_case}"
            + f" --GSw_calc_powfrac={caseSwitches['GSw_calc_powfrac']} \n"
        )
        OPATH.writelines(writescripterrorcheck("e_report.gms"))
        if not LINUXORMAC:
            OPATH.writelines("endlocal\n")
        OPATH.writelines(f'python {logger}\n')
        OPATH.writelines(f'python e_report_dump.py {casedir}\n\n')
        if int(caseSwitches['diagnose']):
             OPATH.writelines(
                "python"
                + f" {os.path.join(reeds_path,'postprocessing','diagnose','diagnose_process.py')}"
                + f" --casepath {casedir} \n\n"
            )
        OPATH.writelines(f'python e_report_dump.py {casedir} -c\n\n')

        ### Run the retail rate module
        if caseSwitches['GSw_Region'].lower() == 'usa':
            OPATH.writelines(
                "python"
                + f" {os.path.join(reeds_path,'postprocessing','retail_rate_module','retail_rate_calculations.py')}"
                + f" {batch_case} -p\n\n"
            )

        ## Run air-quality and health damages calculation script
        if int(caseSwitches['GSw_HealthDamages']):
            OPATH.writelines(
                f"python {os.path.join(reeds_path,'postprocessing','air_quality','health_damage_calculations.py')} {casedir}\n\n"
            )

        ### Make script to unload all data to .gdx file
        command = (
            'gams dump_alldata.gms'
            + ' o='+os.path.join('lstfiles','dump_alldata_{}_{}.lst'.format(BatchName,case))
        )
        command_write = (
            command
            + ' r='+os.path.join('g00files','{}_{}_{}i0'.format(BatchName,case,solveyears[-1]))
        )
        with open(os.path.join(casedir,'dump_alldata'+ext),'w+') as datadumper:
            datadumper.writelines('cd ' + os.path.join(reeds_path,'runs','{}_{}'.format(BatchName,case)) + '\n')
            for line in [
                f"By default, this script dumps data for the first iteration of {solveyears[-1]}.",
                "If more iterations were needed, increase the number at the end of the",
                f"next line after 'i' (e.g. {solveyears[-1]}i0 -> {solveyears[-1]}i1)",
            ]:
                comment(line, datadumper)
            datadumper.writelines(command_write)
        if int(caseSwitches['dump_alldata']) or int(caseSwitches['debug']):
            OPATH.writelines(command + (' r=$r' if LINUXORMAC else ' r=!r!') + '\n')

        ## ReEDS_to_rev processing
        if caseSwitches['reeds_to_rev'] == '1':
            OPATH.writelines('cd {} \n\n'.format(reeds_path))
            OPATH.writelines(f'python hourlize/reeds_to_rev.py {reeds_path} {casedir} "priority" '
                             '-t "wind-ons" -l "gamslog.txt" -r\n')
            OPATH.writelines(f'python hourlize/reeds_to_rev.py {reeds_path} {casedir} "priority" '
                             '-t "wind-ofs" -l "gamslog.txt" -r\n')
            OPATH.writelines(f'python hourlize/reeds_to_rev.py {reeds_path} {casedir} "simultaneous" '
                             '-t "upv" -l "gamslog.txt" -r\n\n')
            OPATH.writelines(f'python hourlize/reeds_to_rev.py {reeds_path} {casedir} "simultaneous" '
                             '-t "geohydro_allkm" -l "gamslog.txt" -r\n\n')
            OPATH.writelines(f'python hourlize/reeds_to_rev.py {reeds_path} {casedir} "simultaneous" '
                             '-t "egs_allkm" -l "gamslog.txt" -r\n\n')

        if caseSwitches['land_use_analysis'] == '1':
            # Run the land-used characterization module
            OPATH.writelines(
                f"python {os.path.join(reeds_path,'postprocessing','land_use','land_use_analysis.py')} {casedir}\n\n"
            )

        ## Run Bokeh
        bokehdir = os.path.join(reeds_path,"postprocessing","bokehpivot","reports")
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(reeds_path,"runs",batch_case) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","standard_report_reduced.py") + ' "html,excel,csv" one '
            + os.path.join(reeds_path,"runs",batch_case,"outputs","reeds-report-reduced") + ' No\n')
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(reeds_path,"runs",batch_case) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","standard_report_expanded.py") + ' "html,excel" one '
            + os.path.join(reeds_path,"runs",batch_case,"outputs","reeds-report") + ' No\n')
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(reeds_path,"runs",batch_case) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","state_report.py") + ' "csv" one '
            + os.path.join(reeds_path,"runs",batch_case,"outputs","reeds-report-state") + ' No\n\n')
        OPATH.writelines('python postprocessing/vizit/vizit_prep.py ' + '"{}"'.format(os.path.join(casedir,'outputs')) + '\n\n')

        if int(caseSwitches['delete_big_files']):
            for file in [
                os.path.join(inputs_case, 'recf.h5'),
                os.path.join(inputs_case, 'load.h5'),
                os.path.join(inputs_case, 'csp_profiles.h5'),
                os.path.join(inputs_case, 'rsc_combined.csv'),
                ### Uncomment the following two lines to delete the .g00 files
                # os.path.join('g00files', restartfile + '.g00'),
                # os.path.join('g00files', restartfile.rstrip(str(cur_year)+'_') + '.g00'),
            ]:
                write_delete_file(checkfile=file, deletefile=file, PATH=OPATH)
            OPATH.writelines('')

        if int(caseSwitches['transmission_maps']):
            OPATH.writelines('python postprocessing/transmission_maps.py -c {} -y {}\n'.format(
                casedir, (
                    solveyears[-1]
                    if int(caseSwitches['transmission_maps']) > int(solveyears[-1])
                    else caseSwitches['transmission_maps'])
            ))

        ### Write the call to the R2X tests
        pipe = '2>&1 | tee -a' if LINUXORMAC else '>>'
        tolog = f"{pipe} {os.path.join(casedir,'gamslog.txt')}"
        OPATH.writelines(
            f"\npython -m pytest -v -l tests/test_r2x_integration.py --casepath {casedir} {tolog}\n"
        )

        ### Check the error level
        OPATH.writelines(f"\npython postprocessing/check_error.py {casedir} {tolog}\n")

    ### =====================================================================================
    ### --- CALL THE CREATED BATCH FILE ---
    ### =====================================================================================

    # If you're not running on eagle or AWS...
    if (not hpc) & (not int(caseSwitches['AWS'])):
        # Start the command prompt similar to the sequential solve
        # - waiting for it to finish before starting a new thread
        if LINUXORMAC:
            print("Starting the run for case " + batch_case)
            # Give execution rights to the shell script
            os.chmod(os.path.join(casedir, call + batch_case + ext), 0o777)
            # Open it up - note the in/out/err will be written to the shellscript parameter
            shellscript = subprocess.Popen(
                [os.path.join(casedir, call + batch_case + ext)], shell=True)
            # Wait for it to finish before killing the thread
            shellscript.wait()
        else:
            if int(caseSwitches['keep_run_terminal']) == 1:
                terminal_keep_flag = ' /k '
            else:
                terminal_keep_flag = ' /c '
            os.system('start /wait cmd' + terminal_keep_flag + os.path.join(casedir, call + batch_case + ext))

    elif hpc:
        # Create a copy of srun_template in casedir as {batch_case}.sh
        shutil.copy("srun_template.sh", os.path.join(casedir, batch_case+".sh"))

        # option to run on a debug node on an hpc system
        if debugnode:
            writelines = []
            # comment out original time specification
            with open(os.path.join(casedir, batch_case+".sh"), 'r') as SPATH:
                for line in SPATH:
                    writelines.append(('# ' if '--time' in line else '') + line.strip())
            # rewrite file with new time and debug partition
            with open(os.path.join(casedir, batch_case+".sh"), 'w') as SPATH:
                for line in writelines:
                    SPATH.writelines(line + '\n')
                SPATH.writelines("#SBATCH --time=01:00:00\n")
                SPATH.writelines("#SBATCH --partition=debug\n")

        with open(os.path.join(casedir, batch_case+".sh"), 'a') as SPATH:
            # Add the name for easy tracking of the case
            SPATH.writelines("#SBATCH --job-name=" + batch_case + "\n")
            SPATH.writelines("#SBATCH --output=" + os.path.join(casedir, "slurm-%j.out") + "\n\n")
            SPATH.writelines("#load your default settings\n")
            SPATH.writelines(". $HOME/.bashrc" + "\n\n")
            # Add the call to the sh file created throughout this function
            SPATH.writelines("sh " + os.path.join(casedir, call + batch_case + ext))
        # Close the file
        SPATH.close()
        # Call that file
        batchcom = "sbatch " + os.path.join(casedir, batch_case + ".sh")
        subprocess.Popen(batchcom.split())

    elif int(caseSwitches['AWS']):
        print("Starting the run for case " + batch_case)
        # Give execution rights to the shell script
        os.chmod(os.path.join(casedir, call + batch_case + ext), 0o777)
        # Issue a nohup (no hangup) command and direct output to
        # case-specific txt files in the root of the repository
        shellscript = subprocess.Popen(
            ['nohup ' + os.path.join(casedir, call + batch_case + ext) + " > " +os.path.join(casedir,batch_case+ ".txt") ],
                stdin=open(os.path.join(casedir,batch_case+"_in.txt"),'w'),
                stdout=open(os.path.join(casedir,batch_case+"_out.txt"),'w'),
                stderr=open(os.path.join(casedir,batch_case+"_err.log"),'w'),
                shell=True,preexec_fn=os.setpgrp)
        # Wait for it to finish before killing the thread
        shellscript.wait()

    ### Record the ending time
    now = datetime.isoformat(datetime.now())
    try:
        with open(os.path.join(casedir,'meta.csv'), 'a') as METAFILE:
            METAFILE.writelines('0,end,,{},\n'.format(now))
    except Exception:
        print('meta.csv not found or not writeable')
        pass


def main(
        BatchName='', cases_suffix='', single='', simult_runs=0,
        forcelocal=False, restart=False, skip_checks=False,
        debug=False, debugnode=False,
    ):
    """
    Executes parallel solves based on cases in 'cases.csv'
    """
    print(" ")
    print(" ")
    print("--------------------------------------------------------------------------------------------------")
    print(" ")
    print("         MMM.  808   MMM;   BMW       rMM   @MMMMMMMM2     XM@MMMMMMMMMS   MM0         ")
    print("        iMMM@S,MMM;X@MMMZ   MMMM.     aMM   MMMW@MMMMMMM   BMMMW@M@M@MMX   MMM         ")
    print("         r2MMZ     SMMa;i   MMMMM;    SMM   MMB      7MMS  ZMM.            MMM         ")
    print("           Z         Z      MMZ7MM2   XMM   MMW       MM8  ZMM.            MMM         ")
    print("        .MMr         .MM7   MM8 rMMB  XMM   MM@     ,MMM   ZMMMMMMMMMM     MMM         ")
    print("        .MMr         ,MMr   MMB  :MMM :MM   MMW  MMMMMB    ZMMMWMMMMM@     MMM         ")
    print("           Z         Z      MMW    MMMaMM   MM@   MMMi     ZMM.            MMM         ")
    print("         XaMM8     aMMZXi   MMW     MMMMM   MM@    0MMr    ZMM.            MMW         ")
    print("        iMMMW7,MMM;;BMMMZ   MMM      8MMM   MMM     aMMB   0MMMWMMM@MMMZ   MMM@MMMMMMM ")
    print("         BZ0   SSS   0Z0.   ZBX       :0B   8BS      :BM7  ;8Z8WWWWWW@M2   BZZ0WWWWWWM ")
    print(" ")
    print("--------------------------------------------------------------------------------------------------")
    print(" ")
    print(" ")

    # Gather user inputs before calling GAMS programs
    envVar = setupEnvironment(
        BatchName=BatchName, cases_suffix=cases_suffix,
        single=single, simult_runs=simult_runs,
        forcelocal=forcelocal, restart=restart, skip_checks=skip_checks,
        debug=debug, debugnode=debugnode,
    )
    # Threads are created which will handle each case individually
    createmodelthreads(envVar)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--BatchName', '-b', type=str, default='',
                        help='Name for batch of runs')
    parser.add_argument('--cases_suffix', '-c', type=str, default='',
                        help='Suffix for cases CSV file')
    parser.add_argument('--single', '-s', type=str, default='',
                        help='Name of a single case to run (or comma-delimited list)')
    parser.add_argument('--simult_runs', '-r', type=int, default=0,
                        help='Number of simultaneous runs. If negative, run all simultaneously.')
    parser.add_argument('--forcelocal', '-l', action='store_true',
                        help='Force model to run locally instead of submitting a slurm job')
    parser.add_argument('--restart', action="store_true",
                        help='Switch to restart existing ReEDS runs')
    parser.add_argument('--skip_checks', '-f', action="store_true",
                        help="Force run, skipping checks on conda environment and switches")
    parser.add_argument('--debug', '-d', action='count', default=0,
                        help="Run in debug mode (same behavior as debug switch in cases.csv)")
    parser.add_argument('--debugnode', '-n', action="store_true",
                        help="Run using debug specifications for slurm on an hpc system")

    args = parser.parse_args()

    main(
        BatchName=args.BatchName, cases_suffix=args.cases_suffix, single=args.single,
        simult_runs=args.simult_runs, forcelocal=args.forcelocal,
        restart=args.restart, skip_checks=args.skip_checks,
        debug=args.debug, debugnode=args.debugnode,
    )
