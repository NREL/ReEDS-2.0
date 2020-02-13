$title 'ReEDS 2.0'


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

* --- print timing profile ---
option profile = 3
option profiletol = 0

* --- define the input file directory ---
$setglobal input_folder '%gams.curdir%%ds%inputs'

*==========================
* --- Load Switches ---
*==========================
* The following are scalars used to turn on or off various components of the model.
* They are assigned via global switches in cases.csv
* For binary switches, [0] is off and [1] is on.

Scalar
Sw_GrowthRel     "Switch for the relative growth constraint"                       /%GSw_GrowthRel%/,
Sw_GrowthAbs     "Switch for the absolute growth constraint"                       /%GSw_GrowthAbs%/,
Sw_OpRes         "Switch to turn on operating reserve constraint"                  /%GSw_OpRes%/,
Sw_OpResTrade    "Switch to allow trading operating reserves between regions"      /%GSw_OpResTrade%/,
Sw_Refurb        "Switch to allow refurbishments"                                  /%GSw_Refurb%/,
Sw_PRM           "Switch to turn on planning reserve margin constraint"            /%GSw_PRM%/,
Sw_PRMTrade      "Switch to allow trading planning reserve margin between regions" /%GSw_PRMTrade%/,
Sw_Storage       "Switch to allow storage"                                         /%GSw_Storage%/,
Sw_CurtStorage   "Fraction of storage charging that counts toward reducing curtailment" /%GSw_CurtStorage%/,
Sw_FuelSupply    "Switch for fuel supply constraint"                               /%GSw_FuelSupply%/,
Sw_Prescribed    "Switch for prescribed capacity additions"                        /%GSw_Prescribed%/,
Sw_RECapMandate  "Switch for RE capacity targets"                                  / %GSw_RECapMandate%/,
Sw_REGenMandate  "Switch for RE generation targets"                                /%GSw_REGenMandate%/,
Sw_TechPhaseOut  "Switch for forced phase out of select technologies"              /%GSw_TechPhaseOut%/,
Sw_Retire        "Switch allowing endogenous retirements"                          /%GSw_Retire%/,
Sw_REdiversity   "Switch for geographic diversity constraint for RE additions"     /%GSw_REdiversity%/,
Sw_MinGen        "Switch for min loading constraint"                               /%GSw_MinGen%/,
Sw_CarbonTax     "Switch for CO2 tax"                                              /%GSw_CarbonTax%/,
Sw_CO2Limit      "Switch for national CO2 emissions limit"                         /%GSw_CO2Limit%/,
Sw_ValStr        "Switch for valuestreams analysis"                                /%GSw_ValStr%/,
Sw_CCcurtAvg     "Switch to select method for average curt/CC calculations"        /%GSw_CCcurtAvg%/,
Sw_Loadpoint     "Switch to use a loadpoint for the intertemporal case"            /%GSw_Loadpoint%/
;


*==========================
* --- Model Boundaries ---
*==========================
set
    allt                                  "all potential years"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%year_set.csv
          /,
    t                                     "full set of years"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%year_set.csv
          /,
    tmodel
          /

$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%modeledyears_set.csv

          /,
    yearafter "set to loop over for the final year calculation - number of years modeled"
          /1*30/,
    h                                     "time slices"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%h_set.csv
          /,
    peaksznh(h)                            "peak season time slices"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%peaksznh_set.csv
          /,
    szn                                   "seasons"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%szn_set.csv
          /,
    h_szn(h,szn)                          "hours in each season"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%h_szn_set.csv
$offdelim
          /,
    r                                     "all regions, includes BAs and resource regions"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%BA_set.csv
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%rs_set.csv
          /,
    rb(r)                                   "balancing areas"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%BA_set.csv
          /,
    rs(r)                                   "renewable resource regions"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%rs_set.csv
          /,
    region                                   "operating regions"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%region_set.csv
          /,
    country                               "country regions"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%country_set.csv
          /,
    hierarchy(r,region,country)              "establish hierarchy between regions"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%hierarchy_set.csv
$offdelim
          /,
    rfeas(r)                              "BAs to include in the model"
           /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%BA_set.csv //change to BA_set_toy.csv to run subset of regions
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%rs_set.csv
           /,
    countryfeas(country)                  "countries included in the model"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%country_set.csv
          /,
    dummy                             "set used for initalization of numerical sets" / 0*10000 /
          ;

alias(t,tt,ttt);
alias(t,yy,yyy);
alias(h,hh);
alias(r,rr);
alias(region,rregion);
alias(rs,rss);
alias(szn, sznszn);
alias(dummy,adummy);

set
    att(allt,t)                           "mapping set between allt and t" ,
    tfirst(t)                             "first year",
    tlast(t)                              "last year",
    tprev(t,tt)                           "previous modeled tt from year t",
    tfix(t)                               "years to fix variables over when summing over previous years",
    r_region(r,region)                    "map between BAs and regions",
    r_country(r,country)                  "map bewteen BA and country" ,
    rfeas_cap(r)                          "modeled capacity regions"
 ;


scalar
       yeart_tfirst "used for present value factor (PVF) calculation to aggregate capital and onm PVF",
       yeart_tlast  "used for present value factor (PVF) calculation to aggregate capital and onm PVF",
       check        "used for present value factor (PVF) calculation to aggregate capital and onm PVF",
       numclass     "number of new technology classes" /%numclass%/,
       numhintage   "number of bins for existing technologies grouped based on performance and cost" /%numhintage%/
       ;

parameter
      temppvf        "used for present value factor (PVF) calculation to aggregate capital and onm PVF",
      yeart(t)       "numeric value for year",
      year(allt)     "numeric year value for allt",
      mindiff(t)     "minimum difference between t and all other tt that are in tmodel(t)",
      cap_agg(r,r)   "mapping between r,rb,and rs"
;

yeart(t) = t.val;
year(allt) = allt.val;

* input tables
table r_rs(r,rs) "mapping set between BAs and renewable resource regions"
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%r_rs_map.csv
$offdelim
;

*#########################
* --- calculations ---

* initialize numeric values for years
yeart(t) = t.val;
year(allt) = allt.val;

$if not set endyear $setglobal endyear 2047
tmodel(t)$(yeart(t)>%endyear%)= no;

*initialize boundaries on model years
att(allt,t)$(year(allt)=yeart(t)) = yes;
tfirst(t)$(ord(t)=1) = yes;
tlast(t)$(ord(t)=smax(tt,ord(tt))) = yes;

*reset the first and last year indices of the model
tprev(t,tt) = no;
*now get rid of all non-immediately-previous values
tprev(t,tt)$(tmodel(t)$tmodel(tt)$(tt.val<t.val)) = yes;
mindiff(t)$tmodel(t) = smin(tt$tprev(t,tt),t.val-tt.val);
tprev(t,tt)$(tmodel(t)$tmodel(tt)$(t.val-tt.val<>mindiff(t))) = no;

* initialize boundaries on model areas
r_region(r,region)$sum((country)$hierarchy(r,region,country),1) = yes;
r_country(r,country)$sum((region)$hierarchy(r,region,country),1) = yes;

* initialize placeholders for PVF calcualtion
yeart_tfirst = 0;
yeart_tlast = 0;
check = 0;

cap_agg(rb,rb)$sameas(rb,rb) = yes;
cap_agg(r,rs)$(r_rs(r,rs)$(not sameas(rs,"sk"))) = yes;

rfeas_cap(r)$(rb(r) or rs(r)) = yes;

*=============================
* --- Generation Technologies ---
*=============================
set
    i            "generation technologies"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%gen_tech_set.csv
          /,

    prescribed_rsc_set(i)            "technologies available to meet rsc capacity targets"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%prescribed_rsc_set.csv
          /,

    i_subtech    "technology subset categories "
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%i_subtech_set.csv
          /,
    c            "technology class"
          / init-1*init-%numhintage%,
           prescribed,
           new1*new%numclass%/,
    initc(c)     "inital technologies"
          /init-1*init-%numhintage%/,
    existc(c)    "initial and prescribed classes"
          /init-1*init-%numhintage%, prescribed/,
    newc(c)      "new technology set"
          /new1*new%numclass%/,
    ct_corr(c,t) "mapping set between c and t",
    coal(i)      "technologies that use coal",
    gas(i)       "tech that uses gas",
    conv(i)      "conventional generation technologies",
    vre(i)       "variable renewable energy technologies",
    rsc_i(i)     "technologies based on resource supply curves",
    wind(i)      "wind generation technologies",
    upv(i)       "upv generation technologies",
    dupv(i)      "dupv generation technologies",
    storage(i)   "storage technologies",
    hydro(i)     "hydro technologies",
    hydro_d(i)   "dispatchable hydro technologies",
    hydro_nd(i)  "non-dispatchable hydro technologies",
    pv(i)        " pv technologies",
    ict(i,c,t) "mapping set between i c and t - for new technologies"
    ;

alias(i,ii);
alias(c,cc);

scalar
    numnewc "number of new technology classes" /%numclass%/ ,
    ypc     "number of years per technology grouping",
    minyear "minimum year in the solution year set",
    temps   "temp step for looping over tt set when defining correlation set between newc and t as ct_corr" /1/
    ;

parameter
    tempt(t)      "placeholder for years since first year",
    tempc(newc)   "temporary calculation to help in mapping newc to years",
    countnc(i,newc) "number of years in each newc set"
;

* input tables
Table i_subsets(i,i_subtech) "technology subset lookup table"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%tech_subset_table.csv
$offdelim
;

Table ict_num(i,t) "number associated with bin for ict calculation"
$ondelim
$include A_Inputs%ds%inputs%ds%generators%ds%ict.csv
$offdelim
;

set
   rsc_agg(i,ii)            "mapping different vintages of the same tech type";

*######################
* --- calculations ---

ict(i,newc,t)$(ord(newc)=ict_num(i,t)) = yes;

*ypc is calculated as the rounded difference between
*the maximum and minimum years divided by the number of groups
*e.g. if numnewc = 5 and going 2015-2050, ypc = 2050-2015 / 5 = 7 years per grouping
ypc = round( (1 + smax(t,yeart(t)) - smin(t,yeart(t)))  / numnewc,0);
minyear = sum(t$tfirst(t),yeart(t));

tempt(t) = (yeart(t) - minyear) + 1;
tempc(newc) = ord(newc) * ypc * numnewc;

loop(tt,
   ct_corr(newc,tt)$(ord(newc) = temps) = yes;
   temps$((mod(tempt(tt),ypc)=0)$(temps<smax(newc,ord(newc)))) = temps + 1;
);

*add 1 for each t item in the ict set
countnc(i,newc) = sum(t$ict(i,newc,t),1);

* --- define technology subsets ---
COAL(i)     = YES$i_subsets(i,'COAL') ;
GAS(i)      = YES$i_subsets(i,'GAS') ;
CONV(i)     = YES$i_subsets(i,'CONV') ;
VRE(i)      = YES$i_subsets(i,'VRE') ;
RSC_i(i)    = YES$i_subsets(i,'RSC') ;
WIND(i)     = YES$i_subsets(i,'WIND') ;
UPV(i)      = YES$i_subsets(i,'UPV') ;
DUPV(i)     = YES$i_subsets(i,'DUPV') ;
STORAGE(i)  = YES$i_subsets(i,'STORAGE') ;
HYDRO(i)    = YES$i_subsets(i,'HYDRO') ;
HYDRO_D(i)  = YES$i_subsets(i,'HYDRO_D') ;
HYDRO_ND(i) = YES$i_subsets(i,'HYDRO_ND') ;
pv(i)$(UPV(i) or DUPV(i)) = YES;

rsc_agg(i,ii)$(rsc_i(i)$sameas(i,ii)) = yes;



*===========================
* --- Generation Parameters ---
*===========================
parameter
      co2_rate_fuel(i)     "emissions rate of fuel metric ton per GJ"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%fuels%ds%co2_rate_fuel.csv
$offdelim
          /,
      maxage(i)                 "maximum age for technologies"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%maxage.csv
$offdelim
          /,
      heat_rate(i,c,r,t)        "--GJ per MWh-- avg heat rate of existing fleet", // from data_conv table
      co2_rate_fuel(i)          "--metric tons CO2 per GJ-- CO2 emission rate of fuel", //calc from data_co2_rate_fuel
      co2_rate(i,c,r,t)         "--metric tons CO2 per MWh-- CO2 emissions rate", //calc from heat_rate, co2_rate_fuel
      rsc_min_gen(t)          "---fraction--- minimum fraction of rsc (limited by prescribed_rsc_set) generation in total generation mix by year"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%rsc_min_gen_fraction_linear.csv
$offdelim
          /,
      rsc_min_cap(t)          "---MW--- minimum capacity of rsc (limited by prescribed_rsc_set) capacity by year"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%rsc_min_capacity.csv
$offdelim
          /
;


* input tables
table data_conv(allt,i,*)       "data for all technologies not defined in binned_capacity: cost_vom, cost_fom, cost_cap, heat_rate"  //

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%%TechCost_file%
$offdelim
;


*==========================
* --- Generation Capacity ---
*==========================
set
    tg                    "tech groups for growth constraints"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%tg_set.csv
          /,
    tg_i(tg,i)            "technologies that belong in tech group tg"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%tg_i_set.csv
$offdelim
          /,
    tf                    "tech groups for fuel supply constraints"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%tf_set.csv
          /,
  tf_i(tf,i)            "technologies that belong in tech group tf"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%tf_i_set.csv
$offdelim
          /,
    refurbtech(i)         "technologies that can be refurbished"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%refurbtech_set.csv
          /,
    retiretech(i,c,r,t)         "technologies that can be retire",
    valoldrsc(i,c,r,rs,t)       "valid set of existing/prescribed rsc technologies",
    inv_cond(i,c,t,tt)          "investment conditional" ,
    inv_cond_prescrRE(i,c,t,tt) "investment conditional for prescribed RSC plants",
    valcap(i,c,r,t)             "technologies that can be built", //initialized as empty and populated in c_solveprep
    valgen(i,c,r,t)             "technologies that can generate power", //initialized as empty and populated in c_solveprep
    prescriptivetech(i)         "prescribed technologies to be located endogenously"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%prescriptive_tech_set.csv
          /
    ;


parameter
          capacity_exog(i,c,r,rs,t)        "--MW-- exogenously specified capacity", //calc from caponrsc, prescribedretirments, binned_capacity
          avail_retire_exog_rsc            "--MW-- available retired rsc capacity for refurbishments",
          required_prescriptions(i,r,t)    "--MW-- prescribed RSC cap that ReEDS will decide on location", // derived with prescribedrsc
          prescribedretirements(t,r,i,*)   "--MW-- raw prescribed capacity retirement data", // default to 0; can be added as needed
          phase_out_year(i)                "year when select technology must be completely retired from system"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%tech_phase_out_schedule.csv
$offdelim
          /
;

set phase_out_tech(i);
phase_out_tech(i) = phase_out_year(i)

scalar retireyear  "First year for economic retirements" /%retireyear%/;

* input tables

table  binned_capacity(allt,i,r,c,*)    "existing capacity binned by vom cost"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%binned_capacity.csv
$offdelim
;

table capnonrsc(i,r,*) "--MW-- raw capacity data for non-RSC tech"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%capnonrsc.csv
$offdelim
;

table caprsc(i,r,rs,*) "--MW-- raw capacity data for RSC techs"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%caprsc.csv
$offdelim
;

table prescribednonrsc(t,i,r,*) "--MW-- raw prescribed capacity data for non-RSC tech"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%prescribednonrsc.csv
$offdelim
;

table prescribedrsc(t,i,r,rs,*) "--MW-- raw prescribed capacity data for RSC tech"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%prescribedrsc.csv
$offdelim
;

*######################
* --- calculations ---

inv_cond(i,c,t,tt) = no;

* all prescribed retirements included in binned_capacity
prescribedretirements(t,r,i,'value') = no;

* existing capacity equals all existing capacity less retirements (subtracted later)
* here we use the max of zero or that number to avoid any errors with variables that are >= zero
* also have expiration of capital if t - tfirst is greater than the maximum age
* note the first conditional limits this calculation to units that
* do NOT have their capacity binned by heat rates
capacity_exog(i,"init-1",r,"sk",t)$(yeart(t)-sum(tt$tfirst(tt),yeart(tt))<maxage(i)) =
                                 max(0,capnonrsc(i,r,"value") ) - sum(tt$(tt.val<=t.val),  prescribedretirements(tt,r,i,"value") ) ;

*reset any exogenous capacity that is also specified in binned_capacity
*as these are computed based on bins
capacity_exog(i,c,r,rs,t)$(sum((rr,cc,allt),binned_capacity(allt,i,rr,cc,"cap"))) = 0;

*all binned capacity is for rs == sk
capacity_exog(i,c,r,"sk",t)$(sum(allt,binned_capacity(allt,i,r,c,"cap"))) =
               sum(allt$att(allt,t),binned_capacity(allt,i,r,c,"cap")) ;

* existing rsc capacity with known r and rs locations assigned to init-1 class
*conditional here is due to no prescribed retirements for RSC tech
capacity_exog(i,"init-1",r,rs,t)$((yeart(t)-sum(tt$tfirst(tt),yeart(tt))<maxage(i))$(rsc_i(i) or storage(i)))
          = caprsc(i,r,rs,"value");

*prescribed capacity for non-rsc classes gets assigned to rs==sk
*this is the sum of future capacity that has not yet reached its maximum age
capacity_exog(i,"prescribed",r,"sk",t)$sum((tt)$((yeart(t)>=yeart(tt))$(yeart(t)-yeart(tt)<maxage(i))),prescribednonrsc(tt,i,r,"value")) =
         sum((tt)$((yeart(t)>=yeart(tt))$(yeart(t)-yeart(tt)<maxage(i))),prescribednonrsc(tt,i,r,"value"));

*prescribed capacity for rsc technologies follows the same logic but now
*can be attributed to a specific rs (and for some techs rs still equals sk)
capacity_exog(i,"prescribed",r,rs,t)$sum(tt$((yeart(t)>=yeart(tt))$(yeart(t)-yeart(tt)<maxage(i))), prescribedrsc(tt,i,r,rs,"value")) =
         sum(tt$((yeart(t)>=yeart(tt))$(yeart(t)-yeart(tt)<maxage(i))), prescribedrsc(tt,i,r,rs,"value"));


* for first year, required prescriptions is additions plus existing capacity
required_prescriptions(i,r,t)$(prescriptivetech(i))
      = sum(tt$((yeart(t)>=yeart(tt))$(yeart(t)-yeart(tt)<maxage(i))), sum(rs, prescribedrsc(tt,i,r,rs,"value")$(sameas(rs,"sk")) ));

* initialize as empty; these will be populated later
valcap(i,c,r,t) = no;
valgen(i,c,r,t) = no;

* heat rate for new capacity
heat_rate(i,c,r,t)$[CONV(i)$rb(r)] = sum(allt$att(allt,"2017"),data_conv(allt,i,'heat_rate'));


* heat rate for new investments equal to average over that investment class
* e.g. class new1 applies to investments from 2017-2022; the heat rate for new1 equals the average heat rate over this period
heat_rate(i,newc,r,t)$[countnc(i,newc)$CONV(i)$rb(r)] = sum(tt$ict(i,newc,tt),sum(allt$att(allt,tt),data_conv(allt,i,'heat_rate'))) / countnc(i,newc) ;

co2_rate(i,c,rs,t) = no;
co2_rate(i,c,rb,t) = round(heat_rate(i,c,rb,t) * co2_rate_fuel(i),6);


*zero out the capacity for prescribed technologies that are required to be built as endogenous choices
capacity_exog(i,"prescribed",r,"sk",t)$prescriptivetech(i) = 0;

avail_retire_exog_rsc(i,c,r,rs,t) = 0;

loop(tt,
*if you've declined in value
    avail_retire_exog_rsc(i,c,r,rs,t)$(refurbtech(i)$rfeas(r)$(capacity_exog(i,c,r,rs,t-1) > capacity_exog(i,c,r,rs,t))) =
        capacity_exog(i,c,r,rs,t-1)-capacity_exog(i,c,r,rs,t);
  );


* initialize retiretech to no for all technologies
* this is overwritten in solveprep for specific techs and classes that can be retired
retiretech(i,c,r,t) = no;

*=======================================================
* --- Generation Availability (outage, capacity factor) ---
*=======================================================

scalar
       distloss         "distribution losses from bus to final consumption"  /0/
       ;

parameter
      foq(i)                  "forced outage rate"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%foq.csv
$offdelim
          /,
      poq(i)                  "planned outage rate"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%poq.csv
$offdelim
          /,
      cf_adj_hyd(i,szn,r)     "seasonal capacity factor adjustment for hydro"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%cf_adj_hydro.csv
$offdelim
          /,
      outage(i,h)             "outage rate", // calc from foq, poq, peaksznh
      cf_rsc(i,r,rs,h)      "capacity factor for rsc tech - t index included for use in CC/curt calculations" // calc from cf_in, for dupuv also includes distloss, for hydro includes cf_hyd_szn_adj and cf_hyd
 ;


table cf_in(r,rs,i,h,*) "capacity factors for renewable technologies"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%cfout.csv
$offdelim
;

*######################
* --- calculations ---

outage(i,h) = 1;

outage(i,h)$(foq(i)) = (1-foq(i)) * (1-poq(i)$(not peaksznh(h)) * 365 / 273);

*initial assignment of capacity factors
cf_rsc(i,r,rs,h)$(cf_in(r,rs,i,h,'value')$r_rs(r,rs)) = cf_in(r,rs,i,h,'value');

* only need to compute this for rs==sk... otherwise gets huge
* capacity factors for hydro are seasonal
cf_rsc(i,r,"sk",h)$hydro_d(i)  = sum(szn$h_szn(h,szn),cf_adj_hyd(i,szn,r));
cf_rsc(i,r,"sk",h)$hydro_nd(i) = sum(szn$h_szn(h,szn),cf_adj_hyd(i,szn,r));


*==========================
* --- Transmission ---
*==========================
set
    region_rregion_set(r,rr)               "mapping set between BAs that trade across regions"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%region_rregion_set.csv
$offdelim
          /,
  vc                                  "voltage class"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%vc_set.csv
          /,
  trtype                              "transmission capacity type"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%trtype_set.csv
          /,
  futuretran_cat                      "categories of near-future transmission capacity"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%futuretran_cat_set.csv
          /,
  include_future_tran(futuretran_cat) "categories to include as prescribed investments (i.e., certain, possible)"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%include_futuretran_set.csv
          /,
  tranvar                             "variables for transmission substation supply curves"
        /cap, cost/,
  shfeas(r,rr)                        "shipment feasibility set - ie transmission is possible from r to rr",
  tranfeas(r,vc)                      "set to declare what voltage classes are feasible in regions",
  routes(r,rr,trtype,t)               "final conditional on transmission feasibility",
  routes_region(r,rr,trtype,t)        "transmission feasibility between regions"
  ;

scalar
       Trans_Intercost  "--INR-- transmission costs for interconnection substation" /0/,
       tranloss_permile "--% per 100 km-- transmission loss for regional trade" /0/ // CEA demand forecasts includes T&D losses
       ;

parameter
    coordx(r)                       "x coordinate for BA"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%coordx.csv
$offdelim
          /,
    coordy(r)                       "y coordinate for BA"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%coordy.csv
$offdelim
          /,
    InterTransCost(r)               "--INR/MW/km-- cost of transmission capacity for each BA"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%inter_transcost.csv
$offdelim
          /,
    trancap(r,rr,trtype)          "--MW-- transmission capacity by type"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%trancap.csv
$offdelim
          /,
    trancost(r,tranvar,vc)          "transmission substation supply curve by voltage class"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%transmission%ds%trancost.csv
$offdelim
          /,

    distance(r,rr)                  "--km-- distance between BAs" ,
    trancap_exog(r,rr,trtype,t)     "--MW-- exogenous transmission capacity - final value used in the model",
    tranloss(r,rr)                  "transmission loss (%) between r and rr",
    futuretran(r,rr,futuretran_cat,tt,trtype) "--MW-- planned tx additions"
;


*######################
* --- calculations ---

trancap(r,rr,trtype) = trancap(r,rr,trtype) + trancap(rr,r,trtype);
shfeas(r,rr)$sum(trtype,trancap(r,rr,trtype)) = yes;
tranfeas(r,vc)$(trancost(r,"cap",vc)>0) = yes;
futuretran(r,rr,futuretran_cat,tt,trtype) = 0;

trancap_exog(r,rr,trtype,t) =
*initial transmission capacity
                           trancap(r,rr,trtype)
*plus all new/planned transmission capacity
                           + sum((tt,futuretran_cat)$(
                                      (tt.val<=t.val)
                                      $include_future_tran(futuretran_cat)),
                                      futuretran(r,rr,futuretran_cat,tt,trtype)
                                 )
;

routes(r,rr,trtype,t)$(trancap_exog(r,rr,trtype,t) or trancap_exog(rr,r,trtype,t)) = yes;
routes(r,rr,trtype,t)$(sum((tt,futuretran_cat)$((yeart(tt)>=yeart(t))
                        $(not include_future_tran(futuretran_cat))),futuretran(r,rr,futuretran_cat,tt,trtype))) = yes;

routes(rr,r,trtype,t)$(routes(r,rr,trtype,t)) = yes;

routes_region(r,rr,trtype,t)$(routes(r,rr,trtype,t)$region_rregion_set(r,rr)) = yes;
routes_region(rr,r,trtype,t)$(routes_region(r,rr,trtype,t)) = yes;

distance(r,rr) = sqrt(sqr((coordx(r)-coordx(rr)))+sqr((coordy(r)-coordy(rr))));

tranloss(r,rr)$[rb(r)$rb(rr)] = tranloss_permile * distance(r,rr) / 100;

*set transmission losses to 1% per MW since having 0 could give weird results.
tranloss(r,rr)$[rb(r)$rb(rr)] = .01 ;

*==========================
* --- Load ---
*==========================
parameter
      hours(h)            "--hours-- hours in each time block"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%demand%ds%%Hours_file%
$offdelim
          /,
      lmnt(r,h,t)         "--MW-- load by region hour and year"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%demand%ds%%Load_file%
$offdelim
          /,
      peakdem_region(region,szn,t)        "--MW-- peak demand by region and year"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%demand%ds%%PeakDemRegion_file%
$offdelim
          /,
      lmnt0(r,h,t)        "--MW-- original load by region hour and year - unchanged by demand side"
;

*######################
* --- calculations ---

lmnt0(r,h,t) = lmnt(r,h,t);

set maxload_szn(r,h,t,szn) "hour h is the maximum load in each season";

parameter lmnt_szn(r,h,t,szn);
lmnt_szn(r,h,t,szn)$(h_szn(h,szn)) = lmnt(r,h,t);

maxload_szn(r,h,t,szn)$(lmnt_szn(r,h,t,szn)=smax(hh$h_szn(hh,szn),lmnt_szn(r,hh,t,szn))) = yes;
maxload_szn(rs,h,t,szn) = no;

*summarize by region
parameter lmnt_region(region,h,t) "--MW-- load by region timeslice and year";
lmnt_region(region,h,t) = sum(r$r_region(r,region),lmnt(r,h,t))


*==========================
* --- Fuels ---
*==========================
set
    f              "fuel types"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%fuels%ds%fuel_set.csv
          /,
    fuel2tech(f,i) "mapping between fuel types and generators"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%fuels%ds%fuel2tech.csv
$offdelim
          /
    ;

parameter
    fprice(allt,f)    "--INR/GJ-- fuel prices"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%fuels%ds%fprice.csv
$offdelim
          /,
    fuel_limit(tf,t)    "--GJ/yr-- annual limits on fuel supply"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%fuels%ds%%FuelLimit_file%
$offdelim
          /,
    fuel_price(i,r,t) "INR/GJ - fuel prices used in the model"
          ;

scalar
       slackfuel_price "--INR/GJ-- price of Naptha used in gas plants when gas supplies are low"   /400/ ;

slackfuel_price = slackfuel_price*1e6;

parameter fuel_file;

*######################
* --- calculations ---

*rescale fuel limit
fuel_limit(tf,t) = fuel_limit(tf,t)*1e-6;

fuel_price(i,r,t)$sum(f$fuel2tech(f,i),1) = sum((f,allt)$(fuel2tech(f,i)$(year(allt)=yeart(t))), fprice(allt,f));

*map fuel prices to generation technologies
fuel_price(i,r,t)$(sum(f$fuel2tech(f,i),1)$(not fuel_price(i,r,t))) = sum(rr$fuel_price(i,rr,t),fuel_price(i,rr,t)) / max(1,sum(rr$fuel_price(i,rr,t),1));


*==========================
* --- Financial---
*==========================
set
    CSched               "construction schedules"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%CSched.csv
          /,
    CSCorr(dummy,CSched) "correlation between a numerical input and the text-specified construction schedule"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%CSCorr.csv
$offdelim
          /,
    finparam             "financial parameters (LT, DepSched, FLT, CS)"
          /LT "lifetime", DepSched "depreciation schedule", FLT "financial lifetime", CS "construction schedule (numerical)"/, // cols for FinAssumptions table
    ConsSched(i,CSched)  "map construction schedules to technologies"
    ;

* set the discount such that the pvf_onm calculation reflects the inverse of the 20-year crf
* i.e. sum_t (1/(1+discount_rate)^t) == 1/crf
scalar
       discount_rate "--unitless-- discount rate"                               /0.09/,
       growth_rate    "specified growth rate for terminal investment constraint" /0.01/,
       decay_rate     "decay rate for terminal investment condition" /0.01/,
       TaxRate        "federal tax rate" /0.346/,
       InflationRate  "inflation rate" /1.045/,
       RealDiscount   "real discount rate" /1.09/,
       NomIRate       "nominal interest rate" /1.115/,
       DebtCovRat     "debt coverage ratio" /1.4/,
       NomRROE        "Nominal RROE" /1.155/,
       initdebtfrac   "reference debt fraction " /0.7/,
       RROE           "return rate on equity", // calc below
       CRF_s          "scalar for CRF"            /0.100501/,
       cost_scale "cost scaling parameter" / 1e-12 / ;
       ;

parameter


         realdisc(i,t)         "real discount rate" ,// assume same as RealDiscount
         ITC_Frac(country,t,i) "fractional investment tax credit" ,
         firstyear(i)          "first year where economic investment is allowed"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%firstyear.csv
$offdelim
          /,
         FinAssumptions(i,finparam) "input table for finance lifetime, finance period, depscheduletech"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%FinAssumptions.csv
$offdelim
          /,
          pvf(t)                "--unitless-- present value factor" ,
          pvf_capital(t)        "present value factor of capital costs",
          pvf_onm(t)            "present value factor for o&m costs" ,
          DebtFrac(country,i,t) "debt fraction",
          FinanceLifetime(i)    "financed lifetime", // from finassumptions table
          FinancePeriod(i)      "finance period", // from finassumptions table
          DepScheduleTech(i)    "depreciation schedule", // from finassumptions table
          AccInterest(dummy)    "accumulated interest", // calc based on taxrate and NomIrate
          nomdisc(i,t)          "nominal discount rate", // calc based on realdisc and inflation rate
          CRF_i(i)              "capital recovery factor", // calc based on monirate, financeperiod
          CRF_dnl               "capital recovery factor dn,L (tax situation)", // calc based on mondisc and finance period
          CRF_dnIL              "capital recovery factor DNIL", // calc based on realdisc, inflation rate, nomirate
          PVdep(i,t)            "present value of depreciation", //calc based on depschedule, depscheduletech, nomdisc
          ccmult(i)             "construction cost multiplier", // calc based on schedule, conssched, accinterest
          ValueDebt(i,t)        "after tax value of debt", //calc based on crf(i), taxrate, crf_dnl, monirate, CRF_dnIL
          FinMult (country,i,t) "Final financial mulpactiplier",  // calc based on ccmult, taxrate, deptfract, valuedebt, pvdeb
          CRF(t)                "20-year Capital Recovery Factor"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%crf_t_set.csv
$offdelim
          /
;


* input tables
Table Schedule(CSched,dummy) "proportion of project completed by year dummy"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%Schedule.csv
$offdelim
;

Table DepSchedule(dummy,adummy) "depreciation schedule by financial lifetime"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%DepSchedule.csv
$offdelim
;



*#########################
* --- calculations ---

* method to translate numerical inputs to text sets of CSched
ConsSched(i,CSched)$sum(dummy$(cscorr(dummy,CSched)$(dummy.val=FinAssumptions(i,"cs"))),1) = yes;

RROE = NomRROE / InflationRate;

realdisc(i,t) = RealDiscount;
ITC_Frac(country,t,i) = 0;

pvf(t) = 1/power((RealDiscount), ord(t)-1);

DebtFrac(country,i,t) = initdebtfrac;

FinanceLifetime(i) = FinAssumptions(i,"LT");
FinancePeriod(i)   = FinAssumptions(i,"FLT");
DepScheduleTech(i) = FinAssumptions(i,"DepSched");

AccInterest(dummy)$(dummy.val<=9) = 1+(1-TaxRate)*(NomIrate**(dummy.val+0.5)-1);

nomdisc(i,t) = realdisc(i,t) * InflationRate;

CRF_i(i) = (NomIRate-1) / (1-1/(NomIRate)**FinancePeriod(i));

CRF_dnl(i,t) = (nomdisc(i,t) -1) / (1-1/(nomdisc(i,t)**FinancePeriod(i)));

CRF_dnIL(i,t) = (realdisc(i,t)*InflationRate/NomIrate - 1);
CRF_dnIL(i,t) = CRF_dnIL(i,t)/(1-(1+CRF_dnIL(i,t))**(-FinancePeriod(i)));

PVDep(i,t) = sum((dummy,adummy)$((DepSchedule(dummy,adummy))$(adummy.val=DepScheduleTech(i))),
   DepSchedule(dummy,adummy)/((nomdisc(i,t))**(dummy.val)));

ccmult(i) = sum((CSched,dummy)$(Schedule(CSched,dummy)$ConsSched(i,CSched)$AccInterest(dummy)),
                  Schedule(CSched,dummy)*AccInterest(dummy));

ValueDebt(i,t) = CRF_i(i) * (1-TaxRate)/CRF_dnl(i,t) + TaxRate * (CRF_i(i)-(NomIRate-1))/NomIRate/CRF_dnIL(i,t);

*note given the assumptions, crf' / crf == 1 and is not included at the end of this calculation
FinMult(country,i,t) = (ccmult(i) / (1-TaxRate)) * (((1-DebtFrac(country,i,t)) + DebtFrac(country,i,t) * ValueDebt(i,t) -TaxRate * PVDep(i,t)));


*==========================
* --- Costs---
*==========================
parameter
          vom_init(i,r)         "--$ per MWh-- variable OM" //
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%vom_init.csv
$offdelim
          /,
          coal_transport(r)     "--$ per MWh-- transport charge adder for coal plants"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%transport_charge.csv
$offdelim
          /,
          capmult(r,i) "capital cost multiple by region and technology"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%capmult.csv
$offdelim
          /,
          cost_vom(i,c,r,t)         "--INR/MWh-- variable OM" , //from vom_init and binned_capacity
          cost_fom(i,c,r,t)         "--INR/MW/yr-- fixed OM" ,// from data_conv table
          cost_cap(i,t)             "--INR/MW-- capital cost", // from data_conv table
          cost_cap_fin_mult(r,i,t)  "final capital cost multiplier for regions and technologies - used in the objective function"
          ;


*######################
* --- calculations ---

*vom cost initially based on national average values
cost_vom(i,c,r,t) = sum(allt$att(allt,t),data_conv(allt,i,"cost_vom"));

* overwrite with BA specific costs if we have them
cost_vom(i,c,r,t)$vom_init(i,r) = vom_init(i,r);

*VOM costs by c are averaged over the class's associated
*years divided by those values
cost_vom(i,newc,r,t)$countnc(i,newc) = sum(tt$ict(i,newc,tt),sum(allt$att(allt,tt),cost_vom(i,newc,r,t))) / countnc(i,newc) ;

*VOM costs for plants in binned_capacity
cost_vom(i,c,r,t)$(sum(allt$att(allt,t),binned_capacity(allt,i,r,c,"wVC"))) =
                    sum(allt$att(allt,t),binned_capacity(allt,i,r,c,"wVC"));

*VOM costs for new coal plants based on national average plus transport cost
cost_vom(i,newc,r,t)$i_subsets(i,'COAL') = sum(allt$att(allt,t),data_conv(allt,i,"cost_vom")) + coal_transport(r);

* remove invalid combinations of regions and technologies (e.g., CCGT-GAS cost in rs = 1)
cost_vom(i,c,rb,t)$vre(i) = no;
cost_vom(i,c,rs,t)$(not vre(i)) = no;

*previous calculation (without tech binning)
cost_fom(i,c,r,t) = sum(allt$att(allt,t),data_conv(allt,i,"cost_fom"));

*fom costs for a specific bintage is the average over that bintage's time frame
cost_fom(i,newc,r,t)$countnc(i,newc) = sum(tt$ict(i,newc,tt),sum(allt$att(allt,tt),cost_fom(i,newc,r,t))) / countnc(i,newc) ;

cost_fom(i,initc,r,t) = sum(tt$tfirst(tt),cost_fom(i,initc,r,tt));

* remove invalid combinations of regions and technologies (e.g., CCGT-GAS cost in rs = 1)
cost_fom(i,c,rb,t)$vre(i) = no;
cost_fom(i,c,rs,t)$(not vre(i)) = no;

*previous calculation (without tech binning)
cost_cap(i,t) = sum(allt$att(allt,t),data_conv(allt,i,"cost_cap"));


*this creates a financial multiplier for all years and technologies as the product of the
*the financial multiplier and the regional capital cost multiplier
cost_cap_fin_mult(rb,i,t)$(not vre(i)) = capmult(rb,i) * sum(country$r_country(rb,country),FinMult(country,i,t));
cost_cap_fin_mult(rs,i,t)$vre(i)  = capmult(rs,i) * sum(country$r_country(rs,country),FinMult(country,i,t));
*double-check to make sure there are no outliers
cost_cap_fin_mult(rb,i,t)$[(not vre(i))$(cost_cap_fin_mult(rb,i,t)=0)] = 1;
cost_cap_fin_mult(rs,i,t)$[vre(i)$(cost_cap_fin_mult(rs,i,t)=0)] = 1;

*======================================================
* --- RE supply curves, capacity value and curtailment ---
*======================================================
set
    rscbin                            "Resource supply curves bins"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%rscbin.csv
          /,
    rscvar                            "Resource supply curve parameters (capacity and cost)"
          /cap "capacity available", cost "cost of capacity"/,
    curt_params
          /alpha0, beta0/,
    rscfeas(r,rs,i,rscbin)            "feasibility set for r s i and bins", //calc from rsc_dat
    refurb_cond(i,c,r,rs,t,tt,rscbin) "set to indicate whether a tech and vintage combination from year tt can be refurbished in year t" // initialized below
    ;

alias(rscbin,arscbin);


scalar REdiversity  "Maximum fraction of annual VRE investments that can go in any one resource region" /%REdiversity%/;

parameter
          rsc_dat(r,rs,i,rscbin,rscvar)              "Resource supply curve data"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%rsc_dat.csv
$offdelim
          / ,
          remainder(i,r,rs)       "remaining amount of capacity in rscbin after existing stock has been deducted",
          curt_avg(r,h,t)         "--%-- average curtailment rate of all resources in a given year - only used in intertemporal solve",
          curt_old(r,h,t)         "--%-- average curtailment rate of resources already existing in a given year - only used in sequential solve",
          curt_marg(i,r,h,t)      "--%-- marginal curtail rate for new resources - only used in sequential solve",
          cc_old(i,r,szn,t)       "--MW-- capacity value for existing capacity - used in sequential solve similar to heritage reeds",
          cc_old_load(i,r,szn,t)  "--MW-- cc_old loading in from the cc_out gdx file",
          cc_mar(i,r,rs,szn,t)    "--%--  cc_mar loading inititalized to some reasonable value for the 2010 solve",
          cc_mar_load(i,r,szn,t)  "--%--  cc_mar loading in from the cc_out gdx file",
          cc_avg(i,r,szn,t)       "--%--  average fractional capacity value - used in intertemporal solve",
          cc_hydro(i,r,szn,t)     "--%--  average capacity value for hydro techs - not changed by 8760 method",
          cc_eqcf(i,c,r,rs,t)     "--%--  fractional capacity value based off average capacity factors - used without iteration with cc and curt scripts",
          curt_mingen(r,h,t)      "--%--  fraction of addition curtailment induced by increasing the minimum generation level",
          curt_mingen_load(r,h,t) "--%--  fraction of addition curtailment induced by increasing the minimum generation level, loaded from gdx file (so as to not overwrite existing values for non-modeled years)",
          curt_storage(i,r,h,t)   "--%--  fraction of curtailed energy that can be recovered by storage charging during that timeslice",
          surpold(r,h,t)          "--MW-- surplus from old capacity - used to calculate average curtailment for VRE techs",
          resourcescalar(i)       "scalar when multiple types of technologies that can be built on the same plot of land",
          rsc_copy                " copy of rsc_dat used to calculate remainder(i,r,rs)"
          ;


*######################
* --- calculations ---
*following set indicates which combinations of r, s, and i are possible
*this is based on whether or not the bin has capacity available
rscfeas(r,rs,i,rscbin)$rsc_dat(r,rs,i,rscbin,"cap") = yes;

refurb_cond(i,c,r,rs,t,tt,rscbin) = no;

remainder(i,r,rs) = sum(c, sum(t$tfirst(t), capacity_exog(i,c,r,rs,t)));

parameter rsc_copy;
rsc_copy(r,rs,i,rscbin,"cap")  = rsc_dat(r,rs,i,rscbin,"cap");
rsc_copy(r,rs,i,rscbin,"cost") = rsc_dat(r,rs,i,rscbin,"cost");

alias(rscbin,arb)

loop(arb,
    rsc_dat(r,rs,i,arb,"cap")$rscfeas(r,rs,i,arb) = max(0,rsc_dat(r,rs,i,arb,"cap") - remainder(i,r,rs));
    remainder(i,r,rs) = max(0,remainder(i,r,rs)-rsc_copy(r,rs,i,arb,"cap"))
);


* curtailment and capacity value
cc_old(i,r,szn,t) = 0;

*initialize cc_mar at some reasonable value
cc_eqcf(i,c,r,rs,t)$(r_rs(r,rs)$rsc_i(i)) =
  sum(h,hours(h) * cf_rsc(i,r,rs,h)) / sum(h,hours(h));

cc_eqcf(i,c,r,rs,t)$(hydro_d(i)$r_rs(r,rs)) = 1;

cc_mar(i,r,rs,szn,t)$r_rs(r,rs) = sum(c$ict(i,c,t),cc_eqcf(i,c,r,rs,t));

resourcescalar(i) = 1;

*==========================
* --- Storage ---
*==========================
set
     Battery_storage(i) "battery storage technologies",
     SR_Storage(i)       "storage tech available for spinning reserve" // initialized below assuming all are available; can create input file if needed
;

parameter
     storage_eff(i) "storage efficiency"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%storage%ds%storage_efficiency.csv
$offdelim
          /,
     storage_duration(i) "storage duration"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%storage%ds%storage_duration.csv
$offdelim
          /,
     numdays(szn)   "number of days for each season" //calc from hours adn h_szn
;//

scalar
     battery_duration "hours of battery duration"
;

*######################
* --- calculations ---

SR_Storage(i)$storage(i) = yes;
Battery_storage("battery") = yes;

numdays(szn) = sum(h$h_szn(h,szn),hours(h))/24;

battery_duration = storage_duration("BATTERY");

*==========================
* --- Reserves ---
*==========================
Set
    ortype               "types of operating reserve constraints"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%ortype_set.csv
          /,
    orcat                "operating reserve category "
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%orcat_set.csv
          /,
    dayhours(h)          "daytime hours, used to limit PV capacity to the daytime hours"
          /
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%sets%ds%dayhours_set.csv
          /,
    hour_szn_group(h,hh) "h and hh in the same season - used in minloading constraint"
    ;


parameter
          ramptime(ortype)       "minutes for ramping limit constraint in operating reserves"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%ramptime.csv
$offdelim
          /,
          ramprate(i)            "--MW per min-- ramp rate"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%ramprate.csv
$offdelim
          /,
          minloadfrac0(i)        "initial minimum loading fraction"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%%MinLoad_file%
$offdelim
          /,
          prm(r,t)               "planning reserve margin by BA"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%prm.csv
$offdelim
          /,
          prm_region(region,t)    "planning reserve margin by region"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%prm_region.csv
$offdelim
          /,
          cost_opres(i)          "--INR/MWh-- cost of regulating reserves "
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%cost_opres.csv
$offdelim
          /,
          hydmin(i,r,szn) "minimum hydro loading factors by season and region"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%hyd_minload.csv
$offdelim
          /,
          reserve_frac(i,ortype)  "final ramp limit used in model" , // calc based on ramprate and ramptime
          minloadfrac            "minimum loading fraction - final used in model"  // calc from minloadfract0 with adjustments for hydro based on hydmin; did not include adjustment for coal
          ;

* input tables
table orperc(ortype,orcat) "operating reserve percentage by type and category"

$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%reserves%ds%orperc.csv
$offdelim
;


*######################
* --- calculations ---
hour_szn_group(h,hh)$sum(szn$(h_szn(h,szn)$h_szn(hh,szn)),1) = yes;

*reducing problem size by removing h-hh combos that are the same
hour_szn_group(h,hh)$(sameas(h,hh)) = no;

* don't want to exceed 100%, esp w/flex ortype, so use min of 1 or the computed value
reserve_frac(i,ortype) = min(1,ramprate(i) * ramptime(ortype));

minloadfrac(r,i,h) = minloadfrac0(i);
minloadfrac(r,i,h)$(sum(szn$h_szn(h,szn),hydmin(i,r,szn))) = sum(szn$h_szn(h,szn),hydmin(i,r,szn));


*==========================
* --- Policy ---
*==========================
scalar CarbonPolicyStartYear  "First year for carbon policy" /%carbonpolicystartyear%/;

set
    co2mass(r,t)  "BAs and years with CO2 mass limit",
    co2rate(r,t)  "BAs and years with CO2 emissions rate limit",
    co2massnat(t) "set of years with a national CO2 standard"
    ;

parameter
          co2_rate_limit(r,t)       "--metric tons per MWh-- CO2 emission rate limit",
          co2_mass_limit(r,t)       "--million metric tons CO2-- CO2 emissions limit",
          co2_mass_limit_nat(t)     "national co2 mass limit",
          CarbonTax(t)              "national carbon tax in $ / MTCO2"    ,
          growth_limit_relative(i) "--%-- growth limit for technology groups relative to existing capacity"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%growth_limit_relative.csv
$offdelim
          /,
          growth_limit_absolute(r,tg) "--MW-- growth limit for technology groups in absolute terms"
          /
$ondelim
$include %gams.curdir%%ds%A_Inputs%ds%inputs%ds%generators%ds%growth_limit_absolute.csv
$offdelim
          /;


*######################
* --- calculations ---

*disabled by default
co2mass(r,t) = no;
co2rate(r,t) = no;
co2massnat(t) = no;

co2_rate_limit(r,t) = 0;
co2_mass_limit(r,t) = 0;
co2_mass_limit_nat(t) = 0;
CarbonTax(t) = 0;


*==================
* -- RS removal --
*==================
* this section removes the resource region ('rs') index and creates a single index 'r' that includes all BA and rs values
set
m_refurb_cond(i,c,r,t,tt)        "i c r combinations that are built in tt that can be refurbished in t", //derived in c_solveprep
cf_tech(i)                       "techs with capacity factors" //derived from m_cf

;

parameter
m_capacity_exog(i,c,r,t)         "--MW-- exogenous capacity used in the model",
m_required_prescriptions(i,r,t)  "--MW-- required prescriptions by year (non-cumulative)",
m_rscfeas(r,i,rscbin)            "--qualifier-- feasibility conditional for investing in RSC techs",
m_avail_retire_exog_rsc(i,c,r,t) "--MW-- exogenous amoung of available retirements",
m_rsc_dat(r,i,rscbin,rscvar)     "--MW or $/MW-- resource supply curve attributes",
m_cc_mar(i,r,szn,t)              "--%-- marginal capacity value",
m_cf(i,r,h)                    "--%-- modeled capacity factor"
;


  m_capacity_exog(i,c,rb,t) = capacity_exog(i,c,rb,"sk",t);
  m_capacity_exog(i,c,rs,t)$(not sameas(rs,"sk")) = sum(r$r_rs(r,rs),capacity_exog(i,c,r,rs,t));

  m_required_prescriptions(i,rb,t) = required_prescriptions(i,rb,t);

  m_rscfeas(rb,i,rscbin) = rscfeas(rb,"sk",i,rscbin);
  m_rscfeas(rs,i,rscbin)$(not sameas(rs,"sk")) = sum(r$r_rs(r,rs),rscfeas(r,rs,i,rscbin));

  m_avail_retire_exog_rsc(i,c,rb,t) = avail_retire_exog_rsc(i,c,rb,"sk",t);
  m_avail_retire_exog_rsc(i,c,rs,t)$(not sameas(rs,"sk")) = sum(r$r_rs(r,rs),avail_retire_exog_rsc(i,c,r,rs,t));

  m_rsc_dat(rb,i,rscbin,"cap") = rsc_dat(rb,"sk",i,rscbin,"cap");
  m_rsc_dat(rs,i,rscbin,"cap")$(not sameas(rs,"sk")) = sum(r$r_rs(r,rs),rsc_dat(r,rs,i,rscbin,"cap"));

  rsc_dat(r,rs,i,rscbin,"cost")$(hydro(i)$rsc_dat(r,rs,i,rscbin,"cost")) = rsc_dat(r,rs,i,rscbin,"cost") * 1000;

  m_rsc_dat(rb,i,rscbin,"cost") = rsc_dat(rb,"sk",i,rscbin,"cost");
  m_rsc_dat(rs,i,rscbin,"cost")$(not sameas(rs,"sk")) = sum(r$r_rs(r,rs),rsc_dat(r,rs,i,rscbin,"cost"));

  m_cc_mar(i,rb,szn,t) = cc_mar(i,rb,"sk",szn,t);
  m_cc_mar(i,rs,szn,t)$(not sameas(rs,"sk")) = sum(r$r_rs(r,rs),cc_mar(i,r,rs,szn,t));

  cost_cap_fin_mult(rb,i,t)$(not vre(i)) =  cost_cap_fin_mult(rb,i,t);
  cost_cap_fin_mult(rs,i,t)$[(not sameas(rs,"sk"))$vre(i) ] =
      sum(country$sum(r$r_rs(r,rs),r_country(r,country)),FinMult(country,i,t));

  cost_cap_fin_mult(rb,i,t)$[(not vre(i))$(not cost_cap_fin_mult(rb,i,t))] = 1;
  cost_cap_fin_mult(rs,i,t)$[vre(i)$(not cost_cap_fin_mult(rs,i,t))] = 1;

  m_cf(i,rb,h)$rsc_i(i) = cf_rsc(i,rb,"sk",h);
  m_cf(i,rs,h)$[(not sameas(rs,"sk"))$rsc_i(i)] = sum(r$r_rs(r,rs),cf_rsc(i,r,rs,h));

 cf_tech(i)$(sum((c,r,h,t),m_cf(i,r,h))) = yes;

 cc_avg(i,r,szn,t)$(sum(h$h_szn(h,szn),m_cf(i,r,h))) =
        sum(h$h_szn(h,szn),hours(h) * m_cf(i,r,h)) / sum(h$h_szn(h,szn),hours(h));

 cc_hydro(i,r,szn,t) = cc_avg(i,r,szn,t)$hydro_d(i);

execute_unload 'A_Inputs%ds%inputs.gdx';
