from PySide import QtGui, QtCore, QtXml
from aws import FillParams, CreateRESTRequest, CreateRESTSignature, RESTRequest
import db_helper
import httplib

class RequestForm(QtGui.QDialog):
    def __init__(self, parent, icons, accessKey, secretKey, associateTag):
        QtGui.QDialog.__init__(self, parent)

        self.accessKey = accessKey
        self.secretKey = secretKey
        self.associateTag = associateTag

        self.paramsEdit = QtGui.QLineEdit(self)
        self.paramsEdit.textChanged.connect(self.OnParamsTextChanged)
        
        self.comboBox = QtGui.QComboBox(self)
        self.comboBox.currentIndexChanged.connect(self.OnCountryChanged)
        
        self.requestText = QtGui.QPlainTextEdit(self)
        self.outputText = QtGui.QPlainTextEdit(self)
        
        self.fetchButton = QtGui.QPushButton(self.tr("Fetch"))
        self.fetchButton.clicked.connect(self.OnFetch)
        
        self.indentCheck = QtGui.QCheckBox(self.tr("Indent XML Output"))
        
        self.wwCheck = QtGui.QCheckBox(self.tr("Dynamic Word Wrap"))
        self.wwCheck.stateChanged.connect(self.OnWordWrap)

        for country in db_helper.GetAmazonCountries():
            if icons.has_key(country): self.comboBox.addItem(icons[country], country)
            else: self.comboBox.addItem(country)

        self.paramsEdit.setText("Operation=ItemLookup&ResponseGroup=OfferFull&ItemId=1234567")
        self.requestText.setReadOnly(True)
        self.outputText.setReadOnly(True)
        self.outputText.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.indentCheck.setChecked(True)
        self.requestText.setMaximumHeight(100)
        self.requestText.setMinimumWidth(500)
                
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        self.outputText.setSizePolicy(sizePolicy)

        paramsLayout = QtGui.QHBoxLayout()
        paramsLayout.addWidget(self.paramsEdit)
        paramsLayout.addWidget(self.comboBox)

        formLayout = QtGui.QFormLayout()
        formLayout.addRow(self.tr("Params"), paramsLayout)
        formLayout.addRow(self.tr("Request"), self.requestText)
        
        formatLayout = QtGui.QHBoxLayout()
        formatLayout.addWidget(self.indentCheck)
        formatLayout.addWidget(self.wwCheck)
        formatLayout.addStretch(1)

        layout = QtGui.QVBoxLayout()

        layout.addLayout(formLayout)
        layout.addLayout(formatLayout)
        layout.addWidget(self.fetchButton)
        layout.addWidget(self.outputText)
        
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Request Builder"))
        self.setResult(QtGui.QDialog.Accepted)

    def OnCountryChanged(self, index):
        self.OnParamsTextChanged(self.paramsEdit.text())
        
    def OnWordWrap(self, state):
        if state == QtCore.Qt.CheckState.Checked: self.outputText.setWordWrapMode(QtGui.QTextOption.WordWrap)
        else: self.outputText.setWordWrapMode(QtGui.QTextOption.NoWrap)

    def OnParamsTextChanged(self, text):        
        if not text:
            self.requestText.setPlainText("")
            self.fetchButton.setEnabled(False)
            return
        
        params_dict = {}
        
        items = text.split("&")
        
        for item in items:
            param_name, sep, param_value = item.partition("=")
            if not param_name: continue
        
            params_dict[param_name] = param_value
        
        FillParams(params_dict, self.accessKey, self.secretKey, self.associateTag)
        self.rest = CreateRESTRequest(params_dict, self.comboBox.currentText())
        self.rest = RESTRequest(self.rest.method, self.rest.host, self.rest.url, self.rest.params + "&Signature=" + CreateRESTSignature("\n".join(self.rest), self.secretKey))
        request_url = self.rest.host + self.rest.url + "?" + self.rest.params
        
        self.requestText.setPlainText("http://" + request_url)
        self.fetchButton.setEnabled(True)
        
    def OnFetch(self):
        connection = httplib.HTTPConnection(self.rest.host)
        connection.request(self.rest.method, self.rest.url + "?" + self.rest.params)
        result = connection.getresponse()
        content = result.read()
        connection.close()
        
        if result.status != 200: self.outputText.clear()
        else:
            if self.indentCheck.isChecked():
                doc = QtXml.QDomDocument()
                doc.setContent(content)
                content = doc.toString(4)
                
            self.outputText.setPlainText(content)
