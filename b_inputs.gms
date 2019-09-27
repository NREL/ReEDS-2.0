$title 'ReEDS 2.0'

* Note - all dollar values are in 2004$ unless otherwise indicated
* It is our intention that there are no hard-coded values in B_inputs.gms
* but you will note that we still have some work to do to make that happen...

*Setting the default directory separator
$setglobal ds \

$eolcom \\

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

*need to convert the 'unit' numhintage to some large value
$ifthen.unithintage %numhintage%=="unit"
$eval numhintage 100
$endif.unithintage

* there are numeraire hintages on either sides of the outer breaks
* when using calcmethod = 1, here adding two for safety
* NB this will not increase model size given conditions
* dictating valcap and valgen for initial classes
$eval numhintage %numhintage% + 2

* --- define input file directory ---
$setglobal input_folder '%gams.curdir%%ds%inputs'

*$ontext
* --- print timing profile ---
option profile = 3
option profiletol = 0

* --- supress .lst file printing ---
* equations listed per block
option limrow = 0 ;
* variables listed per block
option limcol = 0 ;
* solver's solution output printed
option solprint = off ;
* solver's system output printed
option sysout = off ;
*$offtext

set dummy "set used for initalization of numerical sets" / 0*10000 / ;
alias(dummy,adummy) ;


*======================
* -- Local Switches --
*======================

* Following are scalars used to turn on or off various components of the model.
* They are re-assigned via globals in D_solveprep.gms but defaults are presented here
* For binary swithces, [0] is off and [1] is on

Scalar
Sw_AB32              "Switch for the AB32 constraint"                                     /%GSw_AB32%/
Sw_AnnualCap         "Switch for the carbon cap constraint"                               /%GSw_AnnualCap%/
Sw_AVG_iter          "Switch to select method for curt/CC calculations"                   /%GSw_AVG_iter%/
Sw_BinOM             "Switch to bin historical plant VOM and FOM costs"                   /%GSw_BinOM%/
Sw_BankBorrowCap     "Switch for the carbon cap constraint with banking/borrowing"        /%GSw_BankBorrowCap%/
Sw_CSAPR             "Switch to enable or disable the CSAPR-related constraints"          /%GSw_CSAPR%/
Sw_BatteryMandate    "Switch to enable battery capacity mandates"                         /%GSw_BatteryMandate%/
Sw_CarbTax           "Switch to turn on/off a carbon tax"                                 /%GSw_CarbTax%/
Sw_CoalRetire        "Switch to retire coal plants early"                                 /%GSw_CoalRetire%/
Sw_CSPRelLim         "Annual relative growth limit for CSP technologies"                  /%GSw_CSPRelLim%/
Sw_CurtCC_RTO        "Switch to average cc curt values over RTO"                          /%GSw_CurtCC_RTO%/
Sw_CurtStorage       "Fraction of storage charging that can reduce curtailment"           /%GSw_CurtStorage%/
Sw_ForcePrescription "Switch enforcing near term limits on capacity builds"               /%GSw_ForcePrescription%/
Sw_EV                "Switch to include electric vehicle load"                            /%GSw_EV%/
Sw_GasCurve          "Switch to have a national gas curve [0] or regional gas curves [1]" /%GSw_GasCurve%/
Sw_GenMandate        "Switch for the national generation constraint"                      /%GSw_GenMandate%/
Sw_Geothermal        "Switch to remove [0], have default [1], or extended [1] geothermal" /%GSw_Geothermal%/
Sw_GrowthAbsCon      "Switch for the absolute growth constraint"                          /%GSw_GrowthAbsCon%/
Sw_GrowthRelCon      "Switch for the relative growth constraint"                          /%GSw_GrowthRelCon%/
Sw_HighCostTrans     "Switch to increase costs and losses of transmission"                /%GSw_HighCostTrans%/
Sw_Int_CC            "Switch for intertemporal CC (0=ave, 1=marg, 2=scaled marg)"         /%GSw_Int_CC%/
Sw_Int_Curt          "Switch for intertemporal Curt (0=ave, 1=marg, 2=scaled marg)"       /%GSw_Int_Curt%/
Sw_Loadpoint         "Switch to use a loadpoint for the intertemporal case"               /%GSw_Loadpoint%/
Sw_MaxCFCon          "Switch for the maximum seasonal capacity factor constraint"         /%GSw_MaxCFCon%/
Sw_MinCFCon          "Switch for the minimum annual capacity factor constraint"           /%GSw_MinCFCon%/
Sw_Mingen            "Switch to include or remove MINGEN variable"                        /%GSw_Mingen%/
Sw_NearTermLimits    "Switch enforcing near term limits on capacity builds"               /%GSw_NearTermLimits%/
Sw_OpRes             "Switch for the operating reserves constraints"                      /%GSw_OpRes%/
Sw_ReducedResource   "Switch to reduce the amount of RE resource available"               /%GSw_ReducedResource%/
Sw_Refurb            "Switch allowing refurbishments"                                     /%GSw_Refurb%/
Sw_ReserveMargin     "Switch for the planning reserve margin constraints"                 /%GSw_ReserveMargin%/
Sw_Retire            "Switch allowing endogenous retirements"                             /%GSw_Retire%/
Sw_RGGI              "Switch for the RGGI constraint"                                     /%GSw_RGGI%/
Sw_SolarRelLim       "Annual relative growth limit for UPV and DUPV technologies"         /%GSw_SolarRelLim%/
Sw_StateRPS          "Switch for the state RPS constraints"                               /%GSw_StateRPS%/
Sw_Storage           "Switch for allowing storage (both existing and new)"                /%GSw_Storage%/
Sw_CCS               "Switch for allowing CCS (both existing and new)"                    /%GSw_CCS%/
Sw_WindRelLim        "Annual relative growth limit for wind (ons and ofs) technologies"   /%GSw_WindRelLim%/
;



*==========================
* --- Set Declarations ---
*==========================

set i "generation technologies"
   /
      ice,
      battery
      biopower
      caes
      can-imports
      coal-CCS
      Coal-IGCC
      coal-new
      CoalOldScr
      CoalOldUns
      CofireNew
      CofireOld
      csp-ns
      distPV
      Gas-CC
      Gas-CC-CCS
      Gas-CT
      geothermal
      Hydro
      lfill-gas
      MHKwave
      Nuclear
      Ocean
      o-g-s
      other
      pumped-hydro
      unknown
      upv_1*upv_10,
      dupv_1*dupv_10,
      wind-ofs_1*wind-ofs_15,
      wind-ons_1*wind-ons_10,
      csp1_1*csp1_12,
      csp2_1*csp2_12,
      hydD
      hydND
      hydSD
      hydSND
      hydUD
      hydUND
      hydNPD
      hydNPND
      hydED
      hydEND
      deep-egs_pbinary_1*deep-egs_pbinary_8,
      deep-egs_pflash_1*deep-egs_pflash_8,
      geohydro_pbinary_1*geohydro_pbinary_8,
      geohydro_pflash_1*geohydro_pflash_8,
      NF-EGS_pbinary_1*NF-EGS_pbinary_8,
      NF-EGS_pflash_1*NF-EGS_pflash_8,
      undisc_pbinary_1*undisc_pbinary_8,
      undisc_pflash_1*undisc_pflash_8
   /,

*The following two sets:
*ban - will remove the technology from being considered, anywhere
*bannew - will remove the ability to invest in that technology
  ban(i) "ban from existing, prescribed, and new generation -- usually indicative of missing data or operational constraints"
  /
    ice
    upv_10
    mhkwave
    caes
    other
    unknown
    hydro
  /,

  bannew(i) "banned from creating new capacity, usually due to lacking data or represention"
  /
    can-imports
    hydro
    distpv
    geothermal
    Ocean
    cofireold
    caes
    CoalOldScr
    CoalOldUns
    csp-ns
*you cannot build existing hydro...
    HydEND
    HydED
  /

  geotech "broader geothermal categories"
  /
   deep-egs_pbinary
   geohydro_pbinary
   NF-EGS_pbinary
   undisc_pbinary
   deep-egs_pflash
   geohydro_pflash
   NF-EGS_pflash
   undisc_pflash
  /,

  i_geotech(i,geotech) "crosswalk between an individual geothermal technology and its category"
   /
      (deep-egs_pbinary_1*deep-egs_pbinary_8).deep-egs_pbinary ,
      (geohydro_pbinary_1*geohydro_pbinary_8).geohydro_pbinary ,
      (NF-EGS_pbinary_1*NF-EGS_pbinary_8).NF-EGS_pbinary ,
      (undisc_pbinary_1*undisc_pbinary_8).undisc_pbinary ,
      (deep-egs_pflash_1*deep-egs_pflash_8).deep-egs_pflash ,
      (geohydro_pflash_1*geohydro_pflash_8).geohydro_pflash ,
      (NF-EGS_pflash_1*NF-EGS_pflash_8).NF-EGS_pflash ,
      (undisc_pflash_1*undisc_pflash_8).undisc_pflash
    /,

*technology-specific subsets
  coal(i)              "technologies that use coal",
  gas(i)               "tech that uses gas",
  conv(i)              "conventional generation technologies",
  ccs(i)               "CCS technologies",
  re(i)                "renewable energy technologies",
  vre(i)               "variable renewable energy technologies",
  rsc_i(i)             "technologies based on Resource supply curves",
  wind(i)              "wind generation technologies",
  ofswind(i)           "offshore wind technologies",
  onswind(i)           "onshore wind technologies",
  upv(i)               "upv generation technologies",
  dupv(i)              "dupv generation technologies",
  distpv(i)            "distpv (i.e., rooftop PV) generation technologies",
  pv(i)                "all PV generation technologies",
  csp(i)               "csp generation technologies",
  csp_nostorage(i)     "csp generation without storage",
  csp_storage(i)       "csp generation technologies with thermal storage",
  csp1(i)              "csp-tes generation technologies 1",
  csp2(i)              "csp-tes generation technologies 2",
  storage(i)           "storage technologies",
  storage_no_csp(i)    "storage technologies that are not CSP",
  thermal_storage(i)   "thermal storage technologies"
  battery(i)           "battery storage technologies"
  cofire(i)            "cofire technologies",
  hydro(i)             "hydro technologies",
  hydro_d(i)           "dispatchable hydro technologies",
  hydro_nd(i)          "non-dispatchable hydro technologies",
  geo(i)               "geothermal technologies"
  geo_base(i)          "geothermal technologies typically considered in model runs"
  geo_extra(i)         "geothermal technologies not typically considered in model runs"
  geo_undisc(i)        "undiscovered geothermal technologies"
  canada(i)            "Canadian imports",
  vre_no_csp(i)        "variable renewable energy technologies that are not csp",
  vre_utility(i)       "utility scale wind and PV technologies",
  vre_distributed(i)   "distributed PV technologies",

  UnitCT "unit cooling technology from input data"
   /
    recirc
    none
    once
    pond
    dry
   /,

i_subtech technology subset categories
   /
      COAL
      GAS
      CONV
      CCS
      RE
      VRE
      RSC
      WIND
      OFSWIND
      ONSWIND
      UPV
      DUPV
      distPV
      PV
      CSP
      CSP_NOSTORAGE
      CSP1
      CSP2
      STORAGE
      STORAGE_NO_CSP
      THERMAL_STORAGE
      BATTERY
      COFIRE
      HYDRO
      HYDRO_D
      HYDRO_ND
      GEO
      GEO_BASE
      GEO_EXTRA
      GEO_UNDISC
      GEOTHERMAL_Base
      GEOTHERMAL_Extended
      CANADA
      VRE_NO_CSP
      VRE_UTILITY
      VRE_DISTRIBUTED
   /,

allt "all potential years" /1900*2120/,

t "full set of years" / 2010 * 2050 /,

* Each generation technology is broken out by class:
* 1. initial capacity: init-1, init-2, ..., init-n
* 2. prescribed capacity: prescribed
* 3. new capacity: new
* This allows us to distinguish between existing, prescribed, and model-chosen builds
* The number of classes is set by numhintage for initial capacity and numclass for new capacity
v "technology class"
    /
      init-1*init-%numhintage%,
      new1*new%numclass%
    /,

initv(v) "inital technologies" /init-1*init-%numhintage%/,

newv(v) "new tech set" /new1*new%numclass%/,

r "regions" / p1*p205,s1*s454,sk/,

rb(r) "balancing regions" /p1*p205/,

rs(r) "renewable resource region" /s1*s454,sk/,

h "hour block or time slice" / h1*h17 /,

e "emission categories" /CO2, SO2, NOX, HG/,

summerh(h) "summer hours" /H1,H2,H3,H4,H17/,

szn "seasons" /summ, fall, wint, spri/,

h_szn(h,szn) "mapping of hour blocks to seasons"
   /
      (h1*h4,h17).summ,
      (h5*h8).fall,
      (h9*h12).wint,
      (h13*h16).spri
   /,

vc "voltage class (for transmission)" /vc1*vc5/,

nercr "NERC regions" /nr1*nr15/,

nercr_new "new NERC regions" /nrn1*nrn27/,

rto "RTO regions" /rto1*rto41/,

cendiv "census divisions" /PA, MTN, WNC, ENC, WSC, ESC, SA, MA, NE, MEX/,

interconnect "interconnection regions" /WSCC, eastern, texas, quebec, mexico/,

country "country regions" /USA, MEX, CAN/,

customreg "custom regions, from heritage ReEDS hierarchy"
   /
   WA, NM, OK, PA, MEX,
   OR, TX, AR, RGGI, CAN,
   CA, SD, LA, MS,
   NV, ND, MI, AL,
   ID, NE, IL, FL,
   UT, MN, IN, GA,
   AZ, WI, OH, TN,
   MT, IA, KY, NC,
   WY, KS, VA, SC,
   CO, MO, WV, NJ
   /,


st "US, Mexico, and Canadian States/Provinces"
                   / AL, AR, AZ, CA, CO, CT, DE, FL, GA, IA,
                     ID, IL, IN, KS, KY, LA, MA, MD, ME, MI,
                     MN, MO, MS, MT, NC, ND, NE, NH, NJ, NM,
                     NV, NY, OH, OK, OR, PA, RI, SC, SD, TN,
                     TX, UT, VA, VT, WA, WI, WV, WY,
*  - Mexico -
                     MEX, AGU_GUA_JAL_NAY_QUE_ZAC, BCN, BCS,
                     CAM_CHP_TAB, CHH, COA_DGO_NLE, COL,
                     DIF_HID_MEX_MOR_OAX_PUE_TAM_TLA_VER,
                     GRO_MIC, ROO, SIN_SON, SLP, YUC,
*  - Canada -
                     BC, AB, SK, MB, ON, QC, NB, NS, NL, NFI, PEI
                    /,

tg "tech groups for growth constraints" /wind, solar, csp/,

tg_i(tg,i) "technologies that belong in tech group tg"
    /
    wind.(wind-ons_1*wind-ons_10),
    solar.(upv_1*upv_10,dupv_1*dupv_10),
    csp.(csp1_1*csp1_12, csp2_1*csp2_12)
    /

pcat "prescribed capacity categories"
    /
*seldom-used pound/hashtag populates
*elements of this set with the indicated set
#i
    upv,
    dupv,
    wind-ons,
    wind-ofs,
    csp-ws
    /
;

alias(r,rr) ;
alias(rto,rto2) ;
alias(i,ii) ;
alias(rs,rss) ;
alias(h,hh) ;
alias(v,vv) ;
alias(t,tt,ttt) ;
alias(st,ast,aast) ;
alias(allt,alltt) ;

table r_rs(r,rs) "mapping set between BAs and renewable resource regions"
$offlisting
$ondelim
$include inputs_case%ds%rsout.csv
$offdelim
$onlisting
;


set nexth(h,hh) "order of hour blocks"
  /
    H1.H2, H2.H3, H3.H17, H4.H1,
    H5.H6, H6.H7, H7.H8, H8.H5,
    H9.H10, H10.H11, H11.H12, H12.H9,
    H13.H14, H14.H15, H15.H16, H16.H13, H17.H4
  /
;

*all regions have the sk renewable region
*used to represent the entire region
*for technologies that do not have the full
*356 renewable resource region specification
r_rs(r,"sk") = yes ;


parameter yeart(t) "numeric value for year",
          year(allt) "numeric year value for allt" ;

yeart(t) = t.val ;
year(allt) = allt.val ;

set att(allt,t) "mapping set between allt and t" ;
att(allt,t)$[year(allt) = yeart(t)] = yes ;

*the end year is defined dynamically
*if %end_year% < annual data, we are gonna get into trouble...
*if you aint first you're last
set tfirst(t) "first year",
    tlast(t) "last year" ;

*aint first you're last
tfirst(t)$[ord(t) = 1] = yes ;
tlast(t)$[ord(t) = smax(tt,ord(tt))] = yes ;

*following set is used to interpolate values for any even-year-only data
set oddyears(t) "odd number years of t"
/
$offlisting
$include inputs_case%ds%oddyears.csv
$onlisting
/ ;

set atoddyears(allt) "odd number years of allt"
/
$offlisting
$include inputs_case%ds%oddyears.csv
$onlisting
/ ;

parameter deflator(allt) "Deflator values (for inflation) calculated from http://www.usinflationcalculator.com/inflation/consumer-price-index-and-annual-percent-changes-from-1913-to-2008/ using the Avg-Avg values"
/
$offlisting
$ondelim
$include inputs_case%ds%deflator.csv
$offdelim
$onlisting
/ ;


*various parameters needed for Present Value Factor (PVF) calculations before solving
*specifically these are used in the aggregating of the PVF of
*onm and capital when years are skipped
alias(t,yy,yyy) ;
set yearafter "set to loop over for the final year calculation" /1*19/ ;


* --- Read technology subset lookup table ---
Table i_subsets(i,i_subtech) "technology subset lookup table"
$offlisting
$ondelim
$include inputs_case%ds%tech-subset-table.csv
$offdelim
$onlisting
;


* --- define technology subsets ---
COAL(i)             = YES$i_subsets(i,'COAL') ;
GAS(i)              = YES$i_subsets(i,'GAS') ;
CONV(i)             = YES$i_subsets(i,'CONV') ;
CCS(i)              = YES$i_subsets(i,'CCS') ;
RE(i)               = YES$i_subsets(i,'RE') ;
VRE(i)              = YES$i_subsets(i,'VRE') ;
RSC_i(i)            = YES$i_subsets(i,'RSC') ;
WIND(i)             = YES$i_subsets(i,'WIND') ;
OFSWIND(i)          = YES$i_subsets(i,'OFSWIND') ;
ONSWIND(i)          = YES$i_subsets(i,'ONSWIND') ;
UPV(i)              = YES$i_subsets(i,'UPV') ;
DUPV(i)             = YES$i_subsets(i,'DUPV') ;
DISTPV(i)           = YES$i_subsets(i,'DISTPV') ;
PV(i)               = YES$i_subsets(i,'PV') ;
CSP(i)              = YES$i_subsets(i,'CSP') ;
CSP_NOSTORAGE(i)    = YES$i_subsets(i,'CSP_NOSTORAGE') ;
CSP1(i)             = YES$i_subsets(i,'CSP1') ;
CSP2(i)             = YES$i_subsets(i,'CSP2') ;
STORAGE(i)          = YES$i_subsets(i,'STORAGE') ;
STORAGE_NO_CSP(i)   = YES$i_subsets(i,'STORAGE_NO_CSP') ;
THERMAL_STORAGE(i)  = YES$i_subsets(i,'THERMAL_STORAGE') ;
BATTERY(i)          = YES$i_subsets(i,'BATTERY') ;
COFIRE(i)           = YES$i_subsets(i,'COFIRE') ;
HYDRO(i)            = YES$i_subsets(i,'HYDRO') ;
HYDRO_D(i)          = YES$i_subsets(i,'HYDRO_D') ;
HYDRO_ND(i)         = YES$i_subsets(i,'HYDRO_ND') ;
GEO(i)              = YES$i_subsets(i,'GEO') ;
GEO_BASE(i)         = YES$i_subsets(i,'GEO_BASE') ;
GEO_EXTRA(i)        = YES$i_subsets(i,'GEO_EXTRA') ;
GEO_UNDISC(i)        = YES$i_subsets(i,'GEO_UNDISC') ;
CANADA(i)           = YES$i_subsets(i,'CANADA') ;
VRE_NO_CSP(i)       = YES$i_subsets(i,'VRE_NO_CSP') ;
VRE_UTILITY(i)      = YES$i_subsets(i,'VRE_UTILITY') ;
VRE_DISTRIBUTED(i)  = YES$i_subsets(i,'VRE_DISTRIBUTED') ;
CSP_Storage(i)$csp1(i) = yes ;
CSP_Storage(i)$csp2(i) = yes ;


set cf_tech(i) "technologies that have a specified capacity factor",
    nonvariable(i) "technologies that are non-variable",
    retiretech(i,v,r,t) "combinations of i,v,r,t that can be retired",
    refurbtech(i) "technologies that can be refurbished",
    inv_cond(i,v,r,t,tt) "allows an investment in tech i of class v to be built in region r in year tt and usable in year t" ;

nonvariable(i)$[not(vre(i) or hydro_nd(i))] = yes ;

*pv/wind/csp/hydro techs have capacity factors based on resouce assessments
cf_tech(i)$[pv(i) or wind(i) or csp(i) or hydro(i)] = yes ;

*initialize sets to "no"
retiretech(i,v,r,t) = no ;
inv_cond(i,v,r,t,tt) = no ;


set prescriptivelink0(pcat,ii) "initial set of prescribed categories and their technologies - used in creating valid sets in force_pcat"
/
  upv.(upv_1*upv_10)
  dupv.(dupv_1*dupv_10)
  wind-ons.(wind-ons_1*wind-ons_10)
  csp-ws.(csp1_1*csp1_12,csp2_1*csp2_12)
  wind-ofs.(wind-ofs_1*wind-ofs_15)
  geothermal.(geohydro_pbinary_1*geohydro_pbinary_8,geohydro_pflash_1*geohydro_pflash_8)
/ ;

set prescriptivelink(pcat,i) "final set of prescribed categories and their technologies - used in the model" ;

prescriptivelink(pcat,i)$prescriptivelink0(pcat,i) = yes ;

alias(pcat,ppcat) ;

* active prescriptivelink for all techs not included in the table above
* but restrict out csp techs in this calculation - since they
* are indexed by a separate pcat (csp-ws) and have special considerations
prescriptivelink(pcat,i)$[sameas(pcat,i)$(not sum{ppcat, prescriptivelink(ppcat,i) })$(not csp1(i))] = yes ;
*only geo_hydro techs are considered to meet geothermal prescriptions
prescriptivelink(pcat,i)$[geo_extra(i)] = no ;
prescriptivelink(pcat,i)$[i_geotech(i,"undisc_pbinary") or i_geotech(i,"undisc_pflash")] = no ;


set rsc_agg(i,ii)   "rsc technologies that belong to the same class",
    tg_rsc_cspagg(i, ii) "csp technologies that belong to the same class"
    /
    csp1_1.(csp1_1, csp2_1),
    csp1_2.(csp1_2, csp2_2),
    csp1_3.(csp1_3, csp2_3),
    csp1_4.(csp1_4, csp2_4),
    csp1_5.(csp1_5, csp2_5),
    csp1_6.(csp1_6, csp2_6),
    csp1_7.(csp1_7, csp2_7),
    csp1_8.(csp1_8, csp2_8),
    csp1_9.(csp1_9, csp2_9),
    csp1_10.(csp1_10, csp2_10),
    csp1_11.(csp1_11, csp2_11),
    csp1_12.(csp1_12, csp2_12)
    /
;

rsc_agg(i,ii)$[sameas(i,ii)$(not csp(i))$(not csp(ii))$rsc_i(i)$rsc_i(ii)] = yes ;
rsc_agg(i,ii)$tg_rsc_cspagg(i,ii) = yes ;

*======================================
*     --- Begin hierarchy ---
*======================================

set hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg) "hierarchy of various regional definitions"
/
$offlisting
$include inputs_case%ds%hierarchy.prn
$onlisting
/ ;


* Mappings between r and other region sets
set r_nercr(r,nercr),
    r_nercr_new(r,nercr_new),
    r_rto(r,rto),
    r_cendiv(r,cendiv),
    r_st(r,st),
    r_interconnect(r,interconnect),
    r_country(r,country),
    r_customreg(r,customreg) ;

r_nercr(r,nercr)$sum{(nercr_new,rto,cendiv,st,interconnect,country,customreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg),1} = yes ;
r_nercr_new(r,nercr_new)$sum{(nercr,rto,cendiv,st,interconnect,country,customreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg),1} = yes ;
r_rto(r,rto)$sum{(nercr,nercr_new,cendiv,st,interconnect,country,customreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg),1} = yes ;
r_cendiv(r,cendiv)$sum{(nercr,nercr_new,rto,st,interconnect,country,customreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg),1} = yes ;
r_st(r,st)$sum{(nercr,nercr_new,rto,cendiv,interconnect,country,customreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg),1} = yes ;
r_interconnect(r,interconnect)$sum{(nercr,nercr_new,rto,cendiv,st,country,customreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg),1} = yes ;
r_country(r,country)$sum{(nercr,nercr_new,rto,cendiv,st,interconnect,customreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg),1} = yes ;
r_customreg(r,customreg)$sum{(nercr,nercr_new,rto,cendiv,st,interconnect,country)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg),1} = yes ;

parameter num_interconnect(interconnect) "interconnection numbers"
 /WSCC 1, eastern 2, texas 3, quebec 4, mexico 5/ ;

*======================================
* ---------- Bintage Mapping ----------
*======================================
*following set is un-assumingly important
*it allows for the investment of bintage 'v' at time 't'

*table ictmap(i,t)
table ict_num(i,t) "number associated with bin for ict calculation"
$offlisting
$ondelim
$include inputs_case%ds%ict.csv
$offdelim
$onlisting
;


set ict(i,v,t) "mapping set between i v and t - for new technologies" ;
ict(i,newv,t)$[ord(newv) = ict_num(i,t)] = yes ;

parameter countnc(i,newv) "number of years in each newv set" ;

*add 1 for each t item in the ct_corr set
countnc(i,newv) = sum{t$ict(i,newv,t),1} ;

*=====================================
*--- basic parameter declarations ---
*=====================================

parameter hours(h) "--hours-- number of hours in each time block"
/
$offlisting
$ondelim
$include inputs_case%ds%numhours.csv
$offdelim
$onlisting
/ ;

parameter INr(r) "--unitless-- mapping of r regions to interconnection numbers",
          crf(t) "--unitless-- capital recovery factor"
/
$offlisting
$ondelim
$include inputs_case%ds%crf.csv
$offdelim
$onlisting
/,
* pvf_capital and pvf_onm here are for intertemporal mode. These parameters
* are overwritten for sequential mode in D_solveprep.gms.
          pvf_capital(t) "--unitless-- present value factor for overnight capital costs"
/
$offlisting
$ondelim
$include inputs_case%ds%pvf_cap.csv
$offdelim
$onlisting
/,
          pvf_onm(t)"--unitless-- present value factor of operations and maintenance costs"
/
$offlisting
$ondelim
$include inputs_case%ds%pvf_onm_int.csv
$offdelim
$onlisting
/,
          ptc_unit_value(i,v,r,t) "--$/MWh-- present-value of all PTC payments for 1 hour of operation at CF = 1"
/
$offlisting
$ondelim
$include inputs_case%ds%ptc_unit_value.csv
$offdelim
$onlisting
/,
          pvf_onm_undisc(t) "--unitless-- undiscounted present value factor of operations and maintenance costs"
;

* pvf_onm_undisc is based on intertemporal pvf_onm and pvf_capital,
* and is used for bulk system cost outputs
pvf_onm_undisc(t)$pvf_capital(t) = pvf_onm(t) / pvf_capital(t) ;
INr(r) = sum{interconnect$r_interconnect(r,interconnect), num_interconnect(interconnect) } ;



*==========================================
*     --- Canadian Imports/Exports ---
*==========================================

table can_imports(r,t) "--MWh-- Imports from Canada by year"
$offlisting
$ondelim
$include inputs_case%ds%can_imports.csv
$offdelim
$onlisting
;

table can_exports(r,t) "--MWh-- Exports to Canada by year"
$offlisting
$ondelim
$include inputs_case%ds%can_exports.csv
$offdelim
$onlisting
;

parameter can_imports_szn_frac(szn) "--unitless-- fraction of annual imports that occur in each season"
/
$offlisting
$ondelim
$include inputs_case%ds%can_imports_szn_frac.csv
$offdelim
$onlisting
/
;

parameter can_exports_h_frac(h) "--unitless-- fraction of annual exports that occur in each timeslice"
/
$offlisting
$ondelim
$include inputs_case%ds%can_exports_h_frac.csv
$offdelim
$onlisting
/
;

parameter can_imports_szn(r,szn,t) "--MWh-- Seasonal imports from Canada by year",
          can_exports_h(r,h,t)     "--MW-- Timeslice exports to Canada by year" ;

can_imports_szn(r,szn,t) = can_imports(r,t) * can_imports_szn_frac(szn) ;
can_exports_h(r,h,t) = can_exports(r,t) * can_exports_h_frac(h) / hours(h) ;

parameter firstyear(i) "first year where new investment is allowed"
/
$offlisting
$ondelim
$include inputs_case%ds%firstyear.csv
$offdelim
$onlisting
/ ;

firstyear(i)$[not firstyear(i)] = 2020 ;

parameter firstyear_pcat(pcat) ;
firstyear_pcat(pcat)$[sum{i$sameas(i,pcat), firstyear(i) }] = sum{i$sameas(i,pcat), firstyear(i) } ;
firstyear_pcat("upv") = firstyear("upv_1") ;
firstyear_pcat("dupv") = firstyear("dupv_1") ;
firstyear_pcat("wind-ons") = firstyear("wind-ons_1") ;
firstyear_pcat("wind-ofs") = firstyear("wind-ofs_1") ;
firstyear_pcat("csp-ws") = firstyear("csp2_1") ;
firstyear_pcat("csp-ns") = firstyear("csp2_1") ;


scalar retireyear "first year to allow capacity to start retiring" /%GSw_Retireyear%/ ;

*================================
*sets that define model boundaries
*================================

set tmodel(t) "years to include in the model",
    tpast(t)  "years that have passed in real life (2010-2018)" /2010*2018/,
    tfix(t) "years to fix variables over when summing over previous years",
    tprev(t,tt) "previous modeled tt from year t",
    rfeas(r)  "BAs to include in the model",
    rfeas_cap(r) "regions that are allowed to have capacity"
    countryfeas(country) "countries included in the model"
    stfeas(st) "states to include in the model",
    cdfeas(cendiv) "census divisions to include in the model" ;

*following parameters get re-defined when the solve years have been declared
parameter mindiff(t) "minimum difference between t and all other tt that are in tmodel(t)" ;

tmodel(t) = no ;
tfirst(t) = no ;
tlast(t) = no ;
rfeas(r) = no ;
countryfeas(country) = no ;
tfix(t) = no ;
stfeas(st) = no ;
tprev(t,tt) = no ;

*==============================
* Year specification
*==============================

set tmodel_new(t) "years to run the model"
/
$offlisting
$include inputs_case%ds%%yearset%
$onlisting
/ ;

tmodel_new(t)$[yeart(t) > %endyear%]= no ;

*reset the first and last year indices of the model
tfirst(t)$[ord(t) = smin{tt$tmodel_new(tt), ord(tt )}] = yes ;
tlast(t)$[ord(t) = smax{tt$tmodel_new(tt), ord(tt) }] = yes ;

*now get rid of all non-immediately-previous values (it takes three steps to get there...)
tprev(t,tt)$[tmodel_new(t)$tmodel_new(tt)$(tt.val<t.val)] = yes ;
mindiff(t)$tmodel_new(t) = smin{tt$tprev(t,tt), t.val-tt.val} ;
tprev(t,tt)$[tmodel_new(t)$tmodel_new(tt)$(t.val-tt.val<>mindiff(t))] = no ;



*==============================
* Region specification
*==============================
rfeas(r) = no ;
*note that if you're running just ERCOT, Sw_GasCurve needs to be 2 (static natural gas prices) -
*if kept at 0, ercot is not a standalone census dvision
*if kept at 1, the prices will be too low as it does not allow for the consumption of gas in other regions

$ifthen.naris %GSw_region% == "naris"
* Turn off canadian imports as an option when running NARIS
  ban(i)$canada(i) = yes ;
$endif.naris

*Ingest list of valid BAs ('p' regions), as determined by pre-processing script.
set valid_ba_list(r) "Valid BAs to include in the model run"
/
$offlisting
$include inputs_case%ds%valid_ba_list.csv
$onlisting
/ ;

rfeas(r) = no ;
rfeas(r)$valid_ba_list(r) = yes ;

*Ingest list of all valid regions (both 'p' and 's' regions), as determined by pre-processing script.
set valid_regions_list(r) "Valid BAs and resource regions to include in the model run"
/
$offlisting
$include inputs_case%ds%valid_regions_list.csv
$onlisting
/ ;

rfeas_cap(r) = no ;
rfeas_cap(r)$valid_regions_list(r) = yes ;

*set the state and census division feasibility sets
*determined by which regions are feasible
stfeas(st)$[sum{r$[rfeas(r)$r_st(r,st)], 1 }] = yes ;
countryfeas(country)$[sum{r$[rfeas(r)$r_country(r,country)], 1 }] = yes ;
cdfeas(cendiv)$[sum{r$[rfeas(r)$r_cendiv(r,cendiv)], 1 }] = yes ;



*==========================
* -- existing capacity --
*==========================

*Begin loading of capacity data
*Created using input_processing\R\writecapdat.R
table capnonrsc(i,r,UnitCT,*) "--MW-- raw capacity data for non-RSC tech created by .\inputs\capacitydata\writecapdat.R"
$offlisting
$ondelim
$include inputs_case%ds%allout_nonRSC.csv
$offdelim
$onlisting
;

*Created using input_processing\R\writecapdat.R
table caprsc(pcat,r,rs,UnitCT,*) "--MW-- raw RSC capacity data, created by .\r\writecapdat.R"
$offlisting
$ondelim
$include inputs_case%ds%allout_RSC.csv
$offdelim
$onlisting
;

*Created using input_processing\R\writecapdat.R
table prescribednonrsc(t,pcat,r,UnitCT,*) "--MW-- raw prescribed capacity data for non-RSC tech created by writecapdat.R"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_nonRSC.csv
$offdelim
$onlisting
;

*Created using input_processing\R\writecapdat.R
table prescribedrsc(t,pcat,r,rs,*) "--MW-- raw prescribed capacity data for RSC tech created by .\inputs\capacitydata\writecapdat.R"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_rsc.csv
$offdelim
$onlisting
;

*Created using input_processing\R\writecapdat.R
*following does not include wind
table prescribedretirements(allt,r,i,UnitCT,*) "--MW-- raw prescribed capacity retirement data for non-RSC tech created by .\inputs\capacitydata\writecapdat.R"
$offlisting
$ondelim
$include inputs_case%ds%retirements.csv
$offdelim
$onlisting
;

parameter prescribedretirements_copy(allt,r,i,UnitCT,*) "--MW-- copy of prescribedretirements" ;
prescribedretirements_copy(allt,r,i,UnitCT,"value") = prescribedretirements(allt,r,i,UnitCT,"value") ;

*If coal retirement switch is 1, shorten coal lifetimes by 10 years if the plant retires in 2030 or later
if(Sw_CoalRetire = 1,
     prescribedretirements(allt,r,i,UnitCT,"value")$[coal(i)$(allt.val >= 2030)] = 0 ;
     prescribedretirements(allt,r,i,UnitCT,"value")$coal(i) = prescribedretirements_copy(allt+10,r,i,UnitCT,"value")$(allt.val >= 2030-10) + prescribedretirements(allt,r,i,UnitCT,"value") ;
) ;

*If coal retirement switch is 2, extend coal lifetimes by 10 years if the plant retires in 2022 or later
if(Sw_CoalRetire = 2,
     prescribedretirements(allt,r,i,UnitCT,"value")$[coal(i)$(allt.val >= 2022)] = 0 ;
     prescribedretirements(allt,r,i,UnitCT,"value")$[coal(i)$(allt.val >= 2022)] = prescribedretirements_copy(allt-10,r,i,UnitCT,"value")$(allt.val >= 2022+10) ;
) ;

$ifthen.unit %unitdata%=='ABB'
*Created using .\\capacitydata\\writecapdat.R
table windretirements(i,v,rs,allt) "--MW-- raw prescribed capacity retirement data for non-RSC tech"
$offlisting
$ondelim
$include inputs_case%ds%wind_retirements.csv
$offdelim
$onlisting
;
$endif.unit

table hintage_data(i,v,r,allt,*) "table of existing unit characteristics written by writehintage.r"
$offlisting
$ondelim
$include inputs_case%ds%hintage_data.csv
$offdelim
$onlisting
;


*Created using input_processing\R\writecapdat.R
parameter binned_capacity(i,v,r,allt) "existing capacity (that is not rsc, but including distPV) binned by heat rates" ;

binned_capacity(i,v,r,allt) = hintage_data(i,v,r,allt,"cap") ;


parameter maxage(i) "maximum age for technologies" ;

maxage(i) = 100 ;
maxage(i)$gas(i) = 55 ;
maxage(i)$coal(i) = 70 ;
maxage(i)$wind(i) = 30 ;
maxage(i)$upv(i) = 30 ;
maxage(i)$dupv(i) = 30 ;
maxage("biopower") = 45 ;
maxage(i)$geo(i) = 30 ;
maxage("nuclear") = 80 ;
maxage(i)$hydro(i) = 100 ;
maxage(i)$csp(i) = 30 ;
maxage(i)$battery(i) = 15 ;

*loading in battery mandate here to avoid conflicts in calculation of valcap
parameter batterymandate(r,i,t) "--MW-- cumulative battery mandate levels"
/
$offlisting
$ondelim
$include inputs_case%ds%storage_mandates.csv
$offdelim
$onlisting
/
;

* battery mandate in odd years is the average over
* the two surrounding years (if after 2018)
batterymandate(r,i,t)$[oddyears(t)$(yeart(t) >= 2018)] =
  (batterymandate(r,i,t-1) + batterymandate(r,i,t+1)) / 2 ;


*=============================
* Resource supply curve setup
*=============================

set rscbin "Resource supply curves bins" /bin1*bin5/,
    sc_cat "supply curve categories (capacity and cost)"
      /cap "capacity avaialable",
      cost "cost of capacity"/,
    rscfeas(r,rs,i,rscbin) "feasibility set for r s i and bins" ;

alias(rscbin,arscbin) ;

set refurb_cond(i,v,r,rs,t,tt,rscbin) "set to indicate whether a tech and vintage combination from year tt can be refurbished in year t" ;
refurb_cond(i,v,r,rs,t,tt,rscbin) = no ;

*written by R\\writesupplycurves.r
parameter rsc_dat(r,rs,i,rscbin,sc_cat) "--unit vary-- resource supply curve data for renewables with capacity in MW and costs in $/MW"
$offlisting
$include inputs_case%ds%rsc_combined.txt
$onlisting
;

parameter rsc_dat_geo(i,r,sc_cat) "--units vary-- resource supply curve data for geothermal with capacity in MW and costs in $/MW"
/
$offlisting
$ondelim
$include inputs_case%ds%geo_rsc.csv
$offdelim
$onlisting
/
;

parameter geo_discovery(t) "--fraction-- fraction of undiscovered geothermal that has been 'discovered'"
/
$offlisting
$ondelim
$include inputs_case%ds%geo_discovery.csv
$offdelim
$onlisting
/
;


*geothermal can all get assigned to bin1 and is only considered at the BA level
rsc_dat(r,"sk",i,"bin1",sc_cat)$geo(i) = rsc_dat_geo(i,r,sc_cat) ;

*Convert geothermal supply curve costs from 2015$ to 2004$ and from $/kW to $/MW
rsc_dat(r,"sk",i,"bin1","cost")$geo(i) = deflator('2015') * rsc_dat(r,"sk",i,"bin1","cost") * 1000 ;

*need to adjust units for pumped hydro costs from $ / KW to $ / MW
rsc_dat(r,rs,"pumped-hydro",rscbin,"cost") = rsc_dat(r,rs,"pumped-hydro",rscbin,"cost") * 1000 ;

* Add capacity in Mexico to account to prescribed builds
rsc_dat(r,"s357","wind-ons_3","bin1","cost")$r_rs(r,"s357") =  rsc_dat(r,"s32","wind-ons_3","bin1","cost") ;
rsc_dat(r,"s357","wind-ons_3","bin1","cap")$r_rs(r,"s357") = 155.1 ;

*following set indicates which combinations of r, s, and i are possible
*this is based on whether or not the bin has capacity available
rscfeas(r,rs,i,rscbin)$rsc_dat(r,rs,i,rscbin,"cap") = yes ;

rscfeas(r,rs,i,rscbin)$[csp2(i)$sum{ii$[csp1(ii)$csp2(i)$tg_rsc_cspagg(ii,i)], rscfeas(r,rs,ii,rscbin) }] = yes ;

rscfeas(r,rs,i,rscbin)$[not rfeas(r)] = no ;

*input spur line costs for wind, upv, dupv, and csp are all in 2015$ so convert to 2004$
rsc_dat(r,rs,i,rscbin,"cost")$[wind(i) or upv(i) or dupv(i) or csp(i)] = deflator("2015") * rsc_dat(r,rs,i,rscbin,"cost") ;


parameter binned_heatrates(i,v,r,allt) "--mmBTU / MWh-- existing capacity binned by heat rates" ;
binned_heatrates(i,v,r,allt) = hintage_data(i,v,r,allt,"wHR") ;


$ifthen.unit %unitdata%=='EIA-NEMS'
* Created using .\\capacitydata\\capacity_exog_wind.py
table exog_wind_by_trg(i,v,r,rs,t,*) "existing wind capacity binned by TRG"
$offlisting
$ondelim
$include inputs_case%ds%exog_wind_by_trg.csv
$offdelim
$onlisting
;
$endif.unit



parameter avail_retire_exog_rsc "--MW-- available retired capacity for refurbishments" ;
avail_retire_exog_rsc(i,v,r,rs,t) = 0 ;

set refurbtech(i) "technologies that can be refurbished" ;
refurbtech(i)$wind(i) = yes ;
refurbtech(i)$upv(i) = yes ;
refurbtech(i)$dupv(i) = yes ;


table near_term_wind_capacity(r,t) "MW of cumulative wind capacity in the build pipeline"
$offlisting
$ondelim
$include inputs_case%ds%wind_cap_reg.csv
$offdelim
$onlisting
;

parameter near_term_cap_limits(tg,r,t) "MW of cumulative capacity in project pipelines to limit near-term builds" ;
near_term_cap_limits("wind",r,t) = near_term_wind_capacity(r,t) ;



parameter capacity_exog(i,v,r,rs,t)        "--MW-- exogenously specified capacity",
          m_capacity_exog(i,v,r,t)         "--MW-- exogenous capacity used in the model",
          geo_cap_exog(i,r)                "--MW-- existing geothermal capacity"
/
$offlisting
$include inputs_case%ds%geoexist.txt
$onlisting
/
;


* existing capacity equals all 2010 capacity less retirements
* here we use the max of zero or that number to avoid any errors
* with variables that are gte to zero
* also have expiration of capital if t - tfirst is greater than the maximum age
* note the first conditional limits this calculation to units that
* do NOT have their capacity binned by heat rates (this include distPV for reasons explained below)
capacity_exog(i,"init-1",r,"sk",t)${[yeart(t)-sum{tt$tfirst(tt),yeart(tt)}<maxage(i)]$r_rs(r,"sk")$rb(r)} =
                                 max(0,sum{UnitCT,capnonrsc(i,r,UnitCT,"value")
                                       - sum{allt$[allt.val <= t.val],  prescribedretirements(allt,r,i,UnitCT,"value") }
                                        }
                                    ) ;

*reset any exogenous capacity that is also specified in binned_capacity
*as these are computed based on bins specified by the numhintage global
*in the data-writing files
capacity_exog(i,v,r,rs,t)$[sum{(rr,vv,allt),binned_capacity(i,vv,rr,allt)}] = 0 ;


capacity_exog("hydED","init-1",r,"sk",t)$r_rs(r,"sk") = sum{UnitCT,caprsc("hydED",r,"sk",UnitCT,"value")} ;
capacity_exog("hydEND","init-1",r,"sk",t)$r_rs(r,"sk") = sum{UnitCT,caprsc("hydEND",r,"sk",UnitCT,"value")} ;


*all binned capacity is for rs == sk
capacity_exog(i,v,r,"sk",t)$[r_rs(r,"sk")$sum{allt,binned_capacity(i,v,r,allt)}$rb(r)] =
               sum{allt$att(allt,t),binned_capacity(i,v,r,allt)} ;

*reset all wind exogenous capacity levels
capacity_exog(i,v,r,rs,t)$wind(i) = 0 ;

$ifthen %unitdata% == 'ABB'
*exogenous wind capacity is that which has not retired yet
*NB this is a 'trick' that is used to compute the existing wind capaicty by class
*in that it is the sum of future retirements
capacity_exog(i,v,r,rs,t)$[r_rs(r,rs)$wind(i)] = sum{allt$[year(allt)>=yeart(t)], windretirements(i,v,rs,allt) }$r_rs(r,rs) ;
*fill in odd years with average values
capacity_exog(i,v,r,rs,t)$[r_rs(r,rs)$wind(i)$oddyears(t)] = (capacity_exog(i,v,r,rs,t-1) + capacity_exog(i,v,r,rs,t+1)) / 2 ;
$endif

$ifthen %unitdata% == 'EIA-NEMS'
capacity_exog(i,v,r,rs,t)$[r_rs(r,rs)$wind(i)] = exog_wind_by_trg(i,v,r,rs,t,"value") ;
$endif


*fill in odd years' values for distpv
capacity_exog("distpv",v,r,"sk",t)$oddyears(t) =
    (capacity_exog("distpv",v,r,"sk",t-1) + capacity_exog("distpv",v,r,"sk",t+1)) / 2 ;

capacity_exog("distpv",v,r,"sk",t)$oddyears(t) = (capacity_exog("distpv",v,r,"sk",t-1) + capacity_exog("distpv",v,r,"sk",t+1)) / 2 ;

*capacity for geothermal is determined through forcing of prescribed builds
*geothermal is also not a valid technology and rather a placeholder
capacity_exog("geothermal",v,r,rs,t) = 0 ;

*capacity for hydro is specified for technologies in RSC techs
*ie hydro has specific classes (e.g. HydEd) that are specified
*separately, therefore the general 'hydro' category is not needed
capacity_exog("hydro",v,r,rs,t) = 0 ;

*set Canadian imports as prescribed capacity
capacity_exog("can-imports","init-1",rb,"sk",t) = smax(szn,(can_imports_szn(rb,szn,t) / sum{h$h_szn(h,szn), hours(h) })) ;


parameter remainder(i,r,rs) "remaining amount of capacity in rscbin after existing stock has been deducted",
          totcap(i,r,rs) "total existing capacity as of 2010" ;

set windloop(i) /wind-ons_1*wind-ons_10/ ;

totcap(i,r,rs)$wind(i) = sum{v, capacity_exog(i,v,r,rs,"2010") } ;
remainder(i,r,rs) = totcap(i,r,rs) ;

parameter rsc_copy(r,rs,i,rscbin,sc_cat) "copy of resource supply curve data for use in deducting current capacity" ;
rsc_copy(r,rs,i,rscbin,"cap")  = rsc_dat(r,rs,i,rscbin,"cap") ;
rsc_copy(r,rs,i,rscbin,"cost") = rsc_dat(r,rs,i,rscbin,"cost") ;

alias(rscbin,arb)

loop(arb,
    rsc_dat(r,rs,i,arb,"cap")$rscfeas(r,rs,i,arb) = max(0,rsc_dat(r,rs,i,arb,"cap") - remainder(i,r,rs)) ;
    remainder(i,r,rs) = max(0,remainder(i,r,rs) - rsc_copy(r,rs,i,arb,"cap"))
  ) ;

*if you've declined in value
avail_retire_exog_rsc(i,v,r,rs,t)$[refurbtech(i)$(capacity_exog(i,v,r,rs,t-1) > capacity_exog(i,v,r,rs,t))] =
    capacity_exog(i,v,r,rs,t-1) - capacity_exog(i,v,r,rs,t) ;

avail_retire_exog_rsc(i,v,r,rs,t)$[not initv(v)] = 0 ;

m_capacity_exog(i,v,rb,t) = capacity_exog(i,v,rb,"sk",t) ;
m_capacity_exog(i,v,rs,t)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs), capacity_exog(i,v,r,rs,t) } ;
m_capacity_exog(i,"init-1",r,t)$geo(i) = geo_cap_exog(i,r) ;
*remove any tiny amounts of capacity
m_capacity_exog(i,v,r,t) = round(m_capacity_exog(i,v,r,t),3);



set cap_agg(r,r) "set for aggregated resource regions to BAs"
    valcap(i,v,r,t) "i, v, r, and t combinations that are allowed for capacity",
    valcap_irt(i,r,t) "i, r, and t combinations that are allowed for capacity",
    valinv(i,v,r,t) "i, v, r, and t combinations that are allowed for investments",
    valgen(i,v,r,t) "i, v, r, and t combinations that are allowed for generation",
    m_refurb_cond(i,v,r,t,tt) "i v r combinations that are built in tt that can be refurbished in t",
    m_rscfeas(r,i,rscbin)            "--qualifier-- feasibility conditional for investing in RSC techs"
;

cap_agg(r,rs)$[(not sameas(rs,"sk"))$r_rs(r,rs)] = yes ;
cap_agg(r,rb)$sameas(r,rb) = yes ;

  m_rscfeas(rb,i,rscbin) = rscfeas(rb,"sk",i,rscbin) ;
  m_rscfeas(rs,i,rscbin)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs), rscfeas(r,rs,i,rscbin) } ;
  m_rscfeas(r,i,rscbin)$[sum{ii$tg_rsc_cspagg(ii, i),m_rscfeas(r,ii,rscbin)}] = yes ;
  m_rscfeas(r,i,rscbin)$[not rfeas_cap(r)] = no ;



Parameter required_prescriptions(pcat,r,rs,t) "--MW-- total required prescriptions",
          m_required_prescriptions(pcat,r,t)  "--MW-- required prescriptions by year (cumulative)" ;

*following does not include wind
*conditional here is due to no prescribed retirements for RSC tech
*nb that distpv is an rsc tech but is handled different via binned_capacity as explained above
required_prescriptions(pcat,rb,"sk",t)
          = sum{(tt,UnitCT)$[yeart(t)>=yeart(tt)], prescribednonrsc(tt,pcat,rb,UnitCT,"value") } ;


required_prescriptions(pcat,r,rs,t)$[r_rs(r,rs)$sum{tt$[yeart(t)>=yeart(tt)], prescribedrsc(tt,pcat,r,rs,"value") }
                                    + sum{UnitCT,caprsc(pcat,r,rs,UnitCT,"value") }
                                    ]
        = sum{(tt)$[(yeart(t) >= yeart(tt))], prescribedrsc(tt,pcat,r,rs,"value") }
        + sum{UnitCT, caprsc(pcat,r,rs,UnitCT,"value") }
;


  m_required_prescriptions(pcat,rb,t) = required_prescriptions(pcat,rb,"sk",t) ;
  m_required_prescriptions(pcat,rs,t)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs), required_prescriptions(pcat,r,rs,t) } ;
*remove csp-ns prescriptions at the BA level
  m_required_prescriptions("csp-ns",rb,t) = 0 ;


set force_pcat(pcat,t) "conditional to indicate whether the force prescription equation should be active for pcat" ;

force_pcat(pcat,t)$[
* it is before the first year
                    (yeart(t)<=firstyear_pcat(pcat))
* it is the sameas wind and there are near term cap limits
                      or (sameas(pcat,"wind-ons") and sum{(rr,tt)$(yeart(tt)<=yeart(t)),near_term_cap_limits("wind",rr,t)})
* it is gas-ct (with a first year of 2010) and there are required prescriptions
                      or (sameas(pcat,"gas-ct") and sum{(rr,tt)$(yeart(tt)<=yeart(t)),m_required_prescriptions("gas-ct",rr,t)})
*it is offshore wind and there are required prescriptions
                      or (sameas(pcat,"wind-ofs") and
                            sum{(tt,rr)$(yeart(tt)<yeart(t)),m_required_prescriptions("wind-ofs",rr,tt)})
                   ] = yes ;


force_pcat(pcat,t)$[(yeart(t)>2020) and ((not sameas(pcat,"wind-ofs"))
                    and (not sameas(pcat,"wind-ofs")))] = no ;

*removals from force_pcat
force_pcat("distpv",t) = no ;
force_pcat("hydro",t) = no ;

*disable forcing of pcats if they are represented with an aggregate category
force_pcat(pcat,t)$[(sum{(ppcat,ii)$sameas(pcat,ii), prescriptivelink0(ppcat,ii) } )
*or if they are geothermal technologies since these are
* considered via the geothermal prescriptive category
                   or sum{i$[geo(i)$sameas(i,pcat)$(not sameas(i,"geothermal"))],1}
                   ] = no ;


*==========================================
* -- Valid Capacity and Generation Sets --
*==========================================

* -- valcap specification --
* first all available techs are included
* then we remove those as specified

* start with a blank slate
valcap(i,v,r,t) = no ;

*existing plants are enabled if not in ban(i)
valcap(i,v,r,t)$[m_capacity_exog(i,v,r,t)$(not ban(i))$tmodel_new(t)$rfeas_cap(r)] = yes ;

*enable all new classes for balancing regions
*if available (via ict) and if not an rsc tech
*and if it is not in ban or bannew
*the year also needs to be greater than the first year indicated
*for that specific class (this is the summing over tt portion)
*or it needs to be specified in prescriptivelink
valcap(i,newv,rb,t)$[rfeas(rb)$(not rsc_i(i))$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $(sum{tt$(yeart(tt)<=yeart(t)), ict(i,newv,tt) })
                    ]  = yes ;

*for rsc technologies, enabled if m_rscfeas is populated
*similarly to non-rsc technologies except now all regions
*can be populated (rb vs r) and there is the additional condition
*that m_rscfeas must contain values in at least one rscbin
valcap(i,newv,r,t)$[rfeas_cap(r)$rsc_i(i)$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $sum{rscbin, m_rscfeas(r,i,rscbin) }
                    $sum{tt$(yeart(tt)<=yeart(t)), ict(i,newv,tt) }
                    ]  = yes ;

*make sure sk region does not enter valcap
valcap(i,v,"sk",t) = no ;

*NEW capacity only valid in historical years if and only if it has required prescriptions
*logic here is that we don't want to populate the constraint with CAP <= 0 and instead
*want to simply remove the consideration for CAP altogether and make the constraint unnecessary
*note that the constraint itself is also conditioned on valcap

*therefore remove the consideration of valcap if...
valcap(i,newv,r,t)$[
*the constraint would be active via force_pcat
                  sum{pcat$prescriptivelink(pcat,i), force_pcat(pcat,t) }
*if there are NO required prescriptions
                   $(not sum{pcat$prescriptivelink(pcat,i),
                      m_required_prescriptions(pcat,r,t) } )
*gas-ct treated as a safety valve for operational infeasibilties
                   $(not sameas(i,"gas-ct"))
                   $(yeart(t)<firstyear(i))
                   $(not batterymandate(r,i,t))
                  ] = no ;

*remove undisc geotechs until their first year since they are not able
*to meet the requirement for geothermal prescriptions
valcap(i,newv,r,t)$[(i_geotech(i,"undisc_pbinary") or i_geotech(i,"undisc_pflash"))
                   $(yeart(t)<firstyear(i))] = no ;

*- geothermal switch settings
* N.B. if geothermal set to 2, no removals are necessary

* if switch is equal to zero, remove all geothermal technologies
if(Sw_Geothermal = 0,
  valcap(i,v,r,t)$geo(i) = no ;
) ;

* if equal to one, only keep the non-extended default representation
if(Sw_Geothermal = 1,
  valcap(i,v,r,t)$geo_extra(i) = no ;
) ;

* Restrict valcap for storage techs based on Sw_Storage switch
if(Sw_Storage = 0,
  valcap(i,v,r,t)$storage_no_csp(i) = no ;
  Sw_BatteryMandate = 0 ;
) ;

* Restrict valcap for ccs techs based on Sw_CCS switch
if(Sw_CCS = 0,
  valcap(i,v,r,t)$ccs(i) = no ;
) ;

*csp-ns is only allowed in regions where prescriptions are required
valcap("csp-ns",newv,r,t) = no ;
valcap("csp-ns",newv,r,t)$[m_required_prescriptions("csp-ns",r,t)
                          $sum{tt$(yeart(tt)<=yeart(t)), ict("csp-ns",newv,tt)} ] = yes ;

valcap(i,v,r,t)$[not tmodel_new(t)] = no;

* Add aggregations of valcap
valcap_irt(i,r,t) = sum{v, valcap(i,v,r,t) } ;


* -- valinv specification --
valinv(i,v,r,t) = no ;
valinv(i,v,r,t)$[valcap(i,v,r,t)$ict(i,v,t)] = yes ;


* -- valgen specification --
* if the balancing area and/or its
* resource supply regions have valid capacity
*then you can generate from it

valgen(i,v,r,t) = no ;
valgen(i,v,r,t)$[sum{rr$cap_agg(r,rr),valcap(i,v,rr,t)}] = yes ;


* -- m_refurb_cond specification --

* technologies can be refurbished if...
*  they are part of refurbtech
*  the years from t to tt are beyond the expiration of the tech (via maxage)
*  it was a valid capacity in t and in tt
*  it was a valid investment in year tt (via ict)
m_refurb_cond(i,newv,r,t,tt)$[refurbtech(i)
                              $(yeart(tt)<yeart(t))
                              $(yeart(t) - yeart(tt) > maxage(i))
                              $valcap(i,newv,r,t)$valcap(i,newv,r,tt)
                              $ict(i,newv,tt)
                             ] = yes ;


* -- inv_cond specification --

*if there is a link between the bintage and the year
*all previous years
*if the unit we invested in is not retired...
inv_cond(i,newv,r,t,tt)$[(not ban(i))$(not bannew(i))
                      $tmodel_new(t)$tmodel_new(tt)
                      $(yeart(tt) <= yeart(t))
                      $valinv(i,newv,r,tt)
                      $(ord(t)-ord(tt) < maxage(i))
                      ] = yes ;

*csp-ns needs to be able to be built in
*the first year to meet required prescriptions
*after that, it is replaced by detailed csp technologies
inv_cond("csp-ns",newv,r,t,tt) = no ;

inv_cond("csp-ns",newv,r,t,tt)$[
                      tmodel_new(t)$tmodel_new(tt)
                      $(yeart(tt) <= yeart(t))
*only allow csp to be built in years where prescriptions are enforced
                      $(yeart(tt) <= firstyear("csp-ns"))
                      $valinv("csp-ns",newv,r,tt)
                      $(ord(t)-ord(tt) < maxage("csp-ns"))
                      ] = yes ;


*=====================================
* --- Regional Carbon Constraints ---
*=====================================


Set RGGI_States(st) "states facing RGGI regulation" /MA, CT, DE, MD, ME, NH, NJ, NY, RI, VT/ ,
    RGGI_r(r) "BAs facing RGGI regulation",
    AB32_r(r) "BAs facing AB32 regulation" ;

RGGI_r(r)$[sum{st$RGGI_States(st),r_st(r,st)}] = yes ;
AB32_r(r)$r_st(r,"CA") = yes ;

Scalar RGGI_start_yr "RGGI Start year" /2012/,
       AB32_start_yr "AB32 start year" /2014/ ;

parameter RGGICap(t) "--metric ton-- CO2 emissions cap for RGGI states"
/
$offlisting
$ondelim
$include inputs_case%ds%rggicon.csv
$offdelim
$onlisting
/ ;

parameter AB32Cap(t) "--metric ton-- CO2 emissions cap for AB-32 requirement"
/
$offlisting
$ondelim
$include inputs_case%ds%ab32con.csv
$offdelim
$onlisting
/ ;

*assuming 2016 value from:
*https://ww3.arb.ca.gov/cc/inventory/pubs/reports/2000_2016/ghg_inventory_trends_00-16.pdf
Scalar AB32_Import_Emit "--metric ton CO2 / MWh-- emissions measured on AB32 Imports" /0.26/ ;



*====================================
*         --- RPS data ---
*====================================

set RPSCat                    "RPS constraint categories, including clean energy standards"
                                /RPS_All, RPS_Bundled, CES, CES_Bundled, RPS_Wind, RPS_Solar/,
    RPSAll(i,st)              "technologies that can fulfill the aggregated RPS requirement by state",
    RPSCat_i(RPSCat,i,st)     "mapping between rps category and technologies for each state",
    RPS_bangeo(st)            "states that do not allow geothermal to be used in RPS" /IL, MN, MO, NY/,
    RecMap(i,RPSCat,st,ast,t) "Mapping set for technologies to RPS categories and indicates if st can trade with ast [final set used in the supply model]",
    RecStates(RPSCat,st,t)    "states that have a RPS requirement for each RPSCat",
    RecTrade(RPSCat,st,ast,t) "mapping set between states that can trade RECs with each other",
    RecTech(RPSCat,st,i,t)    "set to indicate which technologies and classes can contribute to a state's RPSCat" ;


Parameter RecPerc(RPSCat,st,t) "--fraction-- fraction of total generation for each state that must be met by RECs for each category"
          RPSTechMult(i,st)    "--fraction-- fraction of generation from each technology that counts towards the RPS"
;

Scalar RPS_StartYear "Start year for states RPS policies" /2020/ ;


RPSAll(i,st)$wind(i) = yes ;
RPSAll(i,st)$upv(i) = yes ;
RPSAll(i,st)$csp(i) = yes ;
RPSAll(i,st)$dupv(i) = yes ;
RPSAll("distpv",st)$[not sameas(st,"ca")] = yes ;
RPSAll("biopower",st) = yes ;
RPSAll("hydro",st) = yes ;
*treat canadian imports similar to hydro
RPSAll(i,st)$[geo(i)$(not RPS_bangeo(st))] = yes ;
RPSAll(i,st)$(RPSAll("hydro",st)$canada(i)) = yes ;
RPSAll("MHKwave",st) = yes ;

*rpscat definitions for each technology
RPSCat_i("RPS_All",i,st)$RPSAll(i,st) = yes ;
RPSCat_i("RPS_Wind",i,st)$wind(i) = yes ;
RPSCat_i("RPS_Solar",i,st)$[upv(i) or dupv(i) or sameas(i,"distpv")] = yes ;
RPSCat_i("CES",i,st)$[RPSCAT_i("RPS_All",i,st) or sameas(i,"nuclear") or hydro(i)] = yes ;

* Massachusetts CES allows for CCS techs, but does not allow for existing hydro, so we don't allow any hydro
RPSCat_i("CES",'gas-cc-ccs','MA') = yes ;
RPSCat_i("CES",'coal-ccs','MA') = yes ;
RPSCat_i("CES",i,'MA')$hydro(i) = no ;

*california does not accept distpv credits
RPSCat_i(RPSCat,"distpv","ca") = no ;

*created using input_processing\R\rpsgather.R
Table RECPerc_in(allt,st,RPSCat) "--fraction-- requirement for state RPS"
$offlisting
$ondelim
$include inputs_case%ds%recperc.csv
$offdelim
$onlisting
;

Table CES_Perc(st,t) "--fraction-- requirement for clean energy standard"
$offlisting
$ondelim
$include inputs_case%ds%ces_fraction.csv
$offdelim
$onlisting
;



RecPerc(RPSCat,st,t) = sum{allt$att(allt,t), RECPerc_in(allt,st,RPSCat) } ;
RecPerc("CES",st,t) = CES_Perc(st,t) ;

*some links (value in RECtable = 2) restricted to bundled trading, while
*some (value in RECtable = 1) allowed to also trade unbundled RECs
*created using input_processing\R\rpsgather.R
table rectable(st,ast) "[1] allowed to trade unbundled recs [2] implies allowed to bundled trade"
$offlisting
$ondelim
$include inputs_case%ds%rectable.csv
$offdelim
$onlisting
;

table acp_price(st,t) "$/REC - safety valve price for RPS constraint"
$offlisting
$ondelim
$include inputs_case%ds%acp_prices.csv
$offdelim
$onlisting
;


RecStates(RPSCat,st,t)$[RecPerc(RPSCat,st,t) or sum(ast,rectable(ast,st))] = yes ;

*if both states have an RPS for the RPSCat and if they're allowed to trade, they can trade
RecTrade(RPSCat,st,ast,t)$((rectable(ast,st)=1)$RecStates(RPSCat,ast,t)) = yes ;

*if both states have an RPS for the RPSCat and if they're allowed to trade, they can trade
RecTrade("RPS_bundled",st,ast,t)$[(rectable(ast,st)=2)$RecStates("RPS_all",ast,t)] = yes ;
RecTrade("CES_bundled",st,ast,t)$[(rectable(ast,st)=2)$RecStates("CES",ast,t)] = yes ;


RecTech(RPSCat,st,i,t)$(RPSCat_i(RPSCat,i,st)$RecStates(RPSCat,st,t)) = yes ;
RecTech(RPSCat,st,i,t)$(hydro(i)$RecTech(RPSCat,st,"hydro",t)) = yes ;
RecTech("RPS_Bundled",st,i,t)$[RecTech("RPS_All",st,i,t)] = yes ;

RecTech("CES",st,i,t)$[(RecTech("RPS_All",st,i,t)) or sameas(i,"nuclear") or hydro(i)] = yes ;
RecTech("CES_Bundled",st,i,t)$[RecTech("RPS_All",st,i,t)] = yes ;


*california does not accept distpv credits
RecTech(RPSCat,"ca","distPV",t) = no ;
*make sure you cannot get credits from banned techs
*note we do not restrict by bannew here but the creation of
*RECS from bannew techs will be restricted via valgen
RecTech(RPSCat,st,i,t)$ban(i) = no ;

*created using input_processing\R\rpsgather.R
parameter RPSHydroFrac(st) "fraction of hydro RPS credits that can count towards RPS goals"
/
$offlisting
$ondelim
$include inputs_case%ds%hydrofrac.txt
$offdelim
$onlisting
/
;

RPSTechMult(i,st) = 1 ;
RPSTechMult(i,st)$hydro(i) = RPSHydroFrac(st) ;


RecMap(i,RPSCat,st,ast,t)$[
*if the receiving state has a requirement for RPSCat
      RecPerc(RPSCat,ast,t)
*if both states can use that technology
      $Rectech(RPScat,st,i,t)
      $RecTech(RPSCat,ast,i,t)
*if the state can trade
      $RecTrade(RPSCat,st,ast,t)
               ] = yes ;

RecMap(i,"RPS_bundled",st,ast,t)$(
*if the receiving state has a requirement for RPSCat
      RecPerc("RPS_all",ast,t)
*if both states can use that technology
      $RecTech("RPS_bundled",st,i,t)
      $RecTech("RPS_bundled",ast,i,t)
*if the state can trade
      $RecTrade("RPS_bundled",st,ast,t)
               ) = yes ;


RecMap(i,"CES_bundled",st,ast,t)$(
*if the receiving state has a requirement for RPSCat
      RecPerc("CES",ast,t)
*if both states can use that technology
      $RecTech("CES_bundled",st,i,t)
      $RecTech("CES_bundled",ast,i,t)
*if the state can trade
      $RecTrade("CES_bundled",st,ast,t)
               ) = yes ;

*states can "import" their own RECs
RecMap(i,RPSCat,st,ast,t)$[
    sameas(st,ast)
    $RecTech(RPSCat,st,i,t)
    $RecPerc(RPSCat,st,t)
      ] = yes ;

*states that allow hydro to fulfill their RPS requirements can trade hydro recs
RecMap(i,RPSCat,st,ast,t)$[
      hydro(i)
      $RPSTechMult(i,st)
      $RPSTechMult(i,ast)
      $RecMap("hydro",RPSCat,st,ast,t)
      ] = yes ;


*created using input_processing\R\rpsgather.R
parameter RPS_oosfrac(st) "fraction of RECs from out of state that can meet the RPS"
/
$offlisting
$ondelim
$include inputs_case%ds%oosfrac.txt
$offdelim
$onlisting
/
;

parameter RPS_unbundled_limit(st) "--fraction-- upper bound of state RPS that can be met with unbundled RECS" ;
RPS_unbundled_limit("CA") = 0.1 ;


parameter national_gen_frac(t) "--fraction-- national fraction of load + losses that must be met by specified techs"
/
$ondelim
$include inputs_case%ds%national_gen_frac.csv
$offdelim
/
;

parameter nat_gen_tech_frac(i) "--fraction-- fraction of each tech generation that may be counted toward eq_national_gen"
/
$ondelim
$include inputs_case%ds%nat_gen_tech_frac.csv
$offdelim
/
;

table offshore_cap_req(st,t) "--MW-- offshore wind capacity requirement under RPS rules by state"
$offlisting
$ondelim
$include inputs_case%ds%offshore_req.csv
$offdelim
$onlisting
;


*====================
* --- CSAPR Data ---
*====================

*current values of CSAPR caps are for 2017
scalar csapr_startyr "start year for CSAPR policy" /2017/ ;

* a CSAPR budget indicates the cap for trading whereas
* assurance indicates the maximum amount a state can emit regardless of trading
set csapr_cat "CSAPR regulation categories" /budget, assurance/,
*trading rules dictate there are two groups of states that can trade with eachother
    csapr_group "CSAPR trading group"       /cg1, cg2/ ;


table csapr_cap(st,csapr_cat) "--MT NOX-- maximum amount of emissions during the ozone season (May-September)"
$offlisting
$ondelim
$include inputs_case%ds%csapr_ozone_season.csv
$offdelim
$onlisting
;


set csapr_group1_ex(st) "CSAPR states that cannot trade with those in group 2" /AR, FL, LA, MS, OK/,
    csapr_group2_ex(st) "CSAPR states that cannot trade with those in group 1" /KS, MN, NE/,
    csapr_group_st(csapr_group,st) "final crosswalk set for use in modeling CSAPR trade relationships" ;

csapr_group_st("cg1",st)$[csapr_cap(st,"budget")$(not csapr_group1_ex(st))$stfeas(st)] = yes ;
csapr_group_st("cg2",st)$[csapr_cap(st,"budget")$(not csapr_group2_ex(st))$stfeas(st)] = yes ;

parameter h_weight_csapr(h) "hour weights for CSAPR ozone season constraints" ;
*assumption here is that the ozone season only cover 1/3 of the months
*in the spring and fall but the entire season in summer,
*therefore weighting each seasons emissions accordingly
h_weight_csapr(h)$h_szn(h,"spri") = 0.3333 ;
h_weight_csapr(h)$h_szn(h,"summ") = 1 ;
h_weight_csapr(h)$h_szn(h,"fall") = 0.3333 ;



*==============================
* --- Transmission Inputs ---
*==============================

* --- transmission sets ---

set trtype                 "transmission capacity type" /AC, DC/
    trancap_fut_cat        "categories of near-term transmission projects that describe the likelihood of being completed" /certain, possible/
    tscfeas(r,vc)          "set to declare which transmission substation supply curve voltage classes are feasible for which regions"
    routes(r,rr,trtype,t)  "final conditional on transmission feasibility"
    opres_routes(r,rr,t)   "final conditional on operating reserve flow feasibility"
;

* --- initial transmission capacity ---
* NOTE: The transmission capacity input data are defined in one direction for each region-to-region pair with the lowest region number listed first.

parameter trancap_init_ac(r,rr) "--MW-- initial AC transmission capacity (tracked in one direction only, low to high region number)" ;
execute "=csv2gdx inputs_case%ds%transmission_capacity_initial.csv output=inputs_case%ds%trancap_init_ac.gdx id=trancap_init_ac index=(1,2) values=3 useHeader=y" ;
execute_load "inputs_case%ds%trancap_init_ac.gdx", trancap_init_ac ;

parameter trancap_init_dc(r,rr) "--MW-- initial DC transmission capacity (tracked in one direction only, low to high region number)" ;
execute "=csv2gdx inputs_case%ds%transmission_capacity_initial.csv output=inputs_case%ds%trancap_init_dc.gdx id=trancap_init_dc index=(1,2) values=4 useHeader=y" ;
execute_load "inputs_case%ds%trancap_init_dc.gdx", trancap_init_dc ;

parameter trancap_init(r,rr,trtype) "--MW-- intial transmission capacity by type (tracked in one direction, low to high region number)" ;
trancap_init(r,rr,"AC")$trancap_init_ac(r,rr) = trancap_init_ac(r,rr) ;
trancap_init(r,rr,"DC")$trancap_init_dc(r,rr) = trancap_init_dc(r,rr) ;

parameter trancap_init_bd(r,rr,trtype) "--MW-- intial transmission capacity by type (tracked in both directions)---this is used for the ReEDS/PLEXOS linkage" ;
trancap_init_bd(r,rr,trtype)$[trancap_init(r,rr,trtype) or trancap_init(rr,r,trtype)] = trancap_init(r,rr,trtype) + trancap_init(rr,r,trtype) ;

* --- future transmission capacity ---
* NOTE: The transmission capacity input data are defined in one direction for each region-to-region pair with the lowest region number listed first.

parameter trancap_fut_ac(r,rr,trancap_fut_cat,t) "--MW-- potential future AC transmission capacity (one direction)" ;
execute "=csv2gdx inputs_case%ds%transmission_capacity_future.csv output=inputs_case%ds%trancap_fut_ac.gdx id=trancap_fut_ac index=(1..4) values=5 useHeader=y" ;
execute_load "inputs_case%ds%trancap_fut_ac.gdx", trancap_fut_ac ;

parameter trancap_fut_dc(r,rr,trancap_fut_cat,t) "--MW-- potential future DC transmission capacity (one direction)" ;
execute "=csv2gdx inputs_case%ds%transmission_capacity_future.csv output=inputs_case%ds%trancap_fut_dc.gdx id=trancap_fut_dc index=(1..4) values=6 useHeader=y" ;
execute_load "inputs_case%ds%trancap_fut_dc.gdx", trancap_fut_dc ;

parameter trancap_fut(r,rr,trancap_fut_cat,t,trtype) "--MW-- potential future transmission capacity by type (one direction)" ;
trancap_fut(r,rr,trancap_fut_cat,t,"AC")$trancap_fut_ac(r,rr,trancap_fut_cat,t) = trancap_fut_ac(r,rr,trancap_fut_cat,t) ;
trancap_fut(r,rr,trancap_fut_cat,t,"DC")$trancap_fut_dc(r,rr,trancap_fut_cat,t) = trancap_fut_dc(r,rr,trancap_fut_cat,t) ;

* --- exogenously specified transmission capacity ---
* NOTE: The transmission capacity input data are defined in one direction for each region-to-region pair with the lowest region number listed first.

parameter trancap_exog(r,rr,trtype,t) "--MW-- cumulative exogenous transmission capacity (one direction)" ;
trancap_exog(r,rr,trtype,t) =
*initial transmission capacity
    + trancap_init(r,rr,trtype)
*plus all "certain" future transmission project capacity through the current year t
    + sum{(tt,trancap_fut_cat)$[(tt.val<=t.val)], trancap_fut(r,rr,"certain",tt,trtype)}
;

* --- valid transmission routes ---

*transmission routes are enabled if:
* (1) there is transmission capacity between the two regions
routes(r,rr,trtype,t)$(trancap_exog(r,rr,trtype,t) or trancap_exog(rr,r,trtype,t)) = yes ;
* (2) there is future capacity available between the two regions
routes(r,rr,trtype,t)$(sum{(tt,trancap_fut_cat)$(yeart(tt)<=yeart(t)),trancap_fut(r,rr,trancap_fut_cat,tt,trtype)}) = yes ;
* (3) there exists a route (r,rr) that is in the opposite direction as (rr,r)
routes(rr,r,trtype,t)$(routes(r,rr,trtype,t)) = yes ;

* operating reserve flows only allowed over AC lines
opres_routes(r,rr,t)$(routes(r,rr,"AC",t)) = yes ;

set samerto(r,rr) "binary indicator if two regions exist in the same rto: 1=same RTO, 0=not same RTO" ;
samerto(r,rr) = sum((rto,rto2)$[r_rto(r,rto)$r_rto(rr,rto2)$sameas(rto,rto2)], 1) ;

*exclude operating reserve flows between two regions in different RTOs
opres_routes(r,rr,t)$[not samerto(r,rr)] = no ;

* --- transmission cost ---

Scalar cost_trandctie  "--$ per MW-- cost for DC intertie between interconnects" /200000/ ;

*created using input_processing\R\trangather.R
Parameter cost_tranline(r) "--$ per MW-mile-- cost of transmission line capacity for each region"
/
$offlisting
$ondelim
$include inputs_case%ds%transmission_line_cost.txt
$offdelim
$onlisting
/
;

*created using input_processing\R\trangather.R
table tsc_dat(r,sc_cat,vc) "--$ per MW (cost) or MW (cap)-- transmission substation supply curve cost and capacity by voltage class"
$offlisting
$ondelim
$include inputs_case%ds%substation_supply_curve.csv
$offdelim
$onlisting
;

parameter cost_transub(r,vc) "--$ per MW-- transmission substation supply curve cost by voltage class" ;
cost_transub(r,vc) = tsc_dat(r,"cost",vc) ;

* defined the transmission supply curve feasiblity condition based on non-zero capacity in the supply curve
tscfeas(r,vc)$(tsc_dat(r,"cap",vc)>0) = yes ;

parameter cost_hurdle(r,rr) "--$ per MWh-- cost for transmission hurdle rate"
          cost_hurdle_country(country) "--$ per MWh-- cost for transmission hurdle rate by country" /MEX 9.718968, CAN 2.389910/
;

* define hurdle rates between the US and Mexico
cost_hurdle(r,rr)$[((r_country(r,"MEX") and r_country(rr,"USA"))
              or (r_country(rr,"MEX") and r_country(r,"USA")))
            $sum{(trtype,t),routes(r,rr,trtype,t)}] = cost_hurdle_country("MEX") ;

* define hurdle rates between the US and Canada
cost_hurdle(r,rr)$[((r_country(r,"CAN") and r_country(rr,"USA"))
              or (r_country(rr,"CAN") and r_country(r,"USA")))
            $sum{(trtype,t),routes(r,rr,trtype,t)}] = cost_hurdle_country("CAN") ;

* --- transmission distance ---

* The distance for an AC cooridor is calculated by tracing the "least-cost" path that follows existing AC lines between the two representative nodes of (r,rr)
* Larger voltage lines have the lowest "cost" for tracing
parameter distance_ac(r,rr) "--miles-- distance between BAs for AC corridors" ;
execute "=csv2gdx inputs_case%ds%transmission_distance.csv output=inputs_case%ds%distance_ac.gdx id=distance_ac index=(1,2) values=3 useHeader=y" ;
execute_load "inputs_case%ds%distance_ac.gdx", distance_ac ;

* The distance for a DC corridor is the reported project distances
* The distance for a DC intertie corridor is the same as the AC distance
parameter distance_dc(r,rr) "--miles-- distance between BAs for DC corridors" ;
execute "=csv2gdx inputs_case%ds%transmission_distance.csv output=inputs_case%ds%distance_dc.gdx id=distance_dc index=(1,2) values=4 useHeader=y" ;
execute_load "inputs_case%ds%distance_dc.gdx", distance_dc ;

parameter distance(r,rr,trtype) "--miles-- distance between BAs by line type" ;
distance(r,rr,"AC")$distance_ac(r,rr) = distance_ac(r,rr) ;
distance(r,rr,"DC")$distance_dc(r,rr) = distance_dc(r,rr) ;

* --- transmission losses ---

parameter tranloss(r,rr,trtype) "transmission loss (%) between r and rr"
          tranloss_permile      "% per mile -- transmission loss for regional trade" /0.0001/,
          distloss              "distribution losses from bus to final consumption" /1.053/ ;
;

tranloss(r,rr,trtype) = tranloss_permile * distance(r,rr,trtype) ;

* --- high cost transmission ---

*If high cost transmission switch is on, triple transmission costs and double the losses
if(Sw_HighCostTrans = 1,
     cost_tranline(r) = cost_tranline(r) * 3 ;
     tranloss(r,rr,trtype) = tranloss(r,rr,trtype) * 2 ;
) ;

*============================
*   --- Fuel Prices ---
*============================
*Note - NG supply curve has its own section

set f fuel types / 'dfo','rfo', 'naturalgas', 'coal', 'uranium', 'biomass' / ;

set fuel2tech(f,i) "mapping between fuel types and generations"
   /
   coal.(coal-new,CoalOldScr,coalolduns,coal-ccs,coal-igcc),

   naturalgas.(gas-cc,gas-ct,o-g-s,gas-cc-ccs),

   uranium.(nuclear)

   biomass.(biopower,cofirenew,cofireold)
   / ;

*double check in case any sets have been changed.
fuel2tech("coal",i)$coal(i) = yes ;
fuel2tech("naturalgas",i)$gas(i) = yes ;

*===============================
*   Generator Characteristics
*===============================

set plantcat "catageries for plant characteristics" / capcost, fom, vom, heatrate, rte / ;

parameter plant_char(i,t,plantcat) "--units vary-- input plant characteristics"
/
$offlisting
$include inputs_case%ds%plantcharout.txt
$onlisting
/ ;

*from KE's original model
parameter data_heat_rate_init(r,i) "initial heat rate" ;

$gdxin inputs_case%ds%sply_inputs.gdx
$load data_heat_rate_init
$gdxin



*=========================================
* --- Capital costs ---
*=========================================

parameter cost_cap(i,t) "--2004$/MW-- overnight capital costs" ;
cost_cap(i,t) = plant_char(i,t,"capcost") ;

* Assigning csp-ns to have the same cost as csp2
cost_cap("csp-ns",t) = cost_cap("csp2_1",t) ;


table geocapmult(t,geotech) "geothermal category capital cost multipliers over time"
$offlisting
$ondelim
$include inputs_case%ds%geocapcostmult.csv
$offdelim
$onlisting
;

table hydrocapmult(t,i) "hydorpower capital cost multipliers over time"
$offlisting
$ondelim
$include inputs_case%ds%hydrocapcostmult.csv
$offdelim
$onlisting
;


scalar dupv_cost_cap_mult "price premium for dupv over upv" /1.087/ ;
*note from MRM
*avg of union and non-union total system cost (without transmission) between 10MW (DUPV) and 100MW (UPV) in:
*Ran Fu, Ted L James, Donald Chung, Douglas Gagne, Anthony Lopez, Aron Dobos. Economic Competitiveness of U.S.
*Utility-Scale Photovoltaics Systems in 2015: Regional Cost Modeling of Installed Cost ($/W) and LCOE ($/kWh).
*Forthcoming paper. Accepted by IEEE PVSC, 2015


set dupv_upv_corr(i,ii) "correlation set for cost of capital calculations of dupv"
/
  upv_1.dupv_1,
  upv_2.dupv_2,
  upv_3.dupv_3,
  upv_4.dupv_4,
  upv_5.dupv_5,
  upv_6.dupv_6,
  upv_7.dupv_7,
  upv_8.dupv_8,
  upv_9.dupv_9,
  upv_10.dupv_10
/ ;

cost_cap(i,t)$dupv(i) = sum{ii$dupv_upv_corr(ii,i),cost_cap(ii,t)} * dupv_cost_cap_mult ;


*====================
* --- Variable OM ---
*====================

*only one vom cost for hydro
scalar vom_hyd "--2004$/MWh-- hydropower VOM" /1.024417098/ ;

parameter cost_vom(i,v,r,t) "--2004$/MWh-- variable OM" ;

cost_vom(i,initv,r,t)$[(not Sw_BinOM)$valgen(i,initv,r,t)] = plant_char(i,'2010','vom') ;

*if binning historical plants cost_vom, still need to assign default values to new plants
cost_vom(i,newv,r,t)$[(Sw_BinOM)$valgen(i,newv,r,t)] = plant_char(i,t,'vom') ;

*if binning VOM and FOM costs, use the values written by writehintage.r for existing plants
cost_vom(i,initv,r,t)$[Sw_BinOM$valgen(i,initv,r,t)] = sum(allt$att(allt,t),hintage_data(i,initv,r,allt,"wVOM")) ;

*use default values if they are missing from the writehintage outputs
*but still active via valgen
cost_vom(i,initv,r,t)$[Sw_BinOM$(not cost_vom(i,initv,r,t))$valgen(i,initv,r,t)] =
                            plant_char(i,'2010','vom') ;

*VOM costs by v are averaged over the class's associated
*years divided by those values
cost_vom(i,newv,r,t)$[valgen(i,newv,r,t)$countnc(i,newv)] =
  sum{tt$ict(i,newv,tt), plant_char(i,tt,'vom') } / countnc(i,newv) ;

cost_vom(i,v,rb,t)$[valcap(i,v,rb,t)$hydro(i)] = vom_hyd ;

*=================
* --- Fixed OM ---
*=================

parameter cost_fom(i,v,r,t) "--2004$/MW-yr-- fixed OM" ;

*previous calculation (without tech binning)
cost_fom(i,v,r,t)$[(not Sw_binOM)$valcap(i,v,r,t)] = plant_char(i,t,'fom') ;

*if using binned costs, still need to assign default values to cost_fom for new plants
cost_fom(i,newv,r,t)$[(Sw_binOM)$valcap(i,newv,r,t)] = plant_char(i,t,'fom') ;

cost_fom(i,initv,r,t)$[Sw_BinOM$valcap(i,initv,r,t)] = sum(allt$att(allt,t),hintage_data(i,initv,r,allt,"wFOM")) ;

*use default values if they are missing from the writehintage outputs
*but still active via valgen
cost_fom(i,initv,r,t)$[Sw_BinOM$(not cost_fom(i,initv,r,t))$valgen(i,initv,r,t)] =
                            plant_char(i,'2010','fom') ;


table hyd_fom(i,r) "--$/MW-year -- Fixed O&M for hydro technologies"
$offlisting
$ondelim
$include inputs_case%ds%hyd_fom.csv
$offdelim
$onlisting
;

parameter geo_fom(i,r) "--$ per MW-yr-- geothermal fixed O&M costs"
/
$offlisting
$ondelim
$include inputs_case%ds%geo_fom.csv
$offdelim
$onlisting
/
;

*Convert geothermal FOM from 2015$ to 2004$ and from $/kW-yr to $/MW-yr
geo_fom(i,r) = geo_fom(i,r) * deflator('2015') * 1000 ;

*fom costs for a specific bintage is the average over that bintage's time frame
cost_fom(i,newv,r,t)$[valcap(i,newv,r,t)$countnc(i,newv)] =
  sum{tt$ict(i,newv,tt), plant_char(i,tt,'fom')  } / countnc(i,newv) ;


* -- FOM adjustments for nuclear plants
* Nuclear FOM cost adjustments are from the report from the IPM team titled
* 'Nuclear Power Plant Life Extension Cost Development Methodology' which indicates
* $1.25/kw increase per year for the first 10 years
* $1.81/kW increase per year for years 10-50
* $0.56/kW increase per year for year 50+
* A single step reduction of $25/kW in year 50
* These are applied in ReEDS relative to 2010 (i.e., year 1 = 2010)

parameter FOM_Adj_Nuclear(allt) "--$/MW-- Cumulative addition to nuclear FOM costs by year"
/
$offlisting
$ondelim
$include inputs_case%ds%nuke_fom_adj.csv
$offdelim
$onlisting
/
;

FOM_Adj_Nuclear(allt) = deflator("2017") * FOM_Adj_Nuclear(allt) ;

cost_fom("nuclear",initv,r,t)$[Sw_BinOM$valcap("nuclear",initv,r,t)] =
  cost_fom("nuclear",initv,r,t) + sum{allt$att(allt,t),FOM_Adj_Nuclear(allt)} ;


*note conditional here that will only replace fom
*for hydro techs if it is included in hyd_fom(i,r)
cost_fom(i,v,r,t)$[valcap(i,v,r,t)$hydro(i)$hyd_fom(i,r)] = hyd_fom(i,r) ;

cost_fom(i,v,rb,t)$[valcap(i,v,rb,t)$geo(i)] = geo_fom(i,rb) ;

cost_fom(i,initv,r,t)$[(not Sw_BinOM)$valcap(i,initv,r,t)] = sum{tt$tfirst(tt), cost_fom(i,initv,r,tt) } ;
cost_fom(i,v,r,t)$[valcap(i,v,r,t)$dupv(i)] = sum{ii$dupv_upv_corr(ii,i), cost_fom(ii,v,r,t) } ;

*====================
* --- Heat Rates ---
*====================

parameter heat_rate(i,v,r,t) "--MMBtu/MWh-- heat rate" ;

heat_rate(i,v,r,t)$valcap(i,v,r,t) = plant_char(i,t,'heatrate') ;

heat_rate(i,newv,r,t)$[valcap(i,newv,r,t)$countnc(i,newv)] =
      sum{tt$ict(i,newv,tt), plant_char(i,tt,'heatrate') } / countnc(i,newv) ;

heat_rate(i,v,r,t)$[CONV(i) and initv(v) and capacity_exog(i,v,r,"sk",t) and rb(r)] = data_heat_rate_init(r,i) ;

* fill in heat rate for initial capacity that does not have a binned heatrate
heat_rate(i,initv,r,t)$[valcap(i,initv,r,t)$(not heat_rate(i,initv,r,t))] =  plant_char(i,'2010','heatrate') ;

*note here conversion from btu/kwh to mmbtu/mwh
heat_rate(i,v,r,t)$[valcap(i,v,r,t)$sum{allt$att(allt,t), binned_heatrates(i,v,r,allt)}] =
                    sum{allt$att(allt,t), binned_heatrates(i,v,r,allt)} / 1000 ;

*part load heatrate adjust based on historical EIA generation and fuel use data
*this reflects the indescrepancy from the partial-loaded heat rate
*and the fully-loaded heat rate
parameter heat_rate_adj(i) "--unitless-- partial load heatrate adjuster based on historical EIA generation and fuel use data"
/
$offlisting
$ondelim
$include inputs_case%ds%heat_rate_adj.csv
$offdelim
$onlisting
/
;

heat_rate(i,v,r,t)$heat_rate_adj(i) = heat_rate_adj(i) * heat_rate(i,v,r,t) ;


*=========================================
* --- Fuel Prices ---
*=========================================

parameter fuel_price(i,r,t) "$/MMbtu - fuel prices by technology" ;


*written by input_processing\R\\fuelcostprep.R
table fprice(allt,r,f) "--2004$/MMBtu-- fuel prices by fuel type"
$offlisting
$ondelim
$include inputs_case%ds%fprice.csv
$offdelim
$onlisting
;

fuel_price(i,r,t)$sum{f$fuel2tech(f,i),1} = sum{(f,allt)$[fuel2tech(f,i)$(year(allt)=yeart(t))], fprice(allt,r,f)} ;

fuel_price(i,r,t)$[sum{f$fuel2tech(f,i),1}$(not fuel_price(i,r,t))] = sum{rr$fuel_price(i,rr,t),fuel_price(i,rr,t)} / max(1,sum{rr$fuel_price(i,rr,t),1}) ;

*==============================================
* --- Capacity Factors and Availability Rate---
*==============================================

parameter avail(i,v,h) "--fraction-- fraction of capacity available for generation by hour",
          cf_rsc(i,v,r,rs,h) "--fraction-- capacity factor for rsc tech - t index included for use in CC/curt calculations" ;

parameter forced_outage(i) "--fraction-- forced outage rate"
/
$offlisting
$ondelim
$include inputs_case%ds%forced_outage.csv
$offdelim
$onlisting
/ ;


parameter planned_outage(i) "--fraction-- planned outage rate"
/
$offlisting
$ondelim
$include inputs_case%ds%planned_outage.csv
$offdelim
$onlisting
/ ;


forced_outage(i)$hydro(i) = 0.05 ;
planned_outage(i)$hydro(i) = 0.019 ;
forced_outage(i)$geo(i) = forced_outage("geothermal") ;
planned_outage(i)$geo(i) = planned_outage("geothermal") ;


avail(i,v,h) = 1 ;

*(1-forced_outage(q)) * (1-planned_outage(q)$(not summerm(m))*365/273)
avail(i,v,h)$forced_outage(i) = (1-forced_outage(i))
                              * (1-planned_outage(i)$[not summerh(h)] * 365 / 273) ;

avail(i,initv,h)$geo(i) = 0.75 ;
avail(i,newv,h)$geo(i) = 0.85 ;


*begin capacity factor calculations

*created by /input_processing/R/cfgather.R
table cf_in(r,rs,i,h) "capacity factors for renewable technologies - wind CFs get adjusted below"
$offlisting
$ondelim
$include inputs_case%ds%cfout.csv
$offdelim
$onlisting
;


*initial assignment of capacity factors
cf_rsc(i,v,r,rs,h)$[cf_in(r,rs,i,h)$r_rs(r,rs)$cf_tech(i)$r_rs(r,rs)] = cf_in(r,rs,i,h) ;


*DUPV has same capacity factors as UPV but does not face the same distribution losses
*The DUPV capacity factors have already been adjusted by distloss
*Once the raw CFs are included, then we'll need to put distloss back in (commented line)
*cf_rsc(i,v,r,rs,h)$dupv(i) = su}(ii$dupv_upv_corr(ii,i), distloss * cf_rsc(ii,v,r,rs,h))
cf_rsc(i,v,r,rs,h)$[dupv(i)$r_rs(r,rs)] = sum{ii$dupv_upv_corr(ii,i), cf_rsc(ii,v,r,rs,h) } ;

*created by /inputs/capacitydata/writecapdat.R
parameter cf_hyd(i,szn,r) "unadjusted hydro capacity factors by season - same as hydcfsn from heritage"
/
$offlisting
$include inputs_case%ds%hydcf.txt
$onlisting
/ ;

*created by /inputs/capacitydata/writecapdat.R
parameter cf_hyd_szn_adj(i,szn,r) "seasonal adjustment for capacity factors - same as seacapadj_hy from heritage"
/
$offlisting
$include inputs_case%ds%hydcfadj.txt
$onlisting
/ ;

*created by /inputs/capacitydata/writecapdat.R
parameter cfhist_hyd(r,t,szn,i) "seasonal adjustment for capacity factors - same as hydhistcfadj from heritage"
/
$offlisting
$include inputs_case%ds%hydcfhist.txt
$onlisting
/ ;

* only need to compute this for rs==sk... otherwise gets yuge
* subtle difference here that hydro_d is assigned cf_hyd_szn_adj to its cf_rsc whereas hydro_nd is assigned cf_hyd
* dispatchable hydro has a separate constraint for seasonal generation which uses cf_hyd
cf_rsc(i,v,r,"sk",h)$hydro_d(i)  = sum{szn$h_szn(h,szn),cf_hyd_szn_adj(i,szn,r)} ;
cf_rsc(i,v,r,"sk",h)$hydro_nd(i) = sum{szn$h_szn(h,szn),cf_hyd(i,szn,r)} ;


table windcfin(t,i) "wind capacity factors by class"
$offlisting
$ondelim
$include inputs_case%ds%windcfout.csv
$offdelim
$onlisting
;

windcfin(t,i)$oddyears(t) = (windcfin(t-1,i) + windcfin(t+1,i)) / 2 ;

parameter cf_adj_t(i,v,t) "capacity factor adjustment over time for RSC technologies",
          cf_adj_hyd(r,i,h,t) "capacity factor adjustment over time for hydro technologies" ;

cf_adj_t(i,v,t)$[rsc_i(i) or hydro(i) or csp_nostorage(i)] = 1 ;
*matching assumption from heritage reeds
cf_adj_t(i,initv,t)$wind(i) = 0.3 ;
cf_adj_t(i,newv,t)$[windcfin(t,i)$countnc(i,newv)] = sum{tt$ict(i,newv,tt),windcfin(tt,i)} / countnc(i,newv) ;


*if not set, set it to one
cfhist_hyd(r,t,szn,i)$[(not cfhist_hyd(r,t,szn,i))$hydro(i)] = 1 ;
*odd, historical years are the average of the surrounding even years
cfhist_hyd(r,t,szn,i)$[oddyears(t)$(yeart(t)<=2015)] = (cfhist_hyd(r,t-1,szn,i) + cfhist_hyd(r,t+1,szn,i)) / 2 ;
*adjustment is the corresponding seasonal historical value
cf_adj_hyd(r,i,h,t)$hydro(i) = sum{szn$h_szn(h,szn),cfhist_hyd(r,t,szn,i)} ;

cf_rsc(i,v,r,rs,h)$[r_rs(r,rs)$rsc_i(i)$(sum{t,capacity_exog(i,v,r,rs,t)})] =
        cf_rsc(i,"init-1",r,rs,h) ;

* Capacity factors for CSP-ns are developed using typical DNI year (TDY) hourly resource data (Habte et al. 2014) from 18 representative sites.
* The TDY weather files are processed through the CSP modules of SAM to develop performance characteristics for a system with a solar multiple of 1.4.
* These representative sites have an average DNI range of 7.25-7.5 kWh/m2/day (see "Class 3" in Table 4 of the ReEDS Model Documnetation: Version 2016).
* Habte, A., A. Lopez, M. Sengupta, and S. Wilcox. 2014. Temporal and Spatial Comparison of Gridded TMY, TDY, and TGY Data Sets. Golden, CO: National Renewable Energy Laboratory. http://www.osti.gov/scitech/biblio/1126297.
parameter cf_cspns(h) "--unitless-- time-slice capacity factors for csp without storage"
/
$offlisting
$ondelim
$include inputs_case%ds%cf_cspns.csv
$offdelim
$onlisting
/
;

scalar avail_cspns "--unitless-- availability of csp without storage" /0.96/ ;

* Add data for CSP-ns to the capacity factor parameter
cf_rsc("csp-ns",v,r,rs,h)$(r_rs(r,rs)) = cf_cspns(h) * avail_cspns ;


*========================================
*      --- OPEARTING RESERVES ---
*========================================


set ortype               "types of operating reserve constraints" /flex, reg, spin/,
    orcat                "operating reserve category for RHS calculations" /or_load, or_wind, or_pv/,
    dayhours(h)          "daytime hours, used to limit PV capacity to the daytime hours" /h2*h4,h6*h8,h10*h12,h14*h16,h17/,
    hour_szn_group(h,hh) "h and hh in the same season - used in minloading constraint" ;

hour_szn_group(h,hh)$sum{szn$(h_szn(h,szn)$h_szn(hh,szn)),1} = yes ;

*reducing problem size by removing h-hh combos that are the same
hour_szn_group(h,hh)$sameas(h,hh) = no ;

Parameter
  ramptime(ortype) "minutes for ramping limit constraint in operating reserves" /flex 60, reg 5, spin 10/,
  reserve_frac(i,ortype) "fraction of a technology's online capacity that can contribute to a reserve type" ;

table orperc(ortype,orcat) "operating reserve percentage by type and category"
$offlisting
$ondelim
$include inputs_case%ds%orperc.csv
$offdelim
$onlisting
;

parameter ramprate(i) "--fraction/min-- ramp rate of dispatchable generators"
/
$offlisting
$ondelim
$include inputs_case%ds%ramprate.csv
$offdelim
$onlisting
/
;



*Only dispatchable hydro can provide operating reserves
ramprate(i)$hydro_d(i) = ramprate("hydro") ;
ramprate(i)$geo(i) = ramprate("geothermal") ;
ramprate(i)$coal(i) = 0.02 ;
ramprate(i)$CSP_Storage(i) = 0.1 ;

* Do not allow the reserve fraction to exceed 100%, so use the minimum of 1 or the computed value.
* The reserve fraction does NOT apply to storage technologies, but storage can provide operating reserves.
reserve_frac(i,ortype) = min(1,ramprate(i) * ramptime(ortype)) ;

parameter cost_opres(i) "--$ / MWh-- cost of reg operating reserves"
/
$offlisting
$ondelim
$include inputs_case%ds%cost_opres.csv
$offdelim
$onlisting
/
;

cost_opres(i)$geo(i) = cost_opres("geothermal") ;

*assuming cost for CSP-TES to provide regulation reserve is the same as o-g-s
cost_opres(i)$CSP_Storage(i) = cost_opres('o-g-s') ;

cost_opres(i) = cost_opres(i) * deflator("2013") ;

Scalar mingen_firstyear "first year for mingen considerations" /2020/ ;

parameter minloadfrac(r,i,h) "minimum loading fraction - final used in model",
          minloadfrac0(i) "initial minimum loading fraction"
/
$offlisting
$ondelim
$include inputs_case%ds%minloadfrac0.csv
$offdelim
$onlisting
/
;

minloadfrac0(i)$geo(i) = minloadfrac0("geothermal") ;

*written by input_processing/R/cfgather.R
table hydmin(i,r,szn) "minimum hydro loading factors by season and region"
$offlisting
$ondelim
$include inputs_case%ds%minhyd.csv
$offdelim
$onlisting
;

minloadfrac(r,i,h) = minloadfrac0(i) ;
minloadfrac(r,i,h)$CSP(i) = 0.15 ;
minloadfrac(r,i,h)$[coal(i)$(not minloadfrac(r,i,h))] = 0.5 ;
minloadfrac(r,i,h)$[sum{szn$h_szn(h,szn), hydmin(i,r,szn )}] = sum{szn$h_szn(h,szn), hydmin(i,r,szn) } ;

*=========================================
*              --- Load ---
*=========================================


parameter demchange(t)   "demand change in t relative to 2015",
          load_exog(r,h,t)    "--MW-- busbar load",
          load_exog0(r,h,t)   "original load by region hour and year - unchanged by demand side" ;

parameter peakdem_h17_ratio(r,szn,t) "recording of original ratio between peak demand and h17" ;

table load_2010(r,h) "--MW-- 2010 end-use load by time slice"
$offlisting
$ondelim
$include inputs_case%ds%load_2010.csv
$offdelim
$onlisting
;

table load_multiplier(cendiv,t) "--unitless-- relative load growth from 2010"
$offlisting
$ondelim
$include inputs_case%ds%load_multiplier.csv
$offdelim
$onlisting
;

scalar load_calibration "calibration adjustment to historical load to enable better matching of load_2010 to historical data" / 1.01 / ;

*Multiplying by distloss converts end-use load to busbar load
load_exog(r,h,t) = load_2010(r,h) * sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t) } * distloss * load_calibration ;


table canmexload(r,h) "load for canadian and mexican regions"
$offlisting
$ondelim
$include inputs_case%ds%canmexload.csv
$offdelim
$onlisting
;

table can_growth_rate(st,t) "growth rate for candadian demand"
$offlisting
$ondelim
$include inputs_case%ds%cangrowth.csv
$offdelim
$onlisting
;

parameter mex_growth_rate(t) "growth rate for mexican demand"
/
$offlisting
$ondelim
$include inputs_case%ds%mex_growth_rate.csv
$offdelim
$onlisting
/
;

load_exog(r,h,t)$sum{st$r_st(r,st),can_growth_rate(st,t)} =
      canmexload(r,h) * sum{st$r_st(r,st),can_growth_rate(st,t)} ;

load_exog(r,h,t)$r_country(r,"MEX") = mex_growth_rate(t) * canmexload(r,h) ;

*-- PHEV demand
* static demand is exogenously-imposed and added directly to load_exog
* whereas dynamic demand is flexible and based on seasonal amounts
* which can be shifted from one timeslice to another

parameter ev_static_demand(r,h,t) "--MWh-- static electricity load from EV charging by timeslice"
$offlisting
/
$ondelim
$include inputs_case%ds%ev_static_demand.csv
$offdelim
/
$onlisting
;

parameter ev_dynamic_demand(r,szn,t) "--MWh-- dynamic load from EV charging by season that is assigned by the model to timeslices"
$offlisting
/
$ondelim
$include inputs_case%ds%ev_dynamic_demand.csv
$offdelim
/
$onlisting
;

*static EV demand is added directly to load_exog
load_exog(r,h,t)$(Sw_EV) = load_exog(r,h,t) + ev_static_demand(r,h,t) ;

* load in odd years is the average between the two surrounding even years
load_exog(r,h,t)$[oddyears(t)$(not load_exog(r,h,t))] = (load_exog(r,h,t-1)+load_exog(r,h,t+1)) / 2 ;

*initial values are set here (after SwI_Load has been accounted for)
load_exog0(r,h,t) = load_exog(r,h,t) ;

parameter
maxload_szn(r,h,t,szn)   "maximum load by season - used to determine hour with highest load within each szn",
mload_exog_szn(r,t,szn)  "maximum load by season - placeholder for calculation hour_szn_group",
load_exog_szn(r,h,t,szn) "maximum load by season - placeholder for calculation hour_szn_group" ;



load_exog_szn(r,h,t,szn)$h_szn(h,szn) = load_exog(r,h,t) ;
mload_exog_szn(r,t,szn) = smax(hh$[not sameas(hh,"h17")],load_exog_szn(r,hh,t,szn)) ;
maxload_szn(r,h,t,szn)$[load_exog_szn(r,h,t,szn)=mload_exog_szn(r,t,szn)] = yes ;



*==============================
* --- Peak Load ---
*==============================

parameter peakdem(r,szn,t) "--MW-- bus bar peak demand by season" ;

*written by input_processing\R\\writeload.R
table peakdem_2010(r,szn) "--MW-- end use peak demand in 2010 by season"
$offlisting
$ondelim
$include inputs_case%ds%peak_2010.csv
$offdelim
$onlisting
;

*Multiplying by distloss converts end-use load to busbar load
peakdem(r,szn,t) = peakdem_2010(r,szn) * sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t) } * distloss * load_calibration ;

*==============================
* --- Planning Reserve Margin ---
*==============================

set h_szn_prm(h,szn) "hour to season linkage for nd_hydro in the planning reserve margin constraint"
/
h3.summ
h7.fall
h11.wint
h15.spri
/ ;

*written by input_processing\R\\writeload.R
table prm_nt(nercr_new,t) "--%-- planning reserve margin for NERC regions"
$offlisting
$ondelim
$include inputs_case%ds%prm_annual.csv
$offdelim
$onlisting
;

*odd years get the average off even years
prm_nt(nercr_new,t)$[oddyears(t)$(not prm_nt(nercr_new,t))] = (prm_nt(nercr_new,t-1) + prm_nt(nercr_new,t+1)) / 2 ;

parameter prm(r,t) "planning reserve margin by BA" ;

prm(r,t) = sum{nercr_new$r_nercr_new(r,nercr_new),prm_nt(nercr_new,t)} ;

* ===========================================================================
* Regional and temporal capital cost multipliers
* ===========================================================================
* Load scenario-specific capital cost multipliers
parameter cost_cap_fin_mult(i,r,t) "final capital cost multiplier for regions and technologies - used in the objective funciton"
/
$offlisting
$ondelim
$include inputs_case%ds%cap_cost_mult.csv
$offdelim
$onlisting
/ ;

parameter cost_cap_fin_mult_noITC(i,r,t) "final capital cost multiplier excluding ITC - used only in outputs"
/
$offlisting
$ondelim
$include inputs_case%ds%cap_cost_mult_noITC.csv
$offdelim
$onlisting
/ ;

parameter rsc_fin_mult(i,r,t) "capital cost multiplier for resource supply curve technologies that have their capital costs included in the supply curves" ;

* Start by setting all multipliers to 1
rsc_fin_mult(i,r,t) = 1 ;

*Hydro and geo both have capital costs included in the supply curve, so change their multiplier to be the same as cost_cap_fin_mult
rsc_fin_mult(i,r,t)$geo(i) = cost_cap_fin_mult('geothermal',r,t) ;
rsc_fin_mult(i,r,t)$hydro(i) = cost_cap_fin_mult('hydro',r,t) ;

* Apply cost reduction multipliers
rsc_fin_mult(i,r,t)$geo(i) = rsc_fin_mult(i,r,t) * sum{geotech$i_geotech(i,geotech), geocapmult(t,geotech) } ;
rsc_fin_mult(i,r,t)$hydro(i) = rsc_fin_mult(i,r,t) * hydrocapmult(t,i) ;


*=========================================
* --- Emission Rate ---
*=========================================

table emit_rate_fuel(i,e)  "--metric tons CO2 per MMBtu-- CO2 emission rate of fuel"
$offlisting
$ondelim
$include inputs_case%ds%emitrate.csv
$offdelim
$onlisting
;


parameter emit_rate(e,i,v,r,t) "--metric tons pollutant per MWh-- CO2 emissions rate" ;


* ===========================================================================
* Emissions Limit
* ===========================================================================

set emit_rate_con(e,r,t) "set to enable or disable emissions rate limits by emittant and region" ;

parameter emit_rate_limit(e,r,t)   "--metric tons pollutant per MWh-- CO2 emission rate limit",
          CarbonTax(t)             "--$/metric ton CO2-- carbon tax" ;

scalar CarbPolicyStartyear /2020/ ;

carbontax(t) = 0 ;

*setting to some huge number for now
emit_rate_limit(e,r,t) = 1e20 ;

*disabled by default
emit_rate_con(e,r,t) = no ;



*======================
* Growth limits
*======================

*growth limits are re-assigned in d_solveprep based on values in cases.csv

parameter growth_limit_relative(tg) "--unitless-- growth limit for technology groups relative to existing capacity",
          growth_limit_absolute(tg) "--MW-- growth limit for technology groups in absolute terms"
*absolute growth penalties based on greatest annual change of capacity for each tech group from 1990-2016
            /solar 16575, wind 26795,csp 16575/ ;

growth_limit_relative("solar") = 1 + Sw_SolarRelLim / 100 ;
growth_limit_relative("wind") = 1 + Sw_WindRelLim / 100 ;
growth_limit_relative("CSP") = 1 + Sw_CSPRelLim / 100 ;

*====================================
* --- CES Gas supply curve setup ---
*====================================

set gb "gas price bin must be an odd number of bins, e.g. gb1*gb11" /gb1*gb15/ ;
alias(gb,gbb) ;

scalar gassupplyscale "shifting of reference gas price bin - notes below" /-0.5/,
* gassupply scale determines how far the bins reference quantity should deviate from its reference price
* with gassupply scale = -0.5, the center of the reference price bin will be the reference quantity
* with gassupplyscale = 0, the end of the reference gas price's bin will the limit for that reference bin
*long run price elasticity as estimated by:
*https://www.diw.de/documents/publikationen/73/diw_01.c.441773.de/dp1372.pdf
       gas_elasticity "gas supply curve elasticity" /0.76/,
       gasscale "percentage change from reference for each gas bin" /0.02/ ;


*note that the supply curve is set up such that the edge of the bin pertaining to the reference
*price sits at its upper limit, we want to move the curve such that the reference price sits at the middle of the
*respective bin

parameter gasprice(cendiv,gb,t) "--$/MMBtu-- price of each gas bin",
          gasquant(cendiv,gb,t) "--MMBtu - natural gas quantity for each bin",
          gaslimit(cendiv,gb,t) "--MMBtu-- gas limit by gas bin"
          gassupply_ele(cendiv,t) "--MMBtu-- reference gas consumption by the ELE sector"
          gassupply_tot(cendiv,t) "--MMBtu-- reference gas consumption by the ELE sector" ;

table gasprice_ref(cendiv,t) "--2004$/MMBtu-- natural gas price by census division"
$offlisting
$ondelim
$include inputs_case%ds%ng_price_cendiv.csv
$offdelim
$onlisting
;

table gasquant_elec(cendiv,t) "--Quads-- Natural gas consumption in the electricity sector"
$offlisting
$ondelim
$include inputs_case%ds%ng_demand_elec.csv
$offdelim
$onlisting
;

table gasquant_tot(cendiv,t) "--Quads-- Total natural gas consumption"
$offlisting
$ondelim
$include inputs_case%ds%ng_demand_tot.csv
$offdelim
$onlisting
;

*need to convert from quadrillion btu to million btu
gassupply_ele(cendiv,t) = 1e9 * gasquant_elec(cendiv,t) ;
gassupply_tot(cendiv,t) = 1e9 * gasquant_tot(cendiv,t) ;


scalar gas_scale "conversion factor for gas-related parameters to help in scaling the problem" /1e6/;

parameter
gassupply_ele_nat(t)    "--quads-- national reference gas supply for electricity " ,
gasprice_nat(t)         "--$/MMbtu-- national NG price",
gasquant_nat(t)         "--quads-- national NG usage",
gasquant_nat_bin(gb,t)  "--quads-- national NG quantity by bin",
gasprice_nat_bin(gb,t)  "--$/MMbtu-- price for each national NG bin",
gasadder_cd(cendiv,t,h) "--$/MMbtu-- adder for NG census divsion, unused",
gaslimit_nat(gb,t)      "--MMbtu-- national gas bin limit" ;

gassupply_ele_nat(t) = sum{cendiv$gassupply_ele(cendiv,t),gassupply_ele(cendiv,t)} ;

gasprice_nat(t) = sum{cendiv$gassupply_ele(cendiv,t),gassupply_ele(cendiv,t) * gasprice_ref(cendiv,t)}
                              / gassupply_ele_nat(t) ;


gasadder_cd(cendiv,t,h) = (gasprice_ref(cendiv,t) - gasprice_nat(t))/2 ;

*winter gas gets marked up
gasadder_cd(cendiv,t,h)$h_szn(h,"wint") = .04 * gasprice_ref(cendiv,t) + gasadder_cd(cendiv,t,h) ;

*now compute the amounts going into each gas bin
*this is computed as the amount relative to the
*reference amount based on the ordinal of the
*gas bin - e.g. gas bin 4 (with a central gas bin of 6 and bin width of 0.1)
*will be gassupply_ele * (1+4-6*0.1) = 0.8 * reference
gasquant(cendiv,gb,t)$gassupply_ele(cendiv,t) = gassupply_ele(cendiv,t) *
                          (1+(ord(gb)-(smax(gbb,ord(gbb))/2 + 0.5))*0.1) ;


gasquant_nat_bin(gb,t)$gassupply_ele_nat(t) = gassupply_ele_nat(t) *
                          (1+(ord(gb)-(smax(gbb,ord(gbb))/2 + 0.5))*0.1) ;


gasprice(cendiv,gb,t)$gassupply_ele(cendiv,t) =
          gas_scale * round(gasprice_ref(cendiv,t) *
               (
* numerator is the quantity in the bin
* [plus] all natural gas usage
* [minus] gas usage in the ele sector
                (gasquant(cendiv,gb,t)+gassupply_tot(cendiv,t) - gassupply_ele(cendiv,t))
                /(gassupply_tot(cendiv,t))
                ) ** (1/gas_elasticity),4) ;


gasprice_nat_bin(gb,t)$sum{cendiv,gassupply_tot(cendiv,t)} =
          gas_scale * round(gasprice_nat(t) *
               (
                (gasquant_nat_bin(gb,t) + sum{cendiv,gassupply_tot(cendiv,t)} - gassupply_ele_nat(t))
                /(sum{cendiv,gassupply_tot(cendiv,t)})
                ) ** (1/gas_elasticity),4) ;


*the quantity available in each bin is the quantity on the supply curve minus the previous bin's quantity supplied
gaslimit(cendiv,gb,t) = round((gasquant(cendiv,gb,t) - gasquant(cendiv,gb-1,t)),0) / gas_scale;


gaslimit(cendiv,"gb1",t) = gaslimit(cendiv,"gb1",t)
                            - gassupplyscale * sum{gb$[ord(gb)=(smax(gbb,ord(gbb)) / 2 + 0.5)],gaslimit(cendiv,gb,t)} ;

*final category gets a huge bonus so we make sure we do not run out of gas
gaslimit(cendiv,gb,t)$[ord(gb)=smax(gbb,ord(gbb))] = 5 * gaslimit(cendiv,gb,t) ;


gaslimit_nat(gb,t) = round((gasquant_nat_bin(gb,t) - gasquant_nat_bin(gb-1,t)),0) / gas_scale;

gaslimit_nat("gb1",t) = gaslimit_nat("gb1",t)
                            - gassupplyscale * sum{gb$[ord(gb)=(smax(gbb,ord(gbb)) / 2 + 0.5)],gaslimit_nat(gb,t)} ;

*final category gets a huge bonus so we make sure we do not run out of gas
gaslimit_nat(gb,t)$(ord(gb)=smax(gbb,ord(gbb))) = 5 * gaslimit_nat(gb,t) ;



*===========================================
* --- Regional Gas supply curve ---
*===========================================

set fuelbin  "gas usage bracket"   /fb1*fb20/ ;
alias(fuelbin,afuelbin) ;

Scalar numfuelbins       "number of fuel bins",
       normfuelbinmin    "bottom cutoff for natural gas supply curve" /0.6/,
       normfuelbinmax    "top cutoff for natural gas supply curve" /1.4/,
       normfuelbinwidth  "typical fuel bin width",
       botfuelbinwidth   "bottom fuel bin width",
       topfuelbinwidth   "top fuel bin width" /2/
;

parameter cd_beta(cendiv,t)                      "--$/MMBtu per Quad-- beta value for census divisions' natural gas supply curves",
          szn_adj_gas(h)                         "--unitless-- seasonal adjustment for gas prices",
          nat_beta(t)                            "--$/MMBtu per Quad-- beta value for national natural gas supply curves",
          gasbinwidth_regional(fuelbin,cendiv,t) "--MMBtu-- census division's gas bin width",
          Gasbinwidth_national(fuelbin,t)        "--MMBtu-- national gas bin width",
          Gasbinp_regional(fuelbin,cendiv,t)     "--$/MMBtu-- price for each gas bin",
          gasusage_national(t)                   "--MMBtu-- reference national gas usage",
          Gasbinqq_regional(fuelbin,cendiv,t)    "--MMBtu-- regional reference level for supply curve calculation of each gas bin",
          Gasbinqq_national(fuelbin,t)           "--MMBtu-- national reference level for supply curve calculation of each gas bin",
          Gasbinp_national(fuelbin,t)            "--$/MMBtu--price for each national gas bin",
          gasmultterm(cendiv,t)                  "parameter to be multiplied by total gas usage to compute the reference costs of gas consumption, from which the bins deviate" ;

*note these do not change over years
*only exception is that the value in the first year is
*set to zero
parameter cd_beta0(cendiv) "--$/MMBtu per Quad-- reference census division beta levels"
/
$offlisting
$ondelim
$include inputs_case%ds%cd_beta0.csv
$offdelim
$onlisting
/
;

*beginning year value is zero (i.e., no elasticity)
cd_beta(cendiv,t)$[not tfirst(t)] = cd_beta0(cendiv) ;

*see documentation for how value is calculated
nat_beta(t)$(not tfirst(t)) = 0.1352 ;


*written by input_processing\R\\fuelcostprep.R
table cd_alpha(t,cendiv) "--$/MMBtu-- alpha value for natural gas supply curves"
$offlisting
$ondelim
$include inputs_case%ds%alpha.csv
$offdelim
$onlisting
;

table cendiv_weights(r,cendiv) "--unitless-- weights to smooth gas prices between census regions to avoid abrupt price changes at the cendiv borders"
$offlisting
$ondelim
$include inputs_case%ds%cendivweights.csv
$offdelim
$onlisting
;


szn_adj_gas(h) = 1 ;

*1.054 is calculated based on natural gas futures prices -- see documentation
szn_adj_gas(h)$h_szn(h,"wint") = 1.054 ;

*number of fuel bins is just the sum of fuel bins
numfuelbins = sum{fuelbin, 1} ;

*note we subtract two here because top and bottom bins are not included
normfuelbinwidth = (normfuelbinmax - normfuelbinmin)/(numfuelbins - 2) ;

*set the bottom fuel bin width
botfuelbinwidth = normfuelbinmin;

*national gas usage computed as sum over census divisions' gas usage
gasusage_national(t) = sum{cendiv,gassupply_ele(cendiv,t)} ;


*gas bin width is typically the reference gas usage times the bin width
Gasbinwidth_regional(fuelbin,cendiv,t) = gassupply_ele(cendiv,t) * normfuelbinwidth;

*bottom and top bins get special treatment
*in that they are expanded by botfuelbinwidth and topfuelbinwidth
Gasbinwidth_regional(fuelbin,cendiv,t)$[ord(fuelbin) = 1] = gassupply_ele(cendiv,t) * botfuelbinwidth;
Gasbinwidth_regional(fuelbin,cendiv,t)$[ord(fuelbin) = smax(afuelbin,ord(afuelbin))] =
                                          gassupply_ele(cendiv,t) * topfuelbinwidth ;

*don't want any super small or zero values -- this follows the same calculations in heritage ReEDS
Gasbinwidth_regional(fuelbin,cendiv,t)$[Gasbinwidth_regional(fuelbin,cendiv,t) < 10] = 10 ;

*gas bin widths are defined simiarly on the national level
Gasbinwidth_national(fuelbin,t) = Gasusage_national(t) * normfuelbinwidth ;
Gasbinwidth_national(fuelbin,t)$[ord(fuelbin) = 1]   = Gasusage_national(t) * botfuelbinwidth ;
Gasbinwidth_national(fuelbin,t)$[ord(fuelbin)=smax(afuelbin,ord(afuelbin))]  = Gasusage_national(t) * topfuelbinwidth ;

*comment from heritage reeds:
*gasbinqq is the centerpoint of each of the smaller bins and is used to determine the price of each bin. The first and last bin have
*gasbinqqs that are just one more step before and after the smaller bins.
Gasbinqq_regional(fuelbin,cendiv,t) =
   gassupply_ele(cendiv,t)  * (normfuelbinmin
    + (ord(fuelbin) - 1)*normfuelbinwidth - normfuelbinwidth / 2) ;

Gasbinqq_national(fuelbin,t) =  Gasusage_national(t)  * (normfuelbinmin + (ord(fuelbin) - 1)*normfuelbinwidth - normfuelbinwidth / 2) ;


*bins' prices are those from the supply curves
*1e9 converts from MMBtu to Quads
Gasbinp_regional(fuelbin,cendiv,t) =
   round((cd_beta(cendiv,t) * (Gasbinqq_regional(fuelbin,cendiv,t) -  gassupply_ele(cendiv,t))) / 1e9,5) ;

Gasbinp_national(fuelbin,t)= round(nat_beta(t)*(Gasbinqq_national(fuelbin,t) - gasusage_national(t)) / 1e9,5) ;


*this is the reference price of gas given last year's gas usage levels
gasmultterm(cendiv,t) = (cd_alpha(t,cendiv)
                     + nat_beta(t) * gasusage_national(t-2) / 1e9
                     + cd_beta(cendiv,t) * gassupply_ele(cendiv,t-2) / 1e9
                        ) ;


*=================================
*       ---- Storage ----
*=================================

parameter numdays(szn) "--number of days-- number of days for each season" ;
numdays(szn) = sum{h$h_szn(h,szn),hours(h)} / 24 ;

parameter hours_daily(h) "--number of hours-- number of hours represented by time-slice 'h' during one day" ;
hours_daily(h) = hours(h) / sum{szn$h_szn(h,szn), numdays(szn)} ;

set store_h_hh(h,hh) "storage correlation across hours"
/
   (h1*h4,h17).(h1*h4,h17),
   (h5*h8).(h5*h8),
   (h9*h12).(h9*h12),
   (h13*h16).(h13*h16)
/ ;

store_h_hh(h,hh)$sameas(h,hh) = no ;

parameter storage_eff(i,t) "--fraction-- efficiency of storage technologies" ;

storage_eff(i,t)$storage(i) = 1 ;
storage_eff("pumped-hydro",t) = 0.8 ;
storage_eff("ICE",t) = 1 ;
storage_eff(i,t)$[storage(i)$plant_char(i,t,'rte')] = plant_char(i,t,'rte') ;

parameter storage_lifetime_cost_adjust(i) "--unitless-- cost adjustment for battery storage technologies because they do not have a 20-year life" ;

*The 1.21 value is the CRF_15 divided by CRF_20 to account for batteries only having a 15-year lifetime.
*It technically should change over time (if CRF changes over time), but is represented as a constant value here for simplicity
storage_lifetime_cost_adjust(i)$battery(i) = 1.21 ;

cost_cap(i,t)$storage_lifetime_cost_adjust(i) = cost_cap(i,t) * storage_lifetime_cost_adjust(i) ;

* Parameters for CSP-ws configurations: used in eq_rsc_INVlim
* csp: this include the SM for representative configurations, divided by the representative SM (2.4) for CSP supply curve;
* all other technologies are 1
parameter
  csp_sm(i) "solar multiple for configurations"
  resourcescaler(i) "resource scaler for rsc technologies"
;

csp_sm(i)$csp1(i) = 2.7 ;
csp_sm(i)$csp2(i) = 2.4 ;
csp_sm('csp-ns') = 1.4 ;

resourcescaler(i)$[not CSP_Storage(i)] = 1 ;
resourcescaler(i)$csp(i) = CSP_SM(i) / 2.4 ;

parameter storage_duration(i) "hours of storage duration" ;

storage_duration(i)$battery(i) = 4 ;
storage_duration(i)$csp1(i) = 14 ;
storage_duration(i)$csp2(i) = 10 ;
storage_duration('CAES') = 12 ;
storage_duration('pumped-hydro') = 12 ;

parameter minCF(i,t) "--unitless-- minimum annual capacity factor"
          maxCF(i,t) "--unitless-- maximum seasonal capacity factor " ;

* set the minimum capacity factor for gas-CTs
minCF('gas-ct',t) = 0.04 ;

* set maxCF for batteries to one cycle per day
maxCF(i,t)$battery(i) = storage_duration(i) / 24 ;

*fom costs are constant for pumped-hydro
cost_fom("pumped-hydro",v,r,t) = 13030 ;


parameter ice_fom(t) "--$/MW-year -- Fixed O&M costs for ice storage"
/
$offlisting
$ondelim
$include inputs_case%ds%ice_fom.csv
$offdelim
$onlisting
/
;


cost_fom("ICE",v,rb,t)$valcap("ICE",v,rb,t) = ice_fom(t) ;

scalar bio_cofire_perc "--fraction-- fraction of total fuel that is biomass used in cofire plants" /0.15/ ;

scalar emit_scale "scaling factor for emissions" /1e6/;

emit_rate(e,i,v,r,t)$[emit_rate_fuel(i,e)$valcap(i,v,r,t)$rb(r)]
  = round(heat_rate(i,v,r,t) * emit_rate_fuel(i,e),6) ;

*only emissions from the coal portion of cofire plants are considered
emit_rate(e,i,v,r,t)$[sameas(i,"cofire")$emit_rate_fuel("coal-new",e)$valcap(i,v,r,t)$rb(r)]
  = round((1-bio_cofire_perc) * heat_rate(i,v,r,t) * emit_rate_fuel("coal-new",e),6) ;


*==============================
* --- BIOMASS SUPPLY CURVES ---
*==============================

set bioclass /bioclass1*bioclass5/,
    biofeas(r) "regions with biomass supply and biopower" ;

parameter biopricemult(r,bioclass,t) "biomass price multiplier" ;

*created by inputs\\supplycurvedata\\combinedat.R
table biosupply(r,*,bioclass) "biomass supply (MMBtu) and biomass cost ($/MMBtu)"
$offlisting
$ondelim
$include inputs_case%ds%bio_supplycurve.csv
$offdelim
$onlisting
;

* biosupply capacity is coming in as GBtu, so multiply by 1000 to get to MMBtu
biosupply(r,"cap",bioclass) = biosupply(r,"cap",bioclass) * 1000 ;


table biopriceramp(r,bioclass) "bio price ramping factor, by year"
$offlisting
$ondelim
$include inputs_case%ds%bio_priceramp.csv
$offdelim
$onlisting
;

$ontext
* 02-04-2010 PTS revert bio fuel price back to using biopriceramp (annual increase by PCA)
* PTS 04-24-09
* 02-28-2013 DJM Updated to include bioclass as dimension of BioPriceRamp
* 04-02-2013 DJM Added dollar control to prevent extrapolation of billion ton update data past 2020 and uses same values for 2010 and 2012 without ramp added
BioFeedstockPrice(bioclass,n)$(cur_year <=2030 and cur_year > 2012) =
      BiofeedstockPrice(bioclass,n)*(BioPriceRamp(bioclass,n)**2) ;
$offtext

biopricemult(r,bioclass,t)$[yeart(t)<=2013] = 1 ;

loop(tt$[(not oddyears(tt))$(yeart(tt)>=2014)$(yeart(tt)<=2030)],
    biopricemult(r,bioclass,tt) = biopricemult(r,bioclass,tt-2) * (biopriceramp(r,bioclass)**2) ;
  ) ;

biopricemult(r,bioclass,t)$oddyears(t) = (biopricemult(r,bioclass,t-1) + biopricemult(r,bioclass,t+1)) / 2 ;

biopricemult(r,bioclass,t)$[yeart(t)>=2030] = biopricemult(r,bioclass,"2030") ;

biofeas(r)$sum{bioclass, biosupply(r,"cost",bioclass) } = yes ;

*removal of bio techs that are not in biofeas(r)
valcap(i,v,r,t)$[(cofire(i) or sameas(i,"biopower"))$(not biofeas(r))] = no ;
valgen(i,v,r,t)$[(cofire(i) or sameas(i,"biopower"))$(not biofeas(r))] = no ;



*================================
* Capacity value and curtailment
*================================

parameters curt_int(i,r,h,t)       "--fraction-- average curtailment rate of all resources in a given year - only used in intertemporal solve",
           curt_excess(r,h,t)      "--MW-- excess curtailment when assuming marginal curtailment in intertemporal solve",
           curt_old(r,h,t)         "--fraction-- average curtailment rate of resources already existing in a given year - only used in sequential solve",
           curt_marg(i,r,h,t)      "--fraction-- marginal curtail rate for new resources - only used in sequential solve",
           cc_old(i,r,szn,t)       "--MW-- capacity credit for existing capacity - used in sequential solve similar to heritage reeds",
           cc_old_load(i,r,szn,t)  "--MW-- cc_old loading in from the cc_out gdx file",
           cc_mar(i,r,rs,szn,t)    "--fraction--  cc_mar loading inititalized to some reasonable value for the 2010 solve",
           cc_mar_load(i,r,szn,t)  "--fraction--  cc_mar loading in from the cc_out gdx file",
           cc_int(i,v,r,szn,t)     "--fraction--  average fractional capacity credit - used in intertemporal solve",
           cc_excess(i,r,szn,t)    "--MW-- this is the excess capacity credit when assuming marginal capacity credit in intertemporal solve",
           cc_eqcf(i,v,r,rs,t)     "--fraction--  fractional capacity credit based off average capacity factors - used without iteration with cc and curt scripts",
           curt_mingen(r,h,t)      "--fraction--  fraction of addition curtailment induced by increasing the minimum generation level (sequential only)",
           curt_mingen_int(r,h,t)  "--fraction--  fractional curtailment of mingen (intertemporal only)",
           curt_mingen_load(r,h,t) "--fraction--  fraction of addition curtailment induced by increasing the minimum generation level, loaded from gdx file (so as to not overwrite existing values for non-modeled years)",
           curt_storage(i,r,h,t)   "--fraction--  fraction of curtailed energy that can be recovered by storage charging during that timeslice"
           surpold(r,h,t)          "--MW-- surplus from old capacity - used to calculate average curtailment for VRE techs" ;



cc_old(i,r,szn,t) = 0 ;

cc_eqcf(i,v,r,rs,t)$[r_rs(r,rs)$vre(i)$(sum{rscbin, rscfeas(r,rs,i,rscbin) })] =
  cf_adj_t(i,v,t) * sum{h,hours(h) * cf_rsc(i,v,r,rs,h)} / sum{h,hours(h)} ;

*initialize cc_mar at some reasonable value
cc_mar(i,r,rs,szn,t)$r_rs(r,rs) = sum{v$ict(i,v,t),cc_eqcf(i,v,r,rs,t)} ;

*initialize cc_int at some reasonable value
cc_int(i,v,r,szn,t)$[(vre(i) or storage(i))$valcap(i,v,r,t)$sum{rs$cc_mar(i,r,rs,szn,t), 1 }] =
    sum{rs$r_rs(r,rs), cc_mar(i,r,rs,szn,t) } / sum{rs$cc_mar(i,r,rs,szn,t), 1 } ;

cc_excess(i,r,szn,t) = 0 ;

*initialize curtailments at zero
curt_int(i,r,h,t) = 0 ;
curt_excess(r,h,t) = 0 ;
curt_old(r,h,t) = 0 ;
curt_marg(i,r,h,t) = 0 ;
curt_mingen(r,h,t) = 0 ;
curt_mingen_int(r,h,t) = 0 ;
curt_storage(i,r,h,t)$[storage(i)$valcap_irt(i,r,t)] = Sw_CurtStorage ;

parameter cf_modeled(i,v,r,rs,h,t) "final value of capacity factor used in the model" ;

* only wind has existing capacity and it is all in the same class
* this is because pv/csp all are forced to be built in the first period

cf_modeled(i,v,r,rs,h,t)$[r_rs(r,rs)$cf_tech(i)$(valcap(i,v,r,t) or valcap(i,v,rs,t))] =
* note here that the CAP_FO_PO_HYD in heritage reeds treated seacapadj_hy as the capacity factor for
* dispatchable hydro and hydcfsn (which is adjusted by the historical factor)
* is used in Hyd_New_Dispatch_Gen and Hyd_Old_Dispatch_Gen
         (1$[not hydro_nd(i)] + cf_adj_hyd(r,i,h,t)$hydro_nd(i))
         * cf_rsc(i,v,r,rs,h)
         * cf_adj_t(i,v,t)
         * avail(i,v,h)
;

parameter emit_cap(e,t)   "--metric tons-- emissions cap, by default a large value and changed in d_solveprep",
          yearweight(t)   "--unitless-- weights applied to each solve year for the banking and borrowing cap - updated in d_solveprep.gms",
          emit_tax(e,r,t) "--$/ metric ton-- Tax applied to emissions" ;

emit_cap(e,t) = 1e15 ;
emit_tax(e,r,t) = 0 ;

yearweight(t) = 0 ;
yearweight(t)$tmodel_new(t) = sum{tt$tprev(tt,t), yeart(tt) } - yeart(t) ;
yearweight(t)$tlast(t) = 1 + smax{yearafter, yearafter.val } ;

parameter co2_cap(t)      "--metric tons-- co2 emissions cap used when Sw_AnnualCap is on"
/
$ondelim
$include inputs_case%ds%co2_cap.csv
$offdelim
/
;

parameter co2_tax(t)      "--$/metric ton CO2-- co2 tax used when Sw_CarbTax is on"
/
$ondelim
$include inputs_case%ds%co2_tax.csv
$offdelim
/
;


* set the carbon tax based on switch arguments
if(Sw_CarbTax = 1,
emit_tax("CO2",r,t) = co2_tax(t) ;
) ;

*=========================================
* BEGIN RS REMOVAL
*=========================================

set capr(r) "regions that can have capacity",
    genr(r) "regions that can provide generation"
;


capr(r)$[(rb(r) or rs(r))$(not sameas(r,"sk"))] = yes ;
genr(r)$rb(r) = yes ;


parameter
m_avail_retire_exog_rsc(i,v,r,t) "--MW-- exogenous amoung of available retirements",
m_rsc_dat(r,i,rscbin,sc_cat)     "--MW or $/MW-- resource supply curve attributes",
m_cc_mar(i,r,szn,t)              "--fraction-- marginal capacity credit",
m_cf(i,v,r,h,t)                  "--fraction-- modeled capacity factor",
m_cf_szn(i,v,r,szn,t)            "--fraction-- modeled capacity factor, averaged by season" ;

  m_avail_retire_exog_rsc(i,v,rb,t) = avail_retire_exog_rsc(i,v,rb,"sk",t) ;
  m_avail_retire_exog_rsc(i,v,rs,t)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs),avail_retire_exog_rsc(i,v,r,rs,t)} ;

  m_rsc_dat(rb,i,rscbin,"cap") = rsc_dat(rb,"sk",i,rscbin,"cap") ;
  m_rsc_dat(rs,i,rscbin,"cap")$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs),rsc_dat(r,rs,i,rscbin,"cap")} ;

rsc_dat(r,rs,i,rscbin,"cost")$[hydro(i)$rsc_dat(r,rs,i,rscbin,"cost")] = rsc_dat(r,rs,i,rscbin,"cost") * 1000 ;

  m_rsc_dat(rb,i,rscbin,"cost") = rsc_dat(rb,"sk",i,rscbin,"cost") ;
  m_rsc_dat(rs,i,rscbin,"cost")$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs),rsc_dat(r,rs,i,rscbin,"cost")} ;

* prescribed hydund in p33 does not have enough rsc_dat
* capacity to meet prescribed amount - check with WC
  m_rsc_dat("p18","hydUND","bin1","cap")   = m_rsc_dat("p18","hydUND","bin1","cap") + 27 ;
  m_rsc_dat("p18","hydNPND","bin1","cap")  = m_rsc_dat("p18","hydNPND","bin1","cap") + 3 ;
  m_rsc_dat("p110","hydNPND","bin1","cap") = m_rsc_dat("p110","hydNPND","bin1","cap") + 58 ;
  m_rsc_dat("p33","hydUND","bin1","cap")   = 5 ;

* rounding resource supply curve numbers to 4 decimal places
  m_rsc_dat(r,i,rscbin,"cap") = round(m_rsc_dat(r,i,rscbin,"cap"),4) ;
  m_rscfeas(r,i,rscbin) = no ;
  m_rscfeas(r,i,rscbin)$m_rsc_dat(r,i,rscbin,"cap") = yes ;
  m_rscfeas(r,i,rscbin)$[sum{ii$tg_rsc_cspagg(ii, i),m_rscfeas(r,ii,rscbin)}] = yes ;
  m_rscfeas("sk",i,rscbin) = no ;


  m_cc_mar(i,rb,szn,t) = cc_mar(i,rb,"sk",szn,t) ;
  m_cc_mar(i,rs,szn,t)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs), cc_mar(i,r,rs,szn,t) } ;

  m_cf(i,v,rb,h,t)$(cf_tech(i)$valcap(i,v,rb,t)) = cf_modeled(i,v,rb,"sk",h,t) ;

  m_cf(i,v,rs,h,t)$[(not sameas(rs,"sk"))$cf_tech(i)$valcap(i,v,rs,t)] = 
            sum{r$r_rs(r,rs), cf_modeled(i,v,r,rs,h,t) } ;

  m_cf(i,newv,r,h,t)$[not sum{tt$(yeart(tt) <= yeart(t)), ict(i,newv,tt )}$valcap(i,newv,r,t)] = 0 ;
  m_cf("distpv",v,r,h,t)$valcap("distpv",v,r,t) = m_cf("distpv",v,r,h,t) * distloss;
  m_cf_szn(i,v,r,szn,t)$valcap(i,v,r,t) = sum{h$h_szn(h,szn), hours(h) * m_cf(i,v,r,h,t) } / sum{h$h_szn(h,szn), hours(h) } ;



*can trim down these matrices fairly significantly...
peakdem_h17_ratio(r,szn,t)$load_exog(r,"h17",t) = peakdem(r,szn,t) / load_exog(r,"h17",t) ;


parameter degrade(i,t,tt) "degradation factor for pv techs" ;
scalar pv_degrade_rate "annual degradation amount for pv techs" /0.005/ ;
degrade(i,t,tt)$[(yeart(tt)>=yeart(t))] = 1 ;
degrade(i,t,tt)$[pv(i)$(yeart(tt)>=yeart(t))] = (1-pv_degrade_rate)**(yeart(tt)-yeart(t)) ;



set force_pcat(pcat,t) "conditional to indicate whether the force prescription equation should be active for pcat" ;

force_pcat(pcat,t)$[
* it is before the first year
                    (yeart(t)<=2022)
* it is the sameas wind and there are near term cap limits
                      or (sameas(pcat,"wind-ons") and sum{(rr,tt)$(yeart(tt)<=yeart(t)), near_term_cap_limits("wind",rr,t) })
* it is gas-ct (with a first year of 2010) and there are required prescriptions
                      or (sameas(pcat,"gas-ct") and sum{(rr,tt)$(yeart(tt)<=yeart(t)), m_required_prescriptions("gas-ct",rr,t) })
*it is offshore wind and there are required prescriptions
                      or (sameas(pcat,"wind-ofs") and
                            sum{(tt,rr)$(yeart(tt)<yeart(t)), m_required_prescriptions("wind-ofs",rr,tt) })
                   ] = yes ;

force_pcat(pcat,t)$[(yeart(t)>2022) and ((not sameas(pcat,"wind-ofs")) and (not sameas(pcat,"wind-ofs")))] = no ;

*removals from force_pcat
force_pcat("distpv",t) = no ;
force_pcat("hydro",t) = no ;
force_pcat("geothermal",t) = no ;

force_pcat(pcat,t)$[sum{(ppcat,ii)$sameas(pcat,ii) ,prescriptivelink0(ppcat,ii) }] = no ;


parameter rsc_reduct_frac(pcat,r) "--unitless-- fraction of renewable resource that is reduced from the supply curve"
          prescrip_rsc_frac(pcat,r) "--unitless-- fraction of prescribed builds to the resource available"
;

rsc_reduct_frac(pcat,r) = 0 ;
prescrip_rsc_frac(pcat,r) = 0 ;

* if the Sw_ReducedResource is on, reduce the available resource by 25%
if (Sw_ReducedResource = 1,
*Calculate the fraction of prescribed builds to the available resource
  prescrip_rsc_frac(pcat,r)$[sum{(rs,i,rscbin)$prescriptivelink(pcat,i), rsc_dat(r,rs,i,rscbin,"cap") } > 0] =
      smax(t,m_required_prescriptions(pcat,r,t)) / sum{(rs,i,rscbin)$prescriptivelink(pcat,i), rsc_dat(r,rs,i,rscbin,"cap") } ;
*Set the default resource reduction fraction
  rsc_reduct_frac(pcat,r) = 0.25 ;
*If the resource reduction fraction will reduce the resource to the point that prescribed builds will be infeasible,
*then replace the resource reduction fraction with the maximum that the resource can be reduced to still have a feasible solution
  rsc_reduct_frac(pcat,r)$[prescrip_rsc_frac(pcat,r) > (1 - rsc_reduct_frac(pcat,r))] = 1 - prescrip_rsc_frac(pcat,r) ;
*Now reduce the resource by the updated resource reduction fraction
  rsc_dat(r,rs,i,rscbin,"cap") = rsc_dat(r,rs,i,rscbin,"cap") * (1 - sum{pcat$prescriptivelink(pcat,i), rsc_reduct_frac(pcat,r) }) ;
) ;
