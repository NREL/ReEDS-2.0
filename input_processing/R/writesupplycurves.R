sink("gamslog.txt",append=TRUE)

library(reshape2)
library(gdxrrw)
library(data.table)

if(!exists("Args")) Args=commandArgs(TRUE)

#combinedat.R
# Args=list()
# Args[1]="F:\\GamsProjectWesley\\ReEDS-2.0\\"
# Args[2]="C:\\GAMS\\win64\\24.7\\"
# Args[3]="ExistingUnits_EIA-NEMS.gdx"
# Args[4]=0
 #Args[5]=2018
# Args[6]='F:\\GamsProjectWesley\\ReEDS-2.0\\runs\\Test3_ref_seq\\'
# Args[7]='BAU'

igdx(paste(Args[2]))
gdxin = file.path(Args[1],"inputs","capacitydata",Args[3])
setwd(file.path(Args[1],"inputs",sep=""))
deduct = Args[4]
supplycurvefile = as.numeric(as.character(Args[5]))
outdir = Args[6]
geoscen = Args[7]
gdxPHS = file.path(Args[1],"inputs","supplycurvedata","PHSsupplycurvedata.gdx")
gdxBio = file.path(Args[1],"inputs","supplycurvedata","Biosupplycurvedata.gdx")

#windfile = 1
#deduct = 0
#gdxin = "d:\\max\\r2_naris\\inputs\\capacitydata\\ExistingUnits_EIA-NEMS.gdx"
#setwd("d:\\max\\r2_naris\\inputs\\")
#gdxbase = "d:\\max\\r2_naris\\inputs\\gdxfiles\\naris.gdx"




rsnew = as.data.frame(read.csv("rsmap.csv"))
colnames(rsnew) = c("r","s")
rsout = rsnew
rsout$val = 1
rsout = dcast(rsout,r~s,value.var="val")
rsout[is.na(rsout)] = 0

##reminder: upv and dupv by ba whereas csp and wnd are by rsc

setwd(file.path(".","supplycurvedata"))

colid = c("i","j","k","l","m","n","o","p")

twnd = rgdx.param(gdxin,"tmpWTOi",names=c(colid[1:(length(colnames(rgdx.param(gdxin,"tmpWTOi")))-1)],"value"))
tcsp = rgdx.param(gdxin,"tmpcspoct",names=c(colid[1:(length(colnames(rgdx.param(gdxin,"tmpcspoct")))-1)],"value"))

twnd$i = paste("s",twnd$i,sep="")
tcsp$j = paste("s",tcsp$j,sep="")
tcsp = tcsp[,c("j","value")]
tcsp$tech ="csp"
twnd$tech ="wind-ons"

colnames(tcsp) = c("i","value","tech")
ts = rbind(tcsp,twnd)

colnames(ts) = c("s","value","tech")
ts = merge(ts,rsnew,by="s")

tupv = rgdx.param(gdxin,"tmpupvon",names=c(colid[1:(length(colnames(rgdx.param(gdxin,"tmpupvon")))-1)],"value"))
tdupv = rgdx.param(gdxin,"tmpdupvon",names=c(colid[1:(length(colnames(rgdx.param(gdxin,"tmpdupvon")))-1)],"value"))
tupv$s = "sk"
tdupv$s = "sk"

colnames(tupv) = c("r","value","s")
colnames(tdupv) = c("r","value","s")
tupv$tech = "upv"
tdupv$tech = "dupv"

tout = rbind(ts,tupv,tdupv)

if(supplycurvefile==0){
#import capacity data
  dupvcap = as.data.frame(read.csv("DUPV_supply_curves_capacity.csv"))
  upvcap = as.data.frame(read.csv("UPV_supply_curves_capacity.csv"))
  windcap = as.data.frame(read.csv("wind_supply_curves_capacity.csv"))

#import cost data
  dupvcost = as.data.frame(read.csv("DUPV_supply_curves_cost.csv"))
  upvcost = as.data.frame(read.csv("UPV_supply_curves_cost.csv"))
  windcost = as.data.frame(read.csv("wind_supply_curves_cost.csv"))

#now using the argument-indicated gdx file for CSP supply curves
  cspfile = gdxin
  cspcap = rgdx.param(cspfile,"CSP2G",names=c(colid[1:(length(colnames(rgdx.param(cspfile,"CSP2G")))-1)],"value"))
  cspcost = rgdx.param(cspfile,"CSP2GPTS",names=c(colid[1:(length(colnames(rgdx.param(cspfile,"CSP2GPTS")))-1)],"value"))

#need to match formatting from before
  cspcap = dcast(cspcap,i+j~k)
  cspcost = dcast(cspcost,i+j~k)

  cspcap[is.na(cspcap)] = 0
  cspcost[is.na(cspcost)] = 0
}



if(supplycurvefile==1){
  print("given argument 6 - using NARIS version of wind, upv, and dupv supply cost curves")
  print("global 'naris_r' controls this setting in b_writedata.gms")
  
  dupvcost = as.data.frame(read.csv("DUPV_supply_curves_cost_NARIS.csv"))
  upvcost = as.data.frame(read.csv("UPV_supply_curves_cost_NARIS.csv"))
  windcost = as.data.frame(read.csv("wind_supply_curves_cost_NARIS.csv"))
  
  dupvcap = as.data.frame(read.csv("DUPV_supply_curves_capacity_NARIS.csv"))
  upvcap = as.data.frame(read.csv("UPV_supply_curves_capacity_NARIS.csv"))
  windcap = as.data.frame(read.csv("wind_supply_curves_capacity_NARIS.csv"))
  
  #now using the argument-indicated gdx file for CSP supply curves
  cspfile = gdxin
  cspcap = rgdx.param(cspfile,"CSP2G",names=c(colid[1:(length(colnames(rgdx.param(cspfile,"CSP2G")))-1)],"value"))
  cspcost = rgdx.param(cspfile,"CSP2GPTS",names=c(colid[1:(length(colnames(rgdx.param(cspfile,"CSP2GPTS")))-1)],"value"))
  
  #need to match formatting from before
  cspcap = dcast(cspcap,i+j~k)
  cspcost = dcast(cspcost,i+j~k)
  
  cspcap[is.na(cspcap)] = 0
  cspcost[is.na(cspcost)] = 0
  
}

if(supplycurvefile==2018){
  print("given argument 6 - using 2018 version of wind, upv, and dupv supply cost curves")
  print("global 'supplycurvefile' controls this setting in b_writedata.gms")
  
  dupvcost = as.data.frame(read.csv("DUPV_supply_curves_cost_2018.csv"))
  upvcost = as.data.frame(read.csv("UPV_supply_curves_cost_2018.csv"))
  windcost = as.data.frame(read.csv("wind_supply_curves_cost_2018.csv"))
  
  dupvcap = as.data.frame(read.csv("DUPV_supply_curves_capacity_2018.csv"))
  upvcap = as.data.frame(read.csv("UPV_supply_curves_capacity_2018.csv"))
  windcap = as.data.frame(read.csv("wind_supply_curves_capacity_2018.csv"))
  
  #now using the 2018 csv files for CSP
  cspcap = as.data.frame(read.csv("CSP_supply_curves_capacity_2018.csv"))
  cspcost = as.data.frame(read.csv("CSP_supply_curves_cost_2018.csv"))
  
  cspcap[is.na(cspcap)] = 0
  cspcost[is.na(cspcost)] = 0
  
}

if(supplycurvefile==2019){
  print("given argument 6 - using 2019 version of wind. Using 2018 version for everything else")
  print("global 'supplycurvefile' controls this setting in b_writedata.gms")
  
  dupvcost = as.data.frame(read.csv("DUPV_supply_curves_cost_2018.csv"))
  upvcost = as.data.frame(read.csv("UPV_supply_curves_cost_2018.csv"))
  windcost = as.data.frame(read.csv("wind_supply_curves_cost_2019.csv"))
  
  dupvcap = as.data.frame(read.csv("DUPV_supply_curves_capacity_2018.csv"))
  upvcap = as.data.frame(read.csv("UPV_supply_curves_capacity_2018.csv"))
  windcap = as.data.frame(read.csv("wind_supply_curves_capacity_2019.csv"))
  
  cspcap = as.data.frame(read.csv("CSP_supply_curves_capacity_2018.csv"))
  cspcost = as.data.frame(read.csv("CSP_supply_curves_cost_2018.csv"))
  
  cspcap[is.na(cspcap)] = 0
  cspcost[is.na(cspcost)] = 0
  
}

colnames(dupvcap) = c("r","class","bin1","bin2","bin3","bin4","bin5")
colnames(upvcap) = c("r","class","bin1","bin2","bin3","bin4","bin5")
colnames(cspcap) = c("s","class","bin1","bin2","bin3","bin4","bin5")

colnames(dupvcost) = c("r","class","bin1","bin2","bin3","bin4","bin5")
colnames(upvcost) = c("r","class","bin1","bin2","bin3","bin4","bin5")
colnames(cspcost) = c("s","class","bin1","bin2","bin3","bin4","bin5")

#wind capacity and costs also differentiate between 'class' and 'tech'
colnames(windcap) = c("s","class","tech","bin1","bin2","bin3","bin4","bin5")
colnames(windcost) = c("s","class","tech","bin1","bin2","bin3","bin4","bin5")

dupvcap$tech = "dupv"
upvcap$tech = "upv"
cspcap$tech = "csp1"

dupvcost$tech = "dupv"
upvcost$tech = "upv"
cspcost$tech = "csp1"
cspcost2 = cspcost
cspcost2$tech = "csp2"
cspcost <- rbind(cspcost, cspcost2)
rm(cspcost2)

scap = rbind(windcap,cspcap)
scost = rbind(windcost,cspcost)

rcap = rbind(upvcap,dupvcap)
rcost = rbind(upvcost,dupvcost)

scap$class = gsub("cspclass","",scap$class)
scap$class = gsub("class","",scap$class)
scost$class = gsub("cspclass","",scost$class)
scost$class = gsub("class","",scost$class)

rcap$class = gsub("class","",rcap$class)
rcost$class = gsub("class","",rcap$class)

rcap$s = "sk"
rcost$s = "sk"

scap$s = paste("s",scap$s,sep="")
scost$s = paste("s",scost$s,sep="")

scap = merge(scap,rsnew,by="s")
scost = merge(scost,rsnew,by="s")

scap$var = "cap"
scost$var = "cost"
rcap$var = "cap"
rcost$var = "cost"

alloutcap = rbind(scap,rcap)
alloutcost = rbind(scost,rcost)

alloutcap$class = paste("class",alloutcap$class,sep="")
t1 = dcast(setDT(alloutcap),r+s+tech+var~class,value.var=c("bin1","bin2","bin3","bin4","bin5"))

#add the existing capacity 
colnames(tout) = c("s","exist","tech","r")

tout$exist = tout$exist/1000

t2 = merge(t1,tout,all=T,by=c("s","r","tech"))

t2[is.na(t2)] = 0

wndonst2 = as.data.frame(subset(t2,tech=="wind-ons"))
wndofst2 = as.data.frame(subset(t2,tech=="wind-ofs"))
cspt2 = as.data.frame(subset(t2,tech=="csp1"))
upvt2 = as.data.frame(subset(t2,tech=="upv"))
dupvt2 = as.data.frame(subset(t2,tech=="dupv"))

binopt = seq(1,5,by=1)

#in the following loops, the order of each technology is specified
#from least-to-most expensive in terms of capacity. the amount of existing
#capacity is deducted from the best bin, computed as [bin capacity available] minus [existing]
#if existing exceeds the bin's capacity, the residual amount is stored in temp
#and that bin's capacity is set to zero. The example is notated in the wind bin
#calculations then repeated for other technologies

ordwnd = seq(1,15,by=1)
ordcsp = seq(5,1,by=-1)
ordpv = seq(9,1,by=-1)

if(deduct==1){
  for(i in ordwnd){
    for(j in binopt){
      yn = paste("bin",j,"_class",i,sep="")
      
      wndonst2$temp = wndonst2[,yn] - wndonst2$exist
      #if existing is greater than the bin/class combo, temp is less than zero
      #the remaining existing amount (to be subtracted off the next class/bin combo) is the absolute value of the remainder
      wndonst2[wndonst2$temp<0,]$exist = abs(wndonst2[wndonst2$temp<0,]$temp)
      #the remaining amount in that class/bin combo is zero
      wndonst2[wndonst2$temp<0,yn] = 0
      
      #if existing is less than the bin/class combo, temp is greater than zero
      #the remaining existing amount (to be subtracted off the next class/bin combo) is the absolute value of the remainder
      wndonst2[wndonst2$temp>=0,]$exist = 0
      #the remaining amount in that class/bin combo is the temp
      wndonst2[wndonst2$temp>=0,yn] = wndonst2[wndonst2$temp>=0,]$temp
    }
  }
  
  for(i in ordcsp){
    for(j in binopt){
      yn = paste("bin",j,"_class",i,sep="")
      cspt2$temp = cspt2[,yn] - cspt2$exist
      cspt2[cspt2$temp<0,]$exist = abs(cspt2[cspt2$temp<0,]$temp)
      cspt2[cspt2$temp<0,yn] = 0
      cspt2[cspt2$temp>=0,]$exist = 0
      cspt2[cspt2$temp>=0,yn] = cspt2[cspt2$temp>=0,]$temp
    }
  }
  
  for(i in ordpv){
    for(j in binopt){
      yn = paste("bin",j,"_class",i,sep="")
      upvt2$temp = upvt2[,yn] - upvt2$exist
      upvt2[upvt2$temp<0,]$exist = abs(upvt2[upvt2$temp<0,]$temp)
      upvt2[upvt2$temp<0,yn] = 0
      upvt2[upvt2$temp>=0,]$exist = 0
      upvt2[upvt2$temp>=0,yn] = upvt2[upvt2$temp>=0,]$temp  
      
      dupvt2$temp = dupvt2[,yn] - dupvt2$exist
      dupvt2[dupvt2$temp<0,]$exist = abs(dupvt2[dupvt2$temp<0,]$temp)
      dupvt2[dupvt2$temp<0,yn] = 0
      dupvt2[dupvt2$temp>=0,]$exist = 0
      dupvt2[dupvt2$temp>=0,yn] = dupvt2[dupvt2$temp>=0,]$temp    
    }
  }
  
  wndofst2$temp = 0
}
outcap = rbind(wndonst2,wndofst2,upvt2,dupvt2,cspt2)


moutcap = melt(outcap,id=c("s","r","tech","var"))
moutcap = subset(moutcap,variable!="exist" & variable!="temp")

moutcap$bin = gsub("_.*$","",moutcap$variable)
moutcap$class = gsub(".*_","",moutcap$variable)
moutcap$class = gsub("class","",moutcap$class)
moutcap = moutcap[,c("s","r","tech","var","bin","class","value")]
moutcap = subset(moutcap,value!=0)


outcapfin = dcast(moutcap,s+r+tech+var+class~bin,value.var="value")

outcapfin[is.na(outcapfin)] <- 0

#head(outcapfin)
allout = rbind(outcapfin,alloutcost)
allout$tech = paste(allout$tech,allout$class,sep="_")

alloutm = melt(allout,id=c("r","s","tech","var"))
alloutm = subset(alloutm,variable!="class")
#alloutd = dcast(alloutm,r+s+tech+variable~var,value.var="value")


# adding hydro costs and capacity separate as it does not 
# require the calculations to reduce capacity by existing amounts
# goal  here is to acquire a data frame that matches the format
# of alloutm so that we can simply stack the two
hydcap = as.data.frame(read.csv("hydcap.csv"))
hydcost = as.data.frame(read.csv("hydcost.csv"))

hydcap = melt(hydcap,id=c("tech","class"))
hydcost = melt(hydcost,id=c("tech","class"))

hydcap$var = "cap"
hydcost$var = "cost"

hyddat = rbind(hydcap,hydcost)
hyddat$s = "sk"
hyddat$bin = gsub("hydclass","bin",hyddat$class)
hyddat$class = gsub("hydclass","",hyddat$class)

colnames(hyddat) = c("tech","class","r","value","var","s","variable")
hyddat = hyddat[,c("tech","r","value","var","s","variable")]

hyddat[is.na(hyddat)] = 0


########################
#PHS supply curves
########################

phs_cap = rgdx.param(gdxPHS,"PHSmax",names=c(colid[1:(length(colnames(rgdx.param(gdxPHS,"PHSmax")))-1)],"value"))
phs_cost = rgdx.param(gdxPHS,"PHScostn",names=c(colid[1:(length(colnames(rgdx.param(gdxPHS,"PHScostn")))-1)],"value"))

phs_cap$var = "cap"
phs_cost$var = "cost"


phs_out = rbind(phs_cap,phs_cost)
phs_out$tech = "pumped-hydro"
phs_out$variable = gsub("phsclass","bin",phs_out$i)
phs_out[is.na(phs_out)] = 0
phs_out$r = phs_out$j
phs_out$s = "sk"
phs_out = phs_out[,colnames(hyddat)]


#now stacking the final versions
alloutm = rbind(alloutm,hyddat,phs_out)

#creating a label that gams can eaisly read
alloutm$label = paste(alloutm$r,alloutm$s,alloutm$tech,alloutm$variable,alloutm$var,sep=".")
alloutm$label = paste("(",alloutm$label,")",sep="")
alloutm$value = paste(alloutm$value,",",sep="")


alloutf = alloutm[,c("label","value")]
alloutf[1,]$label = paste("/",alloutf[1,]$label,sep="")
alloutf[length(alloutf$value),]$value = paste(gsub(",","",alloutf[length(alloutf$value),]$value),"/;",sep="")


########################
#biomass supply curve
########################

bio_cap = rgdx.param(gdxBio,"BioSupplyCurve",names=c(colid[1:(length(colnames(rgdx.param(gdxBio,"BioSupplyCurve")))-1)],"value"))
bio_cost = rgdx.param(gdxBio,"BioFeedstockPrice",names=c(colid[1:(length(colnames(rgdx.param(gdxBio,"BioFeedstockPrice")))-1)],"value"))
bio_cap$var = "cap"
bio_cost$var = "cost"

bio_out = rbind(bio_cap,bio_cost)
bio_out = dcast(bio_out,j+var~i,value.var="value")

bio_ramp = rgdx.param(gdxBio,"BioFeedstockRamp",names=c(colid[1:(length(colnames(rgdx.param(gdxBio,"BioFeedstockRamp")))-1)],"value"))
bio_ramp = dcast(bio_ramp,j~i,value.var="value")


########################
#geothermal supply curve
########################

setwd(file.path('..'))
geo_disc = read.csv(file.path("geothermal",paste0("geo_discovery_",geoscen,".csv")), check.names = F)
geo_fom = read.csv(file.path("geothermal",paste0("geo_fom_",geoscen,".csv")), check.names = F)
geo_rsc = read.csv(file.path("geothermal",paste0("geo_rsc_",geoscen,".csv")), check.names = F)

write.table(alloutf,paste0(outdir,"rsc_combined.txt"),row.names=FALSE,col.names=FALSE,quote=FALSE)
write.csv(rsout,paste0(outdir,"rsout.csv"),row.names=FALSE,quote=FALSE)
write.csv(bio_out,paste0(outdir,"bio_supplycurve.csv"),row.names=FALSE,quote=FALSE)
write.csv(bio_ramp,paste0(outdir,"bio_priceramp.csv"),row.names=FALSE,quote=FALSE)
write.csv(geo_disc,paste0(outdir,"geo_discovery.csv"),row.names=FALSE,quote=FALSE)
write.csv(geo_fom,paste0(outdir,"geo_fom.csv"),row.names=FALSE,quote=FALSE)
write.csv(geo_rsc,paste0(outdir,"geo_rsc.csv"),row.names=FALSE,quote=FALSE)

print("writesupplycurve.R completed successfully")

