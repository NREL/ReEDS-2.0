$title 'Optimize Transmission Flows and Storage Dispatch'

*Setting the default directory separator
$setglobal ds \

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$eolcom \\

* --- supress .lst file printing ---
* equations listed per block
option limrow = 0 ;
* variables listed per block
option limcol = 0 ;
* solver's solution output printed
option solprint = off ;
* solver's system output printed
option sysout = off ;

option profile = 3
option profiletol = 0

*========================
* ---- Model Options ----
*========================

scalar
Sw_MRGen        "switch to set must run generators" / 1 /
Sw_MinGen       "switch to turn on min-gen constraint" / 0 /
Sw_StartCost    "switch to turn on start costs" / 0 /
Sw_Stor         "switch to turn on storage" / 1 /
Sw_Solve        "switch to choose solve method, 1 is loop, 2 is GUSS" / 2 /
Sw_Energy_Level "starting fraction of storage energy level, 1 is full, 0 is empty" / 0.5 /
Sw_Hydro        "switch to turn on/off hydro representation (1 = ReEDS, 0 = PLEXOS)" / 1 /
;

*========================
* -- Set Declarations --
*========================

set i, v, r, szn, routes, storage_no_csp, hydro_d, hydro_nd, canada, coal, geo, nuclear ;

*Load sets from ReEDS
$gdxin ReEDS_Augur%ds%augur_data%ds%reeds_data_%case%_%next_year%.gdx
$loadr i
$loadr v
$loadr r
$loadr szn
$loadr storage_no_csp
$loadr hydro_d
$loadr hydro_nd
$loadr canada
$loadr coal
$loadr geo
$loadr nuclear
$gdxin

set hr_all    "hours in a 48-hour horizon" / hr1*hr48 /,
    hr(hr_all) "hours in a 24-hour horizon" / hr1*hr24 /,
    d        "day"  / d1*d365 /
;


alias (hr,hh) ;

set nexth(hr,hh) "next hour"
    priorh(hr,hh) "previous hour" ;

nexth(hr,hh)$(ord(hr) = ord(hh)-1) = yes ;
nexth(hr,hh)$[(ord(hr) = card(hr))$(ord(hh) = 1)] = yes ;

priorh(hr,hh)$(ord(hr) = ord(hh)+1) = yes ;
priorh(hr,hh)$[(ord(hh) = card(hh))$(ord(hr) = 1)] = yes ;

set d_szn(d,szn) "mapping of days to seasons" /
$offlisting
$ondelim
$include inputs_case%ds%d_szn.csv
$offdelim
$onlisting
/ ;

set mustrun(i) "mustrun technologies" ;

alias (r, rr) ;





*==============================
* -- Parameter Declarations --
*==============================


parameters cost(i,v,r)           "--$/MWh-- total variable generation costs (fuel + VOM)",
           cap_max_in(i,v,r)     "--MW-- maximum generator capacity",
           gen_low(d,hr,i,v,r)    "--MW-- minimum generation level"
           cap_trans(r,rr)       "--MW-- transmission line capacities",
           avail(i,v,r,szn)      "--fraction-- fraction of capacity available"
           mingenfrac(i,r,szn)   "--fraction-- minimum generation level as a fraction of maximum capacity",
           start_cost(i)         "--$/MW-- start up costs",
           storage_energy(i,v,r) "--MWh-- energy capacity of storage resources",
           storage_eff(i)        "--fraction-- round-trip efficiency of storage technologies",
           tranloss(r,rr)        "--fraction-- factor of energy that is lost in moving powering from r to rr"
          ;

* Load values from ReEDS
$gdxin ReEDS_Augur%ds%augur_data%ds%osprey_inputs_%case%_%next_year%.gdx
$loadr cost = gen_cost
$loadr cap_max_in = cap
$loadr cap_trans = cap_trans
$loadr avail = avail
$loadr mingenfrac = mingen
$loadr start_cost = start_cost
$loadr storage_energy = energy_cap
$loadr storage_eff = storage_rte
$loadr routes = routes
$loadr tranloss = tranloss
$gdxin

Parameter cost_dropped_load "--$/MWh-- Cost for dropped load" ;
*Use the maximum cost and increase it by $1 so that it is always higher than the highest generator cost
cost_dropped_load = smax((i,v,r), cost(i,v,r) ) + 1 ;

Parameter cost_flow "--$/MW-- Cost for using transmission lines" ;
*This small value is used to reduce degeneracy in where curtailment occurs
cost_flow = 0.001 ;

Table net_load_in(d,hr_all,r) "--MW-- Net load for 48-hour horizon"
$offlisting
$ondelim
$include ReEDS_Augur%ds%augur_data%ds%net_load_osprey_%case%_%next_year%.csv
$offdelim
$onlisting
;

Parameter net_load(hr,r)       "--MW-- Net load for a given day"
          net_load_day(d,hr,r) "--MW-- Net load for 24-hour horizon"

;

net_load_day(d,hr,r) = net_load_in(d,hr,r) ;

Parameter avail_day(d,i,v,r) "--unitless-- availability factor by day" ;

avail_day(d,i,v,r) = sum{szn$d_szn(d,szn), avail(i,v,r,szn) } ;

Parameter cap_max_model(d,i,v,r) "--MW-- Maximum generator capacity (indexed by d)"
          hydro_gen_day(d,r)     "--MWh-- Daily generation required from hydro to meet seasonal generation level"
          hydro_gen(r)           "--MWh-- Daily generation required from hydro for a single day"
          hydro_gen_feas(r)      "--MWh-- filter for feasible regions where hydro generation constraint should be applied"
;

* Initialize model capacity by the input capacity
cap_max_model(d,i,v,r) = cap_max_in(i,v,r) ;

* Specify mustrun generators - these generators will not be dispatched, rather their generation will be subtracted from the net load
mustrun(i)$[hydro_nd(i) or nuclear(i) or geo(i)] = yes ;

if(Sw_Hydro = 1,
* If not matching PLEXOS do not adjust down the maximum hydro capacity and set a lower bound for hydro generation
  cap_max_model(d,i,v,r)$[(not hydro_d(i))$(not sameas(i,"can-imports"))] = cap_max_in(i,v,r) * avail_day(d,i,v,r) ;

* Some hydro units have avail > 1, so for these units increase the capacity and set avail_day = 1
  cap_max_model(d,i,v,r)$[hydro_d(i)$(avail_day(d,i,v,r)>1)] = cap_max_in(i,v,r) * avail_day(d,i,v,r) ;
  avail_day(d,i,v,r)$[hydro_d(i)$(avail_day(d,i,v,r)>1)] = 1 ;

* Set a lower bound on generation from dispatchable hydro
  gen_low(d,hr,i,v,r)$[(hydro_d(i) or sameas(i,"can-imports"))$cap_max_in(i,v,r)] = cap_max_model(d,i,v,r) * sum{szn$d_szn(d,szn), mingenfrac(i,r,szn) } ;

* Calculate the amount of energy that would be supplied by dispatchable hydro each day given the availability
  hydro_gen_day(d,r) = sum{(i,v)$[hydro_d(i) or sameas(i,"can-imports")], cap_max_in(i,v,r) * avail_day(d,i,v,r) * card(hr) } ;

* If the lower bound on generation would produce too much energy, then reduce the amount of energy in order to satisfy the constraint
  hydro_gen_day(d,r)$[sum{(hr,i,v), gen_low(d,hr,i,v,r) } > hydro_gen_day(d,r)] = sum{(hr,i,v), gen_low(d,hr,i,v,r) } ;

else
* To match hydro in PLEXOS, reduce the available capacity to be the an average level that must be taken
  cap_max_model(d,i,v,r) = cap_max_in(i,v,r) * avail_day(d,i,v,r) ;
  mustrun(i)$[hydro_d(i) or sameas(i,"can-imports")] = yes ;
) ;

Parameter cap_max(i,v,r) "--MW-- Maximum generator capacity (used in model)" ;

Parameter cap_max_feas(i,v,r) "--MW-- used to determine which regions have capacity" ;

if(Sw_Stor = 0,
  cap_max_model(d,i,v,r)$storage_no_csp(i) = 0 ;
) ;

* If mustrun generators are turned on, subtract the max capacity of the mustrun generators from the load and then set their capacity to zero.
if(Sw_MRGen = 1,
  net_load_day(d,hr,r) = net_load_day(d,hr,r) - sum{(i,v)$mustrun(i), cap_max_model(d,i,v,r) } ;
  cap_max_model(d,i,v,r)$mustrun(i) = 0 ;
) ;


* Initialize parameters
cap_max(i,v,r) = cap_max_model("d1",i,v,r) ;
cap_max_feas(i,v,r) = cap_max_model("d1",i,v,r) ;
net_load(hr,r) = net_load_day("d1",hr,r) ;
hydro_gen(r) = hydro_gen_day("d1",r) ;
hydro_gen_feas(r) = hydro_gen_day("d1",r) ;

* Add small cost for discharging storage in order to prevent degeneracy between storage losses and curtailment
* Use the same as used for cost_flow
cost(i,v,r)$[cap_max_feas(i,v,r)$storage_no_csp(i)$(cost(i,v,r) = 0)] = cost_flow ;

*=============================
* -- Variable Declarations --
*=============================

positive variables

GEN(hr,i,v,r)              "--MW-- Electricity generation in hour h"
STORAGE_IN(hr,i,v,r)       "--MW-- Energy going into storage in hour h"
STORAGE_LEVEL(hr,i,v,r)    "--MWh-- storage level in hour h"
FLOW(hr,r,rr)              "--MW-- Electricity flow on transmission lines in hour h"
DROPPED_LOAD(hr,r)         "--MW-- Dropped load"
ON(hr,i,v,r)               "--unitless-- on/off state of the generator"
TURNON(hr,i,v,r)           "--unitless-- amount of generator that was turned on"
TURNOFF(hr,i,v,r)          "--unitless-- amount of generator that was turned off"
;

* The variables are normally binary, but this formulation is for a relaxed MIP, so set the upper bound to 1
* and allow the binary variables to be continuous between 0 and 1
if(Sw_StartCost = 1,
ON.up(hr,i,v,r)$cap_max_feas(i,v,r) = 1 ;
TURNON.up(hr,i,v,r)$cap_max_feas(i,v,r) = 1 ;
TURNOFF.up(hr,i,v,r)$cap_max_feas(i,v,r) = 1 ;
) ;

* initialize the lower bound
GEN.lo(hr,i,v,r) = gen_low("d1",hr,i,v,r) ;

Variable Z "--$-- Objective function value" ;

*=============================
* -- Equation Declarations --
*=============================

Equation

* objective function calculation
 eq_ObjFn                     "--$-- Objective function calculation"

* other equations
 eq_gen_cap(hr,i,v,r)          "--MW-- Generation must not exceed max capacity"
 eq_flow_cap(hr,r,rr)          "--MW-- Transmission flows must not exceed max capacity"
 eq_load_balance(hr,r)         "--MW-- Load must be served"
 eq_hydro_balance(r)          "--MWh-- daily energy balance for hydropower resources"
 eq_mingen(hr,hh,i,v,r,szn)    "--MW-- mingen constraint"
 eq_mingen2(hr,i,v,r,szn)      "--MW-- mingen constraint for start costs"
 eq_on_off(hr,i,v,r)           "--unitless-- set the on/off state of each generator"
 eq_storage_level(hr,i,v,r)    "--MWh-- Storage level inventory balance from one time-slice to the next"
 eq_storage_duration(hr,i,v,r) "--MWh-- limit STORAGE_LEVEL based on hours of storage available"
;

eq_gen_cap(hr,i,v,r)$cap_max_feas(i,v,r)..

    GEN(hr,i,v,r) + STORAGE_IN(hr,i,v,r)$[storage_no_csp(i)$Sw_Stor]

    =l=

    cap_max(i,v,r) * (1$[not Sw_StartCost] + ON(hr,i,v,r)$Sw_StartCost)
;

eq_flow_cap(hr,r,rr)$routes(r,rr)..

    FLOW(hr,r,rr)

    =l=

    cap_trans(r,rr)
;

eq_load_balance(hr,r)..

    + sum{(i,v)$cap_max_feas(i,v,r), GEN(hr,i,v,r) }

    + sum{(rr)$routes(rr,r), (1-tranloss(rr,r)) * FLOW(hr,rr,r) }

    - sum{(rr)$routes(r,rr), FLOW(hr,r,rr) }

    - sum{(i,v)$[storage_no_csp(i)$cap_max_feas(i,v,r)$Sw_Stor], STORAGE_IN(hr,i,v,r) }

    + DROPPED_LOAD(hr,r)

    =g=

    net_load(hr,r)
;

eq_hydro_balance(r)$[hydro_gen_feas(r)$Sw_Hydro]..

   sum{(hr,i,v)$[(hydro_d(i) or sameas(i,"can-imports"))$cap_max_feas(i,v,r)], GEN(hr,i,v,r) }

   =e=

   hydro_gen(r)
;

* Note: The szn index here adn in eq_mingen2 should be removed because they can be handled
* in the d set
eq_mingen(hr,hh,i,v,r,szn)$[cap_max_feas(i,v,r)$mingenfrac(i,r,szn)$Sw_MinGen]..

    GEN(hr,i,v,r)

    =g=

    GEN(hh,i,v,r) * mingenfrac(i,r,szn)
;

eq_mingen2(hr,i,v,r,szn)$[cap_max_feas(i,v,r)$mingenfrac(i,r,szn)$Sw_StartCost]..

    GEN(hr,i,v,r)

    =g=

    cap_max(i,v,r) * mingenfrac(i,r,szn) * ON(hr,i,v,r)
;

eq_on_off(hr,i,v,r)$[cap_max_feas(i,v,r)$start_cost(i)$Sw_StartCost]..

    ON(hr,i,v,r)

    =e=

    sum{hh$[priorh(hr,hh)], ON(hh,i,v,r) }

    + TURNON(hr,i,v,r)

    - TURNOFF(hr,i,v,r)
;

eq_storage_level(hr,i,v,r)$[storage_no_csp(i)$cap_max_feas(i,v,r)$Sw_Stor]..

    sum{hh$[nexth(hr,hh)], STORAGE_LEVEL(hh,i,v,r) }

    =e=

    + STORAGE_LEVEL(hr,i,v,r)

    + storage_eff(i) * STORAGE_IN(hr,i,v,r)

    - GEN(hr,i,v,r)$[storage_no_csp(i)$cap_max_feas(i,v,r)]
;

eq_storage_duration(hr,i,v,r)$[storage_no_csp(i)$cap_max_feas(i,v,r)$Sw_Stor]..

    storage_energy(i,v,r)

    =g=

    STORAGE_LEVEL(hr,i,v,r)
;

eq_ObjFn..

    Z

    =e=

    + sum{(hr,i,v,r)$cap_max_feas(i,v,r),

          cost(i,v,r) * GEN(hr,i,v,r) }

    + sum{(hr,r), DROPPED_LOAD(hr,r) * cost_dropped_load }

    + sum{(hr,i,v,r)$cap_max_feas(i,v,r),

          start_cost(i) * cap_max(i,v,r) * TURNON(hr,i,v,r) }$Sw_StartCost

    + sum{(hr,r,rr)$routes(r,rr), cost_flow * FLOW(hr,r,rr) }

;

Model transmission /all/ ;

transmission.optfile = 1 ;
OPTION RESLIM = 500000 ;

*=============================
* ---- Output Parameters -----
*=============================

set h1(hr) "hours for the first day only" / hr1*hr24 / ;

Parameter prices(d,hr,r)                       "--$/MWh-- energy prices"
          prices_h1(d,h1,r)                   "--$/MWh-- energy prices for the first 24 hours only"
          flows_output(d,hr,r,rr)              "--MW-- transmission flows"
          flows_output_h1(d,h1,r,rr)          "--MW-- transmission flows for the first 24 hours only"
          gen_output(d,hr,i,v,r)               "--MW-- generation"
          gen_output_h1(d,h1,i,v,r)           "--MW-- generation for the first 24 hours only"
          storage_in_output(d,hr,i,v,r)        "--MW-- Energy going into storage"
          storage_in_output_h1(d,h1,i,v,r)    "--MW-- Energy going into storage for the first 24 hours only"
          storage_level_output(d,hr,i,v,r)     "--MWh-- storage level"
          storage_level_output_h1(d,h1,i,v,r) "--MWh-- storage level for the first 24 hours only"
          dropped_load_output(d,hr,r)          "--MW-- Dropped load"
          dropped_load_output_h1(d,h1,r)      "--MW-- Dropped load for the first 24 hours only"

*=============================
* ------- Loop Solution ------
*=============================
if(Sw_Solve = 1,
  Loop(d,
    net_load(hr,r) = net_load_day(d,hr,r) ;
    cap_max(i,v,r) = cap_max_model(d,i,v,r) ;
    hydro_gen(r) = hydro_gen_day(d,r) ;
    GEN.lo(hr,i,v,r) = gen_low(d,hr,i,v,r) ;
    Solve transmission using LP minimizing Z ;
    prices(d,hr,r) =  eq_load_balance.m(hr,r) ;
    flows_output(d,hr,r,rr)$routes(r,rr) = FLOW.l(hr,r,rr) ;
    gen_output(d,hr,i,v,r) = GEN.l(hr,i,v,r) ;
    storage_in_output(d,hr,i,v,r) = STORAGE_IN.l(hr,i,v,r) ;
    storage_level_output(d,hr,i,v,r) = STORAGE_LEVEL.l(hr,i,v,r) ;
    dropped_load_output(d,hr,r) = DROPPED_LOAD.l(hr,r) ;
  ) ;
) ;

*=============================
* ------- GUSS Solution ------
*=============================

set dict / d.                scenario.  ''
           net_load.         param.     net_load_day
           cap_max.          param.     cap_max_model
           hydro_gen.        param.     hydro_gen_day
           GEN.              lower.     gen_low
           eq_load_balance.  marginal.  prices
           FLOW.             level.     flows_output
           GEN.              level.     gen_output
           STORAGE_IN.       level.     storage_in_output
           STORAGE_LEVEL.    level.     storage_level_output
           DROPPED_LOAD.     level.     dropped_load_output
         / ;

if(Sw_Solve = 2,
  Solve transmission using LP minimizing Z scenario dict ;
) ;

prices_h1(d,h1,r) = prices(d,h1,r) ;
flows_output_h1(d,h1,r,rr) = flows_output(d,h1,r,rr) ;
gen_output_h1(d,h1,i,v,r) = gen_output(d,h1,i,v,r) ;
storage_in_output_h1(d,h1,i,v,r) = storage_in_output(d,h1,i,v,r) ;
storage_level_output_h1(d,h1,i,v,r) = storage_level_output(d,h1,i,v,r) ;
dropped_load_output_h1(d,h1,r) = dropped_load_output(d,h1,r) ;

execute_unload "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx", prices, flows_output, gen_output, storage_in_output,
                                                                 storage_level_output, dropped_load_output, net_load_day, cap_max_model
*                                                                 prices_h1, flows_output_h1, gen_output_h1,
*                                                                 storage_in_output_h1, storage_level_output_h1,
*                                                                 dropped_load_output_h1
;


