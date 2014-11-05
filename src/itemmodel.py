from PySide import QtCore, QtGui, QtSql

import db
import helper
import defaults

class TreeItem(object):
    def __init__(self, model, parent = None, name = ""):
        self.model = model
        self.parentItem = parent
        self.childItems = []
        
        self.asin = ""
        self.label = ""
        self.price = 0
        self.priceMin = 0
        self.priceMax = 0
        self.priceLast = 0
        self.country = ""
        self.priceSeries = []
        
    def appendChild(self, item):
        item.parentItem = self
        self.childItems.append(item)
        
    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.model.headerItem)

    def data(self, column):       
        if column == self.model.asinColumn(): return self.asin
        if column == self.model.labelColumn(): return self.label
        if column == self.model.priceColumn(): return db.FormatPrice(self.price, self.country)
        if column == self.model.priceLastColumn(): return db.FormatPrice(self.priceLast, self.country)
        if column == self.model.priceMinColumn(): return db.FormatPrice(self.priceMin, self.country)
        if column == self.model.priceMaxColumn(): return db.FormatPrice(self.priceMax, self.country)
        if column == self.model.chartColumn(): return self.priceSeries
        
        return None

    def parent(self):
        return self.parentItem

    def getparent(self):
        return self.parentItem
    
    def row(self):
        if self.parentItem: return self.parentItem.childItems.index(self)
        return 0

class ItemModel(QtCore.QAbstractItemModel):
    def __init__(self, parent = None):
        QtCore.QAbstractItemModel.__init__(self, parent)
        
        self.headerItem = [self.tr(""), self.tr("ASIN"), self.tr("Label"), self.tr("Price"), self.tr("Last"), self.tr("Min"), self.tr("Max"), self.tr("Chart")]
        
        self.upTextForegroundColor = defaults.GetTextUpForegroundColor()
        self.downTextForegroundColor = defaults.GetTextDownForegroundColor()
        self.nSamples = defaults.GetNumSamples()
        
    def update(self):
        query = QtSql.QSqlQuery()
        query.exec_("SELECT * FROM main")

        self.beginResetModel()

        self.rootItem = TreeItem(self)
        cntr = 0
        
        while query.next():
            record = query.record()
            
            item = TreeItem(self)
            
            item.asin = record.field("asin").value()
            item.label = record.field("label").value()
            item.price = int(record.field("price").value())
            item.priceMin = int(record.field("min").value())
            item.priceMax = int(record.field("max").value())
            item.priceLast = int(record.field("last").value())
            item.country = record.field("country").value()
            item.priceSeries = db.GetNLastPriceChanges(item.asin, self.nSamples)
            
            self.rootItem.appendChild(item)
            
        if helper.debug_mode:
            print("model updated: {0} item(s)".format(self.rootItem.childCount()))
            
        self.endResetModel()
            
    def SetNumSamples(self, n):
        if self.nSamples != n:
            self.nSamples = n
            self.update()
        
    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headerItem[section]
        
    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        
    def columnCount(self, parent = QtCore.QModelIndex()):
        return len(self.headerItem)
    
    def rowCount(self, parent = QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0
        
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
            
        return parentItem.childCount()
    
    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        childItem = parentItem.child(row)
        
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()
    
    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        
        item = index.internalPointer()
        parentItem = item.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()
        
        return self.createIndex(index.row(), 0, parentItem)
    
    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()
        if not item:
            return None
    
        column = index.column()
        
        if role == QtCore.Qt.DisplayRole:
            return item.data(column)
        
        if role == QtCore.Qt.TextColorRole:
            if column == self.priceColumn() or column == self.priceLastColumn():
                if item.price != 0 and item.priceLast != 0:
                    if item.priceLast > item.price: return self.downTextForegroundColor 
                    if item.priceLast < item.price: return self.upTextForegroundColor 
                
        if role == QtCore.Qt.DecorationRole:
            if column == self.countryColumn():
                return helper.GetCountryIcon(item.country)
        
        return None
    
    def item(self, index):
        if not index.isValid():
            return None

        return index.internalPointer()
    
    def asin(self, index):
        if not index.isValid():
            return ""
        
        item = index.internalPointer()
        if not item:
            return None
        
        return item.asin
    
    def countryColumn(self):
        return 0
    
    def asinColumn(self):
        return 1
        
    def labelColumn(self):
        return 2
        
    def priceColumn(self):
        return 3
        
    def priceLastColumn(self):
        return 4
        
    def priceMinColumn(self):
        return 5
        
    def priceMaxColumn(self):
        return 6
        
    def chartColumn(self):
        return 7
        