#### Query gdx solution files ####

# check if 'gdxfiles' exists
if(!exists('gdxfiles')){
  stop("'gfxfiles' is missing.\nCreate a named chr vector 'gdxfiles' of .gdx files with scenario names.\nExample: gdxfiles = c('scenario1' = 'output.gdx')")
}

# add directory to file names
if(!exists('gdx.dir')){
  stop("'gdx.dir' is missing.\nCreate chr value 'gdx.dir' with your directory for .gdx files.\nExample: gdx.dir = 'D:/gdxfiles'")
}

gdxpaths = sapply(gdxfiles, function(x) file.path(gdx.dir, x))

# check that all gdxfiles exist
for(i in gdxpaths){
  if(!file.exists(i)){
    stop(paste0(i, " not found."))
  }
}

# pull out scenario names
scenario.names = names(gdxfiles)

# function for pulling gdx data ----
no_data = function(query){
  result = tryCatch(query,error = function(cond) { return(NULL) } )
  if(any(nrow(result) == 0, is.null(result))) {
    return(data.table(value = NA))
  }else{
    return(result)
  }
}

pull_gdx_data = function(type = c('param','set','variable'), gdx.name, r.name){

  if(type == 'param'){
    use.function = rgdx.param
  }else if(type == 'set'){
    use.function = rgdx.set
  }else if(type == 'variable'){
    use.function = rgdx.var.eq
  }
  
  assign(r.name, data.table(), envir = .GlobalEnv)
  
  for(i in names(gdxfiles)){
    assign(r.name,
           rbind(get(r.name), data.table(no_data(use.function(gdxpaths[i], gdx.name)),
                                         scenario = i), fill = T),
           envir = .GlobalEnv)
    if(anyNA(last(get(r.name)))){
      message(c("Warning: ", type," ",gdx.name," from ",gdxfiles[i]," returned no data"))
    }
  }
  
  message("data.table ", r.name, " created from ", type, " ", gdx.name)
}

re_name_cols = function(data){
  if(is.numeric(data[[1]])){
    message(c("Unexpected column order in ",deparse(substitute(data)), ". Columns not renamed." ))
  }else if(!(ncol(data) == length(col.names))){
    message(c("Unexpected number of columns in ", deparse(substitute(data)),". Columns not renamed. Check col.names."))
  }else{
    setnames(data, col.names)
  }
}

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
# load timeslices
ts.map = fread('data/ts_h_map_5szn.csv')
ts.map[,time_slice := factor(time_slice, levels = ts.map$time_slice)]

# create ordered factors for times and seasons
ts.map[, season_name := tstrsplit(time_slice, "_", fixed=T, keep=1)]
ts.map[, season := factor(season_name, levels = unique(season_name), 
                          labels = c('Dec - Jan','Feb - Mar','Apr - Jun','Jul - Sep','Oct - Nov'))]
ts.map[, time := tstrsplit(time_slice, "_", fixed=T, keep=2)]
ts.map[, time := factor(time, levels = unique(time))]

# load centroids
centroids = fread("data/state_population_centers.csv")
names(centroids) = c("State","x","y")
centroids[,State := gsub(" ","_",State)]
centroids[,State := gsub("_And","",State)]
centroids[,State := gsub("_and","",State)]
centroids[,State := gsub("Puducherry_Pondicherry","Puducherry", State)]
centroids = centroids[, lapply(.SD, mean), by=State, .SDcols=c("x","y") ]
centroids[,State := gsub("Orissa","Odisha",State)]

region.centroids = fread("data/region_centroids.csv")

# load contour data for maps
load("data/contours.Rdata")

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

cap.rs = cap.rs[names %in% c('WIND','UPV','DUPV'), .(value = sum(value)), by = .(names, names.2, names.3, scenario)]

names(cap.rs) = c('Technology','rs','Year','scenario','capacity')
cap.rs = merge(cap.rs, r.rs.map, by = 'rs', all.x = T)
setnames(cap.rs, 'r','State')
cap.rs[,rs := as.character(rs)]

#------------------------------#
# Firm capacity ----
#------------------------------#

pull_gdx_data(type = 'param', gdx.name = 'firm_conv', r.name = 'firm_conv')
pull_gdx_data(type = 'param', gdx.name = 'firm_hydro', r.name = 'firm_hydro')
pull_gdx_data(type = 'param', gdx.name = 'firm_vg', r.name = 'firm_vg')

firm_cap = rbind(firm_conv,firm_hydro)
firm_cap = rbind(firm_cap, firm_vg)

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
# Timeslice generation ----
#------------------------------#

pull_gdx_data(type = 'variable', gdx.name = 'GEN', r.name = 'tslc.gen')

col.names = c('Technology','type','State','Timeslice','Year','generation.MW','scenario')
re_name_cols(tslc.gen)

tslc.gen = merge(tslc.gen, hours, by.x = c('Timeslice','scenario'), by.y = c('h','scenario'))
tslc.gen[,generation := generation.MW*hours]

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
  col.names = c('Technology', 'type','State','Timeslice','Year','storage_in','scenario')
}
names(storage.in) = col.names

# Storage out
pull_gdx_data(type = 'variable', gdx.name = 'STORAGE_OUT', r.name = 'storage.out')

if(anyNA(storage.out)){
  col.names = c('storage_out','scenario','Technology','type','State','Timeslice','Year')
}else{
  col.names = c('Technology', 'type','State','Timeslice','Year','storage_out','scenario')
}
names(storage.out) = col.names

storage = merge(storage.in, storage.out, all=T)
storage = storage[!is.na(Year)]

rm(storage.in, storage.out)

# conver to MWh, multiply by no. hours per timeslice
storage = merge(storage, hours, by.x = c('Timeslice','scenario'), by.y = c('h','scenario'))
storage[,storage_in.MWh := storage_in*hours]
storage[,storage_out.MWh := storage_out*hours]

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
  
  #  prescr.rsc = prescr.rsc[!Technology %in% c('WIND','UPV','DUPV')]
  
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
inv.all[Technology %in% c('WIND','UPV','DUPV'), economic := inv.temp - prescribed]

inv.all[!(Technology %in% c('WIND','UPV','DUPV')), economic := inv.temp]
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
pull_gdx_data(type = 'param', gdx.name = 'trancap_exog', r.name = 'tx.cap')

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

col.names = c('r','Timeslice','Year','iteration','curtailment','scenario')
re_name_cols(curt_iter)

#write.table(curt_iter, 'data/curt_iter.csv',sep = ',', row.names = FALSE)

#------------------------------#
# Capacity Value Iterations ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'cc_iter', r.name = 'cc_iter')

col.names = c('Technology','r','season','Year','iteration','cap.value','scenario')
re_name_cols(cc_iter)

#write.table(cc_iter, 'data/cc_iter.csv',sep = ',', row.names = FALSE)

#------------------------------#
# Existing transmission between states ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'trancap_exog', r.name = 'tx.cap')


col.names = c('State.x','State.y','trtype','Year','cap','scenario')
re_name_cols(tx.cap)

#------------------------------#
# coal transport charge ----
#------------------------------#
pull_gdx_data(type = 'param', gdx.name = 'coal_transport', r.name = 'transport_charge')

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

#-------------------------------#
# Cut data on final year ----
#-------------------------------#

for(i in queries){
    if('Year' %in% names(get(i))){
      assign(i, get(i)[Year <= final.year,])
    }
}

#-------------------------------#
# Keep data only for focus regions
#-------------------------------#

for(i in queries[!grepl('contour',queries)]){
  if('State' %in% names(get(i)) & 'data.table' %in% class(get(i))){
    assign(i, get(i)[State %in% focus.regions,])
  }
}



