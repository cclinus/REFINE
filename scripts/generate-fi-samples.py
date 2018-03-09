#!/usr/bin/env python3.6

import os
import sys
import argparse
import re
import numpy as np
import random
from collections import Counter
from bashplotlib.histogram import plot_hist 


import data
import fi_tools

# Statistical FI
FI_N_SAMPLES = 1068

# Parse profiling data to get stats
def parse_profile(basedir, tool, config, nthreads, input_size, start, end):
    inscount = []
    thread_inscount = {}
    for i in range(0, nthreads):
        thread_inscount[i] = []
    xtime = []

    for trial in range(start, end+1):
        trialdir = '%s/%s/'%(basedir, trial)
        fname = trialdir + fi_tools.files[tool]['inscount']
        # read instruction count
        #print('fname %s'%(fname))
        with open(fname, 'r') as f:
            fdata = f.read()
            #print(data)
            if config == 'omp':
                m = re.findall('thread=(\d+), fi_index=(\d+)', fdata)
                for i in m:
                    thread_inscount[ int(i[0]) ].append( int(i[1]) )

            # XXX: ^ and re.MULTILINE to handle omp instcount (serial works too)
            m = re.search( '^fi_index=(\d+)', fdata, re.MULTILINE )
            inscount.append( int(m[1]) )
        
        # read execution time
        fname = trialdir + 'time.txt'
        with open(fname, 'r') as f:
            xtime.append( float(f.read()) )

    print( thread_inscount ) # ggout
    m_inscount = int(np.mean(inscount))
    s_inscount = np.std(inscount)
    m_thread_inscount = []
    if config == 'omp':
        for i in range( 0, nthreads ):
            m_thread_inscount.append( (i, int(np.mean( thread_inscount[i] ) )) )
    m_time = np.mean(xtime)

    # create mean_time.txt for setting the timeout
    fname = '%s/mean_time.txt'%(basedir)
    print(fname)
    with open(fname, 'w') as f:
        f.write( '%.2f\n'%(m_time) )

    return m_time, m_inscount, s_inscount, m_thread_inscount

def write_fi_files(basedir, tool, config, samples, m_thread_inscount):
    # XXX: used for omp plotting check
    fi_threads = []
    nthreads = len(m_thread_inscount)

    for trial, target in enumerate(samples, 1):
        #print('target %d'%(target)) # ggout
        trialdir = '/%s/%s/'%(basedir, trial)
        #print(trialdir)
        fname = trialdir + fi_tools.files[tool]['target']
        if not os.path.exists(trialdir):
            os.makedirs(trialdir)
        #print('fname %s'%(fname))
        if not os.path.isfile(fname):
            # XXX: need to assign thread and fi_index
            # order instructions from 0...n thread
            if config == 'omp':
                sum_inscount = 0
                # iterate over threads
                for thread, inscount in m_thread_inscount:
                    if target <= ( sum_inscount + inscount ):
                        fi_index = target - sum_inscount
                        fi_threads.append(thread)
                        break

                    sum_inscount += inscount

                print('target=%d'%(target) )
                print('thread=%d, fi_index=%d\n'%( thread, fi_index ))
                #input('press key to continue...')
                with open(fname, 'w') as f:
                    f.write('thread=%d, fi_index=%d\n'%( thread, fi_index ))
            else:
                with open(fname, 'w') as f:
                    f.write( 'fi_index=%d\n'%(target) )
    
    if fi_threads:
        print(Counter(fi_threads).keys())
        print(Counter(fi_threads).values())
        plot_hist(fi_threads, title='Thread distro', bincount=100, xlab=True)

def main():
    parser = argparse.ArgumentParser('Generate FI samples')
    parser.add_argument('-r', '--resdir', help='results directory', required=True)
    parser.add_argument('-t', '--tool', help='tool to run', choices=['refine', 'pinfi', 'refine-noff'], required=True)
    parser.add_argument('-a', '--apps', help='applications to run ( ' + ' | '.join(data.apps) + ' | ALL ) ', nargs='+', required=True)
    parser.add_argument('-c', '--config', help='execution configuration ( serial | omp <nthreads>)', nargs='+', required=True)
    parser.add_argument('-i', '--input', help='input size', choices=['test', 'small', 'large'], required=True)
    parser.add_argument('-s', '--start', help='start trial', type=int, required=True)
    parser.add_argument('-e', '--end', help='end trial', type=int, required=True)
    args = parser.parse_args()

    # Error checking
    assert os.path.isdir(args.resdir), 'Results directory: ' + args.resdir + 'does not exist'
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
        nthreads = int(args.config[1])
        assert nthreads > 0
    else: 
        assert len(args.config) == 1, 'Configuration serial has no arguments'
        nthreads = 0

    rootdir = '%s/%s/%s/'%(args.resdir, args.tool, config)
    # Generate random samples and fi files
    for app in args.apps:
        if config == 'omp':
            profiledir = '%s/%s/profile/%s/%s/'%(rootdir, app, nthreads, args.input)
        else:
            profiledir = '%s/%s/profile/%s/'%(rootdir, app, args.input)

        m_time, m_inscount, s_inscount, m_thread_inscount = parse_profile(profiledir, args.tool, config, int(nthreads), args.input, args.start, args.end)
        print('mean inst. per thread')
        print(m_thread_inscount)
        print('mean inscount %d std %d'%(m_inscount, s_inscount) )
        print('mean time %.2f'%(m_time) )

        # create fi samples
        samples = random.sample(range(1, m_inscount+1), FI_N_SAMPLES)

        # XXX replace profle -> fi
        resultdir = profiledir.replace('profile', 'fi')
        
        write_fi_files(resultdir, args.tool, config, samples, m_thread_inscount)

        samples = [n/m_inscount for n in samples]
        plot_hist(samples, title='Target distro', bincount=100, xlab=True)

if __name__ == "__main__":
    main()
