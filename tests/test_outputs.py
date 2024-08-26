import os
import pandas as pd

def test_check_outputs(casepath):
    outputs_folder = os.path.join(casepath, 'outputs')
    e_report_params_path = os.path.join(casepath, 'e_report_params.csv')

    # each parameter in e_report_params.csv should be associated with an output csv file
    expected_params = pd.read_csv(e_report_params_path, comment='#')
    expected_files = [param.split('(')[0] + '.csv' for param in expected_params.iloc[:,0]]

    # cap_out gets written to cap.csv instead of cap_out.csv, update the expected_files list accordingly
    expected_files.append('cap.csv')
    expected_files.remove('cap_out.csv')

    missing_files = [filename for filename in expected_files if not os.path.exists(os.path.join(outputs_folder, filename))]

    assert (len(missing_files) == 0), f"Missing {len(missing_files)} output files: {missing_files}"


def test_reeds_reports(casepath):
    # given the path to a ReEDS run, this checks for the reeds-report and reeds-report-reduced folders
    outputs_folder = os.path.join(casepath, 'outputs')
    reeds_report_folder = os.path.join(outputs_folder, 'reeds-report')
    reeds_report_reduced_folder = os.path.join(outputs_folder, 'reeds-report-reduced')

    assert os.path.isdir(reeds_report_folder), "reeds-reports folder does not exist"
    assert os.path.isdir(reeds_report_reduced_folder), "reeds-reports-reduced folder does not exist"