"""
    Processes ReEDS data and loads the specified weather year and number of
    time steps.

    Parameters
    ----------
    ReEDS_data : ReEDSData
        ReEDSData object containing the load data.
    weather_year : Int
        The weather year to be loaded.
    timesteps : Int
        The number of time steps to be loaded.

    Returns
    -------
    List
        A list of Region objects containing the load data for the specified
        weather year and number of time steps.
"""
function process_regions_and_load(ReEDS_data, weather_year::Int, timesteps::Int)
    load_info = get_load_file(ReEDS_data)
    load_data = load_info["block0_values"]
    regions = load_info["block0_items"]
    # **TODO: can get a bug/error here if ReEDS case lacks multiple load years
    # slices based on input weather year
    slicer = findfirst(isequal(weather_year), load_info["axis1_level1"])

    # Julia indexes from 1 we need -1 here
    indices = findall(i -> (i == (slicer - 1)), load_info["axis1_label1"])
    slice_reqd = first(indices):(first(indices) + timesteps - 1)

    load_timesteps = load_data[:, slice_reqd]

    return [
        Region(r, timesteps, floor.(Int, load_timesteps[idx, :])) for
        (idx, r) in enumerate(regions)
    ]
end

"""
    This function takes in ReEDS data, a vector of regions, a year, and a
    number of time steps, and returns an array of Line objects. It first gets
    the line capacity data from the ReEDS data, then gets the converter
    capacity data from the ReEDS data. It then adds 0 converter capacity for
    regions that lack a converter. It then creates a system line naming
    dataframe, which is a subset of the line capacity dataframe, and combines
    the MW column by summing it. It then creates a Line object for each row in
    the system line naming dataframe, and adds it to the lines_array. If the
    line is a VSC line, it adds the converter capacity data to the Line object.

    Parameters
    ----------
    ReEDS_data : DataFrame
        DataFrame containing ReEDS line capacity data.
    regions : Vector{<:AbstractString}
        Vector of region names.
    timesteps : Int
        Number of timesteps.

    Returns
    -------
    lines_array : Vector{Line}
        Vector of Line objects.
"""
function process_lines(
    ReEDS_data,
    regions::Vector{<:AbstractString},
    timesteps::Int,
    user_inputs::Dict{Any, Any},
)
    #it is assumed this has prm line capacity data
    line_base_cap_data = get_line_capacity_data(ReEDS_data)

    converter_capacity_data = get_converter_capacity_data(ReEDS_data)
    converter_capacity_dict = Dict(
        convert.(String, converter_capacity_data[!, "r"]) .=>
            converter_capacity_data[!, "MW"],
    )

    #add 0 converter capacity for regions that lack a converter
    if length(keys(converter_capacity_dict)) > 0
        for reg in regions
            if !(reg in keys(converter_capacity_dict))
                @info("$reg does not have VSC converter capacity, so adding" * " a 0")
                converter_capacity_dict[reg] = 0.0
            end
        end
    end

    function keep_line(from_pca, to_pca)
        from_idx = findfirst(x -> x == from_pca, regions)
        to_idx = findfirst(x -> x == to_pca, regions)
        return ~isnothing(from_idx) && ~isnothing(to_idx) && (from_idx < to_idx)
    end
    system_line_naming_data =
        DataFrames.subset(line_base_cap_data, [:r, :rr] => DataFrames.ByRow(keep_line))
    # split-apply-combine b/c some lines have same name convention
    system_line_naming_data = DataFrames.combine(
        DataFrames.groupby(system_line_naming_data, ["r", "rr", "trtype"]),
        :MW => sum,
    )

    lines_array = Line[]
    for row in eachrow(system_line_naming_data)
        forward_cap = sum(
            line_base_cap_data[
                (line_base_cap_data.r .== row.r) .& (line_base_cap_data.rr .== row.rr) .& (line_base_cap_data.trtype .== row.trtype),
                "MW",
            ],
        )
        backward_cap = sum(
            line_base_cap_data[
                (line_base_cap_data.r .== row.rr) .& (line_base_cap_data.rr .== row.r) .& (line_base_cap_data.trtype .== row.trtype),
                "MW",
            ],
        )

        name = "$(row.r)|$(row.rr)|$(row.trtype)"
        @debug(
            "a line $name, with $forward_cap MW forward and $backward_cap" *
            " backward in $(row.trtype)"
        )
        if row.trtype != "VSC"
            push!(
                lines_array,
                Line(
                    name = name,
                    timesteps = timesteps,
                    category = row.trtype,
                    region_from = row.r,
                    region_to = row.rr,
                    forward_cap = forward_cap,
                    backward_cap = backward_cap,
                    legacy = "Existing",
                    FOR = 0.0,
                    MTTR = user_inputs["MTTR"],
                ),
            )
        else
            push!(
                lines_array,
                Line(
                    name = name,
                    timesteps = timesteps,
                    category = row.trtype,
                    region_from = row.r,
                    region_to = row.rr,
                    forward_cap = forward_cap,
                    backward_cap = backward_cap,
                    legacy = "Existing",
                    FOR = 0.0,
                    MTTR = user_inputs["MTTR"],
                    VSC = true,
                    converter_capacity = Dict(
                        row.r => converter_capacity_dict[string(row.r)],
                        row.rr => converter_capacity_dict[string(row.rr)],
                    ),
                ),
            )
        end
    end
    return lines_array
end

"""
    Split generator types into thermal, storage, and variable generation
    resources

    Parameters
    ----------
    ReEDS_data : dict
        Raw ReEDS data as a dict
    year : Int
        Year of interest

    Returns
    -------
    DataFrames
        Thermal capacity, Storage capacity, Variable Generation capacity
"""
function split_generator_types(ReEDS_data::ReEDSdatapaths, year::Int64)
    ## Read {case}/inputs_case/tech-subset-table.csv
    tech_subset_table = get_technology_types(ReEDS_data)
    @debug "tech_subset_table is $(tech_subset_table)"
    ## Read {case}/ReEDS_Augur/augur_data/max_cap_{year}.csv
    capacity_data = get_ICAP_data(ReEDS_data)
    ## Read {case}/inputs_case/resources.csv
    resources = get_valid_resources(ReEDS_data)
    @debug "resources is $(resources)"
    vg_types = unique(resources.i)
    @debug "vg_types is $(vg_types)"

    hyd_disp_types =
        lowercase.(DataFrames.dropmissing(tech_subset_table, :HYDRO_D)[:, "Column1"])
    hyd_non_disp_types =
        lowercase.(DataFrames.dropmissing(tech_subset_table, :HYDRO_ND)[:, "Column1"])

    @debug "hd_types is $(union(hyd_disp_types,hyd_non_disp_types))"

    storage_types =
        unique(DataFrames.dropmissing(tech_subset_table, :STORAGE_STANDALONE)[:, "Column1"])

    @debug "storage type is $(storage_types)"

    # clean vg/storage capacity on a regex, though there might be a better way...
    clean_names!(vg_types)
    @debug "vg_types is $(vg_types)"
    clean_names!(storage_types)

    vg_capacity = filter(x -> x.i in vg_types, capacity_data)
    storage_capacity = filter(x -> x.i in storage_types, capacity_data)

    hyd_disp_capacity = filter(x -> x.i in hyd_disp_types, capacity_data)
    hyd_non_disp_capacity = filter(x -> x.i in hyd_non_disp_types, capacity_data)

    thermal_capacity = filter(
        x -> ~(x.i in union(vg_types, storage_types, hyd_disp_types, hyd_non_disp_types)),
        capacity_data,
    )

    @debug "thermal_capacity is $(thermal_capacity)"
    return thermal_capacity,
    storage_capacity,
    vg_capacity,
    hyd_disp_capacity,
    hyd_non_disp_capacity
end

"""
    Process existing thermal capacities with disaggregation.

    Parameters
    ----------
    ReEDS_data : object
        The ReEDS data object
    thermal_builds : DataFrames.DataFrame
        Data frame containing the thermal build information
    FOR_dict : dict
        Dictionary of Forced Outage Rates (FORs) for each resource
    timesteps : int
        Number of slices to disaggregate the capacity
    year : int
        Year associated with the capacity

    Returns
    -------
    all_generators : Generator[]
        Array of Generator objects containing the disaggregated capacity for
        each resource
"""
function process_thermals_with_disaggregation(
    ReEDS_data,
    thermal_builds::DataFrames.DataFrame,
    FOR_dict::Dict,
    forcedoutage_hourly::DataFrames.DataFrame,
    unitsize_dict::Dict,
    timesteps::Int,
    year::Int,
    user_inputs::Dict{Any, Any};
    all_generators = Generator[],
)
    # csp-ns is not a thermal; just drop in for now
    thermal_builds = thermal_builds[(thermal_builds.i .!= "csp-ns"), :]
    # split-apply-combine to handle differently vintaged entries
    thermal_builds =
        DataFrames.combine(DataFrames.groupby(thermal_builds, ["i", "r"]), :MW => sum)
    EIA_db = get_EIA_NEMS_DB(ReEDS_data)

    filepath = joinpath(ReEDS_data.ReEDSfilepath, "inputs_case", "upgrade_link.csv")
    upgrades = DataFrames.DataFrame(CSV.File(filepath))
    upgrade_dict = Dict(lowercase(row["*TO"]) => lowercase(row["FROM"]) for row in eachrow(upgrades))
    filler_forced_outage_rate = 0.0

    # this loop gets the FOR for each build/tech
    for row in eachrow(thermal_builds)
        # Check to see if the 'i' tech is an upgrade tech. If so, use the 'upgraded-to' 
        # tech to determine FOR
        if haskey(upgrade_dict, row.i)
            tech = upgrade_dict[row.i]   
            @info(
                "$(row.i) ($(row.r)) is an upgrade tech so using $tech to determine outage rate"
            )
        else
            tech = row.i
        end

        i_r = "$tech|$(row.r)"
        if (i_r in DataFrames.names(forcedoutage_hourly))
            gen_for = forcedoutage_hourly[!, i_r]
        elseif lowercase(tech) in keys(FOR_dict)
            gen_for = fill(Float32(FOR_dict[lowercase(tech)]), timesteps)
            @info(
                "$tech ($(row.r)) was not found in forcedoutage_hourly so using " *
                "static value of $(FOR_dict[tech]) from outage_forced_static.csv"
            )
        else
            gen_for = fill(Float32(filler_forced_outage_rate), timesteps)
            @info(
                "$(tech) ($(row.r)) was not found in outage_forced_static.csv so using " *
                "static value of $filler_forced_outage_rate"
            )
        end

        generator_array = disagg_existing_capacity(
            ReEDS_data,
            EIA_db,
            unitsize_dict,
            floor(Int, row.MW_sum),
            String(row.i),
            String(row.r),
            gen_for,
            timesteps,
            year,
            user_inputs,
        )
        append!(all_generators, generator_array)
    end
    return all_generators
end

"""
    We use this function if we want to process hydroelectric generators as fixed capacities.
    It is a replication of the process thermal functions to retain the older way of
    handling hydro plants, where we do not use hydro capacity factors, and distinguish
    dispatchable and non dispatchable hydroelectric generators.

    Parameters
    ----------
    all_generators : Generator[]
        Array of Generator objects containing the capacity for
        each resource, and it is modified in place.
    ReEDS_data : object
        The ReEDS data object
    hd_builds : DataFrames.DataFrame
        Data frame containing the hydro plant information
    FOR_dict : dict
        Dictionary of Forced Outage Rates (FORs) for each resource
    timesteps : int
        Number of slices to disaggregate the capacity
    year : int
        Year associated with the capacity

    Returns
    -------
"""
function process_hd_as_generator!(
    all_generators,
    ReEDS_data,
    hd_builds::DataFrames.DataFrame,
    FOR_dict::Dict,
    forcedoutage_hourly::DataFrames.DataFrame,
    unitsize_dict::Dict,
    timesteps::Int,
    year::Int,
    user_inputs::Dict{Any, Any};
)

    # split-apply-combine to handle differently vintaged entries
    hd_builds = DataFrames.combine(DataFrames.groupby(hd_builds, ["i", "r"]), :MW => sum)
    EIA_db = get_EIA_NEMS_DB(ReEDS_data)

    filepath = joinpath(ReEDS_data.ReEDSfilepath, "inputs_case", "upgrade_link.csv")
    upgrades = DataFrames.DataFrame(CSV.File(filepath))
    upgrade_dict = Dict(lowercase(row["*TO"]) => lowercase(row["DELTA"]) for row in eachrow(upgrades))
    filler_forced_outage_rate = 0.0

    # this loop gets the FOR for each build/tech
    for row in eachrow(hd_builds)
        # Check to see if the 'i' tech is an upgrade tech. If so, use the 'upgraded-to' 
        # tech to determine FOR
        if haskey(upgrade_dict, row.i)
            tech = upgrade_dict[row.i]   
            @info(
                "$(row.i) ($(row.r)) is an upgrade tech so using $tech to determine outage rate"
            )
        else
            tech = row.i
        end

        i_r = "$tech|$(row.r)"
        if (i_r in DataFrames.names(forcedoutage_hourly))
            gen_for = forcedoutage_hourly[!, i_r]
        elseif lowercase(tech) in keys(FOR_dict)
            gen_for = fill(Float32(FOR_dict[lowercase(tech)]), timesteps)
            @info(
                "$tech ($(row.r)) was not found in forcedoutage_hourly so using " *
                "static value of $(FOR_dict[tech]) from outage_forced_static.csv"
            )
        else
            gen_for = fill(Float32(filler_forced_outage_rate), timesteps)
            @info(
                "$(tech) ($(row.r)) was not found in outage_forced_static.csv so using " *
                "static value of $filler_forced_outage_rate"
            )
        end

        generator_array = disagg_existing_capacity(
            ReEDS_data,
            EIA_db,
            unitsize_dict,
            floor(Int, row.MW_sum),
            String(row.i),
            String(row.r),
            gen_for,
            timesteps,
            year,
            user_inputs,
        )
        append!(all_generators, generator_array)
    end
end

"""
    This function is used to process variable generation (VG) builds, taking
    into account different vintages.

    Parameters
    ----------
    generators_array : Vector{<:ReEDS2PRAS.Generator}
        Vector of ReEDS Generators
    vg_builds : DataFrames.DataFrame
        A dataframe containing VG builds
    FOR_dict : Dict
        A dictionary of Forced Outage Rate (FOR) for each technology type
    ReEDS_data : DataFrames.DataFrame
        A dataset from the ReEDS Program
    year : Int
        The current year
    weather_year : Int
        The weather year (when the heat rate variation data was collected)
    timesteps : Int
        Number of time steps
    min_year : Int
        The start year of the data set

    Returns
    -------
    generators_array : Vector{<:ReEDS2PRAS.Generator}
        An array of the VG generators
"""
function process_vg(
    generators_array::Vector{<:ReEDS2PRAS.Generator},
    vg_builds::DataFrames.DataFrame,
    FOR_dict::Dict,
    ReEDS_data,
    timesteps::Int,
    user_inputs::Dict{Any, Any},
)
    cf_info = get_vg_cf_data(ReEDS_data)
    vg_profiles = cf_info["block0_values"]

    # split-apply-combine to handle differently vintaged entries
    vg_builds = DataFrames.combine(DataFrames.groupby(vg_builds, ["i", "r"]), :MW => sum)
    for row in eachrow(vg_builds)
        category = string(row.i)
        name = "$(category)|$(string(row.r))"
        region = string(row.r)

        profile_index = findfirst.(isequal.(name), (cf_info["axis0"],))[1]
        profile = vg_profiles[profile_index, 1:timesteps]

        if category in keys(FOR_dict)
            gen_for = FOR_dict[category]
        else
            gen_for = 0.00 # make this 0 for vg if no match
        end
        name = "$(name)_"

        push!(
            generators_array,
            Variable_Gen(
                name = name,
                timesteps = timesteps,
                region_name = region,
                installed_capacity = maximum(profile),
                capacity = profile,
                type = category,
                legacy = "New",
                FOR = gen_for,
                MTTR = user_inputs["MTTR"],
            ),
        )
    end
    return generators_array
end

"""
    Parameters
    ----------
    generators_array : Vector{<:Generator}
        a vector of strings of distinct regions in the model
    hydro_disp_capacities : DataFrame
        a dataframe containing details of dispatchable (reservoir)
        HD generators
    hydro_non_disp_capacities : DataFrame
        a dataframe containing details of non-dispatchable 
        (run-of-river) HD generators
    FOR_dict : Dict
        a dictionary of forced outage rates, not applied to HD 
        devices for now
    ReEDS_data
        input data from ReEDS
    timesteps : Int
        number of timesteps
    year : Int64
        ReEDS target simulation year
    user_inputs : Dict{Any, Any}
        a dictionary with user inputs
    hydro_energylim : Bool
        a flag which allows users to choose whether to model HD 
        devices as flat generators, or as variable generator for 
        run-of-river plants and generatorstorage for reservoir 
        plants
    unitsize_dict = nothing,
    Returns
    -------
    generators_array : Vector{<:Generator}
        Generators array updated with hydro generators, either all 
        generators as static capacity, or run-of-river generators
        as variable generators
    gen_stors : Gen_Storage
        Generator_storages array returned as empty if we don't 
        process energy limits, or returned with reservoir hydro
        plants (dispatchable type)
"""
function process_hydro(
    generators_array::Vector{<:Generator},
    hydro_disp_capacities::DataFrames.DataFrame,
    hydro_non_disp_capacities::DataFrames.DataFrame,
    FOR_dict::Dict,
    forcedoutage_hourly,
    ReEDS_data,
    year::Int64,
    timesteps::Int,
    user_inputs::Dict{Any, Any},
    unitsize_dict;
    hydro_energylim = false,
)

    # If we do not impose energy limits on hydro and model it as fixed capacity
    if !(hydro_energylim)
        @info "Processing HD generators as generator with fixed capacities..."

        process_hd_as_generator!(
            generators_array,
            ReEDS_data,
            hydro_disp_capacities,
            FOR_dict,
            forcedoutage_hourly,
            unitsize_dict,
            timesteps,
            year,
            user_inputs;
        )

        process_hd_as_generator!(
            generators_array,
            ReEDS_data,
            hydro_non_disp_capacities,
            FOR_dict,
            forcedoutage_hourly,
            unitsize_dict,
            timesteps,
            year,
            user_inputs;
        )
        genstor_array = Gen_Storage[]

        return generators_array, genstor_array
    end

    hydcf, hydcapadj = get_hydro_data(ReEDS_data)
    monthhours = monhours()

    timesteps_year = 8760
    num_years = Int(timesteps // timesteps_year)

    # Combine all plant vintages for each region and plant type for dispatchable plants
    disp_combined_caps =
        DataFrames.combine(DataFrames.groupby(hydro_disp_capacities, [:i, :r]), :MW => sum)

    genstor_array = Gen_Storage[]

    # We need the dispatch limit for each hour from each asset and each month's energy budget
    # applied as an exogenous limit using inflow. We have monthly capacity factors for energy budget
    # and monthly capacity adjustment factor on the nameplate capacity for dispatch limits. 
    # For each month, (i) energy budget is calculated based on number of hours in the month
    # and (ii) dispatch limit is calculated based on the month.
    for (idx, row) in enumerate(DataFrames.eachrow(disp_combined_caps))
        reg_plant_subset =
            filter(x -> (x.r == row.r && x.i == row.i), hydcf)[:, [:month, :value]]
        monthly_energy = zeros(timesteps_year)
        dispatch_limit = zeros(timesteps_year)
        energy_cap = zeros(timesteps_year)
        for monhr in monthhours
            try
                reqd_slice = monhr.slice
                monthly_energy[first(reqd_slice)] =
                    (monhr.numhrs * filter(x -> (x.month == monhr.month), reg_plant_subset)[
                        :,
                        :value,
                    ] * row.MW_sum)[1]

                energy_cap[reqd_slice] .=
                    (monhr.numhrs * filter(x -> (x.month == monhr.month), reg_plant_subset)[
                        :,
                        :value,
                    ] * row.MW_sum)[1]

                capacity_adjust = hydcapadj[
                    (hydcapadj.i .== row.i) .&& (hydcapadj.r .== row.r),
                    [:month, :value],
                ]
                dispatch_limit[reqd_slice] .=
                    (filter(x -> (x.month == monhr.month), capacity_adjust)[
                        :,
                        :value,
                    ] * row.MW_sum)[1]
            catch e
                if isa(e, BoundsError)
                    @error "$(row.r),$(row.i),$(e)"
                else
                    error()
                end
            end
        end

        category = string(row.i)
        name = "$(category)_$(string(row.r))"
        region = string(row.r)

        if category in keys(FOR_dict)
            gen_for = FOR_dict[category]
        else
            gen_for = 0.00 # make this 0 for vg if no match
        end

        # - Charging to genstore is limited by charge_capacity whether from grid or from 
        # inflows. So, that charge_capacity should be equal to the genflow timeseries.
        # - Powerflow into grid is limited by grid_injection, which can come from discharge
        # and/or exogenous inflow. So discharge capacity can be the dispatch limit or 
        # arbitrarily high, while the grid_injection cap has to the dispatch limit.
        # - Energy capacity can be arbitrarily high in the absense of reservoir limit to 
        # ensure month to month energy energy carryover.
        push!(
            genstor_array,
            Gen_Storage(
                name = name,
                timesteps = timesteps,
                region_name = region,
                charge_cap = repeat(monthly_energy, num_years),
                discharge_cap = repeat(dispatch_limit, num_years),
                energy_cap = repeat(energy_cap, num_years),
                inflow = repeat(monthly_energy, num_years),
                grid_withdrawl_cap = zeros(timesteps),
                grid_inj_cap = repeat(dispatch_limit, num_years),
                type = category,
                legacy = "New",
                FOR = 0.0, 
                MTTR = user_inputs["MTTR"],
            ),
        )
    end

    # Non-dispatchable hydro power plants
    non_disp_combined_caps = DataFrames.combine(
        DataFrames.groupby(hydro_non_disp_capacities, [:i, :r]),
        :MW => sum,
    )

    # For non dispatchable hydro plants, the monthly capacity factor is used to determine
    # hourly capacity time series in each month. 
    for (idx, row) in enumerate(DataFrames.eachrow(non_disp_combined_caps))
        reg_type = hydcf[
            findall(x -> (x.r == row.r && x.i == row.i), eachrow(hydcf)),
            [:month, :value],
        ]
        hourly_capacity = zeros(timesteps_year)
        for monhr in monthhours
            try
                reqd_slice = monhr.slice
                hourly_capacity[reqd_slice] .=
                    (filter(x -> (x.month == monhr.month), reg_type)[
                        :,
                        :value,
                    ] * row.MW_sum)[1]
            catch e
                @error "$(row.r),$(row.i),$(e)"
            end
        end

        category = string(row.i)
        name = "$(category)_$(string(row.r))"
        region = string(row.r)

        if category in keys(FOR_dict)
            gen_for = FOR_dict[category]
        else
            gen_for = 0.00 # make this 0 for vg if no match
        end

        push!(
            generators_array,
            Variable_Gen(
                name = name,
                timesteps = timesteps,
                region_name = region,
                installed_capacity = row.MW_sum,
                capacity = repeat(hourly_capacity, num_years),
                type = category,
                legacy = "New",
                FOR = 0.0, 
                MTTR = user_inputs["MTTR"],
            ),
        )
    end

    return generators_array, genstor_array
end

"""
    Process data associated with the regional storage build for modeled time
    period

    Parameters
    ----------
    storage_builds : DataFrames.DataFrame
        Data construct containing regional storage build information
    FOR_dict : Dict
        dictionary of Forced Outage Rates (FOR) associated with storage types
    ReEDS_data
        input data from ReEDS
    timesteps : Int
        Number of timesteps
    year : Int64
        simulated time period

    Returns
    -------
    storages_array : Storage[]
        array of modeled storages
"""
function process_storages(
    storage_builds::DataFrames.DataFrame,
    FOR_dict::Dict,
    unitsize_dict::Dict,
    ReEDS_data,
    timesteps::Int,
    year::Int64,
    user_inputs::Dict{Any, Any},
)
    storage_energy_capacity_data = get_storage_energy_capacity_data(ReEDS_data)
    @debug "storage_energy_capacity_data is $(storage_energy_capacity_data)"
    # split-apply-combine to handle differently vintaged entries
    energy_capacity_df = DataFrames.combine(
        DataFrames.groupby(storage_energy_capacity_data, ["i", "r"]),
        :MWh => sum,
    )

    ## Read {case}/inputs_case/tech-subset-table.csv
    tech_subset_table = get_technology_types(ReEDS_data)
    battery_types = DataFrames.dropmissing(tech_subset_table, :BATTERY)[:, "Column1"]

    storages_array = Storage[]
    for (idx, row) in enumerate(eachrow(storage_builds))
        name = "$(string(row.i))|$(string(row.r))"
        if string(row.i) in keys(FOR_dict)
            gen_for = FOR_dict[string(row.i)]
        else
            gen_for = 0.0
            @info "STORAGE: did not find FOR for storage $name $(row.r)
                   $(row.i), so setting FOR to default value $gen_for"
        end
        name = "$(name)|"#append for later matching

        #we need to know if the storage is battery or not
        #batteries will be deflated...

        # as per discussion w/ patrick, find duration of storage, then make
        # energy capacity on that duration?
        int_duration = round(energy_capacity_df[idx, "MWh_sum"] / row.MW)
        if string(row.i) in battery_types
            push!(
                storages_array,
                Battery(
                    name = name,
                    timesteps = timesteps,
                    region_name = string(row.r),
                    type = string(row.i),
                    charge_cap = row.MW,
                    discharge_cap = row.MW,
                    energy_cap = round(Int, row.MW) * int_duration * (1 - gen_for),
                    legacy = "New",
                    charge_eff = 1.0,
                    discharge_eff = 1.0,
                    carryover_eff = 1.0,
                    FOR = 0.0,
                    MTTR = user_inputs["MTTR"],
                ),
            )
        else
            add_new_capacity!(
                ReEDS_data,
                storages_array,
                round(Int, row.MW),
                round(Int, int_duration),
                0,
                0,
                unitsize_dict,
                row.i,
                row.r,
                gen_for,
                timesteps,
                year,
                user_inputs["MTTR"],
            )
        end
    end
    return storages_array
end

"""
    Disaggregates the existing capacity of a thermal generator given a certain
    year, by taking into account its technology and associated balancing
    authority.

    Parameters
    ----------
    eia_df : DataFrames.DataFrame
        DataFrame containing Expected Information Administration (EIA) data.
    built_capacity : int
        The current built capacity for the thermal generator.
    tech : str
        The technology for the thermal generator.
    pca : str
        The associated balancing authority (PCA).
    gen_for : float
        The forced outage rate associated with the generator.
    timesteps : Int
        Number of timesteps.
    year : int
        The year.

    Returns
    -------
    generators_array : array
        An array composed of thermal generator objects created with the
        disaggregated existing capacities.
"""
function disagg_existing_capacity(
    ReEDS_data::ReEDSdatapaths,
    eia_df::DataFrames.DataFrame,
    unitsize_dict::Dict,
    built_capacity::Int,
    tech::String,
    pca::String,
    gen_for::Vector{Float32},
    timesteps::Int,
    year::Int,
    user_inputs::Dict{Any, Any},
)
    tech_ba_year_existing = DataFrames.subset(
        eia_df,
        :tech => DataFrames.ByRow(==(tech)),
        :reeds_ba => DataFrames.ByRow(==(pca)),
        :RetireYear => DataFrames.ByRow(>=(year)),
        :StartYear => DataFrames.ByRow(<=(year)),
    )

    generators_array = []
    if DataFrames.nrow(tech_ba_year_existing) == 0 && gen_for != 0.0
        add_new_capacity!(
            ReEDS_data,
            generators_array,
            built_capacity,
            0,
            0,
            unitsize_dict,
            tech,
            pca,
            gen_for,
            timesteps,
            year,
            user_inputs["MTTR"],
        )
        return generators_array
    elseif DataFrames.nrow(tech_ba_year_existing) == 0 && gen_for == 0.0
        #not necessary to disagg if generator never fails
        return [
            Thermal_Gen(
                name = "$(tech)|$(pca)|1",
                timesteps = timesteps,
                region_name = pca,
                capacity = built_capacity,
                fuel = tech,
                legacy = "New",
                FOR = gen_for,
                MTTR = user_inputs["MTTR"],
            ),
        ]
    end

    remaining_capacity = built_capacity
    existing_capacity = tech_ba_year_existing[!, "cap"]

    tech_len = length(existing_capacity)
    max_cap = maximum(existing_capacity)
    avg_cap = Statistics.mean(existing_capacity)

    for (idx, built_cap) in enumerate(existing_capacity)
        int_built_cap = floor(Int, built_cap)
        if int_built_cap < remaining_capacity
            gen_cap = int_built_cap
            remaining_capacity -= int_built_cap
        else
            gen_cap = remaining_capacity
            remaining_capacity = 0
        end
        gen = Thermal_Gen(
            name = "$(tech)|$(pca)|$(idx)",
            timesteps = timesteps,
            region_name = pca,
            capacity = gen_cap,
            fuel = tech,
            legacy = "Existing",
            FOR = gen_for,
            MTTR = user_inputs["MTTR"],
        )
        push!(generators_array, gen)
    end

    #whatever remains, we want to build as new capacity
    if remaining_capacity > 0
        add_new_capacity!(
            ReEDS_data,
            generators_array,
            remaining_capacity,
            floor.(Int, avg_cap),
            floor.(Int, max_cap),
            unitsize_dict,
            tech,
            pca,
            gen_for,
            timesteps,
            year,
            user_inputs["MTTR"],
        )
    end

    return generators_array
end

"""
    This function adds new capacity to an existing list of generators. The
    avg_unit_cap parameter is used to determine how many generators
    must be constructed to create the total new_capacity. If there are no
    existing units, a single generator is built with all of the new_capacity.
    For fixed avg_unit_cap values, the remaining capacity is divided
    evenly among the new generators, adding additional capacity to each one,
    then a small remainder may be created and added as a separate generator to
    get the desired total new_capacity. The output of this function is the
    updated generators_array containing all of the newly added generators.

    Parameters
    ----------
    generators_array : Vector{<:Any}
        a vector or list of existing generators
    new_capacity : int
        specified new capacity to be added
    avg_unit_cap : int
        average capacity for the existing units
    max : int
        maximum capacity for the existing units
    tech : string
        type of technology used for the generator unit
    pca : string
        power control authority of the generator unit
    gen_for : float
        generation forecast
    timesteps : Int
        number of timesteps
    year : int
        year in which the generator is operating
    MTTR : int
        mean time to repair for the generator unit

    Returns
    -------
    generators_array: Vector{<:Any}
        updated vector or list of generators containing the new capacity
"""
function add_new_capacity!(
    ReEDS_data::ReEDSdatapaths,
    generators_array::Vector{<:Any},
    new_capacity::Int,
    avg_unit_cap::Int,
    max::Int,
    unitsize_dict::Dict,
    tech::AbstractString,
    pca::AbstractString,
    gen_for::Vector{Float32},
    timesteps::Int,
    year::Int,
    MTTR::Int,
)
    # if there are no existing units to determine size of new unit(s),
    # use ATB
    if avg_unit_cap == 0
        try
            # use conventional name first (no water, no tech)
            avg_unit_cap = unitsize_dict[tech]
        catch
            # if no match, then check if it's an upgraded tech without water suffixes
            # e.g. gas-cc_gas-cc-ccs_mod or gas-cc_H2-CT
            
            # Import and concat upgrade_link.csv and upgradelink_water.csv from inputs_case
            # to make the following dictionary:
            filepath = joinpath(ReEDS_data.ReEDSfilepath, "inputs_case", "upgrade_link.csv")
            df1 = DataFrames.DataFrame(CSV.File(filepath))
            filepath2 = joinpath(ReEDS_data.ReEDSfilepath, "inputs_case", "upgradelink_water.csv")
            df2 = DataFrames.DataFrame(CSV.File(filepath2))

            DataFrames.rename!(df2, "*TO-WATER" => "*TO", "FROM-WATER" => "FROM", "DELTA-WATER" => "DELTA")

            df_combined = vcat(df1,df2)

            df3 = df_combined[:, ["*TO", "DELTA"]]
            df3_dict = Dict(lowercase(row["*TO"]) => lowercase(row["DELTA"]) for row in eachrow(df3))
            
            try
                avg_unit_cap = unitsize_dict[df3_dict[tech]]
            catch
                # if still no match, it might be an upgraded tech with water suffixes
                # e.g. gas-cc_r_fg_gas-cc-ccs_mod_r_fg 
                try
                    avg_unit_cap = unitsize_dict[rsplit(df3_dict[tech], "_"; limit = 3)[1]]
                catch
                    # if still no match, then likely a non-upgraded tech with water suffixes
                    # e.g. gas-cc_r_fg
                    try
                        avg_unit_cap = unitsize_dict[rsplit(tech, "_"; limit = 3)[1]]
                    catch   
                        # if still no match, try dropping trailing digits
                        # e.g. wind-ons_1
                        try
                            avg_unit_cap = unitsize_dict[match(r"(.+)_\d+", tech)[1]]
                        catch
                            # Finally, if still no match, tech is likely "csp{CSP_Type}_{class}"
                            avg_unit_cap = unitsize_dict[match(r"(.+)\d_\d", tech)[1]]
                            # will fail if this last thing doesn't work!
                        end
                    end
                end
            end
        end
    end

    n_gens = floor(Int, new_capacity / avg_unit_cap)
    if n_gens == 0
        return push!(
            generators_array,
            Thermal_Gen(
                name = "$(tech)|$(pca)|new|1",
                timesteps = timesteps,
                region_name = pca,
                capacity = new_capacity,
                fuel = tech,
                legacy = "New",
                FOR = gen_for,
                MTTR = MTTR,
            ),
        )
    end

    for i in range(1, n_gens)
        push!(
            generators_array,
            Thermal_Gen(
                name = "$(tech)|$(pca)|new|$(i)",
                timesteps = timesteps,
                region_name = pca,
                capacity = avg_unit_cap,
                fuel = tech,
                legacy = "New",
                FOR = gen_for,
                MTTR = MTTR,
            ),
        )
    end

    remainder = new_capacity - (n_gens * avg_unit_cap)
    if remainder > 0
        # integer remainder is made into a tiny gen
        push!(
            generators_array,
            Thermal_Gen(
                name = "$(tech)|$(pca)|new|$(n_gens+1)",
                timesteps = timesteps,
                region_name = pca,
                capacity = remainder,
                fuel = tech,
                legacy = "New",
                FOR = gen_for,
                MTTR = MTTR,
            ),
        )
    end

    return generators_array
end

"""
    This function is the same as above but takes an additional arg
    new_duration, which will be picked up by multiple dispatch
    and leading to Battery{} model handling
"""

function add_new_capacity!(
    ReEDS_data::ReEDSdatapaths,
    generators_array::Vector{<:Any},
    new_capacity::Int,
    new_duration::Int,
    avg_unit_cap::Int,
    max::Int,
    unitsize_dict::Dict,
    tech::AbstractString,
    pca::AbstractString,
    gen_for::Float64,
    timesteps::Int,
    year::Int,
    MTTR::Int,
)
    # if there are no existing units to determine size of new unit(s),
    # use ATB
    if avg_unit_cap == 0
        try
            # use conventional name first (no water, no tech)
            avg_unit_cap = unitsize_dict[tech]
        catch
            # if no match, then check if it's an upgraded tech without water suffixes
            # e.g. gas-cc_gas-cc-ccs_mod or gas-cc_H2-CT
            
            # Import and concat upgrade_link.csv and upgradelink_water.csv from inputs_case
            # to make the following dictionary:
            filepath = joinpath(ReEDS_data.ReEDSfilepath, "inputs_case", "upgrade_link.csv")
            df1 = DataFrames.DataFrame(CSV.File(filepath))
            filepath2 = joinpath(ReEDS_data.ReEDSfilepath, "inputs_case", "upgradelink_water.csv")
            df2 = DataFrames.DataFrame(CSV.File(filepath2))

            DataFrames.rename!(df2, "*TO-WATER" => "*TO", "FROM-WATER" => "FROM", "DELTA-WATER" => "DELTA")

            df_combined = vcat(df1,df2)

            df3 = df_combined[:, ["*TO", "DELTA"]]
            df3_dict = Dict(lowercase(row["*TO"]) => lowercase(row["DELTA"]) for row in eachrow(df3))
            
            try
                avg_unit_cap = unitsize_dict[df3_dict[tech]]
            catch
                # if still no match, it might be an upgraded tech with water suffixes
                # e.g. gas-cc_r_fg_gas-cc-ccs_mod_r_fg 
                try
                    avg_unit_cap = unitsize_dict[rsplit(df3_dict[tech], "_"; limit = 3)[1]]
                catch
                    # if still no match, then likely a non-upgraded tech with water suffixes
                    # e.g. gas-cc_r_fg
                    try
                        avg_unit_cap = unitsize_dict[rsplit(tech, "_"; limit = 3)[1]]
                    catch   
                        # if still no match, try dropping trailing digits
                        # e.g. wind-ons_1
                        try
                            avg_unit_cap = unitsize_dict[match(r"(.+)_\d+", tech)[1]]
                        catch
                            # Finally, if still no match, tech is likely "csp{CSP_Type}_{class}"
                            avg_unit_cap = unitsize_dict[match(r"(.+)\d_\d", tech)[1]]
                            # will fail if this last thing doesn't work!
                        end
                    end
                end
            end
        end
    end

    n_gens = floor(Int, new_capacity / avg_unit_cap)
    if n_gens == 0
        return push!(
            generators_array,
            Battery(
                name = "$(tech)|$(pca)|new|1",
                timesteps = timesteps,
                region_name = pca,
                type = tech,
                charge_cap = new_capacity,
                discharge_cap = new_capacity,
                energy_cap = round(Int, new_capacity) * new_duration,
                legacy = "New",
                charge_eff = 1.0,
                discharge_eff = 1.0,
                carryover_eff = 1.0,
                FOR = gen_for,
                MTTR = MTTR,
            ),
        )
    end

    for i in range(1, n_gens)
        push!(
            generators_array,
            Battery(
                name = "$(tech)|$(pca)|new|$(i)",
                timesteps = timesteps,
                region_name = pca,
                type = tech,
                charge_cap = avg_unit_cap,
                discharge_cap = avg_unit_cap,
                energy_cap = round(Int, avg_unit_cap) * new_duration,
                legacy = "New",
                charge_eff = 1.0,
                discharge_eff = 1.0,
                carryover_eff = 1.0,
                FOR = gen_for,
                MTTR = MTTR,
            ),
        )
    end

    remainder = new_capacity - (n_gens * avg_unit_cap)
    if remainder > 0
        # integer remainder is made into a tiny gen
        push!(
            generators_array,
            Battery(
                name = "$(tech)|$(pca)|new|$(n_gens+1)",
                timesteps = timesteps,
                region_name = pca,
                type = tech,
                charge_cap = remainder,
                discharge_cap = remainder,
                energy_cap = round(Int, remainder) * new_duration,
                legacy = "New",
                charge_eff = 1.0,
                discharge_eff = 1.0,
                carryover_eff = 1.0,
                FOR = gen_for,
                MTTR = MTTR,
            ),
        )
    end

    return generators_array
end
