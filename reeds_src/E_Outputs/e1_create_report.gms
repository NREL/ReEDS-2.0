
*This file aggregates and formats key results for analysis

parameter resgen, rescap, capinv, txinv, totflow, resflow, margcost, thermalfirmcap, rscfirmcap, 
fuelcost, capcost, fomcost, vomcost, oprescost, firm_conv, firm_vg, firm_hydro,
avail_refurb, inv_refurb;

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


resgen(i,r,t) = sum((c,h),hours(h) * GEN.l(i,c,r,h,t));

rescap(i,r,t) = sum(c,cap.l(i,c,r,t));

capinv(i,r,t) = sum(c, INV.l(i,c,r,t)) + sum((c,rscbin), INV_RSC.l(i,c,r,t,rscbin));

txinv(r,rr,t) = sum(trtype, INVTRAN.l(r,rr,t,trtype));

totflow(r,rr,t) = sum((trtype,h), hours(h)*FLOW.l(r,rr,h,t,trtype));

resflow(r,rr,h,t) = sum(trtype, FLOW.l(r,rr,h,t,trtype));

margcost(r,h,t) = eq_supply_demand_balance.m(r,h,t);

thermalfirmcap(r,t,i) =  sum(c$[valcap(i,c,r,t)$((not rsc_i(i)))], CAP.l(i,c,r,t) );

rscfirmcap(r,t,i) = sum((c,szn)$[(not hydro(i))$rsc_i(i)$valcap(i,c,r,t)], cc_avg(i,r,szn,t) * CAP.l(i,c,r,t));

fuelcost(i,r,t) = sum((h,c), hours(h) * heat_rate(i,c,r,t) * fuel_price(i,r,t) * GEN.l(i,c,r,h,t) );

capcost(i,r,t) = sum(c, INV.l(i,c,r,t)*cost_cap(i,t));

fomcost(i,r,t) = sum(c, CAP.l(i,c,r,t)*cost_fom(i,c,r,t));

vomcost(i,r,t) = sum((h,c), cost_vom(i,c,r,t) * hours(h) * GEN.l(i,c,r,h,t));

oprescost(i,r,t) = sum((c,h,ortype), hours(h) * cost_opres(i) * OpRes.l(ortype,i,c,r,h,t));

firm_conv(region,szn,t,i) = sum[(c,r)$[r_region(r,region)$valcap(i,c,r,t)$(not rsc_i(i))$(not storage(i))],
          CAP.l(i,c,r,t) ] ;

firm_vg(region,szn,t,i) = sum[r$r_region(r,region),
        sum((c,rr)$[cap_agg(r,rr)$(rsc_i(i) or storage(i))$(not hydro(i))$valcap(i,c,rr,t)],
          cc_avg(i,rr,szn,t) * CAP.l(i,c,rr,t))
        ] ;

firm_hydro(region,szn,t,i) = sum[(c,r)$[r_region(r,region)$valcap(i,c,r,t)$(hydro(i))],
     cc_hydro(i,r,szn,t) * CAP.l(i,c,r,t) ] ;

avail_refurb(i,r,t) = 
*investments that meet the refurbishment requirement (i.e. they've expired)
    sum{(cc,rscbin,tt)$[m_refurb_cond(i,cc,r,t,tt)$tmodel(t)$rfeas(r)$refurbtech(i)],
         INV_RSC.l(i,cc,r,tt,rscbin) }
    + sum{(c,tt)$[yeart(tt)<=yeart(t)],
         m_avail_retire_exog_rsc(i,c,r,tt)$[tmodel(t)$rfeas(r)$refurbtech(i)] } ;

inv_refurb(i,r,t) = INVREFURB.l(i,r,t);


$if not set fname $setglobal fname temp
execute_unload 'E_Outputs%ds%gdxfiles%ds%output_%fname%.gdx'
