#%% Imports
import pandas as pd
import os
import site
import json
from glob import glob
import subprocess
### Local imports
reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


#%%### Functions
def check_slurm(forcelocal=False):
    """Check whether to submit slurm jobs (if on HPC) or run locally"""
    hpc = True if (int(os.environ.get('REEDS_USE_SLURM',0))) else False
    hpc = False if forcelocal else hpc
    return hpc


def submit_job(
    case,
    year=0,
    iteration=None,
    samples=0,
    repo=False,
    overwrite=False,
    write_flow=False,
    write_surplus=False,
    write_energy=False,
    write_shortfall_samples=False,
    write_availability_samples=False,
    switch_mods={},
):
    """
    """
    ### Make the run file
    jobname = f'PRAS-{os.path.basename(case)}-{samples}'
    ## Get the SLURM boilerplate
    commands_header, commands_sbatch, commands_other = [], [], []
    with open(os.path.join(reeds_path,'srun_template.sh'), 'r') as f:
        for line in f:
            if line.strip().startswith('#!'):
                commands_header.append(line.strip())
            elif line.strip().startswith('#SBATCH'):
                commands_sbatch.append(line.strip())
            else:
                commands_other.append(line.strip())
    ## Add the command for this run
    slurm = (
        commands_header
        + commands_sbatch
        + [f"#SBATCH --job-name={jobname}"]
        + [f"#SBATCH --output={os.path.join(case, 'slurm-%j.out')}"]
        + commands_other + ['']
        + [
            f"python {os.path.join(reeds_path,'postprocessing','run_reeds2pras.py')}"
            + f" {case}"
            + f" -y {year}"
            + ('' if iteration is None else f' -i {iteration}')
            + f" -s {samples}"
            + " --local"
            + (' --repo' if repo else '')
            + (' --overwrite' if overwrite else '')
            + (' --flow' if write_flow else '')
            + (' --surplus' if write_surplus else '')
            + (' --energy' if write_energy else '')
            + (' --shortfall' if write_shortfall_samples else '')
            + (' --availability' if write_availability_samples else '')
            + (f' --switch_mods={json.dumps(switch_mods)}' if len(switch_mods) else '')
        ]
    )
    ### Write the SLURM command
    callfile = os.path.join(case, 'call_pras.sh')
    with open(callfile, 'w+') as f:
        for line in slurm:
            f.writelines(line+'\n')
    ### Submit the job
    batchcom = f'sbatch {callfile}'
    subprocess.Popen(batchcom.split())
    quit()


#%% Main function
def main(
    case,
    year=0,
    iteration=None,
    samples=0,
    repo=False,
    overwrite=False,
    write_flow=False,
    write_surplus=False,
    write_energy=False,
    write_shortfall_samples=False,
    write_availability_samples=False,
    switch_mods={},
):
    """
    Run prep_data, ReEDS2PRAS, and PRAS as necessary.
    If running PRAS, append the number of samples to the filename.
    """
    ### Import Augur scripts
    if repo:
        site.addsitedir(reeds_path)
    else:
        site.addsitedir(case)
    import Augur
    import reeds
    import ReEDS_Augur.prep_data as prep_data

    ### Get the switches, overwriting values as necessary
    sw = reeds.io.get_switches(case)
    sw['reeds_path'] = reeds_path
    sw['pras_samples'] = samples

    ### Get the solve years
    years = pd.read_csv(
        os.path.join(case, 'inputs_case', 'modeledyears.csv')
    ).columns.astype(int).tolist()

    ### Parse the year input
    t = year if (year in years) else years[-1]
    sw['t'] = t

    if iteration is None:
        ### Get the largest iteration and run on that system
        iteration = int(
            os.path.splitext(
                sorted(glob(os.path.join(case,'lstfiles',f'*{t}i*.lst')))[-1]
            )[0]
            .split(f'{t}i')[-1]
        )

    print(f'Running PRAS for {t}i{iteration}')

    ### Check if prep_data.py outputs exist; if not, run it
    augur_data = os.path.join(case,'ReEDS_Augur','augur_data')
    files_expected = [
        f'cap_converter_{t}.csv',
        f'energy_cap_{t}.csv',
        f'max_cap_{t}.csv',
        f'tran_cap_{t}.csv',
        f'pras_load_{t}.h5',
        f'pras_vre_gen_{t}.h5',
    ]
    if (
        any([not os.path.isfile(os.path.join(augur_data,f)) for f in files_expected])
        or overwrite
    ):
        augur_csv, augur_h5 = prep_data.main(t, case)

    ### Run ReEDS2PRAS
    Augur.run_pras(
        case,
        t,
        iteration=iteration,
        recordtime=False,
        repo=repo,
        overwrite=overwrite,
        include_samples=True,
        write_flow=write_flow,
        write_surplus=write_surplus,
        write_energy=write_energy,
        write_shortfall_samples=write_shortfall_samples,
        write_availability_samples=write_availability_samples,
        **switch_mods,
    )


#%%### Procedure
if __name__ == '__main__':
    #%% Argument inputs
    import argparse
    description = """Run prep_data, ReEDS2PRAS, and PRAS as necessary.
    Example usage on the HPC:
    `case=/projects/reedsweto/github/ReEDS-2.0/runs/v20230524_ntpH0_Pacific`
    `for s in 100 1000; do python postprocessing/run_reeds2pras.py $case -s $s -r; done`
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('case', type=str,
                        help='path to ReEDS run folder')
    parser.add_argument('--year', '-y', type=int, default=0,
                        help='year to run')
    parser.add_argument('--iteration', '-i', type=str, default='',
                        help='iteration to run (if not provided, runs last iteration)')
    parser.add_argument('--samples', '-s', type=int, default=0,
                        help='PRAS samples to run')
    parser.add_argument('--repo', '-r', action='store_true',
                        help=('Import Augur scripts from local repo '
                              '(instead of from the case being rerun)'))
    parser.add_argument('--local', '-l', action='store_true',
                        help='Run locally (not as SLURM job)')
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help="Overwrite .pras file if it already exists")
    parser.add_argument('--flow', '-f', action='store_true',
                        help="Write hourly flow from PRAS")
    parser.add_argument('--surplus', '-u', action='store_true',
                        help="Write hourly surplus from PRAS")
    parser.add_argument('--energy', '-e', action='store_true',
                        help="Write hourly storage energy from PRAS")
    parser.add_argument('--shortfall', '-d', action='store_true',
                        help="Write hourly shortfall by sample from PRAS")
    parser.add_argument('--availability', '-a', action='store_true',
                        help="Write hourly unit availability by sample from PRAS")
    parser.add_argument('--switch_mods', '-m', type=json.loads, default=json.dumps({}),
                        help=('Dictionary-formated string of switch arguments for '
                        'Augur.run_pras(). Use single quotes outside the dictionary and '
                        'double quotes for keys, as in:\n'
                        '`-s \'{"pras_seed":0}\'`'))

    args = parser.parse_args()
    case = args.case
    year = args.year
    iteration = args.iteration
    if not len(iteration):
        iteration = None
    samples = args.samples
    repo = args.repo
    local = args.local
    overwrite = args.overwrite
    write_flow = args.flow
    write_surplus = args.surplus
    write_energy = args.energy
    write_shortfall_samples = args.shortfall
    write_availability_samples = args.availability
    switch_mods = args.switch_mods

    # #%% Inputs for testing
    # case = '/Users/pbrown/github2/ReEDS-2.0/runs/v20230605_ntpM1_Pacific'
    # year = 2026
    # iteration = None
    # samples = 0
    # repo = True
    # local = False
    # overwrite = False
    # write_flow = False
    # write_surplus = False
    # write_energy = False
    # write_shortfall_samples = False
    # write_availability_samples = False
    # switch_mods = {}

    #%% Determine whether to submit SLURM job
    hpc = check_slurm(forcelocal=local)

    ### Run it
    if hpc:
        submit_job(
            case=case,
            year=year,
            iteration=iteration,
            samples=samples,
            repo=repo,
            overwrite=overwrite,
            write_flow=write_flow,
            write_surplus=write_surplus,
            write_energy=write_energy,
            write_shortfall_samples=write_shortfall_samples,
            write_availability_samples=write_availability_samples,
            switch_mods=switch_mods,
        )
    else:
        main(
            case=case,
            year=year,
            iteration=iteration,
            samples=samples,
            repo=repo,
            overwrite=overwrite,
            write_flow=write_flow,
            write_surplus=write_surplus,
            write_energy=write_energy,
            write_shortfall_samples=write_shortfall_samples,
            write_availability_samples=write_availability_samples,
            switch_mods=switch_mods,
        )
