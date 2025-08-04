#!/bin/bash
#SBATCH --account=[your HPC allocation]
#SBATCH --time=2-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mail-user=[your email address]
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=246000        # RAM in MB; up to 246000 for normal or 2000000 for bigmem on kestrel
# add >>> #SBATCH --qos=high <<< above for quicker launch at double AU cost
#load your default settings

# Set up nodal environment for run
. $HOME/.bashrc
module purge
source /nopt/nrel/apps/env.sh
module load anaconda3
module use /nopt/nrel/apps/software/gams/modulefiles
module load gams
conda activate reeds2
export R_LIBS_USER="$HOME/rlib"

## Uncomment one of these based on which you would like to run, change this to your project directory
# python /kfs2/projects/decarbsagen/ahamilto/EER_load_ingest/ReEDS-2.0/hourlize/eer_to_reeds/eer_splice/eer_splice.py
# python /kfs2/projects/decarbsagen/ahamilto/EER_load_ingest/ReEDS-2.0/hourlize/eer_to_reeds/eer_to_reeds.py
# python /kfs2/projects/decarbsagen/ahamilto/EER_load_ingest/ReEDS-2.0/hourlize/make_historic_load.py
