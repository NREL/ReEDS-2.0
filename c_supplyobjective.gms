$ontext
No globals needed for this file
$offtext

scalar  cost_scale "scaling parameter for the objective function" /1/ ;

Equation
* objective function calculation
 eq_ObjFn                      "--$s-- Objective function calculation"
 eq_ObjFn_inv(t)               "--$s-- Calculation of investment component of the objective function"
 eq_Objfn_op(t)                "--$s-- Calculation of operations component of the objective function"
;

* note these are not restricited to positive domain 
Variable    Z        "--$-- total cost of operations and investment, scale varies based on cost_scale"
            Z_op(t)  "--$-- total cost of operations",
            Z_inv(t)  "--$-- total cost of operations"
;

* objective function is the sum over modeled years of the investment
* and operations components
eq_ObjFn.. Z =e= cost_scale * sum{t$tmodel(t), Z_inv(t) + Z_op(t) } ;

*=======================================================
* -- Investment component of the objective function --
*=======================================================

eq_ObjFn_inv(t)$tmodel(t)..

         Z_inv(t) 
         
         =e=
         
         pvf_capital(t) *
              
              (
* ---investment costs ---
                  + sum{(i,v,r)$valinv(i,v,r,t),
                      cost_cap_fin_mult(i,r,t) * cost_cap(i,t) * INV(i,v,r,t)
                      }

* ---ptc value ---
*subtract the present-value of any production tax credits of technologies with a m_cf.
*ptc_unit_value is the present-value of all PTC payments for 1 hour of operation at CF=1
                  - sum{(i,v,r)$[valinv(i,v,r,t)],
                      INV(i,v,r,t) * (
                          ptc_unit_value(i,v,r,t) *
                          sum{h, hours(h) * m_cf(i,v,r,h,t)
                          * (1 - sum{rr$cap_agg(rr,r), curt_int(i,rr,h,t)
                          + curt_marg(i,rr,h,t) }$(not hydro(i)))
                          } )
                      }

*subtract the present-value of any production tax credits of technologies without a m_cf.
*ptc_unit_value is the present-value of all PTC payments for 1 hour of operation at CF=1
                  - sum{(i,v,r,h)$[valinv(i,v,r,t)$valgen(i,v,r,t)$(not cf_tech(i))], 
                        ptc_unit_value(i,v,r,t) * GEN(i,v,r,h,t) * hours(h) }

* ---cost of upgrading---
                  + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades],
                         cost_upgrade(i,t) * cost_cap_fin_mult(i,r,t) * UPGRADES(i,v,r,t) }

* ---costs of resource supply curve spur line investment---
*Note that cost_cap for hydro, pumped-hydro, and geo techs are zero
*but hydro and geo rsc_fin_mult is equal to the same value as cost_cap_fin_mult
                  + sum{(i,v,r,rscbin)$[m_rscfeas(r,i,t,rscbin)$valinv(i,v,r,t)$rsc_i(i)],
                      m_rsc_dat(r,i,t,rscbin,"cost") * rsc_fin_mult(i,r,t) * Inv_RSC(i,v,r,rscbin,t) }

* ---cost of water access---
                  + [ (8760/1E6) * sum{ (i,v,w,r)$[i_w(i,w)$valinv(i,v,r,t)], sum{wst$i_wst(i,wst), 
                                     m_watsc_dat(wst,"cost",r,t) } * water_rate(i,w,r) *
                                        ( INV(i,v,r,t) + INV_REFURB(i,v,r,t)$[refurbtech(i)$Sw_Refurb] ) 
                                   }]$Sw_WaterMain

*slack variable to update water source type (wst) in the unit database
*Note that existing wst data is not consistent with availability of water source in the region
                  + sum{(wst,r)$[rfeas(r)], 1E6 * WATER_CAPACITY_LIMIT_SLACK(wst,r,t) }$[Sw_WaterMain$Sw_WaterCapacity]

* ---cost of refurbishments of RSC tech---
                  + sum{(i,v,r)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                      cost_cap_fin_mult(i,r,t) * cost_cap(i,t) * INV_REFURB(i,v,r,t)
                      }

*subtract the present-value of any production tax credits. ptc_unit_value is
*the present-value of all PTC payments for 1 hour of operation at CF=1
                  - sum{(i,v,r)$[Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
                      ptc_unit_value(i,v,r,t) * sum{h, hours(h) * m_cf(i,v,r,h,t)
                      * (1 - sum{rr$cap_agg(rr,r), curt_int(i,rr,h,t) + curt_marg(i,rr,h,t) }$(not hydro(i))) } * INV_REFURB(i,v,r,t)
                      }

* ---cost of transmission---
*costs of transmission lines
                  + sum{(r,rr,trtype)$routes_inv(r,rr,trtype,t),
                        transmission_line_capex(r,rr,trtype) * INVTRAN(r,rr,t,trtype) }

*costs of substations
                  + sum{(r,vc)$(rfeas(r)$tscfeas(r,vc)),
                        cost_transub(r,vc) * InvSubstation(r,vc,t) }

*cost of LCC AC/DC converter stations (each LCC DC line implicitly has two, one on each end of the line)
                  + sum{(r,rr)$routes_inv(r,rr,"DC",t),
                        cost_acdc_lcc * 2 * INVTRAN(r,rr,t,"DC") }

*cost of VSC AC/DC converter stations
                  + sum{r$rfeas(r),
                        cost_acdc_vsc * INV_CONVERTER(r,t) }

* ---storage capacity credit---
*small cost penalty to incentivize solver to fill shorter-duration bins first
                  + sum{(i,v,r,szn,sdbin)$[valcap(i,v,r,t)$(storage_standalone(i) or pvb(i) or hyd_add_pump(i))], 
                         bin_penalty(sdbin) * CAP_SDBIN(i,v,r,szn,sdbin,t) }

*cost of capacity upsizing
                  + sum{(i,v,r,rscbin)$allow_cap_up(i,v,r,rscbin,t),
                            cost_cap_fin_mult(i,r,t) * INV_CAP_UP(i,v,r,rscbin,t) * cost_cap_up(i,v,r,rscbin,t) }

*cost of energy upsizing
                  + sum{(i,v,r,rscbin)$allow_ener_up(i,v,r,rscbin,t),
                            cost_cap_fin_mult(i,r,t) * INV_ENER_UP(i,v,r,rscbin,t) * cost_ener_up(i,v,r,rscbin,t) }

* ---H2 transport network investment costs---
                  + sum{(r,rr)$h2_routes(r,rr), cost_h2_transport(r,rr) * H2_TRANSPORT_INV(rr,r,t) }$Sw_H2_Transport

*end to multiplier by pvf_capital
            )
;

*=======================================================
* -- Operational component of the objective function --
*=======================================================

eq_Objfn_op(t)$tmodel(t)..

         Z_op(t)

         =e=

         pvf_onm(t) * (
              
* ---variable O&M costs---
* all technologies except hybrid PV+battery
              sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$cost_vom(i,v,r,t)$(not pvb(i))],
                   hours(h) * cost_vom(i,v,r,t) * GEN(i,v,r,h,t) }

* hybrid PV+battery (PV)
            + sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$cost_vom_pvb_p(i,v,r,t)$pvb(i)],
                   hours(h) * cost_vom_pvb_p(i,v,r,t) * GEN_PVB_P(i,v,r,h,t) }$Sw_PVB

* hybrid PV+battery (Battery)
            + sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$cost_vom_pvb_b(i,v,r,t)$pvb(i)],
                   hours(h) * cost_vom_pvb_b(i,v,r,t) * GEN_PVB_B(i,v,r,h,t) }$Sw_PVB

* ---fixed O&M costs---
* generation
              + sum{(i,v,r)$[valcap(i,v,r,t)],
                   cost_fom(i,v,r,t) * CAP(i,v,r,t) }

* transmission lines
              + sum{(r,rr,trtype)$routes(r,rr,trtype,t),
                    transmission_line_fom(r,rr,trtype) * CAPTRAN(r,rr,trtype,t) }

* LCC AC/DC converter stations
              + sum{(r,rr)$routes(r,rr,"DC",t),
                    cost_acdc_lcc * 2 * trans_fom_frac * CAPTRAN(r,rr,"DC",t) }

* VSC AC/DC converter stations
              + sum{r$rfeas(r),
                    cost_acdc_vsc * trans_fom_frac * CAP_CONVERTER(r,t) }

* ---hourly arbitrage value for storage---
              - sum{(i,v,r)$[valcap(i,v,r,t)$(storage_standalone(i) or pvb(i) or hyd_add_pump(i))],
                   hourly_arbitrage_value(i,r,t) * bcr(i) * CAP(i,v,r,t) }

* ---hourly arbitrage value for dr---
              - sum{(i,v,r)$[valinv(i,v,r,t)$dr(i)],
                   hourly_arbitrage_value(i,r,t) * INV(i,v,r,t) }

* ---penalty for retiring a technology (represents friction in retirements)---
              - sum{(i,v,r)$[valcap(i,v,r,t)$retiretech(i,v,r,t)],
                   cost_fom(i,v,r,t) * retire_penalty * 
                   (CAP(i,v,r,t) - INV(i,v,r,t) - INV_REFURB(i,v,r,t)$[refurbtech(i)$Sw_Refurb]) 
                   }

* ---operating reserve costs---
              + sum{(i,v,r,h,ortype)$[rfeas(r)$valgen(i,v,r,t)$cost_opres(i,ortype,t)$Sw_OpRes],
                   hours(h) * cost_opres(i,ortype,t) * OpRes(ortype,i,v,r,h,t) }

* ---cost of coal and nuclear fuel (except coal used for cofiring)---
              + sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$(not gas(i))$heat_rate(i,v,r,t)
                              $(not bio(i))$(not cofire(i))],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN(i,v,r,h,t) }

* --cofire coal consumption---
* cofire bio consumption already accounted for in accounting of BIOUSED
              + sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$cofire(i)$heat_rate(i,v,r,t)],
                   (1-bio_cofire_perc) * hours(h) * heat_rate(i,v,r,t)
                   * fuel_price("coal-new",r,t) * GEN(i,v,r,h,t) }

* ---cost of natural gas---
*Sw_GasCurve = 2 (static natural gas prices)
              + sum{(i,v,r,h)$[rfeas(r)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)$(Sw_GasCurve = 2)],
                   hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN(i,v,r,h,t) }

*Sw_GasCurve = 0 (census division supply curves natural gas prices)
              + sum{(cendiv,gb)$cdfeas(cendiv), sum{h,hours(h) * GASUSED(cendiv,gb,h,t) }
                   * gasprice(cendiv,gb,t)
                   }$(Sw_GasCurve = 0)

*Sw_GasCurve = 3 (national supply curve for natural gas prices with census division multipliers)
              + sum{(h,cendiv,gb)$cdfeas(cendiv),hours(h) * GASUSED(cendiv,gb,h,t)
                   * gasadder_cd(cendiv,t,h) + gasprice_nat_bin(gb,t)
                   }$(Sw_GasCurve = 3)

*Sw_GasCurve = 1 (national and census division supply curves for natural gas prices)
*first - anticipated costs of gas consumption given last year's amount
              + (sum{(i,r,v,cendiv,h)$[rfeas(r)$valgen(i,v,r,t)$gas(i)$cdfeas(cendiv)],
                   gasmultterm(cendiv,t) * szn_adj_gas(h) * cendiv_weights(r,cendiv) *
                   hours(h) * heat_rate(i,v,r,t) * GEN(i,v,r,h,t) }

*second - adjustments based on changes from last year's consumption at the regional and national level
              + sum{(fuelbin,cendiv)$cdfeas(cendiv),
                   gasbinp_regional(fuelbin,cendiv,t) * VGASBINQ_REGIONAL(fuelbin,cendiv,t) }

              + sum{(fuelbin),
                   gasbinp_national(fuelbin,t) * VGASBINQ_NATIONAL(fuelbin,t) }

              )$[Sw_GasCurve = 1]

* ---cost of biofuel consumption and biomass transport---
              + sum{(r,bioclass)$[sum{(i,v)$(bio(i) or cofire(i)), valgen(i,v,r,t) }],
                   BIOUSED(bioclass,r,t) *
                   (sum{usda_region$r_usda(r,usda_region), biosupply(usda_region, bioclass, "price") } + bio_transport_cost) }

* ---international hurdle costs---
              + sum{(r,rr,h,trtype)$[routes(r,rr,trtype,t)$cost_hurdle(r,rr)],
                   cost_hurdle(r,rr) * FLOW(r,rr,h,t,trtype) * hours(h) }

* ---taxes on emissions---
              + sum{(e,r)$rfeas(r), EMIT(e,r,t) * emit_tax(e,r,t) }

* --cost of CO2 transport and storage from CCS--
              + sum{(i,v,r,h)$[valgen(i,v,r,t)],
                   hours(h) * capture_rate("CO2",i,v,r,t) * GEN(i,v,r,h,t) * CO2_storage_cost }

* --cost of CO2 transport and storage from SMR CCS--
              + sum{(p,v,r,h)$[i_p("smr_ccs",p)$valcap("smr_ccs",v,r,t)], smr_capture_rate * hours(h) *
                             smr_co2_intensity * PRODUCE(p,"smr_ccs",v,r,h,t) * CO2_storage_cost }$Sw_H2

* --cost of CO2 transport and storage from DAC--
              + sum{(i,v,r,h)$[dac(i)$valcap(i,v,r,t)],
                              hours(h) * PRODUCE("dac",i,v,r,h,t) * CO2_storage_cost }$Sw_DAC

* ---State RPS alternative compliance payments---
              + sum{(RPSCat,st)$stfeas(st), acp_price(st,t) * ACP_Purchases(RPSCat,st,t)
                   }$[(yeart(t)>=RPS_StartYear)$Sw_StateRPS]

* ---revenues from purchases of curtailed VRE---
              - sum{(r,h)$rfeas(r), CURT(r,h,t) * hours(h) * cost_curt(t) }$Sw_CurtMarket

* ---costs from producing products (for now DAC and/or H2)---
              + sum{(p,i,v,r,h)$[(h2(i) or dac(i))$valcap(i,v,r,t)$i_p(i,p)],
                    hours(h) * cost_prod(i,v,r,t) * PRODUCE(p,i,v,r,h,t) }$Sw_Prod

              + sum{(r,h)$[rfeas(r)], 1e10 * CURT_SLACK(r,h,t) }$[(yeart(t)<=model_builds_start_yr)$Sw_Hourly]

*end multiplier for pvf_onm
         )
;
