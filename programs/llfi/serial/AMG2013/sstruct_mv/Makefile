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
 -I../IJ_mv\
 ${INCLUDE_CFLAGS}\
 -emit-llvm -S -fno-use-cxa-atexit
                                                                                               
HEADERS =\
 box_map.h\
 headers.h\
 HYPRE_sstruct_mv.h\
 sstruct_graph.h\
 sstruct_grid.h\
 sstruct_matrix.h\
 sstruct_mv.h\
 sstruct_stencil.h\
 sstruct_vector.h

FILES =\
 box_map.c\
 HYPRE_sstruct_graph.c\
 HYPRE_sstruct_grid.c\
 HYPRE_sstruct_matrix.c\
 HYPRE_sstruct_stencil.c\
 HYPRE_sstruct_vector.c\
 sstruct_axpy.c\
 sstruct_copy.c\
 sstruct_graph.c\
 sstruct_grid.c\
 sstruct_innerprod.c\
 sstruct_matrix.c\
 sstruct_matvec.c\
 sstruct_overlap_innerprod.c\
 sstruct_scale.c\
 sstruct_stencil.c\
 sstruct_vector.c

OBJS = ${FILES:.c=.ll}

##################################################################
# Targets
##################################################################

all: libsstruct_mv.ll

clean:
	@rm -f *.ll *.dxx

veryclean: clean
	@rm -f lib*.ll

##################################################################
# Rules
##################################################################

libsstruct_mv.ll: ${OBJS}
	@echo  "Building $@ ... "
	$(CLINK) -S ${OBJS} -o $@

${OBJS}: ${HEADERS}

##################################################################
# Generic rules
##################################################################
                                                                                               
%.ll : %.c
	$(CC) $(CFLAGS) $< -o $@
