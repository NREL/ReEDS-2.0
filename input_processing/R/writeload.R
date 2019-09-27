sink("gamslog.txt",append=TRUE)

library(gdxrrw)
library(reshape2)


print("Beginning calculation of inputs\\writeload.R")

if(!exists("Args")) Args=commandArgs(TRUE)

#writeload.R
# Args=list()
# Args[1]="C:\\Git\\ReEDS-2.0\\"
# Args[3]="AEO_2018_reference"

setwd(paste0(Args[1],"inputs\\loaddata"))

demandscen = Args[2]
outdir = Args[3]

################
#load projection
################

demand = read.csv(paste0("demand_",demandscen,".csv"), check.names = F)


###########################################
#planning reserve margin by region and time
###########################################
prm_ann = read.csv("Annual_PRM.csv")


prm_ann$i = gsub("nr","nrn",prm_ann$i)
prm_ann$i = gsub("new","",prm_ann$i)
prm_ann = dcast(prm_ann,i~j,value.var="value")


# setwd(".\\loaddata\\")
print(paste("Writing load and prm parameters to:",outdir))
write.csv(demand,paste0(outdir,"load_multiplier.csv"),quote=FALSE,row.names=FALSE)
write.csv(prm_ann,paste0(outdir,"prm_annual.csv"),quote=FALSE,row.names=FALSE)







