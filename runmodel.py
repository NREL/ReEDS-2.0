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
#%%#
import os
import subprocess

if os.name == 'posix':
    os.environ['GAMS_DIR'] = os.path.dirname(subprocess.check_output(['which', 'gams'])).decode()

import re
import sys
from datetime import datetime
import queue
import threading
import time
import shutil
import csv
import traceback
import zipfile
import operator
import time
import multiprocessing
import argparse
import platform
from subprocess import Popen, PIPE, STDOUT
import glob

import pandas as pd
from random import randrange
from distutils.dir_util import copy_tree
from builtins import input

from tempfile import mkstemp
from shutil import move
from os import remove, close
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

if platform.system() in ['Darwin','Linux']:
	FILE_EXTENSION = '.sh'
elif platform.system() in ['Windows']:
	FILE_EXTENSION = '.bat'

import logging
logger_ = logging.getLogger(__name__)


#%%#
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
#%%	
def clean_file_paths(path):
	return path.replace('\\', os.sep).replace('/', os.sep)

def get_formatted_time():
	formatted_time = time.strftime('%Y%m%d_%H%M%S')
	return formatted_time
#%%
def setupEnvironment(ui_input=None):
	if ui_input is None:
		ui_input = {}

	# If input is coming at once
	# input = {'run_name': 'test', '}

	# --- Should be ReEDS-2.0/ ---
	INPUTDir = os.path.dirname(__file__) #os.getcwd()

	# --- load in df of cases ---

	# TDOD Update this from input
	if 'case_csv' in ui_input:
		case_df = pd.read_csv(ui_input['case_csv'])
	else:
		case_df = pd.read_csv(os.path.join(INPUTDir, 'A_Inputs','cases.csv'))

	case_df = case_df.set_index('case',drop=True)
	all_cases = list(case_df.columns)[2:] #exclude description and default
	
	if "run_name" not in ui_input:
		print("Specify the name of the run(s)")
		runname = str(input('Run Name (default is a timestamp): ') or 'india_{}'.format(get_formatted_time()))
		print(" ")
	else:
		runname = ui_input['run_name']


	if "scenarios" not in ui_input:
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
	else:
		to_run = ui_input['scenarios']

	# --- User Input of Capacity Value and Curtailment ---
	gams_locator = GamsDirFinder()
	GAMSDir = str(gams_locator.gams_dir)

	if 'settings' not in ui_input:
		cc_curtchoice = int(input('Do you want to iteritively calculate capacity value and curtailment? (0=no / 1=yes, default 1): ') or 1)
		# GAMSDir_input = str(input('Where is the path to the GAMS executable? (default {}): '.format(GAMSDir)))
		GAMSDir_input = ''
		if GAMSDir_input != '': #user input will be '' if nothing was entered.
			GAMSDir = GAMSDir_input
		comp = int(input('Compile inputs and model equations? (0=no / 1=yes, default 1): ') or 1)
		run = int(input('Run model? (0=no / 1=yes, default 1): ') or 1)
	
		if run == 0:
			hpcchoice = int(input('Generate shell scripts to run on NREL HPC (SLURM)? (0=no / 1=yes, default 1):') or 1)
		else:
			hpcchoice = 0
	else:
		cc_curtchoice = int(ui_input['settings']['iterative'])
		comp = int(ui_input['settings']['compile'])
		run = int(ui_input['settings']['run_model'])
		hpcchoice = 0


	# --- Determine which cases are being run ---
	case_df = case_df[['Description','Default Value'] + to_run]

	# --- Initiate the empty lists which will be filled with info from cases ---
	caseList = []
	caseSwitches = [] #list of dicts, one dict for each case

	for c in to_run:
		#Fill any missing switches with the defaults in cases.csv
		case_df[c] = case_df[c].fillna(case_df['Default Value'])

		#Update switches based on input
		if case_df.loc['GSw_Retire', c] == '0':
			case_df.loc['GSw_TechPhaseOut', c] = '0'
		
		#Clean entered file paths
		path_entries = ['yearset','HourlyLoadFile', 'PRMregion_file', 'PRMstate_file', 'FuelLimit_file','FuelPrice_file','TechCost_file','MinLoad_file','Hours_file','Load_file','PeakDemRegion_file', 'PeakDemState_file', 'IVT_file', 'RECapMandate_file', 'RECapFracMandate_file', 'RECapManTech_file', 'REGenMandate_file', 'REGenManTech_file', 'Trancap_file','InterTrancost_file', 'AbsGrowLim_file', 'SouthAsiaImport_file', 'BinnedCapacity_file', 'CapNepalStorage_file', 'CapMult_file', 'CapNonRsc_file', 'CapHydro_file', 'CfAdjHydro_file', 'CfNepalHydro_file', 'CfOut_file', 'PrescribedNonRsc_file', 'PrescribedRsc_file', 'RscDat_file', 'TransportCharge_file', 'VomInit_file', 'HydMinLoad_file', 'BAset_file', 'FocusRegionSet_file', 'HierarchySet_file', 'RrsMap_file', 'RsSet_file', 'StateRMap_file', 'StateRsMap_file', 'CoordX_file', 'CoordY_file', 'FutureTranCapSet_file', 'RegionRRegionSet_file', 'TranCost_file', 'MaxAge_file']
		for r in path_entries:
			case_df.loc[r, c] = clean_file_paths(case_df.loc[r, c])

		shcom = ' --case=' + runname + "_" + c
		for i,v in case_df[c].iteritems():
			shcom = shcom + ' --' + str(i) + '=' + str(v)
		caseList.append(shcom)
		caseSwitches.append(case_df[c].to_dict())

	case_df.drop(['Description','Default Value'], axis='columns',inplace=True)
	timetypeset = case_df.loc['timetype'].tolist()
	yearset = case_df.loc['yearset'].tolist()
	endyearset = case_df.loc['endyear'].tolist()
	ccworkers = min(list(map(int, case_df.loc['augur_workers'])))
	hourlyloadfileset = case_df.loc['HourlyLoadFile'].tolist()
	niterset = case_df.loc['CC/Curtailment Iterations'].tolist()
	
	# --- Intialize envdict, which holds flags written in a batch script eventually ---
	envdict =  {'WORKERS': ccworkers,
				'startiter': 0,
				'hpcchoice' : hpcchoice,
				'casenames': to_run,
				'runname': runname,
				'GAMSDir': GAMSDir,
				'INPUTDir' : INPUTDir,
				'cc_curtchoice' : cc_curtchoice,
				'comp' : comp,
				'run' : run,
				'timetypeset' : timetypeset,
				'yearfileset' : yearset,
				'endyearset' : endyearset,
				'hourlyloadfileset' : hourlyloadfileset,
				'niterset' : niterset,
				'caseList' : caseList,
				'caseSwitches': caseSwitches
				}

	if 'output_folder_path' in ui_input:
		envdict['output_folder_path'] = ui_input['output_folder_path']
				
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
					 ThreadInit['hourlyloadfile'],
					 ThreadInit['cc_curtchoice'],
					 ThreadInit['GAMSDir'],
					 ThreadInit['hpcchoice'],
					 ThreadInit['output_folder_path'],
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
			   'hourlyloadfile':envVar['hourlyloadfileset'][i],
			   'cc_curtchoice':envVar['cc_curtchoice'],
			   'GAMSDir':envVar['GAMSDir'],
			   'hpcchoice':envVar['hpcchoice'],
			   'output_folder_path': envVar.get('output_folder_path', '')
			   })

	q.join() # block until all tasks are done

	for i in range(num_worker_threads): # stop workers
		q.put(None)

	for t in threads:
		t.join()

def makeOptFile(optFileNum, caseIndex, case_name):
    #Get original optfile
    if int(optFileNum) == 1:
        origOptExt = 'opt'
    elif int(optFileNum) < 10:
        origOptExt = 'op' + optFileNum
    else:
        origOptExt = 'o' + optFileNum
    #Create number in 900s for modified opt file and add to options
    if caseIndex < 10:
        modOptFileNum = '90' + str(caseIndex)
    else:
        modOptFileNum = '9' + str(caseIndex)
    #Copy original optfile into new optfile specified by the new number in 900s
    shutil.copyfile('cplex.'+origOptExt, 'cplex.'+modOptFileNum)
    #Add writemps statement to new opt file
    with open('cplex.'+modOptFileNum, 'a') as file:
        file.write('\nwritemps ' + case_name + '.mps')
    return modOptFileNum


def runModel(caseindex,options,caseSwitches,lstfile,niter,timetype,yearfile,INPUTDir,
			 endyear,ccworkers,startiter,hourlyloadfile,
			 cc_curtchoice, GAMSDir, hpcchoice, output_folder=''):

	if output_folder == '':
		output_folder = 'E_Outputs'
		OutputDir = os.path.join(INPUTDir, "E_Outputs", "runs", lstfile)
	else:
		output_folder = os.path.abspath(output_folder)
		OutputDir = os.path.join(output_folder, "runs", lstfile)

	Path(os.path.join(OutputDir)).mkdir(parents=True, exist_ok=True)
	Path(os.path.join(OutputDir, "g00files")).mkdir(parents=True, exist_ok=True)
	Path(os.path.join(OutputDir, "lstfiles")).mkdir(parents=True, exist_ok=True)
	Path(os.path.join(OutputDir, "outputs")).mkdir(parents=True, exist_ok=True)
	Path(os.path.join(OutputDir, "gdxfiles")).mkdir(parents=True, exist_ok=True)
	
	# --- Clean paths entered in cases.csv ---
	yearfile = yearfile.replace('\\', os.sep).replace('/', os.sep)
	hourlyloadfile = hourlyloadfile.replace('\\', os.sep).replace('/', os.sep)
	
	solveyears= list(csv.reader(open(os.path.join(INPUTDir,"A_Inputs","inputs","sets",yearfile), 'r'), delimiter=","))[0]
	solveyears = [y for y in solveyears if y <= endyear]
	toLogGamsString =  ' logOption=4 logFile=' + str(os.path.join(OutputDir, 'gamslog.txt')) + ' ' + 'appendLog=1 '

	with open(os.path.join(OutputDir, 'compile_' + lstfile + FILE_EXTENSION), 'w') as OPATH:
		OPATH.write("gams " + str(os.path.join("A_Inputs", "a_inputs.gms")) +\
					" s=" + str(os.path.join(OutputDir,"g00files","data_india")) +\
					" o=" + str(os.path.join(OutputDir,"lstfiles","inputs.lst")) +\
					" --TotIter=" + str(niter) +' --hourlyloadfile=' + str(hourlyloadfile) + toLogGamsString + options + ' \n')
		OPATH.write("gams " + str(os.path.join("B_Equations","b1_model_constraints.gms")) +\
					" o=" + str(os.path.join(OutputDir,"lstfiles","Supply_Model.lst")) +\
					" r=" + str(os.path.join(OutputDir,"g00files","data_india")) + " s=" +\
					str(os.path.join(OutputDir,"g00files","supmod")) + ' \n')
		OPATH.write("gams " + str(os.path.join("B_Equations","b2_objective_function.gms")) +\
					" o=" + str(os.path.join(OutputDir,"lstfiles","Supply_Objective.lst")) +\
					" r=" + str(os.path.join(OutputDir,"g00files","supmod")) +\
					" s=" + str(os.path.join(OutputDir,"g00files","supply_objective" + ' \n')))

    
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

		if caseSwitches['GSw_ValStr'] != '0':
			modoptfile = makeOptFile(caseSwitches['GSw_gopt'], caseindex, lstfile)
		else:
			modoptfile = 4

		begyear = min(solveyears)
		with open(os.path.join(OutputDir, 'run_' + lstfile + FILE_EXTENSION), 'w') as OPATH:
			savefile = lstfile
			if startiter == 0:
				OPATH.writelines("gams " + str(os.path.join("C_Solve","c1_Solveprep.gms")) + " r=" +\
								 str(os.path.join(OutputDir,"g00files","supply_objective")) +\
								 " s=" + str(os.path.join(OutputDir,"g00files",savefile)) +\
								 " o=" + str(os.path.join(OutputDir,"lstfiles", lstfile +".lst")) +\
								 ' --hourlyloadfile='+str(hourlyloadfile) + toLogGamsString + options + \
								 ' --pythonpath=' + str(os.getenv('PYTHON_PATH')) + \
								 ' --casepath=' + OutputDir +'\n')
				restartfile=savefile
			if startiter > 0:
				restartfile = lstfile+"_"+startiter
	
			#for the number of iterations we have...
			niter = int(niter)
			startiter = int(startiter)

			if cc_curtchoice == 0:
				niter = 1
			
			for i in range(startiter,niter):
				#call the intertemporal solve
				savefile = lstfile+"_"+str(i)
				OPATH.writelines("gams " + str(os.path.join("C_Solve","c2_Solve_Int.gms")) +\
								 " o=" + str(os.path.join(OutputDir,"lstfiles", lstfile + "_" + str(i) + ".lst")) +\
								 " r=" + str(os.path.join(OutputDir,"g00files",restartfile)) + " s=" +\
								 str(os.path.join(OutputDir,"g00files",savefile)) + toLogGamsString +\
								 " --niter=" + str(i) + " --case=" + lstfile  + " --modoptfile=" + str(modoptfile) + ' --casepath=' + OutputDir + '\n')

				#start threads for cc/curt
				#no need to run cc curt scripts for final iteration or for one iteration
				if i < niter and niter > 1:
					if cc_curtchoice == 1:
						OPATH.writelines(f"{os.getenv('PYTHON_PATH')} " + str(os.path.join("D_Augur","d00_pickle_prep.py")) + " " + hourlyloadfile + " " + lstfile +\
										 " " + OutputDir + '\n')
						
						OPATH.writelines(f"{os.getenv('PYTHON_PATH')} " + str(os.path.join("D_Augur","augurbatch.py")) + " " + lstfile + " " + str(ccworkers) +\
										 " " + yearfile + " " + savefile + " " + str(begyear) + " " + str(endyear) + " " + str(timetype) + " " + str(i) + " " +\
										 OutputDir + '\n')
					   
						#merge all the resulting r2_in gdx files
						#the output file will be for the next iteration
						nextiter = i+1
						gdxmergedfile = os.path.join(OutputDir,"augur_data","ReEDS_augur_merged_" + lstfile + "_" + str(nextiter))
						OPATH.writelines("gdxmerge "+os.path.join(OutputDir,"augur_data","ReEDS_augur_"+lstfile+"*")+ " output=" + gdxmergedfile  + ' \n')
						#check to make sure previous calls were successful
						#AR - following line kept throwing up inconsistent tabs and spaces error
                 		#OPATH.writelines(writeerrorcheck(gdxmergedfile+".gdx"))

				restartfile=savefile
	
			if caseSwitches['GSw_ValStr'] != '0':
				OPATH.writelines('gams ' + str(os.path.join("F_Analysis","valuestreams","valuestreams.gms")) + " o=" +\
					 str(os.path.join(OutputDir,"lstfiles","valuestreams_" + lstfile + ".lst")) +\
					 " r=" + str(os.path.join(OutputDir,"g00files",restartfile)) + toLogGamsString +\
					 ' --case=' + lstfile + '\n')

			OPATH.writelines("gams " + str(os.path.join("E_Outputs","e1_create_report.gms")) + " o=" + str(os.path.join(output_folder,"runs",lstfile,"lstfiles","e1_create_report_" + lstfile + ".lst")) +\
							 " r=" + str(os.path.join(OutputDir,"g00files",restartfile)) + toLogGamsString + " --fname=" + lstfile + ' --casepath=' + OutputDir +' \n')
		   	
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


def main(ui_input=None, notify = None, uuid=None):
	
	if ui_input is None:
		ui_input = {}
		os.environ['PYTHON_PATH'] = 'python'
	
	if notify is not None:
		log_contents = []
		# def print(str_):
		# 	notify(str_, uuid)
		# 	log_contents.append(str_ + '\n')


	try:

		# import logging
		# logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s', stream=sys.stdout)
		# if 'output_folder_path' in ui_input:
			# if not os.path.exists(ui_input['output_folder_path']):
			# 	os.mkdir(ui_input['output_folder_path'])
			#sys.stdout = open(os.path.join(ui_input['output_folder_path'], 'process.out'), "w")
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
	#%%#
		# --- Gather user inputs from CLI before calling GAMS programs ---
		envVar = setupEnvironment(ui_input)

		# --- Check for Hourly Static File (i.e. /D_Augur/LDCfiles/India_8760) ---
		#filedst = os.path.join(os.getcwd(),"D_Augur","LDCfiles")
		filedst = os.path.join(os.path.abspath(os.path.dirname(__file__)),"D_Augur","LDCfiles")
	#%%#
		for i in list(set(envVar['hourlyloadfileset'])):
			# --- Stitch together state pickles into single (larger than githubs file limit) pickle ---
			if not os.path.exists(os.path.join(filedst, '{}_load.pkl'.format(i))):
				print(" ")
				print('Stitching together state load pickles for load scenario {}'.format(i))
				print(" ")
				state_load_dfs = []
				load_pickle_dir = os.path.join(filedst, 'state_load_pickles')
				for p in glob.glob(os.path.join(load_pickle_dir,"*{}*".format(i))):
					state_load_dfs.append(pd.read_pickle(os.path.join(load_pickle_dir,p)))
				India_8760_load = pd.concat(state_load_dfs, axis='columns')
				India_8760_load = India_8760_load.reset_index(drop=False)
				India_8760_load.to_pickle(os.path.join(filedst, '{}_load.pkl'.format(i)), protocol=2)

	#	for i in list(set(envVar['hourlystaticfileset'])): # i default is India_8760
	#		for j in pklfiles:
	#			checkLDCpkl(filedst = filedst, filename = i+j)
		checkLDCpkl(filedst, filename = "India_hour_season_ts_map.pkl")

		# --- Create runs directory ---
		if not os.path.exists(os.path.join("E_Outputs","runs")):
			os.mkdir(os.path.join("E_Outputs","runs"))
		
		# --- Create Threads for each Model ---
		createmodelthreads(envVar)
		
		# --- Interpret CLI flags to compile or run after batch scripts are created ---
		runnames = ['{}_{}'.format(envVar['runname'], i) for i in envVar['casenames']]
		n_runs = len(runnames)
		
		if ui_input:
			entry_folder = os.path.abspath(ui_input['output_folder_path'])
		else:
			entry_folder = 'E_Outputs'

		for r in runnames:

			if envVar['comp'] == 1: #compile the model if indicated by user
				shell_script_path = os.path.join(entry_folder,'runs',r,'compile_{}{}'.format(r, FILE_EXTENSION))
				subprocess.call('chmod +x {}'.format(shell_script_path), shell=True)
				subprocess.call(shell_script_path, shell=True)
				# print('Command executed', shell_script_path)
				# p1 = Popen('chmod +x {}'.format(shell_script_path), shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
				# if notify:
				# 	p1_stdout_content = p1.stdout.read().decode().split('\n')
				# 	for each in p1_stdout_content:
				# 		notify(each, uuid)
				# 	log_contents.extend(p1_stdout_content)

				# p2 = Popen(shell_script_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
				# if notify:
				# 	p2_stdout_content = p2.stdout.read().decode().split('\n')
				# 	for each in p2_stdout_content:
				# 		notify(each, uuid)
				# 	log_contents.extend(p2_stdout_content)

			if envVar['run'] == 1: #run the model if indicated by user
				shell_script_path = os.path.join(entry_folder,'runs',r,'run_{}{}'.format(r, FILE_EXTENSION))
				subprocess.call('chmod +x {}'.format(shell_script_path), shell=True)
				subprocess.call(shell_script_path, shell=True)
				# p3 = Popen('chmod +x {}'.format(shell_script_path), shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
				# if notify:
				# 	p3_stdout_content = p3.stdout.read().decode().split('\n')
				# 	for each in p3_stdout_content:
				# 		notify(each, uuid)
				# 	log_contents.extend(p3_stdout_content)

				# p4 = Popen(shell_script_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
				# if notify:
				# 	p4_stdout_content = p4.stdout.read().decode().split('\n')
				# 	for each in p4_stdout_content:
				# 		notify(each, uuid)
				# 	log_contents.extend(p4_stdout_content)
					
			if r == runnames[(n_runs-1)]: #process results if the final run has finished
				if envVar['hpcchoice'] == 0:
					if ui_input == {}:
						solutions_dir = os.path.join("E_Outputs", "runs")
						saveexcel = 'F'
					else:
						solutions_dir = entry_folder
						saveexcel = 'T'
					#print("{} {} {} {} {}".format(os.getenv('PYTHON_PATH'), os.path.join("E_Outputs", "e2_process_outputs.py"), solutions_dir, saveexcel, " ".join(runnames)))
					os.system("{} {} {} {} {}".format(os.getenv('PYTHON_PATH'), os.path.join("E_Outputs", "e2_process_outputs.py"), solutions_dir, saveexcel, " ".join(runnames)))
				else:
					solutions_dir = os.path.join("E_Outputs", "runs")
					saveexcel = 'F'
					process_outputs_command = "{} {} {} {} {}".format(os.getenv('PYTHON_PATH'), os.path.join("E_Outputs", "e2_process_outputs.py"), solutions_dir, saveexcel, " ".join(runnames))
					with open(os.path.join("shfiles", r + '.sh'), 'a') as OPATH:
						OPATH.write("\n")
						OPATH.write(process_outputs_command)
					OPATH.close()

		if notify:
			with open(os.path.join(ui_input['output_folder_path'], 'full_log.txt'), 'w') as f:
				f.writelines(log_contents)
	except Exception as e:
		if notify:
			log_contents.append(traceback.format_exc() + f" >> {str(e)}")
			with open(os.path.join(ui_input['output_folder_path'], 'full_log.txt'), 'w') as f:
				f.writelines(log_contents)

if __name__ == '__main__':
	# --- Wrapper to run from CLI ---
 
	try:
		main()
	except Exception as e:
		raise e
	

# %%
