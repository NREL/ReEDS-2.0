# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 09:58:57 2019

@author: afrazier
"""

import gdxpds
import pandas as pd
import os
import re
import argparse

parser = argparse.ArgumentParser(description="""This file bins prescribed wind by TRG""")

parser.add_argument("reeds_dir", help="ReEDS directory")
parser.add_argument("existing", help="gdx file with existing capacity")
parser.add_argument("retires", help="gdx file with prescribed reitrements")
parser.add_argument("outdir", help="output directory")
parser.add_argument("unitdata", help="unit database")

args = parser.parse_args()

if args.unitdata == 'ABB':
    pass

elif args.unitdata == 'EIA-NEMS':

    os.chdir(args.reeds_dir)

    existing_capacity_file = args.existing
    # existing_capacity_file = 'ExistingUnits_EIA-NEMS.gdx'
    prescribed_retire_file = args.retires
    # prescribed_retire_file = 'PrescriptiveRetirements_EIA-NEMS.gdx'
    outdir = args.outdir
    # outdir = os.path.join('C:/Git','reeds-2.0','runs','test_ref_seq','inputs_case')

    raw_curves = pd.read_csv(os.path.join(outdir,'wind_supply_curves_capacity.csv'))
    raw_curves.columns = ['resource_region','class','tech','bin1','bin2','bin3','bin4','bin5']

    existing_capacity = gdxpds.to_dataframes(os.path.join('inputs','capacitydata',existing_capacity_file))
    existing_capacity = existing_capacity['tmpWTOi']
    existing_capacity.columns = ['resource_region','cap']
    existing_capacity.loc[:,'resource_region'] = pd.to_numeric(existing_capacity.loc[:,'resource_region'])
    prescribed_retire = gdxpds.to_dataframes(os.path.join('inputs','capacitydata',prescribed_retire_file))
    prescribed_retire = prescribed_retire['WindRetireExisting']
    prescribed_retire.columns=['resource_region','tech','year','cap']
    prescribed_retire.loc[:,'resource_region'] = pd.to_numeric(prescribed_retire.loc[:,'resource_region'])
    prescribed_retire.loc[:,'year'] = pd.to_numeric(prescribed_retire.loc[:,'year'])
    prescribed_retire = prescribed_retire[prescribed_retire['year']<2040].reset_index(drop=True)

    col_names = [n for n in range(2010,max(prescribed_retire['year']+1),1)]
    ind = [n for n in range(1,max(raw_curves['resource_region'])+1,1)]

    onshore = pd.DataFrame(index=ind, columns=col_names).fillna(0)
    offshore = pd.DataFrame(index=ind, columns=col_names).fillna(0)

    # Existing Capacity
    existing_capacity = existing_capacity.set_index('resource_region')
        
    # Prescribed retires
    onshore_ret = prescribed_retire[prescribed_retire['tech']=='wind-ons'].pivot(index='resource_region',columns='year',values='cap').fillna(0)
    onshore_ret_cols = list(onshore_ret)
    for i in range(1,len(onshore_ret_cols),1):
        onshore_ret.loc[:,onshore_ret_cols[i]] += onshore_ret.loc[:,onshore_ret_cols[i-1]]
    for col in [x for x in col_names if x < min(onshore_ret_cols)]:
        onshore_ret.loc[:,col] = 0
    for col in [x for x in col_names if x not in list(onshore_ret)]:
        onshore_ret.loc[:,col] = onshore_ret.loc[:,col-1]

    # Gathering totals  
    for i in onshore.index:
        if i in existing_capacity.index:
            onshore.loc[i,:] += existing_capacity.loc[i,'cap']
        if i in onshore_ret.index:
            onshore.loc[i,:] -= onshore_ret.loc[i,:]
            
    onshore = onshore.clip(lower=0)
    onshore = onshore.round(3)

    # =============================================================================
    # Binning by resource TRG
    # =============================================================================

    bin_cols = ['bin' + str(n) for n in range(1,6,1)]

    raw_curves.loc[:,'sum'] = 0
    for col in bin_cols:
        raw_curves.loc[:,'sum'] += raw_curves.loc[:,col]
        
    raw_curves.drop(bin_cols,1,inplace=True)

    for i in range(0,len(raw_curves),1):
        raw_curves.loc[i,'tech'] = raw_curves.loc[i,'tech'] + '_' + re.findall(r'\d+', raw_curves.loc[i,'class'])[0]
        
    raw_curves.drop('class',1,inplace=True)

    wind_ons = ['wind-ons_' + str(n) for n in range(1,11,1)]
    wind_ofs = ['wind-ofs_' + str(n) for n in range(1,16,1)]

    onshore_curves = raw_curves[raw_curves['tech'].isin(wind_ons)].reset_index(drop=True)
    offshore_curves = raw_curves[raw_curves['tech'].isin(wind_ofs)].reset_index(drop=True)

    onshore = onshore.reset_index()
    onshore.rename(columns={'index':'resource_region'},inplace=True)

    onshore = pd.merge(left=onshore_curves, right=onshore, on='resource_region', how='left')

    wind_onshore = pd.DataFrame(columns=['tech','year','resource_region','cap'])

    for i in onshore['resource_region'].drop_duplicates():
        temp = onshore[onshore['resource_region']==i].reset_index(drop=True)
        years = list(temp)
        years.remove('resource_region')
        years.remove('sum')
        years.remove('tech')
        yearly_installed = temp.loc[0,years]
        temp = temp.set_index('tech')
        if yearly_installed.sum() == 0:
            pass
        else:
            for year in years:
                cum_installed = 0
                if yearly_installed[year] == 0:
                    pass
                else:
                    total_installed = yearly_installed[year]
                    c = 0
                    while round(cum_installed, 8) < round(total_installed, 8):
                        trg = wind_ons[c]
                        if trg not in temp.index:
                            c += 1
                        else:
                            c += 1
                            installed_try = temp.loc[trg,year] - cum_installed
                            if installed_try <= temp.loc[trg,'sum']:
                                temp.loc[trg,year] = installed_try
                                cum_installed += installed_try
                            else:
                                temp.loc[trg,year] = temp.loc[trg,'sum']
                                cum_installed += temp.loc[trg,year]
                        
                    while c < len(wind_ons):
                        trg = wind_ons[c]
                        if trg in temp.index:
                            temp.loc[trg,year] = 0
                        c += 1
            temp.drop(['sum','resource_region'],1,inplace=True)
            temp = temp.reset_index()
            temp = pd.melt(temp, id_vars=['tech'], value_vars=years, var_name='year', value_name='cap')
            temp = temp[temp['cap']>0].reset_index(drop=True)
            temp.loc[:,'resource_region'] = i
            wind_onshore = pd.concat([wind_onshore,temp],sort=False).reset_index(drop=True)

    rsmap = pd.read_csv(os.path.join('inputs','rsmap.csv'))
    rsmap = rsmap[['rs','r']].drop_duplicates().reset_index(drop=True)
    rsmap.columns = ['resource_region','ba']
    for i in range(0,len(rsmap)):
        rsmap.loc[i,'resource_region'] = rsmap.loc[i,'resource_region'].split('s')[1]
    rsmap.loc[:,'resource_region'] = rsmap.loc[:,'resource_region'].astype(int)

    wind_onshore.loc[:,'resource_region'] = pd.to_numeric(wind_onshore.loc[:,'resource_region'])
    wind_onshore = pd.merge(left=wind_onshore, right=rsmap, on='resource_region', how='left')

    wind_onshore.loc[:,'class'] = 'init-1'
    wind_onshore.loc[:,'resource_region'] = 's' + wind_onshore.loc[:,'resource_region'].astype(str)

    wind_onshore['cap'] = wind_onshore['cap'].round(5)
    wind_onshore.rename(columns={'cap':'value'}, inplace=True)        

    wind_onshore[['tech','class','ba','resource_region','year','value']].to_csv(os.path.join(outdir,'exog_wind_by_trg.csv'),index=False)