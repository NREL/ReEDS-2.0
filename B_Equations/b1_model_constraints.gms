*==========================
* --- Global sets ---
*==========================

*Setting the default slash
$setglobal ds \
$setglobal copycom copy

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$setglobal copycom cp
$endif.unix

*========================================
* -- Variable Declaration --
*========================================

positive variables

*load variable - set equal to lmnt
  LOAD(r,h,t)

* capacity and investment variables
  CAP(i,v,r,t)                   "--MW-- generation capacity"
  CAP_SDBIN(i,v,r,szn,sdbin,t)   "--MW-- generation capacity by storage duration bin for relevant technologies"
  INV(i,v,r,t)                   "--MW-- generation capacity investment"
  INV_RSC(i,v,r,t,rscbin)        "--MW-- investment in technologies computed on a renewable supply curve"
  INVREFURB(i,v,r,t)               "--MW-- investment in refurbishments of technologies computed on a renewable supply curve"

* generation and storage variables
  GEN(i,v,r,h,t)            "--MW-h-- electricity generation"
  CURT(r,h,t)               "--MW-h-- Curtailed energy"
  CURT_REDUCT_TRANS(r,rr,h,t) "--MW-- curtailment reduction in r from building new transmission in rr"
  STORAGE_IN(i,v,r,h,src,t)     "--MW-h-- storage entering in hour h"
  STORAGE_LEVEL(i,v,r,h,t)    "--MW-h-- storage released in hour h"
  MINGEN(r,szn,t)           "--MW-- seasonal minimum generation level in region r"
  SLACK_FUEL(t)                               "--GJ -- slack variable for naptha use in gas cc plants"

*trade variables
  FLOW(r,rr,h,t,trtype)          "--MW-h-- electricity flow"
  OPRES_FLOW(ortype,r,rr,h,t)    "--MW-- interregional trade of operating reserves by operating reserve type"
  CURT_FLOW(r,rr,h,t)          "--MW-- interregional trade of curtailment"
  PRMTRADE(r,rr,szn,t)           "--MW-- planning reserve margin capacity traded from r to rr"

*operating reserve variables
  OPRES(ortype,i,v,r,h,t)        "--MW-- operating reserves by type"

*emission variables
  EMIT(r,t)                      "--metric tons co2-- total emissions in a region"

* transmission variables
  CAPTRAN(r,rr,trtype,t)         "--MW-- capacity of transmission"
  INVTRAN(r,rr,t,trtype)         "--MW-- investment in transmission capacity"
  INVSUBSTATION(r,vc,t)          "--MW-- substation investment--"

* TEST slack variable for VRE prescriptions equality
  SLACK_VRE(i,v,rs,t)
;

*========================================
* -- Equation Declaration --
*========================================

EQUATION

* objective function calculation
 eq_ObjFn_Supply                      "--INR-- Objective function calculation"

*load constraint
 eq_loadcon(r,h,t)

* main capacity constraints
 eq_cap_init_noret(i,v,r,t)                              "--MW-- Existing capacity that cannot be retired is equal to exogenously-specified amount (eq_cap_mo_exist_noretire)"
 eq_cap_init_retub(i,v,r,t)                  "--MW-- Existing capacity that can be retired is less than or equal to exogenously-specified amount (eq_cap_exist_retire_ub)"
 eq_cap_init_retmo(i,v,r,t)                              "--MW-- Once retired, existing cap stock cannot be built up again"
 eq_cap_mo_new_noret(i,v,r,t)      "--MW-- New capacity equals investments + refurbishments when retirements are not possible"
 eq_cap_new_retub(i,v,r,t)         "--MW-- New capacity cannot exceed INV + refurb when retirements are possible"
 eq_cap_new_retmo(i,v,r,t)         "--MW-- Once retired, new cap of each class cannot be built up again"

* other capacity constraints
 eq_rsc_inv_account(i,v,r,t)       "--MW-- total rsc investments in each resource region equal sum of inv_rsc across all resource bins in that region"
 eq_rsc_INVlim(r,i,rscbin)         "--MW-- total investment from each rsc bin cannot exceed the available investment"
 eq_refurblim(i,r,t)               "--MW-- total refurbishments cannot exceed the refurbishments available computed as the expired investments in capital"
 eq_growthlimit_relative(tg,t)      "--MW-- relative growth limit on technologies in growlim(i)"
 eq_growthlimit_absolute(r,tg,t) "--MW-- absolute growth limit on technologies in growlim(i)"
 eq_tech_phase_out(i,v,r,t)        "--MW-- mandated phase out of select technologies"
 eq_prescribedre_pre2023(i,r,t)    "--MW-- unprescribed economic RE investments are not allowed before 2024"
*eq_prescribedre_pre2024(i,r,t)    "--MW-- unprescribed economic RE investments are not allowed before 2024"
*eq_forceprescription(i,r,t)       "--MW-- after 2024 capacity must meet prescribed targets"
 eq_re_diversity(i,r,t)            "--MW-- No single resource region can have more than 15% of total national capacity (applies to WIND and UPV)"
 eq_cap_sdbin_balance(i,v,r,szn,t) "--MW-- total binned storage capacity must be equal to total storage capacity"
 eq_sdbin_limit(region,szn,sdbin,t)     "--MW-- binned storage capacity cannot exceed storage duration bin size"

* operation and reliability
 eq_supply_demand_balance(r,h,t)         "--MWh-- supply demand balance"
 eq_dhyd_dispatch(i,v,r,szn,t)           "--MWh-- dispatchable hydro seasonal constraint"
 eq_capacity_limit(i,v,r,h,t)            "--MWh-- generation limit for new capacity"
 eq_reserve_margin(region,szn,t)         "--MW--  planning reserve margin requirement"
 eq_transmission_limit(r,rr,h,t,trtype)  "--MWh-- transmission limit"
 eq_trans_reduct1(r,rr,h,t)               "--MW-- limit CURT_REDUCT_TRANS by transmission investment"
 eq_trans_reduct2(r,rr,h,t)               "--MW-- limit CURT_REDUCT_TRANS by maximum level found by Augur"
 eq_minloading(i,v,r,h,hh,t)             "--MWh-- minimum loading across same-season hours"
 eq_fuelsupply_limit(tf,t)               "--GJ-- limit on amount of fuel available per year"
 eq_minszngen(i,v,r,szn,sznszn,t)        "--MWh -- gas CC technologies need to be on every season"
 eq_min_cf(i,r,t)                      "--MWh-- minimum capacity factor constraint for each generator fleet, applied to (i,r)"

* rsc policy constraints
 eq_regen_mandate(t)                 "--fraction-- minimum generation fraction from rsc sources"
 eq_recap_mandate(t)                   "--MW-- minimum capacity from prescribed rsc sources"
 eq_recapfrac_mandate(t)               "--fraction-- minimum capacity fraction from non-fossil techs"
* eq_state_rpo(r,t,rpo_tech)                 "--fraction -- tech specific state RPO target"

* operating reserve constraints
 eq_OpRes_requirement(ortype,region,h,t)  "--MW-- operating reserve constraint"
 eq_ORCap(ortype,i,v,r,h,t)               "--MW-- operating reserve capacity availability constraint"

* regional and national pollution polivecies
 eq_co2_accounting(r,t)                   "--metric tons co2-- accounting for total CO2 emissions in a region"
 eq_co2_rate_limit(r,t)                   "--metric tons CO2 per mwh-- emission rate limit"
 eq_co2_mass_limit(t)                     "--metric tons CO2-- aggregate emission limit"

* transmission equations
 eq_CAPTRANEq(r,rr,trtype,t)                 "--MW-- capacity accounting for transmission"
 eq_INVTRAN_VCLimit(r,vc)                    "--MW-- investment in transmission capacity cannot exceed that available in its VC bin"
 eq_PRMTRADELimit(r,rr,szn,t)                "--MW-- trading of PRM capacity cannot exceed the line's capacity"
 eq_SubStationAccounting(r,t)                "--Substations-- accounting for total investment in each substation"

* storage-specific equations
 eq_storage_capacity(i,v,r,h,t)           "--MWh-- Second storage capacity constraint in addition to eq_capacity_limit"
 eq_storage_duration(i,v,r,h,t)           "--MWh-- limit STORAGE_IN based on hours of storage available"
 eq_storage_level(i,v,r,h,t)              "--MWh per day-- Storage level inventory balance from one time-slice to the next"
 eq_storage_in_min(r,h,t)                 "--MW-- lower bound on STORAGE_IN"
 eq_storage_in_max(r,h,src,t)             "--MW-- upper bound on storage charging that can come from new sources"
 eq_solar_plus_storage(r,t)                       "--MW-- solar plus storage constraint -- investment in new solar must include storage in the same region"

* curtailment equations
 eq_curt_gen_balance(r,h,t)              "--MW-- generation plus reserves cannot exceed max possible generation minus curtailment"
 eq_curtailment(r,h,t)                   "--MW-- curtailment equals avg curt + marg curt for new investments + curt from existing VREs + changes in curt due to min gen - reductions due to storage"
 eq_mingen_lb(r,h,szn,t)                 "--MW-- min gen in each season cannot be lower than min generation level (GEN times minload) in any time slice in that season"
 eq_mingen_ub(r,h,szn,t)                 "--MW-- generation in each time slice in that season must exceed the mingen level for that season"

* test a transmission growth limit of 2GW per year on any corridor
 eq_trangrowth_limit(r,rr,t)

* test annual limit on fractional curtailment
 eq_curtlim(i,t)

;


* 5GW per year transmission growth limit between any two BAs
** TODO: Make this an OPTIONAL INPUT and set off by default 
eq_trangrowth_limit(r,rr,t)$[sum(trtype,routes(r,rr,trtype,t))$tmodel(t)$rfeas(r)$rfeas(rr)]..

    5000 * (yeart(t) - sum{tt$[tprev(t,tt)], yeart(tt)})

    =g=

* limit transmission investment to 5 GW per year for any corridor
     sum{(trtype), INVTRAN(r,rr,t,trtype)$routes(r,rr,trtype,t) + INVTRAN(rr,r,t,trtype)$routes(rr,r,trtype,t)}
;

eq_curtlim(i,t)$[vre(i)$Sw_CurtLim]..

* fraction of potential generation
  0.3 * sum{(v,r,rr,h)$[cap_agg(r,rr)$valcap(i,v,rr,t)$rfeas_cap(rr)$vre(i)],
         m_cf(i,rr,h) * CAP(i,v,rr,t) }

  =g=
    
* realized generation minus total potential generation 
    sum((h,r), sum{(v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$rfeas_cap(rr)$vre(i)],
                   m_cf(i,rr,h) * CAP(i,v,rr,t) } -
               sum{(v,rr)$[valgen(i,v,r,t)$vre(i)],GEN(i,v,r,h,t)} )
;

*=========================
* --- LOAD CONSTRAINT ---
*=========================

*the marginal of of this constraint allows you to
*determine the full price of electricity load
*i.e. the price of load with consideration to operating
*reserve and planning reserve margin considered
eq_loadcon(r,h,t)$[rfeas(r)$tmodel(t)$rb(r)]..
  LOAD(r,h,t) =e= lmnt(r,h,t)
  ;


*==========================================
* --- EQUATIONS TO TRACK TOTAL CAPACITY OVER TIME ---
*==========================================


*====================================
*existing capacity equations
*====================================

* Existing capacity that cannot be retire is equal to the exogenously specified amount
eq_cap_init_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$existv(v)
                                  $((not retiretech(i,v,r,t)) or (yeart(t)<retireyear))]..

    m_capacity_exog(i,v,r,t)

    =e=

    CAP(i,v,r,t)
    ;

* For existing technologies that can be retired,
* the exogenously specified capacity is the upper bound on how much can exist
eq_cap_init_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$existv(v)
                                $(retiretech(i,v,r,t) and (yeart(t)>=retireyear))]..

    m_capacity_exog(i,v,r,t)

    =g=

    CAP(i,v,r,t)
    ;

* Once retired, existing capacity cannot be built up again
eq_cap_init_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$existv(v)
                            $(retiretech(i,v,r,t) and (yeart(t)>=retireyear))]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)],CAP(i,v,r,tt)}

    =g=

    CAP(i,v,r,t)
    ;

* Policy-driven mandatory phase of specified technologies by specific dates
eq_tech_phase_out(i,v,r,t)$[tmodel(t)$rfeas(r)$valcap(i,v,r,t)$phase_out_tech(i)$(yeart(t)>=phase_out_year(i))$Sw_TechPhaseOut]..
    CAP(i,v,r,t) + INV(i,v,r,t)

    =e=

    0
;


*====================================
*new capacity equations
*====================================

*  New capacity equals investments + refurbishments when retirements are not possible
eq_cap_mo_new_noret(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)
                                  $((not retiretech(i,v,r,t)) or (yeart(t)<retireyear))]..

    + sum{tt$[inv_cond(i,v,t,tt)$(tmodel(tt) or tfix(tt))
             $(yeart(tt)<=yeart(t))$valcap(i,v,r,tt)],
          INV(i,v,r,tt) }

    + sum{tt$[ivt(i,v,tt)$(tmodel(tt) or tfix(tt))
             $(yeart(tt)<=yeart(t))$(yeart(t)-yeart(tt)<maxage(i))],
        INVREFURB(i,v,r,tt) }$[refurbtech(i)$Sw_Refurb]

    =e=

    CAP(i,v,r,t)
    ;


* New capacity cannot exceed INV + refurb when retirements are possible
eq_cap_new_retub(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)
                                $(retiretech(i,v,r,t) and (yeart(t)>=retireyear))]..

    + sum{tt$[inv_cond(i,v,t,tt)$(tmodel(tt) or tfix(tt))
             $(yeart(tt)<=yeart(t))$valcap(i,v,r,tt)],
              INV(i,v,r,tt) }$[newv(v)]

    + sum{tt$[ivt(i,v,tt)$(tmodel(tt) or tfix(tt))$
             (yeart(tt)<=yeart(t))$(yeart(t)-yeart(tt)<maxage(i))],
              INVREFURB(i,v,r,tt) }$[refurbtech(i)$Sw_Refurb]

    =g=

    CAP(i,v,r,t)
    ;


* Once retired, new cap of each class cannot be built up again
eq_cap_new_retmo(i,v,r,t)$[valcap(i,v,r,t)$tmodel(t)$newv(v)
                                    $(retiretech(i,v,r,t) and (yeart(t)>=retireyear))]..

    sum{tt$[tprev(t,tt)$valcap(i,v,r,tt)], CAP(i,v,r,tt)}
    + INV(i,v,r,t)$inv_cond(i,v,t,t)
    + INVREFURB(i,v,r,t)$ivt(i,v,t)

    =g=

    CAP(i,v,r,t)
    ;


* Prior to 2023, all additions are prescribed.
* Wind and solar additions with known locations are included in m_capacity_exog
* When locations are not known, the prescribed capacity is added through INV and ReEDS selects the location
eq_prescribedre_pre2023(i,r,t)$[rfeas(r)$tmodel(t)$required_prescriptions(i,r,t)$(yeart(t) < 2023)
                             $prescriptivetech(i)$Sw_Prescribed]..

* investments in prescribed capacity that correlates to the general category in each BA
    sum{(rs,v)$r_rs(r,rs), m_capacity_exog(i,v,rs,t) }

  + sum{(rs,v,tt,rscbin)$[inv_cond(i,v,t,tt)$(tmodel(tt) or tfix(tt))$(yeart(tt)<=yeart(t))],
      INV_RSC(i,v,rs,tt,rscbin)$[(yeart(t)-yeart(tt)<maxage(i))$r_rs(r,rs)$m_rscfeas(rs,i,rscbin)] }

  + sum{(rs,v)$[r_rs(r,rs)$valinv(i,v,r,t)$vre(i)], SLACK_VRE(i,v,rs,t) }

        =e=

*must equal the prescribed amount
    m_required_prescriptions(i,r,t)

;


* capacity must meet prescribed targets.
*eq_forceprescription(i,r,t)$[tmodel(t)$required_prescriptions(i,r,t)$(yeart(t) > 2022)
*                                 $prescriptivetech(i)$Sw_Prescribed]..

* sum{(v)$[valcap(i,v,r,t)], CAP(i,v,r,t) }

*        =g=

*must be greater than the prescribed amount
*    m_required_prescriptions(i,r,t)
*;


*here we limit the amount of refurbishments available in specific year
*this is the sum of all previous year's investment that is now beyond the age
*limit (i.e. it has exited service) plus the amount of retired exogenous capacity
*that we begin with
eq_refurblim(i,r,t)$[rfeas_cap(r)$tmodel(t)$refurbtech(i)$Sw_Refurb]..
*investments that meet the refurbishment requirement (i.e. they've expired)
    sum{(vv,tt)$[m_refurb_cond(i,vv,r,t,tt)$newv(vv)
                $(tmodel(tt) or tfix(tt))$valcap(i,vv,r,tt)],
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
    sum{(vv,tt)$[(yeart(tt)<=yeart(t))$(tmodel(tt) or tfix(tt))$(yeart(t)-yeart(tt)<maxage(i))],
         INVREFURB(i,vv,r,tt) }
;


*aggregate wind and solar investments across all resource bins
eq_rsc_inv_account(i,v,r,t)$[tmodel(t)$valinv(i,v,r,t)$vre(i)]..

  sum{rscbin$m_rscfeas(r,i,rscbin),INV_RSC(i,v,r,t,rscbin) }

  =e=
  INV(i,v,r,t)
  ;


*note that the following equation only restricts inv_rsc and not inv_refurb
*therefore, the capacity indicated by teh supply curve may be limiting
*but the plant can still be refurbished
eq_rsc_INVlim(r,i,rscbin)$[vre(i)$m_rscfeas(r,i,rscbin)]..

*capacity indicated by the resource supply curve
    m_rsc_dat(r,i,rscbin,"cap")

    =g=

*must exceed the amount of total investment from that supply curve
    sum{(v,t), INV_RSC(i,v,r,t,rscbin)$valinv(i,v,r,t) * resourcescalar(i)}
  ;


*limit on year-on-year technology growth rate to avoid unrealistic investment growth
eq_growthlimit_relative(tg,t)$[tmodel(t)$Sw_GrowthRel$(yeart(t)>2022)$(yeart(t)<2031)$growth_limit_relative(tg)]..

*the relative growth rate multiplied by the existing technology group's existing capacity
    (growth_limit_relative(tg)) ** (sum{tt$[tprev(tt,t)], yeart(tt)} - yeart(t)) *
    sum{(i,v,r,tt)$[tprev(t,tt)$valcap(i,v,r,tt)$tg_i(tg,i)$rfeas_cap(r)],
         CAP(i,v,r,tt) }

    =g=

*must exceed the current periods investment
    sum{(i,v,r)$[valinv(i,v,r,t)$tg_i(tg,i)],
        INV(i,v,r,t)}
;


*for some technologies and region, maximum amount of capacity that can be developed based on policy/environmental/resource constraints
eq_growthlimit_absolute(r,tg,t)$[growth_limit_absolute(r,tg)$tmodel(t)$Sw_GrowthAbs]..

* the absolute limit of growth (in MW)
     growth_limit_absolute(r,tg)

     =g=

* must exceed the total capacity
* note scarcely-used set 'tg' is technology group (allows for lumping together or all wind/solar techs)
     sum{(i,v,rr)$[tg_i(tg,i)$cap_agg(r,rr)$vre(i)],
         CAP(i,v,rr,t)} +
     sum{(i,v)$[tg_i(tg,i)$(not vre(i))],
         CAP(i,v,r,t)}

;


eq_regen_mandate(t)$[tmodel(t)$Sw_REGenMandate]..

    sum{(ii,v,r,h)$[rfeas(r)$tmodel(t)$valgen(ii,v,r,t)$genmandate_tech_set(ii)],
        GEN(ii,v,r,h,t) * hours(h)}

        =g=

    sum{(ii,v,r,h)$[rfeas(r)$tmodel(t)$valgen(ii,v,r,t)],
        GEN(ii,v,r,h,t) * hours(h)}*re_mandate_gen(t)
;


eq_recap_mandate(t)$[tmodel(t)$Sw_RECapMandate]..
   
* wind and solar capacity
    sum{(i,v,r)$[rfeas(r)$tmodel(t)$valcap(i,v,r,t)$capmandate_tech_set(i)],
        CAP(i,v,r,t)} 

        =g=

    re_mandate_cap(t)
;

eq_recapfrac_mandate(t)$[tmodel(t)$Sw_RECapFracMandate]..

* wind and solar capacity
    sum{(i,v,r)$[rfeas(r)$tmodel(t)$valcap(i,v,r,t)$capmandate_tech_set(i)],
        CAP(i,v,r,t)} 

        =g=

* fraction of total capacity
    sum{(i,v,r)$[rfeas(r)$tmodel(t)$valcap(i,v,r,t)$(not storage(i))],
        CAP(i,v,r,t)}*re_mandate_capfrac(t)
;


*capacity must be greater than supply
*note this does not apply to both storage and dispatchable hydro
*dispatchable hydro is accounted for in the eq_dhyd_dispatch
eq_capacity_limit(i,v,r,h,t)$[tmodel(t)$rfeas(r)$valgen(i,v,r,t)$(not storage(i))]..

*total amount of dispatchable, non-hydro capacity
    outage(i,h) * sum{rr$cap_agg(r,rr),
                      CAP(i,v,rr,t)$[valcap(i,v,rr,t)$(not cf_tech(i))$(not hydro_d(i))]}

*total amount of dispatchable hydro capacity
    + outage(i,h) * sum{rr$cap_agg(r,rr),
                        CAP(i,v,rr,t)$[valcap(i,v,rr,t)$hydro_d(i)]}

*sum of non-dispatchable capacity multiplied by its rated capacity factor,
*only vre technologies are curtailable
    + sum{rr$[cap_agg(r,rr)$rfeas_cap(rr)$valcap(i,v,rr,t)$cf_tech(i)$(not hydro_d(i))],
          (m_cf(i,rr,h)
           * CAP(i,v,rr,t))}

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
         m_cf(i,rr,h) * CAP(i,v,rr,t) }

*[minus] curtailed generation
    - CURT(r,h,t)

    =g=

*must exceed realized generation
    sum{(i,v)$[valgen(i,v,r,t)$vre(i)],GEN(i,v,r,h,t)}

*[plus] sum of operating reserves by type
    + sum{(ortype,i,v)$[reserve_frac(i,ortype)$valgen(i,v,r,t)$vre(i)],
         OPRES(ortype,i,v,r,h,t) }$Sw_OpRes
;


*VRE curtailment equals curtailment calculated from the last iteration plus changes due to
*redispatching the thermal fleet, investments in storage, and investments in VRE
eq_curtailment(r,h,t)$[tmodel(t)$rfeas(r)]..

*curtailment
    CURT(r,h,t)

    =g=

*curtailment of VRE (intertemporal only)
    sum{(i,v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$rfeas_cap(rr)$vre(i)],
        m_cf(i,rr,h) * CAP(i,v,rr,t) * curt_int(i,rr,h,t)
       }

*[plus] curtailment due to changes in minimum generation levels
    + (curt_mingen_int(r,h,t) * sum{h_szn(h,szn), MINGEN(r,szn,t) })$Sw_Mingen

*[plus] excess curtailment (intertemporal only)
    + curt_excess(r,h,t)


*[plus] the marginal curtailmet of new VRE (sequential only)
*Note: new distpv is included with curt_old
    + sum{(i,v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$vre(i)],
              m_cf(i,rr,h) * curt_marg(i,rr,h,t)
              * (INV(i,v,rr,t) + INVREFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
         }

*[plus] the curtailment from existing VRE (sequential only)
    + curt_old(r,h,t)

*[plus] curtailment due to changes in minimum generation levels (sequential only)
    + curt_mingen(r,h,t) * sum{h_szn(h,szn), MINGEN(r,szn,t)
        - sum{tt$tprev(t,tt), mingen_postret(r,szn,tt) } }$Sw_Mingen


*[minus] curtailment reduction from charging storge during timeslices with curtailment
        - sum{(i,v,src)$[valgen(i,v,r,t)$storage(i)],
           curt_stor(i,v,r,h,src,t) * STORAGE_IN(i,v,r,h,src,t)
         }

*[minus] curtailment reduction from building new transmission to rr
    - sum{rr$sum{trtype, routes(r,rr,trtype,t) }, CURT_REDUCT_TRANS(r,rr,h,t) }

* [plus] net flow of curtailment with no transmission losses (otherwise CURT can be turned into transmission losses)
    + sum{(trtype,rr)$routes(rr,r,trtype,t), CURT_FLOW(r,rr,h,t) }$Sw_CurtFlow
    - sum{(trtype,rr)$routes(r,rr,trtype,t), CURT_FLOW(r,rr,h,t) }$Sw_CurtFlow
;


eq_mingen_lb(r,h,szn,t)$[h_szn(h,szn)$rfeas(r)$tmodel(t)$Sw_MinGen]..

*minimum generation level in a season
    MINGEN(r,szn,t)

    =g=

*must be greater than the minimum generation level in each time slice in that season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)$(not storage(i))],GEN(i,v,r,h,t)  * minloadfrac(r,i,h) }
;


eq_mingen_ub(r,h,szn,t)$[h_szn(h,szn)$rfeas(r)$tmodel(t)$Sw_MinGen]..

*generation in each timeslice in a season
    sum{(i,v)$[valgen(i,v,r,t)$minloadfrac(r,i,h)$(not storage(i))],GEN(i,v,r,h,t)  }

    =g=

*must be greater than the minimum generation level
    MINGEN(r,szn,t)
;


eq_dhyd_dispatch(i,v,r,szn,t)$[rfeas(r)$tmodel(t)$hydro_d(i)$valgen(i,v,r,t)]..

*seasonal hours [times] seasonal capacity factor adjustment [times] total hydro capacity
    sum{h$[h_szn(h,szn)],hours(h) }

*following parameter c♦ould be wrapped into one...
    * cf_adj_hyd(i,szn,r)
    * CAP(i,v,r,t)

    =g=

*total seasonal generation
    sum{h$[h_szn(h,szn)], hours(h)
        * ( GEN(i,v,r,h,t)
              + sum{ortype$reserve_frac(i,ortype), OPRES(ortype,i,v,r,h,t) }$Sw_OpRes )
       }
;

*requirement for fleet of a given tech to have a minimum annual capacity factor
eq_min_cf(i,r,t)$[minCF(i)$tmodel(t)$sum{v, valgen(i,v,r,t) }$Sw_MinCF]..

    sum{(v,h)$[valgen(i,v,r,t)], hours(h) * GEN(i,v,r,h,t) }

    =g=

    sum{v, sum{rr$[cap_agg(r,rr)$valcap(i,v,rr,t)], CAP(i,v,rr,t) } }
    * sum{h, hours(h) } * minCF(i)
;

*===============================
* --- SUPPLY DEMAND BALANCE ---
*===============================

eq_supply_demand_balance(r,h,t)$[rfeas(r)$tmodel(t)$rb(r)]..

* generation
    sum{(i,v)$valgen(i,v,r,t), GEN(i,v,r,h,t) }

* [plus] net transmission with imports reduced by losses
    + sum{(trtype,rr)$[rfeas(rr)$routes(rr,r,trtype,t)], (1-tranloss(rr,r)) * FLOW(rr,r,h,t,trtype) }
    - sum{(trtype,rr)$[rfeas(rr)$routes(r,rr,trtype,t)], FLOW(r,rr,h,t,trtype) }

* [minus] storage charging
    - sum{(i,v,src)$[valgen(i,v,r,t)$storage(i)], STORAGE_IN(i,v,r,h,src,t) }

* [plus] imports from Bhutan
    + sum{exporter, import(exporter,r,h,t)$Sw_SAsia_Trade }

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
                            $tmodel(t)$rfeas(r)$hour_szn_group(h,hh)$Sw_MinGen$(not storage(i))]..

    GEN(i,v,r,h,t)

    =g=

    GEN(i,v,r,hh,t) * minloadfrac(r,i,hh)
;

* gas CC and nuclear plants must generate something each season.
eq_minszngen(i,v,r,szn,sznszn,t)$[valgen(i,v,r,t)$(GASCC(i) or NUCLEAR(i))
                            $tmodel(t)$rfeas(r)]..

    sum{h$h_szn(h,szn), GEN(i,v,r,h,t) }

    =g=

    sum{h$h_szn(h,sznszn), GEN(i,v,r,h,t)*minloadfrac(r,i,h) }
;


*=========================
* --- Fuel Supply Limit ---
*=========================

* total fuel consumed each year across all states cannot exceed the max availble fuel
eq_fuelsupply_limit(tf,t)$[tmodel(t)$Sw_FuelSupply]..

     fuel_limit(tf,t) + SLACK_FUEL(t)

      =g=

      sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$heat_rate(i,v,r,t)$tf_i(tf,i) ],
      hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t) }*1e-6
      ;


*============================
* --- STORAGE CONSTRAINTS ---
*============================

*storage use cannot exceed capacity
eq_storage_capacity(i,v,r,h,t)$[valgen(i,v,r,t)$storage(i)$tmodel(t)$Sw_Storage]..

    CAP(i,v,r,t)$valcap(i,v,r,t) * outage(i,h)

    =g=

    GEN(i,v,r,h,t)

    + sum{src, STORAGE_IN(i,v,r,h,src,t) }

    + sum{ortype, OPRES(ortype,i,v,r,h,t) }$Sw_StorOpres
;


* The daily storage level in the next time-slice (h+1) must equal the
*  daily storage level in the current time-slice (h)
*  plus daily net charging in the current time-slice (accounting for losses).
eq_storage_level(i,v,r,h,t)$[valgen(i,v,r,t)$storage(i)$tmodel(t)$Sw_Storage]..

    sum{(hh)$[nexth(h,hh)], STORAGE_LEVEL(i,v,r,hh,t) }

    =e=

      STORAGE_LEVEL(i,v,r,h,t)

    + storage_eff(i) *  hours_daily(h) * (
          sum{src, STORAGE_IN(i,v,r,h,src,t) }
      )

* natural inflows for existing pumped hydro
*  + (CAP(i,v,r,t)$UPGRADE(i) * outage(i,h) * hours_daily(h) *
   + (CAP(i,v,r,t)$existv(v) * outage(i,h) * hours_daily(h) *
        sum{szn$h_szn(h,szn), cf_adj_hyd(i,szn,r)})

    - hours_daily(h) * GEN(i,v,r,h,t)
;


*batteries are limited by their duration for each normalized hour per season
eq_storage_duration(i,v,r,h,t)$[valcap(i,v,r,t)$battery(i)
                                         $tmodel(t)$Sw_Storage]..

    storage_duration(i) * CAP(i,v,r,t)

    =g=

    STORAGE_LEVEL(i,v,r,h,t)
;

*lower bound on storage charging
eq_storage_in_min(r,h,t)$[sum{(i,v)$storage(i),valgen(i,v,r,t)}$tmodel(t)$Sw_Storage]..

    sum{(i,v)$[storage(i)$valgen(i,v,r,t)], STORAGE_IN(i,v,r,h,"other",t)}

    =g=

    storage_in_min(r,h,t)
;

*upper bound on storage charging from a given source
eq_storage_in_max(r,h,src,t)$[rfeas(r)$rb(r)$(not sameas(src,"other"))$tmodel(t)$Sw_Storage]..

*[plus] the marginal curtailment from new src
    sum{(i,v,rr)$[cap_agg(r,rr)$valinv(i,v,rr,t)$i_src(i,src)],
              m_cf(i,rr,h) * curt_marg(i,rr,h,t)
              * (INV(i,v,rr,t) + INVREFURB(i,v,rr,t)$[refurbtech(i)$Sw_Refurb])
       }$[not sameas(src,"old")]

*[plus] the existing curtailment from "old" src
    + curt_old(r,h,t)$sameas(src,"old")

    =g=

    sum{(i,v)$[storage(i)$valgen(i,v,r,t)], STORAGE_IN(i,v,r,h,src,t) }
;

*binned capacity must be the same as capacity
eq_cap_sdbin_balance(i,v,r,szn,t)$[tmodel(t)$valcap(i,v,r,t)$storage(i)]..

*total capacity in each region
    CAP(i,v,r,t)

    =e=

*sum of all binned capacity within each region
    sum{sdbin, CAP_SDBIN(i,v,r,szn,sdbin,t) }
;

*binned capacity cannot exceed sdbin size
eq_sdbin_limit(region,szn,sdbin,t)$[tmodel(t)]..

*sdbin size from CC script
    sdbin_size(region,szn,sdbin,t)

    =g=

*capacity in each sdbin adjusted by the appropriate CC value
    sum{(i,v,r)$[r_region(r,region)$valcap(i,v,r,t)$storage(i)],
        CAP_SDBIN(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin)
       }

;

eq_solar_plus_storage(r,t)$[tmodel(t)$(yeart(t) > 2023)$Sw_SolarPlusStorage]..

*investment in 4-hr storage
        sum{(i,v), INV(i,v,r,t)$[valinv(i,v,r,t)$sameas(i,'BATTERY_4')] }

        =g=

*must be at least 60% of UPV invetsment in the same region
        sum{(i,v,rr)$cap_agg(r,rr), INV(i,v,rr,t)$[valinv(i,v,rr,t)$upv(i)]} * 0.6

;

*=======================================
* --- OPERATING RESERVE CONSTRAINTS ---
*=======================================


eq_ORCap(ortype,i,v,r,h,t)$[tmodel(t)$rfeas(r)$valgen(i,v,r,t)$Sw_OpRes
                            $reserve_frac(i,ortype)$(not storage(i))$(not hydro_nd(i))]..

*the ramplimit times..
    reserve_frac(i,ortype) * (

* the amount of committed capacity available for a season is assumed to be the amount
* of generation from the timeslice that has the highest demand
         sum{(szn,hh)$[h_szn(h,szn)$maxload_szn(r,hh,t,szn)],
              GEN(i,v,r,hh,t)  }
              )

    =g=

    OPRES(ortype,i,v,r,h,t)
;


*operating reserves must meet the operating reserves requirement (by ortype)
eq_OpRes_requirement(ortype,region,h,t)$[tmodel(t)$Sw_OpRes]..

*operating reserves from technologies that can produce them (i.e. those w/ramp rates)
    sum{(i,v,r)$[r_region(r,region)$valgen(i,v,r,t)$rfeas(r)$(reserve_frac(i,ortype) or hydro_d(i))$(not hydro_nd(i))$(not imports(i))],
         OPRES(ortype,i,v,r,h,t) }

*[plus] net transmission of operating reserves (while including losses for imports)
    + sum{(rr,r),(1-tranloss(rr,r))*OPRES_FLOW(ortype,rr,r,h,t) }$Sw_OpResTrade
    - sum{(r,rr),OPRES_FLOW(ortype,r,rr,h,t) }$Sw_OpResTrade

    =g=

*must meet the demand for or type
*first portion is from load
    sum{r$[rfeas(r)$r_region(r,region)],orperc(ortype,"or_load") * LOAD(r,h,t)}
;



*=================================
* --- PLANNING RESERVE MARGIN ---
*=================================

*trade of planning reserve margin capacity cannot exceed the transmission line's available capacity
eq_PRMTRADELimit(r,rr,szn,t)$[tmodel(t)$rfeas(r)$rfeas(rr)
                         $sum{trtype,routes_region(r,rr,trtype,t)}$Sw_PRM]..

    sum{trtype$[routes_region(r,rr,trtype,t)],CAPTRAN(r,rr,trtype,t)}

    =g=

    PRMTRADE(r,rr,szn,t)
;

*following equation assumes the ratio of all demand to peak demand remains constant
eq_reserve_margin(region,szn,t)$[tmodel(t)$Sw_PRM]..

*sum of all non-rsc and non-storage capacity
    sum{(i,v,r)$[r_region(r,region)$valcap(i,v,r,t)$(not rsc_i(i))$(not storage(i))],
        CAP(i,v,r,t) }

*average capacity value times capacity
*used in rolling window and full intertemporal solve
    + sum{r$r_region(r,region),
        sum{(i,v,rr)$[cap_agg(r,rr)$(rsc_i(i))$(not hydro(i))$(not storage(i))$valcap(i,v,rr,t)],
          cc_int(i,v,rr,szn,t) * CAP(i,v,rr,t)}
        }

* contribution from hydro pondage
    + sum{(i,v,r)$[r_region(r,region)$valcap(i,v,r,t)$hydro_pond(i)],
         cc_hydro(i,r,szn,t) * CAP(i,v,r,t) }

* contribution from dispatchable hydro storage (excluding imports)
    + sum{(i,v,r)$[r_region(r,region)$valcap(i,v,r,t)$hydro_stor(i)],
          CAP(i,v,r,t) }

*contribution from importing hydro if switch is turned on
    + sum{(i,v,r)$[r_region(r,region)$valcap(i,v,r,t)$hydro_d(i)$imports(i)$Sw_SAsia_PRM],
          CAP(i,v,r,t) }

*[plus] firm capacity contribution from all binned storage capacity
*for now this is just battery and pumped-hydro
    + sum{(i,v,r,sdbin)$[r_region(r,region)$storage(i)$valcap(i,v,r,t)],
          cc_storage(i,sdbin) * CAP_SDBIN(i,v,r,szn,sdbin,t)
         }

*[plus] net trade of firm capacity
    + sum{(r,rr)$[r_region(r,region)$sum{trtype,routes_region(rr,r,trtype,t)}$rfeas(rr)$Sw_PRMTrade],(1-tranloss(rr,r))*PRMTRADE(rr,r,szn,t) }
    - sum{(rr,r)$[r_region(r,region)$sum{trtype,routes_region(r,rr,trtype,t)}$rfeas(rr)$Sw_PRMTrade],PRMTRADE(r,rr,szn,t) }

    =g=

    (1+prm_region(region,t)) * peakdem_region(region,szn,t)
;

*================================
* --- TRANSMISSION CAPACITY  ---
*================================

*capacity transmission is equal to the exogenously-specified level of transmission
*plus the investment in transmission capacity
eq_CAPTRANEq(r,rr,trtype,t)$[routes(r,rr,trtype,t)$tmodel(t)$rfeas(r)$rfeas(rr)]..

    CAPTRAN(r,rr,trtype,t)

    =e=

*exogenous transmission capacity has already included both r,rr and rr,r in a_inputs
    trancap_exog(r,rr,trtype,t)

*all previous year's investment, note this can apply for both r and rr
    + sum{(tt)$[(yeart(tt) <= yeart(t))$(tmodel(tt) or tfix(tt))$(tt.val>2022)],
         INVTRAN(r,rr,tt,trtype) + INVTRAN(rr,r,tt,trtype) }
;


*the total amount of substations must fill
*all of the substation voltage class bins
eq_SubStationAccounting(r,t)$[rfeas(r)$tmodel(t)]..

*sum over all voltage classes of substation investments
    sum{vc$tranfeas(r,vc),INVSUBSTATION(r,vc,t) }

    =e=

*is equal to the total amount of AC investment, both in- and out- going
    sum{(rr)$rfeas(rr),
         INVTRAN(r,rr,t,"AC")$routes(r,rr,"AC",t) + INVTRAN(rr,r,t,"AC")$routes(rr,r,"AC",t) }
;


*investment in each voltage class cannot exceed the capacity
*of that substation bin (aka voltage class)
eq_INVTRAN_VCLimit(r,vc)$[rfeas(r)$tranfeas(r,vc)]..

*the voltage class bin's available capacity
    trancost(r,"CAP",vc)

    =g=

*cannot exceed total capacity
    sum{t$[tmodel(t) or tfix(t)],INVSUBSTATION(r,vc,t) }
;


* flow plus OR reserves cannot exceed the total transmission capacity
eq_transmission_limit(r,rr,h,t,trtype)$[tmodel(t)$rfeas(r)$rfeas(rr)
                                        $(routes(r,rr,trtype,t) or routes(rr,r,trtype,t))$Sw_TxLimit]..

    CAPTRAN(r,rr,trtype,t)

    =g=

    FLOW(r,rr,h,t,trtype)

*[plus] operating reserve flows (operating reserves can only be transferred across AC lines)
    + sum{ortype,OPRES_FLOW(ortype,r,rr,h,t) }$[sameas(trtype,"AC")$Sw_OpResTrade]

*[plus] curtailment flows
    + CURT_FLOW(r,rr,h,t)$Sw_CurtFlow
;

* curtailment reduction from new transmission has to be less than transmission investment times the curtailment reduction rate
eq_trans_reduct1(r,rr,h,t)$[tmodel(t)$(sum{trtype, routes(r,rr,trtype,t) } or sum{trtype, routes(rr,r,trtype,t) })]..

    curt_tran(r,rr,h,t) * sum{trtype$(routes(r,rr,trtype,t) or routes(rr,r,trtype,t)), INVTRAN(r,rr,t,trtype) }

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
* --- CARBON POLICIES ---
*=========================

eq_co2_accounting(r,t)$[rfeas(r)$tmodel(t)]..

    EMIT(r,t)

    =e=

    sum{(i,v,h)$[valgen(i,v,r,t)],
         hours(h) * co2_rate(i,v,r,t) * GEN(i,v,r,h,t) }
;


eq_co2_rate_limit(r,t)$[co2rate(r,t)$(yeart(t)>=CarbonPolicyStartYear)$tmodel(t)$rfeas(r)]..

    co2_rate_limit(r,t) * (
         sum{(i,v,h)$[valgen(i,v,r,t)],  hours(h) * GEN(i,v,r,h,t) }
    )

    =g=

    EMIT(r,t)
;


eq_co2_mass_limit(t)$[(yeart(t)>=CarbonPolicyStartYear)$tmodel(t)$Sw_CO2Limit]..

    co2_mass_limit_nat(t)

    =g=

    sum{r$rfeas(r),EMIT(r,t) }
;

*eq_state_rpo(r,t,rpo_tech)$[tmodel(t)$rfeas(r)$state_rpo(t,rpo_tech,r)]..

*sum{ (i,v,h)$valgen(i,v,r,t), hours(h) * GEN(i,v,r,h,t)$rpotech_i(rpo_tech,i) }

*  =g=

*  sum{ (i,v,h)$valgen(i,v,r,t), hours(h) * GEN(i,v,r,h,t)$(not hydro(i)) } * state_rpo(t,rpo_tech,r)
*  ;

*=========================
* --- RE GEOGRAPHIC DIVERSITY CONSTRAINT ---
*=========================

eq_re_diversity(i,r,t)$[tmodel(t)$rs(r)$rfeas(r)$(wind(i) or upv(i))$Sw_REdiversity]..

* sum of all investments multiplied by the diversity factor
    sum{(rr,v)$[rs(rr)$valinv(i,v,rr,t)], INV(i,v,rr,t)} * REdiversity

    =g=

* must be greather than investment in any single resource region
    sum{(v)$[rs(r)$valinv(i,v,r,t)], INV(i,v,r,t)}
;

$ontext
EQUATION
* test Raj by itself
* eq_Raj_import1                      "--MW-- limit imports into Rajasthan";
 eq_Raj_import2                      " limit in other direction";

*eq_Raj_import1(r,rr,h,t,trtype)$[tmodel(t)$rfeas(r)$rfeas(rr)
*                                        $(routes(r,"Rajasthan",trtype,t) or routes("Rajasthan",r,trtype,t))
*                                        $(yeart(t) > 2025)]..

*    FLOW(r,rr,h,t,trtype)

*    =e=

*    0;

eq_Raj_import2(rr,r,h,t,trtype)$[tmodel(t)$rfeas(r)$rfeas(rr)
                                        $(routes(r,"Rajasthan",trtype,t) or routes("Rajasthan",r,trtype,t))
                                        $(yeart(t) > 2025)]..

    FLOW(rr,r,h,t,trtype)

    =e=

    0;
$offtext
