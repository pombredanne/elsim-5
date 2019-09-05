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
#include "bz2.h"

#include <bzlib.h>

int bz2Compress(int level, const unsigned char *data, size_t avail_in, unsigned char *odata, size_t *avail_out)
{
   int ret;
   int verbosity = 0;
   int workFactor = 30;
   bz_stream strm;

   strm.bzalloc = NULL;
   strm.bzfree = NULL;   
   strm.opaque = NULL;

   ret = BZ2_bzCompressInit(&strm, level, verbosity, workFactor);
   if (ret != BZ_OK) return ret;

   strm.next_in = data;
   strm.next_out = odata;
   strm.avail_in = avail_in;
   strm.avail_out = *avail_out;

   ret = BZ2_bzCompress ( &strm, BZ_FINISH );
   if (ret == BZ_FINISH_OK) goto output_overflow;
   if (ret != BZ_STREAM_END) goto errhandler;
   
   /* normal termination */   
   *avail_out -= strm.avail_out;
   BZ2_bzCompressEnd ( &strm );                                                                                                                                                    
   return BZ_OK;
   
   output_overflow:
      BZ2_bzCompressEnd ( &strm );      
      return BZ_OUTBUFF_FULL;

   errhandler:   
      BZ2_bzCompressEnd ( &strm );

   return ret;
}
