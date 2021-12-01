###############
#%% IMPORTS ###
import os
import shutil
import pandas as pd
from pdb import set_trace as b


#%% Get the file locations
if os.name == 'posix':
    drive = '/Volumes/'
else:
    drive = '//nrelnas01/'
ind_path_base = 'ReEDS/Supply_Curve_Data/individual_sites/2021-07-20/'
ons_path = 'wind-ons_08_open_moderate_eos_flicker_2021-07-19-18-19-36-748656/'
off_path = 'wind-ofs_2_moderate_open_2021-07-19-18-20-07-221449/'
reg_map_path = 'results/region_map.csv'

df_ons_sites = pd.read_csv(drive + ind_path_base + ons_path + reg_map_path)
df_off_sites = pd.read_csv(drive + ind_path_base + off_path + reg_map_path)

df_ind_sites = pd.concat([df_ons_sites, df_off_sites],sort=False,ignore_index=True)
df_ind_sites.rename(columns={'rb':'*r', 'region':'rs'}, inplace=True)

df_rsmap_sreg = pd.read_csv('../inputs/rsmap_sreg.csv')

df_rsmap_ind = pd.concat([df_rsmap_sreg, df_ind_sites],sort=False,ignore_index=True)

df_rsmap_ind.to_csv('../inputs/rsmap.csv', index=False)
