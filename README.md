# ReEDS-2.0
This repository contains the code for ReEDS 2.0. 

---
## Software Requirements and Setup

The following software are required to run ReEDS
  * GAMS version 27.4 or later
  * R version 3.4.4 or 3.5.1
  * Python version 2.7.14
  * GitHub and Git

**GAMS setup**
  * Download and install GAMS version 24.7 or later
  * add the path to GAMS.exe to the PATH environment variable on your user account (e.g., C:\GAMS\win64\24.7\)
  * verify that “gams” is a recognized command: type “gams” in the command line and press enter

**R setup**
1. Download and install R version 3.4.4 or 3.5.1
2. Add the path to Rscript.exe to the PATH environment variable on your user account (e.g., C:\Program Files\R\R-3.4.4\bin\)
3. Add/modify the R_LIBS_USER environment variable; set the value equal to the directory where R packages should be stored for your user account (e.g., C:\Users\keurek\Documents\R\R-3.4.4)
4. Verify that “rscript” is a recognized command: type “rscript” in the command line and press enter

**Python setup**
1. Download and install Python version 2.7.14
2. Python should be a part of the PATH environment variable by default
3. Verify that “python” is a recognized command: type “python” in the command line and press enter

**Repository setup**:

Clone into ReEDS\ReEDS-2.0: 

```git clone git@github.nrel.gov:ReEDS/ReEDS-2.0.git [folder name]```

**Additional setup notes**:
1. Max and Jonathan suggest using ConEmu for command line execution
2. To append the PATH environment variable with, for example, “C:\GAMS\win64\24.7\” do the following:
   
   Option 1: From the command line: PATH=%PATH%;C:\GAMS\win64\24.7\
   Option 2: From the control panel:
    * Start -> Control Panel -> User Account -> Change my environment variables
    * Click on "PATH"
    * Click on the "Edit..." button
    * Append the path variable with “C:\GAMS\win64\24.7\”
3. We will be eliminating R from ReEDS in the near future
4. We will be transitioning to using Python version 3 in the near future

---
## File Structure and Execution

Each section below describes the key files necessary to run scenarios in ReEDS 2.0. 
1. How to run this script: description of how to run the script
2. Summary: brief overview of what the file does
3. Inputs: inputs for the script
4. Outputs: outputs from the script
5. Operations: details of what is happening within the script
6. Function: specific functions used in the script

### g00prep.bat

**How to run this script**: navigate to the ReEDS 2.0 directory. Type “g00prep.bat” in the command line

**Summary**: batch file that prepares data for use in GAMS. Max suggests running g00prep.bat first before running runbatch.py to make sure the data preparation works without issue. g00prep.bat is executed when you call runbatch.py.

**Inputs**:
  * Cases.csv – scenario names and
  * You will be asked to answer a set of questions in the command line

**Outputs**: GAMS restart file with all model data and the model formulation

**Operations**:
1. Create file directories

2. Call b_writedata.gms
  * **Inputs**:
    * number of new vintage bins (numclass)
    * number of historical vintage bins (numhintage)
    * GSwprm0Region (The name in g00prep.bat appears to be inconsistent with the name in B_wirtedata.gms – CHECK THIS OUT)
    * heritage reeds input.gdx file name (scen) 
    * historical vintage bin calculation method
    * minimum deviation for binning (mindev)
  * **Outputs**: various input data files (.gdx, .csv, etc.)
  * **Operations**:
    * Setup R packages (akin to setup.R for heritage ReEDS)
      * this uses R_LIBS_USER
      * R issues can occur here; e.g.,rcpp may not be installed correctly, so you may need to install rcpp directly from Rstudio
    * Prepare input data
      * input files from ReEDS include:
      * inputs.gdx (export of all data at the end of A_readinputs.gms)
      * ventyx.csv
      * capacity factors
      * supply curves
    * Process data from ReEDS heritage .gdx file; scenario = name of the ReEDS heritage .gdx file
    * Manipulate the data into the format necessary for ReEDS 2.0
    * **note**: data preparation accounts for odd years
    
3. Call b_inputs.gms
  * **note**: this takes at least 10 minutes
  * **Inputs**: various input data files (.gdx, .csv, etc.)
  * **Outputs**: input.gdx; g00 file (restart point)  
  * **Operations**:
    * Declare and define sets and parameters
    * Load input data into GAMS 
    
4. Call Call b_extrainputs.gms

The data defined here will overwrite the data that were loaded previously
  
5. Call b_inputsdemand.gms
  * **note**: this file is not currently called because the demand side is not typically used and it takes a long time for this file to run. If you want this file to be run by g00prep.bat, you need to adjust the line that calls g00prep.bat in runbatch.py)
  * **Inputs**: g00 file (restart point)
  * **Operations**: Load demand module input data into GAMS
  * **Outputs**: g00 file (restart point)

6.	Call C_supplymodel.gms
  * **Inputs**: g00 file (restart point)
  * **Operations**:
    * Kill parameters will large dimensions that are no longer needed
    * Declare and define model switches (which equations to include or exclude)
    * Declare and define variables and equations
  * **Outputs**: g00 file (restart point)
    
7. Call C_objective_supply
  * **Inputs**: g00 file (restart point)
  * **Operations**: Declare and define the objective function
  * **Outputs**: g00 file (restart point) 

### runbatch.py

**How to run this script**: navigate to the ReEDS 2.0 directory. Type “python runbatch.py” in the command line. You will be prompted to answer some question. After you have answered the questions, the script will proceed.

**Summary**: Scenario batching script. This is what you will use to run your scenarios

**Inputs**:
1. cases.csv- this is where you specify your scenarios that you wish to run 
  * scenario list and options
  * the model switch options here will override the model switch options from c_supplymodel.gms
2. \inputs\userinput\modeledyears.csv: modeled years
3. \inputs\userinput\ict.csv: valid vintage classes for each technology
4. The batch script will request information from the batch script (user inputs)
  * Run Name: batch scenario group name – this will be the name of the directory in the “runs” folder where this set of batched scenarios will appear
  * Number of threads: number of scenarios to run in parallel
  * If you are running an intertemporal solve (specified in cases.csv) you will be asked the following questions:
    * Number of cv/curt iterations for an intertemporal solve: 7 iterations is generally good per Max, but 1 iteration is sufficient for testing purposes.
    * Restart from a previous attempt? which iteration? – If you are running a new scenario you can answer “no” to this question; if you answer “yes”, you will need to provide the iteration number (i.e., iterations between the supply model and REFLOW) that failed last time
  * Create new g00 files? yes or no. if yes, then run g00prep_NoDemand.bat; else skip. if you have already run g00prep.bat and have not changed the model or inputs, then you do not need to rerun this and you may answer “no”

**Outputs**: a suite of .csv files for each scenario executed hat can be used for bokeh for visualization

**Operations**:
1. Load scenario list and user-defined options (“cases.csv”)
2. Create a run directory for each case
3. If desired, call g00prep_NoDemand.bat for each case (Prepare data; load data into GAMS; define model equations)
4. Execute solve for all scenarios
  * call gams d_solveprep.gms
    * define subsets and indexed sets (e.g., rfeas, tmodel)
  * call gams d_solveoneyear.gms (sequential) or d_solveallyears.gms (intertemporal)
    * for the sequential case: call d_solveoneyear.gms; d_callreflow.gms; step forward; repeat
    * for intertemporal case: call d_solveallyears.gms; d_callreflow.gms; repeat n times
  * call gams e_report.gms
  * call gams e_report_dump.gms

**Functions**:
1. Parallel Processing 
2. Solve model
3. 8760

---
## Manually Restarting a Case that Fails

1.	Navigate to the case directory in the “runs” directory: .\runs\[scenario batch name] _ [case_name]
2.	Open the batch file for the failed case: “[scenario batch name] _ [case_name].bat” 
3.	Comment out the commands you want to ignore by adding "rem" at the beginning of the command 
4.	Save the .bat file
5.	Execute the .bat file.


---
## Model Outputs

Scenario data are stored in “run” within a directory that you specify during runbatch.py

Bokehpivot has been modified to work with ReEDS 2.0. Launch the bokehpivot server and select “ReEDS 2.0” prior to specifying the data directory path
