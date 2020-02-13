import sys
import os
import gdxpds
import pandas as pd
import shutil
import numpy as np
import raw_value_streams as rvs
#import gdx2py
from datetime import datetime

# set working directory
this_dir_path = os.path.dirname(os.path.realpath(__file__))
vs_path = this_dir_path 

# load variable map
df_var_map = pd.read_csv(vs_path+'/var_map.csv', dtype=object)

# load rs - region map
df_hier = pd.read_csv(vs_path + '/region_map.csv')
dict_hier = dict(zip(df_hier['rs'], df_hier['ba']))

# extract names of variables
var_list = df_var_map['var_name'].values.tolist()

#function to create a cplex optfile: save equations in mps format
def makeOptFile(optFileNum, caseIndex, case_name):
    #Get original optfile
    if int(optFileNum) == 1:
        origOptExt = 'opt'
    elif int(optFileNum) < 10:
        origOptExt = 'op' + optFileNum
    else:
        origOptExt = 'o' + optFileNum
    #Create number in 900s for modified opt file and add to options
    if caseIndex < 10:
        modOptFileNum = '90' + str(caseIndex)
    else:
        modOptFileNum = '9' + str(caseIndex)
    #Copy original optfile into new optfile specified by the new number in 900s
    shutil.copyfile('cplex.'+origOptExt, 'cplex.'+modOptFileNum)
    #Add writemps statement to new opt file
    with open('cplex.'+modOptFileNum, 'a') as file:
        file.write('\nwritemps ' + case_name + '.mps')
    return modOptFileNum

#common function for outputting to csv
def add_concat_csv(df_in, csv_file):
    df_in['year'] = pd.to_numeric(df_in['year'])
    if not os.path.exists(csv_file):
        df_in.to_csv(csv_file,index=False)
    else:
        df_csv = pd.read_csv(csv_file)
        min_yr = df_in['year'].min()
        df_csv = df_csv[df_csv['year'] < min_yr].copy()
        df_out = pd.concat([df_csv, df_in], ignore_index=True, sort=False)
        df_out.to_csv(csv_file,index=False)

#function to calculate valuestreams
def createValueStreams(case):
    very_start = datetime.now()
    print('Starting valuestreams.py')
    output_dir = 'F_Analysis/valuestreams/outputs'
    solution_file = case + '_p.gdx'
    mps_file = case + '.mps'
    df = rvs.get_value_streams(solution_file, mps_file, var_list)
    print('Raw value streams completed: ' + str(datetime.now() - very_start))

    df = pd.merge(left=df, right=df_var_map, on='var_name', how='inner')

    #Chosen plants (with nonzero levels in solution)
    start = datetime.now()
    df_lev = df[df['var_level'] != 0].copy()
    #convert to list of lists for speed
    df_lev_ls = df_lev.values.tolist()
    cols = df_lev.columns.values.tolist()
    ci = {c:i for i,c in enumerate(cols)}
    #Use iterrows or itertuples or somthing faster? iterrows is most convenient so if this isn't a bottleneck, use it.
    replace_cols = ['tech','tech','reg','year']
    for i, r in enumerate(df_lev_ls):
        var_set_ls = r[ci['var_set']].split('.')
        for c in replace_cols:
            if str(r[ci[c]]).isdigit():
                df_lev_ls[i][ci[c]] = var_set_ls[int(r[ci[c]])]
    #convert back to pandas dataframe
    df_lev = pd.DataFrame(df_lev_ls)
    df_lev.columns = cols

    #Add ba column
    df_lev['ba'] = df_lev['reg'].map(dict_hier)
    #Fill missing values with 'none'
    out_sets = ['tech','ba','year','var_name','con_name']
    df_lev[out_sets] = df_lev[out_sets].fillna(value='none')

    #Reduce df_lev to columns of interest and groupby sum
    out_cols = out_sets + ['value']
    df_lev = df_lev[out_cols]
    df_lev = df_lev.groupby(out_sets, sort=False, as_index =False).sum()

    add_concat_csv(df_lev.copy(), output_dir + '/valuestreams_chosen' + '.csv')
    print('Levels output: ' + str(datetime.now() - start))
    print('Finished valuestreams.py ' + str(datetime.now() - very_start))
    print('Output saved to ' + output_dir)

if __name__ == '__main__':
    createValueStreams(sys.argv[1])