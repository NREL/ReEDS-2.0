## experimental runner for hourlize

# TODO: set up log for submission script? or just use terminal output?
# TODO: delete extra config entries
# TODO: naming convention for outputs (particularly other scenarios)
# TODO: multiple runs on a node? or use jade or torc for batching?
# TODO: add environment check

# TODO: explain casename approach, subsetvars 

# salloc --time=1:00:00 --partition=debug --account=2035study

## Imports
import os
import re
import json
import shutil
import argparse
import datetime
import pandas as pd
import sys
import traceback
import subprocess
from collections import OrderedDict

## Functions ####

# helper function replace {var} with the corresponding var for a given string,
# using either global variable or another config defintion. 
def string_formatter(var, config):
    # find string patterns to fill
    varout = var
    formatvars = re.findall("{.*?}", varout)
    newvals = {}
    for fv in formatvars:
        fvval = re.sub("{|}", "", fv)
        # to fill first check defined variables
        if fvval in globals():
            newval = globals()[fvval]
        # next check config definitions
        elif fvval in config.keys():
            newval = config[fvval]
        # if no definition is found raise error
        else:
            raise Exception(f"{fvval} is not a defined variable; check your config file.")
        newvals.update([(f"{fvval}", newval)])
    varout = varout.format(**newvals)    
    print(f"updated {var} --> {varout}")
    return varout

# function to auto-format {} variables in config with the appropriate variable
def config_string_formatter(config):
    # loop over config variables
    for var in config:
        if isinstance(config[var], str) and bool(re.search("{.*}", config[var])):
            config[var] = string_formatter(config[var], config)
        # special treatment for lists within a variable
        elif isinstance(config[var], list):
            varlist = config[var]
            for i in range(0, len(varlist)):
                if isinstance(varlist[i], str) and bool(re.search("{.*}", varlist[i])):
                    varlist[i] = string_formatter(varlist[i], config)
                    
# function to set up and submit each case to run 
def run_case(casename, case):
    case['casename'] = casename

    ## load relevant config files 
    # first load base config  
    if 'config_base' in case:
        configbase  = f"config_base_{case['config_base']}.json"
    else:
        configbase = "config_base_default.json" 
    cpathbase = os.path.join(hourlizepath, "configs", configbase)
    with open(cpathbase, "r") as f:
        config = json.load(f, object_pairs_hook=OrderedDict)

    # next load tech config 
    if 'config_tech' in case:
        configtech  = f"config_{case['tech']}_{case['config_tech']}.json"
    else:
        configtech = f"config_{case['tech']}_default.json" 
    cpathtech = os.path.join(hourlizepath, "configs", configtech)
    with open(cpathtech, "r") as f:
        configtech = json.load(f, object_pairs_hook=OrderedDict)
        
    # add batch prefix if specified
    if batch != "":
        batchcase = batch + "_" + case['casename']
    else:
        batchcase = case['casename']
    case['batchcase'] = batchcase
    
    ## setup output directory
    outpath = os.path.join(hourlizepath, 'out', batchcase) 
    if os.path.exists(outpath):
        if overwrite:
            shutil.rmtree(outpath)
        else:
            time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            os.rename(outpath, outpath + '-archive-' + time)
    os.makedirs(outpath, exist_ok=True)
    os.makedirs(os.path.join(outpath, 'inputs'), exist_ok=True)
    os.makedirs(os.path.join(outpath, 'results'), exist_ok=True)

    # add additional directory information to config
    case.update({"outpath":outpath, "reedspath": reedspath, "hourlizepath": hourlizepath})

    # combined config (add config for tech later after additional processing)
    configout = {**case, **config['resource'], **config['shared']}
    config_string_formatter(configout)
        
    ## get rev information
    if not os.path.exists(configout['rev_paths_file']):
        raise Exception(f"No 'rev_paths' file detected, check path in config: {configout['rev_paths_file']}")
    df_rev = pd.read_csv(configout['rev_paths_file'])

    # subset to relevant rev path
    df_rev_case = df_rev
    for var in configout['subsetvars']:
        if var not in case:
            raise Exception(f"{var} not specified in cases dictionary")
        df_rev_case = df_rev_case[(df_rev_case[var] == case[var])]

    # check to make sure a valid rev_paths option is around     
    if df_rev_case.shape[0] == 0:
        raise Exception(f"No rev_paths found; check definitions in rev_paths file and modify cases and subsetvars.")
    elif df_rev_case.shape[0] > 1:
        raise Exception(f"More than 1 rev_path found; check definitions in rev_paths file and add conditions to subsetvars.")
    else:
        dct_rev = df_rev_case.squeeze().to_dict()
    
    # update relevant categories with full rev path information
    # rev_cases_path should have files for each year with hourly generation data for each supply curve point 
    # or gen_gid, called [rev_prefix]_rep-profiles_[select_year].h5.
    for rev_info in ['rev_path', 'sc_path', 'sc_file']:
        configout[rev_info] = os.path.join(remotepath, "Supply_Curve_Data", dct_rev[rev_info])
    configout['rev_prefix'] = os.path.basename(dct_rev['rev_path'])

    ## format strings in tech config
    configout = {**configout, **configtech}
    config_string_formatter(configout)

    ## copy relevant files to output folder
    # resource script
    shutil.copy2(os.path.join(hourlizepath, 'resource.py'),
                 os.path.join(os.path.join(outpath, 'inputs')))
    
    # inputs (specified by 'inputfiles' in base config)
    for input in configout['inputfiles']:
        if configout[input] is not None:
            shutil.copy(os.path.join(configout[input]), os.path.join(outpath, "inputs"))

    # dump config file as json file
    configout = json.dumps(configout, indent=4, sort_keys=True)
    configpath = os.path.join(outpath, "inputs", "config.json")
    with open(configpath, "w") as outfile:
        outfile.write(configout)
        
    # setup script to run each case
    ext = '.sh' if os.name == 'posix' else '.bat'
    with open(os.path.join(outpath, batchcase + "_run" + ext), 'w+') as OPATH:
        if os.environ.get('NREL_CLUSTER') == 'kestrel':
            OPATH.writelines("source /nopt/nrel/apps/env.sh \n")
            OPATH.writelines("module load anaconda3 \n")
            OPATH.writelines("conda activate reeds2 \n\n")            
        # run hourlize
        OPATH.writelines(f"cd {hourlizepath}\n")
        OPATH.writelines(f"python resource.py --config {configpath}\n")
    
    # launch run locally or submit to hpc
    if local:
        print("Starting the run for case " + batchcase)
        if os.name!='posix':
            terminal_keep_flag = ' /k '
            os.system('start /wait cmd' + terminal_keep_flag + os.path.join(outpath, batchcase + "_run" + ext))
        if os.name=='posix':
            # Give execution rights to the shell script
            os.chmod(os.path.join(outpath, batchcase + "_run" + ext), 0o777)
            # Open it up - note the in/out/err will be written to the shellscript parameter
            shellscript = subprocess.Popen(
                [os.path.join(outpath, batchcase + "_run" + ext)], shell=True)
            # Wait for it to finish before killing the thread
            shellscript.wait()
    else:
        # set up batch script              
        shutil.copy(os.path.join(hourlizepath, "configs", "srun_template.sh"), 
                    os.path.join(outpath, batchcase+"_batch.sh"))
        
        ## modify batch script for run
        with open(os.path.join(outpath, batchcase+"_batch.sh"), 'a') as SPATH:
            # Add the name for easy tracking of the case
            SPATH.writelines("#SBATCH --job-name=" + batchcase + "\n")
            SPATH.writelines("#SBATCH --output=" + os.path.join(outpath, "slurm-%j.out") + "\n")
            SPATH.writelines("\n. $HOME/.bashrc # load default settings\n\n\n")
            # Add the call to the sh file created throughout this function
            SPATH.writelines("sh " + os.path.join(outpath, batchcase + "_run.sh"))
        SPATH.close()

        ## launch job
        batchcom = "sbatch " + os.path.join(outpath, batchcase + "_batch.sh")
        print(f"Batch script: {batchcom}")

        if nosubmit:
            print("Batch script and output folder created but run not submitted")
        else:
            subprocess.Popen(batchcom.split())
            print(f"{batchcase} submitted")
        

if __name__== '__main__':
    ## Command line arguments to script
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', '-b', type=str, default='', help='Name for batch of runs')
    parser.add_argument('--casefile', '-c', type=str, default='default', help='Suffix for cases json file')
    parser.add_argument('--local', '-l', default=False, action='store_true',
                    help='Run all cases locally (if on HPC will run on current node)')
    parser.add_argument('--nosubmit', '-n', default=False, action='store_true',
                    help='Only create config and output folders without submitting runs to queue')
    parser.add_argument('--overwrite', '-o', action="store_true", help='''Overwrite existing hourlize output folder 
                                                                          if it exists instead of archiving''')
        
    args = parser.parse_args()
    batch = args.batch
    casefile = args.casefile
    overwrite = args.overwrite 
    nosubmit = args.nosubmit
    local = args.local

    ## Path info
    hourlizepath = os.path.dirname(os.path.realpath(__file__))
    reedspath = os.path.abspath(os.path.join(hourlizepath, ".."))

    # remote path for supply curves
    hpc = True if ('NREL_CLUSTER' in os.environ) else False
    if hpc:
        #For running hourlize on the HPC link to shared-projects folder
        if os.environ.get('NREL_CLUSTER') == 'kestrel':
            remotepath = '/projects/shared-projects-reeds/reeds'
        else: 
            remotepath = '/shared-projects/reeds' 
    else:
        #If not on the hpc running link to nrelnas01
        remotepath = ('Volumes' if sys.platform == 'darwin' else '/nrelnas01') + '/ReEDS'
        
    # check remote connection
    if not os.path.exists(remotepath):
        print(
            f"Remote directory {remotepath} not detected. "
            "Check path and connection before running."
            )
        quit()
    
    # confirm local run if on hpc
    if hpc and local:
        print(
            "Note: you are on the HPC but are running locally. "
            "If you are on a login node the run may fail due to insufficient memory."
        )
        confirm_local = str(input('Proceed? [y]/n: ') or 'y')
        if not confirm_local in ['[y]', 'y','Y','yes','Yes','YES']:
            print("Exiting hourlize now.")
            quit()
    
    ## Cases to run
    # load cases from json using specified suffix (default: "cases_default.json")
    casepath = os.path.join(hourlizepath, "configs", f"cases_{casefile}.json")
    with open(casepath, "r") as f:
        cases = json.load(f, object_pairs_hook=OrderedDict)

    ## Main loop for running cases
    for casename in cases:
        try:
            run_case(casename, cases[casename])
        except Exception as err:
            print(f"Error running {casename}\n")
            traceback.print_exc() 
            print(err)
            print(f"\nSkipping {casename}.")
            continue
    print("All hourlize runs processed!")


