#!/bin/bash
#SBATCH --account=2035study
#SBATCH --time=1:00:00
#SBATCH --partition=debug
#SBATCH --ntasks-per-node=3
#SBATCH --mail-user=bsergi@nrel.gov
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=250000    # RAM in MB
