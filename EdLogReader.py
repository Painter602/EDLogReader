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
import ttips

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
         'Thank-you to Fixitman for testing and for his change suggestions'
         )

TEST            =   edlr.TEST
COLOURS         =   edlr.COLOURS            # colour values
DEFAULT_COMMAND =   edlr.DEFAULT_COMMAND    # default command
VERSION         =   '0.01a'                 # version numbers will probably slip
MAX_LINES       =   500

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

def state():
    ''' placeholder to store shared/static variables (globals) '''
state.archive_files = False
state.b_done_start  = False
state.block_follow  = False
state.file_filter   = edlr.LOG_FILTER[ 0 ]
state.joysticks     = {}
state.queue_ms      = 50
state.labels        = {}
state.last_txt      = ''
state.pause         = False
state.reset         = False
state.running       = False
state.skip_test     = False
state.test_devices  = False

########################################################################
class Window:
    ''' A window to show events and warnings, primarily in the early stages of the script '''
    def __init__(self):
        self.window = tk.Tk()
        self.window.title(f'{PROG_NAME}')
        self.menu()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        make_string( ['pause','resume'], master=get_master( self.menu_bar ) )
        self.make_frames()
        self.window.minsize(600, 425)
        self.set_queue()

        self.stop_update = False
        self.in_update = False
        self.next_update = datetime(1900, 1, 1)     # initialising, first run this session

        thread = Thread(target = partial(threaded_function, self))
        thread.daemon = True
        thread.start()
        self.reset_title()

        self.window.mainloop()
        state.running = False
        thread.join()

    def archive_files( self ):
        ''' toggle read archived log files '''
        # prevent true double presses
        self.skip_button[ 'state' ] = tk.DISABLED
        self.history_button[ 'state' ] = tk.DISABLED

        state.archive_files = not state.archive_files
        wait_queue( self, 60 )
        if state.archive_files:
            # self.skip_button[ 'state' ] = tk.DISABLED
            self.history_button[ 'relief' ] = tk.SUNKEN
            self.update( 'Start reading older logs', 0, -1 )
            wait_queue( self, timeout=10 )
            self.reset_title()
        else:
            self.history_button[ 'relief' ] = tk.RAISED
            self.update( 'Start reading current log', 0, -1 )
            wait_queue( self, timeout=10 )
            self.reset_title()
            self.skip_button[ 'state' ] = tk.NORMAL
        set_state_reset( True )
        # allow ro run now
        time.sleep( 0.5 )   # adsorb (some) key bounces
        self.history_button[ 'state' ] = tk.NORMAL

    def button_skip(self):
        ''' Stop processing, and (if possible) disable the button to do this '''
        state.skip_test = True
        try:
            self.skip_button['state'] = tk.DISABLED
        except tk.TclError:
            pass

    def device_test(self):
        ''' toggle request to test devices '''
        # prevent true double presses
        self.skip_button[ 'state' ] = tk.DISABLED
        self.history_button[ 'state' ] = tk.DISABLED

        state.test_devices = not state.test_devices
        wait_queue( self, 60 )
        if state.test_devices:
            # self.history_button[ 'state' ] = tk.DISABLED
            self.skip_button[ 'relief' ] = tk.SUNKEN
            update( self, 'Device test will start in a few seconds', 0, -1 )
            wait_queue( self, timeout=10 )
            self.set_title( "Testing Devices" )
        else:
            self.skip_button[ 'relief' ] = tk.RAISED
            update( self, 'Device test will stop in a few seconds', 0, -1 )
            wait_queue( self, timeout=10 )
            self.reset_title()
            self.history_button[ 'state' ] = tk.NORMAL
        # allow ro run now
        self.skip_button[ 'state' ] = tk.NORMAL

    def make_frames(self):
        ''' build the windows (and buttons) used '''
        self.title = tk.Label( master=self.window, text="Loading")
        self.title.pack()
        tfrm = tk.Frame(master=self.window, padx=10)
        self.scroll = tk.Scrollbar( tfrm )
        self.tbx = tk.Text(tfrm, width=70, height=20, padx=5, pady=20) #  height=20,
        self.scroll.pack( side=tk.RIGHT, fill=tk.Y, expand=True)
        self.tbx.pack(fill=tk.BOTH, expand=True)
        tfrm.pack(fill=tk.BOTH, expand=True)
        self.scroll.config( command=self.tbx.yview )
        self.tbx.config( yscrollcommand=self.scroll.set )

        frm_btm = tk.Frame(master=self.window, padx=10, bd=5)
        self.lbl = tk.Label( self.window, text="Command    of    ", anchor='w', padx=10)
        self.lbl.pack(fill=tk.X, side=tk.LEFT, expand=True)

        bfrm = tk.Frame(frm_btm, bd=5)
        lbl = tk.Label( self.window, text="Test buttons:", anchor='e')
        lbl.pack(side=tk.LEFT)
        self.skip_button = make_button( bfrm,    " Device Test ",
                                        self.device_test,
                                        tooltip='Just your devices,\nignoring your log files' )
        self.history_button = make_button(
                bfrm,
                "Use Old Files",
                self.archive_files,
                tooltip=( 'Test devices by reading your old log files.\n'
                          'Note: events are much closer in time with\n'
                          'this test, and there is more output so processing\n'
                          'has been slowed down' ) )
        self.btn_pause = make_button(  bfrm,
                                       state.labels[ 'pause' ],
                                       self.pause,
                                       tooltip = 'Pause / Resume' )
        # reserve width to show the label
        self.btn_pause[ 'width' ] = len( state.labels[ 'pause' ].get() )
        # but show the pause option
        state.labels[ 'pause' ].set( edlr.translate( 'pause' ) )
        bfrm.pack(fill=tk.X)

        frm_btm.pack(side=tk.BOTTOM, fill=tk.X)

    def menu(self):
        ''' create menus '''
        window = self.window
        self.menu_bar = tk.Menu( master=window )

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        menu_list = {}
        for file_filter in edlr.LOG_FILTER:
            if file_filter == '':
                label = 'live_game'
            elif file_filter == '*':
                label = 'latest_default'
            else:
                if not file_check( file_filter ):
                    continue
                label = file_filter
            menu_list[ label ] = partial(set_filter, (self, file_filter))
        menu_list[ 'none' ] = None
        menu_list[ 'Exit' ] = self.stop
        make_menu( file_menu, menu_list )
        make_string( 'file', window )
        self.menu_bar.add_cascade(label=state.labels[ 'file' ].get(), menu=file_menu, underline=0)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        menu_list = {   'help': partial( help_mssg, (window, 'help', HELP)),
                        'license': partial( help_mssg, (window, 'license', LICENSE )),
                        'about': partial( help_mssg, (window, 'about', ABOUT)) }
        make_menu( help_menu, menu_list )
        make_string( 'help', window )
        self.menu_bar.add_cascade(label=state.labels[ 'help' ].get(), menu=help_menu, underline=0)

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
            sys.exit( 0 )

    def on_closing( self ):
        ''' Ensure program variables are set to reflect the lack of a window '''
        self.stop()

    def pause( self ):
        ''' switch between paused and running '''
        state.pause = not state.pause

        if state.pause:
            state.labels[ 'pause' ].set( edlr.translate( 'resume' ) )
            self.tbx[ 'bg' ] = "#ffd"   # visual feed-back that our state has changed
        else:
            state.labels[ 'pause' ].set( edlr.translate( 'pause' ) )
            self.tbx[ 'bg' ] = "#fff"   # normal background

    def qsize( self ):
        ''' return the current size of the update queue '''
        return self.update_queue.qsize()

    def reset_title(self, qualifier=None):
        ''' Reset title based on the file filter '''
        if qualifier is None:
            if state.archive_files:
                qualifier='Reading Old Files'
            else:
                qualifier='Scanning latest game file'
        if state.file_filter == '':
            title = f'{qualifier} - release version'
        elif state.file_filter == '*':
            title = qualifier
        else:
            title = f'{qualifier} - {state.file_filter} version'
        self.set_title( title )

    def set_queue(self):
        ''' create a message queue, and start watching it '''
        self.update_queue = queue.SimpleQueue()     # queue.Queue()
        self.window.after(state.queue_ms, self.update_listen_for_result)

    def set_title( self, text ):
        ''' Set or change the message above the text box '''
        try:
            self.title[ 'text' ] = text
        except tk.TclError:
            pass

    def stop( self ):
        ''' Prepare this window to be closed, destroy the window '''
        set_skip_test(True)
        state.running = False
        state.archive_files = False
        try:
            self.window.destroy()
        except tk.TclError:     # likely this has been destroyed already
            pass

    def update( self, txt, counter=0, count_max=0, show_command_counter=True, warn=False):
        ''' Update the window, by showing new text '''
        state.block_follow = True
        if count_max:
            self.tbx.insert( tk.END, f'{txt}\n' )
            lines = int(self.tbx.index('end-1c').split('.')[0])
            if lines > MAX_LINES:
                delete = f'{lines-MAX_LINES}.0'
                self.tbx.delete( '1.0', delete )
                self.tbx.insert( '1.0', '*** Earlier lines deleted ***\n' )
            self.tbx.see(tk.END)

        if warn:
            self.warn()

        if show_command_counter:
            if count_max > 0:
                self.lbl[ 'text' ] = f"Command {counter} of {count_max}"
            elif count_max < 0:
                self.lbl[ 'text' ] = ''
            else:
                self.lbl[ 'text' ] = txt
        else:
            self.lbl[ 'text' ] = ''

        self.lbl.pack()
        if state.running:
            self.window.update()

    def update_listen_for_result( self ):
        """ Check if there is something in the queue. """
        while state.running:
            try:
                (func, args) = self.update_queue.get(0)
                state.block_follow = True
            except queue.Empty:
                # we didn't find anything, this is normal
                state.block_follow = False
                if state.running:
                    self.window.after(state.queue_ms, self.update_listen_for_result)
                return

            #we found something
            if func == self.update:     # the function passed in
                ( txt, counter, count_max, show_command_counter, warn ) = args
                self.update( txt, counter, count_max, show_command_counter, warn)
            elif func == self.missing:  # the function passed in
                self.missing( args )
            else:
                func()

        self.window.after(state.queue_ms, self.update_listen_for_result)

    def warn(self):
        ''' recursivly seek all widgets and set their colours '''
        for btn in ( self.skip_button,
                     self.history_button,
                     self.btn_pause ):
            btn[ 'state' ] = tk.DISABLED
        self._warn_down( self.window )
        self.tbx.config( bg="#ff0", fg='#000' )

    def _warn_down( self, master, level=0 ):
        ''' recursivly seek all widgets and set their colours '''
        if isinstance( master, str ):
            return
        if isinstance( master, tk.Menu ):
            # alright, don't mess with menus
            return
        if isinstance( master, tk.Button ):
            # alright, don't mess with menus
            return

        master.config( bg="#000" )

        try:
            master.config( fg='#fff' )
        except tk.TclError:
            # we may have a frame, with background but no foreground colour
            pass

        for child in master.winfo_children():
            self._warn_down( child, level+1 )

########################################################################

def do_colour( device, cmd=None):
    '''
    set colours for a device
    '''
    if not device in state.joysticks:
        return

    if not device in config.config[ 'devices' ]:
        return

    now_time = datetime.utcnow()
    if not device in do_colour.next_colour_time:
        do_colour.next_colour_time[ device ] = datetime(1900, 1, 1)     # first run this sessio
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
        if TEST:
            print( run )

        if state.running:
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
    state.skip_test = set_skip

def set_state_reset( setting ):
    ''' set state.refreshing, and request a queue flush if needed '''
    state.reset = setting

def stop_running():
    '''
    Set a flag to stop running this script
    '''
    state.running = False

def device_test(main_window):
    ''' Display the colour combination for each event to be displayed '''

    wait_queue( main_window, 10 )

    len_inst = len( instructions )

    ctr = 0
    update( main_window, '', ctr, len_inst )
    update( main_window, 'Device Test', ctr, len_inst )
    update( main_window, '===========', ctr, len_inst )
    for instr in instructions:
        if ( not state.test_devices or
             not state.running ):
            break
        while state.pause:
            time.sleep( 0.2 )
            if ( not state.test_devices or
                 not state.running ):
                break

        ctr += 1
        manage( '{"event":"' + instr + '"}', main_window )
        update( main_window, f' {instr}', ctr, len_inst )
        time.sleep(0.5)       # slow down to allow screen to update

    if state.test_devices:
        update( main_window, '', ctr, len_inst )
        main_window.update_queue.put( (main_window.device_test, () ))

def dopack( master ):
    ''' recursively, pack a widget and its ancestors '''
    while True:
        if hasattr( master, 'pack' ):
            master.pack()
        if hasattr( master, 'master' ):
            master = master.master
        else:
            break

def do_start(main_window):
    ''' Handle start up routines '''
    if state.b_done_start:
        return True
    state.running = True

    missing = []

    find_joysticks()
    for instr in instructions:
        for ins in instructions[ instr ]:
            if not ins in state.joysticks:
                if ins not in missing:
                    missing.append( ins )

    if len( missing ) > 0:
        main_window.update_queue.put( (main_window.missing, missing ))
        return False

    try:
        do_reset()
    except FileNotFoundError:
        update( main_window, ( '    Cant find VPC_LED_Control.exe\n\n'
                               '    Hint: Check pathToLEDControl in config.json'),
            count_max=1, show_counter=False, warn=True )
        return False

    state.b_done_start = True
    return True

def file_check( file_filter ):
    ''' how many files are we looking at ? '''
    file_filter = glob.glob(
        f"{config.config['__fPath__']}"
        f"{edlr.LOG_FILE}{file_filter}."
        f"{edlr.LOG_SUFFIX}" )
    return len( file_filter ) > 0

def find_joysticks():
    ''' find devices currently attached '''
    for stick in list_joysticks.list_joy_sticks():
        state.joysticks[ stick[ 'oem_name' ] ] = stick

def follow(the_file, main_window):
    ''' generator function that yields new lines in a file '''
    if not state.archive_files:
        the_file.seek(0, os.SEEK_END)

    follow.cycle = 0
    is_reset = False

    # start infinite loop
    while state.running:
        if state.block_follow or state.pause:
            time.sleep( 0.1 )
            continue
        if state.test_devices:
            return
        if state.reset or not state.running:
            return

        # read last line of file
        try:
            line = the_file.readline()
        except UnicodeDecodeError:
            # non recoverable, non destructive,
            # back out and try again
            return

        # sleep if file hasn't been updated
        if line:
            follow.cycle = 0
            is_reset = False
            yield line
            continue

        if not is_reset:
            if follow.cycle > config.config[ "resetTime" ]:
                is_reset = do_reset()

        if follow.cycle > config.config[ 'timeOut' ]:
            #  - maybe we need a different file?
            return

        if state.archive_files:
            # no point waiting for new data
            return

        if state.running and not state.reset:
            # give the_file a chance to gain more lines
            time.sleep(config.config[ 'sleepTime' ])
        else:
            return

        follow.cycle += config.config[ 'sleepTime' ]
        refresh = ( config.config[ "timeOut" ] -
                    follow.cycle +
                    config.config[ "sleepTime" ] )
        txt = f'Scanning ED {edlr.LOG_FILE} files'
        if refresh > 0:
            txt = f'{txt} (file refreshes in {refresh}s if no new events)'
        update( main_window, txt, 0, 1, False )

def get_master( master ):
    while hasattr( master, 'master' ):
        master = master.master
    return master

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

def make_menu( menu, menulist ):
    ''' make a drop down menu list '''
    master = get_master( menu )
    # while hasattr( master, 'master'):
    #    master = master.master

    for item in menulist:
        if menulist[ item ] is None:
            menu.add_separator()
        else:
            if item == item.lower():
                make_string( item, master=master )
                label = state.labels[ item ].get()
            else:
                label = item
            menu.add_command(label=label, command=menulist[ item ])

def manage( line, window=None, file_name='' ):
    ''' with a line from the game log, arrange to
        send colour instructions to devices '''
    try:
        data = json.loads(line)
    except json.decoder.JSONDecodeError as error:
        # I get an intermittent error here - need to see the cause
        edlr.log( f'{os.path.basename(__file__)} v{VERSION}', 'manage', f'{error}\n\t{line}' )
        return

    if data[ "event" ] in instructions:
        for k in instructions[ data [ "event" ] ]:
            if state.archive_files  and window is not None:
                wait_queue( window, 60 )
            if TEST:
                print( f'{k}: -> {instructions[ data [ "event" ] ][ k ]}' )
            do_colour( k, cmd=instructions[ data [ 'event' ] ][ k ])

        if state.archive_files and window is not None:
            len_instns = len(instructions[ data [ "event" ] ])
            if len_instns > 1:
                ses = 's'
            else:
                ses = ''
            txt = f'{data["event"]} has {len_instns} instruction{ses}'
            txt = f'{file_name} {txt}'
            update( window, txt, counter=0, count_max=1, show_counter=False )

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
            if TEST:
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

    if TEST:
        for event in instructions:
            print( f'Event {event}: {instructions[ event ]}' )

    config_file.close()

def make_string( key, master ):
    ''' make a string varaiable '''
    if isinstance( key, list ):
        str_id = ''
        str_res = ''
        for item in key:
            if len( str_id ) == 0:
                str_id = item
            str_test = edlr.translate( item )
            if len( str_res ) < len( str_test ):
                str_res = str_test
        state.labels[ str_id ] = edlr.make_string( str_id, master )
        state.labels[ str_id ].set( str_res )
        return 
    state.labels[ key ] = edlr.make_string( key, master )

def set_filter( args=None ):
    ''' set/re-set the file filters used when searching for files '''
    if args is not None:
        (window, file_filter) = args
        state.file_filter = file_filter
        set_state_reset( True )
        window.reset_title()

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

def update( window, txt, counter=0, count_max=0, show_counter=True, warn=False ):
    ''' Refresh window (while it is there) '''

    wait_queue( window, timeout=5 )

    if window.update_queue.qsize() < 20:
        window.update_queue.put( (window.update,
                                  ( txt,
                                    counter,
                                    count_max,
                                    show_counter,
                                    warn) ))

def threaded_function(main_window):
    ''' Heart beat of the main process:
        Keeps checking the log files,
        and sending commands to joy sticks
    '''

    if do_start(main_window):
        while state.running:
            if state.test_devices:
                device_test(main_window)

            set_state_reset( False )
            log_file_list = sorted(
                glob.glob( f"{config.config['__fPath__']}"
                           f"{edlr.LOG_FILE}{state.file_filter}."
                           f"{edlr.LOG_SUFFIX}" ),key=os.path.getmtime)
            if len( log_file_list ):
                if not state.archive_files:
                    log_file_list = [ log_file_list[-1] ]
                for file_path in log_file_list:
                    if state.reset or not state.running:
                        break
                    read_file( main_window, file_path )
                if state.running and not state.archive_files:
                    time.sleep(config.config[ 'sleepTime' ])
            else:
                messagebox.showinfo(
                    master=main_window.window,
                    title=f'{PROG_NAME} Warning',
                    message=( 'No Elite Dangerous log files were found\n'
                              'Please check your file path') )
                main_window.update_queue.put( (main_window.stop, () ))
                break

def read_file( main_window, file_path ):
    ''' read one log file, and react to the events recorded '''
    wait_queue( main_window, timeout=10 )

    file_name = file_path.split('\\' )[ -1 ].split('/' )[ -1 ]
    update( main_window, f'{datetime.now().strftime("%Y-%m-%d %H:%M")}\nChecking {file_name}',
            count_max=1, show_counter=False )

    log_file = open(file_path,"r")
    log_lines = follow(log_file, main_window)
    for line in log_lines:
        if state.reset or not state.running:
            break
        manage(line, main_window, f'{file_name}:')
    log_file.close()

def wait_queue( window, timeout=10 ):
    ''' help improve screen responces by giving
        the message queue a chance to clear down '''
    sleeper = 0.2
    counter = int (timeout / sleeper )
    while window.qsize() and counter > 0:
        time.sleep( sleeper )
        counter -= 1


def main():
    ''' Main process '''
    config()
    Window()
    if TEST:
        edlr.unused()

if __name__ == '__main__':
    main()
