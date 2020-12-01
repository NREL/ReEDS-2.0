$ontext
This file creates a gdx file with all of the data necessary for the Augur module to solve. This includes:
    - Generator capacities
    - Exogenous retirments (sequential solves only)
    - Wind capacity by build year (because wind CFs change by build year)
    - heat rates, fuel costs, and vom costs
    - capacity factors (hydro, wind)
    - availability rates (1 - outage rates)
    - transmission capacities and loss rates
    - technology sets
$offtext

$if not set start_year $setglobal start_year 2010

*===============================
* Set and parameter definitions
*===============================

set tcheckret(t) "set of all years to check for retiring capacity"
    tcheckretwind(t)  "set of all years to consider for retiring wind capacity"
    tcur(t)   "current year"
    tnext(t)  "next year"
    valcap_iv(i,v)
    valcap_i(i)
    valcap_ir(i,r)
    routes_filt(r,rr) "set of transmission connections"
;

parameter cap_trans(r,rr,trtype)   "--MW-- transmission capacity"
losses_trans_h(rr,r,h,trtype)      "--MW-- transmission losses by timeslice"
inv_tmp(i,v,r,t,tt)                "--MW-- relevant capacities along with their build year and retire year"
retire_exog_init(i,v,r,rs,t)       "--MW-- exogenous retired capacity"
retire_exog_tmp(i,v,r,t)           "--MW-- exogenous retired capacity"
retire_exog(i,v,r,t)               "--MW-- exogenous retired capacity"
ret_lifetime(i,v,r,t)              "--MW-- capacity that will be retired before the end of the next solve year due to its age"
cap_export(i,v,r)                  "--MW-- relavent capacities for capacity credit calculations"
cap_csp(i,v,r)                     "--MW-- CSP-TES capacity"
cap_cspns(i,v,r)                   "--MW-- CSP-NS capacity"
cap_pv(i,v,r)                      "--MW-- PV capacity"
cap_storage(i,v,r)                 "--MW-- storage capacity"
cap_thermal(i,v,r)                 "--MW-- thermal capacity"
retire_exog_wind(i,v,r,t)          "--MW-- total exogenously retired wind capacity"
ret_lifetime_wind(i,v,r,t)         "--MW-- capacity that will be retired before the end of the next solve year due to its age"
cap_wind_init(i,v,r,t)             "--MW-- initial wind capacity"
cap_wind_inv(i,v,r,t)              "--MW-- wind investments by year"
cap_wind_ret(i,v,r)                "--MW-- total wind capacity retirements"
heat_rate_filt(i,v,r)              "--MMBtu/MWh-- heat rate"
repbioprice_filt(r)                "--2004$/MWh-- marginal price for biofuel in regiond where biofuel was used"
cost_vom_filt(i,v,r)               "--2004$/MWh-- variable OM"
fuel_price_filt(i,r)               "--2004$/MMbtu-- fuel prices by technology"
avail_filt(i,v,szn)                "--fraction-- fraction of capacity available for generation by season"
cf_hyd_filt(i,szn,r)               "--fraction--unadjusted hydro capacity factors by season"
cfhist_hyd_filt(r,szn,i)           "--unitless--seasonal adjustment for capacity factors in historical years"
m_cf_filt(i,v,r,h,t)               "--fraction-- capacity factor used in the model"
cf_adj_t_filt(i,v,t)               "--fraction-- capacity factor adjustment for wind"
cost_cap_fin_mult_filt(i,r,t)      "--unitless-- capital cost financial multipliers"
cost_cap_filt(i,t)                 "--2004$/MW-- technology capital costs"
rsc_dat_filt(r,rs,i,rscbin,sc_cat) "--varies-- resource supply curve data"
flex_load(r,h,t)                   "--MW-- total exogenously defined flexible load"
flex_load_opt(r,h,t)              "--MW-- model results for optimizing flexible load"
;

*populate year sets
tcheckret(t) = no ;
loop(t$[(yeart(t)>%cur_year%)$(yeart(t)<=%next_year%)],
tcheckret(t) = yes ;
) ;

tcheckretwind(t) = no ;
loop(t$[(yeart(t)>=%start_year%)$(yeart(t)<=%next_year%)],
tcheckretwind(t) = yes ;
) ;

tcur(t) = no ;
tcur("%cur_year%") = yes ;

tnext(t) = no ;
tnext("%next_year%") = yes ;

*populate reduced-form sets
valcap_iv(i,v) = sum{(r,t)$tcur(t), valcap(i,v,r,t)} ;
valcap_i(i) = sum{v, valcap_iv(i,v)} ;
valcap_ir(i,r) = sum{t$tcur(t), valcap_irt(i,r,t)} ;

*=======================================
* Removing banned technologies from sets
*=======================================

canada(i) = canada(i)$(not ban(i)) ;
coal(i) = coal(i)$(not ban(i)) ;
csp_sm(i) = csp_sm(i)$(not ban(i)) ;
geo(i) = geo(i)$(not ban(i)) ;
hydro_d(i) = hydro_d(i)$(not ban(i)) ;
hydro_nd(i) = hydro_nd(i)$(not ban(i)) ;
nuclear(i) = nuclear(i)$(not ban(i)) ;
storage(i) = storage(i)$(not ban(i)) ;
storage_duration(i) = storage_duration(i)$(not ban(i)) ;
storage_eff(i,t) = storage_eff(i,t)$(not ban(i)) ;
storage_no_csp(i) = storage_no_csp(i)$(not ban(i)) ;

*==============================
* Get ReEDS generation capacity
*==============================

* get the build year and retire year for all investments
* NOTE the variable CAP holds degraded capacity, so when we retire capacity we need to account for degredation
inv_tmp(i,v,r,t,tt)$[t.val+maxage(i)=tt.val] = [INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)] * degrade(i,t,tt) ;

* determine exogenous retirements by year
retire_exog_init(i,v,r,rs,t)$(capacity_exog(i,v,r,rs,t-1) > capacity_exog(i,v,r,rs,t)) =
        [capacity_exog(i,v,r,rs,t-1) - capacity_exog(i,v,r,rs,t)]$initv(v) ;

* ignore exogenous retirements for any vintage classes that are not "initial"
retire_exog_init(i,v,r,rs,t)$[not initv(v)] = 0 ;

* fix the r & rs indices for exogenous retirements

retire_exog_tmp(i,v,rb,t) = retire_exog_init(i,v,rb,"sk",t) ;
retire_exog_tmp(i,v,rs,t)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs), retire_exog_init(i,v,r,rs,t)} ;

* determine the total exogenous retirements that occur within the tcheckret set
* this represents the retirements of all exogenous capacity between the end of the previous solve year and the end of the next solve year
* note that wind capacity will be handled seperately because the vintage is tied to the build year
retire_exog(i,v,r,"%cur_year%") = sum{tcheckret(tt)$(not wind(i)), retire_exog_tmp(i,v,r,tt)} ;

* determine the capacity that will retire due to age within the tcheckret set
* determine the lifetime retirements between the end of the last solve year and the end of the next solve year
* note that wind capacity will be handled seperately because the vintage is tied to the build year
ret_lifetime(i,v,r,"%cur_year%") = sum{(t,tt)$[tcheckret(tt)$(not wind(i))], inv_tmp(i,v,r,t,tt)} ;

* get the installed capacity minus upcoming retirements for all technologies except wind
if(Sw_Timetype("seq") = 1,
* For a sequential solve: use capacity for the NEXT solve year when calculating capacity credit for the NEXT solve year
cap_export(i,v,r) = sum{t$[tcur(t)$valcap(i,v,r,t)$(not wind(i))], CAP.l(i,v,r,t) - retire_exog(i,v,r,t) - ret_lifetime(i,v,r,t)} ;
* distributed PV is defined exogenously so just defining it here
cap_export("distpv",v,r) = 0 ;
cap_export("distpv","init-1",r)$rfeas(r) = CAP.l("distpv","init-1",r,"%cur_year%") + inv_distpv(r,"%next_year%") ;
else
* For intertemporal or window solves: use the capacity from the PRIOR iteration of the CURRENT solve year for capacity credit for the NEXT iteration of the CURRENT solve year
cap_export(i,v,r) = sum{t$[tcur(t)$valcap(i,v,r,t)$(not wind(i))], CAP.l(i,v,r,t)} ;
) ;

*cap_export can be less than zero if an exogenous retirement was taken early
cap_export(i,v,r)$[cap_export(i,v,r) < 0] = 0 ;

* grouping capacity by technologies
cap_csp(i,v,r) = cap_export(i,v,r)$[csp(i)$(not csp_nostorage(i))] ;

cap_cspns(i,v,r) = cap_export(i,v,r)$csp_nostorage(i) ;

cap_pv(i,v,r) = cap_export(i,v,r)$pv(i) ;

cap_storage(i,v,r) = cap_export(i,v,r)$storage_no_csp(i) ;

cap_thermal(i,v,r) = cap_export(i,v,r)$[not (pv(i) or storage(i) or csp_nostorage(i))] ;

* Wind capacity is treated separately because wind CFs depend on the build year as well as the vintage.
* It is the only technology where this information matters.

* determine the total exogenous retirements of wind capacity through the end of the next solve year
retire_exog_wind(i,v,r,"%cur_year%")$wind(i) = sum{tcheckretwind(tt), retire_exog_tmp(i,v,r,tt)} ;

* determine the total lifetime retirements of wind capacity through the end of the next solve
ret_lifetime_wind(i,v,r,"%cur_year%")$wind(i) = sum{(t,tt)$tcheckretwind(tt), inv_tmp(i,v,r,t,tt)} ;

* get the initial starting capacity of wind
cap_wind_init(i,v,r,t)$[wind(i)$tfirst(t)$valcap(i,v,r,t)] = CAP.l(i,v,r,t);

* get wind capacity investements by build year
cap_wind_inv(i,v,r,t)$[wind(i)$tcheckretwind(t)$(not tfirst(t))$valinv(i,v,r,t)] = INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) ;

* get the total wind capacity retirements throught the end of the next solve year
cap_wind_ret(i,v,r)$wind(i) = sum{(t)$tcur(t), retire_exog_wind(i,v,r,t) + ret_lifetime_wind(i,v,r,t)} ;

*============================
* Filter necessary input data
*============================

heat_rate_filt(i,v,r) = sum{t$[valcap(i,v,r,t)$tcur(t)], heat_rate(i,v,r,t)} ;

repbioprice_filt(r)$rfeas(r) = sum{t$tcur(t), smax{bioclass$bioused.l(bioclass,r,t), biosupply(r,"cost",bioclass) }} ;

cost_vom_filt(i,v,r) = sum{t$[tcur(t)$valgen(i,v,r,t)], cost_vom(i,v,r,t)} ;

fuel_price_filt(i,r) = sum{t$[valcap_irt(i,r,t)$tcur(t)], fuel_price(i,r,t)} ;

avail_filt(i,v,szn)$[valcap_iv(i,v)$(not vre(i))] = smax{h$h_szn(h,szn), avail(i,v,h)} ;

cf_hyd_filt(i,szn,r)$valcap_ir(i,r) = cf_hyd(i,szn,r) ;

cfhist_hyd_filt(r,szn,i) = sum{t$[valcap_irt(i,r,t)$tcur(t)], cfhist_hyd(r,t,szn,i)} ;

m_cf_filt(i,v,r,h,t) = m_cf(i,v,r,h,t)$[vre(i)$tnext(t)] ;

cf_adj_t_filt(i,v,t) = cf_adj_t(i,v,t)$[tcheckretwind(t)$wind(i)] ;

cost_cap_fin_mult_filt(i,r,t) = cost_cap_fin_mult(i,r,t)$[storage_no_csp(i)$tnext(t)] ;

cost_cap_filt(i,t) = cost_cap(i,t)$[storage_no_csp(i)$tnext(t)] ;

rsc_dat_filt(r,rs,i,rscbin,"cost") = rsc_dat(r,rs,i,rscbin,"cost")$[rfeas(r)$storage_no_csp(i)] ;

*============================
* Get ReEDS transmission data
*============================

cap_trans(r,rr,trtype)$[rfeas(r)$rfeas(rr)] = sum{t$tcur(t), CAPTRAN.l(r,rr,trtype,t)} ;

losses_trans_h(rr,r,h,trtype)$[rfeas(r)$rfeas(rr)] = sum{t$tcur(t), tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype)} ;

routes_filt(r,rr)$[rfeas(r)$rfeas(rr)] = sum{(trtype,t)$tcur(t), routes(r,rr,trtype,t)} ;

*============================
* Flexible load data
*============================

flex_load(r,h,"%cur_year%") = sum{flex_type, load_exog_flex(flex_type,r,h,"%cur_year%")} ;

flex_load_opt(r,h,"%cur_year%") = sum{flex_type, FLEX.l(flex_type,r,h,"%cur_year%")} ;

*=======================================
* Unload all relevant data to a gdx file
*=======================================

execute_unload 'ReEDS_Augur%ds%augur_data%ds%reeds_data_%case%_%next_year%.gdx' avail_filt, canada, cap_csp, cap_cspns, cap_pv, cap_storage, cap_thermal, cap_trans, cap_wind_init, cap_wind_inv, cap_wind_ret, cf_hyd_filt,
                                                         cfhist_hyd_filt, coal, cost_vom_filt, csp_sm, fuel_price_filt, geo, h_szn, heat_rate_filt, cost_cap_fin_mult_filt, cost_cap_filt, rsc_dat_filt, flex_load_opt,
                                                         hierarchy, hours, hydmin, hydro_d, hydro_nd, i, load_multiplier, losses_trans_h, m_cf_filt, nuclear, r, r_cendiv, r_rs, repbioprice_filt, flex_load,
                                                         rfeas, routes_filt, sdbin, storage, storage_duration, storage_eff, storage_no_csp, szn, tranloss, v, vom_hyd, cf_adj_t_filt, pvf_onm ;
