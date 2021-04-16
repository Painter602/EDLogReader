'''
Draft script
'''
import sys
import tkinter as tk
from tkinter import ttk

import list_joysticks
import shared
import ttips

try:
    import version
    VERSION     = version.VERSION               # version file, use for executable releases
except ModuleNotFoundError:
    VERSION     =   f'v0.04.13:{edlr.VERSION}'  # version, date based, for script only releases

PROG_NAME =  shared.PROG_NAME
FULL_NAME   = f'{PROG_NAME} v {VERSION}'
LICENSE = ('License:\n'
           '=======\n'
           + PROG_NAME + ', a script to change the LEDs on '
           'Virpil conrollers in responce to events in Elite Dangerous (game)\n'
           'Copyright (C) 2021, Painter602\n\n'
           'This program is free software; you can redistribute it and/or modify '
           'it under the terms of the GNU General Public License as published by '
           'the Free Software Foundation; either version 2 of the License, or '
           '(at your option) any later version.\n\n'

           'This program is distributed in the hope that it will be useful, '
           'but WITHOUT ANY WARRANTY; without even the implied warranty of '
           'MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the '
           'GNU General Public License for more details.\n\n'

           'You should have received a copy of the GNU General Public License along '
           'with this program; if not, write to\nthe Free Software Foundation, Inc., '
           '51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.'
           )
LINK    =   shared.LINK

ABOUT = [   ' ',
            (  'About '+ PROG_NAME + '\n\n'
               'Written by Painter602\n'
               'If needed, you can contact me through github:'),
            LINK,
            (   '\n\n'
                'Thank-you to Fixitman for testing and for his change suggestions'
                '\n\nCopyright (C) 2021, Painter602\t\t\t'
                ),
            VERSION]

COLOURS         =   shared.COLOURS            # colour values
DEFAULT_COMMAND =   shared.DEFAULT_COMMAND    # default command
TEST            =   shared.TEST

HELP = ( PROG_NAME + ' Help\n'
         '==============\n'
         'This script should read your Elite Dangerous log files, and respond'
         'by changing the LED colours\r'
         'displayed on your Virpil Devices.\n\n'
         'Note: your configuration file may need modification before that works.\n'
         )

class MainWindow():
    ''' Well, that's what it is '''
    def __init__(self, master=None):
        self.window = tk.Toplevel(master=master)
        self.window.title(PROG_NAME)
        self.make_menus()
        self.make_tabs()
        self.window.mainloop()

    def joysticks( self, master ):

        js_list = []

        print( f'{static.joysticks}' )
        print( shared.translate.languages[ shared.language ][ 'commands' ] )
        for option in (
            shared.translate.languages[ shared.language ][ 'commands' ] ):
            js_list.append( option )

        
        frame = tk.Frame( master )
        tk.Label( frame, text='Device', ).grid( row=0, column=0, sticky=tk.W)
        tk.Label( frame, text='VID', width=4 ).grid( row=0, column=1, sticky=tk.W )
        tk.Label( frame, text='PID', width=4 ).grid( row=0, column=2, sticky=tk.W )
        column=2
        for key in shared.translate.languages[ shared.language ][ 'range' ]:
            (base, size) = shared.translate.languages[ shared.language ][ 'range' ][ key ]
            if size > 1:
                column += 1
                tk.Label( frame, text=key ).grid( row=0, column=column, padx=2 )
        row = 0
        for js in static.joysticks:
            row += 1
            tk.Label( frame, text=js, anchor='e' ).grid( row=row, column=0, sticky=tk.W )
            tk.Label( frame, text=static.joysticks[ js ][ 'vid' ] ).grid( row=row, column=1, sticky=tk.W )
            tk.Label( frame, text=static.joysticks[ js ][ 'pid' ] ).grid( row=row, column=2, sticky=tk.W )

            column= 2
            for key in shared.translate.languages[ shared.language ][ 'range' ]:
                (base, size) = shared.translate.languages[ shared.language ][ 'range' ][ key ]
                if size > 1:
                    column += 1
                    int_val = tk.IntVar(master=self.window, value=0, name=f'{js}_{key}')
                    int_entry = tk.Spinbox(frame, width=4, textvariable=int_val, from_=0, to=size)
                    int_entry.grid( row=row, column=column )
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        #self.contentframe.grid_columnconfigure(0, weight=1)
        #self.contentframe.grid_rowconfigure(0, weight=1)
        #self.topBar.grid_columnconfigure(0, weight=1)
        #self.topBar.grid_rowconfigure(0, weight=1)
        frame.pack(padx=20, pady=(10,20))

    def make_menus(self):
        pass

    def make_tabs(self):
        self.tab_frame = {}
        tabcontrol = ttk.Notebook( self.window )

        tabs = {'event': None, 'joystick': self.joysticks, 'config': None }

        for tab in tabs:
            self.tab_frame[ tab ] = ttk.Frame( tabcontrol )
            tabcontrol.add( self.tab_frame[ tab ], text=tab )
            if tabs[ tab ] is not None:
                tabs[ tab ]( self.tab_frame[ tab ] )
        tabcontrol.pack(expand=True, fill="both")        

def static():
    ''' a placeholder for global variables '''
    pass
static.joysticks = {}
static.config = {}

def load_config():
    pass

def load_joysticks():
    joysticks = list_joysticks.list_joy_sticks()
    sorted_js = sorted(joysticks, key=lambda kv: f"{kv['oem_name']} {kv['joy_id']}")
    static.joysticks = {}
    for js in sorted_js:
        refresh_joystick( js )

def refresh_joystick( js ):
    n = 0
    jnm = js[ 'oem_name' ]
    while jnm in static.joysticks:
        n+=1
        jnm = f'{js[ "oem_name" ]} ({n})'
    js[ 'oem_name' ] = jnm

    static.joysticks[ js[ 'oem_name' ] ] = {
        'vid'           : js[ 'vid' ],
        'pid'           : js[ 'pid' ],
        'range'         : {'board': -1, 'master': -1, 'slave': -1},
        'connected'     : True
        }
    
def set_value( field, value ):
    if isinstance(field, tk.Variable ):
        field.set( value )
        return field
    return value

def main():
    load_joysticks()
    load_config()
    MainWindow()

if __name__ == '__main__':
    main()
