import os
import sys
import importlib
import site

def run_report(data_type, data_source, scenario_filter, diff, base, report_path, report_format, html_num, output_dir, auto_open):
    # import reeds_bokeh here to since path may differ for different entry points
    import reeds_bokeh as rb
    report_dir = os.path.dirname(report_path)
    sys.path.insert(1, report_dir)
    report_name = os.path.basename(report_path)[:-3]
    report = importlib.import_module(report_name)
    rb.reeds_static(data_type, data_source, scenario_filter, diff, base, report.static_presets, report_path, report_format, html_num, output_dir, auto_open)

if __name__ == '__main__':
    bokeh_path =  os.path.join(sys.path[0], '..')
    site.addsitedir(os.path.join(bokeh_path))
    data_type, data_source, scenario_filter, diff, base, report_path, report_format, html_num, output_dir, auto_open = sys.argv[1:]
    run_report(data_type, data_source, scenario_filter, diff, base, report_path, report_format, html_num, output_dir, auto_open)