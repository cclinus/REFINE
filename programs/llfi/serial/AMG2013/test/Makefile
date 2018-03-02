#BHEADER**********************************************************************
# Copyright (c) 2008,  Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
# This file is part of HYPRE.  See file COPYRIGHT for details.
#
# HYPRE is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License (as published by the Free
# Software Foundation) version 2.1 dated February 1999.
#
# $Revision: 2.4 $
#EHEADER**********************************************************************


.SUFFIXES:
.SUFFIXES: .c .ll

srcdir = .

include ../Makefile.include

 CFLAGS_LL = \
 -I..\
 -I../utilities\
 -I../struct_mv\
 -I../sstruct_mv\
 -I../IJ_mv\
 -I../seq_mv\
 -I../parcsr_mv\
 -I../parcsr_ls\
 -I../krylov\
 ${INCLUDE_CFLAGS}\
 -DHYPRE_TIMING\
 -emit-llvm -S -fno-use-cxa-atexit

CFLAGS = \
 -I..\
 -I../utilities\
 -I../struct_mv\
 -I../sstruct_mv\
 -I../IJ_mv\
 -I../seq_mv\
 -I../parcsr_mv\
 -I../parcsr_ls\
 -I../krylov\
 ${INCLUDE_CFLAGS}\
 -DHYPRE_TIMING\

LFLAGS =\
 -L.\
 -L../parcsr_ls\
 -L../parcsr_mv\
 -L../IJ_mv\
 -L../seq_mv\
 -L../sstruct_mv\
 -L../struct_mv\
 -L../krylov\
 -L../utilities\
 -lparcsr_ls\
 -lparcsr_mv\
 -lseq_mv\
 -lsstruct_mv\
 -lIJ_mv\
 -lHYPRE_struct_mv\
 -lkrylov\
 -lHYPRE_utilities\
 ${INCLUDE_LFLAGS}

LIBS = \
 ../parcsr_ls/libparcsr_ls.ll\
 ../parcsr_mv/libparcsr_mv.ll\
 ../seq_mv/libseq_mv.ll\
 ../sstruct_mv/libsstruct_mv.ll\
 ../IJ_mv/libIJ_mv.ll\
 ../struct_mv/libHYPRE_struct_mv.ll\
 ../krylov/libkrylov.ll\
 ../utilities/libHYPRE_utilities.ll

##################################################################
# Targets
##################################################################

all: amg2013

clean:
	@rm -f *.o *.ll llfi*.txt

veryclean: clean
	@rm -f amg2013

##################################################################
# Rules
##################################################################

LLFI_LFLAGS=-L${LLFI_BUILD_ROOT}/llfi/runtime_lib -Wl,-rpath,${LLFI_BUILD_ROOT}/llfi/runtime_lib -lllfi-rt

amg2013: amg2013.ll llfi/amg2013-profiling.exe llfi/amg2013-faultinjection.exe
	@echo  "Linking" $@ "... "
	${CC} -g ${CFLAGS} -o amg2013 amg2013.ll ${INCLUDE_LFLAGS}

llfi/amg2013-profiling.exe: amg2013.ll
	${LLFI_BUILD_ROOT}/llvm/bin/llc -O2 -filetype=obj -o llfi/amg2013-profiling.o llfi/amg2013-profiling.ll
	${CC} -g ${CFLAGS} -o llfi/amg2013-profiling.exe llfi/amg2013-profiling.o ${INCLUDE_LFLAGS} ${LLFI_LFLAGS}

llfi/amg2013-faultinjection.exe: amg2013.ll
	${LLFI_BUILD_ROOT}/llvm/bin/llc -O2 -filetype=obj -o llfi/amg2013-faultinjection.o llfi/amg2013-faultinjection.ll
	${CC} -g ${CFLAGS} -o llfi/amg2013-faultinjection.exe llfi/amg2013-faultinjection.o ${INCLUDE_LFLAGS} ${LLFI_LFLAGS}

amg2013.ll: amg2013.c
	$(CC) -g $(CFLAGS_LL) $< -o amg2013.obj.ll
	${CLINK} -S ${LIBS} amg2013.obj.ll -o amg2013.all.ll
	${LLFI_BUILD_ROOT}/llvm/bin/opt -disable-opt -S amg2013.all.ll -o $@
	#${LLFI_BUILD_ROOT}/llvm/bin/opt -O2 -S amg2013.all.ll -o $@
	${LLFI_BUILD_ROOT}/llfi/bin/instrument --dir 'llfi' --IRonly --cc c --readable ${INCLUDE_LFLAGS} amg2013.ll

##################################################################
# Generic rules
##################################################################


%.ll : %.c
	$
	CC) $(CFLAGS_LL) $< -o $@
