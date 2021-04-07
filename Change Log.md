# ED Log Reader
## Change log
#### 7 Apr 2021
Change to the way the script works.
It now holds a window open while checking the ED log files.

If the log file is quiet (unchanging), the script reports that it is checking the files.  Note, this implies not much is happening in the game.

If there are a lot of events in the file (and, by implication, in game), then that *should* be reflected in changes to the device LEDs.
The Log Reader window is quiet at these times.

Created this Change log

#### 5 Apr 2021
Added licence information to this file, and to start of shared.py and EdLogReader.py

Updated EdLogReader.py to set several buttons on the same device simultaneously in response to in game events.

Changed Configuration file structure to accomodate the multiple-buttons (for the changes, see comments in configuration file).

Added/changed command line parameters

Changed the function and variable names to be more readable (code fixes).

Various minor bug fixes.
