''' A script to reset environment variables based on the run-time executable

    When compiling for different versions of Python, this is used to reset
    Windows PATH, to (try and) avoid picking up the wrong module versions

'''

import os
import re
import sys
from local import env

'''
PATH_TO_38_64 = env.PATH_TO_38_64
PATH_TO_38_32 = env.PATH_TO_38_32       # these might be more efficient
PATH_TO_39_32 = env.PATH_TO_39_32       # in an array a set or list
PATH_TO_39_64 = env.PATH_TO_39_64       # but, readability ???
'''

PATHS   = env.PATHS

def substitute( path, pold, pnew ):
    ''' replace text '''
    return path.replace( pold, pnew )

def set_env( target ):
    ''' main function, changed the environment PATH
        for this run (if required) and return the new
    '''

    target_list = {}
    for p in PATHS:
        p = p.replace( '/', '\\' )
        sreplace = p.replace("\\","\\\\")
        target_list[ p ] = re.compile( f'^{sreplace}\S*' )
    '''
    sreplace = PATH_TO_39_32.replace("\\","\\\\")
    p_39_32 = re.compile( f'^{sreplace}\S*' )
    sreplace = PATH_TO_39_64.replace("\\","\\\\")
    p_39_64 = re.compile( f'^{sreplace}\S*' )

    target_list = { PATH_TO_38_32: p_38_32,
                    PATH_TO_39_32: p_39_32,
                    PATH_TO_39_64: p_39_64
                    }
    '''

    path_list = []
    for path in os.environ[ 'PATH' ].split(';'):
        for py_ver in target_list:
            if target_list[ py_ver ].match( path ):
                path_list.append(
                    substitute( path, py_ver, target ) )

    os.environ[ 'PATH' ] = ';'.join( path_list )
    return os.environ[ 'PATH' ]

if __name__ == '__main__':
    set_env( 'python' )
    # set_env( 'some_python_folder\\' )   # ideally, one of PATH_TO_38_32,
                                        # PATH_TO_39_32, PATH_TO_39_64
    print( f'PATH = {os.environ[ "PATH" ]}' )

