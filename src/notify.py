from PySide import QtCore, QtGui
import os

def Notify(text, parent, use_system):
    if use_system:
        cmd = "notify-send --icon=\"{0}\" --app-name=\"{1}\" \"{2}\"".format(os.path.abspath(os.path.dirname(__file__)) + QtCore.QDir.separator() + "images" + QtCore.QDir.separator() + "awd.png", "Amazon Watch Dog", text)
        os.system(cmd)
    else:
        tip = NotificationTip(parent, text)
        tip.ThrowNotification(4000)

class NotificationTip(QtGui.QDialog):

    def __init__(self, parent, text):
      
        QtGui.QDialog.__init__(self, parent, QtCore.Qt.ToolTip)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.timerId = -1
        
        label = QtGui.QLabel(self)
        label.setText(text)
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)
        self.updateGeometry()
        
        screenRect = QtCore.QRect(QtGui.qApp.desktop().availableGeometry())
        self.move(screenRect.width() - self.sizeHint().width() - 10, screenRect.height() - self.sizeHint().height() - 10)
        
    def paintEvent(self, event):        
        rect = self.rect()
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)

        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(QtGui.qApp.palette().color(QtGui.QPalette.WindowText), 1))
        painter.drawRect(rect)
    
    def ThrowNotification(self, msecs):
        self.timerId = self.startTimer(msecs)
        self.show()
        
    def mousePressEvent(self, event):
        self.close()
        
    def timerEvent(self, event):
        if event.timerId() == self.timerId:
            self.killTimer(self.timerId)
            if not self.underMouse(): self.close()