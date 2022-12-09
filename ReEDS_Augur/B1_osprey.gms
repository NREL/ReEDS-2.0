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
Sw_Solve        "switch to choose solve method: 1 is loop, 2 is GUSS, 3 is grid" / 3 /
Sw_DR           "switch to turn on dr" / 1 /
Sw_Energy_Level "starting fraction of storage energy level, 1 is full, 0 is empty" / 0.5 /
Sw_Hydro        "switch to turn on/off hydro representation (1 = ReEDS, 0 = PLEXOS)" / 1 /
;

*========================
* -- Set Declarations --
*========================

set i, v, r, rfeas, szn, routes, storage_standalone, dr1, dr2, hydro_d, hydro_nd, geo, nuclear ;

*Load sets from ReEDS
$gdxin ReEDS_Augur%ds%augur_data%ds%reeds_data_%prev_year%.gdx
$loadr i
$loadr v
$loadr r
$loadr rfeas
$loadr szn
$loadr dr1
$loadr dr2
$loadr storage_standalone
$loadr hydro_d
$loadr hydro_nd
$loadr geo
$loadr nuclear
$gdxin

set hr_all    "hours in a 48-hour horizon" / hr1*hr48 /
    hr(hr_all) "hours in a 24-hour horizon" / hr1*hr24 /
    d        "day"  / d1*d%osprey_num_days% /
    trtype "transmission type: AC includes everything except VSC" / AC, VSC /
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

alias (r, rr) ;
alias (trtype, intype, outtype) ;


set dr_h(i,hr,hh) "mapping of with hours DR technologies can shift between" /
$offlisting
$ondelim
$include inputs_case%ds%dr_shifts_augur.csv
$offdelim
$onlisting
/ ;

parameter dr_max_h(i) "maximum hours DR technologies can shed per day" /
$offlisting
$ondelim
$include inputs_case%ds%dr_shed_augur.csv
$offdelim
$onlisting
/ ;


*==============================
* -- Parameter Declarations --
*==============================


parameters cap_trans(r,rr,trtype)         "--MW-- transmission line capacities",
           gen_cost(i,v,r)                "--$/MWh-- total variable generation costs (fuel + VOM)",
           gen_low_hydro_day(d,hr,i,v,r)  "--MW-- minimum generation level for hydro"
           mingen(i,v,r,szn)              "--MW-- minimum generation level",
           start_cost(i)                  "--$/MW-- start up costs",
           storage_eff(i)                 "--fraction-- round-trip efficiency of storage technologies",
           storage_energy(i,v,r)          "--MWh-- energy capacity of storage resources",
           tranloss(r,rr,trtype)          "--fraction-- factor of energy that is lost in moving powering from r to rr"
           prod_load_in(d,r)              "--MWh-- daily demand for hydrogen production"
           prod_cap_in(d,r)               "--MW-- capacity for production activities"
           dr_cf_dec(hr,i,v,r)            "--fraction-- fraction of DR capacity that can be decreased"
           dr_cf_inc(hr,i,v,r)            "--fraction-- fraction of DR capacity that can be increased"
           top_hours_day(d,hr,i,r)        "--one or zero-- allowed top hours for generation by technology"
           cap_converter(r)               "--MW-- VSC AC/DC converter capacity"
           converter_efficiency_vsc       "--fraction-- VSC AC/DC converter efficiency"
           Sw_VSC                         "Switch to turn on/off the multi-terminal VSC HVDC macrogrid"
          ;


* Load values from ReEDS
$gdxin ReEDS_Augur%ds%augur_data%ds%osprey_inputs_%prev_year%.gdx
$loadr cap_trans = trancap
$loadr gen_cost = gen_cost
$loadr mingen = mingen
$loadr routes = routes
$loadr start_cost = startup_costs
$loadr storage_eff = storage_eff
$loadr storage_energy = energy_cap
$loadr tranloss = tranloss
$loadr prod_load_in = prod_load
$loadr prod_cap_in = cap_prod
$loadr top_hours_day = top_hours_day
$loadr cap_converter = cap_converter
$loadr converter_efficiency_vsc = converter_efficiency_vsc
$loadr Sw_VSC = Sw_VSC
$gdxin

Parameter cost_flow "--$/MW-- Cost for using transmission lines" ;
*This small value is used to reduce degeneracy in where curtailment occurs
cost_flow = 0.001 ;

Table cap_in(i,v,r,d) "--MW-- Available capacity for each day"
$offlisting
$ondelim
$include ReEDS_Augur%ds%augur_data%ds%avail_cap_d_%prev_year%.csv
$offdelim
$onlisting
;

$onempty
Parameter energy_budget_in(i,v,r,d) "--MWh-- Energy budget for dispatchable hydro and hybrid resources"
/
$offlisting
$ondelim
$include ReEDS_Augur%ds%augur_data%ds%daily_energy_budget_%prev_year%.csv
$offdelim
$onlisting
/ ;
$offempty

Table net_load_in(d,hr_all,r) "--MW-- Net load for 48-hour horizon"
$offlisting
$ondelim
$include ReEDS_Augur%ds%augur_data%ds%net_load_osprey_%prev_year%.csv
$offdelim
$onlisting
;

Parameter cap(i,v,r)                       "--MW-- Available capacity"
          cap_day(d,i,v,r)                 "--MW-- Available capacity for each day"
          cap_feas(i,v,r)                  "--MW-- Filter instances where available capacity applies"
          dr_cf_inc_day(d,hr,i,v,r)        "--fraction-- fraction of DR capacity that can be increased"
          dr_cf_dec_day(d,hr,i,v,r)        "--fraction-- fraction of DR capacity that can be decreased"
          energy_budget(i,v,r)             "--MWh-- Energy budget for dispatchable hydro and hybrid resources for a given day"
          energy_budget_day(d,i,v,r)       "--MWh-- Energy budget for dispatchable hydro and hybrid resources"
          energy_budget_feas(i,v,r)        "--MW-- Filter instances where energy budget applies"
          net_load(hr,r)                   "--MW-- Net load for a given day"
          net_load_day(d,hr,r)             "--MW-- Net load for 24-hour horizon"

;

cap_day(d,i,v,r) = cap_in(i,v,r,d) ;
energy_budget_day(d,i,v,r) = energy_budget_in(i,v,r,d) ;
gen_low_hydro_day(d,hr,i,v,r)$[hydro_d(i) or sameas(i,"can-imports")] = sum{szn$d_szn(d,szn), mingen(i,v,r,szn) } ;
net_load_day(d,hr,r) = net_load_in(d,hr,r) ;

Parameter prod_load_day(d,r) "--MWh-- demand for production activities by day" ;

prod_load_day(d,r) = prod_load_in(d,r) ;

Parameter prod_cap(d,hr,r)   "--MW-- total electrolyzer capacity in each region" ;
* Initialize production capacity by the input capacity
prod_cap(d,hr,r) = prod_cap_in(d,r) ;

Parameter prod_load(r)     "--MWh-- demand for production (used in model)" ;

Table dr_cf_inc_in(d,hr_all,i,r) "--fraction-- fraction of DR capacity that can be increased"
$offlisting
$ondelim
$include ReEDS_Augur%ds%augur_data%ds%dr_inc_osprey_%prev_year%.csv
$offdelim
$onlisting
;

Table dr_cf_dec_in(d,hr_all,i,r) "--fraction-- fraction of DR capacity that can be decreased"
$offlisting
$ondelim
$include ReEDS_Augur%ds%augur_data%ds%dr_dec_osprey_%prev_year%.csv
$offdelim
$onlisting
;


if(Sw_Stor = 0,
  cap_day(d,i,v,r)$storage_standalone(i) = 0 ;
) ;

if(Sw_DR = 0,
cap_day(d,i,v,r)$dr1(i) = 0 ;
cap_day(d,i,v,r)$dr2(i) = 0 ;
) ;

* Combine DR parameters for GUSS
dr_cf_inc_day(d,hr,i,v,r) = dr_cf_inc_in(d,hr,i,r) * cap_day(d,i,v,r) ;
dr_cf_dec_day(d,hr,i,v,r) = dr_cf_dec_in(d,hr,i,r) * cap_day(d,i,v,r) ;
dr_cf_dec_day(d,hr,i,v,r)$dr2(i) = dr_cf_dec_day(d,hr,i,v,r) * top_hours_day(d,hr,i,r) ;

* Initialize parameters
cap(i,v,r) = cap_day("d1",i,v,r) ;
cap_feas(i,v,r) = cap_day("d1",i,v,r) ;
net_load(hr,r) = net_load_day("d1",hr,r) ;
dr_cf_inc(hr,i,v,r) = dr_cf_inc_day("d1",hr,i,v,r) ;
dr_cf_dec(hr,i,v,r) = dr_cf_dec_day("d1",hr,i,v,r) ;
energy_budget(i,v,r) = energy_budget_day("d1",i,v,r) ;
energy_budget_feas(i,v,r) = energy_budget_day("d1",i,v,r) ;
prod_load(r) = prod_load_day("d1",r) ;

* Add small cost for discharging storage in order to prevent degeneracy between storage losses and curtailment
* Use the same as used for cost_flow
gen_cost(i,v,r)$[cap_feas(i,v,r)$storage_standalone(i)$(gen_cost(i,v,r) = 0)] = cost_flow ;

Parameter cost_dropped_load "--$/MWh-- Cost for dropped load" ;
*Use the maximum cost and increase it by $1 so that it is always higher than the highest generator cost
cost_dropped_load = smax((i,v,r)$cap_feas(i,v,r), gen_cost(i,v,r) ) + 1 ;

*=============================
* -- Variable Declarations --
*=============================

positive variables

GEN(hr,i,v,r)              "--MW-- Electricity generation in hour h"
PRODUCE(hr,r)              "--MW-- electricity generation for meeting production activities demand"
STORAGE_IN(hr,i,v,r)       "--MW-- Energy going into storage in hour h"
STORAGE_LEVEL(hr,i,v,r)    "--MWh-- storage level in hour h"
DR_SHIFT(hr,hh,i,v,r)      "--MW-- DR shifting energy from hour hh to hour h"
DR_SHED(hr,i,v,r)          "--MW-- DR shed energy from hour h"
FLOW(hr,r,rr,trtype)       "--MW-- Electricity flow on transmission lines in hour h"
CONVERSION(hr,r,intype,outtype) "--MW-- conversion of AC->DC_VSC or DC_VSC->AC"
DROPPED_LOAD(hr,r)         "--MW-- Dropped load"
ON(hr,i,v,r)               "--unitless-- on/off state of the generator"
TURNON(hr,i,v,r)           "--unitless-- amount of generator that was turned on"
TURNOFF(hr,i,v,r)          "--unitless-- amount of generator that was turned off"
;

* The variables are normally binary, but this formulation is for a relaxed MIP, so set the upper bound to 1
* and allow the binary variables to be continuous between 0 and 1
if(Sw_StartCost = 1,
  ON.up(hr,i,v,r)$cap_feas(i,v,r) = 1 ;
  TURNON.up(hr,i,v,r)$cap_feas(i,v,r) = 1 ;
  TURNOFF.up(hr,i,v,r)$cap_feas(i,v,r) = 1 ;
) ;

* initialize the lower bound
GEN.lo(hr,i,v,r)$gen_low_hydro_day("d1",hr,i,v,r) = gen_low_hydro_day("d1",hr,i,v,r) ;
PRODUCE.up(hr,r)$prod_cap("d1",hr,r) = prod_cap("d1",hr,r) ;

Variable Z "--$-- Objective function value" ;

*=============================
* -- Equation Declarations --
*=============================

Equation

* objective function calculation
 eq_ObjFn                          "--$-- Objective function calculation"

* other equations
 eq_daily_load_balance(r)          "--MWh-- daily production balance for H2 and DAC"
 eq_dr_max_shed(hr,i,v,r)          "--MWh-- allowed shed of load from DR"
 eq_dr_shed_hrs(i,v,r)             "--MWh-- maximum hours of shed from DR per day"
 eq_dr_max_decrease(hr,i,v,r)      "--MWh-- allowed decrease of load from DR"
 eq_dr_max_increase(hr,i,v,r)      "--MWh-- allowed increase of load from DR"
 eq_dr_gen(hr,i,v,r)               "--MWh-- Generation impact of DR"
 eq_energy_budget_balance(i,v,r)   "--MWh-- daily energy balance for hydropower resources"
 eq_flow_cap(hr,r,rr,trtype)       "--MW-- Transmission flows must not exceed max capacity"
 eq_gen_cap(hr,i,v,r)              "--MW-- Generation must not exceed max capacity"
 eq_load_balance(hr,r)             "--MW-- Load must be served"
 eq_mingen(hr,hh,i,v,r,szn)        "--MW-- mingen constraint"
 eq_mingen2(hr,i,v,r,szn)          "--MW-- mingen constraint for start costs"
 eq_on_off(hr,i,v,r)               "--unitless-- set the on/off state of each generator"
 eq_storage_duration(hr,i,v,r)     "--MWh-- limit STORAGE_LEVEL based on hours of storage available"
 eq_storage_level(hr,i,v,r)        "--MWh-- Storage level inventory balance from one time-slice to the next"
 eq_vsc_flow(hr,r)                 "--MW-- VSC DC power flow"
 eq_conversion_limit(hr,r)         "--MW-- AC/DC energy conversion is limited to converter capacity"
;

* --- Capacity limits ---
eq_gen_cap(hr,i,v,r)$cap_feas(i,v,r)..

    GEN(hr,i,v,r) + STORAGE_IN(hr,i,v,r)$[storage_standalone(i)$Sw_Stor]

    =l=

    cap(i,v,r) * (1$[not Sw_StartCost] + ON(hr,i,v,r)$Sw_StartCost)
;


eq_flow_cap(hr,r,rr,trtype)$routes(r,rr,trtype)..

    FLOW(hr,r,rr,trtype)

    =l=

    cap_trans(r,rr,trtype)
;


* --- Load balance ---
eq_load_balance(hr,r)$rfeas(r)..

    + sum{(i,v)$cap_feas(i,v,r), GEN(hr,i,v,r) }

    + sum{rr$routes(rr,r,"AC"), (1-tranloss(rr,r,"AC")) * FLOW(hr,rr,r,"AC") }
    - sum{rr$routes(r,rr,"AC"), FLOW(hr,r,rr,"AC") }

    + (CONVERSION(hr,r,"VSC","AC") * converter_efficiency_vsc)$[cap_converter(r)$Sw_VSC]
    - (CONVERSION(hr,r,"AC","VSC") / converter_efficiency_vsc)$[cap_converter(r)$Sw_VSC]

    - sum{(i,v)$[storage_standalone(i)$cap_feas(i,v,r)$Sw_Stor], STORAGE_IN(hr,i,v,r) }

    - sum{(i,v,hh)$[dr1(i)$cap_feas(i,v,r)$Sw_DR$dr_h(i,hr,hh)], DR_SHIFT(hr,hh,i,v,r) / storage_eff(i)}

    + DROPPED_LOAD(hr,r)

    =g=

    net_load(hr,r) + PRODUCE(hr,r)  
;


* --- VSC HVDC macrogrid ---
eq_vsc_flow(hr,r)$[rfeas(r)$Sw_VSC]..

* [plus] net VSC DC transmission with imports reduced by losses
    + sum{rr$routes(rr,r,"VSC"), (1-tranloss(rr,r,"VSC")) * FLOW(hr,rr,r,"VSC") }
    - sum{rr$routes(r,rr,"VSC"), FLOW(hr,r,rr,"VSC") }

* [plus] net VSC AC/DC conversion
    + (CONVERSION(hr,r,"AC","VSC") * converter_efficiency_vsc)$cap_converter(r)
    - (CONVERSION(hr,r,"VSC","AC") / converter_efficiency_vsc)$cap_converter(r)

    =e=

* no direct consumption of VSC
    0
;


eq_conversion_limit(hr,r)$[rfeas(r)$cap_converter(r)$Sw_VSC]..

    CONVERSION(hr,r,"AC","VSC") + CONVERSION(hr,r,"VSC","AC")

    =l=

    cap_converter(r)
;


* --- Hydrogen ---
eq_daily_load_balance(r)$rfeas(r)..

    sum{hr, PRODUCE(hr,r)   }
    
    =e=
    
    prod_load(r)
;


* --- Dispatchable hydro and hybrids ---
eq_energy_budget_balance(i,v,r)$[energy_budget_feas(i,v,r)]..

   sum{hr, GEN(hr,i,v,r) }

   =e=

   energy_budget(i,v,r)
;


* --- Minimum-generation level ---
* Note: The szn index here and in eq_mingen2 should be removed because they can be handled
* in the d set
eq_mingen(hr,hh,i,v,r,szn)$[cap_feas(i,v,r)$mingen(i,v,r,szn)$Sw_MinGen]..

    GEN(hr,i,v,r)

    =g=

    mingen(i,v,r,szn)
;


eq_mingen2(hr,i,v,r,szn)$[cap_feas(i,v,r)$mingen(i,v,r,szn)$Sw_StartCost]..

    GEN(hr,i,v,r)

    =g=

    mingen(i,v,r,szn) * ON(hr,i,v,r)
;


* --- Unit commitment ---
eq_on_off(hr,i,v,r)$[cap_feas(i,v,r)$start_cost(i)$Sw_StartCost]..

    ON(hr,i,v,r)

    =e=

    sum{hh$[priorh(hr,hh)], ON(hh,i,v,r) }

    + TURNON(hr,i,v,r)

    - TURNOFF(hr,i,v,r)
;


* --- Storage ---
eq_storage_level(hr,i,v,r)$[storage_standalone(i)$cap_feas(i,v,r)$Sw_Stor]..

    sum{hh$[nexth(hr,hh)], STORAGE_LEVEL(hh,i,v,r) }

    =e=

    + STORAGE_LEVEL(hr,i,v,r)

    + storage_eff(i) * STORAGE_IN(hr,i,v,r)

    - GEN(hr,i,v,r)$[storage_standalone(i)$cap_feas(i,v,r)]
;


eq_storage_duration(hr,i,v,r)$[storage_standalone(i)$cap_feas(i,v,r)$Sw_Stor]..

    storage_energy(i,v,r)

    =g=

    STORAGE_LEVEL(hr,i,v,r)
;

eq_dr_max_shed(hr,i,v,r)$[cap_feas(i,v,r)$dr2(i)$Sw_DR]..

    dr_cf_dec(hr,i,v,r)

    =g= 

    DR_SHED(hr,i,v,r) 
;

eq_dr_shed_hrs(i,v,r)$[cap_feas(i,v,r)$dr2(i)$Sw_DR]..

    dr_max_h(i)

    =g=

    sum{hr, DR_SHED(hr,i,v,r) / dr_cf_dec(hr,i,v,r) }
;

eq_dr_max_decrease(hr,i,v,r)$[cap_feas(i,v,r)$dr1(i)$Sw_DR]..

    dr_cf_dec(hr,i,v,r)

    =g= 

    sum{hh$dr_h(i,hh,hr), DR_SHIFT(hh,hr,i,v,r)} 
;

eq_dr_max_increase(hr,i,v,r)$[cap_feas(i,v,r)$dr1(i)$Sw_DR]..

    dr_cf_inc(hr,i,v,r)

    =g= 

    sum{hh$dr_h(i,hr,hh),DR_SHIFT(hr,hh,i,v,r) / storage_eff(i)}

;

eq_dr_gen(hr,i,v,r)$[cap_feas(i,v,r)$(dr1(i) or dr2(i))$Sw_DR]..

    sum{(hh)$dr_h(i,hh,hr), DR_SHIFT(hh,hr,i,v,r)}

    + DR_SHED(hr,i,v,r)$dr2(i)

    =e=

    GEN(hr,i,v,r)
;



* --------------------------
* --- Objective function ---
* --------------------------
eq_ObjFn..

    Z

    =e=

    + sum{(hr,i,v,r)$cap_feas(i,v,r),

          gen_cost(i,v,r) * GEN(hr,i,v,r) }

    + sum{(hr,r)$rfeas(r), DROPPED_LOAD(hr,r) * cost_dropped_load }

    + sum{(hr,i,v,r)$cap_feas(i,v,r),

          start_cost(i) * cap(i,v,r) * TURNON(hr,i,v,r) }$Sw_StartCost

    + sum{(hr,r,rr,trtype)$routes(r,rr,trtype), cost_flow * FLOW(hr,r,rr,trtype) }
;

* --------------------------
Model transmission /all/ ;

option lp=%solver%;

transmission.optfile = 1 ;
OPTION RESLIM = 500000 ;

*=============================
* ---- Output Parameters -----
*=============================

set h1(hr) "hours for the first day only" / hr1*hr24 / ;
 
Parameter prices(d,hr,r)                           "--$/MWh-- energy prices"
          prices_h1(d,h1,r)                        "--$/MWh-- energy prices for the first 24 hours only"
          flows_output(d,hr,r,rr,trtype)           "--MW-- transmission flows"
          flows_output_h1(d,h1,r,rr,trtype)        "--MW-- transmission flows for the first 24 hours only"
          gen_output(d,hr,i,v,r)                   "--MW-- generation"
          gen_output_h1(d,h1,i,v,r)                "--MW-- generation for the first 24 hours only"
          storage_in_output(d,hr,i,v,r)            "--MW-- Energy going into storage"
          storage_in_output_h1(d,h1,i,v,r)         "--MW-- Energy going into storage for the first 24 hours only"
          storage_level_output(d,hr,i,v,r)         "--MWh-- storage level"
          storage_level_output_h1(d,h1,i,v,r)      "--MWh-- storage level for the first 24 hours only"
          dr_shift_output(d,hr,hh,i,v,r)           "--MWh-- shifted load from hh to hr"
          dr_shed_output(d,hr,i,v,r)               "--MWh-- shed load from hr"
          dr_inc_output(d,hr,i,v,r)                "--MWh-- shifted load from hh to hr"
          dr_inc_output_h1(d,h1,i,v,r)             "--MWh-- shifted load from hh to hr for first 24 hours only"
          dropped_load_output(d,hr,r)              "--MW-- Dropped load"
          dropped_load_output_h1(d,h1,r)           "--MW-- Dropped load for the first 24 hours only"
          PRODUCE_output(d,hr,r)                   "--MW-- additional generation for the production of produce"
          PRODUCE_output_h1(d,h1,r)                "--MW-- additional generation for production for the first 24 hours only"
          CONVERSION_output(d,hr,r,intype,outtype) "--MW-- conversion of AC->DC_VSC or DC_VSC->AC"
          cf_output(i,r)                           "--fraction-- capacity factor of dispatchable generators"
;

*=============================
* ------- Loop Solution ------
*=============================
if(Sw_Solve = 1,
  Loop(d,
    net_load(hr,r) = net_load_day(d,hr,r) ;
    cap(i,v,r) = cap_day(d,i,v,r) ;
    dr_cf_inc(hr,i,v,r) = dr_cf_inc_day(d,hr,i,v,r) ;
    dr_cf_dec(hr,i,v,r) = dr_cf_dec_day(d,hr,i,v,r) ;
    energy_budget(i,v,r) = energy_budget_day(d,i,v,r) ;
    GEN.lo(hr,i,v,r) = gen_low_hydro_day(d,hr,i,v,r) ;
    prod_load(r) = prod_load_day(d,r) ;
    PRODUCE.up(hr  ,r) = prod_cap(d,hr,r) ;
    Solve transmission using LP minimizing Z ;
    prices(d,hr,r) =  eq_load_balance.m(hr,r) ;
    flows_output(d,hr,r,rr,trtype)$routes(r,rr,trtype) = FLOW.l(hr,r,rr,trtype) ;
    gen_output(d,hr,i,v,r) = GEN.l(hr,i,v,r) ;
    storage_in_output(d,hr,i,v,r) = STORAGE_IN.l(hr,i,v,r) ;
    storage_level_output(d,hr,i,v,r) = STORAGE_LEVEL.l(hr,i,v,r) ;
    dr_shift_output(d,hr,hh,i,v,r)$dr1(i) = DR_SHIFT.l(hr,hh,i,v,r) ;
    dr_shed_output(d,hr,i,v,r)$dr2(i) = DR_SHED.l(hr,i,v,r) ;
    dropped_load_output(d,hr,r) = DROPPED_LOAD.l(hr,r) ;
    PRODUCE_output(d,hr,r) = PRODUCE.l(hr,r) ;
    CONVERSION_output(d,hr,r,intype,outtype) = CONVERSION.l(hr,r,intype,outtype) ;
  ) ;
) ;

*=============================
* ------- GUSS Solution ------
*=============================

set gd(d) "days per GUSS run" ;

set dict / gd.                  scenario.  ''
           net_load.            param.     net_load_day
           cap.                 param.     cap_day
           dr_cf_inc.           param.     dr_cf_inc_day
           dr_cf_dec.           param.     dr_cf_dec_day
           energy_budget.       param.     energy_budget_day
           GEN.                 lower.     gen_low_hydro_day
           prod_load.           param.     prod_load_day
           PRODUCE.             upper.     prod_cap
           eq_load_balance.     marginal.  prices
           FLOW.                level.     flows_output
           GEN.                 level.     gen_output
           STORAGE_IN.          level.     storage_in_output
           STORAGE_LEVEL.       level.     storage_level_output
           DR_SHIFT.            level.     dr_shift_output
           DR_SHED.             level.     dr_shed_output
           DROPPED_LOAD.        level.     dropped_load_output
           PRODUCE.             level.     PRODUCE_output
           CONVERSION.          level.     CONVERSION_output
         / ;

if(Sw_Solve = 2,
  gd(d) = yes ;
  Solve transmission using LP minimizing Z scenario dict ;
) ;

*=============================
* ------- Grid Solution ------
*=============================

set thread "grid jobs to run - only used if Sw_Solve=3" / thread1*thread%threads% /
    thread_days(thread,d) "map days to threads" 
      /
$include inputs_case%ds%threads.txt
      /
;

parameter h(thread) "model handles" ;

if(Sw_Solve = 3,
  transmission.solveLink = %solveLink.AsyncThreads% ;
  loop(thread,
    gd(d) = thread_days(thread,d) ;
    Solve transmission using LP minimizing Z scenario dict ;
    h(thread) = transmission.handle ;
  ) ;
* Collect the solutions
  repeat
    loop(thread$handlecollect(h(thread)),
      display$handledelete(h(thread)) "trouble deleting handles" ;
      h(thread) = 0 ;
    ) ;
    display$sleep(card(h)*5/%threads%) "waiting for solver" ;
  until card(h) = 0 or timeelapsed > 7200 ;
) ;

*=============================
* ------- Write results ------
*=============================

prices_h1(d,h1,r) = prices(d,h1,r) ;
flows_output_h1(d,h1,r,rr,trtype) = flows_output(d,h1,r,rr,trtype) ;
gen_output_h1(d,h1,i,v,r) = gen_output(d,h1,i,v,r) ;
storage_in_output_h1(d,h1,i,v,r) = storage_in_output(d,h1,i,v,r) ;
storage_level_output_h1(d,h1,i,v,r) = storage_level_output(d,h1,i,v,r) ;
dr_inc_output(d,hr,i,v,r) = sum{hh$dr_shift_output(d,hr,hh,i,v,r), dr_shift_output(d,hr,hh,i,v,r) / storage_eff(i)} ;
dr_inc_output_h1(d,h1,i,v,r) = dr_inc_output(d,h1,i,v,r) ;
dropped_load_output_h1(d,h1,r) = dropped_load_output(d,h1,r) ;
PRODUCE_output_h1(d,h1,r) = PRODUCE_output(d,h1,r) ;

cf_output(i,r)$sum{v, cap(i,v,r) } = sum{(d,hr,v), gen_output(d,hr,i,v,r) } / (sum{v, cap(i,v,r) } * 8760) ;

execute_unload "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx"
    prices
    flows_output
    gen_output
    storage_in_output
    dr_inc_output
    net_load_day
    dropped_load_output
    PRODUCE_output
    storage_level_output
    cap_day
    energy_budget_day
    gen_low_hydro_day
    gen_cost
    cap_feas
    cost_dropped_load
    energy_budget_feas
    CONVERSION_output
    cf_output
*     prices_h1, flows_output_h1, gen_output_h1,
*     storage_in_output_h1, storage_level_output_h1,
*     dropped_load_output_h1
;
