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
                   sum{(i,c,r)$[newc(c)$valcap(i,c,r,t)],
                        INV(i,c,r,t) * cost_cap_fin_mult(r,i,t) * cost_cap(i,t) }

*costs of rsc investment
              + sum{(i,c,r,rscbin)$[m_rscfeas(r,i,rscbin)$valcap(i,c,r,t)$rsc_i(i)$newc(c)$(not hydro(i))],
                   Inv_RSC(i,c,r,t,rscbin) * m_rsc_dat(r,i,rscbin,"cost") }

*costs of refurbishments of RSC tech
              + sum{(i,c,r)$[Sw_Refurb$ict(i,c,t)$refurbtech(i)],
                    (cost_cap_fin_mult(r,i,t) * cost_cap(i,t)) * InvRefurb(i,r,t) }

*costs of transmission lines
              + sum{(r,rr,trtype)$[routes(r,rr,trtype,t)$rfeas(r)$rfeas(rr)],
                    ((InterTransCost(r) + InterTransCost(rr))/2) * InvTran(r,rr,t,trtype) * distance(r,rr) }

*costs of substations
              + sum{(r,vc)$(rfeas(r)$tranfeas(r,vc)),
                    trancost(r,"cost",vc) * InvSubstation(r,vc,t) }

*cost of back-to-back AC-DC-AC interties
*conditional here that the interconnects must be different
              + sum{(r,rr)$[routes(r,rr,"DC",t)$rfeas(r)$rfeas(rr)],
                    Trans_Intercost * InvTran(r,rr,t,"DC") }

            ) //end to multiplier by pvf_capital
        } //end of capital cost component of objective function

*=======================
* -- OPERATION COSTS --
*=======================

         + sum{t$tmodel(t), cost_scale * pvf_onm(t) * (

*variable O&M costs
               sum{(i,c,r,h)$[rfeas(r)$valgen(i,c,r,t)$cost_vom(i,c,r,t)],
                   hours(h) * cost_vom(i,c,r,t) * GEN(i,c,r,h,t) }

*fixed O&M costs
              + sum{(i,c,r)$[valcap(i,c,r,t)],
                   cost_fom(i,c,r,t) * CAP(i,c,r,t) }

*operating reserve costs
*only applied to reg reserves because cost of providing other reserves is zero...
              + sum{(i,c,r,h,ortype)$[rfeas(r)$valgen(i,c,r,t)$cost_opres(i)$sameas(ortype,"spin")],
                   hours(h) * cost_opres(i) * OpRes(ortype,i,c,r,h,t) }

*cost of fuel 
              + sum{(i,c,r,h)$[rfeas(r)$valgen(i,c,r,t)$heat_rate(i,c,r,t)],
                   hours(h) * heat_rate(i,c,r,t) * fuel_price(i,r,t) * GEN(i,c,r,h,t) }

* cost of emissions from CO2 tax
              + sum{r$[Sw_CarbonTax$(yeart(t) >= CarbonPolicyStartYear)], 
                   EMIT(r,t)*CarbonTax(t) }

* cost of 'slack fuel' used to represent Naptha use in gas CC plants
              + SLACK_FUEL(t)*slackfuel_price

         )//end multiplier for pvf_onm
    }//end operations component for objective function
;
