# Set up nodal environment for run
. $HOME/.bashrc 
module purge 
source /nopt/nrel/apps/env.sh 
module load anaconda3 
conda activate reeds2 

# run script
python collect_land_use.py