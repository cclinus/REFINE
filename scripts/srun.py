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

parser = argparse.ArgumentParser('Srun old script')
parser.add_argument('-d', '--appdir', help='applications root directory', required=True)
parser.add_argument('-r', '--resdir', help='results directory', required=True)
parser.add_argument('-n', '--nodes', help='number of nodes', type=int, required=True)
parser.add_argument('-p', '--partition', help='partition to run experiments', choices=['echo', 'local', 'debug', 'batch' ], required=True)
parser.add_argument('-w', '--workers', help='number of workers', type=int, required=True)
parser.add_argument('-t', '--tool', help='tool to run', choices=['refine', 'pinfi', 'golden', 'refine-noff'], required=True)
parser.add_argument('-x', '--action', help='action to take', choices=['profile', 'fi'], required=True)
parser.add_argument('-a', '--apps', help='applications to run ( ' + ' | '.join(data.apps) + ' | ALL ) ', nargs='+', required=True)
parser.add_argument('-c', '--config', help='run configuration \n <serial | omp> <nthreads> [all | app | omplib])', nargs='+', required=True)
parser.add_argument('-i', '--input', help='input size', choices=data.inputs, required=True)
parser.add_argument('-s', '--start', help='start trial', type=int, required=True)
parser.add_argument('-e', '--end', help='end trial', type=int, required=True)
parser.add_argument('-v', '--verbose', help='verbose', default=False, action='store_true') 
args = parser.parse_args()

# Error checking
assert os.path.isdir(args.appdir), 'Applications directory: ' + args.appdir + 'does not exist'
assert args.nodes > 0, 'Nodes arg must be > 0'
assert args.workers >= 0, 'Workers must be >= 0'
assert not (args.tool == 'golden' and args.action == 'fi'), 'Cannot fi with tool golden'
if args.apps == ['ALL']:
    args.apps = data.apps
else:
    for a in args.apps:
        assert a in data.apps, 'Application: ' + a + ' is invalid'
assert args.start <= args.end, 'Start must be < end'
assert args.config[0] in ['serial', 'omp']
config = args.config[0]
if config == 'omp':
    if args.tool == 'golden':
        assert len(args.config) == 2, 'Golden config: omp <nthreads>'
        nthreads = args.config[1]
        assert int(nthreads) > 0, 'nthreads must be > 0'
        instrument=''
    else: # refine or pinfi
        assert len(args.config) == 3, 'Config: omp <nthreads> <all | app | omplib>'
        nthreads = args.config[1]
        instrument = args.config[2]
        assert int(nthreads) > 0, 'nthreads must be > 0'
        assert instrument in ['all', 'app', 'omplib']
else: # serial
    assert len(args.config) == 1, 'Serial config has no other argument'
    nthreads = ''
    instrument = ''

def srun(chunk):
    runargs = []
    ## Setup the env
    if config == 'omp':
        runargs += [ '-e', 'OMP_NUM_THREADS', nthreads ]
        if int(nthreads) > 1:
            runargs += [ '-e', 'KMP_AFFINITY' , 'compact' ]
    if args.tool == 'refine':
        if instrument == 'all' or instrument == 'omplib':
            runargs += [ '-e', 'LD_LIBRARY_PATH', homedir + '/usr/local/refine/lib:' + homedir + '/usr/local/lib' ]

    for i in chunk:
        runargs += i
    runlist=['./run.py'] + ['-w', str(args.workers)] + runargs
    print(runlist)
    sys.exit(124)
    if args.partition  == 'echo':
        p = subprocess.Popen(['echo'] + runlist)
    elif args.partition in ['debug','batch']:
        p = subprocess.Popen(['srun', '-N', '1', '-pp' + args.partition] + runlist)
    elif args.partition == 'local':
        p = subprocess.Popen(runlist)
    else:
        print('Invalid execution partition ' + args.partition)

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

def get_chunk(it, chunksize):
    chunk = []
    for j in range(0, chunksize):
        e = next(it, None)
        if(e):
            chunk.append(e)
    return chunk

def run_batch(exps, chunksize):
    jobs = []
    it = iter(exps)
    total = len(exps)
    completed = 0
    for i in range(0, args.nodes):
        chunk = get_chunk(it, chunksize)
        if chunk:
            # append process and its chunksize to track progress
            jobs.append( (srun(chunk), len(chunk)) )
            
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
                        newjobs.append( (srun(chunk), len(chunk)) )
                else:
                    newjobs.append( (p, n) )

            jobs = newjobs

            # per second progress printed in stdout
            if args.partition == 'local' or args.partition == 'debug':
                progress(t, total, completed, avg_rate, 's', '\r', '')
            else: # per min progress printed in file
                if t == 1 or t % 60 == 0:
                    # per min rate
                    progress(t, total, completed, avg_rate*60, 'min', '', '\n')
                                
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
    
    with open('%s-%s-%s-%s-%s-%s.txt'%(args.tool, config, args.action, instrument, nthreads, args.input), 'w') as f:
        f.write(str(t) + ' seconds\n')
    
    for p, n in jobs:
        ret = p.wait()
        if ret != 0:
            print( 'Error %s in job'%(ret) )

print('==== EXPERIMENT ====')
print( 'Experiment: %s %s %s %s %s %s %s %s %s'%( args.tool, config, ' '.join(args.apps), args.action, instrument, nthreads, args.input, args.start, args.end) )
# Create fault injection experiment tuples
exps = []
for app in args.apps:
    basedir = '%s/%s/%s/%s/%s/%s/%s/%s/'%(args.resdir, args.tool, config, app, args.action, instrument, nthreads, args.input)
    
    if args.action == 'fi':
        # get timeout
        profiledir = '%s/%s/%s/%s/%s/%s/%s/%s'%(args.resdir, args.tool, config, app, 'profile', instrument, nthreads, args.input)
        fname = '/%s/mean_time.txt'%(profiledir)
        with open(fname, 'r') as f:
            timeout = float( f.read() )
        # XXX: PINFI instruction counts BB, but faultinjections is INS! Use a large timeout
        #print('Read mean profiling time: %.2f, setting timeout 20x:  %.2f'%(timeout, timeout*20) )
        timeout = round(20 * timeout, 2)

    for trial in range(args.start, args.end+1):
        trialdir = basedir + '/' + str(trial) +'/'
        #print(trialdir)
        # Skip already done experiments
        #print('CHECK to skip %s/ret.txt'%(trialdir) )
        if os.path.isfile(trialdir+'/ret.txt'):
            continue

        if args.action == 'profile':
            # create trialdir
            if not os.path.exists(trialdir):
                os.makedirs(trialdir)
            timeout = 0
        elif args.action == 'fi':
            assert os.path.exists(trialdir), 'Trialdir %s does not exist, forgot to run generate-fi-samples?'%(trialdir)
            #assert not os.path.isfile(trialdir + '/'+ fi_tools.files[args.tool]['injection']),\
            #'Reproducible injection is not supported: ' + trialdir + '/' + fi_tools.files[args.tool]['injection']
            if os.path.isfile(trialdir + '/'+ fi_tools.files[args.tool]['injection']):
                print('WARNING: Reproducible injection is not supported, deleting old injection file')
                os.remove(trialdir + '/'+ fi_tools.files[args.tool]['injection'])
        else:
            assert False, 'Invalid action:' + args.action

        # Create executable
        ## Find the program binary to run
        if args.tool == 'pinfi' or args.tool == 'golden':
            compiled = 'golden'
        elif args.tool == 'refine':
            if instrument == 'omplib':
                compiled = 'golden'
            else:
                compiled = 'refine'
        else:
            print('Unknown tool' + args.tool)
            sys.exit(1)
        rootdir = '%s/%s/%s/'%(args.appdir, compiled, config)

        ## Build the exelist
        ### Any tool specific exelist header
        fi_exelist=[]
        if args.tool in fi_tools.exelist:
            if config == 'serial':
                fi_exelist = fi_tools.exelist[args.tool][config][args.action]
            else:
                fi_exelist = fi_tools.exelist[args.tool][config][args.action][instrument]
        #print(fi_exelist)

        ### Patch APPDIR and NTHREADS if needed
        # XXX: replace $APPDIR, needed only for CoMD
        exelist = [ s.replace( '$APPDIR', '%s/%s'%(rootdir, app) ) for s in data.programs[config][app]['exec'][args.input] ]
        # XXX: replace NTHREADS, needed only for XSBench omp
        exelist = [ s.replace( '$NTHREADS', nthreads ) for s in exelist ]
        # XXX: note using rootdir, program binary is relative to that
        exelist = fi_exelist + [ rootdir + exelist[0] ] + exelist[1:]
        exelist = ' '.join(exelist)
        #print('\nexelist< %s >\n'%(exelist))
        # XXX: add cleanup to avoid disk space problems
        cleanlist = data.programs[config][app]['clean']

        ## Append to experiments (must be string list)
        exps.append( ['-r', trialdir, str(timeout), exelist, cleanlist] )
        if args.verbose:
            print(['-r', trialdir, str(timeout), exelist])
        #sys.exit(123)
print("==== experiments ====")
print(exps)
print("==== end experiments ====") # ggout
print('Nof exps: %d'%( len(exps) ) )
if(exps):
    run_batch(exps, args.workers)

print('\nExiting bye-bye')
print('==== END EXPERIMENT ====')

