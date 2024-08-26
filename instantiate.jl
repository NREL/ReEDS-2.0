ENV["JULIA_SSL_CA_ROOTS_PATH"] = ""
import Pkg
Pkg.Registry.update()
Pkg.Registry.add("General")
Pkg.Registry.add(Pkg.RegistrySpec(url="https://github.com/NREL/JuliaRegistry.git"))
Pkg.instantiate()

Pkg.add("Random123")

# Make sure PRAS installation worked
import PRAS

# Make sure TimeZones works
import TimeZones
# TimeZones.build()
TimeZones.ZonedDateTime(2007, 01, 01, 00, TimeZones.tz"EST")
