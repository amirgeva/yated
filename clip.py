#!/usr/bin/env python3
import sys
import atexit
import subprocess

impl = None

class qt_Clipboard:
    def __init__(self):
        from PyQt4 import QtGui
        self.app = QtGui.QApplication(sys.argv)
        self.clipboard = self.app.clipboard()
  
    def copy(self, text):
        self.clipboard.setText(text)
    
    def paste(self):
        return self.clipboard.text()
      
    def close(self):
        self.app.exit()


class xclip_Clipboard:
    def __init__(self):
        self.paste()
        
    def copy(self, text):
        p = subprocess.Popen(['xclip', '-i', '-selection', 'clipboard'], stdin=subprocess.PIPE)
        p.stdin.write(bytes(bytearray(text, 'utf-8')))
        p.stdin.close()
        
    def paste(self):
        try:
            return subprocess.check_output(['xclip', '-o', '-selection', 'clipboard']).decode("utf-8")
        except subprocess.CalledProcessError:
            return ''
    
    def close(self):
        pass


def cleanup():
    if impl is not None:
        impl.close()


atexit.register(cleanup)


def init_qt():
    global impl
    try:
        impl = qt_Clipboard()
    except ImportError:
        pass


def init_xclip():
    global impl
    try:
        impl = xclip_Clipboard()
    except FileNotFoundError:
        pass


def copy(text):
    if impl is not None:
        impl.copy(text)


def paste():
    if impl is None:
        return ''
    return impl.paste()


if impl is None:
    init_xclip()
if impl is None:
    init_qt()


def unit_test():
    copy("bla")
    if paste() != "bla":
        print("Failed")
    else:
        print("Success")


if __name__ == '__main__':
    unit_test()
