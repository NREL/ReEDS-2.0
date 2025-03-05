# Diagnoses
The `diagnose_process.py` script generates reports from ReEDS A and B matrices to obtain model characteristics.  
## Overview

The `diagnose_process.py` script provides detailed statistics of ReEDS using the CONVERT solver. CONVERT is a tool that transforms a GAMS model instance into a scalar model, converting it into formats used by other modeling and solution systems. It requires the GAMS model and a GDX file as inputs.
The `diagnose_process.py` script analyzes the CONVERT outputs to generate model characteristics in CSV files. These characteristics include:
- The number of variables, equations, and non-zero values.
- Reporting variables (if any), along with their names.
- Dense columns and their counts.
- Matrix statistics:
    - Minimum, maximum, absolute minimum, absolute maximum.
    - Ratio of max(abs) to min(abs).
    - Number of reporting variables.
    - Share of reporting variables in total variables.
    - Share of reporting variables in total non-zero variables.
- Equation RHS statistics:
    - Maximum, minimum, absolute maximum, and absolute minimum values.
    - The equations with the maximum and minimum RHS values.


## How to run 

The diagnose analysis can be run as part of a ReEDS run by setting `diagnose = 1`. If diagnose is  is set to 1, ReEDS runs as usual and provides solutions with CONVERT outputs. At the end of batch run, the model runs automatically `/postprocessing/diagnose/diagnose_process.py` to generate model statistics. Alternatively, if the run has CONVERT outputs, the script can be run as a standalone for a specified ReEDS run by passing the folder of the run.

The GAMS provides a Python API that includes several sub-modules for controlling the GAMS system. One of the sub-modules, `gams.transfer`, facilitates data transfer between GAMS and the target programming language. More information about `gams.transfer` can be found here: [gams.tranfer](https://www.gams.com/latest/docs/API_PY_GAMSTRANSFER.html). To install the API, use the following command:

    ```pip install gamsapi[transfer]==xx.y.z```

Here,`xx.y.z` represents the installed GAMS version number. Note that, the `gams.transfer` library is available starting from GAMS 37 version. If you have installation problem, [GAMS API](https://www.gams.com/latest/docs/API_PY_GETTING_STARTED.html#PY_PIP_INSTALL_BDIST) explains how to install the library.

Complex model like ReEDS has a larger number of equations and variables, which increases the size of matrix and RHS informations. To limited the output size, `diagnose_process.py` has three switches to explicitly generate these reports. These switches, have default values of 0, are ;
- `GSw_matrix`: Generates the matrix values.
- `GSw_rhs`: Retrieves the RHS values.
- `GSw_var_count_by_block`: Provides the variable count by block.

Additionally, `diagnose_process.py` includes a `year` switch, which is used to specify a single year for reporting. The default value of `year` is 0, meaning the code will report all years or which dump GDX files and scalars are available.

Example call: `python postprocessing/diagnose/diagnose_process.py --casepath [case path] --year 2050 --GSw_matrix 1 --GSw_rhs 1 --GSw_var_count_by_block 1 `
## Outputs

The CONVERT solver produces `reeds_[year].gdx` and `scalar_model_[year].gms` files for each modeled years which are located in `[casedir]\outputs\model_diagnose`. The script uses these files to produce csv files named in the format `.csv` in same location of CONVERT outputs location. These csv files are;
- `describe_matrix.csv`
- `describe_rhs.csv`
- `reeds_[year].png`
- `var_count.csv`
- `matrix.csv`(optional)
- `rhs.csv`(optional)
- `var_count_by_block.csv`(optional)

  