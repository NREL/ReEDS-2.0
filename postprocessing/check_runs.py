'''
Simple python utility for checking the status of a batch of reeds runs.

Reports information on whether output files exist, total runtime, and last completed step.

'''

import os 
import shutil
import subprocess
import json
import pandas as pd
from datetime import datetime
import argparse
from glob import glob

reedspath = os.path.join(os.path.dirname(os.path.abspath(__file__)) , "..")

parser = argparse.ArgumentParser(description='Collected ReEDS PRs and Issues')
parser.add_argument('--batch', '-b', type=str,help='batch name')
args = parser.parse_args()
batch = args.batch

if batch is None:
    batch = str(input('Enter a valid batch prefix:: '))

## Get list of runs in batch
runs_all = sorted(glob(os.path.join(reedspath,'runs',batch+'*')))

## Check for ongoing runs
sq = f'squeue -u {os.environ["USER"]} -o "%.200j"'
sqout = subprocess.run(sq, capture_output=True, shell=True)
runs_running = [
    os.path.splitext(i.decode())[0] for i in sqout.stdout.split()
    if i.decode().startswith(batch)
]

## Read metadata for each run
run_data = []
for run in runs_all:
    meta = pd.read_csv(os.path.join(run, 'meta.csv'))

    # calculate process time
    meta_time = meta.iloc[2:-1]
    meta_time = meta_time.rename(columns=meta_time.iloc[0]).drop(meta_time.index[0])
    time_h = round(meta_time.processtime.astype('float').sum() / 3600, 2)

    # find last step
    last_step = meta.iloc[-1,1]
    last_year = meta.iloc[-1,0]
    if int(last_year) > 0:
        last_step = last_step + f" ({last_year})"

    # check for outputs
    has_outputs = os.path.exists(os.path.join(run, 'outputs', 'reeds-report', 'report.xlsx'))

    # check if running
    running = os.path.basename(run) in runs_running 

    # compile data
    run_data.append({'run': os.path.basename(run), 
                     'last_step':last_step, 
                     'running': running,
                     'has_outputs': has_outputs, 
                     'time_h':time_h})

data_out = pd.DataFrame(run_data)
print(data_out)