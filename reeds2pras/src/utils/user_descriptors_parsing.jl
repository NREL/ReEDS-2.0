isjson = endswith(".json");

function parse_user_descriptors(file::String)
    if ~(isjson(file))
        @warn "user descriptors file provided is not in JSON format. Using default values."
        file = joinpath(@__DIR__, "Descriptors", "user_descriptors.json")
    end

    user_input_dict = JSON.parsefile(file)
    user_inputs = Dict()
    for key in keys(user_input_dict)
        for inner_key in keys(user_input_dict[key])
            push!(
                user_inputs,
                user_input_dict[key][inner_key]["name"] =>
                    user_input_dict[key][inner_key]["value"],
            )
        end
    end

    return user_inputs
end
