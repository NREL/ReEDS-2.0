

$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

Model %case% /all/ ;


*=================================
* -- MODEL AND SOLVER OPTIONS --
*=================================

OPTION lp = %solver% ;
%case%.optfile = %GSw_gopt% ;
OPTION RESLIM = 50000 ;
*treat fixed variables as parameters
%case%.holdfixed = 1 ;

$ifthen.valstr %GSw_ValStr% == 1
OPTION savepoint = 1 ;
$endif.valstr

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

*only existing coal and gas are retirable if Sw_Retire = 2
valret(i,v)$[(Sw_Retire=2)$initv(v)$(not noretire(i))
            $(coal(i) or gas(i) or ogs(i))] = yes ;

*All new and existing nuclear, coal, and gas are retirable if Sw_Retire = 3
*Existing plants have to meet the min_retire_age before retiring
valret(i,v)$[(Sw_Retire=3)$(not noretire(i))
            $(coal(i) or gas(i) or nuclear(i) or ogs(i))] = yes ;

*new and existings plants of any technology can be retired if Sw_Retire = 4
valret(i,v)$[(Sw_Retire=4)$(not noretire(i))] = yes ;

retiretech(i,v,r,t)$[valret(i,v)$valcap(i,v,r,t)] = yes ;

* when Sw_Retire = 3 ensure that plants do not retire before their minimum age
retiretech(i,v,r,t)$[(Sw_Retire=3)$initv(v)$(not noretire(i))$(plant_age(i,v,r,t) <= min_retire_age(i))
                    $(coal(i) or gas(i) or nuclear(i) or ogs(i))] = no ;


*5 states have subsidies for nuclear power, so do not allow nuclear to retire in these states
*before the year specified (see https://www.eia.gov/todayinenergy/detail.php?id=41534)
retiretech(i,initv,r,t)$[r_st(r,"CT")$(yeart(t)<2030)$valcap(i,initv,r,t)$nuclear(i)] = no ;
retiretech(i,initv,r,t)$[r_st(r,"IL")$(yeart(t)<2028)$valcap(i,initv,r,t)$nuclear(i)] = no ;
retiretech(i,initv,r,t)$[r_st(r,"NJ")$(yeart(t)<2026)$valcap(i,initv,r,t)$nuclear(i)] = no ;
retiretech(i,initv,r,t)$[r_st(r,"NY")$(yeart(t)<2030)$valcap(i,initv,r,t)$nuclear(i)] = no ;
retiretech(i,initv,r,t)$[r_st(r,"OH")$(yeart(t)<2027)$valcap(i,initv,r,t)$nuclear(i)] = no ;

*Do not allow retirements before they are allowed
retiretech(i,v,r,t)$[(yeart(t)<retireyear)] = no ;

*Allow forced retirements to be done endogenously by the model
retiretech(i,v,r,t)$[forced_retirements(i,r,t)$valcap(i,v,r,t)] = yes ;

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
set loadset "set used for loading in merged gdx files" / ReEDS_Augur_%case%_2010*ReEDS_Augur_%case%_2050 /;

parameter curt_old_load(r,h,t)                            "--MW-- curt_old but loaded in from the gdx file for whichever year"
          curt_old_load2(loadset,r,h,t)                   "--MW-- curt_old but loaded in from the gdx file for whichever year"
          curt_marg_load(i,r,h,t)                         "--fraction-- marginal curtailment rate for new generators, loaded from gdx file"
          curt_marg_load2(loadset,i,r,h,t)                "--fraction-- marginal curtailment rate for new generators, loaded from gdx file"
          oldVREgen(r,h,t)                                "--MW-- generation from endogenous VRE capacity that existed the year before, or iteration before"
          oldMINGEN(r,h,t)                                "--MW-- Minimum generation from the previous iteration"
          curt_totmarg(r,h,t)                             "--MW-- original estimate of total curtailment for intertemporal, based on marginals"
          curt_scale(r,h,t)                               "--unitless-- scaling of marginal curtailment levels in intertemporal runs to equal total curtailment levels"
          cc_totmarg(i,r,szn,t)                           "--MW-- original estimate of total capacity value for intertemporal, based on marginals"
          cc_scale(i,r,szn,t)                             "--unitless-- scaling of marginal capacity value levels in intertemporal runs to equal total capacity value"
          cc_iter(i,v,r,szn,t,cciter)                     "--fraction-- Actual capacity value in iteration cciter"
          cc_mar_load(i,r,szn,t)                          "--fraction--  cc_mar loading in from the cc_out gdx file"
          cc_mar_load2(loadset,i,r,szn,t)                 "--fraction--  cc_mar loading in from the cc_out gdx file"
          curt_iter(i,r,h,t,cciter)                       "--fraction-- Actual curtailment in iteration cciter"
          curt_mingen_iter(r,h,t,cciter)                  "--fraction-- Actual curtailment from mingen in iteration cciter"
          cc_change(i,v,r,szn,t)                          "--fraction-- Change of capacity credit between this and previous iteration"
          curt_change(i,r,h,t)                            "--fraction-- Change of curtailment between this and previous iteration"
          curt_mingen_change(r,h,t)                       "--fraction-- Change of mingen curtailment between this and previous iteration"
          curt_stor_load(i,v,r,h,src,t)                   "--fraction-- curt_stor value loaded from gdx file"
          curt_stor_load2(loadset,i,v,r,h,src,t)          "--fraction-- curt_stor value loaded from gdx file"
          curt_tran_load(r,rr,h,t)                        "--fraction-- curt_tran value loaded from gdx file"
          curt_tran_load2(loadset,r,rr,h,t)               "--fraction-- curt_tran value loaded from gdx file"
          curt_reduct_tran_max_load(r,rr,h,t)             "--MW-- curt_reduct_tran loaded from gdx file"
          curt_reduct_tran_max_load2(loadset,r,rr,h,t)    "--MW-- curt_reduct_tran loaded from gdx file"
          storage_in_min_load(r,h,t)                      "--MW-- storage_in_min value loaded from gdx file"
          storage_in_min_load2(loadset,r,h,t)             "--MW-- storage_in_min value loaded from gdx file"
          hourly_arbitrage_value_load(i,r,t)              "--$/MW-yr-- hourly_arbitrage_value value from gdx file"
          hourly_arbitrage_value_load2(loadset,i,r,t)     "--$/MW-yr-- hourly_arbitrage_value value from gdx file"
          sdbin_size_load2(loadset,ccreg,szn,sdbin,t)     "--MW-- bin_size loading in from the cc_out gdx file"
          cc_old_load2(loadset,i,r,szn,t)                 "--MW-- cc_old loading in from the cc_out gdx file"
          curt_mingen_load2(loadset,r,h,t)                "--fraction--  fraction of addition curtailment induced by increasing the minimum generation level, loaded from gdx file (so as to not overwrite existing values for non-modeled years)"
;

parameters powerfrac_upstream_(r,rr,h,t)   "--unitless-- fraction of power at r that was generated at rr",
           powerfrac_downstream_(rr,r,h,t) "--unitless-- fraction of power generated at rr that serves load at r" ;

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

*Initialize marginal on reserve margin constraint
eq_reserve_margin.m(r,szn,t)$[rfeas(r)$tmodel_new(t)] = 0 ;

*trimming the largest matrices to reduce file sizes
cost_vom(i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;
cost_fom(i,v,r,t)$[not valcap(i,v,r,t)] = 0 ;
heat_rate(i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;
m_cf(i,v,r,h,t)$[not valcap(i,v,r,t)] = 0 ;
emit_rate(e,i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;
cost_cap_fin_mult(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))] = 0 ;
cost_cap_fin_mult_noITC(i,r,t)$[not valinv_irt(i,r,t)$(not upgrade(i))] = 0 ;

acp_price(st,t) = round(acp_price(st,t),3) ;
avail(i,v,h) = round(avail(i,v,h),4) ;
batterymandate(r,t) = round(batterymandate(r,t),2) ;
biopricemult(r,bioclass,t) = round(biopricemult(r,bioclass,t),3) ;
can_exports_h(r,h,t) = round(can_exports_h(r,h,t),3) ;
cap_hyd_szn_adj(i,szn,r) = round(cap_hyd_szn_adj(i,szn,r),5) ;
cost_cap(i,t) = round(cost_cap(i,t),3) ;
cost_cap_fin_mult(i,r,t)$[(valinv_irt(i,r,t)) or (upgrade(i))] = round(cost_cap_fin_mult(i,r,t),3) ;
cost_cap_fin_mult_noITC(i,r,t)$[(valinv_irt(i,r,t)) or (upgrade(i))] = round(cost_cap_fin_mult_noITC(i,r,t),3) ;
cost_fom(i,v,r,t)$valcap(i,v,r,t) = round(cost_fom(i,v,r,t),3) ;
cost_opres(i) = round(cost_opres(i),3) ;
cost_tranline(r) = round(cost_tranline(r),3) ;
cost_vom(i,v,r,t)$valgen(i,v,r,t) = round(cost_vom(i,v,r,t),3) ;
degrade(i,tt,t) = round(degrade(i,tt,t),4) ;
distance(r,rr,trtype) = round(distance(r,rr,trtype),3) ;
emit_rate(e,i,v,r,t)$[(not sameas(e,"co2"))$valgen(i,v,r,t)] = round(emit_rate(e,i,v,r,t),6) ;
emit_rate(e,i,v,r,t)$(sameas(e,"co2")$valgen(i,v,r,t)) = round(emit_rate(e,i,v,r,t),4) ;
fuel_price(i,r,t) = round(fuel_price(i,r,t),3) ;
heat_rate(i,v,r,t)$valgen(i,v,r,t) = round(heat_rate(i,v,r,t),2) ;
load_exog(r,h,t)$rfeas(r) = round(load_exog(r,h,t),3) ;
m_avail_retire_exog_rsc(i,v,r,t)$valcap(i,v,r,t) = round(m_avail_retire_exog_rsc(i,v,r,t),4) ;
m_capacity_exog(i,v,r,t)$valcap(i,v,r,t) = round(m_capacity_exog(i,v,r,t),4) ;
m_cf(i,v,r,h,t)$[cf_tech(i)$valcap(i,v,r,t)] = round(m_cf(i,v,r,h,t),5) ;
m_cf(i,v,r,h,t)$[(m_cf(i,v,r,h,t)<0.001)$valcap(i,v,r,t)] = 0 ;
m_required_prescriptions(pcat,r,t) = round(m_required_prescriptions(pcat,r,t),4) ;
m_rsc_dat(r,i,rscbin,"cost")$rsc_i(i) = round(m_rsc_dat(r,i,rscbin,"cost"),3) ;
m_rsc_dat(r,i,rscbin,"cap")$rsc_i(i) = round(m_rsc_dat(r,i,rscbin,"cap"),4) ;
minloadfrac(r,i,h) = round(minloadfrac(r,i,h),4) ;
peakdem_static_szn(r,szn,t) = round(peakdem_static_szn(r,szn,t),2) ;
prm(r,t) = round(prm(r,t),4) ;
ptc_unit_value(i,v,r,t)$valinv(i,v,r,t) = round(ptc_unit_value(i,v,r,t),3) ;
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

*Penalizing new gas built within cost recovery period of 20 years in Virginia
cost_cap_fin_mult(i,r,t)$[gas(i)$r_st(r,'VA')] = cost_cap_fin_mult(i,r,t) * ng_lifetime_cost_adjust(t) ;

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

*Assign csp3 and csp4 to use the same initial values as csp2_1
cc_int(i,v,r,szn,t)$[csp3(i) or csp4(i)] = cc_int('csp2_1',v,r,szn,t) ;

tmodel(t) = no ;
tmodel(t)$[tmodel_new(t)$(yeart(t)<=%endyear%)] = yes ;


parameter pv_age_residual_fraction(i,t) "ratio of the amount of service years remaining on pv panels in the final year from year t to the maximum life of pv panels" ;

pv_age_residual_fraction(i,t)$pv(i) = max(0, maxage(i) - (sum{tt$tlast(tt), yeart(tt) } - yeart(t))) / maxage(i) ;

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
cost_scale = 1 ;

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

parameter pvf_capital0(t) "original pvf_capital used for calculating pvf_capital in window solve",
          pvf_onm0(t)     "original pvf_onm used for calculating pvf_capital in window solve";

pvf_capital0(t) = pvf_capital(t);
pvf_onm0(t) = pvf_onm(t);

cost_scale = 1e-3 ;

*load the default values for capacity credit and curtailment
$ifthene.loadcccurt %cc_curt_load%==1
$gdxin inputs_case%ds%cccurt_defaults.gdx
$loadr cc_int
$loadr curt_int
$loadr curt_mingen_int
$gdxin
$endif.loadcccurt

*Assign csp3 and csp4 to use the same initial values as csp2_1
cc_int(i,v,r,szn,t)$[csp3(i) or csp4(i)] = cc_int('csp2_1',v,r,szn,t) ;

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


parameter pv_age_residual_fraction(i,t) "ratio of the amount of service years remaining on pv panels in the final year from year t to the maximum life of pv panels" ;

* for the window solve, pv_age_residual_fraction is based
* on the window of years being solved
pv_age_residual_fraction(i,t)$pv(i) = 0 ;


$endif.win


*===============================
* --- Capacity Credit SETUP ---
*===============================

* create LDC files that are used in all solve years capacity credit calculations
execute_unload 'inputs_case%ds%LDC_prep.gdx' distloss, rfeas, r_rs, r_ccreg ;
execute 'python inputs_case%ds%LDC_prep.py %HourlyStaticFileSwitch% %case% %basedir% %GSw_EFS1_AllYearLoad%'

*======================
* --- Unload all inputs ---
*======================

execute_unload 'inputs_case%ds%inputs.gdx' ;
