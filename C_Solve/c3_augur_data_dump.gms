$ontext
This file creates a gdx file with all of the data necessary for the Augur module to solve. This includes:
    - Generator capacities
    - Exogenous retirments (sequential solves only)
    - Wind capacity by build year (because wind CFs can change by build year)
    - heat rates, fuel costs, and vom costs
    - capacity factors (hydro, wind)
    - availability rates (1 - outage rates)
    - transmission capacities and loss rates
    - technology sets
$offtext

$if not set start_year $setglobal start_year 2020

*===============================
* Set and parameter definitions
*===============================

set tcheckret(t) "set of all years to check for retiring capacity"
    tcheckretonswind(t)  "set of all years to consider for retiring onshore wind capacity"
    tcheckretofswind(t)  "set of all years to consider for retiring offshore wind capacity"
    tcur(t)   "current year"
    tnext(t)  "next year"
    valcap_iv(i,v)
    valcap_i(i)
    valcap_ir(i,r)
    valcap_irt(i,r,t)
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
cap_pv(i,v,r)                      "--MW-- PV capacity"
cap_storage(i,v,r)                 "--MW-- storage capacity"
cap_thermal(i,v,r)                 "--MW-- thermal capacity"
retire_exog_onswind(i,v,r,t)       "--MW-- total exogenously retired onshore wind capacity"
retire_exog_ofswind(i,v,r,t)       "--MW-- total exogenously retired offshore wind capacity"
ret_lifetime_onswind(i,v,r,t)      "--MW-- capacity that will be retired before the end of the next solve year due to its age (onshore wind)"
ret_lifetime_ofswind(i,v,r,t)      "--MW-- capacity that will be retired before the end of the next solve year due to its age (offshore wind)"
cap_onswind(i,v,r)                 "--MW-- initial onshore wind capacity"
cap_ofswind(i,v,r)                 "--MW-- initial offshore wind capacity"
*cap_wind_inv(i,v,r,t)              "--MW-- wind investments by year"
*cap_wind_ret(i,v,r)                "--MW-- total wind capacity retirements"
heat_rate_filt(i,v,r)              "--MMBtu/MWh-- heat rate"
cost_vom_filt(i,v,r)               "--2017Rs/MWh-- variable OM"
fuel_price_filt(i,r)               "--2017Rs/MMbtu-- fuel prices by technology"
avail_filt(i,v,szn)                "--fraction-- fraction of capacity available for generation by season"
cf_hyd_filt(i,szn,r)               "--fraction--unadjusted hydro capacity factors by season"
m_cf_filt(i,v,r,h,t)               "--fraction-- capacity factor used in the model"
cf_adj_t(i,v,t)                    "--fraction -- capacity factor adjustments over time for RSC technologies"
cf_adj_t_filt_onswind(i,v,t)       "--fraction-- capacity factor adjustment for onshore wind"
cf_adj_t_filt_ofswind(i,v,t)       "--fraction-- capacity factor adjustment for offshore wind"
cost_cap_fin_mult_filt(i,r,t)      "--unitless-- capital cost financial multipliers"
cost_cap_filt(i,t)                 "--2017Rs/MW-- technology capital costs"
rsc_dat_filt(r,rs,i,rscbin,rscvar) "--varies-- resource supply curve data"
;

*populate year sets
tcheckret(t) = no ;
loop(t$[(yeart(t)>%cur_year%)$(yeart(t)<=%next_year%)],
tcheckret(t) = yes ;
) ;

tcheckretonswind(t) = no ;
loop(t$[(yeart(t)>=%start_year%)$(yeart(t)<=%next_year%)],
tcheckretonswind(t) = yes ;
) ;

tcheckretoffswind(t) = no ;
loop(t$[(yeart(t)>=%start_year%)$(yeart(t)<=%next_year%)],
tcheckretoffswind(t) = yes ;
) ;

tcur(t) = no ;
tcur("%cur_year%") = yes ;

tnext(t) = no ;
tnext("%next_year%") = yes ;

*populate reduced-form sets
valcap_iv(i,v) = sum{(r,t)$tcur(t), valcap(i,v,r,t)} ;
valcap_i(i) = sum{v, valcap_iv(i,v)} ;
valcap_ir(i,r) = sum{(v,t)$tcur(t), valcap(i,v,r,t)} ;
valcap_irt(i,r,t) = sum{v, valcap(i,v,r,t)} ;

*=======================================
* Removing banned technologies from sets
*=======================================

coal(i) = coal(i)$(not ban(i)) ;
hydro_d(i) = hydro_d(i)$(not ban(i)) ;
hydro_nd(i) = hydro_nd(i)$(not ban(i)) ;
nuclear(i) = nuclear(i)$(not ban(i)) ;
storage(i) = storage(i)$(not ban(i)) ;
storage_duration(i) = storage_duration(i)$(not ban(i)) ;
storage_eff(i) = storage_eff(i)$(not ban(i)) ;

*==============================
* Get ReEDS generation capacity
*==============================

* get the build year and retire year for all investments
* NOTE the variable CAP holds degraded capacity, so when we retire capacity we need to account for degredation
inv_tmp(i,v,r,t,tt)$[t.val+maxage(i)=tt.val] = [INV.l(i,v,r,t) + INVREFURB.l(i,v,r,t)] * degrade(i,t,tt) ;

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
retire_exog(i,v,r,"%cur_year%") = sum{tcheckret(tt)$(not (windons(i) or windofs(i))), retire_exog_tmp(i,v,r,tt)} ;

* determine the capacity that will retire due to age within the tcheckret set
* determine the lifetime retirements between the end of the last solve year and the end of the next solve year
* note that wind capacity will be handled seperately because the vintage is tied to the build year
ret_lifetime(i,v,r,"%cur_year%") = sum{(t,tt)$[tcheckret(tt)$(not (windons(i) or windofs(i)))], inv_tmp(i,v,r,t,tt)} ;

* get the installed capacity minus upcoming retirements for all technologies except wind
* For intertemporal or window solves: use the capacity from the PRIOR iteration of the CURRENT solve year for capacity credit for the NEXT iteration of the CURRENT solve year
cap_export(i,v,r) = sum{t$[tcur(t)$valcap(i,v,r,t)$(not (windons(i) or windofs(i)))], CAP.l(i,v,r,t)} ;

*cap_export can be less than zero if an exogenous retirement was taken early
cap_export(i,v,r)$[cap_export(i,v,r) < 0] = 0 ;

* grouping capacity by technologies
cap_pv(i,v,r) = cap_export(i,v,r)$pv(i) ;

cap_storage(i,v,r) = cap_export(i,v,r)$storage(i) ;

cap_thermal(i,v,r) = cap_export(i,v,r)$[not (pv(i) or storage(i) )] ;

* Wind capacity is treated separately because wind CFs depend on the build year as well as the vintage.
* It is the only technology where this information matters.

* determine the total exogenous retirements of wind capacity through the end of the next solve year
retire_exog_onswind(i,v,r,"%cur_year%")$onswind(i) = sum{tcheckretonswind(tt), retire_exog_tmp(i,v,r,tt)} ;
retire_exog_ofswind(i,v,r,"%cur_year%")$ofswind(i) = sum{tcheckretofswind(tt), retire_exog_tmp(i,v,r,tt)} ;


* determine the total lifetime retirements of wind capacity through the end of the next solve
ret_lifetime_onswind(i,v,r,"%cur_year%")$onswind(i) = sum{(t,tt)$tcheckretonswind(tt), inv_tmp(i,v,r,t,tt)} ;
ret_lifetime_ofswind(i,v,r,"%cur_year%")$ofswind(i) = sum{(t,tt)$tcheckretofswind(tt), inv_tmp(i,v,r,t,tt)} ;

* get the capacity of wind
cap_onswind(i,v,r) = sum{t$[tcur(t)$valcap(i,v,r,t)$onswind(i)], CAP.l(i,v,r,t)} ;
cap_ofswind(i,v,r) = sum{t$[tcur(t)$valcap(i,v,r,t)$ofswind(i)], CAP.l(i,v,r,t)} ;

* get wind capacity investements by build year
*cap_wind_inv(i,v,r,t)$[wind(i)$tcheckretwind(t)$(not tfirst(t))$valcap(i,v,r,t)] = INV.l(i,v,r,t) + INVREFURB.l(i,v,r,t) ;

* get the total wind capacity retirements throught the end of the next solve year
*cap_wind_ret(i,v,r)$wind(i) = sum{(t)$tcur(t), retire_exog_wind(i,v,r,t) + ret_lifetime_wind(i,v,r,t)} ;

*============================
* Filter necessary input data
*============================

heat_rate_filt(i,v,r) = sum{t$[valcap(i,v,r,t)$tcur(t)], heat_rate(i,v,r,t)} ;

cost_vom_filt(i,v,r) = sum{t$[tcur(t)$valgen(i,v,r,t)], cost_vom(i,v,r,t)} ;

fuel_price_filt(i,r) = sum{t$[valcap_irt(i,r,t)$tcur(t)], fuel_price(i,r,t)} ;

avail_filt(i,v,szn)$[(not vre(i))] = smax{h$h_szn(h,szn), avail(i,v,h)} ;

cf_hyd_filt(i,szn,r)$valcap_ir(i,r) = cf_adj_hyd(i,szn,r) ;

m_cf_filt(i,v,r,h,t) = m_cf(i,r,h)$[vre(i)$tnext(t)] ;

cf_adj_t(i,v,t) = 1;
cf_adj_t_filt_onswind(i,v,t) = cf_adj_t(i,v,t)$[tcheckretonswind(t)$onswind(i)] ;
cf_adj_t_filt_ofswind(i,v,t) = cf_adj_t(i,v,t)$[tcheckretofswind(t)$ofswind(i)] ;


cost_cap_fin_mult_filt(i,r,t) = cost_cap_fin_mult(i,r,t)$[storage(i)$tnext(t)] ;

cost_cap_filt(i,t) = cost_cap(i,t)$[storage(i)$tnext(t)] ;

rsc_dat_filt(r,rs,i,rscbin,"cost") = rsc_dat(r,rs,i,rscbin,"cost")$[rfeas(r)$storage(i)] ;

*============================
* Get ReEDS transmission data
*============================

cap_trans(r,rr,trtype)$[rfeas(r)$rfeas(rr)] = sum{t$tcur(t), CAPTRAN.l(r,rr,trtype,t)} ;

losses_trans_h(rr,r,h,trtype)$[rfeas(r)$rfeas(rr)] = sum{t$tcur(t), tranloss(rr,r) * FLOW.l(rr,r,h,t,trtype)} ;

routes_filt(r,rr)$[rfeas(r)$rfeas(rr)] = sum{(trtype,t)$tcur(t), routes(r,rr,trtype,t)} ;

*=======================================
* Unload all relevant data to a gdx file
*=======================================
$log 'exec unload'
$log '%data_dir%%ds%reeds_data_%case%_%next_year%.gdx'
execute_unload '%data_dir%%ds%reeds_data_%case%_%next_year%.gdx' avail_filt, cap_pv, cap_storage, cap_thermal, cap_trans, cap_onswind, cap_ofswind, cf_hyd_filt,
                                                         coal, cost_vom_filt, fuel_price_filt, h_szn, heat_rate_filt, cost_cap_fin_mult_filt, cost_cap_filt, rsc_dat_filt,
                                                         hierarchy, hours, hydmin, hydro_d, hydro_nd, i, losses_trans_h, m_cf_filt, nuclear, r, r_region, r_rs,
                                                         rfeas, routes_filt, sdbin, storage, storage_duration, storage_eff, szn, tranloss, v, cf_adj_t_filt_onswind, cf_adj_t_filt_ofswind, pvf_onm, pvf_capital, sw_sasia_trade, sw_txlimit;

*execute_unload 'D_Augur%ds%dump.gdx';