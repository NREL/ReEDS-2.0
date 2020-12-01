*Setting the default directory separator
$setglobal ds \

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=prices > "ReEDS_Augur%ds%augur_data%ds%prices_%case%_%next_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=flows_output > "ReEDS_Augur%ds%augur_data%ds%flows_%case%_%next_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=gen_output > "ReEDS_Augur%ds%augur_data%ds%gen_%case%_%next_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=storage_in_output > "ReEDS_Augur%ds%augur_data%ds%storage_in_%case%_%next_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=storage_level_output > "ReEDS_Augur%ds%augur_data%ds%storage_level_%case%_%next_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=dropped_load_output > "ReEDS_Augur%ds%augur_data%ds%dropped_load_%case%_%next_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=net_load_day > "ReEDS_Augur%ds%augur_data%ds%net_load_day_%case%_%next_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=cap_max_model > "ReEDS_Augur%ds%augur_data%ds%cap_max_model_%case%_%next_year%.csv" '
