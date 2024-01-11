import argparse
import os

def check_subdirectories(parentDirectory, testResultFile="test_run_results.txt"):
    """ 
    Checks all subdirectories in a provided parent directory for the expected outputs from a run.
    Looks through the gamslog.txt file for errors.
    Writes the results to the test_run_results.txt file
    """
    with open(testResultFile, 'w') as resultsFile:
        # check to ensure parent directory exists
        if not os.path.exists(parentDirectory):
            resultsFile.write(f"Error: provided directory '{parentDirectory}' does not exist.")
            print("Error: provided directory ", parentDirectory, " does not exist")
            return
    
        # get list of subdirectories in testruns folder
        runs = [d for d in os.listdir(parentDirectory) if os.path.isdir(os.path.join(parentDirectory, d))]

        # check outputs folder of each run
        for r in runs:
            resultsFile.write("==========================================================\n")
            resultsFile.write(f"Checking run '{r}'\n")
            
            outputsFolder = os.path.join(parentDirectory, r, "outputs")
            countOutputFiles = len([f for f in os.listdir(outputsFolder) if os.path.isfile(os.path.join(outputsFolder, f))])
            resultsFile.write(f"Number of files in outputs folder: '{countOutputFiles}'\n")

            # Verify reeds-report folder exists and is not empty
            reedsReportFolder = os.path.join(parentDirectory, outputsFolder, "reeds-report")
            if os.path.exists(reedsReportFolder):
                if len(os.listdir(reedsReportFolder)) > 0:
                    resultsFile.write("reeds-report folder exists and is not empty\n")
            else:
                resultsFile.write("ERROR: reeds-report folder does not exist or is empty\n")

            # parse gamslog.txt for errors
            resultsFile.write("-- gamslog errors -- \n")
            gamslogFile = os.path.join(parentDirectory, r, "gamslog.txt")
            with open(gamslogFile, 'r') as logFile:
                content = logFile.readlines()
                for line in content:
                    if 'ERROR' in line:
                        resultsFile.write(line)
                    if 'tests/' in line:
                        resultsFile.write(line)
           
    print(f"Results can be found in '{resultsFile.name}'")



## Parse inputs
parser = argparse.ArgumentParser(description='Location of test run results')
parser.add_argument('testruns', type=str,
                    help='path to ReEDS folder that contains all test runs')

args = parser.parse_args()
testruns = args.testruns

check_subdirectories(testruns)
