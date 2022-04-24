*Setting the default directory separator
$setglobal ds \

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$call 'gdxdump "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=prices > "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%prices_%case%_%next_year%.csv" '
$call 'gdxdump "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=flows_output > "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%flows_%case%_%next_year%.csv" '
$call 'gdxdump "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=gen_output > "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%gen_%case%_%next_year%.csv" '
$call 'gdxdump "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=storage_in_output > "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%storage_in_%case%_%next_year%.csv" '
$call 'gdxdump "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=storage_level_output > "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%storage_level_%case%_%next_year%.csv" '
$call 'gdxdump "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=dropped_load_output > "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%dropped_load_%case%_%next_year%.csv" '
$call 'gdxdump "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=net_load_day > "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%net_load_day_%case%_%next_year%.csv" '
$call 'gdxdump "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%osprey_outputs_%case%_%next_year%.gdx" format=csv epsout=0 symb=cap_max_model > "reeds_server%ds%users_output%ds%%user%%ds%%runname%%ds%runs%ds%%case%%ds%augur_data%ds%cap_max_model_%case%_%next_year%.csv" '