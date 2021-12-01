#!/bin/bash
#SBATCH --account=[your HPC allocation]
#SBATCH --time=2-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mail-user=[your email address]
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=172000      # RAM in MB

#load your default settings
. $HOME/.bashrc
