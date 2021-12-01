#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

The purpose of this script is to collect 8760 data as it is output by
hourlize and perform clustering to produce load and capacity factor 
parameters that will be read by ReEDS. The other outputs are the
hours/seasons to be modeled in ReEDS and linking sets used in the model.

The full set of outputs is at the very end of the file

As a note, this script can also adjust time zones for ReEDS inputs. This
assumes that the outputs from hourlize are in 'local' time - implying
inputs will need to be shifted such that the sun doesn't rise everywhere
at the same time.

"""

# !
# ! This file requires the runs/[my case]/inputs_case/distPVCF_hourly.csv file
# ! which is copied over to inputs_case in the first few commands of a_writedata.gms
# !

# direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')

import pandas as pd
from pandas import DataFrame
import math

from sklearn.preprocessing import normalize
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestCentroid
import matplotlib
#avoids need to have tkinter installed when loading pyplot
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys
import argparse
import os
from scipy.cluster.vq import vq

import os
import argparse


# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()


def collect_regions(pset,rs):
    rs = list(rs[rs["r"].isin(pset)]["rs"])

    r_subset = pset.copy()
    for x in rs:
        r_subset.append(x)
    
    return r_subset

###################################
# -- Capacity Factor Processing --
###################################

def convert_input(basedir, file_name, regions, GSw_HourlyClusterMultiYear):
    # import csv file
    data_input = pd.read_csv(
        os.path.join(basedir,"inputs","variability","multi_year",file_name+".csv.gz") )
    #drop columns that we'll replace/re-create later...
    #required with csv.gz updates with main merge in May, 2021
    dropcols = ['Unnamed: 0','hour']
    data_input.drop(dropcols, axis=1, errors='ignore', inplace=True)

    years = range(2007,2014)

    # Add year column: 
    years = DataFrame([ y for x in years for y in (x,)*8760 ])
    years.columns = ['year']
    data_input = pd.concat([years,data_input], axis=1)
    
    if GSw_HourlyClusterMultiYear == 0:
        data_input = data_input[data_input['year']==2012]

    # fill any missing value with zero
    data_input = data_input.fillna(0).reset_index(drop=True)
    
    # replace h to start at 1 instead of 0
    hour = DataFrame(list(range(1,8761))*int(len(data_input.index)/8760))
    hour[hour.columns[0]] = 'h' + hour[hour.columns[0]].astype(str)
    data_input = data_input.assign(h=hour[0])
    
    # add prefix to column name and remove siting access label
    file_name_tech = file_name.replace('-reference','')
    file_name_tech = file_name_tech.replace('-limited','')
    file_name_tech = file_name_tech.replace('-open','')
    data_input = data_input.add_prefix(file_name_tech+".")
    
    # change year and h column names
    replace_col = ['year','h']
    for i in replace_col:
        coltemp = file_name_tech+"."+i
        if coltemp in data_input.columns:
            data_input = data_input.rename(columns={coltemp:i})
    

    # melt into long format 
    data_input = pd.melt(data_input, id_vars=['year','h'])
    
    # round nubmer
    data_input = data_input.round({'value': 4})
    
    # split string 
    tech_name = data_input["variable"].str.rsplit("_", expand=True)
    
    # replace string
    tech_name[0] = tech_name[0].str.replace('.', '_', regex=True)
    
    # assign column name
    tech_name.columns =['i', 'r'] 

    # combine into a single dataframe
    result = pd.concat([tech_name, data_input.loc[:, ["year","h", "value"]] ], axis=1)
    
    return result


def make_ref_season(idx,period_length,inputs_case):
    '''
    Create referencing table that has columns ['hour','month','season'].
    This is useful to merge with load data and m_cf data to find seasonal 
    average later.
    
    arg: 
    idx: 365x1 ndarray of daily cluster identities
    period_length: 24 for day, 168 for week
    inputs_case: inputs_case directory of ReEDS run
    
    return: pandas dataframe
    '''
    df_day = [y for x in range(1,366) for y in (x,)*24]

    df_id  =  list(range(1,8761,1))
    
    df_season = [ x for x in idx.season for i in range(24)]
                
    # add hours h01:h24
    df_hour  =  list(range(1,25,1))*365
    df_hour  =  [str(item).zfill(2) for item in df_hour]
    
    # add hours h01:h168 column
    hourly_week  =  list(range(1,169,1))*52 + list(range(1,25,1))
    
    if period_length==24:
        hourly_week  =  df_hour
        
    # add morning, afternoon, evening, postmidnight (just for plotting comparison with h17)
    period_section = (
        ['overnight']*6 + ["morning"]*7 + ["afternoon"]*4 + ["evening"]*5 + ['overnight']*2
    ) * 365

    hourly_week  =  [str(item).zfill(3) for item in hourly_week]

    # merge data set
    df = pd.concat([DataFrame(df_day), DataFrame(df_id), DataFrame(df_season),
                    DataFrame(df_hour), DataFrame(period_section), DataFrame(hourly_week)],
                   axis=1)
    
    # rename columns
    df.columns = ['day', 'hour', 'season', 'daily_hour', 'period', 'hr_week']
    
    # update the hour values to add prefix "h"
    df['hour'] = "h" + df['hour'].astype(str)

    return df


def make_equal_periods(GSw_HourlyNumClusters,period_length):
    '''
    Create referencing table that has columns ['hour','daily_hour,'season'].
    This is useful to merge with load data and m_cf data to find seasonal 
    average later when using the equal_periods method to divide up the year
    into `GSw_HourlyNumClusters` seasons of equal duration.
    
    arg: 
    GSw_HourlyNumClusters: number of periods to divide 365 days into
    period_length: 24 for day, 168 for week
    
    return: pandas dataframe
    '''
    df_day = [y for x in range(1,366) for y in (x,)*24]

    df_id  =  list(range(1,8761,1))
    
    df_season = []
    remainder = 365 % GSw_HourlyNumClusters
    for this_clust in range(1,GSw_HourlyNumClusters + 1): 
        # distribute one extra day to each cluster until any remainder's gone
        if remainder > 0:
            days_in_this_period = math.floor(365/GSw_HourlyNumClusters) + 1
            remainder -= 1
        else:
            days_in_this_period = math.floor(365/GSw_HourlyNumClusters)
        df_season = df_season + ['szn' + str(this_clust)] * days_in_this_period * 24

    # roll months to center clusters on midnight Jan. 1 (such that when
    # GSw_HourlyNumClusters == 4, szn1 reflects winter) if season is odd number of days,
    # have to have one more day on one side of the year than the other
    if sum([ 1 for x in df_season if x == 'szn1' ])/24 % 2 > 0:
        df_season = np.roll(df_season,-int(sum([ 1 for x in df_season if x == 'szn1' ])/2 - 12))
    else:
        df_season = np.roll(df_season,-int(sum([ 1 for x in df_season if x == 'szn1' ])/2))

    # add hours h01:h24
    df_hour  =  list(range(1,25,1))*365
    df_hour  =  [str(item).zfill(2) for item in df_hour]
    
    # add morning, afternoon, evening, postmidnight (just for plotting comparison with h17)
    period_section = (
        ['overnight']*6 + ["morning"]*7 + ["afternoon"]*4 + ["evening"]*5 + ['overnight']*2
    ) * 365

    # add hours h01:h168 column
    hourly_week  =  list(range(1,169,1))*52 + list(range(1,25,1))
    
    if period_length==24:
        hourly_week  =  df_hour
    
    hourly_week  =  [str(item).zfill(3) for item in hourly_week]

    # merge data set
    df = pd.concat([DataFrame(df_day), DataFrame(df_id), DataFrame(df_season), 
                    DataFrame(df_hour), DataFrame(period_section), DataFrame(hourly_week)],
                   axis=1)
    
    # rename columns
    df.columns = ['day', 'hour', 'season', 'daily_hour', 'period', 'hr_week']
    
    # update the hour values to add prefix "h"
    df['hour'] = "h" + df['hour'].astype(str)

    return df

def map_new_hour(df,period_length):
    newmap = DataFrame({'season':df.season.unique()})
    newmap["num"] = newmap.index
    df = pd.merge(df,newmap,how='outer',on=['season'])
    df['hour'] = ([int(i.lstrip("0")) for i in df['h_of_day']] + period_length * df['num'])
    df['hour'] = 'h' + df['hour'].astype(str)
    return df


########################   
# -- Load Processing --
########################

def create_load(pset, GSw_HourlyClusterMultiYear):
    load = pd.read_csv(
        os.path.join(basedir,"inputs","variability","multi_year","load.csv.gz") )[pset]
    years = range(2007,2014)

    # Add year column: 
    years = DataFrame([ y for x in years for y in (x,)*8760 ])
    years.columns = ['year']

    hours = DataFrame(list(range(1,8761))*int(len(load.index)/8760))
    hours[hours.columns[0]] = 'h' + hours[hours.columns[0]].astype(str)
    hours.columns = ['hour']
    
    load = pd.concat([years,hours,load], axis=1)
    
    #organize the data for gams to read in as a table with hours in 
    # the first column and regions in the proceeding columns.
    # Here, we keep the "year" column for use in the clustering.
    cols = ['year','hour']
    
    for x in pset:
        cols.append(x)

    #subset load based on GSw_HourlyClusterMultiYear switch
    if GSw_HourlyClusterMultiYear==0:
        load = load[load['year']==2012]
        load = load.reset_index(drop=True)

    load_subset = load[cols]
    
    load_out = pd.melt(load_subset,id_vars=['year','hour'])
    load_out.columns = ['year','hour','region','value']

    return load_out



def create_outputs(cf_representative,load_representative,pset,rs,GSw_HourlyType):
    
    regions = collect_regions(pset,rs)
    
    # make subsets of larger datasets based on 
    cf_representative = cf_representative[cf_representative['region'].isin(regions)].copy()
    load_representative = load_representative[load_representative['region'].isin(pset)]
    
    #need to rename csp set such that it matches with the sets defined
    # in b_inputs - this gets broadcast to all appropriate csp types
    # via the tg_rsc_agg set in b_inputs
    cf_representative["property"] = (
        cf_representative["property"].str.replace("csp","csp1",case=False).values)
    
    

    # if you're not running 8760...
    if int(GSw_HourlyType) < 3:
        
        # representative day specification
        if int(GSw_HourlyType) == 1:
            period_length=24
                    
        # average week specification
        if int(GSw_HourlyType) == 2:
            period_length=168
        
        # TODO: Need to differentiate between cf_representative inputs
        # (when doing representative days) and cf (when doing 8760) here
        cf_representative = cf_representative.rename(
            columns={'region':'r','property':'i','hour':'h'})
        load_representative = load_representative.rename(
            columns={'region':'r','hour':'h'})
        
        cf_all = cf_representative[['i','r','h','value']]
        load = load_representative[['h','r','value']]
    
    return cf_all, load      

def make_8760_map(period_length,idx):
    #create the reference season
    df_ref_season = make_ref_season(idx,period_length,inputs_case)
    df_ref_season['cat'] = df_ref_season['period'] + '_' + df_ref_season['season']

    k = DataFrame(range(1,period_length+1,1))
    mapset = DataFrame()
    #hacky way to avoid passing GSw_HourlyNumClusters through several functions
    for i in ['szn' + str(x) for x in range(1,len(idx['season'].unique())+1)]:
        k['szn'] = str(i)
        mapset = mapset.append(k)
    mapset = mapset.reset_index(drop=True)
    mapset.columns = ['h_real','szn']
    mapset['h_day'] = mapset['h_real']
    mapset['h_real'] = mapset.index + 1
    mapset['h_day'] = 'h' + mapset['h_day'].astype(str)
    mapset['h_real'] = 'h' + mapset['h_real'].astype(str)
    mapset['match'] = mapset['szn'] + '_' + mapset['h_day']
    df_ref_season['match'] = (
        df_ref_season['season'] + '_h'
        + (df_ref_season['daily_hour'].astype(int)).astype(str))
    df_match = df_ref_season[['hour','season','match']]
    mapset_match = mapset[['h_real','szn','match']]
    mapset_match.columns = ['h_real','season','match']
    map_fin = pd.merge(df_match,mapset_match)[['h_real','hour','season']]
    map_fin.columns = ['h','h_8760','season']                
    map_fin['h_8760'] = map_fin['h_8760'].str.replace('h', '').astype(int)
    
    #loop over possible weather years in Augur to create full potential mapping
    #note it is 2007-2013 but python stops one short
    map_out = DataFrame()
    for i in list(range(2007,2014)):
        map_temp = map_fin.copy()
        map_temp['year'] = i
        map_temp['h_8760'] = map_temp['h_8760'] + (8760 * (i-2007))
        map_out = pd.concat([map_out,map_temp])
    
    #make format match what's expected in augur..
    map_out = map_out[['h','season','year','h_8760']]
    map_out.columns = ['h','season','year','hour']
        
    return map_out, map_fin

def duplicate_r_rs(df,map):
    dfm = pd.merge(map,df,on="r",how="left")
    #!!!! missing maps for some regions in eastern canada
    dfm[pd.isnull(dfm['tz'])]['tz'] = 'ET'
    #drop the 'r' columns and rename 'rs' to 'r'
    dfm = dfm.drop('r',axis=1)
    dfm = dfm.rename(columns={'rs':'r'})
    #stack the original and now-rs dataframes
    df_out = pd.concat([df,dfm])
    
    return df_out
    

###########################
#    -- Clustering --     #
###########################


def cluster_profiles(select_year, cf, load, GSw_HourlyClusterAlgorithm,
                     GSw_HourlyCenterType, GSw_HourlyNumClusters, GSw_HourlyIncludePeak,
                     inputs_case, GSw_HourlyClusterRE, make_plots):
    """
    Cluster the load and (optionally) RE profiles to find representative days for dispatch in ReEDS.
    
    The clustering is configured to consider all regions at an hourly resolution, even if some
    regions are represented at an hourly resolution after this function.
    
    Returns:
        cf_representative - hourly profile of centroid or medoid capacity factor values
                            for all regions and technologies
        load_representative - hourly profile of centroid or medoid load values for all regions
        idx_representative - day indices of each cluster center
    """
    #declarations for those that differ in name from function arguments    
    #cf = cf_full 
    #load = load_full 
    profiles = load.copy()
    profiles['property'] = 'load'

    #! need to check on necessity of following line - certain python package version will 
    #! have 'hour' and 'value' columns swapped in the creation of cf_full..
    #! not sure why so applying patch for certainty here
    cf = cf.rename(columns={'h':'hour','i':'property','r':'region'})
    if pd.api.types.is_string_dtype(cf['value']) and pd.api.types.is_numeric_dtype(cf['hour']):
        cf = cf.rename(columns={'hour':'value','value':'hour'})

    resource = cf.copy()

    if GSw_HourlyClusterRE==1:
        ## keep only BA-level averages to reduce size of clustering problem:
        # resource = resource[resource['region'].str.startswith('p')]
        #average CFs across classes by tech to reduce size of clustering problem:
        resource['property'] = resource['property'].str.split(pat='_',expand=True)[0]
        resource = resource.groupby(['property','region','year','hour'],as_index=False).mean()
        profiles = pd.concat([profiles,resource],axis=0)

    #map hours of year to days of year
    h_to_yday = DataFrame({'yday': [ y for x in range(1,366) for y in (x,)*24 ]})
    h_to_yday['hour'] = ['h'] + (h_to_yday.index+1).astype('str')

    h_of_day  =  list(range(1,25,1))*365
    h_of_day  =  DataFrame({'h_of_day':[str(item).zfill(2) for item in h_of_day]})
    
    h_map = pd.concat([h_to_yday,h_of_day],axis=1)
    profiles = pd.merge(profiles,h_map,on='hour',how='left')
    
    #format wide (with hours of day in columns) for clustering
    profiles_long = profiles.copy()
    profiles = profiles.pivot_table(
        index=['year','yday'], columns=['property','region','h_of_day'])['value']
    #normalize each feature rather than each sample
    profiles_scaled = pd.DataFrame(normalize(profiles, axis=0))

    #grab the peak day (defined as the day where the peak nationally coincident load hour occurs)
    # for use in multiple time selection methods:
    peak_day = profiles_long[
        (profiles_long['year']==select_year) & (profiles_long['property']=='load')
    ].groupby(['year','yday','hour']).sum().idxmax()[0][1]  

    # TODO: Explore slightly different normalization methods to improve clustering, 
    # such as dividing every column by the max value in the column instead to maximize
    # the range of each variable.--MI
    #
    # Scale all columns for load to give load as much weight in the clustering
    # as all RE profiles combined
    if GSw_HourlyClusterRE==1:
        # get scaling factor to give load and resource each 50% weight
        # in the clustering after feature magnitudes are normalized
        scaling_factor = (
            len(profiles_long[profiles_long['property']!='load'])
            / len(profiles_long[profiles_long['property']=='load']))
        load_cols = profiles.columns.get_loc('load')
        profiles_scaled.loc[:,load_cols] = profiles_scaled.loc[:,load_cols] * scaling_factor

    #run the clustering
    #output of each method is day_szn (mapping from day to szn) and medoid_idx (indices of
    # medoid days for each szn) along with other variables for plotting
    
    if GSw_HourlyClusterAlgorithm == 'equal_periods':
        print("Performing equal_periods clustering..\n")
        if GSw_HourlyIncludePeak==1:
            df_season_periods = make_equal_periods(GSw_HourlyNumClusters - 1,24)
            day_szn = df_season_periods[['day','season']].drop_duplicates().reset_index(drop=True)
            #add one to other szns
            day_szn['season'] = day_szn['season'].str.replace('szn', '', regex=True).astype(int) + 1
            #recall peak_day is zero-indexed and thus need to reduce by one here
            # area to check on most-correct usage given previous implementation of:
            # day_szn.loc[peak_day,'season'] = 1 
            day_szn.loc[day_szn.day==peak_day-1,'season'] = 1 # set peak period to season 1
            day_szn['season'] = 'szn' + day_szn['season'].astype(str)
            df_season_periods = pd.merge(
                df_season_periods.drop('season',axis=1),
                day_szn,
                how='left',on='day')
        else: 
            df_season_periods = make_equal_periods(GSw_HourlyNumClusters,24)
            day_szn = df_season_periods[['day','season']].drop_duplicates().reset_index(drop=True)

        

        #avg day
        period_profiles = pd.merge(profiles_long,df_season_periods,on='hour')
        centroids_allyrs = period_profiles.groupby(
            ['property','region','season','h_of_day'], as_index=False).mean()
        centroids_allyrs = centroids_allyrs.pivot_table(
            index=['season'], columns=['property','region','h_of_day'])['value']

        #need select year profiles for plotting:
        centroid_profiles = period_profiles[
            period_profiles['year']==select_year
        ].groupby(['property','region','season','h_of_day'],as_index=False).mean()
        centroid_profiles = centroid_profiles.pivot_table(
            index=['season'], columns=['property','region','h_of_day'])['value']

        #get medoids where we grab actual days from the ReEDS year that are closest to the
        # ALL-YEARS centroids (if the peak day is included as a cluster,
        # it's already been defined as the centroid)
        # vector quantization to find medoids
        medoid_idx, _ = vq(centroids_allyrs,profiles.loc[select_year])
        #TODO: create medoid_profiles or just select medoid days by indexing into profiles
        # with medoid_idx in the plots below. same with centroid_profiles, really

    elif GSw_HourlyClusterAlgorithm == 'hierarchical':
        print("Performing hierarchical clustering..\n")
        # #plot a dendrogram
        # import scipy.cluster.hierarchy as shc
        # plt.figure(figsize=(10,7))
        # plt.title("Dendrogram of Time Clusters")
        # dend = shc.dendrogram(shc.linkage(profiles_scaled, method='ward'))
        # plt.gcf().set_facecolor('white')
        # plt.gcf().set_size_inches(12,9)
        # plt.gcf().savefig(os.path.join('out','dendrogram.png'))
        # plt.show()

        #run the clustering and get centroids based on all years of data input
        clusters = AgglomerativeClustering(
            n_clusters=GSw_HourlyNumClusters, affinity='euclidean', linkage='ward')
        idx = clusters.fit_predict(profiles_scaled)
        centroid_find = NearestCentroid()
        centroid_find.fit(profiles,idx)
        centroids = centroid_find.centroids_
        # insert the np array into df for easy indexing
        centroids_allyrs = profiles.loc[select_year][0:GSw_HourlyNumClusters].copy()
        centroids_allyrs[:] = centroids

        #if we're using the peak load day for one of our clusters, reclassify the clusters
        # including the peak day as a centroid and then redo the clustering
        # without the clusters included in the peak cluster.
        if GSw_HourlyIncludePeak==1:
            #replace the centroid containing the highest load hour with the actual peak day
            cluster_w_highest_load = (
                centroids_allyrs.load.groupby('h_of_day',axis=1).sum()
                .max(axis=1).reset_index()[0].idxmax())
            centroids_w_peak = centroids_allyrs.copy()
            centroids_w_peak.iloc[cluster_w_highest_load,:] = profiles.loc[select_year].xs(peak_day)
            
            # reclassify clusters including peak day as the centroid of the cluster
            # with the highest load
            centroid_find.fit(centroids_w_peak,list(range(0,GSw_HourlyNumClusters)))
            idx_w_peak = centroid_find.predict(profiles)

            #improve the representation of other periods by reclustering
            # having excluded the peak cluster we manually created above
            clusters = AgglomerativeClustering(
                n_clusters=GSw_HourlyNumClusters - 1, affinity='euclidean', linkage='ward')
            idx_off_peak = clusters.fit_predict(profiles_scaled[idx_w_peak!=cluster_w_highest_load])
            centroid_find.fit(profiles[idx_w_peak!=cluster_w_highest_load],idx_off_peak)
            centroids_allyrs_off_peak = centroid_find.centroids_

            #sort all but the peak cluster (which will be cluster zero)
            # from highest to lowest daily total energy (using centroids)
            # insert the np array into df for easy indexing
            centroids_allyrs_off_peak_df = (
                profiles.loc[select_year]
                [0:GSw_HourlyNumClusters-1]
            ).copy()
            centroids_allyrs_off_peak_df[:] = centroids_allyrs_off_peak
            cluster_order_off_peak = (
                centroids_allyrs_off_peak_df.load
                .sum(axis=1).rank(ascending=False))
            #keep 1-indexing from rank() output to make room for peak cluster (index zero)
            cluster_order_off_peak = (
                cluster_order_off_peak.to_frame()
                .reset_index().drop(['yday'],axis=1))
            cluster_order_off_peak[0] = cluster_order_off_peak[0].astype('int')
            idx_off_peak_sorted = np.copy(idx_off_peak)
            for k, v in cluster_order_off_peak.to_dict()[0].items():
                idx_off_peak_sorted[idx_off_peak==k] = v
            idx[idx_w_peak!=cluster_w_highest_load] = idx_off_peak_sorted
            idx[idx_w_peak==cluster_w_highest_load] = 0
            #invert the mapping to get original indices in rank order
            cluster_order_off_peak['newindex'] = cluster_order_off_peak.index
            cluster_order_off_peak = cluster_order_off_peak.sort_values([0]).reset_index(drop=True)
            #reorder centroids
            centroids_allyrs_off_peak = centroids_allyrs_off_peak[
                (cluster_order_off_peak['newindex']).to_numpy(),:]

            #put the peak day cluster and other clusters together
            #peak day is now cluster 0
            centroids_allyrs = np.insert(
                centroids_allyrs_off_peak, 0,
                profiles.loc[select_year].xs(peak_day),
                axis=0)

        else:
            # only need to sort all clusters from highest to lowest daily total energy
            # (using centroids)
            cluster_order = centroids_allyrs.load.sum(axis = 1).rank(ascending=False)
            cluster_order = cluster_order.to_frame().reset_index().drop(['yday'],axis=1)
            # reset from one-indexing of rank() to zero-indexing of clusters
            cluster_order[0] = cluster_order[0].astype('int') - 1
            idx_sorted = np.copy(idx)
            for k, v in cluster_order.to_dict()[0].items(): idx_sorted[idx==k] = v
            idx = idx_sorted

            #invert the mapping to get original indices in rank order
            cluster_order['newindex'] = cluster_order.index
            cluster_order = cluster_order.sort_values([0]).reset_index(drop=True)
            #reorder centroids
            centroids_allyrs = centroids_allyrs.to_numpy()[(cluster_order['newindex']).to_numpy(),:]

        #get load centroids using only the year ReEDS will use for profiles.
        idx_reedsyr = [ idx[j] for j in range(len(idx)) if profiles.iloc[j].name[0] == select_year ]
        idx_reedsyr = np.array(idx_reedsyr)
        centroid_find.fit(profiles.loc[select_year],idx_reedsyr)
        centroids = centroid_find.centroids_
        centroid_profiles = profiles.loc[select_year][0:GSw_HourlyNumClusters].copy()
        centroid_profiles[:] = centroids #now yday index has no significance 
        
        #override the centroid of the peak cluster with the actual peak day
        if GSw_HourlyIncludePeak==1: 
            centroid_profiles.iloc[0] = profiles.loc[select_year].xs(peak_day)
            
        # get medoids where we grab actual days from the ReEDS year that are closest to
        # the ALL-YEARS centroids (if the peak day is included as a cluster,
        # it's already been defined as the centroid)
        # vector quantization to find medoids
        closest, _ = vq(centroids_allyrs,profiles.loc[select_year])
        medoid_profiles = profiles.loc[select_year].iloc[closest]
        #indices of medoids, for use in creating representative day profiles in other functions
        medoid_idx = closest

        # create day_szn, a dataframe with columns day and szn (szn1,szn2,etc.),
        # both one-indexed, for export
        day_szn = DataFrame({'day':range(1,366),'season':idx_reedsyr})
        day_szn['season'] = 'szn' + (day_szn['season'] + 1).astype(str)
        # We're done! We want idx, idx_reedsyr, centroid_profiles, medoid_profiles, and medoid_idx.

    elif GSw_HourlyClusterAlgorithm == 'kmeans':
        # centroids, idx = kmeans2(
        #     profiles_scaled.to_numpy(dtype='float32'),
        #     k=GSw_HourlyNumClusters, iter=5, minit='random')
        raise Exception(
            "The k-means GSw_HourlyClusterAlgorithm is not currently implemented as a choice "
            "for selecting representative days.")
        # TODO: implement as above to get idx, idx_reedsyr, day_szn, centroid_profiles,
        # and medoid_profiles.

    else: 
        raise Exception(
            """'equal_periods', 'hierarchical', and 'kmeans' are the only accepted arguments
            for the `GSw_HourlyClusterAlgorithm` argument
            to specify how to select representative days.""")
    
    # medoid_idx starts off as a vector and needs to become a dataframe with a season columns
    # as its index. this is true for both the equal_periods and hierarchical algorithms
    medoid_idx = DataFrame({'yday':medoid_idx})
    medoid_idx['season'] = medoid_idx.index


    #create cluster center profiles for export
    if GSw_HourlyCenterType == 'medoid':
        print("Creating medoid clusters..\n")
        load_representative = profiles_long[
            (profiles_long['year']==select_year)
            & (profiles_long['property']=='load')
            & (profiles_long['yday'].isin(medoid_idx['yday']))
        ]
        load_representative = pd.merge(load_representative,medoid_idx,on='yday',how='left')
        load_representative = map_new_hour(load_representative,24)
        load_representative = load_representative.drop(
            ['h_of_day','property','year','yday','season'],axis=1)
        #we need to construct the center days from the original cf_full
        cf_representative = pd.merge(cf[cf['year']==select_year],h_map,on='hour',how='left')
        cf_representative = cf_representative[cf_representative['yday'].isin(medoid_idx.yday)]
        cf_representative = pd.merge(cf_representative,medoid_idx,on='yday',how='left')
        cf_representative = map_new_hour(cf_representative,24)
        cf_representative = cf_representative.drop(['h_of_day','year','yday','season'],axis=1)
    elif GSw_HourlyCenterType == 'centroid':
        print("Creating centroid clusters..\n")
        load_representative = pd.merge(
            profiles_long[
                (profiles_long['year']==select_year) & (profiles_long['property']=='load')],
            day_szn,
            left_on='yday', right_on='day',
        ).drop(['yday','day'],axis=1)
        load_representative = load_representative.groupby(
            ['region','h_of_day','season'],
            as_index=False).mean()
        load_representative = map_new_hour(load_representative,24)
        load_representative = load_representative.drop(['h_of_day','year','season'],axis=1)

        #we need to construct the center days from the original cf_full
        cf_representative = pd.merge(cf[cf['year']==select_year],h_map,on='hour',how='left')
        cf_representative = pd.merge(
            cf_representative,
            day_szn,
            left_on='yday', right_on='day'
        ).drop(['yday','day'], axis=1)
        cf_representative = cf_representative.groupby(
            ['property','region','h_of_day','season'],
            as_index=False).mean()
        cf_representative = map_new_hour(cf_representative,24)
        cf_representative = cf_representative.drop(['h_of_day','year','season'],axis=1)
    else: 
        raise Exception(
            """Either 'centroid' or 'medoid' must be provided for the
            `GSw_HourlyCenterType` argument to specify how to construct representative days.""")

    #save daily cluster designations to csv


    if make_plots==1:
        #define colors for plotting
        #TODO: generalize this for any GSw_HourlyNumClusters
        alpha = .05
        col_dict = {0: [1,   0,  0, alpha], 
                    1: [0,   0,  1, alpha], 
                    2: [0, .28,  0, alpha], 
                    3: [1,  .5, .0, alpha],
                    4: [1,   0,  1, alpha],
                    5: [1,  .7, .9, alpha],
                    6: [.7, .5,  0, alpha], 
                    7: [.6, .9, .1, alpha], 
                    8: [.7, .3, .7, alpha], 
                    9: [.2, .5, .2, alpha]}

        #set up the old quarterly season mapping for comparison
        df_season_quarterly = make_equal_periods(4,24)
        #avg day:
        quarterly_profiles = pd.merge(profiles_long,df_season_quarterly,on='hour')
        quarterly_avg_centroids = quarterly_profiles[
            quarterly_profiles['year']==select_year
        ].groupby(['property','region','season','h_of_day'], as_index=False).mean()
        quarterly_avg_centroids = quarterly_avg_centroids.pivot_table(
            index=['year','season'], columns=['property','region','h_of_day'])['value']
        
        #h17:
        quarterly_h17_centroids = quarterly_profiles[
            quarterly_profiles['year']==select_year
        ].groupby(['property','region','season','period'],as_index=False).mean()
        quarterly_h17_centroids = pd.merge(
            quarterly_profiles, quarterly_h17_centroids,
            on=['property','region','season','period'])
        quarterly_h17_profiles = quarterly_h17_centroids[
            ['year_x','region','value_y','hour','season','property','yday_x','h_of_day']]
        quarterly_h17_profiles.columns = [
            'year','region','value','hour','season','property','yday','h_of_day']
        
        quarterly_h17_centroids = quarterly_h17_profiles[
            ['year','region','value','season','property','h_of_day']].drop_duplicates()
        quarterly_h17_centroids = quarterly_h17_centroids.pivot_table(
            index=['year','season'], columns=['property','region','h_of_day'])['value']
        # TODO: grab top 40 hours for h17 mapping

        ## PLOT ALL DAYS ON SAME X AXIS:
        plt.ioff() #turn off interactive mode
        plt.style.use('default')
        leg_h = []
        leg_l = []
        for day in range(profiles.shape[0]): # range(365):
            this_profile = (
                profiles.load.iloc[day].reset_index()
                .groupby('h_of_day').sum().reset_index()
                .drop('h_of_day',axis=1)
            )
            p = plt.plot(this_profile/1e3, color=col_dict[idx[day]])
        #add centroids and medoids to the plot:
        for i in range(GSw_HourlyNumClusters):
            # Centroids:
            p = plt.plot(
                centroid_profiles.iloc[i].groupby('h_of_day').sum()/1e3,
                color=col_dict[i][0:3] + [1], linewidth=2)
            leg_l += ['%s (%d days): %s centroid' % (
                      'szn' + str(i+1), sum(idx_reedsyr == i), select_year)]
            leg_h += p
        #medoids
        for i in range(GSw_HourlyNumClusters):
            p = plt.plot(
                medoid_profiles.iloc[i].groupby('h_of_day').sum()/1e3,
                '--', color=col_dict[i][0:3] + [1], linewidth=2)
            leg_l += ['%s: %s medoid' % ('szn' + str(i+1), select_year)]
            leg_h += p
        # -- Comparison with quarterly season centroids and h17 --
        #quarterly season centroids
        linetype = ['-','--','-.',':']
        for i in range(0,len(df_season_quarterly.season.unique())):
            p = plt.plot(
                quarterly_avg_centroids.load.xs(
                    df_season_quarterly.season.unique()[i],level='season'
                ).iloc[0].groupby('h_of_day').sum()/1e3,
                linetype[i], color='black', linewidth=2)
            leg_l += ['Quarterly Seasons: %s %s avg.' % (
                      select_year, df_season_quarterly.season.unique()[i])]
            leg_h += p
        #h17
        linetype = ['-','--','-.',':']
        for i in range(0,len(df_season_quarterly.season.unique())):
            p = plt.plot(
                quarterly_h17_centroids.load.xs(
                    df_season_quarterly.season.unique()[i],level='season'
                ).iloc[0].groupby('h_of_day').sum()/1e3,
                linetype[i], color='magenta', linewidth=2)
            leg_l += ['h17: %s %s avg.' % (select_year, df_season_quarterly.season.unique()[i])]
            leg_h += p
        #h17
        plt.legend(leg_h, leg_l)
        plt.gca().set_xlabel('Hour')
        plt.gca().set_ylabel('Conterminous US Load (GW)')
        plt.gca().set_title(
            'Cluster Comparison (All Days in {} Shown)'.format('2007–2013'
            if len(profiles.index.unique(level='year')) > 1 else '2012' ))
        plt.gcf().set_size_inches(12,9)
        plt.gcf().savefig(os.path.join(inputs_case,'day_comparison_all.png'))

        ## PLOT LOAD FOR THE ENTIRE ReEDS YEAR COLORED BY CLUSTER AND MEDOID:
        plt.figure()
        plotted = [False for i in range(GSw_HourlyNumClusters)]
        leg_h = []
        leg_l = []
        nationwide_reedsyr_load = profiles_long[
            (profiles_long['year']==select_year) & (profiles_long['property']=='load')
        ].groupby(['year','yday','hour'],as_index=False).sum()
        nationwide_reedsyr_load['hour_numeric'] = pd.to_numeric(
            nationwide_reedsyr_load['hour'].str.lstrip('h'))
        nationwide_reedsyr_load.sort_values(['year','hour_numeric'],inplace=True)
        for this_yday in range(1,366): # plus one to get one-indexed yday
            p = plt.plot(
                nationwide_reedsyr_load.loc[
                    nationwide_reedsyr_load['yday'] == this_yday,'hour_numeric'].to_numpy(),
                nationwide_reedsyr_load.loc[
                    nationwide_reedsyr_load['yday'] == this_yday,'value'].to_numpy()/1e3,
                '-', color=col_dict[idx_reedsyr[this_yday-1]][0:3] + [0.2])
            if not plotted[idx_reedsyr[this_yday-1]]:
                leg_h += p
                leg_l += ['{} ({} days)'.format(
                    day_szn.loc[day_szn['day']==this_yday,'season'].iloc[0],
                    sum(idx_reedsyr == idx_reedsyr[this_yday-1])
                )]
                p = plt.plot(
                    nationwide_reedsyr_load.loc[
                        nationwide_reedsyr_load['yday'] == medoid_idx.loc[
                            medoid_idx['season']==idx_reedsyr[this_yday-1], 'yday'
                        ].iloc[0], 'hour_numeric'
                    ].to_numpy(),
                    medoid_profiles.iloc[
                        idx_reedsyr[this_yday-1]].groupby('h_of_day').sum().to_numpy()/1e3,
                    color=col_dict[idx_reedsyr[this_yday-1]][0:3] + [1], linewidth=2)
                leg_h += p
                leg_l += ['%s Medoid' % day_szn.loc[day_szn['day']==this_yday,'season'].iloc[0]]
                plotted[idx_reedsyr[this_yday-1]] = True
        plt.legend(leg_h[::-1], leg_l[::-1])
        plt.gca().set_ylabel('Conterminous US Load (GW)')
        plt.gca().set_title('Cluster and Medoid Definitions')
        plt.gcf().set_facecolor('white')
        plt.gcf().set_size_inches(15,9)
        plt.gcf().savefig(os.path.join(inputs_case,'year_clusters.png'))

        ## PLOT LDCs:
        # for prop in medoid_profiles.
        plt.figure()
        weights = [ sum(idx_reedsyr == x) for x in range(GSw_HourlyNumClusters) ]
        medoid_sums = medoid_profiles.groupby('h_of_day',axis=1).sum()
        medoid_ldc = np.repeat(np.array(medoid_sums),np.array(weights),axis=0)
        
        centroid_sums = centroid_profiles.groupby('h_of_day',axis=1).sum()
        centroid_ldc = np.repeat(np.array(centroid_sums),np.array(weights),axis=0)
        
        quarterly_avg_sums = quarterly_avg_centroids.groupby('h_of_day',axis=1).sum()
        quarterly_avg_ldc = np.repeat(
            np.array(quarterly_avg_sums),
            np.array([92, 91, 91, 91]),
            axis=0)
        
        quarterly_h17_sums = quarterly_avg_centroids.groupby('h_of_day',axis=1).sum()
        quarterly_h17_ldc = np.repeat(
            np.array(quarterly_h17_sums),
            np.array([92, 91, 91, 91]),
            axis=0)
        #TODO: Account for top 40 hours being used for h17. Currently the above is just h16.
        
        p = plt.plot(
            np.sort(nationwide_reedsyr_load['value'])[::-1]/1e3,
            color='black', linewidth=2)
        leg_h = p
        leg_l = ['2012 Actual']
        p = plt.plot(sorted(medoid_ldc.flatten()/1e3)[::-1], color='red', linewidth=2)
        leg_h += p
        leg_l += ['2012 Medoids']
        p = plt.plot(sorted(centroid_ldc.flatten()/1e3)[::-1], color='blue', linewidth=2)
        leg_h += p
        leg_l += ['2012 Centroids']
        p = plt.plot(sorted(quarterly_avg_ldc.flatten()/1e3)[::-1], color='magenta', linewidth=2)
        leg_h += p
        leg_l += ['Quarterly Season Average Days']
        p = plt.plot(sorted(quarterly_h17_ldc.flatten()/1e3)[::-1], color='green', linewidth=2)
        leg_h += p
        leg_l += ['h17']
        
        # TODO: add LDC for all weather years condensed into an 8760 for comparison.
        # Hopefully the medoids will do well.
        plt.gcf().set_facecolor('white')
        plt.legend(leg_h[::-1], leg_l[::-1])
        plt.gca().set_ylabel('Conterminous US Load (GW)')
        plt.gca().set_xlabel('Hours of %s' % select_year)
        plt.gca().set_title('LDC Validation')
        plt.gcf().set_facecolor('white')
        plt.gcf().set_size_inches(12,7)
        plt.gcf().savefig(os.path.join(inputs_case,'LDC_all.png'))

        # TODO: add a few LDCs for state-averaged load and VRE CF profiles. Superimpose on US map.

    return cf_representative, load_representative, day_szn

def window_overlap(n_day,n_window,n_ovlp):
    #test arguments
    #n_day = 4
    #n_window = 6
    #n_ovlp = 2
    print(
        "Creating hour groups for the minloading constraint with {} clusters, "
        "{} window length, and {} overlapping timeslices \n".format(n_day, n_window, n_ovlp))
    ## create a list of full window
    list_24h = np.arange(1,24+1).tolist()
    list_output = []

    ## create a list consisting of first element of each expected window
    # gap between first elements of each window
    n_gap = n_window - n_ovlp 

    # list of first elements
    list_1st = []  
    k = 1
    while k  <= 24:
        list_1st.append(k)
        k = k + n_gap

    ## list all element in a window 
    for i in list_1st:
        list_window = []

        for j in range(i, i + n_window ):      
            a_element = list_24h[(j % len(list_24h))-1]
            list_window.append(a_element)

        list_output.append(list_window)   
        full_list = np.array(list_output)

    ## scale up to multiple day
    for d in range(1, n_day ):
        one_output = (np.array(list_output) + 24*d)
        full_list = np.concatenate((full_list, one_output) )

    ###--- Formatting Exporting File ---###    
    # convert to pandas dataframe    
    full_list = pd.DataFrame(full_list)

    # add h and comma for all column but last list
    for m in range(0, full_list.shape[1] -1 ):
        full_list[m] = full_list[m].map('h{},'.format)

    # add h and comma for last column
    full_list[full_list.shape[1]-1] = full_list[full_list.shape[1]-1].map('h{}'.format)   

    #formatting for gams readability
    left_bracket = ["("] * len(full_list)
    right_bracket = [")"] * len(full_list)
    dots = ["."] * len(full_list)
    full_list.insert(0,"dot",dots)
    full_list.insert(1,"left",left_bracket)
    full_list.insert(full_list.shape[1],"right",right_bracket)

    list_days = pd.DataFrame(np.arange(1,full_list.shape[0]+1))
    final_output = pd.concat([list_days,full_list,full_list],axis=1)
    return final_output




###########################
#    -- End Functions --  #
###########################



#------------------------------------------------------------------------------------------------
    


if __name__ == '__main__':
    # -- Argument Block --
    parser = argparse.ArgumentParser(
        description="Create the necessary 8760 and capacity factor data for hourly resolution")
    parser.add_argument("-i", "--basedir",
                        help="basedir as passed from a_writedata")
    parser.add_argument("-o", "--inputs_case",
                        help="casedir/inputs_case as passed from a_writedata")
    parser.add_argument("-f", "--GSw_HourlyType", type=int, default=1,
                        help="Output resolution. 1=day, 2=week, 3=8760")
    parser.add_argument("-tz","--GSw_HourlyTZAdj", type=int, default=1,
                        help="GSw_HourlyTZAdj, bool flag to adjust all timezones to EST")
    parser.add_argument("-tz_mid_nt", "--GSw_HourlyTZAdj_MidNight", type=int, default=1,
                        help="bool flag to adjust all timezones to EST")
    parser.add_argument("-y","--select_year", type=int, default=2012,
                        help="year ReEDS will get all load and resource profiles from")
    # Clustering arguments
    parser.add_argument("-a", "--GSw_HourlyClusterAlgorithm", default='hierarchical',
                        choices=['equal_periods','hierarchical','kmeans','random'],
                        help="Algorithm to use for clustering")
    parser.add_argument("-my", "--GSw_HourlyClusterMultiYear", type=int, default=0,
                        help=("bool to run clustering on all weather years "
                              "where True=use 2007-2013 data, False=only select_year"))
    parser.add_argument("-re", "--GSw_HourlyClusterRE", type=int, default=1,
                        help="bool to consider RE capacity factors in the clustering")
    parser.add_argument("-c", "--GSw_HourlyNumClusters", type=int, default=4,
                        help="Number of clusters to create (i.e. number of representative days)")
    parser.add_argument("-ct", "--GSw_HourlyCenterType", default='medoid',
                        help="""'medoid' or 'centroid'""")
    parser.add_argument("-p", "--GSw_HourlyIncludePeak", type=int, default=1,
                        help='Force one of the clusters to have the peak day as its centroid?')
    parser.add_argument("-mp", "--make_plots", type=int, default=0,
                        help='Make plots or not!')
    parser.add_argument("-w", "--GSw_HourlyWindow", type=int, default=0,
                        help=('Number of timeslices in each window for '
                              'minloading nexth consideration'))
    parser.add_argument("-ol", "--GSw_HourlyOverlap", type=int, default=0,
                        help='Overlap of timeslices from one window to the next')
    parser.add_argument("-pv", "--GSw_SitingUPV", type=str, default="reference",
                        help='Overlap of timeslices from one window to the next')
    parser.add_argument("-wndons","--GSw_SitingWindOns", type=str, default="reference",
                        help='Overlap of timeslices from one window to the next')
    parser.add_argument("-wndofs","--GSw_SitingWindOfs", type=str, default="reference",
                        help='Overlap of timeslices from one window to the next')
    
    args = parser.parse_args()
    basedir = args.basedir
    inputs_case = args.inputs_case
    GSw_HourlyType = args.GSw_HourlyType
    GSw_HourlyTZAdj = args.GSw_HourlyTZAdj
    GSw_HourlyTZAdj_MidNight = args.GSw_HourlyTZAdj_MidNight
    GSw_HourlyClusterMultiYear = args.GSw_HourlyClusterMultiYear
    GSw_HourlyClusterRE = args.GSw_HourlyClusterRE
    select_year = args.select_year
    GSw_HourlyClusterAlgorithm = args.GSw_HourlyClusterAlgorithm
    GSw_HourlyNumClusters = args.GSw_HourlyNumClusters
    GSw_HourlyCenterType = args.GSw_HourlyCenterType
    GSw_HourlyIncludePeak = args.GSw_HourlyIncludePeak
    make_plots = args.make_plots
    GSw_HourlyWindow = args.GSw_HourlyWindow
    GSw_HourlyOverlap = args.GSw_HourlyOverlap
    GSw_SitingUPV = args.GSw_SitingUPV
    GSw_SitingWindOns = args.GSw_SitingWindOns
    GSw_SitingWindOfs = args.GSw_SitingWindOfs
    
    
    # #test arguments
# =============================================================================
###
    
    # #arguments for time clustering:
    # basedir = os.path.expanduser('~/github/ReEDS-2.0/')
    # inputs_case = os.path.join(basedir,'runs','v20210624_flexM0_ercot_seq','inputs_case','')
    # GSw_HourlyType = 1
    # GSw_HourlyTZAdj = 1
    # GSw_HourlyTZAdj_MidNight = 0
    # GSw_HourlyClusterMultiYear = 0
    # GSw_HourlyClusterRE = 1
    # select_year = 2012
    # GSw_HourlyClusterAlgorithm = 'equal_periods'
    # GSw_HourlyNumClusters = 4
    # GSw_HourlyCenterType = 'centroid'
    # GSw_HourlyIncludePeak = 1
    # make_plots = 0
    # GSw_HourlyWindow = 8
    # GSw_HourlyOverlap = 2
    # GSw_SitingUPV = 'reference'
    # GSw_SitingWindOns = 'reference'
    # GSw_SitingWindOfs = 'reference'
# 

# =============================================================================
    # gather relevant regions for capacity regions
    rs = pd.read_csv(os.path.join(basedir,"inputs","rsmap_sreg.csv"))
    rs = rs.rename(columns={'*r':'r'})

    #hardcoding modeled regions...
    pset = ['p{}'.format(i+1) for i in range(134)]
    pset_non0 = pset
    regions_non0 = collect_regions(pset_non0,rs)


    # -- 8760 data processing -- #

    # first need to gather all the data for 8760 for all regions that will be
    # non-17-timeslice resolution
    # note appending arguments passed in for site selection of pv/wind-ons/wind-ofs
    cf_file_lists = [
        "csp","dupv",
        "upv-"+GSw_SitingUPV,
        "wind-ons-"+GSw_SitingWindOns,
        "wind-ofs-"+GSw_SitingWindOfs,
    ]
    #,"upv-reference","wind-ofs-reference","wind-ons-reference"]
    #cf_file_lists.append["upv-"+GSw_SitingUPV]
    cf_full = DataFrame()

    print("\nCollecting 8760 capacity factor data..")

    for file_list in cf_file_lists:
        #temp here is a dataframe that gets appended to the final set
        temp = convert_input(basedir,file_list,regions_non0,GSw_HourlyClusterMultiYear)
        cf_full = cf_full.append(temp)
        print('finished converting resource data for: {}'.format(file_list))

    # Note: we don't have dGen results for 2007-2013, so multi-year clustering
    # can't include distPV. We'll just always exclude distPV from the clustering.
    print("\nAppending 8760 distPV capacity factors from: "
          + os.path.join(inputs_case,"distPVCF_hourly.csv"))
    distpv0 = pd.read_csv(os.path.join(inputs_case,"distPVCF_hourly.csv"))
    distpv0.rename( columns={'Unnamed: 0':'r'}, inplace=True )
    distpv = pd.melt(distpv0,id_vars=['r'])
    distpv['h'] = 'h' + distpv['variable'].astype('str')
    distpv['i'] = 'distPV'
    distpv['year'] = select_year
    cf_full = cf_full.append(distpv[['i','r','year','h','value']])
    
    print("\nCollecting 8760 load data..")
    load_full = create_load(pset_non0,GSw_HourlyClusterMultiYear)


    # -- Time Zone Adjustment -- #

    if int(GSw_HourlyTZAdj)==1:
        print("\nBased on Sw_HourlyTZAdj, adjusting time zones for 8760 capacity factor and load..")
        #basic steps: 
        # map timezone to ba
        # map cf and load data to tz
        # map new hour based on tz
        # remove original hour and new columns
        #same file used in Augur
        tz_ba_map = pd.read_csv(os.path.join(inputs_case,"reeds_ba_tz_map.csv"))
        #basic mapping file from original data to new tz-specific hour for each TZ
        allh = ['h' + str(i) for i in range(1,8761)]
        tz_8760_map = pd.DataFrame({'h':allh,'ET':allh,'CT':allh,'MT':allh,'PT':allh})
        tz_8760_map['CT'] = np.roll(tz_8760_map['CT'],-1)
        tz_8760_map['MT'] = np.roll(tz_8760_map['MT'],-2)
        tz_8760_map['PT'] = np.roll(tz_8760_map['PT'],-3)

        #need to map hours to supply regions as well
        r_rs = pd.read_csv(os.path.join(basedir,"inputs","rsmap_sreg.csv"))
        r_rs = r_rs.rename(columns={'*r':'r'})
        
        tz_ba = duplicate_r_rs(tz_ba_map,r_rs).reset_index().drop('index',axis=1)
        
        tz_fullm = pd.melt(tz_8760_map,id_vars=['h'])
        tz_fullm = tz_fullm.rename(columns={'variable':'tz'})
        tz_fullm = tz_fullm.rename(columns={'value':'h_out'})

        #make a full map of all r and h with corresponding shifted hour, h_out
        tz_ba_fullm = pd.merge(tz_ba,tz_fullm,on=['tz'],how='left').drop('tz',axis=1)

        #map regions tz-correct hour as a new columns
        cf_newhour = pd.merge(cf_full,tz_ba_fullm,on=['r','h'],how='left')
        load_newhour = pd.merge(
            load_full.rename(columns={'region':'r','hour':'h'}),
            tz_ba_fullm,
            on=['r','h'], how='left')
        
        #drop the old hour column and rename h_out appropriately
        load_full = load_newhour.drop('h',axis=1).rename(columns={'h_out':'hour','r':'region'})
        cf_full = cf_newhour.drop('h',axis=1).rename(columns={'h_out':'h'})        

    # -- Creation of 8760 average CF for wind technologies -- #
            
    # create a copy of cf_full with just wind techs then take the mean by i/r combinations   
    windcf_annavg = cf_full[
        (cf_full['i'].str[:4]=='wind') & (cf_full['year']==select_year)
    ].groupby(['i','r']).mean().reset_index()
    #need to round to avoid too long value errors in GAMS
    windcf_annavg['value'] = round(windcf_annavg['value'],7)
    # drop year column since we're only reporting for the year ReEDS uses
    # for load and resource profiles
    windcf_annavg = windcf_annavg.drop('year',axis=1)


    #
    # -- Clustering to determine representative days to model in ReEDS
    # (only for pset1 currently --may develop representative week clustering) -- #
    #
    
    print("\n \nBeginning clustering of capacity factors and load..\n")
    sys.stdout.flush()
    #identify clusters mapping 8760 to some number of periods based on input arguments:
    cf_representative, load_representative, idx_representative = cluster_profiles(
        select_year, cf_full, load_full, GSw_HourlyClusterAlgorithm, GSw_HourlyCenterType, 
        GSw_HourlyNumClusters, GSw_HourlyIncludePeak, inputs_case, GSw_HourlyClusterRE, make_plots)

    print("\nClustering complete.\n")

    # -- Averaging or aggregating based on pset assignments -- #

    #capacity factor outputs
    cf_out = DataFrame()
    #load outputs
    load_out = DataFrame()
    #8760 mapping for Augur
    map_8760 = DataFrame()


    if int(GSw_HourlyType)==1:
        print("\nProcessing capacity factor and load for representative day regions...")
        cf_out, load_out  = create_outputs(cf_representative,load_representative,pset,rs,1)
        map_8760, map_single = make_8760_map(24,idx_representative)

    if int(GSw_HourlyType)==2:
        print("\nProcessing capacity factor and load for average week regions...")
        cf_out, load_out  = create_outputs(
            cf_full[cf_full['year']==select_year],
            load_full[load_full['year']==select_year],
            pset, rs, 2)
        map_8760, map_single = make_8760_map(24,idx_representative)
        
    if GSw_HourlyType == 3:
        print("\nProcessing capacity factor and load for 8760 representation...")
        cf_out, load_out = create_outputs(cf_full,load_full,pset,rs,3)

        #a bit hacky here - making the 8760 map but
        #then just replace h_modeled column with the 8760 column
        map_8760, map_single = make_8760_map(24,idx_representative)
        map_out = DataFrame()
        for i in list(range(2007,2014)):
            map_temp = map_single.copy()
            map_temp['year'] = i
            map_temp['h'] = 'h' + map_temp['h_8760'].astype('str')
            map_temp['h_8760'] = map_temp['h_8760'] + (8760 * (i-2007))
            map_out = pd.concat([map_out,map_temp])
        #make format match what's expected in augur..
        map_out = map_out[['h','season','year','h_8760']]
        map_out.columns = ['h','season','year','hour']
        map_8760 = map_out.copy()

    #calculate number of hours represented based on map_single
    hours = map_single.copy()
    hours['dummy'] = 1
    hours = hours[['h','dummy']]
    hours = hours.groupby('h').sum().reset_index()

    #create an h_szn mapping..
    h_szn = map_single.copy()
    h_szn = h_szn[['h','season']].drop_duplicates().reset_index(drop=True)
    #grab minimum and maximum h by szn from h_szn
    #duplicate for all BAs
    #if sw_Hourlytzadj == 1:
    #    get the ba-to-tz mapping csv file
    #    designate the necessary shift for each BA based on its
    #    [roll those hours by necessary shift indicated by regions' timezones]

    #create a szn set to adjust the 'szn' set in b_inputs.gms
    sznset = DataFrame({'szn':[ 'szn' + str(x) for x in range(1,GSw_HourlyNumClusters+1) ]})

    #create an hours set to adjust the 'h' set in b_inputs.gms
    hset = map_single.copy()
    hset = hset[['h']].drop_duplicates().reset_index()
    hset = hset[['h']]

    #need to have the proper ordering for augur to interpret the h_dt_szn
    map_8760 = map_8760.sort_values(by=['hour'])
        
    # -- Net trade with Canada --

    #load in canadian 8760 data
    print("\nLoading in 8760 Canadian net trade from: "
          + os.path.join(inputs_case,"can_trade_8760.csv")) 
    can_8760 = pd.read_csv(os.path.join(inputs_case,"can_trade_8760.csv"))
    can_8760 = can_8760.rename(columns={'h':'hour'})

    print("\nMapping 8760 Canadian data to modeled hours,"
          "filling in missing permutations then averaging")
    can_8760['hour'] = can_8760['hour'].str.replace('h', '').astype('int')
    can_out = pd.merge(can_8760,map_8760,how='left',on=['hour'])
    can_out['net'] = can_out['net'].fillna(0)
    can_out = can_out.dropna()
    can_out['t'] = can_out['t'].astype('int')
    can_out = can_out[['r','h','t','net']]
    can_out = can_out.rename(columns={'net':'Val'})
    #note that we can sum here and avoid creating all permutations of r/h_8760/t
    can_out = can_out.groupby(['r','h','t']).sum().reset_index()

    # -- Seasonal peak demand hours for PRM constraint --
    map_single_h8760 = map_single.copy()
    map_single_h8760['hour'] = 'h' + map_single_h8760['h_8760'].astype(str)
    peak_dem_hourly_load = pd.merge(
        load_full[
            load_full['year']==select_year
        ].drop(['year'],axis=1).groupby(['hour','region'],as_index=False).sum(),
        map_single_h8760[['season','hour']],
        on='hour',
    ).drop(['hour'],axis=1)
    peak_dem_hourly_load = peak_dem_hourly_load.groupby(['region','season'],as_index=False).max()

    # -- Representative day peak demand hour linkage set for ndhydro PRM constraint --
    h_szn_prm = pd.merge(load_out.groupby(['h'],as_index=False).sum(),h_szn,on='h')
    peak_demand_idx = h_szn_prm.groupby(['season'],as_index=False).idxmax()
    h_szn_prm = h_szn_prm.iloc[peak_demand_idx['value']]
    h_szn_prm = h_szn_prm[['h','season']]

    # -- Quarterly (spri, summ, fall, wint) season weights for setting parameters
    # according to traditional seasons --
    quarters = make_equal_periods(4,24)[['hour','season']]
    quartermap = DataFrame({'season':['szn1','szn2','szn3','szn4'],
                            'quarter':['wint','spri','summ','fall']})
    quarters = pd.merge(quarters,quartermap,on='season')
    quarters = quarters.rename(columns={'hour':'h_8760'})
    quarters = quarters[['h_8760','quarter']]
    frac_h_quarter_weights = map_single.copy()
    frac_h_quarter_weights['h_8760'] = 'h' + frac_h_quarter_weights['h_8760'].astype(str)
    frac_h_quarter_weights = pd.merge(frac_h_quarter_weights,quarters,on='h_8760')
    
    #count the number of days in each szn that are part of each quarter
    #to category so that .count() includes zero counts
    frac_h_quarter_weights['quarter'] = frac_h_quarter_weights['quarter'].astype('category')
    frac_h_quarter_weights = frac_h_quarter_weights.groupby(
        ['h','quarter'], as_index=False
    ).count().drop(['h_8760'],axis=1)
    frac_h_quarter_weights = frac_h_quarter_weights.rename(columns={'season':'weight'})
    frac_h_quarter_weights['weight'] = frac_h_quarter_weights['weight'].fillna(0)
    #grab total length in days of each szn for denominator
    frac_h_quarter_weights = pd.merge(frac_h_quarter_weights,hours,on='h')
    frac_h_quarter_weights['weight'] = (
        frac_h_quarter_weights['weight'] / frac_h_quarter_weights['dummy'])
    frac_h_quarter_weights = frac_h_quarter_weights[['h','quarter','weight']]

    # -- Output writing -- #    

    # =============================================================================
    # Hour, Region, and Timezone Mapping
    # =============================================================================
    
    # Load in Data
    data_tz = pd.read_csv(inputs_case + 'reeds_ba_tz_map.csv')

    # =============================================================================
    # Starting Hours
    # =============================================================================

    # will need to be updated for different temporal lengths (e.g. week/8760)
    day = 1
    total_hours = 24 * day * GSw_HourlyNumClusters
    factor = np.arange(0,total_hours,24)
    szn = np.arange(1,day*GSw_HourlyNumClusters+1,1)

    if GSw_HourlyTZAdj_MidNight == 1:
        ##--- Shifting Time Zone ---##
        ET = factor + 1
        CT = factor + 2
        MT = factor + 3
        PT = factor + 4
        
        starting_hours = {'season': szn,'PT': PT , 'MT': MT, 'CT': CT, 'ET': ET }
        starting_hours = pd.DataFrame(data=starting_hours)
        
    else:
        ##--- Not Shifting Time Zone ---##
        ET = factor + 1
        
        starting_hours = {'season': szn,'PT': ET , 'MT': ET, 'CT': ET, 'ET': ET }
        starting_hours = pd.DataFrame(data=starting_hours)
        
    # add h in front of cell value
    starting_hours['season'] = starting_hours['season'].map('szn{}'.format)
    starting_hours['ET'] = starting_hours['ET'].map('h{}'.format)
    starting_hours['CT'] = starting_hours['CT'].map('h{}'.format)
    starting_hours['MT'] = starting_hours['MT'].map('h{}'.format)
    starting_hours['PT'] = starting_hours['PT'].map('h{}'.format)
    
    # melt into long format
    starting_hours = pd.melt(
        starting_hours,
        id_vars=['season'], value_vars=["PT", "MT", "CT", "ET"],
        var_name='tz', value_name='val')
    
    # merging dataframe
    tz_rgn_start_h = pd.merge(data_tz, starting_hours, how="inner", on=["tz"])
    tz_rgn_start_h = tz_rgn_start_h.drop(columns=['tz'])

    # =============================================================================
    # Ending Hours
    # =============================================================================
    if GSw_HourlyTZAdj_MidNight == 1:
    
        ##--- Shifting Time Zone ---##
        ET = factor + 24
        CT = factor + 1
        MT = factor + 2
        PT = factor + 3
        
        ending_hours = {'season': szn,'PT': PT , 'MT': MT, 'CT': CT, 'ET': ET }
        ending_hours = pd.DataFrame(data=ending_hours)
    
       
    else:
        ##--- Not Shifting Time Zone ---##
        ET = factor + 24
        
        ending_hours = {'season': szn,'PT': ET , 'MT': ET, 'CT': ET, 'ET': ET }
        ending_hours = pd.DataFrame(data=ending_hours)
     
    
    # add h in front of cell value
    ending_hours['season'] = ending_hours['season'].map('szn{}'.format)
    ending_hours['ET'] = ending_hours['ET'].map('h{}'.format)
    ending_hours['CT'] = ending_hours['CT'].map('h{}'.format)
    ending_hours['MT'] = ending_hours['MT'].map('h{}'.format)
    ending_hours['PT'] = ending_hours['PT'].map('h{}'.format)
    
    # melt into long format
    ending_hours = pd.melt(
        ending_hours,
        id_vars=['season'], value_vars=["PT", "MT", "CT", "ET"],
        var_name='tz', value_name='val')
    
    # merging dataframe
    tz_rgn_end_h = pd.merge(data_tz, ending_hours, how="inner", on=["tz"])
    tz_rgn_end_h = tz_rgn_end_h.drop(columns=['tz'])

    hour_group = window_overlap(GSw_HourlyNumClusters,GSw_HourlyWindow,GSw_HourlyOverlap)

    print("\n\nWriting data CSVs: \n")
    # no rhyme or reason but sometimes the following print statement for load writing
    # can come before the writing data CSVs line.. therefore putting extraneous
    # empty print line to make sure output to terminal looks normal
    print("")
    print("  Load for all regions as: "
          + os.path.join(inputs_case,"load_hourly.csv\n"))
    load_out.to_csv(os.path.join(inputs_case,"load_hourly.csv"),header=False,index=False)

    print("  Capacity factors as: "
          + os.path.join(inputs_case,"cf_hourly.csv\n"))
    cf_out.to_csv(os.path.join(inputs_case,"cf_hourly.csv"),header=False,index=False)

    print("  Static Canadian trade as: "
          + os.path.join(inputs_case,"can_hourly.csv\n"))
    can_out.to_csv(os.path.join(inputs_case,"can_hourly.csv"),header=False,index=False)

    print("  Season-peak demand hour for each szn's representative day as: "
          + os.path.join(inputs_case,"h_szn_prm_hourly.csv\n"))
    h_szn_prm.to_csv(os.path.join(inputs_case,"h_szn_prm_hourly.csv"),header=False,index=False)

    print("  Peak demand for each season as: "
          + os.path.join(inputs_case,"peak_dem_hourly_load.csv\n"))
    peak_dem_hourly_load.to_csv(os.path.join(
        inputs_case,"peak_dem_hourly_load.csv"),header=False,index=False)

    print("  Wind capacity factor annual average values as: "
          + os.path.join(inputs_case,"hourly_windcf_annavg.csv\n"))
    windcf_annavg.to_csv(
        os.path.join(inputs_case,"hourly_windcf_annavg.csv"),header=False,index=False)

    print("  8760 hour linkage set for Augur as: " + os.path.join(inputs_case,"h_dt_szn.csv\n"))
    map_8760.to_csv(os.path.join(inputs_case,"h_dt_szn.csv"),index=False)

    print("  Writing number of hours represented by each timeslice as: "
          + os.path.join(inputs_case,"hours_hourly.csv\n"))
    hours.to_csv(os.path.join(inputs_case,"hours_hourly.csv"),index=False,header=False)

    print("  Writing hours to season mapping as: "
          + os.path.join(inputs_case,"h_szn_hourly.csv\n"))
    h_szn.to_csv(os.path.join(inputs_case,"h_szn_hourly.csv"),index=False,header=False)
        
    print("  Writing h set for subsetting allh as: "
          + os.path.join(inputs_case,"hset_hourly.csv\n"))
    hset.to_csv(os.path.join(inputs_case,"hset_hourly.csv"),index=False,header=False)              

    print("  Writing szn set for subsetting allszn as: "
          + os.path.join(inputs_case,"sznset_hourly.csv\n"))
    sznset.to_csv(os.path.join(inputs_case,"sznset_hourly.csv"),index=False,header=False)

    print("  Writing quarterly season weights for assigning summer/winter dependent parameters: "
          + os.path.join(inputs_case,"frac_h_quarter_weights_hourly.csv\n"))
    frac_h_quarter_weights.to_csv(
        os.path.join(inputs_case,"frac_h_quarter_weights_hourly.csv"),index=False,header=False)
    
    print("  Writing day to season mapping for Osprey as: "
          + os.path.join(inputs_case,"d_szn.csv\n"))
    idx_representative['day'] = 'd' + idx_representative['day'].astype(str)
    #changing column names 
    idx_representative.columns = ['*day','szn']
    idx_representative.to_csv(
        os.path.join(inputs_case,"d_szn.csv"),index=False,header=True)
    
    print("  Writing tz-specific starting timeslices as: "
          + os.path.join(inputs_case + 'tz_rgn_start_h.csv\n'))
    tz_rgn_start_h.to_csv(
        os.path.join(inputs_case, 'tz_rgn_start_h.csv'), index=False, header=False)

    print("  Writing tz-specific final timeslices as: "
          + os.path.join(inputs_case + 'tz_rgn_end_h.csv\n'))
    tz_rgn_end_h.to_csv(
        os.path.join(inputs_case, 'tz_rgn_end_h.csv'), index=False, header=False)

    print("  Writing minload hour windows with overlap as: "
          + os.path.join(inputs_case + 'hour_group.txt'))
    hour_group.to_csv(
        os.path.join(inputs_case + 'hour_group.txt'), index=False, header=False, sep=' ')

    toc(tic=tic, year=0, process='input_processing/hourly_process.py', 
        path=os.path.join(inputs_case,'..'))
