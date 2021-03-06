# This file is part of Elsim
#
# Copyright (C) 2019, Sebastian Bachmann <hello at reox.at>
# All rights reserved.
#
# Elsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Elsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Elsim.  If not, see <http://www.gnu.org/licenses/>.
"""
Generic Filters for the use with Elsim
"""
from operator import itemgetter

def filter_sort_meth_basic(element, similar_elements, value):
    """
    This filter sorts the items and returns the
    most similar item, if the threshold is reached.

    it returns a list with exactly one entry.

    :param float value: the threshold which must be reached to be "interesting"
    """
    # Sort all items by the value, which is the distance
    z = sorted(similar_elements.items(), key=itemgetter(1))

    if z == []:
        # This Element has no similar items
        return []

    if z[:1][0][1] > value:
        return []

    # The first item will be the one with the lowest distance, i.e. the most similar
    return z[:1]

class FilterNone:
    """
    A Filter which never filters anything
    """
    @staticmethod
    def skip(element):
        return False


class FilterEmpty:
    """
    This filter removes all empty or only whitespace elements
    """
    @staticmethod
    def skip(element):
        if element in (b'', b' '):
            return True

        return False
