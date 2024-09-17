#--------------------------#
# installed capacity by year ----
#--------------------------#

plot_cap_by_year = function(aggregate.by = c("nation","region","state"), state.filter = c(), years = c(),
                            scenario_filter = c(), type.filter = c(), tech.filter = c()){
  
  year.min = min(cap$Year)
  year.max = max(cap$Year)
  
  if(length(years)>0){
    plot.years = years
  }else{
    years = unique(cap$Year)
  }
  
  if(length(tech.filter)>0){
    cap.data = cap[grepl(tech.filter, Technology)]
  }else{
    cap.data = copy(cap)
  }
  
  if("nation" == aggregate.by){
    cap.india = cap.data[Year %in% years, sum(capacity)/1000, by = c('Type','Year','scenario')]
    
    if(length(scenario_filter)>0){
      cap.india = cap.india[scenario %in% scenario_filter]
    }
    
    if(length(type.filter)>0){
      cap.india = cap.india[grepl(type.filter, Type)]
    }
    
    # plot results - national
    p = ggplot(cap.india, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey20', size = 0.05) +
      labs(y = 'Installed capacity (GW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 4)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_wrap(~scenario)
    
    data = dcast.data.table(cap.india, Type + Year ~ scenario, value.var = 'V1')
      
    return.list = list(data = data, plot = p)
    
    return(return.list)

  }
  
  if("region"==aggregate.by){
    cap.region= cap[,sum(capacity)/1000, by = c('Type','Year','region', 'scenario')]
    
    if(length(scenario_filter)>0){
      cap.region = cap.region[scenario %in% scenario_filter]
    }
    
    # plot results - regional 
    p = ggplot(cap.region, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey10') +
      labs(y = 'Installed capacity (GW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(region~scenario, scales = 'free_y')
    
    return.list = list(data = cap.region, plot = p)
  
   return(return.list)
  }
  
  
  if("state" == aggregate.by){
    cap.state= cap[,sum(capacity)/1000, by = c('Type','Year','State', 'scenario')]
    
    if(length(state.filter) > 0){
      cap.state = cap.state[State %in% state.filter]
    }
    
    # plot results - regional 
    p = ggplot(cap.state, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey10') +
      labs(y = 'Installed capacity (GW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(State~scenario, scales = 'free_y')
    
    return.list = list(data = cap.state, plot = p)
    
    return(return.list)
  }

}

#--------------------------#
# capacity mix by year ----
#--------------------------#

plot_cap_mix = function(aggregate.by = c("nation","region","state"), state.filter = c(), years = c(),
                        scenario_filter = c()){
  
  year.min = min(cap$Year)
  year.max = max(cap$Year)
  
  if(length(years)>0){
    plot.years = years
  }else{
    years = unique(cap$Year)
  }
  
  if("nation" == aggregate.by){
    cap.india = cap[Year %in% years, sum(capacity)/1000, by = c('Type','Year', 'scenario')]
    cap.india[, tot := sum(V1), by = .(Year,scenario)]
    cap.india[, mix := V1/tot, by = .(Type,Year,scenario)]
    cap.india[,V1 := NULL]
    
    if(length(scenario_filter)>0){
      cap.india = cap.india[scenario %in% scenario_filter]
    }
    
    # plot results - national
    p = ggplot(data = cap.india) + 
      geom_area(aes(x=Year,y=mix,fill=Type), color = 'grey20') +
      labs(y = 'Capacity mix (%)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min-1, year.max, 2),expand = c(0,0)) +
      scale_y_continuous(labels = scales::percent, expand = c(0,0)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_wrap(~scenario)
    
    data = dcast.data.table(cap.india, Type + Year ~ scenario, value.var = 'mix')
    
    return.list = list(data = data, plot = p)
    
    return(return.list)
    
  }
  
}

#--------------------------#
# installed capacity by year ----
#--------------------------#

plot_cap_by_year_demand = function(aggregate.by = c("nation","region")){
  
  year.min = min(cap$Year)
  year.max = max(cap$Year)
  
  if("nation" %in% aggregate.by){
    cap.india = cap[,sum(capacity)/1000, by = c('Type','Year', 'scenario')]
    
    # plot results - national
    p = ggplot(cap.india, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_area(position = 'stack') +
      geom_line(data = peak.demand, aes(x = Year, y = demand/1000, color = demand), inherit.aes = F) +
      labs(y = 'Installed capacity (GW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min-1, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_wrap(~scenario)
    
    data = dcast.data.table(cap.india, Type + Year ~ scenario, value.var = 'V1')
    
    return.list = list(data = data, plot = p)
    
    return(return.list)
    
  }
  
  if("region" %in% aggregate.by){
    cap.region= cap[,sum(capacity)/1000, by = c('Type','Year','region', 'scenario')]
    
    # plot results - regional 
    p = ggplot(cap.region, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_area(position = 'stack') +
      labs(y = 'Installed capacity (GW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 6)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(scenario~region)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

#------------------#
# Firm Capacity #----
#------------------#
plot_firm_capacity = function(aggregate.by = 'nation', years = c(), state.filter = c(), tech.filter = c(),
                              scenario_filter = c(), type.filter = c()){
  if(aggregate.by == 'nation'){
    firmcap_nat = firm_cap[,.(firmcap = sum(firm_capacity)/1000), by = .(Type,Year,season, scenario)]
    
    demand_nat = demand[time == 'peak',.(demand = sum(demand)/1000), by = .(season, Year, scenario)]
    
    prm_req = demand_nat[,.(season, Year, scenario, prm_req = demand*1.15)]
    
    if(length(scenario_filter)>0){
      firmcap_nat = firmcap_nat[scenario %in% scenario_filter]
      demand_nat = demand_nat[scenario %in% scenario_filter]
      prm_req = prm_req[scenario %in% scenario_filter]
    }
    
    if(length(years) == 0){
    years = tail(sort(unique(firmcap_nat$Year)))
    }
    
    if(length(type.filter) > 0){
      firmcap_nat = firmcap_nat[grepl(type.filter, Type)]
      prm_req = prm_req[Year == 0]
      demand_nat = demand_nat[Year == 0]
    }
    
    p = ggplot() + 
      geom_bar(data=firmcap_nat[Year %in% years], aes(x=season, y=firmcap, fill=Type), stat='identity') +
      geom_point(data=demand_nat[Year %in% years], aes(x=season,y=demand)) +
      geom_point(data=prm_req[Year %in% years], aes(x=season,y=prm_req), color = 'red') +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      labs(x = NULL, y = "Capacity contribution to\nplanning reserve margin (GW)") +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme 
    
    if(length(firmcap_nat[,unique(scenario)])==1){
      p = p + facet_grid(.~Year)
    }else{
      p = p + facet_grid(scenario~Year)
    }
    
    data = firmcap_nat
  }
  
  if(aggregate.by == 'region'){
    years = max(firm_cap$Year)
    
    firmcap_reg = firm_cap[,.(firmcap = sum(firm_capacity)/1000), by = .(Type,Year,season, scenario, region)]
    
    demand_reg = demand[time == 'peak',.(demand = sum(demand)/1000), by = .(season, Year, scenario, region)]
    
    prm_req_reg = demand_reg[,.(season, Year, scenario, region, prm_req = demand*1.15)]
    
    p = ggplot() + 
      geom_bar(data=firmcap_reg[Year %in% years], aes(x=season, y=firmcap, fill=Type), stat='identity') +
      geom_point(data=demand_reg[Year %in% years], aes(x=season,y=demand)) +
      geom_point(data=prm_req_reg[Year %in% years], aes(x=season,y=prm_req), color = 'red') +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme 
    
    if(length(names(solutions))==1){
      p = p + facet_grid(region~Year, scales = 'free_y')
    }else{
      p = p + facet_grid(region~Year+scenario, scales = 'free_y')
    }
    
    data = firmcap_reg
  }
  
  if(aggregate.by == 'state'){
    years = max(firm_cap$Year)
    
    firmcap_st = tslc.gen[Type == 'Wind',.(firmcap = sum(generation.MW)), by = .(Type, Year,season,time, scenario, State)]
    firmcap_st = merge(firmcap_st, cap, by = c('Type','State','scenario','Year'))
    
    firmcap_st[,CF := firmcap/capacity]
    
    # demand_st = demand[time == 'peak',.(demand = sum(demand),region), by = .(season, Year, scenario, State)]
    # demand_region = demand[time == 'peak',.(demand_reg = sum(demand)), by =.(season, Year, scenario, region)]
    # 
    # demand_st = merge(demand_st, demand_region,  by = c('region','scenario','Year','season') )
    # demand_st[,demand_perc := demand/demand_reg]
    # 
    if(length(state.filter)>0){
      firmcap_st = firmcap_st[State %in% state.filter]
      # demand_st = demand_st[State %in% state.filter]
    }
    
    p = ggplot() + 
      geom_bar(data=firmcap_st[Year %in% years], aes(x=season, y=CF, fill=State), stat='identity', position = 'dodge') +
      # geom_point(data=demand_st[Year %in% years], aes(x=season,y=demand_perc)) +
      #geom_point(data=prm_req_st[Year %in% years], aes(x=season,y=prm_req), color = 'red') +
      #scale_fill_manual("",values = gen.colors, drop = TRUE) +
      labs(y='State average wind CF during peak',x = NULL)
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme 
    
    if(length(names(solutions))==1){
      p = p + facet_grid(time~Year)
    }else{
      p = p + facet_grid(State~Year+scenario, scales = 'free_y')
    }
    
    data = firmcap_st
  }
  return_list = list(plot = p, data = data)
  return(return_list)
}

#------------------#
# Firm Capacity #----
#------------------#
plot_capacity_credit = function(aggregate.by = 'nation', years = c(), state.filter = c(), tech.filter = c(),
                              scenario_filter = c(), type.filter = c()){
  if(aggregate.by == 'nation'){
    firmcap_nat = firm_cap[,.(firmcap = sum(firm_capacity)/1000), by = .(Type,Year,season, scenario)]
    
    cap_nat = cap[,.(cap = sum(capacity)/1000), by = .(Type,Year,scenario)]
    
    cc = merge(firmcap_nat, cap_nat)
    cc[,cc := firmcap/cap]
    
    if(length(scenario_filter)>0){
      cc = cc[scenario %in% scenario_filter]
    }
    
    if(length(years) == 0){
      years = tail(sort(unique(firmcap_nat$Year)))
    }
    
    if(length(type.filter) > 0){
      cc = cc[grepl(type.filter, Type)]
    }
    
    p = ggplot() + 
      geom_bar(data=cc[Year %in% years], aes(x=season, y=cc, fill=Type), stat='identity',position = 'dodge') +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      labs(x = NULL, y = "Capacity credit") +
      scale_y_continuous(labels = scales::percent) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme 
    
    if(length(cc[,unique(scenario)])==1){
      p = p + facet_grid(.~Year)
    }else{
      p = p + facet_grid(scenario~Year)
    }
    
    data = cc
  }
  
  return_list = list(plot = p, data = data)
  return(return_list)
}

#------------------#
# Firm Capacity #----
#------------------#
plot_cc_years = function(aggregate.by = 'nation', state.filter = c(), tech.filter = c(),
                                scenario_filter = c(), type.filter = c()){
  if(aggregate.by == 'nation'){
    firmcap_nat = firm_cap[,.(firmcap = sum(firm_capacity)/1000), by = .(Type,Year,season, scenario)]
    
    cap_nat = cap[,.(cap = sum(capacity)/1000), by = .(Type,Year,scenario)]
    
    cc = merge(firmcap_nat, cap_nat)
    cc[,cc := firmcap/cap]
    
    cc = cc[,.(cc = mean(cc)), by = .(Type, Year, scenario)]
    
    if(length(scenario_filter)>0){
      cc = cc[scenario %in% scenario_filter]
    }
    
    if(length(type.filter) > 0){
      cc = cc[grepl(type.filter, Type)]
    }
    
    p = ggplot() + 
      geom_line(data=cc, aes(x=Year, y=cc, color=Type), size = 1.5) +
      scale_color_manual("",values = gen.colors, drop = TRUE) +
      labs(x = NULL, y = "Capacity credit") +
      scale_y_continuous(labels = scales::percent_format(accuracy = 1)) +
      plot_theme 
    
    if(length(cc[,unique(scenario)])==1){
      p = p 
    }else{
      p = p + facet_grid(scenario~.)
    }
    
    data = cc
  }
  
  return_list = list(plot = p, data = data)
  return(return_list)
}


#--------------------------#
# new capacity by year ----
#--------------------------#

plot_new_capacity = function(aggregate.by = c("nation","region"), scenario_filter = c()){
  
  year.min = min(inv.all$Year)
  year.max = max(inv.all$Year)
  
  type.color = c('Economic' = 'grey10', 'Prescribed' = 'red' )
  
  if("nation" %in% aggregate.by){
    inv.all.india = inv.all[,sum(investments)/1000, by = c('Type','Year', 'scenario','type')]
    inv.all.india = inv.all.india[V1 >= 0]
    
    if(length(scenario_filter)>0){
      inv.all.india = inv.all.india[scenario %in% scenario_filter]
    }
    
    # plot results - national
    p = ggplot(inv.all.india, aes(x = Year, y = V1, group = Type, 
                                  fill = Type, color = type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'New capacity (GW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      scale_color_manual("",values = type.color) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme +
      facet_wrap(~scenario)
    
    data = dcast(inv.all.india, Type~Year+scenario+type, value.var = "V1")
    
    return.list = list(data = data, plot = p)
    
    return(return.list)
    
  }
  
  if("region" %in% aggregate.by){
    inv.all.region= inv.all[,sum(investments)/1000, by = c('Type','Year','region', 'scenario')]
    
    if(length(scenario_filter)>0){
      inv.all.region = inv.all.region[scenario %in% scenario_filter]
    }
    
    # plot results - regional 
    p = ggplot(inv.all.region, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey10') +
      labs(y = 'New capacity (GW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 6)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme +
      facet_grid(scenario~region)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

#--------------------------#
# new capacity difference ----
#--------------------------#

plot_new_capacity_diff = function(aggregate.by = c("nation","region"), scenario_filter = c()){
  if(length(solutions) < 2){
    return()
  }

  year.min = min(inv.all$Year)
  year.max = max(inv.all$Year)
  
  ref.scenario = names(solutions[1])
  
  # calculate difference from reference scenario
  inv.all.cast = dcast.data.table(inv.all, Technology + Type + Year + State + region + type ~ scenario,
                       value.var = "investments")
  
  for(i in names(inv.all.cast)){
    inv.all.cast[is.na(get(i)), (i) := 0]
  }
  
  for(i in names(solutions)[!names(solutions) == ref.scenario]){
    inv.all.cast[, (i) := get(i) - get(ref.scenario)]
  }
  
  inv.diff = melt(inv.all.cast, id.vars = c("Technology", "Type", "Year", "State", "region", "type"), 
                 variable.name = "scenario", value.name = "difference")
  
  inv.diff = inv.diff[!(scenario == ref.scenario)]
  
  if(length(scenario_filter)>0){
    inv.diff = inv.diff[scenario %in% scenario_filter]
  }

  if("nation" %in% aggregate.by){
    inv.diff.india = inv.diff[,sum(difference)/1000, by = c('Type','Year', 'scenario','type')]
    
    # plot results - national
    p = ggplot(inv.diff.india, aes(x = Year, y = V1, group = Type, 
                                   fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey10') +
      labs(y = 'Difference from reference scenario (GW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 4)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme +
      facet_wrap(~scenario)
    
    data = dcast(inv.diff.india, Type~Year+scenario+type, value.var = "V1")
    
    return.list = list(data = data, plot = p)
    
    return(return.list)
    
  }
  
  if("region" %in% aggregate.by){
    inv.diff.region= inv.diff[,sum(investments)/1000, by = c('Type','Year','region', 'scenario')]
    
    # plot results - regional 
    p = ggplot(inv.diff.region, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'New capacity (GW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min, year.max, 6)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme +
      facet_grid(scenario~region)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

plot_final_cap_diff = function(aggregate.by = c("nation","region"), scenario_filter = c(), years = final.year,
                               type.filter = c()){
  if(length(solutions) < 2){
    return()
  }
  
  ref.scenario = names(solutions[1])
  
  # calculate difference from reference scenario
  cap.cast = dcast.data.table(cap[Year %in% years], Technology + Type + Year + State + region ~ scenario,
                                value.var = "capacity")
  
  for(i in names(cap.cast)){
    cap.cast[is.na(get(i)), (i) := 0]
  }
  
  for(i in names(solutions)[!names(solutions) == ref.scenario]){
    cap.cast[, (i) := get(i) - get(ref.scenario)]
  }
  
  cap.diff = melt(cap.cast, id.vars = c("Technology", "Type", "Year", "State", "region"), 
                  variable.name = "scenario", value.name = "difference")
  
  # only keep years that are shared by all scenarios
  # minyrs = cap[,length(unique(Year)), by=scenario]
  # yrs = cap[scenario == minyrs[V1==min(V1), scenario], unique(Year)]
  # cap.diff = cap.diff[Year %in% yrs]
  
  cap.diff = cap.diff[!(scenario == ref.scenario)]
  
  if(length(scenario_filter)>0){
    cap.diff = cap.diff[scenario %in% scenario_filter]
  }
  
  if(length(type.filter)>0){
    cap.diff = cap.diff[Type %in% type.filter]
  }
  
  
  if("nation" %in% aggregate.by){
    cap.diff.india = cap.diff[,sum(difference)/1000, by = c('Type','Year', 'scenario')]
    
    # plot results - national
    p = ggplot(cap.diff.india, aes(x = Year, y = V1, group = Type, 
                                   fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey10') +
      labs(y = 'Difference from reference scenario (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme +
      facet_wrap(~scenario)
    
    data = dcast(cap.diff.india, Type~Year+scenario, value.var = "V1")
    
    return.list = list(data = data, plot = p)
    
    return(return.list)
    
  }
  
  if("region" %in% aggregate.by){
    cap.diff.region= cap.diff[,sum(difference)/1000, by = c('Type','Year','region', 'scenario')]
    
    # plot results - regional 
    p = ggplot(cap.diff.region, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Difference from reference scenario (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      plot_theme +
      facet_grid(scenario~region)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

#--------------------------#
# retirements by year ----
#--------------------------#

plot_retirements = function(aggregate.by = c("nation","region")){
  
  year.min = min(retire$Year)
  year.max = max(retire$Year)
  
  if("nation" %in% aggregate.by){
    retire.india = retire[,sum(retire), by = c('Type','Year','scenario','type')]
    
    # plot results - national
    p = ggplot(retire.india, aes(x = Year, y = V1, group = Type, 
                                 fill = Type, color = type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Retirements (MW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min-1, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_wrap(~scenario)
    
    data = dcast.data.table(retire.india, Type + Year + type ~ scenario, value.var = 'V1')
    
    return.list = list(data = data, plot = p)
    
    return(return.list)
    
  }
  
  if("region" %in% aggregate.by){
    retire.region = retire[,sum(retire), by = c('Type','Year','scenario','type','region')]
    
    # plot results - national
    p = ggplot(retire.region, aes(x = Year, y = V1, group = Type, 
                                 fill = Type, color = type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Retirements (MW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min-1, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(region~scenario)
    
    return(p)
  }
  
}

#--------------------------#
# refurbishments by year ----
#--------------------------#

plot_refurbs = function(aggregate.by = c("nation","region")){
  
  year.min = min(cap$Year)
  year.max = max(cap$Year)
  
  if("nation" %in% aggregate.by){
    refurb.india = refurb[,sum(refurb), by = c('Type','Year','scenario')]
    all.yrs = expand.grid(seq(from=year.min,to=year.max, by = 1),
                          unique(refurb.india$scenario),
                          unique(refurb.india$Type))
    names(all.yrs) = c("Year","scenario","Type")
    refurb.india = merge(refurb.india, all.yrs, all = T)
    refurb.india[is.na(V1), V1 := 0]
    
    # plot results - national
    p = ggplot(refurb.india, aes(x = Year, y = V1, group = Type, 
                                 fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Refurbishments (MW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min-1, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_wrap(~scenario)
    
    data = dcast.data.table(refurb.india, Type + Year ~ scenario, value.var = 'V1')
    
    return.list = list(data = data, plot = p)
    
    return(return.list)
    
  }
  
  if("region" %in% aggregate.by){
    refurb.region = refurb[,sum(refurb), by = c('Type','Year','scenario','type','region')]
    
    # plot results - national
    p = ggplot(refurb.region, aes(x = Year, y = V1, group = Type, 
                               fill = Type, color = type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'refurbments (MW)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min-1, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(region~scenario)
    
    return(p)
  }
  
}

#--------------------------#
# generation by year ----
#--------------------------#
plot_generation = function(aggregate.by = c("nation","region"), type.filter = c(),
                           plot_curt = TRUE, scenario_filter = c()){
  
  year.min = min(tslc.gen$Year)
  year.max = max(tslc.gen$Year)
  
  if("nation" %in% aggregate.by){
    gen.india = tslc.gen[!grepl('BESS',Type),sum(generation)/1000000, by = c('Type','Year', 'scenario')]
    
    if(length(type.filter)>0){
      gen.india = gen.india[Type %in% type.filter]
    }
    
    if("curtailment" %in% names(curt) & plot_curt == TRUE){
      curtail = copy(curt)
      setnames(curtail, "curtailment", "generation.MW")
      curtail[,Type := "Curtailment"]
     
      # calculate energy curtailment
      curtail = merge(curtail, hours, by.x = c('Timeslice', 'scenario'), by.y = c('h','scenario'))
      curtail[,value := generation.MW * hours]
      curtail = curtail[,sum(value)/1000000, by = c('Type','Year','scenario')]
      
      gen.india = rbind(gen.india, curtail, fill = T)
    }
    
    if(length(scenario_filter) > 0){
      gen.india = gen.india[scenario %in% scenario_filter]
    }
    
    # plot results - national
    p = ggplot(gen.india, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey20') +
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
    gen.region= tslc.gen[,sum(generation)/1000000, by = c('Type','Year','region', 'scenario')]
  
    if(length(scenario_filter) > 0){
      gen.region = gen.region[scenario %in% scenario_filter]
    }

    if("curtailment" %in% names(curt) & plot_curt == TRUE){
      curtail = copy(curt)
      setnames(curtail, "curtailment", "generation.MW")
      curtail[,Type := "Curtailment"]
     
      # calculate energy curtailment
      curtail = merge(curtail, hours, by.x = c('Timeslice', 'scenario'), by.y = c('h','scenario'))
      curtail[,value := generation.MW * hours]
      curtail = curtail[,sum(value)/1000000, by = c('Type','Year','region','scenario')]
      
      gen.india = rbind(gen.india, curtail, fill = T)
    }
    
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
# storage operations ----
#--------------------------#

plot_storage_ops = function(aggregate.by = c("nation","region"), year = 'year.max',select_state=c(), ops = 'all'){
  
  if(year == 'year.max'){
    year.max = storage[,max(Year)]
  }else{
    year.max = year
  }
  
  storage.data = copy(storage)
  
  if(length(select_state)>0){
    storage.data = storage[State %in% select_state]
  }
  
  if(aggregate.by == "nation"){
    storage.india = storage.data[Year == year.max, .(IN = sum(storage_in)/1000,
                                                GEN = sum(storage_gen)/1000,
                                                LEVEL = sum(storage_level)/1000),
                            by = c('Type','time','season','scenario')]
    
    storage.india = melt(storage.india, 
                         id.vars = c('Type', 'time','season','scenario'))
    storage.india[is.na(value), value := 0]

    if(ops == 'all'){
      # plot results - national
      p = ggplot(storage.india, aes(x = time, y = value, group = Type, fill = Type)) + 
        geom_bar(position = 'stack', stat = 'identity') +
        labs(y = 'Storage variables (GW)', x = NULL) +
        scale_fill_manual("",values = gen.colors, drop = TRUE) +
        plot_theme +
        theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) +
        facet_grid(variable~season)
      
      return.list = list(plot = p)
      
      return(return.list)
    }else{
      # plot results - only STORAGE_IN and STORAGE_OUT
      storage.india = storage.india[variable != 'LEVEL']
      storage.india[variable == 'IN', value := value*-1]
      p = ggplot(storage.india, aes(x = time, y = value, group = Type, fill = Type)) + 
        geom_bar(position = 'stack', stat = 'identity', color = 'grey20') +
        labs(y = 'Storage charging\nand discharging (GW)', x = NULL) +
        scale_fill_manual("",values = gen.colors, drop = TRUE) +
        plot_theme +
        theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) +
        facet_wrap(~season)

      return.list = list(plot = p)
      
      return(return.list)
    }
    
  }
  
  if(aggregate.by == "region"){
    storage.region = storage[Year == year.max, .(IN = sum(storage_in)/1000,
                                                OUT = -sum(storage_out)/1000),
                            by = c('Type','time_slice','scenario','region')]
    
    storage.region = melt(storage.region, 
                         id.vars = c('Type', 'time_slice','scenario','region'))
    storage.region[is.na(value), value := 0]
    
    # plot results - national
    p = ggplot(storage.region, aes(x = time_slice, y = value, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Charging (>0) and discharging (<0) (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
      facet_grid(scenario~.)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

#--------------------------#
# storage sdbins ----
#--------------------------#

plot_sdbin = function(){
  sdbin_cap_india = sdbin_cap[,.(cap=sum(cap)), by = .(Type, Year, sdbin, scenario, season)]
  
  sdbin_size_india = sdbin_size[,.(sdbin_size = sum(sdbin_size)), by = .(sdbin, Year, scenario, season)]
  
  sdbin_cap_india = merge(sdbin_cap_india, sdbin_size_india, all = T)
  sdbin_cap_india = merge(sdbin_cap_india, cc_storage, by = c('Type','sdbin','scenario'), all = T)
  
  p = ggplot(sdbin_cap_india[Year == 2040]) +
    geom_bar(aes(x=sdbin, y=cap, fill = Type), stat = 'identity') +
    #geom_point(aes(x=sdbin, y=sdbin_size)) +
    facet_grid(~season)
  
  
}



#--------------------------#
# timeslice generation ----
#--------------------------#

plot_timeslice_generation = function(aggregate.by = c("nation","region","state"), year = final.year,
                                     type = c('capacity','energy'), scenario_filter = c(),
                                     state_filter = c()){
  
  if(year == final.year){
    year.max = tslc.gen[,max(Year)]
  }else{
    year.max = year
  }
  
  if(type == 'capacity'){
    tslc.gen[,value := generation.MW]

    tot.load = demand[Year == year.max, .(value = sum(demand)), 
                      by = .(Year, State, region, scenario, season, time, time_slice)]
    
  }else if(type == 'energy'){
    tslc.gen[,value := generation]
      
    tot.load = demand[Year == year.max, .(value = sum(demand)), 
                      by = .(Year, State, scenario, season, time, Timeslice, time_slice)]
    tot.load = merge(tot.load, hours, by.x=c('scenario','Timeslice'), by.y=c('scenario','h'))
    tot.load[, value := value*hours]
  }

   tot.gen = tslc.gen[Year == year.max]
  #                 storage[Year == year.max & !is.na(storage_out),
  #                         .(Timeslice,Technology,State,scenario,type,
  #                           Year,value = storage_out, region,
  #                           Type,time_slice, season_name, season,time)], fill = T)
  
  # add curtailment if it exists
  if("curtailment" %in% names(curt)){
    curtail = copy(curt)
    setnames(curtail, "curtailment", "generation.MW")
    curtail[,Type := "Curtailment"]
    # calculate energy curtailment
    curtail = merge(curtail, hours, by.x = c('Timeslice','scenario'), by.y = c('h','scenario'))
    curtail[,generation := generation.MW * hours]
    
    if(type == 'capacity'){
      curtail[,value := generation.MW]
    }else if(type == 'energy'){
      curtail[,value := generation]
    }
    
    curtail = curtail[Year == year.max]
    
    tot.gen = rbind(tot.gen, curtail, fill = T)
  }
  
  if(aggregate.by == "nation"){
    tslc.gen.india = tot.gen[, sum(value)/1000, by = c('Type','time','season','scenario')]
    load.india = tot.load[, .(value=sum(value)/1000), by = c('time','season','scenario')]
    
    if(length(scenario_filter) > 0){
     tslc.gen.india = tslc.gen.india[scenario %in% scenario_filter]
     load.india = load.india[scenario %in% scenario_filter]
    }
    
    # plot results - national
    p = ggplot(tslc.gen.india, aes(x = time, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity', color = 'grey10') +
      labs(y = 'Generation (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      geom_point(data = load.india, aes(x=time, y=value, shape="Demand"), inherit.aes = F) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5))   
    
    if(length(unique(as.character(tslc.gen.india$scenario)))==1){
      p = p + facet_grid(.~season)
    }
    if(length(unique(as.character(tslc.gen.india$scenario)))>1){
      p = p + facet_grid(scenario~season)
    }
    
    return.list = list(plot = p)
    
    return(return.list)
    
  }
  
  if(aggregate.by == "region"){
    tslc.gen.region = tot.gen[Year == year.max, sum(value)/1000, by = c('Type','time_slice','scenario','region')]
    load.region = tot.load[Year == year.max, .(value=sum(value)/1000), by = c('time_slice','scenario','region')]
    
    # plot results - regional
    p = ggplot(tslc.gen.region, aes(x = time_slice, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Generation (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      geom_point(data = load.region, aes(x=time_slice, y=value, shape="Demand"), inherit.aes = F) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(region~scenario, scales = 'free_y')
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
  if(aggregate.by == "state"){
    tslc.gen.state = tot.gen[Year == year.max, sum(value)/1000, by = c('Type','time','season','scenario','State')]
    load.state = tot.load[Year == year.max, .(value=sum(value)/1000), by = c('time','season','scenario','State')]
    
    if(length(state_filter)>0){
      tslc.gen.state = tslc.gen.state[State %in% state_filter]
      load.state = load.state[State %in% state_filter]
    }
    
    # plot results - state
    p = ggplot(tslc.gen.state, aes(x = time, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Generation (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      geom_point(data = load.state, aes(x=time, y=value, shape="Demand"), inherit.aes = F) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(State~season, scales = 'free_y')
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

#--------------------------#
# Curtailment by iteration ----
#--------------------------#

plot_curt_iter = function(){
  curt_timeslice = curt_iter[,.(curtailment = mean(curtailment)*100), by = .(time,season,iteration,scenario)]
  
  curt_year = curt_iter[,.(curtailment = mean(curtailment)*100), by = .(Year,iteration,scenario)]
  
  curt_region = curt_iter[,.(curtailment = mean(curtailment)*100), by = .(r,iteration,scenario)]
  
  p.timeslice = ggplot(curt_timeslice) +
    geom_bar(aes(x=time, y=curtailment, fill = iteration), stat='identity', position = 'dodge') +
    plot_theme +
    labs(x=NULL,y='Average Curtailment (%)', fill = 'iteration') +
    theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) +
    facet_grid(scenario~season)
  
  p.year = ggplot(curt_year) +
    geom_bar(aes(x=Year, y=curtailment, fill = iteration), stat='identity', position = 'dodge') +
    plot_theme +
    labs(x=NULL,y='Average Curtailment (%)', fill = 'iteration') +
    scale_x_continuous(breaks = unique(curt_year$Year)[c(TRUE,FALSE)]) +
    facet_grid(scenario~., scales = 'free_x') +
    theme(axis.text.x = element_text(angle = 30, hjust = 1, vjust = 0)) 
  
  p.region = ggplot(curt_region) +
    geom_bar(aes(x=r, y=curtailment, fill = iteration), stat='identity', position = 'dodge') +
    plot_theme +
    labs(x=NULL,y='Average Curtailment (%)', fill = 'iteration') +
    facet_grid(scenario~.) +
    theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) 
    
  return.list = list(p.timeslice, p.year, p.region)
}

#--------------------------#
# CC by iteration ----
#--------------------------#

plot_cc_iter = function(type_filter = c('BESS|Solar|Wind|Pumped hydro')){
  cc_season = cc_iter[grepl(type_filter, Type),
                      .(cc = mean(cap.value)*100), by = .(season,iteration,scenario,Type)]
  
  cc_year = cc_iter[grepl(type_filter, Type),
                    .(cc = mean(cap.value)*100), by = .(Year,iteration,scenario,Type)]
  
  cc_region = cc_iter[grepl(type_filter, Type),
                      .(cc = mean(cap.value)*100), by = .(r,iteration,scenario, Type)]
  
  p.season = ggplot(cc_season) +
    geom_bar(aes(x=season, y=cc, fill = iteration), stat='identity', position = 'dodge') +
    plot_theme +
    labs(x=NULL,y='Average CC (%)', fill = 'iteration') +
    theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) +
    facet_grid(Type~scenario)
  
  p.year = ggplot(cc_year) +
    geom_bar(aes(x=Year, y=cc, fill = iteration), stat='identity', position = 'dodge') +
    plot_theme +
    scale_x_continuous(breaks = unique(cc_year$Year)[c(TRUE,FALSE)]) +
    theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) +
    labs(x=NULL,y='Average CC (%)', fill = 'iteration') +
    facet_grid(Type~scenario, scales = 'free_x')
  
  p.region = ggplot(cc_region) +
    geom_bar(aes(x=r, y=cc, fill = iteration), stat='identity', position = 'dodge') +
    plot_theme +
    labs(x='State or resource region',y='Average CC (%)', fill = 'iteration') +
    facet_grid(Type~scenario, scales = 'free') 
  
  if(length(unique(cc_region[,r]))>34){
    p.region = p.region + 
      theme(axis.text.x = element_blank(), axis.ticks.x = element_blank())
  }else{
    p.region = p.region +
      theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 1)) 
  }
  
  return.list = list(p.season, p.year, p.region)
}

#--------------------------#
# operating reserve year ----
#--------------------------#

plot_opres_tot = function(aggregate.by = c("nation","region")){
  
  if(aggregate.by == "nation"){
    opres.india = opres[, .(opres = sum(opres)/1000),
                        by = c('Type','Year','scenario')]
    
    opres.india = melt(opres.india, 
                       id.vars = c('Type', 'Year','scenario'))
    opres.india[is.na(value), value := 0]
    
    opres.india[,tot := sum(value), by = .(scenario,Year)]
    opres.india[,percent := value/tot, by = .(scenario,Year)]
    
    # plot results - national
    p = ggplot(opres.india, aes(x = Year, y = percent, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Operating reserve provision (GW)', x = NULL) +
      scale_y_continuous(labels=scales::percent) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      facet_grid(scenario~.)
    
    return.list = list(plot = p)
    
    return(return.list)
    
  }
  
  if(aggregate.by == "region"){
    opres.region = opres[, .(opres = sum(opres)/1000),
                         by = c('Type','Year','scenario','region')]
    
    opres.region = melt(opres.region, 
                        id.vars = c('Type', 'Year','scenario','region'))
    opres.region[is.na(value), value := 0]
    
    opres.region[,tot := sum(value), by = .(scenario,Year,region)]
    opres.region[,percent := value/tot, by = .(scenario,Year,region)]
    
    # plot results - national
    p = ggplot(opres.region, aes(x = Year, y = percent, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Operating reserve provision (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
      facet_grid(region~scenario)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

#--------------------------#
# operating reserve timeslice ----
#--------------------------#

plot_opres = function(aggregate.by = c("nation","region"), year = 'year.max'){
  
  if(year == 'year.max'){
    year.max = storage[,max(Year)]
  }else{
    year.max = year
  }
  
  if(aggregate.by == "nation"){
    opres.india = opres[Year == year.max, .(opres = sum(opres)/1000),
                            by = c('Type','time_slice','season','time','scenario')]
    
    opres.india = melt(opres.india, 
                         id.vars = c('Type', 'time_slice','season','time','scenario'))
    opres.india[is.na(value), value := 0]
    
    # plot results - national
    p = ggplot(opres.india, aes(x = time, y = value, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Operating reserve provision (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
      facet_grid(scenario~season)
    
    return.list = list(plot = p)
    
    return(return.list)
    
  }
  
  if(aggregate.by == "region"){
    opres.region = opres[Year == year.max, .(opres = sum(opres)/1000),
                             by = c('Type','time_slice','scenario','region')]
    
    opres.region = melt(opres.region, 
                          id.vars = c('Type', 'time_slice','scenario','region'))
    opres.region[is.na(value), value := 0]
    
    # plot results - national
    p = ggplot(opres.region, aes(x = time_slice, y = value, group = Type, fill = Type)) + 
      geom_bar(position = 'stack', stat = 'identity') +
      labs(y = 'Operating reserve provision (GW)', x = NULL) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
      facet_grid(region~scenario)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

#--------------------------#
# total system cost ----
#--------------------------#

plot_system_costs = function(aggregate.by = c("nation")){
  
  year = max(cap.cost$Year)
  
  if(aggregate.by == 'nation'){
    fuel = fuel.cost[Year == year,
                     .(value = sum(fuelcost), type = "fuel"), by = .(scenario)]
    fom = fom.cost[Year == year,
                   .(value = sum(fomcost), type = "fom"), by = .(scenario)]
    vom = vom.cost[Year == year,
                   .(value = sum(vomcost), type = "vom"), by = .(scenario)]
    cap = cap.cost[Year == year,
                   .(value = sum(capcost), type = "capacity"), by = .(scenario)]
    
    costs = rbindlist(list(fuel, fom, vom, cap))
    
    costs[,type := factor(type, levels = c("fuel","fom","vom", "capacity"))]
    
    p = ggplot(data = costs) +
      geom_bar(aes(x = scenario, y = value, fill = type), stat = 'identity') +
      labs(y = "Cost (INR)", x = NULL) +
      plot_theme +
      ggtitle(paste0('Total system cost in year ', as.character(year))) 
    
    return(p)
      
  }
  
  if(aggregate.by == 'region'){
    fuel = fuel.cost[Year == year,
                     .(value = sum(fuelcost), type = "fuel"), by = .(scenario, region)]
    fom = fom.cost[Year == year,
                   .(value = sum(fomcost), type = "fom"), by = .(scenario, region)]
    vom = vom.cost[Year == year,
                   .(value = sum(vomcost), type = "vom"), by = .(scenario, region)]
    cap = cap.cost[Year == year,
                   .(value = sum(capcost), type = "capacity"), by = .(scenario, region)]
    
    costs = rbindlist(list(fuel, fom, vom, cap))
    
    costs[,type := factor(type, levels = c("fuel","fom","vom", "capacity"))]
    
    p = ggplot(data = costs) +
      geom_bar(aes(x = region, y = value, fill = type), stat = 'identity') +
      labs(y = "Cost (INR)", x = NULL) +
      plot_theme +
      ggtitle(paste0('System cost in year ', as.character(year))) +
      facet_grid(~scenario)
    
    return(p)
    
  }
  
  if(aggregate.by == 'technology'){
    fuel = fuel.cost[Year == year,
                     .(value = sum(fuelcost), type = "fuel"), by = .(scenario, Type)]
    fom = fom.cost[Year == year,
                   .(value = sum(fomcost), type = "fom"), by = .(scenario, Type)]
    vom = vom.cost[Year == year,
                   .(value = sum(vomcost), type = "vom"), by = .(scenario, Type)]
    cap = cap.cost[Year == year,
                   .(value = sum(capcost), type = "capacity"), by = .(scenario, Type)]
    
    costs = rbindlist(list(fuel, fom, vom, cap))
    
    costs[,type := factor(type, levels = c("fuel","fom","vom", "capacity"))]
    
    p = ggplot(data = costs) +
      geom_bar(aes(x = Type, y = value, fill = type), stat = 'identity') +
      labs(y = "Cost (INR)", x = NULL) +
      plot_theme +
      ggtitle(paste0('Costs in year ', as.character(year))) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(~scenario)
    
    return(p)
    
  }
}

#--------------------------#
# marginal cost ----
#--------------------------#

plot_marginal_cost = function(aggregate.by = c("nation","region")){
  
  if(aggregate.by == 'nation'){
    mc.india =  marg.cost[,sum(margcost), by = c('Timeslice','time','season','Year','scenario')]
    
    #normalize marginal cost by number of hours per timeslice
    mc.india = merge(mc.india, hours, by.x=c('Timeslice','scenario'),by.y=c('h','scenario'))
    mc.india[,marginal := V1/hours]
    
    p = ggplot(mc.india, aes(x = time, y = marginal, group = Year, color = Year)) + 
      geom_line() +
      geom_point() +
      labs(y = 'Marginal cost (INR/MWh)', x = NULL) +
      scale_color_continuous(breaks=seq(min(mc.india$Year), max(mc.india$Year), 1),
                              guide = guide_legend()) +
      #scale_color_distiller(palette = "Blues")+
      plot_theme +
      theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
      facet_grid(scenario~season)
    
    return.list = list(plot=p)
    
  }
  
  if(aggregate.by == 'region'){
    mc.reg =  marg.cost[,sum(margcost), by = c('time_slice','Year','region','scenario')]
    
    p = ggplot(mc.reg, aes(x = time_slice, y = V1, group = Year, color = Year)) + 
      geom_line() +
      geom_point() +
      labs(y = 'Marginal cost (INR/MWh)', x = NULL) +
      scale_color_continuous(breaks=seq(min(mc.india$Year), max(mc.india$Year), 1),
                             guide = guide_legend()) +
      #scale_color_distiller(palette = "Blues")+
      plot_theme +
      theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
      facet_grid(scenario~region)
    
    return.list = list(plot = p)
    
  }
  
  return(return.list)
}

#--------------------------#
# Capacity map by state ----
#--------------------------#

# cloropleth map with capacity by scenario
map_capacity = function(category = c(), 
                        type = c(),
                         palette = c('Blues','BuGn','BuPu',
                                     'GnBu', 'Greens', 'Greys', 'Oranges',
                                     'OrRd', 'PuBu', 'PuBuGn', 'PuRd', 'Purples',
                                     'RdPu', 'Reds', 'YlGn', 'YlGnBu ', 'YlOrBr',
                                     'YlOrRd'),
                         years = final.year,
                         scenario_filter = c()){

  if(length(years) == 1 & max(years) == final.year){
    years = cap[,max(Year)]
  }else{
    years = years
  }
  
  # summarize year capacity by state
  final.cap = cap[Year %in% years]
  
  # filter category or type
  if(length(category)>0){
    final.cap = final.cap[Technology %in% category]
  }else if(length(type)>0){
    final.cap = final.cap[Type %in% type]
  }
  
  final.cap = final.cap[,.(capacity = sum(capacity)), by = .(State, Year, scenario)]

  if(nrow(final.cap) == 0){
    return('No capacity')
  }
  
  # add zero where no capacity
  no.cap.states = cap[,.(State = rep(unique(State),n.scenario), 
                         scenario = rep(unique(scenario), each = length(unique(State))),
                         Year = rep(unique(final.cap$Year),each = n.scenario*length(unique(State))),
                         capacity = 0)]

  no.cap.states = no.cap.states[!(paste0(State,scenario,Year) %in% final.cap[,paste0(State,scenario,Year)]),]
  
  final.cap = rbind(final.cap, no.cap.states, fill = T)
  
  # filter scenarios
  if(length(scenario_filter) > 0){
    final.cap = final.cap[scenario %in% scenario_filter]
  }
  
  contour.reg = merge(contour.reg, final.cap, 
                    by.x = "NAME_1corr", by.y = "State", all.x = T,
                   allow.cartesian = T)
  
  if(length(palette)==1){
    palette = brewer.pal(9,palette)
  }
  
  # plot the map
  p = ggplot() +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.reg[!is.na(scenario)], aes(long, lat, group = group, fill = capacity), 
                 color = "grey90") +
    geom_path(data = contour.nat, aes(long, lat, group = group), color = 'grey10', size = 0.5) +
    scale_fill_gradientn("MW", guide = "legend",
                         colors = palette, labels=comma) + 
    #scale_fill_manual("",values = gen.colors, drop = TRUE) +
    #geom_point(data = nodes, aes(X, Y), size = .5, color = "red") +
    coord_map() +
    theme(axis.ticks = element_blank(), 
          axis.title = element_blank(), 
          axis.text =  element_blank(),
          line = element_blank(),
          plot.title=element_text(color=color.title, size=large.text.size, vjust=1.25),
          panel.background=element_rect(fill=color.background, color=color.background),
          plot.background=element_rect(fill=color.background, color=color.background),
          panel.border=element_blank(),
          panel.grid.major=element_blank(),
          panel.grid.minor=element_blank(),
          strip.background = element_rect(fill="white"),
          strip.text = element_text(size=small.text.size, color = color.axis.text),
          legend.key = element_rect(color = "grey80", size = 0.8), 
          legend.key.size = grid::unit(1.5, "lines"),
          legend.text = element_text(size = small.text.size, color = color.axis.text, margin = margin(l = 5)), 
          legend.title = element_text(size = small.text.size, color = color.axis.title))
  
  
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
# Capacity map by rs ----
#--------------------------#

# cloropleth map with capacity by scenario
map_rs_capacity = function(category = c('WIND','UPV','DISTPV'), 
                           palette = c('Blues','BuGn','BuPu',
                                       'GnBu', 'Greens', 'Greys', 'Oranges',
                                       'OrRd', 'PuBu', 'PuBuGn', 'PuRd', 'Purples',
                                       'RdPu', 'Reds', 'YlGn', 'YlGnBu ', 'YlOrBr',
                                       'YlOrRd'),
                           years = final.year, scenario_filter = c()){
  
  if(length(years) == 1 & max(years) == final.year){
    years = cap.rs[,max(Year)]
  }else{
    years = years
  }
  
  # summarize year capacity by state
  final.cap = cap.rs[Year %in% years]
  
  # filter category
  final.cap = final.cap[Technology %in% category]

  if(nrow(final.cap) == 0){
    return('No capacity')
  }
  
  # add zero where no capacity
  no.cap.rs = cap[,.(rs = rep(unique(r.rs.map$rs),n.scenario),
                         scenario = rep(unique(scenario), each = length(unique(r.rs.map$rs))),
                         Year = rep(unique(final.cap$Year),each = n.scenario*length(unique(r.rs.map$rs))),
                         capacity = 0)]

  no.cap.rs = no.cap.rs[!(paste0(rs,scenario,Year) %in% final.cap[,paste0(rs,scenario,Year)]),]

  final.cap = rbind(final.cap, no.cap.rs, fill = T)
  final.cap[,rs := as.integer(as.character(rs))]
  
  # filter scenarios
  if(length(scenario_filter) > 0){
    final.cap = final.cap[scenario %in% scenario_filter]
  }
  
  contour.rs = merge(contour.rs, final.cap, 
                 by.x = "grid_vals", by.y = "rs", all.x = T,
                 allow.cartesian = T)
  contour.rs[capacity == 0, capacity := NA]
  
  if(length(state_filter) > 0){
    temp = copy(r.rs.map)
    temp[, rs := as.integer(as.character(rs))]
    contour.rs = merge(contour.rs, temp, by.x='id',by.y='rs')
    contour.rs = contour.rs[r %in% state_filter]
    
    bas = bas[id %in% unique(contour.rs$state_name)]
    
    # plot the map
    p = ggplot() +
      geom_polygon(data = contour.rs, aes(long + .05, lat - .05, group = group), 
                   color = "grey70", fill = 'grey60') +
      geom_polygon(data = contour.rs, aes(long + .05, lat + .05, group = group), 
                   color = "grey70", fill = 'grey60') +
      geom_polygon(data = contour.rs, aes(long, lat, group = group, fill = capacity), 
                   color = "grey90", size = 0.8) +
      geom_path(data= bas, aes(long, lat, group = group), color = 'grey10', size = 1) +
      #geom_path(data = contour.rs, aes(long, lat, group = group), color = 'grey20', size = 1) +
      scale_fill_gradientn("MW", guide = guide_legend(reverse = TRUE),
                           colors = brewer.pal(9,palette),
                           na.value = 'grey70', labels=comma) + 
      coord_fixed() +
      theme_bw() +
      theme(axis.ticks = element_blank(), 
            axis.title = element_blank(), 
            axis.text =  element_blank(),
            line = element_blank(),
            panel.border = element_blank(),
            plot.title=element_text(color=color.title, size=large.text.size, vjust=1.25),
            legend.key.size = grid::unit(1.5, "lines"),
            legend.text = element_text(size = small.text.size, color = color.axis.text, margin = margin(l = 5)),
            legend.title = element_text(size =small.text.size, color = color.axis.text))
    
  }else{
  # plot the map
  p = ggplot() +
    geom_polygon(data = contour.rs.nat, aes(long + 15000, lat - 15000, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.rs.nat, aes(long + 15000, lat + 15000, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_path(data = contour.rs.nat, aes(long, lat, group = group), color = 'grey20', size = 1.2) +
    geom_polygon(data = contour.rs, aes(long, lat, group = group, fill = capacity), 
                 color = "grey80") +
    geom_path(data = contour.rs.reg, aes(long,lat,group = group), color = 'grey40') +
    scale_fill_gradientn("MW", guide = guide_legend(reverse = TRUE),
                         colors = brewer.pal(9,palette),
                         na.value = 'grey70', labels=comma) + 
    coord_fixed() +
    theme_bw() +
    theme(axis.ticks = element_blank(), 
          axis.title = element_blank(), 
          axis.text =  element_blank(),
          line = element_blank(),
          panel.border = element_blank(),
          plot.title=element_text(color=color.title, size=large.text.size, vjust=1.25),
          legend.key.size = grid::unit(1.5, "lines"),
          legend.text = element_text(size = small.text.size, color = color.axis.text, margin = margin(l = 5)),
          legend.title = element_text(size =small.text.size, color = color.axis.text))
  
  
  if(length(unique(contour.rs$Year))>1 & length(unique(contour.rs$scenario)) > 1){
    p = p + facet_grid(scenario~Year)
  }else if(length(unique(contour.rs$Year))>1){
    p = p + facet_wrap(~Year)
  }else if(length(unique(contour.rs$scenario))>1){
    p = p + facet_wrap(~scenario)
  }
  
  return(p)
}

#---------------------------#
# plot transmission investments ----
#--------------------------#

plot_tx_inv = function(){
  if(!"State.x" %in% names(tx.inv)){
    return(list(plot = NA, data = NA))
  }
  
  if(nrow(tx.inv) == 0){
    return(list(plot = NA, data = "No transmission investments"))
  }
  
  inv = tx.inv[,.(investments = sum(investments)),
               by = .(State.x, State.y, scenario)]
  inv[paste0(State.x,State.y) %in% paste0(State.y,State.x), rev := T]
  rev = inv[rev == T, .(State.x = State.y, State.y = State.x, investments, scenario)]
  inv[,rev := NULL]
  inv = rbind(inv,rev)
  inv = inv[,.(investments = sum(investments)), by = .(State.x, State.y, scenario)]
  inv[,dup := duplicated(investments)]
  inv = inv[!dup == T]
  
  inv[,State.x := gsub("_"," ",State.x)]
  inv[,State.y := gsub("_"," ",State.y)]
  
  inv = inv[order(investments,decreasing = F)]
  inv[,states := factor(paste(State.x,'-',State.y), levels = unique(paste(State.x,'-',State.y)))]

  p = ggplot(data = inv) +
    geom_bar(aes(x = states, y = investments/1000, fill = scenario), 
             stat = 'identity', position = 'dodge') +
    labs(x = NULL, y = "Transmission investment (GW)") +
    coord_flip() +
    plot_theme 
  
  data = tx.inv[,.(`State From` = State.x, `State To` = State.y,
                   Year, scenario, investments = round(investments, digits = 0))]
  
  data = dcast.data.table(data, `State From` + `State To` + Year ~ scenario,
                          value.var = 'investments')
  data = data[order(Year)]
  
  return.list = list(plot = p, data = data)
}

#---------------------------#
# transmission investment map ----
#--------------------------#

map_tx_inv = function(scenario_filter = c(),years = c(2030,2040,2050)){
  if(!"State.x" %in% names(tx.inv)){
    return(NA)
  }
  
  if(nrow(tx.inv) == 0){
    return("No transmission investments")
  }
  
  inv = tx.inv[,.(investments = sum(investments)),
               by = .(Year,State.x, State.y, scenario)]
  inv[paste0(State.x,State.y) %in% paste0(State.y,State.x), rev := T]
  rev = inv[rev == T, .(State.x = State.y, State.y = State.x, investments, scenario, Year)]
  inv[,rev := NULL]
  inv = rbind(inv,rev)
  inv = inv[,.(investments = sum(investments)), by = .(State.x, State.y, scenario,Year)]
  inv[,dup := duplicated(investments)]
  inv = inv[!dup == T]
  
  # get the cumulative sum
  inv = inv[order(Year,State.x,State.y,scenario)]
  inv[,investments := cumsum(investments), by = .(State.x,State.y,scenario)]
  
  inv = inv[Year %in% years]
  
  # inv from
  inv = merge(inv, centroids, by.x = "State.x", by.y = "State")
  setnames(inv, c('x','y'), c('x.from','y.from'))
  
  # inv to
  inv = merge(inv, centroids, by.x = "State.y", by.y = "State")
  setnames(inv, c('x','y'), c('x.to','y.to'))
  
  # interleave data for mapping
  inv.from = inv[,.(State = State.x, x = x.from, y = y.from, investments, scenario, Year)]
  
  inv.to = inv[,.(State = State.y, x = x.to, y = y.to, investments, scenario, Year)]
  
  NA.rows = data.table(1:nrow(inv),
                       State = NA, x = NA, y = NA, investments = NA, scenario = NA, Year = NA)
  NA.rows = NA.rows[,-1]
  
  inv.interleave = gdata::interleave(inv.from, inv.to, NA.rows)
  inv.interleave[,scenario := zoo::na.locf(scenario)]
  inv.interleave[,Year := zoo::na.locf(Year)]
  inv.interleave = inv.interleave[-.N]
  
  # filter scenario
  if(length(scenario_filter) > 0){
    inv.interleave = inv.interleave[scenario %in% scenario_filter]
  }
  
  # plot map of total transmission inv
  p = ggplot() +
    geom_polygon(data = contour.nat, aes(long + 0.1, lat + 0.1, group = group),
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.nat, aes(long + 0.1, lat - 0.1, group = group),
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.reg, aes(long, lat, group = group),
                 fill = "grey95", color = 'grey50')  +
    geom_path(data = contour.nat, aes(long, lat, group = group), color = 'grey90', size = 0.5) +   
    #geom_point(data = centroids, aes(x, y), size = 1, color = "gold") + # uncomment to plot centroid points
    geom_path(data = inv.interleave, aes(x, y, size = investments)) +
    scale_size(labels = scales::comma, range = c(0.1,2)) +
    coord_map() +
    theme(axis.ticks = element_blank(), 
          axis.title = element_blank(), 
          axis.text =  element_blank(),
          line = element_blank(),
          plot.title=element_text(color=color.title, size=large.text.size, vjust=1.25),
          panel.background=element_rect(fill=color.background, color=color.background),
          plot.background=element_rect(fill=color.background, color=color.background),
          panel.border=element_blank(),
          panel.grid.major=element_blank(),
          panel.grid.minor=element_blank(),
          strip.background = element_rect(fill="white"),
          strip.text = element_text(size=small.text.size, color = color.axis.text),
          legend.key = element_rect(color = "grey80", size = 0.8), 
          legend.key.size = grid::unit(1.5, "lines"),
          legend.text = element_text(size = small.text.size, color = color.axis.text, margin = margin(l = 5)), 
          legend.title = element_text(size = small.text.size, color = color.axis.title)) +
    ggtitle("Total transmission investment") 
  
  if(length(years)==1){
    p = p + facet_grid(~scenario) 
  }else{
    p = p + facet_grid(scenario~Year)
  }
  
  return(p)
  
}

#---------------------------#
# transmission flow map ----
#--------------------------#

map_tx_flow = function(year = final.year, by = c('state','region'), scenario_filter = c()){
  if(anyNA(tot.flow$value)){
    return(NA)
  }

  if(by == 'state'){
    # calculate sum of total flow in both directions
    flow = tot.flow[Year == year]
    flow = rbind(flow, flow[,.(State.x = State.y, State.y = State.x, 
                               flow, scenario, Year)], fill = T)
    flow = flow[,.(flow = sum(flow)), by = .(State.x, State.y, scenario, Year)]
    
    # flow from  
    flow = merge(flow, centroids, by.x = "State.x", by.y = "State")
    setnames(flow, c('x','y'), c('x.from','y.from'))
    
    # flow to
    flow = merge(flow, centroids, by.x = "State.y", by.y = "State")
    setnames(flow, c('x','y'), c('x.to','y.to'))
    
    # interleave data for mapping
    flow.from = flow[,.(State = State.x, x = x.from, y = y.from, flow, scenario)]
    
    flow.to = flow[,.(State = State.y, x = x.to, y = y.to, flow, scenario)]
    
    NA.rows = data.table(1:nrow(flow),
                         State = NA, x = NA, y = NA, flow = NA, scenario = NA)
    NA.rows = NA.rows[,-1]
    
    flow.interleave = gdata::interleave(flow.from, flow.to, NA.rows)
    flow.interleave[,scenario := zoo::na.locf(scenario)]
    flow.interleave = flow.interleave[-.N]
    
    # scenario filter
    if(length(scenario_filter)>0){
      flow.interleave = flow.interleave[scenario %in% scenario_filter]
    }
    
    # plot map of total transmission flow
    p = ggplot() +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                   color = "grey70", fill = 'grey60') +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                   color = "grey70", fill = 'grey60') +
      geom_polygon(data = contour.reg, aes(long, lat, group = group), 
                   fill = "grey95", color = 'grey50')  +
      geom_path(data = contour.nat, aes(long, lat, group = group), color = 'grey10', size = 0.5) +
      #geom_point(data = centroids, aes(x, y), size = 1, color = "gold") + # uncomment to plot centroid points
      geom_path(data = flow.interleave, aes(x, y, color = flow/1000000), 
                size = .8) +
      scale_color_gradient(name = "Total Power Flow (TWh)",
                           low = "gray60", high = "firebrick1", labels = comma) +
      coord_map() +
      theme_bw() +
      theme(axis.ticks = element_blank(), 
            axis.title = element_blank(), 
            axis.text =  element_blank(),
            line = element_blank(),
            panel.border = element_blank()) +
      ggtitle(paste0("Total flow in year ",as.character(year))) 
    }
    
  if(by == 'region'){

    # calculate regional flows
    flow = tot.flow[Year == year]
    flow = flow[!region.x == region.y, .(flow = sum(flow)), by = .(region.x, region.y, Year, scenario)]

    # flow from  
    flow = merge(flow, region.centroids, by.x = "region.x", by.y = "region")
    setnames(flow, c('x','y'), c('x.from','y.from'))

    # flow to
    flow = merge(flow, region.centroids, by.x = "region.y", by.y = "region")
    setnames(flow, c('x','y'), c('x.to','y.to'))

    p = ggplot() +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.region, aes(long, lat, group = group), 
                   fill = "grey95", color = 'grey50')  +
      geom_curve(data = flow, aes(x = x.from, y = y.from, xend = x.to, yend = y.to, color = flow/1000000), 
                 size = 1,
                 alpha = .9,
                 curvature = .3,
                 arrow = arrow(angle = 20, length = unit(.2, "inches"))) +
      scale_color_gradient(name = "Total Power Flow (TWh)",
                           low = "gray60", high = "firebrick1") +
      coord_fixed() +
      theme_bw() +
      theme(axis.ticks = element_blank(), 
            axis.title = element_blank(), 
            axis.text =  element_blank(),
            line = element_blank(),
            panel.border = element_blank()) +
      ggtitle(paste0("Total flow in year ",as.character(year)))
    
  }
  
  if(length(unique(flow$scenario))>1){
    p = p + facet_wrap(~scenario)
  }
  
  return(p)
}

map_max_flow = function(year = final.year, by = c('state','region'), scenario_filter = c()){
  
  if(by == 'state'){
  # get max flow in both directions
  flow = tslc.flow[Year == year, .(flow = sum(flow)), by = .(time_slice, scenario, State.x, State.y, Year)]
  flow = flow[,.(flow = max(flow)), by = .(scenario, State.x, State.y, Year)]
 
  # take the max flow in one direction
  flow = rbind(flow, flow[,.(State.x = State.y, State.y = State.x, 
                             flow, scenario, Year)], fill = T)
  flow = flow[,.(flow = max(flow)), by = .(State.x, State.y, scenario, Year)]
  
  # flow from  
  flow = merge(flow, centroids, by.x = "State.x", by.y = "State")
  setnames(flow, c('x','y'), c('x.from','y.from'))
  
  # flow to
  flow = merge(flow, centroids, by.x = "State.y", by.y = "State")
  setnames(flow, c('x','y'), c('x.to','y.to'))
  
  if(length(scenario_filter)>0){
    flow = flow[scenario %in% scenario_filter]
  }
  
  # exclude the daman&diu and maharashtra flows
  flow = flow[!(State.x == 'Daman_Diu' & State.y == 'Maharashtra')]
  flow = flow[!(State.y == 'Daman_Diu' & State.x == 'Maharashtra')]
  
  # plot map of maximum transmission flow
  p = ggplot() +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.reg, aes(long, lat, group = group), 
                 fill = "grey95", color = 'grey50')  +
    geom_path(data = contour.nat, aes(long, lat, group = group), color = 'grey10', size = 0.5) +
    geom_segment(data = flow, aes(x = x.from, y = y.from, xend = x.to, yend = y.to, color = flow/1000), 
               size = 1,
               alpha = .9) +
    scale_color_gradient(name = "Max Power Flow (GW)",
                         low = "gray60", high = "firebrick1") +
    coord_map() +
    theme_bw() +
    theme(axis.ticks = element_blank(), 
          axis.title = element_blank(), 
          axis.text =  element_blank(),
          line = element_blank(),
          panel.border = element_blank()) +
    ggtitle(paste0("Maximum flow in year ",as.character(year)))
  }
  
  if(by == 'region'){
    flow = tslc.flow[Year == year, .(flow = sum(flow)), by = .(time_slice, scenario, region.x, region.y, Year)]
    flow = flow[!region.x == region.y,.(flow = max(flow)), by = .(scenario, region.x, region.y, Year)]
    
    # take the max flow in one direction
    flow = rbind(flow, flow[,.(region.x = region.y, region.y = region.x, 
                               flow, scenario, Year)], fill = T)
    flow = flow[,.(flow = max(flow)), by = .(region.x, region.y, scenario, Year)]
    
    # flow from  
    flow = merge(flow, region.centroids, by.x = "region.x", by.y = "region")
    setnames(flow, c('x','y'), c('x.from','y.from'))
    
    # flow to
    flow = merge(flow, region.centroids, by.x = "region.y", by.y = "region")
    setnames(flow, c('x','y'), c('x.to','y.to'))
    
    if(length(scenario_filter)>0){
      flow = flow[scenario %in% scenario_filter]
    }
    
    p = ggplot() +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.region, aes(long, lat, group = group), 
                   fill = "grey95", color = 'grey50')  +
      geom_curve(data = flow, aes(x = x.from, y = y.from, xend = x.to, yend = y.to, color = flow/1000), 
                 size = 1,
                 alpha = .9,
                 curvature = .3,
                 arrow = arrow(angle = 20, length = unit(.2, "inches"))) +
      scale_color_gradient(name = "Max Power Flow (GW)",
                           low = "gray60", high = "firebrick1") +
      coord_fixed() +
      theme_bw() +
      theme(axis.ticks = element_blank(), 
            axis.title = element_blank(), 
            axis.text =  element_blank(),
            line = element_blank(),
            panel.border = element_blank()) +
      ggtitle(paste0("Maximum flow in year ",as.character(year)))
    
  }
  
  if(length(unique(flow$scenario))>1){
    p = p + facet_wrap(~scenario)
  }
  return(p)
}

#--------------------------#
# capacity factors ----
#--------------------------#
plot_capacity_factor = function(aggregate.by = c("nation","state"),category.filter = c()){
  
  tlf = merge(cap, gen, 
              by = c('Technology','State','scenario','Year','region','Type'),
              all = T)[!(Technology %in% c('HYDRO-PUMPED','BATTERY'))]
  
  setnames(tlf, 'V1','generation')
  
  tlf[is.na(generation), generation := 0]
  
  tlf = merge(tlf, outage[,.(outage = mean(outage)), by = .(Technology, scenario)], 
              by = c('Technology','scenario'))
  
  tlf[, max.avail := capacity*8760*outage]
  
  tlf[,load.factor := generation/max.avail]
  
  year.min = min(tlf$Year)
  year.max = max(tlf$Year)
  
  if(length(category.filter) > 0){
    tlf = tlf[Type %in% category.filter]
  }
  
  if("nation" %in% aggregate.by){
    tlf.india = tlf[,mean(load.factor), by = c('Type','Year','scenario')]
    
    p = ggplot(tlf.india, aes(x = Year, y = V1, group = scenario, fill = scenario)) + 
      geom_bar(position = 'dodge', stat = 'identity') +
      labs(y = 'Capacity Factor (%)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min-1, year.max, 2)) +
      #scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_wrap(~Type, ncol = 3)
    
    return.list = list(plot = p)
    
    return(return.list)
    
  }
  
  if("state" %in% aggregate.by){
    tlf.state = tlf[,mean(load.factor), by = c('State','Type','Year','scenario')]
    
    p = ggplot(tlf.state, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'dodge', stat = 'identity') +
      labs(y = 'Total Curtailment (%)', x = NULL) +
      #scale_x_continuous(breaks=seq(year.min-1, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(State~scenario)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

#--------------------------#
# planning reserve provision ----
#--------------------------#
plot_prm_provision = function(aggregate.by = c("nation","state")){
  
  tlf = merge(cap, gen, 
              by = c('Technology','State','scenario','Year','region','Type'),
              all = T)[!(Technology %in% c('HYDRO-PUMPED','BATTERY'))]
  
  setnames(tlf, 'V1','generation')
  
  tlf[is.na(generation), generation := 0]
  
  tlf = merge(tlf, outage[,.(outage = mean(outage)), by = .(Technology, scenario)], 
              by = c('Technology','scenario'))
  
  tlf[, max.avail := capacity*8760*outage]
  
  tlf[,load.factor := generation/max.avail]
  
  year.min = min(tlf$Year)
  year.max = max(tlf$Year)
  
  if("nation" %in% aggregate.by){
    tlf.india = tlf[,mean(load.factor), by = c('Type','Year','scenario')]
    
    p = ggplot(tlf.india, aes(x = Year, y = V1, group = scenario, fill = scenario)) + 
      geom_bar(position = 'dodge', stat = 'identity') +
      labs(y = 'Capacity Factor (%)', x = NULL) +
      scale_x_continuous(breaks=seq(year.min-1, year.max, 2)) +
      #scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_wrap(~Type)
    
    return.list = list(plot = p)
    
    return(return.list)
    
  }
  
  if("region" %in% aggregate.by){
    tlf.region = tlf[,mean(load.factor), by = c('region','Type','Year','scenario')]
    
    p = ggplot(tlf.region, aes(x = Year, y = V1, group = Type, fill = Type)) + 
      geom_bar(position = 'dodge', stat = 'identity') +
      labs(y = 'Total Curtailment (%)', x = NULL) +
      #scale_x_continuous(breaks=seq(year.min-1, year.max, 2)) +
      scale_fill_manual("",values = gen.colors, drop = TRUE) +
      plot_theme +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      facet_grid(region~scenario)
    
    return.list = list(plot = p)
    
    return(return.list)
  }
  
}

#---------------------------#
# transmission flow map ----
#--------------------------#
map_tx_flow = function(year = final.year, by = c('state','region')){
  if(anyNA(tot.flow$value)){
    return(NA)
  }
  
  if(by == 'state'){
    # calculate sum of total flow in both directions
    flow = tot.flow[Year == year]
    flow = rbind(flow, flow[,.(State.x = State.y, State.y = State.x, 
                               flow, scenario, Year)], fill = T)
    flow = flow[,.(flow = sum(flow)), by = .(State.x, State.y, scenario, Year)]
    
    # flow from  
    flow = merge(flow, centroids, by.x = "State.x", by.y = "State")
    setnames(flow, c('x','y'), c('x.from','y.from'))
    
    # flow to
    flow = merge(flow, centroids, by.x = "State.y", by.y = "State")
    setnames(flow, c('x','y'), c('x.to','y.to'))
    
    # interleave data for mapping
    flow.from = flow[,.(State = State.x, x = x.from, y = y.from, flow, scenario)]
    
    flow.to = flow[,.(State = State.y, x = x.to, y = y.to, flow, scenario)]
    
    NA.rows = data.table(1:nrow(flow),
                         State = NA, x = NA, y = NA, flow = NA, scenario = NA)
    NA.rows = NA.rows[,-1]
    
    flow.interleave = gdata::interleave(flow.from, flow.to, NA.rows)
    flow.interleave[,scenario := zoo::na.locf(scenario)]
    flow.interleave = flow.interleave[-.N]
    
    # plot map of total transmission flow
    p = ggplot() +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                   color = "grey70", fill = 'grey60') +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                   color = "grey70", fill = 'grey60') +
      geom_polygon(data = contour.reg, aes(long, lat, group = group), 
                   fill = "grey95", color = 'grey50')  +
      geom_path(data = contour.nat, aes(long, lat, group = group), color = 'grey10', size = 0.5) +
      #geom_point(data = centroids, aes(x, y), size = 1, color = "gold") + # uncomment to plot centroid points
      geom_path(data = flow.interleave, aes(x, y, color = flow/1000000), 
                size = .8) +
      scale_color_gradient(name = "Total Power Flow (TWh)",
                           low = "gray60", high = "firebrick1") +
      coord_map() +
      theme_bw() +
      theme(axis.ticks = element_blank(), 
            axis.title = element_blank(), 
            axis.text =  element_blank(),
            line = element_blank(),
            panel.border = element_blank()) +
      ggtitle(paste0("Total flow in year ",as.character(year))) 
  }
  
  if(by == 'region'){
    
    # calculate regional flows
    flow = tot.flow[Year == year]
    flow = flow[!region.x == region.y, .(flow = sum(flow)), by = .(region.x, region.y, Year, scenario)]
    
    # flow from  
    flow = merge(flow, region.centroids, by.x = "region.x", by.y = "region")
    setnames(flow, c('x','y'), c('x.from','y.from'))
    
    # flow to
    flow = merge(flow, region.centroids, by.x = "region.y", by.y = "region")
    setnames(flow, c('x','y'), c('x.to','y.to'))
    
    p = ggplot() +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.region, aes(long, lat, group = group), 
                   fill = "grey95", color = 'grey50')  +
      geom_curve(data = flow, aes(x = x.from, y = y.from, xend = x.to, yend = y.to, color = flow/1000000), 
                 size = 1,
                 alpha = .9,
                 curvature = .3,
                 arrow = arrow(angle = 20, length = unit(.2, "inches"))) +
      scale_color_gradient(name = "Total Power Flow (TWh)",
                           low = "gray60", high = "firebrick1") +
      coord_fixed() +
      theme_bw() +
      theme(axis.ticks = element_blank(), 
            axis.title = element_blank(), 
            axis.text =  element_blank(),
            line = element_blank(),
            panel.border = element_blank()) +
      ggtitle(paste0("Total flow in year ",as.character(year)))
    
  }
  
  if(length(unique(flow$scenario))>1){
    p = p + facet_wrap(~scenario)
  }
  
  return(p)
}

#--------------------------#
# Coal transport charge  ----
#--------------------------#

# cloropleth map with capacity by scenario
map_transport_charge = function(){
 
  transport_charge = unique(transport_charge[,.(State=i,value)])
  
  transport_charge = merge(transport_charge, unique(ba.set[,.(State,region)]), all.y = T)
  
  transport_charge[is.na(value), value := 0]
  
  contour.reg = merge(contour.reg, transport_charge, 
                      by.x = "NAME_1corr", by.y = "State", all.x = T,
                      allow.cartesian = T)
  
  # plot the map
  p = ggplot() +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                 color = "grey70", fill = 'grey60') +
    geom_polygon(data = contour.reg, aes(long, lat, group = group, fill = value), 
                 color = "grey90") +
    geom_path(data = contour.nat, aes(long, lat, group = group), color = 'grey10', size = 0.5) +
    #scale_fill_gradientn("Coal Transport Charge (INR/MWh)", guide = "legend",
     #                    colors = brewer.pal(9,'Blues'), labels=comma) + 
    #scale_fill_manual("",values = gen.colors, drop = TRUE) +
    #geom_point(data = nodes, aes(X, Y), size = .5, color = "red") +
    scale_fill_continuous("Coal Transport Charge", labels=comma, trans='reverse') +
    #guides(fill = guide_legend(reverse=T))+
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
# Map flows during high RE timeslices  ----
#--------------------------#

map_tslc_flow = function(year = final.year, by = c('state','region'), tech = c('Wind','Solar')){
  
  # identify time_slice with highest national generation 
  natgen = tslc.gen[Type == tech, .(gen = sum(generation.MW)), by = .(scenario, time_slice, time, season) ]
  maxgen = natgen[,max(gen), by = scenario]
  maxgen = merge(maxgen, natgen, by.x = c('V1','scenario'), by.y = c('gen','scenario'))
  
  labels = c(paste0(names(solutions),'\n',as.character(maxgen$season), " " , as.character(maxgen$time)))
  names(labels) = names(solutions)

  if(by == 'state'){
    # get flow in both directions for the time-slice
    flow = tslc.flow[Year == year, .(flow = sum(flow)), by = .(time_slice, scenario, State.x, State.y, Year)]
    flow = flow[paste0(time_slice,scenario) %in% paste0(maxgen$time_slice,maxgen$scenario)]
    
    # flow from  
    flow = merge(flow, centroids, by.x = "State.x", by.y = "State")
    setnames(flow, c('x','y'), c('x.from','y.from'))
    
    # flow to
    flow = merge(flow, centroids, by.x = "State.y", by.y = "State")
    setnames(flow, c('x','y'), c('x.to','y.to'))
    
    # plot map of maximum transmission flow
    p = ggplot() +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.reg, aes(long, lat, group = group), 
                   fill = "grey95", color = 'grey50')  +
      geom_segment(data = flow, aes(x = x.from, y = y.from, xend = x.to, yend = y.to, color = flow/1000), 
                   size = 1,
                   alpha = .9) +
      scale_color_gradient(name = "Power Flow (GW)",
                           low = "gray60", high = "firebrick1") +
      coord_map() +
      theme_bw() +
      theme(axis.ticks = element_blank(), 
            axis.title = element_blank(), 
            axis.text =  element_blank(),
            line = element_blank(),
            panel.border = element_blank()) +
      ggtitle(paste0('Power flow during highest ', tech, ' period in ', as.character(year))) +
      facet_wrap(~scenario, labeller =labeller(scenario = labels))
  }
  
  if(by == 'region'){
    # get flow in both directions for the time-slice
    flow = tslc.flow[Year == year, .(flow = sum(flow)), by = .(time_slice, scenario, region.x, region.y, Year)]
    flow = flow[region.x != region.y]
    flow = flow[paste0(time_slice,scenario) %in% paste0(maxgen$time_slice,maxgen$scenario)]
    
    # flow from  
    flow = merge(flow, region.centroids, by.x = "region.x", by.y = "region")
    setnames(flow, c('x','y'), c('x.from','y.from'))
    
    # flow to
    flow = merge(flow, region.centroids, by.x = "region.y", by.y = "region")
    setnames(flow, c('x','y'), c('x.to','y.to'))
    
    p = ggplot() +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat + 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.nat, aes(long + 0.2, lat - 0.2, group = group), 
                   color = "grey80", fill = 'grey70') +
      geom_polygon(data = contour.region, aes(long, lat, group = group), 
                   fill = "grey95", color = 'grey50')  +
      geom_curve(data = flow, aes(x = x.from, y = y.from, xend = x.to, yend = y.to, color = flow/1000), 
                 size = 1,
                 alpha = .9,
                 curvature = .3,
                 arrow = arrow(angle = 20, length = unit(.2, "inches"))) +
      scale_color_gradient(name = "Power Flow (GW)",
                           low = "gray60", high = "firebrick1") +
      coord_fixed() +
      theme_bw() +
      theme(axis.ticks = element_blank(), 
            axis.title = element_blank(), 
            axis.text =  element_blank(),
            line = element_blank(),
            panel.border = element_blank()) +
      ggtitle(paste0('Power flow during highest ', tech, ' period in ', as.character(year))) +
      facet_wrap(~scenario, labeller =labeller(scenario = labels))
    
  }
  
  return(p)
}

# total system cost difference ----
plot_system_costs_diff = function(aggregate.by = c("nation"), year = final.year,
                                 scenario_filter = c()){
  
  if(aggregate.by == 'nation'){
    fuel = fuel.cost[Year <= year,
                     .(value = sum(fuelcost)/10000000, type = "Fuel"), by = .(scenario)]
    fom = fom.cost[Year <= year,
                   .(value = sum(fomcost)/10000000, type = "Fixed O&M"), by = .(scenario)]
    vom = vom.cost[Year <= year,
                   .(value = sum(vomcost)/10000000, type = "Variable O&M"), by = .(scenario)]
    cap = cap.cost[Year <= year,
                   .(value = sum(capcost)/10000000, type = "Generation capacity"), by = .(scenario)]
    tx.cap = tx.cap.cost[Year <= year,
                         .(value = sum(V1)/10000000, type = "Transmission capacity"), by = .(scenario)]
    
    costs = rbindlist(list(fuel, fom, vom, cap, tx.cap))
    
    costs[,type := factor(type, levels = c("Fuel","Fixed O&M","Variable O&M","Transmission capacity","Generation capacity"))]
    costs[,scenario := factor(scenario, levels = names(solutions))]
    
    # calculate difference from reference scenario
    ref.scenario = names(solutions)[1]
    
    costs.cast = dcast.data.table(costs, type ~ scenario, value.var = "value")
    
    for(i in names(solutions)[!names(solutions) == ref.scenario]){
      costs.cast[, (i) := get(i) - get(ref.scenario)]
    }
    
    costs.diff = melt(costs.cast, id.vars = c("type"), variable.name = "scenario", value.name = "difference")
    
    costs.diff = costs.diff[!(scenario == ref.scenario)]
    
    if(length(scenario_filter)>0){
      costs.diff = costs.diff[scenario %in% scenario_filter]
    }
    
    p = ggplot(data = costs.diff) +
      geom_bar(aes(x = scenario, y = difference, fill = type), stat = 'identity') +
      labs(y = "Crore Rs", x = NULL) +
      plot_theme +
      ggtitle(paste0('Total system cost difference from ',ref.scenario)) +
      scale_color_viridis(discrete = TRUE, option = 'D') +
      scale_fill_viridis(discrete = TRUE)
    
    return(p)
    
  }
}
