import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import os, sys, math, site

import geopandas as gpd
import shapely
os.environ['PROJ_NETWORK'] = 'OFF'

reedspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
remotepath = '/Volumes/ReEDS/' if sys.platform == 'darwin' else r'//nrelnas01/ReEDS/'

### Format plots and load other convenience functions
site.addsitedir(os.path.join(reedspath,'postprocessing'))
import plots
plots.plotparams()


def get_zonemap(case):
    """
    Get geodataframe of model zones, applying aggregation if necessary
    """
    ###### Load original shapefiles
    ### Model zones
    dfba_in = (
        gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','US_PCA'))
        .set_index('rb')
    )
    ### Transmission endpoints
    endpoints = (
        gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','transmission_endpoints'))
        .set_index('ba_str')
    )
    ### Keep transmission endpoints in model zones dataframe
    endpoints['x'] = endpoints.centroid.x
    endpoints['y'] = endpoints.centroid.y
    dfba_in['x'] = dfba_in.index.map(endpoints.x)
    dfba_in['y'] = dfba_in.index.map(endpoints.y)
    dfba_in.st = dfba_in.st.str.upper()

    dfba = dfba_in.copy()

    ###### Apply aggregation if necessary
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'),
        header=None, index_col=0, squeeze=True)

    if 'GSw_AggregateRegions' not in sw:
        return dfba

    if int(sw['GSw_AggregateRegions']):
        ### Load original hierarchy file
        hierarchy = pd.read_csv(
            os.path.join(
                reedspath,'inputs','hierarchy{}.csv'.format(
                    '' if (sw['GSw_HierarchyFile'] == 'default')
                    else '_'+sw['GSw_HierarchyFile'])),
            index_col='*r'
        )
        ### Load mapping from aggreg's to anchor regions
        aggreg2anchorreg = pd.read_csv(
            os.path.join(case, 'inputs_case', 'aggreg2anchorreg.csv'),
            index_col='aggreg', squeeze=True)
        ### Map original model regions to aggregs
        rb2aggreg = hierarchy.aggreg.copy()
        dfba['aggreg'] = dfba.index.map(rb2aggreg)
        dfba = dfba.dissolve('aggreg')
        ### Get the endpoints from the anchor regions
        dfba['x'] = dfba.index.map(aggreg2anchorreg).map(endpoints.x)
        dfba['y'] = dfba.index.map(aggreg2anchorreg).map(endpoints.y)
    
    return dfba


def plotdiff(val, casebase, casecomp, runspath, onlytechs=None, plot_kwds=None, titleshorten=0):
    """
    """
    ### Shared inputs
    ycol = {
        '3_Generation (TWh)': 'Generation (TWh)',
        '4_Capacity (GW)': 'Capacity (GW)',
        '5_New Annual Capacity (GW)': 'Capacity (GW)',
        '6_Annual Retirements (GW)': 'Capacity (GW)',
        '7_Final Gen by timeslice (GW)': 'Generation (GW)',
        '11_Firm Capacity (GW)': 'Firm Capacity (GW)',
        '12_Curtailment Rate': 'Curt Rate',
        '14_Transmission (GW-mi)': 'Amount (GW-mi)',
        '15_Bulk System Electricity Pric': '$',
        '18_National Average Electricity': 'Average cost ($/MWh)',
        '24_2020-2050 Present Value of S': 'Discounted Cost (Bil $)',
    }
    xcol = {
        '3_Generation (TWh)': 'year',
        '4_Capacity (GW)': 'year',
        '5_New Annual Capacity (GW)': 'year',
        '6_Annual Retirements (GW)': 'year',
        '7_Final Gen by timeslice (GW)': 'timeslice',
        '11_Firm Capacity (GW)': 'year',
        '12_Curtailment Rate': 'year',
        '14_Transmission (GW-mi)': 'year',
        '15_Bulk System Electricity Pric': 'year',
        '18_National Average Electricity': 'year',
        '24_2020-2050 Present Value of S': 'dummy',
    }
    width = {
        '3_Generation (TWh)': 1.9,
        '4_Capacity (GW)': 1.9,
        '5_New Annual Capacity (GW)': 1.9,
        '6_Annual Retirements (GW)': 1.9,
        '7_Final Gen by timeslice (GW)': 0.9,
        '11_Firm Capacity (GW)': 1.9,
        '12_Curtailment Rate': 1.9,
        '14_Transmission (GW-mi)': 1.9,
        '15_Bulk System Electricity Pric': 1.9,
        '18_National Average Electricity': 0.95,
        '24_2020-2050 Present Value of S': 20,
    }
    colorcol = {
        '3_Generation (TWh)': 'tech',
        '4_Capacity (GW)': 'tech',
        '5_New Annual Capacity (GW)': 'tech',
        '6_Annual Retirements (GW)': 'tech',
        '7_Final Gen by timeslice (GW)': 'tech',
        '11_Firm Capacity (GW)': 'tech',
        '12_Curtailment Rate': 'dummy',
        '14_Transmission (GW-mi)': 'type',
        '15_Bulk System Electricity Pric': 'type',
        '18_National Average Electricity': 'cost_cat',
        '24_2020-2050 Present Value of S': 'cost_cat',
    }
    fixcol = {
        '3_Generation (TWh)': {},
        '4_Capacity (GW)': {},
        '5_New Annual Capacity (GW)': {},
        '6_Annual Retirements (GW)': {},
        '7_Final Gen by timeslice (GW)': {},
        '11_Firm Capacity (GW)': {'season':'summ'},
        '12_Curtailment Rate': {},
        '14_Transmission (GW-mi)': {},
        '15_Bulk System Electricity Pric': {},
        '18_National Average Electricity': {},
        '24_2020-2050 Present Value of S': {},
    }
    tfix = {
        '15_Bulk System Electricity Pric': '15_Bulk System Electricity Price ($/MWh)',
        '$': 'Price ($/MWh)',
        '24_2020-2050 Present Value of S': '24_2020-2050 Present Value of System Cost (Bil $)',
    }
    ylabel = {
        '3_Generation (TWh)': 'Generation [TWh]',
        '4_Capacity (GW)': 'Capacity [GW]',
        '5_New Annual Capacity (GW)': 'Capacity [GW]',
        '6_Annual Retirements (GW)': 'Capacity [GW]',
        '7_Final Gen by timeslice (GW)': 'Generation [GW]',
        '11_Firm Capacity (GW)': 'Firm Capacity [GW]',
        '12_Curtailment Rate': 'Curtailment [%]',
        '14_Transmission (GW-mi)': 'Transmission capacity [TW-mi]',
        '15_Bulk System Electricity Pric': 'Marginal cost [$/MWh]',
        '18_National Average Electricity': 'Average cost [$/MWh]',
        '24_2020-2050 Present Value of S': '[$Billion]',
    }
    scaler = {
        '3_Generation (TWh)': 1,
        '4_Capacity (GW)': 1,
        '5_New Annual Capacity (GW)': 1,
        '6_Annual Retirements (GW)': 1,
        '7_Final Gen by timeslice (GW)': 1,
        '11_Firm Capacity (GW)': 1,
        '12_Curtailment Rate': 100,
        '14_Transmission (GW-mi)': 0.001,
        '15_Bulk System Electricity Pric': 1,
        '18_National Average Electricity': 1,
        '24_2020-2050 Present Value of S': 1,
    }
    
    colors_tech = pd.read_csv(
        os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order')['color']
    colors_cost = pd.read_csv(
        os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','cost_cat_style.csv'),
        index_col='order')['color']
    colors_trans = pd.read_csv(
        os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
        index_col='order')['color']
    colors_tech = {
        **colors_tech,
        **{'ac':'C0','dc':'C1','vsc':'C3'},
        **{'load':'C0', 'nat_gen':'C1', 'nat_rps':'C1', 'oper_res':'C2', 
           'res_marg':'C3', 'state_rps':'C4',},
        **{'Capital':'C0','PTC':'C2','O&M':'C3','Fuel':'C4','Trans':'C1'},
        'dummy':'C0',
        **colors_cost,
        **colors_trans,
    }

    ### Load the data
    dfbase = pd.read_excel(
        os.path.join(runspath,casebase,'outputs','reeds-report/report.xlsx'),
        sheet_name=val, engine='openpyxl',
    ).rename(columns={'trtype':'type'})
    if colorcol[val] == 'dummy':
        dfbase['dummy'] = 'dummy'
    for col in fixcol[val]:
        dfbase = dfbase.loc[dfbase[col] == fixcol[val][col]].copy()
    dfcomp = pd.read_excel(
        os.path.join(runspath,casecomp,'outputs','reeds-report/report.xlsx'),
        sheet_name=val, engine='openpyxl',
    ).rename(columns={'trtype':'type'})
    
    if colorcol[val] == 'dummy':
        dfcomp['dummy'] = 'dummy'
    if xcol[val] == 'dummy':
        dfbase['dummy'] = 0
        dfcomp['dummy'] = 0
    for col in fixcol[val]:
        dfcomp = dfcomp.loc[dfcomp[col] == fixcol[val][col]].copy()
    # indices = sorted(dfbase[xcol[val]].unique())
    indices = dfbase[xcol[val]].unique()
    ### Apply the scaler
    dfbase[ycol[val]] *= scaler[val]
    dfcomp[ycol[val]] *= scaler[val]
    ### Take the diff
    dfdiff = dfbase.drop(['scenario'],1).merge(
        dfcomp.drop(['scenario'],1), on=[colorcol[val],xcol[val]], how='outer',
        suffixes=('_base','_comp')).fillna(0)
    dfdiff['{}_diff'.format(ycol[val])] = (
        dfdiff['{}_comp'.format(ycol[val])] - dfdiff['{}_base'.format(ycol[val])])
    # techs = dfdiff.loc[dfdiff[xcol[val]]==indices[0],colorcol[val]].values
    techs = dfdiff[colorcol[val]].unique()
    if onlytechs is not None:
        techs = onlytechs
    for tech in techs:
        if tech not in colors_tech:
            colors_tech[tech] = 'k'
    ###### Plot it
    plt.close()
    if plot_kwds is None:
        plot_kwds = {'figsize':(13,4)}
    f,ax=plt.subplots(1,3,sharex=True,**plot_kwds)
    ### Base
    for index in indices:
        ### Negative
        negtechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_base']<0),colorcol[val]]
        negheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(negtechs)),
            ycol[val]+'_base'
        ].loc[negtechs.index]
        bottom = negheight.cumsum()
        ax[0].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-negheight.values,
            width=width[val], color=[colors_tech[i] for i in negtechs], lw=0, 
        )
        ### Positive
        postechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_base']>=0),colorcol[val]]
        posheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(postechs)),
            ycol[val]+'_base'
        ].loc[postechs.index]
        bottom = posheight.cumsum()
        ax[0].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-posheight.values,
            width=width[val], color=[colors_tech[i] for i in postechs], lw=0, 
        )
    printbase = negheight.sum() + posheight.sum()
    ### Comp
    for index in indices:
        ### Negative
        negtechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_comp']<0),colorcol[val]]
        negheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(negtechs)),
            ycol[val]+'_comp'
        ].loc[negtechs.index]
        bottom = negheight.cumsum()
        ax[1].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-negheight.values,
            width=width[val], color=[colors_tech[i] for i in negtechs], lw=0, 
        )
        ### Positive
        postechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_comp']>=0),colorcol[val]]
        posheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(postechs)),
            ycol[val]+'_comp'
        ].loc[postechs.index]
        bottom = posheight.cumsum()
        ax[1].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-posheight.values,
            width=width[val], color=[colors_tech[i] for i in postechs], lw=0, 
        )
    printcomp = negheight.sum() + posheight.sum()
    print('{}: base: {:.4f}; comp: {:.4f}; comp/base: {:.4f}; comp-base: {:.4f}'.format(
        val,printbase,printcomp,printcomp/printbase,printcomp-printbase))
    ### Diff
    for index in indices:
        ### Negative
        negtechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_diff']<0),colorcol[val]]
        negheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(negtechs)),
            ycol[val]+'_diff'
        ].loc[negtechs.index]
        bottom = negheight.cumsum()
        ax[2].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-negheight.values,
            width=width[val], color=[colors_tech[i] for i in negtechs], lw=0, 
        )
        ### Positive
        postechs = dfdiff.loc[
            (dfdiff[xcol[val]]==index)
            &(dfdiff[colorcol[val]].isin(techs))
            &(dfdiff[ycol[val]+'_diff']>=0),colorcol[val]]
        posheight = dfdiff.loc[
            (dfdiff[xcol[val]]==index)&(dfdiff[colorcol[val]].isin(postechs)),
            ycol[val]+'_diff'
        ].loc[postechs.index]
        bottom = posheight.cumsum()
        ax[2].bar(
            x=[index]*len(bottom), bottom=bottom.values, height=-posheight.values,
            width=width[val], color=[colors_tech[i] for i in postechs], lw=0, 
        )
    ### Sum
        ax[2].plot(
            [index], [negheight.sum() + posheight.sum()], 
            marker='o', lw=0, markerfacecolor='w', markeredgecolor='k')
    ax[2].axhline(0,c='0.5',lw=0.75,ls=':')

    ### Legend
    handles = [
        mpl.patches.Patch(facecolor=colors_tech[i], edgecolor='none', label=i)
        for i in techs
    ]
    leg = ax[2].legend(
        handles=handles[::-1], loc='center left', bbox_to_anchor=(1,0.5), 
        fontsize='large', ncol=len(techs)//12+1, 
        handletextpad=0.3, handlelength=0.7, columnspacing=0.5, 
    )

    ### Formatting
    # ax[0].set_ylabel(tfix.get(ycol[val],ycol[val]))
    ax[0].set_ylabel(ylabel.get(val, val))
    ymax = max(ax[0].get_ylim()[1], ax[1].get_ylim()[1])
    ymin = max(ax[0].get_ylim()[0], ax[1].get_ylim()[0])
    for col in range(2):
        ax[col].set_ylim(ymin,ymax)
    ax[2].set_ylim(
        min(ax[2].get_ylim()[0]*0.95, ax[2].get_ylim()[0]*1.05),
        max(ax[2].get_ylim()[1]*0.95, ax[2].get_ylim()[1]*1.05)
    )
    if xcol[val] == 'year':
        ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
        ax[0].xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(5))
        if val == '18_National Average Electricity':
            for col in range(3):
                ax[col].set_xlim(None,2050)
    elif xcol[val] == 'timeslice':
        for col in range(3):
            ax[col].set_xticks(range(len(indices)))
            ax[col].set_xticklabels(
                indices, rotation=55, rotation_mode='anchor', ha='right', va='center', fontsize=10)
    elif xcol[val] == 'dummy':
        for col in range(3):
            ax[col].xaxis.set_visible(False)
    ax[0].set_title(os.path.basename(casebase)[titleshorten:], x=0, ha='left', size='large', weight='bold')
    ax[1].set_title(os.path.basename(casecomp)[titleshorten:], x=0, ha='left', size='large', weight='bold')
    ax[2].set_title(
        '{}\n– {}'.format(
            os.path.basename(casecomp)[titleshorten:],
            os.path.basename(casebase)[titleshorten:]),
        x=0, ha='left', size='large', weight='bold')
    ax[0].annotate(
        (tfix.get(val,val) 
         + (', ' if len(fixcol[val]) > 0 else '')
         + ', '.join(['{} = {}'.format(col,fixcol[val][col]) for col in fixcol[val]])),
        xy=(0,1.15),xycoords='axes fraction',size='xx-large',weight='bold')

    plots.despine(ax)
    return f,ax,leg, dfdiff


def plot_trans_diff(
        casebase, casecomp,
        pcalabel=False, wscale=0.0003,
        year='last', yearlabel=True,
        colors={'+':'C3', '-':'C0',
                'AC':'C2', 'DC':'C1', 'LCC':'C1', 'VSC': 'C4',
                'AC_init':plt.cm.tab20(5), 'LCC_init':plt.cm.tab20(3), 'B2B_init':plt.cm.tab20(11)},
        alpha=0.75, dpi=None,
        simpletypes=None,
        trtypes=['AC','VSC','DC','LCC','AC_init','LCC_init','B2B_init'],
    ):
    dfba = get_zonemap(casebase)
    dfstates = dfba.dissolve('st')
    
    cases = {'base': casebase, 'comp': casecomp}
    tran_out = {}
    for case in cases:
        tran_out[case] = pd.read_csv(os.path.join(cases[case],'outputs','tran_out.csv'))
        if tran_out[case].Dim3.dtype == int:
            tran_out[case].rename(
                columns={'Dim1':'r','Dim2':'rr','Dim3':'t','Dim4':'trtype','Val':'MW'}, inplace=True)
        else:
            tran_out[case].rename(
                columns={'Dim1':'r','Dim2':'rr','Dim3':'trtype','Dim4':'t','Val':'MW'}, inplace=True)
        if simpletypes is None:
            ### Add initial capacity to new capacity and plot initial capacity on top
            dicttran = {
                i: tran_out[case].loc[tran_out[case].trtype==i].set_index(['r','rr','t']).MW
                for i in trtypes}
            for trtype in ['AC','LCC']:
                dicttran[trtype] = dicttran[trtype].add(dicttran[trtype+'_init'], fill_value=0)
            tran_out[case] = pd.concat(dicttran, axis=0, names=['trtype','r','rr','t']).reset_index()


    dfplot = tran_out['base'].merge(
        tran_out['comp'], on=['r','rr','t','trtype'], suffixes=('_base','_comp'), how='outer').fillna(0)
    dfplot = dfplot.loc[dfplot.t==(dfplot.t.max() if year=='last' else year)].copy()
    dfplot['MW_diff'] = dfplot['MW_comp'] - dfplot['MW_base']


    dfplot['r_x'] = dfplot.r.map(dfba.x)
    dfplot['r_y'] = dfplot.r.map(dfba.y)
    dfplot['rr_x'] = dfplot.rr.map(dfba.x)
    dfplot['rr_y'] = dfplot.rr.map(dfba.y)

    plt.close()
    f,ax=plt.subplots(
        1,3,sharex=True,sharey=True,figsize=(14,8),
        gridspec_kw={'wspace':-0.05, 'hspace':0.05},
        dpi=dpi,
    )

    ###### Shared
    for col in range(3):
        ### Boundaries
        dfba.plot(ax=ax[col], edgecolor='0.5', facecolor='none', lw=0.1)
        dfstates.plot(ax=ax[col], edgecolor='0.5', facecolor='none', lw=0.2)
        ax[col].axis('off')
        ### Labels
        if pcalabel:
            for r in dfba.index:
                ax[col].annotate(
                    r.replace('p',''), dfba.loc[r,['x','y']].values,
                    ha='center', va='center', fontsize=5, color='0.7'
                )

    if yearlabel:
        ax[0].annotate(
            'Year: {}'.format(year), 
            (0.9,0.97), xycoords='axes fraction', fontsize=10, ha='right', va='top')


    ###### Base
    for i in dfplot.index:
        row = dfplot.loc[i]
        ax[0].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=colors[row['trtype']], lw=wscale*row['MW_base'], solid_capstyle='butt',
            alpha=alpha,
        )
    ax[0].annotate(
        os.path.basename(cases['base']),
        (0.1,1), xycoords='axes fraction', fontsize=10)

    ###### Comp
    for i in dfplot.index:
        row = dfplot.loc[i]
        ax[1].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=colors[row['trtype']], lw=wscale*row['MW_comp'], solid_capstyle='butt',
            alpha=alpha,
        )
    ax[1].annotate(
        os.path.basename(cases['comp']),
        (0.1,1), xycoords='axes fraction', fontsize=10)

    ###### Diff
    for i in dfplot.index:
        row = dfplot.loc[i]
        ax[2].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=(colors['+'] if row['MW_diff'] >= 0 else colors['-']), 
            lw=abs(wscale*row['MW_diff']), solid_capstyle='butt', alpha=alpha,
        )
    ax[2].annotate(
        '{}\n– {}'.format(os.path.basename(cases['comp']),os.path.basename(cases['base'])),
        (0.1,1), xycoords='axes fraction', fontsize=10)
    
    ###### Scale
    ax[0].plot(
        [-2.0e6,-1.5e6], [-1.0e6, -1.0e6],
        color='k', lw=wscale*10e3, solid_capstyle='butt'
    )
    ax[0].annotate(
        '10 GW', (-1.75e6, -1.1e6), ha='center', va='top', weight='bold')

    return f, ax


def plot_trans_onecase(
        case, dfin=None,
        pcalabel=False, wscale=0.0003,
        year='last', yearlabel=True,
        colors={'AC':'C2', 'LCC':'C1', 'VSC': 'C3',
                'AC_init':plt.cm.tab20(5), 'LCC_init':plt.cm.tab20(3),
                'B2B_init':plt.cm.tab20(11), 'B2B':plt.cm.tab20(10)},
        dpi=None,
        trtypes=['AC_init','B2B_init','LCC_init','AC','B2B','LCC','VSC'],
        simpletypes={'AC_init':'AC','LCC_init':'LCC','B2B_init':'B2B'},
        zorders={'AC':1e3,'AC_init':2e3,'VSC':3e3,
                 'LCC':4e3,'LCC_init':5e3,'B2B':7e3,'B2B_init':8e3},
        alpha=1, scalesize='x-large',
        f=None, ax=None, scale=True, title=True,
        routes=False, tolerance=1000,
        subtract_baseyear=None, nest_trtypes=False,
        show_overlap=True, show_background=True, show_converters=0.5,
        crs='ESRI:102008',
        thickborders='none', drawstates=True,
    ):
    """
    Notes
    * If colors is a string instead of a dictionary, aggregate all transmission types
    """
    ### Load shapefiles
    dfba = get_zonemap(case)
    dfstates = dfba.dissolve('st')
    if thickborders not in [None,'','none','None',False]:
        hierarchy = pd.read_csv(
            os.path.join(case,'inputs_case','hierarchy.csv')
        ).rename(columns={'*r':'r'}).set_index('r')
        hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()
        if thickborders in hierarchy:
            dfthick = dfba.copy()
            dfthick[thickborders] = hierarchy[thickborders]
            dfthick.geometry = dfthick.buffer(0.)
            dfthick = dfthick.dissolve(thickborders)

    if routes:
        try:
            transmission_routes = gpd.read_file(
                os.path.join(reedspath,'inputs','shapefiles','transmission_routes-500kVac.gpkg')
            ).set_index(['r','rr']).to_crs(crs)
        except FileNotFoundError:
            print('New routes not found so reverting to old routes')
            transmission_routes = gpd.read_file(
                os.path.join(reedspath,'inputs','shapefiles','transmission_routes')
            ).set_index(['from_ba','to_ba']).to_crs(crs)

        if tolerance:
            transmission_routes['geometry'] = transmission_routes.simplify(tolerance)

    ### Load run-specific output data
    if dfin is None:
        tran_out = pd.read_csv(
            os.path.join(case,'outputs','tran_out.csv')
        )
        ### Correct for different parameters orders
        if tran_out.Dim3.dtype == int:
            tran_out.rename(
                columns={'Dim1':'r','Dim2':'rr','Dim3':'t','Dim4':'trtype','Val':'MW'}, inplace=True)
        else:
            tran_out.rename(
                columns={'Dim1':'r','Dim2':'rr','Dim3':'trtype','Dim4':'t','Val':'MW'}, inplace=True)

        if simpletypes is None:
            dicttran = {
                i: tran_out.loc[tran_out.trtype==i].set_index(['r','rr','t']).MW
                for i in trtypes}
            if nest_trtypes:
                ### Stack the different trtypes to get total capacity
                tran_out = (
                    pd.concat(dicttran, axis=1, names=['trtype'])
                    .fillna(0).cumsum(axis=1)[trtypes[::-1]].stack().rename('MW').reset_index())
            else:
                ### Add initial capacity to new capacity and plot initial capacity on top
                for trtype in ['AC','LCC']:
                    dicttran[trtype] = dicttran[trtype].add(dicttran[trtype+'_init'], fill_value=0)
                tran_out = pd.concat(dicttran, axis=0, names=['trtype','r','rr','t']).reset_index()

        else:
            ### Group initial and new capacity together and only plot with the simple name
            tran_out = (
                tran_out
                .assign(trtype=tran_out.trtype.replace(simpletypes))
                .groupby(['r','rr','trtype','t'], as_index=False).sum()
            )


        dfplot = tran_out.loc[
            (tran_out.t==(tran_out.t.max() if year=='last' else year))
            & (tran_out.trtype.isin(trtypes))
        ].copy()

        if subtract_baseyear:
            ### Currently only works for non-aggregated transmission
            dfplot = (dfplot.set_index(['r','rr','trtype']).MW - tran_out.loc[
                (tran_out.t==subtract_baseyear)
                & (tran_out.trtype.isin(trtypes))
            ].set_index(['r','rr','trtype']).MW.reindex(
                dfplot.set_index(['r','rr','trtype']).index).fillna(0)).clip(lower=0).reset_index()
            dfplot = dfplot.loc[dfplot.MW>0].copy()

    ### Otherwise take the correctly-formatted dataframe passed as an input
    else:
        dfplot = dfin.copy()

    ### Aggregate types if colors is a string instead of a dictionary
    if isinstance(colors, str):
        dfplot = dfplot.groupby(['r','rr','t'], as_index=False).MW.sum()

    dfplot['r_x'] = dfplot.r.map(dfba.x)
    dfplot['r_y'] = dfplot.r.map(dfba.y)
    dfplot['rr_x'] = dfplot.rr.map(dfba.x)
    dfplot['rr_y'] = dfplot.rr.map(dfba.y)

    ## Load VSC converter capacity if necessary
    if show_converters and ('VSC' in dfplot.trtype.unique()):
        dfin = pd.read_csv(
            os.path.join(case,'outputs','cap_converter_out.csv'),
            header=0,  names=['r','t','MW'], dtype={'r':str, 't':int, 'MW':float},
        )
        dfconverter = dfba.merge(
            dfin.loc[dfin.t==year], left_index=True, right_on='r'
        )

    ## Make figure if necessary
    if (not f) and (not ax):
        plt.close()
        f,ax = plt.subplots(figsize=(14,8), dpi=dpi,)

    ###### Shared
    ### Boundaries
    if show_background:
        dfba.plot(ax=ax, edgecolor='0.5', facecolor='none', lw=0.1)
        if drawstates:
            dfstates.plot(ax=ax, edgecolor='0.25', facecolor='none', lw=0.2)
        if thickborders not in [None,'','none','None',False]:
            dfthick.plot(ax=ax, edgecolor='C7', facecolor='none', lw=0.5)
    ax.axis('off')
    ### Labels
    if pcalabel:
        for r in dfba.index:
            ax.annotate(
                r.replace('p',''), dfba.loc[r,['x','y']].values,
                ha='center', va='center', fontsize=5, color='0.7'
            )

    if yearlabel and isinstance(case,str):
        ax.annotate(
            'Year: {}'.format(year), 
            (0.9,1), xycoords='axes fraction', fontsize=10, ha='right', va='top')


    ###### Lines
    if routes:
        if show_overlap:
            for i in dfplot.index:
                row = dfplot.loc[i]
                transmission_routes.loc[[(row.r,row.rr)]].buffer(wscale*row['MW']).plot(
                    ax=ax, alpha=alpha,
                    zorder=(1000 if isinstance(colors,str) else zorders[row['trtype']]),
                    color=(colors if isinstance(colors,str) else colors[row['trtype']]),
                )    
        else:
            if isinstance(colors,dict):
                for trtype in trtypes:
                    alllines = gpd.GeoDataFrame(
                        dfplot.loc[dfplot.trtype==trtype]
                        .merge(
                            transmission_routes[['geometry']],
                            left_on=['r','rr'], right_index=True)
                    )
                    alllines['dummy'] = 'dummy'
                    alllines['geometry'] = alllines.buffer(alllines.MW*wscale)
                    alllines = alllines.dissolve('dummy')
                    alllines.plot(ax=ax, alpha=alpha, color=colors[trtype], label=trtype)
            else:
                alllines = gpd.GeoDataFrame(
                    dfplot.merge(
                        transmission_routes[['geometry']],
                        left_on=['r','rr'], right_index=True)
                )
                alllines['dummy'] = 'dummy'
                alllines['geometry'] = alllines.buffer(alllines.MW*wscale)
                alllines = alllines.dissolve('dummy')
                alllines.plot(ax=ax, alpha=alpha, color=colors)

    else:
        if show_overlap:
            for i in dfplot.index:
                row = dfplot.loc[i]
                ax.plot(
                    [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
                    color=(colors if isinstance(colors, str) else colors[row['trtype']]),
                    lw=wscale*row['MW'], solid_capstyle='butt',
                    alpha=alpha,
                )
        else:
            alllines = []
            for i in dfplot.index:
                row = dfplot.loc[i]
                alllines.append(
                    shapely.geometry.LineString(
                        [(row.r_x, row.r_y), (row.rr_x, row.rr_y)]
                    ).buffer(row.MW*wscale)
                )
            alllines = shapely.ops.unary_union(alllines)
            alllines = gpd.GeoSeries([alllines]).set_crs(crs)
            alllines.plot(ax=ax, alpha=alpha, color=colors)

    ###### VSC converters (if necessary)
    if show_converters and ('VSC' in dfplot.trtype.unique()):
        ax.scatter(
            dfconverter.x.values, dfconverter.y.values,
            facecolor='none', edgecolor='k',
            s=((dfconverter.MW.values*wscale)**2 * 3.14 / 4),
            zorder=1E6, lw=show_converters,
        )
    
    ###### Scale
    if title and isinstance(case,str):
        ax.annotate('{} ({})'.format(os.path.basename(case), year),
                    (0.1,1), xycoords='axes fraction', fontsize=10)
    if scale:
        if routes or (not show_overlap):
            gpd.GeoSeries(
                shapely.geometry.LineString([(-1.9e6,-0.9e6),(-1.6e6,-0.9e6)])
            ).buffer(wscale*10e3).plot(
                ax=ax, color=(colors if isinstance(colors,str) else 'k'), alpha=alpha)
        else:
            ax.plot(
                [-1.9e6,-1.6e6], [-0.9e6, -0.9e6],
                color=(colors if isinstance(colors,str) else 'k'),
                lw=wscale*10e3, solid_capstyle='butt',
            )
        ax.annotate(
            '10 GW', (-1.75e6, -1.0e6), ha='center', va='top', weight='bold', fontsize=scalesize)

    return f,ax


def plotdiffmaps(val, i_plot, year, casebase, casecomp, reedspath, 
                 plot='diff', f=None, ax=None, cmap=plt.cm.Blues,
                 dfba=None, dfstates=None, aea=True, zmax=None, zlim=None,
                 legend_kwds=None, plot_kwds=None,):
    """
    Inputs
    ------
    plot: 'diff', 'base', 'comp'
    """
    ###### Shared inputs
    ycols = {
        'gen_h': ['i','r','h','t','GEN'],
        'gen_ann': ['i','r','t','GEN'],
        'cap': ['i','r','t','CAP'],
        'cap_avail': ['i','r','t','rscbin','CAP'],
    }
    units = {
        'gen_h': 'GWh/timeslice',
        'gen_ann': 'TWh/y',
        'cap': 'GW',
        'cap_avail': 'GW',
    }
    unitscaler = {
        'gen_h': 1E-3,
        'gen_ann': 1E-6,
        'cap': 1E-3,
        'cap_avail': 1E-3,
    }
    ### Get the vals
    valcol = ycols[val][-1]
    units = units[val]
    unitscaler = unitscaler[val]
    if legend_kwds is None:
        legend_kwds = {
            'shrink':0.6, 'pad':0,
            'label':'{} {} {} [{}]'.format(valcol,i_plot,year,units),
            'orientation':'horizontal',
        }
    if plot_kwds is None:
        plot_kwds = {'figsize':(10,7.5),'dpi':100,}
    ### Replace column names
    rep_i = {
        'CoalOldScr':'coal', 'CoalOldUns':'coal', 'Coal-IGCC':'coal', 'coal-IGCC':'coal','coal-new':'coal',
        'csp2':'csp','csp-ns':'csp',
        'Gas-CC':'gas-cc', 'Gas-CT':'gas-ct', 'gas-CC':'gas-cc', 'gas-CT':'gas-ct',
        'can-imports':'Canada',
        'Nuclear':'nuclear',
        'undisc':'geothermal',
        'hydED':'hydro', 'hydEND':'hydro', 'hydND':'hydro', 
        'hydNPND':'hydro', 'hydUD':'hydro', 'hydUND':'hydro',
    }
    ### resourceregion-to-ba mapper
    s2r = pd.read_csv(
        os.path.join(reedspath,'inputs','rsmap_sreg.csv'),
        index_col='rs', squeeze=True
    ).to_dict()

    ### Load the data, sum over hours
    dfbase = pd.read_csv(
        os.path.join(casebase,'outputs',val+'.csv'),
        names=ycols[val], header=0,
    ).replace({'r':s2r})
    dfcomp = pd.read_csv(
        os.path.join(casecomp,'outputs',val+'.csv'),
        names=ycols[val], header=0,
    ).replace({'r':s2r})
    
    ### Drop the tails
    # dfbase.i = dfbase.i.map(lambda x: x if x.startswith('battery') else x.split('_')[0])
    # dfcomp.i = dfcomp.i.map(lambda x: x if x.startswith('battery') else x.split('_')[0])
    dfbase.i = dfbase.i.map(lambda x: x.split('_')[0])
    dfcomp.i = dfcomp.i.map(lambda x: x.split('_')[0])

    ### Simplify the i names
    dfbase.i = dfbase.i.map(lambda x: rep_i.get(x,x))
    dfcomp.i = dfcomp.i.map(lambda x: rep_i.get(x,x))

    dfbase = dfbase.groupby(['i','r','t']).sum().reset_index().copy()
    dfcomp = dfcomp.groupby(['i','r','t']).sum().reset_index().copy()
    
    ### Correct the units
    dfbase[valcol] *= unitscaler
    dfcomp[valcol] *= unitscaler
    
    ### Start the plot
    # plt.close()
    if (f is None) and (ax is None):
        f,ax=plt.subplots(**plot_kwds)
    else:
        pass

    ###### Calculate the diff
    dfdiff = dfbase.merge(
        dfcomp, on=['i','r','t'], how='outer', suffixes=('_base','_comp')).fillna(0)
    if plot in ['diff','pctdiff','pct_diff','diffpct','diff_pct','pct']:
        ### Percent difference
        dfdiff['{}_diff'.format(valcol)] = (
            (dfdiff['{}_comp'.format(valcol)] - dfdiff['{}_base'.format(valcol)])
            / dfdiff['{}_base'.format(valcol)] * 100
        ).replace(np.inf,np.nan)
    elif plot in ['absdiff', 'abs_diff', 'diffabs', 'diff_abs']:
        ### Difference
        dfdiff['{}_diff'.format(valcol)] = (
            dfdiff['{}_comp'.format(valcol)] - dfdiff['{}_base'.format(valcol)])
    
    if zmax is None:
        zmax = max(
            dfdiff.loc[(dfdiff.i==i_plot)&(dfdiff.t==year),valcol+'_base'].max(),
            dfdiff.loc[(dfdiff.i==i_plot)&(dfdiff.t==year),valcol+'_comp'].max(),
        )
    
    ###### Plot the base
    if plot == 'base':
        title = casebase
        dfplot = dfba.merge(
            dfbase.loc[(dfbase.i==i_plot)&(dfbase.t==year),['r',valcol]],
            left_index=True, right_on='r', how='left'
        ).fillna(0).reset_index(drop=True)

        dfplot.plot(ax=ax, column=valcol, cmap=cmap, legend=True,
                    legend_kwds=legend_kwds, vmax=zmax)

    ###### Plot the comp
    elif plot == 'comp':
        title = casecomp
        dfplot = dfba.merge(
            dfcomp.loc[(dfcomp.i==i_plot)&(dfcomp.t==year),['r',valcol]],
            left_index=True, right_on='r', how='left'
        ).fillna(0).reset_index(drop=True)

        dfplot.plot(ax=ax, column=valcol, cmap=cmap, legend=True,
                    legend_kwds=legend_kwds, vmax=zmax)

    ###### Plot the pct diff
    elif plot in ['diff','pctdiff','pct_diff','diffpct','diff_pct','pct']:
        title = '({} – {}) / {}'.format(casecomp, casebase, casebase)
        legend_kwds['label'] = '{} {} {}\n[% diff]'.format(valcol,i_plot,year)

        dfplot = dfba.merge(
            dfdiff.loc[(dfdiff.i==i_plot)&(dfdiff.t==year),['r',valcol+'_diff']],
            left_index=True, right_on='r', how='left'
        ).reset_index(drop=True)

        if zlim is None:
            zlim = max(abs(dfplot[valcol+'_pctdiff'].min()), abs(dfplot[valcol+'_pctdiff'].max()))

        dfplot.plot(ax=ax, column=valcol+'_pctdiff', cmap=cmap, legend=True,
                    vmin=-zlim, vmax=+zlim, legend_kwds=legend_kwds)

    ###### Plot the absolute diff
    elif plot in ['absdiff', 'abs_diff', 'diffabs', 'diff_abs']:
        title = '{} – {}'.format(casecomp, casebase)
        legend_kwds['label'] = '{}diff {} [{}]'.format(valcol,i_plot,units)

        dfplot = dfba.merge(
            dfdiff.loc[(dfdiff.i==i_plot)&(dfdiff.t==year),['r',valcol+'_diff']],
            left_index=True, right_on='r', how='left'
        ).reset_index(drop=True)

        if zlim is None:
            zlim = max(abs(dfplot[valcol+'_diff'].min()), abs(dfplot[valcol+'_diff'].max()))

        dfplot.plot(ax=ax, column=valcol+'_diff', cmap=plt.cm.bwr, legend=True,
                    vmin=-zlim, vmax=+zlim, legend_kwds=legend_kwds)

    ### Finish and return
    # ax.set_title(title, y=0.95)
    dfstates.plot(ax=ax, edgecolor='k', facecolor='none', lw=0.25)
    ax.axis('off')

    return f,ax,dfplot


def plot_trans_vsc(
        case, year=2050, wscale=0.4, alpha=1.0, miles=300,
        cmap=plt.cm.gist_earth_r, scale=True, title=True,
        convertermax=None,
        f=None, ax=None,
    ):
    """
    """
    ### Get the BA map
    dfba = get_zonemap(case)
    dfstates = dfba.dissolve('st')

    ### Load converter capacity
    dfin = pd.read_csv(
        os.path.join(case,'outputs','cap_converter_out.csv'),
        header=0,  names=['r','t','MW'], dtype={'r':str, 't':int, 'MW':float},
    )
    dfconverter = dfba.merge(
        dfin.loc[dfin.t==year], left_index=True, right_on='r'
    ).rename(columns={'MW':'GW'})
    dfconverter.GW /= 1000

    ### Load transmission capacity
    tran_out = pd.read_csv(
        os.path.join(case,'outputs','tran_out.csv')
    )
    if tran_out.Dim3.dtype == int:
        tran_out.rename(
            columns={'Dim1':'r','Dim2':'rr','Dim3':'t','Dim4':'trtype','Val':'MW'},
            inplace=True)
    else:
        tran_out.rename(
            columns={'Dim1':'r','Dim2':'rr','Dim3':'trtype','Dim4':'t','Val':'MW'},
            inplace=True)

    dfplot = tran_out.copy()
    dfplot = dfplot.loc[
        (dfplot.t==year) & (dfplot.trtype == 'VSC')
    ].copy()
    dfplot['GW'] = dfplot['MW'] / 1000

    dfplot['r_x'] = dfplot.r.map(dfba.x)
    dfplot['r_y'] = dfplot.r.map(dfba.y)
    dfplot['rr_x'] = dfplot.rr.map(dfba.x)
    dfplot['rr_y'] = dfplot.rr.map(dfba.y)

    ### Plot it
    if (not f) and (not ax):
        plt.close()
        f,ax=plt.subplots(figsize=(14,8))

    ### Converter capacity
    if cmap:
        axheight = ax.get_window_extent().transformed(f.dpi_scale_trans.inverted()).height
        cbar_label = ('Converter capacity [GW]' if axheight > 2.5 else 'Converter\ncapacity [GW]')
        dfconverter.plot(
            ax=ax, column='GW', cmap=cmap,
            legend=True, 
            legend_kwds={
                'shrink':0.6, 'pad':0, 'orientation':'vertical',
                'label':cbar_label},
            vmin=0, vmax=(convertermax if convertermax else None),
            alpha=0.75,
        )
    ax.scatter(
        dfconverter.x.values, dfconverter.y.values,
        facecolor='none', edgecolor='k',
        s=((dfconverter.GW.values*wscale)**2 * 3.14 / 4),
        zorder=1E6,
    )

    ### Boundaries
    dfba.plot(ax=ax, edgecolor='0.5', facecolor='none', lw=0.1)
    dfstates.plot(ax=ax, edgecolor='0.25', facecolor='none', lw=0.2)

    ### Lines
    for i in dfplot.index:
        row = dfplot.loc[i]
        ax.plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color='C3', lw=wscale*row['GW'], solid_capstyle='butt',
            alpha=alpha,
        )
    if title:
        ax.annotate('{} ({})'.format(os.path.basename(case), year),
                    (0.1,1), xycoords='axes fraction', fontsize=10)

    ### Scale
    if scale:
        ax.plot(
            -1.75e6 + np.array([-1609/2*miles,1609/2*miles]),
            [-1.0e6, -1.0e6],
            color='C3', lw=wscale*10, solid_capstyle='butt'
        )
        ax.annotate(
            '10 GW\n{} miles'.format(miles), (-1.75e6, -1.1e6),
            ha='center', va='top', weight='bold', fontsize='x-large')

    ax.axis('off')

    return f,ax


def plot_transmission_utilization(
        case, year=2050, plottype='mean',
        wscale=0.0004, alpha=1.0, cmap=plt.cm.gist_earth_r,
    ):
    """
    """
    ### Get the output data
    dftrans = {
        'tran_flow_power': pd.read_csv(
            os.path.join(case,'outputs','tran_flow_power.csv'),
            header=0, names=['r','rr','h','trtype','t','MW'],),
        'tran_out':pd.read_csv(
            os.path.join(case,'outputs','tran_out.csv'),
            header=0, names=['r','rr','trtype','t','MW'],),
    }
    ### Combine all transmission types
    for data in ['tran_flow_power','tran_out']:
        dftrans[data].trtype = 'all'
        dftrans[data] = (
            dftrans[data]
            .loc[dftrans[data].t==year]
            .groupby([c for c in dftrans[data] if c not in ['MW','fraction']], as_index=False)
            .sum()
            .drop('t', axis=1)
        )
    ### Get utilization by timeslice
    utilization = dftrans['tran_flow_power'].merge(
        dftrans['tran_out'], on=['r','rr','trtype'], suffixes=('_flow','_cap'),
        how='outer'
    ).fillna(0)
    utilization['fraction'] = utilization.MW_flow.abs() / utilization.MW_cap
    ### Get annual fractional utilization
    ## First try the hourly version; if it doesn't exist load the h17 version
    try:
        hours = pd.read_csv(
            os.path.join(case,'inputs_case','hours_hourly.csv'),
            header=0, names=['h','hours'], index_col='h', squeeze=True)
    except FileNotFoundError:
        hours = pd.read_csv(
            os.path.join(case,'inputs_case','numhours.csv'),
            header=None, names=['h','hours'], index_col='h', squeeze=True)
    utilization['MWh'] = utilization.apply(
        lambda row: hours[row.h] * abs(row.MW_flow),
        axis=1
    )
    utilization_annual = (
        utilization.groupby(['r','rr','trtype']).MWh.sum()
        .divide(dftrans['tran_out'].set_index(['r','rr','trtype']).MW)
        .fillna(0).rename('fraction')
        / 8760
    ).reset_index()

    #%%### Plot max utilization
    dfplots = {
        'max': utilization.groupby(['r','rr','trtype'], as_index=False).fraction.max(),
        'mean': utilization_annual,
    }
    dfplot = dfplots[plottype.lower()]
    ### Load geographic data
    dfba = get_zonemap(case)
    dfstates = dfba.dissolve('st')
    ### Plot it
    dfplot = dfplot.merge(dftrans['tran_out'], on=['r','rr','trtype'], how='left')
    dfplot['r_x'] = dfplot.r.map(dfba.x)
    dfplot['r_y'] = dfplot.r.map(dfba.y)
    dfplot['rr_x'] = dfplot.rr.map(dfba.x)
    dfplot['rr_y'] = dfplot.rr.map(dfba.y)
    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(14,8))
    dfba.plot(ax=ax, edgecolor='0.5', facecolor='none', lw=0.1)
    dfstates.plot(ax=ax, edgecolor='0.25', facecolor='none', lw=0.2)
    for i, row in dfplot.iterrows():
        ax.plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=cmap(row.fraction), alpha=alpha,
            lw=wscale*row['MW'], solid_capstyle='butt',
        )
    plots.addcolorbarhist(
        f=f, ax0=ax, data=dfplot.fraction.values,
        title=f'{plottype.title()} utilization [fraction]', cmap=cmap,
        vmin=0., vmax=1.,
        orientation='horizontal', labelpad=2.25, histratio=1.,
        cbarwidth=0.025, cbarheight=0.25,
        cbarbottom=0.15, cbarhoffset=-0.8,
    )
    ax.annotate(
        '{} ({})'.format(os.path.basename(case), year),
        (0.1,1), xycoords='axes fraction', fontsize=10)
    ax.axis('off')
    return f,ax


def plot_vresites_transmission(
        case, year=2050, crs='ESRI:102008',
        routes=True, wscale=1.5, show_overlap=False,
        subtract_baseyear=None,
        alpha=0.25, colors='k', ms=1.15,
        techs=['upv','wind-ons','wind-ofs'],
        cm={'wind-ons':plt.cm.Blues, 'upv':plt.cm.Reds, 'wind-ofs':plt.cm.Purples},
        zorder={'wind-ons':-20002,'upv':-20001,'wind-ofs':-20000},
        cbarhoffset={'wind-ons':-0.8, 'upv':0.0, 'wind-ofs':0.8},
        label={'wind-ons':'Land-based wind [GW]',
               'upv':'Photovoltaics [GW]',
               'wind-ofs':'Offshore wind [GW]'},
        vmax={'upv':4.303, 'wind-ons':0.4, 'wind-ofs':0.6},
        trans_scale=True,
        show_transmission=True,
        title=True,
    ):
    """
    """
    ### Get the BA map
    dfba = get_zonemap(case)
    ### Aggregate to states
    dfstates = dfba.dissolve('st')
    ### Get the lakes
    try:
        lakes = gpd.read_file(
            os.path.join(reedspath,'inputs','shapefiles','greatlakes.gpkg')).to_crs(crs)
    except FileNotFoundError as err:
        print(err)
    
    ### Get the reeds_to_rev.py outputs
    cap = {}
    for tech in techs:
        try:
            cap[tech] = pd.read_csv(
                os.path.join(case,'outputs','df_sc_out_{}_reduced.csv'.format(tech))
            ).rename(columns={'built_capacity':'capacity_MW'})
            cap[tech]['geometry'] = cap[tech].apply(
                lambda row: shapely.geometry.Point(row.longitude, row.latitude),
                axis=1)
            cap[tech] = gpd.GeoDataFrame(cap[tech]).set_crs('EPSG:4326').to_crs(crs)

        except FileNotFoundError as err:
            print(err)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(8,8), dpi=600)
    dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=0.1, zorder=100000)
    dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.25, zorder=100001)
    try:
        lakes.plot(ax=ax, edgecolor='#2CA8E7', facecolor='#D3EFFA', lw=0.2, zorder=-1)
    except NameError:
        pass
    for tech in cap:
        legend_kwds = {
            'shrink':0.5, 'pad':0.05,
            'label':label[tech],
            'orientation':'horizontal',
        }
        dfplot = cap[tech].loc[cap[tech].year==year].sort_values('capacity_MW')
        dfplot['GW'] = dfplot['capacity_MW'] / 1000

        dfplot.plot(
            ax=ax, column='GW', cmap=cm[tech],
            marker='s', markersize=ms, lw=0,
            legend=False, legend_kwds=legend_kwds,
            vmin=0, vmax=vmax[tech], zorder=zorder[tech],
        )

        plots.addcolorbarhist(
            f=f, ax0=ax, data=dfplot.GW.values, title=legend_kwds['label'], cmap=cm[tech],
            vmin=0., vmax=vmax[tech],
            orientation='horizontal', labelpad=2.25, cbarbottom=-0.01, histratio=1.,
            cbarwidth=0.025, cbarheight=0.25, cbarhoffset=cbarhoffset[tech],
        )

    ### Transmission
    if show_transmission:
        plot_trans_onecase(
            case=case, pcalabel=False, wscale=wscale,
            yearlabel=False, year=year,
            alpha=alpha, colors=colors,
            f=f, ax=ax,
            title=False, scale=False,
            routes=routes, tolerance=1000,
            subtract_baseyear=subtract_baseyear,
            show_overlap=show_overlap,
            crs=crs, show_converters=0,
        )
    ### Transmission scale
    if show_transmission and trans_scale:
        ymin = ax.get_ylim()[0]
        xmin = ax.get_xlim()[0]
        if routes or (not show_overlap):
            gpd.GeoSeries(
                shapely.geometry.LineString([(xmin*0.8,ymin*0.6),(xmin*0.6,ymin*0.6)])
            ).buffer(wscale*10e3).plot(
                ax=ax, color=(colors if isinstance(colors,str) else 'k'), alpha=alpha)
        else:
            ax.plot(
                [xmin*0.8,xmin*0.6], [ymin*0.6, ymin*0.6],
                color=(colors if isinstance(colors,str) else 'k'),
                lw=wscale*10e3, solid_capstyle='butt', alpha=alpha,
            )
        ax.annotate(
            'Transmission\n10 GW', (xmin*0.7, ymin*0.66),
            ha='center', va='top', weight='bold', fontsize='large')

    ### Formatting
    if title:
        ax.annotate(
            '{} ({})'.format(os.path.basename(case), year),
            (0.1,1), xycoords='axes fraction', fontsize=10)
    ax.axis('off')

    return f,ax


def plot_prmtrade(
        case, year=2050,
        cm=plt.cm.inferno_r, wscale=7, alpha=0.8,
        crs='ESRI:102008',
        f=None, ax=None, dpi=150,
    ):
    """
    """
    ### Get the BA map
    dfba = get_zonemap(os.path.join(case))
    ### Aggregate to states
    dfstates = dfba.dissolve('st')
    endpoints = (
        gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','transmission_endpoints'))
        .set_index('ba_str'))
    endpoints['x'] = endpoints.centroid.x
    endpoints['y'] = endpoints.centroid.y
    dfba['x'] = dfba.index.map(endpoints.x)
    dfba['y'] = dfba.index.map(endpoints.y)

    ### Load results, aggregate over transmission types
    dfplot = pd.read_csv(
        os.path.join(case,'outputs','captrade.csv'),
        header=0, names=['r','rr','trtype','szn','t','MW']
    )
    dfplot = dfplot.loc[dfplot.t==year].groupby(['szn','r','rr'], as_index=False).MW.sum()
    dfplot['primary_direction'] = 1

    ### Get scaling and layout
    maxflow = dfplot.MW.abs().max()
    szns = dfplot.szn.sort_values().unique()
    nicelabels = {'wint':'Winter','spri':'Spring','summ':'Summer','fall':'Fall'}
    if 'summ' in szns:
        szns = ['wint','spri','summ','fall']
    ncols = 2
    nrows = int(np.ceil(len(szns) / ncols))
    coords = dict(zip(szns, [(row,col) for row in range(nrows) for col in range(ncols)]))
    
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(4*ncols,3*nrows), dpi=dpi,
        gridspec_kw={'wspace':0.0,'hspace':-0.05})
    for szn in szns:
        ### Background
        dfba.plot(ax=ax[coords[szn]], edgecolor='0.5', facecolor='none', lw=0.1)
        dfstates.plot(ax=ax[coords[szn]], edgecolor='k', facecolor='none', lw=0.2)

        ### Average prmtrade
        dfszn = dfplot.loc[dfplot.szn==szn].copy()
        for i, row in dfszn.iterrows():
            lineflow, primary_direction = row[['MW','primary_direction']]
            if lineflow >= 0:
                startx, starty = dfba.loc[row.r,'x'], dfba.loc[row.r,'y']
                delx = (dfba.loc[row.rr,'x'] - dfba.loc[row.r,'x'])
                dely = (dfba.loc[row.rr,'y'] - dfba.loc[row.r,'y'])
            else:
                startx, starty = dfba.loc[row.rr,'x'], dfba.loc[row.rr,'y']
                delx = (dfba.loc[row.r,'x'] - dfba.loc[row.rr,'x'])
                dely = (dfba.loc[row.r,'y'] - dfba.loc[row.rr,'y'])
            arrow = mpl.patches.FancyArrow(
                startx, starty, delx, dely,
                width=abs(lineflow)*wscale,
                length_includes_head=True,
                head_width=abs(lineflow)*wscale*2.,
                head_length=abs(lineflow)*wscale*1.0,
                lw=0, color=cm(abs(lineflow)/maxflow), alpha=alpha,
                ## Plot the primary direction on bottom since it's thicker
                zorder=(1e6 if primary_direction else 2e6),
            )
            ax[coords[szn]].add_patch(arrow)
        ax[coords[szn]].axis('off')
        ax[coords[szn]].set_title(nicelabels.get(szn,szn), y=0.9, fontsize='large')

    return f, ax


def plot_average_flow(
        case, year=2050,
        cm=plt.cm.inferno_r, wscale=7, alpha=0.8,
        trtypes=['AC','LCC','VSC'],
        simpletypes={'AC_init':'AC','LCC_init':'LCC','B2B_init':'LCC','B2B':'LCC'},
        crs='ESRI:102008',
        f=None, ax=None,
        both_directions=True, debug=False,
    ):
    """
    NOTE: Currently using max flow as max value but should instead
         plot as CF compared to line capacity (for both_directions = True and False).
    """
    ### Get the BA map
    dfba = get_zonemap(os.path.join(case))
    ### Aggregate to states
    dfstates = dfba.dissolve('st')
    endpoints = (
        gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','transmission_endpoints'))
        .set_index('ba_str'))
    endpoints['x'] = endpoints.centroid.x
    endpoints['y'] = endpoints.centroid.y
    dfba['x'] = dfba.index.map(endpoints.x)
    dfba['y'] = dfba.index.map(endpoints.y)

    ### Load results
    if both_directions:
        tran_out = pd.read_csv(
            os.path.join(case,'outputs','tran_out.csv'),
            header=0, names=['r','rr','trtype','t','MW'],
            index_col=['r','rr','trtype','t'],
        )
        hours = pd.read_csv(
            os.path.join(case,'inputs_case','numhours.csv'),
            header=None, names=['h','hours'], index_col='h', squeeze=True,
        )
        tran_flow_power = pd.read_csv(
            os.path.join(case,'outputs','tran_flow_power.csv'),
            header=0, names=['r','rr','h','trtype','t','MW']
        )
        ## Convert to MWh for sum
        tran_flow_power['hours'] = tran_flow_power.h.map(hours)
        tran_flow_power['MWh'] = tran_flow_power.MW * tran_flow_power.hours
        ## Separate flow by positive and negative timeslices
        dfplot = {}
        dfplot['pos'] = (
            tran_flow_power.loc[tran_flow_power.MWh >= 0]
            .groupby(['r','rr','trtype','t'], as_index=False).sum())
        dfplot['neg'] = (
            tran_flow_power.loc[tran_flow_power.MWh < 0]
            .groupby(['r','rr','trtype','t'], as_index=False).sum())
        dfplot = pd.concat(dfplot, axis=0, names=['direction','index'])
        ## Convert back to MW using hours in year
        ## NOTE: Assuming 8760 hours per year; need to adjust if that changes
        dfplot = (
            dfplot.groupby(['direction','r','rr','trtype','t']).MWh.sum()
            # / dfplot.groupby(['direction','r','rr','trtype','t']).hours.sum()
            / 8760
        ).rename('MW').reset_index()
        groupcols = ['direction','r','rr']
        
    else:
        dfplot = pd.read_csv(
            os.path.join(case,'outputs','tran_flow_power_ann.csv'),
            header=0, names=['r','rr','trtype','t','MW']
        )
        groupcols = ['r','rr']

    ### Downselect
    dfplot.trtype = dfplot.trtype.replace(simpletypes)
    dfplot = (
        dfplot
        .loc[dfplot.trtype.isin(trtypes) & (dfplot.t==year)]
        .groupby(groupcols, as_index=False).MW.sum()
    )

    ### Get the primary direction
    if both_directions:
        primary_direction = []
        df = dfplot.set_index(['direction','r','rr']).MW
        for (direction,r,rr), val in df.iteritems():
            other_direction = 'pos' if direction == 'neg' else 'neg'
            try:
                if abs(val) > abs(df.loc[other_direction,r,rr]):
                    primary_direction.append(1)
                else:
                    primary_direction.append(0)
            ### If the other direction doesn't exist, the current direction is primary
            except KeyError:
                primary_direction.append(1)

        dfplot['primary_direction'] = primary_direction
    else:
        dfplot['primary_direction'] = 1

    ### Get scaling
    maxflow = dfplot.MW.abs().max()

    ### Transmission capacity
    if (not f) or (not ax):
        plt.close()
        f,ax = plt.subplots(figsize=(12,8), dpi=150)

    dfba.plot(ax=ax, edgecolor='0.5', facecolor='none', lw=0.2)
    dfstates.plot(ax=ax, edgecolor='k', facecolor='none', lw=0.5)

    ### Average power flow
    for i, row in dfplot.iterrows():
        lineflow, primary_direction = row[['MW','primary_direction']]
        if lineflow >= 0:
            startx, starty = dfba.loc[row.r,'x'], dfba.loc[row.r,'y']
            delx = (dfba.loc[row.rr,'x'] - dfba.loc[row.r,'x'])
            dely = (dfba.loc[row.rr,'y'] - dfba.loc[row.r,'y'])
        else:
            startx, starty = dfba.loc[row.rr,'x'], dfba.loc[row.rr,'y']
            delx = (dfba.loc[row.r,'x'] - dfba.loc[row.rr,'x'])
            dely = (dfba.loc[row.r,'y'] - dfba.loc[row.rr,'y'])
        arrow = mpl.patches.FancyArrow(
            startx, starty, delx, dely,
            width=abs(lineflow)*wscale,
            length_includes_head=True,
            head_width=abs(lineflow)*wscale*2.,
            head_length=abs(lineflow)*wscale*1.0,
            lw=0, color=cm(abs(lineflow)/maxflow), alpha=alpha,
            ## Plot the primary direction on bottom since it's thicker
            zorder=(1e6 if primary_direction else 2e6),
        )
        ax.add_patch(arrow)

    ax.annotate(
        f'{os.path.basename(case)} {year} ({",".join(trtypes)})',
        (0.1,1.0), xycoords='axes fraction', ha='left', va='top')
    ax.axis('off')

    if debug:
        return f, ax, dfplot
    else:
        return f, ax

###### Operations animation
def animate_dispatch(
        case, year=2050, chunklength=4, nodeloc='centroid',
        width=1e5, height=0.5e4, tscale=0.5, figpath=None,
        overwrite=False,
    ):
    """
    # Notes
    * The animation is created with ffmpeg (https://ffmpeg.org/).
      If you're on a mac and have brew, you can install it with `brew install ffmpeg`.
    # Inputs
    nodeloc: ['centroid','endpoint']
    width: bar width in meters
    height: bar height in [meters/GW]
    tscale: transmission linewidth in [points/GW]
    """
    from tqdm import tqdm
    import subprocess

    ###### Define tech aggregations and colors
    aggtechs = {
        **{f'battery_{i}': 'battery' for i in [2,4,6,8,10]},
        **{f'wind-ons_{i}': 'wind-ons' for i in range(1,11)},
        **{f'wind-ofs_{i}': 'wind-ofs' for i in range(1,11)},
        **{f'upv_{i}': 'pv' for i in range(1,11)},
        **{'distpv':'pv','lfill-gas':'biopower','Nuclear':'nuclear','pumped-hydro':'pumped-hydro'},
        **{'hydND':'hydro','hydUD':'hydro','hydUND':'hydro',
           'hydNPND':'hydro','hydED':'hydro','hydEND':'hydro'},
        **{'RE-CT':'h2','Gas-CT_RE-CT':'h2','Gas-CC_RE-CC':'h2'},
    }
    techs = [
        'nuclear','hydro','biopower','h2',
        'wind-ons','wind-ofs','pv',
        'battery','pumped-hydro',
        ]
    try:
        bokehcolors = pd.read_csv(
            os.path.join(reedspath,'bokehpivot','in','reeds2','tech_style.csv'),
            index_col='order', squeeze=True)
    except FileNotFoundError:
        bokehcolors = pd.read_csv(
            os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
            index_col='order', squeeze=True)
    plotcolors = {
        'nuclear': bokehcolors['nuclear'],
        'hydro': bokehcolors['hydro'],
        'biopower': bokehcolors['biopower'],
        'h2': bokehcolors['h2-ct'],
        'wind-ons': bokehcolors['wind-ons'],
        'wind-ofs': bokehcolors['wind-ofs'],
        'pv': bokehcolors['upv'],
        'battery': bokehcolors['battery_4'],
        'pumped-hydro': bokehcolors['pumped-hydro'],
    }

    ###### Make the figure path
    framepath = os.path.join(figpath,'animation')
    os.makedirs(framepath, exist_ok=True)

    ###### Create the index
    fulltimeindex = pd.date_range(
        '2012-01-01', '2013-01-01',
        closed='left', freq='h', tz='Etc/GMT+5',
    )[:8760]
    if chunklength == 4:
        timeindex = fulltimeindex[2::chunklength]
    elif chunklength == 3:
        timeindex = fulltimeindex[1::chunklength] + pd.Timedelta('30min')
    elif chunklength == 2:
        timeindex = fulltimeindex[1::chunklength]
    else:
        timeindex = fulltimeindex

    ###### Load the data
    ##### Map
    dfba = get_zonemap(os.path.join(case))
    dfba['centroid_x'] = dfba.centroid.x
    dfba['centroid_y'] = dfba.centroid.y
    rs = dfba.index.values

    ##### Generation
    gen = pd.read_csv(
        os.path.join(case,'outputs','gen_h.csv'),
        header=0, names=['i','r','h','t','GW']
    )
    gen = gen.loc[gen.t==year].copy()
    gen.GW /= 1000
    gen.i = gen.i.map(lambda x: aggtechs.get(x,x))
    gen = gen.groupby(['h','r','i']).GW.sum()

    ##### Demand
    demand = pd.read_csv(
        os.path.join(case,'inputs_case','load_all_hourly.csv'),
        index_col=['h','r']
    )[str(year)] / 1000

    ##### Transmission capacity
    transcap = pd.read_csv(
        os.path.join(case,'outputs','tran_out.csv'),
        header=0, names=['r','rr','trtype','t','GW']
    )
    transcap = transcap.loc[transcap.t==year].copy()
    transcap.GW /= 1000
    transcap = transcap.groupby(['r','rr']).GW.sum()

    ##### Transmission flow
    flow = pd.read_csv(
        os.path.join(case,'outputs','tran_flow_power.csv'),
        header=0, names=['r','rr','h','trtype','t','GW']
    )
    flow = flow.loc[flow.t==year].copy()
    flow.GW /= 1000
    flow = flow.groupby(['h','r','rr']).GW.sum()

    ###### Define the plotting function
    def plotframe(h, overwrite=overwrite):
        """
        """
        savename = os.path.join(framepath,f"h{int(h.strip('h')):0>4}.png")
        if (not overwrite) and os.path.exists(savename):
            return None
        ###### Inputs
        tpre = 'centroid_' if nodeloc == 'centroid' else ''
        
        ###### Plot it
        ### Background map
        # https://stackoverflow.com/questions/
        # 28757348/how-to-clear-memory-completely-of-all-matplotlib-plots
        f,ax = plt.subplots(num=1, clear=True, figsize=(10,7))
        dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.5)
        ax.axis('off')

        ### Get limits (for plot placement)
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        ###### Transmission
        for ((r,rr),GW) in transcap.iteritems():
            ### Capacity
            ax.plot(
                [dfba.loc[r,tpre+'x'], dfba.loc[rr,tpre+'x']],
                [dfba.loc[r,tpre+'y'], dfba.loc[rr,tpre+'y']],
                lw=GW*tscale, solid_capstyle='butt', c='0.9',#c=plt.cm.tab20(5),#c='0.8',
                zorder=-10000,
            )
            ### Flow
            if (h,r,rr) in flow:
                GW = flow[h,r,rr]
            elif (h,rr,r) in flow:
                GW = -flow[h,rr,r]
            else:
                continue

            tail = (dfba.loc[r,tpre+'x'], dfba.loc[r,tpre+'y'])
            head = (dfba.loc[rr,tpre+'x'], dfba.loc[rr,tpre+'y'])
            pol = ('pos' if GW >= 0 else 'neg')
            ax.annotate(
                '', color='k',
                xy=(head if pol=='pos' else tail),
                xytext=(tail if pol=='pos' else head),
                arrowprops={
                    'width':abs(GW)*tscale, 'headwidth':abs(GW)*tscale,
                    'facecolor':'k', 'lw':0, 'edgecolor':'none',
                },
                zorder=-9000,
            )

        ###### Generation stacks
        for r in rs:
            try:
                df = gen[h][r].to_frame().T
            except KeyError:
                continue
            if df.empty:
                continue
            ### Get coordinates
            x0, bottom = dfba.loc[r,['centroid_x','centroid_y']]
            ### Scale it
            df = (df * height)
            df.index = [x0]
            ### Plot it
            plots.stackbar(
                df=df, ax=ax, colors=plotcolors, width=width, net=False,
                bottom=bottom,
            )
            ### Zero line
            ax.plot(
                [x0-width/2,x0+width/2], [bottom]*2,
                c='k',solid_capstyle='butt',lw=0.8,ls='--')
            ### Demand
            ax.bar(
                x=[x0], bottom=[bottom], height=demand[h,r]*height, width=width,
                color='k', alpha=0.2, zorder=10000,
            )
            ax.plot(
                [x0-width/2,x0+width/2], [bottom+demand[h,r]*height]*2,
                c='k',solid_capstyle='butt',lw=0.8,ls='-')

        ###### Label
        ax.annotate(
            timeindex[int(h.strip('h'))-1].strftime('%Y-%m-%d\n%H:%M:00 EST'),
            (-2e6, -1.2e6), ha='left', va='bottom', fontsize=12,
        )
        ax.set_xlim(xmin,xmax)
        ax.set_ylim(ymin,ymax)
        ###### Save it
        plt.savefig(savename)

    ###### Run it
    hs = [f'h{h+1}' for h in range(len(timeindex))]
    for h in tqdm(hs):
        plotframe(h)

    ###### Combine the frames into an animation
    command = (
        "ffmpeg "
        "-framerate {fps} "
        "-pattern_type glob "
        "-i {figpath}{sep}animation{sep}h*.png "
        "-c:v libx264 "
        "-pix_fmt yuv420p "
        "-vf crop=trunc(iw/2)*2:trunc(ih/2)*2 "
        "{figpath}{sep}animation.mp4"
    ).format(
        fps=24//chunklength, sep=os.sep, figpath=figpath,
    )
    subprocess.call(command.split())


def map_trans_agg(
        case, year=2050, agglevel='transreg', f=None, ax=None, dpi=None,
        wscale=0.2e4, width_inter=3e5, width_intra_frac=0.5,
        drawstates=0., drawzones=0., scale_loc=(2.5,-1.5), scale_val=100,
        drawgrid=False,
    ):
    """
    # Notes
    * Currently only works for agglevel='transreg'; to use other agglevels, add the
      coordinates for the interface boundaries to
      postprocessing/plots/transmission-interface-coords.csv
    
    # TO CONSIDER
    * Would be neat to build a stacked bar chart where the length of each sub-bar is the
      length of the line it's associated with, and the width would be the GW. Sort by length
      so you get something like a population distribution.
    """
    ### Plot settings
    width_intra = width_inter * width_intra_frac

    ###### Get case inputs and outputs
    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()

    tran_out = pd.read_csv(
        os.path.join(case,'outputs','tran_out.csv'),
        header=0, names=['r','rr','trtype','t','GW']
    )
    tran_out.GW /= 1000

    ### Map transmission capacity to agglevel
    tran_out['aggreg1'] = tran_out.r.map(hierarchy[agglevel])
    tran_out['aggreg2'] = tran_out.rr.map(hierarchy[agglevel])
    tran_out_agg = tran_out.copy()
    ## Sort aggreg's alphabetically
    for i, row in tran_out_agg.iterrows():
        if row.aggreg2 < row.aggreg1:
            tran_out_agg.loc[i,'aggreg1'], tran_out_agg.loc[i,'aggreg2'] = (
                tran_out_agg.loc[i,'aggreg2'], tran_out_agg.loc[i,'aggreg1'])
    tran_out_agg = tran_out_agg.groupby(
        ['aggreg1','aggreg2','trtype','t'], as_index=False).GW.sum()

    ### Get region map
    dfba = get_zonemap(case)
    dfstates = dfba.dissolve('st')
    dfba[agglevel] = dfba.index.map(hierarchy[agglevel])
    dfreg = dfba.copy()
    dfreg['geometry'] = dfreg.buffer(0.)
    dfreg = dfreg.dissolve(agglevel)
    dfreg['x'] = dfreg.centroid.x
    dfreg['y'] = dfreg.centroid.y

    ### Get transmission colors
    trtypes = pd.read_csv(
        os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
        index_col='raw')['display']
    transcolors = pd.read_csv(
            os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
            index_col='order')['color']
    transcolors = transcolors.append(trtypes.map(transcolors))

    rename = ['AC_init','B2B_init','LCC_init','AC','LCC','VSC']
    for c in rename:
        if c.lower() in transcolors:
            transcolors[c] = transcolors[c.lower()]

    ###### Get line drawing settings
    dfcorridors = pd.read_csv(
        os.path.join(reedspath,'postprocessing','plots','transmission-interface-coords.csv'),
        index_col=['level','region1','region2'],
    ).drop('drop',axis=1).loc[agglevel].reset_index()
    dfcorridors[['x','y']] *= 1e6
    ### Add reverse direction
    dfcorridors = pd.concat([
        dfcorridors,
        dfcorridors.assign(region1=dfcorridors.region2).assign(region2=dfcorridors.region1)
    ], axis=0).set_index(['region1','region2'])

    dfcorridors = dfcorridors.loc[~dfcorridors.index.duplicated()].copy()

    ### Aggregated
    dfplot = tran_out_agg.loc[tran_out_agg.t==year].pivot(
        index=['aggreg1','aggreg2'],columns='trtype',values='GW'
    ).reindex(['B2B','AC','LCC','VSC'],axis=1)

    ###### Plot it
    if (f == None) and (ax == None):
        plt.close()
        f,ax = plt.subplots(figsize=(12,8),dpi=dpi)
    ### Plot background
    dfreg.plot(ax=ax, facecolor='none', edgecolor='k', lw=1.)
    if drawstates:
        dfstates.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawstates)
    if drawzones:
        dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawzones)

    ### Transmission
    for i, row in dfplot.iterrows():
        r, rr = i
        x, y, _ = dfcorridors.loc[r, rr].T.squeeze()
        y -= row.sum() * wscale / 2
        plots.stackbar(
            df=row.rename(x).to_frame().T*wscale,
            ax=ax, colors=transcolors, width=(width_intra if r==rr else width_inter),
            net=False, bottom=y)

    ### Scale
    if scale_loc:
        ### Get the total intra- and inter-zone capacity in GW
        dfscale = dfplot.reset_index()
        dfintra = (
            dfscale.loc[dfscale.aggreg1 == dfscale.aggreg2]
            .drop(['aggreg1','aggreg2'],axis=1).sum())
        dfinter = (
            dfscale.loc[dfscale.aggreg1 != dfscale.aggreg2]
            .drop(['aggreg1','aggreg2'],axis=1).sum())
        ### Get the bar locations
        gap = 0.06e6
        xintra = scale_loc[0]*1e6 + (width_inter * width_intra_frac)/2 + gap/2
        xinter = scale_loc[0]*1e6 - width_inter/2 - gap/2
        y0 = scale_loc[1]*1e6
        ### Plot and annotate them
        plots.stackbar(
            dfintra.rename(xintra).to_frame().T*wscale,
            ax=ax, colors=transcolors, width=width_intra, net=False, bottom=y0,
        )
        ax.annotate(
            'Intra', (xintra,y0-0.01e6), weight='bold', ha='center', va='top',
            fontsize='large', annotation_clip=False)
        plots.stackbar(
            dfinter.rename(xinter).to_frame().T*wscale,
            ax=ax, colors=transcolors, width=width_inter, net=False, bottom=y0,
        )
        ax.annotate(
            'Inter', (xinter,y0-0.01e6), weight='bold', ha='center', va='top',
            fontsize='large', annotation_clip=False)
        ### Add scale
        xscale = xinter - width_inter/2 - gap
        plots.stackbar(
            pd.DataFrame({'scale':scale_val*wscale}, index=[xscale]),
            ax=ax, colors={'scale':'k'}, width=width_intra/10, net=False, bottom=y0,
        )
        ax.annotate(
            f'{scale_val} GW', (xscale-gap/2,y0+scale_val*wscale/2), weight='bold',
            ha='right', va='center', fontsize='large', annotation_clip=False)

    ax.axis('off')
    ### Grid
    if drawgrid:
        ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5e6))
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.grid(which='major', ls=':', lw=0.75)
        ax.grid(which='minor', ls=':', lw=0.25)
        ax.axis('on')

    return f, ax

def map_agg(
        case, data='cap', startyear=2020, agglevel='transreg',
        f=None, ax=None, dpi=None,
        wscale='auto', width_total=4e5, width_step=5,
        drawstates=0., drawzones=0., scale_loc=(2.3,-1.55), scale_val=1000,
        drawgrid=False,
    ):
    """
    # Inputs
    * data: 'cap' or 'gen'
    # Notes
    * Currently only works for agglevel='transreg'; to use other agglevels, add the
      coordinates for the interface boundaries to
      postprocessing/plots/transmission-interface-coords.csv
    """
    ### Get inputs
    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()

    s2r = pd.read_csv(
        os.path.join(case,'inputs_case','rsmap.csv'),
        index_col='rs', squeeze=True
    ).to_dict()

    ### Get colors and simpler tech names
    capcolors = pd.read_csv(
        os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order', squeeze=True)
    capmap = pd.read_csv(
        os.path.join(reedspath,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'),
        index_col='raw', squeeze=True)

    ### Get outputs
    if data in ['cap','Cap','capacity',None,'GW','']:
        val = pd.read_csv(
            os.path.join(case,'outputs','cap.csv'),
            header=0, names=['i','r','t','Value']
        )
        val.r = val.r.map(lambda x: s2r.get(x,x))
        ### Convert capacity to GW
        val.Value /= 1000
        val.i = val.i.str.lower()
        val = val.loc[val.t >= startyear].copy()
        units = 'GW'
    elif data in ['gen','Gen','generation','TWh']:
        val = pd.read_csv(
            os.path.join(case,'outputs','gen_ann.csv'),
            header=0, names=['i','r','t','Value']
        )
        val.r = val.r.map(lambda x: s2r.get(x,x))
        ### Convert generation to TWh
        val.Value /= 1e6
        val.i = val.i.str.lower()
        val = val.loc[val.t >= startyear].copy()
        units = 'TWh'

    ### Map capacity to agglevel
    val['aggreg'] = val.r.map(hierarchy[agglevel])
    val_agg = val.copy()
    val_agg.i = val_agg.i.map(capmap)
    val_agg = val_agg.groupby(['i','aggreg','t'], as_index=False).Value.sum()

    ### Get region map
    dfba = get_zonemap(case)
    dfstates = dfba.dissolve('st')
    dfba[agglevel] = dfba.index.map(hierarchy[agglevel])
    dfreg = dfba.copy()
    dfreg['geometry'] = dfreg.buffer(0.)
    dfreg = dfreg.dissolve(agglevel)
    dfreg['x'] = dfreg.centroid.x
    dfreg['y'] = dfreg.centroid.y

    ###### Get coordinates of region centers
    dfcenter = pd.read_csv(
        os.path.join(reedspath,'postprocessing','plots','transmission-interface-coords.csv'),
        index_col=['level','region1','region2'],
    ).drop('drop',axis=1).loc[agglevel].reset_index()
    dfcenter[['x','y']] *= 1e6
    dfcenter = (
        dfcenter
        .loc[~dfcenter.index.duplicated()]
        .loc[dfcenter.region1 == dfcenter.region2]
        .rename(columns={'region1':'aggreg'})
        .drop(['region2','angle'], axis=1)
        .set_index('aggreg')
    )

    ### Aggregated
    dfplot = val_agg.pivot(
        index=['aggreg','t'],columns='i',values='Value'
    ).reindex(capcolors.index, axis=1).dropna(axis=1, how='all')

    ### Plot settings
    width_year = width_total / len(val.t.unique())
    yearspan = val.t.max() - startyear
    if wscale in ['auto','scale','default',None,'','max']:
        capmax = dfplot.groupby('t').sum().sum(axis=1).max()
        _wscale = 3e6 / capmax * 0.95
    else:
        _wscale = wscale

    ###### Plot it
    if (f == None) and (ax == None):
        plt.close()
        f,ax = plt.subplots(figsize=(12,8),dpi=dpi)
    ### Plot background
    dfreg.plot(ax=ax, facecolor='none', edgecolor='k', lw=1.)
    if drawstates:
        dfstates.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawstates)
    if drawzones:
        dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawzones)

    ### Capacity
    for aggreg, (x,y) in dfcenter.iterrows():
        df = dfplot.loc[aggreg] * _wscale
        df.index = (df.index - startyear - yearspan/2) * width_year / width_step
        y -= df.sum(axis=1).max() / 2
        plots.stackbar(
            df=df,
            ax=ax, colors=capcolors, width=width_year, net=False,
            bottom=y, x0=x,
        )

    ### Scale
    if scale_loc:
        ### Get the total value
        dfscale = dfplot.groupby('t').sum() * _wscale
        dfscale.index = (dfscale.index - startyear - yearspan/2) * width_year / width_step
        ### Get the bar locations
        gap = 3e4
        x0 = scale_loc[0]*1e6
        y0 = scale_loc[1]*1e6
        ### Plot and annotate them
        plots.stackbar(
            df=dfscale,
            ax=ax, colors=capcolors, width=width_year, net=False,
            bottom=y0, x0=x0,
        )
        ax.annotate(
            'Total', (x0,y0-0.02e6), weight='bold', ha='center', va='top',
            fontsize='large', annotation_clip=False)
        ### Add scale
        xscale = x0 - width_total/2 - width_year/2
        plots.stackbar(
            pd.DataFrame({'scale':scale_val*_wscale}, index=[xscale]),
            ax=ax, colors={'scale':'k'}, width=width_year/4, net=False, bottom=y0,
        )
        ax.annotate(
            f'{scale_val} {units}', (xscale-gap,y0+scale_val*_wscale/2), weight='bold',
            ha='right', va='center', fontsize='large', annotation_clip=False)

    ax.axis('off')
    ### Grid
    if drawgrid:
        ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5e6))
        ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1e6))
        ax.grid(which='major', ls=':', lw=0.75)
        ax.grid(which='minor', ls=':', lw=0.25)
        ax.axis('on')

    return f, ax

def map_hybrid_pv_wind(
        case, val='site_cap', year=2050,
        tech=None, vmax=None,
        markersize=10.75, #stretch=1.2,
        cmap=plt.cm.gist_earth_r,
        f=None, ax=None, figsize=(6,6), dpi=None,
    ):
    """
    # Inputs
    cmap: Suggestions:
        val=site_cap, tech=wind-ons: plt.cm.Blues
        val=site_cap, tech=upv: plt.cm.Oranges
        val=(site_hybridization,site_spurcap), tech=None: plt.cm.gist_earth_r
        val=(site_pv_fraction,site_gir), tech=either: plt.cm.turbo
            or mpl.colors.LinearSegmentedColormap.from_list
                'turboclip', [plt.cm.turbo(c) for c in np.linspace(0.1,0.91,101)])
    """
    ###### Format inputs
    val2col = {
        'site_cap':'MW',
        'site_pv_fraction':'pv_fraction',
        'site_hybridization':'hybridization',
        'site_spurcap':'MW',
        'site_gir':'GIR',
    }
    column = val2col[val]
    label = {
        ('site_cap','upv'): f'{year} PV capacity [MW]',
        ('site_cap','wind-ons'): f'{year} wind capacity [MW]',
        ('site_pv_fraction',None): f'{year} PV fraction [.]',
        ('site_hybridization',None): f'{year} hybridization [.]',
        ('site_spurcap',None): f'{year} spur line capacity [MW]',
        ('site_gir','upv'): f'{year} PV gen:int ratio (GIR) [.]',
        ('site_gir','wind-ons'): f'{year} wind gen:int ratio (GIR) [.]',
    }[val, tech]
    ###### Load the data
    ### Model results
    dictin_hybrid = dict(
        site_cap=pd.read_csv(
            os.path.join(case,'outputs','site_cap.csv'),
            header=0, names=['i','x','t','MW']),
        site_pv_fraction=pd.read_csv(
            os.path.join(case,'outputs','site_pv_fraction.csv'),
            header=0, names=['x','t','pv_fraction']),
        site_hybridization=pd.read_csv(
            os.path.join(case,'outputs','site_hybridization.csv'),
            header=0, names=['x','t','hybridization']),
        site_spurcap=pd.read_csv(
            os.path.join(case,'outputs','site_spurcap.csv'),
            header=0, names=['x','t','MW']),
        site_gir=pd.read_csv(
            os.path.join(case,'outputs','site_gir.csv'),
            header=0, names=['i','x','t','GIR']),
    )

    ### Other shared inputs
    sitemap = pd.read_csv(
        os.path.join(reedspath,'inputs','supplycurvedata','sitemap.csv'),
        index_col='sc_point_gid'
    )
    sitemap.index = 'i' + sitemap.index.astype(str)

    rfeas = pd.read_csv(
        os.path.join(case,'inputs_case','valid_ba_list.csv'),
        header=None, squeeze=True,
    ).values.tolist()

    dfba = get_zonemap(case).loc[rfeas]

    ### Make the combined output dataframe
    df = dictin_hybrid[val].loc[dictin_hybrid[val].t==year].copy()
    df['longitude'] = df.x.map(sitemap.longitude)
    df['latitude'] = df.x.map(sitemap.latitude)
    # df['rb'] = df.x.map(sitemap.rb)
    # df['transreg'] = df.rb.map(hierarchy.transreg)
    ### Check for nulls
    if df.longitude.isnull().sum():
        df.dropna(subset=['longitude'], inplace=True)
    ### Geodataframify it
    dfplot = plots.df2gdf(df)
    ### Filter to single tech
    if tech:
        dfplot = dfplot.loc[dfplot.i.str.startswith(tech)].copy()

    if vmax in ['max','none',None]:
        zmax = dfplot[column].max()
    else:
        zmax = vmax

    ###### Plot it
    if (not f) and (not ax):
        plt.close()
        f,ax = plt.subplots(figsize=figsize, dpi=dpi)
    dfplot.plot(
        ax=ax, column=column, cmap=cmap, marker='s', lw=0, markersize=markersize,
        legend=False, vmin=0, vmax=zmax,
    )
    # xmin, xmax = ax.get_xlim()
    # ymin, ymax = ax.get_ylim()
    # xspan = xmax - xmin
    # yspan = ymax - ymin

    dfba.plot(ax=ax, facecolor='0.9', edgecolor='none', zorder=-1e6)
    dfba.plot(ax=ax, facecolor='none', edgecolor='w', lw=0.3, zorder=1e6)

    plots.addcolorbarhist(
        f=f, ax0=ax, data=dfplot[column].values,
        title=label, cmap=cmap,
        vmin=0., vmax=zmax,
        orientation='horizontal', labelpad=2.5, cbarbottom=-0.06,
        cbarheight=0.5, log=False, #title_fontsize=12,
        nbins=51, histratio=2,
        extend=('max' if tech == 'upv' else 'neither'),
        ticklabel_fontsize=10, title_fontsize=13,
    )

    # ax.set_xlim(xmin-xspan*(stretch-1), xmax+xspan*(stretch-1))
    # ax.set_ylim(ymin-yspan*(stretch-1), ymax+yspan*(stretch-1))
    ax.axis('off')
    return f, ax
