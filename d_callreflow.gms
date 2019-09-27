
$setglobal ds \

$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix


*globals need for this file:
* restartfile : restart file for REflow_RTO_2_params.gms - NO DEFAULT
* case : case you're running NO DEFAULT
* cur_year : previously-solved year NO DEFAULT
* next_year : year that is next in line following cur_year NO DEFAULT
* --- for convergence in intertemporal case, next_year == cur_year
* gdxfout : gdx file name out - if not set, set to be the same as %case%
* REflowSwitch : switch setting for reflow calculations... default == on

$if not set gdxfout $setglobal gdxfout %case%
$if not set REflowSwitch $setglobal REflowSwitch 'ON'
$if not set calc_csp_cc $setglobal calc_csp_cc '0'


$log 'Running reflow for...'
$log ' restartfile == %restartfile%'
$log ' case == %case%'
$log ' cur_year == %cur_year%'
$log ' next_year == %next_year%'
$log ' calc_csp_cc == %calc_csp_cc%'
$log ' timetype == %timetype%'

* --- Call ReEDS_capacity_credit.py with ReEDS-2.0 outputs ---

$call 'GAMS reeds_capacity_credit.gms o=lstfiles%ds%cc_%cur_year%.lst r=%restartfile% --case=%case% --cur_year=%cur_year% --next_year=%next_year% --calc_csp_cc=%calc_csp_cc% --timetype=%timetype%'

$if not exist outputs%ds%variabilityFiles%ds%cc_out_%case%_%next_year%.gdx $abort 'error in ReEDS_capacity_credit.py for %case% in %cur_year%: check ErrorFile'

* --- Translate R2 outputs to be used in REFLOW ----

$call 'GAMS reflow_rto_2_params.gms o=.%ds%lstfiles%ds%reflow-params_%case%_%next_year%.lst r=%restartfile% --case=%case% --cur_year=%cur_year% --next_year=%next_year% --timetype=%timetype%'
$if errorlevel 1 $abort 'error in parameters for %case% in %next_year%'

* --- RUN REFLOW ---

$call 'GAMS reflow_rto_3.gms o=.%ds%lstfiles%ds%reflow_%case%_%next_year%.lst u1=%next_year% u2=%REflowSwitch% --case=%case%'
$if errorlevel 1 $abort 'error in reflow for %case% in %next_year%'

* --- Translate REFLOW outputs to be used in R2
$call 'Rscript %gams.curdir%%ds%d4_translate_variability.r %gams.curdir% %gams.sysdir% %next_year% %case%' 
