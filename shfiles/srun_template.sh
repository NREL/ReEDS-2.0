#!/bin/bash
#SBATCH --account=capexindia
#SBATCH --time=16:00:00  #TIME FOR RUN
#SBATCH --nodes=1
#SBATCH --mail-user=sam.koebrich@NREL.gov
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=90000      # RAM in MB

#load your default settings
. $HOME/.bashrc

#load conda and gams
module purge
module load conda
module load gams
source deactivate
source activate reeds #name of reeds conda env
