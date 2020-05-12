
# pull anaconda 3.x from continuum io and create an environment with python 3.6
FROM continuumio/anaconda3
RUN conda create -n env python=3.6

#install r-base is more reliable than building the environment with R, not sure why...
RUN conda install r-base

#install the python libraries not included with anaconda
RUN pip install gdxpds
#RUN pip install bokeh

#make a directory called reeds and make that the working directory
RUN mkdir /usr/src/reeds
WORKDIR /usr/src/reeds

# copy directory contents to the container
COPY src/. .

# -- install gams --

#make a directory to store GAMS
RUN mkdir /opt/gams
#download gams source code
# RUN wget https://d37drm4t2jghv5.cloudfront.net/distributions/29.1.0/linux/linux_x64_64_sfx.exe -O /opt/gams/gams_linux.exe
#copy gams
COPY linux_x64_64_sfx.exe /opt/gams/gams_linux.exe
#change to that directory
WORKDIR /opt/gams
#set permissions accordingly
RUN chmod u+x /opt/gams/gams_linux.exe
#run the install process
RUN /opt/gams/gams_linux.exe
#copy over the user's gams license
COPY gamslice.txt /opt/gams/gams29.1_linux_x64_64_sfx/gamslice.txt

# -- End GAMS Install --

#change back to the ReEDS directory
WORKDIR /usr/src/reeds

#install VIM
RUN apt-get -y install vim

# set env path 
ENV PATH "$PATH:/opt/gams/gams29.1_linux_x64_64_sfx"
ENV GAMS_DIR=/opt/gams/gams29.1_linux_x64_64_sfx
