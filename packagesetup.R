print("")
print("Installing pacman, reshape2, rmarkdown, and gdxrrw")
print("")

install.packages("gdxrrw_1.0.5.tar.gz",repos=NULL,type="source")
install.packages("pacman", repos="http://cran.rstudio.com/", dep=TRUE)
install.packages("reshape2", repos="http://cran.rstudio.com/", dep=TRUE)
install.packages("rmarkdown", repos="http://cran.rstudio.com/", dep=TRUE)