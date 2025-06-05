import argparse
import os
import sys
from warnings import warn
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


def check_error(case, cutoff=0.01, errors='print', printcase=False):
    e = reeds.io.read_output(case, 'error_check').set_index('*').Value['z']
    errortext = (
        f"Your system cost error is {e}, which is too big!"
        + (f" ← {os.path.basename(case)}" if printcase else '')
    )
    if e >= cutoff:
        if errors == 'print':
            print('ERROR: ' + errortext)
        elif errors == 'warn':
            warn(errortext)
        else:
            raise ValueError(errortext)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Check the system cost error",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        'cases', type=str, nargs='+',
        help='Path(s) to ReEDS case(s)',
    )
    parser.add_argument(
        '--cutoff', '-c', type=float, default=0.01,
        help='Error level above which to raise an exception',
    )
    args = parser.parse_args()
    for case in args.cases:
        check_error(case, cutoff=args.cutoff, printcase=(len(args.cases) > 1))
