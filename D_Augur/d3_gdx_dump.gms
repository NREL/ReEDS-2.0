*Setting the default directory separator
$setglobal ds \

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$call 'gdxdump "%data_dir%%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=prices > "%data_dir%%ds%prices_%case%_%next_year%.csv" '
$call 'gdxdump "%data_dir%%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=flows_output > "%data_dir%%ds%flows_%case%_%next_year%.csv" '
$call 'gdxdump "%data_dir%%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=gen_output > "%data_dir%%ds%gen_%case%_%next_year%.csv" '
$call 'gdxdump "%data_dir%%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=storage_in_output > "%data_dir%%ds%storage_in_%case%_%next_year%.csv" '
$call 'gdxdump "%data_dir%%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=storage_level_output > "%data_dir%%ds%storage_level_%case%_%next_year%.csv" '
$call 'gdxdump "%data_dir%%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=dropped_load_output > "%data_dir%%ds%dropped_load_%case%_%next_year%.csv" '
$call 'gdxdump "%data_dir%%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=net_load_day > "%data_dir%%ds%net_load_day_%case%_%next_year%.csv" '
$call 'gdxdump "%data_dir%%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=cap_max_model > "%data_dir%%ds%cap_max_model_%case%_%next_year%.csv" '