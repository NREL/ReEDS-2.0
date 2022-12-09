

$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

Model ReEDSmodel /all/ ;

*=================================
* -- MODEL AND SOLVER OPTIONS --
*=================================

OPTION lp = %solver% ;
ReEDSmodel.optfile = %GSw_gopt% ;
*treat fixed variables as parameters
ReEDSmodel.holdfixed = 1 ;

$ifthen %solver%==CBC
* adjust the GAMS infeasibility tolerance to handle empty rows when using CBC
ReEDSmodel.tolinfeas = 1e-15 ;
$endif

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
noretire(i)$[(storage_standalone(i) or hyd_add_pump(i))] = yes ;

*all existings plants of any technology can be retired if Sw_Retire = 1
valret(i,v)$[(Sw_Retire=1)$initv(v)$(not noretire(i))] = yes ;

*only existing coal and gas are retirable if Sw_Retire = 2
valret(i,v)$[(Sw_Retire=2)$initv(v)$(not noretire(i))
            $(coal(i) or gas(i) or ogs(i))] = yes ;

*All new and existing nuclear, coal, and gas are retirable if Sw_Retire = 3
*Existing plants have to meet the min_retire_age before retiring
valret(i,v)$[((Sw_Retire=3) or (Sw_Retire=5))$(not noretire(i))
            $(coal(i) or gas(i) or nuclear(i) or ogs(i))] = yes ;

*new and existings plants of any technology can be retired if Sw_Retire = 4
valret(i,v)$[(Sw_Retire=4)$(not noretire(i))] = yes ;

retiretech(i,v,r,t)$[valret(i,v)$valcap(i,v,r,t)] = yes ;

* when Sw_Retire = 3 ensure that plants do not retire before their minimum age
retiretech(i,v,r,t)$[((Sw_Retire=3) or (Sw_Retire=5))$initv(v)$(not noretire(i))$(plant_age(i,v,r,t) <= min_retire_age(i))
                    $(coal(i) or gas(i) or nuclear(i) or ogs(i))] = no ;

* for sw_retire=5, don't allow nuclear to retire until 2030
retiretech(i,v,r,t)$[(Sw_Retire=5)$nuclear(i)$(yeart(t)<=2030)] = no ;

*several states have subsidies for nuclear power, so do not allow nuclear to retire in these states
*before the year specified (see https://www.eia.gov/todayinenergy/detail.php?id=41534)
*Note that Ohio has since repealed their nuclear subsidy, so is no longer included
retiretech(i,initv,r,t)$[r_st(r,"CT")$(yeart(t)<2030)$valcap(i,initv,r,t)$nuclear(i)] = no ;
retiretech(i,initv,r,t)$[r_st(r,"IL")$(yeart(t)<2028)$valcap(i,initv,r,t)$nuclear(i)] = no ;
retiretech(i,initv,r,t)$[r_st(r,"NJ")$(yeart(t)<2026)$valcap(i,initv,r,t)$nuclear(i)] = no ;
retiretech(i,initv,r,t)$[r_st(r,"NY")$(yeart(t)<2030)$valcap(i,initv,r,t)$nuclear(i)] = no ;

* if Sw_NukeNoRetire is enabled, don't allow nuclear to retire through Sw_NukeNoRetireYear
if(Sw_NukeNoRetire = 1,
         retiretech(i,v,r,t)$[nuclear(i)$(yeart(t)<=Sw_NukeNoRetireYear)] = no ;
) ;


*Do not allow retirements before they are allowed
retiretech(i,v,r,t)$[(yeart(t)<Sw_Retireyear)] = no ;

*Allow forced retirements to be done endogenously by the model
retiretech(i,v,r,t)$[forced_retirements(i,r,t)$valcap(i,v,r,t)] = yes ;

*Need to enable endogenous retirements for plants that can have persistent upgrades
retiretech(i,v,r,t)$[(yeart(t)>=Sw_Upgradeyear)$(yeart(t)>=Sw_Retireyear)$(Sw_Upgrades = 2)
                     $sum{ii$[upgrade_from(ii,i)$valcap(ii,v,r,t)], 1 }] = yes ;
*============================
* Setting for CAP SCENARIO
*============================

* set emissions cap here...
* note that it needs to be in metric tons of CO2
if(Sw_AnnualCap = 1,
         emit_cap("CO2",t) = co2_cap(t) ;
) ;

*=============================
* Curtailment and CC Settings
*=============================

set tload(t) "years in which data is loaded" ;
tload(t) = no ;

set cciter "placeholder for iteration number for tracking CC and curtailment" /0*20/ ;
set loadset "set used for loading in merged gdx files" / ReEDS_Augur_2010*ReEDS_Augur_%endyear% /;

parameter
z_rep(t)                                       "--$-- objective function value by year"
z_rep_inv(t)                                   "--$-- investment component of objective function by year"
z_rep_op(t)                                    "--$-- operation component of objective function by year"
cap_fraction_load(i,v,r,t)                     "--fraction-- fraction of capacity that was retired"
cc_change(i,v,r,allszn,t)                      "--fraction-- Change of capacity credit between this and previous iteration"
cc_dr_load(i,r,allszn,t)                       "--fraction--  cc_dr loading in from the cc_out gdx file"
cc_dr_load2(loadset,i,r,allszn,t)              "--fraction--  cc_dr loading in from the cc_out gdx file"
cc_iter(i,v,r,allszn,t,cciter)                 "--fraction-- Actual capacity value in iteration cciter"
cc_mar_load(i,r,ccreg,allszn,t)                "--fraction-- cc_mar loading in from the cc_out gdx file"
cc_mar_load2(loadset,i,r,allszn,t)             "--fraction-- cc_mar loading in from the cc_out gdx file"
cc_old_load2(loadset,i,r,allszn,t)             "--MW-- cc_old loading in from the cc_out gdx file"
cc_scale(i,r,allszn,t)                         "--unitless-- scaling of marginal capacity value levels in intertemporal runs to equal total capacity value"
cc_totmarg(i,r,allszn,t)                       "--MW-- original estimate of total capacity value for intertemporal, based on marginals"
curt_change(i,r,allh,t)                        "--fraction-- Change of curtailment between this and previous iteration"
curt_dr_load(i,v,r,allh,allsrc,t)              "--fraction-- curt_dr value loaded from gdx file"
curt_dr_load2(loadset,i,v,r,allh,allsrc,t)     "--fraction-- curt_dr value loaded from gdx file"
curt_iter(i,r,allh,t,cciter)                   "--fraction-- Actual curtailment in iteration cciter"
curt_marg_load(i,r,allh,t)                     "--fraction-- marginal curtailment rate for new generators, loaded from gdx file"
curt_marg_load2(loadset,i,r,allh,t)            "--fraction-- marginal curtailment rate for new generators, loaded from gdx file"
curt_mingen_change(r,allh,t)                   "--fraction-- Change of mingen curtailment between this and previous iteration"
curt_mingen_iter(r,allh,t,cciter)              "--fraction-- Actual curtailment from mingen in iteration cciter"
curt_mingen_load2(loadset,r,allh,t)            "--fraction-- fraction of addition curtailment induced by increasing the minimum generation level, loaded from gdx file (so as to not overwrite existing values for non-modeled years)"
curt_old_load(r,allh,t)                        "--MW-- curt_old but loaded in from the gdx file for whichever year"
curt_old_load2(loadset,r,allh,t)               "--MW-- curt_old but loaded in from the gdx file for whichever year"
curt_prod_load(r,allh,t)                       "--fraction-- curt_h2 valued loaded from gdx file"
curt_scale(r,allh,t)                           "--unitless-- scaling of marginal curtailment levels in intertemporal runs to equal total curtailment levels"
curt_stor_load(i,v,r,allh,allsrc,t)            "--fraction-- curt_stor value loaded from gdx file"
curt_stor_load2(loadset,i,v,r,allh,allsrc,t)   "--fraction-- curt_stor value loaded from gdx file"
curt_totmarg(r,allh,t)                         "--MW-- original estimate of total curtailment for intertemporal, based on marginals"
curt_tran_load(r,rr,allh,t)                    "--fraction-- curt_tran value loaded from gdx file"
curt_tran_load2(loadset,r,rr,allh,t)           "--fraction-- curt_tran value loaded from gdx file"
hourly_arbitrage_value_load(i,r,t)             "--$/MW-yr-- hourly_arbitrage_value value from gdx file"
hourly_arbitrage_value_load2(loadset,i,r,t)    "--$/MW-yr-- hourly_arbitrage_value value from gdx file"
hybrid_cc_load(pvb_config,r,allszn,sdbin,t)    "--fraction-- derate factor for the capacity credit of hybrid resources"
net_load_adj_no_curt_h_load(r,allh,t)          "--MW-- net load accounting for VRE, mingen, and storage; used to characterize curtailment reduction from new transmission"
oldMINGEN(r,allh,t)                            "--MW-- Minimum generation from the previous iteration"
oldVREgen(r,allh,t)                            "--MW-- generation from endogenous VRE capacity that existed the year before, or iteration before"
sdbin_size_load2(loadset,ccreg,allszn,sdbin,t) "--MW-- bin_size loading in from the cc_out gdx file"
storage_in_min_load(r,allh,t)                  "--MW-- storage_in_min value loaded from gdx file"
storage_in_min_load2(loadset,r,allh,t)         "--MW-- storage_in_min value loaded from gdx file"
storage_starting_soc_load(i,v,r,allh,t)        "--MWh-- starting stage of charge as indicated by Augur"
;

parameters powerfrac_upstream_(r,rr,allh,t)   "--unitless-- fraction of power at r that was generated at rr",
           powerfrac_downstream_(rr,r,allh,t) "--unitless-- fraction of power generated at rr that serves load at r" ;

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
m_capacity_exog(i,v,r,t)$[not valcap(i,v,r,t)] = 0 ;
m_cf(i,v,r,h,t)$[not valcap(i,v,r,t)] = 0 ;
emit_rate(e,i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;



* round parameters
acp_price(st,t)$acp_price(st,t) = round(acp_price(st,t),3) ;
avail(i,h)$avail(i,h) = round(avail(i,h),4) ;
batterymandate(r,t)$batterymandate(r,t) = round(batterymandate(r,t),2) ;
bcr(i)$bcr(i) = round(bcr(i),4) ;
derate_geo_vintage(i,v)$derate_geo_vintage(i,v) = round(derate_geo_vintage(i,v),4) ;
can_exports_h(r,h,t)$can_exports_h(r,h,t) = round(can_exports_h(r,h,t),3) ;
cap_hyd_szn_adj(i,szn,r)$cap_hyd_szn_adj(i,szn,r) = round(cap_hyd_szn_adj(i,szn,r),5) ;
cc_storage(i,sdbin)$cc_storage(i,sdbin) = round(cc_storage(i,sdbin),3) ;
cendiv_weights(r,cendiv)$cendiv_weights(r,cendiv) = round(cendiv_weights(r,cendiv), 3) ;
cf_hyd(i,szn,r,t)$cf_hyd(i,szn,r,t) = round(cf_hyd(i,szn,r,t),4) ;
cost_cap(i,t)$cost_cap(i,t) = round(cost_cap(i,t),3) ;


cost_fom(i,v,r,t)$cost_fom(i,v,r,t) = round(cost_fom(i,v,r,t),3) ;
cost_h2_transport(r,rr)$cost_h2_transport(r,rr) = round(cost_h2_transport(r,rr),3) ;
cost_opres(i,ortype,t)$cost_opres(i,ortype,t) = round(cost_opres(i,ortype,t),3) ;
cost_prod(i,v,r,t)$cost_prod(i,v,r,t) = round(cost_prod(i,v,r,t), 3) ;
cost_upgrade(i,t)$cost_upgrade(i,t) = round(cost_upgrade(i,t), 3) ;
cost_vom(i,v,r,t)$cost_vom(i,v,r,t) = round(cost_vom(i,v,r,t),3) ;
cost_vom_pvb_b(i,v,r,t)$cost_vom_pvb_b(i,v,r,t) = round(cost_vom_pvb_b(i,v,r,t), 3) ;
cost_vom_pvb_p(i,v,r,t)$cost_vom_pvb_p(i,v,r,t) = round(cost_vom_pvb_p(i,v,r,t), 3) ;
degrade(i,tt,t)$degrade(i,tt,t) = round(degrade(i,tt,t),4) ;
distance(r,rr,trtype)$distance(r,rr,trtype) = round(distance(r,rr,trtype),3) ;
* non-CO2 emission/capture rates get small, here making sure accounting stays correct
emit_rate(e,i,v,r,t)$[(not sameas(e,"co2"))$valgen(i,v,r,t)] = round(emit_rate(e,i,v,r,t),6) ;
emit_rate(e,i,v,r,t)$(sameas(e,"co2")$valgen(i,v,r,t)) = round(emit_rate(e,i,v,r,t),4) ;
capture_rate(e,i,v,r,t)$[(not sameas(e,"co2"))$valgen(i,v,r,t)] = round(capture_rate(e,i,v,r,t),6) ;
capture_rate(e,i,v,r,t)$(sameas(e,"co2")$valgen(i,v,r,t)) = round(capture_rate(e,i,v,r,t),4) ;
fuel_price(i,r,t)$fuel_price(i,r,t) = round(fuel_price(i,r,t),3) ;
gasmultterm(cendiv,t)$gasmultterm(cendiv,t) = round(gasmultterm(cendiv,t), 3) ;
h_weight_csapr(h)$h_weight_csapr(h) = round(h_weight_csapr(h),4) ;
heat_rate(i,v,r,t)$heat_rate(i,v,r,t) = round(heat_rate(i,v,r,t),2) ;
load_exog(r,h,t)$[rfeas(r)$load_exog(r,h,t)] = round(load_exog(r,h,t),3) ;
load_exog_static(r,h,t)$[rfeas(r)$load_exog_static(r,h,t)] = round(load_exog_static(r,h,t),3) ;
avail_retire_exog_rsc(i,v,r,t)$valcap(i,v,r,t) = round(avail_retire_exog_rsc(i,v,r,t),4) ;
m_capacity_exog(i,v,r,t)$valcap(i,v,r,t) = round(m_capacity_exog(i,v,r,t),4) ;
m_cf(i,v,r,h,t)$[(m_cf(i,v,r,h,t)<0.001)$valcap(i,v,r,t)] = 0 ;
m_cf(i,v,r,h,t)$[cf_tech(i)$valcap(i,v,r,t)] = round(m_cf(i,v,r,h,t),5) ;
m_rsc_dat(r,i,rscbin,"cap")$m_rsc_dat(r,i,rscbin,"cap") = round(m_rsc_dat(r,i,rscbin,"cap"),4) ;
m_rsc_dat(r,i,rscbin,"cost")$m_rsc_dat(r,i,rscbin,"cost") = round(m_rsc_dat(r,i,rscbin,"cost"),3) ;
mingen_postret(r,szn,tt) = round(mingen_postret(r,szn,tt),4) ;
minloadfrac(r,i,h)$minloadfrac(r,i,h) = round(minloadfrac(r,i,h),4) ;
net_trade_can(r,h,t) = round(net_trade_can(r,h,t),3) ;
peakdem_static_szn(r,szn,t)$peakdem_static_szn(r,szn,t) = round(peakdem_static_szn(r,szn,t),2) ;
prm(r,t)$prm(r,t) = round(prm(r,t),4) ;
ptc_value_scaled(i,v,t)$ptc_value_scaled(i,v,t) = round(ptc_value_scaled(i,v,t),3) ;
recperc(rpscat,st,t)$recperc(rpscat,st,t) = round(recperc(rpscat,st,t),4) ;
rggi_cap(t)$rggi_cap(t) = round(rggi_cap(t),4) ;
state_cap(t)$state_cap(t) = round(state_cap(t),4) ;
storage_eff_pvb_g(i,t)$storage_eff_pvb_g(i,t) = round(storage_eff_pvb_g(i,t),4) ;
storage_eff_pvb_p(i,t)$storage_eff_pvb_p(i,t) = round(storage_eff_pvb_p(i,t),4) ;
szn_adj_gas(h)$szn_adj_gas(h) = round(szn_adj_gas(h), 3) ;
tranloss(r,rr,trtype)$tranloss(r,rr,trtype) = round(tranloss(r,rr,trtype),4) ;
transmission_line_capcost(r,rr,trtype)$transmission_line_capcost(r,rr,trtype) = round(transmission_line_capcost(r,rr,trtype),3) ;
transmission_line_fom(r,rr,trtype)$transmission_line_fom(r,rr,trtype) = round(transmission_line_fom(r,rr,trtype),3) ;
trans_cost_cap_fin_mult(t) = round(trans_cost_cap_fin_mult(t),3) ;
trans_cost_cap_fin_mult_noITC(t) = round(trans_cost_cap_fin_mult_noITC(t),3) ;
winter_cap_frac_delta(i,v,r)$winter_cap_frac_delta(i,v,r) = round(winter_cap_frac_delta(i,v,r),3) ;
seas_cap_frac_delta(i,v,r,szn,t)$seas_cap_frac_delta(i,v,r,szn,t) = round(seas_cap_frac_delta(i,v,r,szn,t),3) ;


* Track the initial amount of m_rsc_dat capacity to compare in e_report
* We adust upwards by small amounts given potential for infeasibilities
* in very tiny amounts and thus track the extent of the adjustments
parameter m_rsc_dat_init(r,i,rscbin) "--MW-- Inital amount of resource supply curve capacity to compare with final amounts after adjustments" ;
m_rsc_dat_init(r,i,rscbin)$m_rsc_dat(r,i,rscbin,"cap") = m_rsc_dat(r,i,rscbin,"cap") ;

*============================
* --- Iteration Tracking ---
*============================

parameter cap_iter(i,v,r,t,cciter)             "--MW-- Capacity by iteration"
          gen_iter(i,v,r,t,cciter)             "--MWh-- Annual uncurtailed generation by iteration"
          cap_firm_iter(i,v,r,allszn,t,cciter) "--MW-- VRE Firm capacity by iteration"
          curt_tot_iter(i,v,r,t,cciter)        "--MWh-- Total VRE total curtailment by iteration"
;
cap_iter(i,v,r,t,cciter) = 0 ;
gen_iter(i,v,r,t,cciter) = 0 ;
*================================================
* --- SEQUENTIAL SETUP ---
*================================================
$ifthen.seq %timetype%=="seq"

* remove cc_int as it is only used in the intertemporal setting
cc_int(i,v,r,szn,t) = 0 ;

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

*Assign csp3 and csp4 to use the same initial values as csp2_1
cc_int(i,v,r,szn,t)$[csp3(i) or csp4(i)] = cc_int('csp2_1',v,r,szn,t) ;

tmodel(t) = no ;
tmodel(t)$[tmodel_new(t)$(yeart(t)<=%endyear%)] = yes ;


parameter pv_age_residual_fraction(i,t) "ratio of the amount of service years remaining on pv panels in the final year from year t to the maximum life of pv panels" ;

pv_age_residual_fraction(i,t)$pv(i) = max(0, maxage(i) - (sum{tt$tlast(tt), yeart(tt) } - yeart(t))) / maxage(i) ;

*Cap the maximum CC in the first solve iteration
cc_int(i,v,r,szn,t)$[rsc_i(i)$(cc_int(i,v,r,szn,t)>0.4)$wind(i)] = 0.4 ;
cc_int(i,v,r,szn,t)$[rsc_i(i)$(cc_int(i,v,r,szn,t)>0.6)$pv(i)] = 0.6 ;


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

pvf_capital0(t) = pvf_capital(t) ;
pvf_onm0(t) = pvf_onm(t) ;

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
$include inputs_case%ds%windows_%windows_suffix%.csv
$offdelim
;


parameter pv_age_residual_fraction(i,t) "ratio of the amount of service years remaining on pv panels in the final year from year t to the maximum life of pv panels" ;

* for the window solve, pv_age_residual_fraction is based
* on the window of years being solved
pv_age_residual_fraction(i,t)$pv(i) = 0 ;


$endif.win


*======================
* --- Unload all inputs ---
*======================

execute_unload 'inputs_case%ds%inputs.gdx' ;
