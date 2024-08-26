using Revise

using ReEDS2PRAS
using PRAS
using CSV
using DataFrames
using Dates
using HDF5
using Statistics
using Test
using TimeZones

using BenchmarkTools

rootfile = @__FILE__

include("testutils.jl")

if length(ARGS) == 0
    required_tests = ["ReEDS2PRAS"]
else
    required_tests = ARGS
end

for test_name in required_tests
    include("test_$(test_name).jl")
end
