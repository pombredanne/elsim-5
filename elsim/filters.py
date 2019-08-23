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

    if z[:1][0][1] > value:
        return []

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
