# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 11:55:00 2020
@author: jho
"""

import gdxpds
import pandas as pd
import numpy as np
import os
import re
import argparse
# direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')

parser = argparse.ArgumentParser(description="""This file produces the static and flexible load inputs""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("flex_on", help="main switch for EFS flexibility")
parser.add_argument("load_type", help="loadtype")
parser.add_argument("flex_type", help="flextype")
parser.add_argument("outdir", help="output directory")

args = parser.parse_args()

#args.reeds_dir="test"
reeds_dir_t = args.reeds_dir
#GSw_EFS_AllYearLoad
load_type_t = args.load_type
#GSw_EFS_Case
flex_type_t = args.flex_type
outdir_t =  args.outdir
#GSw_EFS_Flex - converted to integer
flex_on_t =  int(args.flex_on)

#reeds_dir_t="D:/GamsProjectJonathan/Alt_ReEDS-2.0/"
#load_type_t="EPREFERENCE"
#flex_type_t="none"
#outdir_t="E:/GamsProjectJonathan/Alt_ReEDS-2.0/runs/v08132020_ercot_seq/inputs_case/"
os.chdir(reeds_dir_t)
if (load_type_t=="default"):
    ts_sz_mapping = pd.read_csv(os.path.join('inputs','variability','h_dt_szn.csv'))
    ts_sz_mapping = ts_sz_mapping.filter(['h','season'])
    ts_sz_mapping['season'] = ts_sz_mapping['season'].str[:4]
    ts_sz_mapping['h']=ts_sz_mapping['h'].str.upper()
    ts_sz_mapping=ts_sz_mapping.drop_duplicates()
    ts_sz_mapping=ts_sz_mapping.rename(columns={"h":"timeslice"})
    ts_sz_mapping=ts_sz_mapping.append(pd.DataFrame([["H17","summ"]],columns=["timeslice","season"]),ignore_index=True)
    h_peak_data = pd.read_csv(os.path.join('inputs','loaddata','EPREFERENCEts_peak.csv'.format(load_type_t)))
    h_peak_data17 = h_peak_data.copy()
    ish3 = h_peak_data17['timeslice']=='H3'
    h_peak_data17=h_peak_data17[ish3]
    h_peak_data17['timeslice']='H17'
    h_peak_data = h_peak_data.append(h_peak_data17,ignore_index=True)
    h_peak_data = h_peak_data.filter(['r','timeslice','2010'])
    h_peak_data = h_peak_data.merge(ts_sz_mapping,how='left',on='timeslice')
    seas_peak_data_max=h_peak_data.groupby(['r','season'])['2010'].agg('max')
    seas_peak_data_max=seas_peak_data_max.reset_index()
    peak_data = pd.read_csv(os.path.join('inputs','loaddata','peak_2010.csv'))
    peak_data = pd.melt(peak_data,id_vars='r',var_name='season')
    peak_adj=pd.merge(peak_data,seas_peak_data_max, on=['r','season'])
    peak_adj['adj_factor']=peak_adj['value']/peak_adj['2010']
    peak_adj=peak_adj.drop(['2010','value'],axis=1)
    h_peak_data=h_peak_data.merge(peak_adj,on=['r','season'])
    h_peak_data['2010']=h_peak_data['2010']*h_peak_data['adj_factor']
    h_peak_data=h_peak_data.drop(['season','adj_factor'],axis=1)
    h_peak_data=h_peak_data.round(4)
    peak_data=peak_data.rename(columns={"value":"2010"})
    if flex_on_t > 0:
        flex_data = pd.read_csv(os.path.join('inputs','loaddata','{}_frac.csv'.format(flex_type_t)))
else:    
    load_data = pd.read_csv(os.path.join('inputs','loaddata','{}load.csv'.format(load_type_t)))
    peak_data = pd.read_csv(os.path.join('inputs','loaddata','{}peak.csv'.format(load_type_t)))
    h_peak_data = pd.read_csv(os.path.join('inputs','loaddata','{}ts_peak.csv'.format(load_type_t)))
    h_peak_data17 = h_peak_data.copy()
    ish3 = h_peak_data17['timeslice']=='H3'
    h_peak_data17=h_peak_data17[ish3]
    h_peak_data17['timeslice']='H17'
    h_peak_data = h_peak_data.append(h_peak_data17,ignore_index=True)
    #if flexibility is turned on...
    if flex_on_t > 0:
        #load in the %GSw_EFS_AllYearLoad%_%GSw_EFS_Case%_frac.csv file
        flex_data = pd.read_csv(os.path.join('inputs','loaddata','{}_{}_frac.csv'.format(load_type_t,flex_type_t)))

    #round values
    load_data=load_data.round(4)
    peak_data=peak_data.round(4)
    h_peak_data=h_peak_data.round(4)
    if flex_on_t > 0:
        flex_data=flex_data.round(4)
    load_data.to_csv(os.path.join(outdir_t,'load_all.csv'),index=False)

#if flexibility is not turned on, load in the reference case
if flex_on_t == 0:
    flex_data = pd.read_csv(os.path.join('inputs','loaddata','{}_{}_frac.csv'.format('EPREFERENCE','Baseflex')))
    for col in flex_data.columns:
        #if the value is a number, replace it with zero
        if np.issubdtype(flex_data[col].dtype, np.number):
            flex_data[col].values[:] = 0
else:
    flex_data=flex_data.round(4)

h_peak_data.to_csv(os.path.join(outdir_t,'h_peak_all.csv'),index=False)
peak_data.to_csv(os.path.join(outdir_t,'peak_all.csv'),index=False)
flex_data.to_csv(os.path.join(outdir_t,'flex_frac_all.csv'),index=False)