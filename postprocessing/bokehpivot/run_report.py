'''
This file allows reports to be run directly from this python script (without need for the bokeh server and bokehpivot UI).

Easiest process:
1. Update bokehpivot/reeds_scenarios.csv with desired scenario names and paths.
2. If a different report is desired (other than standard_report_reduced), update 'report_path' (below).
3. Run this file. If you haven't updated 'output_dir', you'll find the results in bokehpivot/out.

If you run this file from another location, update 'bokehpivot_dir' below.
'''
import os
import sys
import pandas as pd
import shutil
import importlib
#EDIT: Manually set bokehpivot_dir to another path if this file is in a different location.
bokehpivot_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, bokehpivot_dir)
import reeds_bokeh as rb

#EDIT THE FOLLOWING FIELDS
report_path = f'{bokehpivot_dir}/reports/templates/reeds2/standard_report_reduced.py' #Path to report that is to be run
diff = 'Yes' #Use 'Yes' if adding differences to a base case, specified below (default base case is first scenario in reeds_scenarios.csv)

data_source = f'{bokehpivot_dir}/reeds_scenarios.csv' #either a scenarios.csv file or ReEDS run directory (or directories separated by pipe symbols).
base = pd.read_csv(data_source)['name'][0] #Name of base case for when diff='Yes'. Defaults to first case in reeds_scenarios.csv.
output_dir = f'{bokehpivot_dir}/out/reeds_report' #This is the directory that will be created to contain the report. If it already exists, the existing directory will be archived with a date.
data_type = 'ReEDS 2.0'
scenario_filter = 'all' #'all' or string of comma-separated names.
html_num = 'one' #'one' or 'multiple'. 'one' will create one html file with all sections, and 'multiple' will create a separate html file for each section
report_format = 'html,excel' #'html', 'excel', or 'csv', or any combination separated by commas
auto_open = 'Yes' #'Yes' or 'No'. Automatically open the resulting report excel and html files when they are created.

#DON'T EDIT THIS SECTION
report_dir = os.path.dirname(report_path)
sys.path.insert(1, report_dir)
report_name = os.path.basename(report_path)[:-3]
report = importlib.import_module(report_name)
rb.reeds_static(data_type, data_source, scenario_filter, diff, base, report.static_presets, report_path, report_format, html_num, output_dir, auto_open)
shutil.copy2(os.path.realpath(__file__), output_dir)

#CUSTOM POSTPROCESSING
#Any post-processing of the excel data that was produced. you can read excel data into dataframes by importing pandas and using pandas.read_excel()
