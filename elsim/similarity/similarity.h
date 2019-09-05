/* 
   This file is part of Elsim.

   Copyright (C) 2012, Anthony Desnos <desnos at t0t0.org>
   All rights reserved.

   Elsim is free software: you can redistribute it and/or modify
   it under the terms of the GNU Lesser General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   Elsim is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of  
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with Elsim.  If not, see <http://www.gnu.org/licenses/>.
   */
#ifndef _LIBSIMILARITY_H
#define _LIBSIMILARITY_H

#include <stdio.h>
#include <string.h>
#include <math.h>

#include "z/z.h"
#include "bz2/bz2.h"
#include "smaz/smaz.h"
#include "lzma/lzma.h"
#include "xz/xz.h"
#include "snappy/snappy.h"
#include "vcblocksort/vcblocksort.h"

#define TYPE_Z          0
#define TYPE_BZ2        1
#define TYPE_SMAZ       2
#define TYPE_LZMA       3
#define TYPE_XZ         4
#define TYPE_SNAPPY     5
#define TYPE_VCBLOCKSORT     6

struct libsimilarity {
   void *orig;
   size_t size_orig;
   void *cmp;
   size_t size_cmp;

   size_t *corig;
   size_t *ccmp;

   float res;
};
typedef struct libsimilarity libsimilarity_t;

#ifdef __cplusplus
extern "C" {                                                                                                                                                                                     
    double entropy(void *, size_t);
    void set_compress_type(int);
    int ncd(int, libsimilarity_t *);
}
#else
void set_compress_type(int);
size_t compress(int, void *, size_t);
int ncd(int, libsimilarity_t *);
int ncs(int, libsimilarity_t *);
int cmid(int, libsimilarity_t *);
double entropy(void *, size_t);
#endif


#endif
