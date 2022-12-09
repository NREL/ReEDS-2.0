*load variable
    LOAD.fx(r,h,tfix)$rfeas(r) = LOAD.l(r,h,tfix) ;
    EVLOAD.fx(r,h,tfix)$[rfeas(r)$Sw_EV] = EVLOAD.l(r,h,tfix) ;
    FLEX.fx(flex_type,r,h,tfix)$[rfeas(r)$Sw_EFS_flex]  = FLEX.l(flex_type,r,h,tfix) ;
    PEAK_FLEX.fx(r,szn,tfix)$[rfeas(r)$Sw_EFS_flex] = PEAK_FLEX.l(r,szn,tfix) ;

* capacity and investment variables
    CAP.fx(i,v,r,tfix)$[valcap(i,v,r,tfix)] = CAP.l(i,v,r,tfix) ;
    CAP_SDBIN.fx(i,v,r,szn,sdbin,tfix)$[valcap(i,v,r,tfix)$(storage(i) or hyd_add_pump(i))$(not csp(i))] = CAP_SDBIN.l(i,v,r,szn,sdbin,tfix) ;
    INV.fx(i,v,r,tfix)$[valinv(i,v,r,tfix)] = INV.l(i,v,r,tfix) ;
    INV_REFURB.fx(i,v,r,tfix)$[valinv(i,v,r,tfix)$refurbtech(i)] = INV_REFURB.l(i,v,r,tfix) ;
    INV_RSC.fx(i,v,r,rscbin,tfix)$[valinv(i,v,r,tfix)$rsc_i(i)$m_rscfeas(r,i,rscbin)] = INV_RSC.l(i,v,r,rscbin,tfix) ;
    CAP_RSC.fx(i,v,r,rscbin,tfix)$[valcap(i,v,r,tfix)$rsc_i(i)$m_rscfeas(r,i,rscbin)] = CAP_RSC.l(i,v,r,rscbin,tfix) ;
    INV_CAP_UP.fx(i,v,r,rscbin,tfix)$[allow_cap_up(i,v,r,rscbin,tfix)] = INV_CAP_UP.l(i,v,r,rscbin,tfix) ;
    INV_ENER_UP.fx(i,v,r,rscbin,tfix)$[allow_ener_up(i,v,r,rscbin,tfix)] = INV_ENER_UP.l(i,v,r,rscbin,tfix) ;
    UPGRADES.fx(i,v,r,tfix)$[valcap(i,v,r,tfix)$upgrade(i)] = UPGRADES.l(i,v,r,tfix) ;
    EXTRA_PRESCRIP.fx(pcat,r,tfix)$[force_pcat(pcat,tfix)$sum{(i,newv)$[prescriptivelink(pcat,i)], valinv(i,newv,r,tfix) }] = EXTRA_PRESCRIP.l(pcat,r,tfix) ;

* generation and storage variables
    GEN.fx(i,v,r,h,tfix)$valgen(i,v,r,tfix) = GEN.l(i,v,r,h,tfix) ;
    GEN_PVB_P.fx(i,v,r,h,tfix)$[pvb(i)$valgen(i,v,r,tfix)$Sw_PVB] = GEN_PVB_P.l(i,v,r,h,tfix) ;
    GEN_PVB_B.fx(i,v,r,h,tfix)$[pvb(i)$valgen(i,v,r,tfix)$Sw_PVB] = GEN_PVB_B.l(i,v,r,h,tfix) ;
    CURT.fx(r,h,tfix)$rfeas(r) = CURT.l(r,h,tfix) ;
    MINGEN.fx(r,szn,tfix)$rfeas(r) = MINGEN.l(r,szn,tfix) ;
    STORAGE_IN.fx(i,v,r,h,src,tfix)$[valgen(i,v,r,tfix)$(storage_standalone(i) or hyd_add_pump(i))] = STORAGE_IN.l(i,v,r,h,src,tfix) ;
    STORAGE_IN_PVB_P.fx(i,v,r,h,src,tfix)$[valgen(i,v,r,tfix)$pvb(i)$Sw_PVB] = STORAGE_IN_PVB_P.l(i,v,r,h,src,tfix) ;
    STORAGE_IN_PVB_G.fx(i,v,r,h,src,tfix)$[valgen(i,v,r,tfix)$pvb(i)$Sw_PVB] = STORAGE_IN_PVB_G.l(i,v,r,h,src,tfix) ;
    STORAGE_LEVEL.fx(i,v,r,h,tfix)$[valgen(i,v,r,tfix)$storage(i)] = STORAGE_LEVEL.l(i,v,r,h,tfix) ;
    LAST_HOUR_SOC.fx(i,v,r,h,tfix)$[valgen(i,v,r,tfix)$storage(i)$final_hour(h)$Sw_Hourly] = LAST_HOUR_SOC.l(i,v,r,h,tfix) ;
    DR_SHIFT.fx(i,v,r,h,hh,src,tfix)$[valgen(i,v,r,tfix)$dr1(i)] = DR_SHIFT.l(i,v,r,h,hh,src,tfix) ;
    DR_SHED.fx(i,v,r,h,tfix)$[valgen(i,v,r,tfix)$dr2(i)] = DR_SHED.l(i,v,r,h,tfix) ;
    AVAIL_SITE.fx(x,h,tfix)$[Sw_SpurScen$xfeas(x)] = AVAIL_SITE.l(x,h,tfix) ;
    
* flexible CCS variables
    CCSFLEX_POW.fx(i,v,r,h,tfix)$[ccsflex(i)$valgen(i,v,r,tfix)$(Sw_CCSFLEX_BYP OR Sw_CCSFLEX_STO OR Sw_CCSFLEX_DAC)] = CCSFLEX_POW.l(i,v,r,h,tfix) ;
    CCSFLEX_POWREQ.fx(i,v,r,h,tfix)$[ccsflex_sto(i)$valgen(i,v,r,tfix)$Sw_CCSFLEX_STO] = CCSFLEX_POWREQ.l(i,v,r,h,tfix) ;
    CCSFLEX_STO_STORAGE_LEVEL.fx(i,v,r,h,tfix)$[ccsflex_sto(i)$valgen(i,v,r,tfix)$Sw_CCSFLEX_STO] = CCSFLEX_STO_STORAGE_LEVEL.l(i,v,r,h,tfix) ;
    CCSFLEX_STO_STORAGE_CAP.fx(i,v,r,tfix)$[ccsflex_sto(i)$valcap(i,v,r,tfix)$Sw_CCSFLEX_STO] = CCSFLEX_STO_STORAGE_CAP.l(i,v,r,tfix) ;

* trade variables
    FLOW.fx(r,rr,h,tfix,trtype)$routes(r,rr,trtype,tfix) = FLOW.l(r,rr,h,tfix,trtype) ;
    OPRES_FLOW.fx(ortype,r,rr,h,tfix)$[Sw_OpRes$opres_routes(r,rr,tfix)] = OPRES_FLOW.l(ortype,r,rr,h,tfix) ;
    PRMTRADE.fx(r,rr,trtype,szn,tfix)$[routes(r,rr,trtype,tfix)$routes_prm(r,rr)] = PRMTRADE.l(r,rr,trtype,szn,tfix) ;

* operating reserve variables
    OPRES.fx(ortype,i,v,r,h,tfix)$[Sw_OpRes$valgen(i,v,r,tfix)$reserve_frac(i,ortype)] = OPRES.l(ortype,i,v,r,h,tfix) ;

* variable fuel amounts
    GASUSED.fx(cendiv,gb,h,tfix)$[Sw_GasCurve=0$cdfeas(cendiv)] = GASUSED.l(cendiv,gb,h,tfix) ;
    VGASBINQ_NATIONAL.fx(fuelbin,tfix)$[Sw_GasCurve=1] = VGASBINQ_NATIONAL.l(fuelbin,tfix) ;
    VGASBINQ_REGIONAL.fx(fuelbin,cendiv,tfix)$[(Sw_GasCurve=1)$cdfeas(cendiv)] = VGASBINQ_REGIONAL.l(fuelbin,cendiv,tfix) ;
    BIOUSED.fx(bioclass,r,tfix)$[sum{(i,v)$(bio(i) or cofire(i)), valgen(i,v,r,tfix) }] = BIOUSED.l(bioclass,r,tfix) ;

* RECS variables
    RECS.fx(RPSCat,i,st,ast,tfix)$[stfeas(st)$RecMap(i,RPSCat,st,ast,tfix)$(stfeas(ast) or sameas(ast,"corporate"))$Sw_StateRPS] = RECS.l(RPSCat,i,st,ast,tfix) ;
    ACP_Purchases.fx(RPSCat,st,tfix)$[(stfeas(st) or sameas(st,"corporate"))$Sw_StateRPS] = ACP_Purchases.l(RPSCat,st,tfix) ;
    EMIT.fx(e,r,tfix)$rfeas(r) = EMIT.l(e,r,tfix) ;

* transmission variables
    CAPTRAN_ENERGY.fx(r,rr,trtype,tfix)$routes(r,rr,trtype,tfix) = CAPTRAN_ENERGY.l(r,rr,trtype,tfix) ;
    CAPTRAN_PRM.fx(r,rr,trtype,tfix)$routes(r,rr,trtype,tfix) = CAPTRAN_PRM.l(r,rr,trtype,tfix) ;
    INVTRAN.fx(r,rr,trtype,tfix)$routes_inv(r,rr,trtype,tfix) = INVTRAN.l(r,rr,trtype,tfix) ;
    INVSUBSTATION.fx(r,vc,tfix)$[rfeas(r)$tscfeas(r,vc)] = INVSUBSTATION.l(r,vc,tfix) ;
    CURT_REDUCT_TRANS.fx(r,rr,h,tfix)$[curt_tran(r,rr,h,tfix)$sum{(n,nn,trtype), translinkage(r,rr,n,nn,trtype) }] = CURT_REDUCT_TRANS.l(r,rr,h,tfix) ;
    INV_CONVERTER.fx(r,tfix)$[rfeas(r)$Sw_VSC] = INV_CONVERTER.l(r,tfix) ;
    CAP_CONVERTER.fx(r,tfix)$[rfeas(r)$Sw_VSC] = CAP_CONVERTER.l(r,tfix) ;
    CONVERSION.fx(r,h,intype,outtype,tfix)$[rfeas(r)$Sw_VSC] = CONVERSION.l(r,h,intype,outtype,tfix) ;
    CAP_SPUR.fx(x,tfix)$[Sw_SpurScen$xfeas(x)] = CAP_SPUR.l(x,tfix) ;
    INV_SPUR.fx(x,tfix)$[Sw_SpurScen$xfeas(x)] = INV_SPUR.l(x,tfix) ;
    INV_POI.fx(r,tfix)$[rfeas(r)$Sw_TransIntraCost] = INV_POI.l(r,tfix) ;

* water climate variables
    WATCAP.fx(i,v,r,tfix)$[valcap(i,v,r,tfix)$Sw_WaterMain$Sw_WaterCapacity] = WATCAP.l(i,v,r,tfix) ;
    WAT.fx(i,v,w,r,h,tfix)$[i_water(i)$valgen(i,v,r,tfix)$Sw_WaterMain] = WAT.l(i,v,w,r,h,tfix) ;
    WATER_CAPACITY_LIMIT_SLACK.fx(wst,r,tfix)$[rfeas(r)$Sw_WaterMain$Sw_WaterCapacity] = WATER_CAPACITY_LIMIT_SLACK.l(wst,r,tfix) ;

*H2 and DAC production variables
    PRODUCE.fx(p,i,v,r,h,tfix)$[consume(i)$valcap(i,v,r,tfix)$Sw_Prod] = PRODUCE.l(p,i,v,r,h,tfix) ;
    H2_FLOW.fx(r,rr,p,h,tfix)$[H2_routes(r,rr)$(Sw_H2 = 2)] = H2_FLOW.l(r,rr,p,h,tfix);
    H2_TRANSPORT_INV.fx(r,rr,tfix)$[H2_routes(r,rr)$(Sw_H2 = 2)] = H2_TRANSPORT_INV.l(r,rr,tfix);

*CO2-related variables
    CO2_CAPTURED.fx(r,h,tfix)$[Sw_CO2_Detail$rfeas(r)] = CO2_CAPTURED.l(r,h,tfix) ;
    CO2_STORED.fx(r,cs,h,tfix)$[Sw_CO2_Detail$r_cs(r,cs)] = CO2_STORED.l(r,cs,h,tfix) ;
    CO2_FLOW.fx(r,rr,h,tfix)$[Sw_CO2_Detail$co2_routes(r,rr)] = CO2_FLOW.l(r,rr,h,tfix) ;
    CO2_TRANSPORT_INV.fx(r,rr,tfix)$[Sw_CO2_Detail$co2_routes(r,rr)] = CO2_TRANSPORT_INV.l(r,rr,tfix) ;
    CO2_SPURLINE_INV.fx(r,cs,tfix)$[Sw_CO2_Detail$r_cs(r,cs)] = CO2_SPURLINE_INV.l(r,cs,tfix) ;
