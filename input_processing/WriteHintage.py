# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 11:53:24 2020

@author: smachen
"""
#%% direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')

# %% packages
import os
import pandas as pd
import argparse
import numpy as np

# %%########### DEBUG ARGUMENTS ###########################################
# Run this block to initialize your kernal to before running main()
#    
#args=dict(cwd="E:\\Scott\\ReEDS-B\\ReEDS-2.0\\",
#          nBin=6,
#          retscen="NukeRefRetireYear",
#          mindev=50,
#          distpvscen='StScen2018_Mid_Case',
#          genunitfile='ReEDS_generator_database_final_EIA-NEMS.csv',
#          outdir="E:\\scott\\",
#          waterconstraints=True
#          )
#locals().update(**args)

# %% functions and classes

class grouping:
    def __init__(self, nbins, *args, **kwargs):
        if nbins == 'unit':
            self.df = self.unit(*args)
        elif nbins == 'group':
            self.df = self.group(*args)
        else:
            nbins = int(nbins)
            self.df = self.kmeans(nbins, *args, **kwargs)
                  
        
    def unit(self, input_df, *args, **kwargs):
        '''
        This method creates a unique hintage bin for every generator
        
        input_df: pandas DataFrame object containing ReEDS generators
        *args: collects unused positional arguments to simplify code
        **kwargs: collects unused keyword arguments to simplify code
        '''
        output_df = pd.DataFrame()
        for ba in input_df.PCA.unique():
            ba_df = input_df[input_df.PCA == ba]
            for tech in ba_df.TECH.unique():
                
                df = ba_df[ba_df.TECH == tech]
                df['bin'] = df.reset_index(drop=True).index + 1
                output_df = pd.concat([output_df, df])
        
        return output_df 
    
    def group(self, input_df, col, *args, **kwargs):
        '''
        This method creates hintage bins for unique region, tech, and specified
        column combinations.
        
        input_df: (pandas.DataFrame object) containting ReEDS generators
        col: (str) The name of the column used in binning
        *args: collects unused positional arguments to simplify code
        **kwargs: collects unused keyword arguments to simplify code
        '''
        grouping_df = (input_df[['PCA', 'TECH', col]]
                       .drop_duplicates()
                       .reset_index(drop=True)
                       )
        output_df = pd.DataFrame()        
        for ba in grouping_df.PCA.unique():
            ba_df = grouping_df[grouping_df.PCA == ba].copy()
            for tech in ba_df.TECH.unique():
                tech_df = ba_df[ba_df.TECH == tech].copy()
                tech_df['bin'] = tech_df.reset_index().index + 1
                
                output_df = pd.concat([output_df, tech_df.reset_index(drop=True)])

        output_df = input_df.merge(output_df,
                                   on=['PCA','TECH', col],
                                   how='left'
                                   )
        return output_df
    
    class _kmeans:
        def __init__(self, input_df, col, bins, minSpread=2000):
            '''
            bin and return the centroids or breakpoints of each bin
    
            df (DataFrame object): Pandas Dataframe containing data for binning
            col (str): the column name that is to be binned
            bins (int): the number of desired bins
            '''
            self.bins = bins
            # if there are fewer generators than there are bins, reset the number
            # of bins to be one fewer than the number of generators.
            df = input_df.copy()
            if len(df[col].unique()) <= bins:
                if (df[col].max() - df[col].min()) < minSpread:
                    df['centroid'] = df[col].mean()
                    df['bin'] = 1
                else:
                    df['centroid'] = df[col]
                    temp = pd.DataFrame(data=dict(centroid=df[col].unique(), bin=None))
                    temp.bin = temp.index + 1
                    df = df.merge(temp, on='centroid', how='left')
                self.centers = df
            else:
                if bins > len(df.index):
                    
                    self.bins = max(len(df)-1, 1)
    
                # make a temporary binning DF
                bin_df = pd.concat([df[col],
                                   pd.DataFrame(columns=['centroid', 'upper',
                                                         'lower', 'bin'])])
                bin_df.rename(columns={0: col}, inplace=True)
    
                spread = minSpread - 1
                nbins = self.bins
                while spread < minSpread or nbins == 1:
                    dDiff = 1
                    # initialize the centroids
                    centroids = np.linspace(df[col].min(),
                                            df[col].max(),
                                            nbins+2)[1:-1]
    
                    # make the binning matrix
                    k = pd.DataFrame(index=df[col], columns=centroids)
                    while dDiff:  # do until dDiff = 0
                        # find the distance from point to centroid
                        for c in centroids:
                            k[c] = abs(k.index - c)
    
                        # select the closest centroid
                        k['centroid'] = k.columns[k[centroids].values.argmin(1)]
    
                        # initialize the change from last iteration
                        dDiff = 0
                        dDiff_temp = []
                        k = k[list(k.centroid.unique()) + ['centroid']]
                        nbins = len(k.centroid.unique())
                        for c in k.centroid.unique():
                            # find the center of the binned data
                            new_centroid = np.mean(k.loc[k.centroid == c].index)
                            # reset centroid columns
                            k.rename(columns={c: new_centroid}, inplace=True)
                            # save the distance between old and new centroids
                            dDiff_temp.append(abs(c-new_centroid))
    
                        # save the largest distance from old to new centroid
                        dDiff = max(dDiff_temp)
    
                        # reset centroids
                        centroids = k.columns[:-1]
    
                    # Merge centroids onto origianl DF
                    k_bins = k.centroid.drop_duplicates().reset_index().copy()
                    k_bins['bin'] = k_bins.index + 1
                    k_map = k.reset_index().merge(k_bins[['centroid', 'bin']],
                                                  on='centroid',
                                                  how='left').set_index('HR')
                    # make sure there is enough spread between centroids
                    d = pd.DataFrame(index=centroids, columns=centroids)
                    spread = []
                    for c in d.index:
                        d[c] = abs(c-d.index)
                        spread.append(d.loc[d[c] != 0, c].min())
                    spread = min(spread)
                    nbins -= 1
                k_map.reset_index(inplace=True)
    
                self.centers = df.merge(k_map.drop_duplicates()[[col, 'centroid', 'bin']],
                                        how='left', on=col)
    
    def kmeans(self, nbins, input_df, col, minSpread=2000, *args, **kwargs):
        '''
        bin and return the centroids or breakpoints of each bin

        df (DataFrame object): Pandas Dataframe containing data for binning
        col (str): the column name that is to be binned
        bins (int): the number of desired bins
        *args: collects unused positional arguments to simplify code
        **kwargs: collects unused keyword arguments to simplify code
        '''
        tdat=pd.DataFrame()
        for i in input_df.id.unique():
            tdat = pd.concat([tdat,
                              self._kmeans(input_df[input_df.id == i],
                                     'HR',
                                     nbins,
                                     minSpread=1000
                                     ).centers])
        return tdat

# %% MAIN
def main(cwd="E:\\Scott\\ReEDS-B\\ReEDS-2.0\\",
         nBin=6,
         retscen="NukeRefRetireYear",
         mindev=50,
         distpvscen='StScen2018_Mid_Case',
         genunitfile='ReEDS_generator_database_final_EIA-NEMS.csv',
         outdir="E:\\scott\\",
         waterconstraints=True):
    # %%
    inflator = 1.69 # Inflation factor 1987$ to 2004$
    
    # change directory to local ReEDS repo
    os.chdir(cwd)

    # read in genunitfile
    indat = pd.read_csv(os.path.join('inputs', 'capacitydata',
                                     '{}'.format(genunitfile)))

    # include O&M of polution control upgrades into FOM
    indat['W_VOM'] = inflator * (indat.W_VOM + indat.WCOMB_V + indat.WSNCR_V
                                 + indat.WSCR_V + indat.W_FFV + indat.W_DSIV)
    indat['W_FOM'] = inflator * (indat.W_FOM + indat.W_CAPAD + indat.WCOMB_F
                                 + indat.WSNCR_F + indat.WSCR_F + indat.W_FFF
                                 + indat.W_DSIF)

    # concatenate tech names based on whether water analysis is on -or- leave
#    them alone
    if waterconstraints:
        indat['tech'] = indat.coolingwatertech
        indat['tech'] = indat.tech.str.split('_', expand=True)[0]

    ad = indat[["tech", "pca", "ctt", "resource_region", "cap", retscen,
                "Commercial.Online.Year.Quarter", "IsExistUnit",
                "Fully.Loaded.Tested.Heat.Rate.Btu.kWh...Modeled",
                "Plant.NAICS.Description", "W_VOM", "W_FOM"]].copy()

    # rename Columns in ad
    rename = {}
    newnames = ["TECH", "PCA", "ctt", "resource.region", "Summer.capacity",
                "RetireYear", "Solve.Year.Online", "EXIST", "HR", "NAICS",
                "VOM", "FOM"]
    for old, new in zip(ad.columns, newnames):
        rename[old] = new
    ad.rename(columns=rename, inplace=True)

    # subset only generators that exist
    ad = ad[ad.EXIST]

    # subset only generators that have these NAICS category and capacity more
    # than 1mw:
    naics_cats = ["Hydroelectric Power Generation",
                  "Nuclear Electric Power Generation",
                  "Other Electric Power Generation",
                  "Electric Power Generation",
                  "Electric Power Distribution",
                  "Utilities",
                  "Electric Power Generation, Transmission and Distribution"
                  ]
    ad = ad[(ad.NAICS.isin(naics_cats)) & (ad['Summer.capacity'] >= 50)]

    # make the solve year column
    ad['onlineyear'] = (ad['Solve.Year.Online']
                        .str
                        .split('-', expand=True)[0]
                        .astype(int)
                        )

    # format regions column
    ad['pcn'] = ad.PCA.str.strip('p').astype(int)

    # only want those with a heat rate - all other binning is arbitrary
    # because the only data we get from genunitfile is the capacity and heat
    # rate but onm costs are assumed
    df = ad[(~ad.HR.isna()) & (~ad.TECH.isin(['geothermal', 'unknown',
            'CofireNew']))]

    # group up similar generators
    dat = df.groupby(['TECH', 'PCA', 'HR', 'resource.region', 'onlineyear',
                      'RetireYear', 'VOM', 'FOM']).sum().reset_index()
    dat.drop(columns=['EXIST', 'pcn'], inplace=True)

    # remove others category
    dat = dat[dat.TECH != 'others'].copy()

    # remove some generators based on retire year and online year
    dat = dat[(dat.RetireYear >= 2010) & (dat['onlineyear'] < 2010)].copy()

    # make unique ID column for generators
    dat['id'] = dat.TECH + '_' + dat.PCA
    
    # bin hintage data
    tdat = grouping(nBin, dat, 'HR', nBin, minspread=mindev).df
    
    # calculate the average heat rate for each bin by taking the product of the
    # sum of the summer capacity and the centroid of the bin
    tdat['wHR'] = tdat.HR * tdat['Summer.capacity']
    tdat['wVOM'] = tdat.VOM * tdat['Summer.capacity']
    tdat['wFOM'] = tdat.FOM * tdat['Summer.capacity']
    tdat['solveYearOnline'] = tdat.onlineyear * tdat['Summer.capacity']    

    zout = pd.DataFrame()
    level_cols = ['wHR', 'wVOM', 'wFOM', 'solveYearOnline']
#    Adjust the hr, vom, fom and solveyearonline
    for i in list(range(2010, tdat.RetireYear.max() + 1)):
        # subset on years earlier than i
        ydat = tdat.loc[tdat.RetireYear > i,
                        ['id', 'bin', 'Summer.capacity'] + level_cols
                        ]
#        sum up the parameters by id and bin
        ydat = ydat.groupby(['id', 'bin']).sum()

#        levelize parameters
        for j in level_cols:
            ydat[j] /= ydat['Summer.capacity']

        ydat['year'] = i
#        paste dataframes together
        zout = pd.concat([zout, ydat])
        
#    parse id
    zout.reset_index(inplace=True)
    zout['tech'] = zout.id.str.split('_', n=1, expand=True)[0]
    zout['ba'] = zout.id.str.split('_', n=1, expand=True)[1]
    zout.drop(columns='id', inplace=True)

    #    get dpv generators
    dpv = (pd
           .read_csv(os.path.join(cwd, 'inputs', 'dGen_Model_Inputs',
                                  distpvscen,
                                  'distPVcap_{}.csv'.format(distpvscen)
                                  )
                     )
           .melt(id_vars='Unnamed: 0')
           )

    dpv.rename(columns=dict(zip(dpv.columns,
                                ['ba', 'year', 'Summer.capacity'])),
               inplace=True)

    # initiate columns for dpv dataframe
    dpv['tech'] = 'distPV'
    dpv['wHR'] = 0
    dpv['wVOM'] = 0
    dpv['wFOM'] = 0
    dpv['bin'] = 1
    dpv['solveYearOnline'] = 2010

    # concat dpv and the output dataframes
    zout = pd.concat([zout, dpv])

    #get forced retirement dataframe and merge onto output dataframe
    forced_retire = pd.read_csv(os.path.join(cwd, "inputs", "state_policies",
                                             "forced_retirements.csv"),
                                header=None)
    forced_retire.rename(columns=dict(zip(forced_retire.columns,
                                          ['tech', 'ba', 'retire_year'])),
                         inplace=True)
    zout = zout.merge(forced_retire,
                      how='left',
                      on=['tech', 'ba']).fillna(9000)
    
    # zero out retired generators' capacity
    zout.loc[zout.solveYearOnline >= zout.retire_year, 'Summer.capacity'] = 0
    
    # clean up output dataframe
    zout['bin'] = 'init-' + zout['bin'].astype(str)
    zout['solveYearOnline'] = zout['solveYearOnline'].round()
    zout['wFOM'] *= 1e3
    cols = ['tech', 'bin', 'ba', 'year', 'Summer.capacity', 'wHR',
            'wFOM', 'wVOM', 'solveYearOnline']
    zout = zout[cols]
    zout.rename(columns={'Summer.capacity': 'cap',
                         'solveYearOnline': 'wOnlineYear',
                         'year': 'yr',
                         'tech': 'TECH'},
                inplace=True)
    zout.cap = zout.cap.round(decimals=1)
    zout.wHR = zout.wHR.round(decimals=1)
    zout.wFOM = zout.wFOM.round(decimals=3)
    zout.wVOM = zout.wVOM.round(decimals=3)

    # save output dataframe in inputs_case folder
    zout.dropna().to_csv(os.path.join(outdir, 'hintage_data.csv'), index=False)


# %% body
if __name__ == '__main__':
    # %%
    parser = argparse.ArgumentParser()
    parser.add_argument('cwd',
                        type=str,
                        help='Path to local ReEDS repo')
    parser.add_argument('nBin',
                        type=str,
                        help='Maximum number of bins for generator grouping')
    parser.add_argument('retscen',
                        type=str,
                        help='Retirement Scenario')
    parser.add_argument('mindev',
                        type=int,
                        help='Minimum distance between bins')
    parser.add_argument('distpvscen',
                        type=str)
    parser.add_argument('genunitfile',
                        type=str)
    parser.add_argument('outdir',
                        type=str)
    parser.add_argument('waterconstraints',
                        nargs='?',
                        default='0',
                        type=bool)

    args = vars(parser.parse_args())
    main(**args)