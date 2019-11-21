sink("gamslog.txt",append=TRUE)

library(reshape2)
library(gdxrrw)

print("Beginning calculations in inputs\\cf\\cfgather.R")


#cfgather.R
#Args=list()
#Args[1]="D:\\Max\\r2_na\\"
#Args[2]="C:\\GAMS\\win64\\24.7\\"
#Args[3]="inputs\\gdxfiles\\harm.gdx"

colid = c("i","j","k","l","m","n","o","p")


if(!exists("Args")) Args=commandArgs(TRUE)

indir = paste(Args[1])
setwd(indir)

igdx(paste(Args[2]))
gdxfile = file.path("inputs","cf","cfdata.gdx")
distpvscen = as.character(Args[3])
outdir = paste0(Args[4])


rs = as.data.frame(read.csv(file.path(indir,"inputs","rsmap.csv")))
colnames(rs) = c("r","s")


####################
# Wind
####################

wind = as.data.frame(rgdx.param(gdxfile,"CF_Corr",names=c(colid[1:(length(colnames(rgdx.param(gdxfile,"CF_Corr")))-1)],"value")))
wind$c = paste(wind$k,"_",gsub("class","",wind$j),sep="")
wind$i = paste("s",wind$i,sep="")
colnames(wind) = c("s","cl","it","h","value","i")
wind=merge(wind,rs,by=c("s"))
wind = wind[,c("r","s","i","h","value")]

wcf = as.data.frame(rgdx.param(gdxfile,"CFW_all",names=c(colid[1:(length(colnames(rgdx.param(gdxfile,"CFW_all")))-1)],"value")))
wcf$i = paste(wcf$i,gsub("class","",wcf$k),sep="_")
wcf = wcf[,c("j","i","value")]
wcf = dcast(wcf,j~i,value.var="value")


####################
# UPV
####################

upv = as.data.frame(rgdx.param(gdxfile,"CFUPV",names=c(colid[1:(length(colnames(rgdx.param(gdxfile,"CFUPV")))-1)],"value")))
upv$c = paste("UPV","_",gsub("class","",upv$k),sep="")
upv$s = "sk"
colnames(upv) = c("r","h","cl","value","i","s")
upv = upv[,c("r","s","i","h","value")]

####################
# DUPV
####################

dupv = as.data.frame(rgdx.param(gdxfile,"CFDUPV",names=c(colid[1:(length(colnames(rgdx.param(gdxfile,"CFDUPV")))-1)],"value")))
dupv$c = paste("DUPV","_",gsub("class","",dupv$k),sep="")
dupv$s = "sk"
colnames(dupv) = c("r","h","cl","value","i","s")
dupv = dupv[,c("r","s","i","h","value")]

####################
# distPV
####################


distpv = as.data.frame(read.csv(file.path(indir,"inputs","dGen_Model_Inputs",distpvscen,paste0("distPVCF_", distpvscen, ".csv"))))
colnames(distpv)[1] = "ba"
distpv = melt(distpv,id=c("ba"))
colnames(distpv) = c("r","h","value")
distpv$i = "distPV"
distpv$s = "sk"

distpv = distpv[,c("r","s","i","h","value")]


####################
# CSP
####################

# CFCspwStorallyears in heritage ReEDS is the adjusted CSP-ws field capacity factor from CFCSPws_tower;
# data for tower system starts from 2018 and are the same across years (no need for a year dimension)
# Note that in the most version, CFCSPws_tower (read from field_capacity_factor.csv file) has already incorporated the availability factors
# (CFCSPws_adj_factor_tower and CSPws_avail_factor)
# so can directly read from CFCSPws_tower

# CF for CSP is from SAM modeling results, and assumes SM=1 (i.e. the numbers will need to be multiplied by the actual SM of certain configurations)

csp = as.data.frame(rgdx.param(gdxfile,"CFCSPws_tower",names=c(colid[1:(length(colnames(rgdx.param(gdxfile,"CFCSPws_tower")))-1)],"value")))
colnames(csp) = c("s","h","i","value")
csp$i = gsub("class","_",csp$i)
csp$i = gsub("csp","csp1",csp$i)
csp$s <- paste0("s", csp$s)
csp <- csp[,c("s","h","i","value")]
csp=merge(csp,rs,by=c("s"))

csp = dcast(csp,r+s+i~h,value.var="value")
csp[is.na(csp)] <- 0
csp$H5 <- 0
csp$H9 <- 0
csp <- csp[,c("r","s","i",sprintf("H%s",seq(1:17)))]

csp_temp <- csp
csp_temp$i <- gsub("csp1","csp2",csp_temp$i)
csp <- rbind(csp, csp_temp)
rm(csp_temp)

###################
#output writing
###################




allcf = rbind(wind,upv,dupv,distpv)
allcf = dcast(allcf,r+s+i~h,value.var="value")
allcf[is.na(allcf)] = 0
allcf <- rbind(allcf, csp)

##############################
#hydro mingen
###############################

hydro = as.data.frame(rgdx.param(gdxfile,"minplantload_hy",names=c(colid[1:(length(colnames(rgdx.param(gdxfile,"minplantload_hy")))-1)],"value")))
hydro$j = substr(hydro$j,1,4)
colnames(hydro) = c("i","szn","r","value")
hydro = dcast(hydro,i+r~szn,value.var="value")


#write.table(out,"cfout.txt",row.names=FALSE,col.names=FALSE,quote=FALSE)
print(paste("writing capacity factor data to:",outdir))
write.csv(allcf,paste0(outdir,"cfout.csv"),row.names=FALSE,quote=FALSE)
# write.csv(csp,paste0(outdir,"cfout_csp.csv"),row.names=FALSE,quote=FALSE)
write.csv(wcf,paste0(outdir,"windcfout.csv"),row.names=FALSE,quote=FALSE)
write.csv(hydro,paste0(outdir,"minhyd.csv"),row.names=FALSE,quote=FALSE)


