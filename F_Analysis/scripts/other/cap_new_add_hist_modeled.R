# Attempting to recreate a capacity plot which tracks historical to modeled capacity

# ------------------------------------------ /
# Library, dir, user func. sourcing
# ------------------------------------------ /

setwd("D:/tbowen/capexp-india")

dir.gdx.data <- "ReEDS-2.0/gdxfiles"
dir.func <- "ReEDS-2.0/solution_processing"
dir.data.hist <- "C:/Users/tbowen/Desktop/"
dir.plot <- "ReEDS-2.0/solution_processing/graphic_outputs"

pacman::p_load(data.table, ggplot2, stringr, lubridate, gdxrrw)

source(file.path(dir.func, "gdxr_functions.r"))

gdx_file <- list.files(dir.gdx.data, pattern = ".gdx", full.names = TRUE)
gdx_file <- grep(gdx_file, pattern = "inputs.gdx$", perl = T, value = T, invert = T)

# Choose appropriate gdx file to plot here
gdx_file <- gdx_file[1]


# Load plot params
source(file.path(dir.func, "plot_parameters.R"))
plot_params <- callplotparams()

# For converting tech types
tech.change <- setNames(object = plot_params$category.map$analysis.category, 
                        nm = paste0("^", plot_params$category.map$reeds.category, "$"))

# for converting states
state.nm.new <- c("Andhra_Pradesh", "Arunachal_Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi", 
                  "Goa", "Gujarat", "Haryana", "Himachal_Pradesh", "Jammu_Kashmir", "Jharkhand", "Karnataka", "Kerala", "Madhya_Pradesh",
                  "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", 
                  "Tamil_Nadu", "Telangana", "Tripura", "Uttar_Pradesh", "Uttarakhand", "West_Bengal")
state.nm.old <- c("ANDHRA PRADESH", "ARUNACHAL PRADESH", "ASSAM", "BIHAR", "CHHATTISGARH", "DELHI", "GOA", "GUJARAT", "HARYANA", 
                  "HIMACHAL PRADESH",  "JAMMU & KASHMIR", "JHARKHAND", "KARNATAKA", "KERALA", "MADHYA PRADESH", "MAHARASHTRA", "MANIPUR",
                  "MEGHALAYA", "MIZORAM", "NAGALAND", "ODISHA", "PUDUCHERRY", "PUNJAB", "RAJASTHAN", "SIKKIM", "TAMIL NADU", "TELANGANA",
                  "TRIPURA", "UTTAR PRADESH", "UTTARAKHAND", "WEST BENGAL")

state.change <- setNames(nm = paste0("^", state.nm.old, "$"), object = state.nm.new)
rm(list = c("state.nm.new", "state.nm.old"))


# ------------------------------------------ /
# Load data, format
# ------------------------------------------ /

# Historical
gen.hist <- fread(file.path(dir.data.hist, "Final_list.csv"), header =TRUE, sep = ",")

# Assuming for now we are not interested in looking at resource region level, just national (and potentially state/regional) level

# Prescribed - Non-rsc
pnrsc <- rgdx.param(gdxName = gdx_file, symName = "prescribednonrsc")
setDT(pnrsc)
setnames(pnrsc, colnames(pnrsc), c("Year", "Technology", "State", "Type", "Capacity.Prescr"))
pnrsc <- pnrsc[, .SD, .SDcols = c("Year", "Technology", "State", "Capacity.Prescr")]

# Prescribed - rsc
prsc <- rgdx.param(gdxName = gdx_file, symName = "prescribedrsc")
setDT(prsc)
setnames(prsc, colnames(prsc), c("Year", "Technology", "State", "Resource.Region", "Type", "Capacity.Prescr"))
prsc <- prsc[, .SD, .SDcols = c("Year", "Technology", "State", "Capacity.Prescr")]
# Wind dupv and upv need to be removed as they are already included in inv_rsc (hydro is not)
prsc <- prsc[!(Technology %in% c("WIND", "DUPV", "UPV")),,]


# Prescribed - retirements
pret <- rgdx.param(gdxName = gdx_file, symName = "prescribedretirements")
setDT(pret)
setnames(pret, colnames(pret), c("Year", "State", "Technology", "Type", "Capacity.Ret"))
pret <- pret[, .SD, .SDcols = c("Year", "Technology", "State", "Capacity.Ret")]

# Retirement - Endog
ret <- rgdx.alltype(gdxFileName = gdx_file, symbolName = "RETIRE", objectType = "variables")$DF
setDT(ret)
setnames(ret, colnames(ret), c("Technology", "Class", "State", "Resource.Region", "Year", "Retire.Total"))
ret <- ret[, .SD, .SDcols = c("Year", "Technology", "State", "Retire.Total")]

# Capacity investments
capinv <- rgdx.param(gdxName = gdx_file, symName = "capinv")
setDT(capinv)
setnames(capinv, colnames(capinv), c("Technology", "State", "Year", "Capacity.Add"))
capinv <- capinv[, .SD, .SDcols = c("Year", "Technology", "State", "Capacity.Add")]

# ------------------------------------------ /
# Historical data
# ------------------------------------------ /

gen.hist <- gen.hist[, .SD, .SDcols = c("Name", "Fuel", "State", "Capacity", "DT-Comm", "DT-Ret")]

gen.hist[, `DT-Comm` := as.POSIXct(`DT-Comm`, format = "%m/%d/%Y", tz = "Indian/Maldives")]
gen.hist[, `DT-Comm` := year(`DT-Comm`),]

gen.hist[, `DT-Ret` := as.POSIXct(`DT-Ret`, format = "%m/%d/%Y", tz = "Indian/Maldives")]
gen.hist[, `DT-Ret` := year(`DT-Ret`),]

gen.hist[, Tech.Simp := str_replace_all(Fuel, tech.change),]
gen.hist[, State := str_replace_all(State, state.change),]

gen.hist <- gen.hist[, (V1 = sum(Capacity, na.rm = T)), by = c("Tech.Simp", "State", "DT-Comm")][`DT-Comm` >= 2000 & `DT-Comm` <= 2016,,]
setnames(gen.hist, c("DT-Comm", "V1"), c("Year", "Capacity"))


# ------------------------------------------ /
# Merge and Manipulate Data
# ------------------------------------------ /

# Consolidate data (since they are now by state and previsouly by resource region)
# Also go ahead and change technology types

capinv[, Technology := str_replace_all(Technology, tech.change)]
capinv <- capinv[, ("Capacity.Total" = sum(Capacity.Add, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(capinv, "V1", "Capacity.Add")

pnrsc[, Technology := str_replace_all(Technology, tech.change)]
pnrsc <- pnrsc[, ("Capacity.Prescr" = sum(Capacity.Prescr, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(pnrsc, "V1", "Capacity.Prescr")

prsc[, Technology := str_replace_all(Technology, tech.change)]
prsc <- prsc[, ("Capacity.Prescr" = sum(Capacity.Prescr, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(prsc, "V1", "Capacity.Prescr")

pret[, Technology := str_replace_all(Technology, tech.change)]
pret <- pret[, ("Capacity.Ret" = sum(Capacity.Ret, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(pret, "V1", "Capacity.Ret")

ret[, Technology := str_replace_all(Technology, tech.change)]
ret <- ret[, ("Retire.Total" = sum(Retire.Total, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(ret, "V1", "Retire.Total")


 # Merge data

# Capacity 
# prescribed.cap <- rbindlist(list(pnrsc, prsc), use.names = TRUE)
# prescribed.cap[, Status := "Prescr.Add"]
# setnames(prescribed.cap, "Capacity.Prescr", "Capacity.Add")

pnrsc[, Status := "Prescr.NRSC.Add"]
prsc[, Status := "Prescr.RSC.Add"]
prescribed.cap <- rbindlist(list(pnrsc, prsc), use.names = TRUE)
setnames(prescribed.cap, "Capacity.Prescr", "Capacity.Add")

capinv[, Status := "Endog.Add"]


# It Appears necessary to remove rsc-prescribed additions from capinv - NEED TO BRING THIS UP WITH ILYA
cap.new <- rbindlist(list(capinv, prescribed.cap), use.names = TRUE)
View(data.table::dcast(cap.new, formula = "Year+Technology+State~Status", value.var = "Capacity.Add"))
# View(data.table::dcast(cap.new, formula = "Year+Technology+State~Status", value.var = "Capacity.Add"))

# Retirements
# ASSUMING THAT RETIRE CONTAINS ONLY ENDOGENOUSLY CHOSEN ECONOMIC RETIREMENTS ... THEREFORE DIRECT MERGING POSSIBLE
pret[, Status := "Prescr.Ret"]
setnames(pret, "Capacity.Ret", "Retire.Total")

ret[, Status := "Endog.Ret"]

retirements.total <- rbindlist(list(ret, pret), use.names = TRUE)
setorder(retirements.total, Year, State, Technology, -Status)
setnames(retirements.total, "Retire.Total", "Capacity.Add")
retirements.total[, Capacity.Add := -Capacity.Add,]

# Merge into one dt for total capacity (prescribed and endogenous) and retirements (prescribed and endogenous)
final.dt <- rbindlist(list(cap.new, retirements.total), use.names = TRUE)

# merge statuses for prescribed additions
final.dt[Status %in% c("Prescr.NRSC.Add", "Prescr.RSC.Add"), Status := "Prescr.Add",]

# ------------------------------------------ /
# Plotting Prep
# ------------------------------------------ /

# ALL OF THE BELOW IS SO THAT I CAN ARRANGE THE VARIOUS 'STATUSES' (Prescribed additions and retirements, endogenous additions and retirements)
#  INDIVIDUALLY WHILE ALSO BEING ABLE TO GET A SINGLE LEGEND AT THE END ...

final.dt.plot <- copy(final.dt)
final.dt.plot[, Tech.stat.col := do.call(paste, c(.SD, sep = "~")), .SDcols = c("Technology", "Status")]

final.dt.plot$Tech.stat.col <- str_replace_all(final.dt.plot$Tech.stat.col, setNames(nm = paste0(names(plot_params$category.colors), "~Endog.Add"), 
                                                                                     object = names(plot_params$category.colors)))


plot_fill_scale <- plot_params$category.colors[rep(1:length(plot_params$category.colors), times = 4)]
names(plot_fill_scale) <- paste0(rep(names(plot_params$category.colors), times =4), rep(c("",  "~Endog.Ret",  "~Prescr.Add", "~Prescr.Ret"), each = length(plot_params$category.colors)))

final.dt.plot$Tech.stat.col <- factor(x = final.dt.plot$Tech.stat.col, levels = names(plot_fill_scale))


plot_color_scale <- setNames(nm = c("Endogenous", "Endog.Ret", "Prescribed", "Prescr.Ret"), object = c(NA, NA, "red", NA))
final.dt.plot$Status <- str_replace_all(final.dt.plot$Status, setNames(nm = sort(unique(final.dt.plot$Status)), object = names(plot_color_scale))) 

final.dt.plot$Status <- factor(x = final.dt.plot$Status, levels = names(plot_color_scale))

setorder(final.dt.plot, Status, Year, Technology)
final.dt.plot.col <-  copy(final.dt.plot)

final.dt.plot.col <- final.dt.plot.col[, ("V1" = sum(Capacity.Add, na.rm = TRUE)), by = c("Year", "Status")]

final.dt.plot.col$Year <- as.numeric(as.character(final.dt.plot.col$Year))
final.dt.plot$Year <- as.numeric(as.character(final.dt.plot$Year))

final.dt.plot.test <- copy(final.dt.plot)
final.dt.plot.test <- final.dt.plot.test[, (Capacity.Add = sum(Capacity.Add, na.rm = T)), by = c("Year", "Technology", "Status", "Tech.stat.col")]
setnames(final.dt.plot.test, "V1", "Capacity.Add")

# ------------------------------------------ /
# Plotting
# ------------------------------------------ /


x <- ggplot() +
  geom_vline(xintercept= 2016.35, linetype = "dashed", color = "darkgrey", size = 1.25)+
  geom_bar(data = final.dt.plot, aes(x = Year, y = Capacity.Add, fill = Tech.stat.col), stat = "identity", color = NA) +
  geom_bar(data = gen.hist, aes(x = Year, y = Capacity, fill = Tech.Simp), stat = "identity", color = NA)+
  geom_bar(data = final.dt.plot.col, aes(x = Year, y = V1, color = Status), stat = "identity", size = .75, fill = NA) +
  scale_fill_manual("Technology", values = plot_fill_scale, breaks =names(plot_params$category.colors)) + 
  scale_color_manual("Status", values = plot_color_scale, breaks = c("Endogenous", "Prescribed"))+
  scale_x_continuous(breaks = 2000:2047, labels = as.character(2000:2047), expand = c(.01,.01)) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 12),
        axis.text.y = element_text(size = 12),
        axis.title.x = element_text(size = 14),
        axis.title.y = element_text(size = 14),
        title = element_text(size = 14),
        legend.title = element_text(size = 14),
        legend.text = element_text(size = 10),
        panel.grid.major.x = element_blank())+
  labs(title = "New Capacity (Historical and Projected) 2000 - 2047", x = "\nYear", y = "Capacity Additions (negative values refer to retirements) (MW)\n")+
  annotate("text", x = c(2013,2020), y=-15000, label = c("Historical", "Projected"), size = 7, color = c("grey30", "firebrick"))


x

ggsave(x, filename = file.path(dir.plot, "Historical_vs_Projected_New_Capacity_Additions_with_Retirements.png"), device = "png", width = 16,
       height = 10, units = "in", dpi = 330)

ggsave(x, filename = file.path(dir.plot, "Historical_vs_Projected_New_Capacity_Additions_with_Retirements.wmf"), device = "wmf", width = 16,
       height = 10, units = "in", dpi = 330)




