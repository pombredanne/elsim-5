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
#include "xz.h"

#include <stdbool.h>
#include <lzma.h>

#define COMPRESSION_LEVEL 9 
#define COMPRESSION_EXTREME true 
#define INTEGRITY_CHECK LZMA_CHECK_NONE 
//LZMA_CHECK_CRC64

int xzCompress(int level, const unsigned char *data, size_t avail_in, unsigned char *odata, size_t *avail_out)
{
   uint32_t preset = COMPRESSION_LEVEL | (COMPRESSION_EXTREME ? LZMA_PRESET_EXTREME : 0);
   lzma_check check = INTEGRITY_CHECK;
   lzma_stream strm = LZMA_STREAM_INIT;

   lzma_action action;
   lzma_ret ret_xz;

   ret_xz = lzma_easy_encoder (&strm, preset, check);
//   printf("RET %d\n", ret_xz);

   action = LZMA_FINISH;

   strm.avail_in = avail_in;
   strm.next_in = data;

   strm.next_out = odata;
   strm.avail_out = *avail_out;

   ret_xz = lzma_code (&strm, action);
//   printf("RET %d\n", ret_xz);
//   printf("%d %d\n", *avail_out, strm.avail_out);

   *avail_out -= strm.avail_out;

   lzma_end (&strm);

   return 0;
}
