
* Activate CONVERT solver and dump gdx files
option lp = convert;
$onecho > convert.opt
gams outputs%ds%model_diagnose%ds%scalar_model_%cur_year%.gms
dumpgdx outputs%ds%model_diagnose%ds%reeds_%cur_year%.gdx
$offecho
ReEDSmodel.optfile = 1;

solve ReEDSmodel minimizing z using lp ;

* Reassign model solver and option file for the model
OPTION lp = %solver% ;
ReEDSmodel.optfile = %GSw_gopt% ;
