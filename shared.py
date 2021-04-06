"""
Functions to be shared between EDLogReader and a proposed Configuration set-up script


Licence:
=======
    VPC-LED_Controller - Script to change the LEDs on
    Virpil conrollers in responce to events in Elite Dangerous (game)
    Copyright (C) 2021, Painter602

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""

from datetime import datetime
import glob
import json
import os
import sys

def in_args( *args ):
    '''
    Check whether flags are given in the run-time/run-line arguments
    '''
    flags = []
    for arg in args:
        flags.append( arg )
    ret = False
    for flag in flags:
        ret = ret or flag in (x.lower() for x in sys.argv)
        ret = ret or f'{flag}s' in (x.lower() for x in sys.argv)
    return ret

BTEST = in_args( '/t', 'test')
DEVICE_TEST = in_args( '/d', 'device')

COLOURS = ["00", "40", "80", "FF"]   # colours available on Virpil devices
CONFIG_FILE = "conf.json"
DEFAULT_COMMAND = 1                      # default command
LOG_FILE = "Journal.*.log"
LANG_FILE = "lang.$.json"
LANG_FILE_NAME = LANG_FILE.replace("$", "*")
PROG_NAME = sys.argv[0].split('\\')[-1].split('.')[0]
SHOW_HELP =  'help' in (x.lower() for x in sys.argv) or '/h' in (x.lower() for x in sys.argv)

config = []
instructions = {}
PLACES = 2

def expand_commands(jsn_txt):
    '''
    expand commands
    '''
    commands= []
    for line in jsn_txt[ 'commands' ]:
        if len( line ) == 1:
            commands.append( line[ 0 ] )
        else:
            e_num = 1
            for d_num in range( line[ 1 ], line[ 2 ]+1 ):
                d_str = f"{('0' * PLACES)}{d_num}"[-PLACES:]
                e_str = f"{('0' * PLACES)}{e_num}"[-PLACES:]
                commands.append( line[ 0 ].replace( '{d}', d_str).replace( '{e}', e_str) )
    if BTEST:
        for cmd in commands:
            print(cmd)
    return commands

def error( module, txt ):
    error_file = open( f'{PROG_NAME}.log', 'a' )
    error_file.write( f'{datetime.utcnow()} UTC\t\tModule: {module}\t\t{txt}\n' )
    error_file.flush()
    os.fsync(error_file.fileno())
    error_file.close()
    

def load_languages():
    '''
    read the language files
    '''

    languages = {}

    lang_file_list = sorted( glob.glob(f"{LANG_FILE_NAME}") )

    for file_name in lang_file_list:
        if BTEST:
            print( file_name )
        try:
            lang_file = open(file_name,"r", encoding="utf-8")
        except:
            # failed to open language file
            continue
        txt = lang_file.read().replace('\n', '')
        lang_file.close()
        jsn_txt = json.loads( txt )
        jsn_txt[ 'commands' ] = expand_commands( jsn_txt )
        languages[ jsn_txt[ 'code' ]] = jsn_txt
        if BTEST:
            print(languages[ jsn_txt[ 'code' ]])
    return languages

def main():
    '''
    run module as a stand-alone program
    '''
    languages = load_languages()
    for language in languages:
        print( f'{language}:' )
        for xlate in languages[ language ]:
            if xlate == 'commands':
                print()
                for cmd in languages[ language ][ xlate ]:
                    print( f'\t{ cmd } ' )
            else:
                print( f'\t{xlate}: { languages[ language ][ xlate ] }' )

if __name__ == '__main__':
    main()
