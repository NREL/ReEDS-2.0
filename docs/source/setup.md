# Getting Started 
The ReEDS model source code is available at no cost from the National Renewable Energy Laboratory. The ReEDS model can be downloaded or cloned from [https://github.com/NREL/ReEDS-2.0](https://github.com/NREL/ReEDS-2.0).

New users may also wish to start with some ReEDS training videos which are available on the NREL YouTube channel at [https://youtu.be/aGj3Jnspk9M?si=iqCRNn5MbGZc8ZIO](https://youtu.be/aGj3Jnspk9M?si=iqCRNn5MbGZc8ZIO).

## Computer Setup for Microsoft Windows 10
The setup and execustion of the ReEDS model can be accomplished using a command-line interpreter application and launching a command line interface (referred to as a "terminal window" in this documentat). For example, initiating the Windows Command Prompt application, i.e., cmd.exe, will launch a terminal window [Figure 1](#figure-1-setup). (Note: If you have issues using command prompt, try using anaconda prompt or a git bash window)

```{figure} ../../images/cmd-prompt.png
:name: figure-1-setup

Figure 1: Screenshot of a Windows Command Prompt terminal window
```

**SUGGESTON:** use a command line emulator such as ConEmu ([https://conemu.github.io/](https://conemu.github.io/)) for a more user-friendly terminal. The screenshots of terminal windows shown in this document are taken using ConEmu.

**IMPORTANT:** Users should exercise Administrative Privileges when installing software. For example, right click on the installer executable for one of the required software (e.g., Anaconda3-2019.07-Windows-x86\_64.exe) and click on "Run as administrator" ([Figure 2](#figure-2-setup)). Alternatively, right click on the executable for the command line interface (e.g., Command Prompt) and click on "Run as administrator" ([Figure 3](#figure-3-setup)). Then run the required software installer executables from the command line.

```{figure} ../../images/run-as-admin.png
:name: figure-2-setup

Figure 2: Screenshot of running an installer executable using "Run as administrator"
```

```{figure} ../../images/run-as-admin-2.png
:name: figure-3-setup

Figure 3: Screenshot of running "Command Prompt" with "Run as administrator"
```

### Python Configuration

Install Anaconda: [https://www.anaconda.com/download](https://www.anaconda.com/download).

**IMPORTANT** : Be sure to download the Windows version of the installer.

Add Python to the "path" environment variable

1. In the Windows start menu, search for "environment variables" and click "Edit the system environment variables" ([Figure 4](#figure-4-setup)). This will open the "System Properties" window ([Figure 5](#figure-5-setup)).

```{figure} ../../images/search-env-var.png
:name: figure-4-setup

Figure 4. Screenshot of a search for "environment variables" in the Windows start menu
```

```{figure} ../../images/sys-prop-win.png
:name: figure-5-setup

Figure 5. Screenshot of the "System Properties" window.
```


2. Click the "Environment Variables" button on the bottom right of the window ([Figure 5](#figure-5-setup)). This will open the "Environment Variables" window ([Figure 6](#figure-6-setup)).


```{figure} ../../images/env-var-win.png
:name: figure-6-setup

Figure 6. Edit the Path environment variable
```


3. Highlight the Path variable and click "Edit" ([Figure 6](#figure-7-setup)). This will open the "Edit environment variable" window ([Figure 7](#figure-7-setup)).

```{figure} ../../images/edit-env-var-win.png
:name: figure-7-setup

Figure 7. Append the Path environment
```


4. Click "New" ([Figure 7](#figure-7-setup)) and add the directory locations for \Anaconda\ and \Anaconda\Scripts to the environment path.

**IMPORTANT** : Test the Python installation from the command line by typing "python" (no quotes) in the terminal window. The Python program should initiate ([Figure 8](#figure-8-setup)).

```{figure} ../../images/py-test.png
:name: figure-8-setup

Figure 8. Screenshot of a test of Python in the terminal window
```

It is highly recommended to run ReEDS using the conda environment provided in the repository. This environment (named `reeds2`) is specified by the `environment.yml` and can be built with the following command:

```
conda env create -f environment.yml
```

You can verify that the environment was successfully created using the following (you should see `reeds2` in the list):

```
conda env list
```


### GAMS Configuration

Install GAMS: [https://www.gams.com/download/](https://www.gams.com/download/). NREL uses GAMS versions 45.2.0 and 34.3. Older versions might also work. A valid GAMS license must be installed. Please refer to the [Required Software](#Software) section above for more information.

Add GAMS to the "path" environment variable. Follow the same instructions as for adding Python to the path in the [Python Configuration](#ConfigPy) section above. Append the environment path with the directory location for the _gams.exe_ application (e.g., C:\GAMS\win64\34).


**IMPORTANT** : Test the GAMS installation from the command line by typing "gams" (no quotes) in the terminal window. The GAMS program should initiate (Figure 9).

```{figure} ../../images/gams-test.png
:name: figure-9-setup

Figure 9. Screenshot of a test of GAMS from the terminal window
```


### ReEDS Repository Setup
The ReEDS source code is hosted on GitHub: [https://github.com/NREL/ReEDS-2.0](https://github.com/NREL/ReEDS-2.0)

1. From the Git command line run the following command to enable large file storage.
```
git lfs install
```
2. Clone the ReEDS-2.0 repository on your desktop. Alternatively, download a ZIP from GitHub ([Figure 10](#figure-10-setup)).

```{figure} ../../images/github-download.png
:name: figure-10-setup

Figure 10. Screenshot of GitHub links to clone the ReEDS repository or download ZIP of the ReEDS files
```



## Computer Setup for MacOS
### Python Configuration
Download the latest version of Anaconda: [https://www.anaconda.com/download](https://www.anaconda.com/download)

During Installation, select to install Anaconda for your machine only.

```{figure} ../../images/anaconda-install-mac.png
:name: figure-11-setup

Figure 11: Image of Anaconda Install Mac
```

To have the installer automatically add anaconda to PATH, ensure that you've selected the box to "Add conda initialization to the shell"

```{figure} ../../images/anaconda-custom-install-mac.png
:name: figure-12-setup

Figure 12: Image of Anaconda Install Mac - Customize Installation Type
```

**To validate Python was installed properly** execute the following command from a new terminal (without quotes): "python"

Python should initiate, looking similar to [Figure 8](#figure-8-setup).

It is highly recommended to run ReEDS using the conda environment provided in the repository. This environment (named `reeds2`) is specified by the `environment.yml` and can be built with the following command - make sure you navigate to the ReEDS repository from terminal first: 

```
conda env create -f environment.yml
```

You can verify that the environment was successfully created using the following (you should see `reeds2` in the list):

```
conda env list
```


### GAMS Configuration 
Install GAMS: [https://www.gams.com/download/](https://www.gams.com/download/). A valid GAMS license must be installed. Please refer to the [Required Software](#Software) section above for more information.

**IMPORTANT**: When installing on Mac, on the 'Installlation Type' page, click 'customize' and ensure the box to 'Add GAMS to PATH' is checked.

```{figure} ../../images/gams-install-mac.png
:name: figure-13-setup

Figure 13: Image of GAMS Install Mac
```

**To validate GAMS was installed properly** execute the following command from a new terminal (without quotes): "gams"

GAMS should initiate, you should see something similar to [Figure 9](#figure-9-setup).



### ReEDS Repository Setup
The ReEDS source code is hosted on GitHub: [https://github.com/NREL/ReEDS-2.0](https://github.com/NREL/ReEDS-2.0)

1. From the Git command line run the following command to enable large file storage.
```
git lfs install
```
2. Clone the ReEDS-2.0 repository on your desktop and use the repository with GitHub Desktop. Alternatively, download a ZIP from GitHub ([Figure 10](#figure-10-setup)).


## Executing the Model
A ReEDS case (also referred to as a "run", "scenario" or "instance") is executed through a python-based case batching program called `runbatch.py` after the repository was setup. The user can execute a single case or a batch of cases using this program.

### Understanding the cases.csv file
ReEDS Model Switches are set in the cases.csv file and need to be specified by the user. The default case configuration file is called "cases.csv".

Within "cases.csv", the data in column A are the model "switches". Column B contains a brief description of each switch. Column C contains the choices available for the given switch (please not, this is not available for all switches). Column D contains the default value for the switch. Finally, the case configuration (or set of switches that define a case) is in column E. 

Within column E, the case name is specified in row 1. The value for each switch is specified beginning in row 2. If a switch value is left blank, the default value from column D is used. 

```{figure} ../../images/cases-csv.png
:name: figure-14-setup

Figure 14. Screenshot of cases.csv
```

There are additional cases_*.csv files that can also be used to run different ReEDS scenarios. The two most commonly used are:
   * cases_standardscenarios.csv: contains all the scenarios that were used for Standard Scenarios
   * cases_test.csv: contains a group of "test" cases that are smaller than the default case in "cases.csv"

The user may also create custom case configuration files by using the suffix in the file name (e.g., "cases_smalltests.csv"). It should follow the same column formatting as cases.csv, but does not need to include all available switches.

### Calling runbatch.py to run ReEDS
1. Navigate to the ReEDS directory from a new command prompt or terminal.
2. Activate the `reeds2` conda environment: `conda activate reeds2`
3. Call runbatch.py: `python runbatch.py`
   * It should look similar to [Figure 15](#figure-15-setup)
4. Provide responses to the suite of prompts in the command line. For more information about the prompts, see the [Prompts for user input during runbatch.py section](#prompts-for-user-input-during-runbatchpy).
5. Once all responses have been received, the batching program will execute the case(s) specified in the case configuration file (e.g., "cases.csv").
   * Please note, if you're running ReEDS on Windows, a separate terminal window will be launched for each case.

For each case that is run, a new subfolder will be created under the "runs/" subdirectory of ReEDS. If you run the default case found in "cases.csv", you can expect to find the outputs from the run at "/ReEDS-2.0/runs/{batch prefix}_Ref/outputs".

```{figure} ../../images/exe-runbatch.png
:name: figure-15-setup

Figure 15. Screenshot of initiating "runbatch.py" from the command line
```


### Prompts for user input during runbatch.py 
**Batch Prefix [string]** - Defines the prefix for files and directories that will be created for the batch of cases to be executed (as listed in a case configuration file, e.g., "cases.csv")
   * All files and directories related to a case will be named "{batch prefix}_{case}". For example, if *batch prefix = "test"* and *case = "Ref"*, then all files and directories related to this case will be named *test_Ref*. 
   * **Important:** A batch prefix cannot start with a number given incompatibility with GAMS.
   * Entering the value of "0" (zero, no quotes) will assign the current date and time for the batch prefix in the form of *v{YYYMMDD}_{HHMM}*. 
   * If you re-use a (batch prefix, case) pair, a new prompt will appear asking if you want to overwrite the existing output directories.
    
**Case Suffix [string]** - Indicates which case configuration file (in the form "cases_{case suffix}.csv") is ingested into "runbatch.py" for processing.
   * Entering an empty value(i.e., pressing "Enter/Return") will cause the default case configuration file "cases.csv" to be used

**Number of Simultaneous Runs [integer]** - Indicated how many cases should be run simultaneously.
   * "runbatch.py" uses a queue to execute multiple cases
   * If there are 4 cases and the *Number of Simultaneous Runs = 1*, then "runbatch.py" will execute the cases one at a time
   * However, if there are 4 cases and the *Number of Simultaneous Runs = 2*, then "runbatch.py" will start 2 cases simultaneously
      * As each case finishes, it will start a new one until all cases have been run
   * **WARNING! Be mindful about the amount of CPU and RAM usage needed for each case**
