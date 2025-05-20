#!/bin/bash
#SBATCH --account=southasia
#SBATCH --time=30:00:00  #TIME FOR RUN
#SBATCH --nodes=1
#SBATCH --mail-user=prateek.joshi@NREL.gov
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=80000    # RAM in MB
#SBATCH --qos=high

#load conda and gams
module purge
module load anaconda3
module load gams
conda deactivate
conda activate /kfs2/projects/southasia/.conda-envs/reeds-india #name of reeds conda env
