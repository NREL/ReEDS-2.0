# import necessary packages
import os
import sys
import queue
import threading
import csv
import subprocess


def createCurtCCThreads(case,ccworkers,yearset,restartfile,startyear,endyear,timetype,iteration):

    q = queue.Queue()
    num_worker_threads = int(ccworkers)
    
    def ccworker():
        while True:
            ThreadInit = q.get()
            if ThreadInit is None:
                break
            case = ThreadInit['case']
            cur_year = ThreadInit['cur_year']
            #call the reflow script with appropriate options
            if os.name!='posix':
                os.system(f"start /wait cmd /c  {os.getenv('PYTHON_PATH')} " + os.path.join('D_Augur','d0_ReEDS_augur.py') + " " + case + " " + str(cur_year) + " " + str(cur_year) + " " + timetype + " " + str(iteration))
            if os.name=="posix":
                shellscript = subprocess.Popen([f"{os.getenv('PYTHON_PATH')} " + os.path.join('D_Augur','d0_ReEDS_augur.py') + " " + case + " " + str(cur_year) + " " + str(cur_year) + " " + timetype + " " + str(iteration) + ' >/dev/null'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,shell=True)
                #wait for it to finish before killing the thread
                shellscript.wait()
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

    case = sys.argv[1]
    ccworkers = sys.argv[2]
    yearfile = sys.argv[3]
    yearset = list(csv.reader(open(os.path.join("A_Inputs","inputs","sets",yearfile), 'r'), delimiter=","))
    restartfile = sys.argv[4]
    startyear = sys.argv[5]
    endyear = sys.argv[6]
    timetype = sys.argv[7]
    iteration = sys.argv[8]

    print("Beginning batch run of Augur calls using options: ")
    print("Case: "+case)
    print("Number of threads: "+str(ccworkers))
    print("Year file: " + yearfile)
    print("Restart file: " + restartfile)
    print("Start year: " + str(startyear))
    print("End year: " + str(endyear))
    print("timetype: " + timetype)
    print("iteration: " + str(iteration))

    createCurtCCThreads(case,ccworkers,yearset,restartfile,startyear,endyear,timetype,iteration)

if __name__ == '__main__':
    main()