import os
import sys
import re
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


### Constants
ignore_techs = ['ocean', 'caes', 'ice', 'mhkwave']


### Functions
def expand_GAMS_tech_groups(df):
    '''
    GAMS has a convention for expanding rows (e.g. upv_1*upv_10 is expanded to upv_1, upv_2,..., upv_10)
    This function expands a df with the same convention, for the instances where a file is ingested
    by both python and GAMS. We assume the numbers we would like to enumerate occur at the end.
    '''
    tech_groups = [group for group in df['i'] if '*' in group]

    for tech_group in tech_groups:
        tech_group_ls = tech_group.split('*')
        num_start = int(re.search(r'(\d+)\s*$', tech_group_ls[0]).group(1))
        num_end = int(re.search(r'(\d+)$', tech_group_ls[1]).group(1))
        tech_group_root = re.sub(r'\d+\s*$', '', tech_group_ls[0])
        techs = [f'{tech_group_root}{num}' for num in range(num_start, num_end + 1)]
        # Extract the tech group from the main df
        df_subset = df[df['i'] == tech_group]
        # Drop the tech group from the main df
        df = df[df['i'] != tech_group]

        df_list = []

        for tech in techs:
            df_expanded_single = df_subset.copy()
            df_expanded_single['i'] = tech
            df_list = df_list + [df_expanded_single]

        df = pd.concat([df] + df_list, ignore_index=True)

    return df


def import_tech_groups(file_path):
    '''
    Creates a dictionary of different tech groups from a csv.
    Used during the import process -- if a particular assumption applies to a family of technologies,
        this dictionary creates the mapping.

    First column of the input csv is the dictionary key for that tech family.
    There cannot be duplicate keys, and they must differ from a tech name.
    '''
    tech_subset_table = pd.read_csv(file_path)
    tech_subset_table = tech_subset_table.rename(columns={'Unnamed: 0': 'i'})

    tech_subset_table = expand_GAMS_tech_groups(tech_subset_table)

    tech_subset_table = tech_subset_table.set_index('i')
    tech_groups = {}
    for col in list(tech_subset_table.columns):
        tech_groups[col] = list(tech_subset_table[col][tech_subset_table[col] == 'YES'].index)

    return tech_groups


def get_tech_subset_table(case):
    """Output techs are in lower case"""
    inputs_case = case if 'inputs_case' in case else os.path.join(case, 'inputs_case')
    tech_subset_table = (
        pd.read_csv(os.path.join(inputs_case, 'tech-subset-table.csv'), index_col=0)
        .rename_axis(index='i', columns='tech_group')
        .stack().dropna()
        .reorder_levels(['tech_group','i']).sort_index()
        .reset_index('i').i
        .str.lower()
    )
    return tech_subset_table


def get_techlist_after_bans(case):
    sw = reeds.io.get_switches(case)
    tech_subset_table = get_tech_subset_table(case)
    techlist = sorted(tech_subset_table.unique())
    if not int(sw.GSw_BECCS):
        techlist = [i for i in techlist if 'beccs' not in i]
    if not int(sw.GSw_Biopower):
        techlist = [i for i in techlist if i != 'biopower']
    if not int(sw.GSw_DAC):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['DAC'].values]
    if not int(sw.GSw_H2_SMR):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['SMR'].values]
    if int(sw.GSw_Storage) == 0:
        techlist = [i for i in techlist if i not in tech_subset_table.loc['STORAGE_STANDALONE'].values]
    elif int(sw.GSw_Storage) == 3:
        techlist = [
            i for i in techlist if (
                (i not in tech_subset_table.loc['STORAGE_STANDALONE'].values)
                or (i in ['battery_4', 'battery_8', 'pumped-hydro'])
            )
        ]
    if not int(sw.GSw_CCSFLEX_BYP):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['CCSFLEX_BYP'].values]
    if not int(sw.GSw_CCSFLEX_STO):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['CCSFLEX_STO'].values]
    if not int(sw.GSw_CCSFLEX_DAC):
        techlist = [i for i in techlist if i not in tech_subset_table.loc['CCSFLEX_DAC'].values]

    return techlist
