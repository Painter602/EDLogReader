"""
A module to track events in Elite Dangerous, and set the
LEDs on Virpil Controls in responce to those events
"""
from datetime import datetime, timedelta
from functools import partial
import glob
import json
import os
import random
import subprocess
import sys
import time
from threading import Thread
import tkinter as tk
from tkinter import messagebox

import list_joysticks
import shared as edlr

PROG_NAME =         sys.argv[0].split('\\')[-1].split('.')[0]

LICENCE = ('\n'
           'Licence:\n'
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

BTEST =             edlr.BTEST
COLOURS =           edlr.COLOURS            # colour values
DEFAULT_COMMAND =   edlr.DEFAULT_COMMAND    # default command
DEVICE_TEST =       edlr.DEVICE_TEST
RTEST =             edlr.RTEST
SHOW_HELP =         edlr.SHOW_HELP

HELP = ( '\n\n' + PROG_NAME + ' Help\n'
         '==============\n'
         'You may run this script with NO parameters, and it should read your\r'
         'Elite Dangerous log files, and respond by changing the LED colours\r'
         'displayed on your Virpil Devices.\n\n'
         'Note: your configuration file may need modification before that works.\n\n\n'
         'Optional command line parameters\n'
         '--------------------------------\n'
         '/h or help\t\\- show this help\n'
         '/d or device(s)\t\\- test devices before reading the game log\n'
         # '/r or running-test\t- test main running\n'
         # '/t or test\t\t- read an existing log file from the front,\n'
         # '\t\t\\  and show device LEDs based on that file\'s\n'
         # '\t\t\\  data\n\n'
         # 'Note: In test mode, a lot of test information is printed out to your command\r'
         # 'window.'
         '\n\n'
         )
# HELP: when displaying HELP on command line windows
#       replace carriage return (\r) with new line (\n)
#       replace double back slash (\\) with tab (\t)
#
#       when displaying HELP in a messagebox
#       replace carriage return (\r) with space when displaying HELP in a messagebox
#       and delete double back slash (\\)
#
# Essentially, line wrapping occures in different places and tabs are of different length

instructions = edlr.instructions    # dictionary of available commands (filled at run time)

def static():
    '''
    placeholder to store shared/static variables (globals)
    '''
static.b_done_start = False
static.joysticks = {}
static.running=False
static.skip_test = False

def do_colour( device, cmd=None):
    '''
    set colours for a device
    '''
    if cmd is None:
        cmd={'Red': 0, 'Green': 0, 'Blue': 0}

    if not device in static.joysticks:
        return

    if not device in config.config[ 'devices' ]:
        return

    now_time = datetime.utcnow()
    if not device in do_colour.next_colour_time:
        do_colour.next_colour_time[ device ] = datetime(1900, 1, 1)     # never run before
    if now_time < do_colour.next_colour_time[ device ]:
        return

    dev_id  = f"{config.config[ 'devices' ][ device ][ 'id' ]}"
    for i in cmd:
        red     = f'{COLOURS[ cmd[ i ]["Red"] ]}'
        green   = f'{COLOURS[ cmd[ i ]["Green"] ]}'
        blue    = f'{COLOURS[ cmd[ i ]["Blue"] ]}'

        run = f"\"{config.config[ '__pathToLEDControl__' ]}\" {dev_id} {i} {red} {green} {blue}"
        # update( main.window, f'Sent to {device}: {i} {red} {green} {blue}',
        #        count_max=1, show_counter=False )
        if BTEST:
            print( run )

        subprocess.Popen( run, creationflags=subprocess.CREATE_NEW_CONSOLE )
    t_delta = timedelta(milliseconds=config.config[ "timedeltaMs" ])
    do_colour.next_colour_time[ device ] = now_time + t_delta

do_colour.next_colour_time = {}    # initialise next_colour_time

def do_reset():
    '''
    Reset a'' devices to default values
    '''
    manage( '{ "event":"Default" }' )
    return True

def help_mssg( args=('Help',HELP)):
    '''
    Display a message in a mesage box
    '''
    (title, txt) = args
    message = txt.replace('\r', ' ').replace('\t\\', '\t')
    messagebox.showinfo(master=main.window.window,
                        title=f'{PROG_NAME} - {title}',
                        message=message)

def reset_height( ctrl, height_max, range_max=20 ):
    '''
    Set the height of the text box
    '''
    if height_max > range_max:
        height_max = range_max
    if height_max > ctrl[ 'height' ]:
        ctrl[ 'height' ] = height_max
        ctrl.pack()
        master = ctrl
        while master.master:
            master = master.master
            try:
                master.pack()
            except AttributeError:
                pass

def reset_width( ctrl, width_min ):
    '''
    Set the width of the text box
    '''

    if width_min > 100:
        width_min = 100

    if width_min >= ctrl[ 'width' ]:
        ctrl[ 'width' ] = width_min + 1
        ctrl.pack()
        master = ctrl
        while master.master:
            master = master.master
            try:
                master.pack()
            except AttributeError:
                pass

def set_skip_test( set_skip=True ):
    '''
    Skip (or stop) testing commands
    '''
    if set_skip:
        try:
            main.window.button_skip()
        except AttributeError:
            pass
    static.skip_test = set_skip

def stop_running():
    '''
    Set a flag to stop running this script
    '''
    static.running = False

class Window:
    '''
    A window to show events and warnings, primarily in the early stages of the script
    '''
    lines = 0

    def __init__(self, missing):
        self.closing = False
        self.window = tk.Tk()
        self.window.title(f'{PROG_NAME}')
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.frm = tk.Frame(master=self.window, bd=10)
        self.title = tk.Label( self.frm, text="Start Up Test")
        self.title.pack()
        self.tbx = tk.Text(self.frm, height=20, width=70, padx=5, pady=5)
        self.tbx.pack(fill=tk.X)
        self.lbl = tk.Label( self.frm, text="Command    of    ")
        self.lbl.pack(side=tk.LEFT)
        self.frm.pack(fill=tk.X)
        frm = tk.Frame(master=self.window, bd=5)

        self.skip_button = make_button( frm, "Skip Device Test", self.button_skip )
        make_button( frm, "Help", partial( help_mssg, ('Help', HELP) ) )
        make_button( frm, "Licence", partial( help_mssg, ('Licence', LICENCE ) ) )

        if len( missing ):
            make_button( frm, "Exit", self.close_down )
        else:
            make_button( frm, "Exit", stop_running )

        frm.pack()
        self._do_missing( missing )

    def _do_missing(self, missing ):
        if len( missing ):
            mssg_top    = [" ",
                           "Devices are Missing:",
                           "====================",
                           ""]
            mssg_bottom = ["", "",
                           "This may be caused by:",
                           "",
                           "The config file may have changed,",
                           "   or become corrupted", "",
                           "Or a device may be unplugged -",
                           "    check your devices",
                           "",
                           "This program will end", "when the window closes",
                           ""]
            len_inst = len( missing ) + len( mssg_top ) + len( mssg_bottom )
            ctr = 0
            for mssg in mssg_top:
                ctr += 1
                self.update( mssg, ctr, len_inst, False )
            for missed in missing:
                ctr += 1
                self.update( f'   {missed}', ctr, len_inst, False )
            for mssg in mssg_bottom:
                ctr += 1
                self.update( mssg, ctr, len_inst, False )
            self.tbx.config( bg="#ff0" )
            self.tbx.master.config( bg="#000" )
            self.button_skip()
            self.window.mainloop()
            sys.exit( 0 )

    def button_skip(self):
        '''
        Stop processing, and (if possible) disable the button to do this
        '''
        static.skip_test = True
        try:
            self.skip_button['state'] = tk.DISABLED
        except tk.TclError:
            pass

    def on_closing( self ):
        '''
        Ensure program variables are set to reflect the lack of a window
        '''
        self.close()

    def close( self ):
        '''
        Prepare this window to be closed, destroy the window
        '''
        set_skip_test(True)
        self.closing = True
        try:
            self.window.destroy()
        except tk.TclError:     # likely this has been destroyed already
            pass

    def close_down( self ):
        '''
        Prepare to close this window and exit the program
        '''
        stop_running()
        self.close()

    def set_title( self, text ):
        '''
        Set or change the message above the text box
        '''
        try:
            self.title[ 'text' ] = text
        except tk.TclError:
            pass

    def update( self, txt, counter=0, count_max=0, show_command_counter=True):
        '''
        Update the window, by showing new text
        '''
        if count_max:
            txt_table = self.tbx.get("1.0", "end")
            reset_height( self.tbx, count_max )
            reset_width( self.tbx, len( txt ) )
            if len( txt_table ) > 1:
                self.tbx.insert( tk.END, '\n' )
                self.lines += 1
            if self.lines > self.tbx[ 'height' ]:
                self.tbx.delete( "1.0", "2.0" )
            self.tbx.insert( tk.END, txt )

        try:
            self.lbl.destroy()
        except tk.TclError:
            pass
        if show_command_counter:
            if count_max:
                self.lbl = tk.Label( self.frm, text=f"Command {counter} of {count_max}")
            else:
                self.lbl = tk.Label( self.frm, text=txt)
            self.lbl.pack(side=tk.LEFT)
        self.frm.update()
        self.window.update()

def do_start():
    '''
    Handle start up routines
    '''
    if static.b_done_start:
        return True
    static.running = True

    missing = {}

    find_joysticks()
    for instr in instructions:
        for ins in instructions[ instr ]:
            if not ins in static.joysticks:
                if ins in missing:
                    missing[ ins ] += 1
                else:
                    missing[ ins ] = 1

    main.window = Window( missing )
    if len( missing ) > 0:
        return False

    # Display the colour combination for each event to be displayed
    len_inst = len( instructions )

    ctr = 0
    for instr in instructions:
        if not DEVICE_TEST:
            break
        if static.skip_test:
            break
        if not static.running:
            break

        ctr += 1
        update( main.window, instr, ctr, len_inst )     # show which command
        manage( '{"event":"' + instr + '"}' )           # send command to devices
        time.sleep(2)

    do_reset()
    static.b_done_start = True
    return True

def find_joysticks():
    '''
    find devices currently attached
    '''
    for stick in list_joysticks.list_joy_sticks():
        static.joysticks[ stick[ 'oem_name' ] ] = stick

def follow(thefile):
    '''
    generator function that yields new lines in a file
    '''

    test_sleep = 0

    if not BTEST:
        # seek the end of the file
        thefile.seek(0, os.SEEK_END)
    cycle = 0
    is_reset = False

    # start infinite loop
    while static.running:
        if RTEST:
            # check every line, but give a chance for the responce to be noted
            #   this can take a while to process, especially at the start of the
            #   file, bear with it.
            if test_sleep:
                time.sleep( test_sleep )

        # read last line of file
        line = thefile.readline()
        if RTEST:
            test_sleep = 0
            print( line )
            if 'event' in line:
                data = json.loads(line)
                if data[ 'event' ] in instructions:
                    test_sleep = 2

        # sleep if file hasn't been updated
        if line:
            cycle = 0
            is_reset = False
            yield line
            continue

        if not is_reset:
            if cycle > config.config[ "resetTime" ]:
                is_reset = do_reset()

        if cycle > config.config[ 'timeOut' ]: # 60:  we have had a minute of inaction
            return                              #  - maybe we need a different file?

        if static.running:
            time.sleep(config.config[ 'sleepTime' ])
        else:
            return
        cycle += config.config[ 'sleepTime' ]
        refresh = config.config[ "timeOut" ]- cycle + config.config[ "sleepTime" ]
        txt = f'Scanning ED log file (file refreshes in {refresh}s if no new events)'
        update( main.window, txt, 0, 1, False )      #, instr, ctr, len_inst )

        if RTEST:
            print( ".", end=' ' )

def make_button(frm, text, command, side=tk.LEFT):
    '''
    Make a simple button
    '''
    button = tk.Button(frm,
              text=f' {text} ',
              command=command )
    button.pack(side=side)
    return button

def manage( line ):
    '''
    with a line from the game log, arrange to send colour instructions to devices
    '''
    try:
        data = json.loads(line)
    except json.decoder.JSONDecodeError:
        # I'm getting an intermittent error here - need to see the cause
        print( line )
        return

    if data[ "event" ] in instructions:
        for k in instructions[ data [ "event" ] ]:
            if BTEST:
                print( f'{k}: -> {instructions[ data [ "event" ] ][ k ]}' )
            do_colour( k, cmd=instructions[ data [ 'event' ] ][ k ])

def random_colour( colour_list=None ):
    '''
    Generate random colour codes
    '''
    if colour_list is None:
        colour_list = []
        for colour in range( len( COLOURS ) ):
            colour_list.append( colour )
    return { 'Red': random.choice(colour_list),
             'Green': random.choice(colour_list),
             'Blue': random.choice(colour_list)}

def config():
    '''
    Read configuration file, and store values in memory
    '''

    config_file = open(f"{edlr.CONFIG_FILE}","r")

    for line in config_file:
        data = json.loads(line)
        if 'Config' in data:
            config.config = data['Config']
            for device in config.config[ 'devices' ]:
                if not 'cmdCount' in config.config[ "devices" ][ device ]:
                    config.config[ "devices" ][ device ][ 'cmdCount' ] = 1
            if BTEST:
                print( f'config: {config.config}' )
        if not 'Interest' in data:
            continue
        if data[ 'Interest' ] == 0:
            continue
        if data[ 'Event' ] >= "DockingRequested":
            pass

        actions = {}
        for key in data:
            if key in ['Event', 'Interest']:
                continue
            if isinstance(data[ key ], (dict, str) ):
                data[ key ] = [ data[ key ], ]

            if not key in actions:
                actions[ key ] = {}

            for data_list in data[ key ]:
                if data_list == 'random':
                    data_list = random_colour()
                for list_item in data_list:
                    if data_list[ list_item ] == 'random':
                        # ? unreachable ?
                        data_list[ list_item ] = random_colour()
                        print ( 'random drill' )
                        sys.exit( 0 )

                    # and handle potential user issues with colours

                    if list_item != "cmd":
                        for colour in ['Red', 'Green', 'Blue' ]:
                            if not colour in data_list:
                                data_list[ colour ] = 0
                            elif data_list[ colour ] >= len( COLOURS ):
                                data_list[ colour ] = len( COLOURS )-1
                if 'cmd' not in data_list:
                    data_list[ 'cmd' ] = DEFAULT_COMMAND
                if data[ 'Event' ] == 'Default':
                    data_list[ 'cmd' ] = 0
                if isinstance( data_list[ 'cmd' ], list ):
                    for list_item in data_list[ 'cmd' ]:
                        actions[ key ][ list_item ] = data_list
                else:
                    actions[ key ][ data_list[ 'cmd' ] ] = data_list
        instructions[ data[ 'Event' ] ] = actions

    for path in ('fPath', 'pathToLEDControl'):
        set_path( path )

    if BTEST:
        for event in instructions:
            print( f'Event {event}: {instructions[ event ]}' )

def set_path( path_key ):
    '''
    Set paths based on information in the config file
    '''
    new_key = f'__{path_key}__'

    if not new_key in config.config:
        path = ""
        term_list = config.config[ path_key ].split("%")
        for term in term_list:
            if len( term ):
                try:
                    env_t = os.getenv(term)
                    path += env_t
                except TypeError:
                    path += term
        config.config[ new_key ] = path

def show_help():
    '''
    Display a help message, then exit the script
    '''
    if SHOW_HELP:
        message = HELP.replace('\r', '\n').replace('\\', '\t')
        print(message)
        sys.exit(0)

def update( window, txt, counter=0, count_max=0, show_counter=True ):
    '''
    Refresh window (while it is there)
    '''
    try:
        window.update( txt, counter, count_max, show_counter )
    except tk.TclError:
        static.running = False

def threaded_function():
    '''
    Heart beat of the main process:
        Keeps checking the log files,
        and sending commands to joy sticks
    '''
    read_logs = do_start()
    main.window.button_skip()
    if read_logs:
        main.window.set_title( 'Scanning ED Logs' )
    while static.running:
        if not read_logs:
            time.sleep( 1 )
            continue

        log_file_list = sorted( glob.glob(f"{config.config['__fPath__']}{edlr.LOG_FILE}") )
        if len( log_file_list ) == 0:
            messagebox.showinfo(
                title=f'{PROG_NAME} Warning',
                message='No Elite Dangerous log files were found\nPlease check your file path')
            static.running = False
            break

        file_path = f"{log_file_list[ -1 ]}"
        file_name = file_path.split('\\' )[ -1 ].split('/' )[ -1 ]
        update( main.window, f'Checking {file_name}', count_max=1, show_counter=False )

        log_file = open(file_path,"r")
        log_lines = follow(log_file)
        for line in log_lines:
            manage(line)
        log_file.close()

        if RTEST:
            print( f'sleep {config.config[ "sleepTime" ]}' )
        time.sleep(config.config[ 'sleepTime' ])

    main.window.close()
    sys.exit(0)

def main():
    '''
    Main process
    '''

    main.window = None
    show_help()
    config()
    thread = Thread(target = threaded_function)
    thread.daemon = True
    thread.start()
    thread.join()

if __name__ == '__main__':
    main()
