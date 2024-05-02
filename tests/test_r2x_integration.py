from utils import get_missing_files, get_missing_columns


def test_r2x_files_exists(fmap, r2x_files):
    """Test that the files used in downstream models are created"""
    file_list = [
        value["fname"]
        for _, value in fmap.items()
        if not value.get("optional")  # Only files that are not optional
    ]

    fnames = list(map(lambda fpath: fpath.name, r2x_files))
    filest_to_check = list(map(lambda fpath: r2x_files[fnames.index(fpath)], file_list))
    missing_files = get_missing_files(filest_to_check)
    assert (
        len(missing_files) == 0
    ), f"The following files are missing: {list(map(lambda fpath: fpath.name, missing_files))}"



def test_r2x_files_column_check(fmap, validation_files):
    """Test that files needed have the appropiate columns"""
    file_column_dict = {
        value["fname"]: value["column_mapping"].keys()
        for _, value in fmap.items()
        if not value.get("optional", False)  # Only files that are not optional
        if value.get("column_mapping", False)  # Only process files with column_mapping
    }

    # fnames = list(map(lambda fpath: fpath.name, files))
    fname = validation_files.name
    fpath = validation_files

    missing_columns = []
    expected_columns = file_column_dict[fname]
    missing_columns = get_missing_columns(fpath, expected_columns)
    assert len(missing_columns) == 0, f"Missing columns in {fpath}: {missing_columns}"
