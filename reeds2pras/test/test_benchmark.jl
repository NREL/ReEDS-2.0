println("Running benchmark")

# Running this benchmark:
# From the base directory, open julia with the project env
# If using a Mac, use 1 thread with `JULIA_NUM_THREADS=1 julia --project=.`
# Execute benchmark with : `using Pkg; Pkg.test(test_args=["benchmark"])`
# If running on Kestrel using a batch job, 
# use this in a script from the root folder:
# JULIA_NUM_THREADS=4 julia --project=. -e "using Pkg; Pkg.test(test_args=[\"benchmark\"])"

# Run this file first with the main branch and 
# then the feature branch, record the reported mean time taken 
# for both ReEDS2PRAS and PRAS, and the CONUS LOLE, nEUE output here 
# while submitting pull request with the PR template

# If making major changes to R2P model, increase number of MC samples used

# Set up this test
reedscase = joinpath(dirname(rootfile), "reeds_cases", "USA_VSC_2035")
solve_year = 2035
timesteps = 61320
weather_year = 2007
samples = 10
seed = 1

# Run ReEDS2PRAS
# Update this function to change whether you want to benchmark with 
# hydro_energylim as true to set hydcf based limits
benchmark_r2p = @benchmark pras_sys =
    ReEDS2PRAS.reeds_to_pras(reedscase, solve_year, timesteps, weather_year)

# Run PRAS
pras_sys = ReEDS2PRAS.reeds_to_pras(reedscase, solve_year, timesteps, weather_year)

simulation = SequentialMonteCarlo(samples = samples, seed = seed)

benchmark_pras = @benchmark shortfall = assess(pras_sys, simulation, Shortfall())

shortfall = assess(pras_sys, simulation, Shortfall())

println()
println("ReEDS2PRAS benchmark")

io = IOBuffer()
show(io, "text/plain", benchmark_r2p)
s = String(take!(io))
println(s)

println("\nPRAS benchmark with $(samples) samples")

io = IOBuffer()
show(io, "text/plain", benchmark_pras)
s = String(take!(io))
println(s)

LOLE = PRAS.LOLE(shortfall[1]).lole.estimate
EUE = PRAS.EUE(shortfall[1]).eue.estimate
nEUE = EUE * 1e6 / sum(pras_sys.regions.load)

println("\nPRAS results")
println("LOLE=$(LOLE), nEUE=$(nEUE)")
