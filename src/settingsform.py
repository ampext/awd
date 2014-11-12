from PySide import QtGui, QtCore
from colorbutton import ColorButton
from helper import ReadColorValue, to_bool

import notify
import defaults


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
        self.listWidget.itemSelectionChanged.connect(self.OnListSelectionChanged)
        
#        selectionColor = self.palette().color(QtGui.QPalette.Highlight)

#        style = """QListView {{ show-decoration-selected: 0; }}
#                QListView::item:selected {{ background-color: {0}; }}
#                QListView::item:hover {{ background: transparent; }}""".format(selectionColor.name())

#        self.listWidget.setStyleSheet(style)
        
        generalItem = QtGui.QListWidgetItem(QtGui.QIcon("images" + QtCore.QDir.separator() + "general.png"), self.tr("General"))
        apprItem = QtGui.QListWidgetItem(QtGui.QIcon("images" + QtCore.QDir.separator() + "appearance.png"), self.tr("Appearance"))
                                         
        generalItem.setTextAlignment(QtCore.Qt.AlignHCenter or QtCore.Qt.AlignVCenter)
        apprItem.setTextAlignment(QtCore.Qt.AlignHCenter or QtCore.Qt.AlignVCenter)
        
        self.listWidget.addItem(generalItem)
        self.listWidget.addItem(apprItem)
        
        self.listWidget.setMaximumHeight(self.listWidget.sizeHintForRow(0) + 4)
        
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

        self.lastPanelIndex = 0
        self.SelectPanel(self.lastPanelIndex)

        self.LoadSettings()
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
        panel = QtGui.QWidget(parent)
        layout = QtGui.QVBoxLayout()
        formLayout = QtGui.QFormLayout()
        
        self.samplesSpin = QtGui.QSpinBox(parent)
        self.samplesSpin.setRange(5, 100)


        self.ulcButton = ColorButton(parent)
        self.ufcButton = ColorButton(parent)
        self.dlcButton = ColorButton(parent)
        self.dfcButton = ColorButton(parent)
        self.nlcButton = ColorButton(parent)
        self.nfcButton = ColorButton(parent)
        self.utcButton = ColorButton(parent)
        self.dtcButton = ColorButton(parent)
        
        self.restoreButton = QtGui.QPushButton(self.tr("Restore defaults"), parent)
        self.restoreButton.clicked.connect(self.OnRestoreDefaults)

        formLayout.addRow(self.tr("Number of preview samples"), self.samplesSpin)

        formLayout.addRow(self.tr("Up line color"), self.ulcButton)
        formLayout.addRow(self.tr("Up fill color"), self.ufcButton)

        formLayout.addRow(self.tr("Down line color"), self.dlcButton)
        formLayout.addRow(self.tr("Down fill color"), self.dfcButton)

        formLayout.addRow(self.tr("Neutral line color"), self.nlcButton)
        formLayout.addRow(self.tr("Neutral fill color"), self.nfcButton)

        formLayout.addRow(self.tr("Up text color"), self.utcButton)
        formLayout.addRow(self.tr("Down text color"), self.dtcButton)
        
        layout.addLayout(formLayout)

        subLayout = QtGui.QHBoxLayout()
        subLayout.addWidget(self.restoreButton)
        subLayout.addStretch()
        
        layout.addLayout(subLayout)
        
        panel.setLayout(layout)

        return panel
    
    def SelectPanel(self, index):
        self.lastPanelIndex = index
        self.stackedWidget.setCurrentIndex(index)
        self.listWidget.setCurrentItem(self.listWidget.item(index))
        
    def OnListItemChanged(self, currentItem, previousItem):
        if currentItem:
            self.SelectPanel(self.listWidget.row(currentItem))   
            
    def OnListSelectionChanged(self):
        if len(self.listWidget.selectedItems()) == 0:
            self.SelectPanel(self.lastPanelIndex)
        
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
        
        self.settings.beginGroup("Appearance")
        
        self.settings.setValue("graph_n_samples", self.samplesSpin.value())
        self.settings.setValue("graph_up_line_color", self.ulcButton.GetColor().name())
        self.settings.setValue("graph_up_fill_color", self.ufcButton.GetColor().name())
        self.settings.setValue("graph_down_line_color", self.dlcButton.GetColor().name())
        self.settings.setValue("graph_down_fill_color", self.dfcButton.GetColor().name())
        self.settings.setValue("graph_neutral_line_color", self.nlcButton.GetColor().name())
        self.settings.setValue("graph_neutral_fill_color", self.nfcButton.GetColor().name())
        self.settings.setValue("text_up_foreground_color", self.utcButton.GetColor().name())
        self.settings.setValue("text_down_foreground_color", self.dtcButton.GetColor().name())

        self.settings.endGroup()

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
        
        self.settings.beginGroup("Appearance")
        
        self.samplesSpin.setValue(int(self.settings.value("graph_n_samples", defaults.GetNumSamples())))
        self.ulcButton.SetColor(ReadColorValue(self.settings, "graph_up_line_color", defaults.GetUpLineColor()))
        self.ufcButton.SetColor(ReadColorValue(self.settings, "graph_up_fill_color", defaults.GetUpFillColor()))
        self.dlcButton.SetColor(ReadColorValue(self.settings, "graph_down_line_color", defaults.GetDownLineColor()))
        self.dfcButton.SetColor(ReadColorValue(self.settings, "graph_down_fill_color", defaults.GetDownFillColor()))
        self.nlcButton.SetColor(ReadColorValue(self.settings, "graph_neutral_line_color", defaults.GetNeutralLineColor()))
        self.nfcButton.SetColor(ReadColorValue(self.settings, "graph_neutral_fill_color", defaults.GetDefaultNeutralFillColor()))
        self.utcButton.SetColor(ReadColorValue(self.settings, "text_up_foreground_color", defaults.GetTextUpForegroundColor()))
        self.dtcButton.SetColor(ReadColorValue(self.settings, "text_down_foreground_color", defaults.GetTextDownForegroundColor()))

        self.settings.endGroup()
        
    def OnTestNotification(self):
        notify.Notify(self.tr("Test action"), self.tr("Notification test"), self, self.sendCheck.isChecked())
        
    def OnClearCache(self):
        self.cache.Clear()
        self.cache.Update()

    def OnRestoreDefaults(self):
        self.samplesSpin.setValue(defaults.GetNumSamples())
        self.ulcButton.SetColor(defaults.GetUpLineColor())
        self.ufcButton.SetColor(defaults.GetUpFillColor())
        self.dlcButton.SetColor(defaults.GetDownLineColor())
        self.dfcButton.SetColor(defaults.GetDownFillColor())
        self.nlcButton.SetColor(defaults.GetNeutralLineColor())
        self.nfcButton.SetColor(defaults.GetDefaultNeutralFillColor())
        self.utcButton.SetColor(defaults.GetTextUpForegroundColor())
        self.dtcButton.SetColor(defaults.GetTextDownForegroundColor())
