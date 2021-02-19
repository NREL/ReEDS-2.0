* File used to create the reference prices and quantities to construct
* the elastic demand representation. To run, call this file from the case directory as:
*
*   gams e_export_ref_pq.gms r=g00files/[my case]_2050.g00
*
* then call following lines from bash or equivalent for command prompt:
*
*   gdxdump pq_data.gdx symb=ref_q_export format=csv noHeader > ../../inputs/demand_elastic/ref_quantities.csv
*   gdxdump pq_data.gdx symb=ref_p_export format=csv noHeader > ../../inputs/demand_elastic/ref_prices.csv


parameter ref_q_export(r,h,t) "reference quantity for export"
          ref_p_export(r,h,t) "reference price for export";

*!!!! be wary of sw_ev and sw_efsflex, see notes (!!!) in c_supplymodel.gms
ref_q_export(r,h,t)$[rfeas(r)$tmodel_new(t)] = LOAD.l(r,h,t);
* correct for adjustments occurring in objective function for price unloading
ref_p_export(r,h,t)$[rfeas(r)$tmodel_new(t)] = eq_loadcon.m(r,h,t) / (cost_scale * pvf_onm(t));

*dump to gdx, dump gdx to csv, copy csv's to appropriate repo base inputs directory 
execute_unload 'pq_data.gdx' ref_q_export, ref_p_export;
