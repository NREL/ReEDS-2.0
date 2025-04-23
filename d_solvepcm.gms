*** Reset years
tmodel(t) = no ;
tmodel("%cur_year%") = yes ;
set t_unfix(t) "year to unfix variables when rerunning a single solve year" ;
t_unfix("%cur_year%") = yes ;

*** Activate PCM mode
Sw_PCM = 1 ;
Sw_MinCF = 0 ;

*** Unfix the operational variables
$include d2_unfix_op.gms

*** Define the h- and szn-dependent parameters
$onMultiR
$include d1_temporal_params.gms
$offMulti

*** Solve it
solve ReEDSmodel minimizing Z using lp ;

*** Abort if the solver returns an error
if (ReEDSmodel.modelStat > 1,
    abort "Model did not solve to optimality",
    ReEDSmodel.modelStat) ;
