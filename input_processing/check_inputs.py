#%% Imports
import gdxpds
import os
import sys
import argparse
import datetime
import yaml
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
tic = datetime.datetime.now()

#%% Argument inputs
parser = argparse.ArgumentParser(
    description='Check inputs.gdx parameters against objective_function_params.yaml',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument('casepath', help='ReEDS-2.0/runs/{case} directory')
args = parser.parse_args()
casepath = args.casepath

# #%% Inputs for testing
# reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
# casepath = os.path.join(reeds_path, 'runs', 'v20241219_checkinputsM1_Pacific')

#%% Functions
rename = {
    'allt': 't',
    'allh': 'h',
}

def get_infiles(inputs, infiles):
    dfs = {}
    for infile in infiles:
        dfs[infile] = inputs[infile].rename(columns=rename)
    return dfs


def check_df(dfcheck, param, kwargs):
    """
    Args:
        dfcheck (pd.DataFrame): Dataframe with a Value column, where any np.nan values
            in the Value column indicate an error. Created by left-merging a set with
            a parameter. If a collection of indices in the set is not present in the
            parameter, left-merging will create a np.nan in the merged dfcheck.
        param (str): Name of parameter being tested
    """
    dfmissing = dfcheck.loc[dfcheck.Value.isnull()]
    if len(dfmissing):
        print(f'{param} values missing for:')
        print(dfmissing)
        for col in [c for c in dfmissing.columns if c.lower() != 'value']:
            print(f"{col} elements: {','.join(dfmissing[col].unique().astype(str))}")
        err = (
            f"Missing values for {param} "
            f"or extraneous values in {' or '.join(kwargs['indexsets'])}"
        )
        raise ValueError(err)


def check_param(param, kwargs, inputs, sw):
    ### Skip if the parameter is switched off.
    ## All switches must be set to their "switchon" values to proceed with the check;
    ## otherwise the parameter will be skipped.
    ## If no "switchon" value is provided, the check will proceed.
    switchon = []
    for k, v in kwargs.get('switchon',{}).items():
        ## Convert Sw_ to GSw_ if necessary
        _k = 'G'+k if k.startswith('Sw_') else k
        switchon.append(
            1 if (
                (int(sw[_k]) == v)
                or (int(sw[_k]) and (v == 'nonzero'))
            )
            else 0
        )

    if len(switchon) and not all(switchon):
        print(
            f"{param:<30}: skipped because "
            f"{' or '.join([f'{k}!={v}' for k,v in kwargs['switchon'].items()])}"
        )
        return None

    ### Get index and parameter from inputs.gdx
    ## Parentheses are only used for labeling (needed since we independently check some 
    ## disparate values stored in a single parameter, like sc_cat in m_rsc_dat, and
    ## dictionary keys have to be unique),
    ## so filter them out and just keep the parameter name.
    _param = param.split('(')[0]
    dfs = get_infiles(inputs, kwargs['indexsets']+kwargs.get('excludesets',[])+[_param])

    ## Only keep the overlap between indexsets.
    ## For example, indexsets = ['valinv', 'rsc_i']
    ## is the same as $[valinv(i,v,r,t)$rsc_i(i)] in GAMS.
    dfindex = dfs[kwargs['indexsets'][0]].drop(columns='Value', errors='ignore')
    for subset in kwargs['indexsets'][1:]:
        dfindex = (
            dfindex
            .merge(dfs[subset], on=None, how='inner')
            .drop(columns='Value', errors='ignore')
        )
    ## Exclude elements in excludesets
    for excludeset in kwargs.get('excludesets', []):
        excludeset_indices = [i for i in dfs[excludeset].columns if i.lower() != 'value']
        ## By left-merging and keeping NaN values, we filter out elements in excludeset
        df = dfindex.merge(
            dfs[excludeset].assign(Value=1),
            on=excludeset_indices, how='left')
        dfindex = df.loc[df.Value.isnull()].drop(columns='Value', errors='ignore')

    ## Left merge to create NaN's in dfcheck for parameters missing from indexsets
    dfcheck = dfindex.merge(dfs[_param], on=None, how='left')

    ## Filter out ignored indices if necessary
    for key, val in kwargs.get('skip', {}).items():
        if kwargs.get('skip_type') == 'start':
            for j in val:
                dfcheck = dfcheck.loc[~dfcheck[key].str.startswith(j)].copy()
        else:
            dfcheck = dfcheck.loc[~dfcheck[key].isin(val)].copy()

    ## Raise exception if there are any NaN's in dfcheck
    check_df(dfcheck, param, kwargs)
    print(f"{param:<30}: passed ({len(dfcheck)} values)")
    return dfcheck


#%% Procedure
if __name__ == '__main__':
    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(casepath,'gamslog.txt'),
    )

    #%% Get inputs dictionary and switches
    print('Load inputs.gdx for error checking')
    inputs = gdxpds.to_dataframes(os.path.join(casepath, 'inputs_case', 'inputs.gdx'))

    sw = reeds.io.get_switches(casepath)

    #%% Get parameters to check
    yamlpath = os.path.join(casepath, 'inputs_case', 'objective_function_params.yaml')
    with open(yamlpath) as f:
        objective_function_params = yaml.safe_load(f)

    #%% Run the checks
    for param, kwargs in objective_function_params.items():
        # #%% For debugging
        # param = 'gasprice'
        # kwargs = objective_function_params[param]
        dfcheck = check_param(param, kwargs, inputs, sw)

    #%% Done
    reeds.log.toc(tic=tic, year=0, process='input_processing/check_inputs.py', path=casepath)
