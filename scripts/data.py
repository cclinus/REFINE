import os
import sys

try:
    appsdir = os.environ['APPSDIR']
except:
    print('Env variable APPSDIR is missing')
    sys.exit(1)

INPUT = 'serial'
NTHREADS = '16'

## XXX: IS is very short running and it has no output to verify
Programs
NAS = {
    'test':{
        'BT':{ 'CLASS':'S' }, 'CG':{ 'CLASS':'S' }, 'DC': { 'CLASS':'S' }, 'EP': { 'CLASS':'S' },
        'FT':{ 'CLASS':'S' }, 'IS':{ 'CLASS':'S' }, 'LU': { 'CLASS':'S' }, 'MG': { 'CLASS':'S' },
        'SP':{ 'CLASS':'S' }, 'UA':{ 'CLASS':'S' }
    }
    'serial':{
        'BT':{ 'CLASS':'A' }, 'CG':{ 'CLASS':'B' }, 'DC': { 'CLASS':'W' }, 'EP': { 'CLASS':'A' },
        'FT':{ 'CLASS':'B' }, 'IS':{ 'CLASS':'A' }, 'LU': { 'CLASS':'A' }, 'MG': { 'CLASS':'B' },
        'SP':{ 'CLASS':'A' }, 'UA':{ 'CLASS':'B' }
    }
    'omp':{
        'BT':{ 'CLASS':'B' }, 'CG':{ 'CLASS':'C' }, 'DC': { 'CLASS':'A' }, 'EP': { 'CLASS':'C' },
        'FT':{ 'CLASS':'B' }, 'IS':{ 'CLASS':'A' }, 'LU': { 'CLASS':'C' }, 'MG': { 'CLASS':'C' },
        'SP':{ 'CLASS':'B' }, 'UA':{ 'CLASS':'B' }

    }
}

AMG= {
    'test'  : ['/AMG/test/amg', '-n', '32', '32', '32'],
    'serial': ['/AMG/test/amg', '-n', '96', '96', '96'],
    'omp'   : ['/AMG/test/amg', '-n', '256', '256', '256'],
},

CoMD = {
    'test'  : ['/CoMD/bin/CoMD-serial', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '4', '-y', '4', '-z', '4'],
    'serial': ['/CoMD/bin/CoMD-serial', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '32', '-y', '32', '-z', '32'],
    'omp'   : ['/CoMD/bin/CoMD-openmp', '-d', './pots/', '-e', '-i', '1', '-j', '1', '-k', '1', '-x', '64', '-y', '64', '-z', '64']

}

HPCCG = {
    'test:' : ['HPCCG-1.0/test_HPCCG', '32', '32', '32'],
    'serial': ['HPCCG-1.0/test_HPCCG', '128', '128', '128'],
    'omp'   : ['HPCCG-1.0/test_HPCCG', '256', '256', '256']
}

lulesh = {
    'test'  : ['lulesh/lulesh2.0', '-i', '10'],
    'serial': ['lulesh/lulesh2.0'],
    'omp'   : ['lulesh/lulesh2.0', '-s', '50'],
}
# XXX: XSBench needs the number of threads
XSBench = {
    'test'  : ['/XSBench/src/XSBench','-s','small', '-l', '100000'],
    'serial': ['/XSBench/src/XSBench','-s','small'],
    'omp'   : ['/XSBench/src/XSBench','-s','large','-t',NTHREADS],
}

miniFE = {
    'test'  : ['/miniFE/ref/src/miniFE.x','-nx','16','-ny','16','-nz','16'],
    'serial': ['/miniFE/ref/src/miniFE.x','-nx','64','-ny','64','-nz','64'],
    'omp'   : ['/miniFE/ref/src/miniFE.x','-nx','256','-ny','256','-nz','256'],
}

NASBASEDIR = 'NPB3.3-SER-C/'

dirs = {
'AMG': { 'appdir':'AMG/test/', 'build':{ 'dir':'AMG/', 'args':[] } },
'CoMD': { 'appdir':'CoMD/', 'build':{ 'dir':'CoMD'+'/src-mpi/', 'args':[] } },
'HPCCG-1.0': { 'appdir':'HPCCG-1.0/', 'build':{ 'dir':'HPCCG-1.0/', 'args':[] } },
'lulesh': { 'appdir':'lulesh/', 'build':{ 'dir':'lulesh/', 'args':[] } },
'XSBench': { 'appdir':'XSBench/src/', 'build':{ 'dir':'XSBench/src/', 'args':[] } },
'miniFE': { 'appdir':'miniFE/ref/src/', 'build':{ 'dir':'miniFE/ref/src/', 'args':[] } },
'BT': { 'appdir':NASBASEDIR+'BT/', 'build':{ 'dir':NASBASEDIR+'BT/', 'args':['BT','CLASS='+NAS[INPUT]['BT']['CLASS']] } },
'CG': { 'appdir':NASBASEDIR+'CG/', 'build':{ 'dir':NASBASEDIR+'CG/', 'args':['CG','CLASS='+NAS[INPUT]['CG']['CLASS']] } },
'DC': { 'appdir':NASBASEDIR+'DC/', 'build':{ 'dir':NASBASEDIR+'DC/', 'args':['DC','CLASS='+NAS[INPUT]['DC']['CLASS']] } },
'EP': { 'appdir':NASBASEDIR+'EP/', 'build':{ 'dir':NASBASEDIR+'EP/', 'args':['EP','CLASS='+NAS[INPUT]['EP']['CLASS']] } },
'FT': { 'appdir':NASBASEDIR+'FT/', 'build':{ 'dir':NASBASEDIR+'FT/', 'args':['FT','CLASS='+NAS[INPUT]['FT']['CLASS']] } },
'LU': { 'appdir':NASBASEDIR+'LU/', 'build':{ 'dir':NASBASEDIR+'LU/', 'args':['LU','CLASS='+NAS[INPUT]['LU']['CLASS']] } },
'MG': { 'appdir':NASBASEDIR+'MG/', 'build':{ 'dir':NASBASEDIR+'MG/', 'args':['MG','CLASS='+NAS[INPUT]['MG']['CLASS']] } },
'SP': { 'appdir':NASBASEDIR+'SP/', 'build':{ 'dir':NASBASEDIR+'SP/', 'args':['SP','CLASS='+NAS[INPUT]['SP']['CLASS']] } },
'UA': { 'appdir':NASBASEDIR+'UA/', 'build':{ 'dir':NASBASEDIR+'UA/', 'args':['UA','CLASS='+NAS[INPUT]['UA']['CLASS']] } },
}

execs = {
'AMG'       : AMG[INPUT],
'CoMD'      : CoMD[INPUT],
'HPCCG-1.0' : HPCCG[INPUT],
'lulesh'    : lulesh[INPUT],
'XSBench'   : XSBench[INPUT],
'miniFE'    : miniFE[INPUT],
'BT':[NASBASEDIR+'bin/bt.'+NAS[INPUT]['BT']['CLASS']+'.x'],
'CG':[NASBASEDIR+'bin/cg.'+NAS[INPUT]['CG']['CLASS']+'.x'],
'DC':[NASBASEDIR+'bin/dc.'+NAS[INPUT]['DC']['CLASS']+'.x'],
'EP':[NASBASEDIR+'bin/ep.'+NAS[INPUT]['EP']['CLASS']+'.x'],
'FT':[NASBASEDIR+'bin/ft.'+NAS[INPUT]['FT']['CLASS']+'.x'],
'LU':[NASBASEDIR+'bin/lu.'+NAS[INPUT]['LU']['CLASS']+'.x'],
'MG':[NASBASEDIR+'bin/lu.'+NAS[INPUT]['MG']['CLASS']+'.x'],
'SP':[NASBASEDIR+'bin/sp.'+NAS[INPUT]['SP']['CLASS']+'.x'],
'UA':[NASBASEDIR+'bin/ua.'+NAS[INPUT]['UA']['CLASS']+'.x'],
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

