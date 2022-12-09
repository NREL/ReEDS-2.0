#%% IMPORTS
import argparse
import os
import pandas as pd
import numpy as np
import h5py
import shutil

#%% FUNCTIONS ###
def read_file(filename, index_columns=1):
    """
    Read input file of various types (for backwards-compatibility)
    """
    # Try reading a .h5 file written by pandas
    try:
        df = pd.read_hdf(filename+'.h5')
    # Try reading a .h5 file written by h5py
    except (ValueError, TypeError, FileNotFoundError, OSError):
        try:
            with h5py.File(filename+'.h5', 'r') as f:
                keys = list(f)
                datakey = 'data' if 'data' in keys else ('cf' if 'cf' in keys else 'load')
                ### If none of these keys work, we're dealing with EER-formatted load
                if datakey not in keys:
                    years = [int(y) for y in keys if y != 'columns']
                    df = pd.concat(
                        {y: pd.DataFrame(f[str(y)][...]) for y in years},
                        axis=0)
                    df.index = df.index.rename(['year','hour'])
                else:
                    df = pd.DataFrame(f[datakey][:])
                    df.index = pd.Series(f['index']).values
                df.columns = pd.Series(f['columns']).map(
                    lambda x: x if type(x) is str else x.decode('utf-8')).values
        # Fall back to .csv.gz
        except (FileNotFoundError, OSError):
            df = pd.read_csv(
                filename+'.csv.gz', index_col=list(range(index_columns)),
                float_precision='round_trip',
            )

    return df


def csp_dispatch(cfcsp, sm=2.4, storage_duration=10):
    """
    Use a simple no-foresight heuristic to dispatch CSP.
    Excess energy from the solar field (i.e. energy above the max plant power output)
    is sent to storage, and energy in storage is dispatched as soon as possible.

    Inputs
    ------
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


#%% Main function
def hourly_prep(basedir, inputs_case):
    # #%% Settings for debugging ###
    # basedir = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
    # inputs_case = os.path.join(
    #     basedir,'runs','v20220906_NTPm1_ercot_seq','inputs_case')

    #%% Fixed inputs
    GSw_CSP_Types = '1_2'

    #%% Inputs from switches
    sw = pd.read_csv(
        os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)
    GSw_EFS1_AllYearLoad = sw.GSw_EFS1_AllYearLoad
    GSw_IndividualSites = int(sw.GSw_IndividualSites)
    GSw_IndividualSiteAgg = sw.GSw_IndividualSiteAgg
    filepath_individual_sites = sw.filepath_individual_sites
    GSw_SitingWindOns = sw.GSw_SitingWindOns
    GSw_SitingWindOfs = sw.GSw_SitingWindOfs
    GSw_SitingUPV = sw.GSw_SitingUPV
    osprey_years = sw.osprey_years
    GSw_PVB_Types = sw.GSw_PVB_Types
    GSw_PVB = int(sw.GSw_PVB)
    capcredit_hierarchy_level = sw.capcredit_hierarchy_level

    #%%### Load inputs
    ### Override GSw_PVB_Types if GSw_PVB is turned off
    GSw_PVB_Types = (
        [int(i) for i in GSw_PVB_Types.split('_')] if int(GSw_PVB)
        else []
    )
    GSw_CSP_Types = [int(i) for i in GSw_CSP_Types.split('_')]

    # -------- Define the file paths --------
    folder = 'multi_year'
    path_variability = os.path.join(basedir,'inputs','variability')

    # -------- Datetime mapper --------
    hdtmap = pd.read_csv(os.path.join(inputs_case, 'h_dt_szn.csv'))
    ### EFS-style load only has one year of data
    if (GSw_EFS1_AllYearLoad == 'default') or ('EER' in GSw_EFS1_AllYearLoad):
        hdtmap_load = hdtmap
    else:
        hdtmap_load = hdtmap[hdtmap.year == 2012]

    ###### Load the input parameters
    scalars = pd.read_csv(
        os.path.join(inputs_case,'scalars.csv'),
        header=None, usecols=[0,1], index_col=0, squeeze=True)
    ### distloss
    distloss = scalars['distloss']

    ### BAs present in the current run
    ### valid_ba_list -> rfeas
    rfeas = sorted(
        pd.read_csv(os.path.join(inputs_case, 'valid_ba_list.csv'), squeeze=True, header=None)
        .tolist())
    ### Years in the current run
    solveyears = pd.read_csv(
        os.path.join(inputs_case,'modeledyears.csv'),
        header=0
    ).columns.astype(int).values

    ### Map BAs to wind/CSP resource regions
    rsmap = pd.read_csv(
        os.path.join(inputs_case,'rsmap.csv')
    ).rename(columns={'*r':'r'})
    rb2rs = rsmap.set_index('r')['rs']
    rs2rb = rsmap.set_index('rs')['r']

    ### Load spatial hierarchy
    hierarchy = pd.read_csv(
        os.path.join(inputs_case,'hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    ### Add ccreg column with the desired hierarchy level
    hierarchy['ccreg'] = hierarchy[capcredit_hierarchy_level].copy()
    ### Map regions to new ccreg's
    rb2ccreg = hierarchy['ccreg']
    rs2ccreg = rs2rb.map(rb2ccreg)
    r2ccreg = pd.concat([rb2ccreg,rs2ccreg], axis=0)

    # BA's and resource regions in the current run
    rfeas_cap = rfeas + rb2rs.loc[rfeas].tolist()

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
                    if not n == len(temp2)-2: temp_tech += '_'
                for c in range(temp_low,temp_high+1):
                    temp_save.append('{}_{}'.format(temp_tech,str(c)))
        for subset in temp_remove:
            techs[tech].remove(subset)
        techs[tech].extend(temp_save)
    vre_dist = techs['VRE_DISTRIBUTED']

    #HANDLING STATIC INPUTS FOR THE FIRST SOLVE YEAR
    # Load
    #       - Filter out load profiles not included in this run
    #       - Scale load profiles by distribution loss factor and load calibration factor
    # Resources:
    #       - Filter out all resources not included in this run
    #       - Add the distributed PV resources
    # RECF:
    #       - Add the distributed PV profiles
    #       - Filter out all resources not included in this run
    #       - Sort the columns in recf to be in the same order as the rows in resources
    #       - Scale distributed resource CF profiles by distribution loss factor and tiein loss factor
    # ------- Read in the static inputs for this run -------

    def get_df_ind(tech, site_prefix, siting_case, sitemap_suffix, has_exog_cap):
        ### Load the dataframe of hourly profiles for each site
        with h5py.File(os.path.join(filepath_individual_sites,
                                    '{}_site-{}.h5'.format(tech, siting_case)),'r') as f:
            df_ind = pd.DataFrame(f['cf'][:])
            df_ind.index = pd.Series(f['index']).values
            df_ind.columns = [
                tech + '_' + col
                for col in pd.Series(f['columns']).map(
                    lambda x: x if type(x) is str else x.decode('utf-8')).values]

        ### Load the lookup table for site aggregation
        lookup_siteagg = pd.read_csv(
            os.path.join(basedir,'inputs','supplycurvedata','sitemap{}.csv'.format(sitemap_suffix)),
            index_col='sc_point_gid'
        )['ragg{}'.format(GSw_IndividualSiteAgg)]
        lookup_siteagg.index = site_prefix + lookup_siteagg.index.astype(str)

        ### Load the site capacities to calculate the site-capacity-weighted average profiles
        supplycurvecapacity = pd.read_csv(
            os.path.join(basedir,'inputs','supplycurvedata',
                            '{}_supply_curve_site-{}.csv'.format(tech, siting_case)),
            usecols=['region','class','capacity'], dtype={'capacity':np.float32}
        )

        ### Load exogenous capacity, which is removed from supply curve capacity in hourlize
        if has_exog_cap:
            exogenouscapacity = pd.read_csv(
                os.path.join(basedir,'inputs','capacitydata',
                                    '{}_exog_cap_site_{}.csv'.format(tech, siting_case)),
            )
            ### Only keep 2010 capacity (since exogenous records pre-2010 builds)
            exogenouscapacity = exogenouscapacity.loc[exogenouscapacity.year==2010].copy()
            ### Merge supply-curve and exogenous capacity to get total site capacity
            sitecapacity = supplycurvecapacity.merge(
                exogenouscapacity[['region','capacity']], on='region', suffixes=('','_exog'),
                how='outer'
            )
            sitecapacity.capacity += sitecapacity.capacity_exog.fillna(0)
        else:
            sitecapacity = supplycurvecapacity.copy()

        sitecapacity.index = (
            tech + '_' + sitecapacity['class'].astype(str) + '_' + sitecapacity.region)

        ### Multiply by site capacity
        df_ind *= sitecapacity['capacity']

        ### Expand the column indices
        df_ind.columns = pd.MultiIndex.from_tuples(
            ### (ragg,rs, i)
            [(lookup_siteagg[c.rsplit('_',1)[1]], c.rsplit('_',1)[1], c.rsplit('_',1)[0]) 
            for c in df_ind.columns]
        )

        ### Get the full lookup for later use
        lookup = pd.DataFrame(
            [list(c) for c in df_ind.columns.values],
            columns=['ragg','rs','i']
        )

        ### Get available capacity per aggregated resource profile
        aggcapacity = (
            lookup
            .merge(sitecapacity, left_on='rs', right_on='region')
            .groupby('ragg')['capacity'].sum()
        )

        ### Average at aggregation level; chunk it for memory+speed
        chunksize = 1000
        df_ind = pd.concat(
            ### Weighted average CF = sum(capacity * CF) / sum(capacity)
            [(df_ind.loc[i:i+chunksize-1].sum(axis=1, level=0)
                / aggcapacity).astype(np.float16).fillna(0)
                for i in np.arange(0, len(df_ind), chunksize)],
            axis=0,
        )

        ### Include the technology (without class) in the column name
        df_ind.columns = [tech + '_' + c for c in df_ind.columns]
        lookup['ragg'] = tech + '_' + lookup['ragg']

        return df_ind, lookup, sitecapacity


    if GSw_IndividualSites:
        df_windons, lookupons, sitecapacity_ons = get_df_ind(
            'wind-ons','i', GSw_SitingWindOns, '', True)
        df_windofs, lookupofs, sitecapacity_ofs = get_df_ind(
            'wind-ofs','o', GSw_SitingWindOfs, '_offshore', False)

        ### Concatenate lookups because this is used later.
        lookup = pd.concat([lookupons, lookupofs],sort=False,ignore_index=True)

        ### Save the list of sites to include
        rs_ls = (['s{}'.format(i) for i in range(1,455)]
              + sitecapacity_ons.index.map(lambda x: x.split('_')[-1]).tolist()
              + sitecapacity_ofs.index.map(lambda x: x.split('_')[-1]).tolist())
        pd.Series(rs_ls).to_csv(
            os.path.join(inputs_case, 'rs.csv'), index=False, header=False)
        r_ls = ['p{}'.format(i) for i in range(1,206)] + rs_ls
        pd.Series(r_ls).to_csv(
            os.path.join(inputs_case, 'r.csv'), index=False, header=False)

        ### Overwrite rsmap.csv, leaving out excluded sites
        rsmap = pd.read_csv(os.path.join(inputs_case, 'rsmap.csv'))
        rsmap.loc[
            rsmap.rs.isin(sitecapacity_ons.region.values.tolist() +
                          sitecapacity_ofs.region.values.tolist())
            | rsmap.rs.map(lambda x: x.startswith('s'))
        ].to_csv(
            os.path.join(inputs_case, 'rsmap_filtered.csv'), index=False)

    else:
        df_windons = read_file(
            os.path.join(path_variability, folder, 'wind-ons-{}'.format(GSw_SitingWindOns)))
        df_windons.columns = ['wind-ons_' + col for col in df_windons]
        ### Don't do aggregation in this case, so make a 1:1 lookup table
        lookup = pd.DataFrame({'ragg':df_windons.columns.values})
        lookup['rs'] = lookup.ragg.map(lambda x: x.rsplit('_',1)[1])
        lookup['i'] = lookup.ragg.map(lambda x: x.rsplit('_',1)[0])
        ### Copy over rsmap_filtered.csv
        shutil.copy(
            os.path.join(inputs_case, 'rsmap.csv'),
            os.path.join(inputs_case, 'rsmap_filtered.csv'),
        )
        ### Offshore sreg
        df_windofs = read_file(
            os.path.join(path_variability, folder, 'wind-ofs-{}'.format(GSw_SitingWindOfs)))
        df_windofs.columns = ['wind-ofs_' + col for col in df_windofs]

    df_upv = read_file(
        os.path.join(path_variability, folder, 'upv-{}'.format(GSw_SitingUPV)))
    df_upv.columns = ['upv_' + col for col in df_upv]

    df_dupv = read_file(
        os.path.join(path_variability, folder, 'dupv'))
    df_dupv.columns = ['dupv_' + col for col in df_dupv]

    cspcf = read_file(
        os.path.join(path_variability, folder, 'csp'))

    #%% Format PV+battery profiles
    ### Get the PVB types
    pvb_ilr = pd.read_csv(
        os.path.join(inputs_case, 'pvb_ilr.csv'),
        header=0, names=['pvb_type','ilr'], index_col='pvb_type', squeeze=True)
    df_pvb = {}
    for pvb_type in GSw_PVB_Types:
        ilr = int(pvb_ilr['pvb{}'.format(pvb_type)] * 100)
        ### UPV uses ILR = 1.3, so use its profile if ILR = 1.3
        infile = 'upv' if ilr == 130 else 'upv_{}AC'.format(ilr)
        df_pvb[pvb_type] = read_file(
            os.path.join(path_variability, 'multi_year', '{}-{}'.format(infile, GSw_SitingUPV)))
        df_pvb[pvb_type].columns = ['pvb{}_{}'.format(pvb_type, c)
                                    for c in df_pvb[pvb_type].columns]
        df_pvb[pvb_type].index = df_upv.index.copy()

    recf = pd.concat(
        [df_windons, df_windofs, df_upv, df_dupv]
        + [df_pvb[pvb_type] for pvb_type in df_pvb],
        sort=False, axis=1, copy=False)

    toadd = pd.DataFrame({'ragg': [c for c in recf.columns if c not in lookup.ragg.values]})
    toadd['rs'] = [c.rsplit('_', 1)[1] for c in toadd.ragg.values]
    toadd['i'] = [c.rsplit('_', 1)[0] for c in toadd.ragg.values]
    resources = (
        pd.concat([lookup, toadd], axis=0, ignore_index=True)
        .rename(columns={'ragg':'resource','rs':'area','i':'tech'})
        .sort_values('resource').reset_index(drop=True)
    )

    distpvCF = pd.read_csv(
        os.path.join(inputs_case,'distPVCF.csv')).rename(columns={'Unnamed: 0':'resource'})

    # ------- Performing load modifications -------
    if GSw_EFS1_AllYearLoad == "default":
        load_profiles = pd.read_csv(
            os.path.join(path_variability, folder, 'load.csv.gz'),
            index_col=0, float_precision='round_trip')[rfeas]
    else:
        load_profiles = read_file(
            os.path.join(path_variability,'EFS_Load',(GSw_EFS1_AllYearLoad+'_load_hourly')),
            index_columns=2,
        ).loc[solveyears,rfeas]

    if GSw_EFS1_AllYearLoad == 'default':

        #Importing timeslice hours for performing load scaling
        hours = pd.read_csv(
            os.path.join(inputs_case,'numhours.csv'), 
            header=None, names=['h','numhours'], index_col='h', squeeze=True)
        hours.index = hours.index.map(lambda x: x.upper())

        # Prepare a dataframe for scaling the load profiles
        # Scaling is done using the annual 2010 timeslice load by BA
        load_TS_2010 = pd.read_csv(os.path.join(inputs_case,'load_2010.csv'), index_col='r')
        # Get total load in each timeslice and region
        load_TS_2010 *= hours
        # Get annual load by region
        load_TS_2010_total = load_TS_2010.sum(1)

        ### Normalize load profiles with 2010 load timeslices
        load_profiles.index = pd.MultiIndex.from_frame(hdtmap_load[['year','hour']])
        ## Scale 2007-2013 load profiles by (actual 2010 load) / (yearly profile load)
        ## so that all singe-year sums equal 2010 load
        load_profiles *= (load_TS_2010_total / load_profiles.groupby('year').sum())
        load_profiles.reset_index(level='year', drop=True, inplace=True)

    # Adjusting load profiles by distribution loss factor and load calibration factor
    load_profiles /= (1 - distloss)


    # ------- Performing resource modifications -------

    # Getting all distpv resources and filtering out those not included in this run
    distpv_resources = pd.DataFrame(distpvCF['resource'])
    distpv_resources.loc[:,'tech'] = 'distpv'
    distpv_resources.loc[:,'area'] = distpv_resources.loc[:,'resource']
    distpv_resources.loc[:,'resource'] = (
        distpv_resources.loc[:,'tech'] + '_' + distpv_resources.loc[:,'resource'])

    # Adding distpv resources to resources
    resources = pd.concat([resources,distpv_resources], sort=False, ignore_index=True)


    # ------- Performing recf modifications -------

    # There is only one year of data for distpv
    # Create multi year distpv profiles by scaling dupv profiles
    # Subset dupv resources
    dupv_resource = ['dupv_' + str(n) for n in range(1,11)]
    resource_temp = resources[resources['tech'].isin(dupv_resource)].reset_index(drop=True)
    missing_dupv_bas = (
        # Missing several BA's to scale by dupv; use upv instead
        resources[~(resources.area.isin(resource_temp.area)) & (resources.tech.str.contains('upv'))]
        .drop_duplicates(subset = 'area',keep = 'last')
    )
    resource_temp = resource_temp.drop_duplicates(subset=['area'], keep='last')
    resource_temp = pd.concat([resource_temp,missing_dupv_bas]).sort_values('resource')

    # Grab the resource profiles for each region to be scaled
    distpv_profiles = recf[resource_temp['resource'].tolist()]
    distpv_profiles.columns = resource_temp['area'].tolist()

    # Aggregate to timeslices for scaling
    distpv_profiles.index = hdtmap['h']
    distpv_timeslice_cf = distpv_profiles.groupby('h').mean().transpose()

    distpvCF.drop('H17', axis=1, inplace=True)
    distpvCF.set_index('resource', inplace=True)
    distpvCF.columns = ['h' + str(n) for n in range(1, 17)]
    # Create and apply scaling factor for each timeslice
    temp_scaling_factor = distpvCF / distpv_timeslice_cf
    temp_scaling_factor = temp_scaling_factor.fillna(0)
    temp_scaling_factor.replace(np.inf, 0, inplace=True)
    temp_scaling_factor = temp_scaling_factor.transpose().reset_index().rename(columns={'index':'h'})
    temp_scaling_factor = pd.merge(
        left=pd.DataFrame(hdtmap['h']), right=temp_scaling_factor,
        on='h', how='left').set_index('h')
    distpv_profiles *= temp_scaling_factor
    distpv_profiles = distpv_profiles.clip(upper=1.0) # Capacity factor must be < 1
    distpv_cols = distpv_profiles.columns.tolist()
    distpv_cols.sort()
    distpv_profiles = distpv_profiles[distpv_cols]
    distpv_cols_rename = ['distpv_' + col for col in distpv_cols]
    distpv_profiles.columns = distpv_cols_rename
    distpv_profiles = distpv_profiles.reset_index(drop=True)

    # Resetting indices before merging to assure there are no issues in the merge
    recf.reset_index(drop=True, inplace=True)
    recf = pd.merge(
        left=recf, right=distpv_profiles,
        left_index=True, right_index=True, copy=False)

    # Filtering out profiles of resources not included in this run
    # and sorting to match the order of the rows in resources
    resources = resources[
        resources['area'].isin(rfeas_cap)
    ].sort_values(['resource','area'])
    recf = recf.reindex(labels=resources['resource'].drop_duplicates(), axis=1, copy=False)

    ### Scale up dupv and distpv by 1/(1-distloss)
    recf.loc[
        :, resources.loc[resources.tech.isin(vre_dist),'resource'].values
    ] /= (1 - distloss)

    # Set the column names for resources to match ReEDS-2.0
    resources['ccreg'] = resources.area.map(r2ccreg)
    resources.rename(columns={'area':'r','tech':'i'}, inplace=True)
    resources = resources[['r','i','ccreg','resource']]

    ### Create CSP resource label for each CSP type (labeled by "tech" as csp1, csp2, etc)
    csptechs = [f'csp{c}' for c in GSw_CSP_Types]
    csp_resources = pd.concat({
        tech:
        pd.DataFrame({
            'resource': cspcf.columns,
            'r': cspcf.columns.map(lambda x: x.split('_')[1]),
            'class': cspcf.columns.map(lambda x: x.split('_')[0])})
        for tech in csptechs
    }, axis=0, names=('tech',)).reset_index(level='tech')

    csp_resources = (
        csp_resources
        .assign(i=csp_resources['tech'] + '_' + csp_resources['class'].astype(str))
        .assign(resource=csp_resources['tech'] + '_' + csp_resources['resource'])
        .assign(ccreg=csp_resources.r.map(r2ccreg))
        .loc[csp_resources.r.isin(rfeas_cap)]
        [['i','r','resource','ccreg']]
    )

    ###### Simulate CSP dispatch for each design
    ### Get solar multiples
    sms = {tech: scalars[f'csp_sm_{tech.strip("csp")}'] for tech in csptechs}
    ### Get storage durations
    storage_duration = pd.read_csv(
        os.path.join(inputs_case,'storage_duration.csv'), header=None, index_col=0, squeeze=True)
    ## All CSP resource classes have the same duration for a given tech, so just take the first one
    durations = {tech: storage_duration[f'csp{tech.strip("csp")}_1'] for tech in csptechs}
    ### Run the dispatch simulation for modeled regions
    keep = [c for c in cspcf if c.split('_')[1] in rfeas_cap]
    csp_system_cf = pd.concat({
        tech: csp_dispatch(cspcf[keep], sm=sms[tech], storage_duration=durations[tech])
        for tech in csptechs
    }, axis=1)
    ## Collapse column labels to single strings
    csp_system_cf.columns = ['_'.join(c) for c in csp_system_cf.columns]

    ### Add CSP to RE output dataframes
    recf = pd.concat([recf, csp_system_cf.reset_index(drop=True)], axis=1)
    resources = pd.concat([resources, csp_resources], axis=0)

    #%%### Make thread-to-days key for Osprey
    def get_threaddays(threads=8, numdays=365):
        """
        Evenly apportion days to threads for efficient parallelization
        """
        base = numdays // threads
        remainder = numdays % threads
        threadnumdays = [base+1]*remainder + [base]*(threads-remainder)
        threadnumdays = dict(zip(range(1,threads+1), threadnumdays))

        ends, threadout = {}, {}
        for thread in range(1,threads+1):
            if thread == 1:
                start = 1
            else:
                start = ends[thread-1]+1
            ends[thread] = start + threadnumdays[thread] - 1

            threadout[thread] = 'thread{}.(d{}*d{})'.format(
                thread, start, ends[thread])

        return threadout

    ### Get number of threads used in Augur/Osprey
    threads = int(
        pd.read_csv(
            os.path.join(inputs_case, '..', 'ReEDS_Augur', 'value_defaults.csv'),
            index_col='key')
        .loc['threads','value']
    )
    ### Get number of days used in Augur/Osprey
    numdays = 365 * len(osprey_years.split(','))
    ### Write the threads-to-days file
    threadout = pd.Series(get_threaddays(threads=threads, numdays=numdays))
    threadout.to_csv(
        os.path.join(inputs_case, 'threads.txt'),
        index=False, header=False,
    )

    #%%
    # ------- Dump static data into HDF5 and csv files for future years -------

    load_profiles.astype(np.float32).to_hdf(
        os.path.join(inputs_case,'load.h5'), key='data', complevel=4, index=True)
    recf.astype(np.float16).to_hdf(
        os.path.join(inputs_case,'recf.h5'), key='data', complevel=4, index=True)
    resources.to_csv(os.path.join(inputs_case,'resources.csv'), index=False)

    ### Overwrite the original hierarchy.csv based on capcredit_hierarchy_level
    hierarchy.rename_axis('*r').to_csv(
        os.path.join(inputs_case, 'hierarchy.csv'), index=True, header=True)
    pd.Series(hierarchy.ccreg.unique()).to_csv(
        os.path.join(inputs_case,'ccreg.csv'), index=False, header=False)


#%% PROCEDURE ###
if __name__ == '__main__':
    #%% direct print and errors to log file
    import sys
    sys.stdout = open('gamslog.txt', 'a')
    sys.stderr = open('gamslog.txt', 'a')
    # Time the operation of this script
    from ticker import toc
    import datetime
    tic = datetime.datetime.now()

    ### Mandatory arguments
    parser = argparse.ArgumentParser(description='Create run-specific pickle files for capacity value')
    parser.add_argument('basedir', type=str, help='Base directory for all batch runs')
    parser.add_argument('inputs_case', help='path to inputs_case directory')

    args = parser.parse_args()
    basedir = args.basedir
    inputs_case = args.inputs_case

    ### Run it
    print('Starting LDC_prep.py', flush=True)
    hourly_prep(basedir, inputs_case)

    toc(tic=tic, year=0, process='input_processing/LDC_prep.py',
        path=os.path.join(inputs_case,'..'))
    print('Finished LDC_prep.py', flush=True)
