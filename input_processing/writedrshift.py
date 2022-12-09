# -*- coding: utf-8 -*-
"""
Code to process allowed shifting hours for demand response into
fraction of hours that can be shifted into each time slice
At some point, it may be nice to instead read in the actual DR
shifting potential and change to fraction of load that can be shifted
but haven't done that yet.

Created on Feb 24 2021
@author: bstoll
"""
# Imports
import os
import argparse
import sys
import shutil
import pandas as pd

# direct print and errors to log file
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Time the operation of this script
from ticker import toc
import datetime
tic = datetime.datetime.now()

if __name__ == "__main__":

    # Argument inputs
    parser = argparse.ArgumentParser(
        description="""This file produces the DR shiftability inputs""")

    parser.add_argument("reeds_dir", help="ReEDS directory")
    parser.add_argument("inputs_case", help="output directory")

    args = parser.parse_args()
    inputs_case = args.inputs_case

    #%% Inputs from switches
    sw = pd.read_csv(
        os.path.join(inputs_case, 'switches.csv'), header=None, index_col=0, squeeze=True)

    GSw_DR = int(sw.GSw_DR)
    drscen = sw.drscen

    # Read in DR shifting for specified scenario
    dr_hrs = pd.read_csv(
        os.path.join(args.reeds_dir, 'inputs', 'demand_response',
                     'dr_shifts_{}.csv').format(drscen)
        )
    # write out dr_hrs for condor
    dr_hrs.to_csv(os.path.join(inputs_case, 'dr_hrs.csv'),
             index=False)

    dr_pos = dr_hrs[['dr_type', 'pos_hrs']].reindex(dr_hrs.index.repeat(dr_hrs.pos_hrs))
    dr_pos['shift'] = dr_pos['pos_hrs'] - dr_pos.groupby(['dr_type']).cumcount()

    dr_neg = dr_hrs[['dr_type', 'neg_hrs']].reindex(dr_hrs.index.repeat(-1*dr_hrs.neg_hrs))
    dr_neg['shift'] = dr_neg['neg_hrs'] + dr_neg.groupby(['dr_type']).cumcount()

    dr_shifts = pd.concat([dr_pos.rename({'pos_hrs': 'hrs'}, axis=1),
                           dr_neg.rename({'neg_hrs': 'hrs'}, axis=1)])

    # Read in timeslice mapping and split off just 8760 hours
    hr_ts = pd.read_csv(
        os.path.join(args.reeds_dir, 'inputs', 'variability', 'h_dt_szn.csv'))
    hr_ts = hr_ts.loc[(hr_ts['hour'] <= 8760), ['h', 'hour', 'season']]

    num_hrs = pd.read_csv(os.path.join(args.reeds_dir, 'inputs', 'numhours.csv'),
                          names=['h', 'numhours'], index_col='h', squeeze=True)

    # Cross join shifts and timeslices
    dr_shifts['key'] = 1
    hr_ts['key'] = 1
    hr_shifts = pd.merge(dr_shifts, hr_ts, on='key').drop('key', axis=1)
    hr_shifts['shifted_hr'] = hr_shifts['hour'] + hr_shifts['shift']
    # Adjust hrs to be between 1 and 8760
    lt0 = hr_shifts.shifted_hr <= 0
    gt8760 = hr_shifts.shifted_hr > 8760
    hr_shifts.loc[lt0, 'shifted_hr'] += 8760
    hr_shifts.loc[gt8760, 'shifted_hr'] -= 8760

    # Merge on hr_ts again to the shifted hours to see what timeslice DR
    # can move load into
    hr_shifts = pd.merge(hr_shifts,
                         hr_ts.rename({'h': 'shifted_h', 'hour': 'shifted_hr',
                                       'season': 'shifted_season'}, axis=1),
                         on='shifted_hr').drop('key', axis=1)
    # Only allow shifts within the same season
    hr_shifts = hr_shifts[hr_shifts.season == hr_shifts.shifted_season]
    hr_shifts.drop(['shifted_season'], axis=1, inplace=True)

    hr_shifts2 = (
        hr_shifts[['dr_type', 'h', 'hour', 'shifted_h']]
        .drop_duplicates()
        .groupby(['dr_type', 'h', 'shifted_h'])
        .size()
        .reset_index()
        )

    ts_shifts = pd.merge(hr_shifts2, num_hrs, on='h')
    ts_shifts['shift_frac'] = ts_shifts[0] / ts_shifts['numhours']

    # Hack for H17 for now. Assume all of H17 comes out of H3 evenly
    # Remove H17 hours from H3 fraction
    ts_shifts.loc[ts_shifts.h == 'h3', 'shift_frac'] /= (1+num_hrs['h17']/num_hrs['h3'])
    # Grab H3 fradtions as H17's
    tmp1 = ts_shifts.loc[ts_shifts.h == 'h3', :].copy()
    tmp1['h'] = 'h17'
    # Grab shifts into H3 as H17's
    tmp2 = ts_shifts.loc[ts_shifts.shifted_h == 'h3', :].copy()
    tmp2['shifted_h'] = 'h17'
    # Recombine
    ts_shifts = pd.concat([ts_shifts, tmp1, tmp2])

    shift_out = ts_shifts.loc[ts_shifts['h'] != ts_shifts['shifted_h'], :]
    shift_out = shift_out.round(4)
    shift_out[['dr_type', 'shifted_h', 'h', 'shift_frac']].to_csv(
        os.path.join(inputs_case, 'dr_shifts.csv'), index=False, header=False)

    # Write out shifting for Augur
    day_shift = pd.merge(dr_shifts,
                         pd.DataFrame({'hr': list(range(1, 25, 1)), 'key': [1]*24}),
                         on='key')
    day_shift['shifted_hr'] = day_shift['hr'] + day_shift['shift']
    # Adjust hrs to be between 1 and 24
    lt0 = day_shift.shifted_hr <= 0
    gt24 = day_shift.shifted_hr > 24
    day_shift.loc[lt0, 'shifted_hr'] += 24
    day_shift.loc[gt24, 'shifted_hr'] -= 24
    day_shift2 = day_shift.copy()
    day_shift2['hr'] = day_shift2['hr'] + 24
    day_shift2['shifted_hr'] = day_shift2['shifted_hr'] + 24
    #day_shift = pd.concat([day_shift, day_shift2])
    day_shift['h'] = 'hr' + day_shift['hr'].astype(str)
    day_shift['hh'] = 'hr' + day_shift['shifted_hr'].astype(str)
    day_shift = day_shift.round(4)
    # Write out raw hour shifting for Augur
    (day_shift[['dr_type', 'h', 'hh']]
     .rename(columns={'dr_type': 'i'})
     .drop_duplicates()
     .to_csv(os.path.join(inputs_case, 'dr_shifts_augur.csv'),
             index=False, header=False)
     )


    # Read in DR shed for specified scenario
    dr_shed = pd.read_csv(
        os.path.join(args.reeds_dir, 'inputs', 'demand_response',
                     'dr_shed_{}.csv').format(drscen)
        )
    # write out dr_shed
    dr_shed[['dr_type', 'yr_hrs']].to_csv(
        os.path.join(inputs_case, 'dr_shed.csv'), index=False, header=False)
    dr_shed[['dr_type', 'day_hrs']].to_csv(
        os.path.join(inputs_case, 'dr_shed_augur.csv'), index=False, header=False)

    # Copy DR types to run folder
    shutil.copy(os.path.join(args.reeds_dir, 'inputs', 'demand_response',
                             'dr_types_{}.csv'.format(drscen)),
                os.path.join(inputs_case, 'dr_types.csv'))
    
    toc(tic=tic, year=0, process='input_processing/writedrshift.py', 
        path=os.path.join(inputs_case,'..'))
