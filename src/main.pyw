#!/usr/bin/env python

from PySide import QtCore, QtGui
from mainform import MainForm
from argparse import ArgumentParser

import sys
import db_helper
import helper

parser = ArgumentParser()
parser.add_argument("-c", "--config", dest = "config_dir", help = "configuration directory", metavar="PATH")
parser.add_argument("-style")
args = parser.parse_args()

helper.config_dir = args.config_dir

app = QtGui.QApplication(sys.argv)

if not QtGui.QSystemTrayIcon.isSystemTrayAvailable():
    QtGui.QMessageBox.critical(None, QtCore.QObject.tr("Amazon Watch Dog"), QtCore.QObject.tr("System tray not found!"))
    sys.exit(0)

QtGui.qApp.setQuitOnLastWindowClosed(False)

db_helper.SetupDatabase()

form = MainForm()

sys.exit(app.exec_())