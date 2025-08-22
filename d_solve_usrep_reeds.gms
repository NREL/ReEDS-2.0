*-----------------------------------------
$TITLE	UR INTEGRATION

$log 'Solving ReEDS-USREP case for...'
$log '  USREP Case Name: %case%'
$log '  ReEDS Case Name: %case%'
$log '  Current Year: %cur_year%'


$setglobal udb %ru_udb%

*parameter loadcheck2 ; 

*-----------------------------------------

* switches useful for testing infeasibilities
$ontext
Sw_StateRPS = 0 ; 
Sw_StateCap = 0 ;
Sw_RGGI = 0 ;
Sw_CSAPR = 0 ;
$offtext

*	System-specific directory seperator
$set ds %system.dirsep% 

*	Working directory
$setglobal wd %gams.workdir%

* $if not set udir	$setglobal udir usrep
$if not set udir	$setglobal udir usrep_windc

*	USREP directory
$set uwd %wd%%udir%/

*   Iteration counter
$if not set iter	$setglobal iter   0
$ife %iter%>0		$eval   iter0     %iter%-1

$eval iter00 %iter%-2

*	USREP directory
$set loadyr %prev_year%

*	Model time dimension:
$if %ru_udb% == implan	$setglobal startyr_USREP 2006
$if %ru_udb% == windc	$setglobal startyr_USREP 2017

$ife %cur_year%=2010	$if %ru_udb% == implan	$set readyr 2006
$ife %cur_year%=2020	$if %ru_udb% == windc	$set readyr 2017

$ife %cur_year%>2010	$if %ru_udb% == implan	$set readyr %loadyr% 
$ife %cur_year%>2020	$if %ru_udb% == windc	$set readyr %loadyr% 

$show


$onmulti

alias (usrep_r,usrep_rr);

parameter 
	chkdev		Check deviation
	eledtrd		Domestic electricity trade (TWh)
	eleftrd		Foreign electricity trade (TWh)
	iterlog		Iteration log
	ur_         USREP solution from previous iteration
	ur_prev     USREP solution from twice-previous iteration used for inter-iteration averaging
	ur_ref      USREP solution for reference case
	urbau
	ur0
	baseprc0
	baseload0
;
$offmulti

* restore benchmark multipliers for computing quantity at benchmark price in reeds_slide parameter
* non-itc adjusted multiplier needed when separating itc in pass to slide
cost_cap_fin_mult0(i,r,t)$tmodel(t) = cost_cap_fin_mult_noITC(i,r,t);
rsc_fin_mult0(i,r,t)$tmodel(t) = rsc_fin_mult_noITC(i,r,t);
rsc_fin_mult00(i,r,t)$tmodel(t) = rsc_fin_mult(i,r,t);



*========================================
*	For the periods before USREP starts, 
*   ReEDS reads SEDS historical data
*========================================

$if not set startyr_USREP $setglobal startyr_USREP 2017

$ife %cur_year%>%startyr_USREP%	$goto endReEDSstandalone

$ifthene.rstandalone %ru_runbenchmark%=1

ur_(usrep_r,"ele","TWh","%cur_year%") = 1e-3 * sedselecon(usrep_r,"%cur_year%");
ur_(usrep_r,fe,"dolperMMBtu","%cur_year%") = deflator("%cur_year%")*sedsfuelprice(usrep_r,fe,"%cur_year%");
ur_(usrep_r,"gas","Quad","%cur_year%") = 1e-6 * sedselefuelcon(usrep_r,"gas","%cur_year%");
ur_(usrep_r,"cap","PrcIdx","%cur_year%") = 1;
ur_(usrep_r,"lab","PrcIdx","%cur_year%") = 1;
ur_(usrep_r,"co2prc","dolpertco2","%cur_year%") = 0;

$else.rstandalone

$gdxin link%ds%ru0.gdx
$loadr ur0=ur_ baseprc0=baseprc baseload0=baseload
$gdxin

$if not set startyr_USREP $setglobal startyr_USREP 2017

ur_(usrep_r,"ele","TWh","%cur_year%") = 1e-6*baseload0(usrep_r,"%cur_year%");
ur_(usrep_r,"ele","dolperMWh","%cur_year%") = baseprc0(usrep_r,"%cur_year%") / deflator("%startyr_USREP%");
ur_(usrep_r,fe,"dolperMMBtu","%cur_year%") = ur0(usrep_r,fe,"dolperMMBtu","%cur_year%");
ur_(usrep_r,"cap","PrcIdx","%cur_year%") = ur0(usrep_r,"cap","PrcIdx","%cur_year%");
ur_(usrep_r,"lab","PrcIdx","%cur_year%") = ur0(usrep_r,"lab","PrcIdx","%cur_year%");
ur_(usrep_r,"delas-pele","delas","%cur_year%") = -0.35;
ur_(usrep_r,"delas-pcarb","delas","%cur_year%") = -0.1;
ur_(usrep_r,"co2prc","dolpertco2","%cur_year%") = 0;
ur_(usrep_r,"emisnonele","MMTCO2","%cur_year%") = 0;
ur_(usrep_r,"emis","MMTCO2","%cur_year%")$ufeas(usrep_r) = 0;
ur_(usrep_r,"DAC","MMTCO2","%cur_year%") = 0;

$endif.rstandalone

$goto endur
$label endReEDSstandalone

*=========================================
* -- end loading of historical data --
*=========================================



* if this is the inital iteration, skip loading in of 
* previous solution from USREP
$ife %iter%=0		$goto urit0

$gdxin link%ds%usrep_out%ds%%ru_case%_%cur_year%_it%iter0%.gdx
$loadr ur_=ur
$gdxin


* if you have solved more than two iterations
$ife %iter%<2 $goto nosmooth

$gdxin link%ds%usrep_out%ds%%ru_case%_%cur_year%_it%iter00%.gdx
$loadr ur_prev=ur
$gdxin

* make ur_ the weighted average of the previous and twice-previous values
ur_(usrep_r,"ele","dolperMWh","%cur_year%") = Sw_RU_SmoothFactor * ur_(usrep_r,"ele","dolperMWh","%cur_year%") + (1-Sw_RU_SmoothFactor) * ur_prev(usrep_r,"ele","dolperMWh","%cur_year%") ;
ur_(usrep_r,"ELE","TWh","%cur_year%") = Sw_RU_SmoothFactor * ur_(usrep_r,"ELE","TWh","%cur_year%") + (1-Sw_RU_SmoothFactor) * ur_prev(usrep_r,"ELE","TWh","%cur_year%") ;
ur_(usrep_r,"cap","PrcIdx","%cur_year%") = Sw_RU_SmoothFactor * ur_(usrep_r,"cap","PrcIdx","%cur_year%") + (1-Sw_RU_SmoothFactor) * ur_prev(usrep_r,"cap","PrcIdx","%cur_year%") ;
ur_(usrep_r,"lab","PrcIdx","%cur_year%") = Sw_RU_SmoothFactor * ur_(usrep_r,"lab","PrcIdx","%cur_year%") + (1-Sw_RU_SmoothFactor) * ur_prev(usrep_r,"lab","PrcIdx","%cur_year%") ;
ur_(usrep_r,"GAS","dolperMMBtu","%cur_year%") = Sw_RU_SmoothFactor * ur_(usrep_r,"GAS","dolperMMBtu","%cur_year%") + (1-Sw_RU_SmoothFactor) * ur_prev(usrep_r,"GAS","dolperMMBtu","%cur_year%") ;
ur_(usrep_r,"COL","dolperMMBtu","%cur_year%") = Sw_RU_SmoothFactor * ur_(usrep_r,"COL","dolperMMBtu","%cur_year%") + (1-Sw_RU_SmoothFactor) * ur_prev(usrep_r,"COL","dolperMMBtu","%cur_year%") ;

ur_(usrep_r,"co2prc0","dolpertco2","%cur_year%") = ur_(usrep_r,"co2prc","dolpertCO2","%cur_year%");
ur_("USA","co2prc0","dolpertco2","%cur_year%") = ur_("USA","co2prc","dolpertCO2","%cur_year%");

ur_(usrep_r,"co2prc","dolpertco2","%cur_year%") = Sw_RU_SmoothFactor * ur_(usrep_r,"co2prc","dolpertCO2","%cur_year%") + (1-Sw_RU_SmoothFactor) * ur_prev(usrep_r,"co2prc","dolpertCO2","%cur_year%");
ur_("USA","co2prc","dolpertco2","%cur_year%") = Sw_RU_SmoothFactor * ur_("USA","co2prc","dolpertCO2","%cur_year%") + (1-Sw_RU_SmoothFactor) * ur_prev("USA","co2prc","dolpertCO2","%cur_year%");


display ur_, ur_prev ;

$label nosmooth

$goto endur

$label urit0


* if we are solving the benchmark case..
$ifthene.benchmark %ru_runbenchmark%=1

$gdxin link%ds%usrep_out%ds%%ru_case%_%readyr%.gdx
* this is no longer a reeds standalone case, even with a single iteration because it loads usrep readyr
$loadr ur_=ur
$gdxin

* for zeroth iteration, assume same load as reeds
ur_(usrep_r,"ele","TWh","%cur_year%") = 
	ur_(usrep_r,"ele","TWh","%readyr%")/sum(usrep_r.local,ur_(usrep_r,"ele","TWh","%readyr%")) * AEOeleload("USA","%cur_year%");
* previous version...
*	sum((r,h)$r_u(r,usrep_r), hours(h) * (load_exog_static(r,h,"%cur_year%") + can_exports_h(r,h,"%cur_year%")$[Sw_Canada=1])) ; 

;

* take previous solves solution values to start
ur_(usrep_r,"cap","PrcIdx","%cur_year%") = ur_(usrep_r,"cap","PrcIdx","%readyr%");
ur_(usrep_r,"lab","PrcIdx","%cur_year%") = ur_(usrep_r,"lab","PrcIdx","%readyr%");
ur_(usrep_r,"GAS","dolperMMBtu","%cur_year%") = ur_(usrep_r,"GAS","dolperMMBtu","%readyr%");
ur_(usrep_r,"COL","dolperMMBtu","%cur_year%") = ur_(usrep_r,"COL","dolperMMBtu","%readyr%");
ur_(usrep_r,"co2prc","dolpertCO2","%cur_year%") = 0;

$else.benchmark


*	Read the reference case solution from ReEDS
$gdxin link%ds%ru0.gdx
$loadr ur0=ur_ baseprc0=baseprc baseload0=baseload
$gdxin

*	It0 in scenario replicates the Ref solution in ReEDS
*	Replace baseprc and baseload with those used in the last ReEDS iter in Reference 
ur_(usrep_r,"cap","PrcIdx","%cur_year%") = ur0(usrep_r,"cap","PrcIdx","%cur_year%");
ur_(usrep_r,"lab","PrcIdx","%cur_year%") = ur0(usrep_r,"lab","PrcIdx","%cur_year%");
ur_(usrep_r,"GAS","dolperMMBtu","%cur_year%") = ur0(usrep_r,"GAS","dolperMMBtu","%cur_year%");
ur_(usrep_r,"COL","dolperMMBtu","%cur_year%") = ur0(usrep_r,"COL","dolperMMBtu","%cur_year%");

ur_(usrep_r,"delas-pele","delas","%cur_year%") = -0.35;
ur_(usrep_r,"ele","dolperMWh","%cur_year%")    = baseprc0(usrep_r,"%cur_year%")/cvt;
ur_(usrep_r,"ele","TWh","%cur_year%")          = 1e-6*baseload0(usrep_r,"%cur_year%");

ur_(usrep_r,"delas-pcarb","delas","%cur_year%") = -0.1;
ur_(usrep_r,"emisnonele","MMTCO2","%cur_year%") = ur0(usrep_r,"emisnonele","MMTCO2","%cur_year%");

$endif.benchmark

$label endur

display ur_;

*	Electricity load by region and time slice
load_exog_static(r,h,t)$[tmodel(t)]
	= 1e6*sum(usrep_r,ref_qprop_usrep(r,usrep_r,t)*ur_(usrep_r,"ele","TWh",t))
	* load_exog_static(r,h,t) / sum(h.local, hours(h)*load_exog_static(r,h,t));	

*	Capital costs
*	might need to be modified in the objective function due to cost_cap parameter not indexed by "r"
cost_cap_fin_mult(i,r,t)$[tmodel(t)]
	= cost_cap_fin_mult0(i,r,t) 
	* sum(usrep_r$r_u(r,usrep_r),ur_(usrep_r,"cap","PrcIdx","%cur_year%"));

***RU***
*	Spur line costs
rsc_fin_mult(i,r,t)$[tmodel(t)] =
	rsc_fin_mult(i,r,t)
	* sum(usrep_r$r_u(r,usrep_r),ur_(usrep_r,"cap","PrcIdx","%cur_year%"));

*	Operating Costs
*	VOM costs
cost_vom(i,v,r,t)$[tmodel(t)$valcap(i,v,r,t)] 
	= cost_vom0(i,v,r,t) 
	* sum(usrep_r$r_u(r,usrep_r),ur_(usrep_r,"lab","PrcIdx","%cur_year%"));

cost_fom(i,v,r,t)$[tmodel(t)$valcap(i,v,r,t)] 
	= cost_fom0(i,v,r,t) 
	* sum(usrep_r$r_u(r,usrep_r),ur_(usrep_r,"lab","PrcIdx","%cur_year%"));

*	Fuel Prices / Costs
*	Rolling average fuel prices

$ifthene.notiter %cur_year%<=2020
fuel_price(i,r,t)$[tmodel(t)$coal(i)] = fuel_price0(i,r,t) ;
fuel_price(i,r,t)$[tmodel(t)$gas(i)] = fuel_price0(i,r,t) ;
$endif.notiter

$ifthene.startiter %cur_year%>2020

fuel_price(i,r,t)$[gas(i)$tmodel(t)] 
	= deflator("2017") * cvt * sum(usrep_r$r_u(r,usrep_r),ur_(usrep_r,"GAS","dolperMMBtu","%cur_year%"));

fuel_price(i,r,t)$[(coal(i) or cofire(i))$tmodel(t)]
	= deflator("2017") * cvt * sum(usrep_r$r_u(r,usrep_r),ur_(usrep_r,"COL","dolperMMBtu","%cur_year%"));

* if no values reported from usrep, default to reeds fuel prices
fuel_price(i,r,t)$[(not fuel_price(i,r,t))$fuel_price0(i,r,t)] = fuel_price0(i,r,t) ; 

$endif.startiter

* load in carbon price/tax
** If iteration 0 then use the exogenous starting point
*!!!! condition this on whether it is a ctax case...
$ontext
$ifthene.ctax %iter%=0
emit_tax("co2",r,t)$[tmodel(t)] = 0;
ur_("USA","co2prc","dolpertCO2","%cur_year%") = co2_tax_ru_init("%cur_year%");
emit_tax("co2",r,t)$[tmodel(t)] = co2_tax_ru_init(t)*emit_scale("CO2");
** else use the smoothed USREP price
$else.ctax
* Carbon tax
* 1.102 converts from tons to MT
emit_tax("co2",r,t)$[tmodel(t)]
*	= deflator("2017") * cvt * sum{usrep_r$r_u(r,usrep_r),ur_(usrep_r,"co2prc","dolpertCO2","%cur_year%")};
	= deflator("2017") * cvt * ur_("USA","co2prc","dolpertCO2","%cur_year%");
display emit_tax, ur_, emit_scale;
* Scale for ReEDS model
emit_tax("co2",r,t)$[tmodel(t)] = emit_tax("co2",r,t) * emit_scale("CO2");
$endif.ctax



** Hack - If 2030 then force in a fixed carbon price for all iterations in ReEDS
$ifthene.ctax %cur_year%=2030
ur_("USA","co2prc","dolpertCO2","%cur_year%") = 5;
emit_tax("co2",r,t)$[tmodel(t)] = ur_("USA","co2prc","dolpertCO2","%cur_year%")*emit_scale("CO2");
$endif.ctax
$offtext


$label skiploadur
$ontext

gasquant_usrep(usrep_r,gb,t)$[tmodel(t)] 
	= ur_(usrep_r,"GAS","MMBtu",t) 
	* (1+(ord(gb)-(smax(gbb,ord(gbb))/2 + 0.5))*0.1);

gasprice_usrep(usrep_r,gb,t)$[ur_(usrep_r,"GAS","MMBtu",t)$tmodel(t)]
	= cvt * ur_(usrep_r,"GAS","dolperMMBtu",t)
               * (
* numerator is the quantity in the bin
* [plus] all natural gas usage
* [minus] gas usage in the ele sector
                gasquant_usrep(usrep_r,gb,t) / (ur_(usrep_r,"GAS","MMBtu",t))
                ) ** (1/gas_elasticity);
$offtext

*=========================================
*	LOAD DEMAND REPRESENTATION
*=========================================

*	SwElas=1 (piecewise linear) 
*	SwElas=2 (quadratic formulation) 
*   for LP only, switch to swelas=2 after LP and before QP
SwElas = 0 ; 

* switch off to ensure no issues with eq_loadcon
Sw_EFS_Flex = 0;
Sw_Prod = 0 ;
Sw_EVMC = 0 ;
Sw_EFS_flex = 0 ; 
evmc_shape(i) = no ;
Sw_H2_CompressorLoad = 0 ;

*!!!! this relates to bug for lfill-gas
firstyear_pcat(pcat)$[firstyear_pcat(pcat)>2020] = 2020;

*	Include case file from usrep
$batinclude %uwd%%ds%case%ds%%ru_case%.cas ReEDScase

$ife %ru_runbenchmark%=0	$goto solveQCP

ReEDSmodel.optfile = 1;
ReEDSmodel.solprint = 0; 
ReEDSmodel.reslim = 50000; 
ReEDSmodel.solvelink = 5; 
ReEDSmodel.holdfixed = 0; 
ReEDSmodel.TryLinear = 1;
ReEDSmodel.scaleopt = 1;

*share of regions and hours contribution to annual USREP_R load
loadrh(r,h,t)$tmodel(t) = 
	(load_exog_static(r,h,t) + can_exports_h(r,h,t)$[Sw_Canada = 1])
	/ sum((rr,hh)$[sum(usrep_r$[r_u(rr,usrep_r)$r_u(r,usrep_r)],1)$hours(hh)], 
		hours(hh) * (load_exog_static(rr,hh,t) + can_exports_h(rr,hh,t)$[Sw_Canada = 1]) )
;

solve ReEDSmodel minimizing z using LP;

*loadcheck2(usrep_r,t,"%iter%",'first_unfiltered')$tmodel(t) = sum((r,h)$r_u(r,usrep_r), load.l(r,h,t) * hours(h)) ; 
*loadcheck2(usrep_r,t,"%iter%",'first_filtered')$tmodel(t) = sum((r,h)$[r_u(r,usrep_r)$h_rep(h)], load.l(r,h,t) * hours(h)) ; 

$batinclude d2_elecost LP

baseprc(usrep_r,t)$(sum(r,r_u(r,usrep_r))$tmodel(t)) = 
	round(elecost(usrep_r,t,'total_unf'), 4);

baseload(usrep_r,t)$(sum(r,r_u(r,usrep_r))$tmodel(t)) = 
	round(sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.L(r,h,t) ), 4);


display "LP-elecost", elecost, loadu.l;
display "%cur_year% - LP - %iter%", baseprc, baseload, eledelas;

chkdev(t,"it%iter%",usrep_r,"LP")$tmodel(t) = LOADU.l(usrep_r,t);

$label solveQCP

* enable qp switch in eq_loadcon
SwElas = 1;
* LOAD.L(r,h,t) = load_exog_static(r,h,t) + can_exports_h(r,h,t)$[Sw_Canada = 1];
* LOADU.L(usrep_r,t) = sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.L(r,h,t));

cappol(e,"USA") = capt(e,"USA","%cur_year%");
emiscap(e,"USA")$cappol(e,"USA") = 1e6*emiscapt(e,"USA","%cur_year%"); 

* emit_tax("co2",r,t)$[tmodel(t)] = 0$cappol("CO2","USA");

display cappol, emiscap, emit_tax;

* note tmodel(t) is especially important for bounds in these equations as 
* the load_exog_static parameters have not been computed until the call
* to d_solveoneyear.gms for that specific year - so it'll fix them at zero
LOAD.UP(r,h,t)$tmodel(t) = 2   * (load_exog_static(r,h,t) + can_exports_h(r,h,t)$[Sw_Canada = 1]);
LOAD.LO(r,h,t)$tmodel(t) = 0.5 * (load_exog_static(r,h,t) + can_exports_h(r,h,t)$[Sw_Canada = 1]);
LOADU.UP(usrep_r,t)$tmodel(t) = 2 * sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.L(r,h,t)) ;
LOADU.LO(usrep_r,t)$tmodel(t) = 0.5 * sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.L(r,h,t)) ; 

$ifthene.QP %ru_runbenchmark%=1

LOADU.L(usrep_r,t)$tmodel(t) = sum((r,h)$(r_u(r,usrep_r)), hours(h) * LOAD.L(r,h,t));

$else.QP

loop(usrep_r$sum(r,r_u(r,usrep_r)),

	baseprc(usrep_r,"%cur_year%") = cvt*ur_(usrep_r,"ele","dolperMWh","%cur_year%");
	baseload(usrep_r,"%cur_year%") = 1e6*ur_(usrep_r,"ele","TWh","%cur_year%");

	eledelas(usrep_r)$(ur_(usrep_r,"delas-pele","delas","%cur_year%") lt 0)
		= min(0.5, - ur_(usrep_r,"delas-pele","delas","%cur_year%"));

	eledelas(usrep_r)$(ur_(usrep_r,"delas-pele","delas","%cur_year%") ge 0) 
		= min(0.05, ur_(usrep_r,"delas-pele","delas","%cur_year%"));
*	eledelas(usrep_r) = 0.15;

	baseemisprc("CO2",usrep_r,"%cur_year%") = max(2, cvt*ur_(usrep_r,"co2prc","dolpertCO2","%cur_year%"));
	baseemisnonele("CO2",usrep_r,"%cur_year%") = 1e6*ur_(usrep_r,"emisnonele","MMTCO2","%cur_year%");

	delasemis("CO2",usrep_r)$(ur_(usrep_r,"delas-pcarb","delas","%cur_year%") lt 0) = min(0.1, - ur_(usrep_r,"delas-pcarb","delas","%cur_year%")/2);
	delasemis("CO2",usrep_r)$(ur_(usrep_r,"delas-pcarb","delas","%cur_year%") ge 0) = min(0.05, ur_(usrep_r,"delas-pcarb","delas","%cur_year%")/2);

);

display "%cur_year% - %iter%", baseprc, baseload, eledelas;

LOAD.L(r,h,t)$tmodel(t) = sum(usrep_r,baseload(usrep_r,t))*loadrh(r,h,t);
LOADU.L(usrep_r,t)$tmodel(t) = baseload(usrep_r,t);

$ifthene.emitnonele %iter%=0

EMITNonELE.fx(e,usrep_r,t)$tmodel(t)
	= min(1e6 * 0.9 * ur_(usrep_r,"emisnonele","MMTCO2",t),
		(1e6*sum(usrep_r.local,cquota(usrep_r,t)) 
* $ife %cur_year%>2010	- 0.6*sum((r,tt)$tprev(t,tt),EMIT.L("CO2",r,tt)) * emit_scale("CO2")
			- 1e6*sum(usrep_r.local$(not ufeas(usrep_r)), ur_(usrep_r,"emis","MMTCO2",t))
		) * ur_(usrep_r,"emisnonele","MMTCO2",t)/sum(usrep_r.local,ur_(usrep_r,"emisnonele","MMTCO2",t))
	)$cappol(e,"USA");


$ife %cur_year%>2025  EMITNonELE.fx(e,usrep_r,t)$tmodel(t) = (1e6 * cquota(usrep_r,t) - 0.8 * sum((tt,r_u(r,usrep_r))$tprev(t,tt), EMIT.l(e,r,tt) * emit_scale("CO2")) )$cappol(e,"USA");

$else.emitnonele
EMITNonELE.up(e,usrep_r,t)$tmodel(t) = 2 * baseemisnonele(e,usrep_r,t)$cappol(e,"USA");
EMITNonELE.lo(e,usrep_r,t)$tmodel(t) = 0.1 * baseemisnonele(e,usrep_r,t)$cappol(e,"USA");
EMITNonELE.l(e,usrep_r,t)$tmodel(t) = baseemisnonele(e,usrep_r,t)$cappol(e,"USA");

$endif.emitnonele

baseemisprc(e,usrep_r,t)$(not ufeas(usrep_r)) = 0;
* ur_("emis") will be zero in any case except the benchmark run, where it doesn't matter for this
* issues with tracking the time step or failure to load something and store it
EMITNonELE.fx(e,usrep_r,t)$(tmodel(t)$(not ufeas(usrep_r))) = 1e6*ur_(usrep_r,"emis","MMTCO2","%cur_year%");

$endif.QP

display "QP parameters", baseprc, baseload, eledelas, loadu.l, EMITNonELE.L,
	baseemisprc, baseemisnonele, delasemis, cappol, emiscap, emit_tax;

* Adjust emissions cap to account for DAC negative emissions
emiscap(e,"USA")$cappol(e,"USA") 
			= 1e6 * emiscapt(e,"USA","%cur_year%")
$ife %ru_runbenchmark%=0	- 1e6 * sum(usrep_r,ur_(usrep_r,"DAC","MMTCO2","%cur_year%"))
;

display "CHECK CARBON CAP2",  emiscap, emiscapt; 

option QCP = CPLEX;
*option QCP = examiner;


ReEDSmodelqcp.optfile = 2;
ReEDSmodelqcp.solprint = 0; 
ReEDSmodelqcp.reslim = 50000; 
*ReEDSmodelqcp.solvelink = 5; 
ReEDSmodelqcp.holdfixed = 0; 
ReEDSmodelqcp.TryLinear = 1;
*ReEDSmodelqcp.scaleopt = 1;

d_quant(dbin,usrep_r,t)$tmodel(t) = baseload(usrep_r,t) * dbin_width ;

d_price(dbin,usrep_r,t)$[tmodel(t)$baseload(usrep_r,t)] = 
	round(baseprc(usrep_r,t) * (sum(ddbin$[ord(ddbin)<=ord(dbin)], d_quant(dbin,usrep_r,t) ) 
		/ baseload(usrep_r,t)) ** (-1 * eledelas(usrep_r) ), 4);

d_quant_emit(dbin,e,usrep_r,t)$tmodel(t) = baseemisnonele(e,usrep_r,t) * dbin_width ;

d_price_emit(dbin,e,usrep_r,t)$[tmodel(t)$baseemisnonele(e,usrep_r,t)] = 
	round(baseemisprc(e,usrep_r,t) * (sum(ddbin$[ord(ddbin)<=ord(dbin)], d_quant_emit(dbin,e,usrep_r,t) ) 
		/ baseemisnonele(e,usrep_r,t)) ** (-1 * delasemis(e,usrep_r) ), 4);

EMITNonELE.fx(e,usrep_r,t)$[tmodel(t)$cappol(e,"USA")] = baseemisnonele(e,usrep_r,t);

swelas = 1 ;


solve ReEDSmodel minimizing z using LP ;

*loadcheck2(usrep_r,t,"%iter%",'second_unfiltered')$tmodel(t) = sum((r,h)$r_u(r,usrep_r), load.l(r,h,t) * hours(h)) ; 
*loadcheck2(usrep_r,t,"%iter%",'second_filtered')$tmodel(t) = sum((r,h)$[r_u(r,usrep_r)$h_rep(h)], load.l(r,h,t) * hours(h)) ; 



$batinclude d2_elecost QP
display "QP-elecost", elecost, loadu.l;
display "%cur_year% - QP - %iter%", baseprc, baseload, eledelas;

chkdev(t,"it%iter%",usrep_r,"QP")$tmodel(t) = LOADU.l(usrep_r,t);
*$ife %ru_runbenchmark%=1	chkdev(t,"it%iter%",usrep_r,"dev") pct(chkdev(t,"it%iter%",usrep_r,"LP"),chkdev(t,"it%iter%",usrep_r,"QP"));

option chkdev:3:3:1;
display chkdev;

*==========================================
*	UPDATE ELECTRICITY FEEDBACK
*==========================================

ru(usrep_r,"ele","TWh",t)$tmodel(t)
	= 1e-6 * (
	  (sum((h,r)$r_u(r,usrep_r),hours(h) * load.l(r,h,t)))$[SwElas = 0]
    + (sum(dbin,LOAD_BIN.l(dbin,usrep_r,t)))$[SwElas = 1]
	+ (LOADU.l(usrep_r,t))$[SwElas = 2] 
	);



*2006$(implan)/2017$(windc)
ru(usrep_r,"ele","dolperMWh",t)$(sum(r,r_u(r,usrep_r))$tmodel(t))
	= max(5, (1/cvt)*elecost(usrep_r,t,"energy") );

* Bilateral domestic trade (TWh)
eledtrd(usrep_r,usrep_rr,"TWh",t)$(tmodel(t)$(not sameas(usrep_r,usrep_rr)))
	= 1e-6 * sum((h,trtype,r,rr)$(routes(rr,r,trtype,t)
		$r_u(r,usrep_r)$r_u(rr,usrep_rr)), 
		hours(h) * FLOW.l(r,rr,h,t,trtype) );

* Currently there is no foreign trade as rfeas is defined by U.S. BA only
loop(country$(not sameas(country,"USA")),
eleftrd(country,usrep_r,"TWh",t)$tmodel(t)
	= 1e-6 * sum((h,trtype,r,rr)$[routes(rr,r,trtype,t)
		$r_u(rr,usrep_r)$r_country(r,country)], 
		hours(h) * FLOW.l(r,rr,h,t,trtype) );

eleftrd(usrep_r,country,"TWh",t)$tmodel(t)
	= 1e-6 * sum((h,trtype,r,rr)$[routes(rr,r,trtype,t)
		$r_u(r,usrep_r)$r_country(rr,country)], 
		hours(h) * FLOW.l(r,rr,h,t,trtype) );
);

* volume of trade (TWh)
ru(usrep_r,"dexp","TWh",t)$tmodel(t) = sum(usrep_rr,eledtrd(usrep_r,usrep_rr,"TWh",t));	
ru(usrep_r,"dimp","TWh",t)$tmodel(t) = sum(usrep_rr,eledtrd(usrep_rr,usrep_r,"TWh",t));
ru(usrep_r,"fexp","TWh",t)$tmodel(t) = sum(country,eleftrd(usrep_r,country,"TWh",t));	
ru(usrep_r,"fimp","TWh",t)$tmodel(t) = sum(country,eleftrd(country,usrep_r,"TWh",t));

* value of trade (Billion$)
ru(usrep_r,"dexp","Bil$",t)$tmodel(t)
	= 1e-3 * sum(usrep_rr,ru(usrep_r,"ele","dolperMWh",t)*eledtrd(usrep_r,usrep_rr,"TWh",t));	
ru(usrep_r,"dimp","Bil$",t)$tmodel(t)
	= 1e-3 * sum(usrep_rr,ru(usrep_rr,"ele","dolperMWh",t)*eledtrd(usrep_rr,usrep_r,"TWh",t));
ru(usrep_r,"fexp","Bil$",t)$tmodel(t)
	= 1e-3 * sum(country,ru(usrep_r,"ele","dolperMWh",t)*eledtrd(usrep_r,country,"TWh",t));	
*!! lacking info on the exporter's eleprc, assume foreign imports at the domestic price
ru(usrep_r,"fimp","Bil$",t)$tmodel(t)
	= 1e-3 * sum(country,ru(usrep_r,"ele","dolperMWh",t)*eledtrd(country,usrep_r,"TWh",t));


ru(usrep_r,"gas","quads",t)$tmodel(t) 
	= sum{(i,v,r,h)$[r_u(r,usrep_r)$valgen(i,v,r,t)$gas(i)$heat_rate(i,v,r,t)
		$(not sameas("biopower",i))$(not cofire(i))],
	  hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t) } / 1e9;

ru(usrep_r,"col","quads",t)$tmodel(t)
	= (sum{(i,v,r,h)$[r_u(r,usrep_r)$valgen(i,v,r,t)$coal(i)$heat_rate(i,v,r,t)
		$(not sameas("biopower",i))$(not cofire(i))],
	  hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t) }
	+ sum{(i,v,r,h)$[r_u(r,usrep_r)$valgen(i,v,r,t)$cofire(i)$heat_rate(i,v,r,t)
		$(not sameas("biopower",i))],
	  (1-bio_cofire_perc) * hours(h) * heat_rate(i,v,r,t) * GEN.l(i,v,r,h,t) }
	  ) / 1e9;

ru(usrep_r,"ql","dollars",t)$tmodel(t)
	= (1/cvt) * ( 
	  sum{(i,v,r,h)$[r_u(r,usrep_r)$valgen(i,v,r,t)$cost_vom(i,v,r,t)],
		hours(h) * cost_vom0(i,v,r,t) * GEN.l(i,v,r,h,t) }
* fixed O&M costs
	+ sum{(i,v,r)$[r_u(r,usrep_r)$valcap(i,v,r,t)],cost_fom0(i,v,r,t) * CAP.l(i,v,r,t) }

	+ sum{(i,v,r,h,ortype)$[r_u(r,usrep_r)$valgen(i,v,r,t)
		$cost_opres(i,ortype,t)$sameas(ortype,"reg")],
	  hours(h) * cost_opres(i,ortype,t) * OpRes.l(ortype,i,v,r,h,t) }
	  );

* production tax credits and 45Q combined
ru(usrep_r,"ptc","dollars",t)$tmodel(t) =
         (1/cvt)*(
* --- Tax credit for CO2 stored ---
             - sum{(i,v,r,h)$[valgen(i,v,r,t)$co2_captured_incentive(i,v,r,t)$r_u(r,usrep_r)],
                             co2_captured_incentive(i,v,r,t) * hours(h) * capture_rate("CO2",i,v,r,t) * GEN.L(i,v,r,h,t)}

* --- Tax credit for CO2 stored for DAC ---
             - sum{(p,i,v,r,h)$[dac(i)$valcap(i,v,r,t)$i_p(i,p)$r_u(r,usrep_r)],
                             co2_captured_incentive(i,v,r,t) * hours(h) * PRODUCE.L(p,i,v,r,h,t)}

* --- PTC value ---
             - sum{(i,v,r,h)$[valgen(i,v,r,t)$ptc_value_scaled(i,v,t)$r_u(r,usrep_r)],
                             hours(h) * ptc_value_scaled(i,v,t) * tc_phaseout_mult(i,v,t) * GEN.L(i,v,r,h,t) }
* end multiplier
         )
;

* investement tax credit -- unamortized
* since we don't multiply by slide_reeds(cap) index for no_itc and out, we can still account for the itc here in this way
*investment costs (without the subtraction of any ITC/PTC value)
ru(usrep_r,"inv_investment_capacity_costs_noITC","dollars",t)$tmodel(t) =
              (1/cvt)*pvf_capital(t) * ((1/5)$[(t.val > 2010)]+1$[(t.val eq 2010)]) *(
               sum{(i,v,r)$[valinv(i,v,r,t)$r_u(r,usrep_r)],
                   INV.l(i,v,r,t) * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t) ) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
              + sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$sccapcosttech(i)$r_u(r,usrep_r)],
                   INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult_noITC(i,r,t) }
*plus cost of upgrades
              + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades$r_u(r,usrep_r)],
                   cost_upgrade(i,v,r,t) * cost_cap_fin_mult_noITC(i,r,t) * UPGRADES.l(i,v,r,t) }
*cost of capacity upsizing
              + sum{(i,v,r,rscbin)$[allow_cap_up(i,v,r,rscbin,t)$r_u(r,usrep_r)],
                   cost_cap_fin_mult_noITC(i,r,t) * INV_CAP_UP.l(i,v,r,rscbin,t) * cost_cap_up(i,v,r,rscbin,t) }
*cost of energy upsizing
              + sum{(i,v,r,rscbin)$[allow_ener_up(i,v,r,rscbin,t)$r_u(r,usrep_r)],
                   cost_cap_fin_mult_noITC(i,r,t) * INV_ENER_UP.l(i,v,r,rscbin,t) * cost_ener_up(i,v,r,rscbin,t) }
              )
;

ru(usrep_r,"inv_investment_capacity_costs_out","dollars",t)$tmodel(t) =
              (1/cvt)*pvf_capital(t) * ((1/5)$[(t.val > 2010)]+1$[(t.val eq 2010)]) *(
               sum{(i,v,r)$[valinv(i,v,r,t)$r_u(r,usrep_r)],
                   INV.l(i,v,r,t) * (cost_cap_fin_mult_out(i,r,t) * cost_cap(i,t) ) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
              + sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$sccapcosttech(i)$r_u(r,usrep_r)],
                   INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult00(i,r,t) }
*plus cost of upgrades
              + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades$r_u(r,usrep_r)],
                   cost_upgrade(i,v,r,t) * cost_cap_fin_mult_out(i,r,t) * UPGRADES.l(i,v,r,t) }
*cost of capacity upsizing
              + sum{(i,v,r,rscbin)$[allow_cap_up(i,v,r,rscbin,t)$r_u(r,usrep_r)],
                   cost_cap_fin_mult_out(i,r,t) * INV_CAP_UP.l(i,v,r,rscbin,t) * cost_cap_up(i,v,r,rscbin,t) }
*cost of energy upsizing
              + sum{(i,v,r,rscbin)$[allow_ener_up(i,v,r,rscbin,t)$r_u(r,usrep_r)],
                   cost_cap_fin_mult_out(i,r,t) * INV_ENER_UP.l(i,v,r,rscbin,t) * cost_ener_up(i,v,r,rscbin,t) }
              )
;

ru(usrep_r,"itc","dollars",t)$tmodel(t) =
	ru(usrep_r,"inv_investment_capacity_costs_out","dollars",t)
*minus capacity costs without ITC
	- ru(usrep_r,"inv_investment_capacity_costs_noITC","dollars",t)
;


*$ontext
* investment costs from ReEDS appear are the overnight capital cost in $/MW for the year "t"
* This is multiplied by INV.l in the objective function
* INV.l is the full capacity added since the last "modeled" year
* So if the time step is 5 years, and the current year is 2015, INV.l is the new capacity added since 2010
* Therefore, for an annualized capital demand, we divide by the time step... 5 years
ru(usrep_r,"qk_newinv","dollars",t)$tmodel(t) 
	= pvf_capital(t) * (1/cvt) * ((1/5)$[(t.val > 2010)]+1$[(t.val eq 2010)]) * ( 
* investment costs
	sum{(i,v,r)$[r_u(r,usrep_r)$valinv(i,v,r,t)],
		INV.l(i,v,r,t) * cost_cap_fin_mult0(i,r,t) * cost_cap(i,t)}

* costs of rsc investment ---MAX TOCHECK---
* Note that cost_cap for hydro techs are zero
* but hydro RSCapMult is equal to the same value as cost_cap_fin_mult

***RU***
* investment in resource supply curve technologies
	+ sum{(i,v,r,rscbin)$[r_u(r,usrep_r)$m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)],
		INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult0(i,r,t) }

* costs of refurbishments of RSC tech
	+ sum{(i,v,r)$[r_u(r,usrep_r)$Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
		cost_cap_fin_mult0(i,r,t) * cost_cap(i,t) * INV_REFURB.l(i,v,r,t) }

* costs of transmission lines
	+ sum{(r,rr,trtype)$[r_u(rr,usrep_r)$r_u(r,usrep_r)$routes_inv(r,rr,trtype,t)],
              trans_cost_cap_fin_mult(t) * transmission_line_capcost(r,rr,trtype) * INVTRAN.l(r,rr,trtype,t) }

*cost of LCC AC/DC converter stations (each LCC DC line implicitly has two, one on each end of the line)
  + sum{(r,rr)$[r_u(rr,usrep_r)$r_u(r,usrep_r)$routes_inv(r,rr,"LCC",t)],
        trans_cost_cap_fin_mult(t) * cost_acdc_lcc * 2 * INVTRAN.l(r,rr,"LCC",t) }

*cost of VSC AC/DC converter stations
  + sum{r$[r_u(r,usrep_r)],
           trans_cost_cap_fin_mult(t) * cost_acdc_vsc * INV_CONVERTER.l(r,t) }

	);
*$offtext


$ife %cur_year%>2010 $goto skipqkbaseyr

* This assumes steady state in base year and 20 year amortization lifetime, 
* which is assumed in the crf(t) calculation, 2010 is a single year investment 
* value for INV... other years are full 5 yr time step

ru(usrep_r,"qk","dollars",t)$tmodel(t) 
	= (20)*crf(t)*(1/cvt)*( 
* investment costs
	sum{(i,v,r)$[r_u(r,usrep_r)$valinv(i,v,r,t)],
		INV.l(i,v,r,t) * cost_cap_fin_mult0(i,r,t) * cost_cap(i,t)}

* costs of rsc investment ---MAX TOCHECK---
* Note that cost_cap for hydro techs are zero
* but hydro RSCapMult is equal to the same value as cost_cap_fin_mult

* investment in resource supply curve technologies
***RU***
	+ sum{(i,v,r,rscbin)$[r_u(r,usrep_r)$m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)],
		INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult0(i,r,t) }

* costs of refurbishments of RSC tech
	+ sum{(i,v,r)$[r_u(r,usrep_r)$Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
		cost_cap_fin_mult0(i,r,t) * cost_cap(i,t) * INV_REFURB.l(i,v,r,t) }

* costs of transmission lines
	+ sum{(r,rr,trtype)$[r_u(rr,usrep_r)$r_u(r,usrep_r)$routes_inv(r,rr,trtype,t)],
              trans_cost_cap_fin_mult(t) * transmission_line_capcost(r,rr,trtype) * INVTRAN.l(r,rr,trtype,t) }

*cost of LCC AC/DC converter stations (each LCC DC line implicitly has two, one on each end of the line)
  + sum{(r,rr)$[r_u(rr,usrep_r)$r_u(r,usrep_r)$routes_inv(r,rr,"LCC",t)],
        trans_cost_cap_fin_mult(t) * cost_acdc_lcc * 2 * INVTRAN.l(r,rr,"LCC",t) }

*cost of VSC AC/DC converter stations
  + sum{r$[r_u(r,usrep_r)],
           trans_cost_cap_fin_mult(t) * cost_acdc_vsc * INV_CONVERTER.l(r,t) }

	);

* calculate ITC
* amortized investment capacity costs
ru(usrep_r,"amort_investment_capacity_costs_noITC","dollars",t)$tmodel(t)
	= (20)*crf(t)*(1/cvt)*( 
	sum{(i,v,r)$[valinv(i,v,r,t)$r_u(r,usrep_r)],
		INV.l(i,v,r,t) * (cost_cap_fin_mult_noITC(i,r,t) * cost_cap(i,t) ) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
	+ sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$sccapcosttech(i)$r_u(r,usrep_r)],
		INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult_noITC(i,r,t) }
*plus cost of upgrades
    + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades$r_u(r,usrep_r)],
        cost_upgrade(i,v,r,t) * cost_cap_fin_mult_noITC(i,r,t) * UPGRADES.l(i,v,r,t) }
*cost of capacity upsizing
    + sum{(i,v,r,rscbin)$[allow_cap_up(i,v,r,rscbin,t)$r_u(r,usrep_r)],
        cost_cap_fin_mult_noITC(i,r,t) * INV_CAP_UP.l(i,v,r,rscbin,t) * cost_cap_up(i,v,r,rscbin,t) }
*cost of energy upsizing
    + sum{(i,v,r,rscbin)$[allow_ener_up(i,v,r,rscbin,t)$r_u(r,usrep_r)],
        cost_cap_fin_mult_noITC(i,r,t) * INV_ENER_UP.l(i,v,r,rscbin,t) * cost_ener_up(i,v,r,rscbin,t) }
    )
;

ru(usrep_r,"amort_investment_capacity_costs_out","dollars",t)$tmodel(t)
	= (20)*crf(t)*(1/cvt)*( 
	sum{(i,v,r)$[valinv(i,v,r,t)$r_u(r,usrep_r)],
		INV.l(i,v,r,t) * (cost_cap_fin_mult_out(i,r,t) * cost_cap(i,t) ) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
	+ sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)$sccapcosttech(i)$r_u(r,usrep_r)],
		INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult00(i,r,t) }
*plus cost of upgrades
    + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,t)$Sw_Upgrades$r_u(r,usrep_r)],
        cost_upgrade(i,v,r,t) * cost_cap_fin_mult_out(i,r,t) * UPGRADES.l(i,v,r,t) }
*cost of capacity upsizing
    + sum{(i,v,r,rscbin)$[allow_cap_up(i,v,r,rscbin,t)$r_u(r,usrep_r)],
        cost_cap_fin_mult_out(i,r,t) * INV_CAP_UP.l(i,v,r,rscbin,t) * cost_cap_up(i,v,r,rscbin,t) }
*cost of energy upsizing
    + sum{(i,v,r,rscbin)$[allow_ener_up(i,v,r,rscbin,t)$r_u(r,usrep_r)],
        cost_cap_fin_mult_out(i,r,t) * INV_ENER_UP.l(i,v,r,rscbin,t) * cost_ener_up(i,v,r,rscbin,t) }
    )
;

* itc value is difference between capacity costs with and without itc
* this will be a negative value for the itc
ru(usrep_r,"itc_amort","dollars",t)$tmodel(t)
	= 
* capacity costs with ITC
	ru(usrep_r,"amort_investment_capacity_costs_out","dollars",t)
*minus capacity costs without ITC
	- ru(usrep_r,"amort_investment_capacity_costs_noITC","dollars",t)
;


$label skipqkbaseyr
$ife %cur_year%=2010 $goto skipqknonbaseyr

ru(usrep_r,"qk","dollars",t)$tmodel(t)
	= 
* track base year remaining amortization payment in year t
	sum(ttt$[tfirst(ttt)$((t.val-ttt.val)<20)], (20-(t.val-ttt.val))/20 * (ru(usrep_r,"qk","dollars",ttt)))
* track amortized investment in all but base year -- see tamort(t,tt) specification for clarity
	+ sum(tt$[tamort(t,tt)], ((tt.val-max(tt.val-5,2010))*(1/5))*crf(tt)*(1/cvt)*( 
* investment costs
	sum{(i,v,r)$[r_u(r,usrep_r)$valinv(i,v,r,tt)],
		INV.l(i,v,r,tt) * cost_cap_fin_mult0(i,r,tt) * cost_cap(i,tt)}

* investment in resource supply curve technologies
	+ sum{(i,v,r,rscbin)$[r_u(r,usrep_r)$m_rscfeas(r,i,rscbin)$valinv(i,v,r,tt)$rsc_i(i)],
		INV_RSC.l(i,v,r,rscbin,tt) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult0(i,r,tt) }

* costs of refurbishments of RSC tech
	+ sum{(i,v,r)$[r_u(r,usrep_r)$Sw_Refurb$valinv(i,v,r,tt)$refurbtech(i)],
		cost_cap_fin_mult0(i,r,tt) * cost_cap(i,tt) * INV_REFURB.l(i,v,r,tt) }

* costs of transmission lines
	+ sum{(r,rr,trtype)$[r_u(rr,usrep_r)$r_u(r,usrep_r)$routes_inv(r,rr,trtype,tt)],
              trans_cost_cap_fin_mult(tt) * transmission_line_capcost(r,rr,trtype) * INVTRAN.l(r,rr,trtype,tt) }

*cost of LCC AC/DC converter stations (each LCC DC line implicitly has two, one on each end of the line)
  + sum{(r,rr)$[r_u(rr,usrep_r)$r_u(r,usrep_r)$routes_inv(r,rr,"LCC",tt)],
        trans_cost_cap_fin_mult(tt) * cost_acdc_lcc * 2 * INVTRAN.l(r,rr,"LCC",tt) }

*cost of VSC AC/DC converter stations
  + sum{r$[r_u(r,usrep_r)],
           trans_cost_cap_fin_mult(tt) * cost_acdc_vsc * INV_CONVERTER.l(r,tt) }
	)
);


* amortized investment capacity costs
ru(usrep_r,"amort_investment_capacity_costs_noITC","dollars",t)$tmodel(t)
	= 
* track base year remaining amortization payment in year t
sum(ttt$[tfirst(ttt)$((t.val-ttt.val)<20)], (20-(t.val-ttt.val))/20 * (ru(usrep_r,"amort_investment_capacity_costs_noITC","dollars",ttt)))
* track amortized investment in all but base year -- see tamort(t,tt) specification for clarity
+ sum(tt$[tamort(t,tt)], ((tt.val-max(tt.val-5,2010))*(1/5))*crf(tt)*(1/cvt)*( 
	sum{(i,v,r)$[valinv(i,v,r,tt)$r_u(r,usrep_r)],
		INV.l(i,v,r,tt) * (cost_cap_fin_mult_noITC(i,r,tt) * cost_cap(i,tt) ) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
	+ sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,tt)$rsc_i(i)$sccapcosttech(i)$r_u(r,usrep_r)],
		INV_RSC.l(i,v,r,rscbin,tt) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult_noITC(i,r,tt) }
*plus cost of upgrades
    + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,tt)$Sw_Upgrades$r_u(r,usrep_r)],
        cost_upgrade(i,v,r,tt) * cost_cap_fin_mult_noITC(i,r,tt) * UPGRADES.l(i,v,r,tt) }
*cost of capacity upsizing
    + sum{(i,v,r,rscbin)$[allow_cap_up(i,v,r,rscbin,tt)$r_u(r,usrep_r)],
        cost_cap_fin_mult_noITC(i,r,tt) * INV_CAP_UP.l(i,v,r,rscbin,tt) * cost_cap_up(i,v,r,rscbin,tt) }
*cost of energy upsizing
    + sum{(i,v,r,rscbin)$[allow_ener_up(i,v,r,rscbin,tt)$r_u(r,usrep_r)],
        cost_cap_fin_mult_noITC(i,r,tt) * INV_ENER_UP.l(i,v,r,rscbin,tt) * cost_ener_up(i,v,r,rscbin,tt) }
	)
)
;

ru(usrep_r,"amort_investment_capacity_costs_out","dollars",t)$tmodel(t)
	= 
* track base year remaining amortization payment in year t
sum(ttt$[tfirst(ttt)$((t.val-ttt.val)<20)], (20-(t.val-ttt.val))/20 * (ru(usrep_r,"amort_investment_capacity_costs_out","dollars",ttt)))
* track amortized investment in all but base year -- see tamort(t,tt) specification for clarity
+ sum(tt$[tamort(t,tt)], ((tt.val-max(tt.val-5,2010))*(1/5))*crf(tt)*(1/cvt)*( 
	sum{(i,v,r)$[valinv(i,v,r,tt)$r_u(r,usrep_r)],
		INV.l(i,v,r,tt) * (cost_cap_fin_mult_out(i,r,tt) * cost_cap(i,tt) ) }
* Plus geo, hydro, and pumped-hydro techs, where costs are in the supply curves
*(Note that this deviates from the objective function structure)
	+ sum{(i,v,r,rscbin)$[m_rscfeas(r,i,rscbin)$valinv(i,v,r,tt)$rsc_i(i)$sccapcosttech(i)$r_u(r,usrep_r)],
		INV_RSC.l(i,v,r,rscbin,tt) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult00(i,r,tt) }
*plus cost of upgrades
    + sum{(i,v,r)$[upgrade(i)$valcap(i,v,r,tt)$Sw_Upgrades$r_u(r,usrep_r)],
        cost_upgrade(i,v,r,tt) * cost_cap_fin_mult_out(i,r,tt) * UPGRADES.l(i,v,r,tt) }
*cost of capacity upsizing
    + sum{(i,v,r,rscbin)$[allow_cap_up(i,v,r,rscbin,tt)$r_u(r,usrep_r)],
        cost_cap_fin_mult_out(i,r,tt) * INV_CAP_UP.l(i,v,r,rscbin,tt) * cost_cap_up(i,v,r,rscbin,tt) }
*cost of energy upsizing
    + sum{(i,v,r,rscbin)$[allow_ener_up(i,v,r,rscbin,tt)$r_u(r,usrep_r)],
        cost_cap_fin_mult_out(i,r,tt) * INV_ENER_UP.l(i,v,r,rscbin,tt) * cost_ener_up(i,v,r,rscbin,tt) }
	)
)
;

* amortized itc value
ru(usrep_r,"itc_amort","dollars",t)$tmodel(t)
	=
	ru(usrep_r,"amort_investment_capacity_costs_out","dollars",t)
*minus capacity costs without ITC
	- ru(usrep_r,"amort_investment_capacity_costs_noITC","dollars",t)
;


$label skipqknonbaseyr

* require negative --- non-CA pacific can be positive at least for 2010 it seems
ru(usrep_r,"itc","dollars",t) = min(ru(usrep_r,"itc","dollars",t),0);
ru(usrep_r,"itc_amort","dollars",t) = min(ru(usrep_r,"itc_amort","dollars",t),0);

* decomposition
ru(usrep_r,"qk_decomp_inv","dollars",t)$tmodel(t) 
	= pvf_capital(t) * (1/cvt) * ((1/5)$[(t.val > 2010)]+1$[(t.val eq 2010)]) * ( 
* investment costs
	sum{(i,v,r)$[r_u(r,usrep_r)$valinv(i,v,r,t)],
		INV.l(i,v,r,t) * cost_cap_fin_mult0(i,r,t) * cost_cap(i,t)}
	);

ru(usrep_r,"qk_decomp_rsc","dollars",t)$tmodel(t) 
	= pvf_capital(t) * (1/cvt) * ((1/5)$[(t.val > 2010)]+1$[(t.val eq 2010)]) * ( 
* costs of rsc investment ---MAX TOCHECK---
* Note that cost_cap for hydro techs are zero
* but hydro RSCapMult is equal to the same value as cost_cap_fin_mult

***RU***
* investment in resource supply curve technologies
	+ sum{(i,v,r,rscbin)$[r_u(r,usrep_r)$m_rscfeas(r,i,rscbin)$valinv(i,v,r,t)$rsc_i(i)],
		INV_RSC.l(i,v,r,rscbin,t) * m_rsc_dat(r,i,rscbin,"cost") * rsc_fin_mult0(i,r,t) }

* costs of refurbishments of RSC tech
	+ sum{(i,v,r)$[r_u(r,usrep_r)$Sw_Refurb$valinv(i,v,r,t)$refurbtech(i)],
		cost_cap_fin_mult0(i,r,t) * cost_cap(i,t) * INV_REFURB.l(i,v,r,t) }
	);

ru(usrep_r,"qk_decomp_trans","dollars",t)$tmodel(t) 
	= pvf_capital(t) * (1/cvt) * ((1/5)$[(t.val > 2010)]+1$[(t.val eq 2010)]) * ( 
* costs of transmission lines
	+ sum{(r,rr,trtype)$[r_u(rr,usrep_r)$r_u(r,usrep_r)$routes_inv(r,rr,trtype,t)],
              trans_cost_cap_fin_mult(t) * transmission_line_capcost(r,rr,trtype) * INVTRAN.l(r,rr,trtype,t) }
	);

ru(usrep_r,"qk_decomp_conv","dollars",t)$tmodel(t) 
	= pvf_capital(t) * (1/cvt) * ((1/5)$[(t.val > 2010)]+1$[(t.val eq 2010)]) * ( 
*cost of LCC AC/DC converter stations (each LCC DC line implicitly has two, one on each end of the line)
  + sum{(r,rr)$[r_u(rr,usrep_r)$r_u(r,usrep_r)$routes_inv(r,rr,"LCC",t)],
        trans_cost_cap_fin_mult(t) * cost_acdc_lcc * 2 * INVTRAN.l(r,rr,"LCC",t) }

*cost of VSC AC/DC converter stations
  + sum{r$[r_u(r,usrep_r)],
           trans_cost_cap_fin_mult(t) * cost_acdc_vsc * INV_CONVERTER.l(r,t) }

	);

* hydro and nuclear generation
ru(usrep_r,"hydro","twh",t)$tmodel(t)
	= sum((i,v,h,r)$[r_u(r,usrep_r)$valgen(i,v,r,t)$hydro(i)],
		gen.l(i,v,r,h,t) * hours(h)) / 1e6;

ru(usrep_r,"nuclear","twh",t)$tmodel(t) 
	= sum((v,h,r)$[r_u(r,usrep_r)$valgen("nuclear",v,r,t)],
		gen.l("nuclear",v,r,h,t) * hours(h)) / 1e6;

* emissions  

* Calculate emissions by technology, converting to million tons
ru(usrep_r,"qco2_tech",i,t)$tmodel(t) 
	= sum((r)$[r_u(r,usrep_r)], 
	1e-6*(
		sum{(v,h)$[valgen(i,v,r,t)],
			hours(h) * emit_rate("co2",i,v,r,t) 
			* (GEN.l(i,v,r,h,t)
				+ CCSFLEX_POW.l(i,v,r,h,t)$[ccsflex(i)$(Sw_CCSFLEX_BYP OR Sw_CCSFLEX_STO OR Sw_CCSFLEX_DAC)])
		} / emit_scale("co2")

* Plus emissions produced via production activities (SMR, SMR-CCS, DAC)
* The "production" of negative CO2 emissions via DAC is also included here
		+ sum{(p,v,h)$[valcap(i,v,r,t)$i_p(i,p)],
			hours(h) * prod_emit_rate("co2",i,t)
			* PRODUCE.l(p,i,v,r,h,t)
		} / emit_scale("co2")

*[minus] co2 reduce from flexible CCS capture
*capture = capture per energy used by the ccs system * CCS energy

* Flexible CCS - bypass
		- (sum{(v,h)$[valgen(i,v,r,t)$ccsflex_byp(i)], 
			ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POW.l(i,v,r,h,t) } / emit_scale("co2"))$Sw_CCSFLEX_BYP

* Flexible CCS - storage
		- (sum{(v,h)$[valgen(i,v,r,t)$ccsflex_sto(i)], 
			ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POWREQ.l(i,v,r,h,t) } / emit_scale("co2"))$Sw_CCSFLEX_STO

	)*emit_scale("co2")
	);

* another with co2 by fuel type in the RU pass 
ru(usrep_r,"qco2_coal","mmtco2",t)$tmodel(t) 
	= sum(i$coal(i), ru(usrep_r,"qco2_tech",i,t));

ru(usrep_r,"qco2_gas","mmtco2",t)$tmodel(t) 
	= sum(i$(gas(i) or ogs(i)), ru(usrep_r,"qco2_tech",i,t));

ru(usrep_r,"qco2_bio","mmtco2",t)$tmodel(t) 
	= sum(i$bio(i), ru(usrep_r,"qco2_tech",i,t));

ru(usrep_r,"qco2","mmtco2",t)$tmodel(t) 
	= 1e-6 * sum(r$(r_u(r,usrep_r)),EMIT.L("CO2",r,t)) * emit_scale("CO2");

ru(usrep_r,"qco2_balance","mmtco2",t)$tmodel(t) 
	= 1e-6 * sum(r$(r_u(r,usrep_r)),EMIT.L("CO2",r,t)) * emit_scale("CO2")
	- sum(i$(coal(i) or gas(i) or ogs(i) or bio(i)), ru(usrep_r,"qco2_tech",i,t));

ru(usrep_r,"nonele","mmtco2",t)$tmodel(t) 
	= 1e-6 * EMITNonELE.L("CO2",usrep_r,t);

ru("USA","ele","mmtco2",t)$tmodel(t) = 1e-6 * sum((r,usrep_r)$(r_u(r,usrep_r)),EMIT.L("CO2",r,t)) * emit_scale("CO2");
ru("USA","nonele","mmtco2",t)$tmodel(t) = 1e-6 * sum(usrep_r,EMITNonELE.L("CO2",usrep_r,t));
ru("USA","total","mmtco2",t)$tmodel(t) = ru("USA","ele","mmtco2",t) + ru("USA","nonele","mmtco2",t);
ru("USA","cap","mmtco2",t)$tmodel(t) = 1e-6 * emiscap("CO2","USA");

* emission prices
ru(usrep_r,"co2prc","dolpertCO2",t)$[tmodel(t)$(sum{r$[r_u(r,usrep_r)],1})]
	= (1/cvt)*vscale(t)*(eq_natemis.m("CO2",t)/emit_scale("CO2"))$cappol("CO2","USA")
	+ ur_("USA","co2prc","dolpertCO2","%cur_year%")$(not cappol("CO2","USA"))
;

*------------------------------------------------------------------------
* Electricity price --- wholesale load cost 
*------------------------------------------------------------------------

*!!! for now avoiding h2/electrolysis impact on peak demand
reqt_quant_ru('res_marg_ann',r,t)$[tmodel(t)] = 
	sum(ccseason, peakdem_static_ccseason(r,ccseason,t) )
;

reqt_price_ru('res_marg_ann',r,t)$[tmodel_new(t)$reqt_quant_ru('res_marg_ann',r,t)] = 
    sum{ccseason, (1 / cost_scale) * (1 / pvf_onm(t)) * eq_reserve_margin.m(r,ccseason,t) * peakdem_static_ccseason(r,ccseason,t) * (1+prm(r,t))  }
	/ reqt_quant_ru('res_marg_ann',r,t)
;

ru(usrep_r,"price_res_marg","dolperMWh",t)$[tmodel(t)$(sum(r$[r_u(r,usrep_r)],reqt_quant_ru("res_marg_ann",r,t)))] =
    (
		sum(r$[r_u(r,usrep_r)],reqt_price_ru("res_marg_ann",r,t)*reqt_quant_ru("res_marg_ann",r,t))
    	/sum(r$[r_u(r,usrep_r)],reqt_quant_ru("res_marg_ann",r,t))
	)
;

ru(usrep_r,"dem_p_reqt","dolperMWh",t)$[tmodel(t)] =
	(1/cvt)*(
		elecost(usrep_r,t,'energy')
		+ ru(usrep_r,"price_res_marg","dolperMWh",t)
	)
;

*------------------------------------------------------------------------


*==========================================
*	ITERATION LOG
*==========================================

$ife %iter%=0	$goto enditerlog	
$gdxin link%ds%reeds_out%ds%%case%_%cur_year%_it%iter0% 
$loadr iterlog
$gdxin
$label enditerlog

loop(t$tmodel(t),

* Elasticities
iterlog("%case%",t,"delas-pele","ReEDS","iter%iter%",usrep_r) = eledelas(usrep_r);
iterlog("%case%",t,"delas-pcarb","ReEDS","iter%iter%",usrep_r) = delasemis("CO2",usrep_r);

* Carbon prices
iterlog("%case%",t,"co2prc","ReEDS","iter%iter%",usrep_r) = ru(usrep_r,"co2prc","dolpertCO2",t);
iterlog("%case%",t,"co2prc","USREP","iter%iter%",usrep_r) = ur_(usrep_r,"co2prc","dolpertco2",t);
iterlog("%case%",t,"co2prc","USREP","iter%iter%","USA") = ur_("USA","co2prc","dolpertco2",t);
iterlog("%case%",t,"co2prc0","USREP","iter%iter%",usrep_r) = ur_(usrep_r,"co2prc0","dolpertco2",t);
iterlog("%case%",t,"co2prc0","USREP","iter%iter%","USA") = ur_("USA","co2prc0","dolpertco2",t);

* Emissions
iterlog("%case%",t,"emis","USREP","iter%iter%",usrep_r) = 1e-6 * baseemisnonele("CO2",usrep_r,t);

$ife %iter%=0	iterlog("%case%",t,"emis","USREP","iter%iter%",usrep_r) = 1e-6*EMITNonELE.L("CO2",usrep_r,t);
$ife %iter%>0	iterlog("%case%",t,"emis","USREP","iter%iter%","USA") = sum(usrep_r$ufeas(usrep_r),ur_(usrep_r,"emisnonele","MMTCO2",t)) + sum(usrep_r$(not ufeas(usrep_r)), ur_(usrep_r,"emis","MMTCO2",t));

iterlog("%case%",t,"emis","ReEDS","iter%iter%",usrep_r) = ru(usrep_r,"qco2","mmtco2",t);
iterlog("%case%",t,"emis","ReEDS","iter%iter%","USA") = sum(usrep_r,iterlog("%case%",t,"emis","ReEDS","iter%iter%",usrep_r));
iterlog("%case%",t,"emis","ttl","iter%iter%","USA")
	= iterlog("%case%",t,"emis","ReEDS","iter%iter%","USA") 
	+ iterlog("%case%",t,"emis","USREP","iter%iter%","USA");

* Emissions cap
iterlog("%case%",t,"cap","ele","iter%iter%",usrep_r) = 1e-6*sum(r$(r_u(r,usrep_r)), EMIT.L("CO2",r,t)) * emit_scale("CO2");
iterlog("%case%",t,"cap","ele","iter%iter%","USA") = 1e-6*sum((r,usrep_r)$(r_u(r,usrep_r)), EMIT.L("CO2",r,t)) * emit_scale("CO2");
*iterlog("%case%",t,"cap","nonele","iter%iter%",usrep_r) = 1e-6*EMITNonELE.L("CO2",usrep_r,t);
*iterlog("%case%",t,"cap","nonele","iter%iter%","USA") = 1e-6*sum(usrep_r, EMITNonELE.L("CO2",usrep_r,t));
iterlog("%case%",t,"cap","ttl","iter%iter%","USA") = 1e-6*emiscap("CO2","USA");
iterlog("%case%",t,"cap","ttl","iter%iter%",usrep_r) = 1e-6*emiscap("CO2",usrep_r);

* electricity price
iterlog("%case%",t,"eleprc","ReEDS","iter%iter%",usrep_r) = ru(usrep_r,"ele","dolperMWh",t);
iterlog("%case%",t,"eleprc","USREP","iter%iter%",usrep_r) = ur_(usrep_r,"ele","dolperMWh",t);

* solve time recording
iterlog("%case%",t,"LP_etSolve","ReEDS","iter%iter%","USA")$[tmodel(t)] = ReEDSmodel.etSolve;
iterlog("%case%",t,"QP_etSolve","ReEDS","iter%iter%","USA")$[tmodel(t)] = ReEDSmodelqcp.etSolve;

);
option iterlog:3:5:1;
display iterlog;

price_out(r,h,t)$[tmodel(t)] = eq_loadcon.m(r,h,t) / pvf_onm(t);

$if not exist link%ds%reeds_out%ds%null	$call mkdir link%ds%reeds_out
execute_unload 'link%ds%reeds_out%ds%%case%_%cur_year%_it%iter%.gdx', ru, ur_, baseprc, baseload, iterlog, price_out;
execute_unload 'link%ds%reeds_out%ds%%case%_%cur_year%.gdx', ru, ur_, baseprc, baseload, price_out;

*execute_unload 'loadcheck_%cur_year%_%iter%.gdx' loadcheck2 ; 
