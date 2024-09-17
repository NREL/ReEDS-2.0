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


variable    Z "--$-- total cost of the supply model, scale varies based on cost_scale";

eq_ObjFn_Supply.. Z =e=

*=======================
* -- INVESTMENT COSTS --
*=======================

         sum{t$tmodel(t), cost_scale * pvf_capital(t) *
              (
*capacity investment costs
                   sum{(i,v,r)$[valinv(i,v,r,t)],
                        INV(i,v,r,t) * cost_cap_fin_mult(i,r,t) * cost_cap(i,t) }

*growth penalties
                  + sum{(gbin,i,state)$[sum{r$[state_r(state,r)], valinv_irt(i,r,t)}],
                        cost_growth(i,state,t) * growth_penalty(gbin) * (yeart(t) - sum{tt$[tprev(t,tt)], yeart(tt) }) * GROWTH_BIN(gbin,i,state,t)
                       }$[(yeart(t)>=model_builds_start_yr)$Sw_GrowthRel]

*costs of rsc investment
              + sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$(not hydro(i))],
                   INV_RSC(i,v,r,t,rscbin) * m_rsc_dat(r,i,rscbin,"cost") }

*costs of refurbishments of RSC tech
              + sum{(i,v,r)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                    (cost_cap_fin_mult(i,r,t) * cost_cap(i,t)) * INVREFURB(i,v,r,t) * refurb_cost_multiplier(i)}

*costs of transmission lines
              + sum{(r,rr,trtype)$[routes(r,rr,trtype,t)$rfeas(r)$rfeas(rr)],
                    r_rr_transcost(r,rr) * INVTRAN(r,rr,t,trtype) }

*costs of substations
              + sum{(r,vc)$(rfeas(r)$tranfeas(r,vc)),
                    trancost(r,"cost",vc) * InvSubstation(r,vc,t) }

*hourly arbitrage value for storage - intertemporal only
              - sum{(i,v,r)$[valinv(i,v,r,t)$storage(i)],
                   hav_int(i,r,t) * INV(i,v,r,t) }
* TESTING slack variable for VRE
              + sum{(i,v,r,rs)$[vre(i)$valinv(i,v,r,t)$r_rs(r,rs)], SLACK_VRE(i,v,rs,t)} * 1e7

            ) //end to multiplier by pvf_capital
        } //end of capital cost component of objective function

*=======================
* -- OPERATION COSTS --
*=======================

         + sum{t$tmodel(t), cost_scale * pvf_onm(t) * (

*variable O&M costs
               sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$cost_vom(i,v,r,t)],
                   hours(h) * cost_vom(i,v,r,t) * GEN(i,v,r,h,t) }

*hourly arbitrage value for storage
              - sum{(i,v,r)$[valinv(i,v,r,t)$storage(i)],
                   hourly_arbitrage_value(i,r,t) * INV(i,v,r,t) }

*fixed O&M costs
              + sum{(i,v,r)$[valcap(i,v,r,t)],
                   cost_fom(i,v,r,t) * CAP(i,v,r,t) }

*operating reserve costs
*only applied to reg reserves because cost of providing other reserves is zero...
              + sum{(i,v,r,h,ortype)$[rfeas(r)$valgen(i,v,r,t)$cost_opres(i)$sameas(ortype,"spin")],
                   hours(h) * cost_opres(i) * OpRes(ortype,i,v,r,h,t) }

*cost of fuel
              + sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$heat_rate(i,v,r,t)],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN(i,v,r,h,t) }

* cost of emissions from CO2 tax
              + sum{r$[Sw_CarbonTax$(yeart(t) >= CarbonPolicyStartYear)],
                   EMIT(r,t)*CarbonTax(t) }

* cost of 'slack fuel' used to represent Naptha use in gas CC plants
              + SLACK_FUEL(t)*slackfuel_price

* --- penalty for retiring a technology (represents friction in retirements)---
              - sum{(i,v,r)$[valcap(i,v,r,t)$retiretech(i,v,r,t)],
                   cost_fom(i,v,r,t) * retire_penalty(t) *
                   (CAP(i,v,r,t)
                    - INV(i,v,r,t)$valinv(i,v,r,t)
                    - INVREFURB(i,v,r,t)$[valinv(i,v,r,t)$refurbtech(i)$Sw_Refurb] )
                   }

         )//end multiplier for pvf_onm
    }//end operations component for objective function
;
