$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$if not set case $setglobal case ref

sets
sys_costs /
  inv_investment_capacity_costs
  inv_investment_capacity_costs_noITC
  inv_investment_refurbishment_capacity
  inv_investment_refurbishment_capacity_noITC
  inv_investment_spurline_costs_rsc_technologies
  inv_transmission_line_investment
  inv_substation_investment_costs
  inv_interconnection_costs
  inv_ptc_payments_negative
  inv_ptc_payments_negative_refurbishments
  op_vom_costs
  op_operating_reserve_costs
  op_fuelcosts_objfn
  op_fom_costs
  op_international_hurdle_rate
  op_emissions_taxes
  op_acp_compliance_costs
/,

sys_costs_inv(sys_costs) /
  inv_investment_capacity_costs
  inv_investment_refurbishment_capacity
  inv_investment_spurline_costs_rsc_technologies
  inv_transmission_line_investment
  inv_substation_investment_costs
  inv_interconnection_costs
  inv_ptc_payments_negative
  inv_ptc_payments_negative_refurbishments
/,

sys_costs_op(sys_costs) /
  op_vom_costs
  op_operating_reserve_costs
  op_fuelcosts_objfn
  op_fom_costs
  op_international_hurdle_rate
  op_emissions_taxes
  op_acp_compliance_costs
/,

rev_cat "categories for renvenue streams" /load, res_marg, oper_res, rps/,

lcoe_cat "categories for LCOE calculation" /capcost, rsccost, fomcost, vomcost, gen /
;

*This parameter list is in alphabetical order - please add new entries that way
parameter
  avg_cf                         "--frac-- Annual average capacity factor for rsc technologies"
  avg_avail                      "--frac-- Annual average avail factor"
  cap_avail                      "--MW-- Available capacity at beginning of model year for rsc techs"
  cap_firm(i,r,szn,t)            "--MW-- firm capacity that counts toward the reserve margin constraint by BA and season",
  cap_new_cc                     "--MW-- new capacity that is VRE, for new capacity credit calculation"
  cc_new                         "--frac-- capacity credit for new VRE techs"
  cap_icrt(i,v,r,t)              "--MW-- capacity by tech, year, region, and class"
  cap_deg_icrt(i,v,r,t)          "--MW-- Degraded capacity, equal to CAP.l"
  cap_new_ann_out(i,r,t)         "--MW/yr-- new annual capacity by region"
  cap_new_bin_out                "--MW-- capacity of built techs"
  cap_new_icrt                   "--MW-- new capacity"
  cap_new_out(i,r,t)             "--MW-- new capacity by region, which are investments from one solve year to the next"
  cap_out(i,r,t)                 "--MW-- capacity by region"
  cost_vom_rr                    "--$/MWh-- vom cost for all regions, including resource regions"
  curt_all_ann(i,v,r,t)          "--frac-- annual average marginal curtailment rate"
  curt_out(r,h,t)                "--MW-- curtailment from VRE generators"
  curt_out_ann(r,t)              "--MWh-- annual curtailment from VRE generators by region"
  curt_rate(t)                   "--frac-- fraction of VRE generation that is curtailed"
  curt_rr(i,rr,h,t)              "--frac-- curtailment fraction for all regions, including resource region"
  curt_all_out                   "--frac-- combined curt_int and curt_marg output"
  gen_new_uncurt                 "--MWh-- uncurtailed generation from new VRE techs"
  curt_new                       "--frac-- curtailment frac for new VRE techs"
  cc_all_out                     "--frac-- combined cc_int and m_cc_mar output"
  emit_nat(t)                    "--metric tons CO2-- co2 emissions, national"
  emit_r(r,t)                    "--metric tons CO2-- co2 emissions, regional"
  error_check(*)                 "--unitless-- set of checks to determine if there is an error - values should be zero if there is no error"
  gen_icrt                       "--MWh-- annual generation"
  gen_icrt_uncurt                "--MWh-- annual uncurtailed generation from VREs"
  gen_out(i,r,h,t)               "--MW-- generation by timeslice"
  gen_out_ann(i,r,t)             "--MWh-- annual generation"
  gen_rsc                        "--MWh/MW-- Annual generation per MW from rsc techs"
  load_rt(r,t)                   "--MWh-- Annual exogenous load"
  load_frac_rt(r,t)              "--fraction-- Fraction of LOAD in each region"
  ilr(i)                         "--unitless-- inverter loading ratio - used to convert DC capacity to AC capacity for PV systems"
  invtran_out(r,rr,t,trtype)     "--MW-- new transmission capacity"
  lcoe                           "--$/MWh-- levelized cost of electricity for all tech options"
  lcoe_built(i,r,t)              "--$/MWh-- levelized cost of electricity for technologies that were built"
  lcoe_built_nat(i,t)            "--$/MWh-- national average levelized cost of electricity for technologies that were built"
  lcoe_cf_act                    "--$/MWh-- LCOE using actual (instead of max) capacity factors"
  lcoe_fullpol                   "--$/MWh-- LCOE considering full ITC and PTC value, whereas the LCOE parameter considers the annualized objective function"
  lcoe_nopol                     "--$/MWh-- LCOE without considering ITC and PTC adjustments"
  lcoe_pieces(lcoe_cat,i,r,t)    "--varies-- levelized cost of electricity elements for technologies that were built"
  lcoe_pieces_nat(lcoe_cat,i,t)  "--varies-- national average levelized cost of electricity elements for technologies that were built"
  losses_ann(*,t)                "--MWh-- annual losses by category",
  losses_tran_h(rr,r,h,t,trtype) "--MW-- transmission losses by timeslice"
  objfn_raw                      "--2004$ in net present value terms-- the raw objective function value"
  opRes_supply_h(ortype,i,r,h,t) "--MW-- supply of operating reserves by timeslice and region",
  opRes_supply(ortype,i,r,t)     "--MW-h-- annual supply of operating reserves by region",
  reqt_price                     "--varies-- Price of requirements"
  reqt_quant                     "--varies-- Requirement quantity"
  raw_inv_cost(t)                "--2004$-- sum of investment costs from systemcost"
  raw_op_cost(t)                 "--2004$-- sum of operational costs from systemcost"
  reduced_cost                   "--2004$/kW undiscounted-- the reduced cost of each investment option. All non-rsc are assigned to nobin"
  repbioprice(r,t)               "--2004$/MMBtu-- highest marginal bioprice of utilized bins for each region"
  repgasprice(cendiv,t)          "--2004$/MMBtu-- highest marginal gas price of utilized gas bins for each census division"
  repgasprice_r(r,t)             "--2004$/MMBtu-- highest marginal gas price of utilized gas bins for each region"
  repgasprice_nat(t)             "--2004$/MMBtu-- weighted-average national natural gas price assuming that plants pay the marginal price"
  repgasquant(cendiv,t)          "--Quads-- quantity of gas consumed in each census division"
  repgasquant_r(r,t)               "--Quads-- quantity of gas consumed in each region"
  repgasquant_nat(t)             "--Quads-- national consumption of natural gas"
  ret_ann_out(i,r,t)             "--MW/yr-- annual retired capacity by region"
  ret_out(i,r,t)                 "--MW-- retired capacity by region"
  rr_country(r,country)          "--unitless-- mapping from all regions, including resource regions, to country"
  revenue(rev_cat,i,r,t)         "--2004$-- sum of revenues"
  revenue_nat(rev_cat,i,t)       "--2004$-- sum of revenues"
  revenue_en(rev_cat,i,r,t)      "--2004$/MWh-- revenues per MWh of generation"
  revenue_en_nat(rev_cat,i,t)    "--2004$/MWh-- revenues per MWh of generation"
  revenue_cap(rev_cat,i,r,t)     "--2004$/MW-- revenues per MW of capacity"
  revenue_cap_nat(rev_cat,i,t)   "--2004$/MW-- revenues per MW of capacity"
  stor_inout                     "--MWh-- Annual energy going into and out of storage"
  stor_in(i,v,r,h,t)             "--MW-- energy going in to storage"
  stor_level(i,v,r,h,t)          "--MWh-- storage level"
  stor_out(i,v,r,h,t)            "--MW-- energy leaving storage"
  systemcost(sys_costs,t)        "--2004$-- reported system cost for each component, where inv costs are model year present value and op costs are single year"
  systemcost_bulk(sys_costs,t)   "--2004$-- reported system cost for each component, where all costs are model year present value"
  systemcost_bulk_ew(sys_costs,t) "--2004$-- same as systemcost_bulk, but the end year is only 1 year of operation and CRF times the investment"
  tran_flow_out(r,rr,t,trtype)   "--MWh-- annual transmission flows between region"
  tran_mi_out(t,trtype)          "--MW-mi-- total transmission capacity by distance"
  tran_out(r,rr,t,trtype)        "--MW-- total transmission capacity"
  tran_util_nat_out(t,trtype)    "--fraction-- national transmission utilization rate by trtype"
  tran_util_nat2_out(t)          "--fraction-- national transmission utilization rate"
  tran_util_out(r,rr,t,trtype)   "--fraction-- regional transmission utilization rate"
;

*=========================
* LCOE
*=========================

avg_avail(i,v) = sum{h, hours(h) * avail(i,v,h) } / 8760 ;
avg_cf(i,v,r,t)$[CAP.l(i,v,r,t)$(not rsc_i(i))] = sum(h,GEN.l(i,v,r,h,t)*hours(h))/(CAP.l(i,v,r,t) * 8760) ;

*non-rsc technologies do not face the grid supply curve
*and thus can be assigned to an individual bin
lcoe(i,v,r,t,"bin1")$((not rsc_i(i))$valcap(i,v,r,t)$ict(i,v,t)$avg_avail(i,v)) =
* cost of capacity divided by generation
   ((crf(t) * cost_cap_fin_mult(i,r,t) * cost_cap(i,t)$newv(v) + cost_fom(i,v,r,t)) / (avg_avail(i,v) * 8760))
*plus ONM costs
   + cost_vom(i,v,r,t)
* plus fuel costs - assuming constant fuel prices here (model prices might be different)
   + heat_rate(i,v,r,t) * fuel_price(i,r,t)
;

curt_rr(i,rr,h,t) = 0 ;
curt_rr(i,rr,h,t)$vre(i) = curt_marg(i,rr,h,t) + curt_int(i,rr,h,t) ;
rr_country(rr,country) = sum{r$cap_agg(r,rr), r_country(r,country) } ;
cost_vom_rr(i,v,rr,t) = sum{r$cap_agg(r,rr), cost_vom(i,v,r,t) } ;
gen_rsc(i,v,r,t)$(valcap(i,v,r,t)$ict(i,v,t)$rsc_i(i)) =
    sum{h, m_cf(i,v,r,h,t) * (1 - curt_rr(i,r,h,t)) * hours(h) } ;

lcoe(i,v,r,t,rscbin)$(valcap(i,v,r,t)$ict(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)) =
* cost of capacity divided by generation
    (crf(t) * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t) + m_rsc_dat(r,i,rscbin,"cost")$newv(v)) + cost_fom(i,v,r,t))
    / gen_rsc(i,v,r,t)

*plus ONM costs
    + cost_vom_rr(i,v,r,t)
;

lcoe_cf_act(i,v,r,t,rscbin)$rsc_i(i) = lcoe(i,v,r,t,rscbin) ;
lcoe_cf_act(i,v,r,t,"bin1")$((not rsc_i(i))$valcap(i,v,r,t)$ict(i,v,t)$avg_cf(i,v,r,t)) =
* cost of capacity divided by generation
   ((crf(t) * cost_cap_fin_mult(i,r,t) * cost_cap(i,t)$newv(v) + cost_fom(i,v,r,t)) / (avg_cf(i,v,r,t) * 8760))
*plus ONM costs
   + cost_vom(i,v,r,t)
*plus fuel costs - assuming constant fuel prices here (model prices might be different)
   + heat_rate(i,v,r,t) * fuel_price(i,r,t)
;

lcoe_nopol(i,v,r,t,rscbin) = lcoe(i,v,r,t,rscbin) ;
lcoe_nopol(i,v,r,t,rscbin)$(valcap(i,v,r,t)$ict(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)) =
* cost of capacity divided by generation
    (crf(t) * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t) + m_rsc_dat(r,i,rscbin,"cost")$newv(v)) + cost_fom(i,v,r,t))
    / gen_rsc(i,v,r,t)

*plus ONM costs
    + cost_vom_rr(i,v,r,t)
;

lcoe_fullpol(i,v,r,t,rscbin) = lcoe(i,v,r,t,rscbin) ;
lcoe_fullpol(i,v,r,t,rscbin)$(valcap(i,v,r,t)$ict(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)) =
* cost of capacity divided by generation
    (crf(t) * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t) + m_rsc_dat(r,i,rscbin,"cost")$newv(v)) + cost_fom(i,v,r,t))
    / gen_rsc(i,v,r,t)

*plus ONM costs
    + cost_vom_rr(i,v,r,t)
;

lcoe_built(i,r,t)$[sum{(v,h)$sum{rr$[valinv(i,v,rr,t)$cap_agg(r,rr)], INV.l(i,v,rr,t) }, GEN.l(i,v,r,h,t) * hours(h) }] =
        (crf(t) * (
         sum{(v,rr)$[valinv(i,v,rr,t)$cap_agg(r,rr)],
             INV.l(i,v,rr,t) * (cost_cap_fin_mult(i,rr,t) * cost_cap(i,t) ) }
       + sum{(v,rr,rscbin)$[m_rscfeas(rr,i,rscbin)$valinv(i,v,rr,t)$rsc_i(i)$cap_agg(r,rr)],
             INV_RSC.l(i,v,rr,rscbin,t) * m_rsc_dat(rr,i,rscbin,"cost") * rsc_fin_mult(i,rr,t) }
                 )
       + sum{(v,rr)$[valinv(i,v,rr,t)$cap_agg(r,rr)], cost_fom(i,v,rr,t) * INV.l(i,v,rr,t) }
       + sum{(v,h)$sum{rr$[valinv(i,v,rr,t)$cap_agg(r,rr)], INV.l(i,v,rr,t) }, (cost_vom(i,v,r,t)+ heat_rate(i,v,r,t) * fuel_price(i,r,t)) * GEN.l(i,v,r,h,t) * hours(h) }
        ) / sum{(v,h)$sum{rr$[valinv(i,v,rr,t)$cap_agg(r,rr)], INV.l(i,v,rr,t) }, GEN.l(i,v,r,h,t) * hours(h) }
;

lcoe_built_nat(i,t)$[sum{(v,r)$valinv(i,v,r,t), INV.l(i,v,r,t) }] =
         sum{r$rfeas(r), lcoe_built(i,r,t) * sum{v$valinv(i,v,r,t), INV.l(i,v,r,t) } } / sum{(v,r)$valinv(i,v,r,t), INV.l(i,v,r,t) } ;

lcoe_pieces("capcost",i,r,t) =  sum{(v,rr)$[valinv(i,v,rr,t)$cap_agg(r,rr)],
             INV.l(i,v,rr,t) * (cost_cap_fin_mult(i,rr,t) * cost_cap(i,t) ) } ;

lcoe_pieces("rsccost",i,r,t) = sum{(v,rr,rscbin)$[m_rscfeas(rr,i,rscbin)$valinv(i,v,rr,t)$rsc_i(i)$cap_agg(r,rr)],
             INV_RSC.l(i,v,rr,rscbin,t) * m_rsc_dat(rr,i,rscbin,"cost") * rsc_fin_mult(i,rr,t) } ;

lcoe_pieces("fomcost",i,r,t) = sum{(v,rr)$[valinv(i,v,rr,t)$cap_agg(r,rr)], cost_fom(i,v,rr,t) * INV.l(i,v,rr,t) } ;

lcoe_pieces("vomcost",i,r,t) = sum{(v,h)$sum{rr$[valinv(i,v,rr,t)$cap_agg(r,rr)], INV.l(i,v,rr,t) }, (cost_vom(i,v,r,t)+ heat_rate(i,v,r,t) * fuel_price(i,r,t)) * GEN.l(i,v,r,h,t) * hours(h) } ;

lcoe_pieces("gen",i,r,t) = sum{(v,h)$sum{rr$[valinv(i,v,rr,t)$cap_agg(r,rr)], INV.l(i,v,rr,t) }, GEN.l(i,v,r,h,t) * hours(h) } ;

lcoe_pieces_nat(lcoe_cat,i,t) = sum{r, lcoe_pieces(lcoe_cat,i,r,t) } ;

*========================================
* REQUIREMENT PRICES AND QUANTITIES
*========================================

load_frac_rt(r,t)$sum{(rr,h), hours(h) * LOAD.l(rr,h,t) } = sum{h, hours(h) * LOAD.l(r,h,t) }/ sum{(rr,h), hours(h) * LOAD.l(rr,h,t) } ;

*Load and operating reserve prices are $/MWh, and reserve margin price is $/kW-yr
reqt_price('load','na',r,h,t)$(rfeas(r)$tmodel_new(t)) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_loadcon.m(r,h,t) / hours(h) ;
reqt_price('res_marg','na',r,szn,t)$(rfeas(r)$tmodel_new(t)) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_reserve_margin.m(r,szn,t) / 1000 ;
reqt_price('res_marg_ann','na',r,'ann',t) = sum{szn, reqt_price('res_marg','na',r,szn,t) } ;
reqt_price('oper_res',ortype,r,h,t)$(rfeas(r)$tmodel_new(t)) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_OpRes_requirement.m(ortype,r,h,t) / hours(h) ;
reqt_price('state_rps',RPSCat,r,'ann',t)$(rfeas(r)$tmodel_new(t)) = (1 / cost_scale) * (1 / pvf_onm(t)) * sum(st$r_st(r,st),eq_REC_Requirement.m(RPSCat,st,t)) ;
reqt_price('nat_gen','na',r,'ann',t)$(rfeas(r)$tmodel_new(t)) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_national_gen.m(t) ;
reqt_price('annual_cap',e,r,'ann',t)$(rfeas(r)$tmodel_new(t)) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_annual_cap.m(e,t) ;

*Load and operating reserve quantities are MWh, and reserve margin quantity is kW
reqt_quant('load','na',r,h,t)$(rfeas(r)$tmodel_new(t)) = hours(h) * LOAD.l(r,h,t) ;
reqt_quant('res_marg','na',r,szn,t)$(rfeas(r)$tmodel_new(t)) = peakdem(r,szn,t) * (1+prm(r,t)) * 1000 ;
reqt_quant('res_marg_ann','na',r,'ann',t) = sum{szn, reqt_quant('res_marg','na',r,szn,t) } ;
reqt_quant('oper_res',ortype,r,h,t)$(rfeas(r)$tmodel_new(t)) =
    hours(h) * (
        orperc(ortype,"or_load") * LOAD.l(r,h,t)
      + orperc(ortype,"or_wind") * sum{(i,v)$[wind(i)$valgen(i,v,r,t)],
          GEN.l(i,v,r,h,t) }
      + orperc(ortype,"or_pv")   * sum{(i,v)$[pv(i)$valcap(i,v,r,t)],
           CAP.l(i,v,r,t) }$dayhours(h)
    ) ;
reqt_quant('state_rps',RPSCat,r,'ann',t)$(rfeas(r)$tmodel_new(t)) =
    sum{st$r_st(r,st),RecPerc(RPSCat,st,t)} *sum{h,hours(h) *( (LOAD.l(r,h,t) - can_exports_h(r,h,t)) / distloss - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) })};
reqt_quant('nat_gen','na',r,'ann',t)$(rfeas(r)$tmodel_new(t)) =
    national_gen_frac(t) * (
    sum{(h)$rfeas(r), LOAD.l(r,h,t) * hours(h) }
    + sum{(rr,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype) * hours(h)) }
    + sum{(i,v,h)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN.l(i,v,r,h,t) * hours(h) }
    - sum{(i,v,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN.l(i,v,r,h,t) * hours(h) }
    ) ;
reqt_quant('annual_cap',e,r,'ann',t)$(rfeas(r)$tmodel_new(t)) = emit_cap(e,t) * load_frac_rt(r,t) ;

load_rt(r,t)$[rfeas(r)$tmodel_new(t)] = sum{h, hours(h) * load_exog(r,h,t) } ;

*========================================
* FUEL PRICES AND QUANTITIES
*========================================


repbioprice(r,t)$tmodel_new(t) = smax{bioclass$bioused.l(bioclass,r,t), biosupply(r,"cost",bioclass) } ;

* 1e9 converts from MMBtu to Quads
repgasquant(cendiv,t)$[(Sw_GasCurve = 0)$tmodel_new(t)$cdfeas(cendiv)] =
    sum{(gb,h), GASUSED.l(cendiv,gb,h,t) * hours(h) } / 1e9 ;

repgasquant(cendiv,t)$[(Sw_GasCurve = 1 or Sw_GasCurve = 2)$tmodel_new(t)$cdfeas(cendiv)] =
    sum{(i,v,r,h)$[r_cendiv(r,cendiv)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t)
       } / 1e9 ;

repgasquant_r(r,t)$[tmodel_new(t)$rfeas(r)] =
    sum{(i,v,h)$[valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t)
       } / 1e9 ;

repgasquant_nat(t)$tmodel_new(t) = sum{cendiv$cdfeas(cendiv), repgasquant(cendiv,t) } ;

*for reported gasprice (not that used to compute system costs)
*scale back to $ / mmbtu
repgasprice(cendiv,t)$[(Sw_GasCurve = 0)$tmodel_new(t)$cdfeas(cendiv)] =
    smax{gb$[sum{h, GASUSED.l(cendiv,gb,h,t) }], gasprice(cendiv,gb,t) } / gas_scale ;

repgasprice(cendiv,t)$[(Sw_GasCurve = 2)$tmodel_new(t)$cdfeas(cendiv)$repgasquant(cendiv,t)] =
    sum{(i,v,r,h)$[r_cendiv(r,cendiv)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h)*heat_rate(i,v,r,t)*fuel_price(i,r,t)*GEN.l(i,v,r,h,t)
       } / (repgasquant(cendiv,t) * 1e9) ;

repgasprice_r(rb,t)$[(Sw_GasCurve = 0 or Sw_GasCurve = 2)$tmodel_new(t)$rfeas(rb)] = sum{cendiv$r_cendiv(rb,cendiv), repgasprice(cendiv,t) } ;

repgasprice_r(rb,t)$[(Sw_GasCurve = 1)$tmodel_new(t)$rfeas(rb)] =
              ( sum{(h,cendiv)$r_cendiv(rb,cendiv),
                   gasmultterm(cendiv,t) * szn_adj_gas(h) * cendiv_weights(rb,cendiv) *
                   hours(h) } / sum{h, hours(h) }

              + smax((fuelbin,cendiv)$VGASBINQ_REGIONAL.l(fuelbin,cendiv,t), gasbinp_regional(fuelbin,cendiv,t) )

              + smax(fuelbin$VGASBINQ_NATIONAL.l(fuelbin,t), gasbinp_national(fuelbin,t) )
              ) ;

repgasprice(cendiv,t)$[(Sw_GasCurve = 1)$tmodel_new(t)$cdfeas(cendiv)] =
    sum{rb$[rfeas(rb)$r_cendiv(rb,cendiv)], repgasprice_r(rb,t) * repgasquant_r(rb,t) } / repgasquant(cendiv,t) ;

repgasprice_nat(t)$[tmodel_new(t)$sum{cendiv$cdfeas(cendiv), repgasquant(cendiv,t) }] =
    sum{cendiv$cdfeas(cendiv), repgasprice(cendiv,t) * repgasquant(cendiv,t) }
    / sum{cendiv$cdfeas(cendiv), repgasquant(cendiv,t) } ;

*=========================
* GENERATION
*=========================

gen_out(i,r,h,t) = sum{v$valgen(i,v,r,t), GEN.l(i,v,r,h,t) - STORAGE_IN.l(i,v,r,h,t)} ;
gen_out_ann(i,r,t) = sum{h, gen_out(i,r,h,t) * hours(h) } ;
gen_icrt(i,v,r,t) = sum{h, GEN.l(i,v,r,h,t) * hours(h) } ;
gen_icrt_uncurt(i,v,r,t)$vre(i) = sum{(rr,h)$[cap_agg(r,rr)$valcap(i,v,rr,t)], m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,t) * hours(h) } ;
stor_inout(i,v,r,t,"in")$storage(i) = sum{h, STORAGE_IN.l(i,v,r,h,t) * hours(h) } ;
stor_inout(i,v,r,t,"out")$storage(i) = gen_icrt(i,v,r,t) ;
stor_in(i,v,r,h,t)$storage(i) = STORAGE_IN.l(i,v,r,h,t) ;
stor_out(i,v,r,h,t)$storage(i) = GEN.l(i,v,r,h,t)$storage(i) ;
stor_level(i,v,r,h,t)$storage(i) = STORAGE_LEVEL.l(i,v,r,h,t) ;

*=========================
* Operating Reserves
*=========================

opres_supply_h(ortype,i,r,h,t)$tmodel_new(t) =
      sum{v, OPRES.l(ortype,i,v,r,h,t) } ;


opres_supply(ortype,i,r,t)$tmodel_new(t) = sum{h, hours(h) * opRes_supply_h(ortype,i,r,h,t) } ;

*=========================
* LOSSES AND CURTAILMENT
*=========================

curt_all_out(i,rr,h,t)$[rfeas_cap(rr)$vre(i)] =
    curt_int(i,rr,h,t) +
    curt_marg(i,rr,h,t)
;
curt_all_ann(i,v,rr,t)$sum{h, hours(h) * m_cf(i,v,rr,h,t) } =
      sum{h, curt_all_out(i,rr,h,t) * hours(h) * m_cf(i,v,rr,h,t) } /
      sum{h, hours(h) * m_cf(i,v,rr,h,t) }
;

gen_new_uncurt(i,rr,h,t)$[vre(i)$valcap_irt(i,rr,t)$rfeas_cap(rr)] =
      sum{v$valinv(i,v,rr,t), (INV.l(i,v,rr,t) + INV_REFURB.l(i,v,rr,t)) * m_cf(i,v,rr,h,t) * hours(h) }
;
curt_new(i,rr,h,t)$gen_new_uncurt(i,rr,h,t) = curt_all_out(i,rr,h,t) ;

curt_out(r,h,t) = CURT.l(r,h,t) ;
curt_out_ann(r,t) = sum{h, curt_out(r,h,t) * hours(h) } ;
curt_rate(t)$tmodel_new(t) = sum{r, curt_out_ann(r,t) } / (sum{(i,r)$vre(i), gen_out_ann(i,r,t) } + sum{r, curt_out_ann(r,t) }) ;

losses_ann('storage',t) = sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)$rfeas(r)], STORAGE_IN.l(i,v,r,h,t) * hours(h) }
                          - sum{(i,v,r,h)$[valcap(i,v,r,t)$storage_no_csp(i)$rfeas(r)], GEN.l(i,v,r,h,t) * hours(h) } ;
losses_ann('trans',t) = sum{(rr,r,h,trtype)$[rfeas(rr)$rfeas(r)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype) * hours(h)) } ;
losses_ann('curt',t) =  sum{r, curt_out_ann(r,t) } ;
losses_ann('load',t) = sum{(r,h)$rfeas(r), LOAD.l(r,h,t) * hours(h) }  ;

losses_tran_h(rr,r,h,t,trtype) = tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype) ;

*=========================
* CAPACTIY
*=========================

ilr(i) = 1 ;
ilr(i)$[upv(i) or dupv(i)] = 1.3 ;
ilr(i)$[sameas(i,"distpv")] = 1.1 ;

cap_deg_icrt(i,v,r,t) = CAP.l(i,v,r,t) / ilr(i) ;
cap_icrt(i,v,r,t)$[not (upv(i) or dupv(i))] = cap_deg_icrt(i,v,r,t) ;
cap_icrt(i,v,r,t)$[upv(i) or dupv(i)] = sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
                                          INV.l(i,v,r,tt) + INV_REFURB.l(i,v,r,tt)$[refurbtech(i)$Sw_Refurb]} / ilr(i) ;
cap_out(i,r,t)$tmodel_new(t) = sum{v$valcap(i,v,r,t), cap_icrt(i,v,r,t) };


*=========================
* NEW CAPACITY
*=========================

cap_new_out(i,r,t)$(not tfirst(t)) = sum(v$valinv(i,v,r,t), INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)) / ilr(i) ;
cap_new_out("distPV",r,t)$(not tfirst(t)) = cap_out("distPV",r,t) - sum(tt$tprev(t,tt), cap_out("distPV",r,tt)) ;
cap_new_ann_out(i,r,t)$cap_new_out(i,r,t) = cap_new_out(i,r,t) / (yeart(t) - sum(tt$tprev(t,tt), yeart(tt))) ;
cap_new_bin_out(i,v,r,t,rscbin)$[rsc_i(i)$valinv(i,v,r,t)] = Inv_RSC.l(i,v,r,rscbin,t) / ilr(i) ;
cap_new_bin_out(i,v,r,t,"bin1")$[(not rsc_i(i))$valinv(i,v,r,t)] = INV.l(i,v,r,t)  /ilr(i) ;
cap_new_icrt(i,v,r,t)$(not tfirst(t)) = (INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)) / ilr(i) ;

*=========================
* AVAILABLE CAPACITY
*=========================
cap_avail(i,r,t,rscbin)$(rsc_i(i)$rfeas_cap(r)$m_rscfeas(r,i,rscbin)) =
  m_rsc_dat(r,i,rscbin,"cap") - sum{(ii,v,tt)$[valinv(ii,v,r,tt)$tprev(t,tt)$(rsc_agg(i,ii))],
         INV_RSC.l(ii,v,r,rscbin,tt) * resourcescaler(ii) };


*=========================
* RETIRED CAPACITY
*=========================

ret_out(i,r,t)$(not tfirst(t)) = sum{tt$tprev(t,tt), cap_out(i,r,tt)} - cap_out(i,r,t) + cap_new_out(i,r,t) ;
ret_out(i,r,t)$(abs(ret_out(i,r,t)) < 1e-6) = 0 ;
ret_ann_out(i,r,t)$ret_out(i,r,t) = ret_out(i,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;

*==================================
* CAPACITY CREDIT AND FIRM CAPACITY
*==================================

cc_all_out(i,v,rr,szn,t) =
    cc_int(i,v,rr,szn,t)$[(vre(i) or storage(i))$valcap(i,v,rr,t)] +
    m_cc_mar(i,rr,szn,t)$[(vre(i) or storage(i))$valinv(i,v,rr,t)]
;

cap_new_cc(i,r,szn,t)$(vre(i) or storage(i)) = sum{v$ict(i,v,t),cap_new_icrt(i,v,r,t) } ;
cc_new(i,r,szn,t)$cap_new_cc(i,r,szn,t) = sum{v$ict(i,v,t), cc_all_out(i,v,r,szn,t) } ;

cap_firm(i,r,szn,t)$tmodel_new(t) =
      sum{v$[(not vre(i))$(not hydro(i))$(not storage(i))], CAP.l(i,v,r,t) }
    + sum{rr$[(vre(i) or storage(i))$cap_agg(r,rr)], cc_old(i,rr,szn,t) }
    + sum{(v,rr)$[cap_agg(r,rr)$(vre(i) or storage(i))$valinv(i,v,rr,t)],
         m_cc_mar(i,rr,szn,t) * (INV.l(i,v,rr,t) + INV_REFURB.l(i,v,rr,t)$[refurbtech(i)$Sw_Refurb]) }
    + sum{(v,rr)$[(vre(i) or storage(i))$cap_agg(r,rr)],
            cc_int(i,v,rr,szn,t) * CAP.l(i,v,rr,t) }
    + sum{(rr)$[(vre(i) or storage(i))$cap_agg(r,rr)],
            cc_excess(i,rr,szn,t) }
    + sum{v$[hydro_nd(i)],
         GEN.l(i,v,r,"h3",t) }
    + sum{v$[hydro_d(i)],
         CAP.l(i,v,r,t) * cf_hyd_szn_adj(i,szn,r) * cf_hyd(i,szn,r)  } ;

* Add in marginal firm capacity of distpv
cap_firm('distpv',r,szn,t)$tmodel_new(t) =
      cap_firm('distpv',r,szn,t)
    + sum{v$valcap('distpv',v,r,t),
          m_capacity_exog('distpv',v,r,t) - sum{tt$tprev(t,tt), m_capacity_exog('distpv',v,r,tt)}
         } * m_cc_mar('distpv',r,szn,t) ;

*========================================
* REVENUE LEVELS
*========================================

revenue('load',i,r,t)$rfeas(r) = sum{(v,h)$valgen(i,v,r,t),
  GEN.l(i,v,r,h,t) * hours(h) * reqt_price('load','na',r,h,t) } ;

revenue('res_marg',i,r,t)$rfeas(r) = sum{szn,
  cap_firm(i,r,szn,t) * reqt_price('res_marg','na',r,szn,t) * 1000 } ;

revenue('oper_res',i,r,t)$rfeas(r) = sum{(ortype,v,h)$valgen(i,v,r,t),
  OPRES.l(ortype,i,v,r,h,t) * hours(h) * reqt_price('oper_res',ortype,r,h,t) } ;

revenue('rps',i,r,t)$rfeas(r) =
  sum{(v,h,RPSCat)$[valgen(i,v,r,t)$sum{st$r_st(r,st), RecTech(RPSCat,st,i,t) }],
      GEN.l(i,v,r,h,t) * sum{st$r_st(r,st), RPSTechMult(i,st) } * hours(h) * reqt_price('state_rps',RPSCat,r,'ann',t) } ;

revenue_nat(rev_cat,i,t) = sum{r$rfeas(r), revenue(rev_cat,i,r,t) } ;

revenue_en(rev_cat,i,r,t)$[sum{(v,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t)}$(not vre(i))] =
  revenue(rev_cat,i,r,t) / sum{(v,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t) * hours(h) } ;

revenue_en(rev_cat,i,r,t)$[sum{(v,rr,h)$[cap_agg(r,rr)$valcap(i,v,rr,t)], m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,t) }$vre(i)] =
  revenue(rev_cat,i,r,t) / sum{(v,rr,h)$[cap_agg(r,rr)$valcap(i,v,rr,t)],
      m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,t) * hours(h) } ;

revenue_en_nat(rev_cat,i,t)$[sum{(v,r,h), GEN.l(i,v,r,h,t)}] =
  revenue_nat(rev_cat,i,t) / sum{(v,r,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t) * hours(h) } ;

revenue_cap(rev_cat,i,r,t)$[sum{(v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)], CAP.l(i,v,rr,t)}] =
  revenue(rev_cat,i,r,t) / sum{(v,rr)$[cap_agg(r,rr)$valcap(i,v,rr,t)], CAP.l(i,v,rr,t) } ;

revenue_cap_nat(rev_cat,i,t)$[sum{(v,r)$valcap(i,v,r,t), CAP.l(i,v,r,t)}] =
  revenue_nat(rev_cat,i,t) / sum{(v,r)$valcap(i,v,r,t), CAP.l(i,v,r,t) } ;

parameter gen_ann_nat(i,t) ;
gen_ann_nat(i,t) = sum{r, gen_out_ann(i,r,t) } ;

*=========================
* EMISSIONS
*=========================
*only outputing co2 emissions in order to not break bokeh
*other emission should be added to this output
emit_r(r,t)$[rfeas(r)$tmodel_new(t)] = emit.l("co2",r,t) ;
emit_nat(t)$tmodel_new(t) = sum{r$rfeas(r), emit_r(r,t) } ;

parameter emit_weighted;
emit_weighted = sum{t$tmodel(t), emit_nat(t) * pvf_onm(t) } ;


*=========================
* SYSTEM COST
*=========================

* REPLICATION OF THE OBJECTIVE FUNCTION

systemcost("inv_investment_capacity_costs",t)$tmodel_new(t) =
*investment costs (without the subtraction of any PTC value)
                   sum{(i,v,r)$valinv(i,v,r,t),
                        INV.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t) ) }
* Plus geo and hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
              + sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$(geo(i) or hydro(i))],
                   Inv_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult(i,r,t) }
;

systemcost("inv_investment_capacity_costs_noITC",t)$tmodel_new(t) =
*investment costs (without the subtraction of any PTC value)
                   sum{(i,v,r)$valinv(i,v,r,t),
                        INV.l(i,v,r,t) * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t) ) }
* Plus geo and hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
              + sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$(geo(i) or hydro(i))],
                   Inv_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * cost_cap_fin_mult_noITC(i,r,t) }
;

systemcost("inv_ptc_payments_negative",t)$tmodel_new(t) =
*ptc payment costs
                  - sum{(i,v,r)$valinv(i,v,r,t),
                        INV.l(i,v,r,t) * (ptc_unit_value(i,v,r,t) * sum{h, hours(h)* m_cf(i,v,r,h,t)
                         *(1-sum{rr$cap_agg(rr,r),curt_int(i,rr,h,t)+curt_marg(i,rr,h,t)}$(not hydro(i))) } ) }
;

systemcost("inv_investment_spurline_costs_rsc_technologies",t)$tmodel_new(t) =
*costs of rsc investment
*Note that cost_cap for hydro and geo techs are zero
*but hydro and geo rsc_fin_mult is equal to the same value as cost_cap_fin_mult
*(Note that exclusions of geo and hydro here deviates from the objective function structure)
              + sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$(not geo(i))$(not hydro(i))],
*investment in resource supply curve technologies
                   Inv_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult(i,r,t) }
;

systemcost("inv_investment_refurbishment_capacity",t)$tmodel_new(t) =
*costs of refurbishments of RSC tech (without the subtraction of any PTC value)
              + sum{(i,v,r)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                        (cost_cap_fin_mult(i,r,t) * cost_cap(i,t)) * INV_REFURB.l(i,v,r,t) }
;

systemcost("inv_investment_refurbishment_capacity_noITC",t)$tmodel_new(t) =
*costs of refurbishments of RSC tech (without the subtraction of any PTC value)
              + sum{(i,v,r)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                        (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t)) * INV_REFURB.l(i,v,r,t) }
;

systemcost("inv_ptc_payments_negative_refurbishments",t)$tmodel_new(t) =
*costs of ptc for refurbished techs
              - sum{(i,v,r)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                        ptc_unit_value(i,v,r,t) * sum{h, hours(h)* m_cf(i,v,r,h,t)
                         *(1-sum{rr$cap_agg(rr,r),curt_int(i,rr,h,t)+curt_marg(i,rr,h,t)}$(not hydro(i))) } * INV_REFURB.l(i,v,r,t) }
;

systemcost("inv_transmission_line_investment",t)$tmodel_new(t)  =
*costs of transmission lines
              + sum{(r,rr,trtype)$[routes(r,rr,trtype,t)$rfeas(r)$rfeas(rr)],
                        ((cost_tranline(r) + cost_tranline(rr)) / 2) * distance(r,rr,trtype) * InvTran.l(r,rr,t,trtype)  }
;

systemcost("inv_substation_investment_costs",t)$tmodel_new(t)  =
*costs of substations
              + sum{(r,vc)$(rfeas(r)$tscfeas(r,vc)),
                        cost_transub(r,vc) * InvSubstation.l(r,vc,t) }
;

systemcost("inv_interconnection_costs",t)$tmodel_new(t)  =
*cost of back-to-back AC-DC-AC interties
*conditional here that the interconnects must be different
              + sum{(r,rr)$[routes(r,rr,"DC",t)$rfeas(r)$rfeas(rr)$(t.val>2020)$(INr(r) <> INr(rr))],
                        cost_trandctie * InvTran.l(r,rr,t,"DC") }
;


*===============
*beginning of operational costs
*===============

systemcost("op_vom_costs",t)$tmodel_new(t)  =
*variable O&M costs
              sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$cost_vom(i,v,r,t)],
                   hours(h) * cost_vom(i,v,r,t) * GEN.l(i,v,r,h,t) }
;

systemcost("op_fom_costs",t)$tmodel_new(t)  =
*fixed O&M costs
              + sum{(i,v,r)$[valcap(i,v,r,t)],
                   cost_fom(i,v,r,t) * CAP.l(i,v,r,t) }
;

systemcost("op_operating_reserve_costs",t)$tmodel_new(t)  =
*operating reserve costs
*only applied to reg reserves because cost of providing other reserves is zero...
              + sum{(i,v,r,h,ortype)$[rfeas(r)$valgen(i,v,r,t)$cost_opres(i)$sameas(ortype,"reg")],
                   hours(h) * cost_opres(i) * OpRes.l(ortype,i,v,r,h,t) }
;

systemcost("op_fuelcosts_objfn",t)$tmodel_new(t)  =
*cost of coal and nuclear fuel (except coal used for cofiring)
              + sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$(not gas(i))$heat_rate(i,v,r,t)
                              $(not sameas("biopower",i))$(not cofire(i))],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN.l(i,v,r,h,t) }

*cofire coal consumption - cofire bio consumption already accounted for in accounting of BIOUSED
              + sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$cofire(i)$heat_rate(i,v,r,t)],
                   (1-bio_cofire_perc) * hours(h) * heat_rate(i,v,r,t)
                   * fuel_price("coal-new",r,t) * GEN.l(i,v,r,h,t) }

*cost of natural gas for Sw_GasCurve = 2 (static natural gas prices)
              + sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)
                              $(not sameas("biopower",i))$(not cofire(i))$(Sw_GasCurve = 2)],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN.l(i,v,r,h,t) }

*cost of natural gas for Sw_GasCurve = 0 (census division supply curves natural gas prices)
              + sum{(cendiv,gb)$cdfeas(cendiv), sum{h,hours(h) * GASUSED.l(cendiv,gb,h,t) }
                   * gasprice(cendiv,gb,t)
                   }$(Sw_GasCurve = 0)

*cost of natural gas for Sw_GasCurve = 3 (national supply curve for natural gas prices with census division multipliers)
              + sum{(h,cendiv,gb)$cdfeas(cendiv),hours(h) * GASUSED.l(cendiv,gb,h,t)
                   * gasadder_cd(cendiv,t,h) + gasprice_nat_bin(gb,t)
                   }$(Sw_GasCurve = 3)


*cost of natural gas for Sw_GasCurve = 1 (national and census division supply curves for natural gas prices)
*first - anticipated costs of gas consumption given last year's amount
              + (sum{(i,r,v,cendiv,h)$[rfeas(r)$valgen(i,v,r,t)$gas(i)$cdfeas(cendiv)],
                   gasmultterm(cendiv,t) * szn_adj_gas(h) * cendiv_weights(r,cendiv) *
                   hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t) }
*second - adjustments based on changes from last year's consumption at the regional and national level
              + sum{(fuelbin,cendiv)$cdfeas(cendiv),
                   gasbinp_regional(fuelbin,cendiv,t) * VGASBINQ_REGIONAL.l(fuelbin,cendiv,t) }

              + sum{(fuelbin),
                   gasbinp_national(fuelbin,t) * VGASBINQ_NATIONAL.l(fuelbin,t) }

              )$[Sw_GasCurve = 1]

*biofuel consumption
              + sum{(r,bioclass)$rfeas(r),
                   biopricemult(r,bioclass,t) * BIOUSED.l(bioclass,r,t) * biosupply(r,"cost",bioclass) }
;

systemcost("op_international_hurdle_rate",t)$tmodel_new(t)  =
*plus international hurdle costs
              + sum{(r,rr,h,trtype)$[routes(r,rr,trtype,t)$cost_hurdle(r,rr)],
                   cost_hurdle(r,rr) * hours(h) * FLOW.l(r,rr,h,t,trtype)  }
;

systemcost("op_emissions_taxes",t)$tmodel_new(t)  =
*plus any taxes on emissions
              + sum{(e,r), EMIT.l(e,r,t) * emit_tax(e,r,t) }
;

systemcost("op_acp_compliance_costs",t)$tmodel_new(t)  =
*plus ACP purchase costs
              + sum{(RPSCat,st)$stfeas(st), acp_price(st,t) * ACP_Purchases.l(RPSCat,st,t)
                   }$(yeart(t)>=RPS_StartYear)
;

raw_inv_cost(t) = sum{sys_costs_inv, systemcost(sys_costs_inv,t) } ;
raw_op_cost(t) = sum{sys_costs_op, systemcost(sys_costs_op,t) } ;

*For bulk system costs present value as of model year, capital costs are unchanged,
*while operation costs use pvf_onm_undisc
systemcost_bulk(sys_costs,t) = systemcost(sys_costs,t) ;
systemcost_bulk(sys_costs_op,t) = systemcost(sys_costs_op,t) * pvf_onm_undisc(t) ;

systemcost_bulk_ew(sys_costs,t) = systemcost_bulk(sys_costs,t) ;
systemcost_bulk_ew(sys_costs_op,t)$tlast(t) = systemcost(sys_costs_op,t) ;

*======================
* Error Check
*======================

error_check('z') = z.l - sum{t$tmodel(t), cost_scale *
                             (pvf_capital(t) * raw_inv_cost(t) + pvf_onm(t) * raw_op_cost(t)) } ;

*Round error_check for z because of small number differences that always show up due to machine rounding and tolerances
error_check('z') = round(error_check('z'), 1) ;

* Check to see is any generation or capacity from dissallowed resources
error_check("gen") = sum{(i,v,r,h,t)$[not valgen(i,v,r,t)], GEN.l(i,v,r,h,t) } ;
error_check("cap") = sum{(i,v,r,t)$[not valcap(i,v,r,t)], CAP.l(i,v,r,t) } ;
error_check("RPS") = sum{(RPSCat,i,st,ast,t)$[(not RecMap(i,RPSCat,st,ast,t))$(not stfeas(ast))], RECS.l(RPSCat,i,st,ast,t) } ;
error_check("OpRes") = sum{(ortype,i,v,r,h,t)$[not valgen(i,v,r,t)], OPRES.l(ortype,i,v,r,h,t) } ;

*======================
* Transmission
*======================

invtran_out(r,rr,t,trtype) = INVTRAN.l(r,rr,t,trtype) ;
tran_out(r,rr,t,trtype)$[ord(r) < ord(rr)] = CAPTRAN.l(r,rr,trtype,t) ;
tran_mi_out(t,trtype) = sum{(r,rr), tran_out(r,rr,t,trtype) * distance(r,rr,trtype) } ;

tran_flow_out(r,rr,t,trtype)$[(ord(r) < ord(rr))$tmodel_new(t)$routes(rr,r,trtype,t)] = sum{h, hours(h) * (FLOW.l(r,rr,h,t,trtype) + FLOW.l(rr,r,h,t,trtype)) } ;
tran_util_out(r,rr,t,trtype)$[tmodel_new(t)$tran_out(r,rr,t,trtype)] = tran_flow_out(r,rr,t,trtype) / (tran_out(r,rr,t,trtype) * 8760) ;

tran_util_nat_out(t,trtype)$[tmodel_new(t)$sum{(r,rr)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_out(r,rr,t,trtype) }] =
         sum{(r,rr)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_flow_out(r,rr,t,trtype) } / (sum{(r,rr)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_out(r,rr,t,trtype) } * 8760) ;

tran_util_nat2_out(t)$[tmodel_new(t)$sum{(r,rr,trtype)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_out(r,rr,t,trtype) }] =
         sum{(r,rr,trtype)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_flow_out(r,rr,t,trtype) } / (sum{(r,rr,trtype)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_out(r,rr,t,trtype) } * 8760) ;

*=========================
* Reduced Cost
*=========================
reduced_cost(i,v,r,t,"nobin","CAP")$valinv(i,v,r,t) = CAP.m(i,v,r,t)/(1000*cost_scale*pvf_capital(t)) ;
reduced_cost(i,v,r,t,"nobin","INV")$valinv(i,v,r,t) = INV.m(i,v,r,t)/(1000*cost_scale*pvf_capital(t)) ;
reduced_cost(i,v,r,t,rscbin,"INV_RSC")$(rsc_i(i)$valinv(i,v,r,t)$m_rscfeas(r,i,rscbin)) = INV_RSC.m(i,v,r,rscbin,t)/(1000*cost_scale*pvf_capital(t)) ;

objfn_raw = z.l;

execute_unload "outputs%ds%rep_%fname%.gdx"
  reqt_price, reqt_quant, load_rt, RecTech, prm,
  emit_r, emit_nat, repgasprice, repgasprice_r, repgasprice_nat, repgasquant_nat, repgasquant, repbioprice,
  gen_out, gen_out_ann, gen_icrt, gen_icrt_uncurt, cap_out, cap_new_ann_out, cap_new_bin_out, cap_new_icrt, cap_avail, cap_firm, ret_ann_out,
  m_capacity_exog, cap_icrt, cap_deg_icrt, ret_out, cap_new_out, cap_iter, gen_iter, cap_firm_iter, curt_tot_iter,
  cap_new_cc, cc_new, gen_new_uncurt, curt_new,
  objfn_raw, lcoe, lcoe_nopol, lcoe_fullpol, lcoe_cf_act,
  raw_inv_cost, raw_op_cost, pvf_capital, pvf_onm,
  systemcost, systemcost_bulk, systemcost_bulk_ew, error_check, cost_scale,
  invtran_out, tran_out, tran_mi_out, tran_flow_out, tran_util_out, tran_util_nat_out, tran_util_nat2_out,
  curt_out, curt_out_ann, curt_all_ann, curt_all_out, cc_all_out
  losses_tran_h, losses_ann, curt_rate, reduced_cost, emit_weighted,
  opRes_supply_h, opRes_supply, stor_inout, stor_in, stor_out, stor_level,
  revenue, revenue_nat, revenue_en, revenue_en_nat, revenue_cap, revenue_cap_nat
  lcoe_built, lcoe_built_nat, lcoe_pieces, lcoe_pieces_nat, gen_ann_nat ;

*This file is used in the ReEDS-to-PLEXOS data translation
execute_unload 'inputs_case%ds%plexos_inputs.gdx' biosupply, can_exports_h, cf_hyd, cf_hyd_szn_adj, forced_outage, h_szn, hierarchy, hours, hydmin, planned_outage,
                                                  pv_degrade_rate, rfeas, rscfeas, storage_duration, storage_eff, trancap_init_bd=trancap, windcfin ;

* compress all gdx files
execute '=gdxcopy -V7C -Replace inputs_case%ds%*.gdx' ;
execute '=gdxcopy -V7C -Replace outputs%ds%*.gdx' ;
execute '=gdxcopy -V7C -Replace outputs%ds%variabilityFiles%ds%*.gdx' ;

