$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix


* globals needed for this file:
* case : name of case you're running
* cur_year : current year

*remove any load years
tload(t) = no ;

$log 'Solving sequential case for...'
$log '  Case: %case%'
$log '  Year: %cur_year%'

*load in results from the cc/curtailment scripts
$ifthene.tcheck %cur_year%>%GSw_SkipAugurYear%

*indicate we're loading data
tload("%cur_year%") = yes ;

*file written by ReEDS_Augur.py
* loaddcr = domain check (dc) + overwrite values storage previously (r)
$gdxin ReEDS_Augur%ds%augur_data%ds%ReEDS_Augur_%cur_year%.gdx
$loaddcr curt_old_load = curt_old
$loaddcr curt_mingen_load = curt_mingen
$loaddcr curt_marg_load = curt_marg
$loaddcr cc_old_load = cc_old
$loaddcr cc_mar_load = cc_mar
$loaddcr cc_dr_load = cc_dr
$loaddcr sdbin_size_load = sdbin_size
$loaddcr curt_stor_load = curt_stor
$loadr curt_dr_load = curt_dr
$loaddcr curt_tran_load = curt_tran
$loaddcr storage_in_min_load = storage_in_min
$loaddcr hourly_arbitrage_value_load = hourly_arbitrage_value
$loaddcr net_load_adj_no_curt_h_load = net_load_adj_no_curt_h
$loaddcr storage_starting_soc_load = storage_starting_soc
$loaddcr cap_fraction_load = ret_frac
$loaddcr curt_prod_load = curt_prod
$gdxin

*Note: these values are rounded before they are written to the gdx file, so no need to round them here
cap_fraction(i,v,r,t)$tload(t) = cap_fraction_load(i,v,r,t) ;
curt_old(r,h,t)$tload(t) = curt_old_load(r,h,t) ;
curt_mingen(r,h,t)$tload(t) = curt_mingen_load(r,h,t) ;
curt_marg(i,r,h,t)$tload(t) = curt_marg_load(i,r,h,t) ;

cc_old(i,rb,szn,t)$[tload(t)$(vre(i) or csp_storage(i) or pvb(i))] = sum{ccreg$r_ccreg(rb,ccreg), cc_old_load(i,rb,ccreg,szn,t) } ;
m_cc_mar(i,rb,szn,t)$[tload(t)$(vre(i) or csp_storage(i) or pvb(i))] = sum{ccreg$r_ccreg(rb,ccreg), cc_mar_load(i,rb,ccreg,szn,t) } ;

cc_old(i,rs,szn,t)$[tload(t)$(vre(i) or csp_storage(i) or pvb(i))] = sum{ccreg$rs_ccreg(rs,ccreg), cc_old_load(i,rs,ccreg,szn,t) } ;
m_cc_mar(i,rs,szn,t)$[tload(t)$(vre(i) or csp_storage(i) or pvb(i))] = sum{ccreg$rs_ccreg(rs,ccreg), cc_mar_load(i,rs,ccreg,szn,t) } ;

m_cc_dr(i,r,szn,t)$[tload(t)$dr(i)] = cc_dr_load(i,r,szn,t) ;

sdbin_size(ccreg,szn,sdbin,t)$tload(t) = sdbin_size_load(ccreg,szn,sdbin,t) ;
curt_stor(i,v,r,h,src,t)$[tload(t)$valcap(i,v,r,t)$(storage_standalone(i) or pvb(i))] = curt_stor_load(i,v,r,h,src,t) ;
curt_dr(i,v,r,h,src,t)$[tload(t)$valcap(i,v,r,t)$dr1(i)] = curt_dr_load(i,v,r,h,src,t) ;
curt_tran(r,rr,h,t)$[tload(t)$rfeas(r)$rfeas(rr)$rb(r)$rb(rr)$(not sameas(r,rr))
                     $sum{(n,nn,trtype)$routes_inv(n,nn,trtype,t), translinkage(r,rr,n,nn,trtype)}
                    ] = curt_tran_load(r,rr,h,t) ;

storage_in_min(r,h,t)$[tload(t)$sum{(i,v)$storage_standalone(i), valcap(i,v,r,t)}] = storage_in_min_load(r,h,t) ;
* Ensure storage_in_min doesn't exceed max input capacity when input capacity < generation capacity
* and when storage_duration_m < storage_duration. Multiple terms are necessary to allow for alternative
* swich settings and cases when input capacity > generation capacity and/or storage_duration_m > storage_duration
* TODO: Pass plant-specific input capacity and duration to Augur and use there
storage_in_min(r,h,t)$storage_in_min(r,h,t) =
    min(storage_in_min(r,h,t),
* scaling by plant-specific pump capacity and storage duration
        sum{(i,v) , ( (storage_duration_m(i,v,r) / storage_duration(i))$storage_duration(i) + 1$(not storage_duration(i)) )
                    * avail(i,v,h) * sum{rr$cap_agg(r,rr), storinmaxfrac(i,v,rr) * sum{tt$tprev(t,tt), CAP.l(i,v,rr,tt)} } } ,
* scaling by plant-specific storage duration
        sum{(i,v) , ( (storage_duration_m(i,v,r) / storage_duration(i))$storage_duration(i) + 1$(not storage_duration(i)) )
                    * avail(i,v,h) * sum{(rr,tt)$[tprev(t,tt)$cap_agg(r,rr)], CAP.l(i,v,rr,tt)} } ,
* scaling by plant-specific pump capacity
        sum{(i,v) , avail(i,v,h) * sum{rr$cap_agg(r,rr), storinmaxfrac(i,v,rr) * sum{tt$tprev(t,tt), CAP.l(i,v,rr,tt)} } }
    ) ;
hourly_arbitrage_value(i,r,t)$[tload(t)$valcap_irt(i,r,t)$(storage_standalone(i) or hyd_add_pump(i) or pvb(i))] = hourly_arbitrage_value_load(i,r,t) ;
net_load_adj_no_curt_h(r,h,t)$[rfeas(r)$tload(t)] = net_load_adj_no_curt_h_load(r,h,t) ;

storage_soc_exog(i,v,r,h,t)$[storage(i)$Sw_Hourly$(not Sw_HourlyWrap)
                            $starting_hour(r,h)$tload(t)$valcap(i,v,r,t)] = 
                    storage_starting_soc_load(i,v,r,h,t) ;

*Upgrades - used for hydropower upgraded to add pumping
curt_stor(i,v,r,h,src,t)$[tload(t)$upgrade(i)$storage_standalone(i)$valcap(i,v,r,t)] = 
        smax(vv, sum{ii$upgrade_to(i,ii), curt_stor(ii,vv,r,h,src,t) } ) ;
hourly_arbitrage_value(i,r,t)$[tload(t)$upgrade(i)$(storage_standalone(i) or hyd_add_pump(i))$valcap_irt(i,r,t)] = 
        sum{ii$upgrade_to(i,ii), hourly_arbitrage_value(ii,r,t) } ;

* --- Assign hybrid PV+battery capacity credit derate factor ---
hybrid_cc_derate(i,r,szn,sdbin,t)$[tload(t)$valcap_irt(i,r,t)$storage_hybrid(i)] = 1 ;

$ontext
Limit the capacity credit of hybrid PV such that the total capacity credit from the PV and the battery do not exceed the inverter limit.
  Example: PV = 130 MWdc, Battery = 65MW, Inverter = 100 MW (PVdc/Battery=0.5; PVdc/INVac=1.3)
  Assuming the capacity credit of the Battery is 65MW, then capacity credit of the PV is limited to 35MW or 0.269 (35MW/130MW) on a relative basis.
  Max capacity credit PV [MWac/MWdc] = (Inverter - Battery capcity credit) / PV_dc
                                     = (P_dc / ILR - P_dc * BCR) / PV_dc
                                     = 1/ILR - BCR
$offtext
* marginal capacity credit
m_cc_mar(i,r,szn,t)$[tload(t)$pvb(i)] = min{ m_cc_mar(i,r,szn,t), 1 / ilr(i) - bcr(i) } ;

* old capacity credit
* (1) convert cc_old from MW to a fractional basis, (2) adjust the fractional value to be less than 1/ILR - BCR, (3) multiply by CAP to convert back to MW
cc_old(i,r,szn,t)$[tload(t)$pvb(i)$sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)}] = min{ cc_old(i,r,szn,t) / sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)}, 1 / ilr(i) - bcr(i) } * sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)};

* --- Assign hybrid PV+battery curtailment ---
* THIS IS RELATED TO WATER COOLING AND WILL BE FIXED IN PART 2 OF THE PULL REQUEST
*Parameter
*    CSPExist(i,r)
*    CSPDenom(i,r)
*    CSPFrac(i,r)
*;
* Initialize to zero out values from prior years
*CSPExist(i,r)=0 ;
*CSPDenom(i,r)=0 ;
*CSPFrac(i,r)=0 ;
* Re-map capacity caluculations for CSP with storage if water technlogies are active
*if(Sw_WaterMain = 1,
* Update existing CSP for retirements
*CSPExist(i,r)=sum{(tt,v)$[sum{t$(t.val=%cur_year%), tprev(t,tt) }$valcap(i,v,r,tt)$csp(i)], CAP.l(i,v,r,tt)- retire_exog(i,v,r,tt) - ret_lifetime(i,v,r,tt) } ;
* Sum to find total CSP capacity of each numeraire CSP technology (non-ctt_wst differentiated)
*CSPDenom(i,r)$[i_numeraire(i)] = sum{ii$ctt_i_ii(ii,i), CSPExist(ii,r) } ;
* Calculate ratio of ctt_wst differentiated CSP of each numeraire tech
*CSPFrac(i,r)$[CSPExist(i,r)$sum{ii$ctt_i_ii(i,ii), CSPDenom(ii,r) }] = CSPExist(i,r) / sum{ii$ctt_i_ii(i,ii), CSPDenom(ii,r) } ;
* Allocate cc_old based on ratio
*cc_old(i,r,szn,t)$[tload(t)$(csp(i)$i_water_cooling(i)$Sw_WaterMain)]=sum{ii$ctt_i_ii(i,ii),cc_old(ii,r,szn,t)}*CSPFrac(i,r) ;
* Remove cc_old for numeraire CSP techs to prevent double-counting
*cc_old(i,r,szn,t)$[csp(i)$(not i_water_cooling(i))]=0 ;
* Map marginal CSP CC to wst_ctt CSP techs
*m_cc_mar(i,r,szn,t)$[tload(t)$(csp(i)$i_water_cooling(i)$Sw_WaterMain)]=sum{ii$ctt_i_ii(i,ii),m_cc_mar(ii,r,szn,t) } ;
*) ;

*curt_int is only used in the intertemporal solve, so ensure it is set to zero
curt_int(i,r,h,t) = 0 ;

curt_prod(r,h,t)$[rfeas(r)$tload(t)] = min{1 , curt_prod_load(r,h,t) } ;
        
*getting mingen level after accounting for retirements
mingen_postret(r,szn,t)$[sum{tt$tprev(t,tt), MINGEN.l(r,szn,tt) }$tload(t)] = 
                  sum{tt$tprev(t,tt), MINGEN.l(r,szn,tt) }
                  - sum{(i,v)$[sum{tt$tprev(t,tt), valgen(i,v,r,tt) }], cap_fraction(i,v,r,t) 
                  * smax{h$h_szn(h,szn), sum{tt$tprev(t,tt), GEN.l(i,v,r,h,tt) }  * minloadfrac(r,i,h) } } ;

* Replacing h3 with h17 values - this was originally done in Augur to simplify hardcoding 
* note this depends on Sw_Flex given that we only want to replace these values with
* the default, h17 temporal resolution and not representative days/weeks/...
if(Sw_Hourly = 0,
 curt_marg(i,r,"h17",t)$[curt_marg(i,r,"h3",t)$tload(t)$rfeas_cap(r)] = curt_marg(i,r,"h3",t) ;
 curt_mingen(r,"h17",t)$[curt_mingen(r,"h3",t)$tload(t)$rfeas_cap(r)] = curt_mingen(r,"h3",t) ;
 curt_old(r,"h17",t)$[curt_old(r,"h3",t)$tload(t)$rfeas_cap(r)] = curt_old(r,"h3",t) ;
 curt_prod(r,"h17",t)$[rfeas(r)$tload(t)] = curt_prod(r,"h3",t) ;
 curt_stor(i,v,r,"h17",src,t)$[curt_stor(i,v,r,"h3",src,t)$tload(t)$rfeas_cap(r)] = curt_stor(i,v,r,"h3",src,t) ;
 curt_tran(r,rr,"h17",t)$[curt_tran(r,rr,"h3",t)$tload(t)$rfeas_cap(r)] = curt_tran(r,rr,"h3",t) ;
 net_load_adj_no_curt_h(r,"h17",t)$[tload(t)] = net_load_adj_no_curt_h(r,"h3",t) ;
 storage_in_min(r,"h17",t)$[storage_in_min(r,"h3",t)$tload(t)$rfeas_cap(r)] = storage_in_min(r,"h3",t) ;
) ;

$endif.tcheck

* --- Estimate curtailment from "old" hybrid PV+battery ---

$ifthene %cur_year%==2010
*initialize CAP.l for 2010 because it has not been defined yet
CAP.l(i,v,r,"2010")$[m_capacity_exog(i,v,r,"2010")] = m_capacity_exog(i,v,r,"2010") ;
$endif

* estimate vre generation potential (capacity factor * available capacity) from previous model year
vre_gen_old(i,r,h,t)$[(vre(i) or pvb(i))$(sum{tt$tload(tt), tprev(tt,t) })$valcap_irt(i,r,t)] =
    sum{(v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)$rfeas_cap(rr)],
         m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,t) * hours(h) }
;

* estimate "old" curtailment from hybrid PV+battery based share of generation potential
curt_old_pvb(r,h,t)$[curt_old(r,h,t)$(sum{i$[vre(i) or pvb(i)], vre_gen_old(i,r,h,t)})] =
  curt_old(r,h,t) * sum{i$pvb(i), vre_gen_old(i,r,h,t)} / sum{i$[vre(i) or pvb(i)], vre_gen_old(i,r,h,t)} ;

* estimate curtailment from hybrid PV+battery for previous model year ("lastyear")
curt_old_pvb_lastyear(r,h) = sum{tt$tprev('%cur_year%',tt), curt_old_pvb(r,h,tt)} ;

* --- reset tmodel ---

tmodel(t) = no ;
tmodel("%cur_year%") = yes ;


* --- report data immediately before the solve statement---

*execute_unload "data_%cur_year%.gdx" ;

* ------------------------------
* Solve the Model
* ------------------------------

tmodel(t) = no ;
tmodel("%cur_year%") = yes ;
solve ReEDSmodel minimizing z using lp ;

*record objective function values right after solve
z_rep(t)$tmodel(t) = Z.l ;
z_rep_inv(t)$tmodel(t) = Z_inv.l(t) ;
z_rep_op(t)$tmodel(t) = Z_op.l(t) ;

*add the just-solved year to tfix and fix variables for next solve year
tfix("%cur_year%") = yes ;
$include d2_varfix.gms

*dump data to be used by Augur
$include d3_augur_data_dump.gms
