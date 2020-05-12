# -------------------------------------------------------------------------------
# name:        d1_8760batch.py
# purpose:     to handle input and output from GAMS models
#
# author:      maxwell brown (maxwell.l.brown@gmail.com)
#
# copyright:    free to share
# -----------------------------------------------------------------------------
# To run this script, adjust the environment to the current PC in
# setupEnvironment(), source the file, then run main() -- instructions to
# generalize this script to other models are below
#

# import necessary packages
import os
import sys
from datetime import datetime
import queue
import threading
import subprocess
import time
import shutil
import csv
import zipfile
import operator
import time
from random import randrange
from distutils.dir_util import copy_tree

from tempfile import mkstemp
from shutil import move
from os import remove, close


def createCCCurtThreads(case,ccworkers,yearset,restartfile,startyear,endyear,ldcgdx):

    q = queue.Queue()
    num_worker_threads = int(ccworkers)
    
    def ccworker():
        while True:
            ThreadInit = q.get()
            if ThreadInit is None:
                break
            case = ThreadInit['case']
            cur_year = ThreadInit['cur_year']
            restartfile = ThreadInit['restartfile']
            #call the 8760 script with appropriate options

            sh_string = "gams " + os.path.join('D_8760', 'd2_call8760.gms') + " --restartfile=" + os.path.join('E_Outputs','runs',case,'g00files',restartfile) + " o=" + os.path.join('E_Outputs','runs',case,'lstfiles','d2_call8760.lst') + " --case=" + case + " --cur_year=" + str(cur_year) + " --next_year=" + str(cur_year) + " logOption=4" + " logFile=" + os.path.join('E_Outputs','runs',case,'8760log.txt') + " appendLog=1"
            
            if os.name!='posix':
                os.system("start /wait cmd /c  " + sh_string)
            if os.name=="posix":
                # shellscript = subprocess.Popen(sh_string, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
                #wait for it to finish before killing the thread
                # shellscript.wait()
                subprocess.call(sh_string, shell=True)
            q.task_done()

    threads = []

    for i in range(num_worker_threads):
        t = threading.Thread(target=ccworker)
        t.start()
        threads.append(t)

    for i in range(len(yearset[0])):
        if int(yearset[0][i]) <= int(endyear) and int(yearset[0][i]) >= int(startyear):
            q.put({'case':case,
                   'cur_year':yearset[0][i],
                   'restartfile':restartfile})

# block until all tasks are done
    q.join()

    # stop workers
    for i in range(num_worker_threads):
        q.put(None)

    for t in threads:
        t.join()


def main():
    InputDir = os.getcwd()


    case = sys.argv[1]
    ccworkers = sys.argv[2]
    yearfile = sys.argv[3]
    yearset = list(csv.reader(open(os.path.join(InputDir,yearfile), 'r'), delimiter=","))
    restartfile = sys.argv[4]
    startyear = sys.argv[5]
    endyear = sys.argv[6]
    ldcgdx = sys.argv[7]

    print("Beginning batch run of 8760 calls using options: ")
    print("Case: "+case)
    print("Number of threads: "+str(ccworkers))
    print("Year file: " + yearfile)
    print("Restart file: " + restartfile)
    print("Start year: " + str(startyear))
    print("End year: " + str(endyear))
    print("LDC gdx file: " + ldcgdx)


    createCCCurtThreads(case,ccworkers,yearset,restartfile,startyear,endyear,ldcgdx)

if __name__ == '__main__':
    main()
