"""
Generic Filters for the use with Elsim
"""

def filter_sim_value_meth(value):
    """
    Returns 1 if v is larger than 0.2
    """
    return 1.0 if value >= 0.2 else value


class FilterNone:
    """
    A Filter which never filters anything
    """
    @staticmethod
    def skip(element):
        return False
