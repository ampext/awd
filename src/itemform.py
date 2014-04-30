from PySide import QtGui, QtCore
from aws import GetAttributes, AWSError
from worker import WorkerThread, TaskResult
import threading
import db_helper
import time

class ItemForm(QtGui.QDialog): 
    def __init__(self, parent, icons, accessKey, secretKey, associateTag, asin = ""):
        QtGui.QDialog.__init__(self, parent)

        self.editMode = not not asin

        self.accessKey = accessKey
        self.secretKey = secretKey
        self.associateTag = associateTag

        self.thread = None

        layout = QtGui.QVBoxLayout()
        
        self.asinEdit = QtGui.QLineEdit(self)
        self.labelEdit = QtGui.QLineEdit(self)
        self.comboBox = QtGui.QComboBox(self)
        self.afButton = QtGui.QPushButton(self.tr("Fill"), self)
               
        asinLayout = QtGui.QHBoxLayout()
        asinLayout.addWidget(self.asinEdit)
        asinLayout.addWidget(self.comboBox)
        asinLayout.addWidget(self.afButton)
        
        formLayout = QtGui.QFormLayout()
        formLayout.addRow(self.tr("ASIN"), asinLayout)
        formLayout.addRow(self.tr("Label"), self.labelEdit)
        
        self.okButton = None
        
        if not self.editMode:
            self.okButton = QtGui.QPushButton(self.tr("Add"), self)
            self.okButton.clicked.connect(self.AddItem)
        else:
            self.okButton = QtGui.QPushButton(self.tr("Edit"), self)
            self.okButton.clicked.connect(self.EditItem)
            self.LoadItem(asin)
            
        cancelButton = QtGui.QPushButton(self.tr("Cancel"), self)
        cancelButton.clicked.connect(self.Cancel)
        
        self.asinEdit.textChanged.connect(self.OnASINTextChanged)
        self.afButton.clicked.connect(self.OnAutoFillFields)
        
        btnLayout = QtGui.QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.okButton)
        btnLayout.addWidget(cancelButton)
        
        layout.addLayout(formLayout)
        layout.addLayout(btnLayout)
        
        for country in db_helper.GetAmazonCountries():
            if icons.has_key(country): self.comboBox.addItem(icons[country], country)
            else: self.comboBox.addItem(country)

        self.EnableControls()
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Item"))
        self.setResult(QtGui.QDialog.Rejected)
        
    def LoadItem(self, asin):  
        lac = db_helper.GetItemLabelAndCountry(asin)   
        self.asinEdit.setText(asin)
        self.labelEdit.setText(lac[0])
        self.comboBox.setCurrentIndex(self.comboBox.findText(lac[1]))

    def AddItem(self):
        if not self.asinEdit.text():
            QtGui.QMessageBox.information(self, self.tr("Validation"), self.tr("ASIN is empty!"))
            return

        if not self.labelEdit.text():
            QtGui.QMessageBox.information(self, self.tr("Validation"), self.tr("Label is empty!"))
            return

        if db_helper.CheckASIN(self.asinEdit.text()): 
            QtGui.QMessageBox.information(self, self.tr("Validation"), self.tr("Cannot add new item because item with same ASIN already exists!"))
            return

        db_helper.AddItem(self.asinEdit.text(), self.labelEdit.text(), self.comboBox.currentText())
        
        self.accept()
    
    def EditItem(self):
        if not self.labelEdit.text():
            QtGui.QMessageBox.information(self, self.tr("Validation"), self.tr("Label is empty!"))
            return
        
        db_helper.EditItemLabel(self.asinEdit.text(), self.labelEdit.text())
        
        self.accept()

    def Cancel(self):      
        if self.thread:
            self.thread.requestInterruption()
            self.thread.wait()

        self.close()
        
    def closeEvent(self, event):
        self.Cancel()

    def OnASINTextChanged(self, text):        
        self.afButton.setEnabled(not not text)
        self.okButton.setEnabled(not not text)

    def DisableControls(self):
        self.asinEdit.setEnabled(False)
        self.labelEdit.setEnabled(False)
        self.comboBox.setEnabled(False)
        self.afButton.setEnabled(False)
        self.okButton.setEnabled(False)

    def EnableControls(self):
        self.asinEdit.setEnabled(not self.editMode)
        self.labelEdit.setEnabled(True)
        self.comboBox.setEnabled(not self.editMode)
        self.afButton.setEnabled(not not self.asinEdit.text())
        self.okButton.setEnabled(not not self.asinEdit.text())

    def OnAutoFillFields(self):
        if self.thread and self.thread.isRunning():
            print("Worker thread is already running")
            return

        self.DisableControls()

        if not self.thread:
            self.thread = WorkerThread()
            self.thread.setTask(lambda abort: self.FetchInfoTask(abort))
            self.thread.resultReady.connect(self.OnFetchInfoTaskFinished)

        self.thread.start()

    def FetchInfoTask(self, abort):
        attrs = {}

        try:
            asin = self.asinEdit.text()
            country = self.comboBox.currentText()
            attrs = GetAttributes(asin, country, self.accessKey, self.secretKey, self.associateTag)
            
        except AWSError, e: return TaskResult(None, 1, e.GetFullDescription())

        return TaskResult(attrs, 0, "")
            
    def OnFetchInfoTaskFinished(self, result):
        self.EnableControls()
        
        if result.error != 0:
            QtGui.QMessageBox.information(self, self.tr("Fetching error"), result.message)
            return

        attrs = result.result
        
        if "Title" in attrs:
            self.labelEdit.setText(attrs["Title"])
        else:
            QtGui.QMessageBox.information(self, self.tr("Fetching error"), self.tr("Attribute \"Title\" not found"))