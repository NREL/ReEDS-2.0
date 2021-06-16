*Setting the default slash
$setglobal ds \

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix



*========================================
* -- Supply Side Variable Declaration --
*========================================

positive variables

*load variable - set equal to load_exog to compute holistic marginal price
  LOAD(r,h,t)                  "--MWh-- busbar load for each balancing region"
  EVLOAD(r,h,t)                "--MWh-- busbar load specific to EVs"
  FLEX(flex_type,r,h,t)        "--MWh-- flexible load shifted to each timeslice"
  PEAK_FLEX(r,szn,t)           "--MWh-- peak busbar load adjustment based on load flexibility"

* capacity and investment variables
  CAP(i,v,r,t)                 "--MW-- total generation capacity"
  CAP_SDBIN(i,v,r,szn,sdbin,t) "--MW-- generation capacity by storage duration bin for relevant technologies"
  INV(i,v,r,t)                 "--MW-- generation capacity add in year t"
  INV_REFURB(i,v,r,t)          "--MW-- investment in refurbishments of technologies that use a resource supply curve"
  INV_RSC(i,v,r,rscbin,t)      "--MW-- investment in technologies that use a resource supply curve"
  UPGRADES(i,v,r,t)            "--MW-- investments in upgraded capacity from ii to i"
  EXTRA_PRESCRIP(pcat,r,t)     "--MW-- builds beyond those prescribed once allowed in firstyear(pcat) - exceptions for gas-ct, wind-ons, and wind-ofs"

* generation and storage variables
  GEN(i,v,r,h,t)               "--MW-- electricity generation (post-curtailment) in hour h"
  CURT(r,h,t)                  "--MW-- curtailment from vre generators in hour h"
  CURT_REDUCT_TRANS(r,rr,h,t)  "--MW-- curtailment reduction in r from building new transmission to rr"
  MINGEN(r,szn,t)              "--MW-- minimum generation level in each season"
  STORAGE_IN(i,v,r,h,src,t)    "--MW-- storage entering in hour hthat is charging from a given source technology"
  STORAGE_LEVEL(i,v,r,h,t)     "--MWh per day-- storage level in hour h"

* seasonal hydrogen storage
  TES(i,v,r,szn,szn2,t)      "--MWh-- Total Energy Stored (TES) from season szn and used in season szn2"
  TEH(i,v,r,szn,t)           "--MWh-- Total Energy Held (TEH) during season szn that is to be used in another season"

* trade variables
  FLOW(r,rr,h,t,trtype)        "--MW-- electricity flow on transmission lines in hour h"
  OPRES_FLOW(ortype,r,rr,h,t)  "--MW-- interregional trade of operating reserves by operating reserve type"
  CURT_FLOW(r,rr,h,t)          "--MW-- interregional trade of curtailment"
  PRMTRADE(r,rr,trtype,szn,t)  "--MW-- planning reserve margin capacity traded from r to rr"
  PRMTRADE_RE(r,rr,trtype,szn,t)        "--MW-- planning reserve margin RE capacity traded from r to rr"

* operating reserve variables
  OPRES(ortype,i,v,r,h,t)      "--MW-- operating reserves by type"

* variable fuel amounts
  GASUSED(cendiv,gb,h,t)                "--MMBtu-- total gas used by gas bin",
  VGASBINQ_NATIONAL(fuelbin,t)          "--MMBtu-- National quantity of gas by bin"
  VGASBINQ_REGIONAL(fuelbin,cendiv,t)   "--MMBtu-- Regional (census divisions) quantity of gas by bin"
  BIOUSED(bioclass,r,t)                 "--MMBtu-- total biomass used by gas bin",

* RECS variables
  RECS(RPSCat,i,st,ast,t)               "--MWh-- renewable energy credits from state s to state ss",
  ACP_Purchases(RPSCat,st,t)            "--MWh-- purchases of ACP credits to meet the RPS constraints",
  EMIT(e,r,t)                           "--million metric tons co2-- total co2 emissions in a region (note: units dependent on emit_scale)"

* transmission variables
  CAPTRAN(r,rr,trtype,t)                "--MW-- capacity of transmission"
  INVTRAN(r,rr,t,trtype)                "--MW-- investment in transmission capacity"
  INVSUBSTATION(r,vc,t)                 "--MW-- substation investment--"

* water climate variables
  WATCAP(i,v,r,t)                        "--million gallons/year; Mgal/yr-- total water access capacity available in terms of withdraw/consumption per year"
  WAT(i,v,w,r,h,t)                       "--Mgal-- quantity of water withdrawn or consumed in hour h"
  WATER_CAPACITY_LIMIT_SLACK(wst,r,t)    "--Mgal/yr-- insufficient water supply in region r, of water type wst, in year t "
;

*========================================
* -- Supply Side Equation Declaration --
*========================================
EQUATION

* objective function calculation
 eq_ObjFn_Supply                      "--$s-- Objective function calculation"

*load constraint to compute proper marginal value
 eq_loadcon(r,h,t)                    "--MW-- load constraint used for computing the marginal energy price"
 eq_evloadcon(r,szn,t)                "--MWh-- mapping of seasonal EV load to each timeslice"

*load flexibility constraints
 eq_load_flex_day(flex_type,r,szn,t)  "--MWh-- total flexible load in each season is equal to the exogenously-specified flexible load"
 eq_load_flex1(flex_type,r,h,t)       "--MWh-- exogenously-specified flexible demand (load_exog_flex) must be served by flexible load (FLEX)"
 eq_load_flex2(flex_type,r,h,t)       "--MWh-- flexible load (FLEX) can't exceed exogenously-specified flexible demand (load_exog_flex)"
 eq_load_flex_peak(r,h,szn,t)         "--MWh-- adjust peak demand as needed based on the load flexibility (FLEX)"

*main capacity constraints
 eq_cap_init_noret(i,v,r,t)   "--MW-- Existing capacity that cannot be retired is equal to exogenously-specified amount"
 eq_cap_init_retub(i,v,r,t)   "--MW-- Existing capacity that can be retired is less than or equal to exogenously-specified amount"
 eq_cap_init_retmo(i,v,r,t)   "--MW-- Existing capacity that can be retired must be monotonically decreasing"
 eq_cap_new_noret(i,v,r,t)    "--MW-- New capacity that cannot be retired is equal to sum of all previous years investment"
 eq_cap_new_retub(i,v,r,t)    "--MW-- New capacity that can be retired is less than or equal to all previous years investment"
 eq_cap_new_retmo(i,v,r,t)    "--MW-- New capacity that can be retired must be monotonically decreasing unless increased by investment"
 eq_cap_upgrade(i,v,r,t)      "--MW-- All purchased upgrades are greater than or equal to the sum of upgraded capacity"

*capacity auxilary constraints
 eq_rsc_inv_account(i,v,r,t)              "--MW-- INV for rsc techs is the sum over all bins of INV_RSC"
 eq_rsc_INVlim(r,i,rscbin,t)              "--MW-- total investment from each rsc bin cannot exceed the available investment"
 eq_refurblim(i,r,t)                      "--MW-- total refurbishments cannot exceed the amount of capacity that has reached the end of its life"
 eq_forceprescription(pcat,r,t)           "--MW-- total investment in prescribed capacity must equal amount from exogenous prescriptions"
 eq_force_retire(i,r,t)                   "--MW-- force retirement of capacity"
 eq_neartermcaplimit(r,t)                 "--MW-- near-term capacity cannot be greater than projects in the pipeline"
 eq_growthlimit_relative(tg,t)            "--MW-- relative growth limit on technologies in growlim(i)"
 eq_growthlimit_absolute(tg,t)            "--MW-- absolute growth limit on technologies in growlim(i)"
 eq_cap_sdbin_balance(i,v,r,szn,t)        "--MW-- total binned storage capacity must be equal to total storage capacity"
 eq_sdbin_limit(ccreg,szn,sdbin,t)        "--MW-- binned storage capacity cannot exceed storage duration bin size"

* operation and reliability
 eq_supply_demand_balance(r,h,t)          "--MW-- supply demand balance"
 eq_dhyd_dispatch(i,v,r,szn,t)            "--MWh-- dispatchable hydro seasonal constraint"
 eq_capacity_limit(i,v,r,h,t)             "--MW-- generation limited to available capacity"
 eq_capacity_limit_hydro_nd(i,v,r,h,t)    "--MW-- generation limited to available capacity for non-dispatchable hydro"
 eq_curt_gen_balance(r,h,t)               "--MW-- net generation and curtailment must equal gross generation"
 eq_curtailment(r,h,t)                    "--MW-- curtailment level"
 eq_mingen_lb(r,h,szn,t)                  "--MW-- lower bound on minimum generation level"
 eq_mingen_ub(r,h,szn,t)                  "--MW-- upper bound on minimum generation level"
 eq_reserve_margin(r,szn,t)               "--MW-- planning reserve margin requirement"
 eq_transmission_limit(r,rr,h,t,trtype)   "--MW-- transmission flow limit"
 eq_trans_reduct1(r,rr,h,t)               "--MW-- limit CURT_REDUCT_TRANS by transmission investment"
 eq_trans_reduct2(r,rr,h,t)               "--MW-- limit CURT_REDUCT_TRANS by maximum level found by Augur"
 eq_minloading(i,v,r,h,hh,t)              "--MW-- minimum loading across same-season hours"
 eq_min_cf(i,t)                           "--MWh-- minimum capacity factor constraint"

* operating reserve constraints
 eq_OpRes_requirement(ortype,r,h,t)       "--MW-- operating reserve constraint"
 eq_ORCap(ortype,i,v,r,h,t)               "--MW-- operating reserve capacity availability constraint"

* regional and national policies
 eq_emit_accounting(e,r,t)                "--metric tons co2-- accounting for total CO2 emissions in a region"
 eq_emit_rate_limit(e,r,t)                "--metric tons pollutant per mwh-- emission rate limit"
 eq_annual_cap(e,t)                       "--metric tons-- annual (year-specific) emissions cap",
 eq_bankborrowcap(e)                      "--weighted metric tons co2-- flexible banking and borrowing cap (to be used w/intertemporal solve only$sum(t$emit_cap(e,t)])"
 eq_RGGI_cap(t)                           "--metric tons co2-- RGGI constraint -- Regions' emissions must be less than the RGGI cap"
 eq_AB32_cap(t)                           "--metric tons co2-- AB32 constraint -- California emissions must be less than the AB32 cap"
 eq_CSAPR_Budget(csapr_group,t)           "--MT NOX-- CSAPR trading group emissions cannot exceed the budget cap"
 eq_CSAPR_Assurance(st,t)                 "--MT NOX-- CSAPR state emissions cannot exceed the assurance cap"
 eq_BatteryMandate(r,t)                   "--MW-- Battery storage capacity must be greater than indicated level"

*RPS Policy
 eq_REC_Generation(RPSCat,i,st,t)         "--RECs-- Generation of RECs by state"
 eq_REC_Requirement(RPSCat,st,t)          "--RECs-- RECs generated plus trade must meet the state's requirement"
 eq_REC_ooslim(RPSCat,st,t)               "--RECs-- RECs imported cannot exceed a fraction of total requirement for certain states",
 eq_REC_launder(RPSCat,st,t)              "--RECs-- RECs laundering constraint"
 eq_REC_BundleLimit(RPSCat,st,ast,t)      "--RECS-- trade in bundle recs must be less than interstate electricity transmission"
 eq_REC_unbundledLimit(RPScat,st,t)       "--RECS-- unbundled RECS cannot exceed some percentage of total REC requirements"
 eq_RPS_OFSWind(st,t)                     "--MW-- MW of offshore wind capacity must be greater than or equal to RPS amount"
 eq_national_gen(t)                       "--MWh-- e.g. a national RPS or CES. require a certain amount of total generation to be from specified sources.",
 eq_national_nucgen(t)                    "--MWh-- require a certain amount of total generation to be from nuclear"
 eq_national_coalgen(t)                   "--MWh-- require a certain amount of total generation to be from coal"
 eq_national_pvgen(t)                     "--MWh-- require a certain amount of total generation to be from PV"
 eq_national_cspgen(t)                    "--MWh-- require a certain amount of total generation to be from CSP"
 eq_national_windgen(t)                   "--MWh-- require a certain amount of total generation to be from wind"
 eq_national_hydrogen(t)                  "--MWh-- require a certain amount of total generation to be from hydro"
 eq_national_natgasgen(t)                 "--MWh-- require a certain amount of total generation to be from natural gas"
 eq_national_ogsgen(t)                    "--MWh-- require a certain amount of total generation to be from o-g-s"
 eq_national_rps_resmarg(r,szn,t)         "--MW-- require that a specified fraction of firm capacity be from renewable sources"

* fuel supply curve equations
 eq_gasused(cendiv,h,t)                   "--MMBtu-- gas used must be from the sum of gas bins"
 eq_gasbinlimit(cendiv,gb,t)              "--MMBtu-- limit on gas from each bin"
 eq_gasbinlimit_nat(gb,t)                 "--MMBtu-- national limit on gas from each bin"
 eq_bioused(r,t)                          "--MMBtu-- bio used must be from the sum of bio bins"
 eq_biousedlimit(bioclass,r,t)            "--MMBtu-- limit on bio from each bin"

*following are used for regional natural gas supply curves
 eq_gasaccounting_regional(cendiv,t)         "--MMBtu-- regional gas consumption cannot exceed the amount used in bins"
 eq_gasaccounting_national(t)                "--MMBtu-- national gas consumption cannot exceed the amount used in bins"
 eq_gasbinlimit_regional(fuelbin,cendiv,t)   "--MMBtu-- regional binned gas usage cannot exceed bin capacity"
 eq_gasbinlimit_national(fuelbin,t)          "--MMBtu-- national binned gas usage cannot exceed bin capacity"

*transmission equations
 eq_CAPTRAN(r,rr,trtype,t)                   "--MW-- capacity accounting for transmission"
 eq_prescribed_transmission(r,rr,trtype,t)   "--MW-- investment in transmission up to 2020 must be less than the exogenous possible transmission",
 eq_INVTRAN_VCLimit(r,vc)                    "--MW-- investment in transmission capacity cannot exceed that available in its VC bin"
 eq_PRMTRADELimit(r,rr,trtype,szn,t)         "--MW-- trading of PRM capacity cannot exceed the line's capacity"
 eq_SubStationAccounting(r,t)                "--Substations-- accounting for total investment in each substation"
 eq_PRMTRADELimit_RE(r,rr,trtype,szn,t)             "--MW-- trading of RE PRM capacity cannot exceed the line's capacity"

* storage-specific equations
 eq_storage_capacity(i,v,r,h,t)           "--MW-- Second storage capacity constraint in addition to eq_capacity_limit"
 eq_storage_duration(i,v,r,h,t)           "--MWh-- limit STORAGE_LEVEL based on hours of storage available"
 eq_storage_thermalres(i,v,r,h,t)         "--MW-- thermal storage contribution to operating reserves is store_in only"
 eq_storage_level(i,v,r,h,t)              "--MWh per day-- Storage level inventory balance from one time-slice to the next"
 eq_storage_in_min(r,h,t)                 "--MW-- lower bound on STORAGE_IN"
 eq_storage_in_max(r,h,src,t)             "--MW-- upper bound on storage charging that can come from new sources"

* hydrogen storage equations
 eq_storage_h2_def_total_energy_held(i,v,r,szn,t)           "--MWh-- define the Total Energy Held in storage during season szn for use in another season"
 eq_storage_h2_ub_start_energy_season(i,v,r,szn,t)          "--MWh-- upper bound of energy in storage at the START of season szn"
 eq_storage_h2_ub_end_energy_season(i,v,r,szn,t)            "--MWh-- upper bound of energy in storage at the END of season szn"
 eq_storage_h2_link_season_timeslice_charge(i,v,r,szn,t)    "--MWh-- link between season and time-slice for energy storage CHARGING"
 eq_storage_h2_link_season_timeslice_discharge(i,vv,r,szn,t) "--MWh-- link between season and time-slice for energy storage DISCHARGING"
 eq_storage_h2_balance_annual(i,v,r,t)                      "--MWh-- total energy charged = total energy discharged during the year"

*Canadian imports balance
 eq_Canadian_Imports(r,szn,t)             "--MWh-- Balance of Canadian imports by season"

* water usage accounting
 eq_water_accounting(i,v,w,r,h,t)         "--Mgal-- water usage accounting"
 eq_water_capacity_total(i,v,r,t)         "--Mgal-- specify required water access based on generation capacity and water use rate"
 eq_water_capacity_limit(wst,r,t)         "--Mgal/yr-- total water access must not exceed supply by region and water type"
 eq_water_use_limit(i,v,w,r,szn,t)        "--Mgal/yr-- water use must not exceed available access"
;

*==========================
* --- LOAD CONSTRAINTS ---
*==========================

*the marginal off of this constraint allows you to
*determine the full price of electricity load
*i.e. the price of load with consideration to operating
*reserve and planning reserve margin considered
eq_loadcon(r,h,t)$[rfeas(r)$tmodel(t)]..

    LOAD(r,h,t)

    =e=

*[plus] the static, exogenous load
    + load_exog_static(r,h,t)

*[plus] exogenously defined exports to Canada
    + can_exports_h(r,h,t)

*[plus] load from EV charging
    + EVLOAD(r,h,t)$Sw_EV

*[plus] load shifted from other timeslices
    + sum{flex_type, FLEX(flex_type,r,h,t) }$Sw_EFS_flex
;


eq_evloadcon(r,szn,t)$[rfeas(r)$tmodel(t)$Sw_EV]..

    sum{h$h_szn(h,szn),hours(h) * EVLOAD(r,h,t) }

    =e=

    ev_dynamic_demand(r,szn,t)
;


*======================================
* --- LOAD FLEXIBILITY CONSTRAINTS ---
*======================================

*The following 3 equations apply to the flexibility of load in ReEDS, originally developed
*as part of the EFS study in ReEDS heritage and adapted for ReEDS-2.0 here.

* FLEX load in each season equals the total exogenously-specified flexible load in each season
eq_load_flex_day(flex_type,r,szn,t)$[rfeas(r)$tmodel(t)$Sw_EFS_flex]..

    sum{h$h_szn(h,szn), FLEX(flex_type,r,h,t) * hours(h) } / numdays(szn)

    =e=

    sum{h$h_szn(h,szn), load_exog_flex(flex_type,r,h,t) * hours(h) } / numdays(szn)
;


* for the "previous" flex type: the amount of exogenously-specified load in timeslice "h"
* must be served by FLEX load either in the timeslice h or the timeslice PRECEEDING h
*
* for the "next" flex type: the amount of exogenously-specified load in timeslice "h"
* must be served by FLEX load either in the timeslice h or the timeslice FOLLOWING h
*
* for the "adjacent" flex type: the amount of exogenously-specified load in timeslice "h"
* must be served by FLEX load either in the timeslice h or a timeslice ADJACENT to h

eq_load_flex1(flex_type,r,h,t)$[rfeas(r)$tmodel(t)$Sw_EFS_flex]..

    FLEX(flex_type,r,h,t) * hours(h)

    + sum{hh$flex_h_corr1(flex_type,h,hh), FLEX(flex_type,r,hh,t) * hours(hh) }

    =g=

    load_exog_flex(flex_type,r,h,t) * hours(h)
;


* for the "previous" flex type: FLEX load in timeslice "h" cannot exceed the sum of
* exogenously-specified load in timeslice h and the timeslice following h
*
* for the "next" flex type: FLEX load in timeslice "h" cannot exceed the sum of
* exogenously-specified load in timeslice h and the timeslice preceeding h
*
* for the "adjacent" flex type: FLEX load in timeslice "h" cannot exceed the sum of
* exogenously-specified load in timeslice h and the timeslices adjacent to h

eq_load_flex2(flex_type,r,h,t)$[rfeas(r)$tmodel(t)$Sw_EFS_flex]..

    load_exog_flex(flex_type,r,h,t) * hours(h)

    + sum{hh$flex_h_corr2(flex_type,h,hh), load_exog_flex(flex_type,r,hh,t) * hours(hh) }

    =g=

    FLEX(flex_type,r,h,t) * hours(h)
;


eq_load_flex_peak(r,h,szn,t)$[rfeas(r)$tmodel(t)$Sw_EFS_flex]..
*   peak demand EFS flexibility adjustment is greater than
    PEAK_FLEX(r,szn,t)$h_szn(h,szn)

    =g=

*   the static peak in each timeslice
    peakdem_static_h(r,h,t)$h_szn(h,szn)

*   PLUS the flexibile load served in each timeslice
    + sum{flex_type, FLEX(flex_type,r,h,t) }$h_szn(h,szn)

*   MINUS the static peak demand in the season corresponding to each timeslice
    - peakdem_static_szn(r,szn,t)$h_szn(h,szn)
;


*=============================================================
* --- EQUATIONS FOR RELATING CAPACITY ACROSS TIME PERIODS ---
*=============================================================

*====================================
* -- existing capacity equations --
*====================================

$ontext

The following six equations dictate how capacity is represented in the model.

The first three equations handle init-X vintages (those that existed pre-2010)
which are bounded by m_capacity_exog. With retirements (in the second and third
equations), the constraints imply that capacity must be less than or
equal to m_capacity_exog and monotonically decreasing over time -
implying that if endogenous capacity was reduced in the previous year,
it cannot be brought back online.

New capacity, handled in equations four through six, is the sum of previous
years' greenfield investments and refurbishments. The same logic is present
for retiring capacity, the only difference being that contemporaneous
investment can increase the present-period's capacity.

Upgraded capacity reduces the total amount of capacity available to the
upgraded-from technology. For example, the model starts with 100MW of
coaloldscr (m_capacity_exog = 100) capacity then upgrades 10MW of that to
coaloldscr_coal-ccs capacity. The remaining amount of available coaloldscr
is thus 90 and coaloldscr_coal-ccs capacity is 10 but both are still less
than the 100 available. As time progresses and exogenous capacity declines,
the model chooses which units to take offline.

$offtext

eq_cap_init_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $(not retiretech(i,v,r,t))]..

    m_capacity_exog(i,v,r,t)

    =e=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;

eq_cap_init_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $retiretech(i,v,r,t)]..

    m_capacity_exog(i,v,r,t)

    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;

eq_cap_init_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $retiretech(i,v,r,t)]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)],
         CAP(i,v,r,tt)

         + sum{ii$[valcap(ii,v,r,tt)$upgrade_from(ii,i)],
               CAP(ii,v,r,tt) }$Sw_Upgrades
        }


    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;


*==============================
* -- new capacity equations --
*==============================

eq_cap_new_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $(not retiretech(i,v,r,t))]..

    sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
        }

    =e=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;

eq_cap_new_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $retiretech(i,v,r,t)]..

    sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
      }

    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;

eq_cap_new_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $retiretech(i,v,r,t)]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)],
         degrade(i,tt,t) * CAP(i,v,r,tt)

         + sum{ii$[valcap(ii,v,r,tt)$upgrade_from(ii,i)],
               CAP(ii,v,r,tt) }$Sw_Upgrades
        }

    + INV(i,v,r,t)$valinv(i,v,r,t)

    + INV_REFURB(i,v,r,t)$[valinv(i,v,r,t)$refurbtech(i)$Sw_Refurb]

    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
           CAP(ii,v,r,t) }$Sw_Upgrades

;

eq_cap_upgrade(i,v,r,t)$[valcap(i,v,r,t)$upgrade(i)$Sw_Upgrades$tmodel(t)]..
*all previous years upgrades
    sum{(tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))
            $(yeart(tt)>=upgradeyear)$(initv(v) or (newv(v) and ivt(i,v,tt)))],
        UPGRADES(i,v,r,tt)}

    =g=

    CAP(i,v,r,t)
;


eq_forceprescription(pcat,r,t)$[rfeas_cap(r)$tmodel(t)$force_pcat(pcat,t)$Sw_ForcePrescription
                               $sum{(i,newv)$[prescriptivelink(pcat,i)], valinv(i,newv,r,t) }]..

*capacity built in the current period
    sum{(i,newv)$[valinv(i,newv,r,t)$prescriptivelink(pcat,i)],
        INV(i,newv,r,t) + INV_REFURB(i,newv,r,t)$[refurbtech(i)$Sw_Refurb]}

    =e=

*must equal the prescribed amount
    noncumulative_prescriptions(pcat,r,t)

* plus any extra buildouts (no penalty here - used as free slack)
* only on or after the first year the techs are available
    + EXTRA_PRESCRIP(pcat,r,t)$[yeart(t)>=firstyear_pcat(pcat)]

* or in regions where there is a offshore wind requirement
    + EXTRA_PRESCRIP(pcat,r,t)$[r_offshore(r,t)$sameas(pcat,'wind-ofs')]
;

eq_force_retire(i,r,t)$[sum{v, valcap(i,v,r,t) }$tmodel(t)$forced_retirements(i,r,t)]..

    sum{v, CAP(i,v,r,t) }

    =e=

    0
;

eq_neartermcaplimit(r,t)$[rfeas_cap(r)$tmodel(t)$sum{rr, near_term_cap_limits("wind",rr,t) }
                            $sum{(i,v)$[valcap(i,v,r,t)$tg_i("wind",i)], 1 }
                            $Sw_NearTermLimits$Sw_ForcePrescription]..

    near_term_cap_limits("wind",r,t)

    =g=

    EXTRA_PRESCRIP("wind-ons",r,t)
;


*here we limit the amount of refurbishments available in specific year
*this is the sum of all previous year's investment that is now beyond the age
*limit (i.e. it has exited service) plus the amount of retired exogenous capacity
*that we begin with
eq_refurblim(i,r,t)$[rfeas_cap(r)$tmodel(t)$refurbtech(i)$Sw_Refurb]..

*investments that meet the refurbishment requirement (i.e. they've expired)
    sum{(vv,tt)$[m_refurb_cond(i,vv,r,t,tt)$(tmodel(tt) or tfix(tt))],
         INV(i,vv,r,tt) }

*[plus] exogenous decay in capacity
*note here that the tfix or tmodel set does not apply
*since we'd want capital that expires in off-years to
*be included in this calculation as well
    + sum{(v,tt)$[yeart(tt)<=yeart(t)],
         m_avail_retire_exog_rsc(i,v,r,tt) }

    =g=

*must exceed the total sum of investments in refurbishments
*that have yet to expire - implying an investment can be refurbished more than once
*if the first refurbishment has exceed its age limit
    sum{(vv,tt)$[inv_cond(i,vv,r,t,tt)$(tmodel(tt) or tfix(tt))],
         INV_REFURB(i,vv,r,tt)
       }
;


eq_rsc_inv_account(i,v,r,t)$[tmodel(t)$valinv(i,v,r,t)$rsc_i(i)]..

  sum{rscbin$m_rscfeas(r,i,rscbin), INV_RSC(i,v,r,rscbin,t) }

  =e=

  INV(i,v,r,t)
;


*note that the following equation only restricts inv_rsc and not inv_refurb
*therefore, the capacity indicated by the supply curve may be limiting
*but the plant can still be refurbished
eq_rsc_INVlim(r,i,rscbin,t)$[tmodel(t)$rsc_i(i)$rfeas_cap(r)$m_rscfeas(r,i,rscbin)$m_rsc_con(r,i)]..
*With water constraints, some RSC techs are expanded to include cooling technologies
*but the combination of m_rsc_con and rsc_agg allows for those investments
*to be limited by the numeraire techs' m_rsc_dat

*capacity indicated by the resource supply curve (with undiscovered geo available at the "discovered" amount)
    m_rsc_dat(r,i,rscbin,"cap") * (1$[not geo_undisc(i)] + geo_discovery(t)$geo_undisc(i))

    =g=

*must exceed the amount of total investment from that supply curve
    sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) <= yeart(t))$rsc_agg(i,ii)],
         INV_RSC(ii,v,r,rscbin,tt) * resourcescaler(ii) }
;


eq_growthlimit_relative(tg,t)$[growth_limit_relative(tg)$tmodel(t)
                              $Sw_GrowthRelCon$(yeart(t)>=2022)$(not tlast(t))]..

*the relative growth rate multiplied by the existing technology group's existing capacity
    growth_limit_relative(tg) ** (sum{tt$[tprev(tt,t)], yeart(tt)} - yeart(t)) *
    sum{(i,v,r,tt)$[tprev(t,tt)$valcap(i,v,r,tt)$tg_i(tg,i)$rfeas_cap(r)],
         CAP(i,v,r,tt) }

    =g=

* must exceed the current periods investment
* note scarcely-used set 'tg' is technology group (allows for lumping together or all wind/solar techs)
    sum{(i,v,r)$[valcap(i,v,r,t)$tg_i(tg,i)$rfeas_cap(r)],
         CAP(i,v,r,t) }
;


eq_growthlimit_absolute(tg,t)$[growth_limit_absolute(tg)$tmodel(t)
                               $Sw_GrowthAbsCon$(yeart(t)>=2018)$(not tlast(t))]..

* the absolute limit of growth (in MW)
     (sum{tt$[tprev(tt,t)], yeart(tt) } - yeart(t))
     * growth_limit_absolute(tg)

     =g=

* must exceed the total investment - same RHS as previous equation
* note scarcely-used set 'tg' is technology group (allows for lumping together or all wind/solar techs)
     sum{(i,v,r,rscbin)$[valinv(i,v,r,t)$m_rscfeas(r,i,rscbin)$tg_i(tg,i)$rsc_i(i)],
          INV_RSC(i,v,r,rscbin,t) }
;


*capacity must be greater than supply
*note this does not apply to both storage and dispatchable hydro
*dispatchable hydro is accounted for in the eq_dhyd_dispatch
eq_capacity_limit(i,v,r,h,t)$[tmodel(t)$valgen(i,v,r,t)$(not storage_no_csp(i))]..
*total amount of dispatchable, non-hydro capacity
    (avail(i,v,h) * sum{rr$cap_agg(r,rr),
                       CAP(i,v,rr,t)$valcap(i,v,rr,t) })$[dispatchtech(i)$(not hydro_d(i))]

*total amount of dispatchable hydro capacity
    + (avail(i,v,h) * sum{(rr,szn)$[cap_agg(r,rr)$h_szn(h,szn)],
                       CAP(i,v,rr,t)$valcap(i,v,rr,t) * cap_hyd_szn_adj(i,szn,rr)})$hydro_d(i)

*sum of non-dispatchable capacity multiplied by its rated capacity factor,
*only vre technologies are curtailable
    + (sum{rr$[cap_agg(r,rr)$rfeas_cap(rr)$valcap(i,v,rr,t)],
          (m_cf(i,v,rr,h,t)
           * CAP(i,v,rr,t)) })$[not dispatchtech(i)]

    =g=

*must exceed generation
    GEN(i,v,r,h,t)

*[plus] sum of operating reserves by type
    + sum{ortype$reserve_frac(i,ortype),
          OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;

eq_capacity_limit_hydro_nd(i,v,r,h,t)$[tmodel(t)$rfeas(r)$valgen(i,v,r,t)$(not storage(i))$hydro_nd(i)]..
*sum of non-dispatchable hydro capacity multiplied by its rated capacity factor,
    + sum{rr$[cap_agg(r,rr)$rfeas_cap(rr)$valcap(i,v,rr,t)],
          (m_cf(i,v,rr,h,t)
           * CAP(i,v,rr,t)) }

    =e=

*must exceed generation
    GEN(i,v,r,h,t)

*[plus] sum of operating reserves by type
    + sum{ortype$reserve_frac(i,ortype),
          OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;


eq_curt_gen_balance(r,h,t)$[tmodel(t)$rfeas(r)]..

*total potential generation
    sum{(i,v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$rfeas_cap(rr)$vre(i)],
         m_cf(i,v,rr,h,t) * CAP(i,v,rr,t) }

*[minus] curtailed generation
    - CURT(r,h,t)

    =g=

*must exceed realized generation
    sum{(i,v)$[valgen(i,v,r,t)$vre(i)], GEN(i,v,r,h,t) }

*[plus] sum of operating reserves by type
    + sum{(ortype,i,v)$[reserve_frac(i,ortype)$valgen(i,v,r,t)$vre(i)],
          OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;


eq_curtailment(r,h,t)$[tmodel(t)$rfeas(r)]..

*curtailment
    CURT(r,h,t)

    =g=

*curtailment of VRE (intertemporal only)
    sum{(i,v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$rfeas_cap(rr)$vre(i)],
        m_cf(i,v,rr,h,t) * CAP(i,v,rr,t) * curt_int(i,rr,h,t)
       }

*[plus] curtailment due to minimum generation (intertemporal only)
    + (curt_mingen_int(r,h,t) * sum{h_szn(h,szn), MINGEN(r,szn,t) })$Sw_Mingen

*[plus] excess curtailment (intertemporal only)
    + curt_excess(r,h,t)

*[plus] the marginal curtailmet of new VRE (sequential only)
*Note: new distpv is included with curt_old
    + sum{(i,v,rr)$[cap_agg(r,rr)$valinv(i,v,rr,t)$vre(i)],
              m_cf(i,v,rr,h,t) * curt_marg(i,rr,h,t)
              * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] the curtailment from existing VRE (sequential only)
    + curt_old(r,h,t)

*[plus] curtailment due to changes in minimum generation levels (sequential only)
    + curt_mingen(r,h,t) * sum{h_szn(h,szn), MINGEN(r,szn,t)
        - sum{tt$tprev(t,tt), mingen_postret(r,szn,tt) } }$[Sw_Mingen$(yeart(t)>=mingen_firstyear)]

*[minus] curtailment reduction from charging storge during timeslices with curtailment
    - sum{(i,v,src)$[valgen(i,v,r,t)$storage_no_csp(i)],
           curt_stor(i,v,r,h,src,t) * STORAGE_IN(i,v,r,h,src,t)
         }

*[minus] curtailment reduction from building new transmission to rr
    - sum{rr$sum{trtype, routes_inv(r,rr,trtype,t) }, CURT_REDUCT_TRANS(r,rr,h,t) }

*[plus] net flow of curtailment with no transmission losses (otherwise CURT can be turned into transmission losses)
    + sum{(trtype,rr)$routes(rr,r,trtype,t), CURT_FLOW(r,rr,h,t) }$Sw_CurtFlow
    - sum{(trtype,rr)$routes(r,rr,trtype,t), CURT_FLOW(r,rr,h,t) }$Sw_CurtFlow
;


eq_mingen_lb(r,h,szn,t)$[h_szn(h,szn)$rfeas(r)$(yeart(t)>=mingen_firstyear)
                        $tmodel(t)$Sw_Mingen]..

*minimum generation level in a season
    MINGEN(r,szn,t)

    =g=

*must be greater than the minimum generation level in each time slice in that season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)], GEN(i,v,r,h,t)  * minloadfrac(r,i,h) }
;


eq_mingen_ub(r,h,szn,t)$[h_szn(h,szn)$rfeas(r)$(yeart(t)>=mingen_firstyear)
                        $tmodel(t)$Sw_Mingen]..

*generation in each timeslice in a season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)], GEN(i,v,r,h,t)  }

    =g=

*must be greater than the minimum generation level
    MINGEN(r,szn,t)
;


*requirement for techs to have a minimum annual capacity factor
*disabled by default and rarely applied
eq_min_cf(i,t)$[minCF(i,t)$tmodel(t)$sum{(v,r), valgen(i,v,r,t) }$Sw_MinCFCon]..

    sum{(v,r,h)$valgen(i,v,r,t), hours(h) * GEN(i,v,r,h,t) }

    =g=

    sum{(v,r), sum{rr$[cap_agg(r,rr)$valcap(i,v,rr,t)], CAP(i,v,rr,t) } } * sum{h, hours(h) } * minCF(i,t)
;


eq_dhyd_dispatch(i,v,r,szn,t)$[rfeas(r)$tmodel(t)$hydro_d(i)$valgen(i,v,r,t)]..

*seasonal hours [times] seasonal capacity factor adjustment [times] total hydro capacity
    sum{h$[h_szn(h,szn)], avail(i,v,h) * hours(h) }

*following parameter could be wrapped into one...
    * CAP(i,v,r,t)
    * cap_hyd_szn_adj(i,szn,r)
    * cf_hyd(i,szn,r,t)
    * cfhist_hyd(r,t,szn,i)

    =g=

*total seasonal generation
    sum{h$[h_szn(h,szn)], hours(h)
        * ( GEN(i,v,r,h,t)
              + sum{ortype$reserve_frac(i,ortype), OPRES(ortype,i,v,r,h,t) }$Sw_OpRes )
       }
;


*===============================
* --- SUPPLY DEMAND BALANCE ---
*===============================

eq_supply_demand_balance(r,h,t)$[rfeas(r)$tmodel(t)]..

* generation
    sum{(i,v)$valgen(i,v,r,t), GEN(i,v,r,h,t) }

* [plus] net transmission with imports reduced by losses
    + sum{(trtype,rr)$routes(rr,r,trtype,t), (1-tranloss(rr,r,trtype)) * FLOW(rr,r,h,t,trtype) }
    - sum{(trtype,rr)$routes(r,rr,trtype,t), FLOW(r,rr,h,t,trtype) }

* [minus] storage charging
    - sum{(i,v,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) }

    =e=

* must exceed demand
    LOAD(r,h,t)
;


*=======================================
* --- MINIMUM LOADING CONSTRAINTS ---
*=======================================

* the generation in any hour cannot exceed the minloadfrac times the
* supply from other hours within that hour correlation set (via hour_szn_group(h,hh))
* note that hour_szn_group does not include the same hour (i.e. h!=hh)
eq_minloading(i,v,r,h,hh,t)$[valgen(i,v,r,t)$minloadfrac(r,i,hh)
                            $tmodel(t)$hour_szn_group(h,hh)]..

    GEN(i,v,r,h,t)

    =g=

    GEN(i,v,r,hh,t) * minloadfrac(r,i,hh)
;


*=======================================
* --- OPERATING RESERVE CONSTRAINTS ---
*=======================================

eq_ORCap(ortype,i,v,r,h,t)$[tmodel(t)$valgen(i,v,r,t)$Sw_OpRes
                            $reserve_frac(i,ortype)$(not STORAGE_NO_CSP(i))$(not hydro_nd(i))]..

*the reserve_frac times...
    reserve_frac(i,ortype) * (
* the amount of committed capacity available for a season is assumed to be the amount
* of generation from the timeslice that has the highest demand (not including h17!)
         sum{(szn,hh)$[h_szn(h,szn)$maxload_szn(r,hh,t,szn)],
              GEN(i,v,r,hh,t) })

    =g=

*note the reserve_frac applies to each opres by type
    OPRES(ortype,i,v,r,h,t)
;


*operating reserves must meet the operating reserves requirement (by ortype)
eq_OpRes_requirement(ortype,r,h,t)$[rfeas(r)$tmodel(t)$Sw_OpRes]..

*operating reserves from technologies that can produce them (i.e. those w/ramp rates)
    sum{(i,v)$[valgen(i,v,r,t)$(reserve_frac(i,ortype) or hydro_d(i) or storage(i))
              $(not hydro_nd(i))],
         OPRES(ortype,i,v,r,h,t) }

*[plus] net transmission of operating reserves (while including losses for imports)
    + sum{rr$opres_routes(rr,r,t),(1-tranloss(rr,r,"AC")) * OPRES_FLOW(ortype,rr,r,h,t) }
    - sum{rr$opres_routes(r,rr,t),OPRES_FLOW(ortype,r,rr,h,t) }

    =g=

*must meet the demand for or type
*first portion is from load
    orperc(ortype,"or_load") * LOAD(r,h,t)

*next portion is from the wind generation
    + orperc(ortype,"or_wind") * sum{(i,v)$[wind(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t)}

*final portion is from upv, dupv, and distpv capacity
*note that pv capacity is held at the balancing area
    + orperc(ortype,"or_pv")   * sum{(i,v)$[pv(i)$valcap(i,v,r,t)],
         CAP(i,v,r,t) }$dayhours(h)
;


*=================================
* --- PLANNING RESERVE MARGIN ---
*=================================

*trade of planning reserve margin capacity cannot exceed the transmission line's available capacity
eq_PRMTRADELimit(r,rr,trtype,szn,t)$[tmodel(t)$routes(r,rr,trtype,t)$Sw_ReserveMargin]..

*[plus] transmission capacity
    + CAPTRAN(r,rr,trtype,t)

    =g=

*[plus] firm capacity traded between regions
    + PRMTRADE(r,rr,trtype,szn,t)
;

*binned capacity must be the same as capacity
eq_cap_sdbin_balance(i,v,r,szn,t)$[tmodel(t)$valcap(i,v,r,t)$storage_no_csp(i)]..

*total capacity in each region
    CAP(i,v,r,t)

    =e=

*sum of all binned capacity within each region
    sum{sdbin, CAP_SDBIN(i,v,r,szn,sdbin,t) }
;

*binned capacity cannot exceed sdbin size
eq_sdbin_limit(ccreg,szn,sdbin,t)$[tmodel(t)$sum{r$r_ccreg(r,ccreg), rfeas(r)}]..

*sdbin size from CC script
    sdbin_size(ccreg,szn,sdbin,t)

    =g=

*capacity in each sdbin adjusted by the appropriate CC value
    sum{(i,v,r)$[r_ccreg(r,ccreg)$valcap(i,v,r,t)$storage_no_csp(i)],
        CAP_SDBIN(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin)
       }

;

eq_reserve_margin(r,szn,t)$[tmodel(t)$rfeas(r)$(yeart(t)>=model_builds_start_yr)$Sw_ReserveMargin]..

*[plus] sum of all non-rsc and non-storage capacity
    + sum{(i,v)$[valcap(i,v,r,t)$(not vre(i))$(not hydro(i))$(not storage(i))],
          CAP(i,v,r,t)
         }

*[plus] firm capacity from existing VRE or CSP
*only used in sequential solve case (otherwise cc_old = 0)
    + sum{(i,rr)$[(vre(i) or csp(i))$cap_agg(r,rr)$rfeas_cap(rr)],
          cc_old(i,rr,szn,t)
         }

*[plus] marginal capacity credit of VRE and csp times new investment
*only used in sequential solve case (otherwise m_cc_mar = 0)
*Note: new distpv is included with cc_old
    + sum{(i,v,rr)$[cap_agg(r,rr)$(vre(i) or csp(i))$valinv(i,v,rr,t)],
          m_cc_mar(i,rr,szn,t) * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] firm capacity contribution from all binned storage capacity
*for now this is just battery, pumped-hydro, CAES, and H2
    + sum{(i,v,rr,sdbin)$[cap_agg(r,rr)$storage_no_csp(i)$valcap(i,v,rr,t)],
          cc_storage(i,sdbin) * CAP_SDBIN(i,v,rr,szn,sdbin,t)
         }

*[plus] average capacity credit times capacity of VRE and storage
*used in rolling window and full intertemporal solve (otherwise cc_int = 0)
    + sum{(i,v,rr)$[(vre(i) or storage(i))$valcap(i,v,rr,t)$cap_agg(r,rr)],
          cc_int(i,v,rr,szn,t) * CAP(i,v,rr,t)
         }

*[plus] excess capacity credit
*used in rolling window and full intertemporal solve when using marginals for cc_int (otherwise cc_excess = 0)
    + sum{(i,rr)$[(vre(i) or storage(i))$cap_agg(r,rr)$rfeas_cap(rr)],
          cc_excess(i,rr,szn,t)
         }

*[plus] firm capacity of non-dispatchable hydro
* nb: hydro_nd generation does not fluctuate
* within a seasons set of hours
    + sum{(i,v,h)$[hydro_nd(i)$valgen(i,v,r,t)$h_szn_prm(h,szn)],
          GEN(i,v,r,h,t)
         }

*[plus] dispatchable hydro firm capacity
    + sum{(i,v)$[hydro_d(i)$valcap(i,v,r,t)],
          CAP(i,v,r,t) * cap_hyd_szn_adj(i,szn,r)
         }

*[plus] imports of firm capacity
    + sum{(rr,trtype)$routes(rr,r,trtype,t),
          (1 - tranloss(rr,r,trtype)) * PRMTRADE(rr,r,trtype,szn,t)
         }

*[minus] exports of firm capacity
    - sum{(rr,trtype)$routes(r,rr,trtype,t),
          PRMTRADE(r,rr,trtype,szn,t)
         }

    =g=

*[plus] the peak demand times the planning reserve margin
    + (peakdem_static_szn(r,szn,t) + PEAK_FLEX(r,szn,t)$Sw_EFS_flex) * (1 + prm(r,t))
;


*================================
* --- TRANSMISSION CAPACITY  ---
*================================

*capacity transmission is equal to the exogenously-specified level of transmission
*plus the investment in transmission capacity
eq_CAPTRAN(r,rr,trtype,t)$[routes(r,rr,trtype,t)$tmodel(t)]..

    CAPTRAN(r,rr,trtype,t)

    =e=

* [plus] cumulative exogenous capacity (initial plus "certain" near-term projects)
* NOTE: The transmission capacity input data are defined in one direction for each region-to-region pair with the lowest region number listed first.
*       Therefore, add together the capacity for both direction to get the corridor capacity in either direction.
*       This arithmetic DOES NOT double count the corridor capacity because the capacity in one of the directions for corridor (r,rr) will be zero.
    + trancap_exog(r,rr,trtype,t)
    + trancap_exog(rr,r,trtype,t)

* [plus] all previous year's investments
* Note: The investment in capacity for corridor (r,rr) applies to corridor (rr,r) as well.
*       However, expansion only needs to be tracked for one of the direcions (r,rr) or (rr,r).
*       Therefore, add together the investments for both direction to get the corridor investment in either direction.
*       Disallow building of new endogenous transmission link until after 2020 because prescriptions are defined through 2020 as exogenous capacity
*       Disallow the DC tie expansion
    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))$routes_inv(r,rr,trtype,tt)],
             INVTRAN(r,rr,tt,trtype)
           + INVTRAN(rr,r,tt,trtype)
         }
;

eq_prescribed_transmission(r,rr,trtype,t)$[routes_inv(r,rr,trtype,t)$tmodel(t)$(yeart(t)<firstyear_tran)]..

*all available transmission capacity expansion that is 'possible'
*note we allow for possible future transmission to accumulate
*hence the sum over all previous years
    sum{tt$[(tmodel(t) or tfix(tt))$(yeart(tt)<=yeart(t))],
         trancap_fut(r,rr,"possible",tt,trtype) + trancap_fut(rr,r,"possible",tt,trtype) }

    =g=

*must exceed the bi-directional investment along that corridor
    sum{tt$[(tmodel(t) or tfix(tt))$(yeart(tt)<=yeart(t))],
        INVTRAN(r,rr,tt,trtype) + INVTRAN(rr,r,tt,trtype) }
;

*similar to heritage reeds, the total amount of substations must fill
*all of the substation voltage class bins
eq_SubStationAccounting(r,t)$[rfeas(r)$tmodel(t)]..

*sum over all voltage classes of substation investments
    sum{vc$tscfeas(r,vc), INVSUBSTATION(r,vc,t) }

    =e=

*is equal to the total amount of AC investment, both in- and out- going
    sum{rr,
         INVTRAN(r,rr,t,"AC")$routes_inv(r,rr,"AC",t) + INVTRAN(rr,r,t,"AC")$routes_inv(rr,r,"AC",t) }
;


*investment in each voltage class cannot exceed the capacity
*of that substation bin (aka voltage class)
eq_INVTRAN_VCLimit(r,vc)$[rfeas(r)$tscfeas(r,vc)]..

*the voltage class bin's available capacity
    tsc_dat(r,"CAP",vc)

    =g=

*cannot exceed total capacity
    sum{t$[tmodel(t) or tfix(t)], INVSUBSTATION(r,vc,t) }
;


* flows cannot exceed the total transmission capacity
eq_transmission_limit(r,rr,h,t,trtype)$[tmodel(t)$routes(r,rr,trtype,t)]..

*transmission capacity must be greater than
    CAPTRAN(r,rr,trtype,t)

    =g=

*[plus] energy flows
    + FLOW(r,rr,h,t,trtype)
    + FLOW(rr,r,h,t,trtype)


*[plus] operating reserve flows (operating reserves can only be transferred across AC lines)
    + sum{ortype, OPRES_FLOW(ortype,r,rr,h,t) }$[Sw_OpRes$sameas(trtype,"AC")$opres_routes(r,rr,t)]
    + sum{ortype, OPRES_FLOW(ortype,rr,r,h,t) }$[Sw_OpRes$sameas(trtype,"AC")$opres_routes(rr,r,t)]

*[plus] curtailment flows
    + CURT_FLOW(r,rr,h,t)$Sw_CurtFlow
    + CURT_FLOW(rr,r,h,t)$Sw_CurtFlow
;


* curtailment reduction from new transmission has to be less than transmission investment times the curtailment reduction rate
eq_trans_reduct1(r,rr,h,t)$[tmodel(t)$sum{trtype, routes_inv(r,rr,trtype,t) }]..

    curt_tran(r,rr,h,t) * sum{trtype$routes_inv(r,rr,trtype,t), INVTRAN(r,rr,t,trtype) }

    =g=

    CURT_REDUCT_TRANS(r,rr,h,t)
;

* curtailment reduction from new transmission has to be less than the maximum amount allowed by Augur
eq_trans_reduct2(r,rr,h,t)$[tmodel(t)$(sum{trtype, routes(r,rr,trtype,t) } or sum{trtype, routes(rr,r,trtype,t) })]..

    curt_reduct_tran_max(r,rr,h,t)

    =g=

    CURT_REDUCT_TRANS(r,rr,h,t)
;


*=========================
* --- EMISSION POLICIES ---
*=========================

eq_emit_accounting(e,r,t)$[rfeas(r)$tmodel(t)]..

    EMIT(e,r,t)

    =e=

    sum{(i,v,h)$[valgen(i,v,r,t)],
         hours(h) * emit_rate(e,i,v,r,t) * GEN(i,v,r,h,t) } / emit_scale
;

eq_RGGI_cap(t)$[tmodel(t)$(yeart(t)>=RGGI_start_yr)$Sw_RGGI]..

    RGGICap(t) / emit_scale

    =g=

    sum{r$[RGGI_r(r)$rfeas(r)], EMIT("CO2",r,t) }
;


eq_AB32_cap(t)$[tmodel(t)$(yeart(t)>=AB32_start_yr)$Sw_AB32]..

    AB32Cap(t) / emit_scale

    =g=

    sum{r$[rfeas(r)$AB32_r(r)], EMIT("CO2",r,t) }

* ab32 import emissions intensity assumed constant at 2016 level
* here the receiving regions (rr) are the AB32 regions and the sending
* regions (r) are those that have connection with AB32 regions
    + sum{(h,r,rr,trtype)$[AB32_r(rr)$(not AB32_r(r))$routes(r,rr,trtype,t)],
         hours(h) * AB32_Import_Emit * FLOW(r,rr,h,t,trtype) } / emit_scale
;

* traded emissions among states in each trading group need
* to be less than the sum of all the state caps within that trading group
eq_CSAPR_Budget(csapr_group,t)$[Sw_CSAPR$tmodel(t)$(yeart(t)>=csapr_startyr)]..

*the accumulation of states csapr cap for the budget category
    sum{st$[stfeas(st)$csapr_group_st(csapr_group,st)],csapr_cap(st,"budget")} / emit_scale

    =g=

*must exceed the summed-over-state hourly-weighted nox emissions by csapr group
    sum{st$csapr_group_st(csapr_group,st),
      sum{(i,v,h,r)$[r_st(r,st)$valgen(i,v,r,t)],
         h_weight_csapr(h) * hours(h) * emit_rate("NOX",i,v,r,t) * GEN(i,v,r,h,t)  / emit_scale
       }
      }
;

* along with the cap on trading groups, each state has
* a maximum amount of NOX emissions during ozone season
eq_CSAPR_Assurance(st,t)$[stfeas(st)$(yeart(t)>=csapr_startyr)
                         $csapr_cap(st,"Assurance")$tmodel(t)]..

*the state level assurance cap
    csapr_cap(st,"assurance") / emit_scale

    =g=

*must exceed the csapr-hourly-weighted nox emissions by state
    sum{(i,v,h,r)$[r_st(r,st)$valgen(i,v,r,t)],
      h_weight_csapr(h) * hours(h) * emit_rate("NOX",i,v,r,t) * GEN(i,v,r,h,t) / emit_scale
    }
;


eq_emit_rate_limit(e,r,t)$[(yeart(t)>=CarbPolicyStartyear)$emit_rate_con(e,r,t)
                          $tmodel(t)$rfeas(r)]..

    emit_rate_limit(e,r,t) * (
         sum{(i,v,h)$[valgen(i,v,r,t)],  hours(h) * GEN(i,v,r,h,t) }
    ) / emit_scale

    =g=

    EMIT(e,r,t)
;


eq_annual_cap(e,t)$[emit_cap(e,t)$tmodel(t)$Sw_AnnualCap]..

*exogenous cap
    emit_cap(e,t) / emit_scale

    =g=

*must exceed annual endogenous emissions
    sum{r$rfeas(r), emit(e,r,t) }
;


eq_bankborrowcap(e)$[Sw_BankBorrowCap$sum{t, emit_cap(e,t) }]..

*weighted exogenous emissions
    sum{t$[tmodel(t)$emit_cap(e,t)],
        yearweight(t) * emit_cap(e,t) } / emit_scale

    =g=

* must exceed weighted endogenous emissions
    sum{(r,t)$[tmodel(t)$rfeas(r)$emit_cap(e,t)],
        yearweight(t) * EMIT(e,r,t) }
;


*==========================
* --- RPS CONSTRAINTS ---
*==========================

eq_REC_Generation(RPSCat,i,st,t)$[stfeas(st)$(not tfirst(t))$tmodel(t)
                                 $Sw_StateRPS$(yeart(t)>=RPS_StartYear)
                                 $(not sameas(RPSCat,"RPS_Bundled"))
                                 $(not sameas(RPSCat,"CES_Bundled"))]..

*RECS are computed as the total annual generation from a technology
*hydro is the only technology adjusted by RPSTechMult
    sum{(v,r,h)$(valgen(i,v,r,t)$RecTech(RPSCat,st,i,t)$rfeas(r)$r_st(r,st)),
         RPSTechMult(RPSCat,i,st) * hours(h) * GEN(i,v,r,h,t) }

    =g=

* Generation must be greater than RECS sent to all states that can trade
    sum{ast$(RecMap(i,RPSCat,st,ast,t)$stfeas(ast)),RECS(RPSCat,i,st,ast,t) }
* RPS_Bundled RECS and RPS_All RECS can meet the same requirement
* therefore lumping them together to avoid double-counting
    + sum{ast$(RecMap(i,"RPS_Bundled",st,ast,t)$stfeas(ast)),
          RECS("RPS_Bundled",i,st,ast,t) }$[sameas(RPSCat,"RPS_All")]

*same logic as bundled RPS RECS is applied to the bundled CES RECS
    + sum{ast$(RecMap(i,"CES_Bundled",st,ast,t)$stfeas(ast)),
          RECS("CES_Bundled",i,st,ast,t) }$[sameas(RPSCat,"CES")]

;


* note that the bundled rpscat can be included
* to comply with the RPS_All categeory
* but it is not in itself explicit requirement
eq_REC_Requirement(RPSCat,st,t)$[RecStates(RPSCat,st,t)$(not tfirst(t))
                                $stfeas(st)$tmodel(t)$Sw_StateRPS$(yeart(t)>=RPS_StartYear)
                                $(not sameas(RPSCat,"RPS_Bundled"))
                                $(not sameas(RPSCat,"CES_Bundled"))]..

* RECs owned (i.e. imported and generated/used in state)
    sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$stfeas(ast)],
         RECS(RPSCat,i,ast,st,t) }

* bundled RECS can also be used to meet the RPS_All requirements
    + sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(ast,st))],
         RECS("RPS_Bundled",i,ast,st,t) }$[sameas(RPSCat,"RPS_All")]

* bundled CES credits can also be used to meet the CES requirements
    + sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(ast,st))],
         RECS("CES_Bundled",i,ast,st,t) }$[sameas(RPSCat,"CES")]


* ACP credits can also be purchased
    + ACP_Purchases(rpscat,st,t)

    =g=

* note here we do not pre-define the rec requirement since load_exog(r,h,t)
* changes when sent to/from the demand side
    RecPerc(RPSCat,st,t) *
    sum{(r,h)$[rfeas(r)$r_st(r,st)],
        hours(h) *
        ( (LOAD(r,h,t) - can_exports_h(r,h,t)) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
       }
;

eq_REC_BundleLimit(RPSCat,st,ast,t)$[stfeas(st)$stfeas(ast)$tmodel(t)
                              $(not sameas(st,ast)$Sw_StateRPS)
                              $(sum{i,RecMap(i,RPSCat,st,ast,t)})
                              $(sameas(RPSCat,"RPS_Bundled") or sameas(RPSCat,"CES_Bundled"))
                              $(yeart(t)>=RPS_StartYear)]..

*amount of net transmission flows from state st to state ast
    sum{(h,r,rr,trtype)$[r_st(r,st)$r_st(rr,ast)$routes(r,rr,trtype,t)],
          hours(h) * FLOW(r,rr,h,t,trtype)
      }

    =g=
* must be greater than bundled RECS
    sum{i$RecMap(i,RPSCat,st,ast,t),
        RECS(RPSCat,i,st,ast,t)}
;


eq_REC_unbundledLimit(RPSCat,st,t)$[RPS_unbundled_limit(st)$tmodel(t)$stfeas(st)
                            $(yeart(t)>=RPS_StartYear)$Sw_StateRPS
                            $(sameas(RPSCat,"RPS_All") or sameas(RPSCat,"CES"))]..
*the limit on unbundled RECS times the REC requirement
      RPS_unbundled_limit(st) * RecPerc(RPSCat,st,t) *
        sum{(r,h)$[rfeas(r)$r_st(r,st)],
            hours(h) *
            ( (LOAD(r,h,t) - can_exports_h(r,h,t)) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
           }
      =g=

*needs to be greater than the unbundled recs
*NB unbundled RECS are computed as all imported RECS minus bundled RECS
    sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS(RPSCat,i,ast,st,t)}

    - sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("RPS_Bundled",i,ast,st,t)}$sameas(RPSCat,"RPS_All")

    - sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("CES_Bundled",i,ast,st,t)}$sameas(RPSCat,"CES")
;



eq_REC_ooslim(RPSCat,st,t)$[RecStates(RPSCat,st,t)$(yeart(t)>=RPS_StartYear)
                           $RPS_oosfrac(st)$stfeas(st)$tmodel(t)$Sw_StateRPS
                           $(not sameas(RPSCat,"RPS_Bundled"))
                           $(not sameas(RPSCat,"CES_Bundled"))]..

*the fraction of imported recs times the requirement
    RPS_oosfrac(st) * RecPerc(RPSCat,st,t) *
        sum{(r,h)$[rfeas(r)$r_st(r,st)],
            hours(h) *
            ( (LOAD(r,h,t) - can_exports_h(r,h,t)) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
           }
    =g=

*imported RECs - note that the not sameas(st,ast) indicates they are not generated in-state
    sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS(RPSCat,i,ast,st,t)
       }

    + sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("RPS_Bundled",i,ast,st,t)
       }$sameas(RPSCat,"RPS_All")

    + sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("CES_Bundled",i,ast,st,t)
       }$sameas(RPSCat,"CES")

;


*exports must be less than RECS generated
eq_REC_launder(RPSCat,st,t)$[RecStates(RPSCat,st,t)$(not tfirst(t))$(yeart(t)>=RPS_StartYear)
                               $tmodel(t)$stfeas(st)$Sw_StateRPS
                               $(not sameas(RPSCat,"RPS_Bundled"))
                               $(not sameas(RPSCat,"CES_Bundled"))]..

*in-state REC generation
    sum{(i,v,r,h)$(valgen(i,v,r,t)$RecTech(RPSCat,st,i,t)$rfeas(r)$r_st(r,st)),
         hours(h) * GEN(i,v,r,h,t) }

    =g=

*exported RECS - NB the conditional that st!=ast
    sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
         RECS(RPSCat,i,st,ast,t) }

    + sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("RPS_Bundled",i,ast,st,t)
       }$sameas(RPSCat,"RPS_All")

    + sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("CES_Bundled",i,ast,st,t)
       }$sameas(RPSCat,"CES")


;


eq_RPS_OFSWind(st,t)$[tmodel(t)$stfeas(st)$offshore_cap_req(st,t)$Sw_StateRPS
                      $sum{r$r_st(r,st),sum{(i,v,rr)$[ofswind(i)$cap_agg(r,rr)],valcap(i,v,rr,t)}}]..

    sum{r$r_st(r,st),
      sum{(i,v,rr)$[valcap(i,v,rr,t)$ofswind(i)$cap_agg(r,rr)],
          CAP(i,v,rr,t)
         }
       }

    =g=

    offshore_cap_req(st,t)
;


eq_batterymandate(r,t)$[rfeas(r)$tmodel(t)$batterymandate(r,t)
                         $Sw_BatteryMandate]..
*battery capacity
    sum{(i,v)$[valcap(i,v,r,t)$battery(i)], CAP(i,v,r,t) }

    =g=

*must be greater than the indicated level
    batterymandate(r,t)
;


eq_national_gen(t)$[tmodel(t)$national_rps_frac(t)$Sw_GenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[nat_gen_tech_frac(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h) * nat_gen_tech_frac(i)}

    =g=

*must exceed the mandated percentage [times]
    national_rps_frac(t) * (

* if Sw_GenMandate = 1, then apply the fraction to the bus bar load
    (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )$[Sw_GenMandate = 1]

* if Sw_GenMandate = 2, then apply the fraction to the end use load
    + (sum{(r,h)$rfeas(r),
        hours(h) *
        ( (LOAD(r,h,t) - can_exports_h(r,h,t)) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
       })$[Sw_GenMandate = 2]
    )
;


eq_national_nucgen(t)$[tmodel(t)$(yeart(t) >= firstyear("nuclear"))$Sw_ConstantGenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[valgen(i,v,r,t)$nuclear(i)],
        GEN(i,v,r,h,t) * hours(h)}

    =e=

*must equal the mandated percentage [times]
    0.2 * (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$routes(rr,r,trtype,t), (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )
;

eq_national_coalgen(t)$[tmodel(t)$(yeart(t) >= firstyear("coal-new"))$Sw_ConstantGenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[coal(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h)}

    =e=

*must equal the mandated percentage [times]
    0.2 * (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )
;

eq_national_pvgen(t)$[tmodel(t)$(yeart(t) >= firstyear("upv_1"))$Sw_ConstantGenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[pv(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h)}

    =e=

*must equal the mandated percentage [times]
    0.03 * (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )
;

eq_national_cspgen(t)$[tmodel(t)$(yeart(t) >= firstyear("csp1_1"))$Sw_ConstantGenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[csp(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h)}

    =e=

*must equal the mandated percentage [times]
    0.001 * (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )
;

eq_national_windgen(t)$[tmodel(t)$(yeart(t) >= firstyear("wind-ons_1"))$Sw_ConstantGenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[wind(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h)}

    =e=

*must equal the mandated percentage [times]
    0.08 * (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )
;

eq_national_hydrogen(t)$[tmodel(t)$(yeart(t) >= firstyear("Hydro"))$Sw_ConstantGenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[hydro(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h)}

    =e=

*must equal the mandated percentage [times]
    0.066 * (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )
;

eq_national_natgasgen(t)$[tmodel(t)$(yeart(t) >= firstyear("gas-cc"))$Sw_ConstantGenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[gas(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h)}

    =e=

*must equal the mandated percentage [times]
    0.400 * (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )
;

eq_national_ogsgen(t)$[tmodel(t)$(yeart(t) >= 2020)$Sw_ConstantGenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[sameas(i,'o-g-s')$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h)}

    =e=

*must equal the mandated percentage [times]
    0.005 * (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )
;


*trade of planning reserve margin capacity cannot exceed the transmission line's available capacity
eq_PRMTRADELimit_RE(r,rr,trtype,szn,t)$[tmodel(t)$rfeas(r)$rfeas(rr)$national_rps_cap(t)
                                     $routes(r,rr,trtype,t)$Sw_ReserveMargin$Sw_RenMandateCap]..

*[plus] transmission capacity
    + CAPTRAN(r,rr,trtype,t)

    =g=

*[plus] firm capacity traded between regions
    + PRMTRADE_RE(r,rr,trtype,szn,t)
;


eq_national_rps_resmarg(r,szn,t)$[tmodel(t)$rfeas(r)$Sw_RenMandateCap$Sw_ReserveMargin$national_rps_cap(t)]..

*[plus] sum of all non-rsc and non-storage capacity
    + sum{(i,v)$[valcap(i,v,r,t)$clean_energy(i)$(not vre(i))$(not hydro(i))$(not storage(i))],
          CAP(i,v,r,t)
         }

*[plus] firm capacity from existing VRE or CSP
*only used in sequential solve case (otherwise cc_old = 0)
    + sum{(i,rr)$[(vre(i) or csp(i))$cap_agg(r,rr)$rfeas_cap(rr)],
          cc_old(i,rr,szn,t)
         }

*[plus] marginal capacity credit of VRE and csp times new investment
*only used in sequential solve case (otherwise m_cc_mar = 0)
*Note: new distpv is included with cc_old
    + sum{(i,v,rr)$[cap_agg(r,rr)$(vre(i) or csp(i))$valinv(i,v,rr,t)],
          m_cc_mar(i,rr,szn,t) * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] firm capacity contribution from all binned storage capacity
*for now this is just battery, pumped-hydro, CAES, and H2
    + sum{(i,v,rr,sdbin)$[cap_agg(r,rr)$storage_no_csp(i)$valcap(i,v,rr,t)],
          cc_storage(i,sdbin) * CAP_SDBIN(i,v,rr,szn,sdbin,t)
         }

*[plus] average capacity credit times capacity of VRE and storage
*used in rolling window and full intertemporal solve (otherwise cc_int = 0)
    + sum{(i,v,rr)$[(vre(i) or storage(i))$valcap(i,v,rr,t)$cap_agg(r,rr)],
          cc_int(i,v,rr,szn,t) * CAP(i,v,rr,t)
         }

*[plus] excess capacity credit
*used in rolling window and full intertemporal solve when using marginals for cc_int (otherwise cc_excess = 0)
    + sum{(i,rr)$[(vre(i) or storage(i))$cap_agg(r,rr)$rfeas_cap(rr)],
          cc_excess(i,rr,szn,t)
         }

*[plus] firm capacity of non-dispatchable hydro
* nb: hydro_nd generation does not fluctuate
* within a seasons set of hours
    + sum{(i,v,h)$[hydro_nd(i)$valgen(i,v,r,t)$h_szn_prm(h,szn)],
          GEN(i,v,r,h,t)
         }

*[plus] dispatchable hydro firm capacity
    + sum{(i,v)$[hydro_d(i)$valcap(i,v,r,t)],
          CAP(i,v,r,t) * cap_hyd_szn_adj(i,szn,r)
         }

*[plus] imports of firm capacity
    + sum{(rr,trtype)$[routes(rr,r,trtype,t)$rfeas(rr)],
          (1 - tranloss(rr,r,trtype)) * PRMTRADE_RE(rr,r,trtype,szn,t)
         }

*[minus] exports of firm capacity
    - sum{(rr,trtype)$[routes(r,rr,trtype,t)$rfeas(rr)],
          PRMTRADE_RE(r,rr,trtype,szn,t)
         }

    =g=

*[plus] the peak demand times the planning reserve margin
    + (peakdem_static_szn(r,szn,t) + PEAK_FLEX(r,szn,t)$Sw_EFS_flex) * (1 + prm(r,t)) * national_rps_cap(t) * (1$[Sw_GenMandate = 1] + (1.0 - distloss)$[Sw_GenMandate = 2])
;

*====================================
* --- FUEL SUPPLY CURVES ---
*====================================


*gas used from each bin is the sum of all gas used
eq_gasused(cendiv,h,t)$[tmodel(t)$((Sw_GasCurve=0) or (Sw_GasCurve=3))$cdfeas(cendiv)]..

    sum{gb,GASUSED(cendiv,gb,h,t) }

    =e=

    sum{(i,v,r)$[valgen(i,v,r,t)$gas(i)$rfeas(r)$r_cendiv(r,cendiv)],
         heat_rate(i,v,r,t) * GEN(i,v,r,h,t) } / gas_scale
;

* gas from each bin needs to less than its capacity
eq_gasbinlimit(cendiv,gb,t)$[tmodel(t)$cdfeas(cendiv)$(Sw_GasCurve=0)]..

    gaslimit(cendiv,gb,t)

    =g=

    sum{h, hours(h) * GASUSED(cendiv,gb,h,t) }
;

eq_gasbinlimit_nat(gb,t)$[tmodel(t)$(Sw_GasCurve=3)]..

   gaslimit_nat(gb,t)

   =g=

   sum{(h,cendiv)$cdfeas(cendiv),
       hours(h) * GASUSED(cendiv,gb,h,t)
      }
;

eq_gasaccounting_regional(cendiv,t)$[cdfeas(cendiv)$tmodel(t)$(Sw_GasCurve=1)]..

    sum{fuelbin,VGASBINQ_REGIONAL(fuelbin,cendiv,t) }

    =e=

    sum{(i,v,r,h)$[valgen(i,v,r,t)$gas(i)$r_cendiv(r,cendiv)$rfeas(r)],
         hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t)
       }
;


eq_gasaccounting_national(t)$[tmodel(t)$(Sw_GasCurve=1)]..

    sum{fuelbin,VGASBINQ_NATIONAL(fuelbin,t)}

    =e=

    sum{(i,v,r,h)$[valgen(i,v,r,t)$gas(i)$rfeas(r)],
         hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t)
       }
;


eq_gasbinlimit_regional(fuelbin,cendiv,t)$[cdfeas(cendiv)$tmodel(t)$(Sw_GasCurve=1)]..

    Gasbinwidth_regional(fuelbin,cendiv,t)

    =g=

    VGASBINQ_REGIONAL(fuelbin,cendiv,t)
;


eq_gasbinlimit_national(fuelbin,t)$[tmodel(t)$(Sw_GasCurve=1)]..

    Gasbinwidth_national(fuelbin,t)

    =g=

    VGASBINQ_NATIONAL(fuelbin,t)
;


*===========
* bio curve
*===========

eq_bioused(r,t)$[rfeas(r)$tmodel(t)]..

    sum{bioclass,BIOUSED(bioclass,r,t) }

    =e=

*biopower generation
    + sum{(i,v,h)$[valgen(i,v,r,t)$bio(i)],
        hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t) }


*portion of cofire generation that is from bio resources
*here we assumed it fixed at 15% (for now)
    + sum{(i,v,h)$[cofire(i)$valgen(i,v,r,t)],
         bio_cofire_perc * hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t) }
;

eq_biousedlimit(bioclass,r,t)$[rfeas(r)$tmodel(t)]..

    biosupply(r,"CAP",bioclass)

    =g=

    BIOUSED(bioclass,r,t)
;


*============================
* --- STORAGE CONSTRAINTS ---
*============================

*storage use cannot exceed capacity
eq_storage_capacity(i,v,r,h,t)$[valgen(i,v,r,t)$storage_no_csp(i)$tmodel(t)]..

    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
        CAP(i,v,rr,t) * avail(i,v,h)
       }

    =g=

    GEN(i,v,r,h,t)

    + sum{src, STORAGE_IN(i,v,r,h,src,t) }

    + sum{ortype, OPRES(ortype,i,v,r,h,t) }
;

* The daily storage level in the next time-slice (h+1) must equal the
*  daily storage level in the current time-slice (h)
*  plus daily net charging in the current time-slice (accounting for losses).
*  CSP with storage energy accounting is also covered by this constraint.
eq_storage_level(i,v,r,h,t)$[valgen(i,v,r,t)$storage(i)$(not storage_h2(i))$tmodel(t)]..

    sum{(hh)$[nexth(h,hh)], STORAGE_LEVEL(i,v,r,hh,t) }

    =e=

      STORAGE_LEVEL(i,v,r,h,t)

    + storage_eff(i,t) *  hours_daily(h) * (
          sum{src, STORAGE_IN(i,v,r,h,src,t) }$storage_no_csp(i)

        + sum{rr$[CSP_Storage(i)$valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
            CAP(i,v,rr,t) * csp_sm(i) * m_cf(i,v,rr,h,t)
           }
      )

    - hours_daily(h) * GEN(i,v,r,h,t)
;

*storage charging must exceed OR contributions for thermal storage
eq_storage_thermalres(i,v,r,h,t)$[valgen(i,v,r,t)$Thermal_Storage(i)
                                 $tmodel(t)$Sw_OpRes]..

    sum{src, STORAGE_IN(i,v,r,h,src,t) }

    =g=

    sum{ortype, OPRES(ortype,i,v,r,h,t) }
;


*batteries and CSP-TES are limited by their duration for each normalized hour per season
eq_storage_duration(i,v,r,h,t)$[valgen(i,v,r,t)$(battery(i) or CSP_Storage(i))
                               $tmodel(t)]..

    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
        storage_duration(i) * CAP(i,v,rr,t)}

    =g=

    STORAGE_LEVEL(i,v,r,h,t)
;


*lower bound on storage charging
eq_storage_in_min(r,h,t)$[sum{(i,v)$storage_no_csp(i),valgen(i,v,r,t)}$tmodel(t)]..

    sum{(i,v)$storage_no_csp(i),STORAGE_IN(i,v,r,h,"other",t)}

    =g=

    storage_in_min(r,h,t)
;


*upper bound on storage charging from a given source
eq_storage_in_max(r,h,src,t)$[rfeas(r)$rb(r)$(not sameas(src,"other"))$tmodel(t)]..

*[plus] the marginal curtailment from new src
    sum{(i,v,rr)$[cap_agg(r,rr)$valinv(i,v,rr,t)$i_src(i,src)],
              m_cf(i,v,rr,h,t) * curt_marg(i,rr,h,t)
              * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
       }$[not sameas(src,"old")]

*[plus] the existing curtailment from "old" src
    + curt_old(r,h,t)$sameas(src,"old")

    =g=

    sum{(i,v)$[storage_no_csp(i)$valgen(i,v,r,t)], STORAGE_IN(i,v,r,h,src,t) }
;


*============================================
* --- Seasonal Hydrogen Storage Equations ---
*============================================
*===================================
* --- CANADIAN IMPORTS EQUATIONS ---
*===================================

eq_storage_h2_def_total_energy_held(i,v,r,szn,t)$[valgen(i,v,r,t)$storage_h2(i)$tmodel(t)$Sw_Storage$Sw_SeasonalStorage]..
* (+) Total energy held in storage during season 'szn'
TEH(i,v,r,szn,t)
=e=
* (+) Total energy stored from season 'szn2' and used in 'szn3' that must pass through season 'szn'
sum{(szn2,szn3)$held(szn,szn2,szn3), TES(i,v,r,szn2,szn3,t)} ;

* ------------------------------------------------------------

eq_storage_h2_ub_start_energy_season(i,v,r,szn,t)$[valgen(i,v,r,t)$storage_h2(i)$tmodel(t)$Sw_Storage$Sw_SeasonalStorage]..
* (+) Total energy stored from all seasons 'szn2' and moved to season 'szn'
+ sum{szn2$[ord(szn2)<>ord(szn)], TES(i,v,r,szn2,szn,t)}
* (+) Total energy held in storage during season 'szn'
+ TEH(i,v,r,szn,t)
* (+) Daily energy stored and moved within the same season 'szn'
+ TES(i,v,r,szn,szn,t) / numdays(szn)
=l=
* storage energy capacity
+ storage_duration(i) * sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)], CAP(i,v,rr,t)}
;

* ------------------------------------------------------------

eq_storage_h2_ub_end_energy_season(i,v,r,szn,t)$[valgen(i,v,r,t)$storage_h2(i)$tmodel(t)$Sw_Storage$Sw_SeasonalStorage]..
* (+) Total energy stored from season 'szn' and moved to a all seasons 'szn2'
+ sum{szn2$[ord(szn2)<>ord(szn)], TES(i,v,r,szn,szn2,t)}
* (+) Total energy held in storage during season 'szn'
+ TEH(i,v,r,szn,t)
* (+) Daily energy stored and moved within the same season 'szn'
+ TES(i,v,r,szn,szn,t) / numdays(szn)
=l=
* storage energy capacity
+ storage_duration(i) * sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)], CAP(i,v,rr,t)}
;

* ------------------------------------------------------------

eq_storage_h2_link_season_timeslice_charge(i,v,r,szn,t)$[valgen(i,v,r,t)$storage_h2(i)$tmodel(t)$Sw_Storage$Sw_SeasonalStorage]..
* Total energy stored from season 'szn' and sent to all seasons 'szn2'
sum{szn2, TES(i,v,r,szn,szn2,t)}
=e=
* total charge in all timeslices 'h' that are in 'szn'
sum{(src,h)$h_szn(h,szn), STORAGE_IN(i,v,r,h,src,t) * hours(h)}
;

* ------------------------------------------------------------

eq_storage_h2_link_season_timeslice_discharge(i,v,r,szn,t)$[valgen(i,v,r,t)$storage_h2(i)$tmodel(t)$Sw_Storage$Sw_SeasonalStorage]..
* Total energy stored in all seasons 'szn2' and sent to season 'szn'
storage_eff(i,t) * sum{szn2, TES(i,v,r,szn2,szn,t)}
=e=
* total daily discharge in all timeslices 'h' that are in 'szn'
sum{h$h_szn(h,szn), GEN(i,v,r,h,t) * hours(h)}
;

* ------------------------------------------------------------

* THIS EQUATION IS NOT NEEDED BECAUSE IT IS REDUNDANT, BUT INCLUDING IT FOR NOW

eq_storage_h2_balance_annual(i,v,r,t)$[valgen(i,v,r,t)$storage_h2(i)$tmodel(t)$Sw_Storage$Sw_SeasonalStorage]..
* Total energy charged (accounting for efficiency loss)
    storage_eff(i,t) * sum{(h,src), hours(h) * STORAGE_IN(i,v,r,h,src,t) }
    =e=
* Total energy discharged
    sum{h, hours(h) * GEN(i,v,r,h,t)}
;

eq_Canadian_Imports(r,szn,t)$[can_imports_szn(r,szn,t)$tmodel(t)]..

    can_imports_szn(r,szn,t)

    =g=

    sum{(i,v,h)$[canada(i)$valgen(i,v,r,t)$h_szn(h,szn)], GEN(i,v,r,h,t) * hours(h) }
;

*==========================
* --- WATER CONSTRAINTS ---
*==========================

*water accounting for all valid power plants for generation where usage is both for cooling and/or non-cooling purposes
eq_water_accounting(i,v,w,r,h,t)$[i_water(i)$valgen(i,v,r,t)$tmodel(t)$Sw_WaterMain]..

    WAT(i,v,w,r,h,t)

    =e=

    GEN(i,v,r,h,t) * hours(h) * water_rate(i,w,r) / 1E6
*division by 1E6 to convert gal of water_rate(i,w,r) to Mgal
;

*total water access is determined by total capacity
eq_water_capacity_total(i,v,r,t)$[rfeas(r)$tmodel(t)$valcap(i,v,r,t)$i_water_cooling(i)$Sw_WaterMain$Sw_WaterCapacity]..

    WATCAP(i,v,r,t)

    =e=
*require enough water capacity to allow 100% capacity factor (8760 hour operation)
    (8760/1E6) * sum{(w,rr)$[i_w(i,w)$rfeas_cap(rr)$cap_agg(r,rr)$valcap(i,v,rr,t)], CAP(i,v,rr,t) * water_rate(i,w,rr) }
*division by 1E6 to convert gal of water_rate(i,w,r) to Mgal
;
*total water access must not exceed supply
eq_water_capacity_limit(wst,r,t)$[rfeas(r)$tmodel(t)$Sw_WaterMain$Sw_WaterCapacity]..

    m_watsc_dat(wst,"cap",r,t)

    + WATER_CAPACITY_LIMIT_SLACK(wst,r,t)

    =g=

    sum{(i,v)$[i_wst(i,wst)$valcap(i,v,r,t)], WATCAP(i,v,r,t) }
;

*water use must not exceed available access
eq_water_use_limit(i,v,w,r,szn,t)$[i_water_cooling(i)$valgen(i,v,r,t)$tmodel(t)$i_w(i,w)$Sw_WaterMain$Sw_WaterCapacity$Sw_WaterUse]..

    WATCAP(i,v,r,t) *sum{wst$i_wst(i,wst), watsa(wst,r,szn,t) }

    =g=

    sum{h$h_szn(h,szn), WAT(i,v,w,r,h,t) }
;

