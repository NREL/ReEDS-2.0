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
$call 'mv %casedir%%ds%inputs_case%ds%distPVCF_hourly_%distpvscen%.csv %casedir%%ds%inputs_case%ds%distPVCF_hourly.csv'
$call 'mv %casedir%%ds%inputs_case%ds%distPVCF_%distpvscen%.csv %casedir%%ds%inputs_case%ds%distPVCF.csv'

*=====================
* -- Data Creation --
*=====================

*R and python scripts for preparing data
*log command here adds some spacing between calls to make it easier to read
$log
$log
$call 'python %basedir%%ds%input_processing%ds%fuelcostprep.py %basedir% %coalscen% %uraniumscen% %ngscen% %GSw_EFS1_AllYearLoad% %GSw_GasSector% %casedir%%ds%inputs_case%ds%'
$log
$log
$call 'python %basedir%%ds%input_processing%ds%writecapdat.py %basedir% ExistingUnits_%unitdata%.gdx PrescriptiveBuilds_%unitdata%.gdx PrescriptiveRetirements_%unitdata%.gdx %retscen% %casedir%%ds%inputs_case%ds% %GSw_WaterMain%'
$log
$log
$call 'python %basedir%%ds%input_processing%ds%writesupplycurves.py -i %basedir% -u %unitdata% -d 0 -s %supplycurve% -o %casedir%%ds%inputs_case%ds% -g %geosupplycurve% -e %geodiscov%'
$log
$log
$call 'python %basedir%%ds%input_processing%ds%capacity_exog_wind.py %basedir% ExistingUnits_%unitdata%.gdx PrescriptiveRetirements_%unitdata%.gdx %casedir%%ds%inputs_case%ds% %unitdata%'
$log
$log
$call 'python %basedir%%ds%input_processing%ds%writeload.py %basedir% %demandscen% %casedir%%ds%inputs_case%ds%'
$log
$log
$call 'python %basedir%%ds%input_processing%ds%WriteHintage.py %basedir% %numhintage% %retscen% %mindev% %distpvscen% "%generatorfile%" %casedir%%ds%inputs_case%ds% %GSw_WaterMain%'
$log
$log
$call 'python %basedir%%ds%input_processing%ds%cfgather.py %basedir% %distpvscen% %casedir%%ds%inputs_case%ds%'
$log
$log
$call 'python %basedir%%ds%input_processing%ds%plantcostprep.py %basedir% %convscen% %onswindscen% %ofswindscen% %upvscen% %cspscen% %batteryscen% %geoscen% %hydroscen% %degrade_suffix% %casedir%%ds%inputs_case%ds% '
$log
$log
$call 'python %basedir%%ds%input_processing%ds%all_year_load.py %basedir% %GSw_EFS_Flex% %GSw_EFS1_AllYearLoad% %GSw_EFS2_FlexCase% %casedir%%ds%inputs_case%ds% '
