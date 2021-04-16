''' Install EdLogReader
    Used to compile the script from within Python
    The primary benifit is one script can compile many versions of the
    language (assuming they are compatible)
'''

import glob
import os
import PyInstaller.__main__
import re
import set_env
import shutil
import sys

import version

def docopy(src, dest):
    for file_name in glob.glob( src ):
        file_name = ''.join( '/'.join( file_name.split( '\\' ) ).split( './') )
        shutil.copy( file_name, f'{dest}/{file_name}' )

def paths(py_local):
    ''' set distribution path based on executable size (32 bit/ 64 bit) '''
    bit = 32
    if sys.maxsize > 2**32:
        bit = 64
    return (f'./build_{py_local}', f'../{py_local}_{bit}bit', f'{bit}bit')

def install(spec, distpath='./dist'):
    ''' now build the executable '''

    PyInstaller.__main__.run([
        '--windowed',
        '--onefile',
        f'--distpath={distpath}',
        spec
        ])

def remove( path ):
    ''' remove a folder and all its contents '''
    try:
        shutil.rmtree( path )
    except FileNotFoundError:
        pass

def set_environment():
    ''' make sure the run-time environmenmt is consistent '''
    exPath = sys.executable.split('\\')
    exPath[ -1 ] = ''               # don't just pop it here!
    py_local = exPath[ -2 ]
    
    exPath = '\\'.join( exPath )
    set_env.set_env(exPath)
    return py_local

def main(project='EdLogReader'):
    ''' main process '''
    py_local = set_environment()
    (my_build_path, my_dist_path, build_type) = paths(py_local)
    project_path = f'{my_dist_path}/{project}'

    print( 'Removing old folders' )
    remove( my_dist_path )
    remove( my_build_path )
    remove( './build' )

    print( 'Installing new executable' )
    install( f'{project}.spec', my_dist_path )

    print( 'Copying data files' )
    for direct in ['lang', ]:
        os.makedirs( f'{project_path}/{direct}' )
    docopy('./lang/*.json', f'{project_path}' )
    docopy('./*.json', f'{project_path}' )
    docopy('./*.md', f'{project_path}' )
    docopy('./*.txt', f'{project_path}' )

    # don't distribute a Microsoft .dll, so remove it
    try:
        os.remove( f'{my_dist_path}/VCRUNTIME140.dll' )
    except FileNotFoundError:
        pass    # we don't care why not

    print( f'Path for zip file: {my_dist_path}/../zip' )
    try:
        os.makedirs( f'{my_dist_path}/../zip' )
    except FileExistsError:
        pass

    print( 'Removing old zip file' )
    try:
        os.remove( f'{my_dist_path}/../zip/{project}_v{version.VERSION}_{build_type}.zip' )
    except FileNotFoundError:
        pass    # we don't care why not
    print( 'Zipping project' )
    shutil.make_archive(f'{my_dist_path}/../zip/{project}_v{version.VERSION}_{build_type}', 'zip', f'{project_path}')
    
    print( 'Moving local build folder' )
    shutil.move('./build', my_build_path)

    print( 'Copying local configuration file(s)' )
    for direct in ['local',]:
        os.makedirs( f'{project_path}/{direct}' )
    docopy( './local/*.json', f'{project_path}' )


if __name__ == '__main__':
    main()
