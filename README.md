# ReEDS 2.0

![Image of NREL Logo](/images/nrel-logo.png)

## Welcome to the Regional Energy Deployment System (ReEDS) Model!

This GitHub repository contains the source code for NREL&#39;s ReEDS model. The ReEDS model source code is available at no cost from the National Renewable Energy Laboratory. The ReEDS model can be downloaded or cloned from [https://github.com/NREL/ReEDS-2.0](https://github.com/NREL/ReEDS-2.0). 

A ReEDS training video (based on the 2020 version of ReEDS) is available on the NREL YouTube channel at https://youtu.be/aGj3Jnspk9M?si=iqCRNn5MbGZc8ZIO.

## Contents

* [Introduction](#Introduction)
* [Required Software](#Software)
* [Computer Setup for Microsoft Windows 10](#Setup)
  * [ReEDS Repository Configuration](#ConfigRepo)
  * [Python Configuration](#ConfigPy)
  * [GAMS Configuration](#ConfigGAMS)
* [Computer Setup for MacOS](#Setup-Mac)
  * [GAMS Configuration](#ConfigGAMS-Mac)
  * [Python Configuration](#ConfigPy-Mac)
  * [ReEDS Repository Configuration](#ConfigRepo-Mac)
* [Executing the Model](#Execution)
  * [Prompts for user input during &quot;runbatch.py&quot;](#Prompts)
  * [Runbatch.py Execution Protocol](#RunBatch)
  * [Case-specific Batch File Execution Protocol](#CaseBatch)
* [Documentation](#Documentation)
* [Model Architecture](#Architecture)
  * [Modules](#Modules)
  * [Tracking Capital Stock](#Stock)
* [Frequently Asked Questions](#FAQ)
  * [How much are the GAMS licensing fees?](#Fees)
  * [Is there a trial version of the GAMS license so I can test ReEDS?](#Trial)
  * [What computer hardware is necessary to run ReEDS?](#Hardware)
  * [Can I configure a ReEDS case to run as an isolated interconnect?](#Interconnect)
* [Contact Us](#Contact)
* [Appendix](#Appendix)
  * [ReEDS Model Switches](#Switches)
  * [Tips for reducing solve time](#SolveTime)

<a name="Introduction"></a>
# Introduction ([https://www.nrel.gov/analysis/reeds/](https://www.nrel.gov/analysis/reeds/)) 

The Regional Energy Deployment System (ReEDS) is a capacity planning and dispatch model for the North American electricity system.

As NREL&#39;s flagship long-term power sector model, ReEDS has served as the primary analytic tool for many studies ([https://www.nrel.gov/analysis/reeds/publications.html](https://www.nrel.gov/analysis/reeds/publications.html)) of important energy sector research questions, including clean energy policy, renewable grid integration, technology innovation, and forward-looking issues of the generation and transmission infrastructure. Data from the most recent base case and a suite of Standard Scenarios are provided.

ReEDS uses high spatial resolution and high-fidelity modeling. Though it covers a broad geographic and technological scope, ReEDS is designed to reflect the regional attributes of energy production and consumption. Unique among long-term capacity expansion models, ReEDS possesses advanced algorithms and data to represent the cost and value of variable renewable energy; the full suite of other major generation technologies, including fossil and nuclear; and transmission and storage expansion options. Used in combination with other NREL tools, data, and expertise, ReEDS can provide objective and comprehensive electricity system futures.

<a name="Software"></a>
# Required Software

The ReEDS model is written primarily in GAMS with auxiliary modules written in Python. R is used for the demand module, which is not active by default, and therefore need not be installed unless you plan on working with that module. At present, NREL uses the following software versions: GAMS 30.3; Python 3.6.5; R 3.4.4. Other versions of these software may be compatible with ReEDS, but NREL has not tested other versions at this time.

GAMS is a mathematical programming software from the GAMS Development Corporation. &quot;The use of GAMS beyond the limits of the free demo system requires the presence of a valid GAMS license file.&quot; [[1](https://www.gams.com/latest/docs/UG_License.html)] The ReEDS model requires the GAMS Base Module and a linear programming (LP) solver (e.g., CPLEX). The LP solver should be connected to GAMS with either a GAMS/Solver license or a GAMS/Solver-Link license. &quot;A GAMS/Solver connects the GAMS Base module to a particular solver and includes a license for this solver to be used through GAMS. It is not necessary to install additional software. A GAMS/Solver-Link connects the GAMS Base Module to a particular solver, but does not include a license for the solver. It may be necessary to install additional software before the solver can be used.&quot; [[2](https://www.gams.com/products/buy-gams/)]

NREL subscribes to the GAMS/CPLEX license for the LP solver, but open-source solvers and free, internet-based services are also available. 
* The [_COIN-OR Optimization Suite_](https://www.coin-or.org/downloading/) includes open-source solvers that can be linked with GAMS through the GAMS Base Module. NREL has tested the use of the COIN-OR Linear Programming (CLP) solver for ReEDS. More information about using CLP for ReEDS can be found [_here_](https://www.nrel.gov/docs/fy21osti/77907.pdf). 
* The [_NEOS Server_](https://neos-server.org/neos/) is a free, internet-based service for solving numerical optimization problems. Links with NEOS can be made through [_KESTREL_](https://www.gams.com/latest/docs/S_KESTREL.html) which is included in GAMS Base Module. In its current form, ReEDS cannot be solved using NEOS due to the 16 MB limit on submissions to the server. However, modifications _could_ be made to ReEDS to _potentially_ reduce the data below to the required submission size. Note that some solvers available on the NEOS server are limited to non-commercial use. 

Python is &quot;an object-oriented programming language, comparable to Perl, Ruby, Scheme, or Java.&quot; [[3](https://wiki.python.org/moin/BeginnersGuide/Overview)] &quot; Python is developed under an OSI-approved open source license, making it freely usable and distributable, even for commercial use. Python&#39;s license is administered by the Python Software Foundation.&quot; [[4](https://www.python.org/about/)]. NREL uses Conda to build the python environment necessary for ReEDS. Conda is a &quot;package, dependency and environment management for any language.&quot; [[5](https://docs.conda.io/en/latest/)]

Git is a version-control tool used to manage code repositories. Included in Git is a unix style command line emulator called Git Bash, which is used by ReEDS to perform some initial setup tasks.

<a name="Setup"></a>
# Computer Setup for Microsoft Windows 10

The setup and execution of the ReEDS model can be accomplished using a command-line interpreter application and launching a command line interface (referred to as a &quot;terminal window&quot; in this document). For example, initiating the Windows Command Prompt application, i.e., cmd.exe, will launch a terminal window ([Figure 1](#Fig1)). (Note: If you have issues using command prompt, try using anaconda prompt or a git bash window)

<a name="Fig1"></a>
![Image of Command Prompt](/images/cmd-prompt.png)

*Figure 1. Screenshot of a Windows Command Prompt terminal window.*

**SUGGESTON:** use a command line emulator such as ConEmu ([https://conemu.github.io/](https://conemu.github.io/)) for a more user-friendly terminal. The screenshots of terminal windows shown in this document are taken using ConEmu.

**IMPORTANT:** Users should exercise Administrative Privileges when installing software. For example, right click on the installer executable for one of the required software (e.g., Anaconda3-2019.07-Windows-x86\_64.exe) and click on &quot;Run as administrator&quot; ([Figure 2](#Fig2)). Alternatively, right click on the executable for the command line interface (e.g., Command Prompt) and click on &quot;Run as administrator&quot; ([Figure 3](#Fig3)). Then run the required software installer executables from the command line.

<a name="Fig2"></a> 
![Image of Run as Admin](/images/run-as-admin.png)

*Figure 2. Screenshot of running an installer executable using &quot;Run as administrator&quot;.*

<a name="Fig3"></a>
![Image of Run as Admin 2](/images/run-as-admin-2.png)
 
*Figure 3. Screenshot of running &quot;Command Prompt&quot; with &quot;Run as administrator&quot;.*

<a name="ConfigRepo"></a>



## ReEDS Repository Setup
The ReEDS source code is hosted on GitHub: https://github.com/NREL/ReEDS-2.0

1. From the Git command line run the following command to enable large file storage.
```
git lfs install
```
2. Clone the ReEDS-2.0 repository on your desktop. Alternatively, download a ZIP from GitHub ([Figure 4](#Fig4)).

<a name="Fig4"></a>
![Image of GitHub Download](/images/github-download.png)
 
*Figure 4. Screenshot of GitHub links to clone the ReEDS repository or download ZIP of the ReEDS files.*

<a name="ConfigPy"></a>
### Python Configuration

Install Anaconda: [https://www.anaconda.com/download](https://www.anaconda.com/download).

**IMPORTANT** : Be sure to download the Windows version of the installer.

Add Python to the &quot;path&quot; environment variable

1. In the Windows start menu, search for &quot;environment variables&quot; and click &quot;Edit the system environment variables&quot; ([Figure 5](#Fig5)). This will open the &quot;System Properties&quot; window ([Figure 6](#Fig6)).

<a name="Fig5"></a>
![Image of Search Environment Variable](/images/search-env-var.png)
 
*Figure 5. Screenshot of a search for &quot;environment variables&quot; in the Windows start menu.*

<a name="Fig6"></a> 
![Image of System Properties Window](/images/sys-prop-win.png)
 
*Figure 6. Screenshot of the &quot;System Properties&quot; window.*

2. Click the &quot;Environment Variables&quot; button on the bottom right of the window ([Figure 6](#Fig6)). This will open the &quot;Environment Variables&quot; window ([Figure 7](#Fig7)).

<a name="Fig7"></a> 
![Image of Environment Variables Window](/images/env-var-win.png)
 
*Figure 7. Edit the Path environment variable.*

3. Highlight the Path variable and click &quot;Edit&quot; ([Figure 7](#Fig7)). This will open the &quot;Edit environment variable&quot; window ([Figure 8](#Fig8)).

<a name="Fig8"></a>
![Image of Edit Environment Variables Window](/images/edit-env-var-win.png)

*Figure 8. Append the Path environment.*

4. Click &quot;New&quot; ([Figure 8](#Fig8)) and add the directory locations for \Anaconda\ and \Anaconda\Scripts to the environment path.

**IMPORTANT** : Test the Python installation from the command line by typing &quot;python&quot; (no quotes) in the terminal window. The Python program should initiate ([Figure 9](#Fig9)).

<a name="Fig9"></a>
![Image of Test Python](/images/py-test.png)

*Figure 9. Screenshot of a test of Python in the terminal window.*

It is highly recommended to run ReEDS using the conda environment provided in the repository. This environment (named `reeds2`) is specified by the `environment.yml` and can be built with the following command:

```
conda env create -f environment.yml
```

You can verify that the environment was successfully created using the following (you should see `reeds2` in the list):

```
conda env list
```

<a name="ConfigGAMS"></a>
### GAMS Configuration

Install GAMS: [https://www.gams.com/download/](https://www.gams.com/download/). NREL uses GAMS versions 45.2.0 and 34.3. Older versions might also work. A valid GAMS license must be installed. Please refer to the [Required Software](#Software) section above for more information.

Add GAMS to the &quot;path&quot; environment variable. Follow the same instructions as for adding Python to the path in the [Python Configuration](#ConfigPy) section above. Append the environment path with the directory location for the _gams.exe_ application (e.g., C:\GAMS\win64\34).


**IMPORTANT** : Test the GAMS installation from the command line by typing &quot;gams&quot; (no quotes) in the terminal window. The GAMS program should initiate (Figure 10).

<a name="Fig10"></a>
![Image of Test GAMS](/images/gams-test.png)

*Figure 10. Screenshot of a test of GAMS from the terminal window.*

<a name="Setup-Mac"></a>
# Computer Setup for MacOS
<a name="ConfigGAMS-Mac"></a>
### Download GAMS

Install GAMS: [https://www.gams.com/download/](https://www.gams.com/download/). A valid GAMS license must be installed. Please refer to the [Required Software](#Software) section above for more information.

**IMPORTANT** When installing on Mac, on the 'Installlation Type' page, click 'customize' and ensure the box to 'Add GAMS to PATH' is checked.
![Image of GAMS Install Mac](/images/gams-install-mac.png)

**To validate GAMS was installed properly** execute the following command from a new terminal (without quotes): "gams"

GAMS should initiate, you should see something similar to [Figure 10](#Fig10).

<a name="ConfigPy-Mac"></a>
### Download Anaconda
Download the latest version of Anaconda: [https://www.anaconda.com/download](https://www.anaconda.com/download)

During Installation, select to install Anaconda for your machine only.

![Image of Anaconda Install Mac](/images/anaconda-install-mac.png)

To have the installer automatically add anaconda to PATH, ensure that you've selected the box to "Add conda initialization to the shell"

![Image of Anaconda Install Mac - Customize Installation Type](/images/anaconda-custom-install-mac.png)

**To validate Python was installed properly** execute the following command from a new terminal (without quotes): "python"

Python should initiate, looking similar to [Figure 9](#Fig9).


<a name="ConfigRepo-Mac"></a>
### Clone the ReEDS Code Repository

The ReEDS source code is hosted on GitHub: https://github.com/NREL/ReEDS-2.0

1. From the Git command line run the following command to enable large file storage.
```
git lfs install
```
2. Clone the ReEDS-2.0 repository on your desktop and use the repository with GitHub Desktop. Alternatively, download a ZIP from GitHub ([Figure 4](#Fig4)).


### Set up the ReEDS conda environment
It is highly recommended to run ReEDS using the conda environment provided in the repository. This environment (named `reeds2`) is specified by the `environment.yml` and can be built with the following command - make sure you navigate to the ReEDS repository from terminal first: 

```
conda env create -f environment.yml
```

You can verify that the environment was successfully created using the following (you should see `reeds2` in the list):

```
conda env list
```


<a name="Execution"></a>
# Executing the Model
A ReEDS case (also referred to as a &quot;run&quot;, &quot;scenario&quot; or &quot;instance&quot;) is executed through a python-based case batching program called `runbatch.py` after the repository was setup. The user can execute a single case or a batch of cases using this program.

**Step 1** : Specify the ReEDS case name(s) and configuration(s) in the case configuration file. ([Figure 11](#Fig11)). The default case configuration file name is called &quot;cases.csv&quot;, but the user may create custom case configuration files by using a suffix in the file name (e.g., &quot;cases\_test.csv&quot;). The file &quot;cases\_test.csv&quot; can be used to execute a &quot;test&quot; version of the model for the ERCOT system.

Within &quot;cases.csv&quot;, The data in Column A are the model &quot;switches&quot; (also referred to as &quot;options&quot;). The data in Column B are brief descriptions of the switches. The data in Column C are the default values of the switches. The case configuration (or set of switches that define a case) begin with Column D. Each case configuration is represented by a single column. The case name is specified in Row 1. The value for each switch is specified beginning in Row 2. If a switch value is left blank, default value from Column C is used. A complete list of switches is provided in the Appendix of this document.

<a name="Fig11"></a>
![Image of Cases.csv](/images/cases-csv.png) 

*Figure 11. Screenshot of cases.csv.*

**Step 2** : Initiate the case batching program

1. Navigate to the ReEDS model directory in the file explorer or command prompt/window.
2. Activate the `reeds2` conda environment: `conda activate reeds2`. For details on creating this environment, see the #ConfigPy section above. 
3. Enter `python runbatch.py` in a command prompt (be sure to be in the ReEDS directory) to run the ReEDS case batching program ([Figure 12](#Fig12)).
4. Provide responses to the suite of prompts in the command line ([Figure 13](#Fig13)). Please refer to the [Prompts for user input during runbatch.py](#Prompts) section below for more information about the prompts.
5. Once all responses have been received, the batching program will execute the case(s) specified in the case configuration file (e.g., &quot;cases.csv&quot;). A separate terminal window will be launched for each case ([Figure 14](#Fig14)).

**Step 3** : Wait for each case to finish, check for successful completion, and view outputs. Once a case has finished (either from successful completion or from an error), the case-specific terminal window will close and a message in the main terminal window (i.e., where &quot;runbatch.py&quot; was initiated) will appear stating that the case has completed ([Figure 15](#Fig15)).

 <a name="Fig12"></a>
![Image of Execute RunBatch.py](/images/exe-runbatch.png) 

*Figure 12. Screenshot of initiating &quot;runbatch.py&quot; from the command line.*

 <a name="Fig13"></a>
![Image of RunBatch.py Prompts](/images/prompts.png)  

*Figure 13. Screenshot of prompts for user input during &quot;runbatch.py&quot;.*

 <a name="Fig14"></a>
![Image of Case Window](/images/case-win.png) 

*Figure 14. Screenshot of a separate terminal window being launched for a case.*

 <a name="Fig15"></a>
![Image of Case Finish Message](/images/case-finish.png)  

*Figure 15. Screenshot of a message in the main terminal window stating when a case has finished.*

<a name="Prompts"></a>
## Prompts for user input during &quot;runbatch.py&quot;

When a user initiates a batch of ReEDS cases through &quot;runbatch.py&quot;, a suite of prompts will appear in the terminal window. Additional details about these prompts are provided below.

**Batch Prefix** **[string]** – Defines the prefix for files and directories that will be created for the batch of cases to be executed (as listed in a case configuration file, e.g., &quot;cases.csv&quot;).

- All files and directories related to a case will be named &quot;_{batch prefix}\_{case}&quot;_. For example, if _batch prefix_=&quot;test&quot; and _case_=&quot;ref\_seq&quot;, then all files and directories related to this case will be named _test\_ref\_seq._ All files and directories for ReEDS cases are stored in a directory called &quot;\runs&quot; 
- **WARNING! A batch prefix cannot start with a number given incompatibility with GAMS.** The GAMS model declaration statement is as follows:

```
model {batch prefix}_{case} /all/ ;
```

Therefore, &quot;batch prefix&quot; CANNOT begin with a numeric and SHOULD begin with an alpha character (e.g., a, A, b, B, …).

- Entering a value of &quot;0&quot; (zero, no quotes) will assign the current date and time for the batch prefix in the form of _v{YYYYMMDD}\_{HHMM}_. Note the preceding letter vee &#39;v&#39; is necessary to ensure the batch prefix begins with an alpha character.  For example, if _batch prefix_=&quot;0&quot; and _case_=&quot;ref\_seq&quot; on September 30, 2019 at 3:00 PM (1500 hours military time), then all files and directories related to this case will be named _v20190930\_1500\_ref\_seq_
- **WARNING! Avoid re-using a (batch prefix, case) pair**. If a directory &quot;\runs\{batch prefix}\_{case}&quot; already exists, a warning will be issued in the case-specific terminal window, but &quot;runbatch.py&quot; will overwrite data in the existing case directory ([Figure 16](#Fig16)). In some instances, the case execution will pause, and a message will appear in the case-specific terminal window &quot;mv: replace […] overriding mode 0666?&quot; ([Figure 17](#Fig17)). Pressing &quot;Enter/Return&quot; will continue the execution. NREL plans to address this overwriting issue in the future by requiring user approval to overwrite an existing case directory.

 <a name="Fig16"></a>
![Image of Duplicate Case Warning](/images/duplicate-case.png)  

*Figure 16. Screenshot of warning message that appears in the main terminal window when reusing a (batch prefix, case) pair.*

 <a name="Fig17"></a>
![Image of Duplicate Case Warning 2](/images/duplicate-case-2.png)  
 
*Figure 17. Screenshot of warning message that occurs in the case-specific terminal window when reusing a (batch prefix, case) pair.*

**Case Suffix [string]**– Indicates which case configuration file—in the form &quot;cases\_{case suffix}.csv&quot;—is ingested into &quot;runbatch.py&quot; for processing.

- Entering an empty value (i.e., pressing &quot;Enter/Return&quot;) will cause the default case configuration file &quot;cases.csv&quot; to be used.
- **SUGGESTION** : Users may want to create a custom case configuration file (&quot;cases\_{…}.csv&quot;) when executing scenarios that vary from the default case configuration file (&quot;case.csv&quot;).

**Number of Simultaneous Runs [integer]** – Indicates how many cases should be run simultaneously in parallel.

- &quot;runbatch.py&quot; uses a queue to execute multiple cases.
- If there are four (4) cases and the _Number of Simultaneous Runs_=1, then &quot;runbatch.py&quot; will execute the cases one at a time.
- If there are four (4) cases and the _Number of Simultaneous Runs_=2, then &quot;runbatch.py&quot; will start two (2) cases simultaneously. Then as each case finishes a new one will start until all cases have been run.
- **WARNING**! **Be mindful about the amount of CPU and RAM usage needed for each case.**
  - Table 4 in the [What computer hardware is necessary to run ReEDS?](#Hardware) section below provides some initial data points for CPU and RAM usage.
  - An Intertemporal solve will take significant resources unless simplified (through the case configuration).
  - A Sequential solve has default value of four (4) threads in &quot;cplex.opt&quot;. The number of threads can be reduced, requiring less CPU resource usage.

**Number of simultaneous CC/Curt runs [integer]** – Indicates how many threads are to be used for the capacity credit (CC) and curtailment (curt) batching program (&quot;reflowbatch.py&quot;).

- This question is only asked when running intertemporal cases (i.e., timetype=&quot;int&quot; in the case configuration file).
- With the intertemporal case, the linear program is formulated and solved for all years at once. Then the capacity credit and curtailment calculations are executed in parallel based on the _Number of simultaneous CC/Curt runs_ specified by the user.

**How many iterations between the model and CC/Curt scripts [integer]**_–_ For an intertemporal case, the &quot;runbatch.py&quot; will execute an LP solve and then call the cc/curt scripts. The value assigned here determines how many of these iterations between the LP and the cc/curt scripts occur.

- This question is only asked when running intertemporal cases (i.e., timetype=&quot;int&quot; in the case configuration file).
- **SUGGESTION** : When executing an intertemporal case, it is good practice to set &quot;cc\_curt\_load = 1&quot; in &quot;cases.csv&quot; to enable pre-computed starting values for capacity credit and curtailment.
- Currently, there is no convergence criterion enforced. Typically, 5-6 iterations are enough for convergence, i.e., the capacity credit and curtailment values have &quot;small&quot; deviations since the prior iteration.

<a name="RunBatch"></a>
# Runbatch.py Execution Protocol

Below are the key steps that occur when a user initiates &quot;runbatch.py&quot;. Knowing these steps may help the user understand the source code of &quot;runbatch.py&quot; if modifications need to be made to the batching program.

1. Request input from user though the command prompt.
2. Ingest case names and case switches from the user-specified case configuration file (e.g., &quot;cases.csv&quot;)
3. Create a new directory for each case (\runs\{batch\_prefix}\_{case}).
4. Create a batch file of execution statements for each case: (\runs\{batch\_prefix}\_{case}\call\_{batch\_prefix}\_{case}.bat)
5. All files from &quot;runfiles.csv&quot; are copied to &quot;\runs\{batch\_prefix}\_{case}\ &quot;
    * Any files from the root of the repository will be copied to &quot;\runs\{batch\_prefix}\_{case}\ &quot;
    * Any files from &quot;\inputs\ &quot; will be copied to &quot;\runs\{batch\_prefix}\_{case}\inputs\_case\ &quot;
6. Execute the batch file for each case in a new, case-specific window. This window will close when the case is finished. GAMS will produced files unique to each case that can help the user with error debugging:
    * **GAMS Log File**
      * Path: &quot;\runs\{batch\_prefix}\_{case}\gamslog.txt &quot;
      * Purpose: contains the log outputs for all execution statements from the case batch file
      * **SUGGESTION** : This is a good place to check in which execution step errors may have occurred.
    * **GAMS listing files (\*.lst)**
      * Path: &quot;\runs\{batch\_prefix}\_{case}\lstfiles\ &quot;
      * Purpose: contains the listing files for GAMS executions
      * **SUGGESTION** : This is a good place to check in which line of the source code errors may have occurred
    * **GAMS workfile (\*.g00)**
      * Path: &quot;\runs\{batch\_prefix}\_{case}\g00files\ &quot;
      * Purpose: stores a snapshot of all the model information available to GAMS at that point in the case execution.
      * For more information about GAMS work files: [https://www.gams.com/latest/docs/UG\_SaveRestart.html](https://www.gams.com/latest/docs/UG_SaveRestart.html)
      * **SUGGESTION** : A failed case can be restarted from this snapshot point. The user can rerun the batch file for the case (\runs\{batch\_prefix}\_{case}\call\_{batch\_prefix}\_{case}.bat) after commenting out execution statements that completed successfully.
7. Build outputs and standard visualization reports for each case that completes successfully.
  * Following a successful run, a suite of .csv output files are created in: &quot;\runs\{batch\_prefix}\_{case}\outputs\ &quot;
  * A standard .html visualization report is stored in: &quot;\runs\{batch prefix}\_{case}\outputs\reeds-report\ &quot;

<a name="CaseBatch"></a>
## Case-specific Batch File Execution Protocol

**Execute CreateModel.gms:**

1. Execute B\_Inputs.gms – ingest data from the files created by the input_processing scripts and format the data to be useful for the GAMS execution
2. Execute C\_SupplyModel.gms – declare the variables and constraints for the linear program
3. Execute C\_SupplyObjective.gms – declare the objective function for the linear program, broken into two parts (investment and operations)
4. Execute D\_SolvePrep.gms – initiate the LP solve and compute parameters based on switch values in the case configuration file (e.g., &quot;cases.csv&quot;)
5. Create a GAMS work file at the completion of CreateModel.gms
  1. Path: &quot;\runs\{batch\_prefix}\_{case}\g00files\{batch\_prefix}\_{case}.g00&quot;
  2. For more information about GAMS work files: [https://www.gams.com/latest/docs/UG\_SaveRestart.html](https://www.gams.com/latest/docs/UG_SaveRestart.html)

**Execute the sequential solve structure** ([Figure 18](#Fig18))

For every year in the model horizon, execute d\_solveoneyear.gms:

1. Execute solve
2. Execute d\_callreflow.gms – Compute capacity credit and curtailment:
  1. Execute ReEDS\_capacity\_credit.gms - compute the parameters necessary for ReEDS\_capacity\_credit.py (which computes the capacity credit)
  2. Execute REflow\_RTO\_2\_params.gms – translate the parameters from ReEDS 2.0 into their equivalents from ReEDS Heritage
  3. Execute REflow\_RTO\_3.gms – compute curtailment using the syntax and structure from ReEDS Heritage
  4. Execute d4\_Translate\_Variability.R – Translate the values from REflow\_RTO\_3.gms (ReEDS Heritage) back to the syntax and structure used in ReEDS 2.0

 <a name="Fig18"></a>
![Image of Sequential Flow](/images/seq-flow.png)  
 
*Figure 18. Depiction of execution sequence for the &quot;sequential&quot; solve.*

**Execute the intertemporal solve structure** ([Figure 19](#Fig19))

For each iteration (specified via the runbatch.py prompt),

1. Execute d\_solveallyears.gms
2. Execute reflowbatch.py
  1. Execute d\_callreflow.gms – Compute capacity credit and curtailment; same process as for sequential, but for all years
  2. Once all cc/curt calculations are done, files are merged via the GAMS gdxmerge utility
3. Execute d5\_mergevariability.R – The resulting file from the gdxmerge execution is restructured for use in GAMS during the next iteration of the intertemporal solve.

 <a name="Fig19"></a>
![Image of Intertemporal Flow](/images/inter-flow.png)  
 
*Figure 19. Depiction of execution sequence for the &quot;intertemporal&quot; solve.*

<a name="Documentation"></a>
# Documentation

The ReEDS Version 2020 Documentation is available at no cost from the National Renewable Energy Laboratory: [https://www.nrel.gov/docs/fy21osti/78195.pdf](https://www.nrel.gov/docs/fy21osti/78195.pdf)

Detailed documentation of ReEDS 2.0 input files are available [here](/sources_documentation.md).

The source code in this repository is the ReEDS Version 2020 model. 

[Table 1](#Tab1) summarizes difference between Versions 2019 and 2020.

<a name="Tab1"></a>
*Table 1. differences between ReEDS Versions 2019 and 2020.*

**Inputs and Treatments**|**2019 Version (July 2019)**|**2020 Version (July 2020)**
:-----:|:-----:|:-----:
Fuel prices|AEO2019|AEO2020
Demand growth|AEO2019|AEO2020
Generator technology cost, performance, and financing|ATB 2019|ATB 2020
Regional Greenhouse Gas Initiative (RGGI)|Virginia not included in RGGI|Virginia included in RGGI
Endogenous retirements|Off by default; when turned on, plants retire when they cannot recover their fixed O&M|On by default; when turned on, plants retire when they cannot recover at least half of their fixed O&M
Coal fixed O&M|Escalate from online year|Escalates from 2019 using assumptions from AEO2019
Nuclear fixed O&M|Escalate from 2010|Escalates from 2019 using assumptions from AEO2019
Wind, solar, and load data|Includes 2012 data only|Includes data for 2007–2013; dispatch is done using 2012 data and capacity credit calculations are done using 2007–2013 data (W. Cole, Greer, et al. 2020)
Electrification|Not included|Includes three levels of electrification
Demand-side flexibility|Not included|Includes three levels of flexibility
Renewable fuel combustion turbine|Not included|Includes combustion turbine that runs on a generic renewable fuel with a minimum 6% capacity factor
Upgrades|Not included|Thermal technologies can be upgraded (e.g., by adding CCS).
Storage curtailment recovery|Assume that every 1 MWh of storage charging reduces curtailment in that region by 0.5 MWh|Uses hourly net load profiles and a dispatch algorithm to determine the amount of curtailment that can be recovered by storage
Battery storage durations|4-hour batteries only|Includes 2-, 4-, 6-, 8-, and 10-hour battery storage
Storage capacity credit|Calculated using one year of hourly data, applies a linear approximation in the optimization model|Calculated using seven years of hourly data; capacity credit bins by duration allow for nonlinear changes in the optimization model; one-hour buffer accounts for uncertainty in forecasts and ability to dispatch
Wind and solar capacity credit|Calculated using one year of hourly resource and load data|Calculated using seven years of hourly resource and load data
Wind supply curve|Exclusions based on land-use land-cover categories as specified in Lopez et al. (2012)|Spatially-explicit modeling of multiple exclusions and setbacks from buildings, roads, transmission rights-of-way, and radar along with other exclusion layers
Wind degradation|Not included|Annual degradation of 0.27% per year represented based on empirical data (Hamilton et al. 2020)
PV degradation|0.5%/yr|0.7%/yr per the ATB 2020
Wind and solar curtailment|Modeled using convolutions of resource and load data at a time-slice resolution |Modeled using a simplified hourly dispatch model
Pumped-hydro capital cost|Static over time|Declines over time per Hydropower Vision (DOE 2016)
Storage energy arbitrage value|Calculated at the ReEDS 17-time-slice resolution|Calculated using hourly prices
Minimum capacity factor for NGCT|None|1% per PLEXOS runs of the 2019 Standard Scenarios
Tax credits|Use a three-year safe harbor construction period; tax credits for CCS not represented|Use a four-year safe harbor construction period; December 2019 production tax credit update represented; tax credits for CCS represented (use of captured carbon is not considered)
State policies|Policies as of July 2019|Policies as of June 2020
Nuclear power plant assistance|Assistance for Illinois and New York represented|Assistance for Connecticut, Illinois, New Jersey, New York, and Ohio represented 
Outage rates|Outage rates based on 2003–2007 Generating Availability Data System data|Outage rates based on 2014–2018 Generating Availability Data System data

### References
* Cole, Wesley, Daniel Greer, Jonathan Ho, and Robert Margolis. &quot;Considerations for maintaining resource adequacy of electricity systems with high penetrations of PV and storage.&quot; Applied Energy 279 (2020): 115795.
* U. S. Department of Energy 2016. &quot;Hydropower Vision: A New Chapter for America’s 1st Renewable Electricity Source.&quot; Technical Report DOE/GO-102016-4869. Washington, D.C.: U. S. Department of Energy. http://energy.gov/eere/water/articles/hydropower-vision-new-chapter-america-s-1st-renewable-electricity-source.
* Lopez, A., B. Roberts, D. Heimiller, N. Blair, and G. Porro. 2012. &quot;US Renewable Energy Technical Potentials: A GIS-Based Analysis.&quot; Golden, CO: National Renewable Energy Laboratory. https://www.nrel.gov/docs/fy12osti/51946.pdf

<a name="Architecture"></a>
# Model Architecture

<a name="Modules"></a>
## Modules

The ReEDS model is comprised of several modules with one and two-way data exchange between the modules. [Figure 20](#Fig20) depicts these modules, including linkages between the modules and directions of data exchange. The supply module is the core module for ReEDS. Within a ReEDS execution, the key data exchanges occur between (1) the Supply Module and the Variable Resource Renewable (VRR) Modules for estimating Capacity Credit and Curtailment; and (2) the Supply Module and the Demand Module. These module interactions are dictated by the model execution approach, i.e., _sequential_ solves, _sliding window_ solves, or _intertemporal_ solves. [Figure 21](#Fig21) illustrates the _sequential_ approach; [Figure 22](#Fig22) the sliding window and intertemporal approaches.

<a name="Fig20"></a>
![Image of ReEDS Modules](/images/modules.png)  

*Figure 20. Depiction of ReEDS modules; arrows indicate directions of data exchange.*

<a name="Fig21"></a>
![Image of Sequential Flow](/images/seq-flow-2.png)   

*Figure 21. Schematic illustrating the model structure with a sequential solve.*

<a name="Fig22"></a>
![Image of Intertemporal Flow](/images/inter-flow-2.png)   

*Figure 22. Schematic illustrating the model structure with sliding window or intertemporal solves.*

<a name="Stock"></a>
## Tracking Capital Stock

Because ReEDS is a long-term capacity planning model, electricity generation capacity (capital stock) must be tracked over time, including initial capacity, new investments, refurbishment investments, lifetime retirements, and endogenous retirements. [Figure 23](#Fig23) depicts time resolution terminology and capital stock terminology. &quot;Historical&quot; years are 2010-2018, inclusive. &quot;Future&quot; years are 2019 and beyond. &quot;Pre-modeled&quot; years are years prior to 2010 and are not represented in the model decision making. &quot;Modeled&quot; years are years beginning in 2010, the first year of the model to the end of the model horizon. Users can specify the frequency of modeled years as depicted in [Figure 24](#Fig24) in &quot;\inputs\user\_input\modeledyears\_default.csv&quot; and the horizon is specified in &quot;cases.csv&quot;.

<a name="Fig23"></a>
![Image of Time and Stock](/images/time-and-stock.jpg)   

*Figure 23. Depiction of time resolution terminology and capital stock terminology*

<a name="Fig24"></a>
![Image of Model Years](/images/model-years.png)   
 
*Figure 24. Depiction of user-specified model years.*

Capital stock added during the model execution is tracked by a vintage classification based on the time frame when the capacity is installed (e.g., capacity installed between 2030 and 2035 could be defined as a vintage class). The user can specify the vintage class resolution by technology type to control the model size (see &quot;\inputs\userinput\ivt.csv&quot;). All capacity of a technology type (e.g., nuclear) within the same vintage class has the same operating characteristics. Regardless of the vintage class, new investments incur capital cost associated with the year that the investment occurs.

Distinction is made between vintage classes for capacity built during the _pre-modeled_ years---i.e., the _initial_ vintage classes---and vintage classes for capacity built during the _modeled_ years, i.e., the _added_ vintage classes, ([Figure 23](#Fig23)). The _initial_ vintage classes are categorized based on plant performance, specifically, heat rate ([Figure 25](#Fig25)). Whereas, _added_ vintage classes are categorized based on when the capacity is installed.

_Initial_ capacity is tracked based on the capacity remaining in each model year after planned retirements have been removed. Planned capacity additions made during _historical modeled_ years, i.e., 2010-2018, are prescribed _exactly_, thus the model must build _exactly_ the prescribed amount. Planned capacity built during _future modeled years_, i.e.,  2019-2050, are prescribed as a _lower bound_ for new investments, thus the model must build _at least_ the prescribed amount ([Figure 23](#Fig23)).

<a name="Fig25"></a>
![Image of Historical Bins](/images/historical-bins.png)   

*Figure 25. Example of categorizing model plants for the existing fleet based on heat rate.*

<a name="FAQ"></a>
# Frequently Asked Questions

<a name="Fees"></a>
## How much are the GAMS licensing fees?

Please contact GAMS for more information.

<a name="Trial"></a>
## Is there a trial version of the GAMS license so that I can test ReEDS?

We have created a reduced size version of the ReEDS model that has less than 5,000 rows and columns, and therefore should be compatible with the GAMS community license (https://www.gams.com/try_gams/ -- Please contact GAMS if you need additional information regarding the community license). You can run this reduced model version by using the cases_small.csv input file. This reduced model uses a smaller technology subset, smaller geographic extent, and simplifies several model constraints.

<a name="Hardware"></a>
## What computer hardware is necessary to run ReEDS?

NREL uses Windows servers to execute the ReEDS model. These servers have Intel(R) Xeon(R) CPUs at 2-2.4GHz and 10-14 cores with 160-320GB of RAM. These servers can execute multiple ReEDS cases in parallel.

[Table 4](#Tab4) summarizes RAM usage and total clock time necessary to execute the default ReEDS configuration for the three different solve structures (sequential, window, and intertemporal) using one of these servers.

<a name="Tab4"></a>
*Table 4. Ballpark RAM usage and clock time for select model configurations executed on NREL servers.*

| Solve Structure | Solve Steps | Approximate LP size <br> per instance (after presolve) | Threads | RAM(GB per instance) | Total Clock Time (hours) |
| --- | --- | --- | --- | --- | --- |
| Sequential | 2010-2030: 2 yr <br> 2031-2050: 5 yr | Rows: 461k <br> Columns: 384k <br> Non-Zeros: 2,042k | 4 | 4-7GB | 3-5 |
| Window | 2010-2030: 2 yr <br> 2031-2050: 5 yr | Rows: 1,143k <br> Columns:869k <br> Non-Zeros: 5,087k | 8 | 14-18GB | 18-22  |
| Intertemporal | 2010-2030: 2 yr <br> 2031-2050: 5 yr | Rows:12,789k <br> Columns: 9,890k <br> Non-Zeros: 61,076k | 12 | 57GB+ | 48-72|

Table Notes:
* Default solve window configuration: 11 windows and 5 iterations per window (see &quot;\inputs\userinput\windows_default.csv&quot;). The problem size is taken from last iteration. The problem size varies by about 5% across iterations.
* Intertemporal: 8-12 hours per iteration, 5-7 iterations total

<a name="Interconnect"></a>
## Can I configure a ReEDS case to run as an isolated interconnect?
Yes, you can configure ReEDS as a single interconnect. Limiting the spatial extent may be beneficial for modeling more difficult instances. 

**WARNING!:** The default case configurations were designed for modeling the lower 48 United States. Therefore, the user should be aware of possible issues with executing an interconnect in isolation, including but not limited to the following:

* Natural gas prices are based on either national or census division supply curves. The natural gas prices are computed as a function of the quantity consumed relative to a reference quantity. Consuming less than the reference quantity drives the price downward; consuming more drives the price upward. When modeling a single interconnection, the user should either modify the reference gas quantity to account for a smaller spatial extent or use fixed gas prices in every census division (i.e., case configuration option [GSw\_GasCurve](#SwOther) = 2). For example, if we execute ERCOT in isolation using census division supply curves, we may want to reduce the reference gas quantity for the West South Central (WSC) census division which includes Texas, Oklahoma, Arkansas, and Louisiana. Or we could assume the gas price in the WSC region is fixed.

* Infeasibilities may arise in state-level constraints when only part of a state is represented in an interconnect. For example, the Western interconnection includes a small portion of Texas (El Paso). State-level constraints will be enforced for Texas, but El Paso may not be able to meet the requirement for all of Texas.

* Certain constraints may not apply in every interconnect. Some examples include: 
  * California State RPS REC trading constraints only apply to the West
  * CAIR and CSAPR only apply to certain states, so the emission limits may need to be adjusted
  * RGGI only applies to a subset of states in the northeast 
  * California policies (e.g., SB32, California Storage Mandate) only apply to California

<a name="Contact"></a>
# Contact Us:

If you have comments and/or questions, please contacts the ReEDS team:

[ReEDS.Inquiries@nrel.gov](mailto:ReEDS.Inquiries@nrel.gov)

<a name="Appendix"></a>
# Appendix:

<a name="Switches"></a>
## ReEDS Model Switches (specified by user in &quot;cases.csv&quot;)

ReEDS model switches are set in the cases.csv file. The "Choices" column lists allowable options for that switch, with N/A meaning that no error checking is performed for the options selected.

<a name="SolveTime"></a>
## Tips for reducing solve time

If you'd like to reduce the model solve time, consider making some of the following changes:
* `yearset_suffix = 4yr` or `yearset_suffix = 5yr`
  * Solve in 4- or 5-year steps
* `GSw_OpRes = 0`
  * Turn off operating reserves
* `GSw_MinLoading = 0`
  * Turn off the sliding-window representation of minimum-generation limits
* `GSw_HourlyNumClusters = 25` (or lower)
  * Reduce the number of representative periods
* `GSw_RegionResolution = aggreg` and `GSw_HierarchyFile = default`, or `agg2`
  * Aggregate the native 134 zones into fewer, larger zones. `GSw_HierarchyFile = default` aggregates the 134 zones into 69 zones (obeying state, interconnect, NERC, and FERC region boundaries); `GSw_HierarchyFile = agg2` aggregates the 134 zones into 54 zones (obeying state boundaries).