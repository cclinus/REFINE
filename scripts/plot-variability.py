#!/usr/bin/env python3.6

import matplotlib.pyplot as plt
import os
import sys
import argparse
import re
import numpy as np
import scipy.stats as stats
import random


import data
import fi_tools

# Parse profiling data to get stats
def parse_profile(basedir, tool, config, nthreads, input_size, start, end):
    inscount = []
    if config == 'omp':
        thread_inscount = {}
        for i in range(0, int(nthreads) ):
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

    m_inscount = int(np.mean(inscount))

    ci = 0.95
    t_critical = stats.t.ppf( q = (1 + ci) /2., df = end-start )
    err_m_inscount = stats.sem(inscount) * t_critical
    #stats.t.interval(0.95, end-start, loc=m_inscount, scale=stats.sem(inscount))
    m_thread_inscount = []
    if config == 'omp':
        #print( thread_inscount ) # ggout
        for i in range( 0, int(nthreads) ):
            m_thread_inscount.append( (i, int(np.mean( thread_inscount[i] ) )) )
    m_time = np.mean(xtime)

    return m_time, m_inscount, err_m_inscount, m_thread_inscount

def main():
    parser = argparse.ArgumentParser('Plot variability')
    parser.add_argument('-r', '--resdir', help='results directory', required=True)
    parser.add_argument('-t', '--tools', help='tool to run', choices=['refine', 'pinfi', 'golden', 'refine-noff'], nargs='+', required=True)
    args = parser.parse_args()

    config = [ 'serial', 'omp' ]
    config = [ 'omp' ] # ggout
    espace = {
            'serial': {
                'inputs':[ 'small' ],
                'instrument': [''],
                'small' : { 'nthreads' : [''] }
                },
            'omp': {
                'inputs':[ 'small', 'large' ],
                'instrument': ['all', 'app', 'omplib'],
                #'small' : { 'nthreads' : [ '16', '8', '1' ] },
                'small' : { 'nthreads' : [ '16' ] },
                #'large' : { 'nthreads' : [ '16', '8' ] },
                'large' : { 'nthreads' : [ '16' ] }
                }
            }
    for c in config:
        for i in espace[c]['inputs']:
            for n in espace[c][i]['nthreads']:
                for ins in espace[c]['instrument']:
                    for app in data.apps:
                        m_inscount_list = []
                        err_inscount_list = []
                        for t in args.tools:
                            profiledir = '%s/%s/%s/%s/%s/%s/%s/%s'%(args.resdir, t, c, app, 'profile', ins, n, i)
                            # TODO replace 1-16 args.ps-pe
                            m_time, m_inscount, err_m_inscount, m_thread_inscount = parse_profile(profiledir, t, c, n, i, 1, 16)
                            print( '%s %s %s %s %s %s m m_inscount %d err_m_inscount %.2f pct %.2f%%'%(app, t, t, c, n, ins, m_inscount, err_m_inscount, 100*err_m_inscount/m_inscount))
                            m_inscount_list.append( m_inscount )
                            err_inscount_list.append( err_m_inscount )

                        print(m_inscount_list)
                        print(err_inscount_list)
                        plt.title( 'Mean instruction count' )
                        plt.bar(range( 0, len(args.tools) ), m_inscount_list, yerr=err_inscount_list, tick_label=args.tools, capsize=8)
                        plt.savefig('%s-%s-%s-%s-%s.eps'%(app, i, c, n, ins) )
                        plt.close()
                        
if __name__ == "__main__":
    main()
