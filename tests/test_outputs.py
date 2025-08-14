import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds

def test_output_files(casepath):
    outputs_folder = os.path.join(casepath, 'outputs')
    e_report_params_path = os.path.join(casepath, 'e_report_params.csv')
    lastyear = reeds.io.get_years(casepath)[-1]

    # each parameter in e_report_params.csv should be associated with an output csv file
    e_report_params = pd.read_csv(e_report_params_path, comment='#')
    e_report_params['fpath'] = e_report_params.param.map(lambda x: x.split('(')[0])
    # rename outputs as specified by output_rename column
    rename = e_report_params.loc[
        ~e_report_params.output_rename.isnull()
    ].set_index('fpath').output_rename.to_dict()
    e_report_params['fpath'] = e_report_params['fpath'].replace(rename) + '.csv'

    # Include additional files in outputs folder that should be generated for each run
    expected_plots = [
        # Static plots (transmission_maps.py)
        os.path.join('maps', i) + '.png' for i in [
            'bars_retirements_additions',
            'inputs_repdays',
            f'plot_dispatch-weightwidth-{lastyear}',
        ]
    ]

    expected_files = (
        e_report_params.fpath.tolist()
        + [
            # Standard bokeh outputs (postprocessing/bokehpivot)
            os.path.join('reeds-report', 'report.html'),
            os.path.join('reeds-report', 'report.xlsx'),
            # Health damages (health_damage_calculations.py)
            'health_damages_caused_r.csv',
            # Retail rates (retail_rate_calculations.py)
            os.path.join('retail', 'retail_rate_components.csv'),
        ]
        + expected_plots
    )

    missing_files = [
        filename for filename in expected_files
        if not os.path.exists(os.path.join(outputs_folder, filename))
    ]

    assert (len(missing_files) == 0), f"Missing {len(missing_files)} output files: {missing_files}"
