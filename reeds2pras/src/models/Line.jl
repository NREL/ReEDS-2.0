const ReEDS_LINE_TYPES = ["AC", "B2B", "LCC", "VSC", "VSC DC-AC converter"]

"""
    Constructs a model of LINE.

    Parameters
    ----------
    name : String
        Name chose for a line object
    timesteps : Int64
        Number of timeseries for the same identifier (assumed same for all
        type of objects)
    category : String
        Type of Line object. Category can be one of AC/B2B/LCC/VSC/VSC
        DC-AC converter
    region_from : String
        Origin region of the line object
    region_to : String
        Destination region of the line object
    forward_cap : Float64
        Capacity of the line object in forward direction
    backward_cap : Float64
        Capacity of the line object in backward direction
    legacy : String
        Check whether it is existing or new i.e., RET or TEST
    FOR : Float64
        Forced Outage Rate of the line object
    MTTR : Int64
        Mean Time to Repair of the line object
    VSC : Bool
        Voltage Source Converter of the line object
    converter_capacity : Dict{String, Float64}
        Dictionary that stores the VSC capacities within Region_From and
        Region_To

    Returns
    -------
    Out: Line
        A new instance of Line object as defined above

"""
struct Line
    name::String
    timesteps::Int64
    category::String
    region_from::String
    region_to::String
    forward_cap::Float64
    backward_cap::Float64
    legacy::String
    FOR::Float64
    MTTR::Int64
    VSC::Bool
    converter_capacity::Dict{String, Float64}

    # Inner Constructors & Checks
    function Line(;
        name = "init_name",
        timesteps = 8760,
        category = "AC",
        region_from = "init_reg_from",
        region_to = "init_reg_to",
        forward_cap = 0.0,
        backward_cap = 0.0,
        legacy = "New",
        FOR = 0.0,
        MTTR = 24,
        VSC = false,
        converter_capacity = Dict(region_from => 0.0, region_to => 0.0),
    )
        category in ReEDS_LINE_TYPES ||
            error("$(name) has category $(category) which is not in $(ReEDS_LINE_TYPES)")

        ~(region_from == region_to) ||
            error("Region_From and Region_To cannot be the same for $(name). PRAS only
                   considers inter-regional lines in zonal analysis")

        all([forward_cap, backward_cap] .>= 0.0) ||
            error("$(name) forward/backward capacity value < 0")

        legacy in ["Existing", "New"] ||
            error("$(name) has legacy $(legacy) which is not in [Existing, New]")

        0.0 <= FOR <= 1.0 || error("$(name) FOR value is < 0 or > 1")

        MTTR > 0 || error("$(name) MTTR value is <= 0")

        all([region_from, region_to] .∈ Ref(keys(converter_capacity))) ||
            error("Check the keys of converter capacity dictionary for VSC DC
                   line: $(name)")

        return new(
            name,
            timesteps,
            category,
            region_from,
            region_to,
            forward_cap,
            backward_cap,
            legacy,
            FOR,
            MTTR,
            VSC,
            converter_capacity,
        )
    end
end

# Getter Functions

get_name(ln::Line) = ln.name

get_category(ln::Line) = ln.category

get_forward_capacity(ln::Line) = fill(round(Int, ln.forward_cap), 1, ln.timesteps)

get_backward_capacity(ln::Line) = fill(round(Int, ln.backward_cap), 1, ln.timesteps)

get_region_from(ln::Line) = ln.region_from

get_region_to(ln::Line) = ln.region_to

#Helper functions

get_outage_rate(ln::Line) = outage_to_rate(ln.FOR, ln.MTTR)

get_λ(ln::Line) = fill(getfield(outage_to_rate(ln.FOR, ln.MTTR), :λ), 1, ln.timesteps)

get_μ(ln::Line) = fill(getfield(outage_to_rate(ln.FOR, ln.MTTR), :μ), 1, ln.timesteps)

"""
    Return all lines with the specified legacy.

    Parameters
    ----------
    lines : Vector{<:Line}
        List of Lines to filter through.
    leg : String
        Legacy of Line, either 'Existing' or 'New'.

    Returns
    -------
    Vector{<:Line}
        List of all lines with the specified legacy.
"""
function get_legacy_lines(lines::Vector{Line}, leg::String)
    leg in ["Existing", "New"] || error("Unidentified legacy passed")

    leg_lines = filter(ln -> ln.legacy == leg, lines)
    if isempty(leg_lines)
        # @warn "No lines with legacy: $(leg)"
    else
        return leg_lines
    end
end
