from PySide import QtCore
from collections import namedtuple

TaskResult = namedtuple("TaskResult", ["result", "error", "message"])

class WorkerThread(QtCore.QThread):
    resultReady = QtCore.Signal(object)

    def __init__(self):
        QtCore.QThread.__init__(self)

        self.interrupt = False
        self.task = None

    def setTask(self, task):
        self.task = task

    def run(self):
        result = self.task(self.isInterruptionRequested)
        self.resultReady.emit(result)

    def isInterruptionRequested(self):
        return self.interrupt

    def requestInterruption(self):
        self.interrupt = True