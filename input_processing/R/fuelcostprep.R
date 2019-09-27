sink("gamslog.txt",append=TRUE)

print("Starting calculation of fuelcostprep.R")

library(reshape2)

if(!exists("Args")) Args=commandArgs(TRUE)

#fuelcostprep.R
# Args=list()
# Args[1]="C:\\ReEDS\\ReEDS-2.0\\"
# Args[2]="AEO_2018_reference"
# Args[3]="AEO_2018_reference"
# Args[4]="AEO_2018_reference"


setwd(paste0(Args[1],"inputs\\fuelprices"))

# Remove files that will be created as outputs
files = c("fprice.csv","ng_price_cendiv.csv","ng_demand_elec.csv","ng_demand_tot.csv","alpha.csv")
for (f in files) {
  if (file.exists(f))
    #Delete file if it exists
    file.remove(f)  
}


coalscen = Args[2]
uraniumscen = Args[3]
ngscen = Args[4]
outdir = paste(Args[5])

r_cendiv = read.csv("..\\r_cendiv.csv")

dollaryear = as.data.frame(read.csv("dollaryear.csv"))
deflator = as.data.frame(read.csv("../deflator.csv"))
colnames(deflator)[1] = "Dollar.Year"

dollaryear = merge(dollaryear,deflator,by = "Dollar.Year")


### Coal
coal = read.csv(paste0("coal_",coalscen,".csv"))
coal = melt(coal, id = c("year"))
colnames(coal)[2] = "cendiv"

#Adjust prices to 2004$
deflate = dollaryear$Deflator[dollaryear$Scenario == coalscen]
coal$value = coal$value * deflate

#Map census regions to BAs
coal = merge(coal,r_cendiv, by = "cendiv")
coal = coal[,c("year","r","value")]
colnames(coal) = c("t","r","coal")

### Uranium
uranium = read.csv(paste0("uranium_",uraniumscen,".csv"))
deflate = dollaryear$Deflator[dollaryear$Scenario == uraniumscen]
uranium$cost = uranium$cost * deflate
uranium = merge(uranium,r_cendiv)
uranium = uranium[,c("year","r","cost")]
colnames(uranium) = c("t","r","uranium")


### Natural Gas Prices
ngprice = read.csv(paste0("ng_",ngscen,".csv"))
ngprice = melt(ngprice, id = c("year"))
colnames(ngprice)[2] = "cendiv"

#Adjust prices to 2004$
deflate = dollaryear$Deflator[dollaryear$Scenario == ngscen]
ngprice$value = ngprice$value * deflate

#Map census regions to BAs
ngprice = merge(ngprice,r_cendiv, by = "cendiv")
ngprice = ngprice[,c("year","r","value")]
colnames(ngprice) = c("t","r","naturalgas")


### Merge fuel price data
fuel = merge(coal,uranium, by = c("t","r"))
fuel = merge(fuel,ngprice, by = c("t","r"))


### Natural Gas Price by Census Region
ngprice2 = read.csv(paste0("ng_",ngscen,".csv"))
n = ngprice2$year
ngprice2 = data.frame(t(ngprice2[,-1]))
colnames(ngprice2) = n

#Adjust prices to 2004$
deflate = dollaryear$Deflator[dollaryear$Scenario == ngscen]
ngprice2 = ngprice2 * deflate


### Natural Gas Demand
#Electric sector only demand
ngdemand = read.csv(paste0("ng_demand_",ngscen,".csv"))
n = ngdemand$year
ngdemand = data.frame(t(ngdemand[,-1]))
colnames(ngdemand) = n

#Total demand
ngtotdemand = read.csv(paste0("ng_tot_demand_",ngscen,".csv"))
n = ngtotdemand$year
ngtotdemand = data.frame(t(ngtotdemand[,-1]))
colnames(ngtotdemand) = n

### Natural Gas Alphas (already in 2004$)
alpha = read.csv(paste0("alpha_",ngscen,".csv"))

write.csv(fuel,paste0(outdir,"fprice.csv"),row.names=FALSE)
write.csv(ngprice2,paste0(outdir,"ng_price_cendiv.csv"))
write.csv(ngdemand,paste0(outdir,"ng_demand_elec.csv"))
write.csv(ngtotdemand,paste0(outdir,"ng_demand_tot.csv"))
write.csv(alpha,paste0(outdir,"alpha.csv"),row.names=FALSE)


print("fuelcostprep.R completed successfully")


