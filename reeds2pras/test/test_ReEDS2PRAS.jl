@testset "ReEDS2PRAS" begin
    reedscase = joinpath(dirname(rootfile), "reeds_cases", "USA_VSC_2035")
    solve_year = 2035
    timesteps = 61320
    weather_year = 2007
    samples = 10
    seed = 1

    # Run ReEDS2PRAS
    pras_sys = ReEDS2PRAS.reeds_to_pras(reedscase, solve_year, timesteps, weather_year)

    compare_generator_capacities(pras_sys, reedscase, solve_year)
    compare_line_capacities(pras_sys, reedscase, solve_year)

    #Testing PRAS Analytics can be done, but not as part of ReEDS2PRAS
    # include("/projects/ntps/llavin/PRAS-Analytics/src/PRAS_Analytics.jl") #will only work if you have this path for this test
    # PRAS.savemodel(psys_LD,joinpath(tp,"outputs","v20221201_NTPh0_VSC_DemHi_90by2035EarlyPhaseout__core_"*string(ty)*".pras"))#save the system to a .pras file

    # pras_sys_location = joinpath(tp,"outputs","v20221201_NTPh0_VSC_DemHi_90by2035EarlyPhaseout__core_"*string(ty)*".pras")

    # PRAS_Analytics.run_pras_analysis(pras_sys_location, "v20221201_NTPh0_VSC_DemHi_90by2035EarlyPhaseout__core", 20232008, 10, plots = true, results_location = tp) 

end
