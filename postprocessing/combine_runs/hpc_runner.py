import argparse
import combine_runs as cr

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(
        description='Runner to submit HPC jobs set up by combine_runs.py',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('scen', type=str, help='scenario to run')
    parser.add_argument('reeds_path', type=str, help='path to reeds directory')
    parser.add_argument('output_path', type=str, help='path to output folder for combined runs')
    args = parser.parse_args()
    cr.run_combine_case(args.scen, args.reeds_path, args.output_path)