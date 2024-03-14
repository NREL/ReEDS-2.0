# simple script to collect land use results and relabel
# run this and then rsync to shared Teams folder:
# rsync -aPu bsergi@kl1.hpc.nrel.gov://scratch/bsergi/ReEDS-2.0/postprocessing/land_use/results/  /Users/bsergi/Documents/Projects/Solar-siting/usgs land_use/land_use_results --dry-run
# rsync -aPu bsergi@kl1.hpc.nrel.gov://scratch/bsergi/ReEDS-2.0/runs/landuse_results/20231206_combined_categories  /Users/bsergi/Library/CloudStorage/OneDrive-NREL/Land\ Cover\ Scenarios --dry-run

# rsync -aPu --include=area* --exclude=* bsergi@kl1.hpc.nrel.gov://scratch/bsergi/ReEDS-2.0/postprocessing/land_use/inputs/  /Users/bsergi/Library/CloudStorage/OneDrive-NREL/Land\ Cover\ Scenarios/no_exclusions_runs --dry-run

# USFWS tranfer: this works but need to clean reeds to rev output files anyway to might as well make one 
# rsync -aPuv --prune-empty-dirs --include="20231127_landuse_BAU_*_nlcd/" --include="20231127_landuse_BAU_*_nlcd/**/" --include="20231127_landuse_BAU_*_nlcd/**/df_sc_out_*_reduced.csv" --exclude="*" bsergi@kl1.hpc.nrel.gov://scratch/bsergi/ReEDS-2.0/runs/  /Users/bsergi/Library/CloudStorage/OneDrive-NREL/USFWS\ wind\ and\ solar
# rsync -aPuv   --include="*nlcd*" --exclude="*" bsergi@kl1.hpc.nrel.gov://scratch/bsergi/ReEDS-2.0/runs/landuse_results/r2r_combined/  /Users/bsergi/Library/CloudStorage/OneDrive-NREL/USFWS\ wind\ and\ solar --dry-run

# salloc -A setosa -t 4:00:00

import os
import shutil
import pandas as pd
from glob import glob
import site
import datetime

logging = False
rerun_r2r = False
copy_r2r = False
rerun_land_use = True
copy_lu_files = False

batch = "20231127_landuse"
outputfolder = "20231206_combined_categories"
reedspath = "/scratch/bsergi/ReEDS-2.0"

# folder for outputs (keep in runs folder so branch isn't cluttered)
#outpath = os.path.join(reedspath, 'postprocessing', 'land_use', 'results', batch)
outpath = os.path.join(reedspath, 'runs', 'landuse_results', outputfolder)

# add path to hourlize
site.addsitedir(os.path.join(reedspath,'hourlize'))
import reeds_to_rev as r2r

import land_use_analysis as lua

site.addsitedir(os.path.join(reedspath,'input_processing'))

if logging:
    from ticker import makelog
    log = makelog(scriptname=__file__, logpath=os.path.join('collect_land_use_log.txt'))

# separate folder for reV files (useful for maps and for USFWS data)
revoutpath = os.path.join(reedspath, 'runs', 'landuse_results', 'r2r_data')

# if output doesn't exist make it
os.makedirs(outpath, exist_ok=True)
os.makedirs(revoutpath, exist_ok=True)

# list of land use files to copy 
#files = ['land_use_nlcd.csv.gz', 'land_use_usgs.csv.gz'] 
files = ['land_use_usgs.csv.gz'] 
r2r_files = ['df_sc_out_upv_reduced.csv', 'df_sc_out_wind-ons_reduced.csv', 'df_sc_out_wind-ofs_reduced.csv']
         
# get list of runs with corresponding batch
cases = sorted(glob(os.path.join(reedspath,'runs',batch+'*')))
print(f"loading runs with {batch} prefix")

for case in cases:
    startTime = datetime.datetime.now()
    casename = os.path.basename(case).replace(batch+"_", "")
    print(f"processing {casename}")

    ## rerun reeds_to_rev
    if rerun_r2r:
        # wind-ons
        r2r.run(reeds_path=reedspath, 
                run_folder=case,
                method="priority",
                priority="cost",
                reduced_only=True,
                tech="wind-ons",
                new_incr_mw=6
                )
        
        # wind-ofs
        r2r.run(reeds_path=reedspath, 
                run_folder=case,
                method="priority",
                priority="cost",
                reduced_only=True,
                tech="wind-ofs",
                )
        
        # upv
        r2r.run(reeds_path=reedspath, 
                run_folder=case,
                method="simultaneous",
                priority="cost",
                reduced_only=True,
                tech="upv",
                )
    
    ## copy rev files
    if copy_r2r:
        for f in r2r_files:
            os.makedirs(os.path.join(revoutpath, casename), exist_ok=True)
            try:
                shutil.copy(os.path.join(case, 'outputs', f), os.path.join(revoutpath, casename, f))
            except:
                print(f"ERROR: could not copy {os.path.join(case, 'outputs', f)}. Moving to next file.")

    # rerun land use script
    if rerun_land_use:
        lua.runLandUse(case, reedspath, debug=True)

    ## copy over land use results

    # read list of valid bas for trimming
    if copy_lu_files:
        val_r = pd.read_csv(os.path.join(case, 'inputs_case', "val_r.csv"), header=None).squeeze()

        for file in files:
            copied = False
            newfile = casename + "_" + file
            try:
                shutil.copy(os.path.join(case, 'outputs', file), os.path.join(outpath, newfile))
                copied = True
            except:
                print(f"...error copying {file} for {casename}, will skip")

            ## county formatting
            # TODO: consider transferring this over to land_use_analysis.py 

            if copied:
                # read in transferred data
                df = pd.read_csv(os.path.join(outpath, newfile))
                
                # subset to appropriate counties
                #df['region'] = 'p'+df.cnty_fips.astype(str).map('{:>05}'.format)
                #df_out = df.loc[df.region.isin(val_r)].drop("region", axis=1)
                df_out = df.loc[df.cnty_fips.isin(val_r)]

                df_out.to_csv(os.path.join(outpath, newfile), index=False)
        endTime = datetime.datetime.now()
        print(f'Finished processing {casename} ({(endTime-startTime)})')







    