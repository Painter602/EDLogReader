# ED Log Reader
## Change log
### 10 Apr 2021
Added ability to scroll output text widget.  The widget is limited to 500 lines.

Added a pause button.  Pausing the feed changes to colour of the output text widget as a clue to the chjanged state.

Bug fixes

To-do: switching to (or from) the display devices mode is slow.

#### 0.02
Small change to the way config files are loaded

### 9 Apr 2021
Rearranged buttons, and added tool-tips.
Lots of bugs chased down and removed.

### 8 Apr 2021
Revised calls to the main window so that the script is more responsive.
Moved most buttons into menu options, removing the buttons.
Removed 'Skip Device Testing' button, replacing it with a run-time test.

Removed most command line options.
Started preparations for multi-language support.

Extended the range of commands in the English language translations file.

###  7 Apr 2021
Change to the way the script works.
It now holds a window open while checking the ED log files.

If the log file is quiet (unchanging), the script reports that it is checking the files.  Note, this implies not much is happening in the game.

If there are a lot of events in the file (and, by implication, in game), then that *should* be reflected in changes to the device LEDs.
The Log Reader window is quiet at these times.

Created this Change log

## Historical changes (pre-dating this log)

###  6 Apr 2021
Fixed an issue where EdLogReader checks the attached devices match the config file.
The script should now show better feedback if a device in config is not attached to the PC.


###  5 Apr 2021
Added licence information to this file, and to start of shared.py and EdLogReader.py

Updated EdLogReader.py to set several buttons on the same device simultaneously in response to in game events.

Changed Configuration file structure to accomodate the multiple-buttons (for the changes, see comments in configuration file).

Added/changed command line parameters

Changed the function and variable names to be more readable (code fixes).

Various minor bug fixes.
