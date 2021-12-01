*load variable
    LOAD.l(r,h,tmodel) = 0 ;
    EVLOAD.l(r,h,tmodel) = 0 ;
    FLEX.l(flex_type,r,h,tmodel) = 0 ;
    PEAK_FLEX.l(r,szn,tmodel) = 0 ;

* capacity and investment variables
    CAP.l(i,v,r,tmodel) = 0 ;
    CAP_SDBIN.l(i,v,r,szn,sdbin,tmodel) = 0 ;
    INV.l(i,v,r,tmodel) = 0 ;
    INV_REFURB.l(i,v,r,tmodel) = 0 ;
    INV_RSC.l(i,v,r,rscbin,tmodel) = 0 ;
    UPGRADES.l(i,v,r,tmodel) = 0 ;
    EXTRA_PRESCRIP.l(pcat,r,tmodel) = 0 ;

* generation and storage variables
    GEN.l(i,v,r,h,tmodel) = 0 ;
    GEN_PVB_P.l(i,v,r,h,tmodel) = 0 ;
    GEN_PVB_B.l(i,v,r,h,tmodel) = 0 ;
    CURT.l(r,h,tmodel) = 0 ;
    MINGEN.l(r,szn,tmodel) = 0 ;
    STORAGE_IN.l(i,v,r,h,src,tmodel) = 0 ;
    STORAGE_IN_PVB_P.l(i,v,r,h,src,tmodel) = 0 ;
    STORAGE_IN_PVB_G.l(i,v,r,h,src,tmodel) = 0 ;
    STORAGE_LEVEL.l(i,v,r,h,tmodel) = 0 ;

* trade variables
    FLOW.l(r,rr,h,tmodel,trtype) = 0 ;
    OPRES_FLOW.l(ortype,r,rr,h,tmodel) = 0 ;
    CURT_FLOW.l(r,rr,h,tmodel) = 0 ;
    PRMTRADE.l(r,rr,trtype,szn,tmodel) = 0 ;

* operating reserve variables
    OPRES.l(ortype,i,v,r,h,tmodel) = 0 ;

* variable fuel amounts
    GASUSED.l(cendiv,gb,h,tmodel) = 0 ;
    VGASBINQ_NATIONAL.l(fuelbin,tmodel) = 0 ;
    VGASBINQ_REGIONAL.l(fuelbin,cendiv,tmodel) = 0 ;
    BIOUSED.l(bioclass,r,tmodel) = 0 ;

* RECS variables
    RECS.l(RPSCat,i,st,ast,tmodel) = 0 ;
    ACP_Purchases.l(RPSCat,st,tmodel) = 0 ;
    EMIT.l(e,r,tmodel) = 0 ;

* transmission variables
    CAPTRAN.l(r,rr,trtype,tmodel) = 0 ;
    INVTRAN.l(r,rr,tmodel,trtype) = 0 ;
    INVSUBSTATION.l(r,vc,tmodel) = 0 ;
    CURT_REDUCT_TRANS.l(r,rr,h,tmodel) = 0 ;

* water climate variables
    WATCAP.l(i,v,r,tmodel) = 0 ;
    WAT.l(i,v,w,r,h,tmodel) = 0 ;
    WATER_CAPACITY_LIMIT_SLACK.l(wst,r,tmodel) = 0 ;

*H2 and DAC production variables
    PRODUCE.l(i,v,r,h,tmodel) = 0 ;

