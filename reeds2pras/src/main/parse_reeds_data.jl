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
    WEATHERYEAR : Int
        variable generation profile year
    timesteps : Int
        Number of timesteps
    year : Int
        ReEDS solve year
    min_year : Int
        starting year for projections

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
    WEATHERYEAR::Int,
    timesteps::Int,
    year::Int,
    min_year::Int,
    user_inputs::Dict{Any, Any},
)
    @info "Processing regions and associating load profiles..."
    region_array = process_regions_and_load(ReEDS_data, WEATHERYEAR, timesteps)

    @info "Processing lines and adding VSC-related regions, if applicable..."
    lines = process_lines(ReEDS_data, get_name.(region_array), year, timesteps, user_inputs)
    lines, regions = process_vsc_lines(lines, region_array)

    # Create Generator Objects
    # **TODO: Should 0 MW generators be allowed after disaggregation?
    # **TODO: Should hydro be split out as a generator-storage?
    # **TODO: is it important to also handle planned outages?
    @info(
        "splitting thermal, storage, vg generator types from installed " *
        "ReEDS capacities..."
    )
    thermal, storage, variable_gens = split_generator_types(ReEDS_data, year)
    @debug "variable_gens: $(variable_gens)"

    @info "reading in ReEDS generator-type forced outage data..."
    forced_outage_data = get_forced_outage_data(ReEDS_data)
    forced_outage_dict =
        Dict(forced_outage_data[!, "ResourceType"] .=> forced_outage_data[!, "FOR"])

    @info "reading in ATB unit size data for use with disaggregation..."
    unitsize_data = get_unitsize_mapping(ReEDS_data)
    unitsize_dict = Dict(unitsize_data[!, "tech"] .=> unitsize_data[!, "atb_capacity_MW"])

    @info "Processing conventional/thermal generators..."
    thermal_gens = process_thermals_with_disaggregation(
        ReEDS_data,
        thermal,
        forced_outage_dict,
        unitsize_dict,
        timesteps,
        year,
        user_inputs,
    )
    @info "Processing variable generation..."
    gens_array = process_vg(
        thermal_gens,
        variable_gens,
        forced_outage_dict,
        ReEDS_data,
        year,
        WEATHERYEAR,
        timesteps,
        min_year,
        user_inputs,
    )

    @info "Processing Storages..."
    @debug "storage is $(storage)"
    storage_array = process_storages(
        storage,
        forced_outage_dict,
        unitsize_dict,
        ReEDS_data,
        timesteps,
        get_name.(regions),
        year,
        user_inputs,
    )

    @info "Processing GeneratorStorages [EMPTY FOR NOW].."
    genstor_array = process_genstors(get_name.(regions), timesteps)

    return lines, regions, gens_array, storage_array, genstor_array
end
