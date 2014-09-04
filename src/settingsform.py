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
        
        layout = QtGui.QVBoxLayout()
        
        self.timeSpin = QtGui.QSpinBox(self)
        self.timeSpin.setRange(0, 3600)

        self.hideCheck = QtGui.QCheckBox(self.tr("Minimize to system tray after start"), self)
        self.notifyCheck = QtGui.QCheckBox(self.tr("Show notifications"), self)
        self.sendCheck = QtGui.QCheckBox(self.tr("Use notify-send (libnotify)"), self)
        self.akEdit = QtGui.QLineEdit(self)
        self.skEdit = QtGui.QLineEdit(self)
        self.atEdit = QtGui.QLineEdit(self)
        self.skEdit.setEchoMode(QtGui.QLineEdit.Password)

        okButton = QtGui.QPushButton(self.tr("Ok"), self)
        okButton.clicked.connect(self.OnOk)

        cancelButton = QtGui.QPushButton(self.tr("Cancel"), self)
        cancelButton.clicked.connect(self.close)
        
        testButton = QtGui.QPushButton(self.tr("Test"), self)
        testButton.clicked.connect(self.OnTestNotification)
        
        clearButton = QtGui.QPushButton(self.tr("Clear image cache"), self)
        clearButton.clicked.connect(self.OnClearCache)
        
        self.notifyGB = QtGui.QGroupBox(self.tr("Notify options"), self)
        
        subLayout = QtGui.QHBoxLayout()
        subLayout.addWidget(self.sendCheck, 1)
        subLayout.addWidget(testButton, 0)
        self.notifyGB.setLayout(subLayout)
        
        self.notifyCheck.toggled.connect(self.notifyGB.setEnabled)

        subLayout = QtGui.QHBoxLayout()
        subLayout.addWidget(QtGui.QLabel(self.tr("Update interval (min)")), 2)
        subLayout.addWidget(self.timeSpin, 1)
        layout.addLayout(subLayout)
        
        self.amazonGB = QtGui.QGroupBox(self.tr("Amazon options"), self)

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
        layout.addStretch()
        
        subLayout = QtGui.QHBoxLayout()
        subLayout.addStretch()
        subLayout.addWidget(okButton)
        subLayout.addWidget(cancelButton)
        layout.addLayout(subLayout)
        
        self.params = {}
        self.LoadSettings()
        
        self.setLayout(layout)
        self.setWindowTitle("Settings")
        
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
