* file reads in all inputs needed for curtailment calculations


$ontext
1. Load the inputs from the .gdx file created at the end of A_readinputs.gms
2. Compute the parameters necessary for 8760 _region.gms
2. Unload the inputs to 8760 20xx.gdx
$offtext

* ===================================================================

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


* call gdxin for the .gdx file created at the end of C_Solve.gms
$if %Interconnect% == 'India' $gdxin .%ds%E_Outputs%ds%gdxfiles%ds%%case%_load.gdx


* -------------------------------
* --- time sets ---
* -------------------------------

alias(t,allyears) ;

set thisyear(allyears) / %cur_year% / ;
scalar cur_year / %cur_year% / ;
set lastsolveyear(allyears) / %cur_year% /;
scalar prior_model_year / %cur_year% / ;

set allyearsbeyond /2017*2080/;

set thisyearbeyond(allyearsbeyond) / %cur_year% / ;

* alias for time-slices
* h = reeds 2.0
* m = reeds
alias(h,m) ;

set s seasons ;
$load s=szn


set notpeakszn(m) time-slices that do not occur in the peak season ;
$load notpeakszn=h

notpeakszn(m) = not peaksznh(m);

set seaperiods(m,s);
$load seaperiods=h_szn

set peak(m) 
/ 
H7
H14
H21
H28
H35 
/ ; 

set notpeak(m) time-slices that are not the peak ;
$load notpeak=h

notpeak(m) = not(peak(m));

set hourid /1*8760/ ;

* -------------------------------
* --- regional sets ---
* -------------------------------

set resregfull wind resource regions;
$load resregfull=rs

set resreg(resregfull) wind resource regions ;
$load resreg=rs

* alias for balancing area
* r = reeds 2.0
* n = reeds
alias(r,n) ;

alias(n,p) ;

set route(n,p,trtype,t) ;
$load route=routes

set AC_routes(n,p) ;
AC_routes(n,p) = sum((t,trtype),route(n,p,trtype,t)$sameas(trtype,"AC")) ;

set ba ;
$load ba=r

set pcaj(n,resreg) crosswalk between BAs and resource regions ;
$load pcaj=r_rs

*set region regional transmission organization ;
set nregion(n,region) "crosswalk between BAs and regions" 
         /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%nregion.csv
$offdelim
/;


set nerc nerc region ;
$load nerc=region

set nnerc_x(n,nerc) ;
$load nnerc_x=r_region

set nnerc(nerc, n) "mapping region and BA" ;
nnerc(nerc,n) = nnerc_x(n,nerc);

set cw_resreg(rs,resregfull) crosswalk: resource regions / #resreg:#resregfull /;

* -------------------------------
* --- technology sets ---
* -------------------------------

*set windtrg  wind techno resource group  ;
*$load windtrg=c
alias(c, windtrg);

set pvclass PV resource class / upv, dupv /;


set bigQ full set of technologies for reporting;
$load bigQ=i

set q(bigQ) conventional generation technologies ;
$load q=conv

* add extra gx technology types to bigQ and q to match 8760 
$onmulti
set bigQ /hydro, curtail, transmission, reqt/;
$offmulti

$onmulti
set q /hydro, curtail, transmission, reqt/;
$offmulti


set coaltech(q) coal generation technologies ;
$load coaltech=coal

set nuctech(q) /"NUCLEAR"/ ;

set distPVtech(bigQ) distPV technologies;
$load distPVtech=dupv

set storetech(bigQ) storage technologies ;
$load storetech=storage

set windtype(bigQ) / wind /;

set hydcats(bigQ)
$load hydcats=hydro

set hydDcats(hydcats) ;
$load hydDcats=hydro_d

set hydNDcats(hydcats) ;
$load hydNDcats=hydro_nd


* -------------------------------
* --- technology/region sets ---
* -------------------------------

set nwithupv(n,pvclass) "BA with upv resource" ;
nwithupv(r,'UPV')$[rfeas(r) and sum{ (i,c,t,rs)$[upv(i) and t.val=cur_year and rfeas(r)], 
  valcap(i,c,rs,t)$r_rs(r,rs) } ]= YES ;

set nwithdupv(n,pvclass) "BA with dupv resource" ;
nwithdupv(r,'DUPV')$[rfeas(r) and sum{(i,c,t,rs)$[dupv(i) and t.val=cur_year and rfeas(r)], 
  valcap(i,c,r,t)$r_rs(r,rs) } ]= YES ; 


set iwithwindtype(resreg,windtype) "resource regions with wind";
iwithwindtype(resreg, windtype)$sum{(i,c,r,rs,t)$[cw_resreg(rs,resreg) and rfeas(r) and r_rs(r,rs) and t.val=cur_year and wind(i)], 
                                  valcap(i,c,rs,t)} = YES ;


* -------------------------------
* --- random parameters ---
* -------------------------------

parameter Hm(m) ;
$load Hm=hours

parameter DXi(resreg) "x-coordinate of resource region" 
         /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%coordx_rs.csv
$offdelim
/;

parameter DYi(resreg) "y-coordinate of resource region" 
         /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%coordy_rs.csv
$offdelim
/;


parameter nomsize(q) "--MW-- nominal size of technology type 'i'"
      /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%nomsize.csv
$offdelim
/;

parameter minplantload(q) ;
$load minplantload=minloadfrac0

parameter minplantload_hy_r2(hydcats, n, s);
$load minplantload_hy_r2 = hydmin

parameter minplantload_hy(hydDcats,s,n) ;
minplantload_hy(hydDcats,s,n) = minplantload_hy_r2(hydDcats,n,s);


* -------------------------------
* --- transmission parameters ---
* -------------------------------

parameter lineflow(n,p,m) --avg MW-- average flow on AC lines between BAs 'n' and 'p' during time-slice 'm' ;
lineflow(r,rr,h)$[rfeas(r) and rfeas(rr)] = sum{(t,trtype)$[routes(rr,r,trtype,t) and t.val=cur_year and sameas(trtype,'AC')],
                      FLOW.l(r,rr,h,t,trtype)
                  } ;

parameter DC_lineflow(n,p,m) --avg MW-- average flow on DC lines between BAs 'n' and 'p' during time-slice 'm' ;
DC_lineflow(r,rr,h)$[rfeas(r) and rfeas(rr)] = sum{(t,trtype)$[routes(rr,r,trtype,t) and t.val=cur_year and sameas(trtype,'DC')],
                         FLOW.l(r,rr,h,t,trtype)
                     } ;


parameter net_inj(n,m) --avg MW-- average net injection from BA 'n' into the grid during time-slice 'm' ;
net_inj(r,h)$rfeas(r) =  sum{(rr,t,trtype)$[rfeas(rr) and routes(rr,r,trtype,t) and t.val=cur_year and sameas(trtype,'AC')],
                               (1-tranloss(rr,r)) * FLOW.l(r,rr,h,t,trtype)
                             - FLOW.l(rr,r,h,t,trtype)
                         }
;

parameter NetImportsRTO(region,m,allyears) --avg MW-- average net imports by RTO for each times-slice ;
NetImportsRTO(region,h,t)$[t.val=cur_year] =
sum{(rr,r,trtype)$[rfeas(rr) and routes(rr,r,trtype,t) and nregion(r,region) and not nregion(rr,region)],
      (1-tranloss(rr,r)) * FLOW.l(rr,r,h,t,trtype)
    - FLOW.l(r,rr,h,t,trtype)
}
;

parameter NetImportsBA(n,m,allyears) --avg MW-- average net imports by balancing areas for each times-slice ;
NetImportsBA(r,h,t)$[rfeas(r) and t.val=cur_year] =
sum{(rr,trtype)$[rfeas(rr) and routes(rr,r,trtype,t)],
      (1-tranloss(rr,r)) * FLOW.l(rr,r,h,t,trtype)
    - FLOW.l(r,rr,h,t,trtype)
}
;

parameter transloss(n,m) "-- MW -- total losses in BA 'n' during time slice 'm'";
transloss(r,h)$rfeas(r) = sum{(rr,t,trtype)$[rfeas(rr) and routes(rr,r,trtype,t) and t.val=cur_year],
                              tranloss(rr,r) * FLOW.l(rr,r,h,t,trtype)
                          }
;

parameter distlossfactor ;
$load distlossfactor=distloss

scalar CFDUPVAdj ;
CFDUPVAdj = 1 ;

scalar TieLossCFAdj ;
TieLossCFAdj = 1;


* ----------------------------------
* --- vre generation parameters ---
* ----------------------------------

parameter WGenOld(n,m) --avg MW-- max possible generation from existing wind in BA 'n' during time-slice 'm' ;
WGenOld(r,h)$rfeas(r) = sum{(rs,i,c,t)$[WIND(i) and t.val=cur_year], 
                                       m_cf(i,rs,h) * CAP.l(i,c,rs,t)$r_rs(r,rs)} ;


parameter UPVGenOld(n,m) --avg MW-- max possible generation from existing UPV in BA 'n' during time-slice 'm' ;
UPVGenOld(r,h)$rfeas(r) = sum{(rs,i,c,t)$[UPV(i) and t.val=cur_year], 
                                       m_cf(i,rs,h) * CAP.l(i,c,rs,t)$r_rs(r,rs)} ;;

parameter DUPVGenOld(n,m) --avg MW-- max possible generation from existing DUPV in BA 'n' during time-slice 'm' ;
DUPVGenOld(r,h)$rfeas(r) = sum{(rs,i,c,t)$[DUPV(i) and t.val=cur_year], 
                                       m_cf(i,rs,h) * CAP.l(i,c,rs,t)$r_rs(r,rs)} ;


* -------------------------------
* --- generation parameters ---
* -------------------------------

parameter gen_8760 (m,n) --avg MW-- average generation from ALL existing generators (except distPV) in BA 'n' during time-slice 'm' ;
* NOTE: No need to subtract curtailment, because it is already included in SPLY
gen_8760 (h,r)$rfeas(r) = sum{(i,c,t)$[not sameas(i,"dupv") and t.val=cur_year], GEN.l(i,c,r,h,t)} ;


* ---------------------------------------
* --- vrre technology crosswalk sets ---
* --------------------------------------
$onmulti
set i / WIND_1*WIND_12 /;
$offmulti

set cw_windtech(windtype,windtrg,i) crosswalk: wind technologies  ;

cw_windtech('WIND','init-1','WIND_1') = YES ;
cw_windtech('WIND','init-2','WIND_2') = YES ;
cw_windtech('WIND','init-3','WIND_3') = YES ;
cw_windtech('WIND','init-4','WIND_4') = YES ;
cw_windtech('WIND','init-5','WIND_5') = YES ;
cw_windtech('WIND','init-6','WIND_6') = YES ;
cw_windtech('WIND','init-7','WIND_7') = YES ;
cw_windtech('WIND','prescribed','WIND_8') = YES ;
cw_windtech('WIND','new1','WIND_9') = YES ;
cw_windtech('WIND','new2','WIND_10') = YES ;
cw_windtech('WIND','new3','WIND_11') = YES ;
cw_windtech('WIND','new4','WIND_12') = YES ;

set cw_windtech2(windtype,i) ;
cw_windtech2('WIND','WIND_1') = YES ;
cw_windtech2('WIND','WIND_2') = YES ;
cw_windtech2('WIND','WIND_3') = YES ;
cw_windtech2('WIND','WIND_4') = YES ;
cw_windtech2('WIND','WIND_5') = YES ;
cw_windtech2('WIND','WIND_6') = YES ;
cw_windtech2('WIND','WIND_7') = YES ;
cw_windtech2('WIND','WIND_8') = YES ;
cw_windtech2('WIND','WIND_9') = YES ;
cw_windtech2('WIND','WIND_10') = YES ;
cw_windtech2('WIND','WIND_11') = YES ;
cw_windtech2('WIND','WIND_12') = YES ;


set cw_upvtech(pvclass,i) crosswalk: upv technologies;
$onmulti
set i / UPV_1*UPV_12 / ;
$offmulti 

cw_upvtech('UPV','UPV_1') = YES ;
cw_upvtech('UPV','UPV_2') = YES ;
cw_upvtech('UPV','UPV_3') = YES ;
cw_upvtech('UPV','UPV_4') = YES ;
cw_upvtech('UPV','UPV_5') = YES ;
cw_upvtech('UPV','UPV_6') = YES ;
cw_upvtech('UPV','UPV_7') = YES ;
cw_upvtech('UPV','UPV_8') = YES ;
cw_upvtech('UPV','UPV_9') = YES ;
cw_upvtech('UPV','UPV_10') = YES ;
cw_upvtech('UPV','UPV_11') = YES ;
cw_upvtech('UPV','UPV_12') = YES ;


set cw_dupvtech(pvclass,i) crosswalk: dupv technologies;
$onmulti
set i / DUPV_1*DUPV_12 /;
$offmulti

cw_dupvtech('dupv','dupv_1') = YES ;
cw_dupvtech('dupv','dupv_2') = YES ;
cw_dupvtech('dupv','dupv_3') = YES ;
cw_dupvtech('dupv','dupv_4') = YES ;
cw_dupvtech('dupv','dupv_5') = YES ;
cw_dupvtech('dupv','dupv_6') = YES ;
cw_dupvtech('dupv','dupv_7') = YES ;
cw_dupvtech('dupv','dupv_8') = YES ;
cw_dupvtech('dupv','dupv_9') = YES ;
cw_dupvtech('dupv','dupv_10') = YES ;
cw_dupvtech('dupv','dupv_11') = YES ;
cw_dupvtech('dupv','dupv_12') = YES ;


* --------------------------------
* --- vrre capacity parameters ---
* --------------------------------

parameter WO(windtrg,windtype,resreg) "--MW-- existing wind capacity by wind TRG, wind type, and resource region"  ;
WO(c,windtype,resreg) = sum{(i,r,rs,t)$[cw_resreg(rs,resreg) and rfeas(r) and r_rs(r,rs) and t.val=cur_year and wind(i)], 
                                    CAP.l(i,c,r,t)} ;

parameter UPVO(n,pvclass) "--MW-- existing UPV capacity by class and BA" ;
UPVO(r,'UPV')$rfeas(r) = sum{(i,c,rs,t)$[upv(i) and t.val=cur_year and rfeas(r)], CAP.l(i,c,r,t)} ;

parameter DUPVO(n,pvclass) "--MW-- existing DUPV capacity by class and BA" ;
DUPVO(r,'DUPV')$rfeas(r) = sum{(i,c,rs,t)$[dupv(i) and t.val=cur_year and rfeas(r)], CAP.l(i,c,r,t)} ;

* existing upv and dupv capacity - used for CFOUPV and CFODUPV calculations.
parameter excap_upv(i,c,r,rs) "existing upv capacity by rs ";
excap_upv(i,c,r,rs) = sum{t$[upv(i) and t.val = cur_year and rfeas(r) and r_rs(r,rs)],  CAP.l(i,c,r,t) };

parameter excap_dupv(i,c,r,rs) "existing upv capacity by rs ";
excap_dupv(i,c,r,rs) = sum{t$[dupv(i) and t.val = cur_year and rfeas(r) and r_rs(r,rs)],  CAP.l(i,c,r,t) };

* -------------------------------
* --- class sets ---
* -------------------------------

* NOTE: these are computed based on remaining resource
parameter class(windtrg,windtype,resreg) ;
class(c,windtype,resreg)$sum{(i,r,rs,t)$[cw_resreg(rs,resreg) and rfeas(r) and r_rs(r,rs) and t.val=cur_year and wind(i)], 
                                  valcap(i,c,r,t)} = YES ;

parameter classupv(pvclass,n) ;
classupv('UPV',r)$[rfeas(r) and sum{(i,c,t)$[upv(i) and t.val=cur_year and rfeas(r)], valcap(i,c,r,t) } ]= YES ;


parameter classdupv(pvclass,n) ;
classdupv('DUPV',r)$[rfeas(r) and sum{(i,c,t)$[dupv(i) and t.val=cur_year and rfeas(r)], valcap(i,c,r,t)}] = YES ;

* -------------------------------
* --- load parameters ---
* -------------------------------

parameter Lmn(n,m) ;
Lmn(r,h)$rfeas(r) = sum{(t)$[t.val=cur_year], lmnt(r,h,t)} ;

parameter lk2n(n,m) "load variance divided by load squared by BA and timeslice"
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%lk2n.csv
$offdelim
/;

parameter lk2factorRTO(region,m) "load variance divided by load squared by RTO and timeslice"
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%lk2n_region.csv
$offdelim
/;


parameter Pregion_t(region,szn,t) "peak demand by region and season";
$load Pregion_t=peakdem_region

parameter Pregion(region, szn) "--MW-- peak demand by region";
Pregion(region, szn) = sum(t$(t.val=cur_year),Pregion_t(region,szn,t)) ;

parameter lk1_region(region,m) "--MW-- demand by RTO";
lk1_region(region,m) = sum(t$(t.val=cur_year),lmnt_region(region,m,t)) ;

parameter load_calibration_adjustment ;
load_calibration_adjustment = 1;

table load_proj_mult(nerc,allyearsbeyond) 
$ondelim 
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%regional_load_multipliers_8760.csv
$offdelim
;

* ------------------------------------------
* --- all technology capacity parameters ---
* ------------------------------------------

parameter STORold(n,storetech) --MW-- capacity of storage technology 'st' in BA 'n' ;
STORold(r,storetech)$rfeas(r) = sum{(i,c,rs,t)$[STORAGE(i) and sameas(i,storetech) and t.val=cur_year], CAP.l(i,c,r,t)} ;
STORold(r,storetech)$rfeas(r) = sum{(i,c,rs,t)$[STORAGE(i) and sameas(i,storetech) and t.val=cur_year], CAP.l(i,c,r,t)} ;

* -------------------------------
* --- outage rate parameters ---
* -------------------------------

* NOTE: FOq and POq are the same name in R and R2
parameter Foq2(q) "forced (unplanned) outage rate" ;
$load FOq2=Foq

parameter Poq2(q) "planned outage rate";
$load Poq2=Poq

parameter Fost(storetech) "forced (unplanned) outage rate for storage plants";
Fost(storetech) = 0 ;

parameter Post(storetech) "planned outage rate for storage plants";
Post(storetech) = 0 ;

* ---------------------------------------
* --- vre capacity factor parameters ---
* ---------------------------------------

parameter CFW_all(windtype,allyears,windtrg) "--fraction-- annual average capacity factor by wind type and wind TRG for all years"
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%CFW_all.csv
$offdelim
/;

parameter CF(windtrg,windtype) --fraction-- annual average capacity factor by wind type and wind TRG for the current year ;
CF(windtrg,windtype) = sum{allyears$[allyears.val=cur_year], CFW_all(windtype,allyears,windtrg)} ;

parameter CF_Corr(resreg,windtrg,windtype,m) "--unitless-- capacity factor correction factor by resource region, wind TRG, and wind type in time-slice 'm'" 
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%CF_corr.csv
$offdelim
/;

parameter cf_rsc_ann(i,c,r,rs) ;
cf_rsc_ann(i,c,r,rs)$r_rs(r,rs) = sum{(h,t)$[t.val=cur_year], m_cf(i,r,h) * Hm(h)} / sum{h, Hm(h)} ;

parameter CFO(windtrg,windtype,resreg) "---unitless--- annual average capacity factor for existing wind by TRG, wind type and resource region for the current year" ;
CFO(c, windtype, resreg)$WO(c,windtype,resreg) = sum{(i, r, rs)$[WIND(i) and cw_resreg(rs,resreg) and r_rs(r,rs) ], cf_rsc_ann(i,c,r,rs)};


* UPV capacity factors do not change over time
parameter cf_rsc_x(i,n,rs,m) ;
$load cf_rsc_x = cf_rsc


* UPV capacity factors do not change over time
parameter CFUPV(n,m,pvclass) "capacity weighted average CF of hourly upv CF by BA, time slice, and pvclass"
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%CFUPV.csv
$offdelim
/;

* DUPV capacity factors do not change over time
parameter CFDUPV(n,m,pvclass) "capacity weighted average CF of hourly upv CF by BA, time slice, and pvclass"
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%CFDUPV.csv
$offdelim
/;

parameter CFOUPV(n,m,pvclass), CFODUPV(n,m,pvclass);
CFOUPV(n,m,pvclass) = CFUPV(n,m,pvclass);
CFODUPV(n,m,pvclass) = CFDUPV(n,m,pvclass);


parameter UPVsigma(n,m,pvclass) "standard deviation of hourly upv CF by BA, time slice, and pvclass"
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%UPVsigma.csv
$offdelim
/;

parameter DUPVsigma(n,m,pvclass) "standard deviation of hourly dupv CF by BA, time slice, and pvclass"
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%DUPVsigma.csv
$offdelim
/;

parameter Wind_CoefVar(resreg,windtrg,m) 
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%Wind_CoefVar.csv
$offdelim
/;

parameter Wind_Sigma(resreg,windtrg,m) "standard deviation of hourly wind CF by res reg, class, and time slice"
/
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%variability%ds%WIND_sigma.csv
$offdelim
/;


* --------------------------------------------

variable CONVqctmn(q,m,n) ;
CONVqctmn.l(q,h,r)$rfeas(r) = sum{(i,c,t)$[CONV(i) and sameas(i,q) and t.val=cur_year], GEN.l(i,c,r,h,t)} ;
CONVqctmn.l("hydro",h,r)$rfeas(r) = sum{(i,c,t)$[hydro(i) and t.val=cur_year], GEN.l(i,c,r,h,t)} ;


parameter CONVOLDqctn(q,n) --MW-- capacity of conventional generation technologies 'q' in BA 'n' ;

CONVOLDqctn(q,r)$rfeas(r) = sum{(i,c,t)$[sameas(i,q) and valcap(i,c,r,t) and t.val=cur_year], CAP.l(i,c,r,t)} ;
CONVOLDqctn('hydro',r)$rfeas(r) = sum{(i,c,t)$[hydro(i) and valcap(i,c,r,t) and t.val=cur_year], CAP.l(i,c,r,t)} ;

* --------------------------------------------

variable STORout(m,n,storetech) ;
STORout.l(h,r,storetech)$rfeas(r) = sum{(i,c,t)$[STORAGE(i) and sameas(i,storetech) and t.val=cur_year], STORAGE_OUT.l(i,c,r,h,t)} ;

variable STORin(m,n,storetech) ;
STORin.l(h,r,storetech)$rfeas(r) = sum{(i,c,t)$[STORAGE(i) and sameas(i,storetech) and t.val=cur_year], STORAGE_IN.l(i,c,r,h,t)} ;

* --- capacity value ---

parameter WCCold(n,m) ;
WCCold(n,m) = WGenOld(n,m) ;

parameter PVCCold(n,m) ;
PVCCold(n,m) = UPVGenOld(n,m) + DUPVGenOld(n,m) ;


* -------------------------------
* --- capacity parameters ---
* -------------------------------
parameter cap_8760 (bigQ, c, r, t) ;
$load cap_8760  = CAP.l

parameter CONVqnallyears(bigQ,n,allyears) "--MW-- existing capacity in all years";

CONVqnallyears(bigQ,r,t)$[rfeas(r)] = sum{(c), CAP_8760 (bigQ,c,r,t)}
;

* ---------------------------------
* --- variable cost parameters ---
* ---------------------------------

parameter data_conv_x(allyears, bigQ, *);
$load data_conv_x=data_conv

parameter CvarOM_all(allyears, q) ;
CvarOM_all(allyears, q) = data_conv_x(allyears, q, 'cost_vom') ;

parameter CvarOM(q) ;
CvarOM(q) = sum{allyears$[allyears.val=cur_year],
                CvarOM_all(allyears,q)
            };

parameter CvarOM_hydro_base(hydcats,n) ;
CvarOM_hydro_base(hydcats,n) = sum{allyears$[allyears.val=cur_year], 
                data_conv_x(allyears, hydcats, 'cost_vom') } ;

* -------------------------------
* ---- generation parameters ---
* -------------------------------
parameter sply_8760 (bigQ, c, r, h,t) ;
$load sply_8760  = GEN.l

parameter CONVqmnallm(bigQ,n,allyears,m) "--avg MW-- average generation by technology, BA, and time-slice for all years"  ;

CONVqmnallm(bigQ,r,t,h)$[rfeas(r)] = sum{(c), sply_8760 (bigQ,c,r,h,t)} ;


CONVqmnallm(storetech,n,allyears,m)$(allyears.val=cur_year) = STORout.l(m,n,storetech) - STORin.l(m,n,storetech) ;


CONVqmnallm('curtail',r,t,h)$[t.val=cur_year] =   sum((i,c,rs)$(rsc_i(i)$r_rs(r,rs)$valcap(i,c,r,t)$m_cf(i,r,h)),
                                                      CURT.l(r,h,t) * m_cf(i,r,h) * CAP.l(i,c,r,t) ) ;

CONVqmnallm('transmission',n,allyears,m)$[allyears.val=cur_year] = sum{p, lineflow(n,p,m) + dc_lineflow(n,p,m)} ;

CONVqmnallm('reqt',r,t,h)$rfeas(r) = sum{(bigQ,c), sply_8760 (bigQ,c,r,h,t)} ;

* -----------------------------------
* --- hydro generation parameter ---
* -----------------------------------

parameter HydCap_allyrs(hydcats,n,m,allyears) "--MW-- average generation for hydro plants by BA and time slice for all years";
HydCap_allyrs(hydDcats,r,h,t)$rfeas(r) = sum{c, sply_8760 (hydDcats, c, r, h, t)} ;

HydCap_allyrs(hydNDcats,r,h,t)$rfeas(r) = sum{c, sply_8760 (hydNDcats,c,r,h,t)} ;

* ------------------------------------------
* ---- conventional heat rate parameters ---
* ------------------------------------------

parameter RegCapAdjnq(n,q) ;
RegCapAdjnq(n,q) = 1 ;

parameter CheatRate_all(allyears,q) "heat rate by year and technology";
CheatRate_all(allyears,q) = data_conv_x(allyears,q,'heat_rate') ;


parameter CheatRate(q,n) ;
CheatRate(q,n) = sum{allyears$[allyears.val=cur_year], CheatRate_all(allyears,q)} / RegCapAdjnq(n,q) ;


* -------------------------------
* --- battery parameters ---
* -------------------------------

parameter storage_efficiency(storetech) ;
$load storage_efficiency=storage_eff

parameter StorageRTE(allyears,storetech) "storage efficiency";
StorageRTE(allyears,storetech)=storage_efficiency(storetech) ;

parameter STOR_RTE(storetech) ;
STOR_RTE(storetech) = sum{allyears$[allyears.val=cur_year],
                   StorageRTE(allyears,storetech)
               };

parameter storage_duration_all(storetech) ;
$load storage_duration_all=storage_duration

* ===================================================================
* Unload data to .gdx file for 8760  execution
* ===================================================================

* using aliases (GAMS param = .gdx param)

Execute_unload "E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%curt_%case%_%cur_year%.gdx",

* sets
         cur_year,
         windtrg=c,
         pvclass,
         resreg=i,
         rfeas=n,
         region,
         m,
         s,
         q,
         storetech=st,
         bigQ,
         notpeakszn,
         seaperiods,
         notpeak,
         hourid,

         AC_routes,
         pcaj,
         nregion,
         Hm,

         class, classupv, classdupv,

         DXi, DYi,

         iwithwindtype, nwithupv, nwithdupv, windtype,

         lineflow, DC_lineflow, net_inj,

         WGenOld,

         UPVGenOld, DUPVGenOld, 

         Lmn, gen_8760 ,

         WO, UPVO, DUPVO, 

         lk2n, lk2factorRto, Pregion, Lk1_region, 

         STORold,

*
         FOq2=Foq,
         POq2=Poq,

         FOst, POst,

         CF, CF_corr, CFO,

         CFUPV, CFOUPV, CFDUPV, CFODUPV, 

         UPVsigma, DUPVsigma, 
         Wind_CoefVar, 
         Wind_Sigma,

         CONVqctmn.l, CONVOLDqctn,

         minplantload, nomsize,

         STORout.l, STORin.l,

         WCCold, PVCCold,

         transloss, 

         allyears,
         thisyear, lastsolveyear,

         distlossfactor,

         nnerc, bigQ, hydcats, hydDcats, allyearsbeyond, thisyearbeyond,

*
         nerc=r,

         CFDUPVAdj, TieLossCFAdj, CONVqnallyears, load_proj_mult,
         CvarOM, CvarOM_hydro_base, CONVqmnallm, HydCap_allyrs, CHeatrate,

         minplantload_hy, 
         StorageRTE, storage_duration_all,
         NetImportsRTO, NetImportsBA, load_calibration_adjustment

;
