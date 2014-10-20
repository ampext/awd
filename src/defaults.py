from PySide import QtGui
from platform import system

def GetUpLineColor():
    return QtGui.QColor("red")

def GetUpFillColor():
    return QtGui.QColor("lightPink")

def GetDownLineColor():
    return QtGui.QColor("darkGreen")

def GetDownFillColor():
    return QtGui.QColor("lightGreen")

def GetNeutralLineColor():
    return QtGui.QColor("darkGray")

def GetDefaultNeutralFillColor():
    return QtGui.QColor("lightGray")

def GetTextUpForegroundColor():
    return  QtGui.QColor("red")

def GetTextDownForegroundColor():
    return  QtGui.QColor("darkGreen")

def GetNumSamples():
	return 10

def GetTrayIconName():
	if system() == "Windows": return "tray_win.png"
	return "tray_kde.png"