#%% IMPORTS
import os
import sys
import queue
import threading
import time
import shutil
import csv
import numpy as np
import pandas as pd
import numpy as np
import subprocess
from datetime import datetime
import argparse
from builtins import input

#############
#%% FUNCTIONS

def scalar_csv_to_txt(path_to_scalar_csv):
    """
    Write a scalar csv to GAMS-readable text
    Format of csv should be: scalar,value,comment
    """
    ### Load the csv
    dfscalar = pd.read_csv(
        path_to_scalar_csv,
        header=None, names=['scalar','value','comment'], index_col='scalar').fillna(' ')
    ### Create the GAMS-readable string (comments can only be 255 characters long)
    scalartext = '\n'.join([
        'scalar {:<30} "{:<5.255}" /{}/ ;'.format(
            i, row['comment'], row['value'])
        for i, row in dfscalar.iterrows()
    ])
    ### Write it to a file, replacing .csv with .txt in the filename
    with open(path_to_scalar_csv.replace('.csv','.txt'), 'w') as w:
        w.write(scalartext)

    return dfscalar


def writeerrorcheck(checkfile, errorcode=17):
    """
    Inputs
    ------
    checkfile: Filename to check. If it does not exist, stop the run.
    errorcode: Value to return if check fails. Should be >0.
    """
    if os.name!='posix':
        return f'\nif not exist {checkfile} (\n echo file {checkfile} missing \n goto:eof \n) \n \n'
    else:
        return f'\nif [ ! -f {checkfile} ]; then \n    exit {errorcode}\nfi\n\n'

def writescripterrorcheck(errorcode=18):
    """
    """
    if os.name == 'posix':
        return f'if [ $? != 0 ]; then echo "script returned $?"; exit {errorcode}; fi\n'
    else:
        return f'if not %errorlevel% == 0 (echo script returned %errorlevel%\ngoto:eof\n)\n'


def write_delete_file(checkfile, deletefile, PATH):
    if os.name=='posix':
        PATH.writelines("if [ -f " + checkfile + " ]; then \n   rm " + deletefile + '\nfi\n\n' )
    else:
        PATH.writelines("if exist " + checkfile + " (del " + deletefile + ')\n' )


def addMPSToOpt(optFileNum, case_dir):
    #Modify the optfile to create an mps file.
    if int(optFileNum) == 1:
        origOptExt = 'opt'
    elif int(optFileNum) < 10:
        origOptExt = 'op' + optFileNum
    else:
        origOptExt = 'o' + optFileNum
    #Add writemps statement to opt file
    with open(case_dir + '/cplex.'+origOptExt, 'a') as file:
        file.write('\nwritemps ReEDSmodel.mps')


def get_ivt_numclass(InputDir, casedir, caseSwitches):
    """
    Extend ivt if necessary and calculate numclass
    """
    ivt = pd.read_csv(
        os.path.join(
            InputDir, 'inputs', 'userinput', 'ivt_{}.csv'.format(caseSwitches['ivt_suffix'])),
        index_col=0)
    ivt_step = pd.read_csv(os.path.join(InputDir, 'inputs', 'userinput', 'ivt_step.csv'), 
                           index_col=0, squeeze=True)
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


#############
#%% PROCEDURE 

def setupEnvironment(BatchName=False, cases_suffix=False, simult_runs=0, verbose=0, forcelocal=0):
    # #%% Inputs for debugging
    # BatchName = 'v20220422_clusterM0_h8760_CL4_CF1_CC10_SD73_noH2_NSMR0_ERCOT'
    # cases_suffix = 'hourly4'
    # WORKERS = 1
    # verbose = 1
    # forcelocal = 0

    #%% Automatic inputs
    InputDir = os.getcwd()

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
        if not confirm_local in ['y','Y','yes','Yes','YES']:
            quit()

    #%% Load specified case file, infer other settings from cases.csv
    df_cases = pd.read_csv('cases.csv', dtype=object, index_col=0)
    cases_filename = 'cases.csv'

    #If we have a case suffix, use cases_[suffix].csv for cases.
    if cases_suffix not in ['','default']:
        df_cases = df_cases[['Choices', 'Default Value']]
        cases_filename = 'cases_' + cases_suffix + '.csv'
        df_cases_suf = pd.read_csv(cases_filename, dtype=object, index_col=0)

        #First use 'Default Value' from cases_[suffix].csv to fill missing switches
        #Later, we will also use 'Default Value' from cases.csv to fill any remaining holes.
        if 'Default Value' in df_cases_suf.columns:
            case_i = df_cases_suf.columns.get_loc('Default Value') + 1
            casenames = df_cases_suf.columns[case_i:].tolist()
            for case in casenames:
                df_cases_suf[case] = df_cases_suf[case].fillna(df_cases_suf['Default Value'])
        df_cases_suf.drop(['Choices','Default Value'], axis='columns',inplace=True, errors='ignore')
        df_cases = df_cases.join(df_cases_suf, how='outer')

    # initiate the empty lists which will be filled with info from cases
    caseList = []
    caseSwitches = [] #list of dicts, one dict for each case
    casenames = [c for c in df_cases.columns if not c in ['Description','Default Value','Choices']]
    # Get the list of switch choices
    choices = df_cases.Choices.copy()

    for case in casenames:
        #Fill any missing switches with the defaults in cases.csv
        df_cases[case] = df_cases[case].fillna(df_cases['Default Value'])
        # Ignore cases with ignore flag
        if int(df_cases.loc['ignore',case]) == 1:
            continue
        # Check to make sure the switch setting is valid
        for i, val in df_cases[case].iteritems():
            ### Split choices by either '; ' or ','
            if choices[i] in ['N/A',None,np.nan]:
                pass
            else:
                i_choices = [
                    str(j).strip() for j in 
                    np.ravel([i.split(',') for i in choices[i].split(';')]).tolist()
                ]
                if str(val) not in i_choices:
                    error = (
                        'Invalid entry for "{}" for case "{}".\n'
                        'Entered "{}" but must be one of the following:\n\n{}'
                    ).format(i, case, val, '\n'.join(i_choices))
                    raise ValueError(error)
        # Add switch settings to list of options passed to GAMS
        shcom = ' --case=' + BatchName + "_" + case
        for i,v in df_cases[case].iteritems():
            #exclude certain switches that don't need to be passed to GAMS
            if i not in ['file_replacements','keep_run_terminal']:
                shcom = shcom + ' --' + i + '=' + v
        caseList.append(shcom)
        caseSwitches.append(df_cases[case].to_dict())

    # ignore cases with ignore flag
    casenames = [case for case in casenames if int(df_cases.loc['ignore',case]) != 1]
    df_cases.drop(
        df_cases.loc['ignore'].loc[df_cases.loc['ignore']=='1'].index, axis=1, inplace=True)

    # Make sure the run folders don't already exist
    outpaths = [os.path.join(InputDir,'runs','{}_{}'.format(BatchName,case)) for case in casenames]
    existing_outpaths = [i for i in outpaths if os.path.isdir(i)]
    if len(existing_outpaths):
        error = (
            'The following output directories already exist.\n'
            'Please use a new batch name or case names.\n\n{}'
        ).format('\n'.join([os.path.basename(i) for i in existing_outpaths]))
        raise IsADirectoryError(error)

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
    elif simult_runs < 0:
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
        'InputDir' : InputDir,
        'niter' : niter,
        'startiter' : startiter,
        'cases_filename': cases_filename,
        'verbose': verbose,
        'hpc': hpc,
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
                InputDir=ThreadInit['InputDir'],
                ccworkers=ThreadInit['ccworkers'],
                startiter=ThreadInit['startiter'],
                BatchName=ThreadInit['BatchName'],
                case=ThreadInit['casename'],
                cases_filename=ThreadInit['cases_filename'],
                verbose=envVar['verbose'],
                hpc=envVar['hpc'],
            )
            print(ThreadInit['lstfile'] + " has finished \n")
            q.task_done()


    threads = []

    for i in range(num_worker_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for i in range(len(envVar['caseList'])):
        q.put({'scen': envVar['caseList'][i],
               'caseSwitches': envVar['caseSwitches'][i],
               'lstfile':envVar['BatchName']+'_'+envVar['casenames'][i],
               'niter':envVar['niter'],
               'InputDir':envVar['InputDir'],
               'ccworkers':envVar['ccworkers'],
               'startiter':envVar['startiter'],
               'BatchName':envVar['BatchName'],
               'casename':envVar['casenames'][i],
               'cases_filename':envVar['cases_filename'],
               })

    # block until all tasks are done
    q.join()

    # stop workers
    for i in range(num_worker_threads):
        q.put(None)

    for t in threads:
        t.join()


def runModel(options, caseSwitches, niter, InputDir, ccworkers, startiter,
             BatchName, case, cases_filename, verbose=0, hpc=False):
    ### For debugging
    # caseSwitches = caseSwitches[0]
    ### Inferred inputs
    lstfile = '{}_{}'.format(BatchName,case)
    endyear = int(caseSwitches['endyear'])

    casedir = os.path.join(InputDir,"runs",lstfile)
    inputs_case = os.path.join(casedir,"inputs_case")

    if os.path.exists(os.path.join("runs",lstfile)):
        print("Caution, case " + lstfile + " already exists in runs \n")

    #%% Set up case-specific directory structure
    os.makedirs(os.path.join("runs",lstfile), exist_ok=True)
    os.makedirs(os.path.join("runs",lstfile,"g00files"), exist_ok=True)
    os.makedirs(os.path.join("runs",lstfile,"lstfiles"), exist_ok=True)
    os.makedirs(os.path.join("runs",lstfile,"outputs"), exist_ok=True)
    os.makedirs(os.path.join("runs",lstfile,"outputs","tc_phaseout_data"), exist_ok=True)
    os.makedirs(inputs_case, exist_ok=True)

    #%% Coerce some switches based on model compatibility

    #%% Record some metadata about this run
    pd.Series(caseSwitches).to_csv(os.path.join(inputs_case,'switches.csv'), header=False)

    #%% Write the GAMS switches
    gswitches = pd.Series(caseSwitches)
    ## Only keep switches that start with 'GSw' and have a numeric value
    def isnumeric(x):
        try:
            float(x)
            if '_' not in x:
                return True
        except:
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
    scalar_csv_to_txt(os.path.join(inputs_case,'gswitches.csv'))

    #%% Information on reV supply curves associated with this run
    shutil.copytree(os.path.join(InputDir,'inputs','supplycurvedata','metadata'),
                    os.path.join(inputs_case,'supplycurve_metadata'))
    revData = pd.read_csv(
            os.path.join(InputDir,'inputs','supplycurvedata','metadata','rev_paths.csv')
        )

    # separate techs with no associated switch
    revDataSub = revData.loc[revData.access_switch == "none",:].copy()
    revData = revData.loc[revData.access_switch != "none",:]

    # match possible supply curves with switches from this run
    siteSwitches = pd.DataFrame.from_dict({s:caseSwitches[s] for s in revData.access_switch.unique()},
                                orient='index').reset_index().rename(columns={'index':'access_switch', 0:'access_case'})
    siteSwitches = siteSwitches.merge(revData, on=['access_switch', 'access_case'])
    siteSwitches = pd.concat([siteSwitches[revDataSub.columns.tolist()], revDataSub])

    # get bin information
    bins = {"wind-ons":"numbins_windons", "wind-ofs": "numbins_windofs", "upv":"numbins_upv"}
    binSwitches = pd.DataFrame.from_dict({b:caseSwitches[bins[b]] for b in bins},
                                orient='index').reset_index().rename(columns={'index':'tech', 0:'bins'})

    siteSwitches = siteSwitches.merge(binSwitches, on=['tech'], how='left')

    # expand on reV path based on where this run is happening
    # To DO: add functionality for AWS
    eagle_path = '/shared-projects/reeds/Supply_Curve_Data'
    if hpc:
        rev_prefix = eagle_path
    else:
        if os.name == 'posix':
            drive = '/Volumes/'
        else:
            drive = '//nrelnas01/'
        rev_prefix = os.path.join(drive,'ReEDS','Supply_Curve_Data')

    siteSwitches['rev_case'] = siteSwitches['rev_path'].apply(lambda row: os.path.basename(row))
    siteSwitches['eagle_path'] = siteSwitches['rev_path'].apply(lambda row: os.path.join(eagle_path, row))
    siteSwitches['rev_path'] = siteSwitches['rev_path'].apply(lambda row: os.path.join(rev_prefix, row))
    siteSwitches['sc_path'] = siteSwitches['sc_path'].apply(lambda row: os.path.join(rev_prefix, row))
    siteSwitches[['tech', 'access_switch', 'access_case', 'bins','rev_case', 'rev_path', 'eagle_path', 'sc_path', 'eagle_sc_file']].to_csv(
                                        os.path.join(inputs_case,'supplycurve_metadata','rev_supply_curves.csv'), index=False)

    ticker = os.path.join(os.getcwd(),'input_processing','ticker.py')
    with open(os.path.join(casedir,'meta.csv'), 'w+') as METAFILE:
        ### Write some git metadata
        METAFILE.writelines('computer,repo,branch,commit,\n')
        try:
            import git
            import socket
            repo = git.Repo()
            try:
                branch = repo.active_branch.name
            except TypeError:
                branch = 'DETACHED_HEAD'
            METAFILE.writelines(
                '{},{},{},{},\n'.format(
                    socket.gethostname(),
                    repo.git_dir, branch, repo.head.object.hexsha))
        except:
            ### In case the user hasn't installed GitPython (conda install GitPython)
            ### or isn't in a git repo or anything else goes wrong
            METAFILE.writelines('None,None,None,None,\n')

        ### Header for timing metadata
        METAFILE.writelines('#,#,#,#,#\n')
        METAFILE.writelines('year,process,starttime,stoptime,processtime\n')

    ### Copy over the cases file and the files in filesforbatch.csv
    shutil.copy2(os.path.join(InputDir, cases_filename), casedir)
    with open('filesforbatch.csv', 'r') as f:
        reader = csv.reader(f, delimiter = ',')
        for row in reader:
            filename = row[0]
            if filename.split('/')[0] in ['inputs', 'postprocessing']:
                dir_dst = inputs_case
            else:
                dir_dst = casedir
            src_file = os.path.join(InputDir, filename)
            if os.path.exists(src_file):
                shutil.copy(src_file, dir_dst)

    ### Rewrite the scalar table as GAMS-readable definitions
    scalar_csv_to_txt(os.path.join(inputs_case,'scalars.csv'))

    ### Get hpc setting (used in Augur)
    caseSwitches['hpc'] = int(hpc)
    options += f' --hpc={int(hpc)}'
    ### Get numclass from the max value in ivt
    caseSwitches['numclass'] = get_ivt_numclass(
        InputDir=InputDir, casedir=casedir, caseSwitches=caseSwitches)
    options += ' --numclass={}'.format(caseSwitches['numclass'])
    ### Get numbins from the max of individual technology bins
    caseSwitches['numbins'] = max(
        int(caseSwitches['numbins_windons']),
        int(caseSwitches['numbins_windofs']),
        int(caseSwitches['numbins_upv']),
        15)
    options += ' --numbins={}'.format(caseSwitches['numbins'])
    options += f' --basedir={InputDir}{os.sep} --casedir={casedir}'

    solveyears = pd.read_csv(
        os.path.join('inputs','modeledyears.csv'),
        usecols=[caseSwitches['yearset_suffix']], squeeze=True,
    ).dropna().astype(int).tolist()
    solveyears = [y for y in solveyears if y <= endyear]
    yearset_augur = os.path.join('inputs_case','modeledyears.csv')
    toLogGamsString = ' logOption=4 logFile=gamslog.txt appendLog=1 '

    if caseSwitches['GSw_ValStr'] != '0':
        addMPSToOpt(caseSwitches['GSw_gopt'], casedir)

    ###### Write run-specific files
    ### Special-case files for individual sites
    if int(caseSwitches['GSw_IndividualSites']):
        shutil.copy(os.path.join(InputDir,'inputs','rsmap.csv'),
                    inputs_case)
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ons_prescribed_builds_site_{}.csv'.format(caseSwitches['GSw_SitingWindOns'])),
                    os.path.join(inputs_case,'wind-ons_prescribed_builds.csv'))
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ofs_prescribed_builds_site_{}.csv'.format(caseSwitches['GSw_SitingWindOfs'])),
                    os.path.join(inputs_case,'wind-ofs_prescribed_builds.csv'))
    else:
        shutil.copy(os.path.join(InputDir,'inputs','rsmap_sreg.csv'),
                    os.path.join(inputs_case,'rsmap.csv'))
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ons_prescribed_builds_sreg_{}.csv'.format(caseSwitches['GSw_SitingWindOns'])),
                    os.path.join(inputs_case,'wind-ons_prescribed_builds.csv'))
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ofs_prescribed_builds_sreg_{}.csv'.format(caseSwitches['GSw_SitingWindOfs'])),
                    os.path.join(inputs_case,'wind-ofs_prescribed_builds.csv'))

    ### Specific versions of files
    osprey_num_years = len(caseSwitches['osprey_years'].split(','))
    shutil.copy(
        os.path.join(
            InputDir, 'inputs', 'variability', 'index_hr_map_{}.csv'.format(osprey_num_years)),
        os.path.join(inputs_case, 'index_hr_map.csv')
    )
    shutil.copy(
        os.path.join(
            InputDir, 'inputs', 'variability', 'd_szn_{}.csv'.format(osprey_num_years)),
        os.path.join(inputs_case, 'd_szn.csv')
    )
    shutil.copy(
        os.path.join(
            InputDir,'inputs','state_policies','offshore_req_{}.csv'.format(caseSwitches['GSw_OfsWindForceScen'])),
        os.path.join(inputs_case,'offshore_req.csv')
    )
    shutil.copy(
        os.path.join(
            InputDir,'inputs','consume',f"dac_gas_{caseSwitches['GSw_DAC_Gas_Case']}.csv"),
        os.path.join(inputs_case,'dac_gas.csv')
    )
    shutil.copy(
        os.path.join(
            InputDir,'inputs','carbonconstraints',f"capture_rates_{caseSwitches['GSw_CCS_Rate']}.csv"),
        os.path.join(inputs_case,'capture_rates.csv')
    )
    shutil.copy(
        os.path.join(
            InputDir,'inputs','hierarchy{}.csv'.format(
                '' if (caseSwitches['GSw_HierarchyFile'] == 'default')
                else '_'+caseSwitches['GSw_HierarchyFile'])),
        os.path.join(inputs_case,'hierarchy.csv')
    )
    for f in ['distPVCF','distPVcap','distPVCF_hourly']:
        shutil.copy(
            os.path.join(
                InputDir,'inputs','dGen_Model_Inputs','{s}','{f}_{s}.csv').format(
                    f=f, s=caseSwitches['distpvscen']),
            os.path.join(inputs_case, f'{f}.csv')
        )
    pd.read_csv(
        os.path.join(InputDir,'inputs','loaddata',f"demand_{caseSwitches['demandscen']}.csv"),
    ).round(6).to_csv(os.path.join(inputs_case,'load_multiplier.csv'),index=False)

    ### Files defined from case inputs
    pd.DataFrame(
        {'*pvb_type': ['pvb{}'.format(i) for i in range(1,4)],
         'ilr': [np.around(float(c) / 100, 2) for c in caseSwitches['GSw_PVB_ILR'].split('_')]}
    ).to_csv(os.path.join(inputs_case, 'pvb_ilr.csv'), index=False)

    pd.DataFrame(
        {'*pvb_type': ['pvb{}'.format(i) for i in range(1,4)],
         'bir': [np.around(float(c) / 100, 2) for c in caseSwitches['GSw_PVB_BIR'].split('_')]}
    ).to_csv(os.path.join(inputs_case, 'pvb_bir.csv'), index=False)

    ### Constant value if input is float, otherwise named profile
    try:
        rate = float(caseSwitches['GSw_MethaneLeakageScen'])
        pd.Series(index=range(2010,2051), data=rate, name='constant').rename_axis('*t').round(5).to_csv(
            os.path.join(inputs_case,'methane_leakage_rate.csv'))
    except ValueError:
        pd.read_csv(
            os.path.join(InputDir,'inputs','carbonconstraints','methane_leakage_rate.csv'),
            index_col='t',
        )[caseSwitches['GSw_MethaneLeakageScen']].rename_axis('*t').round(5).to_csv(
            os.path.join(inputs_case,'methane_leakage_rate.csv'))


    ### Single column from input table
    pd.read_csv(
        os.path.join(InputDir,'inputs','carbonconstraints','ng_crf_penalty.csv'), index_col='t',
    )[caseSwitches['GSw_NG_CRF_penalty']].rename_axis('*t').to_csv(
        os.path.join(inputs_case,'ng_crf_penalty.csv')
    )
    pd.read_csv(
        os.path.join(InputDir,'inputs','carbonconstraints','co2_cap.csv'), index_col='t',
    ).loc[caseSwitches['GSw_AnnualCapScen']].rename_axis('*t').to_csv(
        os.path.join(inputs_case,'co2_cap.csv')
    )
    pd.read_csv(
        os.path.join(InputDir,'inputs','carbonconstraints','co2_tax.csv'), index_col='t',
    )[caseSwitches['GSw_CarbTaxOption']].rename_axis('*t').round(2).to_csv(
        os.path.join(inputs_case,'co2_tax.csv')
    )
    pd.DataFrame(columns=solveyears).to_csv(
        os.path.join(inputs_case,'modeledyears.csv'), index=False)
    pd.read_csv(
        os.path.join(InputDir,'inputs','national_generation','gen_mandate_trajectory.csv'),
        index_col='GSw_GenMandateScen'
    ).loc[caseSwitches['GSw_GenMandateScen']].rename_axis('*t').round(5).to_csv(
        os.path.join(inputs_case,'gen_mandate_trajectory.csv')
    )
    pd.read_csv(
        os.path.join(InputDir,'inputs','national_generation','gen_mandate_tech_list.csv'),
        index_col='*i',
    )[caseSwitches['GSw_GenMandateList']].to_csv(
        os.path.join(inputs_case,'gen_mandate_tech_list.csv')
    )
    pd.read_csv(
        os.path.join(InputDir,'inputs','climate','climate_heuristics_yearfrac.csv'),
        index_col='*t',
    )[caseSwitches['GSw_ClimateHeuristics']].round(3).to_csv(
        os.path.join(inputs_case,'climate_heuristics_yearfrac.csv')
    )
    pd.read_csv(
        os.path.join(InputDir,'inputs','climate','climate_heuristics_finalyear.csv'),
        index_col='*parameter',
    )[caseSwitches['GSw_ClimateHeuristics']].round(3).to_csv(
        os.path.join(inputs_case,'climate_heuristics_finalyear.csv')
    )
    pd.read_csv(
        os.path.join(InputDir,'inputs','capacitydata','upgrade_costs_ccs_coal.csv'),
        index_col='t',
    )[caseSwitches['ccs_upgrade_cost_case']].round(3).rename_axis('*t').to_csv(
        os.path.join(inputs_case,'upgrade_costs_ccs_coal.csv')
    )
    pd.read_csv(
        os.path.join(InputDir,'inputs','capacitydata','upgrade_costs_ccs_gas.csv'),
        index_col='t',
    )[caseSwitches['ccs_upgrade_cost_case']].round(3).rename_axis('*t').to_csv(
        os.path.join(inputs_case,'upgrade_costs_ccs_gas.csv')
    )

    ### All files from the user input folder
    userinputs = os.listdir(os.path.join(InputDir,"inputs","userinput"))

    for file_name in userinputs:
        full_file_name = os.path.join(InputDir,"inputs","userinput", file_name)
        # ivt is now a special case written in calc_financial_inputs, so skip it here
        if (os.path.isfile(full_file_name) and (file_name != 'ivt.csv')):
            shutil.copy(full_file_name, inputs_case)

    ### Legacy files - no longer used
    if caseSwitches['unitdata'] == 'ABB':
        nas = '//nrelnas01/ReEDS/FY18-ReEDS-2.0/data/'
        out = os.path.join(InputDir,'inputs','capacitydata')
        shutil.copy(os.path.join(nas,'ExistingUnits_ABB.gdx'), out)
        shutil.copy(os.path.join(nas,'PrescriptiveBuilds_ABB.gdx'), out)
        shutil.copy(os.path.join(nas,'PrescriptiveRetirements_ABB.gdx'), out)
        shutil.copy(os.path.join(nas,'ReEDS_generator_database_final_ABB.gdx'), out)

    #copy over the ReEDS_Augur folder
    shutil.copytree(os.path.join(InputDir,"ReEDS_Augur"),os.path.join(casedir,'ReEDS_Augur'))

    #make the augur_data folder
    os.mkdir(os.path.join(casedir,'ReEDS_Augur','augur_data'))

    ###### Replace files according to 'file_replacements' in cases. Ignore quotes in input text.
    #<< is used to separate the file that is to be replaced from the file that is used
    #|| is used to separate multiple replacements.
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

    ext = '.sh' if os.name == 'posix' else '.bat'
    comment = '#' if os.name == 'posix' else '::'

    with open(os.path.join(casedir, 'call_' + lstfile + ext), 'w+') as OPATH:
        OPATH.writelines("cd " + casedir + '\n' + '\n' + '\n')

        if hpc:

            OPATH.writelines(comment + " setting up nodal environment for run \n")
            OPATH.writelines(". $HOME/.bashrc \n")
            OPATH.writelines("module purge \n")
            OPATH.writelines("module load conda \n")
            OPATH.writelines("conda activate reeds \n")
            OPATH.writelines("module load gams \n")
            OPATH.writelines('export R_LIBS_USER="$HOME/rlib" \n\n\n')

        #%% Write the input_processing script calls
        OPATH.writelines(comment + " Input processing scripts\n")
        tolog = ''
        for s in [
            'calc_financial_inputs',
            'fuelcostprep',
            'writecapdat',
            'writesupplycurves',
            'cfgather',
            'writedrshift',
            'plantcostprep',
            'all_year_load',
            'climateprep',
            'LDC_prep',
            'forecast',
            'WriteHintage',
            'transmission_multilink',
            'hourly_process',
            'aggregate_regions',
        ]:
            if verbose:
                OPATH.writelines(f"echo 'starting {s}.py'\n")
            OPATH.writelines(
                f"python {os.path.join(InputDir,'input_processing',s)}.py {InputDir} {inputs_case} {tolog}\n")
            OPATH.writelines(writescripterrorcheck()+'\n')

        OPATH.writelines(
            "\ngams createmodel.gms gdxcompress=1 xs="+os.path.join("g00files",lstfile)
            + (' license=gamslice.txt' if hpc else '')
            + " o="+os.path.join("lstfiles","1_Inputs.lst") + options + " " + toLogGamsString + '\n')
        OPATH.writelines('python {t}\n'.format(t=ticker))
        restartfile = lstfile
        OPATH.writelines(writeerrorcheck(os.path.join('g00files',restartfile + '.g*')))


    #############################
    # -- SEQUENTIAL SETUP --
    #############################

        if caseSwitches['timetype']=='seq':
            #loop over solve years
            for i in range(len(solveyears)):

                #current year is the value in solveyears
                cur_year = solveyears[i]
                if cur_year < max(solveyears):
                    #next year becomes the next item in the solveyears vector
                    next_year = solveyears[i+1]
                # Get previous year if after first year
                if i:
                    prev_year = solveyears[i-1]
                else:
                    prev_year = solveyears[i]
                #make an indicator in the batch file for what year is being solved
                OPATH.writelines('\n' + comment + ' \n')
                OPATH.writelines(comment + " Year: " + str(cur_year)  + ' \n')
                OPATH.writelines(comment  + ' \n')

                #savefile is the lstfile plus the current name
                savefile = lstfile+"_"+str(cur_year)

                #Calc tax credit Phasedown
                OPATH.writelines(f"python tc_phaseout.py {cur_year} {casedir}\n")

                #solve one year
                OPATH.writelines(
                    "gams d_solveoneyear.gms"
                    + (" license=gamslice.txt" if hpc else '')
                    + " o="+os.path.join("lstfiles",savefile+".lst")
                    + " r="+os.path.join("g00files",restartfile)
                    + " gdxcompress=1 xs=" + os.path.join("g00files",savefile) + toLogGamsString
                    + " --case=" + lstfile
                    + " --cur_year=" + str(cur_year) + " --next_year=" + str(next_year)
                    + " --prev_year=" + str(prev_year)
                    + " --GSW_SkipAugurYear={}".format(caseSwitches['GSw_SkipAugurYear'])
                    + " --GSw_IndividualSites={}".format(caseSwitches['GSw_IndividualSites'])
                    + '\n')
                OPATH.writelines(writescripterrorcheck())
                OPATH.writelines('python {t} --year={y}\n'.format(t=ticker, y=cur_year))

                if caseSwitches['GSw_ValStr'] != '0':
                    OPATH.writelines( "python valuestreams.py" + '\n')

                #check to see if the restart file exists
                OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))

                # Run Augur if it not the final solve year and if not skipping Augur
                if (
                    ((cur_year < max(solveyears))
                     and (next_year > int(caseSwitches['GSw_SkipAugurYear'])))
                    or (str(cur_year) in caseSwitches['run_osprey_years'].split('_'))
                ):
                    OPATH.writelines(
                        "python Augur.py {} {} {}\n".format(next_year, cur_year, lstfile))
                    # Check to make sure Augur ran successfully; quit otherwise
                    OPATH.writelines(
                        writeerrorcheck(os.path.join(
                            "ReEDS_Augur", "augur_data", "ReEDS_Augur_{}.gdx".format(cur_year))))

                #since we are done with the previous solve file delete it
                if cur_year > min(solveyears):
                    #check to see if the most recent save file exists and if so, delete the previous restart file
                    write_delete_file(
                        checkfile=os.path.join("g00files", savefile + ".g00"),
                        deletefile=os.path.join("g00files", restartfile + '.g00'),
                        PATH=OPATH,
                    )
                #after solving, the restart file is now the save file
                restartfile=savefile


    #############################
    # -- INTERTEMPORAL SETUP --
    #############################

        if caseSwitches['timetype']=='int':
            #beginning year is passed to augurbatch
            begyear = min(solveyears)
            #first save file from d_solveprep is just the case name
            savefile = lstfile
            #if this is the first iteration
            if startiter == 0:
                #restart file becomes the previous calls save file
                restartfile=savefile
                #if this is not the first iteration...
            if startiter > 0:
                #restart file is now the case name plus the iteration number
                restartfile = lstfile+"_"+startiter

            #per the instructions, iterations are
            #the number of iterations after the first solve
            niter = niter+1

            #for the number of iterations we have...
            for i in range(startiter,niter):
                #make an indicator in the batch file for what iteration is being solved
                OPATH.writelines('\n' + comment  + ' \n')
                OPATH.writelines(comment + " Iteration: " + str(i)  + ' \n')
                OPATH.writelines(comment + ' \n \n')
                #call the intertemporal solve
                savefile = lstfile+"_"+str(i)

                if i==0:
                    #check to see if the restart file exists
                    #only need to do this with the zeroth iteration
                    #as the other checks will all be after the solves
                    OPATH.writelines(writeerrorcheck(os.path.join("g00files",restartfile + ".g*")))

                OPATH.writelines(
                    "gams d_solveallyears.gms o="+os.path.join("lstfiles",lstfile + "_" + str(i) + ".lst")
                    +" r="+os.path.join("g00files",restartfile)
                    + " gdxcompress=1 xs="+os.path.join("g00files",savefile) + toLogGamsString
                    + " --niter=" + str(i) + " --case=" + lstfile
                    + " --demand=" + caseSwitches['demand']  + ' \n')

                #check to see if the save file exists
                OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))

                #start threads for cc/curt
                #no need to run cc curt scripts for final iteration
                if i < niter-1:
                    #batch out calls to augurbatch
                    OPATH.writelines(
                        "python augurbatch.py " + lstfile + " " + str(ccworkers) + " "
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
                    #merge all the resulting gdx files
                    #the output file will be for the next iteration
                    nextiter = i+1
                    gdxmergedfile = os.path.join(
                        "ReEDS_Augur","augur_data","ReEDS_Augur_merged_" + str(nextiter))
                    OPATH.writelines(
                        "gdxmerge "+os.path.join("ReEDS_Augur","augur_data","ReEDS_Augur*")
                        + " output=" + gdxmergedfile  + ' \n')
                    #check to make sure previous calls were successful
                    OPATH.writelines(writeerrorcheck(gdxmergedfile+".gdx"))

                #restart file becomes the previous save file
                restartfile=savefile

            if caseSwitches['GSw_ValStr'] != '0':
                OPATH.writelines( "python valuestreams.py" + '\n')


    #####################
    # -- WINDOW SETUP --
    #####################

        if caseSwitches['timetype']=='win':
            #load in the windows
            win_in = list(csv.reader(open(
                os.path.join(
                    InputDir,"inputs","userinput",
                    "windows_{}.csv".format(caseSwitches['windows_suffix'])),
                'r'), delimiter=","))

            restartfile=lstfile

            #for windows indicated in the csv file
            for win in win_in[1:]:

                #beginning year is the first column (start)
                begyear = win[1]
                #end year is the second column (end)
                endyear = win[2]
                #for the number of iterations we have...
                for i in range(startiter,niter):
                    OPATH.writelines(' \n' + comment + ' \n')
                    OPATH.writelines(comment + " Window: " + str(win)  + ' \n')
                    OPATH.writelines(comment + " Iteration: " + str(i)  + ' \n')
                    OPATH.writelines(comment  + ' \n')

                    #call the window solve
                    savefile = lstfile+"_"+str(i)
                    #check to see if the save file exists
                    OPATH.writelines(writeerrorcheck(os.path.join("g00files",restartfile + ".g*")))
                    #solve via the window solve file
                    OPATH.writelines(
                        "gams d_solvewindow.gms o=" + os.path.join("lstfiles",lstfile + "_" + str(i) + ".lst")
                        +" r=" + os.path.join("g00files",restartfile)
                        + " gdxcompress=1 xs=g00files\\"+savefile + toLogGamsString + " --niter=" + str(i)
                        + " --maxiter=" + str(niter-1) + " --case=" + lstfile + " --window=" + win[0] + ' \n')
                    #start threads for cc/curt
                    OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))
                    OPATH.writelines(
                        "python augurbatch.py " + lstfile + " " + str(ccworkers) + " "
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
                    #merge all the resulting r2_in gdx files
                    #the output file will be for the next iteration
                    nextiter = i+1
                    #create names for then merge the curt and cc gdx files
                    gdxmergedfile = os.path.join(
                        "ReEDS_Augur","augur_data","ReEDS_Augur_merged_" + str(nextiter))
                    OPATH.writelines(
                        "gdxmerge " + os.path.join("ReEDS_Augur","augur_data","ReEDS_Augur*")
                        + " output=" + gdxmergedfile  + ' \n')
                    #check to make sure previous calls were successful
                    OPATH.writelines(writeerrorcheck(gdxmergedfile+".gdx"))
                    restartfile=savefile
                if caseSwitches['GSw_ValStr'] != '0':
                    OPATH.writelines( "python valuestreams.py" + '\n')
        #create reporting files
        OPATH.writelines(
            "gams e_report.gms o="+os.path.join("lstfiles","report_" + lstfile + ".lst")
            + (' license=gamslice.txt' if hpc else '')
            + ' r=' +os.path.join("g00files",restartfile) + toLogGamsString + " --fname=" + lstfile
            + ' --GSw_calc_powfrac={} \n'.format(caseSwitches['GSw_calc_powfrac']))
        OPATH.writelines('python {t}\n'.format(t=ticker))
        OPATH.writelines(
            "gams e_report_dump.gms o="+os.path.join("lstfiles","report_dump_" + lstfile + ".lst")
            + (' license=gamslice.txt' if hpc else '')
            + toLogGamsString + " --fname=" + lstfile + ' \n')
        OPATH.writelines('python {t}\n\n'.format(t=ticker))

        ### Run the retail rate module
        OPATH.writelines(
            f"python {os.path.join(os.getcwd(),'postprocessing','retail_rate_module','retail_rate_calculations.py')} {lstfile} -p\n\n"
        )

        ## Run air-quality and health damages calculation script
        if int(caseSwitches['GSw_HealthDamages']):
            OPATH.writelines(
                f"python {os.path.join(os.getcwd(),'postprocessing','air_quality','health_damage_calculations.py')} {casedir}\n\n"
            )

        ## ReEDS_to_rev processing
        if caseSwitches['reeds_to_rev'] == '1':
            OPATH.writelines('cd {} \n\n'.format(InputDir))
            OPATH.writelines(f'python hourlize/reeds_to_rev.py {InputDir} {casedir} "cost" -r\n')

        if caseSwitches['land_use_analysis'] == '1':
            # run the land-used characterization module
            OPATH.writelines(
                f"python {os.path.join(os.getcwd(),'postprocessing','land_use','land_use_analysis.py')} {casedir}\n\n"
            )

        ## Run Bokeh
        bokehdir = os.path.join(os.getcwd(),"postprocessing","bokehpivot","reports")
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(os.getcwd(),"runs",lstfile) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","standard_report_reduced.py") + ' "html,excel,csv" one '
            + os.path.join(os.getcwd(),"runs",lstfile,"outputs","reeds-report-reduced") + ' no\n')
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(os.getcwd(),"runs",lstfile) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","standard_report_expanded.py") + ' "html,excel" one '
            + os.path.join(os.getcwd(),"runs",lstfile,"outputs","reeds-report") + ' no\n\n')
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(os.getcwd(),"runs",lstfile) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","state_report.py") + ' "csv" one '
            + os.path.join(os.getcwd(),"runs",lstfile,"outputs","reeds-report-state") + ' no\n\n')
        OPATH.writelines('python postprocessing/vizit/vizit_prep.py ' + '"{}"'.format(os.path.join(casedir,'outputs')) + '\n')

        # make script to unload all data to .gdx file
        command = (
            'gams dump_alldata.gms'
            + ' o='+os.path.join('lstfiles','dump_alldata_{}_{}.lst'.format(BatchName,case))
            + ' r='+os.path.join('g00files','{}_{}_{}'.format(BatchName,case,solveyears[-1])))
        with open(os.path.join(casedir,'dump_alldata'+ext),'w+') as datadumper:
            datadumper.writelines('cd ' + os.path.join(os.getcwd(),'runs','{}_{}'.format(BatchName,case)) + '\n')
            datadumper.writelines(command)
        if int(caseSwitches['dump_alldata']):
            OPATH.writelines(command+'\n')

        if int(caseSwitches['delete_big_files']):
            for file in [
                os.path.join(inputs_case, 'recf.h5'),
                os.path.join(inputs_case, 'load.h5'),
                os.path.join(inputs_case, 'csp_profiles.h5'),
                os.path.join(inputs_case, 'can_trade_8760.h5'),
                os.path.join(inputs_case, 'rsc_combined.csv'),
                ### Uncomment the following two lines to delete the .g00 files
                # os.path.join('g00files', restartfile + '.g00'),
                # os.path.join('g00files', restartfile.rstrip(str(cur_year)+'_') + '.g00'),
            ]:
                write_delete_file(checkfile=file, deletefile=file, PATH=OPATH)
            OPATH.writelines('')

        if int(caseSwitches['transmission_maps']):
            OPATH.writelines('cd {}\n'.format(InputDir))
            OPATH.writelines('python postprocessing/transmission_maps.py -c {} -y {}\n'.format(
                casedir, (
                    solveyears[-1]
                    if int(caseSwitches['transmission_maps']) > int(solveyears[-1])
                    else caseSwitches['transmission_maps'])
            ))

        ##############################
        # Call the Created Batch File
        ##############################

        OPATH.close()

        #if you're not running on eagle or AWS..
        if (not hpc) & (not int(caseSwitches['AWS'])):
            # start the command prompt similar to the sequential solve
            # - waiting for it to finish before starting a new thread
            if os.name!='posix':
                if int(caseSwitches['keep_run_terminal']) == 1:
                    terminal_keep_flag = ' /k '
                else:
                    terminal_keep_flag = ' /c '
                os.system('start /wait cmd' + terminal_keep_flag + os.path.join(casedir, 'call_' + lstfile + ext))
            if os.name=='posix':
                print("Starting the run for case " + lstfile)
                #give execution rights to the shell script
                os.chmod(os.path.join(casedir, 'call_' + lstfile + ext), 0o777)
                #open it up - note the in/out/err will be written to the shellscript parameter
                if verbose:
                    shellscript = subprocess.Popen(
                        [os.path.join(casedir, 'call_' + lstfile + ext)], shell=True)
                else:
                    shellscript = subprocess.Popen(
                        [os.path.join(casedir, 'call_' + lstfile + ext) + " >/dev/null"],
                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, shell=True)
                #wait for it to finish before killing the thread
                shellscript.wait()

        elif hpc:
            # create a copy of srun_template in casedir as {lstfile}.sh
            if caseSwitches['timetype']=="int":
                shutil.copy("srun_template_int.sh", os.path.join(casedir, lstfile+".sh"))
            else:
                shutil.copy("srun_template.sh", os.path.join(casedir, lstfile+".sh"))
            with open(os.path.join(casedir, lstfile+".sh"), 'a') as SPATH:
                #add the name for easy tracking of the case
                SPATH.writelines("\n#SBATCH --job-name=" + lstfile + "\n\n")
                #add the call to the sh file created throughout this function
                SPATH.writelines("sh " + os.path.join(casedir, 'call_' + lstfile + ext))
            #close the file
            SPATH.close()
            #call that file
            batchcom = "sbatch " + os.path.join(casedir, lstfile + ".sh")
            subprocess.Popen(batchcom.split())

        elif int(caseSwitches['AWS']):
            print("Starting the run for case " + lstfile)
            #give execution rights to the shell script
            os.chmod(os.path.join(casedir, 'call_' + lstfile + ext), 0o777)
            #issue a nohup (no hangup) command and direct output to 
            # case-specific txt files in the root of the repository
            shellscript = subprocess.Popen(
                ['nohup ' + os.path.join(casedir, 'call_' + lstfile + ext) + " > " +os.path.join(casedir,lstfile+ ".txt") ], 
                 stdin=open(os.path.join(casedir,lstfile+"_in.txt"),'w'), 
                 stdout=open(os.path.join(casedir,lstfile+"_out.txt"),'w'), 
                 stderr=open(os.path.join(casedir,lstfile+"_err.log"),'w'),
                 shell=True,preexec_fn=os.setpgrp)
            # wait for it to finish before killing the thread
            shellscript.wait()

        ### Record the ending time
        now = datetime.isoformat(datetime.now())
        try:
            with open(os.path.join(casedir,'meta.csv'), 'a') as METAFILE:
                METAFILE.writelines('0,end,,{},\n'.format(now))
        except:
            print('meta.csv not found or not writeable')
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--BatchName', '-b', type=str, default='',
                        help='Name for batch of runs')
    parser.add_argument('--cases_suffix', '-c', type=str, default='',
                        help='Suffix for cases CSV file')
    parser.add_argument('--simult_runs', '-r', type=int, default=0,
                        help='Number of simultaneous runs. If negative, run all simultaneously.')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Indicate whether to print log to terminal')
    parser.add_argument('-l', '--forcelocal', action='store_true',
                        help='Force model to run locally instead of submitting a slurm job')
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

    args=vars(parser.parse_args())
    #gather user inputs before calling GAMS programs
    envVar = setupEnvironment(**args)

    print(" ")

    if not os.path.exists("runs"): os.mkdir("runs")

    # threads are created which will handle each case individually
    createmodelthreads(envVar)

if __name__ == '__main__':
    main()
