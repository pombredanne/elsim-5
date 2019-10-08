from androguard.core import androconf
from androguard.misc import AnalyzeAPK, AnalyzeDex

def load_analysis(filename):
    """Return an AnalysisObject depding on the filetype"""
    ret_type = androconf.is_android(filename)
    if ret_type == "APK":
        _, _, dx = AnalyzeAPK(filename)
        return dx
    if ret_type == "DEX":
        _, _, dx = AnalyzeDex(filename)
        return dx
    return None

