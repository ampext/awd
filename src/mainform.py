from PySide import QtGui, QtCore, QtSql
from itemform import ItemForm
from settingsform import SettingsForm, to_bool
from requestform import RequestForm
from aboutform import AboutForm
from waitwidget import WaitWidget
from tooltip import ImageToolTip
from worker import WorkerThread, TaskResult
from functools import partial
from chart import ChartItemDelegate, ChartDataProvider
from aws import GetAttributes, GetImageUrls, AWSError

import db_helper
import helper
import notify
import urllib2

class MainForm(QtGui.QMainWindow): 
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)     

        self.CreateToolBar()
        self.CreateStatusBar()
        self.CreateToolTip()

        self.removeAction.setEnabled(False)
        self.editAction.setEnabled(False)
                
        headers = [self.tr(""), self.tr("ASIN"), self.tr("Label"), self.tr("Price"), self.tr("Last"), self.tr("Min"), self.tr("Max"), self.tr("Chart")]
        
        self.listView = QtGui.QTreeWidget(self)
        self.listView.setHeaderLabels(headers)
        self.listView.setRootIsDecorated(False)
        self.listView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        
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
        
        self.listView.viewport().setMouseTracking(True)
        self.listView.viewport().installEventFilter(self);
        self.listView.installEventFilter(self)

        self.upTextForegroundColor = QtGui.QColor(255, 0, 0)
        self.downTextForegroundColor = QtGui.QColor(0, 128, 0)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.OnTimer)
        self.timer.start()
        
        self.updateThread = WorkerThread()
        self.updateThread.setTask(lambda abort: self.OnUpdateItemsTask(abort))
        self.updateThread.resultReady.connect(self.OnUpdateItemsTaskFinished)
        
        self.fetchThread = WorkerThread()
        self.fetchThread.resultReady.connect(self.OnFetchImageTaskFinished)

        self.CreateTray()
        self.tray.show()
        
        self.setCentralWidget(self.listView)
        self.resize(640, 200);
        self.setWindowTitle(self.tr("Items list"))
        self.setWindowIcon(QtGui.QIcon("images" + QtCore.QDir.separator() + "tray.png"))
        
        self.timer.setInterval(60000 * 20)
        self.hideAfterStart = True
        self.showNotifications = True
        self.settings = QtCore.QSettings(helper.GetConfigDir() + QtCore.QDir.separator() + helper.GetConfigName(), QtCore.QSettings.IniFormat, self)
        
        self.seriesProvider = ChartDataProvider()
        self.seriesProvider.Update()

        self.listView.setItemDelegateForColumn(self.chartColumn, ChartItemDelegate(self.listView, self.seriesProvider))
        
        self.LoadSettings()
        self.LoadAppearanceSettings()
        self.LoadCountryIcons()
        self.UpdateListView()
        
        if self.hideAfterStart: self.hide()
        else: self.show()

        self.SetLastUpdateLabel(self.lastUpdate)
        
    def CreateToolBar(self):
        self.toolbar = QtGui.QToolBar(self)
        self.CreateActions()
        
        self.toolbar.addAction(self.addAction)
        self.toolbar.addAction(self.editAction)
        self.toolbar.addAction(self.removeAction)
        self.toolbar.addAction(self.updateAction)
        
        self.addToolBar(self.toolbar)

    def CreateStatusBar(self):
        statusbar = QtGui.QStatusBar(self)

        self.lastUpdateLabel = QtGui.QLabel(statusbar)
        self.waitWidget = WaitWidget(statusbar)
        self.waitWidget.hide()

        statusbar.addWidget(self.lastUpdateLabel)
        statusbar.addWidget(self.waitWidget)

        self.setStatusBar(statusbar)
        
    def CreateToolTip(self):
        self.tooltip = ImageToolTip(self)
        self.tooltipItem = None        

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
        self.addAction = QtGui.QAction(self.tr("Add item..."), self)
        self.addAction.setIcon(QtGui.QIcon("images" + QtCore.QDir.separator() + "add.png"))
        self.addAction.triggered.connect(self.OnAddItem)
        
        self.editAction = QtGui.QAction(self.tr("Edit item..."), self)
        self.editAction.setIcon(QtGui.QIcon("images" + QtCore.QDir.separator() + "edit.png"))
        self.editAction.triggered.connect(self.OnEditItem)
            
        self.removeAction = QtGui.QAction(self.tr("Remove item(s)"), self)
        self.removeAction.setIcon(QtGui.QIcon("images" + QtCore.QDir.separator() + "remove.png"))
        self.removeAction.triggered.connect(self.OnRemoveItem)
        
        self.updateAction = QtGui.QAction(self.tr("Update"), self)
        self.updateAction.setIcon(QtGui.QIcon("images" + QtCore.QDir.separator() + "update.png"))
        self.updateAction.triggered.connect(self.OnUpdateItems)
        
        self.settingsAction = QtGui.QAction(self.tr("Settings..."), self)
        self.settingsAction.setIcon(QtGui.QIcon("images" + QtCore.QDir.separator() + "settings.png"))
        self.settingsAction.triggered.connect(self.OnShowSettings)
        
        self.itemsAction = QtGui.QAction(self.tr("Items..."), self)
        self.itemsAction.setIcon(QtGui.QIcon("images" + QtCore.QDir.separator() + "list.png"))
        self.itemsAction.triggered.connect(self.show)    
        
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
        if self.updateThread.isRunning(): self.updateThread.wait()
        if self.fetchThread.isRunning(): self.fetchThread.wait()

        self.SaveSettings()
        QtGui.qApp.quit()

    def closeEvent(self, event):
        self.hide()
        event.ignore()
        
    def eventFilter(self, obj, event):   
        if event.type() == QtCore.QEvent.ContextMenu:
            self.OnListViewContextMenuEvent(event)
            return True

        elif event.type() == QtCore.QEvent.MouseMove:
            self.OnListViewMouseMoveEvent(event)
            return True           
        
        elif event.type() == QtCore.QEvent.ToolTip:
            self.OnListViewToolTipEvent(event)
            return True
        
        return QtGui.QMainWindow.eventFilter(self, obj, event)
        
    def OnListViewContextMenuEvent(self, event):        
        asins = self.GetSelectedASINs()
        if not asins: return
    
        menu = QtGui.QMenu(self)
        
        if len(asins) == 1:
            urlAction = menu.addAction(self.tr("Open URL"))
            urlAction.triggered.connect(lambda: self.OnOpenURL(asins[0]))
            
            asinAction = menu.addAction(self.tr("Copy ASIN"))
            asinAction.triggered.connect(lambda: self.OnCopyASIN(asins[0]))
            
            if helper.debug_mode:
                attrsAction = menu.addAction(self.tr("Get attributes..."))
                attrsAction.triggered.connect(lambda: self.OnGetAttributes(asins[0]))     
                
                imagesAction = menu.addAction(self.tr("Get images..."))
                imagesAction.triggered.connect(lambda: self.OnGetImages(asins[0]))     
                
            menu.addSeparator()
            
        if len(asins) == 1:
            menu.addAction(self.editAction)
            
        menu.addAction(self.removeAction)

        if len(asins) > 0:
            menu.exec_(event.globalPos())
            
    def OnListViewMouseMoveEvent(self, event):
        item = self.listView.itemAt(event.pos())

        if item is None:
            self.tooltipItem = None
            self.tooltip.hideTip()
        
        if self.tooltipItem is None or item is self.tooltipItem:
            return

        if not item is self.tooltipItem:
            print("self.tooltip.showTip -> {0}".format(item))
            self.tooltip.showTip(QtGui.QCursor.pos())
            self.tooltipItem = item
            self.FetchImage()
            
    def OnListViewToolTipEvent(self, event):
        if self.tooltip.isVisible(): return

        self.tooltipItem = self.listView.itemAt(event.pos())
        
        if self.tooltipItem is None:
            self.tooltip.hideTip()
        else:
            self.tooltip.showTip(QtGui.QCursor.pos())
            self.FetchImage()

    def GetSelectedASINs(self):
        items = self.listView.selectedItems()
        
        if not items: return []
        return list(map(lambda item : item.text(self.asinColumn), items))

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
                item.setForeground(self.priceColumn, self.downTextForegroundColor)
                item.setForeground(self.lastColumn, self.downTextForegroundColor)
            if last < price and price != 0 and last != 0: 
                item.setForeground(self.priceColumn, self.upTextForegroundColor)
                item.setForeground(self.lastColumn, self.upTextForegroundColor)
            

            self.seriesProvider.SetRow2Asin(cntr, asin)
            cntr = cntr + 1

            self.listView.addTopLevelItem(item)

    def OnItemSelectionChanged(self):
        enable_removing = len(self.listView.selectedItems()) > 0
        enable_editing = len(self.listView.selectedItems()) == 1
        
        self.removeAction.setEnabled(enable_removing)
        self.editAction.setEnabled(enable_editing)
    
    def OnAddItem(self):
        form = ItemForm(self, self.icons, self.accessKey, self.secretKey, self.associateTag)
        if form.exec_() == QtGui.QDialog.Accepted:
            self.UpdateListView()
        
    def OnEditItem(self):
        asins = self.GetSelectedASINs()
        if len(asins) > 1: return
        
        form = ItemForm(self, self.icons, self.accessKey, self.secretKey, self.associateTag, asins[0])
        if form.exec_() == QtGui.QDialog.Accepted: self.UpdateListView()
        
    def OnRemoveItem(self):
        if QtGui.QMessageBox.warning(self, self.tr("Warning"), self.tr("Delete this item(s) from database?"),
        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No) == QtGui.QMessageBox.No: return
        
        for asin in self.GetSelectedASINs():
            db_helper.DeleteItem(asin)
        
        self.UpdateListView()
        
    def OnUpdateItems(self):
        if self.updateThread.isRunning():
            print("Worker thread is already running")
            return
        
        if self.accessKey == "" or self.secretKey == "" or self.associateTag == "":
            QtGui.QMessageBox.warning(self, self.tr("Warning"),
            self.tr("Amazon access parameters are not set. Go to \"Settings\" dialog and fill corresponded fields"))
            return
        
        self.waitWidget.show()
        self.waitWidget.Start()
        
        self.toolbar.setEnabled(False)
        self.addAction.setEnabled(False)
        self.removeAction.setEnabled(False)
        self.editAction.setEnabled(False)
        
        self.updateThread.start()

    def OnUpdateItemsTask(self, abort):
        result = db_helper.UpdateDatabase(self.accessKey, self.secretKey, self.associateTag)
        return TaskResult(result, 0, "")
        
    def OnUpdateItemsTaskFinished(self, result):
        self.waitWidget.hide()
        self.waitWidget.Stop()
        
        self.toolbar.setEnabled(True)
        self.addAction.setEnabled(True)
        self.removeAction.setEnabled(True)
        self.editAction.setEnabled(True)
        self.OnItemSelectionChanged()
        
        if result.error != 0:
            QtGui.QMessageBox.information(self, self.tr("Fetching error"), result.message)
            return

        self.DoUpdateItems(result.result[0], result.result[1], result.result[2], result.result[3])
        
    def DoUpdateItems(self, cntr, up, down, error):
        if error != "" and cntr == 0:
            notify.Notify(error, self, self.sysNotify)
            print(error)
            return

        self.lastUpdate = QtCore.QDateTime.currentDateTime()
        self.SetLastUpdateLabel(self.lastUpdate)
        
        self.settings.setValue("last_update", self.lastUpdate)
        
        if not self.showNotifications: return
        
        text = str(cntr) + self.tr(" items have been updated")
        if error != "": text += "\n" + error
        
        notify.Notify(text, self, self.sysNotify)
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
        self.sysNotify = to_bool(self.settings.value("sys_notify", "false"))
        self.lastUpdate = self.settings.value("last_update", QtCore.QDateTime())

    def LoadAppearanceSettings(self):
        def ReadColorValue(key, def_color):
            """
            @type def_color: QtGui.QColor
            """
            if not self.settings.contains(key):
                self.settings.setValue(key, def_color.name())

            color = QtGui.QColor(self.settings.value(key, def_color.name()))

            if color.isValid(): return color
            return def_color

        self.settings.beginGroup("Appearance")

        delegete = self.listView.itemDelegateForColumn(self.chartColumn)

        if delegete:
            delegete.SetUpLineColor(ReadColorValue("graph_up_line_color", delegete.GetUpLineColor()))
            delegete.SetUpFillColor(ReadColorValue("graph_up_fill_color", delegete.GetUpFillColor()))
            delegete.SetDownLineColor(ReadColorValue("graph_down_line_color", delegete.GetDownLineColor()))
            delegete.SetDownFillColor(ReadColorValue("graph_down_fill_color", delegete.GetDownFillColor()))
            delegete.SetDefaultLineColor(ReadColorValue("graph_default_line_color", delegete.GetDefaultLineColor()))
            delegete.SetDefaultFillColor(ReadColorValue("graph_default_fill_color", delegete.GetDefaultFillColor()))

        self.upTextForegroundColor = ReadColorValue("text_up_foreground_color", self.upTextForegroundColor)
        self.downTextForegroundColor = ReadColorValue("text_down_foreground_color", self.downTextForegroundColor)

        self.settings.endGroup()
        
    def OnCopyASIN(self, asin):
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(asin)
        
    def OnOpenURL(self, asin):
        country = db_helper.GetItemCountry(asin)    
        domain = helper.GetDomain(country)
        
        if not domain or not asin: return
        
        url = "http://amzn." + domain + "/" + asin
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        
    def OnGetAttributes(self, asin):
        try:
            country = db_helper.GetItemCountry(asin)
            attrs = GetAttributes(asin, country, self.accessKey, self.secretKey, self.associateTag)
            print(attrs)
            
        except AWSError, e:
            print(e.GetFullDescription())
            
    def OnGetImages(self, asin):
        try:
            country = db_helper.GetItemCountry(asin)
            images = GetImageUrls(asin, country, self.accessKey, self.secretKey, self.associateTag)
            print(images)
            
        except AWSError, e:
            print(e.GetFullDescription())

    def SetLastUpdateLabel(self, date):
        str_date = self.tr("n/a")
        if not date.isNull() and date.isValid(): str_date = date.toString(QtCore.Qt.SystemLocaleLongDate)

        self.lastUpdateLabel.setText(self.tr("Last update:") + " " + str_date)
        
    def FetchImage(self):
        if self.tooltipItem is None: return
        asin = self.tooltipItem.text(self.asinColumn)
        
        if helper.debug_mode:
            print("fetching for asin {0}".format(asin))
        
        if self.fetchThread.isRunning():
            self.fetchThread.requestInterruption()
            return
        
        self.fetchThread.setTask(lambda abort: self.OnFetchImageTask(asin, abort))
        self.fetchThread.start()

    def OnFetchImageTask(self, asin, abort):
        country = db_helper.GetItemCountry(asin)
        urls = GetImageUrls(asin, country, self.accessKey, self.secretKey, self.associateTag)
        
        if not asin in urls: return TaskResult(None, 1, "can not find image URLs for asin {0}".format(asin))
        
        medium_image_url = urls[asin]["M"]
        
        if not medium_image_url: return TaskResult(None, 1, "no \"Medium\" image URL for asin {0}".format(asin))
        
        try:
            request = urllib2.urlopen(medium_image_url, timeout=10)
            if request.getcode() != 200: return TaskResult(None, 1, "server returns {0} code for {1}".format(request.getcode(), medium_image_url))
        
            image = QtGui.QImage.fromData(request.read())
            
            if image.isNull(): return  TaskResult(None, 1, "server returns broken image (size : {0}, mimetype: {1})".format(0, request.getinfo().gettype()))
            else:
                return TaskResult(image, 1, "")
            
        except Exception:
            return TaskResult(None, 1, "can retrive image from {0}".format(medium_image_url))

        return TaskResult(None, 1, "")
        
    def OnFetchImageTaskFinished(self, result):
        if self.tooltip.isVisible():
            if result.result == None: self.tooltip.SetPixmap(None)
            else: self.tooltip.SetPixmap(QtGui.QPixmap.fromImage(result.result))
