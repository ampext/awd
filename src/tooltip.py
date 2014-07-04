from PySide import QtGui, QtCore
from waitwidget import WaitWidget

class ImageToolTip(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent, QtCore.Qt.ToolTip or QtCore.Qt.BypassGraphicsProxyWidget)
    
        self.parent = parent
        
        self.waitWidget = WaitWidget(self)
        self.waitWidget.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed))
        self.waitWidget.hide()
        
        self.imageLabel = QtGui.QLabel(self)
        self.imageLabel.hide()
        
        self.dummyWidget = QtGui.QLabel("n/a", self)
        self.dummyWidget.hide()
        
        self.layout = QtGui.QVBoxLayout(self)    
        self.layout.setAlignment(QtCore.Qt.AlignHCenter or QtCore.Qt.AlignVCenter)
        self.setLayout(self.layout)
        
        self.hideTimer = QtCore.QTimer(self)
        self.hideTimer.timeout.connect(self.OnTimer)
        self.hideTimer.setSingleShot(True)
        
        QtCore.QCoreApplication.instance().installEventFilter(self)
        
        self.ShowWaitWidget()
                
    def eventFilter(self, obj, event):       
        if (event.type() == QtCore.QEvent.WindowActivate 
        or event.type() == QtCore.QEvent.WindowDeactivate
        or event.type() == QtCore.QEvent.FocusIn
        or event.type() == QtCore.QEvent.FocusOut
        or event.type() == QtCore.QEvent.MouseButtonPress
        or event.type() == QtCore.QEvent.MouseButtonRelease
        or event.type() == QtCore.QEvent.MouseButtonDblClick
        or event.type() == QtCore.QEvent.Wheel):
            self.hideTipImmediately()
        
        if event.type() == QtCore.QEvent.Leave:
            self.hideTip()
            
        return False
    
    def showTip(self, pos, pixmap = None):
        self.SetPixmap(pixmap)
        self.hideTimer.stop()
        self.move(pos + QtCore.QPoint(2, 21))
        self.show()
        
    def hideTip(self):
        if not self.hideTimer.isActive():
            self.hideTimer.start(300)
            
    def hideTipImmediately(self):
        self.hideTimer.stop()
        self.hide()
            
    def OnTimer(self):
        self.hideTipImmediately()
        
    def SetWidget(self, widget):
        if self.layout.count() > 1:
            print("suspicious layout items count")
            return
        
        if self.layout.count() != 0:
            if self.layout.itemAt(0).widget() == widget: return
            else:
                self.layout.itemAt(0).widget().hide()
                self.layout.removeWidget(self.layout.itemAt(0).widget())

        self.layout.addWidget(widget)
        widget.show()
        self.layout.layout()
        
    def ShowWaitWidget(self):
        self.SetWidget(self.waitWidget)
        self.waitWidget.Start()

    def ShowImageWidget(self, pixmap):
        self.imageLabel.setPixmap(pixmap)
        self.SetWidget(self.imageLabel)
        self.waitWidget.Stop()
        
    def ShowDummyWidget(self):
        self.SetWidget(self.dummyWidget)
        self.waitWidget.Stop()

    def SetPixmap(self, pixmap):
        if pixmap is None: self.ShowWaitWidget()
        elif pixmap.isNull(): self.ShowDummyWidget()
        else: self.ShowImageWidget(pixmap)
            
    def paintEvent(self, event):
        options = QtGui.QStyleOptionFrame()
        options.initFrom(self)
        
        painter = QtGui.QStylePainter()
        
        painter.begin(self)
        painter.drawPrimitive(QtGui.QStyle.PE_PanelTipLabel, options)
        painter.end()