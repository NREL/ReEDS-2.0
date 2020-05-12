#----------------------------------------
# curtailment 
#---------------------------------------

calc_curtailment = function(aggregate.by = c("nation","region","state","year","timeslice"), 
                            type = c('capacity','energy')){

  # get actual RE generation (used to later calculate fraction curtailed)
  re.gen <- tslc.gen[Type %in% c('Solar-PV', 'Wind'), 
                     lapply(.SD, sum), by = c('Timeslice','State','scenario','Year'),
                     .SDcols = c('generation.MW','generation')]

    
  # combine actual and curtailed gen
  curtail <- merge(curt, re.gen, by.x = c('Timeslice','r','Year','scenario'), by.y = c('Timeslice','State','Year','scenario'), all = TRUE)
  curtail[,Type:= 'Curtailment']
  curtail[,'time_slice' := NULL]
  curtail <- merge(curtail, ts.map, by.x = 'Timeslice',by.y = 'h')
  curtail[is.na(curtail),] <- 0
  
  
  # calculate curtailed energy
  curtail <- merge(curtail, hours, by.x = c('Timeslice','scenario'), by.y = c('h','scenario'))
  curtail[,curt.mwh := curtailment*hours]  
  
  # add region map
  curtail <- merge(curtail, ba.set, by.x = c('r','scenario'),by.y = c('State','scenario'))
  
  
  if("nation" %in% aggregate.by){
    curtail <- curtail[,lapply(.SD, sum), by = c('scenario','Type','Year','time_slice'),
                             .SDcols = c('curtailment','curt.mwh','generation','generation.MW')]
 
    if("year" %in% aggregate.by){
      curtail <- curtail[,lapply(.SD, sum), by = c('scenario','Type','Year'),
                         .SDcols = c('curtailment','curt.mwh','generation','generation.MW')]
      
    }
    }
 
  if("region" %in% aggregate.by){
    curtail <- curtail[,lapply(.SD, sum), by = c('scenario','Type','Year','time_slice','region'),
                       .SDcols = c('curtailment','curt.mwh','generation','generation.MW')]
    
    if("year" %in% aggregate.by){
      curtail <- curtail[,lapply(.SD, sum), by = c('scenario','Type','Year','region'),
                         .SDcols = c('curtailment','curt.mwh','generation','generation.MW')]
      
    }
  }
  
  if("state" %in% aggregate.by){
    curtail <- curtail[,lapply(.SD, sum), by = c('scenario','Type','Year','time_slice','r'),
                       .SDcols = c('curtailment','curt.mwh','generation','generation.MW')]
    
    if("year" %in% aggregate.by){
      curtail <- curtail[,lapply(.SD, sum), by = c('scenario','Type','Year','r'),
                         .SDcols = c('curtailment','curt.mwh','generation','generation.MW')]
      
    }
  }
  
  if("capacity" %in% type){
  curtail[,fract.curt := curtailment/(generation.MW + curtailment)]
  curtail[,c('generation', 'curt.mwh'):= NULL]
  setnames(curtail, 'curtailment','V1')
  
  }
  
  if("energy" %in% type){
    curtail[,fract.curt := curt.mwh/(generation + curt.mwh)]
    curtail[,c('curtailment','generation.MW'):= NULL]
    setnames(curtail, 'curt.mwh','V1')
    
  }
  
  
  return.list = list(curtail = curtail)

  return(return.list)
}


#--------------------------#
# generation by year WITH CURTAILMENT----
#--------------------------#
plot_generation_curt = function(aggregate.by = c("nation","region")){
  
  year.min = min(tslc.gen$Year)
  year.max = max(tslc.gen$Year)

  if("nation" %in% aggregate.by){
    gen.india = tslc.gen[,sum(generation)/1000000, by = c('Type','Year', 'scenario')]
    
    # calculate curtailment
    curtail = calc_curtailment(aggregate.by = c('nation','year'), type = 'energy')
    cur.table <- curtail$curtail
    cur.table <- cur.table[,sum(V1)/1000000, by = c('Type','Year','scenario')]
    
    gen.india <- rbind(gen.india, cur.table[,.(Type, Year, scenario,V1)])
    
    # plot results - national
    p = ggplot(gen.india, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey10') +
      labs(y = 'Generation (TWh)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_wrap(~scenario)
    
    data = dcast(gen.india, Type+Year~scenario, value.var = "V1")
    
    gen.india[,total.gen := sum(V1), by = .(Year, scenario)]
    
    mix_data = gen.india[,.(gen.mix = V1/total.gen, Year, scenario, Type)]
    mix = copy(mix_data)
    mix[,gen.mix := round(gen.mix, digits = 2)]
    mix = dcast(mix, Type+Year~scenario, value.var = "gen.mix")
    
    return.list = list(data = data, plot = p, mix = mix, mix_data = mix_data)
    
    return(return.list)
    
  }
  
  if("region" %in% aggregate.by){
    
    # calculate curtailment
    curtail = calc_curtailment(aggregate.by = c('region','year'), type = 'energy')
    cur.table <- curtail$curtail
    cur.table <- cur.table[,sum(V1)/1000000, by = c('Type','Year','region','scenario')]
    
    gen.region= tslc.gen[,sum(generation)/1000000, by = c('Type','Year','region', 'scenario')]
    
    gen.region <- rbind(gen.region, cur.table[,.(Type, Year, scenario,region, V1)])
    
    # plot results - regional 
    p = ggplot(gen.region, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Generation (TWh)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 6)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(scenario~region)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}


#--------------------------#
# timeslice generation WITH CURTAILMENT----
#--------------------------#

plot_timeslice_generation_curt = function(aggregate.by = c("nation","region"), year = 'year.max',
                                     type = c('capacity','energy'),
                                     season.filter = c(), tslc.filter = c()){
  
  if(year == 'year.max'){
    year.max = tslc.gen[,max(Year)]
  }else{
    year.max = year
  }
  
  if(type == 'capacity'){
    tslc.gen[,value := generation.MW]
  }else if(type == 'energy'){
    tslc.gen[,value := generation]
  }
  
  # add storage discharge
  tot.gen = rbind(tslc.gen[Year == year.max],
                  storage[Year == year.max & !is.na(storage_out),
                          .(Timeslice,Technology,State,scenario,type,
                            Year,value = storage_out, region,
                            Type, season,time, time_slice)], fill = T)
  
  if(aggregate.by == "nation"){
    tslc.gen.india = tot.gen[, sum(value)/1000000, by = c('Type','season','time','scenario')]
    
    # calculate curtailment
    curt.type = type
    curtail = calc_curtailment(aggregate.by = c('nation','timeslice'), type = curt.type)
    cur.table <- curtail$curtail
    cur.table <- cur.table[Year == year.max,]
    cur.table = merge(cur.table, ts.map, by='time_slice')
    cur.table <- cur.table[, sum(V1)/1000000, by = c('Type','season','time','scenario','Year')]
    
    tslc.gen.india <- rbind(tslc.gen.india, cur.table[,.(Type,season,time,scenario,V1)])
    
    if(length(season.filter) > 0){
      tslc.gen.india = tslc.gen.india[season %in% season.filter]
    }
    
    # plot results - national
    p = ggplot(tslc.gen.india, aes(x = time, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey10') +
      labs(y = 'Generation (TW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) +
      facet_grid(scenario~season)
    
    return.list = list(plot = p)
    
    return(return.list)
    
  }
  
  if(aggregate.by == "region"){
    tslc.gen.region = tot.gen[Year == year.max, sum(value)/1000, by = c('Type','time_slice','season','scenario','region')]
    
    # calculate curtailment
    curt.type = type
    curtail = calc_curtailment(aggregate.by = c('region','timeslice'), type = curt.type)
    cur.table <- curtail$curtail
    cur.table <- cur.table[Year == year.max,]
    cur.table = merge(cur.table, ts.map, by='time_slice')
    cur.table <- cur.table[, sum(V1)/1000, by = c('Type','scenario','time_slice','season','Year','region')]
    
    tslc.gen.region <- rbind(tslc.gen.region, cur.table[,.(Type,time_slice,season,scenario,region,V1)])
    
    if(length(season.filter) > 0){
      tslc.gen.region = tslc.gen.region[season %in% season.filter]

    }
    if(length(tslc.filter) > 0){
      tslc.gen.region = tslc.gen.region[time_slice %in% tslc.filter]
    }
    
    # plot results - region
    p = ggplot(tslc.gen.region, aes(x = time_slice, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Generation (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) +
      facet_grid(region~scenario)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

 
#--------------------------#
# Curtailment Map----
#--------------------------#

# cloropleth map with capacity by scenario
map_curtailment = function(palette = c('Blues','BuGn','BuPu',
                                       'GnBu', 'Greens', 'Greys', 'Oranges',
                                       'OrRd', 'PuBu', 'PuBuGn', 'PuRd', 'Purples',
                                       'RdPu', 'Reds', 'YlGn', 'YlGnBu ', 'YlOrBr',
                                       'YlOrRd'),
                           year = final.year){
  
  
  # calculate curtailment
  cur.table = copy(curt)
  cur.table = merge(cur.table, hours, by.x=c('Timeslice','scenario'),by.y=c('h','scenario'))
  cur.table[, value := curtailment*hours]
  cur.table[,Type := 'Curtailment']
  
  # summarize year capacity by state
  final.curt = cur.table[Year == year]

  if(nrow(final.curt) == 0){
    return(paste0('No curtailment in ', final.year))
  }
  
  final.curt = final.curt[,sum(value)/1000000, by = c('scenario','Year','Type','State')]
  
  # fill in missing scenario, year, state combinations
  fill = CJ(scenario = scenario.names, Year = as.numeric(year), r = r.rs.map[,unique(r)])
  setnames(fill, 'r','State')
  
  final.curt = merge(final.curt, fill, by = c('scenario', 'Year','State'), all = T)
  final.curt[is.na(V1), V1 := 0]

  contour.reg = merge(contour.reg, final.curt, 
                   by.x = "NAME_1corr", by.y = "State", all.x = T,
                   allow.cartesian = T)
  
  category = 'Curtailment'
  
  # plot the map
  p = ggplot() +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.reg[!is.na(scenario)], aes(long, lat, group = group, fill = V1), 
                 color = "grey") +
    geom_path(data = contour.nat, aes(long, lat, group = group), color = 'grey10', size = 0.5) +
    scale_fill_gradient2(name = "Curtailment (TWh)",
                          midpoint = mean(range(contour.reg$V1, na.rm = T)),
                          low = "grey95", mid = "goldenrod2",
                          high = "firebrick",
                          guide = guide_legend(reverse = TRUE))  + 
    #scale_fill_manual("",values = gen.colors, drop = TRUE) +
    #geom_point(data = nodes, aes(X, Y), size = .5, color = "red") +
    coord_map() +
    theme_bw() +
    theme(axis.ticks = element_blank(), 
          axis.title = element_blank(), 
          axis.text = element_blank(),
          line = element_blank(),
          panel.border = element_blank()) 
  
  if(length(unique(contour.reg$Year))>1 & length(unique(contour.reg$scenario)) > 1){
    p = p + facet_grid(scenario~Year)
  }else if(length(unique(contour.reg$Year))>1){
    p = p + facet_wrap(~Year)
  }else if(length(unique(contour.reg$scenario))>1){
    p = p + facet_wrap(~scenario)
  }
  
  return(p)
  
}

#--------------------------#
# total system cost - combine variable costs and sum over entire model period ----
#--------------------------#

plot_system_costs_all = function(aggregate.by = c("nation"), year = final.year){
  

  if(aggregate.by == 'nation'){
    fuel = fuel.cost[Year <= year,
                     .(value = sum(fuelcost), type = "fuel"), by = .(scenario)]
    fom = fom.cost[Year <= year,
                   .(value = sum(fomcost), type = "fom"), by = .(scenario)]
    vom = vom.cost[Year <= year,
                   .(value = sum(vomcost), type = "vom"), by = .(scenario)]
    cap = cap.cost[Year <= year,
                   .(value = sum(capcost), type = "capacity"), by = .(scenario)]
    
    var = rbind(fom, vom)
    var <- var[,sum(value), by = .(scenario)]
    var[,type:= 'variable']
    setnames(var, 'V1','value')
    
    costs = rbindlist(list(fom, var, cap))
    
    
    costs[,type := factor(type, levels = c("variable", "fom", "capacity"))]
    
    
    p = ggplot(data = costs) +
      geom_bar(aes(x = scenario, y = value, fill = type), stat = 'identity') +
      labs(y = "Cost (INR)", x = NULL) +
      plot_theme +
      ggtitle('Total system cost') +
      scale_color_viridis(discrete = TRUE, option = 'D') +
      scale_fill_viridis(discrete = TRUE)
    
    return(p)
    
  }
  
  if(aggregate.by == 'region'){
    fuel = fuel.cost[Year <= year,
                     .(value = sum(fuelcost), type = "fuel"), by = .(scenario, region)]
    fom = fom.cost[Year <= year,
                   .(value = sum(fomcost), type = "fom"), by = .(scenario, region)]
    vom = vom.cost[Year <= year,
                   .(value = sum(vomcost), type = "vom"), by = .(scenario, region)]
    cap = cap.cost[Year <= year,
                   .(value = sum(capcost), type = "capacity"), by = .(scenario, region)]
    
    var = rbind(fom, vom)
    var <- var[,sum(value), by = .(scenario,region)]
    var[,type:= 'variable']
    setnames(var, 'V1','value')
    
    costs = rbindlist(list(fom, var, cap))
    
    costs[,type := factor(type, levels = c("variable","fom", "capacity"))]
    
    p = ggplot(data = costs) +
      geom_bar(aes(x = region, y = value, fill = type), stat = 'identity') +
      labs(y = "Cost (INR)", x = NULL) +
      plot_theme +
      ggtitle('Total system cost by region') +
      scale_color_viridis(discrete = TRUE, option = 'D') +
      scale_fill_viridis(discrete = TRUE) +
      facet_grid(~scenario)
    
    return(p)
    
  }
  
  if(aggregate.by == 'technology'){
    fuel = fuel.cost[Year <= year,
                     .(value = sum(fuelcost), type = "fuel"), by = .(scenario, Type)]
    fom = fom.cost[Year <= year,
                   .(value = sum(fomcost), type = "fom"), by = .(scenario, Type)]
    vom = vom.cost[Year <= year,
                   .(value = sum(vomcost), type = "vom"), by = .(scenario, Type)]
    cap = cap.cost[Year <= year,
                   .(value = sum(capcost), type = "capacity"), by = .(scenario, Type)]
    
    var = rbind(fom, vom)
    var <- var[,sum(value), by = .(scenario,Type)]
    var[,type:= 'variable']
    setnames(var, 'V1','value')
    
    costs = rbindlist(list(fom, var, cap))
    
    costs[,type := factor(type, levels = c("variable","fom", "capacity"))]
    
    p = ggplot(data = costs) +
      geom_bar(aes(x = Type, y = value, fill = type), stat = 'identity') +
      labs(y = "Cost (INR)", x = NULL) +
      plot_theme +
      ggtitle('Costs by technology') +
      scale_color_viridis(discrete = TRUE, option = 'D') +
      scale_fill_viridis(discrete = TRUE) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(~scenario)
    
    return(p)
    
  }
}

#--------------------------#
# Capacity as fraction of peak demand----
#--------------------------#

tab_cap_frac_peak = function(){
  
    year.min = min(cap$Year)
    year.max = max(cap$Year)
    
      cap.india = cap[,sum(capacity)/1000, by = c('Type','Year', 'scenario')]
      setnames(cap.india, 'V1','Capacity')
      
      pk = demand[,sum(demand)/1000, by = c('scenario','Year','Timeslice')]
      pk <- pk[,max(V1), by = c('scenario','Year')]
      setnames(pk, 'V1','Peak')
      
      pk.frac <- merge(cap.india, pk, by = c('scenario','Year'))
      pk.frac[,Frac.pk := Capacity/Peak]
      pk.frac[,Frac.pk := round(Frac.pk, digits = 2)]
      
      
      data = dcast.data.table(pk.frac, Type + Year ~ scenario, value.var = 'Frac.pk')
      
      return.list = list(data = data)
      
      return(return.list)
  
  
}

#----------------------------------------
# emissions 
#---------------------------------------

# emissions metric ton of CO2
# generation MWh
# emission.rate = metric ton co2/MWh

plot_emissions = function(category = c('Emissions','Emission.Rate'), year = final.year){  
  
  # create table with total generation and emissions
  emissions = gen[,sum(V1), by = .(State, scenario, Year, region)]
  setnames(emissions, 'V1', 'Generation')
  emissions <- merge(emissions, emit, by = c('State', 'scenario', 'Year', 'region'), all.x = TRUE)
  setnames(emissions, 'value','Emissions')
  
  # set rows with no emissions to 0
  emissions[is.na(emissions),] <- 0
  emissions[,Emission.Rate:= Emissions/Generation]
  
  # cloropleth map with capacity by scenario
  palette = c('Blues','BuGn','BuPu','GnBu', 'Greens', 'Greys', 'Oranges',
              'OrRd', 'PuBu', 'PuBuGn', 'PuRd', 'Purples','RdPu', 'Reds', 
              'YlGn', 'YlGnBu ', 'YlOrBr', 'YlOrRd')
  
  # remove 'TN_' where applicable. 
  #emissions$State <- gsub(".*TN_","",emissions$State)
  #emissions$State <- gsub("_"," ",emissions$State)
  
  contour.reg = merge(contour.reg, emissions, 
                      by.x = 'NAME_1corr', by.y = "State", all.x = T,
                      allow.cartesian = T)
  
  contour.reg.plot = contour.reg[year %in% final.year,]
  
  # plot the map
  p = ggplot() +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.reg.plot[!is.na(scenario)], aes(long, lat, group = group, fill = category), 
                 color = "grey") +
    geom_path(data = contour.nat, aes(long, lat, group = group), color = 'grey10', size = 0.5) +
    scale_fill_gradient2(name = "Metric ton CO2",
                         midpoint = mean(range(contour.reg.plot$Emissions, na.rm = T)),
                         low = "grey95", mid = "goldenrod2",
                         high = "firebrick",
                         guide = guide_colorbar(frame.colour = "black", ticks.colour = "black"))  + 
    #scale_fill_manual("",values = gen.colors, drop = TRUE) +
    #geom_point(data = nodes, aes(X, Y), size = .5, color = "red") +
    coord_map() +
    theme_bw() +
    theme(axis.ticks = element_blank(), 
          axis.title = element_blank(), 
          axis.text =  element_blank(),
          line = element_blank(),
          panel.border = element_blank()) +
    ggtitle(paste0(category, ' in Year ', final.year))
  
  if(length(unique(contour.reg.plot$Year))>1 & length(unique(contour.reg.plot$scenario)) > 1){
    p = p + facet_grid(scenario~Year)
  }else if(length(unique(contour.reg.plot$Year))>1){
    p = p + facet_wrap(~Year)
  }else if(length(unique(contour.reg.plot$scenario))>1){
    p = p + facet_wrap(~scenario)
  }
  
  return.list = list(plot = p, data = emissions)
  
}

#---------------------------#
# plot existing transmission ----
#--------------------------#

plot_tx_ex = function(){
  if(!"State.x" %in% names(tx.cap)){
    return(list(plot = NA, data = NA))
  }
  
  cap = tx.cap[Year == 2017,.(cap = sum(cap)), by = .(State.x, State.y, scenario)]
  
  cap[,State.x := gsub("_"," ",State.x)]
  cap[,State.y := gsub("_"," ",State.y)]
  
  cap = cap[order(cap,decreasing = F)]
  cap[,states := factor(paste(State.x,'-',State.y), levels = unique(paste(State.x,'-',State.y)))]
  
  p = ggplot(data = cap) +
    geom_bar(aes(x = states, y = cap/1000, fill = scenario), 
             stat = 'identity', position = 'dodge') +
    labs(x = NULL, y = "Transmission Capacity (GW)") +
    coord_flip() +
    plot_theme 
  
  data = tx.cap[,.(`State From` = State.x, `State To` = State.y,
                   Year, scenario, cap = round(cap, digits = 0))]
  
  data = dcast.data.table(data, `State From` + `State To` + Year ~ scenario,
                          value.var = 'cap')
  data = data[order(Year)]
  
  return.list = list(plot = p, data = data)
}

#---------------------------#
# existing transmission map ----
#--------------------------#

map_tx_ex = function(){
  if(!"State.x" %in% names(tx.cap)){
    return(NA)
  }
  
  # cap from
  cap = merge(tx.cap[Year == 2017,.(cap = sum(cap)), by = .(State.x,State.y,scenario)], 
              centroids, by.x = "State.x", by.y = "State")
  setnames(cap, c('x','y'), c('x.from','y.from'))
  
  # cap to
  cap = merge(cap, centroids, by.x = "State.y", by.y = "State")
  setnames(cap, c('x','y'), c('x.to','y.to'))
  
  # interleave data for mapping
  cap.from = cap[,.(State = State.x, x = x.from, y = y.from, cap, scenario)]
  
  cap.to = cap[,.(State = State.y, x = x.to, y = y.to, cap, scenario)]
  
  NA.rows = data.table(1:nrow(cap),
                       State = NA, x = NA, y = NA, cap = NA, scenario = NA)
  NA.rows = NA.rows[,-1]
  
  cap.interleave = gdata::interleave(cap.from, cap.to, NA.rows)
  cap.interleave[,scenario := zoo::na.locf(scenario)]
  cap.interleave = cap.interleave[-.N]
  
  # plot map of total transmission inv
  p = ggplot() +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.reg, aes(long, lat, group = group), 
                 fill = "grey95", color = 'grey50')  +
    geom_path(data = contour.nat, aes(long, lat, group = group), color = 'grey10', size = 0.5) +
    geom_path(data = cap.interleave, aes(x, y, color = cap), 
              size = .8) +
    scale_color_gradient2(name = "MW",
                          midpoint = mean(range(cap.interleave$cap, na.rm = T)),
                          low = "steelblue", mid = "goldenrod",
                          high = "firebrick",
                          guide = guide_colorbar(frame.colour = "black", ticks.colour = "black")) +
    coord_map() +
    theme_bw() +
    theme(axis.ticks = element_blank(), 
          axis.title = element_blank(), 
          axis.text =  element_blank(),
          line = element_blank(),
          panel.border = element_blank())
  
  return(p)
  
}

#--------------------------#
# planned capacity additions and retirements ----
#--------------------------#

plot_additions_retirements = function(){
  
  table = fread('data/cap_exog.csv', header = TRUE)
  
  cols <- copy(colnames(table[,3:ncol(table)]))
    
  table = melt(table, id.vars = 'Type', measure.var = cols, variable.name = 'Year', value.name = 'cap')
  table <- table[,sum(cap), by = c('Type','Year')]
  
  table[,Type := factor(Type, levels = c("Solar PV", "Wind", "Other", "Pumped hydro", "Hydro", "Gas CT","Diesel",
                                         "Gas CC","Super-Coal","Sub-Coal","Nuclear"))]
  
  
  # plot results 
  p = ggplot(table, aes(x = Year, y = V1/1000, group = Type, fill = Type)) + 
    geom_bar(position = 'stack', stat = 'identity', color = 'grey10') +
    labs(y = 'Change in installed capacity (GW)', x = NULL) +
    scale_fill_manual("",values = gen.colors, drop = TRUE) +
    plot_theme +
    scale_x_discrete(breaks=seq(2018,2047,3))
  
  p
  
  
}

#----------------------------------------
# firm capacity for a specified geographic region
#---------------------------------------
plot_firm_cap = function(years = c()){
  
  # capacity contribution from hydro
  cc.hydro = merge(cc_hydro, cap, by = c('Technology','State','scenario','Year','region','Type'))
  cc.hydro[,firm.cap:= value*capacity]
  cc.hydro = cc.hydro[,sum(firm.cap)/1000, by = c('scenario','Year','season','Type')]
  
  # capacity contribution from storage
  cc.stor = merge(cc_storage, cap, by = c('Technology','State','scenario','Year','region','Type'))
  cc.stor[,firm.cap:= value*capacity]
  cc.stor = cc.stor[,sum(firm.cap)/1000, by = c('scenario','Year','season','Type')]
  
  # capacity contribution from VRE
  cc.vre = merge(cc_re, cap.rs, by = c('Technology','State','scenario','rs','Year','region','Type'))
  cc.vre[,firm.cap := value*capacity]
  cc.vre = cc.vre[,sum(firm.cap)/1000, by = c('scenario','Year','season','Type')]
  
  # capacity contribution from conventional generators
  cc.conv = cap[!Type %in% c('Solar PV','Hydro','Pumped hydro','Wind'),sum(capacity)/1000, by = c('Year','Type','scenario')]
  # repeat for each season; conv gens have same CC for each season
  n = nrow(cc.conv)
  cc.conv = cc.conv[rep(seq_len(nrow(cc.conv)), length(unique(cc.vre$season))), ]
  szn = rep(unique(cc.vre$season), each = n)
  cc.conv[,season:= szn]
  
  # combine tables
  table = rbind(cc.hydro, cc.stor, cc.vre, cc.conv)
  
  # add demand dots
  demand_st = demand[Year %in% years & time == 'peak',.(demand = sum(demand)/1000), by = .(season, Year, scenario)]
  
  prm_req = demand_st[,.(season, Year, scenario, prm_req = demand*1.15)]
  
  
  p = ggplot() + 
    geom_bar(data = table[Year %in% years], aes(x=season, y=V1, group = Type, fill = Type), position = 'stack', stat = 'identity', color = 'grey10') +
    geom_point(data=demand_st[Year %in% years], aes(x=season,y=demand)) +
    geom_point(data=prm_req[Year %in% years], aes(x=season,y=prm_req), color = 'red') +
    labs(y='Firm Capacity (GW)',x = NULL) +
    scale_fill_manual("",values = gen.colors, drop = TRUE) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
    plot_theme +
    facet_wrap(~Year)
  
  p
  
  return.list = list(data = table, plot = p)
  
  return(return.list)
}
