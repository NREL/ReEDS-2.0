import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
from itertools import product
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from pyproj import Proj
from matplotlib import cm
from colour import Color
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import re as regex

# =============================================================================
#%% USER INPUT 
# =============================================================================

year = 2050
scens_name = "a1"
runs_folder = 'a1'

project_folder = os.path.join('\\\\nrelqnap02','ReEDS','FY20-RE100')
runs_folder = os.path.join(project_folder,'Runs', runs_folder)
link_dir = os.path.join('D:\Scott','ReEDS2_PLEXOS_link')
#link_dir = r'C:\Users\DGREER\Documents\ReEDS2_PLEXOS_link'
reeds_inputs = ('D:\Danny_ReEDs\ReEDs-2.0\inputs')
####################################################
#                   DIrectories 
####################################################
help_files = os.path.join(link_dir,'help_files')
dir_out = os.path.join(runs_folder,'compare_data')
dir_fig_out = os.path.join(dir_out,'figures')

if os.path.isdir(dir_out)==False: os.mkdir(dir_out)            
if os.path.isdir(dir_fig_out)==False: os.mkdir(dir_fig_out)            

####################################################
#                   SCENARIOS 
####################################################

# scenario list
scenarios_base = ['Ref','RE80','RE90','RE95','RE97','RE99','RE100']
scenarios_base_names = [scens_name + '_' + scen for scen in scenarios_base]

#scenario short list 
scenarios_short = ['Ref','RE95','RE97','RE99','RE100']
scenarios_short_names = [scens_name + '_' + scen for scen in scenarios_short]

#sensitivity list
sensitivities = ["LowRE","HighRE","HighBatt","LowBatt","LowDem","HighDem","LowNG","HighNG","CleanEnergy","CleanEnergy_CCS","HVDC_overlay","Low_RE_Batt_Cost","High_RE_Batt_Cost",'2030',"2040","Bus_Bar_Load","NoTrans","No_RE_CT","LowCost"]
sensitivity_repen = ["_".join(tups) for tups in list(product(sensitivities,scenarios_base))]# + ['Long_Duration_Storage_RE100']
sensitivity_names = [scens_name + '_' + scen for scen in sensitivity_repen]

#scenarios_all = scenarios_base
scenarios_all =  scenarios_base + sensitivity_repen
#scenarios_all = scenarios_short

scenarios_all_names = [scens_name + '_' + scen for scen in scenarios_all]

scenario_labels = {'Base':'Base','Ref':'Ref 57%','RE80': '80%','RE90':'90%','RE95':'95%','RE97':'97%','RE99':'99%','RE100':'100%','RE100':'100%','LowRE':'Low RE Cost','HighRE':'High RE Cost','NoTrans':'No New Transmission','HighBatt':'High Battery Cost',
                   'LowBatt':'Low Battery Cost','LowDem':'Low Demand','HighDem':'High Demand','LowNG':'Low Natural Gas Price','HighNG':'High Natural Gas Price','CleanEnergy':'Nuclear Counts',
                   'CleanEnergy_CCS':'Nuclear & CCS Count','HVDC_overlay':'HVDC Overlay',"Low_RE_Batt_Cost":'Low RE & Battery Cost',"High_RE_Batt_Cost":'High RE & Battery Cost',"2030":'100% by 2030',"2040":'100% by 2040',"Bus_Bar_Load":'End-Use Load',
                   "LowCost": 'Lowest System Cost','Long_Duration_Storage':'Long Duration Storage',"No_RE_CT":"No RE-CT"}

####################################################
#               TECHNOLOGY LISTS
####################################################

re = ['DPV','Geothermal','Hydro','UPV','Offshore Wind','Onshore Wind','CSP','Biopower','Imports','RE-CT','Landfill-gas'] #'caes', 'battery', 'phs','canadian_imports'
ce = ['DPV','Geothermal','Hydro','UPV','Offshore Wind','Onshore Wind','CSP','Biopower','Imports','RE-CT','Landfill-gas','Nuclear','Gas-CC-CCS']
vre = ['DPV','UPV','Offshore Wind','Onshore Wind',]
storage = ['Battery 2','Battery 4','Battery 6','Battery 8','Battery 10','Pumped Hydro','PHS']

####################################################
#%%               MAPS
####################################################

scenario_map = pd.DataFrame(list(product(['Base']+sensitivities,scenarios_base)),columns=['sens','base'])
scenario_map.loc[:,'scenario'] = scenarios_all_names
scenario_map.merge(pd.DataFrame(columns=['base','label'],data=scenario_labels),how='left',on='base')

tech_map = pd.read_csv(os.path.join(help_files,'map_techs_RE100.csv'))
cost_cat_map = pd.read_csv(os.path.join(help_files,'cost_cat_map.csv'))
cost_cat_type = pd.read_csv(os.path.join('D:\\Danny_ReEDS\\ReEDS-2.0\\bokehpivot\\in\\reeds2','cost_cat_type.csv'))

tech_colors = pd.read_csv(os.path.join(help_files,'map_techs_colors_RE100.csv'))

seasons = ['summ','fall','wint']
seasons = pd.DataFrame({'szn':seasons})
regions = pd.DataFrame({'r':['p' + str(n) for n in range(1,135)]})
ba_szn = regions.assign(foo=1).merge(seasons.assign(foo=1)).drop('foo',1)

szn_map = {'summ':'Summer','fall':'Fall','wint':'Winter'}

abbreviation_dict = {'trans':'Transmission','load':'Load','curt':'Curtailment',
                     'STORAGE':'Storage','O&M':'O&M','Fuel':'Fuel','Trans':'Transmission','Capital':'Capital'}

r_rs = pd.read_csv(os.path.join(help_files,"r_rs.csv"))

intercon_map = pd.read_csv(os.path.join(project_folder,'regions_default.csv'))
all_years = pd.DataFrame({'t':range(2020,2051)})

requirement = pd.DataFrame(data={'base':['Ref','RE80','RE90','RE95','RE97','RE99','RE100'],'Requirement':[57,80,90,95,97,99,100]})

re_techs = ['Biopower','CSP','DPV','Geothermal','Hydro','Offshore Wind','Onshore Wind','UPV','RE-CT']
####################################################
#%%           DATA AND PLOTTING OPTION
####################################################

get_reeds_data = True
save_reeds = False
get_plexos_data = False
plot_data = True
save_figs = True
extra_figs = True
reeds_inputs_figs = False
plexos_plots = False
####################################################
#           PLOTTING STYLE OPTIONS
####################################################

#fontsize
legend = 18
legend_small= 13
axislabels = 16
ticklabels = 15

cpal = ['#00a9e0','#FFC72C','#84BD00','#ff6d33']

white = Color('white')
cm_subsection = np.linspace(0,1, len(sensitivities)+1)  # start, stop, number_of_lines
scenario_colors = [ cm.tab20(x) for x in cm_subsection ]
####################################################
#                   FUNCTIONS
####################################################
#import os, sys
#sys.path.insert(1, os.path.join(sys.path[0], '..'))
#import core
#import importlib
#
#def run_report(*args):
#    data_type = 'ReEDS 2.0'
#    data_source, report_path, html_num, output_dir, = *args
##    report_path = sys.argv[3]
#    html_num = 'one'#sys.argv[4]
##    output_dir = sys.argv[5]
#    auto_open = 'no'
#    
#    report_dir = os.path.dirname(report_path)
#    sys.path.insert(1, report_dir)
#    report_name = os.path.basename(report_path)[:-3]
#    report = importlib.import_module(report_name)
#    core.static_report(data_type, data_source, report.static_presets, report_path, 'both', html_num, output_dir, auto_open)
        

def process_emissions(emit_temp):
    new_df = pd.DataFrame()
    for scen in emit_temp.scenario.unique():
        df_temp = emit_temp[emit_temp.scenario==scen]
        endyear = int(df_temp.t.max())
        df_temp.set_index('t',inplace=True)
        
        for year in list(range(endyear+2,2070,2)):
            if endyear < 2050:
                df_temp.loc[year] = df_temp.iloc[-1]
                df_temp.loc[year,'emissions'] = 0
            else:
                df_temp.loc[year] = df_temp.loc[endyear]
                
        df_temp.reset_index(inplace=True)
        
        
        odds=pd.DataFrame(dict(t=range(2021,2070,2)))
        odds['sens'] = df_temp.sens.unique()[0]
        odds['base'] = df_temp.base.unique()[0]
        odds['scenario'] = scen
        
        df_temp = pd.concat([df_temp,odds]).sort_values('t')
        df_temp.emissions = df_temp.emissions.interpolate()
#        df_temp.set_index('t',inplace=True)
        new_df = pd.concat([new_df,df_temp]).sort_values(['scenario','t'])
    return new_df
#Collects desired ReEDS data for all scenarios and puts them in one dataframe
def get_all_scen_data_reeds(filename,scen_list,col_names,agg=False,agg_cols=[],map_tech=False):
    for s in scen_list:
        #import data and add column names
        data_temp = pd.read_csv(os.path.join(runs_folder,s,'outputs',filename+'.csv'))
        data_temp.columns = col_names
        
        #Data processing options
        if map_tech:
            data_temp.i = data_temp.i.str.lower()
            data_temp = data_temp.merge(tech_map,on='i',how='left')
            data_temp.cat = data_temp.cat.fillna(data_temp.i)
            data_temp = data_temp.drop(['i'],1).rename(columns={map_tech:'i'})
        if agg:
            data_temp = data_temp.groupby(agg_cols,as_index=False).aggregate(agg)
            
        #add scenario column
        data_temp['scenario'] = s
        
        #create a single dataframe
        if s == scen_list[0]:
            data = data_temp
        else:
            data = pd.concat([data,data_temp])

    return data

def get_all_scen_data_plexos(filename,scenlist,year):
    df_dict = {}
    
    for i, scen in enumerate(scenlist):
        print(scen)
        df = pd.read_pickle(os.path.join(runs_folder,'{}_{}'.format(scens_name,scen),'plexos_export','data','{}_{}.pkl'.format(filename,year)))
        df['scenario']=scen
        df_dict[scen] = df
        
    return df_dict


def get_system_cost(scens_list,*args,pivot=True):
    
    df = pd.read_csv(os.path.join(*args)).rename(columns={'Discounted Cost (Bil $)':'disc_5'})
    df = df[df.scenario.isin(scens_list)]
    
#    for s in scens_list:
#        print(s)
#        df_temp = pd.read_excel(os.path.join(runs_folder,s,'outputs','reeds-report','report.xlsx'),sheet_name='23_2020-2050 Present Value of S').rename(columns={'Discounted Cost (Bil $)':'disc_5'})
#        df_temp.loc[:,'scenario'] = s
#        #create a single dataframe
#        if s == scens_list[0]:
#            df = df_temp
#        else:
#            df = pd.concat([df,df_temp])
    
    if pivot:
        df = df.pivot_table(index='cost_cat',columns='scenario',values='disc_5')
        df = df[scens_list]
    else:
        df = df.groupby(['scenario'],as_index=False).sum()
        
    return df

def get_presystem_cost(scens_list,pivot=False):
    
    for s in scens_list:
        print(s)
        df_temp = pd.read_csv(os.path.join(runs_folder,s,'outputs','systemcost.csv')).rename(columns={'Dim1':'inv_type','Dim2':'year','Val':'system_cost'})
        df_temp.loc[:,'scenario'] = s
        #create a single dataframe
        if s == scens_list[0]:
            df = df_temp
        else:
            df = pd.concat([df,df_temp])
    
    if pivot:
        df = df.pivot_table(index='cost_cat',columns='scenario',values='disc_5')
        df = df[scens_list]
    else:
        df = df.groupby( ['scenario','year'], as_index=False).sum()
        
    return df

# Extra formatting for ReEDS system cost data
def format_sys_cost(df,map_scen = False):
    df = df.loc[df.t>=2020,:]

    
    df2 = df.copy()
    df2 = df2.merge(cost_cat_type,on='cost_cat',how='left')
    df2 = df2.loc[df2.type=='Operation',:]
    df2 = df2[['scenario','cost_cat']].assign(foo=1).merge(all_years.assign(foo=1)).drop('foo',1).drop_duplicates()
    df = df.merge(df2,on=['t','scenario','cost_cat'],how='outer').sort_values(by = ['scenario','cost_cat','t'])
    df = df.fillna(method = 'ffill')
    
    df = df.merge(cost_cat_map, on='cost_cat',how='left')
    df = df.drop(['cost_cat'],1).rename(columns={'display':'cost_cat'})
    
    df.loc[:,'Discounted 5%'] = (df.loc[:,'cost']/(1.05**(df.loc[:,'t']-2020)))*1.3522
    df.loc[:,'Discounted 3%'] = (df.loc[:,'cost']/(1.03**(df.loc[:,'t']-2020)))*1.3522
    df.loc[:,'Discounted 7%'] = (df.loc[:,'cost']/(1.07**(df.loc[:,'t']-2020)))*1.3522
    
    df = df.loc[(df.cost_cat != 'Capital no ITC') & (df.cost_cat!= 'Other')] #& (df.cost_cat!= 'PTC')
    df.loc[(df.cost_cat=='O&M') & (df.t==2050),'cost'] = 0
    df = df.groupby(['scenario','cost_cat'],as_index=False).aggregate('sum')
    
    if map_scen:
        df = df.merge(scenario_map,on='scenario')
        df = df.groupby(['scenario','sens','base'],as_index = False).sum().drop(['t'],1)
        return df
    
    df = df.pivot_table(index='cost_cat',columns='scenario',values='Discounted 5%')/1e9
    
    try:
        df = df[scenarios_base_names]
    except:
        pass
    
    return df


# Extra formatting for ReEDS emissions data
def format_reeds_emissions(df):
    df = df.loc[df.t==2050,:].reset_index(drop=True)
    df = df.drop('t',1)
    #This is temporary until we get PLEXOS data
    x = gen_2050_all.merge(scenario_map,on='scenario',how='left')
    x = x.drop(x.loc[x.scenario.str.contains('Bus')].index).rename(columns={'gen':'emissions'})
    re100_emit = x.loc[x.base == 'RE100',:].groupby(['scenario','sens','base'],as_index=False).sum()#.gen
    re100_emit.loc[:,'emissions'] = (re100_emit.loc[:,'emissions'] * 0#.03 * 0.053061224)/3.412e6
    #Remove the CleanEnergy_CCS scenario because it actually has emissions in the RE100 case
    re100_emit = re100_emit[re100_emit.sens != 'CleanEnergy_CCS']
    df = pd.concat([df,re100_emit[['emissions','scenario','sens','base']]])

    
    df = df.merge(scenario_map,on=['scenario','sens','base'],how='right').fillna(0)
#    df = df.pivot_table(columns='scenario',values='emissions')
    return df

# Extra formatting for ReEDS generation and capacity data
def format_cap_gen(df,capgen,min_year=2020):
    if capgen == 'gen':
        df = df.loc[~(df.i.isin(storage))]
    df = df.loc[df.t >= min_year]
    
    if capgen == 'firmcap':
#        df = df.loc[df.scenario.isin(scenarios_short_names)]
        df = df.drop('t',1)
        df = df.loc[df.szn != 'spri',:]
    return df

# reverse the order of elements in a legend
def reverse_legend(handles,labels):
    handles.reverse()
    labels.reverse()
    return handles, labels

#Function to format and pivot data to make it easier for plotting
def format_capgen_for_plotting(df,values,subset_col='scenario',subset=False,pivot_cols='t'):
    if subset:
        df = df.loc[df[subset_col] == subset,:]
    df = df.pivot(index='i',columns=pivot_cols,values=values)
    df = df.reindex(tech_colors.order).fillna(0)
    df = df[(df.T != 0).any()]
    
    return df

# Define function to read in ba region boundaries and centroids for USA
def read_ba_usa():
    # Read in BA boundaries
    gis_n = pd.read_csv(os.path.join(project_folder, 'gis_rb.csv'))
    gis_n['num'] = gis_n.id.str[1:].astype(int)
    gis_n = gis_n.loc[gis_n.num <= 134] # Filter to just USA
    
    # Read in BA centroids
    gis_centroid_n = pd.read_csv(os.path.join(project_folder, 'gis_centroid_rb.csv'))
    gis_centroid_n = gis_centroid_n.loc[gis_centroid_n.country == 'USA'].drop(
            columns='country') # Filter to just USA

    return gis_n, gis_centroid_n

# Define projection function
def project(df, lat_col, lon_col):
    proj = Proj(proj='utm',lon_0=-96, ellps='WGS84')
    lons = df[lon_col].to_list()
    lats = (1.0*df[lat_col]).to_list() # Match plotly with *1.08
    x, y = proj(lons, lats)
    df[lon_col] = x
    df[lat_col] = y
    return df

# Define map plotting function
def plot_region_flows(data, gis_n, centroids, axn,colorbar=False,color_map='Blues',ymax=10000,label=''):
    '''
    data = needs to have at least two columns:
        n: contains BA indications, e.g. p1
        val: contains data to plot on map
    gis_n = needs to have at least 3 columns:
        long
        lat
        group: 
    '''
    
    # Plotting options
    linewidth = 10

    # Assign colors by region value
    colors = []
    regions = list(gis_n.id.unique())
    for ba in regions:
        color = data.loc[data.n == ba, 'val'].values[0]
        colors.append(color)
    colors.append(ymax)
    
    # Load the polygons into a list
    patches = []
    for ba in regions:
        df = gis_n.loc[gis_n.id == ba, ['long', 'lat']].values    
        polygon = Polygon(df, closed = True, linewidth=linewidth,
                          edgecolor='k')
        patches.append(polygon)

    p = PatchCollection(patches, edgecolors='k', linewidths=0.5)#, alpha=0.4)
#    cgrad = list(white.range_to(Color(color_map),len(colors)))
#    cgrad = [x._hsl for x in cgrad]
#    cgrad = LinearSegmentedColormap('newcolors',cgrad)
    p.set_cmap(color_map)
    
    p.set_array(np.array(colors)) # What is this doing?
    axn.add_collection(p)
    
    # Plot centroids (on the top layer)
    for ba in regions:
        axn.scatter(x=centroids.loc[ba, 'long'],
                    y=centroids.loc[ba, 'lat'],
                    s=0, c='k')


    
    # Remove x ticks and spines
    axn.set_xticks([])
    axn.set_yticks([])
    axn.spines['top'].set_visible(False)
    axn.spines['bottom'].set_visible(False)
    axn.spines['left'].set_visible(False)
    axn.spines['right'].set_visible(False)
    
    # Add colorbar
    if colorbar:
        fig.colorbar(p, ax=axn,label=label)
        
def get_curtailment_duration_curves(plexos_data):
    duration_df = pd.DataFrame()
    
    for scen in list(plexos_data.keys()):
        df = pd.DataFrame(plexos_data[scen])
        df = df[['timestamp','curtailment']].groupby('timestamp').sum().reset_index()
        df['hours']=1
        df.curtailment = round(df.curtailment/1e3)
        df = df.groupby('curtailment').sum()
        df.reset_index(inplace=True)
        df.sort_values( 'curtailment', ascending=False, inplace=True )
        df.reset_index(inplace=True, drop=True)
        df['hours'] = df.hours.cumsum()
        df['scenario'] = scen
        duration_df = pd.concat([duration_df,df])
        
    return duration_df

def get_load_duration_curves(plexos_data,vre_data):
    duration_df = pd.DataFrame()
    vre_plexos = ['ReEDS_distpv','ReEDS_dupv','ReEDS_upv','ReEDS_wind-ofs','ReEDS_wind-ons']
    for scen in list(plexos_data.keys()):
#        vre_df = vre_data[scen]
#        vre_df = vre_df[vre_df['tech'].isin(vre_plexos)]
#        vre_df = vre_df[['timestamp','generation']].groupby('timestamp').sum()
        
        
        df = pd.DataFrame(plexos_data[scen])
        df = df[['timestamp','load']].groupby('timestamp').sum()
        df.load -= vre_df.generation
        df.reset_index(inplace=True)
        df['hours']=1
        df.load = df.load/1e3
        df = df.groupby('load').sum()
        df.reset_index(inplace=True)
        df.sort_values( 'load', ascending=False, inplace=True )
        df.reset_index(inplace=True, drop=True)
        df['hours'] = df.hours.cumsum()
        df['scenario'] = scen
        duration_df = pd.concat([duration_df,df])
        
    return duration_df

def phs(labels):
        for l, label in enumerate(labels):
            if label =='PHS':labels[l]='PSH'
        return labels

    
#########################################
#%%           GET REEDS DATA 
#########################################    
    
if get_reeds_data:
    #%%
    #ReEDS Capacity
    cap_reeds_all = get_all_scen_data_reeds('cap',scenarios_base_names+[scens_name+'_Constant'],['i','r','t','cap'],agg='sum',agg_cols=['i','t'],map_tech='cat')
    cap_reeds_all_scen = get_all_scen_data_reeds('cap',scenarios_all_names,['i','r','t','cap'],agg='sum',agg_cols=['i','t'],map_tech='cat')

    cap_reeds_all = format_cap_gen(cap_reeds_all,'cap')
    cap_reeds_all_scen = format_cap_gen(cap_reeds_all_scen,'cap')

    #ReEDS Capacity all scenarios
    cap_2050_all = get_all_scen_data_reeds('cap',scenarios_all_names,['i','r','t','cap'],agg='sum',agg_cols=['i','t'],map_tech='cat')
    cap_2050_all = format_cap_gen(cap_2050_all,'cap',min_year=2050)
    
    #ReEDS Capacity by BA
    cap_reeds_ba = get_all_scen_data_reeds('cap',[scens_name+'_Ref',scens_name+'_RE100'],['i','r','t','cap'],agg='sum',agg_cols=['i','r','t'],map_tech='group')
    cap_reeds_ba = format_cap_gen(cap_reeds_ba,'cap',min_year=2050)
    
    #Firm Capacity
    firm_cap_all = get_all_scen_data_reeds('cap_firm',scenarios_base_names,['i','r','szn','t','firm_cap'],agg='sum',agg_cols=['i','szn','t'],map_tech='cat')
    firm_cap_all = format_cap_gen(firm_cap_all,'firmcap',min_year=2050)

    #ReEDS Generation
    gen_reeds_all = get_all_scen_data_reeds('gen_ann',scenarios_base_names+[scens_name+'_Constant'],['i','r','t','gen'],agg='sum',agg_cols=['i','t'],map_tech='cat')
    vre_gen_reeds_all = gen_reeds_all.loc[gen_reeds_all.i.isin(vre),:].groupby(['scenario','t',],as_index=False).sum()
    gen_reeds_all = format_cap_gen(gen_reeds_all,'gen')
    #%
    gen_reeds_all_scen = get_all_scen_data_reeds('gen_ann',scenarios_all_names,['i','r','t','gen'],agg='sum',agg_cols=['i','t'],map_tech='cat')
    gen_2050_all = format_cap_gen(gen_reeds_all_scen,'gen',min_year=2050).drop('t',1)
    gen_reeds_all_scen = format_cap_gen(gen_reeds_all_scen,'gen')
    
    #ReEDS RE Penetrations
    gen_2050_total = gen_2050_all.loc[~(gen_2050_all.i.isin(storage)),:].groupby(['scenario'],as_index=False).sum()
    re_gen_total = gen_2050_all.loc[gen_2050_all.i.isin(re),:].groupby(['scenario'],as_index=False).sum().rename(columns={'gen':'regen'})
    ce_gen_total = gen_2050_all.loc[gen_2050_all.i.isin(ce),:].groupby(['scenario'],as_index=False).sum().rename(columns={'gen':'cegen'})
    gen_2050_total = gen_2050_total.merge(re_gen_total,on=['scenario'],how='left')
    gen_2050_total = gen_2050_total.merge(ce_gen_total,on=['scenario'],how='left')
    gen_2050_total.loc[:,'repen'] = ((gen_2050_total.regen/gen_2050_total.gen) *100).round()
    gen_2050_total.loc[:,'cepen'] = ((gen_2050_total.cegen/gen_2050_total.gen) *100).round()
    gen_2050_total = gen_2050_total.merge(scenario_map,how='left',on='scenario')
    #subtract 3% from RE100 pen until we have plexos runs 
    #gen_2050_total.loc[gen_2050_total.base == 'RE100','repen'] = gen_2050_total.loc[gen_2050_total.base == 'RE100','repen']-3
    #gen_2050_total.loc[gen_2050_total.base == 'RE100','cepen'] = gen_2050_total.loc[gen_2050_total.base == 'RE100','cepen']-3

#%%
    sys_cost_base = get_system_cost(scenarios_base_names,runs_folder,'syscost_5.csv')
#    sys_cost_base = pd.read_excel(os.path.join())
    sys_cost_constant = get_system_cost([scens_name+'_Constant'],runs_folder,'syscost_5.csv')
    sys_cost_all = get_system_cost(scenarios_all_names,runs_folder,'syscost_5.csv',pivot=False)
    sys_cost_repen = sys_cost_all.merge(gen_2050_total[['scenario','repen','sens','base']],on='scenario',how='left')
    
    bulk_sys_cost_base = pd.read_excel(os.path.join(runs_folder,'report.xlsx'),sheet_name='1_Bulk System Electricity Price')
    bulk_sys_cost_base = bulk_sys_cost_base[['scenario','year','$','Net Level $']].groupby(['scenario','year']).sum().reset_index()
    dftemp = pd.DataFrame()
    for scen in bulk_sys_cost_base.scenario.unique():
        df = bulk_sys_cost_base[bulk_sys_cost_base.scenario == scen]
        df = df.merge(pd.DataFrame(dict(year=list(range(2011,2050,2)))),on='year',how='outer').sort_values('year').interpolate()
        df.scenario = scen
        dftemp = pd.concat([dftemp,df])
    
    bulk_sys_cost_base = dftemp
    
    load = get_all_scen_data_reeds('reqt_quant',scenarios_base_names,['type','Dim2','r','h','year','requirement'])
    load = load[(load.scenario.str.contains('Ref')) & (load.type=='load')].copy()
    load = load[['year','requirement']].groupby('year').sum().reset_index()
    load.requirement /= 8760    
    load = load.merge(pd.DataFrame(dict(year=list(range(2011,2050,2)))),on='year',how='outer').sort_values('year').interpolate()
    
#    presys_cost_base = get_presystem_cost(scenarios_base_names)
    #%
    #ReEDS Emissions
    emissions_reeds_all = get_all_scen_data_reeds('emit_nat',scenarios_all_names,['t','emissions'])
    emissions_reeds_all = emissions_reeds_all.merge(scenario_map,on='scenario',how='left')
    temp = emissions_reeds_all.loc[emissions_reeds_all.t==2020,['scenario','sens','base']]
    temp['t'] = 2050
    emissions_reeds_2050 = emissions_reeds_all[emissions_reeds_all.t==2050].merge(temp,how = 'outer', on=['t','scenario','sens','base']).fillna(0)
    #%
    #Losses
    losses = get_all_scen_data_reeds('losses_ann',scenarios_all_names,['source','t','losses'])
    losses_2050 = losses.loc[losses.t==2050,['source','losses','scenario']]
    losses_2050 = losses_2050.loc[losses_2050.source != 'load']
    
    #RE capacity price
    cap_price = get_all_scen_data_reeds('RE_cap_price_r',[scens_name+'_RE100'],['r','szn','t','val'])
    cap_price = cap_price.loc[(cap_price.t == 2050) & (cap_price.szn != 'spri'),:]
    cap_price = cap_price.drop(['t','scenario'],1)
    cap_price = cap_price.merge(ba_szn,on=['r','szn'],how='right').fillna(0)
    
    
    #transmission capacity
    transmission_all = get_all_scen_data_reeds('tran_mi_out',scenarios_all_names,['t','type','val'],agg='sum',agg_cols=['t'])
    tran_2050 = transmission_all.loc[transmission_all.t==2050,['scenario','val']]
    #%
    aeo_data = os.path.join(project_folder,'Compare AEO 2020 to AEO 2019.xlsx')
    demand_growth = pd.read_excel(aeo_data,'Demand Growth',index_col=0).iloc[0:3]
    for i in demand_growth.index:
        demand_growth.loc[i,:] = demand_growth.loc[i,:]/demand_growth.loc[i,2020]
    demand_growth = demand_growth.loc[:,list(range(2020,2050))]

    
    ng_prices = pd.read_excel(aeo_data,'NG Prices',index_col=0).iloc[0:3]
    ng_prices = ng_prices.loc[:,list(range(2020,2050))]

    #%
    
    #get technology costs
    low_pv = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','upv_ATB_2020_advanced.csv')).loc[:,['t','capcost']].rename(columns = {'capcost':'Low PV Cost'})
    high_pv = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','upv_ATB_2020_conservative.csv')).loc[:,['t','capcost']].rename(columns = {'capcost':'High PV Cost'})
    ref_pv = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','upv_ATB_2020_moderate.csv')).loc[:,['t','capcost']].rename(columns = {'capcost':'Mid PV Cost'})
    
    low_wind = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','ons-wind_ATB_2020_advanced.csv')).rename(columns = {'Year':'t','Cap cost 1000$/MW':'Low Onshore-Wind Cost'})
    low_wind = low_wind.loc[low_wind['Wind class']==4,['t','Low Onshore-Wind Cost']]
    high_wind = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','ons-wind_ATB_2020_conservative.csv')).rename(columns = {'Year':'t','Cap cost 1000$/MW':'High Onshore-Wind Cost'})
    high_wind = high_wind.loc[high_wind['Wind class']==4,['t','High Onshore-Wind Cost']]
    ref_wind = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','ons-wind_ATB_2020_moderate.csv')).rename(columns = {'Year':'t','Cap cost 1000$/MW':'Mid Onshore-Wind Cost'})
    ref_wind = ref_wind.loc[ref_wind['Wind class']==4,['t','Mid Onshore-Wind Cost']]
    
    low_wind_off = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','ofs-wind_ATB_2020_advanced.csv')).rename(columns = {'Year':'t','Cap cost 1000$/MW':'Low Offshore-Wind Cost'})
    low_wind_off = low_wind_off.loc[low_wind_off['Wind class']==3,['t','Low Offshore-Wind Cost']]
    high_wind_off = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','ofs-wind_ATB_2020_conservative.csv')).rename(columns = {'Year':'t','Cap cost 1000$/MW':'High Offshore-Wind Cost'})
    high_wind_off = high_wind_off.loc[high_wind_off['Wind class']==3,['t','High Offshore-Wind Cost']]
    ref_wind_off = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','ofs-wind_ATB_2020_moderate.csv')).rename(columns = {'Year':'t','Cap cost 1000$/MW':'Mid Offshore-Wind Cost'})
    ref_wind_off = ref_wind_off.loc[ref_wind_off['Wind class']==3,['t','Mid Offshore-Wind Cost']]
    
    low_storage = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','battery_ATB_2020_advanced.csv')).rename(columns = {'capcost':'Low Storage Cost'})
    low_storage = low_storage.loc[low_storage['i']=='battery_4',['t','Low Storage Cost']]
    high_storage = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','battery_ATB_2020_conservative.csv')).rename(columns = {'capcost':'High Storage Cost'})
    high_storage = high_storage.loc[high_storage['i']=='battery_4',['t','High Storage Cost']]
    ref_storage = pd.read_csv(os.path.join(reeds_inputs,'plant_characteristics','battery_ATB_2020_moderate.csv')).rename(columns = {'capcost':'Mid Storage Cost'})
    ref_storage = ref_storage.loc[ref_storage['i']=='battery_4',['t','Mid Storage Cost']]
    
    pv_costs = ref_pv.merge(low_pv,on='t',how='left')
    pv_costs = pv_costs.merge(high_pv,on='t',how='left')
    pv_costs = pv_costs.loc[pv_costs.t.isin(range(2020,2050))]
    pv_costs.index = pv_costs.t
    pv_costs = pv_costs.drop('t',1)
    pv_costs = pv_costs.T
    
    
    wind_costs = ref_wind.merge(low_wind,on='t',how='left')
    wind_costs = wind_costs.merge(high_wind,on='t',how='left')
    wind_costs = wind_costs.loc[wind_costs.t.isin(range(2020,2050))]
    wind_costs.index = wind_costs.t
    wind_costs = wind_costs.drop('t',1)
    wind_costs = wind_costs.T


    off_wind_costs = ref_wind_off.merge(low_wind_off,on='t',how='left')
    off_wind_costs = off_wind_costs.merge(high_wind_off,on='t',how='left')
    off_wind_costs = off_wind_costs.loc[off_wind_costs.t.isin(range(2020,2050))]
    off_wind_costs.index = off_wind_costs.t
    off_wind_costs = off_wind_costs.drop('t',1)
    off_wind_costs = off_wind_costs.T
    
    battery_costs = ref_storage.merge(low_storage,on='t',how='left')
    battery_costs = battery_costs.merge(high_storage,on='t',how='left')
    battery_costs = battery_costs.loc[battery_costs.t.isin(range(2020,2050))]
    battery_costs.index = battery_costs.t
    battery_costs = battery_costs.drop('t',1)
    battery_costs = battery_costs.T
    
    ng_price_natnl = get_all_scen_data_reeds('repgasprice_nat', scenarios_base_names, ['t','price'])
    ng_price_natnl.price = ng_price_natnl.price / pd.read_csv(os.path.join(reeds_inputs,'deflator.csv'),index_col='*Dollar.Year').loc[2019,'Deflator']
    #%%
    
   #save out data if the option is turned on
    if save_reeds:
        cap_reeds_all.to_csv(os.path.join(dir_out,'cap_all_scen.csv'),index=False)
        gen_reeds_all.to_csv(os.path.join(dir_out,'gen_all_scen.csv'),index=False)
        gen_2050_total.to_csv(os.path.join(dir_out,'REpen_all_scen.csv'),index=False)
        sys_cost_all.to_csv(os.path.join(dir_out,'sys_cost_all_scen.csv'),index=False)
        emissions_reeds_all.to_csv(os.path.join(dir_out,'emissions_reeds_all.csv'),index=False)
        firm_cap_all.to_csv(os.path.join(dir_out,'firm_cap_all.csv'),index=False)
        losses.to_csv(os.path.join(dir_out,'losses_all.csv'),index=False)
        cap_price.to_csv(os.path.join(dir_out,'cap_price.csv'),index=False)
        tran_2050.to_csv(os.path.join(dir_out,'transmission_all_scenarios.csv'),index=False)

#########################################
#%%           GET PLEXOS DATA 
#########################################   
if get_plexos_data:
    cap_plexos =            get_all_scen_data_plexos('capacity',scenarios_base,2050)
    gen_plexos =            get_all_scen_data_plexos('generation',scenarios_base,2050)
    curtailment_plexos =    get_all_scen_data_plexos('curtailment',scenarios_base,2050)
    reserveProvison_plexos= get_all_scen_data_plexos('reserve_provision_by_gen',scenarios_base,2050)
    load_plexos =           get_all_scen_data_plexos('load',scenarios_base,2050)
    storageLoad_plexos =    get_all_scen_data_plexos('storage_load',scenarios_base,2050)
    transloss_plexos =      get_all_scen_data_plexos('transloss',scenarios_base,2050)
    regions_map_plexos =    get_all_scen_data_plexos('relations_region_generators',scenarios_base,2050)
    
        
#########################################
#%%           CREATE FIGURES
######################################### 
        
if plot_data:


#%% 1. System cost and marginal CO2 abatement cost bar plot

    emit_temp = emissions_reeds_all.copy()
    emit_temp = emit_temp.loc[emit_temp.scenario.isin(scenarios_base_names),:]
    emit_temp = emit_temp.loc[emit_temp.t >= 2020,:]
    new_df = pd.DataFrame()
    for scen in emit_temp.scenario.unique():
        df_temp = emit_temp[emit_temp.scenario==scen]
        odds=pd.DataFrame(dict(t=range(2021,2050,2)))
        odds['sens'] = df_temp.sens.unique()[0]
        odds['base'] = df_temp.base.unique()[0]
        odds['scenario'] = scen
        
        df_temp = pd.concat([df_temp,odds]).sort_values('t').set_index('t')
        df_temp.emissions = df_temp.emissions.interpolate()
#        df_temp.set_index('t',inplace=True)
        
        for year in list(range(int(df_temp.index[-1])+1,2070)):
            if 'RE100' in scen:
                df_temp.loc[year] = df_temp.iloc[-1]
                df_temp.loc[year,'emissions'] = 0
            else:
                df_temp.loc[year] = df_temp.loc[2050]
                
        df_temp.reset_index(inplace=True)
        new_df = pd.concat([new_df,df_temp])
        
        
    emit_temp = new_df.sort_values(['scenario','t'])
    emit_temp.loc[(emit_temp.t==2049) & (emit_temp.scenario.str.contains('RE100')),'emissions']  = np.mean([emit_temp.loc[(emit_temp.t==2048) & emit_temp.scenario.str.contains('RE100'),'emissions'].values[0],0])
    emit_temp.loc[:,'emissions'] = emit_temp.loc[:,'emissions'] / (1.05**(emit_temp.loc[:,'t']-2020))

    emit_temp = emit_temp.groupby('scenario',as_index=False).sum().drop('t',1)
    
    for i in emit_temp.scenario:
        emit_temp.loc[emit_temp.scenario==i,'sys_cost'] = sys_cost_base.loc[:,i].sum()
    
    emit_temp.index = emit_temp.scenario        
    emit_temp = emit_temp.reindex(scenarios_base_names)#.reset_index()
    emit_temp.loc[:,'sys_cost_diff'] = emit_temp.sys_cost.diff()
    emit_temp.loc[:,'marginal_emissions'] = emit_temp.emissions.diff(-1) 
    emit_temp.loc[:,'marginal_emissions'] = emit_temp.loc[:,'marginal_emissions'].shift(1)

    emit_temp = emit_temp.fillna(0)
    emit_temp.loc[:,'abatement_cost'] = ((emit_temp.sys_cost_diff)/(emit_temp.marginal_emissions)) * 1000 
    emit_temp = emit_temp.reset_index(drop=True).drop(0)
    #%%
    
    fsize=12
    fig, ax = plt.subplots(nrows=1,ncols=2, figsize = (12,6))
    bottom = np.zeros(len(sys_cost_base.columns))
    count = 0
    abbreviation_dict['Capital no ITC'] = 'Capital'
    for cost_cat in sys_cost_base.index:
        if cost_cat == 'Other':
            continue
        ax[0].bar(sys_cost_base.loc[cost_cat,:].index.to_list(),sys_cost_base.loc[cost_cat,:].values,label=abbreviation_dict[cost_cat],bottom=bottom,color = cpal[count])
        bottom+=sys_cost_base.loc[cost_cat,:]
        count += 1

    ax[1].plot([57,80,90,95,97,99,100],[0] + emit_temp.abatement_cost.to_list(),marker='o')
    ax[1].set_ylabel('Levelized Incremental CO$_2$\nAbatement Cost ($/tonne)',fontsize = axislabels)
    ax[1].set_xlabel('RE Requirement (%)',fontsize = axislabels)
    ax[1].grid()
    
    
    ax[0].set_xticklabels([scenario_labels[i] for i in scenarios_base],fontsize = ticklabels, rotation = 40 )
    ax[0].set_ylabel('System Cost (Billion $)',fontsize = axislabels,labelpad=10)
    handles, labels = ax[0].get_legend_handles_labels()
    ax[0].legend(handles,labels,frameon=False,loc = 'upper center',ncol=4,fontsize=legend_small,bbox_to_anchor=(.5,-0.15))
    fig.tight_layout(w_pad=0.0)
#             
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'system_cost_bar_plot.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'system_cost_bar_plot.png'),bbox_inches='tight',dpi=300)    

    else:
        plt.show()
        
#%% metric ton abatement cost
    #!!!!
    emit_temp = emissions_reeds_all.copy()
    emit_temp = emit_temp.loc[emit_temp.t >= 2020,:]
        
    emit_temp = process_emissions(emit_temp)#new_df.sort_values(['scenario','t'])
#    emit_temp.loc[(emit_temp.t==2049) & (emit_temp.scenario.str.contains('RE100')),'emissions']  = np.mean([emit_temp.loc[(emit_temp.t==2048) & emit_temp.scenario.str.contains('RE100'),'emissions'].values[0],0])
    emit_temp.loc[:,'emissions'] = emit_temp.loc[:,'emissions'] / (1.05**(emit_temp.loc[:,'t']-2020))
    emit_temp = emit_temp.groupby(['scenario','base'],as_index=False).sum().drop('t',1)
    
    sys_cost_temp = sys_cost_all.copy()
    sys_cost_temp = sys_cost_temp[['disc_5','scenario']].groupby(['scenario']).sum().reset_index()
    emit_temp = emit_temp.merge(sys_cost_temp[['scenario','disc_5']],on=['scenario'])
    emit_temp = emit_temp.merge(requirement,on='base',how='left')
    emit_temp = emit_temp.merge(scenario_map[['sens','scenario']], on = 'scenario',how='left')
#    emit_temp.sort_values(['sens','Requirement'],inplace=True)
    cost_temp = emit_temp.pivot(index='Requirement',columns='sens',values='disc_5').diff().dropna() 
    emit_temp = emit_temp.pivot(index='Requirement',columns='sens',values='emissions').diff(-1).shift(1).dropna()
    
    abatement = cost_temp*1e9/(emit_temp*1e6)
    
    repen_temp = sys_cost_repen.copy()
    repen_temp = repen_temp[['sens','repen']].groupby('sens').max()
    bluetechs = repen_temp[repen_temp.repen < 99].index.to_list()
    
    
#%%
    w = 5
    h = w*5/8
    fig, ax = plt.subplots(1,1,figsize=(w,h))
    bluelabel=True
    greylabel=True
    style='--'
    for sen in abatement.columns:
        if sen in bluetechs:
            seriesColor = 'dodgerblue'
            seriesLabel=None
            order=19
            if bluelabel:
                seriesLabel='Sensitivities that do not reach 100% RE'
                bluelabel=False
                
        elif sen == 'Base':
            seriesColor = 'gold'
            seriesLabel='Base Case'
            order=20
            style='solid'
            
        else:
            seriesColor = '#6f6f6f'
            seriesLabel=None
            order=1
            if greylabel:
                seriesLabel = 'Sensitivities that reach 100% RE'
                greylabel=False
                
        ax.plot(abatement.index.astype(int), abatement[sen],ls=style, marker='o', markersize=5, color=seriesColor, label=seriesLabel,zorder=order)
        style='--'
        labelme=False
    ax.set_ylabel('Abatement Cost ($/tonne)', fontsize=12)
    ax.set_xlabel('Penetration Requirement (%)', fontsize=12)
    ax.set_xticks(list(range(80,101,5)))
    ax.annotate(scenario_labels[ abatement.T.loc[abatement.T[99]==abatement.loc[99,:].max(),99].index[0]],
                (99,abatement.loc[99,:].max()),
                xycoords='data',
                xytext = (95,2100),
                arrowprops=dict(arrowstyle='->'))
    ax.grid()
    fig.legend(frameon=False,loc='center left',bbox_to_anchor=(1,0.5))
#    fig.tight_layout()
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'abatement_vs_repen.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'abatement_vs_repen.png'),bbox_inches='tight',dpi=300)
        abatement.rename(columns=scenario_labels).T.to_csv(os.path.join(dir_fig_out,'abatement_vs_repen.csv'))

    else:
        plt.show()
    
#%%1. System cost and marginal CO2 abatement cost bar plot for SI

    emit_temp = emissions_reeds_all.copy()
    emit_temp = emit_temp.loc[emit_temp.t >= 2020,:]
    emit_temp = process_emissions(emit_temp)
#    for scen in emit_temp.scenario.unique():
#        df_temp = emit_temp[emit_temp.scenario == scen].set_index('t',drop=True)
#        columns = emit_temp.columns.to_list()
#        common = df_temp.loc[2020,['sens','base']].to_list()
#        odds=[]
#        for y in df_temp.iloc[0:-1].index.to_list():
#            emissions = np.mean([df_temp.loc[y,'emissions'],df_temp.loc[y+2,'emissions']])
#            odds.append( [y+1,emissions,scen]+common)
#        if df_temp.index.max() < 2050:
#            emissions = np.mean([df_temp.loc[df_temp.index.max(),'emissions'],0.])
#            odds.append([df_temp.index.max(),emissions,scen]+common)
#        df_temp = pd.DataFrame(columns=columns,data=odds)
#        concatMe = [emit_temp,df_temp]
#        emit_temp = pd.concat(concatMe).reset_index(drop=True)
        
#    emit_temp.loc[(emit_temp.base=='RE100')&(emit_temp.t==2050),'emissions'] = emit_temp.loc[(emit_temp.base=='RE90')&(emit_temp.t==2050),'emissions'] * .3
    emit_2 = emit_temp.copy()
    emit_8 = emit_temp.copy()
    
    emit_temp.loc[:,'emissions_5']    = emit_temp.loc[:,'emissions'] / (1.05**(emit_temp.loc[:,'t']-2020))
    emit_temp.loc[:,'emissions_2']  = emit_temp.loc[:,'emissions'] / (1.02**(emit_temp.loc[:,'t']-2020))
    emit_temp.loc[:,'emissions_8'] = emit_temp.loc[:,'emissions'] / (1.08**(emit_temp.loc[:,'t']-2020))
    
    emissions_group = ['emissions_5','emissions_2','emissions_8']
    marginal_group = ['marginal_emissions_5','marginal_emissions_2','marginal_emissions_8']

    emit_temp = emit_temp.groupby(['scenario','base'],as_index=False).sum().drop('t',1)
    emit_temp = emit_temp.loc[emit_temp.scenario.isin(scenarios_base_names),:]
    
    for i in emit_temp.scenario:
        emit_temp.loc[emit_temp.scenario==i,'sys_cost'] = sys_cost_base.loc[:,i].sum()
    
    emit_temp.index = emit_temp.scenario        
    emit_temp = emit_temp.reindex(scenarios_base_names)#.reset_index()
    emit_temp.loc[:,'sys_cost_diff'] = emit_temp.sys_cost.diff()
    emit_temp.loc[:,'marginal_emissions_5'] = emit_temp['emissions_5'].diff(-1) 
    emit_temp.loc[:,'marginal_emissions_2'] = emit_temp['emissions_2'].diff(-1)    
    emit_temp.loc[:,'marginal_emissions_8'] = emit_temp['emissions_8'].diff(-1) 
    
    emit_temp.loc[:,'marginal_emissions_5'] = emit_temp.loc[:,'marginal_emissions_5'].shift(1)
    emit_temp.loc[:,'marginal_emissions_2'] = emit_temp.loc[:,'marginal_emissions_2'].shift(1)
    emit_temp.loc[:,'marginal_emissions_8'] = emit_temp.loc[:,'marginal_emissions_8'].shift(1)

    emit_temp = emit_temp.fillna(0)
    abatement_cost_group = ['abatement_cost_5','abatement_cost_2','abatement_cost_8']
    emit_temp.loc[:,'abatement_cost_5'] = ((emit_temp.sys_cost_diff)/(emit_temp['marginal_emissions_5'])) *1000
    emit_temp.loc[:,'abatement_cost_2'] = ((emit_temp.sys_cost_diff)/(emit_temp['marginal_emissions_2'])) *1000    
    emit_temp.loc[:,'abatement_cost_8'] = ((emit_temp.sys_cost_diff)/(emit_temp['marginal_emissions_8'])) *1000
    
    emit_error = pd.DataFrame(columns=['minus'], data=emit_temp['abatement_cost_5'] - emit_temp['abatement_cost_2'])
    emit_error['plus'] = emit_temp['abatement_cost_5'] - emit_temp['abatement_cost_8']
    
    emit_temp = emit_temp.reset_index(drop=True).drop(0)
#    emit_temp['label'] = scenario_labels[]
    
    sys_cost_base_2 = pd.read_csv('{}\\syscost_2.csv'.format(runs_folder)).fillna(0)
    sys_cost_base_8 = pd.read_csv('{}\\syscost_8.csv'.format(runs_folder)).fillna(0)
    
    sys_cost_base_2 = sys_cost_base_2.pivot(index='cost_cat',columns='scenario',values='Discounted Cost (Bil $)')
    sys_cost_base_2 = sys_cost_base_2[sys_cost_base.columns]
    
    sys_cost_base_8 = sys_cost_base_8.pivot(index='cost_cat',columns='scenario',values='Discounted Cost (Bil $)')
    sys_cost_base_8 = sys_cost_base_8[sys_cost_base.columns]
    
    sys_cost_err = pd.DataFrame(index=['Ref 57%','80%','90%','95%','99%','97%','100%'],columns=['No Discount','5% Discount','10% Discount'])
    
    sys_cost_err['2% Discount']  = sys_cost_base_2.sum().values * 100 / sys_cost_base_2.sum()[0]
    sys_cost_err['5% Discount']  = sys_cost_base.sum().values * 100 / sys_cost_base.sum()[0]
    sys_cost_err['8% Discount'] = sys_cost_base_8.sum().values * 100 / sys_cost_base_8.sum()[0]
    
#    sys_cost_err['No Discount']  = ( - sys_cost_base.iloc[:,0].sum() + sys_cost_base_0.sum().values) *100/sys_cost_base.iloc[:,0].sum()
#    sys_cost_err['5% Discount']  = ( - sys_cost_base.iloc[:,0].sum() + sys_cost_base.sum().values)   *100/sys_cost_base.iloc[:,0].sum()
#    sys_cost_err['10% Discount'] = ( - sys_cost_base.iloc[:,0].sum() + sys_cost_base_10.sum().values)*100/sys_cost_base.iloc[:,0].sum()
#    
#
    sys_cost_err -= 100
    sys_cost_err['minus']=sys_cost_err['5% Discount']-sys_cost_err[['2% Discount','8% Discount']].min(1)
    sys_cost_err['plus']=sys_cost_err['5% Discount']-sys_cost_err[['2% Discount','8% Discount']].max(1)

   
   
    
    
    
    #%% SI 2X2 Cost figure
    
    fsize=12
    fig, ax = plt.subplots(nrows=2,ncols=1, figsize = (6,7.5),sharex=True)
    ax = ax.ravel()
    bottom = np.zeros(len(sys_cost_base.columns))
    count = 0
#    for cost_cat in sys_cost_base.index:
#        if cost_cat == 'Other':
#            continue
#        ax[0].bar(sys_cost_base.columns,sys_cost_base.loc[cost_cat,:],label=abbreviation_dict[cost_cat],bottom=bottom,color = cpal[count])
#        bottom+=sys_cost_base.loc[cost_cat,:]
#        count += 1
    
    ax[0].bar(sys_cost_err.index[1:], sys_cost_err['5% Discount'].values[1:],yerr=abs(sys_cost_err[['minus','plus']].T.values[:,1:]),
      error_kw=dict(lw=2,
                    capsize=5,
                    capthick=2)
      )
      
    ax[0].set_ylabel('Difference in\nSystem Cost (%)', fontsize = axislabels)
    
    ax[0].set_xticklabels(sys_cost_err.index[1:],fontsize=ticklabels,rotation=40,ha='right')
#    ax[0].set_xticks([])
    
    
    ax[1].bar(emit_temp.scenario,emit_temp.abatement_cost_5, yerr=abs(emit_error.dropna().T.values),
      error_kw=dict(lw=2,
                    capsize=5,
                    capthick=2)
      )
    ax[1].set_xticklabels([scenario_labels[i] for i in scenarios_base[1:]],fontsize = ticklabels ,rotation=40,ha='right')
    ax[1].set_ylabel('Levelized CO$_2$ Abatement Cost\nBetwen Scenarios ($/tonne)',fontsize = axislabels)
    ymax = 1400
    ax[1].set_ylim(0,ymax)
    
    
    
#    ax[0].set_xticklabels([scenario_labels[i] for i in scenarios_base], fontsize = ticklabels ,rotation=40,ha='right')
##    ax[0].set_xlabel('Scenario',fontsize = axislabels,labelpad=10)
#    ax[0].set_ylabel('System Cost (billion $)',fontsize = axislabels,labelpad=10)
#    handles, labels = ax[0].get_legend_handles_labels()
#    #handles, labels = reverse_legend(handles,labels)
#    ax[0].legend(handles,labels,frameon=False,loc = 'upper center',ncol=4,fontsize=legend_small,bbox_to_anchor=(0.5,-0.23))
    
#    ax[3].text(-.15,50,int((emit_temp.loc[emit_temp.base=='RE80','abatement_cost_5']).round(0)[1]),fontsize=fsize,fontweight='bold')
#    ax[3].text(.9,70,int((emit_temp.loc[emit_temp.base=='RE90','abatement_cost_5']).round(0)[2]),fontsize=fsize,fontweight='bold')
#    ax[3].text(1.9,100,int((emit_temp.loc[emit_temp.base=='RE100','abatement_cost_5']).round(0)[3]),fontsize=fsize,fontweight='bold')
#    ax[3].text(2.8,1330,int((emit_temp.loc[emit_temp.base=='RE100','abatement_cost_5']).round(0)[4]),fontsize=fsize,fontweight='bold')
    ax[1].text(5,ymax,'^',fontsize=fsize+10, fontweight='bold',ha='center',va='top')
    ax[1].text(5,ymax,'  Max: {}'.format(str(abs(emit_error.loc[:,'plus'].values[-1].round()) + emit_temp.loc[emit_temp.base=='RE100','abatement_cost_5'].values[-1].round())[0:-2]),ha='center',va='bottom')
#    
#    ax[2].bar(emit_temp.base,emit_temp.emissions_5)
#    ax[2].set_ylabel('Cumulative Emissions (million\ntonne, discounted)',fontsize=axislabels)
#    ax[2].set_xticklabels([scenario_labels[i] for i in emit_temp.base], fontsize = ticklabels , rotation= 40,ha='right')
    
    fig.tight_layout(h_pad=0.0,w_pad=-1)
#             
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'system_cost_bar_plot_SI.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'system_cost_bar_plot_SI.png'),dpi=300,bbox_inches='tight')    

    else:
        plt.show()
        
    #%% Marginal requirement cost
    sys_cost_temp = sys_cost_base.copy()
    
    gen_temp = gen_reeds_all.copy()
    gen_temp = gen_temp[gen_temp.i.isin(re_techs)==True]
    gen_temp = gen_temp[['t','gen','scenario']].groupby(['t','scenario']).sum().reset_index()
    
    losses_temp = losses.copy()
    losses_temp = losses_temp[losses_temp.source.isin(['STORAGE','trans'])]
    losses_temp = losses_temp.groupby(['t','scenario']).sum()
    
#    vre_temp = vre_gen_reeds_all.copy()
    
    gen_temp = gen_temp.merge(scenario_map, on='scenario', how='left')
    losses_temp = losses_temp.merge(scenario_map, on='scenario', how='left')
    
    gen_temp = gen_temp[gen_temp.sens=='Base']    
    losses_temp = losses_temp[losses_temp.sens=='Base']
    
    for scen in gen_temp.scenario.unique():
        odds = pd.DataFrame(data={'t':list(range(2021,2050,2))})
        odds['scenario'] = scen        
        gen_temp = pd.concat([gen_temp,odds],sort=False)

    gen_temp.sort_values(['scenario','t'],inplace=True)
    gen_temp=gen_temp[['t','scenario','gen']]
    gen_temp.interpolate(inplace=True)
    
    for scen in losses_temp.scenario.unique():
        odds = pd.DataFrame(data={'t':list(range(2021,2050,2))})
        odds['scenario'] = scen        
        losses_temp = pd.concat([losses_temp,odds],sort=False)

    losses_temp.sort_values(['scenario','t'],inplace=True)
    losses_temp=losses_temp[['t','scenario','losses']]
    losses_temp.interpolate(inplace=True)
    
    gen_temp = gen_temp.groupby('scenario').sum()  
    losses_temp = losses_temp.groupby('scenario').sum()
    
    gen_temp.gen = gen_temp.gen - losses_temp.losses
    gen_temp.loc['{}_RE100'.format(scens_name),'gen'] *= 0.97
#    gen_temp['vre']=vre_temp.gen
    
    gen_temp['sys_cost']=sys_cost_temp.sum()
    gen_temp = gen_temp.merge(scenario_map,on='scenario',how='left')
    gen_temp = gen_temp.merge(requirement, on='base',how='left')
    gen_temp.sort_values('Requirement',inplace=True)
    gen_temp.gen *= gen_temp.Requirement/100
    gen_temp['Dre']=gen_temp.gen.diff()
    gen_temp['Dcost']=gen_temp.sys_cost.diff()
    
    gen_temp['levelized_requirement']=gen_temp.Dcost*1e9/gen_temp.Dre
    gen_temp.dropna(inplace=True)
 #%%
    
    fig, ax = plt.subplots(1,1,figsize=(5,3))
    
    ax.bar(gen_temp.Requirement.astype(str),gen_temp.levelized_requirement)
    ax.set_ylim(0,140)
    for tic, bar in enumerate(gen_temp.levelized_requirement.values):
        ax.text(tic,bar+1,'${}'.format(int(round(bar))),ha='center',va='bottom',weight='bold')
        
    ax.set_ylabel('Levelized Cost of Additional\nRenewable Energy ($/MWh)',fontsize=12)
    ax.set_xlabel('Change in Renewable Energy Requirement',fontsize=12)
    ax.set_xticklabels(['57 → 80%','80 → 90%','90 → 95%','95 → 97%','97 → 99%','99 → 100%'],rotation=40,ha='right')
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'incremental_levlized_RE_cost.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'incremental_levlized_RE_cost.png'),dpi=300,bbox_inches='tight')    

    else:
        plt.show()
        
    #%% 2. 6 panel cap and gen bar plot
    
    #
    plt.close()
    fig, ax = plt.subplots(nrows=5,ncols=2,figsize = (12,20))
    for n,s in enumerate(scenarios_short_names):
        
        cap_temp = format_capgen_for_plotting(cap_reeds_all_scen,'cap',subset=s)
        
        bottom = np.zeros(len(cap_temp.columns))
        for i in cap_temp.index:
            ax[n][0].bar(cap_temp.columns,cap_temp.loc[i,:]/1e3,label=i,bottom=bottom,color=tech_colors.loc[tech_colors.order==i,'color'].values[0],width=1.8)
            bottom += cap_temp.loc[i,:].values/1e3
            ax[n][0].set_ylim([0,3.5e3])
            ax[n][0].tick_params(axis='both', which='major', labelsize=ticklabels-3)

            
        gen_temp = format_capgen_for_plotting(gen_reeds_all,'gen',subset=s)

        bottom2 = np.zeros(len(gen_temp.columns))
        for i in gen_temp.index:
            ax[n][1].bar(gen_temp.columns,gen_temp.loc[i,:]/1e6,label=i,bottom=bottom2,color=tech_colors.loc[tech_colors.order==i,'color'].values[0],width=(1.8))
            bottom2 += gen_temp.loc[i,:].values/1e6
            ax[n][1].set_xticks(list(range(2020,2060,10)))
            ax[n][1].set_xticklabels(list(range(2020,2060,10)))            
            ax[n][1].set_ylim([0,5.6e3])
            ax[n][1].tick_params(axis='both', which='major', labelsize=ticklabels-3)
            
        if n < len(scenarios_short_names)-1:
            ax[n][0].set_xticks([])
            ax[n][1].set_xticks([])

        ax[n][0].set_ylabel(scenario_labels[scenarios_short[n]],fontsize=axislabels)
        
    # Remove x ticks and spines
#    ax[0][0].set_xticks([])
#    ax[1][0].set_xticks([])
#    ax[0][1].set_xticks([])
#    ax[1][1].set_xticks([])
#    ax[0][1].set_yticks([])
#    ax[1][1].set_yticks([])
#    ax[2][1].set_yticks([])
    
    ax[0][0].set_title('Capacity (GW)',fontsize=axislabels)
    ax[0][1].set_title('Generation (TWh)',fontsize=axislabels)
        
    handles, labels = ax[2][0].get_legend_handles_labels()
    handles, labels = reverse_legend(handles,labels)
    
    
    fig.legend(handles,phs(labels),frameon=False,fontsize = legend, loc='center right')#,bbox_to_anchor=(.955,.45))
    fig.subplots_adjust(hspace=0.06,wspace=0.15,right=.75)
 
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'cap_gen_bar_plot.svg'),bbox_inches='tight')    
        plt.savefig(os.path.join(dir_fig_out,'cap_gen_bar_plot.png'),bbox_inches='tight')    

    else:
        plt.show()
        

  #%%  fig 3. Firm capacity bar and cap price map 3x2 panel
    
    # Import BA data and project it
    gis_n, gis_centroid_n = read_ba_usa()
    gis_n = project(gis_n, 'lat', 'long')
    gis_centroid_n = project(gis_centroid_n, 'lat', 'long')
    centroids = gis_centroid_n.set_index('id')
    
    fig, ax = plt.subplots(nrows=2,ncols=1,figsize = (5,12))
    
    for n,s in enumerate(firm_cap_all.szn.unique()[1:]):
        
        firm_cap_temp = format_capgen_for_plotting(firm_cap_all,'firm_cap',subset_col='szn',subset=s,pivot_cols='scenario')
        firm_cap_temp = firm_cap_temp[scenarios_base_names ]
        
        bottom = np.zeros(len(firm_cap_temp.columns))
        for i in firm_cap_temp.index:
            ax[n].bar(firm_cap_temp.columns,firm_cap_temp.loc[i,:]/1000,label=i,bottom=bottom,color=tech_colors.loc[tech_colors.order==i,'color'].values[0],width=.8)
            bottom += firm_cap_temp.loc[i,:]/1000
        
        cap_price_temp = cap_price.loc[cap_price.szn==s,:].reset_index(drop=True)
        cap_price_temp.loc[:,'val'] = cap_price_temp.loc[:,'val']/1000
        # Plotting options
        linewidth = 10

#        ax[n].set_ylim([0,1200])
        ax[n].tick_params(axis='both', which='major', labelsize=ticklabels)
        
    ax[0].set_xticks([])
    #ax[1].set_xticks([])
    ax[1].set_xticklabels([scenario_labels[i] for i in scenarios_base],fontsize = ticklabels ,rotation=40,ha='right')
    ax[0].set_ylabel('Summer\nFirm Capacity (GW)', fontsize=axislabels)
    ax[1].set_ylabel('Winter\nFirm Capacity (GW)', fontsize=axislabels)
    


    handles, labels = ax[0].get_legend_handles_labels()
    handles, labels = reverse_legend(handles,labels)
    fig.legend(handles,phs(labels),frameon=False,fontsize = legend, loc='center left',bbox_to_anchor=(1.15,.42))
    fig.subplots_adjust(wspace=0.65,hspace = 0.09,right = .9,left=0)
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'firm_cap.svg'),bbox_inches='tight')    
        plt.savefig(os.path.join(dir_fig_out,'firm_cap.png'),bbox_inches='tight')    
    else:
        plt.show()
            
#%% 4. 2 panel losses stacked bars

    ticklabels_save = ticklabels
    legend_save = legend
    
    ticklabels=10
    axeslabels=legend=12
    
    fig, ax = plt.subplots(nrows=1,ncols=2,figsize = (8,4))
    
    losses_temp = losses_2050.copy()
    losses_temp = losses_temp.pivot(index='source',columns = 'scenario',values='losses')
    losses_temp = losses_temp[scenarios_base_names]/1e6
    
    gen_temp = gen_reeds_all_scen.loc[(gen_reeds_all_scen.i == 'Hydro') | (gen_reeds_all_scen.i == 'Geothermal')]
    gen_temp['diff'] = gen_temp['gen'].diff() / 1e6
    gen_temp = gen_temp[(gen_temp['diff'] < 0)].groupby(['t','scenario']).sum().reset_index().pivot(index='t',columns='scenario',values='diff')
    gen_temp = gen_temp[losses_temp.columns]
    for run in gen_temp.columns:
        if gen_temp.loc[2050,run] <0 : losses_temp.loc['curt',run] -= gen_temp.loc[2050,run]

    vre_gen_2050 = vre_gen_reeds_all.loc[vre_gen_reeds_all.t == 2050]#.drop(['t_x','t_y'],1)
    losses_frac = losses_2050.merge(vre_gen_2050,on='scenario',how='left')
    losses_frac.loc[:,'frac_gen'] = losses_frac.losses / losses_frac.gen
    loss_frac_temp = losses_frac.pivot(index='source',columns='scenario',values='frac_gen')
    loss_frac_temp = loss_frac_temp[scenarios_base_names]
    
    bottom = np.zeros(len(losses_temp.columns))
    count = 0
    for i in losses_temp.index:
        ax[0].bar(losses_temp.columns,losses_temp.loc[i,:],label=i,bottom=bottom,color = cpal[count])
        bottom += losses_temp.loc[i,:]
        ax[0].set_xticklabels([scenario_labels[i] for i in scenarios_base],fontsize = ticklabels,rotation=40)
        count += 1
        
    bottom = np.zeros(len(loss_frac_temp.columns))
    count = 0
    for i in loss_frac_temp.index:
        ax[1].bar(loss_frac_temp.columns,loss_frac_temp.loc[i,:]*100,label=i,bottom=bottom,color = cpal[count])
        bottom += loss_frac_temp.loc[i,:]*100
        ax[1].set_xticklabels([scenario_labels[i] for i in scenarios_base],fontsize = ticklabels,rotation=40)
        count += 1

        
    ax[0].set_ylabel('Amount (TWh)',fontsize=axislabels)
    ax[1].set_ylabel('Percent of VRE\nGeneration (%)',fontsize=axislabels)
    ax[1].set_yticks([0,5,10,15,20])
    ax[1].set_yticklabels(['0%','5%','10%','15%','20%'])
    
    handles, labels = ax[0].get_legend_handles_labels()
    handles, labels = reverse_legend(handles,labels)
    labels = ['Transmission Losses',
              'Curtialment',
              'Storage Losses']#[abbreviation_dict[q] for q in labels]

    fig.legend(handles,labels, frameon=False, fontsize = legend, loc='lower center',ncol=3,bbox_to_anchor=(.47,-0.01))
    plt.subplots_adjust(wspace=0.4)
    plt.tight_layout(rect=(0,0.02,1,1))
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'losses_sm.svg'),bbox_inches='tight')    
        plt.savefig(os.path.join(dir_fig_out,'losses_sm.png'),bbox_inches='tight',dpi=300)        
    else:
        plt.show()
        
    ticklabels = ticklabels_save
    legend = legend_save
#%% fig 5. 2 panel System cost/Repen figure and system cost diff
    
    sys_cost_repen_temp = sys_cost_repen.copy()
    for i in range(len(sys_cost_repen_temp)):
        sys_cost_repen_temp.loc[i,'label'] = int(regex.findall('\d+',scenario_labels[sys_cost_repen_temp.loc[i,'base']])[0])
#    sys_cost_repen_temp.loc[:,'repen'] = sys_cost_repen_temp.merge(gen_2050_total,on=['scenario','base'],how='left')['repen']
    reference = sys_cost_repen_temp.loc[sys_cost_repen_temp.scenario.str.contains('Ref'),:].rename(columns={'disc_5':'ref5'}).drop(['scenario','repen'],1)#,'Discounted 7%':'ref7','Discounted 3%':'ref3','cost':'costref'}).drop(['scenario','repen'],1)
    sys_cost_repen_temp = sys_cost_repen_temp.merge(reference[['ref5','sens']],on='sens',how='left')
    sys_cost_repen_temp.loc[:,'disc_5'] = 100 * (sys_cost_repen_temp.loc[:,'disc_5'] - sys_cost_repen_temp.loc[:,'ref5']) / sys_cost_repen_temp.loc[:,'ref5'] 
#    sys_cost_repen_temp.loc[:,'Discounted 3%'] = 100 * (sys_cost_repen_temp.loc[:,'Discounted 3%'] - sys_cost_repen_temp.loc[:,'ref3']) / sys_cost_repen_temp.loc[:,'ref3'] 
#    sys_cost_repen_temp.loc[:,'Discounted 7%'] = 100 * (sys_cost_repen_temp.loc[:,'Discounted 7%'] - sys_cost_repen_temp.loc[:,'ref7']) / sys_cost_repen_temp.loc[:,'ref7'] 
#    sys_cost_repen_temp.loc[:,'cost'] = 100 * (sys_cost_repen_temp.loc[:,'cost'] - sys_cost_repen_temp.loc[:,'costref']) / sys_cost_repen_temp.loc[:,'costref'] 

    dis_5 = sys_cost_repen_temp.pivot(columns='sens',index='label',values='disc_5')
    
    bars = dis_5.loc[100,:].T-dis_5.loc[100,'Base']
    bars.sort_values(inplace=True)
    bars = bars[bars.index != 'Base']
#    dis_5 = dis_5.loc[dis_5.index[::-1],:]
#    dis_3 = sys_cost_repen_temp.pivot_table(index = 'sens',columns = 'repen',values='Discounted 3%')
#    dis_7 = sys_cost_temp.pivot_table(index = 'sens',columns = 'repen',values='Discounted 7%')
#    dis_7 = sys_cost_repen_temp.pivot_table(index = 'sens',columns = 'repen',values='cost')
    
    not_100re = sys_cost_repen.copy().groupby(['sens']).max()
    not_100re = not_100re[not_100re.repen < 99]
    not_100re['label'] = None
    for i in not_100re.index:
        not_100re.loc[i,'label']=scenario_labels[i]
    
    sys_cost_diff_temp = sys_cost_repen.copy()
    sys_cost_diff_temp = sys_cost_diff_temp.loc[sys_cost_diff_temp.base=='RE100']
    sys_cost_diff_temp.loc[:,'ref'] = sys_cost_diff_temp.loc[sys_cost_diff_temp.sens=='Base','disc_5'].values[0]   
    sys_cost_diff_temp = sys_cost_diff_temp.loc[(sys_cost_diff_temp.sens != 'Base'),:]
    sys_cost_diff_temp.loc[:,'disc_5'] = 100 * (sys_cost_diff_temp.loc[:,'disc_5'] - sys_cost_diff_temp.loc[:,'ref']) / sys_cost_diff_temp.loc[:,'ref']
    sys_cost_diff_temp = sys_cost_diff_temp.pivot_table(index = 'sens',columns = 'base',values='disc_5')
    sys_cost_diff_temp = sys_cost_diff_temp.sort_values('RE100',ascending=False)
    
    emit_temp = emissions_reeds_all.copy()
    emit_temp = emit_temp.loc[(emit_temp.base=='RE100')]#&(emit_temp.sens != 'Base'),:]
    emit_temp = emit_temp.loc[(emit_temp.t >= 2020),:]
    emit_temp = process_emissions(emit_temp)
    emit_temp = emit_temp[emit_temp.t <= 2050]
    emit_temp = emit_temp.groupby(['scenario','sens','base'],as_index=False).sum().drop('t',1)
    emit_temp.loc[:,'emissions'] = emit_temp.loc[:,'emissions']- emit_temp.loc[emit_temp.sens == 'Base','emissions'].values[0]
    emit_temp = emit_temp.loc[(emit_temp.sens != 'Base'),:]
    emit_temp.index = emit_temp.sens
    emit_temp = emit_temp.reindex(sys_cost_diff_temp.index)

    fig, ax = plt.subplots(nrows=1,ncols=2,figsize=(14,5))
    sensitivitiesLabel = True
    not_100reLabel = True
    
    for s in dis_5.columns:
        df5 = dis_5[s]
#        df5 = df5.dropna(axis=0,how='all')

        if s in not_100re.index.to_list():
            if not_100reLabel: label = 'Sensitivities that do not reach 100% RE'
            ax[0].plot(df5[df5.index>60].index,df5[df5.index>60],label=label,color='dodgerblue',ls='--',marker='o',lw=0.8,zorder=19)
            label=''
            not_100reLabel = False
        else:
            if sensitivitiesLabel: label = 'Sensitivities that reach 100% RE'
            ax[0].plot(df5[df5.index>60].index,df5[df5.index>60],label=label,color='#6a6a6a',ls='--',marker='o',lw=0.8)
            label=''
            sensitivitiesLabel =False
        ax[0].grid()
        
#        count +=1
        
    ax[0].plot(dis_5[dis_5.index>60].index, dis_5.loc[dis_5.index>60,'Base'], label='Base Scenarios', color='gold', linewidth=2, ls='-', marker='o',zorder=20)
    
      
    ax2=ax[1]
    ax1=ax2.twiny()

    ax1.barh(bars.index,bars.values,label='Change in system cost')
#    ax1.barh(dis_5.loc[100,'Base'],sys_cost_diff_temp.loc[sys_cost_diff_temp.index[::-1],'RE100'],label='Change in system cost')
#    ax2 =  ax[1].twiny()


    ax2.scatter(emit_temp.loc[emit_temp.index[::-1],'emissions'],sys_cost_diff_temp.index[::-1],color='orange',label='Change in CO2 emissions')
    ax2.set_xlim([-10000,10000])
    ax2.set_xticklabels(list(range(-10000,10001,2500)),rotation = 30)
    ax1.set_xlim([-30,30])
#    ax2.axhline(0)
    ax2.set_xlabel('Cumulative CO$_2$ Emissions Difference\nfrom 100% Base Scenario (million tonnes)',fontsize=axislabels-4,labelpad=5)

    
    ax[0].set_ylabel('System Cost Increase from\nNo Requirment (%)',fontsize=axislabels,)
    ax[0].set_xlabel('Penetration Requirement (%)',fontsize=axislabels)

    ax1.set_yticklabels([scenario_labels[i] for i in sys_cost_diff_temp.index[::-1]])#,rotation='vertical')
    ax1.set_xlabel('Absolute System Cost Increase\nfrom 100% Base Scenario (%)',fontsize=axislabels-4)
#    fig.subplots_adjust(bottom=.45,top=1.2,right=1,left=0)
#    fig.tight_layout()

    pos = ax1.get_position()
    shift = 0.1
    pos.y1 += shift
    pos.x0 += shift
#    pos.x1 += shift
    pos.y0 += shift
    ax1.set_position(pos)
    ax2.set_position(pos)
    
    pos0=ax[0].get_position()
    pos0.y1 = pos.y1 - pos.y1*0.15
    pos0.y0 = pos.y0 + pos.y0*0.15
    ax[0].set_position(pos0)

    ax2.set_zorder(1)
    ax2.patch.set_visible(False)
    
#    tics = ax2.get_yticklabels()
#    for tic in tics:
#        if str(tic).split("'")[-2] in not_100re.label.values:
#            print(str(tic).split("'")[-2])
#            tic.set_color('red')
            
    tics = ax1.get_yticklabels()
    for i in range(len(tics)):
        if str(tics[i]).split("'")[-2] in not_100re.label.values:
            print(str(tics[i]).split("'")[-2])
            ax2.get_yticklabels()[i].set_color('dodgerblue')
    
    handles,labels = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend( handles+handles2, labels+labels2, frameon=False, loc='center' , ncol=2, bbox_to_anchor = (0.5,-.30))
    
    handles, labels =ax[0].get_legend_handles_labels()
    ax[0].legend(handles[::-1],labels[::-1],frameon=False, loc='center' , ncol=3, bbox_to_anchor = (0.5,-.35))
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'sys_cost_re_pen_.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'sys_cost_re_pen_.png'),bbox_inches='tight',dpi=300,transparent=True)
        dis_5.rename(columns = scenario_labels).T.to_csv(os.path.join(dir_fig_out,'sys_cost_re_pen.csv'))
    else:
        plt.show()
  
#%% SI and EXTRA FIGURES
if extra_figs:
#%% carbon abatement for all scenarios
    emit_temp = emissions_reeds_all.copy()
    emit_temp = emit_temp.loc[emit_temp.t >= 2020,:]
    for scen in emit_temp.scenario.unique():
        df_temp = emit_temp[emit_temp.scenario == scen].set_index('t',drop=True)
        columns = emit_temp.columns.to_list()
        common = df_temp.loc[2020,['sens','base']].to_list()
        odds=[]
        for y in df_temp.iloc[0:-1].index.to_list():
            emissions = np.mean([df_temp.loc[y,'emissions'],df_temp.loc[y+2,'emissions']])
            odds.append( [y+1,emissions,scen]+common)
        if df_temp.index.max() < 2050:
            emissions = np.mean([df_temp.loc[df_temp.index.max(),'emissions'],0.])
            odds.append([df_temp.index.max(),emissions,scen]+common)
        df_temp = pd.DataFrame(columns=columns,data=odds)
        concatMe = [emit_temp,df_temp]
        emit_temp = pd.concat(concatMe).reset_index(drop=True)
        
    emit_temp.loc[(emit_temp.base=='RE100')&(emit_temp.t==2050),'emissions'] = emit_temp.loc[(emit_temp.base=='RE90')&(emit_temp.t==2050),'emissions'] * .3
    emit_temp.loc[:,'emissions'] = emit_temp.loc[:,'emissions'] / (1.05**(emit_temp.loc[:,'t']-2020))

    emit_temp = emit_temp.groupby(['scenario','base'],as_index=False).sum().drop('t',1)
    
    sys_cost_temp = bulk_sys_cost_base.copy()
    sys_cost_temp = sys_cost_temp.merge(load,on='year',how='left')
    sys_cost_temp['$'] *= sys_cost_temp.requirement
    sys_cost_temp = sys_cost_temp[['year','scenario','$']].pivot(index='year',columns='scenario',values='$')
    
    for i in emit_temp.scenario:
        emit_temp.loc[emit_temp.scenario==i,'sys_cost'] = sys_cost_temp.loc[:,i].sum()
    
    emit_temp = emit_temp.set_index('base').rename(dict(requirement.values),index='base').reset_index()
    emit_temp = emit_temp.merge(scenario_map[['sens','scenario']],on='scenario',how='left')
    
    
    cost_temp = emit_temp.pivot(index='base',columns='sens',values='sys_cost')
    emit_temp = emit_temp.pivot(index='base',columns='sens',values='emissions')
    
    cost_temp = cost_temp.diff()
    emit_temp = emit_temp.diff(-1) 
    emit_temp = emit_temp.shift(1)

    emit_temp = emit_temp.fillna(0)
    marg_abatement = ((cost_temp)/(emit_temp)) * 1000 
    marg_abatement.fillna(0,inplace=True)
    
    #%%
    
    fig, ax = plt.subplots(1,1,figsize=(6.5,4))
    
    for sens in marg_abatement.columns:
        ax.plot(marg_abatement.index,marg_abatement[sens],color='grey',ls='--')
#        marg_abatement[sens].plot(ax=ax)
    
    if save_figs:
        marg_abatement.to_csv(os.path.join(dir_fig_out,'marg_abatement.csv'))
    
#%% Levelized requirement plot
    if True:
        emit_temp = emissions_reeds_all.copy()
        emit_temp = emit_temp.loc[emit_temp.t >= 2020,:]
        emit_temp = process_emissions(emit_temp)
        emit_temp = emit_temp[emit_temp.t<=2050]
#        for scen in emit_temp.scenario.unique():
#            df_temp = emit_temp[emit_temp.scenario == scen].set_index('t',drop=True)
#            columns = emit_temp.columns.to_list()
#            common = df_temp.loc[2020,['sens','base']].to_list()
#            odds=[]
#            for y in df_temp.iloc[0:-1].index.to_list():
#                emissions = np.mean([df_temp.loc[y,'emissions'],df_temp.loc[y+2,'emissions']])
#                odds.append( [y+1,emissions,scen]+common)
#            if df_temp.index.max() < 2050:
#                emissions = np.mean([df_temp.loc[df_temp.index.max(),'emissions'],0.])
#                odds.append([df_temp.index.max(),emissions,scen]+common)
#            df_temp = pd.DataFrame(columns=columns,data=odds)
#            concatMe = [emit_temp,df_temp]
#            emit_temp = pd.concat(concatMe).reset_index(drop=True)
            
        emit_temp.loc[(emit_temp.base=='RE100')&(emit_temp.t==2050),'emissions'] = emit_temp.loc[(emit_temp.base=='RE90')&(emit_temp.t==2050),'emissions'] * .3
        emit_temp.loc[:,'emissions'] = emit_temp.loc[:,'emissions'] / (1.05**(emit_temp.loc[:,'t']-2020))
    
        emit_temp = emit_temp.groupby(['scenario','base'],as_index=False).sum().drop('t',1)
        emit_temp = emit_temp.loc[emit_temp.scenario.isin(scenarios_base_names),:]
        
        for i in emit_temp.scenario:
            emit_temp.loc[emit_temp.scenario==i,'sys_cost'] = sys_cost_base.loc[:,i].sum()
        
        emit_temp.index = emit_temp.scenario        
        emit_temp = emit_temp.reindex(scenarios_base_names)#.reset_index()
        emit_temp.loc[:,'sys_cost_diff'] = emit_temp.sys_cost.diff()
        emit_temp.loc[:,'marginal_emissions'] = emit_temp.emissions.diff(-1) 
        
        emit_temp.loc[:,'marginal_emissions'] = emit_temp.loc[:,'marginal_emissions'].shift(1)
    
        emit_temp = emit_temp.fillna(0)
        emit_temp.loc[:,'abatement_cost'] = ((emit_temp.sys_cost_diff)/(emit_temp.marginal_emissions)) *1000 
        emit_temp = emit_temp.reset_index(drop=True).drop(0)
    
#%% Cap and Gen bar plot for all RE100 scenarios
    cap_temp = cap_2050_all.merge(scenario_map,on='scenario',how='left')
    cap_temp = cap_temp.loc[cap_temp.base=='RE100']
    cap_temp = format_capgen_for_plotting(cap_temp,'cap',pivot_cols='sens')
    
    gen_temp = gen_2050_all.merge(scenario_map,on='scenario',how='left')
    gen_temp = gen_temp.loc[gen_temp.base=='RE100']
    gen_temp = format_capgen_for_plotting(gen_temp,'gen',pivot_cols='sens')
    
    fig, ax = plt.subplots(nrows=2,ncols=1,figsize = (10,9))        
        
    bottom = np.zeros(len(cap_temp.columns))
    for i in cap_temp.index:
        ax[0].bar(cap_temp.columns,cap_temp.loc[i,:]/1000,label=i,bottom=bottom,color=tech_colors.loc[tech_colors.order==i,'color'].values[0],width=.8)
        bottom += cap_temp.loc[i,:]/1000

    bottom = np.zeros(len(gen_temp.columns))
    for i in gen_temp.index:
        ax[1].bar(gen_temp.columns,gen_temp.loc[i,:]/1e6,label=i,bottom=bottom,color=tech_colors.loc[tech_colors.order==i,'color'].values[0],width=.8)
        bottom += gen_temp.loc[i,:]/1e6
        
    ax[0].set_xticklabels([])
    ax[0].set_xticks([])
    ax[1].set_xticklabels([scenario_labels[i] for i in cap_temp.columns],rotation='vertical')

    ax[0].set_ylabel('Capacity (GW)',fontsize=axislabels)
    ax[1].set_ylabel('Generation (TWh)',fontsize=axislabels)
    
    fig.subplots_adjust(hspace=0.02,right = .8,left=0)

    handles, labels = ax[0].get_legend_handles_labels()
    handles, labels = reverse_legend(handles,labels)
    fig.legend(handles,phs(labels),frameon=False,fontsize = legend_small, loc='center left',bbox_to_anchor=(1.0,.5))
    fig.tight_layout()
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'all_cap_scenarios.svg'),bbox_inches='tight')    
    else:
        plt.show()
     
   
#%% Cap and Gen bar plots for all scenarios

 
    # Cap and Gen bar plot for all RE100 scenarios
    cap_temp = cap_2050_all.merge(scenario_map,on='scenario',how='left')
    gen_temp = gen_2050_all.merge(scenario_map,on='scenario',how='left')
    bases = list(cap_temp.base.unique())
    
    scenario_labels_temp = pd.DataFrame({'sens':list(scenario_labels.keys()),'label':list(scenario_labels.values())})
    scenario_map_temp = scenario_map.copy().merge(scenario_labels_temp,how='left',on='sens')
    cap_temp = cap_temp.merge(scenario_map_temp[['scenario','label']],on='scenario',how='left')
    gen_temp = gen_temp.merge(scenario_map_temp[['scenario','label']],on='scenario',how='left')
    
    base_names={'Ref' : 'Ref 57%',
                'RE80': '80%',
                'RE90' : '90%',
                'RE95' : '95%',
                'RE97' : '97%',
                'RE99': '99%',
                'RE100': '100%'}

#%% Fiure 12    

    
    fig, ax = plt.subplots(nrows=len(scenarios_base),ncols=2,figsize = (9,22))
    handles=[]
    labels=[]
    for b, scen in enumerate(scenarios_base):
        
    #    cap_temp = cap_temp.loc[cap_temp.base=='RE100']
        cap_plot = format_capgen_for_plotting( cap_temp[cap_temp.base==bases[b]], 'cap', pivot_cols='label')
        colnames = cap_plot.columns


        bottom = np.zeros(len(cap_plot.columns))
        for i in cap_plot.index:
            ax[b,0].barh(
                    cap_plot.columns,
                    cap_plot.loc[i,:].values/1000, 
                    label=i,
                    left=bottom,
                    color=tech_colors.loc[tech_colors.order==i,'color'].values[0] 
                    )
            bottom += cap_plot.loc[i,:].values/1000
        ax[b,0].set_ylabel(base_names[bases[b]]+'\n ',fontsize=15)
        ax[b,0].set_xlim(0,4000)
        ax[b,0].set_yticklabels(cap_plot.columns,fontsize=9)
        
        
        gen_plot = format_capgen_for_plotting(gen_temp[gen_temp.base==bases[b]],'gen',pivot_cols='label')
        colnames = gen_plot.columns
        bottom = np.zeros(len(gen_plot.columns))
        for i in gen_plot.index:
            ax[b,1].barh(gen_plot.columns,
              gen_plot.loc[i,:].values/1e6,
              label     = i,
              left      = bottom,
              color     = tech_colors.loc[tech_colors.order==i,'color'].values[0]
              )
            
            bottom += gen_plot.loc[i,:].values/1e6
        ax[b,1].set_yticklabels([])
        ax[b,1].set_xlim(0,6250)
        
        handles_cap, labels_cap = ax[b,0].get_legend_handles_labels()
        handles_gen, labels_gen = ax[b,1].get_legend_handles_labels()
        
        for label, handle in zip(labels_cap, handles_cap):
            if label not in labels:
                labels.append(label)
                handles.append(handle)
        
        for label, handle in zip(labels_cap, handles_cap):
            if label not in labels:
                labels.append(label)
                handles.append(handle)
        
        
        if b != len(scenarios_base)-1:
            ax[b,0].set_xticklabels([])
            ax[b,0].set_xticks([])
            ax[b,1].set_xticklabels([])
            ax[b,1].set_xticks([])
            
#        if b==0:
#            ax[b,0].set_title('Capacity',fontsize='15')
#            ax[b,1].set_title('Generation',fontsize='15')
            
#        if b==max(list(range(5))):
        ax[-1,0].set_xlabel('Capacity (GW)',fontsize=15)
        ax[-1,1].set_xlabel('Generation (TWh)',fontsize=15)
    
    legend_dict = {}    
    for handle, label in zip(handles,labels):
        legend_dict[label]=handle
        
   
    
    sens = scenario_map.sort_values(['base','sens']).loc[:,'sens'].to_list()
    base = scenario_map.sort_values(['base','sens']).loc[:,'base'].to_list()

    


#    handles, labels = ax[2,0].get_legend_handles_labels()
#    handles, labels = reverse_legend(handles,labels)
    handles=[]
    labels=[]
    for label in tech_colors.order.to_list():
        if label in list(legend_dict.keys()):
            handles.append(legend_dict[label])
            labels.append(label)
    fig.legend(handles,phs(labels),frameon=False,fontsize = legend_small, loc='center left',bbox_to_anchor=(1.05,.5))
    
#    fig.tight_layout(h_space=0)
    fig.subplots_adjust(wspace=0.06,hspace=0)    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'cag_gen_bar_all_scenarios.svg'),bbox_inches='tight') 
        plt.savefig(os.path.join(dir_fig_out,'cag_gen_bar_all_scenarios.png'),dpi=300,bbox_inches='tight')
    else:
        plt.show()
        
# %%  capacity maps
        
    gis_n, gis_centroid_n = read_ba_usa()
    gis_n = project(gis_n, 'lat', 'long')
    gis_centroid_n = project(gis_centroid_n, 'lat', 'long')
    centroids = gis_centroid_n.set_index('id')
        
    techs = ['Storage','Biopower','Solar','Wind','Hydro']
    cap_temp = cap_reeds_ba.copy()
    cap_temp = cap_temp.groupby(['i','r','scenario'],as_index=False).sum().drop('t',1)
    cap_temp['base'] = cap_temp.merge(scenario_map,on='scenario',how='left')['base']
    cap_temp = cap_temp.merge(r_rs,on='r',how='left')
    cap_temp.loc[:,'r'] = cap_temp.loc[:,'BA'].fillna(cap_temp.loc[:,'r'])
    cap_temp = cap_temp.drop('BA',1)
    
    techs = ['Storage','RE-CT','Solar','Wind','Hydro']
    cmaps = ['Reds','Greens','Oranges','Blues','Greys']
    
    fig, ax = plt.subplots(nrows=5,ncols=2,figsize=(12,15))
    for q,s in enumerate(['Ref','RE100']):
        cap_temp_2 = cap_temp.loc[cap_temp.base==s,['i','r','cap']]
        for ix,i in enumerate(techs):
            cap_temp_plot = cap_temp_2.loc[cap_temp_2.i==i,['r','cap']]
            cap_temp_plot = cap_temp_plot.merge(regions,on='r',how='right').fillna(0).rename(columns={'r':'n','cap':'val'})
            cap_temp_plot.loc[:,'val'] = cap_temp_plot.loc[:,'val']/1000 
            ymax=cap_temp.loc[cap_temp.i == i,'cap'].max()/1000
            plot_region_flows(cap_temp_plot,gis_n,centroids,ax[ix][q],ymax=ymax,colorbar=True,color_map=cmaps[ix],label=str(i) + ' Capacity GW')


#            if q == 0:
#                plot_region_flows(cap_temp_plot,gis_n,centroids,ax[ix][q],ymax=ymax)
#            else:
#                plot_region_flows(cap_temp_plot,gis_n,centroids,ax[ix][q],ymax=ymax,colorbar=True,color_map='Blues')
            ax[ix][0].set_ylabel(i)
        ax[0][q].set_title(scenario_labels[s])

#    fig.subplots_adjust(left=0.3,wspace=.02,hspace = 0.05,right = 1)
#   Scale and position plot
    plt.axis('scaled')
    plt.tight_layout()
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'capacity_maps.png'),bbox_inches='tight')    
    else:
        plt.show()
#%% Firure 14  Transmission by RE requirement
    
    tran_temp = tran_2050.copy()
    tran_temp = tran_temp.merge(gen_2050_total[['scenario','repen','base','sens']],on='scenario',how='left')
    
    tran_temp = tran_temp.merge(requirement,on='base',how='left')
#    tran_temp = tran_temp.pivot_table(index='sens',columns='repen',values='val')
#    tran_temp = tran_temp.sort_values(100.0,ascending=False)

    fig, ax = plt.subplots(nrows=1,ncols=1,figsize=(12,8))
    count = 0
    greyLabel = True
    blueLabel = True
    for i, s in enumerate(tran_temp.sens.drop_duplicates().to_list()):
        tran_sen = tran_temp[tran_temp['sens']==s]
#        tran_sen = tran_sen.dropna(axis=0,how='all')
        if max(tran_sen.repen)<99 and blueLabel:
            ax.plot(tran_sen.Requirement,tran_sen.val/1000,color='dodgerblue',ls = '--',marker='o',label='Sensitivities that do not reach 100% RE',zorder=19)
            blueLabel=False
        elif max(tran_sen.repen)<99:
            ax.plot(tran_sen.Requirement,tran_sen.val/1000,color='dodgerblue',ls = '--',marker='o',zorder=19)
        elif s == 'Base':
            ax.plot(tran_sen.Requirement,tran_sen.val/1000,color='gold',linewidth=3,marker='o',label='Base Case',zorder=20)
        elif greyLabel:
            ax.plot(tran_sen.Requirement,tran_sen.val/1000,color='#6f6f6f',ls = '--',marker='o',label='Sensitivities that reach 100% RE')
            greyLabel = False
        else:
            ax.plot(tran_sen.Requirement,tran_sen.val/1000,color='#6f6f6f',ls = '--',marker='o')

        
        count +=1
        
    annote = tran_temp.loc[tran_temp.val == tran_temp.val.max(),['sens','Requirement','val']]#tran_temp.loc[emit_temp.Requirement==97,['sens','val','Requirement']].groupby('sens').max().sort_values('val',ascending=False).iloc[:2,:]
    dx = -3
    dy = 0
    
    ax.annotate(scenario_labels[annote.sens.values[0]],
                (float(annote.iloc[0,1]-.25), float(annote.iloc[0,2])/1e3),
                (float(annote.iloc[0,1])+dx, float(annote.iloc[0,2])/1e3+dy),
                arrowprops={'width':0.25,
                            'headwidth':6,
                            'headlength':11,
                            'shrink':0.01,
                            'color':'black'
                            },
                ha='right',
                va='center'
                )

    ax.grid()
    
    ax.set_ylabel('Total Transmission Capacity in 2050 (GW-mi)',fontsize=axislabels)
    ax.set_xlabel('Penetration Requirement (%)',fontsize=axislabels)
#    fig.subplots_adjust(bottom=)

    handles,labels = ax.get_legend_handles_labels()
    fig.legend(handles,labels,frameon=False,ncol=3,loc='lower center',fontsize=legend_small,bbox_to_anchor=(.45,0))
#    fig.tight_layout()
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'transmission_capacity.png'),bbox_inches='tight')  
        tran_temp.pivot(index='Requirement',columns='sens',values='val').rename(columns=scenario_labels).T.to_csv(os.path.join(dir_fig_out,'transmission_capacity.csv'))
    else:
        plt.show()
        
#%% Annual emissions repen

    emit_temp = emissions_reeds_2050.copy()
    emit_temp = emit_temp.groupby(['scenario']).sum().reset_index()
    emit_temp = emit_temp.merge(gen_2050_total[['scenario','sens','base','repen']],on='scenario',how='left')
    emit_temp = emit_temp.merge(requirement, on='base', how='left')

    fig, ax = plt.subplots(nrows=1,ncols=1,figsize=(12,8))
#    count = 0
    blueLabel=True
    greyLabel=True
    for i, s in enumerate(emit_temp.sens.drop_duplicates().to_list()):
        emit_scen = emit_temp.loc[emit_temp['sens']==s,:].sort_values('Requirement')
        if len(emit_scen)>7:
            delete=emit_scen
        if max(emit_scen.repen)==100 and s!='Base':
            if greyLabel:
                ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='--',marker='o',label='Sensitivities that reach 100% RE',color='#6f6f6f')
                greyLabel=False
            else:
                ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='--',marker='o',color='#6f6f6f')
        elif  max(emit_scen.repen)!=100:
            if blueLabel:
                ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='--',marker='o',label='Sensitivities that do not reach 100% RE',color='dodgerblue',zorder=19)
                blueLabel=False
            else:
                ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='--',marker='o',color='dodgerblue',zorder=19)
        elif s=='Base':
            ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='-',lw=3,marker='o',label='Base Case',color='gold',zorder=19)

    ax.grid()
    
    annote = emit_temp.loc[emit_temp.Requirement==100,['sens','emissions','Requirement']].groupby('sens').max().sort_values('emissions',ascending=False).iloc[:2,:]
    dx = -3
    dy = 175
    r  = annote['emissions'].diff().dropna().values[0]
    
    ax.text(annote.iloc[0,1]+dx, 
            annote.iloc[0,0]+dy, 
            scenario_labels[annote.index[0]]+'\n'+scenario_labels[annote.index[1]], 
            ha='right'
            )
    ax.arrow(annote.iloc[0,1]+dx+.2, 
            annote.iloc[0,0]+dy+45,
            -(dx+.2),
            -(dy+40),
            length_includes_head=True,
            head_width=.5,
            head_length=50,
            color='black'
            )
    ax.arrow(annote.iloc[0,1]+dx+.2, 
            annote.iloc[0,0]+dy+15,
            -(dx+.2),
            -(dy+15)+r,
            length_includes_head=True,
            head_width=.5,
            head_length=50,
            color='black'
            )
#    ax.text(annote.iloc[1,1]+dx, annote.iloc[1,0]+dy, scenario_labels[annote.index[1]], ha='right')
    
    ax.set_ylabel('Annual Emissions in 2050 (million tonnes)',fontsize=axislabels-3)
    ax.set_xlabel('Penetration Requirement (%)',fontsize=axislabels-3)

    handles,labels = ax.get_legend_handles_labels()
    fig.legend(handles,labels,frameon=False,ncol=3,loc='lower center',fontsize=legend_small-2,bbox_to_anchor=(.45,0.01))
    fig.tight_layout(rect=(0.08,0.08,1-0.08,1-0.08))
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'emissions_re_pen.png'),bbox_inches='tight',dpi=300) 
        emit_temp.pivot(index='Requirement',columns='sens',values='emissions').rename(columns=scenario_labels).T.to_csv(os.path.join(dir_fig_out,'emissions_re_pen.csv'))
    else:
        plt.show()
        
        #%%
    
# losses RE pen
    losses_temp = losses_2050.copy() 
    losses_temp = losses_temp.merge(gen_2050_total,on='scenario',how='left')
    losses_temp = losses_temp.merge(requirement, on='base',how='left')

    gen_temp = gen_reeds_all_scen.loc[(gen_reeds_all_scen.i == 'Hydro') | (gen_reeds_all_scen.i == 'Geothermal')]#.pivot(index='t',columns='scenario', values='gen')
    gen_temp['diff'] = gen_temp['gen'].diff()
    gen_temp = gen_temp[(gen_temp.t == 2050) & (gen_temp['diff'] < 0)].groupby('scenario').sum()
    

    losses_stor = losses_temp.loc[losses_temp.source=='STORAGE',:]
    losses_curt = losses_temp.loc[losses_temp.source=='curt',:]
    for run in gen_temp.index:
        losses_curt.loc[losses_curt.scenario == run, 'losses' ] -= gen_temp.loc[run,'diff']
        
    losses_tran = losses_temp.loc[losses_temp.source=='trans',:]    

    fig, ax = plt.subplots(nrows=3,ncols=1,figsize=(6,10))
    blueLabel=True
    greyLabel=True
    for s in losses_temp.sens.drop_duplicates().to_list():
        stor = losses_stor[losses_stor['sens']==s].sort_values('Requirement')
        curt = losses_curt[losses_curt['sens']==s].sort_values('Requirement')
        tran = losses_tran[losses_tran['sens']==s].sort_values('Requirement')
        
        labelOn=False
        if max(stor['repen'])<99:
            lcolor='dodgerblue'
            layer=19
            weight=1
            style='--'
            if blueLabel:
                label='Sensitivities that do not reach 100% RE'
                labelOn=True
                blueLabel=False
                
        elif s == 'Base':
            layer=20
            lcolor='gold'
            label='Base Case'
            labelOn=True
            weight=3
            style='-'
            
        else:
            lcolor='#6f6f6f'
            layer=1
            weight=1
            style='--'
            if greyLabel:
                label='Sensitivities that reach 100% RE'
                labelOn=True
                greyLabel=False
        
  
        if labelOn:        
            ax[0].plot(stor.Requirement,stor.losses/1e6,label=label,color=lcolor,ls=style,marker='o',zorder=layer,lw=weight)
            ax[0].grid()
            ax[0].set_title('Storage Losses')
            
            ax[1].plot(curt.Requirement,curt.losses/1e6,label=label,color=lcolor,ls=style,marker='o',zorder=layer,lw=weight)
            ax[1].grid()
            ax[1].set_title('Curtailment Losses')
            
            ax[2].plot(tran.Requirement,tran.losses/1e6,label=label,color=lcolor,ls=style,marker='o',zorder=layer,lw=weight)
            ax[2].grid()
            ax[2].set_title('Transmission Losses')        
        
        else:
            ax[0].plot(stor.Requirement,stor.losses/1e6,color=lcolor,ls=style,marker='o',zorder=layer,lw=weight)
            ax[0].grid()
            ax[0].set_title('Storage Losses')
            ax[0].set_xticks([])

            
            ax[1].plot(curt.Requirement,curt.losses/1e6,color=lcolor,ls=style,marker='o',zorder=layer,lw=weight)
            ax[1].grid()
            ax[1].set_title('Curtailment Losses')
            ax[1].set_xticks([])
            
            
            ax[2].plot(tran.Requirement,tran.losses/1e6,color=lcolor,ls=style,marker='o',zorder=layer,lw=weight)
            ax[2].grid()
            ax[2].set_title('Transmission Losses')
        
#        count += 1
    ax[1].set_ylabel('Losses (TWh)',fontsize=axislabels)
    ax[2].set_xlabel('Penetration Requirement',fontsize=axislabels)

#    ax[1][1].set_axis_off()
    handles,labels = ax[0].get_legend_handles_labels()
    fig.legend(handles,labels,frameon=False,ncol=1,loc='lower center',fontsize=legend_small,bbox_to_anchor=(0.5,0.0))
    pad=0.08
    fig.tight_layout(rect=(pad,0.1,1,1-pad))
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'losses_re_pen.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'losses_re_pen.png'),bbox_inches='tight',dpi=300)
        losses_temp[losses_temp.source == 'STORAGE'].pivot(index='Requirement',columns='sens',values='losses').rename(columns=scenario_labels).T.to_csv(os.path.join(dir_fig_out,'losses_re_pen_storage.csv'))
        losses_temp[losses_temp.source == 'trans'].pivot(index='Requirement',columns='sens',values='losses').rename(columns=scenario_labels).T.to_csv(os.path.join(dir_fig_out,'losses_re_pen_trans.csv'))
        losses_temp[losses_temp.source == 'curt'].pivot(index='Requirement',columns='sens',values='losses').rename(columns=scenario_labels).T.to_csv(os.path.join(dir_fig_out,'losses_re_pen_curt.csv'))
    else:
        plt.show()
#%% cumulative emissions RE Pen
    def interpolate(X,y1,y2,x1,x2):
        return ((y2-y1)/(x2-x1))*(X-x1)+y1
        
        
    emit_temp = emissions_reeds_all.copy()
    emit_temp = process_emissions(emit_temp)
    emit_temp = emit_temp[emit_temp.t <= 2050]
#    for scen in emit_temp.scenario.unique():
#        df_temp = emit_temp[emit_temp.scenario == scen].set_index('t',drop=True)
#        columns = emit_temp.columns.to_list()
#        common = df_temp.loc[2020,['sens','base']].to_list()
#        odds=[]
#        for y in df_temp.iloc[0:-1].index.to_list():
#            emissions = np.mean([df_temp.loc[y,'emissions'],df_temp.loc[y+2,'emissions']])
#            odds.append( [y+1,emissions,scen]+common)
#        if df_temp.index.max() < 2050:
#            emissions = np.mean([df_temp.loc[df_temp.index.max(),'emissions'],0.])
#            odds.append([df_temp.index.max(),emissions,scen]+common)
#        df_temp = pd.DataFrame(columns=columns,data=odds)
#        concatMe = [emit_temp,df_temp]
#        emit_temp = pd.concat(concatMe).reset_index(drop=True)
#        
    emit_temp = emit_temp.merge(requirement,on='base',how='left')
        
#    for i in emit_temp.sens.unique():
#       emit_temp.loc[(emit_temp.sens==i) & (emit_temp.base=='RE100') & (emit_temp.t == 2050),'emissions']  = emit_temp.loc[(emit_temp.sens==i) & (emit_temp.base=='RE90') & (emit_temp.t == 2050),'emissions'] * .3
#       
    emit_temp = emit_temp.merge(gen_2050_total[['scenario','repen']],on='scenario',how='left')
    emit_temp = emit_temp[['emissions','sens','base','repen','Requirement']].groupby(['sens','base','Requirement','repen']).sum().reset_index()
#    emit_temp = emit_temp.pivot_table(index='sens',columns='repen',values='emissions')
#    emit_temp = emit_temp.sort_values(100.0,ascending=False)#.fillna(0)
#    emit_temp = emit_temp.cumsum(1)#.reset_index()
    
    fig, ax = plt.subplots(nrows=1,ncols=1,figsize=(12,8))
#    count = 0
    greyLabel=True
    blueLabel=True
    for s in emit_temp.sens.drop_duplicates().to_list():
        emit_scen = emit_temp[emit_temp['sens']==s]
        emit_scen.sort_values('Requirement',inplace=True)
       
        if max(emit_scen.repen)==100 and s!='Base':
            if greyLabel:
                ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='--',marker='o',label='Sensitivities that reach 100% RE',color='#6f6f6f')
                greyLabel=False
            else:
                ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='--',marker='o',color='#6f6f6f')
        elif  max(emit_scen.repen)!=100:
            if blueLabel:
                ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='--',marker='o',label='Sensitivities that do not reach 100% RE',color='dodgerblue',zorder=19)
                blueLabel=False
            else:
                ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='--',marker='o',color='dodgerblue',zorder=19)
        elif s=='Base':
            ax.plot(emit_scen.Requirement,emit_scen.emissions,ls='-',lw=3,marker='o',label='Base Case',color='gold',zorder=20)
#   
    ax.set_xticks([57,60,70,80,90,100])
    ax.set_xticklabels(['57\nNo Requirement',60,70,80,90,100])
    
    minmax  = emit_temp.loc[emit_temp.Requirement == 80,'emissions'].max()
    annText = emit_temp.loc[(emit_temp.Requirement==80) & (emit_temp.emissions==minmax),'sens']
    
    ax.annotate(scenario_labels[annText.values[0]],(80,minmax),
                xytext=(0.55,0.65), 
                textcoords='axes fraction',
                arrowprops=dict(arrowstyle='->'))
    
    annotation=emit_temp.loc[(emit_temp.Requirement == 57) & (emit_temp.emissions == emit_temp.loc[emit_temp.Requirement== 57,'emissions'].min())].reset_index(drop=True)
    ax.annotate(scenario_labels[annotation.loc[1,'sens']] + '\n' +scenario_labels[annotation.loc[0,'sens']] ,
                (annotation.loc[0,'Requirement'],annotation.loc[0,'emissions']),
                xytext=(0.2,0.4), 
                textcoords='axes fraction',
                ha='right',
                arrowprops=dict(arrowstyle='->'))
    
    annotation = emit_temp.loc[(emit_temp.Requirement==80) & (emit_temp.emissions < 44000)].reset_index(drop=True)
    ax.annotate(scenario_labels[annotation.loc[0,'sens']], (annotation.loc[0,'repen'], annotation.loc[0,'emissions']), 
                xytext=(0.4,0.20), 
                textcoords='axes fraction',
                ha='right',
                arrowprops=dict(arrowstyle='->'))
    
    ax.annotate(scenario_labels[annotation.loc[1,'sens']], (annotation.loc[1,'repen'],annotation.loc[1,'emissions']), 
            xytext=(0.35,0.25), 
            textcoords='axes fraction',
            ha='right',
            arrowprops=dict(arrowstyle='->'))
    
    ax.grid()
#    ax.set_ylim(0,65000)
    
    ax.set_ylabel('2020-2050 Cumulative Emissions (million tonnes)',fontsize=axislabels-3)
    ax.set_xlabel('Penetration Requirement (%)',fontsize=axislabels-3)
    

#    fig.subplots_adjust(bottom=.27)

    handles,labels = ax.get_legend_handles_labels()
    fig.legend(handles,labels,frameon=False,ncol=3,loc='lower center',fontsize=legend_small-2,bbox_to_anchor=(.45,0))
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'cumulative_emissions_re_pen.png'),bbox_inches='tight',dpi=300)  
        emit_temp.pivot(index='Requirement',columns='sens',values='emissions').rename(columns=scenario_labels).T.to_csv(os.path.join(dir_fig_out,'cumulative_emissions_re_pen.csv'))
    else:
        plt.show()      
        
#%% Requirement, RE Pen
    gen_temp = gen_2050_total.copy()
    gen_temp = gen_temp.merge(requirement,on='base',how='left')
    
#    fig.clf()
    fig,ax = plt.subplots(1,1,figsize=(3,3))
    
    msize=5
    
    greyLabel=True
    blueLabel=True
    for sens in gen_temp.sens.drop_duplicates().to_list():
        df = gen_temp[gen_temp.sens==sens].sort_values('Requirement')
                
        if max(df.repen)==100 and sens!='Base':
            if greyLabel:
                    ax.plot(df.Requirement,df.repen,ls=':',lw=2 ,marker='o',markersize=msize-1,label='Sensitivities that reach 100% RE',color='#6f6f6f')
                    greyLabel=False
            else:
                ax.plot(df.Requirement,df.repen,ls=':',lw=2 ,marker='o',markersize=msize-1,color='#6f6f6f')
        elif  max(df.repen)!=100:
#            if blueLabel:
#                ax.plot(df.Requirement,df.repen,ls='--',marker='o',markersize=msize,label='Sensitivities that do not reach 100% RE',zorder=19)
#                blueLabel=False
#            else:
            ax.plot(df.Requirement, df.repen, ls='--', marker='o', markersize=msize-1, zorder=19,label=scenario_labels[sens])
        elif sens=='Base':
            ax.plot(df.Requirement,df.repen,ls='-',lw=6,marker='o',markersize=msize+3,label='Base Case',color='gold',zorder=1)
    
    ax.set_ylabel('Renewable Penetration (%)',fontsize=12)
    ax.set_xlabel('Penetration Requirement (%)',fontsize=12)
    
    
    ax.grid()
    ax.set_xticks(ax.get_yticks())
    ax.set_ylim(40,105)
    ax.set_xlim(40,105)

    handles,labels = ax.get_legend_handles_labels()
    labels = [labels[5],labels[0],labels[3],labels[1],labels[4],labels[2]]
    handles = [handles[5],handles[0],handles[3],handles[1],handles[4],handles[2]]
    fig.legend(handles,labels,frameon=False,loc='center left',bbox_to_anchor = (1,0.5))
    fig.tight_layout()

    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'re-pen_vs_requirement.png'),bbox_inches='tight',dpi=300)
        gen_temp.pivot(index='Requirement',columns='sens',values='repen').rename(columns=scenario_labels).T.to_csv(os.path.join(dir_fig_out,'pen_vs_requirement.csv'))
 
    else:
        plt.show()   
        
#%% 2050 cap/gen bar plot for base and constant scenario
    
    cap_temp = cap_reeds_all.copy()
    cap_temp = cap_temp.loc[cap_reeds_all.t == 2050,:]
    #Convert to GW
    cap_temp['cap'] = cap_temp['cap'] / 1000
    gen_temp = gen_reeds_all.copy()
    gen_temp = gen_temp.loc[gen_temp.t == 2050,:]
    #Convert to TWh
    gen_temp['gen'] = gen_temp['gen'] / 1e6
    
    cap_temp = format_capgen_for_plotting(cap_temp,'cap',pivot_cols='scenario')
    cap_temp = cap_temp[[scens_name+'_Constant']+scenarios_base_names]
    gen_temp = format_capgen_for_plotting(gen_temp,'gen',pivot_cols='scenario')
    gen_temp = gen_temp[[scens_name+'_Constant']+scenarios_base_names]
    
    fig, ax = plt.subplots(nrows=1,ncols=2,figsize=(12,6))
    
    bottom = np.zeros(len(cap_temp.columns))
    bottom2 = np.zeros(len(gen_temp.columns))

    for i in cap_temp.index:
        ax[0].bar(cap_temp.columns,cap_temp.loc[i,:],label=i,bottom=bottom,color=tech_colors.loc[tech_colors.order==i,'color'].values[0])#,width=1.8)
        bottom += cap_temp.loc[i,:]
    
    for i in gen_temp.index:
        ax[1].bar(gen_temp.columns,gen_temp.loc[i,:],label=i,bottom=bottom2,color=tech_colors.loc[tech_colors.order==i,'color'].values[0])#,width=1.8)
        bottom2 += gen_temp.loc[i,:]
    
    ax[0].set_xticklabels(['Constant','Ref 57%','80%','90%','95%','97%','99%','100%'],fontsize=12,rotation=60,ha='right')
    ax[1].set_xticklabels(['Constant','Ref 57%','80%','90%','95%','97%','99%','100%'],fontsize=12,rotation=60,ha='right')
    ax[0].set_yticklabels([int(x) for x in ax[0].get_yticks()],fontsize=12)
    ax[1].set_yticklabels([int(x) for x in ax[1].get_yticks()],fontsize=12)
    ax[0].set_ylabel('Capacity (GW)',fontsize=18)
    ax[1].set_ylabel('Generation (TWh)',fontsize=18)
#    ax[0].set_ylim([0,3.5e6])
#    ax[0].tick_params(axis='both', which='major', labelsize=ticklabels+2)
    handles, labels = ax[0].get_legend_handles_labels()
    fig.legend(handles[::-1], phs(labels[::-1]), frameon=False, loc='center left', bbox_to_anchor=(1,0.5),fontsize=12)
    fig.tight_layout()
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'constant_scen_capgen.svg'),bbox_inches='tight',)
        plt.savefig(os.path.join(dir_fig_out,'constant_scen_capgen.png'),bbox_inches='tight')
    else:
        plt.show()
#%%
    sys_cost_temp = sys_cost_base.copy()
    sys_cost_temp.columns = sys_cost_temp.T.reset_index().scenario.str.split('_',expand=True,n=1)[1]
    sys_cost_temp.rename( columns=scenario_labels, inplace=True )
    sys_cost_temp['Constant'] = sys_cost_constant.copy()
    sys_cost_temp = sys_cost_temp.drop('Other')
    sys_cost_temp = sys_cost_temp.rename(index={'Capital no ITC':'Capital'})
    order = ['Capital','Fuel','O&M','Trans']
    colorder= [ 'Constant','Ref 57%', '80%', '90%', '95%', '97%', '99%', '100%']
    
    sys_cost_temp = sys_cost_temp.loc[order,colorder].cumsum()
    sys_cost_temp.rename(index={'Trans':'Transmission'},inplace=True)
    fig,ax=plt.subplots(1,1,figsize=(5,3))
    
    bottom = np.zeros(len(sys_cost_temp.columns))
    for i, cost in enumerate(sys_cost_temp.index[::-1]):
        ax.bar(sys_cost_temp.columns,sys_cost_temp.loc[cost,:],color = cpal[-1-i],label=cost)
        
    ax.set_xticklabels(sys_cost_temp.columns,rotation=40,ha='right')
    ax.set_ylabel('Discounted System Cost (billion $)')
    ax.set_xlabel('Scenario')
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles[::-1],labels[::-1],frameon=False,ncol=4,loc='lower center',bbox_to_anchor=(0.5,0))
    fig.tight_layout(rect=(0,.05,1,1))
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'discounted_system_cost.svg'),bbox_inches='tight',)
        plt.savefig(os.path.join(dir_fig_out,'discounted_system_csot.png'),bbox_inches='tight',dpi=300)
    else:
        plt.show()
        
###########################
#%%  Carbon Abatement sensitivities
###########################        
    
    
    
    
    
    
###########################
#%%  ReEDS Inputs figures
###########################    

if reeds_inputs_figs:
    #%%NG prices    
    fig, ax = plt.subplots(nrows=1,ncols=1,figsize=(6,4))
    for i in ng_prices.index:
        plt.plot(ng_prices.columns,ng_prices.loc[i],label=i)
    
    plt.ylabel('Natural Gas Price ($2019/MMBtu)',fontsize=axislabels)
    plt.xticks(fontsize=axislabels-4)
    plt.yticks(fontsize=axislabels-4)
    plt.legend(bbox_to_anchor=(0.5,1),frameon=False,fontsize=axislabels-4)
    fig.tight_layout()
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'ng_prices.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'ng_prices.png'),bbox_inches='tight')
    else:
        plt.show()
        
    #%%
    ng_price_temp = ng_price_natnl.copy()
    ng_price_temp = ng_price_temp.merge(scenario_map,on='scenario',how='left')
    ng_price_temp = ng_price_temp.merge(requirement,on='base',how='left')
    ng_price_temp = ng_price_temp.pivot(index='t',columns='Requirement',values='price')
    
    fig, ax = plt.subplots(1,1,figsize=(6,4))    
    ax = ng_price_temp.loc[2020:,:].plot(legend=False)
    handles, labels = ax.get_legend_handles_labels()
    for i, label in enumerate(labels):
        labels[i]='{}%'.format(label)
        if i==0: labels[i]='Ref - {}%'.format(label)
    ax.legend(handles,labels,frameon=False)
    ax.set_ylabel('Natural Gas Price ($/MMBtu)',fontsize=axislabels)
    ax.set_ylim(0)
    ax.set_xlabel(None)
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'ng_prices_timeseries.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'ng_prices_timeseries.png'),bbox_inches='tight',dpi=300)
    else:
        plt.show()
        #%%
    
    #Demand Growth
    fig, ax = plt.subplots(nrows=1,ncols=1,figsize=(6,4))
    for i in demand_growth.index:
        plt.plot(demand_growth.columns,demand_growth.loc[i],label=i)
    
    plt.ylabel('Demand Growth (relative to 2020)',fontsize=axislabels)
    plt.xticks(fontsize=axislabels-4)
    plt.yticks(fontsize=axislabels-4)
    ax.legend(loc='upper left',bbox_to_anchor=(0,1),fontsize=axislabels-4,frameon=False)
    fig.tight_layout()
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'demand_growth.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'demand_growth.png'),bbox_inches='tight')
    else:
        plt.show()
        
        #%%
    
    #technology costs
    l_styles = ['-',':','--']
    fsize=10
    fig, ax = plt.subplots(nrows=2,ncols=2,figsize=(8,6.5))
    for x,i in enumerate(wind_costs.index):
        ax[0][0].plot(wind_costs.columns,wind_costs.loc[i]*1.3522,label=i,linestyle=l_styles[x],color='#035aff')
        ax[0][1].plot(off_wind_costs.columns,off_wind_costs.iloc[x]*1.3522,label=off_wind_costs.index[x],linestyle=l_styles[x],color='#00a9e0')
        ax[1][0].plot(pv_costs.columns,pv_costs.iloc[x]*1.3522,label=pv_costs.index[x],linestyle=l_styles[x],color='orange')
        ax[1][1].plot(battery_costs.columns,battery_costs.iloc[x]*1.3522,label=battery_costs.index[x],linestyle=l_styles[x],color='#3d3f47')

    #fig.legend(ncol=3,loc='lower center',frameon=False)
    fig.subplots_adjust(bottom=0.2,left=.15,top=1,right=1,hspace=.05)
    ax[0][0].set_xticklabels([])
    ax[0][1].set_xticklabels([])
    ax[0][0].set_xticks([])
    ax[0][1].set_xticks([])
    fig.text(.05,.4,'Overnight Capital Costs ($2019)',fontsize=axislabels-2,rotation='vertical')
    
    fig.text(.35,.95,'Onshore-Wind',fontsize=fsize,color='#035aff',fontweight='bold')
    fig.text(.8,.95,'Offshore-Wind',fontsize=fsize,color='#00a9e0',fontweight='bold')
    fig.text(.35,.55,'Solar PV',fontsize=fsize,color='orange',fontweight='bold')
    fig.text(.75,.55,'4-Hour Battery Storage',fontsize=fsize,color='#3d3f47',fontweight='bold')
    
    handles,labels = ax[1][1].get_legend_handles_labels()
    plt.legend(handles,['Mid','Low','High'],frameon=False,ncol=3,loc='lower center',fontsize=legend_small,bbox_to_anchor=(1.3,0))
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'re_costs.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'re_costs.png'),bbox_inches='tight')
    else:
        plt.show()
        
#%% Capacity by sensitivity for all techs
    cap_temp = cap_reeds_all_scen.copy()
    cap_temp = cap_temp[cap_temp.i!='Imports']
    cap_temp = cap_temp.merge(scenario_map,how='left',on='scenario')
    cap_temp = cap_temp[cap_temp.base  == 'RE100']
    cap_temp.cap = cap_temp.cap/1e3

    techs = cap_temp.i.drop_duplicates().reset_index(drop=True)
    techs = tech_colors.merge(techs,left_on='order',right_on='i')
    techs = techs['i']
    years = list(range(2020,2051,2))
    scenarios = pd.DataFrame(columns=cap_temp.sens.drop_duplicates().T,index=years).fillna(0.0)

    #%%
    ncols = 3
    nrows = int(np.ceil(len(techs)/ncols))

    fig, ax = plt.subplots(nrows,ncols,figsize=(8,10.5))
    axe = ax.ravel()

    
    for i, tech in enumerate(techs):
        df = pd.DataFrame(index=years)
        df = pd.concat([df,cap_temp[cap_temp.i == tech].pivot(index='t',columns='sens',values='cap').fillna(0.0)],axis=1).fillna(0.0)
        df.reset_index(inplace=True)
        df = df.merge(scenarios.reset_index(),how='left',on=df.columns.to_list())
        df.set_index('index',inplace=True)
        top = df.max(1)
        bottom = df.min(1)
        
        axe[i].fill_between(df.index,bottom,top,color='silver')
        axe[i].plot(df,ls=':',color = '#6f6f6f')
        axe[i].plot(df['Base'],color='red')
        axe[i].set_ylim(0)

        axe[i].set_title(tech)
        
    axe[3*3].set_ylabel('Capacity (GW)',fontsize=15)
    axe[-2].set_xlabel('Years',fontsize=15)
        
    fig.tight_layout()
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'cap_by_tech.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'cap_by_tech.png'),dpi=300,bbox_inches='tight')
    else:
        plt.show()
    #%%   
    ncols = 3
    nrows = int(np.ceil(len(techs)/ncols))

    fig, ax = plt.subplots(nrows,ncols,figsize=(8,10.5))
    axe = ax.ravel()
    ymax = 700#cap_temp.loc[cap_temp['i']!='UPV','cap'].max()
    
    for i, tech in enumerate(techs):
        df = pd.DataFrame(index=years)
        df = pd.concat([df,cap_temp[cap_temp.i == tech].pivot(index='t',columns='sens',values='cap').fillna(0.0)],axis=1).fillna(0.0)
        df.reset_index(inplace=True)
        df = df.merge(scenarios.reset_index(),how='left',on=df.columns.to_list())
        df.set_index('index',inplace=True)
        top = df.max(1)
        bottom = df.min(1)
        
        axe[i].fill_between(df.index,bottom,top,color='silver')
        axe[i].plot(df,ls=':',color = '#6f6f6f')
        axe[i].plot(df['Base'],color='red')
        axe[i].set_ylim(0,ymax)

        axe[i].set_title(tech)
        axe[i].set_yticks(list(range(0,701,140)))
        
    axe[3*3].set_ylabel('Capacity (GW)',fontsize=15)
    axe[-2].set_xlabel('Years',fontsize=15)
        
    fig.tight_layout()
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'cap_by_tech_equalaxis.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'cap_by_tech_equalaxis.png'),dpi=300,bbox_inches='tight')
    else:
        plt.show()
    
###########################################################################
#%% Plexos Plots
###########################################################################
        #%% Curtailment duration curve
if plexos_plots:   
    curtailment_duration = curtailment_plexos.copy()# get_curtailment_duration_curves(curtailment_plexos)
    

    #%%
    fig, ax = plt.subplots(1,1,figsize = (5,3))
    
    for scen in  ['Ref', 'RE80', 'RE90', 'RE97', 'RE99', 'RE100']:
        df = curtailment_duration[scen].groupby('timestamp').sum().sort_values('curtailment',ascending=False).reset_index()
        df['scenario'] = scen
        ax.plot(df.index,df.curtailment/1e3,label=scenario_labels[scen])
        
    ax.legend(frameon=False)
    ax.set_ylabel('Curtailment (GW)')
    ax.set_xlabel('Duration (hours)')
    
    fig.tight_layout()
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'curtailment_duration.svg'),bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'curtailment_duration.png'),dpi=300,bbox_inches='tight')
    else:
        plt.show()
    
    
    
    #%% Load Duration Curve
  
#    load_duration = get_load_duration_curves(load_plexos,gen_plexos)
    
    duration_df = {}
    vre_plexos = ['ReEDS_distpv','ReEDS_dupv','ReEDS_upv','ReEDS_wind-ofs','ReEDS_wind-ons']
    for scen in ['Ref', 'RE80', 'RE90', 'RE97', 'RE99', 'RE100']: #add 'RE95' back into this list when it is working
        vre_df = gen_plexos[scen].copy()
        vre_df = vre_df[vre_df['tech'].isin(vre_plexos)]
        vre_df = vre_df[['timestamp','generation']].groupby('timestamp').sum()
        
        storageLoad_temp = storageLoad_plexos[scen].copy()
        batteryLosses = storageLoad_temp.loc[storageLoad_temp['storage_resource'].str.contains('battery'),['timestamp','storage_load']]
        phsLosses =     storageLoad_temp.loc[storageLoad_temp['storage_resource'].str.contains('pumped-hydro'),['timestamp','storage_load']]
        storageLoad_temp = storageLoad_temp[['timestamp','storage_load']].groupby('timestamp').sum()
        
        etaBattery = 0.85
        batteryLosses['losses']=batteryLosses.storage_load * (1 - etaBattery)
        batteryLosses = batteryLosses[['timestamp','losses']].groupby('timestamp').sum()
        
        etaPHS = 0.8
        phsLosses['losses'] = phsLosses.storage_load * (1 - etaPHS)
        phsLosses = phsLosses[['timestamp','losses']].groupby('timestamp').sum()

        transloss_temp = transloss_plexos[scen].copy()
        transloss_temp = transloss_temp[['timestamp','losses']].groupby(['timestamp']).sum()        
        
        df = pd.DataFrame(load_plexos[scen]).groupby(['timestamp','r','scenario']).max().reset_index()
        df = df[['timestamp','load']].groupby('timestamp').sum()
        patchup = pd.DataFrame(data = dict(vre_losses = vre_df.generation + storageLoad_temp.storage_load))# + transloss_temp.losses - storageLoad_temp.storage_load - batteryLosses.losses - phsLosses.losses)
        df = df.reset_index().merge(patchup.reset_index(),on='timestamp' ).fillna(0)
        df.load -= df.vre_losses
        df = df.sort_values('load',ascending = False).reset_index(drop=True)
        duration_df[scen] =df
        
        
        del(df)
    
    #%%
    fig, ax = plt.subplots(1,1,figsize = (5,3))
    for scen in list(duration_df.keys()):
        df = duration_df[scen]
        ax.plot(df.index,df.load/1e3,label=scenario_labels[scen])
        
    ax.legend(frameon=False,ncol=3)
    ax.set_ylabel('Net Load (GW)')
    ax.set_xlabel('Duration (hours)')
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'load_duration.svg'), bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'load_duration.png'), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    plt.clf()

#%% percent vre gen duration
    
    duration_df = pd.DataFrame()
    iverter_techs = ['ReEDS_distpv','ReEDS_dupv',
                 'ReEDS_upv',
                 'ReEDS_wind-ofs',
                 'ReEDS_wind-ons',
                 'ReEDS_battery_2',
                 'ReEDS_battery_4',
                 'ReEDS_battery_6',
                 'ReEDS_battery_8',
                 'ReEDS_battery_10']
    
    for scen in list(gen_plexos.keys()):
        df = gen_plexos[scen].copy()
        df = df.merge(regions_map_plexos[scen][['generator','r']],on='generator',how='left')
        df = df.merge(intercon_map[['p','interconnect']],left_on='r',right_on='p',how='left')
        inverter_df = df[df['tech'].isin(iverter_techs)]
        df = df[['interconnect','generation','timestamp']].groupby(['interconnect','timestamp']).sum()
        df['hours'] = 1
        inverter_df = inverter_df[['interconnect','generation','timestamp']].groupby(['interconnect','timestamp']).sum()
        
        df['inverter_fraction'] = inverter_df.generation * 100 / df.generation
        df.reset_index(inplace=True)
        df = df[['interconnect','hours','inverter_fraction']].groupby(['interconnect','inverter_fraction']).sum()
        df.reset_index(inplace=True)
        df.sort_values(['interconnect','inverter_fraction'],ascending=False,inplace=True)
        
        for intercon in df.interconnect.drop_duplicates().to_list():
            df.loc[df['interconnect']==intercon,'hours'] = df.loc[df['interconnect']==intercon,'hours'].cumsum()
        
        df['scenario'] = scen
        
        duration_df = pd.concat([duration_df, df[['interconnect','inverter_fraction','hours','scenario']]])
        
    #%%
    fig, ax = plt.subplots(1,3,figsize=(6,3))
    for i, intercon in enumerate(duration_df.interconnect.drop_duplicates().to_list()):
        axe = ax[i]
        axe.set_title(intercon[0].upper()+intercon[1:]+'\nInterconnect')
        if i != 0: axe.set_yticks([])
        for scen in duration_df.loc[duration_df['interconnect']==intercon,'scenario'].drop_duplicates().unique():
            df = duration_df[(duration_df['scenario']==scen) & (duration_df['interconnect']==intercon)]
            axe.plot(df.hours,df.inverter_fraction,label=scenario_labels[scen])
            axe.set_xlabel('Duration (hours)')
            axe.set_ylim(0,105)
            
    ax[0].set_ylabel('Inverter-Based Generation (%)')
    handles, labels = ax[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(0.5,0.1),frameon=False,ncol=5)
    fig.tight_layout(w_pad=0.0,h_pad=1.1)
    
    if save_figs:
        plt.savefig(os.path.join(dir_fig_out,'inverter_fraction_duration.svg'), bbox_inches='tight')
        plt.savefig(os.path.join(dir_fig_out,'inverter_fraction_duration.png'), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    plt.clf()