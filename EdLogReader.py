"""
"""

import glob
import json
import os
import subprocess
import sys
import time
from threading import Thread
from datetime import datetime, timedelta
import shared as edlr

cv = edlr.cv                # colour values
commands = edlr.commands    # dictionary of available commands (filled at run time)

bRunning = False
bSkipTest = False
bTest = False
dCmd = edlr.dCmd            # default command
pathToLEDControl = ""       # filled at runtime

gNextColourTime = {}        # The earliest we can issue the next command
                            # Reason:
                            # Devices queue commands, and take time to execute the command.
                            # This leads to responces being out of sync with events in game
                            # gNextColourTime is to protect against out of sync responces
                            
bDoneStart = False          # has startup routine been run?
# edlr.bLooping = False     # loop control, not needed

js = {}

def doColour( device, cmd={'Red': 0, 'Green': 0, 'Blue': 0}):
    global gNextColourTime
    global bTest

    if not device in js:
        return

    if not device in config[ 'devices' ]:
        return
	
    thisTime = datetime.utcnow()
    if thisTime < gNextColourTime[ device ]:
        return

    # edlr.setPath( 'pathToLEDControl' )
    run = f"\"{config[ '__pathToLEDControl__' ]}\" {config[ 'devices' ][ device ][ 'id' ]} {cmd[ 'cmd']} {cv[ cmd['Red'] ]} {cv[ cmd['Green'] ]} {cv[ cmd['Blue'] ]}"
    if bTest:
        print( run )

    subprocess.Popen( run, creationflags=subprocess.CREATE_NEW_CONSOLE )
    gNextColourTime[ device ] = thisTime + timedelta(milliseconds=config[ "timedeltaMs" ])


def doReset():
    manage( '{ "event":"Default" }' )
    return True

class Window:
    import tkinter as tk
    lines = 0
    
    def __init__(self, missing, skipTest, closeDown):
        ttl = "ED Log Reader - Start Up"
        self.window = self.tk.Tk()
        self.window.title(ttl)
        self.frm = self.tk.Frame(master=self.window, bd=10)
        lbl = self.tk.Label( self.frm, text="Start Up Test")
        lbl.pack()
        self.tbx = self.tk.Text(self.frm, height=5, width=40, padx=5, pady=5)
        self.tbx.pack(fill=self.tk.X)
        self.lbl = self.tk.Label( self.frm, text="Command    of    ")
        self.lbl.pack(side=self.tk.LEFT)
        self.frm.pack(fill=self.tk.X)
        frm = self.tk.Frame(master=self.window, bd=5)
        bTxt = "Quit"   #   "Close Window"
        if len( missing ):
            bTxt = "Exit"
        else:
            bSkip = "Skip Test"
            button = self.tk.Button(frm, text=f' {bSkip} ', command=skipTest)
            button.pack(side=self.tk.LEFT)
        button = self.tk.Button(frm, text=f' {bTxt} ', command=self.stopRunning)
        button.pack()
        frm.pack()
        self.__doMissing__( missing )

    def __doMissing__(self, missing ):        
        if len( missing ):
            self.update( "Devices are Missing:" )
            h = 4
            for m in missing:
                h += 1
                self.update( m )
            self.tbx.config(height=h)
            self.tbx.config( bg="#ff0" )
            self.tbx.master.config( bg="#000" )
            self.update( "\nThis program will end when the\nwindow closes" )
            self.window.mainloop()
            sys.exit( 0 )

    def close( self ):
        self.window.destroy()
        sys.exit(0)

    def stopRunning( self ):
        global bRunning
        bRunning = False
        self.update( "Stopping", 0, 0)        

    def update( self, txt, counter=0, cMax=0):
        if cMax:
            tt = self.tbx.get("1.0", "end")
            if len( tt ) > 1:
                self.tbx.insert( self.tk.END, '\n' )
                self.lines += 1
            if self.lines > 4:
                self.tbx.delete( "1.0", "2.0" )
            self.tbx.insert( self.tk.END, txt )
        self.lbl.destroy()
        if cMax:
            self.lbl = self.tk.Label( self.frm, text=f"Command {counter} of {cMax}")
        else:
            self.lbl = self.tk.Label( self.frm, text=txt)
        self.lbl.pack(side=self.tk.LEFT)
        self.frm.update()
        self.window.update()

def doCloseDown():
    global bCloseDown

def doSkipTest():
    global bSkipTest
    bSkipTest = True

def doStart():
    global bRunning
    global bSkipTest
    
    if edlr.bDoneStart:
        return
    bSkipTest = False
    bRunning = True

    missing = {}

    findJS()
    for c in commands:
        for d in commands[ c ]:
            if not d in js:
                if d in missing:
                    missing[ d ] += 1
                else:
                    missing[ d ] = 1
    
    window = None
    window = Window( missing, doSkipTest, doCloseDown )
    if len( missing ) > 0:
        return False
    
    # Display the colour combination for each event to be displayed
    lCmd = len( commands )


    for p in ('fPath', 'pathToLEDControl'):
        setPath( p )

    bSkipTest = False
    ctr = 0
    for c in commands:
        if bSkipTest:
            break
        if not bRunning:
            break
        ctr += 1
        try:
            update( window, c, ctr, lCmd )              # show which command
        except:
            pass                            # most likely, window closed by user
        manage( '{"event":"' + c + '"}' )   # send command to devices
        time.sleep(2)

    if bSkipTest:
        update( window, "Test skipped" )
        time.sleep(2)
    else:
        update( window, "Test Complete" )
        time.sleep(1)

    try:
        update( window, "Closing Window" )
        time.sleep(2)
        window.close()
    except:
        pass                                # most likely, window closed by user
    
    doReset()
    edlr.bDoneStart = True
    # return window

def findJS():
    '''
    find devices currently attached
    '''
    import listJS

    jsl = listJS.listJoySticks()
    for j in jsl:
        js[ j[ 'oem_name' ] ] = j

def follow(thefile):
    '''
    generator function that yields new lines in a file
    '''
    global bTest
    
    if not bTest:
        # seek the end of the file
        thefile.seek(0, os.SEEK_END)
    cycle = 0
    isReset = False

    # start infinite loop
    while True:
        # read last line of file
        try:
            line = thefile.readline()
        except Error:
            print( f'Error: {Error}' )
            continue
        
        # sleep if file hasn't been updated
        if not line:
            if isReset == False:
                if cycle > config[ "resetTime" ]:
                     isReset = doReset()
            if cycle > config[ 'timeOut' ]: # 60:  we have had a minute of inaction - maybe we need a different file?
                return
            time.sleep(config[ 'sleepTime' ])
            cycle += config[ 'sleepTime' ]
            if bTest:
                print( ".", end=' ' )
            continue

        cycle = 0
        isReset = False
        yield line

def manage( line ):
    data = json.loads(line)
    
    if data[ "event" ] in commands:
        for k in commands[ data [ "event" ] ]:
            if bTest:
                print( f'{k}: -> {commands[ data [ "event" ] ][ k ]}' ) 
            doColour( k, cmd=commands[ data [ 'event' ] ][ k ])

def randomColour( cList=[ 1 ] ):
    import random
    return { 'Red': random.choice(cList), 'Green': random.choice(cList), 'Blue': random.choice(cList)}

def readConfig():
    global config
    
    cva = [ 0, 1, 2, 3 ]
    # cfFile = "EdLogReader.conf"
    configFile = open(f"{edlr.cfFile}","r")

    dNow = datetime.utcnow() - timedelta(milliseconds=1000)
    
    for line in configFile:
        data = json.loads(line)
        if 'Config' in data:
            config = data['Config']
            for d in config[ 'devices' ]:
                gNextColourTime[ d ] = dNow
        if not 'Interest' in data:
            continue
        if data[ 'Interest' ] == 0:
            continue

        actions = {}
        for k in data:
            if k in ['Event', 'Interest']:
                continue
            if data[ k ] == 'random':
                data[ k ] = randomColour( cva[:data[ 'Interest' ]+1] )

            if not 'cmd' in data[ k ]:
                data[ k ][ 'cmd' ] = dCmd
            
            actions[ k ] = data[ k ]

            # and handle potential user issues with colours
            if k != "cmd":
                for c in ['Red', 'Green', 'Blue' ]:
                    if not c in data[ k ]:
                        actions[ k ][ c ] = 0
                    elif data[ k ][ c ] >= len( cv ):
                        actions[ k ][ c ] = len( cv )-1
        commands[ data[ 'Event' ] ] = actions

def setPath( p ):
    q = f'__{p}__'

    if not q in config:
        path = ""
        s = config[ p ].split("%")
        for t in s:
            if len( t ):
                try:
                    o = os.getenv(t)
                    path += o
                except:
                    path += t
        config[ q ] = path

def update( window, txt, counter=0, cMax=0 ):
    try:
        window.update( txt, counter, cMax )
    except:
        print( txt )

def threaded_function():
    global bRunning
    doStart()
    # window = doStart()
    # try:
    #    window.close()
    # except:
    #    pass
    while bRunning:
        '''
        Change this bit
        '''
        # edlr.setPath( 'fPath' )
        logFileList = sorted( glob.glob(f"{config['__fPath__']}{edlr.fName}") )
        logfile = open(f"{logFileList[ -1 ]}","r")
		
        loglines = follow(logfile)

        # iterate over the generator
        for line in loglines:
            manage(line)
        logfile.close()
        time.sleep(config[ 'sleepTime' ])
    # window.close()
    sys.exit(0)

def main():    
    # enter test mode if we have a run-time argument 'test' (not in quotes on run line!)
    bTest = 'test' in [x.lower() for x in sys.argv]
    
    readConfig()
    thread = Thread(target = threaded_function)
    thread.daemon = True
    thread.start()
    thread.join()

if __name__ == '__main__':
    main()
