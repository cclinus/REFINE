#!/usr/bin/env python3.6

import data
import argparse
import os
import fi_tools
import sys

try:
    homedir = os.environ['HOME']
except:
    print('Env variable HOME is missing')
    sys.exit(1)

def check(appdir, resdir, tool, config, apps, action, instrument, nthreads, inputsize, start, end):
    tota= 0
    exps=[]
    # Create fault injection experiment tuples
    for app in apps:
        basedir = '%s/%s/%s/%s/%s/%s/%s/%s/'%(resdir, tool, config, app, action, instrument, nthreads, inputsize)
        if action == 'fi':
            # get timeout
            profiledir = '%s/%s/%s/%s/%s/%s/%s/%s'%(resdir, tool, config, app, 'profile', instrument, nthreads, inputsize)
            fname = '/%s/mean_time.txt'%(profiledir)
            with open(fname, 'r') as f:
                proftime = float( f.read() )
            # XXX: PINFI instruction counts BB, but faultinjections is INS! Use a large timeout
            #print('Read mean profiling time: %.2f, setting timeout 10x:  %.2f'%(timeout, timeout*20) )
            timeout = round(3 * proftime, 2)
        else: # profile, look opportunistically for previous runs
            # get timeout
            profiledir = '%s/%s/%s/%s/%s/%s/%s/%s/1/'%(resdir, tool, config, app, 'profile', instrument, nthreads, inputsize)
            fname = '/%s/time.txt'%(profiledir)
            if os.path.isfile( fname ):
                with open(fname, 'r') as f:
                    proftime = float( f.read() )
                # XXX: PINFI instruction counts BB, but faultinjections is INS! Use a large timeout
                #print('Read mean profiling time: %.2f, setting timeout 10x:  %.2f'%(timeout, timeout*20) )
                timeout = proftime
                timeout = round(3 * proftime, 2)
            else:
                timeout = 0

        for trial in range(start, end+1):
            trialdir = basedir + '/' + str(trial) +'/'
            #print(trialdir)
            # Skip already done experiments
            #print('CHECK to skip %s/ret.txt'%(trialdir) )
            if os.path.isfile(trialdir+'/ret.txt'):
                continue
            #print('Adding %s trial %s'%( app, trial ) )

            if action == 'profile':
                # create trialdir
                if not os.path.exists(trialdir):
                    os.makedirs(trialdir)
            elif action == 'fi':
                assert os.path.exists(trialdir), 'Trialdir %s does not exist, forgot to run generate-fi-samples?'%(trialdir)
                assert os.path.isfile(trialdir + '/'+ fi_tools.files[tool]['target']),'Trialdir %s does not exist, forgot to run generate-fi-samples?'%(trialdir)
                #assert not os.path.isfile(trialdir + '/'+ fi_tools.files[args.tool]['injection']),\
                #'Reproducible injection is not supported: ' + trialdir + '/' + fi_tools.files[args.tool]['injection']
                #if os.path.isfile(trialdir + '/'+ fi_tools.files[tool]['injection']):
                    #print('WARNING: Reproducible injection is not supported, found injection file')
                    #os.remove(trialdir + '/'+ fi_tools.files[tool]['injection'])
            else:
                assert False, 'Invalid action:' + action

            # Create executable
            ## Find the program binary to run
            if tool == 'pinfi' or tool == 'golden':
                compiled = 'golden'
            elif tool == 'refine':
                if instrument == 'omplib':
                    compiled = 'golden'
                else:
                    compiled = 'refine'
            elif tool == 'refine-noff':
                if instrument == 'omplib':
                    compiled = 'golden'
                else:
                    compiled = 'refine-noff'
            else:
                print('Unknown tool' + tool)
                sys.exit(1)
            rootdir = '%s/%s/%s/'%(appdir, compiled, config)

            ## Build the exelist
            ### Any tool specific exelist header
            fi_exelist=[]
            if tool in fi_tools.exelist:
                if config == 'serial':
                    fi_exelist = fi_tools.exelist[tool][config][action]
                else:
                    fi_exelist = fi_tools.exelist[tool][config][action][instrument]
            #print(fi_exelist)

            ### Patch APPDIR and NTHREADS if needed
            # XXX: replace $APPDIR, needed only for CoMD
            exelist = [ s.replace( '$APPDIR', '%s/%s'%(rootdir, app) ) for s in data.programs[config][app]['exec'][inputsize] ]
            # XXX: replace NTHREADS, needed only for XSBench omp
            exelist = [ s.replace( '$NTHREADS', nthreads ) for s in exelist ]
            # XXX: note using rootdir, program binary in data is relative to that
            exelist = fi_exelist + [ rootdir + exelist[0] ] + exelist[1:]
            exelist = '"%s"'%(' '.join(exelist))
            #print('\nexelist< %s >\n'%(exelist))
            # XXX: add cleanup to avoid disk space problems
            cleanstr = '"%s"'%(data.programs[config][app]['clean'])

            ## Append to experiments (must be string list)
            exps.append( ('-r', trialdir, str(timeout), exelist, cleanstr) )
            #if verbose:
            #    print(runenv + ['-r', trialdir, str(timeout), exelist])
            #sys.exit(123)
    #print("==== experiments ====")
    #print(exps)
    #print("==== end experiments ====")
    exps = sorted( exps, key=lambda exp: float(exp[2]), reverse=True )
    return exps

def msub(nodes, partition, walltime, nworkers, env, chunk, tool, action, config, nthreads, instrument, inputsize, chunkno):
    m, s = divmod(walltime, 60)
    h, m = divmod(m, 60)
    #print('%02d:%02d:%02d'%(h, m, s) )
    fname = 'submit-moab-%s-%s-%s-%s-%s-%s-%s.sh'%(tool, action, config, nthreads, instrument, inputsize, chunkno )
    print(fname)
    with open(fname, 'w') as f:
        filestr = '#!/bin/bash\n'
        filestr += '#MSUB -l nodes=' + str(nodes) + '\n'
        filestr += '#MSUB -l partition=cab\n'
        filestr += '#MSUB -l walltime=%02d:%02d:%02d\n'%( h, m, s )
        filestr += '#MSUB -q p%s\n'%( partition )
        filestr += '#MSUB -V\n'
        filestr += '#MSUB -o /usr/workspace/wsb/ggeorgak/moab.out.%j.%N\n'
        filestr += '#MSUB -e /usr/workspace/wsb/ggeorgak/moab.err.%j.%N\n'

        filestr += 'date\n'

        filestr += '$SCRIPTDIR/srun.py -n %s -p %s -w %s '%(nodes, partition, nworkers)
        filestr += ' '.join(env)
        filestr += ' ' 
        filestr += ' '.join(chunk)
        filestr += '\n'
        
        filestr += 'date\n'
        filestr += 'echo "MSUB COMPLETED"\n'

        f.write(filestr)


# TODO: put descriptive names, remove args access
def generate_jobs(nodes, partition, timelimit, exps, config, tool, action, instrument, nthreads, inputsize):
    nexps = len(exps)
    if nthreads == '' or nthreads == '1':
        nworkers = 16
    else:
        nworkers = 1
    
    env=[]
    if config == 'omp':
        env += [ '-e', 'OMP_NUM_THREADS', nthreads, '-e', 'OMP_PROC_BIND', 'close', '-e', 'OMP_WAIT_POLICY', 'passive' ]
    if tool == 'refine':
        if instrument == 'all' or instrument == 'omplib':
            env += [ '-e', 'LD_LIBRARY_PATH', homedir + '/usr/local/refine/lib:' + homedir + '/usr/local/lib' ]
    if tool == 'refine-noff':
        if instrument == 'all' or instrument == 'omplib':
            env += [ '-e', 'LD_LIBRARY_PATH', homedir + '/usr/local/refine-noff/lib:' + homedir + '/usr/local/lib' ]

    # First Fit Decreasing bin packing
    chunks = []
    for e in exps:
        newchunk = True
        time = e[2]
        time = float(time)

        if time == 0:
            time = 2700

        for i, (t, s, c) in enumerate(chunks):
            if t + time <= timelimit:
                chunks[i] = ( t+time, s+1,  c+list(e) )
                newchunk = False
        if newchunk:
            chunks.append( ( time, 1, list(e) ) )
    #for t, s, c in chunks: # ggout
    #    print('===== CHUNK ====')
    #    print(c)
    #    print( 't %d len(c) %d'%( t, s ) )
    #    print('===== END CHUNK ====')
    #    break
    print( 'total %d'%( len( chunks ) ) )

    # Group by workers in node
    for i, chunk_group in enumerate( get_chunk(chunks, nodes*nworkers) ):
        chunklist = []
        walltime = 0
        # create the chunklist arguments
        for t, s, c in chunk_group:
            chunklist += c
            walltime = max(walltime, t)

        # check if it needs all nodes
        #print('chunk_group len %d'%( len( chunk_group ) ) ) # ggout
        nodes_group = int ( len( chunk_group ) / nworkers )
        if ( len( chunk_group ) % nworkers ) > 0 :
            nodes_group += 1
        #print('nodes %d -- vs nodes_group %d'%(nodes, nodes_group) )

        # round to the next minute
        if walltime % 60 != 0:
            walltime = walltime + (60 - walltime%60)
        #print(walltime)
        msub(nodes_group, partition, walltime, nworkers, env, chunklist, tool, action, config, nthreads, instrument, inputsize, i+1)
    #print('chunkno %d nexps %d'%( chunkno, len(chunk2) ) ) # ggout
    #print('Total chunks:%d'%(chunkno))
    
def get_chunk(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def main():
    parser = argparse.ArgumentParser('Run profiling experiments')
    parser.add_argument('-d', '--appdir', help='applications root directory', required=True)
    parser.add_argument('-r', '--resdir', help='results directory', required=True)
    parser.add_argument('-a', '--apps', help='applications to run', choices=data.apps+['ALL'], nargs='+', required=True)
    parser.add_argument('-t', '--tools', help='tool to run', choices=['refine', 'pinfi', 'golden', 'refine-noff'], nargs='+', required=True)
    parser.add_argument('-x', '--action', help='action to take', choices=['profile', 'fi'], required=True)
    parser.add_argument('-s', '--start', help='start trial', type=int, required=True)
    parser.add_argument('-c', '--config', help='run configuration', choices=['serial', 'omp', 'ALL'], nargs='+', required=True)
    parser.add_argument('-e', '--end', help='end trial', type=int, required=True)
    parser.add_argument('-l', '--timelimit', help='target timelimit (seconds)', type=int, required=True)
    parser.add_argument('-n', '--nodes', help='target nodes', type=int, required=True)
    parser.add_argument('-g', '--generate', help='generate moab jobscripts', default=False, action='store_true')
    parser.add_argument('-p', '--partition', help='partition to run experiments', choices=['echo', 'local', 'debug', 'batch' ], required=True)
    args = parser.parse_args()

    # Error checking
    assert os.path.isdir(args.appdir), 'Applications directory: ' + args.appdir + 'does not exist'
    assert args.start <= args.end, 'Start must be < end'
    assert args.timelimit > 0, 'Walltime must be > 0'
    assert args.nodes > 0, 'Node must be > 0'
    if args.apps == ['ALL']:
        args.apps = data.apps

    config = args.config
    if args.config == ['ALL']:
        config = [ 'serial', 'omp' ]

    experiments = {
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
        for c in config:
            for i in experiments[c]['inputs']:
                for n in experiments[c][i]['nthreads']:
                    for ins in experiments[c]['instrument']:
                        exps = check(args.appdir, args.resdir, t, c, args.apps, args.action, ins, n, i, args.start, args.end)
                        if exps:
                            print('==== EXPERIMENT ====')
                            print( 'Experiment: %s %s %s %s %s %s %s %s [%s]'%( t, args.action, c, n, ins, i, args.start, args.end, ', '.join(args.apps) ) )
                            #print(exps)
                            nexps = len(exps)
                            print('Nof exps: %d'%( nexps ) )
                            if args.generate:
                                #def generate_jobs(exps, c, t, action, ins, n, i, start, end):
                                generate_jobs(args.nodes, args.partition, args.timelimit, exps, c, t, args.action, ins, n, i)
                            
                            print('==== END EXPERIMENT ====')

if __name__ == "__main__":
    main()
