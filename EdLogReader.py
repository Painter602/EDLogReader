"""
A module to track events in Elite Dangerous, and set the
LEDs on Virpil Controls in responce to those events

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

import list_joysticks
import shared as edlr

BTEST = edlr.BTEST
COLOURS = edlr.COLOURS      # colour values
DEFAULT_COMMAND = edlr.DEFAULT_COMMAND            # default command
DEVICE_TEST = edlr.DEVICE_TEST
PROG_NAME = sys.argv[0].split('\\')[-1].split('.')[0]
SHOW_HELP = edlr.SHOW_HELP

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

def set_skip_test( set_skip=True ):
    '''
    Skip (or stop) testing commands
    '''
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
        ttl = f'{PROG_NAME} - Start Up'     #   "ED Log Reader - Start Up"
        self.closing = False
        self.window = tk.Tk()
        self.window.title(ttl)
        self.frm = tk.Frame(master=self.window, bd=10)
        lbl = tk.Label( self.frm, text="Start Up Test")
        lbl.pack()
        self.tbx = tk.Text(self.frm, height=5, width=40, padx=5, pady=5)
        self.tbx.pack(fill=tk.X)
        self.lbl = tk.Label( self.frm, text="Command    of    ")
        self.lbl.pack(side=tk.LEFT)
        self.frm.pack(fill=tk.X)
        frm = tk.Frame(master=self.window, bd=5)
        button_txt = "Quit"   #   "Close Window"
        if len( missing ):
            button_txt = "Exit"
            button = tk.Button(frm, text=f' {button_txt} ', command=self.close_down)
            button.pack()
        else:
            button_skip = "Skip Device Test"
            button = tk.Button(frm,
                               text=f' {button_skip} ',
                               command=partial( set_skip_test, True) )
            button.pack(side=tk.LEFT)
            button = tk.Button(frm, text=f' {button_txt} ', command=stop_running)
            button.pack()
        frm.pack()
        self._do_missing( missing )
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _do_missing(self, missing ):
        if len( missing ):
            mssg_top    = [" ",
                           "Devices are Missing:",
                           "====================",
                           ""]
            mssg_bottom = ["",
                           "This may be caused by:",
                           "",
                           "A config file may have changed,",
                           "   or become corrupted", "",
                           "Or a device may be unplugged -",
                           "    check your devices",
                           "",
                           "This program will end when","   the window closes"]
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
            self.window.mainloop()
            sys.exit( 0 )

    def on_closing( self ):
        '''
        Ensure program variables are set to reflect the lack of a window
        '''
        self.close()

    def close( self ):
        '''
        Prepare this window to be closed, destroy the window
        '''
        if not static.skip_test:
            set_skip_test(True)
        self.closing = True
        # self.update("Closing Window" )
        # time.sleep(2)
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

    def update( self, txt, counter=0, count_max=0, show_command_counter=True):
        '''
        Update the window, by showing new text
        '''
        if count_max:
            txt_table = self.tbx.get("1.0", "end")
            reset_height( self.tbx, count_max )
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
        return
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

    window = None
    window = Window( missing )
    if len( missing ) > 0:
        return

    # Display the colour combination for each event to be displayed
    len_inst = len( instructions )


    for path in ('fPath', 'pathToLEDControl'):
        set_path( path )

    ctr = 0
    for instr in instructions:
        if not DEVICE_TEST:
            break
        if static.skip_test:
            break
        if not static.running:
            break
        ctr += 1

        update( window, instr, ctr, len_inst )              # show which command

        manage( '{"event":"' + instr + '"}' )   # send command to devices
        time.sleep(2)

    window.close()

    do_reset()
    static.b_done_start = True

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
    while True:
        if BTEST:
            # check every line, but give a chance for the responce to be noted
            #   this can take a while to process, especially at the start of the
            #   file, bear with it.
            if test_sleep:
                time.sleep( test_sleep )
        # read last line of file
        #try:
        line = thefile.readline()
        #except Exception as err:
        #    print( f'Exception: {err}' )
        #    continue
        if BTEST:
            test_sleep = 0
            print( line )
            if 'event' in line:
                data = json.loads(line)
                if data[ 'event' ] in instructions:
                    test_sleep = 2

        # sleep if file hasn't been updated
        if not line:
            if not is_reset:
                if cycle > config.config[ "resetTime" ]:
                    is_reset = do_reset()
            if cycle > config.config[ 'timeOut' ]: # 60:  we have had a minute of inaction
                return                      #  - maybe we need a different file?
            time.sleep(config.config[ 'sleepTime' ])
            cycle += config.config[ 'sleepTime' ]
            if BTEST:
                print( ".", end=' ' )
            continue

        cycle = 0
        is_reset = False
        yield line

def manage( line ):
    '''
    with a line from the game log, arrange to send colour instructions to devices
    '''
    data = json.loads(line)

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

    # cva = [ 0, 1, 2, 3 ]
    config_file = open(f"{edlr.CONFIG_FILE}","r")

    # dNow = datetime.utcnow() - timedelta(milliseconds=1000)

    for line in config_file:
        data = json.loads(line)
        if 'Config' in data:
            config.config = data['Config']
            for device in config.config[ 'devices' ]:
                if not 'cmdCount' in config.config[ "devices" ][ device ]:
                    config.config[ "devices" ][ device ][ 'cmdCount' ] = 1
                # static.next_colour_time[ device ] = dNow
            if BTEST:
                print( f'config: {config.config}' )
        if not 'Interest' in data:
            continue
        if data[ 'Interest' ] == 0:
            continue
        if data[ 'Event' ] >= "DockingRequested":
            # exit(0)
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
    if BTEST:
        for event in instructions:
            print( f'Event {event}: {instructions[ event ]}' )

def set_path( path_key ):
    '''
    Set paths based on information in the config file
    '''
    # p = r.split(".")[ -1 ]
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
        my_help = ( '\n\n' + PROG_NAME + '\n'
                 'Help has yet to be written\n'
                 '===========================\n'
                 'In the mean time, you can run this script with '
                 'NO parameters, and it should read your Elite Dangerous '
                 'log files, and respond by changing the LED colours '
                 'displayed on your Virpil Devices\n\n'
                 'Note: your configuration file may need modification before that works\n\n\n'
                 'Optional command line parameters\n'
                 '--------------------------------\n'
                 '/h or help      - show this help\n'
                 '/d or device(s) - open a window and test devices before reading the game log\n'
                 '/t or test      - read an existing log file from the front, and show device\n'
                 '                  LEDs based on that file\'s data\n\n'
                 'Note, a lot of test information is printed out to your command window or\n'
                 'the IDLE test window (if relevant)'
                 '\n\n'
            )
        print(my_help)
        sys.exit(0)

def update( window, txt, counter=0, count_max=0 ):
    '''
    Refresh window (while it is there)
    '''
    try:
        window.update( txt, counter, count_max )
    except tk.TclError as error:
        print( f'Error: {error}' )

def threaded_function():
    '''
    Heart beat of the main process:
        Keeps checking the log files,
        and sending commands to joy sticks
    '''
    # global b_running
    do_start()
    while static.running:
        log_file_list = sorted( glob.glob(f"{config.config['__fPath__']}{edlr.LOG_FILE}") )
        log_file = open(f"{log_file_list[ -1 ]}","r")

        log_lines = follow(log_file)


        for line in log_lines:
            manage(line)
        log_file.close()
        time.sleep(config.config[ 'sleepTime' ])
    # window.close()
    sys.exit(0)

def main():
    '''
    Main process
    '''
    show_help()
    config()
    thread = Thread(target = threaded_function)
    thread.daemon = True
    thread.start()
    thread.join()

if __name__ == '__main__':
    main()
