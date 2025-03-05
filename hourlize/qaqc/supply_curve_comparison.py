"""
Compare any number of supply curves to a base supply curve
"""
import os
import pandas as pd
import json
import requests
import re

this_dir_path = os.path.dirname(os.path.realpath(__file__))

#The first is assumed to be the base case for comparisons. Outputs will be sorted by this order as well.
supply_curves = [
    {'name': 'old_reference', 'path': r"/kfs2/shared-projects/reeds/Supply_Curve_Data/ONSHORE/2025_01_23_H5Fix_CST/wind-ons_reference_ba/results/wind-ons_supply_curve_raw.csv"},
    {'name': 'new_reference', 'path': r"/kfs2/shared-projects/reeds/Supply_Curve_Data/ONSHORE/2025_02_03_Update/wind-ons_reference_ba/results/wind-ons_supply_curve_raw.csv"},
]

val_cols = ['capacity_ac_mw','capacity_factor_ac','lcoe_all_in_usd_per_mwh','supply_curve_cost_per_mw']
for i, sc in enumerate(supply_curves):
    print(f'{sc["name"]}')
    df = pd.read_csv(sc['path'])
    df['name'] = sc['name']
    df['name_idx'] = i
    df = df[['name','name_idx','sc_point_gid','latitude','longitude','state'] + val_cols].copy()
    if i == 0:
        df_all = df.copy()
        df_base = df[['sc_point_gid'] + val_cols].copy()
        val_cols_base = [f'{col}_base' for col in val_cols]
        df_base.columns = ['sc_point_gid'] + val_cols_base
    else:
        df_all = pd.concat([df_all, df], ignore_index=True)
df_all = df_all.merge(df_base, on='sc_point_gid', how='outer') #Outer in case sc_point_gids are different
fillna_cols = ['capacity_ac_mw','capacity_ac_mw_base'] #the other val_cols will just be missing
df_all[fillna_cols] = df_all[fillna_cols].fillna(0)
#Sort by LCOE and add cumulative capacity
df_all = df_all.sort_values(['name_idx','lcoe_all_in_usd_per_mwh'])
df_all['cumulative_cap_mw'] = df_all.groupby('name_idx')['capacity_ac_mw'].cumsum()
#Add 'both_exist' column to show if both the base and comparison supply curves have capacity (capacity_ac_mw and capacity_ac_mw_base are both greater than 0). Set 'both_exist' to 1 if true, 0 if false.
df_all['both_exist'] = (df_all['capacity_ac_mw'] > 0) & (df_all['capacity_ac_mw_base'] > 0)
df_all['both_exist'] = df_all['both_exist'].astype(int)
for col in val_cols:
    #Calculate diff and drop base col
    df_all[f'{col}_diff'] = df_all[col] - df_all[f'{col}_base']
    df_all = df_all.drop(columns=[f'{col}_base'])


print('Dump data')
df_all.to_csv(f'{this_dir_path}/supply_curve_comparison.csv', index=False)

print('Make Vizit report')
vizit_commit = '89b312499b56ff676a731c8a6375c865c61d6ce7'
vizit_url = f'https://raw.githubusercontent.com/mmowers/vizit/{vizit_commit}/index.html'
f_out_str = requests.get(vizit_url).text
#Data
data_dict = {
    'supply_curve_comparison.csv': df_all.to_dict(orient='list'),
}
data_str = json.dumps(data_dict, separators=(',',':'))
f_out_str = re.sub('let rawData = .*;\n', f'let rawData = {data_str};\n', f_out_str, 1)
#Config
with open(f'{this_dir_path}/vizit_sc_compare.json') as json_file:
    vizit_config = json.load(json_file)
#Custom edits to config
for i, sc in enumerate(supply_curves):
    path_adj = sc["path"].replace('\\','/')
    base_str = ' (base)' if i == 0 else ''
    vizit_config['dashboards'][0]['description'] += f'<b>{sc["name"]}</b>: <i>{path_adj}</i> {base_str}<br><br>'
#Convert config to string
config_str = json.dumps(vizit_config, separators=(',',':'))
#Custom string replacements
config_str = config_str.replace('"base"',f'"{supply_curves[0]["name"]}"') #Custom replacement to use different base case name
#Save config string to html string
f_out_str = re.sub('let config_load = .*;\n', f'let config_load = {config_str};\n', f_out_str, 1)
#Dump to HTML
with open(f'{this_dir_path}/vizit_sc_compare.html', 'w') as f_out:
    f_out.write(f_out_str)
