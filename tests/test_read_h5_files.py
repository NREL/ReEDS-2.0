import h5py
import numpy as np
import pandas as pd
import pytest
from pandas import HDFStore

import reeds


@pytest.fixture
def pandas_h5(tmp_path, n_cols=10, n_rows=10):
    fpath = tmp_path / "pandas.h5"
    with HDFStore(fpath, "w") as f:
        column_names = [f"1_p{col:02}" for col in range(n_cols)]
        random_data = np.random.rand(n_rows, n_cols)
        data = pd.DataFrame(random_data, columns=column_names)
        f.put("data", data)
    return fpath


@pytest.fixture
def load_h5(tmp_path, n_cols=10):
    fpath = tmp_path / "regular.h5"
    with h5py.File(fpath, "w") as f:
        solve_years = [2022, 2023, 2024]
        hours = range(24)
        columns = [f"p{i:02}" for i in range(n_cols)]
        f.create_dataset("columns", data=columns)
        for year in solve_years:
            # Create a DataFrame with random data
            data = pd.DataFrame(
                data=np.random.randn(len(hours), n_cols), index=hours, columns=columns
            )
            f.create_dataset(str(year), data=data, dtype="float32")

    return fpath


def test_read_file(pandas_h5):
    # Assert that we raise if the file is not found.
    with pytest.raises(FileNotFoundError):
        _ = reeds.io.read_file("random_non_existing_path.h5")

    pandas_df = pd.read_hdf(pandas_h5)
    pandas_test = reeds.io.read_file(pandas_h5)
    assert isinstance(
        pandas_df, pd.DataFrame
    ), "Function did not return a pandas dataframe."
    assert all(
        pandas_test[column].dtype == np.float32 for column in pandas_test.columns
    ), "Some columns were not converted to float32. Check content of columns"
    assert (
        pandas_df.size == pandas_test.size
    ), "Size of dataframes is different. Check file for multiple keys"


def test_read_h5py_file(load_h5):
    h5_df = reeds.io.read_h5py_file(load_h5)
    assert isinstance(h5_df, pd.DataFrame)
    assert h5_df.size == 720  # 3 years * 24 rows * 10 colums
    assert h5_df.index.names == ["year", "hour"]
