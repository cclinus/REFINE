#!/usr/bin/env python3.6

import os
import sys
import subprocess
import argparse
import itertools
import re
import numpy as np
import time

import data
import fi_tools

try:
    homedir = os.environ['HOME']
except:
    print('Env variable HOME is missing')
    sys.exit(1)

try:
    scriptdir = os.environ['SCRIPTDIR']
except:
    print('Env variable HOME is missing')
    sys.exit(1)


def srun(partition, nworkers, env, chunk):
    runargs = []
    if env:
        for e in env:
            runargs += [ '-e', e[0], e[1] ]
    
    for i in chunk:
        runargs += ['-r'] + i
    runlist=[scriptdir + '/run.py'] + ['-w', str(nworkers)] + runargs
    #print(runlist)
    #print('srun [%s]'%(', '.join(runlist) ) )
    if partition  == 'echo':
        p = subprocess.Popen(['echo'] + runlist)
    elif partition in ['debug','batch']:
        p = subprocess.Popen(['srun', '-N', '1', '-pp' + partition] + runlist)
    elif partition == 'local':
        p = subprocess.Popen(runlist)
    else:
        print('Invalid execution partition ' + partition)

    return p

def progress(t, total, completed, rate, unit, start, end):
    frac = completed/total
    full_progbar = 50
    filled_progbar = round(frac * full_progbar)

    m, s = divmod(t, 60)
    h, m = divmod(m, 60)

    rate = round(rate, 2)

    if rate > 0:
        e_s = (total - completed) / rate 
        e_m, e_s = divmod(e_s, 60)
        e_h, e_m = divmod(e_m, 60)
    else:
        e_h = e_m = e_s = 0

    print('%s'%(start),'Status %5d / %5d'%(completed, total)
        , '#'*filled_progbar + '-'*(full_progbar - filled_progbar)
        , '[{:>7.2%}]'.format(frac)
        , '| %3.2f exps/%s'%(rate, unit)
        , '| Elapsed %2d:%02d:%02d' % (h, m, s)
        , '| Est. remaining %2d:%02d:%02d' % (e_h, e_m, e_s)
        , end='%s'%(end))

    sys.stdout.flush()

def get_chunk(it, chunksize):
    chunk = []
    for j in range(0, chunksize):
        e = next(it, None)
        if(e):
            chunk.append(e)
    return chunk

def run_batch(nodes, partition, nworkers, env, exps, chunksize):
    jobs = []
    it = iter(exps)
    total = len(exps)
    completed = 0
    for i in range(0, nodes):
        chunk = get_chunk(it, chunksize)
        if chunk:
            # append process and its chunksize to track progress
            jobs.append( (srun(partition, nworkers, env, chunk), len(chunk)) )
            
    t = 1
    avg_rate = 0
    last_completed = 0
    win_t = 30

    try:
        while completed < total:
            #print(jobs)
            #print('completed %s total %s'%(completed, total) )
            newjobs = []
            for p, n in jobs:
                ret = p.poll()
                #print('ret %s'%(ret) )
                if ret != None:
                    if ret != 0:
                        print('Error %s'%(ret) )
                    completed += n
                    chunk = get_chunk(it, chunksize)
                    if chunk:
                        newjobs.append( (srun(partition, nworkers, env, chunk), len(chunk)) )
                else:
                    newjobs.append( (p, n) )

            jobs = newjobs

            # per second progress printed in stdout
            if partition == 'local' or partition == 'debug':
                progress(t, total, completed, avg_rate, 's', '\r', '')
            else: # per min progress printed in file
                if t == 1 or t % 60 == 0:
                    # per min rate
                    progress(t, total, completed, avg_rate, 's', '', '\n')
                                
            time.sleep(1)

            t += 1
            if t % win_t == 0:
                avg_rate = 0.5 * ( ( completed - last_completed ) / win_t ) + 0.5 * avg_rate
                last_completed = completed
    except KeyboardInterrupt:
        for p, n in jobs:
            p.terminate()
            p.wait()
        sys.exit(1)

    progress(t, total, completed, (completed*60) / t, 'min', '', '\n')
    
    for p, n in jobs:
        ret = p.wait()
        if ret != 0:
            print( 'Error %s in job'%(ret) )


def main():
    parser = argparse.ArgumentParser('Srun new script')
    parser.add_argument('-n', '--nodes', help='number of nodes', type=int, required=True)
    parser.add_argument('-p', '--partition', help='partition to run experiments', choices=['echo', 'local', 'debug', 'batch' ], required=True)
    parser.add_argument('-w', '--workers', help='number of workers', type=int, required=True)
    parser.add_argument('-v', '--verbose', help='verbose', default=False, action='store_true') 
    parser.add_argument('-e', '--env', help='environment variables to set', nargs=2, action='append')
    parser.add_argument('-r', '--runlist', help='list to run', nargs=4, action='append', required=True)
    args = parser.parse_args()

    # Error checking
    assert args.nodes > 0, 'Nodes arg must be > 0'
    assert args.workers >= 0, 'Workers must be >= 0'

    exps = args.runlist
    #print("==== experiments ====")
    #print(exps)
    #print("==== end experiments ====")
    print('Nof exps: %d'%( len(exps) ) )
    # XXX: chunksize equals to num of local workers, coarse if too much overhead
    chunksize = args.workers
    if(exps):
        run_batch(args.nodes, args.partition, args.workers, args.env, exps, args.workers)

    print('\nExiting bye-bye')
    print('==== END EXPERIMENT ====')


if __name__ == "__main__":
    main()
