#!/usr/bin/env python3

import os
import sys
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import argparse
import itertools
import json

import data

def autolabel(width, ax, rects):
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.00*height + err, '%.1f'%float(height), ha='center', va='bottom', fontsize=8)

def main():
    parser = argparse.ArgumentParser('This script creates the chi-square table')
    parser.add_argument('-r', '--resfile', help='results file', required=True)
    parser.add_argument('-c', '--comparators', help='tool to compare against baseline', nargs=7, action='append', required=True )
    parser.add_argument('-b', '--configbase', help='configure baseline <w><c><i><n><ins>',nargs=7, required=True)
    parser.add_argument('-a', '--apps', help='applications to run', choices=data.apps+['ALL'], nargs='+', required=True)
    parser.add_argument('-o', '--output', help='output filename', required=True )
    args = parser.parse_args()

    if not os.path.isfile( args.resfile ):
        parser_error( 'results file does not exist')

    apps = args.apps
    if apps == ['ALL']:
        apps = data.apps

    results = json.load( open( args.resfile, 'r' ) )

    print('Generating results...')

    linebreak = 4
    cb = args.configbase

    with open('%s'%( args.output ), 'w') as f:
        # Break every 4 apps for readability
        print('\\begin{tabular}{cc' + ( linebreak * 2 ) * 'c' + '}', file=f)
        print('\\toprule', file=f)
        print('Comparison & Base' + linebreak * ' & p-value & Signif. diff.?' + ' \\\\', file=f)
        print('\\midrule', file=f )

        for c in args.comparators:
            current = 0
            print('\\textbf{%s} & \\textbf{%s} '%( c[6].upper(), cb[6].upper() ), file=f, end='' )
            while current < len( apps ):
                # Apps header
                if current > 0:
                    print('& ', file=f, end='' )
                for a in apps[current:current+linebreak]:
                    print('a %s'%( a ) )
                    # add empty columns
                    print( '& \multicolumn{2}{c}{ %s } '%( a ), file=f, end='' )

                print('\\\\', file=f)

                # Apps results
                print('& ', file=f, end='')
                for a in apps[current:current+linebreak]:
                    print(' %s '%( args.configbase ) )
                    baseline = results['fi'][ cb[0] ][ cb[1] ][ a ][ cb[2] ][ cb[3] ][ cb[4] ][ cb[5] ]['outcomes']
                    tool = results['fi'][ c[0] ][ c[1] ][ a ][ c[2] ][ c[3] ][ c[4] ][ c[5] ]['outcomes']
                    print('tool %s '%( c[0] ), end='')
                    print( [ tool['crash'] + tool['timeout'], tool['soc'], tool['benign'] ] )
                    print('baseline %s '%( args.configbase ), end='' )
                    print( [ baseline['crash'] + baseline['timeout'], baseline['soc'], baseline['benign'] ] )

                    chi2, pval, dof, expected = stats.chi2_contingency(
                            [ [ tool['crash'] + tool['timeout']+1, tool['soc']+1, tool['benign']+1 ], # ggout +1
                            [ baseline['crash'] + baseline['timeout']+1, baseline['soc']+1, baseline['benign']+1 ] ], # ggout +1
                            #correction = True,
                            #lambda_="log-likelihood"
                    )
                    print('Comparing %s to baseline %s: p-val %.6f'%( c, cb, pval ) )
                    if pval < 0.05:
                        if pval < 0.01:
                            print('& $< 0.01$ & \\textcolor{red}{yes} ', file=f, end='')
                        else:
                            print('& $%.2f$ & \\textcolor{red}{yes} '%( pval ), file=f, end='')
                    else:
                        print('& $%.2f$ & \\textcolor{green}{no} '%( pval ), file=f, end='')
                # Break every 4 apps for readability
                current += linebreak
                print('\\\\ \midrule', file=f)
                print('current %d len(apps) %d'%( current, len(apps) ) )
        print('\\bottomrule', file=f)
        print('\\end{tabular}', file=f)

if __name__ == "__main__":
    main()
