#!/usr/bin/env python3.6

import os
import sys
import subprocess
import timeit
import time
import multiprocessing as mp
import traceback
import argparse

import data

def error_cb(error):
    traceback.format_exc()

parser = argparse.ArgumentParser('Run a list of experiment tuples')
# tuple of 3: (trialdir, exelist str)
parser.add_argument('-j', '--jobid', help='unique job id', required=True)
parser.add_argument('-w', '--workers', help='number of workers', type=int, required=True)
parser.add_argument('-e', '--env', help='environment variables to set', nargs=2, action='append')
parser.add_argument('-r', '--runlist', help='list to run', nargs=3, action='append', required=True)
args = parser.parse_args()

class Counter(object):
    def __init__(self, initval=0):
        self.val = mp.RawValue('i', initval)
        self.lock = mp.Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1
            # Update jobid log
            with open(args.jobid + '.log', 'w') as f:
                f.write( '%d\n'%(self.val.value)  )

    @property
    def value(self):
        return self.val.value

def init(args):
    counter = args

def run(e):
    trialdir= e[0]
    timeout = float( e[1] )
    # timeout 0 means no timeout
    if timeout == 0:
        timeout = None
    
    exelist = e[2].split()
    #print('trialdir:' + trialdir)
    #print('==== exelist ====')
    #print(exelist)
    #print('==== end of exelist ====')

    out_file = open(trialdir + '/output.txt', 'w')
    err_file = open(trialdir + '/error.txt', 'w')
    ret = 0
    timed_out = False

    #print('==== before run ====')
    #print(exelist)
    #print('==== end before run ====')

    runenv = os.environ.copy()
    #newenv['LD_BIND_NOW'] = '1' # ggout ggin
    if args.env:
        for e in args.env:
            runenv[e[0]] = e[1]
            #print('setting %s=%s'%(e[0], e[1]) ) # ggout
    start = time.perf_counter()
    try:
        #exelist = ['env']
        p = subprocess.Popen(exelist, stdout=out_file, stderr=err_file, env=runenv, cwd=trialdir)
        p.wait(timeout)
        #p = subprocess.run(exelist, stdout=out_file, stderr=err_file, timeout=timeout)
        #p = subprocess.run(exelist, stdout=out_file, stderr=subprocess.DEVNULL, timeout=timeout)
        ret = p.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
    xtime = time.perf_counter() - start

    out_file.close()
    err_file.close()

    #print('RET: ' + str(ret))
    ret_file = open(trialdir + '/ret.txt', 'w')
    if timed_out:
        ret_file.write('timeout\n')
        #print('Process timed out!')
    elif ret < 0:
        ret_file.write('crash, ' + str(ret) + '\n')
    elif ret > 0:
        ret_file.write('error, ' + str(ret) + '\n')
    else:
        ret_file.write('exit, ' + str(ret) + '\n')
    ret_file.close()

    #print('time: %.2f'%(xtime))
    with open(trialdir + '/time.txt', 'w') as f:
        f.write('%.2f'%(xtime) + '\n')

    counter.increment()
    #print('Profiling ' + ' '.join(e) + ' done')


# Create pool of worker threads
nworkers = args.workers
if nworkers <= 0:
    nworkers = os.cpu_count()

counter = Counter(0)
pool = mp.Pool( nworkers, initializer=init, initargs=(counter, ) )

#print('N workers %d'%(nworkers));
#print(args.runlist)

# XXX: coarse grain chunking hurts load balancing, let defaults
pool.map(run, args.runlist)#, chunksize=int( max( 1, len(args.runlist)/nworkers ) ) )

pool.close()
try:
    pool.join()
except KeyboardInterrupt:
    pool.terminate()
    pool.join()
