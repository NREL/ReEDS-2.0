### Imports
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from glob import glob
import os
import sys
import site
from tqdm import tqdm
import openpyxl
import geopandas as gpd
import shapely
import h5py
os.environ['PROJ_NETWORK'] = 'OFF'

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
remotepath = '/Volumes/ReEDS/' if sys.platform == 'darwin' else r'//nrelnas01/ReEDS/'

### Format plots and load other convenience functions
site.addsitedir(os.path.join(reeds_path,'postprocessing'))
import plots
plots.plotparams()
site.addsitedir(os.path.join(reeds_path,'input_processing'))
from hourly_writetimeseries import h2timestamp, timestamp2h
site.addsitedir(os.path.join(reeds_path,'ReEDS_Augur'))
import functions


### Functions
def get_zonemap(case):
    """
    Get geodataframe of model zones, applying aggregation if necessary
    """
    ### Check if resolution is at county level
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'),
        header=None, index_col=0).squeeze(1)
    if 'GSw_RegionResolution' not in sw:
        sw['GSw_RegionResolution'] = 'ba'

    if sw.GSw_RegionResolution != 'county':
        ###### Load original shapefiles
        ### Model zones
        dfba_in = (
            gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','US_PCA'))
            .set_index('rb')
        )
        ### Transmission endpoints
        endpoints = (
            gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','transmission_endpoints'))
            .set_index('ba_str')
        )
        ### Keep transmission endpoints in model zones dataframe
        endpoints['x'] = endpoints.centroid.x
        endpoints['y'] = endpoints.centroid.y
        dfba_in['x'] = dfba_in.index.map(endpoints.x)
        dfba_in['y'] = dfba_in.index.map(endpoints.y)
        dfba_in['labelx'] = dfba_in.geometry.centroid.x
        dfba_in['labely'] = dfba_in.geometry.centroid.y
        dfba_in.st = dfba_in.st.str.upper()

        dfba = dfba_in.copy()

        ###### Apply aggregation if necessary
        if 'GSw_AggregateRegions' not in sw:
            hierarchy = pd.read_csv(
                os.path.join(case,'inputs_case','hierarchy.csv')
            ).rename(columns={'*r':'r'}).set_index('r')
            for col in hierarchy:
                dfba[col] = dfba.index.map(hierarchy[col])
            return dfba

        if int(sw['GSw_AggregateRegions']):
            ### Load original hierarchy file
            hierarchy = pd.read_csv(
                os.path.join(
                    reeds_path,'inputs','hierarchy{}.csv'.format(
                        '' if (sw['GSw_HierarchyFile'] == 'default')
                        else '_'+sw['GSw_HierarchyFile'])),
                index_col='*r'
            )
            ### Load mapping from aggreg's to anchor regions
            aggreg2anchorreg = pd.read_csv(
                os.path.join(case, 'inputs_case', 'aggreg2anchorreg.csv'),
                index_col='aggreg').squeeze(1)
            ### Map original model regions to aggregs
            r2aggreg = hierarchy.aggreg.copy()
            dfba['aggreg'] = dfba.index.map(r2aggreg)
            dfba = dfba.dissolve('aggreg')
            ### Get the endpoints from the anchor regions
            dfba['x'] = dfba.index.map(aggreg2anchorreg).map(endpoints.x)
            dfba['y'] = dfba.index.map(aggreg2anchorreg).map(endpoints.y)

    else:
        ### Get the county map
        crs = 'ESRI:102008'
        dfcnty = gpd.read_file(
            os.path.join(reeds_path,'inputs','shapefiles','US_COUNTY_2022')
        ).to_crs(crs)

        ### format FIPS name
        #dfcnty['r'] = 'p' + dfcnty['STATEFP'] + dfcnty['COUNTYFP']

        ### Add US state code and drop states outside of CONUS
        state_fips = pd.read_csv(
            os.path.join(reeds_path,'inputs','shapefiles', "state_fips_codes.csv"), 
            names=["STATE", "STCODE", "STATEFP", "CONUS"],
            dtype={"STATEFP":"string"}, header=0)
        state_fips = state_fips.loc[state_fips['CONUS'], :]
        dfcnty = dfcnty.merge(state_fips, on="STATEFP")
        dfcnty = dfcnty[['rb', 'NAMELSAD', 'STATE_x', 'geometry']].set_index('rb')

        # add in centroids for later use in tx mapping
        dfcnty['x'] = dfcnty.geometry.centroid.x
        dfcnty['y'] = dfcnty.geometry.centroid.y

        dfcnty.rename(columns={'NAMELSAD':'county','STATE_x':'st'}, inplace=True)

        dfba = dfcnty

    return dfba


def get_dfmap(case):
    dfba = get_zonemap(case)
    dfmap = {}
    for col in ['interconnect','nercr','transreg','transgrp','st','country']:
        dfmap[col] = dfba.copy()
        dfmap[col]['geometry'] = dfmap[col].buffer(0.)
        dfmap[col] = dfmap[col].dissolve(col)
        dfmap[col]['labelx'] = dfmap[col].centroid.x
        dfmap[col]['labely'] = dfmap[col].centroid.y

    return dfmap


def simplify_techs(techs, condense_upgrades=True):
    """
    Notes
    -----
    * Always changes all entries to lower case
    """
    ### Load the map
    tech_map = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')).str.lower()
    tech_map = tech_map.drop_duplicates().set_index('raw').display.str.lower()

    ### Get the unique techs
    _techs = pd.Series(techs).str.lower()
    techs_unique = pd.Series(_techs).unique()

    direct_map = {}
    for i in techs_unique:
        out = i
        ### First try to map each tech to the direct match
        for raw, display in tech_map.items():
            if i == raw:
                out = display
                break
        ### Now redo it for any tech that wasn't matched
        if out not in tech_map.values:
            for raw, display in tech_map.items():
                if i.startswith(raw):
                    out = display
                    break
        ### Other cleanup
        if condense_upgrades:
            if out.endswith('_upgrade'):
                out = out[:-len('_upgrade')]
        direct_map[i] = out

    ### Get the new list of techs
    techs_renamed = _techs.map(lambda x: direct_map.get(x,x))
    return techs_renamed


def get_report_sheetmap(case):
    """
    Create a dictionary of report.xlsx fields to excel sheet names
    """
    excel = openpyxl.load_workbook(
        os.path.join(case,'outputs','reeds-report/report.xlsx'),
        read_only=True, keep_links=False)
    sheets = excel.sheetnames
    val2sheet = dict(zip([sheet.split('_', maxsplit=1)[-1] for sheet in sheets], sheets))
    return val2sheet


def read_pras_results(filepath):
    """Read a run_pras.jl output file"""
    with h5py.File(filepath, 'r') as f:
        keys = list(f)
        df = pd.concat({c: pd.Series(f[c][...]) for c in keys}, axis=1)
        return df


def plotdiff(
        val, casebase, casecomp, onlytechs=None, titleshorten=0,
        yearmin=None, yearmax=2050, colors=None,
        **plot_kwds,
    ):
    """
    """
    ### Shared inputs
    ycol = {
        'Generation (TWh)': 'Generation (TWh)',
        'Capacity (GW)': 'Capacity (GW)',
        'New Annual Capacity (GW)': 'Capacity (GW)',
        'Annual Retirements (GW)': 'Capacity (GW)',
        'Final Gen by timeslice (GW)': 'Generation (GW)',
        'Firm Capacity (GW)': 'Firm Capacity (GW)',
        'Curtailment Rate': 'Curt Rate',
        'Transmission (GW-mi)': 'Amount (GW-mi)',
        'Transmission (PRM) (GW-mi)': 'Trans cap, PRM (GW-mi)',
        'Bulk System Electricity Pric': '$',
        'National Average Electricity': 'Average cost ($/MWh)',
        '2022-2050 Present Value of S': 'Discounted Cost (Bil $)',
        'Present Value of System Cost': 'Discounted Cost (Bil $)',
        'Runtime (hours)': 'processtime',
        'Runtime by year (hours)': 'processtime',
        'NEUE (ppm)': 'neue',
    }
    xcol = {
        'Generation (TWh)': 'year',
        'Capacity (GW)': 'year',
        'New Annual Capacity (GW)': 'year',
        'Annual Retirements (GW)': 'year',
        'Final Gen by timeslice (GW)': 'timeslice',
        'Firm Capacity (GW)': 'year',
        'Curtailment Rate': 'year',
        'Transmission (GW-mi)': 'year',
        'Transmission (PRM) (GW-mi)': 'year',
        'Bulk System Electricity Pric': 'year',
        'National Average Electricity': 'year',
        '2022-2050 Present Value of S': 'dummy',
        'Present Value of System Cost': 'dummy',
        'Runtime (hours)': 'dummy',
        'Runtime by year (hours)': 'year',
        'NEUE (ppm)': 'year',
    }
    width = {
        'Generation (TWh)': 2.9,
        'Capacity (GW)': 2.9,
        'New Annual Capacity (GW)': 2.9,
        'Annual Retirements (GW)': 2.9,
        'Final Gen by timeslice (GW)': 0.9,
        'Firm Capacity (GW)': 2.9,
        'Curtailment Rate': 2.9,
        'Transmission (GW-mi)': 2.9,
        'Transmission (PRM) (GW-mi)': 2.9,
        'Bulk System Electricity Pric': 2.9,
        'National Average Electricity': 0.9,
        '2022-2050 Present Value of S': 20,
        'Present Value of System Cost': 20,
        'Runtime (hours)': 20,
        'Runtime by year (hours)': 2.9,
        'NEUE (ppm)': 2.9,
    }
    colorcol = {
        'Generation (TWh)': 'tech',
        'Capacity (GW)': 'tech',
        'New Annual Capacity (GW)': 'tech',
        'Annual Retirements (GW)': 'tech',
        'Final Gen by timeslice (GW)': 'tech',
        'Firm Capacity (GW)': 'tech',
        'Curtailment Rate': 'dummy',
        'Transmission (GW-mi)': 'type',
        'Transmission (PRM) (GW-mi)': 'type',
        'Bulk System Electricity Pric': 'type',
        'National Average Electricity': 'cost_cat',
        '2022-2050 Present Value of S': 'cost_cat',
        'Present Value of System Cost': 'cost_cat',
        'Runtime (hours)': 'process',
        'Runtime by year (hours)': 'process',
        'NEUE (ppm)': 'dummy',
    }
    fixcol = {
        'Generation (TWh)': {},
        'Capacity (GW)': {},
        'New Annual Capacity (GW)': {},
        'Annual Retirements (GW)': {},
        'Final Gen by timeslice (GW)': {},
        'Firm Capacity (GW)': {'season':0},
        'Curtailment Rate': {},
        'Transmission (GW-mi)': {},
        'Transmission (PRM) (GW-mi)': {},
        'Bulk System Electricity Pric': {},
        'National Average Electricity': {},
        '2022-2050 Present Value of S': {},
        'Present Value of System Cost': {},
        'Runtime (hours)': {},
        'Runtime by year (hours)': {},
        'NEUE (ppm)': {},
    }
    tfix = {
        'Bulk System Electricity Pric': '16_Bulk System Electricity Price ($/MWh)',
        '$': 'Price ($/MWh)',
        '2022-2050 Present Value of S': '25_2022-2050 Present Value of System Cost (Bil $)',
        'Present Value of System Cost': '25_Present Value of System Cost through 2050 (Bil $)',
    }
    ylabel = {
        'Generation (TWh)': 'Generation [TWh]',
        'Capacity (GW)': 'Capacity [GW]',
        'New Annual Capacity (GW)': 'Capacity [GW]',
        'Annual Retirements (GW)': 'Capacity [GW]',
        'Final Gen by timeslice (GW)': 'Generation [GW]',
        'Firm Capacity (GW)': 'Firm Capacity [GW]',
        'Curtailment Rate': 'Curtailment [%]',
        'Transmission (GW-mi)': 'Transmission capacity [TW-mi]',
        'Transmission (PRM) (GW-mi)': 'Transmission capacity [TW-mi]',
        'Bulk System Electricity Pric': 'Marginal cost [$/MWh]',
        'National Average Electricity': 'Average cost [$/MWh]',
        '2022-2050 Present Value of S': '[$Billion]',
        'Present Value of System Cost': '[$Billion]',
        'Runtime (hours)': 'Runtime [hours]',
        'Runtime by year (hours)': 'Runtime [hours]',
        'NEUE (ppm)': 'NEUE [ppm]',
    }
    scaler = {
        'Generation (TWh)': 1,
        'Capacity (GW)': 1,
        'New Annual Capacity (GW)': 1,
        'Annual Retirements (GW)': 1,
        'Final Gen by timeslice (GW)': 1,
        'Firm Capacity (GW)': 1,
        'Curtailment Rate': 100,
        'Transmission (GW-mi)': 0.001,
        'Transmission (PRM) (GW-mi)': 0.001,
        'Bulk System Electricity Pric': 1,
        'National Average Electricity': 1,
        '2022-2050 Present Value of S': 1,
        'Present Value of System Cost': 1,
        'Runtime (hours)': 1,
        'Runtime by year (hours)': 1,
        'NEUE (ppm)': 1,
    }

    colors_time = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','process_style.csv'),
        index_col='order',
    ).squeeze(1).to_dict()
    colors_tech = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order')['color']
    colors_cost = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','cost_cat_style.csv'),
        index_col='order')['color']
    colors_trans = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
        index_col='order')['color']
    colors_tech = {
        **colors_tech,
        **{'ac':'C0','dc':'C1','vsc':'C3'},
        **{'load':'C0', 'nat_gen':'C1', 'nat_rps':'C1', 'oper_res':'C2', 
           'res_marg':'C3', 'state_rps':'C4',},
        **{'Capital':'C0','PTC':'C2','O&M':'C3','Fuel':'C4','Trans':'C1'},
        'dummy':'C0',
        **colors_trans,
        **colors_cost,
        **colors_time,
    }
    if colors:
        colors_tech = colors

    ### Parse the sheet name
    val2sheet = get_report_sheetmap(casebase)
    val = val.split('_')[-1]
    sheet = val2sheet[val]

    ### Load the data
    dfbase = pd.read_excel(
        os.path.join(casebase,'outputs','reeds-report/report.xlsx'),
        sheet_name=sheet, engine='openpyxl',
    ).rename(columns={'trtype':'type'})

    if colorcol[val] == 'dummy':
        dfbase['dummy'] = 'dummy'
    for col in fixcol[val]:
        if isinstance(fixcol[val][col], int):
            fixval = dfbase[col].unique()[fixcol[val][col]]
        else:
            fixval = fixcol[val][col]
        dfbase = dfbase.loc[dfbase[col] == fixval].copy()

    dfcomp = pd.read_excel(
        os.path.join(casecomp,'outputs','reeds-report/report.xlsx'),
        sheet_name=sheet, engine='openpyxl',
    ).rename(columns={'trtype':'type'})
    
    if colorcol[val] == 'dummy':
        dfcomp['dummy'] = 'dummy'
    if xcol[val] == 'dummy':
        dfbase['dummy'] = 0
        dfcomp['dummy'] = 0
    for col in fixcol[val]:
        if isinstance(fixcol[val][col], int):
            fixval = dfcomp[col].unique()[fixcol[val][col]]
        else:
            fixval = fixcol[val][col]
        dfcomp = dfcomp.loc[dfcomp[col] == fixval].copy()

    ### Apply the scaler
    dfbase[ycol[val]] *= scaler[val]
    dfcomp[ycol[val]] *= scaler[val]

    ### Only keep shared x-axis values
    shared_x = [i for i in dfbase[xcol[val]].unique() if i in dfcomp[xcol[val]].unique()]
    dfbase = dfbase.loc[dfbase[xcol[val]].isin(shared_x)].copy()
    dfcomp = dfcomp.loc[dfcomp[xcol[val]].isin(shared_x)].copy()

    ### Take the diff
    dfdiff = dfbase.drop(['scenario'],axis=1).merge(
        dfcomp.drop(['scenario'],axis=1), on=[colorcol[val],xcol[val]], how='outer',
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

    ### Only keep analyzed years
    if val == 'National Average Electricity':
        dfdiff = dfdiff.loc[dfdiff.year <= 2050].copy()
    ### Use yearmin if using a time axis
    if yearmin and (xcol[val]=='year'):
        dfdiff = dfdiff.loc[dfdiff.year >= yearmin].copy()
    ### Use yearmax if using a time axis
    if yearmax and (xcol[val]=='year'):
        dfdiff = dfdiff.loc[dfdiff.year <= yearmax].copy()
    indices = dfdiff[xcol[val]].unique()

    ###### Plot it
    plt.close()
    if not len(plot_kwds):
        plot_kwds = {'figsize':(13,4), 'gridspec_kw':{'wspace':0.25}}
    f,ax=plt.subplots(1, 4, sharex=True, **plot_kwds)

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
    printstring = (
        f'{val}, final year: base = {printbase:.2f};  comp = {printcomp:.2f};  '
        f'comp/base = {printcomp/printbase:.4f};  comp–base = {printcomp-printbase:.2f}'
    )
    print(printstring)

    ### Diff
    for col in [2,3]:
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
            ax[col].bar(
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
            ax[col].bar(
                x=[index]*len(bottom), bottom=bottom.values, height=-posheight.values,
                width=width[val], color=[colors_tech[i] for i in postechs], lw=0, 
            )
            ### Sum
            ax[col].plot(
                [index], [negheight.sum() + posheight.sum()], 
                marker='o', lw=0, markerfacecolor='w', markeredgecolor='k')
        ax[col].axhline(0,c='0.5',lw=0.75,ls=':')

    ### Legend
    handles = [
        mpl.patches.Patch(facecolor=colors_tech[i], edgecolor='none', label=i)
        for i in techs
    ]
    leg = ax[-1].legend(
        handles=handles[::-1], loc='center left', bbox_to_anchor=(1,0.5), 
        fontsize='large', ncol=len(techs)//15+1, 
        handletextpad=0.3, handlelength=0.7, columnspacing=0.5, 
    )

    ### Formatting
    # ax[0].set_ylabel(tfix.get(ycol[val],ycol[val]))
    ax[0].set_ylabel(ylabel.get(val, val))

    ## axes 0 and 1 use the same y limits
    ymax = max(ax[0].get_ylim()[1], ax[1].get_ylim()[1])
    ymin = max(ax[0].get_ylim()[0], ax[1].get_ylim()[0])
    for col in range(2):
        ax[col].set_ylim(ymin,ymax)
    ## axis 2 uses the same y limits as 0 and 1; axis 3 uses its own limits
    ax[2].set_ylim(-(ymin+ymax)/2, (ymin+ymax)/2)
    ax3ymin = min(ax[3].get_ylim()[0]*0.95, ax[3].get_ylim()[0]*1.05)
    ax3ymax = max(ax[3].get_ylim()[1]*0.95, ax[3].get_ylim()[1]*1.05)
    ax[3].set_ylim(ax3ymin, ax3ymax)
    # for col in [2,3]:
    #     ax[col].ticklabel_format(axis='y', style='plain')
    ## draw a line on axis 2 showing the axis 3 limits
    ax[0].set_xlim(*ax[0].get_xlim())
    xmax = ax[0].get_xlim()[1] - (ax[0].get_xlim()[1] - ax[0].get_xlim()[0]) * 0.01
    ax[2].plot([xmax]*2, [ax3ymin, ax3ymax], c='k', lw=1)

    if xcol[val] == 'year':
        ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
        ax[0].xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(5))
        if val == '19_National Average Electricity':
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
    for col in [2,3]:
        ax[col].set_title(
            '{}\n– {}'.format(
                os.path.basename(casecomp)[titleshorten:],
                os.path.basename(casebase)[titleshorten:]),
            x=0, ha='left', size='large', weight='bold')
    ax[0].annotate(
        (tfix.get(val,val) 
         + (', ' if len(fixcol[val]) > 0 else '')
         + ', '.join(['{} = {}'.format(col,fixcol[val][col]) for col in fixcol[val]])),
        xy=(0,1.15),xycoords='axes fraction',size='xx-large',weight='bold')
    ax[2].annotate('shared y axis', (0.02,0.02), xycoords='axes fraction')
    ax[3].annotate('zoomed y axis', (0.02,0.02), xycoords='axes fraction')

    plots.despine(ax)
    return f,ax,leg, dfdiff, printstring


def plot_trans_diff(
        casebase, casecomp,
        level='r',
        pcalabel=False, wscale=0.0003,
        year='last', yearlabel=True,
        colors={'+':'C3', '-':'C0',
                'AC':'C2', 'DC':'C1', 'LCC':'C1', 'VSC':'C3', 'B2B':'C4'},
        alpha=0.75, dpi=None, drawzones=True, drawstates=True,
        simpletypes=None, subtract_baseyear=None,
        trtypes=['AC','B2B','LCC','VSC'],
        f=None, ax=None, scale=True, label_line_capacity=True,
        titleshorten=0,
        thickborders='none', thickness=0.5,
    ):
    """Plot difference map of interzonal transmission"""
    ### Load shapefiles
    dfba = get_zonemap(casebase)
    dfstates = dfba.dissolve('st')
    hierarchy = pd.read_csv(
        os.path.join(casebase,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    for col in hierarchy:
        dfba[col] = dfba.index.map(hierarchy[col])
    hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()
    ## Aggregate zones if necessary
    dfzones = dfba.copy()
    if level not in ['r','rb']:
        dfzones.geometry = dfzones.buffer(0.)
        dfzones = dfzones.dissolve(level)
        dfzones['x'] = dfzones.centroid.x
        dfzones['y'] = dfzones.centroid.y
    ## Get thick borders if necessary
    if thickborders not in [None,'','none','None',False]:
        if thickborders in hierarchy:
            dfthick = dfba.copy()
            dfthick[thickborders] = hierarchy[thickborders]
            dfthick.geometry = dfthick.buffer(0.)
            dfthick = dfthick.dissolve(thickborders)
    
    cases = {'base': casebase, 'comp': casecomp}
    tran_out = {}
    for case in cases:
        tran_out[case] = (
            pd.read_csv(os.path.join(cases[case],'outputs','tran_out.csv'))
            .rename(columns={
                'Dim1':'r','Dim2':'rr','Dim3':'trtype','Dim4':'t','Val':'MW','Value':'MW',
            })
        )
        if simpletypes is None:
            dicttran = {
                i: tran_out[case].loc[tran_out[case].trtype==i].set_index(['r','rr','t']).MW
                for i in trtypes}
            tran_out[case] = pd.concat(dicttran, axis=0, names=['trtype','r','rr','t']).reset_index()

        if subtract_baseyear:
            tran_out[case] = (
                tran_out[case].pivot(index=['r','rr','trtype'], columns='t', values='MW')
                .subtract(
                    tran_out[case].pivot(index=['r','rr','trtype'], columns='t', values='MW')
                    [subtract_baseyear].fillna(0), axis=0)
            ).stack('t').rename('MW').reset_index()

    dfplot = tran_out['base'].merge(
        tran_out['comp'], on=['r','rr','t','trtype'], suffixes=('_base','_comp'), how='outer').fillna(0)
    dfplot = dfplot.loc[dfplot.t==(dfplot.t.max() if year=='last' else year)].copy()
    dfplot['MW_diff'] = dfplot['MW_comp'] - dfplot['MW_base']


    dfplot['r_x'] = dfplot.r.map(dfba.x)
    dfplot['r_y'] = dfplot.r.map(dfba.y)
    dfplot['rr_x'] = dfplot.rr.map(dfba.x)
    dfplot['rr_y'] = dfplot.rr.map(dfba.y)

    ## Make figure if necessary
    justdiff = True
    if (not f) and (not ax):
        justdiff = False
        plt.close()
        f,ax=plt.subplots(
            1,3,sharex=True,sharey=True,figsize=(14,8),
            gridspec_kw={'wspace':-0.05, 'hspace':0.05},
            dpi=dpi,
        )

    ###### Just difference
    if justdiff:
        ### Boundaries
        if drawzones:
            dfba.plot(ax=ax, edgecolor='0.5', facecolor='none', lw=0.1)
        if drawstates:
            dfstates.plot(ax=ax, edgecolor='0.25', facecolor='none', lw=0.2)
        if thickborders not in [None,'','none','None',False]:
            dfthick.plot(ax=ax, edgecolor='0.75', facecolor='none', lw=thickness)
        ax.axis('off')
        ### Diff
        for i, row in dfplot.iterrows():
            ax.plot(
                [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
                color=(colors['+'] if row['MW_diff'] >= 0 else colors['-']), 
                lw=abs(wscale*row['MW_diff']), solid_capstyle='butt', alpha=alpha,
            )
            if label_line_capacity and (abs(row.MW_diff/1000) >= label_line_capacity):
                _label_line(row=row, ax=ax, wscale=wscale, cap='MW_diff', sign=True)
        ### Stop here
        return dfplot

    ###### Absolute and difference
    for col in range(3):
        ### Boundaries
        dfba.plot(ax=ax[col], edgecolor='0.5', facecolor='none', lw=0.1)
        dfstates.plot(ax=ax[col], edgecolor='0.5', facecolor='none', lw=0.2)
        ax[col].axis('off')

    for i, row in dfplot.iterrows():
        ### Base
        ax[0].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=colors[row['trtype']], lw=wscale*row['MW_base'], solid_capstyle='butt',
            alpha=alpha,
        )
        if label_line_capacity and (row.MW_base/1000 >= label_line_capacity):
            _label_line(row=row, ax=ax[0], wscale=wscale, cap='MW_base')
        ### Comp
        ax[1].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=colors[row['trtype']], lw=wscale*row['MW_comp'], solid_capstyle='butt',
            alpha=alpha,
        )
        if label_line_capacity and (row.MW_comp/1000 >= label_line_capacity):
            _label_line(row=row, ax=ax[1], wscale=wscale, cap='MW_comp')
        ### Diff
        ax[2].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=(colors['+'] if row['MW_diff'] >= 0 else colors['-']), 
            lw=abs(wscale*row['MW_diff']), solid_capstyle='butt', alpha=alpha,
        )
        if label_line_capacity and (abs(row.MW_diff/1000) >= label_line_capacity):
            _label_line(row=row, ax=ax[2], wscale=wscale, cap='MW_diff', sign=True)

    ###### Labels
    if pcalabel:
        for col in range(3):
            for r in dfba.index:
                ax[col].annotate(
                    r.replace('p',''), dfba.loc[r,['x','y']].values,
                    ha='center', va='center', fontsize=5, color='0.7')
    if yearlabel:
        ax[0].annotate(
            'Year: {}'.format(year), 
            (0.9,0.97), xycoords='axes fraction', fontsize=10, ha='right', va='top')
    ax[0].annotate(
        os.path.basename(cases['base'])[titleshorten:],
        (0.1,1), xycoords='axes fraction', fontsize=10)
    ax[1].annotate(
        os.path.basename(cases['comp'])[titleshorten:],
        (0.1,1), xycoords='axes fraction', fontsize=10)
    ax[2].annotate(
        '{}\n– {}'.format(
            os.path.basename(cases['comp'])[titleshorten:],
            os.path.basename(cases['base'])[titleshorten:]),
        (0.1,1), xycoords='axes fraction', fontsize=10)

    ###### Scale
    if scale:
        ax[0].plot(
            [-2.0e6,-1.5e6], [-1.0e6, -1.0e6],
            color='k', lw=wscale*10e3, solid_capstyle='butt'
        )
        ax[0].annotate(
            '10 GW', (-1.75e6, -1.1e6), ha='center', va='top', weight='bold')
        if subtract_baseyear:
            ax[0].annotate(
                f'(new since {subtract_baseyear})', (-1.75e6, -1.3e6), ha='center', va='top')

    return f, ax


def _label_line(row, ax, wscale, label_line_color='k', cap='MW', sign=False):
    """
    * only works when line thicknesses are in points (not data units)
    """
    ### Get the angle
    angle = np.arctan((row.rr_y - row.r_y) / (row.rr_x - row.r_x)) * 180 / np.pi
    ## Keep it upright
    if (90 < angle < 270) or (-90 > angle > -270):
        angle *= -1
    ### Get the font size in points
    size = abs(row[cap]) * wscale
    ### Get the middle of the line
    xtext = (row.r_x + row.rr_x) / 2
    ytext = (row.r_y + row.rr_y) / 2

    ### Write it in GW
    ax.annotate(
        (f'{row[cap]/1000:+.0f}' if sign else f'{row[cap]/1000:.0f}'),
        (xtext, ytext), rotation=angle,
        size=size, color=label_line_color, ha='center', va='center',
    )


def plot_trans_onecase(
        case, dfin=None,
        level='r',
        pcalabel=False, wscale=0.0003,
        year='last', yearlabel=True,
        colors={'AC':'C2', 'LCC':'C1', 'VSC':'C3', 'B2B':'C4'},
        dpi=None,
        trtypes=['AC','B2B','LCC','VSC'],
        simpletypes={'AC_init':'AC','LCC_init':'LCC','B2B_init':'B2B'},
        zorders={'AC':1e3, 'VSC':3e3, 'LCC':4e3, 'B2B':7e3,},
        alpha=1, scalesize='x-large',
        f=None, ax=None, scale=True, title=True,
        routes=False, tolerance=1000,
        subtract_baseyear=None,
        show_overlap=True, drawzones=True, show_converters=0.5,
        crs='ESRI:102008',
        thickborders='none', thickness=0.5, drawstates=True,
        label_line_capacity=0, crossing_level='r',
    ):
    """
    Notes
    * If colors is a string instead of a dictionary, aggregate all transmission types
    """
    ### Load shapefiles
    dfba = get_zonemap(case)
    dfstates = dfba.dissolve('st')
    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    for col in hierarchy:
        dfba[col] = dfba.index.map(hierarchy[col])
    hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()
    ## Aggregate zones if necessary
    dfzones = dfba.copy()
    if level not in ['r','rb']:
        dfzones.geometry = dfzones.buffer(0.)
        dfzones = dfzones.dissolve(level)
        dfzones['x'] = dfzones.centroid.x
        dfzones['y'] = dfzones.centroid.y
    ## Get thick borders if necessary
    if thickborders not in [None,'','none','None',False]:
        if thickborders in hierarchy:
            dfthick = dfba.copy()
            dfthick[thickborders] = hierarchy[thickborders]
            dfthick.geometry = dfthick.buffer(0.)
            dfthick = dfthick.dissolve(thickborders)
    ## Get route linestrings if necessary
    if routes:
        try:
            transmission_routes = gpd.read_file(
                os.path.join(reeds_path,'inputs','shapefiles','transmission_routes-500kVac.gpkg')
            ).set_index(['r','rr']).to_crs(crs)
        except FileNotFoundError:
            print('New routes not found so reverting to old routes')
            transmission_routes = gpd.read_file(
                os.path.join(reeds_path,'inputs','shapefiles','transmission_routes')
            ).set_index(['from_ba','to_ba']).to_crs(crs)

        if tolerance:
            transmission_routes['geometry'] = transmission_routes.simplify(tolerance)

    ### Load run-specific output data
    if dfin is None:
        tran_out = pd.read_csv(
            os.path.join(case,'outputs','tran_out.csv'),
            header=0, names=['r','rr','trtype','t','MW'],
        )
        ## If necessary, subset to interregional lines
        if crossing_level != 'r':
            tran_out = tran_out.loc[
                tran_out.r.map(hierarchy[crossing_level])
                != tran_out.rr.map(hierarchy[crossing_level])
            ].copy()
        if simpletypes is None:
            dicttran = {
                i: tran_out.loc[tran_out.trtype==i].set_index(['r','rr','t']).MW
                for i in trtypes}
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

        if level not in ['r','rb']:
            for col in ['r','rr']:
                dfplot[col] = dfplot[col].map(hierarchy[level])
            ## Only keep one direction
            for i, row in dfplot.iterrows():
                dfplot.loc[i,['r','rr']] = sorted(dfplot.loc[i,['r','rr']])
            ## Drop lines within the same level
            dfplot = dfplot.loc[dfplot.r != dfplot.rr].copy()
            ## Aggregate
            dfplot = dfplot.groupby(['r','rr','trtype'], as_index=False).MW.sum()

    ### Otherwise take the correctly-formatted dataframe passed as an input
    else:
        dfplot = dfin.copy()

    ### Aggregate types if colors is a string instead of a dictionary
    if isinstance(colors, str):
        dfplot = dfplot.groupby(['r','rr','t'], as_index=False).MW.sum()

    dfplot['r_x'] = dfplot.r.map(dfzones.x)
    dfplot['r_y'] = dfplot.r.map(dfzones.y)
    dfplot['rr_x'] = dfplot.rr.map(dfzones.x)
    dfplot['rr_y'] = dfplot.rr.map(dfzones.y)

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
    if drawzones:
        dfzones.plot(ax=ax, edgecolor='0.5', facecolor='none', lw=0.1)
    if drawstates:
        dfstates.plot(ax=ax, edgecolor='0.25', facecolor='none', lw=0.2)
    if thickborders not in [None,'','none','None',False]:
        dfthick.plot(ax=ax, edgecolor='0.75', facecolor='none', lw=thickness)
    ax.axis('off')
    ### Labels
    if pcalabel:
        for r in dfzones.index:
            ax.annotate(
                r, dfzones.loc[r,['x','y']].values,
                ha='center', va='center', fontsize=5, color='C7', alpha=0.8,
                bbox={'facecolor':'w', 'edgecolor':'none', 'alpha':0.8, 'pad':0.5},
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
                if label_line_capacity and (row.MW/1000 >= label_line_capacity):
                    _label_line(row=row, ax=ax, wscale=wscale)
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
        ax.annotate(
            '{} ({}{})'.format(
                os.path.basename(case), year,
                f', additions since {subtract_baseyear}' if subtract_baseyear else ' total',
            ),
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


def plotdiffmaps(val, i_plot, year, casebase, casecomp, reeds_path, 
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
        'coaloldscr':'coal', 'coalolduns':'coal', 'coal-igcc':'coal', 'coal-new':'coal',
        'csp2':'csp','csp-ns':'csp',
        'gas-cc':'gas-cc', 'gas-ct':'gas-ct',
        'beccs_mod':'beccs',
        'can-imports':'canada',
        'undisc':'geothermal',
        'hyded':'hydro', 'hydend':'hydro', 'hydnd':'hydro', 
        'hydnpnd':'hydro', 'hydud':'hydro', 'hydund':'hydro',
        'geohydro_pbinary':'geothermal', 'geohydro_pflash':'geothermal', 'undisc_pflash':'geothermal',
        'egs_allkm':'geothermal', 'geohydro_allkm':'geothermal', 'egs_nearfield':'geothermal',
        'gas-cc-ccs_mod':'gas-cc-ccs', 'gas-cc_gas-cc-ccs_mod':'gas-cc-ccs',
        'coal-new_coal-ccs_mod':'coal-ccs', 'coaloldscr_coal-ccs_mod':'coal-ccs',
        'coalolduns_coal-ccs_mod':'coal-ccs', 'coal-igcc_coal-ccs_mod':'coal-ccs',
        're-ct':'h2-ct', 'h2-ct_upgrade':'h2-ct',
        're-cc':'h2-ct', 'h2-cc':'hc-ct', 'h2-cc_upgrade':'h2-ct',
        'gas-cc_re-cc':'h2-ct', 'gas-ct_re-ct':'h2-ct', 'gas-ct_h2-ct':'h2-ct', 
        ### Use if grouping onshore and offshore together
        # 'wind-ons':'wind', 'wind-ofs':'wind',
    }

    ### Get the maps
    if dfba is None:
        dfba = get_zonemap(casecomp)
    if dfstates is None:
        dfstates = dfba.dissolve('st')

    ### Load the data, sum over hours
    dfbase = pd.read_csv(
        os.path.join(casebase,'outputs',val+'.csv'),
        names=ycols[val], header=0,
    )
    dfcomp = pd.read_csv(
        os.path.join(casecomp,'outputs',val+'.csv'),
        names=ycols[val], header=0,
    )

    ### Drop the tails
    dfbase.i = dfbase.i.str.strip('_0123456789').str.lower()
    dfcomp.i = dfcomp.i.str.strip('_0123456789').str.lower()

    ### Simplify the i names
    dfbase.i = dfbase.i.map(lambda x: rep_i.get(x.lower(),x.lower()))
    dfcomp.i = dfcomp.i.map(lambda x: rep_i.get(x.lower(),x.lower()))

    dfbase = dfbase.groupby(['i','r','t']).sum().reset_index().copy()
    dfcomp = dfcomp.groupby(['i','r','t']).sum().reset_index().copy()
    # print(dfbase.i.unique())
    # print(dfcomp.i.unique())

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
            dfdiff.loc[(dfdiff.i.str.startswith(i_plot))&(dfdiff.t==year),valcol+'_base'].max(),
            dfdiff.loc[(dfdiff.i.str.startswith(i_plot))&(dfdiff.t==year),valcol+'_comp'].max(),
        )
    
    ###### Plot the base
    if plot == 'base':
        dfplot = dfba.merge(
            dfbase.loc[(dfbase.i.str.startswith(i_plot))&(dfbase.t==year),['r',valcol]],
            left_index=True, right_on='r', how='left'
        ).fillna(0).reset_index(drop=True)

        dfplot.plot(ax=ax, column=valcol, cmap=cmap, legend=True,
                    legend_kwds=legend_kwds, vmax=zmax)

    ###### Plot the comp
    elif plot == 'comp':
        dfplot = dfba.merge(
            dfcomp.loc[(dfcomp.i.str.startswith(i_plot))&(dfcomp.t==year),['r',valcol]],
            left_index=True, right_on='r', how='left'
        ).fillna(0).reset_index(drop=True)

        dfplot.plot(ax=ax, column=valcol, cmap=cmap, legend=True,
                    legend_kwds=legend_kwds, vmax=zmax)

    ###### Plot the pct diff
    elif plot in ['diff','pctdiff','pct_diff','diffpct','diff_pct','pct']:
        legend_kwds['label'] = '{} {} {}\n[% diff]'.format(valcol,i_plot,year)

        dfplot = dfba.merge(
            dfdiff.loc[(dfdiff.i.str.startswith(i_plot))&(dfdiff.t==year),['r',valcol+'_diff']],
            left_index=True, right_on='r', how='left'
        ).reset_index(drop=True)

        if zlim is None:
            zlim = max(
                abs(dfplot[valcol+'_pctdiff'].min()),
                abs(dfplot[valcol+'_pctdiff'].max()),
                0.1,
            )

        dfplot.plot(ax=ax, column=valcol+'_pctdiff', cmap=cmap, legend=True,
                    vmin=-zlim, vmax=+zlim, legend_kwds=legend_kwds)

    ###### Plot the absolute diff
    elif plot in ['absdiff', 'abs_diff', 'diffabs', 'diff_abs']:
        legend_kwds['label'] = '{}diff {} [{}]'.format(valcol,i_plot,units)

        dfplot = dfba.merge(
            dfdiff.loc[(dfdiff.i.str.startswith(i_plot))&(dfdiff.t==year),['r',valcol+'_diff']],
            left_index=True, right_on='r', how='left'
        ).reset_index(drop=True)

        if zlim is None:
            zlim = max(
                abs(dfplot[valcol+'_diff'].min()),
                abs(dfplot[valcol+'_diff'].max()),
                0.1,
            )

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
        os.path.join(case,'outputs','tran_out.csv'),
        header=0, names=['r','rr','trtype','t','MW'],
    )

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
        case, year=2050, plottype='mean', network='trans',
        wscale=0.0004, alpha=1.0, cmap=plt.cm.gist_earth_r,
        extent='modeled',
    ):
    """
    # Inputs
    extent: 'modeled' for modeled area, 'usa' for contiguous US
    """
    ### Get the output data
    if ('h2' in network.lower()) or ('hydrogen' in network.lower()):
        dftrans = {
            'trans_cap': pd.read_csv(os.path.join(case,'outputs','h2_trans_cap.csv')),
            'trans_flow_power': pd.read_csv(os.path.join(case,'outputs','h2_trans_flow.csv')),
        }
    else:
        dftrans = {
            'trans_cap': pd.read_csv(os.path.join(case,'outputs','tran_out.csv')),
            'trans_flow_power': pd.read_csv(os.path.join(case,'outputs','tran_flow_power.csv')),
        }
    val_r = pd.read_csv(
        os.path.join(case,'inputs_case','val_r.csv'), header=None,
    ).squeeze(1).values.tolist()
    ### Combine all transmission types
    for data in ['trans_flow_power','trans_cap']:
        dftrans[data]['trtype'] = 'all'
        dftrans[data] = (
            dftrans[data]
            .loc[dftrans[data].t==year]
            .groupby([c for c in dftrans[data] if c not in ['Value']], as_index=False)
            .sum()
            .drop('t', axis=1)
        ).rename(columns={'allh':'h','Value':'Val','MW':'Val'})
    ### Get utilization by timeslice
    utilization = dftrans['trans_flow_power'].merge(
        dftrans['trans_cap'], on=['r','rr','trtype'], suffixes=('_flow','_cap'),
        how='outer'
    ).fillna(0)
    utilization['fraction'] = utilization.Val_flow.abs() / utilization.Val_cap
    ### Get annual fractional utilization
    ## First try the hourly version; if it doesn't exist load the h17 version
    try:
        hours = pd.read_csv(
            os.path.join(case,'inputs_case','hours_hourly.csv'),
            header=0, names=['h','hours'], index_col='h').squeeze(1)
    except FileNotFoundError:
        hours = pd.read_csv(
            os.path.join(case,'inputs_case','numhours.csv'),
            header=0, names=['h','hours'], index_col='h').squeeze(1)
    utilization['Valh'] = utilization.apply(
        lambda row: hours[row.h] * abs(row.Val_flow),
        axis=1
    )
    utilization_annual = (
        utilization.groupby(['r','rr','trtype']).Valh.sum()
        .divide(dftrans['trans_cap'].set_index(['r','rr','trtype']).Val)
        .fillna(0).rename('fraction')
        / 8760
    ).reset_index()

    ###### Plot max utilization
    dfplots = {
        'max': utilization.groupby(['r','rr','trtype'], as_index=False).fraction.max(),
        'mean': utilization_annual,
    }
    dfplot = dfplots[plottype.lower()]
    ### Load geographic data
    dfba = get_zonemap(case)
    if extent.lower() not in ['usa','full','nation','us','country','all']:
        dfba = dfba.loc[val_r]
    dfstates = dfba.dissolve('st')
    ### Plot it
    dfplot = dfplot.merge(dftrans['trans_cap'], on=['r','rr','trtype'], how='left')
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
            lw=wscale*row['Val'], solid_capstyle='butt',
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
            os.path.join(reeds_path,'inputs','shapefiles','greatlakes.gpkg')).to_crs(crs)
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
    Plot PRM trading by ccseason (for capacity credit) or average flow during stress periods
    """
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'),
        header=None, index_col=0).squeeze(1)

    ### Load results, aggregate over transmission types
    if int(sw.get('GSw_PRM_CapCredit', 1)):
        dfplot = pd.read_csv(
            os.path.join(case,'outputs','captrade.csv'),
            header=0, names=['r','rr','trtype','ccseason','t','MW']
        )
        dfplot = dfplot.loc[dfplot.t==year].groupby(['ccseason','r','rr'], as_index=False).MW.sum()
    else:
        ### For stress periods take the average flow over each period
        dfplot = pd.read_csv(
            os.path.join(case,'outputs','tran_flow_stress.csv'),
            header=0, names=['r','rr','h','trtype','t','MW'],
        )
        dfplot['ccseason'] = (
            dfplot.h.str.split('h', expand=True)[0]
            ## Convert to timestamp
            .map(lambda x: h2timestamp(x+'h01').strftime('%Y-%m-%d'))
        )
        dfplot = (
            dfplot.loc[dfplot.t==year]
            ## Sum over trtypes
            .groupby(['r','rr','ccseason','h'], as_index=False).MW.sum()
            ## Average over h's in ccseason
            .groupby(['r','rr','ccseason'], as_index=False).MW.mean()
        )
    dfplot['primary_direction'] = 1

    ### Get the BA map
    dfba = get_zonemap(os.path.join(case))
    ## Downselect to modeled regions
    val_r = list(set(dfplot.r.unique().tolist() + dfplot.rr.unique().tolist()))
    dfba = dfba.loc[val_r].copy()
    ## Aggregate to states
    dfstates = dfba.dissolve('st')

    if sw.get('GSw_RegionResolution', 'ba') != 'county':
        endpoints = (
            gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','transmission_endpoints'))
            .set_index('ba_str'))
        endpoints['x'] = endpoints.centroid.x
        endpoints['y'] = endpoints.centroid.y
        dfba['x'] = dfba.index.map(endpoints.x)
        dfba['y'] = dfba.index.map(endpoints.y)

    ### Get scaling and layout
    maxflow = dfplot.MW.abs().max()
    if int(sw.get('GSw_PRM_CapCredit', 1)):
        ccseasons = pd.read_csv(
            os.path.join(reeds_path,'inputs','variability','h_dt_szn.csv')
        ).ccseason.unique()
    else:
        ccseasons = dfplot.ccseason.sort_values().unique()
    nrows, ncols, coords = plots.get_coordinates(ccseasons)
    
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(4*ncols,3*nrows), dpi=dpi,
        gridspec_kw={'wspace':0.0,'hspace':-0.05})
    for ccseason in ccseasons:
        ### Background
        dfba.plot(ax=ax[coords[ccseason]], edgecolor='0.5', facecolor='none', lw=0.1)
        dfstates.plot(ax=ax[coords[ccseason]], edgecolor='k', facecolor='none', lw=0.2)

        ### Average prmtrade
        dfszn = dfplot.loc[dfplot.ccseason==ccseason].copy()
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
                clip_on=False,
            )
            ax[coords[ccseason]].add_patch(arrow)
        ax[coords[ccseason]].axis('off')
        ax[coords[ccseason]].set_title(ccseason, y=0.9, fontsize='large')

    plots.trim_subplots(ax=ax, nrows=nrows, ncols=ncols, nsubplots=len(ccseasons))
    return f, ax


def plot_average_flow(
        case, year=2050, network='trans',
        cm=plt.cm.inferno_r, wscale=7, alpha=0.8,
        trtypes=['AC','LCC','VSC','H2'],
        simpletypes={'AC_init':'AC','LCC_init':'LCC','B2B_init':'LCC','B2B':'LCC'},
        crs='ESRI:102008', scale=True,
        f=None, ax=None, extent='modeled',
        both_directions=True, debug=False, title=False,
        drawzones=True, thickborders='none', thickness=0.5, drawstates=True,
    ):
    """
    NOTE: Currently using max flow as max value but should instead
         plot as CF compared to line capacity (for both_directions = True and False).
    """
    ### Parse some inputs
    if ('h2' in network.lower()) or ('hydrogen' in network.lower()):
        label = 'kT/day'
        labelscale = 24/1000
    else:
        label = 'GW'
        labelscale = 0.001
    ### Get the BA map
    dfba = get_zonemap(os.path.join(case))
    val_r = pd.read_csv(
        os.path.join(case,'inputs_case','val_r.csv'), header=None,
    ).squeeze(1).values.tolist()
    if extent.lower() not in ['usa','full','nation','us','country','all']:
        dfba = dfba.loc[val_r]
    ### Aggregate to states
    dfstates = dfba.dissolve('st')

    ### Check if resolution is at county level
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'),
        header=None, index_col=0).squeeze(1)
    if 'GSw_RegionResolution' not in sw:
        sw['GSw_RegionResolution'] = 'ba'

    if sw.GSw_RegionResolution == 'county':
        pass
    else:
        endpoints = (
            gpd.read_file(os.path.join(reeds_path,'inputs','shapefiles','transmission_endpoints'))
            .set_index('ba_str'))
        endpoints['x'] = endpoints.centroid.x
        endpoints['y'] = endpoints.centroid.y
        dfba['x'] = dfba.index.map(endpoints.x)
        dfba['y'] = dfba.index.map(endpoints.y)

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

    ### Load results
    hours = pd.read_csv(
        os.path.join(case,'inputs_case','numhours.csv'),
        header=0, names=['h','hours'], index_col='h',
    ).squeeze(1)
    if both_directions:
        if ('h2' in network.lower()) or ('hydrogen' in network.lower()):
            flow = pd.read_csv(
                os.path.join(case,'outputs','h2_trans_flow.csv')
            ).assign(trtype='H2').rename(columns={'allh':'h','Value':'Val'})
        else:
            flow = pd.read_csv(
                os.path.join(case,'outputs','tran_flow_power.csv'),
                header=0, names=['r','rr','h','trtype','t','Val'])
        ## Convert to plot units, then sum over hours
        flow.Val *= labelscale
        flow['hours'] = flow.h.map(hours)
        flow['Valh'] = flow.Val * flow.hours
        ## Separate flow by positive and negative timeslices
        dfplot = {}
        dfplot['pos'] = (
            flow.loc[flow.Valh >= 0]
            .groupby(['r','rr','trtype','t'], as_index=False).Valh.sum())
        dfplot['neg'] = (
            flow.loc[flow.Valh < 0]
            .groupby(['r','rr','trtype','t'], as_index=False).Valh.sum())
        dfplot = pd.concat(dfplot, axis=0, names=['direction','index'])
        ## Convert back to MW using hours in year
        dfplot = (
            dfplot.groupby(['direction','r','rr','trtype','t']).Valh.sum()
            / hours.sum()
        ).rename('Val').reset_index()
        groupcols = ['direction','r','rr']

    else:
        dfplot = pd.read_csv(
            os.path.join(case,'outputs','tran_flow_power_ann.csv'),
            header=0, names=['r','rr','trtype','t','Val']
        )
        groupcols = ['r','rr']

    ### Downselect
    dfplot.trtype = dfplot.trtype.replace(simpletypes)
    dfplot = (
        dfplot
        .loc[dfplot.trtype.isin(trtypes) & (dfplot.t==year)]
        .groupby(groupcols, as_index=False).Val.sum()
    )

    ### Get the primary direction
    if both_directions:
        primary_direction = []
        df = dfplot.set_index(['direction','r','rr']).Val
        for (direction,r,rr), val in df.items():
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
    maxflow = dfplot.Val.abs().max()

    ### Transmission capacity
    if (not f) or (not ax):
        plt.close()
        f,ax = plt.subplots(figsize=(12,8), dpi=150)

    if drawzones:
        dfba.plot(ax=ax, edgecolor='0.75', facecolor='none', lw=0.2)
    if drawstates:
        dfstates.plot(ax=ax, edgecolor='0.7', facecolor='none', lw=0.4)
    if thickborders not in [None,'','none','None',False]:
        dfthick.plot(ax=ax, edgecolor='C7', facecolor='none', lw=thickness)

    ### Average power flow
    for i, row in dfplot.iterrows():
        lineflow, primary_direction = row[['Val','primary_direction']]
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
            clip_on=False,
        )
        ax.add_patch(arrow)

    ### Scale
    if scale:
        (startx, starty, delx, dely) = (-2.0e6, -1.2e6, 0.5e6, 0e6)
        arrow = mpl.patches.FancyArrow(
            startx, starty, delx, dely,
            width=maxflow*wscale,
            length_includes_head=True,
            head_width=maxflow*wscale*2.,
            head_length=maxflow*wscale*1.0,
            lw=0, color=cm(maxflow/maxflow), alpha=alpha,
            clip_on=False,
        )
        ax.add_patch(arrow)
        ax.annotate(
            f'{maxflow:.0f} {label}',
            # (startx+delx/2, starty+dely/2), color='0.8', va='center',
            # (startx+delx/2, starty+dely/2+(maxflow*wscale/2)+0.08e6),
            (startx+delx+0.02e6, starty+dely/2), ha='left', va='center',
            color='k', fontsize=14,
            annotation_clip=False,
        )

    ### Formatting
    if title:
        ax.annotate(
            f'{os.path.basename(case)} {year} ({",".join(trtypes)})',
            (0.1,1.0), xycoords='axes fraction', ha='left', va='top')
    ax.axis('off')

    if debug:
        return f, ax, dfplot
    else:
        return f, ax


def get_transfer_peak_fraction(case, level='transreg', tstart=2020, everything=False):
    """Get ratio of interregional transfer capacity to peak demand by region level"""
    ### Implied inputs
    levell = level + level[-1]

    ### Shared inputs
    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')

    dfmap = get_dfmap(case)

    ## Plot regions from west to east
    regions = dfmap[level].bounds.minx.sort_values().index

    ### Run results
    dfin_trans_r = pd.read_csv(
        os.path.join(case,'outputs','tran_out.csv')
    ).rename(columns={'Value':'MW'})
    dfin_trans_r[f'inter_{level}'] = (
        dfin_trans_r.r.map(hierarchy[level])
        != dfin_trans_r.rr.map(hierarchy[level])
    ).astype(int)

    dftrans = dfin_trans_r.loc[
        (dfin_trans_r.t >= tstart)
        & (dfin_trans_r[f'inter_{level}'] == 1)
    ].copy()
    dftrans[level] = dftrans.r.map(hierarchy[level])
    dftrans[levell] = dftrans.rr.map(hierarchy[level])

    ### Get import/export capacity
    transfercap = {}
    for region in regions:
        transfercap[region] = (
            dftrans.loc[
                (dftrans[level]==region) | (dftrans[levell]==region)
            ].groupby('t').MW.sum())
    transfercap = pd.concat(transfercap, axis=1)

    ### Get peak load from hourly demand
    try:
        dfpeak = pd.read_csv(
            os.path.join(case,'inputs_case','peakload.csv'), index_col=['level','region']
        ).loc[level].T
        dfpeak.index = dfpeak.index.astype(int)
    except FileNotFoundError:
        dfdemand = pd.read_hdf(os.path.join(case, 'inputs_case','load.h5'))
        ## Aggregate to level
        dfdemand = dfdemand.rename(columns=hierarchy[level]).groupby(axis=1, level=0).sum()
        ## Calculate peak
        dfpeak = dfdemand.groupby(axis=0, level='year').max()
    ### Get the fraction
    dfout = (transfercap / dfpeak.loc[tstart:])[regions]

    if everything:
        return {'fraction':dfout, 'transfercap':transfercap, 'peak':dfpeak.loc[tstart:]}
    else:
        return dfout


def plot_interreg_transfer_cap_ratio(
        case, colors=None, casenames=None,
        level='transreg', tstart=2020,
        f=None, ax=None,
        grid=True, ymax=None,
    ):
    """Plot interregional transfer capability / peak demand over time"""
    ### Inputs for debugging
    # case = (
    #     '/Users/pbrown/github2/ReEDS-2.0/runs/'
    #     'v20240212_transopM0_WECC_CPNP_GP1_TFY2035_PTL2035_TRc_MITCg0p3')
    # casenames = 'base'
    # level = 'transreg'; tstart=2020;
    # f=None; ax=None; grid=True; ymax=3; colors=None

    ### Parse inputs
    cases = case.split(',') if isinstance(case, str) else case
    if casenames is None:
        casenames = dict(zip(cases, [os.path.basename(c) for c in cases]))
    elif isinstance(casenames, list):
        casenames = dict(zip(cases, casenames))
    elif isinstance(casenames, str):
        casenames = dict(zip(cases, casenames.split(',')))

    if colors is None:
        colors = plots.rainbowmapper(cases)
    elif isinstance(colors, list):
        colors = dict(zip(cases, colors))
    elif isinstance(colors, str):
        colors = dict(zip(cases, colors.split(',')))

    ### Get results
    dfplot = {c: get_transfer_peak_fraction(c, level, tstart) for c in cases}
    dfmap = get_dfmap(cases[0])

    ### Implied inputs
    regions = dfplot[cases[0]].columns
    ncols = len(regions)
    if ncols == 1:
        raise NotImplementedError(
            "Only one region modeled so can't plot interregional transmission")

    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(
            2, ncols, sharex='row', sharey='row', figsize=(1.35*ncols, 6),
            gridspec_kw={'hspace':0.1, 'height_ratios':[0.2,1]},
        )
    for c in cases:
        for col, region in enumerate(regions):
            ax[1,col].plot(
                dfplot[c].index, dfplot[c][region].values, color=colors[c],
                label=casenames[c],
            )
    ## Formatting
    for col, region in enumerate(regions):
        ax[1,col].set_title(region, weight='bold')
        ax[1,col].set_xlabel(None)
        ax[1,col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(20))
        ax[1,col].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(10))
        ax[1,col].yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5))
        ax[1,col].yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1))
        if grid:
            ax[1,col].grid(axis='y', which='major', ls=(0, (5, 5)), c='0.6', lw=0.3)
            ax[1,col].grid(axis='y', which='minor', ls=(0, (5, 10)), c='0.85', lw=0.3)

        ## Maps at top
        dfmap[level].plot(ax=ax[0,col], facecolor='0.99', edgecolor='0.75', lw=0.2)
        dfmap[level].loc[[region]].plot(ax=ax[0,col], facecolor='k', edgecolor='none')
        ax[0,col].axis('off')
        ax[0,col].patch.set_facecolor('none')

    ### Custom legend
    handles = ([
        mpl.patches.Patch(
            facecolor=colors[c], edgecolor='none', label=casenames[c])
        for c in cases[::-1]
    ])

    _leg = ax[1,-1].legend(
        handles=handles,
        loc='upper left', bbox_to_anchor=(-0.05,1.02),
        fontsize='large', frameon=True, edgecolor='none', framealpha=1,
        handletextpad=0.3, handlelength=0.7,
        ncol=1, labelspacing=0.5,
    )

    ## Formatting
    ax[1,0].set_ylabel('Transfer capability\n/ peak demand [fraction]')
    _ymax = 1 if ((ymax is None) and (ax[1,0].get_ylim()[1] < 1)) else ymax
    ax[1,0].set_ylim(0, _ymax)
    ax[1,0].set_xlim(dfplot[c].index.min(), dfplot[c].index.max())
    plots.despine(ax)
    plt.draw()
    plots.shorten_years(ax[1,0], start_shortening_in=2021)

    return f, ax, dfplot


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
        **{'H2-CT':'h2','Gas-CT_H2-CT':'h2','Gas-CC_H2-CT':'h2'},
    }
    try:
        bokehcolors = pd.read_csv(
            os.path.join(reeds_path,'bokehpivot','in','reeds2','tech_style.csv'),
            index_col='order').squeeze(1)
    except FileNotFoundError:
        bokehcolors = pd.read_csv(
            os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
            index_col='order').squeeze(1)
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
        inclusive='left', freq='h', tz='Etc/GMT+5',
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
        os.path.join(case,'inputs_case','load_h_hourly.csv'),
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
        for ((r,rr),GW) in transcap.items():
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
        case, agglevel='transreg', startyear=2020,
        f=None, ax=None, dpi=None,
        wscale='auto', width_inter=3e5, width_intra_frac=0.5, width_step=3,
        drawstates=0., drawzones=0., scale_loc=(2.5,-1.5), scale_val=100,
        drawgrid=False, drawregions=1.,
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
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
        index_col='raw')['display']
    transcolors = pd.read_csv(
            os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
            index_col='order')['color']
    transcolors = pd.concat([transcolors, trtypes.map(transcolors)])

    rename = ['AC_init','B2B_init','LCC_init','AC','LCC','VSC']
    for c in rename:
        if c.lower() in transcolors:
            transcolors[c] = transcolors[c.lower()]

    ###### Get line drawing settings
    dfcorridors = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','plots','transmission-interface-coords.csv'),
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
    dfplot = tran_out_agg.loc[tran_out_agg.t >= startyear].pivot(
        index=['aggreg1','aggreg2','t'],columns='trtype',values='GW'
    ).reindex(['B2B','AC','LCC','VSC'],axis=1).dropna(axis=1, how='all')

    ### Plot settings
    width_year = width_inter / len(tran_out_agg.t.unique())
    yearspan = tran_out_agg.t.max() - startyear
    if wscale in ['auto','scale','default',None,'','max']:
        df = dfplot.reset_index()
        capmax = max([
            (df.loc[df.aggreg1==df.aggreg2].groupby('t').sum().sum(axis=1).max()
             if width_intra else 0),
            df.loc[df.aggreg1!=df.aggreg2].groupby('t').sum().sum(axis=1).max(),
        ])
        _wscale = 3e6 / capmax * 0.95
    else:
        _wscale = wscale

    ###### Plot it
    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=(12,8),dpi=dpi)
    ### Plot background
    if drawregions:
        dfreg.plot(ax=ax, facecolor='none', edgecolor='k', lw=drawregions)
        if drawstates:
            dfstates.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawstates)
        if drawzones:
            dfba.plot(ax=ax, facecolor='none', edgecolor='0.5', lw=drawzones)

    ### Transmission
    for (r1,r2), (x,y,angle) in dfcorridors.iterrows():
        if (r1 == r2) and (not width_intra_frac):
            continue
        try:
            df = dfplot.loc[r1].loc[r2] * _wscale
        except KeyError:
            try:
                df = dfplot.loc[r2].loc[r1] * _wscale
            except KeyError:
                continue
        df.index = (
            (df.index - startyear - yearspan/2)
            * width_year / width_step
            * (width_intra_frac if r1 == r2 else 1)
        )
        y -= df.sum(axis=1).max() / 2

        plots.stackbar(
            df=df,
            ax=ax, colors=transcolors,
            width=(width_year * (width_intra_frac if r1 == r2 else 1)),
            net=False, bottom=y, x0=x,
        )

    ### Scale
    if scale_loc:
        ### Get the total intra- and inter-zone capacity in GW
        dfscale = dfplot.reset_index()
        dfintra = (
            dfscale.loc[dfscale.aggreg1 == dfscale.aggreg2]
            .drop(['aggreg1','aggreg2'],axis=1).groupby('t').sum()
        ) * _wscale
        dfinter = (
            dfscale.loc[dfscale.aggreg1 != dfscale.aggreg2]
            .drop(['aggreg1','aggreg2'],axis=1).groupby('t').sum()
        ) * _wscale
        dfintra.index = (
            (dfintra.index - startyear - yearspan/2)
            * width_year / width_step * width_intra_frac)
        dfinter.index = (dfinter.index - startyear - yearspan/2) * width_year / width_step
        ### Get the bar locations
        gap = 0.06e6
        xintra = scale_loc[0]*1e6 + (width_inter * width_intra_frac)/2 + gap/2
        xinter = scale_loc[0]*1e6 - width_inter/2 - gap/2
        y0 = scale_loc[1]*1e6
        ### Plot and annotate them
        ## Intra
        if width_intra_frac:
            plots.stackbar(
                df=dfintra,
                ax=ax, colors=transcolors, width=width_year*width_intra_frac,
                net=False, bottom=y0, x0=xintra,
            )
            ax.annotate(
                'Intra', (xintra,y0-0.02e6), weight='bold', ha='center', va='top',
                fontsize='large', annotation_clip=False)
        ## Inter
        plots.stackbar(
            df=dfinter,
            ax=ax, colors=transcolors, width=width_year, net=False,
            bottom=y0, x0=xinter,
        )
        ax.annotate(
            'Inter', (xinter,y0-0.02e6), weight='bold', ha='center', va='top',
            fontsize='large', annotation_clip=False)
        ### Add scale
        if scale_val:
            xscale = xinter - width_inter/2 - gap
            plots.stackbar(
                pd.DataFrame({'scale':scale_val*_wscale}, index=[xscale]),
                ax=ax, colors={'scale':'k'}, width=width_intra/10, net=False, bottom=y0,
            )
            ax.annotate(
                f'{scale_val} GW', (xscale-gap/2,y0+scale_val*_wscale/2), weight='bold',
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
        case, data='cap', startyear=2022, agglevel='transreg',
        f=None, ax=None, dpi=None,
        wscale='auto', width_total=4e5, width_step=3,
        drawstates=0., drawzones=0., scale_loc=(2.3,-1.55), scale_val=1000,
        drawgrid=False, transmission=False, legend=True,
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

    ### Get colors and simpler tech names
    capcolors = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)
    tech_map = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*'))
    tech_map = tech_map.drop_duplicates().set_index('raw').display

    ### Get outputs
    if data in ['cap','Cap','capacity',None,'GW','']:
        val = pd.read_csv(
            os.path.join(case,'outputs','cap.csv'),
            header=0, names=['i','r','t','Value']
        )
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
        ### Convert generation to TWh
        val.Value /= 1e6
        val.i = val.i.str.lower()
        val = val.loc[val.t >= startyear].copy()
        units = 'TWh'

    ### Map capacity to agglevel
    val['aggreg'] = val.r.map(hierarchy[agglevel])
    val_agg = val.copy()
    ## Use reduced technology set
    val_agg.i = val_agg.i.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')).map(tech_map)
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
        os.path.join(reeds_path,'postprocessing','plots','transmission-interface-coords.csv'),
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
    if (f is None) and (ax is None):
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
        try:
            df = dfplot.loc[aggreg] * _wscale
        except KeyError:
            continue
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
        ### Scale down scale value if necessary
        if capmax < scale_val*2:
            scale_val /= 10
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

    ###### Inter-regional transmission, if requested
    if transmission:
        map_trans_agg(
            case=case, agglevel=agglevel, startyear=startyear,
            f=f, ax=ax, dpi=dpi, wscale=_wscale, width_step=width_step,
            width_intra_frac=0, drawregions=0, drawgrid=False,
            scale_val=0, width_inter=width_total,
            scale_loc=(scale_loc[0]+0.7, scale_loc[1]),
        )

    ###### Legend
    if legend:
        handles = [
            mpl.patches.Patch(facecolor=capcolors[i], edgecolor='none', label=i)
            for i in capcolors.index if i in dfplot.columns
        ]
        _leg = ax.legend(
            handles=handles[::-1], loc='upper left', fontsize=6, ncol=1, frameon=False,
            bbox_to_anchor=((0.875,0.95) if transmission else (0.955,0.95)),
            handletextpad=0.3, handlelength=0.7, columnspacing=0.5, 
        )

    ###### Formatting
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


def map_capacity_markers(
        case, level='r', year=2050, ms=5,
        unitsize=1,
        f=None, ax=None,
        verbose=0,
    ):
    """
    Inputs
    ------
    level [str]: Hierarchy level at which to distribute markers
    unitsize [float]: GW capacity for each marker
    transmission_linesize [float]: GW capacity for each transmission line
        (if 0, do not plot transmission)
    """
    ### Additional settings
    decrement = 0.02
    markers = {
        'upv': 'o',
        'distpv': 'o',
        'csp': 'o',

        'wind-ons': '^',
        'wind-ofs': 'v',

        'battery_4': (4,1,0),
        'battery_8': (8,1,0),
        'pumped-hydro': (12,1,0),

        'hydro': 's',
        'nuclear': 'p', # '☢️',
        'nuclear-smr': 'p',
        'biopower': (5,1,0),
        'lfill-gas': (5,1,0),
        'beccs_mod': (5,1,180),
        'geothermal': 'h',

        'h2-ct': '>',

        'gas-cc': '<',
        'gas-cc-ccs_mod': 'D',
        'gas-ct': '>',
        'o-g-s': 'd',
        'coal': 'X',
        'coal-ccs_mod': 'P',
    }
    drop = [
        'canada',
        'electrolyzer',
        'smr', 'smr-ccs',
    ]
    tech_style = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order',
    ).squeeze(1)
    tech_style.index = tech_style.index.str.lower()

    ###### All in one
    ### Load the data
    val_r = pd.read_csv(
        os.path.join(case, 'inputs_case', 'val_r.csv'), header=None,
    ).squeeze(1).tolist()
    dfba = get_zonemap(case).loc[val_r]
    dfstates = dfba.dissolve('st')
    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    hierarchy = hierarchy.loc[hierarchy.country.str.lower()=='usa'].copy()

    cap = pd.read_csv(
        os.path.join(case,'outputs','cap.csv')
    )
    cap = cap.loc[cap.t==year].copy()
    cap['GW'] = cap.Value / 1e3
    ### Aggregate and simplify tech classes and types
    cap.i = simplify_techs(cap.i)
    cap = cap.loc[~cap.i.isin(drop)].copy()
    techs = cap.i.unique()
    if any([i not in markers for i in techs]):
        print([i for i in techs if i not in markers])
    ### Group by region
    if level not in ['r','rb']:
        cap.r = cap.r.map(hierarchy[level])
    cap = cap.groupby(['r','i']).GW.sum() / unitsize

    ### Get the geometries
    regions = dfba.index if level in ['r','rb'] else hierarchy[level].unique()
    if level in ['r','rb']:
        dfzones = dfba.copy()
    else:
        dfzones = dfba.copy()
        dfzones['zone'] = dfba.index.map(hierarchy[level])
        dfzones = dfzones.dissolve('zone')

    ### Plot it
    draw_background = False
    if (not f) or (not ax):
        draw_background = True
        f,ax = plt.subplots(figsize=(12,9))
    ### Background
    if draw_background:
        if level in ['r','rb']:
            dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.1)
        dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.2)
    ### Units by zone
    if verbose:
        iterator = tqdm(regions, desc=f'map_capacity_markers {level}')
    else:
        iterator = regions
    for r in iterator:
        ### Get the number of units per tech
        r_units = cap[r].round(0).astype(int).replace(0,np.nan).dropna().astype(int)
        total_units = r_units.sum()
        ### Sort them according to the typical order in tech_style
        r_units_sorted = r_units.reindex(tech_style.index).dropna().astype(int)
        ### Get list of units
        units = [[unit]*number for (unit, number) in r_units_sorted.items()]
        ### Flatten
        units = [item for sublist in units for item in sublist]

        ### Get rectangle containing zone
        geometry = dfzones.loc[r,'geometry']
        minx, miny, maxx, maxy = geometry.bounds
        
        ### Get grid of points
        step_0 = max(maxx-minx, maxy-miny)
        step = step_0
        for iteration in range(1000):
            step = step * (1 - decrement)
            xs = np.arange(minx, maxx+1, step)
            ys = np.arange(miny, maxy+1, step)
            coords = [(x,y) for y in ys for x in xs]
            points = [shapely.geometry.Point(p) for p in coords]
            inside_geometry = [p.within(geometry) for p in points]
            if sum(inside_geometry) >= total_units:
                break

        dfplot = gpd.GeoDataFrame(
            geometry=[shapely.geometry.Point(p) for (i,p) in enumerate(coords)
                      if inside_geometry[i]],
            crs='ESRI:102008'
        ).iloc[:len(units)]
        dfplot['tech'] = units

        ### Plot it
        for tech in dfplot.tech.unique():
            dfplot.loc[dfplot.tech==tech].plot(
                ax=ax, marker=markers.get(tech,'o'),
                color=tech_style.get(tech,'k'),
                lw=0, markersize=ms)

    ### Legend
    handles = [
        mpl.lines.Line2D(
            [], [], marker=markers[i], markerfacecolor=tech_style[i],
            markeredgewidth=0, lw=0, label=i)
        for i in tech_style.index if i in techs
    ][::-1]
    _leg = ax.legend(
        handles=handles, loc='center left', bbox_to_anchor=(0.95,0.5), 
        fontsize='medium', ncol=1, frameon=False,
        handletextpad=0.3, handlelength=0.7, columnspacing=0.5,
        title=f'{unitsize} GW per marker',
    )

    ### Formatting
    ax.axis('off')

    return f, ax


def map_transmission_lines(
        case, level='r', year=2050, subtract_baseyear=None,
        transmission_linesize=2.5, radscale=35, lw=0.25,
        zorder=-1e6, alpha=1,
        f=None, ax=None,
    ):
    """
    Inputs
    ------
    transmission_linesize [float]: GW capacity for each line. Default of 2.5 GW
        is taken from the median of 500 kV lines in the NARIS dataset, rounded
        to the nearest 0.5 GW.
    """
    ### Get styles
    trtype_style = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2',
            'trtype_style.csv'),
        index_col='order',
    ).squeeze(1)
    linecolors = {
        'AC': trtype_style['AC'],
        'B2B': trtype_style['B2B'],
        'LCC': trtype_style['DC, LCC'],
        'VSC': trtype_style['DC, VSC'],
    }
    ### Get inputs
    val_r = pd.read_csv(
        os.path.join(case, 'inputs_case', 'val_r.csv'), header=None,
    ).squeeze(1).tolist()
    dfba = get_zonemap(case).loc[val_r]
    dfstates = dfba.dissolve('st')
    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    hierarchy = hierarchy.loc[hierarchy.country.str.lower()=='usa'].copy()

    if level in ['r','rb']:
        dfzones = dfba.copy()
    else:
        dfzones = dfba.copy()
        dfzones['zone'] = dfba.index.map(hierarchy[level])
        dfzones = dfzones.dissolve('zone')

    tran_out = pd.read_csv(
        os.path.join(case,'outputs','tran_out.csv')
    )
    if subtract_baseyear:
        tran_out = (
            tran_out.loc[tran_out.t==year].set_index(['r','rr','trtype']).Value
            - (
                tran_out
                .loc[(tran_out.t==subtract_baseyear)]
                .set_index(['r','rr','trtype']).Value
                .reindex(tran_out.loc[tran_out.t==year].set_index(['r','rr','trtype']).index)
                .fillna(0)
            )
        ).clip(lower=0).reset_index()
        tran_out = tran_out.loc[tran_out.Value>0].copy()
    else:
        tran_out = tran_out.loc[tran_out.t==year].copy()
    tran_out['lines'] = (
        ## Convert to GW
        tran_out.Value / 1e3
        ## Convert to lines
        / transmission_linesize
    )
    ### Group by region
    if level not in ['r','rb']:
        tran_out.r = tran_out.r.map(hierarchy[level])
        tran_out.rr = tran_out.rr.map(hierarchy[level])
    ### Group and round to lines
    tran_out = (
        tran_out.groupby(['r','rr','trtype']).lines.sum()
        .round(0).astype(int).replace(0,np.nan).dropna().astype(int).reset_index()
    )
    tran_out['interface'] = tran_out.r + '||' + tran_out.rr
    tran_out = tran_out.set_index(['interface','trtype']).lines

    trtypes = tran_out.index.get_level_values('trtype').unique()
    interfaces = tran_out.index.get_level_values('interface').unique()

    draw_background = False
    if (not f) or (not ax):
        draw_background = True
        f,ax = plt.subplots(figsize=(12,9))
    ### Background
    if draw_background:
        if level in ['r','rb']:
            dfba.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.1, zorder=-1e8)
        dfstates.plot(ax=ax, facecolor='none', edgecolor='k', lw=0.2, zorder=-1e8)
    ### Data
    for interface in interfaces:
        ## Get properties of interface
        df = tran_out.loc[interface]
        r,rr = interface.split('||')
        startx, starty = dfzones.loc[r,['x','y']]
        endx, endy = dfzones.loc[rr,['x','y']]
        distance = ((startx-endx)**2 + (starty-endy)**2)**0.5 / 1e3
        ## Get lines
        lines = [[trtype]*val for (trtype,val) in df.items()]
        lines = [item for sublist in lines for item in sublist]
        rads = np.arange(-len(lines)/2, len(lines)/2, 1)
        if not (len(rads) == len(lines)):
            raise ValueError(f'len(rads) = {len(rads)} but len(lines) = {len(lines)}')
        for (line, rad) in zip(lines, rads):
            ax.add_patch(
                mpl.patches.FancyArrowPatch(
                    (startx, starty), (endx, endy),
                    connectionstyle=f'Arc3, rad={rad/distance*radscale}',
                    shrinkA=0, shrinkB=0,
                    lw=lw, color=linecolors[line],
                    zorder=zorder, alpha=alpha,
                )
            )
    ### Legend
    handles = [
        mpl.lines.Line2D([], [], lw=2, label=i, color=linecolors[i])
        for i in linecolors if i in trtypes
    ]
    title = f'{transmission_linesize} GW lines, {year}'
    if subtract_baseyear:
        title += f'\n(new since {subtract_baseyear})'
    leg = ax.legend(
        handles=handles, loc='lower left', bbox_to_anchor=(0.1,0.1), 
        fontsize='medium', ncol=1,
        handletextpad=0.4, handlelength=1, columnspacing=0.5,
        frameon=True, edgecolor='none', framealpha=0.7,
        title=title,
    )
    ax.add_artist(leg)

    ### Formatting
    ax.axis('off')
    return f,ax


def map_zone_capacity(
        case, year=2050, valscale=3e3, width=7e4,
        center=True, linealpha=0.6,
        scale=10, sideplots=True, legend=True,
        f=None, ax=None,
    ):
    """
    Inputs
    ------
    scale: [float] scalebar size in GW; if zero, don't plot scalebar
    sideplots: Nationwide tranmsission, emissions, generation, and generation capacity
    """
    ###### Shared inputs
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'),
        header=None, index_col=0).squeeze(1)
    years = pd.read_csv(
        os.path.join(case,'inputs_case','modeledyears.csv')).columns.astype(int).values
    yearstep = years[-1] - years[-2]
    # tech_map = pd.read_csv(
    #     os.path.join(
    #         reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'),
    #     index_col='raw').squeeze(1)
    bokehcolors = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)
    bokehcolors = pd.concat([
        bokehcolors.loc['smr':'electrolyzer'],
        pd.Series('#D55E00', index=['dac'], name='color'),
        bokehcolors.loc[:'Canada'],
    ])
    bokehcolors['canada'] = bokehcolors['Canada']

    trtype_map = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
        index_col='raw')['display']
    transcolors = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
        index_col='order')['color']
    transcolors = pd.concat([transcolors, trtype_map.map(transcolors)])
    transcolors['LCC'] = transcolors['lcc']
    transcolors['VSC'] = transcolors['vsc']

    dfba = get_zonemap(case)
    dfba['centroid_x'] = dfba.centroid.x
    dfba['centroid_y'] = dfba.centroid.y

    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    for col in hierarchy:
        dfba[col] = dfba.index.map(hierarchy[col])
    hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()

    dfmap = get_dfmap(case)

    ###### Case inputs
    ### Capacity
    dfcap_in = pd.read_csv(
        os.path.join(case,'outputs','cap.csv'),
        names=['i','r','t','MW'], header=0,
    )
    dfcap_in.i = simplify_techs(dfcap_in.i)
    dfcap = dfcap_in.loc[
        (dfcap_in.t==year)
    ].rename(columns={'MW':'GW'}).groupby(['i','r']).GW.sum().unstack('i') / 1e3
    dfcap = (
        dfcap[[c for c in bokehcolors.index if c in dfcap]]
        .drop('electrolyzer', axis=1, errors='ignore')
    ).copy()

    tran_out = pd.read_csv(
        os.path.join(case,'outputs','tran_out.csv')
    ).rename(columns={'Value':'MW'})

    if (f is None) and (ax is None):
        plt.close()
        f,ax = plt.subplots(figsize=(12, 9)) # (10, 6.88)
    ### Background
    dfba.plot(ax=ax, facecolor='none', edgecolor='0.8', lw=0.2)
    dfmap['st'].plot(ax=ax, facecolor='none', edgecolor='0.7', lw=0.4)
    dfmap['interconnect'].plot(ax=ax, facecolor='none', edgecolor='k', lw=1)

    ### Plot transmission
    transmap = tran_out.loc[
        (tran_out.t==year)
    ][['r','rr','trtype','MW']].rename(columns={'MW':'GW'}).copy()
    transmap.GW /= 1e3
    ## Add geographic data to the line capacity
    key = dfba[['centroid_x','centroid_y']]
    for col in ['r','rr']:
        for i in ['x','y']:
            transmap[f'{col}_{i}'] = transmap.apply(
                lambda row: key.loc[row[col]]['centroid_'+i], axis=1)

    ## Convert the line capacity dataframe to a geodataframe with linestrings
    transmap['geometry'] = transmap.apply(
        lambda row: shapely.geometry.LineString([(row.r_x, row.r_y), (row.rr_x, row.rr_y)]),
        axis=1
    )
    transmap = gpd.GeoDataFrame(transmap).set_crs('ESRI:102008')

    ## Buffer the lines into polygons
    transmap['geometry'] = transmap.apply(
        lambda row: row.geometry.buffer(row.GW*valscale/2), axis=1)

    ## Plot it
    for trtype in ['AC','B2B','LCC','VSC']:
        if trtype in transmap.trtype.unique():
            transmap.loc[transmap.trtype==trtype].dissolve().plot(
                ax=ax, facecolor=transcolors[trtype], edgecolor='none', alpha=linealpha,
            )

    ### Plot generation capacity
    plots.plot_region_bars(
        dfzones=dfba, dfdata=dfcap, colors=bokehcolors,
        ax=ax, valscale=valscale, width=width, center=center)

    ### Add a scale bar
    if scale:
        ax.bar(
            x=[-1.8e6], height=[valscale * scale], bottom=[-1.05e6], width=3.0e5,
            align='center', color='k',
        )
        ax.annotate(
            f'{scale:.0f} GW', (-1.8e6, -1.1e6), fontsize=12,
            ha='center', va='top', weight='bold')

    ###### Side plots
    eax = None
    if sideplots:
        ###### Extra data
        renametechs = {
            'h2-cc_upgrade':'h2-cc',
            'h2-ct_upgrade':'h2-ct',
            'gas-cc-ccs_mod_upgrade':'gas-cc-ccs_mod',
            'coal-ccs_mod_upgrade':'coal-ccs_mod',
        }
        dfgen_in = pd.read_excel(
            os.path.join(case,'outputs','reeds-report','report.xlsx'),
            sheet_name='3_Generation (TWh)', engine='openpyxl',
        ).drop('scenario',axis=1)
        dfgen_in.tech = dfgen_in.tech.map(lambda x: renametechs.get(x,x))
        dfgen_in = (
            dfgen_in.groupby(['tech','year'], as_index=False)['Generation (TWh)'].sum())

        dfcap_nat = pd.read_excel(
            os.path.join(case,'outputs','reeds-report','report.xlsx'),
            sheet_name='4_Capacity (GW)',
        ).drop('scenario',axis=1)
        dfcap_nat.tech = dfcap_nat.tech.map(lambda x: renametechs.get(x,x))
        dfcap_nat = (
            dfcap_nat.groupby(['tech','year'], as_index=False)['Capacity (GW)'].sum())

        emit_nat_tech = pd.read_csv(
            os.path.join(case, 'outputs', 'emit_nat_tech.csv'),
        header=0, names=['e','i','t','tonne'], index_col=['e','i','t'],
        ).squeeze(1)

        dfin_trans = pd.read_excel(
            os.path.join(case,'outputs','reeds-report','report.xlsx'),
            sheet_name='14_Transmission (GW-mi)', engine='openpyxl',
        ).drop('scenario',axis=1)

        ###### Make the side plots
        alltechs = set()
        axbounds = {
            ## left, bottom, width, height
            'Trans [TW-mi]': [0.92, 0.62, 0.1, 0.17],
            'CO2e [MMT]': [0.92, 0.41, 0.1, 0.17],
            'Cap [GW]': [0.83, 0.2, 0.1, 0.17],
            'Gen [TWh]': [1.0, 0.2, 0.1, 0.17],
        }
        eax = {}
        for a in axbounds:
            eax[a] = f.add_axes(axbounds[a])
            eax[a].set_ylabel(a)
            plots.despine(eax[a])
            eax[a].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
            eax[a].xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
            eax[a].set_xlim(2020-yearstep/2, 2050+yearstep/2)
        ### Side plot of generation capacity over time
        dfcapacity = dfcap_nat.pivot(index='year', columns='tech', values='Capacity (GW)')
        dfcapacity = (
            dfcapacity[[c for c in bokehcolors.index if c in dfcapacity]]
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all')
            .drop('electrolyzer', axis=1, errors='ignore')
            .loc[2020:]
        )
        alltechs.update(dfcapacity.columns)
        plots.stackbar(
            df=dfcapacity, ax=eax['Cap [GW]'],
            colors=bokehcolors, width=yearstep, net=False)

        ### Side plot of generation over time
        dfgen = dfgen_in.pivot(index='year', columns='tech', values='Generation (TWh)')
        dfgen = (
            dfgen[[c for c in bokehcolors.index if c in dfgen]]
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all')
            .loc[2020:]
        )
        alltechs.update(dfgen.columns)
        plots.stackbar(
            df=dfgen, ax=eax['Gen [TWh]'],
            colors=bokehcolors, width=yearstep, net=False)
        eax['Gen [TWh]'].axhline(0, c='k', ls=':', lw=0.75)

        ### Side plot of transmission capacity over time
        dftrans = dfin_trans.pivot(
            index='year', columns='trtype', values='Amount (GW-mi)') / 1e3
        dftrans = (
            dftrans[[c for c in transcolors.index if c in dftrans]]
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all')
            .loc[2020:]
        )
        plots.stackbar(
            df=dftrans, ax=eax['Trans [TW-mi]'],
            colors=transcolors, width=yearstep, net=False)

        ### Side plot of emissions over time
        dfco2e = (
            emit_nat_tech['CO2']
            .add(emit_nat_tech['CH4']
                / 1e3 * float(sw.GSw_MethaneGWP),
                fill_value=0)
            .unstack('i') / 1e3
        )
        dfco2e.columns = simplify_techs(dfco2e.columns)
        dfco2e = dfco2e.groupby(axis=1, level='i').sum()
        dfco2e = (
            dfco2e[[c for c in bokehcolors.index if c in dfco2e]]
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all').fillna(0)
            .loc[2020:]
        )
        plots.stackbar(
            df=dfco2e, ax=eax['CO2e [MMT]'],
            colors=bokehcolors, width=yearstep, net=True,
            markerfacecolor=(1,1,1,0.8), markersize=4.5)
        eax['CO2e [MMT]'].axhline(0, c='k', ls=':', lw=0.75)

        plt.draw()
        for a in eax:
            plots.shorten_years(eax[a])

        ### Legend
        if legend:
            ### Generation
            handles = [
                mpl.patches.Patch(facecolor=bokehcolors[i], edgecolor='none', label=i)
                for i in bokehcolors.index if i in alltechs
            ]
            leg_gen = ax.legend(
                handles=handles[::-1], loc='lower left', fontsize=6.5, frameon=False,
                bbox_to_anchor=(1.16,0.332),
                handletextpad=0.3, handlelength=0.7, columnspacing=0.5,
            )
            ## Draw it
            ax.add_artist(leg_gen)
            ### Transmission
            handles = [
                mpl.patches.Patch(facecolor=transcolors[i], edgecolor='none', label=i)
                for i in transcolors.index if i in dftrans
            ]
            _leg_trans = ax.legend(
                handles=handles[::-1], loc='upper left', fontsize=6.5, frameon=False,
                bbox_to_anchor=(1.16,0.92),
                handletextpad=0.3, handlelength=0.7, columnspacing=0.5,
            )

    ### Formatting
    ax.axis('off')

    return f, ax, eax


def plot_retire_add(
        case, yearstart=2020, width=0.25, peak=True,
        plotyears=None, figsize=None,
    ):
    """
    """
    ### Colors
    bokehcolors = pd.read_csv(
        os.path.join(
            reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)
    bokehcolors = pd.concat([
        bokehcolors.loc['smr':'electrolyzer'],
        pd.Series('#D55E00', index=['dac'], name='color'),
        bokehcolors.loc[:'Canada'],
    ])
    bokehcolors['canada'] = bokehcolors['Canada']
    bokehcolors = bokehcolors.to_dict()

    ### For this particular plot we put storage below VRE
    plotorder = (
        list(bokehcolors.keys())[:list(bokehcolors.keys()).index('wind-ons')]
        + list(bokehcolors.keys())[
            list(bokehcolors.keys()).index('battery'):list(bokehcolors.keys()).index('Canada')]
        + list(bokehcolors.keys())[
            list(bokehcolors.keys()).index('wind-ons'):list(bokehcolors.keys()).index('battery')]
        + list(bokehcolors.keys())[list(bokehcolors.keys()).index('Canada'):]
    )

    ### Case-specific inputs
    years = pd.read_csv(
        os.path.join(case,'inputs_case','modeledyears.csv')).columns.astype(int).values
    if not plotyears:
        _years = [y for y in years if y >= yearstart]
    else:
        _years = plotyears

    if not figsize:
        _figsize = (len(_years)*1.5, 5)
    else:
        _figsize = figsize

    ## Nationwide capacity
    dfcap_in = pd.read_excel(
        os.path.join(case,'outputs','reeds-report','report.xlsx'),
        sheet_name='4_Capacity (GW)',
    ).drop('scenario', axis=1)
    ## Simplify techs
    renametechs = {
        'h2-cc_upgrade':'h2-cc',
        'h2-ct_upgrade':'h2-ct',
        'gas-cc-ccs_mod_upgrade':'gas-cc-ccs_mod',
        'coal-ccs_mod_upgrade':'coal-ccs_mod',
    }
    dfcap_in.tech = dfcap_in.tech.map(lambda x: renametechs.get(x,x))
    dfcap_in = dfcap_in.groupby(['tech','year'], as_index=False)['Capacity (GW)'].sum()

    ## Time index
    fulltimeindex = np.ravel([
        pd.date_range(
            f'{y}-01-01', f'{y+1}-01-01',
            freq='H', inclusive='left', tz='EST',
        )[:8760]
        for y in range(2007,2014)
    ])

    ## Peak coincident demand
    if peak:
        dfdemand = (
            pd.read_hdf(os.path.join(case,'inputs_case','load.h5'))
            .sum(axis=1).unstack('year').set_index(fulltimeindex)
            / 1e3
        )
        dfpeak = dfdemand.max().loc[_years]

    ### Calculate the retirements and additions
    dfcap = (
        dfcap_in
        .pivot(index='year', columns='tech', values='Capacity (GW)')
        .drop(columns=['Canada','electrolyzer'], errors='ignore')
    )
    dfcap = dfcap[[c for c in plotorder if c in dfcap]].copy()

    difference = {}
    retirements = {}
    additions = {}
    for i, year in enumerate(_years[:-1]):
        difference[year] = dfcap.loc[_years[i+1]] - dfcap.loc[year]
        retirements[year] = difference[year].loc[difference[year] < 0].copy()
        additions[year] = difference[year].loc[difference[year] > 0].copy()


    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=_figsize)
    for x, year in enumerate(_years[:-1]):
        ## First year
        df = dfcap.loc[[year]]
        df.index = [x]
        plots.stackbar(
            df=df, ax=ax, colors=bokehcolors, width=width, net=False,
        )
        bottom = df.sum().sum()
        ## Retirements
        df = retirements[year].rename(x+0.333).to_frame().T
        plots.stackbar(
            df=df, ax=ax, colors=bokehcolors, width=width, net=False, bottom=bottom,
        )
        bottom = bottom + df.sum().sum()
        ## Additions
        df = additions[year].rename(x+0.667).to_frame().T
        plots.stackbar(
            df=df, ax=ax, colors=bokehcolors, width=width, net=False, bottom=bottom,
        )

    ## Last year
    df = dfcap.loc[[_years[-1]]]
    df.index = [len(_years)-1]
    plots.stackbar(
        df=df, ax=ax, colors=bokehcolors, width=width, net=False,
    )

    ### US coincident peak demand
    if peak:
        ax.plot(
            range(len(_years)), dfpeak.values,
            marker='o', markerfacecolor='w', markeredgecolor='k', lw=0,
        )
        ax.annotate(
            va='center', ha='left', annotation_clip=False, fontsize=12,
            text='Peak\ndemand', xy=(0+width/3, dfpeak.iloc[0]),
            xytext=(0+width*1.2, dfpeak.iloc[0]),
            arrowprops={'arrowstyle':'-|>', 'color':'k'}
        )

    ### Legend
    handles = [
        mpl.patches.Patch(facecolor=bokehcolors[i], edgecolor='none', label=i)
        for i in plotorder if i in dfcap
    ]
    _leg = ax.legend(
        handles=handles[::-1], loc='center left', bbox_to_anchor=(1.0,0.5), 
        fontsize='large', ncol=1, frameon=False,
        handletextpad=0.3, handlelength=0.7, columnspacing=0.5, labelspacing=0.1,
    )

    ### Formatting
    xlabels = [[str(year),'retire','add'] for year in _years]
    xlabels = [i for sublist in xlabels for i in sublist][:-2]
    # ## Try making the years bigger
    # xlabels[0] = mpl.text.Text(text='foo', fontsize='x-large', weight='bold')
    ax.set_ylabel('Capacity [GW]')
    ax.set_xticks(np.linspace(0, len(_years)-1, (len(_years)-1)*3 + 1))
    ax.set_xticklabels(xlabels, rotation=45, ha='right', rotation_mode='anchor')
    ax.set_xlim(-width/2 - 0.05, len(_years)-1 + width/2 + 0.05)
    ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(100))
    plots.despine(ax)

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
        os.path.join(reeds_path,'inputs','supplycurvedata','sitemap.csv'),
        index_col='sc_point_gid'
    )
    sitemap.index = 'i' + sitemap.index.astype(str)

    val_r = pd.read_csv(
        os.path.join(case,'inputs_case','val_r.csv'),
        header=None,
    ).squeeze(1).values.tolist()

    dfba = get_zonemap(case).loc[val_r]

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


def plot_dispatch_yearbymonth(
        case, t=2050, f=None, ax=None, figsize=(12,6),
        techs=None, highlight_rep_periods=1):
    """
    Full year dispatch for final year with rep days mapped to actual days
    Inputs
    techs: None to plot all techs, or list of subset techs, or single tech string
    """
    ### Load bokeh tech map and colors
    tech_map = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*'))
    tech_map = tech_map.drop_duplicates().set_index('raw').display

    tech_style = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)

    ### Load run files
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'),
        header=None, index_col=0).squeeze(1)
    hmap_myr = pd.read_csv(os.path.join(case, 'inputs_case', 'hmap_myr.csv'))
    gen_h = pd.read_csv(os.path.join(case, 'outputs', 'gen_h.csv'))
    gen_h.i = gen_h.i.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')
    ).str.lower().map(lambda x: tech_map.get(x,x))
    dispatch = (
        gen_h.loc[gen_h.t==t]
        .groupby(['i','allh']).Value.sum()
        .unstack('i').fillna(0)
        / 1e3
    )
    if techs is not None:
        if isinstance(techs, list):
            dispatch = dispatch[[c for c in techs if c in dispatch]].copy()
        else:
            dispatch = dispatch[[techs]].copy()
    ### Broadcast representative days to actual days
    dfin = (
        hmap_myr[['actual_h','h']]
        .merge(dispatch, left_on='h', right_index=True)
        .sort_values('actual_h').set_index('actual_h').drop('h', axis=1)
    )

    dfin.index = dfin.index.map(h2timestamp)

    ### Put negative parts of columns that go negative on bottom
    goes_negative = list(dfin.columns[(dfin < 0).any()])
    df = dfin.copy()
    for col in goes_negative:
        df[col+'_neg'] = df[col].clip(upper=0)
        df[col+'_off'] = df[col].clip(upper=0).abs()
        df[col+'_pos'] = df[col].clip(lower=0)
    df.drop(goes_negative, axis=1, inplace=True)

    negcols = [c+'_neg' for c in goes_negative]
    offsetcols = [c+'_off' for c in goes_negative]
    poscols = [c+'_pos' for c in goes_negative]
    plotorder = negcols + offsetcols + list(tech_style.index) + poscols
    dfplot = (
        df
        [[c for c in plotorder if c in df]].cumsum(axis=1)
        [[c for c in plotorder[::-1] if c in df]]
    )

    ### Read rep periods if necessary
    if highlight_rep_periods:
        # timestamps = pd.read_csv(os.path.join(case,'inputs_case','timestamps.csv'))
        period_szn = pd.read_csv(os.path.join(case,'inputs_case','period_szn.csv'))
        period_szn['timestamp'] = (period_szn.actual_period+'h001').map(h2timestamp)
        period_szn['rep'] = (period_szn.rep_period == period_szn.actual_period)
        repnum = dict(zip(
            sorted(period_szn.rep_period.unique()),
            range(1, len(period_szn.rep_period.unique())+1)
        ))
        period_szn['repnum'] = period_szn.rep_period.map(repnum)

    ### Plot it
    plt.close()
    f, ax = plots.plotyearbymonth(
        dfplot,
        colors=[
            tech_style[i.replace('_pos','').replace('_neg','').replace('_off','')]
            for i in dfplot],
        lwforline=0, f=f, ax=ax, figsize=figsize)

    if highlight_rep_periods:
        width = pd.Timedelta('5D') if sw['GSw_HourlyType'] == 'wek' else pd.Timedelta('1D')
        ylim = ax[0].get_ylim()
        for i, row in period_szn.iterrows():
            plottime = pd.Timestamp(2001, 1, row.timestamp.day)
            if row.rep:
                ## Draw an outline
                box = mpl.patches.Rectangle(
                    xy=(plottime, ylim[0]),
                    width=width, height=(ylim[1]-ylim[0]),
                    lw=0.75, edgecolor='k', facecolor='none', ls=':',
                    clip_on=False, zorder=2e6
                )
            else:
                ## Wash out the dispatch
                box = mpl.patches.Rectangle(
                    xy=(plottime, ylim[0]),
                    width=width, height=(ylim[1]-ylim[0]),
                    lw=0.75, edgecolor='none', facecolor='w', alpha=0.4,
                    clip_on=False, zorder=1e6
                )
            ax[row.timestamp.month-1].add_patch(box)
            ## Note the rep period
            ax[row.timestamp.month-1].annotate(
                row.repnum,
                (plottime+pd.Timedelta('30m'), ylim[1]*0.95),
                va='top', size=5, zorder=1e7,
                color=('k' if row.rep else 'C7'),
                weight=('normal' if row.rep else 'normal'),
            )

    return f, ax


def plot_dispatch_weightwidth(
        case, val='7_Final Gen by timeslice (GW)', figsize=(13,4)):
    """
    Rep period dispatch for final year with period width given by period weight
    """
    ### Load run files
    hmap_myr = pd.read_csv(os.path.join(case, 'inputs_case', 'hmap_myr.csv'))
    dispatch = (
        pd.read_excel(
            os.path.join(case, 'outputs', 'reeds-report', 'report.xlsx'),
            sheet_name=val, engine='openpyxl')
        .drop(['scenario','Net Level Generation (GW)'], axis=1, errors='ignore')
        .pivot(index='timeslice',columns='tech',values='Generation (GW)'))
    bokehcolors = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order').squeeze(1)
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'),
        header=None, index_col=0).squeeze(1)

    ### Get some settings
    GSw_HourlyChunkLength = int(sw.GSw_HourlyChunkLengthRep)
    hours_per_period = {'day':24, 'wek':120, 'year':24}[sw.GSw_HourlyType]
    dfplot = dispatch[[c for c in bokehcolors.index if c in dispatch]].copy()
    sznweights = (
        hmap_myr['actual_period' if sw.GSw_HourlyType == 'year' else 'season']
        .value_counts()
        // hours_per_period
    )

    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        1, len(sznweights), figsize=figsize, sharex=True, sharey=True,
        gridspec_kw={'wspace':0, 'width_ratios':sznweights.values},
    )
    for col, szn in enumerate(sznweights.index):
        date = h2timestamp(szn).strftime('%Y-%m-%d')
        df = dfplot.loc[dfplot.index.str.startswith(szn)]
        plots.stackbar(df=df, ax=ax[col], colors=bokehcolors, align='edge', net=False)
        ax[col].axhline(0, c='k', ls=':', lw=0.75)
        if col:
            ax[col].axis('off')
        if sw.GSw_HourlyType != 'year':
            ax[col].axvline(0, c='w', lw=0.25)
            ax[col].annotate(f'{date} ({sznweights[szn]})', (0,1), xycoords='axes fraction', rotation=45)
    ### Formatting
    ax[0].set_xlim(0, hours_per_period / GSw_HourlyChunkLength)
    plots.despine(ax[0], bottom=False)
    ax[0].set_xticks([])
    ax[0].set_ylabel('Generation [GW]')

    return f, ax


def get_stressperiods(case):
    """Get dataframe of stress periods sorted by year and iteration"""
    inpaths = [
        i for i in sorted(glob(os.path.join(case,'inputs_case','stress*')))
        if os.path.isdir(i)
    ]
    dictin_stressperiods = {
        tuple([int(x) for x in os.path.basename(f)[len('stress'):].split('i')]):
        pd.read_csv(os.path.join(f,'set_szn.csv'), index_col='*szn').squeeze(1)
        for f in inpaths
    }
    dfstress = pd.concat(dictin_stressperiods, names=['year','iteration']).sort_index()
    dfstress['date'] = dfstress.index.get_level_values('*szn').map(
        lambda x: h2timestamp(x.strip('s')+'h01').strftime('%Y-%m-%d')
    )
    return dfstress


def plot_stressperiod_dispatch(case, tmin=2023, level='country', regions='USA'):
    """
    """
    ### Parse inputs
    if isinstance(regions, str):
        _regions = [regions.lower()]
    else:
        _regions = [r.lower() for r in regions]

    ### Get settings
    sw = pd.read_csv(
        os.path.join(case,'inputs_case','switches.csv'), header=None, index_col=0).squeeze(1)

    tech_map = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'))
    tech_map.raw = tech_map.raw.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*'))
    tech_map = tech_map.drop_duplicates().set_index('raw').display

    tech_style = pd.read_csv(
        os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
        index_col='order',
    ).squeeze(1)

    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    keepr = hierarchy.loc[hierarchy[level].str.lower().isin(_regions)].index

    years = pd.read_csv(
        os.path.join(case,'inputs_case','modeledyears.csv')).columns.astype(int).values

    ### Get model outputs
    gen_h_stress = pd.read_csv(
        os.path.join(case,'outputs','gen_h_stress.csv'),
        header=0, names=['i','r','h','t','GW'],
    )
    gen_h_stress.GW /= 1000
    gen_h_stress.i = gen_h_stress.i.str.lower()

    ### Get stress periods
    dfstress = get_stressperiods(case)

    ### Aggregate
    dispatch_agg = gen_h_stress.copy()
    dispatch_agg.i = dispatch_agg.i.map(
        lambda x: x if x.startswith('battery') else x.strip('_01234567890*')
    ).str.lower().map(lambda x: tech_map.get(x,x))
    dispatch_agg = (
        dispatch_agg.loc[dispatch_agg.r.isin(keepr)]
        .groupby(['i','h','t'], as_index=False).GW.sum())

    dfplot = (
        dispatch_agg.pivot(index=['t','h'], columns='i', values='GW').fillna(0)
        .reindex(tech_style.index, axis=1).dropna(axis=1)
    )

    ### Get plot settings
    ncols = max([len(dfstress.loc[y].drop_duplicates()) for y in years])
    numh = (120 if sw.GSw_HourlyType == 'wek' else 24)//int(sw.GSw_HourlyChunkLengthStress)

    ts = sorted(dfplot.index.get_level_values('t').unique())
    ts = [t for t in ts if t > tmin]

    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        len(ts), ncols, figsize=(1*ncols, 1*len(ts)), sharex=True, sharey=True,
        gridspec_kw={'hspace':0.5},
    )
    for row, t in enumerate(ts):
        dfyear = dfplot.loc[t]
        ### Plot "seed" stress periods first, then iteratively identified periods in order
        dfstress_year = dfstress.loc[t].drop_duplicates()
        stress_period_t = dfstress_year.index.get_level_values('*szn')
        for col in range(ncols):
            ### Turn off axis if unused
            if col >= len(stress_period_t):
                ax[row,col].axis('off')
                continue      
            ### Plot the dispatch for this stress period
            d = stress_period_t[col]
            dfday = dfyear.loc[dfyear.index.str.startswith(d)]
            plots.stackbar(dfday, ax[row,col], colors=tech_style, net=False, align='edge')
            ### Formatting
            ax[row,col].set_title(
                h2timestamp(d+'h01').strftime('%Y-%m-%d'), y=0.92, fontsize=10)
        ### Formatting
        ax[row,0].annotate(
            t, (-0.8,0.5), xycoords='axes fraction', ha='right', va='center',
            weight='bold', fontsize=14)
        ### Draw a line between each iteration
        for col in range(dfstress_year.index.get_level_values('iteration').max()):
            ax[row,len(dfstress_year.loc[:col])-1].annotate(
                '', (1.075,0), xytext=(1.075,1), xycoords='axes fraction',
                annotation_clip=False,
                arrowprops={'arrowstyle':'-', 'color':'C7'},
            )
    ### Formatting
    ax[0,0].set_xlim(0, numh)
    ax[0,0].xaxis.set_major_locator(
        mpl.ticker.MultipleLocator(24//int(sw.GSw_HourlyChunkLengthStress)))
    ax[0,0].xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter(''))
    ax[0,0].annotate(
        'Stress period dispatch [GW]', (-0.5,1.5), xycoords='axes fraction',
        weight='bold', fontsize=14)
    plots.despine(ax)

    return f,ax


def plot_stressperiod_days(case, repcolor='k', sharey=False, figsize=(10,5)):
    """
    figsize [tuple]: Default to fill a ppt slide is (13.33,6.88)
    """
    ### Get shared parameters
    sw = pd.read_csv(
        os.path.join(case,'inputs_case','switches.csv'),
        header=None, index_col=0).squeeze(1)
    period_days = 1 if sw['GSw_HourlyType'] == 'day' else 5
    yplot = 2012
    timeindex = pd.date_range(
        f'{yplot}-01-01', f'{yplot+1}-01-01', freq='H', tz='EST')[:8760]
    ### Get rep periods
    szn_rep = pd.read_csv(
        os.path.join(case,'inputs_case','set_szn.csv')
    ).squeeze(1).sort_values()
    rep_starts = [h2timestamp(d+'h01') for d in szn_rep]
    rep_hours = np.ravel([
        pd.date_range(h, h+pd.Timedelta(f'{period_days}D'), freq='H', inclusive='left')
        for h in rep_starts
    ])
    dfrep = pd.Series(
        index=timeindex,
        data=timeindex.map(lambda x: x.isin(rep_hours)).astype(int),
    )
    ### Want a dict of dataframes with 8760 index, columns for rep,2007,...,2013,
    ### and keys for solve years
    dfplot = {}
    ### Get stress period IDs from output generation
    gen_h_stress = pd.read_csv(
        os.path.join(case,'outputs','gen_h_stress.csv'),
        header=0, names=['i','r','h','t','MW'],
    )
    gen_h_stress['szn'] = gen_h_stress['h'].map(lambda x: x.split('h')[0])

    years = [
        y for y in sorted(gen_h_stress.t.unique())
        if int(y) >= int(sw.GSw_StartMarkets)
    ]
    colors = plots.rainbowmapper(range(2007,2014))
    rep = f"rep ({sw.GSw_HourlyWeatherYears.replace('_',',')})"
    colors[rep] = 'k'

    t2periods = gen_h_stress.groupby('t').szn.unique()
    t2starts = t2periods.map(
        lambda row: [h2timestamp(d+'h01') for d in row]
    )
    # load = pd.read_hdf(os.path.join(case,'inputs_case','load.h5')).sum(axis=1)
    ## Use same procedure as dfpeak and G_plots.plot_e_netloadhours_timeseries()
    for t in years:
        dictout = {rep: dfrep}
        for y in range(2007,2014):
            yearstarts = [i for i in t2starts[t] if i.year == y]
            yearstarts_aligned = [
                pd.Timestamp(f'{yplot}-{i.month}-{i.day} 00:00', tz='EST')
                for i in yearstarts
            ]
            yearhours = np.ravel([
                pd.date_range(
                    h, h+pd.Timedelta(f'{period_days}D'), freq='H', inclusive='left')
                for h in yearstarts_aligned
            ])
            dictout[y] = pd.Series(
                index=timeindex,
                data=timeindex.map(lambda x: x.isin(yearhours)).astype(int),
            )
        dfplot[t] = pd.concat(dictout, axis=1)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(len(years), 1, figsize=figsize, sharex=True, sharey=sharey)
    for row, t in enumerate(years):
        dfplot[t].plot.area(
            ax=ax[row], color=colors, lw=0,
            legend=(True if row == (len(years)-1) else False),
        )
        if row == (len(years) - 1):
            ax[row].legend(
                loc='upper right', bbox_to_anchor=(1,-0.3),
                ncols=dfplot[t].shape[1], frameon=False, fontsize='large',
                columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
            )
        ### Formatting
        ax[row].annotate(
            t,(0.005,0.95),xycoords='axes fraction',ha='left',va='top',
            weight='bold',fontsize='large')
        ax[row].set_ylim(0)
        ax[row].yaxis.set_major_locator(mpl.ticker.MultipleLocator(1))
        ax[row].yaxis.set_major_formatter(plt.NullFormatter())

    ### Formatting
    ylabel = (
        'Modeled stress periods' if repcolor in ['none', None, False]
        else 'Modeled periods (representative + stress)'
    )
    ax[-1].set_ylabel(ylabel, y=0, ha='left')
    plots.despine(ax)

    return f, ax


def plot_stressperiod_evolution(case, level='transgrp', metric='sum', threshold=10):
    """Plot NEUE by year and stress period iteration"""
    ### Load NEUE results
    sw = pd.read_csv(
        os.path.join(case,'inputs_case','switches.csv'),
        header=None, index_col=0).squeeze(1)
    infiles = sorted(glob(os.path.join(case,'outputs','neue_*.csv')))
    dictin_neue = {
        tuple([int(x) for x in os.path.basename(f)[len('neue_'):-len('.csv')].split('i')]):
        pd.read_csv(f, index_col=['level','metric','region'])
        for f in infiles
    }
    ## Reshape to (year,iteration) x (region)
    dfplot = (
        pd.concat(dictin_neue, names=['year','iteration'])
        .xs(level,0,'level')
        .xs(metric,0,'metric')
        .NEUE_ppm.unstack('region')
    )
    ### Load stress periods for labels
    dfstress = get_stressperiods(case)
    ### Plot setup
    years = [
        y for y in dfplot.index.get_level_values('year').unique()
        if y >= int(sw.GSw_StartMarkets)
    ]
    ncols = len(years)
    regions = dfplot.columns
    colors = plots.rainbowmapper(regions)
    ### Plot it
    plt.close()
    f,ax = plt.subplots(1, ncols, sharey=True, figsize=(max(10,ncols*1.2),3))
    for col, year in enumerate(years):
        df = dfplot.loc[year]
        for region in regions:
            ax[col].plot(
                df.index, df[region],
                label=region, c=colors[region], marker='o', markersize=4,
            )
        ### Formatting
        ax[col].set_title(year)
        ax[col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(1))
        ax[col].axhline(threshold, lw=0.75, ls='--', c='0.7', zorder=-1e6)
        ## Annotate the stress periods
        periods = dfstress.loc[year].drop_duplicates()
        note = '\n___________\n'.join([
            f'Iteration {i}:\n'
            + '\n'.join([
                f"{'+' if i else ''} {d}"
                for d in periods.loc[i].date.values
            ])
            for i in periods.index.get_level_values('iteration').unique()
        ])
        ax[col].annotate(
            note, (0,-0.15), xycoords='axes fraction',
            fontsize=10, va='top',
            annotation_clip=False,
        )
    ### Formatting
    ax[-1].legend(
        loc='upper left', bbox_to_anchor=(1,1), frameon=False,
        handletextpad=0.3, handlelength=0.7,
    )
    ax[0].set_ylabel('NEUE [ppm]')
    ax[0].set_ylim(0)
    plots.despine(ax)

    return f,ax


def plot_neue_bylevel(
        case, tmin=2023,
        levels=['country','interconnect','transreg','transgrp'],
        metrics=['sum','max'],
        onlydata=False,
    ):
    """Plot regional NEUE over time"""
    ### Get final iterations
    year2iteration = (
        get_stressperiods(case)
        .reset_index()[['year','iteration']]
        .drop_duplicates(subset='year', keep='last')
        .set_index('year').iteration
        .loc[tmin:]
    )
    ### Get NEUE
    sw = pd.read_csv(
        os.path.join(case, 'inputs_case', 'switches.csv'),
        header=None, index_col=0).squeeze(1)
    sw['casedir'] = case
    dictin_neue = {}
    for t, iteration in year2iteration.items():
        try:
            dictin_neue[t] = pd.read_csv(
                os.path.join(case,'outputs',f'neue_{t}i{iteration}.csv'),
                index_col=['level','metric','region']
            ).squeeze(1)
        except FileNotFoundError:
            dictin_neue[t] = pd.read_csv(
                os.path.join(case,'outputs',f'neue_{t}i{iteration-1}.csv'),
                index_col=['level','metric','region']
            ).squeeze(1)
    dfin_neue = pd.concat(dictin_neue, axis=0, names=['year']).unstack('year')
    if onlydata:
        return dfin_neue
    ### Plot settings
    ncols = len(levels)
    nrows = len(metrics)
    colors = {
        level: plots.rainbowmapper(
            dfin_neue.xs(level,0,'level').reset_index().region.unique())
        for level in levels
    }
    norm = {'sum':1, 'max':1e-4}
    ylabel = {'sum': 'Sum of NEUE [ppm]', 'max':'Max NEUE [%]'}
    thresholds = {
        i.split('_')[0]: float(i.split('_')[1])
        for i in sw.GSw_PRM_StressThreshold.split('/')
    }
    ### Plot it
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(2*ncols, 3*nrows),
        sharex=True, sharey=True,
    )
    for row, metric in enumerate(metrics):
        for col, level in enumerate(levels):
            for region, c in colors[level].items():
                ax[row,col].plot(
                    dfin_neue.columns,
                    dfin_neue.loc[(level,metric,region)].values * norm[metric],
                    c=c, label=region, marker='o', markersize=2,
                )
        ## Formatting
        ax[row,0].set_ylabel(ylabel[metric])
    ## Formatting
    for col, level in enumerate(levels):
        ax[0,col].set_title(level)
        if (level in thresholds) and (not int(sw.GSw_PRM_CapCredit)):
            ax[0,col].axhline(thresholds[level], c='k', ls=':', lw=0.75)
        leg = ax[0,col].legend(
            loc='upper left', frameon=False, fontsize=8,
            handletextpad=0.3, handlelength=0.7, columnspacing=0.5, labelspacing=0.2,
            ncol=(2 if len(colors[level]) >= 10 else 1),
        )
        for legobj in leg.legend_handles:
            legobj.set_linewidth(6)
            legobj.set_solid_capstyle('butt')

    ax[0,0].set_ylim(0)
    plots.despine(ax)

    return f, ax, dfin_neue


def map_h2_capacity(
        case, year=2050, wscale_h2=3, figheight=6, pipescale=10,
        legend_kwds={'shrink':0.6, 'pad':0, 'orientation':'horizontal', 'aspect':12},
        cmap=plt.cm.gist_earth_r, 
    ):
    """
    H2 turbines, production (electrolyzer/SMR), pipelines, and storage
    """
    ### Inputs
    t2kt = 0.001
    disaggregate_types = False
    miles = 300

    if disaggregate_types:
        h2colors = {
            'h2_storage_saltcavern':'s', 'h2_storage_hardrock':'D', 'h2_storage_undergroundpipe':'o',
            'electrolyzer':'^', 'h2_turbine':'v',
        }
    else:
        h2colors = {'h2_storage': 'C1', 'electrolyzer': 'C0', 'h2_turbine': 'C3', 'h2_pipeline':'C9'}

    ### Get the BA map
    val_r = pd.read_csv(
        os.path.join(case,'inputs_case','val_r.csv'), header=None).squeeze(1).values
    dfba = get_zonemap(case).loc[val_r]
    dfmap = get_dfmap(case)

    scalars = pd.read_csv(
        os.path.join(case,'inputs_case','scalars.csv'),
        header=None, usecols=[0,1], index_col=0).squeeze(1)
    h2_ct_intensity = 1e6 / scalars['h2_energy_intensity'] / scalars['lb_per_tonne']

    ### Load storage capacity
    h2_storage_cap_in = pd.read_csv(os.path.join(case,'outputs','h2_storage_cap.csv'))
    h2_storage_cap = (
        h2_storage_cap_in.loc[h2_storage_cap_in.t==year]
        .pivot(index='r', columns='h2_stor', values='Value').fillna(0)
        * t2kt
    )
    if not disaggregate_types:
        h2_storage_cap = h2_storage_cap.sum(axis=1).rename('h2_storage')
    cap_storage = dfba.merge(h2_storage_cap, left_index=True, right_index=True)

    ### Load H2 turbine capacity, convert to kT/day
    cap_ivrt_in = pd.read_csv(os.path.join(case,'outputs','cap_ivrt.csv'))
    cap_ivrt = cap_ivrt_in.loc[
        cap_ivrt_in.i.map(lambda x: 'h2' in x.lower())
        & (cap_ivrt_in.t==year)
    ].set_index(['i','v','r']).Value
    heat_rate_in = pd.read_csv(
        os.path.join(case,'outputs','heat_rate.csv'))
    heat_rate = heat_rate_in.loc[heat_rate_in.t==year].set_index(['i','v','r']).Value
    ## capacity [MW] * heat rate [MMBtu/MWh] * [tonne/MMBtu] / 1000 * [24h/d] = [kT per day]
    cap_h2turbine = (
        cap_ivrt.multiply(heat_rate).dropna() * h2_ct_intensity / 1000 * 24
    ).rename('kTperday').groupby('r').sum()
    ## Merge with zone map
    cap_h2turbine = dfba.merge(cap_h2turbine, left_index=True, right_index=True)

    ### Get H2 production capacity
    prod_cap_in = pd.read_csv(os.path.join(case,'outputs','prod_cap.csv'))
    h2_prod_cap = prod_cap_in.loc[
        ~prod_cap_in.i.str.lower().isin(['dac'])
        & (prod_cap_in.t==year)
    ].groupby('r').Value.sum().rename('kTperday') / 1000 * 24
    ## Merge with zone map
    cap_h2prod = dfba.merge(h2_prod_cap, left_index=True, right_index=True)

    ### Load pipeline capacity
    h2_trans_cap_in = pd.read_csv(os.path.join(case,'outputs','h2_trans_cap.csv'))
    h2_trans_cap = h2_trans_cap_in.loc[h2_trans_cap_in.t==year].rename(columns={'Value':'kTperday'})
    h2_trans_cap.kTperday *= 24 / 1000

    h2_trans_cap['r_x'] = h2_trans_cap.r.map(dfba.x)
    h2_trans_cap['r_y'] = h2_trans_cap.r.map(dfba.y)
    h2_trans_cap['rr_x'] = h2_trans_cap.rr.map(dfba.x)
    h2_trans_cap['rr_y'] = h2_trans_cap.rr.map(dfba.y)

    ### Plot as separate maps
    bounds = dfmap['country'].bounds.loc['USA']
    aspect = abs((bounds.maxx - bounds.minx) / (bounds.maxy - bounds.miny))
    plt.close()
    f,ax = plt.subplots(2,2,sharex=True,sharey=True,figsize=(figheight*aspect,figheight))
    ### Background
    for row in range(2):
        for col in range(2):
            dfba.plot(ax=ax[row,col], edgecolor='0.5', facecolor='none', lw=0.1, zorder=1e4)
            dfmap['st'].plot(ax=ax[row,col], edgecolor='0.25', facecolor='none', lw=0.2, zorder=1e4)
            ax[row,col].axis('off')
    ### H2 turbines
    cap_h2turbine.plot(
        ax=ax[0,0], column='kTperday', cmap=cmap, lw=0, vmin=0,
        legend=True, legend_kwds={**legend_kwds, **{'label':'Turbines [kT/day]'}})
    # ax[0,0].set_title('H2 turbine', y=0.95)
    ### Electrolyzers
    cap_h2prod.plot(
        ax=ax[0,1], column='kTperday', cmap=cmap, lw=0, vmin=0,
        legend=True, legend_kwds={**legend_kwds, **{'label':'Production [kT/day]'}})
    # ax[0,1].set_title('H2 production', y=0.95)
    ### Storage
    cap_storage.plot(
        ax=ax[1,0], column='h2_storage', cmap=cmap, lw=0, vmin=0,
        legend=True, legend_kwds={**legend_kwds, **{'label':'Storage [kT]'}})
    # ax[1,0].set_title('H2 storage', y=0.95)
    ### Pipelines
    for i,row in h2_trans_cap.iterrows():
        ax[1,1].plot(
            [row['r_x'], row['rr_x']], [row['r_y'], row['rr_y']],
            color=h2colors['h2_pipeline'], lw=wscale_h2*row['kTperday'], solid_capstyle='butt',
            alpha=0.7,
        )
    # ax[1,1].set_title('H2 pipelines', y=0.95)
    ax[1,1].scatter(dfba.x.values, dfba.y.values, marker='o', s=1, color='k', lw=0, zorder=2e4)
    if pipescale:
        ax[1,1].plot(
            -1.75e6 + np.array([-1609/2*miles,1609/2*miles]),
            [-1.0e6, -1.0e6], solid_capstyle='butt',
            color=h2colors['h2_pipeline'], lw=wscale_h2*pipescale,
        )
        ax[1,1].annotate(
            f'Transport\n[{pipescale} kT/day]', (-1.75e6, -1.1e6),
            ha='center', va='top', weight='bold', fontsize='x-large')

    return f,ax


def plot_h2_timeseries(
        case, year=2050, agglevel='transreg', grid=0,
        figsize=(12,8),
    ):
    """
    """
    ### Load results in tonne and tonne/hour
    h2techs = ['electrolyzer','smr','smr_ccs']
    h2_storage_level = pd.read_csv(os.path.join(case,'outputs','h2_storage_level.csv'))
    h2_storage_level_szn = pd.read_csv(os.path.join(case,'outputs','h2_storage_level_szn.csv'))
    h2_inout = pd.read_csv(os.path.join(case,'outputs','h2_inout.csv'))
    prod_produce = pd.read_csv(os.path.join(case,'outputs','prod_produce.csv'))
    h2_usage = pd.read_csv(os.path.join(case,'outputs','h2_usage.csv'))
    ### Timeseries data
    hmap_myr = pd.read_csv(os.path.join(case,'inputs_case','hmap_myr.csv'))

    ###### Total across modeled area
    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')
    if agglevel == 'r':
        rmap = pd.Series(hierarchy.index.values, index=hierarchy.index.values)
    else:
        rmap = hierarchy[agglevel]

    ### Combine into one dataframe
    dfall = {
        'production': prod_produce.assign(r=prod_produce.r.map(rmap)).loc[
            prod_produce.i.isin(h2techs) & (prod_produce.t==year)
        ].rename(columns={'allh':'h'}).groupby(['r','h']).Value.sum(),
        'usage': -h2_usage.assign(r=h2_usage.r.map(rmap)).loc[
            (h2_usage.t==year)
        ].rename(columns={'allh':'h'}).groupby(['r','h']).Value.sum(),
        ## Group over H2 storage techs
        'stor_charge': h2_inout.assign(r=h2_inout.r.map(rmap)).loc[
            (h2_inout['*'].str.lower() == 'in') & (h2_inout.t==year)
        ].rename(columns={'allh':'h'}).groupby(['r','h']).Value.sum(),
        'stor_discharge': -h2_inout.assign(r=h2_inout.r.map(rmap)).loc[
            (h2_inout['*'].str.lower() == 'out') & (h2_inout.t==year)
        ].rename(columns={'allh':'h'}).groupby(['r','h']).Value.sum(),
    }
    dfall = pd.concat(dfall, axis=1).fillna(0)
    dfall['stor_dispatch'] = dfall['stor_discharge'] + dfall['stor_charge']
    ### Broadcast representative to actual
    dffull = dfall.unstack('r').reindex(hmap_myr.h)
    dffull.index = (
        hmap_myr.rename(columns={'actual_period':'actualszn','actual_h':'allh'})
        .set_index(['actualszn','h']).index)
    dffull = dffull.reorder_levels(['r',None],axis=1)
    ### Include storage level
    if len(h2_storage_level):
        storstack = (
            h2_storage_level.assign(r=h2_storage_level.r.map(rmap))
            .loc[(h2_storage_level.t==year)]
            .rename(columns={'allh':'h'})
            .groupby(['r','actualszn','h']).Value.sum()
            .rename('stor_level').to_frame().unstack('r')
            .reorder_levels(['r',None], axis=1)
        )
    else:
        storstack = (
            h2_storage_level_szn.assign(r=h2_storage_level_szn.r.map(rmap))
            .loc[(h2_storage_level_szn.t==year)]
            .groupby(['r','actualszn' ]).Value.sum()
            .rename('stor_level').to_frame().unstack('r')
            .reorder_levels(['r',None], axis=1)
            .reindex(hmap_myr.actual_period.values).fillna(0)
        )
    dffull[storstack.columns] = storstack.values
    dffull.columns = dffull.columns.rename(['r','datum'])
    ## Convert to kT
    dffull /= 1000

    ### Don't chunk it
    dfchunk = dffull.fillna(0).round(3).copy()
    timeindex = (hmap_myr.actual_h.map(h2timestamp)).values

    ###### Plot it
    rows = {
        'production':0,
        'stor_charge':1,
        'stor_discharge':2,
        'usage':3,
        'stor_level':4,
    }
    ylabels = {
        'production':'Production\n[kT/day]',
        'stor_charge':'Injection\n[kT/day]',
        'stor_discharge':'Withdrawal\n[kT/day]',
        'usage':'Turbine use\n[kT/day]',
        'stor_level':'Reservoir\nlevel [kT]',
    }
    scale = {k: (24 if 'day' in v else 1) for k,v in ylabels.items()}
    colors = plots.rainbowmapper(dfchunk.columns.get_level_values('r').unique())
    if len(colors) == 1:
        colors[list(colors.keys())[0]] = 'C0'

    ###### Plot it
    plt.close()
    f,ax = plt.subplots(len(rows), 1, sharex=True, sharey=False, figsize=figsize)
    ### Data
    for datum, row in rows.items():
        df = dfchunk.xs(datum, axis=1, level='datum') * scale[datum]
        df.index = timeindex
        order = df.columns
        dfplot = df[order[::-1]].cumsum(axis=1)[order]
        dfplot.plot.area(
            ax=ax[row], color=colors, stacked=False, legend=(not row),
            lw=0, alpha=1,
        )
        ax[row].set_ylabel(ylabels[datum])
    ###### Formatting
    ax[0].legend(
        loc='upper left', bbox_to_anchor=(1,1), frameon=False,
        columnspacing=0.5, handletextpad=0.3, handlelength=0.7,
        fontsize=12,
    )
    ### Scales
    ymax = (dfchunk.groupby(axis=1, level='datum').sum()
            [['production','stor_discharge']].sum(axis=1).max()) * 24
    ymin = (dfchunk.groupby(axis=1, level='datum').sum()
            [['usage','stor_charge']].sum(axis=1).min()) * 24
    scalerows = [v for k,v in rows.items() if 'level' not in k]
    for row in scalerows:
        ax[row].set_ylim(ymin, ymax)
        ax[row].axhline(0, c='k', ls=':', lw=0.5)
        if grid:
            ax[row].grid(which='minor', axis='x', c='C7', ls=':', lw=grid)
    ax[0].set_xlim(
        df.index[0].strftime('%Y-%m-%d'),
        df.index[-1].strftime('%Y-%m-%d') + ' 23:59'
    )
    plots.despine(ax)
    
    return f, ax


def plot_interface_flows(
        case, year=2050,
        source='pras', iteration='last', samples=None,
        level='transreg', weatheryear=2012, decimals=0,
        flowcolors={'forward':'C0', 'reverse':'C3'},
        onlydata=False,
    ):
    """
    """
    fulltimeindex = functions.make_fulltimeindex()
    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')

    if source.lower() == 'pras':
        infile = sorted(glob(
            os.path.join(
                case, 'ReEDS_Augur', 'PRAS',
                f"PRAS_{year}i{'*' if iteration in ['last','latest','final'] else iteration}"
                + (f'-{samples}' if samples is not None else '')
                + '-flow.h5')
        ))[-1]
        dfflow = read_pras_results(infile).set_index(fulltimeindex)
        ## Filter out AC/DC converters from scenarios with VSC
        dfflow = dfflow[[c for c in dfflow if '"DC_' not in c]].copy()
        ## Normalize the interface names
        renamer = {i: '→'.join(i.replace('"','').split(' => ')) for i in dfflow}
    else:
        raise NotImplementedError(f"source must be 'pras' but is '{source}'")

    ### Group by hierarchy level
    df = dfflow.rename(columns=renamer)
    aggcols = {c: '→'.join([hierarchy[level][i] for i in c.split('→')]) for c in df}
    df = df.rename(columns=aggcols).groupby(axis=1, level=0).sum()
    df = df[[c for c in df if c.split('→')[0] != c.split('→')[1]]].copy()
    ### Keep only a single direction
    dflevel = {}
    for c in df:
        r, rr = c.split('→')
        ## Sort alphabetically
        if r < rr:
            dflevel[f'{r}→{rr}'] = dflevel.get(f'{r}→{rr}', 0) + df[c]
        else:
            dflevel[f'{rr}→{r}'] = dflevel.get(f'{rr}→{r}', 0) - df[c]
    dflevel = pd.concat(dflevel, axis=1)
    ## Redefine the dominant direction as "forward"
    toswap = {}
    for c in dflevel:
        if dflevel[c].mean() < 0:
            dflevel[c] *= -1
            toswap[c] = '→'.join(c.split('→')[::-1])
    dfplot = dflevel.rename(columns=toswap)
    if onlydata:
        return dfplot

    ###### Plot it
    ## Sort interfaces by fraction of flow that is "forward"
    forward_fraction = (
        dfplot.clip(lower=0).sum() / dfplot.abs().sum()
    ).sort_values(ascending=False)
    interfaces = forward_fraction.index
    nrows = len(interfaces)
    if nrows == 0:
        raise NotImplementedError(
            "No interfaces to plot (expected if you're only modeling one hierarchy level)")
    elif nrows == 1:
        coords = {'distribution':{interfaces[0]: 0}, 'profile':{interfaces[0]: 1}}
    else:
        coords = {
            'distribution': {interface: (row,0) for row, interface in enumerate(interfaces)},
            'profile': {interface: (row,1) for row, interface in enumerate(interfaces)},
        }
    index = dfplot.loc[str(weatheryear)].index
    plt.close()
    f,ax = plt.subplots(
        nrows, 2, figsize=(10,nrows*0.5), sharex='col', sharey='row',
        gridspec_kw={'width_ratios':[0.06,1], 'wspace':0.1},
    )
    for interface in interfaces:
        ### Hourly
        ## Positive
        ax[coords['profile'][interface]].fill_between(
            index,
            dfplot.loc[str(weatheryear)][interface].clip(lower=0),
            color=flowcolors['forward'], lw=0.1, label='Forward')
        ## Negative
        ax[coords['profile'][interface]].fill_between(
            index,
            dfplot.loc[str(weatheryear)][interface].clip(upper=0),
            color=flowcolors['reverse'], lw=0.1, label='Reverse')
        ### Distribution
        ## Positive
        ax[coords['distribution'][interface]].fill_between(
            np.linspace(0,1,len(dfplot)),
            dfplot[interface].sort_values(ascending=False).clip(lower=0),
            color=flowcolors['forward'], lw=0,
        )
        ## Negative
        ax[coords['distribution'][interface]].fill_between(
            np.linspace(0,1,len(dfplot)),
            dfplot[interface].sort_values(ascending=False).clip(upper=0),
            color=flowcolors['reverse'], lw=0,
        )
        ### Formatting
        ax[coords['profile'][interface]].axhline(0,c='C7',ls=':',lw=0.5)
        ax[coords['distribution'][interface]].set_yticks([0])
        ax[coords['distribution'][interface]].set_yticklabels([])
        ax[coords['distribution'][interface]].set_ylabel(
            f'{interface}\n({forward_fraction[interface]*100:.{decimals}f}% →)',
            rotation=0, ha='right', va='center', fontsize='medium')
    ### Formatting
    ax[coords['distribution'][interfaces[-1]]].set_xticks([0,0.5,1])
    ax[coords['distribution'][interfaces[-1]]].set_xticklabels([0,'','100%'])
    ax[coords['profile'][interfaces[0]]].annotate(
        'Forward ', (0.5,1), xycoords='axes fraction', ha='right', annotation_clip=False,
        weight='bold', fontsize='large', color=flowcolors['forward'],
    )
    ax[coords['profile'][interfaces[0]]].annotate(
        ' Reverse', (0.5,1), xycoords='axes fraction', ha='left', annotation_clip=False,
        weight='bold', fontsize='large', color=flowcolors['reverse'],
    )
    ax[coords['profile'][interfaces[0]]].annotate(
        f'{os.path.basename(case)}\nsystem year: {year}i{iteration}\nweather year: {weatheryear}',
        (1,1), xycoords='axes fraction', ha='right', annotation_clip=False,
    )
    ## Full time range
    ax[coords['profile'][interfaces[-1]]].set_xlim(index[0]-pd.Timedelta('1D'), index[-1])
    ax[coords['profile'][interfaces[-1]]].xaxis.set_major_locator(mpl.dates.MonthLocator())
    ax[coords['profile'][interfaces[-1]]].xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
    plots.despine(ax)
    return f, ax, dfplot


def plot_storage_soc(
        case, year=2050,
        source='pras', iteration='last', samples=None,
        level='transgrp',
        onlydata=False,
    ):
    """Plot storage state of charge from PRAS"""
    fulltimeindex = functions.make_fulltimeindex()
    hierarchy = pd.read_csv(
        os.path.join(case,'inputs_case','hierarchy.csv')
    ).rename(columns={'*r':'r'}).set_index('r')

    ### Get storage state of charge
    if source.lower() == 'pras':
        infile = sorted(glob(
            os.path.join(
                case, 'ReEDS_Augur', 'PRAS',
                f"PRAS_{year}i{'*' if iteration in ['last','latest','final'] else iteration}"
                + (f'-{samples}' if samples is not None else '')
                + '-energy.h5')
        ))[-1]
        _iteration = int(os.path.basename(infile).split('-')[0].split('_')[1].split('i')[1])
        dfenergy = read_pras_results(infile).set_index(fulltimeindex)
    else:
        raise NotImplementedError(f"source must be 'pras' but is '{source}'")
    ## Sum by hierarchy level
    dfenergy_r = (
        dfenergy
        .rename(columns={c: c.split('|')[1] for c in dfenergy.columns})
        .groupby(axis=1, level=0).sum()
    )
    dfenergy_agg = (
        dfenergy_r.rename(columns=hierarchy[level])
        .groupby(axis=1, level=0).sum()
    )
    # dfheadspace_MWh = dfenergy_agg.max() - dfenergy_agg
    # dfheadspace_frac = dfheadspace_MWh / dfenergy_agg.max()
    dfsoc_frac = dfenergy_agg / dfenergy_agg.max()
    if onlydata:
        return dfsoc_frac

    ### Get stress periods
    set_szn = pd.read_csv(
        os.path.join(case, 'inputs_case', f'stress{year}i{_iteration}', 'set_szn.csv')
    ).rename(columns={'*szn':'szn'})
    set_szn['datetime'] = set_szn.szn.map(h2timestamp)
    set_szn['date'] = set_szn.datetime.map(lambda x: x.strftime('%Y-%m-%d'))
    set_szn['year'] = set_szn.datetime.map(lambda x: x.year)

    ### Plot it
    years = range(dfenergy.index.year.min(), dfenergy.index.year.max()+1)
    colors = plots.rainbowmapper(dfsoc_frac.columns)
    plt.close()
    f,ax = plt.subplots(
        len(years), 1, sharey=True, figsize=(13.33,8),
        gridspec_kw={'hspace':1.0},
    )
    for row, y in enumerate(years):
        df = dfsoc_frac.loc[str(y)]
        for region, color in colors.items():
            (df-1)[region].plot.area(
                ax=ax[row], stacked=False, legend=False, lw=0.1, color=color, alpha=0.8)
            # ax[row].fill_between(
            #     df.index, df[region].values, 1, lw=0.1, color=color, label=region, alpha=0.8,
            # )
        for tstart in set_szn.loc[set_szn.year==y, 'datetime'].values:
            ax[row].axvspan(tstart, tstart + pd.Timedelta('1D'), lw=0, color='k', alpha=0.15)
        ax[row].set_ylim(-1,0)
        # ax[row].set_ylim(0,1)
    ax[0].set_yticks([])
    # ax[-1].xaxis.set_minor_locator(mpl.dates.DayLocator())
    ax[0].legend(
        loc='upper left', bbox_to_anchor=(1,1),
        frameon=False, columnspacing=0.5, handlelength=0.7, handletextpad=0.3,
        title=f'Storage\nstate of charge\nby {level},\n{year}i{_iteration}\n[fraction]',
        title_fontsize=12,
    )
    # ax[0].annotate(
    #     f'{os.path.basename(case)}\nsystem year: {year}i{_iteration}',
    #     (1,1.2), xycoords='axes fraction', ha='right', annotation_clip=False,
    # )
    plots.despine(ax, left=False)
    return f, ax, dfsoc_frac
