# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 19:34:39 2021

@author: afrazier
"""

import os
import pandas as pd
import numpy as np

class SwitchSettings(object):
    '''
    Class for all switches in Augur
    '''
    
    data_year = None
    gdx_file = None
    next_year = None
    prev_year = None
    scen = None
    osprey_years = None
    
    @classmethod
    def set_switches(cls, next_year, prev_year, scen):
        cls.gdx_file = os.path.join(
            'ReEDS_Augur','augur_data','reeds_data_{}.gdx'.format(prev_year))
        cls.next_year = next_year
        cls.prev_year = prev_year
        cls.scen = scen
        cls.switches = {}
        # Collect ReEDS switch values
        call_file = 'call_{}.bat'.format(scen)
        if not os.path.isfile(call_file):
            call_file = 'call_{}.sh'.format(scen)
        for l in open(call_file, 'r'):
            if 'createmodel' in l:
                break
        entries = l.split(' ')
        for entry in entries:
            begin = entry[0:2]
            if begin == '--':
                split = entry.split('=')
                switch = split[0][2:]
                value = split[1]
                cls.switches[switch.lower()] = value
        # Collect default Augur values
        defaults = pd.read_csv(os.path.join('ReEDS_Augur', 'value_defaults.csv'))
        for i in range(0, len(defaults)):
            key = defaults.loc[i, 'key']
            value = defaults.loc[i, 'value']
            dtype = defaults.loc[i, 'dtype']
            if dtype == 'float':
                value = float(value)
            if dtype == 'int':
                value = int(value)
            if dtype == 'list':
                value = value.split(',')
            if dtype == 'boolean':
                if value.upper() == 'FALSE':
                    value = bool(False)
                elif value.upper() == 'TRUE':
                    value = bool(True)
                else:
                    raise Exception(
                        '{}:{} must be TRUE or FALSE'.format(key,value))
            cls.switches[key] = value
        cls.data_year = cls.switches['reeds_data_year']
        cls.switches['gdx_file'] = cls.gdx_file
        cls.switches['next_year'] = cls.next_year
        cls.switches['prev_year'] = cls.prev_year
        cls.switches['scen'] = scen
        ### Adjust types for some switches from ReEDS
        cls.switches['capcredit_szn_hours'] = int(cls.switches['capcredit_szn_hours'])
        cls.switches['marg_vre_mw'] = float(cls.switches['marg_vre_mw'])
        cls.switches['marg_stor_mw'] = float(cls.switches['marg_stor_mw'])
        cls.switches['marg_dr_mw'] = float(cls.switches['marg_dr_mw'])
        cls.switches['osprey_years'] = [int(y) for y in cls.switches['osprey_years'].split(',')]
        cls.switches['run_osprey_years'] = [
            int(y) for y in cls.switches['run_osprey_years'].split('_')]
        cls.osprey_years = cls.switches['osprey_years']
        ### Derived values
        cls.switches['osprey_num_years'] = len(cls.switches['osprey_years'])
        cls.switches['osprey_ts_length'] = 8760 * cls.switches['osprey_num_years']
        cls.switches['precision'] = (
            {16:np.float16, 32:np.float32, 64:np.float64}[cls.switches['precision']])
        cls.switches['plot_years'] = [int(y) for y in cls.switches['plot_years']]
        cls.switches['plots'] = True if len(cls.switches['plot_years']) else False
