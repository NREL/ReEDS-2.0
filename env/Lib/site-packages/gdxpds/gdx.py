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

'''
Backend functionality for reading and writing GDX files. 
The GdxFile and GdxSymbol classes are full-featured interfaces
for going between the GDX format and pandas DataFrames,
including translation between GDX and numpy special values. 
'''

from __future__ import absolute_import, print_function
from builtins import super

import atexit
from collections import defaultdict, OrderedDict

try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence

import copy
from ctypes import c_bool
from enum import Enum
import logging
from numbers import Number

# try to import gdx loading utility
HAVE_GDX2PY = False
try:
    # special Windows dll for optimized loading of GAMS parameters
    import gdx2py
    HAVE_GDX2PY = True
except ImportError: pass

# gdxpds needs to be imported before pandas to try to avoid library conflict on 
# Linux that causes a segmentation fault.
from gdxpds import Error
from gdxpds.tools import NeedsGamsDir

import gdxcc
import numpy as np
import pandas as pds

import gdxpds.special as special
# Import some things for backward compatibility
from gdxpds.special import (
    convert_gdx_to_np_svs,
    convert_np_to_gdx_svs,
    gdx_isnan,
    gdx_val_equal,
    NUMPY_SPECIAL_VALUES,
    is_np_eps,
    is_np_sv,
)

logger = logging.getLogger(__name__)


def replace_df_column(df,colname,new_col):
    """
    Utility function that replaces df[colname] with new_col. Special 
    care is taken for the case when df has multiple columns named '*',
    since this causes pandas to crash.

    Parameters
    ----------
    df : pandas.DataFrame
        edited in place by this function
    colname : str
        name of column in df whose data is to be replaced
    new_col : vector, list, pandas.Series
        new column data for df[colname]
    """
    cols = df.columns
    tmpcols = [col if col != '*' else 'aaa' for col in cols ]
    df.columns = tmpcols
    df[colname] = new_col
    df.columns = cols
    return


class GdxError(Error):
    def __init__(self, H, msg):
        """
        Pulls information from gdxcc about the last encountered error and appends
        it to msg.

        Parameters
        ----------
        H : pointer or None
            SWIG binding pointer to a GDX object
        msg : str
            gdxpds error message

        Attributes
        ----------
        msg : str
            msg that is passed in with a gdxErrorStr appended
        """
        if H:
            msg += ". " + gdxcc.gdxErrorStr(H, gdxcc.gdxGetLastError(H))[1] + "."
        super().__init__(msg)


class GdxFile(MutableSequence, NeedsGamsDir):

    def __init__(self,gams_dir=None,lazy_load=True):
        """
        Initializes a GdxFile object by connecting to GAMS and creating a pointer.

        Throws a GdxError if either of those operations fail.
        """
        self.lazy_load = lazy_load
        self._version = None
        self._producer = None
        self._filename = None
        self._symbols = OrderedDict()

        NeedsGamsDir.__init__(self,gams_dir=gams_dir)
        self._H = self._create_gdx_object()
        self.universal_set = GdxSymbol('*',GamsDataType.Set,dims=1,file=None,index=0)
        self.universal_set._file = self

        atexit.register(gdxcc.gdxFree, self.H)
        return

    def cleanup(self):
        gdxcc.gdxFree(self.H)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def __del__(self):
        self.cleanup()

    def clone(self):
        """
        Returns a new GdxFile containing clones of the GdxSymbols in this 
        GdxFile. The clone will not be associated with a filename. The clone's
        GdxSymbols will not have indexes. The clone will be ready to write to 
        a new file.
        """
        result = GdxFile(gams_dir=self.gams_dir,lazy_load=False)
        for symbol in self:
            result.append(symbol.clone())
            result[-1]._file = result
        return result

    @property
    def empty(self):
        """
        Returns True if this GdxFile object contains any symbols.
        """
        return len(self) == 0

    @property
    def H(self):
        """
        GDX object handle
        """
        return self._H

    @property
    def filename(self):
        return self._filename

    @property
    def version(self):
        """
        GDX file version
        """
        return self._version

    @property
    def producer(self):
        """
        What program wrote the GDX file
        """
        return self._producer

    @property
    def num_elements(self):
        return sum([symbol.num_records for symbol in self])

    def read(self,filename):
        """
        Opens gdx file at filename and reads meta-data. If not self.lazy_load, 
        also loads all symbols.

        Throws an Error if not self.empty.

        Throws a GdxError if any calls to gdxcc fail.
        """
        if not self.empty:
            raise Error("GdxFile.read can only be used if the GdxFile is .empty")

        # open the file
        rc = gdxcc.gdxOpenRead(self.H,str(filename))
        if not rc[0]:
            raise GdxError(self.H,f"Could not open {filename!r}")
        self._filename = filename

        # read in meta-data ...
        # ... for the file
        ret, self._version, self._producer = gdxcc.gdxFileVersion(self.H)
        if ret != 1: 
            raise GdxError(self.H,"Could not get file version")
        ret, symbol_count, element_count = gdxcc.gdxSystemInfo(self.H)
        logger.debug("Opening '{}' with {} symbols and {} elements with lazy_load = {}.".format(filename,symbol_count,element_count,self.lazy_load))
        # ... for the symbols
        ret, name, dims, data_type = gdxcc.gdxSymbolInfo(self.H,0)
        if ret != 1:
            raise GdxError(self.H,"Could not get symbol info for the universal set")
        self.universal_set = GdxSymbol(name,data_type,dims=dims,file=self,index=0)
        for i in range(symbol_count):
            index = i + 1
            ret, name, dims, data_type = gdxcc.gdxSymbolInfo(self.H,index)
            if ret != 1:
                raise GdxError(self.H,"Could not get symbol info for symbol {}".format(index))
            self.append(GdxSymbol(name,data_type,dims=dims,file=self,index=index))

        # read all symbols if not lazy_load
        if not self.lazy_load:
            for symbol in self:
                symbol.load()
        return

    def write(self,filename):
        # only write if all symbols loaded
        for symbol in self:
            if not symbol.loaded:
                raise Error("All symbols must be loaded before this file can be written.")

        ret = gdxcc.gdxOpenWrite(self.H,str(filename),"gdxpds")
        if not ret:
            raise GdxError(self.H, f"Could not open {filename!r} for writing. "
                "Consider cloning this file (.clone()) before trying to write.")
        self._filename = filename
        
        # write the universal set
        self.universal_set.write()

        for i, symbol in enumerate(self,start=1):
            try:
                symbol.write(index=i)
            except:
                logger.error("Unable to write {} to {}".format(symbol,filename))
                raise

        gdxcc.gdxClose(self.H)

    def __repr__(self):
        return "GdxFile(self,gams_dir={},lazy_load={})".format(
                   repr(self.gams_dir),
                   repr(self.lazy_load))

    def __str__(self):
        s = "GdxFile containing {} symbols and {} elements.".format(len(self),self.num_elements)
        sep =  " Symbols:\n  "
        for symbol in self:
            s += sep + str(symbol)
            sep = "\n  "
        return s

    def __getitem__(self,key):
        """
        Supports list-like indexing and symbol-based indexing
        """
        return self._symbols[self._name_key(key)]

    def __setitem__(self,key,value):
        self._check_insert_setitem(key, value)
        value._file = self
        if key < len(self):
            self._symbols[self._name_key(key)] = value
            self._fixup_name_keys()
            return
        assert key == len(self)
        self._symbols[value.name] = value
        return

    def __delitem__(self,key):
        del self._symbols[self._name_key(key)]
        return

    def __len__(self):
        return len(self._symbols)

    def insert(self,key,value):
        self._check_insert_setitem(key, value)
        value._file = self
        data = [(symbol.name, symbol) for symbol in self]
        data.insert(key,(value.name,value))
        self._symbols = OrderedDict(data)
        return

    def __contains__(self,key):
        """
        Returns True if __getitem__ works with key.
        """
        try:
            self.__getitem__(key)
            return True
        except:
            return False

    def keys(self):
        return [symbol.name for symbol in self]

    def _name_key(self,key):
        name_key = key
        if isinstance(key,int):
            name_key = list(self._symbols.keys())[key]
        return name_key

    def _check_insert_setitem(self,key,value):
        if not isinstance(value,GdxSymbol):
            raise Error("GdxFiles only contain GdxSymbols. GdxFile was given a {}.".format(type(value)))
        if not isinstance(key,int):
            raise Error("When adding or replacing GdxSymbols in GdxFiles, only integer, not name indices, may be used.")
        if key > len(self):
            raise Error("Invalid key, {}".format(key))
        return

    def _fixup_name_keys(self):
        self._symbols = OrderedDict([(symbol.name, symbol) for cur_key, symbol in self._symbols])
        return        

    def _create_gdx_object(self):
        H = gdxcc.new_gdxHandle_tp()
        rc = gdxcc.gdxCreateD(H,self.gams_dir,gdxcc.GMS_SSSIZE)
        if not rc:
            raise GdxError(H,rc[1])
        return H


class GamsDataType(Enum):
    Set = gdxcc.GMS_DT_SET
    Parameter = gdxcc.GMS_DT_PAR
    Variable = gdxcc.GMS_DT_VAR
    Equation = gdxcc.GMS_DT_EQU
    Alias = gdxcc.GMS_DT_ALIAS


class GamsVariableType(Enum):
    Unknown = gdxcc.GMS_VARTYPE_UNKNOWN
    Binary = gdxcc.GMS_VARTYPE_BINARY
    Integer = gdxcc.GMS_VARTYPE_INTEGER
    Positive = gdxcc.GMS_VARTYPE_POSITIVE
    Negative = gdxcc.GMS_VARTYPE_NEGATIVE
    Free = gdxcc.GMS_VARTYPE_FREE
    SOS1 = gdxcc.GMS_VARTYPE_SOS1
    SOS2 = gdxcc.GMS_VARTYPE_SOS2
    Semicont = gdxcc.GMS_VARTYPE_SEMICONT
    Semiint = gdxcc.GMS_VARTYPE_SEMIINT


class GamsEquationType(Enum):
    Equality = 53 + gdxcc.GMS_EQUTYPE_E
    GreaterThan = 53 + gdxcc.GMS_EQUTYPE_G
    LessThan = 53 + gdxcc.GMS_EQUTYPE_L
    NothingEnforced = 53 + gdxcc.GMS_EQUTYPE_N
    External = 53 + gdxcc.GMS_EQUTYPE_X
    Conic = 53 + gdxcc.GMS_EQUTYPE_C

class GamsValueType(Enum):
    Level = gdxcc.GMS_VAL_LEVEL       # .l
    Marginal = gdxcc.GMS_VAL_MARGINAL # .m
    Lower = gdxcc.GMS_VAL_LOWER       # .lo
    Upper = gdxcc.GMS_VAL_UPPER       # .ub
    Scale = gdxcc.GMS_VAL_SCALE       # .scale

    @classmethod
    def _missing_(cls, value):
        if isinstance(value,str):
            for value_type in cls:
                if value_type.name == value:
                    return value_type
            if value == 'Value':
                return GamsValueType(GamsValueType.Level)
        super()._missing_(value)


GAMS_VALUE_COLS_MAP = defaultdict(lambda : [('Value',GamsValueType.Level.value)])
GAMS_VALUE_COLS_MAP[GamsDataType.Variable] = [(value_type.name, value_type.value) for value_type in GamsValueType]
GAMS_VALUE_COLS_MAP[GamsDataType.Equation] = GAMS_VALUE_COLS_MAP[GamsDataType.Variable]


GAMS_VALUE_DEFAULTS = {
    GamsValueType.Level: 0.0,
    GamsValueType.Marginal: 0.0,
    GamsValueType.Lower: -np.inf,
    GamsValueType.Upper: np.inf,
    GamsValueType.Scale: 1.0
}

GAMS_VARIABLE_DEFAULT_LOWER_UPPER_BOUNDS = {
    GamsVariableType.Unknown: (-np.inf,np.inf),
    GamsVariableType.Binary: (0.0,1.0),
    GamsVariableType.Integer: (0.0,np.inf),
    GamsVariableType.Positive: (0.0,np.inf),
    GamsVariableType.Negative: (-np.inf,0.0),
    GamsVariableType.Free : (-np.inf,np.inf),
    GamsVariableType.SOS1: (0.0,np.inf),
    GamsVariableType.SOS2: (0.0,np.inf),
    GamsVariableType.Semicont: (1.0,np.inf),
    GamsVariableType.Semiint: (1.0,np.inf)
}

class GdxSymbol(object): 
    def __init__(self,name,data_type,dims=0,file=None,index=None,
                 description='',variable_type=None,equation_type=None): 
        self._name = name
        self.description = description
        self._loaded = False
        self._data_type = GamsDataType(data_type)
        self._variable_type = None; self.variable_type = variable_type
        self._equation_type = None; self.equation_type = equation_type
        self._dataframe = None; self._dims = None
        self.dims = dims       
        assert self._dataframe is not None
        self._file = file
        self._index = index        

        if self.file is not None:
            # reading from file
            # get additional meta-data
            ret, records, userinfo, description = gdxcc.gdxSymbolInfoX(self.file.H,self.index)
            if ret != 1:
                raise GdxError(self.file.H,"Unable to get extended symbol information for {}".format(self.name))
            self._num_records = records
            if self.data_type == GamsDataType.Variable:
                self.variable_type = GamsVariableType(userinfo)
            elif self.data_type == GamsDataType.Equation:
                self.equation_type = GamsEquationType(userinfo)
            self.description = description
            if self.index > 0:
                ret, gdx_domain = gdxcc.gdxSymbolGetDomainX(self.file.H,self.index)
                if ret == 0:
                    raise GdxError(self.file.H,"Unable to get domain information for {}".format(self.name))
                assert len(gdx_domain) == len(self.dims), "Dimensional information read in from GDX should be consistent."
                self.dims = gdx_domain
            else:
                # universal set
                assert self.index == 0
                self._loaded = True
            return
        
        # writing new symbol
        self._loaded = True
        return

    def clone(self):
        if not self.loaded:
            raise Error("Symbol {} cannot be cloned because it is not yet loaded.".format(repr(self.name)))

        assert self.loaded
        result = GdxSymbol(self.name,self.data_type,
                           dims=self.dims,
                           description=self.description,
                           variable_type=self.variable_type,
                           equation_type=self.equation_type)
        result.dataframe = copy.deepcopy(self.dataframe)
        assert result.loaded
        return result

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self,value):
        self._name = value
        if self.file is not None:
            self.file._fixup_name_keys()
        return

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self, value):
        if not self.loaded or self.num_records > 0:
            raise Error("Cannot change the data_type of a GdxSymbol that is yet to be read for file or contains records.")
        self._data_type = GamsDataType(value)
        self.variable_type = None
        self.equation_type = None
        self._init_dataframe()
        return

    @property
    def variable_type(self):
        return self._variable_type

    @variable_type.setter
    def variable_type(self,value):
        if self.data_type == GamsDataType.Variable:
            if value is None:
                # default to Free
                self._variable_type = GamsVariableType.Free
            else:
                try:
                    self._variable_type = GamsVariableType(value)
                except:
                    if isinstance(self._variable_type,GamsVariableType):
                        logger.warning("Ignoring invalid GamsVariableType request '{}'.".format(value))
                        return
                    logger.debug("Setting variable_type to {}.".format(GamsVariableType.Free))
                    self._variable_type = GamsVariableType.Free
            return
        assert self.data_type != GamsDataType.Variable
        if value is not None:
            logger.warning("GdxSymbol is not a Variable, so setting variable_type to None")
        self._variable_type = None

    @property
    def equation_type(self):
        return self._equation_type

    @equation_type.setter
    def equation_type(self,value):
        if self.data_type == GamsDataType.Equation:
            if value is None:
                # default to Equality
                self._equation_type = GamsEquationType.Equality
            else:
                try:
                    self._equation_type = GamsEquationType(value)
                except:
                    if isinstance(self._equation_type,GamsEquationType):
                        logger.warning("Ignoring invalid GamsEquationType request '{}'.".format(value))
                        return
                    logger.debug("Setting equation_type to {}.".format(GamsEquationType.Equality))
                    self._equation_type = GamsEquationType.Equality
            return
        assert self.data_type != GamsDataType.Equation
        if value is not None:
            logger.warning("GdxSymbol is not an Equation, so setting equation_type to None")
        self._equation_type = None

    @property
    def value_cols(self):
        """
        Returns list of (name, GamsValueType.value) tuples that describe the 
        value columns in the dataframe, that is, those columns that follow the 
        self.dims.
        """
        return GAMS_VALUE_COLS_MAP[self.data_type]

    @property
    def value_col_names(self):
        return [col_name for col_name, col_ind in self.value_cols]    

    def get_value_col_default(self,value_col_name):
        if not value_col_name in self.value_col_names:
            raise Error(f"{value_col_name} is not one of the value columns for "
                f"this GdxSymbol, which is a {self.data_type}")
        value_col = GamsValueType(value_col_name)
        if self.data_type == GamsDataType.Set:
            assert value_col == GamsValueType.Level
            return c_bool(True)
        if (self.data_type == GamsDataType.Variable) and (
               (value_col == GamsValueType.Lower) or 
               (value_col == GamsValueType.Upper)):
            lb_default, ub_default = GAMS_VARIABLE_DEFAULT_LOWER_UPPER_BOUNDS[self.variable_type]
            if value_col == GamsValueType.Lower:
                return lb_default
            else:
                assert value_col == GamsValueType.Upper
                return ub_default
        return GAMS_VALUE_DEFAULTS[value_col] 

    @property
    def file(self):
        return self._file

    @property
    def index(self):
        return self._index

    @property
    def loaded(self):
        return self._loaded

    @property
    def full_typename(self):
        if self.data_type == GamsDataType.Parameter and self.dims == 0:
            return 'Scalar'
        elif self.data_type == GamsDataType.Variable:
            return self.variable_type.name + " " + self.data_type.name
        return self.data_type.name

    @property
    def dims(self):
        return self._dims

    @dims.setter
    def dims(self, value):
        if (self._dims is not None) and (self.loaded and ((self.num_dims > 0) or (self.num_records > 0))):
            if not isinstance(value,list) or len(value) != self.num_dims:
                raise Error(f"Cannot set dims to {value}, because the number of "
                    "dimensions has already been set to {self.num_dims}.")
        if isinstance(value, int):
            self._dims = ['*'] * value
            self._init_dataframe()
            return
        if not isinstance(value, list):
            raise Error('dims must be an int or a list. Was passed {} of type {}.'.format(value, type(value)))
        for dim in value:
            if not isinstance(dim, str):
                raise Error('Individual dimensions must be denoted by strings. Was passed {} as element of {}.'.format(dim, value))
        assert (self._dims is None) or (self.loaded and (self.num_dims == 0) and (self.num_records == 0)) or (len(value) == self.num_dims)
        self._dims = value
        if self.loaded and self.num_records > 0:
            self._dataframe.columns = self.dims + self.value_col_names
            return
        self._init_dataframe()

    @property
    def num_dims(self):
        return len(self.dims)        

    @property
    def dataframe(self):
        return self._dataframe

    @dataframe.setter
    def dataframe(self, data):
        try:        
            # get data in common format and start dealing with dimensions    
            if isinstance(data, pds.DataFrame):
                df = data.copy()
                has_col_names = True
            else:
                df = pds.DataFrame(data)
                has_col_names = False
                if df.empty:
                    # clarify dimensionality, as needed for loading empty GdxSymbols
                    df = pds.DataFrame(data,columns=self.dims + self.value_cols)
            
            # finish handling dimensions
            n = len(df.columns)
            if (self.num_dims > 0) or (self.num_records > 0):
                if not ((n == self.num_dims) or (n == self.num_dims + len(self.value_cols))):
                    raise Error("Cannot set dataframe to {} because the number ".format(df.head()) + \
                        "of dimensions would change. This symbol has {} ".format(self.num_dims) + \
                        "dimensions, currently represented by {}.".format(self.dims))
                num_dims = self.num_dims
            else:
                # num_dims not explicitly established yet. in this case we must 
                # assume value columns have been provided or dimensionality is 0
                num_dims = max(n - len(self.value_cols),0)
                if (num_dims == 0) and (n < len(self.value_cols)):
                    raise Error("Cannot set dataframe to {} because the number ".format(df.head()) + \
                        "of dimensions cannot be established consistent with {}.".format(self))
                if self.loaded and (num_dims > 0):
                    logger.warning('Inferring {} to have {} dimensions. '.format(self.name,num_dims) + 
                        'Recommended practice is to explicitly set gdxpds.gdx.GdxSymbol dims in the constructor.')

            replace_dims = True
            if has_col_names:
                dim_cols = list(df.columns)[:num_dims]
            elif self.num_dims == num_dims:
                dim_cols = self.dims
                replace_dims = False
            else:
                dim_cols = ['*'] * num_dims            
            for col in dim_cols:
                if not isinstance(col, str):
                    replace_dims = False
                    logger.info("Not using dataframe column names to set dimensions because {} is not a string.".format(col))
                    if num_dims != self.num_dims:
                        self.dims = num_dims
                    break
            if replace_dims:
                self.dims = dim_cols
            # all done establishing dimensions
            assert self.num_dims == num_dims

            # finalize the dataframe
            if n == self.num_dims:
                self._append_default_values(df)
            df.columns = self.dims + self.value_col_names
            self._dataframe = df
        except Exception:
            logger.error("Unable to set dataframe for {} to\n{}\n\nIn process dataframe: {}".format(self,data,self._dataframe))
            raise

        if self.data_type == GamsDataType.Set:
            self._fixup_set_value()
        return

    def _init_dataframe(self):
        self._dataframe = pds.DataFrame([],columns=self.dims + self.value_col_names)
        if self.data_type == GamsDataType.Set:
            colname = self._dataframe.columns[-1]
            replace_df_column(self._dataframe,colname,self._dataframe[colname].astype(c_bool))
        return

    def _append_default_values(self,df):
        assert len(df.columns) == self.num_dims
        logger.debug("Applying default values to create valid dataframe for '{self.name}'.")
        for value_col_name in self.value_col_names:
            df[value_col_name] = self.get_value_col_default(value_col_name)

    def _fixup_set_value(self):
        """
        Tricky to get boolean set values to come through right. 
        isinstance(True,Number) == True and float(True) = 1, but 
        isinstance(c_bool(True),Number) == False, and this keeps the default 
        value of 0.0.

        Could just test for isinstance(,bool), but this fix has the added 
        advantage of speaking the GDX bindings data type language, and also 
        fills in any missing values, so users no longer need to actually specify
        self.dataframe['Value'] = True.
        """
        assert self.data_type == GamsDataType.Set

        colname = self._dataframe.columns[-1]
        assert colname == self.value_col_names[0], f"Unexpected final column {colname!r} in Set dataframe"
        if self._dataframe[colname].isnull().values.any():
            logger.warning(f"Filling null values in {self} with True. To be "
                "filled:\n{self._dataframe[self._dataframe[colname].isnull()]}")
            replace_df_column(self._dataframe, colname, self._dataframe[colname].fillna(value=True))
        replace_df_column(self._dataframe,colname,self._dataframe[colname].apply(lambda x: c_bool(x)))
        return

    @property
    def num_records(self):
        if self.loaded:
            return len(self.dataframe.index)
        return self._num_records

    def __repr__(self):
        return "GdxSymbol({},{},{},file={},index={},description={},variable_type={},equation_type={})".format(
                   repr(self.name),
                   repr(self.data_type),
                   repr(self.dims),
                   repr(self.file),
                   repr(self.index),
                   repr(self.description),
                   repr(self.variable_type),
                   repr(self.equation_type))

    def __str__(self):
        s = self.name
        s += ", " + self.description    
        s += ", " + self.full_typename    
        s += ", {} records".format(self.num_records)
        s += ", {} dims {}".format(self.num_dims, self.dims)
        s += ", loaded" if self.loaded else ", not loaded"
        return s

    def load(self):
        if self.loaded:
            logger.info("Nothing to do. Symbol already loaded.")
            return
        if not self.file:
            raise Error("Cannot load {} because there is no file pointer".format(repr(self)))
        if not self.index:
            raise Error("Cannot load {} because there is no symbol index".format(repr(self)))

        if self.data_type == GamsDataType.Parameter and HAVE_GDX2PY:
            self.dataframe = gdx2py.par2list(self.file.filename,self.name) 
            self._loaded = True
            return

        data = []
        _ret, records = gdxcc.gdxDataReadStrStart(self.file.H,self.index)
        for _i in range(records):
            _ret, elements, values, _afdim = gdxcc.gdxDataReadStr(self.file.H)
            # make sure we pick value columns up correctly
            data.append(elements + [values[col_ind] for col_name, col_ind in self.value_cols])
            if self.data_type == GamsDataType.Set:
                data[-1][-1] = True
                # gdxdict called gdxGetElemText here, but I do not currently see value in doing that
        self.dataframe = data
        if not self.data_type == GamsDataType.Set:
            self.dataframe = special.convert_gdx_to_np_svs(self.dataframe, self.num_dims)
        self._loaded = True
        return

    def unload(self):
        self.dataframe = None
        self._loaded = False

    def write(self,index=None): 
        if not self.loaded:
            raise Error("Cannot write unloaded symbol {}.".format(repr(self.name)))

        if self.data_type == GamsDataType.Set:
            self._fixup_set_value()

        if index is not None:
            self._index = index

        if self.index == 0:
            # universal set
            gdxcc.gdxUELRegisterRawStart(self.file.H)
            gdxcc.gdxUELRegisterRaw(self.file.H,self.name)
            gdxcc.gdxUELRegisterDone(self.file.H)
            return

        # write the data
        userinfo = 0
        if self.variable_type is not None:
            userinfo = self.variable_type.value
        elif self.equation_type is not None:
            userinfo = self.equation_type.value
        if not gdxcc.gdxDataWriteStrStart(self.file.H,
                                          self.name,
                                          self.description,
                                          self.num_dims,
                                          self.data_type.value,
                                          userinfo):
            raise GdxError(self.file.H,"Could not start writing data for symbol {}".format(repr(self.name)))
        # set domain information
        if self.num_dims > 0:
            if self.index:
                if not gdxcc.gdxSymbolSetDomainX(self.file.H,self.index,self.dims):
                    raise GdxError(self.file.H,"Could not set domain information for {}. Domains are {}".format(repr(self.name),repr(self.dims)))
            else:
                logger.info("Not writing domain information because symbol index is unknown.")
        values = gdxcc.doubleArray(gdxcc.GMS_VAL_MAX)
        # make sure index is clean -- needed for merging in convert_np_to_gdx_svs
        self.dataframe = self.dataframe.reset_index(drop=True)
        for row in special.convert_np_to_gdx_svs(self.dataframe, self.num_dims).itertuples(index=False, name=None):
            dims = [str(x) for x in row[:self.num_dims]]
            vals = row[self.num_dims:]
            for _col_name, col_ind in self.value_cols:
                values[col_ind] = float(0.0)
                try:
                    if isinstance(vals[col_ind],Number):
                        values[col_ind] = float(vals[col_ind])
                except: 
                    raise Error("Unable to set element {} from {}.".format(col_ind,vals))
            gdxcc.gdxDataWriteStr(self.file.H,dims,values)
        gdxcc.gdxDataWriteDone(self.file.H)
        return


# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def append_set(gdx_file, set_name, df, cols=None, dim_names=None, 
        description=None):
    """
    Convenience function that appends set_name to gdx_file as a 
    :class:`GamsDataType.Set <GamsDataType>` :class:`GdxSymbol` using data in 
    df.

    Parameters
    ----------
    gdx_file : :class:`GdxFile`
        file to which new :class:`GdxSymbol` is to be added
    set_name : str
        name of the :class:`GdxSymbol` to be added
    df : pandas.DataFrame
        dataframe or data that can be used to construct a dataframe containing 
        the set data. assumes that all columns define dimensions (there is no 
        'Value' column)
    cols : None or list of str
        if not None, these are the columns in df to be used for the set 
        definition
    dim_names : None or list of str
        if provided, the columns of a copy of df (or of df[cols]) will be renamed
        to these names, because the dimension names are taken from the final 
        dataframe, these will also be the dimension names
    description : None or str
        passed directly to :class:`GdxSymbol`
    """
    # ensure df is DataFrame and not Series
    logger.debug(f"Defining set {set_name!r} based on:\n{df!r}")
    tmp = pds.DataFrame(df)
    # select down to data we actually want
    if cols is not None:
        tmp = tmp[cols]
    if dim_names is not None:
        if tmp.empty:
            tmp = pds.DataFrame([], columns = dim_names)
        else:
            tmp.columns = dim_names
    # define the symbol
    gdx_file.append(GdxSymbol(set_name, GamsDataType.Set, 
        dims = list(tmp.columns), description = description))
    # define the data for the symbol
    gdx_file[-1].dataframe = tmp
    # debug description of what happened
    logger.debug(f"Added set {set_name!r} to {gdx_file!r} using processed data:\n{tmp!r}")
    return


def append_parameter(gdx_file, param_name, df, cols=None, dim_names=None, 
        description=None):
    """
    Convenience function that appends param_name to gdx_file as a 
    :class:`GamsDataType.Parameter <GamsDataType>` :class:`GdxSymbol` using 
    data in df.

    Parameters
    ----------
    gdx_file : :class:`GdxFile`
        file to which new :class:`GdxSymbol` is to be added
    param_name : str
        name of the :class:`GdxSymbol` to be added
    df : pandas.DataFrame
        dataframe or data that can be used to construct a dataframe containing 
        the parameter data. assumes that the last selected column is the 'Value' 
        column
    cols : None or list of str
        if not None, these are the columns in df to be used for the parameter
        definition
    dim_names : None or list of str
        if provided, the columns of a copy of df (or of df[cols]) will be renamed
        to these names + ['Value']. because the dimension names are taken from 
        the final dataframe, these will also be the dimension names
    description : None or str
        passed directly to :class:`GdxSymbol`
    """
    # pre-process the data
    logger.debug(f"Defining parameter {param_name!r} based on:\n{df!r}")
    tmp = pds.DataFrame(df)
    if cols is not None:
        tmp = tmp[cols]
    if dim_names is not None:
        if tmp.empty:
            tmp = pds.DataFrame([], columns = dim_names + ['Value'])
        else:
            tmp.columns = dim_names + ['Value']
    # define the symbol
    gdx_file.append(GdxSymbol(param_name, GamsDataType.Parameter,
        dims = list(tmp.columns)[:-1], description = description))
    # define the data for the symbol
    gdx_file[-1].dataframe = tmp
    # debug descripton of what happened
    logger.debug(f"Added parameter {param_name!r} to {gdx_file!r} using processed data:\n{tmp!r}")
    return
