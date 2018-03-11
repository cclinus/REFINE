import data
import sys
import random
import os
import re
import subprocess

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

files = {
        'pinfi': {
            'inscount': 'pin.instcount.txt',
            'injection':'pin.injection.txt',
            'target':'pin.target.txt',
            },
        'refine': {
            'inscount':'refine-inscount.txt',
            'injection':'refine-inject.txt',
            'target':'refine-target.txt'
        },
        'refine-noff': {
            'inscount':'refine-inscount.txt',
            'injection':'refine-inject.txt',
            'target':'refine-target.txt'
        }
    }

exelist = {
    'pinfi':  {
        'serial': {
            'profile':[pinbin, '-t', pinfidir + '/obj-intel64/instcount', '-save-instr', '--'],
            'fi'     :[pinbin, '-t', pinfidir + '/obj-intel64/faultinjection', '--'],
        },
        'omp': {
           'profile': {
                'all'   :[pinbin, '-t', pinfidir + '/obj-intel64/instcount_omp', '-save-instr', '-instr-libs', 'libomp', '--'],
                'app'   :[pinbin, '-t', pinfidir + '/obj-intel64/instcount_omp', '-save-instr', '--'],
                'omplib':[pinbin, '-t', pinfidir + '/obj-intel64/instcount_omp', '-save-instr', '-nomain', '-instr-libs', 'libomp', '--'],
            },
            'fi': {
                'all'   :[pinbin, '-t', pinfidir + '/obj-intel64/faultinjection_omp', '-instr-libs', 'libomp', '--'],
                'app'   :[pinbin, '-t', pinfidir + '/obj-intel64/faultinjection_omp', '--'],
                'omplib':[pinbin, '-t', pinfidir + '/obj-intel64/faultinjection_omp', '-nomain', '-instr-libs', 'libomp', '--']
            }
        }
    },
}
