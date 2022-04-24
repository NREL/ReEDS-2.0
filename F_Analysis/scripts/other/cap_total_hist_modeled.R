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

# ------------------------------------------ /
# Load data, format
# ------------------------------------------ /

# Historical
gen.hist <- fread(file.path(dir.data.hist, "Final_list.csv"), header =TRUE, sep = ",")

# Assuming for now we are not interested in looking at resource region level, just national (and potentially state/regional) level

# Capacity - Total
cap <- rgdx.alltype(gdxFileName = gdx_file, symbolName = "CAP", objectType = "variables")$DF
setDT(cap)
setnames(cap, colnames(cap), c("Technology", "Class", "State", "Resource.Region", "Year", "Capacity.Total"))
cap <- cap[, .SD, .SDcols = c("Year", "Technology", "State", "Capacity.Total")]


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

# Prescribed - retirements
pret <- rgdx.param(gdxName = gdx_file, symName = "prescribedretirements")
setDT(pret)
setnames(pret, colnames(pret), c("Year", "State", "Technology", "Type", "Capacity.Ret"))
pret <- pret[, .SD, .SDcols = c("Year", "Technology", "State", "Capacity.Ret")]

# Retirement - Total
ret <- rgdx.alltype(gdxFileName = gdx_file, symbolName = "RETIRE", objectType = "variables")$DF
setDT(ret)
setnames(ret, colnames(ret), c("Technology", "Class", "State", "Resource.Region", "Year", "Retire.Total"))
ret <- ret[, .SD, .SDcols = c("Year", "Technology", "State", "Retire.Total")]


# ------------------------------------------ /
# Merge and Manipulate Data
# ------------------------------------------ /

# Consolidate data (since they are now by state and previsouly by resource region)

cap <- cap[, ("Capacity.Total" = sum(Capacity.Total, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(cap, "V1", "Capacity.Total")

pnrsc <- pnrsc[, ("Capacity.Prescr" = sum(Capacity.Prescr, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(pnrsc, "V1", "Capacity.Prescr")

prsc <- prsc[, ("Capacity.Prescr" = sum(Capacity.Prescr, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(prsc, "V1", "Capacity.Prescr")

pret <- pret[, ("Capacity.Ret" = sum(Capacity.Ret, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(pret, "V1", "Capacity.Ret")

ret <- ret[, ("Retire.Total" = sum(Retire.Total, na.rm = T)), by = c("Year", "Technology", "State")]
setnames(ret, "V1", "Retire.Total")


# Merge data subtract prescribed from total

# Capacity 
prescribed.cap <- rbindlist(list(pnrsc, prsc), use.names = TRUE)
prescribed.cap[, Status := "Prescr.Add"]
setnames(prescribed.cap, "Capacity.Prescr", "Capacity.Total")

cap[, Status := "Endog.Add"]

cap.endog <- rbindlist(list(cap, prescribed.cap), use.names = TRUE)
setorder(cap.endog, Year, State, Technology, Status)
cap.endog[, Capacity := Capacity.Total - shift(Capacity.Total, type = "lead", fill = 0), by = c("Year", "Technology", "State")]

cap.endog <- cap.endog[Status == "Endog.Add", .SD, .SDcols = c("Year", "Technology", "State", "Capacity", "Status")]

setnames(prescribed.cap, "Capacity.Total", "Capacity")
capacity.total <-rbindlist(list(cap.endog, prescribed.cap), use.names = TRUE)
setorder(capacity.total, Year, State, Technology, Status)

# Retirements
# ASSUMING THAT RETIRE CONTAINS ONLY ENDOGENOUSLY CHOSEN ECONOMIC RETIREMENTS ... THEREFORE DIRECT MERGING POSSIBLE
pret[, Status := "Prescr.Ret"]
setnames(pret, "Capacity.Ret", "Retire.Total")

ret[, Status := "Endog.Ret"]

retirements.total <- rbindlist(list(ret, pret), use.names = TRUE)
setorder(retirements.total, Year, State, Technology, -Status)

setnames(retirements.total, "Retire.Total", "Capacity")
retirements.total[, Capacity := -Capacity,]

# Merge into one dt for total capacity (prescribed and endogenous) and retirements (prescribed and endogenous)
final.dt <- rbindlist(list(capacity.total, retirements.total), use.names = TRUE)

# ------------------------------------------ /
# Plotting Prep
# ------------------------------------------ /

# Merge tech types
final.dt[, "Tech.simp" := str_replace_all(Technology, setNames(object = plot_params$category.map$analysis.category,
                                                               nm = paste0("^", plot_params$category.map$reeds.category, "$")))]

final.dt <- final.dt[, ("V1" = sum(Capacity, na.rm = T)), by = c("Year", "Tech.simp", "State", "Status")]
setnames(final.dt, "V1", "Capacity")

# ALL OF THE BELOW IS SO THAT I CAN ARRANGE THE VARIOUS 'STATUSES' (Prescribed additions and retirements, endogenous additions and retirements)
#  INDIVIDUALLY WHILE ALSO BEING ABLE TO GET A SINGLE LEGEND AT THE END ...

plot_color_scale <- setNames(nm = sort(unique(final.dt$Status)), object = c(NA, NA, "red", NA))

final.dt.plot <- copy(final.dt)
final.dt.plot[, Tech.stat.col := do.call(paste, c(.SD, sep = "~")), .SDcols = c("Tech.simp", "Status")]

final.dt.plot$Tech.stat.col <- str_replace_all(final.dt.plot$Tech.stat.col, setNames(nm = paste0(names(plot_params$category.colors), "~Endog.Add"), 
                                                                                     object = names(plot_params$category.colors)))


plot_color_scale <- setNames(nm = sort(unique(final.dt$Status)), object = c(NA, NA, "red", NA))

plot_fill_scale <- plot_params$category.colors[rep(1:length(plot_params$category.colors), times = 4)]
names(plot_fill_scale) <- paste0(rep(names(plot_params$category.colors), times =4), rep(c("",  "~Endog.Ret",  "~Prescr.Add", "~Prescr.Ret"), each = length(plot_params$category.colors)))

final.dt.plot$Tech.stat.col <- factor(x = final.dt.plot$Tech.stat.col, levels = names(plot_fill_scale))


plot_color_scale <- setNames(nm = c("Endogenous", "Endog.Ret", "Prescribed", "Prescr.Ret"), object = c(NA, NA, "red", NA))
final.dt.plot$Status <- str_replace_all(final.dt.plot$Status, setNames(nm = sort(unique(final.dt.plot$Status)), object = names(plot_color_scale))) 

final.dt.plot$Status <- factor(x = final.dt.plot$Status, levels = names(plot_color_scale))

setorder(final.dt.plot, Status, Year, Tech.simp)
final.dt.plot.col <-  copy(final.dt.plot)

final.dt.plot.col <- final.dt.plot.col[, ("V1" = sum(Capacity, na.rm = TRUE)), by = c("Year", "Status")]

final.dt.plot.col$Year <- as.numeric(as.character(final.dt.plot.col$Year))
final.dt.plot$Year <- as.numeric(as.character(final.dt.plot$Year))

# ------------------------------------------ /
# Historical data
# ------------------------------------------ /

gen.hist <- gen.hist[, .SD, .SDcols = c("Name", "Fuel", "State", "Capacity", "DT-Comm", "DT-Ret")]

gen.hist[, `DT-Comm` := as.POSIXct(`DT-Comm`, format = "%m/%d/%Y", tz = "Indian/Maldives")]
gen.hist[, `DT-Comm` := year(`DT-Comm`),]

gen.hist[, `DT-Ret` := as.POSIXct(`DT-Ret`, format = "%m/%d/%Y", tz = "Indian/Maldives")]
gen.hist[, `DT-Ret` := year(`DT-Ret`),]

gen.hist[, Tech.Simp := str_replace_all(Fuel, setNames(nm = plot_params$category.map$reeds.category,
                                                       object = plot_params$category.map$analysis.category))]


state.nm.new <- c("Andhra_Pradesh", "Arunachal_Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi", 
                  "Goa", "Gujarat", "Haryana", "Himachal_Pradesh", "Jammu_Kashmir", "Jharkhand", "Karnataka", "Kerala", "Madhya_Pradesh",
                  "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", 
                  "Tamil_Nadu", "Telangana", "Tripura", "Uttar_Pradesh", "Uttarakhand", "West_Bengal")
state.nm.old <- c("ANDHRA PRADESH", "ARUNACHAL PRADESH", "ASSAM", "BIHAR", "CHHATTISGARH", "DELHI", "GOA", "GUJARAT", "HARYANA", 
                  "HIMACHAL PRADESH",  "JAMMU & KASHMIR", "JHARKHAND", "KARNATAKA", "KERALA", "MADHYA PRADESH", "MAHARASHTRA", "MANIPUR",
                  "MEGHALAYA", "MIZORAM", "NAGALAND", "ODISHA", "PUDUCHERRY", "PUNJAB", "RAJASTHAN", "SIKKIM", "TAMIL NADU", "TELANGANA",
                  "TRIPURA", "UTTAR PRADESH", "UTTARAKHAND", "WEST BENGAL")

gen.hist$State <- str_replace_all(gen.hist$State, setNames(nm = paste0("^", state.nm.old, "$"), object = state.nm.new))

gen.cumcap <- copy(gen.hist)
n.generators <- nrow(gen.cumcap)
gen.cumcap <- gen.cumcap[rep(seq(.N), each = c(max(gen.cumcap$`DT-Comm`) - min(gen.cumcap$`DT-Comm`))+1),]
gen.cumcap[, Year := rep(c(min(gen.cumcap$`DT-Comm`):max(gen.cumcap$`DT-Comm`)), times = n.generators),]

# If commissioning data after year in question or if retirement before year in question set capacity to 0
gen.cumcap[`DT-Comm` > Year, Capacity := 0,][`DT-Ret` <= Year, Capacity := 0,]

# Find cumulative capacity by technology and state and year
gen.cumcap <- gen.cumcap[, (Total.Cap = sum(Capacity, na.rm = TRUE)), by = c("Year", "Tech.Simp")]

# Only interested in years from 200 on (arbitrary)
gen.cumcap <- gen.cumcap[Year >= 2000 & Year < 2017,,]

gen.cumcap$Tech.Simp <- factor(x = gen.cumcap$Tech.Simp, levels = names(plot_params$category.colors))
gen.cumcap$Year <- as.numeric(gen.cumcap$Year)

# ------------------------------------------ /
# Plotting
# ------------------------------------------ /
 

x <- ggplot() +
  geom_vline(xintercept= 2016.35, linetype = "dashed", color = "darkgrey", size = 1.25)+
  geom_bar(data = final.dt.plot, aes(x = Year, y = Capacity/1000, fill = Tech.stat.col), stat = "identity", color = NA) +
  geom_bar(data = final.dt.plot.col, aes(x = Year, y = V1/1000, color = Status), stat = "identity", size = .4, fill = NA) +
  geom_bar(data = gen.cumcap, aes(x = Year, y = V1/1000, fill = Tech.Simp), stat = "identity", color = NA)+
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
  labs(title = "Historical and Projected Capacity 2000 - 2047", x = "\nYear", y = "Capacity (negative values refer to retirements) (GW)\n")+
  annotate("text", x = c(2014,2019), y=1300, label = c("Historical", "Projected"), size = 7, color = c("grey30", "firebrick"))
  
 
x

ggsave(x, filename = file.path(dir.plot, "Historical_vs_Projected_Capacity_with_Retirements.png"), device = "png", width = 16, 
       height = 10, units = "in", dpi = 330)

ggsave(x, filename = file.path(dir.plot, "Historical_vs_Projected_Capacity_with_Retirements.wmf"), device = "wmf", width = 16, 
       height = 10, units = "in", dpi = 330)




