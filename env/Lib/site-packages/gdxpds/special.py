# [LICENSE]
# Copyright (c) 2018, Alliance for Sustainable Energy.
# All rights reserved.
#
# Redistribution and use in source and binary forms,
# with or without modification, are permitted provided
# that the following conditions are met:
#
# 1. Redistributions of source code must retain the above
# copyright notice, this list of conditions and the
# following disclaimer.
#
# 2. Redistributions in binary form must reproduce the
# above copyright notice, this list of conditions and the
# following disclaimer in the documentation and/or other
# materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the
# names of its contributors may be used to endorse or
# promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# [/LICENSE]

import copy
import logging

import gdxcc
import numpy as np


# List of numpy special values in gdxGetSpecialValues order
#                      1E300,  2E300,  3E300,   4E300,               5E300
NUMPY_SPECIAL_VALUES = [None, np.nan, np.inf, -np.inf, np.finfo(float).eps]

logger = logging.getLogger(__name__)


def convert_gdx_to_np_svs(df, num_dims):
    """
    Converts GDX special values to the corresponding numpy versions.

    Parmeters
    ---------
    df : pandas.DataFrame
        a GdxSymbol DataFrame as it was read directly from GDX
    num_dims : int
        the number of columns in df that list the dimension values for which the
        symbol value is non-zero / non-default

    Returns
    -------
    pandas.DataFrame
        copy of df for which all GDX special values have been converted to
        their numpy equivalents
    """

    # create clean copy of df
    try:
        tmp = copy.deepcopy(df)
    except:
        logger.warning("Unable to deepcopy:\n{}".format(df))
        tmp = copy.copy(df)

    # apply the map to the value columns and merge with the dimensional information
    tmp = (tmp.iloc[:, :num_dims]).merge(tmp.iloc[:, num_dims:].replace(GDX_TO_NP_SVS, value=None),
                                         left_index=True, right_index=True)
    return tmp


def is_np_eps(val):
    """
    Parameters
    ----------
    val : numeric
        value to test

    Returns
    -------
    bool
        True if val is equal to eps (np.finfo(float).eps), False otherwise
    """
    return np.abs(val - NUMPY_SPECIAL_VALUES[-1]) < NUMPY_SPECIAL_VALUES[-1]


def is_np_sv(val):
    """
    Parameters
    ----------
    val : numeric
        value to test

    Returns
    -------
    bool
        True if val is NaN, eps, or is in NUMPY_SPECIAL_VALUES; False otherwise
    """
    return np.isnan(val) or (val in NUMPY_SPECIAL_VALUES) or is_np_eps(val)


def convert_np_to_gdx_svs(df, num_dims):
    """
    Converts numpy special values to the corresponding GDX versions.

    Parmeters
    ---------
    df : pandas.DataFrame
        a GdxSymbol DataFrame in pandas/numpy form
    num_dims : int
        the number of columns in df that list the dimension values for which the
        symbol value is non-zero / non-default

    Returns
    -------
    pandas.DataFrame
        copy of df for which all numpy special values have been converted to
        their GDX equivalents
    """

    # converts a single value; NANs are assumed already handled
    def convert_approx_eps(value):
        # eps values are not always caught by ==, use is_np_eps which applies
        # a tolerance
        if is_np_eps(value):
            return SPECIAL_VALUES[4]
        return value

    # get a clean copy of df
    try:
        tmp = copy.deepcopy(df)
    except:
        logger.warning("Unable to deepcopy:\n{}".format(df))
        tmp = copy.copy(df)

    # fillna and apply map to value columns, then merge with dimensional columns
    try:
        values = tmp.iloc[:, num_dims:].replace(NP_TO_GDX_SVS, value=None).applymap(convert_approx_eps)
        tmp = (tmp.iloc[:, :num_dims]).merge(values, left_index=True, right_index=True)
    except:
        logger.error("Unable to convert numpy special values to GDX special values." + \
                     "num_dims: {}, dataframe:\n{}".format(num_dims, df))
        raise
    return tmp


def pd_isnan(val):
    """
    Utility function for identifying None or NaN (which are indistinguishable in pandas).

    Parameters
    ----------
    val : numeric
        value to test

    Returns
    -------
    bool
        True if val is a GDX encoded special value that maps to None or numpy.nan;
        False otherwise
    """
    return val is None or val != val


def pd_val_equal(val1, val2):
    """
    Utility function used to test special value conversions.

    Parameters
    ----------
    val1 : float or None
        first value to compare
    val2 : float or None
        second value to compare

    Returns
    -------
    bool
        True if val1 and val2 are equal in the sense of == or they are
        both NaN/None. The values that map to None and np.nan are assumed
        to be equal because pandas cannot be relied upon to make the
        distinction.
    """
    return pd_isnan(val1) and pd_isnan(val2) or val1 == val2


def gdx_isnan(val,gdxf):
    """
    Utility function for equating the GDX special values that map to None or NaN
    (which are indistinguishable in pandas).

    Parameters
    ----------
    val : numeric
        value to test
    gdxf : GdxFile
        GDX file containing the value. Provides np_to_gdx_svs map.

    Returns
    -------
    bool
        True if val is a GDX encoded special value that maps to None or numpy.nan;
        False otherwise
    """
    return val in [SPECIAL_VALUES[0], SPECIAL_VALUES[1]]


def gdx_val_equal(val1,val2,gdxf):
    """
    Utility function used to test special value conversions.

    Parameters
    ----------
    val1 : float or GDX special value
        first value to compare
    val2 : float or GDX special value
        second value to compare
    gdxf : GdxFile
        GDX file containing val1 and val2

    Returns
    -------
    bool
        True if val1 and val2 are equal in the sense of == or they are
        equivalent GDX-format special values. The values that map to None
        and np.nan are assumed to be equal because pandas cannot be relied
        upon to make the distinction.
    """
    if gdx_isnan(val1, gdxf) and gdx_isnan(val2, gdxf):
        return True
    return val1 == val2


def load_specials(gams_dir_finder):
    """
    Load special values

    Needs to be called after gdxcc is loaded. Populates the module attributes
    SPECIAL_VALUES, GDX_TO_NP_SVS, and NP_TO_GDX_SVS.

    Parameters
    ----------
    gams_dir_finder : :class:`gdxpds.tools.GamsDirFinder`
    """
    global SPECIAL_VALUES
    global GDX_TO_NP_SVS
    global NP_TO_GDX_SVS

    H = gdxcc.new_gdxHandle_tp()
    rc = gdxcc.gdxCreateD(H, gams_dir_finder.gams_dir, gdxcc.GMS_SSSIZE)
    if not rc:
        raise Exception(rc[1])
    # get special values
    special_values = gdxcc.doubleArray(gdxcc.GMS_SVIDX_MAX)
    gdxcc.gdxGetSpecialValues(H, special_values)

    SPECIAL_VALUES = []
    GDX_TO_NP_SVS = {}
    NP_TO_GDX_SVS = {}
    for i in range(gdxcc.GMS_SVIDX_MAX):
        if i >= len(NUMPY_SPECIAL_VALUES):
            break
        SPECIAL_VALUES.append(special_values[i])
        gdx_val = special_values[i]
        GDX_TO_NP_SVS[gdx_val] = NUMPY_SPECIAL_VALUES[i]
        NP_TO_GDX_SVS[NUMPY_SPECIAL_VALUES[i]] = gdx_val

    gdxcc.gdxFree(H)


# These values are populated by load_specials, called in load_gdxcc
SPECIAL_VALUES = []
GDX_TO_NP_SVS = {}
NP_TO_GDX_SVS = {}
