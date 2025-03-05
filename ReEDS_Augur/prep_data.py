#%% Notes
"""
This script writes inputs for resource adequacy calculations:
* capacity_credit.py (existing and marginal capacity credit)
* run_pras.jl -> ReEDS2PRAS.jl -> PRAS.jl (probabilistic resource adequacy)

The files used by PRAS are:
* In {case}/ReEDS_Augur/augur_data:
    * cap_converter_{year}.csv
    * energy_cap_{year}.csv
    * max_cap_{year}.csv
    * pras_load_{year}.h5
    * pras_vre_gen_{year}.h5
    * tran_cap_{year}.csv
* In {case}/inputs_case:
    * forcedoutage_hourly.h5
    * hydcf.csv
    * outage_forced_static.csv
    * resources.csv
    * tech-subset-table.csv
    * unitdata.csv
    * unitsize.csv
"""

#%% General imports
import os
import pandas as pd
import numpy as np
import gdxpds
### Local imports
import reeds


#%%### Procedure
def main(t, casedir):
    #%%### DEBUGGING: Inputs
    # t = 2020
    # reeds_path = os.path.expanduser('~/github2/ReEDS-2.0')
    # casedir = os.path.join(reeds_path,'runs','v20230214_PRMaugurM0_Pacific_d7fIrh4_CC_y2012')

    #%%### Get inputs from ReEDS
    gdx_file = os.path.join(casedir,'ReEDS_Augur','augur_data',f'reeds_data_{t}.gdx')
    gdxreeds = gdxpds.to_dataframes(gdx_file)
    ### Use indices as multiindex
    for key in gdxreeds:
        # try:
        if 'i' in gdxreeds[key]:
            gdxreeds[key].i = gdxreeds[key].i.str.lower()
        if 'ii' in gdxreeds[key]:
            gdxreeds[key].ii = gdxreeds[key].ii.str.lower()
        if 't' in gdxreeds[key]:
            gdxreeds[key].t = gdxreeds[key].t.astype(int)

    #%% Load other inputs from ReEDS
    inputs_case = os.path.join(casedir, 'inputs_case')

    sw = reeds.io.get_switches(casedir)
    sw['t'] = t

    h_dt_szn = pd.read_csv(os.path.join(inputs_case, 'h_dt_szn.csv'))
    hmap_allyrs = pd.read_csv(os.path.join(inputs_case, 'hmap_allyrs.csv'), low_memory=False)
    hmap_allyrs['szn'] = h_dt_szn['season'].copy()

    h_dt_szn = h_dt_szn.set_index(['year', 'hour'])
    # Add explicit timestamp index
    h_dt_szn['timestamp'] = pd.to_datetime(
        h_dt_szn.index.map(hmap_allyrs.set_index(['year', 'hour'])['*timestamp']))
    h_dt_szn = h_dt_szn.reset_index().set_index('timestamp')

    load = reeds.io.read_file(os.path.join(inputs_case, 'load.h5'), parse_timestamps=True)

    resources = pd.read_csv(os.path.join(inputs_case, 'resources.csv'))
    recf = reeds.io.read_file(os.path.join(inputs_case, 'recf.h5'), parse_timestamps=True)
    recf.columns = pd.MultiIndex.from_tuples([tuple(x.split('|')) for x in recf.columns],
                                             names=('i','r'))

    techs = gdxreeds['i_subsets'].pivot(columns='i_subtech',index='i',values='Value')


    #%%### Set up the output containers and a few other inputs
    csvout, h5out = {}, {}

    #%%### Transmission routes, capacity, and losses
    if int(sw.pras_trans_contingency):
        trancap_reeds = gdxreeds['cap_trans_prm']
    else:
        trancap_reeds = gdxreeds['cap_trans_energy']

    #%%### Efficiencies and storage parameters
    duration = gdxreeds['storage_duration'].loc[
        gdxreeds['storage_duration'].i.isin(gdxreeds['storage_standalone'].i)
    ].set_index('i').Value


    #%%### Nameplate capacity
    cap_ivr_realvint = (
        gdxreeds['cap_ivrt'].loc[gdxreeds['cap_ivrt'].t==t].drop('t', axis=1)
        .groupby(['i','v','r'], as_index=False).Value.sum()
    )
    ### Reset the vintages of all storage units to 'new1' to reduce model size
    cap_storage_devint = cap_ivr_realvint.loc[
        cap_ivr_realvint.i.isin(gdxreeds['storage_standalone'].i)].copy()
    cap_storage_devint['v'] = 'new1'
    cap_storage_devint = (
        cap_storage_devint.groupby(['i','v','r'], as_index=False).Value.sum())

    def _devint_storage(dfin):
        dfout = pd.concat([
            dfin.loc[~dfin.i.isin(gdxreeds['storage_standalone'].i)],
            cap_storage_devint
        ], axis=0)
        return dfout

    cap_ivr = _devint_storage(cap_ivr_realvint)

    #%% Remove VRE techs (i.e. techs with profiles in recf) and H2 production / DAC
    vretechs_i = resources.i.str.lower().unique()

    h2dac = techs['CONSUME'].dropna().index
    cap_nonh2dac = cap_ivr.loc[~cap_ivr.i.isin(h2dac)].copy()

    cap_vre = (
        cap_ivr.loc[cap_ivr.i.str.lower().isin(vretechs_i)]
        .set_index(['i','v','r']).Value.copy()
    )

    #%%### VRE generation, accounting for generation
    ### Apply CF adjustment to capacity (the resulting df is not meaningful but it's only a step
    ### toward the generation df).
    ### Some RE techs, like CSP, don't have cf_adj_t defined in all years,
    ### so fill missing values with 1, then drop rows with missing region (indicating no capacity)
    cf_adj_iv = (
        gdxreeds['cf_adj_t_filt'].loc[gdxreeds['cf_adj_t_filt'].t==t].drop('t', axis=1)
        .set_index(['i','v']).Value
    )
    cap_vre_derated = cap_vre.multiply(cf_adj_iv, fill_value=1).reset_index().dropna()
    if len(cap_vre) != len(cap_vre_derated):
        raise Exception(
            "CF adjustment didn't work; probably missing values in cf_adj_t_filt. "
            f"len(cap_vre) = {len(cap_vre)}; len(cap_vre_derated) = {(len(cap_vre_derated))}."
        )
    cap_vre_derated = cap_vre_derated.groupby(['i','r']).Value.sum()

    ### Multiply derated capacity by CF to get generation
    gen_vre_ir = recf.multiply(cap_vre_derated, axis=1).dropna(axis=1)
    if gen_vre_ir.shape[1] != cap_vre_derated.shape[0]:
        raise Exception("Mismatch between VRE capacity and available CF data")
    ### Aggregate by model zone
    gen_vre_r = gen_vre_ir.copy()
    gen_vre_r = gen_vre_r.groupby(axis=1, level='r').sum()

    ### Store generation by (i,r) for capacity_credit.py
    vre_gen_exist = gen_vre_ir.reindex(resources[['i','r']], axis=1).fillna(0).clip(lower=0)
    vre_gen_exist.columns = ['|'.join(c) for c in vre_gen_exist.columns]
    vre_gen_exist.index = h_dt_szn.set_index(['ccseason','year','h','hour']).index
    h5out['vre_gen_exist'] = vre_gen_exist

    ### Store generation by r for PRAS
    h5out['pras_vre_gen'] = vre_gen_exist


    ###### Store marginal CF by (i,r) for capacity_credit.py
    ## Use the cf_adj_iv for the latest available vintage
    cf_adj_i = cf_adj_iv.reset_index()
    ## Temporarily reformat the vintage so we can select the last one
    def intify(v):
        try:
            return int(v)
        except ValueError:
            return v
    cf_adj_i.v = (
        cf_adj_i.v.str.replace('new','')
        .map(intify)
        .map(lambda x: x if str(x).startswith('init') else f'new{x:>03}')
    )
    cf_adj_i = (
        cf_adj_i.sort_values(['i','v']).drop_duplicates('i', keep='last')
        .set_index('i').Value
        .reindex(recf.columns.get_level_values('i').unique()).fillna(1)
    )

    ### Multiply [CF] * [CF adjustment] to get marginal CF
    vre_cf_marg = (
        recf.multiply(cf_adj_i, level='i', axis=1)
        .reindex(resources[['i','r']], axis=1)
    )
    vre_cf_marg.columns = ['|'.join(c) for c in vre_cf_marg.columns]
    vre_cf_marg.index = h_dt_szn.set_index(['ccseason','year','h','hour']).index
    h5out['vre_cf_marg'] = vre_cf_marg


    h_dt_szn_load_years = h_dt_szn.loc[h_dt_szn.index.isin(load.index.get_level_values('datetime'))]
    #%%### H2 and DAC load
    ### First just make it all inflexible (necessary for PRAS)
    load_h2dac_all_hourly = (
        gdxreeds['prod_filt']
        .groupby(['r', 'allh']).Value.sum().reset_index()
        .merge(h_dt_szn_load_years[['h']].reset_index(), left_on='allh', right_on='h')
        .pivot(index='timestamp', columns='r', values='Value')
        .fillna(0)
    )


    #%%### Total load and net load
    ### Get Candian exports and add to this solve year's load
    can_exports = (
        gdxreeds['can_exports_h_filt']
        .merge(h_dt_szn_load_years[['h']].reset_index(), left_on='allh', right_on='h')
        .pivot(index='timestamp', columns='r', values='Value')
    )
    load_year = load.loc[t].add(can_exports, fill_value=0)

    ### PRAS doesn't yet handle flexible load, so include all H2/DAC load in the
    ### version we write for PRAS
    if int(sw['pras_include_h2dac']):
        pras_load = load_year.add(load_h2dac_all_hourly, fill_value=0)
    else:
        pras_load = load_year.copy()
    pras_load = (
        pras_load.merge(
            h_dt_szn[['season', 'year', 'h', 'hour']], left_index=True, right_index=True
        )
        .set_index(['season', 'year', 'h', 'hour'])
    )
    h5out['pras_load'] = pras_load
    ## Include the hourly H2/DAC load for debugging
    h5out['pras_h2dac_load'] = load_h2dac_all_hourly.reset_index(drop=True)

    ### Store load with the appropriate index for capacity_credit.py
    h5out['load'] = (
        load_year.merge(
            h_dt_szn[['ccseason', 'year', 'h', 'hour']], left_index=True, right_index=True
        )
        .set_index(['ccseason', 'year', 'h', 'hour'])
    )


    #%%### Collect some csv's for ReEDS2PRAS
    csvout['cap_converter'] = (
        gdxreeds['cap_converter_filt'].set_index('r').rename(columns={'Value':'MW'}))
    ### Transmission capacity: Subset for RA according to GSw_PRMTRADE_level switch
    tran_cap = (
        trancap_reeds.set_index(['r','rr','trtype']).rename(columns={'Value':'MW'}))
    if sw.GSw_PRMTRADE_level != 'country':
        hierarchy = reeds.io.get_hierarchy(casedir)
        if sw.GSw_PRMTRADE_level == 'r':
            rmap = dict(zip(hierarchy.index, hierarchy.index))
        else:
            rmap = hierarchy[sw.GSw_PRMTRADE_level]
        tran_cap['level'] = tran_cap.index.get_level_values('r').map(rmap)
        tran_cap['levell'] = tran_cap.index.get_level_values('rr').map(rmap)
        tran_cap = (
            tran_cap.loc[tran_cap.level==tran_cap.levell]
            .drop(['level','levell'], axis=1)
        )
    csvout['tran_cap'] = tran_cap
    ### Nameplate capacity
    max_cap = cap_nonh2dac.set_index(['i','v','r']).Value.rename('MW')
    ## Storage energy capacity [MWh] = power capacity [MW] * duration [h]
    energy_cap = (
        cap_storage_devint
        .set_index(['i','v','r']).Value
        .multiply(duration)
        .rename('MWh')
    )
    ## Drop storage with energy or power capacity below the PRAS cutoff
    too_small_storage = list(set(
        energy_cap.loc[energy_cap < sw['storcap_cutoff']].index.tolist()
        + max_cap.loc[energy_cap.index].loc[
            max_cap.loc[energy_cap.index] < sw['storcap_cutoff']].index.tolist()
        + max_cap.loc[max_cap < sw['storcap_cutoff']/2].index.tolist()
    ))
    csvout['energy_cap'] = energy_cap.drop(too_small_storage, errors='ignore')
    csvout['max_cap'] = max_cap.drop(too_small_storage, errors='ignore')

    #%% Strip water tech suffixes from water-dependent technologies
    ### NOTE: This must be done to make water runs compatible with PRAS, as PRAS is not set 
    ###       up to ingest generation techs with water tech suffixes, as well as to ensure
    ###       PRAS is operating the same for runs with/without GSw_WaterMain on.

    # For each dataframe in csvout, check if it has an 'i' index and if it does, use 
    # i_ctt_wst_link to remove the water suffixes
    watertech_link = pd.read_csv(
        os.path.join(casedir,'inputs_case','i_coolingtech_watersource_link.csv'),
             usecols=['*i','ii']
        )
    waterupgrades_link = pd.read_csv(
        os.path.join(casedir,'inputs_case','i_coolingtech_watersource_upgrades_link.csv'),
             usecols=['*i','ii']
        )
    watertech_link = pd.concat([watertech_link, waterupgrades_link])
    watertech_link = watertech_link.apply(lambda x: x.str.lower()).set_index('*i').squeeze(1)

    for key in csvout.keys():
        df = csvout[key]
        if 'i' in df.index.names:
            # Strip water tech suffixes from tech names
            df.rename(index=watertech_link, level='i', inplace=True)
            # Sum over i,v,t combination duplicates now that water techs have been stripped
            indices = list(df.index.names)
            df = df.groupby(df.index).sum()
            # Reset the index names
            df.index = pd.MultiIndex.from_tuples(df.index, names=indices)
            # Rewrite data in csvout with updated data
            csvout[key] = df.copy()

    #%%### Write it
    #%% .csv files
    for key in csvout:
        csvout[key].round(int(sw['decimals'])).to_csv(
            os.path.join(casedir,'ReEDS_Augur','augur_data',f'{key}_{t}.csv'),
        )
    #%% .h5 files
    for key in h5out:
        h5out[key].astype(np.float32).to_hdf(
            os.path.join(casedir,'ReEDS_Augur','augur_data',f'{key}_{t}.h5'),
            key='data', complevel=4, mode='w',
        )

    #%%### Return outputs for debugging
    return csvout, h5out
