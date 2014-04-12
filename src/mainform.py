from PySide import QtGui, QtCore, QtSql
from itemform import ItemForm
from settingsform import SettingsForm, to_bool
from requestform import RequestForm
from aboutform import AboutForm
from threading import Thread
from functools import partial
from chart import ChartItemDelegate, ChartDataProvider
from aws import GetAttributes

import db_helper
import helper
import notify


class MainForm(QtGui.QDialog): 
    db_updated = QtCore.Signal(int, int, int, str)

    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        
        layout = QtGui.QVBoxLayout()
        subLayout = QtGui.QHBoxLayout()
        
        addButton = QtGui.QPushButton(self.tr("Add item..."), self)
        addButton.clicked.connect(self.OnAddItem)
        subLayout.addWidget(addButton)
        
        self.removeButton = QtGui.QPushButton(self.tr("Remove item"), self)
        self.removeButton.clicked.connect(self.OnRemoveItem)
        subLayout.addWidget(self.removeButton)
        
        self.editButton = QtGui.QPushButton(self.tr("Edit item..."), self)
        self.editButton.clicked.connect(self.OnEditItem)
        subLayout.addWidget(self.editButton)
        
        self.removeButton.setEnabled(False)
        self.editButton.setEnabled(False)
        
        updateButton = QtGui.QPushButton(self.tr("Update"), self)
        updateButton.clicked.connect(self.OnUpdateItems)
        subLayout.addWidget(updateButton)

        layout.addLayout(subLayout)
        
        headers = [self.tr(""), self.tr("ASIN"), self.tr("Label"), self.tr("Price"), self.tr("Last"), self.tr("Min"), self.tr("Max"), self.tr("Chart")]
        
        self.listView = QtGui.QTreeWidget()
        self.listView.setHeaderLabels(headers)
        self.listView.setRootIsDecorated(False)
        
        self.countryColumn, self.asinColumn, self.labelColumn, self.priceColumn, self.lastColumn, self.minColumn, self.maxColumn, self.chartColumn = range(0, 8)
        
        self.listView.setColumnWidth(self.countryColumn, 20)
        self.listView.setColumnWidth(self.asinColumn, 100)
        self.listView.setColumnWidth(self.labelColumn, 210)
        self.listView.setColumnWidth(self.priceColumn, 70)
        self.listView.setColumnWidth(self.lastColumn, 70)
        self.listView.setColumnWidth(self.minColumn, 70)
        self.listView.setColumnWidth(self.maxColumn, 70)
        self.listView.setColumnWidth(self.chartColumn, 30)
        
        self.listView.itemSelectionChanged.connect(self.OnItemSelectionChanged)
        
        layout.addWidget(self.listView)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.OnTimer)
        self.timer.start()
        
        self.CreateActions()
        self.CreateTray()
        
        self.tray.show()
        
        self.setLayout(layout)
        self.resize(640, 200);
        self.setWindowTitle(self.tr("Items list"))
        self.setWindowIcon(QtGui.QIcon("images" + QtCore.QDir.separator() + "tray.png"))

        self.db_updated.connect(self.DoUpdateItems)
        
        self.timer.setInterval(60000 * 20)
        self.hideAfterStart = True
        self.showNotifications = True
        self.settings = QtCore.QSettings(helper.GetConfigDir() + QtCore.QDir.separator() + helper.GetConfigName(), QtCore.QSettings.IniFormat, self)
        
        self.seriesProvider = ChartDataProvider()
        self.seriesProvider.Update()
        
        self.LoadSettings()
        self.LoadCountryIcons()
        self.UpdateListView()
        
        if self.hideAfterStart: self.hide()
        else: self.show()

    def CreateTray(self):
        self.tray = QtGui.QSystemTrayIcon(self)
        self.trayMenu = QtGui.QMenu(self)
        
        self.trayMenu.addAction(self.updateAction)
        self.trayMenu.addAction(self.itemsAction)
        self.trayMenu.addAction(self.settingsAction)
        
        if helper.debug_mode:
            self.trayMenu.addSeparator()
            self.trayMenu.addAction(self.builderAction)
        
        self.trayMenu.addSeparator()
        self.trayMenu.addAction(self.aboutAction)
        self.trayMenu.addAction(self.quitAction)
        
        self.tray.setContextMenu(self.trayMenu)
        self.tray.setIcon(QtGui.QIcon("images" + QtCore.QDir.separator() + "tray.png"))
        self.tray.activated.connect(self.OnTrayActivated)
        
    def CreateActions(self):
        self.settingsAction = QtGui.QAction(self.tr("Settings..."), self)
        self.settingsAction.triggered.connect(self.OnShowSettings)
        
        self.itemsAction = QtGui.QAction(self.tr("Items..."), self)
        self.itemsAction.triggered.connect(self.show)
        
        self.updateAction = QtGui.QAction(self.tr("Update"), self)
        self.updateAction.triggered.connect(self.OnUpdateItems)
        
        self.quitAction = QtGui.QAction(self.tr("Quit"), self)
        self.quitAction.triggered.connect(self.exit)

        self.aboutAction = QtGui.QAction(self.tr("About..."), self)
        self.aboutAction.triggered.connect(self.OnAbout)
        
        if helper.debug_mode:
            self.builderAction = QtGui.QAction(self.tr("Build request..."), self)
            self.builderAction.triggered.connect(self.OnBuildRequest)

    def OnTimer(self):
        self.OnUpdateItems()
        
    def OnTrayActivated(self, reason):
        if reason == QtGui.QSystemTrayIcon.DoubleClick:
            if self.isHidden(): self.show()
            else: self.hide()

    def OnAbout(self):
        form = AboutForm(self)
        form.exec_()

    def exit(self):
        self.SaveSettings()
        QtGui.qApp.quit()

    def closeEvent(self, event):
        self.hide()
        event.ignore()
        
    def contextMenuEvent(self, event):
        asin = self.GetSelectedASIN()
        
        menu = QtGui.QMenu(self)
        
        urlAction = menu.addAction(self.tr("Open URL"))
        urlAction.triggered.connect(lambda: self.OnOpenURL(asin))
        
        asinAction = menu.addAction(self.tr("Copy ASIN"))
        asinAction.triggered.connect(lambda: self.OnCopyASIN(asin))
        
        if helper.debug_mode:
            attrsAction = menu.addAction(self.tr("Get attributes..."))
            attrsAction.triggered.connect(lambda: self.OnGetAttributes(asin))            
        
        menu.exec_(event.globalPos())

    def GetSelectedASIN(self):
        item = self.listView.currentItem()
        
        if item is None: return ""
        return item.text(self.asinColumn)

    def LoadCountryIcons(self):
        self.icons = {}
        
        for country in db_helper.GetAmazonCountries():
            self.icons[country] = QtGui.QIcon("images" + QtCore.QDir.separator() + country + ".png")            

    def GetCountryIcon(self, country):
        if self.icons.has_key(country): return self.icons[country]
        return None

    def UpdateListView(self):
        query = QtSql.QSqlQuery()
        query.exec_("SELECT * FROM main")
        
        self.seriesProvider.Update()

        self.listView.clear()
        cntr = 0
        
        while query.next():
            record = query.record()
            item = QtGui.QTreeWidgetItem()
            
            asin = record.field("asin").value()
            price = int(record.field("price").value())
            min = int(record.field("min").value())
            max = int(record.field("max").value())
            last = int(record.field("last").value())
            country = record.field("country").value()
            icon = self.GetCountryIcon(country)
            
            item.setData(self.countryColumn, QtCore.Qt.UserRole, db_helper.GetAmazonCountries().index(country))
            
            if icon != None: item.setIcon(self.countryColumn, icon)
            item.setText(self.asinColumn, asin)
            item.setText(self.labelColumn, record.field("label").value())
            
            if price <= 0: item.setText(self.priceColumn, "n/a") 
            else: item.setText(self.priceColumn, db_helper.FormatPrice(price, country))
            
            if last <= 0: item.setText(self.lastColumn, "n/a")
            else: item.setText(self.lastColumn, db_helper.FormatPrice(last, country))
            
            if min <= 0: item.setText(self.minColumn, "n/a") 
            else: item.setText(self.minColumn, db_helper.FormatPrice(min, country))
            
            if max <= 0: item.setText(self.maxColumn, "n/a")
            else: item.setText(self.maxColumn, db_helper.FormatPrice(max, country))
            
            if last > price and price != 0 and last != 0:
                item.setForeground(self.priceColumn, QtGui.QColor(0, 128, 0))
                item.setForeground(self.lastColumn, QtGui.QColor(0, 128, 0))
            if last < price and price != 0 and last != 0: 
                item.setForeground(self.priceColumn, QtGui.QColor(255, 0, 0))
                item.setForeground(self.lastColumn, QtGui.QColor(255, 0, 0))
            

            self.seriesProvider.SetRow2Asin(cntr, asin)
            cntr = cntr + 1

            self.listView.addTopLevelItem(item)
            self.listView.setItemDelegateForColumn(self.chartColumn, ChartItemDelegate(self.listView, self.seriesProvider))

    def OnItemSelectionChanged(self):
        enable_editing = len(self.listView.selectedItems()) > 0
        
        self.removeButton.setEnabled(enable_editing)
        self.editButton.setEnabled(enable_editing)
    
    def OnAddItem(self):
        form = ItemForm(self, self.icons)
        if form.exec_() == QtGui.QDialog.Accepted:
            self.UpdateListView()
        
    def OnEditItem(self):
        form = ItemForm(self, self.icons, self.GetSelectedASIN())
        if form.exec_() == QtGui.QDialog.Accepted: self.UpdateListView()
        
    def OnRemoveItem(self):
        if QtGui.QMessageBox.warning(self, self.tr("Warning"), self.tr("Delete this item from database?"),
        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No) == QtGui.QMessageBox.No: return
        
        db_helper.DeleteItem(self.GetSelectedASIN())
        
        self.UpdateListView()
        
    def OnUpdateItems(self):
        if self.accessKey == "" or self.secretKey == "" or self.associateTag == "":
            QtGui.QMessageBox.warning(self, self.tr("Warning"),
            self.tr("Amazon access parameters are not set. Go to \"Settings\" dialog and fill corresponded fields"))
            return

        thread = Thread(target = self.UpdateDatabase)
        thread.start()
        
    def UpdateDatabase(self):
        result = db_helper.UpdateDatabase(self.accessKey, self.secretKey, self.associateTag)
        self.db_updated.emit(result[0], result[1], result[2], result[3])
        
    def DoUpdateItems(self, cntr, up, down, error):
        if error != "" and cntr == 0:
            notify.Notify(error, self, self.sys_notify)
            print(error)
            return
        
        if not self.showNotifications: return
        
        text = str(cntr) + self.tr(" items have been updated")
        if error != "": text += "\n" + error
        
        notify.Notify(text, self, self.sys_notify)
        self.UpdateListView()
        
    def OnShowSettings(self):
        form = SettingsForm(self, self.settings)
        if form.exec_() == QtGui.QDialog.Accepted: self.LoadSettings()
        
    def OnBuildRequest(self):
        form = RequestForm(self, self.icons, self.accessKey, self.secretKey, self.associateTag)
        form.exec_()
        
    def SaveSettings(self):
        self.settings.setValue("mainform_size", self.size())
        self.settings.sync()
            
    def LoadSettings(self):
        self.timer.setInterval(60000 * int(self.settings.value("interval", 20)))
        self.hideAfterStart = to_bool(self.settings.value("hide", "true"))
        self.showNotifications = to_bool(self.settings.value("notifications", "true"))
        self.accessKey = str(self.settings.value("access_key", ""))
        self.secretKey = str(self.settings.value("secret_key", ""))
        self.associateTag = str(self.settings.value("associate_tag", ""))
        self.resize(self.settings.value("mainform_size", QtCore.QSize(640, 200)))
        self.sys_notify = to_bool(self.settings.value("sys_notify", "false"))
        
    def OnCopyASIN(self, asin):
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(asin)
        
    def OnOpenURL(self, asin):
        country = db_helper.GetItemCountry(asin)    
        domain = db_helper.GetDomain(country)
        
        if not domain or not asin: return
        
        url = "http://amzn." + domain + "/" + asin
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        
    def OnGetAttributes(self, asin):

        try:
            country = db_helper.GetItemCountry(asin)
            attrs = GetAttributes(asin, country, self.accessKey, self.secretKey, self.associateTag)
            print(attrs)
        except Exception, e:
            notify.Notify(e.GetFullDescription(), self, self.sys_notify)