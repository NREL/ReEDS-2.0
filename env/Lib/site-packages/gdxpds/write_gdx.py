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
from numbers import Number

# gdxpds needs to be imported before pandas to try to avoid library conflict on 
# Linux that causes a segmentation fault.
from gdxpds.tools import Error
from gdxpds.gdx import GdxFile, GdxSymbol, GAMS_VALUE_COLS_MAP, GamsDataType

import pandas as pds

logger = logging.getLogger(__name__)

class Translator(object):
    def __init__(self,dataframes,gams_dir=None):
        self.dataframes = dataframes
        self.__gams_dir=None

    def __exit__(self, *args):
        if self.__gdx is not None:
            self.__gdx.__exit__(self, *args)

    def __del__(self):
        if self.__gdx is not None:
            self.__gdx.__del__()

    @property
    def dataframes(self):
        return self.__dataframes

    @dataframes.setter
    def dataframes(self,value):
        err_msg = "Expecting map of name, pandas.DataFrame pairs."
        try:
            for symbol_name, df in value.items():
                if not isinstance(symbol_name, str): raise Error(err_msg)
                if not isinstance(df, pds.DataFrame): raise Error(err_msg)
        except AttributeError: raise Error(err_msg)
        self.__dataframes = value
        self.__gdx = None

    @property
    def gams_dir(self):
        return self.__gams_dir

    @gams_dir.setter
    def gams_dir(self, value):
        self.__gams_dir = value

    @property
    def gdx(self):
        if self.__gdx is None:
            self.__gdx = GdxFile(gams_dir=self.__gams_dir)
            for symbol_name, df in self.dataframes.items():
                self.__add_symbol_to_gdx(symbol_name, df)
        return self.__gdx

    def save_gdx(self,path,gams_dir=None):
        if gams_dir is not None:
            self.__gams_dir=gams_dir
        self.gdx.write(path)

    def __add_symbol_to_gdx(self, symbol_name, df):
        data_type, num_dims = self.__infer_data_type(symbol_name,df)
        logger.info("Inferred data type of {} to be {}.".format(symbol_name,data_type.name))

        self.__gdx.append(GdxSymbol(symbol_name,data_type,dims=num_dims))
        self.__gdx[symbol_name].dataframe = df
        return

    def __infer_data_type(self,symbol_name,df):
        """
        Returns
        -------
        (gdxpds.GamsDataType, int)
            symbol type and number of dimensions implied by df
        """
        # See if structure implies that symbol_name may be a Variable or an Equation
        # If so, break tie based on naming convention--Variables start with upper case, 
        # equations start with lower case
        var_or_eqn = False        
        df_col_names = df.columns
        var_eqn_col_names = [col_name for col_name, col_ind in GAMS_VALUE_COLS_MAP[GamsDataType.Variable]]
        if len(df_col_names) >= len(var_eqn_col_names):
            # might be variable or equation
            var_or_eqn = True
            trunc_df_col_names = df_col_names[len(df_col_names) - len(var_eqn_col_names):]
            for i, df_col in enumerate(trunc_df_col_names):
                if df_col and (df_col.lower() != var_eqn_col_names[i].lower()):
                    var_or_eqn = False
                    break
            if var_or_eqn:
                num_dims = len(df_col_names) - len(var_eqn_col_names)
                if symbol_name[0].upper() == symbol_name[0]:
                    return GamsDataType.Variable, num_dims
                else:
                    return GamsDataType.Equation, num_dims

        # Parameter or set
        num_dims = len(df_col_names) - 1
        if len(df.index) > 0:
            if isinstance(df.loc[df.index[0],df.columns[-1]],Number):
                return GamsDataType.Parameter, num_dims
        return GamsDataType.Set, num_dims


def to_gdx(dataframes,path=None,gams_dir=None):
    """
    Parameters:
      - dataframes (map of pandas.DataFrame): symbol name to pandas.DataFrame
        dict to be compiled into a single gdx file. Each DataFrame is assumed to
        represent a single set or parameter. The last column must be the parameter's
        value, or the set's listing of True/False, and must be labeled as (case
        insensitive) 'value'.
      - path (optional string): if provided, the gdx file will be written
        to this path

    Returns a gdxdict.gdxdict, which is defined in [py-gdx](https://github.com/geoffleyland/py-gdx).
    """
    translator = Translator(dataframes,gams_dir=gams_dir)
    if path is not None:
        translator.save_gdx(path)
    return translator.gdx

