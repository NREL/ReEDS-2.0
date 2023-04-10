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

import argparse
import logging
import os

import gdxpds

logger = logging.getLogger(__name__)


def convert_gdx_to_csv(in_gdx, out_dir, gams_dir=None):
    # check inputs
    if not os.path.exists(os.path.dirname(out_dir)):
        raise RuntimeError("Parent directory of output directory '{}' does not exist.".format(out_dir))
        
    # convert to pandas.DataFrames
    dataframes = gdxpds.to_dataframes(in_gdx, gams_dir)

    # write to files
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    
    for symbol_name, df in dataframes.items():
        csv_path = os.path.join(out_dir, symbol_name + ".csv")
        if os.path.exists(csv_path):
            logger.info("Overwriting '{}'".format(csv_path))
        df.to_csv(csv_path,
                  na_rep='NaN',
                  index=False)

if __name__ == "__main__":

    # define and execute the command line interface
    parser = argparse.ArgumentParser(description='''Reads a gdx file into
        pandas dataframes, and then writes them out as csv files.''')
    parser.add_argument('-i', '--in_gdx', help='''Input gdx file to be read
                        and exported as one csv per symbol.''')
    parser.add_argument('-o', '--out_dir', default='./gdx_data/',
                        help='''Directory to which csvs are to be written.''')
    parser.add_argument('-g', '--gams_dir', help='''Path to GAMS installation
                        directory.''', default = None)
        
    args = parser.parse_args()
    
    convert_gdx_to_csv(args.in_gdx, os.path.realpath(args.out_dir), args.gams_dir)
