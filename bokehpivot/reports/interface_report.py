import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import core
import importlib

data_type = sys.argv[1]
data_source = sys.argv[2]
report_path = sys.argv[3]
html_num = sys.argv[4]
output_dir = sys.argv[5]
auto_open = sys.argv[6]

report_dir = os.path.dirname(report_path)
sys.path.insert(1, report_dir)
report_name = os.path.basename(report_path)[:-3]
report = importlib.import_module(report_name)
core.static_report(data_type, data_source, report.static_presets, report_path, 'both', html_num, output_dir, auto_open)
