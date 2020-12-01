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
Sw_CurtFlow          "Switch to turn on curtailment trading between regions"              /%GSw_CurtFlow%/
Sw_CurtMarket        "Switch to specify price (in 2004$/MWh) for curtailed VRE"           /%GSw_CurtMarket%/
Sw_EFS_Flex          "Switch indicating if EFS flexibility is available"                  /%GSw_EFS_Flex%/
Sw_EV                "Switch to include electric vehicle load"                            /%GSw_EV%/
Sw_ForcePrescription "Switch enforcing near term limits on capacity builds"               /%GSw_ForcePrescription%/
Sw_GasCurve          "Switch to have a national gas curve [0] or regional gas curves [1]" /%GSw_GasCurve%/
Sw_GenMandate        "Switch for the national generation constraint"                      /%GSw_GenMandate%/
Sw_Geothermal        "Switch to remove [0], have default [1], or extended [1] geothermal" /%GSw_Geothermal%/
Sw_GrowthAbsCon      "Switch for the absolute growth constraint"                          /%GSw_GrowthAbsCon%/
Sw_GrowthRelCon      "Switch for the relative growth constraint"                          /%GSw_GrowthRelCon%/
Sw_HighCostTrans     "Switch to increase costs and losses of transmission"                /%GSw_HighCostTrans%/
Sw_Int_CC            "Switch for intertemporal CC (0=ave, 1=marg, 2=scaled marg)"         /%GSw_Int_CC%/
Sw_Int_Curt          "Switch for intertemporal Curt (0=ave, 1=marg, 2=scaled marg)"       /%GSw_Int_Curt%/
Sw_Loadpoint         "Switch to use a loadpoint for the intertemporal case"               /%GSw_Loadpoint%/
Sw_MinCFCon          "Switch for the minimum annual capacity factor constraint"           /%GSw_MinCFCon%/
Sw_Mingen            "Switch to include or remove MINGEN variable"                        /%GSw_Mingen%/
Sw_NearTermLimits    "Switch enforcing near term limits on capacity builds"               /%GSw_NearTermLimits%/
Sw_NukeCoalFOMAdj    "Switch to adjust nuclear and coal FOM costs similar to NEMS"        /%GSw_NukeCoalFOM%/
Sw_OpRes             "Switch for the operating reserves constraints"                      /%GSw_OpRes%/
Sw_ReducedResource   "Switch to reduce the amount of RE resource available"               /%GSw_ReducedResource%/
Sw_Refurb            "Switch allowing refurbishments"                                     /%GSw_Refurb%/
Sw_ReserveMargin     "Switch for the planning reserve margin constraints"                 /%GSw_ReserveMargin%/
Sw_Retire            "Switch allowing endogenous retirements"                             /%GSw_Retire%/
Sw_RGGI              "Switch for the RGGI constraint"                                     /%GSw_RGGI%/
Sw_SolarRelLim       "Annual relative growth limit for UPV and DUPV technologies"         /%GSw_SolarRelLim%/
Sw_StateRPS          "Switch for the state RPS constraints"                               /%GSw_StateRPS%/
Sw_Storage           "Switch for allowing storage (both existing and new)"                /%GSw_Storage%/
Sw_TranRestrict      "Switch for restricting transmission builds"                         /%GSw_TranRestrict%/
Sw_Upgrades          "Switch to enable or disable upgrades - not to be used with water"   /%GSw_Upgrades%/
Sw_CCS               "Switch for allowing CCS (both existing and new)"                    /%GSw_CCS%/
Sw_WindRelLim        "Annual relative growth limit for wind (ons and ofs) technologies"   /%GSw_WindRelLim%/
Sw_WaterMain         "Switch for the representation of water use and source types"        /%GSw_WaterMain%/
Sw_WaterCapacity     "Switch for the water capacity constraints"                          /%GSw_WaterCapacity%/
Sw_WaterUse          "Switch for the water capacity and water use constraints"            /%GSw_WaterUse%/
Sw_CoolingTechMults  "Switch to enable cooling tech cost/performance multipliers"         /%GSw_CoolingTechMults%/
;

*year-related switches that define retirement and upgrade start dates
scalar retireyear  "first year to allow capacity to start retiring" /%GSw_Retireyear%/
       upgradeyear "first year to allow capacity to upgrade"        /%GSw_Upgradeyear%/;


set timetype "Type of time method used in the model"
/ seq, win, int / ;

parameter Sw_Timetype(timetype) "Switch that specifies the type of time method used in the model" ;

Sw_Timetype("%timetype%") = 1 ;

*==========================
* --- Set Declarations ---
*==========================

set i "generation technologies"
   /
      ice,
      battery_2
      battery_4
      battery_6
      battery_8
      battery_10
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
      RE-CT
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
      csp3_1*csp3_12,
      csp4_1*csp4_12,
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
*upgrade technologies
      Gas-CC_Gas-CC-CCS
      Gas-CT_RE-CT
      CoalOldUns_CoalOldScr
      CoalOldUns_CofireOld
      CoalOldScr_CofireOld
      Coal-new_CofireNew
      Coal-IGCC_coal-CCS
      coal-new_coal-CCS
      CoalOldScr_coal-CCS
      CoalOldUns_coal-CCS
      CofireNew_coal-CCS
      CofireOld_coal-CCS
*water technologies
$ifthene.ctech %GSw_WaterMain% == 1
$include inputs_case%ds%i_coolingtech_watersource.csv
$endif.ctech
   /,

  ctt "cooling technology type"
    /
    o "once through",
    r "recirculating",
    d "dry cooled",
    p "pond cooled",
    n "no cooling (or generic placeholder)"
    /,

  wst "water source type"
    /
    fsu "fresh surface water that is unappropriated (formerly Unappropriated)",
    fsa "fresh surface water that is appropriated (formerly Appropriated)",
    fsl "fresh surface lake",
    fg  "fresh groundwater (formerly Potable Groundwater)",
    sg  "brackish or saline groundwater (formerly Brackish Groundwater)",
    ss  "saline surface water (new category)",
    ww  "wastewater effluent (formerly Wastewater)"
    /,

  w "form of water use (withdrawal or consumption)" / with, cons / ,

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
    csp3_1*csp3_12
    csp4_1*csp4_12
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
  /,
*Technologies with certain combinations of power technology, cooling technology, and
*water source are also banned from new capacity below after defining
*linking sets between i, ctt, and wst.

*Data is insufficient to characterize new pond cooling systems, regulations effectively
*prohibit new once-through cooling
  bannew_ctt(ctt) "banned ctt from creating new non-numeraire techs, usually due to lacking data or representation"
  /
    o
    p
  /,

  bannew_wst(wst) "banned wst from creating new non-numeraire techs, usually due to lacking data or representation"
  /
    fsl
    ss
  / ;

alias(i,ii,iii) ;
set i_water_cooling(i) "derived technologies from original technologies with cooling technologies other than just none",
*Hereafter numeraire techs in cooling-water context mean original technologies,
*like gas-CC, and non-numeraire techs mean techs that are derived from numeraire techs
*with cooling technology type and water source data appended to them, like gas-CC_r_fsa
*-- it is gas-CC with recirculating cooling and fresh surface appropriated water source.

  i_water_nocooling(i) "technologies that use water, but not for cooling purposes"
  /
        Hydro
        Gas-CT
        geothermal
*       ocean
        distPV
  /,

  i_water(i) "technologies that use water for cooling and non-cooling purposes",
  i_ii_ctt_wst(i,ii,ctt,wst) "linking set between non-numeraire techs, numeraire techs, cooling technology types, and water source types",
*linking sets extracted from i_ii_ctt_wst(i,ii,ctt,wst) that allow one-one mapping among dimensions
  i_ctt(i,ctt) "linking set between non-numeraire techs and cooling technology types",
  i_wst(i,wst) "linking set between non-numeraire techs and water source types",
  wst_i_ii(i,ii) "linking set between non-numeraire techs and numeraire techs",
  ctt_i_ii(i,ii) "linking set between non-numeraire techs and numeraire techs";

*input parameters for non-numeraire techs and linking set only if Sw_WaterMain is ON and start with a blank slate
i_water_cooling(i) = no ;
i_ii_ctt_wst(i,ii,ctt,wst) = no ;
$ifthen.coolingwatersets %GSw_WaterMain% == 1
set i_water_cooling_temp(i)
  /
$include inputs_case%ds%i_coolingtech_watersource.csv
  /,

  i_ii_ctt_wst_temp(i,ii,ctt,wst)
  /
$ondelim
$include inputs_case%ds%i_coolingtech_watersource_link.csv
$offdelim
  / ;

i_water_cooling(i)$i_water_cooling_temp(i) = yes ;
i_ii_ctt_wst(i,ii,ctt,wst)$i_ii_ctt_wst_temp(i,ii,ctt,wst) = yes ;
$endif.coolingwatersets

i_water(i)$[i_water_cooling(i) or i_water_nocooling(i)] = yes ;

*linking sets between non-numeraire techs, numeraire techs, cooling tech, and water source
i_ctt(i,ctt)$[sum{(ii,wst)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = YES ;
i_wst(i,wst)$[sum{(ii,ctt)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = YES ;
*wst_i_ii(i,ii) and ctt_i_ii(i,ii) are identical linking set between non-numeraire and numeraire techs,
*kept both for clarity of use in cooling technology and water source related formulations
wst_i_ii(i,ii)$[sum{(wst,ctt)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = YES ;
ctt_i_ii(i,ii)$[sum{(wst,ctt)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = YES ;

if(Sw_WaterMain = 1,
*By default, ban new builds with bannew_ctt cooling techs for all i,
bannew(i)$[sum(ctt$bannew_ctt(ctt), i_ctt(i,ctt))] = YES ;

* ban new builds of Nuclear and coal-CCS with dry cooling techs as cooling requirements
* of nuclear and coal-CCS make dry cooling impractical
bannew(i)$[sum{ctt_i_ii(i,'Nuclear'), i_ctt(i,'d') }] = YES ;
bannew(i)$[sum{ctt_i_ii(i,'coal-CCS'), i_ctt(i,'d') }] = YES ;

*ban and bannew all non-numeraire techs that are derived from ban numeraire techs
ban(i)$sum{ii$ban(ii), ctt_i_ii(i,ii) } = YES ;
bannew(i)$sum{ii$bannew(ii), ctt_i_ii(i,ii) } = YES ;

* ban new builds of water sources included in bannew_wst for all i
bannew(i)$[sum(wst$bannew_wst(wst), i_wst(i,wst))] = YES ;
) ;

set i_numeraire(i) "numeraire techs that need cooling" ;
*i_numeraire(i) will be removed from valcap set as these technologies are ultimately
*expanded to non-numeraire techs. valcap will have non-numeraire techs if Sw_WaterMain=1
*or will have numeraire techs otherwise.
i_numeraire(ii)$sum{(wst,ctt,i)$i_ii_ctt_wst(i,ii,ctt,wst), 1 } = yes ;

table ctt_hr_mult(i,ctt) "heatrate multipliers to differentiate cooling technology types"
$offlisting
$ondelim
$include inputs_case%ds%heat_rate_mult.csv
$offdelim
$onlisting
;

table ctt_cc_mult(i,ctt) "capital cost multipliers to differentiate cooling technology types"
$offlisting
$ondelim
$include inputs_case%ds%cost_cap_mult.csv
$offdelim
$onlisting
;

table ctt_cost_vom_mult(i,ctt) "VOM cost multipliers to differentiate cooling technology types"
$offlisting
$ondelim
$include inputs_case%ds%cost_vom_mult.csv
$offdelim
$onlisting
;

set geotech "broader geothermal categories"
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
  gas(i)               "techs that use gas (but not o-g-s)",
  gas_cc(i)            "techs that are gas combined cycle"
  gas_ct(i)            "techs that are gas combustion turbine"
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
  csp3(i)              "csp-tes generation technologies 3",
  csp4(i)              "csp-tes generation technologies 4",
  storage(i)           "storage technologies",
  storage_no_csp(i)    "storage technologies that are not CSP",
  thermal_storage(i)   "thermal storage technologies",
  battery(i)           "battery storage technologies",
  cofire(i)            "cofire technologies",
  hydro(i)             "hydro technologies",
  hydro_d(i)           "dispatchable hydro technologies",
  hydro_nd(i)          "non-dispatchable hydro technologies",
  psh(i)               "pumped hydro storage technologies",
  geo(i)               "geothermal technologies"
  geo_base(i)          "geothermal technologies typically considered in model runs"
  geo_extra(i)         "geothermal technologies not typically considered in model runs"
  geo_undisc(i)        "undiscovered geothermal technologies"
  canada(i)            "Canadian imports",
  vre_no_csp(i)        "variable renewable energy technologies that are not csp",
  vre_utility(i)       "utility scale wind and PV technologies",
  vre_distributed(i)   "distributed PV technologies",
  upgrade(i)           "technologies that are upgrades from other technologies",
  nuclear(i)           "nuclear generation"
  plx_convqn(i)        "conventional technology subset for ReEDS2_PLEXOS_translator -- not used in ReEDS"
  plx_reserves(i)      "Operational reserve tecnologies for ReEDS2_PLEXOS_translator -- not used in ReEDS"
  plx_gas(i)           "gas subset for ReEDS2_PLEXOS_translator -- not used in ReEDS"
  plx_csp_st(i)        "technology subset used for ReEDS2_PLEXOS_translator -- not used in ReEDS"


i_subtech technology subset categories
   /
      COAL
      GAS
      GAS_CC
      GAS_CT
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
      CSP3
      CSP4
      STORAGE
      STORAGE_NO_CSP
      THERMAL_STORAGE
      BATTERY
      COFIRE
      HYDRO
      HYDRO_D
      HYDRO_ND
      PSH
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
      UPGRADE
      NUCLEAR
      PLX_CONVQN
      PLX_RESERVES
      PLX_GAS
      PLX_CSP_ST

   /,

allt "all potential years" /1900*2121/,

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

sdbin "storage duration bins" /2,4,6,8,10,12,24,8760/,

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

ccreg "capacity credit regions" /cc1*cc27/,

cendiv "census divisions" /PA, MTN, WNC, ENC, WSC, ESC, SA, MA, NE, MEX/,

interconnect "interconnection regions" /western, eastern, texas, quebec, mexico/,

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
    csp.(csp1_1*csp1_12, csp2_1*csp2_12, csp3_1*csp3_12, csp4_1*csp4_12)
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

set cspns(i) "csp techs without storage" ;
cspns(i)$sameas(i,"csp-ns") = yes ;
cspns(i)$[ctt_i_ii(i,"csp-ns")$Sw_WaterMain] = yes ;

set cspns_pcat(pcat) "exact alias of cspns(i) in pcat domain";
cspns_pcat(pcat)$sum{i$[cspns(i)$sameas(pcat,i)], 1 } = yes ;

set src "sources of storage charging"
/ pv, wind, old, other / ;

alias(r,rr) ;
alias(rto,rto2) ;
alias(rs,rss) ;
alias(h,hh) ;
alias(v,vv) ;
alias(t,tt,ttt) ;
alias(st,ast,aast) ;
alias(allt,alltt) ;
alias(cendiv,cendiv2) ;

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

set nexthflex(h,hh) "order of flexible hour blocks"
  /
    H1.H2, H2.H3, H3.H4, H3.H17, H4.H1,
    H5.H6, H6.H7, H7.H8, H8.H5,
    H9.H10, H10.H11, H11.H12, H12.H9,
    H13.H14, H14.H15, H15.H16, H16.H13, H17.H4
  /
;

set prevhflex(h,hh) "reverse order of flexible hour blocks"
  /
    H2.H1, H3.H2, H4.H3, H4.H17, H1.H4,
    H6.H5, H7.H6, H8.H7, H5.H8,
    H10.H9, H11.H10, H12.H11, H9.H12,
    H14.H13, H15.H14, H16.H15, H13.H16, H17.H3
  /
;

set adjhflex(h,hh) "adjacent flexible hour blocks"
/
    H1.H2, H2.H3, H3.H4, H3.H17, H4.H1,
    H5.H6, H6.H7, H7.H8, H8.H5,
    H9.H10, H10.H11, H11.H12, H12.H9,
    H13.H14, H14.H15, H15.H16, H16.H13, H17.H4
    H2.H1, H3.H2, H4.H3, H4.H17, H1.H4,
    H6.H5, H7.H6, H8.H7, H5.H8,
    H10.H9, H11.H10, H12.H11, H9.H12,
    H14.H13, H15.H14, H16.H15, H13.H16, H17.H3
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

Set upgrade_to(i,ii)         "mapping set that allows for i to be upgraded to ii"
    upgrade_from(i,ii)       "mapping set that allows for i to be upgraded from ii"
    upgrade_link(i,ii,iii)   "indicates that tech i is upgradeable from ii with a delta base of iii"
/
$offlisting
$ondelim
$include inputs_case%ds%upgrade_link.csv
$offdelim
$onlisting
/ ;

upgrade(i)$[sum{(ii,iii), upgrade_link(i,ii,iii) }] = yes;
upgrade_to(i,ii)$[sum{iii, upgrade_link(i,iii,ii) }] = yes ;
upgrade_from(i,ii)$[sum{iii, upgrade_link(i,ii,iii) }] = yes ;

bannew(i)$[upgrade(i)$(not Sw_Upgrades)] = yes ;

* --- Read technology subset lookup table ---
Table i_subsets(i,i_subtech) "technology subset lookup table"
$offlisting
$ondelim
$include inputs_case%ds%tech-subset-table.csv
$offdelim
$onlisting
;

*assign subtechs to each upgrade tech
*based on what they will be upgraded to
i_subsets(i,i_subtech)$[upgrade(i)$Sw_Upgrades] =
  sum{ii$upgrade_to(i,ii), i_subsets(ii,i_subtech) } ;

*approach in cooling water formulation is populating parameters of numeraire tech (e.g. gas-CC)
*for non-numeraire techs (e.g. gas-CC_r_fsa; r = recirculating cooling, fsa=fresh surface appropriated water source)
*e.g. populate i_subsets for non-numeraire techs from numeraire tech using a linking set ctt_i_ii(i,ii)
i_subsets(i,i_subtech)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), i_subsets(ii,i_subtech) } ;

* --- define technology subsets ---
COAL(i)             = YES$i_subsets(i,'COAL') ;
GAS(i)              = YES$i_subsets(i,'GAS') ;
GAS_CC(i)           = YES$i_subsets(i,'GAS_CC') ;
GAS_CT(i)           = yes$i_subsets(i,'GAS_CT') ;
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
CSP3(i)             = YES$i_subsets(i,'CSP3') ;
CSP4(i)             = YES$i_subsets(i,'CSP4') ;
STORAGE(i)          = YES$i_subsets(i,'STORAGE') ;
STORAGE_NO_CSP(i)   = YES$i_subsets(i,'STORAGE_NO_CSP') ;
THERMAL_STORAGE(i)  = YES$i_subsets(i,'THERMAL_STORAGE') ;
BATTERY(i)          = YES$i_subsets(i,'BATTERY') ;
COFIRE(i)           = YES$i_subsets(i,'COFIRE') ;
HYDRO(i)            = YES$i_subsets(i,'HYDRO') ;
HYDRO_D(i)          = YES$i_subsets(i,'HYDRO_D') ;
HYDRO_ND(i)         = YES$i_subsets(i,'HYDRO_ND') ;
PSH(i)              = YES$i_subsets(i,'PSH') ;
GEO(i)              = YES$i_subsets(i,'GEO') ;
GEO_BASE(i)         = YES$i_subsets(i,'GEO_BASE') ;
GEO_EXTRA(i)        = YES$i_subsets(i,'GEO_EXTRA') ;
GEO_UNDISC(i)       = YES$i_subsets(i,'GEO_UNDISC') ;
CANADA(i)           = YES$i_subsets(i,'CANADA') ;
VRE_NO_CSP(i)       = YES$i_subsets(i,'VRE_NO_CSP') ;
VRE_UTILITY(i)      = YES$i_subsets(i,'VRE_UTILITY') ;
VRE_DISTRIBUTED(i)  = YES$i_subsets(i,'VRE_DISTRIBUTED') ;
NUCLEAR(i)          = yes$i_subsets(i,'NUCLEAR') ;
PLX_CONVQN(i)       = yes$i_subsets(i,'PLX_CONVQN') ;
PLX_RESERVES(i)     = yes$i_subsets(i,'PLX_RESERVES') ;
PLX_GAS(i)          = yes$i_subsets(i,'PLX_GAS') ;
PLX_CSP_ST(i)       = yes$i_subsets(i,'PLX_CSP_ST') ;
CSP_Storage(i)$csp1(i) = yes ;
CSP_Storage(i)$csp2(i) = yes ;
CSP_Storage(i)$csp3(i) = yes ;
CSP_Storage(i)$csp4(i) = yes ;

set i_src(i,src) "linking set between i and src" ;
i_src(i,"pv")$pv(i) = yes ;
i_src(i,"wind")$wind(i) = yes ;

*add non-numeraire CSPs in index i of already defined set tg_i(tg,i)
tg_i("csp",i)$[(csp1(i) or csp2(i) or csp3(i) or csp4(i))$Sw_WaterMain] = yes ;

table water_with_cons_rate(i,ctt,w,r) "--gal/MWh-- technology specific-cooling tech based water withdrawal and consumption data"
$offlisting
$ondelim
$include inputs_case%ds%water_with_cons_rate.csv
$offdelim
$onlisting
;

*populate the water withdrawal and consumption data to non-numeraire technologies
*based on numeraire techs and cooling technologies types to avoid repetitive
*entry of data in the input data file and provide flexibility
*in populating data if new combinations come along the way
water_with_cons_rate(i,ctt,w,r)$i_water_cooling(i) =
  sum{(ii,wst)$i_ii_ctt_wst(i,ii,ctt,wst), water_with_cons_rate(ii,ctt,w,r) } ;
*csp-ns and csp-ws have same water withdrawal and consumption rates; populating csp-ws data with the data of csp-ns
water_with_cons_rate(i,ctt,w,r)$[i_water_cooling(i)$(csp1(i) or csp2(i) or csp3(i) or csp4(i))] =
  sum{(ii,wst)$i_ii_ctt_wst(i,ii,ctt,wst), water_with_cons_rate("csp-ns",ctt,w,r) } ;
water_with_cons_rate(ii,ctt,w,r)$[sum{(wst,i)$i_ii_ctt_wst(i,ii,ctt,wst), 1 }] = no ;

parameter water_rate(i,w,r) "--gal/MWh-- water withdrawal/consumption w rate in region r by technology i" ;
* adding geothermal categories for water accounting
i_water(i)$geo(i) = yes ;
water_with_cons_rate(i,ctt,w,r)$geo(i) = water_with_cons_rate("geothermal",ctt,w,r) ;

* Till this point, i already has non-numeraire techs (e.g., gas-CC_o_fsa, gas-CC_r_fsa,
*and gas-CC_r_fg) instead of numeraire technology (e.g., gas-CC)
* The line below just removes ctt dimension, by summing over ctt.
water_rate(i,w,r)$i_water(i) = sum{ctt, water_with_cons_rate(i,ctt,w,r) } ;

set cf_tech(i) "technologies that have a specified capacity factor",
    dispatchtech(i) "technologies that are dispatchable",
    retiretech(i,v,r,t) "combinations of i,v,r,t that can be retired",
    refurbtech(i) "technologies that can be refurbished",
    sccapcosttech(i) "technologies that have their capital costs embedded in supply curves",
    inv_cond(i,v,r,t,tt) "allows an investment in tech i of class v to be built in region r in year tt and usable in year t" ;

dispatchtech(i)$[not(vre(i) or hydro_nd(i))] = yes ;
sccapcosttech(i)$[geo(i) or hydro(i) or psh(i)] = yes ;

*pv/wind/csp/hydro techs have capacity factors based on resouce assessments
cf_tech(i)$[pv(i) or wind(i) or csp(i) or hydro(i)] = yes ;

*initialize sets to "no"
retiretech(i,v,r,t) = no ;
inv_cond(i,v,r,t,tt) = no ;

parameter min_retire_age(i) "minimum retirement age by technology"
/
$offlisting
$ondelim
$include inputs_case%ds%min_retire_age.csv
$offdelim
$onlisting
/
;

min_retire_age(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), min_retire_age(ii) } ;

scalar retire_penalty "--fraction-- penalty for retiring a power plant expressed as a fraction of FOM" /%GSw_RetirePenalty%/ ;


set prescriptivelink0(pcat,ii) "initial set of prescribed categories and their technologies - used in creating valid sets in force_pcat"
/
  upv.(upv_1*upv_10)
  dupv.(dupv_1*dupv_10)
  wind-ons.(wind-ons_1*wind-ons_10)
  csp-ws.(csp1_1*csp1_12,csp2_1*csp2_12)
  wind-ofs.(wind-ofs_1*wind-ofs_15)
  geothermal.(geohydro_pbinary_1*geohydro_pbinary_8,geohydro_pflash_1*geohydro_pflash_8)
/ ;
*include non-numeraire CSPs and then exclude numeraire CSPs in ii dimension of
*prescriptivelink0(pcat,ii) set when Sw_WaterMain is ON
prescriptivelink0("csp-ws",ii)$[(csp1(ii) or csp2(ii) or csp3(ii) or csp4(ii))$Sw_WaterMain] = yes ;
prescriptivelink0("csp-ws",ii)$[csp(ii)$i_numeraire(ii)$Sw_WaterMain] = no ;

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

*upgrades have no prescriptions
prescriptivelink(pcat,i)$[upgrade(i)] = no ;

set rsc_agg(i,ii)   "rsc technologies that belong to the same class",
    tg_rsc_cspagg(i,ii) "csp technologies that belong to the same class"
    /
    csp1_1.(csp1_1, csp2_1, csp3_1, csp4_1),
    csp1_2.(csp1_2, csp2_2, csp3_2, csp4_2),
    csp1_3.(csp1_3, csp2_3, csp3_3, csp4_3),
    csp1_4.(csp1_4, csp2_4, csp3_4, csp4_4),
    csp1_5.(csp1_5, csp2_5, csp3_5, csp4_5),
    csp1_6.(csp1_6, csp2_6, csp3_6, csp4_6),
    csp1_7.(csp1_7, csp2_7, csp3_7, csp4_7),
    csp1_8.(csp1_8, csp2_8, csp3_8, csp4_8),
    csp1_9.(csp1_9, csp2_9, csp3_9, csp4_9),
    csp1_10.(csp1_10, csp2_10, csp3_10, csp4_10),
    csp1_11.(csp1_11, csp2_11, csp3_11, csp4_11),
    csp1_12.(csp1_12, csp2_12, csp3_12, csp4_12)
    /
;

set tg_rsc_cspagg_tmp(i,ii) "expanded tg_rsc_cspagg(i,ii) to include new non-numeraire CPSs" ;

*input parameters for linking set only when Sw_WaterMain is ON and start with a blank slate
tg_rsc_cspagg_tmp(i,ii) = no ;
$ifthen.coolingwatersets %GSw_WaterMain% == 1
set tg_rsc_cspagg_tmp_temp(i,ii)
  /
$ondelim
$include inputs_case%ds%tg_rsc_cspagg_tmp.csv
$offdelim
  / ;
tg_rsc_cspagg_tmp(i,ii)$tg_rsc_cspagg_tmp_temp(i,ii) = yes ;
$endif.coolingwatersets

*include non-numeraire CSPs and then exclude numeraire CSPs in ii dimension
*of tg_rsc_cspagg(i,ii) set when Sw_WaterMain is ON
tg_rsc_cspagg(i,ii)$[tg_rsc_cspagg_tmp(i,ii)$Sw_WaterMain] = yes ;
tg_rsc_cspagg(i,ii)$[csp(ii)$i_numeraire(ii)$Sw_WaterMain] = no ;

rsc_agg(i,ii)$[sameas(i,ii)$(not csp(i))$(not csp(ii))$rsc_i(i)$rsc_i(ii)] = yes ;
rsc_agg(i,ii)$tg_rsc_cspagg(i,ii) = yes ;


*============================
* -- Flexible hours setup --
*============================

set flex_type "set of demand flexibility types: daily, previous, next, adjacent"
  /
  previous, next, adjacent, daily
  /
  ;

set flex_h_corr1(flex_type,h,hh) "correlation set for hours referenced in flexibility constraints",
    flex_h_corr2(flex_type,h,hh) "correlation set for hours referenced in flexibility constraints";

flex_h_corr1("previous",h,hh) = prevhflex(h,hh);
flex_h_corr1("next",h,hh) = nexthflex(h,hh);
flex_h_corr1("adjacent",h,hh) = adjhflex(h,hh);

flex_h_corr2("previous",h,hh) = nexthflex(h,hh);
flex_h_corr2("next",h,hh) = prevhflex(h,hh);
flex_h_corr2("adjacent",h,hh) = adjhflex(h,hh);


*======================================
*     --- Begin hierarchy ---
*======================================

set hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg, ccreg) "hierarchy of various regional definitions"
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
    r_customreg(r,customreg)
    r_ccreg(r,ccreg) ;

r_nercr(r,nercr)$sum{(nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg),1} = yes ;
r_nercr_new(r,nercr_new)$sum{(nercr,rto,cendiv,st,interconnect,country,customreg,ccreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg),1} = yes ;
r_rto(r,rto)$sum{(nercr,nercr_new,cendiv,st,interconnect,country,customreg,ccreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg),1} = yes ;
r_cendiv(r,cendiv)$sum{(nercr,nercr_new,rto,st,interconnect,country,customreg,ccreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg),1} = yes ;
r_st(r,st)$sum{(nercr,nercr_new,rto,cendiv,interconnect,country,customreg,ccreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg),1} = yes ;
r_interconnect(r,interconnect)$sum{(nercr,nercr_new,rto,cendiv,st,country,customreg,ccreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg),1} = yes ;
r_country(r,country)$sum{(nercr,nercr_new,rto,cendiv,st,interconnect,customreg,ccreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg),1} = yes ;
r_customreg(r,customreg)$sum{(nercr,nercr_new,rto,cendiv,st,interconnect,country,ccreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg),1} = yes ;
r_ccreg(r,ccreg)$sum{(nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg)$hierarchy(r,nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg),1} = yes ;

parameter num_interconnect(interconnect) "interconnection numbers"
 /western 1, eastern 2, texas 3, quebec 4, mexico 5/ ;

*======================================
* ---------- Bintage Mapping ----------
*======================================
*following set is un-assumingly important
*it allows for the investment of bintage 'v' at time 't'

*table ivtmap(i,t)
table ivt_num(i,t) "number associated with bin for ivt calculation"
$offlisting
$ondelim
$include inputs_case%ds%ivt.csv
$offdelim
$onlisting
;


set ivt(i,v,t) "mapping set between i v and t - for new technologies" ;
ivt(i,newv,t)$[ord(newv) = ivt_num(i,t)] = yes ;

ivt(i,v,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), ivt(i,v,t) } ;

*important assumption here that upgrade technologies
*receive the same binning assumptions as the technologies
*that they are upgraded to - this allows for easier translation
*and mapping of plant characteristics (cost_vom, cost_fom, heat_rate)
ivt(i,newv,t)$[(yeart(t)>=upgradeyear)$upgrade(i)] = sum{ii$upgrade_to(i,ii), ivt(i,newv,t) } ;


parameter countnc(i,newv) "number of years in each newv set" ;

*add 1 for each t item in the ct_corr set
countnc(i,newv) = sum{t$ivt(i,newv,t),1} ;

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

scalar model_builds_start_yr "--integer-- Start year allowing new generators to be built" ;

*Ignore gas units becuase gas-ct's are allowed in historical years
model_builds_start_yr = smin{i$[(not gas(i))$(not distpv(i))], firstyear(i) } ;

firstyear(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), firstyear(ii)} ;
firstyear(i)$[not firstyear(i)] = model_builds_start_yr ;
firstyear(i)$[i_water_cooling(i)$(not Sw_WaterMain)] = NO ;
firstyear(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), firstyear(ii) } ;

parameter firstyear_pcat(pcat) ;
firstyear_pcat(pcat)$[sum{i$sameas(i,pcat), firstyear(i) }] = sum{i$sameas(i,pcat), firstyear(i) } ;
firstyear_pcat("upv") = firstyear("upv_1") ;
firstyear_pcat("dupv") = firstyear("dupv_1") ;
firstyear_pcat("wind-ons") = firstyear("wind-ons_1") ;
firstyear_pcat("wind-ofs") = firstyear("wind-ofs_1") ;
firstyear_pcat("csp-ws") = firstyear("csp2_1") ;
firstyear_pcat("csp-ns") = firstyear("csp2_1") ;


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
*created by /input_processing/writecapdat.py
table capnonrsc(i,r,*) "--MW-- raw capacity data for non-RSC tech created by .\input_processing\writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%allout_nonRSC.csv
$offdelim
$onlisting
;

*created by /input_processing/writecapdat.py
table caprsc(pcat,r,rs,*) "--MW-- raw RSC capacity data, created by .\writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%allout_RSC.csv
$offdelim
$onlisting
;

*created by /input_processing/writecapdat.py
table prescribednonrsc(t,pcat,r,*) "--MW-- raw prescribed capacity data for non-RSC tech created by writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_nonRSC.csv
$offdelim
$onlisting
;

*Created using input_processing\writecapdat.py
table prescribedrsc(t,pcat,r,rs,*) "--MW-- raw prescribed capacity data for RSC tech created by .\input_processing\writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_rsc.csv
$offdelim
$onlisting
;

*created by /input_processing/writecapdat.py
*following does not include wind
*Retirements for techs binned by heatrates are handled in hintage_data.csv
table prescribedretirements(allt,r,i,*) "--MW-- raw prescribed capacity retirement data for non-RSC, non-heatrate binned tech created by /input_processing/writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%retirements.csv
$offdelim
$onlisting
;


parameter prescribedretirements_copy(allt,r,i,*) "--MW-- copy of prescribedretirements" ;
prescribedretirements_copy(allt,r,i,"value") = prescribedretirements(allt,r,i,"value") ;

*If coal retirement switch is 1, shorten coal lifetimes by 10 years if the plant retires in 2030 or later
if(Sw_CoalRetire = 1,
     prescribedretirements(allt,r,i,"value")$[coal(i)$(allt.val >= 2030)] = 0 ;
     prescribedretirements(allt,r,i,"value")$coal(i) = prescribedretirements_copy(allt+10,r,i,"value")$(allt.val >= 2030-10) + prescribedretirements(allt,r,i,"value") ;
) ;

*If coal retirement switch is 2, extend coal lifetimes by 10 years if the plant retires in 2022 or later
if(Sw_CoalRetire = 2,
     prescribedretirements(allt,r,i,"value")$[coal(i)$(allt.val >= 2022)] = 0 ;
     prescribedretirements(allt,r,i,"value")$[coal(i)$(allt.val >= 2022)] = prescribedretirements_copy(allt-10,r,i,"value")$(allt.val >= 2022+10) ;
) ;

parameter forced_retire_input(i,r) "--integer-- year in which to force retirements of certain techs by region"
/
$offlisting
$ondelim
$include inputs_case%ds%forced_retirements.csv
$offdelim
$onlisting
/
;

parameter forced_retirements(i,r,t) "--MW-- capacity by region and technology that must be retired by a certain year";
forced_retirements(i,r,t)$[(yeart(t) >= forced_retire_input(i,r))$forced_retire_input(i,r)] = sum{(tt,pcat)$[(yeart(tt)<yeart(t))$prescriptivelink(pcat,i)], prescribednonrsc(tt,pcat,r,"value") } ;

$ifthen.unit %unitdata%=='ABB'
*created by /input_processing/writecapdat.py
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

parameter plant_age(i,v,r,t) "--years-- plant age of existing units" ;
*a plants age is the difference between the current year and
*the year at which the plant came online
plant_age(i,v,r,t)$sum{allt$sameas(allt,t), hintage_data(i,v,r,allt,"cap") } =
  max(0, yeart(t) - sum{allt$sameas(allt,t), hintage_data(i,v,r,allt,"wOnlineYear") }) ;

*created by /input_processing/writecapdat.py
parameter binned_capacity(i,v,r,allt) "existing capacity (that is not rsc, but including distPV) binned by heat rates" ;

binned_capacity(i,v,r,allt) = hintage_data(i,v,r,allt,"cap") ;

set bio(i) "all biopower technologies",
  ogs(i) "all o-g-s technologies"
;

bio(i)$[sameas(i,"biopower")] = yes ;
bio(i)$[ctt_i_ii(i,"biopower")$Sw_WaterMain] = yes ;

nuclear(i)$[sameas(i,"nuclear")] = yes ;
nuclear(i)$[ctt_i_ii(i,"nuclear")$Sw_WaterMain] = yes ;

ogs(i)$[sameas(i,"o-g-s")] = yes ;
ogs(i)$[ctt_i_ii(i,"o-g-s")$Sw_WaterMain] = yes ;

parameter maxage(i) "maximum age for technologies" ;

maxage(i) = 100 ;
maxage(i)$gas(i) = 55 ;
maxage(i)$coal(i) = 70 ;
maxage(i)$wind(i) = 30 ;
maxage(i)$upv(i) = 30 ;
maxage(i)$dupv(i) = 30 ;
maxage(i)$bio(i) = 45 ;
maxage(i)$geo(i) = 30 ;
maxage(i)$nuclear(i) = 80 ;
maxage(i)$hydro(i) = 100 ;
maxage(i)$csp(i) = 30 ;
maxage(i)$battery(i) = 15 ;

maxage(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), maxage(ii) } ;

*loading in capacity mandates here to avoid conflicts in calculation of valcap
parameter batterymandate(r,t) "--MW-- cumulative battery mandate levels"
/
$offlisting
$ondelim
$include inputs_case%ds%storage_mandates.csv
$offdelim
$onlisting
/
;

table offshore_cap_req(st,t) "--MW-- offshore wind capacity requirement under RPS rules by state"
$offlisting
$ondelim
$include inputs_case%ds%offshore_req.csv
$offdelim
$onlisting
;

parameter r_offshore(r,t) "regions where offshore wind is required by a mandate" ;

r_offshore(rs,t)$[sum{rb$r_rs(rb,rs), sum{st$r_st(rb,st), offshore_cap_req(st,t) } }$(not sameas(rs,'sk'))] = 1 ;

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
rscfeas(r,rs,i,rscbin)$[csp3(i)$sum{ii$[csp1(ii)$csp3(i)$tg_rsc_cspagg(ii,i)], rscfeas(r,rs,ii,rscbin) }] = yes ;
rscfeas(r,rs,i,rscbin)$[csp4(i)$sum{ii$[csp1(ii)$csp4(i)$tg_rsc_cspagg(ii,i)], rscfeas(r,rs,ii,rscbin) }] = yes ;

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
capacity_exog(i,"init-1",r,"sk",t)${[yeart(t)-sum{tt$tfirst(tt),yeart(tt)}<maxage(i)]$r_rs(r,"sk")$rb(r)$rfeas(r)} =
                                 max(0,capnonrsc(i,r,"value")
                                       - sum{allt$[allt.val <= t.val],  prescribedretirements(allt,r,i,"value") }
                                    ) ;

*reset any exogenous capacity that is also specified in binned_capacity
*as these are computed based on bins specified by the numhintage global
*in the data-writing files
capacity_exog(i,v,r,rs,t)$[sum{(rr,vv,allt), binned_capacity(i,vv,rr,allt) }$initv(v)$rfeas(r)] = 0 ;


capacity_exog("hydED","init-1",r,"sk",t)$r_rs(r,"sk") = caprsc("hydED",r,"sk","value") ;
capacity_exog("hydEND","init-1",r,"sk",t)$r_rs(r,"sk") = caprsc("hydEND",r,"sk","value") ;


*all binned capacity is for rs == sk
capacity_exog(i,v,r,"sk",t)$[r_rs(r,"sk")$sum{allt,binned_capacity(i,v,r,allt)}$rb(r)$rfeas(r)] =
               sum{allt$att(allt,t), binned_capacity(i,v,r,allt) } ;

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
m_capacity_exog(i,v,r,t)$m_capacity_exog(i,v,r,t) = round(m_capacity_exog(i,v,r,t),3) ;

parameter inv_distpv(r,t) "--MW-- capacity of distpv that is build in year t (i.e., INV for distpv)" ;

inv_distpv(r,t) = sum{(i,v)$distpv(i),
                      m_capacity_exog(i,v,r,t) - sum{tt$tprev(t,tt), m_capacity_exog(i,v,r,tt) }
                     } ;


table tech_banned(i,st) "Banned technologies by state"
$offlisting
$ondelim
$include inputs_case%ds%techs_banned.csv
$offdelim
$onlisting
;

set cap_agg(r,r) "set for aggregated resource regions to BAs"
    valcap(i,v,r,t) "i, v, r, and t combinations that are allowed for capacity",
    valcap_irt(i,r,t) "i, r, and t combinations that are allowed for capacity",
    valinv(i,v,r,t) "i, v, r, and t combinations that are allowed for investments",
    valinv_irt(i,r,t) "i, r, and t combinations that are allowed for investments",
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
required_prescriptions(pcat,rb,"sk",t)$rfeas(rb)
          = sum{tt$[yeart(t)>=yeart(tt)], prescribednonrsc(tt,pcat,rb,"value") } ;


required_prescriptions(pcat,r,rs,t)$[r_rs(r,rs)$rfeas(r)$sum{tt$[yeart(t)>=yeart(tt)], prescribedrsc(tt,pcat,r,rs,"value") }
                                    + caprsc(pcat,r,rs,"value")]
        = sum{(tt)$[(yeart(t) >= yeart(tt))], prescribedrsc(tt,pcat,r,rs,"value") }
        + caprsc(pcat,r,rs,"value")
;

m_required_prescriptions(pcat,rb,t)$tmodel_new(t) = required_prescriptions(pcat,rb,"sk",t) ;
m_required_prescriptions(pcat,rs,t)$[(not sameas(rs,"sk"))$tmodel_new(t)] = sum{r$r_rs(r,rs), required_prescriptions(pcat,r,rs,t) } ;
*remove csp-ns prescriptions at the BA level
m_required_prescriptions(pcat,rb,t)$cspns_pcat(pcat) = 0 ;

parameter degrade(i,t,tt) "degradation factor by i"
          degrade_pcat(pcat,t,tt) "degradation factor by pcat" ;

parameter degrade_annual(i) "annual degredation rate"
/
$offlisting
$ondelim
$include inputs_case%ds%degradation_annual.csv
$offdelim
$onlisting
/ ;
degrade_annual(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), degrade_annual(ii) } ;

degrade(i,t,tt)$[(yeart(tt)>=yeart(t))] = 1 ;
degrade(i,t,tt)$[(yeart(tt)>=yeart(t))] = (1-degrade_annual(i))**(yeart(tt)-yeart(t)) ;

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

set prescription_check(i,v,r,t) "check to see if prescriptive capacity comes online in a given year" ;

parameter noncumulative_prescriptions(pcat,r,t) "--MW-- prescribed capacity that comes online in a given year" ;
* need to fill in for unmodeled, gap years via tprev but
* tprev is not defined with tprev(t,tfirst)
noncumulative_prescriptions(pcat,rb,t)$[tmodel_new(t)$rfeas_cap(rb)]
                                  = sum{tt$[(yeart(tt)<=yeart(t)
* this condition populates values of tt which exist between the
* previous modeled year and the current year
                                          $(yeart(tt)>sum{ttt$tprev(t,ttt), yeart(ttt) }))
                                          ],
                                        prescribednonrsc(tt,pcat,rb,"value") + prescribedrsc(tt,pcat,rb,"sk","value")
                                      } ;

* now do the same thing for "rs" technologies
noncumulative_prescriptions(pcat,rs,t)$[tmodel_new(t)$rfeas_cap(rs)]
                                = sum{r$r_rs(r,rs), caprsc(pcat,r,rs,"value") }$tfirst(t)
                                 + sum{tt$[(yeart(tt)<=yeart(t)
                                          $(yeart(tt)>sum{ttt$tprev(t,ttt), yeart(ttt) }))
                                          ],
                                      sum{r$r_rs(r,rs), prescribedrsc(tt,pcat,r,rs,"value") }
                                  } ;

prescription_check(i,newv,r,t)$[sum{pcat$prescriptivelink(pcat,i), noncumulative_prescriptions(pcat,r,t) }
                               $ivt(i,newv,t)$tmodel_new(t)] = yes ;

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
*if available (via ivt) and if not an rsc tech
*and if it is not in ban or bannew
*the year also needs to be greater than the first year indicated
*for that specific class (this is the summing over tt portion)
*or it needs to be specified in prescriptivelink
valcap(i,newv,rb,t)$[rfeas(rb)$(not rsc_i(i))$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $(sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) })$(not upgrade(i))
                    ]  = yes ;

*for rsc technologies, enabled if m_rscfeas is populated
*similarly to non-rsc technologies except now all regions
*can be populated (rb vs r) and there is the additional condition
*that m_rscfeas must contain values in at least one rscbin
valcap(i,newv,r,t)$[rfeas_cap(r)$rsc_i(i)$tmodel_new(t)$(not ban(i))$(not bannew(i))
                    $sum{rscbin, m_rscfeas(r,i,rscbin) }$(not upgrade(i))
                    $sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) }
                    ]  = yes ;

*make sure sk region does not enter valcap
valcap(i,v,"sk",t) = no ;

*NEW capacity only valid in historical years if and only if it has required prescriptions
*logic here is that we don't want to populate the constraint with CAP <= 0 and instead
*want to simply remove the consideration for CAP altogether and make the constraint unnecessary
*note that the constraint itself is also conditioned on valcap

*therefore remove the consideration of valcap if...
valcap(i,newv,r,t)$[
*if there are no required prescriptions
                   (not sum{pcat$prescriptivelink(pcat,i),
                      m_required_prescriptions(pcat,r,t) } )
*if the year is before the first year the technology is allowed
                   $(yeart(t)<firstyear(i))
*if there is not a mandate for that technology in the region
                   $(not ([r_offshore(r,t) and ofswind(i)] or [batterymandate(r,t) and battery(i)]))
                  ] = no ;

*remove undisc geotechs until their first year since they are not able
*to meet the requirement for geothermal prescriptions
valcap(i,newv,r,t)$[(i_geotech(i,"undisc_pbinary") or i_geotech(i,"undisc_pflash"))
                   $(yeart(t)<firstyear(i))] = no ;

*remove any non-prescriptive build capabilities if they are not prescribed
valcap(i,newv,r,t)$[(not sameas(i,'gas-ct'))$(yeart(t)<firstyear(i))$(not sum{tt$(yeart(tt)<=yeart(t)), prescription_check(i,newv,r,tt) })
                   $(not ([r_offshore(r,t) and ofswind(i)] or [batterymandate(r,t) and battery(i)]))] = no ;

*enable prescribed builds of technologies that are earlier listed in bannew when Sw_WaterMain is ON
valcap(i,newv,r,t)$[Sw_WaterMain$sum(ctt$bannew_ctt(ctt),i_ctt(i,ctt))$rfeas(r)$tmodel_new(t)
                  $sum{(tt,pcat)$[(yeart(tt)<=yeart(t))$sameas(pcat,i)], m_required_prescriptions(pcat,r,tt)}
                  $sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) }] = yes ;

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
valcap(i,newv,r,t)$cspns(i) = no ;

valcap(i,newv,r,t)$[cspns(i)$(sum{pcat$cspns_pcat(pcat), m_required_prescriptions(pcat,r,t)})
                          $sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt)} ] = yes ;

valcap(i,v,r,t)$[not tmodel_new(t)] = no ;

valcap(i,v,r,t)$[i_numeraire(i)$Sw_WaterMain] = no ;


*upgraded capacity is available if the tech from which it is upgrading
*is also in valcap but are removed from valcap if sw_upgrades = 0
valcap(i,initv,r,t)$[upgrade(i)$Sw_Upgrades$(yeart(t)>=upgradeyear)
                    $sum{ii$upgrade_from(i,ii),valcap(ii,initv,r,t)}
                    ] = yes ;

*upgrades from new techs are included in valcap if...
* it is an upgrade tech, the switch is enabled, and past the beginning upgrade year
valcap(i,newv,r,t)$[upgrade(i)$Sw_Upgrades$(yeart(t)>=upgradeyear)
*if the capacity that it is upgraded from is available
                   $sum{ii$upgrade_from(i,ii),valcap(ii,newv,r,t)}
*if it is past the first year that technology is available
                   $(yeart(t)>=firstyear(i))
*if it is a valid ivt combination which is duplicated from upgrade_to
                   $sum{tt$(yeart(tt)<=yeart(t)),ivt(i,newv,tt)}
                   ] = yes ;


*remove any upgrade considerations if before the upgrade year
valcap(i,v,r,t)$[upgrade(i)$(yeart(t)<upgradeyear)] = no ;

*remove upgrade capacity consideration is the switch is disabled
*this is more of a failsafe for potential capacity leakage
valcap(i,v,r,t)$[upgrade(i)$(not Sw_Upgrades)] = no ;

* Add aggregations of valcap
valcap_irt(i,r,t) = sum{v, valcap(i,v,r,t) } ;


* -- valinv specification --
valinv(i,v,r,t) = no ;
valinv(i,v,r,t)$[valcap(i,v,r,t)$ivt(i,v,t)] = yes ;

valinv(i,v,rb,t)$[sum{st$r_st(rb,st),tech_banned(i,st)}$(not sum{pcat$prescriptivelink(pcat,i),noncumulative_prescriptions(pcat,rb,t)})] = no ;
*upgrades are not allowed for the INV variable as they are the sum of UPGRADES
valinv(i,v,r,t)$upgrade(i) = no ;

valinv(i,v,rb,t)$[(yeart(t)<firstyear(i))
                 $(not sum{pcat$prescriptivelink(pcat,i), noncumulative_prescriptions(pcat,rb,t) })
                 $(not [batterymandate(rb,t) and battery(i)])] = no ;

* Add aggregations of valinv
valinv_irt(i,r,t) = sum{v, valinv(i,v,r,t) } ;

* -- valgen specification --
* if the balancing area and/or its
* resource supply regions have valid capacity
*then you can generate from it

valgen(i,v,r,t) = no ;
valgen(i,v,r,t)$[sum{rr$cap_agg(r,rr),valcap(i,v,rr,t)}] = yes ;


* -- m_refurb_cond specification --

* technologies can be refurbished if...
*  they are part of refurbtech
*  the number of years from tt to t are beyond the expiration of the tech (via maxage)
*  it is valid capacity in t, the current solve year.
*  it was a valid investment in year tt, the initial investment year.
m_refurb_cond(i,newv,r,t,tt)$[refurbtech(i)
                              $(yeart(tt)<yeart(t))
                              $(yeart(t) - yeart(tt) > maxage(i))
                              $valcap(i,newv,r,t)$valinv(i,newv,r,tt)
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

inv_cond(i,newv,r,t,tt)$[Sw_WaterMain$sum(ctt$bannew_ctt(ctt),i_ctt(i,ctt))$rfeas(r)$tmodel_new(t)$tmodel_new(tt)
                      $sum{(pcat)$[sameas(pcat,i)], noncumulative_prescriptions(pcat,r,tt)}
                      $(yeart(tt) <= yeart(t))
                      $valinv(i,newv,r,tt)
                      $(ord(t)-ord(tt) < maxage(i))
                      ] = yes ;

*csp-ns needs to be able to be built in
*the first year to meet required prescriptions
*after that, it is replaced by detailed csp technologies
inv_cond(i,newv,r,t,tt)$cspns(i) = no ;

inv_cond(i,newv,r,t,tt)$[cspns(i)$
                      tmodel_new(t)$tmodel_new(tt)
                      $(yeart(tt) <= yeart(t))
*only allow csp to be built in years where prescriptions are enforced
                      $(yeart(tt) <= firstyear(i))
                      $valinv(i,newv,r,tt)
                      $(ord(t)-ord(tt) < maxage(i))
                      ] = yes ;

*==========================================
* --- Parameters for water constraints ---
*==========================================

set sw(wst) "surface water types where access is based on consumption not withdrawal" /fsu, fsa, fsl, ss/,
  i_water_surf(i) "subset of technologies that uses surface water",
  i_w(i,w) "linking set between technology and water use type used in constraining water availability" ;

i_water_surf(i)$[sum((sw,ctt,ii)$i_ii_ctt_wst(i,ii,ctt,sw), 1)] = yes ;
i_w(i,"cons")$[i_water(i)$i_water_surf(i)] = yes ;
i_w(i,"with")$[i_water(i)$(not i_water_surf(i))] = yes ;

parameter wat_supply_init(wst,r) "-- million gallons per year -- water supply allocated to initial fleet " ;

table wat_supply_new(wst,*,r)   "-- million gallons per year , $ per million gallons per year -- water supply curve for post-2010 capacity with *=cap,cost"
$offlisting
$ondelim
$include inputs_case%ds%wat_access_cap_cost.csv
$offdelim
$onlisting
;

parameter m_watsc_dat(wst,*,r,t)   "-- million gallons per year, $ per million gallons per year -- water supply curve data with *=cap,cost",
          watsa(wst,r,szn,t) "seasonal distribution factors for new water access by year (fractional)" ;

table watsa_temp(wst,r,szn)   "fractional seasonal allocation of water" \\ check with parameter
$offlisting
$ondelim
$include inputs_case%ds%unapp_water_sea_distr.csv
$offdelim
$onlisting
;
watsa(wst,r,szn,t)$[tmodel_new(t)$rfeas(r)$Sw_WaterMain] = watsa_temp(wst,r,szn) ;

parameter numdays(szn) "--number of days-- number of days for each season" ;
numdays(szn) = sum{h$h_szn(h,szn),hours(h)} / 24 ;

*update seasonal distribution factors for water sources other than fresh surface unappropriated
watsa(wst,r,szn,t)$[(not sameas(wst, "fsu"))$rfeas(r)$tmodel_new(t)$Sw_WaterMain] = round(numdays(szn)/365 , 2) ;

*Initialize water capacity based on water requirements of existing fleet in base year. We conservatively assume plants have
*enough water available to operate up to a 100% capacity factor, or to operate at full capacity at any time of the year.
wat_supply_init(wst,r) = (8760/1E6) * sum{(i,v,w,t)$[i_w(i,w)$valcap(i,v,r,t)$initv(v)$i_wst(i,wst)$tfirst(t)], m_capacity_exog(i,v,r,t) * water_rate(i,w,r) } ;

m_watsc_dat(wst,"cost",r,t)$tmodel_new(t) = wat_supply_new(wst,"cost",r) ;
m_watsc_dat(wst,"cap",r,t)$tmodel_new(t) = wat_supply_new(wst,"cap",r) + wat_supply_init(wst,r) ;

*not allowed to invest in upgrade techs since they are a product of upgrades
inv_cond(i,v,r,t,tt)$upgrade(i) = no;


*=====================================
* --- Regional Carbon Constraints ---
*=====================================


Set RGGI_States(st) "states facing RGGI regulation" /MA, CT, DE, MD, ME, NH, NJ, NY, RI, VT, VA/ ,
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

*assuming 2017 value from figure 9 of:
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


Parameter RecPerc(RPSCat,st,t)     "--fraction-- fraction of total generation for each state that must be met by RECs for each category"
          RPSTechMult(RPSCat,i,st) "--fraction-- fraction of generation from each technology that counts towards the requirement for each category"
;

Scalar RPS_StartYear "Start year for states RPS policies" /2020/ ;


RPSAll(i,st)$wind(i) = yes ;
RPSAll(i,st)$upv(i) = yes ;
RPSAll(i,st)$csp(i) = yes ;
RPSAll(i,st)$dupv(i) = yes ;
RPSAll("distpv",st)$[not sameas(st,"ca")] = yes ;
RPSAll(i,st)$bio(i) = yes ;
RPSAll("hydro",st) = yes ;
*treat canadian imports similar to hydro
RPSAll(i,st)$[geo(i)$(not RPS_bangeo(st))] = yes ;
RPSAll(i,st)$(RPSAll("hydro",st)$canada(i)) = yes ;
RPSAll("MHKwave",st) = yes ;

*rpscat definitions for each technology
RPSCat_i("RPS_All",i,st)$RPSAll(i,st) = yes ;
RPSCat_i("RPS_Wind",i,st)$wind(i) = yes ;
RPSCat_i("RPS_Solar",i,st)$[upv(i) or dupv(i) or sameas(i,"distpv")] = yes ;
RPSCat_i("CES",i,st)$[RPSCAT_i("RPS_All",i,st) or nuclear(i) or hydro(i)] = yes ;

* Massachusetts CES does not allow for existing hydro, so we don't allow any hydro
RPSCat_i("CES",i,'MA')$hydro(i) = no ;
* We allow renewable CT to be elegible for state CES policies
RPSCat_i("CES",'re-ct',st) = yes ;
* We allow CCS techs and upgrades to be elgible for CES policies
* CCS contribution is limited based on the amount of emissions captured later on down
RPSCat_i("CES",i,st)$[ccs(i) or upgrade(i)] = yes ;

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


RecStates(RPSCat,st,t)$[RecPerc(RPSCat,st,t) or sum{ast, rectable(ast,st) }] = yes ;

*if both states have an RPS for the RPSCat and if they're allowed to trade, they can trade
RecTrade(RPSCat,st,ast,t)$((rectable(ast,st)=1)$RecStates(RPSCat,ast,t)) = yes ;

*if both states have an RPS for the RPSCat and if they're allowed to trade, they can trade
RecTrade("RPS_bundled",st,ast,t)$[(rectable(ast,st)=2)$RecStates("RPS_all",ast,t)] = yes ;
RecTrade("CES_bundled",st,ast,t)$[(rectable(ast,st)=2)$RecStates("CES",ast,t)] = yes ;


RecTech(RPSCat,st,i,t)$(RPSCat_i(RPSCat,i,st)$RecStates(RPSCat,st,t)) = yes ;
RecTech(RPSCat,st,i,t)$(hydro(i)$RecTech(RPSCat,st,"hydro",t)) = yes ;
RecTech("RPS_Bundled",st,i,t)$[RecTech("RPS_All",st,i,t)] = yes ;

RecTech("CES",st,i,t)$[(RecTech("RPS_All",st,i,t)) or nuclear(i) or hydro(i)] = yes ;
RecTech("CES_Bundled",st,i,t)$[RecTech("RPS_All",st,i,t)] = yes ;


*california does not accept distpv credits
RecTech(RPSCat,"ca","distPV",t) = no ;
*make sure you cannot get credits from banned techs
*note we do not restrict by bannew here but the creation of
*RECS from bannew techs will be restricted via valgen
RecTech(RPSCat,st,i,t)$ban(i) = no ;

*remove combinations that are not allowed by valgen
RecTech(RPSCat,st,i,t)$[not sum{(v,r)$r_st(r,st), valgen(i,v,r,t) }] = no ;

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

RPSTechMult(RPSCat,i,st)$[not ban(i)] = 1 ;
RPSTechMult(RPSCat,i,st)$[hydro(i)$(sameas(RPSCat,"RPS_All") or sameas(RPSCat,"RPS_Bundled"))] = RPSHydroFrac(st) ;
*CCS technology have a 90% capture rate, so 90% of generation counts toward the requirement
RPSTechMult(RPSCat,i,st)$[ccs(i)$(sameas(RPSCat,"CES") or sameas(RPSCat,"CES_Bundled"))] = 0.9 ;
RPSTechMult(RPSCat,i,st)$[not sum{t, RecTech(RPSCat,st,i,t) }] = 0 ;

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
      $RPSTechMult(RPSCat,i,st)
      $RPSTechMult(RPSCat,i,ast)
      $RecMap("hydro",RPSCat,st,ast,t)
      ] = yes ;

if(Sw_WaterMain=1,
RecMap(i,RPSCat,st,ast,t)$i_water_cooling(i) = sum{ii$ctt_i_ii(i,ii), RecMap(ii,RPSCat,st,ast,t) } ;
) ;

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

set trtype                    "transmission capacity type" /AC, DC/
    trancap_fut_cat           "categories of near-term transmission projects that describe the likelihood of being completed" /certain, possible/
    tscfeas(r,vc)             "set to declare which transmission substation supply curve voltage classes are feasible for which regions"
    routes(r,rr,trtype,t)     "final conditional on transmission feasibility"
    routes_inv(r,rr,trtype,t) "routes where new transmission investment is allowed"
    opres_routes(r,rr,t)      "final conditional on operating reserve flow feasibility"
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
execute "=csv2gdx ..%ds%..%ds%inputs%ds%transmission%ds%transmission_capacity_future_%GSw_TranScen%.csv output=inputs_case%ds%trancap_fut_ac.gdx id=trancap_fut_ac index=(1..4) values=5 useHeader=y" ;
execute_load "inputs_case%ds%trancap_fut_ac.gdx", trancap_fut_ac ;

parameter trancap_fut_dc(r,rr,trancap_fut_cat,t) "--MW-- potential future DC transmission capacity (one direction)" ;
execute "=csv2gdx ..%ds%..%ds%inputs%ds%transmission%ds%transmission_capacity_future_%GSw_TranScen%.csv output=inputs_case%ds%trancap_fut_dc.gdx id=trancap_fut_dc index=(1..4) values=6 useHeader=y" ;
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
    + sum{tt$[(tt.val<=t.val)], trancap_fut(r,rr,"certain",tt,trtype)}
;

* --- valid transmission routes ---

*transmission routes are enabled if:
* (1) there is transmission capacity between the two regions
routes(r,rr,trtype,t)$(trancap_exog(r,rr,trtype,t) or trancap_exog(rr,r,trtype,t)) = yes ;
* (2) there is future capacity available between the two regions
routes(r,rr,trtype,t)$(sum{(tt,trancap_fut_cat)$(yeart(tt)<=yeart(t)),trancap_fut(r,rr,trancap_fut_cat,tt,trtype)}) = yes ;
* (3) there exists a route (r,rr) that is in the opposite direction as (rr,r)
routes(rr,r,trtype,t)$(routes(r,rr,trtype,t)) = yes ;

*disable routes that connect to a region not considered
routes(r,rr,trtype,t)$[(not rfeas(r)) or (not rfeas(rr))] = no ;

*initialize all routes to no
routes_inv(r,rr,trtype,t) = no ;

*If Sw_TranRestrict is 0, allow new builds along any feasible route,
*but not across interconnects
if(Sw_TranRestrict = 0,
    routes_inv(r,rr,trtype,t)$[(INr(r)=INr(rr))$routes(r,rr,trtype,t)] = yes ;
) ;

*If Sw_TranRestrict is 1, only allow intra-state transmission builds,
*and not across interconnects
if(Sw_TranRestrict = 1,
    routes_inv(r,rr,trtype,t)$[sum{st$[r_st(r,st)$r_st(rr,st)], 1 }
                     $routes(r,rr,trtype,t)
                     $(INr(r)=INr(rr))] = yes ;
) ;

*If Sw_TranRestrict is 2, don't allow any new trans (no logic required)

*If Sw_TranRestrict is 3, allow new builds along any feasible route,
*and allow interties across interconnects.
if(Sw_TranRestrict = 3,
    routes_inv(r,rr,trtype,t)$routes(r,rr,trtype,t) = yes ;
) ;

Scalar firstyear_tran "first year transmission investment is allowed" /2022/ ;

*Do not allow transmission investment until firstyear_tran
routes_inv(r,rr,trtype,t)$[yeart(t)<firstyear_tran] = no ;
*Do not allow DC expansion until 2030
routes_inv(r,rr,"DC",t)$[yeart(t)<2030] = no ;
*Do allow "possible" corridors to be expanded
routes_inv(r,rr,trtype,t)$[sum{tt$[(yeart(tt)<=yeart(t))], trancap_fut(r,rr,"possible",tt,trtype) + trancap_fut(rr,r,"possible",tt,trtype) }] = yes ;
routes_inv(rr,r,trtype,t)$[not routes_inv(r,rr,trtype,t)] = no ;

* operating reserve flows only allowed over AC lines
opres_routes(r,rr,t)$(routes(r,rr,"AC",t)) = yes ;

set samerto(r,rr) "binary indicator if two regions exist in the same rto: 1=same RTO, 0=not same RTO" ;
samerto(r,rr) = sum{(rto,rto2)$[r_rto(r,rto)$r_rto(rr,rto2)$sameas(rto,rto2)], 1 } ;

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
* Note that the distloss assumption is a generic estimate of distribution losses taken many years ago from AEO 2006
parameter tranloss(r,rr,trtype) "--fraction-- transmission loss between r and rr"
          tranloss_permile      "--fraction per mile-- transmission losses for regional trade" /0.0001/,
          distloss              "--fraction-- distribution loss rate from bus to final consumption" /0.05/ ;
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

set f fuel types / 'dfo','rfo', 'naturalgas', 'coal', 'uranium', 'biomass', 'rect'/ ;

set fuel2tech(f,i) "mapping between fuel types and generations"
   /
   coal.(coal-new,CoalOldScr,coalolduns,coal-ccs,coal-igcc),

   naturalgas.(gas-cc,gas-ct,o-g-s,gas-cc-ccs),

   uranium.(nuclear)

   biomass.(biopower,cofirenew,cofireold)

   rect.(RE-CT)
   / ;

*double check in case any sets have been changed.
fuel2tech("coal",i)$coal(i) = yes ;
fuel2tech("naturalgas",i)$gas(i) = yes ;
fuel2tech(f,i)$upgrade(i) = sum{ii$upgrade_to(i,ii), fuel2tech(f,ii) } ;


fuel2tech(f,i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), fuel2tech(f,ii) } ;

*===============================
*   Generator Characteristics
*===============================

set plantcat "catageries for plant characteristics" / capcost, fom, vom, heatrate, rte / ;

parameter plant_char0(i,t,plantcat) "--units vary-- input plant characteristics"
/
$offlisting
$include inputs_case%ds%plantcharout.txt
$onlisting
/ ;

*plant_char is indexed with v since cooling cost/technology performance multipliers only applies to new builds
parameter plant_char(i,v,t,plantcat) ;
plant_char(i,v,t,plantcat) = plant_char0(i,t,plantcat) ;
*plant_char cannot be conditioned with valcap or valgen here since the plant_char for unmodeled years is being
* used in calculations of heat_rate, cost_vom, and cost_fom and thus cannot be zeroed out

ctt_cost_vom_mult(i,ctt)$[(csp1(i) or csp2(i) or csp3(i) or csp4(i))$i_numeraire(i)] = ctt_cost_vom_mult("csp-ns",ctt) ;
ctt_cc_mult(i,ctt)$[(csp1(i) or csp2(i) or csp3(i) or csp4(i))$i_numeraire(i)] = ctt_cc_mult("csp-ns",ctt) ;

*populating empty entries of cooling technology type specific multipliers to 1
ctt_cost_vom_mult(i,ctt)$[(not ctt_cost_vom_mult(i,ctt))$i_numeraire(i)] = 1 ;
ctt_cc_mult(i,ctt)$[(not ctt_cc_mult(i,ctt))$i_numeraire(i)] = 1 ;
ctt_hr_mult(i,ctt)$[(not ctt_hr_mult(i,ctt))$i_numeraire(i)] = 1 ;

*applying the cooling technologies dependent multipliers to plant_char
*note that these multipliers are only applied to new builds
if(Sw_WaterMain=1,

if(Sw_CoolingTechMults = 0,
ctt_cost_vom_mult(i,ctt)$ctt_cost_vom_mult(i,ctt) = 1 ;
ctt_cc_mult(i,ctt)$ctt_cc_mult(i,ctt) = 1 ;
ctt_hr_mult(i,ctt)$ctt_hr_mult(i,ctt) = 1 ;
) ;

plant_char(i,v,t,"capcost")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],ctt_cc_mult(ii,ctt)*plant_char0(ii,t,"capcost") } ;
plant_char(i,v,t,"fom")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],plant_char0(ii,t,"fom") } ;
plant_char(i,v,t,"vom")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],ctt_cost_vom_mult(ii,ctt)*plant_char0(ii,t,"vom") } ;
plant_char(i,v,t,"heatrate")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],ctt_hr_mult(ii,ctt)*plant_char0(ii,t,"heatrate") } ;
plant_char(i,v,t,"rte")$[i_water_cooling(i)$newv(v)] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)],plant_char0(ii,t,"rte") } ;
) ;


*from KE's original model
parameter data_heat_rate_init(r,i) "initial heat rate" ;

$gdxin inputs_case%ds%sply_inputs.gdx
$load data_heat_rate_init
$gdxin

data_heat_rate_init(r,i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), data_heat_rate_init(r,ii) } ;

*=========================================
* --- Capital costs ---
*=========================================

parameter cost_cap(i,t)     "--2004$/MW-- overnight capital costs",
          cost_upgrade(i,t) "--2004$/MW-- overnight costs of upgrading to tech i"  ;
cost_cap(i,t) = plant_char0(i,t,"capcost") ;

cost_cap(i,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)], ctt_cc_mult(ii,ctt)*plant_char0(ii,t,"capcost") } ;

* Assigning csp-ns to have the same cost as csp2
cost_cap(i,t)$cspns(i) = cost_cap("csp2_1",t) ;

*costs for upgrading are the difference in capital costs
*between the initial techs and the tech to which the unit is upgraded
cost_upgrade(i,t)$upgrade(i) = sum{ii$upgrade_to(i,ii) ,cost_cap(ii,t) }
                               - sum{ii$upgrade_from(i,ii), cost_cap(ii,t) } ;

*increase cost_upgrade by 1% to prevent building and upgrading in the same year
*(otherwise there is a degeneracy between building new and building+upgrading in the same year)
cost_upgrade(i,t)$upgrade(i) = cost_upgrade(i,t) * 1.01 ;

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

table ofswind_rsc_mult(t,i) "multiplier by year for supply curve cost"
$offlisting
$ondelim
$include inputs_case%ds%ofswind_rsc_mult.csv
$offdelim
$onlisting
;

*Cost premium is the ratio of the 5 MW system cost to the 100 MW system cost from figure 28 of the
*U.S. Solar PV System Cost Benchmark: Q1 2018 (https://www.nrel.gov/docs/fy19osti/72399.pdf)
scalar dupv_cost_cap_mult "price premium for dupv over upv" /1.29/ ;


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

cost_vom(i,initv,r,t)$[(not Sw_BinOM)$valgen(i,initv,r,t)] = plant_char(i,initv,'2010','vom') ;

*if binning historical plants cost_vom, still need to assign default values to new plants
cost_vom(i,newv,r,t)$[(Sw_BinOM)$valgen(i,newv,r,t)] = plant_char(i,newv,t,'vom') ;

*if binning VOM and FOM costs, use the values written by writehintage.r for existing plants
cost_vom(i,initv,r,t)$[Sw_BinOM$valgen(i,initv,r,t)] = sum{allt$att(allt,t), hintage_data(i,initv,r,allt,"wVOM") } ;

*use default values if they are missing from the writehintage outputs
*but still active via valgen
cost_vom(i,initv,r,t)$[Sw_BinOM$(not cost_vom(i,initv,r,t))$valgen(i,initv,r,t)] =
                            plant_char(i,initv,'2010','vom') ;

*VOM costs by v are averaged over the class's associated
*years divided by those values
cost_vom(i,newv,r,t)$[valgen(i,newv,r,t)$countnc(i,newv)] =
  sum{tt$ivt(i,newv,tt), plant_char(i,newv,tt,'vom') } / countnc(i,newv) ;

cost_vom(i,v,rb,t)$[valcap(i,v,rb,t)$hydro(i)] = vom_hyd ;

*upgrade vom costs for initial classes are the vom costs for that tech
*plus the delta between upgrade_to and upgrade_from for the initial year
cost_vom(i,initv,r,t)$[upgrade(i)$Sw_Upgrades
                      $sum{ii$upgrade_from(i,ii), valcap(ii,initv,r,t) }] =
  sum{ii$upgrade_from(i,ii), cost_vom(ii,initv,r,t) }
  + sum{(ii,tt)$[upgrade_to(i,ii)$tfirst(tt)], plant_char(ii,initv,tt,"VOM") }
  - sum{(ii,tt)$[upgrade_from(i,ii)$tfirst(tt)], plant_char(ii,initv,tt,"VOM") } ;


*upgrade vom costs for new classes are the vom costs
*of the plant the upgrade is moving to - note that ivt
*for the upgrade and the upgrade_to plant are the same
cost_vom(i,newv,r,t)$[upgrade(i)$Sw_Upgrades$valcap(i,newv,r,t)
                      $sum{ii$upgrade_from(i,ii), valcap(ii,newv,r,t) }] =
        sum{ii$upgrade_to(i,ii), cost_vom(ii,newv,r,t) } ;

*=================
* --- Fixed OM ---
*=================

parameter cost_fom(i,v,r,t) "--2004$/MW-yr-- fixed OM" ;

*previous calculation (without tech binning)
cost_fom(i,v,r,t)$[(not Sw_binOM)$valcap(i,v,r,t)] = plant_char(i,v,t,'fom') ;

*if using binned costs, still need to assign default values to cost_fom for new plants
cost_fom(i,newv,r,t)$[(Sw_binOM)$valcap(i,newv,r,t)] = plant_char(i,newv,t,'fom') ;

cost_fom(i,initv,r,t)$[Sw_BinOM$valcap(i,initv,r,t)] = sum{allt$att(allt,t), hintage_data(i,initv,r,allt,"wFOM") } ;

*use default values if they are missing from the writehintage outputs
*but still active via valgen
cost_fom(i,initv,r,t)$[Sw_BinOM$(not cost_fom(i,initv,r,t))$valgen(i,initv,r,t)] =
                            plant_char(i,initv,'2010','fom') ;


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
  sum{tt$ivt(i,newv,tt), plant_char(i,newv,tt,'fom')  } / countnc(i,newv) ;


* -- FOM adjustments for nuclear plants
* Nuclear FOM cost adjustments are from the report from the IPM team titled
* 'Nuclear Power Plant Life Extension Cost Development Methodology' which indicates
* $1.25/kw increase per year for the first 10 years
* $1.81/kW increase per year for years 10-50
* $0.56/kW increase per year for year 50+
* A single step reduction of $25/kW in year 50
* These are applied in ReEDS relative to 2019 (i.e., cost escalations are applied beginnning in 2020)

parameter FOM_adj_nuclear(allt) "--$/MW-- Cumulative addition to nuclear FOM costs by year"
/
$offlisting
$ondelim
$include inputs_case%ds%nuke_fom_adj.csv
$offdelim
$onlisting
/
;

* -- FOM adjustments for coal plants
* The escalation factor is taken from NEMS and are roughly based on the report
* at https://www.eia.gov/analysis/studies/powerplants/generationcost/
parameter FOM_adj_coal(allt) "--$/MW-- Cumulative addition to coal FOM costs by year"
/
$offlisting
$ondelim
$include inputs_case%ds%coal_fom_adj.csv
$offdelim
$onlisting
/
;

*Input values are in 2017$, so convert to 2004$
FOM_adj_nuclear(allt) = deflator("2017") * FOM_adj_nuclear(allt) ;
FOM_adj_coal(allt) = deflator("2017") * FOM_adj_coal(allt) ;

cost_fom(i,initv,r,t)$[Sw_BinOM$valcap(i,initv,r,t)$nuclear(i)] =
  cost_fom(i,initv,r,t) + sum{allt$att(allt,t),FOM_adj_nuclear(allt)}$Sw_NukeCoalFOMAdj ;

cost_fom(i,initv,r,t)$[Sw_BinOM$valcap(i,initv,r,t)$coal(i)] =
  cost_fom(i,initv,r,t) + sum{allt$att(allt,t),FOM_adj_coal(allt)}$Sw_NukeCoalFOMAdj ;


*note conditional here that will only replace fom
*for hydro techs if it is included in hyd_fom(i,r)
cost_fom(i,v,r,t)$[valcap(i,v,r,t)$hydro(i)$hyd_fom(i,r)] = hyd_fom(i,r) ;

cost_fom(i,v,rb,t)$[valcap(i,v,rb,t)$geo(i)] = geo_fom(i,rb) ;

cost_fom(i,initv,r,t)$[(not Sw_BinOM)$valcap(i,initv,r,t)] = sum{tt$tfirst(tt), cost_fom(i,initv,r,tt) } ;
cost_fom(i,v,r,t)$[valcap(i,v,r,t)$dupv(i)] = sum{ii$dupv_upv_corr(ii,i), cost_fom(ii,v,r,t) } ;

*upgrade fom costs for initial classes are the fom costs for that tech
*plus the delta between upgrade_to and upgrade_from for the initial year
cost_fom(i,initv,r,t)$[upgrade(i)$Sw_Upgrades
                      $sum{ii$upgrade_from(i,ii), valcap(ii,initv,r,t) }] =
  sum{ii$upgrade_from(i,ii), cost_fom(ii,initv,r,t) }
  + sum{(ii,tt)$[upgrade_to(i,ii)$tfirst(tt)], plant_char(ii,initv,tt,"fom") }
  - sum{(ii,tt)$[upgrade_from(i,ii)$tfirst(tt)], plant_char(ii,initv,tt,"fom") } ;

*upgrade fom costs for new classes are the fom costs
*of the plant that it is being upgraded to
cost_fom(i,newv,r,t)$[upgrade(i)$Sw_Upgrades$valcap(i,newv,r,t)
                      $sum{ii$upgrade_from(i,ii), valcap(ii,newv,r,t) }] =
      sum{ii$upgrade_to(i,ii), cost_fom(ii,newv,r,t) } ;


*====================
* --- Heat Rates ---
*====================

parameter heat_rate(i,v,r,t) "--MMBtu/MWh-- heat rate" ;

heat_rate(i,v,r,t)$valcap(i,v,r,t) = plant_char(i,v,t,'heatrate') ;

heat_rate(i,newv,r,t)$[valcap(i,newv,r,t)$countnc(i,newv)] =
      sum{tt$ivt(i,newv,tt), plant_char(i,newv,tt,'heatrate') } / countnc(i,newv) ;

heat_rate(i,v,r,t)$[CONV(i) and initv(v) and capacity_exog(i,v,r,"sk",t) and rb(r)] = data_heat_rate_init(r,i) ;

* fill in heat rate for initial capacity that does not have a binned heatrate
heat_rate(i,initv,r,t)$[valcap(i,initv,r,t)$(not heat_rate(i,initv,r,t))] =  plant_char(i,initv,'2010','heatrate') ;

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

heat_rate_adj(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), heat_rate_adj(ii) } ;

heat_rate_adj(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), heat_Rate_adj(ii) } ;

*upgrade heat rates for initial classes are the heat rates for that tech
*plus the delta between upgrade_to and upgrade_from for the initial year
heat_rate(i,initv,r,t)$[upgrade(i)$Sw_Upgrades
                      $sum{ii$upgrade_from(i,ii), valcap(ii,initv,r,t) }] =
  sum{ii$upgrade_from(i,ii), heat_rate(ii,initv,r,t) }
  + sum{(ii,tt)$[upgrade_to(i,ii)$tfirst(tt)], plant_char(ii,initv,tt,"heatrate") }
  - sum{(ii,tt)$[upgrade_from(i,ii)$tfirst(tt)], plant_char(ii,initv,tt,"heatrate") } ;

*upgrade heat rates for new classes are the heat rates for
*the bintage and technology for what it is being upgraded to
heat_rate(i,newv,r,t)$[upgrade(i)$Sw_Upgrades$valcap(i,newv,r,t)
                      $sum{ii$upgrade_from(i,ii), valcap(ii,newv,r,t) }] =
        sum{ii$upgrade_to(i,ii), heat_rate(ii,newv,r,t) } ;


heat_rate(i,v,r,t)$heat_rate_adj(i) = heat_rate_adj(i) * heat_rate(i,v,r,t) ;


*=========================================
* --- Fuel Prices ---
*=========================================

parameter fuel_price(i,r,t) "$/MMbtu - fuel prices by technology" ;


*written by input_processing\fuelcostprep.py
table fprice(allt,r,f) "--2004$/MMBtu-- fuel prices by fuel type"
$offlisting
$ondelim
$include inputs_case%ds%fprice.csv
$offdelim
$onlisting
;

fuel_price(i,r,t)$[sum{f$fuel2tech(f,i),1}$rfeas(r)] =
  sum{(f,allt)$[fuel2tech(f,i)$(year(allt)=yeart(t))], fprice(allt,r,f) } ;

fuel_price(i,r,t)$[sum{f$fuel2tech(f,i),1}$(not fuel_price(i,r,t))$rfeas(r)] =
  sum{rr$[fuel_price(i,rr,t)$rfeas(rr)], fuel_price(i,rr,t) } / max(1,sum{rr$[fuel_price(i,rr,t)$rfeas(rr)], 1 }) ;

fuel_price(i,r,t)$[upgrade(i)$rfeas(r)] = sum{ii$upgrade_to(i,ii), fuel_price(ii,r,t) } ;

*==============================================
* --- Capacity Factors and Availability Rate---
*==============================================

parameter avail(i,v,h) "--fraction-- fraction of capacity available for generation by hour",
          cf_rsc(i,v,r,h) "--fraction-- capacity factor for rsc tech - t index included for use in CC/curt calculations" ;

parameter forced_outage(i) "--fraction-- forced outage rate"
/
$offlisting
$ondelim
$include inputs_case%ds%outage_forced.csv
$offdelim
$onlisting
/ ;


parameter planned_outage(i) "--fraction-- planned outage rate"
/
$offlisting
$ondelim
$include inputs_case%ds%outage_planned.csv
$offdelim
$onlisting
/ ;


forced_outage(i)$geo(i) = forced_outage("geothermal") ;
planned_outage(i)$geo(i) = planned_outage("geothermal") ;

planned_outage(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), planned_outage(ii) } ;

forced_outage(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), forced_outage(ii) } ;

avail(i,v,h) = 1 ;

* Assume no plant outages in the summer, adjust the planned outages to account for no planned outages in summer
avail(i,v,h)$[forced_outage(i) or planned_outage(i)] = (1 - forced_outage(i))
                              * (1 - planned_outage(i)$[not summerh(h)] * 365 / 273) ;

*Existing geothermal plants have a 75% availability rate based on historical capacity factors
avail(i,initv,h)$geo(i) = 0.75 ;

*upgrade plants assume the same availability of what theyre upgraded to
avail(i,v,h)$upgrade(i) = sum{ii$upgrade_to(i,ii), avail(ii,v,h) } ;

*begin capacity factor calculations

*created by /input_processing/R/cfgather.R
table cf_in(r,i,h) "capacity factors for renewable technologies - wind CFs get adjusted below"
$offlisting
$ondelim
$include inputs_case%ds%cfout.csv
$offdelim
$onlisting
;
cf_in(r,i,h)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), cf_in(r,ii,h) } ;

*initial assignment of capacity factors
*Note that DUPV does not face the same distribution losses as UPV
*The DUPV capacity factors have already been adjusted by (1.0 - distloss)
cf_rsc(i,v,r,h)$[cf_in(r,i,h)$cf_tech(i)$sum{t, valcap(i,v,r,t) }] = cf_in(r,i,h) ;

*created by /input_processing/writecapdat.py
parameter cf_hyd(i,szn,r) "hydro capacity factors by season"
/
$offlisting
$include inputs_case%ds%hydcf.txt
$onlisting
/ ;

*created by /input_processing/writecapdat.py
parameter cap_hyd_szn_adj(i,szn,r) "seasonal max capacity adjustment for dispatchable hydro"
/
$offlisting
$include inputs_case%ds%hydcfadj.txt
$onlisting
/ ;

*created by /input_processing/writecapdat.py
parameter cfhist_hyd(r,t,szn,i) "seasonal adjustment for capacity factors - same as hydhistcfadj from heritage"
/
$offlisting
$include inputs_case%ds%hydcfhist.txt
$onlisting
/ ;

* only need to compute this for rs==sk... otherwise gets yuge
* dispatchable hydro has a separate constraint for seasonal generation which uses cf_hyd
cf_rsc(i,v,r,h)$[hydro(i)$sum{t, valcap(i,v,r,t) }]  = sum{szn$h_szn(h,szn),cf_hyd(i,szn,r)} ;


table windcfin(t,i) "--unitless-- wind capacity factors by class"
$offlisting
$ondelim
$include inputs_case%ds%windcfout.csv
$offdelim
$onlisting
;

parameter pv_cf_improve(t) "--unitless-- PV capacity factor improvement"
/
$offlisting
$ondelim
$include inputs_case%ds%pv_cf_improve.csv
$offdelim
$onlisting
/
;

parameter cf_adj_t(i,v,t) "--unitless-- capacity factor adjustment over time for RSC technologies",
          cf_adj_hyd(r,i,h,t) "--unitless-- capacity factor adjustment over time for hydro technologies" ;

cf_adj_t(i,v,t)$[rsc_i(i) or hydro(i) or csp_nostorage(i)] = 1 ;

* All existing wind gets a 30% CF
cf_adj_t(i,initv,t)$wind(i) = 0.3 ;
cf_adj_t(i,newv,t)$[windcfin(t,i)$countnc(i,newv)] = sum{tt$ivt(i,newv,tt),windcfin(tt,i)} / countnc(i,newv) ;

cf_adj_t(i,newv,t)$[pv(i)$countnc(i,newv)] = sum{tt$ivt(i,newv,tt),pv_cf_improve(tt)} / countnc(i,newv) ;

*if not set, set it to one
cfhist_hyd(r,t,szn,i)$[(not cfhist_hyd(r,t,szn,i))$hydro(i)$valcap_irt(i,r,t)] = 1 ;
*odd, historical years are the average of the surrounding even years. We could add data for odd historical years if needed.
cfhist_hyd(r,t,szn,i)$[oddyears(t)$(yeart(t)<=2015)] = (cfhist_hyd(r,t-1,szn,i) + cfhist_hyd(r,t+1,szn,i)) / 2 ;
*adjustment is the corresponding seasonal historical value
cf_adj_hyd(r,i,h,t)$hydro(i) = sum{szn$h_szn(h,szn),cfhist_hyd(r,t,szn,i)} ;

cf_rsc(i,v,rb,h)$[rsc_i(i)$(sum{t,capacity_exog(i,v,rb,'sk',t)})] =
        cf_rsc(i,"init-1",rb,h) ;
cf_rsc(i,v,rs,h)$[(not sameas(rs,'sk'))$rsc_i(i)$(sum{(t,r)$r_rs(r,rs),capacity_exog(i,v,r,rs,t)})] =
        cf_rsc(i,"init-1",rs,h) ;

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
cf_rsc(i,v,r,h)$[cspns(i)$sum{t, valcap(i,v,r,t) }] = cf_cspns(h) * avail_cspns ;


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
  ramptime(ortype) "--minutes-- minutes for ramping limit constraint in operating reserves" /flex 60, reg 5, spin 10/,
  reserve_frac(i,ortype) "--fraction-- fraction of a technology's online capacity that can contribute to a reserve type" ;

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

ramprate(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), ramprate(ii) } ;

ramprate(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), ramprate(ii) } ;

* Do not allow the reserve fraction to exceed 100%, so use the minimum of 1 or the computed value.
* The reserve fraction does NOT apply to storage technologies, but storage can provide operating reserves.
reserve_frac(i,ortype) = min(1,ramprate(i) * ramptime(ortype)) ;

reserve_frac(i,ortype)$upgrade(i) = sum{ii$upgrade_to(i,ii), reserve_frac(ii,ortype) } ;

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

cost_opres(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_opres(ii) } ;

cost_opres(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), cost_opres(ii) } ;

Scalar mingen_firstyear "--integer-- first year for mingen considerations" /2020/ ;

parameter minloadfrac(r,i,h) "--fraction-- minimum loading fraction - final used in model",
          minloadfrac0(i) "--fraction-- initial minimum loading fraction"
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
minloadfrac(r,i,h)$upgrade(i) = sum{ii$upgrade_to(i,ii), minloadfrac(r,ii,h) } ;

minloadfrac(r,i,h)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), minloadfrac(r,ii,h) } ;

minloadfrac(r,i,h)$[not sum{(v,t), valcap(i,v,r,t) }] = 0 ;

*=========================================
*              --- Load ---
*=========================================

set h_szn_prm(h,szn) "hour to season linkage for nd_hydro in the planning reserve margin constraint"
/
h3.summ
h7.fall
h11.wint
h15.spri
/ ;

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

$ifthen.allyearload %GSw_EFS1_AllYearLoad% == 'default'
*Dividing by (1-distloss) converts end-use load to busbar load
load_exog(r,h,t) = load_2010(r,h) * sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t) } / (1.0 - distloss) ;
$else.allyearload
table load_allyear(r,h,t) "--MW-- 2010 to 2050 end use load by time slice for use with EFS profiles"
$offlisting
$ondelim
$include inputs_case%ds%load_all.csv
$offdelim
$onlisting
;
load_exog(r,h,t) = load_allyear(r,h,t)/ (1.0 - distloss) ;
$endif.allyearload

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

*-- EFS flexibility

table flex_frac_load(flex_type,r,h,t)
$offlisting
$ondelim
$include inputs_case%ds%flex_frac_all.csv
$offdelim
$onlisting
;

parameter flex_demand_frac(flex_type,r,h,t) "fraction of load able to be considered flexible";

* assign zero values to avoid unassigned parameter errors
flex_demand_frac(flex_type,r,h,t)$rfeas(r) = 0 ;
flex_demand_frac(flex_type,r,h,t)$[Sw_EFS_Flex$rfeas(r)] = flex_frac_load(flex_type,r,h,t) ;


parameter peak_static_frac(r,szn,t) "--fraction-- fraction of peak demand that is static" ;
peak_static_frac(r,szn,t) = 1 - sum{(flex_type,h)$h_szn_prm(h,szn), flex_demand_frac(flex_type,r,h,t)} ;

*static EV demand is added directly to load_exog
load_exog(r,h,t)$(Sw_EV) = load_exog(r,h,t) + ev_static_demand(r,h,t) ;

* load in odd years is the average between the two surrounding even years
load_exog(r,h,t)$[oddyears(t)$(not load_exog(r,h,t))] = (load_exog(r,h,t-1)+load_exog(r,h,t+1)) / 2 ;

*initial values are set here (after SwI_Load has been accounted for)
load_exog0(r,h,t) = load_exog(r,h,t) ;

parameter
load_exog_flex(flex_type,r,h,t)    "the amount of exogenous load that is flexibile"
load_exog_static(r,h,t)            "the amount of exogenous load that is static" ;
load_exog_flex(flex_type,r,h,t) = load_exog(r,h,t) * flex_demand_frac(flex_type,r,h,t) ;
load_exog_static(r,h,t) = load_exog(r,h,t) - sum{flex_type, load_exog_flex(flex_type,r,h,t)} ;



parameter
maxload_szn(r,h,t,szn)   "maximum load by season - used to determine hour with highest load within each szn",
mload_exog_szn(r,t,szn)  "maximum load by season - placeholder for calculation hour_szn_group",
load_exog_szn(r,h,t,szn) "maximum load by season - placeholder for calculation hour_szn_group" ;


load_exog_szn(r,h,t,szn)$[h_szn(h,szn)$rfeas(r)] = load_exog(r,h,t) ;
mload_exog_szn(r,t,szn)$rfeas(r) = smax(hh$[not sameas(hh,"h17")],load_exog_szn(r,hh,t,szn)) ;
maxload_szn(r,h,t,szn)$[(load_exog_szn(r,h,t,szn)=mload_exog_szn(r,t,szn))$rfeas(r)] = yes ;



*==============================
* --- Peak Load ---
*==============================

*written by input_processing\R\\writeload.R
table peakdem_2010(r,szn) "--MW-- end use peak demand in 2010 by season"
$offlisting
$ondelim
$include inputs_case%ds%peak_2010.csv
$offdelim
$onlisting
;

parameter peakdem_static_szn(r,szn,t) "--MW-- bus bar peak demand by season" ;

table peak_allyear(r,szn,t) "--MW-- 2010 to 2050 peak load by season for use with EFS profiles"
$offlisting
$ondelim
$include inputs_case%ds%peak_all.csv
$offdelim
$onlisting
;

$ifthen.allyearpeak %GSw_EFS1_AllYearLoad% == 'default'
*Dividing by (1-distloss) converts end-use load to busbar load
peakdem_static_szn(r,szn,t) = peakdem_2010(r,szn) * peak_static_frac(r,szn,t) * sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t) } / (1.0 - distloss) ;
$else.allyearpeak
peakdem_static_szn(r,szn,t) = peak_allyear(r,szn,t) * peak_static_frac(r,szn,t) / (1.0 - distloss) ;
$endif.allyearpeak

parameter peakdem_static_h(r,h,t) "--MW-- bus bar peak demand by time slice for use with EFS profiles" ;

table peak_allyear_static(r,h,t)
$offlisting
$ondelim
$include inputs_case%ds%h_peak_all.csv
$offdelim
$onlisting
;

$ifthen.allyearpeakstatic %GSw_EFS1_AllYearLoad% == 'default'
peakdem_static_h(r,h,t) = peak_allyear_static(r,h,'2010') * sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t) } * (1 - sum{flex_type, flex_demand_frac(flex_type,r,h,t)}) / (1.0 - distloss);
$else.allyearpeakstatic
peakdem_static_h(r,h,t) = peak_allyear_static(r,h,t) * (1 - sum{flex_type, flex_demand_frac(flex_type,r,h,t)}) / (1.0 - distloss) ;
$endif.allyearpeakstatic

*==============================
* --- Planning Reserve Margin ---
*==============================

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

prm(r,t) = sum{nercr_new$r_nercr_new(r,nercr_new), prm_nt(nercr_new,t) } ;

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

parameter cost_cap_fin_mult_no_credits(i,r,t) "final capital cost multiplier ITC/PTC/Depreciation (i.e. the actual expenditures) - used only in outputs"
/
$offlisting
$ondelim
$include inputs_case%ds%cap_cost_mult_for_ratebase.csv
$offdelim
$onlisting
/ ;

*Assign upgraded techs the same multipliers as the techs they are upgraded from
cost_cap_fin_mult(i,r,t)$[upgrade(i)$rfeas(r)] = sum{ii$upgrade_from(i,ii), cost_cap_fin_mult(ii,r,t) } ;
cost_cap_fin_mult_noITC(i,r,t)$[upgrade(i)$rfeas(r)] = sum{ii$upgrade_from(i,ii), cost_cap_fin_mult_noITC(ii,r,t) } ;

if(Sw_WaterMain=1,
cost_cap_fin_mult(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult(ii,r,t) } ;

cost_cap_fin_mult_noITC(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult_noITC(ii,r,t) } ;
) ;

parameter rsc_fin_mult(i,r,t) "capital cost multiplier for resource supply curve technologies that have their capital costs included in the supply curves" ;
parameter rsc_fin_mult_noITC(i,r,t) "capital cost multiplier excluding ITC for resource supply curve technologies that have their capital costs included in the supply curves" ;

* Start by setting all multipliers to 1
rsc_fin_mult(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;
rsc_fin_mult_noITC(i,r,t) = 1 ;

*Hydro, pumped-hydro, and geo have capital costs included in the supply curve, so change their multiplier to be the same as cost_cap_fin_mult
rsc_fin_mult(i,r,t)$geo(i) = cost_cap_fin_mult('geothermal',r,t) ;
rsc_fin_mult(i,r,t)$hydro(i) = cost_cap_fin_mult('hydro',r,t) ;
rsc_fin_mult('pumped-hydro',r,t) = cost_cap_fin_mult('pumped-hydro',r,t) ;
rsc_fin_mult_noITC(i,r,t)$geo(i) = cost_cap_fin_mult_noITC('geothermal',r,t) ;
rsc_fin_mult_noITC(i,r,t)$hydro(i) = cost_cap_fin_mult_noITC('hydro',r,t) ;
rsc_fin_mult_noITC('pumped-hydro',r,t) = cost_cap_fin_mult_noITC('pumped-hydro',r,t) ;

* Apply cost reduction multipliers
rsc_fin_mult(i,r,t)$geo(i) = rsc_fin_mult(i,r,t) * sum{geotech$i_geotech(i,geotech), geocapmult(t,geotech) } ;
rsc_fin_mult_noITC(i,r,t)$geo(i) = rsc_fin_mult_noITC(i,r,t) * sum{geotech$i_geotech(i,geotech), geocapmult(t,geotech) } ;
rsc_fin_mult(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult_noITC(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult(i,r,t)$[ofswind(i)] = rsc_fin_mult(i,r,t) * ofswind_rsc_mult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$[ofswind(i)] = rsc_fin_mult_noITC(i,r,t) * ofswind_rsc_mult(t,i) ;


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

emit_rate_fuel(i,e)$upgrade(i) = sum{ii$upgrade_to(i,ii), emit_rate_fuel(ii,e) } ;

emit_rate_fuel(i,e)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), emit_rate_fuel(ii,e) } ;

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
                (gasquant(cendiv,gb,t) + gassupply_tot(cendiv,t) - gassupply_ele(cendiv,t))
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

*Penalizing new gas built within cost recovery period of 20 years in Virginia
parameter ng_lifetime_cost_adjust(t) "--unitless-- cost adjustment for NG in Virginia because al NG techs must be retired by 2045"
/
$offlisting
$ondelim
$include inputs_case%ds%va_ng_crf_penalty.csv
$offdelim
$onlisting
/
;



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
parameter cd_beta0(cendiv) "--$/MMBtu per Quad-- reference census division beta levels electric sector"
/
$offlisting
$ondelim
$include inputs_case%ds%cd_beta0.csv
$offdelim
$onlisting
/
;

parameter cd_beta0_allsector(cendiv) "--$/MMBtu per Quad-- reference census division beta levels all sectors"
/
$offlisting
$ondelim
$include inputs_case%ds%cd_beta0_allsector.csv
$offdelim
$onlisting
/
;

$ifthen.gassector %GSw_GasSector% == 'energy_sector'

*beginning year value is zero (i.e., no elasticity)
cd_beta(cendiv,t)$[not tfirst(t)] = cd_beta0_allsector(cendiv) ;

*see documentation for how value is calculated
nat_beta(t)$(not tfirst(t)) = 0.1276 ;

$else.gassector

*beginning year value is zero (i.e., no elasticity)
cd_beta(cendiv,t)$[not tfirst(t)] = cd_beta0(cendiv) ;

*see documentation for how value is calculated
nat_beta(t)$(not tfirst(t)) = 0.1352 ;

$endif.gassector

*written by input_processing\fuelcostprep.py
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
storage_eff(i,t)$[storage(i)$plant_char0(i,t,'rte')] = plant_char0(i,t,'rte') ;

parameter storage_lifetime_cost_adjust(i) "--unitless-- cost adjustment for battery storage technologies because they do not have a 20-year life" ;

*The 1.21 value is the CRF_15 divided by CRF_20 to account for batteries only having a 15-year lifetime.
*It technically should change over time (if CRF changes over time), but is represented as a constant value here for simplicity
storage_lifetime_cost_adjust(i)$battery(i) = 1.21 ;

cost_cap(i,t)$storage_lifetime_cost_adjust(i) = cost_cap(i,t) * storage_lifetime_cost_adjust(i) ;

* Parameters for CSP-ws configurations: used in eq_rsc_INVlim
* csp: this include the SM for representative configurations, divided by the representative SM (2.4) for CSP supply curve;
* all other technologies are 1
parameter
  csp_sm(i) "--unitless-- solar multiple for configurations"
  resourcescaler(i) "--unitless-- resource scaler for rsc technologies"
;

csp_sm(i)$csp1(i) = 2.7 ;
csp_sm(i)$csp2(i) = 2.4 ;
csp_sm(i)$csp3(i) = 1.3 ;
csp_sm(i)$csp4(i) = 1.0 ;
csp_sm(i)$cspns(i) = 1.4 ;

resourcescaler(i)$[not CSP_Storage(i)] = 1 ;
resourcescaler(i)$csp(i) = CSP_SM(i) / 2.4 ;

parameter storage_duration(i)   "--hours-- storage duration"
/
$ondelim
$include inputs_case%ds%storage_duration.csv
$offdelim
/
;
storage_duration(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), storage_duration(ii) } ;

parameter cc_storage(i,sdbin)   "--fraction-- capacity credit of storage by duration"
          bin_duration(sdbin)   "--hours-- duration of each storage duration bin"
;

* set the duration of each storage duration bin
bin_duration(sdbin) = sdbin.val ;

* set the capacity credit of each storage technology for each storage duration bin.
* for example, 2-hour batteries get CC=1 for the 2-hour bin and CC=0.5 for the 4-hour bin
* likewise, 6-hour batteries get CC=1 for the 2-, 4-, and 6-hour bins, but only 0.75 for the 8-hour bin, etc.
cc_storage(i,sdbin)$[not csp(i)] = storage_duration(i) / bin_duration(sdbin) ;
cc_storage(i,sdbin)$(cc_storage(i,sdbin) > 1) = 1 ;
cc_storage(i,sdbin) = round(cc_storage(i,sdbin),3) ;
* this bin is included as a safety valve so that the model can build additional storage beyond what is
* available for diurnal peaking capacity
cc_storage(i,'8760') = 0 ;

parameter hourly_arbitrage_value(i,r,t) "--$/MW-yr-- hourly arbitrage value of energy storage"
          storage_in_min(r,h,t)         "--MW-- lower bound for STORAGE_IN"
;

hourly_arbitrage_value(i,r,t) = 0 ;
storage_in_min(r,h,t) = 0 ;

parameter minCF(i,t)     "--unitless-- minimum annual capacity factor"
          cf(i,v,r,t)    "--unitless-- implied capacity factor from the storage_in_min input" ;

* set the minimum capacity factor for gas-CTs and RE-CTs
* 1% for gas-CT is minimum gas-CT CF across the PLEXOS runs from the 2019 Standard Scenarios
* 6% for RE-CT is based on unpublished PLEXOS runs of 100% RE scenarios performed in summer 2019
minCF('gas-ct',t) = 0.01 ;
minCF('RE-CT',t) = 0.06 ;

minCF(i,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), minCF(ii,t) } ;

minCF(i,t)$[i_water_cooling(i)$Sw_WaterMain] =  sum{ii$ctt_i_ii(i,ii), minCF(ii,t) } ;


*fom costs are constant for pumped-hydro
cost_fom("pumped-hydro",v,r,t)$valcap("pumped-hydro",v,r,t) = 13030 ;


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
biopricemult(r,bioclass,t)$[not rfeas(r)] = 0 ;

biofeas(r)$sum{bioclass, biosupply(r,"cost",bioclass) } = yes ;

*removal of bio techs that are not in biofeas(r)
valcap(i,v,r,t)$[(cofire(i) or bio(i))$(not biofeas(r))] = no ;
valgen(i,v,r,t)$[(cofire(i) or bio(i))$(not biofeas(r))] = no ;
valinv(i,v,r,t)$[(cofire(i) or bio(i))$(not biofeas(r))] = no ;


*================================
* Capacity value and curtailment
*================================

parameters sdbin_size(ccreg,szn,sdbin,t)      "--MW-- available capacity by storage duration bin - used to bin the peaking power capacity contribution of storage by duration",
           sdbin_size_load(ccreg,szn,sdbin,t) "--MW-- bin_size loading in from the cc_out gdx file",
           curt_int(i,r,h,t)                  "--fraction-- average curtailment rate of all resources in a given year - only used in intertemporal solve",
           curt_excess(r,h,t)                 "--MW-- excess curtailment when assuming marginal curtailment in intertemporal solve",
           curt_marg(i,r,h,t)                 "--fraction-- marginal curtail rate for new resources - only used in sequential solve",
           cc_old(i,r,szn,t)                  "--MW-- capacity credit for existing capacity - used in sequential solve similar to heritage reeds",
           cc_old_load(i,r,szn,t)             "--MW-- cc_old loading in from the cc_out gdx file",
           cc_mar(i,r,szn,t)                  "--fraction--  cc_mar loading inititalized to some reasonable value for the 2010 solve",
           cc_int(i,v,r,szn,t)                "--fraction--  average fractional capacity credit - used in intertemporal solve",
           cc_excess(i,r,szn,t)               "--MW-- this is the excess capacity credit when assuming marginal capacity credit in intertemporal solve",
           cc_eqcf(i,v,r,t)                   "--fraction--  fractional capacity credit based off average capacity factors - used without iteration with cc and curt scripts",
           curt_mingen(r,h,t)                 "--fraction--  fraction of addition curtailment induced by increasing the minimum generation level (sequential only)",
           curt_mingen_int(r,h,t)             "--fraction--  fractional curtailment of mingen (intertemporal only)",
           curt_mingen_load(r,h,t)            "--fraction--  fraction of addition curtailment induced by increasing the minimum generation level, loaded from gdx file (so as to not overwrite existing values for non-modeled years)",
           curt_stor(i,v,r,h,src,t)           "--fraction--  fraction of curtailed energy that can be recovered by storage charging from a given source during that timeslice",
           curt_tran(r,rr,h,t)                "--fraction--  fraction of curtailed energy that can be reduced in r by building new transmission lines to rr",
           curt_reduct_tran_max(r,rr,h,t)     "--MW-- maximum amount of curtailment reduction that can occur in r from adding transmission to rr",
           curt_old(r,h,t)                    "--MW-- curtailment from old capacity - used to calculate average curtailment for VRE techs",
           vre_gen_last_year(r,h,t)           "--MW-- generation from VRE generators in the prior solve year",
           cap_fraction(i,v,r,t)              "--fraction--  fraction of capacity that was retired",
           mingen_postret(r,szn,t)            "--MWh-- minimum generation level from retirements" ;

cc_old(i,r,szn,t) = 0 ;
cc_int(i,v,r,szn,t) = 0 ;

cc_eqcf(i,v,rb,t)$[vre(i)$(sum{rscbin, rscfeas(rb,'sk',i,rscbin) })] =
  cf_adj_t(i,v,t) * sum{h,hours(h) * cf_rsc(i,v,rb,h)} / sum{h,hours(h)} ;
cc_eqcf(i,v,rs,t)$[(not sameas(rs,'sk'))$vre(i)$(sum{(rscbin,r)$r_rs(r,rs), rscfeas(r,rs,i,rscbin) })] =
  cf_adj_t(i,v,t) * sum{h,hours(h) * cf_rsc(i,v,rs,h)} / sum{h,hours(h)} ;
cc_mar(i,r,szn,t) = sum{v$ivt(i,v,t),cc_eqcf(i,v,r,t)} ;

cc_excess(i,r,szn,t) = 0 ;

*initialize curtailments at zero
curt_int(i,r,h,t) = 0 ;
curt_excess(r,h,t) = 0 ;
curt_old(r,h,t) = 0 ;
curt_marg(i,r,h,t) = 0 ;
curt_mingen(r,h,t) = 0 ;
curt_mingen_int(r,h,t) = 0 ;
curt_stor(i,v,r,h,src,t) = 0 ;
curt_tran(r,rr,h,t) = 0 ;
curt_reduct_tran_max(r,rr,h,t) = 0 ;

*initializing post retirement mingen to 0
cap_fraction(i,v,r,t) = 0;
mingen_postret(r,szn,t) = 0;

*initialize storage bin sizes
sdbin_size(ccreg,szn,sdbin,"2010") = 1000 ;

parameter cf_modeled(i,v,r,h,t) "--fraction-- final value of capacity factor used in the model" ;

* only wind has existing capacity and it is all in the same class
* this is because pv/csp all are forced to be built in the first period

cf_modeled(i,v,r,h,t)$[cf_tech(i)$valcap(i,v,r,t)] =
* note here that the CAP_FO_PO_HYD in heritage reeds treated seacapadj_hy as the capacity factor for
* dispatchable hydro and hydcfsn (which is adjusted by the historical factor)
* is used in Hyd_New_Dispatch_Gen and Hyd_Old_Dispatch_Gen
         (1$[not hydro(i)] + cf_adj_hyd(r,i,h,t)$hydro(i))
         * cf_rsc(i,v,r,h)
         * cf_adj_t(i,v,t)
         * avail(i,v,h)
;

parameter cost_curt(t) "--$/MWh-- price paid for curtailed VRE" ;

cost_curt(t)$[yeart(t)>=model_builds_start_yr] = Sw_CurtMarket ;



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

scalar emit_scale "scaling factor for emissions" /1e6/;

* set the carbon tax based on switch arguments
if(Sw_CarbTax = 1,
emit_tax("CO2",r,t) = co2_tax(t) * emit_scale;
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

*=========================================
* Reduced Resource Switch
*=========================================

parameter rsc_reduct_frac(pcat,r) "--unitless-- fraction of renewable resource that is reduced from the supply curve"
          prescrip_rsc_frac(pcat,r) "--unitless-- fraction of prescribed builds to the resource available"
;

rsc_reduct_frac(pcat,r) = 0 ;
prescrip_rsc_frac(pcat,r) = 0 ;

* if the Sw_ReducedResource is on, reduce the available resource by 25%
if (Sw_ReducedResource = 1,
*Calculate the fraction of prescribed builds to the available resource
  prescrip_rsc_frac(pcat,r)$[sum{(i,rscbin)$prescriptivelink(pcat,i), m_rsc_dat(r,i,rscbin,"cap") } > 0] =
      smax(t,m_required_prescriptions(pcat,r,t)) / sum{(i,rscbin)$prescriptivelink(pcat,i), m_rsc_dat(r,i,rscbin,"cap") } ;
*Set the default resource reduction fraction
  rsc_reduct_frac(pcat,r) = 0.25 ;
*If the resource reduction fraction will reduce the resource to the point that prescribed builds will be infeasible,
*then replace the resource reduction fraction with the maximum that the resource can be reduced to still have a feasible solution
  rsc_reduct_frac(pcat,r)$[prescrip_rsc_frac(pcat,r) > (1 - rsc_reduct_frac(pcat,r))] = 1 - prescrip_rsc_frac(pcat,r) ;

*In order to avoid small number issues, round down at the 3rd decimal place
*Because the floor function returns an integer, we multiply and divide by 1000 to get proper rounding
  rsc_reduct_frac(pcat,r) = rsc_reduct_frac(pcat,r) * 1000 ;
  rsc_reduct_frac(pcat,r) = floor(rsc_reduct_frac(pcat,r)) ;
  rsc_reduct_frac(pcat,r) = rsc_reduct_frac(pcat,r) / 1000 ;

*Now reduce the resource by the updated resource reduction fraction
  m_rsc_dat(r,i,rscbin,"cap")$rsc_i(i) = m_rsc_dat(r,i,rscbin,"cap") * (1 - sum{pcat$prescriptivelink(pcat,i), rsc_reduct_frac(pcat,r) }) ;
) ;


set m_rsc_con(r,i) "set to detect numeraire rsc techs that have capacity value" ;
m_rsc_con(r,i)$sum{rscbin, m_rsc_dat(r,i,rscbin,"cap") } = yes ;

  m_rscfeas(r,i,rscbin) = no ;
  m_rscfeas(r,i,rscbin)$m_rsc_dat(r,i,rscbin,"cap") = yes ;
  m_rscfeas(r,i,rscbin)$[sum{ii$tg_rsc_cspagg(ii, i),m_rscfeas(r,ii,rscbin)}] = yes ;
  m_rscfeas("sk",i,rscbin) = no ;


  m_cc_mar(i,r,szn,t) = cc_mar(i,r,szn,t) ;
*  m_cc_mar(i,rs,szn,t)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs), cc_mar(i,r,rs,szn,t) } ;

  m_cf(i,v,r,h,t)$(cf_tech(i)$valcap(i,v,r,t)) = cf_modeled(i,v,r,h,t) ;

  m_cf(i,newv,r,h,t)$[not sum{tt$(yeart(tt) <= yeart(t)), ivt(i,newv,tt )}$valcap(i,newv,r,t)] = 0 ;

* distpv capacity factor is divided by (1.0 - distloss) to provide a bus bar equivalent capacity factor
  m_cf("distpv",v,r,h,t)$valcap("distpv",v,r,t) = m_cf("distpv",v,r,h,t) / (1.0 - distloss) ;
  m_cf_szn(i,v,r,szn,t)$[cf_tech(i)$valcap(i,v,r,t)] = sum{h$h_szn(h,szn), hours(h) * m_cf(i,v,r,h,t) } / sum{h$h_szn(h,szn), hours(h) } ;



*can trim down these matrices fairly significantly...
peakdem_h17_ratio(r,szn,t)$load_exog(r,"h17",t) = peakdem_static_szn(r,szn,t) / load_exog_static(r,"h17",t) ;

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

force_pcat(pcat,t)$[sum{(ppcat,ii)$sameas(pcat,ii), prescriptivelink0(ppcat,ii) }] = no ;
