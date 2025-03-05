# Run Checks for Versioning?
# Could we use this script ot tag our versions because we cannot include ReEDS ver as a dependency?

# Check if you can open a file
function check_file(loc::String)
    io = try
        open(loc)
    catch
        nothing
    end

    if (isnothing(io))
        return nothing, false
    else
        return io, isopen(io)
    end
end

function run_checks(data::ReEDSdatapaths)

    # EIA NEMS Database
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "unitdata.csv")

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "EIA NEMS database is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the unitdata .csv file/ deleted it.",
        )
    end

    # ReEDS Load Path
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "pras_load_$(string(data.year)).h5",
    )

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Load data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the load .h5 file/ deleted it.",
        )
    end

    # Line Capacity Data
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "tran_cap_$(string(data.year)).csv",
    )

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Line Capacity data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the tran_cap_$(string(data.year)) .csv file/ deleted it.",
        )
    end

    # Converter Capacity Data
    # Is this Optional?
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "cap_converter_$(string(data.year)).csv",
    )

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Converter Capacity data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the cap_converter_$(string(data.year)) .csv file/ deleted it.",
        )
    end

    # Get Technology Types
    # Should we include a check about the structure here? The p1*p10 issue
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "tech-subset-table.csv")

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Generator Technology types data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the tech-subset-table .csv file/ deleted it.",
        )
    end

    # Installed Capacity Data
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "max_cap_$(string(data.year)).csv",
    )

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Installed Capacity data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the max_cap_$(string(data.year)) .csv file/ deleted it.",
        )
    end

    # Valid Resources
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "resources.csv")

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Resource data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the resources .csv file/ deleted it.",
        )
    end

    # Forced Outage Rate
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "outage_forced_static.csv")

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Forced Outage Rate data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the forced_outage_$(string(data.year)) .csv file/ deleted it.",
        )
    end

    # Hourly Forced Outage Rate
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "forcedoutage_hourly.h5")

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Hourly Forced Outage Rate data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the forcedoutage_hourly.h5 file/ deleted it.",
        )
    end

    # ATB unit size data
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "unitsize.csv")

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "ATB unit size data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the unitsize .csv file/ deleted it.",
        )
    end

    # VG CF Data
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "pras_vre_gen_$(string(data.year)).h5",
    )

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "VG CF data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the pras_vre_gen_$(string(data.year)) .h5 file/ deleted it.",
        )
    end

    # Storage Energy Cap Data
    filepath = joinpath(
        data.ReEDSfilepath,
        "ReEDS_Augur",
        "augur_data",
        "energy_cap_$(string(data.year)).csv",
    )

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Storage Capacity data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the energy_cap_$(string(data.year)) .csv file/ deleted it.",
        )
    end

    # Hydro capacity factor data
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "hydcf.csv")

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Hydroelectric capacity factor data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the hydcf.csv file/ deleted it.",
        )
    end

    # Hydro capacity adjustment data
    filepath = joinpath(data.ReEDSfilepath, "inputs_case", "hydcapadj.csv")

    io, bool = check_file(filepath)

    if (bool)
        close(io)
    else
        error(
            "Hydro capacity adjustment data is not available in ReEDS results. You are either using a ReEDS version not compatible with ReEDS2PRAS (or) the ReEDS case results location passed is erroneous (or) you don't have access to the hydcapadj.csv file/ deleted it.",
        )
    end
end
