$ontext
To run this file independently, type the u1, u2, u3, and u4 values into the  text bar at the top (separated by space) and then press the red run button
e.g., u1=2010 u2=ON u3=LDC_static_inputs_06_27_2019 --case=test_ref_seq
u1 is the current year
u2 is REflowSwitch

Patrick Sullivan May 26, 2011
This file reads in some ReEDS outputs (in particular, wind, load, flows) and calculates:
         1. How power is transmitted around the network. That is, how is the energy dispersed.
            I make an assumption of proportionality: that all inflows mix and are distributed evenly among outflows.
         2. The capacity credit of VRRE installations at each node. This is based on the capacity credit at the various
            destinations of that wind but is brought back to the source.
         3. The marginal capacity credit of a new 100 MW VRRE generator at each (v,i) or (n), again, based on how that energy will be
            dispersed across the network.
         4. Curtailments for the existing system: all VRRE, storage and must-run considered
         5. Marginal curtailment for a new 100 MW VRRE plant at each (v,i) or (n).
         6. Marginal curtailment induced by new must-run capacity.
         7. Marginal curtailment reduction associated with new storage capacity.

Inputs to this algorithm are the sets, parameters, and variables shipped over from ReEDS in the
REflow.gdx file. There are additional input files for the VRRE correlation data; those parameters
never enter ReEDS, so are loaded here separately from their respective excel files.

This algorithm sends the computed variability parameters back to ReEDS via variability.gdx.
That unload statement is at the very bottom of this file.
$offtext

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
$eolcom //

$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix


Option PROFILE = 2
* THIS STATEMENT LIMITS PROFILE output to items taking more than 2 seconds
Option PROFILETOL = 2

$setglobal next_year %gams.user1%
$setglobal projectfolder '%gams.curdir%'
$setglobal outputfolder '%projectfolder%/outputs/variabilityFiles'
$setglobal REflowSwitch %gams.user2%

$gdxin "outputs%ds%variabilityFiles%ds%REflow_%case%_%next_year%.gdx"
* load sets and parameters from .gdx file
* 06-13-13 SMC Added mhkwaveclass
* 12-04-14 BAF add pvclass, nwithupv, nwithdupv
*06-19-2018 PNJ Seasonal RES MARG: added nfull, seaperiodsNoH17
*12-16-2018 AWF removed nfull
Sets v, cCSP, pvclass, mhkwaveclass, i, n, rto, nrto, m, s, q, distPVtech, ct, st, notsummer, seaperiods(s,m), seaperiodsNoH17(s,m), pcaj,
         iwithcsp, thermal_st(st), windtype, iwithwindtype, nwithupv, nwithdupv, allyears ;
$loaddc v, cCSP, pvclass, mhkwaveclass, i, n, rto, nrto, m, s, q, distPVtech, ct, st, notsummer, seaperiods, iwithcsp, thermal_st, windtype, iwithwindtype, nwithupv, nwithdupv, allyears
alias(n,p,nn,pp) ;
alias(i,j,ii) ;
alias(windtype,windtype2) ;
alias(v,v2,v3,v4) ;
alias(cCSP,cCSP2,cCSP3,cCSP4) ;

$load pcaj

Scalar distlossfactor
;

Parameter Hm(m),
         class(v,windtype,i),
         classcsp(cCSP,i),
         classupv(pvclass,n),
         classdupv(pvclass,n),
         load(n,m),
         gen(m,n),
         flow(n,p,m), DC_flow(n,p,m)
         net_injection(n,m)
         transloss(n,m)
;
$load Hm, class, classcsp, classupv, classdupv, load = Lmn, gen = gen_reflow, flow = lineflow, DC_flow = DC_lineflow
$load net_injection = net_inj, transloss, distlossfactor

Parameter WGenOld(n,m),
         CSPGenOld(n,m),
*10-09-15 BAF add CSP with storage parameter for completeness in zk terms (but not included in CSP variability metrics)
         CSPstGenOld(n,m),
         CSPwStor_nomsize,
         CSPwStor_minload,
         UPVGenOld(n,m),
         DUPVGenOld(n,m),
         distPVGenOld(n,m),
* 11-05-12 SMC Added paramters for MHK wave
         MHKwaveGenOld(n,m),

         DXi(i) horizontal distance X for region i,
         DYi(i) vertical distance Y for region i
;
$load WGenOld, CSPGenOld, CSPstGenOld, CSPwStor_nomsize, CSPwStor_minload, UPVGenOld, DUPVGenOld, distPVGenOld, MHKwaveGenOld, DXi, DYi

Variables STORout(m,n,st), STORin(m,n,st) ;
$load STORout, STORin

$gdxin
;

*02-13-15 BAF add DUPV- and distPV-specific versions of powfrac_downstream with conditional shipping.
Parameter DUPVpowfrac_downstream(n,p,m) powfrac_downstream adjusted for distribution line losses and DUPV excess generation requirement,
         distPVpowfrac_downstream(n,p,m) powfrac_downstream adjusted for distribution line losses and distPV excess generation requirement,
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
         CSPnp(n,p,m) 'MW of CSP-without storage from n to p in m',
         CSPp(p,m) 'MW of CSP-without storage into p in m',
         CSPstnp(n,p,m) 'MW of CSP-ws from n to p in m',
         CSPstp(p,m) 'MW of CSP-ws into p in m',
         UPVnp(n,p,m) 'MW of UPV from n to p in m',
         UPVp(p,m) 'MW of UPV into p in m',
*02-03-15 BAF add DUPV and distPV to allow for inter-region shipping
         DUPVnp(n,p,m) 'MW of DUPV from n to p in m',
         DUPVp(p,m) 'MW of DUPV into p in m',
         distPVnp(n,p,m) 'MW of distPV from n to p in m',
         distPVp(p,m) 'MW of distPV into p in m',
* 11-05-12 SMC Added paramters for MHK wave
         MHKWnp(n,p,m) 'MW of MHK wave from n to p in m',
         MHKWp(p,m) 'MW of MHK wave into p in m',
         REnp(n,p,m) 'MW of all VRRE from n to p in m',
         REp(p,m) 'MW of all VRRE into p in m',
         Windfrac_upstream(p,n,m) 'Fraction of wind at p that came from n',
         CSPfrac_upstream(p,n,m) 'Fraction of CSP at p that came from n',
         UPVfrac_upstream(p,n,m) 'Fraction of UPV at p that came from n',
         DUPVfrac_upstream(p,n,m) 'Fraction of DUPV at p that came from n',
         distPVfrac_upstream(p,n,m) 'Fraction of distPV at p that came from n',
         MHKWfrac_upstream(p,n,m) 'Fraction of MHK wave at p that came from n',
         REfrac_upstream(p,n,m) 'Fraction of all VRRE at p that came from n',
         PVGenOld(n,m) generation from PV units (all 3 types) at source
;

totload(n,m) = load(n,m) + sum(st, STORin.l(m,n,st)) + transloss(n,m) ;
totgen(n,m) = totload(n,m) + net_injection(n,m) + sum(p, DC_flow(n,p,m) - DC_flow(p,n,m)) ;
totgen(n,m) = max(0, totgen(n,m)) ;

Parameter inflow(n,m), outflow(n,m) ;
inflow(p,m) = sum(n, flow(n,p,m)) + sum(n, DC_flow(n,p,m)) ;
outflow(n,m) = sum(p, flow(n,p,m)) + sum(p, DC_flow(n,p,m)) ;

through(n,m) = totload(n,m) + outflow(n,m) ;

A_upstream(p,n,m) = 0 ;
A_upstream(n,n,m) = 1 ;
A_upstream(p,n,m)$(flow(n,p,m)+DC_flow(n,p,m)>0 and through(n,m)>0) = -(flow(n,p,m) + DC_flow(n,p,m))/through(n,m) ;
A_downstream(n,p,m) = 0 ;
A_downstream(n,n,m) = 1 ;
A_downstream(n,p,m)$(flow(n,p,m)+ DC_flow(n,p,m)>0 and through(p,m)>0) = -(flow(n,p,m) + DC_flow(n,p,m))/through(p,m) ;

Loop(m,
a(p,n) = A_upstream(p,n,m) ;
execute_unload 'outputs/variabilityFiles/gdxforinverse_%case%_%next_year%.gdx' p,a ;
execute 'invert ./outputs/variabilityFiles/gdxforinverse_%case%_%next_year%.gdx p a ./outputs/variabilityFiles/gdxfrominverse_%case%_%next_year%.gdx ainv >> ./outputs/variabilityFiles/invert1_%case%_%next_year%.log' ;
execute_load './outputs/variabilityFiles/gdxfrominverse_%case%_%next_year%.gdx' , ainv ;
Ainv_upstream(p,n,m) = ainv(p,n) ;
) ;
Loop(m,
a(n,p) = A_downstream(n,p,m) ;
execute_unload './outputs/variabilityFiles/gdxforinverse_%case%_%next_year%.gdx' p,a ;
execute 'invert ./outputs/variabilityFiles/gdxforinverse_%case%_%next_year%.gdx p a ./outputs/variabilityFiles/gdxfrominverse_%case%_%next_year%.gdx ainv >> ./outputs/variabilityFiles/invert2_%case%_%next_year%.log' ;
execute_load './outputs/variabilityFiles/gdxfrominverse_%case%_%next_year%.gdx' , ainv ;
Ainv_downstream(n,p,m) = ainv(n,p) ;
) ;

* Remove gdx files that were created to do the inverse calculation
execute 'rm ./outputs/variabilityFiles/gdxforinverse_%case%_%next_year%.gdx' ;
execute 'rm ./outputs/variabilityFiles/gdxfrominverse_%case%_%next_year%.gdx' ;
execute 'rm ./outputs/variabilityFiles/invert1_%case%_%next_year%.log' ;
execute 'rm ./outputs/variabilityFiles/invert2_%case%_%next_year%.log' ;

Powfrac_upstream(p,n,m)$(through(p,m)>0) = (1/through(p,m)) * Ainv_upstream(p,n,m)*totgen(n,m) ;
Powfrac_upstream(p,n,m)$(Powfrac_upstream(p,n,m)<1e-3) = 0 ;
Powfrac_downstream(n,p,m)$(through(n,m)>0) = (1/through(n,m)) * Ainv_downstream(n,p,m)*totload(p,m) ;
Powfrac_downstream(n,p,m)$(Powfrac_downstream(n,p,m)<1e-3) = 0 ;
Powfrac_downi(i,p,m) = sum(n$pcaj(n,i), Powfrac_downstream(n,p,m)) ;
Powfrac_np(n,p) = sum(m, Powfrac_downstream(n,p,m) * Hm(m)) / 8760 ;
Powfrac_ip(i,p) = sum(n$pcaj(n,i), Powfrac_np(n,p)) ;

Windnp(n,p,m) = WGenOld(n,m)*Powfrac_downstream(n,p,m) ;
Windp(p,m) = sum(n, Windnp(n,p,m)) ;
CSPnp(n,p,m) = CSPGenOld(n,m)*Powfrac_downstream(n,p,m) ;
CSPp(p,m) = sum(n, CSPnp(n,p,m)) ;
CSPstnp(n,p,m) = CSPstGenOld(n,m)*Powfrac_downstream(n,p,m) ;
CSPstp(p,m) = sum(n, CSPstnp(n,p,m)) ;
UPVnp(n,p,m) = UPVGenOld(n,m)*Powfrac_downstream(n,p,m) ;
UPVp(p,m) = sum(n, UPVnp(n,p,m)) ;

*02-13-15 WJC and BAF apply conditional shipping to distribution-level PV so that only ships if gen > load.
*Initialize downstream shipment to 0, apply weighted portion of fractional excess generation each for DUPV and distPV
*to Powfrac_downstream. Then, set shipment to remaining non-adjusted Powfrac_downstream value for n=n. Finally, adjust
*only the shipped fractions (n not equal to p) for distribution line losses squared (remove distlossfactor that was
*credited to distribution PV to determine actual generation, then remove again to account for transfer to transmission lines).
DUPVpowfrac_downstream(n,p,m) = 0 ;
gen_load_ratio(n,m)$(gen(m,n)>load(n,m) and load(n,m)>0) = gen(m,n)/load(n,m) ;
gen_load_ratio(n,m)$(gen_load_ratio(n,m)>2) = 2 ;  // If generation is greater than 200% of the load, set the ratio to 2.  This prevents the next line from increasing Powfrac_downstream when it multiplies by (gen_load_ratio - 1)
DUPVpowfrac_downstream(n,p,m)$(gen(m,n)>load(n,m) and load(n,m)>0) = Powfrac_downstream(n,p,m)*(gen_load_ratio(n,m) - 1) ;
DUPVpowfrac_downstream(n,n,m) = 0 ;
DUPVpowfrac_downstream(n,n,m) = 1 - sum(p, DUPVpowfrac_downstream(n,p,m)) ;
DUPVpowfrac_downstream(n,p,m) = DUPVpowfrac_downstream(n,p,m)/(distlossfactor**2) ;
DUPVpowfrac_downstream(n,n,m) = DUPVpowfrac_downstream(n,n,m)*(distlossfactor**2) ;  //apply credit back to self-consuming regions

*Current treatment is the same for DUPV and distPV
distPVpowfrac_downstream(n,p,m) = DUPVpowfrac_downstream(n,p,m) ;



*Use DUPV and distPV specific fractional shippments above
DUPVnp(n,p,m) = DUPVGenOld(n,m)*DUPVpowfrac_downstream(n,p,m) ;
DUPVp(p,m) = sum(n, DUPVnp(n,p,m)) ;
distPVnp(n,p,m) = distPVGenOld(n,m)*distPVpowfrac_downstream(n,p,m) ;
distPVp(p,m) = sum(n, distPVnp(n,p,m)) ;

* 11-05-12 SMC Added calculations for MHK wave
MHKWnp(n,p,m) = MHKwaveGenOld(n,m)*Powfrac_downstream(n,p,m) ;
MHKWp(p,m) = sum(n, MHKWnp(n,p,m)) ;
REnp(n,p,m) = Windnp(n,p,m) + CSPnp(n,p,m) + UPVnp(n,p,m) + DUPVnp(n,p,m) + distPVnp(n,p,m) + MHKWnp(n,p,m) ;

REp(p,m) = sum(n, REnp(n,p,m)) ;
PVGenOld(n,m) = UPVGenOld(n,m) + DUPVGenOld(n,m) + distPVGenOld(n,m) ;

Windfrac_upstream(p,n,m) = 0 ;
Windfrac_upstream(n,n,m) = 1 ;
Windfrac_upstream(p,n,m)$Windp(p,m) = Windnp(n,p,m) / Windp(p,m) ;
Windfrac_upstream(p,n,m)$(Windfrac_upstream(p,n,m)<0.001) = 0 ;
CSPfrac_upstream(p,n,m) = 0 ;
CSPfrac_upstream(n,n,m) = 1 ;
CSPfrac_upstream(p,n,m)$CSPp(p,m) = CSPnp(n,p,m) / CSPp(p,m) ;
CSPfrac_upstream(p,n,m)$(CSPfrac_upstream(p,n,m)<0.001) = 0 ;
UPVfrac_upstream(p,n,m) = 0 ;
UPVfrac_upstream(n,n,m) = 1 ;
UPVfrac_upstream(p,n,m)$UPVp(p,m) = UPVnp(n,p,m) / UPVp(p,m) ;
UPVfrac_upstream(p,n,m)$(UPVfrac_upstream(p,n,m)<0.001) = 0 ;
DUPVfrac_upstream(p,n,m) = 0 ;
DUPVfrac_upstream(n,n,m) = 1 ;
DUPVfrac_upstream(p,n,m)$DUPVp(p,m) = DUPVnp(n,p,m) / DUPVp(p,m) ;
DUPVfrac_upstream(p,n,m)$(DUPVfrac_upstream(p,n,m)<0.001) = 0 ;
distPVfrac_upstream(p,n,m) = 0 ;
distPVfrac_upstream(n,n,m) = 1 ;
distPVfrac_upstream(p,n,m)$distPVp(p,m) = distPVnp(n,p,m) / distPVp(p,m) ;
distPVfrac_upstream(p,n,m)$(distPVfrac_upstream(p,n,m)<0.001) = 0 ;
* 11-05-12 SMC Added calculations for MHK wave
MHKWfrac_upstream(p,n,m) = 0 ;
MHKWfrac_upstream(n,n,m) = 1 ;
MHKWfrac_upstream(p,n,m)$MHKWp(p,m) = MHKWnp(n,p,m) / MHKWp(p,m) ;
MHKWfrac_upstream(p,n,m)$(MHKWfrac_upstream(p,n,m)<0.001) = 0 ;
REfrac_upstream(p,n,m) = 0 ;
REfrac_upstream(n,n,m) = 1 ;
REfrac_upstream(p,n,m)$REp(p,m) = REnp(n,p,m) / REp(p,m) ;
REfrac_upstream(p,n,m)$(REfrac_upstream(p,n,m)<0.001) = 0 ;

*---------------- Import and Compute Correlation Coeffs --------------------*

Parameters w_w_correlation(i,v,ii,v2),
         xycorrelation(i,ii)
         csp_csp_correlation(i,cCSP,j,cCSP2,m) correlation coefficient between csp of region i and class cCSP and csp of region j and class cCSP2
         w_csp_correlation(i,v,j,cCSP2) correlation coefficient of wind from region i and class cCSP with csp from region j and class cCSP2
         upv_upv_correlation(i,j,m) correlation coefficient between upv of region i and upv of region j (assume same for DUPV and distPV)
         upv_upv_correlnp(n,p,m) correlation coefficient between upv of region n with upv of region p (assume same for DUPV and distPV)
         WAVE_correlnp(n,p,m)            MHK wave correlation coefficient between PCAs in each time slice (0-1)
         W_WAVE_correlation(n,m)         Wind-wave energy correlation coefficient in each PCA in each time slice (0-1)
         Wsigma_ndbc(n)                  Standard deviation of wave power data by PCA
         WAVEsigma(n,m)                  Standard deviation of wave power data by PCA and time slice
;

$gdxin %gams.curdir%/inputs_case/w_w_corr.gdx
$load w_w_correlation
$gdxin

*pld 8-05 Added the x and y correlation factors to derive the exponential decrease in correlation
*Assumes the whole country performs like the midwest....
Scalar   xcorrel "east-west correlation equal to exp(dist*xcorrel) " / -0.0031 /,
         ycorrel "north-south correlation equal to exp(dist*ycorrel) " / -0.0017 /,
* these values from simonsen 04
         correlint rough approximation based on Ed Kahn 1978 report on correlation between sites in CA  / 0.75/
;

* xycorrelation is used to fill in the gaps of w_w_correlation (wind-wind correlation)
xycorrelation(i,ii) = (exp(1.609*xcorrel * abs(DXi(i)-DXi(ii))) * exp(1.609*ycorrel*ABS(DYi(i)-DYi(ii)))) ;

*MRM 4-16-09 adding the following three lines to fill in the gaps of w_w_correlation
w_w_correlation(i,v,ii,v2)$((not w_w_correlation(i,v,ii,v2)) and (ord(i)= ord(ii)) and (ord(v) = ord(v2))) = 1 ;
w_w_correlation(i,v,ii,v2)$((not w_w_correlation(i,v,ii,v2)) and (ord(i) = ord(ii))) = correlint ;
w_w_correlation(i,v,ii,v2)$(not w_w_correlation(i,v,ii,v2)) = xycorrelation(i,ii) ;


$gdxin %gams.curdir%/inputs_case/csp_csp_ts_corr.gdx
$load csp_csp_correlation
$gdxin
csp_csp_correlation(i,cCSP,j,cCSP2,'H16')= csp_csp_correlation(i,cCSP,j,cCSP2,'H14') ;
csp_csp_correlation(i,cCSP,j,cCSP2,'H17')= csp_csp_correlation(i,cCSP,j,cCSP2,'H3') ;

* 05-05-10 MRM filling in csp-csp correlations for classes with no value with other classes in the same region
csp_csp_correlation(i,cCSP,j,cCSP2,m)$(not csp_csp_correlation(i,cCSP,j,cCSP2,m) and iwithcsp(i) and iwithcsp(j) and
                                        sum((cCSP3,cCSP4),csp_csp_correlation(i,cCSP3,j,cCSP4,m))) =
   sum((cCSP3,cCSP4),csp_csp_correlation(i,cCSP3,j,cCSP4,m))/
   sum((cCSP3,cCSP4)$csp_csp_correlation(i,cCSP3,j,cCSP4,m),1) ;

$gdxin %gams.curdir%/inputs_case/w_csp_corr.gdx
$load w_csp_correlation
$gdxin
* on second thought, leave at 0 b/c we don't have any other cross-correlations represented
w_csp_correlation(i,v,j,cCSP2) = 0 ;

$gdxin %gams.curdir%/inputs_case/upv_upv_ts_corr.gdx
$load upv_upv_correlation
$gdxin
upv_upv_correlation(i,j,'H17')= UPV_UPV_correlation(i,j,'H3') ;

upv_upv_correlnp(n,p,m) = 0 ;
upv_upv_correlnp(n,p,m) =
               sum((i,j)$(pcaj(n,i) and pcaj(p,j)), upv_upv_correlation(i,j,m))/
              (sum(i$pcaj(n,i),1)*sum(j$pcaj(p,j),1)) ;
upv_upv_correlnp(n,n,m) = 1;


* 11-05-12 SMC Added parameters for MHK wave variability calculations
* 02-14-13 SMC Added switch for use with MHK OFF
$gdxin %gams.curdir%/inputs_case/mhkwave_var_params.gdx
$load WAVE_correlnp, W_WAVE_correlation, Wsigma_ndbc, WAVEsigma
$gdxin


*------------------ Capacity Credit Calculations -----------------------*

Parameter wvarianceold(v,windtype,i,m) the variance associated with old wind capacity (i.e. all capacity up to now),
         wvariance(v,windtype,i,m) wind variance from above corrected by the ratio of the variance for the user and the variance calculated by the regression for the above,
         wsigmaold(v,windtype,i,m) standard deviation of the existing wind generation distribution,
         wsigma(v,windtype,i,m) standard deviation of the wind generation distribution,
         Wexpected(v,windtype,i,m) expected value of the wind distribution = capacity factor
         WindCap(n) wind capacity at n,
         TWcip(v,windtype,i,p) 'wind capacity of (v,i) that "ends up" at p',
         TWcipm(v,windtype,i,p,m) 'wind capacity of (v,i) that "ends up" at p at time m',
         TW(p,m) 'wind capacity that "ends up" at p',
         TW2(p,m) 'independent variances for wind serving p',
         TWcrossprod_cip(v,windtype,i,p,m) "the sum of covariances between installed wind in v,i and all other installed wind contributing to p",
         TWcrossprod(p,m) 'sum of covariances of wind serving p',
         CSPCap(n) CSP (no storage) capacity at n (MW),
         PVCap(n) UPV + DUPV +distPV degraded capacity at n (MW),
         distPVO(n) existing distPV degraded capacity at n (MW),
         TCSPcipm(cCSP,i,p,m) 'CSP capacity of (cCSP,i) that "ends up" at p',
         TCSP(p,m) 'CSP capacity that "ends up" at p',
         TCSP2(p,m) 'independent variances for CSP serving p',
         TCSPcrossprod_cip(cCSP,i,p,m) "the sum of covariances between installed CSP in v,i and all other installed CSP contributing to p",
         TCSPcrossprod(p,m) 'sum of covariances of CSP serving p',
*02-03-15 BAF add DUPV and distPV terms for inter-regional shipping
         UPVOp(n,p,m,pvclass) existing degraded UPV capacity that is shipped from n to p (analog of TWcip except TWcip is sum of all wind technologies) (MW),
         DUPVOp(n,p,m,pvclass) existing degraded DUPV capacity that is shipped from n to p (MW),
         distPVOp(n,p,m) existing degraded distPV capacity that is shipped from n to p (MW),
         TPVnpm(n,p,m) total existing degraded PV capacity (UPV+DUPV+distPV) that is shipped from n to p (MW),
         TPV(p,m) total existing degraded PV capacity (UPV+DUPV+distPV) that ends up at p (MW),
         UPVcrossprod_np(n,p,m,pvclass) sum of covariances between installed UPV in n by pvclass and all other installed PV contributing to p,
         DUPVcrossprod_np(n,p,m,pvclass) sum of covariances between installed DUPV in n by pvclass and all other installed PV contributing to p,
         distPVcrossprod_np(n,p,m) sum of covariances between installed distPV in n and all other installed PV contributing to p,
         UPVcrossprod(p,m,pvclass) sum of covariances of UPV serving p,
         DUPVcrossprod(p,m,pvclass) sum of covariances of DUPV serving p,
         distPVcrossprod(p,m) sum of covariances of distPV serving p,
         UPV2(p,m) independent variances for UPV serving p,
         DUPV2(p,m) independent variances for DUPV serving p,
         distPV2(p,m) independent variances for distPV serving p,
* 11-05-12 SMC Added MHK wave parameters
         MHKWcap(n) 'MHK wave capacity at n (MW)',
         TMHKWnpm(n,p,m) 'MHK wave capacity of n that "ends up" at p',
         TMHKWnrtom(n,rto,m) 'MHK wave capacity of n that "ends up" at rto',
         TMHKW(p,m) 'MHK wave capacity that "ends up" at p',
         TMHKWcrossprod_np(n,p,m) 'sum of covariances between installed MHK wave in n and all other MHK wave installations contributing to p',
         TMHKWcrossprod(p,m) 'sum of covariances of MHK wave serving p',
         TMHKW2(p,m) 'independent variances for MHK wave serving p',
         wk1(p,m) E(Wind) (MW),
         wk2(p,m) var(W) (MW^2),
         cspk1(p,m) E(CSP) (MW),
         cspk2(p,m) var(CSP) (MW^2),
*10-09-15 BAF add CSP with storage term
         cspstk1(p,m) E(CSP) (MW),
         cspstk2(p,m) var(CSP) (MW^2),
         pvk1(p,m) E(UPV+DUPV+distPV) (MW),
         upvk1(p,m) E(UPV) (MW),
         dupvk1(p,m) E(DPV) (MW),
         distpvk1(p,m) E(distPV) (MW),
         pvk2(p,m) var(UPV+DUPV+distPV) (MW^2),
         upvk2(p,m) var(UPV) (MW^2),
         dupvk2(p,m) var(DUPV) (MW^2),
         distpvk2(p,m) var(distPV) (MW^2),
* 11-05-12 SMC Added MHK wave parameters
         mhkwk1(p,m) E(MHK wave) (MW),
         mhkwk2(p,m) var(MHK wave) (MW^2),
         mhkwk2_rto(rto,m) var(MHK wave) at RTO (MW^2),
         lk1(n,m) E(Load) (MW),
         lk2(n,m) var(L) (MW^2),
         ck1(n,m) E(V) (MW),
         ck2(n,m) var(V) (MW^2),
         sk1(n,m) E(Storage) (MW),
         sk2(n,m) var(S) (MW^2),
         Rwk1(v,windtype,i,p,m) 'E(dW) from (v,i) at p in m (MW)',
         Rcspk1(cCSP,i,p,m) 'E(dCSP) from (v,i) at p in m (MW)',
         Rupvk1(n,p,m,pvclass) 'E(dUPV) from n at p in m (MW)',
         Rdupvk1(n,p,m,pvclass) 'E(dDUPV) at n in m (MW)',
         Rdistpvk1(n,p,m) 'E(ddistPV) at n in m (MW)',
         Rmhkwk1(mhkwaveclass,n,p,m) 'E(dMHKW) at n in m (MW)',
         numplants(q,n),
         plantsize(q,n),
         WCCp(p,m) CC (MW) of all wind delivered to p,
         WCCold(n,m) CC (MW) of all wind installed at n,
         WCCmar_p(v,windtype,i,p,m) CC (frac) of dW at p from all i
         WCCmar(v,windtype,i,m) CC (frac) of dW at i aggregated over all p
         CSPCCp(p,m) CC (MW) of all CSP delivered to p,
         CSPCCold(n,m) CC (MW) of all CSP installed at n,
         CSPCCmar_p(cCSP,i,p,m) CC (frac) of dCSP at p from all i
         CSPCCmar(cCSP,i,m) CC (frac) of dCSP at i aggregated over all p
         PVCCp(p,m) CC (MW) of all PV delivered to p,
         PVCCold(n,m) CC (MW) of all PV installed at n,
         UPVCCmar_p(n,p,m,pvclass) CC (frac) of UPV at p from all n by pvclass,
         DUPVCCmar_p(n,p,m,pvclass) CC (frac) of DUPV at p from all n by pvclass,
         distPVCCmar_p(n,p,m) CC (frac) of distPV at p from all n,
         UPVCCmar(n,m,pvclass) CC (frac) of UPV at n aggregated over all p by pvclass,
         DUPVCCmar(n,m,pvclass) CC (frac) of DUPV at n by pvclass,
         distPVCCmar(n,m) CC (frac) of distPV at n,
* 11-05-12 SMC Added MHK wave parameters
         MHKWCCp(p,m) CC (MW) of all MHK wave delivered to p,
         MHKWCCold(n,m) CC (MW) of all MHK wave installed at n,
         MHKWCCmar_p(n,p,m) CC (frac) of dMHKW at p from all n,
         MHKWCCmar(n,mhkwaveclass,m) CC (frac) of dMHKW at n aggregated over all p
;
Scalar wincrement dW / 1000 /  ;

alias(i,i2) ;
alias(v,v2) ;

* import ReEDS data
Parameters WO(v,windtype,i),  UPVO(n,pvclass), DUPVO(n,pvclass), STORold(n,st),
         lk2n(n,m), lk2_rto(rto,m), lk2FactorRto(rto,m), lk1_rto(rto,m), nomsize(q), FOq(q), POq(q), FOst(st), POst(st),
         CSPOct(cCSP,ct,i), CONVOLDqctn(q,ct,n),
         CF(i,v,windtype,m), CFO(v,windtype,i,m), CFcsp(cCsp,m), old_STOR(n,st),
         CSPsigma(cCSP,m) standard deviation per MW for each class and timeslice for CSP,
         CFUPV(n,m,pvclass), CFOUPV(n,m,pvclass),
         CFDUPV(n,m,pvclass), CFODUPV(n,m,pvclass),
         distPVCF(n,m),
* 11-26-14 BAF add pvclass to UPVsigma and add DUPVsigma, distPVsigma
         UPVsigma(n,m,pvclass),
         DUPVsigma(n,m,pvclass),
         distPVsigma(n,m),
         TPVsigma(n,p,m) sum of sigma capacities for all PV from n to p,
         WCCold(n,m), CSPCCold(n,m), PVCCold(n,m),
* 11-06-12 SMC Added MHK wave parameters
* 06-12-13 SMC Expanded MHK capacity factors by class.
         WAVECF(n,mhkwaveclass,m), WAVECFO(n,mhkwaveclass,m),
         MHKWCCold(n,m),
* 02/24/16 JLH Added import parameters for wind variability currently there are two options that will be removed when a choice is made. Wind Coefficient of Variability allows Wind sigmas
* to change as wind capacity factors change with time. Wind Sigmas use the direct standard deviations from the full hourly profiles.
         Wind_CoefVar(i,v,m) Coefficient of variation for each onshore wind class in each wind region i and timeslice m,
         Wind_Sigma(i,v,m) Standard deviation for each onshore wind class in each wind region i and timeslice m
;

$gdxin "outputs%ds%variabilityFiles%ds%REflow_%case%_%next_year%.gdx"
$load WO, UPVO, DUPVO, STORold, lk2n, lk2FactorRto, nomsize
$load CSPOct, CONVOLDqctn
$load FOq, POq, FOst, POst, CF, CFO, CFcsp
$load CSPsigma, UPVsigma, DUPVsigma, distPVsigma, CFDUPV, CFODUPV, CFUPV, CFOUPV, distPVCF, WCCold, CSPCCold, PVCCold, WAVECF, WAVECFO, MHKWCCold, Wind_CoefVar, Wind_Sigma
$gdxin

Set windexist(v,windtype,i) "filter on class, windtype, and i where potential wind resource exists" ;
windexist(v,windtype,i)$(iwithwindtype(i,windtype) and sum(m, CF(i,v,windtype,m))) = YES ;

Parameters WCCp_LY(p,m), CSPCCp_LY(p,m), PVCCp_LY(p,m) ;
WCCp_LY(p,m) = sum(n, WCCold(n,m) * Powfrac_downstream(n,p,m)) ;
CSPCCp_LY(p,m) = sum(n, CSPCCold(n,m) * Powfrac_downstream(n,p,m)) ;
PVCCp_LY(p,m) = 0 ;
*02-03-15 BAF change PVCCp_LY calculation to include CC of all PV (mirrors wind calculation).
*PVCCold(n,m) represents CC of all PV generation serving 'n' and is apportioned to 'p' using
*aggregate PV "powfrac_downstream" based on individual PV technology shipments,
*with conditional shipping applied to DUPV and distPV (embedded within DUPVnp and distPVnp).
PVCCp_LY(p,m) = sum(n$PVGenOld(n,m), PVCCold(n,m) * (UPVnp(n,p,m)+DUPVnp(n,p,m)+distPVnp(n,p,m))/PVGenOld(n,m)) ;

* 11-06-12 SMC LY CC calculation for MHK wave
Parameter MHKWCCp_LY(p,m) ;
MHKWCCp_LY(p,m) = sum(n, MHKWCCold(n,m) * Powfrac_downstream(n,p,m)) ;

* PTS 12/20/11 Curve fit from external variance calculations.
* Average wind speed w/ Raleigh distribution, run through representative power curve
* to produce power output probability distribution. variance computed as fn of CF.
* see windvar.xlsx for details
Wexpected(v,windtype,i,m)$(windexist(v,windtype,i)) = CF(i,v,windtype,m) ;
wvariance(v,windtype,i,m)$(windexist(v,windtype,i)) = -0.5835*Wexpected(v,windtype,i,m)**2 + 0.6621*Wexpected(v,windtype,i,m) - 0.0374 ;
*JLH 02/24/16 Option one use for onshore wind Wind Coefficient of Variation
*wvariance(v,'wind-ons',i,m)$(windexist(v,'wind-ons',i)) = max(0,Wind_CoefVar(i,v,m) *Wexpected(v,'wind-ons',i,m)) ;
*JLH 02/24/16 Option two use for onshore wind Wind Sigmas directly
*wvariance(v,'wind-ons',i,m)$(windexist(v,'wind-ons',i)) = max(0, Wind_Sigma(i,v,m)**2) ;
wvariance(v,windtype,i,m)$(windexist(v,windtype,i)) = max(0,wvariance(v,windtype,i,m)) ;
wsigma(v,windtype,i,m)$(windexist(v,windtype,i)) =  sqrt(wvariance(v,windtype,i,m)) ;

Wexpected(v,windtype,i,m)$(windexist(v,windtype,i)) = CFO(v,windtype,i,m) ;
wvarianceold(v,windtype,i,m)$(windexist(v,windtype,i)) = -0.5835*Wexpected(v,windtype,i,m)**2 + 0.6621*Wexpected(v,windtype,i,m) - 0.0374 ;
*JLH 02/24/16 Option one use for onshore wind Wind Coefficient of Variation
*wvarianceold(v,'wind-ons',i,m)$(windexist(v,'wind-ons',i)) = max(0,Wind_CoefVar(i,v,m) *Wexpected(v,'wind-ons',i,m)) ;
*JLH 02/24/16 Option two use for onshore wind Wind Sigmas directly
*wvarianceold(v,'wind-ons',i,m)$(windexist(v,'wind-ons',i)) = max(0, Wind_Sigma(i,v,m)**2) ;
*wvarianceold(v,windtype,i,m)$(windexist(v,windtype,i)) = max(0,wvariance(v,windtype,i,m)) ;
wvarianceold(v,windtype,i,m)$(windexist(v,windtype,i)) = max(0, wvarianceold(v,windtype,i,m)) ;

* 04-30-2012 PTS added correlation factor between wind sites in the same class and same region but not necesarily the same resource
Parameter num_wfarms(v,windtype,i) "number of 100MW wind farms in a v,i bundle. fractions allowed."
         wvar_old_corr(v,windtype,i,m) "wind variance reduced to account for not-fully-correlated wind farms contributing to same v,i."
Scalar wci_correlation "correlation between wind farms in same v,i bundle. manually set at unsubstantiated 0.9." ;
num_wfarms(v,windtype,i)$(windexist(v,windtype,i)) = max(1,(WO(v,windtype,i)/100)) ;
wci_correlation = 0.9 ;
wvar_old_corr(v,windtype,i,m)$(windexist(v,windtype,i)) = wvarianceold(v,windtype,i,m)/num_wfarms(v,windtype,i)
         + (num_wfarms(v,windtype,i)-1)/num_wfarms(v,windtype,i)*wci_correlation*wvarianceold(v,windtype,i,m) ;


*--------Wind--------
WindCap(n) = sum((v,windtype,i)$pcaj(n,i), WO(v,windtype,i)) ;
TWcip(v,windtype,i,p) = WO(v,windtype,i) * Powfrac_ip(i,p) ;
TWcipm(v,windtype,i,p,m) = WO(v,windtype,i) * Powfrac_downi(i,p,m) ;
TW(p,m) = sum((v,windtype,i), TWcipm(v,windtype,i,p,m)) ;
* Using 'p' rather than 'n' here to emphasize that 'k1' is related to generation at 'p'
wk1(p,m) = Windp(p,m) ;
wsigmaold(v,windtype,i,m)$(windexist(v,windtype,i)) =  sqrt(wvar_old_corr(v,windtype,i,m)) ;

* 2014--2-18 KPE Code Notes:
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



TW2(p,m) = sum((v,windtype,i)$(windexist(v,windtype,i)), wvar_old_corr(v,windtype,i,m) * TWcipm(v,windtype,i,p,m)**2 ) ;
TWcrossprod_cip(v,windtype,i,p,m)$(windexist(v,windtype,i)) = wsigmaold(v,windtype,i,m) * TWcipm(v,windtype,i,p,m)
                  * sum[(v2,ii,windtype2), wsigmaold(v2,windtype2,ii,m) * TWcipm(v2,windtype2,ii,p,m) * w_w_correlation(i,v,ii,v2)]
            - w_w_correlation(i,v,i,v)*wvar_old_corr(v,windtype,i,m)*sqr(TWcipm(v,windtype,i,p,m)) ;
TWcrossprod(p,m) = 0.5*sum((v,windtype,i)$(windexist(v,windtype,i)), TWcrossprod_cip(v,windtype,i,p,m)) ;
* Using 'p' rather than 'n' here to emphasize that 'k2' is related to generation at 'p'
wk2(p,m) = TW2(p,m)+2*TWcrossprod(p,m) ;

* PTS 8/30/13 RTOsurplus
Parameter wk2_rto(rto,m), TWcirtom(v,windtype,i,rto,m) ;
TWcirtom(v,windtype,i,rto,m)$(windexist(v,windtype,i)) = sum(p$nrto(p,rto), TWcipm(v,windtype,i,p,m)) ;

wk2_rto(rto,m) = sum((v,windtype,i)$(windexist(v,windtype,i)), wvar_old_corr(v,windtype,i,m) * TWcirtom(v,windtype,i,rto,m)**2 )
  + sum((v,windtype,i)$(windexist(v,windtype,i)), wsigmaold(v,windtype,i,m) * TWcirtom(v,windtype,i,rto,m)
                  * sum[(v2,ii,windtype2), wsigmaold(v2,windtype2,ii,m) * TWcirtom(v2,windtype2,ii,rto,m) * w_w_correlation(i,v,ii,v2)]
            - w_w_correlation(i,v,i,v)*wvar_old_corr(v,windtype,i,m) * TWcirtom(v,windtype,i,rto,m)**2 )
;


TW(p,m)$(TW(p,m)<0.001) = 0 ;
wk2(n,m)$(wk1(n,m)<0.001) = 0 ; //yes, i mean for the check to be on wk1
wk1(n,m)$(wk1(n,m)<0.001) = 0 ;


*--------Solar-------
CSPCap(n) = sum((cCSP,ct,i)$pcaj(n,i), CSPOct(cCSP,ct,i)) ;
TCSPcipm(cCSP,i,p,m) = sum(ct, CSPOct(cCSP,ct,i)) * Powfrac_downi(i,p,m) ;
* Using 'p' rather than 'n' here to emphasize that 'k1' is related to generation at 'p'
cspk1(p,m) = CSPp(p,m) ;
TCSP(p,m) = sum((cCSP,i)$(iwithcsp(i)), TCSPcipm(cCSP,i,p,m))  ;
TCSP2(p,m) = sum((cCSP,i)$(iwithcsp(i)), (abs(CSPsigma(cCSP,m) * TCSPcipm(cCSP,i,p,m)))**2) ;
TCSPcrossprod_cip(cCSP,i,p,m)$iwithcsp(i) = CSPsigma(cCSP,m) * TCSPcipm(cCSP,i,p,m)
                  * sum[(cCSP2,ii)$iwithcsp(ii), CSPsigma(cCSP2,m) * TCSPcipm(cCSP2,ii,p,m)
                                 * csp_csp_correlation(i,cCSP,ii,cCSP2,m)]
            - csp_csp_correlation(i,cCSP,i,cCSP,m)*sqr(CSPsigma(cCSP,m)*TCSPcipm(cCSP,i,p,m)) ;
TCSPcrossprod(p,m) = 0.5*sum((cCSP,i)$iwithcsp(i), TCSPcrossprod_cip(cCSP,i,p,m)) ;
* Using 'p' rather than 'n' here to emphasize that 'k3' is related to generation at 'p'
cspk2(p,m) = TCSP2(p,m)+2*TCSPcrossprod(p,m) ;

TCSP(p,m)$(TCSP(p,m)<0.001) = 0 ;
cspk2(n,m)$(cspk1(n,m)<0.001) = 0 ; //yes, i mean for the check to be on wk1
cspk1(n,m)$(cspk1(n,m)<0.001) = 0 ;

*10-09-15 BAF add CSP with storage. For cspstk2, mirror the calculation for ck2, but assume
*system size of 100MW (CSPwStor_nomsize) and manually set the FOR to 5% here (CSPwStor_fo is actually 0 but using it here would set cspstk2=0).
cspstk1(p,m) = CSPstp(p,m) ;
cspstk2(p,m) = cspstk1(p,m)/CSPwStor_nomsize * CSPwStor_nomsize**2 * 0.05 * (1 - 0.05) ;
cspstk2(n,m)$(cspstk1(n,m)<0.001) = 0 ;
cspstk1(n,m)$(cspstk1(n,m)<0.001) = 0 ;

* DJM 8/3/2013 RTOsurplus
Parameter cspk2_rto(rto,m), TCSPcirtom(cCSP,i,rto,m) ;
TCSPcirtom(cCSP,i,rto,m) = sum(p$nrto(p,rto), TCSPcipm(cCSP,i,p,m)) ;
cspk2_rto(rto,m) = sum((cCSP,i), (CSPsigma(cCSP,m) * TCSPcirtom(cCSP,i,rto,m))**2 )
  + sum((cCSP,i), cspsigma(cCSP,m) * TCSPcirtom(cCSP,i,rto,m)
                  * sum[(cCSP2,ii), cspsigma(cCSP2,m) * TCspcirtom(cCSP2,ii,rto,m) * csp_csp_correlation(i,cCSP,ii,cCSP2,m)]
            - csp_csp_correlation(i,cCSP,i,cCSP,m)*(cspsigma(cCSP,m) * Tcspcirtom(cCSP,i,rto,m))**2 )
;


*11-26-14 BAF add pvclass index and incorporate new DUPV and distPV sigma terms. All PV capacities listed here (PVcap, distPVO, UPVO, DUPVO, etc.) are existing degraded capacity.
distPVO(n) = CONVOLDqctn("distPV","none",n) ;
PVCap(n) =  sum(pvclass, UPVO(n,pvclass)$nwithupv(n,pvclass) + DUPVO(n,pvclass)$nwithdupv(n,pvclass)) + distPVO(n) ;

UPVOp(n,p,m,pvclass) = UPVO(n,pvclass)$nwithupv(n,pvclass) * Powfrac_downstream(n,p,m) ;
DUPVOp(n,p,m,pvclass) = DUPVO(n,pvclass)$nwithdupv(n,pvclass) * DUPVpowfrac_downstream(n,p,m) ;
distPVOp(n,p,m) = distPVO(n) * distPVpowfrac_downstream(n,p,m) ;
TPVnpm(n,p,m) = sum(pvclass, UPVOp(n,p,m,pvclass) + DUPVOp(n,p,m,pvclass)) + distPVOp(n,p,m) ;
TPV(p,m) = sum(n, TPVnpm(n,p,m)) ;

UPV2(p,m) = sum((n,pvclass)$nwithupv(n,pvclass), (abs(UPVsigma(n,m,pvclass) * UPVOp(n,p,m,pvclass)))**2) ;
DUPV2(p,m) = sum((n,pvclass)$nwithdupv(n,pvclass), (abs(DUPVsigma(n,m,pvclass) * DUPVOp(n,p,m,pvclass)))**2) ;
distPV2(p,m) = sum(n, (abs(distPVsigma(n,m) * distPVOp(n,p,m)))**2) ;

* 3/6/13 DJM revised terms for clarity, did not change calculation
upvk1(p,m) = UPVp(p,m) ;
dupvk1(p,m) = DUPVp(p,m) ;
distpvk1(p,m) = distPVp(p,m) ;
pvk1(p,m) = upvk1(p,m) + dupvk1(p,m) + distpvk1(p,m) ;

TPVsigma(n,p,m) = sum(pvclass$nwithupv(n,pvclass), UPVsigma(n,m,pvclass)*UPVOp(n,p,m,pvclass))
            + sum(pvclass$nwithdupv(n,pvclass), DUPVsigma(n,m,pvclass)*DUPVOp(n,p,m,pvclass))
            + distPVsigma(n,m)*distPVOp(n,p,m) ;

UPVcrossprod_np(n,p,m,pvclass)$nwithupv(n,pvclass) = UPVsigma(n,m,pvclass)*UPVOp(n,p,m,pvclass)
                  *sum[nn, TPVsigma(nn,p,m)*UPV_UPV_correlnp(n,nn,m)]
            - UPV_UPV_correlnp(n,n,m)*sqr(UPVsigma(n,m,pvclass)*UPVOp(n,p,m,pvclass))  ;

DUPVcrossprod_np(n,p,m,pvclass)$nwithdupv(n,pvclass) = DUPVsigma(n,m,pvclass)*DUPVOp(n,p,m,pvclass)
                  *sum[nn, TPVsigma(nn,p,m)*UPV_UPV_correlnp(n,nn,m)]
            - UPV_UPV_correlnp(n,n,m)*sqr(DUPVsigma(n,m,pvclass)*DUPVOp(n,p,m,pvclass))  ;

distPVcrossprod_np(n,p,m) = distPVsigma(n,m)*distPVOp(n,p,m)
                  *sum[nn, TPVsigma(nn,p,m)*UPV_UPV_correlnp(n,nn,m)]
            - UPV_UPV_correlnp(n,n,m)*sqr(distPVsigma(n,m)*distPVOp(n,p,m))  ;

UPVcrossprod(p,m,pvclass) = 0.5*sum(n, UPVcrossprod_np(n,p,m,pvclass)) ;
DUPVcrossprod(p,m,pvclass) = 0.5*sum(n, DUPVcrossprod_np(n,p,m,pvclass)) ;
distPVcrossprod(p,m) = 0.5*sum(n, distPVcrossprod_np(n,p,m)) ;

upvk2(p,m) = UPV2(p,m)+2*sum(pvclass$nwithupv(p,pvclass), UPVcrossprod(p,m,pvclass)) ;
dupvk2(p,m) = DUPV2(p,m)+2*sum(pvclass$nwithdupv(p,pvclass), DUPVcrossprod(p,m,pvclass)) ;
distpvk2(p,m) = distPV2(p,m)+2*distPVcrossprod(p,m) ;
pvk2(p,m) = upvk2(p,m) + dupvk2(p,m) + distpvk2(p,m) ;

* DJM 8/3/2013 RTOsurplus
Parameter pvk2_rto(rto,m), upvk2_rto(rto,m), dupvk2_rto(rto,m), distpvk2_rto(rto,m), TPVnrtom(n,rto,m),
         TPVnrtom_sigma(n,rto,m) sum of sigma capacities for all PV from n to rto ,
         UPVOrto(n,rto,m,pvclass), DUPVOrto(n,rto,m,pvclass), distPVOrto(n,rto,m) ;
UPVOrto(n,rto,m,pvclass) = sum(p$nrto(p,rto), UPVOp(n,p,m,pvclass)) ;
DUPVOrto(n,rto,m,pvclass) = sum(p$nrto(p,rto), DUPVOp(n,p,m,pvclass)) ;
distPVOrto(n,rto,m) = sum(p$nrto(p,rto), distPVOp(n,p,m)) ;
TPVnrtom(n,rto,m) =  sum(p$nrto(p,rto), TPVnpm(n,p,m)) ;
TPVnrtom_sigma(n,rto,m) = sum(pvclass$nwithupv(n,pvclass), UPVsigma(n,m,pvclass) * UPVOrto(n,rto,m,pvclass))
         +  sum(pvclass$nwithdupv(n,pvclass), DUPVsigma(n,m,pvclass) * DUPVOrto(n,rto,m,pvclass))
         +  distPVsigma(n,m) * distPVOrto(n,rto,m) ;

upvk2_rto(rto,m) = sum((n,pvclass)$nwithupv(n,pvclass), (UPVsigma(n,m,pvclass) * UPVOrto(n,rto,m,pvclass))**2
         + UPVsigma(n,m,pvclass) * UPVOrto(n,rto,m,pvclass)
         * sum[nn, TPVnrtom_sigma(nn,rto,m) * upv_upv_correlnp(n,nn,m)]
         - upv_upv_correlnp(n,n,m)*(UPVsigma(n,m,pvclass) * UPVOrto(n,rto,m,pvclass))**2 ) ;

dupvk2_rto(rto,m) = sum((n,pvclass)$nwithdupv(n,pvclass), (DUPVsigma(n,m,pvclass) * DUPVOrto(n,rto,m,pvclass))**2
         + DUPVsigma(n,m,pvclass) * DUPVOrto(n,rto,m,pvclass)
         * sum[nn, TPVnrtom_sigma(nn,rto,m) * upv_upv_correlnp(n,nn,m)]
         - upv_upv_correlnp(n,n,m)*(DUPVsigma(n,m,pvclass) * DUPVOrto(n,rto,m,pvclass))**2 ) ;

distpvk2_rto(rto,m) = sum(n, (distPVsigma(n,m) * distPVOrto(n,rto,m))**2
         + distPVsigma(n,m) * distPVOrto(n,rto,m)
         * sum[nn, TPVnrtom_sigma(nn,rto,m) * upv_upv_correlnp(n,nn,m)]
         - upv_upv_correlnp(n,n,m)*(distPVsigma(n,m) * distPVOrto(n,rto,m))**2 ) ;

pvk2_rto(rto,m) = upvk2_rto(rto,m) + dupvk2_rto(rto,m) + distpvk2_rto(rto,m) ;

TPV(p,m)$(TPV(p,m)<0.001) = 0 ;
pvk2(n,m)$(pvk1(n,m)<0.001) = 0 ;
pvk1(n,m)$(pvk1(n,m)<0.001) = 0 ;
pvk2_rto(rto,m)$(sum(n$nrto(n,rto), pvk1(n,m))<0.001) = 0 ;


*--------MHK Wave-------
* 11-06-12 SMC Section for MHK Wave added
* 02-14-13 SMC Added switch for use with MHK OFF
mhkwk1(n,m) = 0 ;
mhkwk2(n,m) = 0 ;
mhkwk2_rto(rto,m) = 0 ;

MHKWcap(n) = CONVOLDqctn('ocean','none',n) ;
TMHKWnpm(n,p,m) = MHKWcap(n) * Powfrac_downstream(n,p,m) ;
TMHKW(p,m) = sum(n,TMHKWnpm(n,p,m)) ;
TMHKW2(p,m) = sum(n, (abs(WAVEsigma(n,m)*TMHKWnpm(n,p,m))**2)) ;
* Using 'p' rather than 'n' here to emphasize that 'k1' is related to generation at 'p'
mhkwk1(p,m) = MHKWp(p,m) ;
TMHKWcrossprod_np(n,p,m) = WAVEsigma(n,m)*TMHKWnpm(n,p,m)
         * sum(nn,WAVEsigma(n,m)*TMHKWnpm(nn,p,m)*WAVE_correlnp(n,nn,m))
         - WAVE_correlnp(n,n,m)*sqr(WAVEsigma(n,m)*TMHKWnpm(n,p,m)) ;
TMHKWcrossprod(p,m) = 0.5*sum(n, TMHKWcrossprod_np(n,p,m)) ;
* Using 'p' rather than 'n' here to emphasize that 'k2' is related to generation at 'p'
mhkwk2(p,m) = TMHKW2(p,m) + 2*TMHKWcrossprod(p,m) ;

TMHKWnrtom(n,rto,m) = sum(p$nrto(p,rto), TMHKWnpm(n,p,m)) ;

mhkwk2_rto(rto,m) =  sum(n, abs((WAVEsigma(n,m) * TMHKWnrtom(n,rto,m))**2))
  + sum(n, WAVEsigma(n,m) * TMHKWnrtom(n,rto,m)
                  * sum[nn, WAVEsigma(n,m) * TMHKWnrtom(nn,rto,m) * WAVE_correlnp(n,nn,m)]
             - WAVE_correlnp(n,n,m)*(WAVEsigma(n,m) * TMHKWnrtom(n,rto,m))**2 )
;


TMHKW(p,m)$(TMHKW(p,m)<0.001) = 0 ;
mhkwk2(p,m)$(mhkwk1(p,m)<0.001) = 0 ;
mhkwk1(p,m)$(mhkwk1(p,m)<0.001) = 0 ;
mhkwk2_rto(rto,m)$(sum(p$nrto(p,rto), mhkwk1(p,m)<0.001)) = 0 ;


*--------Load--------
lk1(n,m) = load(n,m) ;  //lk1 is just addition of a scalar later, so it's not used for CC.
lk2(n,m) = lk2n(n,m) * (lk1(n,m))**2 ;
lk1_rto(rto,m) = sum(n$nrto(n,rto), lk1(n,m)) ;
lk2_rto(rto,m) = lk2FactorRto(rto,m) * (lk1_rto(rto,m))**2 ;

*lk2_rto(rto,m) = sum(p$nrto(p,rto), lk2(p,m)) ;


*----Conventionals---
*01-22-15 BAF exclude distPV as it is already accounted for in pvk1 and pvk2
*10-09-15 BAF add CSP with storage onto ck1 and ck2 (must run values also adjusted accordingly)
ck1(n,m) = sum((q,ct)$(not distPVtech(q)), CONVOLDqctn(q,ct,n)*(1-FOq(q))) ;
ck1(p,m) = sum(n, ck1(n,m)*Powfrac_downstream(n,p,m)) + cspstk1(p,m) ;

numplants(q,n) = round( sum(ct,CONVOLDqctn(q,ct,n))/nomsize(q) ) ;

plantsize(q,n) = nomsize(q) ;
plantsize(q,n)$numplants(q,n) = sum(ct,CONVOLDqctn(q,ct,n)) / numplants(q,n) ;
ck2(n,m) = sum(q$(not distPVtech(q)), numplants(q,n)*plantsize(q,n)*plantsize(q,n)*foq(q)*(1-foq(q))) ;
ck2(p,m) = sum(n, ck2(n,m)*Powfrac_downstream(n,p,m)) + cspstk2(p,m) ;

*---------Storage-----
sk1(n,m) = sum(st,
                    STORold(n,st)$(not thermal_st(st))
                 + (STORout.l(m,n,st) - STORin.l(m,n,st))$thermal_st(st)
           )
;
sk1(n,m)$(sk1(n,m) < 0) = 0 ;
* sk2 is not polished: assume CAES, assume all capacity available for charging/discharging, 50 MW plant.
sk2(n,m) = sk1(n,m)/50 * 50**2 * FOst("CAES") * (1-FOst("CAES")) ;


Parameter Powfrac_downirto(i,rto,m),Powfrac_downnrto(n,rto,m), DUPVpowfrac_downnrto(n,rto,m), distPVpowfrac_downnrto(n,rto,m) ;
Powfrac_downirto(i,rto,m) = sum(p$nrto(p,rto), Powfrac_downi(i,p,m)) ;
Powfrac_downnrto(n,rto,m) = sum(p$nrto(p,rto), Powfrac_downstream(n,p,m)) ;
DUPVpowfrac_downnrto(n,rto,m) = sum(p$nrto(p,rto), DUPVpowfrac_downstream(n,p,m)) ;
distPVpowfrac_downnrto(n,rto,m) = sum(p$nrto(p,rto), distPVpowfrac_downstream(n,p,m)) ;

*--------dCSP-------
Rcspk1(cCSP,i,p,m)$(classcsp(cCSP,i) and iwithcsp(i) and Powfrac_downi(i,p,m)) = wincrement * CFcsp(cCSP,m) * Powfrac_downi(i,p,m) ;

Parameter Rcspk2_rto(cCSP,i,rto,m) ;
Rcspk2_rto(cCSP,i,rto,m)$Powfrac_downirto(i,rto,m) =
    (CSPsigma(cCSP,m) * wincrement * Powfrac_downirto(i,rto,m))**2                   //variance of the increment of wind at v,i
  + 2*cspsigma(cCSP,m) * wincrement * Powfrac_downirto(i,rto,m)                      //2*(sum of covariances between the increment and all old wind serving rto)
                  * sum[(cCSP2,ii), cspsigma(cCSP2,m)*TCSPcirtom(cCSP2,ii,rto,m)*
                                 csp_csp_correlation(i,cCSP,ii,cCSP2,m)
                       ]
;

*------- dMHK Wave ---------
Rmhkwk1(mhkwaveclass,n,p,m)$Powfrac_downstream(n,p,m) = wincrement * WAVECF(n,mhkwaveclass,m) * Powfrac_downstream(n,p,m) ;

Parameter Rmhkwk2_rto(mhkwaveclass,n,rto,m) ;

Rmhkwk2_rto(mhkwaveclass,n,rto,m)$Powfrac_downnrto(n,rto,m) =
    (WAVEsigma(n,m) * wincrement * Powfrac_downnrto(n,rto,m))**2
  + 2*WAVEsigma(n,m) * wincrement * Powfrac_downnrto(n,rto,m)
                  * sum[nn, WAVEsigma(n,m)*TMHKWnrtom(nn,rto,m)*
                                 WAVE_correlnp(n,nn,m)
                       ]
;

*--------dWind-------
Rwk1(v,windtype,i,p,m)$(Powfrac_downi(i,p,m) and windexist(v,windtype,i)) = wincrement*CF(i,v,windtype,m)*Powfrac_downi(i,p,m) ;

*DJM 10/31/2013 Variance and covariance due to incremental wind at v,i. Does not include wk2_rto for existing wind capacity
Parameter Rwk2_rto(v,windtype,i,rto,m) ;
Rwk2_rto(v,windtype,i,rto,m)$(Powfrac_downirto(i,rto,m) and windexist(v,windtype,i)) =
         wvariance(v,windtype,i,m) * (wincrement * Powfrac_downirto(i,rto,m))**2        //variance of the increment of wind at v,i
         + 2*wsigma(v,windtype,i,m) * wincrement * Powfrac_downirto(i,rto,m)            //2*(sum of covariances between the increment and all old wind serving rto)
                  * sum[(v2,ii,windtype2), wsigmaold(v2,windtype2,ii,m)*TWcirtom(v2,windtype2,ii,rto,m)*
                                 w_w_correlation(i,v,ii,v2)
                       ]
;

*11-26-14 BAF separate total PV into UPV, DUPV, and distPV components and add pvclass index
*--------dUPV-------
Rupvk1(n,p,m,pvclass)$(nwithupv(n,pvclass) and Powfrac_downstream(n,p,m)) = wincrement * CFUPV(n,m,pvclass) * Powfrac_downstream(n,p,m) ;

Parameter Rupvk2_rto(n,rto,m,pvclass) ;

Rupvk2_rto(n,rto,m,pvclass)$(nwithupv(n,pvclass) and Powfrac_downnrto(n,rto,m)) =
    (UPVsigma(n,m,pvclass) * wincrement * Powfrac_downnrto(n,rto,m))**2                   //variance of the increment of UPV at pvclass,n
    + 2*UPVsigma(n,m,pvclass) * wincrement * Powfrac_downnrto(n,rto,m)                    //2*(sum of covariances between the increment and all old PV serving rto)
                  * sum[nn, TPVnrtom_sigma(nn,rto,m)*upv_upv_correlnp(n,nn,m)] ;

*--------dDUPV-------
Rdupvk1(n,p,m,pvclass)$(nwithdupv(n,pvclass) and DUPVpowfrac_downstream(n,p,m)) = wincrement * CFDUPV(n,m,pvclass) * DUPVpowfrac_downstream(n,p,m) ;

Parameter Rdupvk2_rto(n,rto,m,pvclass) ;
Rdupvk2_rto(n,rto,m,pvclass)$(nwithdupv(n,pvclass) and DUPVpowfrac_downnrto(n,rto,m)) =
    (DUPVsigma(n,m,pvclass) * wincrement * DUPVpowfrac_downnrto(n,rto,m))**2                   //variance of the increment of DUPV at pvclass,n
    + 2*DUPVsigma(n,m,pvclass) * wincrement * DUPVpowfrac_downnrto(n,rto,m)                         //2*(sum of covariances between the increment and all old PV serving rto)
                  * sum[nn, TPVnrtom_sigma(nn,rto,m)*upv_upv_correlnp(n,nn,m)] ;

*--------ddistPV------
Rdistpvk1(n,p,m)$distPVpowfrac_downstream(n,p,m) = wincrement * distPVCF(n,m) * distPVpowfrac_downstream(n,p,m) ;

Parameter Rdistpvk2_rto(n,rto,m) ;
Rdistpvk2_rto(n,rto,m)$distPVpowfrac_downnrto(n,rto,m) =
    (distPVsigma(n,m) * wincrement * distPVpowfrac_downnrto(n,rto,m))**2                   //variance of the increment of distPV at n
    + 2*distPVsigma(n,m) * wincrement * distPVpowfrac_downnrto(n,rto,m)                         //2*(sum of covariances between the increment and all old PV serving rto)
                  * sum[nn, TPVnrtom_sigma(nn,rto,m)*upv_upv_correlnp(n,nn,m)] ;


*-------------- End Capacity Credit Calculations -----------------------*


*-------------- Start Surplus Calculations ----------------------------*

* 11-07-12 SMC Added parameters for MHK wave (beginning with M)
* 03-14-13 PTS/EI Modified must-run level in surplus of alternative systems (with same load).
*12-02-14 BAF add pvclass to appropriate PV terms
*01-11-17 BAF add REflowSwitch

Parameters REk1(p,m) E(renewables),
         REk2(p,m) Var(renewables),
         ck1q(q,p,s) must-run conventional capacity (MW) by type,
         CSPSurplus(cCSP,i,rto,m) curtailments at p with dCSP (MW),
         CSPSurplusmar(cCSP,i,m) marginal curtailment rate for dCSP at i,
         MHKWSurplus(n,rto,mhkwaveclass,m) curtailments at rto with dMHKW (MW),
         MHKWSurplusmar(n,mhkwaveclass,m) marginal curtailment rate for dMHKW at n,
* PTS 8/30/13 RTOsurplus
         zk1_rto(rto,m),
         zk2_rto(rto,m),
         netimports(p,m) ,
         numplants_minq(q,p) ,
         plantsizeq(q,p),
         Cck1(cCSP,i,p,m),
         Cck2(cCSP,i,p,m),
         Mck1(mhkwaveclass,n,p,m),
         Mck2(mhkwaveclass,n,p,m) var(V) (MW^2),
         Czk1_rto(cCSP,i,rto,m) E(V+S+W+CSP+dCSP+PV+MHKW),
         Czk2_rto(cCSP,i,rto,m) var(V+S+W+CSP+dCSP+PV+MHKW+L),
* PTS 8/30/13 RTOsurplus
         Surplus(rto,m) curtailments at rto associated with existing system (MW),
         SurpOld(n,m) curtailed VRRE at n,
         UPVSurplusmar(n,m,pvclass) marginal curtailment rate for dUPV at n,
         DUPVSurplusmar(n,m,pvclass) marginal curtailment rate for DUPV at n,
         distPVSurplusmar(n,m) marginal curtailment rate for ddistPV at n,
         WSurplusmar(v,windtype,i,m) marginal curtailment rate for dW at i,
         MRSurplusMar_region(m,n) curtailment induced at n by incremental increase in MR,
         MRSurplusMar(p,m) marginal curtailment rate for dMR at p,
         UPVSurplusMar_annual(n) annual marginal curtailment rate for an incremental amount of UPV at n
         DUPVSurplusMar_annual(n) annual marginal curtailment rate for an incremental amount of DUPV at n
         distPVSurplusMar_annual(n) annual marginal curtailment rate for an incremental amount of distPV at n
         WSurplusMar_annual(windtype,i) annual marginal curtailment rate for an incremental amount of wind at i
;

$ifthen %REflowSwitch% == 'ON'
Parameters Bck1(p,m), Rck1(v,windtype,i,p,m), Pck1(n,p,m,pvclass), Dck1(n,p,m,pvclass), distDck1(n,p,m), MRck1(n),
         Bck2(p,m), Rck2(v,windtype,i,p,m), Pck2(n,p,m,pvclass), Dck2(n,p,m,pvclass), distDck2(n,p,m), MRck2(n,m),
         sk1_efficacy(n,s),
         storage_effectiveness(n,m) Effectiveness of storage to reduce curtailments via charging,
         Szk1_rto(p,m),
         Szk2_rto(p,m),
         MRzk1_rto(p,m),
         MRzk2_rto(p,m),
         Bzk1(n,m) E(V),
         Bzk2(n,m) var(V),
         Rzk1(v,windtype,i,p,m) E(V+S+W+dW+CSP+PV+MHKW),
         Rzk2(v,windtype,i,p,m) var(V+S+W+dW+CSP+PV+MHKW+L),
         Mzk1(mhkwaveclass,n,p,m) E(V+S+W+CSP+PV+MHKW+dMHKW),
         Mzk2(mhkwaveclass,n,p,m) var(V+S+W+CSP+PV+MHKW+dMHKW+L),
         Rsk1(n,m) E(dS),
         Rsk2(n,m) E(S+dS),
         StSurplus_rto(p,m),
         StSurpRecMar(n,m) surplus recovered per MW of new storage capacity,
         StSurpRecMar_np(n,p,m) curtailments recovered at n via storage increase at p,
         MRfrac(n,m) must-run fraction. used to reduce netimports,
         BSurplus(rto,m) curtailments at rto with no VRRE (MW),
         WSurplus(v,windtype,i,rto,m) curtailments at rto with dW (MW),
         WSurplusmarp(v,windtype,i,p,m),
         UPVSurplus(n,rto,m,pvclass) curtailments at rto with dUPV (MW),
         DUPVSurplus(n,rto,m,pvclass) curtailments at rto with DUPV (MW),
         distPVSurplus(n,rto,m) curtailments at rto with ddistPV (MW),
         distPVSurplus_rto(p,m) curtailments at n with ddistPV (MW),
         MRSurplus_rto(p,m) curtailments at p with dMR (MW),
         MRSurplusMar_np(n,p,m) curtailments induced at n by MR increase at p,
         Rzk1_rto(v,windtype,i,rto,m)
         Rzk2_rto(v,windtype,i,rto,m)
         Bzk1_rto(rto,m)
         Bzk2_rto(rto,m)
         SurpOld_rto(rto,m)
         Pzk1_rto(n,rto,m,pvclass) E(V+S+W+CSP+PV+dUPV+MHKW),
         Pzk2_rto(n,rto,m,pvclass) var(V+S+W+CSP+PV+dUPV+MHKW+L),
*02-03-15 BAF add DUPV and distPV terms
         Dzk1_rto(n,rto,m,pvclass) E(V+S+W+CSP+PV+dDUPV+MHKW),
         Dzk2_rto(n,rto,m,pvclass) var(V+S+W+CSP+PV+dDUPV+MHKW),
         distDzk1_rto(n,rto,m) E(V+S+W+CSP+PV+ddistPV+MHKW),
         distDzk2_rto(n,rto,m) var(V+S+W+CSP+PV+ddistPV+MHKW),
         SurpOld_p(p,m)
;

Scalars max_sthrs maximum hours per storage unit where it will not be energy-limited / 36 /,
         sthrs hours of storage per storage unit / 33 /
;
$endif

* Calculate must-run portion of conventionals
Sets canadan(n) ;
Variables CONVqctmn(q,ct,m,n), CONVOLDqctmn(q,ct,m,n)  ;
Parameters minplantload(q), minplantloadqn(q,n) ;
$gdxin "outputs%ds%variabilityFiles%ds%REflow_%case%_%next_year%.gdx"
$loaddc minplantload, CONVqctmn, CONVOLDqctmn, canadan
$gdxin

* 08-27-14 EI/OZ Set min plant loading for Canadian hydro to 0.5 to avoid curtailment problems
minplantloadqn(q,n) = minplantload(q) ;
minplantloadqn("hydro",n)$canadan(n) = 0.5 ;

ck1q(q,n,s) = smax(m$seaperiods(s,m), sum(ct,CONVqctmn.l(q,ct,m,n) + CONVOLDqctmn.l(q,ct,m,n))) ;
numplants_minq(q,p) = round(ck1q(q,p,"summer")/nomsize(q)) ;
plantsizeq(q,p) = ck1q(q,p,"summer")/max(1,numplants_minq(q,p)) * minplantloadqn(q,p) ;

* 10-09-15 BAF add CSP with storage. Assume FOR=0.05 (CSPwStor_fo is actually 0 but using it here would set csp portion to 0).
Parameters cspstk1q(n,s), cspst_numplants_minq(p), cspst_plantsizeq(p), cspstk1q(n,s) ;
cspstk1q(n,s) = smax(m$seaperiods(s,m), CSPstGenOld(n,m)) ;
cspst_numplants_minq(p) = round(cspstk1q(p,"summer")/CSPwStor_nomsize) ;
cspst_plantsizeq(p) = cspstk1q(p,"summer")/max(1,cspst_numplants_minq(p)) * CSPwStor_minload;
cspstk1q(n,s) = cspstk1q(n,s) * CSPwStor_minload ;

ck1q(q,n,s) = ck1q(q,n,s) * minplantloadqn(q,n) ;
ck1(n,m) = sum((q,s)$seaperiods(s,m), ck1q(q,n,s)) + sum(s$seaperiods(s,m), cspstk1q(n,s)) ;
ck1(p,m) = sum(n, ck1(n,m)*Powfrac_downstream(n,p,m)) ;

ck2(n,m) = sum(q, numplants_minq(q,n) * plantsizeq(q,n)**2 * FOq(q)*(1-FOq(q))) + cspst_numplants_minq(n) * cspst_plantsizeq(n)**2 * 0.05*(1-0.05) ;
ck2(p,m) = sum(n, ck2(n,m)*Powfrac_downstream(n,p,m)) ;

* Expected renewable generation (and variance)
REk1(p,m) = wk1(p,m) + pvk1(p,m) + cspk1(p,m) + mhkwk1(p,m) ;
REk2(p,m) = wk2(p,m) + pvk2(p,m) + cspk2(p,m) + mhkwk2(p,m) ;


$ifthen %REflowSwitch% == 'ON'

* Finish calculate must-run portion of conventionals
MRfrac(n,m) = 0.5 ;
MRfrac(n,m)$sum((q,ct), CONVOLDqctn(q,ct,n)) = ck1(n,m) / sum((q,ct), CONVOLDqctn(q,ct,n)) ;

sk1(n,m) = sum(st,
                   STORold(n,st)$(not thermal_st(st))
                + (STORin.l(m,n,st) - STORout.l(m,n,st))$thermal_st(st)
           ) ;

* 07-30-09ish TTM (Comment added by EI)
* compute efficacy of storage capacity to recover surplus by a seasonable factor based on VRRE/load during that season.
*   The motivation is come up with a functional form that captures the ability of storage to “perfectly” reduce curtailment
*   in the limit of infinite storage (e.g. sthrs = max_sthrs) and not reduce any curtailment in the limit that sthrs = 0.
*   I recall playing with some hyperbolic functions to come up with a reasonable s-shaped curve, but don’t remember exactly remember the derivation right now.
* 02-26-2016 WJC comments: sk1_efficacy goes to 1 when sthrs = max_sthrs and goes to 0 when sthrs = 0.
* The max and min terms in the calculation ensure that sk1_efficacy is always between 0 and 1
sk1_efficacy(n,s)$(sum(m,lk1(n,m))>0) = max(0, min(1, 1-(1-sthrs/max_sthrs)*(1-exp(-(max_sthrs/sthrs) *
         ( sum(m$seaperiods(s,m), (wk1(n,m) + pvk1(n,m) + cspk1(n,m) + mhkwk1(n,m))*Hm(m))
                 /sum(m$seaperiods(s,m), lk1(n,m)*Hm(m))
         )                                                      )
                                                          ) / (1-exp(-max_sthrs/sthrs))
                                )
                         )
;

*storage_effectiveness(n,m) = sum(s$seaperiods(s,m), sk1_efficacy(n,s)) ;
storage_effectiveness(n,m) = 1;
sk1(n,m) = sum(s$seaperiods(s,m), sk1_efficacy(n,s)*sk1(n,m)) ;

$endif


*----surplus on existing system-----*
* PTS 8/30/13 RTOsurplus
zk1_rto(rto,m) = sum(p$nrto(p,rto), ck1(p,m) + REk1(p,m)) - lk1_rto(rto,m) ;
zk2_rto(rto,m) = sum(p$nrto(p,rto), ck2(p,m)) + lk2_rto(rto,m) + wk2_rto(rto,m) + cspk2_rto(rto,m) + pvk2_rto(rto,m) + mhkwk2_rto(rto,m)  ;

parameter REk1_rto(RTO,m), REK2_RTO(rto,m), cslk1_rto(rto,m), cslk2_rto(rto,m) ;

REk2_rto(rto,m) = wk2_rto(rto,m) + cspk2_rto(rto,m) + pvk2_rto(rto,m) + mhkwk2_rto(rto,m)  ;
REK1_rto(rto,m) = sum(p$nrto(p,rto), REk1(p,m)) ;

cslk1_rto(rto,m) = sum(p$nrto(p,rto), ck1(p,m)) - lk1_rto(rto,m) ;
cslk2_rto(rto,m) = sum(p$nrto(p,rto),  ck2(p,m)) + lk2_rto(rto,m) ;

* PTS 8/30/13 RTOsurplus
Surplus(rto,m) = 0 ;
Surplus(rto,m)$(zk2_rto(rto,m)>0) = zk1_rto(rto,m)*errorf(zk1_rto(rto,m)/sqrt(zk2_rto(rto,m)))
                 + sqrt(zk2_rto(rto,m)/2/3.1416) * exp(-(zk1_rto(rto,m)*zk1_rto(rto,m))/2/zk2_rto(rto,m)) ;


$ifthen %REflowSwitch% == 'ON'

*----surplus with no VRRE----*
* 03-14-13 PTS/EI Modified must-run level in surplus of alternative systems (with same load).
Bck1(p,m)$(lk1(p,m)>0) = ck1(p,m) * ((lk1(p,m) + REk1(p,m)) / lk1(p,m) - 1) ;
Bck2(p,m) = 0 ;
Bck2(p,m)$(ck1(p,m) > 0) = ck2(p,m) * (((Bck1(p,m) + ck1(p,m)) / ck1(p,m))**2 - 1) ;


* PTS 8/30/13 RTOsurplus
Bzk1_rto(rto,m) = sum(p$nrto(p,rto), ck1(p,m) + Bck1(p,m)) - lk1_rto(rto,m) ;
Bzk2_rto(rto,m) = sum(p$nrto(p,rto), ck1(p,m) + Bck2(p,m)) + lk2_rto(rto,m) ;

parameter Bcslk1_rto(rto,m), Bcslk2_rto(rto,m) ;


* PTS 8/30/13 RTOsurplus
BSurplus(rto,m) = 0 ;
BSurplus(rto,m)$(Bzk2_rto(rto,m)>0) = Bzk1_rto(rto,m)*errorf(Bzk1_rto(rto,m)/sqrt(Bzk2_rto(rto,m)))
                 + sqrt(Bzk2_rto(rto,m)/2/3.1416) * exp(-(Bzk1_rto(rto,m)*Bzk1_rto(rto,m))/2/Bzk2_rto(rto,m)) ;

*----end surplus with no VRRE----*

* PTS 8/30/13 RTOsurplus: divide RTO surplus among PCAs based on REk1
SurpOld_rto(rto,m) = Surplus(rto,m) - BSurplus(rto,m) ;
SurpOld_p(p,m)$REk1(p,m) = REk1(p,m) * sum(rto$nrto(p,rto), SurpOld_rto(rto,m) / sum(pp$nrto(pp,rto), REk1(pp,m))) ;
SurpOld(n,m) = sum(p, SurpOld_p(p,m) * REfrac_upstream(p,n,m)) ;
SurpOld(n,m) = min(SurpOld(n,m), (WGenOld(n,m) + CSPGenOld(n,m) + PVGenOld(n,m) + MHKwaveGenOld(n,m))) ;
SurpOld(n,m)$(SurpOld(n,m)<.1) = 0 ;
*Parameter SurpOld_ave(m) fractional curtailment averaged across country ;
*SurpOld_ave(m) = sum(n, SurpOld(n,m) * Hm(m)) / sum(n, (WGenOld(n,m) + CSPGenOld(n,m) + PVGenOld(n,m) + MHKwaveGenOld(n,m)) * Hm(m)) ;   //PVGenOld includes UPV, DUPV, and distPV
*SurpOld_ave('H17') = sum((n,m), SurpOld(n,m) * Hm(m)) / sum((n,m), (WGenOld(n,m) + CSPGenOld(n,m) + PVGenOld(n,m) + MHKwaveGenOld(n,m)) * Hm(m)) ;

$endif


*----surplus with incremental CSP----*
* 03-14-13 PTS/EI Modified must-run level in surplus of alternative systems (with same load).
Cck1(cCSP,i,p,m)$((lk1(p,m) + Rcspk1(cCSP,i,p,m)) > 0) = ck1(p,m) *(lk1(p,m) / (lk1(p,m) + Rcspk1(cCSP,i,p,m)) - 1) ;
Cck2(cCSP,i,p,m) = 0 ;
Cck2(cCSP,i,p,m)$ck1(p,m) = ck2(p,m) * (((Cck1(cCSP,i,p,m) + ck1(p,m)) / ck1(p,m))**2 - 1) ;

* DJM 8/30/13 RTOsurplus
Czk1_rto(cCSP,i,rto,m) = zk1_rto(rto,m) + sum(p$nrto(p,rto), Cck1(cCSP,i,p,m) + Rcspk1(cCSP,i,p,m))  ;
Czk2_rto(cCSP,i,rto,m) = zk2_rto(rto,m) + sum(p$nrto(p,rto), Cck2(cCSP,i,p,m)) + Rcspk2_rto(cCSP,i,rto,m) ;

* PTS 8/30/13 RTOsurplus
CSPSurplus(cCSP,i,rto,m) = 0 ;
CSPSurplus(cCSP,i,rto,m)$(Czk2_rto(cCSP,i,rto,m)>0 and sum(p$nrto(p,rto), RCSPk1(cCSP,i,p,m)) > 0) = Czk1_rto(cCSP,i,rto,m)*errorf(Czk1_rto(cCSP,i,rto,m)/sqrt(Czk2_rto(cCSP,i,rto,m)))
         + sqrt(Czk2_rto(cCSP,i,rto,m)/2/3.1416) * exp(-(Czk1_rto(cCSP,i,rto,m)*Czk1_rto(cCSP,i,rto,m))/2/Czk2_rto(cCSP,i,rto,m)) ;

* PTS 8/30/13 RTOsurplus: divide RTO surplus among PCAs based on Rcspk1
CSPSurplusmar(cCSP,i,m)$(CFcsp(cCSP,m) and sum(p,Rcspk1(cCSP,i,p,m))>0) = sum(p$Powfrac_downi(i,p,m), RCSPk1(cCSP,i,p,m) *
         sum(rto$nrto(p,rto), (CSPSurplus(cCSP,i,rto,m) - Surplus(rto,m)) / sum(pp$nrto(pp,rto), Rcspk1(cCSP,i,pp,m)))) / (wincrement*CFCSP(cCSP,m)) ;

CSPsurplusmar(cCSP,i,m) = max(0, CSPsurplusmar(cCSP,i,m)) ;
CSPsurplusmar(cCSP,i,m) = min(1, CSPsurplusmar(cCSP,i,m)) ;
CSPSurplusMar(cCSP,i,m)$(CSPSurplusMar(cCSP,i,m)<.001) = 0 ;


$ifthen %REflowSwitch% == 'ON'

*----surplus with incremental wind----*
* 03-14-13 PTS/EI Modified must-run level in surplus of alternative systems (with same load).
* 10-31-2013 DJM Rck1 is the capacity of must run by which ck1 should ck1 be adjusted
Rck1(v,windtype,i,p,m)$(windexist(v,windtype,i) and (lk1(p,m) + Rwk1(v,windtype,i,p,m)) > 0) = ck1(p,m) * (lk1(p,m) / (lk1(p,m) + Rwk1(v,windtype,i,p,m)) - 1) ;
Rck2(v,windtype,i,p,m) = 0 ;
Rck2(v,windtype,i,p,m)$(ck1(p,m) and windexist(v,windtype,i)) = ck2(p,m) * (((ck1(p,m) + Rck1(v,windtype,i,p,m)) / ck1(p,m))**2 - 1) ;

parameter wk1_rto(v,windtype,i,rto,m) ;
wk1_rto(v,windtype,i,rto,m)$(windexist(v,windtype,i)) = sum(p$nrto(p,rto), rwk1(v,windtype,i,p,m)) ;


* PTS 8/30/13 RTOsurplus
* 10-31-2013 DJM Adjust zk1 and zk2 due to additional incremental wind capacity at i by class v
Rzk1_rto(v,windtype,i,rto,m) = zk1_rto(rto,m) + sum(p$nrto(p,rto), Rck1(v,windtype,i,p,m) + Rwk1(v,windtype,i,p,m)) ;
Rzk2_rto(v,windtype,i,rto,m) = zk2_rto(rto,m) + sum(p$nrto(p,rto), Rck2(v,windtype,i,p,m)) + Rwk2_rto(v,windtype,i,rto,m) ;

* PTS 8/30/13 RTOsurplus
WSurplus(v,windtype,i,rto,m) = 0 ;
WSurplus(v,windtype,i,rto,m)$(Rzk2_rto(v,windtype,i,rto,m)>0 and sum(p$nrto(p,rto), Rwk1(v,windtype,i,p,m)) > 0 and windexist(v,windtype,i)) =
         Rzk1_rto(v,windtype,i,rto,m)*errorf(Rzk1_rto(v,windtype,i,rto,m)/sqrt(Rzk2_rto(v,windtype,i,rto,m)))
         + sqrt(Rzk2_rto(v,windtype,i,rto,m)/2/3.1416) * exp(-(Rzk1_rto(v,windtype,i,rto,m)*Rzk1_rto(v,windtype,i,rto,m))/2/Rzk2_rto(v,windtype,i,rto,m)) ;
WSurplusmarp(v,windtype,i,p,m)$(windexist(v,windtype,i) and Powfrac_downi(i,p,m) and (CF(i,v,windtype,m))) = Rwk1(v,windtype,i,p,m) *
         sum(rto$nrto(p,rto), (WSurplus(v,windtype,i,rto,m) - Surplus(rto,m)) / sum(pp$nrto(pp,rto), Rwk1(v,windtype,i,pp,m)))  / (wincrement*CF(i,v,windtype,m)) ;

*WSurplusmar(v,windtype,i,m)$(windexist(v,windtype,i)) = sum(rto, WSurplus(v,windtype,i,rto,m) - Surplus(rto,m)) ;// / (wincrement*CF(i,v,windtype,m)) ;

WSurplusmar(v,windtype,i,m)$(windexist(v,windtype,i) and (CF(i,v,windtype,m))) = sum(rto$WSurplus(v,windtype,i,rto,m), WSurplus(v,windtype,i,rto,m) - Surplus(rto,m)) / (wincrement*CF(i,v,windtype,m)) ;



* PTS 8/30/13 RTOsurplus: divide RTO surplus among PCAs based on Rwk1
*WSurplusmar(v,windtype,i,m)$(CF(i,v,windtype,m)) = sum(p$Powfrac_downi(i,p,m), Rwk1(v,windtype,i,p,m) *
*         sum(rto$nrto(p,rto), (WSurplus(v,windtype,i,rto,m) - Surplus(rto,m)) / sum(pp$nrto(pp,rto), Rwk1(v,windtype,i,pp,m)))) / (wincrement*CF(i,v,windtype,m)) ;
*Wsurplusmar(v,windtype,i,m)$(windexist(v,windtype,i)) = max(0, Wsurplusmar(v,windtype,i,m)) ;
Wsurplusmar(v,windtype,i,m)$(windexist(v,windtype,i)) = min(1, Wsurplusmar(v,windtype,i,m)) ;
Wsurplusmar(v,windtype,i,m)$(Wsurplusmar(v,windtype,i,m)<.003) = 0 ;


*----surplus with incremental UPV----*
* 03-14-13 PTS/EI Modified must-run level in surplus of alternative systems (with same load).
Pck1(n,p,m,pvclass)$((lk1(p,m) + Rupvk1(n,p,m,pvclass)) > 0) = ck1(p,m) * ((lk1(p,m) / (lk1(p,m) + Rupvk1(n,p,m,pvclass))) - 1) ;
Pck2(n,p,m,pvclass) = 0 ;
Pck2(n,p,m,pvclass)$ck1(p,m) = ck2(p,m) *(((Pck1(n,p,m,pvclass)+ ck1(p,m)) / ck1(p,m))**2 - 1) ;

* DJM 8/30/13 RTOsurplus
Pzk1_rto(n,rto,m,pvclass) = zk1_rto(rto,m) + sum(p$nrto(p,rto), Pck1(n,p,m,pvclass) + Rupvk1(n,p,m,pvclass))  ;
Pzk2_rto(n,rto,m,pvclass) = zk2_rto(rto,m) + sum(p$nrto(p,rto), Pck2(n,p,m,pvclass)) + Rupvk2_rto(n,rto,m,pvclass) ;
* PTS 8/30/13 RTOsurplus
UPVSurplus(n,rto,m,pvclass) = 0 ;
UPVSurplus(n,rto,m,pvclass)$(Pzk2_rto(n,rto,m,pvclass)>0 and sum(p$nrto(p,rto), Rupvk1(n,p,m,pvclass))>0) =
         Pzk1_rto(n,rto,m,pvclass)*errorf(pzk1_rto(n,rto,m,pvclass)/sqrt(pzk2_rto(n,rto,m,pvclass)))
         + sqrt(pzk2_rto(n,rto,m,pvclass)/2/3.1416) * exp(-(pzk1_rto(n,rto,m,pvclass)*pzk1_rto(n,rto,m,pvclass))/2/pzk2_rto(n,rto,m,pvclass)) ;

* PTS 8/30/13 RTOsurplus: divide RTO surplus among PCAs based on Rupvk1
UPVSurplusmar(n,m,pvclass)$CFUPV(n,m,pvclass) = sum(p$Powfrac_downstream(n,p,m), Rupvk1(n,p,m,pvclass) *
         sum(rto$nrto(p,rto), max(0,UPVSurplus(n,rto,m,pvclass) - Surplus(rto,m)) / sum(pp$nrto(pp,rto), Rupvk1(n,pp,m,pvclass)))) / (wincrement*CFUPV(n,m,pvclass)) ;

UPVSurplusmar(n,m,pvclass) = max(0, UPVSurplusmar(n,m,pvclass)) ;
UPVSurplusmar(n,m,pvclass) = min(1, UPVSurplusmar(n,m,pvclass)) ;
UPVSurplusMar(n,m,pvclass)$(UPVSurplusMar(n,m,pvclass)<.001) = 0 ;

*----surplus with incremental DUPV----*
* 03-14-13 PTS/EI Modified must-run level in surplus of alternative systems (with same load).
Dck1(n,p,m,pvclass)$((lk1(p,m) + Rdupvk1(n,p,m,pvclass)) >0) = ck1(p,m) * (lk1(p,m) / (lk1(p,m) + Rdupvk1(n,p,m,pvclass)) - 1) ;
Dck2(n,p,m,pvclass) = 0 ;
Dck2(n,p,m,pvclass)$ck1(p,m) = ck2(p,m) * (((Dck1(n,p,m,pvclass) + ck1(p,m)) / ck1(p,m))**2 - 1) ;

Dzk1_rto(n,rto,m,pvclass) = zk1_rto(rto,m) + sum(p$nrto(p,rto), Dck1(n,p,m,pvclass) + Rdupvk1(n,p,m,pvclass)) ;
Dzk2_rto(n,rto,m,pvclass) = zk2_rto(rto,m) + sum(p$nrto(p,rto), Dck2(n,p,m,pvclass) + Rdupvk2_rto(n,rto,m,pvclass)) ;

DUPVSurplus(n,rto,m,pvclass) = 0 ;
DUPVSurplus(n,rto,m,pvclass)$(Dzk2_rto(n,rto,m,pvclass)>0 and sum(p$nrto(p,rto), Rdupvk1(n,p,m,pvclass))>0) =
         Dzk1_rto(n,rto,m,pvclass)*errorf(Dzk1_rto(n,rto,m,pvclass)/sqrt(Dzk2_rto(n,rto,m,pvclass)))
         + sqrt(Dzk2_rto(n,rto,m,pvclass)/2/3.1416) * exp(-(Dzk1_rto(n,rto,m,pvclass)*Dzk1_rto(n,rto,m,pvclass))/2/Dzk2_rto(n,rto,m,pvclass)) ;

DUPVSurplusmar(n,m,pvclass)$CFDUPV(n,m,pvclass) = sum(p$DUPVpowfrac_downstream(n,p,m), Rdupvk1(n,p,m,pvclass) *
         sum(rto$nrto(p,rto), max(0,DUPVSurplus(n,rto,m,pvclass) - Surplus(rto,m)) / sum(pp$nrto(pp,rto), Rdupvk1(n,pp,m,pvclass)))) / (wincrement*CFDUPV(n,m,pvclass)) ;

DUPVSurplusmar(n,m,pvclass) = max(0, DUPVSurplusmar(n,m,pvclass)) ;
DUPVSurplusmar(n,m,pvclass) = min(1, DUPVSurplusmar(n,m,pvclass)) ;
DUPVSurplusMar(n,m,pvclass)$(DUPVSurplusMar(n,m,pvclass)<.001) = 0 ;


*----surplus with incremental distPV----*
* 03-14-13 PTS/EI Modified must-run level in surplus of alternative systems (with same load).
distDck1(n,p,m)$((lk1(p,m) + Rdistpvk1(n,p,m)) > 0) = ck1(p,m) * (lk1(p,m) / (lk1(p,m) + Rdistpvk1(n,p,m)) -1) ;
distDck2(n,p,m) = 0 ;
distDck2(n,p,m)$ck1(p,m) = ck2(p,m) * (((distDck1(n,p,m) + ck1(p,m)) / ck1(p,m))**2 -1) ;

distDzk1_rto(n,rto,m) = zk1_rto(rto,m) + sum(p$nrto(p,rto), distDck1(n,p,m) + Rdistpvk1(n,p,m)) ;
distDzk2_rto(n,rto,m) = zk2_rto(rto,m) + sum(p$nrto(p,rto), distDck2(n,p,m) + Rdistpvk2_rto(n,rto,m)) ;


distPVSurplus(n,rto,m) = 0 ;
distPVSurplus(n,rto,m)$(distDzk2_rto(n,rto,m)>0 and sum(p$nrto(p,rto), Rdistpvk1(n,p,m))>0) =
         distDzk1_rto(n,rto,m)*errorf(distDzk1_rto(n,rto,m)/sqrt(distDzk2_rto(n,rto,m)))
         + sqrt(distDzk2_rto(n,rto,m)/2/3.1416) * exp(-(distDzk1_rto(n,rto,m)*distDzk1_rto(n,rto,m))/2/distDzk2_rto(n,rto,m)) ;

distPVSurplusmar(n,m)$distPVCF(n,m) = sum(p$distPVpowfrac_downstream(n,p,m), Rdistpvk1(n,p,m) *
         sum(rto$nrto(p,rto), max(0,distPVSurplus(n,rto,m) - Surplus(rto,m)) / sum(pp$nrto(pp,rto), Rdistpvk1(n,pp,m)))) / (wincrement*distPVCF(n,m)) ;

distPVSurplusmar(n,m) = max(0, distPVSurplusmar(n,m)) ;
distPVSurplusmar(n,m) = min(1, distPVSurplusmar(n,m)) ;
distPVSurplusMar(n,m)$(distPVSurplusMar(n,m)<.001) = 0 ;


*----surplus with incremental storage----*
* 03-14-13 PTS/EI Modified must-run level in surplus of alternative systems (with same load).
Rsk1(p,m) = sum(s$seaperiods(s,m), sk1_efficacy(p,s)*2*wincrement) ;   // assume 200 MW of incremental build
Rsk2(p,m) = Rsk1(p,m)/50 * 50**2 * FOst("CAES")*(1-FOst("CAES")) ;


* 9/9/2013 DJM RTO surplus use the zk1 and zk2 across the rto but only add incremental
* zk1_rto(p,m) can be thought of as zk1_rto(p,rto,m), as in: expectation of capacity at
*   rto for incremental addition of storage at p.
*   sum(rto$nrto(p,rto) assigns zk1_rto to p.
Szk1_rto(p,m) = sum(rto$nrto(p,rto), zk1_rto(rto,m)) ;
Szk2_rto(p,m) = sum(rto$nrto(p,rto), zk2_rto(rto,m)) ;

* DJM Surplus in RTO when incremental storage is added at p.
* (at p, but represents surplus across entire rto containing p)
StSurplus_rto(p,m)$(Szk2_rto(p,m)>0) = Szk1_rto(p,m)*errorf(Szk1_rto(p,m)/sqrt(Szk2_rto(p,m)))
                 + sqrt(Szk2_rto(p,m)/2/3.1416) * exp(-(Szk1_rto(p,m)*Szk1_rto(p,m))/2/Szk2_rto(p,m)) ;

* StSurpRecMar(n,m) is a positive coefficient representing recovered curtailments
StSurpRecMar(p,m) =  -(StSurplus_rto(p,m) - sum(rto$nrto(p,rto), Surplus(rto,m))) / (2*wincrement) ;
StSurpRecMar(p,m) = max(0, StSurpRecMar(p,m)) ;
StSurpRecMar(p,m) = min(1, StSurpRecMar(p,m)) ;
StSurpRecMar(p,m)$(StSurpRecMar(p,m)<.01) = 0 ;

* 04-07-2016 WJC StSurpRecMar_np is no longer used in the model file.  These and associated
* calculation can be removed once we have finalized the new load duration curve methodology.
*StSurpRecMar_np(n,p,m) = -(StSurplus(p,m) - Surplus_p(p,m)) * Powfrac_upstream(p,n,m) / (2*wincrement) ;
StSurpRecMar_np(n,p,m) = StSurpRecMar(p,m) * Powfrac_upstream(n,p,m) ;
StSurpRecMar_np(n,p,m) = max(0, StSurpRecMar_np(n,p,m)) ;
StSurpRecMar_np(n,p,m) = min(1, StSurpRecMar_np(n,p,m)) ;
StSurpRecMar_np(n,p,m)$(StSurpRecMar_np(n,p,m)<.005) = 0 ;


*----surplus with incremental must-run----*
* In this case, the increment is not nameplate capacity but instead MW at minimum turndown.
*    That quantity is defined in the model by minplantload(q).
MRck1(p) = 200 ;   // assume 200 MW of incremental must-run (output not necessarily capacity)
* 1/14/13 PTS/EI include additional variance from new mustrun
MRck2(p,m) = 0 ;
MRck2(p,m)$(ck1(p,m)>0 and ((MRck1(p)+ck1(p,m))/ck1(p,m))>0) = ck2(p,m) * (((MRck1(p)+ck1(p,m))/ck1(p,m))**2-1) ;

MRzk1_rto(p,m) = sum(rto$nrto(p,rto), zk1_rto(rto,m)) + MRck1(p) ;
MRzk2_rto(p,m) = sum(rto$nrto(p,rto), zk2_rto(rto,m)) + MRck2(p,m) ;

MRSurplus_rto(p,m) = 0 ;
MRSurplus_rto(p,m)$(MRzk2_rto(p,m)>0) = MRzk1_rto(p,m)*errorf(MRzk1_rto(p,m)/sqrt(MRzk2_rto(p,m)))
                 + sqrt(MRzk2_rto(p,m)/2/3.1416) * exp(-(MRzk1_rto(p,m)*MRzk1_rto(p,m))/2/MRzk2_rto(p,m)) ;

MRSurplusMar(p,m) = (MRSurplus_rto(p,m) - sum(rto$nrto(p,rto), Surplus(rto,m))) / MRck1(p) ;
MRSurplusMar(p,m) = max(0, MRSurplusMar(p,m)) ;
MRSurplusMar(p,m) = min(1, MRSurplusMar(p,m)) ;
MRSurplusMar(p,m)$(MRSurplusMar(p,m)<.01) = 0 ;

MRSurplusMar_np(n,p,m) = MRSurplusMar(p,m) * Powfrac_upstream(p,n,m) ;
MRSurplusMar_np(n,p,m) = max(0, MRSurplusMar_np(n,p,m)) ;
MRSurplusMar_np(n,p,m) = min(1, MRSurplusMar_np(n,p,m)) ;
MRSurplusMar_np(n,p,m)$(MRSurplusMar_np(n,p,m)<.005) = 0 ;

$endif

*----surplus with MHK Wave----*
* 11-07-12 SMC Added section for MHK wave
* 02-14-13 SMC Added switch for use with MHK OFF
* 03-14-13 PTS/EI Modified must-run level in surplus of alternative systems (with same load).
Mck1(mhkwaveclass,n,p,m)$((lk1(p,m) + Rmhkwk1(mhkwaveclass,n,p,m)) > 0) = ck1(p,m) * (lk1(p,m) / (lk1(p,m) + Rmhkwk1(mhkwaveclass,n,p,m)) - 1) ;
Mck2(mhkwaveclass,n,p,m) = 0 ;
Mck2(mhkwaveclass,n,p,m)$ck1(p,m) = ck2(p,m) * (((Mck1(mhkwaveclass,n,p,m) + ck1(p,m)) / ck1(p,m))**2 - 1) ;

parameter Mzk1_rto(mhkwaveclass,n,rto,m), Mzk2_rto(mhkwaveclass,n,rto,m) ;

Mzk1_rto(mhkwaveclass,n,rto,m) = zk1_rto(rto,m) + sum(p$nrto(p,rto), Mck1(mhkwaveclass,n,p,m) + Rmhkwk1(mhkwaveclass,n,p,m)) ;
Mzk2_rto(mhkwaveclass,n,rto,m) = zk2_rto(rto,m) + sum(p$nrto(p,rto), Mck2(mhkwaveclass,n,p,m)) + Rmhkwk2_rto(mhkwaveclass,n,rto,m) ;



MHKWSurplus(n,rto,mhkwaveclass,m) = 0 ;
MHKWSurplus(n,rto,mhkwaveclass,m)$(Mzk2_rto(mhkwaveclass,n,rto,m)>0 and sum(p$nrto(p,rto), Rmhkwk1(mhkwaveclass,n,p,m)) > 0) = Mzk1_rto(mhkwaveclass,n,rto,m)*errorf(Mzk1_rto(mhkwaveclass,n,rto,m)/sqrt(Mzk2_rto(mhkwaveclass,n,rto,m)))
         + sqrt(Mzk2_rto(mhkwaveclass,n,rto,m)/2/3.1416) * exp(-(Mzk1_rto(mhkwaveclass,n,rto,m)*Mzk1_rto(mhkwaveclass,n,rto,m))/2/Mzk2_rto(mhkwaveclass,n,rto,m)) ;

*needs to be corrected?


* PTS 8/30/13 RTOsurplus: divide RTO surplus among PCAs based on Rupvk1
MHKWSurplusmar(n,mhkwaveclass,m)$WaveCF(n,mhkwaveclass,m) = sum(p$Powfrac_downstream(n,p,m), Rmhkwk1(mhkwaveclass,n,p,m) *
         sum(rto$nrto(p,rto), max(0,MHKWSurplus(n,rto,mhkwaveclass,m) - Surplus(rto,m)) / sum(pp$nrto(pp,rto), Rmhkwk1(mhkwaveclass,n,pp,m)))) / (wincrement*WaveCF(n,mhkwaveclass,m)) ;

MHKWSurplusmar(n,mhkwaveclass,m) = max(0, MHKWSurplusmar(n,mhkwaveclass,m)) ;
MHKWSurplusmar(n,mhkwaveclass,m) = min(1, MHKWSurplusmar(n,mhkwaveclass,m)) ;
MHKWSurplusMar(n,mhkwaveclass,m)$(MHKWSurplusMar(n,mhkwaveclass,m)<.01) = 0 ;

*---------------- End Surplus Calculations ----------------------------*


* Summarize results to annual level
UPVSurplusMar_annual(n)$(sum((m,pvclass), CFUPV(n,m,pvclass) * Hm(m)) > 0) =  sum((m,pvclass), Hm(m) * UPVSurplusmar(n,m,pvclass) * CFUPV(n,m,pvclass)) / sum((m,pvclass), Hm(m) * CFUPV(n,m,pvclass)) ;
DUPVSurplusMar_annual(n)$(sum((m,pvclass), CFDUPV(n,m,pvclass) * Hm(m)) > 0) =  sum((m,pvclass), Hm(m) * DUPVSurplusmar(n,m,pvclass) * CFDUPV(n,m,pvclass)) / sum((m,pvclass), Hm(m) * CFDUPV(n,m,pvclass)) ;
distPVSurplusMar_annual(n)$(sum(m, distPVCF(n,m) * Hm(m)) > 0) =  sum(m, Hm(m) * distPVSurplusmar(n,m) * distPVCF(n,m)) / sum(m, Hm(m) * distPVCF(n,m)) ;
WSurplusmar_annual(windtype,i)$(sum((v,m), CF(i,v,windtype,m) * Hm(m)) > 0) =
         sum((v,m), Hm(m) * WSurplusmar(v,windtype,i,m) * CF(i,v,windtype,m)) / sum((v,m), Hm(m) * CF(i,v,windtype,m)) ;

* 11-07-12 SMC Added MHK Wave parameters
Execute_Unload "./outputs/variabilityFiles/rawvariability_%case%_%next_year%.gdx",

         SurpOld, WSurplusmar, CSPSurplusMar, UPVSurplusMar, DUPVSurplusMar,
         distPVSurplusMar, distPVSurplusMar_annual, UPVSurplusMar_annual, DUPVSurplusMar_annual, WSurplusmar_annual, MHKWSurplusMar, MRSurplusMar
;
