#!/usr/bin/env python3

import os
import sys
import data
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import argparse

parser = argparse.ArgumentParser('This script creates outcome plots')
parser.add_argument('-r', '--resdir', help='results directory', required=True)
parser.add_argument('-a', '--apps', help='applications to run', choices=data.apps+['ALL'], nargs='+', required=True)
parser.add_argument('-t', '--tools', help='tool to run', choices=['refine', 'pinfi', 'refine-noff'], nargs='+', required=True)
parser.add_argument('-s', '--start', help='start trial', type=int, required=True)
parser.add_argument('-e', '--end', help='end trial', type=int, required=True)
args = parser.parse_args()

print('Generating plots...')

config = [ 'serial', 'omp' ]
espace = {
        'serial': {
            'inputs':[ 'small' ],
            'instrument': [''],
            'small' : { 'nthreads' : [''] }
            },
        'omp': {
            'inputs':[ 'small', 'large' ],
            'instrument': ['all', 'app', 'omplib'],
            'small' : { 'nthreads' : [ '16', '8', '1' ] },
            'large' : { 'nthreads' : [ '16', '8' ] },
            }
        }

print('Creating plots...')
for t in args.tools:
        for a in args.apps:
            for c in config:
                for i in espace[c]['inputs']:
                    for n in espace[c][i]['nthreads']:
                        for ins in espace[c]['instrument']:
                            if c == 'serial':
                                fname ='results-%s-%s-serial-%s-%s-%s.txt'%( a, t, i, args.start, args.end)
                            else: #omp
                                fname = 'results-%s-%s-omp-%s-%s-%s-%s-%s.txt'%( a, t, i, n, ins, args.start, args.end)

                            y = []
                            with open(fname, 'r') as f:
                                missing = int(f.readline().rstrip().split(':')[1])
                                y.append( missing )
                                timeout = int(f.readline().rstrip().split(':')[1])
                                y.append( timeout )
                                crash = int(f.readline().rstrip().split(':')[1])
                                y.append( crash )
                                soc = int(f.readline().rstrip().split(':')[1])
                                y.append( soc )
                                benign = int(f.readline().rstrip().split(':')[1])
                                y.append( benign )

                            plt.title( fname.replace('.txt', '').replace('results-', '') )
                            plt.bar(range(0, len(y)), y, label=['missing', 'timeout', 'crash', 'soc', 'benign'] )
                            plt.savefig( fname.replace('txt', 'eps') )
                            plt.close()



