# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 19:31:33 2021

@author: afrazier
"""

import pandas as pd

from ReEDS_Augur.utility.switchsettings import SwitchSettings
from ReEDS_Augur.utility.functions import agg_rs_to_r, apply_series_to_df, \
    filter_data_year, get_prop, map_szn_to_day
from ReEDS_Augur.utility.hourlyprofiles import HOURLY_PROFILES
from ReEDS_Augur.utility.inputs import INPUTS


class TechData(SwitchSettings):
    '''
    Class for ReEDS generation technologies
    '''

    # Defualt minimum generator size (MW)
    # Generators smaller than this will not be considered in Augur.
    min_gen_size = 5

    def __init__(self, tech_key, *args, **kwargs):
        self.avail_cap = None
        self.daily_energy_budget = None
        self.energy_cap = None
        self.gen_cost = None
        self.hourly_cfs_exist = None
        self.hourly_cfs_marg = None
        self.max_cap = None
        self.mingen = None
        self.ret_frac = None
        self.tech_key = tech_key

    def agg_gens(self, df):
        '''
        aggregrating generators together by technology, vintage, and region
        '''
        df = df.groupby(['i', 'v', 'r'], as_index = False).sum()
        df.drop('t', axis = 1, inplace = True)
        return df

    def apply_degradation(self, df):
        '''
        Degradation factors in the "degrade_annual" parameter are applied here
        '''
        df = get_prop(df, 'degrade_annual', merge_cols = ['i']).fillna(0)
        deg_rate = df.loc[0, 'rate']
        first_year = INPUTS['first_year'].get_data()
        year_list = list(range(self.next_year, first_year-1, -1))
        df_deg = pd.DataFrame(columns=['t', 'degrade'])
        df_deg['t'] = year_list
        df_deg.reset_index(inplace=True)
        df_deg.loc[:, 'degrade'] = (1-deg_rate) ** df_deg.loc[:, 'index']
        df = df.merge(df_deg, on='t', how='left')
        df['MW'] *= df['degrade']
        df.drop(['rate', 'index', 'degrade'], axis=1, inplace=True)
        return df

    def calc_emit_cost(self, df):
        '''
        Calculating the cost of emissions
        '''
        emit_rate = INPUTS['emit_rate'].get_data()
        emit_rate = self.filter_tech(emit_rate)
        ### Include non-CO2 GHG emissions based on global warming potential if specified
        if int(SwitchSettings.switches['gsw_annualcapco2e']):
            emit_rate_co2e = emit_rate.loc[emit_rate.e=='CO2'].merge(
                emit_rate.loc[emit_rate.e=='CH4'].drop(['e'], axis=1),
                on=['i','v','r'], how='left', suffixes=('','_CH4')
            ).fillna(0)
            emit_rate_co2e.emit_rate += (
                emit_rate_co2e.emit_rate_CH4 * float(SwitchSettings.switches['gsw_methanegwp']))
            emit_rate = pd.concat([
                emit_rate_co2e.drop(['emit_rate_CH4'], axis=1),
                emit_rate.loc[emit_rate.e != 'CO2']
            ], axis=0)
        ### Apply emissions price
        emit_price = INPUTS['emit_price'].get_data()
        emit_cost = emit_price.merge(emit_rate, on = ['e', 'r'])
        emit_cost['emit_cost'] = emit_cost['emit_rate'] * emit_cost['emit_price']
        emit_cost.drop(['emit_price', 'emit_rate'], axis = 1, inplace = True)
        emit_cost = emit_cost.groupby(['i', 'v', 'r'], as_index = False).sum()
        if not emit_cost.empty:
            df = pd.merge(left = df,
                          right = emit_cost,
                          on = ['i', 'v', 'r'],
                          how = 'outer'
                          ).fillna(0)
        else:
            df['emit_cost'] = 0
        return df

    def calc_fuel_cost(self):
        '''
        Calculating the fuel cost (in $/MWh) based on prices and heat rate
        '''
        df = self.get_fuel_price()
        df = get_prop(df, 'heat_rate', merge_cols = ['i', 'r'])
        df['fuel_cost'] = df['fuel_price'] * df['heat_rate']
        df = df[['i', 'v', 'r', 'fuel_cost']]
        return df

    def filter_tech(self, df, *args, **kwargs):
        '''
        filter a dataframe by technology
        '''
        techs = INPUTS['i_subsets'].get_data()
        df = df[df['i'].isin(techs[self.tech_key])]
        df.index = range(len(df))
        return df

    def format_avail_cap(self):
        '''
        Generator availability is equal to the max capacity multiplied by the
        "avail" parameter in ReEDS.
        '''
        df = self.max_cap.copy()
        df = get_prop(df, 'avail_cap', merge_cols = ['i', 'v'])
        df['MW'] *= df['avail']
        df = df[['i', 'v', 'r', 'szn', 'MW']]
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.avail_cap = df
        return df

    def format_daily_energy_budget(self):
        '''
        Daily energy budget for generation in Osprey. Most technologies have
        no daily energy budget. Those that do will be specified in their
        technology classes below.
        '''
        return None

    def format_energy_cap(self):
        '''
        Energy capacity only applies to storage technologies. This property
        Is defined for storage technologies below.
        '''
        return None

    def format_gen_cost(self):
        '''
        Generation cost is fuel cost plus VO&M
        (Also plus emissions costs if they exist)
        '''
        df = self.calc_fuel_cost()
        df_temp = INPUTS['cost_vom'].get_data()
        df_temp = self.filter_tech(df_temp)
        df = pd.merge(left = df,
                      right = df_temp,
                      on = ['i', 'v', 'r'],
                      how = 'outer'
                      ).fillna(0)
        df = self.calc_emit_cost(df)
        df['gen_cost'] = df['fuel_cost'] + df['cost_vom'] + df['emit_cost']
        df = df[['i', 'v', 'r', 'gen_cost']]
        df['gen_cost'] = df['gen_cost'].round(self.switches['decimals'])
        self.gen_cost = df
        return df

    def format_hourly_cfs_exist(self):
        '''
        VRE generators have scaling factors applied to their capacity in
        addition to the hourly capacity factors. Those modifications are
        included here so that these values can be multiplied by the hourly
        profiles to obtain VRE generation. This doesn't apply to most
        technologies, so it is defined in a class for VRE below.
        '''
        return None

    def format_hourly_cfs_marg(self):
        '''
        VRE generators have scaling factors applied to their capacity in
        addition to the hourly capacity factors. Those modifications are
        included here so that these values can be multiplied by the hourly
        profiles to obtain VRE generation. Scaling factors typically increase
        over time, so the values for new VRE builds differ from existing
        capacity, so we define marginal values for VRE here separate from the
        existing values.
        '''
        return None

    def format_max_cap(self):
        '''
        Generator capacity is separated by "init" and "inv". This is because
        retirements of "init" vintage generators is handled differently within
        ReEDS. After retirements are accounted for, all capacity is put into a
        single dataframe here.
        '''
        cap_init = self.get_init_cap()
        cap_inv = self.get_inv()
        df = pd.concat([cap_init, cap_inv], sort = False, ignore_index = True)
        if not df.empty:
            df = self.apply_degradation(df)
            df = self.agg_gens(df)
            df = df[df['MW'] >= self.min_gen_size]
            df.index = range(len(df))
        else:
            df = pd.DataFrame(columns = ['i', 'v', 'r', 'MW'])
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.max_cap = df
        return df

    def format_mingen(self):
        '''
        Set generator mingen levels. These are equal to the fractional mingen
        level in the WECC database multiplied by max capacity.
        '''
        df = self.max_cap.copy()
        wecc_data = INPUTS['wecc_data'].get_data()
        mingen = wecc_data[['i', 'Min Stable Level/cap']]
        df = df.merge(mingen, on = 'i', how = 'left').fillna(0)
        df['mingen'] = df['MW'] * df['Min Stable Level/cap']
        df = df[['i', 'v', 'r', 'mingen']]
        # Mingen is indexed by szn (because hydro mingen depends on szn)
        szns = INPUTS['szn'].get_data()
        df_allszn = pd.DataFrame(columns = ['i', 'v', 'r', 'szn', 'mingen'])
        for szn in szns['szn']:
            temp = df.copy()
            temp['szn'] = szn
            df_allszn = pd.concat([df_allszn, temp],
                                    sort = False,
                                    ignore_index = True)
        df_allszn['mingen'] = df_allszn['mingen'].round(
                                                self.switches['decimals'])
        self.mingen = df_allszn
        return df_allszn

    def format_ret_frac(self):
        '''
        Getting the fraction of capacity that is retiring due to being old
        or being scheduled for exogenous retirment.
        '''
        # Getting exogenous retirements that were not already retired by
        # the model endogenously.
        df = INPUTS['cap_init'].get_data()
        df_exog = INPUTS['cap_exog'].get_data()
        df = df.merge(df_exog, on=['i', 'v', 'r'], how='outer').fillna(0)
        df = self.filter_tech(df)
        exog_retire = df['MW'] > df['exog']
        df_ret = df[exog_retire].copy()
        df_ret['ret'] = df_ret['MW'] - df_ret['exog']
        df_ret['ret_frac'] = df_ret['ret'] / df_ret['MW']
        df_ret.drop(['MW', 'exog', 'ret'], axis = 1, inplace = True)
        df_ret['ret_frac'] = df_ret['ret_frac'].round(
                                                self.switches['decimals'])
        df_ret['t'] = self.next_year
        df_ret = df_ret[['i', 'v', 'r', 't', 'ret_frac']]
        self.ret_frac = pd.concat([self.ret_frac, df_ret],
                                    sort = False,
                                    ignore_index = True)
        '''
        Getting age-based retirements that were not already retired by the
        model endogenously.
        '''
        # Investments by ReEDS year
        df = INPUTS['cap_inv'].get_data()
        df = self.filter_tech(df)
        # Total retirements of "newv" (new vintage) generators
        df_ret = INPUTS['cap_ret'].get_data()
        df_ret = self.filter_tech(df_ret)
        # Retire capacity from oldest to newest
        if not df_ret.empty:
            df.loc[:, 'count'] = (
                df
                .groupby([c for c in ['i', 'v', 'r']])
                .cumcount()
                + 1
                )
            df = pd.merge(left=df,
                         right=df_ret,
                         on=['i', 'v', 'r'],
                         how='left'
                         ).fillna(0)
            df.loc[df['count'] == 1, 'Left to retire'] = \
                df.loc[df['count'] == 1, 'ret']
            df = df.sort_values(['v', 'i', 'r', 'count'], ignore_index = True)
            df.index = range(len(df))
            for i in range(0, len(df), 1):
                if i+1 < len(df):
                    if df.loc[i+1, 'count'] == 1 + df.loc[i, 'count']:
                        df.loc[i+1, 'Left to retire'] = (
                            df.loc[i, 'Left to retire']
                            - df.loc[i, 'MW']
                            )
                    if df.loc[i+1, 'Left to retire'] < 0:
                        df.loc[i+1, 'Left to retire'] = 0
                df.loc[i, 'MW'] -= df.loc[i, 'Left to retire']
        if not df.empty:
            df = df[df['MW'] > 0.01]
        df.index = range(len(df))
        df =  df[['i', 'v', 'r', 't', 'MW']]
        # Age-based retirements for the next solve year
        maxage = INPUTS['maxage'].get_data()
        df = df.merge(maxage, on = 'i', how = 'left')
        df['tretire'] = self.next_year - df['maxage']
        age_retire = df['tretire'] >= df['t']
        df_ret = df[age_retire].copy()
        df_ret.rename(columns = {'MW':'ret'}, inplace = True)
        df_ret = df_ret.merge(df, on = ['i', 'v', 'r', 't', 'maxage', 'tretire'])
        df_ret['ret_frac'] = df_ret['ret'] / df_ret['MW']
        df_ret['t'] = self.next_year
        df_ret = df_ret[['i', 'v', 'r', 't', 'ret_frac']]
        df_ret['ret_frac'] = df_ret['ret_frac'].round(
                                                self.switches['decimals'])
        self.ret_frac = pd.concat([self.ret_frac, df_ret],
                                    sort = False,
                                    ignore_index = True)
        return self.ret_frac

    def get_fuel_price(self):
        '''
        Most techs have endogenously determined marginal fuel prices.
        For technologies that have dynamic fuel prices, they will have
        their own get_fuel_price method defined below.
        '''
        df = INPUTS['fuel_price'].get_data()
        df = self.filter_tech(df)
        return df

    def get_init_cap(self):
        '''
        Getting the capacity of initv generators in ReEDS, accounting for
        retirements in the next solve year as defined by capacity_exog.
        Since these generators could also be retired by ReEDS endogenously
        depending on how GsW_Retire is set, we compare the initv capacity
        in the previous solve year with the capacity_exog numbers in the
        next solve year. Wherever capacity exog is less than the modeled
        initv capacity, replace the modeled capacity with the capacity_exog
        numbers. This accounts for prescribed retirements without double
        counting both endogenous and exogenous retirements.
        Also keep track of retired capacity so this can be sent back to ReEDS
        and the mingen difference from this capacity can be accounted for.
        '''
        df = INPUTS['cap_init'].get_data()
        df_exog = INPUTS['cap_exog'].get_data()
        df = df.merge(df_exog, on=['i', 'v', 'r'], how='outer').fillna(0)
        df = self.filter_tech(df)
        exog_retire = df['MW'] > df['exog']
        df.loc[exog_retire,'MW'] = df.loc[exog_retire,'exog']
        df.drop('exog', axis = 1, inplace = True)
        df = df[df['MW'] > 0]
        df.index = range(len(df))
        first_year = INPUTS['first_year'].get_data()
        df['t'] = first_year
        return df[['i', 'v', 'r', 't', 'MW']]

    def get_inv(self):
        '''
        Getting capacity of investments, accounting first for endogenous
        retirements, then age-based retirements before the next solve year.
        Also keep track of newly-retired capacity (age-based retirements)
        so this can be sent back to ReEDS and the mingen difference from
        this capacity can be accounted for.
        '''
        # Investments by ReEDS year
        df = INPUTS['cap_inv'].get_data()
        df = self.filter_tech(df)
        # Total retirements of "newv" (new vintage) generators
        df_ret = INPUTS['cap_ret'].get_data()
        df_ret = self.filter_tech(df_ret)
        # Retire capacity from oldest to newest
        if not df_ret.empty:
            df.loc[:, 'count'] = (
                df
                .groupby([c for c in ['i', 'v', 'r']])
                .cumcount()
                + 1
                )
            df = pd.merge(left=df,
                         right=df_ret,
                         on=['i', 'v', 'r'],
                         how='left'
                         ).fillna(0)
            df.loc[df['count'] == 1, 'Left to retire'] = \
                df.loc[df['count'] == 1, 'ret']
            df = df.sort_values(['v', 'i', 'r', 'count'], ignore_index = True)
            df.index = range(len(df))
            for i in range(0, len(df), 1):
                if i+1 < len(df):
                    if df.loc[i+1, 'count'] == 1 + df.loc[i, 'count']:
                        df.loc[i+1, 'Left to retire'] = (
                            df.loc[i, 'Left to retire']
                            - df.loc[i, 'MW']
                            )
                    if df.loc[i+1, 'Left to retire'] < 0:
                        df.loc[i+1, 'Left to retire'] = 0
                df.loc[i, 'MW'] -= df.loc[i, 'Left to retire']
        df.index = range(len(df))
        df =  df[['i', 'v', 'r', 't', 'MW']]
        # Age-based retirements for the next solve year
        maxage = INPUTS['maxage'].get_data()
        df = df.merge(maxage, on = 'i', how = 'left')
        df['tretire'] = self.next_year - df['maxage']
        age_retire = df['tretire'] >= df['t']
        df = df[~age_retire]
        df.index = range(len(df))
        return df[['i', 'v', 'r', 't', 'MW']]

    def prep_data(self, key):
        '''
        Preparing data based on key provided
        '''
        if key == 'avail_cap':
            result = self.format_avail_cap()
        elif key == 'daily_energy_budget':
            result = self.format_daily_energy_budget()
        elif key == 'energy_cap':
            result = self.format_energy_cap()
        elif key == 'gen_cost':
            result = self.format_gen_cost()
        elif key == 'hourly_cfs_exist':
            result = self.format_hourly_cfs_exist()
        elif key == 'hourly_cfs_marg':
            result = self.format_hourly_cfs_marg()
        elif key == 'max_cap':
            result = self.format_max_cap()
        elif key == 'mingen':
            result = self.format_mingen()
        elif key == 'ret_frac':
            result = self.format_ret_frac()
        return result


class BiopowerData(TechData):
    '''
    Handling properties specific to biopwer
    '''

    def calc_fuel_cost(self):
        '''
        Calculating the fuel cost (in $/MWh) based on prices and heat rate.
        Biopower fuel prices are defined only by region.
        '''
        df = self.get_fuel_price()
        df = get_prop(df, 'heat_rate', merge_cols = 'r', method = 'right')
        df = self.filter_tech(df)
        df['fuel_cost'] = df['fuel_price'] * df['heat_rate']
        df = df[['i', 'v', 'r', 'fuel_cost']]
        return df

    def get_fuel_price(self):
        '''
        Biopower has a supply curve for fuel prices. Using the fuel price from
        the marginal supply curve bin used in ReEDS. If biopower is not used,
        the model is set up to send the price from the first supply curve bin.
        (see d3_augur_data_dump.gms)
        '''
        df = INPUTS['fuel_price_biopower'].get_data()
        df = df.sort_values('r', ignore_index = True)
        return df


class CanImportData(TechData):
    '''
    Handling properties specific to can-imports
    '''

    def format_max_cap(self):
        '''
        Capacity of can-imports is defined exogenously for ReEDS. And there
        is no need to track retired capacity of can-imports.
        '''
        df = INPUTS['can_imports_cap'].get_data()
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.max_cap = df
        return df

    def format_daily_energy_budget(self):
        '''
        Can-imports have seasonal energy budgets in ReEDS. We assume that the
        energy budget for each season is spread out equally across each day.
        '''
        df = INPUTS['can_imports_szn'].get_data()
        hours = INPUTS['hours'].get_data()
        h_szn = INPUTS['h_szn'].get_data()
        hours = hours.merge(h_szn, on = 'h')
        hours_szn = hours.groupby('szn', as_index = False).sum()
        df = df.merge(hours_szn, on = 'szn')
        df['MWh'] = 24 * df['imports'] / df['hours']
        df['i'] = 'can-imports'
        df['v'] = 'init-1'
        df = map_szn_to_day(df)
        df = df[['i', 'v', 'r', 'd', 'MWh']]
        # Ensuring we round down to avoid infeasibilities
        cap = self.avail_cap.copy()
        cap = get_prop(cap, 'd_szn', merge_cols = ['szn'])
        df = df.merge(cap, on = ['i', 'v', 'r', 'd'])
        df['MW'] *= 24
        cap_check = df['MW'] < df['MWh']
        df.loc[cap_check, 'MWh'] = df.loc[cap_check, 'MW']
        df.drop(['szn', 'MW'], axis = 1, inplace = True)
        df['MWh'] = df['MWh'].round(self.switches['decimals'])
        self.daily_energy_budget = df
        return df

    def format_gen_cost(self):
        '''
        Can-imports are assigned the same generation cost as domestic hydro
        '''
        ### GRABBING GEN_COST FOR DOMESTIC HYDRO
        df_cost = GEN_TECHS['hydro_d'].format_gen_cost()
        ### GRABBING GEN COST FOR DOMESTIC HYDRO
        cost = round(df_cost['gen_cost'].mean(), self.switches['decimals'])
        df = self.max_cap.copy()
        df.drop('MW', axis = 1, inplace = True)
        df['gen_cost'] = cost
        self.gen_cost = df
        return df

    def format_ret_frac(self):
        '''
        Ignoring ret_frac for can-imports
        '''
        return None


class ConsumeData(TechData):
    '''
    Class for H2 and DAC technologies
    '''

    # Don't drop any H2 or DAC capacity
    min_gen_size = 0


class DispatchableHydroData(TechData):
    '''
    Handling properties specific to dispatchable hydro
    '''

    def format_daily_energy_budget(self):
        '''
        Dispatchable hydro has seasonal energy budgets in ReEDS. We assume
        that the energy budget for each season is spread out equally across
        each day in Osprey.
        '''
        df = self.avail_cap.copy()
        df = get_prop(df, 'cap_hyd_szn_adj', merge_cols = ['i', 'r', 'szn'])
        df = get_prop(df, 'm_cf_szn', merge_cols = ['i', 'v', 'r', 'szn'])
        # Don't let hydro CF exceed 1
        cf_check = df['seacf'] * df['m_cf_szn'] > 1
        df.loc[cf_check, ['seacf', 'm_cf_szn']] = 1
        df['MWh'] = df['MW'] * \
                    df['seacf'] * \
                    df['m_cf_szn'] * \
                    24
        df = map_szn_to_day(df)
        df = df[['i', 'v', 'r', 'd', 'MWh']]
        df['MWh'] = df['MWh'].round(self.switches['decimals'])
        self.daily_energy_budget = df
        return df

    def format_mingen(self):
        '''
        Setting the mingen level of hydro equal to the seasonal average CF
        multiplied by the minload parameter.
        '''
        df = self.avail_cap.copy()
        df = get_prop(df, 'cap_hyd_szn_adj', merge_cols = ['i', 'r', 'szn'])
        df = get_prop(df, 'm_cf_szn', merge_cols = ['i', 'v', 'r', 'szn'])
        # Don't let hydro CF exceed 1
        cf_check = df['seacf'] * df['m_cf_szn'] > 1
        df.loc[cf_check, ['seacf', 'm_cf_szn']] = 1
        df = get_prop(df, 'minloadfrac', merge_cols = ['i', 'r', 'szn'])
        df['mingen'] = df['MW'] * \
                       df['seacf'] * \
                       df['m_cf_szn'] * \
                       df['minloadfrac']
        df = df[['i', 'v', 'r', 'szn', 'mingen']]
        df['mingen'] = df['mingen'].round(self.switches['decimals'])
        self.mingen = df
        return df


class NonDispatchableHydroData(TechData):
    '''
    Handling properties specific to hydro
    '''

    def format_avail_cap(self):
        '''
        Setting the mingen level of hydro equal to the seasonal average CF
        multiplied by the minload parameter.
        '''
        df = self.max_cap.copy()
        df = get_prop(df, 'avail_cap', merge_cols = ['i', 'v'])
        df = get_prop(df, 'm_cf_szn', merge_cols = ['i', 'v', 'r', 'szn'])
        df['MW'] = df['MW'] * \
                       df['avail'] * \
                       df['m_cf_szn']
        df = df[['i', 'v', 'r', 'szn', 'MW']]
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.mingen = df
        return df

    def format_mingen(self):
        '''
        Ignoring mingen for non-dispatchable hydro
        '''
        pass


class NGData(TechData):
    '''
    Handling properties specific to natural gas
    '''

    def calc_fuel_cost(self):
        '''
        Calculating the fuel cost (in $/MWh) based on prices and heat rate
        NG fuel prices are defined only by region.
        '''
        df = self.get_fuel_price()
        df = get_prop(df, 'heat_rate', merge_cols = 'r', method = 'right')
        df = self.filter_tech(df)
        df['fuel_cost'] = df['fuel_price'] * df['heat_rate']
        df = df[['i', 'v', 'r', 'fuel_cost']]
        return df

    def get_fuel_price(self):
        '''
        There are several options for determning NG fuel prices in ReEDS.
        Whatever method is used, NG fuel prices are stored separately.
        '''
        return INPUTS['ng_price'].get_data()


class PVBData(TechData):
    '''
    Handling properties specific to PVB
    NOTE that PVB generators are simply added to the upv capacity of the same
    resource class. The "max_cap" dataframe in the "GEN_DATA" dictionary will
    have the combined capacity for both UPV and battery, but the "max_cap"
    attribute in the "GEN_TECHS" dictionary will have the separate capacity
    for each (e.g. GEN_TECHS['pvb'].max_cap with have the PVB contribution to
    upv and battery).
    '''

    # Minimum PVB generator size (MW)
    # We do not drop VRE capacity in Osprey
    min_gen_size = 0

    def agg_gens_bat(self, df):
        '''
        Storage generators are aggregated together over vintage for
        simplified representation in Osprey.
        '''
        df = df.groupby(['i', 'r'], as_index = False).sum()
        df['v'] = 'new1'
        return df[['i', 'v', 'r', 'MW']]

    def agg_gens_pv(self, df):
        '''
        Aggregrating generators together by tech, resource class, and region
        just like is done for PV below.
        '''
        df = df.groupby(['i', 'r'], as_index = False).sum()
        df.drop('t', axis = 1, inplace = True)
        return df

    def apply_bat_cap_ratio(self, df):
        '''
        PVB has a battery capacity ratio defined by the bcr parameter. The
        battery capacity component of PVB is reduced by this factor.
        '''
        df = get_prop(df, 'bcr', merge_cols = ['i'])
        df['MW'] *= df['bcr']
        df.drop('bcr', axis = 1, inplace = True)
        pvb_dur = self.switches['gsw_pvb_dur']
        df['i'] = 'battery_' + pvb_dur
        return df

    def apply_cf_adj(self, df):
        '''
        Applying the cf adjustment to the PV capacity component of PVB.
        '''
        df = get_prop(df, 'cf_adj', merge_cols = ['i', 'v', 't'])
        df['MW'] *= df['CF']
        df.drop('CF', axis = 1, inplace = True)
        return df

    def filter_for_bats(self, df):
        '''
        Filtering for just battery capacity for the battery capacity
        component of PVB.
        '''
        self.tech_key = 'battery'
        df = self.filter_tech(df)
        self.tech_key = 'pvb'
        return df

    def format_avail_cap(self):
        '''
        Need to remove pv capacity from pvb avail_cap
        '''
        df = self.max_cap.copy()
        df = self.filter_for_bats(df)
        df = get_prop(df, 'avail_cap', merge_cols = ['i', 'v'])
        df['MW'] *= df['avail']
        df = df[['i', 'v', 'r', 'szn', 'MW']]
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.avail_cap = df
        return df

    def format_energy_cap(self):
        '''
        Format the energy capacity of the battery component of PVB
        '''
        df = self.max_cap.copy()
        df = self.filter_for_bats(df)
        df = get_prop(df, 'storage_duration', merge_cols = ['i'])
        df['MWh'] = df['MW'] * df['duration']
        df = df[['i', 'v', 'r', 'MWh']]
        df['MWh'] = df['MWh'].round(self.switches['decimals'])
        self.energy_cap = df
        return df

    def format_hourly_cfs_exist(self):
        '''
        '''
        cap_init = self.get_init_cap()
        cap_inv = self.get_inv()
        df = pd.concat([cap_init, cap_inv],
                        sort=False,
                        ignore_index=True)
        if not df.empty:
            df = self.apply_degradation(df)
            df = self.apply_cf_adj(df)
            df = self.agg_gens_pv(df)
            df = self.merge_in_resources(df)
        else:
            df = pd.DataFrame(columns = ['i', 'r', 'resource', 'MW'])
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.hourly_cfs_exist = df
        return df
    
    def format_hourly_cfs_marg(self):
        '''
        This property includes the cf adjustment for VRE generators
        so it can be multiplied by the hourly profiles to get
        generation but is specific to the vintage of VRE that would
        be deployed in the next solve year if there are investments.
        '''
        resources = INPUTS['resources'].get_data()
        resources = self.filter_tech(resources)
        df = INPUTS['cf_adj'].get_data()
        df.rename(columns = {'CF':'cf_marg'}, inplace = True)
        newv = INPUTS['vintage_inv'].get_data()
        newv = newv[newv['t'] == self.next_year]
        newv = self.filter_tech(newv)
        df = df.merge(newv, on = ['i', 'v', 't'], how = 'right')
        df = df.merge(resources, on = 'i', how = 'right')
        df['cf_marg'].fillna(1, inplace = True)
        df = df[['i', 'r', 'resource', 'cf_marg']]

        self.hourly_cfs_marg = df
        return df

    def format_max_cap(self):
        '''
        Adding pvb capacity to battery and upv as defualt.
        '''
        cap_init = self.get_init_cap()
        cap_inv = self.get_inv()
        df = pd.concat([cap_init, cap_inv], sort = False, ignore_index = True)
        if not df.empty:
            df_bat = self.apply_bat_cap_ratio(df)
            df_bat = self.agg_gens_bat(df_bat)
            df_pv = self.apply_degradation(df)
            df_pv = self.agg_gens(df_pv)
            df = pd.concat([df_bat, df_pv], sort = False)
        else:
            df = pd.DataFrame(columns = ['i', 'v', 'r', 'MW'])
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.max_cap = df
        return df

    def merge_in_resources(self, df):
        '''
        Merging in resources for mapping resources to profiles
        '''
        resources = INPUTS['resources'].get_data()
        resources = self.filter_tech(resources)
        df = df.merge(resources, on = ['i', 'r'], how = 'right').fillna(0)
        df = df[['i', 'r', 'resource', 'MW']]
        return df

    def format_mingen(self):
        '''
        Ignoring mingen for PVB generators
        '''
        return None


class StorageData(TechData):
    '''
    Handling properties specific to storage
    '''

    # Minimum storage generator size (MW)
    # We use a smaller minimum size for storage technologies
    min_gen_size = 1

    def agg_gens(self, df):
        '''
        Storage generators are aggregated together over vintage.
        '''
        df = df.groupby(['i', 'r'], as_index = False).sum()
        df['v'] = 'new1'
        return df[['i', 'v', 'r', 'MW']]

    def format_avail_cap(self):
        '''
        Generator availability is equal to the max capacity multiplied by the
        "avail" parameter in ReEDS.
        Storage avail capacity is handled separately because it cannot be
        merged on the 'v' column because all storage vintage is hard-coded to
        be 'new1'
        '''
        df = self.max_cap.copy()
        avail = INPUTS['avail_cap'].get_data()
        avail = self.filter_tech(avail)
        avail = avail.groupby(['i', 'szn'], as_index = False).mean()
        avail['v'] = 'new1'
        df = df.merge(avail, on = ['i', 'v'])
        df['MW'] *= df['avail']
        df = df[['i', 'v', 'r', 'szn', 'MW']]
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.avail_cap = df
        return df

    def format_energy_cap(self):
        '''
        Fromat the energy capacity of storage generators
        '''
        df = self.max_cap.copy()
        df = get_prop(df, 'storage_duration', merge_cols = ['i'])
        df['MWh'] = df['MW'] * df['duration']
        df = df[['i', 'v', 'r', 'MWh']]
        df['MWh'] = df['MWh'].round(self.switches['decimals'])
        self.energy_cap = df
        return df

class PSHData(StorageData):
    '''
    Handling properties specific to pumped-hydro
    '''

    def agg_gens(self, df):
        '''
        Storage generators are aggregated together over vintage.
        '''
        df['i'] = 'pumped-hydro'
        df = df.groupby(['i', 'r'], as_index = False).sum()
        df['v'] = 'new1'
        return df[['i', 'v', 'r', 'MW']]


class VREData(TechData):
    '''
    Handling properties specific to VRE
    '''

    # Minimum VRE generator size (MW)
    # We do not drop VRE capacity in Osprey
    min_gen_size = 0

    def agg_gens_for_cfs(self, df):
        '''
        Aggregate capacity over vintage for determining CFs
        '''
        df = df.groupby(['i', 'r'], as_index = False).sum()
        if 't' in df.columns: df.drop('t', axis = 1, inplace = True)
        return df

    def apply_cf_adj(self, df):
        '''
        Applying the CF adjustment to VRE generators
        '''
        df = get_prop(df, 'cf_adj', merge_cols = ['i', 'v', 't'])
        df['MW'] *= df['CF']
        df.drop('CF', axis = 1, inplace = True)
        return df

    def format_avail_cap(self):
        '''
        Ignoring available capacity for VRE generators
        '''
        return None

    def format_mingen(self):
        '''
        Ignoring mingen for VRE generators
        '''
        return None

    def merge_in_resources(self, df):
        '''
        Merging in resource column for mapping to hourly CF profiles
        '''
        resources = INPUTS['resources'].get_data()
        resources = self.filter_tech(resources)
        df = df.merge(resources, on = ['i', 'r'], how = 'right').fillna(0)
        return df


class CSPNSData(VREData):
    '''
    Handling properties specific to CSPNS
    NOTE that cspns generators are simply added to the upv capacity of the best
    resource class in whatever region it is in. The "max_cap" dataframe in the
    "GEN_DATA" dictionary will have the combined capacity, but the "max_cap"
    attribute in the "GEN_TECHS" dictionary will have the separate capacity
    for each (e.g. GEN_TECHS['cspns'].max_cap with have the cspns contribution)
    '''

    def agg_gens(self, df, rs_to_r = True):
        '''
        CSP generators need to be aggregated from the "s" regions to the "p"
        regions.
        '''
        df = super().agg_gens(df)
        if rs_to_r: df = agg_rs_to_r(df)
        return df

    def assign_upv_tech(self, df):
        '''
        Assigning the upv tech of the best class as the cspns tech
        '''
        i_new = self.get_best_upv_class()
        i_new.rename(columns = {'i':'i_new'}, inplace = True)
        df = df.merge(i_new, on = 'r', how = 'left')
        df.drop('i', axis = 1, inplace = True)
        df.rename(columns = {'i_new':'i'}, inplace = True)
        df = df[['i', 'v', 'r', 'MW']]
        return df

    def format_hourly_cfs_exist(self):
        '''
        Generator capacity is separated by "init" and "inv". This is because
        retirements of "init" vintage generators is handled differently within
        ReEDS.
        Defining this here for cspns so the additional "assign_upv_tech" method
        can be called.
        '''
        cap_init = self.get_init_cap()
        cap_inv = self.get_inv()
        df = pd.concat([cap_init, cap_inv], sort = False, ignore_index = True)
        if not df.empty:
            df = self.apply_degradation(df)
            df = self.apply_cf_adj(df)
            df = self.agg_gens(df)
            df = self.assign_upv_tech(df)
            df = self.agg_gens_for_cfs(df)
            df = self.merge_in_resources(df)
            df = df[df['MW'] >= self.min_gen_size]
            df = df[['i', 'r', 'resource', 'MW']]
            df.index = range(len(df))
        else:
            df = pd.DataFrame(columns = ['i', 'v', 'r', 'MW'])
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.hourly_cf_exist = df
        return df

    def format_max_cap(self):
        '''
        Generator capacity is separated by "init" and "inv". This is because
        retirements of "init" vintage generators is handled differently within
        ReEDS.
        Defining this here for cspns so the additional "assign_upv_tech" method
        can be called.
        '''
        cap_init = self.get_init_cap()
        cap_inv = self.get_inv()
        df = pd.concat([cap_init, cap_inv], sort = False, ignore_index = True)
        if not df.empty:
            df = self.apply_degradation(df)
            df = self.agg_gens(df)
            df = self.assign_upv_tech(df)
            df = df[df['MW'] >= self.min_gen_size]
            df.index = range(len(df))
        else:
            df = pd.DataFrame(columns = ['i', 'v', 'r', 'MW'])
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.max_cap = df
        return df

    def get_best_upv_class(self):
        '''
        csp-ns is assigned to the best UPV class in it's region
        '''
        resources = INPUTS['resources'].get_data()
        self.tech_key = 'upv'
        resources_upv = self.filter_tech(resources)
        self.tech_key = 'csp_nostorage'
        resources_upv_best = resources_upv[['i', 'r']].drop_duplicates(
                                                    subset='r',
                                                    keep='last',
                                                    ignore_index = True)
        return resources_upv_best

    def merge_in_resources(self, df):
        '''
        Merging in resource column for mapping to hourly CF profiles
        '''
        resources = INPUTS['resources'].get_data()
        self.tech_key = 'upv'
        resources = self.filter_tech(resources)
        self.tech_key = 'csp_nostorage'
        df = df.merge(resources, on = ['i', 'r'], how = 'left').fillna(0)
        return df


class PVWindCSPData(VREData):
    '''
    Handling properties specific to PV and wind
    '''

    def format_hourly_cfs_exist(self):
        '''
        This property includes the cf adjustment for VRE generators
        so it can be multiplied by the hourly profiles to get
        generation.
        '''
        cap_init = self.get_init_cap()
        cap_inv = self.get_inv()
        df = pd.concat([cap_init, cap_inv], sort = False, ignore_index = True)
        if not df.empty:
            df = self.apply_degradation(df)
            df = self.apply_cf_adj(df)
            df = self.agg_gens_for_cfs(df)
            df = self.merge_in_resources(df)
            df = df[['i', 'r', 'resource', 'MW']]
        else:
            df = pd.DataFrame(columns = ['i', 'v', 'r', 'MW'])
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.hourly_cfs_exist = df
        return df

    def format_hourly_cfs_marg(self):
        '''
        This property includes the cf adjustment for VRE generators
        so it can be multiplied by the hourly profiles to get
        generation but is specific to the vintage of VRE that would
        be deployed in the next solve year if there are investments.
        '''
        resources = INPUTS['resources'].get_data()
        resources = self.filter_tech(resources)
        df = INPUTS['cf_adj'].get_data()
        df.rename(columns = {'CF':'cf_marg'}, inplace = True)
        newv = INPUTS['vintage_inv'].get_data()
        newv = newv[newv['t'] == self.next_year]
        newv = self.filter_tech(newv)
        df = df.merge(newv, on = ['i', 'v', 't'], how = 'right')
        df = df.merge(resources, on = 'i', how = 'right')
        df['cf_marg'].fillna(1, inplace = True)
        df = df[['i', 'r', 'resource', 'cf_marg']]

        self.hourly_cfs_marg = df
        return df


class DRData(VREData):
    '''
    Handling properties specific to DR
    '''

    def agg_gens(self, df):
        '''
        Storage generators are aggregated together over vintage.
        '''
        df = df.groupby(['i', 'r'], as_index = False).sum()
        df['v'] = 'new1'
        return df[['i', 'v', 'r', 'MW']]

    def format_avail_cap(self):
        '''
        Generator availability is equal to the max capacity multiplied by the
        "avail" parameter in ReEDS.
        DR avail capacity mirrors storage, as these resources are modeled similarly
        '''
        df = self.max_cap.copy()
        avail = INPUTS['avail_cap'].get_data()
        avail = self.filter_tech(avail)
        avail = avail.groupby(['i', 'szn'], as_index = False).mean()
        avail['v'] = 'new1'
        df = df.merge(avail, on = ['i', 'v'])
        df['MW'] *= df['avail']
        df = df[['i', 'v', 'r', 'szn', 'MW']]
        df['MW'] = df['MW'].round(self.switches['decimals'])
        self.avail_cap = df
        return df


# Dictionary where each entry is a different generator property. All
# generation technologies are combined into a single dataframe for each
# entry. Note max_cap is done first because that information is needed for some
# of the other properties.
GEN_DATA = {
    'max_cap':             pd.DataFrame(columns = ['i', 'v', 'r', 'MW']),
    'avail_cap':           pd.DataFrame(columns = ['i', 'v', 'r', 'szn', 'MW']),
    'daily_energy_budget': pd.DataFrame(columns = ['i', 'v', 'r', 'd', 'MWh']),
    'energy_cap':          pd.DataFrame(columns = ['i', 'v', 'r', 'MWh']),
    'gen_cost':            pd.DataFrame(columns = ['i', 'v', 'r', 'gen_cost']),
    'hourly_cfs_exist':    pd.DataFrame(columns = ['i', 'r', 'resource', 'MW']),
    'hourly_cfs_marg':     pd.DataFrame(columns = ['i', 'r', 'resource', 'cf_marg']),
    'mingen':              pd.DataFrame(columns = ['i', 'v', 'r', 'szn', 'mingen']),
    'ret_frac':            pd.DataFrame(columns = ['i', 'v', 'r', 't', 'ret_frac'])
}

# Dictionary where each entry is a generation technology and the values are
# the class defined above that corresponds to each technology.
GEN_TECHS = {
    'battery':     StorageData('battery'),
    'biopower':    BiopowerData('bio'),
    'can-imports': CanImportData('canada'),
    'coal':        TechData('coal'),
    'consume':     ConsumeData('consume'),
    'csp':         PVWindCSPData('csp_storage'),
    'cspns':       CSPNSData('csp_nostorage'),
    'distpv':      PVWindCSPData('distpv'),
    'dr1':         DRData('dr1'),
    'dr2':         DRData('dr2'),
    'dupv':        PVWindCSPData('dupv'),
    'gas':         NGData('gas'),
    'geothermal':  TechData('geo'),
    'hydro_d':     DispatchableHydroData('hydro_d'),
    'hydro_nd':    NonDispatchableHydroData('hydro_nd'),
    'lfill-gas':   TechData('lfill'),
    'nuclear':     TechData('nuclear'),
    'o-g-s':       NGData('ogs'),
    'psh':         PSHData('psh'),
    'pvb':         PVBData('pvb'),
    're-ct':       TechData('re_ct'),
    'upv':         PVWindCSPData('upv'),
    'wind':        PVWindCSPData('wind'),
}
#%%
