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

CFLAGS =\
 -I..\
 ${INCLUDE_CFLAGS}\
 -DHYPRE_TIMING\
 -emit-llvm -S -fno-use-cxa-atexit

##################################################################
# Targets
##################################################################

all: libHYPRE_utilities.ll

clean:
	@rm -f *.ll

veryclean: clean
	@rm -f libHYPRE_*.ll

##################################################################
# Utilities rules
##################################################################

UTILITIES_HEADERS =\
 amg_linklist.h\
 exchange_data.h\
 general.h\
 hypre_memory.h\
 hypre_smp_forloop.h\
 HYPRE_utilities.h\
 mpistubs.h\
 threading.h\
 thread_mpistubs.h\
 timing.h\
 umalloc_local.h\
 utilities.h

UTILITIES_FILES =\
 amg_linklist.c\
 binsearch.c\
 exchange_data.c\
 hypre_memory.c\
 hypre_qsort.c\
 memory_dmalloc.c\
 mpistubs.c\
 qsplit.c\
 random.c\
 threading.c\
 thread_mpistubs.c\
 timer.c\
 timing.c\
 umalloc_local.c\
 hypre_error.c

UTILITIES_OBJS = ${UTILITIES_FILES:.c=.ll}

libHYPRE_utilities.ll: ${UTILITIES_OBJS}
	@echo  "Building $@ ... "
	$(CLINK) -S ${UTILITIES_OBJS} -o $@

${UTILITIES_OBJS}: ${UTILITIES_HEADERS}

#timer.o: timer.c
#	${CC} -D_POSIX_SOURCE -o $@ -c ${CFLAGS} $<
timer.ll: timer.c
	${CC} -D_POSIX_SOURCE -o $@ -c ${CFLAGS} $<

##################################################################
# Generic rules
##################################################################

%.ll : %.c
	$(CC) $(CFLAGS) $< -o $@
