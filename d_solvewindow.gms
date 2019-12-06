
* global needed for this file:
* case : name of case you're running
* niter : current iteration

$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix


$log 'Running window solve for...'
$log ' case == %case%'
$log ' iteration == %niter%'
$log ' window == %window%'

*remove any load years
tload(t) = no ;

$if not set niter $setglobal niter 0
$eval previter %niter%-1

tmodel(t) = no ;
*enable years that fall within the window range
tmodel(t)$[tmodel_new(t)$(yeart(t)>=solvewindows("%window%","start"))
                     $(yeart(t)<=solvewindows("%window%","stop"))] = yes ;

*reset tlast to the final modeled period for this window
*then re-compute the financial multiplier for pv
tlast(t) = no ;
tlast(t)$[ord(t)=smax(tt$tmodel(tt),ord(tt))] = yes ;

*reset the age residual fraction
pv_age_residual_fraction(i,t) = 0 ;

pv_age_residual_fraction(i,t)$[tmodel(t)$pv(i)] = max(0, maxage(i) - (sum(tt$tlast(tt),yeart(tt)) - yeart(t))) / maxage(i) ;

*need to increase the financial multiplier for PV to account for the future capacity degradation
*should avoid hardcoding in the future -- for the intertemporal case, using a portion
*of the degradation multiplier based on fraction of life beyond the solve period

cost_cap_fin_mult(i,r,t)$[tmodel(t)$pv(i)] =
      round((1 + 0.052 * pv_age_residual_fraction(i,t)) * cost_cap_fin_mult(i,r,t), 4) ;

cost_cap_fin_mult_noITC(i,r,t)$[tmodel(t)$pv(i)] =
      round((1 + 0.052 * pv_age_residual_fraction(i,t)) * cost_cap_fin_mult_noITC(i,r,t), 4) ;



*if this isn't the first iteration
$ifthene.notfirstiter %niter%>0

*============================
* --- CC and Curtailment ---
*============================

*indicate we're loading data
tload(t)$tmodel(t) = yes ;

$gdxin outputs%ds%variabilityFiles%ds%mergedcurt_%case%_%niter%_out.gdx
$loadr curt_mingen_load = MRsurplusmarginal
$loadr surpmarg_ = surplusmarginal
$loadr surpold_=surpold
*end loading of data from curt script
$gdxin

$gdxin outputs%ds%variabilityFiles%ds%mergedcc_%case%_%niter%_out.gdx
$loadr cc_old_load = season_all_cc
$loadr m_cc_mar = marginalcc
$gdxin

*===========================
* --- Begin Curtailment ---
*===========================

*Clear params before calculation
oldVREgen(r,h,t)$tload(t) = 0 ;
oldMINGEN(r,h,t)$tload(t) = 0 ;
curt_int(i,r,h,t)$tload(t) = 0 ;
curt_totmarg(r,h,t)$tload(t) = 0 ;
curt_excess(r,h,t)$tload(t) = 0 ;
curt_scale(r,h,t)$tload(t) = 0 ;
curt_mingen_int(r,h,t)$tload(t) = 0 ;


oldVREgen(r,h,t)$(tload(t)$rfeas(r)) =
    sum{(i,v,rr)$[cap_agg(r,rr)$vre(i)$valcap(i,v,rr,t)],
          m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,t)
       } ;
oldMINGEN(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)] = sum{h_szn(h,szn), MINGEN.l(r,szn,t) } ;

*Sw_Int_Curt=0 means use average curtailment, and don't differentiate techs
if(Sw_Int_Curt=0,
    curt_int(i,rr,h,t)$[tload(t)$valcap_irt(i,rr,t)$vre(i)$sum{r$cap_agg(r,rr), oldVREgen(r,h,t) + oldMINGEN(r,h,t) }] =
        sum{r$cap_agg(r,rr), surpold_(r,h,t) / (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) } ;
    curt_mingen_int(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)$(oldVREgen(r,h,t) + oldMINGEN(r,h,t))] =
        surpold_(r,h,t) / (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) ;
) ;

*For the remaining options we initially use marginal values for curt_int
if(Sw_Int_Curt=1 or Sw_Int_Curt=2 or Sw_Int_Curt=3,
    curt_int(i,rb,h,t)$[tload(t)$vre(i)$valcap_irt(i,rb,t)] = surpmarg_(i,rb,"sk",h,t) ;
    curt_int(i,rs,h,t)$[tload(t)$vre(i)$(valcap_irt(i,rs,t)$(not sameas(rs,"sk")))] =
        sum{r$r_rs(r,rs), surpmarg_(i,r,rs,h,t) } ;
    curt_mingen_int(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)] = curt_mingen_load(r,h,t) ;
    curt_totmarg(r,h,t)$tload(t) =
        sum{(i,v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$vre(i)],
              m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,t) * curt_int(i,rr,h,t)
           }
        + curt_mingen_int(r,h,t) * oldMINGEN(r,h,t)
    ;
) ;

*Sw_Int_Curt=1 means use average curtailment, but differentiate techs.
*We start with marginal values for curtailment, but then scale these such that
*total curtailment is equal to surpold. Marginals are just used to differentiate based on technology.
if(Sw_Int_Curt=1,
    curt_scale(r,h,t)$tload(t) = 1 ;
    curt_scale(r,h,t)$curt_totmarg(r,h,t) = surpold_(r,h,t) / curt_totmarg(r,h,t) ;
    curt_int(i,rr,h,t)$curt_int(i,rr,h,t) = curt_int(i,rr,h,t) * sum{r$cap_agg(r,rr),curt_scale(r,h,t) } ;
    curt_mingen_int(r,h,t)$curt_mingen_int(r,h,t) = curt_mingen_int(r,h,t) * curt_scale(r,h,t) ;
) ;

*Sw_Int_Curt=2 means use marginal curtailment, but group techs together so that they are not differentiated.
if(Sw_Int_Curt=2,
    curt_int(i,rr,h,t)$[tload(t)$valcap_irt(i,rr,t)$vre(i)$sum{r$cap_agg(r,rr), (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) }] =
        sum{r$cap_agg(r,rr), curt_totmarg(r,h,t) / (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) } ;
    curt_mingen_int(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)$(oldVREgen(r,h,t) + oldMINGEN(r,h,t))] =
        curt_totmarg(r,h,t) / (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) ;
    curt_excess(r,h,t)$curt_totmarg(r,h,t) = surpold_(r,h,t) - curt_totmarg(r,h,t) ;
) ;

*Sw_Int_Curt=3 means use marginal curtailment, but leave techs differentiated
if(Sw_Int_Curt=3,
    curt_excess(r,h,t)$curt_totmarg(r,h,t) = surpold_(r,h,t) - curt_totmarg(r,h,t) ;
) ;

curt_int(i,r,h,t)$[curt_int(i,r,h,t) > 1] = 1 ;

*curt_marg, curt_old, curt_mingen, and surpold are only used in the sequential solve, so ensure they are set to zero
curt_marg(i,r,h,t) = 0 ;
curt_old(r,h,t) = 0 ;
curt_mingen(r,h,t) = 0 ;
surpold(r,h,t) = 0 ;

*===============================
* --- Begin Capacity Credit ---
*===============================

*Clear params before calculation
cc_int(i,v,r,szn,t) = 0 ;
cc_totmarg(i,r,szn,t) = 0 ;
cc_excess(i,r,szn,t) = 0 ;
cc_scale(i,r,szn,t) = 0 ;

*Sw_Int_CC=0 means use average capacity credit for each tech, and don't differentiate vintages
*If there is no existing capacity to calculate average, use marginal capacity credit instead.
if(Sw_Int_CC=0,
    cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)$sum{(vv)$(valcap(i,vv,r,t)), CAP.l(i,vv,r,t) }] =
        cc_old_load(i,r,szn,t) / sum{(vv)$(valcap(i,vv,r,t)), CAP.l(i,vv,r,t) } ;
    cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)$(cc_old_load(i,r,szn,t)=0)] = m_cc_mar(i,r,szn,t) ;
) ;

*For the remaining options we initially use marginal values for cc_int, differentiated by vintage based on seasonal capacity factors.
if(Sw_Int_CC=1 or Sw_Int_CC=2,
    cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)$sum(vv$ict(i,vv,t),m_cf_szn(i,vv,r,szn,t))] =
        m_cc_mar(i,r,szn,t) * m_cf_szn(i,v,r,szn,t) / sum{vv$ict(i,vv,t), m_cf_szn(i,vv,r,szn,t) } ;
    cc_totmarg(i,r,szn,t)$[tload(t)$(vre(i) or storage(i))] = sum{v$valcap(i,v,r,t), cc_int(i,v,r,szn,t) * CAP.l(i,v,r,t) } ;
) ;

*Sw_Int_CC=1 means use average capacity credit for each tech, but differentiate based on vintage.
*Start with marginal capacity credit with seasonal vintage-based capacity factor adjustment,
*and scale with cc_old_load to result in the correct total capacity credit.
if(Sw_Int_CC=1,
    cc_scale(i,r,szn,t)$[tload(t)$(vre(i) or storage(i))] = 1 ;
    cc_scale(i,r,szn,t)$[tload(t)$(vre(i) or storage(i))$cc_totmarg(i,r,szn,t)] = cc_old_load(i,r,szn,t) / cc_totmarg(i,r,szn,t) ;
    cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)] = cc_int(i,v,r,szn,t) * cc_scale(i,r,szn,t) ;
) ;

*Sw_Int_CC=2 means use marginal capacity credit, adjusted by seasonal capacity factors by vintage
if(Sw_Int_CC=2,
    cc_excess(i,r,szn,t)$[tload(t)$cc_totmarg(i,r,szn,t)] = cc_old_load(i,r,szn,t) - cc_totmarg(i,r,szn,t) ;
) ;


*no longer want m_cc_mar since it should not enter the planning reserve margin constraint
m_cc_mar(i,r,szn,t) = 0 ;

cc_int(i,v,r,szn,t)$[cc_int(i,v,r,szn,t) > 1] = 1 ;
cc_int(i,v,r,szn,t)$[tload(t)$csp_storage(i)$valcap(i,v,r,t)] = 1 ;

*=======================================
* --- Begin Averaging of CC/Curt ---
*=======================================

$ifthene.afterseconditer %niter%>1

*when set to 1 - it will take the average over all previous iterations
if(Sw_AVG_iter=1,
        cc_int(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)] = round((cc_int(i,v,r,szn,t) + cc_iter(i,v,r,szn,t,"%previter%")) / 2 ,4) ;
        curt_int(i,r,h,t)$[tload(t)$vre(i)$valcap_irt(i,r,t)] = round((curt_int(i,r,h,t) + curt_iter(i,r,h,t,"%previter%")) / 2, 4) ;
        curt_mingen_int(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)] = round((curt_mingen_int(r,h,t) + curt_mingen_iter(r,h,t,"%previter%")) / 2,4) ;
    ) ;

$endif.afterseconditer

*Remove very small numbers to make it easier for the solver
cc_int(i,v,r,szn,t)$[cc_int(i,v,r,szn,t) < 0.001] = 0 ;
curt_int(i,r,h,t)$[curt_int(i,r,h,t) < 0.001] = 0 ;

cc_iter(i,v,r,szn,t,"%niter%")$cc_int(i,v,r,szn,t) = cc_int(i,v,r,szn,t) ;
curt_iter(i,r,h,t,"%niter%")$curt_int(i,r,h,t) = curt_int(i,r,h,t) ;
curt_mingen_iter(r,h,t,"%niter%")$curt_mingen_int(r,h,t) = curt_mingen_int(r,h,t) ;

execute_unload 'outputs%ds%variabilityFiles%ds%curtout_%case%_%niter%.gdx' cc_int, curt_int, oldVREgen ;

*following line will load in the level values if the switch is enabled
*note that this is still within the conditional that we are now past the first iteration
*and thus a loadpoint is enabled
if(Sw_Loadpoint = 1,
execute_loadpoint 'gdxfiles%ds%%case%_load.gdx' ;
%case%.optfile = 8 ;
) ;

$endif.notfirstiter

*==============================
* --- Solve Supply Side ---
*==============================

solve %case% using lp minimizing z ;

*add years to tfix(t) if this is the last iteration
$ifthene.lastiter %niter%=%maxiter%

$eval nextwindow %window% + 1
tfix(t)$(tmodel(t)$(yeart(t)<solvewindows("%nextwindow%","start"))) = yes ;
$include d2_varfix.gms

$endif.lastiter

