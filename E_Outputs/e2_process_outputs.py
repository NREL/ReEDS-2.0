# Process model results from gams, arrange the tables, save key results in Excel format, create basic plots

#%%
import gdxpds
import pandas as pd
import os
import datetime
import sys

# suppress pandas chained assignments warning
pd.options.mode.chained_assignment = None

# Bokeh libraries
from bokeh.io import output_file, output_notebook
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
from bokeh.layouts import row, column, gridplot
from bokeh.models.widgets import Tabs, Panel
from bokeh.transform import factor_cmap
from pathlib import Path

case = str(sys.argv[1])
#case = 'Sep22_UI_test1'
#os.chdir('..')
#%%
def summarize(df, sumby):
    out = df.groupby(sumby).sum().reset_index()
    return(out)

def setnames(df, lvl_name):
    out = df.rename(columns={'i':'Technology','h':'Timeslice','r':'State','t':'Year','Level':lvl_name})
    return(out)

def map_rs_to_state(df, rmap):
    out = pd.merge(df, rmap, left_on = 'r', right_on = 'rs', how='left')
    out['r_y'].loc[out['r_y'].isnull()] = out['r_x']
    out.rename(columns = {'r_y':'r'}, inplace = True)
    return(out)

def get_tslc_hours(df, left_on, tslc_hours):
    df = df.merge(tslc_hours, left_on = left_on, right_on = 'h')
    df.rename(columns = {'Value':'Timeslice_hours'}, inplace = True)
    return(df)

# %%

#%%
def ProcessingGdx():

    # developing mode - start with a single gdx file
    # TODO: endable processing multiple cases/files

    case_gdx = "output_{}.gdx".format(case)
    run_name = case.split('_')[0] + '_' + case.split('_')[1]
    #gdxdir = os.path.join("E_Outputs","gdxfiles",case_gdx) # TODO: change save location to user-specific folder
    gdxdir = os.path.join("reeds_server","users_output", case.split('_')[0], run_name,"gdxfiles",case_gdx)

    savedir = os.path.join("reeds_server", "users_output", case.split('_')[0], run_name, 'exceloutput') # TODO: change save location to user-specific folder
    Path(savedir).mkdir(parents=True, exist_ok=True)

    # check that file exists
    if (not os.path.exists(gdxdir)):
        print("{} not found".format(gdxdir))
        exit()
    else:
        print("Processing {}".format(gdxdir))
    #%%
    gdxin = gdxpds.to_dataframes(gdxdir)
    #%%

    # get mapping of resource regions to states
    rmap = gdxin['r_rs'][['r','rs']]

    # timeslice horus map
    tslc_hours = gdxin['hours']
    #%%
    ####### Begin data queries 
    #######

    # Installed capacity
    global cap
    cap = gdxin['CAP']
    cap = map_rs_to_state(cap, rmap)
    cap = summarize(cap, ['i','r','t'])
    cap = setnames(cap, 'capacity_MW')
    cap = cap[['Technology','State','Year','capacity_MW']]

    #%%
    # Capacity investments
    inv = gdxin['INV']
    inv = map_rs_to_state(inv, rmap)
    inv = summarize(inv, ['i','r','t'])
    inv = setnames(inv, 'investments_MW')
    inv = inv[['Technology','State','Year','investments_MW']]

    #%%
    # Firm capacity 
    pdlist = [gdxin['firm_conv'],gdxin['firm_hydro'],gdxin['firm_vg'],gdxin['firm_stor']]
    firmcap = pd.concat(pdlist)
    firmcap.set_axis(['Region','Season','Year','Technology','firm_capacity_MW'], axis = 1, inplace = True)

    #%%
    # Timeslice dispatch
    gen_tslc = gdxin['GEN']
    gen_tslc = summarize(gen_tslc, ['i','r','h','t'])
    gen_tslc = setnames(gen_tslc, 'dispatch_MW')
    gen_tslc = get_tslc_hours(gen_tslc, 'Timeslice', tslc_hours)
    gen_tslc = gen_tslc[['Technology','State','Year','Timeslice','Timeslice_hours','dispatch_MW']]
    gen_tslc['generation_MWh'] = gen_tslc['dispatch_MW'] * gen_tslc['Timeslice_hours']

    # Annual generation
    gen = summarize(gen_tslc, ['Technology','State','Year'])
    gen = gen[['Technology','State','Year','generation_MWh']]

    #%%
    # Timeslice operating reserves
    opres_tslc = summarize(gdxin['OPRES'], ['i','r','h','t'])
    opres_tslc = setnames(opres_tslc, 'operating_reserves_MW')
    opres_tslc = opres_tslc[['Technology','State','Timeslice','Year','operating_reserves_MW']]
    opres_tslc = get_tslc_hours(opres_tslc, 'Timeslice', tslc_hours)
    opres_tslc = opres_tslc[['Technology','State','Year','Timeslice','Timeslice_hours','operating_reserves_MW']]
    opres_tslc['operating_reserves_MWh'] = opres_tslc['operating_reserves_MW'] * opres_tslc['Timeslice_hours']

    # Annual operating reserves
    opres = summarize(opres_tslc, ['Technology','State','Year'])
    opres = opres[['Technology','State','Year','operating_reserves_MWh']]

    #%%
    # Storage operation
    storin = summarize(gdxin['STORAGE_IN'], ['i','r','h','t'])
    storin = setnames(storin, 'STOR_IN_MW')

    storlev = summarize(gdxin['STORAGE_LEVEL'], ['i','r','h','t'])
    storlev = setnames(storlev, 'STOR_LVL_MWh')

    storgen = gen_tslc.loc[pd.Series(gen_tslc['Technology']).str.contains('BATTERY|PUMPED').tolist()]
    storgen.rename(columns = {"dispatch_MW":"STOR_GEN_MW"}, inplace = True)

    storops = pd.merge(storin, storlev, on = ['Technology','State','Year','Timeslice'])
    storops = pd.merge(storops, storgen, on = ['Technology','State','Year','Timeslice'])
    storops = storops[['Technology','State','Year','Timeslice','STOR_IN_MW','STOR_LVL_MWh','STOR_GEN_MW']]

    #%%
    # Transmission capacity
    txcap = summarize(gdxin['CAPTRAN'], ['r','rr','t'])
    txcap = txcap[['r','rr','t','Level']]
    txcap.set_axis(['State_from','State_to','Year','transmission_capacity_MW'], axis = 1, inplace = True)

    # Transmission investments
    txinv = gdxin['txinv'].copy()
    txinv.set_axis(['State_from','State_to','Year','transmission_investment_MW'], axis = 1, inplace = True)

    # Emissions
    emit = gdxin['EMIT']

    #%%
    ##### Organize sheets
    # Sheet 1: Annual results - cap, inv, gen, opres, emit
    annual_out = pd.merge(cap, inv, on = ['Technology','State','Year'], how='left')
    annual_out = annual_out.merge(gen, on = ['Technology','State','Year'], how='left')
    annual_out = annual_out.merge(opres, on = ['Technology','State','Year'], how='left')
    #annual_out = annual_out.merge(emit, on = ['Technology','State','Year'])

    # Sheet 2: Seasonal firm capacity - firmcap
    # just firmcap here

    # Sheet 3: Timeslice results - gen_tslc, opres_tslc, storops
    tslc_out = pd.merge(gen_tslc, opres_tslc, on = ['Technology','State','Year','Timeslice'])
    tslc_out = tslc_out.merge(storops, on = ['Technology','State','Year','Timeslice'] )

    # Sheet 4: Transmission results - txcap, txinv
    tx_out = pd.merge(txcap, txinv, on = ['State_from','State_to','Year'], how='left')

    #%%
    #%%
    ######## EXPORT TO EXCEL
    ########
    # separate sheet for each table
    writer = pd.ExcelWriter(os.path.join(os.getcwd(),savedir,"{}_results.xlsx".format(case)))

    annual_out.to_excel(writer, sheet_name = "Annual results")
    firmcap.to_excel(writer, sheet_name = "Seasonal firm capacity")
    tslc_out.to_excel(writer, sheet_name = "Timeslice results")
    tx_out.to_excel(writer, sheet_name='Transmission results')

    writer.save()
    print("Results saved to " + os.path.join(savedir,"{}_results.xlsx".format(case)))
# %%

#%%
# read gdx output and save results as excel
ProcessingGdx()


#%%
#%%
# Plotting interactive figures 
# TODO: load metadata that will be used later
# 1. Load analysis parameters (gen order, gen types, etc. )
# plotparams = pd.read_csv(os.path.join('A_Inputs','inputs','analysis','analysis_parameters.csv'))

# tech_type_map = plotparams[['reeds.category','Type']].dropna()
# type_color_map = plotparams[['Gen.Type','Plot.Color']].dropna()
# type_order = plotparams[['Gen.Order']].dropna()

#     # 2. state centroids
#     # 3. timeslice names map
#     # 4. region map (from GDX)
#     # 5. timeslice hours map (from GDX)


# #%%
# #### Generate basic plots of results
# #output_file('output_plots.html')  # Render to static HTML, or 
# output_notebook()  # Render inline in a Jupyter Notebook - for testing
# #%%
# cap_bytype = cap.merge(tech_type_map, left_on = 'Technology', right_on = 'reeds.category')
# cap_bytype = summarize(cap_bytype, ['Year','Type'])
# types = cap_bytype['Type'].unique().tolist()

# cap_pivot = cap_bytype.pivot_table(index=['Year'],columns='Type',aggfunc=sum).fillna(0).reset_index()
# cap_pivot.columns = cap_pivot.columns.to_series().str.join('').str.lstrip('capacity_MW')
# cap_pivot.rename(columns = {'nd':'Wind'}, inplace = True)

# # set Year column type to datetime
# cap_pivot['Year'] = pd.to_datetime(cap_pivot['Year'], format='%Y')

# # filter colors and order based on on what's in the data
# type_color_map = type_color_map.loc[type_color_map['Gen.Type'].isin(types)]
# type_order = type_order.loc[type_order['Gen.Order'].isin(types)].values.tolist()
# type_order = sum(type_order, [])

# # sort the columms and colors according to the type order
# type_order_rev = type_order.copy()
# type_order_rev.reverse()
# type_color_map['Gen.Type'] = type_color_map['Gen.Type'].astype('category')
# type_color_map['Gen.Type'].cat.set_categories(type_order, inplace=True)
# type_color_map.sort_values(["Gen.Type"], inplace=True)

# type_order.append('Year')

# cmap_rev = type_color_map['Plot.Color'].tolist()
# cmap_rev.reverse()
# #%%
# # Example figure
# fig = figure(background_fill_color='white',
#                 background_fill_alpha=0.5,
#                 border_fill_color='white',
#                 border_fill_alpha=0.25,
#                 plot_height=300,
#                 plot_width=500,
#                 x_axis_type='datetime',
#                 y_axis_label='Capacity (MW)',
#                 y_axis_location='left',
#                 toolbar_location='right')

# #cmap = factor_cmap('types', palette=type_color_map['Plot.Color'].tolist(), factors=type_color_map['Gen.Type'])
# fig.vbar_stack(type_order_rev, x='Year', source=cap_pivot, legend_label = type_order_rev,
#                 width=datetime.timedelta(days=365),
#                 color=cmap_rev)

# new_legend = fig.legend[0]
# fig.legend[0] = None
# fig.add_layout(new_legend, 'right')
# fig.legend.label_text_font_size = '8pt'
# fig.label_text_baseline: "top"
# fig.legend.label_height: 5
# fig.legend.label_width: 5
# fig.legend.glyph_height = 10
# fig.legend.glyph_width = 10
# fig.legend.spacing = 0

# show(fig)  

# %%
