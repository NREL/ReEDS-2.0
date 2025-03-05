# ReEDS 2.0
## Welcome to the Regional Energy Deployment System (ReEDS) Model!

This GitHub repository contains the source code for NREL&#39;s ReEDS model. The ReEDS model source code is available at no cost from the National Renewable Energy Laboratory. The ReEDS model can be downloaded or cloned from [https://github.com/NREL/ReEDS-2.0](https://github.com/NREL/ReEDS-2.0). 

**For more information about the model, see the [ReEDS-2.0 Documentation](https://pages.github.nrel.gov/ReEDS/ReEDS-2.0)**

<!-- **For more information about the model, see the [open source ReEDS-2.0 Documentation](https://nrel.github.io/ReEDS-2.0)** -->

A ReEDS training video (based on the 2020 version of ReEDS) is available on the NREL YouTube channel at [https://youtu.be/aGj3Jnspk9M?si=iqCRNn5MbGZc8ZIO](https://youtu.be/aGj3Jnspk9M?si=iqCRNn5MbGZc8ZIO).

<a name="Introduction"></a>
# Introduction ([https://www.nrel.gov/analysis/reeds/](https://www.nrel.gov/analysis/reeds/)) 

The Regional Energy Deployment System (ReEDS) is a capacity planning and dispatch model for the North American electricity system.

As NREL&#39;s flagship long-term power sector model, ReEDS has served as the primary analytic tool for many studies ([https://www.nrel.gov/analysis/reeds/publications.html](https://www.nrel.gov/analysis/reeds/publications.html)) of important energy sector research questions, including clean energy policy, renewable grid integration, technology innovation, and forward-looking issues of the generation and transmission infrastructure. Data from the most recent base case and a suite of Standard Scenarios are provided.

ReEDS uses high spatial resolution and high-fidelity modeling. Though it covers a broad geographic and technological scope, ReEDS is designed to reflect the regional attributes of energy production and consumption. Unique among long-term capacity expansion models, ReEDS possesses advanced algorithms and data to represent the cost and value of variable renewable energy; the full suite of other major generation technologies, including fossil and nuclear; and transmission and storage expansion options. Used in combination with other NREL tools, data, and expertise, ReEDS can provide objective and comprehensive electricity system futures.

<a name="Software"></a>
# Required Software

The ReEDS model is written primarily in GAMS with auxiliary modules written in Python. At present, NREL uses the following software versions: GAMS 45.2; Python 3.11. Other versions of these software may be compatible with ReEDS, but NREL has not tested other versions at this time.

GAMS is a mathematical programming software from the GAMS Development Corporation. &quot;The use of GAMS beyond the limits of the free demo system requires the presence of a valid GAMS license file.&quot; [[1](https://www.gams.com/latest/docs/UG_License.html)] The ReEDS model requires the GAMS Base Module and a linear programming (LP) solver (e.g., CPLEX). The LP solver should be connected to GAMS with either a GAMS/Solver license or a GAMS/Solver-Link license. &quot;A GAMS/Solver connects the GAMS Base module to a particular solver and includes a license for this solver to be used through GAMS. It is not necessary to install additional software. A GAMS/Solver-Link connects the GAMS Base Module to a particular solver, but does not include a license for the solver. It may be necessary to install additional software before the solver can be used.&quot; [[2](https://www.gams.com/products/buy-gams/)]

NREL subscribes to the GAMS/CPLEX license for the LP solver, but open-source solvers and free, internet-based services are also available. 
* The [_COIN-OR Optimization Suite_](https://www.coin-or.org/downloading/) includes open-source solvers that can be linked with GAMS through the GAMS Base Module. NREL has tested the use of the COIN-OR Linear Programming (CLP) solver for ReEDS. More information about using CLP for ReEDS can be found [_here_](https://www.nrel.gov/docs/fy21osti/77907.pdf). 
* The [_NEOS Server_](https://neos-server.org/neos/) is a free, internet-based service for solving numerical optimization problems. Links with NEOS can be made through [_KESTREL_](https://www.gams.com/latest/docs/S_KESTREL.html) which is included in GAMS Base Module. In its current form, ReEDS cannot be solved using NEOS due to the 16 MB limit on submissions to the server. However, modifications _could_ be made to ReEDS to _potentially_ reduce the data below to the required submission size. Note that some solvers available on the NEOS server are limited to non-commercial use. 

Python is &quot;an object-oriented programming language, comparable to Perl, Ruby, Scheme, or Java.&quot; [[3](https://wiki.python.org/moin/BeginnersGuide/Overview)] &quot; Python is developed under an OSI-approved open source license, making it freely usable and distributable, even for commercial use. Python&#39;s license is administered by the Python Software Foundation.&quot; [[4](https://www.python.org/about/)]. NREL uses Conda to build the python environment necessary for ReEDS. Conda is a &quot;package, dependency and environment management for any language.&quot; [[5](https://docs.conda.io/en/latest/)]

Git is a version-control tool used to manage code repositories. Included in Git is a unix style command line emulator called Git Bash, which is used by ReEDS to perform some initial setup tasks.

<a name="Contact"></a>
# Contact Us:

If you have comments and/or questions, you can contact the ReEDS team at [ReEDS.Inquiries@nrel.gov](mailto:ReEDS.Inquiries@nrel.gov)

Alternatively, you can post questions at ReEDS repository [discussion page](https://github.com/NREL/ReEDS-2.0/discussions).
