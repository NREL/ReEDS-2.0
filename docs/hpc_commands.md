# Instructions for first time setup and running ReEDS-India on the HPC

## Step 1. SSH into an HPC login node
`ssh -m hmac-sha2-512 [hpc-username]@kestrel.hpc.nrel.gov`

*Type your password and hit enter/return*

## Step 2. Add a GAMS license (for first time setup or if GAMS license is renewed)
> navigate to the appropriate directory
`cd ../../home/[your username]` 
> create folders to store the GAMS license
`mkdir .local/share/GAMS`
> Navigate to teh GAMS folder that was just created
`cd .local/share/GAMS`
> Upload the GAMS license file into this folder and name it as "gamslice.txt"

## Step 3. Setup a screen (for first time setup or if HPC restarts)
`screen -S reeds`

> other useful commands for screens
> - list available screens: `screen -ls`
> - restart a screen: `screen -r [screen name]`
> - detach from a screen: `ctrl+a d`

### Navigate to southasia project folder (for first time setup or if HPC restarts)
`cd ../../projects/southasia` *default dir is your hpc user folder*

*Now you can either create your own folder within projects/southasia or use an existing repo.* <br />
*For this example, we will create a repo called reeds_india_api in projects/southasia.*

### Clone the reeds_india_api repo (for first time setup only)
`git clone git@github.com:NREL/reeds_india_api.git`

### Setup environment (for first time setup or if HPC restarts)
`cd reeds_india_api` <br />
`module purge` <br />
`module load anaconda3` <br />
`module load gams` <br />
`conda deactivate` <br />
`conda activate /kfs2/projects/southasia/.conda-envs/reeds-india`

### Update srun_template.sh (for first time setup only)
*Edit shfiles/srun_template.sh* <br />
- Update `--mail-user=` to your NREL email
- Update `--time=` with your best estimate for maximum time needed. *NOTE: A lower time request will have a shorter wait in the queue for a compute node*
> For command line editing use `vim shfiles/srun_template.sh` or `nano shfiles/srun_template.sh` <br />
> Other options for editing files: 
> - Use an SSH-enabled IDE like VSCode
> - Use a remote SSH file explorer like SSH
> - Mount the remote SSH directory to your machine using SFTP Drive


## Step 4. Compile inputs and generate batch files
*Type:*

`python runmodel.py`
> *Answer the prompts:*
> - Run Name: *Choose a short but discriptive name. No spaces or special characters."*
> - Selected scenarios: *Select scenarios by listing associated numbers, e.g., 0,1,2,3.*
> - Do you want to iteritavely calculate capacity value and curtailment?: *typically yes (1), hit enter/return (1 is default)*
> - Compile inputs and model equations?: *yes (1), hit enter/return (1 is default)*
> - Run model?: **NO. DO NOT RUN ON A LOGIN NODE. TYPE 0 AND HIT ENTER/RETURN.**
> - Generate shell scripts to run on NREL HPC?: *type 1 and hit enter*

## Step 5. Update batch file and submit run(s)
*At this point you have everything needed to submit a run into the HPC queue. Before you do, double-check options in the .sh batch file for your run.* 
- *Batch files fo runs are saved in folder:* `shfiles`  
- *Ensure `--time=` is sufficient for each run.*
- *Use `--qos=high` to get higher in the HPC queue. This option triggers a higher "cost" in allocation hours*

*Submit a run:* <br />
`sbatch shfiles/[runname_scenario].sh` <br />
*Repeat this command for each scenario you want to run* <br />

> *NOTE: The process described in Steps 3 and 4 will create a unique batch script for each run-scenario combination. This will run each scenario simultaneously using separate compute node requests. To run scenarios sequentially with a single compute node request, copy the last line from the each .sh file to the end of a single .sh file and run command `sbatch` on the single .sh file. Don't forget to update the `--time=` option accordingly.*


# Other useful commands
*Check jobs in the queue and estimated start time* <br />
`squeue --start -u [username]`

*Request an interactive debug node* <br />
`srun --time=30 --account=southasia --partition=debug --ntasks=36 --pty $SHELL`

*Request an interactive "short" node (less than 4 hours)* <br />
`srun --time=30 --account=southasia --partition=short --qos=high --pty $SHELL`







