"""
A holding docstring
"""

from functools import partial
import json
import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import shared as edlr

VERSION         =   '0.04.11'               # date based version, numbers will probably slip

BTEST = 'test' in [x.lower() for x in sys.argv]
COLOURS = edlr.COLOURS
DEFAULT_COMMAND = 0                # default command

def static():
    ''' a holder for static/global variables '''
static.commands         = edlr.instructions
static.comments         = []
static.cmdlen           = 0
static.instruction      = [ ('colourmode', 3), ('Red', 4), ('Green', 4), ('Blue', 4), ('cmd', 45) ]
# pretty sure instruction can be simplified ^^^

static.colour_options   = ['ignore', 'randomcolour', 'setcolour']
static.colour_mode      = []
static.config           = None
static.devices          = {}
static.var              = {}

'''
for each event:
    for each device:
        for each led:
            have a red field
            have a green field
            have a blue field            
        for each slave_led
            have a red field
            have a green field
            have a blue field
'''

for l in edlr.translate.languages:
    edlr.translate.unused[ l ] = {}
    for tlate in edlr.translate.languages[ l ]:
        edlr.translate.unused[ l ][ tlate ] = edlr.translate.languages[ l ][ tlate ]
progName = sys.argv[0].split('\\')[-1].split('.')[0]

'''
def change_device( device ):
    main.window.change_device( device )
'''

def change_event( event ):
    main.window.change_event( event )

def colourchooser(args):
    (cfrm, event, device) = args
    rgb = ( static.var[ event ][ device ][ "Red" ].get(),
            static.var[ event ][ device ][ "Green" ].get(),
            static.var[ event ][ device ][ "Blue" ].get())
    colourChooser( rgb, colourchoosercallback, (cfrm, event, device) )

def colourchoosercallback( *args ):
    ((cfrm, event, device), colour ) = args
    static.var[ event ][ device ][ "Red" ].set(colour[ 0 ])
    static.var[ event ][ device ][ "Green" ].set(colour[ 1 ])
    static.var[ event ][ device ][ "Blue" ].set(colour[ 2 ])
    setcolour( cfrm, (event, device) )

def command_devices( master ):
    ''' add device into events '''
    for cmd in static.commands:
        # print( f'command_devices: {cmd}' )
        # print( f'a {static.commands[ cmd ]}' )
        if not cmd in static.var:
            static.var[ cmd ] = {}
        for dev in static.devices:
            if static.devices[ dev ][ "vid" ] != '3344':
                # skip non Virpil devices
                continue

            if not dev in static.var[ cmd ]:
                static.var[ cmd ][ dev ] = {}

            static.var[ cmd ][ dev ][ 'button' ] = tk.StringVar(master=master)

            # print( static.instruction )
            for (i, unused) in static.instruction:
                for command in static.commands:
                    continue        # too many errors here, need a re-think
                    if i in static.var[ cmd ][ dev ]:
                        # we have this already
                        continue

                    if i == 'colourmode':
                        static.var[ cmd ][ dev ][ i ] = tk.StringVar(master=master)
                        static.var[ cmd ][ dev ][ i ].set( static.colour_mode[ 0 ] )
                        # print( f'\n\n{i}: static.var[ { cmd } ][ { dev } ][ {i} ]
                        #       -> {static.var[ cmd ][ dev ][ i ].get()}' )
                        continue

                    if i == 'cmd':
                        static.var[ cmd ][ dev ][ i ] = tk.StringVar(master=master)
                        static.var[ cmd ][ dev ][ i ].set( languages[ lang ][ "commands" ][ 0 ] )
                        if dev in static.commands[ cmd ]:
                            if 'cmd' in static.commands[ cmd ][ dev ]:
                                static.var[ cmd ][ dev ][ i ].set( languages[ lang ][
                                    "commands" ][ int( static.commands[ cmd ][ dev ][ 'cmd' ] ) ] )
                        continue

                    static.var[ cmd ][ dev ][ i ] = tk.IntVar(master=master)

                    if i in ['Red', 'Green', 'Blue']:
                        # a non-random colour ... i.e. a colour that we have set up
                        static.var[ cmd ][ dev ][ 'colourmode' ].set( static.colour_mode[ 2 ] )
                        # print( f'{i}: static.var[ { cmd } ][ { dev } ][ static.colour_mode ]
                        #           -> {static.var[ cmd ][ dev ][ "colourmode" ].get()}' )

                    if cmd == 'Default':
                        static.var[ cmd ][ dev ][ 'colourmode' ].set( static.colour_mode[ 1 ] )

def get_colour_mode( event, device ):
    # print( f'event: {event}, device: {device}, static.var -> {static.var[ event ][ device ]}' )
    # print( f'\n\n{event}, {device} {static.var[ event ][ device ]}\n\n' )
    # print( f'\n\n{event}, {device} {static.var[ event ][ device ][ "button" ].textvariable.get()} ({len(static.var[ event ][ device ][ "button" ].textvariable.get())})\n\n' )

    # if colour_mode is None or len( colour_mode ) == 0:
    #   colour_mode == '02'
    # return
    if 'colourmode' in static.var[ event ][ device ]:
        return static.var[ event ][ device ][ 'colourmode' ].get()[1:3]
    else:
        ret = []
        for key in static.commands[ event ][ device ]:
            str_key = f'00{key}'[-2:]
            ret.append( str_key )
        return ret

def language( lang_code ):
    edlr.language = lang_code
    main.window.translate()
    main.window.makemenu()
    setcmdlen()

def setcmdlen():
    global lang
    global cmdlen
    static.cmdlen = 0
    # print( edlr.translate.languages )
    # print( edlr.language )
    for i in edlr.translate.languages[ edlr.language ][ "commands" ]:
        static.cmdlen = max( static.cmdlen, len( i ) )

def test( args ):

    import random, subprocess
    (event) = args

    mssgs = []

    for device in static.devices:
        if static.devices[ device ][ 'vid' ] != '3344':
            continue

        cm = get_colour_mode( event, device )

        if cm == '00':
            mssgs.append( [cm, xlate('ignored'), device, xlate( 'commandignored' ) ] )
            continue
        elif cm == '01':
            red = random.choice( COLOURS )
            green = random.choice( COLOURS )
            blue = random.choice( COLOURS )
            mssgs.append( [cm, xlate('random'), device, xlate( 'commandrandom' ) ] )
        else:
            red = COLOURS[ static.var[ event ][ device ][ 'Red' ].get() ]
            green = COLOURS[ static.var[ event ][ device ][ 'Green' ].get() ]
            blue = COLOURS[ static.var[ event ][ device ][ 'Blue' ].get() ]

        cmd = static.var[ event ][ device ][ 'cmd' ].get()[ 1:3 ]

        run = f"\"{static.config[ '__pathToLEDControl__' ]}\""
        run = f"{run} {static.config[ 'devices' ][ device ][ 'id' ]} {cmd} { red } { green } { blue }"
        if BTEST:
            print( run )
        subprocess.Popen( run, creationflags=subprocess.CREATE_NEW_CONSOLE )

    if len( mssgs ):
        cm = 99
        title = ''
        txt = ''
        for m in mssgs:
            if int( m[ 0 ] ) < cm:
                cm = int( m[ 0 ] )
                title = m[ 1 ]
            txt = f'{txt}\n{m[ 2 ]}\n{m[3]}\n'

        messagebox.showwarning(title=title, message=txt)

def makeString(sId, master=None ): #, master, lblW):
    # global lang
    tlate = tk.StringVar(master=master)
    tlate.set( edlr.translate(sId, edlr.language ) )
    return tlate

def setcolour_mode():
    if static.colour_mode is None:
        static.colour_mode = []    
    while len( static.colour_mode ) < len( static.colour_options ):
        static.colour_mode.append( '' )
    for col_mode in range( len( static.colour_options ) ):
        num = f'00{ col_mode }'[-2:]
        static.colour_mode[ col_mode ] = f'[{num}] {edlr.translate( static.colour_mode[ col_mode ] )}'

def setcolour( *args ):
    return
    (a , b) = args
    try:
        if len( a ):
            (cfrm, (event, device) ) = a
    except:
        (cfrm, (event, device) ) = args

    cm = get_colour_mode( event, device )
    # print( cm )

    # print( f"static.var[ {event} ][ {device} ][ 'colourmode' ].get()[4:]" )
    # buttontxt = static.var[ event ][ device ][ 'colourmode' ].get()[4:]

    for colour_mode in cm:
        state = tk.DISABLED
        if colour_mode == '00':
            # print(static.var[ event ][ device ])
            # print(static.commands[ event ][ device ] )
            # print(static.commands[ event ][ device ][ int(colour_mode)] )
            red = static.var[ event ][ device ][ int(colour_mode)][ 'Red' ].set(0)
            green = static.var[ event ][ device ][ int(colour_mode)][ 'Green' ].set(0)
            blue = static.var[ event ][ device ][ int(colour_mode)][ 'Blue' ].set(0)
        elif colour_mode == '01':
            red = static.var[ event ][ device ][ int(colour_mode)][ 'Red' ].set(3)
            green = static.var[ event ][ device ][ int(colour_mode)][ 'Green' ].set(3)
            blue = static.var[ event ][ device ][ int(colour_mode)][ 'Blue' ].set(3)
        else: # colour_mode == '02':
            state = tk.NORMAL
            # print( f"red = static.var[ {event} ][ {device} ][ 'Red' ].get()" )
            red = static.var[ event ][ device ][ int(colour_mode)][ 'Red' ].get()
            green = static.var[ event ][ device ][ int(colour_mode)][ 'Green' ].get()
            blue = static.var[ event ][ device ][ int(colour_mode)][ 'Blue' ].get()

        # red = static.var[ event ][ device ][ 'Red' ].get()
        # green = static.var[ event ][ device ][ 'Green' ].get()
        # blue = static.var[ event ][ device ][ 'Blue' ].get()
        background = swatch( red, green, blue )
        if colour_mode == '02':
            # static.var[ event ][ device ][ 'button' ].set(background)
            pass
        else:
            # static.var[ event ][ device ][ 'button' ].set(buttontxt)
            pass

        tone = max(red,  max(green, (red + green + blue )/3))
        if tone > 2:
            fg =  swatch( 0, 0, 0)
        else:
            fg = swatch( 3, 3, 3 )
        b = 0
        c = 0
        for child in cfrm.winfo_children():
            try:
                child[ 'background' ] = background
                child[ 'fg' ] = fg
            except:
                pass
            if isinstance( child, tk.ttk.Combobox ):
                if c in range( 1, 4 ):
                    child[ 'state' ] = state
                c += 1
            elif isinstance( child, tk.Button ):
                if b == 0:
                    child[ 'state' ] = state
                b += 1

class colourChooser:
    def __init__(self, background, callback, args):
        self.default_background = background
        self.background = background
        self.callback = callback
        self.callbackargs = args
        self.window = tk.Tk()
        self.window.title(f'{progName} - Colour Chooser')

        main.window.grab_release()
        self.window.grab_set()

        frm = tk.Frame(master=self.window)
        cfrm = tk.Frame(master=frm, bd=10)
        for red in range( 4 ):
            rfrm = tk.Frame(master=cfrm, bd=4)
            for green in range( 4 ):
                gfrm = tk.Frame(master=rfrm)
                for blue in range( 4 ):
                    cbackground = swatch( red, green, blue )

                    bfrm = tk.Frame(master=gfrm , width=30, height=30,
                                    highlightthickness=2, highlightcolor="#888888" )
                    bfrm.pack(side=tk.TOP)
                    bfrm.configure(background=cbackground, bd=1)
                    bfrm.bind("<Button-1>", self.colour_click)
                    bfrm.bind("<Double-Button-1>", self.double_colour_click)
                    bfrm.pack(side=tk.TOP)
                gfrm.pack(side=tk.LEFT)
            rfrm.pack(side=tk.LEFT)
        cfrm.pack(side=tk.TOP)
        self.swatch = tk.Frame(master=frm,
                               width=120, height=60,
                               bd=10,
                               background=swatch( background[0], background[1], background[2] ))
        self.swatch.pack(side=tk.TOP)
        self.set_swatch(self.background)
        btnfrm = tk.Frame(master=frm , width=200, height=80, bd=10)
        for btn in (["Accept",self.accept], ["Reset",self.reset], ["Cancel",self.cancel] ):
            self.btn = tk.Button(
                text =btn[ 0 ],
                width=6,
                master=btnfrm,
                # state=tk.DISABLED
                command=btn[1],
                )
            self.btn.pack(side=tk.LEFT)
        btnfrm.pack()
        frm.pack()
        self.window.mainloop()

    def __del__(self):
        try:
            self.window.grab_release()
        except:
            pass
        try:
            main.window.grab_set()
        except:
            pass

    def accept(self):
        self.callback(self.callbackargs, self.background)
        self.cancel()

    def cancel(self):
        self.window.grab_release()
        self.window.destroy()

    def colour_click(self, event ):
        wdgt = str( event.widget ).split(".!frame")
        for n in range( len(wdgt)):
            if len( wdgt[ n ] ):
                wdgt[ n ] = int( wdgt[ n ] ) - 1
            else:
                wdgt[ n ] = 0
        self.set_swatch( [f'{wdgt[ 3 ]}', f'{wdgt[ 4 ]}', f'{wdgt[ 5 ]}'] )

    def double_colour_click(self, event ):
        self.accept()

    def reset(self):
        self.set_swatch( self.default_background )

    def set_swatch(self, background):
        self.background = background
        self.swatch.configure(background=swatch(
                        self.background[0],
                        self.background[ 1 ],
                        self.background[ 2 ]))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        xscrollbar = ttk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
                )
            )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=xscrollbar.set, yscrollcommand=scrollbar.set )

        scrollbar.pack(side="right", fill="y")
        xscrollbar.pack(side="bottom", fill="x")
        canvas.pack(anchor='nw', fill="both", expand=True)

class mainWindow(tk.Tk):

    buttons = {}
    bSaved = True
    bShow0 = False
    bShowInterst = True
    labels = {}
    padx = (0, 30)
    lCmds = 0
    ldevs = 0

    # background = [['#ddddee','#ddddee','#ddddee','#eeeeff'],
    #        ['#bbbbbb','#bbbbbb','#bbbbbb','#cccccc']]

    background = [['#f0f0f0','#f0f0f0','#f0f0f0','#e0e0e0'],
            ['#fcfcfc','#fcfcfc','#fcfcfc','#e0e0e0'],
            ['#f0f0f0','#f0f0f0','#f0f0f0','#e0e0e0'],
            ['#e4e4e4','#e4e4e4','#e4e4e4','#cccccc']]

    def __init__(self, master=None):
        super().__init__(master)

        # self.var = {}

        self.title( progName )
        setcolour_mode()
        self.makemenu()
        self.set_screen_size( 1530, 500, 500, 100 )

        self.mssgFrm = tk.Frame(self)
        self.mssg = tk.Text(self.mssgFrm)
        self.mssg[ 'height' ] = 4
        self.mssg.pack(expand=True)
        self.mssgFrm.pack(expand=False, side=tk.TOP, fill="x")

        self.btnFrm = tk.Frame(self, height=1)
        self.makeButtons()

        self.workfrm = tk.Frame(self)
        self.devfrm = tk.Frame(self.workfrm, height=1)
        self.devfrm.pack(expand=False, side=tk.TOP, fill="x")

        self.wkSpace = ScrollableFrame(self.workfrm)
        self.wkSpace.pack(expand=True, fill="both")
        self.workfrm.pack(expand=True, side=tk.TOP, fill="both")

        self.devices()
        self.translate()
        command_devices( self )

        self.change_event()

    def change_event( self, event_key=None, evtfilter='' ):
        for child in self.devfrm.winfo_children():
            child.destroy()
        self.devfrm.pack()

        ################################################

        self.rebuild_workspace()

        # self.wkSpace.destroy()
        # self.wkSpace = ScrollableFrame(self.workfrm)
        # self.wkSpace.pack(expand=True, fill="both")
        # self.workfrm.pack()

        self.labels[ "event" ] = makeString( "event", master=self.devfrm )
        self.labels[ "test" ] = makeString( "test", master=self.devfrm )

        n = -1
        r = 1
        events = []
        if event_key is None:
            for event in static.commands:
                events.append( event )
        elif isinstance( event_key, str ):
            if len( event_key ) == 1:
                for event in static.commands:
                    if event[ 0 ] == event_key:
                        events.append( event )
            else:
                events.append( event_key )
                
        for event in events:
            label = tk.Label( self.devfrm, textvariable=self.labels[ "event" ], anchor=tk.W )
            label.pack(side=tk.LEFT)
            label = tk.Label( self.devfrm, text=f'-  {event}' )
            label.pack(side=tk.LEFT)
            n += r
            n %= len( self.background )
            cfrm = tk.Frame( self.wkSpace.scrollable_frame, background=self.background[ n ][ 0 ] )
            r = self.loadEvent( cfrm, event, n, event )

    def change_event_active( self ):
        self.change_event( event=None, evtfilter=static.colour_mode[ 2 ] )

    def change_event_ignore( self ):
        self.change_event( event=None, evtfilter=static.colour_mode[ 0 ] )

    def change_event_random( self ):
        self.change_event( event=None, evtfilter=static.colour_mode[ 1 ] )

    def load_device( self, master, device, backgroundc ):
        background=self.background[ backgroundc ][ 0 ]
        if device in static.config[ "devices" ]:
            dev_id = f'{static.devices[ device ][ "vid" ]} {static.devices[ device ][ "pid" ]}'
            if 'id' not in static.config[ "devices" ][ device ]:
                static.config[ "devices" ][ device ][ 'id' ] = dev_id

            if static.config[ "devices" ][ device ][ 'id' ].upper() != f'{(dev_id).upper()}':
                messagebox.showwarning( title="device id error",
                                        message=(f"{device} has a different id\n"
                                                 f'{static.config[ "devices" ][ device ][ "id" ]} should be '
                                                 f'{dev_id}') )
                background = 'yellow'
            else:
                static.config[ "devices" ][ device ][ 'id' ] = dev_id
                
        cfrm = tk.Frame( self.wkSpace.scrollable_frame,
                         background=background )

        for (txt, width, weight) in ( ('', 10, ''),
                                      (device, self.len_devices(), 'bold'),
                                      (static.devices[ device ][ 'vid' ], 4, ''),
                                      (static.devices[ device ][ 'pid' ], 4, '')):
            label = tk.Label( cfrm, text=txt, width=width,
                              anchor="w", background=background,
                              font=('TkDefaultFont', 11, weight),
                              justify=tk.LEFT )
            label.pack(side=tk.LEFT, fill='both')

        if not 'cb' in static.devices[ device ]:
            static.devices[ device ][ 'cb' ] =  tk.BooleanVar(self)
            static.devices[ device ][ 'cb' ].set( device in static.config[ "devices" ] )

        cb = tk.Checkbutton( cfrm, text=edlr.translate("configure"),
                             variable=static.devices[ device ][ 'cb' ], background=background)
        cb.pack( side=tk.LEFT, fill='both' )
        # https://www.geeksforgeeks.org/python-tkinter-checkbutton-widget/

        if device in static.config[ "devices" ]:

            if 'cmdList' in static.config[ "devices" ][ device ]:
                label = tk.Label( cfrm, text=static.config[ "devices" ][ device ][ 'cmdList' ],
                                  anchor="w", background=background,
                                  justify=tk.LEFT )
                label.pack(side=tk.LEFT, fill='both', padx=( 20, 5 ))
        
        cfrm.pack()
        return 1

    def loadEvent(self, master, event, backgroundc, label='', evtfilter='' ):
        # evtfilter = str( evtfilter )
        if len( evtfilter ):
            ret = True
            for dev in static.devices:
                if static.devices[ dev ][ 'vid' ] != '3344':
                    continue
                if BTEST:
                    var_str = f'{static.var[ event ][ dev ][ "colourmode" ].get() }'
                    # print( f'{ dev } -> { var_str } ({evtfilter})' )

                if static.var[ event ][ dev ][ 'colourmode' ].get() == evtfilter:
                    ret = False
                    break
            if ret:
                return 0

        state = tk.NORMAL
        if event == 'Default':
            state = tk.DISABLED
        n = 0

        cfrm = tk.Frame( master, background=self.background[ backgroundc ][n])

        if len( label ):
            label = tk.Label( cfrm, text=label, width=self.lenCommands(),
                              anchor="w", background=self.background[ backgroundc ][ n ],
                              font=('TkDefaultFont', 11, 'bold'), justify=tk.LEFT )
            label.pack(side=tk.LEFT, fill='both')
            # cfrm.pack( side=tk.LEFT )

        dwfrm = tk.Frame( cfrm, background=self.background[ backgroundc ][n])

        for dev in static.devices:
            if static.devices[ dev ][ 'vid' ] != '3344':
                continue

            if BTEST:
                if dev in static.commands[ event ]:
                    print( f'{ dev } -> {static.commands[ event ][ dev ]}' )
                else:
                    print( f'{ dev } not in static.commands[ {event} ]' )

            dfrm = tk.Frame( dwfrm, background=self.background[ backgroundc ][n])
            label = tk.Label( dfrm, text=dev, width=self.lenCommands(),
                              anchor="w", background=self.background[backgroundc][n],
                              font=('TkDefaultFont', 10, 'bold') )
            label.pack(side=tk.LEFT)

            for (i, r) in static.instruction:
                txt = edlr.translate(i, edlr.language)
                label = tk.Label( dfrm, text=f'{txt}:',
                                  width=len(txt)+1,
                                  anchor="w",
                                  background=self.background[backgroundc][n] )
                label.pack(side=tk.LEFT)

                w = 4
                if i == 'colourmode':
                    if static.colour_mode is None:
                        setcolour_mode()
                    for cm in range( len( static.colour_mode) ):
                        w = max( w, len( static.colour_mode[ cm ] ) )
                elif i == 'cmd':
                    global cmdlen
                    w = static.cmdlen

                cb = ttk.Combobox(dfrm,
                                  width = w,
                                  # textvariable = static.var[ event ][ dev ][ i ]
                                  )
                cb.bind("<<ComboboxSelected>>", partial( setcolour, (dfrm, (event, dev) )))
                cb['state'] = state
                values = []
                if i == 'colourmode':
                    if static.colour_mode is not None:
                        values = static.colour_mode
                elif i == 'cmd':
                    values = edlr.translate.languages[ edlr.language ]      # [ "commands" ] commands substructure rounded back up
                else:
                    for q in range( r ):
                        values.append( q )

                cb[ 'values' ] = tuple(values)
                cb.pack( side=tk.LEFT, padx=self.padx )
                if i in ('Red', 'Green', 'Blue' ):
                    # label.pack_forget()
                    # cb.pack_forget()
                    pass

                if i == 'colourmode':
                    bu = tk.Button( dfrm, textvariable=static.var[ event ][ dev ][ 'button' ],
                                         command=partial( colourchooser, (dfrm, event, dev) ),
                                         width=len(edlr.translate('randomcolour')))
                    bu.pack( side=tk.LEFT, padx=self.padx )
                    bu[ 'state' ] = state
                    # static.var[ event ][ dev ][ 'button' ].command =
                    #       partial( setcolour, (dfrm, (event, dev) ))

            dfrm.pack( side=tk.TOP )
            setcolour(dfrm, (event, dev) )
        dwfrm.pack( side=tk.LEFT )
        bu = tk.Button( cfrm, textvariable=self.labels[ "test" ],
                        command=partial( test, (event) ),
                        width=len(edlr.translate('test')))
        bu.pack(  side=tk.LEFT, padx=self.padx )
        cfrm.pack(side=tk.TOP)
        master.pack()
        self.wkSpace.pack()

        return 1

    def devices( self ):
        global lang
        self.devicesmenu()

        self.missingDevices = load_devices()

        mainWindow.ldevs = 0

    def devicesmenu(self):
        self.devicemenu.delete(0, 'end')     # if we are refreshing
        self.devicemenu.add_command( label=edlr.translate("showDevices", edlr.language), command=self.show_devices )
        self.devicemenu.add_command( label=edlr.translate("refreshDevices", edlr.language), command=self.devices )

    def exit( self ):
        if self.bSaved:
            self.destroy()

    def lenCommands(self):
        if mainWindow.lCmds > 0:
            return mainWindow.lCmds

        for c in static.commands:
            mainWindow.lCmds = max( mainWindow.lCmds, len( c ) )

        return mainWindow.lCmds

    def len_devices(self):
        if mainWindow.ldevs > 0:
            return mainWindow.ldevs

        for dev in static.devices:
            mainWindow.ldevs = max( mainWindow.ldevs, len( dev ) )

        return mainWindow.ldevs

    def makeButtons(self):
        global lang
        btn_txt = {"refreshDevices": [self.devices], "save": [self.save], "exit": [self.exit]}
        w = 0
        for k in btn_txt:
            w = max( w, len( edlr.translate(k, edlr.language) ) )

        for child in self.btnFrm.winfo_children():
            child.destroy()

        minW = 0
        for k in btn_txt:
            self.labels[ k ] = makeString( k, master=self )
            self.buttons[ k ] = tk.Button( self.btnFrm,
                                           textvariable=self.labels[ k ],
                                           command = btn_txt[ k ][ 0 ], width=w)
            self.buttons[ k ].pack(side=tk.LEFT, expand=True)
            minW += w
        minW += w
        self.btnFrm.pack(expand=False, side=tk.BOTTOM)
        self.saveState()
        (w,h) = self.minsize()
        if minW < w:
            minW = w

        self.minsize( minW, h )

    def makemenu( self ):
        self.menubar = None
        self.menubar = tk.Menu( master=self )

        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        filemenu = {"save": self.save, "none": None, "exit": self.exit }
        for k in filemenu:
            if k == "none":
                self.filemenu.add_separator()
            else:
                self.labels[ k ] = makeString( k, master=self )
                self.filemenu.add_command(label=self.labels[ k ].get(), command=filemenu[ k ])
        self.labels[ "file" ] = makeString( "file", master=self )
        self.menubar.add_cascade(label=self.labels[ "file" ].get(), menu=self.filemenu, underline=0)

        self.eventmenu = tk.Menu( self.menubar, tearoff=0 )
        self.menuevents()
        self.labels[ "events" ] = makeString( "events", master=self )
        self.menubar.add_cascade(
            label=self.labels[ "events" ].get(),
            menu=self.eventmenu, underline=0)

        self.devicemenu = tk.Menu( self.menubar, tearoff=0 )
        self.devices()
        self.labels[ "devices" ] = makeString( "devices", master=self )
        self.menubar.add_cascade(
            label=self.labels[ "devices" ].get(),
            menu=self.devicemenu, underline=0)

        langmenu = tk.Menu(self.menubar, tearoff=0)
        lang = {}
        for l in edlr.translate.languages:
            langmenu.add_command(label=edlr.translate.languages[ l ]['language'], command=partial( language, l ))

        self.labels[ "language" ] = makeString( "language", master=self )
        self.menubar.add_cascade(label=self.labels[ "language" ].get(), menu=langmenu, underline=0)

        help_menu = tk.Menu(self.menubar, tearoff=0)
        menu_list = {   #'help': partial( help_mssg, (window, 'help', HELP)),
                        #'license': partial( help_mssg, (window, 'license', LICENSE )),
                        #'about': partial( help_mssg, (window, 'about', ABOUT))
            }
        # make_menu( help_menu, menu_list )
        self.labels[ "help" ] = makeString( 'help', master=self )
        self.menubar.add_cascade(label=self.labels[ 'help' ].get(), menu=help_menu, underline=0)


        self.config( menu=self.menubar )

    def menuevents( self ):
        if len( static.colour_mode ) == 0:
            # might not have been set yet
            setcolour_mode()

        self.eventmenu.delete(0, 'end')     # if we are refreshing
        self.eventmenu.add_command(
            label=edlr.translate( 'allevents' ),
            command=partial( change_event, None ) )
        self.eventmenu.add_separator()
        # print( static.colour_mode )
        self.eventmenu.add_command(
            label=f'{static.colour_mode[ 2 ][5:]} Events',
            command=self.change_event_active )
        self.eventmenu.add_command(
            label=f'{static.colour_mode[ 1 ][5:]} Events',
            command=self.change_event_random )
        self.eventmenu.add_command(
            label=f'{static.colour_mode[ 0 ][5:]} Events',
            command=self.change_event_ignore )
        self.eventmenu.add_separator()
        initial = ''
        for c in static.commands:
            if c == 'Default':
                self.eventmenu.add_command( label=c, command=partial( change_event, c ) )
            else:
                if initial != c[ 0 ]:
                    initial = c[ 0 ]
                    submenu = tk.Menu( self.eventmenu, tearoff=0 )
                    self.eventmenu.add_cascade(label=initial, menu=submenu, underline=0)
                    submenu.add_command( label=initial, command=partial( change_event, initial ) )
                    submenu.add_separator()
                submenu.add_command( label=c, command=partial( change_event, c ) )

    def save( self ):
        # do something
        self.bSaved = True
        self.saveState()

    def saveState(self):
        global lang
        if self.bSaved:
            self.buttons[ 'save' ][ 'state' ] = tk.DISABLED
            #self.btnSave.pack()
        else:
            self.buttons[ 'save' ][ 'state' ] = tk.NORMAL
        self.filemenu.entryconfigure(edlr.translate('save', edlr.language), state=self.buttons[ 'save' ][ 'state' ])

    def setChanged(self):
        self.bSaved = False

    def set_screen_size(self, width=1330, height=500, min_width=500, min_height=100 ):
        
        self.minsize( min_width, min_height )
        
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        width = min( width, screen_width-100 )      # leaving some space for manouver
        screen_height = root.winfo_screenheight()
        height = min( height, screen_height-250 )   # leaving some space for manouver
        root.destroy()
        self.geometry( f"{width}x{height}" )
    
    def rebuild_workspace(self):
        self.wkSpace.destroy()
        self.wkSpace = ScrollableFrame(self.workfrm)
        self.wkSpace.pack(expand=True, fill="both")
        self.workfrm.pack()

    def show_devices( self ):
        ''' open a devices list in the main frame '''
        self.rebuild_workspace()

        n = -1
        r = 1

        for dev in sorted( static.devices ):
            n += r
            n %= len( self.background )
            cfrm = tk.Frame( self.wkSpace.scrollable_frame,
                             background=self.background[ n ][ 0 ] )
            r = self.load_device( cfrm, dev, n )

        '''
        for dev in static.devices:
            # print( f'{dev}: {static.devices[ dev ]}' )
            if dev not in static.config[ "devices" ]:
                n += r
                n %= len( self.background )
                cfrm = tk.Frame( self.wkSpace.scrollable_frame,
                                 background=self.background[ n ][ 0 ] )            
                r = self.load_device( cfrm, dev, n )
        '''
        return

    def translate(self):
        for l in self.labels:
            self.labels[ l ].set( edlr.translate( l, edlr.language ) )
        self.makemenu()
        self.makeButtons()
        return

        # really shouldn't need the rest of this function

        children = []
        for child in self.btnFrm.winfo_children():
            child.pack()
            children.append( child )
        self.btnFrm.pack()
        return

        for child in children:
            for btn in self.buttons:
                if self.buttons[ btn ] == child:
                    my_btn = tk.Button(self.btnFrm, textvariable=self.labels[ btn ],
                                       command = child['command'], width=child['width'])
                    my_btn.pack( side=tk.LEFT, expand=True )
                    self.buttons[ btn ] = b
                    child.destroy()

def load_devices():
    import list_joysticks
    # global devices
    static.devices = {}

    jsList = list_joysticks.list_joy_sticks()

    for r in jsList:
        if r[ 'oem_name' ] in static.devices:
            oem_name = f'{r[ "oem_name" ]} {r["joy_id"]}'
        else:
            oem_name = f'{r[ "oem_name" ]}'
        static.devices[ oem_name ] = r

    if BTEST:
        for dev in static.devices:
            print( dev )
            print( static.devices[ dev ], end = '\n\n' )

    missing = []
    for dev in static.config[ 'devices' ]:
        if not dev in static.devices:
            missing.append( dev )
        else:
            dev_id = f'{static.devices[ dev ][ "vid" ]} {static.devices[ dev ][ "pid" ]}'
            if not dev_id == static.config[ 'devices' ][ dev ][ 'id' ]:
                missing.append( dev )
    return missing

def main():
    ''' the main function, does everythin '''
    config()

    # and run the script
    main.window     = mainWindow()
    main.window.mainloop()

    if BTEST:
        # log any unused terms
        edlr.log_unused()

def random_colour():
    ''' return a random colour '''
    return { 'Red': 'random', 'Green': 'random', 'Blue': 'random'}

def config():
    ''' Read configuration file, and any over-riding items in a local sub-folder '''
    config_load( f"{edlr.CONFIG_FILE}" )

    try:
        # see if there is a config file in a local sub-folder
        config_file = open( f"local/{edlr.CONFIG_FILE}","r")
    except FileNotFoundError:
        return

    # if found, add to, or over ride (some of) the main config information
    for line in config_file:
        data = json.loads(line)
        if 'Config' in data:
            for key in data[ 'Config' ]:
                static.config[ key ] = data[ 'Config' ][ key ]

    config_file.close()
    setcmdlen()

    for path in ('fPath', 'pathToLEDControl'):
        setPath( path )

    # for path in ('fPath', 'pathToLEDControl'):
    #    set_path( path )



def config_load(file_name):
    global config
    # global actions        # change with every new line ...

    # cva = [ 0, 1, 2, 3 ]
    configFile = open(file_name,"r")

    # dNow = datetime.utcnow() - timedelta(milliseconds=1000)

    for line in configFile:
        data = json.loads(line)
        if 'Config' in data:
            static.config = data['Config']
            for k in static.config[ 'devices' ]:
                if not 'leds' in static.config[ "devices" ][ k ]:
                    static.config[ "devices" ][ k ][ 'leds' ] = 0
                if not 'slave_leds' in static.config[ "devices" ][ k ]:
                    static.config[ "devices" ][ k ][ 'slave_leds' ] = 0
            # print( static.config[ 'devices' ] )
            # print( f'static.config: {static.config}' )
            continue
        if 'Comment' in data:
            static.comments.append( data['Comment'] )
            continue

        # print( data )

        actions = {}
        for k in data:
            if k in ['Event']:
                continue
            if k in ['Interest', 'interest']:
                if data[ "Event" ] == 'Default':
                    actions[ 'Interest' ] = 1
                else:
                    actions[ 'Interest' ] = int( data[ k ] )
                continue
            # if k in ['interest']:
            #    actions[ k ] = int( data[ k ] )
            #    continue

            if not isinstance(data[k], list):
                data[ k ] = [ data[k] ]
            # print( f'zz {data["Event"]} -> {data[ k ]}' )
            # print( f'xx {data}' )
            if actions[ 'Interest' ] == 0:
                # print( f'yy {data}' )
                pass
            lis = {}
            for data_k in data[ k ]:
                if data_k == 'random':
                    if ('Interest', 'interest') in data:
                        data_k = random_colour() # random_colour( cva[:data[ 'Interest' ]+1] )
                    #if 'interest' in data:
                    #    data_k = random_colour() # random_colour( cva[:data[ 'interest' ]+1] )
                    if not 'cmd' in data_k:
                        data_k = random_colour()
                        # print( data_k )
                        data_k[ 'cmd' ] = 0
                # print( f"a {data_k[ 'cmd' ]} {data_k}" )
                if data[ "Event" ] == 'Default':
                    data_k[ 'cmd' ] = 0
                if isinstance(data_k[ 'cmd' ], list):
                    for cmd in data_k[ 'cmd' ]:
                        lis[ cmd ]= data_k
                else:
                    lis[ data_k[ 'cmd' ] ]= data_k
            data[ k ] = lis
            actions[ k ] = data[ k ]

        for dev in static.config[ 'devices' ]:
            if dev not in actions:
                actions[ dev ] = {0: {
                    'Red': 0,
                    'Green': 0,
                    'Blue': 0,
                    'cmd': 0}}
                if 'cmdList' in static.config[ 'devices' ][ dev ]:
                    for cmd in  static.config[ 'devices' ][ dev ][ 'cmdList' ]:
                        actions[ dev ][ cmd ] = {
                            'Red': 0,
                            'Green': 0,
                            'Blue': 0,
                            'cmd': cmd
                            }
        static.commands[ data[ 'Event' ] ] = actions

        if BTEST:
            for c in static.comments:
                print( c )
            for c in static.commands:
                print( f'{c}: {static.commands[ c ]}\n' )
    configFile.close()

def setPath( p ):
    import os
    q = f'__{p}__'

    if not q in static.config:
        path = ""
        s = static.config[ p ].split("%")
        for t in s:
            if len( t ):
                try:
                    o = os.getenv(f'{ t }')
                    path += o
                except:
                    path += t
        static.config[ q ] = path

def swatch( red=0, green=0, blue=0 ):
    import shared
    return f'#{shared.COLOURS[ int(red) ]}{shared.COLOURS[ int(green) ]}{shared.COLOURS[ int(blue) ]}'

if __name__ == '__main__':
    main()
