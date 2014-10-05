from PySide import QtGui, QtCore

class ColorButton(QtGui.QPushButton): 
    def __init__(self, parent, color = QtGui.QColor("lightPink")):
        QtGui.QPushButton.__init__(self, parent)
        
        self.color = color
        
        self.clicked.connect(self.OnChooseColor)
        
    def paintEvent(self, event):
        buttonOption = QtGui.QStyleOptionButton()
        self.initStyleOption(buttonOption)
        
        painter = QtGui.QPainter(self)
        
        self.style().drawControl(QtGui.QStyle.CE_PushButtonBevel, buttonOption, painter, self)
        
        rect = self.style().subElementRect(QtGui.QStyle.SE_PushButtonContents, buttonOption, self)
        rect.adjust(4, 4, -5, -5)
        
        painter.setPen(QtGui.QPen(self.color.darker()))
        painter.setBrush(QtGui.QBrush(self.color))
        painter.drawRect(rect)
        
        if self.hasFocus():
            focusOption = QtGui.QStyleOptionFocusRect()
            focusOption.initFrom(self)
            focusOption.rect = self.style().subElementRect(QtGui.QStyle.SE_PushButtonFocusRect, buttonOption, self)
            focusOption.backgroundColor = self.palette().color(QtGui.QPalette.Background)
            
            self.style().drawPrimitive(QtGui.QStyle.PE_FrameFocusRect, focusOption, painter, self)
            
    def OnChooseColor(self):
        self.color = QtGui.QColorDialog.getColor(self.color, self, self.tr("Select color"), QtGui.QColorDialog.DontUseNativeDialog)
        
    def SetColor(self, color):
        self.color = color
        
    def GetColor(self):
        return self.color