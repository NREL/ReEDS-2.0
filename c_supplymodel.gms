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
  LOAD(r,h,t)                "--MWh-- busbar load for each balancing region"
  EVLOAD(r,h,t)              "--MWh-- busbar load specific to EVs"

* capacity and investment variables
  CAP(i,v,r,t)               "--MW-- total generation capacity"
  INV(i,v,r,t)               "--MW-- generation capacity add in year t"
  INV_REFURB(i,v,r,t)         "--MW-- investment in refurbishments of technologies that use a resource supply curve"
  INV_RSC(i,v,r,rscbin,t)    "--MW-- investment in technologies that use a resource supply curve"
  EXTRA_PRESCRIP(pcat,r,t)   "--MW-- builds beyond those prescribed once allowed in firstyear(pcat) - exceptions for gas-ct, wind-ons, and wind-ofs"

* generation and storage variables
  GEN(i,v,r,h,t)             "--MW-- electricity generation (post-curtailment) in hour h"
  CURT(r,h,t)                "--MW-- curtailment from vre generators in hour h"
  MINGEN(r,szn,t)            "--MW-- minimum generation level in each season"
  STORAGE_IN(i,v,r,h,t)      "--MW-- storage entering in hour h"
  STORAGE_LEVEL(i,v,r,h,t)   "--MWh per day-- storage level in hour h"

* trade variables
  FLOW(r,rr,h,t,trtype)          "--MW-- electricity flow on transmission lines in hour h"
  OPRES_FLOW(ortype,r,rr,h,t)    "--MW-- interregional trade of operating reserves by operating reserve type"
  PRMTRADE(r,rr,trtype,szn,t)    "--MW-- planning reserve margin capacity traded from r to rr"

* operating reserve variables
  OPRES(ortype,i,v,r,h,t)       "--MW-- operating reserves by type"

* variable fuel amounts
  GASUSED(cendiv,gb,h,t)                "--MMBtu-- total gas used by gas bin",
  VGASBINQ_NATIONAL(fuelbin,t)          "--MMBtu-- National quantity of gas by bin"
  VGASBINQ_REGIONAL(fuelbin,cendiv,t)   "--MMBtu-- Regional (census divisions) quantity of gas by bin"
  BIOUSED(bioclass,r,t)                 "--MMBtu-- total biomass used by gas bin",

* RECS variables
  RECS(RPSCat,i,st,ast,t)               "--MWh-- renewable energy credits from state s to state ss",
  ACP_Purchases(RPSCat,st,t)            "--MWh-- purchases of ACP credits to meet the RPS constraints",
  EMIT(e,r,t)                             "--metric tons co2-- total co2 emissions in a region"

* transmission variables
  CAPTRAN(r,rr,trtype,t)                "--MW-- capacity of transmission"
  INVTRAN(r,rr,t,trtype)                "--MW-- investment in transmission capacity"
  INVSUBSTATION(r,vc,t)                 "--MW-- substation investment--"

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

*main capacity constraints
 eq_cap_init_noret(i,v,r,t)  "--MW-- Existing capacity that cannot be retired is equal to exogenously-specified amount"
 eq_cap_init_retub(i,v,r,t)  "--MW-- Existing capacity that can be retired is less than or equal to exogenously-specified amount"
 eq_cap_init_retmo(i,v,r,t)  "--MW-- Existing capacity that can be retired must be monotonically decreasing"
 eq_cap_new_noret(i,v,r,t)   "--MW-- New capacity that cannot be retired is equal to sum of all previous years investment"
 eq_cap_new_retub(i,v,r,t)   "--MW-- New capacity that can be retired is less than or equal to all previous years investment"
 eq_cap_new_retmo(i,v,r,t)   "--MW-- New capacity that can be retired must be monotonically decreasing unless increased by investment"


*capacity auxilary constraints
 eq_rsc_inv_account(i,v,r,t)              "--MW-- INV for rsc techs is the sum over all bins of INV_RSC"
 eq_rsc_INVlim(r,i,rscbin,t)              "--MW-- total investment from each rsc bin cannot exceed the available investment"
 eq_refurblim(i,r,t)                      "--MW-- total refurbishments cannot exceed the amount of capacity that has reached the end of its life"
 eq_forceprescription(pcat,r,t)           "--MW-- total investment in prescribed capacity must equal amount from exogenous prescriptions"
 eq_neartermcaplimit(r,t)                 "--MW-- near-term capacity cannot be greater than projects in the pipeline"
 eq_growthlimit_relative(tg,t)            "--MW-- relative growth limit on technologies in growlim(i)"
 eq_growthlimit_absolute(tg,t)            "--MW-- absolute growth limit on technologies in growlim(i)"

* operation and reliability
 eq_supply_demand_balance(r,h,t)                      "--MW-- supply demand balance"
 eq_dhyd_dispatch(i,v,r,szn,t)                        "--MWh-- dispatchable hydro seasonal constraint"
 eq_capacity_limit(i,v,r,h,t)                         "--MW-- generation limited to available capacity"
 eq_curt_gen_balance(r,h,t)                           "--MW-- net generation and curtailment must equal gross generation"
 eq_curtailment(r,h,t)                                "--MW-- curtailment level"
 eq_mingen_lb(r,h,szn,t)                              "--MW-- lower bound on minimum generation level"
 eq_mingen_ub(r,h,szn,t)                              "--MW-- upper bound on minimum generation level"
 eq_reserve_margin(r,szn,t)                           "--MW-- planning reserve margin requirement"
 eq_transmission_limit(r,rr,h,t,trtype)               "--MW-- transmission flow limit"
 eq_minloading(i,v,r,h,hh,t)                          "--MW-- minimum loading across same-season hours"
 eq_min_cf(i,v,r,t)                                   "--MWh-- minimum capacity factor constraint"
 eq_max_cf(i,v,r,szn,t)                               "--MWh-- maximum capacity factor constraint by season"

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
 eq_BatteryMandate(r,i,t)                 "--MW-- Battery storage capacity must be greater than indicated level"

*RPS Policy
 eq_REC_Generation(RPSCat,i,st,t)         "--RECs-- Generation of RECs by state"
 eq_REC_Requirement(RPSCat,st,t)          "--RECs-- RECs generated plus trade must meet the state's requirement"
 eq_REC_ooslim(RPSCat,st,t)               "--RECs-- RECs imported cannot exceed a fraction of total requirement for certain states",
 eq_REC_launder(RPSCat,st,t)              "--RECs-- RECs laundering constraint"
 eq_REC_BundleLimit(RPSCat,st,ast,t)      "--RECS-- trade in bundle recs must be less than interstate electricity transmission"
 eq_REC_unbundledLimit(RPScat,st,t)       "--RECS-- unbundled RECS cannot exceed some percentage of total REC requirements"
 eq_RPS_OFSWind(st,t)                     "--MW-- MW of offshore wind capacity must be greater than or equal to RPS amount"
 eq_national_gen(t)                       "--MWh-- e.g. a national RPS or CES. require a certain amount of total generation to be from specified sources.",

* fuel supply curve equations
 eq_gasused(cendiv,h,t)                   "--MMBtu-- gas used must be from the sum of gas bins"
 eq_gasbinlimit(cendiv,gb,t)              "--MMBtu-- limit on gas from each bin"
 eq_gasbinlimit_nat(gb,t)                 "--MMBtu-- national limit on gas from each bin"
 eq_bioused(r,t)                          "--MMBtu-- bio used must be from the sum of bio bins"
 eq_biousedlimit(bioclass,r,t)            "--MMBtu-- limit on bio from each bin"

*following are used for regional natural gas supply curves
 eq_gasaccounting_regional(cendiv,t)           "--MMBtu-- regional gas consumption cannot exceed the amount used in bins"
 eq_gasaccounting_national(t)                  "--MMBtu-- national gas consumption cannot exceed the amount used in bins"
 eq_gasbinlimit_regional(fuelbin,cendiv,t)     "--MMBtu-- regional binned gas usage cannot exceed bin capacity"
 eq_gasbinlimit_national(fuelbin,t)            "--MMBtu-- national binned gas usage cannot exceed bin capacity"

*transmission equations
 eq_CAPTRAN(r,rr,trtype,t)                   "--MW-- capacity accounting for transmission"
 eq_prescribed_transmission(r,rr,trtype,t)   "--MW-- investment in transmission up to 2020 must be less than the exogenous possible transmission",
 eq_INVTRAN_VCLimit(r,vc)                    "--MW-- investment in transmission capacity cannot exceed that available in its VC bin"
 eq_PRMTRADELimit(r,rr,trtype,szn,t)         "--MW-- trading of PRM capacity cannot exceed the line's capacity"
 eq_SubStationAccounting(r,t)                "--Substations-- accounting for total investment in each substation"

* storage-specific equations
 eq_storage_capacity(i,v,r,h,t)           "--MW-- Second storage capacity constraint in addition to eq_capacity_limit"
 eq_storage_duration(i,v,r,h,t)           "--MWh-- limit STORAGE_LEVEL based on hours of storage available"
 eq_storage_thermalres(i,v,r,h,t)         "--MW-- thermal storage contribution to operating reserves is store_in only"
 eq_storage_level(i,v,r,h,t)              "--MWh per day-- Storage level inventory balance from one time-slice to the next"

*Canadian imports balance
 eq_Canadian_Imports(r,szn,t)             "--MWh-- Balance of Canadian imports by season"
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

    load_exog(r,h,t) + can_exports_h(r,h,t) + EVLOAD(r,h,t)$Sw_EV
;


eq_evloadcon(r,szn,t)$[rfeas(r)$tmodel(t)$Sw_EV]..

    sum{h$h_szn(h,szn),hours(h) * EVLOAD(r,h,t)}


    =e=

    ev_dynamic_demand(r,szn,t)
;


*=============================================================
* --- EQUATIONS FOR RELATING CAPACITY ACROSS TIME PERIODS ---
*=============================================================

*====================================
* -- existing capacity equations --
*====================================

eq_cap_init_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)
                           $((not retiretech(i,v,r,t)) or (yeart(t)<retireyear))]..

    m_capacity_exog(i,v,r,t)

    =e=

    CAP(i,v,r,t)
;

eq_cap_init_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)
                           $(retiretech(i,v,r,t) and (yeart(t)>=retireyear))]..

    m_capacity_exog(i,v,r,t)

    =g=

    CAP(i,v,r,t)
;

eq_cap_init_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$initv(v)
                           $(retiretech(i,v,r,t) and (yeart(t)>=retireyear))]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)], CAP(i,v,r,tt) }

    =g=

    CAP(i,v,r,t)
;


*==============================
* -- new capacity equations --
*==============================

eq_cap_new_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)
                          $((not retiretech(i,v,r,t)) or (yeart(t)<retireyear))]..

    + sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
         }

    =e=

    CAP(i,v,r,t)
;

eq_cap_new_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)
                          $(retiretech(i,v,r,t) and (yeart(t)>=retireyear))]..

    + sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
              degrade(i,tt,t) * (INV(i,v,r,tt) + INV_REFURB(i,v,r,tt)$[refurbtech(i)$Sw_Refurb])
         }

    =g=

    CAP(i,v,r,t)
;

eq_cap_new_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)
                          $(retiretech(i,v,r,t) and (yeart(t)>=retireyear))]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)], degrade(i,tt,t) * CAP(i,v,r,tt) }

    + INV(i,v,r,t)$valinv(i,v,r,t)

    + INV_REFURB(i,v,r,t)$[valinv(i,v,r,t)$refurbtech(i)$Sw_Refurb]

    =g=
    CAP(i,v,r,t)
;


eq_forceprescription(pcat,r,t)$[rfeas_cap(r)$tmodel(t)$force_pcat(pcat,t)$Sw_ForcePrescription
                               $sum{(i,newv)$[prescriptivelink(pcat,i)],valcap(i,newv,r,t)}]..

*capacity in the current period
    sum{(i,newv)$[valcap(i,newv,r,t)$prescriptivelink(pcat,i)],
        CAP(i,newv,r,t)}

    =e=

*must equal the prescribed amount
    m_required_prescriptions(pcat,r,t)

* plus any extra buildouts (no penalty here - used as free slack)
* only occuring in the first year the techs are available
    + EXTRA_PRESCRIP(pcat,r,t)$[yeart(t)>=firstyear_pcat(pcat)]
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
eq_rsc_INVlim(r,i,rscbin,t)$[tmodel(t)$rsc_i(i)$rfeas_cap(r)$m_rscfeas(r,i,rscbin)]..

*capacity indicated by the resource supply curve (with undiscovered geo available at the "discovered" amount)
    m_rsc_dat(r,i,rscbin,"cap") * (1$[not geo_undisc(i)] + geo_discovery(t)$geo_undisc(i))

    =g=

*must exceed the amount of total investment from that supply curve
    sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) <= yeart(t))$rsc_agg(i,ii)],
         INV_RSC(ii,v,r,rscbin,tt) * resourcescaler(ii) };


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
     sum{(i,v,r,rscbin)$[valinv(i,v,r,t)$m_rscfeas(r,i,rscbin)$tg_i(tg,i)],
          INV_RSC(i,v,r,rscbin,t) }
;


*capacity must be greater than supply
*note this does not apply to both storage and dispatchable hydro
*dispatchable hydro is accounted for in the eq_dhyd_dispatch
eq_capacity_limit(i,v,r,h,t)$[tmodel(t)$rfeas(r)$valgen(i,v,r,t)$(not storage_no_csp(i))$(not hydro_d(i))]..
*total amount of dispatchable capacity
    (avail(i,v,h) * sum{rr$cap_agg(r,rr),
                       CAP(i,v,rr,t)$[valcap(i,v,rr,t)$nonvariable(i)] })

*sum of non-dispatchable capacity multiplied by its rated capacity factor,
*only vre technologies are curtailable
    + sum{rr$[cap_agg(r,rr)$rfeas_cap(rr)$valcap(i,v,rr,t)$(not nonvariable(i))],
          (m_cf(i,v,rr,h,t)
           * CAP(i,v,rr,t)) }

    =g=

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
    + sum{(i,v,rr)$[cap_agg(r,rr)$valinv(i,v,rr,t)$vre(i)],
              m_cf(i,v,rr,h,t) * curt_marg(i,rr,h,t)
              * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] the curtailment from existing VRE (sequential only)
    + surpold(r,h,t)

*[plus] curtailment due to changes in minimum generation levels (sequential only)
* note the strictly greater than symbol here for mingen_firstyear
* as the initial year for mingen would be differencing from a previous
* year with no mingen considerations
    + curt_mingen(r,h,t) * sum{h_szn(h,szn), MINGEN(r,szn,t)
        - sum{tt$tprev(t,tt), MINGEN(r,szn,tt) } }$[Sw_Mingen$(yeart(t)>mingen_firstyear)]

*[minus] curtailment reduction from charging storge during timeslices with curtailment
    - sum{(i,v)$[valgen(i,v,r,t)$storage_no_csp(i)], curt_storage(i,r,h,t) * STORAGE_IN(i,v,r,h,t) }

;


eq_mingen_lb(r,h,szn,t)$[h_szn(h,szn)$rfeas(r)$(yeart(t)>=mingen_firstyear)
                        $tmodel(t)$Sw_Mingen]..

*minimum generation level in a season
    MINGEN(r,szn,t)

    =g=
*must be greater than the minimum generation level in each time slice in that season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)],GEN(i,v,r,h,t)  * minloadfrac(r,i,h) }
;


eq_mingen_ub(r,h,szn,t)$[h_szn(h,szn)$rfeas(r)$(yeart(t)>=mingen_firstyear)
                        $tmodel(t)$Sw_Mingen]..

*generation in each timeslice in a season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)],GEN(i,v,r,h,t)  }

    =g=

*must be greater than the minimum generation level
    MINGEN(r,szn,t)
;


*requirement for techs to have a minimum annual capacity factor
*disabled by default and rarely applied
eq_min_cf(i,v,r,t)$[minCF(i,t)$tmodel(t)
                   $rfeas(r)$valgen(i,v,r,t)$Sw_MinCFCon]..

    sum{h, hours(h) * GEN(i,v,r,h,t) }

    =g=

    sum{rr$[cap_agg(r,rr)$valcap(i,v,rr,t)], CAP(i,v,rr,t) } * sum{h, hours(h) } * minCF(i,t)
;


*maximum capacity factor constraint, applied by season
eq_max_cf(i,v,r,szn,t)$[maxCF(i,t)$tmodel(t)
                        $rfeas(r)$valgen(i,v,r,t)$Sw_MaxCFCon]..

    sum{rr$[cap_agg(r,rr)$valcap(i,v,rr,t)], CAP(i,v,rr,t) } * sum{h$h_szn(h,szn), hours(h) } * maxCF(i,t)

    =g=

    sum{h$h_szn(h,szn), hours(h) * GEN(i,v,r,h,t) }

;


eq_dhyd_dispatch(i,v,r,szn,t)$[rfeas(r)$tmodel(t)$hydro_d(i)$valgen(i,v,r,t)]..

*seasonal hours [times] seasonal capacity factor adjustment [times] total hydro capacity
    sum{h$[h_szn(h,szn)], avail(i,v,h) * hours(h) }

*following parameter could be wrapped into one...
    * cfhist_hyd(r,t,szn,i)
    * cf_hyd_szn_adj(i,szn,r)
    * cf_hyd(i,szn,r)
    * CAP(i,v,r,t)

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
    + sum{(trtype,rr)$[rfeas(rr)$routes(rr,r,trtype,t)], (1-tranloss(rr,r,trtype)) * FLOW(rr,r,h,t,trtype) }
    - sum{(trtype,rr)$[rfeas(rr)$routes(r,rr,trtype,t)], FLOW(r,rr,h,t,trtype) }

* [minus] storage charging
    - sum{(i,v)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,t) }

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
                            $tmodel(t)$rfeas(r)$hour_szn_group(h,hh)]..

    GEN(i,v,r,h,t)

    =g=

    GEN(i,v,r,hh,t) * minloadfrac(r,i,hh)
;


*=======================================
* --- OPERATING RESERVE CONSTRAINTS ---
*=======================================

eq_ORCap(ortype,i,v,r,h,t)$[tmodel(t)$rfeas(r)$valgen(i,v,r,t)$Sw_OpRes
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
    + sum{rr$[opres_routes(rr,r,t)$rfeas(rr)],(1-tranloss(rr,r,"AC")) * OPRES_FLOW(ortype,rr,r,h,t) }
    - sum{rr$[opres_routes(r,rr,t)$rfeas(rr)],OPRES_FLOW(ortype,r,rr,h,t) }

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
eq_PRMTRADELimit(r,rr,trtype,szn,t)$[tmodel(t)$rfeas(r)$rfeas(rr)
                                     $routes(r,rr,trtype,t)$Sw_ReserveMargin]..

*[plus] transmission capacity
    + CAPTRAN(r,rr,trtype,t)

    =g=

*[plus] firm capacity traded between regions
    + PRMTRADE(r,rr,trtype,szn,t)
;


eq_reserve_margin(r,szn,t)$[tmodel(t)$rfeas(r)$Sw_ReserveMargin]..

*[plus] sum of all non-rsc and non-storage capacity
    + sum{(i,v)$[valcap(i,v,r,t)$(not vre(i))$(not hydro(i))$(not storage(i))],
          CAP(i,v,r,t)
         }

*[plus] firm capacity from existing VRE or storage
*only used in sequential solve case (otherwise cc_old = 0)
    + sum{(i,rr)$[(vre(i) or storage(i))$cap_agg(r,rr)$rfeas_cap(rr)],
          cc_old(i,rr,szn,t)
         }

*[plus] marginal capacity credit of VRE and storage times new investment
*only used in sequential solve case (otherwise m_cc_mar = 0)
    + sum{(i,v,rr)$[cap_agg(r,rr)$(vre(i) or storage(i))$valinv(i,v,rr,t)],
          m_cc_mar(i,rr,szn,t) * (INV(i,v,rr,t) + INV_REFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] marginal capacity credit of distpv
*distpv is not in INV, so it's marginal capacity credit is treated separately using m_capacity_exog
    + sum{v$valcap('distpv',v,r,t),
          m_capacity_exog('distpv',v,r,t) - sum{tt$tprev(t,tt),
                                                m_capacity_exog('distpv',v,r,tt)
                                               }
         } * m_cc_mar('distpv',r,szn,t)$[yeart(t)>2010]

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
          CAP(i,v,r,t) * cf_hyd_szn_adj(i,szn,r) * cf_hyd(i,szn,r)
         }

*[plus] imports of firm capacity
    + sum{(rr,trtype)$[routes(rr,r,trtype,t)$rfeas(rr)],
          (1 - tranloss(rr,r,trtype)) * PRMTRADE(rr,r,trtype,szn,t)
         }

*[minus] exports of firm capacity
    - sum{(rr,trtype)$[routes(r,rr,trtype,t)$rfeas(rr)],
          PRMTRADE(r,rr,trtype,szn,t)
         }

    =g=

*[plus] the peak demand times the planning reserve margin
    + peakdem(r,szn,t) * (1 + prm(r,t))
;


*================================
* --- TRANSMISSION CAPACITY  ---
*================================

*capacity transmission is equal to the exogenously-specified level of transmission
*plus the investment in transmission capacity
eq_CAPTRAN(r,rr,trtype,t)$[routes(r,rr,trtype,t)$tmodel(t)$rfeas(r)$rfeas(rr)]..

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
    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))$(tt.val>2020)],
             INVTRAN(r,rr,tt,trtype)
           + INVTRAN(rr,r,tt,trtype)
         } $[INr(r)=INr(rr)]
;

eq_prescribed_transmission(r,rr,trtype,t)$[routes(r,rr,trtype,t)$tmodel(t)$rfeas(r)
                                           $rfeas(rr)$(yeart(t)<=2020)]..

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
    sum{(rr)$rfeas(rr),
         INVTRAN(r,rr,t,"AC")$routes(r,rr,"AC",t) + INVTRAN(rr,r,t,"AC")$routes(rr,r,"AC",t) }
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


* flow plus OR reserves cannot exceed the total transmission capacity
eq_transmission_limit(r,rr,h,t,trtype)$[tmodel(t)$rfeas(r)$rfeas(rr)
                                        $(routes(r,rr,trtype,t) or routes(rr,r,trtype,t))]..

    CAPTRAN(r,rr,trtype,t)

    =g=

    FLOW(r,rr,h,t,trtype)

*QS and OR flows only count towards the AC transmission limit
    + sum{ortype, OPRES_FLOW(ortype,r,rr,h,t) }$[Sw_OpRes$sameas(trtype,"AC")$opres_routes(r,rr,t)]
;


*=========================
* --- CARBON POLICIES ---
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
    + sum{(h,r,rr,trtype)$[AB32_r(rr)$(not AB32_r(r))$routes(r,rr,trtype,t)
                          $rfeas(r)$rfeas(rr)],
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


eq_batterymandate(r,i,t)$[rfeas(r)$tmodel(t)$batterymandate(r,i,t)
                         $sameas(i,"battery")$valcap_irt("battery",r,t)
                         $Sw_BatteryMandate]..
*battery capacity
    sum{v$valcap(i,v,r,t), CAP(i,v,r,t) }

    =g=

*must be greater than the indicated level
    batterymandate(r,i,t)
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
         RPSTechMult(i,st) * hours(h) * GEN(i,v,r,h,t) }

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
        ( (LOAD(r,h,t) - can_exports_h(r,h,t)) / distloss - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
       }
;

eq_REC_BundleLimit(RPSCat,st,ast,t)$[stfeas(st)$stfeas(ast)$tmodel(t)
                              $(not sameas(st,ast)$Sw_StateRPS)
                              $(sum{i,RecMap(i,RPSCat,st,ast,t)})
                              $(sameas(RPSCat,"RPS_Bundled") or sameas(RPSCat,"CES_Bundled"))
                              $(yeart(t)>=RPS_StartYear)]..

*amount of net transmission flows from state st to state ast
    sum{(h,r,rr,trtype)$[rfeas(r)$rfeas(rr)$r_st(r,st)$r_st(rr,ast)$routes(r,rr,trtype,t)],
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
            ( (LOAD(r,h,t) - can_exports_h(r,h,t)) / distloss - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
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
            ( (LOAD(r,h,t) - can_exports_h(r,h,t)) / distloss - sum{v$valgen("distpv",v,r,t), GEN("distpv",v,r,h,t) })
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


eq_national_gen(t)$[tmodel(t)$national_gen_frac(t)$Sw_GenMandate]..

*generation from renewables (already post-curtailment)
    sum{(i,v,r,h)$[nat_gen_tech_frac(i)$valgen(i,v,r,t)],
        GEN(i,v,r,h,t) * hours(h) * nat_gen_tech_frac(i)}

    =g=

*must exceed the mandated percentage [times]
    national_gen_frac(t) * (
* load
    sum{(r,h)$rfeas(r), LOAD(r,h,t) * hours(h) }
* [plus] transmission losses
    + sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW(rr,r,h,t,trtype) * hours(h)) }
* [plus] storage losses
    + sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN(i,v,r,h,t) * hours(h) }
    - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN(i,v,r,h,t) * hours(h) }
    )
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
    sum{(v,h)$[valgen("biopower",v,r,t)],
         hours(h) * heat_rate("biopower",v,r,t) * GEN("biopower",v,r,h,t) }

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

    + STORAGE_IN(i,v,r,h,t)

    + sum{ortype, OPRES(ortype,i,v,r,h,t) }
;

* The daily storage level in the next time-slice (h+1) must equal the
*  daily storage level in the current time-slice (h)
*  plus daily net charging in the current time-slice (accounting for losses).
*  CSP with storage energy accounting is also covered by this constraint.
eq_storage_level(i,v,r,h,t)$[valgen(i,v,r,t)$Storage(i)$tmodel(t)]..

    sum{hh$[nexth(h,hh)], STORAGE_LEVEL(i,v,r,hh,t) }

    =e=

      STORAGE_LEVEL(i,v,r,h,t)

    + storage_eff(i,t) *  hours_daily(h) * (
          STORAGE_IN(i,v,r,h,t)$storage_no_csp(i)

        + sum{rr$[CSP_Storage(i)$valcap(i,v,rr,t)$rfeas_cap(rr)$cap_agg(r,rr)],
            CAP(i,v,rr,t) * csp_sm(i) * m_cf(i,v,rr,h,t)
           }
      )

    - hours_daily(h) * GEN(i,v,r,h,t)
;

*storage charging must exceed OR contributions for thermal storage
eq_storage_thermalres(i,v,r,h,t)$[valgen(i,v,r,t)$Thermal_Storage(i)
                                 $tmodel(t)$Sw_OpRes]..

    STORAGE_IN(i,v,r,h,t)

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



*===================================
* --- CANADIAN IMPORTS EQUATIONS ---
*===================================

eq_Canadian_Imports(r,szn,t)$[can_imports_szn(r,szn,t)$tmodel(t)]..

    can_imports_szn(r,szn,t)

    =g=

    sum{(i,v,h)$[canada(i)$valgen(i,v,r,t)$h_szn(h,szn)], GEN(i,v,r,h,t) * hours(h) }
;
