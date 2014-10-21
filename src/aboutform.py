from PySide import QtGui, QtCore
import notify
import helper
import os

class AboutForm(QtGui.QDialog): 
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        verticalLayout = QtGui.QVBoxLayout(self)

        frame = QtGui.QFrame(self)
        frame.setAutoFillBackground(True)
        frame.setFrameShape(QtGui.QFrame.StyledPanel)
        frame.setFrameShadow(QtGui.QFrame.Sunken)

        horizontalLayout = QtGui.QHBoxLayout(frame)

        brush = QtGui.QBrush(QtGui.QColor("white"))

        palette = QtGui.QPalette()
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        frame.setPalette(palette)

        iconLabel = QtGui.QLabel(frame)
        
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        
        iconLabel.setSizePolicy(sizePolicy)
        iconLabel.setMinimumSize(QtCore.QSize(0, 0))
        iconLabel.setMaximumSize(QtCore.QSize(64, 64))
        iconLabel.setPixmap(QtGui.QPixmap("images" + QtCore.QDir.separator() + "awd.png"))
        iconLabel.setScaledContents(True)

        programLabel = QtGui.QLabel(frame)
        programLabel.setText("<html><body><span style=\"font-weight:bold; font-size: 12pt;\">Amazon Watch Dog</span><br><span style=\"font-weight:bold;\">Version 0.4</body></html>")

        horizontalLayout.addWidget(iconLabel)
        horizontalLayout.addWidget(programLabel)

        verticalLayout.addWidget(frame)

        tabWidget = QtGui.QTabWidget(self)

        aboutTab = QtGui.QWidget()
        tabWidget.addTab(aboutTab, self.tr("About"))

        aboutLayout = QtGui.QHBoxLayout(aboutTab)
        aboutLabel = QtGui.QLabel(aboutTab)
        aboutLabel.setText("<html><body>AWD - Amazon Watch Dog<br><br>(c) 2010 - 2014 Artem Semenov<br><br>License: GNU General Public License Version 3</body></html>")
        aboutLayout.addWidget(aboutLabel)

        authorsTab = QtGui.QWidget()
        tabWidget.addTab(authorsTab, self.tr("Authors"))

        authorsLayout = QtGui.QHBoxLayout(authorsTab)
        authorsLabel = QtGui.QLabel(authorsTab)
        authorsLabel.setText("<html><body>Artem Semenov</body></html>")
        authorsLayout.addWidget(authorsLabel)

        verticalLayout.addWidget(tabWidget)

        box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok, QtCore.Qt.Horizontal, self)

        verticalLayout.addWidget(box)

        box.accepted.connect(self.close)

        self.setWindowTitle(self.tr("About Amazon Watch Dog"))
