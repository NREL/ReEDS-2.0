*load variable
    LOAD.fx(r,h,tfix)$rfeas(r) = LOAD.l(r,h,tfix) ;
    EVLOAD.fx(r,h,tfix)$[rfeas(r)$Sw_EV] = EVLOAD.l(r,h,tfix) ;
    FLEX.fx(flex_type,r,h,tfix)$[rfeas(r)$Sw_EFS_flex]  = FLEX.l(flex_type,r,h,tfix) ;
    PEAK_FLEX.fx(r,szn,tfix)$[rfeas(r)$Sw_EFS_flex] = PEAK_FLEX.l(r,szn,tfix) ;

* capacity and investment variables
    CAP.fx(i,v,r,tfix)$[valcap(i,v,r,tfix)] = CAP.l(i,v,r,tfix) ;
    CAP_SDBIN.fx(i,v,r,szn,sdbin,tfix)$[valcap(i,v,r,tfix)$storage_no_csp(i)] = CAP_SDBIN.l(i,v,r,szn,sdbin,tfix) ;
    INV.fx(i,v,r,tfix)$[valinv(i,v,r,tfix)] = INV.l(i,v,r,tfix) ;
    INV_REFURB.fx(i,v,r,tfix)$[valinv(i,v,r,tfix)$refurbtech(i)] = INV_REFURB.l(i,v,r,tfix) ;
    INV_RSC.fx(i,v,r,rscbin,tfix)$[valinv(i,v,r,tfix)$rsc_i(i)$m_rscfeas(r,i,rscbin)] = INV_RSC.l(i,v,r,rscbin,tfix) ;
    UPGRADES.fx(i,v,r,tfix)$[valcap(i,v,r,tfix)$upgrade(i)] = UPGRADES.l(i,v,r,tfix) ;
    EXTRA_PRESCRIP.fx(pcat,r,tfix)$[force_pcat(pcat,tfix)$sum{(i,newv)$[prescriptivelink(pcat,i)], valinv(i,newv,r,tfix) }] = EXTRA_PRESCRIP.l(pcat,r,tfix) ;

* generation and storage variables
    GEN.fx(i,v,r,h,tfix)$valgen(i,v,r,tfix) = GEN.l(i,v,r,h,tfix) ;
    CURT.fx(r,h,tfix)$rfeas(r) = CURT.l(r,h,tfix) ;
    MINGEN.fx(r,szn,tfix)$rfeas(r) = MINGEN.l(r,szn,tfix) ;
    STORAGE_IN.fx(i,v,r,h,src,tfix)$[valgen(i,v,r,tfix)$storage_no_csp(i)] = STORAGE_IN.l(i,v,r,h,src,tfix) ;
    STORAGE_LEVEL.fx(i,v,r,h,tfix)$[valgen(i,v,r,tfix)$storage(i)] = STORAGE_LEVEL.l(i,v,r,h,tfix) ;

* trade variables
    FLOW.fx(r,rr,h,tfix,trtype)$routes(r,rr,trtype,tfix) = FLOW.l(r,rr,h,tfix,trtype) ;
    OPRES_FLOW.fx(ortype,r,rr,h,tfix)$opres_routes(r,rr,tfix) = OPRES_FLOW.l(ortype,r,rr,h,tfix) ;
    CURT_FLOW.fx(r,rr,h,tfix)$sum{trtype, routes(r,rr,trtype,tfix) } = CURT_FLOW.l(r,rr,h,tfix) ;
    PRMTRADE.fx(r,rr,trtype,szn,tfix)$routes(r,rr,trtype,tfix) = PRMTRADE.l(r,rr,trtype,szn,tfix) ;

* operating reserve variables
    OPRES.fx(ortype,i,v,r,h,tfix)$[Sw_OpRes$valgen(i,v,r,tfix)$(reserve_frac(i,ortype) or hydro_d(i) or storage(i))] = OPRES.l(ortype,i,v,r,h,tfix) ;

* variable fuel amounts
    GASUSED.fx(cendiv,gb,h,tfix)$[Sw_GasCurve=0$cdfeas(cendiv)] = GASUSED.l(cendiv,gb,h,tfix) ;
    VGASBINQ_NATIONAL.fx(fuelbin,tfix)$[Sw_GasCurve=1] = VGASBINQ_NATIONAL.l(fuelbin,tfix) ;
    VGASBINQ_REGIONAL.fx(fuelbin,cendiv,tfix)$[(Sw_GasCurve=1)$cdfeas(cendiv)] = VGASBINQ_REGIONAL.l(fuelbin,cendiv,tfix) ;
    BIOUSED.fx(bioclass,r,tfix)$[rfeas(r)$biofeas(r)] = BIOUSED.l(bioclass,r,tfix) ;

* RECS variables
    RECS.fx(RPSCat,i,st,ast,tfix)$[stfeas(st)$RecMap(i,RPSCat,st,ast,tfix)$stfeas(ast)] = RECS.l(RPSCat,i,st,ast,tfix) ;
    ACP_Purchases.fx(RPSCat,st,tfix)$stfeas(st) = ACP_Purchases.l(RPSCat,st,tfix) ;
    EMIT.fx(e,r,tfix)$rfeas(r) = EMIT.l(e,r,tfix) ;

* transmission variables
    CAPTRAN.fx(r,rr,trtype,tfix)$routes(r,rr,trtype,tfix) = CAPTRAN.l(r,rr,trtype,tfix) ;
    INVTRAN.fx(r,rr,tfix,trtype)$routes_inv(r,rr,trtype,tfix) = INVTRAN.l(r,rr,tfix,trtype) ;
    INVSUBSTATION.fx(r,vc,tfix)$[rfeas(r)$tscfeas(r,vc)] = INVSUBSTATION.l(r,vc,tfix) ;

* water climate variables
    WATCAP.fx(i,v,r,tfix)$[valcap(i,v,r,tfix)$Sw_WaterMain$Sw_WaterCapacity] = WATCAP.l(i,v,r,tfix) ;
    WAT.fx(i,v,w,r,h,tfix)$[i_water(i)$valgen(i,v,r,tfix)$Sw_WaterMain] = WAT.l(i,v,w,r,h,tfix) ;
    WATER_CAPACITY_LIMIT_SLACK.fx(wst,r,tfix)$[rfeas(r)$Sw_WaterMain$Sw_WaterCapacity] = WATER_CAPACITY_LIMIT_SLACK.l(wst,r,tfix) ;