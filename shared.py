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
from functools import partial
import re
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter.font import Font
import subprocess
import webbrowser

import file_handler
import ttips

try:
    import version
    VERSION     = version.VERSION   # version file, use for executable releases
except ModuleNotFoundError:
    VERSION     = '0.04.13'         # version, date based, for script only releases

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

TEST = in_args( '/t', '-t', 't', 'test')
# DEVICE_TEST = in_args( '/d', '-d', 'd', 'device')

COLOURS         = ["00", "40", "80", "FF"]              # colours available on Virpil devices
CONFIG_FILE     = "conf.json"
DEFAULT_COMMAND = 1                             # default command
LANG_FILE       = "lang.$.json"
LANG_FILE_NAME  = LANG_FILE.replace("$", "*")
LINK    = 'https://github.com/Painter602/EDLogReader/issues'
LOG_FILE        = "Journal"
LOG_FILTER      = ['*', '', 'Alpha', 'Beta', 'Gamma' ]    # Gamma release very rare/never used?
LOG_SUFFIX      = "*.log"
PROG_NAME       = sys.argv[0].split('\\')[-1].split('.')[0]
SHOW_HELP       =  'help' in (x.lower() for x in sys.argv) or '/h' in (x.lower() for x in sys.argv)

config          = []
instructions    = {}
language        = 'en'
state           = {}


class About():
    def __init__(self, master=None, title='', message=None, program='', *ret):
        # master=window,
        # title=f'{PROG_NAME} - {title}',
        # message=message
        # super().__init__( )
        self.window = tk.Toplevel()
        self.master=master
        self.ret=False
        self.window.deiconify()
        if len( program.strip() ) == 0:
            program = title.strip()
        
        if len(title):
            self.window.title( title )
        elif master is not None:
            self.window.title( master[ 'title' ] )

        label = None
        if isinstance( message, str ):
            label = tk.Label( self.window, text=message, justify='left', padx=20, pady=20)
            label.pack()
            label.bind('<Double-1>', partial( webbrowser.open, f'{LINK}'))
        elif isinstance( message, list ):
            frm = tk.Frame(master=self.window)
            for txt in message:
                if txt == LINK:
                    label = tk.Label( self.window, text=txt, justify='left')
                    label.pack(fill=tk.X)
                    font = Font(label, label.cget("font"))
                    font.configure(underline = True)
                    label.configure( font=font )
                    label.bind('<Button-1>', partial( webbrowser.open, f'{LINK}'))
                    ttips.Create( label, 'Click to open the link in your browser', bgcol='#fdfdfd' )
                elif txt == VERSION:
                    label = tk.Label( self.window, text=program, justify='right', anchor='e')
                    label.pack(fill=tk.X, padx=20, pady=20)
                    font = Font(label, label.cget("font"))
                    font.configure(underline = True)
                    label.configure( font=font )
                    label.bind('<Button-1>', partial( self.copy ))
                    ttips.Create( label, 'Click to copy the program\'s name to your clip-board', bgcol='#fdfdfd' )
                else:
                    tk.Label( self.window, text=txt, justify='left', anchor='w').pack(fill=tk.X, padx=20, pady=0)
            frm.pack(padx=20, pady=(20,0))
            
        frm_btn = tk.Frame(master=self.window )

        ok_btn = make_button( frm_btn,
                              "OK",
                              partial( self.btn_press, False),
                              tooltip='Close this About window' )
        # ok_btn[ 'width' ] = len( prog_name )
        ok_btn.pack(fill=tk.BOTH)
        frm_btn.pack(pady=( 0, 20 ))

        self.window.grab_set()

    def btn_press( self, value=False ):
        self.ret = value
        self.window.destroy()

    def copy(self, event):
        copy2clip( f'{state[ "full_name" ]}')

    def show(self):
        self.window.wait_window()
        return self.ret

def copy2clip(txt):
    cmd= f'echo {txt.strip()} |clip'
    subprocess.run( cmd, shell=True )

def expand_commands(jsn_txt):
    '''
    expand commands
    '''
    places          = 2
    commands= []
    for line in jsn_txt[ 'commands' ]:
        if len( line ) == 1:
            commands.append( line[ 0 ] )
        else:
            e_num = 0
            for d_num in range( line[ 1 ], line[ 2 ]+1 ):
                e_num += 1
                d_str = f"{('0' * places)}{d_num}"[-places:]
                e_str = f"{('0' * places)}{e_num}"[-places:]
                commands.append( line[ 0 ].replace( '{d}', d_str).replace( '{e}', e_str) )
    if TEST:
        for cmd in commands:
            print(cmd)
    return commands

def log( module, function, txt ):
    ''' Write errors to a log file, to help track them '''
    log_file = open( f'{PROG_NAME}.log', 'a', encoding="utf-8" )
    log_file.write(   f'{datetime.utcnow()} UTC\t'
                        f'{os.path.splitext(module)[ 0 ]} . '
                        f': {function}\t\t{txt}\n' )
    log_file.flush()
    os.fsync(log_file.fileno())
    log_file.close()

def load_languages():
    '''
    read the language files
    '''

    languages = {}

    # same folder for lang files used to be in the same folder
    # now, they can have their own sub-folder
    lang_file_list = ( glob.glob(f"{LANG_FILE_NAME}") +
                       glob.glob(f"lang\\{LANG_FILE_NAME}") )
    if len( lang_file_list ) == 0:
        timeout( 'No language files found' )

    found_en = False
    for fname in lang_file_list:
        found_en = re.search("\S*.en.\S*", fname )
        if found_en:
            break
    if not found_en:
        timeout( 'We need file lang\\lang.en.json' )

    for file_name in lang_file_list:
        if TEST:
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
    return languages

def main():
    '''
    run module as a stand-alone program
    '''
    languages = load_languages()
    for lang in languages:
        print( f'{lang}:' )
        for xlate in languages[ lang ]:
            if xlate == 'commands':
                print()
                for cmd in languages[ lang ][ xlate ]:
                    print( f'\t{ cmd } ' )
            else:
                print( f'\t{xlate}: { languages[ lang ][ xlate ] }' )

def make_button(frm, text, command, side=tk.LEFT, tooltip=''):
    ''' Make a simple button '''
    if isinstance(text, tk.StringVar):
        button = tk.Button(frm,
                           textvariable=text,
                           command=command )
    else:
        button = tk.Button(frm,
                           text=f' {text} ',
                           command=command )
    button.pack(side=side)

    if len( tooltip ) > 0:
        ttips.Create( button, tooltip, bgcol='#eeeeee' )
    return button

def make_string(txt, master=None ):
    ''' Make a string variable '''
    tlate = tk.StringVar(master=master)
    tlate.set( translate(txt, language ) )
    return tlate

def timeout( message ):
    ''' show a warning before closing the script '''
    win = tk.Tk()
    messagebox.showerror( "Error", message, master=win )
    win.destroy()
    sys.exit(0)

def translate( txt, lang=language ):
    ''' take a lookup key (txt), and provide a translation
        in language lang, or English, or default to txt '''
    # txt = txt.lower( )
    if lang not in translate.unused:
        translate.unused[ lang ] = {}
    if txt in translate.unused[ lang ]:
        translate.unused[ lang ].pop( txt )
    if txt in translate.languages[ lang ]:
        return translate.languages[ lang ][ txt ]

    # note missing translations
    if lang not in translate.missing:
        translate.missing[ lang ] = []
    # and record it in the log (without duplication - at least, for this run)
    if not txt in translate.missing[ lang ]:
        translate.missing[ lang ].append( txt )
        log( f'{file_handler.module_name(__file__)} v{VERSION}',
             'translate',
             f'translation missing ({lang}): {txt}' )

    if lang != 'en':
        return translate( txt, lang='en' )
    return txt

translate.missing = {}
translate.unused = {}
translate.languages = load_languages()

def unused():
    ''' list unused translations '''
    for not_used in translate.unused:
        log( f'{file_handler.module_name(__file__)} v {VERSION}', 'unused', f'{translate.unused[not_used]}' )

if __name__ == '__main__':
    main()
