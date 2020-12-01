# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 16:30:30 2020

@author: smachen
"""
import argparse
import pandas as pd
import os


def pkl_to_csv(file,path,outdir=False, remove=False):
       
    #check for file extensions
    if file[-3:] != 'pkl': 
        infile = file + '.pkl'
        outfile = file + '.csv.gz'
    else:
        infile = file
        outfile = file[:-4] + '.csv.gz'
    
    #read in .pkl file
    inpath  = os.path.join(path,infile)        
    df = pd.read_pickle(inpath)
    
    #write out .csv.gz file
    if outdir:
        if not os.path.exists(outdir): os.mkdir(outdir)
        df.to_csv(os.path.join(outdir,outfile))
    else:
        df.to_csv(os.path.join(path,outfile))
    
    #remove original pickle file if requested    
    if remove:
        os.remove(inpath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pklFile',
                        help='pickle file name',
                        type=str)
    parser.add_argument('indir',
                        type=str,
                        help='directory containing pickle file')
    parser.add_argument('-o',
                        '--output',
                        type=str,
                        help='optional output directory path')
    parser.add_argument('-r',
                        '--remove',
                        action='store_true',
                        help='remove original pickle file')
    
    args = parser.parse_args()
    
    deleteFile=False
    if args.remove: deleteFile=True
    
    if args.output:
        pkl_to_csv(file = args.pklFile, path = args.indir, outdir=args.output, remove = deleteFile)
    else:
        pkl_to_csv(file = args.pklFile, path= args.indir, remove = deleteFile)
    
    
    