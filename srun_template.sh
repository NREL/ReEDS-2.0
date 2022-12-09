#!/bin/bash
#SBATCH --account=[your HPC allocation]
#SBATCH --time=2-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mail-user=[your email address]
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=90000    # RAM in MB; 90000 for normal or 184000 for big-mem

# add >>> #SBATCH --qos=high <<< above for quicker launch at double AU cost

#load your default settings
. $HOME/.bashrc
