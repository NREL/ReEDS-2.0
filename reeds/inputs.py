### Imports
import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


### Functions
def parse_regions(case_or_string, case=None):
    """
    Inputs
    ------
    case_or_string: path to a ReEDS case or a parseable string in the format of GSw_Region
    case: path to a ReEDS case. Only used if case_or_string is not a ReEDS case. Should be
        used if you want to select a subset of model zones from a ReEDS case that used
        region aggregation.

    Returns
    -------
    np.array of zone names
        - If case_or_string is a case, return the regions modeled in the run
        - If case_or_string is a parseable string in the format of GSw_Region, return
          the regions that obey that string

    Examples
    --------
    parse_regions('transreg/NYISO') -> ['p127', 'p128']
    parse_regions('st/PA') -> ['p115', 'p119', 'p120', 'p122']
    parse_regions('st/PA', 'path/to/case/using/region/aggregation') -> ['p115', 'p120', 'z122']
    """
    if os.path.exists(case_or_string):
        sw = reeds.io.get_switches(case_or_string)
        hierarchy = reeds.io.get_hierarchy(case_or_string)
        GSw_Region = sw['GSw_Region']
    ## Provide case argument if using aggregated regions
    elif os.path.exists(str(case)):
        hierarchy = reeds.io.get_hierarchy(case)
        GSw_Region = case_or_string
    else:
        hierarchy = reeds.io.get_hierarchy()
        GSw_Region = case_or_string

    if '/' in GSw_Region:
        level, regions = GSw_Region.split('/')
        regions = regions.split('.')
        if level in ['r', 'ba']:
            rs = [r for r in hierarchy.index if r in regions]
        else:
            rs = hierarchy.loc[hierarchy[level].isin(regions)].index
    else:
        modeled_regions = pd.read_csv(
            os.path.join(reeds.io.reeds_path, 'inputs', 'userinput', 'modeled_regions.csv')
        )
        modeled_regions.columns = modeled_regions.columns.str.lower()
        rs = list(
            modeled_regions[
                ~modeled_regions[GSw_Region.lower()].isna()
            ]['r'].unique()
        )
    return rs
