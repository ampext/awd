from PySide import QtGui, QtCore
import notify
import helper

def to_bool(value):
    if isinstance(value, unicode): return value.lower() == "true"
    return bool(value)

class SettingsForm(QtGui.QDialog): 
    def __init__(self, parent, settings, cache):
        QtGui.QDialog.__init__(self, parent)
        self.settings = settings
        self.cache = cache
        
        self.listWidget = QtGui.QListWidget(self)
        self.listWidget.setFlow(QtGui.QListView.LeftToRight)
        self.listWidget.setViewMode(QtGui.QListView.IconMode)
        self.listWidget.setMovement(QtGui.QListView.Static)
        self.listWidget.setIconSize(QtCore.QSize(48, 48))
        self.listWidget.setUniformItemSizes(True)
        self.listWidget.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed))
        self.listWidget.currentItemChanged.connect(self.OnListItemChanged)
        
        generalItem = QtGui.QListWidgetItem(QtGui.QIcon("images" + QtCore.QDir.separator() + "general.png"), self.tr("General"))
        apprItem = QtGui.QListWidgetItem(QtGui.QIcon("images" + QtCore.QDir.separator() + "appearance.png"), self.tr("Appearance"))
                                         
        generalItem.setTextAlignment(QtCore.Qt.AlignHCenter or QtCore.Qt.AlignVCenter)
        apprItem.setTextAlignment(QtCore.Qt.AlignHCenter or QtCore.Qt.AlignVCenter)
        
        self.listWidget.addItem(generalItem)
        self.listWidget.addItem(apprItem)
        
        self.listWidget.setMaximumHeight(self.listWidget.sizeHintForRow(0) + 10)
        
        self.stackedWidget = QtGui.QStackedWidget(self)
        self.stackedWidget.addWidget(self.CreateGeneralPanel(self.stackedWidget))
        self.stackedWidget.addWidget(self.CreateAppearancePanel(self.stackedWidget))
        
        okButton = QtGui.QPushButton(self.tr("Ok"), self)
        okButton.clicked.connect(self.OnOk)

        cancelButton = QtGui.QPushButton(self.tr("Cancel"), self)
        cancelButton.clicked.connect(self.close)
        
        subLayout = QtGui.QHBoxLayout()
        subLayout.addStretch()
        subLayout.addWidget(okButton)
        subLayout.addWidget(cancelButton)
        
        layout = QtGui.QVBoxLayout()
        
        layout.addWidget(self.listWidget)
        layout.addWidget(self.stackedWidget)
        layout.addStretch()
        layout.addLayout(subLayout)            
        
        self.setLayout(layout)

        self.LoadSettings()
        self.SelectPanel(0)
        self.setWindowTitle(self.tr("Settings"))
        
    def CreateGeneralPanel(self, parent):
        panel = QtGui.QWidget(parent)
        layout = QtGui.QVBoxLayout()
        
        panel.setLayout(layout)
        
        self.timeSpin = QtGui.QSpinBox(parent)
        self.timeSpin.setRange(0, 3600)

        self.hideCheck = QtGui.QCheckBox(self.tr("Minimize to system tray after start"), parent)
        self.notifyCheck = QtGui.QCheckBox(self.tr("Show notifications"), parent)
        self.sendCheck = QtGui.QCheckBox(self.tr("Use notify-send (libnotify)"), parent)
        self.akEdit = QtGui.QLineEdit(parent)
        self.skEdit = QtGui.QLineEdit(parent)
        self.atEdit = QtGui.QLineEdit(parent)
        self.skEdit.setEchoMode(QtGui.QLineEdit.Password)
        
        testButton = QtGui.QPushButton(self.tr("Test"), parent)
        testButton.clicked.connect(self.OnTestNotification)
        
        clearButton = QtGui.QPushButton(self.tr("Clear image cache"), parent)
        clearButton.clicked.connect(self.OnClearCache)
        
        self.notifyGB = QtGui.QGroupBox(self.tr("Notify options"), parent)
        
        subLayout = QtGui.QHBoxLayout()
        subLayout.addWidget(self.sendCheck, 1)
        subLayout.addWidget(testButton, 0)
        self.notifyGB.setLayout(subLayout)
        
        self.notifyCheck.toggled.connect(self.notifyGB.setEnabled)

        subLayout = QtGui.QHBoxLayout()
        subLayout.addWidget(QtGui.QLabel(self.tr("Update interval (min)")), 2)
        subLayout.addWidget(self.timeSpin, 1)
        layout.addLayout(subLayout)
        
        self.amazonGB = QtGui.QGroupBox(self.tr("Amazon options"), parent)

        subLayout = QtGui.QFormLayout()
        subLayout.addRow(QtGui.QLabel(self.tr("Access key")), self.akEdit)
        subLayout.addRow(QtGui.QLabel(self.tr("Secret key")), self.skEdit)
        subLayout.addRow(QtGui.QLabel(self.tr("Associate tag")), self.atEdit)
        self.amazonGB.setLayout(subLayout)

        layout.addWidget(self.amazonGB)
        layout.addWidget(self.notifyCheck)
        layout.addWidget(self.notifyGB)
        layout.addWidget(self.hideCheck)
        
        subLayout = QtGui.QHBoxLayout()
        subLayout.addWidget(clearButton)
        subLayout.addStretch()
        
        layout.addLayout(subLayout)
        
        return panel
        
    def CreateAppearancePanel(self, parent):
        return QtGui.QWidget(parent)
    
    def SelectPanel(self, index):
        self.stackedWidget.setCurrentIndex(index)
        self.listWidget.setCurrentItem(self.listWidget.item(index))
        
    def OnListItemChanged(self, currentItem, previousItem):
        if currentItem:
            self.SelectPanel(self.listWidget.row(currentItem))   
        
    def OnOk(self):
        self.SaveSettings()
        self.accept()
        
    def SaveSettings(self):     
        self.settings.setValue("interval", self.timeSpin.value())
        self.settings.setValue("access_key", self.akEdit.text())
        self.settings.setValue("secret_key", self.skEdit.text())
        self.settings.setValue("associate_tag", self.atEdit.text())
        self.settings.setValue("hide", self.hideCheck.isChecked())
        self.settings.setValue("notifications", self.notifyCheck.isChecked())
        self.settings.setValue("sys_notify", self.sendCheck.isChecked())
        
        self.settings.sync()
        
    def LoadSettings(self):
        self.timeSpin.setValue(int(self.settings.value("interval", 20)))
        self.akEdit.setText(self.settings.value("access_key", ""))
        self.skEdit.setText(self.settings.value("secret_key", ""))
        self.atEdit.setText(self.settings.value("associate_tag", ""))
        self.hideCheck.setChecked(to_bool(self.settings.value("hide", "true")))
        self.notifyCheck.setChecked(to_bool(self.settings.value("notifications", "true")))
        self.sendCheck.setChecked(to_bool(self.settings.value("sys_notify", "true")))
        self.notifyGB.setEnabled(self.notifyCheck.isChecked())
        
    def OnTestNotification(self):
        notify.Notify(self.tr("Notification test"), self, self.sendCheck.isChecked())
        
    def OnClearCache(self):
        self.cache.Clear()
        self.cache.Update()
