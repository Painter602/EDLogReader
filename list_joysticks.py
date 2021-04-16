"""
    List Joysticks - and other game input devices

    This is a cut down and modified version of rdb's js_winmm.py
    found at: https://gist.github.com/rdb/8883307 as at 26 Jan 2021

    ---------------------------------------------------

    Released by rdb under the Unlicense (unlicense.org)
    Further reading about the WinMM Joystick API:
    http://msdn.microsoft.com/en-us/library/windows/desktop/dd757116(v=vs.85).aspx

    Adapted by Painter602


    Unlicence:
    This is free and unencumbered software released into the public domain.

    Anyone is free to copy, modify, publish, use, compile, sell, or
    distribute this software, either in source code form or as a compiled
    binary, for any purpose, commercial or non-commercial, and by any
    means.

    In jurisdictions that recognize copyright laws, the author or authors
    of this software dedicate any and all copyright interest in the
    software to the public domain. We make this dedication for the benefit
    of the public at large and to the detriment of our heirs and
    successors. We intend this dedication to be an overt act of
    relinquishment in perpetuity of all present and future rights to this
    software under copyright law.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
    OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

    For more information, please refer to <http://unlicense.org/>
"""


import ctypes
import winreg
from ctypes.wintypes import WORD, UINT
from ctypes.wintypes import WCHAR as TCHAR
import re

CTL_PATH = "System\\CurrentControlSet\\Control"
MAXPNAMELEN = 32
MAX_JOYSTICKOEMVXDNAME = 260

# Define some structures from WinMM that we will use in function calls.
class JOYCAPS(ctypes.Structure):
    '''
    Data structure for Joystick capabilities
    '''
    _fields_ = [
        ('wMid', WORD),
        ('wPid', WORD),
        ('szPname', TCHAR * MAXPNAMELEN),
        ('wXmin', UINT),
        ('wXmax', UINT),
        ('wYmin', UINT),
        ('wYmax', UINT),
        ('wZmin', UINT),
        ('wZmax', UINT),
        ('wNumButtons', UINT),
        ('wPeriodMin', UINT),
        ('wPeriodMax', UINT),
        ('wRmin', UINT),
        ('wRmax', UINT),
        ('wUmin', UINT),
        ('wUmax', UINT),
        ('wVmin', UINT),
        ('wVmax', UINT),
        ('wCaps', UINT),
        ('wMaxAxes', UINT),
        ('wNumAxes', UINT),
        ('wMaxButtons', UINT),
        ('szRegKey', TCHAR * MAXPNAMELEN),
        ('szOEMVxD', TCHAR * MAX_JOYSTICKOEMVXDNAME),
        ]

    def get( self, field ):
        '''
        Get the value of a field
        '''
        return eval( f'self.{field}' )


def list_joy_sticks():
    '''
    Generate a list of available joysticks
    '''

    ret = []

    # Fetch function pointers
    joy_get_num_devs = ctypes.windll.winmm.joyGetNumDevs
    joy_get_dev_caps = ctypes.windll.winmm.joyGetDevCapsW

    # Define constants
    # Get the number of supported devices (usually 16).
    num_devs = joy_get_num_devs()
    if num_devs == 0:
        print("Joystick driver not loaded.")

    # Number of the joystick to open.
    for joy_id in range( num_devs ):
        joy_stick = {}
        joy_stick[ 'joy_id' ] = joy_id
        # Get device capabilities.
        caps = JOYCAPS()
        if joy_get_dev_caps(joy_id, ctypes.pointer(caps), ctypes.sizeof(JOYCAPS)) != 0:
            continue
            # print("Failed to get device capabilities.")
        # Fetch the name from registry.
        # key = None
        if len(caps.szRegKey) > 0:
            try:
                resource = '\\MediaResources\\Joystick\\'
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        f"{CTL_PATH}{resource}{caps.szRegKey}\\CurrentJoystickSettings")
            except WindowsError:
                key = None
        if key:
            joy_stick[ 'key' ] = key
            oem_name = winreg.QueryValueEx(key, "Joystick%dOEMName" % (joy_id + 1))
            did = re.split(r'([_&]+)', oem_name[ 0 ])
            if did[ 0 ] == 'VID':
                joy_stick[ 'vid' ] = did[ 2 ]
            if did[ 4 ] == 'PID':
                joy_stick[ 'pid' ] = did[ 6 ]
            if oem_name:
                resource = '\\MediaProperties\\PrivateProperties\\Joystick\\'
                key2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        f"{CTL_PATH}{resource}OEM\\{oem_name[0]}")
                if key2:
                    oem_name = winreg.QueryValueEx(key2, "OEMName")
                    # print("OEM name:", oem_name[0])
                    joy_stick[ 'oem_name' ] = oem_name[ 0 ]
                key2.Close()
        for k in ( 'wMid', 'wPid', 'szPname', 'wXmin', 'wXmax',  'wYmin',
                   'wYmax', 'wZmin', 'wZmax', 'wNumButtons', 'wPeriodMin',
                   'wPeriodMax', 'wRmin', 'wRmax', 'wUmin', 'wUmax', 'wVmin',
                   'wVmax', 'wCaps', 'wMaxAxes', 'wNumAxes', 'wMaxButtons',
                   'szRegKey', 'szOEMVxD' ):
            joy_stick[ k ] = caps.get( k )
        ret.append( joy_stick )
    return ret


if __name__ == '__main__':
    joy_sticks = list_joy_sticks()
    for stick in joy_sticks:
        for attribute in stick:
            print( f'{attribute}: {stick[attribute]}' )
        print( ' .' * 12 )
