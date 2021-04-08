"""
A module to track events in Elite Dangerous, and set the
LEDs on Virpil Controls in responce to those events
"""
from datetime import datetime, timedelta
from functools import partial
import glob
import json
import os
import queue
import random
import subprocess
import sys
import time
from threading import Thread
import tkinter as tk
from tkinter import messagebox

import list_joysticks
import shared as edlr

PROG_NAME =  edlr.PROG_NAME

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

ABOUT = ('About '+ PROG_NAME + '\n\n'
         'Written by Painter602\n\n'
         'For now, contact me through github (https://github.com/Painter602/EDLogReader)\n'
         'Or message me on Virpil\'s forum\n\n'
         'Copyright (C) 2021, Painter602\n\n'
         )

BTEST =             edlr.BTEST
COLOURS =           edlr.COLOURS            # colour values
DEFAULT_COMMAND =   edlr.DEFAULT_COMMAND    # default command
DEVICE_TEST =       edlr.DEVICE_TEST
RTEST =             edlr.RTEST

HELP = ( PROG_NAME + ' Help\n'
         '==============\n'
         'You may run this script with NO parameters, and it should read your\r'
         'Elite Dangerous log files, and respond by changing the LED colours\r'
         'displayed on your Virpil Devices.\n\n'
         'Note: your configuration file may need modification before that works.\n'
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
    ''' placeholder to store shared/static variables (globals) '''
static.b_done_start = False
static.joysticks = {}
static.running=False
static.skip_test = False
static.test_devices = False
# main_window = None
static.labels = {}

def do_colour( device, cmd=None):
    '''
    set colours for a device
    '''
    if not device in static.joysticks:
        return

    if not device in config.config[ 'devices' ]:
        return

    now_time = datetime.utcnow()
    if not device in do_colour.next_colour_time:
        do_colour.next_colour_time[ device ] = datetime(1900, 1, 1)     # never run before
    if now_time < do_colour.next_colour_time[ device ]:
        return

    if cmd is None:
        cmd={0: {'Red': 0, 'Green': 0, 'Blue': 0}}
    for key in cmd:
        dev_id  = f"{config.config[ 'devices' ][ device ][ 'id' ]}"
        red     = f'{COLOURS[ cmd[ key ]["Red"]]}'
        green   = f'{COLOURS[ cmd[ key ]["Green"]]}'
        blue    = f'{COLOURS[ cmd[ key ]["Blue"]]}'

        run = f"\"{config.config[ '__pathToLEDControl__' ]}\" {dev_id} {key} {red} {green} {blue}"
        # update( main.window, f'Sent to {device}: {i} {red} {green} {blue}',
        #        count_max=1, show_counter=False )
        if BTEST:
            print( run )

        subprocess.Popen( run, creationflags=subprocess.CREATE_NEW_CONSOLE )
    t_delta = timedelta(milliseconds=config.config[ "timedeltaMs" ])
    do_colour.next_colour_time[ device ] = now_time + t_delta

do_colour.next_colour_time = {}    # initialise next_colour_time

def do_reset():
    ''' Reset a'' devices to default values '''
    manage( '{ "event":"Default" }' )
    return True

def help_mssg( args=None):
    ''' Display a message in a mesage box '''
    if args is not None:
        (window, title, txt) = args
        message = txt.replace('\r', ' ').replace('\t\\', '\t')
        messagebox.showinfo(master=window,
                            title=f'{PROG_NAME} - {title}',
                            message=message)

def reset_height( ctrl, height_max, range_max=20 ):
    ''' Set the height of the text box '''
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
    ''' Set the width of the text box '''

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
    ''' Skip (or stop) testing commands '''
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
    ''' A window to show events and warnings, primarily in the early stages of the script '''
    lines = 0

    def __init__(self):
        self.closing = False
        self.window = tk.Tk()
        self.window.title(f'{PROG_NAME}')
        self.menu()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.set_queue()

        self.frm = tk.Frame(master=self.window, bd=10)
        self.title = tk.Label( self.frm, text="Start Up Test")
        self.title.pack()
        self.tbx = tk.Text(self.frm, height=20, width=70, padx=5, pady=5)
        self.tbx.pack(fill=tk.X)
        self.lbl = tk.Label( self.frm, text="Command    of    ")
        self.lbl.pack(side=tk.LEFT)
        self.frm.pack(fill=tk.X)
        frm = tk.Frame(master=self.window, bd=5)

        self.skip_button = make_button( frm, "Device Test", self.device_test )
        # make_button( frm, "Exit", self.stop) # stop_running )

        frm.pack()
        thread = Thread(target = partial(threaded_function, self))
        thread.daemon = True
        thread.start()
        self.window.mainloop()
        static.running = False
        thread.join()

    def device_test(self):
        ''' toggle request to test devices '''
        static.test_devices = not static.test_devices
        if static.test_devices:
            self.skip_button[ 'relief' ] = tk.SUNKEN
            update( self, 'Device test starting in a few seconds', 0, -1 )
        else:
            self.skip_button[ 'relief' ] = tk.RAISED
            update( self, 'Device test stopping in a few seconds', 0, -1 )

    def set_queue(self):
        ''' create a message queue, and start watching it '''
        self.update_queue = queue.Queue()
        self.window.after(100, self.update_listen_for_result)

    def menu(self):
        ''' create menus '''
        window = self.window
        self.menu_bar = tk.Menu( master=window )

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        menu_list = {}
        menu_list[ 'Exit' ] = self.stop
        make_menu( file_menu, menu_list )
        make_string( 'file', window )
        self.menu_bar.add_cascade(label=static.labels[ 'file' ].get(), menu=file_menu, underline=0)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        menu_list = {   'help': partial( help_mssg, (window, 'help', HELP)),
                        'license': partial( help_mssg, (window, 'license', LICENSE )),
                        'about': partial( help_mssg, (window, 'about', ABOUT)) }
        make_menu( help_menu, menu_list )
        make_string( 'help', window )
        self.menu_bar.add_cascade(label=static.labels[ 'help' ].get(), menu=help_menu, underline=0)

        window.config( menu=self.menu_bar )

    def missing(self, missing ):
        ''' display missing/unconnected devices '''
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
            # self.window.mainloop()
            sys.exit( 0 )

    def button_skip(self):
        ''' Stop processing, and (if possible) disable the button to do this '''
        static.skip_test = True
        try:
            self.skip_button['state'] = tk.DISABLED
        except tk.TclError:
            pass

    def on_closing( self ):
        ''' Ensure program variables are set to reflect the lack of a window '''
        self.stop()

    def set_title( self, text ):
        ''' Set or change the message above the text box '''
        try:
            self.title[ 'text' ] = text
        except tk.TclError:
            pass

    def stop( self ):
        ''' Prepare this window to be closed, destroy the window '''
        set_skip_test(True)
        self.closing = True
        try:
            self.window.destroy()
        except tk.TclError:     # likely this has been destroyed already
            pass

    def update( self, txt, counter=0, count_max=0, show_command_counter=True):
        ''' Update the window, by showing new text '''
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

        if show_command_counter:
            if count_max > 0:
                # self.lbl = tk.Label( self.frm, text=f"Command {counter} of {count_max}")
                self.lbl[ 'text' ] = f"Command {counter} of {count_max}"
            elif count_max < 0:
                self.lbl[ 'text' ] = ''
            else:
                #self.lbl = tk.Label( self.frm, text=txt)
                self.lbl[ 'text' ] = txt
        else:
            self.lbl[ 'text' ] = ''

        self.lbl.pack()
        self.frm.update()
        self.window.update()

    def update_listen_for_result( self ):
        """ Check if there is something in the queue. """
        try:
            (func, args) = self.update_queue.get(0)
            if func == self.update:     # is this the function
                ( txt, counter, count_max, show_command_counter ) = args
                self.update( txt, counter, count_max, show_command_counter)
            elif func == self.missing:  # is this the function
                self.missing( args )
            else:
                func()
            self.window.after(100, self.update_listen_for_result)
        except queue.Empty:
            self.window.after(100, self.update_listen_for_result)

def device_test(main_window):
    ''' Display the colour combination for each event to be displayed '''
    len_inst = len( instructions )

    ctr = 0
    update( main_window, '', ctr, len_inst )
    update( main_window, 'Device Test', ctr, len_inst )
    update( main_window, '===========', ctr, len_inst )
    for instr in instructions:
        if not static.test_devices:
            break
        if not static.running:
            break

        ctr += 1
        manage( '{"event":"' + instr + '"}' )           # send command to devices
        update( main_window, instr, ctr, len_inst )     # show which command
        time.sleep(4)

    if static.test_devices:
        main_window.update_queue.put( (main_window.device_test, () ))

    update( main_window, '', ctr, len_inst )
    update( main_window, 'Device Test Stopped', ctr, len_inst )
    update( main_window, '===================', ctr, len_inst )
    update( main_window, '', ctr, len_inst )



def do_start(main_window):
    ''' Handle start up routines '''
    if static.b_done_start:
        return True
    static.running = True

    missing = []

    find_joysticks()
    for instr in instructions:
        for ins in instructions[ instr ]:
            if not ins in static.joysticks:
                if ins not in missing:
                    missing.append( ins )

    if len( missing ) > 0:
        main_window.update_queue.put( (main_window.missing, missing ))
        return False
    do_reset()
    static.b_done_start = True
    return True

def find_joysticks():
    ''' find devices currently attached '''
    for stick in list_joysticks.list_joy_sticks():
        static.joysticks[ stick[ 'oem_name' ] ] = stick

def follow(the_file, main_window):
    ''' generator function that yields new lines in a file '''
    if not BTEST:
        # seek the end of the file
        the_file.seek(0, os.SEEK_END)

    follow.cycle = 0
    is_reset = False

    # start infinite loop
    while static.running:
        if static.test_devices:
            return

        # read last line of file
        line = the_file.readline()

        # sleep if file hasn't been updated
        if line:
            follow.cycle = 0
            is_reset = False
            yield line
            continue

        if not is_reset:
            if follow.cycle > config.config[ "resetTime" ]:
                is_reset = do_reset()

        if follow.cycle > config.config[ 'timeOut' ]: # 60:  we have had a minute of inaction
            return                              #  - maybe we need a different file?

        if static.running:
            time.sleep(config.config[ 'sleepTime' ])
        else:
            return

        follow.cycle += config.config[ 'sleepTime' ]
        refresh = config.config[ "timeOut" ]- follow.cycle + config.config[ "sleepTime" ]
        if refresh >= 0:
            txt = f'Scanning ED {edlr.LOG_FILE} files '
            txt = f'{txt} (file refreshes in {refresh}s if no new events)'
        else:
            txt = f'Scanning ED {edlr.LOG_FILE} files'
        update( main_window, txt, 0, 1, False )      #, instr, ctr, len_inst )

def make_button(frm, text, command, side=tk.LEFT):
    ''' Make a simple button '''
    button = tk.Button(frm,
              text=f' {text} ',
              command=command )
    button.pack(side=side)
    return button

def make_menu( menu, menulist ):
    ''' make a drop down menu list '''
    master = menu
    while hasattr( master, 'master'):
        master = master.master

    for item in menulist:
        if menulist[ item ] is None:
            menu.add_separator()
        else:
            if item == item.lower():
                make_string( item, master=master )
                label = static.labels[ item ].get()
            else:
                label = item
            menu.add_command(label=label, command=menulist[ item ])

def manage( line ):
    ''' with a line from the game log, arrange to send colour instructions to devices '''
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
            print( f'{k}: -> {instructions[ data [ "event" ] ][ k ]}' )
            do_colour( k, cmd=instructions[ data [ 'event' ] ][ k ])

def random_colour( colour_list=None ):
    ''' Generate random colour codes '''
    if colour_list is None:
        colour_list = []
        for colour in range( len( COLOURS ) ):
            colour_list.append( colour )
    return { 'Red': random.choice(colour_list),
             'Green': random.choice(colour_list),
             'Blue': random.choice(colour_list)}

def config():
    ''' Read configuration file, and store values in memory '''

    config_file = open(f"{edlr.CONFIG_FILE}","r")

    for line in config_file:
        data = json.loads(line)
        if 'Config' in data:
            config.config = data['Config']
            if 'language' in config.config:
                edlr.language = config.config['language']
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

def make_string( key, master ):
    ''' make a string varaiable '''
    static.labels[ key ] = edlr.make_string( key, master )

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

def update( window, txt, counter=0, count_max=0, show_counter=True ):
    '''
    Refresh window (while it is there)
    '''
    # try:
    window.update_queue.put( (window.update, ( txt, counter, count_max, show_counter ) ))
    # except tk.TclError:
    #    static.running = False

def threaded_function(main_window):
    '''
    Heart beat of the main process:
        Keeps checking the log files,
        and sending commands to joy sticks
    '''

    config()
    read_logs = do_start(main_window)
    if not read_logs:
        return
    ## main.window.button_skip()
    ## if read_logs:
    ##    main.window.set_title( 'Scanning ED Logs' )
    while static.running:
        if static.test_devices:
            device_test(main_window)

        log_file_list = sorted( glob.glob(f"{config.config['__fPath__']}"
                                          f"{edlr.LOG_FILE}"
                                          f"{edlr.LOG_SUFFIX}"
                                          ))
        if len( log_file_list ) == 0:
            messagebox.showinfo(
                master=main_window.window,
                title=f'{PROG_NAME} Warning',
                message='No Elite Dangerous log files were found\nPlease check your file path')
            main_window.update_queue.put( (main_window.stop, () ))
            break

        file_path = f"{log_file_list[ -1 ]}"
        file_name = file_path.split('\\' )[ -1 ].split('/' )[ -1 ]
        update( main_window, f'Checking {file_name}', count_max=1, show_counter=False )

        log_file = open(file_path,"r")
        log_lines = follow(log_file, main_window)
        for line in log_lines:
            manage(line)
        log_file.close()

        if static.running:
            if RTEST:
                print( f'sleep {config.config[ "sleepTime" ]}' )
            time.sleep(config.config[ 'sleepTime' ])

def main():
    ''' Main process '''
    Window()
    # edlr.unused()

if __name__ == '__main__':
    main()
