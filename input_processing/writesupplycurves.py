"""
@author: pbrown
@date: 20201104 14:47
* Adapted from input_processing/R/writesupplycurves.R
* All supply curves are organized by BA

This script gathers supply curve data for on/offshore wind, upv, dupv, csp, hydro, and
psh into a single inputs_case file, rsc_combined.csv. 

This script contains additional procedures for gathering geothermal supply curve data, 
demand response and EV managed charging supply curve data, and spurline supply curve data 
into various separate inputs_case files.

"""

#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import numpy as np
import os
import sys
import datetime
import pandas as pd
import site
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
### Typically this script is run from the version copied to the run folder, but the
### alternative path is included in case it's run from the root of ReEDS during development
try:
    reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..'))
    site.addsitedir(os.path.join(reeds_path))
    from hourlize.resource import get_bin
except ImportError:
    reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
    site.addsitedir(os.path.join(reeds_path))
    from hourlize.resource import get_bin

#%%#################
### FIXED INPUTS ###

### Number of bins used for everything other than wind and PV
numbins_other = 5
### Rounding precision
decimals = 7
### spur_cutoff [$/MW]: Cutoff for spur line costs; clip cost for sites with larger costs
spur_cutoff = 1e7

#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def concat_sc_point_gid(x):
    return x.astype(str).str.cat(sep=',')

def wm(df):
    """Make a function to take the capacity-weighted average in a .groupby() call"""
    def _wm(x):
        return np.average(
            x,
            weights=(
                df.loc[x.index, 'capacity']
                if df.loc[x.index, 'capacity'].sum() > 0
                else 0
            )
        )
    return _wm

def agg_supplycurve(scpath, inputs_case, numbins_tech,
                    agglevel, AggregateRegions, bin_method='equal_cap_cut', 
                    bin_col='supply_curve_cost_per_mw',spur_cutoff=1e7, 
                    agglevel_variables=None, deflate=None,sw=None, write=False):
    """
    """
    ### Get inputs
    dfin = pd.read_csv(scpath)
    # convert supply curve columns (temporary fix until all supply curve files are updated)
    dfin.rename(columns={"trans_adder_per_MW": "trans_adder_per_mw", 
                         "capital_adder_per_MW": "capital_adder_per_mw",
                         "dist_km": "dist_spur_km",
                         "reinforcement_dist_km": "dist_reinforcement_km",
                         }, inplace=True)
    
    # Mixed resolution procedure
    if agglevel_variables['lvl'] == 'mult' :
        dfin_ba = dfin[dfin['region'].isin(agglevel_variables['ba_regions'])]
        dfin_county = dfin[dfin['region'].isin(agglevel_variables['county_regions'])]

        if 'aggreg' in agglevel :
            ### Map to new regions if regional aggregation is larger than BA        
            if int(AggregateRegions):
                ### Get the ba-to-agglevel map
                rb2agglevel = pd.read_csv(os.path.join(inputs_case,'r_ba.csv')).set_index('ba').squeeze()
                rb2agglevel_ba = rb2agglevel[rb2agglevel.index.isin(agglevel_variables['ba_regions'])]
                ### Map old regions to new aggregated regions
                dfin_ba.region = dfin_ba.region.map(rb2agglevel_ba)
        ### Assign bins
        if dfin_ba.empty:
            dfin_ba['bin'] = []
        else:
            dfin_ba = dfin_ba.groupby(['region','class'], sort=False, group_keys=True).apply(
            get_bin, numbins_tech, bin_method, bin_col
            ).reset_index(drop=True).sort_values('sc_point_gid')
        if dfin_county.empty:
            dfin_county['bin'] = []
        else: 
            dfin_county = dfin_county.groupby(['region','class'], sort=False, group_keys=True).apply(
                get_bin, numbins_tech, bin_method, bin_col
            ).reset_index(drop=True).sort_values('sc_point_gid')
        
        ###### Aggregate values by (region,class,bin)
        ### Define the aggregation settings
        cost_adder_cols_ba = [c for c in dfin_ba if c in ['trans_adder_per_mw','capital_adder_per_mw']]
        cost_adder_cols_county = [c for c in dfin_ba if c in ['trans_adder_per_mw','capital_adder_per_mw']]

        ### cost and distance are weighted averages, with capacity as the weighting factor
        aggs = {'capacity': 'sum', 'sc_point_gid': concat_sc_point_gid}
        index_cols = ['region', 'class', 'bin']
        aggs_ba = {
            col: aggs.get(col, wm(dfin_ba)) for col in dfin_ba
            if col not in index_cols
        }
        aggs_county = {
            col: aggs.get(col, wm(dfin_county)) for col in dfin_county
            if col not in index_cols
        }

        ### Aggregate it
        dfout_ba = dfin_ba.groupby(index_cols).agg(aggs_ba)
        ### Clip negative costs and costs above cutoff
        dfout_ba.supply_curve_cost_per_mw = dfout_ba.supply_curve_cost_per_mw.clip(
            lower=0, upper=spur_cutoff)
        
        dfout_county = dfin_county.groupby(index_cols).agg(aggs_county)

        df_write = pd.concat([dfout_ba, dfout_county])
        # Write out the supply curve data for use in hourly_repperiods.py
        if (write) and (AggregateRegions):
            filename = scpath.replace('supply_curve','sc')
            df_write.to_csv(os.path.join(inputs_case,filename), index=True, header=True)
        # Convert dollar year
        if os.path.basename(scpath) == 'csp_supply_curve.csv':
            deflate_scen = 'CSP_supply_curves_cost_2018'
        else:
            deflate_scen = os.path.basename(scpath).replace('.csv','')
           
        cost_adder_cols_ba = [c for c in dfout_ba if c in ['trans_adder_per_mw', 'capital_adder_per_mw']]
        dfout_ba[['supply_curve_cost_per_mw'] + cost_adder_cols_ba] *= deflate[deflate_scen]
        cost_adder_cols_county = [c for c in dfout_county if c in ['trans_adder_per_mw', 'capital_adder_per_mw']]
        dfout_county[['supply_curve_cost_per_mw'] + cost_adder_cols_county] *= deflate[deflate_scen]
        
        # Subtract GSw_TransIntraCost (converted to $/MW) to avoid double-counting
        # but only if not running at county-level (county-level does not include
        # transmission reinforcement costs in the supply curve)
        if os.path.basename(scpath) in [
                'csp_supply_curve.csv', 'geohydro_supply_curve.csv', 'egs_supply_curve.csv',]:     
            for c in ['supply_curve_cost_per_mw']:
                dfout_ba[c] *= deflate[deflate_scen]
                dfout_county[c] *= deflate[deflate_scen]
                dfout_ba[c] = (dfout_ba[c] - float(sw['GSw_TransIntraCost'])*1e3).clip(lower=0)
        
        else:
            for c in ['supply_curve_cost_per_mw', 'trans_adder_per_mw']:
                dfout_ba[c] = (dfout_ba[c] - float(sw['GSw_TransIntraCost'])*1e3).clip(lower=0)
        
        # Combine BA an county data
        dfin = pd.concat([dfin_ba, dfin_county])
        dfin['bin'] = dfin['bin'].astype(int)
        dfout = pd.concat([dfout_ba, dfout_county])


    #Single resolution procedure
    else:    
        ### Map to new regions if regional aggregation is larger than BA
        if agglevel not in ['county','ba']:
            if int(AggregateRegions):
                ### Get the ba-to-agglevel map
                rb2agglevel = pd.read_csv(os.path.join(inputs_case,'r_ba.csv')).set_index('ba').squeeze()
                ### Map old regions to new aggregated regions
                dfin.region = dfin.region.map(rb2agglevel)
        ### Assign bins
        if dfin.empty:
            dfin['bin'] = []
        else: 
            dfin = dfin.groupby(['region','class'], sort=False, group_keys=True).apply(
                get_bin, numbins_tech, bin_method, bin_col
            ).reset_index(drop=True).sort_values('sc_point_gid')
        ###### Aggregate values by (region,class,bin)
        ### Define the aggregation settings
        cost_adder_cols = [c for c in dfin if c in ['trans_adder_per_mw','capital_adder_per_mw']]

        ### cost and distance are weighted averages, with capacity as the weighting factor
        aggs = {'capacity': 'sum', 'sc_point_gid': concat_sc_point_gid}
        index_cols = ['region', 'class', 'bin']
        aggs = {
            col: aggs.get(col, wm(dfin)) for col in dfin
            if col not in index_cols
        }
        ### Aggregate it
        dfout = dfin.groupby(index_cols).agg(aggs)
        ### Clip negative costs and costs above cutoff
        dfout.supply_curve_cost_per_mw = dfout.supply_curve_cost_per_mw.clip(
            lower=0, upper=spur_cutoff)

        # Write out the supply curve data for use in hourly_repperiods.py
        if (write) and (AggregateRegions):
            filename = scpath.replace('supply_curve','sc')
            dfout.to_csv(os.path.join(inputs_case,filename), index=True, header=True)
        # Convert dollar year
        if os.path.basename(scpath) == 'csp_supply_curve.csv':
            deflate_scen = 'CSP_supply_curves_cost_2018'
        else:
            deflate_scen = os.path.basename(scpath).replace('.csv','')           
        cost_adder_cols = [c for c in dfout if c in ['trans_adder_per_mw', 'capital_adder_per_mw']]
        dfout[['supply_curve_cost_per_mw'] + cost_adder_cols] *= deflate[deflate_scen]

        # Subtract GSw_TransIntraCost (converted to $/MW) to avoid double-counting
        # but only if not running at county-level (county-level does not include
        # transmission reinforcement costs in the supply curve)
        if agglevel not in ['county']:
            if (os.path.basename(scpath) == 'csp_supply_curve.csv' or os.path.basename(scpath) == 'geohydro_supply_curve.csv' 
                or os.path.basename(scpath) == 'egs_supply_curve.csv'):
                for c in ['supply_curve_cost_per_mw']:
                    dfout[c] = (dfout[c] - float(sw['GSw_TransIntraCost'])*1e3).clip(lower=0)
            else:
                for c in ['supply_curve_cost_per_mw', 'trans_adder_per_mw']:
                    dfout[c] = (dfout[c] - float(sw['GSw_TransIntraCost'])*1e3).clip(lower=0)
    
        
    return dfin, dfout

#%% ============================================================================
### --- MAIN FUNCTION ---
### ============================================================================

def main(reeds_path,inputs_case,AggregateRegions=1,rsc_wsc_dat=None,write=True,**kwargs):
    print('Starting writesupplycurves.py')

    # #%% Settings for testing
    # reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # inputs_case = os.path.join(reeds_path,'runs','Jul2_test_Western_agg','inputs_case')
    # AggregateRegions=1
    # rsc_wsc_dat=None
    # write=False
    
    #%% Inputs from switches
    sw = reeds.io.get_switches(inputs_case)
    ### Overwrite switches with keyword arguments
    for kw, arg in kwargs.items():
        sw[kw] = arg
    endyear = int(sw.endyear)
    startyear = int(sw.startyear)
    geohydrosupplycurve = sw.geohydrosupplycurve
    egssupplycurve = sw.egssupplycurve
    egsnearfieldsupplycurve = sw.egsnearfieldsupplycurve
    pshsupplycurve = sw.pshsupplycurve
    numbins = {'upv':int(sw.numbins_upv), 
                'wind-ons':int(sw.numbins_windons), 
                'wind-ofs':int(sw.numbins_windofs), 
                'csp':int(sw.numbins_csp),
                'geohydro':int(sw.numbins_geohydro_allkm),
                'egs': int(sw.numbins_egs_allkm)} 

    # Use agglevel_variables function to obtain spatial resolution variables 
    agglevel_variables  = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)
    agglevel = agglevel_variables['agglevel']

    val_r_all = pd.read_csv(
        os.path.join(inputs_case,'val_r_all.csv'), header=None).squeeze(1).tolist()
    # Read in tech-subset-table.csv to determine number of csp configurations
    tech_subset_table = pd.read_csv(os.path.join(inputs_case, "tech-subset-table.csv"))
    csp_configs = tech_subset_table.loc[
        (tech_subset_table.CSP== 'YES' ) & (tech_subset_table.STORAGE == 'YES')].shape[0]

    # Read in dollar year conversions for RSC data
    dollaryear = pd.read_csv(os.path.join(inputs_case,'dollaryear_sc.csv'))
    deflator = pd.read_csv(os.path.join(inputs_case,"deflator.csv"))
    deflator.columns = ["Dollar.Year","Deflator"]
    deflate = dollaryear.merge(deflator,on="Dollar.Year",how="left").set_index('Scenario')['Deflator']

    #%% Load the existing RSC capacity (PV plants, wind, and CSP) if not provided in main function call
    if rsc_wsc_dat is None:
        # writesupplycurves.py is being run as a main input processing script
        rsc_wsc = pd.read_csv(os.path.join(inputs_case,'rsc_wsc.csv'))
    else:
        # writesupplycurves.py is being passed rsc_wsc data from an aggregate_regions.py call
        rsc_wsc = rsc_wsc_dat.copy()

    for j,row in rsc_wsc.iterrows():
        # Group CSP tech
        if row['i'] in ['csp-ws']:
            rsc_wsc.loc[j,'i'] = 'csp'
    rsc_wsc = rsc_wsc.groupby(['r','i']).sum().reset_index()
    rsc_wsc.i = rsc_wsc.i.str.lower()
    
    if len(rsc_wsc.columns) < 3:
        rsc_wsc['value'] = ''
        rsc_wsc.columns = ['r','tech','exist']

    else:
        rsc_wsc.columns = ['r','tech','exist']

    ### Change the units
    rsc_wsc.exist /= 1000
    tout = rsc_wsc.copy()

    #%% Load supply curve files ---------------------------------------------------------

    #%%#################
    #    -- Wind --    #
    ####################

    windin, wind = {}, {}
    cost_components_wind = {}

    for s in ['ons','ofs']:
        windin[s], wind[s] = agg_supplycurve(
            scpath=os.path.join(inputs_case,f'wind-{s}_supply_curve.csv'),
            inputs_case=inputs_case, 
            agglevel=agglevel, AggregateRegions=AggregateRegions, 
            numbins_tech=numbins[f'wind-{s}'], spur_cutoff=spur_cutoff,
            agglevel_variables=agglevel_variables, deflate=deflate,
            sw=sw, write=write
            )
        
        cost_components_wind[s] = (
            wind[s][['trans_adder_per_mw', 'capital_adder_per_mw']]
            .round(2).reset_index()
            .rename(columns={
                'region':'r', 'class':'*i', 'bin':'rscbin',
                'trans_adder_per_mw':'cost_trans',
                'capital_adder_per_mw':'cost_cap'
            })
        )
          
        cost_components_wind[s]['*i'] = f'wind-{s}_' + cost_components_wind[s]['*i'].astype(str)
        cost_components_wind[s]['rscbin'] = 'bin' + cost_components_wind[s]['rscbin'].astype(str)
        cost_components_wind[s] = pd.melt(
            cost_components_wind[s], id_vars=['*i','r','rscbin'], var_name='sc_cat', value_name= 'value')


    windall = (
        pd.concat(wind, axis=0)
        .reset_index(level=0).rename(columns={'level_0':'type'})
        .reset_index()
    )
    ### Normalize formatting
    windall['type'] = 'wind-' + windall['type']
    windall.supply_curve_cost_per_mw = windall.supply_curve_cost_per_mw.round(2)
    windall['class'] = 'class' + windall['class'].astype(str)
    windall['bin'] = 'wsc' + windall['bin'].astype(str)
    ### Pivot, with bins in long format
    windcost = (
        windall.pivot(index=['region','class','type'], columns='bin', values='supply_curve_cost_per_mw')
        .fillna(0).reset_index())
    windcap = (
        windall.pivot(index=['region','class','type'], columns='bin', values='capacity')
        .fillna(0).reset_index())
    ### Write the onshore sc_point_gid-to-(region,class,bin) map for writecapdat.py
    gid2irb_wind = wind['ons']['sc_point_gid'].reset_index().rename(columns={'region':'r','bin':'rscbin'})
    gid2irb_wind['i'] = 'wind-ons_' + gid2irb_wind['class'].astype(str)
    ## Unpack the sc_point_gid's
    out = []
    for i, row in gid2irb_wind.iterrows():
        for sc_point_gid in row.sc_point_gid.split(','):
            out.append([sc_point_gid, row.i, row.r, row.rscbin])
    gid2irb_wind = (
        pd.DataFrame(out, columns=['sc_point_gid','i','r','rscbin'])
        .astype({'sc_point_gid':int})
        .set_index('sc_point_gid'))

    #%%#########################################################
    #    -- Onshore Wind Exogenous (pre-tstart) Capacity --    #
    ############################################################

    ### Get the site-level builds
    dfwindexog = pd.read_csv(
        os.path.join(inputs_case,'wind-ons_exog_cap.csv')
    ).rename(columns={'capacity':'MW'})
    ### Get the rscbin, then sum by (i,r,rscbin,t)
    dfwindexog['rscbin'] = 'bin'+dfwindexog.sc_point_gid.map(gid2irb_wind.rscbin).astype(int).astype(str)
    dfwindexog = dfwindexog.groupby(['*tech','region','rscbin','year']).MW.sum()

    #%%###############
    #    -- PV --    #
    ##################

    upvin, upv = agg_supplycurve(
        scpath=os.path.join(inputs_case,'upv_supply_curve.csv'),
        inputs_case=inputs_case,
        agglevel=agglevel, AggregateRegions=AggregateRegions,
        numbins_tech=numbins['upv'], spur_cutoff=spur_cutoff,
        agglevel_variables=agglevel_variables, deflate=deflate,
        sw=sw, write=write
        )

    #Similar to wind, save the trans vs cap components and then concatenate them below just
    #before outputting rsc_combined.csv
    cost_components_upv = upv[['trans_adder_per_mw', 'capital_adder_per_mw']].round(2).reset_index()
    cost_components_upv = cost_components_upv.rename(columns={
        'region':'r','class':'*i','bin':'rscbin','trans_adder_per_mw':'cost_trans',
        'capital_adder_per_mw':'cost_cap'})
    cost_components_upv['*i'] = 'upv_' + cost_components_upv['*i'].astype(str)
    cost_components_upv['rscbin'] = 'bin' + cost_components_upv['rscbin'].astype(str)
    cost_components_upv = pd.melt(
        cost_components_upv, id_vars=['*i','r','rscbin'], var_name='sc_cat', value_name= 'value')

    ### Write the upv sc_point_gid-to-(region,class,bin) map
    gid2irb_upv = upv['sc_point_gid'].reset_index().rename(columns={'region':'r','bin':'rscbin'})
    gid2irb_upv['i'] = 'upv_' + gid2irb_upv['class'].astype(str)
    ## Unpack the sc_point_gid's
    out = []
    for i, row in gid2irb_upv.iterrows():
        for sc_point_gid in row.sc_point_gid.split(','):
            out.append([sc_point_gid, row.i, row.r, row.rscbin])
    gid2irb_upv = (
        pd.DataFrame(out, columns=['sc_point_gid','i','r','rscbin'])
        .astype({'sc_point_gid':int})
        .set_index('sc_point_gid'))
    
    ### Normalize formatting
    upv = upv.reset_index()
    upv['class'] = 'class' + upv['class'].astype(str)
    upv['bin'] = 'upvsc' + upv['bin'].astype(str)
    ### Pivot, with bins in long format
    upvcost = (
        upv.pivot(columns='bin',values='supply_curve_cost_per_mw',index=['region','class'])
        .fillna(0)
        ### reV spur line and reinforcement costs are now in per MW-AC terms, so removing the 
        ### correction term that was applied. 
    ).reset_index()
    upvcap = (
        upv.pivot(columns='bin',values='capacity',index=['region','class'])
        .fillna(0).reset_index())
    
    #%%################################################
    #    -- UPV Exogenous (pre-tstart) Capacity --    #
    ###################################################
    
    ### Get the site-level builds
    dfupvexog = pd.read_csv(
        os.path.join(inputs_case,'upv_exog_cap.csv')
    ).rename(columns={'capacity':'MW'})

    ### Get the rscbin, then sum by (i,r,rscbin,t)
    dfupvexog['rscbin'] = 'bin'+dfupvexog.sc_point_gid.map(gid2irb_upv.rscbin).astype(int).astype(str)
    dfupvexog = dfupvexog.groupby(['*tech','region','rscbin','year']).MW.sum()
    
    #%%################
    #    -- CSP --    #
    ###################
    
    cspin, csp = agg_supplycurve(
        scpath=os.path.join(inputs_case,'csp_supply_curve.csv'),
        inputs_case=inputs_case,
        agglevel=agglevel, AggregateRegions=AggregateRegions, 
        numbins_tech=numbins['csp'], spur_cutoff=spur_cutoff,
        agglevel_variables=agglevel_variables, deflate=deflate,
        sw=sw, write=False
    )

    ### Normalize formatting
    csp = csp.reset_index()
    csp['class'] = 'class' + csp['class'].astype(str)
    csp['bin'] = 'cspsc' + csp['bin'].astype(str)
    ### Pivot, with bins in long format
    cspcost = (
        csp.pivot(columns='bin',values='supply_curve_cost_per_mw',index=['region','class'])
        .fillna(0)
    ).reset_index()
    cspcap = (
        csp.pivot(columns='bin',values='capacity',index=['region','class'])
        .fillna(0).reset_index())
    
    ## Duplicate the CSP supply curve for each CSP configuration
    cspcap = (
        pd.concat({'csp{}'.format(i): cspcap for i in range(1,csp_configs+1)}, axis=0)
        .reset_index(level=0).rename(columns={'level_0':'tech'}).reset_index(drop=True))
    cspcost = (
        pd.concat({'csp{}'.format(i): cspcost for i in range(1,csp_configs+1)}, axis=0)
        .reset_index(level=0).rename(columns={'level_0':'tech'}).reset_index(drop=True))
    
    # If CSP is turned off, remove the CSP supply curve data
    if int(sw['GSw_CSP']) == 0:
        cspcap = pd.DataFrame(columns = cspcap.columns)
        cspcost = pd.DataFrame(columns = cspcost.columns)
    
    #%% Geothermal
    use_geohydro_rev_sc = geohydrosupplycurve == "reV"
    use_egs_rev_sc = egssupplycurve == "reV"

    ## reV supply curves
    if use_geohydro_rev_sc or use_egs_rev_sc:
        geoin, geo = {}, {}
        rev_geo_types = []
        if use_geohydro_rev_sc:
            rev_geo_types.append('geohydro')
        if use_egs_rev_sc:
            rev_geo_types.append('egs')
        for s in rev_geo_types:
            geoin[s], geo[s] = agg_supplycurve(
                scpath=os.path.join(
                    inputs_case,
                    f'{s}_supply_curve.csv'),
                numbins_tech=numbins[s], inputs_case=inputs_case,
                agglevel=agglevel, AggregateRegions=AggregateRegions,
                spur_cutoff=spur_cutoff,agglevel_variables=agglevel_variables, deflate=deflate,
                sw=sw, write=False
            )

        geoall = (
            pd.concat(geo, axis=0)
            .reset_index(level=0).rename(columns={'level_0':'type'})
            .reset_index()
        )
        geoall['type']=geoall['type']+'_allkm'
        geoall.supply_curve_cost_per_mw = geoall.supply_curve_cost_per_mw.round(2)
        geoall['class'] = 'class' + geoall['class'].astype(str)
        geoall['bin'] = 'geosc' + geoall['bin'].astype(str)
        ### Pivot, with bins in long format
        geocost = (
            geoall.pivot(index=['region', 'class', 'type'], columns='bin', values='supply_curve_cost_per_mw')
            .fillna(0).reset_index())
        geocap = (
            geoall.pivot(index=['region', 'class', 'type'], columns='bin', values='capacity')
            .fillna(0).reset_index())
        
        ### Geothermal bins (flexible)
        bins_geo = (range(1, max(numbins['geohydro']*use_geohydro_rev_sc, numbins['egs']*use_egs_rev_sc) + 1))

        geocap.rename(
            columns={
                **{'region':'r', 'type':'tech',
                'Unnamed: 0':'r', 'Unnamed: 1':'class', 'Unnamed 2': 'tech'},
                **{'geosc{}'.format(i): 'bin{}'.format(i) for i in bins_geo}},
            inplace=True)
        geocost.rename(
            columns={
                **{'region':'r', 'type':'tech',
                'Unnamed: 0':'r', 'Unnamed: 1':'class', 'Unnamed 2': 'tech'},
                **{'geosc{}'.format(i): 'bin{}'.format(i) for i in bins_geo}},
            inplace=True)
        
        if use_geohydro_rev_sc:
            ### Write the geohydro sc_point_gid-to-(region,class,bin) map
            gid2irb_geohydro = geo['geohydro']['sc_point_gid'].reset_index().rename(columns={'region':'r','bin':'rscbin'})
            gid2irb_geohydro['i'] = 'geohydro_' + gid2irb_geohydro['class'].astype(str)
            ## Unpack the sc_point_gid's
            out = []
            for i, row in gid2irb_geohydro.iterrows():
                for sc_point_gid in row.sc_point_gid.split(','):
                    out.append([sc_point_gid, row.i, row.r, row.rscbin])
            gid2irb_geohydro = (
                pd.DataFrame(out, columns=['sc_point_gid','i','r','rscbin'])
                .astype({'sc_point_gid':int})
                .set_index('sc_point_gid'))
        
            #%% Write the geohydro exogenous (pre-tstart) capacity
            ### Get the site-level builds
            dfgeohydroexog = pd.read_csv(
                os.path.join(inputs_case,'geohydro_exog_cap.csv')
            ).rename(columns={'capacity':'MW'})

            ### Get the rscbin, then sum by (i,r,rscbin,t)
            dfgeohydroexog['rscbin'] = 'bin'+dfgeohydroexog.sc_point_gid.map(gid2irb_geohydro.rscbin).astype(int).astype(str)
            dfgeohydroexog = dfgeohydroexog.groupby(['*tech','region','rscbin','year']).MW.sum()

    #%% Get supply-curve data for postprocessing
    spurout_list = [
        (
            wind['ons'].reset_index()
            .assign(i='wind-ons_'+wind['ons'].reset_index()['class'].astype(str))
            .assign(rscbin='bin'+wind['ons'].reset_index()['bin'].astype(str))
            .rename(columns={'region':'r'})
            [['i','r','rscbin','capacity','dist_spur_km','dist_reinforcement_km','supply_curve_cost_per_mw']]
        ),
        (
            wind['ofs'].reset_index()
            .assign(i='wind-ofs_'+wind['ofs'].reset_index()['class'].astype(str))
            .assign(rscbin='bin'+wind['ofs'].reset_index()['bin'].astype(str))
            .rename(columns={'region':'r'})
            [['i','r','rscbin','capacity','dist_spur_km','dist_reinforcement_km','supply_curve_cost_per_mw']]
        ),
        (
            upv
            .assign(i='upv_'+upv['class'].astype(str).str.strip('class'))
            .assign(rscbin='bin'+upv['bin'].str.strip('upvsc'))
            .rename(columns={'region':'r'})
            [['i','r','rscbin','capacity','dist_spur_km','dist_reinforcement_km','supply_curve_cost_per_mw']]
        ),
        (
            csp
            .assign(i='csp_'+csp['class'].astype(str).str.strip('class'))
            .assign(rscbin='bin'+csp['bin'].str.strip('cspsc'))
            .rename(columns={'region':'r'})
            [['i','r','rscbin','capacity','dist_spur_km','dist_reinforcement_km','supply_curve_cost_per_mw']]
        ),
    ]
    if use_geohydro_rev_sc:
        spurout_list.append(
            geo['geohydro'].reset_index()
            .assign(i='geohydro_allkm_'+geo['geohydro'].reset_index()['class'].astype(str))
            .assign(rscbin='bin'+geo['geohydro'].reset_index()['bin'].astype(str))
            .rename(columns={'region':'r'})
            [['i','r','rscbin','capacity','dist_spur_km','dist_reinforcement_km','supply_curve_cost_per_mw']]
        )
    if use_egs_rev_sc:
        spurout_list.append(
            geo['egs'].reset_index()
            .assign(i='egs_allkm_'+geo['egs'].reset_index()['class'].astype(str))
            .assign(rscbin='bin'+geo['egs'].reset_index()['bin'].astype(str))
            .rename(columns={'region':'r'})
            [['i','r','rscbin','capacity','dist_spur_km','dist_reinforcement_km','supply_curve_cost_per_mw']]
        )
    spurout = pd.concat(spurout_list).round(2)

    ### Get spur-line and reinforcement distances if using in annual trans investment limit
    poi_distance = spurout.copy()
    ## Duplicate CSP entries for each CSP system design
    poi_distance_csp = poi_distance.loc[poi_distance.i.str.startswith('csp')].copy()
    poi_distance_csp_broadcasted = pd.concat([
        poi_distance_csp.assign(i=poi_distance_csp.i.str.replace('csp_',f'csp{i}_'))
        for i in range(1,csp_configs+1)
    ], axis=0)
    poi_distance_out = (
        pd.concat([
            poi_distance.loc[~poi_distance.i.str.startswith('csp')],
            poi_distance_csp_broadcasted
        ], axis=0)
        ## Reformat to save for GAMS
        .rename(columns={'i':'*i'}).set_index(['*i','r','rscbin'])
    )
    ## Convert to miles
    distance_spur = (
        poi_distance_out.dist_spur_km.rename('miles') / 1.609).round(3)
    distance_reinforcement = (
        poi_distance_out.dist_reinforcement_km.rename('miles') / 1.609).round(3)

    #%%###################################
    #    -- DUPV Supply Curve Data --    #
    ######################################
    
    # Using 2018 version for everything else
    dupvcost = pd.read_csv(os.path.join(inputs_case,'dupv_supply_curves_cost.csv'))
    dupvcap = pd.read_csv(os.path.join(inputs_case,'dupv_supply_curves_capacity.csv'))
    # If DUPV is turned off, then zero out the cost and capacity data
    if int(sw['GSw_DUPV']) == 0:
        print("DUPV turned off")
        dupvcost = pd.DataFrame(columns = dupvcost.columns)
        dupvcap = pd.DataFrame(columns = dupvcap.columns)

    # Convert dollar years
    dupvcost[dupvcost.select_dtypes(include=['number']).columns] *= deflate['DUPV_supply_curves_cost_2018']
    
    #%% Reformat the supply curve dataframes
    ### Non-wind bins
    bins = list(range(1, numbins_other + 1))
    ### Wind bins (flexible)
    bins_wind = list(range(1, max(numbins['wind-ons'], numbins['wind-ofs']) + 1))
    ### UPV bins (flexible)
    bins_upv = list(range(1, numbins['upv'] + 1))
    ### CSP bins (flexible)
    bins_csp = list(range(1, numbins['csp'] + 1))

    ### NOTE: wind capacity and costs also differentiate between 'class' and 'tech'
    rcolnames = {'region':'r', 'type':'tech'}

    dupvcap.rename(
        columns={
            **{'dupvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
    upvcap.rename(
        columns={
            **rcolnames, 
            **{'upvsc{}'.format(i): 'bin{}'.format(i) for i in bins_upv}}, inplace=True)
    cspcap.rename(
        columns={
            **rcolnames, 
            **{'cspsc{}'.format(i): 'bin{}'.format(i) for i in bins_csp}}, inplace=True)
    windcap.rename(
        columns={
            **rcolnames,
            **{'wsc{}'.format(i): 'bin{}'.format(i) for i in bins_wind}},inplace=True)

    dupvcost.rename(
        columns={
            **{'dupvsc{}'.format(i): 'bin{}'.format(i) for i in bins}}, inplace=True)
    upvcost.rename(
        columns={
            **rcolnames, 
            **{'upvsc{}'.format(i): 'bin{}'.format(i) for i in bins_upv}}, inplace=True)
    cspcost.rename(
        columns={
            **rcolnames, 
            **{'cspsc{}'.format(i): 'bin{}'.format(i) for i in bins_csp}}, inplace=True)
    windcost.rename(
        columns={
            **rcolnames,
            **{'wsc{}'.format(i): 'bin{}'.format(i) for i in bins_wind}},inplace=True)

    dupvcap['tech'] = 'dupv'
    upvcap['tech'] = 'upv'

    dupvcost['tech'] = 'dupv'
    upvcost['tech'] = 'upv'
    
    #%% Combine the supply curves
    alloutcap_list = [windcap, cspcap, upvcap, dupvcap]
    alloutcost_list = [windcost, cspcost, upvcost, dupvcost]

    if use_geohydro_rev_sc or use_egs_rev_sc:
        alloutcap_list.append(geocap)
        alloutcost_list.append(geocost)

    alloutcap = pd.concat(alloutcap_list)
    alloutcost = (
        pd.concat(alloutcost_list)
        .set_index(['r','class','tech'])
        .reset_index())

    alloutcap['class'] = alloutcap['class'].map(lambda x: x.lstrip('cspclass'))
    alloutcap['class'] = alloutcap['class'].map(lambda x: x.lstrip('class'))
    alloutcost['class'] = alloutcost['class'].map(lambda x: x.lstrip('cspclass'))
    alloutcost['class'] = alloutcost['class'].map(lambda x: x.lstrip('class'))

    alloutcap['var'] = 'cap'
    alloutcost['var'] = 'cost'

    alloutcap['class'] = 'class' + alloutcap['class'].astype(str)
    t1 = alloutcap.pivot(
        index=['r','tech','var'], columns='class',
        values=[c for c in alloutcap.columns if c.startswith('bin')]).reset_index()
    ### Concat the multi-level column names to a single level
    t1.columns = ['_'.join(i).strip('_') for i in t1.columns.tolist()]

    t2 = t1.merge(tout, on=['r','tech'], how='outer').fillna(0)

    ### Subset to single-tech curves
    wndonst2 = t2.loc[t2.tech=="wind-ons"].copy()
    wndofst2 = t2.loc[t2.tech=="wind-ofs"].copy()
    cspt2 = t2.loc[t2.tech.isin(['csp{}'.format(i) for i in range(1,csp_configs+1)])]
    upvt2 = t2.loc[t2.tech=="upv"].copy()
    dupvt2 = t2.loc[t2.tech=="dupv"].copy()
    geohydrot2 = t2.loc[t2.tech=="geohydro_allkm"].copy()
    egst2 = t2.loc[t2.tech=="egs_allkm"].copy()

    ### Get the combined outputs
    outcap = pd.concat([wndonst2, wndofst2, upvt2, dupvt2, cspt2, geohydrot2, egst2])

    moutcap = pd.melt(outcap, id_vars=['r','tech','var'])
    moutcap = moutcap.loc[~moutcap.variable.isin(['exist','temp'])].copy()

    moutcap['bin'] = moutcap.variable.map(lambda x: x.split('_')[0])
    moutcap['class'] = moutcap.variable.map(lambda x: x.split('_')[1].lstrip('class'))
    outcols = ['r','tech','var','bin','class','value']
    moutcap = moutcap.loc[moutcap.value != 0, outcols].copy()

    outcapfin = moutcap.pivot(
        index=['r','tech','var','class'], columns='bin', values='value'
    ).fillna(0).reset_index()

    allout = pd.concat([outcapfin, alloutcost])
    allout['tech'] = allout['tech'] + '_' + allout['class'].astype(str)


    #%%----------------------------------------------------------------------------------
    ##########################
    #    -- Hydropower --    #
    ##########################
    '''
    Adding hydro costs and capacity separate as it does not
    require the calculations to reduce capacity by existing amounts.
    
    Goal here is to acquire a data frame that matches the format
    of alloutm so that we can simply stack the two.
    '''
    hydcap = pd.read_csv(os.path.join(inputs_case,'hydcap.csv'))
    hydcost = pd.read_csv(os.path.join(inputs_case,'hydcost.csv'))

    hydcap = (pd.melt(hydcap, id_vars=['tech','class'])
                .set_index(['tech','class','variable'])
                .sort_index())
    hydcap = hydcap.reset_index()
    hydcost = pd.melt(hydcost, id_vars=['tech','class'])

    # Convert dollar year
    hydcost[hydcost.select_dtypes(include=['number']).columns] *= deflate['hydcost']

    hydcap['var'] = 'cap'
    hydcost['var'] = 'cost'

    hyddat = pd.concat([hydcap, hydcost])
    hyddat['bin'] = hyddat['class'].map(lambda x: x.replace('hydclass','bin'))
    hyddat['class'] = hyddat['class'].map(lambda x: x.replace('hydclass',''))

    hyddat.rename(columns={'variable':'r','bin':'variable'}, inplace=True)
    hyddat = hyddat[['tech','r','value','var','variable']].fillna(0)


    #########################################
    #    -- Pumped Storage Hydropower --    #
    #########################################
    
    # Input processing currently assumes that cost data in CSV file is in 2004$
    psh_cap = pd.read_csv(os.path.join(inputs_case,'psh_supply_curves_capacity.csv'))
    psh_cost = pd.read_csv(os.path.join(inputs_case,'psh_supply_curves_cost.csv'))
    psh_durs = pd.read_csv(os.path.join(inputs_case,'psh_supply_curves_duration.csv'), header=0)

    psh_cap = pd.melt(psh_cap, id_vars=['r'])
    psh_cost = pd.melt(psh_cost, id_vars=['r'])

    # Convert dollar year
    psh_cost[psh_cost.select_dtypes(include=['number']).columns] *= deflate['PHScostn']

    psh_cap['var'] = 'cap'
    psh_cost['var'] = 'cost'

    psh_out = pd.concat([psh_cap, psh_cost]).fillna(0)
    psh_out['tech'] = 'pumped-hydro'
    psh_out['variable'] = psh_out.variable.map(lambda x: x.replace('pshclass','bin'))
    psh_out = psh_out[hyddat.columns].copy()

    # Select storage duration correponding to the supply curve
    psh_dur_out = psh_durs[psh_durs['pshsupplycurve']==pshsupplycurve]['duration']


    #######################################################
    #    -- Demand Response and EV Managed Charging --    #
    #######################################################
    rsc_dr = {}
    for drcat in ['dr','evmc']:
        scen = {'dr':sw.drscen, 'evmc':sw.evmcscen}[drcat]
        active = {'dr':int(sw.GSw_DR), 'evmc':int(sw.GSw_EVMC)}[drcat]
        if (scen.lower() != 'none') and active:
            rsc = pd.read_csv(os.path.join(inputs_case,f'{drcat}_rsc.csv'))
            rsc['var'] = rsc['var'].str.lower()

            # Convert dollar year
            rsc.loc[rsc['var']=='Cost','value'] *= deflate[f'{drcat}_rsc_{scen}']
        
            # Duplicate or interpolate data for all years between start and
            # end year. Only DR has yearly supply curve data.
            yrs = pd.DataFrame(list(range(startyear, endyear+1)), columns=['year'])
            yrs['tmp'] = 1

            # Get all years for all parts of data
            tmp = rsc[[c for c in rsc.columns if c not in ['year','value']]].drop_duplicates()
            tmp['tmp'] = 1
            tmp = pd.merge(tmp, yrs, on='tmp').drop('tmp',axis=1)
            tmp = pd.merge(tmp, rsc, how='outer', on=list(tmp.columns))
            # Interpolate between years that exist using a linear spline interpolation
            # extrapolating any values at the beginning or end as required
            # Include all years here then filter later to get spline correct if data
            # covers more than the years modeled
            def grouper(group):
                return group.interpolate(
                    limit_direction='both', method='slinear', fill_value='extrapolate')
        
            rsc = (
                tmp
                .groupby([c for c in tmp.columns if c not in ['value','year']], group_keys=True)
                .apply(grouper)
            )
            rsc = (
                rsc[rsc.year.isin(yrs.year)]
                ### Reorder to match other supply curves
                [['tech','r','var','bin','year','value']]
                ### Rename the first column so GAMS reads the header as a comment
                .rename(columns={'tech':'*tech','var':'sc_cat','bin':'rscbin','year':'t'})
            )
            # Ensure no values are < 0
            rsc['value'].clip(lower=0, inplace=True)
        else:
            rsc = pd.DataFrame(columns=['*tech','r','sc_cat','rscbin','t','value'])

        rsc_dr[drcat] = rsc.copy()


    #%%----------------------------------------------------------------------------------
    ##################################
    #    -- Combine everything --    #
    ##################################

    ### Stack the final versions
    alloutm = pd.melt(allout, id_vars=['r','tech','var'])
    alloutm = alloutm.loc[alloutm.variable != 'class'].copy()
    alloutm = pd.concat([alloutm, hyddat, psh_out])

    ### Drop the (cap,cost) entries with nan cost
    alloutm = (
        alloutm
        .pivot(index=['r','tech','variable'], columns=['var'], values=['value'])
        .dropna()['value']
        .reset_index()
        .melt(id_vars=['r','tech','variable'])
        [['tech','r','var','variable','value']]
        ### Rename the first column so GAMS reads the header as a comment
        .rename(columns={'tech':'*i','var':'sc_cat','variable':'rscbin'})
        .astype({'value':float})
        ### Drop 0 values
        .replace({'value':{0.:np.nan}}).dropna()
        .round(5)
    )

    ## Merge geothermal non-reV supply curves if applicable
    if not use_geohydro_rev_sc:
        geohydro_rsc = pd.read_csv(
            os.path.join(inputs_case,'geo_rsc.csv'),
            header=0)
        geohydro_rsc = geohydro_rsc.loc[geohydro_rsc['*i'].str.startswith("geohydro_allkm")]
        # Filter by valid regions
        geohydro_rsc = geohydro_rsc.loc[geohydro_rsc['r'].isin(val_r_all)]
        # Convert dollar year
        geohydro_rsc.sc_cat = geohydro_rsc.sc_cat.str.lower()
        geohydro_rsc.loc[geohydro_rsc.sc_cat=='cost', 'value'] *= deflate['geo_rsc_{}'.format(geohydrosupplycurve)]
        geohydro_rsc["rscbin"] = "bin1"
        alloutm = pd.concat([alloutm, geohydro_rsc])
    
    if not use_egs_rev_sc:
        egs_rsc = pd.read_csv(
            os.path.join(inputs_case,'geo_rsc.csv'),
            header=0)
        egs_rsc = egs_rsc.loc[egs_rsc['*i'].str.startswith("egs_allkm")]
        # Filter by valid regions
        egs_rsc = egs_rsc.loc[egs_rsc['r'].isin(val_r_all)]
        # Convert dollar year
        egs_rsc.sc_cat = egs_rsc.sc_cat.str.lower()
        egs_rsc.loc[egs_rsc.sc_cat=='cost', 'value'] *= deflate['geo_rsc_{}'.format(egssupplycurve)]
        egs_rsc["rscbin"] = "bin1"
        alloutm = pd.concat([alloutm, egs_rsc])

    egsnearfield_rsc = pd.read_csv(
            os.path.join(inputs_case,'geo_rsc.csv'),
            header=0)
    egsnearfield_rsc = egsnearfield_rsc.loc[egsnearfield_rsc['*i'].str.startswith("egs_nearfield")]
    # Filter by valid regions
    egsnearfield_rsc = egsnearfield_rsc.loc[egsnearfield_rsc['r'].isin(val_r_all)]
    # Convert dollar year
    egsnearfield_rsc.sc_cat = egsnearfield_rsc.sc_cat.str.lower()
    egsnearfield_rsc.loc[egsnearfield_rsc.sc_cat=='cost', 'value'] *= deflate['geo_rsc_{}'.format(egsnearfieldsupplycurve)]
    egsnearfield_rsc["rscbin"] = "bin1"
    alloutm = pd.concat([alloutm, egsnearfield_rsc])

    ### Combine with cost components
    alloutm = pd.concat(
        [alloutm, cost_components_upv,cost_components_wind['ons'], cost_components_wind['ofs']])
    
    #%%----------------------------------------------------------------------------------
    #######################
    #    -- Biomass --    #
    #######################
    '''
    Biomass is currently being handled directly in b_inputs.gms
    '''

    #%%----------------------------------------------------------------------------------
    ##########################
    #    -- Geothermal --    #
    ##########################

    geo_disc_rate = pd.read_csv(os.path.join(inputs_case,'geo_discovery_rate.csv'))
    geo_discovery_factor = pd.read_csv(os.path.join(inputs_case,'geo_discovery_factor.csv'))
    geo_discovery_factor = geo_discovery_factor.loc[
        geo_discovery_factor.r.isin(val_r_all)].copy()


    #%%----------------------------------------------------------------------------------
    ##########################################
    #    -- Spur lines (disaggregated) --    #
    ##########################################
    '''
    NOTE: In the upv and wind-ons supply curves from reV, a single site (indicated by
    a single sc_point_gid value) can be mapped to different BAs for upv and wind, depending
    on the distribution of tech-specific developable area within the reV cell.
    That could presumably lead to errors for site-specific spur lines indexed by sc_point_gid.
    Here we re-map each upv/wind-ons supply curve point based on the no-exclusions
    transmission table. But note that that will throw off the CF profiles, which are
    calculated as weighted averages over the available gid's within the reV cell.
    So it would be better to do this correction in hourlize (and even better to make the
    fix upstream in reV.)
    '''
    ### Get the fips-to-r map
    fips2r = pd.read_csv(os.path.join(inputs_case,'r_county.csv'),index_col=1).squeeze(1)
        
    ###### Spur line costs
    spursites = pd.read_csv(os.path.join(inputs_case,'spur_cost.csv'))
    ### Deflate to ReEDS dollar year
    spursites['trans_cap_cost_per_mw'] *= deflate['spur']
    spursites = (
        spursites
            .assign(x='i'+spursites['sc_point_gid'].astype(str))
            .assign(r=(
                ### Update Oglala Lakota county, SD
                spursites['r'].map(lambda x: {'p46113':'p46102'}.get(x,x))))
            ### drop sites with too high of spur-line cost
            .loc[spursites['trans_cap_cost_per_mw'] < spur_cutoff]
            .round(2)
    )
    
    ### Map sites to the proper regional aggregation
    spursites['r'] = spursites['r'].map(fips2r)

    ### Filter for valid regions
    spursites.dropna(subset=['r'], inplace=True)

    ###### Site maps
    ### UPV
    sitemap_upv = (
        upvin
        .assign(i='upv_'+upvin['class'].astype(str))
        .assign(rscbin='bin'+upvin['bin'].astype(str))
        .assign(x='i'+upvin['sc_point_gid'].astype(str))
    )
    sitemap_upv = (
        sitemap_upv
        ### Assign rb's based on the no-exclusions transmission table
        .assign(r=sitemap_upv.x.map(spursites.set_index('x').r))
        [['i','r','rscbin','x']]
        .rename(columns={'i':'*i'})
    )
    ### wind-ons
    sitemap_windons = (
        windin['ons']
        .assign(i='wind-ons_'+windin['ons']['class'].astype(str))
        .assign(rscbin='bin'+windin['ons']['bin'].astype(str))
        .assign(x='i'+windin['ons']['sc_point_gid'].astype(str))
    )
    sitemap_windons = (
        sitemap_windons
        ### Assign r's based on the no-exclusions transmission table
        .assign(r=sitemap_windons.x.map(spursites.set_index('x').r))
        [['i','r','rscbin','x']]
        .rename(columns={'i':'*i'})
    )

    ### Combine, then only keep sites that show up in both supply curve and spur-line cost tables
    spurline_sitemap_list = [sitemap_upv,sitemap_windons]
    ### geohydro_allkm
    if use_geohydro_rev_sc:
        sitemap_geohydro = (
            geoin['geohydro']
            .assign(i='geohydro_allkm_'+geoin['geohydro']['class'].astype(str))
            .assign(rscbin='bin'+geoin['geohydro']['bin'].astype(str))
            .assign(x='i'+geoin['geohydro']['sc_point_gid'].astype(str))
        )
        sitemap_geohydro = (
            sitemap_geohydro
            ### Assign rb's based on the no-exclusions transmission table
            .assign(r=sitemap_geohydro.x.map(spursites.set_index('x').r))
            [['i','r','rscbin','x']]
            .rename(columns={'i':'*i'})
        )
        spurline_sitemap_list.append(sitemap_geohydro)
    ### egs_allkm
    if use_egs_rev_sc:
        sitemap_egs = (
            geoin['egs']
            .assign(i='egs_allkm_'+geoin['egs']['class'].astype(str))
            .assign(rscbin='bin'+geoin['egs']['bin'].astype(str))
            .assign(x='i'+geoin['egs']['sc_point_gid'].astype(str))
        )
        sitemap_egs = (
            sitemap_egs
            ### Assign rb's based on the no-exclusions transmission table
            .assign(r=sitemap_egs.x.map(spursites.set_index('x').r))
            [['i','r','rscbin','x']]
            .rename(columns={'i':'*i'})
        )
        spurline_sitemap_list.append(sitemap_egs)
    
    spurline_sitemap = pd.concat(spurline_sitemap_list, ignore_index=True)
    spurline_sitemap = spurline_sitemap.loc[spurline_sitemap.x.isin(spursites.x.values)].copy()
    spursites = spursites.loc[spursites.x.isin(spurline_sitemap.x.values)].copy()

    ### Add mapping from sc_point_gid to bin for reeds_to_rev.py
    site_bin_map_list = [
        windin['ons'].assign(tech='wind-ons')[['tech','sc_point_gid','bin']],
        windin['ofs'].assign(tech='wind-ofs')[['tech','sc_point_gid','bin']],
        upvin.assign(tech='upv')[['tech','sc_point_gid','bin']],
    ]
    if use_geohydro_rev_sc:
        site_bin_map_list.append(geoin['geohydro'].assign(tech='geohydro_allkm')[['tech','sc_point_gid','bin']])
    if use_egs_rev_sc:
        site_bin_map_list.append(geoin['egs'].assign(tech='egs_allkm')[['tech','sc_point_gid','bin']])
    site_bin_map = pd.concat(site_bin_map_list, ignore_index=True)

    
    #%%##############################
    #    -- Data Write-Out --    #
    #################################

    if write:
        ## Everything
        alloutm.to_csv(os.path.join(inputs_case, 'rsc_combined.csv'), index=False, header=True)
        ## Exogenous wind
        dfwindexog.round(3).to_csv(os.path.join(inputs_case,'exog_wind_ons_rsc.csv'))
        ## Exogenous UPV
        dfupvexog.round(3).to_csv(os.path.join(inputs_case,'exog_upv_rsc.csv'))
        ## Exogenous geohydro
        if use_geohydro_rev_sc:
            dfgeohydroexog.round(3).to_csv(os.path.join(inputs_case,'exog_geohydro_allkm_rsc.csv'))
        ## Geothermal discovery rates
        geo_disc_rate.round(decimals).to_csv(os.path.join(inputs_case, 'geo_discovery_rate.csv'), index=False)
        geo_discovery_factor.round(decimals).to_csv(os.path.join(inputs_case, 'geo_discovery_factor.csv'), index=False)
        ## DR and EVMC
        for drcat in ['dr','evmc']:
            rsc_dr[drcat].to_csv(
                os.path.join(inputs_case ,f'rsc_{drcat}.csv'), index=False, header=True)
        ## Hybrids
        spursites[['x','trans_cap_cost_per_mw']].rename(columns={'x':'*x'}).to_csv(
            os.path.join(inputs_case,'spurline_cost.csv'), index=False)
        spursites['x'].to_csv(os.path.join(inputs_case,'x.csv'), index=False, header=False)
        spurline_sitemap.to_csv(
            os.path.join(inputs_case,'spurline_sitemap.csv'), index=False)
        spurline_sitemap[['x','r']].rename(columns={'x':'*x'}).drop_duplicates().to_csv(
            os.path.join(inputs_case,'x_r.csv'), index=False)
        ## Bin mapping
        site_bin_map.to_csv(os.path.join(inputs_case,'site_bin_map.csv'), index=False)
        ## Spurline and reinforcement distances and costs
        spurout.to_csv(os.path.join(inputs_case,'spur_parameters.csv'), index=False)
        distance_spur.to_csv(os.path.join(inputs_case,'distance_spur.csv'))
        distance_reinforcement.to_csv(os.path.join(inputs_case,'distance_reinforcement.csv'))
        ## Supply-Curve-Specific PSH Duration
        psh_dur_out.to_csv(os.path.join(inputs_case,'psh_sc_duration.csv'), index=False, header=False)

    return alloutm

#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__ == '__main__':
    ### Time the operation of this script
    tic = datetime.datetime.now()

    ### Parse arguments
    parser = argparse.ArgumentParser(description='Format and supply curves')
    parser.add_argument('reeds_path', help='path to ReEDS directory')
    parser.add_argument('inputs_case', help='path to inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    #%% Run it
    print('Starting writesupplycurves.py')

    main(reeds_path=reeds_path, inputs_case=inputs_case)

    reeds.log.toc(
        tic=tic, year=0, process='input_processing/writesupplycurves.py',
        path=os.path.join(inputs_case,'..'))
    
    print('Finished writesupplycurves.py')
