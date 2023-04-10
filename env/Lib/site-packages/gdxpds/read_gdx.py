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

from collections import OrderedDict
import logging

# gdxpds needs to be imported before pandas to try to avoid library conflict on 
# Linux that causes a segmentation fault.
from gdxpds.tools import Error
from gdxpds.gdx import GdxFile

logger = logging.getLogger(__name__)

class Translator(object):
    def __init__(self,gdx_file,gams_dir=None,lazy_load=False):
        self.__gdx = GdxFile(gams_dir=gams_dir,lazy_load=lazy_load)
        self.__gdx.read(gdx_file)
        self.__dataframes = None

    def __exit__(self, *args):
        self.__gdx.__exit__(self, *args)

    def __del__(self):
        self.__gdx.__del__()

    @property
    def gams_dir(self):
        return self.gdx.gams_dir

    @gams_dir.setter
    def gams_dir(self, value):
        self.gdx.gams_dir = value

    @property
    def gdx_file(self):
        return self.gdx.filename

    @gdx_file.setter
    def gdx_file(self,value):
        self.__gdx.__del__()
        self.__gdx = GdxFile(gams_dir=self.gdx.gams_dir,lazy_load=self.gdx.lazy_load)
        self.__gdx.read(value)
        self.__dataframes = None

    @property
    def gdx(self):
        return self.__gdx

    @property
    def dataframes(self):
        if self.__dataframes is None:
            self.__dataframes = OrderedDict()
            for symbol in self.__gdx:
                if not symbol.loaded:
                    symbol.load()
                self.__dataframes[symbol.name] = symbol.dataframe.copy()
        return self.__dataframes

    @property
    def symbols(self):
        return [symbol_name for symbol_name in self.gdx]

    def dataframe(self, symbol_name):
        if not symbol_name in self.gdx:
            raise Error("No symbol named '{}' in '{}'.".format(symbol_name, self.gdx_file))
        if not self.gdx[symbol_name].loaded:
            self.gdx[symbol_name].load()
        # This was returning { symbol_name: dataframe }, which seems intuitively off.
        return self.gdx[symbol_name].dataframe.copy()

def to_dataframes(gdx_file,gams_dir=None):
    """
    Primary interface for converting a GAMS GDX file to pandas DataFrames.

    Parameters:
      - gdx_file (string): path to a GDX file
      - gams_dir (string): optional path to GAMS directory

    Returns a dict of Pandas DataFrames, one item for each symbol in the GDX
    file, keyed with the symbol name.
    """
    dfs = Translator(gdx_file,gams_dir=gams_dir).dataframes
    return dfs

def list_symbols(gdx_file,gams_dir=None):
    """
    Returns the list of symbols available in gdx_file.

    Parameters:
      - gdx_file (string): path to a GDX file
      - gams_dir (string): optional path to GAMS directory
    """
    symbols = Translator(gdx_file,gams_dir=gams_dir,lazy_load=True).symbols
    return symbols

def to_dataframe(gdx_file,symbol_name,gams_dir=None,old_interface=True):
    """
    Interface for getting the { symbol_name: pandas.DataFrame } dict for a
    single symbol.

    Parameters:
      - gdx_file (string): path to a GDX file
      - symbol_name (string): symbol whose pandas.DataFrame is being requested
      - gams_dir (string): optional path to GAMS directory

    Returns a dict with a single entry, where the key is symbol_name and the
    value is the corresponding pandas.DataFrame.
    """
    df = Translator(gdx_file,gams_dir=gams_dir,lazy_load=True).dataframe(symbol_name)
    return {symbol_name: df} if old_interface else df
