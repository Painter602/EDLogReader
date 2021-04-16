'''
Draft script
'''
import tkinter as tk
from tkinter import ttk

import list_joysticks
import shared

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
    def __init__(self):
        self.window = tk.Tk()
        self.window.title(PROG_NAME)
        self.make_menus()
        self.make_tabs()

    def joysticks( self, master ):

        js_list = []

        print( f'{static.joysticks}' )
        print( shared.translate.languages[ shared.language ][ 'commands' ] )
        for option in (
            shared.translate.languages[ shared.language ][ 'commands' ] ):
            js_list.append( option )
        
        lbl_width = 0
        for js in static.joysticks:
            lbl_width = max( lbl_width, len( js ) )

        
        frame = tk.Frame( master )
        tk.Label(   frame, text='Device',
                    width=lbl_width, anchor='e' ).pack(
                        side=tk.LEFT)
        tk.Label( frame, text='VID', width=4 ).pack( side=tk.LEFT) 
        tk.Label( frame, text='PID', width=4 ).pack( side=tk.LEFT)
        tk.Label( frame, text='Is LED\nDevice', width=6 ).pack( side=tk.LEFT)
        tk.Label( frame, text='JS', width=4 ).pack( side=tk.LEFT)
        tk.Label( frame, text='Master', width=6 ).pack( side=tk.LEFT)
        tk.Label( frame, text='Slave', width=6 ).pack( side=tk.LEFT)
        frame.pack(expand=True, fill=tk.X)
        
        for js in static.joysticks:
            frame = tk.Frame( master )
            tk.Label( frame, text=js, width=lbl_width, anchor='e' ).pack(
                side=tk.LEFT)
            tk.Label( frame, text=static.joysticks[ js ][ 'vid' ] ).pack(
                side=tk.LEFT)
            tk.Label( frame, text=static.joysticks[ js ][ 'pid' ] ).pack(
                side=tk.LEFT)
            if isinstance( static.joysticks[ js ][ 'led_device' ], bool ):
                static.joysticks[ js ][ 'led_device' ] = tk.BooleanVar(
                    master=self.window,
                    value=static.joysticks[ js ][ 'led_device' ] )
            tk.Checkbutton( frame,
                         variable=static.joysticks[ js ][ 'led_device' ],
                            text='',
                            width=6, anchor='c'
                         ).pack(side=tk.LEFT)
            menubutton = tk.Menubutton( frame, text='Ranges' )
            menu = tk.Menu( menubutton, tearoff=False )
            menubutton.configure( menu=menu )
            menubutton.pack()
            for choice in js_list:
                static.joysticks[ js ][ 'range' ][ choice ] = (
                    tk.IntVar( value=-1 ) )
                menu.add_checkbutton(
                    label=choice,
                    variable=static.joysticks[ js ][ 'range' ][ choice ],
                    onvalue=int(choice[1:2]), offvalue=-1 )
            
            frame.pack(expand=True, fill=tk.X)

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
    for js in static.joysticks:
        static.joysticks[ js[ 'oem_name' ] ][ 'visible' ] = (
            set_value(
                static.joysticks[ js[ 'oem_name' ] ][ 'visible' ],
                False )
            )
    for js in joysticks:
        refresh_joystick( js )

def refresh_joystick( js ):
    if js[ 'oem_name' ] in static.joysticks:
        static.joysticks[ js[ 'oem_name' ] ][ 'connected' ] = (
            set_value(
                static.joysticks[ js[ 'oem_name' ] ][ 'connected' ],
                True )
            )
    else:
        static.joysticks[ js[ 'oem_name' ] ] = {
            'vid'           : js[ 'vid' ],
            'pid'           : js[ 'pid' ],
            'led_device'    : False,
            'range'         : {},
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
