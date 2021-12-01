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
$eval numhintage 300
$endif.unithintage

*need to convert the 'group' numhintage to some large value
$ifthen.unithintage %numhintage%=="group"
$eval numhintage 300
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
Sw_AnnualCap               "Switch for the carbon cap constraint"                                 /%GSw_AnnualCap%/
Sw_AVG_iter                "Switch to select method for curt/CC calculations"                     /%GSw_AVG_iter%/
Sw_BankBorrowCap           "Switch for the carbon cap constraint with banking/borrowing"          /%GSw_BankBorrowCap%/
Sw_BatteryMandate          "Switch to enable battery capacity mandates"                           /%GSw_BatteryMandate%/
Sw_BECCS                   "Switch to bin historical plant VOM and FOM costs"                     /%GSw_BECCS%/
Sw_BinOM                   "Switch to bin historical plant VOM and FOM costs"                     /%GSw_BinOM%/
Sw_BioSupply               "Switch to change the total biomass supply (multiplier)"               /%GSw_BioSupply%/
Sw_BioTransportCost        "Switch to set price of biomass transport (input value in 2020$)"      /%GSw_BioTransportCost%/
Sw_Canada                  "Switch to control representation of trade with Canada"                /%GSw_Canada%/
Sw_CapTranMax              "--MW-- maximum transmission capacity along each BA-BA corridor"       /%GSw_CapTranMax%/
Sw_CarbTax                 "Switch to turn on/off a carbon tax"                                   /%GSw_CarbTax%/
Sw_CCS                     "Switch for allowing CCS (both existing and new)"                      /%GSw_CCS%/
Sw_CES                     "Switch to treat RPS as CES (nuclear allowed)"                         /%GSw_CES%/
Sw_CleanEnergy             "Switch to allow Nuclear and CCS to count as clean energy"             /%GSw_CleanEnergy%/
Sw_ClimateDemand           "Switch to turn on/off climate impacts on demand"                      /%GSw_ClimateDemand%/
Sw_ClimateHydro            "Switch to turn on/off climate impacts on hydropower"                  /%GSw_ClimateHydro%/
Sw_ClimateWater            "Switch to turn on/off climate impacts on cooling water"               /%GSw_ClimateWater%/
Sw_HourlyNumClusters       "Switch for defining the number of szns when Sw_Hourly == 1"           /%GSw_HourlyNumClusters%/
Sw_CO2_Storage             "Switch to track CO2 storage amounts/costs (input value in 2020$)"     /%GSw_CO2_Storage%/
Sw_CoalRetire              "Switch to retire coal plants early"                                   /%GSw_CoalRetire%/
Sw_CoolingTechMults        "Switch to enable cooling tech cost/performance multipliers"           /%GSw_CoolingTechMults%/
Sw_CSAPR                   "Switch to enable or disable the CSAPR-related constraints"            /%GSw_CSAPR%/
Sw_CSPRelLim               "Annual relative growth limit for CSP technologies"                    /%GSw_CSPRelLim%/
Sw_CurtFlow                "Switch to turn on curtailment trading between regions"                /%GSw_CurtFlow%/
Sw_CurtMarket              "Switch to specify price (in 2004$/MWh) for curtailed VRE"             /%GSw_CurtMarket%/
Sw_DAC                     "Switch to enable or disable direct air capture"                       /%GSw_DAC%/
Sw_DR                      "Switch to enable demand response investment as a generator"           /%GSw_DR%/
Sw_DRReserves              "Switch to allow DR to provide reserves"                               /%GSw_DRReserves%/
Sw_EFS_Flex                "Switch indicating if EFS flexibility is available"                    /%GSw_EFS_Flex%/
Sw_EV                      "Switch to include electric vehicle load"                              /%GSw_EV%/
Sw_Hourly                  "Enable hourly resolution switch"                                      /%GSw_Hourly%/
Sw_HourlyWrap              "Switch to have time loop infinitely within szn with Sw_Hourly"        /%GSw_HourlyWrap%/
Sw_Hourly_Midnight         "Switch to have ET midnight or local midnights"                        /%GSw_HourlyTZAdj_Midnight%/
Sw_ForcePrescription       "Switch enforcing near term limits on capacity builds"                 /%GSw_ForcePrescription%/
Sw_GasCurve                "Switch to have a national gas curve [0] or regional gas curves [1]"   /%GSw_GasCurve%/
Sw_GenMandate              "Switch for the national generation constraint"                        /%GSw_GenMandate%/
Sw_Geothermal              "Switch to remove [0], have default [1], or extended [1] geothermal"   /%GSw_Geothermal%/
Sw_GrowthAbsCon            "Switch for the absolute growth constraint"                            /%GSw_GrowthAbsCon%/
Sw_GrowthRelCon            "Switch for the relative growth constraint"                            /%GSw_GrowthRelCon%/
Sw_H2                      "Switch to control hydrogen representation, 1=national, 2=regional"    /%GSw_H2%/
Sw_H2_Start                "Switch to control the year when hydrogen constraints are enforced"    /%GSw_H2_Demand_Start%/
Sw_H2_Transport            "Switch to enable or disable hydrogen transport representation"        /%GSw_H2_Transport%/
Sw_H2_Transport_Cost       "$2016/tonne-MI costs for hydrogen transport pipeline"                 /%GSw_H2_Transport_Cost%/
Sw_H2_Transport_Uniform    "H2 national transport/storage costs (input value in 2020$)"           /%GSw_H2_Transport_Uniform%/
Sw_HydroCapEnerUpgradeType "Switch to couple (1) or decouple (2) hydro capacity/energy upgrades"  /%GSw_HydroCapEnerUpgradeType%/
Sw_IndividualSites         "Switch for individual wind sites (1=sites, 0=s regions)"              /%GSw_IndividualSites%/
Sw_IndividualSiteAgg       "Switch for aggregation level of individual site profiles"             /%GSw_IndividualSiteAgg%/
Sw_Int_CC                  "Switch for intertemporal CC (0=ave, 1=marg, 2=scaled marg)"           /%GSw_Int_CC%/
Sw_Int_Curt                "Switch for intertemporal Curt (0=ave, 1=marg, 2=scaled marg)"         /%GSw_Int_Curt%/
Sw_Loadpoint               "Switch to use a loadpoint for the intertemporal case"                 /%GSw_Loadpoint%/
Sw_MinCF                   "Switch for the minimum annual fleet capacity factor constraint"       /%GSw_MinCF%/
Sw_Mingen                  "Switch to include or remove MINGEN variable"                          /%GSw_Mingen%/
Sw_Minloading              "Switch to enable or disable the minloading constraint"                /%GSw_Minloading%/
Sw_NearTermLimits          "Switch enforcing near term limits on capacity builds"                 /%GSw_NearTermLimits%/
Sw_NukeCoalFOMAdj          "Switch to adjust nuclear and coal FOM costs similar to NEMS"          /%GSw_NukeCoalFOM%/
Sw_NukeFlex                "Switch to enable more flexible nuclear operations"                    /%GSw_NukeFlex%/
Sw_OpRes                   "Switch for the operating reserves constraints"                        /%GSw_OpRes%/
Sw_OpResTrade              "Switch for allowing operating reserves trade"                         /%GSw_OpResTrade%/
Sw_OpResTradeMult          "Multiplier on operating reserve flow for transmission"                /%GSw_OpResTradeMult%/
Sw_Prod                    "Scalar value for whether Sw_H2 or Sw_DAC are enabled, set below"      /0/
Sw_PVB                     "Switch to enable or disable hybrid PV+battery"                        /%GSw_PVB%/
Sw_ReducedResource         "Switch to reduce the amount of RE resource available"                 /%GSw_ReducedResource%/
Sw_Refurb                  "Switch allowing refurbishments"                                       /%GSw_Refurb%/
Sw_ReserveMargin           "Switch for the planning reserve margin constraints"                   /%GSw_ReserveMargin%/
Sw_ResReqMultiplier        "Multiplier on total reserve requirement"                              /%GSw_OpResReqMult%/
Sw_Retire                  "Switch allowing endogenous retirements"                               /%GSw_Retire%/
Sw_RGGI                    "Switch for the RGGI constraint"                                       /%GSw_RGGI%/
Sw_SolarRelLim             "Annual relative growth limit for UPV and DUPV technologies"           /%GSw_SolarRelLim%/
Sw_StateCap                "Switch for the state cap and trade constraint"                        /%GSw_StateCap%/
Sw_StateRPS                "Switch for the state RPS constraints"                                 /%GSw_StateRPS%/
Sw_OffshoreFrc             "Switch for offshore mandate. 1=combined fix+float, 2=separate"        /%GSw_OffshoreFrc%/
Sw_Storage                 "Switch for allowing storage (both existing and new)"                  /%GSw_Storage%/
Sw_Storage_in_Min          "Switch to require minimum charging amount as dictated by Augur"       /%GSw_Storage_in_Min%/
Sw_TranRestrict            "Switch for restricting transmission builds"                           /%GSw_TranRestrict%/
Sw_TransCostMult           "--fraction-- multiplier for bulk BA-BA transmission costs"            /%GSw_TransCostMult%/
Sw_TransMultiLink          "Switch for multi-link transmission"                                   /%GSw_TransMultiLink%/
Sw_VSC                     "Switch to turn on/off the multi-terminal VSC HVDC macrogrid"          /%GSw_VSC%/
Sw_Upgrades                "Switch to enable or disable upgrades - not to be used with water"     /%GSw_Upgrades%/
Sw_WaterCapacity           "Switch for the water capacity constraints"                            /%GSw_WaterCapacity%/
Sw_WaterMain               "Switch for the representation of water use and source types"          /%GSw_WaterMain%/
Sw_WaterUse                "Switch for the water capacity and water use constraints"              /%GSw_WaterUse%/
Sw_WindRelLim              "Annual relative growth limit for wind (ons and ofs) technologies"     /%GSw_WindRelLim%/
;

* need to specify all hours upfront to avoid naming conflicts
* with index 'h2' and hydrogen production subsets 'h2'
set allh "all potentially modeled hours" /h1*h8760/ ;

Sw_Prod$[Sw_H2 or Sw_DAC] = 1 ;

*year-related switches that define retirement and upgrade start dates
scalar retireyear  "first year to allow capacity to start retiring" /%GSw_Retireyear%/
       upgradeyear "first year to allow capacity to upgrade"        /%GSw_Upgradeyear%/
       climateyear "first year to apply climate impacts"            /%GSw_ClimateStartYear%/ ;


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
      beccs
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
*the RE-CC is a gas-CC that has been upgraded to an RE-CT. It is therefor a combustion turbine and not a combined cycle system.
      RE-CC
      geothermal
      Hydro
      lfill-gas
      MHKwave
      Nuclear
      Nuclear-SMR
      Ocean
      o-g-s
      other
      pumped-hydro
      pumped-hydro-flex
      unknown
      upv_1*upv_10,
      dupv_1*dupv_10,
      pvb1_1 * pvb1_10  "hybrid pv+battery config 1"
      pvb2_1 * pvb2_10  "hybrid pv+battery config 2"
      pvb3_1 * pvb3_10  "hybrid pv+battery config 3"
      wind-ofs_1*wind-ofs_15,
      wind-ons_1*wind-ons_10,
      csp1_1*csp1_12,
      csp2_1*csp2_12,
      csp3_1*csp3_12,
      csp4_1*csp4_12,
      dr1_1*dr1_20,
      dr2_1*dr2_20,
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
*consuming technologies
* electrolyzer == h2 production from electricity
      electrolyzer
* smr = steam methane reforming
      smr
      smr_ccs
* dac == direct air capture
      dac
*upgrade technologies
      Gas-CC_Gas-CC-CCS
      Gas-CT_RE-CT
      Gas-CC_RE-CC
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
      hydEND_hydED
      hydED_pumped-hydro
      hydED_pumped-hydro-flex
*water technologies
$ifthene.ctech %GSw_WaterMain% == 1
$include inputs_case%ds%i_coolingtech_watersource.csv
$include inputs_case%ds%i_coolingtech_watersource_upgrades.csv
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
    wind-ofs_15
    mhkwave
    caes
    other
    unknown
    hydro
    csp3_1*csp3_12
    csp4_1*csp4_12
    pvb2_1*pvb2_10
    pvb3_1*pvb3_10
    pumped-hydro-flex
    hydED_pumped-hydro-flex
$ifthene.hydup not %GSw_HydroCapEnerUpgradeType% == 1
    hydUD
    hydUND
$endif.hydup
$ifthene.hydup2 %GSw_HydroAddPumpDispUpgSwitch% == 0
    hydEND_hydED
    hydED_pumped-hydro
$endif.hydup2
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
    pvb2_1*pvb2_10
    pvb3_1*pvb3_10
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

*ban canadian imports as a technology if Sw_Canada is not equal to one
ban('can-imports')$[Sw_Canada <> 1] = yes ;

alias(i,ii,iii) ;

if(Sw_BECCS = 0,
ban('beccs') = yes ;
bannew('beccs') = yes ;
) ;


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
$include inputs_case%ds%i_coolingtech_watersource_upgrades_link.csv
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
bannew(i)$[sum{ctt$bannew_ctt(ctt), i_ctt(i,ctt) }] = YES ;

* ban new builds of Nuclear and coal-CCS with dry cooling techs as cooling requirements
* of nuclear and coal-CCS make dry cooling impractical
bannew(i)$[sum{ctt_i_ii(i,'Nuclear'), i_ctt(i,'d') }] = YES ;
bannew(i)$[sum{ctt_i_ii(i,'Nuclear-SMR'), i_ctt(i,'d') }] = YES ;
bannew(i)$[sum{ctt_i_ii(i,'coal-CCS'), i_ctt(i,'d') }] = YES ;

*ban and bannew all non-numeraire techs that are derived from ban numeraire techs
ban(i)$sum{ii$ban(ii), ctt_i_ii(i,ii) } = YES ;
bannew(i)$sum{ii$bannew(ii), ctt_i_ii(i,ii) } = YES ;

* ban new builds of water sources included in bannew_wst for all i
bannew(i)$[sum{wst$bannew_wst(wst), i_wst(i,wst) }] = YES ;
* end parentheses for Sw_WaterMain = 1
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
  bio(i)               "technologies that use biofuel"
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
  pvb(i)               "hybrid pv+battery technologies",
  pvb1(i)              "pvb generation technologies 1",
  pvb2(i)              "pvb generation technologies 2",
  pvb3(i)              "pvb generation technologies 3",
  csp(i)               "csp generation technologies",
  csp_nostorage(i)     "csp generation without storage",
  csp_storage(i)       "csp generation technologies with thermal storage",
  csp1(i)              "csp-tes generation technologies 1",
  csp2(i)              "csp-tes generation technologies 2",
  csp3(i)              "csp-tes generation technologies 3",
  csp4(i)              "csp-tes generation technologies 4",
  dr(i)                "demand response technologies",
  dr1(i)               "demand response storage technologies",
  dr2(i)               "demand response shed technologies"
  storage(i)           "storage technologies",
  storage_hybrid(i)    "hybrid VRE-storage technologies",
  storage_standalone(i) "stand alone storage technologies",
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
  hyd_add_pump(i)      "hydro techs with an added pump",
  nuclear(i)           "nuclear technologies"
  ogs(i)               "oil-gas-steam technologies"
  lfill(i)             "land-fill gas technologies"
  consume(i)           "technologies that consume electricity and add to load"
  h2(i)                "hydrogen-producing technologies"
  smr(i)               "steam methane reforming technologies"
  dac(i)               "direct air capture technologies"
  re_ct(i)             "re-ct and re-cc technologies"


i_subtech technology subset categories
   /
      BIO
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
      PVB
      PVB1
      PVB2
      PVB3
      CSP
      CSP_NOSTORAGE
      CSP_STORAGE
      CSP1
      CSP2
      CSP3
      CSP4
      DR
      DR1
      DR2
      STORAGE
      STORAGE_HYBRID
      STORAGE_STANDALONE
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
      OGS
      LFILL
      CONSUME
      h2
      SMR
      DAC
      RE_CT
   /,

allt "all potential years" /1900*2500/,
t(allt) "full set of years" /2010*%endyear%/,

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

sdbin "storage duration bins" /2,4,6,8,10,12,24,48,72,8760/
;

$ifthen.individualsites %GSw_IndividualSites% == 1
set r "regions"
/
$offlisting
$include inputs_case%ds%r.csv
$onlisting
/ ;
set rs(r) "renewable resource regions"
/
$offlisting
$include inputs_case%ds%rs.csv
$onlisting
/ ;
$else.individualsites
set r "regions" / p1*p205, s1*s454, sk / ,
    rs(r) "renewable resource regions" / s1*s454, sk / ;
$endif.individualsites

set ccreg "capacity credit regions"
/
$offlisting
$include inputs_case%ds%ccreg.csv
$onlisting
/ ;

set rb(r) "balancing regions" /p1*p205/,

*see end of file for expansion to 'h' set based on hourly setting
h(allh) "modeled ReEDS hours - starts as h1-h17 but adjusts based on hourly setting" /h1*h17/

h_heritage(allh) "traditionally-modeled 17 timeslices used in ReEDS - used in reporting" /h1*h17/

e "emission categories" /CO2, SO2, NOX, HG/,

summerh(allh) "summer hours" /h1,h2,h3,h4,h17/

*DAC == direct air capture
*H2 == hydrogen
* H2_Blue == H2 with associated emissions
* H2_green == H2 without associated emissions
p "products produced"  /DAC, H2_blue, H2_green/

h2_p(p) "hydrogen-related products" /H2_blue, H2_green/,

allszn "all potentially modeled seasons" /summ, fall, wint, spri, szn1*szn%GSw_HourlyNumClusters%/,

szn(allszn) "modeled ReEDS seasons" /summ, fall, wint, spri/,

h_szn(allh,allszn) "mapping of hour blocks to seasons"
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

rto_agg "Aggregated RTO regions (similar to rto but some regions combined)"
  /
  AZNM, BPA, CAISO, CAN, ERCOT,
  FRCC, ISO-NE, MEX, MISO, NYISO,
  NWPP, PJM, RMPP, SE, SPP, TVA, VACAR
  /,

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


* biomass supply curves defined by USDA region
usda_region "Biomass supply curve regions"
    / Appalachia, Corn-Belt, Delta-States, Lake-States, Mountain,
      Northeast, Pacific, Southeast, Southern-Plains, Northern-Plains, Other /,

tg "tech groups for growth constraints" /wind, solar, csp/,

tg_i(tg,i) "technologies that belong in tech group tg"
    /
    wind.(wind-ons_1*wind-ons_10),
    solar.(upv_1*upv_10, dupv_1*dupv_10, pvb1_1*pvb1_10, pvb2_1*pvb2_10, pvb3_1*pvb3_10)
    csp.(csp1_1*csp1_12, csp2_1*csp2_12, csp3_1*csp3_12, csp4_1*csp4_12)
    /

pcat "prescribed capacity categories"
    /
*seldom-used pound/hashtag populates
*elements of this set with the indicated set
#i
    upv,
    dupv,
    pvb,
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
/ pv "new storage charging from new pv curtailment",
  wind "new storage charging from new wind curtailment",
  old "new storage charging from old/existing VRE curtailment",
  other "storage charging from a source other than curtailment"
/ ;

hyd_add_pump('hydED_pumped-hydro') = yes ;
hyd_add_pump('hydED_pumped-hydro-flex') = yes ;

alias(r,rr,n,nn) ;
alias(rb,rb2) ;
alias(rto,rto2) ;
alias(rs,rss) ;
alias(allh,allhh) ;
alias(h,hh) ;
alias(szn,szn2) ;
alias(v,vv) ;
alias(t,tt,ttt) ;
alias(st,ast,aast) ;
alias(allt,alltt) ;
alias(cendiv,cendiv2) ;
alias(szn,szn2) ;

set r_rs(r,rs) "mapping set between BAs and renewable resource regions" ;
r_rs(r,rs) = no ;
set r_rs_input(r,rs)
/
$offlisting
$ondelim
$include inputs_case%ds%rsmap_filtered.csv
$offdelim
$onlisting
/ ;
r_rs(r,rs)$r_rs_input(r,rs) = yes ;


set nexth0(allh,allh) "order of hour blocks for h17 temporal resolution"
  /
    H1.H2, H2.H3, H3.H17, H4.H1,
    H5.H6, H6.H7, H7.H8, H8.H5,
    H9.H10, H10.H11, H11.H12, H12.H9,
    H13.H14, H14.H15, H15.H16, H16.H13, H17.H4
  /

    nexth(r,allh,allh) "order of hours blocks by region"

    nexthflex(allh,allh) "order of flexible hour blocks"
  /
    H1.H2, H2.H3, H3.H4, H3.H17, H4.H1,
    H5.H6, H6.H7, H7.H8, H8.H5,
    H9.H10, H10.H11, H11.H12, H12.H9,
    H13.H14, H14.H15, H15.H16, H16.H13, H17.H4
  /

   prevhflex(allh,allh) "reverse order of flexible hour blocks"
  /
    H2.H1, H3.H2, H4.H3, H4.H17, H1.H4,
    H6.H5, H7.H6, H8.H7, H5.H8,
    H10.H9, H11.H10, H12.H11, H9.H12,
    H14.H13, H15.H14, H16.H15, H13.H16, H17.H3
  /
;

*for h17 version, populate with default sequence of hours
nexth(r,h,hh)$nexth0(h,hh) = yes;

set adjhflex(allh,allh) "adjacent flexible hour blocks"
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
* declared over allt to allow for external data files that extend beyond end_year
set oddyears(allt) "odd number years of t"
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
$ifthen.ctech %GSw_WaterMain% == 1
$include inputs_case%ds%upgradelink_water.csv
$endif.ctech
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

* Declassify hydro pump upgrade techs from standalone storage subset
i_subsets(i,'STORAGE_STANDALONE')$hyd_add_pump(i) = NO ;

*approach in cooling water formulation is populating parameters of numeraire tech (e.g. gas-CC)
*for non-numeraire techs (e.g. gas-CC_r_fsa; r = recirculating cooling, fsa=fresh surface appropriated water source)
*e.g. populate i_subsets for non-numeraire techs from numeraire tech using a linking set ctt_i_ii(i,ii)
i_subsets(i,i_subtech)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), i_subsets(ii,i_subtech) } ;

* --- define technology subsets ---
BIO(i)$(not ban(i))                 = YES$i_subsets(i,'BIO') ;
COAL(i)$(not ban(i))                = YES$i_subsets(i,'COAL') ;
GAS(i)$(not ban(i))                 = YES$i_subsets(i,'GAS') ;
GAS_CT(i)$(not ban(i))              = YES$i_subsets(i,'GAS_CT') ;
GAS_CC(i)$(not ban(i))              = YES$i_subsets(i,'GAS_CC') ;
CONV(i)$(not ban(i))                = YES$i_subsets(i,'CONV') ;
CCS(i)$(not ban(i))                 = YES$i_subsets(i,'CCS') ;
RE(i)$(not ban(i))                  = YES$i_subsets(i,'RE') ;
VRE(i)$(not ban(i))                 = YES$i_subsets(i,'VRE') ;
RSC_i(i)$(not ban(i))               = YES$i_subsets(i,'RSC') ;
WIND(i)$(not ban(i))                = YES$i_subsets(i,'WIND') ;
OFSWIND(i)$(not ban(i))             = YES$i_subsets(i,'OFSWIND') ;
ONSWIND(i)$(not ban(i))             = YES$i_subsets(i,'ONSWIND') ;
UPV(i)$(not ban(i))                 = YES$i_subsets(i,'UPV') ;
DUPV(i)$(not ban(i))                = YES$i_subsets(i,'DUPV') ;
DISTPV(i)$(not ban(i))              = YES$i_subsets(i,'DISTPV') ;
PV(i)$(not ban(i))                  = YES$i_subsets(i,'PV') ;
PVB(i)$(not ban(i))                 = YES$i_subsets(i,'PVB') ;
PVB1(i)$(not ban(i))                = YES$i_subsets(i,'PVB1') ;
PVB2(i)$(not ban(i))                = YES$i_subsets(i,'PVB2') ;
PVB3(i)$(not ban(i))                = YES$i_subsets(i,'PVB3') ;
CSP(i)$(not ban(i))                 = YES$i_subsets(i,'CSP') ;
CSP_NOSTORAGE(i)$(not ban(i))       = YES$i_subsets(i,'CSP_NOSTORAGE') ;
CSP1(i)$(not ban(i))                = YES$i_subsets(i,'CSP1') ;
CSP2(i)$(not ban(i))                = YES$i_subsets(i,'CSP2') ;
CSP3(i)$(not ban(i))                = YES$i_subsets(i,'CSP3') ;
CSP4(i)$(not ban(i))                = YES$i_subsets(i,'CSP4') ;
DR(i)$(not ban(i))                  = YES$i_subsets(i,'DR') ;
DR1(i)$(not ban(i))                 = YES$i_subsets(i,'DR1') ;
DR2(i)$(not ban(i))                 = YES$i_subsets(i,'DR2') ;
STORAGE(i)$(not ban(i))             = YES$i_subsets(i,'STORAGE') ;
STORAGE_HYBRID(i)$(not ban(i))      = YES$i_subsets(i,'STORAGE_HYBRID') ;
STORAGE_STANDALONE(i)$(not ban(i))  = YES$i_subsets(i,'STORAGE_STANDALONE') ;
THERMAL_STORAGE(i)$(not ban(i))     = YES$i_subsets(i,'THERMAL_STORAGE') ;
BATTERY(i)$(not ban(i))             = YES$i_subsets(i,'BATTERY') ;
COFIRE(i)$(not ban(i))              = YES$i_subsets(i,'COFIRE') ;
HYDRO(i)$(not ban(i))               = YES$i_subsets(i,'HYDRO') ;
HYDRO_D(i)$(not ban(i))             = YES$i_subsets(i,'HYDRO_D') ;
HYDRO_ND(i)$(not ban(i))            = YES$i_subsets(i,'HYDRO_ND') ;
PSH(i)$(not ban(i))                 = YES$i_subsets(i,'PSH') ;
GEO(i)$(not ban(i))                 = YES$i_subsets(i,'GEO') ;
GEO_BASE(i)$(not ban(i))            = YES$i_subsets(i,'GEO_BASE') ;
GEO_EXTRA(i)$(not ban(i))           = YES$i_subsets(i,'GEO_EXTRA') ;
GEO_UNDISC(i)$(not ban(i))          = YES$i_subsets(i,'GEO_UNDISC') ;
CANADA(i)$(not ban(i))              = YES$i_subsets(i,'CANADA') ;
VRE_NO_CSP(i)$(not ban(i))          = YES$i_subsets(i,'VRE_NO_CSP') ;
VRE_UTILITY(i)$(not ban(i))         = YES$i_subsets(i,'VRE_UTILITY') ;
VRE_DISTRIBUTED(i)$(not ban(i))     = YES$i_subsets(i,'VRE_DISTRIBUTED') ;
NUCLEAR(i)$(not ban(i))             = YES$i_subsets(i,'NUCLEAR') ;
OGS(i)$(not ban(i))                 = YES$i_subsets(i,'OGS') ;
LFILL(i)$(not ban(i))               = YES$i_subsets(i,'LFILL') ;
CONSUME(i)$(not ban(i))             = YES$i_subsets(i,'CONSUME') ;
H2(i)$(not ban(i))                  = YES$i_subsets(i,'H2') ;
SMR(i)$(not ban(i))                 = YES$i_subsets(i,'SMR') ;
DAC(i)$(not ban(i))                 = YES$i_subsets(i,'DAC') ;
CSP_STORAGE(i)$(not ban(i))         = YES$i_subsets(i,'CSP_STORAGE') ;
RE_CT(i)$(not ban(i))               = YES$i_subsets(i,'RE_CT') ;

*Hybrid pv+battery (PVB) configurations are defined by:
*  (1) inverter loading ratio (DC/AC) and
*  (2) battery capacity ratio (Battery/PV Array)
*Each configuration has ten resource classes
*The PV portion refers to "UPV", but not "DUPV"
*The battery portion refers to "battery_X", where X is the duration
set pvb_config "set of hybrid pv+battery configurations" / pvb1, pvb2, pvb3 / ;

set pvb_agg(pvb_config,i) "crosswalk between hybrid pv+battery configurations and technology options"
/
pvb1.(pvb1_1, pvb1_2, pvb1_3, pvb1_4, pvb1_5, pvb1_6, pvb1_7, pvb1_8, pvb1_9, pvb1_10)
pvb2.(pvb2_1, pvb2_2, pvb2_3, pvb2_4, pvb2_5, pvb2_6, pvb2_7, pvb2_8, pvb2_9, pvb2_10)
pvb3.(pvb3_1, pvb3_2, pvb3_3, pvb3_4, pvb3_5, pvb3_6, pvb3_7, pvb3_8, pvb3_9, pvb3_10)
/ ;

*ban techs in hybrid PV+battery if the switch calls for it
if(Sw_PVB=0,
  ban(i)$pvb(i) = yes ;
  bannew(i)$pvb(i) = yes ;
) ;

set i_src(i,src) "linking set between generating technolgy i and src" ;
i_src(i,"pv")$pv(i) = yes ;
i_src(i,"pv")$pvb(i) = yes ;
i_src(i,"wind")$wind(i) = yes ;

*add non-numeraire CSPs in index i of already defined set tg_i(tg,i)
tg_i("csp",i)$[(csp1(i) or csp2(i) or csp3(i) or csp4(i))$Sw_WaterMain] = yes ;

*Offhsore wind turbine types
set ofstype "offshore types used in offshore requirement constraint (eq_RPS_OFSWind)" / ofs_fix, ofs_float, ofs_all / ;
set ofstype_i(ofstype,i) "crosswalk between ofstype and i"
/
ofs_all.(wind-ofs_1*wind-ofs_15)
ofs_fix.(wind-ofs_1*wind-ofs_7)
ofs_float.(wind-ofs_8*wind-ofs_15)
/ ;

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
    noret_upgrade_tech(i) "upgrade techs that do not retire",
    retiretech(i,v,r,t) "combinations of i,v,r,t that can be retired",
    refurbtech(i) "technologies that can be refurbished",
    sccapcosttech(i) "technologies that have their capital costs embedded in supply curves",
    inv_cond(i,v,r,t,tt) "allows an investment in tech i of class v to be built in region r in year tt and usable in year t" ;

noret_upgrade_tech(i)$hyd_add_pump(i) = yes ;
dispatchtech(i)$[not(vre(i) or hydro_nd(i))] = yes ;
sccapcosttech(i)$[geo(i) or hydro(i) or psh(i)] = yes ;

*pv/wind/csp/hydro/pvb techs have capacity factors based on resouce assessments
cf_tech(i)$[pv(i) or wind(i) or csp(i) or hydro(i) or pvb(i)] = yes ;

*initialize sets to "no"
retiretech(i,v,r,t) = no ;
inv_cond(i,v,r,t,tt) = no ;

* src_curt is defined below after all necessary set definitions
parameter src_curt(i,src) "sources of storage charging for curtailment recovery" ;
*standalone storage can recover curtailment from any source but "other"
src_curt(i,src)$[(storage_standalone(i) or hyd_add_pump(i))$(not sameas(src,"other"))] = 1 ;
*pvb can recover curtailment from "old" VRE and new pv only
src_curt(i,src)$[pvb(i)$(sameas(src,"pv") or sameas(src,"old"))] = 1 ;
*DR shift can recover curtailment from any source but "other"
src_curt(i,src)$[dr1(i)$(not sameas(src,"other"))] = 1 ;

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


set prescriptivelink0(pcat,ii) "initial set of prescribed categories and their technologies - used in assigning prescribed builds"
/
  upv.(upv_1*upv_10)
  dupv.(dupv_1*dupv_10)
  pvb.(pvb1_1*pvb1_10,pvb2_1*pvb2_10,pvb3_1*pvb3_10)
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

$ontext
Replicating the construct for CSP to link Hybrid PV+battery and UPV for the resoruce supply curve constraints
  eq_rsc_invlim(i,bin).. sum{ii$rsc_agg(i,ii), INV_RSC(i,bin) } <= bin_capacity(i,bin) ;
  When i = "upv_1", this constraint looks like:
  eq_rsc_invlim("upv_1",bin).. INV_RSC("pvb1_1") + INV_RSC("upv_1") <= bin_capacity("upv_1",bin)
  Because the first index of rsc_agg is only a UPV technology the above constraint will never be generated when "i" is a pvb(i).
$offtext

set tg_rsc_upvagg(i,ii) "pv and pvb technologies that belong to the same class"
/
upv_1.(upv_1, pvb1_1, pvb2_1, pvb3_1),
upv_2.(upv_2, pvb1_2, pvb2_2, pvb3_2),
upv_3.(upv_3, pvb1_3, pvb2_3, pvb3_3),
upv_4.(upv_4, pvb1_4, pvb2_4, pvb3_4),
upv_5.(upv_5, pvb1_5, pvb2_5, pvb3_5),
upv_6.(upv_6, pvb1_6, pvb2_6, pvb3_6),
upv_7.(upv_7, pvb1_7, pvb2_7, pvb3_7),
upv_8.(upv_8, pvb1_8, pvb2_8, pvb3_8),
upv_9.(upv_9, pvb1_9, pvb2_9, pvb3_9),
upv_10.(upv_10, pvb1_10, pvb2_10, pvb3_10)
/
;

*initialize rsc aggregation set for 'i'='ii'
*rsc_agg(i,ii)$[sameas(i,ii)$(not csp(i))$(not csp(ii))$rsc_i(i)$rsc_i(ii)] = yes ;
rsc_agg(i,ii)$[sameas(i,ii)$rsc_i(i)$rsc_i(ii)] = yes ;
*add csp to rsc aggregation set
rsc_agg(i,ii)$tg_rsc_cspagg(i,ii) = yes ;
*add upv to rsc aggregation set
rsc_agg(i,ii)$tg_rsc_upvagg(i,ii) = yes ;
*Pumped hydro flex also uses the base pumped hydro supply curve
rsc_agg('pumped-hydro','pumped-hydro-flex') = yes ;
rsc_agg('pumped-hydro-flex','pumped-hydro-flex') = no ;

*ban techs in re_ct and re_cc if the switch calls for it
$ifthene.banrect %GSw_BanRECT%
bannew(i)$re_ct(i) = yes ;
$endif.banrect

*============================
* -- Flexible hours setup --
*============================

set flex_type "set of demand flexibility types: daily, previous, next, adjacent"
  /
  previous, next, adjacent, daily
  /
  ;

set flex_h_corr1(flex_type,allh,allh) "correlation set for hours referenced in flexibility constraints",
    flex_h_corr2(flex_type,allh,allh) "correlation set for hours referenced in flexibility constraints";

flex_h_corr1("previous",h,hh) = prevhflex(h,hh) ;
flex_h_corr1("next",h,hh) = nexthflex(h,hh) ;
flex_h_corr1("adjacent",h,hh) = adjhflex(h,hh) ;

flex_h_corr2("previous",h,hh) = nexthflex(h,hh) ;
flex_h_corr2("next",h,hh) = prevhflex(h,hh) ;
flex_h_corr2("adjacent",h,hh) = adjhflex(h,hh) ;


parameter allowed_shifts(i,allh,allhh) "how much load each dr type is allowed to shift into h from hh" 
  /
$ondelim
$include inputs_case%ds%dr_shifts.csv
$offdelim
  / ;


parameter allowed_shed(i) "how many hours each dr type is allowed to shed load" 
  /
$ondelim
$include inputs_case%ds%dr_shed.csv
$offdelim
  / ;


*======================================
*     --- Begin hierarchy ---
*======================================

set hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region) "hierarchy of various regional definitions"
/
$offlisting
$ondelim
$include inputs_case%ds%hierarchy.csv
$offdelim
$onlisting
/ ;


* Mappings between r and other region sets
set r_nercr(r,nercr),
    r_nercr_new(r,nercr_new),
    r_rto(r,rto),
    r_rto_agg(r,rto_agg),
    r_cendiv(r,cendiv),
    r_st(r,st),
    r_interconnect(r,interconnect),
    r_country(r,country),
    rr_country(r,country),
    r_customreg(r,customreg)
    r_ccreg(r,ccreg)
    rs_ccreg(rs,ccreg)
    r_usda(r,usda_region)
    ;

r_nercr(r,nercr)$sum{(nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_nercr_new(r,nercr_new)$sum{(nercr,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_rto(r,rto)$sum{(nercr,nercr_new,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_rto_agg(r,rto_agg)$sum{(nercr,nercr_new,rto,cendiv,st,interconnect,country,customreg,ccreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_cendiv(r,cendiv)$sum{(nercr,nercr_new,rto,rto_agg,st,interconnect,country,customreg,ccreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_st(r,st)$sum{(nercr,nercr_new,rto,rto_agg,cendiv,interconnect,country,customreg,ccreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_interconnect(r,interconnect)$sum{(nercr,nercr_new,rto,rto_agg,cendiv,st,country,customreg,ccreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_country(r,country)$sum{(nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,customreg,ccreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_customreg(r,customreg)$sum{(nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,ccreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_ccreg(r,ccreg)$sum{(nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,usda_region)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;
r_usda(r,usda_region)$sum{(nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg)$hierarchy(r,nercr,nercr_new,rto,rto_agg,cendiv,st,interconnect,country,customreg,ccreg,usda_region),1} = yes ;

*rr_country is a mapping from all r (whether BA or resource region) to country
rr_country(r,country) = r_country(r,country) ;
rr_country(rs,country)$sum{r$[r_country(r,country)$r_rs(r,rs)], 1} = yes ;
rs_ccreg(rs,ccreg)$sum{rb$[r_rs(rb,rs)$r_ccreg(rb,ccreg)], 1} = yes ;

parameter num_interconnect(interconnect) "interconnection numbers"
 /western 1, eastern 2, texas 3, quebec 4, mexico 5/ ;


*======================================
* ---------- Bintage Mapping ----------
*======================================
*following set is un-assumingly important
*it allows for the investment of bintage 'v' at time 't'

*table ivtmap(i,t)
* declared over allt to allow for external data files that extend beyond end_year
table ivt_num(i,allt) "number associated with bin for ivt calculation"
$offlisting
$ondelim
$include inputs_case%ds%ivt.csv
$offdelim
$onlisting
;


set ivt(i,v,t) "mapping set between i v and t - for new technologies" ;
ivt(i,newv,t)$[ord(newv) = ivt_num(i,t)] = yes ;

ivt(i,v,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), ivt(ii,v,t) } ;

*important assumption here that upgrade technologies
*receive the same binning assumptions as the technologies
*that they are upgraded to - this allows for easier translation
*and mapping of plant characteristics (cost_vom, cost_fom, heat_rate)
ivt(i,newv,t)$[(yeart(t)>=upgradeyear)$upgrade(i)] = sum{ii$upgrade_to(i,ii), ivt(ii,newv,t) } ;


parameter countnc(i,newv) "number of years in each newv set" ;

*add 1 for each t item in the ct_corr set
countnc(i,newv) = sum{t$ivt(i,newv,t),1} ;

*=====================================
*--- basic parameter declarations ---
*=====================================

*##
parameter hours(allh) "--hours-- number of hours in each time block"
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
          ptc_country(i,v,country,t) "--$/MWh-- minimum of ptc_unit_value in country",
          pvf_onm_undisc(t) "--unitless-- undiscounted present value factor of operations and maintenance costs"
;

ptc_country(i,v,country,t)$sum{r$[rr_country(r,country)$ptc_unit_value(i,v,r,t)], 1 } =
                           sum{r$[rr_country(r,country)$ptc_unit_value(i,v,r,t)], ptc_unit_value(i,v,r,t) } /
                           sum{r$[rr_country(r,country)$ptc_unit_value(i,v,r,t)], 1 }
;

* pvf_onm_undisc is based on intertemporal pvf_onm and pvf_capital,
* and is used for bulk system cost outputs
pvf_onm_undisc(t)$pvf_capital(t) = pvf_onm(t) / pvf_capital(t) ;
INr(r) = sum{interconnect$r_interconnect(r,interconnect), num_interconnect(interconnect) } ;



*==========================================
*     --- Canadian Imports/Exports ---
*==========================================

* declared over allt to allow for external data files that extend beyond end_year
table can_imports(r,allt) "--MWh-- Imports from Canada by year"
$offlisting
$ondelim
$include inputs_case%ds%can_imports.csv
$offdelim
$onlisting
;

table can_exports(r,allt) "--MWh-- Exports to Canada by year"
$offlisting
$ondelim
$include inputs_case%ds%can_exports.csv
$offdelim
$onlisting
;

parameter can_imports_szn_frac(allszn) "--unitless-- fraction of annual imports that occur in each season"
/
$offlisting
$ondelim
$include inputs_case%ds%can_imports_szn_frac.csv
$offdelim
$onlisting
/
;

parameter can_exports_h_frac(allh) "--unitless-- fraction of annual exports that occur in each timeslice"
/
$offlisting
$ondelim
$include inputs_case%ds%can_exports_h_frac.csv
$offdelim
$onlisting
/
;

parameter net_trade_can(r,allh,allt) "--MWh-- static net trade with Canada"
/
$offlisting
$offdigit
$ondelim
$include inputs_case%ds%net_trade_can_h17.csv
$offdelim
$ondigit
$onlisting
/
;

*net trade is initially computed as the sum over all hours to
*avoid loading in the hardcoded hours parameter
net_trade_can(r,h,t) = net_trade_can(r,h,t) / hours(h) ;


parameter can_imports_szn(r,allszn,t) "--MWh-- Seasonal imports from Canada by year",
          can_exports_h(r,allh,t)     "--MW-- Timeslice exports to Canada by year" ;

can_imports_szn(r,szn,t) = can_imports(r,t) * can_imports_szn_frac(szn) ;
can_exports_h(r,h,t) = can_exports(r,t) * can_exports_h_frac(h) / hours(h) ;

* Note that some techs have a dummy firstyear of 2500
parameter firstyear(i) "first year where new investment is allowed"
/
$offlisting
$ondelim
$include inputs_case%ds%firstyear.csv
$offdelim
$onlisting
/ ;

scalar model_builds_start_yr "--integer-- Start year allowing new generators to be built" ;

*Ignore gas units because gas-ct's are allowed in historical years
model_builds_start_yr = smin{i$[(not gas_ct(i))$(not distpv(i))$(not upgrade(i))$(not ban(i))$firstyear(i)], firstyear(i) } ;

firstyear(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), firstyear(ii) } ;

firstyear(i)$[not firstyear(i)] = model_builds_start_yr ;
firstyear(i)$[i_water_cooling(i)$(not Sw_WaterMain)] = NO ;
firstyear(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), firstyear(ii) } ;

parameter firstyear_pcat(pcat) ;
firstyear_pcat(pcat)$[sum{i$[sameas(i,pcat)$(not ban(i))], firstyear(i) }] = sum{i$sameas(i,pcat), firstyear(i) } ;
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
    tpast(allt)  "years that have passed in real life (2010-2018)" /2010*2018/,
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

* declared over allt to allow for external data files that extend beyond end_year
set tmodel_new(allt) "years to run the model"
/
$offlisting
$include inputs_case%ds%%yearset%
$onlisting
/ ;

tmodel_new(allt)$[year(allt) > %endyear%]= no ;

*reset the first and last year indices of the model
tfirst(t)$[ord(t) = smin{tt$tmodel_new(tt), ord(tt) }] = yes ;
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
valid_regions_list(rs)$sum(rb$valid_regions_list(rb), r_rs(rb,rs)) = yes ;
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
table caprsc(pcat,r,*) "--MW-- raw RSC capacity data, created by .\writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%allout_RSC.csv
$offdelim
$onlisting
;

*created by /input_processing/writecapdat.py
* declared over allt to allow for external data files that extend beyond end_year
table prescribednonrsc(allt,pcat,r,*) "--MW-- raw prescribed capacity data for non-RSC tech created by writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_nonRSC.csv
$offdelim
$onlisting
;

*Created using input_processing\writecapdat.py
table prescribedrsc(allt,pcat,r,*) "--MW-- raw prescribed capacity data for RSC tech created by .\input_processing\writecapdat.py"
$offlisting
$ondelim
$include inputs_case%ds%prescribed_rsc.csv
$offdelim
$onlisting
;

*For onshore and offshore wind, use outputs of hourlize to override what is in prescribedrsc
table prescribed_wind_ons(rs,allt,*) "--MW-- prescribed wind capacity, created by hourlize"
$offlisting
$ondelim
$include inputs_case%ds%wind-ons_prescribed_builds.csv
$offdelim
$onlisting
;
prescribedrsc(allt,"wind-ons",rs,"value") = prescribed_wind_ons(rs,allt,"capacity") ;

table prescribed_wind_ofs(rs,allt,*) "--MW-- prescribed wind capacity, created by hourlize"
$offlisting
$ondelim
$include inputs_case%ds%wind-ofs_prescribed_builds.csv
$offdelim
$onlisting
;
prescribedrsc(allt,"wind-ofs",rs,"value") = prescribed_wind_ofs(rs,allt,"capacity") ;

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
     prescribedretirements(allt,r,i,"value")$coal(i) =
        prescribedretirements_copy(allt+10,r,i,"value")$(allt.val >= 2030-10)
        + prescribedretirements(allt,r,i,"value") ;
) ;

*If coal retirement switch is 2, extend coal lifetimes by 10 years if the plant retires in 2022 or later
if(Sw_CoalRetire = 2,
     prescribedretirements(allt,r,i,"value")$[coal(i)$(allt.val >= 2022)] = 0 ;
     prescribedretirements(allt,r,i,"value")$[coal(i)$(allt.val >= 2022)] =
        prescribedretirements_copy(allt-10,r,i,"value")$(allt.val >= 2022+10) ;
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
forced_retirements(i,r,t)$[(yeart(t) >= forced_retire_input(i,r))$forced_retire_input(i,r)] =
      sum{(tt,pcat)$[(yeart(tt)<yeart(t))$prescriptivelink(pcat,i)], prescribednonrsc(tt,pcat,r,"value") } ;


$ifthen.unit %unitdata%=='ABB'
*created by /input_processing/writecapdat.py
* declared over allt to allow for external data files that extend beyond end_year
table windretirements(i,v,rs,allt) "--MW-- raw prescribed capacity retirement data for non-RSC tech"
$offlisting
$ondelim
$include inputs_case%ds%wind_retirements.csv
$offdelim
$onlisting
;
$endif.unit

table hintage_data(i,v,r,allt,*) "table of existing unit characteristics written by writehintage.py"
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

parameter maxage(i) "--years-- maximum age for technologies"
/
$offlisting
$ondelim
$include inputs_case%ds%maxage.csv
$offdelim
$onlisting
/ ;
* generators not included in maxage.csv get maxage=100 years
maxage(i)$[not maxage(i)] = 100 ;
* upgrades and cooling-water techs inherit maxage from the base tech
maxage(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), maxage(ii) } ;
maxage(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), maxage(ii) } ;

*loading in capacity mandates here to avoid conflicts in calculation of valcap
* declared over allt to allow for external data files that extend beyond end_year
parameter batterymandate(r,allt) "--MW-- cumulative battery mandate levels"
/
$offlisting
$ondelim
$include inputs_case%ds%storage_mandates.csv
$offdelim
$onlisting
/
;

scalar firstyear_battery "--year-- the first year battery technologies can be built, used to enforce storage mandate" ;
firstyear_battery = smin(i$battery(i),firstyear(i)) ;

table offshore_cap_req_all(st,allt) "--MW-- offshore wind capacity requirement under RPS rules by state"
$offlisting
$ondelim
$include inputs_case%ds%offshore_req.csv
$offdelim
$onlisting
;

table offshore_cap_goal_fix(st,allt) "--MW-- offshore fixed wind capacity requirement from Biden goals"
$offlisting
$ondelim
$include inputs_case%ds%offshore_goal_fix.csv
$offdelim
$onlisting
;

table offshore_cap_goal_float(st,allt) "--MW-- offshore float wind capacity requirement from Biden goals"
$offlisting
$ondelim
$include inputs_case%ds%offshore_goal_float.csv
$offdelim
$onlisting
;

parameter offshore_cap_req(st,allt,ofstype) "--MW-- offshore requirement/goal by type of offshore" ;
parameter r_offshore(r,t) "regions where offshore wind is required by a mandate" ;

if(Sw_OffshoreFrc = 1,
  offshore_cap_req(st,allt,'ofs_all') = offshore_cap_req_all(st,allt) ;
  r_offshore(rs,t)$[sum{rb$r_rs(rb,rs), sum{st$r_st(rb,st), offshore_cap_req_all(st,t) } }$(not sameas(rs,'sk'))] = 1 ;
) ;

if(Sw_OffshoreFrc = 2,
  offshore_cap_req(st,allt,'ofs_fix') = offshore_cap_goal_fix(st,allt) ;
  offshore_cap_req(st,allt,'ofs_float') = offshore_cap_goal_float(st,allt) ;
  r_offshore(rs,t)$[sum{rb$r_rs(rb,rs), sum{st$r_st(rb,st), offshore_cap_goal_fix(st,t) 
                                           + offshore_cap_goal_float(st,t) } }$(not sameas(rs,'sk'))] = 1 ;
) ;

*=============================
* Resource supply curve setup
*=============================

set rscbin "Resource supply curves bins" /bin1*bin%numbins%/,
    sc_cat "supply curve categories (capacity and cost)"
      /cap "capacity avaialable",
      cost "cost of capacity"/,
    rscfeas(r,rs,i,t,rscbin) "feasibility set for r s i and bins" ;

alias(rscbin,arscbin) ;

set refurb_cond(i,v,r,rs,t,tt,rscbin) "set to indicate whether a tech and vintage combination from year tt can be refurbished in year t" ;
refurb_cond(i,v,r,rs,t,tt,rscbin) = no ;

*written by writesupplycurves.py
parameter rsc_dat(r,rs,i,t,rscbin,sc_cat) "--unit vary-- resource supply curve data for renewables with capacity in MW and costs in $/MW"
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

* declared over allt to allow for external data files that extend beyond end_year
parameter geo_discovery(allt) "--fraction-- fraction of undiscovered geothermal that has been 'discovered'"
/
$offlisting
$ondelim
$include inputs_case%ds%geo_discovery.csv
$offdelim
$onlisting
/
;

* read data defining increase in hydropower upgrade availability over time. should only exist for hydUD and hydUND
table hyd_add_upg_cap(r,i,rscbin,allt) "--MW-- cumulative increase in available upgrade capacity relative to base year"
$offlisting
$ondelim
$include inputs_case%ds%hyd_add_upg_cap.csv
$offdelim
$onlisting
;

*geothermal can all get assigned to bin1 and is only considered at the BA level
rsc_dat(r,"sk",i,t,"bin1",sc_cat)$geo(i) = rsc_dat_geo(i,r,sc_cat) ;

*Convert geothermal supply curve costs from $/kW to $/MW
rsc_dat(r,"sk",i,t,"bin1","cost")$geo(i) = rsc_dat(r,"sk",i,t,"bin1","cost") * 1000 ;

*need to adjust units for pumped hydro costs from $ / KW to $ / MW
rsc_dat(r,rs,"pumped-hydro",t,rscbin,"cost") = rsc_dat(r,rs,"pumped-hydro",t,rscbin,"cost") * 1000 ;

*To allow pumped-hydro-flex via rscfeas and m_rscfeas, we set its supply curve capacity equal to pumped-hydro fixed.
*Note however that they will share the same supply curve capacity (see rsc_agg).
rsc_dat(r,rs,"pumped-hydro-flex",t,rscbin,"cap") = rsc_dat(r,rs,"pumped-hydro",t,rscbin,"cap") ;

*Make pumped-hydro-flex more expensive than fixed pumped-hydro by a fixed percent
rsc_dat(r,rs,"pumped-hydro-flex",t,rscbin,"cost") = rsc_dat(r,rs,"pumped-hydro",t,rscbin,"cost") * %GSw_HydroVarPumpCostRatio% ;

* Add capacity in Mexico to account to prescribed builds
$ifthen.sreg %GSw_IndividualSites% == 0
rsc_dat(r,"s357","wind-ons_3",t,"bin1","cost")$r_rs(r,"s357") =  rsc_dat(r,"s32","wind-ons_3",t,"bin1","cost") ;
rsc_dat(r,"s357","wind-ons_3",t,"bin1","cap")$r_rs(r,"s357") = 155.1 ;
$endif.sreg

$ontext
Replicate the UPV supply curve data for hybrid PV+battery
"rsc_data" for hybrid PV+battery is never used in the resource constraint (see note above about rsc_dat and tg_rsc_upvagg).
This copy is necessary to ensure the conditionals for the supply curve investment variables get created for pvb.
Example: "m_rscfeas(r,i,rscbin,t)" is created for "eq_rsc_inv_account"
$offtext

rsc_dat(r,rs,i,t,rscbin,sc_cat)$pvb(i) =  sum{ii$[upv(ii)$rsc_agg(ii,i)], rsc_dat(r,rs,ii,t,rscbin,sc_cat) } ;

*following set indicates which combinations of r, s, and i are possible
*this is based on whether or not the bin has capacity available
rscfeas(r,rs,i,t,rscbin)$rsc_dat(r,rs,i,t,rscbin,"cap") = yes ;

rscfeas(r,rs,i,t,rscbin)$[csp2(i)$sum{ii$[csp1(ii)$csp2(i)$tg_rsc_cspagg(ii,i)], rscfeas(r,rs,ii,t,rscbin) }] = yes ;
rscfeas(r,rs,i,t,rscbin)$[csp3(i)$sum{ii$[csp1(ii)$csp3(i)$tg_rsc_cspagg(ii,i)], rscfeas(r,rs,ii,t,rscbin) }] = yes ;
rscfeas(r,rs,i,t,rscbin)$[csp4(i)$sum{ii$[csp1(ii)$csp4(i)$tg_rsc_cspagg(ii,i)], rscfeas(r,rs,ii,t,rscbin) }] = yes ;

rscfeas(r,rs,i,t,rscbin)$[(not rfeas(r)) or ban(i)] = no ;

parameter binned_heatrates(i,v,r,allt) "--MMBtu / MWh-- existing capacity binned by heat rates" ;
binned_heatrates(i,v,r,allt) = hintage_data(i,v,r,allt,"wHR") ;


$ifthen.unit %unitdata%=='EIA-NEMS'
*Created by hourlize
*declared over allt to allow for external data files that extend beyond end_year
table exog_wind_ons(i,rs,allt,*) "existing wind capacity binned by TRG"
$offlisting
$ondelim
$include inputs_case%ds%wind-ons_exog_cap.csv
$offdelim
$onlisting
;
$endif.unit



parameter avail_retire_exog_rsc(i,v,r,t) "--MW-- available retired capacity for refurbishments" ;
avail_retire_exog_rsc(i,v,r,t) = 0 ;

set refurbtech(i) "technologies that can be refurbished" ;
refurbtech(i)$wind(i) = yes ;
refurbtech(i)$upv(i) = yes ;
refurbtech(i)$dupv(i) = yes ;
refurbtech(i)$dr(i) = yes ;
refurbtech(i)$pvb(i) = yes ;

table near_term_wind_capacity(r,allt) "MW of cumulative wind capacity in the build pipeline"
$offlisting
$ondelim
$include inputs_case%ds%wind_cap_reg.csv
$offdelim
$onlisting
;

parameter near_term_cap_limits(tg,r,t) "MW of cumulative capacity in project pipelines to limit near-term builds" ;
near_term_cap_limits("wind",r,t) = near_term_wind_capacity(r,t) ;



* declared over allt to allow for external data files that extend beyond end_year
parameter capacity_exog(i,v,r,allt)        "--MW-- exogenously specified capacity",
          m_capacity_exog(i,v,r,allt)      "--MW-- exogenous capacity used in the model",
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
capacity_exog(i,"init-1",r,t)${[yeart(t)-sum{tt$tfirst(tt),yeart(tt)}<maxage(i)]$rfeas(r)} =
                                 max(0,capnonrsc(i,r,"value")
                                       - sum{allt$[allt.val <= t.val],  prescribedretirements(allt,r,i,"value") }
                                    ) ;

*reset any exogenous capacity that is also specified in binned_capacity
*as these are computed based on bins specified by the numhintage global
*in the data-writing files
capacity_exog(i,v,r,t)$[sum{(rr,vv,allt), binned_capacity(i,vv,rr,allt) }$initv(v)$rfeas(r)] = 0 ;

capacity_exog("hydED","init-1",r,t)$rb(r) = caprsc("hydED",r,"value") ;
capacity_exog("hydEND","init-1",r,t)$rb(r) = caprsc("hydEND",r,"value") ;
capacity_exog(i,v,r,t)$[sum{allt,binned_capacity(i,v,r,allt)}$rfeas(r)] =
               sum{allt$att(allt,t), binned_capacity(i,v,r,allt) } ;

*reset all wind exogenous capacity levels
capacity_exog(i,v,r,t)$wind(i) = 0 ;

$ifthen %unitdata% == 'ABB'
*exogenous wind capacity is that which has not retired yet
*this is a 'trick' that is used to compute the existing wind capacity by class
*in that it is the sum of future retirements
capacity_exog(i,v,rs,t)$[wind(i)$rfeas_cap(rs)] = sum{allt$[year(allt)>=yeart(t)], windretirements(i,v,rs,allt) } ;
*fill in odd years with average values
capacity_exog(i,v,rs,t)$[wind(i)$oddyears(t)$rfeas_cap(rs] = (capacity_exog(i,v,rs,t-1) + capacity_exog(i,v,rs,t+1)) / 2 ;
$endif

$ifthen %unitdata% == 'EIA-NEMS'
capacity_exog(i,"init-1",rs,t)$[rfeas_cap(rs)$onswind(i)] = exog_wind_ons(i,rs,t,"capacity") ;
$endif


*fill in odd years' values for distpv
capacity_exog("distpv",v,r,t)$[oddyears(t)$rfeas(r)] =
    (capacity_exog("distpv",v,r,t-1) + capacity_exog("distpv",v,r,t+1)) / 2 ;

capacity_exog("distpv",v,r,t)$[oddyears(t)$rfeas(r)] = (capacity_exog("distpv",v,r,t-1) + capacity_exog("distpv",v,r,t+1)) / 2 ;

*capacity for geothermal is determined through forcing of prescribed builds
*geothermal is also not a valid technology and rather a placeholder
capacity_exog("geothermal",v,r,t) = 0 ;

*capacity for hydro is specified for technologies in RSC techs
*ie hydro has specific classes (e.g. HydEd) that are specified
*separately, therefore the general 'hydro' category is not needed
capacity_exog("hydro",v,r,t) = 0 ;

*set Canadian imports as prescribed capacity
capacity_exog("can-imports","init-1",rb,t) = smax(szn,(can_imports_szn(rb,szn,t) / sum{h$h_szn(h,szn), hours(h) })) ;

*if you've declined in value
avail_retire_exog_rsc(i,v,r,t)$[refurbtech(i)$(capacity_exog(i,v,r,t-1) > capacity_exog(i,v,r,t))$rfeas_cap(r)] =
    capacity_exog(i,v,r,t-1) - capacity_exog(i,v,r,t) ;

avail_retire_exog_rsc(i,v,r,t)$[not initv(v)] = 0 ;

m_capacity_exog(i,v,r,t)$rfeas_cap(r) = capacity_exog(i,v,r,t) ;
m_capacity_exog(i,"init-1",r,t)$geo(i) = geo_cap_exog(i,r) ;


* with regional h2 demands, we assume capacity follows demand and thus load in
* national demand values, the shares of national demand by each BA
* we then convert those to MW of capacity using the conversion of tonnes / mw

parameter h2_exogenous_demand(p,allt)            "--tonne/yr-- exogenous demand of hydrogen",
          h2_exogenous_demand_regional(r,p,allt) "--tonne/yr-- exogenous demand of hydrogen at the BA level"


table h2_exogenous_demand0(p,allt,*) "--million tonnes-- exogenous demand of H2 by type (blue or green), year, and scenario - loaded in"
$ondelim
$include inputs_case%ds%h2_exogenous_demand.csv
$offdelim
;

* 1e6 used to convert from million tonne to tonne
h2_exogenous_demand(p,t) = 1e6 * h2_exogenous_demand0(p,t,"%GSw_H2_Demand_Case%") ;

parameter h2_share(r,allt) "--fraction-- regional share of national hydrogen demand"
/
$ondelim
$include inputs_case%ds%h2_ba_share.csv
$offdelim
/;

*Units for electrolyzer:
*  Overnight Capital Cost ($/kW)
*  FOM  ($/kW-yr)
*  Elec Efficiency (kWh/kg)
*Units for SMR:
*  Overnight Capital Cost ($/kg/day)
*  FOM  ($/kg/day-yr)
*  Elec Efficiency (kWh/kg)
*  NG Efficiency (MMBtu/kg)
parameter consume_char0(i,allt,*) "--units vary (see commented text above)-- input plant characteristics"
$offlisting
$ondelim
$offdigit
/
$include inputs_case%ds%consume_char_%GSw_H2_Inputs%.csv
/
$ondigit
$offdelim
$onlisting
;


h2_share(r,t)$[rfeas(r)$(yeart(t)<=2021)] = h2_share(r,"2021");

* need to linearly interpolate all gap years as input data is only populated for 2050 and 2021
h2_share(r,t)$[rfeas(r)$(yeart(t)>2021)$(yeart(t)<2050)] =
  h2_share(r,"2021") + ((h2_share(r,"2050") - h2_share(r,"2021")) / (2050-2021)) * (yeart(t) - 2021) ;

h2_exogenous_demand_regional(r,p,t)$[rfeas(r)$tmodel_new(t)] = h2_share(r,t) * h2_exogenous_demand(p,t) ;

* adjust capacity such that it matches regional demand
* while also adjusting for timeslice-weighted availability assumptions
m_capacity_exog("smr","init-1",r,t)$Sw_H2 =
* regional exogenous demand (in tonnes)
* note that with rounding of parameters in d_solveprep we need
* to make a tiny adjustment upwards to avoid infeasibilities
* this parameter is further updated below after the population
* of the avail parameter - doing the initial calculations here
* helps to avoid issues with valcap in the assignment of
* consuming technology characteristics
  1.0001 * (( sum{p, h2_exogenous_demand_regional(r,p,"2020") }
* adjusting for tonnes / MW
  / (1 / consume_char0("smr","2010","ele_efficiency")) )
* from annual to hourly
  ) / 8760;


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

set cap_agg(r,r)              "set for aggregated resource regions to BAs"
    valcap(i,v,r,t)           "i, v, r, and t combinations that are allowed for capacity",
    valcap_irt(i,r,t)         "i, r, and t combinations that are allowed for capacity",
    valinv(i,v,r,t)           "i, v, r, and t combinations that are allowed for investments",
    valinv_irt(i,r,t)         "i, r, and t combinations that are allowed for investments",
    valgen(i,v,r,t)           "i, v, r, and t combinations that are allowed for generation",
    m_refurb_cond(i,v,r,t,tt) "i v r combinations that are built in tt that can be refurbished in t",
    m_rscfeas(r,i,t,rscbin)   "--qualifier-- feasibility conditional for investing in RSC techs"
;

cap_agg(r,rs)$[(not sameas(rs,"sk"))$r_rs(r,rs)] = yes ;
cap_agg(r,rb)$sameas(r,rb) = yes ;

* define qualifier for renewable supply curve investment variables
  m_rscfeas(rb,i,t,rscbin) = rscfeas(rb,"sk",i,t,rscbin) ;
  m_rscfeas(rs,i,t,rscbin)$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs), rscfeas(r,rs,i,t,rscbin) } ;
* CSP
  m_rscfeas(r,i,t,rscbin)$[sum{ii$tg_rsc_cspagg(ii, i),m_rscfeas(r,ii,t,rscbin) }] = yes ;
* Hybrid PV+battery
  m_rscfeas(r,i,t,rscbin)$[sum{ii$tg_rsc_upvagg(ii, i),m_rscfeas(r,ii,t,rscbin) }] = yes ;
* exclude ineligible regions
  m_rscfeas(r,i,t,rscbin)$[not rfeas_cap(r)] = no ;

Parameter m_required_prescriptions(pcat,r,t)  "--MW-- required prescriptions by year (cumulative)" ;

*following does not include wind
*conditional here is due to no prescribed retirements for RSC tech
*distpv is an rsc tech but is handled different via binned_capacity as explained above
m_required_prescriptions(pcat,rb,t)$[rfeas(rb)$tmodel_new(t)]
          = sum{tt$[yeart(t)>=yeart(tt)], prescribednonrsc(tt,pcat,rb,"value") } ;


m_required_prescriptions(pcat,r,t)$[rfeas_cap(r)$tmodel_new(t)
                                   $(sum{tt$[yeart(t)>=yeart(tt)], prescribedrsc(tt,pcat,r,"value") }
                                     or caprsc(pcat,r,"value"))]
        = sum{(tt)$[(yeart(t) >= yeart(tt))], prescribedrsc(tt,pcat,r,"value") }
        + caprsc(pcat,r,"value")
;

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

* Hybrid degradation is initially defined as the battery degradation for calculating the ITC for the hybrid battery (degradation_annual_default.csv).
* Here, reassign hybrid PV+Battery to have the same value as UPV.
* Currently the degradation for the battery is zero, but if becomes non-zero, then two separate degradation factors should be defined
* (e.g., degrade_pvb_p, degrade_pvb_b) to allow for degradation to be applied to both the PV and battery.
degrade_annual(i)$pvb(i) = sum{ii$[upv(ii)$rsc_agg(ii,i)], degrade_annual(ii) } ;

degrade_annual(i)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), degrade_annual(ii) } ;

degrade(i,t,tt)$[(yeart(tt)>=yeart(t))$(not ban(i))] = 1 ;
degrade(i,t,tt)$[(yeart(tt)>=yeart(t))$(not ban(i))] = (1-degrade_annual(i))**(yeart(tt)-yeart(t)) ;

set prescription_check(i,v,r,t) "check to see if prescriptive capacity comes online in a given year" ;

parameter noncumulative_prescriptions(pcat,r,t) "--MW-- prescribed capacity that comes online in a given year" ;
* need to fill in for unmodeled, gap years via tprev but
* tprev is not defined with tprev(t,tfirst)
noncumulative_prescriptions(pcat,r,t)$[tmodel_new(t)$rfeas_cap(r)]
                                  = sum{tt$[(yeart(tt)<=yeart(t)
* this condition populates values of tt which exist between the
* previous modeled year and the current year
                                          $(yeart(tt)>sum{ttt$tprev(t,ttt), yeart(ttt) }))
                                          ],
                                        prescribednonrsc(tt,pcat,r,"value") + prescribedrsc(tt,pcat,r,"value")
                                      } ;

prescription_check(i,newv,rb,t)$[sum{pcat$prescriptivelink(pcat,i), noncumulative_prescriptions(pcat,rb,t) }
                                 $ivt(i,newv,t)$tmodel_new(t)$(not csp(i))$(not wind(i))$(not ban(i))$rfeas(rb)] = yes ;

prescription_check(i,newv,rs,t)$[sum{pcat$prescriptivelink(pcat,i), noncumulative_prescriptions(pcat,rs,t) }
                                 $ivt(i,newv,t)$tmodel_new(t)$(csp(i) or wind(i))$(not ban(i))$sum{r$r_rs(r,rs), rfeas(r) }] = yes ;

*==========================================
* -- Valid Capacity and Generation Sets --
*==========================================

* -- valcap specification --
* first all available techs are included
* then we remove those as specified

* need to add H2 techs and/or DAC techs to ban(i)
* before specification of valcap if those switches are disabled

$ifthene.h2ban %GSw_H2% == 0
ban(i)$h2(i) = yes ;
$endif.h2ban

$ifthene.dacban %GSw_DAC% == 0
ban(i)$dac(i) = yes ;
$endif.dacban

$ifthene.cspban %GSw_CSP% == 0
* Add csp(i) tech to ban(i)
ban(i)$csp(i) = yes ;
$endif.cspban

* Add ofswind(i) tech to ban(i)
$ifthene.ofswindban %GSw_OfsWind% == 0
ban(i)$ofswind(i) = yes ;
$endif.ofswindban

* turn off first 5 onshore wind technologies
$ifthene.onswindban %GSw_OnsWind6to10% == 0
bannew('wind-ons_6') = yes ;
bannew('wind-ons_7') = yes ;
bannew('wind-ons_8') = yes ;
bannew('wind-ons_9') = yes ;
bannew('wind-ons_10') = yes ;
$endif.onswindban

* turn off biopower technology
$ifthene.biopowerban %GSw_Biopower% == 0
ban('biopower') = yes ;
$endif.biopowerban

* turn off Coal-IGCC technology
$ifthene.coaligccban %GSw_CoalIGCC% == 0
ban('Coal-IGCC') = yes ;
$endif.coaligccban

* turn off CoFireNew technology
$ifthene.cofirenewban %GSw_CofireNew% == 0
ban('CofireNew') = yes ;
$endif.cofirenewban

* turn off lfill-gas technology
$ifthene.lfillgasban %GSw_LfillGas% == 0
ban('lfill-gas') = yes ;
$endif.lfillgasban

* exclude dupv
$ifthene.dupvban %GSw_DUPV% == 0
ban(i)$dupv(i) = yes ;
$endif.dupvban

* place coal-new to ban set
$ifthene.coalnewban %GSw_CoalNew% == 0
ban('coal-new') = yes ;
$endif.coalnewban

* add nuclear(i) to bannew(i)
$ifthene.nuclearbannew %GSw_Nuclear% == 0
bannew(i)$nuclear(i) = yes ;
$endif.nuclearbannew


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
                    $sum{rscbin, m_rscfeas(r,i,t,rscbin) }$(not upgrade(i))
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
valcap(i,newv,r,t)$[Sw_WaterMain$sum{ctt$bannew_ctt(ctt),i_ctt(i,ctt) }$rfeas(r)$tmodel_new(t)
                  $sum{(tt,pcat)$[(yeart(tt)<=yeart(t))$sameas(pcat,i)], m_required_prescriptions(pcat,r,tt) }
                  $sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) }] = yes ;

* if switch is equal to zero, remove all geothermal technologies
if(Sw_Geothermal = 0,
  valcap(i,v,r,t)$geo(i) = no ;
  ban(i)$geo(i) = yes ;
) ;

* if equal to one, only keep the non-extended default representation
if(Sw_Geothermal = 1,
  valcap(i,v,r,t)$geo_extra(i) = no ;
  ban(i)$geo_extra(i) = yes ;
) ;


* Restrict valcap for storage techs based on Sw_Storage switch
if(Sw_Storage = 0,
 valcap(i,v,r,t)$storage_standalone(i) = no ;
 ban(i)$storage_standalone(i) = yes ;
 Sw_BatteryMandate = 0 ;
) ;

* Restrict valcap for DR techs based on Sw_DR switch
if(Sw_DR = 0,
  valcap(i,v,r,t)$dr(i) = no ;
  ban(i)$[dr(i)] = yes ;
) ;

* Restrict valcap for storage techs based on Sw_Storage switch
if(Sw_Storage = 4,
 valcap(i,v,r,t)$[storage_standalone(i)$(not sameas(i,'battery_4'))] = no ;
 ban(i)$[storage_standalone(i)$(not sameas(i,'battery_4'))] = yes ;
) ;

* Restrict valcap for ccs techs based on Sw_CCS switch
if(Sw_CCS = 0,
  valcap(i,v,r,t)$ccs(i) = no ;
  ban(i)$ccs(i) = yes ;
) ;

*csp-ns is only allowed in regions where prescriptions are required
valcap(i,newv,r,t)$cspns(i) = no ;

valcap(i,newv,r,t)$[rfeas_cap(r)$cspns(i)$(sum{pcat$cspns_pcat(pcat), m_required_prescriptions(pcat,r,t) })
                          $sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) } ] = yes ;

valcap(i,v,r,t)$[not tmodel_new(t)] = no ;

valcap(i,v,r,t)$[i_numeraire(i)$Sw_WaterMain] = no ;


*upgraded init capacity is available if the tech from which it is
*upgrading is in valcap and not banned
valcap(i,initv,r,t)$[upgrade(i)$Sw_Upgrades$(yeart(t)>=upgradeyear)
                    $sum{ii$upgrade_from(i,ii), valcap(ii,initv,r,t) }
                    $(not ban(i))
                    $(not sum{ii$upgrade_to(i,ii), ban(ii) })
                    ] = yes ;

*upgrades from new techs are included in valcap if...
* it is an upgrade tech, the switch is enabled, and past the beginning upgrade year
valcap(i,newv,r,t)$[upgrade(i)$Sw_Upgrades$(yeart(t)>=upgradeyear)
*if the capacity that it is upgraded from is available
                   $sum{ii$upgrade_from(i,ii), valcap(ii,newv,r,t) }
*if the technology is not banned
                   $(not ban(i))
*if the technology you upgrade to is not banned
                   $(not sum{ii$upgrade_to(i,ii), ban(ii) })
*if it is past the first year that technology is available
                   $(yeart(t)>=firstyear(i))
*if it is a valid ivt combination which is duplicated from upgrade_to
                   $sum{tt$(yeart(tt)<=yeart(t)), ivt(i,newv,tt) }
                   ] = yes ;

*remove any upgrade considerations if before the upgrade year
valcap(i,v,r,t)$[upgrade(i)$(yeart(t)<upgradeyear)] = no ;

*this is more of a failsafe for potential capacity leakage
valcap(i,v,r,t)$[upgrade(i)$(not Sw_Upgrades)] = no ;

*remove capacity from valcap that is required to retire
valcap(i,v,r,t)$forced_retirements(i,r,t) = no ;

*do not allow upgrades when there is no capacity to upgrade from
valcap(i,v,r,t)$[(not sum{ii$upgrade_from(i,ii),valcap(ii,v,r,t) })$upgrade(i)] = no ;

* remove upgrade technologies that are explicitly banned
valcap(i,v,r,t)$[upgrade(i)$ban(i)] = no ;

$ifthene.hydEDban %GSw_hydED% == 0
* Only leave hydED, turn off remaining hydro technologies
valcap(i,v,r,t)$[hydro(i)$(not sameas(i,"hydED"))] = no ;
$endif.hydEDban


* Add aggregations of valcap
valcap_irt(i,r,t) = sum{v, valcap(i,v,r,t) } ;

* -- valinv specification --
valinv(i,v,r,t) = no ;
valinv(i,v,r,t)$[valcap(i,v,r,t)$ivt(i,v,t)] = yes ;

valinv(i,v,rb,t)$[sum{st$r_st(rb,st),tech_banned(i,st) }$(not sum{pcat$prescriptivelink(pcat,i),noncumulative_prescriptions(pcat,rb,t) })] = no ;
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
valgen(i,v,r,t)$[sum{rr$cap_agg(r,rr),valcap(i,v,rr,t) }] = yes ;
* consuming technologies are not allowed to generate
valgen(i,v,r,t)$consume(i) = no ;

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

inv_cond(i,newv,r,t,tt)$[Sw_WaterMain$sum{ctt$bannew_ctt(ctt),i_ctt(i,ctt) }$rfeas(r)$tmodel_new(t)$tmodel_new(tt)
                      $sum{(pcat)$[sameas(pcat,i)], noncumulative_prescriptions(pcat,r,tt) }
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

i_water_surf(i)$[sum{(sw,ctt,ii)$i_ii_ctt_wst(i,ii,ctt,sw), 1}] = yes ;
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
          watsa(wst,r,allszn,t) "seasonal distribution factors for new water access by year (fractional)" ;

table watsa_temp(wst,r,allszn)   "fractional seasonal allocation of water" \\ check with parameter
$offlisting
$ondelim
$include inputs_case%ds%unapp_water_sea_distr.csv
$offdelim
$onlisting
;
watsa(wst,r,szn,t)$[tmodel_new(t)$rfeas(r)$Sw_WaterMain] = watsa_temp(wst,r,szn) ;

parameter numdays(allszn) "--number of days-- number of days for each season" ;
numdays(szn) = sum{h$h_szn(h,szn),hours(h) } / 24 ;

*update seasonal distribution factors for water sources other than fresh surface unappropriated and also fsu with missing data
watsa(wst,r,szn,t)$[(not sum{szn2, watsa(wst,r,szn2,t)})$rfeas(r)$tmodel_new(t)$Sw_WaterMain] = round(numdays(szn)/365 , 2) ;

*Initialize water capacity based on water requirements of existing fleet in base year. We conservatively assume plants have
*enough water available to operate up to a 100% capacity factor, or to operate at full capacity at any time of the year.
wat_supply_init(wst,r) = (8760/1E6) * sum{(i,v,w,t)$[i_w(i,w)$valcap(i,v,r,t)$initv(v)$i_wst(i,wst)$tfirst(t)],
                                                        m_capacity_exog(i,v,r,t) * water_rate(i,w,r) } ;

m_watsc_dat(wst,"cost",r,t)$tmodel_new(t) = wat_supply_new(wst,"cost",r) ;
m_watsc_dat(wst,"cap",r,t)$tmodel_new(t) = wat_supply_new(wst,"cap",r) + wat_supply_init(wst,r) ;

*not allowed to invest in upgrade techs since they are a product of upgrades
inv_cond(i,v,r,t,tt)$upgrade(i) = no;


*===============================================
* --- Climate change impacts: Cooling water ---
*===============================================

$ifthen.climatewater %GSw_ClimateWater% == 1

* Indicate which cooling techs are affected by climate change
set wst_climate(wst) "water sources affected by climate change" /fsu, fsa/ ;

* Update seasonal distribution factors for fsu; other water types are unchanged
* declared over allt to allow for external data files that extend beyond end_year
table watsa_climate(wst,r,allszn,allt)  "time-varying fractional seasonal allocation of water"
$offlisting
$ondelim
$include inputs_case%ds%climate_UnappWaterSeaAnnDistr.csv
$offdelim
$onlisting
;
* Use the sparse assignment $= to make sure we don't assign zero to wst's not included in watsa_climate
watsa(wst,r,szn,t)$[wst_climate(wst)$rfeas(r)$r_country(r,"USA")$tmodel_new(t)$Sw_WaterMain$(yeart(t)>=climateyear)] $=
  sum{allt$att(allt,t), watsa_climate(wst,r,szn,allt) };
* If wst is in wst_climate but does not have data in input file, assign its multiplier to the fsu multiplier
watsa(wst,r,szn,t)$[wst_climate(wst)$rfeas(r)$r_country(r,"USA")$tmodel_new(t)$Sw_WaterMain$(yeart(t)>=climateyear)$sum{allt$att(allt,t), (not watsa_climate(wst,r,szn,allt)) }] $=
  sum{allt$att(allt,t), watsa_climate('fsu',r,szn,allt) };

* Update water supply curve with annually-varying water supply. Multiplier is applied to (wat_supply_new + wat_supply_init).
* NOTE: Only the capacity changes, not the cost
table wat_supply_climate(wst,r,allt)  "time-varying annual water supply"
$offlisting
$ondelim
$include inputs_case%ds%climate_UnappWaterMultAnn.csv
$offdelim
$onlisting
;
m_watsc_dat(wst,"cap",r,t)$[wst_climate(wst)$rfeas(r)$r_country(r,"USA")$tmodel_new(t)$(yeart(t)>=climateyear)] $=
  sum{allt$att(allt,t), m_watsc_dat(wst,"cap",r,t) * wat_supply_climate(wst,r,allt) } ;
* If wst is in wst_climate but does not have data in input file, assign its multiplier to the fsu multiplier
m_watsc_dat(wst,"cap",r,t)$[wst_climate(wst)$rfeas(r)$r_country(r,"USA")$tmodel_new(t)
                           $(yeart(t)>=climateyear)$sum{allt$att(allt,t), (not wat_supply_climate(wst,r,allt)) }] $=
  sum{allt$att(allt,t), m_watsc_dat(wst,"cap",r,t) * wat_supply_climate('fsu',r,allt) } ;

$endif.climatewater


*=====================================
* --- Regional Carbon Constraints ---
*=====================================


Set RGGI_States(st) "states with RGGI regulation" /MA, CT, DE, MD, ME, NH, NJ, NY, RI, VT, VA/ ,
    RGGI_r(r) "BAs with RGGI regulation",
    state_cap_r(r) "BAs with state co2 cap regulation" ;

RGGI_r(r)$[sum{st$RGGI_States(st),r_st(r,st) }] = yes ;
state_cap_r(r)$r_st(r,"CA") = yes ;

Scalar RGGI_start_yr "RGGI Start year" /2012/,
       state_cap_start_yr "state co2 cap start year" /2014/ ;

* declared over allt to allow for external data files that extend beyond end_year
parameter RGGI_cap(allt) "--metric ton-- CO2 emissions cap for RGGI states"
/
$offlisting
$ondelim
$include inputs_case%ds%rggicon.csv
$offdelim
$onlisting
/ ;

* These values are based on 42 MMT trajectory from section 8.1 of the CPUC "Inputs & Assumptions:
* "2019-2020 Integrated Resource Plannin." This document can be found at
* ftp://ftp.cpuc.ca.gov/energy/modeling/Inputs%20%20Assumptions%202019-2020%20CPUC%20IRP%202020-02-27.pdf
parameter state_cap(allt) "--metric ton-- CO2 emissions cap for CA cap and trade requirement"
/
$offlisting
$ondelim
$include inputs_case%ds%statecap.csv
$offdelim
$onlisting
/ ;

*assuming 2017 value from figure 9 of:
*https://ww3.arb.ca.gov/cc/inventory/pubs/reports/2000_2018/ghg_inventory_trends_00-18.pdf
Scalar CA_import_emit "--metric ton CO2 / MWh-- emissions measured on imports to California" /0.25/ ;



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
RPSAll(i,st)$re_ct(i) = yes ;

*rpscat definitions for each technology
RPSCat_i("RPS_All",i,st)$RPSAll(i,st) = yes ;
RPSCat_i("RPS_Wind",i,st)$wind(i) = yes ;
* Add hybrid PV+battery to the solar category for tracking REC types
RPSCat_i("RPS_Solar",i,st)$[upv(i) or dupv(i) or sameas(i,"distpv") or pvb(i)] = yes ;
RPSCat_i("CES",i,st)$[RPSCAT_i("RPS_All",i,st) or nuclear(i) or hydro(i)] = yes ;

* Massachusetts CES does not allow for existing hydro, so we don't allow any hydro
RPSCat_i("CES",i,'MA')$hydro(i) = no ;

* We allow CCS techs and upgrades to be elgible for CES policies
* CCS contribution is limited based on the amount of emissions captured later on down
RPSCat_i("CES",i,st)$ccs(i) = yes ;

*california does not accept distpv credits
RPSCat_i(RPSCat,"distpv","ca") = no ;

* created using input_processing\cfgather.py
* declared over allt to allow for external data files that extend beyond end_year
Table RECPerc_in(allt,st,RPSCat) "--fraction-- requirement for state RPS"
$offlisting
$ondelim
$include inputs_case%ds%recperc.csv
$offdelim
$onlisting
;

Table CES_Perc(st,allt) "--fraction-- requirement for clean energy standard"
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

table acp_price(st,allt) "$/REC - safety valve price for RPS constraint"
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


set rpsScen "National RPS scenario options"
  /
    80, 90, 95, 99, 97, 100,
    80_2030, 90_2030, 95_2030, 97_2030, 99_2030, 100_2030,
    95_2035, 97_2035, 99_2035, 100_2035,
    80_2040, 90_2040, 95_2040, 97_2040, 99_2040, 100_2040
  / ;

table national_gen_frac_allScen(allt,rpsScen) "--%-- national fraction of load + losses that must be met by RE by scenario"
$ondelim
$include inputs_case%ds%national_gen_frac_allScen.csv
$offdelim
;

parameter national_gen_frac(t) "--%-- national fraction of load + losses that must be met by RE" ;
national_gen_frac(t) = national_gen_frac_allScen(t,"%GSw_RenMandateScen%") ;

parameter nat_gen_tech_frac(i) "--fraction-- fraction of each tech generation that may be counted toward eq_national_gen"
/
$ondelim
$include inputs_case%ds%nat_gen_tech_frac.csv
$offdelim
/
;
* GSw_CES treats the RPS as a clean-energy standard and thus includes nuclear
if(Sw_CES = 1,
  nat_gen_tech_frac(i)$nuclear(i) = yes ;
) ;


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


table csapr_cap(st,csapr_cat,allt) "--MT NOX-- maximum amount of emissions during the ozone season (May-September)"
$offlisting
$ondelim
$include inputs_case%ds%csapr_ozone_season.csv
$offdelim
$onlisting
;


set csapr_group1_ex(st) "CSAPR states that cannot trade with those in group 2" /AR, FL, LA, MS, OK/,
    csapr_group2_ex(st) "CSAPR states that cannot trade with those in group 1" /KS, MN, NE/,
    csapr_group_st(csapr_group,st) "final crosswalk set for use in modeling CSAPR trade relationships" ;

csapr_group_st("cg1",st)$[sum{t,csapr_cap(st,"budget",t)}$(not csapr_group1_ex(st))$stfeas(st)] = yes ;
csapr_group_st("cg2",st)$[sum{t,csapr_cap(st,"budget",t)}$(not csapr_group2_ex(st))$stfeas(st)] = yes ;

parameter h_weight_csapr(allh) "hour weights for CSAPR ozone season constraints" ;
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

set trtype                    "transmission capacity type" /AC, DC, VSC/
    aclike(trtype)            "transmission capacity types that are treated like AC" /AC, DC/
    trancap_fut_cat           "categories of near-term transmission projects that describe the likelihood of being completed" /certain, possible/
    tscfeas(r,vc)             "set to declare which transmission substation supply curve voltage classes are feasible for which regions"
    routes(r,rr,trtype,t)     "final conditional on transmission feasibility"
    routes_inv(r,rr,trtype,t) "routes where new transmission investment is allowed"
    opres_routes(r,rr,t)      "final conditional on operating reserve flow feasibility"
;
alias(trtype,intype,outtype) ;

* --- initial transmission capacity ---
* NOTE: The transmission capacity input data are defined in one direction for each region-to-region pair with the lowest region number listed first.
parameter trancap_init(r,rr,trtype) "--MW-- initial transmission capacity by type (tracked in one direction, low to high region number)"
/
$offlisting
$ondelim
$include inputs_case%ds%trancap_init.csv
$offdelim
$onlisting
/ ;

parameter trancap_init_bd(r,rr,trtype) "--MW-- initial transmission capacity by type (tracked in both directions)---this is used for the ReEDS/PLEXOS linkage" ;
trancap_init_bd(r,rr,trtype)$[trancap_init(r,rr,trtype) or trancap_init(rr,r,trtype)] =
                                trancap_init(r,rr,trtype) + trancap_init(rr,r,trtype) ;

* --- future transmission capacity ---
* NOTE: The transmission capacity input data are defined in one direction for each region-to-region pair with the lowest region number listed first.
parameter trancap_fut(r,rr,trancap_fut_cat,allt,trtype) "--MW-- potential future transmission capacity by type (one direction)"
/
$offlisting
$ondelim
$include inputs_case%ds%trancap_fut.csv
$offdelim
$onlisting
/ ;

* --- exogenously specified transmission capacity ---
* NOTE: The transmission capacity input data are defined in one direction for each region-to-region pair with the lowest region number listed first.

parameter trancap_exog(r,rr,trtype,t) "--MW-- cumulative exogenous transmission capacity (one direction)" ;
trancap_exog(r,rr,trtype,t) =
*initial transmission capacity
    + trancap_init(r,rr,trtype)
*plus all "certain" future transmission project capacity through the current year t
    + sum{tt$[(tt.val<=t.val)], trancap_fut(r,rr,"certain",tt,trtype) }
;

* --- valid transmission routes ---

*transmission routes are enabled if:
* (1) there is transmission capacity between the two regions
routes(r,rr,trtype,t)$(trancap_exog(r,rr,trtype,t) or trancap_exog(rr,r,trtype,t)) = yes ;
* (2) there is future capacity available between the two regions
routes(r,rr,trtype,t)$(sum{(tt,trancap_fut_cat)$(yeart(tt)<=yeart(t)),trancap_fut(r,rr,trancap_fut_cat,tt,trtype) }) = yes ;
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

*IF SW_TranRestrict is 4, only allow intra-RTO transmission builds,
*and not across interconnects
if(Sw_TranRestrict = 4,
    routes_inv(r,rr,trtype,t)$[sum{rto_agg$[r_rto_agg(r,rto_agg)$r_rto_agg(rr,rto_agg)], 1 }
                     $routes(r,rr,trtype,t)
                     $(INr(r)=INr(rr))] = yes ;
) ;

* Transmission scalars: tranloss_permile_ac, tranloss_permile_dc, distloss,
* converter_efficiency_ac,  converter_efficiency_vsc, converter_efficiency_lcc,
* cost_acdc_lcc, cost_acdc_vsc, firstyear_trans, trans_fom_frac, trans_fom_region_mult
* Note that the distloss assumption is a generic estimate of distribution losses taken many years ago from AEO 2006
$include inputs_case%ds%scalars_transmission.txt

*Do not allow transmission expansion on most corridors until firstyear_trans
routes_inv(r,rr,trtype,t)$[yeart(t)<firstyear_trans] = no ;
*Do allow "possible" corridors to be expanded
routes_inv(r,rr,trtype,t)$[sum{tt$[(yeart(tt)<=yeart(t))], trancap_fut(r,rr,"possible",tt,trtype) + trancap_fut(rr,r,"possible",tt,trtype) }] = yes ;
routes_inv(rr,r,trtype,t)$[not routes_inv(r,rr,trtype,t)] = no ;

*Undo the change from adding "possible" routes when Sw_TranRestrict = 2
if(Sw_TranRestrict = 2,
    routes_inv(r,rr,trtype,t) = no ;
) ;

* operating reserve flows only allowed over AC lines
opres_routes(r,rr,t)$routes(r,rr,"AC",t) = yes ;

set samerto(r,rr) "binary indicator if two regions exist in the same rto: 1=same RTO, 0=not same RTO" ;
samerto(r,rr) = sum{(rto,rto2)$[r_rto(r,rto)$r_rto(rr,rto2)$sameas(rto,rto2)], 1 } ;

*exclude operating reserve flows between two regions in different RTOs
opres_routes(r,rr,t)$[not samerto(r,rr)] = no ;

*allow for turning off all operating reserve trade between BAs
opres_routes(r,rr,t)$[Sw_OpResTrade=0] = no ;

* Multiplier on opres flow. This multiplier increases the amount of transmission required
* to trade operating reserves (e.g. a value of 1.1 means that 1.1 MW of free transmission is needed
* to transfer 1 MW of operating reserves). Multiplier serves as a means of ensuring there is
* "extra" transmission available to reduce the potential for line overloading in the case of
* an outage/contingency in which spinning reserves would be deployed.
Scalar opres_mult "multiplier on opres flow in transmission constraint" ;
opres_mult = Sw_OpResTradeMult;


* --- multi-link transmission routes ---

set translinkage(r,rr,n,nn,trtype) "optimal transmission paths between all regions" ;
translinkage(r,rr,n,nn,trtype) = no ;
$ifthen.multilink %GSw_TransMultiLink% == 1
* If using multilink transmission, translinkage(r',rr',n',nn',trtype') exists if
* (n',nn',trtype') is a link in the optimal path from r' to rr'
set translinkage_input(r,rr,n,nn,trtype)
/
$offlisting
$ondelim
$include inputs_case%ds%trans-multilink-segments.csv
$offdelim
$onlisting
/ ;
translinkage(r,rr,n,nn,trtype)$[translinkage_input(r,rr,n,nn,trtype)$rfeas(r)$rfeas(rr)] = yes ;

$else.multilink
* Otherwise, translinkage(r',rr',n',nn',trtype') exists if
* n'=r' and nn'=rr' and (r',rr',trtype') is in routes_inv
translinkage(r,rr,n,nn,trtype)$[
  sameas(r,n)$sameas(rr,nn)$(ord(n)<ord(nn))$sum{t, routes_inv(r,rr,trtype,t)}] = yes ;
translinkage(r,rr,n,nn,trtype)$[
  sameas(r,nn)$sameas(rr,n)$(ord(n)<ord(nn))$sum{t, routes_inv(r,rr,trtype,t)}] = yes ;
$endif.multilink


* --- transmission cost ---

*created using input_processing\R\trangather.R
Table cost_tranline(r,trtype) "--$ per MW-mile-- cost of transmission line capacity for each region"
$offlisting
$ondelim
$include inputs_case%ds%transmission_line_cost.csv
$offdelim
$onlisting
;

* Scale regional transmission costs by Sw_TransCostMult (for sensitivity analysis)
cost_tranline(r,trtype) = cost_tranline(r,trtype) * Sw_TransCostMult ;

* Transmission FOM cost (written by input_processing/transmission_multilink.py)
Table trans_fom(r,trtype) "--$ per MW-mile per year-- fixed O&M cost of transmission for each region"
$offlisting
$ondelim
$include inputs_case%ds%trans_fom.csv
$offdelim
$onlisting
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
            $sum{(trtype,t),routes(r,rr,trtype,t) }] = cost_hurdle_country("MEX") ;

* define hurdle rates between the US and Canada
cost_hurdle(r,rr)$[((r_country(r,"CAN") and r_country(rr,"USA"))
              or (r_country(rr,"CAN") and r_country(r,"USA")))
            $sum{(trtype,t),routes(r,rr,trtype,t) }] = cost_hurdle_country("CAN") ;

* --- transmission distance ---

* The distance for an AC cooridor is calculated by tracing the "least-cost" path
* that follows existing AC lines between the two representative nodes of (r,rr)
* Larger voltage lines have the lowest "cost" for tracing
* The distance for a DC corridor is the reported project distances
* The distance for a DC intertie corridor is the same as the AC distance
parameter distance(r,rr,trtype) "--miles-- distance between BAs by line type"
/
$offlisting
$ondelim
$include inputs_case%ds%transmission_distance.csv
$offdelim
$onlisting
/ ;

* --- transmission losses ---
* Written by input_processing/transmission_multilink.py
parameter tranloss(r,rr,trtype)    "--fraction-- transmission loss between r and rr"
/
$offlisting
$ondelim
$include inputs_case%ds%tranloss.csv
$offdelim
$onlisting
/
;


* --- VSC HVDC macrogrid ---
set
vsc_required(r,rr) "BA pairs for which the optimal multi-link path for curtailment reduction uses VSC"
val_converter(r,t) "BAs where VSC converter investment is allowed"
;
vsc_required(r,rr) = no ;
val_converter(r,t) = no ;

$ifthen.vsc %GSw_VSC% == 1
* We define a single optimal path (either cost-minimizing or loss-minimizing) between each source
* and sink BA in transmission_mutlilink.py, which is then used in the calculation of curtailment
* reduction potential in Augur/C2_marginal_curtailment. We first do the calculation for AC and
* LCC DC lines, then do it again for VSC (including the cost of a new converter in the source and
* sink BA), keeping whichever has lower cost/losses. vsc_required(r,rr) indicates the (r,rr) pairs
* for which VSC has lower cost/losses than AC and LCC DC, and is used in c_supplymodel to constrain
* CURT_REDUCT_TRANS to be less than INV_CONVERTER.
set vsc_required_input(r,rr) "BA pairs for which the optimal multi-link path for curtailment reduction uses VSC"
/
$offlisting
$ondelim
$include inputs_case%ds%trans-multilink-converters.csv
$offdelim
$onlisting
/ ;
vsc_required(r,rr)$[vsc_required_input(r,rr)$rfeas(r)$rfeas(rr)] = yes ;

* Written by input_processing/transmission_multilink.py, with input values in
* inputs/transmission/converter_vsc_bas_{GSw_VSC_BAlist}.csv
set val_converter_input(r) "BAs where VSC converter investment is allowed"
/
$offlisting
$ondelim
$include inputs_case%ds%transmission_vsc_regions.csv
$offdelim
$onlisting
/ ;
val_converter(r,t)$[(yeart(t)>=firstyear_trans)$val_converter_input(r)$rfeas(r)] = yes ;

* Written by input_processing/transmission_multilink.py, with input values in
* inputs/transmission/converter_vsc_bas_{GSw_VSC_LinkList}.csv
set routes_vsc(r,rr) "valid routes for VSC HVDC investment"
/
$offlisting
$ondelim
$include inputs_case%ds%transmission_vsc_routes.csv
$offdelim
$onlisting
/ ;

* Add VSC to the previously-created transmission sets and parameters
cost_tranline(r,"VSC") = cost_tranline(r,"DC") ;
trans_fom(r,"VSC") = trans_fom(r,"DC") ;
routes(r,rr,"VSC",t)$[(yeart(t)>=firstyear_trans)$rfeas(r)$rfeas(rr)$routes_vsc(r,rr)] = yes ;
routes_inv(r,rr,"VSC",t)$[(yeart(t)>=firstyear_trans)$rfeas(r)$rfeas(rr)$routes_vsc(r,rr)] = yes ;
* Include both directions
routes(rr,r,"VSC",t)$[(yeart(t)>=firstyear_trans)$rfeas(r)$rfeas(rr)$routes_vsc(r,rr)] = yes ;
routes_inv(rr,r,"VSC",t)$[(yeart(t)>=firstyear_trans)$rfeas(r)$rfeas(rr)$routes_vsc(r,rr)] = yes ;

$endif.vsc

* --- transmission $/MW ---
* Once we move to individual corridor costs (regional transmission costs * line-specific
* terrain modifiers) we'll read this parameter directly instead of calculating it as the
* average of the regional costs.
parameter transmission_line_capex(r,rr,trtype) "--$/MW-- transmission line capex between r and rr" ;
transmission_line_capex(r,rr,trtype)$[rfeas(r)$rfeas(rr)] =
  (cost_tranline(r,trtype) + cost_tranline(rr,trtype)) / 2 * distance(r,rr,trtype) ;

parameter transmission_line_fom(r,rr,trtype) "--$/MW/year-- transmission line FOM between r and rr" ;
transmission_line_fom(r,rr,trtype)$[rfeas(r)$rfeas(rr)] =
  (trans_fom(r,trtype) + trans_fom(rr,trtype)) / 2 * distance(r,rr,trtype) ;

*============================
*   --- Fuel Prices ---
*============================
*Note - NG supply curve has its own section

set f fuel types / 'dfo','rfo', 'naturalgas', 'coal', 'uranium', 'biomass', 'rect'/ ;

set fuel2tech(f,i) "mapping between fuel types and generations"
   /
   coal.(coal-new,CoalOldScr,coalolduns,coal-ccs,coal-igcc),

   naturalgas.(gas-cc,gas-ct,o-g-s,gas-cc-ccs),

   uranium.(nuclear,nuclear-smr)

   biomass.(biopower,beccs,cofirenew,cofireold)

   rect.(RE-CT,RE-CC)
   / ;

*double check in case any sets have been changed.
fuel2tech("coal",i)$coal(i) = yes ;
fuel2tech("naturalgas",i)$gas(i) = yes ;
fuel2tech("uranium",i)$nuclear(i) = yes ;
fuel2tech(f,i)$upgrade(i) = sum{ii$upgrade_to(i,ii), fuel2tech(f,ii) } ;


fuel2tech(f,i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), fuel2tech(f,ii) } ;

*===============================
*   Generator Characteristics
*===============================

set plantcat "categories for plant characteristics" / capcost, fom, vom, heatrate, rte / ;

* declared over allt to allow for external data files that extend beyond end_year
parameter plant_char0(i,allt,plantcat) "--units vary-- input plant characteristics"
/
$offlisting
$include inputs_case%ds%plantcharout.txt
$onlisting
/ ;

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

* Assign hybrid PV+battery to have the same value as battery_X
* PV outage rates are included in the PV capacity factors
forced_outage(i)$pvb(i) = forced_outage("battery_%GSw_pvb_dur%") ;
planned_outage(i)$pvb(i) = planned_outage("battery_%GSw_pvb_dur%") ;

forced_outage(i)$geo(i) = forced_outage("geothermal") ;
planned_outage(i)$geo(i) = planned_outage("geothermal") ;

planned_outage(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), planned_outage(ii) } ;

*upgrade plants assume the same planned outage of what theyre upgraded to
planned_outage(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), planned_outage(ii) } ;

forced_outage(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), forced_outage(ii) } ;

parameter avail(i,v,allh) "--fraction-- fraction of capacity available for generation by hour" ;

*upgrade plants assume the same forced outage of what theyre upgraded to
avail(i,v,h)$[sum{(r,t), valcap(i,v,r,t) }] = 1 ;
forced_outage(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), forced_outage(ii) } ;

* Assume no plant outages in the summer, adjust the planned outages to account for no planned outages in summer
avail(i,v,h)$[forced_outage(i) or planned_outage(i)] = (1 - forced_outage(i))
                              * (1 - planned_outage(i)$[not summerh(h)] * 365 / 273) ;

*Existing geothermal plants have a 75% availability rate based on historical capacity factors
avail(i,initv,h)$geo(i) = 0.75 ;

m_capacity_exog("smr","init-1",r,t) = m_capacity_exog("smr","init-1",r,t)
                                      / (sum((h),avail("smr","init-1",h) * hours(h)) / 8760 ) ;

*============================================
* -- Consume technologies specification --
*============================================

set H2_Routes(r,rr) "set of feasible trade corridors for hydrogen";
h2_routes(r,rr)$[sum{(trtype,t)$[routes(r,rr,trtype,t) or routes(rr,r,trtype,t)],1 }] = yes;

parameter cost_prod(i,v,r,t)                  "--$/tonne-- cost or benefit of producing output from consuming technologies"
          dac_conversion_rate(i)              "--tonne/MWh-- CO2 captured per MWh of electricity consumed"
          h2_conversion_rate(i,v,r,t)         "--tonne/MWh-- H2 produced per MWh of electricity consumed"
          prod_conversion_rate(i,v,r,t)       "--tonne/MWh-- amount of product produced (H2 or CO2) per MWh of electricity consumed"
          cost_h2_transport(r,rr)             "--$/tonne-- cost of H2 inter-BA transport pipeline"
;

scalar    h2_rect_intensity              "--tonne/MMBtu-- amount of hydrogen consumed per MMBtu of RE-CT fuel consumption"
          dac_vom_percentage             "--%-- percent of capex accounting for in opex"
;

* For smr consume_char0 has capital costs in $/kg/day and "ele_efficiency" of kWh/kg
* convert to $/MW by ($/kg/day) / (kwh/kg) * (1000 kWh/MWh) * (24 hr/day)
* divide by availability because the annual amount produced is a function of availability
* the same conversion applies to FOM
* use weighted average by hours for annual availability for smrs by year
plant_char0(i,t,"capcost")$smr(i) = deflator("2016") * consume_char0(i,t,"cost_cap") / consume_char0(i,t,"ele_efficiency") * (1000 * 24) /
  sum{v$ivt(i,v,t), (sum{h, hours(h)*avail(i,v,h) } / sum{h, hours(h) }) } ;
plant_char0(i,t,"fom")$smr(i) = deflator("2016") * consume_char0(i,t,"fom") / consume_char0(i,t,"ele_efficiency") * (1000 * 24) /
  sum{v$ivt(i,v,t), (sum{h, hours(h)*avail(i,v,h) } / sum{h, hours(h) }) } ;


*electrolyzers capcot just need to go from $/kW to $/MW
plant_char0("electrolyzer",t,"capcost") = deflator("2018") * consume_char0("electrolyzer",t,"cost_cap") * 1000 ;
plant_char0("electrolyzer",t,"fom") = deflator("2018") * consume_char0("electrolyzer",t,"fom") * 1000 ;

parameter dac_assumptions(*) "assumptions for DAC operations - conversion rates in MWh / MT initially, VOM is percentage of capital expense"
/
$ondelim
$include inputs_case%ds%dac_assumptions.csv
$offdelim
/;


* assuming 1500 kwh / mtco2 based on most-efficient estimate from
* table 1 in Fasihi et al. (2019): https://www.sciencedirect.com/science/article/pii/S0959652619307772
* note this also only for non-chemical/thermal DAC producers on the list
* could be between 1.5 and 2.79 MWh / metric tonne CO2 on the denominator, latter assumed in conservative case
dac_conversion_rate(i)$dac(i) = 1 / dac_assumptions("dac_conversion_rate_bau") ;
dac_vom_percentage = dac_assumptions("dac_vom_percentage_bau") ;

* switch to enable conservative DAC costs
if(Sw_DAC=2,
  dac_conversion_rate(i)$dac(i) = 1 / dac_assumptions("dac_conversion_rate_conservative") ;
  consume_char0("dac",t,"cost_cap") = consume_char0("dac",t,"cost_cap_conservative") ;
  dac_vom_percentage = dac_assumptions("dac_vom_percentage_conservative") ;
) ;

scalar euros_dollar "dollars per euro exchange rate from treasury department" /1.124/ ;
*source for euro conversion rate (took reciprocal of value):
* https://fiscal.treasury.gov/files/reports-statements/treasury-reporting-rates-exchange/ratesofexchangeasofdecember312019.pdf

* calculate VOM for DAC as a percentage of capital costs
* VOM for consume techs/cost_prod in units of $ per tonne, so
* this calculation needs to occur before converting capital costs from $ / tonnes to $ / MW
cost_prod(i,newv,r,t)$[dac(i)$valcap(i,newv,r,t)] = euros_dollar * deflator("2019") *
    dac_vom_percentage * (sum(tt$ivt(i,newv,tt),consume_char0("dac",tt,"cost_cap") ) / countnc(i,newv)) ;

* DAC capital costs go from [euros] / t-year to $ / MW
* convert by ($ / (t / year)) * (t / MWh) * (8760 hours / year)
* see Table 4 in Fasihi et al. (2019): https://www.sciencedirect.com/science/article/pii/S0959652619307772
plant_char0("dac",t,"capcost") = euros_dollar * deflator("2019") * consume_char0("dac",t,"cost_cap") * dac_conversion_rate("dac") * 8760 ;

*plant_char cannot be conditioned with valcap or valgen here since the plant_char for unmodeled years is being
*used in calculations of heat_rate, cost_vom, and cost_fom and thus cannot be zeroed out
*plant_char is indexed with v since cooling cost/technology performance multipliers only apply to new builds
parameter plant_char(i,v,t,plantcat) "--various units-- plant characteristics such as cap, vom, fom costs and heat rates";
plant_char(i,v,t,plantcat) = plant_char0(i,t,plantcat) ;

* -- Consuming Technologies costs and demands --

set i_p(i,p)
/
dac.dac,
electrolyzer.(h2_blue,h2_green),
smr.h2_blue,
smr_ccs.(h2_blue,h2_green)
/ ;


set i_h2type(i,p)   "designation of technologies to H2 type"
/
electrolyzer.(h2_blue,h2_green),
smr.h2_blue,
smr_ccs.(h2_blue,h2_green)
/ ;


* see note from earlier... converting from MT / MWh from kg / kWh does not require adjustment..
* but we still need to convert from MWh / MT to MT / MWh <- could choose either units
* just need to make sure we change signs throughout
h2_conversion_rate(i,newv,r,t)$[h2(i)$valcap(i,newv,r,t)] =
    1 / (sum{tt$ivt(i,newv,tt),consume_char0(i,tt,"ele_efficiency") } / countnc(i,newv) ) ;

h2_conversion_rate(i,initv,r,t)$[h2(i)$valcap(i,initv,r,t)] =
    1 / consume_char0(i,"2010","ele_efficiency") ;

prod_conversion_rate(i,v,r,t)$[consume(i)$valcap(i,v,r,t)] =
    h2_conversion_rate(i,v,r,t)$h2(i) + dac_conversion_rate(i)$dac(i) ;

* energy intensity (52,217 btu / lb) is from:
* https://www.nrel.gov/docs/gen/fy08/43061.pdf
* need to get from Btu / lb to tonne / MMBtu
* (1/(btu/lb)) * (tonne / lb) * (Btu / MMBtu) = tonne / MMBtu
h2_rect_intensity = (1/52217) * (1/2204.62) * 1e6 ;

*"--tonnes CO2-- emissions from SMR activities"
*"The median CO2 emission normalized for SMR hydrogen production was 9 kg CO2/kg H2 production, or 75 g
* CO2/MJ H2 (using H2 low heating value [LHV]). The median emission is similar with the value of 9.26 kg CO2/kg H2
* in GREET 2018, which was based on the H2A modeling by Rutkowski et al (2012).”
* from: https://greet.es.anl.gov/publication-smr_h2_2019
* Actual emissions value of 9.83 and 90% capture rate based on a 2011 NETL study (DOE/NETL-2011/1434)
scalar smr_co2_intensity "--tonnes CO2 / tonnes H2-- emissions rate for SMR H2 production, SMR_CCS assumed at smr_capture_rate" /9.83/,
       smr_capture_rate  "--percent-- capture rate of CO2 for SMR with CCS" /0.90/ ;

* here converting from $/kg-mi to $/tonne via multiplication of miles and kg/tonne
*That value is based on the calculation in https://www.nrel.gov/docs/fy21osti/77610.pdf
* default value of 2.2 $2016 / tonne-mi is from $0.39/kg for long distance (250 km)
* = $0.39/kg / (250 km * 0.62 mile/km) = $0.0025 / kg-mile
cost_h2_transport(r,rr)$H2_Routes(r,rr) = deflator ("2016") * Sw_H2_Transport_Cost
                                          * max(distance(r,rr,"DC"), distance(r,rr,"AC")) ;


*======================================================
* -- Cooling water cost and performance adjustments --
*======================================================

*CSP with Storage costs assume dry cooling removing 5% cost adder
ctt_cost_vom_mult(i,ctt)$[(csp1(i) or csp2(i) or csp3(i) or csp4(i))$i_numeraire(i)] = 1 ;
ctt_cc_mult(i,ctt)$[(csp1(i) or csp2(i) or csp3(i) or csp4(i))$i_numeraire(i)] = 1 ;

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


*==================================
* --- PV+Battery Configurations ---
*==================================

parameter ilr_pvb_config(pvb_config) "--unitless-- inverter loading ratio for each hybrid pv+battery configuration"
/
$offlisting
$ondelim
$include inputs_case%ds%pvb_ilr.csv
$offdelim
$onlisting
/ ;

parameter ilr(i) "--unitless-- inverter loading ratio - used to convert DC capacity to AC capacity for PV" ;
* assign a default value of 1.0 for every technology (used in e_report.gms)
ilr(i) = 1 ;
ilr(i)$[upv(i) or dupv(i)] = 1.3 ;
ilr(i)$[sameas(i,"distpv")] = 1.1 ;
* assign an ILR to hybrid PV+battery technologies based on the ILR for the configurations
ilr(pvb) = sum{pvb_config$pvb_agg(pvb_config,pvb), ilr_pvb_config(pvb_config) } ;

parameter bcr_pvb_config(pvb_config) "--unitless-- ratio of the battery capacity to the inverter capacity (MW_battery / MW_inverter) for each hybrid pv+battery configuration"
/
$offlisting
$ondelim
$include inputs_case%ds%pvb_bcr.csv
$offdelim
$onlisting
/ ;

* Assign a battery capacity ratio to each hybrid PV+battery technology
parameter bcr(i) "--unitless-- ratio of the battery capacity to the inverter capacity (battery capacity ratio)" ;
bcr(pvb) = sum{pvb_config$pvb_agg(pvb_config,pvb), bcr_pvb_config(pvb_config) } ;
bcr(i)$[storage_standalone(i) or hyd_add_pump(i)] = 1 ;

*=========================================
* --- Capital costs ---
*=========================================

parameter cost_cap(i,t)     "--2004$/MW-- overnight capital costs",
          cost_upgrade(i,t) "--2004$/MW-- overnight costs of upgrading to tech i"  ;

cost_cap(i,t) = plant_char0(i,t,"capcost") ;

cost_cap(i,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{(ii,ctt)$[ctt_i_ii(i,ii)$i_ctt(i,ctt)], ctt_cc_mult(ii,ctt)*plant_char0(ii,t,"capcost") } ;

* Assign csp-ns to have the same value as csp2
cost_cap(i,t)$cspns(i) = cost_cap("csp2_1",t) ;

* Assign hybrid PV+battery to have the same value as UPV
parameter cost_cap_pvb_p(i,t) "--2004$/MW-- overnight capital costs for PV portion of hybrid PV+battery" ;
cost_cap_pvb_p(i,t)$pvb(i) =  sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap(ii,t) } ;

* Assign hybrid PV+battery to have the same value as battery_X
parameter cost_cap_pvb_b(i,t) "--2004$/MW-- overnight capital costs for battery portion of hybrid PV+battery" ;
cost_cap_pvb_b(i,t)$pvb(i) = cost_cap("battery_%GSw_pvb_dur%",t) ;

* declared over allt to allow for external data files that extend beyond end_year
table geocapmult(allt,geotech) "geothermal category capital cost multipliers over time"
$offlisting
$ondelim
$include inputs_case%ds%geocapcostmult.csv
$offdelim
$onlisting
;

table hydrocapmult(allt,i) "hydorpower capital cost multipliers over time"
$offlisting
$ondelim
$include inputs_case%ds%hydrocapcostmult.csv
$offdelim
$onlisting
;

table ofswind_rsc_mult(allt,i) "multiplier by year for supply curve cost"
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

cost_cap(i,t)$dupv(i) = sum{ii$dupv_upv_corr(ii,i),cost_cap(ii,t) } * dupv_cost_cap_mult ;


*====================
* --- Variable OM ---
*====================

*only one vom cost for hydro
scalar vom_hyd "--2004$/MWh-- hydropower VOM" /1.024417098/ ;

parameter cost_vom(i,v,r,t) "--2004$/MWh-- variable OM" ;

cost_vom(i,initv,r,t)$[(not Sw_BinOM)$valgen(i,initv,r,t)] = plant_char(i,initv,'2010','vom') ;

*if binning historical plants cost_vom, still need to assign default values to new plants
cost_vom(i,newv,r,t)$[(Sw_BinOM)$valgen(i,newv,r,t)] = plant_char(i,newv,t,'vom') ;

*if binning VOM and FOM costs, use the values written by writehintage.py for existing plants
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

* Assign hybrid PV+battery to have the same value as UPV
parameter cost_vom_pvb_p(i,v,r,t) "--2004$/MWh-- variable OM for the PV portion of hybrid PV+battery " ;
cost_vom_pvb_p(i,v,r,t)$pvb(i) =  sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_vom(ii,v,r,t) } ;

* Assign hybrid PV+battery to have the same value as Battery_X
parameter cost_vom_pvb_b(i,v,r,t) "--2004$/MWh-- variable OM for the battery portion of hybrid PV+battery " ;
cost_vom_pvb_b(i,v,r,t)$pvb(i) =  cost_vom("battery_%GSw_pvb_dur%",v,r,t) ;

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
cost_fom(i,initv,r,t)$[Sw_BinOM$(not cost_fom(i,initv,r,t))$valcap(i,initv,r,t)] =
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

parameter geo_fom_reduction(i,allt) "--fraction-- ratio of cost reduction relative to 2010"
/
$offlisting
$ondelim
$include inputs_case%ds%%geoscen%_FOM.csv
$offdelim
$onlisting
/
;

*Convert geothermal FOM from 2015$ to 2004$ and from $/kW-yr to $/MW-yr
geo_fom(i,r) = geo_fom(i,r) * deflator('2015') * 1000 ;

*fom costs for a specific bintage is the average over that bintage's time frame
cost_fom(i,newv,r,t)$[valcap(i,newv,r,t)$countnc(i,newv)] =
  sum{tt$ivt(i,newv,tt), plant_char(i,newv,tt,'fom')  } / countnc(i,newv) ;

* Assign hybrid PV+battery to have the same value as UPV
parameter cost_fom_pvb_p(i,v,r,t) "--2004$/MW-yr-- fixed OM for the PV portion of hybrid PV+battery " ;
cost_fom_pvb_p(i,v,r,t)$pvb(i) =  sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_fom(ii,v,r,t) } ;

* Assign hybrid PV+battery to have the same value as Battery_X
parameter cost_fom_pvb_b(i,v,r,t) "--2004$/MW-yr-- fixed OM for the battery portion of hybrid PV+battery " ;
cost_fom_pvb_b(i,v,r,t)$pvb(i) =  cost_fom("battery_%GSw_pvb_dur%",v,r,t) ;

cost_fom(i,v,r,t)$[valcap(i,v,r,t)$pvb(i)] = cost_fom_pvb_p(i,v,r,t) + bcr(i) * cost_fom_pvb_b(i,v,r,t) ;

* -- FOM adjustments for nuclear plants
* Nuclear FOM cost adjustments are from the report from the IPM team titled
* 'Nuclear Power Plant Life Extension Cost Development Methodology' which indicates
* $1.25/kw increase per year for the first 10 years
* $1.81/kW increase per year for years 10-50
* $0.56/kW increase per year for year 50+
* A single step reduction of $25/kW in year 50
* These are applied in ReEDS relative to 2019 (i.e., cost escalations are applied beginnning in 2020)

* declared over allt to allow for external data files that extend beyond end_year
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
  cost_fom(i,initv,r,t) + sum{allt$att(allt,t),FOM_adj_nuclear(allt) }$Sw_NukeCoalFOMAdj ;

cost_fom(i,initv,r,t)$[Sw_BinOM$valcap(i,initv,r,t)$coal(i)] =
  cost_fom(i,initv,r,t) + sum{allt$att(allt,t),FOM_adj_coal(allt) }$Sw_NukeCoalFOMAdj ;


*note conditional here that will only replace fom
*for hydro techs if it is included in hyd_fom(i,r)
cost_fom(i,v,r,t)$[valcap(i,v,r,t)$hydro(i)$hyd_fom(i,r)] = hyd_fom(i,r) ;

cost_fom(i,v,rb,t)$[valcap(i,v,rb,t)$geo(i)] = geo_fom(i,rb) * geo_fom_reduction(i,t) ;

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

*from KE's original model
parameter heat_rate_init(r,i) "initial heat rate"
/
$offlisting
$ondelim
$include inputs_case%ds%heat_rate_init.csv
$offdelim
$onlisting
/
;

heat_rate_init(r,i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), heat_rate_init(r,ii) } ;

parameter heat_rate(i,v,r,t) "--MMBtu/MWh-- heat rate" ;

heat_rate(i,v,r,t)$valcap(i,v,r,t) = plant_char(i,v,t,'heatrate') ;

heat_rate(i,newv,r,t)$[valcap(i,newv,r,t)$countnc(i,newv)] =
      sum{tt$ivt(i,newv,tt), plant_char(i,newv,tt,'heatrate') } / countnc(i,newv) ;

heat_rate(i,v,r,t)$[CONV(i) and initv(v) and capacity_exog(i,v,r,t) and rb(r)] = heat_rate_init(r,i) ;

* fill in heat rate for initial capacity that does not have a binned heatrate
heat_rate(i,initv,r,t)$[valcap(i,initv,r,t)$(not heat_rate(i,initv,r,t))] =  plant_char(i,initv,'2010','heatrate') ;

*note here conversion from btu/kwh to MMBtu/MWh
heat_rate(i,v,r,t)$[valcap(i,v,r,t)$sum{allt$att(allt,t), binned_heatrates(i,v,r,allt) }] =
                    sum{allt$att(allt,t), binned_heatrates(i,v,r,allt) } / 1000 ;

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

parameter fuel_price(i,r,t) "$/MMBtu - fuel prices by technology" ;


*written by input_processing\fuelcostprep.py
* declared over allt to allow for external data files that extend beyond end_year
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

* fuel price for RE-CT is accounted for as the marginal off h2 demand equations
* and thus can be removed when Sw_H2 = 1 and the year is beyond Sw_H2_Start
fuel_price(i,r,t)$[re_ct(i)$Sw_H2$(yeart(t)>=Sw_H2_Start)] = 0 ;

*==============================================
* --- Capacity Factors ---
*==============================================

parameter cf_rsc(i,v,r,allh,t) "--fraction-- capacity factor for rsc tech - t index included for use in CC/curt calculations" ;

*begin capacity factor calculations

*created by /input_processing/R/cfgather.R
table cf_in(r,i,allh) "--fraction-- capacity factors for renewable technologies - wind CFs get adjusted below"
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
cf_rsc(i,v,r,h,t)$[cf_in(r,i,h)$cf_tech(i)$valcap(i,v,r,t)] = cf_in(r,i,h) ;

*created by /input_processing/writecapdat.py
parameter cf_hyd_input(i,allszn,r) "hydro capacity factors by season"
/
$offlisting
$include inputs_case%ds%hydcf.txt
$onlisting
/ ;

* time-varying hydro CF starts with same value for all years; adjusted if climate impacts on hydro are included
parameter cf_hyd(i,allszn,r,t) "hydro capacity factors by season and year" ;
cf_hyd(i,szn,r,t) = cf_hyd_input(i,szn,r) ;

*** Climate impacts on nondispatchable hydropower
$ifthen.climatehydro %GSw_ClimateHydro% == 1

* declared over allt to allow for external data files that extend beyond end_year
table climate_hydro_annual(r,allt)  "annual dispatchable hydropower availability"
$offlisting
$ondelim
$include inputs_case%ds%climate_hydadjann.csv
$offdelim
$onlisting
;


table climate_hydro_seasonal(r,allszn,allt)  "annual/seasonal nondispatchable hydropower availability"
$offlisting
$ondelim
$include inputs_case%ds%climate_hydadjsea.csv
$offdelim
$onlisting
;

* adjust cf_hyd based on annual/seasonal climate multipliers
* non-dispatchable hydro gets new seasonal profiles as well as annually-varying CF
* dispatchable hydro keeps the original seasonal profiles; only annual CF changes. Reflects the assumption
* that reservoirs will be utilized in the same seasonal pattern even if seasonal inflows change.
cf_hyd(i,szn,r,t)$[hydro_nd(i)$(yeart(t)>=climateyear)] =
    sum{allt$att(allt,t), cf_hyd(i,szn,r,t) * climate_hydro_seasonal(r,szn,allt) } ;

cf_hyd(i,szn,r,t)$[hydro_d(i)$(yeart(t)>=climateyear)]  =
    sum{allt$att(allt,t), cf_hyd(i,szn,r,t) * climate_hydro_annual(r,allt) } ;

$endif.climatehydro


*created by /input_processing/writecapdat.py
parameter cap_hyd_szn_adj(i,allszn,r) "seasonal max capacity adjustment for dispatchable hydro"
/
$offlisting
$include inputs_case%ds%hydcfadj.txt
$onlisting
/ ;

*created by /input_processing/writecapdat.py
parameter cfhist_hyd(r,allt,allszn,i) "seasonal adjustment for capacity factors - same as hydhistcfadj from heritage"
/
$offlisting
$include inputs_case%ds%hydcfhist.txt
$onlisting
/ ;

* only need to compute this for rs==sk... otherwise gets yuge
* dispatchable hydro has a separate constraint for seasonal generation which uses m_cf_szn
cf_rsc(i,v,r,h,t)$[hydro(i)$valcap(i,v,r,t)] = sum{szn$h_szn(h,szn), cf_hyd(i,szn,r,t) } ;


table wind_cf_adj_t(allt,i) "--unitless-- wind capacity factor adjustments by class, from ATB"
$offlisting
$ondelim
$include inputs_case%ds%windcfout.csv
$offdelim
$onlisting
;

parameter pv_cf_improve(allt) "--unitless-- PV capacity factor improvement"
/
$offlisting
$ondelim
$include inputs_case%ds%pv_cf_improve.csv
$offdelim
$onlisting
/
;

parameter cf_adj_t(i,v,t)        "--unitless-- capacity factor adjustment over time for RSC technologies",
          cf_adj_hyd(r,i,allh,t) "--unitless-- capacity factor adjustment over time for hydro technologies" ;

cf_adj_t(i,v,t)$[(rsc_i(i) or hydro(i) or csp_nostorage(i))$sum{r, valcap(i,v,r,t) }] = 1 ;

* Existing wind uses 2010 cf adjustment
cf_adj_t(i,initv,t)$[wind(i)$sum{r, valcap(i,initv,r,t) }] = wind_cf_adj_t("2010",i) ;

cf_adj_t(i,newv,t)$[wind_cf_adj_t(t,i)$countnc(i,newv)$sum{r, valcap(i,newv,r,t) }] =
          sum{tt$ivt(i,newv,tt), wind_cf_adj_t(tt,i) } / countnc(i,newv) ;

* Apply PV capacity factor improvements
cf_adj_t(i,newv,t)$[(pv(i) or pvb(i))$countnc(i,newv)$sum{r, valcap(i,newv,r,t) }] =
          sum{tt$ivt(i,newv,tt), pv_cf_improve(tt) } / countnc(i,newv) ;

*if not set, set it to one
cfhist_hyd(r,t,szn,i)$[(not cfhist_hyd(r,t,szn,i))$hydro(i)$valcap_irt(i,r,t)] = 1 ;
*odd, historical years are the average of the surrounding even years. We could add data for odd historical years if needed.
cfhist_hyd(r,t,szn,i)$[oddyears(t)$(yeart(t)<=2015)] = (cfhist_hyd(r,t-1,szn,i) + cfhist_hyd(r,t+1,szn,i)) / 2 ;
*adjustment is the corresponding seasonal historical value
cf_adj_hyd(r,i,h,t)$hydro(i) = sum{szn$h_szn(h,szn),cfhist_hyd(r,t,szn,i) } ;

cf_rsc(i,v,r,h,t)$[rsc_i(i)$(sum{tt, capacity_exog(i,v,r,tt) })] =
        cf_rsc(i,"init-1",r,h,t) ;


*Upgraded hydro parameters:
* By default, capacity factors for upgraded hydro techs use what we upgraded from.
cf_hyd(i,szn,r,t)$[upgrade(i)$rfeas(r)$(hydro(i) or psh(i))] =
    sum{ii$upgrade_from(i,ii), cf_hyd(ii,szn,r,t) } ;
cfhist_hyd(r,t,szn,i)$[upgrade(i)$rfeas(r)$(hydro(i) or psh(i))] =
    sum{ii$upgrade_from(i,ii), cfhist_hyd(r,t,szn,ii) } ;
* For cap_hyd_szn_adj, which only applies to dispatchable hydro or upgraded disp hydro with added pumping, we first try using the from-tech, but if that is
* not available we use to to-tech, and if not that either we just use 1.
cap_hyd_szn_adj(i,szn,r)$[upgrade(i)$rfeas(r)$(hydro_d(i) or psh(i))] =
    sum{ii$upgrade_from(i,ii), cap_hyd_szn_adj(ii,szn,r) } ;
cap_hyd_szn_adj(i,szn,r)$[upgrade(i)$rfeas(r)$hydro_d(i)$(not cap_hyd_szn_adj(i,szn,r))] =
    sum{ii$upgrade_to(i,ii), cap_hyd_szn_adj(ii,szn,r) } ;
cap_hyd_szn_adj(i,szn,r)$[upgrade(i)$rfeas(r)$hydro_d(i)$(not cap_hyd_szn_adj(i,szn,r))] = 1 ;

* Capacity factors for CSP-ns are developed using typical DNI year (TDY) hourly resource data (Habte et al. 2014) from 18 representative sites.
* The TDY weather files are processed through the CSP modules of SAM to develop performance characteristics for a system with a solar multiple of 1.4.
* These representative sites have an average DNI range of 7.25-7.5 kWh/m2/day (see "Class 3" in Table 4 of the ReEDS Model Documnetation: Version 2016).
* Habte, A., A. Lopez, M. Sengupta, and S. Wilcox. 2014. Temporal and Spatial Comparison of Gridded TMY, TDY, and TGY Data Sets. Golden, CO: National Renewable Energy Laboratory. http://www.osti.gov/scitech/biblio/1126297.
parameter cf_cspns(allh) "--unitless-- time-slice capacity factors for csp without storage"
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
cf_rsc(i,v,r,h,t)$[cspns(i)$valcap(i,v,r,t)] = cf_cspns(h) * avail_cspns ;


*demand response capacity factors currently created manually
$onempty
parameter dr_inc(i,r,allh) "--unitless-- average capacity factor for dr reduction in load in timeslice h"
/
$offlisting
$ondelim
$include inputs_case%ds%dr_increase.csv
$offdelim
$onlisting
$offempty
/
;

$onempty
parameter dr_dec(i,r,allh) "--unitless-- average capacity factor for dr increase in load in timeslice h"
/
$offlisting
$ondelim
$include inputs_case%ds%dr_decrease.csv
$offdelim
$onlisting
$offempty
/
;

*========================================
*      --- OPERATING RESERVES ---
*========================================


set ortype                    "types of operating reserve constraints" /flex, reg, spin/,
    orcat                     "operating reserve category for RHS calculations" /or_load, or_wind, or_pv/,
    dayhours(allh)            "daytime hours, used to limit PV capacity to the daytime hours" /h2*h4,h6*h8,h10*h12,h14*h16,h17/,
    hour_szn_group(allh,allh) "h and hh in the same season - used in minloading constraint" ;

hour_szn_group(h,hh)$sum{szn$(h_szn(h,szn)$h_szn(hh,szn)), 1 } = yes ;

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

* multiplier for reserves requirement
orperc(ortype,orcat) = orperc(ortype,orcat) * Sw_ResReqMultiplier ;

*ramp rates are used to limit a technology's contribution to Operating Reserve.
parameter ramprate(i) "--fraction/min-- ramp rate of dispatchable generators"
/
$offlisting
$ondelim
$include inputs_case%ds%ramprate.csv
$offdelim
$onlisting
/
;

*dispatchable hydro is the only "hydro" technology that can provide operating reserves.
ramprate(i)$hydro_d(i) = ramprate("hydro") ;
ramprate(i)$geo(i) = ramprate("geothermal") ;

*if running with flexible nuclear, set ramp rate of nuclear to that of coal
ramprate(i)$[nuclear(i)$Sw_NukeFlex] = ramprate("coal-new") ;

ramprate(i)$upgrade(i) = sum{ii$upgrade_to(i,ii), ramprate(ii) } ;

ramprate(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), ramprate(ii) } ;

* Do not allow the reserve fraction to exceed 100%, so use the minimum of 1 or the computed value.
reserve_frac(i,ortype) = min(1,ramprate(i) * ramptime(ortype)) ;
*Only allow DR to provide reserves if the switch to do so is on
reserve_frac(i,ortype)$[dr(i)$(not Sw_DRReserves)] = 0 ;

reserve_frac(i,ortype)$upgrade(i) = sum{ii$upgrade_to(i,ii), reserve_frac(ii,ortype) } ;

* input data for opres reserve costs by generator type (in $2004)
* current options are bottom up costs by generator type ("default") or estimates based on historical reserve prices ("market")
* market data based on national reserve prices in https://www.nrel.gov/docs/fy19osti/72578.pdf (converted from $2017)
table cost_opres_input(i,ortype)
$offlisting
$ondelim
$include inputs_case%ds%cost_opres_%GSw_OpResCost%.csv
$offdelim
$onlisting
;

parameter cost_opres(i,ortype,t) "--$ / MWh-- cost of reg operating reserves" ;
cost_opres(i,ortype,t) = cost_opres_input(i, ortype) ;

* assign reserve costs to all geothermal techs
cost_opres(i,ortype,t)$geo(i) = cost_opres("geothermal",ortype,t) ;

* Assign hybrid PV+battery the same value as battery_X
cost_opres(i,ortype,t)$pvb(i) = cost_opres("battery_%GSw_pvb_dur%",ortype,t) ;

* add heat rate penalty for providing reserves (currently only applied to spin)
* input data calculated based on heat rates in the PLEXOS EI database as of Dec. 2020
parameter spin_hr_penalty(i) "--fraction-- heat rate penalty for providing spinning reserves"
/
$offlisting
$ondelim
$include inputs_case%ds%heat_rate_penalty_spin.csv
$offdelim
$onlisting
/
;
* calculate average heat rate and fuel prices
parameter fuel_price_avg(i,t) ;
parameter heat_rate_avg(i,t) ;

* calculate average fuel price and heat rates
fuel_price_avg(i,t)$[sum{r, fuel_price(i,r,t) }] = sum{r, fuel_price(i,r,t) } / sum{r, 1$[fuel_price(i,r,t)] } ;

heat_rate_avg(i,t)$[sum{(v,r), heat_rate(i,v,r,t) }] =
  sum{(v,r), heat_rate(i,v,r,t) } / sum{(v,r), 1$[heat_rate(i,v,r,t)] } ;

* calculate penalty value, assign to cost_opres
* only assign penalty in instances where spin costs are not already defined
cost_opres(i,"spin",t)$[not cost_opres(i,"spin",t)] =
  spin_hr_penalty(i) * heat_rate_avg(i,t) * fuel_price_avg(i,t) ;

cost_opres(i,ortype,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_opres(ii,ortype,t) } ;

cost_opres(i,ortype,t)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), cost_opres(ii,ortype,t) } ;

*reg_energy_frac is from Page 7 (pdf page 16) of https://www.nrel.gov/docs/fy14osti/60568.pdf
scalar reg_energy_frac "--fraction-- fraction of regulating reserves that produces energy" /0.15/ ;

Scalar mingen_firstyear "--integer-- first year for mingen considerations" /2020/ ;

parameter minloadfrac(r,i,allh) "--fraction-- minimum loading fraction - final used in model",
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
table hydmin(i,r,allszn) "minimum hydro loading factors by season and region"
$offlisting
$ondelim
$include inputs_case%ds%minhyd.csv
$offdelim
$onlisting
;

minloadfrac(r,i,h) = minloadfrac0(i) ;

* adjust nuclear mingen to 40% if running with flexible nuclear
minloadfrac(r,i,h)$[nuclear(i)$Sw_NukeFlex] = 0.4 ;

minloadfrac(r,i,h)$CSP(i) = 0.15 ;
minloadfrac(r,i,h)$[coal(i)$(not minloadfrac(r,i,h))] = 0.5 ;
minloadfrac(r,i,h)$[sum{szn$h_szn(h,szn), hydmin(i,r,szn ) }] = sum{szn$h_szn(h,szn), hydmin(i,r,szn) } ;
minloadfrac(r,i,h)$upgrade(i) = sum{ii$upgrade_to(i,ii), minloadfrac(r,ii,h) } ;

minloadfrac(r,i,h)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), minloadfrac(r,ii,h) } ;

minloadfrac(r,i,h)$[not sum{(v,t), valcap(i,v,r,t) }] = 0 ;



*=========================================
*              --- Load ---
*=========================================

set h_szn_prm(allh,allszn) "hour to season linkage for nd_hydro in the planning reserve margin constraint"
/
h3.summ
h7.fall
h11.wint
h15.spri
/ ;

parameter demchange(t)   "demand change in t relative to 2015",
          load_exog(r,allh,t)    "--MW-- busbar load",
          load_exog0(r,allh,t)   "original load by region hour and year - unchanged by demand side" ;



parameter peakdem_h17_ratio(r,allszn,t) "recording of original ratio between peak demand and h17" ;

table load_2010(r,allh) "--MW-- 2010 end-use load by time slice"
$offlisting
$ondelim
$include inputs_case%ds%load_2010.csv
$offdelim
$onlisting
;

* declared over allt to allow for external data files that extend beyond end_year
table load_multiplier(cendiv,allt) "--unitless-- relative load growth from 2010"
$offlisting
$ondelim
$include inputs_case%ds%load_multiplier.csv
$offdelim
$onlisting
;

* If using default load with no climate impacts, calculate future load from load_multiplier
$ifthen.allyearload '%GSw_EFS1_AllYearLoad%%GSw_ClimateDemand%' == 'default0'
*Dividing by (1-distloss) converts end-use load to busbar load
load_exog(r,h,t) = load_2010(r,h) * sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t) } / (1.0 - distloss) ;
* Otherwise if using EFS load or climate impacts, import the yearly load directly
$else.allyearload
table load_allyear(r,allh,allt) "--MW-- 2010 to 2050 (or endyear) end use load by time slice for use with EFS profiles"
$offlisting
$ondelim
$include inputs_case%ds%load_all.csv
$offdelim
$onlisting
;
load_exog(r,h,t) = load_allyear(r,h,t)/ (1.0 - distloss) ;
$endif.allyearload

table canmexload(r,allh) "load for canadian and mexican regions"
$offlisting
$ondelim
$include inputs_case%ds%canmexload.csv
$offdelim
$onlisting
;

table can_growth_rate(st,allt) "growth rate for candadian demand"
$offlisting
$ondelim
$include inputs_case%ds%cangrowth.csv
$offdelim
$onlisting
;

parameter mex_growth_rate(allt) "growth rate for mexican demand"
/
$offlisting
$ondelim
$include inputs_case%ds%mex_growth_rate.csv
$offdelim
$onlisting
/
;

load_exog(r,h,t)$sum{st$r_st(r,st),can_growth_rate(st,t) } =
      canmexload(r,h) * sum{st$r_st(r,st),can_growth_rate(st,t) } ;

load_exog(r,h,t)$r_country(r,"MEX") = mex_growth_rate(t) * canmexload(r,h) ;

*-- PHEV demand
* static demand is exogenously-imposed and added directly to load_exog
* whereas dynamic demand is flexible and based on seasonal amounts
* which can be shifted from one timeslice to another

parameter ev_static_demand(r,allh,allt) "--MWh-- static electricity load from EV charging by timeslice"
$offlisting
/
$ondelim
$include inputs_case%ds%ev_static_demand.csv
$offdelim
/
$onlisting
;

parameter ev_dynamic_demand(r,allszn,allt) "--MWh-- dynamic load from EV charging by season that is assigned by the model to timeslices"
$offlisting
/
$ondelim
$include inputs_case%ds%ev_dynamic_demand.csv
$offdelim
/
$onlisting
;

*-- EFS flexibility

table flex_frac_load(flex_type,r,allh,allt)
$offlisting
$ondelim
$include inputs_case%ds%flex_frac_all.csv
$offdelim
$onlisting
;

parameter flex_demand_frac(flex_type,r,allh,t) "fraction of load able to be considered flexible";


* assign zero values to avoid unassigned parameter errors
flex_demand_frac(flex_type,r,h,t)$rfeas(r) = 0 ;
flex_demand_frac(flex_type,r,h,t)$[Sw_EFS_Flex$rfeas(r)] = flex_frac_load(flex_type,r,h,t) ;


parameter peak_static_frac(r,allszn,t) "--fraction-- fraction of peak demand that is static" ;
peak_static_frac(r,szn,t) = 1 - sum{(flex_type,h)$h_szn_prm(h,szn), flex_demand_frac(flex_type,r,h,t) } ;

*static EV demand is added directly to load_exog
load_exog(r,h,t)$(Sw_EV) = load_exog(r,h,t) + ev_static_demand(r,h,t) ;

* load in odd years is the average between the two surrounding even years
load_exog(r,h,t)$[oddyears(t)$(not load_exog(r,h,t))] = (load_exog(r,h,t-1)+load_exog(r,h,t+1)) / 2 ;

*initial values are set here (after SwI_Load has been accounted for)
load_exog0(r,h,t) = load_exog(r,h,t) ;

parameter
load_exog_flex(flex_type,r,allh,t)    "the amount of exogenous load that is flexibile"
load_exog_static(r,allh,t)            "the amount of exogenous load that is static" ;

load_exog_flex(flex_type,r,h,t) = load_exog(r,h,t) * flex_demand_frac(flex_type,r,h,t) ;
load_exog_static(r,h,t) = load_exog(r,h,t) - sum{flex_type, load_exog_flex(flex_type,r,h,t) } ;



parameter
maxload_szn(r,allh,t,allszn)   "maximum load by season - used to determine hour with highest load within each szn",
mload_exog_szn(r,t,allszn)  "maximum load by season - placeholder for calculation hour_szn_group",
load_exog_szn(r,allh,t,allszn) "maximum load by season - placeholder for calculation hour_szn_group" ;


load_exog_szn(r,h,t,szn)$[h_szn(h,szn)$rfeas(r)] = load_exog(r,h,t) ;
mload_exog_szn(r,t,szn)$rfeas(r) = smax(hh$[not sameas(hh,"h17")],load_exog_szn(r,hh,t,szn)) ;
maxload_szn(r,h,t,szn)$[(load_exog_szn(r,h,t,szn)=mload_exog_szn(r,t,szn))$rfeas(r)] = yes ;



*==============================
* --- Peak Load ---
*==============================

*written by input_processing\R\\writeload.R
table peakdem_2010(r,allszn) "--MW-- end use peak demand in 2010 by season"
$offlisting
$ondelim
$include inputs_case%ds%peak_2010.csv
$offdelim
$onlisting
;

parameter peakdem_static_szn(r,allszn,t) "--MW-- bus bar peak demand by season" ;

* declared over allt to allow for external data files that extend beyond end_year
table peak_allyear(r,allszn,allt) "--MW-- 2010 to 2050 (or endyear) peak load by season for use with EFS profiles"
$offlisting
$ondelim
$include inputs_case%ds%peak_all.csv
$offdelim
$onlisting
;


* If using default load with no climate impacts, calculate future load from load_multiplier
$ifthen.allyearpeak '%GSw_EFS1_AllYearLoad%%GSw_ClimateDemand%' == 'default0'
*Dividing by (1-distloss) converts end-use load to busbar load
peakdem_static_szn(r,szn,t) = peakdem_2010(r,szn) * peak_static_frac(r,szn,t)
                              * sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t) } / (1.0 - distloss) ;

* Otherwise if using EFS load or climate impacts, import the yearly load directly
$else.allyearpeak
peakdem_static_szn(r,szn,t) = peak_allyear(r,szn,t) * peak_static_frac(r,szn,t) / (1.0 - distloss) ;
$endif.allyearpeak

parameter peakdem_static_h(r,allh,t) "--MW-- bus bar peak demand by time slice for use with EFS profiles" ;

table peak_allyear_static(r,allh,allt)
$offlisting
$ondelim
$include inputs_case%ds%h_peak_all.csv
$offdelim
$onlisting
;

* If using default load with no climate impacts, calculate future load from load_multiplier
$ifthen.allyearpeakstatic '%GSw_EFS1_AllYearLoad%%GSw_ClimateDemand%' == 'default0'
peakdem_static_h(r,h,t) = peak_allyear_static(r,h,'2010') * sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t) }
                          * (1 - sum{flex_type, flex_demand_frac(flex_type,r,h,t) }) / (1.0 - distloss) ;
* Otherwise if using EFS load or climate impacts, import the yearly load directly
$else.allyearpeakstatic
peakdem_static_h(r,h,t) = peak_allyear_static(r,h,t) * (1 - sum{flex_type, flex_demand_frac(flex_type,r,h,t) }) / (1.0 - distloss) ;
$endif.allyearpeakstatic




*==============================
* --- Planning Reserve Margin ---
*================================

*written by input_processing\R\\writeload.R
table prm_nt(nercr_new,allt) "--%-- planning reserve margin for NERC regions"
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

parameter cost_cap_fin_mult_out(i,r,t) "final capital cost multiplier for system cost outputs" ;

* --- Hybrid PV+Battery ---
* Hybrid PV+Battery: PV portion
parameter cost_cap_fin_mult_pvb_p(i,r,t)            "capital cost multiplier for the PV portion of hybrid PV+Battery"
          cost_cap_fin_mult_pvb_p_noITC(i,r,t)      "capital cost multiplier for the PV portion of hybrid PV+Battery, excluding ITC"
          cost_cap_fin_mult_pvb_p_no_credits(i,r,t) "capital cost multiplier for the PV portion of hybrid PV+Battery, excluding ITC/PTC/Depreciation"
;
* Assign the PV portion of PVB the value of UPV
cost_cap_fin_mult_pvb_p(i,r,t)$pvb(i) = sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult(ii,r,t) } ;
cost_cap_fin_mult_pvb_p_noITC(i,r,t)$pvb(i) = sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult_noITC(ii,r,t) } ;
cost_cap_fin_mult_pvb_p_no_credits(i,r,t)$pvb(i) = sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult_no_credits(ii,r,t) } ;

* Hybrid PV+Battery: Battery portion
parameter cost_cap_fin_mult_pvb_b(i,r,t)            "capital cost multiplier for the battery portion of hybrid PV+Battery"
          cost_cap_fin_mult_pvb_b_noITC(i,r,t)      "capital cost multiplier for the battery portion of hybrid PV+Battery, excluding ITC"
          cost_cap_fin_mult_pvb_b_no_credits(i,r,t) "capital cost multiplier for the battery portion of hybrid PV+Battery, excluding ITC/PTC/Depreciation"
;

* In the financing module (python), PVB refers to the battery portion of the hybrid.
* This convention is used to estimate the ITC benefit for the battery.
* Assign the battery portion of PVB the value computed in the financing module for PVB
cost_cap_fin_mult_pvb_b(i,r,t)$pvb(i) = cost_cap_fin_mult(i,r,t) ;
cost_cap_fin_mult_pvb_b_noITC(i,r,t)$pvb(i) = cost_cap_fin_mult_noITC(i,r,t) ;
cost_cap_fin_mult_pvb_b_no_credits(i,r,t)$pvb(i) = cost_cap_fin_mult_no_credits(i,r,t) ;

* Assign "cost_cap_fin_mult" for PVB to be the weighted average of the PV and battery portions
* The weighting is based on:
*   (1) the cost of each portion: PV=cost_cap_pvb_p; Battery=cost_cap_pvb_b
*   (2) the relative size of each portion: PV=1; Battery=bcr
* The "-1" and "+1" values are needed because the multipliers are adjustments off of 1.0
cost_cap_fin_mult(i,r,t)$pvb(i) = ((cost_cap_fin_mult_pvb_p(i,r,t) - 1) * cost_cap_pvb_p(i,t)
                                   + bcr(i) * (cost_cap_fin_mult_pvb_b(i,r,t) - 1) * cost_cap_pvb_b(i,t))
                                   / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_noITC(i,r,t)$pvb(i) = ((cost_cap_fin_mult_pvb_p_noITC(i,r,t) - 1) * cost_cap_pvb_p(i,t)
                                        + bcr(i) * (cost_cap_fin_mult_pvb_b_noITC(i,r,t) - 1) * cost_cap_pvb_b(i,t))
                                        / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_no_credits(i,r,t)$pvb(i) = ((cost_cap_fin_mult_pvb_p_no_credits(i,r,t) - 1) * cost_cap_pvb_p(i,t)
                                             + bcr(i) * (cost_cap_fin_mult_pvb_b_no_credits(i,r,t) - 1) * cost_cap_pvb_b(i,t))
                                             / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_noITC(i,r,t)$geo(i) = cost_cap_fin_mult_noITC("geothermal",r,t) ;
cost_cap_fin_mult_no_credits(i,r,t)$geo(i) = cost_cap_fin_mult_no_credits("geothermal",r,t) ;

* --- Upgrades ---
*Assign upgraded techs the same multipliers as the techs they are upgraded from
cost_cap_fin_mult(i,r,t)$[upgrade(i)$rfeas(r)] = sum{ii$upgrade_from(i,ii), cost_cap_fin_mult(ii,r,t) } ;
cost_cap_fin_mult_noITC(i,r,t)$[upgrade(i)$rfeas(r)] = sum{ii$upgrade_from(i,ii), cost_cap_fin_mult_noITC(ii,r,t) } ;

if(Sw_WaterMain=1,
cost_cap_fin_mult(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult(ii,r,t) } ;

cost_cap_fin_mult_noITC(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult_noITC(ii,r,t) } ;
) ;

* --- Renewable Supply Curves ---
parameter rsc_fin_mult(i,r,t) "capital cost multiplier for resource supply curve technologies that have their capital costs included in the supply curves" ;
parameter rsc_fin_mult_noITC(i,r,t) "capital cost multiplier excluding ITC for resource supply curve technologies that have their capital costs included in the supply curves" ;

* Start by setting all multipliers to 1
rsc_fin_mult(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;
rsc_fin_mult_noITC(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;

*Hydro, pumped-hydro, and geo have capital costs included in the supply curve, so change their multiplier to be the same as cost_cap_fin_mult
rsc_fin_mult(i,r,t)$geo(i) = cost_cap_fin_mult('geothermal',r,t) ;
rsc_fin_mult(i,r,t)$hydro(i) = cost_cap_fin_mult('hydro',r,t) ;
rsc_fin_mult(i,r,t)$psh(i) = cost_cap_fin_mult(i,r,t) ;
rsc_fin_mult_noITC(i,r,t)$geo(i) = cost_cap_fin_mult_noITC('geothermal',r,t) ;
rsc_fin_mult_noITC(i,r,t)$hydro(i) = cost_cap_fin_mult_noITC('hydro',r,t) ;
rsc_fin_mult_noITC(i,r,t)$psh(i) = cost_cap_fin_mult_noITC(i,r,t) ;

* Apply cost reduction multipliers
rsc_fin_mult(i,r,t)$geo(i) = rsc_fin_mult(i,r,t) * sum{geotech$i_geotech(i,geotech), geocapmult(t,geotech) } ;
rsc_fin_mult_noITC(i,r,t)$geo(i) = rsc_fin_mult_noITC(i,r,t) * sum{geotech$i_geotech(i,geotech), geocapmult(t,geotech) } ;
rsc_fin_mult(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult_noITC(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult(i,r,t)$ofswind(i) = rsc_fin_mult(i,r,t) * ofswind_rsc_mult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$ofswind(i) = rsc_fin_mult_noITC(i,r,t) * ofswind_rsc_mult(t,i) ;

$ifthen.sregfin %GSw_IndividualSites% == 1
* For individual sites, we add the following "_rb" parameters to calculate financial multipliers
* at the BA-level, using a strict average of the resource regions within each BA. These BA-level
* parameters are then applied uniformly to the individual sites within that BA.
Parameters
cost_cap_fin_mult_rb(i,rb,t) "BA-level capital cost multiplier",
cost_cap_fin_mult_noITC_rb(i,rb,t) "BA-level capital cost multiplier without ITC",
cost_cap_fin_mult_no_credits_rb(i,rb,t) "BA-level capital cost multiplier without ITC/PTC/depreciation (i.e. actual expenditures)",
rsc_fin_mult_rb(i,rb,t) "BA-level capital cost multiplier for resource supply curve technologies that have their capital costs included in the supply curves",
rsc_fin_mult_noITC_rb(i,rb,t) "BA-level capital cost multiplier for resource supply curve technologies without ITC"
;

cost_cap_fin_mult_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult(i,rr,t)], cost_cap_fin_mult(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult(i,rr,t)], 1 }
;

cost_cap_fin_mult_noITC_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_noITC(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_noITC(i,rr,t)], cost_cap_fin_mult_noITC(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_noITC(i,rr,t)], 1 }
;

cost_cap_fin_mult_no_credits_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_no_credits(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_no_credits(i,rr,t)], cost_cap_fin_mult_no_credits(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$cost_cap_fin_mult_no_credits(i,rr,t)], 1 }
;

rsc_fin_mult_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$rsc_fin_mult(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$rsc_fin_mult(i,rr,t)], rsc_fin_mult(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$rsc_fin_mult(i,rr,t)], 1 }
;

rsc_fin_mult_noITC_rb(i,rb,t)$sum{rr$[cap_agg(rb,rr)$rsc_fin_mult_noITC(i,rr,t)], 1 } =
    sum{rr$[cap_agg(rb,rr)$rsc_fin_mult_noITC(i,rr,t)], rsc_fin_mult_noITC(i,rr,t) }
   /sum{rr$[cap_agg(rb,rr)$rsc_fin_mult_noITC(i,rr,t)], 1 }
;

cost_cap_fin_mult(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), cost_cap_fin_mult_rb(i,rb,t) } ;
cost_cap_fin_mult_noITC(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), cost_cap_fin_mult_noITC_rb(i,rb,t) } ;
cost_cap_fin_mult_no_credits(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), cost_cap_fin_mult_no_credits_rb(i,rb,t) } ;
rsc_fin_mult(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), rsc_fin_mult_rb(i,rb,t) } ;
rsc_fin_mult_noITC(i,r,t)$[wind(i)$valcap_irt(i,r,t)] = sum{rb$cap_agg(rb,r), rsc_fin_mult_noITC_rb(i,rb,t) } ;
ptc_unit_value(i,v,r,t)$[onswind(i)$valinv(i,v,r,t)] = sum{country$rr_country(r,country), ptc_country(i,v,country,t) } ;
$endif.sregfin

*=========================================
* --- Emission Rate ---
*=========================================

table emit_rate_fuel(i,e)  "--tons per MMBtu (CO2 in metric tons, others in short tons)-- emission rate of fuel by technology type"
$offlisting
$ondelim
$include inputs_case%ds%emitrate.csv
$offdelim
$onlisting
;

* this table links CCS techs with their uncontrolled tech counterpart
set ccs_link(i,ii)
/
$offlisting
$ondelim
$include inputs_case%ds%ccs_link.csv
$offdelim
$onlisting
/
;

table capture_rate_input(i,e) "--fraction-- fraction of emissions that are captured"
$offlisting
$ondelim
$include inputs_case%ds%capture_rates_%GSw_CCS_Rate%.csv
$offdelim
$onlisting
;

* calculate emit rate for non-bio CCS techs
emit_rate_fuel(i,e)$[ccs(i)$(not bio(i))] = (1 - capture_rate_input(i,e)) * sum{ii$ccs_link(i,ii), emit_rate_fuel(ii,e) } ;

* adjust the CO2 emission rate for biopower plants
* uncontrolled biopower plants are zero'd out here because they don't have a capture rate
* this reflects our net-zero assumptoin for biopower
emit_rate_fuel(i,"CO2")$bio(i) = - capture_rate_input(i,"CO2") * emit_rate_fuel(i,"CO2") ;

* set upgrade tech emissions
emit_rate_fuel(i,e)$upgrade(i) = sum{ii$upgrade_to(i,ii), emit_rate_fuel(ii,e) } ;

* this sets emissions rates for water techs
emit_rate_fuel(i,e)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), emit_rate_fuel(ii,e) } ;

* parameters for calculating captured emissions
parameter capture_rate_fuel(i,e) "--tons per MMBtu (CO2 in metric tons, others in short tons)-- emission capture rate of fuel by technology type";
capture_rate_fuel(i,e) = capture_rate_input(i,e) * sum{ii$ccs_link(i,ii), emit_rate_fuel(ii,e) } ;

* for beccs, the emission rate already accounts for uncontrolled emissions being net zero, so captured CO2 is simply the emission rate * -1
* note that the negative value defined in emitrate.csv for beccs is based on the assumption of ER = 0.08845 tonnes/MMBtu and CR = 0.9
* (value from https://www.nrel.gov/docs/fy03osti/33123.pdf (see table 1.6-3))
capture_rate_fuel("beccs","CO2") = - emit_rate_fuel("beccs","CO2") ;

parameter capture_rate(e,i,v,r,t) "--tons per MWh (CO2 in metric tons, others in short tons)-- emissions capture rate" ;

* ===========================================================================
* Emissions Limit
* ===========================================================================

set emit_rate_con(e,r,t) "set to enable or disable emissions rate limits by emittant and region" ;

parameter emit_rate_limit(e,r,t)   "--tons per MWh (metric for CO2)-- emission rate limit",
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
       gasscale       "percentage change from reference for each gas bin" /0.02/ ;


*note that the supply curve is set up such that the edge of the bin pertaining to the reference
*price sits at its upper limit, we want to move the curve such that the reference price sits at the middle of the
*respective bin

parameter gasprice(cendiv,gb,t)   "--$/MMBtu-- price of each gas bin",
          gasquant(cendiv,gb,t)   "--MMBtu - natural gas quantity for each bin",
          gaslimit(cendiv,gb,t)   "--MMBtu-- gas limit by gas bin"
          gassupply_ele(cendiv,t) "--MMBtu-- reference gas consumption by the ELE sector"
          gassupply_tot(cendiv,t) "--MMBtu-- reference gas consumption by the ELE sector" ;

* declared over allt to allow for external data files that extend beyond end_year
table gasprice_ref(cendiv,allt)   "--2004$/MMBtu-- natural gas price by census division"
$offlisting
$ondelim
$include inputs_case%ds%ng_price_cendiv.csv
$offdelim
$onlisting
;

* fuel costs for H2 production
* starting units for gas efficiency are MMBtu / kg - need to express this in terms of
* $ / MT through MMBtu / kg * (kg / MT) * ($ / MMBtu)
* SMR production costs seem high given gas-intensity and units
* 1.17 multiplier included to account for the cost differences between electricity and industrial gas prices in the AEO 2021 data
* -- cost of production, for now, just gas_intensity times reference gas price, can revisit gas price assumptions --
scalar industrialGasMult "accounts for differences in the gas price for electricity generators and industrial customers" / 1.17 / ;
parameter h2_fuel_cost(i,v,r,t) "--$/tonne-- fuel cost for hydrogen production" ;
h2_fuel_cost(i,newv,r,t)$[h2(i)$valcap(i,newv,r,t)] = 1000 * (sum(tt$ivt(i,newv,tt),consume_char0(i,tt,"gas_efficiency")) / countnc(i,newv))
                                                           * sum(cendiv$r_cendiv(r,cendiv),gasprice_ref(cendiv,t)) * industrialGasMult ;

* initial capacity gets charged at the initial NG efficiency
h2_fuel_cost(i,initv,r,t)$[h2(i)$valcap(i,initv,r,t)] = 1000 * consume_char0(i,"2010","gas_efficiency")
                                                             * sum(cendiv$r_cendiv(r,cendiv),gasprice_ref(cendiv,t)) * industrialGasMult ;

* -- adding in $ / tonne adder for transport and storage and h2 vom cost
parameter h2_stor_tran(i,t) "--$/tonne-- adder for the cost of hydrogen transport and storage"
          h2_vom(i,t)       "--$/tonne-- variable cost of hydrogen production" ;

* if using regional H2 transport network then h2_stor_tran is not needed
h2_stor_tran(i,t)$[Sw_H2_Transport=0] = deflator("2016") * consume_char0(i,t,"stortran_adder") ;

* option to apply a uniform H2 storage/transport cost that does not vary by tech or year
* note that this overrides input values from the consume_char input file
h2_stor_tran(i,t)$[Sw_H2_Transport_Uniform$h2(i)$sum{(v,r), valcap(i,v,r,t) }] = deflator("2020") * Sw_H2_Transport_Uniform ;

*multiply vom by 1000 because input costs are in $/kg
h2_vom(i,t) = deflator("2016") * consume_char0(i,t,"vom") * 1000 ;

* total cost of h2 production activities ($ per metric tonne)
* note that DAC VOM costs are added above
cost_prod(i,v,r,t)$[h2(i)$valcap(i,v,r,t)] = h2_fuel_cost(i,v,r,t) + h2_stor_tran(i,t) + h2_vom(i,t) ;


table gasquant_elec(cendiv,allt) "--Quads-- Natural gas consumption in the electricity sector"
$offlisting
$ondelim
$include inputs_case%ds%ng_demand_elec.csv
$offdelim
$onlisting
;

table gasquant_tot(cendiv,allt) "--Quads-- Total natural gas consumption"
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
gassupply_ele_nat(t)       "--quads-- national reference gas supply for electricity " ,
gasprice_nat(t)            "--$/MMBtu-- national NG price",
gasquant_nat(t)            "--quads-- national NG usage",
gasquant_nat_bin(gb,t)     "--quads-- national NG quantity by bin",
gasprice_nat_bin(gb,t)     "--$/MMbtu-- price for each national NG bin",
gasadder_cd(cendiv,t,allh) "--$/MMbtu-- adder for NG census divsion, unused",
gaslimit_nat(gb,t)         "--MMbtu-- national gas bin limit" ;

gassupply_ele_nat(t) = sum{cendiv$gassupply_ele(cendiv,t),gassupply_ele(cendiv,t) } ;

gasprice_nat(t) = sum{cendiv$gassupply_ele(cendiv,t),gassupply_ele(cendiv,t) * gasprice_ref(cendiv,t) }
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


gasprice_nat_bin(gb,t)$sum{cendiv,gassupply_tot(cendiv,t) } =
          gas_scale * round(gasprice_nat(t) *
               (
                (gasquant_nat_bin(gb,t) + sum{cendiv,gassupply_tot(cendiv,t) } - gassupply_ele_nat(t))
                /(sum{cendiv,gassupply_tot(cendiv,t) })
                ) ** (1/gas_elasticity),4) ;


*the quantity available in each bin is the quantity on the supply curve minus the previous bin's quantity supplied
gaslimit(cendiv,gb,t) = round((gasquant(cendiv,gb,t) - gasquant(cendiv,gb-1,t)),0) / gas_scale;


gaslimit(cendiv,"gb1",t) = gaslimit(cendiv,"gb1",t)
                            - gassupplyscale * sum{gb$[ord(gb)=(smax(gbb,ord(gbb)) / 2 + 0.5)],gaslimit(cendiv,gb,t) } ;

*final category gets a huge bonus so we make sure we do not run out of gas
gaslimit(cendiv,gb,t)$[ord(gb)=smax(gbb,ord(gbb))] = 5 * gaslimit(cendiv,gb,t) ;


gaslimit_nat(gb,t) = round((gasquant_nat_bin(gb,t) - gasquant_nat_bin(gb-1,t)),0) / gas_scale;

gaslimit_nat("gb1",t) = gaslimit_nat("gb1",t)
                            - gassupplyscale * sum{gb$[ord(gb)=(smax(gbb,ord(gbb)) / 2 + 0.5)],gaslimit_nat(gb,t) } ;

*final category gets a huge bonus so we make sure we do not run out of gas
gaslimit_nat(gb,t)$(ord(gb)=smax(gbb,ord(gbb))) = 5 * gaslimit_nat(gb,t) ;

*Penalizing new gas built within cost recovery period of 20 years in Virginia
* declared over allt to allow for external data files that extend beyond end_year
parameter ng_lifetime_cost_adjust(allt) "--unitless-- cost adjustment for NG in Virginia because al NG techs must be retired by 2045"
/
$offlisting
$ondelim
$include inputs_case%ds%va_ng_crf_penalty.csv
$offdelim
$onlisting
/
;

parameter ng_carb_lifetime_cost_adjust(allt) "--unitless-- cost adjustment for NG with zero emissions"
/
$offlisting
$ondelim
$include inputs_case%ds%co2_cap_%capscenario%_ng_crf_penalty.csv
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
          szn_adj_gas(allh)                      "--unitless-- seasonal adjustment for gas prices",
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
* declared over allt to allow for external data files that extend beyond end_year
table cd_alpha(allt,cendiv) "--$/MMBtu-- alpha value for natural gas supply curves"
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
gasusage_national(t) = sum{cendiv,gassupply_ele(cendiv,t) } ;


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

parameter hours_daily(allh) "--number of hours-- number of hours represented by time-slice 'h' during one day" ;
hours_daily(h) = round(hours(h) / sum{szn$h_szn(h,szn), numdays(szn) }, 3) ;

set store_h_hh(allh,allh) "storage correlation across hours"
/
   (h1*h4,h17).(h1*h4,h17),
   (h5*h8).(h5*h8),
   (h9*h12).(h9*h12),
   (h13*h16).(h13*h16)
/ ;

store_h_hh(h,hh)$sameas(h,hh) = no ;

* --- Storage Efficency ---

parameter storage_eff(i,t) "--fraction-- efficiency of storage technologies" ;

storage_eff(i,t)$storage(i) = 1 ;
storage_eff(psh,t) = 0.8 ;
storage_eff("ICE",t) = 1 ;
storage_eff(i,t)$[storage(i)$plant_char0(i,t,'rte')] = plant_char0(i,t,'rte') ;
storage_eff(i,t)$[dr1(i)$plant_char0(i,t,'rte')] = plant_char0(i,t,'rte') ;
storage_eff(i,t)$pvb(i) = storage_eff("battery_%GSw_pvb_dur%",t) ;

scalar inverter_efficiency "one-way efficiency of AC-DC or DC-AC conversion" /0.98/ ;

parameter storage_eff_pvb_p(i,t) "--fraction-- efficiency of hybrid PV+battery when charging from the coupled PV"
          storage_eff_pvb_g(i,t) "--fraction-- efficiency of hybrid PV+battery when charging from the grid" ;

*when charging from PV the pvb system will have a higher efficiency due to one less inverter conversion
storage_eff_pvb_p(i,t)$pvb(i) = storage_eff(i,t) / inverter_efficiency ;
*when charging from the grid the efficiency will be the same as standalone storage
storage_eff_pvb_g(i,t)$pvb(i) = storage_eff("battery_%GSw_pvb_dur%",t) ;

*upgrade plants assume the same as what theyre upgraded to
storage_eff(i,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), storage_eff(ii,t) } ;

parameter storage_lifetime_cost_adjust(i) "--unitless-- cost adjustment for battery storage technologies because they do not have a 20-year life" ;

*The 1.21 value is the CRF_15 divided by CRF_20 to account for batteries only having a 15-year lifetime.
*It technically should change over time (if CRF changes over time), but is represented as a constant value here for simplicity
storage_lifetime_cost_adjust(i)$[battery(i) or pvb(i)] = 1.24 ;

cost_cap(i,t)$[storage_lifetime_cost_adjust(i)$(not pvb(i))] = cost_cap(i,t) * storage_lifetime_cost_adjust(i) ;
cost_cap_pvb_b(i,t)$[storage_lifetime_cost_adjust(i)$pvb(i)] = cost_cap_pvb_b(i,t) * storage_lifetime_cost_adjust(i) ;

* --- Storage Input Capacity ---

parameter minstorfrac(i,v,r,allh) "--fraction-- minimum storage_in as a fraction of total input capacity";
minstorfrac(i,v,r,h)$[sum{t, valcap(i,v,r,t) }$psh(i)] = %GSw_HydroStorInMinLoad% ;

parameter storinmaxfrac(i,v,r)  "--fraction-- max storage input capacity as a fraction of output capacity" ;
table storinmaxfrac_data(i,v,r) "--fraction-- data for max storage input capacity as a fraction of capacity if data is available"
$offlisting
$ondelim
$include inputs_case%ds%storinmaxfrac.csv
$offdelim
$onlisting
;
$ifthen.storcap %GSw_HydroStorInMaxFrac% == "data"
* Use data file for available PSH data
storinmaxfrac(psh,v,r) = storinmaxfrac_data(psh,v,r) ;
$else.storcap
* Use numerical value from case file for PSH only
storinmaxfrac(psh,v,r) = %GSw_HydroStorInMaxFrac% ;
$endif.storcap
* Fill any gaps with values of 1
storinmaxfrac(i,v,r)$[(storage_standalone(i) or hyd_add_pump(i))$(not storinmaxfrac(i,v,r))$sum{t, valcap(i,v,r,t) }] = 1 ;

* --- Hybrid PV+Battery ---

table pvbcapmult(allt,pvb_config) "PV+Battery capital cost multipliers over time"
$offlisting
$ondelim
$include inputs_case%ds%pvbcapcostmult.csv
$offdelim
$onlisting
;

* the capital cost for PVB includes both the PV and battery portions
* total cost = cost(PV) * cap(PV) + cost(B) * cap(B)
*            = cost(PV) * cap(PV) + cost(B) * bcr * cap(PV)
*            = [cost(PV) + cost(B) * bcr ] * cap(PV)
cost_cap(i,t)$pvb(i) = (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) * sum{pvb_config$pvb_agg(pvb_config,i), pvbcapmult(t,pvb_config) } ;

*last instance of cost_cap just occured, so now assign upgrade costs

*costs for upgrading are the difference in capital costs
*between the initial techs and the tech to which the unit is upgraded
cost_upgrade(i,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_cap(ii,t) }
                               - sum{ii$upgrade_from(i,ii), cost_cap(ii,t) } ;

*the coal-CCS input from ATB 2021 and on is for a pulverized coal plant
*assume that the upgrade cost for coal-IGCC_coal-CCS is the same as for
*coal-new_coal-CCS
cost_upgrade('coal-IGCC_coal-CCS',t) = cost_upgrade('coal-new_coal-CCS',t) ;

*increase cost_upgrade by 1% to prevent building and upgrading in the same year
*(otherwise there is a degeneracy between building new and building+upgrading in the same year)
cost_upgrade(i,t)$upgrade(i) = cost_upgrade(i,t) * 1.01 ;

*Sets upgrade costs for RE-CT and RE-CC plants based relative to capital cost for RE-CT
*this is done because upgrade costs are higher than new build costs
*RE-CT upgrades are 20% of the cost of the gas-CT
cost_upgrade('Gas-CT_RE-CT',t) = cost_cap('gas-ct',t) * 0.2 ;
*RE-CC upgrades includes replacing the steam turbine capacity with a new RE-CT
*and assumes that the gas-CC is 2/3 gas-CT and 1/3 steam turbine
cost_upgrade('Gas-CC_RE-CC',t) = cost_cap('gas-ct',t) * [(2/3 * 0.2) + 1/3] ;

* Assign upgrade costs for hydro technology upgrades using values from cases file
cost_upgrade('hydEND_hydED',t) = %GSw_HydroCostAddDispatch% ;
cost_upgrade('hydED_pumped-hydro',t) = %GSw_HydroCostAddPump% ;
cost_upgrade('hydED_pumped-hydro-flex',t) = %GSw_HydroCostAddPump% ;

parameter vre_gen_old(i,r,allh,t)              "--MWh-- estimated pre-curtailment generation from VRE and Hybrid PV+Battery" ;
parameter curt_old_pvb(r,allh,t)               "--avg MW-- estimated curtailment from existing hybrid PV+Battery sources (sequential only)" ;
parameter curt_old_pvb_lastyear(r,allh)        "--avg MW-- estimated curtailment from existing hybrid PV+Battery sources in the previous model year (sequential only)" ;
parameter hybrid_cc_derate(i,r,allszn,sdbin,t) "--fraction-- derate factor for hybrid PV+battery storage capacity credit" ;

* initialize to 1 and adjust based on the results from Augur
hybrid_cc_derate(i,r,szn,sdbin,t)$[pvb(i)$rfeas(r)$tmodel_new(t)] = 1 ;

scalar pvb_itc_qual_frac "--fraction-- fraction of energy that must be charge from local PV for hybrid PV+battery" ;
pvb_itc_qual_frac = %GSw_PVB_ITC_Qual_Constraint% ;

* --- CSP with storage ---

* used in eq_rsc_INVlim
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

resourcescaler(i)$[(not CSP_Storage(i))$(not ban(i))] = 1 ;
resourcescaler(i)$csp(i) = CSP_SM(i) / 2.4 ;

* --- Storage Duration ---

parameter storage_duration(i)   "--hours-- storage duration by tech"
/
$offlisting
$ondelim
$include inputs_case%ds%storage_duration.csv
$offdelim
$onlisting
/
;

* Change PSH default duration to 10 hours if using a corresponding supply curve
$ifthen.pshdur %pshsupplycurve% == "10hr_15bin_wcontingency"
storage_duration(i)$psh(i) = 10 ;
$elseif.pshdur %pshsupplycurve% == "8hr_15bin_wcontingency"
storage_duration(i)$psh(i) = 8 ;
$elseif.pshdur %pshsupplycurve% == "10hr_15bin_wcontingency_hicost"
storage_duration(i)$psh(i) = 10 ;
$endif.pshdur

storage_duration(i)$[i_water_cooling(i)$Sw_WaterMain] =
  sum{ii$ctt_i_ii(i,ii), storage_duration(ii) } ;

storage_duration(i)$pvb(i) = storage_duration("battery_%GSw_pvb_dur%") ;

*upgrade plants assume the same as what they're upgraded to
storage_duration(i)$upgrade(i) = sum{ii$upgrade_to(i,ii),storage_duration(ii) } ;

parameter storage_duration_m(i,v,r)   "--hours-- storage duration by tech, vintage, and region"
          cc_storage(i,sdbin,t)   "--fraction-- capacity credit of storage by duration"
          bin_duration(sdbin)   "--hours-- duration of each storage duration bin"
          bin_penalty(sdbin)    "--$-- penalty to incentivize solve to fill the shorter duration bins first"
          within_seas_frac(i,v,r) "--unitless-- fraction of energy that must be used within season. 1 means no shifting. <1 means we can shift"
;
table storage_duration_pshdata(i,v,r) "--hours-- storage duration data for PSH"
$onlisting
$ondelim
$include inputs_case%ds%storage_duration_pshdata.csv
$offdelim
$offlisting
;

* Initialize using generic tech-specific duration
storage_duration_m(i,v,r)$[storage_duration(i)$sum{t, valcap(i,v,r,t) }] = storage_duration(i) ;
* Overwrite storage duration for existing PSH capacity when using datafile
$ifthen %GSw_HydroPSHDurData% == 1
storage_duration_m(psh,v,r)$storage_duration_pshdata(psh,v,r) = storage_duration_pshdata(psh,v,r) ;
$endif
* Define fraction of energy that must be used within season. Use input parameters for dispatchable hydropower and PSH.
within_seas_frac(i,v,r)$[sum{t, valcap(i,v,r,t) }] = 1;
within_seas_frac(hydro_d,v,r) = %GSw_HydroWithinSeasFrac% ;
$ifthen.usedur %GSw_HydroPumpWithinSeasFrac% == "data"
* Use storage duration data to define.
* This will only allow shifting for durations > 168 hours, where 168-730.5 hr is classified by the
*   International Hydropower Association as "intra-month", and >730.5 hr is classified as Seasonal.
within_seas_frac(psh,v,r)$[storage_duration_m(psh,v,r) > 168] = round(1 - storage_duration_m(psh,v,r)/(24*7*(52/4)), 3) ;
within_seas_frac(psh,v,r)$[within_seas_frac(psh,v,r) < 0] = 0 ;
$else.usedur
* Use numerical value from case file for PSH only
within_seas_frac(psh,v,r)$[sum{t, valcap(psh,v,r,t) }] = %GSw_HydroPumpWithinSeasFrac% ;
$endif.usedur

* set the duration of each storage duration bin
bin_duration(sdbin) = sdbin.val ;

* set the capacity credit of each storage technology for each storage duration bin.
* for example, 2-hour batteries get CC=1 for the 2-hour bin and CC=0.5 for the 4-hour bin
* likewise, 6-hour batteries get CC=1 for the 2-, 4-, and 6-hour bins, but only 0.75 for the 8-hour bin, etc.
cc_storage(i,sdbin,t) = storage_duration(i) / bin_duration(sdbin) ;
cc_storage(i,sdbin,t)$(cc_storage(i,sdbin,t) > 1) = 1 ;
cc_storage(i,sdbin,t) = round(cc_storage(i,sdbin,t),3) ;
* this bin is included as a safety valve so that the model can build additional storage beyond what is
* available for diurnal peaking capacity
cc_storage(i,'8760',t) = 0 ;

bin_penalty(sdbin) = 1e-5 * (ord(sdbin) - 1) ;

*upgrade plants assume the same as what they're upgraded to
cc_storage(i,sdbin,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cc_storage(ii,sdbin,t) } ;

parameter hourly_arbitrage_value(i,r,t) "--$/MW-yr-- hourly arbitrage value of energy storage"
          storage_in_min(r,allh,t)      "--MW-- lower bound for STORAGE_IN"
;

hourly_arbitrage_value(i,r,t) = 0 ;
storage_in_min(r,h,t) = 0 ;

* --- minimum capacity factor ----
parameter minCF(i,t)  "--fraction-- minimum annual capacity factor for each tech fleet, applied to (i,rto)" ;

* 1% for gas-CT is minimum gas-CT CF across the PLEXOS runs from the 2019 Standard Scenarios
* 6% for RE-CT and RE-CC is based on unpublished PLEXOS runs of 100% RE scenarios performed in summer 2019
parameter minCF_input(i) "--fraction-- minimum annual capacity factor for each tech fleet, applied to (i,rto)"
/
$offlisting
$ondelim
$include inputs_case%ds%minCF.csv
$offdelim
$onlisting
/ ;
minCF(i,t) = minCF_input(i) ;
minCF(i,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), minCF(ii,t) } ;
minCF(i,t)$[i_water_cooling(i)$Sw_WaterMain] = sum{ii$ctt_i_ii(i,ii), minCF(ii,t) } ;

* adjust fleet mincf for nuclear when using flexible nuclear
minCF(i,t)$[nuclear(i)$Sw_NukeFlex] = 0.06 ;

* --- storage fixed OM cost ---

*fom and vom costs are constant for pumped-hydro
*values are taken from ATB
cost_fom(psh,v,r,t)$valcap(psh,v,r,t) = 13030 ;
cost_vom(psh,v,r,t)$valcap(psh,v,r,t) = 0.375 ;


* declared over allt to allow for external data files that extend beyond end_year
parameter ice_fom(allt) "--$/MW-year -- Fixed O&M costs for ice storage"
/
$offlisting
$ondelim
$include inputs_case%ds%ice_fom.csv
$offdelim
$onlisting
/
;

cost_fom("ICE",v,rb,t)$valcap("ICE",v,rb,t) = ice_fom(t) ;

parameter emit_rate(e,i,v,r,t) "--tons per MWh (CO2 in metric tons, others in short tons)-- emissions rate" ;
scalar bio_cofire_perc "--fraction-- fraction of total fuel that is biomass used in cofire plants" /0.15/ ;

emit_rate(e,i,v,r,t)$[emit_rate_fuel(i,e)$valcap(i,v,r,t)$rb(r)]
  = round(heat_rate(i,v,r,t) * emit_rate_fuel(i,e),6) ;

*only emissions from the coal portion of cofire plants are considered
emit_rate(e,i,v,r,t)$[sameas(i,"cofire")$emit_rate_fuel("coal-new",e)$valcap(i,v,r,t)$rb(r)]
  = round((1-bio_cofire_perc) * heat_rate(i,v,r,t) * emit_rate_fuel("coal-new",e),6) ;

* calculate emissions capture rates (same logic as emissions calc above)
capture_rate(e,i,v,r,t)$[capture_rate_fuel(i,e)$valcap(i,v,r,t)$rb(r)]
  = round(heat_rate(i,v,r,t) * capture_rate_fuel(i,e),6) ;

* deflate CO2 transport and storage cost from $2020 to $2004
scalar CO2_storage_cost ;
CO2_storage_cost = Sw_CO2_Storage * deflator('2020') ;


*==============================
* --- BIOMASS SUPPLY CURVES ---
*==============================

* supply curves defined by 21 price increments
set bioclass / bioclass1*bioclass21 /
    biofeas(r) "regions with biomass supply and biopower"
;

* supply curve derived from 2016 ORNL Billion Ton study
* annual supply of woody biomass available to the power sector (in million dry tons)
* by USDA region at price P (2015$ per dry ton)
table biosupply(usda_region,bioclass,*) "biomass supply (million dry tons) and biomass cost ($/ton)"
$offlisting
$ondelim
$include inputs_case%ds%bio_supplycurve.csv
$offdelim
$onlisting
;

* convert biomass supply from million dry tons to MMBtu
* assuming 13 MMBtu per dry ton based on 2016 ORNL Billion Ton Study
scalar bio_energy_content "MMBtu per dry ton of biomass" / 13 / ;
biosupply(usda_region,bioclass,"cap") = biosupply(usda_region, bioclass,"cap") * 1E6 * bio_energy_content ;

* muliplier for total biomass supply, set by user via input switch (default is 1)
biosupply(usda_region,bioclass,"cap") = biosupply(usda_region,bioclass,"cap") * Sw_BioSupply ;

* convert price into $ per MMBtu
* input price ($/ton) / (MMBtu/ton) = $/MMBtu ; also deflate from 2015$
biosupply(usda_region,bioclass,"price") = biosupply(usda_region, bioclass,"price") / bio_energy_content * deflator('2015') ;

* regions with biomass supply
biofeas(r)$[sum{bioclass, sum{usda_region$r_usda(r, usda_region), biosupply(usda_region,bioclass,"cap") } } ] = yes ;

*removal of bio techs that are not in biofeas(r)
valcap(i,v,r,t)$[(cofire(i) or bio(i))$(not biofeas(r))] = no ;
valgen(i,v,r,t)$[(cofire(i) or bio(i))$(not biofeas(r))] = no ;
valinv(i,v,r,t)$[(cofire(i) or bio(i))$(not biofeas(r))] = no ;

*do not allow upgrades when there is no capacity to upgrade from
*here re-doing the calculation based on biofeas subsetting
valcap(i,v,r,t)$[(not sum{ii$upgrade_from(i,ii),valcap(ii,v,r,t) })$upgrade(i)] = no ;
valgen(i,v,r,t)$[not sum{rr$cap_agg(r,rr),valcap(i,v,rr,t) }] = no ;
valinv(i,v,r,t)$[not valcap(i,v,r,t)] = no ;

scalar bio_transport_cost ;
* biomass transport cost enter in $ per ton, convert to $ per MMBtu and deflate from $2020 to $2004
bio_transport_cost = Sw_BioTransportCost / bio_energy_content * deflator('2020') ;

* get price of cheapest supply curve bin that has resources (needed for Augur)
* price includes any transport costs for biomass
parameter rep_bio_price_unused(r) "--2004$/MWh-- marginal price of lowest cost available supply curve bin for biofuel" ;
rep_bio_price_unused(r)$[sum{usda_region, 1$r_usda(r,usda_region) }] =
    smin{bioclass$[sum{usda_region$r_usda(r, usda_region), biosupply(usda_region,bioclass,"cap") }],
        sum{usda_region$r_usda(r, usda_region), biosupply(usda_region,bioclass,"price") } } + bio_transport_cost ;

*================================
* Capacity value and curtailment
*================================

parameters sdbin_size(ccreg,allszn,sdbin,t)      "--MW-- available capacity by storage duration bin - used to bin the peaking power capacity contribution of storage by duration",
           sdbin_size_load(ccreg,allszn,sdbin,t) "--MW-- bin_size loading in from the cc_out gdx file",
           curt_int(i,r,allh,t)                  "--fraction-- average curtailment rate of all resources in a given year - only used in intertemporal solve",
           curt_excess(r,allh,t)                 "--MW-- excess curtailment when assuming marginal curtailment in intertemporal solve",
           curt_marg(i,r,allh,t)                 "--fraction-- marginal curtail rate for new resources - only used in sequential solve",
           cc_old(i,r,allszn,t)                  "--MW-- capacity credit for existing capacity - used in sequential solve similar to heritage reeds",
           cc_old_load(i,r,ccreg,allszn,t)       "--MW-- cc_old loading in from the cc_out gdx file",
           cc_mar(i,r,allszn,t)                  "--fraction--  cc_mar loading inititalized to some reasonable value for the 2010 solve",
           cc_int(i,v,r,allszn,t)                "--fraction--  average fractional capacity credit - used in intertemporal solve",
           cc_excess(i,r,allszn,t)               "--MW-- this is the excess capacity credit when assuming marginal capacity credit in intertemporal solve",
           cc_eqcf(i,v,r,t)                      "--fraction--  fractional capacity credit based off average capacity factors - used without iteration with cc and curt scripts",
           cc_dr(i,r,allszn,t)                   "--fraction-- fractional capacity credit of DR"
           curt_mingen(r,allh,t)                 "--fraction--  fraction of addition curtailment induced by increasing the minimum generation level (sequential only)",
           curt_mingen_int(r,allh,t)             "--fraction--  fractional curtailment of mingen (intertemporal only)",
           curt_mingen_load(r,allh,t)            "--fraction--  fraction of addition curtailment induced by increasing the minimum generation level, loaded from gdx file (so as to not overwrite existing values for non-modeled years)",
           curt_stor(i,v,r,allh,src,t)           "--fraction--  fraction of curtailed energy that can be recovered by storage charging from a given source during that timeslice",
           curt_dr(i,v,r,allh,src,t)             "--fraction--  fraction of curtailed energy that can be recovered by DR charging from a given source during that timeslice",
           curt_tran(r,rr,allh,t)                "--fraction--  fraction of curtailed energy that can be reduced in r by building new transmission lines to rr",
           curt_prod(r,allh,t)                   "--fraction--  fraction of H2 electricity consumption that can be used for curtailment recovery",
           net_load_adj_no_curt_h(r,allh,t)      "--MW-- net load accounting for VRE, mingen, and storage; used to characterize curtailment reduction from new transmission",
           curt_reduct_tran_max(r,rr,allh,allt)  "--MW-- maximum amount of curtailment reduction that can occur in r from adding transmission to rr",
           curt_old(r,allh,t)                    "--MW-- curtailment from old capacity - used to calculate average curtailment for VRE techs",
           vre_gen_last_year(r,allh,t)           "--MW-- generation from VRE generators in the prior solve year",
           cap_fraction(i,v,r,t)                 "--fraction--  fraction of capacity that was retired",
           mingen_postret(r,allszn,t)            "--MWh-- minimum generation level from retirements" ;


cc_old(i,r,szn,t) = 0 ;
cc_int(i,v,r,szn,t) = 0 ;
cc_dr(i,r,szn,t) = 0 ;

cc_eqcf(i,v,rb,t)$[vre(i)$(sum{rscbin, rscfeas(rb,'sk',i,t,rscbin) })] =
  cf_adj_t(i,v,t) * sum{h,hours(h) * cf_rsc(i,v,rb,h,t) } / sum{h,hours(h) } ;
cc_eqcf(i,v,rs,t)$[(not sameas(rs,'sk'))$vre(i)$(sum{(rscbin,r)$r_rs(r,rs), rscfeas(r,rs,i,t,rscbin) })$valcap(i,v,rs,t)] =
  cf_adj_t(i,v,t) * sum{h,hours(h) * cf_rsc(i,v,rs,h,t) } / sum{h,hours(h) } ;

cc_mar(i,r,szn,t) = sum{v$ivt(i,v,t), cc_eqcf(i,v,r,t) } ;

cc_excess(i,r,szn,t) = 0 ;

*initialize curtailments at zero
curt_int(i,r,h,t) = 0 ;
curt_excess(r,h,t) = 0 ;
curt_old(r,h,t) = 0 ;
curt_marg(i,r,h,t) = 0 ;
curt_mingen(r,h,t) = 0 ;
curt_mingen_int(r,h,t) = 0 ;
curt_stor(i,v,r,h,src,t) = 0 ;
curt_prod(r,h,t) = 0 ;
curt_dr(i,v,r,h,src,t) = 0 ;
curt_tran(r,rr,h,t) = 0 ;
curt_reduct_tran_max(r,rr,h,t) = 0 ;
net_load_adj_no_curt_h(r,h,t) = 0 ;

*initializing post retirement mingen to 0
cap_fraction(i,v,r,t) = 0 ;
mingen_postret(r,szn,t) = 0 ;

*initialize storage bin sizes
sdbin_size(ccreg,szn,sdbin,"2010") = 1000 ;

parameter cost_curt(t) "--$/MWh-- price paid for curtailed VRE" ;

cost_curt(t)$[yeart(t)>=model_builds_start_yr] = Sw_CurtMarket ;

parameter emit_cap(e,t)   "--tons (metric for CO2)-- emissions cap, by default a large value and changed in d_solveprep",
          yearweight(t)   "--unitless-- weights applied to each solve year for the banking and borrowing cap - updated in d_solveprep.gms",
          emit_tax(e,r,t) "--$/ton (metric for CO2)-- Tax applied to emissions" ;

emit_cap(e,t) = 0 ;
emit_tax(e,r,t) = 0 ;

yearweight(t) = 0 ;
yearweight(t)$tmodel_new(t) = sum{tt$tprev(tt,t), yeart(tt) } - yeart(t) ;
yearweight(t)$tlast(t) = 1 + smax{yearafter, yearafter.val } ;

* declared over allt to allow for external data files that extend beyond end_year
parameter co2_cap(allt)      "--metric tons-- co2 emissions cap used when Sw_AnnualCap is on"
/
$ondelim
$include inputs_case%ds%co2_cap_%capscenario%.csv
$offdelim
/
;

parameter co2_tax(allt)      "--$/metric ton CO2-- co2 tax used when Sw_CarbTax is on"
/
$offlisting
$ondelim
$include inputs_case%ds%co2_tax_%GSw_CarbTaxOption%.csv
$offdelim
$onlisting
/
;

parameter emit_scale(e) "scaling factor for emissions" /
CO2 1000
SO2 1
NOX 1
HG 1
/ ;

* set the carbon tax based on switch arguments
if(Sw_CarbTax = 1,
emit_tax("CO2",r,t) = co2_tax(t) * emit_scale("CO2") ;
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
m_rsc_dat(r,i,t,rscbin,sc_cat)     "--MW or $/MW-- resource supply curve attributes",
m_cc_mar(i,r,allszn,t)           "--fraction-- marginal capacity credit",
m_cc_dr(i,r,allszn,t)            "--fraction-- marginal capacity credit",
m_cf(i,v,r,allh,t)               "--fraction-- modeled capacity factor",
m_cf_szn(i,v,r,allszn,t)         "--fraction-- modeled capacity factor, averaged by season" ;

  m_avail_retire_exog_rsc(i,v,r,t) = avail_retire_exog_rsc(i,v,r,t) ;

  m_rsc_dat(rb,i,t,rscbin,"cap") = rsc_dat(rb,"sk",i,t,rscbin,"cap") ;
  m_rsc_dat(rs,i,t,rscbin,"cap")$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs),rsc_dat(r,rs,i,t,rscbin,"cap") } ;

rsc_dat(r,rs,i,t,rscbin,"cost")$[hydro(i)$rsc_dat(r,rs,i,t,rscbin,"cost")] = rsc_dat(r,rs,i,t,rscbin,"cost") * 1000 ;

  m_rsc_dat(rb,i,t,rscbin,"cost") = rsc_dat(rb,"sk",i,t,rscbin,"cost") ;
  m_rsc_dat(rs,i,t,rscbin,"cost")$[not sameas(rs,"sk")] = sum{r$r_rs(r,rs),rsc_dat(r,rs,i,t,rscbin,"cost") } ;

* prescribed hydund in p33 does not have enough rsc_dat
* capacity to meet prescribed amount - check with WC
  m_rsc_dat("p18","hydUND",t,"bin1","cap")   = m_rsc_dat("p18","hydUND",t,"bin1","cap") + 27 ;
  m_rsc_dat("p18","hydNPND",t,"bin1","cap")  = m_rsc_dat("p18","hydNPND",t,"bin1","cap") + 3 ;
  m_rsc_dat("p110","hydNPND",t,"bin1","cap") = m_rsc_dat("p110","hydNPND",t,"bin1","cap") + 58 ;
  m_rsc_dat("p33","hydUND",t,"bin1","cap")   = 5 ;

*=========================================
* Reduced Resource Switch
*=========================================

parameter rsc_reduct_frac(pcat,r,t) "--unitless-- fraction of renewable resource that is reduced from the supply curve"
          prescrip_rsc_frac(pcat,r,t) "--unitless-- fraction of prescribed builds to the resource available"
;

rsc_reduct_frac(pcat,r,t) = 0 ;
prescrip_rsc_frac(pcat,r,t) = 0 ;

* if the Sw_ReducedResource is on, reduce the available resource by 50%
if (Sw_ReducedResource = 1,
*Calculate the fraction of prescribed builds to the available resource
* 2021-05-05 the prescriptions are being applied across all years until we decide a better way to do this
  prescrip_rsc_frac(pcat,r,t)$[sum{(i,rscbin)$prescriptivelink(pcat,i), m_rsc_dat(r,i,t,rscbin,"cap") } > 0] =
      smax(tt,m_required_prescriptions(pcat,r,tt)) / sum{(i,rscbin)$prescriptivelink(pcat,i), m_rsc_dat(r,i,t,rscbin,"cap") } ;
*Set the default resource reduction fraction
  rsc_reduct_frac(pcat,r,t) = 0.5 ;
*If the resource reduction fraction will reduce the resource to the point that prescribed builds will be infeasible,
*then replace the resource reduction fraction with the maximum that the resource can be reduced to still have a feasible solution
  rsc_reduct_frac(pcat,r,t)$[prescrip_rsc_frac(pcat,r,t) > (1 - rsc_reduct_frac(pcat,r,t))] = 1 - prescrip_rsc_frac(pcat,r,t) ;

*In order to avoid small number issues, round down at the 3rd decimal place
*Because the floor function returns an integer, we multiply and divide by 1000 to get proper rounding
  rsc_reduct_frac(pcat,r,t) = rsc_reduct_frac(pcat,r,t) * 1000 ;
  rsc_reduct_frac(pcat,r,t) = floor(rsc_reduct_frac(pcat,r,t)) ;
  rsc_reduct_frac(pcat,r,t) = rsc_reduct_frac(pcat,r,t) / 1000 ;

*Now reduce the resource by the updated resource reduction fraction
*(only do this for hydro, geothermal, PSH, and CSP; PV and wind have limited resource supply curves)
  m_rsc_dat(r,i,t,rscbin,"cap")$[rsc_i(i)$(csp(i) or hydro(i) or psh(i) or geo(i))] =
          m_rsc_dat(r,i,t,rscbin,"cap") * (1 - sum{pcat$prescriptivelink(pcat,i), rsc_reduct_frac(pcat,r,t) }) ;
) ;

*adjust cost of PV+Battery interconnection [$/MWdc] based on the ILR; base=1.3
m_rsc_dat(r,i,t,rscbin,"cost")$pvb(i) = m_rsc_dat(r,i,t,rscbin,"cost") * 1.3 / ilr(i) ;

set m_rsc_con(r,i,t) "set to detect numeraire rsc techs that have capacity value" ;
m_rsc_con(r,i,t)$sum{rscbin, m_rsc_dat(r,i,t,rscbin,"cap") } = yes ;

  m_rscfeas(r,i,t,rscbin) = no ;
  m_rscfeas(r,i,t,rscbin)$m_rsc_dat(r,i,t,rscbin,"cap") = yes ;
  m_rscfeas(r,i,t,rscbin)$[sum{ii$tg_rsc_cspagg(ii, i),m_rscfeas(r,ii,t,rscbin) }] = yes ;
  m_rscfeas("sk",i,t,rscbin) = no ;

  m_cc_mar(i,r,szn,t) = cc_mar(i,r,szn,t) ;
  m_cc_dr(i,r,szn,t) = cc_dr(i,r,szn,t) ;

* do not apply "avail" for hybrid PV+battery because "avail" represents the battery availability
  m_cf(i,v,r,h,t)$[cf_tech(i)$valcap(i,v,r,t)] =
         (1$[not hydro(i)] + cf_adj_hyd(r,i,h,t)$hydro(i))
         * cf_rsc(i,v,r,h,t)
         * cf_adj_t(i,v,t)
         * (avail(i,v,h)$[not pvb(i)] + 1$pvb(i)) ;

* can remove capacity factors for new vintages that have not been introduced yet
  m_cf(i,newv,r,h,t)$[not sum{tt$(yeart(tt) <= yeart(t)), ivt(i,newv,tt ) }$valcap(i,newv,r,t)] = 0 ;

* distpv capacity factor is divided by (1.0 - distloss) to provide a bus bar equivalent capacity factor
  m_cf("distpv",v,r,h,t)$valcap("distpv",v,r,t) = m_cf("distpv",v,r,h,t) / (1.0 - distloss) ;
  m_cf_szn(i,v,r,szn,t)$[cf_tech(i)$valcap(i,v,r,t)] = sum{h$h_szn(h,szn), hours(h) * m_cf(i,v,r,h,t) } / sum{h$h_szn(h,szn), hours(h) } ;

* adding upgrade techs for hydro
  m_cf_szn(i,v,r,szn,t)$[cf_tech(i)$upgrade(i)$valcap(i,v,r,t)$(hydro_d(i) or psh(i))] =
        sum{ii$upgrade_from(i,ii), m_cf_szn(ii,v,r,szn,t) } ;

  m_cf_szn(i,v,r,szn,t)$[cf_tech(i)$upgrade(i)$valcap(i,v,r,t)$hydro_d(i)$(not m_cf_szn(i,v,r,szn,t))] =
        sum{ii$upgrade_to(i,ii), m_cf_szn(ii,v,r,szn,t) } ;

  m_cf_szn(i,v,r,szn,t)$[cf_tech(i)$upgrade(i)$valcap(i,v,r,t)$hydro_d(i)$(not m_cf_szn(i,v,r,szn,t))] = 1 ;



*can trim down these matrices fairly significantly...
peakdem_h17_ratio(r,szn,t)$load_exog(r,"h17",t) = peakdem_static_szn(r,szn,t) / load_exog_static(r,"h17",t) ;

set force_pcat(pcat,t) "conditional to indicate whether the force prescription equation should be active for pcat" ;

force_pcat(pcat,t)$[yeart(t) < firstyear_pcat(pcat)] = yes ;
force_pcat(pcat,t)$[sum{r$rfeas_cap(r), noncumulative_prescriptions(pcat,r,t) }] = yes ;

set clean_energy(i) "set of technologies that contribute toward clean energy requirements" ;

clean_energy(i) = no ;
clean_energy(i)$re(i) = yes ;
nat_gen_tech_frac(i)$re(i) = yes ;

*Switch allows Nuclear and CCS to be counted towards RE
if(Sw_CleanEnergy = 1,
      clean_energy(i)$nuclear(i) = YES ;
      nat_gen_tech_frac(i)$nuclear(i) = 1 ;
) ;

if(Sw_CleanEnergy = 2,
      clean_energy(i)$ccs(i)  = YES ;
      nat_gen_tech_frac(i)$ccs(i) = 1 ;
      clean_energy(i)$nuclear(i) = YES ;
      nat_gen_tech_frac(i)$nuclear(i) = 1 ;
) ;

*=========================================
* Decoupled Capacity/Energy Upgrades
*=========================================
Parameter
cost_cap_up(i,v,r,rscbin,t)     "--2004$/MW-- capacity upgrade costs",
cost_ener_up(i,v,r,rscbin,t)    "--2004$/MW-- energy upgrade costs.",
cap_cap_up(i,v,r,rscbin,t)      "--MW-- capacity of capacity upgrades",
cap_ener_up(i,v,r,rscbin,t)     "--MW-- capacity of energy upgrades",
allow_cap_up(i,v,r,rscbin,t)    "i, v, r, and t combinations that are allowed for capacity upsizing",
allow_ener_up(i,v,r,rscbin,t)   "i, v, r, and t combinations that are allowed for energy upsizing"
;

* Adjust available capacity and costs for hydropower upgrades using switch input.
m_rsc_dat(r,'hydUD',t,rscbin,"cap") = m_rsc_dat(r,'hydUD',t,rscbin,"cap") * %GSw_HydroUpgradeCapMult% ;
m_rsc_dat(r,'hydUND',t,rscbin,"cap") = m_rsc_dat(r,'hydUND',t,rscbin,"cap") * %GSw_HydroUpgradeCapMult% ;
m_rsc_dat(r,'hydUD',t,rscbin,"cost") = m_rsc_dat(r,'hydUD',t,rscbin,"cost") * %GSw_HydroUpgradeCostMult% ;
m_rsc_dat(r,'hydUND',t,rscbin,"cost") = m_rsc_dat(r,'hydUND',t,rscbin,"cost") * %GSw_HydroUpgradeCostMult% ;

* Use hydropower upgrade supply curves and multiplier from switch input to define decoupled capacity/energy upgrade costs.
cost_cap_up('hydED','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUD',t,rscbin,"cost") * %GSw_HydroCostFracCapUp% ;
cost_cap_up('hydEND','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUND',t,rscbin,"cost") * %GSw_HydroCostFracCapUp% ;
cost_ener_up('hydED','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUD',t,rscbin,"cost") * %GSw_HydroCostFracEnerUp% ;
cost_ener_up('hydEND','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUND',t,rscbin,"cost") * %GSw_HydroCostFracEnerUp% ;

* Initialize available capacity/energy upgrades to zero to avoid double counting if using coupled capacity/energy upgrades.
cap_cap_up(i,v,r,rscbin,t) = 0 ;
cap_ener_up(i,v,r,rscbin,t) = 0 ;

* If decoupling hydropower capacity/energy upgrades, use upgrade supply curves to define upgrade resource availability.
$ifthene.hydup2 %GSw_HydroCapEnerUpgradeType% == 2
* Need to re-multiply by 1000 because inclusion of hydUD and hydUND in the ban(i) set with this setting
*   prevents correct scaling of hydro costs.
cost_cap_up(i,v,r,rscbin,t)$cost_cap_up(i,v,r,rscbin,t) = cost_cap_up(i,v,r,rscbin,t) * 1000 ;
cost_ener_up(i,v,r,rscbin,t)$cost_ener_up(i,v,r,rscbin,t) = cost_ener_up(i,v,r,rscbin,t) * 1000 ;

cap_cap_up('hydED','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUD',t,rscbin,"cap") + hyd_add_upg_cap(r,'hydUD',rscbin,t) ;
cap_cap_up('hydEND','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUND',t,rscbin,"cap") + hyd_add_upg_cap(r,'hydUND',rscbin,t) ;
cap_ener_up('hydED','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUD',t,rscbin,"cap")  + hyd_add_upg_cap(r,'hydUD',rscbin,t) ;
cap_ener_up('hydEND','init-1',r,rscbin,t) = m_rsc_dat(r,'hydUND',t,rscbin,"cap") + hyd_add_upg_cap(r,'hydUND',rscbin,t) ;
$endif.hydup2

* Use available decoupled upgrade resource to define sets for allowable decoupled capacity/energy upgrades.
allow_cap_up(i,v,r,rscbin,t)$[valcap(i,v,r,t)$cap_cap_up(i,v,r,rscbin,t)$(t.val>=upgradeyear)] = yes ;
allow_ener_up(i,v,r,rscbin,t)$[valcap(i,v,r,t)$cap_ener_up(i,v,r,rscbin,t)$(t.val>=upgradeyear)] = yes ;

*======================================================
* -- Begin Hourly Temporal Resolution Calculations --
*======================================================

set starting_hour(r,allh)             "Flag for whether allh is the first chronological hour by day type",
    final_hour(r,allh)                "Flag for whether allh is the last chronological hour in a day type"
;
starting_hour(r,allh) = no;
final_hour(r,allh) = no;


* ---- Begin Hourly Calculations ---- *

$ifthene.Hourly %GSw_Hourly% == 1

* created by input_processing/hourly_process.py
set szn_hourly(allszn)
/
$offdelim
$include inputs_case%ds%sznset_hourly.csv
$ondelim
/,

quarter(allszn) "original ReEDS seasons (used in hourly calculations to accommodate hard-coded quarterly season assignments"
/ summ,
  fall,
  wint,
  spri /,

* created by input_processing/hourly_process.py
h_hourly(allh)
/
$offlisting
$offdelim
$include inputs_case%ds%hset_hourly.csv
$ondelim
$onlisting
/,

* created by input_processing/hourly_process.py
h_szn_hourly(allh,allszn)
/
$offlisting
$ondelim
$include inputs_case%ds%h_szn_hourly.csv
$offdelim
$onlisting
/;

* created by input_processing/hourly_process.py
parameter hours_hourly(allh)
/
$offlisting
$ondelim
$include inputs_case%ds%hours_hourly.csv
$offdelim
$onlisting
/;

*enable new set of seasons based on what was produced by hourly_process.py
szn(allszn) = no;
szn(szn_hourly) = yes;

*enable new set of hours based on what was produced by hourly_process.py
h(h_hourly) = yes;
*remove previous h_szn set
h_szn(allh,allszn) = no;
h_szn(h,szn)$h_szn_hourly(h,szn) = yes;
h_szn(h,szn)$[not h_szn_hourly(h,szn)] = no;

hours(h) = hours_hourly(h) ;

hour_szn_group(h,hh) = no ;

set d "set of windows of overlapping hours" /1*1000/ ;

*load in the options for minload windows with nexth
* created by input_processing/hourly_process.py
set h_group_hourly(d,allh,allhh) "windows for minloading constraint with hourly resolution"
/
$include inputs_case%ds%hour_group.txt
/
;

* note that we need the double-indexed sets here since
* cumbersome/impossible to declare both h over the same set of subsets
hour_szn_group(h,hh)$sum{d$h_group_hourly(d,h,hh), 1} = yes ;

*reducing problem size by removing h-hh combos that are the same
hour_szn_group(h,hh)$sameas(h,hh) = no ;

*assumes we're always modeling at least a 24 hour period
hours_daily(h) = 1 ;

* -- chronological hour specification --

* There are three options with the definition of nexth:
*  1. The last hour in the modeled day loops back to the first (with Sw_HourlyWrap = 1)
*  2. The last hour in the modeled day does not loop back to the first,
*     and each region's starting and final hour is based on EST midnight
*  3. The last hour in the modeled day does not loop back to the first,
*     and each region's starting and final hour is based on local midnight
*     Enabled with Sw_HourlyTZAdj_Midnight -- more info in next comment block
*
* Note that the option for Sw_HourlyWrap will dominate the other switches,
* ie if Sw_HourlyWrap = 1, the operations surrounding Sw_HourlyTZAdj_Midnight
*    negate all of its potential modifications to the nexth set

* When there is no infinite loop or hour wrapping enabled (ie Sw_HourlyWrap = 0) we impose
* an exogenous limit on the beginning-hour state of charge for each szn
* when Sw_HourlyTZAdj is enabled, timezone adjustments occur and each
* region's "midnight" is based on its location's timezone, therefore
* we can choose whether to have true region-specific midnight or a uniform midnight
* If Sw_HourlyTZAdj_Midnight = 1, each region (PT, MT, CT, ET) should have their local midnight.
* If Sw_HourlyTZAdj_Midnight = 0, each region will use ET midight (aka universal midnight).

* created by input_processing/hourly_process.py
set hourly_szn_rgn_start(r,allszn, allh) "region and starting hour linkage by season"
/
$offlisting
$ondelim
$include inputs_case%ds%tz_rgn_start_h.csv
$offdelim
$onlisting
/;

* created by input_processing/hourly_process.py
set hourly_szn_rgn_end(r,allszn, allh) "region and ending hour linkage by season"
/
$offlisting
$ondelim
$include inputs_case%ds%tz_rgn_end_h.csv
$offdelim
$onlisting
/;

$offOrder

set starting_hour_notzadj(allh) "starting hour without tz adjustments",
    final_hour_notzadj(allh)    "final hour without tz adjustments" ;

* find the minimum and maximum ordinal of modeled hours within each season
starting_hour_notzadj(h)$[sum{szn,h_szn(h,szn)$(smin(hh$h_szn(hh,szn),ord(hh))=ord(h)) }] = yes ;
final_hour_notzadj(h)$[sum{szn,h_szn(h,szn)$(smax(hh$h_szn(hh,szn),ord(hh))=ord(h)) }] = yes ;

* note summing over szn to find the minimum/maximum ordered hour within that season
starting_hour(r,h)$[sum{szn, hourly_szn_rgn_start(r,szn,h) }$(not Sw_HourlyWrap)] = yes ;
final_hour(r,h)$[sum{szn, hourly_szn_rgn_end(r,szn,h) }$(not Sw_HourlyWrap)] = yes ;

*remove all elements in nexth
nexth(r,h,hh) = no ;
*populate nexth_rh for chronological sequences of hours
nexth(r,h,hh)$[(ord(hh) = ord(h) + 1)] = yes ;

*need to remove those not from the same season
nexth(r,h,hh)$[not sum{szn$[h_szn(h,szn)$h_szn(hh,szn)], 1 }] = no ;

* enable infinite loop and cut links where specified
* note we condition this on both infinite looping or
* on tzadj_midnight - with tzadj_midnight we will
* break the chain of hours based on region-specific
* starting and ending hours
nexth(r,h,hh)$[starting_hour_notzadj(hh)$final_hour_notzadj(h)
              $(Sw_HourlyWrap or Sw_Hourly_Midnight)
              $sum{szn$[h_szn(h,szn)$h_szn(hh,szn)],1 }] = yes ;

* if we are using region/timezone-specific midnights break the infinite loop chain
* at starting and ending hours based on outputs from hourly_process.py
nexth(r,h,hh)$[(not Sw_HourlyWrap)$Sw_Hourly_Midnight$final_hour(r,h)$starting_hour(r,hh)] = no ;

$onOrder

* -- Load and capacity factor determination -- *

* created by input_processing/hourly_process.py
parameter load_hourly(allh,r) "--MWh-- load used in hourly representation"
/
$offlisting
$offdigit
$ondelim
$include inputs_case%ds%load_hourly.csv
$offdelim
$ondigit
$onlisting
/;

* created by input_processing/hourly_process.py
parameter m_cf_hourly(i,r,allh) "--unitless-- capacity factors for 8760 regions and subregions"
/
$offlisting
$offdigit
$ondelim
$include inputs_case%ds%cf_hourly.csv
$offdelim
$ondigit
$onlisting
/;

* -- Assumption copied from above --
*Assign hybrid PV+battery to have the same value as UPV, but increase the capacity factor to account for clipped energy
*  capacity factor = Gen[MWh] / (Cap[MW]  * 8760[h])
*  Increase Generation by 0.2%, then: cf_adjusted = Generation * 1.002 / (Capacity * 8760) = cf * 1.002
*  0.2% is an estimate and will be revised once PVB technologies are converted to use DC input profiles
m_cf_hourly(i,r,h)$[pvb(i)$Sw_PVB] =  sum{ii$[upv(ii)$rsc_agg(ii,i)], m_cf_hourly(ii,r,h) } * (1 + 0.002) ;

* created by input_processing/hourly_process.py
parameter can_hourly(r,allh,allt) "--MWh-- static canadian imports computed in hourly_process.py"
/
$offlisting
$offdigit
$ondelim
$include inputs_case%ds%can_hourly.csv
$offdelim
$ondigit
$onlisting
/;

* created by input_processing/hourly_process.py
set h_szn_prm_hourly(allh,allszn) "hour to season linkage representing each season's peak hour for nd_hydro in the planning reserve margin constraint"
/
$offlisting
$offdigit
$ondelim
$include inputs_case%ds%h_szn_prm_hourly.csv
$offdelim
$ondigit
$onlisting
/;

* created by input_processing/hourly_process.py
parameter frac_h_quarter_weights_hourly(allh,quarter) "--unitless-- fraction of each modeled in each quarterly season for use setting quarter-hardcoded parameters "
/
$offlisting
$offdigit
$ondelim
$include inputs_case%ds%frac_h_quarter_weights_hourly.csv
$offdelim
$ondigit
$onlisting
/;

* created by input_processing/hourly_process.py
parameter peak_dem_hourly_load(r,allszn) "peak demand used in the planning reserve margin constraint"
/
$offlisting
$offdigit
$ondelim
$include inputs_case%ds%peak_dem_hourly_load.csv
$offdelim
$ondigit
$onlisting
/;

*recalculate census division-level gas price adders
gasadder_cd(cendiv,t,h) = (gasprice_ref(cendiv,t) - gasprice_nat(t))/2 ;
*winter gas gets marked up
gasadder_cd(cendiv,t,h) = gasadder_cd(cendiv,t,h) + .04 * frac_h_quarter_weights_hourly(h,"wint") * gasprice_ref(cendiv,t) ;

*winter gets a gas price adjustment - hardcoded from above
szn_adj_gas(h) = 1 ;
szn_adj_gas(h) = szn_adj_gas(h) + frac_h_quarter_weights_hourly(h,"wint") * 1.054 ;

*redefine CSAPR weights for new season definitions
h_weight_csapr(h) = 0 ;
h_weight_csapr(h) = frac_h_quarter_weights_hourly(h,"spri") * 0.3333 ;
h_weight_csapr(h) = frac_h_quarter_weights_hourly(h,"summ") * 1 ;
h_weight_csapr(h) = frac_h_quarter_weights_hourly(h,"fall") * 0.3333 ;

*redefine h_szn_prm with new temporal resolution
h_szn_prm(allh,allszn) = no;
h_szn_prm(allh,allszn)$h_szn_prm_hourly(allh,allszn) = yes;

*again - canadian imports are summed over corresponding 8760 hours
*therefore need to adjust by number of representative hours
net_trade_can(r,h,t)$rfeas(r) = can_hourly(r,h,t) / hours(h) ;

*only Sw_Canada = 2 is currently compatible with Sw_Hourly
*only alternative to consider would be if Sw_Canada = 0 (trade off)
*can alleviate concerns on previous situtation by conditioning on itself
Sw_Canada$Sw_Canada = 2 ;

*-- capacity factor and availability assignments --*

*replace csp values given csp is all csp1_X in m_cf_hourly
m_cf_hourly(i,r,h)$[sum{ii,tg_rsc_cspagg(ii,i) }] =
                     sum{ii$tg_rsc_cspagg(ii,i),m_cf_hourly(ii,r,h) } ;

m_cf_hourly("csp-ns",r,h) = m_cf_hourly("csp2_1",r,h) ;

*populate a set of technologies so we can trim down the next few cf calculations...
set cf_in_hourly(i) "set to subset operations on hourly capacity factor calculations",
    avail_reduction(i,v) "set to subset operations on hourly avail calculation" ;

cf_in_hourly(i)$[sum{(r,h), m_cf_hourly(i,r,h) }] = yes ;

*add techs we know have CFs that need to get replaced
cf_in_hourly(i)$[pv(i) or wind(i) or csp(i)] = yes ;

*only care about i/v/r combinations that have any valcap specifications
avail_reduction(i,v)$sum{(r,t)$tmodel_new(t), valcap(i,v,r,t) } = yes ;

*populate one values which will get replaced in next few steps
avail(i,v,h)$[avail_reduction(i,v)] = 1 ;

* Assume no plant outages in the summer, adjust the planned outages to account for no planned outages in summer
avail(i,v,h)$[avail_reduction(i,v)$(forced_outage(i) or planned_outage(i))]
                              = (1 - forced_outage(i))
                              * (1 - planned_outage(i)* sum{quarter$[not sameas(quarter,"summ")],
                                  frac_h_quarter_weights_hourly(h,quarter) } * 365 / 273) ;

*Existing geothermal plants have a 75% availability rate based on historical capacity factors
avail(i,initv,h)$[avail_reduction(i,initv)$geo(i)] = 0.75 ;

*upgrade plants assume the same availability of what they are upgraded to
avail(i,v,h)$[upgrade(i)$avail_reduction(i,v)]
                = sum{ii$upgrade_to(i,ii), avail(ii,v,h) } ;

*need to have the capacity factors from hourlize scaled up or down based on
*what is being read in as windcfin since windcfin reflects the national average cf
* calculation here is (m_cf_hourly / cf_avg_wind) * windcfin
* this can be interpreted as converting m_cf_hourly to an index relative to the annual
* average capacity factor then multiplying it by the class-specific but
* national, annual capacity factor which can be scenario-dependent

* created by input_processing/hourly_process.py
parameter cf_avg_wind(i,r) "annual average capacity factors for wind from hourly_process.py"
/
$offlisting
$ondelim
$include inputs_case%ds%hourly_windcf_annavg.csv
$offdelim
$onlisting
/;

*static load is adjusted for census-level growth rates and distribution losses
*same calculation as above
load_exog_static(r,h,t)$rfeas(r) =
      load_hourly(h,r) * sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t) } / (1.0 - distloss) ;

*assign day hours to when PV capacity factors are available
*dynamic calculation given potential variations in temporal resolution
*that can be addressed with another hardcoded set
dayhours(h)$[sum{(i,v,r,t)$[pv(i)$valcap(i,v,r,t)], m_cf(i,v,r,h,t) }] = yes ;

*-- minloadfrac assignment --*
*set to default values
minloadfrac(r,i,h)$[rfeas(r)] = minloadfrac0(i) ;

*CSP minloadfrac is hardcoded in (from above)
minloadfrac(r,i,h)$[rfeas(r)$CSP(i)] = 0.15 ;

*set values for coal which do not have a minloadfrac - also hardcoded from above
minloadfrac(r,i,h)$[coal(i)$(not minloadfrac(r,i,h))$rfeas(r)] = 0.5 ;

*upgrade techs get their corresponding upgraded-to minloadfracs
minloadfrac(r,i,h)$[rfeas(r)$upgrade(i)] =
        sum{ii$upgrade_to(i,ii), minloadfrac(r,ii,h) } ;

*water tech assignment
minloadfrac(r,i,h)$[i_water_cooling(i)$Sw_WaterMain] =
        sum{ii$ctt_i_ii(i,ii), minloadfrac(r,ii,h) } ;

*remove minloadfrac for non-viable generators
minloadfrac(r,i,h)$[(not sum{(v,t), valgen(i,v,r,t) })] = 0 ;

parameter szn_quarter_weights(allszn,quarter) "weights of hourly szns with respect to default, quarterly seasons" ;

alias(quarter,q2) ;

szn_quarter_weights(szn,quarter) = sum{h,frac_h_quarter_weights_hourly(h,quarter) }
                                 / sum{(h,q2),frac_h_quarter_weights_hourly(h,q2) } ;

watsa(wst,r,szn,t) = sum{quarter, szn_quarter_weights(szn,quarter) * watsa(wst,r,quarter,t) } ;
cf_hyd(i,szn,r,t) = sum{quarter, szn_quarter_weights(szn,quarter) * cf_hyd(i,quarter,r,t) } ;
cfhist_hyd(r,t,szn,i) = sum{quarter, szn_quarter_weights(szn,quarter) * cfhist_hyd(r,t,quarter,i) } ;
cap_hyd_szn_adj(i,szn,r) = sum{quarter, szn_quarter_weights(szn,quarter) * cap_hyd_szn_adj(i,quarter,r) } ;
ev_dynamic_demand(r,szn,allt) = sum{quarter, szn_quarter_weights(szn,quarter) * ev_dynamic_demand(r,quarter,allt) } ;
hydmin(i,r,szn) = sum{quarter, szn_quarter_weights(szn,quarter) * hydmin(i,r,quarter) } ;

*set seasonal values for minloadfrac for hydro techs
minloadfrac(r,i,h)$[rfeas(r)$sum{szn$h_szn(h,szn), hydmin(i,r,szn) }] =
        sum{szn$h_szn(h,szn), hydmin(i,r,szn) } ;


*adjust from 2010 base year to 2012 with load_multiplier
peakdem_static_szn(r,szn,t)$rfeas(r) = peak_dem_hourly_load(r,szn) *
                                          sum{cendiv$r_cendiv(r,cendiv), load_multiplier(cendiv,t)
                                              / load_multiplier(cendiv,"2012") }
                                          / (1.0 - distloss) ;

* convert m_cf_hourly to index
m_cf_hourly(i,r,h)$[wind(i)$cf_avg_wind(i,r)] = m_cf_hourly(i,r,h) / cf_avg_wind(i,r) ;

*recalculate capacity factors for non-h17 regions
* -- for non-hydro techs:
m_cf(i,v,r,h,t)$[cf_tech(i)$valcap(i,v,r,t)$cf_in_hourly(i)$(not hydro(i))] =
        m_cf_hourly(i,r,h)
        * cf_adj_t(i,v,t)
        * (avail(i,v,h)$[not pvb(i)] + 1$pvb(i))
;


* -- for hydro techs:
m_cf(i,v,r,h,t)$[cf_tech(i)$valcap(i,v,r,t)$hydro(i)] =
        sum{(szn)$h_szn(h,szn),cfhist_hyd(r,t,szn,i) }
        * sum{szn$h_szn(h,szn),cf_hyd(i,szn,r,t) }
        * cf_adj_t(i,v,t)
        * avail(i,v,h)
;

* re-compute m_cf_szn
m_cf_szn(i,v,r,szn,t)$[cf_tech(i)$valcap(i,v,r,t)] =
    sum{h$h_szn(h,szn), hours(h) * m_cf(i,v,r,h,t) }
      / sum{h$h_szn(h,szn), hours(h) } ;


parameter all_load(allh,allszn) "placeholder calculation to sum load over all regions for each timeslice" ;
all_load(h,szn) = sum{r$rfeas(r), load_exog_static(r,h,"2010") } ;
*populate h_szn_prm with the highest load per season
h_szn_prm(h,szn) = no ;
h_szn_prm(h,szn)$[(smax(hh$h_szn(hh,szn),all_load(hh,szn)) = all_load(h,szn))] = yes ;

maxload_szn(r,h,t,szn) = no;
maxload_szn(r,h,t,szn)$[h_szn(h,szn)$(smax(hh$h_szn(hh,szn),load_exog_static(r,hh,t)) = load_exog_static(r,h,t))] = yes ;

numdays(szn) = sum{h$h_szn(h,szn), hours(h) } / 24 ;

$endif.hourly

*reduced set of minloading constraints and mingen contributors
*with sw_minloading = 2
minloadfrac(r,i,h)$[geo(i)$(Sw_MinLoading = 2)] = 0 ;
minloadfrac(r,i,h)$[csp(i)$(Sw_MinLoading = 2)] = 0 ;
minloadfrac(r,i,h)$[lfill(i)$(Sw_MinLoading = 2)] = 0 ;

parameter  storage_soc_exog(i,v,r,allh,t) "--MWh-- from Augur, an exogenously-imposed storage state of charge for starting_hour r/h combinations, used when Sw_HourlyInfLoop=0" ;
storage_soc_exog(i,v,r,h,t)$[storage(i)$valcap(i,v,r,t)] = 0 ;
