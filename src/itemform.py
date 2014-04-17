from PySide import QtGui, QtCore
from aws import GetAttributes, AWSError
import db_helper

class ItemForm(QtGui.QDialog): 
    def __init__(self, parent, icons, accessKey, secretKey, associateTag, asin = ""):
        QtGui.QDialog.__init__(self, parent)
        
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.associateTag = associateTag
        
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
        
        okButton = None
        
        if not asin:
            okButton = QtGui.QPushButton(self.tr("Add"), self)
            okButton.clicked.connect(self.AddItem)
        else:
            okButton = QtGui.QPushButton(self.tr("Edit"), self)
            okButton.clicked.connect(self.EditItem)
            
            self.asinEdit.setDisabled(True)
            self.comboBox.setDisabled(True)
            self.LoadItem(asin)
            
        cancelButton = QtGui.QPushButton(self.tr("Cancel"), self)
        cancelButton.clicked.connect(self.close)
        
        self.asinEdit.textChanged.connect(self.OnASINTextChanged)
        self.afButton.clicked.connect(self.OnAutoFillFields)
        
        btnLayout = QtGui.QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(okButton)
        btnLayout.addWidget(cancelButton)
        
        layout.addLayout(formLayout)
        layout.addLayout(btnLayout)
        
        for country in db_helper.GetAmazonCountries():
            if icons.has_key(country): self.comboBox.addItem(icons[country], country)
            else: self.comboBox.addItem(country)
        
        if not asin: self.afButton.setEnabled(False)
        
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
        
    def OnASINTextChanged(self, text):        
        self.afButton.setEnabled(not not text)
        
    def OnAutoFillFields(self):
        attrs = {}
        
        try:
            asin = self.asinEdit.text()
            country = self.comboBox.currentText()
            attrs = GetAttributes(asin, country, self.accessKey, self.secretKey, self.associateTag)
            
        except AWSError, e:
            QtGui.QMessageBox.information(self, self.tr("Validation"), e.GetFullDescription())
            
        if "Title" in attrs:
            self.labelEdit.setText(attrs["Title"])
        
    def FillFields(self):
        pass