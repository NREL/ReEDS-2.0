* global needed for this file:
* case : name of case you're running
* niter : current iteration

$setglobal ds %ds%

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix


$log 'Running intertemporal solve for...'
$log ' case == %case%'
$log ' iteration == %niter%'

*remove any load years
tload(t) = no ;

$if not set niter $setglobal niter 0
$eval previter %niter%-1

*if this isn't the first iteration
$ifthene.firstiter %niter%>0

$if not set load_ref_dem $setglobal load_ref_dem 0

$ifthene.loadref %load_ref_dem% == 0
* need to load psupply0 and load_exog0...
* should also set load_exog to load_exog0


$endif.loadref

*============================
* --- CC and Curtailment ---
*============================

*indicate we're loading data
tload(t)$tmodel(t) = yes ;

*set of files for first column of merged gdx files
* consider making tfirst and tlast globals to avoid hardcoding the years
$ifthene.seconditer %niter%==1
set gdxfiles /ReEDS_augur_%case%_2023*ReEDS_augur_%case%_2025/;
$endif.seconditer

* create dummy parameters to read in gdx data. 
parameter curt_old_load_file(gdxfiles, r,h,t)
curt_mingen_load_file(gdxfiles, r,h,t)
curt_marg_load_file(gdxfiles, i,r,h,t)
cc_old_load_file(gdxfiles,i,r,szn,t)
cc_mar_load_file(gdxfiles,i,r,szn,t)
sdbin_size_load_file(gdxfiles, region,szn,sdbin,t)
curt_stor_load_file(gdxfiles, i,v,r,h,src,t)
curt_tran_load_file(gdxfiles,r,rr,h,t) 
curt_reduct_tran_max_load_file(gdxfiles,r,rr,h,t)
storage_in_min_load_file(gdxfiles,r,h,t) 
hourly_arbitrage_value_load_file(gdxfiles,i,r,t)
hav_int_load(gdxfiles,i,r,dummy);

$gdxin %casepath%%ds%augur_data%ds%ReEDS_augur_merged_%case%_%niter%.gdx
$loadr curt_old_load_file = curt_old
$loadr curt_mingen_load_file = curt_mingen
$loadr curt_marg_load_file = curt_marg
$loadr cc_old_load_file = cc_old
$loadr cc_mar_load_file = cc_mar
$loadr sdbin_size_load_file = sdbin_size
$loadr curt_stor_load_file = curt_stor
$loadr curt_tran_load_file = curt_tran
$loadr curt_reduct_tran_max_load_file = curt_reduct_tran_max
$loadr storage_in_min_load_file = storage_in_min
$loadr hourly_arbitrage_value_load_file = hourly_arbitrage_value
$loadr hav_int_load = hourly_arbitrage_value
$gdxin


*remove the file column from the parameters
curt_old_load(r,h,t) = sum{gdxfiles, curt_old_load_file(gdxfiles, r,h,t) };
curt_mingen_load(r,h,t) = sum{gdxfiles, curt_mingen_load_file(gdxfiles, r,h,t) };
curt_marg_load(i,r,h,t) = sum{gdxfiles, curt_marg_load_file(gdxfiles, i,r,h,t) };
cc_old_load(i,r,szn,t) = sum{gdxfiles, cc_old_load_file(gdxfiles,i,r,szn,t)};
cc_mar_load(i,r,szn,t) = sum{gdxfiles, cc_mar_load_file(gdxfiles,i,r,szn,t)};
sdbin_size_load(region,szn,sdbin,t) = sum{gdxfiles, sdbin_size_load_file(gdxfiles, region,szn,sdbin,t) };
curt_stor_load(i,v,r,h,src,t) = sum{gdxfiles, curt_stor_load_file(gdxfiles, i,v,r,h,src,t) } ;
curt_tran_load(r,rr,h,t) = sum{gdxfiles, curt_tran_load_file(gdxfiles,r,rr,h,t) };
curt_reduct_tran_max_load(r,rr,h,t) = sum{gdxfiles, curt_reduct_tran_max_load_file(gdxfiles,r,rr,h,t) };
storage_in_min_load(r,h,t) = sum{gdxfiles, storage_in_min_load_file(gdxfiles,r,h,t) };
hourly_arbitrage_value_load(i,r,t) = sum{gdxfiles, hourly_arbitrage_value_load_file(gdxfiles,i,r,t) };



*===========================
* --- Begin Curtailment ---
*===========================

*Clear params before calculation
oldVREgen(r,h,t) = 0 ;
oldMINGEN(r,h,t) = 0 ;
curt_int(i,r,h,t) = 0 ;
curt_totmarg(r,h,t) = 0 ;
curt_excess(r,h,t) = 0 ;
curt_scale(r,h,t) = 0 ;
curt_mingen_int(r,h,t) = 0 ;

oldVREgen(r,h,t)$[tload(t)$rfeas(r)] = sum{(i,v,rr)$[cap_agg(r,rr)$vre(i)$valcap(i,v,rr,t)], m_cf(i,rr,h) * CAP.l(i,v,rr,t) } ;

oldMINGEN(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)] = sum{h_szn(h,szn), MINGEN.l(r,szn,t) } ;

*Sw_Int_Curt=0 means use average curtailment, and don't differentiate techs
if(Sw_Int_Curt=0,
    curt_int(i,rr,h,t)$[tload(t)$valcap_irt(i,rr,t)$vre(i)$sum{r$cap_agg(r,rr), oldVREgen(r,h,t) + oldMINGEN(r,h,t) }] =
        sum{r$cap_agg(r,rr), curt_old_load(r,h,t) / (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) } ;
    curt_mingen_int(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)$(oldVREgen(r,h,t) + oldMINGEN(r,h,t))] =
        curt_old_load(r,h,t) / (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) ;
) ;

*For the remaining options we initially use marginal values for curt_int
if(Sw_Int_Curt=1 or Sw_Int_Curt=2 or Sw_Int_Curt=3,
    curt_int(i,rb,h,t)$[tload(t)$vre(i)$valcap_irt(i,rb,t)] = curt_marg_load(i,rb,h,t) ;
    curt_int(i,rs,h,t)$[tload(t)$vre(i)$(valcap_irt(i,rs,t)$(not sameas(rs,"sk")))] =
        sum{r$r_rs(r,rs), curt_marg_load(i,r,h,t) } ;
    curt_mingen_int(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)] = curt_mingen_load(r,h,t) ;
    curt_totmarg(r,h,t)$tload(t) =
        sum{(i,v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$vre(i)],
              m_cf(i,rr,h) * CAP.l(i,v,rr,t) * curt_int(i,rr,h,t)
           }
        + curt_mingen_int(r,h,t) * oldMINGEN(r,h,t)
    ;
) ;

*Sw_Int_Curt=1 means use average curtailment, but differentiate techs.
*We start with marginal values for curtailment, but then scale these such that
*total curtailment is equal to curt_old. Marginals are just used to differentiate based on technology.
if(Sw_Int_Curt=1,
    curt_scale(r,h,t)$tload(t) = 1 ;
    curt_scale(r,h,t)$curt_totmarg(r,h,t) = curt_old_load(r,h,t) / curt_totmarg(r,h,t) ;
    curt_int(i,rr,h,t)$curt_int(i,rr,h,t) = curt_int(i,rr,h,t) * sum{r$cap_agg(r,rr),curt_scale(r,h,t) } ;
    curt_mingen_int(r,h,t)$curt_mingen_int(r,h,t) = curt_mingen_int(r,h,t) * curt_scale(r,h,t) ;
) ;

*Sw_Int_Curt=2 means use marginal curtailment, but group techs together so that they are not differentiated.
if(Sw_Int_Curt=2,
    curt_int(i,rr,h,t)$[tload(t)$valcap_irt(i,rr,t)$vre(i)$sum{r$cap_agg(r,rr), (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) }] =
        sum{r$cap_agg(r,rr), curt_totmarg(r,h,t) / (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) } ;
    curt_mingen_int(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)$(oldVREgen(r,h,t) + oldMINGEN(r,h,t))] =
        curt_totmarg(r,h,t) / (oldVREgen(r,h,t) + oldMINGEN(r,h,t)) ;
    curt_excess(r,h,t)$curt_totmarg(r,h,t) = curt_old_load(r,h,t) - curt_totmarg(r,h,t) ;
) ;

*Sw_Int_Curt=3 means use marginal curtailment, but leave techs differentiated
if(Sw_Int_Curt=3,
    curt_excess(r,h,t)$curt_totmarg(r,h,t) = curt_old_load(r,h,t) - curt_totmarg(r,h,t) ;
) ;


curt_int(i,r,h,t)$[curt_int(i,r,h,t) > 1] = 1 ;

*curt_marg, curt_old, curt_mingen, and curt_old are only used in the sequential solve, so ensure they are set to zero
curt_marg(i,r,h,t) = 0 ;
curt_old(r,h,t) = 0 ;
curt_mingen(r,h,t) = 0 ;

*==============================
* --- Begin Capacity Value ---
*==============================

*Clear params before calculation
cc_int(i,v,r,szn,t) = 0 ;
cc_totmarg(i,r,szn,t) = 0 ;
cc_excess(i,r,szn,t) = 0 ;
cc_scale(i,r,szn,t) = 0 ;
sdbin_size(region,szn,sdbin,t) = 0 ;
curt_stor(i,v,r,h,src,t) = 0 ;
curt_tran(r,rr,h,t) = 0 ;
curt_reduct_tran_max(r,rr,h,t) = 0 ;
storage_in_min(r,h,t) = 0 ;
hav_int(i,r,t) = 0 ;

*Storage duration bin sizes by year
sdbin_size(region,szn,sdbin,t)$tload(t) = sdbin_size_load(region,szn,sdbin,t) ;
curt_stor(i,v,r,h,src,t)$[tload(t)$valcap(i,v,r,t)$storage(i)] = curt_stor_load(i,v,r,h,src,t) ;
curt_tran(r,rr,h,t)$[tload(t)$(sum{trtype, routes(r,rr,trtype,t) } or sum{trtype, routes(rr,r,trtype,t) })] = curt_tran_load(r,rr,h,t) ;
curt_reduct_tran_max(r,rr,h,t)$[tload(t)$(sum{trtype, routes(r,rr,trtype,t) } or sum{trtype, routes(rr,r,trtype,t) })] = curt_reduct_tran_max_load(r,rr,h,t) ;
storage_in_min(r,h,t)$[tload(t)] = storage_in_min_load(r,h,t) ;

parameter hav_temp(i,r,t,dummy);
hav_temp(i,r,t,dummy)$sum(storage(i)$(dummy.val >= t.val  and dummy.val<= t.val + FinanceLifetime(i)),1) = hourly_arbitrage_value_load(i,r,t) ;
hav_temp(i,r,t,dummy)$[sum(gdxfiles,hav_int_load(gdxfiles,i,r,dummy))$tmodel(t)] = sum(gdxfiles,hav_int_load(gdxfiles,i,r,dummy))$hav_temp(i,r,t,dummy);
*
* accumulate and discount arbitrage value over the lifetime of the asset
hav_int(i,r,t) = sum(dummy, hav_temp(i,r,t,dummy) * pvf_hav(i,t,dummy)) ;

* HAV cannot exceed the capital cost
hav_int(i,r,t)$(hav_int(i,r,t) >= cost_cap(i,t)) = cost_cap(i,t) ;

if(Sw_StorHAV=0,
	hav_int(i,r,t) = 0;
);

*Sw_Int_CC=0 means use average capacity credit for each tech, and don't differentiate vintages
*If there is no existing capacity to calculate average, use marginal capacity credit instead.
if(Sw_Int_CC=0,
    cc_int(i,v,r,szn,t)$[tload(t)$vre(i)$valcap(i,v,r,t)$sum{(vv)$(valcap(i,vv,r,t)), CAP.l(i,vv,r,t) }] =
        cc_old_load(i,r,szn,t) / sum{(vv)$(valcap(i,vv,r,t)), CAP.l(i,vv,r,t) } ;
    cc_int(i,v,r,szn,t)$[tload(t)$vre(i)$valcap(i,v,r,t)$(cc_old_load(i,r,szn,t)=0)] = cc_mar_load(i,r,szn,t) ;
) ;

*For the remaining options we initially use marginal values for cc_int, differentiated by vintage based on seasonal capacity factors.
if(Sw_Int_CC=1 or Sw_Int_CC=2,
    cc_int(i,v,r,szn,t)$[tload(t)$vre(i)$valcap(i,v,r,t)$m_cf_szn(i,r,szn) ] =
        m_cc_mar(i,r,szn,t) * m_cf_szn(i,r,szn) / m_cf_szn(i,r,szn)  ;
    cc_totmarg(i,r,szn,t)$[tload(t)$vre(i)] = sum{v$valcap(i,v,r,t), cc_int(i,v,r,szn,t) * CAP.l(i,v,r,t) } ;
) ;

*Sw_Int_CC=1 means use average capacity credit for each tech, but differentiate based on vintage.
*Start with marginal capacity credit with seasonal vintage-based capacity factor adjustment,
*and scale with cc_old_load to result in the correct total capacity credit.
if(Sw_Int_CC=1,
    cc_scale(i,r,szn,t)$[tload(t)$vre(i)] = 1 ;
    cc_scale(i,r,szn,t)$[tload(t)$vre(i)$cc_totmarg(i,r,szn,t)] = cc_old_load(i,r,szn,t) / cc_totmarg(i,r,szn,t) ;
    cc_int(i,v,r,szn,t)$[tload(t)$vre(i)$valcap(i,v,r,t)] = cc_int(i,v,r,szn,t) * cc_scale(i,r,szn,t) ;
) ;

*Sw_Int_CC=2 means use marginal capacity credit, adjusted by seasonal capacity factors by vintage
if(Sw_Int_CC=2,
    cc_excess(i,r,szn,t)$[tload(t)$cc_totmarg(i,r,szn,t)] = cc_old_load(i,r,szn,t) - cc_totmarg(i,r,szn,t) ;
) ;

*no longer want m_cc_mar since it should not enter the planning reserve margin constraint
m_cc_mar(i,r,szn,t) = 0 ;

cc_int(i,v,r,szn,t)$[cc_int(i,v,r,szn,t) > 1] = 1 ;


*=======================================
* --- Begin Averaging of CC/Curt ---
*=======================================

cc_iter(i,v,r,szn,t,"%niter%")$cc_int(i,v,r,szn,t) = cc_int(i,v,r,szn,t) ;
curt_iter(i,r,h,t,"%niter%")$curt_int(i,r,h,t) = curt_int(i,r,h,t) ;
curt_mingen_iter(r,h,t,"%niter%")$curt_mingen_int(r,h,t) = curt_mingen_int(r,h,t) ;

$ifthene.seconditer %niter%>1

*when set to 1 - it will take the average over all previous iterations
if(Sw_CCcurtAvg=1,
        cc_int(i,v,r,szn,t)$[tload(t)$vre(i)$valcap(i,v,r,t)] =
          (cc_int(i,v,r,szn,t) + cc_iter(i,v,r,szn,t,"%previter%")) / 2 ;

        curt_int(i,r,h,t)$[tload(t)$vre(i)$valcap_irt(i,r,t)] =
          (curt_int(i,r,h,t) + curt_iter(i,r,h,t,"%previter%")) / 2 ;

        curt_mingen_int(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)] =
          (curt_mingen_int(r,h,t) + curt_mingen_iter(r,h,t,"%previter%")) / 2 ;
          );

*when set to 2 - just take the average over the past two if it is over some threshold
if(Sw_CCcurtAvg=2,
        cc_int(i,v,r,szn,t)$[tload(t)$vre(i)$valcap(i,v,r,t)] = 
          (cc_iter(i,v,r,szn,t,"%niter%") + cc_iter(i,v,r,szn,t,"%previter%")) / 2 ;

        curt_int(i,r,h,t)$[tload(t)$vre(i)$valcap_irt(i,r,t)] =
          (curt_iter(i,r,h,t,"%niter%") + curt_iter(i,r,h,t,"%previter%")) / 2 ;

        curt_mingen_int(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)] =
          (curt_mingen_iter(r,h,t,"%niter%") + curt_mingen_iter(r,h,t,"%previter%")) / 2 ;
          );

cc_iter(i,v,r,szn,t,"%niter%")$cc_int(i,v,r,szn,t) = cc_int(i,v,r,szn,t) ;
curt_iter(i,r,h,t,"%niter%")$curt_int(i,r,h,t) = curt_int(i,r,h,t) ;
curt_mingen_iter(r,h,t,"%niter%")$curt_mingen_int(r,h,t) = curt_mingen_int(r,h,t) ;

$endif.seconditer

*Remove very small numbers to make it easier for the solver
cc_int(i,v,r,szn,t)$[cc_int(i,v,r,szn,t) < 0.001] = 0 ;
curt_int(i,r,h,t)$[curt_int(i,r,h,t) < 0.001] = 0 ;

execute_unload '%casepath%%ds%augur_data%ds%curtout_%case%_%niter%.gdx' cc_int, curt_int, oldVREgen ;

*following line will load in the level values if the switch is enabled
*note that this is still within the conditional that we are now past the first iteration
*and thus a loadpoint is enabled
if(Sw_Loadpoint = 1,
execute_loadpoint '%casepath%%ds%gdxfiles%ds%%case%_load.gdx';
);


$endif.firstiter

*initial values for capacity credit for first iteration
if(%niter%=0, 
    cc_int(i,v,r,szn,t) = cc_mar(i,r,szn,t);
);

* set storage_in_min to zero, otherwise model does not solve. ISSUE: July 2022 
storage_in_min(r,h,t) = 0;

* rounding of all cc and curt parameters
* used in the intertemporal case

cc_int(i,v,r,szn,t) = round(cc_int(i,v,r,szn,t), 4) ;
cc_totmarg(i,r,szn,t) = round(cc_totmarg(i,r,szn,t), 4) ;
cc_excess(i,r,szn,t) = round(cc_excess(i,r,szn,t), 4) ;
cc_scale(i,r,szn,t) = round(cc_scale(i,r,szn,t), 4) ;
curt_int(i,r,h,t) = round(curt_int(i,r,h,t), 4) ;
curt_totmarg(r,h,t) = round(curt_totmarg(r,h,t), 4) ;
curt_excess(r,h,t) = round(curt_excess(r,h,t), 4) ;
curt_scale(r,h,t) = round(curt_scale(r,h,t), 4) ;
curt_mingen_int(r,h,t) = round(curt_mingen_int(r,h,t), 4) ;
*curt_stor(i,v,r,h,src,t) = 0;
*sdbin_size(region,szn,sdbin,t) = 0;

* turn off storage contribution to capacity credit if switch is 0
if(Sw_StorCC = 0,
  sdbin_size(region,szn,sdbin,t) = 0;
);

if(%niter% = 3,
  if(Sw_ValStr = 1,
    %case%.optfile = %modoptfile% ;
    );
);

* set curtialment to zero when running copperplate
if(Sw_TxLimit = 0,
*  curt_int(i,r,h,t) = 0;
  storage_in_min(r,h,t) = 0;
  );
*==============================
* --- Solve Supply Side ---
*==============================
solve %case% using lp minimizing z;

if(Sw_Loadpoint = 1,
execute_unload '%casepath%%ds%gdxfiles%ds%%case%_load.gdx';
);

*============================
* --- Iteration Tracking ---
*============================

cap_iter(i,v,r,t,"%niter%")$valcap(i,v,r,t) = CAP.l(i,v,r,t) ;
gen_iter(i,v,r,t,"%niter%")$valcap(i,v,r,t) = sum{h, GEN.l(i,v,r,h,t) * hours(h) } ;
gen_iter(i,v,r,t,"%niter%")$[vre(i)$valcap(i,v,r,t)] = sum{h, m_cf(i,r,h) * CAP.l(i,v,r,t) * hours(h) } ;
cap_firm_iter(i,v,r,szn,t,"%niter%")$cc_int(i,v,r,szn,t) = cc_int(i,v,r,szn,t) * CAP.l(i,v,r,t) ;
cap_firm_iter(i,v,r,szn,t,"%niter%")$storage(i) = sum{sdbin, CAP_SDBIN.l(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin) } ;
curt_tot_iter(i,v,r,t,"%niter%")$[tload(t)$vre(i)$valcap(i,v,r,t)] = sum{h, m_cf(i,r,h) * CAP.l(i,v,r,t) * curt_int(i,r,h,t) * hours(h) } ;
$ifthene.postseconditer %niter%>1
cc_change(i,v,r,szn,t)$[tload(t)$(vre(i) or storage(i))$valcap(i,v,r,t)] = cc_iter(i,v,r,szn,t,"%niter%") - cc_iter(i,v,r,szn,t,"%previter%") ;
curt_change(i,r,h,t)$[tload(t)$vre(i)$valcap_irt(i,r,t)] = curt_iter(i,r,h,t,"%niter%") - curt_iter(i,r,h,t,"%previter%") ;
curt_mingen_change(r,h,t)$[Sw_Mingen$tload(t)$rfeas(r)] = curt_mingen_iter(r,h,t,"%niter%") - curt_mingen_iter(r,h,t,"%previter%") ;
$endif.postseconditer
