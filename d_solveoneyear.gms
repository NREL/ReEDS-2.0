$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

* globals needed for this file:
* case : name of case you're running
* cur_year : current year

*remove any load years
tload(t) = no ;

* --- reset tmodel ---
tmodel(t) = no ;
tmodel("%cur_year%") = yes ;

$log 'Solving sequential case for...'
$log '  Case: %case%'
$log '  Year: %cur_year%'


*** Define the h- and szn-dependent parameters
$onMultiR
$include d1_temporal_params.gms
$offMulti


* need to have values initialized before making adjustments
* thus cannot perform these adjustments until 2010 has solved
$ifthene.post_startyear %cur_year%>%startyear%
* Here we calculate the RHS value of eq_rsc_INVlim because floating point
* differences can cause small number issues that either make the model
* infeasible or result in very tiny number (order 1e-16) in the matrix
rhs_eq_rsc_INVlim(r,i,rscbin,t)$[tmodel(t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$m_rsc_con(r,i)] = 

*capacity indicated by the resource supply curve (with undiscovered geo available
*at the "discovered" amount and hydro upgrade availability adjusted over time)
    m_rsc_dat(r,i,rscbin,"cap") * (
        1$[not geo_hydro(i)] + geo_discovery(i,r,t)$geo_hydro(i))
    + hyd_add_upg_cap(r,i,rscbin,t)$(Sw_HydroCapEnerUpgradeType=1)
* available DR capacity
    + rsc_dr(i,r,"cap",rscbin,t)
* available EVMC capacity
    + rsc_evmc(i,r,"cap",rscbin,t)
*minus the cumulative invested capacity in that region/class/bin...
*Note that yeart(tt) is stricly < here, while it is <= in eq_rsc_INVlim. That is because
*values where yeart(tt)==yeart(t) are variables rather than parameters because they are not
*values from prior solve years.
    - sum{(ii,v,tt)$[valinv(ii,v,r,tt)$(yeart(tt) < yeart(t))$rsc_agg(i,ii)$(not dr(i))],
         INV_RSC.l(ii,v,r,rscbin,tt) * resourcescaler(ii) }
*minus exogenous (pre-start-year) capacity, using its level in the first year (tfirst)
    - sum{(ii,v,tt)$[tfirst(tt)$rsc_agg(i,ii)$(not dr(i))$exog_rsc(i)],
         capacity_exog_rsc(ii,v,r,rscbin,tt) }
* note that the dr(i) term from eq_rsc_INVlim is not included here because the equation
* sums over INV_RSC(t) rather than INV_RSC(tt), so it is not a parameter to be included
* in the RHS.
;


flag_eq_rsc_INVlim(r,i,rscbin,t)$tmodel(t) = no ;

* Identify instances when the RHS values are within rhs_tolerance of zero
flag_eq_rsc_INVlim(r,i,rscbin,t)$[tmodel(t)$rsc_i(i)$m_rscfeas(r,i,rscbin)$m_rsc_con(r,i)
                                 $(rhs_eq_rsc_INVlim(r,i,rscbin,t) > -rhs_tolerance)
                                 $(rhs_eq_rsc_INVlim(r,i,rscbin,t) < rhs_tolerance)] = yes ;

* When RHS is 0 (or close enough), the eq_rsc_INVlim equation says that all relevant INV_RSC are 0.
* Therefore we can set the INV_RSC variable to zero anywhere the flag_eq_rsc_INVlim is true
loop(i$rsc_i(i),
    INV_RSC.fx(ii,v,r,rscbin,t)$[tmodel(t)$m_rscfeas(r,i,rscbin)$m_rsc_con(r,i)
                                $(flag_eq_rsc_INVlim(r,i,rscbin,t))$(valinv(ii,v,r,t)$rsc_agg(i,ii))] = 0 ;
) ;

* set m_capacity_exog to the maximum of either its original amount
* or the amount of upgraded capacity that has occurred in the past "Sw_UpgradeLifespan" years
* to avoid forcing recently upgraded capacity into retirement
if(Sw_Upgrades = 1,

    m_capacity_exog(i,v,r,t)$[valcap(i,v,r,t)$sameas(t,"%cur_year%")
                         $(sum{(ii,tt)$[(tt.val <= t.val)$(t.val - tt.val <= Sw_UpgradeLifespan)
                                       $valcap(ii,v,r,tt)$upgrade_from(ii,i)], UPGRADES.l(ii,v,r,tt) } ) ] =
* [maximum of] initial capacity recorded in d_solveprep
                    max( m_capacity_exog0(i,v,r,t),
* -or- capacity of upgrades that have occurred from this i v r t combination
                    sum{(ii,tt)$[(tt.val <= t.val)$(t.val - tt.val <= Sw_UpgradeLifespan)
                                 $valcap(ii,v,r,tt)$upgrade_from(ii,i)],
                                 UPGRADES.l(ii,v,r,tt) }
    ) ;

) ;

* if the relative growth constraint is turned on, then calculate the growth
* limits for each growth bin
if(Sw_GrowthPenalties > 0,

* Calculate the maximum deployment that could have been achieved in the last modeled
* year. For example, if tmodel is 2023 and the prior two solve years were 2020 and 
* 2015, then we are calculating the maximum deployment that could have occured in
* 2020 at the growth rate specified in gbin1. This requires looking back to tprev
* and the solve year before tprev, hence the need for the yeart(ttt).
* The denominator is simply a discount term, and the multiplication is an associated
* compounding term.
    last_year_max_growth(st,tg,t)$tmodel(t) = 
        sum{(i,v,r,tt)$[valinv(i,v,r,tt)$r_st(r,st)$tg_i(tg,i)$tprev(t,tt)],
            INV.l(i,v,r,tt) } 
        / sum{allt$[(allt.val>sum{tt$tprev(t,tt), sum{ttt$tprev(tt,ttt), yeart(ttt) } })
                   $(allt.val<=sum{tt$tprev(t,tt), yeart(tt) })],
              (growth_bin_size_mult("gbin1") ** (allt.val - sum{tt$tprev(t,tt), sum{ttt$tprev(tt,ttt), yeart(ttt) } } - 1)) }
        * (growth_bin_size_mult("gbin1") ** ((sum{tt$tprev(t,tt), yeart(tt) - sum{ttt$tprev(tt,ttt), yeart(ttt) } }) - 1)) ;

* Now calculate the growth bin size for the current solve year, assuming that the 
* maximum growth allowed in gbin1 happens each year over the current solve period.
    growth_bin_limit("gbin1",st,tg,t)$tmodel(t) = 
        sum{allt$[(allt.val>sum{tt$tprev(t,tt), yeart(tt) })
                 $(allt.val<=yeart(t))],
            last_year_max_growth(st,tg,t) * growth_bin_size_mult("gbin1") ** (allt.val - sum{tt$tprev(t,tt), yeart(tt) }) }
        / (yeart(t) - sum{tt$tprev(t,tt), yeart(tt) }) ;

* Do not allow growth_bin_limit to decline over time (i.e., if a higher growth
* rate was achieved in the past, allow the model to start from that higher level)
    growth_bin_limit("gbin1",st,tg,t)$tmodel(t) = smax{tt, growth_bin_limit("gbin1",st,tg,tt) } ;
   
* If the calculated  gbin1 value is less than the minimum bin size, then set it to the minimum bin size
    growth_bin_limit("gbin1",st,tg,t)$[tmodel(t)$(growth_bin_limit("gbin1",st,tg,t) < gbin_min(tg))$stfeas(st)] = gbin_min(tg) ;

* Now set the size of the remaining bins
    growth_bin_limit(gbin,st,tg,t)$[tmodel(t)$(not sameas(gbin,"gbin1"))] = 
        growth_bin_limit("gbin1",st,tg,t) * (growth_bin_size_mult(gbin) - growth_bin_size_mult("gbin1")) ;

    growth_bin_limit(gbin,st,tg,t)$growth_bin_limit(gbin,st,tg,t) = round(growth_bin_limit(gbin,st,tg,t),0) ;

) ;

$endif.post_startyear

*load in results from the cc/curtailment scripts
$ifthene.tcheck %cur_year%>%GSw_SkipAugurYear%

*indicate we're loading data
tload("%cur_year%") = yes ;

*file written by ReEDS_Augur.py
* loaddcr = domain check (dc) + overwrite values storage previously (r)
$gdxin ReEDS_Augur%ds%augur_data%ds%ReEDS_Augur_%prev_year%.gdx
$loaddcr cc_old_load = cc_old
$loaddcr cc_mar_load = cc_mar
$loaddcr cc_dr_load = cc_dr
$loaddcr sdbin_size_load = sdbin_size
$gdxin

*Note: these values are rounded before they are written to the gdx file, so no need to round them here

* assign old and marginal capacity credit parameters to those
* corresponding to each balancing areas cc region
cc_old(i,r,ccseason,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] =
    sum{ccreg$r_ccreg(r,ccreg), cc_old_load(i,r,ccreg,ccseason,t) } ;

m_cc_mar(i,r,ccseason,t)$[tload(t)$(vre(i) or csp(i) or pvb(i))] =
    sum{ccreg$r_ccreg(r,ccreg), cc_mar_load(i,r,ccreg,ccseason,t) } ;

m_cc_dr(i,r,ccseason,t)$[tload(t)$demand_flex(i)] = cc_dr_load(i,r,ccseason,t) ;

sdbin_size(ccreg,ccseason,sdbin,t)$tload(t) = sdbin_size_load(ccreg,ccseason,sdbin,t) ;

* --- Assign hybrid PV+battery capacity credit ---
$ontext
Limit the capacity credit of hybrid PV such that the total capacity credit from the PV and the battery do not exceed the inverter limit.
  Example: PV = 130 MWdc, Battery = 65 MW, Inverter = 100 MW (PVdc/Battery=0.5; PVdc/INVac=1.3)
  Assuming the capacity credit of the Battery is 65 MW, then capacity credit of the PV is limited to 35 MW or 0.269 (35MW/130MW) on a relative basis.
  Max capacity credit PV [MWac/MWdc] = (Inverter - Battery capacity credit) / PV_dc
                                     = (PV_dc / ILR - PV_dc * BCR) / PV_dc
                                     = 1/ILR - BCR
$offtext
* marginal capacity credit
m_cc_mar(i,r,ccseason,t)$[tload(t)$pvb(i)] = min{ m_cc_mar(i,r,ccseason,t), 1 / ilr(i) - bcr(i) } ;

* old capacity credit
* (1) convert cc_old from MW to a fractional basis, (2) adjust the fractional value to be less than 1/ILR - BCR, (3) multiply by CAP to convert back to MW
cc_old(i,r,ccseason,t)$[tload(t)$pvb(i)$sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)}] =
    min{ cc_old(i,r,ccseason,t) / sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)}, 1 / ilr(i) - bcr(i) }
    * sum{(v,tt)$tprev(t,tt), CAP.l(i,v,r,tt)};

$endif.tcheck

* --- Ingest tax credit phaseout mult --- *

$gdxin outputs%ds%tc_phaseout_data%ds%tc_phaseout_mult_%cur_year%.gdx
$loaddcr tc_phaseout_mult_t_load = tc_phaseout_mult_t
$gdxin

tc_phaseout_mult_t(i,t)$tload(t) = tc_phaseout_mult_t_load(i,t) ;

*if tcphaseout is enabled, overwrite initialization
*this requires re-calculating cost_cap_fin_mult and its various permutations
if(Sw_TCPhaseout > 0,
* apply the phaseout multiplier of the current level for current year
* and all future builds. Note that the value will remain the same for
* the cur_year-available vintage but can be updated for vintages whose
* first year hasn't solved yet. i.e. tc_phaseout_mult will remain constant for all
* current and historically-buildable plants but future plants may get updated.
tc_phaseout_mult(i,v,t)$[tload(t)$(firstyear_v(i,v)>=%cur_year%)] =
    tc_phaseout_mult_t(i,t) ;
);

* --- Start calculations of cost_cap_fin_mult family of parameters --- *
* These are calculated here because the ITC phaseout can influence these parameters,
* and the timing of the phaseout is not known beforehand.
cost_cap_fin_mult(i,r,t) = ccmult(i,t) / (1.0 - tax_rate(t))
    * (1.0-tax_rate(t) * (1.0 - (itc_frac_monetized(i,t) * itc_energy_comm_bonus(i,r) * tc_phaseout_mult_t(i,t)/2.0) )
    * pv_frac_of_depreciation(i,t) - itc_frac_monetized(i,t) * tc_phaseout_mult_t(i,t))
    * degradation_adj(i,t) * financing_risk_mult(i,t) * reg_cap_cost_mult(i,r)
    * eval_period_adj_mult(i,t) ;

cost_cap_fin_mult_noITC(i,r,t) = ccmult(i,t) / (1.0 - tax_rate(t))
    * (1.0-tax_rate(t)*pv_frac_of_depreciation(i,t)) * degradation_adj(i,t)
    * financing_risk_mult(i,t) * reg_cap_cost_mult(i,r) * eval_period_adj_mult(i,t) ;

cost_cap_fin_mult_no_credits(i,r,t) = ccmult(i,t) * reg_cap_cost_mult(i,r) ;

* Assign the PV portion of PVB the value of UPV
cost_cap_fin_mult_pvb_p(i,r,t)$pvb(i) =
    sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult(ii,r,t) } ;

cost_cap_fin_mult_pvb_p_noITC(i,r,t)$pvb(i) =
    sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult_noITC(ii,r,t) } ;

cost_cap_fin_mult_pvb_p_no_credits(i,r,t)$pvb(i) =
    sum{ii$[upv(ii)$rsc_agg(ii,i)], cost_cap_fin_mult_no_credits(ii,r,t) } ;

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
cost_cap_fin_mult(i,r,t)$pvb(i) =
    ( (cost_cap_fin_mult_pvb_p(i,r,t) - 1) * cost_cap_pvb_p(i,t)
    + bcr(i) * (cost_cap_fin_mult_pvb_b(i,r,t) - 1) * cost_cap_pvb_b(i,t) )
    / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_noITC(i,r,t)$pvb(i) =
    ( (cost_cap_fin_mult_pvb_p_noITC(i,r,t) - 1) * cost_cap_pvb_p(i,t)
    + bcr(i) * (cost_cap_fin_mult_pvb_b_noITC(i,r,t) - 1) * cost_cap_pvb_b(i,t) )
    / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

cost_cap_fin_mult_no_credits(i,r,t)$pvb(i) =
    ((cost_cap_fin_mult_pvb_p_no_credits(i,r,t) - 1) * cost_cap_pvb_p(i,t)
    + bcr(i) * (cost_cap_fin_mult_pvb_b_no_credits(i,r,t) - 1) * cost_cap_pvb_b(i,t))
    / (cost_cap_pvb_p(i,t) + bcr(i) * cost_cap_pvb_b(i,t)) + 1 ;

* --- Upgrades ---
*Assign upgraded techs the same multipliers as the techs they are upgraded from
*This assignment must take place after expanding for water techs, if applicable.

if(Sw_WaterMain=1,
cost_cap_fin_mult(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult(ii,r,t) } ;

cost_cap_fin_mult_noITC(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult_noITC(ii,r,t) } ;

cost_cap_fin_mult_no_credits(i,r,t)$i_water_cooling(i) =
    sum{(ii)$[ctt_i_ii(i,ii)], cost_cap_fin_mult_no_credits(ii,r,t) } ;
) ;

cost_cap_fin_mult(i,r,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_cap_fin_mult(ii,r,t) } ;
cost_cap_fin_mult_noITC(i,r,t)$upgrade(i) = sum{ii$upgrade_to(i,ii), cost_cap_fin_mult_noITC(ii,r,t) } ;

* --- Nuclear Ban ---
*Assign increased cost multipliers to regions with state nuclear bans
if(Sw_NukeStateBan = 2,
  cost_cap_fin_mult(i,r,t)$[nuclear(i)$nuclear_ba_ban(r)] =
    cost_cap_fin_mult(i,r,t) * nukebancostmult ;

  cost_cap_fin_mult_noITC(i,r,t)$[nuclear(i)$nuclear_ba_ban(r)] =
    cost_cap_fin_mult_noITC(i,r,t) * nukebancostmult ;
) ;

* Start by setting all multipliers to 1
rsc_fin_mult(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;
rsc_fin_mult_noITC(i,r,t)$[valcap_irt(i,r,t)$rsc_i(i)] = 1 ;

*Hydro and pumped-hydrohave capital costs included in the supply curve,
* so change their multiplier to be the same as cost_cap_fin_mult
rsc_fin_mult(i,r,t)$hydro(i) = cost_cap_fin_mult('hydro',r,t) ;
rsc_fin_mult(i,r,t)$psh(i) = cost_cap_fin_mult(i,r,t) ;
rsc_fin_mult_noITC(i,r,t)$hydro(i) = cost_cap_fin_mult_noITC('hydro',r,t) ;
rsc_fin_mult_noITC(i,r,t)$psh(i) = cost_cap_fin_mult_noITC(i,r,t) ;

* Apply cost reduction multipliers for geothermal hydro and offshore wind
rsc_fin_mult(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult(i,r,t) * hydrocapmult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$[hydro(i) or psh(i)] = rsc_fin_mult_noITC(i,r,t) * hydrocapmult(t,i) ;

* Create a new parameter to hold capital financing multipliers with and without ITC for OSW transmission costs inside the resource supply curve cost
* Currently, OSW receives federal incentives in both its capital and transmission costs, hence this custom application for OSW
rsc_fin_mult(i,r,t)$ofswind(i) = cost_cap_fin_mult(i,r,t) * ofswind_rsc_mult(t,i) ;
rsc_fin_mult_noITC(i,r,t)$ofswind(i) = cost_cap_fin_mult_noITC(i,r,t) ;

*trimming the cost_cap_fin_mult parameters to reduce file sizes
cost_cap_fin_mult(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                         $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                         $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

cost_cap_fin_mult_noITC(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                               $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                               $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

cost_cap_fin_mult_no_credits(i,r,t)$[(not valinv_irt(i,r,t))$(not upgrade(i))
                                    $(not sum{(v,rscbin), allow_cap_up(i,v,r,rscbin,t) })
                                    $(not sum{(v,rscbin), allow_ener_up(i,v,r,rscbin,t) })] = 0 ;

*round the cost_cap_fin_mult parameters, since they were re-calculated
cost_cap_fin_mult(i,r,t)$cost_cap_fin_mult(i,r,t)
  = round(cost_cap_fin_mult(i,r,t),3) ;

cost_cap_fin_mult_noITC(i,r,t)$cost_cap_fin_mult_noITC(i,r,t)
  = round(cost_cap_fin_mult_noITC(i,r,t),3) ;

cost_cap_fin_mult_no_credits(i,r,t)$cost_cap_fin_mult_no_credits(i,r,t)
  = round(cost_cap_fin_mult_no_credits(i,r,t),3) ;

rsc_fin_mult(i,r,t)$rsc_fin_mult(i,r,t) = round(rsc_fin_mult(i,r,t),3) ;

*Set cost_cap_fin_mult_out equal to cost_cap_fin_mult before we alter cost_cap_fin_mult for Virginia policy
*and zero carbon policy.
cost_cap_fin_mult_out(i,r,t) = cost_cap_fin_mult(i,r,t) ;

*Penalizing new gas built within cost recovery period of 20 years for states that require fossil retirements
cost_cap_fin_mult(i,r,t)$[gas(i)$valcap_irt(i,r,t)$sum{st$r_st(r,st), ng_crf_penalty_st(t,st) }] =
    cost_cap_fin_mult(i,r,t) * sum{st$r_st(r,st), ng_crf_penalty_st(t,st) } ;

*Penalizing new gas that can be upgraded to recover upgrade costs prior to upgrade within 20 years of a zero carbon policy
cost_cap_fin_mult(i,r,t)$[gas(i)$(not ccs(i))] =
    cost_cap_fin_mult(i,r,t) * (((ng_carb_lifetime_cost_adjust(t) - 1) * .2) + 1) ;

* --- End calculations of cost_cap_fin_mult family of parameters --- *

* --- Estimate curtailment from "old" hybrid PV+battery ---

$ifthene %cur_year%==%startyear%
*initialize CAP.l for 2010 because it has not been defined yet
CAP.l(i,v,r,"%startyear%")$[m_capacity_exog(i,v,r,"%startyear%")] = m_capacity_exog(i,v,r,"%startyear%") ;
$endif

* Now that cost_cap_fin_mult is done, calculate cost_growth, which is
* the minimum cost of that technology within a state
if(Sw_GrowthPenalties > 0,
*rsc_fin_mult holds the multipliers for hydro, psh, and geo techs, so don't include them here
    cost_growth(i,st,t)$[tmodel(t)$sum{r$[r_st(r,st)], valinv_irt(i,r,t) }$stfeas(st)$(not (geo(i) or hydro(i) or psh(i)))] = 
        smin{r$[valinv_irt(i,r,t)$r_st(r,st)$cost_cap_fin_mult(i,r,t)$cost_cap(i,t)],
            cost_cap_fin_mult(i,r,t) * cost_cap(i,t) } ;

*rsc_fin_mult holds the multipliers for hydro, psh, and geo techs
    cost_growth(i,st,t)$[tmodel(t)$sum{r$[r_st(r,st)], valinv_irt(i,r,t) }$stfeas(st)$(geo(i) or hydro(i) or psh(i))] = 
        smin{(r,rscbin)$[valinv_irt(i,r,t)$r_st(r,st)$rsc_fin_mult(i,r,t)$m_rsc_dat(r,i,rscbin,"cost")],
            rsc_fin_mult(i,r,t) * m_rsc_dat(r,i,rscbin,"cost") } ;

    cost_growth(i,st,t)$cost_growth(i,st,t) = round(cost_growth(i,st,t),3) ;
) ;

* Write the inputs for debugging and error checks:
* Always write data for the first solve year (currently always 2010).
* Overwrites the versions written by d_solveprep.gms and d1_temporal_params.gms.
$ifthene.write %cur_year%=%startyear%
execute_unload 'inputs_case%ds%inputs.gdx' ;
$endif.write

* If using debug mode, write the inputs for every solve year
$ifthene.debug %debug%>0
execute_unload 'alldata_%stress_year%.gdx' ;
$endif.debug


* --- diagnoses gdx dump settings ---
$ifthene.diagnose %diagnose%=1
$ifthene.diagnose_2 %diagnose_year%<=%cur_year%
$include inputs_case%ds%diagnose.gms
$endif.diagnose_2
$endif.diagnose

* ------------------------------
* Solve the Model
* ------------------------------
$ifthen.valstr %GSw_ValStr% == 1
OPTION lp = convert ;
ReEDSmodel.optfile = 1 ;
$echo dumpgdx ReEDSmodel_jacobian.gdx > convert.opt
solve ReEDSmodel minimizing z using lp ;
OPTION lp = %solver% ;
ReEDSmodel.optfile = %GSw_gopt% ;
OPTION savepoint = 1 ;
$endif.valstr

solve ReEDSmodel minimizing z using lp ;
tsolved(t)$tmodel(t) = yes ;

if(Sw_NewValCapShrink = 1,

* remove newv dimensions for technologies that do not have capacity in this year
* and if it is not a vintage you can build in future years 
* and if the plant has not been upgraded
* note since we're applying this only to new techs the upgrades portion 
* needs to be present in combination with the ability to be built in future periods
* said differently, we want to make sure the vintage cannot be built in future periods,
* it hasn't been built yet, and it has no associated upgraded units
* here the second year index tracks which year has just solved
    valcap_remove(i,v,r,t,"%cur_year%")$[newv(v)$valcap(i,v,r,t)$ivt(i,v,"%cur_year%")
* if there is no capacity..
                       $(not CAP.l(i,v,r,"%cur_year%"))
* if you have not invested in it..
                       $(not sum(tt$[(yeart(tt)<=%cur_year%)], INV.l(i,v,r,tt) ))
* if you cannot invest in the ivt combo in future years..
                       $(not sum{tt$[tt.val>%cur_year%],ivt(i,v,tt)})
                       $(not sum(tt$[valinv(i,v,r,tt)$(yeart(tt)>%cur_year%)],1))
* if it has not been upgraded..
* note the newv condition above allows for the capacity equations
* of motion to still function - this would/does not work for initv vintanges without additional work
                       $(not sum{(tt,ii)$[tsolved(tt)$upgrade_from(ii,i)$valcap(ii,v,r,tt)], 
                                UPGRADES.l(ii,v,r,tt)})
                       ] = yes ;
    valcap(i,v,r,t)$valcap_remove(i,v,r,t,"%cur_year%") = no ;
    valgen(i,v,r,t)$valcap_remove(i,v,r,t,"%cur_year%") = no ;
    valinv(i,v,r,t)$valcap_remove(i,v,r,t,"%cur_year%") = no ;
    inv_cond(i,v,r,t,"%cur_year%")$valcap_remove(i,v,r,t,"%cur_year%") = no ;
    valcap_irt(i,r,t) = sum{v, valcap(i,v,r,t) } ;
    valcap_iv(i,v)$sum{(r,t)$tmodel_new(t), valcap(i,v,r,t) } = yes ;
    valcap_i(i)$sum{v, valcap_iv(i,v) } = yes ;
    valcap_ivr(i,v,r)$sum{t, valcap(i,v,r,t) } = yes ;
    valgen_irt(i,r,t) = sum{v, valgen(i,v,r,t) } ;
    valinv_irt(i,r,t) = sum{v, valinv(i,v,r,t) } ;
    valinv_tg(st,tg,t)$sum{(i,r)$[tg_i(tg,i)$r_st(r,st)], valinv_irt(i,r,t) } = yes ;

) ; 



$ontext
* the removal of these computed sets would be more complete
* but the vintage-agnostic approach does not allow for their proper representation
* -however- these only apply as constraint generation conditions and
* will not create free/unbounded variables within the model

    valinv_irt(i,r,t)$[valinv_irt(i,r,t)$
                      sum{v, valcap_remove(i,v,r,t,"%cur_year%")}] = no ;

    valinv_tg(st,tg,t)$[valinv_tg(st,tg,t)
                       $sum{(i,v,r)$[tg_i(tg,i)$r_st(r,st)], 
                        valcap_remove(i,v,r,t,"%cur_year%")}] = no ;

$offtext
*record objective function values right after solve
z_rep(t)$tmodel(t) = Z.l ;
z_rep_inv(t)$tmodel(t) = Z_inv.l(t) ;
z_rep_op(t)$tmodel(t) = Z_op.l(t) ;

if(Sw_Upgrades = 1,
* note sum over tt required here as we want to only remove the incentive
* from years beyond the current year if upgrades occurred in this solve year

* extend the current-year incentive beyond current date to expiration date - only needed
* when needing to specify beyond current amounts
    co2_captured_incentive(i,v,r,t)$[sum{tt$tmodel(tt),upgrades.l(i,v,r,tt) }
                                    $(not sum{tt$tfix(tt),upgrades.l(i,v,r,tt)})
                                    $(year(t) < %cur_year% + co2_capture_incentive_length)
                                    $(yeart(t) >= %cur_year%)
                                    $valcap(i,v,r,t) ] = co2_captured_incentive(i,v,r,"%cur_year%") ;

* remove co2 captured incentive after the length of time if upgrades occurred in this year
    co2_captured_incentive(i,v,r,t)$[sum{tt$tmodel(tt),upgrades.l(i,v,r,tt) }
                                    $(year(t) >= %cur_year% + co2_capture_incentive_length)
                                    $valcap(i,v,r,t) ] = 0 ;

* adjust fom of upgraded-from plant to updated cost for maintaining the CCS equipment
    cost_fom(i,v,r,t)$[sum{(ii,tt)$[tmodel(tt)$upgrade_from(ii,i)],upgrades.l(ii,v,r,tt) }
                                    $(year(t) >= %cur_year%)
                                    $valcap(i,v,r,t) ] =
        max(cost_fom(i,v,r,t),
            sum{ii$upgrade_from(ii,i),cost_fom(ii,v,r,t) }
           ) ;
) ;

$include d2_varfix.gms

*dump data to be used by Augur
$include d3_augur_data_dump.gms

*dump data for tax credit phaseout calculations
parameter
  emit_r_tc(r,t)  "--metric tons-- CO2 emissions, regional"
  emit_nat_tc(t)  "--metric tons-- CO2 emissions, national"
;

* emit_r_tc is calculated the same as the EMIT variable in the model. We do not use
* EMIT.l here because the emissions are only modeled for those in the emit_modeled
* set.
emit_r_tc(r,t)$tmodel_new(t) = 

* Emissions from generation
    sum{(i,v,h)$[valgen(i,v,r,t)$h_rep(h)],
        hours(h) * emit_rate("CO2",i,v,r,t)
        * (GEN.l(i,v,r,h,t)
           + CCSFLEX_POW.l(i,v,r,h,t)$[ccsflex(i)$(Sw_CCSFLEX_BYP OR Sw_CCSFLEX_STO OR Sw_CCSFLEX_DAC)])
       }

* Plus emissions produced via production activities (SMR, SMR-CCS, DAC)
* The "production" of negative CO2 emissions via DAC is also included here
    + sum{(p,i,v,h)$[valcap(i,v,r,t)$i_p(i,p)$h_rep(h)],
          hours(h) * prod_emit_rate("CO2",i,t)
          * PRODUCE.l(p,i,v,r,h,t)
         }

*[minus] co2 reduce from flexible CCS capture
*capture = capture per energy used by the ccs system * CCS energy

* Flexible CCS - bypass
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_byp(i)$h_rep(h)],
        ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POW.l(i,v,r,h,t) })$Sw_CCSFLEX_BYP

* Flexible CCS - storage
    - (sum{(i,v,h)$[valgen(i,v,r,t)$ccsflex_sto(i)$h_rep(h)],
        ccsflex_co2eff(i,t) * hours(h) * CCSFLEX_POWREQ.l(i,v,r,h,t) })$Sw_CCSFLEX_STO
;

emit_nat_tc(t)$tmodel_new(t) = sum{r, emit_r_tc(r,t) } ;
* [metric kiloton] * [1000 metric ton / metric kiloton] / ([MW] * [hours]) = [metric ton/MWh]
$ifthen.stateco2 %GSw_StateCO2ImportLevel% == 'r'
    co2_emit_rate_r(r,t)$tmodel(t) = (
        emit_r_tc(r,t)
        / sum{(i,v,h)$[valgen(i,v,r,t)], hours(h) * GEN.l(i,v,r,h,t) }
* Avoid division-by-zero errors
    )$sum{(i,v,h)$[valgen(i,v,r,t)], hours(h) * GEN.l(i,v,r,h,t) } ;
$else.stateco2
* sum emissions and generation within the region
    co2_emit_rate_regional(%GSw_StateCO2ImportLevel%,t)$tmodel(t) = (
        sum{rr$r_%GSw_StateCO2ImportLevel%(rr,%GSw_StateCO2ImportLevel%),
            emit_r_tc(rr,t) }
        / sum{(i,v,rr,h)$[valgen(i,v,rr,t)
                        $r_%GSw_StateCO2ImportLevel%(rr,%GSw_StateCO2ImportLevel%)],
              hours(h) * GEN.l(i,v,rr,h,t) }
* Avoid division-by-zero errors
    )$sum{(i,v,rr,h)$[valgen(i,v,rr,t)
                    $r_%GSw_StateCO2ImportLevel%(rr,%GSw_StateCO2ImportLevel%)],
          hours(h) * GEN.l(i,v,rr,h,t) }
    ;
* broadcast the regional emissions rate to each r in the region
    co2_emit_rate_r(r,t)$tmodel(t) =
        sum{%GSw_StateCO2ImportLevel%
            $r_%GSw_StateCO2ImportLevel%(r,%GSw_StateCO2ImportLevel%),
            co2_emit_rate_regional(%GSw_StateCO2ImportLevel%,t) }
    ;
$endif.stateco2


execute_unload "outputs%ds%tc_phaseout_data%ds%emit_for_tc_phaseout_calc_%cur_year%.gdx"
  emit_nat_tc, emit_r_tc
;

* Abort if the solver returns an error
if (ReEDSmodel.modelStat > 1,
    abort "Model did not solve to optimality",
    ReEDSmodel.modelStat) ;
