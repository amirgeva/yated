import sys
import atexit

impl=None
copy_func=None
paste_func=None

class qt_Clipboard:
    def __init__(self):
        from PyQt4 import QtGui
        self.app=QtGui.QApplication(sys.argv)
        self.clipboard=self.app.clipboard()
        global copy_func
        global paste_func
        copy_func=self.copy
        paste_func=self.paste
  
    def copy(self,text):
        self.clipboard.setText(text)
    
    def paste(self):
        return self.clipboard.text()
      
    def close(self):
        self.app.exit()


def cleanup():
    if not impl is None:
        impl.close()

atexit.register(cleanup)

def init_qt():
    global impl
    try:
        impl=qt_Clipboard()
    except ImportError:
        pass

def copy(text):
    if not copy_func is None:
        copy_func(text)

def paste():
    if paste_func is None:
        return ''
    return paste_func()

if impl is None:
    init_qt()

