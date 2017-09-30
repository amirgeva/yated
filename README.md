# Yet Another Text EDitor

This is a terminal based text editor, inspired by a wish to have 
an editor with default visual and key bindings that resemble typical
GUI based editors.

Written in Python and relying on the curses module, support for various
key combinations varies with system and terminal.

So far, best results are seen in the _gnome-terminal_

Depends on either xclip or python3-pyqt4 for clipboard operations

Install with apt:

    sudo apt install python3 python3-pip xclip
    sudo pip3 install yated


Main features:

* Simple arrow based navigation
* Ctrl-left/right for next prev word
* Text selection with shifted arrows
* Block indentation with tab
* Block C/C++ comment with //
* Menu to help find commands / options
* Simple macro recording
* Text search with case/whole word/regex support
* Fast.  Loading 100Mb file takes about 1 second, compared to 40 seconds on gedit
* For simplicity, tabs are replaced by spaces (size configurable)
