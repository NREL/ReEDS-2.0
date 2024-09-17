# plotting capital costs of all technologies (conventional) across years

# ----------------------------------------------------------- /
# Libraries, dirs
# ----------------------------------------------------------- /

library(data.table)
library(stringr)
library(ggplot2)

setwd("D:/arose/ReEDS-2.0/F_Analysis/scripts/other")

wd <- getwd()
setwd("..")

# ----------------------------------------------------------- /
# Load data
# ----------------------------------------------------------- /

data.conv <- fread("A_Inputs/inputs/generators/data_conv.csv", sep = ",", header = TRUE)

source("F_Analysis/scripts/plot_parameters.R")

# load analysis parameters
input.params = fread("F_Analysis/data/analysis_parameters.csv")
input.params[input.params == ""] = NA
gen.order = input.params[!is.na(Gen.Order), Gen.Order]
gen.type.map = na.omit(input.params[,.(reeds.category, Type = factor(Type, levels = gen.order))])

gen.colors = input.params[!is.na(Plot.Color),Plot.Color]
names(gen.colors) = input.params[!is.na(Gen.Type),Gen.Type]

focus.regions = input.params[,Focus.Regions]

# ----------------------------------------------------------- /
# Manipulate data, plot, save plot
# ----------------------------------------------------------- /
data.conv <- data.conv[!i %in% c('CSP', 'SUBCRITICAL-OIL', 'CCGT-NAPTHA', 'SUBCRITICAL-OIL'),]
data.conv <- data.conv[, .SD, .SDcols = c("allt", "i", "cost_cap")]
data.conv <- merge(data.conv, gen.type.map, by.x = 'i', by.y = 'reeds.category', all.x = TRUE)

data.conv[, Line.Style := c("solid", "dotted", "dashed")[1:.N], by = c("allt", "Type")]

# data.conv[, Tech.stat.col := do.call(paste, c(.SD, sep = "~")), .SDcols = c("Tech.simp", "Status")]

data.conv[, Line.Style := as.factor(Line.Style),]
data.conv[, Type := as.factor(Type),]


line.type <- unique(data.conv[, .SD, .SDcols = c("i", "Line.Style")])
line.type[, Line.Style := str_replace_all(Line.Style, setNames(nm = c(1:3), object = c("solid", "dotted", "dashed")))]
col.type <- unique(data.conv[, .SD, .SDcols = c("i", "Type")])
col.type[, Type := str_replace_all(Type, gen.colors)]

col.type <- setNames(object = col.type$Type, nm = col.type$i)
line.type <- setNames(object = line.type$Line.Style, nm = line.type$i)

# create plots 

plot.unified <- ggplot(data.conv, aes(x = allt, y = cost_cap/(10e6), color = i, linetype = i))+
  geom_line(size = 1.5) + plot_theme + scale_color_manual(name = "Legend", values = col.type) + 
  scale_linetype_manual(name = "Legend", values = line.type) +
  labs(color  = "Legend", linetype = "Legend", title = "Capital Costs by Technology", x = "Year", y = "Crore/MW") +
  plot_theme +
  theme(legend.key.size = unit(1.75,"line"))+
  guides(color=guide_legend(ncol=1))+
  scale_x_continuous(labels = as.character(2017:2047), breaks = 2017:2047)


ggsave(plot = plot.unified, filename = file.path("../plots/Capital_costs_by_technology.png"), device = "png", width = 14, height = 8, units = "in", dpi = 330)
ggsave(plot = plot.unified, filename = file.path(plot.theme.dir, "graphic_outputs", "Capital_costs_by_technology.wmf"), device = "wmf", width = 14, height = 8, units = "in", dpi = 330)



plot.unified.without.battery <- ggplot(data.conv[i != "BATTERY",,], aes(x = allt, y = cost_cap/(10e6), color = i, linetype = i))+
  geom_line(size = 1.25) + plot_theme + scale_color_manual(name = "Legend", values = col.type[!grepl(names(col.type), pattern = "BATTERY")]) + 
  scale_linetype_manual(name = "Legend", values = line.type[!grepl(names(line.type), pattern = "BATTERY")]) +
  labs(color  = "Legend", linetype = "Legend", title = "Capital Costs by Technology", x = "Year", y = "Crore/MW") +
  plot_theme +
  theme(legend.key.size = unit(1.75,"line"))+
  guides(color=guide_legend(ncol=1))+
  scale_x_continuous(labels = as.character(2017:2047), breaks = 2017:2047)


ggsave(plot = plot.unified.without.battery, filename = file.path(plot.theme.dir, "graphic_outputs", "Capital_costs_by_technology_without_Battery.png"), device = "png", width = 14, height = 8, units = "in", dpi = 330)
ggsave(plot = plot.unified.without.battery, filename = file.path(plot.theme.dir, "graphic_outputs", "Capital_costs_by_technology_without_Battery.wmf"), device = "wmf", width = 14, height = 8, units = "in", dpi = 330)


# ----------------------------------------------------------- /
# Alternative, combine techs with same cost plots
# ----------------------------------------------------------- /
gen.map <- data.table(i = c(
  'BATTERY', 
  'CCGT-GAS',
  'CCGT-LNG',
  'CCGT-NAPTHA',
  'COGENERATION-BAGASSE',
  'CT-GAS',
  'DIESEL',
  'DUPV',
  'HYDRO-PONDAGE',
  'HYDRO-PUMPED',
  'HYDRO-ROR',
  'HYDRO-STORAGE',
  'NUCLEAR',
  'SUBCRITICAL-COAL',
  'SUBCRITICAL-LIGNITE',
  'SUPERCRITICAL-COAL',
  'UPV',
  'WHR',
  'WIND'), 
  Type.redux = c(
    'BESS', 
    'Gas CC',
    'Gas CC',
    'Gas CC',
    'Cogen & WHR',
    'Gas CT & Diesel',
    'Gas CT & Diesel',
    'DUPV',
    'Hydro-Pondage',
    'Hydro Pumped & Storage',
    'Hydro-ROR',
    'Hydro Pumped & Storage',
    'Nuclear',
    'Sub-Coal & Super-Coal',
    'Sub-Coal & Super-Coal',
    'Sub-Coal & Super-Coal',
    'UPV',
    'Cogen & WHR',
    'Wind')
)

category.order <- c(
  'BESS',
  'DUPV',
  'UPV',
  'Wind',
  'Gas CC', 
  'Nuclear',
  'Hydro-Pondage',
  'Hydro-ROR',
  'Gas CT & Diesel',
  'Cogen & WHR',
  'Sub-Coal & Super-Coal',
  'Hydro Pumped & Storage'
)



category.colors <-c(
  'DUPV' = "orange",
  "BESS" = "coral1",
  "Nuclear" = "mediumpurple3",
  "Hydro-Pondage" = "lightblue",
  "Hydro-ROR" = "lightblue",
  "Hydro Pumped & Storage" = "darkblue",
  "Sub-Coal & Super-Coal" = "gray 50",
  "Wind" = "steelblue3",
  "Cogen & WHR" = "peru",
  "UPV" = "orange",
  "Gas CC" = "darkolivegreen4",
  "Gas CT & Diesel" ="violetred2"
)

Line.Style <-c(
  'DUPV' = "dotted",
  "BESS" = "solid",
  "Nuclear" = "solid",
  "Hydro-Pondage" = "solid",
  "Hydro-ROR" = "dotted",
  "Hydro Pumped & Storage" = "solid",
  "Sub-Coal & Super-Coal" = "solid",
  "Wind" = "solid",
  "Cogen & WHR" = "solid",
  "UPV" = "solid",
  "Gas CC" = "solid",
  "Gas CT & Diesel" ="solid"
)

data.conv2 <- data.conv[!i %in% c('CSP', 'SUBCRITICAL-OIL'),]
data.conv2 <- data.conv2[, .SD, .SDcols = c("allt", "i", "cost_cap")]
data.conv2 <- merge(data.conv2, gen.map, by = 'i', all.x = TRUE)

# remove duplicate rows
data.conv2 <- data.conv2[,.(allt, cost_cap, Type.redux)]
data.conv2 <- data.conv2[!duplicated(data.conv2)]


# factor and add colors
data.conv2[,Type.redux := factor(Type.redux, levels = category.order)]

# create plots 

plot.unified <- ggplot(data.conv2, aes(x = allt, y = cost_cap/(10e6), color = Type.redux, linetype = Type.redux))+
  geom_line(size = 1.25) + plot_theme + scale_color_manual(name = "Legend", values = category.colors) + 
  scale_linetype_manual(name = "Legend", values = Line.Style) +
  labs(color  = "Legend", linetype = "Legend", x = "Year", y = "Crore/MW") +
  plot_theme +
  theme(legend.key.size = unit(1.75,"line"))+
  guides(color=guide_legend(ncol=1))+
  scale_x_continuous(breaks=seq(2017, 2047, 2)) +
  theme(legend.position="bottom")+
  guides(col = guide_legend(nrow = 2))

plot.unified

ggsave(plot = plot.unified, filename = file.path("F_Analysis/plots/Capital_costs_by_technology_redux.png"), device = "png", width = 8, height = 5, units = "in", dpi = 330)
ggsave(plot = plot.unified, filename = file.path(plot.theme.dir, "graphic_outputs", "Capital_costs_by_technology_redux.wmf"), device = "wmf", width = 14, height = 8, units = "in", dpi = 330)


# ----------------------------------------------------------- /
# Cost scenarios plot
# ----------------------------------------------------------- /

#redo with gradient colors rather than different linestyles


costs = fread('F_Analysis/data/cost_scenarios.csv',header = TRUE)

scenario = c('Base','10%','20%','30%','40%','50%')
Type = c('UPV','DUPV','Wind','BESS')

category.colors <-c(
  'Base' = "#253494",
  "20%" = "#41b6c4",
  "30%" = "#7fcdbb",
  "40%" = "#c7e9b4",
  "50%" = "#ffffcc",
  "10%" = "dodgerblue2"
)

# factor and add colors
costs[,Scenario := factor(Scenario, levels = scenario)]

plot.costs <- ggplot(costs, aes(x = Year, y = Cost/(10e6),  color = Scenario))+
  geom_line(size = 1.0) + plot_theme + 
  scale_color_manual(name = "Legend", values = category.colors) + 
  #scale_linetype_manual(name = "Legend", values = Line.Style) +
  labs(color  = "Legend", linetype = "Legend", x = "Year", y = "Crore/MW") +
  plot_theme +
  theme(legend.key.size = unit(1.75,"line"))+
  guides(color=guide_legend(ncol=1))+
  scale_x_continuous(breaks=seq(2017, 2047, 3)) +
  theme(legend.position="bottom")+
  guides(col = guide_legend(nrow = 1)) +
  facet_wrap(~Type, scales = "free_y")

plot.costs

ggsave(plot = plot.costs, filename = file.path("F_Analysis/plots/cost_scenarios.png"), device = "png", width = 8, height = 5, units = "in", dpi = 330)

