# compare curtailment values from REFlow with back of envelop R values


pacman::p_load(data.table, readxl,ggplot)

# load packages, data and plotting functions
if(!require("pacman")){
  install.packages('devtools')
  require(remotes)
  install_version("pacman", version = "0.4.6", repos = "http://cran.us.r-project.org")
}

pacman::p_load(gdxrrw, ggplot2, data.table, maptools, mapproj, RColorBrewer, 
               rgdal, rgeos, scales, stringr, rmarkdown, gdata, zoo, viridis)



#--------------------------#
# look at changes in CV and Curtailment across iterations----
#--------------------------#

# read in 'cv' table created in query_gdx_files
cv.iter <- fread('data/cv_iter.csv')
cv.iter <- cv.iter[!Technology == 'CSP',]

# look at change in cv by season and tech
cv.mean <- cv.iter[,mean(cap.value), by = c('Technology','season','Year','iteration','scenario')]

cv.plot<- cv.mean[scenario == 'LowSolar',]
p.cv.mean = ggplot(cv.plot, aes(x = Year, y = V1, group = iteration, color = iteration)) + 
  geom_line() +
  geom_point() +
  labs(y = 'Mean Capacity Value', x = NULL) +
  #scale_color_discrete(breaks=seq(1,6, 1),
  #                       guide = guide_legend()) +
  #scale_color_distiller(palette = "Blues")+
  #plot_theme +
  theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
  facet_grid(Technology~season, scales = 'free')
p.cv.mean


# look only at cases where CV changes between iterations
cv.var <- cv.iter[,var:= var(cap.value), by = c('Technology','r','season','Year','scenario')]
cv.var <- cv.var[!var <= 0.00001,]


# get mean by state, season, technology, Year, and iteration
cv.var <- cv.var[,mean(cap.value), by = c('Technology','season','Year','iteration','scenario')]

cv.var.plot <- cv.var[scenario == 'LowSolar',]

p.cv.var = ggplot(cv.var.plot, aes(x = Year, y = V1, group = iteration, color = iteration)) + 
  geom_line() +
  geom_point() +
  labs(y = 'Mean Capacity Value', x = NULL) +
  #scale_color_discrete(breaks=seq(1,6, 1),
  #                       guide = guide_legend()) +
  #scale_color_distiller(palette = "Blues")+
  #plot_theme +
  theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
  facet_grid(season~Technology, scales = 'free')
p.cv.var

# --------- curtailment ---------------- #
# read in 'cv' table created in query_gdx_files
curt.iter <- fread('data/curt_iter.csv')

# map timeslices
curt.iter <- merge(curt.iter, ts.map, by.x = 'Timeslice',by.y = 'h')

# look at change in cv by timeslice
curt.mean <- curt.iter[,mean(curtailment), by = c('Year','iteration','time_slice','scenario')]

# remove istances where curtailment = 0
curt.mean[,avg:= mean(V1), by = c('time_slice','Year','scenario')]
curt.mean <- curt.mean[!avg <= 0.005]

curt.mean.plot <- curt.mean[scenario == 'LowSolar',]

p.curt.mean = ggplot(curt.mean.plot, aes(x = Year, y = V1, group = iteration, color = iteration)) + 
  geom_line() +
  geom_point() +
  labs(y = 'Mean Curtailment (%)', x = NULL) +
  #scale_color_discrete(breaks=seq(1,6, 1),
  #                       guide = guide_legend()) +
  #scale_color_distiller(palette = "Blues")+
  #plot_theme +
  theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
  facet_wrap(~time_slice, scales = 'free')
p.curt.mean

# total annual curtailment

curt.tot <- merge(curt.iter, hours[,.(h,hours,scenario)], by.x = c('Timeslice','scenario'), by.y = c('h','scenario'))
curt.tot[,wgt:= curtailment*hours]
curt.tot <- curt.tot[,sum(wgt)/8760, by = c('Year','iteration','scenario')]

curt.tot.plot <- curt.tot[scenario == 'LowSolar',]

p.curt.tot = ggplot(curt.tot.plot, aes(x = Year, y = V1, group = iteration, color = iteration)) + 
  geom_line() +
  geom_point() +
  labs(y = 'Mean Curtailment (%)', x = NULL) +
  #scale_color_discrete(breaks=seq(1,6, 1),
  #                       guide = guide_legend()) +
  #scale_color_distiller(palette = "Blues")+
  #plot_theme +
  theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
  facet_wrap(~scenario, scales = 'free')
p.curt.tot



#--------------------------#
# look at changes in RE capacity across iterations----
#--------------------------#

# based on 'cap' table created in query_gdx_files
# look at RE technologies and high RE states
cap.re <- cap[Technology %in% c('UPV','WIND') &
                State %in% c('Andhra_Pradesh', 'Gujarat','Karnataka','Rajasthan','Tamil_Nadu'),]

p = ggplot(cap.re, aes(x = Year, y = capacity, group = scenario, color = scenario)) + 
  geom_line() +
  geom_point() +
  labs(y = 'Installed Capacity (MW)', x = NULL) +
  #scale_color_discrete(breaks=seq(1,6, 1),
  #                       guide = guide_legend()) +
  #scale_color_distiller(palette = "Blues")+
  #plot_theme +
  theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
  facet_grid(State~Technology)
p
