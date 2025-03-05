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
    user_descriptors::Union{Nothing, String} = nothing,
)
    if (user_descriptors === nothing)
        user_descriptors =
            joinpath(@__DIR__, "utils", "Descriptors", "user_descriptors.json")
    end
    user_inputs = parse_user_descriptors(user_descriptors)
    # assume valid weather years as hardcode for now. These should eventually
    # be read in from ReEDS
    if weather_year ∉ user_inputs["weather_years"]
        error(
            "The weather year $weather_year is not a valid year for available VG & Load data " *
            "year. Currrently, it should be an Int in [2007-2013] or [2016-2023].",
        )
    end

    ReEDS_data = ReEDSdatapaths(reedscase, solve_year)

    @info "Running checks on input data..."
    run_checks(ReEDS_data)

    @info "Parsing ReEDS data and creating ReEDS2PRAS objects..."
    out = parse_reeds_data(
        ReEDS_data,
        weather_year,
        timesteps,
        solve_year,
        user_inputs,
        hydro_energylim = hydro_energylim,
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
