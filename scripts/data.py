import os
import sys

#TODO: REMOVE NTHREADS
NTHREADS = '16'

#Programs
## XXX: IS is very short running and it has no output to verify
#TODO ADD MG
apps = [ 'AMG' , 'CoMD', 'HPCCG-1.0', 'lulesh', 'XSBench', 'miniFE', 'BT', 'CG', 'DC', 'EP', 'FT', 'LU', 'SP', 'UA' ]


NASBASEDIR_SERIAL = 'NPB3.3-SER-C/'
NASBASEDIR_OMP= 'NPB3.3-OMP-C/'

dirs = {
    'serial' : {
        'AMG': { 'rundir':'AMG/test/', 'build':{ 'dir':'AMG/', 'args': { 'test':[], 'small':[], 'large':[] }
        'CoMD': { 'rundir':'CoMD/', 'build':{ 'dir':'CoMD'+'/src-mpi/', 'args':[] } },
        'HPCCG-1.0': { 'rundir':'HPCCG-1.0/', 'build':{ 'dir':'HPCCG-1.0/', 'args':[] } },
        'lulesh': { 'rundir':'lulesh/', 'build':{ 'dir':'lulesh/', 'args':[] } },
        'XSBench': { 'rundir':'XSBench/src/', 'build':{ 'dir':'XSBench/src/', 'args':[] } },
        'miniFE': { 'rundir':'miniFE/ref/src/', 'build':{ 'dir':'miniFE/ref/src/', 'args':[] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
        'BT': {'rundir':NASBASEDIR_SERIAL+'BT/','builddir':NASBASEDIR_SERIAL+'BT/','args':{ 'test': ['BT','CLASS=S'], 'small': ['BT','CLASS=A'], 'large': ['BT', 'CLASS=B'] } },
    },
    'omp': {
        'AMG': { 'rundir':'AMG/test/', 'build':{ 'dir':'AMG/', 'args':[] } },
        'CoMD': { 'rundir':'CoMD/', 'build':{ 'dir':'CoMD'+'/src-openmp/', 'args':[] } },
        'HPCCG-1.0': { 'rundir':'HPCCG-1.0/', 'build':{ 'dir':'HPCCG-1.0/', 'args':[] } },
        'lulesh': { 'rundir':'lulesh/', 'build':{ 'dir':'lulesh/', 'args':[] } },
        'XSBench': { 'rundir':'XSBench/src/', 'build':{ 'dir':'XSBench/src/', 'args':[] } },
        'miniFE': { 'rundir':'miniFE/openmp-opt/src/', 'build':{ 'dir':'miniFE/openmp-opt/src/', 'args':[] } },
        'BT': { 'rundir':NASBASEDIR_OMP+'BT/', 'build':{ 'dir':NASBASEDIR_OMP+'BT/', 'args':['BT','CLASS='+NAS[INPUT]['BT']['CLASS']] } },
        'CG': { 'rundir':NASBASEDIR_OMP+'CG/', 'build':{ 'dir':NASBASEDIR_OMP+'CG/', 'args':['CG','CLASS='+NAS[INPUT]['CG']['CLASS']] } },
        'DC': { 'rundir':NASBASEDIR_OMP+'DC/', 'build':{ 'dir':NASBASEDIR_OMP+'DC/', 'args':['DC','CLASS='+NAS[INPUT]['DC']['CLASS']] } },
        'EP': { 'rundir':NASBASEDIR_OMP+'EP/', 'build':{ 'dir':NASBASEDIR_OMP+'EP/', 'args':['EP','CLASS='+NAS[INPUT]['EP']['CLASS']] } },
        'FT': { 'rundir':NASBASEDIR_OMP+'FT/', 'build':{ 'dir':NASBASEDIR_OMP+'FT/', 'args':['FT','CLASS='+NAS[INPUT]['FT']['CLASS']] } },
        'LU': { 'rundir':NASBASEDIR_OMP+'LU/', 'build':{ 'dir':NASBASEDIR_OMP+'LU/', 'args':['LU','CLASS='+NAS[INPUT]['LU']['CLASS']] } },
        'MG': { 'rundir':NASBASEDIR_OMP+'MG/', 'build':{ 'dir':NASBASEDIR_OMP+'MG/', 'args':['MG','CLASS='+NAS[INPUT]['MG']['CLASS']] } },
        'SP': { 'rundir':NASBASEDIR_OMP+'SP/', 'build':{ 'dir':NASBASEDIR_OMP+'SP/', 'args':['SP','CLASS='+NAS[INPUT]['SP']['CLASS']] } },
        'UA': { 'rundir':NASBASEDIR_OMP+'UA/', 'build':{ 'dir':NASBASEDIR_OMP+'UA/', 'args':['UA','CLASS='+NAS[INPUT]['UA']['CLASS']] } },
    }
}

execs = {
    'serial' : {
        'AMG' : {
            'test'  : ['/AMG/test/amg', '-n', '32', '32', '32'],
            'small' : ['/AMG/test/amg', '-n', '96', '96', '96'],
            'large' : ['/AMG/test/amg', '-n', '256', '256', '256'],
        }

        'CoMD' : {
            'test'  : ['/CoMD/bin/CoMD-serial', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '4', '-y', '4', '-z', '4'],
            'small' : ['/CoMD/bin/CoMD-serial', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '32', '-y', '32', '-z', '32'],
            'large' : ['/CoMD/bin/CoMD-serial', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '64', '-y', '64', '-z', '64']

        }

        'HPCCG-1.0' : {
            'test:' : ['HPCCG-1.0/test_HPCCG', '32', '32', '32'],
            'small' : ['HPCCG-1.0/test_HPCCG', '128', '128', '128'],
            'large' : ['HPCCG-1.0/test_HPCCG', '256', '256', '256']
        }

        'lulesh' : {
            'test'  : ['lulesh/lulesh2.0', '-i', '10'],
            'small' : ['lulesh/lulesh2.0'],
            'large' : ['lulesh/lulesh2.0', '-s', '50'],
        }
        # XXX: XSBench needs the number of threads
        'XSBench' : {
            'test'  : ['/XSBench/src/XSBench','-s','small', '-l', '100000'],
            'small' : ['/XSBench/src/XSBench','-s','small'],
            'large' : ['/XSBench/src/XSBench','-s','large','-t',NTHREADS],
        }

        'miniFE' : {
            'test'  : ['/miniFE/ref/src/miniFE.x','-nx','16','-ny','16','-nz','16'],
            'small' : ['/miniFE/ref/src/miniFE.x','-nx','64','-ny','64','-nz','64'],
            'large' : ['/miniFE/ref/src/miniFE.x','-nx','256','-ny','256','-nz','256'],
        }

        'BT': {
            'test'  : [NASBASEDIR_SERIAL+'bin/bt.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/bt.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/bt.B.x'],
        }

        'CG': {
            'test'  : [NASBASEDIR_SERIAL+'bin/cg.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/cg.B.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/cg.C.x'],
        }
        'DC': {
            'test'  : [NASBASEDIR_SERIAL+'bin/dc.W.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/dc.W.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/dc.A.x'],
        }
        'EP': {
            'test'  : [NASBASEDIR_SERIAL+'bin/ep.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/ep.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/ep.C.x'],
        }
        'FT': {
            'test'  : [NASBASEDIR_SERIAL+'bin/ft.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/ft.B.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/ft.B.x'],
        }
        'IS': {
            'test'  : [NASBASEDIR_SERIAL+'bin/is.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/is.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/is.A.x'],
        }
        'LU': {
            'test'  : [NASBASEDIR_SERIAL+'bin/lu.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/lu.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/lu.C.x'],
        }
        'MG': {
            'test'  : [NASBASEDIR_SERIAL+'bin/mg.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/mg.B.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/mg.C.x'],
        }
        'SP': {
            'test'  : [NASBASEDIR_SERIAL+'bin/sp.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/sp.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/sp.B.x'],
        }
        'UA': {
            'test'  : [NASBASEDIR_SERIAL+'bin/ua.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/ua.B.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/ua.B.x'],
        }
    }
    # XXX: Used by refine
    'serial-noff' : {
        'AMG' : {
            'test'  : ['/AMG/test/amg', '-n', '32', '32', '32'],
            'small' : ['/AMG/test/amg', '-n', '96', '96', '96'],
            'large' : ['/AMG/test/amg', '-n', '256', '256', '256'],
        }

        'CoMD' : {
            'test'  : ['/CoMD/bin/CoMD-serial', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '4', '-y', '4', '-z', '4'],
            'small' : ['/CoMD/bin/CoMD-serial', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '32', '-y', '32', '-z', '32'],
            'large' : ['/CoMD/bin/CoMD-serial', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '64', '-y', '64', '-z', '64']

        }

        'HPCCG-1.0' : {
            'test:' : ['HPCCG-1.0/test_HPCCG', '32', '32', '32'],
            'small' : ['HPCCG-1.0/test_HPCCG', '128', '128', '128'],
            'large' : ['HPCCG-1.0/test_HPCCG', '256', '256', '256']
        }

        'lulesh' : {
            'test'  : ['lulesh/lulesh2.0', '-i', '10'],
            'small' : ['lulesh/lulesh2.0'],
            'large' : ['lulesh/lulesh2.0', '-s', '50'],
        }
        # XXX: XSBench needs the number of threads
        'XSBench' : {
            'test'  : ['/XSBench/src/XSBench','-s','small', '-l', '100000'],
            'small' : ['/XSBench/src/XSBench','-s','small'],
            'large' : ['/XSBench/src/XSBench','-s','large','-t',NTHREADS],
        }

        'miniFE' : {
            'test'  : ['/miniFE/ref/src/miniFE.x','-nx','16','-ny','16','-nz','16'],
            'small' : ['/miniFE/ref/src/miniFE.x','-nx','64','-ny','64','-nz','64'],
            'large' : ['/miniFE/ref/src/miniFE.x','-nx','256','-ny','256','-nz','256'],
        }

        'BT': {
            'test'  : [NASBASEDIR_SERIAL+'bin/bt.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/bt.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/bt.B.x'],
        }

        'CG': {
            'test'  : [NASBASEDIR_SERIAL+'bin/cg.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/cg.B.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/cg.C.x'],
        }
        'DC': {
            'test'  : [NASBASEDIR_SERIAL+'bin/dc.W.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/dc.W.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/dc.A.x'],
        }
        'EP': {
            'test'  : [NASBASEDIR_SERIAL+'bin/ep.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/ep.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/ep.C.x'],
        }
        'FT': {
            'test'  : [NASBASEDIR_SERIAL+'bin/ft.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/ft.B.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/ft.B.x'],
        }
        'IS': {
            'test'  : [NASBASEDIR_SERIAL+'bin/is.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/is.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/is.A.x'],
        }
        'LU': {
            'test'  : [NASBASEDIR_SERIAL+'bin/lu.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/lu.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/lu.C.x'],
        }
        'MG': {
            'test'  : [NASBASEDIR_SERIAL+'bin/mg.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/mg.B.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/mg.C.x'],
        }
        'SP': {
            'test'  : [NASBASEDIR_SERIAL+'bin/sp.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/sp.A.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/sp.B.x'],
        }
        'UA': {
            'test'  : [NASBASEDIR_SERIAL+'bin/ua.S.x'],
            'small' : [NASBASEDIR_SERIAL+'bin/ua.B.x'],
            'large' : [NASBASEDIR_SERIAL+'bin/ua.B.x'],
        }
    }
    'omp' : {
        'AMG' : {
            'test'  : ['/AMG/test/amg', '-n', '32', '32', '32'],
            'small' : ['/AMG/test/amg', '-n', '96', '96', '96'],
            'large' : ['/AMG/test/amg', '-n', '256', '256', '256'],
        }

        'CoMD' : {
            'test'  : ['/CoMD/bin/CoMD-openmp', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '4', '-y', '4', '-z', '4'],
            'small' : ['/CoMD/bin/CoMD-openmp', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '32', '-y', '32', '-z', '32'],
            'large' : ['/CoMD/bin/CoMD-openmp', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '64', '-y', '64', '-z', '64']

        }

        'HPCCG-1.0' : {
            'test:' : ['HPCCG-1.0/test_HPCCG', '32', '32', '32'],
            'small' : ['HPCCG-1.0/test_HPCCG', '128', '128', '128'],
            'large' : ['HPCCG-1.0/test_HPCCG', '256', '256', '256']
        }

        'lulesh' : {
            'test'  : ['lulesh/lulesh2.0', '-i', '10'],
            'small' : ['lulesh/lulesh2.0'],
            'large' : ['lulesh/lulesh2.0', '-s', '50'],
        }
        # XXX: XSBench needs the number of threads
        'XSBench' : {
            'test'  : ['/XSBench/src/XSBench','-s','small', '-l', '100000'],
            'small' : ['/XSBench/src/XSBench','-s','small'],
            'large' : ['/XSBench/src/XSBench','-s','large','-t',NTHREADS],
        }

        'miniFE' : {
            'test'  : ['/miniFE/openmp-opt/src/miniFE.x','-nx','16','-ny','16','-nz','16'],
            'small' : ['/miniFE/openmp-opt/src/miniFE.x','-nx','64','-ny','64','-nz','64'],
            'large' : ['/miniFE/openmp-opt/src/miniFE.x','-nx','256','-ny','256','-nz','256'],
        }

        'BT': {
            'test'  : [NASBASEDIR_OMP+'bin/bt.S.x'],
            'small' : [NASBASEDIR_OMP+'bin/bt.A.x'],
            'large' : [NASBASEDIR_OMP+'bin/bt.B.x'],
        }

        'CG': {
            'test'  : [NASBASEDIR_OMP+'bin/cg.S.x'],
            'small' : [NASBASEDIR_OMP+'bin/cg.B.x'],
            'large' : [NASBASEDIR_OMP+'bin/cg.C.x'],
        }
        'DC': {
            'test'  : [NASBASEDIR_OMP+'bin/dc.W.x'],
            'small' : [NASBASEDIR_OMP+'bin/dc.W.x'],
            'large' : [NASBASEDIR_OMP+'bin/dc.A.x'],
        }
        'EP': {
            'test'  : [NASBASEDIR_OMP+'bin/ep.S.x'],
            'small' : [NASBASEDIR_OMP+'bin/ep.A.x'],
            'large' : [NASBASEDIR_OMP+'bin/ep.C.x'],
        }
        'FT': {
            'test'  : [NASBASEDIR_OMP+'bin/ft.S.x'],
            'small' : [NASBASEDIR_OMP+'bin/ft.B.x'],
            'large' : [NASBASEDIR_OMP+'bin/ft.B.x'],
        }
        'IS': {
            'test'  : [NASBASEDIR_OMP+'bin/is.S.x'],
            'small' : [NASBASEDIR_OMP+'bin/is.A.x'],
            'large' : [NASBASEDIR_OMP+'bin/is.A.x'],
        }
        'LU': {
            'test'  : [NASBASEDIR_OMP+'bin/lu.S.x'],
            'small' : [NASBASEDIR_OMP+'bin/lu.A.x'],
            'large' : [NASBASEDIR_OMP+'bin/lu.C.x'],
        }
        'MG': {
            'test'  : [NASBASEDIR_OMP+'bin/mg.S.x'],
            'small' : [NASBASEDIR_OMP+'bin/mg.B.x'],
            'large' : [NASBASEDIR_OMP+'bin/mg.C.x'],
        }
        'SP': {
            'test'  : [NASBASEDIR_OMP+'bin/sp.S.x'],
            'small' : [NASBASEDIR_OMP+'bin/sp.A.x'],
            'large' : [NASBASEDIR_OMP+'bin/sp.B.x'],
        }
        'UA': {
            'test'  : [NASBASEDIR_OMP+'bin/ua.S.x'],
            'small' : [NASBASEDIR_OMP+'bin/ua.B.x'],
            'large' : [NASBASEDIR_OMP+'bin/ua.B.x'],
        }
    }
}

ifiles = {
'AMG': [],
# it's actually a dir
'CoMD' : [ 'pots' ],
'HPCCG-1.0' : [],
'lulesh' : [],
'XSBench' : [],
'miniFE' : [],
'BT' : [],
'CG': [],
'DC' : [],
'EP' : [],
'FT' : [],
'LU' : [],
'MG' : [],
'SP' : [],
'UA' : []
}

# Ths will run in a shell=True subprocess
cleanup = {
'AMG': '',
'CoMD' : '/bin/rm -rf CoMD*yaml',
'HPCCG-1.0' : '/bin/rm -rf hpccg*yaml',
'lulesh' : '',
'XSBench' : '',
'miniFE' : '/bin/rm -rf miniFE*yaml',
'BT' : '',
'CG': '',
'DC' : '/bin/rm -rf ADC.*',
'EP' : '',
'FT' : '',
'LU' : '',
'MG' : '',
'SP' : '',
'UA' : ''
}

EXPFLOAT = r'[+-]?\d+\.\d+[Ee][+-]?\d+'
FLOAT = r'[+-]?\d+\.\d+'

XSBench_verify_string = {
        'test'  : '74966788162', # small
        'serial': '74966788162', # small
        'omp'   : '74994938929' #large
}

verify = {
'AMG' :['Final Relative Residual Norm = ' + EXPFLOAT],
'CoMD': ['Final energy\s+: ' + FLOAT, 'Final atom count : \d+, no atoms lost' ],
'HPCCG-1.0':['Final residual: : ' + EXPFLOAT ],
'lulesh':['Final Origin Energy = ' + EXPFLOAT ],
'XSBench':['Verification checksum: ' + XSBench_verify_string[INPUT]],
'miniFE':['Final Resid Norm: ' + EXPFLOAT],
'BT':['\d\s+' + EXPFLOAT +' ' + EXPFLOAT + ' ' + EXPFLOAT],
'CG':[' Zeta\s+' + EXPFLOAT],
'DC':['Checksum\s+=\s+' + EXPFLOAT],
'EP':['Sums =\s+' + EXPFLOAT + '\s+' + EXPFLOAT],
'FT':['T =\s+\d+\s+Checksum =\s+' + EXPFLOAT + '\s+' + EXPFLOAT],
'LU': ['\d\s+' + EXPFLOAT +' ' + EXPFLOAT + ' ' + EXPFLOAT, '\s+' + EXPFLOAT +' ' + EXPFLOAT + ' ' + EXPFLOAT, ],
'MG': ['L2 Norm is\s+' + EXPFLOAT ],
'SP':['\d\s+' + EXPFLOAT +' ' + EXPFLOAT + ' ' + EXPFLOAT],
'UA':['\s+' + EXPFLOAT +' ' + EXPFLOAT + ' ' + EXPFLOAT, ],
}

