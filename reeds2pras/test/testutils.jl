function capacity_checker(
    capacity_data::DataFrames.DataFrame,
    gentype::String,
    region::String,
)
    capacity_data_subset =
        capacity_data[(capacity_data.i .== gentype) .& (capacity_data.r .== region), :]
    return sum(capacity_data_subset[!, "MW"])
end

function vg_capacity_checker(cf_info::Dict, gentype::String, region::String)
    name = "$(gentype)_$(region)"
    profile_index = findfirst.(isequal.(name), (cf_info["axis0"],))[1]

    if isnothing(profile_index)
        return 0
    else
        profile = cf_info["block0_values"][profile_index, :]
        return maximum(profile)
    end
end

function PRAS_generator_capacity_checker(pras_system, gentype::String, region::String)
    name_vec = -abs.(cmp.(gentype, pras_system.generators.categories)) .+ 1 #exact match is needed to exclude ccs
    reg_vec = occursin.("$(region)_", pras_system.generators.names)
    out_vec = .*(name_vec, reg_vec)
    retained_gens = [idx for (idx, val) in enumerate(out_vec) if val == 1]

    return sum(maximum.(eachrow(pras_system.generators.capacity[Int.(retained_gens), :])))
end

function PRAS_storage_capacity_checker(pras_system, gentype::String, region::String)
    name_vec = occursin.(gentype, pras_system.storages.names)
    reg_vec = occursin.("$(region)_", pras_system.storages.names)
    out_vec = .*(name_vec, reg_vec)
    retained_gens = [idx for (idx, val) in enumerate(out_vec) if val == 1]

    return sum(
        maximum.(eachrow(pras_system.storages.discharge_capacity[Int.(retained_gens), :])),
    )
end

function clean_gentype(input_name::String)
    if occursin("*", input_name)
        input_name = String(match(r"\*([a-zA-Z]+-*[a-zA-Z]*)_*", input_name)[1])
        input_vec = expand_vg_types([input_name], 15)
    else
        input_vec = [input_name]
    end
    return input_vec
end

function expand_vg_types(vg_vec::Vector{<:AbstractString}, timesteps::Int64)
    return vec(["$(a)_$(n)" for a in vg_vec, n in 1:timesteps])
end

function run_pras_system(sys::PRAS.SystemModel, sample::Int)
    shortfalls, flows = PRAS.assess(
        sys,
        PRAS.SequentialMonteCarlo(samples = sample, seed = 1),
        PRAS.Shortfall(),
        PRAS.Flow(),
    )
    println(PRAS.LOLE(shortfalls))
    println(PRAS.EUE(shortfalls))
    return shortfalls, flows
end

function compare_generator_capacities(
    pras_system::PRAS.SystemModel,
    ReEDSfilepath,
    year::Int,
)
    #first actually have to load in case-level capacity data, which may not be passed
    ReEDS_data = ReEDS2PRAS.ReEDSdatapaths(ReEDSfilepath, year)

    capacity_data = ReEDS2PRAS.get_ICAP_data(ReEDS_data)
    vg_resource_types = ReEDS2PRAS.get_valid_resources(ReEDS_data)
    cf_info = ReEDS2PRAS.get_vg_cf_data(ReEDS_data)

    for gentype in unique(capacity_data.i)
        gentype = String(gentype)
        for region in pras_system.regions.names
            if occursin(gentype, join(unique(vg_resource_types.i)))#vg only
                v1 = 0
                for row in eachrow(vg_resource_types)
                    if row.i == gentype && String(row.r) == region
                        v1 += vg_capacity_checker(cf_info, gentype, String(row.r))
                    end
                end
                delta = 0.95
            else
                v1 = capacity_checker(capacity_data, gentype, region) #need to split out numbering for vg...
                delta = 1.0
            end
            v2a = PRAS_generator_capacity_checker(pras_system, gentype, region)
            v2b = PRAS_storage_capacity_checker(pras_system, gentype, region)
            v2 = v2a + v2b
            if (v1 != 0 || v2 != 0) && (1 / delta) >= (abs(v1 - v2) / v2) >= delta
                @info "for $gentype-$region input is $v1 MW, output is $v2 MW. Mismatch!!"
            end
        end
    end
end

function compare_line_capacities(pras_system::PRAS.SystemModel, ReEDSfilepath, year::Int)
    ReEDS_data = ReEDS2PRAS.ReEDSdatapaths(ReEDSfilepath, year)
    line_df = ReEDS2PRAS.get_line_capacity_data(ReEDS_data)

    for row in eachrow(line_df)
        r1_vec = occursin.("$(row.r)_", pras_system.lines.names)
        r2_vec = occursin.("$(row.rr)_", pras_system.lines.names)
        type_vec = occursin.(row.trtype, pras_system.lines.names)
        out_vec = .*(r1_vec, r2_vec, type_vec)
        mw_sum = 0
        retained_lines = [idx for (idx, val) in enumerate(out_vec) if val == 1]
        for idx in retained_lines #TODO: there has to be a better, way, but for now
            mw_sum += row.MW
        end
        mw_out_fwd, mw_out_bck = get_pras_line_capacity(pras_system, Int.(retained_lines))

        if row.r < row.rr #actually want to compare strings to get proper ordering
            @info "forward in MW is $mw_sum out forward is $mw_out_fwd, for $(row.r) to $(row.rr), $(row.trtype)"
            @assert abs(mw_sum - mw_out_fwd) <= 1
        else #bckwd line cap
            @info "backward in MW is $mw_sum out backward is $mw_out_bck for $(row.r) to $(row.rr), $(row.trtype)"
            @assert abs(mw_sum - mw_out_bck) <= 1
        end
    end
end

function get_pras_line_capacity(pras_system::PRAS.SystemModel, idx_list::Vector)
    #TODO: check backward capacity?
    fwd = sum(maximum.(eachrow(pras_system.lines.forward_capacity[idx_list, :]))) #get pras line fwd capacity
    bck = sum(maximum.(eachrow(pras_system.lines.backward_capacity[idx_list, :]))) #get pras line fwd capacity
    return fwd, bck
end
