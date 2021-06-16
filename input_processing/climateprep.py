# -*- coding: utf-8 -*-
"""
@author: pbrown 
@date: 20200812 11:56

Inputs
------

Outputs
-------

"""

###########
#%% IMPORTS

import pandas as pd
import numpy as np
import os
import argparse
from warnings import warn
# direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')

print('Starting climateprep.py')

##########
#%% INPUTS

### Set rounding precision
decimals = 5

parser = argparse.ArgumentParser(description="Format and write climate inputs")
parser.add_argument('-i', '--reedsdir', help='ReEDS directory')
parser.add_argument('-o', '--outdir', help='output directory')
parser.add_argument('-c', '--climatescen', help='climate scenario', default='HadGEM2-ES_rcp45_AT')
parser.add_argument('-l', '--climateloc', help='climate scenario location', default='inputs/cira')
parser.add_argument('-w', '--climatewater', help='GSw_ClimateWater', default='0')
parser.add_argument('-y', '--climatehydro', help='GSw_ClimateHydro', default='0')
parser.add_argument('-e', '--endyear', help='last year to be modeled', default='2050')

args = parser.parse_args()
reedsdir = args.reedsdir
outdir = args.outdir
climatescen = args.climatescen
climateloc = args.climateloc
GSw_ClimateWater = int(args.climatewater)
GSw_ClimateHydro = int(args.climatehydro)
endyear = int(args.endyear)

# ### (DEBUG) ###
# reedsdir = os.path.expanduser('~/github/ReEDS-2.0/')
# outdir = os.path.expanduser('~/github/ReEDS-2.0/runs/v20200911_master_Ref/inputs_case/')
# climatescen = 'HadGEM2-ES_rcp45_AT'
# climateloc = 'inputs/cira'
# climateloc = '/Volumes/ReEDS/CIRA_Inputs_R2/'
# GSw_ClimateWater = 1
# GSw_ClimateHydro = 1
# endyear = 2050

if climateloc.startswith('inputs'):
    climateloc = os.path.join(reedsdir, *(os.path.split(climateloc)))
else:
    pass

### Get the directory for climate inputs
climatedir = os.path.join(climateloc, climatescen)

#############
#%% FUNCTIONS

def readwrite(
    infile, climatedir=climatedir, outdir=outdir, decimals=decimals, endyear=endyear):
    """
    Load modifiers, interpolate to all years, write GAMS-readable csv.
    """
    ### Indicate which indices to use
    index = {
        'UnappWaterMult': ['wst','r','szn'], 
        'UnappWaterSeaAnnDistr': ['wst','r','szn'],
        'UnappWaterMultAnn': ['wst','r'],
        'hydadjann': ['r'],
        'hydadjsea': ['r','szn'],
    }
    ### Load the climate scenario data
    dfin = pd.read_csv(os.path.join(climatedir, infile+'.csv'))
    ### Put in GAMS-readable format
    dfout = pd.pivot_table(dfin, values='Value', index=index[infile], columns=['t'])
    ### If data end before endyear, create a column for endyear so we can forward-fill to it
    lastdatayear = max([int(y) for y in dfout.columns])
    if endyear > lastdatayear:
        dfout[endyear] = dfout.loc[:,lastdatayear]
    ### If data start after 2010, add a column for 2010
    if (2010 not in dfout.columns) and all(dfout.columns.values > 2010):
        ### For UnappWaterSeaAnnDistr we give the new values directly rather than as a ratio,
        ### so we backfill with the earliest available data
        if infile == 'UnappWaterSeaAnnDistr':
            dfout[2010] = dfout.iloc[:,0]
        ### Otherwise we fill with 1 (i.e. no change). Note that since we interpolate to the
        ### next value, the years between 2010 and the first year with data will not be 1.
        else:
            dfout[2010] = 1.
        ### Move 2010 column to the front of the dataframe
        dfout.sort_index(axis=1, inplace=True)
    ### Interpolate to missing years
    dfinterp = (
        dfout
        ### Switch column names from integer years to timestamps
        .rename(columns={c: pd.Timestamp(str(c)) for c in dfout.columns})
        ### Add empty columns at year-starts between existing data (mean doesn't do anything)
        .resample('YS', axis=1).mean()
        ### Interpolate linearly to fill the new columns
        .T.interpolate('linear').T
    )
    dfout = (
        ### Switch back to integer year column names
        dfinterp.rename(columns={c: c.year for c in dfinterp.columns})
        ### Drop extra data after the model end year
        .loc[:,:endyear]
    )
    ### Write it to output folder
    dfout.round(decimals).to_csv(os.path.join(outdir, 'climate_'+infile+'.csv'))
    return dfout

#############
#%% PROCEDURE

if GSw_ClimateWater:
    print('Writing annual and seasonal water climate multipliers')
    for infile in ['UnappWaterMult','UnappWaterMultAnn','UnappWaterSeaAnnDistr']:
        readwrite(infile=infile)

if GSw_ClimateHydro:
    print('Writing annual and seasonal hydro climate multipliers')
    for infile in ['hydadjann','hydadjsea']:
        readwrite(infile=infile)

if not any([GSw_ClimateWater,GSw_ClimateHydro]):
    print("All climate switches are off. We stopped climate change!")

print('Finished climateprep.py')
