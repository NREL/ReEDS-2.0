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


* create the model
 Model %case% /all/;


*=================================
* -- MODEL AND SOLVER OPTIONS --
*=================================

OPTION lp = %solver% ;
%case%.optfile = %GSw_gopt% ;
OPTION RESLIM = 50000 ;
*treat fixed variables as parameters
%case%.holdfixed = 1 ;

$ifthen.valstr Sw_ValStr == 1
OPTION savepoint = 1 ;
$endif.valstr

$if not set loadgdx $setglobal loadgdx 0

$ifthen.gdxin %loadgdx% == 1
execute_loadpoint "gdxfiles%ds%%gdxfin%.gdx" ;
Option BRatio = 0.0 ;
$endif.gdxin


*====================================
* --- Endogenous Retirements ---
*====================================

if(Sw_Retire=1,
*add retirement techs here
*make sure only setting retiretech for 'existv'
retiretech(i,existv,rb,t) = yes;
retiretech("HYDRO-PUMPED",existv,rb,t) = no;
retiretech(battery,existv,rb,t) = no;
retiretech(hydro, existv,rb,t) = no;
retiretech('NUCLEAR',existv,rb,t) = no;
  );
retiretech(i,v,r,t)$vre(i) = no;
retiretech(i,v,rs,t) = no;

*====================================
*remove capacity_exog, prescribed capacity
*and prescribed retirements if Sw_TechPhaseOut is turned on
*====================================

capacity_exog(i,v,r,rs,t)$[Sw_TechPhaseOut$phase_out_tech(i)$(yeart(t)>=phase_out_year(i))] = 0;
prescribednonrsc(t,i,r,"value")$[Sw_TechPhaseOut$phase_out_tech(i)$(yeart(t)>=phase_out_year(i))] = 0;
prescribedrsc(t,i,r,rs,"value")$[Sw_TechPhaseOut$phase_out_tech(i)$(yeart(t)>=phase_out_year(i))] = 0;
prescribedretirements(t,r,i,"value")$[Sw_TechPhaseOut$phase_out_tech(i)$(yeart(t)>=phase_out_year(i))] = 0;

*==============================
* Year specification
*==============================

*$if not set yearset $setglobal yearset %yearset%

set tmodel_new(t) /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%%yearset%
/;


$if not set endyear $setglobal endyear 2050
tmodel_new(t)$(yeart(t)>%endyear%)= no;

*reset the first and last year indices of the model
tfirst(t) = no;
tlast(t) = no;
tfirst(t)$(ord(t)=smin(tt$tmodel_new(tt),ord(tt))) = yes;
tlast(t)$(ord(t)=smax(tt$tmodel_new(tt),ord(tt))) = yes;
yeart_tfirst = sum(t$tfirst(t),yeart(t));
yeart_tlast = sum(t$tlast(t),yeart(t));


tprev(t,tt) = no;
*now get rid of all non-immediately-previous values (it takes three steps to get there...)
tprev(t,tt)$(tmodel_new(t)$tmodel_new(tt)$(tt.val<t.val)) = yes;
mindiff(t)$tmodel_new(t) = smin(tt$tprev(t,tt),t.val-tt.val);
tprev(t,tt)$(tmodel_new(t)$tmodel_new(tt)$(t.val-tt.val<>mindiff(t))) = no;


*==============================
* Banned Sets specification
*==============================

*The following two sets:
*ban - will remove the technology from being considered, anywhere
*bannew - will remove the ability to invest in that technology
set ban(i) "ban from existing, prescribed, and new generation -- usually indicative of missing data or operational constraints"
    bannew(i) "banned from creating new capacity, usually due to lacking data or represention"
;

ban(i) = no;
bannew("SUBCRITICAL-OIL") = yes;
bannew("NEPAL_STORAGE") = yes;

*==============================
* Region specification
*==============================

rfeas_cap(r)$rfeas(r) = yes;
rfeas_cap(rs)$(sum(r$rfeas(r),r_rs(r,rs))) = yes;
rfeas_cap("sk") = no;

*set the country feasibility sets
*determined by which regions are feasible
countryfeas(country)$(sum(r$(rfeas(r)$r_country(r,country)),1)) = yes;

m_rscfeas(rb,i,rscbin) = rscfeas(rb,"sk",i,rscbin);
m_rscfeas(rs,i,rscbin)$(not sameas(rs,"sk")) = sum(r$r_rs(r,rs),rscfeas(r,rs,i,rscbin));


*==========================================
* -- Valid Capacity and Generation Sets --
*==========================================

* -- valcap specification --
* first all available techs are included
* then we remove those as specified

*existing plants are enabled if not in ban(i)
valcap(i,v,r,t)$[m_capacity_exog(i,v,r,t)$(not ban(i))$rfeas_cap(r)$tmodel_new(t)] = yes;

*enable all new classes for balancing regions
*if available (via ivt) and if not an rsc tech
*and if it is not in ban or bannew
*the year also needs to be greater than the first year indicated
*for that specific class (this is the summing over tt portion)
*or it needs to be specified in prescriptivelink
valcap(i,newv,rb,t)$[rfeas(rb)$(not rsc_i(i))$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $(sum(tt$(yeart(tt)<=yeart(t)),ivt(i,newv,tt)))
                    $((yeart(t)>=firstyear(i)) )
                    ]  = yes;

*for rsc technologies, enabled if m_rscfeas is populated
*similarly to non-rsc technologies except now all regions
*can be populated (rb vs r) and there is the additional condition
*that m_rscfeas must contain values in at least one rscbin
valcap(i,newv,r,t)$[rfeas_cap(r)$rsc_i(i)$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $sum{rscbin,m_rscfeas(r,i,rscbin)}
                    $sum(tt$(yeart(tt)<=yeart(t)),ivt(i,newv,tt))
                    $((yeart(t)>=firstyear(i)) )
                    ]  = yes;

* make sure sk region does not enter valcap
valcap(i,v,"sk",t) = no;

valcap_irt(i,r,t) = sum{v, valcap(i,v,r,t) };

* -- valinv specification --
valinv(i,v,r,t)$[valcap(i,v,r,t)$ivt(i,v,t)] = yes ;

* add aggregations of valinv
valinv_irt(i,r,t) = sum{v, valinv(i,v,r,t) } ;

* new gas investments are not allowed in Uttar Pradesh
if(Sw_BanGasUP=1,
valcap(i,v,r,t)$[gas(i)$newv(v)$focus_region(r)]=no
);

* remove colocated green H2 techs from valcap if not modeling colocation
if(Sw_ColocatedGreenH2=0,
valcap(i,v,r,t)$[greenhydrogentech(i)]=no
);

* -- valgen specification --
* if the balancing area and/or its
* resource supply regions have valid capacity
* then you can generate from it

valgen(i,v,r,t) = no;
valgen(i,v,r,t)$[sum{rr$cap_agg(r,rr),valcap(i,v,rr,t)}] = yes;

* -- m_refurb_cond specification --

* technologies can be refurbished if...
*  they are part of refurbtech
*  the years from t to tt are beyond the expiration of the tech (via maxage)
*  it was a valid capacity in t and in tt
*  it was a valid investment in year tt (via ivt)
m_refurb_cond(i,newv,r,t,tt)$[refurbtech(i)
                              $(yeart(tt)<yeart(t))
                              $(yeart(t) - yeart(tt) > maxage(i))
                              $valcap(i,newv,r,t)$valcap(i,newv,r,tt)
                              $ivt(i,newv,tt)
                             ] = yes;


* -- inv_cond specification --

*if there is a link between the bintage and the year
*all previous years
*if the unit we invested in is not retired...
inv_cond(i,newv,t,tt)$[(not ban(i))$(not bannew(i))
                      $tmodel_new(t)$tmodel_new(tt)
                      $(yeart(tt) <= yeart(t))
                      $(yeart(tt) >= firstyear(i))
                      $ivt(i,newv,tt)
                      $(ord(t)-ord(tt) < maxage(i))
                      ] = yes;


*=============================
* Curtailment and CC Settings
*=============================

set tload(t) "years in which data is loaded" ;
tload(t) = no ;

set cciter "placeholder for iteration number for tracking CC and curtailment" /0*20/ ;

parameter curt_old_load(r,h,t)                "--MW-- curt_old but loaded in from the gdx file for whichever year"
          curt_marg_load(i,r,h,t)             "--fraction-- marginal curtailment rate for new generators, loaded from gdx file"
          oldVREgen(r,h,t)                    "--MW-- generation from endogenous VRE capacity that existed the year before, or iteration before"
          oldMINGEN(r,h,t)                    "--MW-- Minimum generation from the previous iteration"
          curt_totmarg(r,h,t)                 "--MW-- original estimate of total curtailment for intertemporal, based on marginals"
          curt_scale(r,h,t)                   "--unitless-- scaling of marginal curtailment levels in intertemporal runs to equal total curtailment levels"
          cc_totmarg(i,r,szn,t)               "--MW-- original estimate of total capacity value for intertemporal, based on marginals"
          cc_scale(i,r,szn,t)                 "--unitless-- scaling of marginal capacity value levels in intertemporal runs to equal total capacity value"
          cc_iter(i,v,r,szn,t,cciter)         "--fraction-- Actual capacity value in iteration cciter"
          cc_mar_load(i,r,szn,t)              "--fraction--  cc_mar loading in from the cc_out gdx file",
          curt_iter(i,r,h,t,cciter)           "--fraction-- Actual curtailment in iteration cciter"
          curt_mingen_iter(r,h,t,cciter)      "--fraction-- Actual curtailment from mingen in iteration cciter"
          cc_change(i,v,r,szn,t)              "--fraction-- Change of capacity credit between this and previous iteration"
          curt_change(i,r,h,t)                "--fraction-- Change of curtailment between this and previous iteration"
          curt_mingen_change(r,h,t)           "--fraction-- Change of mingen curtailment between this and previous iteration"
          curt_stor_load(i,v,r,h,src,t)       "--fraction-- curt_stor value loaded from gdx file"
          curt_tran_load(r,rr,h,t)            "--fraction-- curt_tran value loaded from gdx file"
          curt_reduct_tran_max_load(r,rr,h,t) "--MW-- curt_reduct_tran loaded from gdx file"
          storage_in_min_load(r,h,t)          "--MW-- storage_in_min value loaded from gdx file"
          hourly_arbitrage_value_load(i,r,t)  "--$/MW-yr-- hourly_arbitrage_value value from gdx file"
;

parameters powerfrac_upstream_(r,rr,h,t)   "--unitless-- fraction of power at r that was generated at rr",
           powerfrac_downstream_(rr,r,h,t) "--unitless-- fraction of power generated at rr that serves load at r" ;

*start the values at zero to avoid errors that
*these values have not been assigned
cc_int(i,v,r,szn,t) = 0 ;
cc_totmarg(i,r,szn,t) = 0 ;
cc_excess(i,r,szn,t) = 0 ;
cc_scale(i,r,szn,t) = 0 ;
curt_int(i,r,h,t) = 0 ;
curt_totmarg(r,h,t) = 0 ;
curt_excess(r,h,t) = 0 ;
curt_scale(r,h,t) = 0 ;
curt_mingen_int(r,h,t) = 0 ;
tfix(t) = no;


*=============================
* Trim largest matrices to reduce file sizes
*=============================

cost_vom(i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;
cost_fom(i,v,r,t)$[not valcap(i,v,r,t)] = 0 ;
heat_rate(i,v,r,t)$[not valgen(i,v,r,t)] = 0 ;
avail(i,v,h) = round(avail(i,v,h),4) ;
cost_cap(i,t) = round(cost_cap(i,t),3) ;
cost_fom(i,v,r,t)$valcap(i,v,r,t) = round(cost_fom(i,v,r,t),3) ;
cost_opres(i) = round(cost_opres(i),3) ;
InterTransCost(r) = round(InterTransCost(r),3) ;
cost_vom(i,v,r,t)$valgen(i,v,r,t) = round(cost_vom(i,v,r,t),3) ;
degrade(i,tt,t) = round(degrade(i,tt,t),4) ;
distance(r,rr) = round(distance(r,rr),3) ;
fuel_price(i,r,t) = round(fuel_price(i,r,t),3) ;
heat_rate(i,v,r,t)$valgen(i,v,r,t) = round(heat_rate(i,v,r,t),2) ;
m_avail_retire_exog_rsc(i,v,r,t)$valcap(i,v,r,t) = round(m_avail_retire_exog_rsc(i,v,r,t),4) ;
m_capacity_exog(i,v,r,t)$valcap(i,v,r,t) = round(m_capacity_exog(i,v,r,t),4) ;
m_cf(i,r,h)$[cf_tech(i)] = round(m_cf(i,r,h),5) ;
m_cf(i,r,h)$[(m_cf(i,r,h)<0.001)] = 0 ;
m_required_prescriptions(i,r,t) = round(m_required_prescriptions(i,r,t),4) ;
m_rsc_dat(r,i,rscbin,"cost") = round(m_rsc_dat(r,i,rscbin,"cost"),3) ;


*============================
* --- Iteration Tracking ---
*============================

parameter cap_iter(i,v,r,t,cciter) "--MW-- Capacity by iteration"
          gen_iter(i,v,r,t,cciter) "--MWh-- Annual uncurtailed generation by iteration"
          cap_firm_iter(i,v,r,szn,t,cciter) "--MW-- VRE Firm capacity by iteration"
          curt_tot_iter(i,v,r,t,cciter) "--MWh-- Total VRE total curtailment by iteration"
;
cap_iter(i,v,r,t,cciter) = 0 ;
gen_iter(i,v,r,t,cciter) = 0 ;


*================================================
* --- INTERTEMPORAL SETUP ---
*================================================

$ifthen.int %timetype%=="int"

tmodel(t) = no ;
tmodel(t)$[tmodel_new(t)$(yeart(t)<=%endyear%)] = yes ;


parameter pv_age_residual_fraction(i,t) "ratio of the amount of service years remaining on pv panels in the final year from year t to the maximum life of pv panels" ;

pv_age_residual_fraction(i,t)$pv(i) = max(0, maxage(i) - (sum{tt$tlast(tt), yeart(tt) } - yeart(t))) / maxage(i) ;

*need to increase the financial multiplier for PV to account for the future capacity degradation
*should avoid hardcoding in the future -- for the intertemporal case, using a portion
*of the degradation multiplier based on fraction of life beyond the solve period

cost_cap_fin_mult(i,r,t)$pv(i) =
      round((1 + 0.052 * pv_age_residual_fraction(i,t)) * cost_cap_fin_mult(i,r,t), 4) ;

*Cap the maximum CC in the first solve iteration
cc_int(i,v,r,szn,t)$[rsc_i(i)$(cc_int(i,v,r,szn,t)>0.7)$wind(i)] = 0.7 ;
cc_int(i,v,r,szn,t)$[rsc_i(i)$(cc_int(i,v,r,szn,t)>0.5)$pv(i)] = 0.5 ;


*increase reslim for the intertemporal solve
option reslim = 345600 ;
*set objective function to millions of dollars
*cost_scale = 1 ;

*marginal capacity value not used in intertemporal case
m_cc_mar(i,r,szn,t) = 0 ;
*static capacity value for existing capacity not used in intertemporal case
cc_old(i,r,szn,t) = 0 ;


scalar    maxdev    "maximum deviation of price from one iteration to the next" /0.25/ ;

*both pvfs start out the same but below we loop over each year
*and accumulate the values of pvf_onm for years not in tmodel_new(t);
pvf_capital(t) = round(1/((1+discount_rate)**(t.val-yeart_tfirst)),6);
pvf_onm(t) = 1/((1+discount_rate)**(t.val-yeart_tfirst));


*pvf in modeled years is the sum of all years
*starting at the modeled year up to the modeled year
*said differently, it is the sum of the modeled year
*plus those in the gap until the next solve year
scalar check_solve "binary to see if the current year is modeled in the following loop that establish PVF_onm for intertemporal solves" /0/;

loop(t$(tmodel_new(t)$(not tlast(t))),
  check_solve=0;
  loop(yy$(yy.val>t.val),
    if(tmodel_new(yy),
        check_solve=1;
      );

    if(check_solve=0,
       pvf_onm(t) = pvf_onm(t) + pvf_onm(yy);
      );
    );
  );

*the final periods pvf_onm is the sum over the next 19 years
*of those years pvf_onm values.
*e.g. pvf_onm(2050) = pvf_onm(2050)+pvf_onm(2051)+... pvf_onm(2069)
temppvf(yearafter) = (1/(1+discount_rate)**(yearafter.val + yeart_tlast - yeart_tfirst));
pvf_onm(t)$tlast(t) = pvf_onm(t) + sum(yearafter,temppvf(yearafter));
pvf_onm(t) = round(pvf_onm(t),6);


*set objective function to millions of rupees
cost_scale = 1e-6;

$endif.int



*======================
* --- Capacity Credit SETUP ---
*======================
$if NOT dexist %casepath%%ds%augur_data $call 'mkdir %casepath%%ds%augur_data';

* create PKL files that are used in all solve years cc_py calculations
execute_unload '%casepath%%ds%augur_data%ds%pickle_prep.gdx' rb, r_rs, r_region;
execute '%pythonpath% D_Augur%ds%d00_pickle_prep.py %HourlyLoadFile% %case% %casepath%'

*======================
* --- Unload all inputs ---
*======================

execute_unload 'C_Solve%ds%alldat.gdx';
display valgen;