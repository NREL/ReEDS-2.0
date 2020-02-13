#!/bin/python

# -------------------------------------------------------------------------------
# name:        runmodel.py
# purpose:     to handle input and output from GAMS models
#
# author:      maxwell brown (maxwell.l.brown@gmail.com), sam koebrich (sam.koebrich@NREL.gov), elainethale
#
# copyright:    free to share
# -----------------------------------------------------------------------------
# To run this script, adjust the environment to the current PC in
# setupEnvironment(), source the file, then run main() -- instructions to
# generalize this script to other models are below
#

import os
import re
import sys
from datetime import datetime
import queue
import threading
import time
import shutil
import csv
import zipfile
import operator
import time
import multiprocessing
import argparse
import platform
import subprocess

import pandas as pd
from random import randrange
from distutils.dir_util import copy_tree
from builtins import input

from tempfile import mkstemp
from shutil import move
from os import remove, close

if platform.system() in ['Darwin','Linux']:
	FILE_EXTENSION = '.sh'
elif platform.system() in ['Windows']:
	FILE_EXTENSION = '.bat'

class GamsDirFinder(object):
	"""
	Class for finding and accessing the system's GAMS directory. 
	The find function first looks for the 'GAMS_DIR' environment variable. If 
	that is unsuccessful, it next uses 'which gams' for POSIX systems, and the 
	default install location, 'C:/GAMS', for Windows systems. In the latter case
	it prefers the largest version number.
	
	You can always specify the GAMS directory directly, and this class will attempt 
	to clean up your input. (Even on Windows, the GAMS path must use '/' rather than 
	'\'.)
	"""
	gams_dir_cache = None

	def __init__(self,gams_dir=None):
		self.gams_dir = gams_dir
		
	@property
	def gams_dir(self):
		"""The GAMS directory on this system."""
		if self.__gams_dir is None:
			raise RuntimeError("Unable to locate your GAMS directory.")
		return self.__gams_dir
		
	@gams_dir.setter
	def gams_dir(self, value):
		self.__gams_dir = None
		if isinstance(value, str):
			self.__gams_dir = self.__clean_gams_dir(value)
		if self.__gams_dir is None:
			self.__gams_dir = self.__find_gams()
			
	def __clean_gams_dir(self,value):
		"""
		Cleans up the path string.
		"""
		assert(isinstance(value, str))
		ret = os.path.realpath(value)
		if not os.path.exists(ret):
			return None
		ret = re.sub('\\\\','/',ret)
		return ret
		
	def __find_gams(self):
		"""
		For all systems, the first place we examine is the GAMS_DIR environment
		variable.
		For Windows, the next step is to look for the GAMS directory based on 
		the default install location (C:/GAMS).
		
		For all others, the next step is 'which gams'.
		
		Returns
		-------
		str or None
			If not None, the return value is the found gams_dir
		"""
		# check for environment variable
		ret = os.environ.get('GAMS_DIR')
		
		if ret is None:
			if os.name == 'nt':
				# windows systems
				# search in default installation location
				cur_dir = r'C:\GAMS'
				if os.path.exists(cur_dir):
					# level 1 - prefer win64 to win32
					for p, dirs, files in os.walk(cur_dir):
						if 'win64' in dirs:
							cur_dir = os.path.join(cur_dir, 'win64')
						elif len(dirs) > 0:
							cur_dir = os.path.join(cur_dir, dirs[0])
						else:
							return ret
						break
				if os.path.exists(cur_dir):
					# level 2 - prefer biggest number (most recent version)
					for p, dirs, files in os.walk(cur_dir):
						if len(dirs) > 1:
							try:
								versions = [float(x) for x in dirs]
								ret = os.path.join(cur_dir, "{}".format(max(versions)))
							except:
								ret = os.path.join(cur_dir, dirs[0])
						elif len(dirs) > 0:
							ret = os.path.join(cur_dir, dirs[0])
						break
			else:
				# posix systems
				try:
					ret = os.path.dirname(subprocess.check_output(['which', 'gams'])).decode()
				except:
					ret = None
				
		if ret is not None:
			ret = self.__clean_gams_dir(ret)
			GamsDirFinder.gams_dir_cache = ret

		if ret is None:
			print("Did not find GAMS directory. Using cached value {}.".format(self.gams_dir_cache))
			ret = GamsDirFinder.gams_dir_cache
			
		return ret
	
def clean_file_paths(path):
	return path.replace('\\', os.sep).replace('/', os.sep)

def get_formatted_time():
	formatted_time = time.strftime('%Y%m%d_%H%M%S')
	return formatted_time

def setupEnvironment():

	# --- Should be ReEDS-2.0/ ---
	INPUTDir = os.getcwd()

	# --- load in df of cases ---
	case_df = pd.read_csv(os.path.join(INPUTDir, 'A_Inputs','cases.csv'))
	case_df = case_df.set_index('case',drop=True)
	all_cases = list(case_df.columns)[2:] #exclude description and default
	
	print("Specify the name of the run(s)")
	runname = str(input('Run Name (default is a timestamp): ') or 'india_{}'.format(get_formatted_time()))
	print(" ")

	# --- User Input of Scenarios ---
	print(" ")
	print("Please select which scenarios you would like to run")
	print("Enter each selected number seperated by a comma (i.e. 1, 3)")
	print("-----------------------------------------------------------")

	case_number_lookup = {}
	for i, s in enumerate(all_cases):
		print("{} -- {}".format(i, s))
		case_number_lookup[i] = s
	last = i + 1

	print("{} -- RUN ALL".format(last))
	scenarios = str(input('Selected scenarios (default {}): '.format(last)) or last)
	selected = [int(i) for i in scenarios.replace(" ","").split(",")]

	#filter out non selected cases if RUN ALL isn't selected
	if last in selected:
		to_run = all_cases
	else:
		to_run = [case_number_lookup[c] for c in selected]

	# --- User Input of Capacity Value and Curtailment ---
	gams_locator = GamsDirFinder()
	GAMSDir = str(gams_locator.gams_dir)
	cc_curtchoice = int(input('Do you want to iteritively calculate capacity value and curtailment? (0=no / 1=yes, default 1): ') or 1)
	GAMSDir_input = str(input('Where is the path to the GAMS executable? (default {}): '.format(GAMSDir)))
	if GAMSDir_input != '': #user input will be '' if nothing was entered.
		GAMSDir = GAMSDir_input
	comp = int(input('Compile inputs and model equations? (0=no / 1=yes, default 1): ') or 1)
	run = int(input('Run model? (0=no / 1=yes, default 1): ') or 1)
	rmdchoice = int(input('Generate R Markdown for visualization after scenario run? (0=no / 1=yes, default 1): ') or 1)

	if run == 0:
		hpcchoice = int(input('Generate shell scripts to run on NREL HPC (SLURM)? (0=no / 1=yes, default 0):') or 0)
	else:
		hpcchoice = 0

	# --- Determine which cases are being run ---
	case_df = case_df[['Description','Default Value'] + to_run]

	# --- Initiate the empty lists which will be filled with info from cases ---
	caseList = []
	caseSwitches = [] #list of dicts, one dict for each case

	for c in to_run:
		#Fill any missing switches with the defaults in cases.csv
		case_df[c] = case_df[c].fillna(case_df['Default Value'])
		
		#Clean entered file paths
		path_entries = ['yearset','HourlyStaticFile','FuelLimit_file','TechCost_file','MinLoad_file','Hours_file','Load_file','PeakDemRegion_file']
		for r in path_entries:
			case_df.loc[r, c] = clean_file_paths(case_df.loc[r, c])

		shcom = ' --case=' + runname + "_" + c
		for i,v in case_df[c].iteritems():
			shcom = shcom + ' --' + i + '=' + v
		caseList.append(shcom)
		caseSwitches.append(case_df[c].to_dict())
	
	case_df.drop(['Description','Default Value'], axis='columns',inplace=True)
	timetypeset = case_df.loc['timetype'].tolist()
	yearset = case_df.loc['yearset'].tolist()
	endyearset = case_df.loc['endyear'].tolist()
	hourlystaticfileset = case_df.loc['HourlyStaticFile'].tolist()
	niterset = case_df.loc['CC/Curtailment Iterations'].tolist()


	# --- Intialize envdict, which holds flags written in a batch script eventually ---
	envdict =  {'WORKERS': 1,
				'startiter': 0,
				'hpcchoice' : hpcchoice,
				'casenames': to_run,
				'runname': runname,
				'GAMSDir': GAMSDir,
				'INPUTDir' : INPUTDir,
				'cc_curtchoice' : cc_curtchoice,
				'rmdchoice' : rmdchoice,
				'comp' : comp,
				'run' : run,
				'timetypeset' : timetypeset,
				'yearfileset' : yearset,
				'endyearset' : endyearset,
				'hourlystaticfileset' : hourlystaticfileset,
				'niterset' : niterset,
				'caseList' : caseList,
				'caseSwitches': caseSwitches,
				}
				
	return envdict

#%%
def createmodelthreads(envVar):
	"""Create threads that are used for multiprocessing the *creation* of agent files, 
	does not actually impact multiprocessing of ReEDS."""

	q = queue.Queue()
	num_worker_threads = envVar['WORKERS']
	
	def worker():
		while True:
			ThreadInit = q.get()
			if ThreadInit is None:
				break
			runModel(ThreadInit['caseindex'],
					 ThreadInit['scen'],
					 ThreadInit['caseSwitches'],
					 ThreadInit['lstfile'],
					 ThreadInit['niter'],
					 ThreadInit['timetype'],
					 ThreadInit['yearfile'],
					 ThreadInit['INPUTDir'],
					 ThreadInit['endyear'],
					 ThreadInit['ccworkers'],
					 ThreadInit['startiter'],
					 ThreadInit['hourlystaticfile'],
					 ThreadInit['cc_curtchoice'],
					 ThreadInit['GAMSDir'],
					 ThreadInit['hpcchoice']
					 )
			q.task_done()

	threads = []
	for i in range(num_worker_threads):
		t = threading.Thread(target=worker)
		t.start()
		threads.append(t)

	for i in range(len(envVar['caseList'])):
		q.put({'caseindex': i,
			   'scen': envVar['caseList'][i],
			   'caseSwitches': envVar['caseSwitches'][i],
			   'lstfile':envVar['runname']+'_'+envVar['casenames'][i],
			   'niter':envVar['niterset'][i],
			   'timetype':envVar['timetypeset'][i],
			   'yearfile':envVar['yearfileset'][i],
			   'INPUTDir':envVar['INPUTDir'],
			   'endyear':envVar['endyearset'][i],
			   'ccworkers':envVar['WORKERS'],
			   'startiter':envVar['startiter'],
			   'hourlystaticfile':envVar['hourlystaticfileset'][i],
			   'cc_curtchoice':envVar['cc_curtchoice'],
			   'GAMSDir':envVar['GAMSDir'],
			   'hpcchoice':envVar['hpcchoice']
			   })

	q.join() # block until all tasks are done

	for i in range(num_worker_threads): # stop workers
		q.put(None)

	for t in threads:
		t.join()


def runModel(caseindex,options,caseSwitches,lstfile,niter,timetype,yearfile,INPUTDir,
			 endyear,ccworkers,startiter,hourlystaticfile,
			 cc_curtchoice, GAMSDir, hpcchoice):
	
	if not os.path.exists(os.path.join("E_Outputs", "runs", lstfile)):
		os.mkdir(os.path.join("E_Outputs", "runs", lstfile))
	if not os.path.exists(os.path.join("E_Outputs", "runs", lstfile, "g00files")):
		os.mkdir(os.path.join("E_Outputs", "runs", lstfile, "g00files"))
	if not os.path.exists(os.path.join("E_Outputs", "runs", lstfile, "lstfiles")):
		os.mkdir(os.path.join("E_Outputs", "runs", lstfile, "lstfiles"))
	if not os.path.exists(os.path.join("E_Outputs", "runs", lstfile, "outputs")):
		os.mkdir(os.path.join("E_Outputs", "runs", lstfile, "outputs"))
	if not os.path.exists(os.path.join("E_Outputs", "runs", lstfile, "outputs", "variabilityFiles")):
		os.mkdir(os.path.join("E_Outputs", "runs", lstfile, "outputs", "variabilityFiles"))
	
	# --- Clean paths entered in cases.csv ---
	yearfile = yearfile.replace('\\', os.sep).replace('/', os.sep)
	hourlystaticfile = hourlystaticfile.replace('\\', os.sep).replace('/', os.sep)

	OutputDir = os.path.join(INPUTDir, "E_Outputs", "runs", lstfile)
	solveyears= list(csv.reader(open(os.path.join(INPUTDir,yearfile), 'r'), delimiter=","))[0]
	solveyears = [y for y in solveyears if y <= endyear]
	toLogGamsString =  ' logOption=4 logFile=' + str(os.path.join("E_Outputs", "runs", lstfile, 'gamslog.txt')) + ' ' + 'appendLog=1 '
		
	with open(os.path.join(OutputDir, 'compile_' + lstfile + FILE_EXTENSION), 'w') as OPATH:
		OPATH.write("gams " + str(os.path.join("A_Inputs", "a_inputs.gms")) +\
					" s=" + str(os.path.join("E_Outputs","runs",lstfile,"g00files","data_india")) +\
					" o=" + str(os.path.join("E_Outputs","runs",lstfile,"lstfiles","inputs.lst")) +\
					" --TotIter=" + str(niter) +' --hourlystaticfile=' + str(hourlystaticfile) + toLogGamsString + options + ' \n')
		OPATH.write("gams " + str(os.path.join("B_Equations","b1_model_constraints.gms")) +\
					" o=" + str(os.path.join("E_Outputs","runs",lstfile,"lstfiles","Supply_Model.lst")) +\
					" r=" + str(os.path.join("E_Outputs","runs",lstfile,"g00files","data_india")) + " s=" +\
					str(os.path.join("E_Outputs","runs",lstfile,"g00files","supmod")) + ' \n')
		OPATH.write("gams " + str(os.path.join("B_Equations","b2_objective_function.gms")) +\
					" o=" + str(os.path.join("E_Outputs","runs",lstfile,"lstfiles","Supply_Objective.lst")) +\
					" r=" + str(os.path.join("E_Outputs","runs",lstfile,"g00files","supmod")) +\
					" s=" + str(os.path.join("E_Outputs","runs",lstfile,"g00files","supply_objective" + ' \n')))

	#############################
	# -- sequential setup -- 
	#############################
	if timetype=='seq':
		raise NotImplementedError("This branch is currently only implemented to work with intertemporal solve!")
	
	#############################
	# -- window setup -- 
	#############################
	if timetype=='win':
		raise NotImplementedError("This branch is currently only implemented to work with intertemporal solve!")

	#############################
	# -- intertemporal setup -- 
	#############################
	if timetype=='int':
		begyear = min(solveyears)
		with open(os.path.join(OutputDir, 'run_' + lstfile + FILE_EXTENSION), 'w') as OPATH:
			savefile = lstfile
			if startiter == 0:
				OPATH.writelines("gams " + str(os.path.join("C_Solve","c1_Solveprep.gms")) + " r=" +\
								 str(os.path.join("E_Outputs","runs",lstfile,"g00files","supply_objective")) +\
								 " s=" + str(os.path.join("E_Outputs","runs",lstfile,"g00files",savefile)) +\
								 " o=" + str(os.path.join("E_Outputs","runs",lstfile,"lstfiles", lstfile +".lst")) +\
								 ' --hourlystaticfile='+str(hourlystaticfile) + toLogGamsString + options + ' \n')
				restartfile=savefile
			if startiter > 0:
				restartfile = lstfile+"_"+startiter
	
			#for the number of iterations we have...
			niter = int(niter)
			startiter = int(startiter)
			for i in range(startiter,niter):
				#call the intertemporal solve
				savefile = lstfile+"_"+str(i)
				OPATH.writelines("gams " + str(os.path.join("C_Solve","c2_Solve_Int.gms")) +\
								 " o=" + str(os.path.join("E_Outputs","runs",lstfile,"lstfiles", lstfile + "_" + str(i) + ".lst")) +\
								 " r=" + str(os.path.join("E_Outputs","runs",lstfile,"g00files",restartfile)) + " s=" +\
								 str(os.path.join("E_Outputs","runs",lstfile,"g00files",savefile)) + toLogGamsString +\
								 " --niter=" + str(i) + " --case=" + lstfile  + ' \n')
				
				#start threads for cc/curt
				#no need to run cc curt scripts for final iteration
				if i < niter:
					if cc_curtchoice == 1:
						OPATH.writelines("python " + str(os.path.join("D_8760","d1_8760batch.py")) + " " + lstfile + " " + str(ccworkers) +\
										 " " + yearfile + " " + savefile + " " + str(begyear) + " " + str(endyear)  + " " + hourlystaticfile + " " + ' \n')
					   
						#merge all the resulting r2_in gdx files
						#the output file will be for the next iteration
						nextiter = i+1
						curt_gdxmergedfile = str(os.path.join("E_Outputs","runs",lstfile,"outputs","variabilityFiles","mergedcurt_" + lstfile + "_" + str(nextiter)))            
						cc_gdxmergedfile = str(os.path.join("E_Outputs","runs",lstfile,"outputs","variabilityFiles","mergedcc_" + lstfile + "_" + str(nextiter)))
						OPATH.writelines("gdxmerge " + str(os.path.join("E_Outputs","runs",lstfile,"outputs","variabilityFiles","cc_out_"+lstfile+"*")) +\
										 " output=" + cc_gdxmergedfile + " \n")
						OPATH.writelines("gdxmerge " + str(os.path.join("E_Outputs","runs",lstfile,"outputs","variabilityFiles","curt_out_"+lstfile+"*")) +\
										 " output=" + curt_gdxmergedfile  + ' \n')
							
						#do necessary conversions to make the merged gdx file readable into GAMS 
						OPATH.writelines("Rscript " + str(os.path.join(INPUTDir,"D_8760","d8_Merge_8760.R")) + " " + INPUTDir + " " + GAMSDir + " " +\
										  curt_gdxmergedfile + " " + cc_gdxmergedfile + ' \n')
				restartfile=savefile
	
			if caseSwitches['GSw_ValStr'] != '0':
				OPATH.writelines('gams ' + str(os.path.join("F_Analysis","valuestreams","valuestreams.gms")) + " o=" +\
					 str(os.path.join("E_Outputs","runs",lstfile,"lstfiles","valuestreams_" + lstfile + ".lst")) +\
					 " r=" + str(os.path.join("E_Outputs","runs",lstfile,"g00files",restartfile)) + toLogGamsString +\
					 ' --case=' + lstfile + '\n')

			OPATH.writelines("gams " + str(os.path.join("E_Outputs","e1_create_report.gms")) + " o=" + str(os.path.join("E_Outputs","runs",lstfile,"lstfiles","e1_create_report_" + lstfile + ".lst")) +\
							 " r=" + str(os.path.join("E_Outputs","runs",lstfile,"g00files",restartfile)) + toLogGamsString + " --fname=" + lstfile + ' \n')
					   
		OPATH.close()

		if hpcchoice == 1:
			shutil.copy(os.path.join("shfiles","srun_template.sh"),os.path.join("shfiles",lstfile+".sh"))
			with open(os.path.join("shfiles", lstfile + '.sh'), 'a') as OPATH:
				 OPATH.writelines("\n#SBATCH --job-name=" + lstfile + "\n\n")
				 OPATH.writelines("sh " + os.path.join(OutputDir, 'run_' + lstfile + FILE_EXTENSION))
			OPATH.close()

		print('done writing files')

def checkLDCpkl(filedst,filename,filesrc=os.path.join('nrelqnap02','ReEDS','8760_Method_Inputs')):
	"""Copy 8760 files from NREL QNAP server to local folders.
	   For India, this should never run."""
	
	if not os.path.exists(os.path.join(filedst, filename)):
		print('WARNING! ReEDS India should never be here, the necessary pickle files should already be in the git repo.')
		print("Copying file: " + filename)
		print("From: " + filesrc)
		print("To: " + filedst)
		print(" ")
		shutil.copy(os.path.join(filesrc, filename), os.path.join(filedst, filename))     


def main():
	""" Executes parallel solves based on cases in 'cases.csv' """

	print(" ")
	print(" ")
	print("--------------------------------------------------------------------------------------------------")
	print(" ")
	print("         MMM.  808   MMM;   BMW       rMM   @MMMMMMMM2     XM@MMMMMMMMMS   MM0         ")
	print("        iMMM@S,MMM;X@MMMZ   MMMM.     aMM   MMMW@MMMMMMM   BMMMW@M@M@MMX   MMM         ")
	print("         r2MMZ     SMMa;i   MMMMM;    SMM   MMB      7MMS  ZMM.            MMM         ")
	print("           Z         Z      MMZ7MM2   XMM   MMW       MM8  ZMM.            MMM         ")
	print("        .MMr         .MM7   MM8 rMMB  XMM   MM@     ,MMM   ZMMMMMMMMMM     MMM         ")
	print("        .MMr         ,MMr   MMB  :MMM :MM   MMW  MMMMMB    ZMMMWMMMMM@     MMM         ")
	print("           Z         Z      MMW    MMMaMM   MM@   MMMi     ZMM.            MMM         ")
	print("         XaMM8     aMMZXi   MMW     MMMMM   MM@    0MMr    ZMM.            MMW         ")
	print("        iMMMW7,MMM;;BMMMZ   MMM      8MMM   MMM     aMMB   0MMMWMMM@MMMZ   MMM@MMMMMMM ")
	print("         BZ0   SSS   0Z0.   ZBX       :0B   8BS      :BM7  ;8Z8WWWWWW@M2   BZZ0WWWWWWM ")
	print(" ")
	print("--------------------------------------------------------------------------------------------------")
	print(" ")
	print(" ")
	print(" ")
 
 
	# --- Gather user inputs from CLI before calling GAMS programs ---
	envVar = setupEnvironment()

	# --- Check for Hourly Static File (i.e. /D_8760/LDCfiles/India_8760) ---
	filedst = os.path.join(os.getcwd(),"D_8760","LDCfiles")
	pklfiles = ["_load.pkl","_recf.pkl","_resources.pkl"]

	if 'India_8760_load.pkl' not in list(os.listdir(filedst)):
		# --- Stitch together state pickles into single (larger than githubs file limit) pickle ---
		print(" ")
		print('Stitching together state load pickles...')
		print(" ")
		state_load_dfs = []
		load_pickle_dir = os.path.join(filedst, 'state_load_pickles')
		for p in os.listdir(os.path.join(load_pickle_dir)):
			state_load_dfs.append(pd.read_pickle(os.path.join(load_pickle_dir,p)))
		India_8760_load = pd.concat(state_load_dfs, axis='columns')
		India_8760_load = India_8760_load.reset_index(drop=False)
		India_8760_load.to_pickle(os.path.join(filedst, 'India_8760_load.pkl'), protocol=4)

	for i in list(set(envVar['hourlystaticfileset'])): # i default is India_8760
		for j in pklfiles:
			checkLDCpkl(filedst = filedst, filename = i+j)
	checkLDCpkl(filedst, filename = "India_hour_season_ts_map.pkl")

	# --- Create runs directory ---
	if not os.path.exists(os.path.join("E_Outputs","runs")):
		os.mkdir(os.path.join("E_Outputs","runs"))
	
	# --- Create Threads for each Model ---
	createmodelthreads(envVar)
	
	# --- Interpret CLI flags to compile or run after batch scripts are created ---
	runnames = ['{}_{}'.format(envVar['runname'], i) for i in envVar['casenames']]
	for r in runnames:
		if envVar['comp'] == 1: #compile the model if indicated by user
			shell_script_path = os.path.join('E_Outputs','runs',r,'compile_{}{}'.format(r, FILE_EXTENSION))
			subprocess.call('chmod +x {}'.format(shell_script_path), shell=True)
			subprocess.call(shell_script_path, shell=True)
		if envVar['run'] == 1: #run the model if indicated by user
			shell_script_path = os.path.join('E_Outputs','runs',r,'run_{}{}'.format(r, FILE_EXTENSION))
			subprocess.call('chmod +x {}'.format(shell_script_path), shell=True)
			subprocess.call(shell_script_path, shell=True)

	if envVar['rmdchoice'] == 1:
		rmd_path = os.path.join("E_Outputs","gdxfiles","rmd{}".format(FILE_EXTENSION))

		gdxrmdstring = ''
		for c in envVar['casenames']:
			gdxrmdstring = gdxrmdstring + c + '#' + 'output_' + envVar['runname'] + '_' + c + '.gdx' + '##'
		gdxrmdstring = "'{}'".format(gdxrmdstring)
		gamsdirdd = "'{}'".format(envVar['GAMSDir']) #R needs the string wrapped in single quotes
		endyearmin = str(min([int(i) for i in envVar['endyearset']]))
		endyearmin = "'{}'".format(endyearmin)
		curt = envVar['cc_curtchoice']
		pandoc_path = str(os.path.join("Program Files","RStudio","bin","pandoc")).replace("\\","\\\\")
		rmd_render_path = str(os.path.join('F_Analysis','ReEDS-India-markdown.Rmd')).replace("\\","\\\\")

		with open(rmd_path, 'w') as OPATH:
			OPATH.writelines("""Rscript -e "Sys.setenv(RSTUDIO_PANDOC='{}')" -e "rmarkdown::render('{}', output_file='ReEDS-India-results_{}.html', params = list('gdxlist' = {}, 'gamsdir' = {}, 'final.year' = {}, 'curt.switch' = {}))" \n""".format(pandoc_path, rmd_render_path, get_formatted_time(),gdxrmdstring, gamsdirdd, endyearmin, curt))
			html_path = os.path.join('F_Analysis','ReEDS-India-results_{}.html'.format(get_formatted_time())).replace("\\","\\\\")
			OPATH.writelines("""start {} \n""".format(html_path))
		
		if envVar['run'] == 1: #only generate R markdown if model ran
			subprocess.call('chmod +x {}'.format(rmd_path), shell=True)
			subprocess.call(rmd_path, shell=True)
		
if __name__ == '__main__':
	# --- Wrapper to run from CLI ---
 
	try:
		main()
	except Exception as e:
		raise e
	
