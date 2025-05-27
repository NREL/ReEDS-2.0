* =============================================
* REPORT ELECTRICITY PRICE BY COST COMPONENT
* =============================================

$onmulti
parameter
	vscale		Value scale
	elecost		Cost of electricity generation;
$offmulti

vscale(t)$tmodel(t) = (1/cost_scale) * (1/pvf_onm(t));

loop((usrep_r,t)$(sum(r,r_u(r,usrep_r))$tmodel(t)),

elecost(usrep_r,t,'total')
	= sum((r,h)$(r_u(r,usrep_r)$h_rep(h)), vscale(t) * eq_loadcon.m(r,h,t) * LOAD.l(r,h,t))
		/ sum((r,h)$(r_u(r,usrep_r)$h_rep(h)), hours(h) * load.l(r,h,t)) ;

elecost(usrep_r,t,'total_unf')
	= sum((r,h)$(r_u(r,usrep_r)), vscale(t) * eq_loadcon.m(r,h,t) * LOAD.l(r,h,t))
		/ sum((r,h)$(r_u(r,usrep_r)), hours(h) * load.l(r,h,t)) ;


elecost(usrep_r,t,'energy')
	= sum((r,h)$(r_u(r,usrep_r)$h_rep(h)), vscale(t)*eq_supply_demand_balance.m(r,h,t)*LOAD.l(r,h,t))
	/ sum((r,h)$(r_u(r,usrep_r)$h_rep(h)), hours(h)*LOAD.l(r,h,t));

elecost(usrep_r,t,'opres')
	= sum((ortype,r,h)$(r_u(r,usrep_r)), 
		vscale(t)*eq_OpRes_requirement.m(ortype,r,h,t)*orperc(ortype,"or_load")*LOAD.l(r,h,t))
	/ sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.l(r,h,t));

elecost(usrep_r,t,'Rec_require')
	= sum((RPSCat,r,st,h)$(r_st(r,st)$r_u(r,usrep_r)), 
		vscale(t)*eq_REC_Requirement.m(RPSCat,st,t)*RecPerc(RPSCat,st,t)*hours(h)*LOAD.l(r,h,t)*(1.0 - distloss))
	/ sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.l(r,h,t));

elecost(usrep_r,t,'Rec_ooslim')
	= - sum((RPSCat,r,st,h)$(r_st(r,st)$r_u(r,usrep_r)), 
		vscale(t)*eq_REC_ooslim.m(RPSCat,st,t)*RPS_oosfrac(st)
			*RecPerc(RPSCat,st,t)*hours(h)*LOAD.l(r,h,t)*(1.0 - distloss))
	/ sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.l(r,h,t));

elecost(usrep_r,t,'Rec_unbundled')
	= - sum((RPSCat,r,st,h)$(r_st(r,st)$r_u(r,usrep_r)), 
*		vscale(t)*eq_REC_unbundledLimit.m(RPSCat,st,t)*RPS_unbundled_limit(st)
		vscale(t)*eq_REC_unbundledLimit.m(RPSCat,st,t)*0.1
			*RecPerc(RPSCat,st,t)*hours(h)*LOAD.l(r,h,t)*(1.0 - distloss))
	/ sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.l(r,h,t));

*elecost(usrep_r,t,'inertia')
*	= sum((r,rto,h)$(r_rto(r,rto)$r_u(r,usrep_r)), 
*		vscale(t)*eq_inertia_requirement.m(rto,h,t)*inertia_req(t)*LOAD.l(r,h,t)/distloss)
*	/ sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.l(r,h,t));

elecost(usrep_r,t,'natgen') 
	= sum((r,h)$(r_u(r,usrep_r)),
		vscale(t)*eq_national_gen.m(t)*national_gen_frac(t)*hours(h)
			*(LOAD.l(r,h,t)$[Sw_GenMandate = 1]
				+ (LOAD.l(r,h,t)*(1.0 - distloss))$[Sw_GenMandate = 2]
			))
	/ sum((r,h)$(r_u(r,usrep_r)), hours(h)*LOAD.l(r,h,t));

elecost(usrep_r,t,"bal") 
	= elecost(usrep_r,t,'total')
	- elecost(usrep_r,t,'energy')
	- elecost(usrep_r,t,'opres')
	- elecost(usrep_r,t,'Rec_require')
	- elecost(usrep_r,t,'Rec_ooslim')
	- elecost(usrep_r,t,'Rec_unbundled')
*	- elecost(usrep_r,t,'inertia')
	- elecost(usrep_r,t,'natgen')
	;

);

*.display elecost;