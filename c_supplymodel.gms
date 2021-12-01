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

* load variable - set equal to load_exog to compute holistic marginal price
  LOAD(r,allh,t)                  "--MWh-- busbar load for each balancing region"
  EVLOAD(r,allh,t)                "--MWh-- busbar load specific to EVs"
  FLEX(flex_type,r,allh,t)        "--MWh-- flexible load shifted to each timeslice"
  PEAK_FLEX(r,allszn,t)           "--MWh-- peak busbar load adjustment based on load flexibility"

* capacity and investment variables
  CAP_SDBIN(i,v,r,allszn,sdbin,t)  "--MW-- generation capacity by storage duration bin for relevant technologies"
  CAP(i,v,r,t)                     "--MW-- total generation capacity in MWac (MWdc for PV); PV capacity of hybrid PV+battery"
  INV(i,v,r,t)                     "--MW-- generation capacity add in year t"
  EXTRA_PRESCRIP(pcat,r,t)         "--MW-- builds beyond those prescribed once allowed in firstyear(pcat) - exceptions for gas-ct, wind-ons, and wind-ofs"
  INV_CAP_UP(i,v,r,rscbin,t)       "--MW-- upsized generation capacity addition in year t"
  INV_ENER_UP(i,v,r,rscbin,t)      "--MW-- upsized energy addition in year t using capacity factor to convert to capacity units"
  INV_REFURB(i,v,r,t)              "--MW-- investment in refurbishments of technologies that use a resource supply curve"
  INV_RSC(i,v,r,rscbin,t)          "--MW-- investment in technologies that use a resource supply curve"
  UPGRADES(i,v,r,t)                "--MW-- investments in upgraded capacity from ii to i"

* The units for  all of the operatinal variables are average MW or MWh/time-slice hours
* generation and storage variables
  GEN(i,v,r,allh,t)                   "--MW-- electricity generation (post-curtailment) in hour h"
  GEN_PVB_P(i,v,r,allh,t)             "--MW-- average PV generation from hybrid PV+Battery in hour h"
  GEN_PVB_B(i,v,r,allh,t)             "--MW-- average Battery generation (discharge) from hybrid PV+Battery in hour h"
  CURT(r,allh,t)                      "--MW-- curtailment from vre generators in hour h"
  CURT_SLACK(r,allh,t)                "--MW-- curtailment slack used in historical years in flex representation"
  CURT_REDUCT_TRANS(r,rr,allh,t)      "--MW-- curtailment reduction in r from building new transmission to rr"
  MINGEN(r,allszn,t)                  "--MW-- minimum generation level in each season"
  STORAGE_IN(i,v,r,allh,src,t)        "--MW-- storage charging in hour h that is charging from a given source technology; not used for CSP-TES"
  STORAGE_IN_PVB_P(i,v,r,allh,src,t)  "--MW-- PV+Battery storage charging in hour h that is charging from a coupled PV technology"
  STORAGE_IN_PVB_G(i,v,r,allh,src,t)  "--MW-- PV+Battery storage charging in hour h that is charging from a source on the grid"
  STORAGE_LEVEL(i,v,r,allh,t)         "--MWh per day-- storage level in hour h"
  DR_SHIFT(i,v,r,allh,allhh,src,t)    "--MWh-- annual demand response load shifted to timeslice h from timeslice hh"
  DR_SHED(i,v,r,allh,t)               "--MWh-- annual demand response load shed from timeslice h"
  PRODUCE(p,i,v,r,allh,t)             "--tonnes/hour-- production of hydrogen or DAC capture"
  LAST_HOUR_SOC(i,v,r,allh,t)         "--MWh-- last hour state of charge when running flex without infinite loop"

* trade variables
  FLOW(r,rr,allh,t,trtype)        "--MW-- electricity flow on transmission lines in hour h"
  OPRES_FLOW(ortype,r,rr,allh,t)  "--MW-- interregional trade of operating reserves by operating reserve type"
  CURT_FLOW(r,rr,allh,t)          "--MW-- interregional trade of curtailment"
  PRMTRADE(r,rr,trtype,allszn,t)  "--MW-- planning reserve margin capacity traded from r to rr"

* operating reserve variables
  OPRES(ortype,i,v,r,allh,t)      "--MW-- operating reserves by type"

* variable fuel amounts
  GASUSED(cendiv,gb,allh,t)             "--MMBtu-- total gas used by gas bin",
  VGASBINQ_NATIONAL(fuelbin,t)          "--MMBtu-- National quantity of gas by bin"
  VGASBINQ_REGIONAL(fuelbin,cendiv,t)   "--MMBtu-- Regional (census divisions) quantity of gas by bin"
  BIOUSED(bioclass,r,t)                 "--MMBtu-- total biomass used by biomass class"

* RECS variables
  RECS(RPSCat,i,st,ast,t)               "--MWh-- renewable energy credits from state s to state ss",
  ACP_Purchases(RPSCat,st,t)            "--MWh-- purchases of ACP credits to meet the RPS constraints",

* transmission variables
  CAPTRAN(r,rr,trtype,t)                         "--MW-- capacity of transmission"
  INVTRAN(r,rr,t,trtype)                         "--MW-- investment in transmission capacity"
  INVSUBSTATION(r,vc,t)                          "--MW-- substation investment--"
  CAP_CONVERTER(r,t)                             "--MW-- VSC AC/DC converter capacity"
  INV_CONVERTER(r,t)                             "--MW-- investment in AC/DC converter capacity"
  CONVERSION(r,allh,intype,outtype,t)            "--MW-- conversion of AC->DC or DC->AC"
  CONVERSION_PRM(r,allszn,intype,outtype,t)      "--MW-- planning reserve margin capacity sent through VSC AC/DC converters"

* hydrogen-specific variables
  H2_FLOW(r,rr,p,allh,t)                "--tonnes-- interregional flow of hydrogen"
  H2_TRANSPORT_INV(r,rr,t)              "--tonnes-- investment in interregional hydrogen transmission capacity"

* water climate variables
  WATCAP(i,v,r,t)                        "--million gallons/year; Mgal/yr-- total water access capacity available in terms of withdraw/consumption per year"
  WAT(i,v,w,r,allh,t)                    "--Mgal-- quantity of water withdrawn or consumed in hour h"
  WATER_CAPACITY_LIMIT_SLACK(wst,r,t)    "--Mgal/yr-- insufficient water supply in region r, of water type wst, in year t "
;

Variables
* with negative emissions technologies (e.g. BECCS, DAC) - emissions 
* can become negative thus not restrictied to the positive domain
  EMIT(e,r,t)                            "----tons (thousand metric tons for CO2)-- total emissions in a region (note: units dependent on emit_scale)"
;

*========================================
* -- Supply Side Equation Declaration --
*========================================
EQUATION

* load constraint to compute proper marginal value
 eq_loadcon(r,allh,t)                    "--MW-- load constraint used for computing the marginal energy price"
 eq_evloadcon(r,allszn,t)                "--MWh-- mapping of seasonal EV load to each timeslice"

* load flexibility constraints
 eq_load_flex_day(flex_type,r,allszn,t)  "--MWh-- total flexible load in each season is equal to the exogenously-specified flexible load"
 eq_load_flex1(flex_type,r,allh,t)       "--MWh-- exogenously-specified flexible demand (load_exog_flex) must be served by flexible load (FLEX)"
 eq_load_flex2(flex_type,r,allh,t)       "--MWh-- flexible load (FLEX) can't exceed exogenously-specified flexible demand (load_exog_flex)"
 eq_load_flex_peak(r,allh,allszn,t)      "--MWh-- adjust peak demand as needed based on the load flexibility (FLEX)"

* capital stock constraints
 eq_cap_init_noret(i,v,r,t)               "--MW-- Existing capacity that cannot be retired is equal to exogenously-specified amount"
 eq_cap_init_retmo(i,v,r,t)               "--MW-- Existing capacity that can be retired must be monotonically decreasing"
 eq_cap_init_retub(i,v,r,t)               "--MW-- Existing capacity that can be retired is less than or equal to exogenously-specified amount"
 eq_cap_new_noret(i,v,r,t)                "--MW-- New capacity that cannot be retired is equal to sum of all previous years investment"
 eq_cap_new_retmo(i,v,r,t)                "--MW-- New capacity that can be retired must be monotonically decreasing unless increased by investment"
 eq_cap_new_retub(i,v,r,t)                "--MW-- New capacity that can be retired is less than or equal to all previous years investment"
 eq_cap_up(i,v,r,rscbin,t)                "--MW-- limit on capacity upsizing"
 eq_cap_upgrade_noret(i,v,r,t)            "--MW-- For upgrade techs that do not retire, purchased upgrades are equal to the cumulative sum of previously upgraded capacity"
 eq_cap_upgrade(i,v,r,t)                  "--MW-- All purchased upgrades are greater than or equal to the sum of upgraded capacity"
 eq_ener_up(i,v,r,rscbin,t)               "--MW-- limit on energy upsizing"
 eq_forceprescription(pcat,r,t)           "--MW-- total investment in prescribed capacity must equal amount from exogenous prescriptions"
 eq_neartermcaplimit(r,t)                 "--MW-- near-term capacity cannot be greater than projects in the pipeline"
 eq_refurblim(i,r,t)                      "--MW-- total refurbishments cannot exceed the amount of capacity that has reached the end of its life"

* renewable supply curves
 eq_rsc_inv_account(i,v,r,t)              "--MW-- INV for rsc techs is the sum over all bins of INV_RSC"
 eq_rsc_INVlim(r,i,rscbin,t)              "--MW-- total investment from each rsc bin cannot exceed the available investment"

* capacity growth limits
 eq_growthlimit_relative(tg,t)            "--MW-- relative growth limit on technologies in growlim(i)"
 eq_growthlimit_absolute(tg,t)            "--MW-- absolute growth limit on technologies in growlim(i)"

* storage capacity credit supply curves
 eq_cap_sdbin_balance(i,v,r,allszn,t)        "--MW-- total binned storage capacity must be equal to total storage capacity"
 eq_sdbin_limit(ccreg,allszn,sdbin,t)        "--MW-- binned storage capacity cannot exceed storage duration bin size"

* operation and reliability
 eq_capacity_limit_hydro_nd(i,v,r,allh,t)                "--MW-- generation limited to available capacity for non-dispatchable hydro"
 eq_capacity_limit(i,v,r,allh,t)                         "--MW-- generation limited to available capacity"
 eq_curt_gen_balance(r,allh,t)                           "--MW-- net generation and curtailment must equal gross generation"
 eq_curtailment(r,allh,t)                                "--MW-- curtailment level"
 eq_dhyd_dispatch(i,v,r,allszn,t)                        "--MWh-- dispatchable hydro seasonal energy constraint (when not allowing seasonal enregy shifting)"
 eq_dhyd_dispatch_ann(i,v,r,t)                           "--MWh-- dispatchable hydro annual energy constraint (only when allowing seasonal energy shifting)"
 eq_dhyd_dispatch_szn(i,v,r,allszn,t)                    "--MWh-- dispatchable hydro seasonal energy constraint"
 eq_min_cf(i,rto,t)                                      "--MWh-- minimum capacity factor constraint for each generator fleet, applied to (i,rto)"
 eq_mingen_lb(r,allh,allszn,t)                           "--MW-- lower bound on minimum generation level"
 eq_mingen_ub(r,allh,allszn,t)                           "--MW-- upper bound on minimum generation level"
 eq_minloading(i,v,r,allh,allhh,t)                       "--MW-- minimum loading across same-season hours"
 eq_reserve_margin(r,allszn,t)                           "--MW-- planning reserve margin requirement"
 eq_supply_demand_balance(r,allh,t)                      "--MW-- supply demand balance"
 eq_vsc_flow(r,allh,t)                                   "--MW-- DC power flow"
 eq_trans_reduct_multilink(r,rr,n,nn,trtype,allh,t)      "--MW-- limit CURT_REDUCT_TRANS by transmission investment along single- and multi-link paths"
 eq_trans_reduct_singlelink(n,nn,trtype,allh,t)          "--MW-- limit CURT_REDUCT_TRANS by transmission investment along single links"
 eq_trans_reduct_sinkload(rr,allh,t)                     "--MW-- limit CURT_REDUCT_TRANS by net load in sink region"
 eq_trans_reduct_vsc_source(r,allh,t)                    "--MW-- limit CURT_REDUCT_TRANS by converter investment in source if using VSC macrogrid"
 eq_trans_reduct_vsc_sink(rr,allh,t)                     "--MW-- limit CURT_REDUCT_TRANS by converter investment in sink if using VSC macrogrid"
 eq_transmission_limit(r,rr,allh,t,trtype)               "--MW-- transmission flow limit"

* operating reserve constraints
 eq_OpRes_requirement(ortype,r,allh,t)         "--MW-- operating reserve constraint"
 eq_ORCap_large_res_frac(ortype,i,v,r,allh,t)  "--MW-- operating reserve capacity availability constraint for generators with reserve_frac > 0.5"
 eq_ORCap_small_res_frac(ortype,i,v,r,allh,t)  "--MW-- operating reserve capacity availability constraint for generators with reserve_frac <= 0.5"

* regional and national policies
 eq_emit_accounting(e,r,t)                "--tons (metric for CO2)-- accounting for total emissions in a region"
 eq_emit_rate_limit(e,r,t)                "--tons per MWh (metric for CO2)-- emission rate limit"
 eq_annual_cap(e,t)                       "--tons (metric for CO2)-- annual (year-specific) emissions cap",
 eq_bankborrowcap(e)                      "--weighted tons (metric for CO2)-- flexible banking and borrowing cap (to be used w/intertemporal solve only"
 eq_RGGI_cap(t)                           "--metric tons CO2-- RGGI constraint -- Regions' emissions must be less than the RGGI cap"
 eq_state_cap(t)                          "--metric tons CO2-- state-level CO2 cap constraint -- used to represent California cap and trade program"
 eq_CSAPR_Budget(csapr_group,t)           "--MT NOx-- CSAPR trading group emissions cannot exceed the budget cap"
 eq_CSAPR_Assurance(st,t)                 "--MT NOx-- CSAPR state emissions cannot exceed the assurance cap"
 eq_BatteryMandate(r,t)                   "--MW-- Battery storage capacity must be greater than indicated level"

* RPS Policy equations
 eq_REC_Generation(RPSCat,i,st,t)         "--RECs-- Generation of RECs by state"
 eq_REC_Requirement(RPSCat,st,t)          "--RECs-- RECs generated plus trade must meet the state's requirement"
 eq_REC_ooslim(RPSCat,st,t)               "--RECs-- RECs imported cannot exceed a fraction of total requirement for certain states",
 eq_REC_launder(RPSCat,st,t)              "--RECs-- RECs laundering constraint"
 eq_REC_BundleLimit(RPSCat,st,ast,t)      "--RECS-- trade in bundle recs must be less than interstate electricity transmission"
 eq_REC_unbundledLimit(RPScat,st,t)       "--RECS-- unbundled RECS cannot exceed some percentage of total REC requirements"
 eq_RPS_OFSWind(st,t,ofstype)             "--MW-- MW of offshore wind capacity must be greater than or equal to RPS amount"
 eq_national_gen(t)                       "--MWh-- e.g. a national RPS or CES. require a certain amount of total generation to be from specified sources."

* fuel supply curve equations
 eq_gasused(cendiv,allh,t)                "--MMBtu-- gas used must be from the sum of gas bins"
 eq_gasbinlimit(cendiv,gb,t)              "--MMBtu-- limit on gas from each bin"
 eq_gasbinlimit_nat(gb,t)                 "--MMBtu-- national limit on gas from each bin"
 eq_bioused(r,t)                          "--MMBtu-- bio used must be from the sum of bio bins"
 eq_biousedlimit(bioclass,usda_region,t)  "--MMBtu-- limit on bio from each bin in each USDA region"

* regional natural gas supply curves
 eq_gasaccounting_regional(cendiv,t)         "--MMBtu-- regional gas consumption cannot exceed the amount used in bins"
 eq_gasaccounting_national(t)                "--MMBtu-- national gas consumption cannot exceed the amount used in bins"
 eq_gasbinlimit_regional(fuelbin,cendiv,t)   "--MMBtu-- regional binned gas usage cannot exceed bin capacity"
 eq_gasbinlimit_national(fuelbin,t)          "--MMBtu-- national binned gas usage cannot exceed bin capacity"

* hydrogen supply and demand
 eq_prod_capacity_limit(i,v,r,allh,t)        "--tonne-- production of hydrogen cannot exceeds its capacity"
 eq_h2_demand(p,t)                           "--tonne-- production of hydrogen must meet exogenous demand plus RE-CT use"
 eq_h2_demand_regional(r,p,t)                "--tonne-- regional hydrogen supply must equal demand"
 eq_h2_transport_caplimit(r,rr,allh,t)       "--tonne-- limit on interregional hydrogen trade"


* transmission equations
 eq_CAPTRAN(r,rr,trtype,t)                   "--MW-- capacity accounting for transmission"
 eq_prescribed_transmission(r,rr,trtype,t)   "--MW-- investment in transmission up to first year allowed must be less than the exogenous possible transmission",
 eq_INVTRAN_VCLimit(r,vc)                    "--MW-- investment in transmission capacity cannot exceed that available in its VC bin"
 eq_PRMTRADELimit(r,rr,trtype,allszn,t)      "--MW-- trading of PRM capacity cannot exceed the line's capacity"
 eq_SubStationAccounting(r,t)                "--Substations-- accounting for total investment in each substation"
 eq_CAPTRAN_max(r,rr,trtype,t)               "--MW-- upper limit for transmission capacity along individual corridors"
 eq_CAP_CONVERTER(r,t)                       "--MW-- capacity acounting for VSC AC/DC converters"
 eq_converter_max(r,t)                       "--MW-- upper limit for VSC AC/DC converter capacity in individual BAs"
 eq_CONVERSION_limit_energy(r,allh,t)        "--MW-- AC/DC energy conversion is limited to converter capacity"
 eq_CONVERSION_limit_prm(r,allszn,t)         "--MW-- AC/DC PRM conversion is limited to converter capacity"
 eq_PRMTRADE_VSC(r,allszn,t)                 "--MW-- PRM capacity can flow through VSC lines but doesn't directly contribute to PRM"

* storage-specific equations
 eq_storage_capacity(i,v,r,allh,t)                "--MW-- Second storage capacity constraint in addition to eq_capacity_limit"
 eq_storage_duration(i,v,r,allh,t)                "--MWh-- limit STORAGE_LEVEL based on hours of storage available"
 eq_storage_in_cap(i,v,r,allh,t)                  "--MW-- storage_in must be less than a given fraction of power output capacity"
 eq_storage_in_max(r,allh,src,t)                  "--MW-- upper bound on storage charging that can come from new sources"
 eq_storage_in_min(r,allh,t)                      "--MW-- lower bound on STORAGE_IN at the hourly level"
 eq_storage_in_min_szn(r,allszn,t)                "--MW-- lower bound on STORAGE_IN at the seasonal level"
 eq_storage_in_minloading(i,v,r,allh,allhh,src,t) "--MW-- minimum level for storage_in across same-season hours"
 eq_storage_level(i,v,r,allh,t)                   "--MWh per day-- Storage level inventory balance from one time-slice to the next"
 eq_storage_opres(i,v,r,allh,t)                   "--MWh per day-- there must be sufficient energy in the storage to be able to provide operating reserves"
 eq_storage_seas_szn(i,v,r,allszn,t)              "--MWh-- GEN in a season must be greater than a certain percentage of STORAGE_IN in that season"
 eq_storage_seas(i,v,r,t)                         "--MWh-- total STORAGE_IN must balance GEN across all time-slices"
 eq_storage_starting_soc(i,v,r,allh,t)            "--MW-- when flex is enabled but no infinite loop, bound the starting amount of storage by the average across 8760 as seen by augur"
 eq_storage_thermalres(i,v,r,allh,t)              "--MW-- thermal storage contribution to operating reserves is store_in only"


* demand-response specific equations
 eq_dr_max_shed(i,v,r,allh,t)             "--MW-- total shed allowed by demand response technologies from timeslice h"
 eq_dr_max_shed_hrs(i,v,r,t)              "--MW-- total hours shed is allowed to operate over the year"
 eq_dr_max_shift(i,v,r,allh,allhh,t)      "--MW-- total shifting allowed by demand response technologies to timeslice h from timeslice hh"
 eq_dr_max_decrease(i,v,r,allh,t)         "--MW-- maximum allowed decrease of load from demand response in timeslice h"
 eq_dr_max_increase(i,v,r,allh,t)         "--MW-- maximum allowed increase of load from demand response in timeslice h"
 eq_dr_gen(i,v,r,allh,t)                  "--MW-- link demand response shifting to generation"
 eq_dr_in_max(r,allh,src,t)               "--MW-- upper bound on DR charging for curtailment recovery"

* hybrid PV+battery equations
 eq_pvb_storage_in_max(r,allh,src,t)     "--MW-- upper bound on storage charging for curtailment recovery from local PV"
 eq_pvb_total_gen(i,v,r,allh,t)          "--MW-- generation post curtailment = generation from pv (post curtailment) + generation from battery - charging from PV"
 eq_pvb_array_energy_limit(i,v,r,allh,t) "--MW-- PV energy to storage (no curtailment recovery) + PV energy to inverter <= PV resource"
 eq_pvb_inverter_limit(i,v,r,allh,t)     "--MW-- energy moving through the inverter cannot exceed the inverter capacity"
 eq_pvb_itc_charge_reqt(i,v,r,t)         "--MWh-- total energy charged from local PV >= ITC qualification fraction * total energy charged"

* Canadian imports balance
 eq_Canadian_Imports(r,allszn,t)          "--MWh-- Balance of Canadian imports by season"

* water usage accounting
 eq_water_accounting(i,v,w,r,allh,t)      "--Mgal-- water usage accounting"
 eq_water_capacity_total(i,v,r,t)         "--Mgal-- specify required water access based on generation capacity and water use rate"
 eq_water_capacity_limit(wst,r,t)         "--Mgal/yr-- total water access must not exceed supply by region and water type"
 eq_water_use_limit(i,v,w,r,allszn,t)     "--Mgal/yr-- water use must not exceed available access"
;

*==========================
* --- LOAD CONSTRAINTS ---
*==========================

* ---------------------------------------------------------------------------

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
* note net canadian load (when Sw_Canada = 2) is included
* in eq_supply_demand since LOAD needs to stay positive
* while net_trade can be negative and cause infeasibilities
    + can_exports_h(r,h,t)$[Sw_Canada = 1]

*[plus] load from EV charging
    + EVLOAD(r,h,t)$Sw_EV

*[plus] load shifted from other timeslices
    + sum{flex_type, FLEX(flex_type,r,h,t) }$Sw_EFS_flex

*[plus] Load created by production activities
    + sum{(p,i,v)$[consume(i)$valcap(i,v,r,t)$i_p(i,p)],
          PRODUCE(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) }$Sw_Prod
;

* ---------------------------------------------------------------------------

eq_evloadcon(r,szn,t)$[rfeas(r)$tmodel(t)$Sw_EV]..

    sum{h$h_szn(h,szn),hours(h) * EVLOAD(r,h,t) }

    =e=

    ev_dynamic_demand(r,szn,t)
;

* ---------------------------------------------------------------------------

*======================================
* --- LOAD FLEXIBILITY CONSTRAINTS ---
*======================================

* ---------------------------------------------------------------------------

*The following 3 equations apply to the flexibility of load in ReEDS, originally developed
*as part of the EFS study in ReEDS heritage and adapted for ReEDS-2.0 here.

* Additional work has been done to represent flexible load as a generator + storage
* with boundaries on how many timeslices this generator may shift. See equations
* in the DR CONSTRAINTS section for that representation

* FLEX load in each season equals the total exogenously-specified flexible load in each season
eq_load_flex_day(flex_type,r,szn,t)$[rfeas(r)$tmodel(t)$Sw_EFS_flex]..

    sum{h$h_szn(h,szn), FLEX(flex_type,r,h,t) * hours(h) } / numdays(szn)

    =e=

    sum{h$h_szn(h,szn), load_exog_flex(flex_type,r,h,t) * hours(h) } / numdays(szn)
;

* ---------------------------------------------------------------------------

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

* ---------------------------------------------------------------------------

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

* ---------------------------------------------------------------------------

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

* ---------------------------------------------------------------------------

*=========================================================
* --- EQUATIONS RELATING CAPACITY ACROSS TIME PERIODS ---
*=========================================================

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

* ---------------------------------------------------------------------------

eq_cap_init_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $(not retiretech(i,v,r,t))]..

    m_capacity_exog(i,v,r,t)
* Account for capcity upsizing within init vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)], 
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =e=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;

* ---------------------------------------------------------------------------

eq_cap_init_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $retiretech(i,v,r,t)]..

    m_capacity_exog(i,v,r,t)
* Account for capcity upsizing within init vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)], 
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }


    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;

* ---------------------------------------------------------------------------

eq_cap_init_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)$(not upgrade(i))
                           $retiretech(i,v,r,t)]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)],
         CAP(i,v,r,tt)

         + sum{ii$[valcap(ii,v,r,tt)$upgrade_from(ii,i)],
               CAP(ii,v,r,tt) }$Sw_Upgrades
        }

* Account for capcity upsizing within init vintages
    + sum{rscbin$allow_cap_up(i,v,r,rscbin,t), INV_CAP_UP(i,v,r,rscbin,t) }


    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;

* ---------------------------------------------------------------------------

*==============================
* -- new capacity equations --
*==============================

* ---------------------------------------------------------------------------

eq_cap_new_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $(not retiretech(i,v,r,t))]..

    sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
        }
* Account for capcity upsizing within new vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)], 
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =e=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;

* ---------------------------------------------------------------------------

eq_cap_new_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $retiretech(i,v,r,t)]..

    sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
      }
* Account for capcity upsizing within new vintages
    + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))$allow_cap_up(i,v,r,rscbin,tt)], 
                      degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt) }

    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
          CAP(ii,v,r,t) }$Sw_Upgrades
;

* ---------------------------------------------------------------------------

eq_cap_new_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)$(not upgrade(i))
                          $retiretech(i,v,r,t)]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)],
         degrade(i,tt,t) * CAP(i,v,r,tt)

         + sum{ii$[valcap(ii,v,r,tt)$upgrade_from(ii,i)],
               CAP(ii,v,r,tt) }$Sw_Upgrades
        }

    + INV(i,v,r,t)$valinv(i,v,r,t)

    + INV_REFURB(i,v,r,t)$[valinv(i,v,r,t)$refurbtech(i)$Sw_Refurb]
* Account for capcity upsizing within new vintages
    + sum{rscbin$allow_cap_up(i,v,r,rscbin,t), INV_CAP_UP(i,v,r,rscbin,t) }

    =g=

    CAP(i,v,r,t)

    + sum{ii$[valcap(ii,v,r,t)$upgrade_from(ii,i)],
           CAP(ii,v,r,t) }$Sw_Upgrades
;

* ---------------------------------------------------------------------------

eq_cap_upgrade(i,v,r,t)$[valcap(i,v,r,t)$upgrade(i)$Sw_Upgrades$tmodel(t)$(not noret_upgrade_tech(i))]..

*all previous years upgrades
    sum{(tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))
            $(yeart(tt)>=upgradeyear)$(initv(v) or (newv(v) and ivt(i,v,tt)))],
        UPGRADES(i,v,r,tt) }

    =g=

    CAP(i,v,r,t)
;

* ---------------------------------------------------------------------------

eq_cap_upgrade_noret(i,v,r,t)$[valcap(i,v,r,t)$upgrade(i)$Sw_Upgrades$tmodel(t)$noret_upgrade_tech(i)]..
*all previous years upgrades
    sum{(tt)$[(tfix(tt) or tmodel(tt))$(yeart(tt)<=yeart(t))
            $(yeart(tt)>=upgradeyear)$(initv(v) or (newv(v) and ivt(i,v,tt)))],
        UPGRADES(i,v,r,tt) }

*use equality constraint for technologies that do not retire (e.g., hydro)
    =e=

    CAP(i,v,r,t)
;

* ---------------------------------------------------------------------------

* Capacity upsizing limit
*   This uses rscbin to constrain hydropower upsizing using supply curve data.
eq_cap_up(i,v,r,rscbin,t)$[tmodel(t)$allow_cap_up(i,v,r,rscbin,t)]..

    cap_cap_up(i,v,r,rscbin,t)

    =g=

    sum{tt$[(tmodel(tt) or tfix(tt))], INV_CAP_UP(i,v,r,rscbin,tt) }
;

* ---------------------------------------------------------------------------

*Energy upsizing limit
*   This uses rscbin to constrain hydropower upsizing using supply curve data.
eq_ener_up(i,v,r,rscbin,t)$[tmodel(t)$allow_ener_up(i,v,r,rscbin,t)]..

    cap_ener_up(i,v,r,rscbin,t)

    =g=

    sum{tt$[(tmodel(tt) or tfix(tt))], INV_ENER_UP(i,v,r,rscbin,tt) }
;

* ---------------------------------------------------------------------------

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


* ---------------------------------------------------------------------------

eq_neartermcaplimit(r,t)$[rfeas_cap(r)$tmodel(t)$sum{rr, near_term_cap_limits("wind",rr,t) }
                            $sum{(i,v)$[valcap(i,v,r,t)$tg_i("wind",i)], 1 }
                            $Sw_NearTermLimits$Sw_ForcePrescription]..

    near_term_cap_limits("wind",r,t)

    =g=

    EXTRA_PRESCRIP("wind-ons",r,t)
;

* ---------------------------------------------------------------------------

*limit the amount of refurbishments available in specific year
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

* ---------------------------------------------------------------------------

eq_rsc_inv_account(i,v,r,t)$[tmodel(t)$valinv(i,v,r,t)$rsc_i(i)]..

  sum{rscbin$m_rscfeas(r,i,t,rscbin), INV_RSC(i,v,r,rscbin,t) }

  =e=

  INV(i,v,r,t)
;

* ---------------------------------------------------------------------------

*note that the following equation only restricts inv_rsc and not inv_refurb
*therefore, the capacity indicated by the supply curve may be limiting
*but the plant can still be refurbished
eq_rsc_INVlim(r,i,rscbin,t)$[tmodel(t)$rsc_i(i)$rfeas_cap(r)$m_rscfeas(r,i,t,rscbin)$m_rsc_con(r,i,t)]..
*With water constraints, some RSC techs are expanded to include cooling technologies
*but the combination of m_rsc_con and rsc_agg allows for those investments
*to be limited by the numeraire techs' m_rsc_dat

*capacity indicated by the resource supply curve (with undiscovered geo available at the "discovered" amount and hydro upgrade availability adjusted over time)
    m_rsc_dat(r,i,t,rscbin,"cap") * (1$[not geo_undisc(i)]
                                     + geo_discovery(t)$geo_undisc(i))
                                     + hyd_add_upg_cap(r,i,rscbin,t)$(Sw_HydroCapEnerUpgradeType=1)

    =g=

*must exceed the amount of total investment from that supply curve
    sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) <= yeart(t))$rsc_agg(i,ii)$(not dr(i))],
         INV_RSC(ii,v,r,rscbin,tt) * resourcescaler(ii) }

*must exceed the amount of total investment from that supply curve in that year (DR investment is annual)
    +  sum{(ii,v)$[valinv(ii,v,r,t)$rsc_agg(i,ii)$dr(i)],
           INV_RSC(ii,v,r,rscbin,t) * resourcescaler(ii) }
;

* ---------------------------------------------------------------------------

eq_growthlimit_relative(tg,t)$[growth_limit_relative(tg)$tmodel(t)
                              $Sw_GrowthRelCon$(yeart(t)>=2022)$(not tlast(t))]..

*the relative growth rate multiplied by the existing technology group's existing capacity
    growth_limit_relative(tg) ** (sum{tt$[tprev(tt,t)], yeart(tt) } - yeart(t)) *
    sum{(i,v,r,tt)$[tprev(t,tt)$valcap(i,v,r,tt)$tg_i(tg,i)$rfeas_cap(r)],
         CAP(i,v,r,tt) }

    =g=

* must exceed the current periods investment
* note scarcely-used set 'tg' is technology group (allows for lumping together or all wind/solar techs)
    sum{(i,v,r)$[valcap(i,v,r,t)$tg_i(tg,i)$rfeas_cap(r)],
         CAP(i,v,r,t) }
;

* ---------------------------------------------------------------------------

eq_growthlimit_absolute(tg,t)$[growth_limit_absolute(tg)$tmodel(t)
                               $Sw_GrowthAbsCon$(yeart(t)>=2018)$(not tlast(t))]..

* the absolute limit of growth (in MW)
     (sum{tt$[tprev(tt,t)], yeart(tt) } - yeart(t))
     * growth_limit_absolute(tg)

     =g=

* must exceed the total investment - same RHS as previous equation
* note scarcely-used set 'tg' is technology group (allows for lumping together or all wind/solar techs)
     sum{(i,v,r,rscbin)$[valinv(i,v,r,t)$m_rscfeas(r,i,t,rscbin)$tg_i(tg,i)$rsc_i(i)],
          INV_RSC(i,v,r,rscbin,t) }
;

* ---------------------------------------------------------------------------

*capacity must be greater than supply
*dispatchable hydro is accounted for both in this constraint and in eq_dhyd_dispatch
*this constraint does not apply to storage nor hybrid PV+Battery
*  limits for storage (including storage of hybrid PV+Battery) are tracked in eq_storage_capacity
*  limits for PV of Hybrid PV+Battery are tracked in eq_pvb_energy_balance
eq_capacity_limit(i,v,r,h,t)$[tmodel(t)$valgen(i,v,r,t)$(not storage_standalone(i))$(not pvb(i))$(not hydro_nd(i))]..
*total amount of dispatchable, non-hydro capacity
    (avail(i,v,h) * sum{rr$cap_agg(r,rr),
                       CAP(i,v,rr,t)$valcap(i,v,rr,t) })$[dispatchtech(i)$(not hydro_d(i))]

*total amount of dispatchable hydro capacity
    + (avail(i,v,h) * sum{(rr,szn)$[cap_agg(r,rr)$h_szn(h,szn)],
                       CAP(i,v,rr,t)$valcap(i,v,rr,t) * cap_hyd_szn_adj(i,szn,rr) })$hydro_d(i)

*sum of non-dispatchable capacity multiplied by its rated capacity factor,
*only vre technologies are curtailable.
*This term accounts for energy-only and capacity-only upsizing, which is initially implemented only for hydro.
    + sum{rr$[cap_agg(r,rr)$rfeas_cap(rr)$valcap(i,v,rr,t)],
          m_cf(i,v,rr,h,t)
           * (CAP(i,v,rr,t)
*add energy embedded in energy-only upsizing
           + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))], 
                    INV_ENER_UP(i,v,rr,rscbin,tt)$allow_ener_up(i,v,rr,rscbin,tt) 
*subtract energy that would be embedded in a capacity-only upsizing
                     - degrade(i,tt,t) * INV_CAP_UP(i,v,rr,rscbin,tt)$allow_cap_up(i,v,rr,rscbin,tt) }) 
                }$[not dispatchtech(i)]

    =g=

*must exceed generation
    GEN(i,v,r,h,t)

*[plus] sum of operating reserves by type
    + sum{ortype$reserve_frac(i,ortype),
          OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;

* ---------------------------------------------------------------------------

eq_capacity_limit_hydro_nd(i,v,r,h,t)$[tmodel(t)$valgen(i,v,r,t)$hydro_nd(i)]..
*sum of non-dispatchable hydro capacity multiplied by its rated capacity factor,
    + sum{rr$[cap_agg(r,rr)$rfeas_cap(rr)$valcap(i,v,rr,t)],
          (m_cf(i,v,rr,h,t)
           * CAP(i,v,rr,t)) }

    =e=

*must be equal to generation
    GEN(i,v,r,h,t)

*[plus] sum of operating reserves by type
    + sum{ortype$reserve_frac(i,ortype),
          OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;

* ---------------------------------------------------------------------------

eq_curt_gen_balance(r,h,t)$[tmodel(t)$rfeas(r)]..

*total potential generation
    sum{(i,v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$rfeas_cap(rr)$(vre(i) or pvb(i))],
         m_cf(i,v,rr,h,t) * CAP(i,v,rr,t) }

*[minus] curtailed generation
    - CURT(r,h,t)

    + CURT_SLACK(r,h,t)$[(yeart(t)<=model_builds_start_yr)$Sw_Hourly]

    =g=

*must exceed realized generation; exclude hybrid PV+Batttery
    sum{(i,v)$[valgen(i,v,r,t)$vre(i)], GEN(i,v,r,h,t) }

*must exceed realized PV generation from hybrid PV+Batttery
  + sum{(i,v)$[valgen(i,v,r,t)$pvb(i)], GEN_PVB_P(i,v,r,h,t) }$Sw_PVB

*[plus] sum of operating reserves by type; exclude hybrid PV+Batttery because the PV does not provide reserves
    + sum{(ortype,i,v)$[reserve_frac(i,ortype)$valgen(i,v,r,t)$vre(i)],
          OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;

* ---------------------------------------------------------------------------

eq_curtailment(r,h,t)$[tmodel(t)$rfeas(r)]..

*curtailment
    CURT(r,h,t)

    =g=

* --- INTERTEMPORAL ONLY ---

*curtailment of VRE (intertemporal only)
    sum{(i,v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$rfeas_cap(rr)$(vre(i) or pvb(i))],
        m_cf(i,v,rr,h,t) * CAP(i,v,rr,t) * curt_int(i,rr,h,t)
       }

*[plus] curtailment due to minimum generation (intertemporal only)
    + (curt_mingen_int(r,h,t) * sum{h_szn(h,szn), MINGEN(r,szn,t) })$Sw_Mingen

*[plus] excess curtailment (intertemporal only)
    + curt_excess(r,h,t)

* --- SEQUENTIAL ONLY ---

*[plus] the marginal curtailmet of new VRE (sequential only)
*Note: new distpv is included with curt_old
    + sum{(i,v,rr)$[cap_agg(r,rr)$valinv(i,v,rr,t)$(vre(i) or pvb(i))],
              m_cf(i,v,rr,h,t) * curt_marg(i,rr,h,t)
              * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] the curtailment from existing VRE (sequential only)
    + curt_old(r,h,t)

*[plus] curtailment due to changes in minimum generation levels (sequential only)
    + curt_mingen(r,h,t) * sum{h_szn(h,szn), MINGEN(r,szn,t)
        - sum{tt$tprev(t,tt), mingen_postret(r,szn,tt) } }$[Sw_Mingen$(yeart(t)>=mingen_firstyear)]

* --- SEQUENTIAL AND INTERTEMPORAL ---

*[minus] curtailment reduction from charging storge during timeslices with curtailment
*  Storage Charging; not hybrid PV+Battery
    - sum{(i,v,src)$[valgen(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))$src_curt(i,src)],
           curt_stor(i,v,r,h,src,t) * STORAGE_IN(i,v,r,h,src,t)
         }

* Reduction of curtailment from the operation of H2-producing plants
* Note that the inclusion is subsetted on valinv(i,v,r,t) given that
* we are only allowing new units to recover curtailment
* while old units are accounted for in Osprey
    - sum{(p,i,v)$[consume(i)$valinv(i,v,r,t)$i_p(i,p)],
            curt_prod(r,h,t) * PRODUCE(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) }$Sw_Prod

*Storage Charging for hybrid PV+Battery
    - sum{(i,v,src)$[valgen(i,v,r,t)$pvb(i)$src_curt(i,src)],
             curt_stor(i,v,r,h,src,t) * STORAGE_IN_PVB_P(i,v,r,h,src,t)$[dayhours(h)$(not sameas(src,"wind"))]
           + curt_stor(i,v,r,h,src,t) * STORAGE_IN_PVB_G(i,v,r,h,src,t)
         }$Sw_PVB

*DR 'charging';
    - sum{(i,v,hh,src)$[valgen(i,v,r,t)$dr1(i)$src_curt(i,src)$allowed_shifts(i,h,hh)],
           curt_dr(i,v,r,h,src,t) * DR_SHIFT(i,v,r,h,hh,src,t) / storage_eff(i,t) / hours(h)
         }
*[minus] curtailment reduction from building new transmission to rr
    - sum{rr$[rfeas(rr)
            $(not sameas(r,rr))
            $sum{(n,nn,trtype)$routes_inv(n,nn,trtype,t), translinkage(r,rr,n,nn,trtype) }],
          CURT_REDUCT_TRANS(r,rr,h,t)$curt_tran(r,rr,h,t) }

*[plus] net flow of curtailment with no transmission losses
*(otherwise CURT can be turned into transmission losses)
    + sum{(trtype,rr)$routes(rr,r,trtype,t), CURT_FLOW(rr,r,h,t) }$Sw_CurtFlow
    - sum{(trtype,rr)$routes(r,rr,trtype,t), CURT_FLOW(r,rr,h,t) }$Sw_CurtFlow
;

* ---------------------------------------------------------------------------

eq_mingen_lb(r,h,szn,t)$[h_szn(h,szn)$rfeas(r)$(yeart(t)>=mingen_firstyear)
                        $tmodel(t)$Sw_Mingen]..

*minimum generation level in a season
    MINGEN(r,szn,t)

    =g=

*must be greater than the minimum generation level in each time slice in that season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)], GEN(i,v,r,h,t)  * minloadfrac(r,i,h) }
;

* ---------------------------------------------------------------------------

eq_mingen_ub(r,h,szn,t)$[h_szn(h,szn)$rfeas(r)$(yeart(t)>=mingen_firstyear)
                        $tmodel(t)$Sw_Mingen]..

*generation in each timeslice in a season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)], GEN(i,v,r,h,t)  }

    =g=

*must be greater than the minimum generation level
    MINGEN(r,szn,t)
;

* ---------------------------------------------------------------------------

*requirement for fleet of a given tech to have a minimum annual capacity factor
eq_min_cf(i,rto,t)$[minCF(i,t)$tmodel(t)$sum{(v,r)$r_rto(r,rto), valgen(i,v,r,t) }$Sw_MinCF]..

    sum{(v,r,h)$[valgen(i,v,r,t)$r_rto(r,rto)], hours(h) * GEN(i,v,r,h,t) }

    =g=

    sum{(v,r)$r_rto(r,rto), sum{rr$[cap_agg(r,rr)$valcap(i,v,rr,t)], CAP(i,v,rr,t) } }
    * sum{h, hours(h) } * minCF(i,t)
;

* ---------------------------------------------------------------------------

* Seasonal energy constraint for dispatchable hydropower when all energy must be used within season (no seasonal energy shifting)
eq_dhyd_dispatch(i,v,r,szn,t)$[tmodel(t)$hydro_d(i)$valgen(i,v,r,t)$(within_seas_frac(i,v,r) = 1)]..

*seasonal hours [times] seasonal capacity factor [times] total hydro capacity [times] seasonal capacity adjustment
    sum{h$[h_szn(h,szn)], avail(i,v,h) * hours(h) }
    * (CAP(i,v,r,t) + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))],
               INV_ENER_UP(i,v,r,rscbin,tt)$allow_ener_up(i,v,r,rscbin,tt) 
             - degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt)$allow_cap_up(i,v,r,rscbin,tt) })
    * cap_hyd_szn_adj(i,szn,r)
    * m_cf_szn(i,v,r,szn,t)

    =g=

*total seasonal generation plus fraction of energy for regulation
    sum{h$[h_szn(h,szn)], hours(h)
        * ( GEN(i,v,r,h,t)
              + reg_energy_frac * OPRES("reg",i,v,r,h,t)$Sw_OpRes )
       }
;

* ---------------------------------------------------------------------------

* Annual energy constraint for dispatchable hydropower when seasonal shifting is allowed
eq_dhyd_dispatch_ann(i,v,r,t)$[tmodel(t)$hydro_d(i)$valgen(i,v,r,t)$(within_seas_frac(i,v,r) < 1)]..

    sum{szn,
* seasonal hours [times] seasonal capacity factor  
        sum{h$[h_szn(h,szn)], avail(i,v,h) * hours(h) }
* [times] total hydro capacity
        * (CAP(i,v,r,t) + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))],
            INV_ENER_UP(i,v,r,rscbin,tt)$allow_ener_up(i,v,r,rscbin,tt) 
            - degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt)$allow_cap_up(i,v,r,rscbin,tt) })
* [times] seasonal capacity adjustment            
        * cap_hyd_szn_adj(i,szn,r)
        * m_cf_szn(i,v,r,szn,t) }
    =g=

    sum{szn,
*total seasonal generation plus fraction of energy for regulation
        sum{h$[h_szn(h,szn)], hours(h)
            * ( GEN(i,v,r,h,t)
              + reg_energy_frac * OPRES("reg",i,v,r,h,t)$Sw_OpRes ) } }

;

* ---------------------------------------------------------------------------

* Required fraction of energy used within a season for dispatchable hydropower when seasonal shifting is allowed
eq_dhyd_dispatch_szn(i,v,r,szn,t)$[tmodel(t)$hydro_d(i)$valgen(i,v,r,t)$(within_seas_frac(i,v,r) < 1)]..

*total seasonal generation plus fraction of energy for regulation
    sum{h$[h_szn(h,szn)], hours(h)
        * ( GEN(i,v,r,h,t)
              + reg_energy_frac * OPRES("reg",i,v,r,h,t)$Sw_OpRes )
       }

    =g=

*fractional in-season energy requirement
    within_seas_frac(i,v,r) * (
*seasonal hours [times] seasonal capacity factor [times] total hydro capacity [times] seasonal capacity adjustment
        sum{h$[h_szn(h,szn)], avail(i,v,h) * hours(h) }
        * (CAP(i,v,r,t) + sum{(tt,rscbin)$[(tmodel(tt) or tfix(tt))],INV_ENER_UP(i,v,r,rscbin,tt)$allow_ener_up(i,v,r,rscbin,tt) 
           - degrade(i,tt,t) * INV_CAP_UP(i,v,r,rscbin,tt)$allow_cap_up(i,v,r,rscbin,tt) })
        * cap_hyd_szn_adj(i,szn,r)
        * (m_cf_szn(i,v,r,szn,t)$(m_cf_szn(i,v,r,szn,t) <= 1) + 1$(m_cf_szn(i,v,r,szn,t) > 1))
    )
;

*===============================
* --- SUPPLY DEMAND BALANCE ---
*===============================

* ---------------------------------------------------------------------------

* The treatment of power flow along DC lines depends on the type of AC/DC converter used.
* LCC DC lines are single poit-to-point lines connected to the AC grid on either end, and
* as such are treated like AC lines (with different costs/losses).
* VSC DC lines are part of a multi-terminal DC network; DC power can flow through a node
* without converting to AC and incurring DC/AC/DC losses. Power flow along VSC lines is
* therefore treated separately through the CONVERSION variable and eq_vsc_flow equation.
eq_supply_demand_balance(r,h,t)$[rfeas(r)$tmodel(t)]..

* generation from all sources, including storage discharge and DR
*  for DR - GEN represents the reduction in load from shifting away
*  from the focal timeslice load to another timeslice - this 
*  included both DR_SHIFT and DR_SHED variables amounts
    sum{(i,v)$valgen(i,v,r,t), GEN(i,v,r,h,t) }

* [plus] net AC and LCC DC transmission with imports reduced by losses
    + sum{(trtype,rr)$[routes(rr,r,trtype,t)$aclike(trtype)],
          (1-tranloss(rr,r,trtype)) * FLOW(rr,r,h,t,trtype) }
    - sum{(trtype,rr)$[routes(r,rr,trtype,t)$aclike(trtype)],
          FLOW(r,rr,h,t,trtype) }

* [plus] net AC/DC conversion through VSC converter stations
    + (CONVERSION(r,h,"VSC","AC",t) * converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]
    - (CONVERSION(r,h,"AC","VSC",t) / converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]

* [minus] storage charging; not Hybrid PV+Battery
    - sum{(i,v,src)$[valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))], STORAGE_IN(i,v,r,h,src,t) }

* [minus] energy into storage for hybrid pv+battery from grid
    - sum{(i,v,src)$[valcap(i,v,r,t)$pvb(i)], STORAGE_IN_PVB_G(i,v,r,h,src,t) }$Sw_PVB

* [minus] load shifting from demand response
    - sum{[i,v,hh,src]$[valgen(i,v,r,t)$dr1(i)$allowed_shifts(i,h,hh)], 
                     DR_SHIFT(i,v,r,h,hh,src,t) / hours(h) / storage_eff(i,t) }$Sw_DR

    + net_trade_can(r,h,t)$[Sw_Canada = 2]

    =e=

* must exceed demand
    LOAD(r,h,t)
;

* ---------------------------------------------------------------------------

eq_vsc_flow(r,h,t)
    $[rfeas(r)
    $tmodel(t)
    $Sw_VSC]..

* [plus] net VSC DC transmission with imports reduced by losses
    + sum{rr$routes(rr,r,"VSC",t), (1-tranloss(rr,r,"VSC")) * FLOW(rr,r,h,t,"VSC") }
    - sum{rr$routes(r,rr,"VSC",t), FLOW(r,rr,h,t,"VSC") }

* [plus] net VSC AC/DC conversion
    + (CONVERSION(r,h,"AC","VSC",t) * converter_efficiency_vsc)$val_converter(r,t)
    - (CONVERSION(r,h,"VSC","AC",t) / converter_efficiency_vsc)$val_converter(r,t)

    =e=

* no direct consumption of VSC
    0
;

* ---------------------------------------------------------------------------

*=======================================
* --- MINIMUM LOADING CONSTRAINTS ---
*=======================================

* ---------------------------------------------------------------------------

* the generation in any hour cannot exceed the minloadfrac times the
* supply from other hours within that hour correlation set (via hour_szn_group(h,hh))
* note that hour_szn_group does not include the same hour (i.e. h!=hh)
eq_minloading(i,v,r,h,hh,t)$[valgen(i,v,r,t)$minloadfrac(r,i,hh)
                            $((yeart(t)>=model_builds_start_yr) or (Sw_Hourly = 0))
                            $tmodel(t)$hour_szn_group(h,hh)$Sw_MinLoading]..

    GEN(i,v,r,h,t)

    =g=

    GEN(i,v,r,hh,t) * minloadfrac(r,i,hh)
;

*=======================================
* --- OPERATING RESERVE CONSTRAINTS ---
*=======================================

* ---------------------------------------------------------------------------

*generation must occur at some point during the szn (i.e., day)
*in order to procure operating reserves from that resource
*ORPRES for storage is limited by the storage capacity per the constraint "eq_storage_capacity"

eq_ORCap_large_res_frac(ortype,i,v,r,h,t)$[tmodel(t)$valgen(i,v,r,t)$Sw_OpRes
                            $(reserve_frac(i,ortype)>0.5)$(not storage_standalone(i))$(not hyd_add_pump(i))]..

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

* ---------------------------------------------------------------------------

*for plants with reserve_frac <= 0.5, generation must occur during the timeslice
*in which reserves are provided
eq_ORCap_small_res_frac(ortype,i,v,r,h,t)$[tmodel(t)$valgen(i,v,r,t)$Sw_OpRes
                            $(reserve_frac(i,ortype)<=0.5)]..

*generation
    GEN(i,v,r,h,t)

    =g=

*must be greater than the operating reserves procured
    OPRES(ortype,i,v,r,h,t)
;

* ---------------------------------------------------------------------------

*operating reserves must meet the operating reserves requirement (by ortype)
eq_OpRes_requirement(ortype,r,h,t)$[rfeas(r)$tmodel(t)$Sw_OpRes]..

*operating reserves from technologies that can produce them (i.e. those w/ramp rates)

    sum{(i,v)$[valgen(i,v,r,t)$reserve_frac(i,ortype)],
         OPRES(ortype,i,v,r,h,t) }

*[plus] net transmission of operating reserves (while including losses for imports)
    + sum{rr$opres_routes(rr,r,t), (1 - tranloss(rr,r,"AC")) * OPRES_FLOW(ortype,rr,r,h,t) }
    - sum{rr$opres_routes(r,rr,t), OPRES_FLOW(ortype,r,rr,h,t) }

    =g=

*must meet the demand for or type
*first portion is from load
    orperc(ortype,"or_load") * LOAD(r,h,t)

*next portion is from the wind generation
    + orperc(ortype,"or_wind") * sum{(i,v)$[wind(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) }

*final portion is from upv, dupv, and distpv capacity
*note that pv capacity is held at the balancing area
*include the hybrid PV+battery PV capacity here
    + orperc(ortype,"or_pv") * sum{(i,v)$[(pv(i) or pvb(i))$valcap(i,v,r,t)],
         CAP(i,v,r,t) }$dayhours(h)
;

* ---------------------------------------------------------------------------

*=================================
* --- PLANNING RESERVE MARGIN ---
*=================================

* ---------------------------------------------------------------------------

*trade of planning reserve margin capacity cannot exceed the transmission line's available capacity
eq_PRMTRADELimit(r,rr,trtype,szn,t)$[tmodel(t)$routes(r,rr,trtype,t)$Sw_ReserveMargin]..

*[plus] transmission capacity
    + CAPTRAN(r,rr,trtype,t)

    =g=

*[plus] firm capacity traded between regions
    + PRMTRADE(r,rr,trtype,szn,t)
;

* ---------------------------------------------------------------------------

eq_PRMTRADE_VSC(r,szn,t)
    $[rfeas(r)
    $tmodel(t)
    $Sw_ReserveMargin
    $Sw_VSC]..

*[plus] net VSC DC imports - exports of firm capacity with imports reduced by losses
    + sum{rr$routes(rr,r,"VSC",t), (1-tranloss(rr,r,"VSC")) * PRMTRADE(rr,r,"VSC",szn,t) }
    - sum{rr$routes(r,rr,"VSC",t), PRMTRADE(r,rr,"VSC",szn,t) }

* [plus] net VSC AC/DC conversion
    + (CONVERSION_PRM(r,szn,"AC","VSC",t) * converter_efficiency_vsc)$val_converter(r,t)
    - (CONVERSION_PRM(r,szn,"VSC","AC",t) / converter_efficiency_vsc)$val_converter(r,t)

    =e=

* no direct contribution of VSC
    0
;

* ---------------------------------------------------------------------------

*binned capacity must be the same as capacity
eq_cap_sdbin_balance(i,v,r,szn,t)$[tmodel(t)$valcap(i,v,r,t)$(storage_standalone(i) or pvb(i) or hyd_add_pump(i))]..

*total capacity in each region
    bcr(i) * CAP(i,v,r,t)

    =e=

*sum of all binned capacity within each region
    sum{sdbin, CAP_SDBIN(i,v,r,szn,sdbin,t) }
;

* ---------------------------------------------------------------------------

*binned capacity cannot exceed sdbin size
eq_sdbin_limit(ccreg,szn,sdbin,t)$[tmodel(t)$sum{r$r_ccreg(r,ccreg), rfeas(r) }]..

*sdbin size from CC script
    sdbin_size(ccreg,szn,sdbin,t)

    =g=

*standalone storage capacity in each sdbin adjusted by the appropriate CC value
    sum{(i,v,r)$[r_ccreg(r,ccreg)$valcap(i,v,r,t)$(storage_standalone(i) or hyd_add_pump(i))],
        CAP_SDBIN(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin,t)
        }

*[plus] hybrid storage capacity in each sdbin adjusted by the appropriate CC value and the hybrid derate factor
    + sum{(i,v,r)$[r_ccreg(r,ccreg)$valcap(i,v,r,t)$pvb(i)],
          CAP_SDBIN(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin,t) * hybrid_cc_derate(i,r,szn,sdbin,t)
          }
;

* ---------------------------------------------------------------------------

eq_reserve_margin(r,szn,t)$[tmodel(t)$rfeas(r)$(yeart(t)>=model_builds_start_yr)$Sw_ReserveMargin]..

*[plus] sum of all non-rsc and non-storage capacity
    + sum{(i,v)$[valcap(i,v,r,t)$(not vre(i))$(not hydro(i))$(not storage(i))$(not dr(i))$(not consume(i))],
          CAP(i,v,r,t)
         }

*[plus] firm capacity from existing VRE or CSP
*only used in sequential solve case (otherwise cc_old = 0)
    + sum{(i,rr)$[(vre(i) or csp(i) or pvb(i))$cap_agg(r,rr)$rfeas_cap(rr)],
          cc_old(i,rr,szn,t)
         }

*[plus] marginal capacity credit of VRE and csp times new investment
*only used in sequential solve case (otherwise m_cc_mar = 0)
*Note: new distpv is included with cc_old
    + sum{(i,v,rr)$[cap_agg(r,rr)$(vre(i) or csp(i) or pvb(i))$valinv(i,v,rr,t)],
          m_cc_mar(i,rr,szn,t) * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] firm capacity contribution from all binned storage capacity
*battery, pumped-hydro, and CAES
*excludes hydro upgraded to add pumps
    + sum{(i,v,rr,sdbin)$[cap_agg(r,rr)$(storage_standalone(i) or hyd_add_pump(i))$valcap(i,v,rr,t)],
          cc_storage(i,sdbin,t) * CAP_SDBIN(i,v,rr,szn,sdbin,t)
         }
*hybrid PV+battery
    + sum{(i,v,rr,sdbin)$[cap_agg(r,rr)$pvb(i)$valcap(i,v,rr,t)],
          cc_storage(i,sdbin,t) * hybrid_cc_derate(i,rr,szn,sdbin,t) * CAP_SDBIN(i,v,rr,szn,sdbin,t)
         }
*[plus] firm capacity contribution from all DR
    + sum{(i,v,rr)$[cap_agg(r,rr)$dr(i)$valcap(i,v,rr,t)],
          m_cc_dr(i,rr,szn,t) * CAP(i,v,rr,t)
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
* include hydro upgraded to add pumps
    + sum{(i,v)$[(hydro_d(i) or hyd_add_pump(i))$valcap(i,v,r,t)],
          CAP(i,v,r,t) * cap_hyd_szn_adj(i,szn,r)
         }

*[plus] imports of firm capacity through AC and LCC DC lines
    + sum{(rr,trtype)$[routes(rr,r,trtype,t)$aclike(trtype)],
          (1 - tranloss(rr,r,trtype)) * PRMTRADE(rr,r,trtype,szn,t)
         }

*[minus] exports of firm capacity through AC and LCC DC lines
    - sum{(rr,trtype)$[routes(r,rr,trtype,t)$aclike(trtype)],
          PRMTRADE(r,rr,trtype,szn,t)
         }

*[plus] net AC/DC conversion of firm capacity through VSC converters
    + (CONVERSION_PRM(r,szn,"VSC","AC",t) * converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]
    - (CONVERSION_PRM(r,szn,"AC","VSC",t) / converter_efficiency_vsc)$[Sw_VSC$val_converter(r,t)]

    =g=

*[plus] the peak demand times the planning reserve margin
    + (
        peakdem_static_szn(r,szn,t)

        + PEAK_FLEX(r,szn,t)$Sw_EFS_flex

*[plus] only steam methane reforming technologies are assumed to increase peak demand
* contribution to peak demand based on weighted-average across timeslices in each season
        + (sum{(p,i,v,h)$[smr(i)$valcap(i,v,r,t)$h_szn(h,szn)$h2_p(p)$i_p(i,p)],
               PRODUCE(p,i,v,r,h,t) / prod_conversion_rate(i,v,r,t) * hours(h) }$Sw_Prod
            / sum{h$h_szn(h,szn), hours(h) }
          )

      ) * (1 + prm(r,t))
;

* ---------------------------------------------------------------------------

*================================
* --- TRANSMISSION CAPACITY  ---
*================================

* ---------------------------------------------------------------------------

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
*       However, expansion only needs to be tracked for one of the direcions (r,rr) or (rr,r).
*       Therefore, add together the investments for both direction to get the corridor investment in either direction.
*       Disallow building of new endogenous transmission link until after 2020 because prescriptions are defined through 2020 as exogenous capacity
    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))$routes_inv(r,rr,trtype,tt)],
             INVTRAN(r,rr,tt,trtype)
           + INVTRAN(rr,r,tt,trtype)
         }
;

* ---------------------------------------------------------------------------

eq_prescribed_transmission(r,rr,trtype,t)$[routes_inv(r,rr,trtype,t)$tmodel(t)$(yeart(t)<firstyear_trans)]..

*all available transmission capacity expansion that is 'possible'
*note we allow for possible future transmission to accumulate
*hence the sum over all previous years
    sum{tt$[(tmodel(tt) or tfix(tt))$(yeart(tt)<=yeart(t))],
         trancap_fut(r,rr,"possible",tt,trtype) + trancap_fut(rr,r,"possible",tt,trtype) }

    =g=

*must exceed the bi-directional investment along that corridor
    sum{tt$[(tmodel(tt) or tfix(tt))$(yeart(tt)<=yeart(t))$routes_inv(r,rr,trtype,tt)],
        INVTRAN(r,rr,tt,trtype) + INVTRAN(rr,r,tt,trtype) }
;

* ---------------------------------------------------------------------------

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

* ---------------------------------------------------------------------------

*investment in each voltage class cannot exceed the capacity
*of that substation bin (aka voltage class)
eq_INVTRAN_VCLimit(r,vc)$[rfeas(r)$tscfeas(r,vc)]..

*the voltage class bin's available capacity
    tsc_dat(r,"CAP",vc)

    =g=

*cannot exceed total capacity
    sum{t$[tmodel(t) or tfix(t)], INVSUBSTATION(r,vc,t) }
;

* ---------------------------------------------------------------------------

* flows cannot exceed the total transmission capacity
eq_transmission_limit(r,rr,h,t,trtype)$[tmodel(t)$routes(r,rr,trtype,t)]..

*transmission capacity must be greater than
    CAPTRAN(r,rr,trtype,t)

    =g=

*[plus] energy flows
    + FLOW(r,rr,h,t,trtype)
    + FLOW(rr,r,h,t,trtype)


*[plus] operating reserve flows (operating reserves can only be transferred across AC lines)
    + sum{ortype, OPRES_FLOW(ortype,r,rr,h,t) }$[Sw_OpRes$sameas(trtype,"AC")$opres_routes(r,rr,t)] * opres_mult
    + sum{ortype, OPRES_FLOW(ortype,rr,r,h,t) }$[Sw_OpRes$sameas(trtype,"AC")$opres_routes(rr,r,t)] * opres_mult

*[plus] curtailment flows
    + CURT_FLOW(r,rr,h,t)$Sw_CurtFlow
    + CURT_FLOW(rr,r,h,t)$Sw_CurtFlow
;

* ---------------------------------------------------------------------------

* CAP_CONVERTER accumulates INV_CONVERTER from years <= t
eq_CAP_CONVERTER(r,t)
    $[tmodel(t)
    $rfeas(r)
    $val_converter(r,t)
    $Sw_VSC]..

    CAP_CONVERTER(r,t)

    =e=

    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))],
          INV_CONVERTER(r,tt) }
;

* ---------------------------------------------------------------------------

* AC/DC conversion cannot exceed the converter capacity
eq_CONVERSION_limit_energy(r,h,t)
    $[tmodel(t)
    $rfeas(r)
    $val_converter(r,t)
    $Sw_VSC]..

    CAP_CONVERTER(r,t)

    =g=

    CONVERSION(r,h,"AC","VSC",t) + CONVERSION(r,h,"VSC","AC",t)
;

* ---------------------------------------------------------------------------

* AC/DC PRM conversion cannot exceed the converter capacity
eq_CONVERSION_limit_prm(r,szn,t)
    $[tmodel(t)
    $rfeas(r)
    $val_converter(r,t)
    $Sw_VSC]..

    CAP_CONVERTER(r,t)

    =g=

    CONVERSION_PRM(r,szn,"AC","VSC",t) + CONVERSION_PRM(r,szn,"VSC","AC",t)
;

* ---------------------------------------------------------------------------

* Limit the curtailment reduction from multi-link path (r,rr) to the lowest-capacity
* transmission investment in a link along (r,rr), times (r,rr) curtailment reduction rate.
* Losses are already accounted for in curt_tran(r,rr,h,t)
eq_trans_reduct_multilink(r,rr,n,nn,trtype,h,t)
    $[curt_tran(r,rr,h,t)
    $tmodel(t)
    $translinkage(r,rr,n,nn,trtype)
    $routes_inv(n,nn,trtype,t)
    $rfeas(r)$rfeas(rr)]..

    curt_tran(r,rr,h,t) * (INVTRAN(n,nn,t,trtype)$routes_inv(n,nn,trtype,t)
                           + INVTRAN(nn,n,t,trtype)$routes_inv(nn,n,trtype,t))

    =g=

    CURT_REDUCT_TRANS(r,rr,h,t)
;

* ---------------------------------------------------------------------------

* A single link (n',nn',trtype') can't reduce curtailment in a single timestamp by more than its capacity
eq_trans_reduct_singlelink(n,nn,trtype,h,t)
    $[tmodel(t)
    $sum{(r,rr)$curt_tran(r,rr,h,t), translinkage(r,rr,n,nn,trtype) }
    $routes_inv(n,nn,trtype,t)]..

    INVTRAN(n,nn,t,trtype)$routes_inv(n,nn,trtype,t)
    + INVTRAN(nn,n,t,trtype)$routes_inv(nn,n,trtype,t)

    =g=

    sum{(r,rr)$translinkage(r,rr,n,nn,trtype), CURT_REDUCT_TRANS(r,rr,h,t)$curt_tran(r,rr,h,t) }
;

* ---------------------------------------------------------------------------

* All the transmission into region rr can't reduce curtailment by more than net load in region rr
eq_trans_reduct_sinkload(rr,h,t)$[tmodel(t)$rfeas(rr)]..

    net_load_adj_no_curt_h(rr,h,t)

    =g=

    + sum{r$[rfeas(r)
           $(not sameas(r,rr))
           $sum{(n,nn,trtype)$routes_inv(n,nn,trtype,t), translinkage(r,rr,n,nn,trtype) }],
          CURT_REDUCT_TRANS(r,rr,h,t)$curt_tran(r,rr,h,t) }
;

* ---------------------------------------------------------------------------

* If using the VSC HVDC macrogrid, for all source,sink (r,rr) pairs where the 
* optimal path uses VSC transmission, limit the total curtailment reduction across
* all sinks to the new investment in converter capacity in the source region
eq_trans_reduct_vsc_source(r,h,t)
    $[tmodel(t)
    $rfeas(r)
    $sum{rr, curt_tran(r,rr,h,t) }
    $val_converter(r,t)
    $Sw_VSC]..

    INV_CONVERTER(r,t)

    =g=

    + sum{rr$[rfeas(rr)
            $(not sameas(r,rr))
            $vsc_required(r,rr)],
          CURT_REDUCT_TRANS(r,rr,h,t)$curt_tran(r,rr,h,t) }
;

* ---------------------------------------------------------------------------

* If using the VSC HVDC macrogrid, for all source,sink (r,rr) pairs where the 
* optimal path uses VSC transmission, limit the total curtailment reduction across
* all sources to the new investment in converter capacity in the sink region
eq_trans_reduct_vsc_sink(rr,h,t)
    $[tmodel(t)
    $rfeas(rr)
    $sum{r, curt_tran(r,rr,h,t) }
    $val_converter(rr,t)
    $Sw_VSC]..

    INV_CONVERTER(rr,t)

    =g=

    + sum{r$[rfeas(r)
           $(not sameas(r,rr))
           $vsc_required(r,rr)],
          CURT_REDUCT_TRANS(r,rr,h,t)$curt_tran(r,rr,h,t) }
;

* ---------------------------------------------------------------------------

* Limit the total transmission capacity of each corridor link to captran_max
eq_CAPTRAN_max(r,rr,trtype,t)$[tmodel(t)$routes(r,rr,trtype,t)$Sw_CapTranMax]..

    Sw_CapTranMax

    =g=

    CAPTRAN(r,rr,trtype,t)
;

* ---------------------------------------------------------------------------

* Limit the total VSC AC/DC converter capacity in each BA to captran_max
eq_converter_max(r,t)
    $[tmodel(t)
    $rfeas(r)
    $val_converter(r,t)
    $Sw_VSC
    $Sw_CapTranMax]..

    Sw_CapTranMax

    =g=

    CAP_CONVERTER(r,t)
;

* ---------------------------------------------------------------------------

*=========================
* --- EMISSION POLICIES ---
*=========================

* ---------------------------------------------------------------------------

eq_emit_accounting(e,r,t)$[rfeas(r)$tmodel(t)]..

    EMIT(e,r,t)

    =e=

    sum{(i,v,h)$[valgen(i,v,r,t)],
         hours(h) * emit_rate(e,i,v,r,t) * GEN(i,v,r,h,t) } / emit_scale(e)

*less co2 reduced via DAC
    - (sum{(i,v,h)$[dac(i)$valcap(i,v,r,t)$i_p(i,"DAC")], hours(h) * PRODUCE("DAC",i,v,r,h,t) }
                               / emit_scale("CO2") )$[Sw_DAC$sameas(e,"co2")]

;

* ---------------------------------------------------------------------------

eq_RGGI_cap(t)$[tmodel(t)$(yeart(t)>=RGGI_start_yr)$Sw_RGGI]..

    RGGI_cap(t) / emit_scale("CO2")

    =g=

    sum{r$[RGGI_r(r)$rfeas(r)], EMIT("CO2",r,t) }
;

* ---------------------------------------------------------------------------

eq_state_cap(t)$[tmodel(t)$(yeart(t)>=state_cap_start_yr)$Sw_StateCap]..

    state_cap(t) / emit_scale("CO2")

    =g=

    sum{r$[rfeas(r)$state_cap_r(r)], EMIT("CO2",r,t) }

* import emissions intensity assumed constant
* here the receiving regions (rr) are the cap regions and the sending
* regions (r) are those that have connection with cap regions
    + sum{(h,r,rr,trtype)$[state_cap_r(rr)$(not state_cap_r(r))$routes(r,rr,trtype,t)],
         hours(h) * CA_import_emit * FLOW(r,rr,h,t,trtype) } / emit_scale("CO2")
;

* ---------------------------------------------------------------------------

* traded emissions among states in each trading group need
* to be less than the sum of all the state caps within that trading group
eq_CSAPR_Budget(csapr_group,t)$[Sw_CSAPR$tmodel(t)$(yeart(t)>=csapr_startyr)]..

*the accumulation of states csapr cap for the budget category
    sum{st$[stfeas(st)$csapr_group_st(csapr_group,st)], csapr_cap(st,"budget",t) } / emit_scale("NOX")

    =g=

*must exceed the summed-over-state hourly-weighted nox emissions by csapr group
    sum{st$csapr_group_st(csapr_group,st),
      sum{(i,v,h,r)$[r_st(r,st)$valgen(i,v,r,t)],
         h_weight_csapr(h) * hours(h) * emit_rate("NOX",i,v,r,t) * GEN(i,v,r,h,t)  / emit_scale("NOX")
       }
      }
;

* ---------------------------------------------------------------------------

* along with the cap on trading groups, each state has
* a maximum amount of NOX emissions during ozone season
eq_CSAPR_Assurance(st,t)$[stfeas(st)$(yeart(t)>=csapr_startyr)
                         $csapr_cap(st,"Assurance",t)$tmodel(t)]..

*the state level assurance cap
    csapr_cap(st,"assurance",t) / emit_scale("NOX")

    =g=

*must exceed the csapr-hourly-weighted nox emissions by state
    sum{(i,v,h,r)$[r_st(r,st)$valgen(i,v,r,t)],
      h_weight_csapr(h) * hours(h) * emit_rate("NOX",i,v,r,t) * GEN(i,v,r,h,t) / emit_scale("NOX")
    }
;

* ---------------------------------------------------------------------------

eq_emit_rate_limit(e,r,t)$[(yeart(t)>=CarbPolicyStartyear)$emit_rate_con(e,r,t)
                          $tmodel(t)$rfeas(r)]..

    emit_rate_limit(e,r,t) * (
         sum{(i,v,h)$[valgen(i,v,r,t)],  hours(h) * GEN(i,v,r,h,t) }
    ) / emit_scale(e)

    =g=

    EMIT(e,r,t)
;

* ---------------------------------------------------------------------------

eq_annual_cap(e,t)$[sum{tt, emit_cap(e,tt) }$tmodel(t)$Sw_AnnualCap]..

*exogenous cap
    emit_cap(e,t) / emit_scale(e)

    =g=

*must exceed annual endogenous emissions
    sum{r$rfeas(r), EMIT(e,r,t) }
;

* ---------------------------------------------------------------------------

eq_bankborrowcap(e)$[Sw_BankBorrowCap$sum{t, emit_cap(e,t) }]..

*weighted exogenous emissions
    sum{t$[tmodel(t)$emit_cap(e,t)],
        yearweight(t) * emit_cap(e,t) } / emit_scale(e)

    =g=

* must exceed weighted endogenous emissions
    sum{(r,t)$[tmodel(t)$rfeas(r)$emit_cap(e,t)],
        yearweight(t) * EMIT(e,r,t) }
;

* ---------------------------------------------------------------------------

*==========================
* --- RPS CONSTRAINTS ---
*==========================

* ---------------------------------------------------------------------------

eq_REC_Generation(RPSCat,i,st,t)$[stfeas(st)$(not tfirst(t))$tmodel(t)
                                 $Sw_StateRPS$(yeart(t)>=RPS_StartYear)
                                 $(not sameas(RPSCat,"RPS_Bundled"))
                                 $(not sameas(RPSCat,"CES_Bundled"))]..

*RECS are computed as the total annual generation from a technology
*hydro is the only technology adjusted by RPSTechMult
*because GEN from pvb(i) includes grid charging, subtract out its grid charging
    + sum{(v,r,h)$[valgen(i,v,r,t)$RecTech(RPSCat,st,i,t)$rfeas(r)$r_st(r,st)],
          RPSTechMult(RPSCat,i,st) * hours(h)
          * (GEN(i,v,r,h,t) - sum{src$[pvb(i)$Sw_PVB], STORAGE_IN_PVB_G(i,v,r,h,src,t) * storage_eff_pvb_g(i,t) })
         }

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

* ---------------------------------------------------------------------------

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
        ( (LOAD(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
       }
;

* ---------------------------------------------------------------------------

eq_REC_BundleLimit(RPSCat,st,ast,t)$[stfeas(st)$stfeas(ast)$tmodel(t)
                              $(not sameas(st,ast)$Sw_StateRPS)
                              $(sum{i,RecMap(i,RPSCat,st,ast,t) })
                              $(sameas(RPSCat,"RPS_Bundled") or sameas(RPSCat,"CES_Bundled"))
                              $(yeart(t)>=RPS_StartYear)]..

*amount of net transmission flows from state st to state ast
    sum{(h,r,rr,trtype)$[r_st(r,st)$r_st(rr,ast)$routes(r,rr,trtype,t)],
          hours(h) * FLOW(r,rr,h,t,trtype)
      }

    =g=
* must be greater than bundled RECS
    sum{i$RecMap(i,RPSCat,st,ast,t),
        RECS(RPSCat,i,st,ast,t) }
;

* ---------------------------------------------------------------------------

eq_REC_unbundledLimit(RPSCat,st,t)$[RPS_unbundled_limit(st)$tmodel(t)$stfeas(st)
                            $(yeart(t)>=RPS_StartYear)$Sw_StateRPS
                            $(sameas(RPSCat,"RPS_All") or sameas(RPSCat,"CES"))]..
*the limit on unbundled RECS times the REC requirement
      RPS_unbundled_limit(st) * RecPerc(RPSCat,st,t) *
        sum{(r,h)$[rfeas(r)$r_st(r,st)],
            hours(h) *
            ( (LOAD(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
           }
      =g=

*needs to be greater than the unbundled recs
*NB unbundled RECS are computed as all imported RECS minus bundled RECS
    sum{(i,ast)$[RecMap(i,RPSCat,ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS(RPSCat,i,ast,st,t) }

    - sum{(i,ast)$[RecMap(i,"RPS_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("RPS_Bundled",i,ast,st,t) }$sameas(RPSCat,"RPS_All")

    - sum{(i,ast)$[RecMap(i,"CES_Bundled",ast,st,t)$stfeas(ast)$(not sameas(st,ast))],
        RECS("CES_Bundled",i,ast,st,t) }$sameas(RPSCat,"CES")
;

* ---------------------------------------------------------------------------

eq_REC_ooslim(RPSCat,st,t)$[RecStates(RPSCat,st,t)$(yeart(t)>=RPS_StartYear)
                           $RPS_oosfrac(st)$stfeas(st)$tmodel(t)$Sw_StateRPS
                           $(not sameas(RPSCat,"RPS_Bundled"))
                           $(not sameas(RPSCat,"CES_Bundled"))]..

*the fraction of imported recs times the requirement
    RPS_oosfrac(st) * RecPerc(RPSCat,st,t) *
        sum{(r,h)$[rfeas(r)$r_st(r,st)],
            hours(h) *
            ( (LOAD(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada=1]) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
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

* ---------------------------------------------------------------------------

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

* ---------------------------------------------------------------------------

eq_RPS_OFSWind(st,t,ofstype)$[tmodel(t)$stfeas(st)$offshore_cap_req(st,t,ofstype)$Sw_StateRPS
                      $sum{r$r_st(r,st),sum{(i,v,rr)$[ofstype_i(ofstype,i)$cap_agg(r,rr)],valcap(i,v,rr,t) }}]..

* existing capacity of wind
    sum{r$r_st(r,st),
        sum{(i,v,rr)$[ofstype_i(ofstype,i)$cap_agg(r,rr)], m_capacity_exog(i,v,rr,t) }

* investments over time
      + sum{(i,v,rr,tt)$[ofstype_i(ofstype,i)$cap_agg(r,rr)$inv_cond(i,v,rr,t,tt)$(tmodel(tt) or tfix(tt))],
            INV(i,v,rr,tt) + INV_REFURB(i,v,rr,tt)$[refurbtech(i)$Sw_Refurb] }
* end sum over regions in r_st
    }

    =g=

*exogenously-specified requirement for offshore wind capacity
    offshore_cap_req(st,t,ofstype)
;

* ---------------------------------------------------------------------------

eq_batterymandate(r,t)$[rfeas(r)$tmodel(t)$batterymandate(r,t)$(yeart(t)>=firstyear_battery)
                        $Sw_BatteryMandate]..
*battery capacity
    sum{(i,v)$[valcap(i,v,r,t)$(battery(i) or pvb(i))], bcr(i) * CAP(i,v,r,t) }

    =g=

*must be greater than the indicated level
    batterymandate(r,t)
;

* ---------------------------------------------------------------------------

eq_national_gen(t)$[tmodel(t)$national_gen_frac(t)$Sw_GenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[nat_gen_tech_frac(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h) * nat_gen_tech_frac(i) }

    =g=

*must exceed the mandated percentage [times]
    national_gen_frac(t) * (

* if Sw_GenMandate = 1, then apply the fraction to the bus bar load
    (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$routes(rr,r,trtype,t), (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_standalone(i)], STORAGE_IN(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_standalone(i)], GEN(i,v,r,h,t) * hours(h) }
    )$[Sw_GenMandate = 1]

* if Sw_GenMandate = 2, then apply the fraction to the end use load
    + (sum{(r,h)$rfeas(r),
        hours(h) *
        ( (LOAD(r,h,t) - can_exports_h(r,h,t)$[Sw_Canada = 1]) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
       })$[Sw_GenMandate = 2]
    )
;

* ---------------------------------------------------------------------------

*====================================
* --- FUEL SUPPLY CURVES ---
*====================================

* ---------------------------------------------------------------------------

*gas used from each bin is the sum of all gas used
eq_gasused(cendiv,h,t)$[tmodel(t)$((Sw_GasCurve=0) or (Sw_GasCurve=3))$cdfeas(cendiv)]..

    sum{gb,GASUSED(cendiv,gb,h,t) }

    =e=

    sum{(i,v,r)$[valgen(i,v,r,t)$gas(i)$rfeas(r)$r_cendiv(r,cendiv)],
         heat_rate(i,v,r,t) * GEN(i,v,r,h,t) } / gas_scale
;

* ---------------------------------------------------------------------------

* gas from each bin needs to less than its capacity
eq_gasbinlimit(cendiv,gb,t)$[tmodel(t)$cdfeas(cendiv)$(Sw_GasCurve=0)]..

    gaslimit(cendiv,gb,t)

    =g=

    sum{h, hours(h) * GASUSED(cendiv,gb,h,t) }
;

* ---------------------------------------------------------------------------

eq_gasbinlimit_nat(gb,t)$[tmodel(t)$(Sw_GasCurve=3)]..

   gaslimit_nat(gb,t)

   =g=

   sum{(h,cendiv)$cdfeas(cendiv),
       hours(h) * GASUSED(cendiv,gb,h,t)
      }
;

* ---------------------------------------------------------------------------

eq_gasaccounting_regional(cendiv,t)$[cdfeas(cendiv)$tmodel(t)$(Sw_GasCurve=1)]..

    sum{fuelbin,VGASBINQ_REGIONAL(fuelbin,cendiv,t) }

    =e=

    sum{(i,v,r,h)$[valgen(i,v,r,t)$gas(i)$r_cendiv(r,cendiv)$rfeas(r)],
         hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t)
       }
;

* ---------------------------------------------------------------------------

eq_gasaccounting_national(t)$[tmodel(t)$(Sw_GasCurve=1)]..

    sum{fuelbin,VGASBINQ_NATIONAL(fuelbin,t) }

    =e=

    sum{(i,v,r,h)$[valgen(i,v,r,t)$gas(i)$rfeas(r)],
         hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t)
       }
;

* ---------------------------------------------------------------------------

eq_gasbinlimit_regional(fuelbin,cendiv,t)$[cdfeas(cendiv)$tmodel(t)$(Sw_GasCurve=1)]..

    Gasbinwidth_regional(fuelbin,cendiv,t)

    =g=

    VGASBINQ_REGIONAL(fuelbin,cendiv,t)
;

* ---------------------------------------------------------------------------

eq_gasbinlimit_national(fuelbin,t)$[tmodel(t)$(Sw_GasCurve=1)]..

    Gasbinwidth_national(fuelbin,t)

    =g=

    VGASBINQ_NATIONAL(fuelbin,t)
;

* ---------------------------------------------------------------------------

*==============================
* -- Bioenergy Supply Curve --
*==============================

* ---------------------------------------------------------------------------

eq_bioused(r,t)$[sum{(i,v)$(bio(i) or cofire(i)), valgen(i,v,r,t) }$tmodel(t)]..

    sum{bioclass, BIOUSED(bioclass,r,t) }

    =e=

*biopower generation
    + sum{(i,v,h)$[valgen(i,v,r,t)$bio(i)],
        hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t) }


*portion of cofire generation that is from bio resources
*here we assumed it fixed at 15% (for now)
    + sum{(i,v,h)$[cofire(i)$valgen(i,v,r,t)],
         bio_cofire_perc * hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

* biomass consumption limit is annual
eq_biousedlimit(bioclass,usda_region,t)$[tmodel(t)]..

    biosupply(usda_region,bioclass,"cap")

    =g=

    sum{r$[r_usda(r,usda_region)$sum{(i,v)$(bio(i) or cofire(i)), valgen(i,v,r,t) }], BIOUSED(bioclass,r,t) }
;

* ---------------------------------------------------------------------------

*============================
* --- STORAGE CONSTRAINTS ---
*============================

* ---------------------------------------------------------------------------

*storage use cannot exceed capacity
*this constraint does not apply to CSP+TES or hydro pump upgrades
eq_storage_capacity(i,v,r,h,t)$[valgen(i,v,r,t)$(storage_standalone(i) or pvb(i))$tmodel(t)]..

* [plus] Capacity of all storage technologies
    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
        CAP(i,v,rr,t) * bcr(i) * avail(i,v,h)
       }

    =g=

* [plus] Generation from storage, excluding hybrid PV+Battery
    GEN(i,v,r,h,t)$(not pvb(i))

* [plus] Generation from battery of hybrid PV+Battery
    + GEN_PVB_B(i,v,r,h,t)$[pvb(i)$Sw_PVB]

* [plus] Storage charging
* not hybrid PV+Battery
    + sum{src, STORAGE_IN(i,v,r,h,src,t) }$[not pvb(i)]
* hybrid PV+Battery: PV
    + sum{src$[not sameas(src,"wind")], STORAGE_IN_PVB_P(i,v,r,h,src,t) }$[pvb(i)$dayhours(h)$Sw_PVB]
* hybrid PV+Battery: Grid
    + sum{src, STORAGE_IN_PVB_G(i,v,r,h,src,t) }$[pvb(i)$Sw_PVB]

* [plus] Operating reserves
    + sum{ortype,
          reserve_frac(i,ortype) * OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;

* ---------------------------------------------------------------------------

* The daily storage level in the next time-slice (h+1) must equal the
*  daily storage level in the current time-slice (h)
*  plus daily net charging in the current time-slice (accounting for losses).
*  CSP with storage energy accounting is also covered by this constraint.
*  Does not apply for storage technologies that allow cross-season energy arbitrage.
eq_storage_level(i,v,r,h,t)$[valgen(i,v,r,t)$storage(i)$(within_seas_frac(i,v,r) = 1)$tmodel(t)]..

*[plus] storage level in h+1
    sum{(hh)$[nexth(r,h,hh)], STORAGE_LEVEL(i,v,r,hh,t) }

*When flex is enabled but there is no infinite loop, we still need to enforce this 
* constraint but there is no next-period storage_level that corresponds to this final hour
* Thus we can add a slack variable that allows the end-of-day/week/etc energy balance 
* to be positive - avoiding certain errors and infeasibilities mainly with storage_in_min
* associated with storage_in_min. final_hour also depends on Sw_Hourly and Sw_HourlyWrap
    + LAST_HOUR_SOC(i,v,r,h,t)$[final_hour(r,h)$Sw_Hourly]

    =e=

* only want to include storage_level from periods that have had a previous storage_level
* otherwise it becomes a free variable, implying you can charge storage without bound
    STORAGE_LEVEL(i,v,r,h,t)

*[plus] storage charging
    + storage_eff(i,t) *  hours_daily(h) * (
*energy into stand-alone storage (not CSP-TES) and hydropower that adds pumping
          sum{src, STORAGE_IN(i,v,r,h,src,t) }$[storage_standalone(i) or hyd_add_pump(i)]

*energy into storage from CSP field
        + sum{rr$[CSP_Storage(i)$valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
            CAP(i,v,rr,t) * csp_sm(i) * m_cf(i,v,rr,h,t)
           }
      )
*[plus] water inflow energy available for hydropower that adds pumping
    + (CAP(i,v,r,t) * avail(i,v,h) * hours_daily(h) *
        sum{szn$h_szn(h,szn), cap_hyd_szn_adj(i,szn,r) * m_cf_szn(i,v,r,szn,t) }
        )$hyd_add_pump(i)

*[plus] energy into hybrid PV+battery storage
*hybrid pv+battery: PV charging
    + storage_eff_pvb_p(i,t) * hours_daily(h) * sum{src$[not sameas(src,"wind")], 
            STORAGE_IN_PVB_P(i,v,r,h,src,t) } $[pvb(i)$dayhours(h)$Sw_PVB]

*hybrid pv+battery: grid charging
    + storage_eff_pvb_g(i,t) * hours_daily(h) * sum{src, STORAGE_IN_PVB_G(i,v,r,h,src,t) } $[pvb(i)$Sw_PVB]

*[minus] generation from stand-alone storage (discharge) and CSP
*exclude hybrid PV+Battery because GEN refers to output from both the PV and the battery
    - hours_daily(h) * GEN(i,v,r,h,t)$[not pvb(i)]

*[minus] Generation from Battery (dicharge) of hybrid PV+Battery
    - hours_daily(h) * GEN_PVB_B(i,v,r,h,t) $[pvb(i)$Sw_PVB]

*[minus] losses from reg reserves (only half because only charging half
*the time while providing reg reserves)
    - (hours_daily(h) * OPRES("reg",i,v,r,h,t) * (1 - storage_eff(i,t)) / 2 * reg_energy_frac)$Sw_OpRes
;

* ---------------------------------------------------------------------------

eq_storage_starting_soc(i,v,r,h,t)$[valgen(i,v,r,t)$storage(i)$tmodel(t)
                          $starting_hour(r,h)$Sw_Hourly$(not Sw_HourlyWrap)]..
* if infinite loop is not enabled, take the starting hour state of charge 
* as the average across relevant 8760 hours from Augur
    storage_soc_exog(i,v,r,h,t)

    =g=

    STORAGE_LEVEL(i,v,r,h,t)
    ;


* ---------------------------------------------------------------------------

* Annual energy balance for storage that can shift energy across seasons
eq_storage_seas(i,v,r,t)$[valgen(i,v,r,t)$storage(i)$(within_seas_frac(i,v,r) < 1)$tmodel(t)]..

    sum{h,
*[plus] annual storage charging
        storage_eff(i,t) *  hours(h) * (
*energy into stand-alone storage (not CSP-TES) and hydropower that adds pumping
           sum{src, STORAGE_IN(i,v,r,h,src,t) }$(storage_standalone(i) or hyd_add_pump(i))

*energy into storage from CSP field
           + sum{rr$[CSP_Storage(i)$valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
                  CAP(i,v,rr,t) * csp_sm(i) * m_cf(i,v,rr,h,t) }
      )

*[plus] energy into hybrid PV+battery storage
*hybrid pv+battery: PV charging
    + storage_eff_pvb_p(i,t) * hours(h) * sum{src$[not sameas(src,"wind")], 
        STORAGE_IN_PVB_P(i,v,r,h,src,t) } $[pvb(i)$dayhours(h)$Sw_PVB]

*hybrid pv+battery: grid charging
    + storage_eff_pvb_g(i,t) * hours(h) * sum{src, STORAGE_IN_PVB_G(i,v,r,h,src,t) } $[pvb(i)$Sw_PVB]

*[plus] annual water inflow energy available for hydropower that adds pumping
    + (CAP(i,v,r,t) * avail(i,v,h) * hours(h) *
        sum{szn$h_szn(h,szn), cap_hyd_szn_adj(i,szn,r) * m_cf_szn(i,v,r,szn,t) }
        )$hyd_add_pump(i)
    }

    =e=
*[plus] annual generation
    sum{h, hours(h) * GEN(i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

* Minimum amount of storage input in a season to be used for generation in that season,
* when cross-season energy shifting is available
eq_storage_seas_szn(i,v,r,szn,t)$[valgen(i,v,r,t)$storage(i)$(within_seas_frac(i,v,r) < 1)$tmodel(t)]..

*[plus] seasonal generation
    sum{h$h_szn(h,szn), hours(h) * GEN(i,v,r,h,t) }

=g=

*fractional in-season energy requirement
    within_seas_frac(i,v,r) *
*[plus] seasonal storage charging
    sum{h$h_szn(h,szn),
        storage_eff(i,t) *  hours(h) * 
*energy into stand-alone storage (not CSP-TES) and hydropower that adds pumping
        (   sum{src, STORAGE_IN(i,v,r,h,src,t) }$(storage_standalone(i) or hyd_add_pump(i))

*energy into storage from CSP field
            + sum{rr$[CSP_Storage(i)$valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
              CAP(i,v,rr,t) * csp_sm(i) * m_cf(i,v,rr,h,t) }
        )

*[plus] energy into hybrid PV+battery storage
*hybrid pv+battery: PV charging
    + storage_eff_pvb_p(i,t) * hours(h) * sum{src$[not sameas(src,"wind")], 
        STORAGE_IN_PVB_P(i,v,r,h,src,t) } $[pvb(i)$dayhours(h)$Sw_PVB]
*hybrid pv+battery: grid charging
    + storage_eff_pvb_g(i,t) * hours(h) * sum{src, STORAGE_IN_PVB_G(i,v,r,h,src,t) } $[pvb(i)$Sw_PVB]

*[plus] seasonal water inflow energy available for hydropower that adds pumping
    + (CAP(i,v,r,t) * avail(i,v,h) * hours(h)
        * cap_hyd_szn_adj(i,szn,r)
        * m_cf_szn(i,v,r,szn,t)
      )$hyd_add_pump(i)
    }
;

* ---------------------------------------------------------------------------

*there must be sufficient energy in storage to provide operating reserves
eq_storage_opres(i,v,r,h,t)$[valgen(i,v,r,t)$tmodel(t)$Sw_OpRes
                            $(storage_standalone(i) or pvb(i) or hyd_add_pump(i))]..

*[plus] initial storage level
    STORAGE_LEVEL(i,v,r,h,t)

*[minus] generation that occurs during this timeslice
    - hours_daily(h) * GEN(i,v,r,h,t) $[not pvb(i)]

*[minus] generation that occurs during this timeslice
    - hours_daily(h) * GEN_PVB_B(i,v,r,h,t) $[pvb(i)$Sw_PVB]

*[minus] losses from reg reserves (only half because only charging half
*the time while providing reg reserves)
    - hours_daily(h) * OPRES("reg",i,v,r,h,t) * (1 - storage_eff(i,t)) / 2 * reg_energy_frac

    =g=

*[plus] energy reserved for operating reserves
    + hours_daily(h) * sum{ortype, OPRES(ortype,i,v,r,h,t) }
;

* ---------------------------------------------------------------------------

*storage charging must exceed OR contributions for thermal storage
eq_storage_thermalres(i,v,r,h,t)$[valgen(i,v,r,t)$Thermal_Storage(i)
                                 $tmodel(t)$Sw_OpRes]..

    sum{src, STORAGE_IN(i,v,r,h,src,t) }

    =g=

    sum{ortype,
        reserve_frac(i,ortype) * OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;

* ---------------------------------------------------------------------------

*batteries and CSP-TES are limited by their duration for each normalized hour per season
eq_storage_duration(i,v,r,h,t)$[valgen(i,v,r,t)$(battery(i) or CSP_Storage(i) or pvb(i) or psh(i))
                               $tmodel(t)]..

* [plus] storage duration times storage capacity
    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
        storage_duration(i) * CAP(i,v,rr,t) * (1$CSP_Storage(i) + 1$psh(i) + bcr(i)$(battery(i) or pvb(i))) }

    =g=

    STORAGE_LEVEL(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

*lower bound on storage charging that is linked to the arbitrage value estimated in Augur
eq_storage_in_min(r,h,t)$[sum{(i,v)$storage_standalone(i), valgen(i,v,r,t) }
                         $tmodel(t)$(Sw_Storage_in_Min=1)]..

    sum{(i,v)$[storage_standalone(i)$valgen(i,v,r,t)], STORAGE_IN(i,v,r,h,"other",t) }

    =g=

    storage_in_min(r,h,t) 
;

* ---------------------------------------------------------------------------

*lower bound on storage charging that is linked to the arbitrage value estimated in Augur
eq_storage_in_min_szn(r,szn,t)$[sum{(i,v)$storage_standalone(i), valgen(i,v,r,t) }
                               $tmodel(t)$(Sw_Storage_in_Min=2)]..

    sum{(i,v,h)$[storage_standalone(i)$valgen(i,v,r,t)$h_szn(h,szn)], 
                STORAGE_IN(i,v,r,h,"other",t) }

    =g=

    sum{h$h_szn(h,szn), storage_in_min(r,h,t) }

;

* ---------------------------------------------------------------------------

*upper bound on storage charging to recover curtailment from each source (old, new pv, new wind)
*'other' does not represent curtailment recovery so it is excluded
eq_storage_in_max(r,h,src,t)$[rfeas(r)$sum{i$storage(i), src_curt(i,src) }$tmodel(t)]..

*[plus] the marginal curtailment from "new" sources
    sum{(i,v,rr)$[cap_agg(r,rr)$valinv(i,v,rr,t)$i_src(i,src)],
              m_cf(i,v,rr,h,t) * curt_marg(i,rr,h,t)
              * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
       }$[not sameas(src,"old")]

*[plus] the existing curtailment from "old" sources
    + curt_old(r,h,t)$sameas(src,"old")

    =g=

*[plus] stand-alone and hydro pump upgrade storage charging
      sum{(i,v)$[(storage_standalone(i) or hyd_add_pump(i))$valgen(i,v,r,t)$src_curt(i,src)],  
          STORAGE_IN(i,v,r,h,src,t) }

*[plus] hybrid PV+battery storage charging
* storage charging from PV
    + sum{(i,v)$[pvb(i)$valgen(i,v,r,t)$src_curt(i,src)], 
          STORAGE_IN_PVB_P(i,v,r,h,src,t) }$[dayhours(h)$(not sameas(src,"wind"))$Sw_PVB]

* storage charging from the grid
    + sum{(i,v)$[pvb(i)$valgen(i,v,r,t)$src_curt(i,src)], 
          STORAGE_IN_PVB_G(i,v,r,h,src,t) }$Sw_PVB
;

* ---------------------------------------------------------------------------

* Charging power must be less than a specified fraction of power output capacity
* This is required in addition to eq_storage_capacity for facilities where input capacity < output capacity.
* If storinmaxfrac were applied to CAP in eq_storage_capacity, it would also limit output capacity.
eq_storage_in_cap(i,v,r,h,t)$[(storage_standalone(i) or hyd_add_pump(i))$valgen(i,v,r,t)
                              $tmodel(t)$(storinmaxfrac(i,v,r) < 1)]..

*[plus] maximum storage input capacity as a fraction of output capacity and accounting for availability
    avail(i,v,h) * storinmaxfrac(i,v,r) *
    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)], CAP(i,v,rr,t) }

    =g=

*[plus] storage input across all src
    sum{src, STORAGE_IN(i,v,r,h,src,t) }
;

* ---------------------------------------------------------------------------

* the charging power in any time slice cannot exceed the minstorfrac times the
* charging power from any other hour within the same season (via hour_szn_group(h,hh))
eq_storage_in_minloading(i,v,r,h,hh,src,t)$[(storage_standalone(i) or hyd_add_pump(i))$tmodel(t)
                                            $minstorfrac(i,v,r,hh)$valgen(i,v,r,t)$hour_szn_group(h,hh)]..

    STORAGE_IN(i,v,r,h,src,t)

    =g=

    STORAGE_IN(i,v,r,hh,src,t) * minstorfrac(i,v,r,hh)
;

* ---------------------------------------------------------------------------

*===============================
* --- Hybrid PV+Battery ---
*===============================

* ---------------------------------------------------------------------------

*upper bound on storage charing to recover PV curtailment from 'old' or 'new' Hybrid PV+battery
*'other' does not represent curtailment recovery so it is excluded
* eq_pvb_energy_balance" limits charging from 'other':  sum{src, STORAGE_IN} <= local PV resource
eq_pvb_storage_in_max(r,h,src,t)$[rfeas(r)$dayhours(h)$(sameas(src,"pv") or sameas(src,"old"))
                                 $tmodel(t)$Sw_PVB]..

*[plus] the marginal curtailment from "new" hybrid PV+Battery
    sum{(i,v,rr)$[cap_agg(r,rr)$valinv(i,v,rr,t)$i_src(i,src)$pvb(i)],
              m_cf(i,v,rr,h,t) * curt_marg(i,rr,h,t)
              * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
       }$sameas(src,"pv")

*[plus] the curtailment from "old" hybrid PV+Battery (estimated from the previous year)
    + curt_old_pvb_lastyear(r,h)$[sameas(src,"old")]

    =g=

* hybrid PV+battery storage charging from the local PV
    + sum{(i,v)$[(pvb(i))$valgen(i,v,r,t)], STORAGE_IN_PVB_P(i,v,r,h,src,t) }

;

* ---------------------------------------------------------------------------

* Generation post curtailment =
*    + generation from pv (post curtailment)
*    + generation from battery
*    - storage charging from PV for curtailment recovery: src={pv, old}
*    - storage charging from PV - not for curtailment recovery: src={other}
eq_pvb_total_gen(i,v,r,h,t)$[pvb(i)$tmodel(t)$valgen(i,v,r,t)$Sw_PVB]..

    + GEN_PVB_P(i,v,r,h,t)

    + GEN_PVB_B(i,v,r,h,t)

* [minus] charging from PV (1) for curtailment recovery and (2) not for curtailment recovery
    - sum{src$[not sameas(src,"wind")], STORAGE_IN_PVB_P(i,v,r,h,src,t) }$dayhours(h)

    =e=

    GEN(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

* Energy to storage from PV (not for curtailment recovery) + PV generation (post curtailment) <= PV resource
* capacity factor is adjusted to include inverter losses, clipping losses, and low voltage losses
eq_pvb_array_energy_limit(i,v,r,h,t)$[pvb(i)$tmodel(t)$valgen(i,v,r,t)$Sw_PVB]..

* [plus] PV output
    sum{rr$[cap_agg(r,rr)$rfeas_cap(rr)$valcap(i,v,rr,t)],
        m_cf(i,v,rr,h,t) * CAP(i,v,rr,t)
       }

    =g=

* [plus] charging from PV (no curtailment recovery)
    + sum{src$sameas(src,"other"), STORAGE_IN_PVB_P(i,v,r,h,src,t) }$dayhours(h)

* [plus] generation from PV (post curtailment)
    + GEN_PVB_P(i,v,r,h,t)
;

* ---------------------------------------------------------------------------

* Energy moving through the inverter cannot exceed the inverter capacity
eq_pvb_inverter_limit(i,v,r,h,t)$[pvb(i)$tmodel(t)$valgen(i,v,r,t)$Sw_PVB]..

* [plus] inverter capacity [AC] = panel capacity [DC] / ILR [DC/AC]
    + sum{rr$[cap_agg(r,rr)$rfeas_cap(rr)$valcap(i,v,rr,t)], CAP(i,v,rr,t) } / ilr(i)

    =g=

* [plus] Output from PV
    + GEN_PVB_P(i,v,r,h,t)

* [plus] Output form battery
    + GEN_PVB_B(i,v,r,h,t)

* [plus] Battery charging from grid
    + sum{src, STORAGE_IN_PVB_G(i,v,r,h,src,t) }

* [plus] Battery operating reserves
    + sum{ortype, OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;

* ---------------------------------------------------------------------------

* total energy charged from local PV >= ITC qualification fraction * total energy charged

eq_pvb_itc_charge_reqt(i,v,r,t)$[pvb(i)$tmodel(t)$valgen(i,v,r,t)$pvb_itc_qual_frac$Sw_PVB]..

* [plus] Battery charging from PV
    + sum{(h,src)$[dayhours(h)$(not sameas(src,"wind"))], STORAGE_IN_PVB_P(i,v,r,h,src,t) * hours(h) }

    =g=

    + pvb_itc_qual_frac * (

* [plus] Battery charging from PV
    + sum{(h,src)$[dayhours(h)$(not sameas(src,"wind"))], STORAGE_IN_PVB_P(i,v,r,h,src,t) * hours(h) }

* [plus] Battery charging from Grid
    + sum{(h,src), STORAGE_IN_PVB_G(i,v,r,h,src,t) * hours(h) }
    )
;

* ---------------------------------------------------------------------------

*============================
* --- DEMAND RESPONSE CONSTRAINTS ---
*============================

*maximum energy shifted to timeslice h from timeslice hh 
eq_dr_max_shift(i,v,r,h,hh,t)$[allowed_shifts(i,h,hh)$valgen(i,v,r,t)$dr1(i)$tmodel(t)$Sw_DR]..
    
    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
        CAP(i,v,rr,t) * dr_dec(i,rr,hh) * hours(hh) * allowed_shifts(i,h,hh)
       }

    =g=

    sum{src, DR_SHIFT(i,v,r,h,hh,src,t) }
;

*total allowable load decrease in timeslice h
eq_dr_max_decrease(i,v,r,h,t)$[valgen(i,v,r,t)$dr1(i)$tmodel(t)$Sw_DR]..

    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
        CAP(i,v,rr,t) * dr_dec(i,rr,h) * hours(h)
       }

    =g=

    sum{(hh,src)$[allowed_shifts(i,hh,h)], DR_SHIFT(i,v,r,hh,h,src,t) }
;

*total allowable load increase in timeslice h
* DR efficiency applied to the load increase, so shows up here and not in above
* DR Shift tracks the total energy decreased, so the increase will be proportionally
* larger, requiring division here to ensure it doesn't exceed allowed increase
eq_dr_max_increase(i,v,r,h,t)$[valgen(i,v,r,t)$dr1(i)$tmodel(t)$Sw_DR]..

    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
        CAP(i,v,rr,t) * dr_inc(i,rr,h) * hours(h)
       }

    =g=

    sum{(hh,src)$[allowed_shifts(i,h,hh)], DR_SHIFT(i,v,r,h,hh,src,t) } 

    / storage_eff(i,t)
;

* tie load reductions from demand response to generation
eq_dr_gen(i,v,r,h,t)$[valgen(i,v,r,t)$dr(i)$tmodel(t)$SW_DR]..
* [plus] DR shift types reduction in load    
    sum{(hh,src)$[allowed_shifts(i,hh,h)$dr1(i)], DR_SHIFT(i,v,r,hh,h,src,t) / hours(h) }$Sw_DR

* [plus] DR shed types reduction in load
    + DR_SHED(i,v,r,h,t)$dr2(i) / hours(h)

    =e=

    GEN(i,v,r,h,t)
;

*upper bound on dr charging to recover curtailment from each source (old, new pv, new wind)
eq_dr_in_max(r,h,src,t)$[rfeas(r)$rb(r)$sum{i$dr1(i), src_curt(i,src) }$tmodel(t)]..

* the marginal curtailment from "new" sources
    sum{(i,v,rr)$[cap_agg(r,rr)$valinv(i,v,rr,t)$i_src(i,src)],
              m_cf(i,v,rr,h,t) * curt_marg(i,rr,h,t)
              * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
       }$[not sameas(src,"old")]

* [plus] the existing curtailment from "old" sources
    + curt_old(r,h,t)$sameas(src,"old")

    =g=

* stand-alone dr charging
      sum{(i,v,hh)$[dr1(i)$valgen(i,v,r,t)$src_curt(i,src)$allowed_shifts(i,h,hh)], DR_SHIFT(i,v,r,h,hh,src,t) 

* [divide] DR efficiency for load increases and hours for timeslice accounting
          / storage_eff(i,t) / hours(h) }$Sw_DR
;

*total allowable load decrease in timeslice h from shed types DR
eq_dr_max_shed(i,v,r,h,t)$[valgen(i,v,r,t)$dr2(i)$tmodel(t)$Sw_DR]..

    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
        CAP(i,v,rr,t) * dr_dec(i,rr,h) * hours(h)
       }

    =g=

    DR_SHED(i,v,r,h,t)
;

eq_dr_max_shed_hrs(i,v,r,t)$[valgen(i,v,r,t)$dr2(i)$tmodel(t)$Sw_DR]..

    sum{rr$[valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
        CAP(i,v,rr,t) * allowed_shed(i)
      }

    =g=

    sum{h$dr_dec(i,r,h), DR_SHED(i,v,r,h,t) / dr_dec(i,r,h) }
;


*===================================
* --- CANADIAN IMPORTS EQUATIONS ---
*===================================

* ---------------------------------------------------------------------------

eq_Canadian_Imports(r,szn,t)$[can_imports_szn(r,szn,t)$tmodel(t)$(Sw_Canada=1)]..

    can_imports_szn(r,szn,t)

    =g=

    sum{(i,v,h)$[canada(i)$valgen(i,v,r,t)$h_szn(h,szn)], GEN(i,v,r,h,t) * hours(h) }
;

* ---------------------------------------------------------------------------

*==========================
* --- WATER CONSTRAINTS ---
*==========================

* ---------------------------------------------------------------------------

*water accounting for all valid power plants for generation where usage is both for cooling and/or non-cooling purposes
eq_water_accounting(i,v,w,r,h,t)$[i_water(i)$valgen(i,v,r,t)$tmodel(t)$Sw_WaterMain]..

    WAT(i,v,w,r,h,t)

    =e=

*division by 1E6 to convert gal of water_rate(i,w,r) to Mgal
    GEN(i,v,r,h,t) * hours(h) * water_rate(i,w,r) / 1E6
;

* ---------------------------------------------------------------------------

*total water access is determined by total capacity
eq_water_capacity_total(i,v,r,t)$[rfeas(r)$tmodel(t)$valcap(i,v,r,t)
                                 $i_water_cooling(i)$Sw_WaterMain$Sw_WaterCapacity]..

    WATCAP(i,v,r,t)

    =e=

*require enough water capacity to allow 100% capacity factor (8760 hour operation)
*division by 1E6 to convert gal of water_rate(i,w,r) to Mgal
    (8760 / 1E6) * sum{(w,rr)$[i_w(i,w)$rfeas_cap(rr)$cap_agg(r,rr)$valcap(i,v,rr,t)],
                       CAP(i,v,rr,t) * water_rate(i,w,rr) }
;

* ---------------------------------------------------------------------------

*total water access must not exceed supply
eq_water_capacity_limit(wst,r,t)$[rfeas(r)$tmodel(t)$Sw_WaterMain$Sw_WaterCapacity]..

    m_watsc_dat(wst,"cap",r,t)

    + WATER_CAPACITY_LIMIT_SLACK(wst,r,t)

    =g=

    sum{(i,v)$[i_wst(i,wst)$valcap(i,v,r,t)], WATCAP(i,v,r,t) }
;

* ---------------------------------------------------------------------------

*water use must not exceed available access
eq_water_use_limit(i,v,w,r,szn,t)$[i_water_cooling(i)$valgen(i,v,r,t)$tmodel(t)
                                  $i_w(i,w)$Sw_WaterMain$Sw_WaterCapacity$Sw_WaterUse]..

    WATCAP(i,v,r,t) *sum{wst$i_wst(i,wst), watsa(wst,r,szn,t) }

    =g=

    sum{h$h_szn(h,szn), WAT(i,v,w,r,h,t) }
;

* ---------------------------------------------------------------------------

*==============================
* -- H2 and DAC Constraints --
*==============================

eq_prod_capacity_limit(i,v,r,h,t)$[tmodel(t)$consume(i)$valcap(i,v,r,t)$Sw_Prod]..

* available capacity [times] the conversion rate of tonne / MW
    CAP(i,v,r,t) * avail(i,v,h) * prod_conversion_rate(i,v,r,t)

    =g=

* production in that timeslice
    sum{p$i_p(i,p), PRODUCE(p,i,v,r,h,t) }
;

eq_h2_demand(p,t)$[h2_p(p)$tmodel(t)$(yeart(t)>=Sw_H2_Start)$(Sw_H2=1)]..

* annual tonnes of production
    sum{(i,v,r,h)$[h2(i)$valcap(i,v,r,t)$i_h2type(i,p)],
        PRODUCE(p,i,v,r,h,t) * hours(h) }

    =g=

* annual demand
    h2_exogenous_demand(p,t)

* assuming here that h2 production and use in RE_CT can be temporally asynchronous
* that is, the hydrogen does not need to produced in the same hour it is consumed by re-ct's
    + sum{(i,v,r,h)$[valgen(i,v,r,t)$re_ct(i)],
            GEN(i,v,r,h,t) * hours(h) * h2_rect_intensity * heat_rate(i,v,r,t)
*assumption here is that RE-CT's can only consume 'green' hydrogen
       }$sameas(p,"h2_green")
;

eq_h2_transport_caplimit(r,rr,h,t)$[rfeas(r)$rfeas(rr)$h2_routes(r,rr)$(yeart(t)>=Sw_H2_Start)
                                   $tmodel(t)$Sw_H2_Transport$(Sw_H2=2)]..

*capacity computed as cumulative investments of H2 pipelines up to the current year
    sum{tt$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))],
        H2_TRANSPORT_INV(r,rr,tt) + H2_TRANSPORT_INV(rr,r,tt) }

    =g=

*bi-directional flow of hydrogen
    sum{p$h2_p(p), H2_Flow(rr,r,p,h,t) + H2_Flow(r,rr,p,h,t) }
;

eq_h2_demand_regional(r,p,t)$[rfeas(r)$tmodel(t)$(Sw_H2=2)$(yeart(t)>=Sw_H2_Start)$h2_p(p)]..

* endogenous supply of hydrogen
    sum{h, hours(h) * (
* tonnes of production in a timeslice
        sum{(i,v)$[h2(i)$valcap(i,v,r,t)$i_h2type(i,p)],
            PRODUCE(p,i,v,r,h,t) }

* net hydrogen trade
        + sum(rr$h2_routes(rr,r),H2_Flow(rr,r,p,h,t))$[Sw_H2_Transport$(yeart(t)>=Sw_H2_Start)]
        - sum(rr$h2_routes(r,rr),H2_Flow(r,rr,p,h,t))$[Sw_H2_Transport$(yeart(t)>=Sw_H2_Start)]
        ) }

    =g=

* annual demand
    h2_exogenous_demand_regional(r,p,t)

* region-specific H2 consumption from RE-CTs
    + sum{(i,v,h)$[valgen(i,v,r,t)$re_ct(i)],
            hours(h) * GEN(i,v,r,h,t) * h2_rect_intensity * heat_rate(i,v,r,t)
*assumption here is that RE-CT's can only consume 'green' hydrogen
       }$sameas(p,"h2_green")
;
