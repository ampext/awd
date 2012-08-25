from PySide import QtGui, QtCore, QtSql

countryColumn, asinColumn, labelColumn, priceColumn, lastColumn, minColumn, maxColumn = range(0, 7)

class TreeWidgetItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent = None):
        QtGui.QTreeWidgetItem.__init__(self, parent)
        
    def __ge__(self, item):
        pass
    
    def __lt__(self, ite,):
        pass