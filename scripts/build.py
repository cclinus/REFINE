#!/usr/bin/env python

import subprocess
import timeit
import sys
import data
import fi_tools
import argparse
import os
import numpy as np

def make(workdir, args):
    out = open('compile-out.txt', 'w')
    err = open('compile-err.txt', 'w')
    p = subprocess.Popen(['make'] + args, stdout = out, stderr = err, cwd = workdir)
    p.wait()
    if p.returncode == 0:
        print('make succeeded')
    else:
        print('make failed!')
        sys.exit(p.returncode)

def clean(workdir):
    p = subprocess.Popen(['make', 'clean'], cwd = workdir, stdout = None)
    p.wait()
    if p.returncode == 0:
        print('make clean succeeded')
    else:
        print('make clean failed!')
        sys.exit(p.returncode)

def build(action, repeat, workdir, args):
    if action == 'clean':
        clean(workdir)
    elif action == 'build':
        make(workdir, args)
    elif action == 'profile':
        clean(workdir)
        times = []
        for r in range(1,repeat+1):
            t = timeit.timeit(lambda: make(workdir, args), number = 1)
            times.append(t)
            with open(workdir+'compile-time-' + str(r) + '.txt', 'w') as f:
                f.write('%.2f'%(t) + '\n')
            clean(workdir)
        with open(workdir+'mean-compile-time.txt', 'w') as f:
            f.write('%.2f'%(np.mean(times)) + '\n')

tools = ['golden', 'pinfi', 'refine']

configs = {
'golden' : [ 'serial', 'omp' ],
'pinfi'  : [ 'serial', 'omp' ],
'refine' : [ 'serial-noff', 'serial', 'omp' ]
}

parser = argparse.ArgumentParser('Build applications for tools and their configurations')
# tuple of 3: (tool, app, iter)
parser.add_argument('-d', '--appdir', help='application directory', required=True)
parser.add_argument('-a', '--apps', help='applications to build ( ' + ' | '.join(data.apps) + ' | ALL ) ', nargs='+', required=True)
parser.add_argument('-t', '--tool', help='tool to build (golden | pinfi | refine)', required=True)
parser.add_argument('-c', '--configs', help='configuration to build (serial | omp | serial-noff (refine-only) )', nargs='+', required=True)
parser.add_argument('-o', '--action', help='action (build | clean | profile)', required=True)
parser.add_argument('-r', '--repeat', help='repeat build action (to profile compiling times)', type=int, default=1)
args = parser.parse_args()

assert os.path.isdir(args.appdir), 'Application directory: ' + args.appdir + 'does not exist'
for a in args.apps:
    assert a in data.apps or a == 'ALL', 'Application: ' + a + 'is invalid'
if args.apps == 'ALL':
    args.apps = data.apps
assert args.tool in tools, 'Tool: ' + args.tool + 'is invalid'
for c in args.configs:
    assert c in configs[args.tool], 'Config ' + c + ' is invalid for tool ' + args.tool
assert args.action in ['build', 'clean', 'profile'], 'Action: ' + args.action + 'is invalid'
assert args.repeat >=1, 'Repeat: ' + args.repeat+ 'is invalid'

for c in args.configs:
    for a in args.apps:
        print('%s %s %s'%(args.tool,c,a))
        workdir = args.appdir+'/'+args.tool+'/'+c+'/'+data.dirs[c][a]['build']['dir']
        build_args = data.dirs[c][a]['build']['args']
        print('Build dir: '+workdir+' '+' '.join(build_args))

        build(args.action, args.repeat, workdir, build_args)
        sys.exit(1)




