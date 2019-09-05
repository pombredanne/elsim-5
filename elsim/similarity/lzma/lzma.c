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
#include "lzma.h"

#include "LzmaLib.h"

int lzmaCompress(int level, const unsigned char *data, size_t avail_in, unsigned char *odata, size_t *avail_out)
{
   unsigned char outProps[5];
   size_t outPropsSize = 5;

   return LzmaCompress( odata, avail_out, data, avail_in, outProps, &outPropsSize, level, 0, -1, -1, -1, -1, -1 );
}
