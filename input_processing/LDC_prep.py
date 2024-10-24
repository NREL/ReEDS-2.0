'''
This script handles the modifications of static inputs for the first solve year. These inputs
include the 8760 load and 8760 renewable energy capacity factor (RECF) profiles. RECF and
resource data for various technologies are combined into single files for output:

Load:
        - Scale load profiles by distribution loss factor and load calibration factor
Resources:
        - Creates a resource-to-(i,r,ccreg) lookup table for use in hourly_writesupplycurves.py 
          and Augur
        - Add the distributed PV resources
RECF:
        - Add the distributed PV recf profiles
        - Sort the columns in recf to be in the same order as the rows in resources
        - Scale distributed resource CF profiles by distribution loss factor and tiein loss factor
'''

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import h5py
import numpy as np
import os
import pandas as pd
import re
import sys

import logging
from pathlib import Path
from pandas.api.types import is_float_dtype 

logger = logging.getLogger(__file__)

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def read_h5py_file(filename: Path | str) -> pd.DataFrame:
    """Return dataframe object for a h5py file.

    This function returns a pandas dataframe of a h5py file. If the file has multiple dataset on it
    means it has yearly index.

    Parameters
    ----------
    filename
        File path to read

    Returns
    -------
    pd.DataFrame
        Pandas dataframe of the file
    """
    
    valid_data_keys = ["data", "cf", "load", "evload"]

    with h5py.File(filename, "r") as f:
        # Identify keys in h5 file and check for overlap with valid key set
        keys = list(f.keys())
        datakey = list(set(keys).intersection(valid_data_keys))

        # Adding safety check to validate that it only returns one key
        assert len(datakey) <= 1, f"Multiple keys={datakey} found for {filename}"
        datakey = datakey[0] if datakey else None

        # standard approach for data with one of the matching keys
        if datakey in keys:
            # load data
            df = pd.DataFrame(f[datakey][:])
            # check for indices
            idx_cols = [c for c in keys if 'index' in c]
            idx_cols.sort()
            idx_cols_out = []
            # loop over indices and add to data
            if len(idx_cols) == 1 and idx_cols[0] == "index":
                df.index = pd.Series(f["index"]).values
            else:
                for idx_col in idx_cols:
                    # with multindex expecting the word 'index' plus a number indicating the order
                    # based on format specified when writing out h5 files in copy_files
                    idx_col_out = re.sub('index[0-9]*_', '', idx_col)
                    idx_cols_out.append(idx_col_out)
                    df[idx_col_out] = pd.Series(f[idx_col]).values
                df = df.set_index(idx_cols_out)
        # if none of these keys work, we're dealing with EER-formatted load
        else:
            years = [column for column in keys if column.isdigit()]
            # Extract all the years and concat them in a single dataframe.
            df = pd.concat({int(y): pd.DataFrame(f[y][...]) for y in years}, axis=0)
            df.index = df.index.rename(["year", "hour"])
        
        # add columns to data if specified
        if 'columns' in keys:
            df.columns = (pd.Series(f["columns"]).map(lambda x: x if isinstance(x, str) else x.decode("utf-8")).values)

    return df

def read_file(filename: Path | str, **kwargs) -> pd.DataFrame:
    """Return dataframe object of input file for multiple file formats.

    This function read multiple file formats for h5 file sand returns a dataframe from the file. 

    Parameters
    ----------
    filename
        File path to read

    Returns
    -------
    pd.DataFrame
        Pandas dataframe of the file

    Raises
    ------
    FileNotFoundError
        If the file does not exists
    """
    if isinstance(filename, str):
        filename = Path(filename)

    if not filename.exists():
        raise FileNotFoundError(f"Mandatory file {filename} does not exist.")

    # We have two cases, either the data is contained as a single dataframe or we have multiple
    # datasets that composes the h5 file. For a single dataset we use pandas (since it is the most
    # convenient) and h5py for the custom h5 file.
    try:
        df = pd.read_hdf(filename)

    except ValueError:
        df = read_h5py_file(filename)
    
    # All values being NaN indicates that the region filtering in copy_files.py removed all
    # data, leaving an empty dataframe.
    # Return an empty dataframe with the original file's index if all values are NaN
    if all(df.isnull().all()):
        df = df.drop(columns=df.columns)
        return df

    # NOTE: Some files are saved as float16, so we cast to float32 to prevent issues with
    # large/small numbers
    numeric_cols = [c for c in df if is_float_dtype(df[c].dtype)]
    df = df.astype({column:np.float32 for column in numeric_cols})
    
    return df


def local_to_eastern(df, inputs_case, by_year=False):
    """
    Convert a wide dataframe from local to eastern time.
    The column names are assumed to end with _{r}.
    
    --- Inputs ---
    by_year: Indicate whether to roll by year (True) or to roll the whole
    dataset at once (False)
    """
    ### Get some inputs
    r2tz = pd.read_csv(
        os.path.join(inputs_case,'reeds_region_tz_map.csv'),
        index_col='r')

    r2tz['hourshift'] = r2tz.tz.map({'PT':+3, 'MT':+2, 'CT':+1, 'ET':0, 'AT':-1, 'NT': -2})
    r2tz.dropna(inplace = True)
    r2shift = r2tz.drop('tz', axis = 1)
    r2shift['hourshift'] = r2shift['hourshift'].astype(int)
    ### Roll the input columns according to the shift
    if by_year:
        dfout = pd.concat({
            year: pd.DataFrame(
                {col: np.roll(df.loc[year][col], r2shift.loc[col.split('|')[-1]]) for col in df},
                index=df.loc[year].index)
            for year in df.index.get_level_values('year').unique()
        }, axis=0, names=('year',))
    else:
        dfout = pd.DataFrame(
            {col: np.roll(df[col], r2shift.loc[col.split('|')[-1]]) for col in df},
            index=df.index)

    return dfout


def csp_dispatch(cfcsp, sm=2.4, storage_duration=10):
    """
    Use a simple no-foresight heuristic to dispatch CSP.
    Excess energy from the solar field (i.e. energy above the max plant power output)
    is sent to storage, and energy in storage is dispatched as soon as possible.

    --- Inputs ---
    cfcsp: hourly energy output of solar field [fraction of max field output]
    sm: solar multiple [solar field max output / plant max power output]
    storage_duration: hours of storage as multiple of plant max power output
    """
    ### Calculate derived dataframes
    ## Field energy output as fraction of plant max output
    dfcf = cfcsp * sm
    ## Excess energy as fraction of plant max output
    clipped = (dfcf - 1).clip(lower=0)
    ## Remaining generator capacity after direct dispatch (can be used for storage dispatch)
    headspace = (1 - dfcf).clip(lower=0)
    ## Direct generation from solar field
    direct_dispatch = dfcf.clip(upper=1)

    ### Numpy arrays
    clipped_val = clipped.values
    headspace_val = headspace.values
    hours = range(len(clipped_val))
    storage_dispatch = np.zeros(clipped_val.shape)
    ## Need one extra storage hour at the end, though it doesn't affect dispatch
    storage_energy_hourstart = np.zeros((len(hours)+1, clipped_val.shape[1]))

    ### Loop over all hours and simulate dispatch
    for h in hours:
        ### storage dispatch is...
        storage_dispatch[h] = np.where(
            clipped_val[h],
            ## zero if there's clipping in hour
            0,
            ## otherwise...
            np.where(
                headspace_val[h] > storage_energy_hourstart[h],
                ## storage energy at start of hour if more headspace than energy
                storage_energy_hourstart[h],
                ## headspace if more storage energy than headspace
                headspace_val[h]
            )
        )
        ### storage energy at start of next hour is...
        storage_energy_hourstart[h+1] = np.where(
            clipped_val[h],
            ## storage energy in current hour plus clipping if clipping
            storage_energy_hourstart[h] + clipped_val[h],
            ## storage energy in current hour minus dispatch if not clipping
            storage_energy_hourstart[h] - storage_dispatch[h]
        )
        storage_energy_hourstart[h+1] = np.where(
            storage_energy_hourstart[h+1] > storage_duration,
            ## clip storage energy to storage duration if energy > duration
            storage_duration,
            ## otherwise no change
            storage_energy_hourstart[h+1]
        )

    ### Format as dataframe and calculate total plant dispatch
    storage_dispatch = pd.DataFrame(
        index=clipped.index, columns=clipped.columns, data=storage_dispatch)

    total_dispatch = direct_dispatch + storage_dispatch

    return total_dispatch


def get_distpv_profiles(inputs_case, recf, rb2fips, agglevel):
    """
    We only have one year's profile (2012) for distributed PV. Because we want to
    maintain weather coincidence between distpv and upv, we start with the lowest-cf
    upv profile in each region, scale it by its CF ratio with distributed PV in that
    region, and take that scaled profile as the distpv profile.
    """
    ### Get average CF (used to scale down UPV profiles to generate distpv profiles)
    distpv_meancf = (
        pd.read_csv(os.path.join(inputs_case,'distpvcf_hourly.csv'), index_col=0)
          .mean(axis=1).rename_axis('ba').rename('cf')
        )
    ### Uniformly disaggregate regions if running at county level
    if agglevel == 'county':
        distpv_meancf = distpv_meancf.reset_index()
        distpv_meancf = (distpv_meancf.merge(rb2fips,how='inner')
                                      .set_index('r'))['cf']
    ### Get the worst upv resource in each region and use its profile for distpv,
    ### scaled by the distpv/upv CF ratio
    upv_cf = (
        recf[[c for c in recf if c.startswith('upv')]].mean()
        .rename_axis('resource').rename('cf').reset_index()
        )
    upv_cf['r'] = upv_cf.resource.map(lambda x: x.split('|')[-1])
    worst_upv = (
        upv_cf.sort_values(['r','cf'])
        .drop_duplicates('r', keep='first').set_index('r').resource
        )
    ### Get the distpv/upv CF ratio for those UPV resources
    distpv_upv_cf_ratio = (
        distpv_meancf / upv_cf.set_index('resource').loc[worst_upv].set_index('r').cf
        )
    ### Scale UPV Profiles by distpv/upv CF ratio
    distpv_profiles = (
        recf[worst_upv].rename(columns=dict(zip(worst_upv,worst_upv.index)))
        * distpv_upv_cf_ratio
    ).clip(upper=1)
    distpv_profiles.columns = 'distpv|' + distpv_profiles.columns

    return distpv_profiles


def fix_class_region_delimiter(df):
    """
    Replace {class}_{region} with {class}|{region}.
    Eventually we'll update the names upstream in hourlize and won't require this step.
    """
    if not df.empty:
        if '|' not in df.columns[0]:
            df.columns = [c.replace('_','|',1) for c in df.columns]


#%% ===========================================================================
### --- MAIN FUNCTION ---
### ===========================================================================
def main(reeds_path, inputs_case):
    print('Starting ldc_prep.py')
    
    # #%% Settings for testing
    # reeds_path = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
    # inputs_case = os.path.join(
    #     reeds_path,'runs','v20240904_vcM1_Everything','inputs_case')

    #%% Inputs from switches
    sw = pd.read_csv(
        os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0,
    ).squeeze(1)
    GSw_EFS1_AllYearLoad = sw.GSw_EFS1_AllYearLoad
    GSw_CSP_Types = [int(i) for i in sw.GSw_CSP_Types.split('_')]
    GSw_PVB_Types = sw.GSw_PVB_Types
    GSw_PVB = int(sw.GSw_PVB)
    GSw_LoadAdjust = int(sw.GSw_LoadAdjust)
    GSw_LoadAdjust_Profiles=sw.GSw_LoadAdjust_Profiles
    GSw_LoadAdjust_Adoption=sw.GSw_LoadAdjust_Adoption

    # ReEDS only supports a single entry for agglevel right now, so use the
    # first value from the list (copy_files.py already ensures that only one
    # value is present)
    # The 'lvl' variable ensures that BA and larger spatial aggregations use BA data and methods
    agglevel = pd.read_csv(
        os.path.join(inputs_case, 'agglevels.csv')).squeeze(1).tolist()[0]
    lvl = 'ba' if agglevel in ['ba','state','aggreg'] else 'county'

    #%%### Load inputs

    # -------- Datetime mapper --------
    hdtmap = pd.read_csv(os.path.join(inputs_case, 'h_dt_szn.csv'))

    ###### Load the input parameters
    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, usecols=[0,1], index_col=0).squeeze(1)
    ### distloss
    distloss = scalars['distloss']

    ### BAs present in the current run
    val_r_all = sorted(
        pd.read_csv(
             os.path.join(inputs_case, 'val_r_all.csv'), header=None,
        ).squeeze(1).tolist()
    )
    ### Years in the current run
    solveyears = pd.read_csv(
        os.path.join(inputs_case,'modeledyears.csv'),
        header=0
    ).columns.astype(int).values

    ### Load spatial hierarchy
    hierarchy = pd.read_csv(
        os.path.join(inputs_case,'hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    hierarchy_original = (
        pd.read_csv(os.path.join(inputs_case, 'hierarchy_original.csv'))
        .rename(columns={'ba':'r'})
        .set_index('r')
    )
    ### Add ccreg column with the desired hierarchy level
    if sw['capcredit_hierarchy_level'] == 'r':
        hierarchy['ccreg'] = hierarchy.index.copy()
        hierarchy_original['ccreg'] = hierarchy_original.index.copy()
    else:
        hierarchy['ccreg'] = hierarchy[sw.capcredit_hierarchy_level].copy()
        hierarchy_original['ccreg'] = hierarchy_original[sw.capcredit_hierarchy_level].copy()
    ### Map regions to new ccreg's
    rb2fips = pd.read_csv(os.path.join(inputs_case,'r_ba.csv'))
    if agglevel =='county' :
        r2ccreg = hierarchy['ccreg']
    else:
        r2ccreg = hierarchy_original['ccreg']

    # Map BAs to states and census divisions for use with AEO load multipliers
    st2rb = hierarchy.reset_index(drop=False)[['r', 'st']]
    cd2rb = hierarchy.reset_index(drop=False)[['r', 'cendiv']]

    # Get technology subsets
    tech_table = pd.read_csv(
        os.path.join(inputs_case,'tech-subset-table.csv'), index_col=0).fillna(False).astype(bool)
    techs = {tech:list() for tech in list(tech_table)}
    for tech in techs.keys():
        techs[tech] = tech_table[tech_table[tech]].index.values.tolist()
        techs[tech] = [x.lower() for x in techs[tech]]
        temp_save = []
        temp_remove = []
        # Interpreting GAMS syntax in tech-subset-table.csv
        for subset in techs[tech]:
            if '*' in subset:
                temp_remove.append(subset)
                temp = subset.split('*')
                temp2 = temp[0].split('_')
                temp_low = pd.to_numeric(temp[0].split('_')[-1])
                temp_high = pd.to_numeric(temp[1].split('_')[-1])
                temp_tech = ''
                for n in range(0,len(temp2)-1):
                    temp_tech += temp2[n]
                    if not n == len(temp2)-2:
                        temp_tech += '_'
                for c in range(temp_low,temp_high+1):
                    temp_save.append('{}_{}'.format(temp_tech,str(c)))
        for subset in temp_remove:
            techs[tech].remove(subset)
        techs[tech].extend(temp_save)
    vre_dist = techs['VRE_DISTRIBUTED']

    # ------- Read in the static inputs for this run -------

    ### Onshore Wind
    df_windons = read_file(os.path.join(inputs_case,'recf_wind-ons.h5'))
    fix_class_region_delimiter(df_windons)
    df_windons.columns = ['wind-ons_' + col for col in df_windons]
    ### Don't do aggregation in this case, so make a 1:1 lookup table
    lookup = pd.DataFrame({'ragg':df_windons.columns.values})
    lookup['r'] = lookup.ragg.map(lambda x: x.rsplit('|',1)[1])
    lookup['i'] = lookup.ragg.map(lambda x: x.rsplit('|',1)[0])

    ### Offshore Wind
    df_windofs = read_file(os.path.join(inputs_case,'recf_wind-ofs.h5'))
    fix_class_region_delimiter(df_windofs)
    df_windofs.columns = ['wind-ofs_' + col for col in df_windofs]

    ### UPV
    df_upv = read_file(os.path.join(inputs_case,'recf_upv.h5'))
    fix_class_region_delimiter(df_upv)
    df_upv.columns = ['upv_' + col for col in df_upv]

    # If DUPV is turned off, create an empty dataframe with the same index as df_dupv to concat
    if int(sw['GSw_DUPV']) == 0: 
        df_dupv = pd.DataFrame(index=df_upv.index)
    elif int(sw['GSw_DUPV']) == 1:
        df_dupv = read_file(os.path.join('recf_dupv.h5'))
        fix_class_region_delimiter(df_dupv)
        df_dupv.columns = ['dupv_' + col for col in df_dupv]

    ### CSP
    cspcf = read_file(os.path.join(inputs_case,'recf_csp.h5'))
    fix_class_region_delimiter(cspcf)
    # If CSP is turned off, create an empty dataframe with an appropriate index
    if int(sw['GSw_CSP']) == 0:
        cspcf = pd.DataFrame(index=cspcf.index)

    ### Format PV+battery profiles
    # Get the PVB types
    pvb_ilr = pd.read_csv(
        os.path.join(inputs_case, 'pvb_ilr.csv'),
        header=0, names=['pvb_type','ilr'], index_col='pvb_type').squeeze(1)
    df_pvb = {}
    # Override GSw_PVB_Types if GSw_PVB is turned off
    GSw_PVB_Types = (
        [int(i) for i in GSw_PVB_Types.split('_')] if int(GSw_PVB)
        else []
    )
    for pvb_type in GSw_PVB_Types:
        ilr = int(pvb_ilr['pvb{}'.format(pvb_type)] * 100)
        # If PVB uses same ILR as UPV then use its profile
        infile = 'recf_upv' if ilr == scalars['ilr_utility'] * 100 else f'recf_upv_{ilr}AC'
        df_pvb[pvb_type] = read_file(os.path.join(inputs_case,infile+'.h5'))
        fix_class_region_delimiter(df_pvb[pvb_type])
        df_pvb[pvb_type].columns = [f'pvb{pvb_type}_{c}'
                                    for c in df_pvb[pvb_type].columns]
        df_pvb[pvb_type].index = df_upv.index.copy()

    ### Concat RECF data
    recf = pd.concat(
        [df_windons, df_windofs, df_upv, df_dupv]
        + [df_pvb[pvb_type] for pvb_type in df_pvb],
        sort=False, axis=1, copy=False)

    ### Add the other recf techs to the resources lookup table
    toadd = pd.DataFrame({'ragg': [c for c in recf.columns if c not in lookup.ragg.values]})
    toadd['r'] = [c.rsplit('|', 1)[1] for c in toadd.ragg.values]
    toadd['i'] = [c.rsplit('|', 1)[0] for c in toadd.ragg.values]
    resources = (
        pd.concat([lookup, toadd], axis=0, ignore_index=True)
        .rename(columns={'ragg':'resource','r':'area','i':'tech'})
        .sort_values('resource').reset_index(drop=True)
    )

    #%%%#########################################
    #    -- Performing Load Modifications --    #
    #############################################

    if GSw_EFS1_AllYearLoad == 'historic':
        load_historical = read_file(
            os.path.join(inputs_case,'load_hourly.h5')
        )
        # Read load multipliers
        load_multiplier = pd.read_csv(os.path.join(inputs_case, 'load_multiplier.csv'))
        
        if 'cendiv' in load_multiplier.columns:
            # AEO multipliers at the Census division level are in a wide format so
            # need to be changed to a long format
            load_multiplier = pd.melt(load_multiplier, id_vars=['cendiv'], 
                                      var_name='year', value_name='multiplier')
            load_multiplier['year'] = load_multiplier['year'].astype(int)
            # Map census division multipliers to BAs
            load_multiplier = load_multiplier.merge(cd2rb, on=['cendiv'], how='outer'
                                                    ).dropna(axis=0, how='any')
        else:
            # AEO multipliers at the state level are already in a long format
            # Map state multipliers to BAs
            load_multiplier = load_multiplier.merge(st2rb, on=['st'], how='outer'
                                                    ).dropna(axis=0, how='any')
        # Subset load multipliers for solve years only 
        load_multiplier = load_multiplier[load_multiplier['year'].isin(solveyears)
                                          ][['year', 'r', 'multiplier']]
        # Reformat hourly load profiles to merge with load multipliers
        load_historical.index = pd.MultiIndex.from_frame(hdtmap[['year','hour']])
        load_historical.reset_index(drop=False, inplace=True)
        load_historical = pd.melt(load_historical, id_vars=['year', 'hour'], 
                                  var_name='r', value_name='load')
        # Merge load multipliers into hourly load profiles 
        load_historical = load_historical.merge(load_multiplier, on=['r'], 
                                                how='outer', suffixes=('_w', '')
                                                ).reset_index(drop=True)
        load_historical.sort_values(by=['r', 'year'], ascending=True, inplace=True)
        load_historical['load'] *= load_historical['multiplier']
        load_historical = load_historical[['year', 'hour', 'r', 'load']]
        # Hours should be 0-8759 (not 1-8760) for later use with hourly_repperiods.py
        load_historical['hour'] -= 1
        # Reformat hourly load profiles for GAMS
        load_profiles = load_historical.pivot_table(index=['year', 'hour'], 
                                                    columns='r', values='load'
                                                    ).reset_index()
        load_profiles = load_profiles.set_index(['year', 'hour'])
        
    else:
        load_profiles = read_file(
            os.path.join(inputs_case,'load_hourly.h5'),
        ).loc[solveyears]
        ### If using EFS-style demand with only a single 2012 weather year, concat each profile
        ### 7 times to match the 7-year VRE profiles
        num_years = 7
        load_profiles_wide = load_profiles.unstack('year')
        if len(load_profiles_wide) == 8760:
            load_profiles = (
                pd.concat([load_profiles_wide] * num_years, axis=0, ignore_index=True)
                .rename_axis('hour').stack('year')
                .reorder_levels(['year','hour']).sort_index(axis=0, level=['year','hour'])
            )

    # ------- Perform Load Adjustments based on GSw_LoadAdjust ------- #
    if GSw_LoadAdjust:
        # Splitting load adjustment profiles and adoption rates
        LoadAdjust_Profiles = GSw_LoadAdjust_Profiles.split("__")
        LoadAdjust_Adoption = GSw_LoadAdjust_Adoption.split("__")
        # Checking for an equal # of load adjustment profiles and adoption rates
        if len(LoadAdjust_Adoption) != len(LoadAdjust_Profiles):
            sys.exit(
                "Number of GSw load adjustment profiles does not equal the "
                "same number of adoption rate profiles"
            )
        # Creating a list of load profile years and regions
        load_profiles_years = load_profiles.reset_index().year.unique().tolist()
        load_profiles_regions = load_profiles.columns.tolist()
        # Creating a load profile with specified adoption rates
        for i in range(len(GSw_LoadAdjust_Profiles)):
            # Reading in the load adjustment profiles and adoption rates
            profile = pd.read_csv(
                os.path.join(inputs_case, f'ghp_delta_{GSw_LoadAdjust_Profiles[i]}.csv'
                )
            )
            adoption = pd.read_csv(
                os.path.join(inputs_case, f'adoption_trajectories_{GSw_LoadAdjust_Adoption[i]}.csv'
                )
            )
            # Drop Years from adoption rates that are not in load profiles
            adoption = adoption[adoption["year"].isin(load_profiles_years)]
            # Reshape load adjustment profiles and adoption rates
            profile = pd.melt(
                profile, id_vars=["hour"], var_name="Regions", value_name="Amount"
            )
            adoption = pd.melt(
                adoption,
                id_vars=["year"],
                var_name="Regions",
                value_name="Adoption Rate",
            )
            # Merge adoption rates and load adjustment profiles on "Regions"
            adoption_by_profile = pd.merge(adoption, profile, on="Regions")

            # Calculate regional load adjustment (weighted by adoption rate)
            adoption_by_profile["Load Value"] = (
                adoption_by_profile["Adoption Rate"] * adoption_by_profile["Amount"]
            )
            #Drop unnecessary columns, filter regions, and create pivot table
            adoption_by_profile = adoption_by_profile.drop(
                columns=["Adoption Rate", "Amount"]
            )
            adoption_by_profile = adoption_by_profile[
                adoption_by_profile["Regions"].isin(load_profiles_regions)
            ]
            adoption_by_profile = pd.pivot(
                adoption_by_profile,
                index=["year", "hour"],
                columns="Regions",
                values="Load Value",
            )
            # Shaping the data to match the 7-year VRE profiles
            adoption_by_profile_wide = adoption_by_profile.unstack("year")
            if len(adoption_by_profile_wide) == 8760:
                adoption_by_profile = (
                    pd.concat([adoption_by_profile_wide] * 7, axis=0, ignore_index=True)
                    .rename_axis("hour")
                    .stack("year")
                    .reorder_levels(["year", "hour"])
                    .sort_index(axis=0, level=["year", "hour"])
                )
            # Adding the regional load adjustment to load_profiles
            load_profiles = pd.concat([load_profiles, adoption_by_profile])
            load_profiles = load_profiles.groupby(["year", "hour"]).sum()

    # Adjusting load profiles by distribution loss factor
    load_profiles /= (1 - distloss)

    #%%%#############################################
    #    -- Performing Resource Modifications --    #
    #################################################
    #### Distributed PV (distpv)
    ### Get distpv profiles
    distpv_profiles = get_distpv_profiles(inputs_case, recf, rb2fips, agglevel)
    ### Get distpv resources and include in list of resources
    distpv_resources = pd.DataFrame({'resource':distpv_profiles.columns, 'tech':'distpv'})
    distpv_resources['area'] = distpv_resources.resource.map(lambda x: x.split('|')[-1])

    # Resetting indices before merging to assure there are no issues in the merge
    resources = pd.concat([resources, distpv_resources], sort=False, ignore_index=True)
    recf = pd.merge(
        left=recf.reset_index(drop=True), right=distpv_profiles.reset_index(drop=True),
        left_index=True, right_index=True, copy=False)

    # Remove resources that are turned off
    if int(sw['GSw_distpv']) == 0:
        resources = resources[~resources['tech'].isin(['distpv'])]
    if int(sw['GSw_OfsWind']) == 0:
        wind_ofs_resource = ['wind-ofs_' + str(n) for n in range(1,16)]
        resources = resources[~resources['tech'].isin(wind_ofs_resource)]
    
    # Sorting profiles of resources to match the order of the rows in resources
    resources = resources.sort_values(['resource','area'])
    recf = recf.reindex(labels=resources['resource'].drop_duplicates(), axis=1, copy=False)

    ### Scale up dupv and distpv by 1/(1-distloss)
    recf.loc[
        :, resources.loc[resources.tech.isin(vre_dist),'resource'].values
    ] /= (1 - distloss)

    # Set the column names for resources to match ReEDS-2.0
    resources['ccreg'] = resources.area.map(r2ccreg)
    resources.rename(columns={'area':'r','tech':'i'}, inplace=True)
    resources = resources[['r','i','ccreg','resource']]


    #%%### Concentrated solar thermal power (CSP)
    ### Create CSP resource label for each CSP type (labeled by "tech" as csp1, csp2, etc)
    csptechs = [f'csp{c}' for c in GSw_CSP_Types]
    csp_resources = pd.concat({
        tech:
        pd.DataFrame({
            'resource': cspcf.columns,
            'r': cspcf.columns.map(lambda x: x.split('|')[1]),
            'class': cspcf.columns.map(lambda x: x.split('|')[0]),
        })
        for tech in csptechs
    }, axis=0, names=('tech',)).reset_index(level='tech')

    csp_resources = (
        csp_resources
        .assign(i=csp_resources['tech'] + '_' + csp_resources['class'].astype(str))
        .assign(resource=csp_resources['tech'] + '_' + csp_resources['resource'])
        .assign(ccreg=csp_resources.r.map(r2ccreg))
        [['i','r','resource','ccreg']]
    )

    ###### Simulate CSP dispatch for each design
    ### Get solar multiples
    sms = {tech: scalars[f'csp_sm_{tech.strip("csp")}'] for tech in csptechs}
    ### Get storage durations
    storage_duration = pd.read_csv(
        os.path.join(inputs_case,'storage_duration.csv'), header=None, index_col=0).squeeze(1)
    ## All CSP resource classes have the same duration for a given tech, so just take the first one
    durations = {tech: storage_duration[f'csp{tech.strip("csp")}_1'] for tech in csptechs}
    ### Run the dispatch simulation for modeled regions

    csp_system_cf = pd.concat({
        tech: csp_dispatch(cspcf, sm=sms[tech], storage_duration=durations[tech])
        for tech in csptechs
    }, axis=1)
    ## Collapse multiindex column labels to single strings
    csp_system_cf.columns = ['_'.join(c) for c in csp_system_cf.columns]

    ### Add CSP to RE output dataframes
    recf = pd.concat([recf, csp_system_cf.reset_index(drop=True)], axis=1)
    resources = pd.concat([resources, csp_resources], axis=0)


    #%%### Convert from local time to Eastern time
    recf_eastern = local_to_eastern(recf, inputs_case, by_year=False)
    load_eastern = local_to_eastern(load_profiles, inputs_case, by_year=True).astype(np.float32)
    cspcf_eastern = local_to_eastern(cspcf, inputs_case, by_year=False)
    
    # Disaggregate load data here if running at county resolution
    if agglevel == 'county':
        print('Disaggregating load data')
        #Read fractional weights for population-based disaggregation
        fracdata = pd.read_csv(
            os.path.join(inputs_case,'disagg_population.csv'), 
            dtype={'fracdata':np.float32},
            index_col='FIPS',
        )
        #Sort by counties to maintain sequence
        fracdata.sort_values('FIPS', inplace=True)
        fracdata = fracdata.loc[fracdata.PCA_REG.isin(val_r_all)].copy()
        # Create timeseries of county load fraction * BA hourly profile
        load_eastern = pd.concat(
            {fips: row.fracdata * load_eastern[row.PCA_REG]
             for fips, row in fracdata.iterrows()},
            axis=1,
        )
        # Filter by regions again for cases when only a subset of a model balancing area is represented
        load_eastern = load_eastern.loc[:,load_eastern.columns.isin(val_r_all)].copy()

    #%% Calculate coincident peak demand at different levels for convenience later
    _hierarchy = hierarchy if sw['GSw_RegionResolution'] == 'county' else hierarchy_original
    _peakload = {}
    for _level in _hierarchy.columns:
        _peakload[_level] = (
            ## Aggregate to level
            load_eastern.rename(columns=_hierarchy[_level])
            .groupby(axis=1, level=0).sum()
            ## Calculate peak
            .groupby(axis=0, level='year').max()
            .T
        )
    ## Also do it at r level
    _peakload['r'] = load_eastern.groupby(axis=0, level='year').max().T
    peakload = pd.concat(_peakload, names=['level','region']).round(3)


    #%%###########################
    #    -- Data Write-Out --    #
    ##############################

    load_eastern.astype(np.float32).to_hdf(
        os.path.join(inputs_case,'load.h5'), key='data', complevel=4, index=True)
    recf_eastern.astype(np.float16).to_hdf(
        os.path.join(inputs_case,'recf.h5'), key='data', complevel=4, index=True)
    resources.to_csv(os.path.join(inputs_case,'resources.csv'), index=False)
    peakload.to_csv(os.path.join(inputs_case,'peakload.csv'))
    ### Write peak demand by NERC region to use in firm net import constraint
    peakload.loc['nercr'].stack('year').rename_axis(['*nercr','t']).rename('MW').to_csv(
        os.path.join(inputs_case,'peakload_nercr.csv'))
    ### Write the CSP solar field CF (no SM or storage) for hourly_writetimeseries.py
    (cspcf_eastern
        .rename(columns=dict(zip(cspcf_eastern.columns, [f'csp_{i}' for i in cspcf_eastern.columns])))
        .astype(np.float32)
        .reset_index(drop=True)
    ).to_hdf(
        os.path.join(inputs_case,'csp.h5'), key='data', complevel=4, index=False)
    ### Overwrite the original hierarchy.csv based on capcredit_hierarchy_level
    hierarchy.rename_axis('*r').to_csv(
        os.path.join(inputs_case, 'hierarchy.csv'), index=True, header=True)
    pd.Series(hierarchy.ccreg.unique()).to_csv(
        os.path.join(inputs_case,'ccreg.csv'), index=False, header=False)


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__ == '__main__':
    # Time the operation of this script
    from ticker import toc, makelog
    import datetime
    tic = datetime.datetime.now()

    ### Parse arguments
    parser = argparse.ArgumentParser(description='Create run-specific pickle files for capacity value')
    parser.add_argument('reeds_path', type=str, help='Base directory for all batch runs')
    parser.add_argument('inputs_case', help='path to inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = makelog(scriptname=__file__, logpath=os.path.join(inputs_case,'..','gamslog.txt'))

    #%% Run it
    main(reeds_path=reeds_path, inputs_case=inputs_case)

    toc(tic=tic, year=0, process='input_processing/ldc_prep.py',
        path=os.path.join(inputs_case,'..'))
    
    print('Finished ldc_prep.py')
