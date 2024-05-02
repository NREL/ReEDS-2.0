#!/bin/bash
#SBATCH --account=[your HPC allocation]
#SBATCH --time=4:00:00
#SBATCH --ntasks-per-node=1
#SBATCH --mail-user=[your email]
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem=248000    # RAM in MB
