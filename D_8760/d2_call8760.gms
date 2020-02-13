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


*globals need for this file:
* restartfile : restart file for curt_params.gms - NO DEFAULT
* case : case you're running NO DEFAULT
* cur_year : previously-solved year NO DEFAULT
* next_year : year that is next in line following cur_year NO DEFAULT
* --- for convergence in intertemporal case, next_year == cur_year
* gdxfout : gdx file name out - if not set, set to be the same as %case%
* Interconnect : default 'US'
* LDCvariabilitySwitch : which LDC calculations to do -- default == CConly
* DistPVSwitch : name for distributed PV switch
* ReFlowSwitch : switch setting for 8760 calculations... default == on
* HourlyStaticFile : file for static inputs default as of India_8760

$if not set gdxfout $setglobal gdxfout %case%
$if not set Interconnect $setglobal Interconnect 'India'
$if not set Do8760Switch $setglobal Do8760Switch 'ON'
$if not set LDCvariabilitySwitch $setglobal LDCvariabilitySwitch 'CConly' 
$if not set HourlyStaticFile $setglobal HourlyStaticFile 'India_8760'


$log 'Running 8760 for...'
$log ' restartfile == %restartfile%'
$log ' case == %case%'
$log ' cur_year == %cur_year%'
$log ' next_year == %next_year%'
$log ' interconnect == %interconnect%'
$log ' LDCvariabilitySwitch == %LDCvariabilitySwitch%'
$log ' DistPVSwitch == %DistPVSwitch%'
$log ' HourlyStaticFile == %HourlyStaticFile%'



* --- Call CC_py directly with ReEDS-2.0 outputs ---
$call 'gams D_8760%ds%d3_run_CC_py.gms o=E_Outputs%ds%runs%ds%%case%%ds%lstfiles%ds%run_CC_py_%cur_year%.lst r=%restartfile% --case=%case% --cur_year=%cur_year% --next_year=%next_year% logOption=4 logFile=E_Outputs%ds%runs%ds%%case%%ds%8760log.txt appendLog=1';
$if not exist E_Outputs%ds%runs%ds%%case%%ds%outputs%ds%variabilityFiles%ds%cc_out_%case%_%next_year%.gdx $abort 'error in CC_py for %case% in %cur_year%: check ErrorFile'


* --- Translate R2 outputs to be used in 8760 ----
$call 'gams D_8760%ds%d5_Curt_param.gms o=E_Outputs%ds%runs%ds%%case%%ds%lstfiles%ds%curt-params_%case%_%cur_year%.lst r=%restartfile% --case=%case% --Interconnect=%Interconnect% --cur_year=%cur_year% --LDCvariabilitySwitch=%LDCvariabilitySwitch% --DistPVSwitch=%DistPVSwitch% logOption=4 logFile=E_Outputs%ds%runs%ds%%case%%ds%8760log.txt appendLog=1';
$if errorlevel 1 $abort 'error in parameters for %case% in %cur_year%'

* --- RUN 8760 ---
$call 'gams D_8760%ds%d6_Curt_calc.gms o=E_Outputs%ds%runs%ds%%case%%ds%lstfiles%ds%curt_%case%_%cur_year%.lst u1=%Interconnect% u2=%cur_year% u3=%Do8760Switch% u4=%LDCvariabilitySwitch%  u5=%HourlyStaticFile% --case=%case% logOption=4 logFile=E_Outputs%ds%runs%ds%%case%%ds%8760log.txt appendLog=1' ;
$if errorlevel 1 $abort 'error in 8760 for %case% in %cur_year%'

* --- Translate 8760 outputs to be used in R2
$call 'Rscript %gams.curdir%%ds%D_8760%ds%d7_Translate_8760.R %gams.curdir% %gams.sysdir% %cur_year% %next_year% %case%';


