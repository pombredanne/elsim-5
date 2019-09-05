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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#ifdef __cplusplus
#include <string>
#include <snappy.h>

using namespace std;

extern "C" size_t snappy_max_compressed_size(size_t length) {
   return snappy::MaxCompressedLength(length);
}

extern "C" void snappy_compress(const char * input, size_t input_size, char * output, size_t *avail_out)
{
   //printf("COMPRESS 0x%x %d 0x%x %d\n", input, input_size, output, *avail_out);
   snappy::RawCompress(input, input_size, output, avail_out);
}

extern "C" void snappy_decompress(const char * input, size_t input_size, char * output, size_t *avail_out)
{
   //printf("COMPRESS 0x%x %d 0x%x %d\n", input, input_size, output, *avail_out);
   snappy::RawUncompress(input, input_size, output); //, avail_out);
}

#endif

extern "C" int snappyCompress(int level, const unsigned char *data, size_t avail_in, unsigned char *odata, size_t *avail_out)
{
   size_t max_comp_size;

   //printf("DATA = 0x%x %d 0x%x %d\n", data, avail_in, odata, *avail_out);

   max_comp_size = snappy_max_compressed_size( avail_in );
   //printf("MAX_COMP_SIZE = %d\n", max_comp_size); 

   // FIXME
   if (max_comp_size > *avail_out) {

   }

   snappy_compress((char *)data, avail_in, (char *)odata, avail_out);

   return 0;
}

extern "C" int snappyDecompress(int level, const unsigned char *data, size_t avail_in, unsigned char *odata, size_t *avail_out) {
   snappy_decompress((char *)data, avail_in, (char *)odata, avail_out);

   return 0;
}
