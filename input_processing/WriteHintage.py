# -*- coding: utf-8 -*-
"""

The purpose of this script is to group existing generating 
units into historical, binned vintages (hintages) 

The primary arguments are the plant data file to use, the number of bins, 
and the minimum deviation across bins. There are also operations specific
to proessing data for whether or not waterconstraints are enabled. 

Kmeans clustering is the default option and the general sequence, by tech and 
BA combinations, is as follows:
    
    1. Check to see if the number of unique units is less than the number of bins
       - if true, check to see if the deviation across all those different units exceeds the minimum deviation
         - if true, use the raw data and assign bins to each individual units
         - if false, proceed with binning 
       - if false, proceed with binning
    2. Perform capacity-weighted kmeans clustering with the maximum number of bins
       - Maximum number of bins first defined as the minimum of..
         - number of bins assigned by user
         - number of unique heat rates
         - number of units in the tech/BA combination
    3. Check to see if the deviation across all heat rate centroids exceed the minimum deviation 
       - if so, proceed to '4'
       - if not, return to '2' but reduce the number of bins by 1
    4. Assign units to their nearest heat rate bin
       - if only one unique unit in a bin, assign its original heat rate
       - if more than one unit in a bin, assign the capacity-weighted average
    5. For all years from 2010-2100, compute the remaining amount of capacity
       based on the units specified retirement date and compute the remaining
       units' capacity-weighted-average characteristics (FOM/VOM/HR/...)

---

For testing - the default arguments are passed in to the main(...) function

"""
#%% direct print and errors to log file
import sys
sys.stdout = open('gamslog.txt', 'a')
sys.stderr = open('gamslog.txt', 'a')
# Time the operation of this script
from ticker import toc
import datetime
import math

tic = datetime.datetime.now()

# %% packages
import os
import pandas as pd
import argparse
import numpy as np
from sklearn.cluster import KMeans


# %% functions and classes
class grouping:
    def __init__(self, nbins, *args, **kwargs):
        #df = tdat
        #nbins=6
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
        #Note: The calculations here and below in group() can probably be done faster by group (without a loop).
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
        
        input_df: (pandas.DataFrame object) containing ReEDS generators
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
            df = input_df.copy()
            
            #if the number of unique heat rates is already less than the number of bins
            if len(df[col].unique()) <= bins:
                #no matter what, set the bins to the number of unique heat rates
                self.bins = len(df[col].unique())

                # in order for us to skip binning, we'll need to check
                # if the minimum difference across all unique heat rates
                # exceeds the minSpread - if so, we can justify
                # avoiding the binning algorithm
                if len(df[col].unique()) > 1:
                    mindiff_unique = min([abs(j-i) for i, j in zip(df[col].unique()[:-1], 
                                                                   df[col].unique()[1:])])
                    
                #note that if we only have one unique value for this tech/BA combo 
                #heat rate, then we can skip binning altogether
                if len(df[col].unique()) == 1:
                    mindiff_unique = minSpread + 1
                
            # if the number of unique elements is greater than the number of bins
            # make sure we skip the following condition and perform binning
            else:
                mindiff_unique = minSpread + 1
            
            # if you can use the raw data as is - ie if the observed heat rates
            # are disparate enough such that they exceed minspread and the 
            # the number of units is not greater than the number of bins -
            # then just use the raw data
            if len(df[col].unique()) <= bins and mindiff_unique > minSpread:
                bins = len(df[col].unique())
                # if the maximum deviation across all heat rates 
                # is less than the minimum deviation
                if (df[col].max() - df[col].min()) < minSpread:
                    # put all units into one bin
                    df['centroid'] = df[col].mean()
                    df['bin'] = 1
                else:
                    df['centroid'] = df[col]
                    temp = pd.DataFrame(data=dict(centroid=df[col].unique(), bin=None))
                    temp.bin = temp.index + 1
                    df = df.merge(temp, on='centroid', how='left')
                self.centers = df
            
            # if you can't just use the raw data
            else:
                # if the number of bins exceeds the number of observations
                # reset the number of bins to the length of the data
                # note if the heat rates were not disparate enough
                # we would've caught that in the previous condition block
                if bins > len(df.index):
                    self.bins = max(len(df)-1, 1)
    
                # make a temporary binning DF
                bin_df = pd.concat([df[col],
                                   pd.DataFrame(columns=['centroid', 'upper',
                                                         'lower', 'bin'])])
                bin_df.rename(columns={0: col}, inplace=True)
    
                # establish parameters necessary for the while loop
                spread = minSpread - 1
                nbins = self.bins
                
                # while the minimum spread hasn't been exceeded
                # and the number of bins haven't been exhausted
                # keep attempting to cluster - if these conditions
                # haven't been met, try again with one fewer bin                
                while spread < minSpread or nbins == 1:  
                    df = input_df.copy()
                    
                    # initialize the centroids - note that the
                    # random_state argument implies a static seed
                    # for the random processes/distribution-draws 
                    # used in the kmeans function           
                    centroids_obj = KMeans(
                        n_clusters=nbins, random_state=0, max_iter=1000
                    ).fit(df[[col]].to_numpy(), sample_weight = df['Summer.capacity'].to_numpy())
                    
                    #need to convert array of length-one arrays to one long array
                    centroids = [ i[0] for i in centroids_obj.cluster_centers_]

                    # create a list of unique centroids
                    centroids = list(set(centroids))
                                        
                    # make the binning matrix
                    k = pd.DataFrame(index=df[col], columns=centroids).reset_index()
                    k = k.set_index('HR')

                    # compute the difference between the observed heat rate and the centroid                                        
                    for c in centroids:
                        k[c] = abs(k.index - c)
                        
                    # select the closest centroid
                    k['centroid'] = k.columns[k[centroids].values.argmin(1)]
        
                    # Merge centroids onto original DF
                    k_bins = k.centroid.drop_duplicates().reset_index().copy()
                    k_bins['bin'] = k_bins.index + 1
                    k_map = k.reset_index().merge(k_bins[['centroid', 'bin']],
                                                  on='centroid',
                                                  how='left').set_index('HR')
                    
                    # find the minimum deviation across all heat rate combinations
                    if len(centroids)>1:
                        spread = min([abs(j-i) for i, j in zip(k['centroid'].unique()[:-1], 
                                                               k['centroid'].unique()[1:])])
                    # if there is only one centroid, 
                    # set the conditional to exit the while loop
                    else:
                        spread = minSpread + 1 
                    
                    #reset the index for formatting
                    k_map.reset_index(inplace=True)                    
                                   
                    nbins -= 1
                    #end of while loop for nbins and spread < minspread check
                
                # merge the binned heat rates with the original plant data
                # this will be the output to the kmeans function
                self.centers = df.merge(k_map.drop_duplicates()[[col, 'centroid', 'bin']],
                                        how='left', on=col)
    
    def kmeans(self, nbins, input_df, *args, **kwargs):
        '''
        bin and return the centroids or breakpoints of each bin

        df (DataFrame object): Pandas Dataframe containing data for binning
        col (str): the column name that is to be binned
        bins (int): the number of desired bins
        *args: collects unused positional arguments to simplify code
        **kwargs: collects unused keyword arguments to simplify code
        '''
        print("Starting kmeans clustering of existing generators")
        print("using {} bins and a minimum deviation of {} mmBTU/MWh \n".format(
            nbins, kwargs['minSpread']))
        print("Note that the clustering can result in warnings if the heat rates")
        print("or number of unique plants exceeds the bins specified in the loop")
        tdat=pd.DataFrame()
        
        # for all unique BA/technology combinations...
        for i in input_df.id.unique():
            tdat = pd.concat([tdat,
                              self._kmeans(input_df[input_df.id == i],
                                     'HR',
                                     nbins,
                                     minSpread=int(kwargs['minSpread'])
                                     ).centers])
        return tdat

# %% MAIN
def main(cwd="/users/mbrown1/Documents/GitHub/MI_R2",
         nBin=6,
         retscen="NukeRefRetireYear",
         mindev=50,
         distpvscen='StScen2020_Mid_Case',
         genunitfile='ReEDS_generator_database_final_EIA-NEMS.csv',
         outdir="/users/mbrown1/Desktop",
         waterconstraints='0',
         make_plots=0):
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
    # them alone
    if waterconstraints == '1':
        indat['tech'] = indat.coolingwatertech

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

    # subset only generators that have these NAICS category
    naics_cats = ["Hydroelectric Power Generation",
                  "Nuclear Electric Power Generation",
                  "Other Electric Power Generation",
                  "Electric Power Generation",
                  "Electric Power Distribution",
                  "Utilities",
                  "Electric Power Generation, Transmission and Distribution"
                  ]
    ad = ad[(ad.NAICS.isin(naics_cats))]

    # make the solve year column
    ad['onlineyear'] = (ad['Solve.Year.Online']
                        .str
                        .split('-', expand=True)[0]
                        .astype(float)
                        .round()
                        .astype(int)
                        )

    # format regions column
    ad['pcn'] = (ad
                .PCA
                .str
                .strip('p')
                .astype(float)
                .round()
                .astype(int)
                )

    # only want those with a heat rate - all other binning is arbitrary
    # because the only data we get from genunitfile is the capacity and heat
    # rate but O&M costs are assumed
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
    
    # bin hintage data - this leverages the kmeans function in
    # the grouping class to perform the operations in the _kmeans sub-class
    # and returns the 'dat' dataframe with the additional 'bin' column
    tdat = grouping(nBin, dat, 'HR', minSpread=mindev).df
    
    # calculate the capacity-weighted average heat rate for each bin 
    # by taking the product of the sum of the capacity and the centroid of the bin
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
    if waterconstraints == '1':
        zout['tech'] = zout.id.str.rsplit('_', n=1, expand=True)[0]
        zout['ba'] = zout.id.str.rsplit('_', n=1, expand=True)[1]
    else:
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
    zout['bin_int'] = zout['bin'] #keep integer bins in dataframe for ease of plotting
    zout['bin'] = 'init-' + zout['bin'].astype(str)
    zout['solveYearOnline'] = zout['solveYearOnline'].round()
    zout['wFOM'] *= 1e3
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
    cols = ['TECH', 'bin', 'ba', 'yr', 'cap', 'wHR',
        'wFOM', 'wVOM', 'wOnlineYear']
    zout[cols].dropna().to_csv(os.path.join(outdir, 'hintage_data.csv'), index=False)


    # Make plots comparing actual unit heatrates with binned ones, if desired
    if make_plots:
        import matplotlib.pyplot as plt
        # Create facet plots for heatrate, FO&M, VO&M, and online year
        allgens = pd.merge(
            tdat.loc[
                (tdat.RetireYear > 2020) & (tdat['onlineyear'] < 2020),
                ['TECH','PCA','bin','HR','FOM','VOM','onlineyear','Summer.capacity']],
            zout.loc[zout.yr==2020],
            left_on=['PCA','TECH','bin'],
            right_on=['ba','TECH','bin_int'],
            how='left')
        
        
        ## Summary scatter plot for all techs
        plt.close()
        plt.scatter(allgens['HR'],allgens['wHR'],c=allgens['Summer.capacity'],alpha=0.15)
        plt.rcParams["figure.figsize"] = (7,10)
        color_bar = plt.colorbar()
        color_bar.set_label('Summer Capacity (MW)')
        #Plot an abline of slope 1 for reference
        x_vals = np.array((0,45000))
        y_vals = 1 * x_vals
        plt.plot(x_vals, y_vals)
        plt.title('Hintage Binning Results for All BAs and All Techs')
        plt.xlabel("Actual Heat Rate (MMBtu / MWh)")
        plt.ylabel("Binned Heat Rate (MMBtu / MWh)")
        plt.savefig(os.path.join(outdir, 'hintage_data_2020_heatrate_binning_summary.png'))


        ## Faceted scatter plot showing a fairly random selection of nine BAs for all techs
        # Get color axes range to set static across subplots:
        color_col = 'onlineyear'
        bas_to_plot = ['p1','p2','p3','p50','p51','p52','p110','p120','p130']
        vmin_global = min([ allgens.loc[allgens['ba']==ba,color_col].min() for ba in bas_to_plot])
        vgmax_global = max([ allgens.loc[allgens['ba']==ba,color_col].max() for ba in bas_to_plot])

        plt.close()
        f = plt.figure()    
        f, axes = plt.subplots(nrows = 3, ncols = 3, figsize=(12,12), sharex=True, sharey = True)

        axes = axes.ravel()
        for i,ba in zip(range(9),bas_to_plot):
            im = axes[i].scatter(allgens.loc[allgens['ba']==ba,'HR'],
                                 allgens.loc[allgens['ba']==ba,'wHR'],
                                 c=allgens.loc[allgens['ba']==ba,color_col],
                                 vmin=vmin_global,
                                 vmax=vgmax_global)
            
            #Plot an abline of slope 1 for reference
            x_vals = np.array((5000,25000))
            y_vals = 1 * x_vals
            axes[i].plot(x_vals, y_vals)
            axes[i].set_title(ba)
        
        # Add common axis labels:
        f.add_subplot(111, frame_on=False)
        plt.tick_params(labelcolor="none", bottom=False, left=False)
        plt.xlabel("Actual Heat Rate (MMBtu / MWh)")
        plt.ylabel("Binned Heat Rate (MMBtu / MWh)",labelpad=20)

        f.subplots_adjust(right=0.8)
        cbar_ax = f.add_axes([0.85,0.1,0.03,0.8]) 
        color_bar = f.colorbar(im, cax=cbar_ax)
        color_bar.set_label(color_col)

        plt.savefig(os.path.join(outdir, 'hintage_data_2020_BA_binning_examples_all_techs.png'))


        ## Faceted scatter plot showing the BA with the highest number of units for each tech 
        # (i.e. where our binning assumptions have the most impact)
        color_col = 'onlineyear'
        allgens.groupby(["PCA", "TECH"]).count().groupby('TECH').max()
        bas_with_max_num_units_by_tech = (
            allgens.groupby(["PCA", "TECH"]).count()
            .groupby('TECH').idxmax()['bin_x'].tolist()
        )

        # Get color axes range to set static across subplots:
        vmin_global = min(
            [allgens.loc[(allgens['ba']==ba) & (allgens['TECH']==tech), color_col].min()
             for ba,tech in bas_with_max_num_units_by_tech])
        vgmax_global = max(
            [allgens.loc[(allgens['ba']==ba) & (allgens['TECH']==tech), color_col].max()
             for ba,tech in bas_with_max_num_units_by_tech])

        # Create plot:
        plt.close()
        f = plt.figure()    
        num_cols = math.floor(math.sqrt(len(bas_with_max_num_units_by_tech)))
        add_row = math.ceil(math.sqrt(len(bas_with_max_num_units_by_tech)) % num_cols)

        f, axes = plt.subplots(
            nrows=(num_cols + add_row), ncols=num_cols, figsize=(14,12), sharex=True, sharey=True)

        axes = axes.ravel()
        i=0
        for ba,tech in bas_with_max_num_units_by_tech:
            im = axes[i].scatter(
                allgens.loc[(allgens['ba']==ba) & (allgens['TECH']==tech),'HR'],
                allgens.loc[(allgens['ba']==ba) & (allgens['TECH']==tech),'wHR'],
                c=allgens.loc[(allgens['ba']==ba) & (allgens['TECH']==tech),color_col],
                vmin=vmin_global,
                vmax=vgmax_global)
            
            #Plot an abline of slope 1 for reference
            x_vals = np.array((5000,25000))
            y_vals = 1 * x_vals
            axes[i].plot(x_vals, y_vals)

            num_units = len(allgens.loc[(allgens['ba']==ba) & (allgens['TECH']==tech),'HR'])
            axes[i].set_title(f'{tech} in {ba}: {num_units} units')

            i += 1
        
        # Add common axis labels:
        f.add_subplot(111, frame_on=False)
        plt.tick_params(labelcolor="none", bottom=False, left=False)
        plt.xlabel("Actual Heat Rate (MMBtu / MWh)")
        plt.ylabel("Binned Heat Rate (MMBtu / MWh)",labelpad=20)

        f.subplots_adjust(right=0.8)
        cbar_ax = f.add_axes([0.85,0.1,0.03,0.8]) 
        color_bar = f.colorbar(im, cax=cbar_ax)
        color_bar.set_label(color_col)

        plt.savefig(os.path.join(outdir, 'hintage_data_2020_BAs_with_max_num_units_of_each_tech.png'))


        corrcoef = allgens['HR'].corr(allgens['wHR'])
        print(f'Pearson correlation coefficient between actual and binned heat rates is {corrcoef}')


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
                        type=str)

    args = vars(parser.parse_args())
    main(**args)

    toc(tic=tic, year=0, process='input_processing/WriteHintage.py', 
        path=os.path.join(args['outdir'],'..'))
