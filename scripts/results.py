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

parser = argparse.ArgumentParser('Run profiling experiments')
parser.add_argument('-r', '--resdir', help='results directory', required=True)
parser.add_argument('-t', '--tool', help='tool to run', choices=['refine', 'pinfi', 'golden', 'refine-noff'], required=True)
parser.add_argument('-c', '--config', help='execution configuration ( serial | omp <nthreads>)', nargs='+', required=True)
parser.add_argument('-a', '--apps', help='applications to run ( ' + ' | '.join(data.apps) + ' | ALL ) ', nargs='+', required=True)
parser.add_argument('-i', '--input', help='input size', choices=data.inputs, required=True)
parser.add_argument('-s', '--start', help='start trial', type=int, required=True)
parser.add_argument('-e', '--end', help='end trial', type=int, required=True)
args = parser.parse_args()

# Error checking
assert os.path.isdir(args.resdir), 'Results directory: ' + args.resdir + 'does not exist'
for a in args.apps:
    assert a in data.apps or a == 'ALL', 'Application: ' + a + ' is invalid'
if args.apps == ['ALL']:
    args.apps = data.apps
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

for app in args.apps:
    print('app:'+app)
    timeout = crash = soc = benign = 0
    # base app dir
    rootdir = '%s/%s/%s/'%(args.resdir, 'golden', config)
    # specific trial dir
    if config == 'omp':
        profiledir = '%s/%s/profile/%s/%s/'%(rootdir, app, nthreads, args.input)
    else:
        profiledir = '%s/%s/profile/%s/'%(rootdir, app, args.input)

    # Use the first experiment on golden to get the valid output
    # TODO: check whether outputs with omp may differ but still valid
    trialdir = profiledir + '1/'

    verify_list = []
    with open(trialdir + 'output.txt', 'r') as f:
        for v in data.programs[config][app]['verify'][args.input]:
            #print(v)
            m = re.findall(v, f.read())
            verify_list += m
    #print(verify_list)
    assert verify_list, 'verify_list cannot be empty'

    # XXX: replacements
    fidir = profiledir.replace('golden', args.tool).replace('profile', 'fi')

    for trial in range(args.start, args.end+1):
        trialdir = '%s/%s/'%( fidir, trial )
        # XXX: hack for golden to check output validity
        if args.tool == 'golden':
            trialdir = trialdir.replace('fi', 'profile')
        with open(trialdir + 'ret.txt', 'r') as retf:
            res = retf.read()
            res = res.strip().split(',')
            if res[0] == 'timeout':
                timeout += 1
            elif res[0] == 'crash':
                crash += 1
            elif res[0] == 'error':
                crash += 1
            elif res[0] == 'exit':
                with open(trialdir + '/' + 'output.txt', 'r') as f:
                    verify_out = []
                    for v in data.programs[config][app]['verify'][args.input]:
                        m = re.findall(v, f.read())
                        verify_out += m
                    verified = True
                    for out in verify_list:
                        if not out in verify_out:
                            verified = False
                            break
                    print('=== verify ===')
                    print(verify_list)
                    print(verify_out) # ggout
                    print('=== end verify ===')
                    print('trial %d verified: %s'%(trial, verified)) # ggout
                    if verified:
                        benign += 1
                    else:
                        soc += 1
                    #print('\ttimeout: ' + str(timeout) + ', crash: ' + str(crash) + ', soc: ' + str(soc) + ', benign: ' + str(benign))
            else:
                print('Invalid result ' + args.tool + ' ' + app + ' ' + str(trial) +' :' + str(res[0]))

    print('\ttimeout: ' + str(timeout) + ', crash: ' + str(crash) + ', soc: ' + str(soc) + ', benign: ' + str(benign))
    total = args.end - args.start + 1
    print('\t(%%) timeout %3.2f, crash %3.2f, soc %3.2f, benign %3.2f'%(timeout*100.0/total, crash*100.0/total, soc*100.0/total, benign*100.0/total) )
