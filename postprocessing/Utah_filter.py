#%%
import pandas as pd
import numpy as np
import os
import shutil
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
import e_report_dump
import subprocess
import argparse
import h5py
import gdxpds

#%% ARGUMENT INPUTS
parser = argparse.ArgumentParser(description='Utah Filter')
parser.add_argument('--case', '-c', type=str, required=True,
                    help='Path to the ReEDS run folder')

args = parser.parse_args()
case = args.case

# Path to folder where ReEDS repo is
reeds_path = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))


#%%
'''
User Inputs 
'''
# Path for folder where the ReEDS runs are located
runs_folder = os.path.join(reeds_path,'runs')

# Read switch setting for spatial resolution of case
switches = pd.read_csv(os.path.join(case,'inputs_case','switches.csv'))
resolution = switches[switches['AWS']=='GSw_RegionResolution']['0'].item() 

# List of ReEDS BAs that belong to Utah 
list_of_regions_to_isolate = ['p25','p26']

# Populate folders list with file paths to runs that you want to extract Utah data from  

# Folders = ['/data/shared/projects/lserpe/public/ReEDS-2.0/runs/v1_050725_Utah_mixed',
#            #'/data/shared/projects/lserpe/public/ReEDS-2.0/runs/v1_050725_WI_county_PRAS'           
#             ]

Folders = [case,           
            ]

#%%

inputs_case = os.path.join(reeds_path,'runs',Folders[0],'inputs_case')

if resolution == 'ba' or resolution == 'aggreg':
    # List of ReEDS BAs that belong to Utah 
    regions  = list_of_regions_to_isolate 


elif resolution == 'county':
# List of counties that belong to Utah if running at county resolution 
# Comment out if using BA resolution runs
    county2zone = pd.read_csv(os.path.join(reeds_path,'inputs','county2zone.csv'))
    regions = ['p' + str(fips) for fips in county2zone.loc[county2zone['ba'].isin(list_of_regions_to_isolate), 'FIPS'].tolist()]


elif resolution == 'mixed':
    county2zone = pd.read_csv(os.path.join(reeds_path,'inputs','county2zone.csv'))
    # List of ReEDS couties and BAs to isolate 
    agglevel_variables = reeds.spatial.get_agglevel_variables(reeds_path, inputs_case)
    ba_regions = list(set(agglevel_variables['ba_regions']) & set(list_of_regions_to_isolate))
    ba2county =  ['p' + str(fips) for fips in county2zone.loc[county2zone['ba'].isin(list_of_regions_to_isolate), 'FIPS'].tolist()]
    county_regions = list(set(agglevel_variables['county_regions']) & set(ba2county))
    regions = list(set(ba_regions + county_regions))
    

#%%
## This section is used to overwrite the ReEDS report with a new report that contains only Utah data 

for f in Folders:
    # Copy outputs and inputs folder to create a version where the filtered data will live 
    source_folder = f
    destination_folder = os.path.join(runs_folder, f.split(os.sep)[-1] + '_isolated') 

    # Copy specific subfolders but exclude certain folders within them
    folders_to_copy = ['outputs', 'inputs_case','ReEDS_Augur']
    exclude_folders = ['Augur_plots', 'hourly','maps','tc_pahseout_data','maps','vizit',
                       '_pychache_','augur_data','PRAS']        

    for folder in folders_to_copy:
        src_folder = os.path.join(source_folder, folder)
        dest_folder = os.path.join(destination_folder, folder)
        if os.path.exists(src_folder):
            try:
                os.makedirs(dest_folder, exist_ok=True)
                for item in os.listdir(src_folder):
                    item_path = os.path.join(src_folder, item)
                    if os.path.isdir(item_path) and item not in exclude_folders:
                        shutil.copytree(item_path, os.path.join(dest_folder, item))
                    elif os.path.isfile(item_path):
                        shutil.copy2(item_path, dest_folder)
                print(f"Copied {src_folder} to {dest_folder} excluding {exclude_folders}")
            except Exception as e:
                print(f"Error copying {src_folder}: {e}")
        else:
            print(f"Folder {src_folder} does not exist.")

    # copy_specific

    # change folder path to copied folder
    f = destination_folder
    # Path to folder where ReEDS output report is located
    # This report is automatically generated when a ReEDS run is completed
    report_dir = os.path.join(f, 'outputs', 'reeds-report', 'report.xlsx')
    

    #### Generation
    # Generation in report is at national level 
    report_GEN= pd.read_excel(report_dir, sheet_name = '3_Generation (TWh)')
    scenario = report_GEN.scenario.tolist()[0]
    output_dir = os.path.join(f, 'outputs')
    # Get generation by region data
    output_GEN = pd.read_csv(os.path.join(output_dir, 'gen_ann.csv'))
    # Filter to region of interest
    output_GEN = output_GEN.loc[output_GEN.r.isin(regions)]

    # Reformat to match report data
    output_GEN['scenario'] = scenario       
    GEN_table = output_GEN.pivot_table(index = ['scenario','i','t'],
                                       values = 'Value',
                                       aggfunc = 'sum')
    GEN_table.Value/=1e6
    
    GEN_table.reset_index(inplace=True, drop = False)
    for y in GEN_table.t.unique():
        GEN_table.loc[GEN_table.t == y,'Net Level Generation (TWh)'] = GEN_table.loc[GEN_table.t == y,'Value'].sum()
    
    # Reformat technology names to match report data technology names 
    GEN_table.loc[['hydN' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['hydU' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['hydE' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['oal' in x for x in GEN_table.i],'i'] = 'coal'
    GEN_table.loc[['CC' in x for x in GEN_table.i],'i'] = 'gas-cc'
    GEN_table.loc[['CT' in x for x in GEN_table.i],'i'] = 'gas-ct'
    GEN_table.loc[['upv' in x for x in GEN_table.i],'i'] = 'upv'
    GEN_table.loc[['wind-ons' in x for x in GEN_table.i],'i'] = 'wind-ons'
    GEN_table.loc[['wind-ofs' in x for x in GEN_table.i],'i'] = 'wind-ofs'
    GEN_table.loc[['geo' in x for x in GEN_table.i],'i'] = 'geothermal'
    GEN_table.loc[['egs' in x for x in GEN_table.i],'i'] = 'geothermal'
    GEN_table.loc[['csp' in x for x in GEN_table.i],'i'] = 'csp'
    GEN_table.columns = report_GEN.columns

    GEN_table = GEN_table.groupby(['scenario','tech','year','Net Level Generation (TWh)']).sum().reset_index()
    GEN_table = GEN_table[['scenario','tech','year','Generation (TWh)','Net Level Generation (TWh)']]

    # Write the region-specific generation data to the report
    with pd.ExcelWriter(os.path.join(f, 'outputs', 'reeds-report', 'report.xlsx'), engine="openpyxl", mode="a", if_sheet_exists='replace') as writer:
        GEN_table.to_excel(writer, sheet_name = '3_Generation (TWh)', index = False)


    #### Capacity

    report_GEN= pd.read_excel(report_dir, sheet_name = '4_Capacity (GW)')
    output_GEN = pd.read_csv('//'.join([output_dir,'cap.csv']))
    output_GEN = output_GEN.loc[output_GEN.r.isin(regions)]
    output_GEN['scenario'] = scenario
    
    
    GEN_table = output_GEN.pivot_table(index = ['scenario','i','t'],
                                       values = 'Value',
                                       aggfunc = 'sum')
    GEN_table.Value/=1e3
    
    GEN_table.reset_index(inplace=True, drop = False)
    for y in GEN_table.t.unique():
        GEN_table.loc[GEN_table.t == y,'Net Level Capacity (GW)'] = GEN_table.loc[GEN_table.t == y,'Value'].sum()
    

    GEN_table.loc[['hydN' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['hydU' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['hydE' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['oal' in x for x in GEN_table.i],'i'] = 'coal'
    GEN_table.loc[['CC' in x for x in GEN_table.i],'i'] = 'gas-cc'
    GEN_table.loc[['CT' in x for x in GEN_table.i],'i'] = 'gas-ct'
    GEN_table.loc[['upv' in x for x in GEN_table.i],'i'] = 'upv'
    GEN_table.loc[['wind-ons' in x for x in GEN_table.i],'i'] = 'wind-ons'
    GEN_table.loc[['wind-ofs' in x for x in GEN_table.i],'i'] = 'wind-ofs'
    GEN_table.loc[['geo' in x for x in GEN_table.i],'i'] = 'geothermal'
    GEN_table.loc[['egs' in x for x in GEN_table.i],'i'] = 'geothermal'
    GEN_table.loc[['csp' in x for x in GEN_table.i],'i'] = 'csp'
    GEN_table.columns = report_GEN.columns

    GEN_table = GEN_table.groupby(['scenario','tech','year','Net Level Capacity (GW)']).sum().reset_index()
    GEN_table = GEN_table[['scenario','tech','year','Capacity (GW)','Net Level Capacity (GW)']]

    with pd.ExcelWriter('//'.join([f,'outputs','reeds-report','report.xlsx']),engine="openpyxl", mode="a",if_sheet_exists='replace') as writer:
        GEN_table.to_excel(writer, sheet_name = '4_Capacity (GW)', index = False)

    
    #### new Capacity

    report_GEN= pd.read_excel(report_dir, sheet_name = '5_New Annual Capacity (GW)')
    output_GEN = pd.read_csv('//'.join([output_dir,'cap_new_ann.csv']))
    output_GEN = output_GEN.loc[output_GEN.r.isin(regions)]
    output_GEN['scenario'] = scenario
    
    
    GEN_table = output_GEN.pivot_table(index = ['scenario','i','t'],
                                       values = 'Value',
                                       aggfunc = 'sum')
    GEN_table.Value/=1e3
    
    GEN_table.reset_index(inplace=True, drop = False)
    for y in GEN_table.t.unique():
        GEN_table.loc[GEN_table.t == y,'Net Level Capacity (GW)'] = GEN_table.loc[GEN_table.t == y,'Value'].sum()
    

    GEN_table.loc[['hydN' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['hydU' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['hydE' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['oal' in x for x in GEN_table.i],'i'] = 'coal'
    GEN_table.loc[['CC' in x for x in GEN_table.i],'i'] = 'gas-cc'
    GEN_table.loc[['CT' in x for x in GEN_table.i],'i'] = 'gas-ct'
    GEN_table.loc[['upv' in x for x in GEN_table.i],'i'] = 'upv'
    GEN_table.loc[['wind-ons' in x for x in GEN_table.i],'i'] = 'wind-ons'
    GEN_table.loc[['wind-ofs' in x for x in GEN_table.i],'i'] = 'wind-ofs'
    GEN_table.loc[['geo' in x for x in GEN_table.i],'i'] = 'geothermal'
    GEN_table.loc[['egs' in x for x in GEN_table.i],'i'] = 'geothermal'
    GEN_table.loc[['csp' in x for x in GEN_table.i],'i'] = 'csp'
    GEN_table.columns = report_GEN.columns

    GEN_table = GEN_table.groupby(['scenario','tech','year','Net Level Capacity (GW)']).sum().reset_index()
    GEN_table = GEN_table[['scenario','tech','year','Capacity (GW)','Net Level Capacity (GW)']]

    with pd.ExcelWriter(os.path.join(f,'outputs','reeds-report','report.xlsx'),engine="openpyxl", mode="a",if_sheet_exists='replace') as writer:
        GEN_table.to_excel(writer, sheet_name = '5_New Annual Capacity (GW)', index = False)


    #### Retirements 

    report_GEN= pd.read_excel(report_dir, sheet_name = '6_Annual Retirements (GW)')
    output_GEN = pd.read_csv(os.path.join(output_dir,'ret_ann.csv'))
    output_GEN = output_GEN.loc[output_GEN.r.isin(regions)]
    output_GEN['scenario'] = scenario
    
    
    GEN_table = output_GEN.pivot_table(index = ['scenario','i','t'],
                                       values = 'Value',
                                       aggfunc = 'sum')
    GEN_table.Value/=1e3
    
    GEN_table.reset_index(inplace=True, drop = False)
    for y in GEN_table.t.unique():
        GEN_table.loc[GEN_table.t == y,'Net Level Capacity (GW)'] = GEN_table.loc[GEN_table.t == y,'Value'].sum()
    

    GEN_table.loc[['hydN' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['hydU' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['hydE' in x for x in GEN_table.i],'i'] = 'hydro'
    GEN_table.loc[['oal' in x for x in GEN_table.i],'i'] = 'coal'
    GEN_table.loc[['CC' in x for x in GEN_table.i],'i'] = 'gas-cc'
    GEN_table.loc[['CT' in x for x in GEN_table.i],'i'] = 'gas-ct'
    GEN_table.loc[['upv' in x for x in GEN_table.i],'i'] = 'upv'
    GEN_table.loc[['wind-ons' in x for x in GEN_table.i],'i'] = 'wind-ons'
    GEN_table.loc[['wind-ofs' in x for x in GEN_table.i],'i'] = 'wind-ofs'
    GEN_table.loc[['geo' in x for x in GEN_table.i],'i'] = 'geothermal'
    GEN_table.loc[['egs' in x for x in GEN_table.i],'i'] = 'geothermal'
    GEN_table.loc[['csp' in x for x in GEN_table.i],'i'] = 'csp'
    GEN_table.columns = report_GEN.columns

    GEN_table = GEN_table.groupby(['scenario','tech','year','Net Level Capacity (GW)']).sum().reset_index()
    GEN_table = GEN_table[['scenario','tech','year','Capacity (GW)','Net Level Capacity (GW)']]

    with pd.ExcelWriter(os.path.join(f,'outputs','reeds-report','report.xlsx'),engine="openpyxl", mode="a",if_sheet_exists='replace') as writer:
        GEN_table.to_excel(writer, sheet_name = '6_Annual Retirements (GW)', index = False)


    #### Firm Capacity 

    # If using PRAS instead of capacity credit method for Resource Adequacy then firm_cap is not populated 
    switches = pd.read_csv(os.path.join(f,'inputs_case','switches.csv'))
    if switches[switches['AWS']=='GSw_PRM_CapCredit']['0'].item() ==1:
        report_GEN= pd.read_excel(report_dir, sheet_name = '11_Firm Capacity (GW)')
        output_GEN = pd.read_csv(os.path.join(output_dir,'cap_firm.csv'))
        output_GEN = output_GEN.loc[output_GEN.r.isin(regions)]
        output_GEN['scenario'] = scenario
        
        
        GEN_table = output_GEN.pivot_table(index = ['ccseason','scenario','i','t'],
                                        values = 'Value',
                                        aggfunc = 'sum')
        GEN_table.Value/=1e3
        
        GEN_table.reset_index(inplace=True, drop = False)
        for y in GEN_table.t.unique():
            GEN_table.loc[GEN_table.t == y,'Net Level Capacity (GW)'] = GEN_table.loc[GEN_table.t == y,'Value'].sum()
        

        GEN_table.loc[['hydN' in x for x in GEN_table.i],'i'] = 'hydro'
        GEN_table.loc[['hydU' in x for x in GEN_table.i],'i'] = 'hydro'
        GEN_table.loc[['hydE' in x for x in GEN_table.i],'i'] = 'hydro'
        GEN_table.loc[['oal' in x for x in GEN_table.i],'i'] = 'coal'
        GEN_table.loc[['CC' in x for x in GEN_table.i],'i'] = 'gas-cc'
        GEN_table.loc[['CT' in x for x in GEN_table.i],'i'] = 'gas-ct'
        GEN_table.loc[['upv' in x for x in GEN_table.i],'i'] = 'upv'
        GEN_table.loc[['wind-ons' in x for x in GEN_table.i],'i'] = 'wind-ons'
        GEN_table.loc[['wind-ofs' in x for x in GEN_table.i],'i'] = 'wind-ofs'
        GEN_table.loc[['geo' in x for x in GEN_table.i],'i'] = 'geothermal'
        GEN_table.loc[['egs' in x for x in GEN_table.i],'i'] = 'geothermal'
        GEN_table.loc[['csp' in x for x in GEN_table.i],'i'] = 'csp'
        GEN_table.columns = report_GEN.columns

        GEN_table = GEN_table.groupby(['scenario','tech','year','Net Level Capacity (GW)']).sum().reset_index()
        GEN_table = GEN_table[['scenario','tech','year','Capacity (GW)','Net Level Capacity (GW)']]


        with pd.ExcelWriter(os.path.join(f,'outputs','reeds-report','report.xlsx'),engine="openpyxl", mode="a",if_sheet_exists='replace') as writer:
            GEN_table.to_excel(writer, sheet_name = '11_Firm Capacity (GW)', index = False)


    #### Emissions

    report_GEN= pd.read_excel(report_dir, sheet_name = '25_Emissions National (metric t')
    output_GEN = pd.read_csv(os.path.join(output_dir,'emit_r.csv'))
    output_GEN = output_GEN.loc[output_GEN.r.isin(regions)]
    output_GEN['scenario'] = scenario
    
    
    GEN_table = output_GEN.pivot_table(index = ['eall','scenario','t'],
                                       values = 'Value',
                                       aggfunc = 'sum')
    GEN_table.Value/=1e3
    
    GEN_table.reset_index(inplace=True, drop = False)
    for y in GEN_table.t.unique():
        GEN_table.loc[GEN_table.t == y,'Emissions (metric tons)'] = GEN_table.loc[GEN_table.t == y,'Value'].sum()
    


    with pd.ExcelWriter(os.path.join(f,'outputs','reeds-report','report.xlsx'),engine="openpyxl", mode="a",if_sheet_exists='replace') as writer:
        GEN_table.to_excel(writer, sheet_name = '25_Emissions National (metric t', index = False)


    #### Transmission

    # report_GEN= pd.read_excel(report_dir, sheet_name = '14_Transmission (GW-mi)')
    # output_GEN = pd.read_csv(os.path.join(output_dir,'tran_out.csv'))
    # output_GEN = output_GEN.loc[output_GEN.r.isin(regions)]
    # output_GEN = output_GEN.loc[output_GEN.rr.isin(regions)]
    # output_GEN['scenario'] = scenario
    
    
    # GEN_table = output_GEN.pivot_table(index = ['scenario','trtype','t'],
    #                                    values = 'Value',
    #                                    aggfunc = 'sum')
    # GEN_table.Value/=1e3
    
    # GEN_table.reset_index(inplace=True, drop = False)
    # for y in GEN_table.t.unique():
    #     GEN_table.loc[GEN_table.t == y,'Net Level Amount (GW-mi)'] = GEN_table.loc[GEN_table.t == y,'Value'].sum()

    # GEN_table.columns = report_GEN.columns
    
    # GEN_table = GEN_table.groupby(['scenario','trtype','t','Net Level Amount (GW-mi)']).sum().reset_index()
    # GEN_table = GEN_table[['scenario','tech','year','Amount (GW-mi)','Net Level Amount (GW-mi)']]


    # with pd.ExcelWriter(os.path.join(f,'outputs','reeds-report','report.xlsx'),engine="openpyxl", mode="a",if_sheet_exists='replace') as writer:
    #     GEN_table.to_excel(writer, sheet_name = '25_Emissions National (metric t', index = False)


    

    
GEN_table


#%%
# This section is used to filter the ReEDS output files to only include data for Utah regions
for f in Folders:
    f = os.path.join(runs_folder, os.path.basename(f) + '_isolated')
    output_dir = os.path.join(f,'outputs')
    for file in os.listdir(output_dir):
        if '.csv' in file:
            try:
                output_file = pd.read_csv(os.path.join(output_dir,file))
                if 'r' in output_file.columns.tolist():
                    print(file)
                    output_file = output_file.loc[output_file.r.isin(regions)]
                    output_file.to_csv(os.path.join(output_dir,file),index = False)
            except:
                print('Failed',file)

        if '.h5' in file:
            if 'outputs' in file:
                    try:
                        ### outputs gdx
                        gdx_file_name = f.split('/')[-1].split("_")
                        gdx_file_name  = '_'.join(gdx_file_name[:-1])
                        dict_out = gdxpds.to_dataframes(
                            os.path.join(output_dir, f"rep_{os.path.basename(gdx_file_name)}.gdx")
                        )
                        outputs_list = list(dict_out.keys())
                        for i in outputs_list:
                            if 'r' in dict_out[i].columns.tolist():
                                print(i)
                                dict_out[i] = dict_out[i].loc[dict_out[i].r.isin(regions)]
                            elif 'rr' in dict_out[i].columns.tolist():
                                dict_out[i] = dict_out[i].loc[dict_out[i].rr.isin(regions)]


                            ## re- write the h5
                        e_report_dump.dfdict_to_h5(
                            dfdict=dict_out,
                            filepath=os.path.join(output_dir, 'outputs.h5'),
                            overwrite=True,
                            symbol_list=None,
                            rename=dict(),
                            errors="warn",
                            #**kwargs,
                        )

                    except:
                        print('Failed',file)




# This section is used to filter the ReEDS input case files to only include data for Utah regions
for f in Folders:
    f = os.path.join(runs_folder, os.path.basename(f) + '_isolated')
    output_dir = os.path.join(f,'inputs_case')
    for file in os.listdir(output_dir):
        if '.csv' in file:
            try:
                output_file = pd.read_csv(os.path.join([output_dir,file]))
                if 'r' in output_file.columns.tolist():
                    print(file)
                    output_file = output_file.loc[output_file.r.isin(regions)]
                    output_file.to_csv(os.path.join(output_dir,file),index = False)
            except:
                print('Failed',file)

        if '.h5' in file:
            if 'load' in file:
                try:
                    output_file = reeds.io.read_file(os.path.join(output_dir,file))                               
                    print(file)
                    output_file = output_file[regions]
                    reeds.io.write_profile_to_h5(output_file, file, output_dir)  
                except:
                    print('Failed',file)

            if 'recf' in file:
                try:
                    output_file = reeds.io.read_file(os.path.join(output_dir,file))                               
                    print(file)
                    col_list = [col for col in output_file.columns if any(region in col for region in regions)]                  
                    output_file = output_file[col_list]
                    reeds.io.write_profile_to_h5(output_file, file, output_dir)      
                except:
                    print('Failed',file)



# This section is used to copy misc files to isolated run folder
misc_files =['gamslog.txt','e_report_params.csv']
for f in Folders:
    f_destination = os.path.join(runs_folder, os.path.basename(f) + '_isolated')  
    for file in misc_files:
        try:
            shutil.copy(os.path.join(f, file), os.path.join(f_destination, file))
            print(f"Copied {file} to {f_destination}")
        except Exception as e:
            print(f"Failed to copy {file}: {e}")

# %%
# # Re-Run transmission_maps.py for isolated data
# for f in Folders:
#     casedir = os.path.join(runs_folder, f.split(os.sep)[-1] + '_isolated')
#     caseSwitches = pd.read_csv(os.path.join(runs_folder, casedir,'inputs_case', 'switches.csv'))
#     solveyears = pd.read_csv(os.path.join(runs_folder, casedir,'inputs_case', 'modeledyears.csv')).T.reset_index()['index'].tolist()
        
#     # Call the transmission_maps.py script to re-run for isolated data
#     transmission_maps_script = os.path.join(reeds_path, 'postprocessing', 'transmission_maps.py -c {} -y {}'.format(
#                     casedir, (
#                         solveyears[-1]
#                         if int(caseSwitches[caseSwitches['AWS']=='transmission_maps']['0'].item()) > int(solveyears[-1])
#                         else caseSwitches[caseSwitches['AWS']=='transmission_maps']['0'].item())
#                 ))
    
#     subprocess.run(['python', transmission_maps_script], check=True)


