

$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

Model %case% /all/ ;


*=================================
* -- MODEL AND SOLVER OPTIONS --
*=================================

OPTION lp = cplex
OPTION RESLIM = 50000 ;
OPTION NLP = pathNLP ;
%case%.holdfixed = 1 ;

*quick check for the HPC
*if so, have to use gurobi
*currently no option file for unix systems. optfile remains at default
$ifthen.os %system.filesys% == UNIX
OPTION  lp = gurobi
$endif.os

*If this is not UNIX, use the specfied optfile.
$ifthen.os not %system.filesys% == UNIX
%case%.optfile = %GSw_gopt% ;
$ifthen.valstr %GSw_ValStr% == 1
OPTION savepoint = 1 ;
$endif.valstr
$endif.os

$if not set loadgdx $setglobal loadgdx 0

$ifthen.gdxin %loadgdx% == 1
execute_loadpoint "gdxfiles%ds%%gdxfin%.gdx" ;
Option BRatio = 0.0 ;
$endif.gdxin


*====================================
* --- Endogenous Retirements ---
*====================================

retiretech(i,v,r,t) = no ;

set valret(i,v) "technologies and classes that can be retired",
    noretire(i) "technologies that will never be retired" /distpv, can-imports/ ;

* storage technologies are not appropriately attributing capacity value to CAP variable
* therefore not allowing them to endogenously retire
noretire(i)$[storage_no_csp(i)] = yes ;

*all existings plants of any technology can be retired if Sw_Retire = 1
valret(i,v)$[(Sw_Retire=1)$initv(v)$(not noretire(i))] = yes ;

*only coal and gas are retirable if Sw_Retire = 2
valret(i,v)$[(Sw_Retire=2)$initv(v)$(not noretire(i))
            $(coal(i) or gas(i) or sameas(i,"o-g-s"))] = yes ;

*only nuclear, coal, and gas are retirable if Sw_Retire = 3
valret(i,v)$[(Sw_Retire=3)$initv(v)$(not noretire(i))
            $(coal(i) or gas(i) or sameas(i,"nuclear") or sameas(i,"o-g-s"))] = yes ;

*new and existings plants of any technology can be retired if Sw_Retire = 4
valret(i,v)$[(Sw_Retire=4)$(not noretire(i))] = yes ;


retiretech(i,v,r,t)$[valret(i,v)$valcap(i,v,r,t)] = yes ;
*both NY and IL have policies to support existing nuclear
*plants until 2030 and 2028, respectively
retiretech("nuclear",initv,r,t)$[r_st(r,"NY")$(yeart(t)<2030)$valcap("nuclear",initv,r,t)] = no ;
retiretech("nuclear",initv,r,t)$[r_st(r,"IL")$(yeart(t)<2028)$valcap("nuclear",initv,r,t)] = no ;


*============================
* Setting for CAP SCENARIO
*============================

emit_cap(e,t) = 0 ;
* set emissions cap here...
* note that it needs to be in MTCO2
if(Sw_AnnualCap = 1,
         emit_cap("CO2",t) = co2_cap(t) ;
) ;


*=============================
* Curtailment and CC Settings
*=============================

set tload(t) "years in which data is loaded" ;
tload(t) = no ;

set cciter "placeholder for iteration number for tracking CC and curtailment" /0*20/ ;

parameter SurpOld_(r,h,t) "--MW-- surpold but loaded in from the gdx file for whichever year"
          surpmarg_(i,r,rs,h,t) "--fraction-- marginal curtailment rate for new generators, loaded from gdx file"
          oldVREgen(r,h,t) "--MW-- generation from endogenous VRE capacity that existed the year before, or iteration before"
          oldMINGEN(r,h,t) "--MW-- Minimum generation from the previous iteration"
          curt_totmarg(r,h,t) "--MW-- original estimate of total curtailment for intertemporal, based on marginals"
          curt_scale(r,h,t) "--unitless-- scaling of marginal curtailment levels in intertemporal runs to equal total curtailment levels"
          cc_totmarg(i,r,szn,t) "--MW-- original estimate of total capacity value for intertemporal, based on marginals"
          cc_scale(i,r,szn,t) "--unitless-- scaling of marginal capacity value levels in intertemporal runs to equal total capacity value"
          cc_iter(i,v,r,szn,t,cciter) "--fraction-- Actual capacity value in iteration cciter"
          curt_iter(i,r,h,t,cciter) "--fraction-- Actual curtailment in iteration cciter"
          curt_mingen_iter(r,h,t,cciter) "--fraction-- Actual curtailment from mingen in iteration cciter"
          cc_change(i,v,r,szn,t) "--fraction-- Change of capacity credit between this and previous iteration"
          curt_change(i,r,h,t) "--fraction-- Change of curtailment between this and previous iteration"
          curt_mingen_change(r,h,t) "--fraction-- Change of mingen curtailment between this and previous iteration"
;

*start the values at zero to avoid errors that
*these values have not been assigned
cc_int(i,v,r,szn,t) = 0 ;
cc_totmarg(i,r,szn,t) = 0 ;
cc_excess(i,r,szn,t) = 0 ;
cc_scale(i,r,szn,t) = 0 ;
curt_int(i,r,h,t) = 0 ;
curt_totmarg(r,h,t) = 0 ;
curt_excess(r,h,t) = 0 ;
curt_scale(r,h,t) = 0 ;
curt_mingen_int(r,h,t) = 0 ;


*Initialize surpold to zero
SurpOld(r,h,t) = 0 ;

*trimming the largest matrices to reduce file sizes
cost_vom(i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;
cost_fom(i,v,r,t)$[not valcap(i,v,r,t)] = 0 ;
heat_rate(i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;
m_cf(i,v,r,h,t)$[not valcap(i,v,r,t)] = 0 ;
emit_rate(e,i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;

acp_price(st,t) = round(acp_price(st,t),3) ;
avail(i,v,h) = round(avail(i,v,h),4) ;
batterymandate(r,i,t) = round(batterymandate(r,i,t),2) ;
biopricemult(r,bioclass,t) = round(biopricemult(r,bioclass,t),3) ;
can_exports_h(r,h,t) = round(can_exports_h(r,h,t),3) ;
cf_hyd_szn_adj(i,szn,r) = round(cf_hyd_szn_adj(i,szn,r),5) ;
cost_cap(i,t) = round(cost_cap(i,t),3) ;
cost_cap_fin_mult(i,r,t) = round(cost_cap_fin_mult(i,r,t),3) ;
cost_cap_fin_mult_noITC(i,r,t) = round(cost_cap_fin_mult_noITC(i,r,t),3) ;
cost_fom(i,v,r,t) = round(cost_fom(i,v,r,t),3) ;
cost_opres(i) = round(cost_opres(i),3) ;
cost_opres(i) = round(cost_opres(i),4) ;
cost_tranline(r) = round(cost_tranline(r),3) ;
cost_vom(i,v,r,t) = round(cost_vom(i,v,r,t),3) ;
degrade(i,tt,t) = round(degrade(i,tt,t),4) ;
distance(r,rr,trtype) = round(distance(r,rr,trtype),3) ;
emit_rate(e,i,v,r,t)$[not sameas(e,"co2")] = round(emit_rate(e,i,v,r,t),6) ;
emit_rate(e,i,v,r,t)$sameas(e,"co2") = round(emit_rate(e,i,v,r,t),4) ;
fuel_price(i,r,t) = round(fuel_price(i,r,t),3) ;
heat_rate(i,v,r,t) = round(heat_rate(i,v,r,t),2) ;
load_exog(r,h,t) = round(load_exog(r,h,t),3) ;
m_avail_retire_exog_rsc(i,v,r,t) = round(m_avail_retire_exog_rsc(i,v,r,t),4) ;
m_capacity_exog(i,v,r,t) = round(m_capacity_exog(i,v,r,t),4) ;
m_cf(i,v,r,h,t) = round(m_cf(i,v,r,h,t),5) ;
m_cf(i,v,r,h,t)$(m_cf(i,v,r,h,t)<0.001) = 0 ;
m_required_prescriptions(pcat,r,t) = round(m_required_prescriptions(pcat,r,t),4) ;
m_rsc_dat(r,i,rscbin,"cost") = round(m_rsc_dat(r,i,rscbin,"cost"),3) ;
minloadfrac(r,i,h) = round(minloadfrac(r,i,h),4) ;
peakdem(r,szn,t) = round(peakdem(r,szn,t),2) ;
prm(r,t) = round(prm(r,t),4) ;
ptc_unit_value(i,v,r,t) = round(ptc_unit_value(i,v,r,t),3) ;
recperc(rpscat,st,t) = round(recperc(rpscat,st,t),4) ;
rsc_fin_mult(i,r,t) = round(rsc_fin_mult(i,r,t),3) ;
tranloss(r,rr,trtype) = round(tranloss(r,rr,trtype),4) ;




*============================
* --- Iteration Tracking ---
*============================

parameter cap_iter(i,v,r,t,cciter) "--MW-- Capacity by iteration"
          gen_iter(i,v,r,t,cciter) "--MWh-- Annual uncurtailed generation by iteration"
          cap_firm_iter(i,v,r,szn,t,cciter) "--MW-- VRE Firm capacity by iteration"
          curt_tot_iter(i,v,r,t,cciter) "--MWh-- Total VRE total curtailment by iteration"
;
cap_iter(i,v,r,t,cciter) = 0 ;
gen_iter(i,v,r,t,cciter) = 0 ;
*================================================
* --- SEQUENTIAL SETUP ---
*================================================
$ifthen.seq %timetype%=="seq"

* remove cc_int as it is only used in the intertemporal setting
cc_int(i,v,r,szn,t) = 0 ;

*need to increase the financial multiplier for PV
*to account for the future capacity degradation
*should avoid hardcoding in the future
cost_cap_fin_mult(i,r,t)$pv(i) = 1.052 * cost_cap_fin_mult(i,r,t) ;
cost_cap_fin_mult_noITC(i,r,t)$pv(i) = 1.052 * cost_cap_fin_mult_noITC(i,r,t) ;

*for the sequential solve, what matters is the relative ratio of the pvf for capital and the pvf for onm
*therefore, we set the pvf capital to one, and then pvf_onm to the relative 20 year present value by using the crf
pvf_capital(t) = 1 ;
pvf_onm(t)$tmodel_new(t) = round(1 / crf(t),6) ;

$endif.seq


*================================================
* --- INTERTEMPORAL SETUP ---
*================================================

$ifthen.int %timetype%=="int"

*load the default values for capacity credit and curtailment
$ifthene.loadcccurt %cc_curt_load%==1
$gdxin inputs_case%ds%cccurt_defaults.gdx
$loadr cc_int
$loadr curt_int
$loadr curt_mingen_int
$gdxin
$endif.loadcccurt

tmodel(t) = no ;
tmodel(t)$[tmodel_new(t)$(yeart(t)<=%endyear%)] = yes ;


parameter pv_age_residual_fraction(i,t) "ratio of the amount of service years remaining on pv panels in the final year from year t to the maximum life of pv panels";

pv_age_residual_fraction(i,t)$pv(i) = max(0, maxage(i) - (sum(tt$tlast(tt),yeart(tt)) - yeart(t))) / maxage(i);

*need to increase the financial multiplier for PV to account for the future capacity degradation 
*should avoid hardcoding in the future -- for the intertemporal case, using a portion
*of the degradation multiplier based on fraction of life beyond the solve period

cost_cap_fin_mult(i,r,t)$pv(i) = 
      round((1 + 0.052 * pv_age_residual_fraction(i,t)) * cost_cap_fin_mult(i,r,t), 4) ;

cost_cap_fin_mult_noITC(i,r,t)$pv(i) = 
      round((1 + 0.052 * pv_age_residual_fraction(i,t)) * cost_cap_fin_mult_noITC(i,r,t), 4) ;

*Cap the maximum CC in the first solve iteration
cc_int(i,v,r,szn,t)$[rsc_i(i)$(cc_int(i,v,r,szn,t)>0.4)$wind(i)] = 0.4 ;
cc_int(i,v,r,szn,t)$[rsc_i(i)$(cc_int(i,v,r,szn,t)>0.6)$pv(i)] = 0.6 ;


*increase reslim for the intertemporal solve
option reslim = 345600 ;
*set objective function to millions of dollars
cost_scale = 1;

*marginal capacity value not used in intertemporal case
m_cc_mar(i,r,szn,t) = 0 ;
*static capacity value for existing capacity not used in intertemporal case
cc_old(i,r,szn,t) = 0 ;

*sets needed for the demand side
*following sets are needed for linear interpolation of price
*that determine the year before the non-solved year and the year after
set t_before, t_after ;
alias(t,ttt) ;
t_before(t,tt)$[tprev(t,tt)$(ord(tt) = smax{ttt, ord(ttt)$tprev(t,ttt) })] = yes ;
t_after(t,tt)$tprev(tt,t) = yes ;

* intentionally not declaring all indices to make these flexibile
* rep only used when running the demand side
parameter rep                  "reporting for all sectors/timeslices/regions"
          repannual(t,*,*)     "national and annual reporting"
;


scalar    maxdev    "maximum deviation of price from one iteration to the next" /0.25/ ;


$endif.int


*=======================
* --- WINDOW SETUP ---
*=======================

$ifthen.win %timetype%=="win"

cost_scale = 1e-3 ;

*load the default values for capacity credit and curtailment
$ifthene.loadcccurt %cc_curt_load%==1
$gdxin inputs_case%ds%cccurt_defaults.gdx
$loadr cc_int
$loadr curt_int
$loadr curt_mingen_int
$gdxin
$endif.loadcccurt

*marginal capacity value not used in intertemporal case
m_cc_mar(i,r,szn,t) = 0 ;
*static capacity value for existing capacity not used in intertemporal case
cc_old(i,r,szn,t) = 0 ;

tmodel(t) = no ;

set windows /1*40/ ;
set blocks /start,stop/ ;


table solvewindows(windows,blocks)
$ondelim
$include inputs_case%ds%windows.csv
$offdelim
;


parameter pv_age_residual_fraction(i,t) "ratio of the amount of service years remaining on pv panels in the final year from year t to the maximum life of pv panels";

* for the window solve, pv_age_residual_fraction is based 
* on the window of years being solved
pv_age_residual_fraction(i,t)$pv(i) = 0;


$endif.win

*===============================
* --- Capacity Credit SETUP ---
*===============================

* create LDC files that are used in all solve years capacity credit calculations
execute_unload 'inputs_case%ds%LDC_prep.gdx'   rfeas, r_rs, r_rto;
execute 'python inputs_case%ds%LDC_prep.py %HourlyStaticFileSwitch% %case% %basedir% %csp_configs%'

*======================
* --- Unload all inputs ---
*======================

execute_unload 'inputs_case%ds%inputs.gdx' ;
