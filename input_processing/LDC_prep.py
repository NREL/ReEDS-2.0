#%% IMPORTS
import argparse
import os
import pandas as pd
import numpy as np
import h5py
import shutil
#%% direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()

#%% FUNCTIONS ###
def hourly_prep(
        basedir, inputs_case,
        GSw_EFS1_AllYearLoad='default',
        GSw_IndividualSites=1,
        GSw_IndividualSiteAgg=1,
        filepath_individual_sites='//nrelnas01/ReEDS/Supply_Curve_Data/individual_sites/2021',
        GSw_SitingWindOns='reference',
        GSw_SitingWindOfs='reference',
        GSw_SitingUPV='reference',
        osprey_years='2012',
        ldcProfiles='standard',
        GSw_PVB_Types='1',
        GSw_PVB=1,
        capcredit_hierarchy_level='ccreg',
    ):
    # #%% Settings for debugging ###
    # basedir = os.path.expanduser('~/github/ReEDS-2.0')
    # inputs_case = os.path.join(basedir, 'runs', 'v20210527_o7_Z35', 'inputs_case')
    # GSw_EFS1_AllYearLoad = "default"
    # GSw_IndividualSites = 1
    # GSw_IndividualSiteAgg = 2
    # filepath_individual_sites = '//nrelnas01/ReEDS/Supply_Curve_Data/individual_sites/2021'
    # GSw_SitingWindOns = 'reference'
    # GSw_SitingWindOfs = 'reference'
    # GSw_SitingUPV = 'reference'
    # osprey_years = '2012'
    # ldcProfiles = 'standard'
    # GSw_PVB_Types = '1'
    # GSw_PVB = 1
    # capcredit_hierarchy_level = 'ccreg'
    # ################################

    #%%### Inputs
    ### Override GSw_PVB_Types if GSw_PVB is turned off
    GSw_PVB_Types = (
        [int(i) for i in GSw_PVB_Types.split('_')] if int(GSw_PVB)
        else []
    )
    # -------- Define the file paths --------
    if ldcProfiles == 'standard':
        folder = 'multi_year'
    else:
        folder = 'test_profiles'
    path_variability = os.path.join(basedir,'inputs','variability')

    # -------- Datetime mapper --------

    hdtmap = pd.read_csv(os.path.join(inputs_case, 'h_dt_szn.csv'))
    ### Non-default load only has one year of data
    if GSw_EFS1_AllYearLoad != 'default':
        hdtmap_load = hdtmap[hdtmap.year == 2012]
    else:
        hdtmap_load = hdtmap

    precision = np.float16 if GSw_IndividualSites else np.float32

    ###### Load the input parameters
    ### distloss
    distloss = pd.read_csv(
        os.path.join(inputs_case,'scalars_transmission.csv'),
        header=None, usecols=[0,1], index_col=0, squeeze=True)['distloss']

    ### BAs present in the current run
    ### valid_ba_list -> rfeas
    rfeas = sorted(
        pd.read_csv(os.path.join(inputs_case, 'valid_ba_list.csv'))
        .columns.tolist())

    ### Map BAs to wind/CSP resource regions (there are no 'sk' values in rsmap.csv)
    rsmap = pd.read_csv(
        os.path.join(inputs_case,'rsmap.csv')
    ).rename(columns={'*r':'r'}).set_index('r')['rs']
    map_BAtoWINDREG = (
        rsmap.loc[rfeas]
        .reset_index().rename(columns={'r':'ba','rs':'area'})
    )

    ### hierarchy -> r_ccreg -> map_BAtoCCREG
    hierarchy = pd.read_csv(
        os.path.join(inputs_case,'hierarchy.csv'),
        names=['r','nercr','nercr_new','rto','rto_agg','cendiv','st',
               'interconnect','country','customreg','ccreg','usda'],
    )
    ### Overwrite the ccreg column with the desied hierarchy level
    hierarchy.ccreg = hierarchy[capcredit_hierarchy_level].copy()
    hierarchy = hierarchy.set_index('r')

    ## Get the mapper
    map_BAtoCCREG = hierarchy.loc[rfeas]['ccreg'].reset_index().rename(columns={'r':'area'})

    # -------- Get spatial mappers --------

    map_WINDREGtoCCREG = pd.merge(
        left=map_BAtoWINDREG, right=map_BAtoCCREG.rename(columns={'area':'ba'}),
        on='ba', how='left')
    map_WINDREGtoCCREG = map_WINDREGtoCCREG.drop('ba',1).reset_index(drop=True)
    map_AREAtoCCREG = pd.concat([map_BAtoCCREG,map_WINDREGtoCCREG]).reset_index(drop=True)

    # Resource regions present in the current run
    ResReg_true = pd.DataFrame(data={'area': rfeas + map_BAtoWINDREG.area.tolist()})

    # Get technology subsets
    tech_table = pd.read_csv(
        os.path.join(inputs_case,'tech-subset-table.csv')).set_index('Unnamed: 0',1)
    techs = {tech:list() for tech in list(tech_table)}
    for tech in techs.keys():
        techs[tech] = tech_table[tech_table[tech]=='YES'].index.values.tolist()
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

    # Get number of csp configurations
    configs =  int(len(tech_table.query('CSP == "YES" and STORAGE == "YES"')))

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
    if GSw_EFS1_AllYearLoad == "default":
        load_profiles = pd.read_csv(
            os.path.join(path_variability,
                            folder,
                            'load.csv.gz'
                            ),
            index_col=0, float_precision='round_trip')
    else:
        load_profiles = pd.read_csv(
            os.path.join(path_variability,
                            'EFS_Load',
                            (GSw_EFS1_AllYearLoad + '_load_hourly.csv.gz')
                            ),
            index_col=[0,1], float_precision='round_trip')

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
                / aggcapacity).astype(precision).fillna(0)
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
              + ['sk']
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
        df_windons = pd.read_csv(
            os.path.join(path_variability, folder, 
                        'wind-ons-{}.csv.gz'.format(GSw_SitingWindOns)), 
            index_col=0, float_precision='round_trip').astype(precision)
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
        df_windofs = pd.read_csv(
            os.path.join(path_variability, folder,
                        'wind-ofs-{}.csv.gz'.format(GSw_SitingWindOfs)),
            index_col=0, float_precision='round_trip').astype(precision)
        df_windofs.columns = ['wind-ofs_' + col for col in df_windofs]

    df_upv = pd.read_csv(
        os.path.join(path_variability, folder,
                     'upv-{}.csv.gz'.format(GSw_SitingUPV)),
        index_col=0, float_precision='round_trip').astype(precision)
    df_upv.columns = ['upv_' + col for col in df_upv]

    df_dupv = pd.read_csv(
        os.path.join(path_variability, folder, 'dupv.csv.gz'),
        index_col=0, float_precision='round_trip').astype(precision)
    df_dupv.columns = ['dupv_' + col for col in df_dupv]

    cspcf = pd.read_csv(
        os.path.join(path_variability, folder, 'csp.csv.gz'),
        index_col=0, float_precision='round_trip').astype(precision)

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
        df_pvb[pvb_type] = pd.read_csv(
            os.path.join(path_variability, 'multi_year', 
                         '{}-{}.csv.gz'.format(infile, GSw_SitingUPV)),
            index_col=0, float_precision='round_trip').astype(precision)
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

    distPVCF = pd.read_csv(
        os.path.join(inputs_case,'distPVCF.csv')).rename(columns={'Unnamed: 0':'resource'})

    # ------- Performin load modifications -------
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

        regions = list(load_profiles.columns)
        load_profiles['year'] = list(hdtmap_load.year)
        #normalize load profiles with 2010 load timeslices
        for y in load_profiles.year.unique():
            for i in regions:
                load_profiles.loc[load_profiles.year==y,i] = (
                    load_profiles.loc[:,i][load_profiles.year == y]
                    * (load_TS_2010_total.loc[i] / load_profiles.loc[:,i][load_profiles.year == y].sum())
                )

    # Filtering out load profiles not included in this run
    load_profiles = load_profiles[rfeas].copy()

    # Adjusting load profiles by distribution loss factor and load calibration factor
    load_profiles.loc[:,:] = load_profiles.loc[:,:] / (1 - distloss)


    # ------- Performing resource modifications -------

    # Getting all distpv resources and filtering out those not included in this run
    distPV_resources = pd.DataFrame(distPVCF['resource'])
    distPV_resources.loc[:,'tech'] = 'distpv'
    distPV_resources.loc[:,'area'] = distPV_resources.loc[:,'resource']
    distPV_resources.loc[:,'resource'] = (
        distPV_resources.loc[:,'tech'] + '_' + distPV_resources.loc[:,'resource'])

    # Adding distpv resources to resources
    resources = pd.concat([resources,distPV_resources], sort=False, ignore_index=True)


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

    distPVCF.drop('H17', 1, inplace=True)
    distPVCF.set_index('resource', inplace=True)
    distPVCF.columns = ['h' + str(n) for n in range(1, 17)]
    # Create and apply scaling factor for each timeslice
    temp_scaling_factor = distPVCF / distpv_timeslice_cf
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
        left=recf, right=distpv_profiles.astype(np.float32),
        left_index=True, right_index=True, copy=False)

    # Filtering out profiles of resources not included in this run
    # and sorting to match the order of the rows in resources
    resources = resources[
        resources['area'].isin(ResReg_true['area'])
    ].sort_values(['resource','area'])
    recf = recf.reindex(labels=resources['resource'].drop_duplicates(), axis=1, copy=False)

    ### Scale up dupv and distpv by 1/(1-distloss)
    recf.loc[
        :, resources.loc[resources.tech.isin(vre_dist),'resource'].values
    ] /= (1 - distloss)

    # Set the column names for resources to match ReEDS-2.0
    resources = pd.merge(left=resources, right=map_AREAtoCCREG, on='area', how='left')
    resources.rename(columns={'area':'r','tech':'i'}, inplace=True)
    resources = resources[['r','i','ccreg','resource']]

    # Format CSP resources
    csp_resources = pd.DataFrame(columns=['i','r','resource','ccreg'])
    csp_profiles = pd.DataFrame()

    get_csp_resources = pd.DataFrame({
        'resource': cspcf.columns,
        'area': cspcf.columns.map(lambda x: x.split('_')[1]),
        'class': cspcf.columns.map(lambda x: x.split('_')[0]),
    })
    get_csp_resources = pd.merge(left=get_csp_resources, right=map_BAtoWINDREG, on='area')
    get_csp_resources.rename(columns={'area':'r','ba':'area'},inplace=True)
    get_csp_resources = pd.merge(left=get_csp_resources, right=map_BAtoCCREG, on='area').drop('area',1)

    for i in range(0,configs):
        temp_csp_resources = get_csp_resources.copy()
        temp_csp_resources.loc[:,'i'] = 'csp{}_'.format(str(i+1)) + temp_csp_resources.loc[:,'class']
        temp_csp_resources.drop('class',1,inplace=True)
        temp_csp_resources.loc[:,'resource'] = (
            temp_csp_resources.loc[:,'i'] + '_' + temp_csp_resources.loc[:,'r'])
        csp_resources = pd.concat([csp_resources,temp_csp_resources],sort=False).reset_index(drop=True)
        temp_cspcf = cspcf.copy()

        #filter csp columns in csp cf for those that have strings contained in resreg_true
        newcspcols = [col for col in temp_cspcf.columns if col.split('_')[1] in ResReg_true['area'].values]
        temp_cspcf = temp_cspcf[newcspcols]
        temp_cspcf.columns = temp_csp_resources['resource']
        csp_profiles = pd.concat([csp_profiles,temp_cspcf],sort=False, axis=1)

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
    # ------- Dump static data into pickle files for future years -------

    load_profiles.to_pickle(os.path.join(inputs_case,'load.pkl'))
    recf.to_pickle(os.path.join(inputs_case,'recf.pkl'))
    resources.to_csv(os.path.join(inputs_case,'resources.csv'), index=False)
    csp_profiles.to_pickle(os.path.join(inputs_case,'csp_profiles.pkl'))
    csp_resources.to_csv(os.path.join(inputs_case,'csp_resources.csv'), index=False)
    ### Overwrite the original hierarchy.csv based on capcredit_hierarchy_level
    hierarchy.to_csv(os.path.join(inputs_case, 'hierarchy.csv'), header=False)
    pd.Series(hierarchy.ccreg.unique()).to_csv(
        os.path.join(inputs_case,'ccreg.csv'), index=False, header=False)

#%% PROCEDURE ###
if __name__ == '__main__':
    ### Mandatory arguments
    parser = argparse.ArgumentParser(description='Create run-specific pickle files for capacity value')
    parser.add_argument('-i', '--basedir', type=str, help='Base directory for all batch runs')
    parser.add_argument('-o', '--inputs_case', help='path to inputs_case directory')
    parser.add_argument('-l', '--GSw_EFS1_AllYearLoad', type=str, default='default',
                        help='All year load name for EFS or SingleYear')
    parser.add_argument('-x', '--GSw_IndividualSites', type=int, default=1, 
                        choices=[0,1], help='Switch to use individual sites')
    parser.add_argument('-a', '--GSw_IndividualSiteAgg', type=str, default='1',
                        choices=[str(i) for i in range(1,11)] + ['BA'],
                        help='level of aggregation for individual site profiles')
    parser.add_argument('-d', '--filepath_individual_sites', type=str,
                        default='//nrelnas01/ReEDS/Supply_Curve_Data/individual_sites/2021',
                        help='path to directory with hourly profiles for individual sites')
    parser.add_argument('-w', '--GSw_SitingWindOns', type=str, default='reference',
                        choices=['reference','open','limited'],
                        help='siting access scenario for onshore wind')
    parser.add_argument('-f', '--GSw_SitingWindOfs', type=str, default='reference',
                        choices=['reference','open','limited'],
                        help='siting access scenario for offshore wind')
    parser.add_argument('-p', '--GSw_SitingUPV', type=str, default='reference',
                        choices=['reference','open','limited'],
                        help='siting access scenario for UPV')
    parser.add_argument('-y', '--osprey_years', type=str, default='2012',
                        help='Years to include in Osprey hourly dispatch')
    parser.add_argument('-t','--ldcProfiles', type=str, default='standard',
                        help='Load profiles to use')
    parser.add_argument('-v', '--GSw_PVB_Types', type=str, default='1',
                        help='_-delimited pvb_types to include, such as 1 or 1_2')
    parser.add_argument('-b', '--GSw_PVB', type=int, default='1',
                        help='switch to turn on/off hybrid PV+battery (overrides GSw_PVB_Types)')
    parser.add_argument('-r', '--capcredit_hierarchy_level', type=str, default='ccreg',
                        help='level of hierarchy.csv at which to aggregate net load for cap credit')

    args = vars(parser.parse_args())
    inputs_case = args['inputs_case']

    ### Run it
    print('Starting LDC_prep.py', flush=True)
    hourly_prep(**args)

    toc(tic=tic, year=0, process='input_processing/LDC_prep.py',
        path=os.path.join(inputs_case,'..'))
    print('Finished LDC_prep.py', flush=True)
