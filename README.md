# EDLogReader
Script to read Elite Dangerous Logs (journals) and to change the LEDs on Virpil controllers in response to events in Elite Dangerous (game).

In principal, this could be adapted to other JSON based log files.

# Required:
1) Elite Dangerous game

2) One or more Virpil devices

3) Virpil's VPC_LED_Control.exe program.  This is bundled with their VPC Software Setup files, download from: https://support.virpil.com/en/support/solutions/47000010107

4) A Python runtime environment, or Python compiler.  The Python environment can be downloaded from https://www.python.org/downloads/

   The script was written for Python 3.9.

   It will not work with versions 2.x or earlier.

# Nice to have:
The script can run from the command line or from Python's IDLE.

I built an executable from my copy using a Python compiler.

There are several Python compilers out there.  I used py2exe, but suggest you research available options, and select the one best suited to you.

# Why not distribute an executable version?
Simple answer, I do not have a Microsoft compiler with the necessary licences to do so.

# After uploading
There are three configuration files:
1) conf.json
2) Left VPC WarBrd.conf.json
3) RIGHT VPC Stick WarBRD.conf.json

If you have just one joystick, rename or delete 'conf.json', and replace it with the appropriate left or right conf file.
This will save you having to delete un-needed joystick references in the file.

Edit your conf.json file:
Set the path to your VPC_LED_Control.exe file - this will vary from system to system.

Make sure the device names and id correspond to your devices, check with your VPC Configuration Tool.

# Trouble shooting
1) The VPC_LED_Control.exe should be the same version as the VPC Configuration Tool used to configure your device.

2) The script checks that the device can be found. If not, stop the script, enable the device, and restart the script.

3) If Windows start stacking up on screen, stop the script, then close the windows.  Double check the name and id of your device(s) in configuration.

# How does this relate to Joystick Gremlin or other helper programes?
I run this script in parallel with Joystick Gremlin (JG, link: https://whitemagic.github.io/JoystickGremlin/ ).

JG is not required to run this script.
