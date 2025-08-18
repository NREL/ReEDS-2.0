#%%### Imports
import os
import sys
import subprocess
import argparse
import pandas as pd
from glob import glob


#%%### Arugment inputs
parser = argparse.ArgumentParser(
    description='Run reporting scripts on latest completed year',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    'casepath', type=str, nargs='?', default='',
    help='path to ReEDS case',
)
parser.add_argument(
    '--only', '-o', type=str, default='',
    help=',-delimited list of strings; only run reports that contain provided strings'
)
args = parser.parse_args()
casepath = args.casepath
only = [i for i in args.only.split(',') if len(i)]
if not len(casepath):
    ### If the user provides a case path, switch to it; otherwise assume we're already there
    casepath = os.path.dirname(os.path.abspath(__file__))


#%%### Procedure
### Move to casepath
os.chdir(casepath)

### Get model execution file
files = glob('*')
callfile = [c for c in files if os.path.basename(c).startswith('call')][0]
### Get final year_iteration that the model plans to run
final_year = int(pd.read_csv(os.path.join('inputs_case','modeledyears.csv')).columns[-1])
final_year_iteration = f'{final_year}i0'

#%% Get the lines to run
commands = []
start_copying = 0
with open(callfile, 'r') as f:
    for line in f:
        if ('# Output processing' in line) or start_copying:
            start_copying = 1
            if (line.strip() != '') and not (line.strip().startswith('#')):
                commands.append(line.strip())

### If "only" strings are specified, only include them (and cd lines)
if len(only):
    commands = [cmd for cmd in commands if any([s in cmd for s in only+['cd ']])]

#%% Run it
result = subprocess.run(
    '\n'.join(commands), shell=True,
    stderr=sys.stderr, stdout=sys.stdout,
)
