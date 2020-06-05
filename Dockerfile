
# pull miniconda 3.x from continuum io and create an environment with python 3.6
FROM continuumio/miniconda3

# Create conda env from .yml
COPY reeds.yml /usr/src/reeds.yml
RUN conda env create -f /usr/src/reeds.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "reeds", "/bin/bash", "-c"]

# install additional R dependencies
COPY gdxrrw_1.0.5.tar.gz /usr/src/gdxrrw_1.0.5.tar.gz
COPY packagesetup.R /usr/src/packagesetup.R
#RUN conda activate reeds
#RUN Rscript /usr/src/packagesetup.R

#make a volume called reeds and make that the working directory
RUN mkdir /usr/src/reeds
VOLUME /usr/src/reeds
WORKDIR /usr/src/reeds

#make a directory to store GAMS
RUN mkdir /opt/gams

#download gams source code
RUN wget https://d37drm4t2jghv5.cloudfront.net/distributions/29.1.0/linux/linux_x64_64_sfx.exe -O /opt/gams/gams_linux.exe
# COPY linux_x64_64_sfx.exe /opt/gams/gams_linux.exe

#change to that directory
WORKDIR /opt/gams

#set permissions accordingly
RUN chmod u+x /opt/gams/gams_linux.exe

#run the install process
RUN /opt/gams/gams_linux.exe

#copy over the user's gams license
COPY gamslice.txt /opt/gams/gams29.1_linux_x64_64_sfx/gamslice.txt

#change back to the ReEDS directory
WORKDIR /usr/src/reeds

#install VIM, a simple text editor
RUN apt-get -y install vim

# set env path 
ENV PATH "$PATH:/opt/gams/gams29.1_linux_x64_64_sfx"
ENV GAMS_DIR=/opt/gams/gams29.1_linux_x64_64_sfx