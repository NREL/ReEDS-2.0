#%%### Imports
import os
import sys
import yaml
import argparse
import datetime
import itertools
import subprocess
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds

reeds_path = reeds.io.reeds_path

pd.options.display.max_rows = 45
pd.options.display.max_columns = 200


#%%### Functions
def make_case(label, defaults, dimensions):
    """Define the case name format"""
    ### Get collections of settings
    dimension_names = list(dimensions.keys())
    dimension_values = label.split('_')
    dimension_keyvals = dict(zip(dimension_names, dimension_values))
    ### Build the new case settings
    settings = {}
    for k,v in dimension_keyvals.items():
        settings = {**settings, **dimensions[k][v]}
    ### Make sure all the switches are entered properly
    for key in settings:
        if key not in defaults.index:
            raise Exception(f'{key} not in defaults')
    ### Create series of key:value pairs
    case = pd.Series(settings, dtype='object').reindex(defaults.index).fillna('')
    return case


def drop_default_rows(dfcases, shared={}):
    """Drop rows that use original defaults for every case"""
    df = dfcases.copy()
    drop_rows = df.loc[
        df.drop(columns='Default Value', errors='ignore')
        .astype(str).astype(bool).sum(axis=1) == 0
    ].index
    ## Keep the 'ignore' row for ease of use
    drop_rows = [i for i in drop_rows if (i != 'ignore') and (i not in shared)]
    return df.drop(drop_rows)


def reassign_defaults(dfcases, threshold=0.51):
    """If most entries use a particular value, set it to the default"""
    df = dfcases.astype(str).copy()
    cases = [i for i in dfcases if i != 'Default Value']
    for switch, row in df.iterrows():
        value_counts = row.drop(columns='Default Value').value_counts()
        value_fraction = value_counts / value_counts.sum()
        top = value_fraction.nlargest(1)
        top_value, top_fraction = [(k,v) for (k,v) in top.items()][0]
        if (top_value != '') and (top_fraction >= threshold):
            new_default = top_value
            df.loc[switch, 'Default Value'] = new_default
            df.loc[switch, cases] = df.loc[switch, cases].replace(new_default, '')
    return df


def validate_casematrix(casematrix):
    """Make sure casematrix is formatted correctly"""
    ## Dimensions
    dimensions = casematrix['dimensions']
    if not isinstance(dimensions, dict):
        err = f"dimensions has type {type(dimensions)} but should be a dictionary"
        raise TypeError(err)

    disallowed = ['_', ' ', '.', '&', '/']
    for dimension, elements in dimensions.items():
        for i, item in enumerate(list(elements.keys())):
            if any([i in item for i in disallowed]):
                err = (
                    f'Element #{i} of the "{dimension}" dimension ({item}) uses one or '
                    f'more of the following disallowed characters: {disallowed}'
                )
                raise ValueError(err)

    ## Casegroups
    casegroups = casematrix['casegroups']
    if not isinstance(casegroups, list):
        err = f"casegroups has type {type(casegroups)} but should be a list"
        raise TypeError(err)

    num_dimensions = len(dimensions)
    for i, casegroup in enumerate(casegroups):
        if len(casegroup) != num_dimensions:
            err = (
                f"There are {num_dimensions} dimensions ({list(dimensions.keys())}) but "
                f"casegroup #{i} has {len(casegroup)} elements: {casegroup}"
            )
            raise ValueError(err)


def parse_casegroups(casegroups, dimensions):
    """Expand list of casegroups into list of case names"""
    dimension_names = list(dimensions.keys())
    caselist = []
    for casegroup in casegroups:
        case_generator = []
        for i, dimension in enumerate(casegroup):
            dimension_name = dimension_names[i]
            if isinstance(dimension, str):
                dimension_values = [dimension]
            elif isinstance(dimension, list):
                ## If not empty, use the provided values
                if len(dimension):
                    dimension_values = dimension
                ## Otherwise, if empty, use all values
                else:
                    dimension_values = list(dimensions[dimension_name].keys())
            else:
                raise TypeError(dimension)
            ### Create list of lists of dimension values
            case_generator.append(dimension_values)
        ### Combine list of lists combinatorially
        case_elements = list(itertools.product(*case_generator))
        cases = ['_'.join(i) for i in case_elements]
        caselist.extend(cases)
    return caselist


def main(casematrix_path=None, batchname=None):
    ### Parse inputs
    if batchname in [None, '']:
        _batchname = datetime.datetime.now().strftime("%Y%m%d")
    else:
        _batchname = batchname

    if casematrix_path in [None, '']:
        _casematrix_path = os.path.join(
            reeds_path, 'preprocessing', 'casematrix_example.yaml',
        )
    elif os.path.isfile(casematrix_path):
        _casematrix_path = casematrix_path
    else:
        _casematrix_path = os.path.join(
            reeds_path, 'preprocessing', f'casematrix_{casematrix_path}.yaml',
        )
    if not os.path.isfile(_casematrix_path):
        raise FileNotFoundError(_casematrix_path)

    ### Read from YAML
    with open(_casematrix_path, 'r') as f:
        casematrix = yaml.safe_load(f)

    ### Validate formatting
    validate_casematrix(casematrix)

    ### Define switch collections for scenarios
    shared = casematrix.get('shared', {})
    dimensions = casematrix['dimensions']
    casegroups = casematrix['casegroups']

    ### Load defaults and apply shared settings
    defaults = pd.read_csv(
        os.path.join(reeds_path,'cases.csv'),
        index_col=0,
    )['Default Value']
    for key, val in shared.items():
        defaults[key] = val

    ### Create the case names
    cases = parse_casegroups(casegroups, dimensions)

    ### Create the cases dataframe
    dfcases = pd.concat({
        **{'Default Value':defaults},
        **{case: make_case(case, defaults, dimensions) for case in cases},
    }, axis=1)

    ### Clean it up
    dfcases = drop_default_rows(dfcases, shared)
    reassign_defaults(dfcases)
    dfcases = dfcases.T.drop_duplicates().T

    ### Print the resulting cases
    numcases = dfcases.shape[1]-1
    msg = f'{numcases} cases:'
    print(
        f"{msg}\n{'-'*len(msg)}\n"
        + '\n'.join([i for i in dfcases.columns if i != 'Default Value'])
    )

    ### Write it
    dfcases.to_csv(os.path.join(reeds_path,f'cases_{_batchname}.csv'))

    ### Make sure the switch names and values pass the checks in runbatch.py
    sep = ';' if os.name == 'posix' else '&&'
    cmd = f"cd {reeds_path} {sep} python runbatch.py -b test -c {_batchname} -r 4 -p 1 --dryrun"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    err = result.stderr.decode()
    if len(err):
        raise ValueError(err)

    return dfcases


#%%### Procedure
if __name__ == '__main__':
    #%% Argument inputs
    parser = argparse.ArgumentParser(
        description='Create cases .csv file from casematrix .yaml file',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        'casematrix_path', type=str, nargs='?',
        help=(
            'Path to casematrix_{suffix}.yaml file, '
            'or just {suffix} if file is in the preprocessing folder. '
            'If empty, uses preprocessing/casematrix_example.yaml.'
        )
    )
    parser.add_argument(
        '--batchname', '-b', type=str, default='',
        help=(
            'Filename to use in output cases_{batchname}.csv file. '
            "If empty, uses today's date in YYYYMMDD format."
        )
    )
    args = parser.parse_args()
    casematrix_path = args.casematrix_path
    batchname = args.batchname

    # #%% Inputs for testing
    # casematrix_path = None
    # batchname = ''

    #%% Run it
    main(casematrix_path=casematrix_path, batchname=batchname)
