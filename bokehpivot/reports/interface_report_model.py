import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import reeds_bokeh as rb
import importlib

data_type = sys.argv[1]
data_source = sys.argv[2]
scenario_filter = sys.argv[3]
diff = sys.argv[4]
base = sys.argv[5]
report_path = sys.argv[6]
html_num = sys.argv[7]
output_dir = sys.argv[8]
auto_open = sys.argv[9]

report_dir = os.path.dirname(report_path)
sys.path.insert(1, report_dir)
report_name = os.path.basename(report_path)[:-3]
report = importlib.import_module(report_name)
rb.reeds_static(data_type, data_source, scenario_filter, diff, base, report.static_presets, report_path, 'both', html_num, output_dir, auto_open)
