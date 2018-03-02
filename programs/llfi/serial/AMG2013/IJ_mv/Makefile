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
 -I../utilities\
 -I../struct_mv\
 -I../seq_mv\
 -I../parcsr_mv\
 -I../parcsr_ls\
 ${INCLUDE_CFLAGS}\
 -emit-llvm -S -fno-use-cxa-atexit
 
HEADERS =\
 aux_parcsr_matrix.h\
 aux_par_vector.h\
 headers.h\
 HYPRE_IJ_mv.h\
 IJ_matrix.h\
 IJ_mv.h\
 IJ_vector.h

FILES =\
 aux_parcsr_matrix.c\
 aux_par_vector.c\
 HYPRE_IJMatrix.c\
 HYPRE_IJVector.c\
 IJMatrix.c\
 IJMatrix_parcsr.c\
 IJVector_parcsr.c

OBJS = ${FILES:.c=.ll}

##################################################################
# Targets
##################################################################

all: libIJ_mv.ll

clean:
	@rm -f *.dxx *.ll
 
veryclean: clean
	@rm -f lib*.ll
 
##################################################################
# Rules
##################################################################

libIJ_mv.ll: ${OBJS}
	@echo  "Building $@ ... "
	$(CLINK) -S ${OBJS} -o $@

${OBJS}: ${HEADERS}

##################################################################
# Generic rules
##################################################################
 
%.ll : %.c
	$(CC) $(CFLAGS) $< -o $@
