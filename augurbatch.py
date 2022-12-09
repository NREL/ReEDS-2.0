
# import necessary packages
import os
import sys
import queue
import threading
import csv
import subprocess


def createCurtCCThreads(case, ccworkers, yearset, restartfile, startyear,
                        endyear, distpv, csp, dr, timetype, waterswitch,
                        iteration):

    q = queue.Queue()
    num_worker_threads = int(ccworkers)

    def ccworker():
        while True:
            ThreadInit = q.get()
            if ThreadInit is None:
                break
            case = ThreadInit['case']
            cur_year = ThreadInit['cur_year']
            # call the reflow script with appropriate options
            if os.name != 'posix':
                os.system('start /wait cmd /c  python ' + os.path.join(
                    'ReEDS_Augur', 'ReEDS_Augur.py') + ' ' + case + ' '
                    + str(cur_year) + ' ' + str(cur_year) + ' ' + timetype
                    + ' ' + str(csp) + ' ' + str(dr) + ' ' + str(waterswitch) + ' '
                    + str(iteration) + ' ' + str(marg_vre) + ' ' + str(marg_dr) + ' '
                    + str(marg_stor) + ' ' + str(marg_dr))
            if os.name == 'posix':
                shellscript = subprocess.Popen(
                    ['python ' + os.path.join('ReEDS_Augur', 'ReEDS_Augur.py')
                     + ' ' + case + ' ' + str(cur_year) + ' ' + str(cur_year)
                     + ' ' + timetype + ' ' + str(csp) + ' ' + str(dr) + ' ' + str(waterswitch)
                     + ' ' + str(iteration) + ' ' + str(marg_vre) + ' ' + str(marg_dr) + ' '
                     + str(marg_stor) + ' ' + str(marg_dr) + ' >/dev/null'],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, shell=True)
                # wait for it to finish before killing the thread
                shellscript.wait()
            q.task_done()

    threads = []

    for i in range(num_worker_threads):
        t = threading.Thread(target=ccworker)
        t.start()
        threads.append(t)

    for i in range(len(yearset[0])):
        idx1 = int(yearset[0][i]) <= int(endyear)
        idx2 = int(yearset[0][i]) >= int(startyear)
        if idx1 and idx2:
            q.put({'case': case,
                   'cur_year': yearset[0][i],
                   'restartfile': restartfile})

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
    yearset = list(csv.reader(open(os.path.join(yearfile), 'r'),
                              delimiter=','))
    restartfile = sys.argv[4]
    startyear = sys.argv[5]
    endyear = sys.argv[6]
    distpv = sys.argv[7]
    csp = sys.argv[8]
    dr = sys.argv[9]
    timetype = sys.argv[10]
    waterswitch = sys.argv[11]
    iteration = sys.argv[12]
    marg_vre = sys.argv[13]
    marg_stor = sys.argv[14]
    marg_dr = sys.argv[15]

    print('Beginning batch run of Augur calls using options: ')
    print('Case: '+case)
    print('Number of threads: '+str(ccworkers))
    print('Year file: ' + yearfile)
    print('Restart file: ' + restartfile)
    print('Start year: ' + str(startyear))
    print('End year: ' + str(endyear))
    print('distpv switch setting: ' + distpv)
    print('calc_csp_cc setting: ' + csp)
    print('calc_dr_cc setting: ' + dr)
    print('timetype: ' + timetype)
    print('waterswitch' + waterswitch)
    print('iteration: ' + str(iteration))
    print('marg_vre: ' + str(marg_vre))
    print('marg_stor: ' + str(marg_stor))
    print('marg_dr: ' + str(marg_dr))

    createCurtCCThreads(case, ccworkers, yearset, restartfile, startyear,
                        endyear, distpv, csp, dr, timetype, waterswitch,
                        iteration, marg_vre, marg_stor, marg_dr)


if __name__ == '__main__':
    main()
