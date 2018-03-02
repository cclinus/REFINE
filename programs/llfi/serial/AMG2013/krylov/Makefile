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
 
include ../Makefile.include

CFLAGS = \
 -I..\
 -I../utilities\
 ${INCLUDE_CFLAGS}\
 -emit-llvm -S -fno-use-cxa-atexit

HEADERS =\
 all_krylov.h\
 gmres.h\
 krylov.h\
 pcg.h\
 HYPRE_MatvecFunctions.h

FILES =\
 gmres.c\
 HYPRE_gmres.c\
 HYPRE_pcg.c\
 pcg.c

OBJS = ${FILES:.c=.ll}

##################################################################
# Targets
##################################################################

all: libkrylov.ll

clean:
	rm -f *.o *.dxx *.ll

veryclean: clean
	rm -f lib*.ll


##################################################################
# Rules
##################################################################

libkrylov.ll: ${OBJS}
	@echo  "Building $@ ... "
	$(CLINK) -S ${OBJS} -o $@


${OBJS}: ${HEADERS}

##################################################################
# Generic rules
##################################################################
 
%.ll : %.c
	$(CC) $(CFLAGS) $< -o $@

