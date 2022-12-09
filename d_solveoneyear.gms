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

* need to have values initialized before making adjustments
* thus cannot perform m_rsc_dat adjustments until 2010 has solved
$ifthene.rsccheck %cur_year%>2010
* adjust the m_rsc_dat capacity upward to avoid infeasibilities
* these are caused by floating point differences that occur in GAMS
* which will report the model as infeasible before sending to CPLEX
* whereas CPLEX will still attempt to solve the model if the infeasibilities
* are less than the eprhs option specified in cplex.opt (default 1e-6)
m_rsc_dat(r,i,rscbin,"cap")$[m_rsc_dat(r,i,rscbin,"cap")] =
    max(m_rsc_dat(r,i,rscbin,"cap"),
        sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) <= yeart("%cur_year%"))$rsc_agg(i,ii)],
            INV_RSC.l(ii,v,r,rscbin,tt) * resourcescaler(ii) }
    ) ;

$endif.rsccheck


*load in results from the cc/curtailment scripts
$ifthene.tcheck %cur_year%>%GSw_SkipAugurYear%

*indicate we're loading data
tload("%cur_year%") = yes ;

*file written by ReEDS_Augur.py
* loaddcr = domain check (dc) + overwrite values storage previously (r)
$gdxin ReEDS_Augur%ds%augur_data%ds%ReEDS_Augur_%prev_year%.gdx
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
curt_old(r,h,t)$[tload(t)$Sw_AugurCurtailment] = curt_old_load(r,h,t) ;
curt_mingen(r,h,t)$[tload(t)$Sw_AugurCurtailment] = curt_mingen_load(r,h,t) ;
curt_marg(i,r,h,t)$[tload(t)$Sw_AugurCurtailment] = curt_marg_load(i,r,h,t) ;

cc_old(i,rb,szn,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] = sum{ccreg$r_ccreg(rb,ccreg), cc_old_load(i,rb,ccreg,szn,t) } ;
m_cc_mar(i,rb,szn,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] = sum{ccreg$r_ccreg(rb,ccreg), cc_mar_load(i,rb,ccreg,szn,t) } ;

cc_old(i,rs,szn,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] = sum{ccreg$rs_ccreg(rs,ccreg), cc_old_load(i,rs,ccreg,szn,t) } ;
m_cc_mar(i,rs,szn,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] = sum{ccreg$rs_ccreg(rs,ccreg), cc_mar_load(i,rs,ccreg,szn,t) } ;

m_cc_dr(i,r,szn,t)$[tload(t)$dr(i)] = cc_dr_load(i,r,szn,t) ;

sdbin_size(ccreg,szn,sdbin,t)$tload(t) = sdbin_size_load(ccreg,szn,sdbin,t) ;

curt_stor(i,v,r,h,src,t)$[tload(t)$Sw_AugurCurtailment$valcap(i,v,r,t)$(storage_standalone(i) or pvb(i))] = curt_stor_load(i,v,r,h,src,t) ;
curt_dr(i,v,r,h,src,t)$[tload(t)$Sw_AugurCurtailment$valcap(i,v,r,t)$dr1(i)] = curt_dr_load(i,v,r,h,src,t) ;
curt_tran(r,rr,h,t)$[tload(t)$Sw_AugurCurtailment$rfeas(r)$rfeas(rr)$rb(r)$rb(rr)$(not sameas(r,rr))
                     $sum{(n,nn,trtype)$routes_inv(n,nn,trtype,t), translinkage(r,rr,n,nn,trtype)}
                    ] = curt_tran_load(r,rr,h,t) ;

storage_in_min(r,h,t)$[tload(t)$Sw_AugurCurtailment$sum{(i,v)$storage_standalone(i), valcap(i,v,r,t)}] = storage_in_min_load(r,h,t) ;
* Ensure storage_in_min doesn't exceed max input capacity when input capacity < generation capacity
* and when storage_duration_m < storage_duration. Multiple terms are necessary to allow for alternative
* swich settings and cases when input capacity > generation capacity and/or storage_duration_m > storage_duration
* TODO: Pass plant-specific input capacity and duration to Augur and use there
storage_in_min(r,h,t)$storage_in_min(r,h,t) =
    min(storage_in_min(r,h,t),
* scaling by plant-specific pump capacity and storage duration
        sum{(i,v) , ( (storage_duration_m(i,v,r) / storage_duration(i))$storage_duration(i) + 1$(not storage_duration(i)) )
                    * avail(i,h) * sum{rr$cap_agg(r,rr), storinmaxfrac(i,v,rr) * sum{tt$tprev(t,tt), CAP.l(i,v,rr,tt)} } } ,
* scaling by plant-specific storage duration
        sum{(i,v) , ( (storage_duration_m(i,v,r) / storage_duration(i))$storage_duration(i) + 1$(not storage_duration(i)) )
                    * avail(i,h) * sum{(rr,tt)$[tprev(t,tt)$cap_agg(r,rr)], CAP.l(i,v,rr,tt)} } ,
* scaling by plant-specific pump capacity
        sum{(i,v) , avail(i,h) * sum{rr$cap_agg(r,rr), storinmaxfrac(i,v,rr) * sum{tt$tprev(t,tt), CAP.l(i,v,rr,tt)} } }
    ) ;
hourly_arbitrage_value(i,r,t)$[tload(t)$valcap_irt(i,r,t)$(storage_standalone(i) or hyd_add_pump(i) or pvb(i))] = hourly_arbitrage_value_load(i,r,t) ;
net_load_adj_no_curt_h(r,h,t)$[rfeas(r)$tload(t)$Sw_AugurCurtailment] = net_load_adj_no_curt_h_load(r,h,t) ;

storage_soc_exog(i,v,r,h,t)$[storage(i)$Sw_Hourly$(not Sw_HourlyWrap)
                            $starting_hour(h)$tload(t)$valcap(i,v,r,t)] =
                    storage_starting_soc_load(i,v,r,h,t) ;

*Upgrades - used for hydropower upgraded to add pumping
curt_stor(i,v,r,h,src,t)$[tload(t)$Sw_AugurCurtailment$upgrade(i)$storage_standalone(i)$valcap(i,v,r,t)] =
        smax(vv, sum{ii$upgrade_to(i,ii), curt_stor(ii,vv,r,h,src,t) } ) ;
hourly_arbitrage_value(i,r,t)$[tload(t)$upgrade(i)$(storage_standalone(i) or hyd_add_pump(i))$valcap_irt(i,r,t)] =
        sum{ii$upgrade_to(i,ii), hourly_arbitrage_value(ii,r,t) } ;

* --- Assign hybrid PV+battery capacity credit ---
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
*curt_int is only used in the intertemporal solve, so ensure it is set to zero
curt_int(i,r,h,t) = 0 ;

curt_prod(r,h,t)$[rfeas(r)$tload(t)$Sw_AugurCurtailment] = min{1 , curt_prod_load(r,h,t) } ;

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

* --- Ingest tax credit phaseout mult --- *

$gdxin outputs%ds%tc_phaseout_data%ds%tc_phaseout_mult_%cur_year%.gdx
$loaddcr tc_phaseout_mult_t_load = tc_phaseout_mult_t
$gdxin

tc_phaseout_mult_t(i,t)$tload(t) = tc_phaseout_mult_t_load(i,t) ;

*if tcphaseout is enabled, overwrite initialization
*this requires re-calculating cost_cap_fin_mult and its various permutations
if(Sw_TCPhaseout > 0,
* apply the phaseout multiplier of the current level for current year
* and all future builds. Note that the value will remain the same for
* the cur_year-available vintage but can be updated for vintages whose
* first year hasn't solved yet. i.e. tc_phaseout_mult will remain constant for all
* current and historically-buildable plants but future plants may get updated.
tc_phaseout_mult(i,v,t)$[tload(t)$(firstyear_v(i,v)>=%cur_year%)] = 
    tc_phaseout_mult_t(i,t) ;
);

* --- Start calculations of cost_cap_fin_mult family of parameters --- *
* These are calculated here because the ITC phaseout can influence these parameters,
* and the timing of the phaseout is not known beforehand.
cost_cap_fin_mult(i,r,t) = ccmult(i,t) / (1.0 - tax_rate(t)) 
    * (1.0-tax_rate(t) * (1.0 - (itc_frac_monetized(i,t) * tc_phaseout_mult_t(i,t)/2.0) )
    * pv_frac_of_depreciation(i,t) - itc_frac_monetized(i,t) * tc_phaseout_mult_t(i,t))
    * degradation_adj(i,t) * financing_risk_mult(i,t) * reg_cap_cost_mult(i,r) 
    * eval_period_adj_mult(i,t) * (1.0+supply_chain_adj(t)) ;

cost_cap_fin_mult_noITC(i,r,t) = ccmult(i,t) / (1.0 - tax_rate(t)) 
    * (1.0-tax_rate(t)*pv_frac_of_depreciation(i,t)) * degradation_adj(i,t) 
    * financing_risk_mult(i,t) * reg_cap_cost_mult(i,r) * eval_period_adj_mult(i,t) 
    * (1.0+supply_chain_adj(t) );

cost_cap_fin_mult_no_credits(i,r,t) = ccmult(i,t) * reg_cap_cost_mult(i,r) * (1.0+supply_chain_adj(t)) ;

* Assign the PV portion of PVB the value of UPV
cost_cap_fin_mult_pvb_p(i,r,t)$pvb(i) = sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult(ii,r,t) } ;
cost_cap_fin_mult_pvb_p_noITC(i,r,t)$pvb(i) = sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult_noITC(ii,r,t) } ;
cost_cap_fin_mult_pvb_p_no_credits(i,r,t)$pvb(i) = sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult_no_credits(ii,r,t) } ;

* In the financing module (python), PVB refers to the battery portion of the hybrid.
* This convention is used to estimate the ITC benefit for the battery.
* Assign the battery portion of PVB the value computed in the financing module for PVB
cost_cap_fin_mult_pvb_b(i,r,t)$pvb(i) = cost_cap_fin_mult(i,r,t) ;
cost_cap_fin_mult_pvb_b_noITC(i,r,t)$pvb(i) = cost_cap_fin_mult_noITC(i,r,t) ;
cost_cap_fin_mult_pvb_b_no_credits(i,r,t)$pvb(i) = cost_cap_fin_mult_no_credits(i,r,t) ;

* Assign "cost_cap_fin_mult" for PVB to be the weighted average of the PV and battery portions
* The weighting is based on:
*   (1) the cost of each portion: PV=cost_cap_pvb_p; Battery=cost_cap_pvb_b
*   (2) the relative size of each portion: PV=1; Battery=bcr
* The "-1" and "+1" values are needed because the multipliers are adjustments off of 1.0
cost_cap_fin_mult(i,r,t)$pvb(i) = ((cost_cap_fin_mult_pvb_p(i,r,t) - 1) * cost_cap_pvb_p(i,t)
                                   + bcr(i) * (cost_cap_fin_mult_pvb_b(i,r,t) - 1) * cost_cap_pvb_b(i,t))
                                   / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_noITC(i,r,t)$pvb(i) = ((cost_cap_fin_mult_pvb_p_noITC(i,r,t) - 1) * cost_cap_pvb_p(i,t)
                                        + bcr(i) * (cost_cap_fin_mult_pvb_b_noITC(i,r,t) - 1) * cost_cap_pvb_b(i,t))
                                        / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_no_credits(i,r,t)$pvb(i) = ((cost_cap_fin_mult_pvb_p_no_credits(i,r,t) - 1) * cost_cap_pvb_p(i,t)
                                             + bcr(i) * (cost_cap_fin_mult_pvb_b_no_credits(i,r,t) - 1) * cost_cap_pvb_b(i,t))
                                             / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_noITC(i,r,t)$geo(i) = cost_cap_fin_mult_noITC("geothermal",r,t) ;
cost_cap_fin_mult_no_credits(i,r,t)$geo(i) = cost_cap_fin_mult_no_credits("geothermal",r,t) ;

* --- Upgrades ---
*Assign upgraded techs the same multipliers as the techs they are upgraded from
cost_cap_fin_mult(i,r,t)$[upgrade(i)$rfeas(r)] = sum{ii$upgrade_from(i,ii), cost_cap_fin_mult(ii,r,t) } ;
cost_cap_fin_mult_noITC(i,r,t)$[upgrade(i)$rfeas(r)] = sum{ii$upgrade_from(i,ii), cost_cap_fin_mult_noITC(ii,r,t) } ;

if(Sw_WaterMain=1,
cost_cap_fin_mult(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult(ii,r,t) } ;

cost_cap_fin_mult_noITC(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult_noITC(ii,r,t) } ;
) ;

* --- Nuclear Ban ---
*Assign increased cost multipliers to regions with state nuclear bans
if(Sw_NukeStateBan = 2,
  cost_cap_fin_mult(i,r,t)$[nuclear(i)$nuclear_ba_ban(r)] = cost_cap_fin_mult(i,r,t) * nukebancostmult ;
  cost_cap_fin_mult_noITC(i,r,t)$[nuclear(i)$nuclear_ba_ban(r)] = cost_cap_fin_mult_noITC(i,r,t) * nukebancostmult ;
) ;

* Start by setting all multipliers to 1
rsc_fin_mult(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;
rsc_fin_mult_noITC(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;

*Hydro, pumped-hydro, and geo have capital costs included in the supply curve, so change their multiplier to be the same as cost_cap_fin_mult
rsc_fin_mult(i,r,t)$geo(i) = cost_cap_fin_mult('geothermal',r,t) ;
rsc_fin_mult(i,r,t)$hydro(i) = cost_cap_fin_mult('hydro',r,t) ;
rsc_fin_mult(i,r,t)$psh(i) = cost_cap_fin_mult(i,r,t) ;
rsc_fin_mult_noITC(i,r,t)$geo(i) = cost_cap_fin_mult_noITC('geothermal',r,t) ;
rsc_fin_mult_noITC(i,r,t)$hydro(i) = cost_cap_fin_mult_noITC('hydro',r,t) ;
rsc_fin_mult_noITC(i,r,t)$psh(i) = cost_cap_fin_mult_noITC(i,r,t) ;

* Apply cost reduction multipliers
rsc_fin_mult(i,r,t)$geo(i) = rsc_fin_mult(i,r,t) * sum{geotech$i_geotech(i,geotech), geocapmult(t,geotech) } ;
rsc_fin_mult_noITC(i,r,t)$geo(i) = rsc_fin_mult_noITC(i,r,t) * sum{geotech$i_geotech(i,geotech), geocapmult(t,geotech) } ;
rsc_fin_mult(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult_noITC(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult(i,r,t)$ofswind(i) = rsc_fin_mult(i,r,t) * ofswind_rsc_mult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$ofswind(i) = rsc_fin_mult_noITC(i,r,t) * ofswind_rsc_mult(t,i) ;

$ifthen.sregfin %GSw_IndividualSites% == 1
* For individual sites, we add the following "_rb" parameters to calculate financial multipliers
* at the BA-level, using a strict average of the resource regions within each BA. These BA-level
* parameters are then applied uniformly to the individual sites within that BA.

cost_cap_fin_mult_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult(i,rr,t)], cost_cap_fin_mult(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult(i,rr,t)], 1 }
;

cost_cap_fin_mult_noITC_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_noITC(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_noITC(i,rr,t)], cost_cap_fin_mult_noITC(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_noITC(i,rr,t)], 1 }
;

cost_cap_fin_mult_no_credits_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_no_credits(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_no_credits(i,rr,t)], cost_cap_fin_mult_no_credits(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_no_credits(i,rr,t)], 1 }
;

rsc_fin_mult_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$rsc_fin_mult(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$rsc_fin_mult(i,rr,t)], rsc_fin_mult(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$rsc_fin_mult(i,rr,t)], 1 }
;

rsc_fin_mult_noITC_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$rsc_fin_mult_noITC(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$rsc_fin_mult_noITC(i,rr,t)], rsc_fin_mult_noITC(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$rsc_fin_mult_noITC(i,rr,t)], 1 }
;

cost_cap_fin_mult(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), cost_cap_fin_mult_rb(i,rb,t) } ;
cost_cap_fin_mult_noITC(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), cost_cap_fin_mult_noITC_rb(i,rb,t) } ;
cost_cap_fin_mult_no_credits(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), cost_cap_fin_mult_no_credits_rb(i,rb,t) } ;
rsc_fin_mult(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), rsc_fin_mult_rb(i,rb,t) } ;
rsc_fin_mult_noITC(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), rsc_fin_mult_noITC_rb(i,rb,t) } ;
$endif.sregfin

*trimming the cost_cap_fin_mult parameters to reduce file sizes
cost_cap_fin_mult(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))$(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                         $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

cost_cap_fin_mult_noITC(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                                $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                                $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

cost_cap_fin_mult_no_credits(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                                    $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                                    $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

*round the cost_cap_fin_mult parameters, since they were re-calculated
cost_cap_fin_mult(i,r,t)$[valinv_irt(i,r,t) or upgrade(i) or sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) }
                         or sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) }] = round(cost_cap_fin_mult(i,r,t),3) ;

cost_cap_fin_mult_noITC(i,r,t)$[valinv_irt(i,r,t) or upgrade(i) or sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) }
                               or sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) }] = round(cost_cap_fin_mult_noITC(i,r,t),3) ;

cost_cap_fin_mult_no_credits(i,r,t)$[valinv_irt(i,r,t) or upgrade(i) or sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) }
                                    or sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) }]
                            = round(cost_cap_fin_mult_no_credits(i,r,t),3) ;

rsc_fin_mult(i,r,t)$rsc_fin_mult(i,r,t) = round(rsc_fin_mult(i,r,t),3) ;

*Set cost_cap_fin_mult_out equal to cost_cap_fin_mult before we alter cost_cap_fin_mult for Virginia policy
*and zero carbon policy.
cost_cap_fin_mult_out(i,r,t) = cost_cap_fin_mult(i,r,t) ;

*Penalizing new gas built within cost recovery period of 20 years in Virginia
cost_cap_fin_mult(i,r,t)$[gas(i)$r_st(r,'VA')] = cost_cap_fin_mult(i,r,t) * ng_lifetime_cost_adjust(t) ;

*Penalizing new gas that can be upgraded to recover upgrade costs prior to upgrade within 20 years of a zero carbon policy
cost_cap_fin_mult(i,r,t)$[gas(i)$(not ccs(i))] = cost_cap_fin_mult(i,r,t) * (((ng_carb_lifetime_cost_adjust(t) - 1) * .2) + 1) ;

* --- End calculations of cost_cap_fin_mult family of parameters --- *

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

*dump data for tax credit phaseout calculations
parameter
  emit_r_tc(r,t)                          "--million metric tons CO2-- co2 emissions, regional (note: units dependent on emit_scale)"
  emit_nat_tc(t)                          "--million metric tons CO2-- co2 emissions, national (note: units dependent on emit_scale)"
;

emit_r_tc(r,t)$[rfeas(r)$tmodel_new(t)] = emit.l("CO2",r,t) * emit_scale("CO2") ;
emit_nat_tc(t)$tmodel_new(t) = sum{r$rfeas(r), emit_r_tc(r,t) } ;

execute_unload "outputs%ds%tc_phaseout_data%ds%emit_for_tc_phaseout_calc_%cur_year%.gdx"
  emit_nat_tc, emit_r_tc
;

* Abort if the solver returns an error
if (ReEDSmodel.modelStat > 1,
    abort "Model did not solve to optimality",
    ReEDSmodel.modelStat) ;
