* Put the following line of code in the GAMS command line to run this code using a restart file
* r=.\g00files\test_ref_seq_2010 --case=test_ref_seq --cur_year=2012 '

$eolcom //

$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix


*option profile=1 ;
*option profiletol=1 ;

$ontext
1. Load the inputs from the .gdx file created at the end of A_readinputs.gms
  - for inputs that are unique to REFLOW, load them directly
  - for inputs that are shared between ReEDS and ReEDS 2.0, use aliases
2. Compute the parameters necessary for REFLOW_RTO.gms
2. Unload the inputs to REFLOW20xx.gdx
$offtext

* ===================================================================

* call gdxin for the .gdx file created at the end of A_readinputs.gms
$gdxin inputs_case%ds%REflow_static_inputs.gdx

* --- time sets ---

alias(t,allyears) ;

scalar prev_year / %cur_year% / ;

$ifthen %timetype% == seq
* use data from the next year for a sequential solve
  scalar next_year / %next_year% / ;
$else
* use data for the current year for an intertemporal and window solve
  scalar next_year / %cur_year% / ;
$endif

* alias for time-slices
* h = reeds 2.0
* m = reeds
alias(h,m) ;

set s seasons ;
$load s

*SEASONS that are not summer
set notsummer(m) time-slices that do not occur in the summer ;
$load notsummer

set seaperiods;
$load seaperiods

* --- regional sets ---

set resregfull wind and CSP resource regions;
$load resregfull=ifull

set resreg(resregfull) wind and CSP resource regions ;
$load resreg=i

* alias for balancing area
* r = reeds 2.0
* n = reeds
alias(r,n) ;

alias(n,p) ;

set pcaj(n,resreg) crosswalk between BAs and resource regions ;
$load pcaj

*NOTE: 'RTO' this is already a set in R2
*set rto regional transmission organization ;
*$load rto

set nrto(n,rto) crosswalk between BAs and rtos ;
$load nrto

set canadan(n) ;
$load canadan

* --- technology sets ---

set windtrg  wind techno resource group  ;
$load windtrg=c

set cCSP  CSP resource class ;
$load cCSP

set pvclass PV resource class  ;
$load pvclass

set mhkwaveclass PV resource class ;
$load mhkwaveclass

set bigQ full set of technologies for reporting;
$load bigQ

set q(bigQ) conventional generation technologies ;
$load q

set coaltech(q) coal generation technologies ;
$load coaltech

set nuctech(q) nuclear generation technologies ;
$load nuctech

set distPVtech(bigQ) distPV technologies;
$load distPVtech

set storetech(bigQ) storage technologies ;
$load storetech=st

set ct cooling technologies ;
$load ct

set windtype(bigQ) ;
$load windtype

* --- technology/region sets ---

set iwithcsp(resreg) ;
$load iwithcsp

set nwithupv(n,pvclass) ;
$load nwithupv

set nwithdupv(n,pvclass) ;
$load nwithdupv

set thermal_st(storetech) ;
$load thermal_st

set iwithwindtype(resreg,windtype) ;
$load iwithwindtype

* --- random parameters ---

parameter Hm(m) ;
$load Hm

parameter DXi(resreg) x-coordinate of resource region ;
$load DXi

parameter DYi(resreg) y-coordinate of resource region ;
$load DYi

scalar CSPwStor_nomsize --MW-- nominal size of CSP-ws ;
$load CSPwStor_nomsize

scalar CSPwStor_minload --frac-- minimum load point for CSP-ws ;
$load CSPwStor_minload

parameter nomsize(q) --MW-- nominal size of technology type 'q'
$load nomsize

parameter minplantload(q)
$load minplantload

* --- transmission parameters ---

parameter lineflow(n,p,m) --avg MW-- average flow on AC lines between BAs 'n' and 'p' during time-slice 'm' ;
*lineflow(n,p,m) = AC_flow.l(m,n,p) ;
lineflow(r,rr,h)$[rfeas(r) and rfeas(rr)] = sum{(t,trtype)$[routes(rr,r,trtype,t) and t.val=prev_year and sameas(trtype,'AC')],
                      FLOW.l(r,rr,h,t,trtype)
                  } ;

parameter DC_lineflow(n,p,m) --avg MW-- average flow on DC lines between BAs 'n' and 'p' during time-slice 'm' ;
*DC_lineflow(n,p,m) = DC_flow.l(m,n,p) ;
DC_lineflow(r,rr,h)$[rfeas(r) and rfeas(rr)] = sum{(t,trtype)$[routes(rr,r,trtype,t) and t.val=prev_year and sameas(trtype,'DC')],
                         FLOW.l(r,rr,h,t,trtype)
                     } ;


parameter net_inj(n,m) --avg MW-- average net injection from BA 'n' into the grid during time-slice 'm' ;
*net_inj(n,m) = sum(p, AC_flow.l(m,p,n) * (1 - TLOSS(n,p)*Distancenp(n,p)) - AC_flow.l(m,n,p)) ;
net_inj(r,h)$rfeas(r) =  sum{(rr,t,trtype)$[rfeas(rr) and routes(rr,r,trtype,t) and t.val=prev_year and sameas(trtype,'AC')],
                               (1-tranloss(rr,r,trtype)) * FLOW.l(r,rr,h,t,trtype)
                             - FLOW.l(rr,r,h,t,trtype)
                         }
;


parameter transloss(n,m) ;
*transloss(n,m) = AC_loss.l(m,n) + sum(p$DC_routes(n,p), DC_flow.l(m,p,n) * TLOSS(n,p)*Distancenp(n,p))
transloss(r,h)$rfeas(r) = sum{(rr,t,trtype)$[rfeas(rr) and routes(rr,r,trtype,t) and t.val=prev_year],
                              tranloss(rr,r,trtype) * FLOW.l(rr,r,h,t,trtype)
                          }
;

parameter distlossfactor ;
distlossfactor = distloss ;

* --- vrre generation parameters ---

* For the sequential solve, this set will consist of all years between the previous solve and next solve, excluding the previous solve year
* For the intertemporal solve, this will be an empty set
set tcheck(t) "set of all years to check for retiring capacity"
  /
  %cur_year% * %next_year%
  /
;

tcheck(t)$[t.val=prev_year] = no ;


* get the retire year for all vre and storage investments
* NOTE the variable CAP holds degraded capacity, so when retired capacity we need to retire the degraded capacity
parameter inv_tmp(i,v,r,t,tt) "--MW-- relevant capacities along with their build year and retire year" ;
inv_tmp(i,v,r,t,tt)$[(t.val+maxage(i)=tt.val)$valcap(i,v,r,t)] =
              [INV.l(i,v,r,t) + INV_REFURB.l(i,v,r,t)] * degrade(i,t,tt)
;
* calculate exogenous retirements based on the change in exogenous capacity
parameter retire_exog_init(i,v,r,rs,t) "--MW-- exogenous retired capacity" ;
retire_exog_init(i,v,r,rs,t)$[(capacity_exog(i,v,r,rs,t-1) > capacity_exog(i,v,r,rs,t))$(not canada(i))] =
        [capacity_exog(i,v,r,rs,t-1) - capacity_exog(i,v,r,rs,t)]$initv(v)
;
* ignore vintage classes that are not "initial"
retire_exog_init(i,v,r,rs,t)$[not initv(v)] = 0 ;
* fix the r & rs indices for exogenous retirements
parameter retire_exog_tmp(i,v,r,t) "--MW-- exogenous retired capacity" ;
retire_exog_tmp(i,v,rb,t) = retire_exog_init(i,v,rb,"sk",t) ;
retire_exog_tmp(i,v,rs,t)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs), retire_exog_init(i,v,r,rs,t)} ;
* Accounting for degredation of PV capacity. As of 7/30/19 there is no pv capacity in capacity_exog, but this is included for future compatibility.
retire_exog_tmp(i,v,r,t) = retire_exog_tmp(i,v,r,t) * sum{tt$tfirst(tt),degrade(i,tt,t)} ;
* calculate all the capacity that will retire between the end of solve year t and the end of solve year t+1
parameter ret_exog(i,v,r,t) "--MW-- capacity that exogenously scheduled to retire between the previous solve year t and the end of the next solve year t+1" ;
ret_exog(i,v,r,t)$(t.val=prev_year) = sum{tcheck(tt), retire_exog_tmp(i,v,r,tt)}
;
* determine the lifetime retirements between the end of the last solve and the end of the next solve
parameter ret_lifetime(i,v,r,t) "--MW-- capacity that will be retired between the previous solve year t and the end of the next solve year t+1" ;
ret_lifetime(i,v,r,ttt)$[ttt.val=prev_year] = sum{(t,tt)$tcheck(tt), inv_tmp(i,v,r,t,tt)}
* get the capacity of vre and storage
parameter cap_est(i,v,r,t) "--MW-- relavent capacities for curtailment calculations" ;
$ifthen %timetype% == seq
* For a sequential solve, calculate the capacity that will remain on the system for the next solve year
* Capacity at end of prior solve year
* MINUS exogenous retirements through next solve year
* MINUS lifetime retirements through next solve year
* EQUALS remaining capacity for next solve year
cap_est(i,v,r,t)$[valcap(i,v,r,t)$(t.val=next_year)] = sum{tt$[tt.val=prev_year], CAP.l(i,v,r,tt) - ret_exog(i,v,r,tt) - ret_lifetime(i,v,r,tt)} ;
* Do not consider retirements for distpv since distpv capacity is defined as a monotonically increasing function
cap_est("distpv",v,r,t)$[t.val=next_year] = 0 ;
cap_est("distpv",v,r,t)$[t.val=next_year] = sum{tt$[tt.val=prev_year], CAP.l("distpv",v,r,tt)} ;
$else
* For intertemporal or window solves: use the capacity from the PRIOR iteration of the CURRENT solve year to estimate curtailment for the NEXT iteration of the SAME solve year
cap_est(i,v,r,t)$[valcap(i,v,r,t)$(t.val=prev_year)] = CAP.l(i,v,r,t)
$endif
;

parameter WGenOld(n,m) --avg MW-- average generation from existing wind in BA 'n' during time-slice 'm' ;
*WGenOld(n,m) = WGenOld(n,m) + sum((v,windtype,i)$pcaj(n,i), (WN.l(v,windtype,i) * CF(v,windtype) * CF_Corr(i,v,windtype,m))$class(v,windtype,i)) ;
WGenOld(r,h)$rfeas(r) = sum{(i,v,rr,t)$[WIND(i) and t.val=next_year and valcap(i,v,rr,t) and cap_agg(r,rr)],
                                       m_cf(i,v,rr,h,t) * cap_est(i,v,rr,t)} ;


parameter CSPGenOld(n,m) --avg MW-- average generation from existing CSP-ns in BA 'n' during time-slice 'm' ;
$ontext
CSPGenOld(n,m) = sum{ct,
                         CSPGenOldct(ct,n,m)
                       + sum{(cCsp,i)$(pcaj(n,i) and iwithcsp(i) and classcsp(cCsp,i)), CspNct.l(ct,i) * CFcsp(cCsp,m)}
;
$offtext

CSPGenOld(r,h)$rfeas(r) = sum{(i,v,rr,t)$[sameas(i,"csp-ns") and t.val=next_year and valcap(i,v,rr,t) and cap_agg(r,rr)],
                                       m_cf(i,v,rr,h,t) * cap_est(i,v,rr,t)} ;

* TODO: add this
parameter CSPstGenOld(n,m) --avg MW-- average generation from existing CSP-ws in BA 'n' during time-slice 'm' ;
* CSPstGenOld(n,m) = sum(ct, CSPTurbPowNct.l(ct,n,m) + CSPTurbPowOct.l(ct,n,m)) ;   //CSP with storage old and new
CSPstGenOld(r,h)$rfeas(r) = 0 ;

parameter UPVGenOld(n,m) --avg MW-- average generation from existing UPV in BA 'n' during time-slice 'm' ;
*UPVGenOld(n,m) = sum(pvclass$classupv(pvclass,n), UPVN.l(n,pvclass)*CFUPV(n,m,pvclass)) + UPVGenOld(n,m) ;
UPVGenOld(r,h)$rfeas(r) = sum{(i,v,rr,t)$[UPV(i) and t.val=next_year and valcap(i,v,rr,t) and cap_agg(r,rr)],
                                       m_cf(i,v,rr,h,t) * cap_est(i,v,rr,t)} ;

parameter DUPVGenOld(n,m) --avg MW-- average generation from existing DUPV in BA 'n' during time-slice 'm' ;
*DUPVGenOld(n,m) = sum(pvclass$classdupv(pvclass,n), DUPVN.l(n,pvclass)*CFDUPV(n,m,pvclass)) + DUPVGenOld(n,m) ;
DUPVGenOld(r,h)$rfeas(r) = sum{(i,v,rr,t)$[DUPV(i) and t.val=next_year and valcap(i,v,rr,t) and cap_agg(r,rr)],
                                       m_cf(i,v,rr,h,t) * cap_est(i,v,rr,t)} ;

parameter distPVGenOld(n,m) --avg MW-- average generation from existing distPV in BA 'n' during time-slice 'm' ;
*distPVGenOld(n,m) = CONVOLDqctmn.l("distPV","none",m,n) + CONVqctmn.l("distPV","none",m,n) ;
distPVGenOld(r,h)$rfeas(r) = sum{(i,v,t)$[sameas(i,"distpv") and t.val=next_year and valcap(i,v,r,t)],
                                       m_cf(i,v,r,h,t) * cap_est(i,v,r,t)} ;

parameter MHKwaveGenOld(n,m) --avg MW-- average generation from existing MHK wave in BA 'n' during time-slice 'm' ;
*MHKwaveGenOld(n,m) = CONVqctmn.l('ocean','none',m,n) + CONVOLDqctmn.l('ocean','none',m,n) ;
MHKwaveGenOld(r,h)$rfeas(r) = sum{(i,v,t)$[sameas(i,"mhkwave") and t.val=next_year and valcap(i,v,r,t)],
                                       m_cf(i,v,r,h,t) * cap_est(i,v,r,t)} ;

* --- generation parameters ---

parameter gen_reflow(m,n) --avg MW-- average generation from ALL existing non-storage generators (except distPV) in BA 'n' during time-slice 'm' ;
$ontext
gen_reflow(m,n)= Hm(m)*(sum((q,ct)$(not distpvtech(q)), CONVqctmn.l(q,ct,m,n) + CONVOLDqctmn.l(q,ct,m,n))
                 + WGenOld(n,m)
                 + sum(ct, CSPGenOldct(ct,n,m))
                 + sum(ct, (CSPTurbPowNct.l(ct,n,m)+CSPTurbPowOct.l(ct,n,m))$nwithcsp(n))
                 + UPVGenOld(n,m) + DUPVGenOld(n,m) // DistPVGenOld not included because it reduces sales
* Only subtract out the curtailment that is not from distPVgen
                 - (Surplus.l(m,n) * (WGenOld(n,m) + UPVGenOld(n,m) + DUPVGenOld(n,m) + CSPGenOld(n,m))
                   / (WGenOld(n,m) + UPVGenOld(n,m)+ DUPVGenOld(n,m) + CSPGenOld(n,m) + distPVGenOld(n,m)))$(WGenOld(n,m) + UPVGenOld(n,m) + DUPVGenOld(n,m) + CSPGenOld(n,m) + distPVGenOld(n,m))
                ) ;
$offtext


* NOTE: No need to subtract curtailment, because it is already included in GEN
gen_reflow(h,r)$rfeas(r) = sum{(i,v,t,tt)$[not sameas(i,"distPV") and not storage_no_csp(i)
                                           and t.val=prev_year and tt.val=next_year and valgen(i,v,r,tt)],
                                  GEN.l(i,v,r,h,t) * Hm(h)} ;


* --- vrre technology crosswalk sets ---

set cw_resreg(r,resregfull) crosswalk: resource regions
/
$ondelim
$include inputs_case%ds%cw_resreg.csv
$offdelim
/
;

set cw_windtech(windtype,windtrg,i) crosswalk: wind technologies  ;

cw_windtech('wind-ons','class1','wind-ons_1') = YES ;
cw_windtech('wind-ons','class2','wind-ons_2') = YES ;
cw_windtech('wind-ons','class3','wind-ons_3') = YES ;
cw_windtech('wind-ons','class4','wind-ons_4') = YES ;
cw_windtech('wind-ons','class5','wind-ons_5') = YES ;
cw_windtech('wind-ons','class6','wind-ons_6') = YES ;
cw_windtech('wind-ons','class7','wind-ons_7') = YES ;
cw_windtech('wind-ons','class8','wind-ons_8') = YES ;
cw_windtech('wind-ons','class9','wind-ons_9') = YES ;
cw_windtech('wind-ons','class10','wind-ons_10') = YES ;

cw_windtech('wind-ofs','class1','wind-ofs_1') = YES ;
cw_windtech('wind-ofs','class2','wind-ofs_2') = YES ;
cw_windtech('wind-ofs','class3','wind-ofs_3') = YES ;
cw_windtech('wind-ofs','class4','wind-ofs_4') = YES ;
cw_windtech('wind-ofs','class5','wind-ofs_5') = YES ;
cw_windtech('wind-ofs','class6','wind-ofs_6') = YES ;
cw_windtech('wind-ofs','class7','wind-ofs_7') = YES ;
cw_windtech('wind-ofs','class8','wind-ofs_8') = YES ;
cw_windtech('wind-ofs','class9','wind-ofs_9') = YES ;
cw_windtech('wind-ofs','class10','wind-ofs_10') = YES ;
cw_windtech('wind-ofs','class11','wind-ofs_11') = YES ;
cw_windtech('wind-ofs','class12','wind-ofs_12') = YES ;
cw_windtech('wind-ofs','class13','wind-ofs_13') = YES ;
cw_windtech('wind-ofs','class14','wind-ofs_14') = YES ;
cw_windtech('wind-ofs','class15','wind-ofs_15') = YES ;

set cw_windtech2(windtype,i) ;
cw_windtech2('wind-ons','wind-ons_1') = YES ;
cw_windtech2('wind-ons','wind-ons_2') = YES ;
cw_windtech2('wind-ons','wind-ons_3') = YES ;
cw_windtech2('wind-ons','wind-ons_4') = YES ;
cw_windtech2('wind-ons','wind-ons_5') = YES ;
cw_windtech2('wind-ons','wind-ons_6') = YES ;
cw_windtech2('wind-ons','wind-ons_7') = YES ;
cw_windtech2('wind-ons','wind-ons_8') = YES ;
cw_windtech2('wind-ons','wind-ons_9') = YES ;
cw_windtech2('wind-ons','wind-ons_10') = YES ;

cw_windtech2('wind-ofs','wind-ofs_1') = YES ;
cw_windtech2('wind-ofs','wind-ofs_2') = YES ;
cw_windtech2('wind-ofs','wind-ofs_3') = YES ;
cw_windtech2('wind-ofs','wind-ofs_4') = YES ;
cw_windtech2('wind-ofs','wind-ofs_5') = YES ;
cw_windtech2('wind-ofs','wind-ofs_6') = YES ;
cw_windtech2('wind-ofs','wind-ofs_7') = YES ;
cw_windtech2('wind-ofs','wind-ofs_8') = YES ;
cw_windtech2('wind-ofs','wind-ofs_9') = YES ;
cw_windtech2('wind-ofs','wind-ofs_10') = YES ;
cw_windtech2('wind-ofs','wind-ofs_11') = YES ;
cw_windtech2('wind-ofs','wind-ofs_12') = YES ;
cw_windtech2('wind-ofs','wind-ofs_13') = YES ;
cw_windtech2('wind-ofs','wind-ofs_14') = YES ;
cw_windtech2('wind-ofs','wind-ofs_15') = YES ;

set cw_csptech(cCSP,i) crosswalk: csp-ns technologies;
cw_csptech('cspclass3','csp-ns') = YES ;

set cw_upvtech(pvclass,i) crosswalk: upv technologies;

cw_upvtech('class1','upv_1') = YES ;
cw_upvtech('class2','upv_2') = YES ;
cw_upvtech('class3','upv_3') = YES ;
cw_upvtech('class4','upv_4') = YES ;
cw_upvtech('class5','upv_5') = YES ;
cw_upvtech('class6','upv_6') = YES ;
cw_upvtech('class7','upv_7') = YES ;
cw_upvtech('class8','upv_8') = YES ;
cw_upvtech('class9','upv_9') = YES ;

set cw_dupvtech(pvclass,i) crosswalk: dupv technologies;

cw_dupvtech('class1','dupv_1') = YES ;
cw_dupvtech('class2','dupv_2') = YES ;
cw_dupvtech('class3','dupv_3') = YES ;
cw_dupvtech('class4','dupv_4') = YES ;
cw_dupvtech('class5','dupv_5') = YES ;
cw_dupvtech('class6','dupv_6') = YES ;
cw_dupvtech('class7','dupv_7') = YES ;
cw_dupvtech('class8','dupv_8') = YES ;
cw_dupvtech('class9','dupv_9') = YES ;

* --- vrre capacity parameters ---

parameter WO(windtrg,windtype,resreg) "--MW-- existing wind capacity by wind TRG, wind type, and resource region"  ;
*WO(v,windtype,i) = WN.l(v,windtype,i)$class(v,windtype,i) + WO(v,windtype,i)$iwithwindtype(i,windtype) ;
WO(windtrg,windtype,resreg) = sum{(i,v,r,t)$[valcap(i,v,r,t) and WIND(i) and cw_windtech(windtype,windtrg,i)
                                  and cw_resreg(r,resreg) and t.val=next_year],
                                    cap_est(i,v,r,t)
                                } ;
* Sometimes there are very small negative numbers for wind in CAP. This will eliminate those.
WO(windtrg,windtype,resreg) = round(WO(windtrg,windtype,resreg), 5)

parameter CspOct(cCsp,ct,resreg) "--MW-- existing CSP-ns capacity by class, cooling tech, and resource region" ;
*CspOct(cCsp,ct,i) = CspNct.l(ct,i)*classcsp(cCsp,i) + CspOct(cCsp,ct,i) ;

CspOct(cCsp,'none',resreg) = sum{(i,v,r,t)$[csp_nostorage(i) and cw_csptech(cCSP,i) and cw_resreg(r,resreg)
                                  and t.val=next_year], cap_est(i,v,r,t)} ;

parameter UPVO(n,pvclass) "--MW-- existing UPV capacity by class and BA" ;
*UPVO(n,pvclass) = UPVO(n,pvclass)$nwithupv(n,pvclass) + UPVN.l(n,pvclass)$classupv(pvclass,n) ;
UPVO(r,pvclass)$rfeas(r) = sum{(i,v,t)$[UPV(i) and cw_upvtech(pvclass,i) and t.val=next_year], cap_est(i,v,r,t)} ;

parameter DUPVO(n,pvclass) "--MW-- existing DUPV capacity by class and BA" ;
*DUPVO(n,pvclass) = DUPVO(n,pvclass)$nwithdupv(n,pvclass) + DUPVN.l(n,pvclass)$classdupv(pvclass,n)
DUPVO(r,pvclass)$rfeas(r) = sum{(i,v,t)$[DUPV(i) and cw_dupvtech(pvclass,i) and t.val=next_year], cap_est(i,v,r,t)} ;


* --- class sets ---

* NOTE: these are computed based on remaining resource
parameter class(windtrg,windtype,resreg) ;
class(windtrg,windtype,resreg)$sum{(i,v,r,t)$[cw_windtech(windtype,windtrg,i) and cw_resreg(r,resreg)
                                  and rfeas(r) and t.val=next_year], valcap(i,v,r,t)} = YES ;

parameter classcsp(cCSP,resreg) ; // only one class is allowed
classcsp(cCSP,resreg)$sum{(i,v,r,t)$[cw_csptech(cCSP,i) and cw_resreg(r,resreg) and
                          rfeas(r) and t.val=next_year], valcap(i,v,r,t)} = YES ;

parameter classupv(pvclass,n) ;
classupv(pvclass,r)$[rfeas(r) and sum{(i,v,t)$[cw_upvtech(pvclass,i) and t.val=next_year], valgen(i,v,r,t)}] = YES ;

parameter classdupv(pvclass,n) ;
classdupv(pvclass,r)$[rfeas(r) and sum{(i,v,t)$[cw_dupvtech(pvclass,i)and t.val=next_year], valgen(i,v,r,t)}] = YES ;

* --- load parameters ---

parameter Lmn(n,m) ;
Lmn(r,h)$rfeas(r) = sum{(t)$[t.val=next_year], load_exog(r,h,t) + can_exports_h(r,h,t)} ;

parameter lk2n(n,m) ;
$load lk2n

parameter lk2factorRTO(rto,m) ;
$load lk2factorRTO

parameter lk1_rto(rto,m) ;
$load lk1_rto

* --- all technology capacity parameters ---

parameter CONVOLDqctn(q,ct,n) --MW-- capacity of conventional generation technologies 'q' of cooling technology type 'ct' in BA 'n' ;

$ontext
CONVOLDqctn(q,ct,n) = CONVOLDqctn(q,ct,n) + CONVqctn.l(q,ct,n) - RETIREqctn.l(q,ct,n)
                 + sum(qq, UPGRADEqctn.l(qq,q,ct,n)) - sum(qq, UPGRADEqctn.l(q,qq,ct,n)) - (UPGRADEqctn.l('coaloldscr',q,ct,n)*CCS_retro_Capderatepen)$coalccstech(q)
                 + sum(ct2, ctUPGRADEqctn.l(q,ct2,ct,n)*ctMultRetCTtoCT2Capac(q,ct2,ct)) - sum(ct2, ctUPGRADEqctn.l(q,ct,ct2,n)) ;
$offtext
* NOTE: cooling technologies do not matter in this case; using "none"
CONVOLDqctn(q,'none',r)$rfeas(r) = sum{(i,v,t)$[sameas(i,q) and valcap(i,v,r,t) and t.val=next_year], cap_est(i,v,r,t)} ;
CONVOLDqctn('hydro','none',r)$rfeas(r) = sum{(i,v,t)$[hydro(i) and valcap(i,v,r,t) and t.val=next_year], cap_est(i,v,r,t)} ;
CONVOLDqctn('geothermal','none',r)$rfeas(r) =  sum{(i,v,t)$(valcap(i,v,r,t)$geo(i)$(t.val=next_year)), cap_est(i,v,r,t)};


parameter STORold(n,storetech) --MW-- capacity of storage technology 'st' in BA 'n' ;

*STORold(n,st) = STORold(n,st) + STOR.l(n,st) ;
STORold(r,storetech)$rfeas(r) = sum{(i,v,t)$[STORAGE(i) and sameas(i,storetech) and t.val=next_year], cap_est(i,v,r,t)} ;

* --- outage rate parameters ---

* NOTE: FOq and POq are the same name in R and R2
parameter Foq2(q) ;
$load FOq2=Foq

parameter Poq2(q) ;
$load Poq2=Poq

parameter Fost(storetech) ;
$load Fost

parameter Post(storetech) ;
$load Post

* --- vrre capacity factor parameters ---

parameter CF(resreg,windtrg,windtype,m) "--unitless-- capacity factor correction factor by resource region, wind TRG, and wind type in time-slice 'm'" ;
CF(resreg,windtrg,windtype,h) = sum{(i,v,rs,t)$[wind(i) and valcap(i,v,rs,t) and t.val=next_year and cw_resreg(rs,resreg) and cw_windtech(windtype,windtrg,i)],
                                       m_cf(i,v,rs,h,t) } ;

parameter cf_rsc_ann(i,v,r) ;
*cf_rsc_ann(i,v,r,rs)$r_rs(r,rs) = sum{h, cf_rsc(i,v,r,rs,h) * Hm(h)} / sum{h, Hm(h)} ;
cf_rsc_ann(i,v,r) = sum{(h,t)$[t.val=next_year], m_cf(i,v,r,h,t) * Hm(h)} / sum{h, Hm(h)} ;

parameter cap_wind(windtrg,windtype,resreg) ;
cap_wind(windtrg,windtype,resreg) = sum{(i,v,r,t)$[WIND(i) and cw_windtech(windtype,windtrg,i) and
                                    cw_resreg(r,resreg) and t.val=next_year], cap_est(i,v,r,t)}

parameter CFO(windtrg,windtype,resreg,h) "---unitless--- annual average capacity factor for existing wind by TRG, wind type, resource region and time slice for the current year" ;

CFO(windtrg,windtype,resreg,h)$cap_wind(windtrg,windtype,resreg) =
                            sum{(i,v,r,t)$[WIND(i) and cw_windtech(windtype,windtrg,i) and cw_resreg(r,resreg)
                                          and valcap(i,v,r,t) and t.val=next_year],
                                m_cf(i,v,r,h,t) * cap_est(i,v,r,t)}
                             / cap_wind(windtrg,windtype,resreg)
;

parameter CFCSPallyears(allyears,m,cCSP) ;
$load CFCSPallyears

parameter CFcsp(cCsp,m) ;
CFCsp(cCsp,m) = sum{allyears$[allyears.val=next_year], CFCSPallyears(allyears,m,cCSP)} ;

parameter CSPsigma(cCsp,m) ;
$load CSPsigma

* UPV capacity factors do not change over time
parameter CFOUPV(n,m,pvclass) ;
$load CFOUPV = CFUPV

* UPV capacity factors do not change over time
parameter CFUPV(n,m,pvclass) ;
$load CFUPV

* DUPV capacity factors do not change over time
parameter CFODUPV(n,m,pvclass) ;
$load CFODUPV = CFDUPV

* DUPV capacity factors do not change over time
parameter CFDUPV(n,m,pvclass) ;
$load CFDUPV

parameter distPVCF(n,m) ;
$load distPVCF

* Wave capacity factors do not change over time
parameter WAVECFO(n,mhkwaveclass,m) ;
$load WAVECFO = WAVECF

* Wave capacity factors do not change over time
parameter WAVECF(n,mhkwaveclass,m) ;
$load WAVECF

parameter UPVsigma(n,m,pvclass) ;
$load UPVsigma

parameter DUPVsigma(n,m,pvclass) ;
$load DUPVsigma

parameter distPVsigma(n,m) ;
$load distPVsigma

table Wind_CoefVar(resreg,windtrg,m)
$offlisting
$ondelim
$include inputs_case%ds%Wind_CoeffVar.csv
$offdelim
$onlisting
;

table Wind_Sigma(resreg,windtrg,m)
$offlisting
$ondelim
$include inputs_case%ds%Wind_Sigma.csv
$offdelim
$onlisting
;

* --------------------------------------------
* NOTE: CONVqctmn and CONVOLDqctmn are added together in REFLOW, so we only need one or the other
* It is difficult to separate out "Old" and "New"

parameter ctallowqct(q,ct) ;
$load ctallowqct

variable CONVqctmn(q,ct,m,n) ;
CONVqctmn.l(q,ct,m,n)$ctallowqct(q,ct) = 0 ;

* do not need the cooling tech distinction, so using 'none' as a placeholder
variable CONVOLDqctmn(q,ct,m,n) ;
CONVOLDqctmn.l(q,'none',h,r)$rfeas(r) =
            sum{(i,v,t,tt)$[CONV(i) and sameas(i,q) and t.val=prev_year
                           and tt.val=next_year and valgen(i,v,r,tt)], GEN.l(i,v,r,h,t)} ;

CONVOLDqctmn.l("hydro",'none',h,r)$rfeas(r) =
            sum{(i,v,t,tt)$[hydro(i) and t.val=prev_year
                           and tt.val=next_year and valgen(i,v,r,tt)], GEN.l(i,v,r,h,t)} ;

CONVOLDqctmn.l("geothermal",'none',h,r)$rfeas(r) =
            sum((i,v,t,tt)$[valgen(i,v,r,t)$geo(i)$(t.val=prev_year)
                           and tt.val=next_year and valgen(i,v,r,tt)],GEN.l(i,v,r,h,t)) ;

* --------------------------------------------

variable STORout(m,n,storetech) ;
STORout.l(h,r,storetech)$rfeas(r) = sum{(i,v,t,tt)$[storage_no_csp(i) and sameas(i,storetech) and t.val=prev_year and tt.val=next_year and valgen(i,v,r,tt)], GEN.l(i,v,r,h,t)} ;

variable STORin(m,n,storetech) ;
STORin.l(h,r,storetech)$rfeas(r) = sum{(i,v,t,tt)$[storage_no_csp(i) and sameas(i,storetech) and t.val=prev_year and tt.val=next_year and valgen(i,v,r,tt)], STORAGE_IN.l(i,v,r,h,t)} ;

* --- capacity credit ---
*TODO: fill these with values from the previous REFLOW execution
parameter WCCold(n,m) ;
WCCold(n,m) = WGenOld(n,m) ;

parameter CSPCCold(n,m) ;
CSPCCold(n,m) = CSPGenOld(n,m) ;

parameter PVCCold(n,m) ;
PVCCold(n,m) = UPVGenOld(n,m) + DUPVGenOld(n,m) + distPVGenOld(n,m) ;

parameter MHKWCCold(n,m) ;
MHKWCCold(n,m) = MHKwaveGenOld(n,m) ;

$gdxin



* ===================================================================
* Unload data to .gdx file for REFLOW execution
* ===================================================================

* using aliases (GAMS param = .gdx param)

Execute_unload "outputs%ds%variabilityFiles%ds%REflow_%case%_%next_year%.gdx",

* sets
         prev_year,
         windtrg=v,
         cCSP,
         pvclass,
         mhkwaveclass,
***
         resreg=i,
         rfeas=n,
         rto,
         m,
         s,
         q,
         distPVtech,
         ct,
***
         storetech=st,
         notsummer,
         seaperiods,
         pcaj,
         nrto,
         Hm,

         class, classcsp, classupv, classdupv,

         DXi, DYi,

         iwithwindtype, iwithcsp, nwithupv, nwithdupv, thermal_st, windtype,

         lineflow, DC_lineflow, net_inj,

         WGenOld, CSPGenOld, CSPstGenOld,

         CSPwStor_nomsize, CSPwStor_minload,

         UPVGenOld, DUPVGenOld, distPVGenOld, MHKwaveGenOld,

         Lmn, gen_reflow,

         WO, CSPOct, UPVO, DUPVO

         lk2n, lk2factorRto, Lk1_rto,

         CONVOLDqctn, STORold,

***
         FOq2=Foq,
         POq2=Poq,

         FOst, POst,

         CF, CFO, CFcsp,

         CSPsigma, CFUPV, CFOUPV, CFDUPV, CFODUPV, distPVCF, WAVECF, WAVECFO,

         UPVsigma, DUPVsigma, distPVsigma,
         Wind_CoefVar, Wind_Sigma,

         nomsize, minplantload,

         CONVqctmn.l, CONVOLDqctmn.l, STORout.l, STORin.l,

         WCCold, CSPCCold, PVCCold, MHKWCCold,

         transloss, canadan,

         allyears,

         distlossfactor

;
