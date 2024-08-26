# Model Information
## Overview 
ReEDS is a mathematical programming model of the electric power sector. Given a set of input assumptions, ReEDS models the evolution and operation of generation, storage, transmission, and production technologies. 

The model consists of two separate but interrelated modules:
  * Supply module -  this module solves a linear program for the cost-minimizing levels of power sector investment
  * Operation and storage (VRE) module - this module calculates key parameters for assessing the 
  value of VRE generators and storage

The full, detailed documentation of the ReEDS model can be found in the latest version of the published documentation: [Regional Energy Deployment System (ReEDS) Model Documentation: Version 2020](https://www.nrel.gov/docs/fy21osti/78195.pdf).

Detailed documentation of ReEDS 2.0 input files are available [here](./sources.md)


## Model Switches
```{eval-rst}
.. include:: ../../input_processing/README.md
    :parser: myst_parser.sphinx_
```

## Troubleshooting
This section provides guidance on identifying and resolving common issues encountered during model execution. By checking the locations and files listed below, users can better pinpoint errors. 

### Key Areas for Error Checking
* GAMS Log File
  * Path: "/runs/{batch_prefix}_{case}/gamslog.txt"
  * Purpose: contains the log outputs for all execution statements from the case batch file
  * What to look for: 
    * 'ERROR': will provide more information into the specific file or line in the source code that failed or has an error
    * 'LP status' and 'Status': can provide more insight into the model run
    * 'Cur_year': can help you determine which year the model run failed in

* GAMS Listing Files 
  * Path: "/runs//{batch_prefix}_{case}/lstfiles/" 
  * Purpose: contains the listing files for GAMS executions
  * What to look for: 
    * '1_inputs.lst': errors will be preceded by '****'
    * '{batch_prefix}_{case}_{year}i0.lst': there should be one file for each year of the model run
    * 'Augur_errors_{year}': this file will appear in the event that there is an augur-related issue

* GAMS Workfiles
  * Path: "/runs/{batch_prefix}_{case}/g00files/"
  * Purpose: stores a snapshot of all the model information available to GAMS at that point in the case execution. More information about GAMS work files can be found here: [https://www.gams.com/latest/docs/UG_SaveRestart.html](https://www.gams.com/latest/docs/UG_SaveRestart.html)
  * What to look for: 
    * '{batch_prefix}_{case}_{last year run}i0.g00': should exist for the last year run

* Output Directory
  * Path: "/runs/{batch_prefix}_{case}/outputs/"
  * Purpose: the outputs folder contains the generated output files from the model run
  * What to look for: 
    * '*.csv' files: there should be many '.csv' files in this folder
      * these files should contain data, an error message "GDX file not found" indicates an issue with the reporting script at the end of the model
    * 'reeds-report/' and 'reeds-report-reduced/': if these folders are not present, it can indicate a problem with the post-processing scripts

* Augur Data 
  * Path: "/runs/{batch_prefix}_{case}/ReEDS_Augur/augur_data/"
  * What to look for: 
    * 'ReEDS_Augur_{year}.gdx': there should be a file for each year of the model run =
    * 'reeds_data_{year}.gdx': there should be a file for each year of the model run

* Case Inputs
  * Path: "/runs/{batch_prefix}_{case}/inputs_case/"
  * What to look for: 
    * '*.csv' files: there should be many '.csv' files in this folder, if there isn't, it could indicate a problem with the pre-processing scripts
    * 'inputs.gdx': if this doesn't exist, it could indicate a problem with the pre-processing scripts

### Re-running a Failed ReEDS Case
To re-run a failed case from the year it failed: 
1. Comment out all the execution statements that completed successfully in "/runs/{batch_prefix}_{case}/call_{batch_prefix}_{case}.bat" (or *.sh file if on Mac)
   * Shortcut for commenting multiple lines: Ctrl + '/' (Command + '/' if on Mac)

2. Re-run "/runs/{batch_prefix}_{case}/call_{batch_prefix}_{case}.bat"

Additionally, 'restart_runs.py' is a helper script that can be used to restart any failed runs. For more information on how to use this script, see the section on [Helper Scripts and Tools](postprocessing_tools.md#helper-scripts-and-tools). 