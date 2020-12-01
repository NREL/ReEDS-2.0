sink("gamslog.txt",append=TRUE)

#File to aggregate units clustered by performance characteristics

library(data.table)
library(dplyr)
library(reshape2)

print(" ")
print("Beginning calculation of inputs\\capacitydata\\WriteHintage.R")

#need to set a seed to make the kmeans clustering algorithm deterministic
#this is combined with several draws (here 1000) to make sure there is
#consistency in the aggregation algorithm
set.seed(7)

#need to convert from 1987$ to 2004$ via the following parameter
#computed from values at:
#https://www.minneapolisfed.org/community/financial-and-economic-education/cpi-calculator-information/consumer-price-index-and-inflation-rates-1913
inflate_87_04 = 1.69

#WriteHintage.R
# Args=list()
# Args[1]="D:\\scott\\ReEDS-2.0\\"
# Args[2]=7
# Args[3]="NukeRefRetireYear"
# Args[4]=50
# Args[5]=0
# Args[6]='afterFOMfix2_Mid_Case'
# Args[7]='ReEDS_generator_database_final_EIA-NEMS.csv'
# Args[8]="D:\\Danny_ReEDS\\ReEDS-2.0\\runs\\Apr21_RPS_updates\\inputs_case\\"# Args[9]=1
# Args[9]=0


#setting working directory
if(!exists("Args")) Args=commandArgs(TRUE)
setwd(file.path(Args[1],"inputs","capacitydata"))

#check what type some args are? Set number of bins
if(Args[2]!='unit'){
  MaxBins = as.numeric(as.character(Args[2]))
}
if(Args[2]=='unit'){
  MaxBins = as.character(Args[2])
}

#initialize variables
retscen = as.character(Args[3])
mindev = as.numeric(as.character(Args[4]))
calcmethod = as.numeric(as.character(Args[5]))
distpvscen = as.character(Args[6])
genunitfile = as.character(Args[7])
outdir = paste(Args[8])
waterconstraints = as.numeric(as.character(Args[9]))

#load in the full unit data from genunitfile
indat = as.data.frame(read.csv(genunitfile))

#note the number of bins needs to be reduced by 1 in the actual calculations due to kmeans algorithm
print(paste("Chosen number of bins for heat rate binning:",MaxBins))
#print(paste("Note that the final number of bins could have one more than stated"))

#include O&M of polution control upgrades into FOM
indat$W_VOM = inflate_87_04 * (indat$W_VOM + indat$WCOMB_V + indat$WSNCR_V + indat$WSCR_V + indat$W_FFV + indat$W_DSIV)
indat$W_FOM = inflate_87_04 * (indat$W_FOM + indat$W_CAPAD + indat$WCOMB_F + indat$WSNCR_F + indat$WSCR_F + indat$W_FFF + indat$W_DSIF)

#need to assign w_fom as the sum of all fixed cost categories, simiar for w_vom

#concatenate tech names based on whether water analysis is on -or- leave them alone
if(waterconstraints==1){
indat$tech = indat$coolingwatertech
indat$tech = gsub("_","x",indat$tech)
}

ad = indat[,c("tech","pca","ctt","resource_region","cap",retscen,"Commercial.Online.Year.Quarter","IsExistUnit",
              "Fully.Loaded.Tested.Heat.Rate.Btu.kWh...Modeled","Plant.NAICS.Description","W_VOM","W_FOM")]

ad$IsExistUnit = as.character(ad$IsExistUnit)

colnames(ad) = c("TECH","PCA","ctt","resource.region","Summer.capacity","RetireYear",
                 "Solve.Year.Online","EXIST","HR","NAICS","VOM","FOM")

naics_cats<-c("Hydroelectric Power Generation",
              "Nuclear Electric Power Generation",
              "Other Electric Power Generation",
              "Electric Power Generation",
              "Electric Power Distribution",
              "Utilities",
              "Electric Power Generation, Transmission and Distribution"
)


swnaics = 1

ad$EXIST = toupper(ad$EXIST)

ad = subset(ad,EXIST==TRUE)

if(swnaics==1){
  ad = subset(ad,NAICS %in% naics_cats | Summer.capacity>=50)
}


ad$onlineyear = as.numeric(as.character(substr(ad$Solve.Year.Online,1,4)))
ad$pcn = as.numeric(as.character(gsub("p","",ad$PCA)))


#only want those with a heat rate - all other binning is arbitrary
#because the only data we get from genunitfile is the capacity and heat rate
#but onm costs are assumed
dt = subset(ad,HR!="NA" & TECH!="geothermal" & TECH!="unknown" & TECH!="CofireNew")
dt$Solve.Year.Online = as.numeric(as.character(dt$onlineyear))


#can aggregate over units that have the same characteristics
dat = aggregate(dt$Summer.capacity,by=list(dt$TECH,dt$PCA,dt$HR,dt$resource.region,
                                           dt$Solve.Year.Online,dt$RetireYear,dt$VOM,dt$FOM),FUN=sum)

#reset the column names
colnames(dat) = c("TECH","PCA","HR","resource.region","Solve.Year.Online",
                  "RetireYear","VOM","FOM","Summer.capacity")

#remove others category
dat = subset(dat,TECH!="others")

#set the solve year here, avoiding the quarter designation
#could use this later to specify whether a plant is available in a specific quarter
dat$Solve.Year.Online = as.numeric(as.character(substr(dat$Solve.Year.Online,1,4)))

dat = subset(dat,RetireYear>=2010 & Solve.Year.Online < 2010)

dat$id = paste(dat$TECH,dat$PCA,sep="_")

if(MaxBins!="unit"){

  tdat = data.frame()
  jj = data.frame()
  
  # note that given bounds, the final
  # number of bins will be maxbins+1
  #mindev = 100
  
  print("following commands may result in warnings - these are normal")
  print("and the binning will be re-attempted with fewer bins")
  paste("minimum deviation to qualify for separate bins = ",as.character(mindev),sep="")
  
  
  if(MaxBins>1){
    
    dat$ran = sample(1e5,size=nrow(dat),replace=FALSE) /1e6
    dat$HR = as.numeric(dat$HR + dat$ran)
    dat = dat[,!(colnames(dat)%in%c("ran"))]
    exceptlist = c("gas-CC_p98","gas-CT_p42","gas-CT_p82","gas-CT_p91",
                   "gas-CT_p5","CoalOldScr_p70","CoalOldScr_p72","CoalOldScr_p72")
    
    jj = data.frame()
    for(i in unique(dat$id)){
      tdat = subset(dat,id==i)
      for(t in seq(MaxBins,0,-1)){
        if(i %in% exceptlist & length(tdat$HR)<=MaxBins){
          nj = data.frame(j.brks = unique(tdat$HR),id=i)
          nj$bin = row(nj)[,1]
          break
        }
    
        #if there are uniquely-binnable items
        if(length(unique(tdat$HR))>t & t!=0){
          #kmeans requires a matrix, here just taking the row of values
          #and finding the averages and boundaries (via $centers and $brks) of each bins
          #j = classIntervals(tdat$HR,n=1,style="jenks")
          nj = data.frame(j.brks = kmeans(as.matrix(tdat$HR)[,1],t,nstart=1000)$centers)
          nj = data.frame(j.brks = nj[order(nj$j.brks),])
          #new data frame id gets assigned from the loop
          nj$id = i
          #bin specified from the kmeans
          nj$bin = row(nj)[,1]
          #compute the minimum difference of heat rates across bins
          #this will be used to decide whether binning should be re-attempted
          minbreakdiff = 1e10
          #if there is more than one bin
          if(t>1){
            for(u in seq(1,length(nj$j.brks)-1,1)){
              minbreakdiff = min(minbreakdiff,nj$j.brks[u+1] - nj$j.brks[u])
            }
            #if that minimum break exceed the threshold...
            #if not - the loop will continue with one less bin
            if(minbreakdiff>mindev){
              break
            }
          }
          #solution for the couples problem
          if(t==1 & length(unique(tdat$HR)==2) & (abs(unique(tdat$HR)[1] - unique(tdat$HR)[2])>mindev) ){
            z1 = data.frame(j.brks=unique(tdat$HR)[1],id=i,bin=1)
            z2 = data.frame(j.brks=unique(tdat$HR)[2],id=i,bin=2)
            nj = rbind(z1,z2)
            break
          }
          }
      }#end for loop on maximum bins
      if(t==0){
        nj = data.frame(j.brks = kmeans(as.matrix(tdat$HR,nstart=1000)[,1],1)$centers)
        nj$id = i
        nj$bin = MaxBins+1
      }
      jj = rbind(jj,nj)
    }#end id loop
    
    
    
    #need to compute average heat rate for each bin
    #weighted by the total amount of summer capacity
    jd = merge(dat,dcast(jj,id~bin,value.var = "j.brks"))
    #jd = merge(dat2,dcast(nj,id~bin,value.var = "j.brks"))
    
    parcol = 10
    
    jd_nbin = na.omit(jd[,c(1:parcol,parcol+MaxBins+1)])
    jd_nbin$bin = MaxBins+2
    jd_wbin = jd[,c(1:(parcol+MaxBins+1))]
    
    #all binned id combinations will have data for the first bin
    jd_wbin = jd_wbin[complete.cases(jd_wbin[,parcol]),]
    
    
    tj = jd_wbin
    tj$bin = 0
    tj$HR = round(tj$HR,0)
    
    
    # for either calcmethod, helpful to remember that...
    # tj[,c(parcol+i)] == the bin's heat rate as indicated by kmeans
    # tj$hr == units' heat rates
    
    bins = seq(1,MaxBins,1)
    diffcols = paste("diff",bins,sep="")
    
    print(paste("given argument 5 - you've chosen calcmethod",calcmethod))
    
    #with calcmethod = 0 finding the minimum difference from what was indicated as the break
    if(calcmethod==0){
      print("this implies that you'll be binning plants by nearest break")
      tj[,diffcols] = abs(tj[,paste(bins)]-tj$HR)
      tj$min_colname  = apply(tj[,diffcols], 1, function(x) colnames(tj[,diffcols])[which.min(x)])
      tj$bin = ifelse(rowSums(is.na(tj[,paste(bins)])) == MaxBins,MaxBins+1,0)
      tj[tj$bin!=MaxBins+1,]$bin = gsub("diff","",tj[tj$bin!=MaxBins+1,]$min_colname)
    }
    
    #previous method
    if(calcmethod==1){
    
      print("this implies that you'll be binning plants by defining bins' boundaries")
    
      for(i in 1:MaxBins){
        #tj = jd_wbin[complete.cases(jd_wbin[,parcol+i]),]
      
        if(i==1){
          #i=1
          #less than or equal to the lowest value
          tj$bin = ifelse(!is.na(tj[,c(parcol+i)]) &  tj[,c(parcol+i)]>=tj$HR,i,tj$bin)
        }
      
        if(i>1 & i<MaxBins){
          #greater than the previous bin and less than or equal to the current bin+
          tj$bin = ifelse(!is.na(tj[,c(parcol+i)]) &  tj[,c(parcol+i)]>=tj$HR & tj[,c(parcol+i-1)]<tj$HR,i,tj$bin)
          tj$bin = ifelse(!is.na(tj[,c(parcol+i)]) &  tj[,c(parcol+i)]<tj$HR,i+1,tj$bin)
        }
      
        if(i==MaxBins){
          #less than or equal to the lowest value
          tj$bin = ifelse(!is.na(tj[,c(parcol+i)]) &  tj[,c(parcol+i)]>=tj$HR & tj[,c(parcol+i-1)]<tj$HR,i,tj$bin)
          tj$bin = ifelse(!is.na(tj[,c(parcol+i)]) &  tj[,c(parcol+i)]<tj$HR,i+1,tj$bin)
        }
      }
        tj$bin = tj$bin + 1
    }
      
  }
    
  if(MaxBins==1){
    tj = dat
    tj$bin = 1
  }
  
  
  common_columns = c("id","TECH","PCA","HR","resource.region","Solve.Year.Online","RetireYear","VOM","FOM","Summer.capacity","bin")
  
  tj = tj[,common_columns]
  
  zall = tj
  zall$bin = as.numeric(as.character(zall$bin))
  zall$id = paste(zall$id,zall$bin,sep="_")
  
  #Scale Hr, VOM, solve.year.online, and FOM by summer capacity factor
  zall$wHR = zall$HR * zall$Summer.capacity
  zall$wVOM = zall$VOM * zall$Summer.capacity
  zall$wFOM = zall$FOM * zall$Summer.capacity
  zall$Solve.Year.Online = as.numeric(as.character(zall$Solve.Year.Online)) * zall$Summer.capacity
  
  
  
  zout = data.frame()
  
  for(i in 2010:2100){
    #only want units that haven't retired yet
    #NB we can include  & Solve.Year.Online<i -but- we already have prescribed retirements that take care of this
    zt = subset(zall,RetireYear>i)
  
    #get the total capacity by bin
    if(nrow(zt)>0){
      
      ztc = aggregate(zt$Summer.capacity,by=list(zt$id),FUN=sum)
      colnames(ztc) = c("id","cap")
      ztc$cap = round(ztc$cap,digits=4)
    
      zthr = aggregate(zt$wHR,by=list(zt$id),FUN=sum)
      ztvom = aggregate(zt$wVOM,by=list(zt$id),FUN=sum)
      ztfom = aggregate(zt$wFOM,by=list(zt$id),FUN=sum)
      ztonlineyear = aggregate(zt$Solve.Year.Online,by=list(zt$id),FUN=sum)
      colnames(zthr) = c("id","wHR")
      colnames(ztvom) = c("id","wVOM")
      colnames(ztfom) = c("id","wFOM")
      colnames(ztonlineyear) = c("id","onlineyear")
      ztm = merge(ztc,zthr)
      ztm = merge(ztm,ztfom)
      ztm = merge(ztm,ztvom)
      ztm = merge(ztm,ztonlineyear)
      ztm$wHR = round(ztm$wHR / ztm$cap,digits=3)
      ztm$wVOM = round(ztm$wVOM / ztm$cap,digits=3)
      #need to convert FOM to $ / KW to $ / MW  
      ztm$wFOM = round(1000 * ztm$wFOM / ztm$cap,digits=3)
      ztm$wOnlineYear = round(ztm$onlineyear / ztm$cap,digits=0)
      ztm$yr = i
      zout = rbind(zout,ztm)
    
    
    }
  }
  
  
  #end of conditional for unit-level representation
}

#begin unit level representation
if(MaxBins=="unit"){
  
  datfin = data.frame()
  
  dat$HR = round(dat$HR,0)
  
  zall_coal = subset(dat,TECH %in% coaltechs)
  zall_nocoal = subset(dat,!(TECH %in% coaltechs))
  
  
  zall_coal$id = paste(zall_coal$TECH,zall_coal$PCA,zall_coal$HR,zall_coal$Solve.Year.Online,zall_coal$VOM,zall_coal$FOM,sep="_")
  zall_nocoal$id = paste(zall_nocoal$TECH,zall_nocoal$PCA,zall_nocoal$HR,zall_nocoal$VOM,zall_nocoal$FOM,sep="_")
  
  zall= rbind(zall_coal,zall_nocoal)
  
  zall$id2 = paste(zall$TECH,zall$PCA,sep="_")
  
  #create a unique 'bin' for each unit
  for(i in unique(zall$id2)){
    dat0 = subset(zall,id2==i)
    dat0$bin <- dat0 %>% group_indices(id) 
    datfin = rbind(datfin,dat0)
  }
  

  common_columns = c("id","TECH","PCA","HR","resource.region","Solve.Year.Online","RetireYear","VOM","FOM","Summer.capacity","bin")
  
  zall = datfin[,common_columns]
  
  zall$bin = as.numeric(as.character(zall$bin))
  zall$id = paste(zall$id,zall$bin,sep="_")
  zall$wHR = zall$HR * zall$Summer.capacity
  zall$wVOM = zall$VOM * zall$Summer.capacity
  zall$wFOM = zall$FOM * zall$Summer.capacity
  zall$Solve.Year.Online = as.numeric(as.character(zall$Solve.Year.Online)) * zall$Summer.capacity
  
    
  zout = data.frame()
  


  for(i in 2010:2100){
    #only want units that haven't retired yet
    #NB we can include  & Solve.Year.Online<i -but- we already have prescribed retirements that take care of this
    zt = subset(zall,RetireYear>i)
    
    #get the total capacity by bin
    if(nrow(zt)>0){
      
      ztc = aggregate(zt$Summer.capacity,by=list(zt$id),FUN=sum)
      colnames(ztc) = c("id","cap")
      ztc$cap = round(ztc$cap,digits=4)
      
      #sum the weighted heat rate, VOM, and FOM (will be divided by total capacity)
      zthr = aggregate(zt$wHR,by=list(zt$id),FUN=sum)
      ztvom = aggregate(zt$wVOM,by=list(zt$id),FUN=sum)
      ztfom = aggregate(zt$wFOM,by=list(zt$id),FUN=sum)
      ztonlineyear = aggregate(zt$Solve.Year.Online,by=list(zt$id),FUN=sum)
      colnames(zthr) = c("id","wHR")
      colnames(ztvom) = c("id","wVOM")
      colnames(ztfom) = c("id","wFOM")
      colnames(ztonlineyear) = c("id","onlineyear")
      ztm = merge(ztc,zthr)
      ztm = merge(ztm,ztfom)
      ztm = merge(ztm,ztvom)
      ztm = merge(ztm,ztonlineyear)
      ztm$wHR = round(ztm$wHR / ztm$cap,digits=3)
      ztm$wVOM = round(ztm$wVOM / ztm$cap,digits=3)
      #need to convert FOM to $ / KW to $ / MW  
      ztm$wFOM = round(1000 * ztm$wFOM / ztm$cap,digits=3)
      ztm$wOnlineYear = round(ztm$onlineyear / ztm$cap,digits=0)
      ztm$yr = i
      zout = rbind(zout,ztm)
    }
  }
  

#end of operations if doing unit level representation
}


#separate out elements in zout$id
zout$TECH = gsub("_.*$","",zout$id)
for(i in unique(zout$TECH)){
  zout$id = gsub(paste(i,"_",sep=""),"",zout$id)
}

zout$ba = gsub("_.*$","",zout$id)
zout$bin = gsub(".*_","",zout$id)


zout = zout[,c("yr","TECH","ba","bin","wHR","wFOM","wVOM","wOnlineYear","cap")]


#adding distributed PV here
#hintages are the only capacity indexed by time
#strange, I know, but fits better than any other
#exogenous parameter preparation script
DPV = as.data.frame(read.csv(file.path(Args[1],"inputs","dGen_Model_Inputs",distpvscen,paste0("distPVcap_", distpvscen, ".csv"))))
DPV = melt(DPV,id=c("X"))
colnames(DPV) = c("ba","yr","cap")
#DPV$rs = "sk"
DPV$yr = as.numeric(as.character(gsub("X","",DPV$yr)))
DPV$TECH = "distPV"
DPV$wHR = 0
DPV$wVOM = 0
DPV$wFOM = 0
DPV$bin = 1
DPV$wOnlineYear = 2010

zout = rbind(zout,DPV)


zout$bin = paste("init-",zout$bin,sep="")
zout = zout[,c("TECH","bin","ba","yr","cap","wHR","wFOM","wVOM","wOnlineYear")]

#Implementing forced retirements by technology and BA
forced_retire = as.data.frame(read.table(file.path(Args[1],"inputs","state_policies","forced_retirements.csv"),sep=',',col.names=c('i','r','t')))
forced_retire$id = paste0(forced_retire$r,'_',forced_retire$i)
zout$id = paste0(zout$ba,'_',zout$TECH)
#Marge dataframe where ba and tech combo exists in forced_retire
zout = merge(zout,forced_retire[,c('t','id')],by='id',all.x=TRUE)
# t is the mandated retire year. When yr is >= t cap should be 0. Setting t to really high number for combinations not in forced retire
zout$t[is.na(zout$t)] = 10000000000000
zout$cap[zout$yr >= zout$t] = 0

#drop extra columns
zout$t <- zout$id <- NULL

print(paste0("New hintage data written as: "))
  print(paste0(outdir,"hintage_data.csv"))

#substitute temporary placeholder with underscore for coolingwatertech
if(waterconstraints==1){
    zout$TECH = gsub("x","_",zout$TECH)
}

write.csv(zout, paste0(outdir,"hintage_data.csv"), row.names=FALSE, quote=FALSE)

