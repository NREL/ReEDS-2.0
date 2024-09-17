# Capacity plot that tracks historical to modeled capacity

plot_hist_new_cap = function(){
# ------------------------------------------ /
# Load data
# ------------------------------------------ /

scenario.filter = 'Base'

# Load historical generator additions and retirements
hist.cap = fread("data/India_gens_historic.csv", header =TRUE, sep = ",")

n.generators = nrow(hist.cap)

# Create full time series for each generator (I would do this differently)
hist.cap = hist.cap[rep(seq(.N), each = c(max(hist.cap$Comm) - min(hist.cap$Comm))+1),]
hist.cap[, Year := rep(c(min(hist.cap$Comm):max(hist.cap$Comm)), times = n.generators),]

# If commissioning data after year in question or if retirement before year in question set capacity to 0
hist.cap[Comm > Year, Capacity := 0,][Ret <= Year, Capacity := 0,]

# Find cumulative capacity by technology and state and year
hist.cap <- hist.cap[, (Total.Cap = sum(Capacity, na.rm = TRUE)), by = c("Year", "Type")]

# Only interested in years from 2000 to 2017 
hist.cap <- hist.cap[Year >= 2000 & Year < 2017,,]

# based on NEP Exhibit 2.11 pg 79
hist.re = data.table(Year = c(2016,2016), 
                     Type = c("Wind", "Solar PV"),
                     V1 = c(32279.77,12288.83))

hist.cap = rbind(hist.cap, hist.re)

hist.cap[Year == 2016 & Type == "Other", V1 := V1 + 4379.86]

hist.cap[,Type := factor(Type, levels = gen.order)]

# new capacity, including endogenous and prescribed retirements
new.cap = cap[scenario == scenario.filter, .(capacity = sum(capacity)), by = .(Type, Year)]
new.cap = new.cap[order(Type, Year)]

# endogenous retirements
new.cap[,retire := capacity - shift(capacity,1,type = 'lag'), by = Type]

new.cap[retire >= 0, retire := 0]

new.cap = melt(new.cap, id.vars = c('Year','Type'), measure.vars = c('capacity','retire'),
               value.name = 'capacity')
new.cap = new.cap[capacity != 0]
new.cap[,variable := NULL]

# identify prescribed capacity additions and retirements
pull_gdx_data(type = 'param', gdx.name = 'capacity_exog', r.name = 'exog')
setnames(exog, c('i1','i3','i5','value'),c('Category','State','Year','capacity_exog'))
exog[,Year := as.numeric(as.character(Year))]

exog = merge(exog, gen.type.map, by.x = 'Category', by.y = 'reeds.category')

exog = exog[scenario == scenario.filter,.(cap.exog = sum(capacity_exog)), by = .(Type, Year)]

exog[,diff := cap.exog - shift(cap.exog,1, type = 'lag'), by = 'Type']

# add RE
exog.re = prescr.rsc[scenario %in% scenario.filter & Type != 'Hydro',
                     .(diff = sum(prescribed)), by = .(Type, Year)]

exog = rbind(exog, exog.re, fill = T)

new.cap = merge(new.cap, exog, by = c('Type','Year'), all.x = T)

new.cap[diff > 0 & capacity > 0,capacity := capacity - diff]

setnames(new.cap,c('capacity','diff'),c('Endogenous','Prescribed'))
new.cap = melt(new.cap, id.vars = c('Type','Year'), measure.vars = c('Endogenous','Prescribed'))
new.cap = new.cap[!is.na(value)]
new.cap = new.cap[value != 0]

# ------------------------------------------ /
# Plotting
# ------------------------------------------ /
 
p = ggplot() +
  geom_vline(xintercept= 2017, linetype = "dashed", color = "darkgrey", size = 1.25)+
  geom_bar(data = new.cap, aes(x = Year, y = value/1000, fill = Type), stat = "identity") +
  geom_bar(data = hist.cap, aes(x = Year, y = V1/1000, fill = Type), stat = "identity")+
  scale_fill_manual("Type", values = gen.colors, breaks = gen.order) + 
  scale_color_manual("Status", values = c(NA,'red'), breaks = c("Endogenous", "Prescribed"))+
  scale_x_continuous(breaks = seq(from =1999, to= 2047, by = 2),
                     expand = c(.01,.01)) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1, size = large.text.size),
        axis.text.y = element_text(size = large.text.size),
        axis.title.x = element_text(size = large.text.size),
        axis.title.y = element_text(size = large.text.size),
        legend.title = element_blank(),
        legend.text = element_text(size = small.text.size, margin = margin(l = 5, r = 5)),
        legend.key = element_rect(fill = "grey95", colour = "white"), legend.key.size = unit(1.2, "lines"),
        panel.grid.major.x = element_blank())+
  labs(x=NULL, y = "Installed Capacity and Retirements (GW)")+
  annotate("text", x = c(2010,2024), y=1300, label = c("Historic", "Projected"), size = 5, color = c("grey30", "firebrick"))
 
return(p) 
}



