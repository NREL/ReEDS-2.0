#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================
import os
import sys
import datetime
import numpy as np
import pandas as pd
import argparse
import shutil
import subprocess
import yaml
import re
# Local Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


#%% ===========================================================================
### --- General Read Functions---
### ===========================================================================
def is_active_switch(switch_value, active_switch_value):
    # In 'active_switch_value', '~' represents a "NOT" criterion
    # and '|' represents an "OR" set of criteria.
    # '~' applies first in order of operations: '~A|B' means (not A) or B.
    # Entries can use regex after processing '~' and '|' (but don't use '|' as
    # part of regex; '|' is processed before the regex check)
    tests = [
        (not re.match(switch_value, rule.lstrip('~'))) if rule.startswith('~')
        else re.match(switch_value, rule)
        for rule in active_switch_value.split('|')
    ]
    return any(tests)

def is_required_file(runfiles_row, sw):
    if runfiles_row['depends_on_switch'] == 'ignore':
        return False
    elif not runfiles_row['depends_on_switch']:
        return True
    else:
        # In 'linked_switch', '|' represents an "OR" set of switches (file
        # is required if any switches are active) and ',' represents an
        # "AND" set (file is required if all switches are active)
        linked_switch = runfiles_row['depends_on_switch']
        active_switch_value = runfiles_row['depends_on_switch_value']
        if '|' in linked_switch:
            linked_switches = linked_switch.split('|')
            file_required = any([
                is_active_switch(sw[switch], active_switch_value)
                for switch in linked_switches
            ])
        elif ',' in linked_switch:
            linked_switches = linked_switch.split(',')
            file_required = all([
                is_active_switch(sw[switch], active_switch_value)
                for switch in linked_switches
            ])
        else:
            file_required = is_active_switch(sw[linked_switch], active_switch_value)

        return file_required


def read_runfiles(reeds_path, inputs_case, sw, agglevel_variables):
    """
    Read runfiles.csv and return the runfiles dataframe
    Identify files that have a region index versus those that do not.
    """
    runfiles = (
        pd.read_csv(
            os.path.join(reeds_path, 'runfiles.csv'),
            dtype={'fix_cols':str,
                   'depends_on_switch':str,
                   'depends_on_switch_value': str},
            comment='#',
        ).fillna({'fix_cols':'',
                  'depends_on_switch':'',
                  'depends_on_switch_value':''})
    )

    # Temp hard coded fix for reading supply curve files with reinforcement costs included
    if sw['GSw_NoReinforcement']=='none' :
        sw['GSw_NoReinforcement'] = ''

    runfiles['file_is_required'] = runfiles.apply(
        axis=1,
        func=is_required_file,
        args=(sw,),
    )

    # If a filepath isn't specified, that means it is already in the
    # inputs_case folder, otherwise use the filepath
    # We leave the 'lvl' portion of 'full_filepath' unformatted because
    # we may need to read multiple 'lvl' variants of the file at once later
    runfiles['full_filepath'] = runfiles.apply(
        axis=1,
        func=lambda row: os.path.join(inputs_case, row['filename'])
        if pd.isna(row['filepath'])
        else os.path.join(reeds_path, row['filepath'].format(**{**sw, **{'lvl': '{lvl}'}}))
    )

    # Create a copy of runfiles that specifies the 'lvl' that applies to each file
    # (only used to determine missing files, the original runfiles is used later).
    # In general, the 'lvl' corresponds to GSw_RegionResolution.
    # For mixed resolution, each 'lvl'-indexed file is split into two rows -
    # one for the BA-level file and the other for the county-level file.
    runfiles_with_lvls = runfiles.assign(lvl='')
    lvl_indexed_file_mask = (
        (runfiles_with_lvls.filepath.notna())
        & (runfiles_with_lvls.filepath.str.contains('{lvl}'))
    )
    if agglevel_variables['lvl'] == 'mult':
        runfiles_with_lvls.loc[lvl_indexed_file_mask, 'lvl'] = 'ba,county'
        runfiles_with_lvls['lvl'] = runfiles_with_lvls['lvl'].str.split(',')
        runfiles_with_lvls = runfiles_with_lvls.explode('lvl')
    else:
        runfiles_with_lvls.loc[lvl_indexed_file_mask, 'lvl'] = agglevel_variables['lvl']
    
    # Determine existence of each file
    runfiles_with_lvls['full_filepath'] = runfiles_with_lvls.apply(
        axis=1,
        func=lambda x: x['full_filepath'].format(**{'lvl': x['lvl']})
    )
    runfiles_with_lvls['file_exists'] = (
        runfiles_with_lvls['full_filepath'].apply(lambda x: os.path.exists(x))
    )

    # Raise an error if any of the required files with specified filepaths are missing
    missing_required_files = list(
        runfiles_with_lvls.loc[(
            runfiles_with_lvls['file_is_required']
            & ~runfiles_with_lvls['file_exists']
            & ~runfiles_with_lvls['filepath'].isna()
        )]['filepath']
    )
    if len(missing_required_files) > 0:
        raise FileNotFoundError(
            'The following required files are missing. Add them '
            'to the inputs directory or update runfiles.csv to specify optionality:\n{}\n'
            .format('\n'.join(missing_required_files))
        )

    # Non-region files that need copied either do not have an entry in region_col
    # or have 'ignore' as the entry. They also have a filepath specified.
    non_region_files = (
        runfiles[
            ((runfiles['region_col'].isna()) | (runfiles['region_col'] == 'ignore'))
            & (~runfiles['filepath'].isna())]
        )

    # Region files are those that have a region and do not specify 'ignore'
    # Also ignore files that are created after this script runs (i.e., post_copy = 1)
    region_files = (
        runfiles[
            (~runfiles['region_col'].isna())
            & (runfiles['region_col'] != 'ignore')
            & (runfiles['post_copy'] != 1)]
        )

    return runfiles, non_region_files, region_files


def get_source_deflator_map(reeds_path):
    """
    Get the deflator for each input file
    """
    # Inflation-adjusted inputs
    sources_dollaryear = pd.read_csv(
        os.path.join(reeds_path,'sources.csv'),
        usecols=["RelativeFilePath", "DollarYear"]
    )
    deflator = pd.read_csv(
        os.path.join(reeds_path,'inputs','financials','deflator.csv'),
        header=0, names=['Dollar.Year','Deflator'], index_col='Dollar.Year').squeeze(1)
    # Create a mapping between inputs' relative filepaths and their deflation
    # multipliers based on the dollar years their monetary values are in
    sources_dollaryear = (
        # Filter out rows that don't contain a valid dollar year
        sources_dollaryear[pd.to_numeric(sources_dollaryear['DollarYear'], errors='coerce').notnull()]
        # Note: We must remove the backslash that prepends each relative filepath
        # for compatibility with the 'os' package (otherwise it is treated as an absolute path)
        .assign(RelativeFilePath=sources_dollaryear["RelativeFilePath"].str[1:])
        .astype({"DollarYear": "int64"})
        .rename(columns={"DollarYear": "Dollar.Year"})
        .merge(deflator,on="Dollar.Year",how="left")
    )

    source_deflator_map = dict(zip(sources_dollaryear["RelativeFilePath"], sources_dollaryear["Deflator"]))

    return source_deflator_map


def get_regions_and_agglevel(
    reeds_path,
    inputs_case,
    save_regions_and_agglevel=True,
    NARIS=False
):
    """
    Create a regional mapping to help filter for specific regions and aggregation levels.
    This function reads various input files, processes them to create mappings of regions
    at different levels of aggregation, and writes these mappings to csv files.

    If save_regions_and_agglevel is False do not save intermediate files
    (You just want the mapping)
    """
    sw = reeds.io.get_switches(inputs_case)

    # Load the full regions list
    hierarchy = pd.read_csv(
        os.path.join(reeds_path, 'inputs', 'hierarchy{}.csv'.format(
            '' if (sw['GSw_HierarchyFile'] == 'default')
            else '_'+sw['GSw_HierarchyFile']))
    )

    # Save the original hierarchy file: used in ldc_prep.py and hourly_*.py scripts
    if save_regions_and_agglevel:
        hierarchy.to_csv(
            os.path.join(inputs_case,'hierarchy_original.csv'),
            index=False, header=True
            )

    if not NARIS:
        hierarchy = hierarchy.loc[hierarchy.country.str.lower()=='usa'].copy()

    # Add a row for each county
    county2zone = pd.read_csv(
        os.path.join(reeds_path, 'inputs', 'county2zone.csv'), dtype={'FIPS':str},
    )
    county2zone['county'] = 'p' + county2zone.FIPS
    # Add county info to hierarchy
    hierarchy = hierarchy.merge(county2zone.drop(columns=['FIPS','state']), on='ba')

    # Subset hierarchy for the region of interest (based on the GSw_Region switch)
    # Parse the GSw_Region switch. If it includes a '/' character, it has the format
    # {column of hierarchy.csv}/{period-delimited entries to keep from that column}.
    if '/' in sw['GSw_Region']:
        GSw_RegionLevel, GSw_Region = sw['GSw_Region'].split('/')
        GSw_Region = GSw_Region.split('.')
        if len(GSw_Region) == 1:
            hier_sub = hierarchy[hierarchy[GSw_RegionLevel] == GSw_Region[0]].copy()
        else:
            for idx in range(0,len(GSw_Region)):
                if idx == 0:
                    hier_sub = hierarchy[hierarchy[GSw_RegionLevel] == GSw_Region[idx]].copy()
                else:
                    hier_sub = pd.concat([
                        hier_sub,
                        hierarchy[hierarchy[GSw_RegionLevel] == GSw_Region[idx]]
                    ])
    # Otherwise use the modeled_regions.csv file to define the regions
    else:
        modeled_regions = pd.read_csv(
            os.path.join(reeds_path,'inputs','userinput','modeled_regions.csv'))
        modeled_regions.columns = modeled_regions.columns.str.lower()
        val_r_in = list(
            modeled_regions[~modeled_regions[sw['GSw_Region'].lower()].isna()]['r'].unique())
        hier_sub = hierarchy[hierarchy['ba'].isin(val_r_in)].copy()


    # Read region resolution switch to determine agglevel
    agglevel = sw['GSw_RegionResolution'].lower()

    # Check if desired spatial resolution is mixed
    if agglevel == 'mixed':

        #Set value in resolution column of hier_sub to match value assigned in modeled_regions.csv
        region_def = pd.read_csv(
            os.path.join(reeds_path,'inputs','userinput','modeled_regions.csv'))
        region_def =  region_def[['r', sw['GSw_Region']]]

        res_map = region_def.set_index('r')[sw['GSw_Region']].to_dict()
        hier_sub['resolution'] = hier_sub['ba'].map(res_map)

    else:
        hier_sub['resolution'] = agglevel


    # Write out all unique aggregation levels present in the hierarchy resolution column
    agglevels = hier_sub['resolution'].unique()

    # Write agglevel
    if save_regions_and_agglevel:
        pd.DataFrame(agglevels, columns=['agglevels']).to_csv(
            os.path.join(inputs_case, 'agglevels.csv'), index=False)


    # Create an r column at the front of the dataframe and populate it with the
    # county-level regions (overwritten if needed)
    hier_sub.insert(0,'r',hier_sub['county'])

    # Overwrite the regions with the ba, state, or aggreg values as specififed
    for level in ['ba','aggreg']:
        hier_sub['r'][hier_sub['resolution'] == level] = (
            hier_sub[level][hier_sub['resolution'] == level])

    # Write out mappings of r and ba to all counties
    r_county = hier_sub[['r','county']]
    ba_county = hier_sub[['ba','county']]

    if save_regions_and_agglevel:
        hier_sub[['r','county']].to_csv(
            os.path.join(inputs_case, 'r_county.csv'), index=False)

        # Write out a mapping of r to ba regions
        hier_sub[['r','ba']].drop_duplicates().to_csv(
            os.path.join(inputs_case, 'r_ba.csv'), index=False)
        # Write out mapping of r to census divisions
        hier_sub[['r','cendiv']].drop_duplicates().to_csv(
            os.path.join(inputs_case, 'r_cendiv.csv'), index=False)

        # Write out mapping of rb to aggreg (for writesupplycurves.py)
        hier_sub[['ba','aggreg']].drop_duplicates().to_csv(
            os.path.join(inputs_case, 'rb_aggreg.csv'), index=False)

        # Write out val_county and val_ba before collapsing to unique regions
        hier_sub['county'].to_csv(
            os.path.join(inputs_case, 'val_county.csv'), header=False, index=False)
        hier_sub['ba'].drop_duplicates().to_csv(
            os.path.join(inputs_case, 'val_ba.csv'), header=False, index=False)

    # Find all the unique elements that might define a region
    val_r_all = []
    for column in hier_sub.columns:
        val_r_all.extend(hier_sub[column].unique().tolist())

    # Converting to a set ensures that only unique values are kept
    val_r_all = sorted(list(set(val_r_all)))

    if save_regions_and_agglevel:
        pd.Series(val_r_all).to_csv(
            os.path.join(inputs_case, 'val_r_all.csv'), header=False, index=False)

    # Rename columns and save as hierarchy_with_res.csv for use in agglevel_variables function
    hier_sub.rename(columns={'r':'*r'}).to_csv(
        os.path.join(inputs_case, 'hierarchy_with_res.csv'), index=False)

    # Drop county name and resolution columns
    hier_sub = hier_sub.drop(['county_name','resolution'],axis=1)


    # Collapse to only unique regions
    hier_sub = hier_sub.drop_duplicates(subset=['r'])

    # Sort hier_sub by r so that "ord(r)" commands in GAMS result in the properly
    # ordered outputs
    hier_sub['numeric_value'] = hier_sub['r'].str.extract('(\d+)').astype(float)
    hier_sub = hier_sub.sort_values(by='numeric_value').drop('numeric_value', axis=1)

    # Drop any substate region columns as these will no longer be needed
    hier_sub = hier_sub.drop(['county','ba','st_interconnect'],axis=1)

    # Populate val_st as unique states (not st_int) from the subsetted hierarchy table
    # Also include "voluntary" state for modeling voluntary market REC trading
    val_st = list(hier_sub['st'].unique()) + ['voluntary']

    # Write out the unique values of each column in hier_sub to val_[column name].csv
    # Note the conversion to a pd Series is necessary to leverage the to_csv function
    if save_regions_and_agglevel:
        for i in hier_sub.columns:
            pd.Series(hier_sub[i].unique()).to_csv(
                os.path.join(inputs_case,'val_' + i + '.csv'),index=False,header=False)

        # Overwrite val_st with the val_st used here (which includes 'voluntary')
        pd.Series(val_st).to_csv(
            os.path.join(inputs_case, 'val_st.csv'), header=False, index=False)

        # Rename columns and save as hierarchy.csv
        hier_sub.rename(columns={'r':'*r'}).drop(columns='aggreg').to_csv(
            os.path.join(inputs_case, 'hierarchy.csv'), index=False)

    levels = list(hier_sub.columns)
    valid_regions = {level: list(hier_sub[level].unique()) for level in levels}

    val_r = valid_regions['r']

    # Export region files
    if save_regions_and_agglevel:
        pd.Series(val_r).to_csv(
            os.path.join(inputs_case, 'val_r.csv'), header=False, index=False)

    # Create list of CS regions that are included in modeled regions
    r_cs = pd.read_csv(os.path.join(reeds_path, 'inputs', 'ctus', 'r_cs.csv'))
    r_cs = r_cs[r_cs['*r'].isin(val_r_all)]

    # Export valid cs files to val_cs.csv
    val_cs = pd.Series(r_cs['cs'].unique())

    if save_regions_and_agglevel:
        val_cs.to_csv(os.path.join(inputs_case, 'val_cs.csv'), header=False, index=False)
        # Export filtered r_cs to r_cs.csv
        r_cs.to_csv(os.path.join(inputs_case, 'r_cs.csv'), index=False)
        r_cs = r_cs.rename(columns = {'*r':'r'})
    regions_and_agglevel = {"valid_regions": valid_regions,
                            "val_r_all": val_r_all,
                            "val_st": val_st,
                            "val_cs": val_cs,
                            "r_county": r_county,
                            "ba_county": ba_county,
                            "levels": levels,
                            "r_cs":r_cs}

    return regions_and_agglevel


def read_banned_tech_file(full_path, filepath, inputs_case, r_county):
    """
    Parses the list of regionally (state/county-level) banned techs from the
    provided YAML file and reformats it as a GAMS-compatible table.
    Regions banning nuclear are exported as their own list, as nuclear bans
    have their own switches and functionalities that are handled separately.
    """
    if not (full_path.endswith('yaml') or full_path.endswith('yml')):
        raise TypeError(f'filetype for {full_path} is not .yaml/.yml')

    with open(full_path) as f:
        techs_banned = yaml.safe_load(f)

    hierarchy = pd.read_csv(os.path.join(inputs_case, 'hierarchy.csv'))
    df = pd.DataFrame(data=0, columns=hierarchy['*r'], index=techs_banned.keys())

    # Nuclear bans are handled specially in the model,
    # so we create a separate dataframe for those regions.
    nuclear_ban_regions = pd.DataFrame(data=[], columns=['*r'])
    for tech, ban_lists in techs_banned.items():
        ban_regions = []

        if not all([x in ['st', 'county'] for x in ban_lists.keys()]):
            raise NotImplementedError(
                "The regional scope of banned techs must be either 'st' or 'county'. "
                f"Update the nested keys in {filepath}."
            )

        # Apply state-wide bans to all of the regions belonging to those states
        if 'st' in ban_lists.keys():
            ban_states = ban_lists['st']
            state_ban_regions = list(hierarchy.loc[hierarchy.st.isin(ban_states)]['*r'])
            ban_regions.extend(state_ban_regions)

        # Apply county-wide bans to regions where all of the counties have banned the tech
        if 'county' in ban_lists.keys():
            ban_counties = ['p' + str(fips).zfill(5) for fips in ban_lists['county']]
            r_ban_counties_map = (
                r_county.loc[r_county.county.isin(ban_counties)]
                .groupby('r')
                ['county']
                .apply(list)
                .apply(sorted)
            )
            r_all_counties_map = (
                r_county.groupby('r')
                ['county']
                .apply(list)
                .apply(sorted)
            )
            county_ban_regions = list(
                r_ban_counties_map
                .loc[(r_ban_counties_map.isin(r_all_counties_map))]
                .index
            )
            ban_regions.extend(county_ban_regions)

        if tech == 'nuclear':
            nuclear_ban_regions['*r'] = ban_regions
        else:
            df.loc[tech, ban_regions] = 1
        
    df = df.reset_index(names=['i'])

    return df, nuclear_ban_regions


def subset_to_valid_regions(
    sw,
    region_file_entry,
    agglevel_variables,
    regions_and_agglevel,
    inputs_case=None
):
    """
    Filter data for valid regions and return a dataframe
    """
    levels = regions_and_agglevel["levels"]
    val_r_all = regions_and_agglevel["val_r_all"]
    val_st = regions_and_agglevel["val_st"]
    val_cs = regions_and_agglevel["val_cs"]
    valid_regions = regions_and_agglevel["valid_regions"]
    r_cs = regions_and_agglevel["r_cs"]

    # Read file and return dataframe filtered for valid regions
    filepath = region_file_entry['filepath']
    filename = region_file_entry['filename']
    full_path = region_file_entry['full_filepath']

    # Get the filetype of the input file from the filepath string
    filetype_in = os.path.splitext(filepath)[1].strip('.')

    region_col = region_file_entry['region_col']
    fix_cols = region_file_entry['fix_cols'].split(',')

    # When running at mixed resolution we need to copy both ba and county resolution data
    if (agglevel_variables['lvl'] == 'mult') and ('lvl' in filepath):
        #Read in BA and county resolution data
        full_path_ba = full_path.replace('{lvl}', 'ba')
        full_path_county = full_path.replace('{lvl}', 'county')
        match filetype_in:
            case 'h5':
                df_ba = reeds.io.read_file(full_path_ba)
                df_county = reeds.io.read_file(full_path_county)
            case 'csv':
                df_ba = pd.read_csv(
                    full_path_ba,
                    dtype={'FIPS':str, 'fips':str, 'cnty_fips':str}
                )
                df_county = pd.read_csv(
                    full_path_county,
                    dtype={'FIPS':str, 'fips':str, 'cnty_fips':str}
                )
            case _:
                raise TypeError(f'filetype for {full_path} is not .csv or .h5')

        match filename:        
            case 'recf_csp.h5':
                # Change index for csp BA data
                df_ba.index = [
                    s.decode('utf-8').replace(' ','T').encode('utf-8')
                    for s in df_ba.index[:]
                ]
                df_ba.index.name = 'datetime'
            case 'recf_distpv.h5':
                # Change columns for distpv county data
                # Remove 'distpv' from column name and add back in ldc_prep.py
                # This matches the format for the other resource h5 files
                df_county.columns = df_county.columns.str.replace('distpv|','')
            case _:
                pass

    # Single resolution procedure
    else:
        # Replace '{switchnames}' in full_path with corresponding switch values
        full_path = full_path.format(**{**sw, **{'lvl':agglevel_variables['lvl']}})

        if filetype_in == 'h5':
            df = reeds.io.read_file(full_path)
            if filename == 'recf_distpv.h5':
                df.columns = df.columns.str.replace('distpv|','')

        elif filetype_in == 'csv':
            df = pd.read_csv(full_path, dtype={'FIPS':str, 'fips':str, 'cnty_fips':str})

        elif filename == 'techs_banned.csv':
            df, nuclear_ban_regions = read_banned_tech_file(
                full_path,
                filepath,
                inputs_case,
                r_county=regions_and_agglevel['r_county']
            )
            nuclear_ban_regions.to_csv(
                os.path.join(inputs_case,'nuclear_ba_ban_list.csv'),
                index=False
            )

        else:
            raise TypeError(f'filetype for {full_path} is not .csv or .h5')

    # ---- Filter data to valid regions ----

    # If running at mixed resolution we need to remove BA level data for regions that are being solved at county resolution
    if (agglevel_variables['lvl'] == 'mult') and ('lvl' in filepath):
        hier = pd.read_csv(os.path.join(inputs_case,'hierarchy_with_res.csv')).rename(columns = {'*r':'r'})
        # Filter function parameters to only include BA resolution regions
        val_cs_ba = r_cs[r_cs['r'].isin(agglevel_variables['ba_regions'])]['cs']
        valid_regions_ba = {level: list(hier[hier['r']
                                .isin(agglevel_variables['ba_regions'])][level].unique()) for level in levels}
        val_st_ba = valid_regions_ba['st']
        val_r_all_ba = []
        for value in valid_regions_ba.values():
            val_r_all_ba.extend(value)
        val_r_all_ba = list(set(val_r_all_ba))
        # Add BA regions associated with states and aggregs being run at BA resolution
        val_r_all_ba.extend(x for x in agglevel_variables['ba_regions']if x not in val_r_all_ba)

        df_ba = filter_data(df_ba,region_col, fix_cols,levels, val_r_all = val_r_all_ba,valid_regions = valid_regions_ba,
                            val_st = val_st_ba,val_cs = val_cs_ba, filename = filename)


        # Transmission files need to be filtered differently to allow interfaces between BA and county resolution regions
        transmission_files = ['transmission_capacity_init_AC_r.csv','transmission_capacity_init_nonAC.csv',
                      'transmission_distance_cost_500kVac.csv','transmission_distance_cost_500kVdc.csv',
                      'r_rr_adj.csv']

        if filename in transmission_files:
            # Filter county data to include regions being solved at both BA and county resolution
            df_county = filter_data(df_county,region_col, fix_cols,levels, val_r_all ,
                                    valid_regions ,val_st,val_cs, filename = filename)
            # Assign the counties that are not being solved at county resolution to the correct BA
            tx_region_col = '*r' if '*r' in df_county.columns.values else 'r'
            for idx, region in df_county[tx_region_col].items():
                if region not in agglevel_variables['county_regions']:
                    df_county.loc[idx, tx_region_col] = agglevel_variables['BA_2_county'][df_county.loc[idx,tx_region_col]]
                
            for idx,region in df_county['rr'].items():
                if region not in agglevel_variables['county_regions']:
                    df_county.loc[idx, 'rr'] = agglevel_variables['BA_2_county'][df_county.loc[idx, 'rr']]
            # Drop if *r and rr are same region
            df_county = df_county.drop(df_county[df_county[tx_region_col]==df_county['rr']].index)
            # Drop if line is BA-to-BA
            drop_list = []
            for idx,region in df_county.iterrows():
                if (
                    (region[tx_region_col] in agglevel_variables['ba_regions'])
                    and (region['rr'] in agglevel_variables['ba_regions'])
                ):
                    drop_list.append(idx)
                            
            df_county = df_county.drop(drop_list)
            # Group lines going between same BA and county
            if 'distance' in filename:
                df_county = df_county.groupby([tx_region_col,'rr']).mean().reset_index()
            else:
                df_county = df_county.groupby([tx_region_col,'rr']).sum().reset_index()
            if filename != 'r_rr_adj.csv':
                df_county['interface'] = df_county[tx_region_col] + '||'+df_county['rr']
            df_county.reset_index(drop=True,inplace=True)

        else:
            # Filter function parameters to only include county resolution regions
            val_cs_county = r_cs[r_cs['r'].isin(agglevel_variables['county_regions2ba'])]['cs']
            valid_regions_county = {level: (hier[hier['r']
                                    .isin(agglevel_variables['county_regions'])][level].unique()) for level in levels}
            val_st_county = valid_regions_county['st']
            val_r_all_county = []
            for value in valid_regions_county.values():
                val_r_all_county.extend(value)
            val_r_all_county = list(dict.fromkeys(val_r_all_county))

            df_county = filter_data(df_county,region_col, fix_cols,levels, val_r_all = val_r_all_county,
                                    valid_regions = valid_regions_county,val_st = val_st_county,val_cs = val_cs_county,
                                    filename = filename)

         # Combine BA and county data

        # The filter data function returns a dataframe with NAN values to prevent empty H5 files
        # If either the BA data or county data are populated we can drop the nan data
        if df_county.isna().all().all() and not df_ba.isna().all().all():
            df = df_ba
        elif not df_county.isna().all().all() and df_ba.isna().all().all():
            df = df_county
        else:
            # Combine BA and county data
            if region_file_entry['wide'] == 1 :
                df = pd.concat([df_ba,df_county],axis =1)
            else:
                df = pd.concat([df_ba,df_county])

    # Single resolution procedure
    # Or procedure for input data that exist at single resolution and
    # are aggregated/disaggregated later
    else:
        df = filter_data(
            df,region_col, fix_cols,levels, val_r_all ,
            valid_regions ,val_st, val_cs, filename=filename,
        )

    return df


#%% ===========================================================================
### --- General Write Functions---
### ===========================================================================
def scalar_csv_to_txt(path_to_scalar_csv):
    """
    Write a scalar csv to GAMS-readable text
    Format of csv should be: scalar,value,comment
    """
    # Load the csv
    dfscalar = pd.read_csv(
        path_to_scalar_csv,
        header=None, names=['scalar','value','comment'], index_col='scalar').fillna(' ')
    # Create the GAMS-readable string (comments can only be 255 characters long)
    scalartext = '\n'.join([
        'scalar {:<30} "{:<5.255}" /{}/ ;'.format(
            i, row['comment'], row['value'])
        for i, row in dfscalar.iterrows()
    ])
    # Write it to a file, replacing .csv with .txt in the filename
    with open(path_to_scalar_csv.replace('.csv','.txt'), 'w') as w:
        w.write(scalartext)

    return dfscalar


def param_csv_to_txt(path_to_param_csv, writelist=True):
    """
    Write a parameter csv to GAMS-readable text
    Format of csv should be: parameter(indices),units,comment
    """
    # Load the csv
    dfparams = pd.read_csv(
        path_to_param_csv,
        index_col='param', comment='#',
    )
    # Create the GAMS-readable param definition string (comments must be ≤255 characters)
    paramtext = '\n'.join([
        f'parameter {i:<50} "--{row.units}-- {row.comment:.255}" ;'
        # Don't define parameters with an input flag because they already exist
        for i, row in dfparams.loc[dfparams.input != 1].iterrows()
    ])
    # Write it to a file, replacing .csv with .gms in the filename
    param_gms_path = path_to_param_csv.replace('.csv','.gms')
    with open(param_gms_path, 'w') as w:
        w.write(paramtext)
    # Write the list of parameters if desired
    if writelist:
        # Create the GAMS-readable list of parameters (without indices)
        paramlist = '\n'.join(dfparams.index.map(lambda x: x.split('(')[0]).tolist())
        param_list_path = (
            path_to_param_csv.replace('params','paramlist').replace('.csv','.txt'))
        with open(param_list_path, 'w') as w:
            w.write(paramlist)

    return dfparams

# Function to filter data to valid regions
def filter_data(
    df,
    region_col,
    fix_cols,
    levels,
    val_r_all,
    valid_regions,
    val_st,
    val_cs,
    filename
):
    if region_col == 'wide':
        # Check to see if the regions are listed in the columns. If they are,
        # then use those columns
        if df.columns.isin(val_r_all).any():
            df = df.loc[:,df.columns.isin(fix_cols + val_r_all)]
        else:
            # Checks if regions are in columns as '[class]|[region]' or '[class]_[region]' (e.g. in 8760 RECF data).
            # This 'try' attempts to split each column name using '|' and '_' as delimiters and checks the second
            # value for any regions.
            # If it can't do so, it will instead use a blank dataframe.
            try:
                if '|' in df.columns[0]:
                    delim = '|'
                elif '_' in df.columns[0]:
                    delim = '_'
                else:
                    raise ValueError(f"Cannot split columns in {filename} by '|' or '_' (example: {df.columns[0]}).")
                column_mask = (df.columns.str.split(delim,expand=True)
                                .get_level_values(1)
                                .isin(val_r_all)
                                .tolist()
                )
                df = df.loc[:,column_mask]
                # Empty h5 files cannot be read in, causing errors in ldc_prep.py.
                # In the case that val_r_all filters out all columns, leaving an empty dataframe,
                # fill a single column with NaN to preserve the file index for use in ldc_prep
                if len(df.columns) == 0:
                    df = pd.DataFrame(np.nan, index = df.index,columns = val_r_all)
            except Exception:
                df = pd.DataFrame()

    # If there is a region-to-region mapping set
    elif region_col.strip('*') in ['r,rr','transgrp,transgrpp']:
        # make sure both the r and rr regions are in val_r
        r,rr = region_col.split(',')
        df = df.loc[df[r].isin(val_r_all) & df[rr].isin(val_r_all)]

    # Subset on the valid regions except for r regions
    # (r regions might also include s regions, which complicates things...)
    elif ((region_col.strip('*') in levels) & (region_col.strip('*') != 'r')):
        df = df.loc[df[region_col].isin(valid_regions[region_col.strip('*')])]

    elif (region_col == 'cs' or region_col == '*cs'):
        # subset to just cs regions
        df = df.loc[df[region_col].isin(val_cs)]

    # Subset both column of 'st' and columns of state if st_st
    elif (region_col.strip('*') == 'st_st'):
        # make sure both the state regions are in val_st
        df = df.loc[df['st'].isin(val_st)]
        df = df.loc[:,df.columns.isin(fix_cols + val_st)]

    elif (region_col.strip('*') == 'r_cendiv'):
        # Make sure both the r is in val_r_all and cendiv is in val_cendiv
        val_cendiv = valid_regions['cendiv']
        df = df.loc[df['r'].isin(val_r_all)]
        df = df.loc[:,df.columns.isin(["r"] + val_cendiv)]

    # Subset on val_{level} if region_col == 'wide_{level}'
    elif (region_col.split('_')[0] == 'wide') and (region_col.split('_')[1] in valid_regions.keys()):
        # Check to see if the region values are listed in the columns. If they are,
        # then use those columns
        val_reg = valid_regions[region_col.split('_')[1]]
        if df.columns.isin(val_reg).any():
            df = df.loc[:,df.columns.isin(fix_cols + val_reg)]
        # Otherwise just use an empty dataframe
        else:
            df = pd.DataFrame()

    # If region_col is not wide, st, or aliased..
    else:
        df = df.loc[df[region_col].isin(val_r_all)]

    return df


def write_scalars(scalars, inputs_case):
    """
    Write modified scalars.csv file
    Special-case handling of scalars.csv: turn years_until into firstyear
    """
    toadd = scalars.loc[scalars.index.str.startswith('years_until')].copy()
    toadd.index = toadd.index.map(lambda x: x.replace('years_until','firstyear'))
    toadd.value += scalars.loc['this_year','value']
    scalars_write = pd.concat([scalars, toadd], axis=0)

    # Trim trailing decimal zeros
    scalars_write.value = scalars_write.value.astype(str).replace('\.0+$', '', regex=True)
    scalars_write.to_csv(os.path.join(inputs_case, 'scalars.csv'), header=False)

    # Rewrite the scalar tables as GAMS-readable definition
    scalar_csv_to_txt(os.path.join(inputs_case,'scalars.csv'))


def write_GAMS_sets(runfiles, reeds_path, inputs_case):
    """
    Write GAMS-readable sets to the inputs_case directory
    """
    casedir = os.path.dirname(inputs_case)

    # Create Sets folder
    shutil.copytree(
        os.path.join(reeds_path,'inputs','sets'),
        os.path.join(inputs_case,'sets'),
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns('README*','readme*'),
    )

    # Write commands to load sets
    sets = runfiles.loc[runfiles.GAMStype=='set'].copy()
    settext = '$offlisting\n' + '\n\n'.join([
        f"set {row.GAMSname} '{row.comment:.255}'"
        '\n/'
        f"\n$include inputs_case%ds%{row.filename}"
        '\n/ ;'
        for i, row in sets.iterrows()
    ]) + '\n$onlisting\n'
    # Write to file
    with open(os.path.join(casedir,'b_sets.gms'), 'w') as f:
        f.write(settext)


def write_non_region_file(filename, src_file, dir_dst, sw, regions_and_agglevel):
    """
    Copy a non-region specific file (filename) from src_file to dir_dst
    """
    # Check if source file exists and is not rev_paths.csv
    if (os.path.exists(src_file)) and (filename!='rev_paths.csv'):

        # Special Case: Values in load_multiplier.csv need to be rounded prior to copy
        if filename == 'load_multiplier.csv':
            df_load_multiplier = pd.read_csv(src_file).round(6)
            df_load_multiplier.to_csv(os.path.join(dir_dst,'load_multiplier.csv'),index=False)

        elif filename == 'h2_exogenous_demand.csv':
            # h2_exogenous_demand.csv has a path in runfiles.csv (considered a non-region file)
            df=pd.read_csv(src_file,index_col=['p','t'])
            df[sw['GSw_H2_Demand_Case']].round(3).rename_axis(['*p','t']).to_csv(
                os.path.join(dir_dst,'h2_exogenous_demand.csv')
            )

        elif filename == 'energy_communities.csv':
            # Map energy communities to regions and compute the percentage of energy communities
            # within each region to assign a weighted bonus.

            # Rename column in energy_communities.csv and map county to r, save as energy_communities.csv
            energy_communities = pd.read_csv(src_file)
            energy_communities.rename(columns={'County Region': 'county'}, inplace=True)

            r_county = regions_and_agglevel ['r_county']
            # Map energy communities to regions
            e_df = pd.merge(energy_communities, r_county, on='county', how='left').dropna()

            # Group energy community regions and count the number of counties in each
            energy_county_counts = e_df.groupby('r')['county'].nunique()

            # Group all regions and count the number of counties in each
            total_county_counts = r_county.groupby('r')['county'].nunique()

            # Calculate the percentage of counties that are energy communities in each region
            e_df = (energy_county_counts / total_county_counts).round(3).reset_index().dropna()

            # Rename columns from ['r','county'] to ['r','percentage_energy_communities']
            e_df.columns = ['r', 'percentage_energy_communities']

            e_df.to_csv(os.path.join(dir_dst,filename),index=False)

        else:
            shutil.copy(src_file, os.path.join(dir_dst,filename))

            if filename == 'e_report_params.csv':
                # Rewrite e_report_params as GAMS-readable definition
                param_csv_to_txt(os.path.join(dir_dst,'e_report_params.csv'))

            if filename == 'scalars.csv':
                # Rewrite scalars.csv as GAMS-readable definition
                scalars = reeds.io.get_scalars(full=True)
                write_scalars(scalars, dir_dst)


def write_non_region_files(non_region_files, sw, inputs_case, regions_and_agglevel):
    """
    Copy non-region specific files to the input case directory.
    """
    print('Copying non-region-indexed files')

    for _, row in non_region_files.iterrows():
        print(f'...copying {row.filename}')

        if row['filepath'].split('/')[0] in ['inputs','postprocessing','tests']:
            dir_dst = inputs_case
        else:
            dir_dst = os.path.dirname(inputs_case)

        filename = row['filename']
        src_file = row['full_filepath']
        write_non_region_file(filename, src_file, dir_dst, sw, regions_and_agglevel)


def write_county_vre_hourly_profiles(inputs_case, reeds_path):
    """
    Copy county-level RE hourly profiles to the ReEDS folder
    """
    # Read the supply curve meta data
    revData = pd.read_csv(os.path.join(inputs_case,'rev_paths.csv'))

    # EGS and GeoHydro supply curves come from hourlize but don't have profiles,
    # so drop those from consideration as well
    revData = revData[revData['tech'] != 'egs']
    revData = revData[revData['tech'] != 'geohydro']

    # Create a dataframe to hold the new file version information
    rev_data_cols = ['tech','access_case']
    file_version_new = pd.DataFrame(columns = rev_data_cols + ['file version'])
    for rdc in rev_data_cols:
        file_version_new[rdc] = revData[rdc]

    # Check to see if there is a file version file for existing county-level
    # profiles, if not, then we'll need to copy over the files. If they are
    # present, then we need to check to see if they are the right version.
    try:
        file_version = pd.read_csv(
            os.path.join(reeds_path,'inputs','variability','multi_year','file_version.csv')
        )
        missing_cols = set(['tech','access_case','file version']) - set(file_version.columns)
        if len(missing_cols) > 0:
            print(
                f"Current file_version.csv is missing {missing_cols}; "
                "will delete and re-copy county-level profiles."
            )
            existing_fv = 0
        else:
            existing_fv = 1
    except FileNotFoundError:
        print(
            f"{os.path.join(reeds_path,'inputs','variability','multi_year','file_version.csv')} "
            "not found; copying county-level profiles from remote"
        )
        existing_fv = 0

    if existing_fv:
        profile_data = pd.merge(revData,file_version,on=['tech','access_case'], how='left')
        # NaN means this profile is missing from the current file version
        profile_data['file version'] = profile_data['file version'].fillna("missing")
        # Check to see if the file version in the repo is already present
        profile_data['present'] = profile_data['sc_path'].apply(
            lambda x: x.split('/')[-1]) == profile_data['file version']
        # Check that entries in the file version have an existing file
        profile_data['present'] = profile_data.apply(
            lambda row: row.present and os.path.exists(
            os.path.join(
                reeds_path,'inputs','variability','multi_year',
                f'{row.tech}-{row.access_case}_county.h5')),
            axis=1)

        # Populate the new file version file with the existing file version
        # information to start
        file_version_new = file_version
    else:
        profile_data = revData
        profile_data['present'] = False

    # If the profile data doesn't exist for the correct version of the supply
    # curve, then copy it over and put the supply curve version in
    # file_version.csv
    present_in_fv = 0
    file_version_updates = 0
    missing_file_versions = []
    for i,row in profile_data.iterrows():
        # If the profile is already present, do nothing
        if row['present'] is True:
            present_in_fv += 1
            continue
        # Otherwise copy the profile over
        else:
            # Check if ReEDS is being run by a non-NREL user. Non-NREL users must
            # download county-level data manually from OpenEI to the ReEDS
            # multi-year input folder. NREL users will auto-magically have the
            # county-level data downloaded from the remote location that coincides
            # with where they are running ReEDS from.
            try:
                remote_data = subprocess.check_output('git remote -v', stderr=subprocess.STDOUT, shell=True)
                remote_url = (remote_data.splitlines()[0].split()[1].decode('utf-8'))
            except Exception:
                # Set remote_url to 'no remote' if ReEDS was downloaded via zip file
                remote_url = 'no remote'
            access_case = row['access_case']
            # If NREL user, then attempt to copy data from the remote location defined in
            # rev_paths.csv.

            # github runner test settings
            # tries to get environment variable from github, if it's not found it defaults to False
            github_test = os.getenv("GITHUB_COUNTY_TEST", False)

            if 'github.nrel.gov' in remote_url:
                sc_path = row['sc_path']
                print(f'Copying county-level hourly profiles for {row["tech"]} {row["access_case"]}')

                if github_test:
                    # this is a county-level test run, get the data from the tests/data folder
                    shutil.copy(
                        os.path.join(reeds_path,'tests','data','county',f'{row["tech"]}.h5'),
                        os.path.join(
                            reeds_path,'inputs','variability','multi_year',
                            f'{row["tech"]}-{access_case}_county.h5')
                    )

                else:
                    try:
                        shutil.copy(
                            os.path.join(
                                sc_path,f'{row["tech"]}_{access_case}_county','results',
                                f'{row["tech"]}.h5'),
                            os.path.join(
                                reeds_path,'inputs','variability','multi_year',
                                f'{row["tech"]}-{access_case}_county.h5')
                        )
                    except FileNotFoundError:
                        err = (
                            "Cannot copy {}.\nCheck that you are connected to "
                            "external drive ({}).".format(
                                os.path.join(
                                    f'{row["tech"]}_{access_case}_county',
                                    'results',f'{row["tech"]}.h5'),
                                sc_path
                            )
                        )
                        raise FileNotFoundError(err)

                # Update the file version information
                condition = (
                    (file_version_new['tech'] == row['tech'])
                    & (file_version_new['access_case'] == row['access_case'])
                )

                if condition.any():
                    file_version_new.loc[condition, 'file version'] = sc_path.split("/")[-1]
                else:
                    newrow = pd.DataFrame(
                        data={
                            'tech': [row['tech']],
                            'access_case': [row['access_case']],
                            'file version': [sc_path.split("/")[-1]]
                        }
                    )
                    file_version_new = pd.concat([file_version_new, newrow])
                file_version_updates += 1

            # If non-NREL user, then save the name of the missing file, and write it out
            # in the error message below
            else:
                missing_file_versions.append(f'{row["tech"]}-{access_case}_county.h5')
    # If any county-level file is missing from the inputs folder but a file_version.csv exists,
    # then print out an error message to delete the file_version.csv and restart the run
    if (existing_fv) and (present_in_fv < 1):
        error = ("It appears that there is a file_version.csv present in\n"
            "/inputs/variability/multi-year/ despite a county-level file(s) missing\n"
            "from the folder. Delete file_version.csv from the folder and restart the run\n"
            "to have ReEDS redownload the missing county-level file(s)."
        )
        raise ValueError(error)
    # If any missing files for non-NREL users, then print out an error message with those
    # file names and where to download them
    if len(missing_file_versions) > 0:
        error = ("To run ReEDS at county-level spatial resolution, please download the following\n"
            "county-level data files from OpenEI to /inputs/variability/multi-year/\n\n"
            "Files:\n"
            +"\n".join(missing_file_versions)+"\n\n"
            +"OpenEI files link:\n"
            "[https://data.openei.org/submissions/8379]"
        )
        raise ValueError(error)
    # Write out the new file version file if there are any updates
    if file_version_updates > 0:
        file_version_new.to_csv(
            os.path.join(
                reeds_path,'inputs','variability','multi_year','file_version.csv'), index = False)


def calculate_county_fractions(df, regions_and_agglevel):
    """
    Calculates the value associated with each county as a percentage
    of the total value for the county's BA. The provided dataframe must have
    columns 'FIPS' and 'value'.
    """
    required_columns = ['FIPS', 'value']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if len(missing_columns) > 0:
        raise KeyError(f"Provided dataframe is missing required columns {missing_columns}")

    df = (
        df.merge(
            regions_and_agglevel['ba_county'],
            left_on='FIPS',
            right_on='county'
        )
        .rename(columns={'ba': 'PCA_REG'})
    )
    df['fracdata'] = (
        df.groupby('PCA_REG')
        ['value']
        .transform(lambda x: x / x.sum())
    )
    df = df[['PCA_REG', 'FIPS', 'fracdata']]

    return df


def upscale_from_county_to_ba(
    df,
    region_file_entry,
    agglevel_variables,
    regions_and_agglevel,
    aggfunc=None
):
    """
    Changes the resolution of the provided region_col from county to BA
    or mixed resolution and aggregates according to the provided aggfunc.
    """
    original_cols = df.columns
    region_col = region_file_entry['region_col']
    # Aggregate values to ba resolution if not running county-level resolution
    # and if county level is not a desired resolution in mixed resolution runs
    if 'county' not in agglevel_variables['agglevel']:
        df = (
            df.set_index(region_col)
            .merge(regions_and_agglevel['ba_county'], left_index=True, right_on='county')
            .drop('county', axis=1)
            .rename(columns={'ba': region_col})
        )
    # Mixed resolution procedure
    elif agglevel_variables['lvl'] == 'mult':
        # Filter out BA regions and aggregate
        df_ba = df[df[region_col].isin(agglevel_variables['BA_county_list'])]
        df_ba[region_col] = df_ba[region_col].map(agglevel_variables['BA_2_county'])

        # Filter out county regions
        df_county = df[df[region_col].isin(agglevel_variables['county_regions'])]

        # Combine county and BA
        df = pd.concat([df_ba, df_county])
    else:
        pass

    if aggfunc:
        fix_cols = region_file_entry['fix_cols'].split(',')
        if all([fix_col in df.columns for fix_col in fix_cols]):
            groupby_cols = list(set(fix_cols + [region_col]))
            df = df.groupby(groupby_cols, as_index=False).agg(aggfunc)
        else:
            df = df.groupby(region_col, as_index=False).agg(aggfunc)

    df = df[original_cols]

    return df


def write_region_indexed_file(
    df,
    dir_dst,
    source_deflator_map,
    sw,
    region_file_entry,
    regions_and_agglevel,
    agglevel_variables
):
    """
    Write a single region-indexed file to the dir_dst directory
    """
    filename = region_file_entry['filename']
    # Get the filetype of the output file from the filename string
    filetype_out = os.path.splitext(filename)[1].strip('.')

    #---- Write data to dir_dst (inputs_case) folder ----
    if filetype_out == 'h5':
        reeds.io.write_profile_to_h5(df, filename, dir_dst)
    else:
        # Special cases: These files' values need to be adjusted to copy
        filepath = region_file_entry['filepath']
        match filename:
            case 'bio_supplycurve.csv':
                # Adjust for inflation
                df['price'] = df['price'].astype(float) * source_deflator_map[filepath]
            case 'co2_site_char.csv':
                # Adjust for inflation
                df[f"bec_{sw['GSw_CO2_BEC']}"] *= source_deflator_map[filepath]
            case (
                'can_exports.csv'
                | 'can_imports.csv'
                | 'demonstration_plants.csv'
                | 'distpvcap.csv'
                | 'h2_ba_share.csv'
                | 'regional_cap_cost_mult.csv'
            ):
                if agglevel_variables['lvl'] != 'county':
                    df = upscale_from_county_to_ba(
                        df=df,
                        region_file_entry=region_file_entry,
                        agglevel_variables=agglevel_variables,
                        regions_and_agglevel=regions_and_agglevel,
                        aggfunc=region_file_entry.aggfunc
                    )
                # Mixed resolution procedure
                elif agglevel_variables['lvl'] == 'mult':
                    # Filter out BA regions and aggregate
                    df_ba = df[df['r'].isin(agglevel_variables['BA_county_list'])].copy()  
                    df_ba.loc[:, 'r'] = df_ba['r'].map(agglevel_variables['BA_2_county']) 
                    df_ba = df_ba.groupby('r', as_index=False).sum()

                    # Filter out county regions
                    df_county = df[df['r'].isin(agglevel_variables['county_regions'])]

                    # Combine county and BA
                    df = pd.concat([df_ba, df_county])

            case 'disagg_population.csv':
                df = calculate_county_fractions(df, regions_and_agglevel)
            case _:
                pass

        df.to_csv(os.path.join(dir_dst,filename), index=False)


def write_region_indexed_files(
    inputs_case,
    sw,
    region_files,
    regions_and_agglevel,
    agglevel_variables,
    source_deflator_map
):
    """
    Filter and copy data for files with regions
    """
    print('Copying region-indexed files: filtering for valid regions')
    for _, region_file_entry in region_files.iterrows():
        print(f'...copying {region_file_entry.filename}')

        # Read file and return dataframe filtered for valid regions
        df = subset_to_valid_regions(
            sw,
            region_file_entry,
            agglevel_variables,
            regions_and_agglevel,
            inputs_case
        )

        write_region_indexed_file(
            df,
            inputs_case,
            source_deflator_map,
            sw,
            region_file_entry,
            regions_and_agglevel,
            agglevel_variables
        )


def write_miscellaneous_files(
    sw,
    regions_and_agglevel,
    agglevel_variables,
    source_deflator_map,
    inputs_case,
    reeds_path
):
    """
    Handle miscellaneous files.
    Many of these files are not in the non_region_files and region_files set
    (runfiles.csv - from function read_runfiles).
    """
    # ---- Miscellaneous files not in non_region_files or region_files ----
    val_nercr = regions_and_agglevel['valid_regions']['nercr']

    pd.DataFrame(
        {'*pvb_type': [f'pvb{i}' for i in sw['GSw_PVB_Types'].split('_')],
        'ilr': [np.around(float(c) / 100, 2) for c in sw['GSw_PVB_ILR'].split('_')
                ][0:len(sw['GSw_PVB_Types'].split('_'))]}
    ).to_csv(os.path.join(inputs_case, 'pvb_ilr.csv'), index=False)

    pd.DataFrame(
        {'*pvb_type': [f'pvb{i}' for i in sw['GSw_PVB_Types'].split('_')],
        'bir': [np.around(float(c) / 100, 2) for c in sw['GSw_PVB_BIR'].split('_')
                ][0:len(sw['GSw_PVB_Types'].split('_'))]}
    ).to_csv(os.path.join(inputs_case, 'pvb_bir.csv'), index=False)

    # Constant value if input is float, otherwise named profile
    try:
        rate = float(sw['GSw_MethaneLeakageScen'])
        pd.Series(index=range(2010,2051), data=rate, name='constant').rename_axis('*t').round(5).to_csv(
            os.path.join(inputs_case,'methane_leakage_rate.csv'))
    except ValueError:
        pd.read_csv(
            os.path.join(reeds_path,'inputs','emission_constraints','methane_leakage_rate.csv'),
            index_col='t',
        )[sw['GSw_MethaneLeakageScen']].rename_axis('*t').round(5).to_csv(
            os.path.join(inputs_case,'methane_leakage_rate.csv'))

    # Add this_year to years_until_endogenous to generate the tech-specific firstyear.csv file
    scalars = reeds.io.get_scalars(full=True)
    (
        pd.read_csv(
            # years_until_endogenous created using function write_non_region_files
            os.path.join(inputs_case, 'years_until_endogenous.csv'),
            index_col=0,
        ).squeeze(1)
        + int(scalars.loc['this_year','value'])
    ).rename_axis('*i').rename('t').to_csv(os.path.join(inputs_case, 'firstyear.csv'))


    ### Single column from input table ###

    pd.read_csv(
        os.path.join(reeds_path,'inputs','emission_constraints','ng_crf_penalty.csv'), index_col='t',
    )[sw['GSw_NG_CRF_penalty']].rename_axis('*t').to_csv(
        os.path.join(inputs_case,'ng_crf_penalty.csv')
    )

    gwp = pd.read_csv(
        os.path.join(reeds_path,'inputs','emission_constraints','gwp.csv'),
        index_col='e',
    )
    if sw['GSw_GWP'] in gwp:
        gwp_write = gwp[sw['GSw_GWP']]
    else:
        gwp_ch4, gwp_n2o = [float(i.split('_')[1]) for i in sw['GSw_GWP'].split('/')]
        gwp_write = pd.Series({'CO2':1, 'CH4':gwp_ch4, 'N2O':gwp_n2o})
    gwp_write.to_csv(os.path.join(inputs_case,'gwp.csv'), header=False)

    # Calculate CO2 cap based on GSw_Region chosen (national or sub-national regions)
    # Read in national co2 cap
    co2_cap = (
        pd.read_csv(
            os.path.join(reeds_path, 'inputs', 'emission_constraints', 'co2_cap.csv'),
            index_col='t',
        )
        .loc[sw['GSw_AnnualCapScen']]
        .rename_axis('*t')
        .rename('tonne_per_year')
    )

    # Read in 2022 CO2 emission share by county calculated from 2022 eGrid emission data:
    em_share = pd.read_csv(
        os.path.join(
            reeds_path,'inputs','emission_constraints','county_co2_share_egrid_2022.csv'),
        index_col=0)

    # Filter the counties that are in chosen GSw_Region
    val_county = pd.read_csv(os.path.join(inputs_case,'val_county.csv'),names=['r'])

    # Merge emission share by county with the counties in GSw_Region and calculate emission share of GSw_Region
    region_em_share = val_county.merge(em_share, on='r', how='left').fillna(0)
    region_em_share = region_em_share['share'].sum()

    # Apply the emission share to national cap to get the emission cap trajectory of GSw_Region
    co2_cap *= region_em_share
    co2_cap.round(0).to_csv(os.path.join(inputs_case, 'co2_cap.csv'))

    # CO2 tax
    pd.read_csv(
        os.path.join(reeds_path,'inputs','emission_constraints','co2_tax.csv'), index_col='t',
    )[sw['GSw_CarbTaxOption']].rename_axis('*t').round(2).to_csv(
        os.path.join(inputs_case,'co2_tax.csv')
    )

    solveyears = pd.read_csv(
        os.path.join(reeds_path,'inputs','modeledyears.csv'),
        usecols=[sw['yearset_suffix']],
    ).squeeze(1).dropna().astype(int).tolist()
    if int(sw['startyear']) not in solveyears:
        solveyears.append(int(sw['startyear']))
        solveyears = sorted(solveyears)
    solveyears = [y for y in solveyears if (y >= int(sw['startyear'])) and (y <= int(sw['endyear']))]
    pd.DataFrame(columns=solveyears).to_csv(
        os.path.join(inputs_case,'modeledyears.csv'), index=False)

    pd.read_csv(
        os.path.join(reeds_path,'inputs','national_generation','gen_mandate_trajectory.csv'),
        index_col='GSw_GenMandateScen'
    ).loc[sw['GSw_GenMandateScen']].rename_axis('*t').round(5).to_csv(
        os.path.join(inputs_case,'gen_mandate_trajectory.csv')
    )

    pd.read_csv(
        os.path.join(reeds_path,'inputs','national_generation','gen_mandate_tech_list.csv'),
        index_col='*i',
    )[sw['GSw_GenMandateList']].to_csv(
        os.path.join(inputs_case,'gen_mandate_tech_list.csv')
    )

    pd.read_csv(
        os.path.join(reeds_path,'inputs','climate','climate_heuristics_yearfrac.csv'),
        index_col='*t',
    )[sw['GSw_ClimateHeuristics']].round(3).to_csv(
        os.path.join(inputs_case,'climate_heuristics_yearfrac.csv')
    )

    pd.read_csv(
        os.path.join(reeds_path,'inputs','climate','climate_heuristics_finalyear.csv'),
        index_col='*parameter',
    )[sw['GSw_ClimateHeuristics']].round(3).to_csv(
        os.path.join(inputs_case,'climate_heuristics_finalyear.csv')
    )

    pd.read_csv(
        os.path.join(reeds_path,'inputs','upgrades','upgrade_costs_ccs_coal.csv'),
        index_col='t',
    )[sw['ccs_upgrade_cost_case']].round(3).rename_axis('*t').to_csv(
        os.path.join(inputs_case,'upgrade_costs_ccs_coal.csv')
    )

    pd.read_csv(
        os.path.join(reeds_path,'inputs','upgrades','upgrade_costs_ccs_gas.csv'),
        index_col='t',
    )[sw['ccs_upgrade_cost_case']].round(3).rename_axis('*t').to_csv(
        os.path.join(inputs_case,'upgrade_costs_ccs_gas.csv')
    )

    prm_profiles = pd.read_csv(
        os.path.join(reeds_path,'inputs','reserves','prm_annual.csv'),
        index_col=['*nercr','t']
    )
    if sw['GSw_PRM_scenario'] in prm_profiles:
        prm = prm_profiles[sw['GSw_PRM_scenario']]
    else:
        prm = pd.Series(index=prm_profiles.index, data=float(sw['GSw_PRM_scenario']))

    # Filter values to those that only include valide nercr regions while processing
    (prm[prm.index.get_level_values('*nercr').isin(val_nercr)]
        .unstack('*nercr').reindex(solveyears)
        .fillna(method='bfill').rename_axis('t').stack('*nercr')
        .reorder_levels(['*nercr','t']).round(4)
    ).to_csv(os.path.join(inputs_case,'prm_annual.csv'))

    # Deflate nuke_fom_adj and coal_fom_adj
    for relative_fpath in ["inputs/plant_characteristics/nuke_fom_adj.csv",
                    "inputs/plant_characteristics/coal_fom_adj.csv"]:
        fname = os.path.basename(relative_fpath)
        (
            pd.read_csv(os.path.join(reeds_path,relative_fpath),
                        index_col='*t')
            .mul(source_deflator_map[relative_fpath])
            .round(0)
            .to_csv(os.path.join(inputs_case,fname))
        )

    # Add capacity deployment limits based on interconnection queue data
    cap_queue = pd.read_csv(
        os.path.join(reeds_path,'inputs','capacity_exogenous','interconnection_queues.csv'))
    # Filter the counties that are in chosen GSw_Region
    cap_queue = cap_queue[cap_queue['r'].isin(val_county['r'])]

    # Single resolution procedure
    if (agglevel_variables["lvl"] != 'county') and ('county' not in agglevel_variables['agglevel']):
        cap_queue = cap_queue.rename(columns={'r':'county'})
        cap_queue = pd.merge(cap_queue, regions_and_agglevel["r_county"], on='county', how='left').dropna()
        cap_queue = cap_queue.drop('county', axis=1)

    # Mixed resolution procedure
    elif agglevel_variables['lvl'] == 'mult':
        # Filter out BA regions and aggregate
        cap_queue_ba = cap_queue[cap_queue['r'].isin(agglevel_variables['BA_county_list'])]
        if 'aggreg' in agglevel_variables['agglevel'] :
            r_county_dict = regions_and_agglevel["r_county"].set_index('county')['r'].to_dict()
            cap_queue_ba['r'] = cap_queue_ba['r'].map(r_county_dict)

        else:
            cap_queue_ba['r'] = cap_queue_ba['r'].map(agglevel_variables['BA_2_county'])

        # Filter out county regions
        cap_queue_county = cap_queue[cap_queue['r'].isin(agglevel_variables['county_regions'])]

        #combine BA and county
        cap_queue = pd.concat([cap_queue_ba,cap_queue_county])

    cap_queue = cap_queue.groupby(['tg','r'],as_index=False).sum()
    cap_queue.to_csv(os.path.join(inputs_case,'cap_limit.csv'), index=False)



    large_load_additions = pd.read_csv(os.path.join(reeds_path, 'inputs', 'load', f"large_load_additions_{sw['GSw_LargeLoadAdd']}.csv"))
    # Single resolution procedure
    if (agglevel_variables["lvl"] != 'county') and ('county' not in agglevel_variables['agglevel']):
        large_load_additions = large_load_additions.rename(columns={'*r':'county'})
        large_load_additions = pd.merge(
            large_load_additions, regions_and_agglevel["r_county"], on='county', how='left'
        ).dropna()
        large_load_additions = large_load_additions.rename(columns ={'r':'*r'}).drop('county', axis=1)[['*r', 't', 'value']]
    # Mixed resolution procedure
    elif agglevel_variables['lvl'] == 'mult':
        # Filter out BA regions and aggregate
        large_load_additions_ba = large_load_additions[
            large_load_additions['*r'].isin(agglevel_variables['BA_county_list'])]
        if 'aggreg' in agglevel_variables['agglevel'] :
            r_county_dict = regions_and_agglevel["r_county"].set_index('county')['r'].to_dict()
            large_load_additions_ba['*r'] = large_load_additions_ba['*r'].map(r_county_dict)
        else:
            large_load_additions_ba['*r'] = large_load_additions_ba['*r'].map(
                agglevel_variables['BA_2_county'])

        # Filter out county regions
        large_load_additions_county = large_load_additions[
            large_load_additions['*r'].isin(agglevel_variables['county_regions'])]

        # Combine county and BA
        large_load_additions = pd.concat([large_load_additions_ba,large_load_additions_county])

    large_load_additions = large_load_additions.groupby(['*r','t'],as_index=False).sum()
    large_load_additions.to_csv(os.path.join(inputs_case,'large_load_additions.csv'), index=False)

    # ----  Miscelanous files in non_region_files or region_files (in this case we are overwriting them)
    # Expand i (technologies) set if modeling water use. Overwrite originals.
    if int(sw['GSw_WaterMain']):
        pd.concat([
            pd.read_csv(
                os.path.join(inputs_case,'i.csv'),
                comment='*', header=None).squeeze(1),
            pd.read_csv(
                os.path.join(inputs_case,'i_coolingtech_watersource.csv'),
                comment='*', header=None).squeeze(1),
            pd.read_csv(
                os.path.join(inputs_case,'i_coolingtech_watersource_upgrades.csv'),
                comment='*', header=None).squeeze(1),
        ]).to_csv(os.path.join(inputs_case,'i.csv'), header=False, index=False)

    # Calculate county land areas as percentage of BA land areas
    dfcounty = reeds.io.get_countymap(exclude_water_areas=True)
    county_geosize = (
        dfcounty.set_index('rb')
        .rename_axis('FIPS')
        .area
        .rename('value')
        .reset_index()
    )
    county_geosize_relative = calculate_county_fractions(
        county_geosize, regions_and_agglevel
    )
    county_geosize_relative.to_csv(
        os.path.join(inputs_case,'disagg_geosize.csv'),
        index=False
    )


def generate_maps_gpkg(inputs_case):
    """
    Write maps.gpkg to speed up map visualization in postprocessing.
    If using region dis/aggregation, maps.gpkg is overwritten in aggregation_regions.py.
    """
    mapsfile = os.path.join(inputs_case, 'maps.gpkg')
    if os.path.exists(mapsfile):
        os.remove(mapsfile)

    dfmap = reeds.io.get_dfmap(os.path.abspath(os.path.join(inputs_case,'..')))
    for level in dfmap:
        dfmap[level].to_file(mapsfile, layer=level)


#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================
def main(reeds_path, inputs_case, NARIS=False):
    """
    Run copy_files.py for use in the ReEDS workflow

    Parameters:
    reeds_path : str (Path to the ReEDS directory)
    inputs_case : str (Path to the run/inputs_case directory)
    NARIS : Ture/False (NARIS: North American Renewable Integration Study)

    Returns:
    None (Writes files to the inputs_case directory)
    """
    #%% ===========================================================================
    ### --- Gather dataframes and dictionaries necessary for the script execution ---
    ### ===========================================================================
    # Obtain data necessary to filter and aggregate regions
    regions_and_agglevel = get_regions_and_agglevel(reeds_path, inputs_case, NARIS=NARIS)
    # Use agglevel_variables function to obtain spatial resolution variables
    agglevel_variables = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)

    #%% ===========================================================================
    ### --- Copying files ---
    ### ===========================================================================

    # Copy county-level vre hourly profiles to the ReEDS folder if necessary
    if (agglevel_variables['lvl'] == 'county') or ('county' in agglevel_variables['agglevel']):
        write_county_vre_hourly_profiles(inputs_case, reeds_path)

    sw = reeds.io.get_switches(inputs_case)
    runfiles, non_region_files, region_files = read_runfiles(
        reeds_path,
        inputs_case,
        sw,
        agglevel_variables
    )

    # Write general GAMS files
    # Write GAMS-readable sets to the inputs_case directory
    write_GAMS_sets(runfiles, reeds_path, inputs_case)

    # Rewrite the switches tables as GAMS-readable definition
    # (gswitches.csv is first written at runbatch.py)
    scalar_csv_to_txt(os.path.join(inputs_case,'gswitches.csv'))

    # Copy non-region files
    write_non_region_files(non_region_files, sw, inputs_case, regions_and_agglevel)

    # Copy region files
    source_deflator_map = get_source_deflator_map(reeds_path)
    write_region_indexed_files(
        inputs_case,
        sw,
        region_files,
        regions_and_agglevel,
        agglevel_variables,
        source_deflator_map
    )

    # Create a maps.gpkg for this run
    # Skip if using region dis/aggregation, maps will be written in aggregation_regions.py.
    if agglevel_variables['lvl'] == 'ba':
        generate_maps_gpkg(inputs_case)

    #%% ===========================================================================
    ### --- Exceptions ---
    ### ===========================================================================
    # Handle miscellaneous files not included in non_region_files, region_files.
    # Needs to run after copy of non-region files
    write_miscellaneous_files(
        sw,
        regions_and_agglevel,
        agglevel_variables,
        source_deflator_map,
        inputs_case,
        reeds_path
    )

#%% Procedure
if __name__ == '__main__' and not hasattr(sys, 'ps1'):
    # ---- Parse arguments ----
    parser = argparse.ArgumentParser(description="Copy files needed for this run")
    parser.add_argument('reeds_path', help='ReEDS directory')
    parser.add_argument('inputs_case', help='output directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    # #%% Settings for testing ###
    # reeds_path = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
    # inputs_case = os.path.join(reeds_path,'runs','v20250126_hydroprasM0_Pacific','inputs_case','')
    # NARIS = False

    # ---- Set up logger ----
    tic = datetime.datetime.now()
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    print('Starting copy_files.py')
    main(reeds_path, inputs_case)

    reeds.log.toc(tic=tic, year=0, process='input_processing/copy_files.py',
        path=os.path.join(inputs_case,'..'))
    print('Finished copy_files.py')
    