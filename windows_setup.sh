# gams installation directory
firstgams=$(find /c/ -wholename "*/gams.exe" -printf '%h' -quit)
basedir=$(pwd)
cd ${firstgams//" "/"\ "}
cd ..
gamsparent=$(pwd)
cd $basedir
clear
# ask the user which installation to use
PS3="Select which gams installation to use: "
select GAMS in $(find ${gamsparent//" "/"\ "} -wholename "*/gams.exe" -printf '%h ')
do
	echo 'You chose ' $GAMS 
	echo '...Linking Directories'
	break
done

# make a symbolic link to gams in the local repo's gams directory
echo "The user selected " $GAMS >> testlog.txt
ln -s $GAMS/ ./gams

# setup the PATH environment variables
LOCALGAMS=$(find $(pwd) -wholename "/*/gams.exe" -printf '%h')
PYTHON=${LOCALGAMS//" "/"\ "}"/GMSPython"
SCRIPTS=$PYTHON"/Scripts"
#PATHVAR=(${!PATH@})

# write the PATH variables to .bashrc and add them to this gibash's PATH variable
echo export PATH=$PYTHON:$SCRIPTS:${LOCALGAMS//" "/"\ "}:${PATH//" "/"\ "} > ./.bashrc
export PATH=$PYTHON:$SCRIPTS:$LOCALGAMS:$PATH


# install python packages in the gams link directory
echo "...Installing Python packages"
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py >> setuplog.txt
python get-pip.py >> setuplog.txt
python -m pip install gdxpds >> setuplog.txt
python -m pip install xlrd >> setuplog.txt
python -m pip install jinja2 >> setuplog.txt
python -m pip install bokeh >> setuplog.txt
python -m pip install scipy >> setuplog.txt
python -m pip install alabaster==0.7.12 >> setuplog.txt
python -m pip install applaunchservices==0.2.1 >> setuplog.txt
python -m pip install appnope==0.1.0 >> setuplog.txt
python -m pip install appscript==1.0.1 >> setuplog.txt
python -m pip install argh==0.26.2 >> setuplog.txt
python -m pip install asn1crypto==1.3.0 >> setuplog.txt
python -m pip install astroid==2.3.3 >> setuplog.txt
python -m pip install astropy==4.0 >> setuplog.txt
python -m pip install atomicwrites==1.3.0 >> setuplog.txt
python -m pip install attrs==19.3.0 >> setuplog.txt
python -m pip install autopep8==1.4.4 >> setuplog.txt
python -m pip install Babel==2.8.0 >> setuplog.txt
python -m pip install backcall==0.1.0 >> setuplog.txt
python -m pip install backports.functools-lru-cache==1.6.1 >> setuplog.txt
python -m pip install backports.shutil-get-terminal-size==1.0.0 >> setuplog.txt
python -m pip install backports.tempfile==1.0 >> setuplog.txt
python -m pip install backports.weakref==1.0.post1 >> setuplog.txt
python -m pip install beautifulsoup4==4.8.2 >> setuplog.txt
python -m pip install bitarray==1.2.1 >> setuplog.txt
python -m pip install bkcharts==0.2 >> setuplog.txt
python -m pip install bleach==3.1.0 >> setuplog.txt
python -m pip install bokeh==1.4.0 >> setuplog.txt
python -m pip install boto==2.49.0 >> setuplog.txt
python -m pip install Bottleneck==1.3.2 >> setuplog.txt
python -m pip install certifi==2019.11.28 >> setuplog.txt
python -m pip install cffi==1.14.0 >> setuplog.txt
python -m pip install chardet==3.0.4 >> setuplog.txt
python -m pip install Click==7.0 >> setuplog.txt
python -m pip install cloudpickle==1.3.0 >> setuplog.txt
python -m pip install clyent==1.2.2 >> setuplog.txt
python -m pip install colorama==0.4.3 >> setuplog.txt
python -m pip install contextlib2==0.6.0.post1 >> setuplog.txt
python -m pip install cryptography==2.8 >> setuplog.txt
python -m pip install cycler==0.10.0 >> setuplog.txt
python -m pip install Cython==0.29.15 >> setuplog.txt
python -m pip install cytoolz==0.10.1 >> setuplog.txt
python -m pip install dask==2.11.0 >> setuplog.txt
python -m pip install decorator==4.4.1 >> setuplog.txt
python -m pip install defusedxml==0.6.0 >> setuplog.txt
python -m pip install diff-match-patch==20181111 >> setuplog.txt
python -m pip install distributed==2.11.0 >> setuplog.txt
python -m pip install docutils==0.16 >> setuplog.txt
python -m pip install entrypoints==0.3 >> setuplog.txt
python -m pip install et-xmlfile==1.0.1 >> setuplog.txt
python -m pip install fastcache==1.1.0 >> setuplog.txt
python -m pip install filelock==3.0.12 >> setuplog.txt
python -m pip install flake8==3.7.9 >> setuplog.txt
python -m pip install Flask==1.1.1 >> setuplog.txt
python -m pip install fsspec==0.6.2 >> setuplog.txt
python -m pip install future==0.18.2 >> setuplog.txt
python -m pip install gdxcc==7.28.20 >> setuplog.txt
python -m pip install gdxpds==1.1.0 >> setuplog.txt
python -m pip install gevent==1.4.0 >> setuplog.txt
python -m pip install glob2==0.7 >> setuplog.txt
python -m pip install gmpy2==2.0.8 >> setuplog.txt
python -m pip install greenlet==0.4.15 >> setuplog.txt
python -m pip install h5py==2.10.0 >> setuplog.txt
python -m pip install HeapDict==1.0.1 >> setuplog.txt
python -m pip install html5lib==1.0.1 >> setuplog.txt
python -m pip install hypothesis==5.5.4 >> setuplog.txt
python -m pip install idna==2.8 >> setuplog.txt
python -m pip install imageio==2.6.1 >> setuplog.txt
python -m pip install imagesize==1.2.0 >> setuplog.txt
python -m pip install importlib-metadata==1.5.0 >> setuplog.txt
python -m pip install intervaltree==3.0.2 >> setuplog.txt
python -m pip install ipykernel==5.1.4 >> setuplog.txt
python -m pip install ipython==7.12.0 >> setuplog.txt
python -m pip install ipython-genutils==0.2.0 >> setuplog.txt
python -m pip install ipywidgets==7.5.1 >> setuplog.txt
python -m pip install isort==4.3.21 >> setuplog.txt
python -m pip install itsdangerous==1.1.0 >> setuplog.txt
python -m pip install jdcal==1.4.1 >> setuplog.txt
python -m pip install jedi==0.14.1 >> setuplog.txt
python -m pip install Jinja2==2.11.1 >> setuplog.txt
python -m pip install joblib==0.14.1 >> setuplog.txt
python -m pip install json5==0.9.1 >> setuplog.txt
python -m pip install jsonschema==3.2.0 >> setuplog.txt
python -m pip install jupyter==1.0.0 >> setuplog.txt
python -m pip install jupyter-client==5.3.4 >> setuplog.txt
python -m pip install jupyter-console==6.1.0 >> setuplog.txt
python -m pip install jupyter-core==4.6.1 >> setuplog.txt
python -m pip install jupyterlab==1.2.6 >> setuplog.txt
python -m pip install jupyterlab-server==1.0.6 >> setuplog.txt
python -m pip install keyring==21.1.0 >> setuplog.txt
python -m pip install kiwisolver==1.1.0 >> setuplog.txt
python -m pip install lazy-object-proxy==1.4.3 >> setuplog.txt
python -m pip install libarchive-c==2.8 >> setuplog.txt
python -m pip install lief==0.9.0 >> setuplog.txt
python -m pip install llvmlite==0.31.0 >> setuplog.txt
python -m pip install locket==0.2.0 >> setuplog.txt
python -m pip install lxml==4.5.0 >> setuplog.txt
python -m pip install MarkupSafe==1.1.1 >> setuplog.txt
python -m pip install matplotlib==3.1.3 >> setuplog.txt
python -m pip install mccabe==0.6.1 >> setuplog.txt
python -m pip install mistune==0.8.4 >> setuplog.txt
python -m pip install mkl-fft==1.0.15 >> setuplog.txt
python -m pip install mkl-random==1.1.0 >> setuplog.txt
python -m pip install mkl-service==2.3.0 >> setuplog.txt
python -m pip install mock==4.0.1 >> setuplog.txt
python -m pip install more-itertools==8.2.0 >> setuplog.txt
python -m pip install mpmath==1.1.0 >> setuplog.txt
python -m pip install msgpack==0.6.1 >> setuplog.txt
python -m pip install multipledispatch==0.6.0 >> setuplog.txt
python -m pip install navigator-updater==0.2.1 >> setuplog.txt
python -m pip install nbconvert==5.6.1 >> setuplog.txt
python -m pip install nbformat==5.0.4 >> setuplog.txt
python -m pip install networkx==2.4 >> setuplog.txt
python -m pip install nltk==3.4.5 >> setuplog.txt
python -m pip install nose==1.3.7 >> setuplog.txt
python -m pip install notebook==6.0.3 >> setuplog.txt
python -m pip install numba==0.48.0 >> setuplog.txt
python -m pip install numexpr==2.7.1 >> setuplog.txt
python -m pip install numpy==1.18.1 >> setuplog.txt
python -m pip install numpydoc==0.9.2 >> setuplog.txt
python -m pip install olefile==0.46 >> setuplog.txt
python -m pip install openpyxl==3.0.3 >> setuplog.txt
python -m pip install packaging==20.1 >> setuplog.txt
python -m pip install pandas==1.1.5 >> setuplog.txt
python -m pip install pandocfilters==1.4.2 >> setuplog.txt
python -m pip install parso==0.5.2 >> setuplog.txt
python -m pip install partd==1.1.0 >> setuplog.txt
python -m pip install path==13.1.0 >> setuplog.txt
python -m pip install pathlib2==2.3.5 >> setuplog.txt
python -m pip install pathtools==0.1.2 >> setuplog.txt
python -m pip install patsy==0.5.1 >> setuplog.txt
python -m pip install pep8==1.7.1 >> setuplog.txt
python -m pip install pexpect==4.8.0 >> setuplog.txt
python -m pip install pickleshare==0.7.5 >> setuplog.txt
python -m pip install Pillow==7.0.0 >> setuplog.txt
python -m pip install pip==20.0.2 >> setuplog.txt
python -m pip install pkginfo==1.5.0.1 >> setuplog.txt
python -m pip install plotly==4.8.2 >> setuplog.txt
python -m pip install pluggy==0.13.1 >> setuplog.txt
python -m pip install ply==3.11 >> setuplog.txt
python -m pip install prometheus-client==0.7.1 >> setuplog.txt
python -m pip install prompt-toolkit==3.0.3 >> setuplog.txt
python -m pip install psutil==5.6.7 >> setuplog.txt
python -m pip install ptyprocess==0.6.0 >> setuplog.txt
python -m pip install py==1.8.1 >> setuplog.txt
python -m pip install pycodestyle==2.5.0 >> setuplog.txt
python -m pip install pycosat==0.6.3 >> setuplog.txt
python -m pip install pycparser==2.19 >> setuplog.txt
python -m pip install pycrypto==2.6.1 >> setuplog.txt
python -m pip install pycurl==7.43.0.5 >> setuplog.txt
python -m pip install pydocstyle==4.0.1 >> setuplog.txt
python -m pip install pyflakes==2.1.1 >> setuplog.txt
python -m pip install Pygments==2.5.2 >> setuplog.txt
python -m pip install pylint==2.4.4 >> setuplog.txt
python -m pip install pyodbc==4.0.0-unsupported >> setuplog.txt
python -m pip install pyOpenSSL==19.1.0 >> setuplog.txt
python -m pip install pyparsing==2.4.6 >> setuplog.txt
python -m pip install pyrsistent==0.15.7 >> setuplog.txt
python -m pip install PySocks==1.7.1 >> setuplog.txt
python -m pip install pytest==5.3.5 >> setuplog.txt
python -m pip install pytest-arraydiff==0.3 >> setuplog.txt
python -m pip install pytest-astropy==0.8.0 >> setuplog.txt
python -m pip install pytest-astropy-header==0.1.2 >> setuplog.txt
python -m pip install pytest-doctestplus==0.5.0 >> setuplog.txt
python -m pip install pytest-openfiles==0.4.0 >> setuplog.txt
python -m pip install pytest-remotedata==0.3.2 >> setuplog.txt
python -m pip install python-dateutil==2.8.1 >> setuplog.txt
python -m pip install python-jsonrpc-server==0.3.4 >> setuplog.txt
python -m pip install python-language-server==0.31.7 >> setuplog.txt
python -m pip install pytz==2019.3 >> setuplog.txt
python -m pip install PyWavelets==1.1.1 >> setuplog.txt
python -m pip install PyYAML==5.3 >> setuplog.txt
python -m pip install pyzmq==18.1.1 >> setuplog.txt
python -m pip install QDarkStyle==2.8 >> setuplog.txt
python -m pip install QtAwesome==0.6.1 >> setuplog.txt
python -m pip install qtconsole==4.6.0 >> setuplog.txt
python -m pip install QtPy==1.9.0 >> setuplog.txt
python -m pip install requests==2.22.0 >> setuplog.txt
python -m pip install retrying==1.3.3 >> setuplog.txt
python -m pip install rope==0.16.0 >> setuplog.txt
python -m pip install Rtree==0.9.3 >> setuplog.txt
python -m pip install ruamel-yaml==0.15.87 >> setuplog.txt
python -m pip install scikit-image==0.16.2 >> setuplog.txt
python -m pip install scikit-learn==0.22.1 >> setuplog.txt
python -m pip install scipy==1.4.1 >> setuplog.txt
python -m pip install seaborn==0.10.0 >> setuplog.txt
python -m pip install Send2Trash==1.5.0 >> setuplog.txt
python -m pip install setuptools==46.0.0. >> setuplog.txt
python -m pip install simplegeneric==0.8.1 >> setuplog.txt
python -m pip install singledispatch==3.4.0.3 >> setuplog.txt
python -m pip install six==1.14.0 >> setuplog.txt
python -m pip install snowballstemmer==2.0.0 >> setuplog.txt
python -m pip install sortedcollections==1.1.2 >> setuplog.txt
python -m pip install sortedcontainers==2.1.0 >> setuplog.txt
python -m pip install soupsieve==1.9.5 >> setuplog.txt
python -m pip install Sphinx==2.4.0 >> setuplog.txt
python -m pip install sphinxcontrib-applehelp==1.0.1 >> setuplog.txt
python -m pip install sphinxcontrib-devhelp==1.0.1 >> setuplog.txt
python -m pip install sphinxcontrib-htmlhelp==1.0.2 >> setuplog.txt
python -m pip install sphinxcontrib-jsmath==1.0.1 >> setuplog.txt
python -m pip install sphinxcontrib-qthelp==1.0.2 >> setuplog.txt
python -m pip install sphinxcontrib-serializinghtml==1.1.3 >> setuplog.txt
python -m pip install sphinxcontrib-websupport==1.2.0 >> setuplog.txt
python -m pip install spyder==4.0.1 >> setuplog.txt
python -m pip install spyder-kernels==1.8.1 >> setuplog.txt
python -m pip install SQLAlchemy==1.3.13 >> setuplog.txt
python -m pip install statsmodels==0.11.0 >> setuplog.txt
python -m pip install sympy==1.5.1 >> setuplog.txt
python -m pip install tables==3.6.1 >> setuplog.txt
python -m pip install tblib==1.6.0 >> setuplog.txt
python -m pip install terminado==0.8.3 >> setuplog.txt
python -m pip install testpath==0.4.4 >> setuplog.txt
python -m pip install toolz==0.10.0 >> setuplog.txt
python -m pip install tornado==6.0.3 >> setuplog.txt
python -m pip install tqdm==4.42.1 >> setuplog.txt
python -m pip install traitlets==4.3.3 >> setuplog.txt
python -m pip install ujson==1.35 >> setuplog.txt
python -m pip install unicodecsv==0.14.1 >> setuplog.txt
python -m pip install urllib3==1.25.8 >> setuplog.txt
python -m pip install vroom==1.0.2 >> setuplog.txt
python -m pip install watchdog==0.10.2 >> setuplog.txt
python -m pip install wcwidth==0.1.8 >> setuplog.txt
python -m pip install webencodings==0.5.1 >> setuplog.txt
python -m pip install Werkzeug==1.0.0 >> setuplog.txt
python -m pip install wheel==0.34.2 >> setuplog.txt
python -m pip install widgetsnbextension==3.5.1 >> setuplog.txt
python -m pip install wrapt==1.11.2 >> setuplog.txt
python -m pip install wurlitzer==2.0.0 >> setuplog.txt
python -m pip install xlrd==1.2.0 >> setuplog.txt
python -m pip install XlsxWriter==1.2.7 >> setuplog.txt
python -m pip install xlwings==0.17.1 >> setuplog.txt
python -m pip install xlwt==1.3.0 >> setuplog.txt
python -m pip install xmltodict==0.12.0 >> setuplog.txt
python -m pip install yapf==0.28.0 >> setuplog.txt
python -m pip install zict==1.0.0 >> setuplog.txt
python -m pip install zipp==2.2.0 >> setuplog.txt

# enum34 causes problems so it gets to sit in time-out... FOREVER! >:D
echo 'y' | python -m pip uninstall enum34 >> setuplog.txt

exit
