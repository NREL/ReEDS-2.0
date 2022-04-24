# create regional load multipliers

pacman::p_load(data.table)

baload = fread("../demand/load.csv", header = F)

# state region map
r.rto.map = fread("../sets/hierarchy_set.csv", header = F)

baload = merge(baload, r.rto.map, by = 'V1')

rload = baload[,.(demand = sum(V4)), by = .(Year = V3.x, rto = V2.y)]

rload[,scale := demand/demand[Year == 2017], by = rto]

rload.scale = dcast(rload, formula = rto ~ Year, value.var = "scale", drop = T)

write.csv(rload.scale, file = "regional_load_multipliers.csv", row.names = F, quote = F)

# superpeak timeslices

ts.h.map = fread('../../../Data/Load/output/ts_h_map_5szn.csv')

hours = fread('../demand/hours.csv')

baload = merge(baload, ts.h.map, by.x = 'V2', by.y = 'h')

baload[,season := tstrsplit(time_slice, "_")[1]]

baload[,tot.demand := sum(V4), by = .(time_slice, V3)]

superpeak = baload[V3 == 2017]

superpeak = superpeak[,.(timeslice = V2[tot.demand == max(tot.demand)]), by = season]

superpeak = unique(superpeak)

superpeak = merge(superpeak, hours, by.x = 'timeslice', by.y = 'V1')

setnames(superpeak, 'V2', 'hours')

superpeak[,season := NULL]

superpeak[,true_timeslice := timeslice]

write.csv(superpeak, 'superpeak_hours.csv', row.names = F, quote = F)
