# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 19:31:06 2021

@author: afrazier
"""

import gdxpds
import os
import pandas as pd

from ReEDS_Augur.utility.switchsettings import SwitchSettings


class AugurInput(SwitchSettings):
    '''
    Class for all Augur inputs. Some come from directly from ReEDS and are
    located in that year's .gdx file, others come from .csv files in the
    inputs_case folder.
    All inputs are loaded here so that they can be accessed in an organized
    way and so things can be standardized as soon as they are read in. E.g.
    all inputs are filtered by rfeas as soon as they are read in so that if
    you are running a spatial subset of ReEDS there are no stray regions
    in any of the parameters that are not included in the ReEDS solve. Also
    technology types can be standardized i.e. if you are running ReEDS with
    the water cooling switch on we can be sure that all inputs have the
    cooling tech appended to the technology name wherever applicable.
    '''

    def get_data(self, *args, **kwargs):

        def get_r_rs_feas():
            '''
            Get the r and rs regions that are included in the model
            '''
            rfeas = INPUTS['rfeas'].get_data()
            r_rs = INPUTS['r_rs'].get_data()
            r_rs_feas = rfeas.merge(r_rs, on = 'r', how='left')
            r_rs_feas = r_rs_feas['r'].drop_duplicates().tolist() + \
                                    r_rs_feas['rs'].tolist()
            return r_rs_feas

        def map_water_cooling_techs(df):
            '''
            Map generic techs to techs including water cooling information.
            '''
            watertechs = INPUTS['watertechs'].get_data()
            for col in watertechs.columns:
                watertechs[col] = watertechs[col].str.lower()
            df_temp = df[~df['i'].isin(watertechs['ii'])]
            df.rename(columns={'i':'ii'}, inplace=True)
            df = watertechs.merge(df, on = 'ii')
            df.drop('ii', axis = 1, inplace = True)
            df = pd.concat([df, df_temp], sort = False, ignore_index = True)
            df = df.drop_duplicates()
            df.index = range(len(df))
            return df

        def map_upgrades(df):
            '''
            Map generic techs to techs including upgrades e.g. start costs
            for coal-ccs will be assigned to coal-igcc_coal-ccs
            '''
            upgrades = INPUTS['upgrades'].get_data()
            for col in upgrades.columns:
                upgrades[col] = upgrades[col].str.lower()
            df_temp = df[~df['i'].isin(upgrades['ii'])]
            df.rename(columns={'i':'ii'}, inplace=True)
            df = upgrades.merge(df, on = 'ii')
            df.drop('ii', axis = 1, inplace = True)
            df = pd.concat([df, df_temp], sort = False, ignore_index = True)
            df = df.drop_duplicates()
            df.index = range(len(df))
            return df

        if self.df is None:
            self.df = self.read_data(*args, **kwargs)
            if self.col_names: self.df.columns = self.col_names
            if 'drop' in self.df.columns:
                self.df.drop('drop', axis=1, inplace=True)
            if 'i' in self.df.columns:
                self.df.i = self.df.i.str.lower()
                if self.switches['gsw_watermain'] == '1':
                    self.df = map_water_cooling_techs(self.df)
                if self.switches['gsw_upgrades'] == '1':
                    self.df = map_upgrades(self.df)
            if 'r' in self.df.columns:
                rfeas = get_r_rs_feas()
                self.df = self.df[self.df['r'].isin(rfeas)]
            if 'h' in self.df.columns:
                self.df.h = self.df.h.str.lower()
            if 't' in self.df.columns:
                self.df.t = self.df.t.astype(int)
            self.df.index = range(len(self.df))
        return self.df.copy()


class H5Input(AugurInput):
    '''
    Class for grabbing data from .h5 files.
    '''

    def __init__(self, file, col_names):
        self.file = file
        self.col_names = col_names
        self.df = None

    def read_data(self, *args, **kwargs):
        '''
        Get data from a .h5 file
        '''
        if self.df is None:
            self.df = pd.read_hdf(self.file)
        return self.df


class LoadData(H5Input):
    '''
    Class for load because load can be stored differently when EFS or climate
    profiles are used
    '''
    def read_data(self, *args, **kwargs):
        if self.df is None:
            super().read_data()
            # Filter for proper data year here if EFS load profiles are used
            if self.switches['gsw_efs1_allyearload'] != 'default':
                self.df = self.df.loc[
                    (self.next_year if SwitchSettings.switches['osprey_load_year'] == 'next'
                     else self.prev_year)
                ]
        return self.df


class LoadDataWithSwitch(LoadData):
    '''
    Class for year-specific load files
    '''
    def read_data(self, suffix, *args, **kwargs):
        if self.df is None:
            self.df = pd.read_hdf(self.file + str(suffix) + '.h5')
            # Filter for proper data year here if EFS load profiles are used
            if self.switches['gsw_efs1_allyearload'] != 'default':
                self.df = self.df.loc[
                    (self.next_year if SwitchSettings.switches['osprey_load_year'] == 'next'
                     else self.prev_year)
                ]
        return self.df


class CSVInput(AugurInput):
    '''
    Class for grabbing data from .csv files.
    '''

    def __init__(self, file, col_names):
        self.file = file
        self.col_names = col_names
        self.df = None

    def read_data(self, *args, **kwargs):
        '''
        Get data from a csv file
        '''
        if self.df is None:
            self.df = pd.read_csv(self.file)
        return self.df


class CSVInputWithSwitch(AugurInput):
    '''
    Class for grabbing data from .csv files that have a suffix appended to the
    end of the file name.
    '''

    def __init__(self, file, col_names):
        self.file = file
        self.col_names = col_names
        self.df = None

    def read_data(self, suffix, *args, **kwargs):
        '''
        Get data from a csv file.
        Note that a suffix is required (e.g. the year for any Osprey outputs).
        '''
        if self.df is None:
            self.df = pd.read_csv(self.file + str(suffix) + '.csv')
        return self.df


class GDXInput(AugurInput):
    '''
    Class for grabbing data from the Augur input .gdx file from ReEDS.
    '''
    def __init__(self, key, col_names):
        self.key = key
        self.col_names = col_names
        self.df = None

    def read_data(self):
        '''
        Get data from the gdx file.
        Note that a suffix is required (e.g. the year for any Osprey outputs).
        '''
        if self.df is None:
            self.df = gdxpds.to_dataframe(self.gdx_file,
                                          self.key)[self.key]
        return self.df


class GDXValue(GDXInput):
    '''
    ReEDS input property with a single value
    '''
    def get_data(self):
        df = super().get_data()
        value = df.values[0][0]
        return value


class TechMapping(GDXInput):
    '''
    Class for reading in tech mapping sets.
    '''
    def get_data(self, *args, **kwargs):

        def get_r_rs_feas():
            '''
            Get the r and rs regions that are included in the model
            '''
            rfeas = INPUTS['rfeas'].get_data()
            r_rs = INPUTS['r_rs'].get_data()
            r_rs_feas = rfeas.merge(r_rs, on = 'r', how='left')
            r_rs_feas = r_rs_feas['r'].drop_duplicates().tolist() + \
                                    r_rs_feas['rs'].tolist()
            return r_rs_feas

        if self.df is None:
            self.df = self.read_data(*args, **kwargs)
            if self.col_names: self.df.columns = self.col_names
            if 'drop' in self.df.columns:
                self.df.drop('drop', axis=1, inplace=True)
            if 'i' in self.df.columns:
                self.df.loc[:, 'i'] = self.df.loc[:, 'i'].str.lower()
            if 'r' in self.df.columns:
                rfeas = get_r_rs_feas()
                self.df = self.df[self.df['r'].isin(rfeas)]
            if 'h' in self.df.columns:
                self.df.loc[:, 'h'] = self.df.loc[:, 'h'].str.lower()
            if 't' in self.df.columns:
                self.df.loc[:, 't'] = self.df.loc[:, 't'].astype(int)
            self.df.index = range(len(self.df))
        return self.df.copy()


class TechTypes(GDXInput):
    '''
    Create a dictionary of technology subsets
    '''
    def get_data(self):
        if self.df is None:
            df = super().get_data()
            tech_dict = {}
            for cat in df['tech_cat'].drop_duplicates():
                tech_dict[cat.lower()] = df[df['tech_cat']==cat]['i'].tolist()
            for i in df['i']:
                if i not in tech_dict.keys():
                    tech_dict[i] = [i]
            self.df = tech_dict.copy()
        return self.df

'''
All data needed for ReEDS-to-PLEXOS is included here. Most data comes from the
inputs.gdx file in the inputs_case folder. Some data comes from .csv files in
the inputs_case folder.
'''
INPUTS = {
    'avail_cap': GDXInput(
        'avail_filt', ['i','v','szn','avail']),
    'bcr': GDXInput(
        'bcr', ['i','bcr']),
    'bir_pvb_config': GDXInput(
        'bir_pvb_config', ['pvb_config','bir']),
    'can_exports': GDXInput(
        'can_exports_h_filt', ['r', 'h', 'MW']),
    'can_imports_cap': GDXInput(
        'can_imports_cap', ['i', 'v', 'r', 'MW']),
    'can_imports_szn': GDXInput(
        'can_imports_szn_filt', ['r', 'szn', 'imports']),
    'can_trade_8760':H5Input(
        os.path.join('inputs_case', 'can_trade_8760.h5'),
        ['r','hours','t','MW']),
    'cap_converter': GDXInput(
        'cap_converter_filt', ['r', 'MW']),
    'cap_hyd_szn_adj': GDXInput(
        'cap_hyd_szn_adj_filt', ['i', 'szn', 'r', 'seacf']),
    'cap_exog': GDXInput(
        'cap_exog_filt', ['i', 'v', 'r', 'exog']),
    'cap_init': GDXInput(
        'cap_init', ['i', 'v', 'r', 'MW']),
    'cap_inv': GDXInput(
        'inv_ivrt', ['i', 'v', 'r', 't', 'MW']),
    'cap_ret': GDXInput(
        'ret', ['i', 'v', 'r', 'ret']),
    'cf_adj': GDXInput(
        'cf_adj_t_filt', ['i', 'v', 't', 'CF']),
    'co2_tax': GDXInput(
        'co2_tax', ['t', 'Price']),
    'consumption_demand': GDXInput(
        'prod_filt', ['i', 'v', 'r', 'h', 'MWh']),
    'converter_efficiency_vsc': GDXInput(
        'converter_efficiency_vsc', ['value']),
    'cost_cap': GDXInput(
        'cost_cap_filt', ['i', 't', 'cost_cap']),
    'cost_cap_fin_mult': GDXInput(
        'cost_cap_fin_mult_filt', ['i', 'r', 't', 'fin_mult']),
    'cost_vom': GDXInput(
        'cost_vom_filt', ['i', 'v', 'r', 'cost_vom']),
    'csp_sm': GDXInput(
        'csp_sm', ['i', 'sm']),
    'd_szn': CSVInput(
        os.path.join('inputs_case', 'd_szn.csv'),
        ['d', 'szn']),
    'degrade_annual': GDXInput(
        'degrade_annual', ['i', 'rate']),
    'dr_inc': CSVInput(os.path.join('inputs_case', 'dr_inc.csv'),
        False),
    'dr_dec': CSVInput(os.path.join('inputs_case', 'dr_dec.csv'),
        False),
    'dr_hrs': CSVInput(os.path.join('inputs_case', 'dr_hrs.csv'),
        ["i", "pos_hrs", "neg_hrs"]),
    'dr_shed': GDXInput(
        'allowed_shed', ['i', 'max_hrs']),
    'emit_price': GDXInput(
        'emissions_price', ['e', 'r', 'emit_price']),
    'emit_rate': GDXInput(
        'emit_rate_filt', ['e', 'i', 'v', 'r', 'emit_rate']),
    'first_year': GDXValue(
        'tfirst', ['t', 'drop']),
    'flex_load': GDXInput(
        'flex_load', ['r', 'h', 'exog']),
    'flex_load_opt': GDXInput(
        'flex_load_opt', ['r', 'h', 'opt']),
    'fuel_price': GDXInput(
        'fuel_price_filt', ['i', 'r', 'fuel_price']),
    'fuel_price_biopower': GDXInput(
        'repbioprice_filt', ['r', 'fuel_price']),
    'h_dt_szn': CSVInput(
        os.path.join('inputs_case', 'h_dt_szn.csv'),
        False),
    'h_szn': GDXInput(
        'h_szn', ['h', 'szn', 'drop']),
    'heat_rate': GDXInput(
        'heat_rate_filt', ['i', 'v', 'r', 'heat_rate']),
    'hierarchy': GDXInput(
        'hierarchy', [
            'r', 'nercr', 'transreg', 'cendiv', 'st', 'interconnect',
            'country', 'usda_region', 'aggreg', 'ccreg', 'drop']),
    'hours': GDXInput(
        'hours', ['h', 'hours']),
    'hours_peak': CSVInput(
        os.path.join('inputs_case', 'STATIC_inputs',
                     'superpeak_hour_mapper.csv'),
        ['h', 'h_mapped']),
    'i_subsets': TechTypes(
        'i_subsets', ['i', 'tech_cat', 'drop']),
    'ilr': GDXInput(
        'ilr', ['i','ilr']),
    'ilr_pvb_config': GDXInput(
        'ilr_pvb_config', ['pvb_config','ilr']),
    'index_hr_map': CSVInput(
        os.path.join('inputs_case','index_hr_map.csv'),
        False),
    'load_climate_allyears': LoadData(
        os.path.join('ReEDS_Augur','augur_data','load_allyears.h5'),
        False),
    'load_climate_sevenyears': LoadDataWithSwitch(
        os.path.join('ReEDS_Augur','augur_data','load_7year_'),
        False),
    'load_multiplier': GDXInput(
        'load_multiplier_filt', ['cendiv', 'load_mult']),
    'load_profiles': LoadData(
        os.path.join('inputs_case', 'load.h5'),
        False),
    'm_cf': GDXInput(
        'm_cf_filt', ['i', 'v', 'r', 'h', 'CF']),
    'm_cf_szn': GDXInput(
        'm_cf_szn_filt', ['i', 'v', 'r', 'szn', 'm_cf_szn']),
    'map_BAtoTZ': CSVInput(
        os.path.join('inputs_case', 'reeds_ba_tz_map.csv'),
        ['r', 'tz']),
    'maxage': GDXInput(
        'maxage', ['i','maxage']),
    'minloadfrac': GDXInput(
        'minloadfrac_filt', ['r', 'i', 'szn', 'minloadfrac']),
    'month_hrs': CSVInput(
        os.path.join('inputs_case', 'STATIC_inputs', 'month_hrs.csv'),
        False),
    'ng_price': GDXInput(
        'repgasprice_filt', ['r', 'fuel_price']),
    'osprey_charging': CSVInputWithSwitch(
        os.path.join('ReEDS_Augur', 'augur_data', 'storage_in_'),
        False),
    'osprey_conversion': CSVInputWithSwitch(
        os.path.join('ReEDS_Augur', 'augur_data', 'conversion_'),
        False),
    'osprey_dr': CSVInputWithSwitch(
        os.path.join('ReEDS_Augur', 'augur_data', 'dr_inc_'),
        False),
    'osprey_flows': CSVInputWithSwitch(
        os.path.join('ReEDS_Augur', 'augur_data', 'flows_'),
        False),
    'osprey_gen': CSVInputWithSwitch(
        os.path.join('ReEDS_Augur', 'augur_data', 'gen_'),
        False),
    'osprey_prices': CSVInputWithSwitch(
        os.path.join('ReEDS_Augur', 'augur_data', 'prices_'),
        False),
    'osprey_produce': CSVInputWithSwitch(
        os.path.join('ReEDS_Augur', 'augur_data', 'produce_'),
        False),
    'osprey_SOC': CSVInputWithSwitch(
        os.path.join('ReEDS_Augur', 'augur_data', 'storage_level_'),
        False),
    'pvf_onm': GDXInput(
        'pvf_onm', ['t', 'pvf']),
    'r_rs': GDXInput(
        'r_rs', ['r', 'rs', 'drop']),
    'resources': CSVInput(
        os.path.join('inputs_case', 'resources.csv'),
        False),
    'rfeas': GDXInput(
        'rfeas', ['r', 'drop']),
    'routes': GDXInput(
        'routes_filt', False),
    'rsc_dat': GDXInput(
        'rsc_dat_filt', ['i', 'r', 'sc_cat', 'rscbin', 'Value']),
    'rsc_dat_dr': GDXInput(
        'rsc_dat_dr', ['i', 'r', 'sc_cat', 'rscbin', 'cost']),
    'sdbin': GDXInput(
        'sdbin', ['bin', 'drop']),
    'storage_duration': GDXInput(
        'storage_duration', ['i', 'duration']),
    'storage_eff': GDXInput(
        'storage_eff_filt', ['i', 'RTE']),
    'szn': GDXInput(
        'szn', ['szn', 'drop']),
    'trancap': GDXInput(
        'cap_trans', ['r', 'rr', 'trtype', 'MW']),
    'tranloss': GDXInput(
        'tranloss', ['r', 'rr', 'trtype', 'tranloss']),
    'vintage_inv': GDXInput(
        'inv_cond_filt', ['i', 'v', 't', 'drop']),
    'upgrades': TechMapping(
        'upgrade_to_filt', ['i', 'ii', 'drop']),
    'vre_profiles': H5Input(
        os.path.join('inputs_case', 'recf.h5'),
        False),
    'watertechs': TechMapping(
        'ctt_i_ii_filt', ['i', 'ii', 'drop']),
    'wecc_data': CSVInput(
        os.path.join('inputs_case', 'hourly_operational_characteristics.csv'),
        ['i', 'maxcap', 'avgcap', 'Min Up Time', 'Mid Down Time',
         'Forced Outage Rate', 'Maintenance Rate', 'Mean Time to Repair',
         'Start Cost/cap', 'Min Stable Level/cap', 'Max Ramp/cap']),
    'yearset': GDXInput(
        'tmodel_new', ['t', 'drop']),
        }
    #%%
