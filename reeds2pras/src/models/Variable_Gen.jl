const ReEDS_VRE_TYPES = [
    "wind-ons",
    "wind-ofs",
    "dupv",
    "upv",
    "distpv",
    "csp",
    "pvb",
    "hydnd",
    "hydsnd",
    "hydund",
    "hydnpnd",
    "hydend",
]

function check_reeds_vre_type(
    type::Union{STRING, String},
) where {STRING <: InlineStrings.InlineString}
    if (sum(occursin.(ReEDS_VRE_TYPES, type)) == 1)
        return true
    else
        return false
    end
end

"""
    This function takes in the attributes of a variable generator (Variable_Gen)
    and returns an object containing all its information. The input
    parameters are:

    Parameters
    ----------
    name : String
        Name of the Variable Generator.
    timesteps : Int64
        Number of timesteps for the PRAS model.
    region_name : String
        Name of the Region where Variable Generator's load area is present.
    installed_capacity : Float64
        Installed Capacity of the Variable Generator.
    capacity : Vector{Float64}
        Capacity factor time series data ('forecasted capacity' /
        'nominal capacity') for the PRAS Model.
    type : String
        Type of Variable Generator being passed.
    legacy : String
        State of the Variable Generator, i.e., existing or new.
    FOR : Float64
        Forced Outage Rate parameter of the Variable Generator.
    MTTR : Int64
        Mean Time To Repair parameter of the Variable Generator.

    Returns
    -------
    Variable_Gen : Struct
        Returns a struct with all the given attributes.
"""
struct Variable_Gen <: Generator
    name::String
    timesteps::Int64
    region_name::String
    installed_capacity::Float64
    capacity::Vector{Float64}
    type::String
    legacy::String
    FOR::Float64
    MTTR::Int64

    # Inner Constructors & Checks
    function Variable_Gen(;
        name = "init_name",
        timesteps = 8760,
        region_name = "init_name",
        installed_capacity = 10.0,
        capacity = zeros(Float64, timesteps),
        type = "wind-ons_init_name",
        legacy = "New",
        FOR = 0.0,
        MTTR = 24,
    )
        all(0.0 .<= capacity .<= installed_capacity) || if ~(startswith(type, "hyd"))
            # We do not need to ensure that capacity is < installed capacity
            # for hydroelectric plants because we sometimes have 
            # capacity factors > 1
            error("$(name) time series has values < 0 or > installed capacity
            ($(installed_capacity))")
        end

        length(capacity) == timesteps ||
            error("The length of the $(name) time series data is $(length(capacity))
                   but it should be should be equal to PRAS timesteps ($(timesteps))")

        check_reeds_vre_type(type) ||
            error("$(name) has type $(type) which is not in $(ReEDS_VRE_TYPES)")

        legacy in ["Existing", "New"] ||
            error("$(name) has legacy $(legacy) which is not in [Existing, New]")

        0.0 <= FOR <= 1.0 || error("$(name) FOR value is < 0 or > 1")

        MTTR > 0 || error("$(name) MTTR value is <= 0")

        return new(
            name,
            timesteps,
            region_name,
            installed_capacity,
            capacity,
            type,
            legacy,
            FOR,
            MTTR,
        )
    end
end

# Getter Functions

get_capacity(gen::Variable_Gen) = permutedims(round.(Int, gen.capacity))

get_category(gen::Variable_Gen) = "$(gen.legacy)|$(gen.type)"

get_type(gen::Variable_Gen) = gen.type
