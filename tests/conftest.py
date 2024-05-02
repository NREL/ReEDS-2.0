import os
import json
import pytest
from pathlib import Path

DATA_TEST_DIR = "data"


def pytest_addoption(parser):
    parser.addoption("--casepath", action="store", help="File path to ReEDS run.")


# Read file map
@pytest.fixture(scope="module", autouse=True)
def fmap(request):
    tests_dir = os.path.dirname(request.module.__file__)
    data_filename = os.path.join(tests_dir, DATA_TEST_DIR, "r2x_files.json")
    with open(data_filename, "r") as f:
        return json.load(f)


# Get folder of ReEDS path
@pytest.fixture()
def casepath(pytestconfig):
    return Path(pytestconfig.getoption("casepath"))


@pytest.fixture
def r2x_files(casepath, fmap):
    file_list = []
    for _, i_dict in fmap.items():
        if i_dict.get("input"):
            fpath = casepath.joinpath("inputs_case")
        else:
            fpath = casepath.joinpath("outputs")
        file_list.append(fpath.joinpath(i_dict.get("fname")))
    return file_list


@pytest.hookimpl
def pytest_generate_tests(metafunc):
    tests_dir = os.path.dirname(metafunc.module.__file__)
    data_filename = os.path.join(tests_dir, DATA_TEST_DIR, "r2x_files.json")
    casepath = Path(metafunc.config.getoption("casepath"))
    with open(data_filename, "r") as f:
        fmap = json.load(f)
    file_list = []
    for _, i_dict in fmap.items():
        if i_dict.get("input"):
            fpath = casepath.joinpath("inputs_case")
        else:
            fpath = casepath.joinpath("outputs")

        if not i_dict.get("optional", True) and i_dict.get("column_mapping"):
            file_list.append(fpath.joinpath(i_dict.get("fname")))
    if "validation_files" in metafunc.fixturenames:
        metafunc.parametrize(
            "validation_files",
            file_list,
            ids=list(map(lambda fpath: fpath.stem, file_list)),  # To actually know what file
        )
