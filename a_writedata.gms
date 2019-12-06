*Setting the default slash
$setglobal ds \
$setglobal copycom copy 

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$setglobal copycom cp
$endif.unix

*Set the end of line comment to %ds%
$eolcom \\

$if not set supplycurvefile $setglobal supplycurvefile 2019
$if not set hintage_calcmethod $setglobal hintage_calcmethod 0
$if not set generatorfile $setglobal generatorfile 'ReEDS_generator_database_final_%unitdata%.csv'

*If using ABB database, %copycom% those files to the inputs/capacitydata folder
*This option is only available if one is on the NREL network
$ifthen %unitdata% == 'ABB'
$call '%copycom% %ds%%ds%nrelqnap02%ds%ReEDS%ds%FY18-ReEDS-2.0%ds%data%ds%ExistingUnits_%unitdata%.gdx %basedir%%ds%inputs%ds%capacitydata%ds%'
$call '%copycom% %ds%%ds%nrelqnap02%ds%ReEDS%ds%FY18-ReEDS-2.0%ds%data%ds%PrescriptiveBuilds_%unitdata%.gdx %basedir%%ds%inputs%ds%capacitydata%ds%'
$call '%copycom% %ds%%ds%nrelqnap02%ds%ReEDS%ds%FY18-ReEDS-2.0%ds%data%ds%PrescriptiveRetirements_%unitdata%.gdx %basedir%%ds%inputs%ds%capacitydata%ds%'
$call '%copycom% %ds%%ds%nrelqnap02%ds%ReEDS%ds%FY18-ReEDS-2.0%ds%data%ds%ReEDS_generator_database_final_%unitdata%.gdx %basedir%%ds%inputs%ds%capacitydata%ds%'
$endif

*Copying the necessary dGen distPV inputs to the inputs_case folder
$call '%copycom% %basedir%%ds%inputs%ds%dGen_Model_Inputs%ds%%distpvscen%%ds%distPVCF_%distpvscen%.csv %casedir%%ds%inputs_case%ds%'
$call '%copycom% %basedir%%ds%inputs%ds%dGen_Model_Inputs%ds%%distpvscen%%ds%distPVcap_%distpvscen%.csv %casedir%%ds%inputs_case%ds%'
$call '%copycom% %basedir%%ds%inputs%ds%dGen_Model_Inputs%ds%%distpvscen%%ds%distPVCF_hourly_%distpvscen%.csv %casedir%%ds%inputs_case%ds%'
*Removing the distPV scenario name from the hourly distPV CF filename for the ReEDS-to-PLEXOS translation process
$call '%copycom% %casedir%%ds%inputs_case%ds%distPVCF_hourly_%distpvscen%.csv %casedir%%ds%inputs_case%ds%distPVCF_hourly.csv'


*=====================
* -- Data Creation --
*=====================

*R and python scripts for preparing data
*log command here adds some spacing between calls to make it easier to read
$log
$log
$call 'Rscript %basedir%%ds%input_processing%ds%R%ds%fuelcostprep.R %basedir% %coalscen% %uraniumscen% %ngscen% %casedir%%ds%inputs_case%ds%'
$log
$log
$call 'Rscript %basedir%%ds%input_processing%ds%R%ds%writecapdat.R %basedir% "%gams.sysdir%" ExistingUnits_%unitdata%.gdx PrescriptiveBuilds_%unitdata%.gdx PrescriptiveRetirements_%unitdata%.gdx %retscen% %casedir%%ds%inputs_case%ds%  '
$log
$log
$call 'Rscript %basedir%%ds%input_processing%ds%R%ds%writesupplycurves.R %basedir% "%gams.sysdir%" ExistingUnits_%unitdata%.gdx 0 %supplycurvefile% %casedir%%ds%inputs_case%ds% %geosupplycurve%'
$log
$log
$call 'python %basedir%%ds%inputs%ds%capacitydata%ds%capacity_exog_wind.py %basedir% %supplycurvefile% ExistingUnits_%unitdata%.gdx PrescriptiveRetirements_%unitdata%.gdx %casedir%%ds%inputs_case%ds% %unitdata%'
$log
$log
$call 'Rscript %basedir%%ds%input_processing%ds%R%ds%writeload.R %basedir% %demandscen% %casedir%%ds%inputs_case%ds%'
$log
$log
$call 'Rscript %basedir%%ds%input_processing%ds%R%ds%WriteHintage.R %basedir% %numhintage% %retscen% %mindev% %hintage_calcmethod% %distpvscen% "%generatorfile%" %casedir%%ds%inputs_case%ds%'
$log
$log
$call 'Rscript %basedir%%ds%input_processing%ds%R%ds%cfgather.R %basedir% "%gams.sysdir%" %distpvscen% %casedir%%ds%inputs_case%ds%  '
$log
$log
$call 'Rscript %basedir%%ds%input_processing%ds%R%ds%plantcostprep.R %basedir% %convscen% %windscen% %upvscen% %cspscen% %batteryscen% %geoscen% %hydroscen% %casedir%%ds%inputs_case%ds%'
$log
$log
