
print("")
print("Installing necessary packages")
print("")

list.of.packages <- c(	"plyr","lazyeval","colorspace","data.table",
						"dplyr","dtplyr","ggplot2","ggthemes","grid","gtools",
						"reshape2","rlang","scales","stringr","stringi",
						"xtable","zoo","tibble")


#packages used only on the demand side, 
#                   no longer used,
#                   or installed via dependency:
#"RColorBrewer",
#"taRifx"
#"doBy"
#"iterators"
#"openxlsx"
#"doParallel"
#"lpSolve"
#"MASS"

new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos = "http://cran.rstudio.com/", dep = TRUE)

if(!("gdxrrw") %in% installed.packages()[,"Package"]){
	install.packages("input_processing\\R\\gdxrrw_0.4.0.zip", repos = NULL)
}

######################################################
## Check to see if packages are installed correctly ##
######################################################

for(i in c(list.of.packages,"gdxrrw")) {
	if (!suppressMessages(require(i,character.only = TRUE)))
		{print(paste("Package",i,"not installed correctly"))}
		else 
		{print(paste("Package",i,"installed correctly"))}
}


