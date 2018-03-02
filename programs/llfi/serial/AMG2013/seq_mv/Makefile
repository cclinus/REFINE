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
 csr_matrix.h\
 headers.h\
 HYPRE_seq_mv.h\
 seq_mv.h\
 vector.h

FILES =\
 big_csr_matrix.c\
 csr_matop.c\
 csr_matrix.c\
 csr_matvec.c\
 genpart.c\
 HYPRE_csr_matrix.c\
 HYPRE_vector.c\
 vector.c

OBJS = ${FILES:.c=.ll}

##################################################################
# Targets
##################################################################
 
all: libseq_mv.ll

clean:
	@rm -f *.ll *.dxx
 
veryclean: clean
	@rm -f lib*.ll
 

##################################################################
# Rules
##################################################################

libseq_mv.ll: ${OBJS}
	@echo  "Building $@ ... "
	$(CLINK) -S ${OBJS} -o $@

${OBJS}: ${HEADERS}

##################################################################
# Generic rules
##################################################################
 
%.ll : %.c
	$(CC) $(CFLAGS) $< -o $@

