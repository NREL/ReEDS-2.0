#!/bin/bash
#SBATCH --account=southasia
#SBATCH --time=24:00:00  #TIME FOR RUN
#SBATCH --nodes=1
#SBATCH --mail-user=ilya.chernyakhovskiy@NREL.gov
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=80000    # RAM in MB
#SBATCH --qos=high

#load conda and gams
module purge
module use /nopt/nrel/apps/modules/centos74/modulefiles/
module load conda
module load gams
source deactivate
source activate /lustre/eaglefs/projects/southasia/.conda-envs/reeds #name of reeds conda env
