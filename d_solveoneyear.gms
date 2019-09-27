$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

* global needed for this file:
* case : name of case you're running
* cur_year : current year

*remove any load years
tload(t) = no ;

$log 'Solving sequential case for...'
$log '  Case: %case%'
$log '  Year: %cur_year%'

*load in results from the cc/curtailment scripts
$ifthene.tcheck %cur_year%>2010

*indicate we're loading data
tload("%cur_year%") = yes ;

*file written by d4_Translate_Variability.R
$gdxin outputs%ds%variabilityFiles%ds%curt_out_%case%_%cur_year%.gdx
$loadr surpold_ = surpold
$loadr curt_mingen_load = MRsurplusmarginal
$loadr surpmarg_ = surplusmarginal
*end loading of data from curt script
$gdxin

surpold(r,h,t)$tload(t) = surpold_(r,h,t) ;
curt_mingen(r,h,t)$tload(t) = curt_mingen_load(r,h,t) ;

*file written by ReEDS_capacity_credit.py
$gdxin outputs%ds%variabilityFiles%ds%cc_out_%case%_%cur_year%.gdx
$loadr cc_old_load = season_all_cc
$loadr cc_mar_load = season_all_cc_mar
$gdxin

m_cc_mar(i,r,szn,t)$[tload(t)$(vre(i) or storage(i))] = cc_mar_load(i,r,szn,t) ;
cc_old(i,r,szn,t)$[tload(t)$(vre(i) or storage(i))] = cc_old_load(i,r,szn,t) ;


*compute the average curtailment rate of the surplus from old capacity
*divided by the total amount of old generation (note use of tprev here with the sequential solve)
oldVREgen(r,h,t)$[tload(t)$rfeas(r)] = sum{(i,v,rr,tt)$[cap_agg(r,rr)$tprev(t,tt)
                                                       $(wind(i) or pv(i) or csp_nostorage(i))$valcap(i,v,rr,tt)],
                                           m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,tt) } ;



curt_old(r,h,t)$[tload(t)$rfeas(r)$oldVREgen(r,h,t)] =
                                surpold_(r,h,t) / oldVREgen(r,h,t)
;

curt_marg(i,rb,h,t)$[tload(t)$rfeas(rb)] = surpmarg_(i,rb,"sk",h,t) ;
curt_marg(i,rs,h,t)$[tload(t)$(rfeas_cap(rs)$(not sameas(rs,"sk")))] = sum{r$r_rs(r,rs), surpmarg_(i,r,rs,h,t) } ;

*curt_int is only used in the intertemporal solve, so ensure it is set to zero
curt_int(i,r,h,t) = 0 ;

execute_unload 'outputs%ds%variabilityFiles%ds%cc_curt_%case%_%cur_year%.gdx' oldVREgen, curt_old, cc_mar, cc_old ;


curt_old(r,h,t)$[curt_old(r,h,t) > 1] = 1 ;
curt_marg(i,r,h,t)$[curt_marg(i,r,h,t) > 1] = 1 ;

*Remove very small numbers to make it easier for the solver
curt_old(r,h,t)$[curt_old(r,h,t) < 0.001] = 0 ;
curt_marg(i,r,h,t)$[curt_marg(i,r,h,t) < 0.001] = 0 ;
curt_mingen(r,h,t)$[curt_mingen(r,h,t) < 0.001] = 0 ;

$endif.tcheck
*$ontext

tmodel(t) = no ;
tmodel("%cur_year%") = yes ;
solve %case% minimizing z using lp ;
tfix("%cur_year%") = yes ;
$include d2_varfix.gms
*$offtext


