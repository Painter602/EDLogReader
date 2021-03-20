"""
    List Joysticks - and other game input devices

    This is a cut down and modified version of rdb's js_winmm.py
    found at: https://gist.github.com/rdb/8883307 as at 26 Jan 2021

    ---------------------------------------------------
    
    Released by rdb under the Unlicense (unlicense.org)
    Further reading about the WinMM Joystick API:
    http://msdn.microsoft.com/en-us/library/windows/desktop/dd757116(v=vs.85).aspx
    Adapted by Painte4r602

"""

def listJoySticks():

    ret = []

    import ctypes
    import winreg
    from ctypes.wintypes import WORD, UINT, DWORD
    from ctypes.wintypes import WCHAR as TCHAR
    import re

    # Fetch function pointers
    joyGetNumDevs = ctypes.windll.winmm.joyGetNumDevs
    joyGetDevCaps = ctypes.windll.winmm.joyGetDevCapsW

    # Define constants
    MAXPNAMELEN = 32
    MAX_JOYSTICKOEMVXDNAME = 260

    # Define some structures from WinMM that we will use in function calls.
    class JOYCAPS(ctypes.Structure):
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

    # Get the number of supported devices (usually 16).
    num_devs = joyGetNumDevs()
    if num_devs == 0:
        print("Joystick driver not loaded.")

    # Number of the joystick to open.
    for joy_id in range( num_devs ):
        js = {}
        js[ 'joy_id' ] = joy_id
        # Get device capabilities.
        caps = JOYCAPS()
        if joyGetDevCaps(joy_id, ctypes.pointer(caps), ctypes.sizeof(JOYCAPS)) != 0:
            continue
            # print("Failed to get device capabilities.")
        # Fetch the name from registry.
        key = None
        if len(caps.szRegKey) > 0:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "System\\CurrentControlSet\\Control\\MediaResources\\Joystick\\%s\\CurrentJoystickSettings" % (caps.szRegKey))
            except WindowsError:
                key = None
        if key:
            js[ 'key' ] = key
            oem_name = winreg.QueryValueEx(key, "Joystick%dOEMName" % (joy_id + 1))
            did = re.split(r'([_&]+)', oem_name[ 0 ])
            vid = ''
            pid = ''
            if did[ 0 ] == 'VID':
                js[ 'vid' ] = did[ 2 ]
            if did[ 4 ] == 'PID':
                js[ 'pid' ] = did[ 6 ]
            if oem_name:
                key2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "System\\CurrentControlSet\\Control\\MediaProperties\\PrivateProperties\\Joystick\\OEM\\%s" % (oem_name[0]))
                if key2:
                    oem_name = winreg.QueryValueEx(key2, "OEMName")
                    # print("OEM name:", oem_name[0])
                    js[ 'oem_name' ] = oem_name[ 0 ]
                key2.Close()
        for k in ( 'wMid', 'wPid', 'szPname', 'wXmin', 'wXmax',  'wYmin',
                   'wYmax', 'wZmin', 'wZmax', 'wNumButtons', 'wPeriodMin',
                   'wPeriodMax', 'wRmin', 'wRmax', 'wUmin', 'wUmax', 'wVmin',
                   'wVmax', 'wCaps', 'wMaxAxes', 'wNumAxes', 'wMaxButtons',
                   'szRegKey', 'szOEMVxD' ):
            js[ k ] = eval( f'caps.{ k }' )
        ret.append( js )
    return ret


if __name__ == '__main__':
    js = listJoySticks()
    for j in js:
        for k in j:
            print( f'{k}: {j[k]}' )
        print( ' .' * 12 )
