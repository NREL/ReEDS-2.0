
/*
 * gcmt.c
 *
 * implementation of support routines for multi-threaded apps
 *
 * Copyright (c) 2017-2020 GAMS Software GmbH <support@gams.com>
 * Copyright (c) 2017-2020 GAMS Development Corp. <support@gams.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

#include "gcmt.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#if defined(_WIN32)
#  include <windows.h>
#else
#  include <unistd.h>
#  include <errno.h>
#  include <pthread.h>
#  include <sys/time.h>
#endif

#define WINMX(p) &(p->wcs)
#define PTHMX(p) &(p->pmx)
#define WINCV(p) &(p->wcv)
#define PTHCV(p) &(p->pcv)

/* GC_WtTime_t is essentially the Windows _FILETIME:
 * the number of 100-nanosecond intervals since
 * 1 Jan, 1601 (UTC)
 * Let's call a nick a 100-nanosecond interval
 * Basic facts:
 *   encodeDateCV(1601,1,1) = 0
 *   encodeDateCV(1602,1,1) = 315360000000000
 *                          = number of nicks in a non-leap-year
 *
 *   encodeDate(1899,12,30) = 0
 *   encodeDate(1601,1,1)   = -109205
 *
 * so we want
 *
 *   encodeDateCV(1899,12,30) = 109205 * nicksPerDay
 *                            = 94353120000000000
 *                              (verified via SystemTimeToFileTime)
 */

/* Epochs (zero-time) for some different time types:
 *   Unix      epoch:  1 Jan 1970 00:00:00.00 UTC
 *   WtTime_t  epoch:  1 Jan 1601 00:00:00.00 UTC
 *   TDateTime epoch: 30 Dec 1899 00:00:00.00 local time
 *
 * WtTime_t epoch + DATE_DELTA_WT_DT = TDateTime epoch
 * so ...  trunk(TDateTime) + DATE_DELTA_WT_DT = (WtTime_t div NICKS_PER_DAY)
 * WtTime_t epoch + DATE_DELTA_WT_UNIX = Unix epoch
 */

#define DATE_DELTA_WT_UNIX 134774

#define NICKS_PER_USEC 10L   /* one NICK = 1e-1 micro-seconds = 1e-7 seconds */
#define NICKS_PER_MSEC (1000L * NICKS_PER_USEC)
#define NICKS_PER_SEC  (1000L * NICKS_PER_MSEC)
#define NICKS_PER_MIN  (60L * NICKS_PER_SEC)
#if defined(GC_LONG_LONG)
# define NICKS_PER_HOUR (60LL * NICKS_PER_MIN)
# define NICKS_PER_DAY  (24LL * NICKS_PER_HOUR)
# define NICKS_PER_YEAR (365LL * NICKS_PER_DAY)
#else
# define NICKS_PER_HOUR (60L * NICKS_PER_MIN)
# define NICKS_PER_DAY  (24L * NICKS_PER_HOUR)
# define NICKS_PER_YEAR (365L * NICKS_PER_DAY)
#endif

#if defined(_WIN32)
typedef union FTunion {
  __int64 i64;
  FILETIME ft;
} FTunion_t;


/* return number of ticks in (wt - now), rounding up, or to zero if negative */
static DWORD tickDeltaWtTime (GC_WtTime_t wt)
{
  DWORD result;
  GC_WtTime_t d, r;

  d = wt - GC_nowWtTime();
  if (d < 0)
    return 0;
  result = (DWORD) (d / NICKS_PER_MSEC);
  r = d % NICKS_PER_MSEC;
  if (r > 0)
    result++;
  return result;
} /* tickDeltaWtTime */

#else

static void wttime2timespec (GC_WtTime_t wt, struct timespec *ts)
{
  GC_WtTime_t t;                /* really an int64 */

  t = wt - NICKS_PER_DAY * DATE_DELTA_WT_UNIX;
  ts->tv_sec = t / NICKS_PER_SEC;
  t = t % NICKS_PER_SEC;
  ts->tv_nsec = t * 100;
} /* wttime2timespec */


#endif  /* if defined(_WIN32) .. else .. */


GC_WtTime_t GC_nowWtTime (void)
{
#if defined(_WIN32)
  FTunion_t ftu;

  GetSystemTimeAsFileTime (&(ftu.ft));
  return ftu.i64;
#else
  struct timeval tv;
  int rc;

  rc = gettimeofday (&tv, NULL);
  if (rc)
    return 0;
  return  tv.tv_sec * NICKS_PER_SEC + tv.tv_usec * NICKS_PER_USEC
    + NICKS_PER_DAY * DATE_DELTA_WT_UNIX;
#endif
} /* GC_nowWtTime */


void GC_incWtTime (GC_WtTime_t *wt, unsigned int ticks)
{
  *wt += ticks * NICKS_PER_MSEC;
} /* GC_incWtTime */


void GC_decWtTime (GC_WtTime_t *wt, unsigned int ticks)
{
  *wt -= ticks * NICKS_PER_MSEC;
} /* GC_decWtTime */


typedef int (*threadProc_t)(GC_thread_t *thd);

typedef struct GC_threadRec {
  threadProc_t thdProc;
  GC_thread_t *thd;
} GC_threadRec_t;


#if defined(_WIN32)
static DWORD __stdcall winWrapper (void *arg)
{
  GC_threadRec_t *p;
  threadProc_t f;
  GC_thread_t *_thd;
  int rc;

  p = (GC_threadRec_t *) arg;
  f = p->thdProc;
  _thd = p->thd;
  free(p);
  rc = f(_thd);
  return (DWORD) rc;
} /* winWrapper */
#else
/* pthreadWrapper
 * wrapper function for calling user functions associated with threads
 * make sure to save the args into local space first, since the routine
 * calling this thread wrapper function
 * is in another thread and may return before we get rolling, so we can't put the
 * data on the stack of the routine that started this thread.
 */
static void * pthreadWrapper (void *arg)
{
  GC_threadRec_t *p;
  threadProc_t f;
  GC_thread_t *_thd;
  int rc;
  long rcLong;

  p = (GC_threadRec_t *) arg;
  f = p->thdProc;
  _thd = p->thd;
  free(p);
  rc = f(_thd);
  rcLong = rc;
  return (void *) rcLong;
} /* pthreadWrapper */
#endif


static int threadProc (GC_thread_t *thd)
{
  int rc;

#if defined(_WIN32)
#else
  (void) pthread_mutex_lock (&(thd->suspendedMux)); /* use mutex like a binary semaphore */
#endif
  if (! thd->terminated)
    thd->thdFunc (thd);
  rc = thd->returnValue;
  thd->finished = 1;
#if defined(_WIN32)
  ExitThread(rc);
#else
  {
    long int rcLong = rc;
    pthread_exit((void *)rcLong);
  }
#endif
  return rc;
} /* threadProc */

int GC_thread_init (GC_thread_t *thd, GC_thread_func_t _thdFunc, void *_userData)
{
  int rc;
  GC_threadRec_t *p;

  if ((NULL == thd) || (NULL == _thdFunc))
    return 1;
  memset (thd, 0, sizeof(*thd));
  thd->thdFunc = _thdFunc;
  thd->userData = _userData;
  p = (GC_threadRec_t*) malloc (sizeof(*p)); /* free in threadWrapper - need the space until then */
  assert(p);
  p->thdProc = threadProc;
  p->thd = thd;

#if defined(_WIN32)
  {
    HANDLE h;
    DWORD tid;

    h = CreateThread (NULL, 0, &winWrapper, p, CREATE_SUSPENDED, &tid);
    if (0 == h) {
      rc = GetLastError();
      free(p);
      return rc;
    }
    thd->handle = h;
    thd->threadID = tid;
  }
#else
  rc = pthread_mutex_init (&(thd->suspendedMux), NULL);
  if (rc) {
    free(p);
    return rc;
  }
  rc = pthread_mutex_lock (&(thd->suspendedMux));
  if (rc) {
    free(p);
    (void) pthread_mutex_destroy (&(thd->suspendedMux));
    return rc;
  }
  rc = pthread_create (&(thd->pth), NULL, &pthreadWrapper, p);
  if (rc) {
    free(p);
    (void) pthread_mutex_unlock (&(thd->suspendedMux));
    (void) pthread_mutex_destroy (&(thd->suspendedMux));
    return rc;
  }
#endif
  
  return 0;
} /* GC_thread_init */


void GC_thread_resume (GC_thread_t *thd)
{
  if (! thd->initialSuspendDone) {
    thd->initialSuspendDone = 1;
#if defined(_WIN32)
    (void) ResumeThread (thd->handle);
#else
    (void) pthread_mutex_unlock (&(thd->suspendedMux));
#endif
  }
  return;
} /* GC_thread_resume */


int GC_thread_waitFor (GC_thread_t *thd)
{
#if defined(_WIN32)
  int waitResult;
  BOOL brc;
  DWORD d;

  waitResult = WaitForSingleObject (thd->handle, INFINITE);
  brc = GetExitCodeThread (thd->handle, &d);
  if (brc)
    return (int) d;
  return -1;
#else
  void *vp = NULL;
  int rc;
  long int rcLong;
  pthread_t pth;

  pth = thd->pth;
  thd->pth = 0;
  rc = pthread_join (pth, &vp);
  rcLong = (long int) vp;
  rc = (int) rcLong;
  return rc;
#endif
} /* GC_thread_waitFor */


void GC_thread_delete (GC_thread_t *thd)
{
  int tid;

#if defined(_WIN32)
  tid = (0 != thd->threadID);
#else
  tid = (0 != thd->pth);
#endif

  if (tid && (! thd->finished)) {
    thd->terminated = 1;
    GC_thread_resume (thd);
    GC_thread_waitFor (thd);
  }
#if defined(_WIN32)
  if (thd->handle)
    CloseHandle (thd->handle);
#else
  if (thd->pth) {
    pthread_detach (thd->pth);
  }
  /* should probably check if non-null first */
  (void) pthread_mutex_destroy (&(thd->suspendedMux));
#endif
  memset (thd, 0, sizeof(*thd));
} /* GC_thread_delete */


int GC_mutex_init (GC_mutex_t *mx)
{
#if defined(_WIN32)
  InitializeCriticalSection (WINMX(mx));
  return 0;
#else
  int rc;
  rc = pthread_mutex_init (PTHMX(mx), NULL);
  return rc;
#endif
} /* GC_mutex_init */


void GC_mutex_delete (GC_mutex_t *mx)
{
#if defined(_WIN32)
  DeleteCriticalSection (WINMX(mx));
#else
  (void) pthread_mutex_destroy (PTHMX(mx));
#endif
  memset (mx, 0, sizeof(*mx));
  return;
} /* GC_mutex_delete */


int GC_mutex_lock (GC_mutex_t *mx)
{
#if defined(_WIN32)
  EnterCriticalSection (WINMX(mx));
  return 0;
#else
  int rc;

  rc = pthread_mutex_lock (PTHMX(mx));
  return rc;
#endif
} /* GC_mutex_lock */


int GC_mutex_trylock (GC_mutex_t *mx, int *gotIt)
{
#if defined(_WIN32)
  *gotIt = TryEnterCriticalSection (WINMX(mx));
  return 0;
#else
  int rc;

  *gotIt = 1;
  rc = pthread_mutex_trylock (PTHMX(mx));
  if (EBUSY == rc) {
    *gotIt = 0;
    rc = 0;
  }
  return rc;
#endif
} /* GC_mutex_trylock */


int GC_mutex_unlock (GC_mutex_t *mx)
{
#if defined(_WIN32)
  LeaveCriticalSection (WINMX(mx));
  return 0;
#else
  int rc;

  rc = pthread_mutex_unlock (PTHMX(mx));
  return rc;
#endif
} /* GC_mutex_unlock */


int GC_cond_init (GC_cond_t *cv)
{
#if defined(_WIN32)
  memset (cv, 0, sizeof(*cv));
  InitializeConditionVariable (WINCV(cv));
  return 0;
#else
  int rc;
  rc = pthread_cond_init (PTHCV(cv), NULL);
  return rc;
#endif
} /* GC_cond_init */


void GC_cond_delete (GC_cond_t *cv)
{
#if defined(_WIN32)
                                /* nothing to do on Windows */
#else
  (void) pthread_cond_destroy (PTHCV(cv));
#endif
  memset (cv, 0, sizeof(*cv));
  return;
} /* GC_cond_delete */


void GC_cond_notifyOne (GC_cond_t *cv)
{
#if defined(_WIN32)
  WakeConditionVariable (WINCV(cv));
#else
  (void) pthread_cond_signal (PTHCV(cv));
#endif
} /* GC_cond_notifyOne */


void GC_cond_notifyAll (GC_cond_t *cv)
{
#if defined(_WIN32)
  WakeAllConditionVariable (WINCV(cv));
#else
  (void) pthread_cond_broadcast (PTHCV(cv));
#endif
} /* GC_cond_notifyAll */

void GC_cond_wait (GC_cond_t *cv, GC_mutex_t *mx)
{
#if defined(_WIN32)
  SleepConditionVariableCS (WINCV(cv), WINMX(mx), INFINITE);
#else
  (void) pthread_cond_wait (PTHCV(cv), PTHMX(mx));
#endif
} /* GC_cond_wait */

/* GC_cond_timedWaitAbs
 * returns "notified", i.e.,
 *    false    if the time limit was reached,
 *    true     o/w, i.e. the CV was notified
 */
int GC_cond_timedWaitAbs (GC_cond_t *cv, GC_mutex_t *mx, GC_WtTime_t absTime)
{
#if defined(_WIN32)
  DWORD dw, ticks;

  ticks = tickDeltaWtTime (absTime);
  if (! SleepConditionVariableCS (WINCV(cv), WINMX(mx), ticks)) {
    dw = GetLastError();
    if ((ERROR_TIMEOUT == dw) || (WAIT_TIMEOUT == dw))
      return 0;                 /* not notified, timed out instead */
    assert(0);                  /* should not be - what to do? */
  }
  return 1;                     /* was notified */
#else
  int rc;
  struct timespec ts;

  wttime2timespec (absTime, &ts);
  rc = pthread_cond_timedwait (PTHCV(cv), PTHMX(mx), &ts);
  if (ETIMEDOUT == rc)
    return 0;
  /* assert(0==rc); */
  return (0==rc);
#endif
} /* GC_cond_timedWaitAbs */
