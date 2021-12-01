'''
This file is for converting back from ReEDS capacity results to reV sites.
'''

import argparse
import datetime
import os
import sys
import glob
import shutil
import h5py
import logging
import numpy as np
import pandas as pd


# ------------------------------------------------------------------------------
# Setup logger
# ------------------------------------------------------------------------------
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
logger.info('Resource logger setup.')


def get_supply_curve(run_folder, sc_file, tech, cost_col, exist_plant_file,
                     r2rev_priority, out_dir):

    # ------------------------------------------------------------------------------
    # Define Files and Directories
    # ------------------------------------------------------------------------------
    # reeds run output files
    # Only used to get the set of model years run.
    year_src = os.path.join(run_folder, 'outputs', 'systemcost.csv')
    # New investments by reg/class/bin
    inv_rsc = os.path.join(run_folder, 'outputs', 'cap_new_bin_out.csv')
    # Refurbishments by reg/class/bin
    inv_refurb = os.path.join(run_folder, 'outputs', 'cap_new_ivrt_refurb.csv')
    # Existing capacity over time. Used for retirements of existing capacity.
    cap_exog = os.path.join(run_folder, 'outputs', 'm_capacity_exog.csv')
    cap_chk = os.path.join(run_folder, 'outputs', 'cap.csv')

    # Get lifetimes
    lifetimes = pd.read_csv(os.path.join(run_folder, 'inputs_case', 'maxage.csv'),
                            names=['tech', 'lifetime'])
    lifetimes = expand_star(lifetimes, index=False, col='tech')

    # ------------------------------------------------------------------------------
    # Prepare Output Directory
    # ------------------------------------------------------------------------------
    # Add log file to output folder
    fh = logging.FileHandler(os.path.join(out_dir, 'log_{}.txt'.format(tech)),
                             mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Copy this file into the output folder
    this_file_path = os.path.realpath(__file__)
    shutil.copy(this_file_path, out_dir)

    # ------------------------------------------------------------------------------
    # Get years
    # ------------------------------------------------------------------------------
    df_yr = pd.read_csv(year_src, low_memory=False)
    years = sorted(df_yr['Dim2'].unique().tolist())
    years = [2009] + years

    # ------------------------------------------------------------------------------
    # Prepare Supply Curve Dataframe for ReEDS to reV Matching
    # ------------------------------------------------------------------------------
    # Get reV supply curve
    if os.path.splitext(sc_file)[1] == '.csv':
        df_sc_in = pd.read_csv(sc_file, low_memory=False)
    elif os.path.splitext(sc_file)[1] == '.h5':
        with h5py.File(sc_file, mode='r') as h:
            df_sc_in = pd.DataFrame(np.asarray(h['rev']['supply_curve']))
        df_sc_in.rename(columns={'gid': 'sc_gid',
                                 'substation_gid': 'sc_point_gid',
                                 're_class': 'class',
                                 'capacity_mw': 'capacity'},
                        inplace=True)
        rname = 'p' if tech in ['upv', 'dupv'] else 's'
        df_sc_in['region'] = rname + df_sc_in['model_region'].map(str)
        df_sc_in['bin'] = None
    # Save initial state of df_sc_in for later
    df_sc_in_raw = df_sc_in.copy()
    # Remove unneeded columns
    df_sc_in = df_sc_in[['sc_gid', 'sc_point_gid', 'latitude', 'longitude',
                         'region', 'class', 'bin', 'capacity', cost_col]].copy()
    df_sc_in.rename(columns={'capacity': 'cap_avail'}, inplace=True)

    # Sort data by:
    #  (1) region - ascending
    #  (2) class - ascending
    #  (3) bin - ascending
    #  (4a) cost - ascending
    #  (4b) is_exist - descending
    #  (5b) cost - ascending
    if r2rev_priority == "cost":
        df_sc_in = df_sc_in.sort_values(by=['region', 'class', 'bin', cost_col],
                                        ascending=[True, True, True, True])
    elif r2rev_priority == "existing":
        # Get list of existing plants
        #  (1) sc_point_gid = unique identifier for each supply curve grid cell
        #      of a given wind regime {reference access, open access, limited access}
        #  (2) is_exist = 1 if existing wind farm polygon intersects a supply
        #      curve grid cell; 0 otherwise
        df_exist_plant = pd.read_csv(exist_plant_file, low_memory=False)
        # Join existing wind farms to reV supply curve; join column="sc_point_gid"
        df_sc_in = df_sc_in.merge(df_exist_plant, how='left',
                                  on=['sc_point_gid'], sort=False)
        df_sc_in = df_sc_in.sort_values(by=['region', 'class', 'bin', 'is_exist', cost_col],
                                        ascending=[True, True, True, False, True])

    # Write input data
    df_sc_in.to_csv(os.path.join(out_dir, 'df_sc_in_{}.csv'.format(tech)), index=False)

    # Initialize supply curve data frame for processing
    df_sc = df_sc_in.copy()
    df_sc['cap_expand'] = df_sc['cap_avail']
    df_sc['cap_left'] = df_sc['cap_avail']
    df_sc['cap'] = 0
    df_sc['inv_rsc'] = 0
    df_sc['ret'] = 0
    df_sc['refurb'] = 0
    df_sc['expanded'] = 'no'
    # df_sc['cum_cap'] = df_sc.groupby(['region','class','bin'])['cap_avail'].cumsum()

    # For CSP, need to assign CSP-NS the best class in each region.
    df_sc_max = df_sc.groupby(['region'])['class'].max().reset_index()
    df_sc_max.rename(columns={'class': 'max_class'}, inplace=True)

    # ------------------------------------------------------------------------------
    # Prepare Capital Stock Data (Existing, Refurbishments, Retirements)
    # ------------------------------------------------------------------------------
    # Find existing capacity by bin with raw supply curve.
    # Consider existing capacity as investment in 2009 to use the
    # same logic as inv_rsc when assigning to gid.
    exist_columns = ['tech','region','year','bin','MW']
    if 'existing_capacity' in df_sc_in_raw:
        df_bin_exist = df_sc_in_raw[(df_sc_in_raw['existing_capacity'] > 0) &
                                    (df_sc_in_raw['online_year'] < 2010)].copy()
        df_bin_exist = df_bin_exist[['region','class','bin','existing_capacity']].copy()
        df_bin_exist = df_bin_exist.groupby(['region','class','bin'], sort=False, as_index =False).sum()
        df_bin_exist['raw_tech'] = tech
        df_bin_exist['tech'] = df_bin_exist['raw_tech'] + '_' + df_bin_exist['class'].astype(str)
        df_bin_exist['year'] = 2009
        df_bin_exist['bin'] = 'bin' + df_bin_exist['bin'].astype(str)
        df_bin_exist['MW'] = df_bin_exist['existing_capacity']
        df_bin_exist = df_bin_exist[exist_columns].copy()
    else:
        df_bin_exist = pd.DataFrame(columns=exist_columns)

    # Read in inv_rsc
    df_inv_rsc = pd.read_csv(inv_rsc, low_memory=False)
    df_inv_rsc.columns = ['tech', 'vintage', 'region', 'year', 'bin', 'MW']
    df_inv_rsc = df_inv_rsc[df_inv_rsc['tech'].str.startswith(tech)].copy()
    df_inv_rsc.drop(columns=['vintage'], inplace=True)

    # Concatenate existing and inv_rsc
    df_inv = pd.concat([df_bin_exist, df_inv_rsc], sort=False, ignore_index=True)
    # Split tech from class
    df_inv[['tech_cat', 'class']] = df_inv['tech'].str.split('_', 1, expand=True)
    # Specifically for CSP, csp-ns should get assigned higest class
    if tech == 'csp':
        df_inv = pd.merge(df_inv, df_sc_max, on='region')
        ns_idx = df_inv['tech_cat'] == 'csp-ns'
        df_inv.loc[ns_idx, 'class'] = df_inv.loc[ns_idx, 'max_class']
    df_inv = df_inv[['year', 'region', 'class', 'bin', 'MW']]
    df_inv['class'] = df_inv['class'].astype('int')
    df_inv['bin'] = df_inv['bin'].str.replace('bin', '', regex=False).astype('int')
    df_inv = df_inv.sort_values(by=['year', 'region', 'class', 'bin'])

    # Refurbishments
    df_inv_refurb_in = pd.read_csv(inv_refurb, low_memory=False)
    df_inv_refurb_in.columns = ['tech', 'vintage', 'region', 'year', 'MW']
    df_inv_refurb_in = df_inv_refurb_in[df_inv_refurb_in['tech'].str.startswith(tech)].copy()
    df_inv_refurb_in.drop(columns=['vintage'], inplace=True)
    # Split tech from class
    df_inv_refurb = df_inv_refurb_in.copy()
    if df_inv_refurb.empty:
        df_inv_refurb[['tech_cat', 'class']] = ''
    else:
        df_inv_refurb[['tech_cat', 'class']] = df_inv_refurb['tech'].str.split('_', 1, expand=True)
    # Specifically for CSP, csp-ns should get assigned higest class
    if tech == 'csp':
        df_inv_refurb = pd.merge(df_inv_refurb, df_sc_max, on='region')
        ns_idx = df_inv_refurb['tech_cat'] == 'csp-ns'
        df_inv_refurb.loc[ns_idx, 'class'] = df_inv_refurb.loc[ns_idx, 'max_class']
    df_inv_refurb = df_inv_refurb[['year', 'region', 'class', 'MW']]
    df_inv_refurb['class'] = df_inv_refurb['class'].astype('int')
    df_inv_refurb = df_inv_refurb.sort_values(by=['year', 'region', 'class'])

    # Retirements of inv_rsc. We don't need bins. We actually never needed bins...
    df_ret_inv_rsc = df_inv_rsc.drop(columns=['bin'])
    df_ret_inv_rsc = pd.merge(df_ret_inv_rsc, lifetimes, on='tech')
    df_ret_inv_rsc['year'] += df_ret_inv_rsc['lifetime']
    # Ensure lifetime retirements hit on a year in years
    # Set each year to the first year greater than or equal to it in years
    yr_idx = df_ret_inv_rsc['year'] <= max(years)
    df_ret_inv_rsc.loc[yr_idx, 'year'] = df_ret_inv_rsc.loc[yr_idx, 'year'].apply(
        lambda x: years[next((index for index, value
                              in enumerate([y-x for y in years])
                              if value >= 0), None)]
        )

    # Retirements of inv_refurb:
    df_ret_inv_refurb = pd.merge(df_inv_refurb_in, lifetimes, on='tech')
    df_ret_inv_refurb['year'] += df_ret_inv_refurb['lifetime']
    # Ensure refurbishments hit on a year in years
    # Set each year to the first year greater than or equal to it in years
    yr_idx = df_ret_inv_refurb['year'] <= max(years)
    df_ret_inv_refurb.loc[yr_idx, 'year'] = df_ret_inv_refurb.loc[yr_idx, 'year'].apply(
        lambda x: years[next((index for index, value
                              in enumerate([y-x for y in years])
                              if value >= 0), None)]
        )

    # Retirements of existing by taking year-to-year difference of cap_exog.
    df_cap_exog = pd.read_csv(cap_exog, low_memory=False)
    df_cap_exog.columns = ['tech', 'vintage', 'region', 'year', 'MW']
    df_cap_exog.drop(columns=['vintage'], inplace=True)
    df_cap_exog = df_cap_exog[df_cap_exog['tech'].str.startswith(tech)].copy()
    if not df_cap_exog.empty:
        # Filter to years of cap_new_bin_out
        df_cap_exog = df_cap_exog[df_cap_exog['year'].isin(years)].copy()
        # pivot out table, add another year and fill with zeros, then melt back
        df_cap_exog = df_cap_exog.pivot_table(index=['tech', 'region'],
                                              columns=['year'],
                                              values='MW').reset_index()
        df_cap_exog.fillna(0, inplace=True)
        # This finds the next year in years and sets it equal to zero.
        # If there are more years in df_cap_exog, latest year + 1 is
        # set equal to 0. This only happens if run is only through 2020s
        if years.index(df_cap_exog.columns[-1]) == (len(years)-1):
            yr = df_cap_exog.columns[-1] + 1
        else:
            yr = years[years.index(df_cap_exog.columns[-1]) + 1]
        df_cap_exog[yr] = 0
        # Melt back and diff
        df_cap_exog = pd.melt(df_cap_exog, id_vars=['tech', 'region'],
                              value_vars=df_cap_exog.columns.tolist()[2:],
                              var_name='year', value_name='MW')
        df_ret_exist = df_cap_exog.copy()
        df_ret_exist['MW'] = df_ret_exist.groupby(['tech', 'region'])['MW'].diff()
        df_ret_exist['MW'].fillna(0, inplace=True)
        df_ret_exist['MW'] = df_ret_exist['MW'] * -1
    else:
        df_ret_exist = pd.DataFrame()

    # Concatenate retirements of existing, inv_rsc, and inv_refurb
    df_ret = pd.concat([df_ret_exist, df_ret_inv_rsc, df_ret_inv_refurb],
                       sort=False, ignore_index=True)
    # remove zeros
    df_ret = df_ret[df_ret['MW'] != 0].copy()
    # Remove retirements in later years
    df_ret = df_ret[df_ret['year'].isin(years)].copy()
    # Split tech from class
    if not df_ret.empty:
        # Specifically for CSP, csp-ns doesn't split so fixing here
        if all(df_ret.tech.unique()) == 'csp-ns':
            df_ret['class'] = 0
        else:
            df_ret[['tech_cat', 'class']] = df_ret['tech'].str.split('_', 1, expand=True)
        # Specifically for CSP, csp-ns should get assigned higest class
        if tech == 'csp':
            df_ret = pd.merge(df_ret, df_sc_max, on='region')
            ns_idx = df_ret['tech_cat'] == 'csp-ns'
            df_ret.loc[ns_idx, 'class'] = df_ret.loc[ns_idx, 'max_class']
        df_ret = df_ret[['year', 'region', 'class', 'MW']]
        df_ret['class'] = df_ret['class'].astype('int')
        df_ret = df_ret.sort_values(by=['year', 'region', 'class'])
    else:
        df_ret['class'] = 0
        df_ret = df_ret[['year', 'region', 'class', 'MW']]

    # Get check for capacity
    df_cap_chk = pd.read_csv(cap_chk, low_memory=False)
    df_cap_chk.columns = ['tech', 'region', 'year', 'MW']
    df_cap_chk = df_cap_chk[df_cap_chk['tech'].str.startswith(tech)].copy()
    df_cap_chk[['tech_cat', 'class']] = df_cap_chk['tech'].str.split('_', 1, expand=True)
    # Specifically for CSP, csp-ns doesn't split so fixing here
    df_cap_chk.loc[df_cap_chk['tech_cat'] == 'csp-ns', 'class'] = 0
    df_cap_chk = df_cap_chk[['year', 'region', 'class', 'MW']]
    df_cap_chk['class'] = df_cap_chk['class'].astype('int')

    # ------------------------------------------------------------------------------
    # ReEDS to ReV Assignment
    # ------------------------------------------------------------------------------
    # now we loop through years and determine the investment in each supply
    # cuve point in each year by filling up the supply curve point capacities
    # in the associated (region,class,bin) tuple in order of:
    #    priority="existing plants": (1) existing sites; (2) lowest cost based
    #              on investment
    #    priority="lowest cost": (1) lowest cost based on the investment
    df_sc_out = pd.DataFrame()
    for year in years:
        logger.info('Starting %i', year)
        df_sc['year'] = year

        # First retirements
        # reset retirements associated with gids for each year.
        df_sc['ret'] = 0
        df_ret_yr = df_ret[df_ret['year'] == year].copy()

        for i, r in df_ret_yr.iterrows():
            # This loops through all the retirements
            df_sc_rc = df_sc[(df_sc['region'] == r['region'])
                             & (df_sc['class'] == r['class'])].copy()
            rcy = str(r['region']) + '_' + str(r['class']) + '_' + str(year)
            ret_left = r['MW']
            for sc_i, sc_r in df_sc_rc.iterrows():
                # This loops through each gid of the supply curve for this
                # region/class
                if round(ret_left, 2) > round(sc_r['cap'], 2):
                    # retirement is too large for just this gid. Fill up this
                    # gid and move to the next.
                    df_sc.loc[sc_i, 'ret'] = sc_r['cap']
                    ret_left = ret_left - sc_r['cap']
                    df_sc.loc[sc_i, 'cap'] = 0
                else:
                    # Remaining retirement is smaller than capacity in this gid
                    # so assign remaining retirement to this gid and break the
                    # loop through gids to move to the next retirement by
                    # region/class.
                    df_sc.loc[sc_i, 'ret'] = ret_left
                    df_sc.loc[sc_i, 'cap'] = sc_r['cap'] - ret_left
                    ret_left = 0
                    break
            if round(ret_left, 2) != 0:
                logger.info('ERROR at rcy=%s: ret_left should be 0 and it is:%s',
                            rcy, str(ret_left))

        df_sc['cap_left'] = df_sc['cap_expand'] - df_sc['cap']

        # Then refurbishments
        # reset refurbishments associated with gids for each year.
        df_sc['refurb'] = 0
        df_inv_refurb_yr = df_inv_refurb[df_inv_refurb['year'] == year].copy()

        for i, r in df_inv_refurb_yr.iterrows():
            # This loops through all the refurbishments
            df_sc_rc = df_sc[(df_sc['region'] == r['region'])
                             & (df_sc['class'] == r['class'])].copy()
            rcy = str(r['region']) + '_' + str(r['class']) + '_' + str(year)
            inv_left = r['MW']
            for sc_i, sc_r in df_sc_rc.iterrows():
                # This loops through each gid of the supply curve for this
                # region/class
                if round(inv_left, 2) > round(sc_r['cap_left'], 2):
                    # refurbishment is too large for just this gid. Fill up
                    # this gid and move to the next.
                    df_sc.loc[sc_i, 'refurb'] = sc_r['cap_left']
                    inv_left = inv_left - sc_r['cap_left']
                    df_sc.loc[sc_i, 'cap_left'] = 0
                else:
                    # Remaining refurbishment is smaller than capacity in this
                    # gid, so assign remaining refurb to this gid and break the
                    # loop through gids to move to the next refurbishment by
                    # region/class.
                    df_sc.loc[sc_i, 'refurb'] = inv_left
                    df_sc.loc[sc_i, 'cap_left'] = max(0, sc_r['cap_left'] - inv_left)
                    inv_left = 0
                    break
            if round(inv_left, 2) != 0:
                logger.info('ERROR at rcy=%s: inv_left for refurb should be 0 and it is %s',
                            rcy, str(inv_left))

        df_sc['cap'] = df_sc['cap_expand'] - df_sc['cap_left']

        # Finally, new site investments
        # reset investments associated with gids for each year.
        df_sc['inv_rsc'] = 0
        df_inv_yr = df_inv[df_inv['year'] == year].copy()
        # df_sc = df_sc.merge(df_inv_yr, how='left', on=['region','class','bin'], sort=False)
        for i, r in df_inv_yr.iterrows():
            # This loops through all the investments
            # old h5 files don't include bin, so only filter if that col exists
            df_sc_rcb = df_sc[(df_sc['region'] == r['region'])
                              & (df_sc['class'] == r['class'])
                              & ((df_sc['bin'] == r['bin']) | df_sc['bin'].isnull())].copy()
            rcby = str(r['region']) + '_' + str(r['class']) + '_' + str(r['bin']) + '_' + str(year)
            inv_left = r['MW']
            for sc_i, sc_r in df_sc_rcb.iterrows():
                # This loops through each gid of the supply curve for this region/class/bin
                if inv_left - sc_r['cap_left'] > 0.001:
                    # invesment is too large for just this gid.
                    if sc_i == df_sc_rcb.index[-1]:
                        # This is the final supply curve row, so we are
                        # building more capacity than is available in the supply curve.
                        # In this case, we should add the remainder to the
                        # first row, expanding that gids capacity
                        logger.info('WARNING at rcby=%s. We are building %s but only have %s',
                                    rcby, str(inv_left), str(sc_r['cap_left']))
                        df_sc.loc[sc_i, 'inv_rsc'] = sc_r['cap_left']
                        df_sc.loc[sc_i, 'cap_left'] = 0
                        df_sc.loc[df_sc_rcb.index[0], 'inv_rsc'] += inv_left - sc_r['cap_left']
                        df_sc.loc[df_sc_rcb.index[0], 'cap_expand'] += inv_left - sc_r['cap_left']
                        df_sc.loc[df_sc_rcb.index[0], 'expanded'] = 'yes'
                        inv_left = 0
                        break
                    else:
                        # This is the normal logic. Fill up this gid and move
                        # to the next.
                        df_sc.loc[sc_i, 'inv_rsc'] = sc_r['cap_left']
                        inv_left = inv_left - sc_r['cap_left']
                        df_sc.loc[sc_i, 'cap_left'] = 0
                else:
                    # Remaining investment is smaller than available capacity
                    # in this gid, so assign remaining investment to this gid
                    # And break the loop through gids to move to the next
                    # investment by region/class/bin.
                    df_sc.loc[sc_i, 'inv_rsc'] = inv_left
                    df_sc.loc[sc_i, 'cap_left'] = max(0, sc_r['cap_left'] - inv_left)
                    inv_left = 0
                    break
                if inv_left < 0:
                    logger.info('ERROR at rcby=%s: inv_left is negative: %s',
                                rcby, str(inv_left))
            if round(inv_left, 2) != 0:
                logger.info('ERROR at rcby=%s: inv_left should be zero and it is: %s',
                            rcby, str(inv_left))
        df_sc['cap'] = df_sc['cap_expand'] - df_sc['cap_left']

        # check if capacity is the same as from cap.csv
        # cap_df_sc_yr = df_sc['cap'].sum()
        # cap_chk_yr = df_cap_chk[df_cap_chk['year'] == year]['MW'].sum()
        # if round(cap_df_sc_yr) != round(cap_chk_yr):
        #     logger.info('WARNING: total capacity, ' + str(round(cap_df_sc_yr)) + ', is not the same as from cap.csv, ' + str(round(cap_chk_yr)))
        df_sc_out = pd.concat([df_sc_out, df_sc], sort=False)

    # ------------------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------------------
    cap_fin_df_sc = df_sc['cap'].sum()
    inv_rsc_cum = df_inv['MW'].sum()
    inv_refurb_cum = df_inv_refurb['MW'].sum()
    ret_cum = df_ret['MW'].sum()
    cap_fin_calc = inv_rsc_cum + inv_refurb_cum - ret_cum
    cap_csv_fin = df_cap_chk[df_cap_chk['year'] == years[-1]]['MW'].sum()

    logger.info('Final Capacity check (MW):')
    logger.info('final cap in df_sc: %s', str(cap_fin_df_sc))
    logger.info('Final cap.csv: %s', str(cap_csv_fin))
    logger.info('Difference (error): %s', str(cap_fin_df_sc - cap_csv_fin))
    logger.info('Calculated capacity from investment and retirement input: %s',
                str(cap_fin_calc))
    logger.info('Cumulative inv_rsc: %s', str(inv_rsc_cum))
    logger.info('Cumulative retirements: %s', str(ret_cum))
    logger.info('Cumulative inv_refurb: %s', str(inv_refurb_cum))

    return df_sc_out


def expand_star(df, index=True, col=None):
    """
    expands technologies according to GAMS syntax
    if index=True, uses index as technology to expand
    otherwise uses col
    """
    def expand(df):
        df_new = pd.DataFrame(columns=df.columns)
        for subset in df.index:
            temp_save = []
            if '*' in subset:
                temp_remove = df.loc[[subset]]
                df.drop(subset, inplace=True)
                temp = subset.split('*')
                temp2 = temp[0].split('_')
                temp_low = pd.to_numeric(temp[0].split('_')[-1])
                temp_high = pd.to_numeric(temp[1].split('_')[-1])
                temp_tech = ''
                for n in range(0, len(temp2)-1):
                    temp_tech += temp2[n]
                    if not n == len(temp2)-2:
                        temp_tech += '_'
                for c in range(temp_low, temp_high+1):
                    temp_save.append('{}_{}'.format(temp_tech, str(c)))
                df_new = pd.concat([df_new,
                    pd.DataFrame(np.repeat(temp_remove.values, len(temp_save), axis=0),
                                 index=temp_save, columns=df.columns)])
        return pd.concat([df, df_new])

    if index:
        return expand(df)
    else:
        tmp = expand(df.set_index(col))
        return tmp.reset_index().rename(columns={'index': col})


if __name__ == "__main__":
    # Argument inputs
    parser = argparse.ArgumentParser(
        description="""This file produces the DR shiftability inputs""")

    parser.add_argument("run_folder", help="Folder containing ReEDS run")
    parser.add_argument("tech", help="technology to get supply curve data for",
                        choices=['wind-ons', 'wind-ofs', 'upv', 'dupv', 'csp'])
    parser.add_argument('access_type', choices=['reference', 'open', 'limited'],
                        help='What type of access was used to create the ' +
                        'supply curve data. Should be read in from switch' +
                        'GWs_Siting[UPV/WindOns/WindOfs] based on tech')
    parser.add_argument('priority', default='existing',
                        choices=['existing', 'cost'],
                        help="How to rank reV sites. " +
                        "   lowest cost = Assign capacity to supply curve points based on lowest cost" + \
                        "   existing plants = First assign capacity to supply curve " + \
                        "                     points that had existing plants as " + \
                        "                     of 2020; Second based on lowest cost")
    parser.add_argument('-b', '--bins', default=None,
                        help='Number of bins used. Currently only for UPV')
    parser.add_argument('-v', '--version', default=None,
                        help='Which version of data to use. Default uses ' +
                        'most updated data available for each type.')
    parser.add_argument('-r', '--reduced_only', action="store_true",
                        help='Switch if you only want the reduced outputs')
    args = parser.parse_args()

    # ------------------------------------------------------------------------------
    # Define Constants
    # ------------------------------------------------------------------------------
    # Make sure if running PV, you have bins set
    assert args.tech != 'upv' or args.bins, "If using upv, bins must be set"

    # Location of supply curve data.
    # This is not great, because not everywhere can access the drive as
    # //nrelnas01, but leaving for now because all likely places this is
    # run will be able to.
    if os.name != 'posix':
        sc_path = r'//nrelnas01/ReEDS/Supply_Curve_Data'
    else:
        sc_path = r'/Volumes/ReEDS/Supply_Curve_Data'

    sc_tech = {'wind-ons': 'ONSHORE',
               'wind-ofs': 'OFFSHORE',
               'upv': 'UPV',
               'dupv': 'DUPV',
               'csp': 'CSP'}

    updated_versions = {'wind-ons': '2021_Update',
                        'wind-ofs': '2021_Update',
                        'upv': '2021_Update',
                        'dupv': '2018_Update',
                        'csp': '2019_Existing'}

    access_str = {'upv': {'reference': 'scen_128_ed1_{}bin-upv_*'.format(args.bins),
                          'open': 'scen_128_ed0_{}bin-upv_*'.format(args.bins),
                          'limited': 'scen_128_ed4_{}bin-upv_*'.format(args.bins)},
                  'wind-ons': {'reference': 'wind-ons_10_reference_*',
                               'open': 'wind-ons_08_open_*',
                               'limited': 'wind-ons_11_limited_*'},
                  'wind-ofs': {'open': 'wind-ofs_2_moderate_open_*',
                               'limited': 'wind-ofs_3_moderate_limited_*'},
                  'dupv': {'reference': '',
                           'open': '',
                           'limited': ''},
                  'csp': {'reference': '',
                          'open': '',
                          'limited': ''}}
    # ------------------------------------------------------------------------------
    # Define User Inputs
    # ------------------------------------------------------------------------------
    # technology
    tech = args.tech

    # ---Priority for assigning ReEDS capacity to reV sites---
    r2rev_priority = args.priority

    # Version of data to use
    ver = args.version if args.version else updated_versions[tech]

    # Pre 2020 update, hdf5 files were used, with a different file structure
    if int(ver[0:4]) < 2020:
        sc_file = os.path.join(sc_path, sc_tech[tech], ver, '*.h5')
    else:
        sc_file = os.path.join(sc_path, sc_tech[tech], ver,
                               access_str[tech][args.access_type],
                               'results', '{}_supply_curve_raw.csv'.format(tech))
    # Ensure the wildcard matches one and only one file
    sc_list = glob.glob(sc_file)
    if len(sc_list) != 1:
        logger.info(
            'The wildcard in {} should only match one SC file.\nIt matches files \n  {}'.format(
                sc_file, sc_list))
        sys.exit('Please fix your file paths for this tech and version.')

    sc_file = sc_list[0]

    # tansmission cost column of supply curve data frame
    if tech in ['wind-ons','wind-ofs']:
        cost_col = 'supply_curve_cost_per_mw'
    elif os.path.splitext(sc_file)[1] == '.csv':
        cost_col = 'trans_cap_cost'
    elif os.path.splitext(sc_file)[1] == '.h5':
        cost_col = 'cap_cost_transmission'


    run_folder = args.run_folder

    # existing plant file, only used if r2rev_priority = "existing plants"
    # TODO: check if this shouldn't depend on access regime. E.g. can we use
    # Open Access for all three access regimes?
    # Also, these files seem to include offshore too, even though they're
    # labeled "wind-ons"...
    exist_plant_file = os.path.join(sc_path, sc_tech[tech], ver, 'multi_wind-ons_2020-08-14-17-52-38-083947',
                                    'results', '{}_existing_lbnl2020.csv'.format(tech))

    out_dir = os.path.join(run_folder, 'outputs')

    # ------------------------------------------------------------------------------
    # For testing
    # ------------------------------------------------------------------------------
    # tech = 'wind-ons'
    # r2rev_priority = "existing plants"
    # sc_file = r'//nrelnas01/ReEDS/Supply_Curve_Data/ONSHORE/2020_Update/multi_wind-ons_2020-08-14-17-52-38-083947/results/wind-ons_supply_curve_raw.csv' #Reference Access
    # run_folder = r'//nrelnas01/ReEDS/FY20-reV_R2-MRM/runs_2020-08-27/bl_ref_mod' #Reference Access ATB moderate costs
    # exist_plant_file = r'//nrelnas01/ReEDS/Supply_Curve_Data/ONSHORE/2020_Update/multi_wind-ons_2020-08-14-17-52-38-083947/results/wind-ons_existing_lbnl2020.csv'
    #
    # scen = os.path.basename(run_folder)
    # timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
    # out_dir = os.path.join(
    #     'out', 'r2rev_{}_{}_{}'.format(scen, tech, timestamp))
    # ------------------------------------------------------------------------------

    # Make output directory
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    df_sc_out = get_supply_curve(run_folder, sc_file, tech, cost_col,
                                 exist_plant_file, r2rev_priority, out_dir)

    # ------------------------------------------------------------------------------
    # Dump outputs
    # ------------------------------------------------------------------------------
    logger.info('Outputting data...')
    df_sc_out['investment_bool'] = 0
    df_sc_out.loc[(df_sc_out['inv_rsc'] > 1e-3)
                  | (df_sc_out['refurb'] > 1e-3), 'investment_bool'] = 1
    df_sc_out = df_sc_out.rename(columns={'cap': 'capacity_MW'})
    if not args.reduced_only:
        df_sc_out.to_csv(os.path.join(out_dir, 'df_sc_out_{}.csv'.format(tech)),
                         index=False)
    # reduced version of df_sc_out
    df_sc_out = df_sc_out[df_sc_out['capacity_MW'] > 1e-3].copy()
    df_sc_out = df_sc_out[['year', 'sc_gid', 'sc_point_gid', 'latitude',
                           'longitude', 'region', 'class', 'bin',
                           cost_col, 'capacity_MW', 'investment_bool']].copy()
    df_sc_out.to_csv(os.path.join(out_dir, 'df_sc_out_{}_reduced.csv'.format(tech)),
                     index=False)
    logger.info('All done!')
