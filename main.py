__author__ = 'Галлям'

from PyQt5 import QtWidgets
import sys
from gui.gui import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())