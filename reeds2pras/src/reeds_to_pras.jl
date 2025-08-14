#runs ReEDS2PRAS
"""
    Generates a PRAS system from data in ReEDSfilepath

    Parameters
    ----------
    ReEDSfilepath : String
        Location of ReEDS filepath where inputs, results, and outputs are
        stored
    year : Int64
        ReEDS solve year
    timesteps : Int
        Number of timesteps
    weather_year : Int
        The weather year for variable gen profiles and load
    hydro_energylim : Bool
        If this is false we process hydro with fixed capacity based one
        name plate from the max_cap file. If true, we process non-dispatchable
        hydro as a VRE with varying capacity and dispatchable hydro as
        a generator storage with monthly inflows

    Returns
    -------
    PRAS.SystemModel
        PRAS SystemModel struct with regions, interfaces, generators,
        region_gen_idxs, storages, region_stor_idxs, generatorstorages,
        region_genstor_idxs, lines, interface_line_idxs, timestamps

"""
function reeds_to_pras(
    reedscase::String,
    solve_year::Int64,
    timesteps::Int,
    weather_year::Int,
    hydro_energylim::Bool = false,
    pras_agg_ogs_lfillgas::Bool = false,
    pras_existing_unit_size::Bool = true,
)
    ReEDS_data = ReEDSdatapaths(reedscase, solve_year)

    @info "Running checks on input data..."
    run_checks(ReEDS_data)

    @info "Parsing ReEDS data and creating ReEDS2PRAS objects..."
    out = parse_reeds_data(
        ReEDS_data,
        timesteps,
        solve_year,
        hydro_energylim = hydro_energylim,
        pras_agg_ogs_lfillgas = pras_agg_ogs_lfillgas,
        pras_existing_unit_size = pras_existing_unit_size,
    )
    lines, regions, gens, storages, genstors = out
    
    @info "ReEDS data successfully parsed, creating a PRAS system"
    return create_pras_system(
        regions,
        lines,
        gens,
        storages,
        genstors,
        timesteps,
        weather_year,
    )
end
