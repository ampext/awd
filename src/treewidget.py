from PySide import QtGui, QtCore
from tooltip import ImageTooltip

class TreeWidget(QtGui.QTreeWidget):
    def __init__(self, parent = None):
        QtGui.QTreeWidget.__init__(self)