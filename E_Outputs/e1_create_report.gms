
*This file aggregates and formats key results for analysis

parameter resgen, rescap, capinv, txinv, totflow, resflow, margcost, 
fuelcost, capcost, fomcost, vomcost, oprescost, firm_conv, firm_vg, firm_hydro, firm_stor,
avail_refurb, inv_refurb, txcapcost, substcost;

resgen(i,r,t) = sum((v,h),hours(h) * GEN.l(i,v,r,h,t));

rescap(i,r,t) = sum(v,cap.l(i,v,r,t));

capinv(i,r,t) = sum(v, INV.l(i,v,r,t)) ;

txinv(r,rr,t) = sum(trtype, INVTRAN.l(r,rr,t,trtype));

totflow(r,rr,t) = sum((trtype,h), hours(h)*FLOW.l(r,rr,h,t,trtype));

resflow(r,rr,h,t) = sum(trtype, FLOW.l(r,rr,h,t,trtype));

margcost(r,h,t) = eq_supply_demand_balance.m(r,h,t);

capcost(i,r,t) = sum(v$valinv(i,v,r,t), INV.l(i,v,r,t) * cost_cap_fin_mult(i,r,t) * cost_cap(i,t))   
                 + sum((v, rscbin)$valinv(i,v,r,t), INV_RSC.l(i,v,r,t,rscbin) * m_rsc_dat(r,i,rscbin,"cost")) 
                 + sum(v$valinv(i,v,r,t), cost_cap_fin_mult(i,r,t) * cost_cap(i,t) * INVREFURB.l(i,v,r,t) * refurb_cost_multiplier(i));

txcapcost(r,rr,t,trtype) = 
                    ((InterTransCost(r) + InterTransCost(rr))/2) * INVTRAN.l(r,rr,t,trtype) * distance(r,rr) ;

substcost(r,t) = sum{(vc), trancost(r,"cost",vc) * InvSubstation.l(r,vc,t) };

vomcost(i,r,t) = sum((h,v), hours(h) * cost_vom(i,v,r,t)  * GEN.l(i,v,r,h,t));

fomcost(i,r,t) = sum(v, cost_fom(i,v,r,t) * CAP.l(i,v,r,t));

oprescost(i,r,t) = sum((v,h,ortype), hours(h) * cost_opres(i) * OpRes.l(ortype,i,v,r,h,t));

fuelcost(i,r,t) = sum((h,v), hours(h) * heat_rate(i,v,r,t) * fuel_price(i,r,t) * GEN.l(i,v,r,h,t) );

firm_conv(region,szn,t,i) = sum[(v,r)$[r_region(r,region)$valcap(i,v,r,t)$(not rsc_i(i))$(not storage(i))],
          CAP.l(i,v,r,t) ] ;

firm_vg(region,szn,t,i) = sum[r$r_region(r,region),
        sum((v,rr)$[cap_agg(r,rr)$(rsc_i(i))$(not hydro(i))$valcap(i,v,rr,t)],
          cc_int(i,v,rr,szn,t) * CAP.l(i,v,rr,t))
        ] ;

firm_hydro(region,szn,t,i) = sum[(v,r)$[r_region(r,region)$valcap(i,v,r,t)$hydro_pond(i)], cc_hydro(i,r,szn,t) * CAP.l(i,v,r,t) ] +
                             sum[(v,r)$[r_region(r,region)$valcap(i,v,r,t)$hydro_stor(i)],  CAP.l(i,v,r,t) ];

firm_stor(region,szn,t,i) = sum[(v,r,sdbin)$[r_region(r,region)$valcap(i,v,r,t)$storage(i)],
				  CAP_SDBIN.l(i,v,r,szn,sdbin,t) * cc_storage(i,sdbin) ] ;

avail_refurb(i,r,t) = 
*investments that meet the refurbishment requirement (i.e. they've expired)
    sum{(vv,rscbin,tt)$[m_refurb_cond(i,vv,r,t,tt)$tmodel(t)$rfeas(r)$refurbtech(i)],
         INV_RSC.l(i,vv,r,tt,rscbin) }
    + sum{(v,tt)$[yeart(tt)<=yeart(t)],
         m_avail_retire_exog_rsc(i,v,r,tt)$[tmodel(t)$rfeas(r)$refurbtech(i)] } ;

inv_refurb(i,r,t) = sum(v, INVREFURB.l(i,v,r,t));

*Load and operating reserve prices are $/MWh, and reserve margin price is $/kW-yr
parameter
reqt_price							"--varies-- price of requirements",
load_frac_prm(rb,szn,t)              "--fraction-- Fraction of peak LOAD in each BA contributing to PRM",
load_frac_opres(rb,h,t)			"--fraction-- Fraction of operating reserve in each BA",
maxload_szn_r(rb,szn,t)			"--MW-- maximum load in each season"
;

maxload_szn_r(rb,szn,t) = smax(hh$h_szn(hh,szn), lmnt(rb,hh,t));
load_frac_prm(rb,szn,t) = maxload_szn_r(rb,szn,t) / sum(region$[r_region(rb,region)], peakdem_region(region,szn,t) );
load_frac_opres(rb,h,t) = lmnt(rb,h,t) / sum(rr, lmnt(rr,h,t));

reqt_price('load','na',rb,h,t)$(rfeas(rb)$tmodel_new(t)) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_loadcon.m(rb,h,t) / hours(h) ;
reqt_price('res_marg','na',region,szn,t)$tmodel_new(t) = (1 / cost_scale) * (1 / pvf_onm(t)) * eq_reserve_margin.m(region,szn,t)  ;
reqt_price('oper_res',ortype,rb,h,t)$(rfeas(rb)$tmodel_new(t)) = sum(region,(1 / cost_scale) * (1 / pvf_onm(t)) * eq_OpRes_requirement.m(ortype,region,h,t) / hours(h) * load_frac_opres(rb,h,t));

$if not set fname $setglobal fname temp
execute_unload 'reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%gdxfiles%ds%output_%fname%.gdx'
