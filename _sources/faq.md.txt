# FAQ
## How much are the GAMS licensing fees?
Please contact GAMS for more information.

## Is there a trial version of the GAMS license so that I can test ReEDS?
We have created a reduced size version of the ReEDS model that has less than 5,000 rows and columns, and therefore should be compatible with the GAMS community license ([https://www.gams.com/try_gams/](https://www.gams.com/try_gams/) -- Please contact GAMS if you need additional information regarding the community license). You can run this reduced model version by using the cases_small.csv input file. This reduced model uses a smaller technology subset, smaller geographic extent, and simplifies several model constraints.

## What computer hardware is necessary to run ReEDS?
Running ReEDS using the reference case (located in cases.csv) is feasible on a laptop with 32GV of RAM. However, for running ReEDS with enhanced features such as explicit H2 modeling, C02 networks, increased temporal/spatial resolution, etc., it is recommened to utlize a higher-performance workstation or High-Performance Computing (HPC) machine.

can be run on a laptop with 32GB of RAM. However, if you would like to run ReEDS with more detailed options (explicit H2 modeling, C02 networks, higher temporal/spatial resolution, etc.), it is recommended to use a higher-performance workstation or HPC.

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

## Is there a way to reduce solve time?

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

## How often are updates made to ReEDS?
Every year we target June 1 for the bulk of model changes to be completed, which allows us to meet the hard deadline for having a working, updated version of the model by June 30. We typically make minor updates to the model over the summer and tag a final version for that year in August or September. This version is then used to produce the Standard Scenarios and Cambium data products. 

Additionally, changes are made throughout the year and a new version is created and published roughly every month. You can find current and past ReEDS versions here: [ReEDS-2.0 Releases]({{ github_releases_url }})

If you would like to run ReEDS with a previous version, you can either download the source code directly or check out that version using the tag. 

To check out a previous version using its tag, you can run the following command from your command line or terminal (ensure you have the main branch of the repo checked out): 
```
git checkout tags/{version number}
```

Here is an example of what this would look like: 
```
git checkout tags/v2024.0.0
```