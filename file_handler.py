''' making executables with py2exe we mai have problems with __file__ ''

import os
import sys

def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""
    return hasattr(sys, "frozen")


def module_name( file ):   # use __file__ from the calling module
    """ This will get us the program's directory,
        even if we are frozen using py2exe"""
    if we_are_frozen():
        return os.path.basename( sys.executable).split('.')[ 0 ]
    return os.path.basename( file ).split('.')[ 0 ]

def module_path( file ):   # use __file__ from the calling module
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))
