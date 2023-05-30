# Switches
1. `GSw_HierarchyFile`: Indicate the suffix of the inputs/hierarchy.csv file you wish to use.
    1. By default the transreg boundaries are used for operating reserve sharing, capacity credit calculations, and the boundaries for limited-transmission cases.
1. `GSw_TransInvMaxLongTerm`: Limit on annual transmission deployment nationwide **IN/AFTER** `firstyear_trans_longterm`, measured in TW-miles
1. `GSw_TransInvMaxNearTerm`: Limit on annual transmission deployment nationwide **BEFORE** `firstyear_trans_longterm`, measured in TW-miles
1. `GSw_TransInvPRMderate`: By default, adding 1 MW of transmission capacity between two zones increases the energy transfer capability by 1 MW but the PRM trading capability by only 0.85 MW; here you can adjust that derate
1. `GSw_TransCostMult`: Applies to interzonal transmission capacity (including AC/DC converters) but not FOM costs
1. `GSw_TransSquiggliness`: Somewhat similar to `GSw_TransCostMult`, but scales the distance for each inter-zone interface. So turning it up to 1.3 will increase costs and losses by 1.3, and for the same amount of GW it will increase TWmiles by 1.3.
1. `GSw_TransInterconnect`: Indicate whether to allow LCC or VSC expansion across interconnects.
1. `GSw_TransHurdle`: Intra-US hurdle rate for interzonal flows, measured in $2004/MWh
1. `GSw_TransHurdleLevel`: Indicate the level of hierarchy.csv between which to apply the hurdle rate specified by `GSw_TransHurdle`. i.e. if set to ‘st’, intra-state flows will have no hurdle rates but inter-state flows will have hurdle rates specified by `GSw_TransHurdle`.
1. `GSw_TransRestrict`: Indicate the level of hierarchy.csv within which to allow transmission expansion. i.e. if set to ‘st’, no inter-state expansion is allowed.
1. `GSw_TransScen`: Indicate the inputs/transmission/transmission_capacity_future_{`GSw_TransScen`}.csv file to use, which includes the list of interfaces that can be expanded. Note that the full list of expandable interfaces is indicated by this file plus transmission_capacity_future_default.csv (currently planned additions) plus transmission_capacity_init_AC_NARIS2024.csv (existing AC interfaces, which can be expanded by default) plus transmission_capacity_init_nonAC.csv (existing DC connections, which can be expanded by default). Applies to AC, LCC, and VSC.
1. `GSw_VSC`: Indicate whether to allow VSC expansion. Will only have an effect if paired with a `GSw_TransScen` that includes VSC interfaces.
1. `GSw_PRM_hierarchy_level`: Level of hierarchy.csv within which to calculate net load, used for capacity credit. Larger levels indicate more planning coordination between regions.
1. `GSw_PRMTRADE_level`: Level of hierarchy.csv within which to allow PRM trading. By default it’s set to ‘country’, indicating no limits. If set to ‘r’, no PRM trading is allowed.
