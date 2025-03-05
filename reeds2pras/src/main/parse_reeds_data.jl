"""
    This function creates PRAS objects based on data from the ReEDS
    capacity expansion model. It processes regional load profiles,
    interregional transmission lines, thermal generators,
    storages, and GeneratorStorages into arrays suitable for creating
    a PRAS system.

    Parameters
    ----------
    ReEDS_data : ReEDSdatapaths
        data paths with specific ReEDS file paths
    weather_year : Int
        variable generation profile year
    timesteps : Int
        Number of timesteps
    solve_year : Int
        ReEDS solve year

    Returns
    -------
    lines : Array{Line}
        contains Line objects
    regions : Array{Region}
        contains Region objects
    gens_array : Array{VegGen}
        contains VG Gen objects
    storage_array : Array{Storage}
        contains Storage objects
    genstor_array : Array{GeneratorStorage}
        contains GeneratorStorage objects
"""
function parse_reeds_data(
    ReEDS_data::ReEDSdatapaths,
    weather_year::Int,
    timesteps::Int,
    solve_year::Int,
    user_inputs::Dict{Any, Any};
    hydro_energylim = false,
)
    @info "Processing regions and associating load profiles..."
    region_array = process_regions_and_load(ReEDS_data, weather_year, timesteps)

    @info "Processing lines and adding VSC-related regions, if applicable..."
    lines = process_lines(ReEDS_data, get_name.(region_array), timesteps, user_inputs)
    lines, regions = process_vsc_lines(lines, region_array)

    # Create Generator Objects
    # **TODO: Should 0 MW generators be allowed after disaggregation?
    # **TODO: is it important to also handle planned outages?
    @info(
        "splitting thermal, storage, variable and hydro generator types from installed " *
        "ReEDS capacities..."
    )
    thermal_builds, storage, variable_gens, hydro_disp_gens, hydro_non_disp_gens =
        split_generator_types(ReEDS_data, solve_year)
    @debug "variable_gens: $(variable_gens)"

    @info "reading in ReEDS generator-type forced outage data..."
    forced_outage_data = get_forced_outage_data(ReEDS_data)
    FOR_dict = Dict(forced_outage_data[!, "ResourceType"] .=> forced_outage_data[!, "FOR"])

    @info "reading hourly forced outage rates"
    filepath = joinpath(ReEDS_data.ReEDSfilepath, "inputs_case", "forcedoutage_hourly.h5")
    # forcedoutage_hourly = HDF5.h5read(infile, "data")
    forcedoutage_hourly_index = HDF5.h5read(filepath, "index")
    first_ts = filter(x -> contains(x, "$weather_year"), forcedoutage_hourly_index)[1]
    start_idx = findfirst(isequal(first_ts), forcedoutage_hourly_index)
    end_idx = start_idx + timesteps - 1
    forcedoutage_hourly = DataFrames.DataFrame(
        HDF5.h5read(filepath, "data")',
        HDF5.h5read(filepath, "columns"),
    )
    forcedoutage_hourly = forcedoutage_hourly[start_idx:end_idx, :]

    @info "reading in ATB unit size data for use with disaggregation..."
    unitsize_data = get_unitsize_mapping(ReEDS_data)
    unitsize_dict = Dict(unitsize_data[!, "tech"] .=> unitsize_data[!, "atb_capacity_MW"])

    @info "Processing conventional/thermal generators..."
    thermal_gens = process_thermals_with_disaggregation(
        ReEDS_data,
        thermal_builds,
        FOR_dict,
        forcedoutage_hourly,
        unitsize_dict,
        timesteps,
        solve_year,
        user_inputs,
    )
    @info "Processing variable generation..."
    gens_array = process_vg(
        thermal_gens,
        variable_gens,
        FOR_dict,
        ReEDS_data,
        timesteps,
        user_inputs,
    )

    @info "Processing Storages..."
    @debug "storage is $(storage)"
    storage_array = process_storages(
        storage,
        FOR_dict,
        unitsize_dict,
        ReEDS_data,
        timesteps,
        solve_year,
        user_inputs,
    )

    @info "Processing hydroelectric generators..."
    gens_array, genstor_array = process_hydro(
        gens_array,
        hydro_disp_gens,
        hydro_non_disp_gens,
        FOR_dict,
        forcedoutage_hourly,
        ReEDS_data,
        solve_year,
        timesteps,
        user_inputs,
        unitsize_dict,
        hydro_energylim = hydro_energylim,
    )

    #@info "Processing GeneratorStorages"
    #genstor_array = process_genstors(genstor_array, get_name.(regions), timesteps)

    return lines, regions, gens_array, storage_array, genstor_array
end
