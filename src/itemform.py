from PySide import QtGui, QtCore
import db_helper

class ItemForm(QtGui.QDialog): 
    def __init__(self, parent = None, icons = {}, asin = ""):
        QtGui.QDialog.__init__(self, parent)
        
        layout = QtGui.QVBoxLayout()
        
        self.asinEdit = QtGui.QLineEdit(self)
        self.labelEdit = QtGui.QLineEdit(self)
        
        subLayout = QtGui.QHBoxLayout()
        subLayout.addWidget(QtGui.QLabel(self.tr("ASIN"), self), 1)
        subLayout.addWidget(self.asinEdit, 2)
        layout.addLayout(subLayout)

        subLayout = QtGui.QHBoxLayout()
        subLayout.addWidget(QtGui.QLabel(self.tr("Label"), self), 1)
        subLayout.addWidget(self.labelEdit, 2)
        layout.addLayout(subLayout)
        
        self.comboBox = QtGui.QComboBox(self)
        
        for country in db_helper.GetAmazonCountries():
            if icons.has_key(country): self.comboBox.addItem(icons[country], country)
            else: self.comboBox.addItem(country)
        
        layout.addWidget(self.comboBox)
        
        okButton = None
        
        if asin == "":
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
        
        subLayout = QtGui.QHBoxLayout()
        subLayout.addStretch(1)
        subLayout.addWidget(okButton)
        subLayout.addWidget(cancelButton)
        layout.addLayout(subLayout)
        
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Item"))
        self.setResult(QtGui.QDialog.Rejected)
        
    def LoadItem(self, asin):  
        lac = db_helper.GetItemLabelAndCountry(asin)   
        self.asinEdit.setText(asin)
        self.labelEdit.setText(lac[0])
        self.comboBox.setCurrentIndex(self.comboBox.findText(lac[1]))

    def AddItem(self):
        # TODO: remove whitespace characters from text

        if self.asinEdit.text() == "":
            QtGui.QMessageBox.information(self, self.tr("Validation"), self.tr("ASIN is empty!"))
            return

        if self.labelEdit.text() == "":
            QtGui.QMessageBox.information(self, self.tr("Validation"), self.tr("Label is empty!"))
            return

        if db_helper.CheckASIN(self.asinEdit.text()): 
            QtGui.QMessageBox.information(self, self.tr("Validation"), self.tr("Can't add new item because item with same ASIN already exists!"))
            return

        db_helper.AddItem(self.asinEdit.text(), self.labelEdit.text(), self.comboBox.currentText())
        
        self.accept()
    
    def EditItem(self):
        
        if self.labelEdit.text() == "":
            QtGui.QMessageBox.information(self, self.tr("Validation"), self.tr("Label is empty!"))
            return
        
        db_helper.EditItemLabel(self.asinEdit.text(), self.labelEdit.text())
        
        self.accept()