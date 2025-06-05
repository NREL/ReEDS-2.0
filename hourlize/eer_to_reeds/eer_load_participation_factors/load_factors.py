'''
This script calculates load participation factors between states and BAs, which should be consistent across EER case, model year, weather year and weather hour. But there are switches to test this consistency across these dimensions.

DC is in p123 (Maryland). Two options (controlled by dc_opt) are:
1. First assign DC to MD and then determine participation factors from MD to p121 and p123 -OR-
2. First remove DC load from p123, then determine participation factors from MD to p121 and p123, then add factor of 1 from DC to p123 (more accurate I think).
'''
import os
import h5py
import pandas as pd
from pdb import set_trace as b

this_dir_path = os.path.dirname(os.path.realpath(__file__))

weather_year = 2012
eer_case = 'ira' #ira, ira_con, central, baseline
model_year = 2050
eer_load_path = '/projects/eerload/source_eer_load_profiles/20230604_eer_load'
ba_load_path = '/projects/eerload/reeds_load/20230604_reeds_load'
dc_opt = 2 #1 or 2. See description at top of file

df_ba_state_map = pd.read_csv(f'{this_dir_path}/ba_state_map.csv')
f_eer = h5py.File(f'{eer_load_path}_{weather_year}.h5')
df_eer_meta = pd.DataFrame(f_eer['meta'][:]).astype(str)
eer_load = pd.DataFrame(f_eer['load'][:]).sum() #Annual sum of load
f_eer.close()
df_eer_meta = df_eer_meta[(df_eer_meta['YEAR']==str(model_year))&(df_eer_meta['SCENARIO'].str.lower()==eer_case)]
df_ba_load = pd.read_csv(f'{ba_load_path}_{eer_case}_e{model_year}_w{weather_year}.csv')
if dc_opt == 1:
    df_eer_meta['STATE'] = df_eer_meta['STATE'].replace('district of columbia','maryland')
    states = [s for s in df_eer_meta['STATE'].unique()]
elif dc_opt == 2:
    states = [s for s in df_eer_meta['STATE'].unique() if s != 'district of columbia']
ls_loadfac = []
for state in states:
    df_eer_meta_st = df_eer_meta[df_eer_meta['STATE']==state]
    eer_load_st = eer_load[df_eer_meta_st.index].sum()
    ba_ls = df_ba_state_map[df_ba_state_map['state'] == state]['ba'].tolist()
    ba_load_st = df_ba_load[ba_ls].sum() #Annual sum of load
    if dc_opt == 2 and state == 'maryland':
        df_eer_meta_dc = df_eer_meta[df_eer_meta['STATE']=='district of columbia']
        eer_load_dc = eer_load[df_eer_meta_dc.index].sum()
        ba_load_st['p123'] = ba_load_st['p123'] - eer_load_dc
    ba_loadfac = ba_load_st.div(eer_load_st)
    ls_loadfac.append(ba_loadfac)
ba_load_factors = pd.concat(ls_loadfac)
df_load_factors = df_ba_state_map.merge(ba_load_factors.rename('load_factor'), left_on='ba', right_index=True)
if dc_opt == 2:
    df_load_factors.loc[len(df_load_factors)] = ['p123','DC','district of columbia',1]
df_load_factors.to_csv(f'{this_dir_path}/load_factors.csv', index=False)
b()