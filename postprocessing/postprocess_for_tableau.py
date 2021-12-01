# ReEDS-to-Tableau Postprocessing
#
# Install the Tableau Hyper API with:
# `pip install tableauhyperapi`
# 
# Currently, this script uses relative paths and should be run from the `postprocessing` directory.

import argparse
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add bokehpivot to the path so we can grab some of its functions:
sys.path.insert(1, os.path.join(os.pardir,'bokehpivot'))

import core
from reeds2 import pre_systemcost, inflate_series
import bokeh.models.widgets as bmw #for setting dollar year widget in cost reporting
import reeds_bokeh


from tableauhyperapi import HyperProcess, Telemetry, \
    Connection, CreateMode, \
    NULLABLE, SqlType, TableDefinition, \
    Inserter, \
    escape_name, escape_string_literal, \
    HyperException


# Define a dict of column types mapping their names to data types and fancier names we'll use within Tableau for plotting.
# "val" is excluded here, which refers to the measured value column. Whatever's in the "label" column of tables_to_aggregate
# will be applied as the name and the column's assigned as a double.
column_types = {"scenario":  ["Scenario", SqlType.text()],
                "i":         ["Technology or Category", SqlType.text()],
                "v":         ["Class", SqlType.text()],
                "h":         ["Timeslice", SqlType.text()],
                "r":         ["Region", SqlType.text()],
                "rf":        ["From Region", SqlType.text()],
                "rt":        ["To Region", SqlType.text()],
                "t":         ["Year", SqlType.int()],
                "bin":       ["Bin", SqlType.text()],
                "szn":       ["Season", SqlType.text()],
                "ortype":    ["Reserve Type", SqlType.text()],
                "trtype":    ["Transmission Type", SqlType.text()],
                "type":      ["Type", SqlType.text()],
                "subtype":   ["Subtype", SqlType.text()],
                "sys_costs": ["Cost Type", SqlType.text()]
                }


def create_table_definitions(table_aggregation_csv_path):
    """
    Create a dict of Tableau Hyper API objects which define all the tables to be created in the .hyper file.
    
    returns: 
        table_dict, a dict of Hyper API table def objects whose keys are each csv to be aggregated
        columnnames_dict, a dict of column names for each concatenated csv
    """
    csv_list = pd.read_csv(table_aggregation_csv_path)
    csv_list = csv_list[csv_list.ignore!=1].reset_index() #ignore any csvs flagged as such

    table_dict = {}
    columnnames_dict = {}
    for this_csv_idx in range(0,len(csv_list)):
        csv_parameters = csv_list.loc[this_csv_idx]

        # Assemble the columns from those listed in the table aggregation csv
        column_objects = []
        column_objects.append(TableDefinition.Column('Scenario', SqlType.text(), NULLABLE)) #first column is always ReEDS scenario
        for col in csv_parameters[5:]:
            if not isinstance(col,str): #have run out of columns to add
                break
            elif col == 'val': #label the measure column according to what's specified in the table aggregation csv
                column_objects.append(TableDefinition.Column(csv_parameters['label'], SqlType.double(), NULLABLE))
            else: #regular column listed in column_types
                try:
                    column_objects.append(TableDefinition.Column(column_types[col][0], column_types[col][1], NULLABLE))
                except KeyError:
                    print('{} contains a column name whose type has not been defined in column_types.'.format(csv_parameters['csv']))

        this_table = TableDefinition(
            table_name=csv_parameters['csv'],
            columns = column_objects
        )
        
        table_dict[csv_parameters['csv']] = this_table
    
        these_columnnames = csv_parameters[5:]
        these_columnnames[these_columnnames=='val'] = csv_parameters['label']
        columnnames_dict[csv_parameters['csv']] = [ x for x in these_columnnames if str(x) != 'nan' ]

    return table_dict, columnnames_dict


def update_hyper_file_from_csv(table_def,csv_path,hyper_path,create_new=False):
    """
    Load data from a csv into a Hyper file, creating a new Hyper file if directed to do so
    """
    print(f"Loading data from {csv_path} into table in Tableau Hyper file at {hyper_path}")
    create_mode_to_use = CreateMode.CREATE_AND_REPLACE if create_new else CreateMode.NONE

    # Optional process parameters.
    # They are documented in the Tableau Hyper documentation, chapter "Process Settings"
    # (https://help.tableau.com/current/api/hyper_api/en-us/reference/sql/processsettings.html).
    process_parameters = {
        # Limits the number of Hyper event log files to two.
        "log_file_max_count": "2",
        # Limits the size of Hyper event log files to 100 megabytes.
        "log_file_size_limit": "100M"
    }

    # Starts the Hyper Process with telemetry enabled to send data to Tableau.
    # To opt out, simply set telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU.
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters=process_parameters) as hyper:

        # Optional connection parameters.
        # They are documented in the Tableau Hyper documentation, chapter "Connection Settings"
        # (https://help.tableau.com/current/api/hyper_api/en-us/reference/sql/connectionsettings.html).
        connection_parameters = {"lc_time": "en_US"}

        # Creates new Hyper file if directed to.
        with Connection(endpoint=hyper.endpoint,
                        database=hyper_path,
                        create_mode=create_mode_to_use,
                        parameters=connection_parameters) as connection:

            connection.catalog.create_table_if_not_exists(table_definition=table_def)

            # Using path to current file, create a path that locates CSV file packaged with these examples.
            # path_to_csv = str(Path(__file__).parent / "data" / "customers.csv")

            # Load all rows into the table from the CSV file.
            # `execute_command` executes a SQL statement and returns the impacted row count.
            #
            # Note:
            # You might have to adjust the COPY parameters to the format of your specific csv file.
            # The example assumes that your columns are separated with the ',' character
            # and that NULL values are encoded via the string 'NULL'.
            # Also be aware that the `header` option is used in this example:
            # It treats the first line of the csv file as a header and does not import it.
            #
            # The parameters of the COPY command are documented in the Tableau Hyper SQL documentation
            # (https:#help.tableau.com/current/api/hyper_api/en-us/reference/sql/sql-copy.html).
            count_in_table = connection.execute_command(
                command=f"COPY {table_def.table_name} from {escape_string_literal(str(csv_path))} with "
                f"(format csv, NULL 'NULL', delimiter ',', header)") #include ", header" in string if header is present to skip it

            # TODO: add an UPDATE query to add scenario names directly, allowing us to not have to make csvs first

            # print(f"The number of rows in table {table_def.table_name} is {count_in_table}.")

        # print("The connection to the Hyper file has been closed.")
    # print("The Hyper process has been shut down.")


if __name__ == 'main':
    # -- Argument Block --
    parser = argparse.ArgumentParser(description="""This script concatenates csv outputs from specified ReEDS runs and outputs them as csvs and a Tableau Hyper extract file.""")
    parser.add_argument("-d","--reeds_dir", help="full path to ReEDS directory")
    parser.add_argument("-o","--output_dir", help="name of new directory to create to house outputs within ReEDS-2.0/runs")
    parser.add_argument("-s","--scenarios", help="Python list of scenario names to include")
    parser.add_argument("-t","--table_aggregation_csv_path", help="full path to csv containing format information of all csvs to be included in outputs")
    parser.add_argument("-dy","--dollar_year", default=reeds_bokeh.DEFAULT_DOLLAR_YEAR, help="desired dollar year for outputs (!!!!note: only works for bokehpivot system cost outputs currently. All else still in 2004$")

    args = parser.parse_args()
    reeds_dir = args.reeds_dir
    output_dir = args.output_dir
    scenarios = args.scenarios
    table_aggregation_csv_path = args.table_aggregation_csv_path
    DOLLAR_YEAR = args.dollar_year

    # Test arguments:
    reeds_dir = "D:/mirish/projects/ReEDS-2.0/"
    output_dir = "bvre02"
    scenarios = ['bvre02_tax30',
                 'bvre02_tax30_nobeccs',
                 #'bvre02_tax50',
                 'bvre02_tax50_nobeccs',
                 'bvre02_100_2050',
                 'bvre02_100_2050_nobeccs']
    table_aggregation_csv_path = 'D:/mirish/projects/ReEDS-2.0/postprocessing/tables_to_aggregate.csv'
    DOLLAR_YEAR = '2020'
    
    # Internal defaults (only used for bokehpivot currently):
    PV_YEAR = reeds_bokeh.DEFAULT_PV_YEAR
    DISCOUNT_RATE = reeds_bokeh.DEFAULT_DISCOUNT_RATE
    END_YEAR = reeds_bokeh.DEFAULT_END_YEAR 

    # -- Concatenate scenarios --

    # Create results directory in reeds_dir/runs if it doesn't exist:
    output_path = (Path(reeds_dir) / 'runs' / output_dir)
    output_path.mkdir(parents=False,exist_ok=True)

    # Load in Tableau table definitions for all specified csvs:
    table_defs, columnname_defs = create_table_definitions(table_aggregation_csv_path)

    # -- Loop through ReEDS scenarios, concatenating the chosen csvs --
    create_new = True # create a new .hyper file on the first iteration
    for this_csv in table_defs:
        df_list = []
        for this_scenario in scenarios:
            # -- Add a scenario name and append this csv to the list --
            this_df = pd.read_csv(Path(reeds_dir) / 'runs' / this_scenario / 'outputs' / ( this_csv + '.csv'))
            this_df.insert(0,'Scenario',this_scenario)
            df_list.append(this_df)
        
        #Concatenate all the dfs:
        this_df = pd.concat(df_list,axis=0)

        #Rename the columns to their set names so they're not just "Dim1", "Dim2", etc.
        this_df.columns = ['scenario'] + columnname_defs[this_csv]
        
        # Write to a csv:
        this_df.to_csv(output_path / ( this_csv + '_all.csv'),index=False)
        
        # Write to .hyper file:
        try:
            update_hyper_file_from_csv(table_defs[this_csv],output_path / ( this_csv + '_all.csv'),output_path / (output_dir + '.hyper'),create_new)
        except HyperException as ex:
            print(ex)
        
        create_new = False #only update the existing .hyper file on all subsequent iterations


    # -- Create pivot tables from concatenated csvs --
    # Set bokehpivot internals needed for cost calculations:
    core.GL['widgets'] = {'var_dollar_year': bmw.TextInput(title='Dollar Year', value=str(DOLLAR_YEAR), css_classes=['wdgkey-dollar_year', 'reeds-vars-drop'], visible=False),
                            'var_discount_rate': bmw.TextInput(title='Discount Rate', value=str(DISCOUNT_RATE), css_classes=['wdgkey-discount_rate', 'reeds-vars-drop'], visible=False),
                            'var_pv_year': bmw.TextInput(title='Present Value Reference Year', value=str(PV_YEAR), css_classes=['wdgkey-pv_year', 'reeds-vars-drop'], visible=False),
                            'var_end_year': bmw.TextInput(title='Present Value End Year', value=str(END_YEAR), css_classes=['wdgkey-end_year', 'reeds-vars-drop'], visible=False)}

    # Read in mapping csv to get label values for each csv:
    csv_list = pd.read_csv(table_aggregation_csv_path)

    # Create a list of pivotted csvs/Tableau tables with the concatenated csvs from above that they pull data from:
    pivot_dict = {'scen_i_r_t':             {'id_columns': ['scenario','i','r','t'],
                                             'csvs': ['gen_ivrt','cap_ivrt','cap_new_ivrt','cap_upgrade_ivrt','ret_ivrt','systemcost_ba','curt_all_ann','cc_new','opRes_supply_h'],
                                             'operation':  ['sum','sum','sum','sum','sum','sum','mean','sum','sum']},
                  'scen_r_t':               {'id_columns': ['scenario','r','t'],
                                             'csvs': ['reqt_price','reqt_quant'],
                                             'operation':  ['custom','custom']},
                  'scen_i_h_r_t':           {'id_columns': ['scenario','i','h','r','t'],
                                             'csvs': ['gen_h','opRes_supply_h'],
                                             'operation':  ['sum','sum']},
                  'scen_t':                 {'id_columns': ['scenario','t'],
                                             'csvs': ['cap_ivrt','gen_ivrt'],
                                             'operation':  ['sum','sum']},
                  'scen_rf_rt_trtype_t':    {'id_columns': ['scenario','rf','rt','trtype','t'],
                                             'csvs': ['tran_flow_out','tran_out','losses_tran_h'],
                                             'operation':  ['sum','sum']}
                                             }

    create_new = True #create a new .hyper file on the first iteration
    for this_pivot_name in pivot_dict:
        this_pivot_info = pivot_dict[this_pivot_name]
        col_defs = [ TableDefinition.Column(column_types[col][0], column_types[col][1], NULLABLE) for col in this_pivot_info['id_columns'] ] #probably need to manually change some of these names

        pivot = pd.DataFrame(columns = this_pivot_info['id_columns'])
        # Initialize the Tableau column definitions for the pivot table's ID columns:
        for this_csv, this_operation in zip(this_pivot_info['csvs'],this_pivot_info['operation']):
            this_df = pd.read_csv(output_path / ( this_csv + '_all.csv'))
            print(f'Processing {this_csv}')
            # Custom table manipulations below: 
            this_col_list = []
            if this_df.empty:
                print(f'Warning: {this_csv} is empty. Still adding a column of NULL values to the pivot table.')
            elif this_csv in ['systemcost_ba','systemcost_ba_bulk']:
                this_df = this_df.rename(columns={'sys_costs':'i'}) #so that it fits into the technology column in the pivoted table
                this_df = this_df.groupby(this_pivot_info['id_columns'],as_index=False).sum()
            elif this_csv == 'opRes_supply_h':
                this_df = this_df.pivot_table(index=this_pivot_info['id_columns'], columns='ortype', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                this_col_list = {'reg':'Reserve Supply - Reg (MWh)',
                                 'spin':'Reserve Supply - Spin (MWh)',
                                 'flex':'Reserve Supply - Flex (MWh)'}
                this_df = this_df.rename(columns=this_col_list)
                this_col_list = [ x for x in this_df.columns if x not in this_pivot_info['id_columns'] ]
            elif this_csv == 'reqt_price':
                this_df['type_subtype'] = this_df['type'] + '_' + this_df['subtype']
                this_df = this_df.pivot_table(index=this_pivot_info['id_columns'], columns='type_subtype', aggfunc=np.mean).droplevel(0,axis=1).reset_index()
                this_col_list = {'annual_cap_CO2':'CO2 Cap Compliance Price (2004 $)',
                                 'load_na':'Average Energy Price (2004 $/MWh)',
                                 'oper_res_flex':'Reserve Price - Flex (2004 $/MW-h)',
                                 'oper_res_reg':'Reserve Price - Reg (2004 $/MW-h)',
                                 'oper_res_spin':'Reserve Price - Spin (2004 $/MW-h)',
                                 'res_marg_ann_na':'Planning Reserve Compliance Price (2004 $)',
                                 'res_marg_na':'duplicate',
                                 'state_rps_CES':'State CES Compliance Price (2004 $)',
                                 'state_rps_RPS_All':'State All-RPS Price (2004 $)',
                                 'state_rps_RPS_Solar':'State Solar RPS Price (2004 $)'}
                this_df = this_df.rename(columns=this_col_list)
                this_df = this_df.drop(['duplicate'],axis=1)
                this_col_list = [ x for x in this_df.columns if x not in this_pivot_info['id_columns'] ]
            elif this_csv == 'reqt_quant':
                this_df['type_subtype'] = this_df['type'] + '_' + this_df['subtype']
                this_df = this_df.pivot_table(index=this_pivot_info['id_columns'], columns='type_subtype', aggfunc=np.sum).droplevel(0,axis=1).reset_index()
                this_col_list = {'annual_cap_CO2':'CO2 Emissions (Mt CO2)',
                                 'load_na':'Load (MWh)',
                                 'nat_gen_na':'Generation (MWh)',
                                 'oper_res_flex':'Reserve Provision - Flex (MW-h)',
                                 'oper_res_reg':'Reserve Provision - Reg (MW-h)',
                                 'oper_res_spin':'Reserve Provision - Spin (MW-h)',
                                 'res_marg_ann_na':'Planning Reserve Margin (%))',
                                 'res_marg_na':'duplicate',
                                 'state_rps_CES':'State CES Generation (MWh)',
                                 'state_rps_RPS_All':'State All-RPS Generation (MWh))',
                                 'state_rps_RPS_Solar':'State Solar RPS Generation (MWh)',
                                 'state_rps_RPS_Wind':'State Wind RPS Generation (MWh)'}
                this_df = this_df.rename(columns=this_col_list)
                this_df = this_df.drop(['duplicate'],axis=1)
                this_col_list = [ x for x in this_df.columns if x not in this_pivot_info['id_columns'] ]
            elif this_csv == 'systemcost_ba': #Special: we use bokehpivot preprocessing functions here for discounting, annualizing, and inflating 
                this_df_list = []
                for this_scenario in scenarios:
                    this_sc = pd.read_csv(Path(reeds_dir) / 'runs' / this_scenario / 'outputs' / 'systemcost_ba.csv', header=0, names=['cost_cat', 'r', 'year', 'Cost (Bil $)'])
                    dfs = {'sc': this_sc.copy(),
                           'existcap': pd.read_csv(Path(reeds_dir) / 'runs' / this_scenario / 'inputs_case' / 'cappayments.csv', header=0, names=['year', 'existingcap']),
                           'crf': pd.read_csv(Path(reeds_dir) / 'runs' / this_scenario / 'inputs_case' / 'crf.csv', header=None, names=['year', 'crf'])}
                    this_scen_df = pre_systemcost(dfs,annualize=True, remove_existing=True, crf_from_user=True, shift_capital=True) #this func is from reeds2.py
                    
                    this_sc['Cost (Bil $)'] = inflate_series(this_sc['Cost (Bil $)']) * 1e-9 #convert to billions and desired dollar year (DOLLAR_YEAR)
                    this_sc = this_sc.rename(columns={'Cost (Bil $)':f'Annual Cost with Non-Annualized CapEx (Bil {DOLLAR_YEAR}$)'})
                    this_scen_df = pd.merge(this_scen_df,this_sc,on=['r','year','cost_cat'],how='outer') #also pull in annual (not annualized) cost output straight from GAMS
                    this_scen_df['scenario'] = this_scenario
                    this_df_list.append(this_scen_df)
                this_df = pd.concat(this_df_list)
                this_col_list = {'year':'t',
                                 'cost_cat':'i',
                                 'Cost (Bil $)':f'Undiscounted Annualized Cost (Bil {DOLLAR_YEAR}$)',
                                 'Discounted Cost (Bil $)':f'Annualized Cost Discounted to {PV_YEAR} (Bil {DOLLAR_YEAR}$)'}
                this_df = this_df.rename(columns=this_col_list)
                this_col_list = [ x for x in this_df.columns if x not in this_pivot_info['id_columns'] ]
            # For the rest of the csvs, just sum or take an average:
            elif this_pivot_info['operation'][this_pivot_info['csvs'] == this_csv] == 'sum':
                this_df = this_df.groupby(this_pivot_info['id_columns'],as_index=False).sum()
            elif this_pivot_info['operation'][this_pivot_info['csvs'] == this_csv] == 'mean':
                this_df = this_df.groupby(this_pivot_info['id_columns'],as_index=False).mean()
            elif this_operation not in ['sum','mean']: 
                raise ValueError(f"""Operation "{this_operation}" is not implemented.""")

            # Unforgivably hacky--Anywhere there's a "2004" in a column name, convert the dollar year to the one desired:
            if any('2004' in s for s in this_col_list):
                for s in [x for x in this_col_list if '2004' in x]:
                    # this_df[s] = inflate_series(this_df[s]) #this bokehpivot function uses the dollar year DOLLAR_YEAR, via core.GL (set above)
                    this_col_list[this_col_list==s] = s.replace('2004',DOLLAR_YEAR)

            # Record the Tableau column definition(s) for this csv:
            if this_col_list:
                this_col_def = [ TableDefinition.Column(col, SqlType.double(), NULLABLE) for col in this_col_list ]
                col_defs = col_defs + this_col_def
            else:
                this_df = this_df[this_pivot_info['id_columns'] + csv_list.loc[csv_list['csv']==this_csv,'label'].to_list()]
                this_col_def = TableDefinition.Column(csv_list.loc[csv_list['csv']==this_csv,'label'].to_list()[0], SqlType.double(), NULLABLE)
                col_defs.append(this_col_def)

            pivot = pd.merge(pivot,this_df,how='outer',on=this_pivot_info['id_columns'])

        pivot.fillna('NULL').to_csv(output_path / (this_pivot_name + '.csv'),index=False) #have to fill NAs to NULL for direct writing to .hyper
        
        # Write to .hyper file:
        this_table_def = TableDefinition(
            table_name=this_pivot_name,
            columns = col_defs
        )
        try:
            update_hyper_file_from_csv(this_table_def,output_path / (this_pivot_name + '.csv'),output_path / (output_dir + '_pivot.hyper'),create_new)
            create_new = False
            print(f'''Added {this_pivot_name} to {(output_dir + '_pivot.hyper')}.''')
        except HyperException as ex:
            print(ex)
            
    print('Done.')