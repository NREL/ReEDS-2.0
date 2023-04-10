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
import os

# gdxpds needs to be imported before pandas to try to avoid library conflict on 
# Linux that causes a segmentation fault.
import gdxpds

import pandas as pds

def convert_csv_to_gdx(input_files, output_file, gams_dir=None):
    # check input files
    for ifile in input_files:
        if not os.path.splitext(ifile)[1] in ['.csv','.txt']:
            msg = "Input file '{}' is of unexpected type. Expected .csv or .txt.".format(ifile)
            raise RuntimeError(msg)
        if not os.path.isfile(ifile):
            raise RuntimeError("'{}' is not a file.".format(ifile))
   
    # convert input_files into one list of csvs
    ifiles = []
    for ifile in input_files:
        if os.path.splitext(ifile)[1] == '.csv':
            ifiles.append(ifile)
        else:
            # must be .txt
            f = open(ifile, 'r')
            for line in f:
                if not line == '':
                    if os.path.splitext(line.strip())[1] == '.csv':
                        ifiles.append(line.strip())
                    else:
                        print("Skipping '{}' found in '{}'.".format(line,ifile))
            f.close()
    if len(ifiles) == 0:
        raise RuntimeError("Nothing to convert.")
        
    # convert list of csvs to map of dataframes
    dataframes = {}
    for ifile in ifiles:
        dataframes[os.path.splitext(os.path.basename(ifile))[0]] = \
            pds.read_csv(ifile,index_col=None)
            
    gdxpds.to_gdx(dataframes, output_file, gams_dir)
    

if __name__ == "__main__":

    # define and execute the command line interface
    parser = argparse.ArgumentParser(description='''Accepts one or more input
        csv files as input. Writes each csv as a separate symbol to an output
        gdx.''')
    parser.add_argument('-i', '--input', nargs='+', help='''List one or more
        .csv or .txt files. The latter are assumed to be a line-delimited list
        of .csv files.''')
    parser.add_argument('-o', '--output', default='export.gdx', help='''Path
        to the output gdx file. Will be overwritten if it already exists.''')
    parser.add_argument('-g', '--gams_dir', help='''Path to GAMS installation
        directory.''', default = None)
        
    args = parser.parse_args()
    
    convert_csv_to_gdx(args.input, args.output, args.gams_dir)
