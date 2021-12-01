# import necessary packages
import os
import sys
import queue
import threading
import time
import shutil
import csv
import pandas as pd
import subprocess
from datetime import datetime
import argparse

from builtins import input

sys.path.insert(0, 'input_processing') # add the dir to the path for importing modules

import calc_financial_inputs as cFuncs


def setupEnvironment(BatchName=False, cases_suffix=False, simult_runs=0):
    #inputs (machines.csv and cases.csv) are located where the python script is booted from
    #this by default is .ssh\ReEDS\USREP\batch
    InputDir = os.getcwd()

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

    df_cases = pd.read_csv('cases.csv', dtype=object, index_col=0)
    cases_filename = 'cases.csv'

    #If we have a case suffix, use cases_[suffix].csv for cases.
    if cases_suffix != '':
        df_cases = df_cases[['Description', 'Default Value']]
        cases_filename = 'cases_' + cases_suffix + '.csv'
        df_cases_suf = pd.read_csv(cases_filename, dtype=object, index_col=0)

        #First use 'Default Value' from cases_[suffix].csv to fill missing switches
        #Later, we will also use 'Default Value' from cases.csv to fill any remaining holes.
        if 'Default Value' in df_cases_suf.columns:
            case_i = df_cases_suf.columns.get_loc('Default Value') + 1
            casenames = df_cases_suf.columns[case_i:].tolist()
            for case in casenames:
                df_cases_suf[case] = df_cases_suf[case].fillna(df_cases_suf['Default Value'])
        df_cases_suf.drop(['Default Value','Description'], axis='columns',inplace=True, errors='ignore')
        df_cases = df_cases.join(df_cases_suf, how='outer')

    # initiate the empty lists which will be filled with info from cases
    caseList = []
    caseSwitches = [] #list of dicts, one dict for each case
    casenames = df_cases.columns[2:].tolist()

    for case in casenames:
        #Fill any missing switches with the defaults in cases.csv
        df_cases[case] = df_cases[case].fillna(df_cases['Default Value'])
        # ignore cases with ignore flag
        if int(df_cases.loc['ignore',case]) == 1:
            continue
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

    df_cases.drop(['Description','Default Value'], axis='columns',inplace=True)
    timetype = df_cases.loc['timetype'].tolist()
    yearset_suffix = df_cases.loc['yearset_suffix'].tolist()
    endyearset = df_cases.loc['endyear'].tolist()
    demandset = df_cases.loc['demand'].tolist()
    distpvset = df_cases.loc['distpvscen'].tolist()
    cspset = df_cases.loc['calc_csp_cc'].tolist()
    drset = df_cases.loc['GSw_DR'].tolist()
    marg_vre_set = df_cases.loc['marg_vre_mw'].tolist()
    marg_stor_set = df_cases.loc['marg_stor_mw'].tolist()
    marg_dr_set = df_cases.loc['marg_dr_mw'].tolist()
    hpcset = df_cases.loc['hpc'].tolist()
    GAMSDIR = df_cases.loc['GAMSDIR'].tolist()

    if hpcset.count("1")>0:
        if not os.path.exists(os.path.join("shfiles")): os.mkdir(os.path.join("shfiles"))
        #need to use os.path.join here or the unicode separation characters
        #will be included in the call to d5_mergevariability.r when writing to call_'case'.sh
        GAMSDIR = [os.path.join("/Applications","GAMS24.7","GAMS24.7","sysdir") for x in GAMSDIR]


    print(" ")
    print(" ")
    print("The GAMS directory is required to be specified for the intertemporal and window cases")
    print("The assignment is in the cases.csv file as the GAMSDIR option")
    print("GAMS directory: " + str(GAMSDIR[0]))
    print(" ")
    print(" ")

    print("Cases being run:")
    for case in casenames:
        print(case)
    print(" ")

    reschoice = 0
    startiter = 0
    ccworkers = 5
    niter = 5
    if len(caseList)==1:
        print("Only one case is to be run, therefore only one thread is needed")
        WORKERS = 1
    elif simult_runs > 0:
        WORKERS = simult_runs
        print(WORKERS)
    else:
        WORKERS = int(input('Number of simultaneous runs [integer]: '))

    print("")

    if 'int' in timetype or 'win' in timetype:
        ccworkers = int(input('Number of simultaneous CC/Curt runs [integer]: '))
        print("")
        print("The number of iterations defines the number of combinations of")
        print(" solving the model and computing capacity credit and curtailment")
        print(" Note this does not include the initial solve")
        print("")
        niter = int(input('How many iterations between the model and CC/Curt scripts: '))
#        reschoice = int(input('Do you want to restart from a previous convergence attempt (0=no, 1=yes): '))

        if reschoice==1:
            startiter = int(input('Iteration to start from (recall it starts at zero): '))


    envVar = {
        'WORKERS': WORKERS,
        'ccworkers': ccworkers,
        'casenames': casenames,
        'BatchName': BatchName,
        'GAMSDIR': GAMSDIR,
        'caseList': caseList,
        'caseSwitches': caseSwitches,
        'timetype' : timetype,
        'yearset_suffix' : yearset_suffix,
        'InputDir' : InputDir,
        'niter' : niter,
        'endyearset' : endyearset,
        'startiter' : startiter,
        'demandset' : demandset,
        'distpvset' : distpvset,
        'cspset' : cspset,
        'drset' : drset,
        'marg_vre_set' : marg_vre_set,
        'marg_stor_set' : marg_stor_set,
        'marg_dr_set' : marg_dr_set,
        'hpcset' : hpcset,
        'cases_filename': cases_filename,
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
                GAMSDir=ThreadInit['GAMSDIR'],
                options=ThreadInit['scen'],
                caseSwitches=ThreadInit['caseSwitches'],
                lstfile=ThreadInit['lstfile'],
                niter=ThreadInit['niter'],
                timetype=ThreadInit['timetype'],
                yearset_suffix=ThreadInit['yearset_suffix'],
                InputDir=ThreadInit['InputDir'],
                endyear=ThreadInit['endyear'],
                ccworkers=ThreadInit['ccworkers'],
                startiter=ThreadInit['startiter'],
                demandsetting=ThreadInit['demandsetting'],
                distpv=ThreadInit['distpv'],
                csp=ThreadInit['csp'],
                dr=ThreadInit['dr'],
                marg_vre=ThreadInit['marg_vre'],
                marg_stor=ThreadInit['marg_stor'],
                marg_dr=ThreadInit['marg_dr'],
                batch=ThreadInit['BatchName'],
                case=ThreadInit['casename'],
                hpc=ThreadInit['hpc'],
                cases_filename=ThreadInit['cases_filename'],
            )
            print(ThreadInit['lstfile'] + " has finished \n")
            q.task_done()


    threads = []

    for i in range(num_worker_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for i in range(len(envVar['caseList'])):
        q.put({'GAMSDIR' : envVar['GAMSDIR'][i],
               'scen': envVar['caseList'][i],
               'caseSwitches': envVar['caseSwitches'][i],
               'lstfile':envVar['BatchName']+'_'+envVar['casenames'][i],
               'niter':envVar['niter'],
               'timetype':envVar['timetype'][i],
               'yearset_suffix':envVar['yearset_suffix'][i],
               'InputDir':envVar['InputDir'],
               'endyear':envVar['endyearset'][i],
               'ccworkers':envVar['ccworkers'],
               'startiter':envVar['startiter'],
               'demandsetting':envVar['demandset'][i],
               'distpv':envVar['distpvset'][i],
               'csp':envVar['cspset'][i],
               'dr':envVar['drset'][i],
               'marg_vre':envVar['marg_vre_set'][i],
               'marg_stor':envVar['marg_stor_set'][i],
               'marg_dr':envVar['marg_dr_set'][i],
               'BatchName':envVar['BatchName'],
               'casename':envVar['casenames'][i],
               'hpc':envVar['hpcset'][i],
               'cases_filename':envVar['cases_filename'],
               })

    # block until all tasks are done
    q.join()

    # stop workers
    for i in range(num_worker_threads):
        q.put(None)

    for t in threads:
        t.join()


def writeerrorcheck(checkfile):
    if os.name!='posix':
        return '\nif not exist '+ checkfile + ' (\n echo file ' + checkfile + ' missing \n goto:eof \n) \n \n'
    else:
        return '\nif [ ! -f ' + checkfile + ' ]; then \n      exit 0\nfi\n\n'

def runModel(GAMSDir,options,caseSwitches,lstfile,niter,timetype,yearset_suffix,InputDir,endyear,
             ccworkers,startiter,demandsetting,distpv,csp,dr,marg_vre,marg_stor,marg_dr,batch,case,hpc, cases_filename):


    casedir = os.path.join(InputDir,"runs",lstfile)
    inputs_case = os.path.join(casedir,"inputs_case")

    if os.path.exists(os.path.join("runs",lstfile)):
        print("Caution, case " + lstfile + " already exists in runs \n")

    #set up case-specific directory structure
    os.makedirs(os.path.join("runs",lstfile), exist_ok=True)
    os.makedirs(os.path.join("runs",lstfile,"g00files"), exist_ok=True)
    os.makedirs(os.path.join("runs",lstfile,"lstfiles"), exist_ok=True)
    os.makedirs(os.path.join("runs",lstfile,"outputs"), exist_ok=True)
    os.makedirs(inputs_case, exist_ok=True)

    #%% Record some metadata about this run
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

    finance_dict = cFuncs.calc_financial_inputs(batch,case,caseSwitches)
    ### Get numclass from the max value in ivt
    caseSwitches['numclass'] = finance_dict['numclass']
    options += ' --numclass={}'.format(caseSwitches['numclass'])
    ### Get numbins from the max of individual technology bins
    caseSwitches['numbins'] = max(
        int(caseSwitches['numbins_windons']),
        int(caseSwitches['numbins_windofs']),
        int(caseSwitches['numbins_upv']),
        15)
    options += ' --numbins={}'.format(caseSwitches['numbins'])

    yearset_path = os.path.join('inputs','userinput','modeledyears_%s.csv' % yearset_suffix)
    yearset_augur = os.path.join('inputs_case','modeledyears_%s.csv' % yearset_suffix)
    solveyears=list(csv.reader(open(os.path.join(InputDir,yearset_path), 'r'), delimiter=","))[0]
    solveyears = [int(y) for y in solveyears if y <= endyear]
    toLogGamsString = ' logOption=4 logFile=gamslog.txt appendLog=1 '
    waterswitch = str(caseSwitches['GSw_WaterMain'])

    ds = '/' if os.name == 'posix' else '\\'

    options += (
        ' --basedir=' + InputDir + ds
        + ' --casedir=' + casedir
        + ' --yearset=modeledyears_%s.csv' % yearset_suffix)

    dir_src = InputDir

    shutil.copy2(os.path.join(dir_src, cases_filename), casedir)

    with open('filesforbatch.csv', 'r') as f:
        reader = csv.reader(f, delimiter = ',')
        for row in reader:
            filename = row[0]
            if filename[:6]=='inputs':
                dir_dst = inputs_case
            else:
                dir_dst = casedir
            src_file = os.path.join(InputDir, filename)
            if os.path.exists(src_file):
                shutil.copy(src_file, dir_dst)

    if caseSwitches['GSw_ValStr'] != '0':
        addMPSToOpt(caseSwitches['GSw_gopt'], casedir)

    # Copy special-case files for individual sites
    if int(caseSwitches['GSw_IndividualSites']):
        shutil.copy(os.path.join(InputDir,'inputs','rsmap.csv'),
                    inputs_case)
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ons_prescribed_builds_site_{}.csv'.format(caseSwitches['GSw_SitingWindOns'])),
                    os.path.join(inputs_case,'wind-ons_prescribed_builds.csv'))
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ofs_prescribed_builds_site_{}.csv'.format(caseSwitches['GSw_SitingWindOfs'])),
                    os.path.join(inputs_case,'wind-ofs_prescribed_builds.csv'))
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ons_exog_cap_site_{}.csv'.format(caseSwitches['GSw_SitingWindOns'])),
                    os.path.join(inputs_case,'wind-ons_exog_cap.csv'))
    else:
        shutil.copy(os.path.join(InputDir,'inputs','rsmap_sreg.csv'),
                    os.path.join(inputs_case,'rsmap.csv'))
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ons_prescribed_builds_sreg_{}.csv'.format(caseSwitches['GSw_SitingWindOns'])),
                    os.path.join(inputs_case,'wind-ons_prescribed_builds.csv'))
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ofs_prescribed_builds_sreg_{}.csv'.format(caseSwitches['GSw_SitingWindOfs'])),
                    os.path.join(inputs_case,'wind-ofs_prescribed_builds.csv'))
        shutil.copy(os.path.join(InputDir,'inputs','capacitydata','wind-ons_exog_cap_sreg_{}.csv'.format(caseSwitches['GSw_SitingWindOns'])),
                    os.path.join(inputs_case,'wind-ons_exog_cap.csv'))

    ### Copy run-specific files
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

    #copy over files from the user input folder
    userinputs = os.listdir(os.path.join(InputDir,"inputs","userinput"))

    for file_name in userinputs:
        full_file_name = os.path.join(InputDir,"inputs","userinput", file_name)
        # ivt is now a special case written in calc_financial_inputs, so skip it here
        if (os.path.isfile(full_file_name) and (file_name != 'ivt.csv')):
            shutil.copy(full_file_name, inputs_case)

    #copy over the ReEDS_Augur folder
    shutil.copytree(os.path.join(InputDir,"ReEDS_Augur"),os.path.join(casedir,'ReEDS_Augur'))

    #make the augur_data folder
    os.mkdir(os.path.join(casedir,'ReEDS_Augur','augur_data'))

    #Replace files according to 'file_replacements' in cases. Ignore quotes in input text.
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

        if hpc=="1":

            OPATH.writelines(comment + " setting up nodal environment for run \n")
            OPATH.writelines(". $HOME/.bashrc \n")
            OPATH.writelines("module purge \n")
            OPATH.writelines("module load conda \n")
            OPATH.writelines("conda activate reeds \n")
            OPATH.writelines("module load gams \n")
            OPATH.writelines('export R_LIBS_USER="$HOME/rlib" \n\n\n')

        OPATH.writelines(
            "gams createmodel.gms gdxcompress=1 xs="+os.path.join("g00files",lstfile)
            + " o="+os.path.join("lstfiles","1_Inputs.lst") + options + " " + toLogGamsString + '\n')
        OPATH.writelines('python {t}\n'.format(t=ticker))
        restartfile = lstfile
        OPATH.writelines(writeerrorcheck(os.path.join('g00files',restartfile + '.g*')))


    #############################
    # -- SEQUENTIAL SETUP --
    #############################

        if timetype=='seq':
            #loop over solve years
            for i in range(len(solveyears)):

                #current year is the value in solveyears
                cur_year = solveyears[i]
                if cur_year < max(solveyears):
                    #next year becomes the next item in the solveyears vector
                    next_year = solveyears[i+1]
                #make an indicator in the batch file for what year is being solved
                OPATH.writelines('\n' + comment + ' \n')
                OPATH.writelines(comment + " Year: " + str(cur_year)  + ' \n')
                OPATH.writelines(comment  + ' \n')

                #savefile is the lstfile plus the current name
                savefile = lstfile+"_"+str(cur_year)

                #solve one year
                OPATH.writelines(
                    "gams d_solveoneyear.gms"
                    + (" license=gamslice.txt" if int(caseSwitches['hpc']) else '')
                    + " o="+os.path.join("lstfiles",savefile+".lst")
                    + " r="+os.path.join("g00files",restartfile)
                    + " gdxcompress=1 xs=" + os.path.join("g00files",savefile) + toLogGamsString
                    + " --case=" + lstfile
                    + " --cur_year=" + str(cur_year) + " --next_year=" + str(next_year)
                    + " --GSW_SkipAugurYear={}".format(caseSwitches['GSw_SkipAugurYear'])
                    + '\n')
                OPATH.writelines('python {t} --year={y}\n'.format(t=ticker, y=cur_year))

                if caseSwitches['GSw_ValStr'] != '0':
                    OPATH.writelines(
                        'gams valuestreams.gms o='+os.path.join("lstfiles",'valuestreams_' + savefile + '.lst')
                        + ' r='+os.path.join("g00files",restartfile) + toLogGamsString + '\n')

                #check to see if the restart file exists
                OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))

                # Run Augur if it not the final solve year and if not skipping Augur
                if (cur_year < max(solveyears)) and (next_year > int(caseSwitches['GSw_SkipAugurYear'])):
                    OPATH.writelines(
                        "python Augur.py {} {} {}\n".format(next_year, cur_year, lstfile))
                    # Check to make sure Augur ran successfully; quit otherwise
                    OPATH.writelines(
                        writeerrorcheck(os.path.join(
                            "ReEDS_Augur", "augur_data", "ReEDS_Augur_{}.gdx".format(next_year))))

                #since we are done with the previous solve file delete it
                if cur_year > min(solveyears):
                    #check to see if the most recent save file exists and if so, delete the previous restart file
                    if os.name!='posix':
                        OPATH.writelines(
                            "if exist "+os.path.join("g00files",savefile+ ".g00")
                            + " (del "+os.path.join("g00files", restartfile + '.g00')+')\n' )
                    if os.name=='posix':
                        #'\nif [ ! -f ' + checkfile + ' ]; then \n      exit 0\nfi\n\n'
                        OPATH.writelines(
                            "if [ -f " + os.path.join("g00files",savefile+ ".g00") + " ]; "
                            + "then \n   rm "+os.path.join("g00files", restartfile + '.g00') +'\nfi\n\n' )
                #after solving, the restart file is now the save file
                restartfile=savefile


    #############################
    # -- INTERTEMPORAL SETUP --
    #############################

        if timetype=='int':
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
                    + " --niter=" + str(i) + " --case=" + lstfile + " --demand=" + demandsetting  + ' \n')

                #check to see if the save file exists
                OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))

                #start threads for cc/curt
                #no need to run cc curt scripts for final iteration
                if i < niter-1:
                    #batch out calls to augurbatch
                    OPATH.writelines(
                        "python augurbatch.py " + lstfile + " " + str(ccworkers) + " "
                        + yearset_augur + " " + savefile + " " + str(begyear) + " "
                        + str(endyear) + " " + distpv + " " + str(csp) + " " + str(dr) + " "
                        + str(timetype) + " " + str(waterswitch) + " " + str(i) + " "
                        + str(marg_vre) + " " + str(marg_dr) + " " + str(marg_stor) + " " + str(marg_dr) + " "
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
                OPATH.writelines(
                    'gams valuestreams.gms o='+os.path.join("lstfiles",'valuestreams_' + lstfile + '.lst')
                    + " r=" + os.path.join("runs",lstfile,'g00files',restartfile) + toLogGamsString + '\n')


    #####################
    # -- WINDOW SETUP --
    #####################

        if timetype=='win':
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
                        + str(endyear) + " " + distpv + " " + str(csp) + " " + str(dr) + " "
                        + str(timetype) + " " + str(waterswitch) + " " + str(i) + " "
                        + str(marg_vre) + " " + str(marg_dr) + " " + str(marg_stor) + " " + str(marg_dr) + " "
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
                    OPATH.writelines(
                        'gams valuestreams.gms o='
                        + os.path.join("lstfiles",'valuestreams_' + lstfile + '_' + str(begyear) + '.lst')
                        + ' r=' + os.path.join('g00files',restartfile) + toLogGamsString + '\n')

        #create reporting files
        OPATH.writelines(
            "gams e_report.gms o="+os.path.join("lstfiles","report_" + lstfile + ".lst")
            + ' r=' +os.path.join("g00files",restartfile) + toLogGamsString + " --fname=" + lstfile + ' \n')
        OPATH.writelines('python {t}\n'.format(t=ticker))
        OPATH.writelines("gams e_report_dump.gms " + toLogGamsString + " --fname=" + lstfile + ' \n')
        OPATH.writelines('python {t}\n\n'.format(t=ticker))

        ### Run the retail rate module
        if not int(caseSwitches['GSw_Hourly']):
            OPATH.writelines(
                'python {reeds}{ds}retail_rate_module{ds}retail_rate_calculations.py {case} -p\n\n'.format(
                    reeds=os.getcwd(), ds=ds, case=lstfile)
            )

        bokehdir = os.path.join(os.getcwd(),"bokehpivot","reports")
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(os.getcwd(),"runs",lstfile) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","standard_report_reduced.py") + " one "
            + os.path.join(os.getcwd(),"runs",lstfile,"outputs","reeds-report-reduced") + ' no\n')
        OPATH.writelines(
            'python ' + os.path.join(bokehdir,"interface_report_model.py") + ' "ReEDS 2.0" '
            + os.path.join(os.getcwd(),"runs",lstfile) + " all No none "
            + os.path.join(bokehdir,"templates","reeds2","standard_report_expanded.py") + " one "
            + os.path.join(os.getcwd(),"runs",lstfile,"outputs","reeds-report") + ' no\n\n')

        if caseSwitches['reeds_to_rev'] == '1':
            OPATH.writelines('cd {} \n\n'.format(InputDir))
            OPATH.writelines('python hourlize/reeds_to_rev.py {} "csp" "reference" "cost" -r\n'.format(casedir))
            OPATH.writelines('python hourlize/reeds_to_rev.py {} "dupv" "reference" "cost" -r\n'.format(casedir))
            OPATH.writelines('python hourlize/reeds_to_rev.py {} "upv" "{}" "cost" -b {} -r\n'.format(
                casedir, caseSwitches['GSw_SitingUPV'], caseSwitches['numbins_upv']))
            OPATH.writelines('python hourlize/reeds_to_rev.py {} "wind-ofs" "{}" "cost" -r\n'.format(
                casedir, caseSwitches['GSw_SitingWindOfs']))
            OPATH.writelines('python hourlize/reeds_to_rev.py {} "wind-ons" "{}" "cost" -r\n'.format(
                casedir, caseSwitches['GSw_SitingWindOns']))
        
        #make .bat file to unload alldata to .gdx file
        with open(os.path.join(casedir,'dump_alldata'+ext),'w+') as datadumper:
            datadumper.writelines('cd ' + os.path.join(os.getcwd(),'runs','{}_{}'.format(batch,case)) + '\n')
            datadumper.writelines(
                'gams dump_alldata.gms o='+os.path.join('lstfiles','dump_alldata_{}_{}.lst'.format(batch,case))
                + ' r='+os.path.join('g00files','{}_{}_{}'.format(batch,case,solveyears[-1])))

        ##############################
        # Call the Created Batch File
        ##############################

        OPATH.close()

        #if you're not running on eagle or AWS..
        if (hpc=="0") & (caseSwitches['AWS']=="0"):
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
                shellscript = subprocess.Popen(
                    [os.path.join(casedir, 'call_' + lstfile + ext) + " >/dev/null"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,shell=True)
                #wait for it to finish before killing the thread
                shellscript.wait()
        if hpc=="1":
                # create a copy of srun_template to shfiles as lstfile.sh
                if timetype!="int":
                    shutil.copy("srun_template.sh",os.path.join("shfiles",lstfile+".sh"))
                if timetype=="int":
                    shutil.copy("srun_template_int.sh",os.path.join("shfiles",lstfile+".sh"))
                with open(os.path.join("shfiles",lstfile+".sh"), 'a') as SPATH:
                    #add the name for easy tracking of the case
                    SPATH.writelines("\n#SBATCH --job-name=" + lstfile + "\n\n")
                    #add the call to the sh file created throughout this fntion
                    SPATH.writelines("sh " + os.path.join(casedir, 'call_' + lstfile + ext))
                #close the file
                SPATH.close()
                #call that file
                batchcom = "sbatch " + os.path.join("shfiles", lstfile +".sh")
                subprocess.Popen(batchcom.split())
        
        if caseSwitches['AWS'] == "1":

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
                 shell=True,preexec_fn=os.setpgrp)                #wait for it to finish before killing the thread
            shellscript.wait()

        ### Record the ending time
        now = datetime.isoformat(datetime.now())
        try:
            with open(os.path.join(casedir,'meta.csv'), 'a') as METAFILE:
                METAFILE.writelines('0,end,,{},\n'.format(now))
        except:
            print('meta.csv not found or not writeable')
            pass

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

def checkLDCpkl(filesrc,filedst,filename):
    if not os.path.exists(os.path.join(filedst, filename)):
        print("Copying file: " + filename)
        print("From: " + filesrc)
        print("To: " + filedst)
        print(" ")
        shutil.copy(os.path.join(filesrc, filename), os.path.join(filedst, filename))
    if not os.path.exists(os.path.join(filedst, filename)):
    	print("Error copying "+filename)
    	sys.exit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--BatchName',
                        '-b',
                        type=str,
                        default='',
                        help='Name for batch of runs'
                        )
    parser.add_argument('--cases_suffix',
                        '-c',
                        type=str,
                        default='',
                        help='Suffix for cases CSV file'
                        )
    parser.add_argument('--simult_runs',
                        '-r',
                        type=int,
                        default=0,
                        help='Number of simultaneous runs'
                        )
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
