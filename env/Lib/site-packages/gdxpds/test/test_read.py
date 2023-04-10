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

import pytest

import gdxpds.gdx
from gdxpds import to_dataframes
from gdxpds.test import base_dir

logger = logging.getLogger(__name__)

def test_read():
    filename = 'all_generator_properties_input.gdx'
    gdx_file = os.path.join(base_dir,filename)
    with gdxpds.gdx.GdxFile() as f:
        f.read(gdx_file)
        for symbol in f:
            symbol.load()

def test_read_none():
    with pytest.raises(gdxpds.gdx.GdxError) as excinfo:
        to_dataframes(None)
    assert "Could not open None" in str(excinfo.value)

def test_read_path():
    filename = 'all_generator_properties_input.gdx'
    from pathlib import Path
    gdx_file = Path(base_dir) / filename
    to_dataframes(gdx_file)

def test_unload():
    filename = 'all_generator_properties_input.gdx'
    gdx_file = os.path.join(base_dir,filename)
    with gdxpds.gdx.GdxFile() as f:
        f.read(gdx_file)
        assert not f['startupfuel'].loaded
        assert f['startupfuel'].dataframe.empty

        f['startupfuel'].load()
        assert f['startupfuel'].loaded
        assert not f['startupfuel'].dataframe.empty
        assert 'CC' in f['startupfuel'].dataframe['*'].tolist()

        f['startupfuel'].unload()
        assert not f['startupfuel'].loaded
        assert f['startupfuel'].dataframe.empty
        
        f['startupfuel'].load()
        assert f['startupfuel'].loaded
        assert not f['startupfuel'].dataframe.empty
        assert 'CC' in f['startupfuel'].dataframe['*'].tolist()
