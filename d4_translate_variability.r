sink("gamslog.txt",append=TRUE)

library(gdxrrw)

print("")
print("Beginning calculation of d4_Translate_Variability.R")
print("Purpose of this file is to translate outputs from heritage ReEDS variability scripts")


colid=c("i","j","k","l","m","n")

if(!exists("Args")) Args=commandArgs(TRUE)
setwd(paste(Args[1]))
igdx(paste(Args[2]))
nextyear = paste(Args[3])
case = paste(Args[4])
infile = file.path("outputs","variabilityFiles",paste0("rawvariability_",case,"_",nextyear,".gdx"))
outfile = file.path("outputs","variabilityFiles",paste0("curt_out_",case,"_",nextyear,".gdx"))


print("")
print(paste("Starting Translation of cc/curt scripts for case:",case))
print("")
print(paste("Using ",infile,sep=""))
print(paste("Creating ",outfile,sep=""))
print("")


#all we need from the supply side solve is the r_rs mapping set
solfile = file.path("inputs_case","r_rs.gdx")
r_rs = rgdx.param(solfile,"r_rs",names=c(colid[1:(length(colnames(rgdx.param(solfile,"r_rs")))-1)],"value"))
r_rs = r_rs[,c("i","j")]
colnames(r_rs) = c("r","rs")


############################################################################
#
#        MARGINAL CURTAILMENT
#
# COMPUTING MARGINAL CURTAILMENT VALUES
# BY TECHNOLOGY 
############################################################################

allsm = data.frame(i = factor(),
                   r = factor(),
                   rs = factor(),
                   h = factor(),
                   value = double())
sm_keep = c("i","r","rs","h","value")

distpvsm = rgdx.param(infile,"distpvsurplusmar",names=c("r","h","value"))
if(nrow(distpvsm) > 0){
  distpvsm$i = "distPV"
  distpvsm$rs = "sk"
  allsm = rbind(allsm,distpvsm[,colnames(distpvsm) %in% sm_keep])
}


dupvsm = rgdx.param(infile,"dupvsurplusmar",names=c("r","h","i","value"))
if(nrow(dupvsm) > 0){
  dupvsm$i = paste("dupv_",gsub("class","",dupvsm$i),sep="")
  dupvsm$rs = "sk"
  allsm = rbind(allsm,dupvsm[,colnames(dupvsm) %in% sm_keep])
}

upvsm = rgdx.param(infile,"upvsurplusmar",names=c("r","h","i","value"))
if(nrow(upvsm) > 0){
  upvsm$i = paste("UPV_",gsub("class","",upvsm$i),sep="")
  upvsm$rs = "sk"
  allsm = rbind(allsm,upvsm[,colnames(upvsm) %in% sm_keep])
}

wsm = rgdx.param(infile,"wsurplusmar",names=c("i1","i2","rs","h","value"))
if(nrow(wsm) > 0){
  wsm$i = paste(wsm$i2,gsub("class","",wsm$i1),sep="_")
  wsm$rs = paste("s",wsm$rs,sep="")
  wsm = merge(wsm,r_rs,by=c("rs"))
  allsm = rbind(allsm,wsm[,colnames(wsm) %in% sm_keep])
}

if(length(rgdx.param(infile,"cspsurplusmar")[,1])>0){
  cspsm = rgdx.param(infile,"cspsurplusmar",names=c("i","rs","h","value"))
  cspsm$rs = paste("s",cspsm$rs,sep="")
  cspsm$i = gsub("cspclass","CSP_",cspsm$i)
  cspsm = merge(cspsm,r_rs,by=c("rs"))
  allsm = rbind(allsm, cspsm[,colnames(cspsm) %in% sm_keep])
}

if(nrow(allsm)>0){
  allsm$t = nextyear  
} else {
  allsm = data.frame("i"="wind-ons_1","r"="p1","rs"="s3","h"="h1","t"=nextyear,"value"=0)
}


allsm = allsm[,c("i","r","rs","h","t","value")]


#######################################
#
#       Preparing MRSurplusMar
#
#######################################

MRsurplusm = rgdx.param(infile,"MRSurplusMar",names=c("r","h","value"))
if(nrow(MRsurplusm)>0){
  MRsurplusm$t = nextyear
  MRsurplusm = MRsurplusm[,c("r","h","t","value")]
} else {
  MRsurplusm = data.frame("r"="p1","h"="h1","t"=nextyear,"value"=0)
}


#######################################
#
#       Preparing curtailment
#
#######################################

surpold = rgdx.param(infile,"SurpOld",names=c("r","h","value"))
surpold$t = nextyear
surpold = surpold[,c("r","h","t","value")]

#######################################
#
#       WRITING OUTPUT
#
#######################################


columnfactors <- function(df){
  for(j in colnames(df)[1:length(colnames(df))-1]){
    df[,j] = factor(df[,j],levels=unique(df[,j]))
  }
  return(as.data.frame(df))
}

allsm = columnfactors(allsm)
attr(allsm,"symName") = "surplusmarginal"

MRsurplusm= columnfactors(MRsurplusm)
attr(MRsurplusm,"symName") = "MRsurplusmarginal"

surpold= columnfactors(surpold)
attr(surpold,"symName") = "surpold"

wgdx.lst(outfile,allsm,MRsurplusm,surpold)


