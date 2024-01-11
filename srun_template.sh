#!/bin/bash
#SBATCH --account=[your HPC allocation]
#SBATCH --time=2-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mail-user=[your email address]
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=250000        # RAM in MB; up to 256000 for normal or 2000000 for bigmem on kestrel
# add >>> #SBATCH --qos=high <<< above for quicker launch at double AU cost
