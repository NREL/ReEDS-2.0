*** Shrink sets based on technologies used (optional)
if(Sw_NewValCapShrink = 1,

* remove newv dimensions for technologies that do not have capacity in this year
* and if it is not a vintage you can build in future years 
* and if the plant has not been upgraded
* note since we're applying this only to new techs the upgrades portion 
* needs to be present in combination with the ability to be built in future periods
* said differently, we want to make sure the vintage cannot be built in future periods,
* it hasn't been built yet, and it has no associated upgraded units
* here the second year index tracks which year has just solved
    valcap_remove(i,v,r,t,"%cur_year%")$[newv(v)$valcap(i,v,r,t)$ivt(i,v,"%cur_year%")
* if there is no capacity..
                       $(not CAP.l(i,v,r,"%cur_year%"))
* if you have not invested in it..
                       $(not sum(tt$[(yeart(tt)<=%cur_year%)], INV.l(i,v,r,tt) ))
* if you cannot invest in the ivt combo in future years..
                       $(not sum{tt$[tt.val>%cur_year%],ivt(i,v,tt)})
                       $(not sum(tt$[valinv(i,v,r,tt)$(yeart(tt)>%cur_year%)],1))
* if it has not been upgraded..
* note the newv condition above allows for the capacity equations
* of motion to still function - this would/does not work for initv vintanges without additional work
                       $(not sum{(tt,ii)$[tsolved(tt)$upgrade_from(ii,i)$valcap(ii,v,r,tt)], 
                                UPGRADES.l(ii,v,r,tt)})
                       ] = yes ;
    valcap(i,v,r,t)$valcap_remove(i,v,r,t,"%cur_year%") = no ;
    valgen(i,v,r,t)$valcap_remove(i,v,r,t,"%cur_year%") = no ;
    valinv(i,v,r,t)$valcap_remove(i,v,r,t,"%cur_year%") = no ;
    inv_cond(i,v,r,t,"%cur_year%")$valcap_remove(i,v,r,t,"%cur_year%") = no ;
    valcap_irt(i,r,t) = sum{v, valcap(i,v,r,t) } ;
    valcap_iv(i,v)$sum{(r,t)$tmodel_new(t), valcap(i,v,r,t) } = yes ;
    valcap_i(i)$sum{v, valcap_iv(i,v) } = yes ;
    valcap_ivr(i,v,r)$sum{t, valcap(i,v,r,t) } = yes ;
    valgen_irt(i,r,t) = sum{v, valgen(i,v,r,t) } ;
    valinv_irt(i,r,t) = sum{v, valinv(i,v,r,t) } ;
    valinv_tg(st,tg,t)$sum{(i,r)$[tg_i(tg,i)$r_st(r,st)], valinv_irt(i,r,t) } = yes ;

) ;

*** Adjust CCS incentives for upgrades
if(Sw_Upgrades = 1,
* note sum over tt required here as we want to only remove the incentive
* from years beyond the current year if upgrades occurred in this solve year

* extend the current-year incentive beyond current date to expiration date - only needed
* when needing to specify beyond current amounts
    co2_captured_incentive(i,v,r,t)$[sum{tt$tmodel(tt),upgrades.l(i,v,r,tt) }
                                    $(not sum{tt$tfix(tt),upgrades.l(i,v,r,tt)})
                                    $(year(t) < %cur_year% + co2_capture_incentive_length)
                                    $(yeart(t) >= %cur_year%)
                                    $valcap(i,v,r,t) ] = co2_captured_incentive(i,v,r,"%cur_year%") ;

* remove co2 captured incentive after the length of time if upgrades occurred in this year
    co2_captured_incentive(i,v,r,t)$[sum{tt$tmodel(tt),upgrades.l(i,v,r,tt) }
                                    $(year(t) >= %cur_year% + co2_capture_incentive_length)
                                    $valcap(i,v,r,t) ] = 0 ;

* adjust fom of upgraded-from plant to updated cost for maintaining the CCS equipment
    cost_fom(i,v,r,t)$[sum{(ii,tt)$[tmodel(tt)$upgrade_from(ii,i)],upgrades.l(ii,v,r,tt) }
                                    $(year(t) >= %cur_year%)
                                    $valcap(i,v,r,t) ] =
        max(cost_fom(i,v,r,t),
            sum{ii$upgrade_from(ii,i),cost_fom(ii,v,r,t) }
           ) ;
) ;


*** Regional emissions for tax credit phaseout
* emit_r_tc is calculated the same as the EMIT variable in the model. We do not use
* EMIT.l here because the emissions are only modeled for those in the emit_modeled set.
emit_r_tc(r,t)$tmodel_new(t) = 

* Emissions from generation
    sum{(i,v,h)$[valgen(i,v,r,t)$h_rep(h)],
        hours(h) * emit_rate("CO2",i,v,r,t)
        * (GEN.l(i,v,r,h,t)
           + CCSFLEX_POW.l(i,v,r,h,t)$[ccsflex(i)$(Sw_CCSFLEX_BYP OR Sw_CCSFLEX_STO OR Sw_CCSFLEX_DAC)])
       }

* Plus emissions produced via production activities (SMR, SMR-CCS, DAC)
* The "production" of negative CO2 emissions via DAC is also included here
    + sum{(p,i,v,h)$[valcap(i,v,r,t)$i_p(i,p)$h_rep(h)],
          hours(h) * prod_emit_rate("CO2",i,t)
          * PRODUCE.l(p,i,v,r,h,t)
         }

*[minus] co2 reduce from flexible CCS capture
*capture = capture per energy used by the ccs system * CCS energy

* Flexible CCS - bypass
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_byp(i)$h_rep(h)],
        ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POW.l(i,v,r,h,t) })$Sw_CCSFLEX_BYP

* Flexible CCS - storage
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_sto(i)$h_rep(h)],
        ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POWREQ.l(i,v,r,h,t) })$Sw_CCSFLEX_STO
;

emit_nat_tc(t)$tmodel_new(t) = sum{r, emit_r_tc(r,t) } ;


*** Recalculate regional CO2 emissions rate for use in state CO2 cap import accounting
* [metric kiloton] * [1000 metric ton / metric kiloton] / ([MW] * [hours]) = [metric ton/MWh]
$ifthen.stateco2 %GSw_StateCO2ImportLevel% == 'r'
    co2_emit_rate_r(r,t)$tmodel(t) = (
        emit_r_tc(r,t)
        / sum{(i,v,h)$[valgen(i,v,r,t)], hours(h) * GEN.l(i,v,r,h,t) }
* Avoid division-by-zero errors
    )$sum{(i,v,h)$[valgen(i,v,r,t)], hours(h) * GEN.l(i,v,r,h,t) } ;
$else.stateco2
* sum emissions and generation within the region
    co2_emit_rate_regional(%GSw_StateCO2ImportLevel%,t)$tmodel(t) = (
        sum{rr$r_%GSw_StateCO2ImportLevel%(rr,%GSw_StateCO2ImportLevel%),
            emit_r_tc(rr,t) }
        / sum{(i,v,rr,h)$[valgen(i,v,rr,t)
                        $r_%GSw_StateCO2ImportLevel%(rr,%GSw_StateCO2ImportLevel%)],
              hours(h) * GEN.l(i,v,rr,h,t) }
* Avoid division-by-zero errors
    )$sum{(i,v,rr,h)$[valgen(i,v,rr,t)
                    $r_%GSw_StateCO2ImportLevel%(rr,%GSw_StateCO2ImportLevel%)],
          hours(h) * GEN.l(i,v,rr,h,t) }
    ;
* broadcast the regional emissions rate to each r in the region
    co2_emit_rate_r(r,t)$tmodel(t) =
        sum{%GSw_StateCO2ImportLevel%
            $r_%GSw_StateCO2ImportLevel%(r,%GSw_StateCO2ImportLevel%),
            co2_emit_rate_regional(%GSw_StateCO2ImportLevel%,t) }
    ;
$endif.stateco2
