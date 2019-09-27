sink("gamslog.txt",append=TRUE)

library(gdxrrw)
library(reshape2)

print("Beginning calculation of inputs\\capacitydata\\writecapdat.R")


#writecapdat.R
# Args=list()
# Args[1]="D:\\Danny_ReEDS\\ReEDS-2.0\\"
# Args[2]="C:\\GAMS\\win64\\24.7\\"
# Args[3]="ExistingUnits_EIA-NEMS.gdx"
# Args[4]="PrescriptiveBuilds_EIA-NEMS.gdx"
# Args[5]="PrescriptiveRetirements_EIA-NEMS.gdx"
# Args[6]="NukeRefRetireYear"


if(!exists("Args")) Args=commandArgs(TRUE)


curwd = paste0(Args[1],"inputs\\capacitydata\\")
igdx(paste(Args[2]))

setwd(curwd)

gdxname = paste(Args[3])
gdxnamePRES = paste(Args[4])
gdxnameRET = paste(Args[5])
nukescen = paste(Args[6])
outdir = paste(Args[7])
gdxhydro = paste0(Args[1],"inputs\\capacitydata\\hydrounitdata.gdx")


rs = as.data.frame(read.csv("rsmap.csv"))

rsm = melt(rs,id="X")
colnames(rsm) = c("rs","r","val")
rsm = rsm[,c("r","rs","val")]
rsm = subset(rsm,val=="Y")
rsnew = rsm[,c("r","rs")]

#original names follow the names from the respective files


#=================================
#   --- Retirements Data ---
#=================================

retdat = rgdx.param(gdxnameRET,nukescen,names=c("t","r","i","UnitCT","value"))


#=================================
# --- NONRSC EXISTING CAPACITY ---
#=================================


#following are indexed by BA
#this one's easy
nonrsc = rgdx.param(gdxname,"CONVOLDqctn")
colnames(nonrsc) = c("i","r","UnitCT","value")

#also need to add storage capacities
stor = rgdx.param(gdxname,"import_store_power_cap_at_grid")
colnames(stor) = c("i","r","value")
stor$UnitCT = "none"
stor = stor[,c("i","r","UnitCT","value")]

nonrsc = rbind(nonrsc,stor)


#====================================
# --- NONRSC PRESCRIBED CAPACITY ---
#====================================

#following are indexed by BA
#this one's easy
pnonrsc = rgdx.param(gdxnamePRES,"PrescriptiveBuildsnqct")
colnames(pnonrsc) = c("t","r","i","UnitCT","value")
pnonrsc_storage = rgdx.param(gdxnamePRES,"PrescriptiveBuildsStorage")
colnames(pnonrsc_storage) = c("t","r","i","value")
pnonrsc_storage$UnitCT = "none"
pnonrsc = rbind(pnonrsc,pnonrsc_storage)



#===============================
# --- RSC EXISTING CAPACITY ---
#===============================

#following are RSC tech that are treated differently in the model
DUPV = rgdx.param(gdxname,"tmpDUPVOn")
UPV = rgdx.param(gdxname,"tmpUPVon")
CSP = rgdx.param(gdxname,"tmpCSPOct")

colnames(DUPV) = c("r","value")
colnames(UPV) = c("r","value")
colnames(CSP) = c("rs","UnitCT","value")


#add cooling tech
DUPV$UnitCT = "none"
UPV$UnitCT = "none"


#DUPV AND UPV both have the same resource region
DUPV$rs = "sk"
UPV$rs = "sk"

#labels need to match
CSP$rs = paste("s",CSP$rs,sep="")

#collect BA info by matching rs with BA
CSP = merge(CSP,rsnew,by=c("rs"))

#data for hydro 
HYD = as.data.frame(read.csv("hydrocap.csv"))
HYD = melt(HYD,id=c("tech","class"))
HYD = HYD[!is.na(HYD$value),]
HYD$rs = "sk"
HYD$UnitCT = "none"
HYD$i = HYD$tech
colnames(HYD) = c("tech","class","r","value","rs","UnitCT","i")

#we can drop the class column as only has one place (HYDClass1)
HYD = HYD[,c("rs","UnitCT","value","r","i")]

#assign tech labels
DUPV$i = "dupv_her"
UPV$i = "upv_her"
CSP$i = "CSP_her"

if(grepl('EIA-NEMS',gdxnameRET)){
	WNew = rgdx.param(gdxnameRET,"WindRetireExisting")
	colnames(WNew) = c("rs","i","t","value")
	} else if (grepl('ABB',gdxnameRET)) {
		WNew = rgdx.param(gdxnameRET,"WindRetire")
		colnames(WNew) = c("rs","c","i","t","value")
	}
WNew$i = paste0(WNew$i,gsub("class","_",WNew$c))
WNew$rs = paste0("s",WNew$rs)
WNew$c = "'init-1'"

WNew = dcast(WNew,i+c+rs~t,value.var="value")
WNew[is.na(WNew)] = 0



#======
# distPV calculations
#======

allout_RSC = rbind(DUPV,UPV,CSP,HYD)


#=================================
# --- RSC PRESCRIBED CAPACITY ---
#=================================

pupv = rgdx.param(gdxnamePRES,"PrescriptiveBuildsNonQn")
colnames(pupv) = c("t","r","i","value")
pupv$i = gsub("DUPV","dupv_her",pupv$i)
pupv$i = gsub("UPV","upv_her",pupv$i)
pupv$rs = "sk"

#load in wind builds
pwind = rgdx.param(gdxnamePRES,"PrescriptiveBuildsWind")
colnames(pwind) = c("t","rs","i","value")
pwind$rs = paste0("s",pwind$rs)
pwind = merge(pwind,rsnew,by=c("rs"))

phyd = rgdx.param(gdxhydro,"PrescriptiveBuildshydcats")
colnames(phyd) = c("t","r","i","value")
phyd$rs = "sk"

pcsp = read.csv("prescribed_csp.csv")
pcsp$rs = paste0("s",pcsp$rs)
pcsp = merge(pcsp,rsnew,by=c("rs"))

prsc = rbind(pupv,pwind,phyd,pcsp)


#=================================
# --- NONRSC RETIREMENTS ---
#=================================

ret = rgdx.param(gdxnameRET,nukescen)
colnames(ret) = c("t","r","i","UnitCT","value")
hydret_ed = rgdx.param(gdxhydro,"PRetire_hydro_all_ed")
colnames(hydret_ed) = c("t","r","value")
hydret_end = rgdx.param(gdxhydro,"PRetire_hydro_all_end")
colnames(hydret_end) = c("t","r","value")
hydret_ed$i = "hydED"
hydret_end$i = "hydEND"

hydret = rbind(hydret_ed,hydret_end)

hydret$UnitCT = "none"

ret = rbind(ret,hydret)


#=================================
# --- HYDRO Capacity Factor ---
#=================================

hydcf = rgdx.param(gdxhydro,"hydcfsn")
colnames(hydcf) = c("i","szn","r","value")


#need names to match
hydcf$szn = gsub("summer","summ",hydcf$szn)
hydcf$szn = gsub("spring","spri",hydcf$szn)
hydcf$szn = gsub("winter","wint",hydcf$szn)
hydcf$id = paste("(",hydcf$i,".",hydcf$szn,".",hydcf$r,")   ",hydcf$value,",",sep="")
hydcf[length(hydcf$id),]$id = gsub(",","",hydcf[length(hydcf$id),]$id)



#hydro cf adjustment by szn
hydcfadj = rgdx.param(gdxhydro,"SeaCapAdj_hy")
colnames(hydcfadj) = c("i","szn","r","value")

#need names to match
hydcfadj$szn = gsub("summer","summ",hydcfadj$szn)
hydcfadj$szn = gsub("spring","spri",hydcfadj$szn)
hydcfadj$szn = gsub("winter","wint",hydcfadj$szn)
hydcfadj$id = paste("(",hydcfadj$i,".",hydcfadj$szn,".",hydcfadj$r,")   ",hydcfadj$value,",",sep="")
hydcfadj[length(hydcfadj$id),]$id = gsub(",","",hydcfadj[length(hydcfadj$id),]$id)


#historical capacity factors for calibation
#not always used - see b_inputs.gms

hydcfhist = melt(as.data.frame(read.csv("cf_hyd_hist.csv")),id=c("r"))
hydcfhist$variable = gsub("X","",hydcfhist$variable)
hydcfhist$id = paste("(",hydcfhist$r,".",hydcfhist$variable,")    ",hydcfhist$value,",",sep="")

hydcfhist$id = gsub("summer","summ",hydcfhist$id)
hydcfhist$id = gsub("spring","spri",hydcfhist$id)
hydcfhist$id = gsub("winter","wint",hydcfhist$id)

hydcfhist[length(hydcfhist$id),]$id = gsub(",","",hydcfhist[length(hydcfhist$id),]$id)



#substitutions for new representation of pcat (and not i)
prsc$i = gsub("_her","",prsc$i)
allout_RSC$i = gsub("_her","",allout_RSC$i)
allout_RSC$i = gsub("CSP","csp-ns",allout_RSC$i)


#note that wind is loaded in a separate file
allout_RSC = subset(allout_RSC,i!="wind_her")
pnonrsc$i = gsub("Gas-CC-NSP","gas-CC-NSP",pnonrsc$i)
pnonrsc$i = tolower(pnonrsc$i)
pnonrsc$i = gsub("-nsp","",pnonrsc$i)

pnonrsc = aggregate(pnonrsc$value,by=list(pnonrsc$t,pnonrsc$r,pnonrsc$i,pnonrsc$UnitCT),FUN=sum)
colnames(pnonrsc) = c("t","r","i","UnitCT","value")

retdat$i = gsub("Gas-CC-NSP","gas-CC-NSP",retdat$i)
retdat$i = tolower(retdat$i)
retdat$i = gsub("-nsp","",retdat$i)
retdat = aggregate(retdat$value,by=list(retdat$t,retdat$r,retdat$i,retdat$UnitCT),FUN=sum)
colnames(retdat) = c("t","r","i","UnitCT","value")


#=================================
# --- Data Export ---
#=================================


print(paste("Writing capacity data in: ",outdir))
write.csv(nonrsc[c("i","r","UnitCT","value")],paste0(outdir,"allout_nonRSC.csv"),row.names=FALSE,quote=FALSE)
write.csv(retdat,paste0(outdir,"retirements.csv"),row.names=FALSE,quote=FALSE)
write.csv(pnonrsc[c("t","i","r","UnitCT","value")],paste0(outdir,"prescribed_nonRSC.csv"),row.names=FALSE,quote=FALSE)
write.csv(allout_RSC[c("i","r","rs","UnitCT","value")],paste0(outdir,"allout_RSC.csv"),row.names=FALSE,quote=FALSE)
write.csv(prsc[c("t","i","r","rs","value")],paste0(outdir,"prescribed_rsc.csv"),row.names=FALSE,quote=FALSE)
write.csv(WNew,paste0(outdir,"wind_retirements.csv"),row.names=FALSE,quote=FALSE)
write.table(hydcf[,c("id")],paste0(outdir,"hydcf.txt"),quote=FALSE,row.names = FALSE,col.names = FALSE)
write.table(hydcfadj[,c("id")],paste0(outdir,"hydcfadj.txt"),quote=FALSE,row.names = FALSE,col.names = FALSE)
write.table(hydcfhist[,c("id")],paste0(outdir,"hydcfhist.txt"),quote=FALSE,row.names = FALSE,col.names = FALSE)


print("writecapdat.R completed successfully")



