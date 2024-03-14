#!/bin/bash
#SBATCH --account=setosa
#SBATCH --time=04:00:00
###SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mail-user=bsergi@nrel.gov
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=250000
#SBATCH --job-name=collect_land_use
#SBATCH --output=slurm-%j.out

#load your default settings
. $HOME/.bashrc

sh run_collect_land_use.sh