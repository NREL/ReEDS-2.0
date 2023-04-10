/*
 * gcmt.h
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

#if ! defined(_GCMT_H_)
#define       _GCMT_H_

#if defined(_WIN32)
#  include <windows.h>
#  define GC_thread_API WINAPI
#else
#  include <unistd.h>
#  include <pthread.h>
#  define GC_thread_API
#endif

typedef struct GC_thread GC_thread_t;
typedef void (GC_thread_API *GC_thread_func_t) (GC_thread_t *thr);

struct GC_thread {
  void *userData;
  GC_thread_func_t thdFunc;
  int returnValue;
  int terminated;               /* was termination requested?? */
  int finished;                 /* has thdFunc finished? */
  int initialSuspendDone;
#if defined(_WIN32)
  HANDLE handle;
  DWORD threadID;
#else
  pthread_mutex_t suspendedMux;
  pthread_t pth;
#endif
};


typedef struct GC_mutex {
#if defined(_WIN32)
  CRITICAL_SECTION wcs;         /* win cs */
#else
  pthread_mutex_t pmx;          /* pthread mutex */
#endif
} GC_mutex_t;

typedef struct GC_cond {
#if defined(_WIN32)
  CONDITION_VARIABLE wcv;       /* win cv */
#else
  pthread_cond_t pcv;           /* pthread cv */
#endif
} GC_cond_t;

#if defined(_WIN32)
typedef __int64 GC_WtTime_t;

#elif (defined(__WORDSIZE) && (64 == __WORDSIZE))
typedef long int GC_WtTime_t;

#elif (defined(__SIZEOF_POINTER__) && (8 == __SIZEOF_POINTER__))
typedef long int GC_WtTime_t;

#else
typedef long long int GC_WtTime_t;   /* incomplete */
#define GC_LONG_LONG
#endif


#if defined(__cplusplus)
extern "C" {
#endif

GC_WtTime_t GC_nowWtTime (void);
void GC_incWtTime (GC_WtTime_t *wt, unsigned int ticks);
void GC_decWtTime (GC_WtTime_t *wt, unsigned int ticks);

int GC_thread_init (GC_thread_t *thd, GC_thread_func_t _thdFunc, void *_userData);
void GC_thread_resume (GC_thread_t *thd);
int GC_thread_waitFor (GC_thread_t *thd);
void GC_thread_delete (GC_thread_t *thd);

int GC_mutex_init (GC_mutex_t *mx);
void GC_mutex_delete (GC_mutex_t *mx);
int GC_mutex_lock (GC_mutex_t *mx);
int GC_mutex_trylock (GC_mutex_t *mx, int *gotIt);
int GC_mutex_unlock (GC_mutex_t *mx);

int GC_cond_init (GC_cond_t *cv);
void GC_cond_delete (GC_cond_t *cv);
void GC_cond_notifyOne (GC_cond_t *cv);
void GC_cond_notifyAll (GC_cond_t *cv);
void GC_cond_wait (GC_cond_t *cv, GC_mutex_t *mx);
int GC_cond_timedWaitAbs (GC_cond_t *cv, GC_mutex_t *mx, GC_WtTime_t absTime);

#if defined(__cplusplus)
}
#endif

#endif /* defined(_GCMT_H_) */
