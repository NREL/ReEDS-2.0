*=============================================
* -- Timeslices and seasons --
*=============================================
Sets
* Most of these are copied from inputs/variability, overwritten by hourly_writetimeseries.py
h_rep(allh) "representative timeslices"
/
$offlisting
$include inputs_case%ds%set_h.csv
$onlisting
/

$onempty
h_stress(allh) "stress timeslices for the current model year"
/
$offlisting
$include inputs_case%ds%stress%stress_year%%ds%set_h.csv
$onlisting
/
$offempty


szn_rep(allszn) "representative periods, or seasons if modeling full year"
/
$offlisting
$include inputs_case%ds%set_szn.csv
$onlisting
/

actualszn(allszn) "actual periods (each is described by a representative period)"
/
$offlisting
$include inputs_case%ds%set_actualszn.csv
$onlisting
/

$onempty
szn_stress(allszn) "stress periods for the current model year"
/
$offlisting
$include inputs_case%ds%stress%stress_year%%ds%set_szn.csv
$onlisting
/
$offempty
;

* The h set contains h_rep and h_stress; the szn set containts szn_rep and szn_stress
h(allh) = no ;
szn(allszn) = no ;

h(allh)$[h_rep(allh)] = yes ;
h(allh)$[h_stress(allh)] = yes ;
szn(allszn)$[szn_rep(allszn)] = yes ;
szn(allszn)$[szn_stress(allszn)] = yes ;

Sets
h_szn(allh,allszn) "mapping of hour blocks to seasons"
/
$offlisting
$ondelim
$include inputs_case%ds%h_szn.csv
$include inputs_case%ds%stress%stress_year%%ds%h_szn.csv
$offdelim
$onlisting
/

h_szn_start(allszn,allh) "starting hour of each season"
/
$offlisting
$ondelim
$include inputs_case%ds%h_szn_start.csv
$include inputs_case%ds%stress%stress_year%%ds%h_szn_start.csv
$offdelim
$onlisting
/

h_szn_end(allszn,allh) "ending hour of each season"
/
$offlisting
$ondelim
$include inputs_case%ds%h_szn_end.csv
$include inputs_case%ds%stress%stress_year%%ds%h_szn_end.csv
$offdelim
$onlisting
/

* Inter-seasonal storage level (e.g. H2), which uses h_actualszn and nexth_actualszn,
* is only tracked over actual ("energy") periods, not stress periods
h_actualszn(allh,allszn) "mapping from rep timeslices to actual periods"
/
$offlisting
$ondelim
$include inputs_case%ds%h_actualszn.csv
$offdelim
$onlisting
/

nexth_actualszn(allszn,allh,allszn,allh) "Mapping between one timeslice and the next for actual periods (szns)"
/
$offlisting
$ondelim
$include inputs_case%ds%nexth_actualszn.csv
$offdelim
$onlisting
/

nexth(allh,allh) "Mapping set between one timeslice (first) and the following (second)"
/
$offlisting
$ondelim
$include inputs_case%ds%nexth.csv
$include inputs_case%ds%stress%stress_year%%ds%nexth.csv
$offdelim
$onlisting
/

;

* Record the stress periods for each model year
h_t(h,t)$[tmodel(t)] = yes ;
szn_t(szn,t)$[tmodel(t)] = yes ;
h_stress_t(h,t)$[h_stress(h)$tmodel(t)] = yes ;
szn_stress_t(szn,t)$[szn_stress(szn)$tmodel(t)] = yes ;
h_szn_t(h,szn,t)$[h_szn(h,szn)$tmodel(t)] = yes ;


$offOrder
set starting_hour(allh) "starting hour without tz adjustments"
    final_hour(allh)    "final hour without tz adjustments"
;

* find the minimum and maximum ordinal of modeled hours within each season
starting_hour(h)$[sum{szn,h_szn(h,szn)$(smin(hh$h_szn(hh,szn),ord(hh))=ord(h)) }] = yes ;
final_hour(h)$[sum{szn,h_szn(h,szn)$(smax(hh$h_szn(hh,szn),ord(hh))=ord(h)) }] = yes ;

* note summing over szn to find the minimum/maximum ordered hour within that season
starting_hour_nowrap(h)$[sum{szn, h_szn_start(szn,h) }$(not Sw_HourlyWrap)] = yes ;
final_hour_nowrap(h)$[sum{szn, h_szn_end(szn,h) }$(not Sw_HourlyWrap)] = yes ;

* Get the order of actual periods
nextszn(actualszn,actualsznn)$[(ord(actualsznn) = ord(actualszn) + 1)] = yes ;
nextszn(actualszn,actualsznn)
    $[(ord(actualszn) = smax(actualsznnn, ord(actualsznnn)))
    $(ord(actualsznn) = smin(actualsznnn, ord(actualsznnn)))]
    = yes ;

$onOrder


parameter hours(allh) "--hours-- number of hours in each time block"
/
$offlisting
$ondelim
$include inputs_case%ds%numhours.csv
$include inputs_case%ds%stress%stress_year%%ds%numhours.csv
$offdelim
$onlisting
/ ;

parameter numdays(allszn) "--number of days-- number of days for each season" ;
numdays(szn) = sum{h$h_szn(h,szn),hours(h) } / 24 ;

parameter numhours_nexth(allh,allhh) "--hours-- number of times hh follows h throughout year"
/
$offlisting
$ondelim
$include inputs_case%ds%numhours_nexth.csv
$offdelim
$onlisting
/ ;

* Written by input_processing/hourly_writetimeseries.py
parameter frac_h_quarter_weights(allh,quarter) "--unitless-- fraction of timeslice associated with each quarter"
/
$offlisting
$ondelim
$include inputs_case%ds%frac_h_quarter_weights.csv
$include inputs_case%ds%stress%stress_year%%ds%frac_h_quarter_weights.csv
$offdelim
$onlisting
/ ;

parameter frac_h_ccseason_weights(allh,ccseason) "--unitless-- fraction of timeslice associated with each ccseason"
/
$offlisting
$ondelim
$include inputs_case%ds%frac_h_ccseason_weights.csv
$include inputs_case%ds%stress%stress_year%%ds%frac_h_ccseason_weights.csv
$offdelim
$onlisting
/ ;

szn_quarter_weights(szn,quarter) =
    sum{h$h_szn(h,szn), frac_h_quarter_weights(h,quarter) }
    / sum{h$h_szn(h,szn), 1} ;

szn_ccseason_weights(szn,ccseason) =
    sum{h$h_szn(h,szn), frac_h_ccseason_weights(h,ccseason) }
    / sum{h$h_szn(h,szn), 1} ;

hours_daily(h_rep) = %GSw_HourlyChunkLengthRep% ;
hours_daily(h_stress) = %GSw_HourlyChunkLengthStress% ;


*=============================================
* -- Climate, hydro, and water --
*=============================================
watsa(wst,r,szn,t)$[tmodel_new(t)$Sw_WaterMain] =
    sum{quarter,
        szn_quarter_weights(szn,quarter) * watsa_temp(wst,r,quarter) } ;

* update seasonal distribution factors for water sources other than fresh surface unappropriated
* and also fsu with missing data
watsa(wst,r,szn,t)$[(not sum{sznn, watsa(wst,r,sznn,t)})$tmodel_new(t)$Sw_WaterMain] = 
    round(numdays(szn)/365 , 2) ;


$ifthen.climatewater %GSw_ClimateWater% == 1

* Update seasonal distribution factors for fsu; other water types are unchanged
* declared over allt to allow for external data files that extend beyond end_year
* Written by climateprep.py
table watsa_climate(wst,r,allszn,allt)  "time-varying fractional seasonal allocation of water"
$offlisting
$ondelim
$include inputs_case%ds%climate_UnappWaterSeaAnnDistr.csv
$offdelim
$onlisting
;
* Use the sparse assignment $= to make sure we don't assign zero to wst's not included in watsa_climate
watsa(wst,r,szn,t)$[wst_climate(wst)$r_country(r,"USA")$tmodel_new(t)$Sw_WaterMain$(yeart(t)>=Sw_ClimateStartYear)] $=
  sum{allt$att(allt,t), watsa_climate(wst,r,szn,allt) };
* If wst is in wst_climate but does not have data in input file, assign its multiplier to the fsu multiplier
watsa(wst,r,szn,t)$[wst_climate(wst)$r_country(r,"USA")$tmodel_new(t)$Sw_WaterMain$(yeart(t)>=Sw_ClimateStartYear)$sum{allt$att(allt,t), (not watsa_climate(wst,r,szn,allt)) }] $=
  sum{allt$att(allt,t), watsa_climate('fsu',r,szn,allt) };

$endif.climatewater

trans_cap_delta(h,t) =
    climate_heuristics_finalyear('trans_summer_cap_delta') * climate_heuristics_yearfrac(t)
    * sum{quarter$sameas(quarter,"summ"), frac_h_quarter_weights(h,quarter) }
;



*=============================================
* -- Mexico and Canada --
*=============================================
$ifthene.Canada %GSw_Canada% == 1
parameter can_imports_szn_frac(allszn) "--unitless-- [Sw_Canada=1] fraction of annual imports that occur in each season"
/
$offlisting
$ondelim
$include inputs_case%ds%can_imports_szn_frac.csv
$offdelim
$onlisting
/ ;

parameter can_exports_h_frac(allh) "--unitless-- [Sw_Canada=1] fraction of annual exports by timeslice"
/
$offlisting
$ondelim
$include inputs_case%ds%can_exports_h_frac.csv
$offdelim
$onlisting
/ ;

can_imports_szn(r,szn,t) = can_imports(r,t) * can_imports_szn_frac(szn) ;
can_exports_h(r,h,t)$[hours(h)] = can_exports(r,t) * can_exports_h_frac(h) / hours(h) ;

$endif.Canada


$onempty
parameter canmexload(r,allh) "load for canadian and mexican regions"
/
$offlisting
$ondelim
$include inputs_case%ds%canmexload.csv
$offdelim
$onlisting
/ ;
$offempty


*=============================================
* -- Air quality policies --
*=============================================
h_weight_csapr(h) =
    sum{quarter, frac_h_quarter_weights(h,quarter) * quarter_weight_csapr(quarter) } ;



*=============================================
* -- Availability (forced and planned outages) --
*=============================================
parameter forcedoutage_h(i,r,allh) "--fraction-- forced outage rate"
/
$offlisting
$ondelim
$include inputs_case%ds%forcedoutage_h.csv
$include inputs_case%ds%stress%stress_year%%ds%forcedoutage_h.csv
$offdelim
$onlisting
/ ;

* Infer some forced outage rates from parent techs
forcedoutage_h(i,r,h)$pvb(i) = forcedoutage_h("battery_%GSw_pvb_dur%",r,h) ;
forcedoutage_h(i,r,h)$geo(i) = forcedoutage_h("geothermal",r,h) ;

* Upgrade plants assume the same forced outage rate as what they're upgraded to
forcedoutage_h(i,r,h)$upgrade(i) = sum{ii$upgrade_to(i,ii), forcedoutage_h(ii,r,h) } ;

forcedoutage_h(i,r,h)$[i_water_cooling(i)$Sw_WaterMain] =
    sum{ii$ctt_i_ii(i,ii), forcedoutage_h(ii,r,h) } ;

* Calculate availability (includes forced and planned outage rates)
avail(i,r,h)$valcap_i(i) = 1 ;

* For rep periods, assume no planned outages in the summer, and adjust the planned outages
* to account for no planned outages in summer
avail(i,r,h)$[valcap_i(i)$(forcedoutage_h(i,r,h) or planned_outage(i))$h_rep(h)] =
    (1 - forcedoutage_h(i,r,h))
    * (1 - planned_outage(i)
           * sum{quarter$[not sameas(quarter,"summ")], frac_h_quarter_weights(h,quarter) }
           * 365 / 273) ;

* For stress periods, only apply forced outages
avail(i,r,h)$[valcap_i(i)$forcedoutage_h(i,r,h)$h_stress(h)] =
    (1 - forcedoutage_h(i,r,h)) ;

*upgrade plants assume the same availability of what they are upgraded to
avail(i,r,h)$[upgrade(i)$valcap_i(i)] = sum{ii$upgrade_to(i,ii), avail(ii,r,h) } ;

* In  eq_reserve_margin, thermal outages are captured through the PRM rather than through
* forced/planned outages. If GSw_PRM_StressOutages is not true,
* set the availability of thermal generator to 1 during stress periods.
avail(i,r,h)
    $[h_stress(h)$valcap_i(i)$(Sw_PRM_StressOutages=0)
    $(not vre(i))$(not hydro(i))$(not storage(i))$(not dr(i))$(not consume(i))
    ] = 1 ;

* Geothermal is currently the only tech where derate_geo_vintage(i,v) != 1.
* If other techs with a non-unity vintage-dependent derate are added, avail(i,r,h) may need to be
* multiplied by derate_geo_vintage(i,v) in additional locations throughout the model.
* Divide by (1 - outage rate) (i.e. avail) since geothermal_availability is defined
* as the total product of derate_geo_vintage(i,v) * avail(i,r,h).
derate_geo_vintage(i,initv)$[geo(i)$valcap_iv(i,initv)] =
    geothermal_availability
    / (sum{(r,h), avail(i,r,h) * hours(h) }
       / sum{(r,h), hours(h) }) ;

seas_cap_frac_delta(i,v,r,szn,t) =
    sum{quarter, szn_quarter_weights(szn,quarter) * quarter_cap_frac_delta(i,v,r,quarter,t) } ;



*=============================================
* -- Hydrogen --
*=============================================
* assign hydrogen demand by region and timeslice
* we assumed demand is flat, i.e., timeslices w/ more hours 
* have more demand in metric tons but the same rate in metric tons/hour
h2_exogenous_demand_regional(r,p,h,t)$[tmodel_new(t)]
    = h2_share(r,t) * h2_exogenous_demand(p,t) / 8760 ;


*=============================================
* -- Capacity factor --
*=============================================
* Written by cfgather.py, overwritten by hourly_writetimeseries.py
parameter cf_in(i,r,allh) "--fraction-- capacity factors for renewable technologies"
/
$offlisting
$ondelim
$include inputs_case%ds%cf_vre.csv
$include inputs_case%ds%stress%stress_year%%ds%cf_vre.csv
$offdelim
$onlisting
/ ;

cf_in(i,r,h)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), cf_in(ii,r,h) } ;

*initial assignment of capacity factors
*Note that DUPV does not face the same distribution losses as UPV
*The DUPV capacity factors have already been adjusted by (1.0 - distloss)
cf_rsc(i,v,r,h,t)$[cf_in(i,r,h)$cf_tech(i)$valcap(i,v,r,t)] = cf_in(i,r,h) ;

* Written by input_processing/hourly_writetimeseries.py
parameter cf_hyd(i,allszn,r,allt) "--fraction-- hydro capacity factors by season and year"
/
$offlisting
$ondelim
$include inputs_case%ds%cf_hyd.csv
$include inputs_case%ds%stress%stress_year%%ds%cf_hyd.csv
$offdelim
$onlisting
/ ;

$ifthen.climatehydro %GSw_ClimateHydro% == 1

* declared over allt to allow for external data files that extend beyond end_year
* Written by climateprep.py
table climate_hydro_annual(r,allt)  "annual dispatchable hydropower availability"
$offlisting
$ondelim
$include inputs_case%ds%climate_hydadjann.csv
$offdelim
$onlisting
;

* Written by climateprep.py
table climate_hydro_seasonal(r,allszn,allt)  "annual/seasonal nondispatchable hydropower availability"
$offlisting
$ondelim
$include inputs_case%ds%climate_hydadjsea.csv
$offdelim
$onlisting
;

* adjust cf_hyd based on annual/seasonal climate multipliers
* non-dispatchable hydro gets new seasonal profiles as well as annually-varying CF
* dispatchable hydro keeps the original seasonal profiles; only annual CF changes. Reflects the assumption
* that reservoirs will be utilized in the same seasonal pattern even if seasonal inflows change.
cf_hyd(i,szn,r,t)$[hydro_nd(i)$(yeart(t)>=Sw_ClimateStartYear)] =
    sum{allt$att(allt,t), cf_hyd(i,szn,r,t) * climate_hydro_seasonal(r,szn,allt) } ;

cf_hyd(i,szn,r,t)$[hydro_d(i)$(yeart(t)>=Sw_ClimateStartYear)]  =
    sum{allt$att(allt,t), cf_hyd(i,szn,r,t) * climate_hydro_annual(r,allt) } ;

$endif.climatehydro

*created by /input_processing/writecapdat.py
parameter cap_hyd_szn_adj(i,allszn,r) "--fraction-- seasonal max capacity adjustment for dispatchable hydro"
/
$offlisting
$ondelim
$include inputs_case%ds%cap_hyd_szn_adj.csv
$include inputs_case%ds%stress%stress_year%%ds%cap_hyd_szn_adj.csv
$offdelim
$onlisting
/ ;



* dispatchable hydro has a separate constraint for seasonal generation which uses m_cf_szn
cf_rsc(i,v,r,h,t)$[hydro(i)$valcap(i,v,r,t)] = sum{szn$h_szn(h,szn), cf_hyd(i,szn,r,t) } ;

cf_rsc(i,v,r,h,t)$[rsc_i(i)$(sum{tt, capacity_exog(i,v,r,tt) })] =
        cf_rsc(i,"init-1",r,h,t) ;

*Upgraded hydro parameters:
* By default, capacity factors for upgraded hydro techs use what we upgraded from.
cf_hyd(i,szn,r,t)$[upgrade(i)$(hydro(i) or psh(i))] =
    sum{ii$upgrade_from(i,ii), cf_hyd(ii,szn,r,t) } ;
* For cap_hyd_szn_adj, which only applies to dispatchable hydro or upgraded disp hydro with added pumping, we first try using the from-tech, but if that is
* not available we use to to-tech, and if not that either we just use 1.
cap_hyd_szn_adj(i,szn,r)$[upgrade(i)$(hydro_d(i) or psh(i))] =
    sum{ii$upgrade_from(i,ii), cap_hyd_szn_adj(ii,szn,r) } ;
cap_hyd_szn_adj(i,szn,r)$[upgrade(i)$hydro_d(i)$(not cap_hyd_szn_adj(i,szn,r))] =
    sum{ii$upgrade_to(i,ii), cap_hyd_szn_adj(ii,szn,r) } ;
cap_hyd_szn_adj(i,szn,r)$[upgrade(i)$hydro_d(i)$(not cap_hyd_szn_adj(i,szn,r))] = 1 ;


* do not apply "avail" for hybrid PV+battery because "avail" represents the battery availability
m_cf(i,v,r,h,t)$[cf_tech(i)$valcap(i,v,r,t)] =
    cf_rsc(i,v,r,h,t)
    * cf_adj_t(i,v,t)
    * (avail(i,r,h)$[not pvb(i)] + 1$pvb(i)) ;

* can remove capacity factors for new vintages that have not been introduced yet
m_cf(i,newv,r,h,t)$[not sum{tt$(yeart(tt) <= yeart(t)), ivt(i,newv,tt ) }$valcap(i,newv,r,t)] = 0 ;

* distpv capacity factor is divided by (1.0 - distloss) to provide a busbar equivalent capacity factor
m_cf(i,v,r,h,t)$[distpv(i)$valcap(i,v,r,t)] = m_cf(i,v,r,h,t) / (1.0 - distloss) ;

* doing this before calculating m_cf_szn to make sure 
* m_cf_szn does not get populated with very small values
m_cf(i,v,r,h,t)$[not valcap(i,v,r,t)] = 0 ;
m_cf(i,v,r,h,t)$[(m_cf(i,v,r,h,t)<0.01)$valcap(i,v,r,t)] = 0 ;
m_cf(i,v,r,h,t)$[cf_tech(i)$valcap(i,v,r,t)] = round(m_cf(i,v,r,h,t),3) ;

* Remove capacity when there is no corresponding capacity factor
m_capacity_exog(i,v,r,t)$[initv(v)$cf_tech(i)$(not sum{h, m_cf(i,v,r,h,t) })] = 0 ;

* Average CF by season
m_cf_szn(i,v,r,szn,t)$[cf_tech(i)$valcap(i,v,r,t)$(hydro_d(i) or hyd_add_pump(i))] =
    sum{h$h_szn(h,szn), hours(h) * m_cf(i,v,r,h,t) }
    / sum{h$h_szn(h,szn), hours(h) } ;

* adding upgrade techs for hydro
m_cf_szn(i,v,r,szn,t)
    $[cf_tech(i)$upgrade(i)$valcap(i,v,r,t)$(hydro_d(i) or psh(i))]
    = sum{ii$upgrade_from(i,ii), m_cf_szn(ii,v,r,szn,t) } ;

m_cf_szn(i,v,r,szn,t)
    $[cf_tech(i)$upgrade(i)$valcap(i,v,r,t)$hydro_d(i)$(not m_cf_szn(i,v,r,szn,t))]
    = sum{ii$upgrade_to(i,ii), m_cf_szn(ii,v,r,szn,t) } ;

m_cf_szn(i,v,r,szn,t)
    $[cf_tech(i)$upgrade(i)$valcap(i,v,r,t)$hydro_d(i)$(not m_cf_szn(i,v,r,szn,t))]
    = 1 ;

* Calculate daytime hours (for PVB) based on hours with nonzero PV CF
dayhours(h)$[sum{(i,v,r,t)$[pv(i)$valgen(i,v,r,t)], m_cf(i,v,r,h,t) }] = yes ;


*=============================================
* -- Operating reserves and minloading --
*=============================================
$onempty
set opres_periods(allszn) "Periods within which the operating reserve constraint applies"
/
$offlisting
$ondelim
$include inputs_case%ds%opres_periods.csv
$offdelim
$onlisting
/ ;
$offempty

opres_h(h) = sum{szn$opres_periods(szn), h_szn(h,szn) } ;


set hour_szn_group(allh,allhh) "h and hh in the same season - used in minloading constraint"
/
$offlisting
$ondelim
$include inputs_case%ds%hour_szn_group.csv
$offdelim
$onlisting
/ ;

*reducing problem size by removing h-hh combos that are the same
hour_szn_group(h,hh)$sameas(h,hh) = no ;

hydmin(i,r,szn) = round(sum{quarter, szn_quarter_weights(szn,quarter) * hydmin_quarter(i,r,quarter) }, 3) ;

minloadfrac(r,i,h) = minloadfrac0(i) ;

* adjust nuclear mingen to minloadfrac_nuclear_flex if running with flexible nuclear
minloadfrac(r,i,h)$[nuclear(i)$Sw_NukeFlex] = minloadfrac_nuclear_flex ;
* CSP and coal use user inputs
minloadfrac(r,i,h)$csp(i) = minloadfrac_csp ;
minloadfrac(r,i,h)$[coal(i)$(not minloadfrac(r,i,h))] = minloadfrac_coal ;
*set seasonal values for minloadfrac for hydro techs
minloadfrac(r,i,h)$[sum{szn$h_szn(h,szn), hydmin(i,r,szn ) }] =
    sum{szn$h_szn(h,szn), hydmin(i,r,szn) } ;
*upgrade techs get their corresponding upgraded-to minloadfracs
minloadfrac(r,i,h)$upgrade(i) = sum{ii$upgrade_to(i,ii), minloadfrac(r,ii,h) } ;
*water tech assignment
minloadfrac(r,i,h)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), minloadfrac(r,ii,h) } ;
*remove minloadfrac for non-viable generators
minloadfrac(r,i,h)$[not sum{(v,t), valcap(i,v,r,t) }] = 0 ;

*reduced set of minloading constraints and mingen contributors
minloadfrac(r,i,h)$[(Sw_MinLoadTechs=0)] = 0 ;
minloadfrac(r,i,h)$[(Sw_MinLoadTechs=2)$(geo(i) or csp(i) or lfill(i))] = 0 ;
minloadfrac(r,i,h)$[(Sw_MinLoadTechs=3)$(not nuclear(i))$(not hydro(i))] = 0 ;
minloadfrac(r,i,h)$[(Sw_MinLoadTechs=4)$(not boiler(i))$(not hydro(i))] = 0 ;



*=============================================
* -- Electricity demand --
*=============================================

* Flexible demand
$onempty
parameter flex_frac_load(flex_type,r,allh,allt)
/
$offlisting
$ondelim
$include inputs_case%ds%flex_frac_all.csv
$offdelim
$onlisting
/ ;

* Demand response
parameter allowed_shifts(i,allh,allh) "how much load each dr type is allowed to shift into h from hh"
/
$offlisting
$ondelim
$include inputs_case%ds%dr_shifts.csv
$offdelim
$onlisting
/ ;

parameter dr_increase(i,r,allh) "--unitless-- average capacity factor for dr reduction in load in timeslice h"
/
$offlisting
$ondelim
$include inputs_case%ds%dr_increase.csv
$offdelim
$onlisting
/ ;

parameter dr_decrease(i,r,allh) "--unitless-- average capacity factor for dr increase in load in timeslice h"
/
$offlisting
$ondelim
$include inputs_case%ds%dr_decrease.csv
$offdelim
$onlisting
/ ;

* EV adoptable managed charging

parameter evmc_baseline_load(r,allh,allt) "--fraction-- how much adopted shaped EV load is allowed to be shed in each timeslice h"
/
$offlisting
$ondelim
$include inputs_case%ds%evmc_baseline_load.csv
$offdelim
$onlisting
/ ;

parameter evmc_shape_gen(i,r,allh) "--fraction-- how much adopted shaped EV load is allowed to be shed in each timeslice h"
/
$offlisting
$ondelim
$include inputs_case%ds%evmc_shape_generation.csv
$offdelim
$onlisting
/ ;

parameter evmc_shape_load(i,r,allh) "--fraction-- how much adopted shaped EV load is added in each timeslice h"
/
$offlisting
$ondelim
$include inputs_case%ds%evmc_shape_load.csv
$offdelim
$onlisting
/ ;

parameter evmc_storage_discharge_frac(i,r,allh,allt) "--fraction-- fraction of adopted EV storage discharge capacity that can be discharged (deferred charging) in each timeslice h"
/
$offlisting
$ondelim
$include inputs_case%ds%evmc_storage_discharge.csv
$offdelim
$onlisting
/ ;

parameter evmc_storage_charge_frac(i,r,allh,allt) "--fraction-- fraction of adopted EV storage discharge capacity that can be charged (add back deferred charging) in each timeslice h"
/
$offlisting
$ondelim
$include inputs_case%ds%evmc_storage_charge.csv
$offdelim
$onlisting
/ ;

parameter evmc_storage_energy_hours(i,r,allh,allt) "--hours-- Allowable EV storage SOC (quantity deferred EV charge) [MWh] divided by nameplate EVMC discharge capacity [MW]"
/
$offlisting
$ondelim
$include inputs_case%ds%evmc_storage_energy.csv
$offdelim
$onlisting
/ ;
$offempty

* Written by hourly_writetimeseries.py
parameter load_allyear(r,allh,allt) "--MW-- end-use load by region, timeslice, and year"
/ 
$offlisting
$ondelim
$include inputs_case%ds%load_allyear.csv
$include inputs_case%ds%stress%stress_year%%ds%load_allyear.csv
$offdelim
$onlisting
/ ;
* Dividing by (1-distloss) converts end-use load to busbar load
load_exog(r,h,t) = load_allyear(r,h,t) / (1.0 - distloss) ;

* Stress-period load is scaled up by PRM
load_exog(r,h,t)$h_stress(h) = load_exog(r,h,t) * (1 + prm(r,t)) ;

* first define mexican growth load then replace canadian with
* province-specific growth factors
load_exog(r,h,t)$canmexload(r,h) = mex_growth_rate(t) * canmexload(r,h) ;

load_exog(r,h,t)$sum{st$r_st(r,st),can_growth_rate(st,t) } =
      canmexload(r,h) * sum{st$r_st(r,st),can_growth_rate(st,t) } ;

* Flexible load doesn't yet work with hourly resolution
flex_h_corr1(flex_type,allh,allh) = no ;
flex_h_corr2(flex_type,allh,allh) = no ;

* assign zero values to avoid unassigned parameter errors
flex_demand_frac(flex_type,r,h,t) = 0 ;
flex_demand_frac(flex_type,r,h,t)$Sw_EFS_Flex = flex_frac_load(flex_type,r,h,t) ;

*initial values are set here (after SwI_Load has been accounted for)
load_exog0(r,h,t) = load_exog(r,h,t) ;


load_exog_flex(flex_type,r,h,t) = load_exog(r,h,t) * flex_demand_frac(flex_type,r,h,t) ;
load_exog_static(r,h,t) = load_exog(r,h,t) - sum{flex_type, load_exog_flex(flex_type,r,h,t) } ;



set maxload_szn(r,allh,t,allszn)   "hour with highest load within each szn" ;

maxload_szn(r,h,t,szn)
    $[(smax(hh$[h_szn(hh,szn)], load_exog_static(r,hh,t))
       = load_exog_static(r,h,t))
    $h_szn(h,szn)$Sw_OpRes] = yes ;



set h_ccseason_prm(allh,ccseason) "peak-load hour for the entire modeled system by ccseason"
/
$offlisting
$ondelim
$include inputs_case%ds%h_ccseason_prm.csv
$offdelim
$onlisting
/ ;

peak_static_frac(r,ccseason,t) = 1 - sum{(flex_type,h)$h_ccseason_prm(h,ccseason), flex_demand_frac(flex_type,r,h,t) } ;



* Written by hourly_writetimeseries.py
parameter peak_ccseason(r,ccseason,allt) "--MW-- end-use peak demand by region, season, year"
/
$offlisting
$ondelim
$include inputs_case%ds%peak_ccseason.csv
$offdelim
$onlisting
/ ;
*Dividing by (1-distloss) converts end-use load to busbar load
peakdem_static_ccseason(r,ccseason,t) = peak_ccseason(r,ccseason,t) * peak_static_frac(r,ccseason,t) / (1.0 - distloss) ;


$onempty
parameter peak_h(r,allh,allt) "--MW-- busbar peak demand by timeslice"
/
$offlisting
$ondelim
$include inputs_case%ds%peak_h.csv
$offdelim
$onlisting
/ ;
$offempty

peakdem_static_h(r,h,t) = peak_h(r,h,t) * (1 - sum{flex_type, flex_demand_frac(flex_type,r,h,t) }) / (1.0 - distloss) ;



*=============================================
* -- Fossil gas supply curve --
*=============================================
gasadder_cd(cendiv,t,h) = (gasprice_ref(cendiv,t) - gasprice_nat(t))/2 ;

*winter gas gets marked up
gasadder_cd(cendiv,t,h) =
    gasadder_cd(cendiv,t,h)
    + gasprice_ref_frac_adder * frac_h_quarter_weights(h,"wint") * gasprice_ref(cendiv,t) ;


szn_adj_gas(h) = 1 ;

szn_adj_gas(h)$frac_h_quarter_weights(h,"wint") =
    szn_adj_gas(h) + frac_h_quarter_weights(h,"wint") * szn_adj_gas_winter ;

*=============================================
* -- Round parameters for GAMS --
*=============================================
avail(i,r,h)$avail(i,r,h) = round(avail(i,r,h),3) ;
can_exports_h(r,h,t)$can_exports_h(r,h,t) = round(can_exports_h(r,h,t),3) ;
h_weight_csapr(h)$h_weight_csapr(h) = round(h_weight_csapr(h),3) ;
load_exog(r,h,t)$load_exog(r,h,t) = round(load_exog(r,h,t),3) ;
load_exog_static(r,h,t)$load_exog_static(r,h,t) = round(load_exog_static(r,h,t),3) ;
minloadfrac(r,i,h)$minloadfrac(r,i,h) = round(minloadfrac(r,i,h),3) ;
szn_adj_gas(h)$szn_adj_gas(h) = round(szn_adj_gas(h), 3) ;
cap_hyd_szn_adj(i,szn,r)$cap_hyd_szn_adj(i,szn,r) = round(cap_hyd_szn_adj(i,szn,r),3) ;
peakdem_static_ccseason(r,ccseason,t)$peakdem_static_ccseason(r,ccseason,t) = round(peakdem_static_ccseason(r,ccseason,t),2) ;
seas_cap_frac_delta(i,v,r,szn,t)$seas_cap_frac_delta(i,v,r,szn,t) = round(seas_cap_frac_delta(i,v,r,szn,t),3) ;


* Write the inputs for debugging purposes
$ifthene.write %cur_year% == 2010
execute_unload 'inputs_case%ds%inputs.gdx' ;
$endif.write
