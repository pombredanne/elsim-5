"""
Generic Filters for the use with Elsim
"""

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
