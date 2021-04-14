''' set up file for compiuling with py2exe '''
''' Note: as far as I can tell, py2exe is 64 bit only '''

from distutils.core import setup
import glob
import os
import py2exe
import shutil

# distribute to an adjacent folder
dist_dir    =   '../distribute'

# make a windows only .exe (no consol)
setup(
    windows=['EdLogReader.py'],
    options={
        "py2exe":{
            'dist_dir' : dist_dir
            }
        }
    )

# and copy related/support stuff over
#
for sufx in ['txt', 'json', 'md' ]:
    gfiles  = glob.glob( f'*.{sufx}' )
    for file in gfiles:
        shutil.copy(file, dist_dir)
