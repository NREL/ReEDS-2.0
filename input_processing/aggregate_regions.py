"""
prbrown 20220421

Notes to user:
--------------
* This script loops over files in runs/{}/inputs_case/ and aggregates them
  based on the directions given in inputs/userinput/aggregate_region_files.csv.
    * If new files have been added to inputs_case, you'll need to add rows with 
      processing directions to aggregate_region_files.csv. 
    * The column names should be self-explanatory; most likely there's also at least
      one similarly-formatted file in inputs_case that you can copy the settings for.
* Some files are aggregated in other scripts:
    * WriteHintage.py (these files are handled upstream since
      aggregation affects the clustering of generators into (b/h/v)intages):
        * hintage_data.csv 
    * transmission_multilink.py (these files are handled upstream since the multilink optimal-path
      algorithm needs to use the final topology):
        * trans_multilink_converters.csv
        * trans_multilink_paths.csv
        * trans_multilink_segments.csv
        * transmission_vsc_routes.csv
        * transmission_vsc_regions.csv

TODO
* Decide whether to fix VRE supply curves. (Currently we're grouping over the old
  bins but would be better to create new bins at the aggregated resolution.)
"""

#%%########
### IMPORTS
import gdxpds
import pandas as pd
import numpy as np
import os, sys, csv, pickle, shutil
import argparse
from glob import glob
from warnings import warn

#%% Direct print and errors to log file
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
#%% Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()

#%%#################
### FIXED INPUTS ###
decimals = 6
### anchortype: 'load' sets rb with largest 2010 load as anchor reg;
### 'size' sets largest rb as anchor reg
anchortype = 'size'

#%%###############################
### Functions and dictionaries ###
the_unnamer = {'Unnamed: {}'.format(i): '' for i in range(1000)}

aggfuncmap = {
    'mode': pd.Series.mode,
}


#%%####################
### ARGUMENT INPUTS ###
parser = argparse.ArgumentParser(description='Extend inputs to arbitrary future year')
parser.add_argument('basedir', help='path to ReEDS directory')
parser.add_argument('inputs_case', help='path to inputs_case directory')

args = parser.parse_args()
basedir = args.basedir
inputs_case = os.path.join(args.inputs_case)

# #%%#########################
# ### Settings for testing ###
# basedir = os.path.expanduser('~/github2/ReEDS-2.0')
# inputs_case = os.path.join(
#     basedir,'runs','v20221014_PTDFm0_ERCOT_h8760_agg1','inputs_case')

#%% Inputs from switches
sw = pd.read_csv(
    os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)
endyear = int(sw.endyear)
###### Inputs related to debugging
### Set debug == True to copy the original files to a new folder (inputs_case_original).
### If debug == False, the original files are overwritten.
debug = True
### missing: 'raise' or 'warn'
missing = 'raise'
### verbose: 0, 1, 2
verbose = 2

#%%###################
### Derived inputs ###

#%% Get the case name (ReEDS-2.0/runs/{casename}/inputscase/)
casename = inputs_case.split(os.sep)[-3]

#%% DEBUG: Copy the original inputs_case files
if debug and int(sw['GSw_AggregateRegions']):
    import distutils.dir_util
    os.makedirs(inputs_case+'_original', exist_ok=True)
    distutils.dir_util.copy_tree(inputs_case, inputs_case+'_original')

#%% Get the region hierarchy
hierarchy = pd.read_csv(
    os.path.join(inputs_case,'hierarchy.csv')
).rename(columns={'*r':'r'}).set_index('r')
rb2aggreg = hierarchy.aggreg.copy()

#%% Get the rb-to-rs map
rsmap = pd.read_csv(
    os.path.join(basedir,'inputs','rsmap_sreg.csv'), index_col='rs', squeeze=True)
### Make all-regions-to-aggreg map
r2aggreg = pd.concat([rb2aggreg, rsmap.map(rb2aggreg)])

#%% Write the full set of regions
pd.Series(hierarchy.index.values).to_csv(
    os.path.join(inputs_case, 'rb.csv'), index=False, header=False)
pd.Series(hierarchy.aggreg.unique()).to_csv(
    os.path.join(inputs_case, 'aggreg.csv'), index=False, header=False)
if not int(sw['GSw_IndividualSites']):
    pd.Series(rsmap.index.values).to_csv(
        os.path.join(inputs_case, 'rs.csv'), index=False, header=False)
    pd.concat([pd.Series(hierarchy.index), pd.Series(rsmap.index)]).to_csv(
        os.path.join(inputs_case, 'r.csv'), index=False, header=False)

#%%##############################################
### If using default 134 regions, exit the script
if not int(sw['GSw_AggregateRegions']):
    print('GSw_AggregationRegions = 0, so skip aggregate_regions.py')
    quit()
else:
    print('Starting aggregate_regions.py', flush=True)

#%%### Get the "anchor" zone for each aggregation region
### For transmission we want to use the old endpoints to avoid requiring a new run of the
### reV least-cost-paths procedure.
if anchortype in ['load','demand','MW','MWh']:
    ### Take the "anchor" zone as the zone with the largest annual demand in 2010.
    ## Get annual average load
    load = pd.read_csv(
        os.path.join(basedir, 'inputs', 'variability', 'multi_year', 'load.csv.gz'),
        index_col=0,
    ).mean().rename_axis('r').rename('MW').to_frame()
    ## Add column for new regions
    load['aggreg'] = load.index.map(r2aggreg)
    ## Take the original zone with largest demand
    aggreg2anchorreg = load.groupby('aggreg').idxmax()['MW'].rename('rb')
elif anchortype in ['size','km2','area']:
    ### Take the "anchor" zone as the zone with the largest area [km2]
    import geopandas as gpd
    dfba = gpd.read_file(os.path.join(basedir,'inputs','shapefiles','US_PCA')).set_index('rb')
    dfba['km2'] = dfba.area / 1e6
    ## Add column for new regions
    dfba['aggreg'] = dfba.index.map(r2aggreg)
    ## Take the original zone with largest area
    aggreg2anchorreg = dfba.groupby('aggreg').km2.idxmax().rename('rb')
else:
    raise ValueError(f'Invalid choice of anchortype: {anchortype}')

anchorreg2aggreg = pd.Series(index=aggreg2anchorreg.values, data=aggreg2anchorreg.index)
## Save it for plotting
aggreg2anchorreg.to_csv(os.path.join(inputs_case, 'aggreg2anchorreg.csv'))

#%%### Get RSC VRE available capacity to use in capacity-weighted averages
### We need the original un-aggregated supply curves, so run writesupplycurves again
# rscweight = pd.read_csv(os.path.join(inputs_case, 'rsc_combined.csv'))
import writesupplycurves
rscweight = writesupplycurves.main(
    basedir, inputs_case, GSw_AggregateRegions=0, write=False)
rscweight = (
    rscweight.loc[(rscweight.sc_cat=='cap')]
    .rename(columns={'*i':'i'})
    .drop_duplicates(subset=['i','r','rscbin'])
    [['i','r','rscbin','value']].rename(columns={'value':'MW'})
).copy()

#%% Get distpv capacity to use in capacity-weighted averages
distpvcap = pd.read_csv(
    os.path.join(inputs_case, 'distPVcap.csv'), index_col=0
### TODO: Need a single year so arbitrarily use 2036
)['2036'].rename_axis('r').rename('MW')
## Add it to rscweight_nobin
rscweight_nobin = rscweight.groupby(['i','r'], as_index=False).sum()
rscweight_nobin = pd.concat([rscweight_nobin, distpvcap.reset_index().assign(i='distpv')], axis=0)


#%% Get the settings file
aggfiles = pd.read_csv(
    os.path.join(basedir, 'inputs', 'userinput', 'aggregate_region_files.csv'),
    dtype={'fix_cols':str},
).fillna({'fix_cols':''})
#%% If any files are missing, stop and alert the user
inputfiles = [os.path.basename(f) for f in glob(os.path.join(inputs_case,'*'))]
missingfiles = [
    f for f in inputfiles if ((f not in aggfiles.filename.values) and ('.' in f))]
if any(missingfiles):
    if missing == 'raise':
        raise Exception(
            'Missing aggregation method for:\n{}\n'
            '>>> Need to add entries for these files to aggregate_region_files.csv'
            .format('\n'.join(missingfiles))
        )
    else:
        from warnings import warn
        warn(
            'Missing aggregation directions for:\n{}\n'
            '>>> For this run, these files are copied without modification'
            .format('\n'.join(missingfiles))
        )
        for filename in missingfiles:
            shutil.copy(os.path.join(inputs_case, filename), os.path.join(inputs_case, filename))
            print('copied {}, which is missing from aggregate_region_files.csv'.format(filename),
                flush=True)

#%% Loop it
for i, row in aggfiles.iterrows():
    ### For debugging: Specify a single file to process
    # i = 195
    # row = aggfiles.loc[i]
    print('{:-<45}> '.format(row.filename+' '), end='', flush=True)
    filetic = datetime.datetime.now()
    #%% continue loop
    filename = aggfiles.loc[i, 'filename']
    if aggfiles.loc[i,'ignore'] == 0:
        pass
    ### if ignore == 1, just copy the file to inputs_case and skip the rest
    elif int(aggfiles.loc[i, 'ignore']):
        if verbose > 1:
            print('ignored', flush=True)
        continue

    #%% If the file isn't in inputs_case, skip it
    if filename not in inputfiles:
        if verbose > 1:
            print('skipped since not in inputs_case')
        continue

    #%% Settings
    ### header: 0 if file has column labels, otherwise 'None'
    header = (None if row['header'] in ['None','none','',None,np.nan]
              else 'keepindex' if row['header'] == 'keepindex'
              else int(row['header']))
    ### rb_col: usually 'r', 'rb', or 'region', or 'wide' if file uses regions as columns
    rb_col = row['rb_col']
    rb_cols = rb_col.split(',')
    ### aggfunc: usually 'sum' or 'mean', with special cases defined above
    aggfunc = aggfuncmap.get(row['aggfunc'], row['aggfunc'])
    ### wide: 1 if any parameters are in wide format, otherwise 0
    wide = int(row['wide'])
    filetype = row['filetype']
    ### key: only used for gdx files, indicating the parameter name. 
    ### gdx files need a separate line in aggregate_region_files.csv for each parameter.
    key = row['key']
    ### fix_cols: indicate columns to use as for fields that should be projected
    ### independently to future years (e.g. r, szn, tech)
    fix_cols = row['fix_cols']
    fix_cols = (list() if fix_cols in ['None','none','',None,np.nan] else fix_cols.split(','))
    ## special cases
    if filename == 'load.h5':
        if sw['GSw_EFS1_AllYearLoad'] == 'default':
            fix_cols = ['hour']
        else:
            fix_cols = ['year','hour']


    #%%### Load it
    if filetype in ['.csv', '.csv.gz']:
        dfin = pd.read_csv(os.path.join(inputs_case, filename), header=header,)
    elif filetype == '.h5':
        dfin = pd.read_hdf(os.path.join(inputs_case, filename))
        if header == 'keepindex':
            indexnames = list(dfin.index.names)
            if (len(indexnames) == 1) and (not indexnames[0]):
                indexnames = ['index']
            dfin.reset_index(inplace=True)
    elif filetype == '.gdx':
        ### Read in the full gdx file, but only change the 'key' parameter
        ### given in aggfiles. That's wasteful, but currently there's only
        ### one gdx file (cccurt_defaults.gdx) and we ignore it by default since
        ### it's only used for intertemporal/windows. To speed things up we could 
        ### change that file to .csv.
        dfall = gdxpds.to_dataframes(os.path.join(inputs_case, filename))
        dfin = dfall[key]
    else:
        raise Exception('Unsupported filetype: {}'.format(filename))

    dfin.rename(columns={c:str(c) for c in dfin.columns}, inplace=True)
    columns = dfin.columns.tolist()


    #%%### Reshape to long format
    if (aggfunc == 'sc_cat') and (not wide):
        ### Supply-curve format. Expect an sc_cat column with 'cap' and 'cost' values.
        ## 'cap' values are summed; 'cost' values use the 'cap'-weighted mean
        df = dfin.pivot(index=fix_cols+rb_cols,columns='sc_cat',values=key).reset_index()
    elif (aggfunc == 'sc_cat') and wide and (len(fix_cols) == 1):
        ### Supply-curve format. Expect an sc_cat column with 'cap' and 'cost' values.
        ## Some value other than rb is in wide format
        ## So turn rb and the wide value into the index
        df = dfin.set_index(rb_cols+['sc_cat']).stack().rename('value')
        df.index = df.index.rename(rb_cols+['sc_cat','wide'])
        ## Make value columns for 'cap' and 'cost'
        df = df.unstack('sc_cat').reset_index()
    elif not wide:
        ### File is already long so don't do anything
        df = dfin.copy()
    elif wide and (rb_col != 'wide') and (len(fix_cols) == 1) and (fix_cols[0] == 'wide'):
        ## Some value other than rb is in wide format
        ## So turn rb and the wide value into the index
        df = dfin.set_index(rb_col).stack().rename('value')
        df.index = df.index.rename([rb_col, 'wide'])
        ## Turn index into columns
        df = df.reset_index()
    elif wide and (rb_col != 'wide') and (len(fix_cols) > 1) and ('wide' in fix_cols):
        ## Some value other than rb is in wide format
        ## So turn rb, other fix_cols, and the wide value into the index
        df = dfin.set_index([rb_col]+[c for c in fix_cols if c != 'wide']).stack().rename('value')
        df.index = df.index.rename([rb_col]+fix_cols)
        ## Turn index into columns
        df = df.reset_index()
    elif wide and (rb_col == 'wide') and len(fix_cols):
        ### File has some fixed columns and then regions in wide format
        df = (
            ## Turn all identifying columns into indices, with rb as the last index
            dfin.set_index(fix_cols).stack()
            ## Name the rb column 'wide'
            .rename_axis(fix_cols+['wide']).rename('value')
            ## Turn index into columns
            .reset_index()
        )


    #%%### Aggregate by region
    df1 = df.copy()
    ### Map old regions to new regions
    if aggfunc not in ['trans_lookup','mean_cap','recf']:
        for c in rb_cols:
            df1[c] = df1[c].map(lambda x: r2aggreg.get(x,x))

    ### Group according to aggfunc
    if aggfunc == 'sc_cat':
        ## Weight cost by cap
        df1['cap_times_cost'] = df1['cap'] * df1['cost']
        ## Sum everything
        df1 = df1.groupby(fix_cols+[rb_col]).sum()
        ## Divide cost*cap by cap
        df1['cost'] = df1['cap_times_cost'] / df1['cap']
        df1.drop(['cap_times_cost'], axis=1, inplace=True)
    elif aggfunc == 'trans_lookup':
        ## Get data for anchor zones
        for c in rb_cols:
            df1 = df1.loc[df1[c].isin(aggreg2anchorreg)].copy()
        ## Map to aggregated regions
        for c in rb_cols:
            df1[c] = df1[c].map(anchorreg2aggreg)
    elif aggfunc == 'mean_cap':
        df1 = (
            df1.rename(columns={'value':'cf'})
            .merge(
                (rscweight_nobin.rename(columns={'i':'*i'}) if '*i' in fix_cols
                else rscweight_nobin),
                on=['r',('*i' if '*i' in fix_cols else 'i')], how='left')
            ## There are some nan's because we subtract existing capacity from the supply curve.
            ## Fill them with 1 MW for now, but it would be better to change that procedure.
            ## Note also that the weighting will be off
            .fillna(1)
        )
        ### Similar procedure as above for aggfunc == 'sc_cat'
        df1 = (
            df1
            .assign(r=df1.r.map(r2aggreg))
            .assign(cap_times_cf=df1.cf*df1.MW)
            .groupby(fix_cols+rb_cols).sum()
        )
        df1.cf = df1.cap_times_cf / df1.MW
        df1 = df1.drop(['cap_times_cf','MW'], axis=1).rename(columns={'cf':'value'})
    elif aggfunc == 'resources':
        ### Special case: Rebuild the 'resources' column as {tech}_{region}
        df1 = (
            df1
            .assign(resource=df1.i+'_'+df1.r)
            .drop_duplicates()
        )
    elif aggfunc == 'recf':
        ### Special case: Region is embedded in the 'resources' column as {tech}_{region}
        col2r = dict(zip(columns, [c.split('_')[-1] for c in columns]))
        col2i = dict(zip(columns, ['_'.join(c.split('_')[:-1]) for c in columns]))
        df1 = df1.rename(columns={'value':'cf'})
        df1['r'] = df1[rb_col].map(col2r)
        df1['i'] = df1[rb_col].map(col2i).replace({'distpv':'distpv'})
        ## Get capacities
        df1 = df1.merge(rscweight_nobin, on=['r','i'], how='left')
        ## Similar procedure as above for aggfunc == 'sc_cat'
        df1 = (
            df1
            .assign(r=df1.r.map(r2aggreg))
            .assign(cap_times_cf=df1.cf*df1.MW)
            .groupby(['index','i','r']).sum()
        )
        df1.cf = df1.cap_times_cf / df1.MW
        df1 = df1.rename(columns={'cf':'value'}).reset_index()
        ## Remake the resources (column names) with new regions
        df1['wide'] = df1.i + '_' + df1.r
        df1 = df1.set_index(['index','wide'])[['value']].astype(np.float16)
    else:
        df1 = df1.groupby(fix_cols+rb_cols).agg(aggfunc)


    #%%### Put back in original format
    if (aggfunc == 'sc_cat') and (not wide):
        dfout = df1.stack().rename(key).reset_index()[columns]
    elif (aggfunc == 'sc_cat') and wide and (len(fix_cols) == 1):
        dfout = df1.stack().rename('value').unstack('wide').reset_index()[columns].fillna(0)
    elif not wide:
        dfout = df1.reset_index()[columns]
    elif (wide) and (rb_col != 'wide') and (len(fix_cols) == 1) and (fix_cols[0] == 'wide'):
        dfout = df1.unstack('wide')['value'].reset_index()
    elif (wide) and (rb_col != 'wide') and (len(fix_cols) > 1) and ('wide' in fix_cols):
        dfout = df1.unstack('wide')['value'].reset_index()[columns]
    elif wide and (rb_col == 'wide') and len(fix_cols):
        dfout = df1.unstack('wide')['value'].reset_index()

    ### Drop rows where r and rr are the same
    if key == 'drop_dup_r':
        dfout = dfout.loc[dfout[rb_cols[0]] != dfout[rb_cols[1]]].copy()

    #%% Unname any unnamed columns
    dfout.rename(columns=the_unnamer, inplace=True)

    #%%### Write it
    if filetype in ['.csv','.csv.gz']:
        dfout.round(decimals).to_csv(
            os.path.join(inputs_case, filename),
            header=(False if header is None else True),
            index=False,
        )
    elif filetype == '.h5':
        if header == 'keepindex':
            dfwrite = dfout.sort_values(indexnames).set_index(indexnames)
            dfwrite.columns.name = None
        else:
            dfwrite = dfout
        dfwrite.to_hdf(
            os.path.join(inputs_case, filename), key='data', complevel=4, format='table')
    elif filetype == '.gdx':
        ### Overwrite the projected parameter
        dfall[key] = dfout.round(decimals)
        ### Write the whole file
        gdxpds.to_gdx(dfall, inputs_case+filename)

    if verbose > 1:
        now = datetime.datetime.now()
        print('aggregated ({:.1f} seconds)'.format((now-filetic).total_seconds()), flush=True)


#%% Finish
toc(tic=tic, year=0, process='input_processing/aggregate_regions.py', 
    path=os.path.join(inputs_case,'..'))
print('Finished aggregate_regions.py')
