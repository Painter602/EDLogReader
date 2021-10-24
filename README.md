# EDLogReader
A program to read Elite Dangerous Logs (journals) and to change the LEDs on Virpil controllers in response to events in Elite Dangerous (game).

In principal, this could be adapted to other JSON based log files.

## Required:
1. Elite Dangerous game

2. One or more Virpil devices

3. Virpil's VPC_LED_Control.exe program.  This is bundled with their VPC Software Setup files, download from: https://support.virpil.com/en/support/solutions/47000010107

4. Download one of the current release files (.zip files).

## After uploading
There are three configuration files:
1) conf.json
2) Left VPC WarBrd.conf.json
3) RIGHT VPC Stick WarBRD.conf.json

If you have just one joystick, rename or delete 'conf.json', and replace it with the appropriate left or right conf file.
This will save you having to delete un-needed joystick references in the file.

## **Edit your conf.json file**:
Set the path to your VPC_LED_Control.exe file - this will vary from system to system.

Make sure the device names and id correspond to your devices, check with your VPC Configuration Tool.

## Trouble shooting
1) The VPC_LED_Control.exe should be the same version as the VPC Configuration Tool used to configure your device.

2) The script checks that the device can be found. If not, stop the script, enable the device, and restart the script.

3) If Windows start stacking up on screen, stop the script, then close the windows.  Double check the name and id of your device(s) in configuration.
4) The executable relies on a Microsoft .dll ( VCRUNTIME140.dll).  That isn't included in the distribution, but most of us have a copy anyway.

   If for some reason you dont have the .dll, get it from Microsoft, here: https://visualstudio.microsoft.com/downloads/
   
   Scroll down and open Other Tools, Frameworks and Redistributables
   
   Look for Microsoft Visual C++ Redistributable for Visual Studio 2019
   
   Select the option that suits your PC, and click download.

## How does this relate to Joystick Gremlin or other helper programes?
~~I run this script in parallel with Joystick Gremlin (JG, link: https://whitemagic.github.io/JoystickGremlin/ ).~~

I used to run the script in parallel with JoystickGremlin, but I stopped using JG.

JG is not required to run this script.

## Contact
Either raise an issue here ( https://github.com/Painter602/EDLogReader/issues ), or message me (Painter) on Virpil's forum

## Licence
 GPL-2.0 License, part Unlicense (unlicense.org)

## Acknowledgements
Elite Dangerous is a trade mark of Frontier Developments plc, 26 Science Park, Milton Road, Cambridge, CB4 0FP, England, UK

Virpil is a trade mark of  TERRAZYT PLUS LTD, Gorkogo St., 91-1, Grodno, 230005, Belarus 

## Thank-you
Thank-you to Fixitman for finding the commands for the CM3 throttle and for testing.
