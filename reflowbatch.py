
# import necessary packages
import os
import sys
import queue
import threading
import csv
import subprocess


def createCurtCCThreads(case,ccworkers,yearset,restartfile,startyear,endyear,ldcgdx,distpv,csp,timetype):

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
            #call the reflow script with appropriate options
            if os.name!='posix':
                os.system("start /wait cmd /c  gams d_callreflow.gms --restartfile=" + os.path.join("g00files",restartfile)+" --case=" + case + " --cur_year=" + str(cur_year) + " --next_year="+str(cur_year) + ' --DistPVSwitch='+ str(distpv) + ' --calc_csp_cc='+ str(csp) + ' --timetype=' + str(timetype))
            if os.name=="posix":
                shellscript = subprocess.Popen(["gams d_callreflow.gms logOption=2 al=1 logFile=gamslog.txt --restartfile=" + os.path.join("g00files",restartfile)+" --case=" + case + " --cur_year=" + str(cur_year) + " --next_year="+str(cur_year) + ' --DistPVSwitch='+ str(distpv) + ' --calc_csp_cc='+ str(csp) + ' --timetype=' + str(timetype) + ' >/dev/null'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,shell=True)
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
    yearset = list(csv.reader(open(os.path.join(yearfile), 'r'), delimiter=","))
    restartfile = sys.argv[4]
    startyear = sys.argv[5]
    endyear = sys.argv[6]
    ldcgdx = sys.argv[7]
    distpv = sys.argv[8]
    csp = sys.argv[9]
    timetype = sys.argv[10]


    print("Beginning batch run of reflow calls using options: ")
    print("Case: "+case)
    print("Number of threads: "+str(ccworkers))
    print("Year file: " + yearfile)
    print("Restart file: " + restartfile)
    print("Start year: " + str(startyear))
    print("End year: " + str(endyear))
    print("LDC gdx file: " + ldcgdx)
    print("distPV switch setting: " + distpv)
    print("calc_csp_cc setting: " + csp)
    print("timetype: " + timetype)

    createCurtCCThreads(case,ccworkers,yearset,restartfile,startyear,endyear,ldcgdx,distpv,csp,timetype)

if __name__ == '__main__':
    main()
