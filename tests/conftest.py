import os
import pytest
from pathlib import Path
import sys

def pytest_addoption(parser):
    parser.addoption(
        "--casepath", 
        action="store", 
        help="File path to ReEDS run."
    )

# Get folder of ReEDS path
@pytest.fixture()
def casepath(pytestconfig):
    return Path(pytestconfig.getoption("casepath"))
