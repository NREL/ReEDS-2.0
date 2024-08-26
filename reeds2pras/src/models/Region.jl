"""
    Constructs the ReEDS2PRAS Region type. Region objects have three main
    attributes - name (String), timesteps (Int64) and load
    (Vector{Float64}). The load attribute represents the region's total
    power demand data over N intervals of measure given in MW, which must
    always be greater than 0.

    Parameters
    ----------
    name : String
        Name to give the region.
    timesteps : Int64
        Number of PRAS timesteps. 
    load : Vector{Float64}
        Time series data for the region's total power demand must match N
        in length.

    Returns
    -------
    A new instance of the PRAS Region type.
"""
struct Region
    name::String
    timesteps::Int64
    load::Vector{Float64}

    # Inner Constructors & Checks
    function Region(name, timesteps, load = zeros(Float64, timesteps))
        length(load) == timesteps || error(
            "The length of the region $(name) load time series data is $(length(load)) but it should be
             equal to PRAS timesteps ($(timesteps))",
        )

        all(load .>= 0.0) ||
            error("Check for negative values in region $(name) load time series data.")

        return new(name, timesteps, load)
    end
end

# Getter Functions 

get_name(reg::Region) = reg.name

get_load(reg::Region) = permutedims(round.(Int, reg.load))
