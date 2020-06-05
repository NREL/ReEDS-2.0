### What is Docker anyways? 

Docker is a tool which allows us to create “containers” in which we can run software. Think of containers as a self-contained virtual machine, with its own operating system (linux), software installations, and user preferences already preconfigured. This virtual machine is command line only (no graphical user interface) and it is running on your computer, using an amount of resources (CPU cores, RAM) that you can configure. Although this concept can be confusing, the big benefit of using docker is that everyone who uses this container should have an identical environment, complete with all software dependencies installed. That way, when anyone runs ReEDS within that container, they will have the exact same experience as anyone else doing the same. 

Docker has “images” and “containers”, images serve as the starting point, telling docker what to install and how to configure things. Containers represent individual instances of this image that you can actually do stuff on. For example, you could follow the instructions below to create a ReEDS image (using the `docker build`) command, and then create two containers, and run a ReEDS model on each one. This isn’t necessarily how you should structure your model runs, but is an example to explain the difference between images and containers, as those two terms will come up a lot when using docker. 


### So, how do we get started:

You can [download docker](https://docs.docker.com/get-docker/) here for your operating system. For most operating systems, you should be installing Docker Desktop, which includes the command line version of docker along with “docker dashboard” which provides a graphical interface to monitor running containers. 

Once installed, open your command line of choice and run `docker run hello-world`. After a second, docker should print to the command line a detailed message explaining what it did in order to print “Hello from Docker!”. The gist, is that docker created a container with its own self contained operating system on your computer and instructed that operating system to send a “hello world” message back to your command line. Pretty neat! 

Finally, I encourage you to run `docker run -it ubuntu bash`. This will download an ubuntu image from docker hub (an online repository of secure docker image), which will be around 30 MBs, it will then set up a new container using the image. The `-it` flag indicates that you want an ‘interactive’ mode that will let you enter the command line within this operating system, which you are specifying that you want the commonly used `bash` shell. 

### Using docker with ReEDS India:

The ReEDS model has several dependencies including gams, R, and python which can sometimes be complicated to install and configure for users. The following commands will create a new docker image (from which you can create docker containers) to easily install and run ReEDS. 


First we need to download ReEDS onto your local machine. For this we use git’s `clone` command. The `-b` flag specifies which branch we want. 

```
git clone https://github.com/skoeb/ReEDS_OpenAccess.git -b India_Docker
```

If you are familiar with ReEDS or git, you can think of this `India_Docker` branch as a wrapper that exists one directory up from the ReEDS source code (such as the version on the `India`) branch. The actual ReEDS source code lives within the `src` directory, which uses git’s submodule feature to stay up to date. If this didn’t make sense, don’t worry, just run the following commands. 

```
cd ReEDS_OpenAccess #move into the git directory
git submodule init #initialize the `src` directory as its own git repo
git submodule update #pull down the India branch into the `/src` director
```

Great! We’re done on the git side of things. We can now `build` the docker image. The instructions for this are contained within the `Dockerfile` in this repository. Let’s run:

```
docker build --tag reeds .
```

This will take some time, as we are:
- creating a new image with its own operating system
- downloading anaconda, python, r, and gams within the operating system
- configuring some environmental variables

When this completes, we can create a ‘container’ from our image. To do so, we use the `docker run` command, and can specify that we want to run a container using the reeds image that we named with `--tag` earlier. We also need to 'mount' the  `reeds/` directory (containing the ReEDS India source code) as a volume within the container. That way, we can see model results on our local drive. To do this we provide docker with a 'map' of the absolute path to the `reeds/` directory on our local computer, and where we want it within the linux container (`/usr/src/reeds`). 

Where this folder is on your local computer will vary. For instance, on __Mac, Linux, and Windows Powershell__ you can run:

```
docker run -it -v ${PWD}/reeds/:/usr/src/reeds reeds
```

But in other console emulators (such as __ConEmu__ on windows), we may need to change this to:

```
docker run -it -v %CD%/reeds/:/usr/src/reeds reeds
```

This command runs an interactive session (i.e. you will be taken to the command prompt within the container) and sets up a docker `volume` between the `src/` directory on your local machine, and the `usr/src/reeds` directory on the virtual machine. This way, any changes made on either side, appear magically in the other! This allows the user to edit scenarios or code on their local machine, have the updated model run within the docker container, and then view results back on the local machine. Yay Docker!

From this point, you should find yourself on a command line within the container. You can proceed to edit any files as you would on your local machine (i.e. server or laptop) and run ReEDS according to the instructions provided within that branches' `README.md`

There is one more package that we need to install. To do this, run the following lines from within the docker container:
```
conda activate reeds #activate reeds environment
Rscript ../packagesetup.R $this will install the gdxrrw package, which is not currently available on CRAN
```

To run the model, first make sure that you have activated the 'reeds' conda environment. Run this line:
```
conda activate reeds
```

Proceed to run the model with the instructions provided within `README.md`
```
python run_model.py
```

Other notes:
------------
- You should have a little whale icon on your task bar, indicating that Docker is running. There is a 'preferences' option within this menu that will allow you to determine the resources allocated to docker. 
- The gamslice.txt folder in this directory is an expired GAMS license available to NREL. You should replace this file (either within the repo, or within your container at `/opt/gams/gams291._linux_x64_64_sfc/gamslice.txt` with a valid license.
- If you want to run ReEDS in the background, you can replace `-it` with `-d` in the `docker run` command, which will allow you to detach from the container with the `cntrl-D` command.
