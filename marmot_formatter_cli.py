import os
import re
import argparse
import gdxpds
import pandas as pd

from marmot.marmot_h5_formatter import MarmotFormat

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

gams_locator = GamsDirFinder()
GAMSDir = str(gams_locator.gams_dir)
os.environ['GAMSDIR'] = GAMSDir

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="""Marmot Formatter CLI""")
    parser.add_argument("model", help="Which model type are you formatting",
                        choices=['ReEDS', 'ReEDS_India', 'SIIP','PLEXOS'])
    parser.add_argument("scenarios", help="Scenario names", nargs='+', type=str)
    parser.add_argument("model_input_folder",
                        help="PLEXOS/ReEDS solutions folder", type=str)
    parser.add_argument("properties_file",
                        help="model properties filepath with list of properties to process",
                        type=str)
    # args = parser.parse_args()
    parser.add_argument("-sf", "--solutions_folder", help='where to save outputs (defaults to model_input_folder)',
                        type=str, default=None)
    parser.add_argument("-rm", "--region_mapping", help='region_mapping filepath to map custom regions/zones',
                        type=str, default=pd.DataFrame())
    parser.add_argument("-emit", "--emit_names", help='emit_names filepath to rename emissions types',
                        type=str, default=pd.DataFrame())


    args = parser.parse_args()

    if args.solutions_folder is None:
        solutions_folder = args.model_input_folder
    else:
        solutions_folder = args.solutions_folder

    for scenario in args.scenarios:
        initiate = MarmotFormat(
                Scenario_name=scenario,
                Model_Solutions_folder=args.model_input_folder,
                Marmot_Solutions_folder=solutions_folder,
                Properties_File=args.properties_file,
                Region_Mapping=args.region_mapping,
                emit_names=args.emit_names
                )
        initiate.run_formatter(args.model)
