pacman::p_load(data.table, ggplot2, viridis, RColorBrewer)

########################
# Using marginals ----
########################

# TO DO: update valuestreams to spit out BOTH marginals and variable levels

vsout = fread('outputs/valuestreams_Dec17_Reference_hours.csv')

source("../scripts/plot_parameters.R")

# get average values of the country
vs = vsout[,.(value = mean(value)), by = .(tech,year,var_name,con_name,tslc=m)]

# keep values that are relevant for storage
vs = vs[year %in% c(2022:2050) & grepl('battery|pumped',tech) &
  con_name %in% c('_obj',
                  '_augur',
                  'eq_supply_demand_balance',
                  'eq_reserve_margin',
                  'eq_opres_requirement') &
  var_name %in% c('cap_sdbin','gen','opres','arbitrage',
                  'inv','storage_in','cap')]

# scale gen and opres variables by hours to get INR/MW
hours = fread('hours.csv')
hours[,V1 := tolower(V1)]
names(hours) = c('tslc','hours')

vs = merge(vs, hours, by = 'tslc', all.x = TRUE)

vs[var_name %in% c('gen','opres','storage_in'), value := value / hours]

# sum across time slices to get $/MW-yr
vs = vs[,.(value = sum(value)), by = .(tech,year,var_name,con_name)]

# convert everything to future value (undiscounted)
pvfcap = fread('pvf_capital.csv')
names(pvfcap) = c('year','pvfcap')
pvfonm = fread('pvf_onm.csv')
names(pvfonm) = c('year','pvfonm')
pvf = merge(pvfcap,pvfonm)

vs = merge(vs, pvf, by='year')
vs[var_name %in% c('inv','arbitrage'), value_future := value/pvfcap]
vs[var_name %in% c('gen','opres','cap_sdbin','storage_in','cap'), value_future := value/pvfonm]

# get the net value of energy (revenue from discharging - cost of charging)
storage_in = vs[var_name == "storage_in", .(year,tech,value_in=value,value_fut_in=value_future)]
storage_out = vs[var_name == "gen", .(year,tech,value_gen=value,value_fut_gen=value_future)]
gen_val = merge(storage_in, storage_out, by = c('year','tech'))
gen_val[, value_net := value_gen + value_in]
gen_val[, value_fut_net := value_fut_gen + value_fut_in]

# add together arbitrage and net energy value
# first scale arbitrage by 1000000 (cost_scale) -- TO DO: Do this in the valuestreams script
vs[var_name == 'arbitrage', value := value/1000000]
vs[var_name == 'arbitrage', value_future := value_future/1000000]

arbitrage_val = vs[var_name == 'arbitrage', .(year, tech, value_arb=value, value_fut_arb=value_future)]
energy_val = merge(gen_val, arbitrage_val, by = c('year','tech'), all = T)
energy_val[, value := sum(value_net, value_arb, na.rm = T), by = 1:NROW(energy_val)]
energy_val[, value_future := sum(value_fut_net, value_fut_arb, na.rm = T), by = 1:NROW(energy_val)]
energy_val[, var_name := 'energy']
energy_val[, con_name := 'eq_supply_demand_balance']

vs = rbind(vs, energy_val[,.(year,tech,var_name,con_name,value,value_future)], fill = T)

# give variables useful names
var_name_map = data.table(var_name = c('energy','cap_sdbin','opres',
                                       'opres','cap','inv','storage_in'),
                          con_name = c('eq_supply_demand_balance','eq_reserve_margin','eq_opres_requirement',
                                       '_obj','_obj','_obj','eq_supply_demand_balance'),
                          var_cat = c('Value - Energy arbitrage','Value - Firm capacity','Value - Operating reserves',
                                      'Cost - Operating reserves','Cost - Fixed O&M','Cost - Capital investment','Cost - Charging'))

vs = merge(vs, var_name_map)


# ----- # 
# plot values 
# ----- #
plot_vs = function(choose_tech = c()){
  if(length(choose_tech) > 0 ){
    vsdat = vs[tech %in% choose_tech]
  }
  
  vsdat = vsdat[grepl('Value',var_cat)]
  
  ggplot(vsdat[year > 2022]) +
    geom_bar(aes(x=year, y = value_future/70*1000000, fill = var_cat), stat='identity') +
    scale_y_continuous(labels = scales::comma) +
    labs(x=NULL,y='$/MW-yr') +
    scale_fill_brewer(palette='Dark2') +
    plot_theme +
    facet_grid(var_cat~tech, scales = 'free_y')
  
}

plot_vs(c('battery_2','battery_4','battery_6'))
