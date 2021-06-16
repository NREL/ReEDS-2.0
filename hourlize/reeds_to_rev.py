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
This file is for converting back from ReEDS capacity results to reV sites.
'''

#Setup logger
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
logger.info('Resource logger setup.')

#What about PV ILR? it's included in cap_new_bin_out.csv, but should it be included here??

#user inputs
tech = 'wind-ons'
cost_col = 'trans_cap_cost'
lifetime = 30 #years
reV_folder = r'//nrelqnap02/ReEDS/Supply_Curve_Data/ONSHORE/2020_Update/multi_wind-ons_2020-08-14-17-52-38-083947'
run_folder = r'//nrelqnap02/ReEDS/FY20-reV_R2-MRM/runs_2020-08-19/bl_cut20_ref_adv'

#reV files
sc_file = reV_folder + '/results/wind-ons_supply_curve_raw.csv'

#reeds run output files
year_src = run_folder + '/outputs/systemcost.csv' #Only used to get the set of model years run.
inv_rsc = run_folder + '/outputs/cap_new_bin_out.csv' #New investments by reg/class/bin
inv_refurb = run_folder + '/outputs/cap_new_icrt_refurb.csv' #Refurbishments by reg/class/bin 
cap_exog = run_folder + '/outputs/m_capacity_exog.csv' #Existing capacity stock over time. Used for retirements of existing capacity.
rsc_wo_exist = run_folder + '/outputs/rsc_dat.csv' #Capacity by reg/class/bin after removing existing. Used with rsc_w_exist for calculating existing capacity by reg/class/bin
rsc_w_exist = run_folder + '/outputs/rsc_copy.csv' #Capacity by reg/class/bin before removing exisitng. Used with rsc_wo_exist for calculating existing capacity by reg/class/bin
cap_chk = run_folder + '/outputs/cap.csv' #Capacity by reg/class. Used only for checking results.
scen = os.path.basename(run_folder)

#Make output directory and add log file
out_dir = 'out/r2rev_' + scen + '_' + tech + '_' + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f') + '/'
os.makedirs(out_dir)
fh = logging.FileHandler(out_dir + 'log.txt', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

#Copy this file into the output folder
this_file_path = os.path.realpath(__file__)
shutil.copy(this_file_path, out_dir)

#Get years
df_yr = pd.read_csv(year_src, low_memory=False)
years = sorted(df_yr['Dim2'].unique().tolist())
years = [2009] + years

#get supply curve, remove unneeded columns, and sort
df_sc_in = pd.read_csv(sc_file, low_memory=False)
df_sc_in = df_sc_in[['sc_gid','latitude','longitude','region','class','bin','capacity',cost_col]].copy()
df_sc_in.rename(columns={'capacity':'cap_avail'}, inplace=True)
df_sc_in = df_sc_in.sort_values(by=['region','class','bin', cost_col])
df_sc = df_sc_in.copy()
df_sc['cap_expand'] = df_sc['cap_avail']
df_sc['cap_left'] = df_sc['cap_avail']
df_sc['cap'] = 0
df_sc['inv_rsc'] = 0
df_sc['ret'] = 0
df_sc['refurb'] = 0
df_sc['expanded'] = 'no'
# df_sc['cum_cap'] = df_sc.groupby(['region','class','bin'])['cap_avail'].cumsum()

#Find existing capacity by bin using difference between rsc_w_exist and rsc_wo_exist
#Consider existing capacity as investment in 2009 to use the same logic as inv_rsc when assigning to gid.
df_bin_wo_exist = pd.read_csv(rsc_wo_exist, low_memory=False)
df_bin_wo_exist.columns = ['ba', 'region', 'tech', 'bin', 'type', 'MW w/o exist']
df_bin_w_exist = pd.read_csv(rsc_w_exist, low_memory=False)
df_bin_w_exist.columns = ['ba', 'region', 'tech', 'bin', 'type', 'MW w/ exist']
df_bin_exist = df_bin_w_exist.merge(df_bin_wo_exist, how='outer', on=['ba', 'region', 'tech', 'bin', 'type'], sort=False)
df_bin_exist = df_bin_exist[df_bin_exist['type'] == 'cap'].copy()
df_bin_exist = df_bin_exist[df_bin_exist['tech'].str.startswith(tech)].copy()
df_bin_exist = df_bin_exist.fillna(0)
df_bin_exist['MW'] = df_bin_exist['MW w/ exist'] - df_bin_exist['MW w/o exist']
df_bin_exist = df_bin_exist[df_bin_exist['MW'] > 0].copy()
df_bin_exist['year'] = 2009
df_bin_exist = df_bin_exist[['tech','region','year','bin','MW']].copy()

#Read in inv_rsc
df_inv_rsc = pd.read_csv(inv_rsc, low_memory=False)
df_inv_rsc.columns = ['tech','vintage','region','year','bin','MW']
df_inv_rsc = df_inv_rsc[df_inv_rsc['tech'].str.startswith(tech)].copy()
df_inv_rsc.drop(columns=['vintage'], inplace=True)

#Concatenate existing and inv_rsc
df_inv = pd.concat([df_bin_exist, df_inv_rsc],sort=False,ignore_index=True)
#Split tech from class
df_inv[['tech_cat','class']] = df_inv['tech'].str.split('_',1, expand=True)
df_inv = df_inv[['year','region','class','bin','MW']]
df_inv['class'] = df_inv['class'].astype('int')
df_inv['bin'] = df_inv['bin'].str.replace('bin', '', regex=False).astype('int')
df_inv = df_inv.sort_values(by=['year','region','class','bin'])

#Refurbishments
df_inv_refurb_in = pd.read_csv(inv_refurb, low_memory=False)
df_inv_refurb_in.columns = ['tech','vintage','region','year','MW']
df_inv_refurb_in = df_inv_refurb_in[df_inv_refurb_in['tech'].str.startswith(tech)].copy()
df_inv_refurb_in.drop(columns=['vintage'], inplace=True)
#Split tech from class
df_inv_refurb = df_inv_refurb_in.copy()
df_inv_refurb[['tech_cat','class']] = df_inv_refurb['tech'].str.split('_',1, expand=True)
df_inv_refurb = df_inv_refurb[['year','region','class','MW']]
df_inv_refurb['class'] = df_inv_refurb['class'].astype('int')
df_inv_refurb = df_inv_refurb.sort_values(by=['year','region','class'])

#Retirements of inv_rsc. We don't need bins. We actually never needed bins...
df_ret_inv_rsc = df_inv_rsc.drop(columns=['bin'])
df_ret_inv_rsc['year'] = df_ret_inv_rsc['year'] + lifetime

#Retirements of inv_refurb:
df_ret_inv_refurb = df_inv_refurb_in.copy()
df_ret_inv_refurb['year'] = df_ret_inv_refurb['year'] + lifetime

#Retirements of existing by taking year-to-year difference of cap_exog.
df_cap_exog = pd.read_csv(cap_exog, low_memory=False)
df_cap_exog.columns = ['tech','vintage','region','year','MW']
df_cap_exog.drop(columns=['vintage'], inplace=True)
df_cap_exog = df_cap_exog[df_cap_exog['tech'].str.startswith(tech)].copy()
#Filter to years of cap_new_bin_out
df_cap_exog = df_cap_exog[df_cap_exog['year'].isin(years)].copy()
#pivot out table, add another year and fill with zeros, and then melt back
df_cap_exog = df_cap_exog.pivot_table(index=['tech','region'], columns=['year'], values='MW').reset_index()
df_cap_exog.fillna(0, inplace=True)
df_cap_exog[years[years.index(df_cap_exog.columns[-1]) + 1]] = 0 #This finds the next year in years and sets it equal to zero.
df_cap_exog = pd.melt(df_cap_exog, id_vars=['tech','region'], value_vars=df_cap_exog.columns.tolist()[2:], var_name='year', value_name= 'MW')
df_ret_exist = df_cap_exog.copy()
df_ret_exist['MW'] = df_ret_exist.groupby(['tech','region'])['MW'].diff()
df_ret_exist['MW'].fillna(0, inplace=True)
df_ret_exist['MW'] = df_ret_exist['MW'] * -1

#Concatenate retirements of existing, inv_rsc, and inv_refurb
df_ret = pd.concat([df_ret_exist, df_ret_inv_rsc, df_ret_inv_refurb],sort=False,ignore_index=True)
#remove zeros
df_ret = df_ret[df_ret['MW'] != 0].copy()
#Remove retirements in later years
df_ret = df_ret[df_ret['year'].isin(years)].copy()
#Split tech from class
df_ret[['tech_cat','class']] = df_ret['tech'].str.split('_',1, expand=True)
df_ret = df_ret[['year','region','class','MW']]
df_ret['class'] = df_ret['class'].astype('int')
df_ret = df_ret.sort_values(by=['year','region','class'])

#Get check for capacity
df_cap_chk = pd.read_csv(cap_chk, low_memory=False)
df_cap_chk.columns = ['tech','region','year','MW']
df_cap_chk = df_cap_chk[df_cap_chk['tech'].str.startswith(tech)].copy()
df_cap_chk[['tech_cat','class']] = df_cap_chk['tech'].str.split('_',1, expand=True)
df_cap_chk = df_cap_chk[['year','region','class','MW']]
df_cap_chk['class'] = df_cap_chk['class'].astype('int')

#now we loop through years and determine the investment in each supply cuve point in each year
#by filling up the supply curve point capacities in order of trans_cap_cost based on the investment
#in the associated region,class,bin.
df_sc_out = pd.DataFrame()
for year in years:
    logger.info('Starting ' + str(year))
    df_sc['year'] = year

    #First retirements
    df_sc['ret'] = 0 #reset retirements associated with gids for each year.
    df_ret_yr = df_ret[df_ret['year'] == year].copy()

    for i, r in df_ret_yr.iterrows():
        #This loops through all the retirements
        df_sc_rc = df_sc[(df_sc['region']==r['region']) & (df_sc['class']==r['class'])].copy()
        rcy =str(r['region']) + '_' + str(r['class']) + '_' + str(year)
        ret_left = r['MW']
        for sc_i, sc_r in df_sc_rc.iterrows():
            #This loops through each gid of the supply curve for this region/class
            if round(ret_left, 2) > round(sc_r['cap'], 2):
                #retirement is too large for just this gid. Fill up this gid and move to the next.
                df_sc.loc[sc_i,'ret'] = sc_r['cap']
                ret_left = ret_left - sc_r['cap']
                df_sc.loc[sc_i,'cap'] = 0
            else:
                #Remaining retirement is smaller than capacity in this gid, so assign remaining retirement to this gid
                #And break the loop through gids to move to the next retirement by region/class.
                df_sc.loc[sc_i,'ret'] = ret_left
                df_sc.loc[sc_i,'cap'] = sc_r['cap'] - ret_left
                ret_left = 0
                break
        if round(ret_left,2) != 0:
            logger.info('ERROR at rcy=' + rcy + ': ret_left should be zero and it is:' + str(ret_left))

    df_sc['cap_left'] = df_sc['cap_expand'] - df_sc['cap']

    #Then refurbishments
    df_sc['refurb'] = 0 #reset refurbishments associated with gids for each year.
    df_inv_refurb_yr = df_inv_refurb[df_inv_refurb['year'] == year].copy()

    for i, r in df_inv_refurb_yr.iterrows():
        #This loops through all the refurbishments
        df_sc_rc = df_sc[(df_sc['region']==r['region']) & (df_sc['class']==r['class'])].copy()
        rcy =str(r['region']) + '_' + str(r['class']) + '_' + str(year)
        inv_left = r['MW']
        for sc_i, sc_r in df_sc_rc.iterrows():
            #This loops through each gid of the supply curve for this region/class
            if round(inv_left, 2) > round(sc_r['cap_left'], 2):
                #refurbishment is too large for just this gid. Fill up this gid and move to the next.
                df_sc.loc[sc_i,'refurb'] = sc_r['cap_left']
                inv_left = inv_left - sc_r['cap_left']
                df_sc.loc[sc_i,'cap_left'] = 0
            else:
                #Remaining refurbishment is smaller than capacity in this gid, so assign remaining refurb to this gid
                #And break the loop through gids to move to the next refurbishment by region/class.
                df_sc.loc[sc_i,'refurb'] = inv_left
                df_sc.loc[sc_i,'cap_left'] = max(0, sc_r['cap_left'] - inv_left)
                inv_left = 0
                break
        if round(inv_left,2) != 0:
            logger.info('ERROR at rcy=' + rcy + ': inv_left for refurb should be zero and it is ' + str(inv_left))

    df_sc['cap'] = df_sc['cap_expand'] - df_sc['cap_left']

    #Finally, new site investments
    df_sc['inv_rsc'] = 0 #reset investments associated with gids for each year.
    df_inv_yr = df_inv[df_inv['year'] == year].copy()
    #df_sc = df_sc.merge(df_inv_yr, how='left', on=['region','class','bin'], sort=False)
    for i, r in df_inv_yr.iterrows():
        #This loops through all the investments
        df_sc_rcb = df_sc[(df_sc['region']==r['region']) & (df_sc['class']==r['class']) & (df_sc['bin']==r['bin'])].copy()
        rcby =str(r['region']) + '_' + str(r['class']) + '_' + str(r['bin']) + '_' + str(year)
        inv_left = r['MW']
        for sc_i, sc_r in df_sc_rcb.iterrows():
            #This loops through each gid of the supply curve for this region/class/bin
            if round(inv_left, 2) > round(sc_r['cap_left'], 2):
                #invesment is too large for just this gid.
                if sc_i == df_sc_rcb.index[-1]:
                    #This is the final supply curve row, so we are building more capacity than is available in the supply curve.
                    #In this case, we should add the remainder to the first row, expanding that gids capacity
                    logger.info('WARNING at rcby=' + rcby + '. We are building ' + str(inv_left) + ' but only have ' + str(sc_r['cap_left']))
                    df_sc.loc[sc_i,'inv_rsc'] = sc_r['cap_left']
                    df_sc.loc[sc_i,'cap_left'] = 0
                    df_sc.loc[df_sc_rcb.index[0],'inv_rsc'] += inv_left - sc_r['cap_left']
                    df_sc.loc[df_sc_rcb.index[0],'cap_expand'] += inv_left - sc_r['cap_left']
                    df_sc.loc[df_sc_rcb.index[0],'expanded'] = 'yes'
                    inv_left = 0
                    break
                else:
                    #This is the normal logic. Fill up this gid and move to the next.
                    df_sc.loc[sc_i,'inv_rsc'] = sc_r['cap_left']
                    inv_left = inv_left - sc_r['cap_left']
                    df_sc.loc[sc_i,'cap_left'] = 0
            else:
                #Remaining investment is smaller than available capacity in this gid, so assign remaining investment to this gid
                #And break the loop through gids to move to the next investment by region/class/bin.
                df_sc.loc[sc_i,'inv_rsc'] = inv_left
                df_sc.loc[sc_i,'cap_left'] = max(0, sc_r['cap_left'] - inv_left)
                inv_left = 0
                break
            if inv_left < 0:
                logger.info('ERROR at rcby=' + rcby + ': inv_left is negative: ' + str(inv_left))
        if round(inv_left,2) != 0:
            logger.info('ERROR at rcby=' + rcby + ': inv_left should be zero and it is:' + str(inv_left))
    df_sc['cap'] = df_sc['cap_expand'] - df_sc['cap_left']

    #check if capacity is the same as from cap.csv
    # cap_df_sc_yr = df_sc['cap'].sum()
    # cap_chk_yr = df_cap_chk[df_cap_chk['year'] == year]['MW'].sum()
    # if round(cap_df_sc_yr) != round(cap_chk_yr):
    #     logger.info('WARNING: total capacity, ' + str(round(cap_df_sc_yr)) + ', is not the same as from cap.csv, ' + str(round(cap_chk_yr)))
    df_sc_out = pd.concat([df_sc_out, df_sc], sort=False)

#Checks
cap_fin_df_sc = df_sc['cap'].sum()
inv_rsc_cum = df_inv['MW'].sum()
inv_refurb_cum = df_inv_refurb['MW'].sum()
ret_cum = df_ret['MW'].sum()
cap_fin_calc = inv_rsc_cum + inv_refurb_cum - ret_cum
cap_csv_fin = df_cap_chk[df_cap_chk['year'] == years[-1]]['MW'].sum()

logger.info('Final Capacity check (MW):')
logger.info('final cap in df_sc: ' + str(cap_fin_df_sc))
logger.info('Final cap.csv: ' + str(cap_csv_fin))
logger.info('Difference (error): ' + str(cap_fin_df_sc - cap_csv_fin))
logger.info('Calculated capacity from investment and retirement inputs: ' + str(cap_fin_calc))
logger.info('Cumulative inv_rsc: ' + str(inv_rsc_cum))
logger.info('Cumulative retirements: ' + str(ret_cum))
logger.info('Cumulative inv_refurb: ' + str(inv_refurb_cum))

logger.info('Outputting data...')

#Dump outputs
df_sc_out.to_csv(out_dir + 'df_sc_out.csv', index=False)
df_sc_in.to_csv(out_dir + 'df_sc_in.csv', index=False)
logger.info('All done!')
