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


*====================================
*remove capacity_exog, prescribed capacity 
*and prescribed retirements if Sw_TechPhaseOut is turned on
*====================================

capacity_exog(i,c,r,rs,t)$[Sw_TechPhaseOut$phase_out_tech(i)$(yeart(t)>=phase_out_year(i))] = 0;
prescribednonrsc(t,i,r,"value")$[Sw_TechPhaseOut$phase_out_tech(i)$(yeart(t)>=phase_out_year(i))] = 0;
prescribedrsc(t,i,r,rs,"value")$[Sw_TechPhaseOut$phase_out_tech(i)$(yeart(t)>=phase_out_year(i))] = 0;
prescribedretirements(t,r,i,"value")$[Sw_TechPhaseOut$phase_out_tech(i)$(yeart(t)>=phase_out_year(i))] = 0;

*==============================
* Year specification
*==============================

$if not set yearset $setglobal yearset 'inputs%ds%sets%ds%modeledyears_set.csv'


set tmodel_new(t) /
$include %yearset%
/;


$if not set endyear $setglobal endyear 2047
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

* start with an empty set
valcap(i,c,r,t) = no;

*existing plants are enabled if not in ban(i)
valcap(i,c,r,t)$[m_capacity_exog(i,c,r,t)$(not ban(i))$rfeas_cap(r)$tmodel_new(t)] = yes;

*enable all new classes for balancing regions
*if available (via ict) and if not an rsc tech
*and if it is not in ban or bannew
*the year also needs to be greater than the first year indicated
*for that specific class (this is the summing over tt portion)
*or it needs to be specified in prescriptivelink
valcap(i,newc,rb,t)$[rfeas(rb)$(not rsc_i(i))$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $(sum(tt$(yeart(tt)<=yeart(t)),ict(i,newc,tt)))
                    $((yeart(t)>=firstyear(i)) )
                    ]  = yes;

*for rsc technologies, enabled if m_rscfeas is populated
*similarly to non-rsc technologies except now all regions
*can be populated (rb vs r) and there is the additional condition
*that m_rscfeas must contain values in at least one rscbin
valcap(i,newc,r,t)$[rfeas_cap(r)$rsc_i(i)$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $sum{rscbin,m_rscfeas(r,i,rscbin)}
                    $sum(tt$(yeart(tt)<=yeart(t)),ict(i,newc,tt))
                    $((yeart(t)>=firstyear(i)) )
                    ]  = yes;

*make sure sk region does not enter valcap
valcap(i,c,"sk",t) = no;


* -- valgen specification --
* if the balancing area and/or its
* resource supply regions have valid capacity
* then you can generate from it

valgen(i,c,r,t) = no;
valgen(i,c,r,t)$[sum{rr$cap_agg(r,rr),valcap(i,c,rr,t)}] = yes;

* -- m_refurb_cond specification --

* technologies can be refurbished if...
*  they are part of refurbtech
*  the years from t to tt are beyond the expiration of the tech (via maxage)
*  it was a valid capacity in t and in tt
*  it was a valid investment in year tt (via ict)
m_refurb_cond(i,newc,r,t,tt)$[refurbtech(i)
                              $(yeart(tt)<yeart(t))
                              $(yeart(t) - yeart(tt) > maxage(i))
                              $valcap(i,newc,r,t)$valcap(i,newc,r,tt)
                              $ict(i,newc,tt)
                             ] = yes;


* -- inv_cond specification --

*if there is a link between the bintage and the year
*all previous years
*if the unit we invested in is not retired...
inv_cond(i,newc,t,tt)$[(not ban(i))$(not bannew(i))
                      $tmodel_new(t)$tmodel_new(tt)
                      $(yeart(tt) <= yeart(t))
                      $(yeart(tt) >= firstyear(i))
                      $ict(i,newc,tt)
                      $(ord(t)-ord(tt) < maxage(i))
                      ] = yes;


*=================================
* -- MODEL AND SOLVER OPTIONS --
*=================================

OPTION lp = %solver%;
OPTION RESLIM = 50000;
OPTION NLP = pathNLP;
%case%.holdfixed = 1;

*load in a previous solution if specified in cases.csv
$if not set loadgdx $setglobal loadgdx 0

$ifthen.gdxin %loadgdx% == 1
execute_loadpoint "E_Outputs%ds%gdxfiles%ds%%gdxfin%.gdx";
Option BRatio = 0.0;
$endif.gdxin

*====================================
* --- Endogenous Retirements ---
*====================================

if(Sw_Retire=1,
*add retirement techs here
*make sure only setting retiretech for 'existc'
retiretech(i,existc,r,t) = yes;
retiretech("HYDRO-PUMPED",existc,r,t) = no;
retiretech(hydro, existc,r,t) = no;
retiretech('NUCLEAR',existc,r,t) = no;
  );



*=============================
* Curtailment and CC Settings
*=============================

set tload(t) "years in which data is loaded";
tload(t) = no;

set cciter "placeholder for iteration number for tracking CC and curtailment" /0*20/;

parameter SurpOld_(r,h,t) "--MW-- surpold but loaded in from the gdx file for whichever year",
          surpmarg_(i,r,rs,h,t) "--unitless-- marginal curtailment rate for new generators, loaded from gdx file",
          oldVREgen(r,h,t) "--MWh-- generation from endogenous VRE capacity that existed the year before"
          cc_iter(i,r,szn,t,cciter) "Actual capacity value in iteration cciter",
          curt_iter(r,h,t,cciter) "Actual curtailment in iteration cciter";

*Initialize surpold to zero
SurpOld(r,h,t) = 0;

*trimming the largest matrices to reduce file sizes
cost_vom(i,c,r,t)$(not valgen(i,c,r,t)) = 0;
cost_fom(i,c,r,t)$(not valcap(i,c,r,t)) = 0;
heat_rate(i,c,r,t)$(not valgen(i,c,r,t)) = 0;
co2_rate(i,c,r,t)$(not valgen(i,c,r,t)) = 0;


*==============================
* -- CC/Curt initialization --
*==============================

curt_avg(r,h,t) = 0;
curt_marg(i,r,h,t) = 0;
curt_mingen(r,h,t) = 0;
curt_storage(i,r,h,t)$storage(i) = Sw_CurtStorage ;
surpold(r,h,t) = 0;
tfix(t) = no;


$ifthen.int %timetype%=="int"

*================================================
* --- INTERTEMPORAL SETUP ---
*================================================

*increase maximum solve time
option reslim = 345600;

tmodel(t) = no;
tmodel(t)$(tmodel_new(t)$(yeart(t)<=%endyear%)) = yes;

*Cap the maximum CC in the first solve iteration
cc_avg(i,r,szn,t)$(rsc_i(i)$(cc_avg(i,r,szn,t)>0.4)$wind(i)) = 0.4;
cc_avg(i,r,szn,t)$(rsc_i(i)$(cc_avg(i,r,szn,t)>0.6)$pv(i)) = 0.6;

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

*marginal capacity value not used in intertemporal case
m_cc_mar(i,r,szn,t) = 0;

*static capacity value for existing capacity not used in intertemporal case
cc_old(i,r,szn,t) = 0;

$endif.int


*======================
* --- CC PY SETUP ---
*======================
*This is throwing errors on HPC, commenting out for now
$if NOT dexist E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%pickles $call 'mkdir E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%pickles';

* create PKL files that are used in all solve years cc_py calculations
execute_unload 'E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%pickles%ds%pickle_prep.gdx'   rb, r_rs, r_region;
execute 'python D_8760%ds%d0_pickle_prep.py %HourlyStaticFile% %case%'

execute_unload 'D_8760%ds%r_rs.gdx'   r_rs;

execute_unload 'C_Solve%ds%alldat.gdx';
