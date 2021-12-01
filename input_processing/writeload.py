import pandas as pd
import os
import argparse
# direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()

print('Beginning calculation of inputs\\writeload.py')

# Model Inputs
parser = argparse.ArgumentParser(description="""This file processes and writes out load data.""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("demandscen", help="demand scenarion")
parser.add_argument("outdir", help="output directory")

args = parser.parse_args()

reeds_dir = args.reeds_dir
demandscen = args.demandscen
outdir = args.outdir

#%%
#Inputs for testing
#reeds_dir = 'd:\\Danny_ReEDS\\ReEDS-2.0'
#demandscen = 'AEO_2019_reference'
#outdir = os.getcwd()

os.chdir(os.path.join(reeds_dir,'inputs','loaddata'))

################
#load projection
################

demand = pd.read_csv('demand_'+demandscen+'.csv')
demand = demand.round(6)

###########################################
#planning reserve margin by region and time
###########################################
prm_ann = pd.read_csv("Annual_PRM.csv")
prm_ann.i = prm_ann.i.str.replace('nr','nrn')
prm_ann.i = prm_ann.i.str.replace('new','')
prm_ann = prm_ann.pivot(index='i',columns='j',values='value').reset_index()
prm_ann = prm_ann.round(4)

print('Writing load and prm parameter to: ' + outdir)
demand.to_csv(os.path.join(outdir,'load_multiplier.csv'),index=False)
prm_ann.to_csv(os.path.join(outdir,'prm_annual.csv'),index=False)

toc(tic=tic, year=0, process='input_processing/writeload.py', 
    path=os.path.join(outdir,'..'))
