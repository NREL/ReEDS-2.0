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
$call '%copycom% %ds%%ds%nrelnas01%ds%ReEDS%ds%FY18-ReEDS-2.0%ds%data%ds%ExistingUnits_%unitdata%.gdx %basedir%%ds%inputs%ds%capacitydata%ds%'
$call '%copycom% %ds%%ds%nrelnas01%ds%ReEDS%ds%FY18-ReEDS-2.0%ds%data%ds%PrescriptiveBuilds_%unitdata%.gdx %basedir%%ds%inputs%ds%capacitydata%ds%'
$call '%copycom% %ds%%ds%nrelnas01%ds%ReEDS%ds%FY18-ReEDS-2.0%ds%data%ds%PrescriptiveRetirements_%unitdata%.gdx %basedir%%ds%inputs%ds%capacitydata%ds%'
$call '%copycom% %ds%%ds%nrelnas01%ds%ReEDS%ds%FY18-ReEDS-2.0%ds%data%ds%ReEDS_generator_database_final_%unitdata%.gdx %basedir%%ds%inputs%ds%capacitydata%ds%'
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
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%fuelcostprep.py %basedir% %coalscen% %uraniumscen% %ngscen% %rectfuelscen% %GSw_EFS1_AllYearLoad% %GSw_GasSector% %casedir%%ds%inputs_case%ds%'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%writecapdat.py %basedir% ExistingUnits_%unitdata%.gdx PrescriptiveBuilds_%unitdata%.gdx PrescriptiveRetirements_%unitdata%.gdx %retscen% %casedir%%ds%inputs_case%ds% %GSw_WaterMain% -d %GSw_DemonstrationPlants%'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%writesupplycurves.py -i %basedir% -u %unitdata% -d 0 -s %supplycurve% -o %casedir%%ds%inputs_case%ds% -g %geosupplycurve% -e %geodiscov% -n %numbins_windons% -c %numbins_windofs% -b %numbins_upv% -x %GSw_IndividualSites% -w %GSw_SitingWindOns% -f %GSw_SitingWindOfs% -p %GSw_SitingUPV% -psh %pshsupplycurve% -dr %drscen% -y %endyear%'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%writeload.py %basedir% %demandscen% %casedir%%ds%inputs_case%ds%'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%cfgather.py %basedir% %distpvscen% %casedir%%ds%inputs_case%ds% -x %GSw_IndividualSites% -w %GSw_SitingWindOns% -f %GSw_SitingWindOfs% -p %GSw_SitingUPV% -b %GSw_PVB% -v %GSw_PVB_Types%'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%writedrshift.py %basedir% %GSw_DR% %drscen% %casedir%%ds%inputs_case%ds%'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%plantcostprep.py %basedir% %convscen% %onswindscen% %ofswindscen% %upvscen% %cspscen% %batteryscen% %drscen% %pvbscen% %geoscen% %hydroscen% %beccsscen% %rectscen% %degrade_suffix% %casedir%%ds%inputs_case%ds% 2030 ons-wind_ATB_2020_moderate ofs-wind_ATB_2020_moderate'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%all_year_load.py %basedir% %GSw_EFS_Flex% %GSw_EFS1_AllYearLoad% %GSw_EFS2_FlexCase% %GSw_DR% %drscen% %casedir%%ds%inputs_case%ds% -t %ldcProfiles%'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%climateprep.py -i %basedir% -o %casedir%%ds%inputs_case%ds% -c %climatescen% -l %climateloc% -w %GSw_ClimateWater% -y %GSw_ClimateHydro% -a %yearset% -e %endyear% -d %GSw_ClimateDemand% -s %GSw_ClimateStartYear% -f %GSw_EFS1_AllYearLoad% -vv'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%LDC_prep.py -i %basedir% -o %casedir%%ds%inputs_case%ds% -l %GSw_EFS1_AllYearLoad% -x %GSw_IndividualSites% -a %GSw_IndividualSiteAgg% -d %filepath_individual_sites% -w %GSw_SitingWindOns% -f %GSw_SitingWindOfs% -p %GSw_SitingUPV% -y %osprey_years% -t %ldcProfiles% -v %GSw_PVB_Types% -b %GSw_PVB% -r %capcredit_hierarchy_level%'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%forecast.py -i %basedir% -o %casedir%%ds%inputs_case%ds% -e %endyear% -y %yearset% -p %distpvscen% -vvv'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%WriteHintage.py %basedir% %numhintage% %retscen% %mindev% %distpvscen% "%generatorfile%" %casedir%%ds%inputs_case%ds% %GSw_WaterMain%'
$log
$log
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%transmission_multilink.py -i %basedir% -o %casedir%%ds%inputs_case%ds% -t %GSw_TranScen% -l %GSw_TransMultiLink% -e %GSw_TransExtent% -w cost -v %GSw_VSC% -b %GSw_VSC_BAlist% -s %GSw_VSC_LinkList%'
$log
$log
*only need to run hourly_process if GSw_Hourly == 1
$ifthene.hourly_process %GSw_Hourly% == 1
$call.checkErrorLevel 'python %basedir%%ds%input_processing%ds%hourly_process.py -i %basedir% -o %casedir%%ds%inputs_case%ds% -f %GSw_HourlyType% -tz %GSw_HourlyTZAdj% -tz_mid_nt %GSw_HourlyTZAdj_MidNight% -a %GSw_HourlyClusterAlgorithm% -c %GSw_HourlyNumClusters% -p %GSw_HourlyIncludePeak% -ct %GSw_HourlyCenterType% -re %GSw_HourlyClusterRE% -my %GSw_HourlyClusterMultiYear% -w %GSw_HourlyWindow% -ol %GSw_HourlyOverlap% -pv %GSw_SitingUPV% -wndons %GSw_SitingWindOns% -wndofs %GSw_SitingWindOfs%'
$endif.hourly_process
$log
$log
