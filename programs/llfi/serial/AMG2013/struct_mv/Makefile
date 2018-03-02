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
 ${INCLUDE_CFLAGS}\
 -emit-llvm -S -fno-use-cxa-atexit
                                                                                               
HEADERS =\
 assumed_part.h\
 box.h\
 box_manager.h\
 box_neighbors.h\
 box_pthreads.h\
 computation.h\
 headers.h\
 hypre_box_smp_forloop.h\
 HYPRE_struct_mv.h\
 struct_communication.h\
 struct_grid.h\
 struct_matrix.h\
 struct_mv.h\
 struct_stencil.h\
 struct_vector.h

FILES =\
 assumed_part.c\
 box_algebra.c\
 box_alloc.c\
 box_boundary.c\
 box.c\
 box_manager.c\
 box_neighbors.c\
 communication_info.c\
 computation.c\
 grow.c\
 HYPRE_struct_grid.c\
 HYPRE_struct_matrix.c\
 HYPRE_struct_stencil.c\
 HYPRE_struct_vector.c\
 new_assemble.c\
 new_box_neighbors.c\
 project.c\
 struct_axpy.c\
 struct_communication.c\
 struct_copy.c\
 struct_grid.c\
 struct_innerprod.c\
 struct_io.c\
 struct_matrix.c\
 struct_matrix_mask.c\
 struct_matvec.c\
 struct_overlap_innerprod.c\
 struct_scale.c\
 struct_stencil.c\
 struct_vector.c

OBJS = ${FILES:.c=.ll}

##################################################################
# Targets
##################################################################

all: libHYPRE_struct_mv.ll

clean:
	@rm -f *.ll *.dxx

veryclean: clean
	@rm -f lib*.ll

##################################################################
# Rules
##################################################################

libHYPRE_struct_mv.ll: ${OBJS}
	@echo  "Building $@ ... "
	$(CLINK) -S ${OBJS} -o $@

${OBJS}: ${HEADERS}

##################################################################
# Generic rules
##################################################################
                                                                                               
%.ll : %.c
	$(CC) $(CFLAGS) $< -o $@
