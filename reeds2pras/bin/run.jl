"""
Run script for reeds_to_pras routine
"""

include(joinpath(dirname(@__DIR__),"src","ReEDS2PRAS.jl"))

import PRAS
import ArgParse

# Check if output_filepath is a pras file
is_pras_file = endswith(".pras");

function run_checks(parsed_args::Dict{String,Any})
    if ~(isdir(parsed_args["reedscase"]))
        error("ReEDS case path passed is not a directory.")
    end

    if ~(isnothing(parsed_args["output_filepath"]))
        if ~(is_pras_file(parsed_args["output_filepath"]))
            error("output_filepath passed is not a valid pras file.")
        end
    end

    if ~(isnothing(parsed_args["user_descriptors_filepath"]))
        if ~(ReEDS2PRAS.isjson(parsed_args["user_descriptors_filepath"]))
            error("user descriptors file path passeed is not a valid format.")
        end
    end
end

function parse_commandline()
    """
    Parse command line arguments for use with the reeds_to_pras function
    """
    s = ArgParse.ArgParseSettings()

    @ArgParse.add_arg_table s begin
        "reedscase"
            help = "Location of ReEDS filepath where inputs, results, and " *
                   "outputs are stored"
            required = true
        "solve_year"
            help = "Year for the case being generated"
            required = true
        "timesteps"
            help = "Number of timesteps to use"
            required = true
        "weather_year"
            help = "The year corresponding to the vg profiles"
            required = true
        "output_filepath"
            help = "The path for saving the final model. e.g. ./model.pras"
            required = false
        "user_descriptors_filepath"
            help = "The path of the JSON with user_descriptors"
            required = false
    end

    return ArgParse.parse_args(s)
end


function main()
    parsed_args = parse_commandline()
    @info "Running reeds_to_pras with the follow inputs:"
    for (arg, val) in parsed_args
        @info "$arg  =>  $val"
    end

    run_checks(parsed_args)

    pras_system = 
    if isnothing(parsed_args["user_descriptors_filepath"])
        ReEDS2PRAS.reeds_to_pras(
            parsed_args["reedscase"],
            parse(Int64, parsed_args["solve_year"]),
            parse(Int64, parsed_args["timesteps"]),
            parse(Int64, parsed_args["weather_year"])
        )
    else
        ReEDS2PRAS.reeds_to_pras(
            parsed_args["reedscase"],
            parse(Int64, parsed_args["solve_year"]),
            parse(Int64, parsed_args["timesteps"]),
            parse(Int64, parsed_args["weather_year"]),
            user_descriptors = parsed_args["user_descriptors_filepath"]
        )
    end
    
    if ~isnothing(parsed_args["output_filepath"])
        PRAS.savemodel(pras_system, parsed_args["output_filepath"])
    end
    
    return parsed_args
end

# Run ReEDS2PRAS from command line arguments
main()