#!/usr/bin/env python3

import argparse
import subprocess
import data
import os
import re
import fi_tools

def results(resdir, tool, config, app, action, instrument, nthreads, inputsize, start, end, verbose):
    print('===== APP %s %s %s %s %s %s %s %s %s  ====='%(app, tool, config, action, instrument, nthreads, inputsize, start, end) )
    missing = timeout = crash = soc = benign = 0
    # base app dir
    rootdir = '%s/%s/%s/'%(resdir, 'golden', config)
    # specific trial dir
    profiledir = '%s/%s/profile/%s/%s/'%(rootdir, app, nthreads, inputsize )

    # Use the first experiment on golden to get the valid output
    # TODO: check whether outputs with omp may differ but still valid
    trialdir = profiledir + '1/'

    verify_list = []
    with open(trialdir + 'output.txt', 'r') as f:
        for v in data.programs[config][app]['verify'][inputsize]:
            #print(v)
            m = re.findall(v, f.read())
            verify_list += m
    #print(verify_list)
    assert verify_list, 'verify_list cannot be empty file: ' + trialdir + 'output.txt' + ', verify:' + ' '.join(data.programs[config][app]['verify'][inputsize])

    # XXX: replacements
    basedir = '%s/%s/%s/%s/%s/%s/%s/%s/'%(resdir, tool, config, app, action, instrument, nthreads, inputsize)

    for trial in range(start, end+1):
        trialdir = '%s/%s/'%( basedir, trial )
        with open(trialdir + 'ret.txt', 'r') as retf:
            if not os.path.isfile(trialdir + fi_tools.files[tool]['injection']):
                missing += 1
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
                    #print('open: ' + trialdir +'/' + 'output.txt')
                    verify_out = []
                    for v in data.programs[config][app]['verify'][inputsize]:
                        m = re.findall(v, f.read())
                        verify_out += m
                    verified = True
                    for out in verify_list:
                        if not out in verify_out:
                            verified = False
                            break
                    if verbose:
                        print('*** verify ***')
                        print(verify_list)
                        print(verify_out)
                        print('trial %d verified: %s'%(trial, verified))
                        print('*** end verify ***')
                    if verified:
                        benign += 1
                    else:
                        soc += 1
                        #TODO: extend verifier with tolerance
                    #print('\ttimeout: ' + str(timeout) + ', crash: ' + str(crash) + ', soc: ' + str(soc) + ', benign: ' + str(benign))
            else:
                print('Invalid result ' + tool + ' ' + app + ' ' + str(trial) +' :' + str(res[0]))

    print('\tmissing: ' + str(missing) + ', timeout: ' + str(timeout) + ', crash: ' + str(crash) + ', soc: ' + str(soc) + ', benign: ' + str(benign))
    total = end - start + 1
    print('\t(%%) timeout %3.2f, crash %3.2f, soc %3.2f, benign %3.2f'%(timeout*100.0/total, crash*100.0/total, soc*100.0/total, benign*100.0/total) )
    print('===== END APP ' + app +' =====\n');
    if config == 'serial':
        with open('results-%s-%s-serial-%s-%s-%s.txt'%( app, tool, inputsize, start, end), 'w' ) as f:
            f.write('missing: %d\n'%(missing) )
            f.write('timeout: %d\n'%(timeout) )
            f.write('crash: %d\n'%( crash ) )
            f.write('soc: %d\n'%( soc ) )
            f.write('benign: %d\n'%( benign ) )
    else: # omp
        with open('results-%s-%s-omp-%s-%s-%s-%s-%s.txt'%( app, tool, inputsize, nthreads, instrument, start, end), 'w') as f:
            f.write('missing: %d\n'%(missing) )
            f.write('timeout: %d\n'%(timeout) )
            f.write('crash: %d\n'%( crash ) )
            f.write('soc: %d\n'%( soc ) )
            f.write('benign: %d\n'%( benign ) )

def main():
    parser = argparse.ArgumentParser('Run profiling experiments')
    parser.add_argument('-r', '--resdir', help='results directory', required=True)
    parser.add_argument('-a', '--apps', help='applications to run', choices=data.apps+['ALL'], nargs='+', required=True)
    parser.add_argument('-t', '--tools', help='tool to run', choices=['refine', 'pinfi', 'refine-noff'], nargs='+', required=True)
    parser.add_argument('-x', '--action', help='results for action', choices=['profile', 'fi'], required=True)
    parser.add_argument('-s', '--start', help='start trial', type=int, required=True)
    parser.add_argument('-e', '--end', help='end trial', type=int, required=True)
    args = parser.parse_args()

    # Error checking
    assert os.path.isdir(args.resdir), 'Applications directory: ' + args.resdir + 'does not exist'
    assert args.start <= args.end, 'Start must be < end'
    if args.apps == ['ALL']:
        args.apps = data.apps

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

    #def check(tool, config, apps, action, instrument, nthreads, inputsize, start, end)
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

                            if not os.path.isfile(fname):
                                #def result(resdir, tool, config, app, action, instrument, nthreads, inputsize, start, end, verbose)
                                results(args.resdir, t, c, a, args.action, ins, n, i, args.start, args.end, False)

if __name__ == "__main__":
    main()
