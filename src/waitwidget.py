from PySide import QtGui, QtCore
import math

class WaitWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.angleProperty = 0.0
        self.color = QtGui.QColor("OrangeRed")
        
        self.angleAnimation = QtCore.QPropertyAnimation(self, "angle")
        self.angleAnimation.setDuration(1000)
        self.angleAnimation.setStartValue(0.0)
        self.angleAnimation.setEndValue(360.0)
        self.angleAnimation.setLoopCount(-1)
        self.angleAnimation.setEasingCurve(QtCore.QEasingCurve.Linear)
        self.angleAnimation.valueChanged.connect(lambda value: self.update())
        
        self.cachedPath = None
        self.cachedSize = QtCore.QSize(-1, -1)
        self.setMinimumSize(10, 10)
        
    def sizeHint(self):
        return QtCore.QSize(32, 32)
        
    def SetColor(self, color):
        self.color = color
        
    def GetColor(self):
        return self.color
    
    def SetAngle(self, angle):
        self.angleProperty = angle
        
    def GetAngle(self):
        return self.angleProperty
    
    angle = QtCore.Property(float, GetAngle, SetAngle)
        
    def CreatePath(self, center, radius, width, start, length):
        inner_radius = radius - width
        if inner_radius < 0: return QtGui.QPainterPath()
        
        path = QtGui.QPainterPath()
        path.moveTo(center.x() + math.cos(math.radians(start)) * inner_radius, center.y() + math.sin(math.radians(start)) * inner_radius);
        path.arcTo(center.x() - inner_radius, center.y() - inner_radius, 2 * inner_radius, 2 * inner_radius, start, length)
        path.lineTo(center.x() + math.cos(math.radians(start + length)) * radius, center.y() + math.sin(math.radians(start + length)) * radius);
        path.arcTo(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius, start + length, -length)
        path.closeSubpath()
        
        return path
    
    def Start(self):
        self.angleAnimation.start()
    
    def Stop(self):
        self.angleAnimation.stop()
    
    def sizeHint(self):
        return QtCore.QSize(20, 20)
        
    def paintEvent(self, event):
        painter = QtGui.QPainter()
        
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        if self.cachedSize != self.size():
           self.cachedSize = self.size()
           self.cachedPath = None
           
        center = QtCore.QPoint(self.size().width() / 2, self.size().height() / 2)
        
        if not self.cachedPath:    
            padding = 0
            width = 4
            radius = min(self.size().width(), self.size().height()) / 2 - padding
            
            self.cachedPath = self.CreatePath(center, radius, width, 0.0, 360.0)

        gradient = QtGui.QConicalGradient(center, 0.0)
        gradient.setColorAt(0.0, self.color)
        gradient.setColorAt(1.0, QtGui.QColor(255, 255, 255, 0))
        gradient.setAngle(self.GetAngle())
        
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawPath(self.cachedPath)
        
        painter.end()