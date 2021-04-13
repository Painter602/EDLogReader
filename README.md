# EDLogReader
Script to read Elite Dangerous Logs (journals) and to change the LEDs on Virpil controllers in response to events in Elite Dangerous (game).

In principal, this could be adapted to other JSON based log files.

### Back-story
Originally, this program was written in Python for my eco-system (two Virpil Alpha joysticks on WarBRD bases).

It has been tested by somebody who has a Virpil throttle, and, after editing the conf.json file, it worked with his devices too.

## Required:
1) Elite Dangerous game

2) One or more Virpil devices

3) Virpil's VPC_LED_Control.exe program.  This is bundled with their VPC Software Setup files, download from: https://support.virpil.com/en/support/solutions/47000010107

## After uploading
There are three configuration files:
1) conf.json
2) Left VPC WarBrd.conf.json
3) RIGHT VPC Stick WarBRD.conf.json

If you have just one joystick, rename or delete 'conf.json', and replace it with the appropriate left or right conf file.
This will save you having to delete un-needed joystick references in the file.

Edit your conf.json file:
Set the path to your VPC_LED_Control.exe file - this will vary from system to system.

Make sure the device names and id correspond to your devices, check with your VPC Configuration Tool.

## Trouble shooting
1) The VPC_LED_Control.exe should be the same version as the VPC Configuration Tool used to configure your device.

2) The script checks that the device can be found. If not, stop the script, enable the device, and restart the script.

3) If Windows start stacking up on screen, stop the script, then close the windows.  Double check the name and id of your device(s) in configuration.

## How does this relate to Joystick Gremlin or other helper programes?
I run this script in parallel with Joystick Gremlin (JG, link: https://whitemagic.github.io/JoystickGremlin/ ).

JG is not required to run this script.

## To Do
### Configuration Front End
We need a front end.  Writing and editing a large .json file (conf.json) is not fun, and can introduce obscure errors.

### Language files
Files named lang.??.json, where ?? is the international two character lanuage code.  In principal, the five character country code would work: for example en, en-EN, and en-US. 
The English language file is the most up-to-date.  Inturprutations need to be added, and many existing ones can be deleted, and the scripts trawlled for hard-coded text.
The other language files are very out-of-date.  They are based on an earlier version of the English language file, and rely on machine translation.

Translations for other languages are possible.


## Contact
Either:
* Raise an issue on github ( https://github.com/Painter602/EDLogReader/issues ), or message me (Painter) on Virpil's forum.
* There is a thread **Elite Dangerous and Virpil LEDs** in Virpil's forum ( https://forum.virpil.com/index.php?/topic/3500-elite-dangerous-and-virpil-leds/ ) - give me a heads-up ( @Painter) if you post there, so I know to check.
* I'm also on Discord.

## Licence
 GPL-2.0 License, part Unlicense (unlicense.org)

## Acknowledgemnts
Elite Dangerous is a trade mark of Frontier Developments plc, 26 Science Park, Milton Road, Cambridge, CB4 0FP, England, UK

Virpil is a trade mark of  TERRAZYT PLUS LTD, Gorkogo St., 91-1, Grodno, 230005, Belarus 

## Thank-you
Thank-you to Fixitman for finding the commands for the CM3 throttle and for testing.
