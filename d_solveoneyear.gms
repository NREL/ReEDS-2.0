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

*file written by ReEDS_Augur.py
$gdxin ReEDS_Augur%ds%augur_data%ds%ReEDS_augur_%case%_%cur_year%.gdx
$loadr curt_old_load = curt_old
$loadr curt_mingen_load = curt_mingen
$loadr curt_marg_load = curt_marg
$loadr cc_old_load = cc_old
$loadr cc_mar_load = cc_mar
$loadr sdbin_size_load = sdbin_size
$loadr curt_stor_load = curt_stor
$loadr curt_tran_load = curt_tran
$loadr curt_reduct_tran_max_load = curt_reduct_tran_max
$loadr storage_in_min_load = storage_in_min
$loadr hourly_arbitrage_value_load = hourly_arbitrage_value
$gdxin

*Note: these values are rounded before they are written to the gdx file, so no need to round them here
curt_old(r,h,t)$tload(t) = curt_old_load(r,h,t) ;
curt_mingen(r,h,t)$tload(t) = curt_mingen_load(r,h,t) ;
curt_marg(i,r,h,t)$tload(t) = curt_marg_load(i,r,h,t) ;
cc_old(i,r,szn,t)$[tload(t)$(vre(i) or csp_storage(i))] = cc_old_load(i,r,szn,t) ;
m_cc_mar(i,r,szn,t)$[tload(t)$(vre(i) or csp_storage(i))] = cc_mar_load(i,r,szn,t) ;
sdbin_size(ccreg,szn,sdbin,t)$tload(t) = sdbin_size_load(ccreg,szn,sdbin,t) ;
curt_stor(i,v,r,h,src,t)$[tload(t)$valcap(i,v,r,t)$storage_no_csp(i)] = curt_stor_load(i,v,r,h,src,t) ;
curt_tran(r,rr,h,t)$[tload(t)$(sum{trtype, routes(r,rr,trtype,t) } or sum{trtype, routes(rr,r,trtype,t) })] = curt_tran_load(r,rr,h,t) ;
curt_reduct_tran_max(r,rr,h,t)$[tload(t)$(sum{trtype, routes(r,rr,trtype,t) } or sum{trtype, routes(rr,r,trtype,t) })] = curt_reduct_tran_max_load(r,rr,h,t) ;
storage_in_min(r,h,t)$[tload(t)$sum{(i,v)$storage_no_csp(i),valcap(i,v,r,t)}] = storage_in_min_load(r,h,t) ;
hourly_arbitrage_value(i,r,t)$[tload(t)$sum{v, valcap(i,v,r,t) }$storage_no_csp(i)] = hourly_arbitrage_value_load(i,r,t) ;

*curt_int is only used in the intertemporal solve, so ensure it is set to zero
curt_int(i,r,h,t) = 0 ;

$endif.tcheck


tmodel(t) = no ;
tmodel("%cur_year%") = yes ;
solve %case% minimizing z using lp ;
tfix("%cur_year%") = yes ;
$include d2_varfix.gms
$include d3_augur_data_dump.gms

*getting mingen level after accounting for retirements
*this is included after the solve statement because retire_exog is in d3_augur_data_dump
cap_fraction(i,v,r,t)$[valcap(i,v,r,t)$sum{tt$tprev(t,tt), CAP.l(i,v,r,tt) }$tload(t)$sum{h, minloadfrac(r,i,h) }] = (retire_exog(i,v,r,t) + ret_lifetime(i,v,r,t)) / sum{tt$tprev(t,tt), CAP.l(i,v,r,tt) } ;
mingen_postret(r,szn,t)$[sum{tt$tprev(t,tt), MINGEN.l(r,szn,tt) }$tload(t)] = sum{tt$tprev(t,tt), MINGEN.l(r,szn,tt) }
                                          - sum{(i,v)$[sum{tt$tprev(t,tt), valgen(i,v,r,tt) }], cap_fraction(i,v,r,t) * smax{h$h_szn(h,szn), sum{tt$tprev(t,tt), GEN.l(i,v,r,h,tt) }  * minloadfrac(r,i,h) } } ;
