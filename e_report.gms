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
  inv_investment_water_access
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
  inv_investment_water_access
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

rev_cat "categories for renvenue streams" /load, res_marg, oper_res, rps, charge, arbitrage/,

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
  cap_sdbin_out(i,r,szn,sdbin,t) "--MW-- binned storage capacity by year"
  cap_deg_icrt(i,v,r,t)          "--MW-- Degraded capacity, equal to CAP.l"
  cap_new_ann_out(i,r,t)         "--MW/yr-- new annual capacity by region"
  cap_new_bin_out                "--MW-- capacity of built techs"
  cap_new_icrt                   "--MW-- new capacity"
  cap_new_icrt_refurb            "--MW-- new refurbished capacity (including tfirst year)"
  cap_new_out(i,r,t)             "--MW-- new capacity by region, which are investments from one solve year to the next"
  cap_out(i,r,t)                 "--MW-- capacity by region"
  capex_ivrt(i,v,r,t)            "--$-- capital expenditure for new capacity, no ITC/depreciation/PTC reductions"
  cap_upgrade(i,r,t)             "--MW-- upgraded capacity by region"
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
  emit_nat(t)                    "--million metric tons CO2-- co2 emissions, national (note: units dependent on emit_scale)"
  emit_r(r,t)                    "--million metric tons CO2-- co2 emissions, regional (note: units dependent on emit_scale)"
  error_check(*)                 "--unitless-- set of checks to determine if there is an error - values should be zero if there is no error"
  expenditure_flow(*,r,rr,t)      "--2004$-- expenditures from flows of * moving from r to rr"
  expenditure_flow_rps(st,ast,t)  "--2004$-- expenditures from trades of RECS from st to ast"
  flex_load_out(flex_type,r,h,t)     "--MWh-- flexible load consumed in each timeslice"
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
  peak_load_adj(r,szn,t)         "--MWh-- peak load adjustment for each season"
  raw_inv_cost(t)                "--2004$-- sum of investment costs from systemcost"
  raw_op_cost(t)                 "--2004$-- sum of operational costs from systemcost"
  rec_outputs(RPSCat,i,st,ast,t) "--MWh-- quantity of RECs served from state st to state ast"
  reduced_cost                   "--2004$/kW undiscounted-- the reduced cost of each investment option. All non-rsc are assigned to nobin"
  RE_gen_price_nat(t)            "--2004$/MWh-- marginal cost of the national RE generation constraint"
  RE_cap_price_r(r,szn,t)        "--2004$/MW-yr-- marginal cost of the RE capacity constraint by BA"
  RE_cap_price_nat(szn,t)        "--2004$/MW-yr-- national average marginal cost of the RE capacity constraint"
  repbioprice(r,t)               "--2004$/MMBtu-- highest marginal bioprice of utilized bins for each region"
  repgasprice(cendiv,t)          "--2004$/MMBtu-- highest marginal gas price of utilized gas bins for each census division"
  repgasprice_r(r,t)             "--2004$/MMBtu-- highest marginal gas price of utilized gas bins for each region"
  repgasprice_nat(t)             "--2004$/MMBtu-- weighted-average national natural gas price assuming that plants pay the marginal price"
  repgasquant(cendiv,t)          "--Quads-- quantity of gas consumed in each census division"
  repgasquant_r(r,t)               "--Quads-- quantity of gas consumed in each region"
  repgasquant_nat(t)             "--Quads-- national consumption of natural gas"
  reqt_price                     "--varies-- Price of requirements"
  reqt_quant                     "--varies-- Requirement quantity"
  ret_ann_out(i,r,t)             "--MW/yr-- annual retired capacity by region"
  ret_out(i,r,t)                 "--MW-- retired capacity by region"
  revenue(rev_cat,i,r,t)         "--2004$-- sum of revenues"
  revenue_nat(rev_cat,i,t)       "--2004$-- sum of revenues"
  revenue_en(rev_cat,i,r,t)      "--2004$/MWh-- revenues per MWh of generation"
  revenue_en_nat(rev_cat,i,t)    "--2004$/MWh-- revenues per MWh of generation"
  revenue_cap(rev_cat,i,r,t)     "--2004$/MW-- revenues per MW of capacity"
  revenue_cap_nat(rev_cat,i,t)   "--2004$/MW-- revenues per MW of capacity"
  rr_country(r,country)          "--unitless-- mapping from all regions, including resource regions, to country"
  stor_inout                     "--MWh-- Annual energy going into and out of storage"
  stor_in(i,v,r,h,t)             "--MW-- energy going in to storage"
  stor_level(i,v,r,h,t)          "--MWh-- storage level"
  stor_out(i,v,r,h,t)            "--MW-- energy leaving storage"
  systemcost(sys_costs,t)        "--2004$-- reported system cost for each component, where inv costs are model year present value and op costs are single year"
  systemcost_bulk(sys_costs,t)   "--2004$-- reported system cost for each component, where inv costs are model year present value and op costs are model year present value until next model year"
  systemcost_bulk_ew(sys_costs,t) "--2004$-- same as systemcost_bulk, but the end year is same as systemcost"
  systemcost_ba(sys_costs,r, t)  "--2004$-- reported ba-level system cost for each component, where inv costs are model year present value and op costs are single year"
  systemcost_ba_bulk(sys_costs,r,t) "--2004$-- reported system cost for each component, where all costs are model year present value"
  systemcost_ba_bulk_ew(sys_costs,r,t) "--2004$-- same as systemcost_bulk, but the end year is only 1 year of operation and CRF times the investment"
  ACP_State_RHS(st,t)            "--MWh-- right hand side of eq_REC_Requirement at state level without multiplying RecPerc"
  ACP_portion(r,t)               "--unitless-- BA level proportion of ACP requirement"
  tax_expenditure_itc(t)         "--2004$-- ITC tax expenditure"
  tax_expenditure_ptc(t)         "--2004$-- PTC tax expenditure"
  tran_flow_out(r,rr,t,trtype)   "--MWh-- annual transmission flows between region"
  tran_flow_detail(r,rr,h,t,trtype) "--MWh-- transmission flows between region by time slice"
  tran_mi_out(t,trtype)          "--MW-mi-- total transmission capacity by distance"
  tran_out(r,rr,t,trtype)        "--MW-- total transmission capacity"
  tran_util_nat_out(t,trtype)    "--fraction-- national transmission utilization rate by trtype"
  tran_util_nat2_out(t)          "--fraction-- national transmission utilization rate"
  tran_util_out(r,rr,t,trtype)   "--fraction-- regional transmission utilization rate"
  vre_cost_vom(i,v,r,t)          "--2004$/MWh-- vom cost where vre technologies subtracts RE gen price nat"
  captrade(r,rr,trtype,szn,t)    "--MW-- planning reserve margin capacity traded from r to rr"
  gasshare_ba(r,cendiv,t)        "--unitless-- share of natural gas consumption in BA relative to corresponding cendiv consumption"
  gasshare_cendiv(cendiv,t)      "--unitless-- share of natural gas consumption in cendiv relative to national consumption"
  gascost_cendiv(cendiv,t)       "--2004$-- natual gas fuel cost at cendiv level"
  water_withdrawal_ivrt(i,v,r,t) "--Mgal-- water withdrawal by tech, year, region, and class"
  water_consumption_ivrt(i,v,r,t) "--Mgal-- water consumption by tech, year, region, and class"
  watcap_ivrt(i,v,r,t)           "--Mgal-- water capacity by tech, year, region, and class"
  watcap_out(i,r,t)              "--Mgal-- water capacity by region"
  watcap_new_ivrt(i,v,r,t)       "--Mgal-- new water capacity"
  watcap_new_out(i,r,t)          "--Mgal-- new water capacity by region, which are investments from one solve year to the next"
  watcap_new_ann_out(i,v,r,t)    "--Mgal/yr-- new annual water capacity by region"
  watret_out(i,r,t)              "--Mgal-- retired water capacity by region"
  watret_ann_out(i,v,r,t)        "--Mgal/yr-- annual retired water capacity by region"
;


*=========================
* LCOE
*=========================

avg_avail(i,v) = sum{h, hours(h) * avail(i,v,h) } / 8760 ;
avg_cf(i,v,r,t)$[CAP.l(i,v,r,t)$(not rsc_i(i))] = sum{h, GEN.l(i,v,r,h,t) * hours(h) } / (CAP.l(i,v,r,t) * 8760) ;

*non-rsc technologies do not face the grid supply curve
*and thus can be assigned to an individual bin
lcoe(i,v,r,t,"bin1")$((not rsc_i(i))$valcap(i,v,r,t)$ivt(i,v,t)$avg_avail(i,v)) =
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
gen_rsc(i,v,r,t)$(valcap(i,v,r,t)$ivt(i,v,t)$rsc_i(i)) =
    sum{h, m_cf(i,v,r,h,t) * (1 - curt_rr(i,r,h,t)) * hours(h) } ;

lcoe(i,v,r,t,rscbin)$(valcap(i,v,r,t)$ivt(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)) =
* cost of capacity divided by generation
    (crf(t) * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t) + m_rsc_dat(r,i,rscbin,"cost")$newv(v)) + cost_fom(i,v,r,t))
    / gen_rsc(i,v,r,t)

*plus ONM costs
    + cost_vom_rr(i,v,r,t)
;

lcoe_cf_act(i,v,r,t,rscbin)$rsc_i(i) = lcoe(i,v,r,t,rscbin) ;
lcoe_cf_act(i,v,r,t,"bin1")$((not rsc_i(i))$valcap(i,v,r,t)$ivt(i,v,t)$avg_cf(i,v,r,t)) =
* cost of capacity divided by generation
   ((crf(t) * cost_cap_fin_mult(i,r,t) * cost_cap(i,t)$newv(v) + cost_fom(i,v,r,t)) / (avg_cf(i,v,r,t) * 8760))
*plus ONM costs
   + cost_vom(i,v,r,t)
*plus fuel costs - assuming constant fuel prices here (model prices might be different)
   + heat_rate(i,v,r,t) * fuel_price(i,r,t)
;

lcoe_nopol(i,v,r,t,rscbin) = lcoe(i,v,r,t,rscbin) ;
lcoe_nopol(i,v,r,t,rscbin)$(valcap(i,v,r,t)$ivt(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)) =
* cost of capacity divided by generation
    (crf(t) * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t) + m_rsc_dat(r,i,rscbin,"cost")$newv(v)) + cost_fom(i,v,r,t))
    / gen_rsc(i,v,r,t)

*plus ONM costs
    + cost_vom_rr(i,v,r,t)
;

lcoe_fullpol(i,v,r,t,rscbin) = lcoe(i,v,r,t,rscbin) ;
lcoe_fullpol(i,v,r,t,rscbin)$(valcap(i,v,r,t)$ivt(i,v,t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$gen_rsc(i,v,r,t)) =
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

load_frac_rt(r,t)$sum{(rr,h), LOAD.l(rr,h,t) } = sum{h, hours(h) * LOAD.l(r,h,t) }/ sum{(rr,h), hours(h) * LOAD.l(rr,h,t) } ;

*Load and operating reserve prices are $/MWh, and reserve margin price is $/kW-yr
reqt_price('load','na',r,h,t)$[rfeas(r)$tmodel_new(t)] = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_supply_demand_balance.m(r,h,t) / hours(h) ;
reqt_price('res_marg','na',r,szn,t)$[rfeas(r)$tmodel_new(t)] = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_reserve_margin.m(r,szn,t) / 1000 ;
reqt_price('res_marg_ann','na',r,'ann',t) = sum{szn, reqt_price('res_marg','na',r,szn,t) } ;
reqt_price('oper_res',ortype,r,h,t)$[rfeas(r)$tmodel_new(t)] = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_OpRes_requirement.m(ortype,r,h,t) / hours(h) ;
reqt_price('state_rps',RPSCat,r,'ann',t)$[rfeas(r)$tmodel_new(t)] = (1 / cost_scale) * (1 / pvf_onm(t)) * sum{st$r_st(r,st), eq_REC_Requirement.m(RPSCat,st,t) } ;
reqt_price('annual_cap',e,r,'ann',t)$[rfeas(r)$tmodel_new(t)] = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_annual_cap.m(e,t) ;
reqt_price('nat_rps','na',r,'ann',t)$(rfeas(r)$tmodel_new(t)) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_national_gen.m(t) ;
reqt_price('nat_rps_res_marg','na',r,szn,t)$(rfeas(r)$tmodel_new(t)) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_national_rps_resmarg.m(r,szn,t) / 1000 ;
reqt_price('nat_rps_res_marg_ann','na',r,'ann',t) = sum{szn, reqt_price('nat_rps_res_marg','na',r,szn,t) } ;

*Load and operating reserve quantities are MWh, and reserve margin quantity is kW
reqt_quant('load','na',r,h,t)$[rfeas(r)$tmodel_new(t)] = hours(h) * LOAD.l(r,h,t) ;
reqt_quant('res_marg','na',r,szn,t)$[rfeas(r)$tmodel_new(t)] = (peakdem_static_szn(r,szn,t) + PEAK_FLEX.l(r,szn,t)) * (1+prm(r,t)) * 1000 ;
reqt_quant('res_marg_ann','na',r,'ann',t) = sum{szn, reqt_quant('res_marg','na',r,szn,t) } ;
reqt_quant('oper_res',ortype,r,h,t)$[rfeas(r)$tmodel_new(t)] =
    hours(h) * (
        orperc(ortype,"or_load") * LOAD.l(r,h,t)
      + orperc(ortype,"or_wind") * sum{(i,v)$[wind(i)$valgen(i,v,r,t)],
          GEN.l(i,v,r,h,t) }
      + orperc(ortype,"or_pv")   * sum{(i,v)$[pv(i)$valcap(i,v,r,t)],
           CAP.l(i,v,r,t) }$dayhours(h)
    ) ;
reqt_quant('state_rps',RPSCat,r,'ann',t)$[rfeas(r)$tmodel_new(t)] =
    sum{st$r_st(r,st),RecPerc(RPSCat,st,t)} *sum{h,hours(h) *( (LOAD.l(r,h,t) - can_exports_h(r,h,t)) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) })} ;
reqt_quant('nat_rps','na',r,'ann',t)$(rfeas(r)$tmodel_new(t)) =
    national_rps_frac(t) * (
* if Sw_GenMandate = 1, then apply the fraction to the bus bar load
    (
    sum{h, LOAD.l(r,h,t) * hours(h) }
    + sum{(rr,h,trtype)$[rfeas(rr)$routes(rr,r,trtype,t)], (tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype) * hours(h)) }
    + sum{(i,v,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)], STORAGE_IN.l(i,v,r,h,src,t) * hours(h) }
    - sum{(i,v,h)$[valcap(i,v,r,t)$storage_no_csp(i)], GEN.l(i,v,r,h,t) * hours(h) }
    )$[Sw_GenMandate = 1]

* if Sw_GenMandate = 2, then apply the fraction to the end use load
    + (sum{h,
        hours(h) *
        ( (LOAD.l(r,h,t) - can_exports_h(r,h,t)) * (1.0 - distloss) - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) })
       })$[Sw_GenMandate = 2]
    ) ;
reqt_quant('annual_cap',e,r,'ann',t)$[rfeas(r)$tmodel_new(t)] = emit_cap(e,t) * load_frac_rt(r,t) ;
reqt_quant('nat_rps_res_marg','na',r,szn,t)$(rfeas(r)$tmodel_new(t)) = national_rps_frac(t) * peakdem_static_szn(r,szn,t) * (1+prm(r,t)) * 1000 ;
reqt_quant('nat_rps_res_marg_ann','na',r,'ann',t) = sum{szn, reqt_quant('nat_rps_res_marg','na',r,szn,t) } ;

load_rt(r,t)$[rfeas(r)$tmodel_new(t)] = sum{h, hours(h) * load_exog(r,h,t) } ;

*========================================
* RPS AND CES CREDIT OUTPUTS
*========================================

rec_outputs(RPSCat,i,st,ast,t)$[stfeas(st)$stfeas(ast)$tmodel_new(t)] = RECS.l(RPSCat,i,st,ast,t) ;

*========================================
* FUEL PRICES AND QUANTITIES
*========================================

* The marginal biomass fuel price is derived from the linear program constraint marginals
* Case 1: the resource of a biomass class is NOT exhausted, i.e., BIOUSED.l(bioclass) < biosupply(bioclass)
*    Marginal Biomass Price = eq_bioused.m
* Case 2: the resource of one or more biomass classes ARE exhausted, i.e., BIOUSED.l(bioclass) = biosupply(bioclass)
*    Marginal Biomass Price = maximum difference between eq_bioused.m and eq_biousedlimit.m(bioclass) across all biomass classes in a region

repbioprice(r,t)$[tmodel_new(t)$rfeas(r)] = max{0, smax{bioclass$BIOUSED.l(bioclass,r,t), eq_bioused.m(r,t) - eq_biousedlimit.m(bioclass,r,t)} } / pvf_onm(t) ;

* 1e9 converts from MMBtu to Quads
repgasquant(cendiv,t)$[(Sw_GasCurve = 0 or Sw_GasCurve = 3)$tmodel_new(t)$cdfeas(cendiv)] =
    sum{(gb,h), GASUSED.l(cendiv,gb,h,t) * hours(h) } * gas_scale/ 1e9 ;

repgasquant(cendiv,t)$[(Sw_GasCurve = 1 or Sw_GasCurve = 2)$tmodel_new(t)$cdfeas(cendiv)] =
    sum{(i,v,r,h)$[rfeas(r)$r_cendiv(r,cendiv)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t)
       } / 1e9 ;

repgasquant_r(r,t)$[tmodel_new(t)$rfeas(r)] =
    sum{(i,v,h)$[rfeas(r)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)],
          hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t)
       } / 1e9 ;

repgasquant_nat(t)$tmodel_new(t) = sum{cendiv$cdfeas(cendiv), repgasquant(cendiv,t) } ;

*for reported gasprice (not that used to compute system costs)
*scale back to $ / mmbtu
repgasprice(cendiv,t)$[(Sw_GasCurve = 0)$tmodel_new(t)$cdfeas(cendiv)$repgasquant(cendiv,t)] =
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

repgasprice(cendiv,t)$[(Sw_GasCurve = 1)$tmodel_new(t)$cdfeas(cendiv)$repgasquant(cendiv,t)] =
    sum{rb$[rfeas(rb)$r_cendiv(rb,cendiv)], repgasprice_r(rb,t) * repgasquant_r(rb,t) } / repgasquant(cendiv,t) ;

repgasprice_nat(t)$[tmodel_new(t)$sum{cendiv$cdfeas(cendiv), repgasquant(cendiv,t) }] =
    sum{cendiv$cdfeas(cendiv), repgasprice(cendiv,t) * repgasquant(cendiv,t) }
    / sum{cendiv$cdfeas(cendiv), repgasquant(cendiv,t) } ;

*========================================
* NATURAL GAS FUEL COSTS
*========================================

gasshare_ba(r,cendiv,t)$[rfeas(r)$r_cendiv(r,cendiv)$tmodel_new(t)$repgasquant(cendiv,t)] =
                 repgasquant_r(r,t) / repgasquant(cendiv,t) ;

gasshare_cendiv(cendiv,t)$[sum{cendiv2,repgasquant(cendiv2,t)}] = repgasquant(cendiv,t) / sum{cendiv2,repgasquant(cendiv2,t)} ;

gascost_cendiv(cendiv,t)$[cdfeas(cendiv)$tmodel_new(t)] =
*cost of natural gas for Sw_GasCurve = 2 (static natural gas prices)
              + sum{(i,v,r,h)$[rfeas(r)$r_cendiv(r,cendiv)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)
                              $(not bio(i))$(not cofire(i))$(Sw_GasCurve = 2)],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN.l(i,v,r,h,t) }

*cost of natural gas for Sw_GasCurve = 0 (census division supply curves natural gas prices)
              + sum{gb, sum{h,hours(h) * GASUSED.l(cendiv,gb,h,t) } * gasprice(cendiv,gb,t)
                   }$(Sw_GasCurve = 0)

*cost of natural gas for Sw_GasCurve = 3 (national supply curve for natural gas prices with census division multipliers)
              + sum{(h,gb)$cdfeas(cendiv), hours(h) * GASUSED.l(cendiv,gb,h,t)
                   * gasadder_cd(cendiv,t,h) + gasprice_nat_bin(gb,t)
                   }$(Sw_GasCurve = 3)
*cost of natural gas for Sw_GasCurve = 1 (national and census division supply curves for natural gas prices)
*first - anticipated costs of gas consumption given last year's amount
              + (sum{(i,v,r,h)$[valgen(i,v,r,t)$gas(i)$rfeas(r)$cdfeas(cendiv)],
                   gasmultterm(cendiv,t) * szn_adj_gas(h) * cendiv_weights(r,cendiv) *
                   hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t) }
*second - adjustments based on changes from last year's consumption at the regional and national level
              + sum{(fuelbin)$cdfeas(cendiv),
                   gasbinp_regional(fuelbin,cendiv,t) * VGASBINQ_REGIONAL.l(fuelbin,cendiv,t) }

              + sum{(fuelbin),
                   gasbinp_national(fuelbin,t) * VGASBINQ_NATIONAL.l(fuelbin,t) } * gasshare_cendiv(cendiv,t)

              )$[Sw_GasCurve = 1];



*=========================
* GENERATION
*=========================

gen_out(i,r,h,t) = sum{v$valgen(i,v,r,t), GEN.l(i,v,r,h,t) - sum{src, STORAGE_IN.l(i,v,r,h,src,t) } } ;
gen_out_ann(i,r,t) = sum{h, gen_out(i,r,h,t) * hours(h) } ;
gen_icrt(i,v,r,t) = sum{h, GEN.l(i,v,r,h,t) * hours(h) } ;
gen_icrt_uncurt(i,v,r,t)$vre(i) = sum{(rr,h)$[cap_agg(r,rr)$valcap(i,v,rr,t)], m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,t) * hours(h) } ;
stor_inout(i,v,r,t,"in")$storage(i) = sum{(h,src), STORAGE_IN.l(i,v,r,h,src,t) * hours(h) } ;
stor_inout(i,v,r,t,"out")$storage(i) = gen_icrt(i,v,r,t) ;
stor_in(i,v,r,h,t)$storage(i) = sum{src, STORAGE_IN.l(i,v,r,h,src,t) } ;
stor_out(i,v,r,h,t)$storage(i) = GEN.l(i,v,r,h,t)$storage(i) ;
stor_level(i,v,r,h,t)$storage(i) = STORAGE_LEVEL.l(i,v,r,h,t) ;

*=====================================================================
* WATER ACCOUNTING, CAPACITY, NEW CAPACITY, AND RETIRED CAPACITY
*=====================================================================
water_withdrawal_ivrt(i,v,r,t)$valgen(i,v,r,t) = sum{h$valgen(i,v,r,t), WAT.l(i,v,"with",r,h,t) } ;
water_consumption_ivrt(i,v,r,t)$valgen(i,v,r,t) = sum{h$valgen(i,v,r,t), WAT.l(i,v,"cons",r,h,t) } ;

watcap_ivrt(i,v,r,t)$valcap(i,v,r,t) = WATCAP.l(i,v,r,t) ;
watcap_out(i,r,t)$valcap_irt(i,r,t) = sum{v$valcap(i,v,r,t), WATCAP.l(i,v,r,t) } ;

watcap_new_ivrt(i,v,r,t)$valcap(i,v,r,t) = (8760/1E6) * sum{w$[i_w(i,w)], water_rate(i,w,r) * ( INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) ) } ;
watcap_new_out(i,r,t)$valcap_irt(i,r,t) = (8760/1E6) * sum{(w,v)$[i_w(i,w)$valinv(i,v,r,t)], water_rate(i,w,r) * ( INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) ) } ;
watcap_new_ann_out(i,v,r,t)$watcap_new_out(i,r,t) = watcap_new_out(i,r,t) / (yeart(t) - sum(tt$tprev(t,tt), yeart(tt))) ;

watret_out(i,r,t)$[(not tfirst(t))$valcap_irt(i,r,t)] = sum{tt$tprev(t,tt), watcap_out(i,r,tt)} - watcap_out(i,r,t) + watcap_new_out(i,r,t) ;
watret_out(i,r,t)$[(abs(watret_out(i,r,t)) < 1e-6)] = 0 ;
watret_ann_out(i,v,r,t)$watret_out(i,r,t) = watret_out(i,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;

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

losses_ann('storage',t) = sum{(i,v,r,h,src)$[valcap(i,v,r,t)$storage_no_csp(i)$rfeas(r)], STORAGE_IN.l(i,v,r,h,src,t) * hours(h) }
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

cap_deg_icrt(i,v,r,t)$valcap(i,v,r,t) = CAP.l(i,v,r,t) / ilr(i) ;
cap_icrt(i,v,r,t)$[not (upv(i) or dupv(i) or wind(i))] = cap_deg_icrt(i,v,r,t) ;
cap_icrt(i,v,r,t)$[upv(i) or dupv(i) or wind(i)] = (m_capacity_exog(i,v,r,t)$tmodel_new(t) + sum{tt$[inv_cond(i,v,r,t,tt)$(tmodel(tt) or tfix(tt))],
                                          INV.l(i,v,r,tt) + INV_REFURB.l(i,v,r,tt)$[refurbtech(i)$Sw_Refurb]}) / ilr(i) ;
cap_out(i,r,t)$tmodel_new(t) = sum{v$valcap(i,v,r,t), cap_icrt(i,v,r,t) } ;


*=========================
* NEW CAPACITY
*=========================

cap_new_out(i,r,t)$[not tfirst(t)] = sum{v$valinv(i,v,r,t), INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t) } / ilr(i) ;
cap_new_out("distPV",r,t)$[not tfirst(t)] = cap_out("distPV",r,t) - sum{tt$tprev(t,tt), cap_out("distPV",r,tt) } ;
cap_new_ann_out(i,r,t)$cap_new_out(i,r,t) = cap_new_out(i,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;
cap_new_bin_out(i,v,r,t,rscbin)$[rsc_i(i)$valinv(i,v,r,t)] = Inv_RSC.l(i,v,r,rscbin,t) / ilr(i) ;
cap_new_bin_out(i,v,r,t,"bin1")$[(not rsc_i(i))$valinv(i,v,r,t)] = INV.l(i,v,r,t)  /ilr(i) ;
cap_new_icrt(i,v,r,t)$[(not tfirst(t))$valinv(i,v,r,t)] = (INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)) / ilr(i) ;
cap_new_icrt_refurb(i,v,r,t)$valinv(i,v,r,t) = INV_REFURB.l(i,v,r,t) / ilr(i) ;

*=========================
* AVAILABLE CAPACITY
*=========================
cap_avail(i,r,t,rscbin)$(rsc_i(i)$rfeas_cap(r)$m_rscfeas(r,i,rscbin)) =
  m_rsc_dat(r,i,rscbin,"cap") - sum{(ii,v,tt)$[valinv(ii,v,r,tt)$tprev(t,tt)$(rsc_agg(i,ii))],
         INV_RSC.l(ii,v,r,rscbin,tt) * resourcescaler(ii) } ;


*=========================
* UPGRADED CAPACITY
*=========================

cap_upgrade(i,r,t)$[rfeas(r)$upgrade(i)] = sum{v, UPGRADES.l(i,v,r,t) } ;

*=========================
* RETIRED CAPACITY
*=========================

ret_out(i,r,t)$(not tfirst(t)) = sum{tt$tprev(t,tt), cap_out(i,r,tt)} - cap_out(i,r,t) + cap_new_out(i,r,t) + cap_upgrade(i,r,t) ;
ret_out(i,r,t)$(abs(ret_out(i,r,t)) < 1e-6) = 0 ;
ret_ann_out(i,r,t)$ret_out(i,r,t) = ret_out(i,r,t) / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;

*==================================
* BINNED STORAGE CAPACITY
*==================================

cap_sdbin_out(i,r,szn,sdbin,t) = sum{v, CAP_SDBIN.l(i,v,r,szn,sdbin,t)} ;

*==================================
* CAPACITY CREDIT AND FIRM CAPACITY
*==================================

cc_all_out(i,v,rr,szn,t) =
    cc_int(i,v,rr,szn,t)$[(vre(i) or storage(i))$valcap(i,v,rr,t)] +
    m_cc_mar(i,rr,szn,t)$[(vre(i) or storage(i))$valinv(i,v,rr,t)]
;

cap_new_cc(i,r,szn,t)$(vre(i) or storage(i)) = sum{v$ivt(i,v,t),cap_new_icrt(i,v,r,t) } ;
cc_new(i,r,szn,t)$cap_new_cc(i,r,szn,t) = sum{v$ivt(i,v,t), cc_all_out(i,v,r,szn,t) } ;

cap_firm(i,r,szn,t)$tmodel_new(t) =
      sum{v$[(not vre(i))$(not hydro(i))$(not storage(i))], CAP.l(i,v,r,t) }
    + sum{rr$[(vre(i) or csp(i))$cap_agg(r,rr)], cc_old(i,rr,szn,t) }
    + sum{(v,rr)$[cap_agg(r,rr)$(vre(i) or csp(i))$valinv(i,v,rr,t)],
         m_cc_mar(i,rr,szn,t) * (INV.l(i,v,rr,t) + INV_REFURB.l(i,v,rr,t)$[refurbtech(i)$Sw_Refurb]) }
    + sum{(v,rr)$[(vre(i) or csp(i))$cap_agg(r,rr)],
            cc_int(i,v,rr,szn,t) * CAP.l(i,v,rr,t) }
    + sum{(rr)$[(vre(i) or csp(i))$cap_agg(r,rr)],
            cc_excess(i,rr,szn,t) }
    + sum{v$[hydro_nd(i)],
         GEN.l(i,v,r,"h3",t) }
    + sum{v$[hydro_d(i)],
         CAP.l(i,v,r,t) * cap_hyd_szn_adj(i,szn,r) }
    + sum{(v,sdbin)$storage_no_csp(i), CAP_SDBIN.l(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin) } ;

* Capacity trading to meet PRM
captrade(r,rr,trtype,szn,t)$tmodel_new(t) = PRMTRADE.l(r,rr,trtype,szn,t) ;

*========================================
* REVENUE LEVELS
*========================================

revenue('load',i,r,t)$sum{v, valgen(i,v,r,t) } = sum{(v,h)$valgen(i,v,r,t),
  GEN.l(i,v,r,h,t) * hours(h) * reqt_price('load','na',r,h,t) } ;

*revenue from storage charging (storage charging from curtailment recovery does not have a cost)
revenue('charge',i,r,t)$[storage_no_csp(i)$sum{v, valgen(i,v,r,t) }] = - sum{(v,h,src)$valgen(i,v,r,t),
  ( (1 - curt_stor(i,v,r,h,src,t)) * STORAGE_IN.l(i,v,r,h,src,t)
  ) * hours(h) * reqt_price('load','na',r,h,t) } ;

revenue('arbitrage',i,r,t)$[storage_no_csp(i)$sum{v, valinv(i,v,r,t) }] =  hourly_arbitrage_value(i,r,t) * sum{v, INV.l(i,v,r,t)} ;

revenue('res_marg',i,r,t)$sum{v, valgen(i,v,r,t) } = sum{szn,
  cap_firm(i,r,szn,t) * reqt_price('res_marg','na',r,szn,t) * 1000 } ;

revenue('oper_res',i,r,t)$sum{v, valgen(i,v,r,t) } = sum{(ortype,v,h)$valgen(i,v,r,t),
  OPRES.l(ortype,i,v,r,h,t) * hours(h) * reqt_price('oper_res',ortype,r,h,t) } ;

revenue('rps',i,r,t)$sum{v, valgen(i,v,r,t) } =
  sum{(v,h,RPSCat)$[valgen(i,v,r,t)$sum{st$r_st(r,st), RecTech(RPSCat,st,i,t) }],
      GEN.l(i,v,r,h,t) * sum{st$r_st(r,st), RPSTechMult(RPSCat,i,st) } * hours(h) * reqt_price('state_rps',RPSCat,r,'ann',t) } ;

revenue_nat(rev_cat,i,t) = sum{r$rfeas(r), revenue(rev_cat,i,r,t) } ;

revenue_en(rev_cat,i,r,t)$[sum{(v,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t)}$(not vre(i))] =
  revenue(rev_cat,i,r,t) / sum{(v,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t) * hours(h) } ;

revenue_en(rev_cat,i,r,t)$[sum{(v,rr,h)$[cap_agg(r,rr)$valcap(i,v,rr,t)], m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,t) }$vre(i)] =
  revenue(rev_cat,i,r,t) / sum{(v,rr,h)$[cap_agg(r,rr)$valcap(i,v,rr,t)],
      m_cf(i,v,rr,h,t) * CAP.l(i,v,rr,t) * hours(h) } ;

revenue_en_nat(rev_cat,i,t)$[sum{(v,r,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t) }] =
  revenue_nat(rev_cat,i,t) / sum{(v,r,h)$valgen(i,v,r,t), GEN.l(i,v,r,h,t) * hours(h) } ;

revenue_cap(rev_cat,i,r,t)$[sum{rr$[cap_agg(r,rr)$valcap_irt(i,rr,t)], cap_out(i,rr,t) }] =
  revenue(rev_cat,i,r,t) / sum{rr$[cap_agg(r,rr)$valcap_irt(i,rr,t)], cap_out(i,rr,t) } ;

revenue_cap_nat(rev_cat,i,t)$[sum{r$valcap_irt(i,r,t), cap_out(i,r,t) }] =
  revenue_nat(rev_cat,i,t) / sum{r$valcap_irt(i,r,t), cap_out(i,r,t) } ;

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

*==================================
* National RE Constraint Marginals
*==================================

RE_gen_price_nat(t)$tmodel_new(t) = (1/cost_scale) * crf(t) * eq_national_gen.m(t);

RE_cap_price_r(r,szn,t)$tmodel_new(t) = (1/cost_scale) * crf(t) * eq_national_rps_resmarg.m(r,szn,t) ;

RE_cap_price_nat(szn,t)$tmodel_new(t) = (1/cost_scale) * crf(t) * sum(r,eq_national_rps_resmarg.m(r,szn,t) * peakdem_static_szn(r,szn,t)) /
                                           sum(r,peakdem_static_szn(r,szn,t)) ;

*=========================
* [i,v,r,t]-level capital expenditures (for retail rate calculations)
*=========================
capex_ivrt(i,v,r,t) = INV.l(i,v,r,t) * (cost_cap_fin_mult_no_credits(i,r,t) * cost_cap(i,t) )
                      + sum{(rscbin),Inv_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * cost_cap_fin_mult_no_credits(i,r,t) }
                      + INV_REFURB.l(i,v,r,t) * (cost_cap_fin_mult_no_credits(i,r,t) * cost_cap(i,t));

*=========================
* BA-Level SYSTEM COST: Capital
*=========================

* REPLICATION OF THE OBJECTIVE FUNCTION

systemcost_ba("inv_investment_capacity_costs",r,t)$[rfeas_cap(r)$tmodel_new(t)] =
*investment costs (without the subtraction of any PTC value)
                sum{(i,v)$valinv(i,v,r,t),
                   INV.l(i,v,r,t) * (cost_cap_fin_mult(i,r,t) * cost_cap(i,t) ) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
              + sum{(i,v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$sccapcosttech(i)],
                   Inv_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult(i,r,t) }
*plus cost of upgrades
              + sum{(i,v)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades],
                   cost_upgrade(i,t) * cost_cap_fin_mult(i,r,t) * UPGRADES.l(i,v,r,t) }
;

systemcost_ba("inv_investment_capacity_costs_noITC",r,t)$[rfeas_cap(r)$tmodel_new(t)] =
*investment costs (without the subtraction of any PTC value)
                   sum{(i,v)$valinv(i,v,r,t),
                        INV.l(i,v,r,t) * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t) ) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
              + sum{(i,v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$sccapcosttech(i)],
                   Inv_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult_noITC(i,r,t) }
;

systemcost_ba("inv_ptc_payments_negative",r,t)$[rfeas_cap(r)$tmodel_new(t)] =
*ptc payment costs
                  - sum{(i,v)$valinv(i,v,r,t),
                        INV.l(i,v,r,t) * (ptc_unit_value(i,v,r,t) * sum{h, hours(h)* m_cf(i,v,r,h,t)
                         *(1 - sum{rr$cap_agg(rr,r), curt_int(i,rr,h,t) + curt_marg(i,rr,h,t) }$(not hydro(i))) } ) }
;

systemcost_ba("inv_investment_spurline_costs_rsc_technologies",r,t)$[rfeas_cap(r)$tmodel_new(t)] =
*costs of rsc spur line investment
*Note that cost_cap for hydro, pumped-hydro, and geo techs are zero
*but hydro and geo rsc_fin_mult is equal to the same value as cost_cap_fin_mult
*(Note that exclusions of geo and hydro here deviates from the objective function structure)
              + sum{(i,v,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$(not sccapcosttech(i))],
*investment in resource supply curve technologies
                   Inv_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult(i,r,t) }
;

systemcost_ba("inv_investment_refurbishment_capacity",r,t)$[rfeas_cap(r)$tmodel_new(t)] =
*costs of refurbishments of RSC tech (without the subtraction of any PTC value)
              + sum{(i,v)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                        (cost_cap_fin_mult(i,r,t) * cost_cap(i,t)) * INV_REFURB.l(i,v,r,t) }
;

systemcost_ba("inv_investment_refurbishment_capacity_noITC",r,t)$[rfeas_cap(r)$tmodel_new(t)] =
*costs of refurbishments of RSC tech (without the subtraction of any PTC value)
              + sum{(i,v)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                        (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t)) * INV_REFURB.l(i,v,r,t) }
;

systemcost_ba("inv_ptc_payments_negative_refurbishments",r,t)$[rfeas_cap(r)$tmodel_new(t)] =
*costs of ptc for refurbished techs
              - sum{(i,v)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                        ptc_unit_value(i,v,r,t) * sum{h, hours(h)* m_cf(i,v,r,h,t)
                         *(1 - sum{rr$cap_agg(rr,r), curt_int(i,rr,h,t) + curt_marg(i,rr,h,t) }$(not hydro(i))) } * INV_REFURB.l(i,v,r,t) }
;

systemcost_ba("inv_transmission_line_investment",r,t)$[rfeas(r)$tmodel_new(t)]  =
*costs of transmission lines
              + sum{(rr,trtype)$[routes(r,rr,trtype,t)$routes_inv(r,rr,trtype,t)],
                        ((cost_tranline(r) + cost_tranline(rr)) / 2) * distance(r,rr,trtype) * (INVTRAN.l(r,rr,t,trtype) + trancap_fut(r,rr,"certain",t,trtype))  }
;

systemcost_ba("inv_substation_investment_costs",r,t)$[rfeas(r)$tmodel_new(t)]  =
*costs of substations
              + sum{(vc)$(rfeas(r)$tscfeas(r,vc)),
                        cost_transub(r,vc) * INVSUBSTATION.l(r,vc,t) }
;

systemcost_ba("inv_interconnection_costs",r,t)$[rfeas(r)$tmodel_new(t)]  =
*cost of back-to-back AC-DC-AC interties
*conditional here that the interconnects must be different
              + sum{(rr)$[routes_inv(r,rr,"DC",t)$(t.val>2020)$(INr(r) <> INr(rr))],
                        cost_trandctie * INVTRAN.l(r,rr,t,"DC") }
;

systemcost_ba("inv_investment_water_access",r,t)$[rfeas_cap(r)$tmodel_new(t)] =
*cost of water access
              + (8760/1E6) * sum{ (i,v,w)$[i_w(i,w)$valinv(i,v,r,t)], sum{wst$i_wst(i,wst), m_watsc_dat(wst,"cost",r,t)} * water_rate(i,w,r) *
                        ( INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)$[refurbtech(i)$Sw_Refurb] ) }
;

*===============
* BA-Level SYSTEM COST: Operational (the op_ prefix is used by the retail rate module to identify which costs are operational costs)
*===============

systemcost_ba("op_vom_costs",r, t)$[rfeas(r)$tmodel_new(t)]  =
*variable O&M costs
              sum{(i,v,h)$[rfeas(r)$valgen(i,v,r,t)$cost_vom(i,v,r,t)],
                   hours(h) * cost_vom(i,v,r,t) * GEN.l(i,v,r,h,t) }
;

systemcost_ba("op_fom_costs",r,t)$[rfeas_cap(r)$tmodel_new(t)]  =
*fixed O&M costs
              + sum{(i,v)$[valcap(i,v,r,t)],
                   cost_fom(i,v,r,t) * CAP.l(i,v,r,t) }
;

systemcost_ba("op_operating_reserve_costs",r,t)$[rfeas(r)$tmodel_new(t)]  =
*operating reserve costs
*only applied to reg reserves because cost of providing other reserves is zero...
              + sum{(i,v,h,ortype)$[rfeas(r)$valgen(i,v,r,t)$cost_opres(i)$sameas(ortype,"reg")],
                   hours(h) * cost_opres(i) * OpRes.l(ortype,i,v,r,h,t) }
;

*systemcost_ba("op_ngfuelcosts_objfn",r,t)$tmodel_new(t) =
*         sum{cendiv$r_cendiv(r,cendiv), gascost_cendiv(cendiv,t) * gasshare_ba(r,cendiv,t) } ;

systemcost_ba("op_fuelcosts_objfn",r,t)$[rfeas(r)$tmodel_new(t)]  =
*cost of coal and nuclear fuel (except coal used for cofiring)
              + sum{(i,v,h)$[rfeas(r)$valgen(i,v,r,t)$(not gas(i))$heat_rate(i,v,r,t)
                              $(not bio(i))$(not cofire(i))],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN.l(i,v,r,h,t) }

*cofire coal consumption - cofire bio consumption already accounted for in accounting of BIOUSED
              + sum{(i,v,h)$[rfeas(r)$valgen(i,v,r,t)$cofire(i)$heat_rate(i,v,r,t)],
                   (1-bio_cofire_perc) * hours(h) * heat_rate(i,v,r,t)
                   * fuel_price("coal-new",r,t) * GEN.l(i,v,r,h,t) }

*cost of natural gas fuel
              + sum{cendiv$r_cendiv(r,cendiv), gascost_cendiv(cendiv,t) * gasshare_ba(r,cendiv,t) }

*biofuel consumption
              + sum{(bioclass)$rfeas(r),
                   biopricemult(r,bioclass,t) * BIOUSED.l(bioclass,r,t) * biosupply(r,"cost",bioclass) }
;

systemcost_ba("op_international_hurdle_rate",r,t)$[rfeas(r)$tmodel_new(t)]  =
*plus international hurdle costs
              + sum{(rr,h,trtype)$[routes(r,rr,trtype,t)$cost_hurdle(r,rr)],
                   cost_hurdle(r,rr) * hours(h) * FLOW.l(r,rr,h,t,trtype)  }
;

systemcost_ba("op_emissions_taxes",r,t)$[rfeas(r)$tmodel_new(t)]  =
*plus any taxes on emissions
              + sum{(e), EMIT.l(e,r,t) * emit_tax(e,r,t) }
;

ACP_State_RHS(st,t)$(stfeas(st)$tmodel_new(t)) = sum{(r,h)$[rfeas(r)$r_st(r,st)],
                                                      hours(h) *
                                                      ( (LOAD.l(r,h,t) - can_exports_h(r,h,t)) / distloss - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) })} ;
ACP_portion(r,t)$(rfeas(r)$tmodel_new(t)) = sum{h,hours(h) *( (LOAD.l(r,h,t) - can_exports_h(r,h,t)) / distloss - sum{v$valgen("distpv",v,r,t), GEN.l("distpv",v,r,h,t) })} / sum{st$r_st(r,st), ACP_State_RHS(st,t)} ;

systemcost_ba("op_acp_compliance_costs",r,t)$[rfeas(r)$tmodel_new(t)]  =
*plus ACP purchase costs
              + sum{(st)$[stfeas(st)$r_st(r,st)], ACP_portion(r,t)* sum{RPSCat, acp_price(st,t) * ACP_Purchases.l(RPSCat,st,t) } }$(yeart(t)>=RPS_StartYear)
;

*For bulk system costs present value as of model year, capital costs are unchanged,
*while operation costs use pvf_onm_undisc
systemcost_ba_bulk(sys_costs,r,t) = systemcost_ba(sys_costs,r,t) ;
systemcost_ba_bulk(sys_costs_op,r,t) = systemcost_ba(sys_costs_op,r,t) * pvf_onm_undisc(t) ;

systemcost_ba_bulk_ew(sys_costs,r,t) = systemcost_ba_bulk(sys_costs,r,t) ;
systemcost_ba_bulk_ew(sys_costs_op,r,t)$tlast(t) = systemcost_ba(sys_costs_op,r,t) ;


*=========================
* National System Cost
*=========================

systemcost(sys_costs,t) = sum{r, systemcost_ba(sys_costs,r,t) } ;
systemcost_bulk(sys_costs,t) = systemcost(sys_costs,t) ;
systemcost_bulk(sys_costs_op,t) = systemcost(sys_costs_op,t) * pvf_onm_undisc(t) ;

systemcost_bulk_ew(sys_costs,t) = systemcost_bulk(sys_costs,t) ;
systemcost_bulk_ew(sys_costs_op,t)$tlast(t) = systemcost(sys_costs_op,t) ;

* Federal tax expenditure calculation
tax_expenditure_itc(t) = systemcost("inv_investment_capacity_costs",t) - systemcost("inv_investment_capacity_costs_noITC",t) + systemcost("inv_investment_refurbishment_capacity",t) - systemcost("inv_investment_refurbishment_capacity_noITC",t) ;
tax_expenditure_ptc(t) = systemcost("inv_ptc_payments_negative",t) + systemcost("inv_ptc_payments_negative_refurbishments",t) ;

raw_inv_cost(t) = sum{sys_costs_inv, systemcost(sys_costs_inv,t) } ;
raw_op_cost(t) = sum{sys_costs_op, systemcost(sys_costs_op,t) } ;

*======================
* Error Check
*======================

error_check('z') = z.l - sum{t$tmodel(t), cost_scale *
                             (pvf_capital(t) * raw_inv_cost(t) + pvf_onm(t) * raw_op_cost(t))
*minus small penalty to move storage into shorter duration bins
                             - pvf_capital(t) * sum{(i,v,r,szn,sdbin)$[valcap(i,v,r,t)$storage_no_csp(i)], bin_penalty(sdbin) * CAP_SDBIN.l(i,v,r,szn,sdbin,t) }
*minus hourly arbitrage value of storage
                             - pvf_onm(t) * sum{(i,v,r)$[valinv(i,v,r,t)$storage_no_csp(i)],
                                  hourly_arbitrage_value(i,r,t) * INV.l(i,v,r,t) }
*minus retirement penalty
                             - pvf_onm(t) * sum{(i,v,r)$[valcap(i,v,r,t)$retiretech(i,v,r,t)],
                                  cost_fom(i,v,r,t) * retire_penalty * (CAP.l(i,v,r,t) - INV.l(i,v,r,t) - INV_REFURB.l(i,v,r,t)$[refurbtech(i)$Sw_Refurb]) }
*minus revenue from purchases of curtailed VRE
                             - pvf_onm(t) * sum{(r,h), CURT.l(r,h,t) * hours(h) * cost_curt(t) }$Sw_CurtMarket
                            } ;

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
tran_flow_detail(r,rr,h,t,trtype)$[(ord(r) < ord(rr))$tmodel_new(t)$routes(rr,r,trtype,t)] = hours(h) * (FLOW.l(r,rr,h,t,trtype) + FLOW.l(rr,r,h,t,trtype)) ;
tran_util_out(r,rr,t,trtype)$[tmodel_new(t)$tran_out(r,rr,t,trtype)] = tran_flow_out(r,rr,t,trtype) / (tran_out(r,rr,t,trtype) * 8760) ;

tran_util_nat_out(t,trtype)$[tmodel_new(t)$sum{(r,rr)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_out(r,rr,t,trtype) }] =
         sum{(r,rr)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_flow_out(r,rr,t,trtype) } / (sum{(r,rr)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_out(r,rr,t,trtype) } * 8760) ;

tran_util_nat2_out(t)$[tmodel_new(t)$sum{(r,rr,trtype)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_out(r,rr,t,trtype) }] =
         sum{(r,rr,trtype)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_flow_out(r,rr,t,trtype) } / (sum{(r,rr,trtype)$[rfeas(r)$rfeas(rr)$routes(r,rr,trtype,t)], tran_out(r,rr,t,trtype) } * 8760) ;

*==========================
* Expenditures Exchanged
*==========================

expenditure_flow('load',r,rr,t)$[tmodel_new(t)$sum{trtype, routes(r,rr,trtype,t) }] = sum{h, hours(h) * reqt_price('load','na',r,h,t) * sum{trtype, FLOW.l(r,rr,h,t,trtype) } } ;
*res_marg prices are in $/kW-yr but captrade is in MW, so multiply by 1000
expenditure_flow('res_marg_ann',r,rr,t)$[tmodel_new(t)$sum{trtype, routes(r,rr,trtype,t) }] = sum{szn, reqt_price('res_marg','na',r,szn,t) * 1000 * sum{trtype, captrade(r,rr,trtype,szn,t) } } ;
expenditure_flow('oper_res',r,rr,t)$[tmodel_new(t)$sum{trtype, routes(r,rr,trtype,t) }] = sum{(h,ortype), hours(h) * reqt_price('oper_res',ortype,r,h,t) * OPRES_FLOW.l(ortype,r,rr,h,t) } ;
*unlike for the three services above, use the destination price rather than the sending price for calculating RPS expenditure flows
expenditure_flow_rps(st,ast,t)$[tmodel_new(t)$(not sameas(st,ast))] = (1 / cost_scale) * (1 / pvf_onm(t)) * sum{RPSCat, eq_REC_Requirement.m(RPSCat,ast,t) * sum{i, RECS.l(RPSCat,i,st,ast,t) } } ;

*=========================
* Reduced Cost
*=========================
reduced_cost(i,v,r,t,"nobin","CAP")$valinv(i,v,r,t) = CAP.m(i,v,r,t)/(1000*cost_scale*pvf_capital(t)) ;
reduced_cost(i,v,r,t,"nobin","INV")$valinv(i,v,r,t) = INV.m(i,v,r,t)/(1000*cost_scale*pvf_capital(t)) ;
reduced_cost(i,v,r,t,rscbin,"INV_RSC")$(rsc_i(i)$valinv(i,v,r,t)$m_rscfeas(r,i,rscbin)) = INV_RSC.m(i,v,r,rscbin,t)/(1000*cost_scale*pvf_capital(t)) ;

*=========================
* Flexible load
*=========================
flex_load_out(flex_type,r,h,t) = FLEX.l(flex_type,r,h,t) ;
peak_load_adj(r,szn,t) = PEAK_FLEX.l(r,szn,t) ;

objfn_raw = z.l ;

$include e_powfrac_calc.gms

execute_unload "outputs%ds%rep_%fname%.gdx"
  reqt_price, reqt_quant, load_rt, RecTech, prm, rec_outputs,
  emit_r, emit_nat, repgasprice, repgasprice_r, repgasprice_nat, repgasquant_nat, repgasquant, repgasquant_r, repbioprice,
  gen_out, gen_out_ann, gen_icrt, gen_icrt_uncurt, cap_out, cap_new_ann_out, cap_new_bin_out, cap_sdbin_out, cap_new_icrt, cap_avail, cap_firm, ret_ann_out, cap_upgrade,
  m_capacity_exog, cap_icrt, cap_deg_icrt, ret_out, cap_new_out, cap_new_icrt_refurb, cap_iter, gen_iter, cap_firm_iter, curt_tot_iter,
  cap_new_cc, cc_new, gen_new_uncurt, curt_new, cost_cap, capex_ivrt,
  objfn_raw, lcoe, lcoe_nopol, lcoe_cf_act, flex_load_out, peak_load_adj,
  raw_inv_cost, raw_op_cost, pvf_capital, pvf_onm,
  systemcost, systemcost_bulk, systemcost_bulk_ew, error_check, cost_scale,
  invtran_out, tran_out, tran_mi_out, tran_flow_out, tran_util_out, tran_util_nat_out, tran_util_nat2_out,
  curt_out, curt_out_ann, curt_all_ann, curt_all_out, cc_all_out
  losses_tran_h, losses_ann, curt_rate, reduced_cost, emit_weighted, RE_cap_price_r, RE_cap_price_nat, RE_gen_price_nat, vre_cost_vom
  opRes_supply_h, opRes_supply, stor_inout, stor_in, stor_out, stor_level,
  revenue, revenue_nat, revenue_en, revenue_en_nat, revenue_cap, revenue_cap_nat,
  lcoe_built, lcoe_built_nat, lcoe_pieces, lcoe_pieces_nat, gen_ann_nat, sdbin_size,
  tax_expenditure_itc, tax_expenditure_ptc, systemcost_ba, systemcost_ba_bulk, systemcost_ba_bulk_ew, expenditure_flow, expenditure_flow_rps,
  powerfrac_upstream, powerfrac_downstream, captrade,
  rsc_dat, rsc_copy,
  water_withdrawal_ivrt, water_consumption_ivrt, watcap_ivrt, watcap_out, watcap_new_ivrt, watcap_new_out, watcap_new_ann_out, watret_out, watret_ann_out ;

*This file is used in the ReEDS-to-PLEXOS data translation
execute_unload 'inputs_case%ds%plexos_inputs.gdx' biosupply, cf_adj_t, cf_hyd, cap_hyd_szn_adj, forced_outage, h_szn, hierarchy, hours, hydmin, planned_outage,
                                                  degrade_annual, rfeas, r_rs, storage_duration, storage_eff, tranloss ;

* compress all gdx files
execute '=gdxcopy -V7C -Replace inputs_case%ds%*.gdx' ;
execute '=gdxcopy -V7C -Replace outputs%ds%*.gdx' ;

