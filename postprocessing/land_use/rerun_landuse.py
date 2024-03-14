import os
import site
import argparse
from glob import glob

parser = argparse.ArgumentParser(description='Restart failed runs on the HPC')
parser.add_argument('batch_name', type=str, help='batch name (case prefix) to search for')
args = parser.parse_args()

#%% Get all runs 
#reedspath = os.path.dirname(os.path.abspath(__file__))
reedspath = "/scratch/bsergi/ReEDS-2.0"
runs_all = sorted(glob(os.path.join(reedspath,'runs',args.batch_name+'*')))

site.addsitedir(os.path.join(reedspath, "postprocessing", "land_use"))
import land_use_analysis as lu

#%% check which runs have land use results
runs_finished = [
    i for i in runs_all
    if os.path.exists(os.path.join(i, 'outputs', 'land_use_upv.csv'))
]

runs_unfinished = [i for i in runs_all if i not in runs_finished]

# print("Rerunning 'land_use_analysis.py' for the following cases:")
# print(runs_finished)

# rerun land_use script for runs that have finished
for run in runs_finished:
    print(f"Rerunning landuse analysis script for {os.path.basename(run)}")
    lu.runLandUse(run, reedspath, debug=True)
