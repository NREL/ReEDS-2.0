*==============================================
* -- Modeling to Generate Alternatives (MGA) --
*==============================================

Equation eq_MGA_CostEnvelope(t) "--$-- System cost must be within allowed envelope" ;
eq_MGA_CostEnvelope(t)$[tmodel(t)$Sw_MGA]..
    (z_rep_inv(t) + z_rep_op(t)) * (1 + Sw_MGA_CostDelta)
    =g=
    Z_inv(t) + Z_op(t)
;

* ---------------------------------------------------------------------------

$ifthen.mgaobj %GSw_MGA_Objective% == 'capacity'
Equation eq_MGA_Objective "--MW-- Defines generation capacity for MGA" ;
Variable MGA_OBJ "--MW-- Capacity of technology to be minimized/maximied" ;
eq_MGA_Objective$Sw_MGA..
    MGA_OBJ
    =e=
    sum{(i,v,r,t)
        $[tmodel(t)
        $valcap(i,v,r,t)
        $%GSw_MGA_SubObjective%(i)],
        CAP(i,v,r,t)
    }
;

* ---------------------------------------------------------------------------

$elseif.mgaobj %GSw_MGA_Objective% == 'transmission'
Equation eq_MGA_Objective "--MW-- Defines transmission capacity for MGA" ;
Variable MGA_OBJ "--MW-- Transmission capacity of all types" ;
eq_MGA_Objective$Sw_MGA..
    MGA_OBJ
    =e=
    sum{(r,rr,trtype,t)
        $[tmodel(t)
        $routes(r,rr,trtype,t)],
        CAPTRAN_ENERGY(r,rr,trtype,t)
    }
;

* ---------------------------------------------------------------------------

$elseif.mgaobj %GSw_MGA_Objective% == 'rasharing'
Equation eq_MGA_Objective "--MWh-- Defines RA flows for MGA" ;
Variable MGA_OBJ "--MWh-- Flows between NERC regions during stress periods" ;
eq_MGA_Objective$Sw_MGA..
    MGA_OBJ
    =e=
    sum{(r,rr,h,trtype,nercr,nercrr,t)
        $[tmodel(t)
        $routes(r,rr,trtype,t)
        $routes_prm(r,rr)
        $routes_nercr(nercr,nercrr,r,rr)
        $h_stress(h)],
        FLOW(r,rr,h,t,trtype) * hours(h)
    }
;

* ---------------------------------------------------------------------------

$elseif.mgaobj %GSw_MGA_Objective% == 'co2'
Equation eq_MGA_Objective "--tonne-- Defines CO2 emissions for MGA" ;
Variable MGA_OBJ "--tonne-- Direct (process) CO2 emissions" ;
eq_MGA_Objective$Sw_MGA..
    MGA_OBJ
    =e=
    sum{(r,t)
        $[tmodel(t)],
        EMIT("process","CO2",r,t)
    }
;

* ---------------------------------------------------------------------------

$endif.mgaobj
