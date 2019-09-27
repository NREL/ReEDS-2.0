sink("gamslog.txt",append=TRUE)

library(plyr)

print("Starting calculation of R\\plantcostprep.R")

if(!exists("Args")) Args=commandArgs(TRUE)

#plantcostprep.R
# Args=list()
# Args[1]="c:\\ReEDS\\ReEDS-2.0\\"
# Args[2]="conv_ATB_2019"
# Args[3]="wind_ATB_2019_mid"
# Args[4]="upv_ATB_2019_mid"
# Args[5]="csp_ATB_2019_mid"
# Args[6]="battery_ATB_2019_mid"
# Args[7]="geo_ATB_2019_mid"
# Args[8]="hydro_ATB_2019_mid"


convcase = Args[2]
windcase = Args[3]
upvcase = Args[4]
cspcase = Args[5]
batterycase = Args[6]
geocase = Args[7]
hydrocase = Args[8]
caescase = "caes_reference"
outdir = Args[9]


setwd(paste0(Args[1],"inputs\\plant_characteristics"))

# Remove files that will be created as outputs
files = c("plantcharout.txt","windcfout.txt")
for (f in files) {
  if (file.exists(f))
    #Delete file if it exists
    file.remove(f)  
}

convfile = paste0(convcase,".csv")
windfile = paste0(windcase,".csv")
upvfile = paste0(upvcase,".csv")
cspfile = paste0(cspcase,".csv")
batteryfile = paste0(batterycase,".csv")
geofile = paste0(geocase,".csv")
hydrofile = paste0(hydrocase,".csv")
caesfile = paste0(caescase,".csv")

dollaryear = as.data.frame(read.csv("dollaryear.csv"))
deflator = as.data.frame(read.csv("../deflator.csv"))
colnames(deflator)[1] = "Dollar.Year"

dollaryear = merge(dollaryear,deflator,by = "Dollar.Year")

upv = as.data.frame(read.csv(upvfile))
upv$i = "UPV"

#Adjust cost data to 2004$
deflate = dollaryear$Deflator[dollaryear$Scenario == upvcase]
upv$capcost = upv$capcost * deflate
upv$fom = upv$fom * deflate
upv$vom = upv$vom * deflate

upv_stack = data.frame()

#create categories for all upv cats
for(n in seq(1,10,1)){
  tupv = upv
  tupv$i = paste0("UPV_",n)
  upv_stack = rbind(upv_stack,tupv)
}

conv = as.data.frame(read.csv(convfile))
deflate = dollaryear$Deflator[dollaryear$Scenario == convcase]
conv$capcost = conv$capcost * deflate
conv$fom = conv$fom * deflate
conv$vom = conv$vom * deflate

winddata = as.data.frame(read.csv(windfile))
colnames(winddata) = c("tech","trg","t","cf","capcost","fom","vom")

winddata$tech = gsub("ONSHORE","wind-ons",winddata$tech)
winddata$tech = gsub("OFFSHORE","wind-ofs",winddata$tech)
winddata$i = paste0(winddata$tech,"_",winddata$trg)
wind_stack = winddata[,c("t","i","capcost","fom","vom")]
deflate = dollaryear$Deflator[dollaryear$Scenario == windcase]
wind_stack$capcost = wind_stack$capcost * deflate
wind_stack$fom = wind_stack$fom * deflate
wind_stack$vom = wind_stack$vom * deflate


csp = as.data.frame(read.csv(cspfile))
deflate = dollaryear$Deflator[dollaryear$Scenario == cspcase]
csp$capcost = csp$capcost * deflate
csp$fom = csp$fom * deflate
csp$vom = csp$vom * deflate

csp_stack = data.frame()

for(n in seq(1,12,1)){
  tcsp = csp
  tcsp$i = paste0(csp$type,"_",n)
  csp_stack = rbind(csp_stack,tcsp)
}
csp_stack = csp_stack[,c("t","capcost","fom","vom","i")]

battery = as.data.frame(read.csv(batteryfile))
battery$i = "battery"
deflate = dollaryear$Deflator[dollaryear$Scenario == batterycase]
battery$capcost = battery$capcost * deflate
battery$fom = battery$fom * deflate
battery$vom = battery$vom * deflate

caes = as.data.frame(read.csv(caesfile))
caes$i = "caes"
deflate = dollaryear$Deflator[dollaryear$Scenario == caescase]
caes$capcost = caes$capcost * deflate
caes$fom = caes$fom * deflate
caes$vom = caes$vom * deflate

alldata = rbind.fill(conv,upv_stack,wind_stack,csp_stack,battery,caes)

alldata$t = as.numeric(as.character(alldata$t))

#Convert values from $/kW to $/MW
alldata$capcost = round(alldata$capcost * 1000)
alldata$fom = round(alldata$fom * 1000)

#Replace NAs with zeros
alldata[is.na(alldata)] = 0

#Combine data into a single list
outdata = c(paste0("(",alldata$i,".",alldata$t,".capcost)","  ",alldata$capcost,","),
            paste0("(",alldata$i,".",alldata$t,".fom)","  ",alldata$fom,","),
            paste0("(",alldata$i,".",alldata$t,".vom)","  ",alldata$vom,","),
            paste0("(",alldata$i,".",alldata$t,".heatrate)","  ",alldata$heatrate,","),
            paste0("(",alldata$i,".",alldata$t,".rte)","  ",alldata$rte,",")
)

#Remove the comma for the last entry
outdata[length(outdata)] = gsub(",","",outdata[length(outdata)])


### Wind Capacity Factors

windcf = winddata[,c("t","i","cf")]
windcf$id = paste0("(",windcf$t,".",windcf$i,")","  ",windcf$cf,",")
windcf[length(windcf$id),]$id = gsub(",","",windcf[length(windcf$id),]$id)
outwindcf = data.frame(out=windcf[,c("id")])


### Geo Cost Multipliers

geo = read.csv(geofile, check.names = F)


### Hydro Cost Multipliers

hydro = read.csv(hydrofile, check.names = F)


print(paste("writing plant data to:",getwd()))
write.table(outdata,paste0(outdir,"plantcharout.txt"),row.names=FALSE,col.names=FALSE,quote=FALSE)
write.table(outwindcf,paste0(outdir,"windcfout.txt"),row.names=FALSE,col.names=FALSE,quote=FALSE)
write.csv(geo,paste0(outdir,"geocapcostmult.csv"),row.names=FALSE)
write.csv(hydro,paste0(outdir,"hydrocapcostmult.csv"),row.names=FALSE)
print("plantcostprep.R completed successfully")