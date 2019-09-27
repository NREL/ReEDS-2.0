sink("gamslog.txt",append=TRUE)

#the purpose of this file is to take the GDX files resultings from
#the call to d4_translate_variability.r, merge those together, then 
#output a new file r2_in_int_%case%_%niter%.gdx

library(gdxrrw)
if(!exists("Args")) Args=commandArgs(TRUE)
setwd(paste(Args[1]))
igdx(paste(Args[2]))
infile_curt = paste0(Args[3],".gdx")
infile_cc = paste0(Args[4],".gdx")



#setwd("d:\\max\\r2_link\\")
#igdx("c:\\gams\\win64\\24.7\\")
#infile = paste("inout\\gdxfiles\\t4_test1_1.gdx",sep="")


cc_old_mw = rgdx.param(infile_cc,"season_all_cc",names=c("file","i","r","szn","t","value"))
#cc_old_mw_i = rgdx.param(infile_cc,"cc_old_mw_i",names=c("file","r","tech","szn","t","value"))
marginalcc = rgdx.param(infile_cc,"season_all_cc_mar",names=c("file","i","r","szn","t","value"))
surplusmarginal = rgdx.param(infile_curt,"surplusmarginal",names=c("file","i","r","rs","h","value"))
MRsurplusmar = rgdx.param(infile_curt,"MRsurplusmarginal",names=c("file","r","h","t","value"))
surpold = rgdx.param(infile_curt,"surpold",names=c("file","r","h","t","value"))

#reorder marginal cc to match reeds
#marginalcc = marginalcc[,c("file","i","r","rs","szn","t","value")]

remove_file_column <- function(x,name){
  x = as.data.frame(x[,!(names(x) %in% c("file"))])
  attr(x,"symName") = name
  x
}

columnfactors <- function(df){
  for(j in colnames(df)[1:length(colnames(df))-1]){
    df[,j] = factor(df[,j],levels=unique(df[,j]))
  }
  return(as.data.frame(df))
}

#reorder cc_old_mw_i
#cc_old_mw_i = cc_old_mw_i[,c("file","tech","r","szn","t","value")]
#cc_old_mw_i$tech = gsub("PV","allpv",cc_old_mw_i$tech)

cc_old_mw = columnfactors(remove_file_column(cc_old_mw,"season_all_cc"))
#cc_old_mw_i = columnfactors(remove_file_column(cc_old_mw_i,"cc_old_mw_i"))
marginalcc = columnfactors(remove_file_column(marginalcc,"marginalcc"))
surplusmarginal = columnfactors(remove_file_column(surplusmarginal,"surplusmarginal"))
MRsurplusmar = columnfactors(remove_file_column(MRsurplusmar,"MRsurplusmarginal"))
surpold = columnfactors(remove_file_column(surpold,"surpold"))

out_curt = gsub(".gdx","_out.gdx",infile_curt)
print(paste("Writing merged curtailment data as ",out_curt))
wgdx.lst(out_curt,surplusmarginal,MRsurplusmar,surpold)

out_cc = gsub(".gdx","_out.gdx",infile_cc)
print(paste("Writing merged CC data as ",out_cc))
wgdx.lst(out_cc,cc_old_mw,marginalcc)


