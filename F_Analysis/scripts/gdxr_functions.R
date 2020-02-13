defNames <- function(n,isPar)
{
  if (1 == n) {
    dnames <- list("i")
  } else if (2 == n) {
    dnames <- list("i","j")
  } else if (3 == n) {
    dnames <- list("i","j","k")
  } else {
    dnames <- list()
    for (d in c(1:n)) {
      dnames[[d]] <- paste0("i",d)
    }
  }
  if (isPar) {
    dnames[[n+1]] <- "value"
  }
  return(dnames)
} # defNames

patchNames <- function(dNames,n)
{
  if (n > 3) {
    for (d in c(1:n)) {
      if ("*" == dNames[[d]]) {
        dNames[[d]] <- paste0(".i",d)
      }
    }
    return(dNames)
  }
  
  if ("*" == dNames[[1]]) {
    dNames[[1]] <- paste0(".i")
  }
  if (1 == n) {
    return(dNames)
  }
  if ("*" == dNames[[2]]) {
    dNames[[2]] <- paste0(".j")
  }
  if (2 == n) {
    return(dNames)
  }
  if ("*" == dNames[[3]]) {
    dNames[[3]] <- paste0(".k")
  }
  return(dNames)
} # patchNames

rgdx.var.eq <- function (gdxName, symName, names = "names", compress = FALSE, ts = FALSE, 
                         squeeze = TRUE, useDomInfo = TRUE, check.names = TRUE) 
{
  
  sym <- rgdx(gdxName, list(name = symName, compress = compress, 
                            ts = ts), squeeze = squeeze, useDomInfo = useDomInfo)
  
  if (sym$type != "variable" && sym$type != "equation") {
    stop("Expected to read a variable: symbol ", symName, 
         " is a ", sym$type)
  }
  symDim <- sym$dim
  if (symDim < 1) {
    stop("Symbol ", symName, " is a scalar: data frame output not possible")
  }
  fnames <- list()
  if (is.null(names)) {
    domainNames <- getOption("gdx.domainNames", default = T)
    if (domainNames) {
      domainNames <- !(("NA" == sym$domInfo) || ("none" == 
                                                   sym$domInfo) || ("unknown" == sym$domInfo))
    }
    if (domainNames) {
      fnames <- sym$domains
      if (check.names) {
        fnames <- patchNames(fnames, symDim)
      }
      fnames[[symDim + 1]] <- sym$name
    }else{
      fnames <- defNames(symDim, T)
    }
  }else{
    if (is.vector(names)) {
      namlen <- length(names)
      d2 <- 1
      for (d in c(1:symDim)) {
        fnames[[d]] <- as.character(names[d2])
        d2 <- d2 + 1
        if (d2 > namlen) 
          d2 <- 1
      }
      if (namlen <= symDim) {
        fnames[[symDim + 1]] <- "value"
      }else{
        fnames[[symDim + 1]] <- as.character(names[d2])
      }
    }else if (is.list(names)) {
      namlen <- length(names)
      d2 <- 1
      for (d in c(1:symDim)) {
        fnames[[d]] <- as.character(names[[d2]])
        d2 <- d2 + 1
        if (d2 > namlen) 
          d2 <- 1
      }
      if (namlen <= symDim) {
        fnames[[symDim + 1]] <- "value"
      }else{
        fnames[[symDim + 1]] <- as.character(names[[d2]])
      }
    }else{
      for (d in c(1:symDim)) {
        fnames[[d]] <- paste(as.character(names), d, 
                             sep = ".")
      }
      fnames[[symDim + 1]] <- "value"
    }
  }
  if (check.names) {
    fnames <- make.names(fnames, unique = TRUE)
  }
  dflist <- list()
  if (0 == dim(sym$val)[1]) {
    for (d in c(1:symDim)) {
      dflist[[d]] <- factor(numeric(0))
    }
  }else{
    for (d in c(1:symDim)) {
      nUels <- length(sym$uels[[d]])
      dflist[[d]] <- factor(as.integer(sym$val[, d]), seq(to = nUels), 
                            labels = sym$uels[[d]])
    }
  }
  dflist[[symDim + 1]] <- sym$val[, symDim + 1]
  names(dflist) <- fnames
  symDF <- data.frame(dflist, check.names = check.names)
  attr(symDF, "symName") <- sym$name
  attr(symDF, "domains") <- sym$domains
  if (is.character(sym$domInfo)) {
    attr(symDF, "domInfo") <- sym$domInfo
  }
  if (ts) {
    attr(symDF, "ts") <- sym$ts
  }
  return(symDF)
}#rgdx variable or equation

rgdx.param2 <- function(gdxName, symName, names=NULL, compress=FALSE,
                        ts=FALSE, squeeze=TRUE, useDomInfo=TRUE,
                        check.names=TRUE)
{
  sym <- rgdx(gdxName, list(name=symName,compress=compress,ts=ts),squeeze=squeeze,useDomInfo=useDomInfo)
  if (sym$type != "parameter") {
    stop ("Expected to read a parameter: symbol ", symName, " is a ", sym$type)
  }
  symDim <- sym$dim
  if (symDim < 1) {
    symDF <- rgdx.scalar(gdxName, symName)
  }else{
    
    fnames <- list()
    if (is.null(names)) {
      ## no names passed via args
      domainNames <- getOption('gdx.domainNames',default=T)
      if (domainNames) {
        domainNames <- ! ( ("NA"==sym$domInfo) ||
                             ("none"==sym$domInfo) ||
                             ("unknown"==sym$domInfo) )
      }
      if (domainNames) {
        fnames <- sym$domains
        if (check.names) {
          fnames <- patchNames(fnames,symDim)
        }
        fnames[[symDim+1]] <- sym$name
      }
      else {
        fnames <- defNames(symDim,T)
      }
    } else {
      # process the user-provided names
      if (is.vector(names)) {
        namlen <- length(names)
        d2 <- 1
        for (d in c(1:symDim)) {
          fnames[[d]] <- as.character(names[d2])
          d2 <- d2+1
          if (d2 > namlen) d2 <- 1
        }
        # consider 2 cases: names provided just for the index cols,
        # or for the data column too
        if (namlen <= symDim) {
          fnames[[symDim+1]] <- "value"
        }
        else {
          fnames[[symDim+1]] <- as.character(names[d2])
        }
      } else if (is.list(names)) {
        namlen <- length(names)
        d2 <- 1
        for (d in c(1:symDim)) {
          fnames[[d]] <- as.character(names[[d2]])
          d2 <- d2+1
          if (d2 > namlen) d2 <- 1
        }
        # consider 2 cases: names provided just for the index cols,
        # or for the data column too
        if (namlen <= symDim) {
          fnames[[symDim+1]] <- "value"
        }
        else {
          fnames[[symDim+1]] <- as.character(names[[d2]])
        }
      } else {
        for (d in c(1:symDim)) {
          fnames[[d]] <- paste(as.character(names),d,sep=".")
        }
        fnames[[symDim+1]] <- "value"
      }
    }
    if (check.names) {
      fnames <- make.names(fnames,unique=TRUE)
    }
    
    dflist <- list()
    for (d in c(1:symDim)) {
      nUels <- length(sym$uels[[d]])
      # first arg to factor must be integer, not numeric: different as.character results
      dflist[[d]] <- factor(as.integer(sym$val[,d]), seq(to=nUels), labels=sym$uels[[d]])
    }
    dflist[[symDim+1]] <- sym$val[,symDim+1]
    names(dflist) <- fnames
    symDF <- data.frame(dflist, check.names=check.names)
    attr(symDF,"symName") <- sym$name
    attr(symDF,"domains") <- sym$domains
    ## for now, make domInfo conditional
    if (is.character(sym$domInfo)) {
      attr(symDF,"domInfo") <- sym$domInfo
    }
    if (ts) {
      attr(symDF,"ts") <- sym$ts
    }
  }
  return(symDF)
} # rgdx.param2

rgdx.scalar2 <- function(gdxName, symName, ts=FALSE)
{
  request <- list(name=symName,ts=ts)
  readsym <- rgdx(gdxName, request)
  # if (readsym$type != "parameter") {
  #   stop ("Expected to read a scalar: symbol ", symName, " is a ", readsym$type)
  # }
  dimsym <- readsym$dim
  if (dimsym > 0) {
    stop ("Parameter ", symName, " has dimension ", dimsym, ": scalar output not possible")
  }
  c <- 0
  if (1 == dim(readsym$val)[1]) {
    c <- readsym$val[1,1]
  }
  attr(c,"symName") <- readsym$name
  if (ts) {
    attr(c,"ts") <- readsym$ts
  }
  return(c)
}#rgdx.scalar2

rgdx.alltype <- function(gdxFileName, symbolName, objectType){
  
  if(rgdx(gdxFileName, requestList = list(name=symbolName))$dim < 1){
    symdf <- rgdx.scalar2(gdxName = gdxFileName, symName = symbolName)
    symtype <- "scalar"
  }else{
    if(objectType=="sets"){
      symdf <- rgdx.set(gdxName = gdxFileName, symName = symbolName)
    }
    if(objectType=="parameters"){
      symdf <- rgdx.param2(gdxName = gdxFileName, symName = symbolName)
    }
    if(objectType=="variables" || objectType=="equations"){
      symdf <- rgdx.var.eq(gdxName = gdxFileName, symName = symbolName)
    }
    symtype <- objectType
  }
  
  return(list("Type" = symtype, "DF" = symdf))
  
}
