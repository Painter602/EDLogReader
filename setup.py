from distutils.core import setup
import glob
import os
import py2exe
import shutil

dist_dir    =   '../distribute'

setup(
    windows=['EdLogReader.py'],
    options={
        "py2exe":{
            'dist_dir' : dist_dir
            }
        }
    )

for sufx in ['txt', 'json', 'md' ]:
    gfiles  = glob.glob( f'*.{sufx}' )
    for file in gfiles:
        shutil.copy(file, dist_dir)
