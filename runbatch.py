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

from builtins import input

sys.path.insert(0, 'input_processing') # add the dir to the path for importing modules

import calc_financial_inputs as cFuncs


def setupEnvironment():
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

    print("\n\nSpecify the suffix for the cases_suffix.csv file")
    print("A blank input will default to the cases.csv file\n")

    cases_suffix = str(input('Case Suffix: '))

    df_cases = pd.read_csv('cases.csv', dtype=object, index_col=0)

    #If we have a case suffix, use cases_[suffix].csv for cases.
    if cases_suffix != '':
        df_cases = pd.read_csv('cases_' + cases_suffix + '.csv', dtype=object, index_col=0)
        df_cases = df_cases[['Description', 'Default Value']]
        df_cases_suf = pd.read_csv('cases_' + cases_suffix + '.csv', dtype=object, index_col=0)

        #First use 'Default Value' from cases_[suffix].csv to fill missing switches
        #Later, we will also use 'Default Value' from cases.csv to fill any remaining holes.
        if 'Default Value' in df_cases_suf.columns:
            case_i = df_cases_suf.columns.get_loc('Default Value') + 1
            casenames = df_cases_suf.columns[case_i:].tolist()
            for case in casenames:
                df_cases_suf[case] = df_cases_suf[case].fillna(df_cases_suf['Default Value'])

        df_cases_suf.drop(['Default Value','Description'], axis='columns',inplace=True, errors='ignore')
        df_cases = df_cases.join(df_cases_suf, how='left')

    # initiate the empty lists which will be filled with info from cases
    caseList = []
    caseSwitches = [] #list of dicts, one dict for each case
    casenames = df_cases.columns[2:].tolist()

    for case in casenames:
        #Fill any missing switches with the defaults in cases.csv
        df_cases[case] = df_cases[case].fillna(df_cases['Default Value'])
        shcom = ' --case=' + BatchName + "_" + case
        for i,v in df_cases[case].iteritems():
            shcom = shcom + ' --' + i + '=' + v
        caseList.append(shcom)
        caseSwitches.append(df_cases[case].to_dict())


    df_cases.drop(['Description','Default Value'], axis='columns',inplace=True)
    timetype = df_cases.loc['timetype'].tolist()
    yearset_suffix = df_cases.loc['yearset_suffix'].tolist()
    endyearset = df_cases.loc['endyear'].tolist()
    demandset = df_cases.loc['demand'].tolist()
    ldcgdxset = df_cases.loc['HourlyStaticFileSwitch'].tolist()
    distpvset = df_cases.loc['distpvscen'].tolist()
    cspset = df_cases.loc['calc_csp_cc'].tolist()
    GAMSDIR = df_cases.loc['GAMSDIR'].tolist()


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

    
    return {'WORKERS': WORKERS,
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
            'ldcgdxset' : ldcgdxset,
            'distpvset' : distpvset,
            'cspset' : cspset
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
            runModel(ThreadInit['GAMSDIR'],
                     ThreadInit['scen'],
                     ThreadInit['caseSwitches'],
                     ThreadInit['lstfile'],
                     ThreadInit['niter'],
                     ThreadInit['timetype'],
                     ThreadInit['yearset_suffix'],
                     ThreadInit['InputDir'],
                     ThreadInit['endyear'],
                     ThreadInit['ccworkers'],
                     ThreadInit['startiter'],
                     ThreadInit['demandsetting'],
                     ThreadInit['ldcgdx'],
                     ThreadInit['distpv'],
                     ThreadInit['csp'],
                     ThreadInit['BatchName'],
                     ThreadInit['casename'])
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
               'ldcgdx':envVar['ldcgdxset'][i],
               'distpv':envVar['distpvset'][i],
               'csp':envVar['cspset'][i],
               'BatchName':envVar['BatchName'],
               'casename':envVar['casenames'][i]
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
             ccworkers,startiter,demandsetting,ldcgdx,distpv,csp,batch,case):
    
    
    casedir = os.path.join(InputDir,"runs",lstfile)
    caseinputs = os.path.join(casedir,"inputs_case")

    if os.path.exists(os.path.join("runs",lstfile)): print("Caution, case " + lstfile + " already exists in runs \n")

    #set up case-specific directory structure
    if not os.path.exists(os.path.join("runs",lstfile)): os.mkdir(os.path.join("runs",lstfile))
    if not os.path.exists(os.path.join("runs",lstfile,"g00files")): os.mkdir(os.path.join("runs",lstfile,"g00files"))
    if not os.path.exists(os.path.join("runs",lstfile,"lstfiles")): os.mkdir(os.path.join("runs",lstfile,"lstfiles"))
    if not os.path.exists(os.path.join("runs",lstfile,"outputs")): os.mkdir(os.path.join("runs",lstfile,"outputs"))
    if not os.path.exists(os.path.join("runs",lstfile,"outputs","variabilityFiles")): os.mkdir(os.path.join("runs",lstfile,"outputs","variabilityFiles"))
    if not os.path.exists(caseinputs): os.mkdir(caseinputs)

    cFuncs.calc_financial_inputs(batch,case,caseSwitches)
    
    OutputDir = os.path.join(InputDir, "runs", lstfile)
    yearset_path = os.path.join('inputs','userinput','modeledyears_%s.csv' % yearset_suffix)
    yearset_reflow = os.path.join('inputs_case','modeledyears_%s.csv' % yearset_suffix)
    solveyears=list(csv.reader(open(os.path.join(InputDir,yearset_path), 'r'), delimiter=","))[0]
    solveyears = [y for y in solveyears if y <= endyear]
    toLogGamsString = ' logOption=4 logFile=gamslog.txt appendLog=1 '

    ds = "\\"
    
    if os.name=="posix":
        ds="/"
    
    options += ' --basedir=' + InputDir + ds + ' --casedir=' + casedir + ' --yearset=modeledyears_%s.csv' % yearset_suffix
    
    dir_src = InputDir

    with open('filesforbatch.csv', 'r') as f:
        reader = csv.reader(f, delimiter = ',')
        for row in reader:
            filename = row[0]
            if filename[:6]=='inputs':
                dir_dst = caseinputs
            else:
                dir_dst = casedir
            src_file = os.path.join(dir_src, filename)
            if os.path.exists(src_file):
                shutil.copy(src_file, dir_dst)

    if caseSwitches['GSw_ValStr'] != '0':
        addMPSToOpt(caseSwitches['GSw_gopt'], casedir, lstfile)

    #copy over files from the user input folder
    userinputs = os.listdir(os.path.join(InputDir,"inputs","userinput"))

    for file_name in userinputs:
        full_file_name = os.path.join(InputDir,"inputs","userinput", file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, caseinputs)

    ext = '.bat'
    comment = "::"

    if os.name=='posix':
        ext = '.sh'
        comment = "#"

    with open(os.path.join(OutputDir, 'call_' + lstfile + ext), 'w+') as OPATH:
        OPATH.writelines("cd " + casedir + '\n' + '\n' + '\n')

        OPATH.writelines("gams createmodel.gms gdxcompress=1 xs="+os.path.join("g00files",lstfile) + " o="+os.path.join("lstfiles","1_Inputs.lst") + options + " " + toLogGamsString + '\n')
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
                #make an indicator in the batch file for what year is being solved
                if os.name!='posix':
                    OPATH.writelines('\n' + comment  + ' \n')
                    OPATH.writelines(comment + " Year: " + str(cur_year)  + ' \n')
                    OPATH.writelines(comment  + ' \n')

                #savefile is the lstfile plus the current name
                savefile = lstfile+"_"+str(cur_year)
                #for subsequent solve years, only need to check to see if 
                #the gdx files from reflow (curt_out... and cc_out...) are 
                #created - note that the g00 file check is written below (before the call to reflow) 			
                if cur_year > min(solveyears):
                	OPATH.writelines(writeerrorcheck(os.path.join("outputs","variabilityFiles","curt_out_" + lstfile + "_" + str(cur_year) + ".gdx")))
                	OPATH.writelines(writeerrorcheck(os.path.join("outputs","variabilityFiles","cc_out_" + lstfile + "_" + str(cur_year) + ".gdx")))

                #solve one year
                OPATH.writelines("gams d_solveoneyear.gms o="+os.path.join("lstfiles",savefile+".lst") + " r="+os.path.join("g00files",restartfile) + " gdxcompress=1 xs=" + os.path.join("g00files",savefile) + toLogGamsString + " --case=" + lstfile + " --cur_year=" + str(cur_year)+'\n')
                #since we are done with the previous solve file delete it
                if cur_year > min(solveyears):
                    #check to see if the most recent save file exists and if so, delete the previous restart file
                    if os.name!='posix':                   
                        OPATH.writelines("if exist "+os.path.join("g00files",savefile+ ".g00") + "(del "+os.path.join("g00files", restartfile + '.g00')+')\n' )
                    if os.name=='posix':
                        #'\nif [ ! -f ' + checkfile + ' ]; then \n      exit 0\nfi\n\n'
                        OPATH.writelines("if [ -f " + os.path.join("g00files",savefile+ ".g00") + " ]; then \n   rm "+os.path.join("g00files", restartfile + '.g00') +'\nfi\n\n' )
                #after solving, the restart file is now the save file
                restartfile=savefile
                if caseSwitches['GSw_ValStr'] != '0':
                    OPATH.writelines('gams valuestreams.gms o='+os.path.join("lstfiles",'valuestreams_' + savefile + '.lst')+ ' r='+os.path.join("g00files",restartfile) + toLogGamsString +' --case=' + lstfile + '\n')
                
                #check to see if the restart file exists
                OPATH.writelines(writeerrorcheck(os.path.join("g00files",restartfile + ".g*")))

                #if it not the final solve year
                if cur_year < max(solveyears):
                    #next year becomes the next item in the solveyears vector
                    next_year = solveyears[i+1]
                    #call reflow for that save file
                    OPATH.writelines("gams d_callreflow.gms " + toLogGamsString + " --restartfile="+os.path.join("g00files",restartfile) + " --case=" + lstfile + " --cur_year=" + str(cur_year) + " --next_year="+str(next_year)+' --HourlyStaticFileSwitch='+ str(ldcgdx) + ' --DistPVSwitch='+ str(distpv) + ' --calc_csp_cc='+ str(csp) + ' --timetype=' + str(timetype) + '\n')
        
    #############################
    # -- INTERTEMPORAL SETUP -- 
    #############################

        if timetype=='int':
            #beginning year is passed to reflowbatch
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

                OPATH.writelines("gams d_solveallyears.gms o="+os.path.join("lstfiles",lstfile + "_" + str(i) + ".lst")+" r="+os.path.join("g00files",restartfile) + " gdxcompress=1 xs="+os.path.join("g00files",savefile) + toLogGamsString + " --niter=" + str(i) + " --case=" + lstfile + " --demand=" + demandsetting  + ' \n')

                #check to see if the save file exists
                OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))

                #start threads for cc/curt
                #no need to run cc curt scripts for final iteration
                if i < niter-1:
                    #batch out calls to reflowbatch
                    OPATH.writelines("python reflowbatch.py " + lstfile + " " + str(ccworkers) + " " + yearset_reflow + " " + savefile + " " + str(begyear) + " " + str(endyear)  + " " + ldcgdx + " " + distpv + " " + str(csp) + " " + str(timetype) + ' \n')
                    #merge all the resulting r2_in gdx files
                    #the output file will be for the next iteration
                    nextiter = i+1
                    #give names to the cc and curtailment gdx files that will then be merged
                    curt_gdxmergedfile = os.path.join("outputs","variabilityFiles","mergedcurt_" + lstfile + "_" + str(nextiter))            
                    cc_gdxmergedfile = os.path.join("outputs","variabilityFiles","mergedcc_" + lstfile + "_" + str(nextiter))            
                    OPATH.writelines("gdxmerge "+os.path.join("outputs","variabilityFiles","cc_out_"+lstfile+"*")+ " output=" + cc_gdxmergedfile  + ' \n')
                    OPATH.writelines("gdxmerge "+os.path.join("outputs","variabilityFiles","curt_out_"+lstfile+"*")+" output=" + curt_gdxmergedfile  + ' \n')
                    #check to make sure previous calls were successful
                    OPATH.writelines(writeerrorcheck(curt_gdxmergedfile+".gdx"))
                    OPATH.writelines(writeerrorcheck(cc_gdxmergedfile+".gdx"))

                    #do necessary conversions to make the merged gdx file readable into GAMS
                    OPATH.writelines("Rscript " + os.path.join(InputDir,"runs",lstfile,"d5_mergevariability.r") + " " + casedir + " '" + GAMSDir + "' " + curt_gdxmergedfile + ' ' + cc_gdxmergedfile + ' \n')

                #restart file becomes the previous save file
                restartfile=savefile
    
            if caseSwitches['GSw_ValStr'] != '0':
                OPATH.writelines('gams valuestreams.gms o='+os.path.join("lstfiles",'valuestreams_' + lstfile + '.lst') + " r=" + os.path.join("runs",lstfile,'g00files',restartfile) + toLogGamsString +' --case=' + lstfile + '\n')


    #####################
    # -- WINDOW SETUP -- 
    #####################

        if timetype=='win':
            #load in the windows
            win_in = list(csv.reader(open(os.path.join(InputDir,"inputs","userinput","windows.csv"), 'r'), delimiter=","))
        
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
                    OPATH.writelines("gams d_solvewindow.gms o="+os.path.join("lstfiles",lstfile + "_" + str(i) + ".lst")+" r="+os.path.join("g00files",restartfile) + " gdxcompress=1 xs=g00files\\"+savefile + toLogGamsString + " --niter=" + str(i) + " --maxiter=" + str(niter) + " --case=" + lstfile + " --window=" + win[0] + ' \n')
                    #start threads for cc/curt
                    OPATH.writelines(writeerrorcheck(os.path.join("g00files",savefile + ".g*")))
                    OPATH.writelines("python reflowbatch.py " + lstfile + " " + str(ccworkers) + " " + yearset_reflow + " " + savefile + " " + str(begyear) + " " + str(endyear)  + " " + ldcgdx + " " + distpv + " " + str(csp) + " " + str(timetype) + ' \n')
                    #merge all the resulting r2_in gdx files
                    #the output file will be for the next iteration
                    nextiter = i+1
                    #create names for then merge the curt and cc gdx files
                    curt_gdxmergedfile = os.path.join("outputs","variabilityFiles","mergedcurt_" + lstfile + "_" + str(nextiter))            
                    cc_gdxmergedfile = os.path.join("outputs","variabilityFiles","mergedcc_" + lstfile + "_" + str(nextiter))
                    OPATH.writelines("gdxmerge " + os.path.join("outputs","variabilityFiles","cc_out_"+lstfile+"*")+ " output=" + cc_gdxmergedfile  + ' \n')
                    OPATH.writelines("gdxmerge " + os.path.join("outputs","variabilityFiles","curt_out_"+lstfile+"*") + " output=" + curt_gdxmergedfile  + ' \n')
                    #check to make sure previous calls were successful
                    OPATH.writelines(writeerrorcheck(curt_gdxmergedfile+".gdx"))
                    OPATH.writelines(writeerrorcheck(cc_gdxmergedfile+".gdx"))
                    #do necessary conversions to make the merged gdx file readable into GAMS
                    OPATH.writelines("Rscript " + os.path.join(InputDir,"d5_mergevariability.r") + " " + casedir + " '" + GAMSDir + "' " + curt_gdxmergedfile + ' ' + cc_gdxmergedfile + ' \n')
                    restartfile=savefile
                if caseSwitches['GSw_ValStr'] != '0':
                    OPATH.writelines('gams valuestreams.gms o=' + os.path.join("lstfiles",'valuestreams_' + lstfile + '_' + str(begyear) + '.lst')+ ' r=' + os.path.join('g00files',restartfile) + toLogGamsString +' --case=' + lstfile + '\n')

        #create reporting files
        OPATH.writelines("gams e_report.gms o="+os.path.join("lstfiles","report_" + lstfile + ".lst") + ' r=' +os.path.join("g00files",restartfile) + toLogGamsString + " --fname=" + lstfile + ' \n')
        OPATH.writelines("gams e_report_dump.gms " + toLogGamsString + " --fname=" + lstfile + ' \n\n')

        bokehdir = os.path.join(os.getcwd(),"bokehpivot","reports")
        OPATH.writelines('python ' + os.path.join(bokehdir,"interface_report.py") + ' "ReEDS 2.0" ' + os.path.join(os.getcwd(),"runs",lstfile) + " all No none " + os.path.join(bokehdir,"templates","reeds2","standard_report_reduced.py") + " one " + os.path.join(os.getcwd(),"runs",lstfile,"outputs","reeds-report-reduced") + ' no\n')
        OPATH.writelines('python ' + os.path.join(bokehdir,"interface_report.py") + ' "ReEDS 2.0" ' + os.path.join(os.getcwd(),"runs",lstfile) + " all No none " + os.path.join(bokehdir,"templates","reeds2","standard_report_expanded.py") + " one " + os.path.join(os.getcwd(),"runs",lstfile,"outputs","reeds-report") + ' no\n')

        ##############################
        # Call the Created Batch File
        ##############################

        OPATH.close()
        #start the command prompt similar to the sequential solve - waiting for it to finish before starting a new thread
        if os.name!='posix':
            os.system('start /wait cmd /c ' + os.path.join(OutputDir, 'call_' + lstfile + ext))
        if os.name=='posix':
            print("Starting the run for case " + lstfile)
            #give execution rights to the shell script
            os.chmod(os.path.join(OutputDir, 'call_' + lstfile + ext), 0o777)
            #open it up - note the in/out/err will be written to the shellscript parameter
            shellscript = subprocess.Popen([os.path.join(OutputDir, 'call_' + lstfile + ext) + " >/dev/null"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,shell=True)
            #wait for it to finish before killing the thread
            shellscript.wait()

def addMPSToOpt(optFileNum, case_dir, case_name):
    #Modify the optfile to create an mps file.
    if int(optFileNum) == 1:
        origOptExt = 'opt'
    elif int(optFileNum) < 10:
        origOptExt = 'op' + optFileNum
    else:
        origOptExt = 'o' + optFileNum
    #Add writemps statement to opt file
    with open(case_dir + '/cplex.'+origOptExt, 'a') as file:
        file.write('\nwritemps ' + case_name + '.mps')

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



    #gather user inputs before calling GAMS programs
    envVar = setupEnvironment()
    
    print(" ")

    if not os.path.exists("runs"): os.mkdir("runs")
	
    # threads are created which will handle each case individually
    createmodelthreads(envVar)

if __name__ == '__main__':
    main()
