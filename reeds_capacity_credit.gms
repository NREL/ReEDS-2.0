$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

set tcheck(t) "set of all years to check for retiring capacity"
  /
  %cur_year%*%next_year%
  /
;

tcheck("%cur_year%") = no ;


* get the retire year for all vre and storage investments
* NOTE the variable CAP holds degraded capacity, so when we retire capacity we need to account for degredation
parameter inv_tmp(i,r,t,tt) "--MW-- relevant capacities along with their build year and retire year" ;
inv_tmp(i,r,t,tt)$[(t.val+maxage(i)=tt.val)$(vre(i) or storage(i))] = sum{v, INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) } * degrade(i,t,tt)
;

* calculate exogenous retirements based on the change in exogenous capacity
parameter retire_exog_init(i,v,r,rs,t) "--MW-- exogenous retired capacity" ;
retire_exog_init(i,v,r,rs,t)$[(capacity_exog(i,v,r,rs,t-1) > capacity_exog(i,v,r,rs,t))$(vre(i) or storage(i))] =
        [capacity_exog(i,v,r,rs,t-1) - capacity_exog(i,v,r,rs,t)]$initv(v)
;

* ignore vintage classes that are not "initial"
retire_exog_init(i,v,r,rs,t)$[not initv(v)] = 0 ;
* fix the r & rs indices for exogenous retirements
parameter retire_exog_tmp(i,v,r,t) "--MW-- exogenous retired capacity" ;
retire_exog_tmp(i,v,rb,t) = retire_exog_init(i,v,rb,"sk",t) ;
retire_exog_tmp(i,v,rs,t)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs), retire_exog_init(i,v,r,rs,t)} ;

* sum over "initial" classes
parameter retire_exog(i,r,t) "--MW-- exogenous retired capacity" ;
retire_exog(i,r,"%cur_year%") = sum{[initv(v),tcheck(tt)], retire_exog_tmp(i,v,r,tt) }
;
* determine the lifetime retirements between the end of the last solve and the end of the next solve
parameter ret_lifetime(i,r,t) "--MW-- capacity that will be retired before the end of the next solve year due to its age" ;
ret_lifetime(i,r,"%cur_year%") = sum{(t,tt)$tcheck(tt), inv_tmp(i,r,t,tt)}

* get the capacity of vre and storage
parameter cap_export(i,r,t) "--MW-- relavent capacities for capacity credit calculations" ;
$ifthen %timetype% == seq
* For a sequential solve: use capacity for the NEXT solve year when calculating capacity credit for the NEXT solve year
cap_export(i,r,t)$[(vre(i) or storage(i))$valcap_irt(i,r,t)$(t.val=%cur_year%)] = sum{v$valcap(i,v,r,t), CAP.l(i,v,r,t) } - retire_exog(i,r,t) - ret_lifetime(i,r,t) ;
* Sometimes removing exogenous retirements without adding prescribed builds results in negative capacities
cap_export("distpv",r,"%cur_year%") = 0 ;
cap_export("distpv",r,"%cur_year%") = sum{v, CAP.l("distpv",v,r,"%cur_year%")} ;
$else
* For intertemporal or window solves: use the capacity from the PRIOR iteration of the CURRENT solve year for capacity credit for the NEXT iteration of the CURRENT solve year
cap_export(i,r,t)$[(vre(i) or storage(i))$valcap_irt(i,r,t)$(t.val=%cur_year%)] = sum{v$valcap(i,v,r,t), CAP.l(i,v,r,t) }
$endif
;

execute_unload 'outputs%ds%variabilityFiles%ds%cc_in_%case%_%next_year%.gdx' cap_export, csp_sm, hierarchy, load_multiplier, r_rs, rfeas,
                                                                             storage_duration, storage_eff, windcfin ;

execute 'python ReEDS_capacity_credit.py "outputs%ds%variabilityFiles%ds%cc_in_%case%_%next_year%.gdx" "outputs%ds%variabilityFiles%ds%cc_out_%case%_%next_year%.gdx" "%case%" "%cur_year%" "%next_year%" "%calc_csp_cc%"'
