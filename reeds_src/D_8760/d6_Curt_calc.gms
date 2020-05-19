
$ontext
Main difference between this and US 8760 is we have removed cooling technologies, CSP, distPV, and MHKWave


To run this file independently, type the u1, u2, u3, and u4 values into the  text bar at the top (separated by space) and then press the red run button
e.g., u1=US u2=2012 u3=OFF u4=CConly u5=LDC_static_inputs_07_14_2017.gdx
u1 is the interconnect
u2 is the year
u3 is ReFlowSwitch
u4 is LDCvariabilitySwitch
u5 is HourlyStaticFile

Patrick Sullivan May 26, 2011
This file reads in some ReEDS outputs (in particular, wind, load, flows) and calculates:
         1. How power is transmitted around the network. That is, how is the energy dispersed.
            I make an assumption of proportionality: that all inflows mix and are distributed evenly among outflows.
         2. The capacity value of VRRE installations at each node. This is based on the capacity value at the various
            destinations of that wind but is brought back to the source.
         3. The marginal capacity value of a new 100 MW VRRE generator at each (c,i) or (n), again, based on how that energy will be
            dispersed across the network.
         4. Curtailments for the existing system: all VRRE, storage and must-run considered
         5. Marginal curtailment for a new 100 MW VRRE plant at each (c,i) or (n).
         6. Marginal curtailment induced by new must-run capacity.
         7. Marginal curtailment reduction associated with new storage capacity.

Inputs to this algorithm are the sets, parameters, and variables shipped over from ReEDS in the
8760.gdx file. There are additional input files for the VRRE correlation data; those parameters
never enter ReEDS, so are loaded here separately from their respective excel files.

This algorithm sends the computed variability parameters back to ReEDS via variability.gdx.
That unload statement is at the very bottom of this file.
$offtext

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

*Set the end of line comment to //
$eolcom //

$onlisting
$offdollar
$offinclude
$offuelxref
$lines 0
$stitle
$offsymxref
* this turns off printing the list but also , where the symbol or parameter is used and defined etc.....
$offsymlist
* to cease the symbol list
$offuellist
* this just turns off the element reference list
$offuelxref

Option PROFILE = 2
* THIS STATEMENT LIMITS PROFILE output to items taking more than 2 seconds
Option PROFILETOL = 2



$setglobal Interconnect %gams.user1%
$setglobal begy %gams.user2%
$setglobal projectfolder '%gams.curdir%'
$setglobal outputfolder '%projectfolder%%ds%D_8760'
$setglobal Do8760Switch %gams.user3%
$setglobal LDCvariabilitySwitch %gams.user4%
$setglobal HourlyStaticFile %gams.user5%
$if not set cur_year $setglobal cur_year %begy%


$gdxin E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%curt_%case%_%cur_year%.gdx

* load sets and parameters from .gdx file
Sets c, pvclass, i, n, region, nregion, m, s, q, st, notpeakszn, seaperiods(m,s), AC_routes, pcaj,
         windtype, iwithwindtype, nwithupv, nwithdupv, allyears ;
$loaddc c, pvclass, i, n, region, nregion, m, s, q, st, notpeakszn, seaperiods, windtype, iwithwindtype, nwithupv, nwithdupv, allyears

alias(n,p,nn,pp) ;
alias(i,j,ii) ;
alias(windtype,windtype2);
alias(c,c2,c3,c4) ;

$load AC_routes, pcaj

AC_routes(n,p) = yes$(AC_routes(p,n) or AC_routes(n,p)) ;
AC_routes(n,n) = yes ;


Scalar cur_year,
       distlossfactor
;

Parameter Hm(m),
         class(c,windtype,i),
         classupv(pvclass,n),
         classdupv(pvclass,n),
         load(n,m),
         gen(m,n),
         flow(n,p,m), DC_flow(n,p,m)
         net_injection(n,m)
         transloss(n,m)
;
$load Hm, class, classupv, classdupv, load = Lmn, gen = gen_8760, flow = lineflow, DC_flow = DC_lineflow
$load net_injection = net_inj, cur_year, transloss, distlossfactor


Parameter WGenOld(n,m),
         UPVGenOld(n,m),
         DUPVGenOld(n,m),
         DXi(i) horizontal distance X for region i,
         DYi(i) vertical distance Y for region i
;
$load WGenOld, UPVGenOld, DUPVGenOld, DXi, DYi


Variables STORout(m,n,st), STORin(m,n,st) ;
$load STORout, STORin

$gdxin
;

* DUPV--specific versions of powfrac_downstream with conditional shipping.
Parameter DUPVpowfrac_downstream(n,p,m) powfrac_downstream adjusted for distribution line losses and DUPV excess generation requirement,
         gen_load_ratio(n,m) ratio of generation to the load
;

*------------------ Dispersion of Wind Power --------------------------*
Parameter totgen(n,m) 'Total Generation in (n,m), calculated as load + outflows - inflows',
         totload(n,m) load modified to include charging of storage and transmission losses
         A_upstream(p,n,m) 'upstream power distribution matrix',
         Ainv_upstream(n,p,m) 'inverse of A_upstream'
         A_downstream(n,p,m) 'downstream power distribution matrix'
         Ainv_downstream(n,p,m) 'inverse of A_downstream'
         through(n,m) 'flow through node n (sum of outflows, including load)'
         Powfrac_upstream(p,n,m) 'fraction of power at p that was generated at n'
         Powfrac_downstream(n,p,m) 'fraction of power generated at n that serves load at p'
         Powfrac_downi(i,p,m) 'fraction of power generated at i that serves load at p'
         Powfrac_np(n,p) 'time-averaged power distribution from n to p'
         Powfrac_ip(i,p) 'time-averaged power distribution from i to p'
         a(p,n), ainv(n,p)
         Windnp(n,p,m) 'MW of wind from n to p in m',
         Windp(p,m) 'MW of wind into p in m',
         UPVnp(n,p,m) 'MW of UPV from n to p in m',
         UPVp(p,m) 'MW of UPV into p in m',
* DUPV to allow for inter-region shipping
         DUPVnp(n,p,m) 'MW of DUPV from n to p in m',
         DUPVp(p,m) 'MW of DUPV into p in m',
         REnp(n,p,m) 'MW of all VRRE from n to p in m',
         REp(p,m) 'MW of all VRRE into p in m',
         Windfrac_upstream(p,n,m) 'Fraction of wind at p that came from n',
         UPVfrac_upstream(p,n,m) 'Fraction of UPV at p that came from n',
         DUPVfrac_upstream(p,n,m) 'Fraction of DUPV at p that came from n',
         REfrac_upstream(p,n,m) 'Fraction of all VRRE at p that came from n',
         PVGenOld(n,m) generation from PV units (all 3 types) at source
;

totload(n,m) = load(n,m) + sum(st, STORin.l(m,n,st)) + transloss(n,m) ;
totgen(n,m) = totload(n,m) + net_injection(n,m) + sum(p, DC_flow(n,p,m) - DC_flow(p,n,m)) ;
totgen(n,m) = max(0, totgen(n,m)) ;

Parameter inflow(n,m), outflow(n,m) ;
inflow(p,m) = sum(n$AC_routes(n,p), flow(n,p,m)) + sum(n, DC_flow(n,p,m)) ;
outflow(n,m) = sum(p$AC_routes(n,p), flow(n,p,m)) + sum(p, DC_flow(n,p,m)) ;

through(n,m) = totload(n,m) + outflow(n,m) ;

A_upstream(p,n,m) = 0 ;
A_upstream(n,n,m) = 1 ;
A_upstream(p,n,m)$(flow(n,p,m)+DC_flow(n,p,m)>0 and through(n,m)>0) = -(flow(n,p,m) + DC_flow(n,p,m))/through(n,m) ;
A_downstream(n,p,m) = 0 ;
A_downstream(n,n,m) = 1 ;
A_downstream(n,p,m)$(flow(n,p,m)+ DC_flow(n,p,m)>0 and through(p,m)>0) = -(flow(n,p,m) + DC_flow(n,p,m))/through(p,m) ;

Loop(m,
a(p,n) = A_upstream(p,n,m) ;
execute_unload 'D_8760%ds%gdxfiles%ds%gdxforinverse_%case%_%begy%.gdx' p,a;
execute 'invert D_8760%ds%gdxfiles%ds%gdxforinverse_%case%_%begy%.gdx p a D_8760%ds%gdxfiles%ds%gdxfrominverse_%case%_%begy%.gdx ainv >> D_8760%ds%gdxfiles%ds%invert1_%case%_%begy%.log';
execute_load 'D_8760%ds%gdxfiles%ds%gdxfrominverse_%case%_%begy%.gdx' , ainv;
Ainv_upstream(p,n,m) = ainv(p,n) ;
);
Loop(m,
a(n,p) = A_downstream(n,p,m) ;
execute_unload 'D_8760%ds%gdxfiles%ds%gdxforinverse_%case%_%begy%.gdx' p,a;
execute 'invert D_8760%ds%gdxfiles%ds%gdxforinverse_%case%_%begy%.gdx p a D_8760%ds%gdxfiles%ds%gdxfrominverse_%case%_%begy%.gdx ainv >> D_8760%ds%gdxfiles%ds%invert2_%case%_%begy%.log';
execute_load 'D_8760%ds%gdxfiles%ds%gdxfrominverse_%case%_%begy%.gdx' , ainv;
Ainv_downstream(n,p,m) = ainv(n,p) ;
);

* Remove gdx files that were created to do the inverse calculation
execute 'rm D_8760%ds%gdxfiles%ds%gdxforinverse_%case%_%begy%.gdx' ;
execute 'rm D_8760%ds%gdxfiles%ds%gdxfrominverse_%case%_%begy%.gdx' ;
execute 'rm D_8760%ds%gdxfiles%ds%invert1_%case%_%begy%.log' ;
execute 'rm D_8760%ds%gdxfiles%ds%invert2_%case%_%begy%.log' ;

Powfrac_upstream(p,n,m)$(through(p,m)>0) = (1/through(p,m)) * Ainv_upstream(p,n,m)*totgen(n,m) ;
Powfrac_upstream(p,n,m)$(Powfrac_upstream(p,n,m)<1e-3) = 0 ;
Powfrac_downstream(n,p,m)$(through(n,m)>0) = (1/through(n,m)) * Ainv_downstream(n,p,m)*totload(p,m) ;
Powfrac_downstream(n,p,m)$(Powfrac_downstream(n,p,m)<1e-3) = 0 ;
Powfrac_downi(i,p,m) = sum(n$pcaj(n,i), Powfrac_downstream(n,p,m)) ;
Powfrac_np(n,p) = sum(m, Powfrac_downstream(n,p,m) * Hm(m)) / 8760 ;
Powfrac_ip(i,p) = sum(n$pcaj(n,i), Powfrac_np(n,p)) ;

Windnp(n,p,m) = WGenOld(n,m)*Powfrac_downstream(n,p,m) ;
Windp(p,m) = sum(n, Windnp(n,p,m)) ;
UPVnp(n,p,m) = UPVGenOld(n,m)*Powfrac_downstream(n,p,m) ;
UPVp(p,m) = sum(n, UPVnp(n,p,m)) ;

*Initialize downstream shipment to 0, apply weighted portion of fractional excess generation each for DUPV
*to Powfrac_downstream. Then, set shipment to remaining non-adjusted Powfrac_downstream value for n=n. Finally, adjust
*only the shipped fractions (n not equal to p) for distribution line losses squared (remove distlossfactor that was
*credited to distribution PV to determine actual generation, then remove again to account for transfer to transmission lines).
DUPVpowfrac_downstream(n,p,m) = 0;
gen_load_ratio(n,m)$(gen(m,n)>load(n,m) and load(n,m)>0) = gen(m,n)/load(n,m);
gen_load_ratio(n,m)$(gen_load_ratio(n,m)>2) = 2;  // If generation is greater than 200% of the load, set the ratio to 2.  This prevents the next line from increasing Powfrac_downstream when it multiplies by (gen_load_ratio - 1)
DUPVpowfrac_downstream(n,p,m)$(gen(m,n)>load(n,m) and load(n,m)>0) = Powfrac_downstream(n,p,m)*(gen_load_ratio(n,m) - 1);
DUPVpowfrac_downstream(n,n,m) = 0;
DUPVpowfrac_downstream(n,n,m) = 1 - sum(p, DUPVpowfrac_downstream(n,p,m));
DUPVpowfrac_downstream(n,p,m) = DUPVpowfrac_downstream(n,p,m);
DUPVpowfrac_downstream(n,p,m)$(distlossfactor > 0) = DUPVpowfrac_downstream(n,p,m)/(distlossfactor**2) ;
DUPVpowfrac_downstream(n,n,m) = DUPVpowfrac_downstream(n,n,m);
DUPVpowfrac_downstream(n,n,m)$(distlossfactor > 0) = DUPVpowfrac_downstream(n,n,m)*(distlossfactor**2) ;  //apply credit back to self-consuming regions

*Use DUPV specific fractional shippments above
DUPVnp(n,p,m) = DUPVGenOld(n,m)*DUPVpowfrac_downstream(n,p,m) ;
DUPVp(p,m) = sum(n, DUPVnp(n,p,m)) ;


REnp(n,p,m) = Windnp(n,p,m) + UPVnp(n,p,m) + DUPVnp(n,p,m) ;

REp(p,m) = sum(n, REnp(n,p,m)) ;
PVGenOld(n,m) = UPVGenOld(n,m) + DUPVGenOld(n,m) ;

Windfrac_upstream(p,n,m) = 0 ;
Windfrac_upstream(n,n,m) = 1 ;
Windfrac_upstream(p,n,m)$Windp(p,m) = Windnp(n,p,m) / Windp(p,m) ;
Windfrac_upstream(p,n,m)$(Windfrac_upstream(p,n,m)<0.001) = 0 ;
UPVfrac_upstream(p,n,m) = 0 ;
UPVfrac_upstream(n,n,m) = 1 ;
UPVfrac_upstream(p,n,m)$UPVp(p,m) = UPVnp(n,p,m) / UPVp(p,m) ;
UPVfrac_upstream(p,n,m)$(UPVfrac_upstream(p,n,m)<0.001) = 0 ;
DUPVfrac_upstream(p,n,m) = 0 ;
DUPVfrac_upstream(n,n,m) = 1 ;
DUPVfrac_upstream(p,n,m)$DUPVp(p,m) = DUPVnp(n,p,m) / DUPVp(p,m) ;
DUPVfrac_upstream(p,n,m)$(DUPVfrac_upstream(p,n,m)<0.001) = 0 ;
REfrac_upstream(p,n,m) = 0 ;
REfrac_upstream(n,n,m) = 1 ;
REfrac_upstream(p,n,m)$REp(p,m) = REnp(n,p,m) / REp(p,m) ;
REfrac_upstream(p,n,m)$(REfrac_upstream(p,n,m)<0.001) = 0 ;


*---------------- Import and Compute Correlation Coeffs --------------------*


Parameters w_w_correlation(i,c,ii,c2),
         upv_upv_correlation(i,j,m) correlation coefficient between upv of region i and upv of region j (assume same for DUPV and distPV)
         upv_upv_correlnp(n,p,m) correlation coefficient between upv of region n with upv of region p (assume same for DUPV and distPV)
;

w_w_correlation(i,c,ii,c2) = 1;
upv_upv_correlation(i,j,m) = 1;
upv_upv_correlnp(n,p,m) = 1;

*upv_upv_correlnp(n,p,m) = 0;
*upv_upv_correlnp(n,p,m) =
*               sum((i,j)$(pcaj(n,i) and pcaj(p,j)), upv_upv_correlation(i,j,m))/
*              (sum(i$pcaj(n,i),1)*sum(j$pcaj(p,j),1));
upv_upv_correlnp(n,n,m) = 1;


*------------------ Capacity Value Calculations -----------------------*

Parameter wvarianceold(c,windtype,i,m) the variance associated with old wind capacity (i.e. all capacity up to now),
         wvariance(c,windtype,i,m) wind variance from above corrected by the ratio of the variance for the user and the variance calculated by the regression for the above,
         wsigmaold(c,windtype,i,m) standard deviation of the existing wind generation distribution,
         wsigma(c,windtype,i,m) standard deviation of the wind generation distribution,
         Wexpected(c,windtype,i,m) expected value of the wind distribution = capacity factor
         WindCap(n) wind capacity at n,
         TWcip(c,windtype,i,p) 'wind capacity of (c,i) that "ends up" at p',
         TWcipm(c,windtype,i,p,m) 'wind capacity of (c,i) that "ends up" at p at time m',
         TW(p,m) 'wind capacity that "ends up" at p',
         TW2(p,m) 'independent variances for wind serving p',
         TWcrossprod_cip(c,windtype,i,p,m) "the sum of covariances between installed wind in c,i and all other installed wind contributing to p",
         TWcrossprod(p,m) 'sum of covariances of wind serving p',
         PVCap(n) UPV + DUPV +distPV degraded capacity at n (MW),
*DUPV terms for inter-regional shipping
         UPVOp(n,p,m,pvclass) existing degraded UPV capacity that is shipped from n to p (analog of TWcip except TWcip is sum of all wind technologies) (MW),
         DUPVOp(n,p,m,pvclass) existing degraded DUPV capacity that is shipped from n to p (MW),
         TPVnpm(n,p,m) total existing degraded PV capacity (UPV+DUPV+distPV) that is shipped from n to p (MW),
         TPV(p,m) total existing degraded PV capacity (UPV+DUPV+distPV) that ends up at p (MW),
         UPVcrossprod_np(n,p,m,pvclass) sum of covariances between installed UPV in n by pvclass and all other installed PV contributing to p,
         DUPVcrossprod_np(n,p,m,pvclass) sum of covariances between installed DUPV in n by pvclass and all other installed PV contributing to p,
         UPVcrossprod(p,m,pvclass) sum of covariances of UPV serving p,
         DUPVcrossprod(p,m,pvclass) sum of covariances of DUPV serving p,
         UPV2(p,m) independent variances for UPV serving p,
         DUPV2(p,m) independent variances for DUPV serving p,

         wk1(p,m) E(Wind) (MW),
         wk2(p,m) var(W) (MW^2),

         pvk1(p,m) E(UPV+DUPV+distPV) (MW),
         upvk1(p,m) E(UPV) (MW),
         dupvk1(p,m) E(DPV) (MW),
         pvk2(p,m) var(UPV+DUPV+distPV) (MW^2),
         upvk2(p,m) var(UPV) (MW^2),
         dupvk2(p,m) var(DUPV) (MW^2),

         lk1(n,m) E(Load) (MW),
         lk2(n,m) var(L) (MW^2),
         ck1(n,m) E(C) (MW),
         ck2(n,m) var(C) (MW^2),
         sk1(n,m) E(Storage) (MW),
         sk2(n,m) var(S) (MW^2),
         Rwk1(c,windtype,i,p,m) 'E(dW) from (c,i) at p in m (MW)',
         Rupvk1(n,p,m,pvclass) 'E(UPV) from n at p in m (MW)',
         Rdupvk1(n,p,m,pvclass) 'E(dDUPV) at n in m (MW)',
         numplants(q,n),
         plantsize(q,n),
         WCCp(p,m) CC (MW) of all wind delivered to p,
         WCCold(n,m) CC (MW) of all wind installed at n,
         WCCmar_p(c,windtype,i,p,m) CC (frac) of dW at p from all i
         WCCmar(c,windtype,i,m) CC (frac) of dW at i aggregated over all p
         PVCCp(p,m) CC (MW) of all PV delivered to p,
         PVCCold(n,m) CC (MW) of all PV installed at n,
         UPVCCmar_p(n,p,m,pvclass) CC (frac) of UPV at p from all n by pvclass,
         DUPVCCmar_p(n,p,m,pvclass) CC (frac) of DUPV at p from all n by pvclass,
         UPVCCmar(n,m,pvclass) CC (frac) of UPV at n aggregated over all p by pvclass,
         DUPVCCmar(n,m,pvclass) CC (frac) of DUPV at n by pvclass
;
Scalar wincrement dW / 100 /  ;

alias(i,i2) ;
alias(c,c2) ;

* import ReEDS data

Parameters WO(c,windtype,i),  UPVO(n,pvclass), DUPVO(n,pvclass),STORold(n,st),
         lk2n(n,m), lk2_region(region,m), lk2FactorRto(region,m), lk1_region(region,m), nomsize(q), FOq(q), POq(q), FOst(st), POst(st), CF(c,windtype),
         CONVOLDqctn(q,n), 
         CF_corr(i,c,windtype,m), CFO(c,windtype,i), 
         CFUPV(n,m,pvclass), CFOUPV(n,m,pvclass),
         CFDUPV(n,m,pvclass), CFODUPV(n,m,pvclass),

         UPVsigma(n,m,pvclass),
         DUPVsigma(n,m,pvclass),
         TPVsigma(n,p,m) sum of sigma capacities for all PV from n to p,
         WCCold(n,m), PVCCold(n,m)
* import parameters for wind variability currently there are two options that will be removed when a choice is made. Wind Coefficient of Variability allows Wind sigmas
* to change as wind capacity factors change with time. Wind Sigmas use the direct standard deviations from the full hourly profiles.
         Wind_CoefVar(i,c,m) Coefficient of variation for each onshore wind class in each wind region i and timeslice m,
         Wind_Sigma(i,c,m) Standard deviation for each onshore wind class in each wind region i and timeslice m
;

$gdxin E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%curt_%case%_%cur_year%.gdx
$load WO, UPVO, DUPVO, STORold, lk2n, lk2FactorRto, nomsize
$load CONVOLDqctn
$load FOq, POq, FOst, POst, CF, CF_corr, CFO
$load UPVsigma, DUPVsigma, CFDUPV, CFODUPV, CFUPV, CFOUPV, WCCold, PVCCold, Wind_CoefVar, Wind_Sigma
$gdxin

Set windexist(c,windtype,i) "filter on class, windtype, and i where potential wind resource exists" ;
windexist(c,windtype,i)$(iwithwindtype(i,windtype) and sum(m, CF(c,windtype)*CF_corr(i,c,windtype,m))) = YES ;

Parameters WCCp_LY(p,m), PVCCp_LY(p,m);
WCCp_LY(p,m) = sum(n, WCCold(n,m) * Powfrac_downstream(n,p,m)) ;
PVCCp_LY(p,m) = 0 ;
*PVCCold(n,m) represents CC of all PV generation serving 'n' and is apportioned to 'p' using
*aggregate PV "powfrac_downstream" based on individual PV technology shipments,
*with conditional shipping applied to DUPV (embedded within DUPVnp).
PVCCp_LY(p,m) = sum(n$PVGenOld(n,m), PVCCold(n,m) * (UPVnp(n,p,m)+DUPVnp(n,p,m))/PVGenOld(n,m)) ;

* Curve fit from external variance calculations.
* Average wind speed w/ Raleigh distribution, run through representative power curve
* to produce power output probability distribution. variance computed as fn of CF.
* see windvar.xlsx for details
Wexpected(c,windtype,i,m)$(windexist(c,windtype,i)) = CF(c,windtype)*CF_corr(i,c,windtype,m) ;
wvariance(c,windtype,i,m)$(windexist(c,windtype,i)) = -0.5835*Wexpected(c,windtype,i,m)**2 + 0.6621*Wexpected(c,windtype,i,m) - 0.0374;
*Option one use for onshore wind Wind Coefficient of Variation
*wvariance(c,'wind-ons',i,m)$(windexist(c,'wind-ons',i)) = max(0,Wind_CoefVar(i,c,m) *Wexpected(c,'wind-ons',i,m));
*Option two use for onshore wind Wind Sigmas directly
*wvariance(c,'wind-ons',i,m)$(windexist(c,'wind-ons',i)) = max(0, Wind_Sigma(i,c,m)**2) ;
wvariance(c,windtype,i,m)$(windexist(c,windtype,i)) = max(0,wvariance(c,windtype,i,m));
wsigma(c,windtype,i,m)$(windexist(c,windtype,i)) =  sqrt(wvariance(c,windtype,i,m)) ;

Wexpected(c,windtype,i,m)$(windexist(c,windtype,i)) = CFO(c,windtype,i)*CF_corr(i,c,windtype,m) ;
wvarianceold(c,windtype,i,m)$(windexist(c,windtype,i)) = -0.5835*Wexpected(c,windtype,i,m)**2 + 0.6621*Wexpected(c,windtype,i,m) - 0.0374 ;
*Option one use for onshore wind Wind Coefficient of Variation
*wvarianceold(c,'wind-ons',i,m)$(windexist(c,'wind-ons',i)) = max(0,Wind_CoefVar(i,c,m) *Wexpected(c,'wind-ons',i,m));
*Option two use for onshore wind Wind Sigmas directly
*wvarianceold(c,'wind-ons',i,m)$(windexist(c,'wind-ons',i)) = max(0, Wind_Sigma(i,c,m)**2) ;
*wvarianceold(c,windtype,i,m)$(windexist(c,windtype,i)) = max(0,wvariance(c,windtype,i,m));
wvarianceold(c,windtype,i,m)$(windexist(c,windtype,i)) = max(0, wvarianceold(c,windtype,i,m)) ;

* correlation factor between wind sites in the same class and same region but not necesarily the same resource
Parameter num_wfarms(c,windtype,i) "number of 100MW wind farms in a c,i bundle. fractions allowed."
         wvar_old_corr(c,windtype,i,m) "wind variance reduced to account for not-fully-correlated wind farms contributing to same c,i."
Scalar wci_correlation "correlation between wind farms in same c,i bundle. manually set at unsubstantiated 0.9." ;
num_wfarms(c,windtype,i)$(windexist(c,windtype,i)) = max(1,(WO(c,windtype,i)/100)) ;
wci_correlation = 0.9 ;
wvar_old_corr(c,windtype,i,m)$(windexist(c,windtype,i)) = wvarianceold(c,windtype,i,m)/num_wfarms(c,windtype,i)
         + (num_wfarms(c,windtype,i)-1)/num_wfarms(c,windtype,i)*wci_correlation*wvarianceold(c,windtype,i,m) ;


*--------Wind--------
WindCap(n) = sum((c,windtype,i)$pcaj(n,i), WO(c,windtype,i)) ;
TWcip(c,windtype,i,p) = WO(c,windtype,i) * Powfrac_ip(i,p) ;
TWcipm(c,windtype,i,p,m) = WO(c,windtype,i) * Powfrac_downi(i,p,m) ;
TW(p,m) = sum((c,windtype,i), TWcipm(c,windtype,i,p,m)) ;
* Using 'p' rather than 'n' here to emphasize that 'k1' is related to generation at 'p'
wk1(p,m) = Windp(p,m) ;
wsigmaold(c,windtype,i,m)$(windexist(c,windtype,i)) =  sqrt(wvar_old_corr(c,windtype,i,m)) ;

*  The wk2 calculations resembles resembles portfolio variance calculation:
*        S(a,b)^2 = S(a)^2 + S(b)^2 + 2*covar(a,b)
*        where,
*                TW2 = S(a)^2 + S(b)^2
*                TWcrossprod = 2*covar(a,b)
*
*  As written here, TWcrossprod(i) = sum(j, var(i)*var(j)*rho(i,j)) for all 'i', where 'i' and 'j' can be the same.
*    Therefore, we subtract off the self-covariance, i.e., w_w_correlation(i,i)* sigma(i) * sigma(i) from TWcrossprod because by
*    definition the self-covariance is simply the wind site variance which is already accounted for in TW2.
*  TWcrossprod is multiplied by 1/2 here so that it can be multiplied by 2 in the Rwk2 below to make Rwk2 resemble
*    a portfolio variance calculation.

TW2(p,m) = sum((c,windtype,i)$(windexist(c,windtype,i)), wvar_old_corr(c,windtype,i,m) * abs(TWcipm(c,windtype,i,p,m))**2 ) ;
TWcrossprod_cip(c,windtype,i,p,m)$(windexist(c,windtype,i)) = wsigmaold(c,windtype,i,m) * TWcipm(c,windtype,i,p,m)
                  * sum[(c2,ii,windtype2), wsigmaold(c2,windtype2,ii,m) * TWcipm(c2,windtype2,ii,p,m) * w_w_correlation(i,c,ii,c2)]
            - w_w_correlation(i,c,i,c)*wvar_old_corr(c,windtype,i,m)*sqr(TWcipm(c,windtype,i,p,m)) ;
TWcrossprod(p,m) = 0.5*sum((c,windtype,i)$(windexist(c,windtype,i)), TWcrossprod_cip(c,windtype,i,p,m)) ;
* Using 'p' rather than 'n' here to emphasize that 'k2' is related to generation at 'p'
wk2(p,m) = TW2(p,m)+2*TWcrossprod(p,m) ;

Parameter wk2_region(region,m), TWciregionm(c,windtype,i,region,m) ;
TWciregionm(c,windtype,i,region,m)$(windexist(c,windtype,i)) = sum(p$nregion(p,region), TWcipm(c,windtype,i,p,m)) ;
wk2_region(region,m) = sum((c,windtype,i)$(windexist(c,windtype,i)), wvar_old_corr(c,windtype,i,m) * TWciregionm(c,windtype,i,region,m)**2 )
  + sum((c,windtype,i)$(windexist(c,windtype,i)), wsigmaold(c,windtype,i,m) * TWciregionm(c,windtype,i,region,m)
                  * sum[(c2,ii,windtype2), wsigmaold(c2,windtype2,ii,m) * TWciregionm(c2,windtype2,ii,region,m) * w_w_correlation(i,c,ii,c2)]
            - w_w_correlation(i,c,i,c)*wvar_old_corr(c,windtype,i,m) * TWciregionm(c,windtype,i,region,m)**2 )
;


TW(p,m)$(TW(p,m)<0.001) = 0 ;
wk2(n,m)$(wk1(n,m)<0.001) = 0 ; //intentionally set the check to be on wk1
wk1(n,m)$(wk1(n,m)<0.001) = 0 ;


*--------Solar-------

*All PV capacities listed here (PVcap, UPVO, DUPVO, etc.) are existing degraded capacity.
PVCap(n) =  sum(pvclass, UPVO(n,pvclass)$nwithupv(n,pvclass) + DUPVO(n,pvclass)$nwithdupv(n,pvclass))  ;

UPVOp(n,p,m,pvclass) = UPVO(n,pvclass)$nwithupv(n,pvclass) * Powfrac_downstream(n,p,m) ;
DUPVOp(n,p,m,pvclass) = DUPVO(n,pvclass)$nwithdupv(n,pvclass) * DUPVpowfrac_downstream(n,p,m) ;
TPVnpm(n,p,m) = sum(pvclass, UPVOp(n,p,m,pvclass) + DUPVOp(n,p,m,pvclass)) ;
TPV(p,m) = sum(n, TPVnpm(n,p,m)) ;

UPV2(p,m) = sum((n,pvclass)$nwithupv(n,pvclass), (abs(UPVsigma(n,m,pvclass) * UPVOp(n,p,m,pvclass)))**2) ;
DUPV2(p,m) = sum((n,pvclass)$nwithdupv(n,pvclass), (abs(DUPVsigma(n,m,pvclass) * DUPVOp(n,p,m,pvclass)))**2) ;


upvk1(p,m) = UPVp(p,m) ;
dupvk1(p,m) = DUPVp(p,m) ;
pvk1(p,m) = upvk1(p,m) + dupvk1(p,m) ;

TPVsigma(n,p,m) = sum(pvclass$nwithupv(n,pvclass), UPVsigma(n,m,pvclass)*UPVOp(n,p,m,pvclass))
            + sum(pvclass$nwithdupv(n,pvclass), DUPVsigma(n,m,pvclass)*DUPVOp(n,p,m,pvclass))
            ;

UPVcrossprod_np(n,p,m,pvclass)$nwithupv(n,pvclass) = UPVsigma(n,m,pvclass)*UPVOp(n,p,m,pvclass)
                  *sum[nn, TPVsigma(nn,p,m)*UPV_UPV_correlnp(n,nn,m)]
            - UPV_UPV_correlnp(n,n,m)*sqr(UPVsigma(n,m,pvclass)*UPVOp(n,p,m,pvclass))  ;

DUPVcrossprod_np(n,p,m,pvclass)$nwithdupv(n,pvclass) = DUPVsigma(n,m,pvclass)*DUPVOp(n,p,m,pvclass)
                  *sum[nn, TPVsigma(nn,p,m)*UPV_UPV_correlnp(n,nn,m)]
            - UPV_UPV_correlnp(n,n,m)*sqr(DUPVsigma(n,m,pvclass)*DUPVOp(n,p,m,pvclass))  ;

UPVcrossprod(p,m,pvclass) = 0.5*sum(n, UPVcrossprod_np(n,p,m,pvclass)) ;
DUPVcrossprod(p,m,pvclass) = 0.5*sum(n, DUPVcrossprod_np(n,p,m,pvclass)) ;

upvk2(p,m) = UPV2(p,m)+2*sum(pvclass$nwithupv(p,pvclass), UPVcrossprod(p,m,pvclass)) ;
dupvk2(p,m) = DUPV2(p,m)+2*sum(pvclass$nwithdupv(p,pvclass), DUPVcrossprod(p,m,pvclass)) ;
pvk2(p,m) = upvk2(p,m) + dupvk2(p,m)  ;


Parameter pvk2_region(region,m), upvk2_region(region,m), dupvk2_region(region,m), TPVnregionm(n,region,m),
         TPVnregionm_sigma(n,region,m) sum of sigma capacities for all PV from n to region ,
         UPVOregion(n,region,m,pvclass), DUPVOregion(n,region,m,pvclass);
UPVOregion(n,region,m,pvclass) = sum(p$nregion(p,region), UPVOp(n,p,m,pvclass)) ;
DUPVOregion(n,region,m,pvclass) = sum(p$nregion(p,region), DUPVOp(n,p,m,pvclass)) ;
TPVnregionm(n,region,m) =  sum(p$nregion(p,region), TPVnpm(n,p,m)) ;
TPVnregionm_sigma(n,region,m) = sum(pvclass$nwithupv(n,pvclass), UPVsigma(n,m,pvclass) * UPVOregion(n,region,m,pvclass))
         +  sum(pvclass$nwithdupv(n,pvclass), DUPVsigma(n,m,pvclass) * DUPVOregion(n,region,m,pvclass))
         ;

upvk2_region(region,m) = sum((n,pvclass)$nwithupv(n,pvclass), (UPVsigma(n,m,pvclass) * UPVOregion(n,region,m,pvclass))**2
         + UPVsigma(n,m,pvclass) * UPVOregion(n,region,m,pvclass)
         * sum[nn, TPVnregionm_sigma(nn,region,m) * upv_upv_correlnp(n,nn,m)]
         - upv_upv_correlnp(n,n,m)*(UPVsigma(n,m,pvclass) * UPVOregion(n,region,m,pvclass))**2 );

dupvk2_region(region,m) = sum((n,pvclass)$nwithdupv(n,pvclass), (DUPVsigma(n,m,pvclass) * DUPVOregion(n,region,m,pvclass))**2
         + DUPVsigma(n,m,pvclass) * DUPVOregion(n,region,m,pvclass)
         * sum[nn, TPVnregionm_sigma(nn,region,m) * upv_upv_correlnp(n,nn,m)]
         - upv_upv_correlnp(n,n,m)*(DUPVsigma(n,m,pvclass) * DUPVOregion(n,region,m,pvclass))**2 );

pvk2_region(region,m) = upvk2_region(region,m) + dupvk2_region(region,m)  ;

TPV(p,m)$(TPV(p,m)<0.001) = 0 ;
pvk2(n,m)$(pvk1(n,m)<0.001) = 0 ;
pvk1(n,m)$(pvk1(n,m)<0.001) = 0 ;
pvk2_region(region,m)$(sum(n$nregion(n,region), pvk1(n,m))<0.001) = 0 ;


*--------Load--------
lk1(n,m) = load(n,m) ;  //lk1 is just addition of a scalar later, so it's not used for CC.
lk2(n,m) = lk2n(n,m) * (lk1(n,m))**2 ;
lk1_region(region,m) = sum(n$nregion(n,region), lk1(n,m)) ;
lk2_region(region,m) = lk2FactorRto(region,m) * (lk1_region(region,m))**2 ;


*----Conventionals---

ck1(n,m) = sum((q), CONVOLDqctn(q,n)*(1-FOq(q))) ;
ck1(p,m) = sum(n, ck1(n,m)*Powfrac_downstream(n,p,m))  ;

numplants(q,n)$(nomsize(q) > 0) = round( CONVOLDqctn(q,n))/nomsize(q)  ;

plantsize(q,n) = nomsize(q) ;
plantsize(q,n)$numplants(q,n) = CONVOLDqctn(q,n) / numplants(q,n);
ck2(n,m) = sum(q, numplants(q,n)*plantsize(q,n)*plantsize(q,n)*foq(q)*(1-foq(q))) ;
ck2(p,m) = sum(n, ck2(n,m)*Powfrac_downstream(n,p,m))  ;

*---------Storage-----
sk1(n,m) = sum(st,
                    STORold(n,st)
                 + (STORout.l(m,n,st) - STORin.l(m,n,st))
           )
;
sk1(n,m)$(sk1(n,m) < 0) = 0 ;

Parameter Powfrac_downiregion(i,region,m),Powfrac_downnregion(n,region,m), DUPVpowfrac_downnregion(n,region,m) ;
Powfrac_downiregion(i,region,m) = sum(p$nregion(p,region), Powfrac_downi(i,p,m)) ;
Powfrac_downnregion(n,region,m) = sum(p$nregion(p,region), Powfrac_downstream(n,p,m)) ;
DUPVpowfrac_downnregion(n,region,m) = sum(p$nregion(p,region), DUPVpowfrac_downstream(n,p,m)) ;


*--------dWind-------
Rwk1(c,windtype,i,p,m)$(Powfrac_downi(i,p,m) and windexist(c,windtype,i)) = wincrement*CF(c,windtype)*CF_corr(i,c,windtype,m)*Powfrac_downi(i,p,m) ;

*Variance and covariance due to incremental wind at c,i. Does not include wk2_region for existing wind capacity
Parameter Rwk2_region(c,windtype,i,region,m);
Rwk2_region(c,windtype,i,region,m)$(Powfrac_downiregion(i,region,m) and windexist(c,windtype,i)) =
         wvariance(c,windtype,i,m) * (wincrement * Powfrac_downiregion(i,region,m))**2        //variance of the increment of wind at c,i
         + 2*wsigma(c,windtype,i,m) * wincrement * Powfrac_downiregion(i,region,m)            //2*(sum of covariances between the increment and all old wind serving region)
                  * sum[(c2,ii,windtype2), wsigmaold(c2,windtype2,ii,m)*TWciregionm(c2,windtype2,ii,region,m)*
                                 w_w_correlation(i,c,ii,c2)
                       ]
;

*separate total PV into UPV, DUPV components and add pvclass index
*--------dUPV-------
Rupvk1(n,p,m,pvclass)$(nwithupv(n,pvclass) and Powfrac_downstream(n,p,m)) = wincrement * CFUPV(n,m,pvclass) * Powfrac_downstream(n,p,m) ;

Parameter Rupvk2_region(n,region,m,pvclass);

Rupvk2_region(n,region,m,pvclass)$(nwithupv(n,pvclass) and Powfrac_downnregion(n,region,m)) =
    (UPVsigma(n,m,pvclass) * wincrement * Powfrac_downnregion(n,region,m))**2                   //variance of the increment of UPV at pvclass,n
    + 2*UPVsigma(n,m,pvclass) * wincrement * Powfrac_downnregion(n,region,m)                    //2*(sum of covariances between the increment and all old PV serving region)
                  * sum[nn, TPVnregionm_sigma(nn,region,m)*upv_upv_correlnp(n,nn,m)];

*--------dDUPV-------
Rdupvk1(n,p,m,pvclass)$(nwithdupv(n,pvclass) and DUPVpowfrac_downstream(n,p,m)) = wincrement * CFDUPV(n,m,pvclass) * DUPVpowfrac_downstream(n,p,m);

Parameter Rdupvk2_region(n,region,m,pvclass);
Rdupvk2_region(n,region,m,pvclass)$(nwithdupv(n,pvclass) and DUPVpowfrac_downnregion(n,region,m)) =
    (DUPVsigma(n,m,pvclass) * wincrement * DUPVpowfrac_downnregion(n,region,m))**2                   //variance of the increment of DUPV at pvclass,n
    + 2*DUPVsigma(n,m,pvclass) * wincrement * DUPVpowfrac_downnregion(n,region,m)                         //2*(sum of covariances between the increment and all old PV serving region)
                  * sum[nn, TPVnregionm_sigma(nn,region,m)*upv_upv_correlnp(n,nn,m)];

*-------------- End Capacity Value Calculations -----------------------*


*-------------- Start Surplus Calculations ----------------------------*

Parameters REk1(p,m) E(renewables),
         REk2(p,m) Var(renewables),
         ck1q(q,p,s) must-run conventional capacity (MW) by type,

         zk1_region(region,m),
         zk2_region(region,m),
         netimports(p,m) ,
         numplants_minq(q,p) ,
         plantsizeq(q,p),

         Surplus(region,m) curtailments at region associated with existing system (MW),
         SurpOld(n,m) curtailed VRRE at n,
         UPVSurplusmar(n,m,pvclass) marginal curtailment rate for dUPV at n,
         DUPVSurplusmar(n,m,pvclass) marginal curtailment rate for DUPV at n,
         WSurplusmar(c,windtype,i,m) marginal curtailment rate for dW at i,
         MRSurplusMar_region(m,n) curtailment induced at n by incremental increase in MR,
         MRSurplusMar(p,m) marginal curtailment rate for dMR at p,
         UPVSurplusMar_annual(n) annual marginal curtailment rate for an incremental amount of UPV at n
         DUPVSurplusMar_annual(n) annual marginal curtailment rate for an incremental amount of DUPV at n
         WSurplusMar_annual(windtype,i) annual marginal curtailment rate for an incremental amount of wind at i
;

$ifthen %Do8760Switch% == 'ON'
Parameters Bck1(p,m), Rck1(c,windtype,i,p,m), Pck1(n,p,m,pvclass), Dck1(n,p,m,pvclass), MRck1(n),
         Bck2(p,m), Rck2(c,windtype,i,p,m), Pck2(n,p,m,pvclass), Dck2(n,p,m,pvclass), MRck2(n,m),
         sk1_efficacy(n,s),
         storage_effectiveness(n,m) Effectiveness of storage to reduce curtailments via charging,
         Szk1_region(p,m),
         Szk2_region(p,m),
         MRzk1_region(p,m),
         MRzk2_region(p,m),
         Bzk1(n,m) E(C),
         Bzk2(n,m) var(C),
         Rzk1(c,windtype,i,p,m) E(C+S+W+dW+PV+MHKW),
         Rzk2(c,windtype,i,p,m) var(C+S+W+dW+PV+MHKW+L),
         Rsk1(n,m) E(dS),
         Rsk2(n,m) E(S+dS),
         StSurplus_region(p,m),
         StSurpRecMar(n,m) surplus recovered per MW of new storage capacity,
         StSurpRecMar_np(n,p,m) curtailments recovered at n via storage increase at p,
         MRfrac(n,m) must-run fraction. used to reduce netimports,
         BSurplus(region,m) curtailments at region with no VRRE (MW),
         WSurplus(c,windtype,i,region,m) curtailments at region with dW (MW),
         WSurplusmarp(c,windtype,i,p,m),
         UPVSurplus(n,region,m,pvclass) curtailments at region with dUPV (MW),
         DUPVSurplus(n,region,m,pvclass) curtailments at region with DUPV (MW),
         MRSurplus_region(p,m) curtailments at p with dMR (MW),
         MRSurplusMar_np(n,p,m) curtailments induced at n by MR increase at p,
         Rzk1_region(c,windtype,i,region,m)
         Rzk2_region(c,windtype,i,region,m)
         Bzk1_region(region,m)
         Bzk2_region(region,m)
         SurpOld_region(region,m)
         Pzk1_region(n,region,m,pvclass) E(C+S+W+PV+dUPV+MHKW),
         Pzk2_region(n,region,m,pvclass) var(C+S+W+PV+dUPV+MHKW+L),

         Dzk1_region(n,region,m,pvclass) E(C+S+W+PV+dDUPV+MHKW),
         Dzk2_region(n,region,m,pvclass) var(C+S+W+PV+dDUPV+MHKW),
         distDzk1_region(n,region,m) E(C+S+W+PV+ddistPV+MHKW),
         distDzk2_region(n,region,m) var(C+S+W+PV+ddistPV+MHKW),
         SurpOld_p(p,m)
;

Scalars max_sthrs maximum hours per storage unit where it will not be energy-limited / 36 /,
         sthrs hours of storage per storage unit / 33 /
;
$endif

* Calculate must-run portion of conventionals
Variables CONVqctmn(q,m,n) ;
Parameters minplantload(q), minplantloadqn(q,n);
$gdxin E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%curt_%case%_%cur_year%.gdx
$loaddc minplantload, CONVqctmn
$gdxin


minplantloadqn(q,n) = minplantload(q) ;

ck1q(q,n,s) = smax(m$seaperiods(m,s), CONVqctmn.l(q,m,n) );
* based on season with highest generation; 
numplants_minq(q,p)$(nomsize(q) > 0) = round(smax(s, ck1q(q,p,s)/nomsize(q)));
plantsizeq(q,p) = smax(s,ck1q(q,p,s))/max(1,numplants_minq(q,p)) * minplantloadqn(q,p);


ck1q(q,n,s) = ck1q(q,n,s) * minplantloadqn(q,n) ;
ck1(n,m) = sum((q,s)$seaperiods(m,s), ck1q(q,n,s))  ;
ck1(p,m) = sum(n, ck1(n,m)*Powfrac_downstream(n,p,m)) ;

ck2(n,m) = sum(q, numplants_minq(q,n) * plantsizeq(q,n)**2 * FOq(q)*(1-FOq(q)));
ck2(p,m) = sum(n, ck2(n,m)*Powfrac_downstream(n,p,m)) ;

* Expected renewable generation (and variance)
REk1(p,m) = wk1(p,m) + pvk1(p,m)  ;
REk2(p,m) = wk2(p,m) + pvk2(p,m)  ;


$ifthen %Do8760Switch% == 'ON'

* Finish calculate must-run portion of conventionals
MRfrac(n,m) = 0.5 ;
MRfrac(n,m)$sum((q), CONVOLDqctn(q,n)) = ck1(n,m) / sum((q), CONVOLDqctn(q,n)) ;

sk1(n,m) = sum(st,
                   STORold(n,st)
                + (STORin.l(m,n,st) - STORout.l(m,n,st))
           ) ;

* compute efficacy of storage capacity to recover surplus by a seasonable factor based on VRRE/load during that season.
*   The motivation is come up with a functional form that captures the ability of storage to “perfectly” reduce curtailment
*   in the limit of infinite storage (e.g. sthrs = max_sthrs) and not reduce any curtailment in the limit that sthrs = 0.
*   I recall playing with some hyperbolic functions to come up with a reasonable s-shaped curve, but don’t remember exactly remember the derivation right now.
* sk1_efficacy goes to 1 when sthrs = max_sthrs and goes to 0 when sthrs = 0.
* The max and min terms in the calculation ensure that sk1_efficacy is always between 0 and 1
sk1_efficacy(n,s)$(sum(m,lk1(n,m))>0) = max(0, min(1, 1-(1-sthrs/max_sthrs)*(1-exp(-(max_sthrs/sthrs) *
         ( sum(m$seaperiods(m,s), (wk1(n,m) + pvk1(n,m) )*Hm(m))
                 /sum(m$seaperiods(m,s), lk1(n,m)*Hm(m))
         )                                                      )
                                                          ) / (1-exp(-max_sthrs/sthrs))
                                )
                         )
;

*storage_effectiveness(n,m) = sum(s$seaperiods(s,m), sk1_efficacy(n,s));
storage_effectiveness(n,m) = 1;
sk1(n,m) = sum(s$seaperiods(m,s), sk1_efficacy(n,s)*sk1(n,m));

$endif


*----surplus on existing system-----*

zk1_region(region,m) = sum(p$nregion(p,region), ck1(p,m) + REk1(p,m)) - lk1_region(region,m) ;
zk2_region(region,m) = sum(p$nregion(p,region), ck2(p,m)) + lk2_region(region,m) + wk2_region(region,m)  + pvk2_region(region,m)  ;

parameter REk1_region(region,m), REk2_region(region,m), cslk1_region(region,m), cslk2_region(region,m) ;

REk2_region(region,m) = wk2_region(region,m) + pvk2_region(region,m)   ;
REK1_region(region,m) = sum(p$nregion(p,region), REk1(p,m)) ;

cslk1_region(region,m) = sum(p$nregion(p,region), ck1(p,m)) - lk1_region(region,m) ;
cslk2_region(region,m) = sum(p$nregion(p,region),  ck2(p,m)) + lk2_region(region,m) ;


Surplus(region,m) = 0 ;
Surplus(region,m)$(zk2_region(region,m)>0) = zk1_region(region,m)*errorf(zk1_region(region,m)/sqrt(zk2_region(region,m)))
                 + sqrt(zk2_region(region,m)/2/3.1416) * exp(-(zk1_region(region,m)*zk1_region(region,m))/2/zk2_region(region,m)) ;


$ifthen %Do8760Switch% == 'ON'

*----surplus with no VRRE----*
Bck1(p,m)$(lk1(p,m)>0) = ck1(p,m) * ((lk1(p,m) + REk1(p,m)) / lk1(p,m) - 1) ;
Bck2(p,m) = 0 ;
Bck2(p,m)$(ck1(p,m) > 0) = ck2(p,m) * (((Bck1(p,m) + ck1(p,m)) / ck1(p,m))**2 - 1) ;


Bzk1_region(region,m) = sum(p$nregion(p,region), ck1(p,m) + Bck1(p,m)) - lk1_region(region,m);
Bzk2_region(region,m) = sum(p$nregion(p,region), ck1(p,m) + Bck2(p,m)) + lk2_region(region,m) ;

parameter Bcslk1_region(region,m), Bcslk2_region(region,m) ;


BSurplus(region,m) = 0 ;
BSurplus(region,m)$(Bzk2_region(region,m)>0) = Bzk1_region(region,m)*errorf(Bzk1_region(region,m)/sqrt(Bzk2_region(region,m)))
                 + sqrt(Bzk2_region(region,m)/2/3.1416) * exp(-(Bzk1_region(region,m)*Bzk1_region(region,m))/2/Bzk2_region(region,m));

*----end surplus with no VRRE----*

SurpOld_region(region,m) = Surplus(region,m) - BSurplus(region,m) ;
SurpOld_p(p,m)$REk1(p,m) = REk1(p,m) * sum(region$nregion(p,region), SurpOld_region(region,m) / sum(pp$nregion(pp,region), REk1(pp,m))) ;
SurpOld(n,m) = sum(p, SurpOld_p(p,m) * REfrac_upstream(p,n,m)) ;
SurpOld(n,m)$(SurpOld(n,m)<.1) = 0 ;
SurpOld(n,m) = min(SurpOld(n,m), (WGenOld(n,m) + PVGenOld(n,m) )) ;


$endif

$ifthen %Do8760Switch% == 'ON'

*----surplus with incremental wind----*
* Rck1 is the capacity of must run by which ck1 should ck1 be adjusted
Rck1(c,windtype,i,p,m)$(windexist(c,windtype,i) and (lk1(p,m) + Rwk1(c,windtype,i,p,m)) > 0) = ck1(p,m) * (lk1(p,m) / (lk1(p,m) + Rwk1(c,windtype,i,p,m)) - 1) ;
Rck2(c,windtype,i,p,m) = 0 ;
Rck2(c,windtype,i,p,m)$(ck1(p,m) and windexist(c,windtype,i)) = ck2(p,m) * (((ck1(p,m) + Rck1(c,windtype,i,p,m)) / ck1(p,m))**2 - 1) ;

parameter wk1_region(c,windtype,i,region,m);
wk1_region(c,windtype,i,region,m)$(windexist(c,windtype,i)) = sum(p$nregion(p,region), rwk1(c,windtype,i,p,m)) ;


* Adjust zk1 and zk2 due to additional incremental wind capacity at i by class c
Rzk1_region(c,windtype,i,region,m) = zk1_region(region,m) + sum(p$nregion(p,region), Rck1(c,windtype,i,p,m) + Rwk1(c,windtype,i,p,m)) ;
Rzk2_region(c,windtype,i,region,m) = zk2_region(region,m) + sum(p$nregion(p,region), Rck2(c,windtype,i,p,m)) + Rwk2_region(c,windtype,i,region,m) ;


WSurplus(c,windtype,i,region,m) = 0;
WSurplus(c,windtype,i,region,m)$(Rzk2_region(c,windtype,i,region,m)>0 and sum(p$nregion(p,region), Rwk1(c,windtype,i,p,m)) > 0 and windexist(c,windtype,i)) =
         Rzk1_region(c,windtype,i,region,m)*errorf(Rzk1_region(c,windtype,i,region,m)/sqrt(Rzk2_region(c,windtype,i,region,m)))
         + sqrt(Rzk2_region(c,windtype,i,region,m)/2/3.1416) * exp(-(Rzk1_region(c,windtype,i,region,m)*Rzk1_region(c,windtype,i,region,m))/2/Rzk2_region(c,windtype,i,region,m)) ;
WSurplusmarp(c,windtype,i,p,m)$(windexist(c,windtype,i) and Powfrac_downi(i,p,m) and (CF(c,windtype)*CF_corr(i,c,windtype,m))) = Rwk1(c,windtype,i,p,m) *
         sum(region$nregion(p,region), (WSurplus(c,windtype,i,region,m) - Surplus(region,m)) / sum(pp$nregion(pp,region), Rwk1(c,windtype,i,pp,m)))  / (wincrement*CF(c,windtype)*CF_corr(i,c,windtype,m)) ;

WSurplusmar(c,windtype,i,m)$(windexist(c,windtype,i) and (CF(c,windtype)*CF_corr(i,c,windtype,m))) = sum(region$WSurplus(c,windtype,i,region,m), WSurplus(c,windtype,i,region,m) - Surplus(region,m)) / (wincrement*CF(c,windtype)*CF_corr(i,c,windtype,m)) ;


Wsurplusmar(c,windtype,i,m)$(windexist(c,windtype,i)) = min(1, Wsurplusmar(c,windtype,i,m)) ;
Wsurplusmar(c,windtype,i,m)$(Wsurplusmar(c,windtype,i,m)<.003) = 0 ;


*----surplus with incremental UPV----*
Pck1(n,p,m,pvclass)$((lk1(p,m) + Rupvk1(n,p,m,pvclass)) > 0) = ck1(p,m) * ((lk1(p,m) / (lk1(p,m) + Rupvk1(n,p,m,pvclass))) - 1) ;
Pck2(n,p,m,pvclass) = 0 ;
Pck2(n,p,m,pvclass)$ck1(p,m) = ck2(p,m) *(((Pck1(n,p,m,pvclass)+ ck1(p,m)) / ck1(p,m))**2 - 1) ;


Pzk1_region(n,region,m,pvclass) = zk1_region(region,m) + sum(p$nregion(p,region), Pck1(n,p,m,pvclass) + Rupvk1(n,p,m,pvclass))  ;
Pzk2_region(n,region,m,pvclass) = zk2_region(region,m) + sum(p$nregion(p,region), Pck2(n,p,m,pvclass)) + Rupvk2_region(n,region,m,pvclass) ;

UPVSurplus(n,region,m,pvclass) = 0;
UPVSurplus(n,region,m,pvclass)$(Pzk2_region(n,region,m,pvclass)>0 and sum(p$nregion(p,region), Rupvk1(n,p,m,pvclass))>0) =
         Pzk1_region(n,region,m,pvclass)*errorf(pzk1_region(n,region,m,pvclass)/sqrt(pzk2_region(n,region,m,pvclass)))
         + sqrt(pzk2_region(n,region,m,pvclass)/2/3.1416) * exp(-(pzk1_region(n,region,m,pvclass)*pzk1_region(n,region,m,pvclass))/2/pzk2_region(n,region,m,pvclass)) ;


UPVSurplusmar(n,m,pvclass)$CFUPV(n,m,pvclass) = sum(p$Powfrac_downstream(n,p,m), Rupvk1(n,p,m,pvclass) *
         sum(region$nregion(p,region), max(0,UPVSurplus(n,region,m,pvclass) - Surplus(region,m)) / sum(pp$nregion(pp,region), Rupvk1(n,pp,m,pvclass)))) / (wincrement*CFUPV(n,m,pvclass)) ;

UPVSurplusmar(n,m,pvclass) = max(0, UPVSurplusmar(n,m,pvclass)) ;
UPVSurplusmar(n,m,pvclass) = min(1, UPVSurplusmar(n,m,pvclass)) ;
UPVSurplusMar(n,m,pvclass)$(UPVSurplusMar(n,m,pvclass)<.001) = 0 ;

*----surplus with incremental DUPV----*
Dck1(n,p,m,pvclass)$((lk1(p,m) + Rdupvk1(n,p,m,pvclass)) >0) = ck1(p,m) * (lk1(p,m) / (lk1(p,m) + Rdupvk1(n,p,m,pvclass)) - 1) ;
Dck2(n,p,m,pvclass) = 0 ;
Dck2(n,p,m,pvclass)$ck1(p,m) = ck2(p,m) * (((Dck1(n,p,m,pvclass) + ck1(p,m)) / ck1(p,m))**2 - 1) ;

Dzk1_region(n,region,m,pvclass) = zk1_region(region,m) + sum(p$nregion(p,region), Dck1(n,p,m,pvclass) + Rdupvk1(n,p,m,pvclass)) ;
Dzk2_region(n,region,m,pvclass) = zk2_region(region,m) + sum(p$nregion(p,region), Dck2(n,p,m,pvclass) + Rdupvk2_region(n,region,m,pvclass)) ;

DUPVSurplus(n,region,m,pvclass) = 0;
DUPVSurplus(n,region,m,pvclass)$(Dzk2_region(n,region,m,pvclass)>0 and sum(p$nregion(p,region), Rdupvk1(n,p,m,pvclass))>0) =
         Dzk1_region(n,region,m,pvclass)*errorf(Dzk1_region(n,region,m,pvclass)/sqrt(Dzk2_region(n,region,m,pvclass)))
         + sqrt(Dzk2_region(n,region,m,pvclass)/2/3.1416) * exp(-(Dzk1_region(n,region,m,pvclass)*Dzk1_region(n,region,m,pvclass))/2/Dzk2_region(n,region,m,pvclass)) ;

DUPVSurplusmar(n,m,pvclass)$CFDUPV(n,m,pvclass) = sum(p$DUPVpowfrac_downstream(n,p,m), Rdupvk1(n,p,m,pvclass) *
         sum(region$nregion(p,region), max(0,DUPVSurplus(n,region,m,pvclass) - Surplus(region,m)) / sum(pp$nregion(pp,region), Rdupvk1(n,pp,m,pvclass)))) / (wincrement*CFDUPV(n,m,pvclass)) ;

DUPVSurplusmar(n,m,pvclass) = max(0, DUPVSurplusmar(n,m,pvclass)) ;
DUPVSurplusmar(n,m,pvclass) = min(1, DUPVSurplusmar(n,m,pvclass)) ;
DUPVSurplusMar(n,m,pvclass)$(DUPVSurplusMar(n,m,pvclass)<.001) = 0 ;

*----surplus with incremental storage----*
Rsk1(p,m) = sum(s$seaperiods(m,s), sk1_efficacy(p,s)*2*wincrement) ;   // assume 200 MW of incremental build


* zk1_region(p,m) can be thought of as zk1_region(p,region,m), as in: expectation of capacity at
*   region for incremental addition of storage at p.
*   sum(region$nregion(p,region) assigns zk1_region to p.
Szk1_region(p,m) = sum(region$nregion(p,region), zk1_region(region,m)) ;
Szk2_region(p,m) = sum(region$nregion(p,region), zk2_region(region,m)) ;

* Surplus in region when incremental storage is added at p.
* (at p, but represents surplus across entire region containing p)
StSurplus_region(p,m)$(Szk2_region(p,m)>0) = Szk1_region(p,m)*errorf(Szk1_region(p,m)/sqrt(Szk2_region(p,m)))
                 + sqrt(Szk2_region(p,m)/2/3.1416) * exp(-(Szk1_region(p,m)*Szk1_region(p,m))/2/Szk2_region(p,m)) ;

* StSurpRecMar(n,m) is a positive coefficient representing recovered curtailments
StSurpRecMar(p,m) =  -(StSurplus_region(p,m) - sum(region$nregion(p,region), Surplus(region,m))) / (2*wincrement) ;
StSurpRecMar(p,m) = max(0, StSurpRecMar(p,m)) ;
StSurpRecMar(p,m) = min(1, StSurpRecMar(p,m)) ;
StSurpRecMar(p,m)$(StSurpRecMar(p,m)<.01) = 0 ;

StSurpRecMar_np(n,p,m) = StSurpRecMar(p,m) * Powfrac_upstream(n,p,m) ;
StSurpRecMar_np(n,p,m) = max(0, StSurpRecMar_np(n,p,m)) ;
StSurpRecMar_np(n,p,m) = min(1, StSurpRecMar_np(n,p,m)) ;
StSurpRecMar_np(n,p,m)$(StSurpRecMar_np(n,p,m)<.005) = 0 ;


*----surplus with incremental must-run----*
* In this case, the increment is not nameplate capacity but instead MW at minimum turndown.
*    That quantity is defined in the model by minplantload(q).
MRck1(p) = 2*wincrement ;   // assume 200 MW of incremental must-run (output not necessarily capacity)
MRck2(p,m) = 0 ;
MRck2(p,m)$(ck1(p,m)>0 and ((MRck1(p)+ck1(p,m))/ck1(p,m))>0) = ck2(p,m) * (((MRck1(p)+ck1(p,m))/ck1(p,m))**2-1) ;

MRzk1_region(p,m) = sum(region$nregion(p,region), zk1_region(region,m)) + MRck1(p) ;
MRzk2_region(p,m) = sum(region$nregion(p,region), zk2_region(region,m)) + MRck2(p,m) ;

MRSurplus_region(p,m) = 0 ;
MRSurplus_region(p,m)$(MRzk2_region(p,m)>0) = MRzk1_region(p,m)*errorf(MRzk1_region(p,m)/sqrt(MRzk2_region(p,m)))
                 + sqrt(MRzk2_region(p,m)/2/3.1416) * exp(-(MRzk1_region(p,m)*MRzk1_region(p,m))/2/MRzk2_region(p,m));

MRSurplusMar(p,m) = (MRSurplus_region(p,m) - sum(region$nregion(p,region), Surplus(region,m))) / MRck1(p) ;
MRSurplusMar(p,m) = max(0, MRSurplusMar(p,m)) ;
MRSurplusMar(p,m) = min(1, MRSurplusMar(p,m)) ;
MRSurplusMar(p,m)$(MRSurplusMar(p,m)<.01) = 0 ;

MRSurplusMar_np(n,p,m) = MRSurplusMar(p,m) * Powfrac_upstream(p,n,m) ;
MRSurplusMar_np(n,p,m) = max(0, MRSurplusMar_np(n,p,m)) ;
MRSurplusMar_np(n,p,m) = min(1, MRSurplusMar_np(n,p,m)) ;
MRSurplusMar_np(n,p,m)$(MRSurplusMar_np(n,p,m)<.005) = 0 ;

$endif

*---------------- End Surplus Calculations ----------------------------*


* Summarize results to annual level
UPVSurplusMar_annual(n)$(sum((m,pvclass), CFUPV(n,m,pvclass) * Hm(m)) > 0) =  sum((m,pvclass), Hm(m) * UPVSurplusmar(n,m,pvclass) * CFUPV(n,m,pvclass)) / sum((m,pvclass), Hm(m) * CFUPV(n,m,pvclass)) ;
DUPVSurplusMar_annual(n)$(sum((m,pvclass), CFDUPV(n,m,pvclass) * Hm(m)) > 0) =  sum((m,pvclass), Hm(m) * DUPVSurplusmar(n,m,pvclass) * CFDUPV(n,m,pvclass)) / sum((m,pvclass), Hm(m) * CFDUPV(n,m,pvclass)) ;
WSurplusmar_annual(windtype,i)$(sum((c,m), CF(c,windtype) * CF_corr(i,c,windtype,m) * Hm(m)) > 0) =
         sum((c,m), Hm(m) * WSurplusmar(c,windtype,i,m) * CF(c,windtype) * CF_corr(i,c,windtype,m)) / sum((c,m), Hm(m) * CF(c,windtype) * CF_corr(i,c,windtype,m)) ;


Execute_Unload "E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%rawvariability_%case%_%begy%.gdx",

         SurpOld, WSurplusmar, UPVSurplusMar, DUPVSurplusMar,
         UPVSurplusMar_annual, DUPVSurplusMar_annual, WSurplusmar_annual, MRSurplusMar,
         WSurplus, UPVSurplus, DUPVSurplus
;