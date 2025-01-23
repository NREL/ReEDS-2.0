"""
Check to make sure each aggreg is only assigned to a single transreg / transgrp / etc.

If you receive a message like
    hierarchy_agg3.csv
    ------------------
                              hurdlereg aggreg
    ba                                        
    p95       Duke_Energy_Carolinas_LLC     SC
    p96  South_Carolina_Electric_Gas_Co     SC
you should either set hurdlereg=South_Carolina_Electric_Gas_Co in row p95
or hurdlereg=Duke_Energy_Carolinas_LLC in row p96 so that both match.
"""

#%% Imports
import pandas as pd
import os
from glob import glob

reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))

#%% Functions
def check_aggreg_unique(hierarchy):
    """
    Make sure each aggreg is only assigned to a single transreg / transgrp / st / etc.
    """
    testcols = [i for i in hierarchy.columns if i != 'aggreg']
    aggreg_errors = {}
    for col in testcols:
        unique_aggregs = (
            hierarchy[[col,'aggreg']]
            .drop_duplicates()
            .groupby('aggreg')[col].count()
        )
        duplicated = unique_aggregs.loc[unique_aggregs>1]
        if len(duplicated):
            aggreg_errors[col] = hierarchy.loc[
                hierarchy.aggreg.isin(duplicated.index),
                [col,'aggreg']
            ]
    return aggreg_errors


def test_hierarchy_files(reeds_path, country='USA'):
    hierarchy_paths = sorted(glob(os.path.join(reeds_path, 'inputs', 'hierarchy*.csv')))
    hierarchy_errors = {}
    for hierarchy_path in hierarchy_paths:
        hierarchy = (
            pd.read_csv(hierarchy_path, index_col=0)
            .drop(columns=['st_interconnect'], errors='ignore')
        )
        hierarchy = hierarchy.loc[hierarchy.country.str.lower() == country.lower()].copy()
        aggreg_errors = check_aggreg_unique(hierarchy)
        if len(aggreg_errors):
            hierarchy_errors[os.path.basename(hierarchy_path)] = aggreg_errors
    return hierarchy_errors


#%% Procedure
if __name__ == '__main__':
    hierarchy_errors = test_hierarchy_files(reeds_path)
    for hierarchy_path, error in hierarchy_errors.items():
        print(hierarchy_path)
        print('-'*len(hierarchy_path))
        for v in error.values():
            print(v)
            print()

    if len(hierarchy_errors):
        err = (
            "There are aggreg values spanning multiple hierarchy levels in\n > "
            f"{' > '.join(hierarchy_errors.keys())}\n"
            "Please modify these hierarchy files to make sure each aggreg is not used\n"
            "more than once for each entry in each hierarchy level.\n"
        )
        raise ValueError(err)
