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
    pinroot = os.environ['PIN_ROOT']
except:
    print('Env variable PIN_ROOT is missing')
    sys.exit(1)

try:
    pinfidir = os.environ['PINFI']
except:
    print('Env variable PINFI is missing')
    sys.exit(1)

pinbin = pinroot + 'pin'

parser = argparse.ArgumentParser('Run profiling experiments')
parser.add_argument('-d', '--appdir', help='applications root directory', required=True)
parser.add_argument('-r', '--resdir', help='results directory', required=True)
parser.add_argument('-n', '--nodes', help='number of nodes', type=int, required=True)
parser.add_argument('-p', '--partition', help='partition to run experiments', choices=['echo', 'local', 'debug', 'batch' ], required=True)
parser.add_argument('-w', '--workers', help='number of workers', type=int, required=True)
parser.add_argument('-t', '--tool', help='tool to run', choices=['refine', 'pinfi', 'golden', 'refine-noff'], required=True)
parser.add_argument('-x', '--action', help='action to take', choices=['profile', 'fi'], required=True)
parser.add_argument('-a', '--apps', help='applications to run ( ' + ' | '.join(data.apps) + ' | ALL ) ', nargs='+', required=True)
parser.add_argument('-c', '--config', help='execution configuration ( serial | omp <nthreads>)', nargs='+', required=True)
parser.add_argument('-i', '--input', help='input size', choices=data.inputs, required=True)
parser.add_argument('-s', '--start', help='start trial', type=int, required=True)
parser.add_argument('-e', '--end', help='end trial', type=int, required=True)
args = parser.parse_args()

# Error checking
assert os.path.isdir(args.appdir), 'Applications directory: ' + args.appdir + 'does not exist'
assert args.nodes > 0, 'Nodes arg must be > 0'
assert args.workers >= 0, 'Workers muse be >= 0'
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
    assert len(args.config) == 2, 'Missing nthreads for omp config?'
    nthreads = args.config[1]
    assert int(nthreads) > 0
else: 
    assert len(args.config) == 1, 'Configuration serial has no arguments'
    nthreads = ''

def chunkify(lst, n):
    # Break in n chunks
    chunks = [ lst[i::n] for i in range(n)]
    # Return cleaned-up from empty sub-chunks
    return [c for c in chunks if c]

def run_batch(exps):
    jobs = []
    batches = chunkify(exps, args.nodes)
    for i, batch in enumerate(batches, 1):
        # Flatten batch to pass as argument
        runargs = [j for b in batch for j in b]
        #print("==== runargs ===")
        #print(runargs)
        #print("==== end runargs ====")
        # Create unique job id for workers to update progress
        jobid = '%d.%d'%(os.getpid(), i)
        print('jobid ' + jobid) # ggout
        # Touch file
        with open(jobid + '.log', 'w') as f:
            f.write('0\n')
        runlist=['./run.py'] + ['-j', jobid, '-w', str(args.workers)] + runargs
        #print(runlist)

        if args.partition  == 'echo':
            p = subprocess.Popen(['echo'] + runlist)
        elif args.partition in ['debug','batch']:
            if args.partition == 'debug':
                p = subprocess.Popen(['srun', '-N', '1', '-pp' + args.partition] + runlist)
            else:
                outf = open('srun-' + args.tool + '-' + str(args.start) + '-' + str(args.end) + '-' + str(i) + '.out', 'w')
                errf = open('srun-' + args.tool + '-' + str(args.start) + '-' + str(args.end) + '-' + str(i) + '.err', 'w')
                p = subprocess.Popen(['srun', '-N', '1', '-pp' + args.partition] + runlist, stdout = outf, stderr = errf)
        elif args.partition == 'local':
            p = subprocess.Popen(runlist)
        else:
            print('Invalid execution partition ' + args.partition)
        jobs.append({'tool':args.tool, 'range': str(args.start) + '-' + str(args.end), 'proc': p, 'jobid':jobid})

    try:
        # Keeps time
        t = 1
        while True:
            completed = 0
            total = len(exps)
            for j in jobs:
                #if j['proc'].wait() != 0:
                #    print('Error in process: ' + j['tool'] + ', range: ' + j['range'] +', ret: ' + str(j['proc'].returncode))
                try:
                    with open(j['jobid']+'.log', 'r') as f:
                        completed += int( f.read() )
                # ignore concurrent write problems
                except ValueError:
                    continue
            #print('completed %d total %d'%(completed, total) )
            frac = completed/total
            full_progbar = 50
            filled_progbar = round(frac * full_progbar)
            rate = round(completed/t, 2)

            m, s = divmod(t, 60)
            h, m = divmod(m, 60)

            if rate > 0:
                e_s = (total - completed) / rate 
                e_m, e_s = divmod(e_s, 60)
                e_h, e_m = divmod(e_m, 60)
            else:
                e_h = e_m = e_s = 0

            print('\r','Status %4d / %4d'%(completed, total)
                    , '#'*filled_progbar + '-'*(full_progbar - filled_progbar)
                    , '[{:>7.2%}]'.format(frac)
                    , '| %2.2f exps/s'%(rate)
                    , '| Elapsed time %2d:%02d:%02d' % (h, m, s)
                    , '| Est. remaining time %3d:%02d:%02d' % (e_h, e_m, e_s)
                    , end='')
            if completed >= total:
                break
            time.sleep(1)
            t += 1
    except KeyboardInterrupt:
        for j in jobs:
            j['proc'].terminate()
    
    print('\nRemoving log files...')
    # Remove log files
    for j in jobs:
        os.remove(j['jobid']+'.log')

# Create fault injection experiment tuples
exps = []
for app in args.apps:
    for trial in range(args.start, args.end+1):
        print('Experiment: %s %s %s %s %s %s %s'%( args.tool, config, app, args.action, nthreads, args.input, trial ))
        trialdir = '%s/%s/%s/%s/%s/%s/%s/%s/'%(args.resdir, args.tool, config, app, args.action, nthreads, args.input, trial)

        print(trialdir)
        # Skip already done experiments
        if os.path.isfile(trialdir+'ret.txt'):
            print('Skip: %s %s %s %s %s %s %s'%( args.tool, config, app, args.action, nthreads, args.input, trial ))
            continue

        if args.action == 'profile':
            # create trialdir
            if not os.path.exists(trialdir):
                os.makedirs(trialdir)
            timeout = 0
        elif args.action == 'fi':
            assert os.path.exists(trialdir), 'Trialdir %s does not exist, forgot to run generate-fi-samples?'%(trialdir)
            # get timeout
            profiledir = '%s/%s/%s/%s/%s/%s/%s/'%(args.resdir, args.tool, config, app, 'profile', nthreads, args.input)
            fname = '/%s/mean_time.txt'%(profiledir)
            with open(fname, 'r') as f:
                timeout = float( f.read() )
            # XXX: PINFI instruction counts BB, but faultinjections is INS! Use a large timeout
            print('Read mean profiling time: %.2f, setting timeout 20x:  %.2f'%(timeout, timeout*20) )
            timeout = round(20 * timeout, 2)
        else:
            assert False, 'Invalid action:' + args.action

        if args.tool == 'pinfi' or args.tool == 'golden':
            compiled = 'golden'
        elif args.tool == 'refine':
            compiled = 'refine'
        else:
            print('Unknown tool' + args.tool)
            sys.exit(1)
        rootdir = '%s/%s/%s/'%(args.appdir, compiled, config)
        # XXX: replace $APPDIR, needed only for CoMD
        exelist = [ s.replace( '$APPDIR', '%s/%s'%(rootdir, app) ) for s in data.programs[config][app]['exec'][args.input] ]
        # XXX: replace NTHREADS, needed only for XSBench
        exelist = [ s.replace( '$NTHREADS', nthreads ) for s in exelist ]

        # XXX: note using rootdir, program binary in data is relative to that
        exelist = fi_tools.exelist[args.tool][config][args.action] + [ rootdir + exelist[0] ] + exelist[1:]
        exelist = ' '.join(exelist)
        print('exelist< %s >'%(exelist))
        if nthreads:
            exps.append(['-e', 'OMP_NUM_THREADS', nthreads, '-r', trialdir, str(timeout), exelist])
        else:
            exps.append(['-r', trialdir, str(timeout), exelist])

#print("==== experiments ====")
#print(exps)
#print("==== end experimetns ====")
print("Nof exps:", end='')
print(len(exps))
if(exps):
    run_batch(exps)

print('\nExiting bye-bye')

