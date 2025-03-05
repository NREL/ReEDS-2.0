"""
Tests for reeds_to_rev
"""
import logging
from pathlib import Path
import runpy
import sys
from conftest import temporary_parent_directory

import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

import path_fix as _  # noqa: F401


def fix_sc_paths(run_folder, integration_data_path):
    """
    Edits values in inputs_case/rev_paths.csv so that the sc_file values are
    preceded by the integration_data_path, and sc_path values are the parent directory
    of the sc_file paths.

    Parameters
    ----------
    run_folder : pathlib.Path
        ReEDS run folder, containing inputs_case/rev_paths.csv
    integration_data_path : pathlib.Path
        Path that will be prepended to sc_file values.
    """
    # fix supply curve paths in the rev_paths.csv
    rev_paths_src = run_folder.joinpath("inputs_case", "rev_paths.csv")
    sc_info_df = pd.read_csv(rev_paths_src)
    sc_info_df["sc_file"] = sc_info_df["sc_file"].apply(
        lambda x: integration_data_path.joinpath(x).as_posix()
    )
    sc_info_df["sc_path"] = sc_info_df["sc_file"].apply(
        lambda x: Path(x).parent.as_posix()
    )
    sc_info_df.to_csv(rev_paths_src, index=False, header=True)


def remove_stream_handlers(logger_name):
    """
    Removes any existing StreamHandlers from the logger named
    ``""``. This is necessary to avoid duplicate (or more) messages
    logging to stdout when running multiple tests involving reeds_to_rev.
    """

    stream_handlers = [
        h
        for h in logging.getLogger(logger_name).handlers
        if isinstance(h, logging.StreamHandler)
    ]
    for stream_handler in stream_handlers:
        logging.getLogger(logger_name).removeHandler(stream_handler)


def test_reeds_to_rev_usage(hourlize_path):
    """
    Basic test of reeds_to_rev.py to make sure it can be run
    as a command/script and will return usage instructions when
    --help is specified.
    """

    sys.argv = [None, "--help"]
    try:
        runpy.run_path(hourlize_path.joinpath("reeds_to_rev.py"), run_name="__main__")
    except SystemExit as e:
        assert e.code == 0, "reeds_to_rev.py encountered an error."


@pytest.mark.parametrize(
    "tech",
    [
        "egs_allkm",
        "geohydro_allkm",
        "wind-ons",
        "wind-ofs",
        "upv",
    ],
)
@pytest.mark.parametrize("out_format", ["reduced", "full"])
def test_reeds_to_rev_integration(tech, out_format, test_data_path, hourlize_path):
    """
    Integration test of reeds_to_rev.py to ensure it returns the
    expected outputs. This test covers the following techs:
    upv, wind-ons, wind-ofs.
    """

    if tech in ["egs_allkm", "geohydro_allkm"]:
        integration_data_path = test_data_path.joinpath("r2r_integration_geothermal")
    else:
        integration_data_path = test_data_path.joinpath("r2r_integration")

    reeds_source_path = integration_data_path.joinpath("reeds")

    with temporary_parent_directory(reeds_source_path) as temp_reeds:
        reeds_path = Path(temp_reeds.name)
        run_folder = reeds_path.joinpath("reeds")

        fix_sc_paths(run_folder, integration_data_path)

        remove_stream_handlers("reeds_to_rev")
        sys.argv = [
            None,
            reeds_path.as_posix(),
            run_folder.as_posix(),
            "priority",
            "--priority",
            "cost",
            "--tech",
            tech,
        ]
        if out_format == "reduced":
            sys.argv.append("--reduced_only")

        runpy.run_path(hourlize_path.joinpath("reeds_to_rev.py"), run_name="__main__")

        if out_format == "reduced":
            out_csv_name = f"df_sc_out_{tech}_reduced.csv"
        else:
            out_csv_name = f"df_sc_out_{tech}.csv"

        result_csv_path = run_folder.joinpath("outputs", out_csv_name)
        assert result_csv_path.exists()

        expected_csv_path = integration_data_path.joinpath(
            "expected_results", out_csv_name
        )
        assert expected_csv_path.exists()

        result_df = pd.read_csv(result_csv_path)
        expected_df = pd.read_csv(expected_csv_path)

        assert_frame_equal(result_df, expected_df, check_like=True, check_dtype=False)


def test_reeds_to_rev_simul_fill_upv(integration_data_path, hourlize_path):
    """
    Integration test of reeds_to_rev.py to ensure it returns the
    expected outputs when using the simultaneous fill method. This test only covers
    UPV since the behavior should be the same for other technologies.
    """

    reeds_source_path = integration_data_path.joinpath("reeds")

    with temporary_parent_directory(reeds_source_path) as temp_reeds:
        reeds_path = Path(temp_reeds.name)
        run_folder = reeds_path.joinpath("reeds")

        fix_sc_paths(run_folder, integration_data_path)

        remove_stream_handlers("reeds_to_rev")
        sys.argv = [
            None,
            reeds_path.as_posix(),
            run_folder.as_posix(),
            "simultaneous",
            "--reduced_only",
            "--tech",
            "upv",
        ]
        try:
            runpy.run_path(
                hourlize_path.joinpath("reeds_to_rev.py"), run_name="__main__"
            )
        except SystemExit as e:
            assert e.code == 0, "reeds_to_rev.py encountered an error."

        out_csv_name = "df_sc_out_upv_reduced.csv"
        result_csv_path = run_folder.joinpath("outputs", out_csv_name)
        assert result_csv_path.exists()

        expected_csv_path = integration_data_path.joinpath(
            "expected_results", "df_sc_out_upv_reduced_simul_fill.csv"
        )
        assert expected_csv_path.exists()

        result_df = pd.read_csv(result_csv_path)
        expected_df = pd.read_csv(expected_csv_path)

        assert_frame_equal(result_df, expected_df)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
