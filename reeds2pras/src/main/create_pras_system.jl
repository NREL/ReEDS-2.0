"""
    This function creates a PRAS (Probabilistic Resource Adequacy System) model
    from a set of regions, lines, generators, storages, and generator-storages.
    It takes in a vector of Region objects, a vector of Line objects, a vector
    of Generator objects, a vector of Storage objects, a vector of Gen_Storage
    objects, an integer timesteps representing the number of timesteps, and an
    integer weather_year representing the year of the simulation. It then
    creates a StepRange object for the timestamps, creates
    PRAS lines and interfaces from the sorted lines and interface indices,
    creates PRAS regions from the regions, creates PRAS generators from the
    sorted generators and generator indices, creates PRAS storages from the
    storages and storage indices, creates PRAS generator-storages from the
    sorted generator-storages and generator-storage indices, and finally
    returns a PRAS system model object.

    Parameters
    ----------
    regions : Vector{Region}
        Vector of Region objects.
    lines : Vector{Line}
        Vector of Line objects.
    gens : Vector{<:Generator}
        Vector of Generator objects.
    storages : Vector{<:Storage}
        Vector of Storage objects.
    gen_stors : Vector{<:Gen_Storage}
        Vector of Gen_Storage objects.
    timesteps : Int
        Number of timesteps.
    weather_year : Int
        Year of the simulation.

    Returns
    -------
    PRAS.SystemModel
        PRAS system model object.
"""
function create_pras_system(
    regions::Vector{Region},
    lines::Vector{Line},
    gens::Vector{<:Generator},
    storages::Vector{<:Storage},
    gen_stors::Vector{<:Gen_Storage},
    timesteps::Int,
    weather_year::Int,
)
    first_ts = TimeZones.ZonedDateTime(weather_year, 01, 01, 00, TimeZones.tz"UTC")
    last_ts = first_ts + Dates.Hour(timesteps - 1)
    my_timestamps = StepRange(first_ts, Dates.Hour(1), last_ts)

    out = get_sorted_lines(lines, regions)
    sorted_lines, interface_reg_idxs, interface_line_idxs = out
    pras_lines, pras_interfaces =
        make_pras_interfaces(sorted_lines, interface_reg_idxs, interface_line_idxs, regions)
    pras_regions = PRAS.Regions{timesteps, PRAS.MW}(
        get_name.(regions),
        reduce(vcat, get_load.(regions)),
    )
    ##
    sorted_gens, gen_idxs = get_sorted_components(gens, get_name.(regions))
    capacity_matrix = reduce(vcat, get_capacity.(sorted_gens))
    λ_matrix = reduce(vcat, get_λ.(sorted_gens))
    μ_matrix = reduce(vcat, get_μ.(sorted_gens))
    pras_gens = PRAS.Generators{timesteps, 1, PRAS.Hour, PRAS.MW}(
        get_name.(sorted_gens),
        get_type.(sorted_gens),
        capacity_matrix,
        λ_matrix,
        μ_matrix,
    )
    ##
    storages, stor_idxs = get_sorted_components(storages, regions)

    stor_names = isempty(get_name.(storages)) ? String[] : get_name.(storages)
    stor_types = isempty(get_type.(storages)) ? String[] : get_type.(storages)
    stor_charge_cap_array = reduce(
        vcat,
        get_charge_capacity.(storages),
        init = Matrix{Int64}(undef, 0, timesteps),
    )
    stor_discharge_cap_array = reduce(
        vcat,
        get_discharge_capacity.(storages),
        init = Matrix{Int64}(undef, 0, timesteps),
    )
    stor_energy_cap_array = reduce(
        vcat,
        get_energy_capacity.(storages),
        init = Matrix{Int64}(undef, 0, timesteps),
    )
    stor_chrg_eff_array = reduce(
        vcat,
        get_charge_efficiency.(storages),
        init = Matrix{Float64}(undef, 0, timesteps),
    )
    stor_dischrg_eff_array = reduce(
        vcat,
        get_discharge_efficiency.(storages),
        init = Matrix{Float64}(undef, 0, timesteps),
    )
    stor_cryovr_eff = reduce(
        vcat,
        get_carryover_efficiency.(storages),
        init = Matrix{Float64}(undef, 0, timesteps),
    )
    λ_stor = reduce(vcat, get_λ.(storages), init = Matrix{Float64}(undef, 0, timesteps))
    μ_stor = reduce(vcat, get_μ.(storages), init = Matrix{Float64}(undef, 0, timesteps))
    pras_storages = PRAS.Storages{timesteps, 1, PRAS.Hour, PRAS.MW, PRAS.MWh}(
        stor_names,
        stor_types,
        stor_charge_cap_array,
        stor_discharge_cap_array,
        stor_energy_cap_array,
        stor_chrg_eff_array,
        stor_dischrg_eff_array,
        stor_cryovr_eff,
        λ_stor,
        μ_stor,
    )
    ##
    sorted_gen_stors, genstor_idxs = get_sorted_components(gen_stors, regions)

    gen_stor_names =
        isempty(get_name.(sorted_gen_stors)) ? String[] : get_name.(sorted_gen_stors)
    gen_stor_cats =
        isempty(get_type.(sorted_gen_stors)) ? String[] : get_type.(sorted_gen_stors)
    gen_stor_cap_array = reduce(
        vcat,
        get_charge_capacity.(sorted_gen_stors),
        init = Matrix{Int64}(undef, 0, timesteps),
    )
    gen_stor_dis_cap_array = reduce(
        vcat,
        get_discharge_capacity.(sorted_gen_stors),
        init = Matrix{Int64}(undef, 0, timesteps),
    )
    gen_stor_enrgy_cap_array = reduce(
        vcat,
        get_energy_capacity.(sorted_gen_stors),
        init = Matrix{Int64}(undef, 0, timesteps),
    )
    gen_stor_chrg_eff_array = reduce(
        vcat,
        get_charge_efficiency.(sorted_gen_stors),
        init = Matrix{Float64}(undef, 0, timesteps),
    )
    gen_stor_dischrg_eff_array = reduce(
        vcat,
        get_discharge_efficiency.(sorted_gen_stors),
        init = Matrix{Float64}(undef, 0, timesteps),
    )
    gen_stor_carryovr_eff_array = reduce(
        vcat,
        get_carryover_efficiency.(sorted_gen_stors),
        init = Matrix{Float64}(undef, 0, timesteps),
    )
    gen_stor_inflow_array = reduce(
        vcat,
        get_inflow.(sorted_gen_stors),
        init = Matrix{Int64}(undef, 0, timesteps),
    )
    gen_stor_grid_withdrawl_array = reduce(
        vcat,
        get_grid_withdrawl_capacity.(sorted_gen_stors),
        init = Matrix{Int64}(undef, 0, timesteps),
    )
    gen_stor_grid_inj_array = reduce(
        vcat,
        get_grid_injection_capacity.(sorted_gen_stors),
        init = Matrix{Int64}(undef, 0, timesteps),
    )
    gen_stor_λ =
        reduce(vcat, get_λ.(sorted_gen_stors), init = Matrix{Float64}(undef, 0, timesteps))
    gen_stor_μ =
        reduce(vcat, get_μ.(sorted_gen_stors), init = Matrix{Float64}(undef, 0, timesteps))

    gen_stors = PRAS.GeneratorStorages{timesteps, 1, PRAS.Hour, PRAS.MW, PRAS.MWh}(
        gen_stor_names,
        gen_stor_cats,
        gen_stor_cap_array,
        gen_stor_dis_cap_array,
        gen_stor_enrgy_cap_array,
        gen_stor_chrg_eff_array,
        gen_stor_dischrg_eff_array,
        gen_stor_carryovr_eff_array,
        gen_stor_inflow_array,
        gen_stor_grid_withdrawl_array,
        gen_stor_grid_inj_array,
        gen_stor_λ,
        gen_stor_μ,
    )

    return PRAS.SystemModel(
        pras_regions,
        pras_interfaces,
        pras_gens,
        gen_idxs,
        pras_storages,
        stor_idxs,
        gen_stors,
        genstor_idxs,
        pras_lines,
        interface_line_idxs,
        my_timestamps,
    )
end
