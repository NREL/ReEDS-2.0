#============================================
# Annualized capacity payment for existing power plants
#============================================

# Yinong Sun, 12/30/2019, adapted from Max Brown's script from 20180124
# This file is used to calculated annualized capacity payment for pre-2010 (i.e. existing) power plants.
# Output of this script are 1)cappayments.csv and 2)cappayments_ba.csv files located in the same folder as this script (repo/inputs/capacitydata), and will be copied to each run folder after running scenarios;
# Once the two files are already created, this file doesn't need to be re-run again. We keep this file in the repo in case we want to find how the cappayment csv files are calcualted.

library(data.table)
library(dplyr)
library(reshape2)
library(gdxrrw)
igdx("c:\\gams\\win64\\24.7")

#WriteHintage.R
Args=list()
#WriteHintage.R
# localrepo <- "D:/ReEDS_YSun/ReEDS-2.0/"
setwd(localrepo)
genunitfile='inputs\\capacitydata\\ReEDS_generator_database_final_EIA-NEMS.csv'
retscen = "NukeRefRetireYear"

# Originally we were using social discount rate d and the corresponding formula below to annualize investment;  We should now we the crf numbers from model inputs
# When we use social discount rate to calculate:
# loan_length = 20 #years of loan length and interest rate to match 2010 assumptions from reeds
# interest_rate = 0.05
# d = 0.05 # interest rate
# crf = d*(1+d)**20/((1+d)**20 - 1)
# Now we use crf from inputs
crf <- read.csv(paste0(runfolder,"inputs_case/crf.csv"))
colnames(crf) <- c("year","crf")
crf <- crf[1,2]

#load in the full unit data from genunitfile
indat = as.data.frame(read.csv(genunitfile))

#need to assign w_fom as the sum of all fixed cost categories, simiar for w_vom

ad = indat[,c("tech","pca","ctt","resource_region","cap",retscen,"Commercial.Online.Year.Quarter","IsExistUnit",
              "Fully.Loaded.Tested.Heat.Rate.Btu.kWh...Modeled","Plant.NAICS.Description","W_VOM","W_FOM")]

ad$IsExistUnit = as.character(ad$IsExistUnit)


colnames(ad) = c("TECH","PCA","ctt","resource.region","Summer.capacity","RetireYear",
                 "Solve.Year.Online","EXIST","HR","NAICS","VOM","FOM")

#only need relevant info
findat = ad[,c("TECH","PCA","Solve.Year.Online","EXIST")]

#Read in capital costs
costs = as.data.frame(rgdx.param("inputs\\capacitydata\\cost_cap.gdx","cost_cap"))
colnames(costs) = c("TECH","year","cost")
capcost = subset(costs,year==2010)
capcost = capcost[,c("TECH","cost")]


alldat = merge(findat,capcost)

alldat$onlineyear = as.numeric(as.character(substr(alldat$Solve.Year.Online,1,4)))

#only care about plants that exist before the modeled period
alldat = subset(alldat,onlineyear<2010)
alldat = subset(alldat,EXIST==TRUE)

modeledyears = seq(2010,2050,1)

alldat[,c(paste0(modeledyears))] = 0

for(i in modeledyears){
  #calculate the age of the plant 
  alldat[,c(paste0(i))] = as.numeric(i-alldat$onlineyear)
  #don't care about units that have not come online yet  
  alldat[alldat[,c(paste0(i))]<0,c(paste0(i))] = 0
  #don't care about units who have paid off their loans
  alldat[alldat[,c(paste0(i))]>loan_length,c(paste0(i))] = 0
  #now set up a boolean that will distinguish whether or not the loan is in repayment  
  alldat[alldat[,c(paste0(i))]>0,c(paste0(i))] = 1
  #loan payment is simply the crf * the original cost of capacity (here assuming it to be the 2010 amount)  
  alldat[,c(paste0(i))] = alldat[,c(paste0(i))] * crf * alldat$cost
}


head(alldat)
mdat = alldat[,c("PCA",modeledyears)]
mdat = melt(mdat,id=c("PCA"))

mdat = aggregate(mdat$value,by=list(mdat$PCA,mdat$variable),FUN=sum)

#note the use of '*' to have gams avoid trying to load in the first row
colnames(mdat) = c("*r","t","value")

mdat_national <- aggregate(value ~ t, mdat, sum)
mdat_national$value <- mdat_national$value/10^9 #in billion $
colnames(mdat_national) <- c("year","existingcap")

mdat <- merge(expand.grid('*r' = sprintf("p%s",seq(1:134)), "t" = seq(2010, 2070)), mdat, by = c("*r","t"), all.x = T)
mdat[is.na(mdat)] <- 0
mdat$value <- mdat$value/10^9 #in billion $

#Write the two csv files as outputs:
#National annualized capacity payment:
# write.csv(mdat_national,"inputs\\capacitydata\\cappayments.csv",row.names=FALSE,quote=FALSE)
#BA-level annualized capacity payment:
# write.csv(mdat,"inputs\\capacitydata\\cappayments_ba.csv",row.names=FALSE,quote=FALSE)
