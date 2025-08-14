#%% Imports
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import os
import sys
import argparse
import subprocess as sp
import platform
from glob import glob
from tqdm import tqdm
import traceback
import cmocean
from pptx.util import Inches
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
from reeds import plots
from reeds import reedsplots
from reeds.results import SLIDE_HEIGHT, SLIDE_WIDTH
from bokehpivot.defaults import DEFAULT_DOLLAR_YEAR, DEFAULT_PV_YEAR, DEFAULT_DISCOUNT_RATE

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plots.plotparams()

#%% Argument inputs
parser = argparse.ArgumentParser(
    description='Compare multiple ReEDS cases',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    'caselist', type=str, nargs='+',
    help=('space-delimited list of cases to plot, OR shared casename prefix, '
          'OR csv file of cases. The first case is treated as the base case '
          'unless a different one is provided via the --basecase/-b argument.'))
parser.add_argument(
    '--casenames', '-n', type=str, default='',
    help='comma-delimited list of shorter case names to use in plots')
parser.add_argument(
    '--titleshorten', '-s', type=str, default='',
    help='characters to cut from start of case name (only used if no casenames)')
parser.add_argument(
    '--startyear', '-t', type=int, default=2020,
    help='First year to show')
parser.add_argument(
    '--sharey', '-y', action='store_true',
    help='Use same y-axis scale for absolute and difference plots')
parser.add_argument(
    '--basecase', '-b', type=str, default='',
    help='Substring of case path to use as default (if empty, uses first case in list)')
parser.add_argument(
    '--skipbp', '-p', action='store_true',
    help='flag to prevent bokehpivot report from being generated')
parser.add_argument(
    '--bpreport', '-r', type=str, default='standard_report_reduced',
    help='which bokehpivot report to generate')
parser.add_argument(
    '--detailed', '-d', action='store_true',
    help='Include more detailed plots')
parser.add_argument(
    '--forcemulti', '-m', action='store_true',
    help='Always use multi-case plots (even for 2 cases)')
parser.add_argument(
    '--lesslabels', '-l', action='count',
    help='Add less value labels to plots')
parser.add_argument(
    '--nowrap', '-w', action='store_true',
    help="Don't wrap subplot titles")

args = parser.parse_args()
caselist = args.caselist
casenames = args.casenames
try:
    titleshorten = int(args.titleshorten)
except ValueError:
    titleshorten = len(args.titleshorten)
basecase_in = args.basecase
startyear = args.startyear
sharey = True if args.sharey else 'row'
bpreport = args.bpreport
skipbp = args.skipbp
detailed = args.detailed
forcemulti = args.forcemulti
lesslabels = args.lesslabels
nowrap = args.nowrap
interactive = False

#%% Inputs for testing
# reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# caselist = [os.path.join(reeds_path,'postprocessing','example.csv')]
# casenames = ''
# titleshorten = 0
# startyear = 2020
# sharey = 'row'
# basecase_in = ''
# skipbp = True
# bpreport = 'standard_report_reduced'
# interactive = True
# forcemulti = False
# lesslabels = 0
# nowrap = False
# detailed = False


#%%### Fixed inputs
cmap = cmocean.cm.rain
cmap_diff = plt.cm.RdBu_r
## https://www.whitehouse.gov/wp-content/uploads/2023/11/CircularA-4.pdf
discountrate_social = DEFAULT_DISCOUNT_RATE
## https://www.epa.gov/environmental-economics/scghg
discountrate_scghg = 0.02
assert discountrate_scghg in [0.015, 0.02, 0.025]
central_health = {'cr':'ACS', 'model':'EASIUR'}
reeds_dollaryear = 2004
output_dollaryear = DEFAULT_DOLLAR_YEAR
startyear_notes = DEFAULT_PV_YEAR

colors_social = {
    'CO2': plt.cm.tab20b(4),
    'CH4': plt.cm.tab20b(5),
    'health': plt.cm.tab20b(7),
}

techmap = {
    **{f'upv_{i}':'Utility PV' for i in range(20)},
    **{f'wind-ons_{i}':'Land-based wind' for i in range(20)},
    **{f'wind-ofs_{i}':'Offshore wind' for i in range(20)},
    **dict(zip(['nuclear','nuclear-smr'], ['Nuclear']*20)),
    **dict(zip(
        ['gas-cc_re-cc','gas-ct_re-ct','re-cc','re-ct',
         'gas-cc_h2-ct','gas-ct_h2-ct','h2-cc','h2-ct',],
        ['H2 turbine']*20)),
    **{f'battery_{i}':'Battery/PSH' for i in range(20)}, **{'pumped-hydro':'Battery/PSH'},
    # **dict(zip(
    #     ['coal-igcc', 'coaloldscr', 'coalolduns', 'gas-cc', 'gas-ct', 'coal-new', 'o-g-s',],
    #     ['Fossil']*20)),
    **dict(zip(
        ['gas-cc_gas-cc-ccs_mod','gas-cc_gas-cc-ccs_max','gas-cc-ccs_mod','gas-cc-ccs_max',
         'gas-cc_gas-cc-ccs_mod','coal-igcc_coal-ccs_mod','coal-new_coal-ccs_mod',
        'coaloldscr_coal-ccs_mod','coalolduns_coal-ccs_mod','cofirenew_coal-ccs_mod',
        'cofireold_coal-ccs_mod','gas-cc_gas-cc-ccs_max','coal-igcc_coal-ccs_max',
        'coal-new_coal-ccs_max','coaloldscr_coal-ccs_max','coalolduns_coal-ccs_max',
        'cofirenew_coal-ccs_max','cofireold_coal-ccs_max',],
        ['Fossil+CCS']*50)),
    **dict(zip(['dac','beccs_mod','beccs_max'],['CO2 removal']*20)),
    **dict(zip(
        ['gas-cc', 'gas-ct', ],
        ['Gas']*20)),
    **dict(zip(
        ['coal-igcc', 'coaloldscr', 'coalolduns', 'coal-new', 'o-g-s',],
        ['Other Fossil']*20)),
}

maptechs = [
    'Utility PV',
    'Land-based wind',
    'Offshore wind',
    'Nuclear',
    'Battery/PSH',
    'Fossil+CCS',
    'Fossil',
    'Gas',
]

plotdiffvals = [
    'Generation (TWh)',
    'Capacity (GW)',
    'New Annual Capacity (GW)',
    'Annual Retirements (GW)',
    'Firm Capacity (GW)',
    'Curtailment Rate',
    'Transmission (GW-mi)',
    'Transmission (PRM) (GW-mi)',
    'Bulk System Electricity Pric',
    'National Average Electricity',
    'Present Value of System Cost',
    'NEUE (ppm)',
    'Runtime (hours)',
    'Runtime by year (hours)',
]
onlytechs = None
i_plots = ['wind-ons','upv','battery','h2-ct','nuclear','gas-cc-ccs','coal-ccs',]
## mapdiff: 'cap' or 'gen_ann'
mapdiff = 'cap'



#%%### Functions
def plot_bars_abs_stacked(
        dfplot, basecase, colors, ax, col=0,
        net=True, label=True, ypad=0.02, fontsize=9,
    ):
    """
    * ax must have at least 2 rows
    * dfplot must have cases as rows and stacked bar elements (matching colors) as cols
    """
    ## Absolute and difference
    if isinstance(basecase, str):
        dfdiff = dfplot - dfplot.loc[basecase]
    elif isinstance(basecase, list):
        dfdiff = dfplot - dfplot.loc[basecase].values
    elif isinstance(basecase, dict):
        dfdiff = dfplot - dfplot.loc[basecase.values()].values

    for (row, df) in enumerate([dfplot, dfdiff]):
        plots.stackbar(df=df, ax=ax[row,col], colors=colors, net=(net or row), width=0.8)
        ymin, ymax = ax[row,col].get_ylim()
        _ypad = (ymax - ymin) * ypad
        ## label net value
        if label:
            for x, case in enumerate(df.index):
                val = df.loc[case].sum()
                if np.around(val, 0) == 0:
                    continue
                ax[row,col].annotate(
                    f'{val:.0f}', (x, val - _ypad), ha='center', va='top',
                    color='k', size=fontsize,
                    path_effects=[pe.withStroke(linewidth=2.0, foreground='w', alpha=0.7)],
                )
    ## Legend info
    legend_handles = [
        mpl.patches.Patch(facecolor=colors[i], edgecolor='none', label=i)
        for i in (colors if isinstance(colors, dict) else colors.index) if i in dfplot
    ]
    return legend_handles


#%%### Procedure
#%% Parse arguments
cases, colors, basecase, basemap = reeds.results.parse_caselist(
    caselist,
    casenames,
    basecase_in,
    titleshorten,
)
maxlength = max([len(c) for c in cases])

## Arrange the maps
nrows, ncols, coords = plots.get_coordinates(cases, aspect=2)

#%% Create output folder
firstcasepath = list(cases.values())[0]
outpath = os.path.join(firstcasepath, 'outputs', 'comparisons')
os.makedirs(outpath, exist_ok=True)
## Remove disallowed characters and clip filename to max length
max_filename_length = 250
savename = os.path.join(
    outpath,
    (f"results-{','.join(cases.keys())}"
     .replace(':','').replace('/','').replace(' ','').replace('\\n','').replace('\n','')
     [:max_filename_length-len('.pptx')]) + '.pptx'
)
print(f'Saving results to {savename}')

#%% Create bokehpivot report as subprocess
if not skipbp:
    start_str = 'start ' if platform.system() == 'Windows' else ''
    bp_path = f'{reeds_path}/postprocessing/bokehpivot'
    bp_py_file = f'{bp_path}/reports/interface_report_model.py'
    report_path = f'{bp_path}/reports/templates/reeds2/{bpreport}.py'
    bp_outpath = f'{outpath}/{bpreport}-diff-multicase'
    add_diff = 'Yes'
    auto_open = 'Yes'
    bp_colors = pd.read_csv(f'{bp_path}/reeds_scenarios.csv')['color'].tolist()
    bp_colors = bp_colors*10 #Up to 200 scenarios
    bp_colors = bp_colors[:len(cases.keys())]
    df_scenarios = pd.DataFrame({'name':cases.keys(), 'color':bp_colors, 'path':cases.values()})
    scenarios_path = f'{outpath}/scenarios.csv'
    df_scenarios.to_csv(scenarios_path, index=False)
    call_str = (
        f'{start_str}python "{bp_py_file}" "ReEDS 2.0" "{scenarios_path}" all ' +
        f'{add_diff} "{basecase}" "{report_path}" "html,excel" one "{bp_outpath}" {auto_open}'
    )
    sp.Popen(call_str, shell=True)

#%%### Load data
#%% Shared
sw = reeds.io.get_switches(cases[basecase])
scalars = reeds.io.get_scalars(cases[basecase])
phaseout_trigger = float(scalars.co2_emissions_2022) * float(sw.GSw_TCPhaseout_trigger_f)

inflatable = reeds.io.get_inflatable(os.path.join(
    reeds_path,'inputs','financials','inflation_default.csv'))
inflator = inflatable[reeds_dollaryear, output_dollaryear]

scghg = pd.read_csv(
    os.path.join(reeds_path, 'postprocessing', 'plots', 'scghg_annual.csv'),
    comment='#', thousands=','
).rename(columns={
    'gas':'e',
    'emission.year':'t',
    '2.5% Ramsey':'2020_2.5%',
    '2.0% Ramsey':'2020_2.0%',
    '1.5% Ramsey':'2020_1.5%',
}).set_index(['e','t'])
scghg_central = (
    scghg[f'2020_{discountrate_scghg*100:.1f}%'].unstack('e')
    * inflatable[2020, output_dollaryear]
)

#%% Colors
bokehcostcolors = pd.read_csv(
    os.path.join(
        reeds_path,'postprocessing','bokehpivot','in','reeds2','cost_cat_style.csv'),
    index_col='order').squeeze(1)
bokehcostcolors = bokehcostcolors.loc[~bokehcostcolors.index.duplicated()]

colors_time = pd.read_csv(
    os.path.join(
        reeds_path,'postprocessing','bokehpivot','in','reeds2','process_style.csv'),
    index_col='order',
).squeeze(1)

bokehcolors = pd.read_csv(
    os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_style.csv'),
    index_col='order').squeeze(1)

tech_map = pd.read_csv(
    os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','tech_map.csv'),
    index_col='raw').squeeze(1)
    
bokehcolors = pd.concat([
    bokehcolors.loc['smr':'electrolyzer'],
    pd.Series('#D55E00', index=['dac'], name='color'),
    bokehcolors.loc[:'Canada'],
])

bokehcolors['canada'] = bokehcolors['Canada']

techcolors = {
    'gas-cc_gas-cc-ccs':bokehcolors['gas-cc-ccs_mod'],
    'cofire':bokehcolors['biopower'],
    'gas-cc':'#5E1688',
    'gas-cc-ccs':'#9467BD',
}
for i in bokehcolors.index:
    if i in techcolors:
        pass
    elif i in bokehcolors.index:
        techcolors[i] = bokehcolors[i]
    else:
        raise Exception(i)

techcolors = {i: techcolors[i] for i in bokehcolors.index}

trtype_map = pd.read_csv(
    os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_map.csv'),
    index_col='raw')['display']
colors_trans = pd.read_csv(
    os.path.join(reeds_path,'postprocessing','bokehpivot','in','reeds2','trtype_style.csv'),
    index_col='order')['color']

#%% Parse excel report sheet names
val2sheet = reeds.io.get_report_sheetmap(cases[basecase])

#%% Read input files
renametechs = {
    'h2-cc_upgrade':'h2-cc',
    'h2-ct_upgrade':'h2-ct',
    'gas-cc-ccs_mod_upgrade':'gas-cc-ccs_mod',
    'coal-ccs_mod_upgrade':'coal-ccs_mod',
}
dictin_sw = {case: reeds.io.get_switches(cases[case]) for case in cases}

hierarchy = {case: reeds.io.get_hierarchy(cases[case]) for case in cases}

dictin_error = {}
for case in tqdm(cases, desc='system cost error'):
    dictin_error[case] = reeds.io.read_output(cases[case], 'error_check').set_index('*').squeeze(1)

dictin_cap = {}
for case in tqdm(cases, desc='national capacity'):
    dictin_cap[case] = reeds.io.read_report(cases[case], 'Capacity (GW)', val2sheet)
    ### Simplify techs
    dictin_cap[case].tech = dictin_cap[case].tech.map(lambda x: renametechs.get(x,x))
    dictin_cap[case] = (
        dictin_cap[case].groupby(['tech','year'], as_index=False)
        ['Capacity (GW)'].sum())
    dictin_cap[case] = dictin_cap[case].loc[
        ~dictin_cap[case].tech.isin(['electrolyzer','smr','smr-ccs','dac'])].copy()

dictin_gen = {}
for case in tqdm(cases, desc='national generation'):
    dictin_gen[case] = reeds.io.read_report(cases[case], 'Generation (TWh)', val2sheet)
    ### Simplify techs
    dictin_gen[case].tech = dictin_gen[case].tech.map(lambda x: renametechs.get(x,x))
    dictin_gen[case] = (
        dictin_gen[case].groupby(['tech','year'], as_index=False)
        ['Generation (TWh)'].sum())

costcat_rename = {
    'CO2 Spurline':'CO2 T&S Capex',
    'CO2 Pipeline':'CO2 T&S Capex',
    'CO2 Storage':'CO2 T&S Capex',
    'CO2 Spurline FOM':'CO2 T&S O&M',
    'CO2 Pipeline FOM':'CO2 T&S O&M',
    'CO2 Incentive Payments':'CCS Incentives',
    'Capital': 'Gen & Stor Capex',
    'O&M': 'Gen & Stor O&M',
    'CO2 Network':'CO2 T&S Capex',
    'CO2 Incentives':'CCS Incentives',
    'CO2 FOM':'CO2 T&S O&M',
    'CO2 Capture':'CO2 T&S Capex',
    'H2 Fuel':'Fuel',
    'H2 VOM':'H2 Prod O&M',
}
dictin_npv = {}
for case in tqdm(cases, desc='NPV of system cost'):
    dictin_npv[case] = (
        reeds.io.read_report(cases[case], 'Present Value of System Cost', val2sheet)
        .set_index('cost_cat')['Discounted Cost (Bil $)']
    )
    dictin_npv[case].index = pd.Series(dictin_npv[case].index).replace(costcat_rename)
    dictin_npv[case] = dictin_npv[case].groupby(level=0, sort=False).sum()

dictin_scoe = {}
for case in tqdm(cases, desc='SCOE'):
    dictin_scoe[case] = reeds.io.read_report(cases[case], 'National Average Electricity', val2sheet)
    dictin_scoe[case].cost_cat = dictin_scoe[case].cost_cat.replace(
        {**costcat_rename,**{'CO2 Incentives':'CCS Incentives'}})
    dictin_scoe[case] = (
        dictin_scoe[case].groupby(['cost_cat','year'], sort=False, as_index=False)
        ['Average cost ($/MWh)'].sum())

dictin_syscost = {}
for case in tqdm(cases, desc='annual system cost'):
    dictin_syscost[case] = reeds.io.read_report(cases[case], 'Undiscounted Annualized Syst', val2sheet)
    dictin_syscost[case].cost_cat = dictin_syscost[case].cost_cat.replace(
        {**costcat_rename,**{'CO2 Incentives':'CCS Incentives'}})
    dictin_syscost[case] = (
        dictin_syscost[case].groupby(['cost_cat','year'], sort=False)
        ['Cost (Bil $)'].sum().unstack('cost_cat'))

dictin_emissions = {}
for case in tqdm(cases, desc='national emissions'):
    dictin_emissions[case] = (
        reeds.io.read_output(cases[case], 'emit_nat', valname='ton')
    )
    if int(dictin_sw[case].get('GSw_Precombustion', 1)):
        dictin_emissions[case] = dictin_emissions[case].groupby(['e','t']).ton.sum().unstack('e')
    else:
        dictin_emissions[case] = (
            dictin_emissions[case]
            .set_index(['etype','e','t'])
            .loc['combustion']
            .groupby(['e','t']).ton.sum()
            .unstack('e')
        )

dictin_trans = {}
for case in tqdm(cases, desc='national transmission'):
    dictin_trans[case] = reeds.io.read_report(cases[case], 'Transmission (GW-mi)')

dictin_trans_r = {}
for case in tqdm(cases, desc='regional transmission'):
    dictin_trans_r[case] = reeds.io.read_output(cases[case], 'tran_out', valname='MW')
    for _level in ['interconnect','transreg','transgrp','st']:
        dictin_trans_r[case][f'inter_{_level}'] = (
            dictin_trans_r[case].r.map(hierarchy[case][_level])
            != dictin_trans_r[case].rr.map(hierarchy[case][_level])
        ).astype(int)

dictin_cap_r = {}
for case in tqdm(cases, desc='regional capacity'):
    try:
        dictin_cap_r[case] = reeds.io.read_output(cases[case], 'cap', valname='MW')
    except KeyError:
        dictin_cap_r[case] = reeds.io.read_output(cases[case], 'cap_out', valname='MW')
    ### Simplify techs
    dictin_cap_r[case].i = dictin_cap_r[case].i.map(lambda x: renametechs.get(x,x))
    dictin_cap_r[case].i = dictin_cap_r[case].i.str.lower().map(lambda x: techmap.get(x,x))
    dictin_cap_r[case] = dictin_cap_r[case].groupby(['i','r','t'], as_index=False).MW.sum()

dictin_cap_firm = {}
for case in tqdm(cases, desc='firm capacity'):
    dictin_cap_firm[case] = reeds.io.read_output(cases[case], 'cap_firm', valname='MW')
    ### Simplify techs
    dictin_cap_firm[case].i = reedsplots.simplify_techs(dictin_cap_firm[case].i)
    dictin_cap_firm[case] = dictin_cap_firm[case].groupby(['i','r','ccseason','t'], as_index=False).MW.sum()

dictin_runtime = {}
for case in tqdm(cases, desc='runtime'):
    dictin_runtime[case] = (
        reeds.io.read_report(cases[case], 'Runtime by year (hours)', val2sheet)
        .drop(columns='Net Level processtime')
    )

dictin_neue = {}
for case in tqdm(cases, desc='NEUE'):
    infiles = sorted(glob(os.path.join(cases[case],'outputs','neue_*.csv')))
    if not len(infiles):
        continue
    df = {}
    for f in infiles:
        y, i = [int(s) for s in os.path.basename(f).strip('neue_.csv').split('i')]
        df[y,i] = pd.read_csv(f)
        df[y,i] = df[y,i].loc[
            (df[y,i].level=='country') & (df[y,i].metric=='sum'),
            'NEUE_ppm'
        ].iloc[0]
    df = (
        pd.Series(df, name='NEUE [ppm]').rename_axis(['t','iteration'])
        .sort_index().reset_index()
        .drop_duplicates(subset='t', keep='last')
        .set_index('t')['NEUE [ppm]']
    )
    dictin_neue[case] = df

### Model years and discount rates
years = {}
yearstep = {}
for case in cases:
    years[case] = sorted(dictin_cap[case].year.astype(int).unique())
    years[case] = [y for y in years[case] if y >= startyear]
    yearstep[case] = years[case][-1] - years[case][-2]
lastyear = max(years[case])
## Years for which to add data notes
startyear_sums = 2023
allyears = range(startyear_sums,lastyear+1)
noteyears = [2035, 2050]
if all([lastyear < y for y in noteyears]):
    noteyears = [lastyear]
startyear_growth = 2035

discounts = pd.Series(
    index=range(startyear_notes,lastyear+1),
    data=[1/(1+discountrate_social)**(y-startyear_notes)
          for y in range(startyear_notes,lastyear+1)]
).rename_axis('t')

### Health impacts
dictin_health = {}
dictin_health_central = {}
dictin_health_central_mort = {}
for case in tqdm(cases, desc='health'):
    try:
        dictin_health[case] = (
            reeds.io.read_output(cases[case], 'health_damages_caused_r.csv')
            .groupby(['year','pollutant','model','cr']).sum()
        )
        dictin_health_central[case] = (
            dictin_health[case]
            .xs(central_health['cr'], level='cr')
            .xs(central_health['model'], level='model')
            .groupby('year').sum()
            ['damage_$']
            ### Inflate from reeds_dollaryear (2004) to bokeh output_dollaryear (2021)
            * inflator
            ### Convert to $B
            / 1e9
        )
        dictin_health_central_mort[case] = (
            dictin_health[case]
            .xs(central_health['cr'], level='cr')
            .xs(central_health['model'], level='model')
            .groupby('year').sum()
            ['mortality']
        )
    except (FileNotFoundError, KeyError) as err:
        print(f'Health impacts error for {case}: {err}')
        dictin_health_central[case] = (
            pd.Series(np.nan, index=years[case], name='damage_$')
            .rename_axis('year')
        )
        dictin_health_central_mort[case] = (
            pd.Series(np.nan, index=years[case], name='mortality')
            .rename_axis('year')
        )


#%% Detailed inputs
if detailed:
    ### Timeslice generation by region
    dictin_gen_h = {}
    for case in tqdm(cases, desc='gen_h'):
        dictin_gen_h[case] = reeds.io.read_output(cases[case], 'gen_h', valname='GW')
        dictin_gen_h[case].GW /= 1e3
        dictin_gen_h[case].i = reedsplots.simplify_techs(dictin_gen_h[case].i)
        dictin_gen_h[case] = dictin_gen_h[case].groupby(['i','r','h','t'], as_index=False).GW.sum()
        ## Separate charge and discharge
        dictin_gen_h[case].loc[
            (dictin_gen_h[case].i.str.startswith('battery')
            | dictin_gen_h[case].i.str.startswith('pumped-hydro'))
            & (dictin_gen_h[case].GW < 0),
            'i'
        ] += '|charge'
        dictin_gen_h[case].loc[
            (dictin_gen_h[case].i.str.startswith('battery')
            | dictin_gen_h[case].i.str.startswith('pumped-hydro'))
            & (~dictin_gen_h[case].i.str.endswith('|charge')),
            'i'
        ] += '|discharge'

    ### Aggregated generation by region
    dictin_gen_h_twh = {}
    for case in tqdm(dictin_gen_h):
        numhours = pd.read_csv(
            os.path.join(cases[case],'inputs_case','numhours.csv'),
        ).rename(columns={'*h':'h'}).set_index('h').squeeze(1)

        dictin_gen_h_twh[case] = dictin_gen_h[case].copy()
        dictin_gen_h_twh[case]['TWh'] = (
            dictin_gen_h_twh[case]['GW'] * dictin_gen_h_twh[case]['h'].map(numhours)
            / 1e3
        ).round(3)

        dictin_gen_h_twh[case] = dictin_gen_h_twh[case].groupby(['t','i']).TWh.sum().unstack('i')

    ### Stress period dispatch
    dictin_gen_h_stress = {}
    for case in tqdm(cases, desc='gen_h_stress'):
        dictin_gen_h_stress[case] = reeds.io.read_output(cases[case], 'gen_h_stress', valname='GW')
        dictin_gen_h_stress[case].GW /= 1e3
        dictin_gen_h_stress[case].i = reedsplots.simplify_techs(dictin_gen_h_stress[case].i)
        ## Separate charge and discharge
        dictin_gen_h_stress[case].loc[dictin_gen_h_stress[case].GW < 0,'i'] += '|charge'
        dictin_gen_h_stress[case].loc[dictin_gen_h_stress[case].i.isin(
            ['battery_4','battery_8','pumped-hydro']),'i'] += '|discharge'

    ### Stress period flows
    dictin_tran_flow_stress = {}
    for case in tqdm(cases, desc='tran_flow_stress'):
        dictin_tran_flow_stress[case] = reeds.io.read_output(
            cases[case], 'tran_flow_stress', valname='GW')
        dictin_tran_flow_stress[case].GW /= 1e3

    ### Stress period load
    dictin_load_stress = {}
    for case in tqdm(cases, desc='load_stress'):
        dictin_load_stress[case] = reeds.io.read_output(cases[case], 'load_stress', valname='GW')
        dictin_load_stress[case].GW /= 1e3

    ### Peak load (for capacity credit)
    distloss = 0.05
    dictin_peak_ccseason = {}
    for case in tqdm(cases, desc='peak_ccseason'):
        dictin_peak_ccseason[case] = pd.read_csv(
            os.path.join(cases[case],'inputs_case','peak_ccseason.csv'),
        ).rename(columns={'*r':'r', 'MW':'GW'})
        dictin_peak_ccseason[case].GW /= (1e3 * (1 - distloss))

    ### Capacity credit PRMTRADE
    dictin_prmtrade = {}
    for case in tqdm(cases, desc='prmtrade'):
        dictin_prmtrade[case] = reeds.io.read_output(cases[case], 'captrade', valname='GW')
        dictin_prmtrade[case].GW /= 1e3


#%%### Plots ######
### Set up powerpoint file
prs = reeds.results.init_pptx()



#%%### Generation capacity lines
aggtechsplot = {
    'Interregional\ntransmission': 'inter_transreg',
    'Land-based\nwind': ['wind-ons'],
    'Offshore\nwind': ['wind-ofs'],
    # 'Wind': ['wind-ons', 'wind-ofs'],
    'Solar': ['upv', 'distpv', 'csp', 'pvb'],
    'Battery': ['battery_{}'.format(i) for i in [2,4,6,8,10]],
    'Pumped\nstorage\nhydro': ['pumped-hydro'],
    # 'Storage': ['battery_{}'.format(i) for i in [2,4,6,8,10]] + ['pumped-hydro'],
    'Hydro, geo, bio': [
        'hydro','geothermal',
        'biopower','lfill-gas','cofire','beccs_mod','beccs'
    ],
    'Nuclear': ['nuclear', 'nuclear-smr'],
    'Hydrogen\nturbine': ['h2-cc', 'h2-cc-upgrade', 'h2-ct', 'h2-ct-upgrade'],
    'Gas CCS': ['gas-cc-ccs_mod'],
    'Coal CCS': ['coal-ccs_mod'],
    # 'Fossil\n(with CCS)': ['gas-cc-ccs_mod','coal-ccs_mod'],
    'Fossil\n(w/o CCS)': ['gas-cc', 'gas-ct', 'o-g-s', 'coal', 'cofire'],
#     'CDR': ['dac', 'beccs'],
#     'H2 production': ['smr', 'smr-ccs', 'electrolyzer'],
}
checktechs = [i for sublist in aggtechsplot.values() for i in sublist]
alltechs = pd.concat(dictin_cap).tech.unique()
printstring = (
    'The following techs are not plotted: '
    + ', '.join([c for c in alltechs if c not in checktechs])
)

offsetstart = {
    'Solar': (15,0),
    'Wind': (15,0), 'Land-based\nwind': (15,0),
}

val = '4_Capacity (GW)'
ycol = 'Capacity (GW)'
techrows, techcols = 2, len(aggtechsplot)//2+len(aggtechsplot)%2
techcoords = dict(zip(
    list(aggtechsplot.keys()),
    [(row,col) for row in range(techrows) for col in range(techcols)]
))

offset = dict()

plt.close()
f,ax = plt.subplots(
    techrows, techcols, sharex=True, sharey=True,
    figsize=(SLIDE_WIDTH, SLIDE_HEIGHT),
    gridspec_kw={'wspace':0.3, 'hspace':0.15},
)
df = {}
for tech in aggtechsplot:
    for case in cases:
        ### Central cases
        if 'transmission' in tech.lower():
            df[tech,case] = dictin_trans_r[case].loc[
                dictin_trans_r[case][aggtechsplot[tech]]==1
            ].groupby('t').MW.sum() / 1e3
        else:
            df[tech,case] = dictin_cap[case].loc[
                dictin_cap[case].tech.isin(aggtechsplot[tech])
            ].groupby('year')[ycol].sum().reindex(years[case]).fillna(0)
        ax[techcoords[tech]].plot(
            df[tech,case].index, df[tech,case].values,
            label=case, color=colors[case], ls='-',
        )
        ### Annotate the last value (with overlaps)
        fincap = df[tech,case].reindex([lastyear]).fillna(0).squeeze()
        ax[techcoords[tech]].annotate(
            ' {:.0f}'.format(fincap),
            (lastyear, fincap+offset.get((tech,case),0)),
            ha='left', va='center',
            color=colors[case], fontsize='small',
            annotation_clip=False,
        )
    ### Formatting
    ax[techcoords[tech]].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(5 if lastyear>2040 else 1))
    ax[techcoords[tech]].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10 if lastyear>2040 else 5))
    ax[techcoords[tech]].annotate(
        tech,
        (0.05,1.0), va='top', ha='left',
        xycoords='axes fraction', 
        fontsize='x-large', weight='bold',)
    ### Annotate the 2020 value
    if len(df[tech,basecase]):
        plots.annotate(
            ax[techcoords[tech]], basecase,
            startyear, offsetstart.get(tech,(10,10)), color='C7',
            arrowprops={'arrowstyle':'-|>', 'color':'C7'})
if len(aggtechsplot) % 2:
    ax[-1,-1].axis('off')
## Legend
handles, labels = ax[-1,0].get_legend_handles_labels()
leg = ax[0,-1].legend(
    handles, labels,
    fontsize='large', frameon=False, 
    loc='center left', bbox_to_anchor=(1.1,-0.075),
    handletextpad=0.3, handlelength=0.7,
    ncol=1,
)
for legobj in leg.legend_handles:
    legobj.set_linewidth(8)
    legobj.set_solid_capstyle('butt')
ax[techcoords[list(aggtechsplot.keys())[0]]].set_xlim(startyear,lastyear)
ax[techcoords[list(aggtechsplot.keys())[0]]].set_ylim(0)
ax[techcoords[list(aggtechsplot.keys())[0]]].set_ylabel('Capacity [GW]', y=-0.075)
# for row in range(techrows):
#     ax[row,0].set_ylabel('Capacity [GW]')
ax[techcoords[list(aggtechsplot.keys())[0]]].set_ylim(0)
# ## Annotate the last value (without overlaps)
# ymax = ax[techcoords[list(aggtechsplot.keys())[0]]].get_ylim()[1]
# df = pd.concat(df, axis=1)
# for tech in aggtechsplot:
#     plots.label_last(
#         df[tech], ax[techcoords[tech]], colors=colors, extend='both',
#         mindistance=ymax*0.05, fontsize='small',
#     )

plots.despine(ax)
plt.draw()
plots.shorten_years(ax[1,0])
### Save it
slide = reeds.results.add_to_pptx('Capacity', prs=prs)
reeds.results.add_textbox(printstring, slide)
if interactive:
    print(printstring)
    plt.show()


#%%### Capacity and generation bars

toplot = {
    'Capacity': {
        'data': dictin_cap,
        'colors':techcolors,
        'columns':'tech',
        'values':'Capacity (GW)',
        'label':'Capacity [GW]'
    },
    'Generation': {
        'data': dictin_gen,
        'colors':techcolors,
        'columns':'tech',
        'values':'Generation (TWh)',
        'label':'Generation [TWh]'
    },
    'Runtime': {
        'data': dictin_runtime,
        'colors':colors_time.to_dict(),
        'columns':'process',
        'values':'processtime',
        'label':'Runtime [hours]'
    },
}
plotwidth = 2.0
figwidth = plotwidth * len(cases)
dfbase = {}
for slidetitle, data in toplot.items():
    plt.close()
    f,ax = plt.subplots(
        2, len(cases), figsize=(figwidth, 6.8),
        sharex=True, sharey=sharey, dpi=None,
    )
    ax[0,0].set_ylabel(data['label'], y=-0.075)
    ax[0,0].set_xlim(2017.5, lastyear+2.5)
    ax[1,0].annotate(
        f'Diff\nfrom\n{basecase}', (0.03,0.03), xycoords='axes fraction',
        fontsize='x-large', weight='bold')
    ###### Absolute
    alltechs = set()
    for col, case in enumerate(cases):
        if case not in data['data']:
            continue
        dfplot = data['data'][case].pivot(index='year', columns=data['columns'], values=data['values'])
        dfplot = (
            dfplot[[c for c in data['colors'] if c in dfplot]]
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all')
        )
        if case == basecase:
            dfbase[slidetitle] = dfplot.copy()
        alltechs.update(dfplot.columns)
        plots.stackbar(df=dfplot, ax=ax[0,col], colors=data['colors'], width=yearstep[case], net=False)
        ax[0,col].set_title(
            (case if nowrap else plots.wraptext(case, width=plotwidth*0.9, fontsize=14)),
            fontsize=14, weight='bold', x=0, ha='left', pad=8,)
        ax[0,col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
        ax[0,col].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(5))


    ### Legend
    handles = [
        mpl.patches.Patch(
            facecolor=data['colors'][i], edgecolor='none',
            label=i.replace('Canada','imports').split('/')[-1]
        )
        for i in data['colors'] if i in alltechs
    ]
    leg = ax[0,-1].legend(
        handles=handles[::-1], loc='upper left', bbox_to_anchor=(1.0,1.0), 
        fontsize='medium', ncol=1,  frameon=False,
        handletextpad=0.3, handlelength=0.7, columnspacing=0.5, 
    )

    ###### Difference
    for col, case in enumerate(cases):
        ax[1,col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
        ax[1,col].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(5))
        ax[1,col].axhline(0,c='k',ls='--',lw=0.75)

        if (case not in data['data']) or (case == basecase):
            continue
        dfplot = data['data'][case].pivot(index='year', columns=data['columns'], values=data['values'])
        dfplot = (
            dfplot
            .round(3).replace(0,np.nan)
            .dropna(axis=1, how='all')
        )
        dfplot = dfplot.subtract(dfbase[slidetitle], fill_value=0)
        dfplot = dfplot[[c for c in data['colors'] if c in dfplot]].copy()
        alltechs.update(dfplot.columns)
        plots.stackbar(df=dfplot, ax=ax[1,col], colors=data['colors'], width=yearstep[case], net=True)

    plots.despine(ax)
    plt.draw()
    plots.shorten_years(ax[1,0])
    ### Save it
    slide = reeds.results.add_to_pptx(
        slidetitle+' stack', prs=prs, width=min(figwidth, SLIDE_WIDTH))
    if interactive:
        plt.show()


#%% Alternate view: Stacks with bars labeled
barwidth = 0.35
labelpad = 0.08
width = 1.6*len(cases) + 0.5
aggstack = {
    **{f'battery_{i}':'Storage' for i in [2,4,6,8,10]},
    **{f'battery_{i}|charge':'Storage|charge' for i in [2,4,6,8,10]},
    **{f'battery_{i}|discharge':'Storage|discharge' for i in [2,4,6,8,10]},
    **{
        'pumped-hydro':'Storage',
        'pumped-hydro|charge':'Storage|charge', 'pumped-hydro|discharge':'Storage|discharge',

        'h2-cc':'H2 turbine', 'h2-ct':'H2 turbine',

        'beccs_mod':'Bio/BECCS',
        'biopower':'Bio/BECCS', 'lfill-gas':'Bio/BECCS', 'cofire':'Bio/BECCS',

        'gas-cc-ccs_mod':'Gas+CCS',
        'coal-ccs_mod':'Coal+CCS',
        'gas-cc':'Gas', 'gas-ct':'Gas', 'o-g-s':'Gas',
        'coal':'Coal',

        'Canada':'Canadian imports', 'canada':'Canadian imports',

        'hydro':'Hydro',
        'geothermal':'Geothermal',

        'csp':'CSP',
        'upv':'PV', 'distpv':'PV',
        'pvb':'PVB',

        'wind-ofs':'Offshore wind',
        'wind-ons':'Land-based wind',

        'nuclear':'Nuclear', 'nuclear-smr':'Nuclear',
    }
}
aggcolors = {
    'Nuclear':'C3',

    'Coal':plt.cm.binary(1.0),
    'Gas':plt.cm.tab20(8),
    'Coal+CCS':'C7',
    'Gas+CCS':plt.cm.tab20(9),

    'Hydro': techcolors['hydro'],
    'Geothermal': techcolors['geothermal'],
    'Canadian imports': techcolors['dr_shed'],

    # 'Bio/BECCS':plt.cm.tab20(4),
    # 'H2 turbine':plt.cm.tab20(5),
    'Bio/BECCS':techcolors['biopower'],
    'H2 turbine':techcolors['h2-ct'],

    'Land-based wind':techcolors['wind-ons'],
    'Offshore wind':techcolors['wind-ofs'],

    'CSP':techcolors['csp'],
    'PV':techcolors['upv'],
    'PVB':techcolors['pvb'],

    # 'Storage':plt.cm.tab20(12),
    # 'Storage|charge':plt.cm.tab20(12),
    # 'Storage|discharge':plt.cm.tab20(12),
    'Storage':techcolors['battery_8'],
    'Storage|charge':techcolors['battery_8'],
    'Storage|discharge':techcolors['battery_8'],
}
aggtechs_disagg = aggstack.copy()
for k,v in aggstack.items():
    if v == 'Storage':
        aggtechs_disagg[k+'|charge'] = 'Storage|charge'
        aggtechs_disagg[k+'|discharge'] = 'Storage|discharge'


if len(cases) <= 4:
    plt.close()
    f,ax = plt.subplots(figsize=(width, 5))

    ### Final capacity and generation
    datum = 'Capacity'
    data = {
        'data': dictin_cap,
        'values':'Capacity (GW)',
        'label':f' {lastyear} Capacity [GW]',
    }
    ax.set_ylabel(data['label'])
    dfplot = pd.concat(
        {case:
            data['data'][case].loc[data['data'][case].year==lastyear]
            .set_index('tech')[data['values']]
            for case in cases},
        axis=1,
    ).T
    dfplot = dfplot.rename(columns=aggstack).groupby(axis=1, level='tech').sum()
    unmapped = [c for c in dfplot if c not in aggcolors]
    if len(unmapped):
        raise Exception(f"Unmapped techs: {unmapped}")
    dfplot = (
        dfplot[[c for c in aggcolors if c in dfplot]]
        .round(3).replace(0,np.nan).dropna(axis=1, how='all').fillna(0)
    )
    mindistance = dfplot.sum(axis=1).max() / 20
    dfcumsum = dfplot.cumsum(axis=1)
    dfdiff = dfplot - dfplot.loc[dfplot.index.map(basemap)].values

    ## Absolute and difference
    plots.stackbar(df=dfplot, ax=ax, colors=aggcolors, width=barwidth, net=False)

    ### Labels
    for x, case in enumerate(cases):
        labels = (dfcumsum.loc[case] - dfplot.loc[case]/2).rename('middle').to_frame()
        try:
            labels['ylabel'] = plots.optimize_label_positions(
                ydata=labels.middle.values, mindistance=mindistance, ypad=0,
            )
        except ValueError:
            labels['ylabel'] = labels['middle'].values
        labels['yval'] = labels.index.map(dfplot.loc[case])
        for i, row in labels.iterrows():
            ## Draw the line
            ax.annotate(
                '',
                xy=(x+barwidth/2, row.middle),
                xytext=(x+barwidth/2+labelpad, row.ylabel),
                arrowprops={
                    'arrowstyle':'-', 'shrinkA':0, 'shrinkB':0,
                    'color':aggcolors[i], 'lw':0.5},
                annotation_clip=False,
            )
            ## Write the label
            diff = np.around(dfdiff.loc[case,i], 0)
            ax.annotate(
                # f"{row.yval:.0f} {i}" + (f" ({diff:+.0f})" if diff else ''),
                (
                    f"{row.yval:.0f}"
                    + (f" {i}" if case == list(cases.keys())[-1] else '')
                    + (f" ({diff:+.0f})" if diff else '')
                ),
                (x+barwidth/2+labelpad+0.01, row.ylabel),
                va='center', ha='left', fontsize=9, color=aggcolors[i],
                weight=('bold' if abs(diff) >= 100 else 'normal'),
                annotation_clip=False,
            )

    ### Formatting
    ax.set_xticks(range(len(cases)))
    ax.set_xticklabels(cases.keys(), rotation=45, rotation_mode='anchor', ha='right')
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(5))
    plt.tight_layout()
    plots.despine(ax)
    plt.draw()
    ### Save it
    slide = reeds.results.add_to_pptx('Capacity stacks', prs=prs, width=width)
    if interactive:
        plt.show()
#%%
## Capacity and generation bars aggtechs
aggstack = {
    **{f'battery_{i}':'Storage' for i in [2,4,6,8,10]},
    **{f'battery_{i}|charge':'Storage|charge' for i in [2,4,6,8,10]},
    **{f'battery_{i}|discharge':'Storage|discharge' for i in [2,4,6,8,10]},
    **{
        'pumped-hydro':'Storage',
        'pumped-hydro|charge':'Storage|charge', 'pumped-hydro|discharge':'Storage|discharge',

        'h2-cc':'H2 turbine', 'h2-ct':'H2 turbine',

        # 'beccs_mod':'Bio/BECCS',
        # 'biopower':'Bio/BECCS', 'lfill-gas':'Bio/BECCS', 'cofire':'Bio/BECCS',
        'beccs_mod':'Biopower',
        'biopower':'Biopower', 'lfill-gas':'Biopower', 'cofire':'Biopower',

        'gas-cc-ccs_mod':'Gas+CCS',
        'coal-ccs_mod':'Coal+CCS',
        'gas-cc':'Gas', 'gas-ct':'Gas', 'o-g-s':'Gas',
        'coal':'Coal',

        'Canada':'Canadian imports', 'canada':'Canadian imports',

        'hydro':'Hydro',
        'geothermal':'Geothermal',

        'csp':'PV',
        'upv':'PV', 'distpv':'Dist PV',
        'pvb':'PVB',

        'wind-ofs':'Offshore wind',
        'wind-ons':'Land-based wind',

        'nuclear':'Nuclear', 'nuclear-smr':'Nuclear',
    }
}
aggcolors = {
    'Nuclear':'C3',

    'Coal':plt.cm.binary(1.0),
    'Gas':plt.cm.tab20(8),
    'Coal+CCS':'C7',
    'Gas+CCS':plt.cm.tab20(9),

    'Hydro': techcolors['hydro'],
    'Geothermal': techcolors['geothermal'],
    'Canadian imports': techcolors['dr_shed'],

    # 'Bio/BECCS':plt.cm.tab20(4),
    # 'H2 turbine':plt.cm.tab20(5),
    'Biopower':techcolors['biopower'],
    'H2 turbine':techcolors['h2-ct'],

    'Land-based wind':techcolors['wind-ons'],
    'Offshore wind':techcolors['wind-ofs'],

    'CSP':techcolors['csp'],
    'PV':techcolors['upv'],
    'PVB':techcolors['pvb'],
    'Dist PV':techcolors['distpv'],

    # 'Storage':plt.cm.tab20(12),
    # 'Storage|charge':plt.cm.tab20(12),
    # 'Storage|discharge':plt.cm.tab20(12),
    'Storage':techcolors['battery_8'],
    'Storage|charge':techcolors['battery_8'],
    'Storage|discharge':techcolors['battery_8'],
}

toplot = {
    'Capacity': {
        'data': dictin_cap,
        'colors':techcolors,
        'columns':'tech',
        'values':'Capacity (GW)',
        'label':'Capacity [GW]'
    },
    'Generation': {
        'data': dictin_gen,
        'colors':techcolors,
        'columns':'tech',
        'values':'Generation (TWh)',
        'label':'Generation [TWh]'
    },
}
plotwidth = 2.0
figwidth = plotwidth * len(cases)
dfbase = {}
for slidetitle, data in toplot.items():
    plt.close()
    f,ax = plt.subplots(
        2, len(cases), figsize=(figwidth, 6.8),
        sharex=True, sharey=sharey, dpi=None,
    )
    ax[0,0].set_ylabel(data['label'], y=-0.075)
    ax[0,0].set_xlim(2017.5, lastyear+2.5)
    ax[1,0].annotate(
        f'Diff\nfrom\n{basecase}', (0.03,0.03), xycoords='axes fraction',
        fontsize='x-large', weight='bold')
    ###### Absolute
    alltechs = set()
    for col, case in enumerate(cases):
        if case not in data['data']:
            continue
        
        dfplot = data['data'][case].pivot(index='year', columns=data['columns'], values=data['values'])
        #dfplot = dfplot[dfplot.index < 2046]
        dfplot = dfplot.rename(columns=aggstack).groupby(axis=1, level='tech').sum()
        unmapped = [c for c in dfplot if c not in aggcolors]
        if len(unmapped):
            raise Exception(f"Unmapped techs: {unmapped}")
        dfplot = (
            dfplot[[c for c in aggcolors if c in dfplot]]
            .round(3).replace(0,np.nan).dropna(axis=1, how='all').fillna(0)
        )
        #dfplot = dfplot.drop(columns ='Canadian imports')
        if case == basecase:
            dfbase[slidetitle] = dfplot.copy()
        alltechs.update(dfplot.columns)
        plots.stackbar(df=dfplot, ax=ax[0,col], colors=aggcolors, width=yearstep[case], net=False)
        ax[0,col].set_title(
            (case if nowrap else plots.wraptext(case, width=plotwidth*0.9, fontsize=14)),
            fontsize=14, weight='bold', x=0, ha='left', pad=8,)
        ax[0,col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
        ax[0,col].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(5))


    ### Legend
    handles = [
        mpl.patches.Patch(
            facecolor=aggcolors[i], edgecolor='none',
            label=i.replace('Canada','imports').split('/')[-1]
        )
        for i in aggcolors if i in alltechs
    ]
    leg = ax[0,-1].legend(
        handles=handles[::-1], loc='upper left', bbox_to_anchor=(1.0,1.0), 
        fontsize='medium', ncol=1,  frameon=False,
        handletextpad=0.3, handlelength=0.7, columnspacing=0.5, 
    )

    ###### Difference
    for col, case in enumerate(cases):
        ax[1,col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
        ax[1,col].xaxis.set_minor_locator(mpl.ticker.MultipleLocator(5))
        ax[1,col].axhline(0,c='k',ls='--',lw=0.75)

        if (case not in data['data']) or (case == basecase):
            continue
        dfplot = data['data'][case].pivot(index='year', columns=data['columns'], values=data['values'])
        #dfplot = dfplot[dfplot.index < 2046]
        dfplot = dfplot.rename(columns=aggstack).groupby(axis=1, level='tech').sum()
        unmapped = [c for c in dfplot if c not in aggcolors]
        if len(unmapped):
            raise Exception(f"Unmapped techs: {unmapped}")
        dfplot = (
            dfplot[[c for c in aggcolors if c in dfplot]]
            .round(3).replace(0,np.nan).dropna(axis=1, how='all').fillna(0)
        )
        #dfplot = dfplot.drop(columns ='Canadian imports')
        # dfplot = (
        #     dfplot
        #     .round(3).replace(0,np.nan)
        #     .dropna(axis=1, how='all')
        # )
        dfplot = dfplot.subtract(dfbase[slidetitle], fill_value=0)
        # dfplot = dfplot[[c for c in aggcolors if c in dfplot]].copy()
        # alltechs.update(dfplot.columns)
        plots.stackbar(df=dfplot, ax=ax[1,col], colors=aggcolors, width=yearstep[case], net=True)

    plots.despine(ax)
    plt.draw()
    plots.shorten_years(ax[1,0])
    ### Save it
    slide = reeds.results.add_to_pptx(
        'Aggregated techs stack', prs=prs, width=min(figwidth, SLIDE_WIDTH))
    if interactive:
        plt.show()

#%%### Generation fraction
ycol = 'Generation (TWh)'
stortechs = [f'battery_{i}' for i in [2,4,6,8,10]] + ['pumped-hydro']
vretechs = ['upv','wind-ons','wind-ofs','distpv','csp']
retechs = vretechs + ['hydro','geothermal','biopower']
zctechs = vretechs + ['hydro','geothermal','nuclear','nuclear-smr']
fossiltechs = ['coal','coal-ccs_mod','gas-cc','gas-cc-ccs_mod','gas-ct','o-g-s','cofire']
reccsnuctechs = retechs + ['coal-ccs_mod','gas-cc-ccs_mod','nuclear','nuclear-smr']

dftotal = pd.concat({
    case:
    dictin_gen[case].loc[~dictin_gen[case].tech.isin(stortechs)].groupby('year')[ycol].sum()
    for case in cases
}, axis=1)

dfvre = pd.concat({
    case:
    dictin_gen[case].loc[dictin_gen[case].tech.isin(vretechs)].groupby('year')[ycol].sum()
    for case in cases
}, axis=1)

dfre = pd.concat({
    case:
    dictin_gen[case].loc[dictin_gen[case].tech.isin(retechs)].groupby('year')[ycol].sum()
    for case in cases
}, axis=1)

dfzc = pd.concat({
    case:
    dictin_gen[case].loc[dictin_gen[case].tech.isin(zctechs)].groupby('year')[ycol].sum()
    for case in cases
}, axis=1)

dffossil = pd.concat({
    case:
    dictin_gen[case].loc[dictin_gen[case].tech.isin(fossiltechs)].groupby('year')[ycol].sum()
    for case in cases
}, axis=1)

dfreccsnuc = pd.concat({
    case:
    dictin_gen[case].loc[dictin_gen[case].tech.isin(reccsnuctechs)].groupby('year')[ycol].sum()
    for case in cases
}, axis=1)

dfplot = {
    'VRE share [%]': (dfvre / dftotal * 100).loc[startyear:],
    'RE share [%]': (dfre / dftotal * 100).loc[startyear:],
    'Zero carbon share [%]': (dfzc / dftotal * 100).loc[startyear:],
    'RE + Nuclear + CCS share [%]': (dfreccsnuc / dftotal * 100).loc[startyear:],
    'Fossil share [%]': (dffossil / dftotal * 100).loc[startyear:],
}

### Plot them
plt.close()
f,ax = plt.subplots(1, 5, figsize=(SLIDE_WIDTH, 4.5), gridspec_kw={'wspace':0.7})
for col, (ylabel, df) in enumerate(dfplot.items()):
    ax[col].set_ylabel(ylabel, labelpad=-4)
    ax[col].set_ylim(0,100)
    ax[col].yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    for case in cases:
        ax[col].plot(df.index, df[case].values, label=case, color=colors[case])
    ## annotate the last value
    plots.label_last(df, ax[col], mindistance=3.5, colors=colors, extend='both', tail='%')

### Legend
leg = ax[0].legend(
    loc='upper left', bbox_to_anchor=(-0.3,-0.05), frameon=False, fontsize='large',
    handletextpad=0.3, handlelength=0.7,
)
for legobj in leg.legend_handles:
    legobj.set_linewidth(8)
    legobj.set_solid_capstyle('butt')

### Formatting
plots.despine(ax)
plt.draw()
for col in range(len(dfplot)):
    ax[col].xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
    ax[col].xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    plots.shorten_years(ax[col])
### Save it
slide = reeds.results.add_to_pptx('Generation share', prs=prs)
if interactive:
    plt.show()


#%%### Transmission maps

### Absolute
wscale = 0.0003
alpha = 0.8
for subtract_baseyear in [None, 2020]:
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(SLIDE_WIDTH, SLIDE_HEIGHT),
        gridspec_kw={'wspace':0.0,'hspace':-0.1},
    )
    for case in cases:
        ### Plot it
        reedsplots.plot_trans_onecase(
            case=cases[case], pcalabel=False, wscale=wscale,
            yearlabel=False, year=lastyear, simpletypes=None,
            alpha=alpha, scalesize=8,
            f=f, ax=ax[coords[case]], title=False,
            subtract_baseyear=subtract_baseyear,
            thickborders='transreg', drawstates=False, drawzones=False, 
            label_line_capacity=10,
            scale=(True if case == basecase else False),
        )
        ax[coords[case]].set_title(case)
    ### Formatting
    title = (
        f'New interzonal transmission since {subtract_baseyear}' if subtract_baseyear
        else 'All interzonal transmission')
    for row in range(nrows):
        for col in range(ncols):
            if nrows == 1:
                ax[col].axis('off')
            elif ncols == 1:
                ax[row].axis('off')
            else:
                ax[row,col].axis('off')
    ### Save it
    slide = reeds.results.add_to_pptx(title, prs=prs)
    if interactive:
        plt.show()


### Difference
plt.close()
f,ax = plt.subplots(
    nrows, ncols, figsize=(SLIDE_WIDTH, SLIDE_HEIGHT),
    gridspec_kw={'wspace':0.0,'hspace':-0.1},
)
for case in cases:
    ax[coords[case]].set_title(case)
    if case == basecase:
        ### Plot absolute
        reedsplots.plot_trans_onecase(
            case=cases[case], pcalabel=False, wscale=wscale,
            yearlabel=False, year=lastyear, simpletypes=None,
            alpha=alpha, scalesize=8,
            f=f, ax=ax[coords[case]], title=False,
            subtract_baseyear=subtract_baseyear,
            thickborders='transreg', drawstates=False, drawzones=False, 
            label_line_capacity=10,
            scale=(True if case == basecase else False),
        )
    else:
        ### Plot the difference
        reedsplots.plot_trans_diff(
            casebase=cases[basecase], casecomp=cases[case],
            pcalabel=False, wscale=wscale,
            yearlabel=False, year=lastyear, simpletypes=None,
            alpha=alpha,
            f=f, ax=ax[coords[case]],
            subtract_baseyear=subtract_baseyear,
            thickborders='transreg', drawstates=False, drawzones=False, 
            label_line_capacity=10,
            scale=False,
        )
### Formatting
title = 'Interzonal transmission difference'
for row in range(nrows):
    for col in range(ncols):
        if nrows == 1:
            ax[col].axis('off')
        elif ncols == 1:
            ax[row].axis('off')
        else:
            ax[row,col].axis('off')
### Save it
slide = reeds.results.add_to_pptx(title, prs=prs)
if interactive:
    plt.show()

#%%### Generation capacity maps
### Shared data
base = cases[list(cases.keys())[0]]
val_r = dictin_cap_r[basecase].r.unique()
dfmap = reeds.io.get_dfmap(base)
dfba = dfmap['r']
dfba = dfba[dfba.index.isin(val_r)].copy()
dfstates = dfmap['st']
dfstates = dfstates[dfstates.index.isin(val_r)].copy()

figwidth = SLIDE_WIDTH
#### Absolute maps
if (nrows == 1) or (ncols == 1):
    legendcoords = max(nrows, ncols) - 1
elif (nrows-1, ncols-1) in coords.values():
    legendcoords = (nrows-1, ncols-1)
else:
    legendcoords = (nrows-2, ncols-1)

### Set up plot
for tech in maptechs:
    ### Get limits
    vmin = 0.
    vmax = float(pd.concat({
        case: dictin_cap_r[case].loc[
            (dictin_cap_r[case].i==tech)
            & (dictin_cap_r[case].t.astype(int)==lastyear)
        ].groupby('r').MW.sum()
        for case in cases
    }).max()) / 1e3
    if np.isnan(vmax):
        vmax = 0.
    if not vmax:
        print(f'{tech} has zero capacity in {lastyear}, so skipping maps')
        continue
    ### Set up plot
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(figwidth, SLIDE_HEIGHT),
        gridspec_kw={'wspace':0.0,'hspace':-0.1},
    )
    ### Plot it
    for case in cases:
        dfval = dictin_cap_r[case].loc[
            (dictin_cap_r[case].i==tech)
            & (dictin_cap_r[case].t.astype(int)==lastyear)
        ].groupby('r').MW.sum()
        dfplot = dfba.copy()
        dfplot['GW'] = (dfval / 1e3).fillna(0)

        ax[coords[case]].set_title(
            case if nowrap else plots.wraptext(case, width=figwidth/ncols*0.9, fontsize=14)
        )
        dfba.plot(
            ax=ax[coords[case]],
            facecolor='none', edgecolor='k', lw=0.1, zorder=10000)
        dfstates.plot(
            ax=ax[coords[case]],
            facecolor='none', edgecolor='k', lw=0.2, zorder=10001)
        dfplot.plot(
            ax=ax[coords[case]], column='GW', cmap=cmap, vmin=vmin, vmax=vmax,
            legend=False,
        )
        ## Legend
        if coords[case] == legendcoords:
            plots.addcolorbarhist(
                f=f, ax0=ax[coords[case]], data=dfplot.GW.values,
                title=f'{tech} {lastyear}\ncapacity [GW]', cmap=cmap, vmin=vmin, vmax=vmax,
                orientation='horizontal', labelpad=2.25, histratio=0.,
                cbarwidth=0.05, cbarheight=0.85,
                cbarbottom=-0.05, cbarhoffset=0.,
            )

    for row in range(nrows):
        for col in range(ncols):
            if nrows == 1:
                ax[col].axis('off')
            elif ncols == 1:
                ax[row].axis('off')
            else:
                ax[row,col].axis('off')
    ### Save it
    slide = reeds.results.add_to_pptx(f'{tech} capacity {lastyear} [GW]', prs=prs)
    if interactive:
        plt.show()

#### Difference maps
### Set up plot
for tech in maptechs:
    ### Get limits
    dfval = pd.concat({
        case: dictin_cap_r[case].loc[
            (dictin_cap_r[case].i==tech)
            & (dictin_cap_r[case].t.astype(int)==lastyear)
        ].groupby('r').MW.sum()
        for case in cases
    }, axis=1).fillna(0) / 1e3
    dfdiff = dfval.subtract(dfval[basecase], axis=0)
    ### Get colorbar limits
    absmax = dfval.stack().max()
    diffmax = dfdiff.unstack().abs().max()

    if np.isnan(absmax):
        absmax = 0.
    if not absmax:
        print(f'{tech} has zero capacity in {lastyear}, so skipping maps')
        continue
    ### Set up plot
    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(figwidth, SLIDE_HEIGHT),
        gridspec_kw={'wspace':0.0,'hspace':-0.1},
    )
    ### Plot it
    for case in cases:
        dfplot = dfba.copy()
        dfplot['GW'] = dfval[case] if case == basecase else dfdiff[case]

        ax[coords[case]].set_title(
            case if nowrap else plots.wraptext(case, width=figwidth/ncols*0.9, fontsize=14)
        )
        dfba.plot(
            ax=ax[coords[case]],
            facecolor='none', edgecolor='k', lw=0.1, zorder=10000)
        dfstates.plot(
            ax=ax[coords[case]],
            facecolor='none', edgecolor='k', lw=0.2, zorder=10001)
        dfplot.plot(
            ax=ax[coords[case]], column='GW',
            cmap=(cmap if case == basecase else cmap_diff),
            vmin=(0 if case == basecase else -diffmax),
            vmax=(absmax if case == basecase else diffmax),
            legend=False,
        )
        ## Difference legend
        if coords[case] == legendcoords:
            plots.addcolorbarhist(
                f=f, ax0=ax[coords[case]], data=dfplot.GW.values,
                title=f'{tech} {lastyear}\ncapacity, difference\nfrom {basecase} [GW]',
                cmap=(cmap if case == basecase else cmap_diff),
                vmin=(0 if case == basecase else -diffmax),
                vmax=(absmax if case == basecase else diffmax),
                orientation='horizontal', labelpad=2.25, histratio=0.,
                cbarwidth=0.05, cbarheight=0.85,
                cbarbottom=-0.05, cbarhoffset=0.,
            )
    ## Absolute legend
    plots.addcolorbarhist(
        f=f, ax0=ax[coords[basecase]], data=dfval[basecase].values,
        title=f'{tech} {lastyear}\ncapacity [GW]',
        cmap=cmap, vmin=0, vmax=absmax,
        orientation='horizontal', labelpad=2.25, histratio=0.,
        cbarwidth=0.05, cbarheight=0.85,
        cbarbottom=-0.05, cbarhoffset=0.,
    )

    for row in range(nrows):
        for col in range(ncols):
            if nrows == 1:
                ax[col].axis('off')
            elif ncols == 1:
                ax[row].axis('off')
            else:
                ax[row,col].axis('off')
    ### Save it
    slide = reeds.results.add_to_pptx(f'Difference: {tech} capacity {lastyear} [GW]', prs=prs)
    if interactive:
        plt.show()

#%%
# Net import and exports

# Create a bar chart for net imports
fig, axes = plt.subplots(1, len(cases), figsize=(10 * (len(cases)), 10), sharey=True)

# Plot individual cases
for idx, (case, path) in enumerate(cases.items()):
    exports = pd.read_csv(
        os.path.join(path, 'outputs', 'export_ann_rep.csv')
    ).rename(columns={'Value': 'exports'})
    imports = pd.read_csv(
        os.path.join(path, 'outputs', 'import_ann_rep.csv')
    ).rename(columns={'Value': 'imports'})

    net = pd.merge(imports, exports, on=['r', 't'])
    net['net'] = (net['imports'] - net['exports']) / 1000

    net = net[net['t']>=2026]

    ax = axes[idx]
    net.groupby('t')['net'].sum().plot(kind='bar', ax=ax, color='skyblue', edgecolor='black')
    ax.set_title(f'Net Imports\nfor {case}', fontsize=24)
    #ax.set_xlabel('Year', fontsize=12)
#     ax.set_ylabel('GWh', fontsize=22)
#     ax.set_xticklabels(net['t'].unique(), rotation=45, fontsize=30)
#     ax.grid(axis='y', linestyle='--', alpha=0.7)


# axes[0].tick_params(axis='y', labelsize=30)
# #plt.xlabel('Year', fontsize=12)
# plt.ylabel('GWh', fontsize=22)
# plt.tight_layout()
# plt.show()  

# ### Save it
# slide = reeds.results.add_to_pptx(f'Net Imports', prs=prs)
# if interactive:
#     plt.show()

    ax.set_ylabel('GWh', fontsize=22)
    ax.set_xticklabels(net['t'].unique(), rotation=45, fontsize=30)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

axes[0].tick_params(axis='y', labelsize=30)
plt.ylabel('GWh', fontsize=22)
plt.tight_layout()

# Save figure to slide
slide = reeds.results.add_to_pptx('Net Imports', prs=prs)
if interactive:
    plt.show()
plt.close(fig)

#%% Save the powerpoint file
prs.save(savename)
print(f'\ncompare_casegroup.py results saved to:\n{savename}')

### Open it
if sys.platform == 'darwin':
    sp.run(f"open '{savename}'", shell=True)
elif platform.system() == 'Windows':
    sp.run(f'"{savename}"', shell=True)
