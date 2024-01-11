###########
#%% IMPORTS
import os
import sys
import subprocess
import argparse
import pandas as pd
from glob import glob

#%% Inputs
### If the user provides a case path, switch to it; otherwise assume we're already there
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
    casepath = os.path.dirname(os.path.abspath(__file__))

#############
#%% PROCEDURE
### Move to casepath
os.chdir(casepath)

### Get model execution file
files = glob('*')
callfile = [c for c in files if os.path.basename(c).startswith('call')][0]
### Get final year_iteration that the model plans to run
final_year = int(pd.read_csv(os.path.join('inputs_case','modeledyears.csv')).columns[-1])
final_year_iteration = f'{final_year}i0'

#%% Get the lines to run
old_commands = []
start_copying = 0
with open(callfile, 'r') as f:
    for line in f:
        if ('# Output processing' in line) or start_copying:
            start_copying = 1
            if (line.strip() != '') and not (line.strip().startswith('#')):
                old_commands.append(line.strip())

#%% Change the .g00 file from the final year to the most recently finished year
### Get the year-iteration from the most recent .g00 file
g00files = glob(os.path.join('g00files','*'))
years_iterations = []
for f in g00files:
    try:
        ### Keep it if it ends with _{year}i{iteration}
        year_iteration = os.path.splitext(f)[0].split('_')[-1]
        year = int(year_iteration.split('i')[0])
        years_iterations.append(year_iteration)
    except ValueError:
        ### If we can't turn the piece after the '_' into an int, it's not a year
        pass
### Keep the last one
run_year_iteration = years_iterations[-1]

### Overwrite the g00file with the latest one to finish
old_g00file_declaration = [i for i in old_commands if 'r=g00files' in i][0]
new_g00file_declaration = old_g00file_declaration.replace(
    final_year_iteration, run_year_iteration)
new_commands = [
    new_g00file_declaration if i == old_g00file_declaration
    else i
    for i in old_commands
]
### If "only" strings are specified, only include them (and cd lines)
if len(only):
    new_commands = [cmd for cmd in new_commands if any([s in cmd for s in only+['cd ']])]

#%% Run it
result = subprocess.run(
    '\n'.join(new_commands), shell=True,
    stderr=sys.stderr, stdout=sys.stdout,
)
