import sys
import atexit

app=None
clipboard=None

def closeApp():
    if not app is None:
        app.exit()

try:
    from PyQt4 import QtGui
    app=QtGui.QApplication(sys.argv)
    atexit.register(closeApp)
    clipboard=app.clipboard()
except ImportError:
    pass

def copy(text):
    if not clipboard is None:
        clipboard.setText(text)

def paste():
    if clipboard is None:
        return ''
    return clipboard.text()
