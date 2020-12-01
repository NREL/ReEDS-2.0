'''
ReEDS 2.0 results metadata and preprocess functions.

When adding a new ReEDS result and associated presets, this should be the only file you need to modify.

There are three sections:
1. Preprocess functions: Only needed for a result if the gdx data needs to be manipulated
2. Columns metatdata: This allows column values from a result to be mapped to display categories, joined with other columns, and styled
3. Results metadata: This is where all result configuration happens
'''
from __future__ import division
import os
import pandas as pd
import numpy as np
import collections
import core
from pdb import set_trace as pdbst

rb_globs = {'output_subdir':'/outputs/', 'test_file':'cap.csv', 'report_subdir':'/reeds2'}
this_dir_path = os.path.dirname(os.path.realpath(__file__))
df_deflator = pd.read_csv(this_dir_path + '/in/inflation.csv', index_col=0)
costs_orig_inv = ['Capital no ITC']
costs_pol_inv = ['Capital','PTC','Emissions Tax']
coststreams = ['_obj','eq_bioused','eq_gasused']
vf_valstreams = ['eq_supply_demand_balance','eq_reserve_margin','eq_opres_requirement','eq_rec_requirement','eq_curt_gen_balance','eq_curtailment']
# valuestreams = ['eq_supply_demand_balance','eq_reserve_margin','eq_opres_requirement','eq_rec_requirement','eq_national_gen','eq_annual_cap','eq_curt_gen_balance','eq_curtailment','eq_emit_accounting','eq_mingen_lb','eq_mingen_ub','eq_rps_ofswind']
energy_valstreams = ['eq_supply_demand_balance','eq_curt_gen_balance','eq_curtailment']
cc_techs = ['hydro','wind-ons','wind-ofs','csp','upv','dupv','pumped-hydro','battery', 'battery_2', 'battery_4', 'battery_6', 'battery_8', 'battery_10']
price_types = ['load','res_marg','oper_res','state_rps','nat_gen']

#1. Preprocess functions for results_meta
def scale_column(df, **kw):
    df[kw['column']] = df[kw['column']] * kw['scale_factor']
    return df

def add_cooling_water(df, **kw):
    #load the tech mapping to ctt and wst
    df_tech_ctt_wst = pd.read_csv(this_dir_path + '/in/reeds2/tech_ctt_wst.csv')
    df_tech_ctt_wst['tech'] = df_tech_ctt_wst['tech'].str.lower()
    df = pd.merge(left=df, right=df_tech_ctt_wst, how='left', on=['tech'], sort=False)
    #fill na values
    df['wst'].fillna('other', inplace=True)
    df['ctt'].fillna('none', inplace=True)
    return df

def scale_column_filtered(df, **kw):
    cond = df[kw['by_column']].isin(kw['by_vals'])
    df.loc[cond, kw['change_column']] = df.loc[cond, kw['change_column']] * kw['scale_factor']
    return df

def sum_over_cols(df, **kw):
    if 'val_cols' in kw:
        drop_cols = [c for c in df.columns if c not in kw['group_cols']+kw['val_cols']]
    elif 'drop_cols' in kw:
        drop_cols = kw['drop_cols']
    df = df.drop(drop_cols, axis='columns')
    df =  df.groupby(kw['group_cols'], sort=False, as_index =False).sum()
    return df

def apply_inflation(df, **kw):
    df[kw['column']] = inflate_series(df[kw['column']])
    return df

def inflate_series(ser_in):
    return ser_in * 1/df_deflator.loc[int(core.GL['widgets']['var_dollar_year'].value), 'Deflator']

def pre_systemcost(dfs, **kw):
    df = dfs['sc']

    #apply inflation and adjust to billion dollars
    df['Cost (Bil $)'] = inflate_series(df['Cost (Bil $)']) * 1e-9
    d = float(core.GL['widgets']['var_discount_rate'].value)
    y0 = int(core.GL['widgets']['var_pv_year'].value)

    #Gather lists of capital and operation labels
    cost_cats_df = df['cost_cat'].unique().tolist()
    df_cost_type = pd.read_csv(this_dir_path + '/in/reeds2/cost_cat_type.csv')
    #Make sure all cost categories in df are in df_cost_type and throw error if not!!
    if not set(cost_cats_df).issubset(df_cost_type['cost_cat'].values.tolist()):
        print('WARNING: Not all cost categories have been mapped!!!')
    cap_type_ls = [c for c in cost_cats_df if c in df_cost_type[df_cost_type['type']=='Capital']['cost_cat'].tolist()]
    op_type_ls = [c for c in cost_cats_df if c in df_cost_type[df_cost_type['type']=='Operation']['cost_cat'].tolist()]

    #Calculate objective function system costs
    if 'objective' in kw and kw['objective'] == True:
        #Multiply all capital costs by pvf_capital and operation by pvf_onm
        df = pd.merge(left=df, right=dfs['pvf_cap'], how='left', on=['year'], sort=False)
        df = pd.merge(left=df, right=dfs['pvf_onm'], how='left', on=['year'], sort=False)
        cap_cond = df['cost_cat'].isin(cap_type_ls)
        onm_cond = df['cost_cat'].isin(op_type_ls)
        df.loc[cap_cond, 'Cost (Bil $)'] = df.loc[cap_cond, 'Cost (Bil $)'] * df.loc[cap_cond, 'pvfcap']
        df.loc[onm_cond, 'Cost (Bil $)'] = df.loc[onm_cond, 'Cost (Bil $)'] * df.loc[onm_cond, 'pvfonm']
        df.drop(['pvfcap','pvfonm'], axis='columns',inplace=True)
        #We don't add a discounted cost column
        return df

    #Annualize if specified
    if 'annualize' in kw and kw['annualize'] == True:
        #Turn each cost category into a column
        df = df.pivot_table(index=['year'], columns='cost_cat', values='Cost (Bil $)')
        #Add rows for all years (including 20 years after end year) and fill
        full_yrs = list(range(df.index.min() - 19, df.index.max() + 21))
        df = df.reindex(full_yrs)
        #For capital costs, multiply by CRF to annualize, and sum over previous 20 years.
        #This requires 20 years before 2010 to sum properly, and we need to shift capital dataframe down
        #so that capital payments start in the year after the investment was made
        if 'crf_from_user' in kw and kw['crf_from_user'] == True:
            crf = pd.DataFrame({'year':full_yrs, 'crf':d*(1+d)**20/((1+d)**20 - 1)}).set_index('year')
        #otherwise use the crf from model run
        else:
            crf = dfs['crf']
            crf = crf.set_index('year').reindex(full_yrs)
            crf = crf.interpolate(method ='linear')
            crf['crf'] = crf['crf'].fillna(method='bfill')
        df = pd.merge(left=df, right=crf, how='left',on=['year'], sort=False)
        df[cap_type_ls] = df[cap_type_ls].shift().fillna(0)
        df[cap_type_ls] = df[cap_type_ls].multiply(df["crf"], axis="index")
        df[cap_type_ls] = df[cap_type_ls].rolling(20).sum()
        #Remove years before 2010
        full_yrs = list(range(df.index.min() + 19, df.index.max() + 1))
        df = df.reindex(full_yrs)

        #Add capacity payment for existing (pre-2010) generators (in billion $)
        df_existingpayment = dfs['existcap']
        df_existingpayment = df_existingpayment.set_index('year')
        df_existingpayment = df_existingpayment.reindex(full_yrs)
        df_existingpayment = df_existingpayment.fillna(0)
        df['inv_investment_capacity_costs'] = df['inv_investment_capacity_costs']+df_existingpayment['existingcap']

        #For operation costs, simply fill missing years with model year values.
        df[op_type_ls] = df[op_type_ls].fillna(method='ffill')
        #The final year should only include capital payments because operation payments last for 20 yrs starting
        #in the model year, whereas capital payments last for 20 yrs starting in the year after the model year.
        df.loc[df.index.max(), op_type_ls] = 0
        df = df.fillna(0)
        df = pd.melt(df.reset_index(), id_vars=['year'], value_vars=cap_type_ls + op_type_ls, var_name='cost_cat', value_name= 'Cost (Bil $)')

    #Add Dicounted Cost column (including for annualized)
    df['Discounted Cost (Bil $)'] = df['Cost (Bil $)'] / (1 + d)**(df['year'] - y0)
    return df

def pre_avgprice(dfs, **kw):
    df = dfs['sc']
    #apply inflation and adjust to billion dollars
    df['Cost (Bil $)'] = inflate_series(df['Cost (Bil $)']) * 1e-9

    #Gather lists of capital and operation labels
    cost_cats_df = df['cost_cat'].unique().tolist()
    df_cost_type = pd.read_csv(this_dir_path + '/in/reeds2/cost_cat_type.csv')
    #Make sure all cost categories in df are in df_cost_type and throw error if not!!
    if not set(cost_cats_df).issubset(df_cost_type['cost_cat'].values.tolist()):
        print('WARNING: Not all cost categories have been mapped!!!')
    cap_type_ls = [c for c in cost_cats_df if c in df_cost_type[df_cost_type['type']=='Capital']['cost_cat'].tolist()]
    op_type_ls = [c for c in cost_cats_df if c in df_cost_type[df_cost_type['type']=='Operation']['cost_cat'].tolist()]

    #Depending on whether 'National' or 'BA'-level average cost if specified
    if 'National' in kw and kw['National'] == True:
        #Turn each cost category into a column
        df = df.pivot_table(index=['year'], columns='cost_cat', values='Cost (Bil $)')
        #Add rows for all years (including 20 years after end year) and fill
        full_yrs = list(range(df.index.min() - 19, df.index.max() + 21))
        df = df.reindex(full_yrs)
        #For capital costs, multiply by CRF to annualize, and sum over previous 20 years.
        #This requires 20 years before 2010 to sum properly, and we need to shift capital dataframe down
        #so that capital payments start in the year after the investment was made
        crf = dfs['crf']
        crf = crf.set_index('year').reindex(full_yrs)
        crf = crf.interpolate(method ='linear')
        crf['crf'] = crf['crf'].fillna(method='bfill')
        df = pd.merge(left=df, right=crf, how='left',on=['year'], sort=False)
        df[cap_type_ls] = df[cap_type_ls].shift().fillna(0)
        df[cap_type_ls] = df[cap_type_ls].multiply(df["crf"], axis="index")
        df[cap_type_ls] = df[cap_type_ls].rolling(20).sum()
        #Remove years before 2010
        full_yrs = list(range(df.index.min() + 19, df.index.max() + 1))
        df = df.reindex(full_yrs)

        #Add capacity payment for existing (pre-2010) generators (in billion $)
        df_existingpayment = dfs['existcap']
        df_existingpayment = df_existingpayment.set_index('year')
        df_existingpayment = df_existingpayment.reindex(full_yrs)
        df_existingpayment = df_existingpayment.fillna(0)
        df['inv_investment_capacity_costs'] = df['inv_investment_capacity_costs']+df_existingpayment['existingcap']
        #For operation costs, simply fill missing years with model year values.
        df[op_type_ls] = df[op_type_ls].fillna(method='ffill')
        #The final year should only include capital payments because operation payments last for 20 yrs starting
        #in the model year, whereas capital payments last for 20 yrs starting in the year after the model year.
        df.loc[df.index.max(), op_type_ls] = 0
        df = df.fillna(0)
        df = pd.melt(df.reset_index(), id_vars=['year'], value_vars=cap_type_ls + op_type_ls, var_name='cost_cat', value_name= 'Cost (Bil $)')

        #Read in load
        df_load = dfs['q']
        df_load_nat = df_load[df_load['type'] == 'load'].groupby('year')['q'].sum()
        df_load_nat = df_load_nat.to_frame()
        df_load_nat = df_load_nat.reindex(full_yrs)
        df_load_nat = df_load_nat.interpolate(method ='linear')

        df_natavgprice = pd.merge(left=df, right=df_load_nat, how='left',on=['year'], sort=False)
        df_natavgprice['Average cost ($/MWh)'] = df_natavgprice['Cost (Bil $)'] * 1e9 / df_natavgprice['q']

        return df_natavgprice

    if 'BA' in kw and kw['BA'] == True:

        df_rrs_map = pd.read_csv(this_dir_path + '/in/reeds2/region_map.csv')
        df_rrs_map.columns = ['region','regionnew']

        df_hours_map = pd.read_csv(this_dir_path + '/in/reeds2/m_map.csv')
        df_hours_width = pd.read_csv(this_dir_path + '/in/reeds2/m_bar_width.csv')
        df_hours_map = pd.merge(left=df_hours_map, right=df_hours_width, how='left',on=['display'],sort=False)
        df_hours_map.dropna(inplace=True)
        df_hours_map = df_hours_map.drop(columns = ['display'])
        df_hours_map.columns = ["timeslice","hours"]

        #-------Capital and operational costs--------
        #Aggregate costs to BA-level
        df = pd.merge(left=df, right=df_rrs_map, how='left',on=['region'], sort=False)
        df['regionnew'] = df['regionnew'].fillna(df['region'])
        df = df.groupby(['cost_cat','regionnew','year',])['Cost (Bil $)'].sum().reset_index()
        df.columns = ['cost_cat','region', 'year', 'Cost (Bil $)']

        region_ls = df['region'].unique().tolist()

        #Turn each cost category into a column
        df = df.pivot_table(index=['year'], columns=['region','cost_cat'], values='Cost (Bil $)')
        #Add rows for all years (including 20 years after end year) and fill
        full_yrs = list(range(df.index.min() - 19, df.index.max() + 21))
        df = df.reindex(full_yrs)
        #For capital costs, multiply by CRF to annualize, and sum over previous 20 years.
        #This requires 20 years before 2010 to sum properly, and we need to shift capital dataframe down
        #so that capital payments start in the year after the investment was made
        crf = dfs['crf']
        crf = crf.set_index('year').reindex(full_yrs)
        crf = crf.interpolate(method ='linear')
        crf['crf'] = crf['crf'].fillna(method='bfill')
        df = pd.merge(left=df, right=crf, how='left',on=['year'], sort=False)
        colname_ls = pd.MultiIndex.from_product([region_ls, cap_type_ls],names=['region', 'cost_cat'])
        colname_ls = [c for c in colname_ls if c in df.columns.tolist()]
        df[colname_ls] = df[colname_ls].shift().fillna(0)
        df[colname_ls] = df[colname_ls].multiply(df["crf"], axis="index")
        df[colname_ls] = df[colname_ls].rolling(20).sum()
        df = df.drop(columns = ['crf'])
        #Remove years before 2010
        full_yrs = list(range(df.index.min() + 19, df.index.max() + 1))
        df = df.reindex(full_yrs)

        #For operation costs, simply fill missing years with model year values.
        colname_ls = pd.MultiIndex.from_product([region_ls, op_type_ls],names=['region', 'cost_cat'])
        colname_ls = [c for c in colname_ls if c in df.columns.tolist()]
        df[colname_ls] = df[colname_ls].fillna(method='ffill')
        #The final year should only include capital payments because operation payments last for 20 yrs starting
        #in the model year, whereas capital payments last for 20 yrs starting in the year after the model year.
        df.loc[df.index.max(), colname_ls] = 0
        df = df.fillna(0)

        df = df.T
        df.index = pd.MultiIndex.from_tuples(df.index.values, names=('region','cost_cat'))
        df = df.reset_index()
        df = pd.melt(df, id_vars=['region','cost_cat'], value_vars=df.columns.tolist()[2:], var_name='year', value_name= 'Cost (Bil $)')
        df = df.pivot_table(index=['year','region'], columns=['cost_cat'], values='Cost (Bil $)')
        df = df.reset_index(level='region')

        #Add capacity payment for existing (pre-2010) generators (in billion $)
        df_existingpayment = pd.read_csv('D:/ReEDS_YSun/ReEDS-2.0/runs/v20191230_ref_seq_ng0/outputs/cappayments_ba.csv')
        df_existingpayment.columns = ['region', 'year','existingcap']
        df = pd.merge(left=df, right=df_existingpayment, how='left',on=['year','region'], sort=False)
        df = df.fillna(0)
        df['inv_investment_capacity_costs'] = df['inv_investment_capacity_costs']+df['existingcap']
        df = df.drop(columns = 'existingcap')
        df = pd.melt(df.reset_index(), id_vars=['year','region'], value_vars=df.columns.tolist()[2:], var_name='cost_cat', value_name= 'Cost (Bil $)')

        #-------Capacity trading--------
        df_captrade = dfs['captrade']
        df_captrade = df_captrade.groupby(['rb_out', 'rb_in', 'season', 'year'])['Amount (MW)'].sum().reset_index()

        df_capprice = dfs['p']
        df_capprice = df_capprice.loc[df_capprice['type'] == 'res_marg'].reset_index()
        df_capprice = df_capprice[df_capprice.columns[3:]]
        df_capprice.columns = ['rb_out','season','year', 'p']

        df_captrade = pd.merge(left=df_captrade, right=df_capprice, how='left',on=['rb_out','season','year'], sort=False)
        df_captrade = df_captrade.dropna()
        df_captrade['cost_rb_out'] = df_captrade['p'] * df_captrade['Amount (MW)']  *1e3 / 1e9  #in billion dollars

        df_capimportcost = df_captrade.groupby(['rb_in','year',])['cost_rb_out'].sum().reset_index()
        df_capexportcost = df_captrade.groupby(['rb_out','year',])['cost_rb_out'].sum().reset_index()
        df_capexportcost['cost_rb_out'] = -df_capexportcost['cost_rb_out']

        df_capimportcost['cost_cat'] = 'cap_trade_import_cost'
        df_capimportcost.columns = ['region','year','Cost (Bil $)','cost_cat']
        df_capimportcost = df_capimportcost[['year','region','cost_cat','Cost (Bil $)']]
        df_capexportcost['cost_cat'] = 'cap_trade_export_cost'
        df_capexportcost.columns = ['region','year','Cost (Bil $)','cost_cat']
        df_capexportcost = df_capexportcost[['year','region','cost_cat','Cost (Bil $)']]
        df_captradecost = pd.concat([df_capimportcost,df_capexportcost], sort=False)

        #-------Energy trading--------
        df_gen = dfs['gen']
        df_gen = df_gen.groupby(['r', 'timeslice', 'year'])['Generation (GW)'].sum().reset_index()

        df_energyprice = dfs['p']
        df_energyprice = df_energyprice.loc[df_energyprice['type'] == 'load'].reset_index()
        df_energyprice = df_energyprice[df_energyprice.columns[3:]]
        df_energyprice.columns = ['r', 'timeslice', 'year', 'p']

        df_powfrac_up = dfs['powerfrac_upstream']
        df_powfrac_down = dfs['powerfrac_downstream']
        df_powfrac_up = df_powfrac_up.loc[df_powfrac_up['r'] != df_powfrac_up['rr'] ].reset_index()
        df_powfrac_down = df_powfrac_down.loc[df_powfrac_down['r'] != df_powfrac_down['rr'] ].reset_index()

        df_energyimport = pd.merge(left=df_powfrac_up, right=df_gen, how='left',on=['r','timeslice','year'], sort=False)
        df_energyimport = pd.merge(left=df_energyimport, right=df_energyprice, how='left',left_on=['rr','timeslice','year'], right_on=['r','timeslice','year'], sort=False)
        df_energyimport = df_energyimport.drop(columns = 'r_y')
        df_energyimport.columns = ['index', 'r', 'rr', 'timeslice', 'year', 'frac', 'Generation (GW)','p']
        df_energyimport = pd.merge(left=df_energyimport, right=df_hours_map, how='left',on=['timeslice'], sort=False)
        df_energyimport['importcost (Bil $)'] = df_energyimport['frac'] *df_energyimport['Generation (GW)'] * df_energyimport['p'] * df_energyimport['hours'] / 1e9
        df_energyimportcost = df_energyimport.groupby(['r', 'year'])['importcost (Bil $)'].sum().reset_index()

        df_energyexport = df_powfrac_down.groupby(['rr', 'timeslice', 'year'])['frac'].sum().reset_index()
        df_energyexport.columns = ['r', 'timeslice', 'year','frac']
        df_energyexport= pd.merge(left=df_energyexport, right=df_gen, how='left',on=['r','timeslice','year'], sort=False)
        df_energyexport = pd.merge(left=df_energyexport, right=df_energyprice, how='left',on=['r','timeslice','year'], sort=False)
        df_energyexport = pd.merge(left=df_energyexport, right=df_hours_map, how='left',on=['timeslice'], sort=False)

        df_energyexport['exportcost (Bil $)'] = df_energyexport['frac'] *df_energyexport['Generation (GW)'] * df_energyexport['p'] * df_energyexport['hours'] / 1e9
        df_energyexportcost = df_energyexport.groupby(['r', 'year'])['exportcost (Bil $)'].sum().reset_index()
        df_energyexportcost['exportcost (Bil $)'] = -df_energyexportcost['exportcost (Bil $)']

        df_energyimportcost['cost_cat'] = 'energy_trade_import_cost'
        df_energyimportcost.columns = ['region','year','Cost (Bil $)','cost_cat']
        df_energyimportcost = df_energyimportcost[['year','region','cost_cat','Cost (Bil $)']]
        df_energyexportcost['cost_cat'] = 'energy_trade_export_cost'
        df_energyexportcost.columns = ['region','year','Cost (Bil $)','cost_cat']
        df_energyexportcost = df_energyexportcost[['year','region','cost_cat','Cost (Bil $)']]
        df_energytradecost = pd.concat([df_energyimportcost,df_energyexportcost], sort=False)

        #-------Combine with load to calculate average cost--------
        df = pd.concat([df,df_captradecost,df_energytradecost], sort=False)

        df_load = dfs['q']
        df_load_ba = df_load[df_load['type'] == 'load'].groupby(['year','rb'])['q'].sum().reset_index()
        df_load_ba.columns = ['year','region','load (MWh)']

        df_baavgprice = pd.merge(left=df, right=df_load_ba, how='left',on=['year','region'], sort=False)
        df_baavgprice = df_baavgprice.dropna()
        df_baavgprice['Average cost ($/MWh)'] = df_baavgprice['Cost (Bil $)'] * 1e9 / df_baavgprice['load (MWh)']
        df_baavgprice.rename(columns={'region':'rb'}, inplace=True)

        return df_baavgprice

def pre_abatement_cost(dfs, **kw):
    if 'objective' in kw and kw['objective'] == True:
        #Preprocess costs
        df_sc = pre_systemcost(dfs, objective=True)
        df_sc['type'] = 'Cost (Bil $)'
        df_sc.rename(columns={'Cost (Bil $)':'val'}, inplace=True)
        #Preprocess emissions
        df_co2 = dfs['emit']
        df_co2.rename(columns={'CO2 (MMton)':'val'}, inplace=True)
        df_co2['val'] = df_co2['val'] * 1e-3 #converting to billion metric tons
        #Multiply by pvfonm to convert to total objective level of emissions for that year
        df_co2 = pd.merge(left=df_co2, right=dfs['pvf_onm'], how='left', on=['year'], sort=False)
        df_co2['val'] = df_co2['val'] * df_co2['pvfonm']
        df_co2.drop(['pvfonm'], axis='columns',inplace=True)
        #Add type and cost_cat columns so we can concatenate
        df_co2['type'] = 'CO2 (Bil metric ton)'
        df_co2['cost_cat'] = 'CO2 (Bil metric ton)'
        #Concatenate costs and emissions
        df = pd.concat([df_sc, df_co2],sort=False,ignore_index=True)

    elif 'annualize' in kw and kw['annualize'] == True:
        #Preprocess costs
        df_sc = pre_systemcost(dfs, annualize=True)
        df_sc = sum_over_cols(df_sc, group_cols=['year','cost_cat'], drop_cols=['Discounted Cost (Bil $)'])
        df_sc['type'] = 'Cost (Bil $)'
        df_sc.rename(columns={'Cost (Bil $)':'val'}, inplace=True)
        #Preprocess emissions
        df_co2 = dfs['emit']
        df_co2.rename(columns={'CO2 (MMton)':'val'}, inplace=True)
        df_co2['val'] = df_co2['val'] * 1e-3 #converting to billion metric tons
        full_yrs = list(range(df_sc['year'].min(), df_sc['year'].max() + 1))
        df_co2 = df_co2.set_index('year').reindex(full_yrs).reset_index()
        df_co2['val'] = df_co2['val'].fillna(method='ffill')
        df_co2['type'] = 'CO2 (Bil metric ton)'
        df_co2['cost_cat'] = 'CO2 (Bil metric ton)'
        #Concatenate costs and emissions
        df = pd.concat([df_sc, df_co2],sort=False,ignore_index=True)
        #Add discounted value column
        d = float(core.GL['widgets']['var_discount_rate'].value)
        y0 = int(core.GL['widgets']['var_pv_year'].value)
        df['disc val'] = df['val'] / (1 + d)**(df['year'] - y0)
        #Add cumulative columns
        df['cum val'] = df.groupby('cost_cat')['val'].cumsum()
        df['cum disc val'] = df.groupby('cost_cat')['disc val'].cumsum()

    return df

def add_class(df, **kw):
    cond = df['tech'].str.contains('_', regex=False)
    #Assume class is at the end, after the final underscore:
    df.loc[cond, 'class']='class_' + df.loc[cond, 'tech'].str.split('_').str[-1]
    return df

def map_rs_to_rb(df, **kw):
    df_hier = pd.read_csv(this_dir_path + '/in/reeds2/region_map.csv')
    dict_hier = dict(zip(df_hier['rs'], df_hier['rb']))
    df.loc[df['region'].isin(dict_hier.keys()), 'region'] = df['region'].map(dict_hier)
    df.rename(columns={'region':'rb'}, inplace=True)
    if 'groupsum' in kw:
        df = df.groupby(kw['groupsum'], sort=False, as_index=False).sum()
    return df

def remove_ba(df, **kw):
    df = df[~df['region'].astype(str).str.startswith('p')].copy()
    df.rename(columns={'region':'rs'}, inplace=True)
    return df

def pre_val_streams(dfs, **kw):
    index_cols = ['tech', 'vintage', 'rb', 'year']
    inv_vars = ['inv','inv_refurb']
    cum_vars = ['gen','cap','opres','storage_in']

    if 'remove_inv' in kw:
        dfs['vs'] = dfs['vs'][~dfs['vs']['var_name'].isin(inv_vars)].copy()

    if 'uncurt' in kw:
        #For techs that are in gen_uncurt, use gen_uncurt instead of gen
        dfs['gen'] = dfs['gen'][~dfs['gen']['tech'].isin(dfs['gen_uncurt']['tech'].unique())].copy()
        dfs['gen'] = pd.concat([dfs['gen'], dfs['gen_uncurt']],sort=False,ignore_index=True)

    if 'investment_only' in kw:
        #Analyze only investment years
        #The first attempt of this was to use the ratio of new vs cumulative capacity in a vintage, but this has issues
        #because of the mismatch in regionality between capacity and generation, meaning ba-level capacity ratio may not
        #even out value streams.
        #First, use the capacity/investment linking equations with the investment and capacity variables to find the
        #scaling factors between investment and capacity value streams
        linking_eqs = ['eq_cap_new_noret','eq_cap_new_retub','eq_cap_new_retmo'] #eq_cap_new_retmo also includes previous year's CAP, is this bad?!
        df_vs_links = dfs['vs'][dfs['vs']['con_name'].isin(linking_eqs)].copy()
        df_vs_inv = df_vs_links[df_vs_links['var_name'].isin(inv_vars)].copy()
        df_vs_cap = df_vs_links[df_vs_links['var_name'] == 'cap'].copy()
        df_vs_inv = sum_over_cols(df_vs_inv, group_cols=index_cols, drop_cols=['var_name','con_name'])
        df_vs_cap = sum_over_cols(df_vs_cap, group_cols=index_cols, drop_cols=['var_name','con_name'])
        #merge left with df_vs_inv so that we're only looking at cumulative value streams in investment years.
        df_scale = pd.merge(left=df_vs_inv, right=df_vs_cap, how='left', on=index_cols, sort=False)
        df_scale['mult'] = df_scale['$_x'] / df_scale['$_y'] * -1
        df_scale = df_scale[index_cols + ['mult']]
        #Gather cumulative value streams. NEED TO ADD TRANSMISSION
        df_cum = dfs['vs'][dfs['vs']['var_name'].isin(cum_vars)].copy()
        #Left merge with df_scale to keep only the cumulative streams in investment years
        df_cum = pd.merge(left=df_scale, right=df_cum, how='left', on=index_cols, sort=False)
        #Scale the cumulative value streams
        df_cum['$'] = df_cum['$'] * df_cum['mult']
        df_cum.drop(['mult'], axis='columns',inplace=True)
        #Concatenate modified cumulative value streams with the rest of the value streams
        dfs['vs'] = dfs['vs'][~dfs['vs']['var_name'].isin(cum_vars)].copy()
        dfs['vs'] = pd.concat([dfs['vs'], df_cum],sort=False,ignore_index=True)
        #Adjust generation based on the same scaling factor. Not sure this is exactly right, but if
        #value streams for GEN have scaled, it makes sense to attribute this to quantity of energy being scaled,
        #rather than prices changing.
        dfs['gen'] = pd.merge(left=df_scale, right=dfs['gen'], how='left', on=index_cols, sort=False)
        dfs['gen']['MWh'] = dfs['gen']['MWh'] * dfs['gen']['mult']
        dfs['gen'].drop(['mult'], axis='columns',inplace=True)

    #apply inflation
    dfs['vs']['$'] = inflate_series(dfs['vs']['$'])

    if 'value_factors' in kw:
        #sum over vintage in both generation and value streams:
        df_gen = sum_over_cols(dfs['gen'], group_cols=['tech','rb','year'], val_cols=['MWh'])
        df = sum_over_cols(dfs['vs'], group_cols=['tech','rb','year','con_name'], val_cols=['$'])
        #Reduce value streams to only the ones we care about
        df = df[df['con_name'].isin(vf_valstreams)].copy()
        #Include all con_name options for each tech,rb,year combo and fill na with zero
        df = df.pivot_table(index=['tech','rb','year'], columns='con_name', values='$').reset_index()
        df = pd.melt(df, id_vars=['tech','rb','year'], var_name='con_name', value_name= '$')
        df['$'].fillna(0, inplace=True)
        #convert value streams from bulk $ as of discount year to annual as of model year
        df = pd.merge(left=df, right=dfs['pvf_onm'], how='left', on=['year'], sort=False)
        df['$'] = df['$'] / dfs['cost_scale'].iloc[0,0] / df['pvfonm']
        df.drop(['pvfonm'], axis='columns',inplace=True)

        #get requirement prices and quantities and build benchmark value streams
        dfs['p']['p'] = inflate_series(dfs['p']['p'])
        df_bm = pd.merge(left=dfs['q'], right=dfs['p'], how='left', on=['type', 'subtype', 'rb', 'timeslice', 'year'], sort=False)
        df_bm['p'].fillna(0, inplace=True)
        #Add con_name:
        types = ['load','res_marg','oper_res','state_rps','curt_realize','curt_cause'] #the curt ones don't exist, they are just placeholders for the mapping.
        df_bm = df_bm[df_bm['type'].isin(types)].copy()
        df_con_type = pd.DataFrame({'type':types,'con_name':vf_valstreams})
        df_bm = pd.merge(left=df_bm, right=df_con_type, how='left', on=['type'], sort=False)
        #drop type and subtype because we're using con_name from here on
        df_bm.drop(['type','subtype'], axis='columns', inplace=True)
        #columns of df_bm at this point are rb,timeslice,year,con_name,p,q

        #Calculate annual load for use in benchmarks
        df_load = dfs['q'][dfs['q']['type']=='load'].copy()
        df_load = sum_over_cols(df_load, group_cols=['rb', 'year'], val_cols=['q'])

        #All-in benchmarks. These assume the benchmark tech provides all value streams at requirement levels,
        #and prices are calculated by dividing value by load.
        df_bm_allin = df_bm.copy()
        df_bm_allin['$'] = df_bm_allin['p'] * df_bm_allin['q']
        df_bm_allin = sum_over_cols(df_bm_allin, group_cols=['con_name', 'rb', 'year'], val_cols=['$'])
        df_bm_allin = pd.merge(left=df_bm_allin, right=df_load, how='left', on=['rb', 'year'], sort=False)

        #local all-in (weighted) benchmark. First calculate prices as $ of requirement divided by MWh energy
        df_bm_allin_loc = df_bm_allin.copy()
        df_bm_allin_loc['$ all-in loc'] = df_bm_allin_loc['$'] / df_bm_allin_loc['q']
        df_bm_allin_loc.drop(['$','q'], axis='columns', inplace=True)
        df = pd.merge(left=df, right=df_bm_allin_loc, how='left', on=['year','rb','con_name'], sort=False)

        #system-wide all-in (weighted) benchmark
        df_bm_allin_sys = sum_over_cols(df_bm_allin, group_cols=['year','con_name'], val_cols=['$','q'])
        df_bm_allin_sys['$ all-in sys'] = df_bm_allin_sys['$'] / df_bm_allin_sys['q']
        df_bm_allin_sys.drop(['$','q'], axis='columns', inplace=True)
        df = pd.merge(left=df, right=df_bm_allin_sys, how='left', on=['year','con_name'], sort=False)

        #Flat-block benchmarks. These assume the tech provides energy + reserve margin only.
        flatblock_cons = ['eq_supply_demand_balance','eq_reserve_margin']
        df_bm_flat_loc = df_bm[df_bm['con_name'].isin(flatblock_cons)].copy()
        #Add hours
        df_hours = pd.read_csv(this_dir_path + '/in/reeds2/hours.csv')
        df_bm_flat_loc = pd.merge(left=df_bm_flat_loc, right=df_hours, how='left', on=['timeslice'], sort=False)
        #First we calculate p as annual $ for 1 kW flat-block tech,
        #so we need to multiply eq_supply_demand_balance price ($/MWh) by hours divided by 1000 (eq_reserve_margin price is fine as is) and sum across timeslices
        load_cond = df_bm_flat_loc['con_name'] == 'eq_supply_demand_balance'
        df_bm_flat_loc.loc[load_cond, 'p'] = df_bm_flat_loc.loc[load_cond, 'p'] * df_bm_flat_loc.loc[load_cond, 'hours'] / 1000
        df_bm_flat_loc = sum_over_cols(df_bm_flat_loc, group_cols=['year','rb','con_name'], val_cols=['p'])
        #Convert to $/MWh from $/kW: 1 kW flat block produces 8.76 MWh annual energy.
        df_bm_flat_loc['$ flat loc'] = df_bm_flat_loc['p'] / 8.76
        df_bm_flat_loc.drop(['p'], axis='columns', inplace=True)
        df = pd.merge(left=df, right=df_bm_flat_loc, how='left', on=['year','rb','con_name'], sort=False)

        #system flat benchmark. We weight the local prices by annual load
        df_bm_flat_sys = pd.merge(left=df_bm_flat_loc, right=df_load, how='left', on=['rb', 'year'], sort=False)
        df_bm_flat_sys['$'] = df_bm_flat_sys['$ flat loc'] * df_bm_flat_sys['q']
        df_bm_flat_sys = sum_over_cols(df_bm_flat_sys, group_cols=['con_name', 'year'], val_cols=['$','q'])
        df_bm_flat_sys['$ flat sys'] = df_bm_flat_sys['$'] / df_bm_flat_sys['q']
        df_bm_flat_sys.drop(['$','q'], axis='columns', inplace=True)
        df = pd.merge(left=df, right=df_bm_flat_sys, how='left', on=['year','con_name'], sort=False)

        #Merge with generation so we can calculate $ associated with all benchmarks
        df = pd.merge(left=df, right=df_gen, how='left', on=['tech','rb','year'], sort=False)
        #Now convert all prices to values
        vf_cols = ['$ all-in loc','$ all-in sys','$ flat loc','$ flat sys']
        df[vf_cols] = df[vf_cols].multiply(df['MWh'], axis="index")
        df.drop(['MWh'], axis='columns',inplace=True)
        df_gen['con_name'] = 'MWh'
        df_gen.rename(columns={'MWh': '$'}, inplace=True) #So we can concatenate
        for vf_col in vf_cols:
            df_gen[vf_col] = df_gen['$'] #Duplicating MWh across all the value columns
        df = pd.concat([df, df_gen],sort=False,ignore_index=True)
        df = df.fillna(0)
        return df

    #Use pvf_capital to convert to present value as of data year (model year for CAP and GEN but investment year for INV,
    #although i suppose certain equations, e.g. eq_cap_new_retmo also include previous year's CAP).
    df = pd.merge(left=dfs['vs'], right=dfs['pvf_cap'], how='left', on=['year'], sort=False)
    df['Bulk $'] = df['$'] / dfs['cost_scale'].iloc[0,0] / df['pvfcap']
    df.drop(['pvfcap', '$'], axis='columns',inplace=True)

    #Add total value and total cost
    # df_val = df[df['con_name'].isin(valuestreams)].copy()
    # df_val = sum_over_cols(df_val, group_cols=index_cols, drop_cols=['var_name','con_name'])
    # df_val['var_name'] = 'val_tot'
    # df_val['con_name'] = 'val_tot'
    # df_cost = df[df['con_name'].isin(coststreams)].copy()
    # df_cost = sum_over_cols(df_cost, group_cols=index_cols, drop_cols=['var_name','con_name'])
    # df_cost['var_name'] = 'cost_tot'
    # df_cost['con_name'] = 'cost_tot'
    # df = pd.concat([df, df_val, df_cost],sort=False,ignore_index=True)

    #Preprocess gen: convert from annual MWh to bulk MWh present value as of data year
    df_gen = dfs['gen'].groupby(index_cols, sort=False, as_index =False).sum()
    df_gen = pd.merge(left=df_gen, right=dfs['pvf_cap'], how='left', on=['year'], sort=False)
    df_gen = pd.merge(left=df_gen, right=dfs['pvf_onm'], how='left', on=['year'], sort=False)
    df_gen['MWh'] = df_gen['MWh'] * df_gen['pvfonm'] / df_gen['pvfcap'] #This converts to bulk MWh present value as of data year
    df_gen.rename(columns={'MWh': 'Bulk $'}, inplace=True) #So we can concatenate
    df_gen['var_name'] = 'MWh'
    df_gen['con_name'] = 'MWh'
    df_gen.drop(['pvfcap', 'pvfonm'], axis='columns',inplace=True)
    df = pd.concat([df, df_gen],sort=False,ignore_index=True)

    #Preprocess capacity: map i to n, convert from MW to kW, reformat columns to concatenate
    df_cap = map_rs_to_rb(dfs['cap'])
    df_cap =  df_cap.groupby(index_cols, sort=False, as_index =False).sum()
    df_cap['MW'] = df_cap['MW'] * 1000 #Converting to kW
    df_cap.rename(columns={'MW': 'Bulk $'}, inplace=True) #So we can concatenate
    df_cap['var_name'] = 'kW'
    df_cap['con_name'] = 'kW'
    df = pd.concat([df, df_cap],sort=False,ignore_index=True)
    
    #Add discounted $ using interface year
    d = float(core.GL['widgets']['var_discount_rate'].value)
    y0 = int(core.GL['widgets']['var_pv_year'].value)
    df['Bulk $ Dis'] = df['Bulk $'] / (1 + d)**(df['year'] - y0) #This discounts $, MWh, and kW, important for NVOE, NVOC, LCOE, etc.

    #Add new columns
    df['tech, vintage'] = df['tech'] + ', ' + df['vintage']
    df['var, con'] = df['var_name'] + ', ' + df['con_name']
    #Make adjusted con_name column where all _obj are replaced with var_name, _obj
    df['con_adj'] = df['con_name']
    df.loc[df['con_name'] == '_obj', 'con_adj'] = df.loc[df['con_name'] == '_obj', 'var, con']

    if 'competitiveness' in kw:
        df = df[index_cols+['Bulk $ Dis','con_name']]

        #Total cost for each tech
        df_cost = df[df['con_name'].isin(coststreams)].copy()
        df_cost.rename(columns={'Bulk $ Dis':'Cost $'}, inplace=True)
        df_cost = sum_over_cols(df_cost, group_cols=index_cols, drop_cols=['con_name'])
        df_cost['Cost $'] = df_cost['Cost $'] * -1

        #Total Value for each tech
        df_value = df[df['con_name'].isin(vf_valstreams)].copy()
        df_value.rename(columns={'Bulk $ Dis':'Value $'}, inplace=True)
        df_value = sum_over_cols(df_value, group_cols=index_cols, drop_cols=['con_name'])

        #Total energy for each tech
        df_energy = df[df['con_name'] == 'MWh'].copy()
        df_energy.rename(columns={'Bulk $ Dis':'MWh'}, inplace=True)
        df_energy = sum_over_cols(df_energy, group_cols=index_cols, drop_cols=['con_name'])

        #Benchmark price, excluding national_generation constraint, with the assumption that this constraint
        #represents a simple forcing function rather than a policy. If the constraint represents a CES or RPS policy e.g.,
        #we probably should use 'tot' rather than the sum of 'load','res_marg','oper_res', and 'state_rps'.
        df_benchmark = pre_prices(dfs)
        df_benchmark = df_benchmark[df_benchmark['type'].isin(['q_load','load','res_marg','oper_res','state_rps'])].copy()
        df_benchmark = sum_over_cols(df_benchmark, group_cols=['type','year'], val_cols=['$'])
        df_benchmark = df_benchmark.pivot_table(index=['year'], columns=['type'], values='$').reset_index()
        df_benchmark['P_b'] = (df_benchmark['load'] + df_benchmark['res_marg'] + df_benchmark['oper_res'] + df_benchmark['state_rps']) / df_benchmark['q_load']
        df_benchmark = df_benchmark[['year','P_b']].copy()

        #Merge all the dataframes
        df = pd.merge(left=df_cost, right=df_energy, how='left', on=index_cols, sort=False)
        df = pd.merge(left=df, right=df_value, how='left', on=index_cols, sort=False)
        df = pd.merge(left=df, right=df_benchmark, how='left', on=['year'], sort=False)

        #Build metrics
        df['LCOE'] = df['Cost $'] / df['MWh']
        df['LVOE'] = df['Value $'] / df['MWh']
        df['NVOE'] = df['LVOE'] - df['LCOE']
        df['BCR'] = df['Value $'] / df['Cost $']
        df['PLCOE'] = df['P_b'] * df['Cost $'] / df['Value $']
        df['value factor'] = df['LVOE'] / df['P_b']
        df['integration cost'] = df['P_b'] - df['LVOE']
        df['SLCOE'] = df['LCOE'] + df['integration cost']
        df.replace([np.inf, -np.inf], np.nan, inplace=True)

    return df

def pre_reduced_cost(df, **kw):
    df['irbv'] = df['tech'] + ' | ' + df['region'] + ' | ' + df['bin'] + ' | ' + df['variable']
    return df

def pre_lcoe(dfs, **kw):
    #Apply inflation
    dfs['lcoe']['$/MWh'] = inflate_series(dfs['lcoe']['$/MWh'])
    #Merge with available capacity
    df = pd.merge(left=dfs['lcoe'], right=dfs['avail'], how='left', on=['tech', 'region', 'year', 'bin'], sort=False)
    df['available MW'].fillna(0, inplace=True)
    df['available'] = 'no'
    df.loc[df['available MW'] > 0.001, 'available'] = 'yes'
    #Merge with chosen capacity
    df = pd.merge(left=df, right=dfs['inv'], how='left', on=['tech', 'vintage', 'region', 'year', 'bin'], sort=False)
    df['chosen MW'].fillna(0, inplace=True)
    df['chosen'] = 'no'
    df.loc[df['chosen MW'] != 0, 'chosen'] = 'yes'
    #Add icrb column
    df['icrb'] = df['tech'] + ' | ' + df['vintage'] + ' | ' + df['region'] + ' | ' + df['bin']
    return df

def pre_curt_new(dfs, **kw):
    df = pd.merge(left=dfs['gen_uncurt'], right=dfs['curt_rate'], how='left',on=['tech', 'region', 'timeslice', 'year'], sort=False)
    df['Curt Rate']=df['Curt Rate'].fillna(0)
    if 'annual' in kw:
        df['MWh curt'] = df['Curt Rate'] * df['MWh uncurt']
        df = sum_over_cols(df, group_cols=['tech', 'region', 'year'], drop_cols=['timeslice','Curt Rate'])
        df['Curt Rate'] = df['MWh curt'] / df['MWh uncurt']
        df['Curt Rate']=df['Curt Rate'].fillna(0)
    return df

def pre_cc_new(dfs, **kw):
    df = pd.merge(left=dfs['cap'], right=dfs['cc'], how='left',on=['tech', 'region', 'season', 'year'], sort=False)
    df['CC Rate']=df['CC Rate'].fillna(0)
    return df

def pre_firm_cap(dfs, **kw):
    #aggregate capacity to ba-level
    df_cap = map_rs_to_rb(dfs['cap'], groupsum=['tech','rb','year'])
    #Add seasons to capacity dataframe
    dftemp = pd.DataFrame({'season':dfs['firmcap']['season'].unique().tolist()})
    dftemp['temp'] = 1
    df_cap['temp'] = 1
    df_cap = pd.merge(left=df_cap, right=dftemp, how='left',on=['temp'], sort=False)
    df_cap.drop(columns=['temp'],inplace=True)
    df = pd.merge(left=df_cap, right=dfs['firmcap'], how='left',on=['tech', 'rb', 'year','season'], sort=False)
    df = df.fillna(0)
    df[['Capacity (GW)','Firm Capacity (GW)']] = df[['Capacity (GW)','Firm Capacity (GW)']] * 1e-3
    df['Capacity Credit'] = df['Firm Capacity (GW)'] / df['Capacity (GW)']
    return df

def pre_curt(dfs, **kw):
    df = pd.merge(left=dfs['gen_uncurt'], right=dfs['gen'], how='left',on=['tech', 'vintage', 'rb', 'year'], sort=False)
    df['MWh']=df['MWh'].fillna(0)
    df['Curt Rate'] = 1 - df['MWh']/df['MWh uncurt']
    df_re_n = sum_over_cols(dfs['gen_uncurt'], group_cols=['rb','year'], drop_cols=['tech','vintage'])
    df_re_nat = sum_over_cols(dfs['gen_uncurt'], group_cols=['year'], drop_cols=['tech','vintage','rb'])
    df_load_nat = sum_over_cols(dfs['load'], group_cols=['year'], drop_cols=['rb'])
    df_vrepen_n = pd.merge(left=dfs['load'], right=df_re_n, how='left',on=['rb', 'year'], sort=False)
    df_vrepen_n['VRE penetration n'] = df_vrepen_n['MWh uncurt'] / df_vrepen_n['MWh load']
    df_vrepen_n = df_vrepen_n[['rb','year','VRE penetration n']]
    df_vrepen_nat = pd.merge(left=df_load_nat, right=df_re_nat, how='left',on=['year'], sort=False)
    df_vrepen_nat['VRE penetration nat'] = df_vrepen_nat['MWh uncurt'] / df_vrepen_nat['MWh load']
    df_vrepen_nat = df_vrepen_nat[['year','VRE penetration nat']]
    df = pd.merge(left=df, right=df_vrepen_n, how='left',on=['rb', 'year'], sort=False)
    df = pd.merge(left=df, right=df_vrepen_nat, how='left',on=['year'], sort=False)
    return df

def pre_curt_iter(dfs, **kw):
    df_gen = dfs['gen_uncurt']
    df_curt = dfs['curt']
    df_gen = df_gen[df_gen['tech'].isin(df_curt['tech'].unique())].copy()
    df_gen['type'] = 'gen'
    df_curt['type'] = 'curt'
    df = pd.concat([df_gen, df_curt],sort=False,ignore_index=True)
    return df

def pre_cc_iter(dfs, **kw):
    df_cap = dfs['cap']
    df_cap_firm = dfs['cap_firm']
    df_cap = df_cap[df_cap['tech'].isin(df_cap_firm['tech'].unique())].copy()
    df_cap['type'] = 'cap'
    df_cap_firm['type'] = 'cap_firm'
    seasons = list(df_cap_firm['season'].unique())
    df_season = pd.DataFrame({'season':seasons,'temp':[1]*len(seasons)})
    df_cap['temp'] = 1
    df_cap = pd.merge(left=df_cap, right=df_season, how='left',on=['temp'], sort=False)
    df_cap.drop(['temp'], axis='columns',inplace=True)
    df = pd.concat([df_cap, df_cap_firm],sort=False,ignore_index=True)
    return df

def pre_cf(dfs, **kw):
    index_cols = ['tech', 'vintage', 'rb', 'year']
    dfs['cap'] = map_rs_to_rb(dfs['cap'])
    dfs['cap'] =  dfs['cap'].groupby(index_cols, sort=False, as_index=False).sum()
    df = pd.merge(left=dfs['cap'], right=dfs['gen'], how='left',on=index_cols, sort=False)
    df['MWh']=df['MWh'].fillna(0)
    df['CF'] = df['MWh']/(df['MW']*8760)
    return df

def pre_new_vre_cf(dfs, **kw):
    index_cols = ['tech', 'rs', 'year']
    dfs['gen_new_uncurt'] = sum_over_cols(dfs['gen_new_uncurt'], group_cols=index_cols, val_cols=['MWh'])
    df = pd.merge(left=dfs['gen_new_uncurt'], right=dfs['cap_new'], how='inner',on=index_cols, sort=False)
    df['CF'] = df['MWh']/(df['MW']*8760)
    return df

def pre_prices(dfs, **kw):
    #Apply inflation
    dfs['p']['p'] = inflate_series(dfs['p']['p'])
    #Join prices and quantities
    df = pd.merge(left=dfs['q'], right=dfs['p'], how='left', on=['type', 'subtype', 'rb', 'timeslice', 'year'], sort=False)
    df['p'].fillna(0, inplace=True)
    #Calculate $
    df['$'] = df['p'] * df['q']
    df.drop(['p', 'q'], axis='columns',inplace=True)
    #Calculate total $
    df_tot = df[df['type'].isin(price_types)].copy()
    df_tot = df_tot.groupby(['rb', 'timeslice', 'year'], sort=False, as_index=False).sum()
    df_tot['type'] = 'tot'
    df_tot['subtype'] = 'na'
    #Reformat quantities
    df_q = dfs['q']
    df_q.rename(columns={'q':'$'}, inplace=True)
    df_q['type'] = 'q_' + df_q['type']
    #Concatenate all dataframes
    df = pd.concat([df, df_tot, df_q],sort=False,ignore_index=True)
    return df

def pre_ng_price(dfs, **kw):
    #Apply inflation
    dfs['p']['p'] = inflate_series(dfs['p']['p'])
    #Join prices and quantities
    df = pd.merge(left=dfs['q'], right=dfs['p'], how='left', on=['census', 'year'], sort=False)
    df['p'].fillna(0, inplace=True)
    return df

def add_joint_locations_col(df, **kw):
    df[kw['new']] = df[kw['col1']] + '-' + df[kw['col2']]
    return df
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------

#2. Columns metadata. These are columns that are referenced in the Results section below.
#This is where joins, maps, and styles are applied for the columns.
#For 'style', colors are in hex, but descriptions are given (see http://www.color-hex.com/color-names.html).
#raw and display tech mappings for appending in tech_map.csv for coolingwatertech are given in:
#(https://github.nrel.gov/ReEDS/NEMS_Unit_Database_Water_Sources/blob/master/coolingtech/append2tech_map.csv)
columns_meta = {
    'tech':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/tech_map.csv',
        'style': this_dir_path + '/in/reeds2/tech_style.csv',
    },
    'class':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/class_map.csv',
        'style': this_dir_path + '/in/reeds2/class_style.csv',
    },
    'region':{
        'type':'string',
    },
    'rs':{
        'type':'string',
        'join': this_dir_path + '/in/reeds2/hierarchy.csv',
    },
    'rb':{
        'type':'string',
        'join': this_dir_path + '/in/reeds2/hierarchy.csv',
    },
    'timeslice':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/m_map.csv',
        'style': this_dir_path + '/in/reeds2/m_style.csv',
    },
    'year':{
        'type':'number',
        'filterable': True,
        'seriesable': True,
        'y-allow': False,
    },
    'iter':{
        'type':'string',
    },
    'icrb':{
        'type': 'string',
        'filterable': False,
        'seriesable': False,
    },
    'irbv':{
        'type': 'string',
        'filterable': False,
        'seriesable': False,
    },
    'cost_cat':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/cost_cat_map.csv',
        'style': this_dir_path + '/in/reeds2/cost_cat_style.csv',
    },
    'con_adj':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/con_adj_map.csv',
        'style': this_dir_path + '/in/reeds2/con_adj_style.csv',
    },
    'wst':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/wst_map.csv',
        'style': this_dir_path + '/in/reeds2/wst_style.csv',
    },
    'ctt':{
        'type':'string',
        'map': this_dir_path + '/in/reeds2/ctt_map.csv',
        'style': this_dir_path + '/in/reeds2/ctt_style.csv',
    },
}

#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------

#3. Results metadata. This is where all ReEDS results are defined. Parameters are read from gdx files, and
#are converted into pandas dataframes for pivoting. Preprocess functions may be used to perform additional manipulation.
#Note that multiple parameters may be read in for the same result (search below for 'sources')
#Presets may also be defined.
results_meta = collections.OrderedDict((
    ('Capacity National (GW)',
        {'file':'cap.csv',
        'columns': ['tech', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': sum_over_cols, 'args': {'drop_cols': ['region'], 'group_cols': ['tech', 'year']}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Capacity BA (GW)',
        {'file':'cap.csv',
        'columns': ['tech', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': map_rs_to_rb, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'rb', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Capacity BA by class (GW)',
        {'file':'cap.csv',
        'columns': ['tech', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': add_class, 'args': {}},
            {'func': map_rs_to_rb, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
        )),
        }
    ),

    ('Capacity icrt (GW)',
        {'file':'cap_icrt.csv',
        'columns': ['tech', 'vintage', 'region', 'year','Capacity (GW)'],
        'preprocess': [
            {'func': map_rs_to_rb, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('New Annual Capacity National (GW)',
        {'file':'cap_new_ann.csv',
        'columns': ['tech', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': sum_over_cols, 'args': {'drop_cols': ['region'], 'group_cols': ['tech', 'year']}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('New Annual Capacity BA (GW)',
        {'file':'cap_new_ann.csv',
        'columns': ['tech', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': map_rs_to_rb, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'rb', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Annual Retirements National (GW)',
        {'file':'ret_ann.csv',
        'columns': ['tech', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': sum_over_cols, 'args': {'drop_cols': ['region'], 'group_cols': ['tech', 'year']}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Annual Retirements BA (GW)',
        {'file':'ret_ann.csv',
        'columns': ['tech', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': map_rs_to_rb, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'rb', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Exogenous capacity (GW)',
        {'file':'m_capacity_exog.csv',
        'columns': ['tech', 'vintage', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': map_rs_to_rb, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Capacity Resource Region (GW)',
        {'file':'cap.csv',
        'columns': ['tech', 'region', 'year', 'Capacity (GW)'],
        'preprocess': [
            {'func': remove_ba, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'index': ['tech', 'rs', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('RS Map Final by Tech',{'x':'rs', 'y':'Capacity (GW)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('RS Map Final Wind',{'x':'rs', 'y':'Capacity (GW)', 'explode':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last', 'tech':['wind-ons', 'wind-ofs']}}),
        )),
        }
    ),

    ('Generation National (TWh)',
        {'file':'gen_ann.csv',
        'columns': ['tech', 'rb', 'year', 'Generation (TWh)'],
        'preprocess': [
            {'func': sum_over_cols, 'args': {'drop_cols': ['rb'], 'group_cols': ['tech', 'year']}},
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Generation (TWh)'}},
        ],
        'index': ['tech', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars Gen Frac',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'tech', 'adv_col_base':'Total'}),
            ('Explode By Tech',{'x':'year', 'y':'Generation (TWh)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Generation BA (TWh)',
        {'file':'gen_ann.csv',
        'columns': ['tech', 'rb', 'year', 'Generation (TWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Generation (TWh)'}},
        ],
        'index': ['tech', 'rb', 'year'],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Stacked Bars Gen Frac',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'tech', 'adv_col_base':'Total'}),
            ('Explode By Tech',{'x':'year', 'y':'Generation (TWh)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Generation (TWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Generation (TWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Generation icrt (TWh)',
        {'file':'gen_icrt.csv',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Generation (TWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Generation (TWh)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Generation (TWh)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Generation (TWh)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Generation (TWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Generation (TWh)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Water Withdrawal ivrt (Bgal)',
        {'file':'water_withdrawal_ivrt.csv',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Water Withdrawal (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'Water Withdrawal (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Water Withdrawal (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Water Withdrawal (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Water Withdrawal (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Water Withdrawal (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Water Withdrawal (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Water Consumption ivrt (Bgal)',
        {'file':'water_consumption_ivrt.csv',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Water Consumption (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'Water Consumption (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Water Consumption (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Water Consumption (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Water Consumption (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Water Consumption (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Water Consumption (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Water Capacity ivrt (Bgal)',
        {'file':'watcap_ivrt.csv',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Water Capacity (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'Water Capacity (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Water Capacity (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Water Capacity by Region irt (Bgal)',
        {'file':'watcap_out.csv',
        'columns': ['tech', 'rb', 'year', 'Water Capacity by Region (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'Water Capacity by Region (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('New Water Capacity (Bgal)',
        {'file':'watcap_new_ivrt.csv',
        'columns': ['tech', 'vintage', 'rb', 'year', 'New Water Capacity (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'New Water Capacity (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'New Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'New Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'New Water Capacity (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'New Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'New Water Capacity (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('New Water Capacity by Region irt (Bgal)',
        {'file':'watcap_new_out.csv',
        'columns': ['tech', 'rb', 'year', 'New Water Capacity by Region (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'New Water Capacity by Region (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'New Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'New Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'New Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'New Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'New Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('New Annual Water Capacity by Region ivrt (Bgal)',
        {'file':'watcap_new_ann_out.csv',
        'columns': ['tech', 'vintage', 'rb', 'year', 'New Annual Water Capacity by Region (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-3, 'column':'New Annual Water Capacity by Region (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'New Annual Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'New Annual Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'New Annual Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'New Annual Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'New Annual Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Retired Water Capacity by Region irt (Bgal)',
        {'file':'watret_out.csv',
        'columns': ['tech', 'rb', 'year', 'Retired Water Capacity by Region (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-9, 'column':'Retired Water Capacity by Region (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Retired Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Retired Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Retired Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Retired Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Retired Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Retired Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Retired Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Retired Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Retired Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Retired Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Annual Retired Water Capacity by Region ivrt (Bgal)',
        {'file':'watret_ann_out.csv',
        'columns': ['tech', 'vintage', 'rb', 'year', 'Annual Retired Water Capacity by Region (Bgal)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-9, 'column':'Annual Retired Water Capacity by Region (Bgal)'}},
            {'func': add_cooling_water, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'tech', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'tech', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('Stacked Area by Water Source Type',{'x':'year', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars by Water Source Type',{'x':'year', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'series':'wst', 'explode':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Water Source Type',{'x':'year', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'series':'scenario', 'explode':'wst', 'chart_type':'Line'}),
            ('PCA Map Final by Water Source Type',{'x':'rb', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Water Source Type',{'x':'st', 'y':'Annual Retired Water Capacity by Region (Bgal)', 'explode':'scenario', 'explode_group':'wst', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Gen by timeslice national (GW)',
        {'file':'gen_h.csv',
        'columns': ['tech', 'region', 'timeslice', 'year', 'Generation (GW)'],
        'index': ['tech', 'year', 'timeslice'],
        'preprocess': [
            {'func': map_rs_to_rb, 'args': {}},
            {'func': sum_over_cols, 'args': {'drop_cols': ['rb'], 'group_cols': ['tech', 'year', 'timeslice']}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Generation (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars Final',{'x':'timeslice', 'y':'Generation (GW)', 'series':'tech', 'explode':'scenario', 'chart_type':'Bar', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Capacity Factor icrt',
        {'sources': [
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year','MWh']},
            {'name': 'cap', 'file': 'cap_icrt.csv', 'columns': ['tech', 'vintage', 'region', 'year','MW']},
        ],
        'preprocess': [
            {'func': pre_cf, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('CF Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'CF', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'y_min':'0','y_max':'1', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('CF weighted ave',{'chart_type':'Line', 'x':'year', 'y':'CF', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MW', 'explode':'tech', 'series':'scenario', 'y_min':'0','y_max':'1', }),
        )),
        }
    ),

    ('New VRE CF uncurt',
        {'sources': [
            {'name': 'gen_new_uncurt', 'file': 'gen_new_uncurt.csv', 'columns': ['tech', 'rs', 'timeslice', 'year', 'MWh']},
            {'name': 'cap_new', 'file':'cap_new_out.csv', 'columns': ['tech', 'rs', 'year', 'MW']},
        ],
        'preprocess': [
            {'func': pre_new_vre_cf, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('CF weighted ave',{'chart_type':'Line', 'x':'year', 'y':'CF', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MW', 'explode':'tech', 'series':'scenario', 'y_min':'0','y_max':'1', }),
            ('CF Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'CF', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'y_min':'0','y_max':'1', 'circle_size':r'3', 'bar_width':r'1.75', }),
        )),
        }
    ),

    ('Storage Charge/Discharge (TWh)',
        {'file':'stor_inout.csv',
        'columns': ['tech', 'vintage', 'region', 'year', 'type', 'TWh'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'TWh'}},
        ],
        'presets': collections.OrderedDict((
            ('Explode By Tech',{'x':'year', 'y':'TWh', 'series':'scenario', 'explode':'type', 'explode_group':'tech', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Operating Reserves (TW-h)',
        {'file':'opres_supply.csv',
        'columns': ['ortype', 'tech', 'region', 'year', 'Reserves (TW-h)'],
        'index': ['ortype', 'tech', 'year'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Reserves (TW-h)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'Reserves (TW-h)', 'series':'tech', 'explode':'scenario', 'explode_group':'ortype', 'chart_type':'Bar', 'bar_width':'1.75', }),
        )),
        }
    ),

    ('Operating Reserves by Timeslice National (GW)',
        {'file':'opres_supply_h.csv',
        'columns': ['ortype', 'tech', 'region', 'timeslice', 'year', 'Reserves (GW)'],
        'index': ['ortype', 'tech', 'year', 'timeslice'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Reserves (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars Final',{'x':'timeslice', 'y':'Reserves (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'ortype', 'chart_type':'Bar', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Firm Capacity National (GW)',
        {'sources': [
            {'name': 'firmcap', 'file': 'cap_firm.csv', 'columns': ['tech', 'rb', 'season', 'year', 'Firm Capacity (GW)']},
            {'name': 'cap', 'file': 'cap.csv', 'columns': ['tech', 'region', 'year', 'Capacity (GW)']},
        ],
        'index': ['tech', 'season', 'year'],
        'preprocess': [
            {'func': pre_firm_cap, 'args': {}},
            {'func': sum_over_cols, 'args': {'drop_cols': ['rb'], 'group_cols': ['tech', 'season', 'year']}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'Firm Capacity (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'season', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Average Capacity Credit',{'x':'year', 'y':'Capacity Credit', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Capacity (GW)', 'series':'scenario', 'explode':'season', 'explode_group':'tech', 'chart_type':'Line'}),
            ('Average Capacity Credit CC Techs',{'x':'year', 'y':'Capacity Credit', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Capacity (GW)', 'series':'scenario', 'explode':'season', 'explode_group':'tech', 'chart_type':'Line', 'filter':{'tech':cc_techs}}),
        )),
        }
    ),

    ('Firm Capacity BA (GW)',
        {'sources': [
            {'name': 'firmcap', 'file': 'cap_firm.csv', 'columns': ['tech', 'rb', 'season', 'year', 'Firm Capacity (GW)']},
            {'name': 'cap', 'file': 'cap.csv', 'columns': ['tech', 'region', 'year', 'Capacity (GW)']},
        ],
        'index': ['tech', 'rb', 'season', 'year'],
        'preprocess': [
            {'func': pre_firm_cap, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'Firm Capacity (GW)', 'series':'tech', 'explode':'scenario', 'explode_group':'season', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Average Capacity Credit',{'x':'year', 'y':'Capacity Credit', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Capacity (GW)', 'series':'scenario', 'explode':'season', 'explode_group':'tech', 'chart_type':'Line'}),
            ('Average Capacity Credit CC Techs',{'x':'year', 'y':'Capacity Credit', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Capacity (GW)', 'series':'scenario', 'explode':'season', 'explode_group':'tech', 'chart_type':'Line', 'filter':{'tech':cc_techs}}),
        )),
        }
    ),

    ('CO2 Emissions National (MMton)',
        {'file':'emit_nat.csv',
        'columns': ['year', 'CO2 (MMton)'],
        'preprocess': [
        ],
        'index': ['year'],
        'presets': collections.OrderedDict((
            ('Scenario Lines Over Time',{'x':'year', 'y':'CO2 (MMton)', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('CO2 Emissions BA (MMton)',
        {'file':'emit_r.csv',
        'columns': ['rb', 'year', 'CO2 (MMton)'],
        'preprocess': [
        ],
        'index': ['rb', 'year'],
        'presets': collections.OrderedDict((
            ('Final BA Map',{'x':'rb', 'y':'CO2 (MMton)', 'explode':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Natural Gas Price ($/MMBtu)',
        {'sources': [
            {'name': 'p', 'file': 'repgasprice.csv', 'columns': ['census', 'year', 'p']},
            {'name': 'q', 'file': 'repgasquant.csv', 'columns': ['census', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_ng_price, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'p', 'y_agg':'None', 'range':'Boxplot', 'explode':'scenario', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('Weighted Average',{'chart_type':'Line', 'x':'year', 'y':'p', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'q', 'series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('Requirement Prices and Quantities National',
        {'sources': [
            {'name': 'p', 'file': 'reqt_price.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_prices, 'args': {}},
            {'func': sum_over_cols, 'args': {'drop_cols': ['rb'], 'group_cols': ['type', 'subtype', 'timeslice', 'year']}},
        ],
        'presets': collections.OrderedDict((
            ('Energy Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load']}}),
            ('OpRes Price Lines ($/MW-h)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'subtype', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res']}}),
            ('ResMarg Price Lines ($/kW-yr)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg_ann', 'filter': {'type':['res_marg_ann','q_res_marg_ann']}}),
            ('ResMarg Season Price Lines ($/kW-yr)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'timeslice', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg', 'filter': {'type':['res_marg','q_res_marg']}}),
            ('National RPS Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_nat_gen', 'filter': {'type':['nat_gen','q_nat_gen']}}),
            ('CO2 Price Lines ($/metric ton)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_annual_cap', 'y_scale':'1e-6', 'filter': {'type':['annual_cap','q_annual_cap'],'subtype':['co2']}}),
            ('Energy Price by Timeslice Final ($/MWh)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load'], 'year':'last'}}),
            ('OpRes Price by Timeslice Final ($/MW-h)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'subtype', 'explode_group':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res'], 'year':'last'}}),
            ('Bulk System Electricity Price ($/MWh)',{'x':'year', 'y':'$', 'series':'type', 'explode': 'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': price_types+['q_load']}}),
            ('Total Bulk System Electricity Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': ['tot', 'q_load']}}),
        )),
        }
    ),

    ('Requirement Prices and Quantities BA',
        {'sources': [
            {'name': 'p', 'file': 'reqt_price.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_prices, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Energy Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load']}}),
            ('OpRes Price Lines ($/MW-h)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'subtype', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res']}}),
            ('ResMarg Price Lines ($/kW-yr)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg_ann', 'filter': {'type':['res_marg_ann','q_res_marg_ann']}}),
            ('ResMarg Season Price Lines ($/kW-yr)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'timeslice', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_res_marg', 'filter': {'type':['res_marg','q_res_marg']}}),
            ('National RPS Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_nat_gen', 'filter': {'type':['nat_gen','q_nat_gen']}}),
            ('CO2 Price Lines ($/metric ton)',{'x':'year', 'y':'$', 'series':'scenario', 'explode': 'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_annual_cap', 'y_scale':'1e-6', 'filter': {'type':['annual_cap','q_annual_cap'],'subtype':['co2']}}),
            ('Energy Price by Timeslice Final ($/MWh)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load'], 'year':'last'}}),
            ('OpRes Price by Timeslice Final ($/MW-h)',{'x':'timeslice', 'y':'$', 'series':'type', 'explode':'subtype', 'explode_group':'scenario', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_oper_res', 'filter': {'type':['oper_res','q_oper_res'], 'year':'last'}}),
            ('Energy Price Final BA Map ($/MWh)',{'x':'rb', 'y':'$', 'explode': 'scenario', 'explode_group': 'type', 'chart_type':'Area Map', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type':['load','q_load'], 'year':'last'}}),
            ('Bulk System Electricity Price ($/MWh)',{'x':'year', 'y':'$', 'series':'type', 'explode': 'scenario', 'chart_type':'Bar', 'bar_width':'1.75', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': price_types+['q_load']}}),
            ('Total Bulk System Electricity Price Lines ($/MWh)',{'x':'year', 'y':'$', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'q_load', 'filter': {'type': ['tot', 'q_load']}}),
        )),
        }
    ),

    ('Sys Cost Objective (Bil $)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost.csv', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
        ],
        'index': ['cost_cat', 'year'],
        'preprocess': [
            {'func': pre_systemcost, 'args': {'objective':True}},
        ],
        'presets': collections.OrderedDict((
            ('Cost by Year',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Cost by Year No Pol',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
        )),
        }
    ),

    ('Sys Cost beyond final year (Bil $)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost_bulk.csv', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
        ],
        'index': ['cost_cat', 'year'],
        'preprocess': [
            {'func': pre_systemcost, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Total Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Total Discounted No Pol',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
            ('2018-end Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_orig_inv}, 'year': {'start':2018}}}),
            ('2018-end Discounted No Pol',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_pol_inv}, 'year': {'start':2018}}}),
            ('Discounted by Year',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Discounted by Year No Pol',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
            ('Undiscounted by Year',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Undiscounted by Year No Pol',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
        )),
        }
    ),

    ('Sys Cost truncated at final year (Bil $)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost_bulk_ew.csv', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
        ],
        'index': ['cost_cat', 'year'],
        'preprocess': [
            {'func': pre_systemcost, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Total Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Total Discounted No Pol',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
            ('2018-end Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_orig_inv}, 'year': {'start':2018}}}),
            ('2018-end Discounted No Pol',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_pol_inv}, 'year': {'start':2018}}}),
            ('Discounted by Year',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Discounted by Year No Pol',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
            ('Undiscounted by Year',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Undiscounted by Year No Pol',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
        )),
        }
    ),

    ('Sys Cost Annualized (Bil $)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost.csv', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'existcap', 'file': '../inputs_case/cappayments.csv', 'columns': ['year', 'existingcap']},
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'header': None, 'columns': ['year', 'crf']},

        ],
        'index': ['cost_cat', 'year'],
        'preprocess': [
            {'func': pre_systemcost, 'args': {'annualize':True}},
        ],
        'presets': collections.OrderedDict((
            ('Total Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Total Discounted No Pol',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
            ('2020-2050 Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_orig_inv}, 'year': {'start':2020, 'end':2050}}}),
            ('2020-2050 Discounted No Pol',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_pol_inv}, 'year': {'start':2020, 'end':2050}}}),
            ('2018-end Discounted',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_orig_inv}, 'year': {'start':2018}}}),
            ('2018-end Discounted No Pol',{'x':'scenario','y':'Discounted Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_pol_inv}, 'year': {'start':2018}}}),
            ('Discounted by Year',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Discounted by Year No Pol',{'x':'year','y':'Discounted Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
            ('Total Undiscounted',{'x':'scenario','y':'Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Total Undiscounted No Pol',{'x':'scenario','y':'Cost (Bil $)','series':'cost_cat','chart_type':'Bar', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
            ('Undiscounted by Year',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Undiscounted by Year No Pol',{'x':'year','y':'Cost (Bil $)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
        )),
        }
    ),

    ('National Average Electricity Cost ($/MWh)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost.csv', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'q', 'file': 'reqt_quant.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
            {'name': 'existcap', 'file': '../inputs_case/cappayments.csv', 'columns': ['year', 'existingcap']},
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'header': None, 'columns': ['year', 'crf']},
        ],
        'preprocess': [
            {'func': pre_avgprice, 'args': {'National':True}},
        ],
        'presets': collections.OrderedDict((
            ('Average Electricity Cost by Year ($/MWh)',{'x':'year','y':'Average cost ($/MWh)','series':'cost_cat','explode':'scenario','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
        )),
        }
    ),

    ('BA-level Average Electricity Cost ($/MWh)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost_ba.csv', 'columns': ['cost_cat','region', 'year', 'Cost (Bil $)']},
            {'name': 'q', 'file': 'reqt_quant.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
            {'name': 'p', 'file': 'reqt_price.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'gen', 'file': 'gen_h.csv', 'columns': ['tech', 'r', 'timeslice', 'year', 'Generation (GW)']},
            {'name': 'existcap', 'file': '../inputs_case/cappayments_ba.csv', 'columns': ['region', 'year','existingcap']},
            {'name': 'captrade', 'file': 'captrade.csv', 'columns': ['rb_out', 'rb_in', 'type', 'season', 'year', 'Amount (MW)']},
            {'name': 'powerfrac_downstream', 'file': 'powerfrac_downstream.csv', 'columns': ['rr', 'r', 'timeslice', 'year', 'frac']},
            {'name': 'powerfrac_upstream', 'file': 'powerfrac_upstream.csv', 'columns': ['r', 'rr', 'timeslice', 'year', 'frac']},
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'header': None, 'columns': ['year', 'crf']},
        ],
        'preprocess': [
            {'func': pre_avgprice, 'args': {'BA':True}},
        ],
        'presets': collections.OrderedDict((
            ('Average BA-level Electricity Cost by Year ($/MWh)',{'x':'year','y':'Average cost ($/MWh)','series':'cost_cat','explode':'rb','chart_type':'Bar', 'bar_width':'1.75', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
        )),
        }
    ),

    ('CO2 Abatement Cost ($/metric ton)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost.csv', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'emit', 'file': 'emit_nat.csv', 'columns': ['year', 'CO2 (MMton)']},
            {'name': 'crf', 'file': '../inputs_case/crf.csv', 'header': None, 'columns': ['year', 'crf']},
        ],
        'preprocess': [
            {'func': pre_abatement_cost, 'args': {'annualize':True}},
        ],
        'presets': collections.OrderedDict((
            #To work properly, these presets require selecting the correct scenario for the Advanced Operation base.
            ('Cumulative Undiscounted Over Time',{'x':'year','y':'cum val','series':'scenario','chart_type':'Line', 'explode':'type', 'adv_op':'Difference', 'adv_col':'scenario', 'adv_col_base':'None', 'adv_op2': 'Ratio', 'adv_col2': 'type', 'adv_col_base2': 'CO2 (Bil metric ton)', 'y_scale':'-1', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Cumulative Undiscounted Over Time No Pol',{'x':'year','y':'cum val','series':'scenario','chart_type':'Line', 'explode':'type', 'adv_op':'Difference', 'adv_col':'scenario', 'adv_col_base':'None', 'adv_op2': 'Ratio', 'adv_col2': 'type', 'adv_col_base2': 'CO2 (Bil metric ton)', 'y_scale':'-1', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
            ('Cumulative Discounted Over Time',{'x':'year','y':'cum disc val','series':'scenario','chart_type':'Line', 'explode':'type', 'adv_op':'Difference', 'adv_col':'scenario', 'adv_col_base':'None', 'adv_op2': 'Ratio', 'adv_col2': 'type', 'adv_col_base2': 'CO2 (Bil metric ton)', 'y_scale':'-1', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
            ('Cumulative Discounted Over Time No Pol',{'x':'year','y':'cum disc val','series':'scenario','chart_type':'Line', 'explode':'type', 'adv_op':'Difference', 'adv_col':'scenario', 'adv_col_base':'None', 'adv_op2': 'Ratio', 'adv_col2': 'type', 'adv_col_base2': 'CO2 (Bil metric ton)', 'y_scale':'-1', 'filter': {'cost_cat':{'exclude':costs_pol_inv}}}),
        )),
        }
    ),

    ('CO2 Abatement Cost Objective ($/metric ton)',
        {'sources': [
            {'name': 'sc', 'file': 'systemcost.csv', 'columns': ['cost_cat', 'year', 'Cost (Bil $)']},
            {'name': 'emit', 'file': 'emit_nat.csv', 'columns': ['year', 'CO2 (MMton)']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
        ],
        'preprocess': [
            {'func': pre_abatement_cost, 'args': {'objective':True}},
        ],
        'presets': collections.OrderedDict((
            #To work properly, these presets require selecting the correct scenario for the Advanced Operation base.
            ('Abatement Cost By Year',{'x':'year','y':'val','series':'scenario','chart_type':'Line', 'explode':'type', 'adv_op':'Difference', 'adv_col':'scenario', 'adv_col_base':'None', 'adv_op2': 'Ratio', 'adv_col2': 'type', 'adv_col_base2': 'CO2 (Bil metric ton)', 'y_scale':'-1', 'filter': {'cost_cat':{'exclude':costs_orig_inv}}}),
        )),
        }
    ),

    ('Value Streams Sequential New Techs',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_new_icrt.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale.csv', 'columns': ['cs']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'investment_only':True}},
        ],
        'presets': collections.OrderedDict((
            ('NVOE over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'bar_width':'1.75', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOE final', {'x':'rb','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['kW']}}}),
            ('NVOE final nat', {'x':'tech','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['kW']}}}),
            ('NVOE final nat tech explode', {'x':'scenario','y':'Bulk $ Dis','series':'con_adj','explode':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['kW']}}}),
            ('NVOC over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'bar_width':'1.75', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['MWh']}}}),
            ('NVOC final', {'x':'rb','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['MWh']}}}),
            ('NVOC final nat', {'x':'tech','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['MWh']}}}),
            ('NVOC final nat tech explode', {'x':'scenario','y':'Bulk $ Dis','series':'con_adj','explode':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['MWh']}}}),
            ('LCOE over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'bar_width':'1.75', 'sync_axes':'No', 'y_scale':'-1', 'filter': {'con_name':coststreams+['MWh']}}),
            ('LCOE final', {'x':'rb','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'y_scale':'-1', 'filter': {'year':'last','con_name':coststreams+['MWh']}}),
            ('LCOE final nat', {'x':'tech','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'y_scale':'-1', 'filter': {'year':'last','con_name':coststreams+['MWh']}}),
            ('NVOE var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'MWh, MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'kW, kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['MWh']}}}),
        )),
        }
    ),

    ('Value Streams Sequential New Techs (uncurt MWh)',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_new_icrt.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'gen_uncurt', 'file': 'gen_icrt_uncurt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale.csv', 'columns': ['cs']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'investment_only':True, 'uncurt':True}},
        ],
        'presets': collections.OrderedDict((
            ('NVOE over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'bar_width':'1.75', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOE final', {'x':'rb','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['kW']}}}),
            ('NVOE final nat', {'x':'tech','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['kW']}}}),
            ('NVOE final nat tech explode', {'x':'scenario','y':'Bulk $ Dis','series':'con_adj','explode':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['kW']}}}),
            ('NVOC over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'bar_width':'1.75', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['MWh']}}}),
            ('NVOC final', {'x':'rb','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['MWh']}}}),
            ('NVOC final nat', {'x':'tech','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['MWh']}}}),
            ('NVOC final nat tech explode', {'x':'scenario','y':'Bulk $ Dis','series':'con_adj','explode':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'year':'last','con_name':{'exclude':['MWh']}}}),
            ('LCOE over time', {'x':'year','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'bar_width':'1.75', 'sync_axes':'No', 'y_scale':'-1', 'filter': {'con_name':coststreams+['MWh']}}),
            ('LCOE final', {'x':'rb','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','explode_group':'tech','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'y_scale':'-1', 'filter': {'year':'last','con_name':coststreams+['MWh']}}),
            ('LCOE final nat', {'x':'tech','y':'Bulk $ Dis','series':'con_adj','explode':'scenario','adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'y_scale':'-1', 'filter': {'year':'last','con_name':coststreams+['MWh']}}),
            ('NVOE var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'MWh, MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'kW, kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'sync_axes':'No', 'filter': {'con_name':{'exclude':['MWh']}}}),
        )),
        }
    ),

    ('Competitiveness Sequential New Techs',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_new_icrt.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale.csv', 'columns': ['cs']},
            {'name': 'p', 'file': 'reqt_price.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'investment_only':True, 'competitiveness':True}},
        ],
        'presets': collections.OrderedDict((
            ('LCOE boxplot over time', {'x':'year','y':'LCOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('LCOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'LCOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('LVOE boxplot over time', {'x':'year','y':'LVOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('LVOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'LVOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('NVOE boxplot over time', {'x':'year','y':'NVOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('NVOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'NVOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('value factor boxplot over time', {'x':'year','y':'value factor','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('value factor weighted ave',{'chart_type':'Line', 'x':'year', 'y':'value factor', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('integration cost boxplot over time', {'x':'year','y':'integration cost','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('integration cost weighted ave',{'chart_type':'Line', 'x':'year', 'y':'integration cost', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('BCR boxplot over time', {'x':'year','y':'BCR','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('BCR weighted ave',{'chart_type':'Line', 'x':'year', 'y':'BCR', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Cost $', 'explode':'tech', 'series':'scenario'}),
            ('PLCOE boxplot over time', {'x':'year','y':'PLCOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('PLCOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'PLCOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Value $', 'explode':'tech', 'series':'scenario'}),
            ('SLCOE boxplot over time', {'x':'year','y':'SLCOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('SLCOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'SLCOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario'}),
            ('Benchmark price ($/MWh)',{'chart_type':'Line', 'x':'year', 'y':'P_b', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'Cost $', 'series':'scenario'}),
        )),
        }
    ),

    ('LCOE ($/MWh) Sequential New Techs (uncurt MWh)',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_new_icrt.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'gen_uncurt', 'file': 'gen_icrt_uncurt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale.csv', 'columns': ['cs']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'investment_only':True, 'competitiveness':True, 'uncurt':True}},
        ],
        'presets': collections.OrderedDict((
            ('LCOE boxplot over time', {'x':'year','y':'LCOE','y_agg':'None','explode':'scenario','explode_group':'tech','range':'Boxplot', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75'}),
            ('LCOE weighted ave',{'chart_type':'Line', 'x':'year', 'y':'LCOE', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh', 'explode':'tech', 'series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('Value Streams Sequential Existing Techs',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_icrt.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale.csv', 'columns': ['cs']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'remove_inv':True}},
        ],
        'presets': collections.OrderedDict((
            ('NVOE', {'x':'tech, vintage','y':'Bulk $ Dis','series':'con_adj', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC', {'x':'tech, vintage','y':'Bulk $ Dis','series':'con_adj', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'filter': {'con_name':{'exclude':['MWh']}}}),
            ('NVOE var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'MWh, MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'kW, kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'filter': {'con_name':{'exclude':['MWh']}}}),
        )),
        }
    ),

    ('Value Streams Intertemporal',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'cap', 'file': 'cap_new_icrt.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'MW']},
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale.csv', 'columns': ['cs']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('NVOE', {'x':'tech, vintage','y':'Bulk $ Dis','series':'con_adj', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC', {'x':'tech, vintage','y':'Bulk $ Dis','series':'con_adj', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'con_adj', 'adv_col_base':'kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'filter': {'con_name':{'exclude':['MWh']}}}),
            ('NVOE var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'MWh, MWh', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'filter': {'con_name':{'exclude':['kW']}}}),
            ('NVOC var-con', {'x':'tech, vintage','y':'Bulk $ Dis','series':'var, con', 'explode': 'scenario', 'adv_op':'Ratio', 'adv_col':'var, con', 'adv_col_base':'kW, kW', 'chart_type':'Bar', 'plot_width':'600', 'plot_height':'600', 'filter': {'con_name':{'exclude':['MWh']}}}),
        )),
        }
    ),
    ('Value Factors Sequential New Techs',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'gen_uncurt', 'file': 'gen_icrt_uncurt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale.csv', 'columns': ['cs']},
            {'name': 'p', 'file': 'reqt_price.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'investment_only':True, 'uncurt':True, 'value_factors':True}},
        ],
        'presets': collections.OrderedDict((
            ('LVOE', {'chart_type':'Bar', 'x':'year', 'y':'$', 'series':'con_name', 'explode':'scenario', 'explode_group':'tech', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'sync_axes':'No', 'filter': {}}),
            ('Total price flat benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ flat sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {}}),
            ('Total price all-in weighted benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ all-in sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {}}),
            ('Total value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Total value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Local value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Local value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Spatial value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ flat loc','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Spatial value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ all-in loc','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),

            ('Energy LVOE', {'chart_type':'Bar', 'x':'year', 'y':'$', 'series':'con_name', 'explode':'scenario', 'explode_group':'tech', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams+['MWh']}}),
            ('Energy price flat benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ flat sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {'con_name':energy_valstreams+['MWh']}}),
            ('Energy price with all-in weighted benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ all-in sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {'con_name':energy_valstreams+['MWh']}}),
            ('Energy total value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy total value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy local value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy local value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy spatial value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ flat loc','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),
            ('Energy spatial value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ all-in loc','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':energy_valstreams}}),

            ('ResMarg LVOE', {'chart_type':'Bar', 'x':'year', 'y':'$', 'series':'con_name', 'explode':'scenario', 'explode_group':'tech', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin','MWh']}}),
            ('ResMarg price flat benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ flat sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {'con_name':['eq_reserve_margin','MWh']}}),
            ('ResMarg price all-in weighted benchmark ($/MWh)', {'chart_type':'Bar', 'x':'year', 'y':'$ all-in sys', 'series':'con_name', 'explode':'scenario', 'adv_op':'Ratio', 'adv_col':'con_name', 'adv_col_base':'MWh', 'filter': {'con_name':['eq_reserve_margin','MWh']}}),
            ('ResMarg total value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg total value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg local value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg local value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg spatial value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ flat loc','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
            ('ResMarg spatial value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ all-in loc','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':['eq_reserve_margin']}}),
        )),
        }
    ),

    ('Value Factors Sequential Existing Techs (curtailment caused missing)',
        {'sources': [
            {'name': 'vs', 'file': 'valuestreams_chosen.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'var_name', 'con_name', '$']},
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'gen_uncurt', 'file': 'gen_icrt_uncurt.csv', 'columns': ['tech', 'vintage', 'rb', 'year', 'MWh']},
            {'name': 'pvf_cap', 'file': 'pvf_capital.csv', 'columns': ['year', 'pvfcap']},
            {'name': 'pvf_onm', 'file': 'pvf_onm.csv', 'columns': ['year', 'pvfonm']},
            {'name': 'cost_scale', 'file': 'cost_scale.csv', 'columns': ['cs']},
            {'name': 'p', 'file': 'reqt_price.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'p']},
            {'name': 'q', 'file': 'reqt_quant.csv', 'columns': ['type', 'subtype', 'rb', 'timeslice', 'year', 'q']},
        ],
        'preprocess': [
            {'func': pre_val_streams, 'args': {'remove_inv':True, 'uncurt':True, 'value_factors':True}},
        ],
        'presets': collections.OrderedDict((
            ('Total value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Total value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Local value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ flat loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Local value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$','y_b':'$ all-in loc','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Spatial value factor with flat benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ flat loc','y_b':'$ flat sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
            ('Spatial value factor with all-in weighted benchmark', {'chart_type':'Line', 'x':'year', 'y':'$ all-in loc','y_b':'$ all-in sys','y_agg':'sum(a)/sum(b)', 'series':'scenario', 'explode':'tech', 'sync_axes':'No', 'filter': {'con_name':vf_valstreams}}),
        )),
        }
    ),

    ('Reduced Cost ($/kW)',
        {'file':'reduced_cost.csv',
        'columns': ['tech', 'vintage', 'region', 'year','bin','variable','$/kW'],
        'preprocess': [
            {'func': pre_reduced_cost, 'args': {}},
            {'func': map_rs_to_rb, 'args': {}},
            {'func': apply_inflation, 'args': {'column': '$/kW'}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'irbv', 'y':'$/kW', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'irbv', 'y':'$/kW', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
        )),
        }
    ),

    ('LCOE ($/MWh)',
        {'sources': [
            {'name': 'lcoe', 'file': 'lcoe.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'bin','$/MWh']},
            {'name': 'inv', 'file': 'cap_new_bin_out.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'bin','chosen MW']},
            {'name': 'avail', 'file': 'cap_avail.csv', 'columns': ['tech', 'region', 'year', 'bin','available MW']},
        ],
        'preprocess': [
            {'func': pre_lcoe, 'args': {}},
            {'func': map_rs_to_rb, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
            ('Final supply curves chosen', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'chosen':['yes']}}),
            ('Final supply curves chosen p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'chosen':['yes'], 'rb':['p1']}}),
        )),
        }
    ),

    ('LCOE cf_act ($/MWh)',
        {'sources': [
            {'name': 'lcoe', 'file': 'lcoe_cf_act.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'bin','$/MWh']},
            {'name': 'inv', 'file': 'cap_new_bin_out.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'bin','chosen MW']},
            {'name': 'avail', 'file': 'cap_avail.csv', 'columns': ['tech', 'region', 'year', 'bin','available MW']},
        ],
        'preprocess': [
            {'func': pre_lcoe, 'args': {}},
            {'func': map_rs_to_rb, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
            ('Final supply curves chosen', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'chosen':['yes']}}),
            ('Final supply curves chosen p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'chosen':['yes'], 'rb':['p1']}}),
        )),
        }
    ),

    ('LCOE nopol ($/MWh)',
        {'sources': [
            {'name': 'lcoe', 'file': 'lcoe_nopol.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'bin','$/MWh']},
            {'name': 'inv', 'file': 'cap_new_bin_out.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'bin','chosen MW']},
            {'name': 'avail', 'file': 'cap_avail.csv', 'columns': ['tech', 'region', 'year', 'bin','available MW']},
        ],
        'preprocess': [
            {'func': pre_lcoe, 'args': {}},
            {'func': map_rs_to_rb, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
            ('Final supply curves chosen', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'chosen':['yes']}}),
            ('Final supply curves chosen p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'chosen':['yes'], 'rb':['p1']}}),
        )),
        }
    ),

    ('LCOE fullpol ($/MWh)',
        {'sources': [
            {'name': 'lcoe', 'file': 'lcoe_fullpol.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'bin','$/MWh']},
            {'name': 'inv', 'file': 'cap_new_bin_out.csv', 'columns': ['tech', 'vintage', 'region', 'year', 'bin','chosen MW']},
            {'name': 'avail', 'file': 'cap_avail.csv', 'columns': ['tech', 'region', 'year', 'bin','available MW']},
        ],
        'preprocess': [
            {'func': pre_lcoe, 'args': {}},
            {'func': map_rs_to_rb, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Final supply curves', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', }}),
            ('Final supply curves p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'rb':['p1']}}),
            ('Final supply curves chosen', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'chosen':['yes']}}),
            ('Final supply curves chosen p1', {'chart_type':'Dot', 'x':'icrb', 'y':'$/MWh', 'explode':'scenario','explode_group':'tech', 'sync_axes':'No', 'cum_sort': 'Ascending', 'plot_width':'600', 'plot_height':'600', 'filter': {'year':'last', 'chosen':['yes'], 'rb':['p1']}}),
        )),
        }
    ),

    ('Losses (TWh)',
        {'file':'losses_ann.csv',
        'columns': ['type', 'year', 'Amount (TWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .000001, 'column':'Amount (TWh)'}},
        ],
        'index': ['type', 'year'],
        'presets': collections.OrderedDict((
            ('Total Losses Over Time',{'x':'year', 'y':'Amount (TWh)', 'series':'scenario', 'chart_type':'Line', 'filter': {'type':{'exclude':['load']} }}),
            ('Losses by Type Over Time',{'x':'year', 'y':'Amount (TWh)', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'filter': {'type':{'exclude':['load']} }}),
            ('Fractional Losses by Type Over Time',{'x':'year', 'y':'Amount (TWh)', 'series':'scenario', 'explode':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'load'}),
        )),
        }
    ),

    ('Average VRE Curtailment',
        {'file':'curt_rate.csv',
        'columns': ['year', 'Curt Rate'],
        'index': ['year'],
        'presets': collections.OrderedDict((
            ('Curt Rate Over Time',{'x':'year', 'y':'Curt Rate', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Curtailment Rate icrt (Realized)',
        {'sources': [
            {'name': 'gen', 'file': 'gen_icrt.csv', 'columns': ['tech', 'vintage', 'rb', 'year','MWh']},
            {'name': 'gen_uncurt', 'file': 'gen_icrt_uncurt.csv', 'columns': ['tech', 'vintage', 'rb', 'year','MWh uncurt']},
            {'name': 'load', 'file': 'load_rt.csv', 'columns': ['rb', 'year','MWh load']},
        ],
        'preprocess': [
            {'func': pre_curt, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Curt Rate Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'Curt Rate', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('Curt Rate weighted ave',{'chart_type':'Line', 'x':'year', 'y':'Curt Rate', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh uncurt', 'explode':'tech', 'series':'scenario', 'sync_axes':'No', }),
            ('Curt Rate weighted ave vs penetration',{'chart_type':'Line', 'x':'VRE penetration nat', 'y':'Curt Rate', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh uncurt', 'explode':'tech', 'series':'scenario', 'sync_axes':'No', }),
            ('VRE penetration',{'chart_type':'Line', 'x':'year', 'y':'VRE penetration nat', 'y_agg':'ave(a)','series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('New Tech Curtailment Frac (Caused)',
        {'sources': [
            {'name': 'gen_uncurt', 'file': 'gen_new_uncurt.csv', 'columns': ['tech', 'region', 'timeslice', 'year', 'MWh uncurt']},
            {'name': 'curt_rate', 'file': 'curt_new.csv', 'columns': ['tech', 'region', 'timeslice', 'year', 'Curt Rate']},
        ],
        'preprocess': [
            {'func': pre_curt_new, 'args': {'annual':True}},
            {'func': map_rs_to_rb, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('Curt Rate Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'Curt Rate', 'y_agg':'None', 'range':'Boxplot', 'explode':'tech', 'explode_group':'scenario', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('Curt Rate weighted ave',{'chart_type':'Line', 'x':'year', 'y':'Curt Rate', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MWh uncurt', 'explode':'tech', 'series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('New Tech Capacity Credit',
        {'sources': [
            {'name': 'cap', 'file': 'cap_new_cc.csv', 'columns': ['tech', 'region', 'season', 'year', 'MW']},
            {'name': 'cc', 'file': 'cc_new.csv', 'columns': ['tech', 'region', 'season', 'year', 'CC Rate']},
        ],
        'preprocess': [
            {'func': pre_cc_new, 'args': {}},
            {'func': map_rs_to_rb, 'args': {}},
        ],
        'presets': collections.OrderedDict((
            ('CC Rate Boxplot',{'chart_type':'Dot', 'x':'year', 'y':'CC Rate', 'y_agg':'None', 'range':'Boxplot', 'explode':'season', 'explode_group':'tech', 'series':'scenario', 'sync_axes':'No', 'circle_size':r'3', 'bar_width':r'1.75', }),
            ('CC Rate weighted ave',{'chart_type':'Line', 'x':'year', 'y':'CC Rate', 'y_agg':'sum(a*b)/sum(b)', 'y_b':'MW', 'explode':'season', 'explode_group':'tech', 'series':'scenario', 'sync_axes':'No', }),
        )),
        }
    ),

    ('Transmission (GW-mi)',
        {'file':'tran_mi_out.csv',
        'columns': ['year', 'type', 'Amount (GW-mi)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Amount (GW-mi)'}},
        ],
        'index': ['type', 'year'],
        'presets': collections.OrderedDict((
            ('Transmission Capacity',{'x':'year', 'y':'Amount (GW-mi)', 'series':'scenario', 'explode':'type', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Transmission Capacity Network (GW)',
        {'file':'tran_out.csv',
        'columns': ['rb_out', 'rb_in', 'year', 'type', 'Amount (GW)'],
        'preprocess': [
            {'func': add_joint_locations_col, 'args': {'col1':'rb_out','col2':'rb_in','new':'rb-rb'}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Amount (GW)'}},
        ],
        'index': ['rb-rb', 'year', 'type'],
        'presets': collections.OrderedDict((
            ('Map Final', {'x':'rb-rb', 'y':'Amount (GW)', 'series':'scenario', 'explode':'year', 'chart_type':'Line Map', 'filter': {'year': 'last'}}),
            ('Map Final AC/DC', {'x':'rb-rb', 'y':'Amount (GW)', 'series':'scenario', 'explode':'type', 'explode_group':'year', 'chart_type':'Line Map', 'filter': {'year': 'last'}}),
            ('Map minus 2018', {'x':'rb-rb', 'y':'Amount (GW)', 'series':'scenario', 'explode':'year', 'chart_type':'Line Map', 'adv_op':'Difference', 'adv_col':'year', 'adv_col_base':'2018', 'filter': {'year': ['2018','2050']}}),
        )),
        }
    ),

    ('RE Generation Price ($/MWh)',
        {'file':'RE_gen_price_nat.csv',
        'columns': ['year', 'Price ($/MWh)'],
        'preprocess': [
            {'func': apply_inflation, 'args': {'column':'Price ($/MWh)'}},
        ],
        #'index': ['year'],
        'presets': collections.OrderedDict((
            ('Scenario Lines Over Time',{'x':'year', 'y':'Price ($/MWh)', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('RE Capacity Price ($/kW-yr)',
        {'file':'RE_cap_price_nat.csv',
        'columns': ['season', 'year', 'Price ($/kW-yr)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Price ($/kW-yr)'}},
            {'func': apply_inflation, 'args': {'column':'Price ($/kW-yr)'}},
        ],
        'index': ['season', 'year'],
        'presets': collections.OrderedDict((
            ('Seasonal RE Capacity Price Over Time',{'x':'year', 'y':'Price ($/kW-yr)', 'series':'scenario', 'explode':'season', 'chart_type':'Line'}),
            ('Total RE Capacity Price Over Time',{'x':'year', 'y':'Price ($/kW-yr)', 'series':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('RE Capacity Price BA ($/kW-yr)',
        {'file':'RE_cap_price_r.csv',
        'columns': ['rb', 'season', 'year', 'Price ($/kW-yr)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Price ($/kW-yr)'}},
            {'func': apply_inflation, 'args': {'column':'Price ($/kW-yr)'}},
        ],
        'index': ['rb', 'season', 'year'],
        'presets': collections.OrderedDict((
            ('RE Cap Price by BA',{'x':'rb', 'y':'Price ($/kW-yr)', 'explode':'scenario', 'explode_group':'season', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('CO2 Price exxon ($/tonne)',
        {'file':'co2_price.csv',
        'columns': ['year', '$/tonne'],
        'preprocess': [
            {'func': apply_inflation, 'args': {'column':'$/tonne'}},
        ],
        'index': ['year'],
        'presets': collections.OrderedDict((
            ('CO2 price over time',{'chart_type':'Line', 'x':'year', 'y':'$/tonne', 'series':'scenario', }),
        )),
        }
    ),

    ('Error Check',
        {'file':'error_check.csv',
        'columns': ['type', 'Value'],
        'presets': collections.OrderedDict((
            ('Errors',{'x':'type', 'y':'Value', 'explode':'scenario', 'chart_type':'Bar'}),
        )),
        }
    ),

    ('Capacity Iteration (GW)',
        {'file':'cap_iter.csv',
        'columns': ['tech', 'vintage', 'rs', 'year', 'iter', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Capacity (GW)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Capacity (GW)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Generation Iteration (TWh)',
        {'file':'gen_iter.csv',
        'columns': ['tech', 'vintage', 'rs', 'year', 'iter', 'Gen (TWh)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'Gen (TWh)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Area',{'x':'year', 'y':'Gen (TWh)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Area'}),
            ('Stacked Bars',{'x':'year', 'y':'Gen (TWh)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Gen (TWh)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Line'}),
            ('PCA Map Final by Tech',{'x':'rb', 'y':'Gen (TWh)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
            ('State Map Final by Tech',{'x':'st', 'y':'Gen (TWh)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Area Map', 'filter': {'year':'last'}}),
        )),
        }
    ),

    ('Firm Capacity Iteration (GW)',
        {'file':'cap_firm_iter.csv',
        'columns': ['tech', 'vintage', 'rs', 'season', 'year', 'iter', 'Capacity (GW)'],
        'preprocess': [
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'Capacity (GW)'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'Capacity (GW)', 'series':'tech', 'explode':'iter', 'explode_group':'scenario', 'chart_type':'Bar', 'bar_width':'1.75'}),
            ('Explode By Tech',{'x':'year', 'y':'Capacity (GW)', 'series':'iter', 'explode':'tech', 'explode_group':'scenario', 'chart_type':'Line'}),
        )),
        }
    ),

    ('Capacity Credit Iteration (GW)',
        {'sources': [
            {'name': 'cap_firm', 'file': 'cap_firm_iter.csv', 'columns': ['tech', 'vintage', 'rs', 'season', 'year', 'iter', 'GW']},
            {'name': 'cap', 'file': 'cap_iter.csv', 'columns': ['tech', 'vintage', 'rs', 'year', 'iter', 'GW']},
        ],
        'preprocess': [
            {'func': pre_cc_iter, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': .001, 'column':'GW'}},
        ],
        'presets': collections.OrderedDict((
            ('Stacked Bars',{'x':'year', 'y':'GW', 'series':'tech', 'explode':'iter', 'explode_group':'type', 'chart_type':'Bar', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'cap'}),
            ('Explode By Tech',{'x':'year', 'y':'GW', 'series':'iter', 'explode':'tech', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'cap'}),
        )),
        }
    ),

    ('Curtailment Iteration (TWh)',
        {'sources': [
            {'name': 'curt', 'file': 'curt_tot_iter.csv', 'columns': ['tech', 'vintage', 'rs', 'year', 'iter', 'TWh']},
            {'name': 'gen_uncurt', 'file': 'gen_iter.csv', 'columns': ['tech', 'vintage', 'rs', 'year', 'iter', 'TWh']},
        ],
        'preprocess': [
            {'func': pre_curt_iter, 'args': {}},
            {'func': scale_column, 'args': {'scale_factor': 1e-6, 'column':'TWh'}},
        ],
        'presets': collections.OrderedDict((
            ('Explode By Tech',{'x':'year', 'y':'TWh', 'series':'iter', 'explode':'tech', 'explode_group':'type', 'chart_type':'Line', 'adv_op':'Ratio', 'adv_col':'type', 'adv_col_base':'gen', }),
        )),
        }
    ),
))

#Sort alphabetically
results_meta = collections.OrderedDict(sorted(results_meta.items()))