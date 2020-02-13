*==========================
* --- Global sets ---
*==========================

*Setting the default slash
$setglobal ds \
$setglobal copycom copy

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$setglobal copycom cp
$endif.unix


parameter cap_export "relavent capacities to export to CC_py"; 
cap_export(i,r,t)$[(upv(i) or dupv(i) or wind(i) or storage(i))$(t.val=%cur_year%)] = sum(c,cap.l(i,c,r,t));

parameter NetImportsBA "transmission (MW) to be sent to CC_py";
NetImportsBA(r,h,t)$[rfeas(r) and t.val=%cur_year%] =
sum{(rr,trtype)$[rfeas(rr) and routes(rr,r,trtype,t)],
      (1-tranloss(rr,r)) * FLOW.l(rr,r,h,t,trtype)
    - FLOW.l(r,rr,h,t,trtype)
}
;

*Create the directory for the CC_py input and output files
*This is throwing errors on HPC, commenting out for now
$if NOT dexist %ds%E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles $call 'mkdir E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles'

execute_unload 'E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%CC_py_inputs_%case%_%next_year%.gdx' cap_export, NetImportsBA, 
									wind, upv, dupv, storage, vre, storage_eff, storage_duration, hours, h_szn, rfeas, r_region, distloss, r_rs;

execute 'python D_8760%ds%d4_CC_py.py "E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%CC_py_inputs_%case%_%next_year%.gdx" "E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%cc_out_%case%_%next_year%.gdx" "%case%" "%cur_year%" "%next_year%" >> "E_Outputs%ds%runs%ds%%case%%ds%8760log.txt"'