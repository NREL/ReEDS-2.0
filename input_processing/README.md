# hourly_process.py

## Switches
* `GSw_HourlyNumClusters` specifies the maximum number of representative periods.
* Two other switches, `GSw_HourlyPeakLevel` and `GSw_HourlyMinRElevel`, indicate additional "stress periods" that can be added. They're both set to "interconnect" by default, so for the US they add the 3 peak-load days, 3 minimum-wind days, and 3 minimum-PV days by interconnect, resulting in 33+9=42 by default if `GSw_HourlyNumClusters`=33.
* When using `GSw_HourlyClusterAlgorithm=optimized` (the default), then depending on the setting of `GSw_HourlyClusterRegionLevel` there will be a maximum number of days it needs to reproduce the distribution of load/pv/wind. When `GSw_HourlyClusterRegionLevel=transreg` (the default), there are 11 regions and 3 features, so it needs ~33 days to reproduce the distribution (like an eigenvalue problem).
    * So turning up `GSw_HourlyNumClusters` on its own won't increase the temporal coverage. If you want more temporal coverage, the options are:
        * Switch to `GSw_HourlyType=wek`, which increases the length of the periods from 1 day to 5 days. If all the other switches are left at their defaults, switching to `wek` would increase the coverage from 42 days to 5*42=210 days.
        * Reduce `GSw_HourlyClusterRegionLevel` to something smaller than transreg (like `st`), and then increase `GSw_HourlyNumClusters`
        * Switch to `GSw_HourlyClusteAlgorithm=hierarchical` and then increase `GSw_HourlyNumClusters` (although that's less desirable, because hierarchical clustering doesn't do as good of a job of reproducing the actual spatial distribution of CF and load)
        * Switch to `Gsw_HourlyType=year`. Although if you're running for the whole US you'll need to turn on region aggregation (`GSw_AggregateRegions=1` and `GSw_HierarchyFile` in [`agg0`, `agg1`, or `agg2`]) for it to solve.
* `GSw_HourlyClusterAlgorithm`
    * If set to 'hierarchical', then hierarchical clustering is used via
        ```python
        sklearn.cluster.AgglomerativeClustering(
            n_clusters=int(sw['GSw_HourlyNumClusters']),
            affinity='euclidean', linkage='ward')
        ```
    * If set to 'optimized', then a two-step custom optimization is performed using the `hourly_repperiods.optimize_period_weights()` and `hourly_repperiods.assign_representative_days()` functions to minimize the deviation in regional load and PV/wind CF between the weighted representative periods and the full year.

## Conventions
* Timestamps are formatted as `y{year}d{day of year}h{hour of day}` in hour-ending format in Eastern Standard Time. The numbering of days begins at 1. For example, the hour from 3am-4am on January 3, 2012 would be indicated as `y2012d003h004`.
    * When using representative weks (5-day periods), timestamps are instead formatted as `y{year}w{wek of year}h{hour of wek}`. The numbering of weks begins at 1. In this format, the hour from 3am-4am on January 3, 2012 would be indicated as `y2012w001h052`.
* Representative and stress *periods* (indexed as `szn` within ReEDS) are labeled similarly to timestamps but without the `h{hour of day}` component.
