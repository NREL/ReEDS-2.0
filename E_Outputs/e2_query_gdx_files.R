#### Query gdx solution files and create .Rdata file ####

args = commandArgs(trailingOnly=TRUE)
gdxfiles = args[1]
gdxpaths = file.path('E_Outputs','gdxfiles',gdxfiles)

# check that all gdxfiles exist
for(i in gdxpaths){
  if(!file.exists(i)){
    stop(paste0(i, " not found."))
  }
}

# load packages
#if(!require("pacman")){
#  install.packages('devtools')
#  require(remotes)
#  install_version("pacman", version = "0.4.6", repos = "http://cran.us.r-project.org")
#}

save.path = file.path('F_Analysis','data')
save.file = file.path(save.path, gsub('.gdx','.Rdata',gdxfiles))

#pacman::p_load(gdxrrw, data.table, zoo)
rpackagelib = "D:/Conda_envs/reeds3/Lib/R/library"
library(gdxrrw, lib.loc = rpackagelib)
library(data.table, lib.loc = rpackagelib)
library(zoo, lib.loc = rpackagelib)

# load data for analysis
source(file.path('E_Outputs','gdxr_functions.R'))

inputs_dir = file.path('A_Inputs','inputs','analysis')

region.centroids = fread(file.path(inputs_dir,"region_centroids.csv"))

ts.map = fread(file.path(inputs_dir,'time_slice_names.csv'))

centroids = fread(file.path(inputs_dir,"state_population_centers.csv"))

input.params = fread(file.path(inputs_dir,"analysis_parameters.csv"))

# clean and format data
names(centroids) = c("State","x","y")
centroids[,State := gsub(" ","_",State)]
centroids[,State := gsub("_And","",State)]
centroids[,State := gsub("_and","",State)]
centroids[,State := gsub("Puducherry_Pondicherry","Puducherry", State)]
centroids = centroids[, lapply(.SD, mean), by=State, .SDcols=c("x","y") ]
centroids[,State := gsub("Orissa","Odisha",State)]

ts.map[,time_slice := factor(time_slice, levels = ts.map$time_slice)]

input.params[input.params == ""] = NA
gen.order = input.params[!is.na(Gen.Order), Gen.Order]
gen.type.map = na.omit(input.params[,.(reeds.category, Type = factor(Type, levels = gen.order))])

# pull out scenario names
scenario.names = gsub(".gdx|output_","",gdxfiles)
names(gdxfiles) = scenario.names
names(gdxpaths) = scenario.names

# pull states and balancing authorities
pull_gdx_data(type = 'set', gdx.name = 'r_region', r.name = 'ba.set')

ba.set = unique(ba.set)
names(ba.set) = c('State','region','scenario')

# pull resource regions and states
pull_gdx_data(type = 'param', gdx.name = 'r_rs', r.name = 'r.rs.map')
if(any(names(r.rs.map) %in% c('i','j'))){
setnames(r.rs.map, c("i","j",'value','scenario'), c('r','rs','value','scenario'))
}
r.rs.map = unique(r.rs.map[!rs == 'sk',.(r,rs)], by = c('r','rs'))

# pull hours per timeslice
pull_gdx_data(type = 'param', gdx.name = 'hours', r.name = 'hours')
if(any(names(hours) %in% c('i','value'))){
  setnames(hours, c("i", "value", "scenario"), c("h", "hours", "scenario"))
}

# create ordered factors for times and seasons
ts.map[, season_name := tstrsplit(time_slice, "_", fixed=T, keep=1)]
ts.map[, season := factor(season_name, levels = unique(season_name), 
                          labels = c('Dec - Jan','Feb - Mar','Apr - Jun','Jul - Sep','Oct - Nov'))]
ts.map[, time := tstrsplit(time_slice, "_", fixed=T, keep=2)]
ts.map[, time := factor(time, levels = unique(time))]

#------------------------------#
# Demand ----
#------------------------------#

pull_gdx_data(type = 'param', gdx.name = 'lmnt', r.name = 'demand')

col.names = c('State','Timeslice','Year','demand','scenario')
re_name_cols(demand)

#demand = merge(demand, ts.map, by.x = 'Timeslice',by.y = 'h')

# peak demand
peak.demand = demand[, .(demand = sum(demand)),
                     by = .(Year, scenario, Timeslice)]

peak.demand = peak.demand[,.(demand = max(demand)),
                          by = .(Year, scenario)]

#------------------------------#
# Installed capacity ----
#------------------------------#

pull_gdx_data(type = 'variable', gdx.name = 'CAP', r.name = 'cap')

cap = merge(cap, r.rs.map, by.x = 'names.2', by.y = 'rs', all.x = T)
cap[is.na(r), r := names.2]
cap = cap[,.(value = sum(value)), by = .(names,r,names.3,scenario)]

col.names = c('Technology','State','Year','scenario','capacity')
re_name_cols(cap)

# wind and solar capacity by resource region
pull_gdx_data(type = 'variable', gdx.name = 'CAP', r.name = 'cap.rs')

cap.rs = cap.rs[names %in% c('WIND','UPV','DISTPV'), .(value = sum(value)), by = .(names, names.2, names.3, scenario)]

names(cap.rs) = c('Technology','rs','Year','scenario','capacity')
cap.rs = merge(cap.rs, r.rs.map, by = 'rs', all.x = T)
setnames(cap.rs, 'r','State')
cap.rs[,rs := as.character(rs)]

# capacity by storage duration bin
# pull_gdx_data(type = 'variable', gdx.name = 'CAP_SDBIN', r.name = 'sdbin_cap')
# names(sdbin_cap) = c('Technology','type','State','season','sdbin','Year','cap','scenario')
# 
pull_gdx_data(type = 'param', gdx.name = 'sdbin_size', r.name = 'sdbin_size')
if('value' %in% names(sdbin_size)){sdbin_size[,value := NULL]}
if(length(names(sdbin_size)) == 6){
  sdbin_size = sdbin_size[!is.na(sdbin_size)]
  names(sdbin_size) = c('region','season','sdbin','Year','sdbin_size','scenario')
}
# 
# pull_gdx_data(type = 'param', gdx.name = 'cc_storage', r.name = 'cc_storage')
# names(cc_storage) = c('Technology','sdbin','cc_storage', 'scenario')

#------------------------------#
# Capacity iterations ----
#------------------------------#

pull_gdx_data(type = 'param', gdx.name = 'cap_iter', r.name = 'cap_iter')
setnames(cap_iter,'r','rold')
cap_iter = merge(cap_iter, r.rs.map, by.x = 'rold', by.y = 'rs', all.x = T)
cap_iter[is.na(r), r := rold]
cap_iter = cap_iter[,.(value = sum(cap_iter)), by = .(i,v,r,t,cciter,scenario)]

col.names = c('Technology','tech_type','State','Year','cciter','scenario','capacity')
re_name_cols(cap_iter)

#------------------------------#
# Timeslice generation ----
#------------------------------#

pull_gdx_data(type = 'variable', gdx.name = 'GEN', r.name = 'tslc.gen')

col.names = c('Technology','type','State','Timeslice','Year','generation.MW','scenario')
re_name_cols(tslc.gen)

tslc.gen = merge(tslc.gen, hours, by.x = c('Timeslice','scenario'), by.y = c('h','scenario'))
tslc.gen[,generation := generation.MW*hours]


#------------------------------#
# Firm capacity ----
#------------------------------#

pull_gdx_data(type = 'param', gdx.name = 'firm_conv', r.name = 'firm_conv')
pull_gdx_data(type = 'param', gdx.name = 'firm_hydro', r.name = 'firm_hydro')
pull_gdx_data(type = 'param', gdx.name = 'firm_vg', r.name = 'firm_vg')
pull_gdx_data(type = 'param', gdx.name = 'firm_stor', r.name = 'firm_stor')
firm_stor = firm_stor[!is.na(value)]

#firm_stor = merge(tslc.gen, ba.set, by = c("State","scenario"))
#firm_stor = merge(firm_stor, ts.map, by.x = ('Timeslice') , by.y = ('h'))

#firm_stor = firm_stor[,.(value = sum(generation.MW)), by = .(region, season = season_name, Year, Technology, scenario, Timeslice)]
#firm_stor = firm_stor[grepl('BATTERY|PUMPED', Technology),.(value = max(value)), by = .(region, season, Year, Technology, scenario)]
#names(firm_stor) = c('i1','i2','i3','i4','scenario','value')

firm_cap = rbind(firm_conv, firm_hydro)
firm_cap = rbind(firm_cap, firm_vg)
if((!anyNA(firm_stor)) & length(names(firm_stor)) == 6){
  firm_cap = rbind(firm_cap, firm_stor)
}

firm_cap = firm_cap[!is.na(value)]

col.names = c('region','season','Year','Technology','firm_capacity','scenario')
re_name_cols(firm_cap)

firm_cap[, season := factor(season, levels = unique(season),
                            labels = c('Dec - Jan','Feb - Mar','Apr - Jun','Jul - Sep','Oct - Nov'))]

#------------------------------#
# Generation ----
#------------------------------#

pull_gdx_data(type = 'variable', gdx.name = 'GEN', r.name = 'gen')

col.names = c('Technology','type','State','h','Year','generation.MW','scenario')
re_name_cols(gen)

gen <- merge(gen, hours, by= c('h','scenario'))
gen[,generation.MWh := generation.MW*hours]
gen <- gen[,sum(generation.MWh), by = c('Technology','State','Year','scenario')]


#------------------------------#
# South Asia Imports/Exports ----
#------------------------------#

pull_gdx_data(type = 'param', gdx.name = 'import', r.name = 'trade')

col.names = c('Country','State','Timeslice','Year','trade','scenario')
re_name_cols(trade)

# add Nepal storage generation
trade = rbind(trade, tslc.gen[Technology == 'NEPAL_STORAGE'], fill=T)
trade[Technology == 'NEPAL_STORAGE', trade := generation.MW]
trade[Technology == 'NEPAL_STORAGE', Country := 'Nepal']

trade = trade[,.(trade = sum(trade)), by = .(Country,State,Timeslice,Year,scenario)]
#------------------------------#
# Operating reserve provision ----
#------------------------------#

pull_gdx_data(type = 'variable', gdx.name = 'OPRES', r.name = 'opres')

col.names = c('rm1','Technology','rm2','State','Timeslice','Year','opres','scenario')
re_name_cols(opres)

#------------------------------#
# Storage operations ----
#------------------------------#

# Storage in
pull_gdx_data(type = 'variable', gdx.name = 'STORAGE_IN', r.name = 'storage.in')

if(anyNA(storage.in)){
  col.names = c('storage_in','scenario','Technology','type','State','Timeslice','Year')
}else{
  col.names = c('Technology', 'type','State','Timeslice','src','Year','storage_in','scenario')
}
names(storage.in) = col.names

# Storage level
pull_gdx_data(type = 'variable', gdx.name = 'STORAGE_LEVEL', r.name = 'storage.level')

if(anyNA(storage.level)){
  col.names = c('storage_level','scenario','Technology','type','State','Timeslice','Year')
}else{
  col.names = c('Technology', 'type','State','Timeslice','Year','storage_level','scenario')
}

names(storage.level) = col.names

# Storage gen
storage.gen = tslc.gen[grepl('BATTERY|PUMPED', Technology), .(storage_gen=generation.MW,State,scenario,Year,Timeslice,Technology,type) ]

# merge them all together
storage = merge(storage.in, storage.level, all=T)

storage = merge(storage, storage.gen, by=names(storage.gen)[!names(storage.gen)=='storage_gen'], all=T)
storage[is.na(storage_in), storage_in := 0]
storage[is.na(storage_level), storage_level := 0]
storage[is.na(storage_gen), storage_gen := 0]
# 

# convert to MWh, multiply by no. hours per timeslice
storage = merge(storage, hours, by.x = c('Timeslice','scenario'), by.y = c('h','scenario'))
storage[,storage_in.MWh := storage_in*hours]
storage[,storage_gen.MWh := storage_gen*hours]
storage[,storage_level.MWh := storage_level*hours]

#------------------------------#
# Capacity additions -----
#------------------------------#

pull_gdx_data(type = 'variable', gdx.name = 'INV', r.name = 'inv')

inv = merge(inv, r.rs.map, by.x = 'names.2', by.y = 'rs', all.x = T)
inv[is.na(r), r := names.2]
inv = inv[,.(value = sum(value)), by = .(names,r,names.3,scenario)]

col.names = c('Technology','State','Year', 'scenario', 'inv.temp')
re_name_cols(inv)

# add prescribed additions
## conventional prescriptions
pull_gdx_data(type = 'param', gdx.name = 'prescribednonrsc', r.name = 'prescr.nonrsc')

col.names = c('Year','Technology', 'State', 'temp', 'prescribed','scenario')
re_name_cols(prescr.nonrsc)

## RE prescriptions
pull_gdx_data(type = 'param', gdx.name = 'prescribedrsc', r.name = 'prescr.rsc')

col.names = c('Year','Technology','State','Res_Region','temp','prescribed','scenario')
re_name_cols(prescr.rsc)

if("Technology" %in% names(prescr.rsc)){
  prescr.nonrsc = prescr.nonrsc[,!"temp"] ; prescr.rsc = prescr.rsc[,!"temp"]
  
  #  prescr.rsc = prescr.rsc[!Technology %in% c('WIND','UPV','DISTPV')]
  
  prescr.all = rbind(prescr.nonrsc, 
                     prescr.rsc[,.(prescribed=sum(prescribed)),by=.(Year,Technology,State,scenario)])
}else{
  prescr.all = prescr.nonrsc
}

# combine prescribed and model additions
if("prescribed" %in% names(prescr.all)){
  inv.all = merge(inv, prescr.all[Year %in% inv$Year], 
                  by = c("Year","Technology","State","scenario"),
                  all = T)
  inv.all[is.na(inv.temp), inv.temp := 0] ; inv.all[is.na(prescribed), prescribed := 0]
}else{
  inv.all = inv
}

# identify RE investment (INV_RSC includes prescriptions)
inv.all[Technology %in% c('WIND','UPV','DISTPV'), economic := inv.temp - prescribed]

inv.all[!(Technology %in% c('WIND','UPV','DISTPV')), economic := inv.temp]
inv.all[,inv.temp := NULL]

inv.all = melt(inv.all, id.vars = c('Year','Technology','State','scenario'),
               measure.vars = c('economic','prescribed'),
               variable.name = 'type', value.name = 'investments')

inv.all[,investments := round(investments, 4)]

# # throw a warning if there are any negative investments
# if(any(inv.all[,investments < 0 ])){
#   warning("Data includes negative investments... check INV equations for issues.\n")
# }

inv.all[type == 'economic', type := 'Economic']
inv.all[type == 'prescribed', type := 'Prescribed']

# #------------------------------#
# # Retirements ----
# # #------------------------------#
# pull_gdx_data(type = 'variable', gdx.name = 'RETIRE', r.name = 'retire')
# col.names = c('Technology','rm1','State','rm2','Year','retire','scenario')
# re_name_cols(retire)
# 
# retire[,type := 'Economic']
# 
# pull_gdx_data(type = 'param', gdx.name = 'prescribedretirements', r.name = 'prescr.retire')
# col.names = c('Year','State','Technology','rm3','retire','scenario')
# re_name_cols(prescr.retire)
# 
# prescr.retire[,type := 'Prescribed']
# 
# retire = rbind(retire, prescr.retire,
#                fill = T)
# 
# retire[is.na(retire), retire := 0]
# 
# rm(prescr.retire)

#------------------------------#
# Refurbishments ----
#------------------------------#
# pull_gdx_data(type = 'variable', gdx.name = 'INVREFURB', r.name = 'refurb')
# 
# col.names = c('Technology','State','temp','Year','refurb','scenario')
# re_name_cols(refurb)

#------------------------------#
# Transmission capacity between states ----
#------------------------------#
pull_gdx_data(type = 'variable', gdx.name = 'CAPTRAN', r.name = 'tx.cap')

col.names = c('State.x','State.y','trtype','Year','cap','scenario')
re_name_cols(tx.cap)

#------------------------------#
# Region-region transmission capacity ----
#------------------------------#
pull_gdx_data(type = 'set', gdx.name = 'routes_region', r.name = 'reg.tx.routes')
col.names = c('r','rr','trtype','Year','scenario')
re_name_cols(reg.tx.routes)

reg.tx.routes[,route := paste(r,rr,sep = "-")]

tx.reg = copy(tx.cap)
tx.reg[,route := paste(State.x,State.y, sep = "-")]

tx.reg = tx.reg[route %in% reg.tx.routes$route]
tx.reg = merge(tx.reg, ba.set, by.x = c('State.x','scenario'), by.y = c('State','scenario'))

#------------------------------#
# Transmission additions between states ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'txinv', r.name = 'tx.inv')


col.names = c('State.x','State.y','Year','investments','scenario')
re_name_cols(tx.inv)

#------------------------------#
# Total flow between states ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'totflow', r.name = 'tot.flow')

col.names = c('State.x','State.y','Year','flow','scenario')
re_name_cols(tot.flow)

#------------------------------#
# Timeslice flow between states ----
#------------------------------#
pull_gdx_data(type = 'variable', gdx.name = 'FLOW', r.name = 'tslc.flow')

col.names = c('State.x','State.y','Timeslice','Year','trtype','flow','scenario')
re_name_cols(tslc.flow)

#------------------------------#
# Marginal cost ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'margcost', r.name = 'marg.cost')

col.names = c('State','Timeslice','Year','margcost', 'scenario')
re_name_cols(marg.cost)

pull_gdx_data(type = 'param', gdx.name = 'reqt_price', r.name = 'marg.cost.type')

col.names = c('Type','restype','State','Timeslice','Year','margcost','scenario')
re_name_cols(marg.cost.type)

# add time slice definitions
#marg.cost = merge(marg.cost, ts.map, by.x = 'Timeslice',by.y = 'h')

#------------------------------#
# Capital cost ($ per kW) ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'capcost', r.name = 'cap.cost')

cap.cost = merge(cap.cost, r.rs.map, by.x = 'j', by.y = 'rs', all.x = T)
cap.cost[is.na(r), r := j]
cap.cost = cap.cost[,.(value = sum(value)), by = .(i,r,k,scenario)]

col.names = c('Technology','State','Year','scenario','capcost')
re_name_cols(cap.cost)

pull_gdx_data(type = 'param', gdx.name = 'txcapcost', r.name = 'tx.cap.cost')

tx.cap.r = tx.cap.cost[,.(value = sum(value)/2), by = .(i1, i3,scenario)]
tx.cap.rr = tx.cap.cost[,.(value = sum(value)/2), by = .(i2, i3,scenario)]

col.names = c('State','Year', 'scenario','tx.capcost')
re_name_cols(tx.cap.r)
re_name_cols(tx.cap.rr)

tx.cap.cost = rbind(tx.cap.r, tx.cap.rr)

tx.cap.cost = tx.cap.cost[,sum(tx.capcost), by = c('State','Year','scenario')]

#------------------------------#
# O&M costs ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'fomcost', r.name = 'fom.cost')

fom.cost = merge(fom.cost, r.rs.map, by.x = 'j', by.y = 'rs', all.x = T)
fom.cost[is.na(r), r := j]
fom.cost = fom.cost[,.(value = sum(value)), by = .(i,r,k,scenario)]

col.names = c('Technology','State','Year','scenario','fomcost')
re_name_cols(fom.cost)

pull_gdx_data(type = 'param', gdx.name = 'vomcost', r.name = 'vom.cost')

vom.cost = merge(vom.cost, r.rs.map, by.x = 'j', by.y = 'rs', all.x = T)
vom.cost[is.na(r), r := j]
vom.cost = vom.cost[,.(value = sum(value)), by = .(i,r,k,scenario)]

col.names = c('Technology','State','Year', 'scenario','vomcost')
re_name_cols(vom.cost)

#------------------------------#
# Fuel cost ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'fuelcost', r.name = 'fuel.cost')

fuel.cost = merge(fuel.cost, r.rs.map, by.x = 'j', by.y = 'rs', all.x = T)
fuel.cost[is.na(r), r := j]
fuel.cost = fuel.cost[,.(value = sum(value)), by = .(i,r,k,scenario)]

col.names = c('Technology','State','Year','scenario','fuelcost')
re_name_cols(fuel.cost)

rm(col.names)

#------------------------------#
# Opres cost ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'oprescost', r.name = 'opres.cost')

opres.cost = merge(opres.cost, r.rs.map, by.x = 'j', by.y = 'rs', all.x = T)
opres.cost[is.na(r), r := j]
opres.cost = opres.cost[,.(value = sum(value)), by = .(i,r,k,scenario)]

col.names = c('Technology','State','Year','scenario','oprescost')
re_name_cols(opres.cost)

rm(col.names)

#------------------------------#
# Substation cost ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'substcost', r.name = 'subst.cost')

col.names = c('State','Year','substcost','scenario')
re_name_cols(subst.cost)

rm(col.names)

#------------------------------#
# Outages ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'outage', r.name = 'outage')

col.names = c('Technology','Timeslice','outage','scenario')
re_name_cols(outage)


#------------------------------#
# RE Investments (by rs) ----
#------------------------------#
pull_gdx_data(type = 'variable', gdx.name = 'INV_RSC', r.name = 'inv.re')
inv.re = inv.re[,.(value = sum(value)), by = .(names,names.2,names.3,scenario)]

col.names = c('Technology','rs','Year','scenario','capacity')
re_name_cols(inv.re)

#------------------------------#
# Curtailment ----
#------------------------------#
pull_gdx_data(type = 'variable', gdx.name = 'CURT', r.name = 'curt')

col.names = c('State','Timeslice','Year','curtailment','scenario')
re_name_cols(curt)

#------------------------------#
# Curtailment Iterations ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'curt_iter', r.name = 'curt_iter')

col.names = c('Technology','r','Timeslice','Year','iteration','curtailment','scenario')
re_name_cols(curt_iter)

#write.table(curt_iter, 'data/curt_iter.csv',sep = ',', row.names = FALSE)

#------------------------------#
# Capacity Value Iterations ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'cc_iter', r.name = 'cc_iter')

col.names = c('Technology','type','r','season','Year','iteration','cap.value','scenario')
re_name_cols(cc_iter)

#write.table(cc_iter, 'data/cc_iter.csv',sep = ',', row.names = FALSE)

#------------------------------#
# coal transport charge ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'coal_transport', r.name = 'transport_charge')

#------------------------------#
# Emissions ----
#------------------------------#
pull_gdx_data(type = 'variable', gdx.name = 'EMIT', r.name = 'emit')

col.names = c('State','Year','value','scenario')
re_name_cols(emit)

#------------------------------#
# Storage arbitrage value ----
#------------------------------#

# annual value from augur
pull_gdx_data(type = 'param', gdx.name = 'hourly_arbitrage_value_load', r.name = 'hav')
names(hav) = c('Technology','State','Year','HAV','scenario')
hav = merge(hav, ba.set, by = c("State","scenario"))

# total value
pull_gdx_data(type = 'param', gdx.name = 'hav_int', r.name = 'hav_val')
if(length(names(hav_val)) == 6){
  names(hav_val) = c('Technology','State','Year','HAV_VAL','scenario')
  hav_val = merge(hav_val, ba.set, by = c("State","scenario"))
}

#------------------------------#
# Storage arbitrage value ----
#------------------------------#

# add tech investment cost for comparison
pull_gdx_data(type = 'param', gdx.name = 'cost_cap', r.name = 'capital_cost')
names(capital_cost) = c('Technology','Year','cost','scenario')

#------------------------------#
# PVF ONM ----
#------------------------------#

pull_gdx_data(type = 'param', gdx.name = 'pvf_onm', r.name = 'pvf_onm')

#------------------------------------------------------------------------------#
# END DATA QUERIES
#------------------------------------------------------------------------------#

queries = ls()[!ls() %in% c('ba.set','india.df')]

#------------------------------#
# Add region names to data -----
#------------------------------#

for(i in queries){
  if(all("State" %in% names(get(i)) & "scenario" %in% names(get(i)) & 'data.table' %in% class(get(i)))){
     assign(i, merge(get(i), ba.set, by = c("State","scenario")), envir = .GlobalEnv)
  }
}

if("State.x" %in% names(tot.flow)){
  tot.flow = merge(tot.flow, ba.set, by.x = c("State.x","scenario"), by.y = c('State','scenario'))
  tot.flow = merge(tot.flow, ba.set, by.x = c("State.y","scenario"), by.y = c('State','scenario'))
  setcolorder(tot.flow, c('State.x','State.y','region.x','region.y','Year','flow','scenario'))
}

if("State.x" %in% names(tslc.flow)){
  tslc.flow = merge(tslc.flow, ba.set, by.x = c("State.x","scenario"), by.y = c('State','scenario'))
  tslc.flow = merge(tslc.flow, ba.set, by.x = c("State.y","scenario"), by.y = c('State','scenario'))
  setcolorder(tslc.flow, c('State.x','State.y','region.x','region.y','Timeslice','Year','trtype','flow','scenario'))
}

#-------------------------------#
# Change BATTERY from old solutions to BATTERY_4
#-------------------------------#

for(i in queries){
  if('Technology' %in% names(get(i)) & 'data.table' %in% class(get(i))){
    assign(i, get(i)[Technology == 'BATTERY', Technology := 'BATTERY_4'])
  }
}


#------------------------------#
# Set scenario order -----
#------------------------------#

for(i in queries){
  if('scenario' %in% names(get(i))){
    get(i)[,scenario := factor(scenario, scenario.names)]
  }
}

#------------------------------#
# Change Year to numeric -----
#------------------------------#

# check that Year variable exists
for(i in queries){
  if("Year" %in% names(get(i))){
    get(i)[,Year := as.numeric(as.character(Year))]
  }
}

#------------------------------#
# Map technology to analysis category -----
#------------------------------#

# check that Technology variable exists
for(i in queries){
  if("Technology" %in% names(get(i))){
    assign(i, 
           merge(get(i), gen.type.map,
                 by.x = 'Technology',
                 by.y = 'reeds.category'))
  }
}

#------------------------------#
# Add timeslice definitions -----
#------------------------------#

for(i in queries){
  if('Timeslice' %in% names(get(i))){
    assign(i, merge(get(i), ts.map, by.x = 'Timeslice',by.y = 'h'))
  }
}

message(c("Saving analysis data for scenario ", scenario.names))

# save an .Rdata file for analysis
tables = c()
for(i in ls()){
  if('data.table' %in% class(get(i))) tables = c(tables, i)
}
save(list = tables, file = save.file)

# save analysis parameters



