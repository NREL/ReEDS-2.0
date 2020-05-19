
* global needed for this file:
* case : name of case you're running
* niter : current iteration

$setglobal ds %ds%
$if not set GSw_gopt $setglobal GSw_gopt 4

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$log 'Running intertemporal solve for...'
$log ' case == %case%'
$log ' iteration == %niter%'

*If this is not UNIX, use the specfied optfile. If value streams switch is on and
*this is the last iteration,
*use a modified version of this optfile that produces an mps file. The modified
*optfile number is in the 900's.
$eval valstrcheck %niter%+Sw_ValStr

$ifthen.os not %system.filesys% == UNIX
$ifthen.valstr %TotIter% == %valstrcheck%
%case%.optfile = 900;
OPTION savepoint = 1;
$else.valstr
%case%.optfile = %GSw_gopt%;
$endif.valstr
$endif.os

*remove any load years
tload(t) = no;

$if not set niter $setglobal niter 0
$eval previter %niter%-1

*if this isn't the first iteration
$ifthene.firstiter %niter%>0

$if not set load_ref_dem $setglobal load_ref_dem 0

$ifthene.loadref %load_ref_dem% == 0
* need to load psupply0 and lmnt0...
* should also set lmnt to lmnt0


$endif.loadref


*============================
* --- CC and Curtailment ---
*============================

*indicate we're loading data
tload(t)$tmodel(t) = yes;

$gdxin E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%mergedcurt_%case%_%niter%_out.gdx
$loadr curt_mingen_load = MRsurplusmarginal
$loadr surpold_=surpold
*end loading of data from curt script
$gdxin

$gdxin E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%mergedcc_%case%_%niter%_out.gdx
$loadr cc_old_load = season_all_cc
$loadr m_cc_mar = marginalcc
$gdxin


*===========================
* --- Begin Curtailment ---
*===========================

*compute the average curtailment rate of the surplus from old capacity
*divided by the total amount of old generation (note no use of tprev here)
*%% called oldgen(r,h,t) in c_solve_india.gms
oldVREgen(r,h,t)$(tload(t)$rfeas(r)) = sum((i,c,rr)$[cap_agg(r,rr)
                          $vre(i)$valcap(i,c,rr,t)],
                   m_cf(i,rr,h) * CAP.l(i,c,rr,t));

*%% called curt(r,h,t) in c_solve_india.gms
curt_avg(r,h,t)$(tload(t)$rfeas(r)$oldVREgen(r,h,t)) =
                        surpold_(r,h,t) / oldVREgen(r,h,t);


curt_mingen(r,h,t)$tload(t) = curt_mingen_load(r,h,t);

*curt_marg, curt_old, and surpold are only used in the sequential solve, so ensure they are set to zero
*%% following three are no in c_solve_india.gms
curt_marg(i,r,h,t) = 0;
curt_old(r,h,t) = 0;
surpold(r,h,t) = 0;

curt_avg(r,h,t)$(curt_avg(r,h,t)>1) = 1;


*==============================
* --- Begin Capacity Value ---
*==============================

cc_avg(i,r,szn,t)$(tload(t)$sum{(c)$valcap(i,c,r,t),CAP.l(i,c,r,t)})
                                   = cc_old_load(i,r,szn,t) /
                                   sum{(c)$(valcap(i,c,r,t)),CAP.l(i,c,r,t)};

*average cc if no cc_old is just cc_mar
cc_avg(i,r,szn,t)$[cc_old_load(i,r,szn,t)=0] = m_cc_mar(i,r,szn,t);
*no longer want m_cc_mar since it should not enter the planning reserve margin constraint
m_cc_mar(i,r,szn,t) = 0;

*%% not in c_solve_india.gms
*cc_avg(i,r,szn,t)$(csp_storage(i)) = 1;

cc_iter(i,r,szn,t,"%niter%")$cc_avg(i,r,szn,t) = cc_avg(i,r,szn,t);
curt_iter(r,h,t,"%niter%")$curt_avg(r,h,t) = curt_avg(r,h,t);


*=======================================
* --- Begin Averaging of CC/Curt ---
*=======================================

$ifthene.seconditer %niter%>1

*when set to 1 - it will take the average over all previous iterations
if(Sw_CCcurtAvg=1,
        cc_avg(i,r,szn,t)$(tload(t)$sum(cciter$((cciter.val<=%niter%)$cc_iter(i,r,szn,t,cciter)),1))  = sum(cciter$((cciter.val<=%niter%)$cc_iter(i,r,szn,t,cciter)),cc_iter(i,r,szn,t,cciter)) / sum(cciter$((cciter.val<=%niter%)$cc_iter(i,r,szn,t,cciter)),1) ;
        curt_avg(r,h,t)$(tload(t)$sum(cciter$((cciter.val<=%niter%)$curt_iter(r,h,t,cciter)),1)) = sum(cciter$((cciter.val<=%niter%)$curt_iter(r,h,t,cciter)),curt_iter(r,h,t,cciter)) / sum(cciter$((cciter.val<=%niter%)$curt_iter(r,h,t,cciter)),1);
        );

*when set to 2 - just take the average over the past two if it is over some threshold
if(Sw_CCcurtAvg=2,
        cc_avg(i,r,szn,t)$tload(t) = (cc_iter(i,r,szn,t,"%niter%") + cc_iter(i,r,szn,t,"%previter%")) / 2 ;
        curt_avg(r,h,t)$tload(t) = (curt_iter(r,h,t,"%niter%") + curt_iter(r,h,t,"%previter%")) / 2;
        );
$endif.seconditer

*Remove very small numbers to make it easier for the solver
cc_avg(i,r,szn,t)$(cc_avg(i,r,szn,t) < 0.001) = 0;
curt_avg(r,h,t)$(curt_avg(r,h,t) < 0.001) = 0;

execute_unload 'E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%curtout_%case%_%niter%.gdx' cc_avg, curt_avg, oldVREgen;

*following line will load in the level values if the switch is enabled
*note that this is still within the conditional that we are now past the first iteration
*and thus a loadpoint is enabled
if(Sw_Loadpoint = 1,
execute_loadpoint 'E_Outputs%ds%gdxfiles%ds%%case%_load.gdx';
);

$endif.firstiter


*==============================
* --- Solve Supply Side ---
*==============================
solve %case% using lp minimizing z;

if(Sw_Loadpoint = 1,
execute_unload 'E_Outputs%ds%gdxfiles%ds%%case%_load.gdx';
);
