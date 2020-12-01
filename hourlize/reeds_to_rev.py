import pandas as pd
import numpy as np
import sklearn.cluster as sc
from pdb import set_trace as b
import datetime
import os
import sys
import shutil
import tables
import json
import config as cf
import logging

'''
This file is for converting back from ReEDS investment results to reV capacity.
'''

#inputs
tech = 'wind-ons'
scen = 'na_f40_adv'
cost_col = 'trans_cap_cost'
sc_file = r"\\nrelqnap02\ReEDS\FY20-reV_R2-MRM\hourlize\na_wind-ons_2020-06-21-15-27-13-143715\results\wind-ons_supply_curve_raw.csv"
inv_file = r"//nrelqnap02/ReEDS/FY20-reV_R2-MRM/runs_2020-07-12/" + scen + "/outputs/cap_new_bin_out.csv"

out_dir = 'out/r2rev_' + scen + '_' + tech + '_' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + '/'
os.makedirs(out_dir)
#Copy this file into the output folder
this_file_path = os.path.realpath(__file__)
shutil.copy(this_file_path, out_dir)

df_inv = pd.read_csv(inv_file)
df_inv.columns = ['tech','vintage','region','year','bin','inv']
#limit to just this tech
df_inv = df_inv[df_inv['tech'].str.startswith(tech)].copy()
#split tech from class
df_inv[['tech_cat','class']] = df_inv['tech'].str.split('_',1, expand=True)
df_inv = df_inv[['year','region','class','bin','inv']]
df_inv['class'] = df_inv['class'].astype('int')
df_inv['bin'] = df_inv['bin'].str.replace('bin', '', regex=False).astype('int')
df_inv = df_inv.sort_values(by=['year','region','class','bin'])

#get supply curve, remove unneeded columns, and sort
df_sc = pd.read_csv(sc_file)
df_sc = df_sc[['sc_gid','region','class','bin','capacity',cost_col]].copy()
df_sc = df_sc.sort_values(by=['region','class','bin', cost_col])
df_sc['inv_sc'] = 0
df_sc_in = df_sc.copy()
# df_sc['cum_cap'] = df_sc.groupby(['region','class','bin'])['capacity'].cumsum()

#now we loop through years and determine the investment in each supply cuve point in each year
#by filling up the supply curve point capacities in order of trans_cap_cost based on the investment
#in the associated region,class,bin.
df_sc_out = pd.DataFrame()
for year in df_inv['year'].unique():
    df_inv_yr = df_inv[df_inv['year'] == year].copy()
    #df_sc = df_sc.merge(df_inv_yr, how='left', on=['region','class','bin'], sort=False)
    df_sc['inv_sc'] = 0
    for inv_i, inv_r in df_inv_yr.iterrows():
        df_sc_inv = df_sc[(df_sc['region']==inv_r['region']) & (df_sc['class']==inv_r['class']) & (df_sc['bin']==inv_r['bin'])]
        inv_left = inv_r['inv']
        for sc_i, sc_r in df_sc_inv.iterrows():
            if inv_left > sc_r['capacity']:
                df_sc.loc[sc_i,'inv_sc'] = sc_r['capacity']
                inv_left = inv_left - sc_r['capacity']
                df_sc.loc[sc_i,'capacity'] = 0
            else:
                df_sc.loc[sc_i,'inv_sc'] = inv_left
                df_sc.loc[sc_i,'capacity'] = sc_r['capacity'] - inv_left
                break
            if inv_left < 0:
                print('ERROR: inv_left is ' + str(inv_left))
    df_sc_out_yr = df_sc[df_sc['inv_sc'] > 0].copy()
    df_sc_out_yr['year'] = year
    df_sc_out = pd.concat([df_sc_out, df_sc_out_yr], sort=False)
    print("Done with " + str(year))


#Make cumulative capacity output by sc_gid
df_sc_cum_out = df_sc_out.copy()
df_sc_cum_out = df_sc_cum_out[['sc_gid','year','inv_sc']]
all_years = list(range(df_sc_out['year'].min(), df_sc_out['year'].max() + 1))
index_cols = ['sc_gid','year']
full_idx = pd.MultiIndex.from_product([df_sc_out['sc_gid'].unique().tolist(), all_years], names=index_cols)
df_sc_cum_out = df_sc_cum_out.set_index(index_cols).reindex(full_idx).reset_index()
df_sc_cum_out['inv_sc'] = df_sc_cum_out['inv_sc'].fillna(0)
df_sc_cum_out['cum_cap'] = df_sc_cum_out.groupby(['sc_gid'])['inv_sc'].cumsum()
df_sc_cum_out = df_sc_cum_out.sort_values(by=['sc_gid','year'])

#Dump outputs
df_sc_out.to_csv(out_dir + 'df_sc_out.csv', index=False)
df_sc_in.to_csv(out_dir + 'df_sc_in.csv', index=False)
df_inv.to_csv(out_dir + 'df_inv.csv', index=False)
df_sc_cum_out.to_csv(out_dir + scen + '_' + tech + '_' +'cap_by_sc.csv', index=False)
