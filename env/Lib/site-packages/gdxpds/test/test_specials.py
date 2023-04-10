# [LICENSE]
# Copyright (c) 2020, Alliance for Sustainable Energy.
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

import logging
import os
import subprocess as subp

import gdxpds.gdx
import gdxpds.special
from gdxpds.test import base_dir, run_dir
from gdxpds.test.test_session import manage_rundir
from gdxpds.test.test_conversions import roundtrip_one_gdx

import gdxcc
import numpy as np
import pandas as pds
import pytest

logger = logging.getLogger(__name__)


def value_column_index(sym,gams_value_type):
    for i, val in enumerate(sym.value_cols):
        if val[1] == gams_value_type.value:
            break
    return len(sym.dims) + i


def test_roundtrip_just_special_values(manage_rundir):
    outdir = os.path.join(run_dir,'special_values')
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    # create gdx file containing all special values
    with gdxpds.gdx.GdxFile() as f:
        df = pds.DataFrame([['sv' + str(i+1), gdxpds.special.SPECIAL_VALUES[i]] for i in range(gdxcc.GMS_SVIDX_MAX-2)],
                           columns=['sv','Value'])
        logger.info("Special values are:\n{}".format(df))

        # save this directly as a GdxSymbol
        filename = os.path.join(outdir,'direct_write_special_values.gdx')
        ret = gdxcc.gdxOpenWrite(f.H,filename,"gdxpds")
        if not ret:
            raise gdxpds.gdx.GdxError(f.H,"Could not open {} for writing. Consider cloning this file (.clone()) before trying to write".format(repr(filename)))
        # write the universal set
        f.universal_set.write()
        if not gdxcc.gdxDataWriteStrStart(f.H,
                                          'special_values',
                                          '',
                                          1,
                                          gdxpds.gdx.GamsDataType.Parameter.value,
                                          0):
            raise gdxpds.gdx.GdxError(f.H,"Could not start writing data for symbol special_values")
        # set domain information
        if not gdxcc.gdxSymbolSetDomainX(f.H,1,[df.columns[0]]):
            raise gdxpds.gdx.GdxError(f.H,"Could not set domain information for special_values.")
        values = gdxcc.doubleArray(gdxcc.GMS_VAL_MAX)
        for row in df.itertuples(index=False,name=None):
            dims = [str(x) for x in row[:1]]
            vals = row[1:]
            for _col_name, col_ind in gdxpds.gdx.GAMS_VALUE_COLS_MAP[gdxpds.gdx.GamsDataType.Parameter]:
                values[col_ind] = float(vals[col_ind])
            gdxcc.gdxDataWriteStr(f.H,dims,values)
        gdxcc.gdxDataWriteDone(f.H)
        gdxcc.gdxClose(f.H)

    # general test for expected values
    def check_special_values(gdx_file):
        df = gdx_file['special_values'].dataframe
        for i, val in enumerate(df['Value'].values):
            assert gdxpds.special.pd_val_equal(val, gdxpds.special.NUMPY_SPECIAL_VALUES[i])

    # now roundtrip it gdx-only
    with gdxpds.gdx.GdxFile(lazy_load=False) as f:
        f.read(filename)
        check_special_values(f)
        with f.clone() as g:
            rt_filename = os.path.join(outdir,'roundtripped.gdx')
            g.write(rt_filename)
    with gdxpds.gdx.GdxFile(lazy_load=False) as g:
        g.read(filename)
        check_special_values(g)

    # now roundtrip it through csv
    roundtripped_gdx = roundtrip_one_gdx(filename,'roundtrip_just_special_values')
    with gdxpds.gdx.GdxFile(lazy_load=False) as h:
        h.read(roundtripped_gdx)
        check_special_values(h)
    

def test_roundtrip_special_values(manage_rundir):
    filename = 'OptimalCSPConfig_Out.gdx'
    original_gdx = os.path.join(base_dir,filename)
    roundtripped_gdx = roundtrip_one_gdx(filename,'roundtrip_special_values')
    data = []
    for gdx_file in [original_gdx, roundtripped_gdx]:
        with gdxpds.gdx.GdxFile(lazy_load=False) as gdx:
            data.append([])
            gdx.read(gdx_file)
            sym = gdx['calculate_capacity_value']
            assert sym.data_type == gdxpds.gdx.GamsDataType.Equation
            val = sym.dataframe.iloc[0,value_column_index(sym,gdxpds.gdx.GamsValueType.Marginal)]
            assert gdxpds.special.is_np_sv(val)
            data[-1].append(val)
            sym = gdx['CapacityValue']
            assert sym.data_type == gdxpds.gdx.GamsDataType.Variable
            val = sym.dataframe.iloc[0,value_column_index(sym,gdxpds.gdx.GamsValueType.Upper)]
            assert gdxpds.special.is_np_sv(val)
            data[-1].append(val)
    data = list(zip(*data))
    for pt in data:
        for i in range(1,len(pt)):
            assert (pt[i] == pt[0]) or (np.isnan(pt[i]) and np.isnan(pt[0]))


def test_special_integrity():
    """
    Check that the special values line up
    """
    assert all(sv in gdxpds.special.GDX_TO_NP_SVS for sv in gdxpds.special.SPECIAL_VALUES)
    assert all(sv in gdxpds.special.NP_TO_GDX_SVS for sv in gdxpds.special.NUMPY_SPECIAL_VALUES)

    for val in gdxpds.special.SPECIAL_VALUES:
        assert gdxpds.special.NP_TO_GDX_SVS[gdxpds.special.GDX_TO_NP_SVS[val]] == val

    for val in gdxpds.special.NUMPY_SPECIAL_VALUES:
        # Can't use "==", as None != NaN
        assert gdxpds.special.pd_val_equal(gdxpds.special.GDX_TO_NP_SVS[gdxpds.special.NP_TO_GDX_SVS[val]], val)


def test_numpy_eps():
    assert(gdxpds.special.is_np_eps(np.finfo(float).eps))
    assert(not gdxpds.special.is_np_eps(float(0.0)))
    assert(not gdxpds.special.is_np_eps(2.0 * np.finfo(float).eps))


